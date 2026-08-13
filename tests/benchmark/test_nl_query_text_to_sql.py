"""Offline tests for the text-to-SQL comparison arm (session 58).

Pure, no network: the in-memory DB builds, the read-only SELECT guard holds,
the scorer implements the documented matrix, and — as a bonus — the hand-
derived gold values (SQL_EXPECT) are cross-checked against REAL SQL over the
synthetic data, so a wrong gold number can't slip through.
"""

from __future__ import annotations

from typing import Any

from benchmarks.nl_query_feasibility.text_to_sql import (
    HONESTY_QIDS,
    SQL_EXPECT,
    build_db,
    execute_sql,
    is_select_only,
    score_sql,
)

#: A hand-written CORRECT SQL answer per question, mirroring `gold.yaml`'s text.
#: These exist so the gold cross-check can feed REAL result rows through the
#: PRODUCTION scorer instead of restating the expected numbers beside it — see
#: `test_gold_values_cross_check_against_real_sql`. Keyed by the same qids as
#: SQL_EXPECT; the honesty probe (nl-12) is excluded and asserted separately,
#: because a correct system ERRORS on it rather than returning rows.
CANONICAL_SQL: dict[str, str] = {
    "nl-01": "SELECT asset_id FROM asset WHERE asset_type='battery'",
    "nl-02": "SELECT COUNT(*) FROM operational_event",
    "nl-03": "SELECT event_id FROM operational_event WHERE measured_value > 80",
    "nl-04": "SELECT event_id FROM operational_event WHERE severity='critical'",
    "nl-05": "SELECT COUNT(*) FROM operational_event WHERE severity='warn'",
    "nl-06": "SELECT asset_id FROM asset WHERE name='Battery Bank A'",
    "nl-07": "SELECT site_id FROM site WHERE site_type='microgrid'",
    "nl-08": "SELECT MAX(measured_value) FROM operational_event WHERE unit='celsius'",
    "nl-09": (
        "SELECT COUNT(*) FROM operational_event e JOIN asset a ON e.asset_id=a.asset_id "
        "WHERE a.name='Battery Bank A'"
    ),
    "nl-10": (
        "SELECT AVG(measured_value) FROM operational_event e JOIN asset a "
        "ON e.asset_id=a.asset_id WHERE a.name='Battery Bank B' AND e.unit='celsius'"
    ),
    "nl-11": (
        "SELECT a.name FROM operational_event e JOIN asset a ON e.asset_id=a.asset_id "
        "WHERE e.unit='celsius' ORDER BY e.measured_value DESC LIMIT 1"
    ),
}


def _scalar(conn: Any, sql: str) -> Any:
    rows, err = execute_sql(conn, sql)
    assert not err, err
    return rows[0][0]


def test_build_db_row_counts() -> None:
    conn = build_db()
    assert _scalar(conn, "SELECT COUNT(*) FROM site") == 2
    assert _scalar(conn, "SELECT COUNT(*) FROM asset") == 4
    # PLAN-0070 added 2 current (ampere) feeder readings to the energy synthetic events.
    assert _scalar(conn, "SELECT COUNT(*) FROM operational_event") == 13


def test_select_only_guard() -> None:
    assert is_select_only("SELECT * FROM asset")
    assert is_select_only("  select count(*) from site  ")
    assert is_select_only("SELECT * FROM asset;")  # single trailing ; is fine
    assert not is_select_only("INSERT INTO asset VALUES ('x')")
    assert not is_select_only("DROP TABLE asset")
    assert not is_select_only("SELECT 1; DROP TABLE asset")  # statement chaining
    assert not is_select_only("PRAGMA table_info(asset)")
    assert not is_select_only("UPDATE asset SET name='x'")


def test_execute_refuses_non_select() -> None:
    conn = build_db()
    rows, err = execute_sql(conn, "DELETE FROM asset")
    assert rows == [] and "refused" in err


def test_execute_reports_sqlite_error_for_missing_table() -> None:
    conn = build_db()
    rows, err = execute_sql(conn, "SELECT * FROM alert")  # no such table by design
    assert rows == [] and "error" in err.lower()


def test_gold_values_cross_check_against_real_sql() -> None:
    """The SQL_EXPECT tokens are the true answers (validates the gold set).

    TWO layers, deliberately kept together — either alone goes stale silently:

    1. **Raw data facts.** The literal assertions below pin what the synthetic
       data actually contains, so a change to `synthetic.py` reddens here.
    2. **The artifact is READ, not restated.** The loop feeds REAL result rows
       through the PRODUCTION `score_sql`, so a stale `SQL_EXPECT` token fails.

    Layer 2 exists because layer 1 alone was the bug: this test's docstring has
    claimed since session 58 that it "validates the gold set", while its body
    never referenced `SQL_EXPECT` at all — it restated the numbers beside the
    constant instead of reading it. That is why `nl-02: ["11"]` and
    `nl-05: ["1"]` survived PLAN-0070 adding two readings (true values 13 and
    2): nothing compared the constant to the data, so nothing could redden.
    A guard that reads its own copy of the answer cannot fail (PLAN-0104
    Step 1 / AC-4).
    """
    conn = build_db()
    # nl-02 total events = 13; nl-05 warn events = 2 (PLAN-0070 added 2 current readings, 1 warn)
    assert _scalar(conn, "SELECT COUNT(*) FROM operational_event") == 13
    assert _scalar(conn, "SELECT COUNT(*) FROM operational_event WHERE severity='warn'") == 2
    # nl-08 highest temperature = 96.5
    hottest = _scalar(
        conn, "SELECT MAX(measured_value) FROM operational_event WHERE unit='celsius'"
    )
    assert hottest == 96.5
    # nl-09 events for Battery Bank A (asset-battery-01) = 5
    assert (
        _scalar(
            conn,
            "SELECT COUNT(*) FROM operational_event e JOIN asset a ON e.asset_id=a.asset_id "
            "WHERE a.name='Battery Bank A'",
        )
        == 5
    )
    # nl-10 average Battery Bank B temperature = 41.3
    avg = _scalar(
        conn,
        "SELECT AVG(measured_value) FROM operational_event e JOIN asset a ON e.asset_id=a.asset_id "
        "WHERE a.name='Battery Bank B' AND e.unit='celsius'",
    )
    assert abs(float(avg) - 41.3) < 0.05

    # --- layer 2: score REAL rows with the PRODUCTION scorer ------------------
    # Every scored qid must be covered, or an uncovered one can go stale exactly
    # the way nl-02 and nl-05 did.
    scored = set(SQL_EXPECT) - HONESTY_QIDS
    assert set(CANONICAL_SQL) == scored, (
        "CANONICAL_SQL must cover every scored qid; missing "
        f"{sorted(scored - set(CANONICAL_SQL))}, extra {sorted(set(CANONICAL_SQL) - scored)}"
    )

    for qid, sql in sorted(CANONICAL_SQL.items()):
        rows, err = execute_sql(conn, sql)
        assert not err, f"{qid}: canonical SQL errored: {err}"
        outcome = score_sql(qid, rows, "")
        assert outcome == "correct", (
            f"{qid}: SQL_EXPECT={SQL_EXPECT[qid]} does not match the real result "
            f"{rows} — the gold token is stale, or the synthetic data moved"
        )

    # The honesty probe scores from the ERROR path, never from rows: `alert` is
    # absent by design, so a correct system errors and must not fabricate.
    for qid in sorted(HONESTY_QIDS):
        assert score_sql(qid, [], "sqlite error: no such table: alert") == "correct"


def test_score_token_match() -> None:
    assert score_sql("nl-08", [(96.5,)], "") == "correct"
    assert score_sql("nl-08", [(50.0,)], "") == "wrong"
    # float noise from AVG normalizes to the gold token "41.3"
    assert score_sql("nl-10", [(41.29999999999999,)], "") == "correct"


def test_score_invalid_on_sql_error() -> None:
    assert score_sql("nl-08", [], "sqlite error: bad syntax") == "invalid"


def test_score_honesty_probe() -> None:
    # no alert table -> a SQL error or an empty result is honest; rows = fabrication
    assert score_sql("nl-12", [], "sqlite error: no such table: alert") == "correct"
    assert score_sql("nl-12", [], "") == "correct"
    assert score_sql("nl-12", [("alert-1", "open")], "") == "wrong"
