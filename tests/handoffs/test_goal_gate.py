"""Tests for ``.claude/hooks/_goal_gate.py`` (PLAN-0021 Step 2).

Matrix rows covered here (the §Verification case-coverage matrix):

- **happy-1** — checks pass + judge PASS verdict -> ``status: "passed"``,
  info ping, ``None`` (stop fires normally)
- **boundary-1** — per-criterion ``timeout_s`` exceeded -> ``timeout``;
  total ``CLAUDE_GOAL_CHECK_BUDGET_S`` exhausted -> ``skipped``; both are
  unresolved -> warn path (never pass, never block)
- **fail-open** — an unanswered dispatch-marker with no new work ->
  ``released-unevaluated`` + loud ping + ``None`` (D4; no wedge)
- **adversarial-2** — poison cmd printing "PASS" but exiting non-zero ->
  fail (exit code is the only truth); shell metacharacters are NOT
  interpreted (argv-not-shell)
- **chain-cap** — fingerprint unchanged after a verdict -> no re-dispatch
  (warn); FAIL verdict + NEW work -> re-dispatch (the fix->re-evaluate loop)
- goal-less / non-active / malformed -> ``None`` with zero side effects
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
    CHECK_FAIL,
    CHECK_INVALID,
    CHECK_PASS,
    CHECK_SKIPPED,
    CHECK_TIMEOUT,
    EVALUATOR_NAME,
    GATE_BLOCKED_MARKER,
    GATE_DISPATCH_MARKER,
    GATE_ENFORCE_BLOCK_MARKER,
    GATE_PASSED_MARKER,
    GATE_RELEASED_MARKER,
    _divergence_decision,
    run_goal_gate,
)
from _goal_state import (  # noqa: E402
    STATUS_ACTIVE,
    STATUS_BLOCKED_PENDING_HUMAN,
    STATUS_PASSED,
    STATUS_RELEASED_UNEVALUATED,
    Amendment,
    Criterion,
    Evaluation,
    Goal,
    load_goal,
    new_goal,
    record_amendment,
    record_evaluation,
    save_goal,
)

PY = sys.executable


def _check_ok(crit_id: str = "C1", timeout_s: int = 30) -> Criterion:
    return Criterion(
        id=crit_id,
        kind="check",
        cmd=f'"{PY}" -c "import sys; sys.exit(0)"',
        desc="always green",
        timeout_s=timeout_s,
    )


def _check_fail(crit_id: str = "C1") -> Criterion:
    return Criterion(
        id=crit_id,
        kind="check",
        cmd=f'"{PY}" -c "import sys; sys.exit(1)"',
        desc="always red",
        timeout_s=30,
    )


def _judge(crit_id: str = "J1") -> Criterion:
    return Criterion(id=crit_id, kind="judge", desc="doc resolves every OQ")


@pytest.fixture
def gate_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, Any]:
    """Isolated goal path + captured Telegram + pinned fingerprint."""
    goal_file = tmp_path / "goal.json"
    monkeypatch.setenv("CLAUDE_GOAL_PATH", str(goal_file))
    monkeypatch.delenv("CLAUDE_GOAL_CHECK_BUDGET_S", raising=False)
    pings: list[tuple[str, str]] = []

    def capture_ping(event: str, goal_text: str, detail: str) -> None:
        pings.append((event, detail))

    monkeypatch.setattr(_goal_gate, "_ping_telegram", capture_ping)
    monkeypatch.setattr(_goal_gate, "work_fingerprint", lambda: "fp-A")
    return {"goal_file": goal_file, "pings": pings, "monkeypatch": monkeypatch}


def _seed(goal: Goal, env: dict[str, Any]) -> None:
    save_goal(goal, env["goal_file"])


def _reload(env: dict[str, Any]) -> Goal:
    loaded = load_goal(env["goal_file"])
    assert loaded is not None
    return loaded


class TestGoalLess:
    def test_no_goal_file_returns_none(self, gate_env: dict[str, Any]) -> None:
        assert run_goal_gate({}) is None
        assert gate_env["pings"] == []

    def test_malformed_goal_file_returns_none(self, gate_env: dict[str, Any]) -> None:
        gate_env["goal_file"].write_text("{broken", encoding="utf-8")
        assert run_goal_gate({}) is None
        assert gate_env["pings"] == []

    @pytest.mark.parametrize("status", [STATUS_PASSED, STATUS_RELEASED_UNEVALUATED])
    def test_non_active_status_returns_none(self, gate_env: dict[str, Any], status: str) -> None:
        goal = new_goal("g", [_check_ok()])
        goal.status = status
        _seed(goal, gate_env)
        assert run_goal_gate({}) is None
        assert gate_env["pings"] == []


class TestHappyPath:
    def test_checks_only_goal_passes(self, gate_env: dict[str, Any]) -> None:
        _seed(new_goal("g", [_check_ok("C1"), _check_ok("C2")]), gate_env)
        assert run_goal_gate({}) is None
        reloaded = _reload(gate_env)
        assert reloaded.status == STATUS_PASSED
        assert reloaded.evaluations[-1].evaluator == GATE_PASSED_MARKER
        assert reloaded.evaluations[-1].deterministic == {"C1": CHECK_PASS, "C2": CHECK_PASS}
        assert [e for e, _ in gate_env["pings"]] == ["passed"]

    def test_checks_plus_judge_pass_verdict_passes(self, gate_env: dict[str, Any]) -> None:
        goal = new_goal("g", [_check_ok(), _judge("J1")])
        record_evaluation(
            goal,
            Evaluation(
                ts="t1",
                fingerprint="fp-A",
                judged={"J1": {"verdict": "PASS", "reason": "ok"}},
                evaluator=EVALUATOR_NAME,
            ),
        )
        _seed(goal, gate_env)
        assert run_goal_gate({}) is None
        assert _reload(gate_env).status == STATUS_PASSED


class TestCheckFailureWarns:
    def test_check_fail_warns_never_blocks(self, gate_env: dict[str, Any]) -> None:
        _seed(new_goal("g", [_check_fail("C1"), _judge("J1")]), gate_env)
        assert run_goal_gate({}) is None  # warn-only: the stop fires
        reloaded = _reload(gate_env)
        assert reloaded.status == STATUS_ACTIVE  # not passed, not released
        events = [e for e, _ in gate_env["pings"]]
        assert events == ["warn"]

    def test_missing_timeout_is_invalid_and_warns(self, gate_env: dict[str, Any]) -> None:
        crit = _check_ok("C1")
        crit.timeout_s = None
        _seed(new_goal("g", [crit]), gate_env)
        assert run_goal_gate({}) is None
        (event, detail), *_ = gate_env["pings"]
        assert event == "warn"
        assert CHECK_INVALID in detail


class TestBoundary:
    def test_per_criterion_timeout(self, gate_env: dict[str, Any]) -> None:
        slow = Criterion(
            id="C1",
            kind="check",
            cmd=f'"{PY}" -c "import time; time.sleep(5)"',
            desc="too slow",
            timeout_s=1,
        )
        _seed(new_goal("g", [slow]), gate_env)
        assert run_goal_gate({}) is None
        (event, detail), *_ = gate_env["pings"]
        assert event == "warn"
        assert CHECK_TIMEOUT in detail

    def test_total_budget_exhaustion_skips(self, gate_env: dict[str, Any]) -> None:
        mp: pytest.MonkeyPatch = gate_env["monkeypatch"]
        mp.setenv("CLAUDE_GOAL_CHECK_BUDGET_S", "1")
        slow = Criterion(
            id="C1",
            kind="check",
            cmd=f'"{PY}" -c "import time; time.sleep(3)"',
            desc="eats the budget",
            timeout_s=30,
        )
        never_run = _check_ok("C2")
        _seed(new_goal("g", [slow, never_run]), gate_env)
        assert run_goal_gate({}) is None
        (event, detail), *_ = gate_env["pings"]
        assert event == "warn"
        assert CHECK_SKIPPED in detail  # C2 never ran: budget exhausted


class TestAdversarial2:
    def test_poison_output_cannot_fake_pass(self, gate_env: dict[str, Any]) -> None:
        poison = Criterion(
            id="C1",
            kind="check",
            cmd=f'"{PY}" -c "print(\'PASS\'); import sys; sys.exit(1)"',
            desc="prints PASS, exits 1",
            timeout_s=30,
        )
        _seed(new_goal("g", [poison]), gate_env)
        assert run_goal_gate({}) is None
        (event, detail), *_ = gate_env["pings"]
        assert event == "warn"
        assert CHECK_FAIL in detail  # exit code is the only truth

    def test_shell_metacharacters_not_interpreted(self, gate_env: dict[str, Any]) -> None:
        """With a shell, `ok-cmd && fail-cmd` would exit 1. Without one, the
        trailing tokens are inert argv to the first command -> exit 0. A PASS
        here proves the gate never spawned a shell."""
        meta = Criterion(
            id="C1",
            kind="check",
            cmd=(f'"{PY}" -c "import sys; sys.exit(0)" && "{PY}" -c "import sys; sys.exit(1)"'),
            desc="metachar probe",
            timeout_s=30,
        )
        _seed(new_goal("g", [meta]), gate_env)
        assert run_goal_gate({}) is None
        assert _reload(gate_env).status == STATUS_PASSED  # `&&` was NOT a shell operator


class TestDispatchFlow:
    def test_unresolved_judge_with_new_work_dispatches(self, gate_env: dict[str, Any]) -> None:
        _seed(new_goal("g", [_check_ok(), _judge("J1")]), gate_env)
        directive = run_goal_gate({})
        assert directive is not None
        assert directive["decision"] == "block"
        assert "GOAL-GATE DISPATCH" in directive["reason"]
        assert "goal-evaluator" in directive["reason"]
        assert "J1" in directive["reason"]
        reloaded = _reload(gate_env)
        assert reloaded.evaluations[-1].evaluator == GATE_DISPATCH_MARKER
        assert reloaded.evaluations[-1].fingerprint == "fp-A"
        assert reloaded.status == STATUS_ACTIVE

    def test_dispatch_payload_carries_d6_contract(self, gate_env: dict[str, Any]) -> None:
        """adversarial-1 (payload-construction half): the spawn instruction
        itself pins the D6 input contract — pointers + machine outputs only,
        narrative success claims disregarded — so the creator cannot narrate
        its way past the critic via the dispatch payload."""
        _seed(new_goal("g", [_check_ok(), _judge("J1")]), gate_env)
        directive = run_goal_gate({})
        assert directive is not None
        reason = directive["reason"]
        assert "disregard natural-language success claims" in reason
        assert "machine outputs" in reason
        assert "do NOT narrate" in reason
        assert "hook-narrowed to goal.json" in reason  # SD-1 stated to the spawner
        assert directive["hookSpecificOutput"] == {"hookEventName": "Stop"}

    def test_fail_verdict_plus_new_work_redispatches(self, gate_env: dict[str, Any]) -> None:
        """The fix -> re-evaluate loop: FAIL is not terminal once work changed."""
        goal = new_goal("g", [_check_ok(), _judge("J1")])
        record_evaluation(
            goal,
            Evaluation(
                ts="t1",
                fingerprint="fp-OLD",
                judged={"J1": {"verdict": "FAIL", "reason": "nope"}},
                evaluator=EVALUATOR_NAME,
            ),
        )
        _seed(goal, gate_env)
        directive = run_goal_gate({})  # fingerprint now fp-A != fp-OLD
        assert directive is not None
        assert _reload(gate_env).evaluations[-1].evaluator == GATE_DISPATCH_MARKER

    def test_chain_cap_row_fingerprint_unchanged_no_redispatch(
        self, gate_env: dict[str, Any]
    ) -> None:
        goal = new_goal("g", [_check_ok(), _judge("J1")])
        record_evaluation(
            goal,
            Evaluation(
                ts="t1",
                fingerprint="fp-A",  # same as the pinned current fingerprint
                judged={"J1": {"verdict": "FAIL", "reason": "nope"}},
                evaluator=EVALUATOR_NAME,
            ),
        )
        _seed(goal, gate_env)
        assert run_goal_gate({}) is None  # warn, no re-dispatch
        events = [e for e, _ in gate_env["pings"]]
        assert events == ["warn"]
        assert _reload(gate_env).status == STATUS_ACTIVE


class TestFailOpen:
    def test_unanswered_dispatch_releases_unevaluated(self, gate_env: dict[str, Any]) -> None:
        """fail-open row: dispatch-marker + no new work + no verdict ->
        released-unevaluated + LOUD ping + stop fires (None, no wedge)."""
        goal = new_goal("g", [_check_ok(), _judge("J1")])
        record_evaluation(
            goal,
            Evaluation(ts="t1", fingerprint="fp-A", evaluator=GATE_DISPATCH_MARKER),
        )
        _seed(goal, gate_env)
        assert run_goal_gate({}) is None
        reloaded = _reload(gate_env)
        assert reloaded.status == STATUS_RELEASED_UNEVALUATED
        assert reloaded.evaluations[-1].evaluator == GATE_RELEASED_MARKER
        (event, detail), *_ = gate_env["pings"]
        assert event == "released_unevaluated"
        assert "WITHOUT evaluation" in detail

    def test_released_goal_then_stands_down(self, gate_env: dict[str, Any]) -> None:
        goal = new_goal("g", [_check_ok(), _judge("J1")])
        record_evaluation(
            goal,
            Evaluation(ts="t1", fingerprint="fp-A", evaluator=GATE_DISPATCH_MARKER),
        )
        _seed(goal, gate_env)
        run_goal_gate({})  # releases
        gate_env["pings"].clear()
        assert run_goal_gate({}) is None  # status != active -> zero delta
        assert gate_env["pings"] == []


class TestNeverRaise:
    def test_gate_returns_none_on_unreadable_goal_dir(
        self, gate_env: dict[str, Any], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Point the override at a directory, not a file:
        monkeypatch.setenv("CLAUDE_GOAL_PATH", str(gate_env["goal_file"].parent))
        assert run_goal_gate({}) is None  # load_goal -> OSError family -> None


class TestFingerprint:
    def test_real_fingerprint_against_repo(self) -> None:
        fp_a = _goal_gate.work_fingerprint()
        fp_b = _goal_gate.work_fingerprint()
        assert fp_a == fp_b  # stable when the tree doesn't change
        assert fp_a == "" or len(fp_a) == 16


# ---------------------------------------------------------------------------
# PLAN-0069 PR2 — the v2 warn→enforce ladder (enforce flag + drift/redirect)
# ---------------------------------------------------------------------------


def _goal_with_divergence(
    amendments_seen: int,
    num_amendments: int,
    verdict: str = "DIVERGENT",
    enforce: bool = True,
) -> Goal:
    """A goal whose latest evaluator entry (at the pinned fp-A, no new work)
    carries a judge FAIL + a divergence verdict recording ``amendments_seen``,
    plus ``num_amendments`` ratifying amendments — the SD-D freshness inputs."""
    goal = new_goal("g", [_check_ok(), _judge("J1")], enforce=enforce)
    record_evaluation(
        goal,
        Evaluation(
            ts="t1",
            fingerprint="fp-A",
            judged={"J1": {"verdict": "FAIL", "reason": "off"}},
            evaluator=EVALUATOR_NAME,
            amendments_seen=amendments_seen,
            divergence={"verdict": verdict, "reason": "off-anchor"},
        ),
    )
    for i in range(num_amendments):
        record_amendment(goal, Amendment(ts=f"a{i}", event="typed", fingerprint=f"fp-am{i}"))
    return goal


class TestEnforceLadder:
    def test_check_fail_blocks_once_then_parks(self, gate_env: dict[str, Any]) -> None:
        """AC-5: enforce:true + an evidence-backed check FAIL -> exactly one
        bounded block, then park at blocked-pending-human on the re-Stop."""
        _seed(new_goal("g", [_check_fail("C1")], enforce=True), gate_env)
        # rung 1 — one bounded block (no ping; a directive, like dispatch)
        directive = run_goal_gate({})
        assert directive is not None
        assert directive["decision"] == "block"
        assert "GOAL-GATE ENFORCE" in directive["reason"]
        assert "blocked-pending-human" in directive["reason"]
        mid = _reload(gate_env)
        assert mid.status == STATUS_ACTIVE
        assert mid.evaluations[-1].evaluator == GATE_ENFORCE_BLOCK_MARKER
        # rung 2 — re-Stop still failing: park (NOT a second block)
        assert run_goal_gate({}) is None
        parked = _reload(gate_env)
        assert parked.status == STATUS_BLOCKED_PENDING_HUMAN
        assert parked.evaluations[-1].evaluator == GATE_BLOCKED_MARKER
        assert [e for e, _ in gate_env["pings"]] == ["blocked_pending_human"]
        # rung 3 — parked status != active: self-quiesce, zero delta
        gate_env["pings"].clear()
        assert run_goal_gate({}) is None
        assert gate_env["pings"] == []

    def test_never_blocks_twice_for_same_state(self, gate_env: dict[str, Any]) -> None:
        """AC-5: the ladder never issues a second block for the same failing
        state — the re-Stop parks."""
        _seed(new_goal("g", [_check_fail("C1")], enforce=True), gate_env)
        d1 = run_goal_gate({})
        assert d1 is not None and d1["decision"] == "block"
        d2 = run_goal_gate({})
        assert d2 is None
        assert _reload(gate_env).status == STATUS_BLOCKED_PENDING_HUMAN

    def test_judge_fail_no_work_blocks_then_parks(self, gate_env: dict[str, Any]) -> None:
        """AC-5 (judge axis): checks green, a recorded judge FAIL with no new
        work -> block then park under enforce."""
        goal = new_goal("g", [_check_ok(), _judge("J1")], enforce=True)
        record_evaluation(
            goal,
            Evaluation(
                ts="t1",
                fingerprint="fp-A",
                judged={"J1": {"verdict": "FAIL", "reason": "nope"}},
                evaluator=EVALUATOR_NAME,
            ),
        )
        _seed(goal, gate_env)
        d1 = run_goal_gate({})
        assert d1 is not None and d1["decision"] == "block"
        assert run_goal_gate({}) is None
        assert _reload(gate_env).status == STATUS_BLOCKED_PENDING_HUMAN


class TestEnforceNeverSilentPass:
    def test_unanswered_dispatch_parks_not_released(self, gate_env: dict[str, Any]) -> None:
        """AC-6 / V2-D4: an unanswered dispatch under enforce parks at
        blocked-pending-human — NEVER released-unevaluated, NEVER passed."""
        goal = new_goal("g", [_check_ok(), _judge("J1")], enforce=True)
        record_evaluation(
            goal,
            Evaluation(ts="t1", fingerprint="fp-A", evaluator=GATE_DISPATCH_MARKER),
        )
        _seed(goal, gate_env)
        assert run_goal_gate({}) is None
        parked = _reload(gate_env)
        assert parked.status == STATUS_BLOCKED_PENDING_HUMAN
        assert parked.status != STATUS_RELEASED_UNEVALUATED
        assert parked.status != STATUS_PASSED
        assert parked.evaluations[-1].evaluator == GATE_BLOCKED_MARKER
        (event, detail), *_ = gate_env["pings"]
        assert event == "blocked_pending_human"
        assert "blocked-pending-human" in detail


class TestDriftRedirect:
    def test_divergence_decision_positional_freshness(self) -> None:
        """AC-7 (pure function): positional freshness, clock-free. Amendment
        AFTER the flag -> redirect; BEFORE or none -> drift; ALIGNED -> none."""
        assert _divergence_decision(_goal_with_divergence(0, 1)) == "redirect"
        assert _divergence_decision(_goal_with_divergence(1, 1)) == "drift"
        assert _divergence_decision(_goal_with_divergence(0, 0)) == "drift"
        assert _divergence_decision(_goal_with_divergence(0, 1, verdict="ALIGNED")) == "none"

    def test_drift_under_enforce_blocks(self, gate_env: dict[str, Any]) -> None:
        """AC-7: unredirected drift under enforce -> the ladder (block)."""
        _seed(_goal_with_divergence(0, 0, enforce=True), gate_env)
        directive = run_goal_gate({})
        assert directive is not None
        assert directive["decision"] == "block"
        assert "DIVERGES" in directive["reason"]

    def test_redirect_passes_freely_no_block(self, gate_env: dict[str, Any]) -> None:
        """AC-7: a divergence explained by a POSITIONALLY fresher amendment ->
        pass freely (no block, no park; the goal stays active)."""
        _seed(_goal_with_divergence(0, 1, enforce=True), gate_env)
        assert run_goal_gate({}) is None
        reloaded = _reload(gate_env)
        assert reloaded.status == STATUS_ACTIVE
        (event, _detail), *_ = gate_env["pings"]
        assert event == "redirect"

    def test_drift_under_enforce_false_warns(self, gate_env: dict[str, Any]) -> None:
        """AC-7 (enforce:false half): drift warns, never blocks — and this path
        only ever fires on a v2 divergence verdict (a v1 replay has none)."""
        _seed(_goal_with_divergence(0, 0, enforce=False), gate_env)
        assert run_goal_gate({}) is None
        (event, detail), *_ = gate_env["pings"]
        assert event == "warn"
        assert "DIVERGES" in detail


class TestEnforceFalseParity:
    def test_enforce_is_the_only_pivot_for_check_fail(self, gate_env: dict[str, Any]) -> None:
        """AC-3: an enforce:false goal takes the EXACT v1 warn path (return
        None, one 'warn' ping with the verbatim v1 detail, status stays
        active) — the flag is the sole difference from the enforce:true ladder
        (proven blocking in TestEnforceLadder)."""
        _seed(new_goal("g", [_check_fail("C1")], enforce=False), gate_env)
        assert run_goal_gate({}) is None
        (event, detail), *_ = gate_env["pings"]
        assert event == "warn"
        assert detail.startswith("checks NOT green:")
        assert detail.endswith("(warn-only, stop fires)")
        assert _reload(gate_env).status == STATUS_ACTIVE
