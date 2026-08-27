"""The DB-test floor's own counting mechanism (PLAN-0107 AC-12).

Step 10 asks for this explicitly: *"a synthetic session where all DB tests skip must
trip it"*. The floor exists because an unreachable Postgres turns 475 DB-backed tests
into skips and `pytest -q` still exits 0 — a mass skip is indistinguishable from a
mass pass on the summary line. A guard against that shape is worthless unless the
shape can be shown to fail it, so the first test here IS that shape.

The decision is factored into :func:`db_floor_verdict` — pure, three inputs — so these
cases drive it directly instead of orchestrating a nested pytest session. The
recording half (`db_support._record_executed_db_test`) is exercised separately: it is
the other place the count can silently go wrong.
"""

from __future__ import annotations

import pytest

from tests import db_support
from tests.conftest import _DB_TEST_FLOOR, db_floor_verdict


def test_a_session_where_every_db_test_skipped_trips_the_floor() -> None:
    """THE shape the floor exists for: Postgres unreachable, zero executed, CI green.

    If this ever passes, the floor has stopped being able to fail for its own reason.
    """
    verdict = db_floor_verdict(executed=0, ci="true", args=["tests"])

    assert verdict is not None, "0 executed DB tests under CI must FAIL the run"
    assert "0 DB-backed test(s) executed" in verdict
    assert str(_DB_TEST_FLOOR) in verdict, "the message must name the floor it enforced"


def test_the_measured_baseline_passes() -> None:
    """Positive control — without it, a floor that failed EVERYTHING would look correct."""
    assert db_floor_verdict(executed=475, ci="true", args=["tests"]) is None


def test_exactly_at_the_floor_passes() -> None:
    """The boundary is inclusive; stated as a test so it is not re-derived from the `>=`."""
    assert db_floor_verdict(executed=_DB_TEST_FLOOR, ci="true", args=["tests"]) is None
    assert db_floor_verdict(executed=_DB_TEST_FLOOR - 1, ci="true", args=["tests"]) is not None


def test_a_local_run_is_never_floored() -> None:
    """Worktrees legitimately lack the dev Docker Postgres — the floor is CI-only.

    AC-12: *"Local behaviour is untouched"*. A floor that fired locally would make a
    worktree checkout unusable and get disabled within a day.
    """
    assert db_floor_verdict(executed=0, ci=None, args=["tests"]) is None
    assert db_floor_verdict(executed=0, ci="", args=["tests"]) is None


def test_a_partial_selection_under_ci_is_never_floored() -> None:
    """Measured: one module under `CI=1` executes 7 DB tests — far under the floor.

    Without this carve-out the floor would redden every targeted CI run, which is the
    fastest route to it being deleted rather than fixed.
    """
    assert (
        db_floor_verdict(executed=7, ci="true", args=["tests/api/test_run_link_scenario.py"])
        is None
    )
    assert db_floor_verdict(executed=0, ci="true", args=["tests/api"]) is None


def test_the_recorder_counts_distinct_tests_not_phases(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setup and call phases of ONE test must count once.

    `PYTEST_CURRENT_TEST` carries a trailing phase marker; if the strip regressed, a
    test that builds two engines would inflate the count and quietly lift the floor's
    effective margin.
    """
    monkeypatch.setattr(db_support, "EXECUTED_DB_TESTS", set())

    monkeypatch.setenv("PYTEST_CURRENT_TEST", "tests/x.py::test_a (setup)")
    db_support._record_executed_db_test()
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "tests/x.py::test_a (call)")
    db_support._record_executed_db_test()
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "tests/x.py::test_b (call)")
    db_support._record_executed_db_test()

    assert db_support.EXECUTED_DB_TESTS == {"tests/x.py::test_a", "tests/x.py::test_b"}


def test_the_recorder_is_silent_outside_pytest(monkeypatch: pytest.MonkeyPatch) -> None:
    """No env var, no recording — and no crash. The floor then simply sees no population."""
    monkeypatch.setattr(db_support, "EXECUTED_DB_TESTS", set())
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    db_support._record_executed_db_test()

    assert db_support.EXECUTED_DB_TESTS == set()
