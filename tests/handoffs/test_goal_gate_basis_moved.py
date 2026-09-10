"""PLAN-0123 AC-3 (SD-2 = c) — a HEAD-pinned check after HEAD moved reads ``basis-moved``.

🔴 **The s289 finding this closes.** A goal declared before a PR merge carried a check of
the form ``git show <sha>:<path>``. After the merge HEAD moved; the pinned object was
gone; the check failed at four consecutive Stops, and each failure was recorded as a
DEFECT in an append-only trail — teaching the wrong lesson, that a gate which reliably
fails after success is noise. Cray ruled (typed, s289) the declarative eighth check
state: a check whose ``cmd`` matches ``git show <rev>:`` **and** whose goal's
``declared_head`` differs from the current HEAD reads ``basis-moved`` rather than
``fail`` — no ladder, no defect in the trail, one ping naming the moved basis, goal
stays ``active``.

**Detection is declarative, never inferential.** The state is assigned from the
command's *shape* plus a *declared* sha — never from "it failed after a commit". A
tree-basis check that fails after HEAD moved is a real failure and stays ``fail``
(A2). That is what keeps this from masking a regression, and it is the assertion
probe P3b exists to redden.

The RED today is honest by construction: the goal file is written through the real
serializer and then given ``declared_head`` by hand (today's ``to_json`` would strip
it — G12, the reason the field must be first-class); ``_current_head`` is planted with
``raising=False`` so the first run reaches A1 and reads ``C1: fail`` instead of dying
on AttributeError. Three functions, one assertion each, so each probe reddens exactly
one node id.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

import _goal_gate  # noqa: E402  — sys.path manipulation above
from _goal_gate import GATE_ENFORCE_BLOCK_MARKER, run_goal_gate  # noqa: E402
from _goal_state import (  # noqa: E402
    STATUS_ACTIVE,
    Criterion,
    Goal,
    load_goal,
    new_goal,
    save_goal,
)

PY = sys.executable
#: X — the basis the goal was declared against. Not a real object; `git show X:...`
#: exits 128, which is exactly the shape the s289 goal produced after its merge.
DECLARED_HEAD = "1111111111111111111111111111111111111111"
#: Y — where HEAD is now. Anything != X.
CURRENT_HEAD = "2222222222222222222222222222222222222222"
BASIS_MOVED = "basis-moved"


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, Any]:
    """Isolated goal path + captured Telegram + pinned fingerprint + pinned HEAD."""
    goal_file = tmp_path / "goal.json"
    monkeypatch.setenv("CLAUDE_GOAL_PATH", str(goal_file))
    monkeypatch.delenv("CLAUDE_GOAL_CHECK_BUDGET_S", raising=False)
    monkeypatch.setenv("CLAUDE_PROBE_BATTERY_LOCK", str(tmp_path / "no-such-battery.lock"))
    pings: list[tuple[str, str]] = []
    monkeypatch.setattr(_goal_gate, "_ping_telegram", lambda e, _g, d: pings.append((e, d)))
    monkeypatch.setattr(_goal_gate, "work_fingerprint", lambda: "fp-A")
    # The basis the gate compares declared_head against. raising=False: today no such
    # hook exists, and the honest first RED is at A1 (`C1: fail`), not an AttributeError.
    monkeypatch.setattr(_goal_gate, "_current_head", lambda: CURRENT_HEAD, raising=False)
    return {"goal_file": goal_file, "pings": pings}


def _seed(env: dict[str, Any], *, enforce: bool, tree_check_exit: int) -> None:
    goal = new_goal(
        "basis-moved fixture",
        [
            Criterion(
                id="C1",
                kind="check",
                cmd=f"git show {DECLARED_HEAD}:some/path",
                desc="HEAD-pinned (the s289 shape)",
                timeout_s=20,
            ),
            Criterion(
                id="C2",
                kind="check",
                cmd=f'"{PY}" -c "import sys; sys.exit({tree_check_exit})"',
                desc="tree-basis",
                timeout_s=20,
            ),
        ],
        enforce=enforce,
    )
    save_goal(goal, env["goal_file"])
    # Written by hand, on purpose: the real serializer must learn this field (G12).
    doc = json.loads(env["goal_file"].read_text(encoding="utf-8"))
    doc["declared_head"] = DECLARED_HEAD
    env["goal_file"].write_text(json.dumps(doc), encoding="utf-8")


def _reload(env: dict[str, Any]) -> Goal:
    loaded = load_goal(env["goal_file"])
    assert loaded is not None
    return loaded


def _report(env: dict[str, Any], goal: Goal) -> dict[str, str]:
    last = goal.evaluations[-1] if goal.evaluations else None
    states = dict(last.deterministic) if last is not None else {}
    ladder_rung = sum(1 for e in goal.evaluations if e.evaluator == GATE_ENFORCE_BLOCK_MARKER)
    marker = last.evaluator if last is not None else None
    print(
        f"head={CURRENT_HEAD[:7]} declared={DECLARED_HEAD[:7]} states={states} "
        f"ladder_rung={ladder_rung} trail_marker={marker} status={goal.status} "
        f"pings={[e for e, _ in env['pings']]}"
    )
    return states


def test_a1_a_head_pinned_check_after_head_moved_reads_basis_moved(env: dict[str, Any]) -> None:
    _seed(env, enforce=False, tree_check_exit=1)
    run_goal_gate({})
    states = _report(env, _reload(env))
    # A1 — declared shape + moved basis => basis-moved, not fail.
    assert states.get("C1") == BASIS_MOVED, f"C1={states.get('C1')}"


def test_a2_a_tree_basis_check_is_not_reclassified(env: dict[str, Any]) -> None:
    _seed(env, enforce=False, tree_check_exit=1)
    run_goal_gate({})
    states = _report(env, _reload(env))
    # A2 — a real failure after HEAD moved is still a failure. This is the assertion
    # that keeps basis-moved from masking a regression (probe P3b reddens it).
    assert states.get("C2") == "fail", f"C2={states.get('C2')}"


def test_a3_basis_moved_alone_never_advances_the_enforce_ladder(env: dict[str, Any]) -> None:
    _seed(env, enforce=True, tree_check_exit=0)
    returned = run_goal_gate({})
    goal = _reload(env)
    _report(env, goal)
    ladder_rung = sum(1 for e in goal.evaluations if e.evaluator == GATE_ENFORCE_BLOCK_MARKER)
    # A3 — like `contended`: no ladder, goal stays active, the stop falls through.
    assert ladder_rung == 0, f"ladder_rung={ladder_rung}"
    assert goal.status == STATUS_ACTIVE, f"status={goal.status}"
    assert returned is None, f"returned={returned!r}"
