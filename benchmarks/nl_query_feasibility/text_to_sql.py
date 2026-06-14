"""Text-to-SQL comparison arm of the NL-query feasibility spike (session 58).

The engine-A spike (``run_benchmark.py``) measured the SHIPPED
NL->StructuredQuery path. This arm runs the SAME 12 questions through a
**NL->SQL** path — the LLM writes a read-only SQLite SELECT over the same
synthetic energy data, which we execute and score — to separate two failure
classes the engine-A run surfaced:

* **architecture ceiling** (StructuredQuery can't express joins / aggregates):
  does text-to-SQL clear them natively (JOIN, MAX/AVG, GROUP BY)?
* **model discipline** (the model under-specifying — the whole-table fetch):
  does the same model omit the ``WHERE`` clause in SQL too?

Read-only by construction: only single ``SELECT`` statements are executed,
against an **in-memory** SQLite built fresh from ``synthetic.py`` (no real DB,
no network besides the model). ``run_text_to_sql.py`` is the MANUAL live runner.
"""

from __future__ import annotations

import json
import re
import sqlite3
import time
from dataclasses import dataclass
from typing import Any

from services.engine.llm.client import OllamaClient
from services.engine.llm.structured import ChatClient
from verticals.energy.data_adapter import synthetic

# --- schema shown to the model (mirrors energy_v0.yaml; enum hints included) --

SCHEMA_DDL = """\
CREATE TABLE site (
  site_id   TEXT PRIMARY KEY,
  name      TEXT,
  site_type TEXT,   -- one of: substation, microgrid, depot
  lat       REAL,
  lng       REAL
);
CREATE TABLE asset (
  asset_id    TEXT PRIMARY KEY,
  name        TEXT,
  asset_type  TEXT,   -- one of: battery, inverter, meter, transformer
  capacity_kw REAL,   -- NULL for some assets (e.g. meters)
  status      TEXT,   -- e.g. active
  install_date TEXT,  -- ISO date
  site_id     TEXT REFERENCES site(site_id)
);
CREATE TABLE operational_event (
  event_id       TEXT PRIMARY KEY,
  event_type     TEXT,   -- one of: reading, transition, alarm
  severity       TEXT,   -- one of: info, warn, error, critical
  measured_value REAL,   -- NULL for transition/alarm events
  unit           TEXT,   -- e.g. celsius, hz (NULL when no measured_value)
  description    TEXT,
  occurred_at    TEXT,   -- ISO datetime (UTC)
  asset_id       TEXT REFERENCES asset(asset_id),
  site_id        TEXT REFERENCES site(site_id)
);"""

#: The load-bearing tokens that must appear in a correct SQL result, per question
#: (SQL-result value scoring — the analogue of the engine-A gold). Honesty probe
#: handled by HONESTY_QIDS (no ``alert`` table exists → a correct system errors
#: or returns nothing, never fabricates).
SQL_EXPECT: dict[str, list[str]] = {
    "nl-01": ["asset-battery-01", "asset-battery-02"],
    "nl-02": ["11"],
    "nl-03": ["event-reading-06", "event-reading-03"],
    "nl-04": ["event-reading-03"],
    "nl-05": ["1"],
    "nl-06": ["asset-battery-01"],
    "nl-07": ["site-microgrid-01"],
    "nl-08": ["96.5"],
    "nl-09": ["5"],
    "nl-10": ["41.3"],
    "nl-11": ["Battery Bank A"],
    "nl-12": [],
}
HONESTY_QIDS = {"nl-12"}

_TABLES = {
    "site": (synthetic.sites, ("site_id", "name", "site_type", "lat", "lng")),
    "asset": (
        synthetic.assets,
        ("asset_id", "name", "asset_type", "capacity_kw", "status", "install_date", "site_id"),
    ),
    "operational_event": (
        synthetic.operational_events,
        (
            "event_id",
            "event_type",
            "severity",
            "measured_value",
            "unit",
            "description",
            "occurred_at",
            "asset_id",
            "site_id",
        ),
    ),
}


def build_db() -> sqlite3.Connection:
    """Build a fresh in-memory SQLite from the deterministic synthetic data."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA_DDL)
    for table, (source, columns) in _TABLES.items():
        placeholders = ", ".join("?" for _ in columns)
        rows = [tuple(_cell(rec.get(col)) for col in columns) for rec in source()]
        # table name is from the trusted hardcoded _TABLES dict, never user input
        conn.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)  # noqa: S608
    conn.commit()
    return conn


def _cell(value: Any) -> Any:
    """Coerce a synthetic value to a SQLite-storable scalar (dates -> ISO str)."""
    if value is None or isinstance(value, str | int | float):
        return value
    return str(value)


_SELECT_ONLY = re.compile(r"^\s*select\b", re.IGNORECASE)
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|attach|detach|pragma|create|replace|vacuum)\b",
    re.IGNORECASE,
)


def is_select_only(sql: str) -> bool:
    """True iff ``sql`` is a single read-only SELECT (no DDL/DML, one statement)."""
    stripped = sql.strip().rstrip(";").strip()
    if ";" in stripped:  # reject statement chaining
        return False
    return bool(_SELECT_ONLY.match(stripped)) and not _FORBIDDEN.search(stripped)


def execute_sql(conn: sqlite3.Connection, sql: str) -> tuple[list[tuple[Any, ...]], str]:
    """Execute a read-only SELECT; return (rows, error). Non-SELECT is refused."""
    if not is_select_only(sql):
        return [], "refused: not a read-only SELECT"
    try:
        cur = conn.execute(sql.strip().rstrip(";"))
        return cur.fetchall(), ""
    except sqlite3.Error as exc:
        return [], f"sqlite error: {exc}"


async def generate_sql(client: ChatClient, question: str) -> tuple[str, str]:
    """Ask the model for one read-only SQLite SELECT; return (sql, error)."""
    system = (
        "You translate an operator's plain-language question into ONE read-only "
        "SQLite SELECT over the schema below. Use only these tables and columns. "
        "Resolve names across tables with JOINs and use aggregates (COUNT, AVG, "
        "MAX, MIN, GROUP BY) when the question needs them. Filter values must "
        "match the data (e.g. unit = 'celsius', not 'C'). Return ONLY JSON of the "
        f'form {{"sql": "SELECT ..."}}.\n\nSchema:\n{SCHEMA_DDL}'
    )
    schema = {
        "type": "object",
        "properties": {"sql": {"type": "string"}},
        "required": ["sql"],
    }
    result = await client.chat(
        [{"role": "system", "content": system}, {"role": "user", "content": question}],
        response_format=schema,
    )
    try:
        parsed = json.loads(result.content)
    except json.JSONDecodeError as exc:
        return "", f"non-JSON reply: {exc}"
    sql = parsed.get("sql") if isinstance(parsed, dict) else None
    if not isinstance(sql, str) or not sql.strip():
        return "", "reply had no 'sql' string"
    return sql, ""


def score_sql(qid: str, rows: list[tuple[Any, ...]], error: str) -> str:
    """Outcome: correct | wrong | invalid.

    Honesty probe (no alert table): a SQL error or an empty result is correct
    (no fabrication); any rows is wrong. Otherwise: every SQL_EXPECT token must
    appear in the stringified result (and the query must not have errored).
    """
    if qid in HONESTY_QIDS:
        return "correct" if error or not rows else "wrong"
    if error:
        return "invalid"
    # Normalize float cells so a raw AVG (e.g. 41.29999999999999) matches the
    # gold token "41.3" — the engine-A phrase step rounds; raw SQL does not.
    blob = " ".join(_norm_cell(cell) for row in rows for cell in row)
    expect = SQL_EXPECT.get(qid, [])
    return "correct" if all(tok in blob for tok in expect) else "wrong"


def _norm_cell(cell: Any) -> str:
    """Stringify one result cell, rounding floats to 2 dp (so AVG noise matches)."""
    if isinstance(cell, float):
        return str(round(cell, 2))
    return str(cell)


@dataclass(frozen=True)
class SqlResult:
    """One question's text-to-SQL outcome."""

    qid: str
    sql: str
    row_count: int
    outcome: str  # correct | wrong | invalid
    latency_s: float
    result_preview: str
    error: str


async def run_case(conn: sqlite3.Connection, case: dict[str, Any], client: ChatClient) -> SqlResult:
    """Generate + execute + score one question through the text-to-SQL path."""
    qid = str(case["id"])
    start = time.perf_counter()
    sql, gen_err = await generate_sql(client, str(case["text"]))
    if gen_err:
        return SqlResult(qid, "", 0, "invalid", time.perf_counter() - start, "", gen_err)
    rows, exec_err = execute_sql(conn, sql)
    latency = time.perf_counter() - start
    preview = "; ".join(str(r) for r in rows[:4])
    return SqlResult(
        qid=qid,
        sql=sql.replace("\n", " ").strip(),
        row_count=len(rows),
        outcome=score_sql(qid, rows, exec_err),
        latency_s=latency,
        result_preview=preview[:90],
        error=exec_err,
    )


def summarize(results: list[SqlResult]) -> dict[str, Any]:
    """Aggregate the text-to-SQL run."""
    latencies = [r.latency_s for r in results]
    return {
        "n": len(results),
        "correct": sum(1 for r in results if r.outcome == "correct"),
        "wrong": [r.qid for r in results if r.outcome == "wrong"],
        "invalid": [r.qid for r in results if r.outcome == "invalid"],
        "latency_p50_s": round(_pct(latencies, 50.0), 2) if latencies else 0.0,
        "latency_p95_s": round(_pct(latencies, 95.0), 2) if latencies else 0.0,
        "latency_max_s": round(max(latencies), 2) if latencies else 0.0,
    }


def _pct(values: list[float], pct: float) -> float:
    from benchmarks.procedure_baseline.harness import percentile

    return percentile(values, pct)


__all__ = [
    "OllamaClient",
    "SqlResult",
    "build_db",
    "execute_sql",
    "generate_sql",
    "is_select_only",
    "run_case",
    "score_sql",
    "summarize",
]
