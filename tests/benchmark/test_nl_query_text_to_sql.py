"""Offline tests for the text-to-SQL comparison arm (session 58).

Pure, no network: the in-memory DB builds, the read-only SELECT guard holds,
the scorer implements the documented matrix, and — as a bonus — the hand-
derived gold values (SQL_EXPECT) are cross-checked against REAL SQL over the
synthetic data, so a wrong gold number can't slip through.
"""

from __future__ import annotations

from typing import Any

from benchmarks.nl_query_feasibility.text_to_sql import (
    build_db,
    execute_sql,
    is_select_only,
    score_sql,
)


def _scalar(conn: Any, sql: str) -> Any:
    rows, err = execute_sql(conn, sql)
    assert not err, err
    return rows[0][0]


def test_build_db_row_counts() -> None:
    conn = build_db()
    assert _scalar(conn, "SELECT COUNT(*) FROM site") == 2
    assert _scalar(conn, "SELECT COUNT(*) FROM asset") == 4
    assert _scalar(conn, "SELECT COUNT(*) FROM operational_event") == 11


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
    """The SQL_EXPECT tokens are the true answers (validates the gold set)."""
    conn = build_db()
    # nl-02 total events = 11; nl-05 warn events = 1
    assert _scalar(conn, "SELECT COUNT(*) FROM operational_event") == 11
    assert _scalar(conn, "SELECT COUNT(*) FROM operational_event WHERE severity='warn'") == 1
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
