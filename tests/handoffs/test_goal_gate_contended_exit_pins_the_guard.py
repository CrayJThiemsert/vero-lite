"""🔴 The gate and the test-database guard must agree on ONE reserved exit code.

``.claude/hooks/_goal_gate.py`` runs **Windows-side** and cannot import ``tests/`` — it
is reached through ``wsl bash -lc`` from the other side of a filesystem and interpreter
boundary. So ``CONTENDED_EXIT`` is a **literal in both files**, and duplicated constants
drift. This is the same cross-file shape as
``test_goal_gate_budget_fits_the_hook.py`` (the Stop hook's timeout vs the gate's check
budget) and ``test_goal_gate_battery_lock.py`` (the staleness bound).

What drift would cost, concretely: the guard exits 75, the gate is looking for 74, and
a contended session is recorded as an ordinary ``fail`` — a fabricated defect written
into an append-only trail that nobody can remove, and under ``enforce: true`` ridden
straight into the V2-D3 ladder. That is the s275 failure exactly, and it happened three
times (s228, s253, s275) before it had a name.

This file is the only thing that would ever notice the two sides parting.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parents[2] / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

import _goal_gate  # noqa: E402  — sys.path manipulation above

from tests import db_guard  # noqa: E402


def test_the_two_sides_agree_on_the_reserved_exit_code() -> None:
    """🔴 The pin. Both literals, one value."""
    print(f"gate={_goal_gate.CONTENDED_EXIT} guard={db_guard.CONTENDED_EXIT}")
    assert _goal_gate.CONTENDED_EXIT == db_guard.CONTENDED_EXIT


def test_the_reserved_code_cannot_be_confused_with_a_pytest_verdict() -> None:
    """pytest owns 0-5 for its own verdicts and 128+ is signal death.

    A code inside either range would make a contended session indistinguishable from an
    ordinary result — which is the entire failure this constant exists to prevent, so
    the range is asserted rather than trusted to whoever next edits the literal.
    """
    code = _goal_gate.CONTENDED_EXIT
    print(f"code={code} (must satisfy 5 < code < 128)")
    assert 5 < code < 128


def test_the_two_sides_agree_on_the_marker_variable_name() -> None:
    """The identity marker is a literal on both sides for the same reason.

    A drifted NAME fails more quietly than a drifted code: the gate would set a variable
    nobody reads, every check would resolve the session's own database, and the token
    would report ``ACQUIRED`` on a run that is not isolated at all — success-shaped, and
    wrong. AC-1's positive control catches it at runtime; this catches it at edit time.
    """
    print(f"gate={_goal_gate.DB_ROLE_ENV!r} guard={db_guard.ROLE_ENV!r}")
    assert _goal_gate.DB_ROLE_ENV == db_guard.ROLE_ENV


def test_the_gate_role_is_one_the_guard_would_accept() -> None:
    """🟢 The value the gate injects must survive the guard's own validation.

    A role the guard rejects raises at import inside the check subprocess — the check
    would fail for a reason that has nothing to do with the work being verified, and the
    trail would record it as a defect.
    """
    assert db_guard.validated_role(_goal_gate.DB_ROLE_VALUE) == _goal_gate.DB_ROLE_VALUE


def test_the_validator_the_test_above_relies_on_actually_rejects_things() -> None:
    """🟢 POSITIVE CONTROL for the test above. A validator that accepted everything
    would make it vacuous — it would pass for any string the gate happened to inject,
    including one that silently means 'no isolation'."""
    with pytest.raises(RuntimeError):
        db_guard.validated_role("NOT A VALID ROLE")
