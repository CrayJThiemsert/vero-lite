"""AC-1, AC-2 and AC-8 of PLAN-0120 — the gate stops sharing a test database.

ADR-0018 **D8.2**: a ``check`` criterion may bind the test database only because the
gate is made resource-isolated. The gate injects an identity marker
(``VERO_TEST_DB_ROLE=gate``, SD-A ruled) into every check subprocess, so its pytest
resolves a database name of its own instead of the one the session it interrupts is
already using. That sharing is what fabricated nine test failures in s275, and s228 and
s253 before it.

🔴 **The whole point is the CHILD process.** Every assertion here reads a value the
child produced — a resolved database name, an exit code — never a variable the parent
merely set. A test that checked the parent's environment would pass on a build where
the marker never crosses the ``wsl.exe`` boundary (D8-VX-1), which is the silent
failure this AC exists to prevent. The WSLENV crossing itself needs a Windows host and
belongs to Step 7's single live run; what is offline-testable is that the child, not
the parent, is the thing being measured.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

HOOKS_DIR = Path(__file__).resolve().parents[2] / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

import _goal_gate  # noqa: E402  — sys.path manipulation above
from _goal_gate import (  # noqa: E402
    CHECK_CONTENDED,
    CHECK_FAIL,
    CHECK_PASS,
    CONTENDED_EXIT,
    DB_ROLE_ENV,
    DB_ROLE_VALUE,
    _run_one_check,
    run_goal_gate,
)
from _goal_state import Criterion, Goal, load_goal, new_goal, save_goal  # noqa: E402

PY = sys.executable


def _criterion(cmd: str, crit_id: str = "C1", timeout_s: int = 30) -> Criterion:
    return Criterion(id=crit_id, kind="check", cmd=cmd, desc="probe", timeout_s=timeout_s)


#: Reports the marker the CHILD sees, then exits on whether it is the expected value.
#: Exit 3 rather than 1 so a merely-failing command cannot be mistaken for this answer.
_ECHO_ROLE = (
    "import os, sys; "
    "v = os.environ.get('VERO_TEST_DB_ROLE'); "
    "print(f'child_role={v}'); "
    "sys.exit(0 if v == 'gate' else 3)"
)


@pytest.fixture
def gate_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, Any]:
    """Isolated goal path, isolated battery lock, captured Telegram.

    Both isolations are load-bearing: a live ``goal.json`` or a real battery lock on the
    dev box would otherwise decide these tests' outcome instead of the code under test.
    """
    goal_file = tmp_path / "goal.json"
    monkeypatch.setenv("CLAUDE_GOAL_PATH", str(goal_file))
    monkeypatch.delenv("CLAUDE_GOAL_CHECK_BUDGET_S", raising=False)
    monkeypatch.setenv("CLAUDE_PROBE_BATTERY_LOCK", str(tmp_path / "no-such-battery.lock"))
    # The parent must NOT already carry the marker, or "the gate injected it" would be
    # indistinguishable from "it was inherited".
    monkeypatch.delenv(DB_ROLE_ENV, raising=False)
    pings: list[tuple[str, str]] = []
    monkeypatch.setattr(
        _goal_gate, "_ping_telegram", lambda event, goal_text, detail: pings.append((event, detail))
    )
    monkeypatch.setattr(_goal_gate, "work_fingerprint", lambda: "fp-A")
    return {"goal_file": goal_file, "pings": pings, "monkeypatch": monkeypatch}


# --------------------------------------------------------------- AC-1 / AC-2


def test_the_check_child_receives_the_gate_role(gate_env: dict[str, Any]) -> None:
    """🔴 AC-1 (offline half). The marker reaches the CHILD process.

    The child reports what it sees and exits 0 only if it is ``gate``; the gate sees
    only the exit code, so this cannot pass on a variable that was merely set in the
    parent.
    """
    state, tail = _run_one_check(_criterion(f'"{PY}" -c "{_ECHO_ROLE}"'), 30.0)
    print(f"state={state} child_tail={tail.strip()!r}")
    assert state == CHECK_PASS
    assert f"child_role={DB_ROLE_VALUE}" in tail


def test_without_the_injection_the_child_sees_nothing(
    gate_env: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """🟢 AC-2 / the positive control, and the load-bearing one.

    With the injection removed the same child reports ``None`` and exits 3. Without
    this, a build that inherited the marker from the ambient environment — or one where
    every child happens to be called ``gate`` — would satisfy the test above perfectly.
    """
    monkeypatch.setattr(_goal_gate, "_check_env", lambda: None)
    state, tail = _run_one_check(_criterion(f'"{PY}" -c "{_ECHO_ROLE}"'), 30.0)
    print(f"state={state} child_tail={tail.strip()!r}")
    assert state == CHECK_FAIL
    assert "child_role=None" in tail


# --------------------------------------------------------------------- AC-8


def test_a_contended_exit_code_is_classified_contended_not_fail(
    gate_env: dict[str, Any],
) -> None:
    """🔴 AC-8. The reserved code is an INFRASTRUCTURE verdict, not a test failure.

    Classifying it as ``fail`` is the s275 defect exactly: a contention recorded into an
    append-only trail as a defect nobody can remove afterwards, and — under
    ``enforce: true`` — ridden straight into the V2-D3 ladder.
    """
    cmd = f'"{PY}" -c "import sys; sys.exit({CONTENDED_EXIT})"'
    state, _ = _run_one_check(_criterion(cmd), 30.0)
    print(f"state={state} (rc={CONTENDED_EXIT} must NOT be {CHECK_FAIL})")
    assert state == CHECK_CONTENDED


def test_an_ordinary_nonzero_exit_is_still_a_failure(gate_env: dict[str, Any]) -> None:
    """🟢 POSITIVE CONTROL for the mapping above. A gate that called EVERY non-zero exit
    'contended' would satisfy it perfectly and stop reporting real failures at all."""
    cmd = f'"{PY}" -c "import sys; sys.exit(1)"'
    state, _ = _run_one_check(_criterion(cmd), 30.0)
    print(f"state={state} (rc=1 must still be {CHECK_FAIL})")
    assert state == CHECK_FAIL


def test_a_contended_check_stands_the_gate_down_with_zero_residue(
    gate_env: dict[str, Any],
) -> None:
    """🔴 AC-8's other half — nothing is written to the append-only trail.

    PLAN-0115 SD-2's ruling applied to the same trail: a contention is an event about
    the HOST, not about the goal, so the goal's record must not carry it. Telegram is
    the channel of record. The gate re-arms at the next Stop.
    """
    goal = new_goal("isolate the gate", [_criterion(f'"{PY}" -c "import sys; sys.exit(75)"')])
    goal.enforce = True
    save_goal(goal, gate_env["goal_file"])

    pre = len(_reloaded(gate_env).evaluations)
    result = run_goal_gate({})
    post_goal = _reloaded(gate_env)
    post = len(post_goal.evaluations)
    events = [event for event, _ in gate_env["pings"]]
    print(f"result={result} evaluations pre={pre} post={post} status={post_goal.status} {events=}")

    # 🔴 ORDER is deliberate, not style. `post == pre` is THE claim of this AC — the
    # append-only trail must not carry a host event — and pytest stops at the first
    # failing assert. Asserting `result is None` first would leave zero-residue
    # NOT-REACHED under the mutation that removes the stand-down: state unknown, never
    # green, and with no witness anywhere.
    assert post == pre
    assert result is None
    assert post_goal.status == "active"
    assert "db_contended" in events


def test_an_ordinary_failing_check_still_records_and_consequences(
    gate_env: dict[str, Any],
) -> None:
    """🟢 POSITIVE CONTROL for the stand-down. A gate that stood down on EVERY check
    would write nothing ever, satisfy the test above, and silently stop verifying."""
    goal = new_goal("isolate the gate", [_criterion(f'"{PY}" -c "import sys; sys.exit(1)"')])
    save_goal(goal, gate_env["goal_file"])

    pre = len(_reloaded(gate_env).evaluations)
    run_goal_gate({})
    post = len(_reloaded(gate_env).evaluations)
    events = [event for event, _ in gate_env["pings"]]
    print(f"evaluations pre={pre} post={post} {events=}")
    assert post > pre


def test_the_contention_ping_names_the_holder_pid(gate_env: dict[str, Any]) -> None:
    """A red that does not say WHY is a red nobody can act on (ADR-0038 C6).

    The child prints the guard's token on its way out; the pid in it is the process a
    human has to reap, and it exists in the child's stdout and nowhere else.
    """
    token = "TEST-DB-GUARD db=x role=- key=1 outcome=CONTENDED holder_pid=424242 db_tests=0"
    cmd = f'"{PY}" -c "print({token!r}); import sys; sys.exit(75)"'
    goal = new_goal("isolate the gate", [_criterion(cmd)])
    save_goal(goal, gate_env["goal_file"])

    run_goal_gate({})
    details = [detail for event, detail in gate_env["pings"] if event == "db_contended"]
    print(f"ping_details={details}")
    assert details
    assert "424242" in details[0]


def _reloaded(env: dict[str, Any]) -> Goal:
    loaded = load_goal(env["goal_file"])
    assert loaded is not None
    return loaded
