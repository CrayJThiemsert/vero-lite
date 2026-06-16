"""Arm (b) of the B-γ comparison — raw text-to-SQL (PLAN-0027 D-3).

Reuses the ``nl_query_feasibility.text_to_sql`` pattern verbatim — the read-only
``SELECT`` guard, the in-memory SQLite, the ``{"sql": ...}`` generation seam — but
builds the DB **per scenario** from the procedure-baseline breach ``Scenario``
(its breached entity + distractor siblings as rows), because the
procedure-baseline dataset's abstract entity keys (``asset-E01`` …) are NOT the
``synthetic.py`` demo assets. The breached entity must be present in the DB for a
correct SELECT to find it (PLAN-0027 §3.2 — "how the breach scenario maps onto
rows").

Graded on **entity-ID only** — the affected primary-key token must appear in the
stringified SQL result (the ``score_sql`` value-token method, hyphen-normalized
like the grader). Raw SQL returns data, not an action proposal, so the **action
class is structurally unavailable** — recorded as the D-3 finding, NEVER scored as
a wrong answer.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from typing import Any

from benchmarks.nl_query_feasibility.text_to_sql import (
    SCHEMA_DDL,
    execute_sql,
    generate_sql,
)
from benchmarks.procedure_baseline.grader import normalize_primary_key
from benchmarks.procedure_baseline.schema import Scenario
from benchmarks.procedure_comparison.questions import render_sql_question
from services.engine.llm.structured import ChatClient

ACTION_CLASS_NA = "structurally N/A — raw SQL returns data, not an action proposal (D-3)"
"""Constant recorded for every arm-(b) item: SQL cannot propose an action class."""


def build_scenario_db(scenario: Scenario) -> sqlite3.Connection:
    """Build a fresh in-memory SQLite holding the scenario's readings.

    One ``site``; one ``asset`` + one ``operational_event`` reading per entity —
    the breached entity plus every distractor sibling — so a correct
    ``WHERE measured_value >= threshold`` discovers the breach and excludes the
    (safe-side) distractors. Reuses the ``text_to_sql.SCHEMA_DDL`` schema; rows are
    synthesised from the self-contained ``Scenario`` (the dataset keys are not in
    ``synthetic.py``).
    """
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA_DDL)
    conn.execute(
        "INSERT INTO site VALUES (?, ?, ?, ?, ?)",
        ("site-cmp-01", "Comparison Site", "substation", 0.0, 0.0),
    )
    readings: list[tuple[str, float]] = [(scenario.primary_key, scenario.measured_value)]
    readings += [(decoy.primary_key, decoy.measured_value) for decoy in scenario.distractors]
    for index, (primary_key, value) in enumerate(readings):
        conn.execute(
            "INSERT INTO asset VALUES (?, ?, ?, ?, ?, ?, ?)",
            (primary_key, primary_key, "battery", 250.0, "active", "2024-01-01", "site-cmp-01"),
        )
        conn.execute(
            "INSERT INTO operational_event VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"event-{index:02d}",
                "reading",
                "critical",
                value,
                scenario.unit,
                f"{primary_key} {scenario.unit} reading",
                "2026-05-21T08:10:00Z",
                primary_key,
                "site-cmp-01",
            ),
        )
    conn.commit()
    return conn


def entity_in_result(scenario: Scenario, rows: list[tuple[Any, ...]]) -> bool:
    """True iff the affected primary-key token appears in the stringified result
    (the ``score_sql`` value-token method, hyphen-normalized on both sides like
    the procedure-baseline grader's ``affected_primary_key`` check)."""
    blob = normalize_primary_key(" ".join(str(cell) for row in rows for cell in row))
    return normalize_primary_key(scenario.primary_key) in blob


@dataclass(frozen=True)
class ArmBResult:
    """One breach item's raw-text-to-SQL outcome.

    ``outcome`` is the failure-mode bucket (``correct`` | ``wrong`` | ``invalid``);
    ``action_class`` is the constant D-3 structural-N/A note. ``sql`` /
    ``result_preview`` / ``error`` are the offline-VERIFY evidence (``--dump-json``).
    """

    item_id: str
    sql: str
    row_count: int
    outcome: str
    entity_correct: bool
    action_class: str
    latency_s: float
    result_preview: str
    error: str


async def run_item_b(
    item_id: str,
    scenario: Scenario,
    client: ChatClient,
    reading_parameter: str,
) -> ArmBResult:
    """Generate + execute + grade one breach scenario through the text-to-SQL arm.

    ``invalid`` = the model returned no usable SQL OR a non-read-only / erroring
    statement (refused by ``is_select_only`` / SQLite); ``wrong`` = a valid SELECT
    ran but the affected entity token was not in the result; ``correct`` otherwise.
    """
    question = render_sql_question(scenario, reading_parameter)
    conn = build_scenario_db(scenario)
    start = time.perf_counter()
    sql, gen_err = await generate_sql(client, question)
    if gen_err:
        return ArmBResult(
            item_id,
            "",
            0,
            "invalid",
            False,
            ACTION_CLASS_NA,
            time.perf_counter() - start,
            "",
            gen_err,
        )
    rows, exec_err = execute_sql(conn, sql)
    latency = time.perf_counter() - start
    one_line_sql = sql.replace("\n", " ").strip()
    if exec_err:
        return ArmBResult(
            item_id,
            one_line_sql,
            0,
            "invalid",
            False,
            ACTION_CLASS_NA,
            latency,
            "",
            exec_err,
        )
    entity_correct = entity_in_result(scenario, rows)
    preview = "; ".join(str(row) for row in rows[:4])[:90]
    return ArmBResult(
        item_id=item_id,
        sql=one_line_sql,
        row_count=len(rows),
        outcome="correct" if entity_correct else "wrong",
        entity_correct=entity_correct,
        action_class=ACTION_CLASS_NA,
        latency_s=latency,
        result_preview=preview,
        error="",
    )


__all__ = [
    "ACTION_CLASS_NA",
    "ArmBResult",
    "build_scenario_db",
    "entity_in_result",
    "run_item_b",
]
