"""AC-7 — the goal gate stands down while a probe battery mutates the tree.

**Safety hole 1, in one sentence** (PLAN-0115 Step 2). The gate runs `check` criteria as
subprocesses against the working tree and fingerprints it as `sha256(HEAD + porcelain)`, so
a battery mutating that tree makes every Stop event (a) record a **false** `fail` into an
**append-only** trail nobody can remove afterwards, and (b) read the mutation as "new work"
eligible to dispatch the `goal-evaluator` against code that is broken on purpose.

**SD-2 as Cray ruled it**: under the lock the gate writes **nothing** to `goal.json` — zero
residue in the very artifact being protected. Both drafted options fell on measurement: (a)
a stderr note lands nowhere a human or Claude ever sees, and (b) a trail annotation corrupts
four separate control-flow reads that filter only on `GATE_WARN_MARKER`. The visibility half
moved to Telegram, keyed to the lock, and lives on the driver side.

Its own module rather than a class in `test_goal_gate.py`: this needs a lock fixture the
other 60-odd tests never touch, and keeping it separate means an accidental import cycle
between the gate and the driver shows up as one red file, not sixty.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

HOOKS_DIR = Path(__file__).resolve().parents[2] / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

import _goal_gate  # noqa: E402  — sys.path manipulation above
from _goal_gate import run_goal_gate  # noqa: E402
from _goal_state import Criterion, Goal, load_goal, new_goal, save_goal  # noqa: E402

PY = sys.executable


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, Any]:
    goal_file = tmp_path / "goal.json"
    lock = tmp_path / "probe_battery.lock"
    monkeypatch.setenv("CLAUDE_GOAL_PATH", str(goal_file))
    monkeypatch.setenv("CLAUDE_PROBE_BATTERY_LOCK", str(lock))
    monkeypatch.delenv("CLAUDE_GOAL_CHECK_BUDGET_S", raising=False)
    pings: list[tuple[str, str]] = []
    monkeypatch.setattr(
        _goal_gate,
        "_ping_telegram",
        lambda event, goal_text, detail: pings.append((event, detail)),
    )
    monkeypatch.setattr(_goal_gate, "work_fingerprint", lambda: "fp-A")
    return {"goal_file": goal_file, "lock": lock, "pings": pings, "tmp_path": tmp_path}


def _write_lock(env: dict[str, Any], **over: Any) -> Path:
    payload: dict[str, Any] = {
        "run_id": "run-test",
        "pid": 4242,
        "head_sha": "deadbeef",
        "acquired": datetime.now(UTC).isoformat(),
        "heartbeat": 3,
        "heartbeat_ts": datetime.now(UTC).isoformat(),
    }
    payload.update(over)
    lock: Path = env["lock"]
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(json.dumps(payload), encoding="utf-8")
    return lock


def _touching_check(env: dict[str, Any]) -> tuple[Criterion, Path]:
    """A check whose only job is to prove, by side effect, whether it ever ran.

    A real subprocess writing a real file — never a monkeypatched `_run_checks`. The AC says
    the gate runs NO check subprocess, and a stubbed call cannot witness that: it would
    prove only that the stub was not called.
    """
    sentinel = env["tmp_path"] / "check-ran.marker"
    crit = Criterion(
        id="C1",
        kind="check",
        cmd=f"\"{PY}\" -c \"open(r'{sentinel}', 'w').close()\"",
        desc="touches a sentinel",
        timeout_s=30,
    )
    return crit, sentinel


def _failing_check() -> Criterion:
    return Criterion(
        id="C1",
        kind="check",
        cmd=f'"{PY}" -c "import sys; sys.exit(1)"',
        desc="always red",
        timeout_s=30,
    )


def _seed(goal: Goal, env: dict[str, Any]) -> None:
    save_goal(goal, env["goal_file"])


def _reload(env: dict[str, Any]) -> Goal:
    loaded = load_goal(env["goal_file"])
    assert loaded is not None
    return loaded


# -- the stand-down ---------------------------------------------------------------------


def test_a_fresh_lock_stands_the_gate_down(env: dict[str, Any]) -> None:
    _write_lock(env)
    _seed(new_goal("g", [_failing_check()]), env)
    assert run_goal_gate({}) is None


def test_a_fresh_lock_runs_no_check_subprocess(env: dict[str, Any]) -> None:
    """🔴 Not "the result was ignored" — the subprocess must never start. Running it against
    a deliberately-broken tree is what manufactures the false `fail`."""
    crit, sentinel = _touching_check(env)
    _write_lock(env)
    _seed(new_goal("g", [crit]), env)
    run_goal_gate({})
    assert not sentinel.exists()


def test_without_the_lock_that_same_check_does_run(env: dict[str, Any]) -> None:
    """🟢 POSITIVE CONTROL. Without it, a criterion whose command was simply broken would
    satisfy the test above perfectly."""
    crit, sentinel = _touching_check(env)
    _seed(new_goal("g", [crit]), env)
    run_goal_gate({})
    assert sentinel.exists()


# -- zero residue in goal.json ----------------------------------------------------------


def test_the_evaluations_trail_is_unchanged_in_length(env: dict[str, Any]) -> None:
    """🔴 A DELTA assert, not a presence one. `evaluations` is append-only, so "the trail
    holds no battery entry" is satisfied by a trail that grew for some other reason. Only
    the length being *identical* shows zero residue."""
    _seed(new_goal("g", [_failing_check()]), env)
    before = len(_reload(env).evaluations)
    _write_lock(env)
    run_goal_gate({})
    assert len(_reload(env).evaluations) == before


def test_without_the_lock_the_identical_goal_does_grow_the_trail(env: dict[str, Any]) -> None:
    """🟢 POSITIVE CONTROL for the delta: same goal, same gate, no lock — the trail grows.
    So the unchanged length is the lock's doing, not a gate that never writes."""
    _seed(new_goal("g", [_failing_check()]), env)
    before = len(_reload(env).evaluations)
    run_goal_gate({})
    assert len(_reload(env).evaluations) > before


def test_the_defer_is_tallied_in_the_locks_own_sidecar(env: dict[str, Any]) -> None:
    """The count the driver reports once on release — kept OUT of `goal.json`, which is the
    artifact the whole guard exists to protect."""
    lock = _write_lock(env)
    _seed(new_goal("g", [_failing_check()]), env)
    run_goal_gate({})
    sidecar = lock.with_name(lock.name + ".defers")
    assert sidecar.exists() and sidecar.read_text(encoding="utf-8").strip()


def test_standing_down_pings_nothing(env: dict[str, Any]) -> None:
    """Per-defer silence is deliberate (s254 ruling 2): the lock is held once per battery
    while Stop fires every turn, so a per-defer ping would emit several per battery — the
    only spam shape anyone could reasonably have been guarding against."""
    _write_lock(env)
    _seed(new_goal("g", [_failing_check()]), env)
    run_goal_gate({})
    assert env["pings"] == []


# -- staleness --------------------------------------------------------------------------


def test_a_stale_lock_does_not_stand_the_gate_down(env: dict[str, Any]) -> None:
    """A driver that died must not silence the gate forever."""
    crit, sentinel = _touching_check(env)
    _write_lock(env, heartbeat_ts="2020-01-01T00:00:00+00:00")
    _seed(new_goal("g", [crit]), env)
    run_goal_gate({})
    assert sentinel.exists()


def test_a_stale_lock_is_said_out_loud(env: dict[str, Any]) -> None:
    """A stale lock usually means a battery died with mutations still on disk, so the ping
    names the recovery path rather than passing over it in silence."""
    _write_lock(env, heartbeat_ts="2020-01-01T00:00:00+00:00")
    _seed(new_goal("g", [_failing_check()]), env)
    run_goal_gate({})
    assert any(event == "battery_lock_stale" for event, _ in env["pings"])


def test_a_heartbeat_in_the_future_reads_as_fresh_not_stale(env: dict[str, Any]) -> None:
    """🔴 The WSL2 clock hazard, asserted. This box's wall clock steps BACKWARDS, so a
    heartbeat stamped in the future is a clock artifact, not evidence. Reading it as stale
    would wake the gate mid-battery — the exact failure being guarded against."""
    crit, sentinel = _touching_check(env)
    _write_lock(env, heartbeat_ts="2099-01-01T00:00:00+00:00")
    _seed(new_goal("g", [crit]), env)
    run_goal_gate({})
    assert not sentinel.exists()


def test_a_malformed_lock_counts_as_absent(env: dict[str, Any]) -> None:
    """The gate's job when it cannot read the protocol is to keep working — never to
    silence itself on the strength of a file it does not understand."""
    crit, sentinel = _touching_check(env)
    lock: Path = env["lock"]
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text("{not json", encoding="utf-8")
    _seed(new_goal("g", [crit]), env)
    run_goal_gate({})
    assert sentinel.exists()


def test_an_absent_lock_gates_normally(env: dict[str, Any]) -> None:
    """🟢 The baseline the other cases are measured against."""
    crit, sentinel = _touching_check(env)
    _seed(new_goal("g", [crit]), env)
    run_goal_gate({})
    assert sentinel.exists()


# -- the two sides of the protocol ------------------------------------------------------


def test_the_two_sides_agree_on_the_staleness_bound() -> None:
    """🔴 The gate runs Windows-side and the driver WSL-side; they parse the same lock file
    and cannot import each other, so the constant is duplicated by necessity. Duplicated
    constants drift, and this assertion is the only thing that would ever notice."""
    from tools.probe_battery import _lock as driver_lock

    assert _goal_gate.BATTERY_LOCK_STALE_AFTER_S == driver_lock.STALE_AFTER_S


def test_the_two_sides_agree_on_the_default_lock_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Same reasoning, and the more likely drift: a path typo makes the gate watch a file
    the driver never writes, which fails OPEN and silently restores safety hole 1."""
    from tools.probe_battery import _lock as driver_lock

    monkeypatch.delenv("CLAUDE_PROBE_BATTERY_LOCK", raising=False)
    repo_root = Path(_goal_gate.REPO_ROOT)
    assert _goal_gate._battery_lock_path() == driver_lock.lock_path(repo_root)


def test_the_two_sides_agree_on_the_sidecar_name(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The gate writes the tally and the driver reads it; a mismatched suffix would make
    every battery report "0 Stops deferred" no matter how many it actually deferred."""
    from tools.probe_battery import _lock as driver_lock

    monkeypatch.setenv("CLAUDE_PROBE_BATTERY_LOCK", str(tmp_path / "x.lock"))
    gate_side = _goal_gate._battery_lock_path()
    gate_sidecar = gate_side.with_name(gate_side.name + ".defers")
    assert gate_sidecar == driver_lock.defers_path(gate_side)
