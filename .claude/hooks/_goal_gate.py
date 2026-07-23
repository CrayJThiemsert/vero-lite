"""Goal gate for the Axis-B verification loop (PLAN-0021 Step 2; ADR-0018 D4;
PLAN-0069 PR2 = the v2 warn→enforce ladder).

Invoked from ``stop_continuation.py::main()`` at the D4 insertion point —
**after** the chain-cap check, **before** the classifier dispatch — via the
same lazy-import + catch-all wrapper shape as ``_sonnet_classifier`` (the
sibling-module-in-flow precedent). Entrypoint::

    run_goal_gate(payload) -> dict | None

``None`` = fall through to the classifier flow unchanged (the common case —
no active goal costs nothing, AC-2). A dict = a ready-to-print Stop ``block``
directive: either the ``goal-evaluator`` dispatch (v1) or the v2 enforce block
(PLAN-0069 — the hook never spawns and never loops unbounded).

Control flow (ADR-0018 §spec 2; ordering note: a deterministic ``check``
failure routes to the WARN/enforce path per spec step 5's "FAIL verdict
recorded (either layer)" — the evaluator cannot overrule an exit code, so
dispatch fires only when every check passes and judge residue remains):

1. No ``goal.json`` / not ``active`` -> ``None`` (zero delta). A goal parked at
   ``blocked-pending-human`` is not ``active``, so it self-quiesces here.
2. Run ``check`` criteria — argv (never shell), per-criterion ``timeout_s``
   (missing -> ``invalid``), total budget ``$CLAUDE_GOAL_CHECK_BUDGET_S``
   (default 600 s; exhausted -> ``skipped``). Unresolved states never pass.
3. All checks pass + all ``judge`` criteria carry a PASS verdict (or none
   exist) -> ``status: "passed"`` + trail entry + Telegram info -> ``None``.
4. Judge residue unresolved + **work since the last trail entry**
   (fingerprint mismatch) -> append a dispatch-marker trail entry + return
   the dispatch directive (counts toward the same chain-cap in M1).
5. Check failure, judge FAIL verdict, or fingerprint unchanged after a
   verdict -> **warn** (``enforce: false`` — D5 warn-only, the stop fires) OR
   the **enforce ladder** (``enforce: true`` — PLAN-0069 L-3: one bounded block,
   then on re-Stop still failing park at ``blocked-pending-human``).
6. Fingerprint unchanged after an **unanswered dispatch-marker** (the spawn
   produced no verdict — API dead / spawn failed / malformed verdict) ->
   ``status: "released-unevaluated"`` + loud Telegram -> ``None`` (D4 fail-open,
   ``enforce: false``) OR ``status: "blocked-pending-human"`` (``enforce: true``
   — V2-D4: evidence-missing NEVER a silent pass, NEVER released).

**enforce parity (PLAN-0069 AC-3):** every v2 consequence is gated behind
``if goal.enforce``; an ``enforce: false`` goal takes the EXACT v1 branches, so
its return value / status transitions / trail markers / Telegram events are
identical to v1.

**Work-state fingerprint** (the re-dispatch guard): sha256 over
``git rev-parse HEAD`` + ``git status --porcelain`` (16 hex chars) — changes
when commits land or the working tree changes; ``goal.json`` itself is
gitignored so gate/evaluator writes never self-trigger. On git failure the
fingerprint is ``""`` and comparisons treat the state as *changed* (fail
toward evaluating, never toward silent release).

**Drift vs redirect (SD-D, clock-free):** the evaluator may append a
``divergence`` verdict (V2-D2). A DIVERGENT verdict is a *redirect* (passes)
iff a ratifying amendment is POSITIONALLY fresher than it —
``len(amendments) > divergence_entry.amendments_seen`` — because the WSL wall
clock is non-monotonic, so no time ordering. Otherwise it is *drift* (warn /
ladder). Pure function of the parsed artifact — no subprocess, no LLM, no clock.

Never raises into the harness (same catch-all posture as ``_classify``); all
state I/O honors the ``CLAUDE_*`` env-override family for testability.
"""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from _goal_state import (  # noqa: E402  — sys.path manipulation above
    STATUS_ACTIVE,
    STATUS_BLOCKED_PENDING_HUMAN,
    STATUS_PASSED,
    STATUS_RELEASED_UNEVALUATED,
    Criterion,
    Evaluation,
    Goal,
    load_goal,
    record_evaluation,
    save_goal,
)
from _wsl_bridge import bash_argv, env_with_wslenv_passthrough  # noqa: E402

DEFAULT_TELEGRAM_SCRIPT = REPO_ROOT / "tools" / "notify" / "telegram.sh"
DEFAULT_CHECK_BUDGET_S = 600
TELEGRAM_TIMEOUT_SEC = 5

_FORWARDED_ENV = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")

# Trail markers distinguishing gate-written entries from evaluator verdicts.
GATE_DISPATCH_MARKER = "_goal_gate:dispatch"
GATE_PASSED_MARKER = "_goal_gate:passed"
GATE_RELEASED_MARKER = "_goal_gate:released"
# V2 (PLAN-0069): the enforce ladder's two rungs.
GATE_ENFORCE_BLOCK_MARKER = "_goal_gate:enforce_block"
GATE_BLOCKED_MARKER = "_goal_gate:blocked_pending_human"
EVALUATOR_NAME = "goal-evaluator"

PASS_VERDICT = "PASS"  # noqa: S105 — verdict label, not a credential
DIVERGENT_VERDICT = "DIVERGENT"

# Resolved check states. Only "pass" counts as success; every other state is
# unresolved-or-failed and routes to the warn path (never a pass, never a
# block — VX-2).
CHECK_PASS = "pass"  # noqa: S105 — check-state label, not a credential
CHECK_FAIL = "fail"
CHECK_TIMEOUT = "timeout"
CHECK_SKIPPED = "skipped"
CHECK_INVALID = "invalid"
CHECK_ERROR = "error"


def _check_budget_s() -> int:
    raw = os.environ.get("CLAUDE_GOAL_CHECK_BUDGET_S")
    if not raw:
        return DEFAULT_CHECK_BUDGET_S
    try:
        v = int(raw)
        return v if v > 0 else DEFAULT_CHECK_BUDGET_S
    except ValueError:
        return DEFAULT_CHECK_BUDGET_S


def _telegram_script() -> Path:
    override = os.environ.get("CLAUDE_TELEGRAM_SCRIPT")
    return Path(override) if override else DEFAULT_TELEGRAM_SCRIPT


def _now_iso() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S%z")


def _ping_telegram(event: str, goal_text: str, detail: str) -> None:
    """Best-effort Telegram ping (never raises; the gate flow continues).

    Same ``_wsl_bridge`` Pattern-A invocation as ``stop_continuation``'s cap
    ping: formatted body as a single argv element per the ``telegram.sh``
    contract (argv, never stdin).
    """
    script = _telegram_script()
    if not script.exists():
        return
    body = f"[vero-lite/goal_gate_{event}]\ngoal: {goal_text}\n{detail}"
    cmd = bash_argv(script, body)
    env = env_with_wslenv_passthrough(_FORWARDED_ENV)
    try:
        # S603: argv from hook-controlled script path + formatted text; no shell.
        subprocess.run(  # noqa: S603
            cmd,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=TELEGRAM_TIMEOUT_SEC,
        )
    except (subprocess.TimeoutExpired, OSError):
        pass


def work_fingerprint() -> str:
    """Work-state fingerprint: sha256(HEAD + porcelain status), 16 hex chars.

    ``""`` on any git failure — callers treat empty as *changed* (fail toward
    evaluating). ``goal.json`` lives under gitignored ``.claude/state/`` so
    gate/evaluator writes never perturb the fingerprint.
    """
    try:
        head = subprocess.run(  # noqa: S603 — fixed git argv, no shell
            ["git", "rev-parse", "HEAD"],  # noqa: S607 — PATH-resolved git intended
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
        status = subprocess.run(  # noqa: S603 — fixed git argv, no shell
            ["git", "status", "--porcelain"],  # noqa: S607 — PATH-resolved git intended
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (subprocess.TimeoutExpired, OSError):
        return ""
    if head.returncode != 0 or status.returncode != 0:
        return ""
    digest = hashlib.sha256((head.stdout + "\n" + status.stdout).encode("utf-8"))
    return digest.hexdigest()[:16]


def _run_one_check(criterion: Criterion, remaining_budget_s: float) -> str:
    """Run one ``check`` criterion. Exit code is the only truth
    (adversarial-2: argv-not-shell; stdout claiming PASS is ignored).
    """
    if not criterion.cmd.strip():
        return CHECK_INVALID
    if criterion.timeout_s is None:
        return CHECK_INVALID  # VX-2: timeout_s is required for check criteria
    if remaining_budget_s <= 0:
        return CHECK_SKIPPED
    try:
        argv = shlex.split(criterion.cmd)
    except ValueError:
        return CHECK_INVALID
    if not argv:
        return CHECK_INVALID
    timeout = min(float(criterion.timeout_s), remaining_budget_s)
    try:
        # S603: argv from the goal author's declared cmd, intentionally
        # executed WITHOUT a shell so metacharacters never get interpreted.
        proc = subprocess.run(  # noqa: S603
            argv,
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return CHECK_TIMEOUT
    except (OSError, ValueError):
        return CHECK_ERROR
    return CHECK_PASS if proc.returncode == 0 else CHECK_FAIL


def _run_checks(goal: Goal) -> dict[str, str]:
    """Run all ``check`` criteria under the total budget (VX-2)."""
    results: dict[str, str] = {}
    budget = float(_check_budget_s())
    started = time.monotonic()
    for criterion in goal.check_criteria():
        remaining = budget - (time.monotonic() - started)
        results[criterion.id] = _run_one_check(criterion, remaining)
    return results


def _latest_verdicts(goal: Goal) -> dict[str, str]:
    """Latest evaluator verdict per judge-criterion id (newest entry wins)."""
    verdicts: dict[str, str] = {}
    for entry in goal.evaluations:
        if entry.evaluator != EVALUATOR_NAME:
            continue
        for crit_id, verdict in entry.judged.items():
            v = verdict.get("verdict", "")
            if v:
                verdicts[crit_id] = v
    return verdicts


def _judges_all_pass(goal: Goal) -> bool:
    """True iff every ``judge`` criterion carries a PASS verdict (or none
    exist). Anything else — no verdict yet, FAIL, INSUFFICIENT-EVIDENCE —
    means the judge residue still *needs evaluation*: after new work the
    gate re-dispatches (the fix -> re-evaluate loop the fingerprint guard
    exists to allow); with no new work it warns (spec step 5).
    """
    judges = goal.judge_criteria()
    if not judges:
        return True
    verdicts = _latest_verdicts(goal)
    return all(verdicts.get(c.id, "") == PASS_VERDICT for c in judges)


def _divergence_decision(goal: Goal) -> str:
    """SD-D drift/redirect — a PURE, clock-free function over the parsed goal.

    Looks at the latest evaluator entry carrying a ``divergence`` verdict:

      - no such entry, or the latest is ``ALIGNED`` -> ``"none"``
      - ``DIVERGENT`` with a POSITIONALLY fresher ratifying amendment
        (``len(amendments) > entry.amendments_seen``) -> ``"redirect"`` (a typed
        Cray sign-off updated the anchor AFTER the flag — deliberate, passes)
      - ``DIVERGENT`` with no fresher amendment -> ``"drift"``

    Positional (``amendments_seen``), never wall-clock: the WSL clock is
    non-monotonic, so time ordering is barred (SD-D).
    """
    latest: Evaluation | None = None
    for entry in goal.evaluations:
        if entry.divergence and entry.divergence.get("verdict"):
            latest = entry
    if latest is None or latest.divergence is None:
        return "none"
    if latest.divergence.get("verdict") != DIVERGENT_VERDICT:
        return "none"
    return "redirect" if len(goal.amendments) > latest.amendments_seen else "drift"


# ADR-0018 D6: the spawn-instruction template lives verbatim in-module (the
# precedent was stop_continuation's _PLAN_DRAFTER_BUDGET_REMINDER, since
# removed with the classifier dispatch arm's demotion — PLAN-0092) so the
# dispatch payload contract —
# pointers + machine outputs only; narration is not evidence — is fixed here,
# not improvised per call.
_EVALUATOR_DISPATCH_TEMPLATE = (
    "GOAL-GATE DISPATCH (ADR-0018 D4 / PLAN-0021). The active goal has "
    "unresolved judge criteria and work has occurred since the last "
    "evaluation. Spawn the `goal-evaluator` subagent via the Agent tool "
    "with a payload containing ONLY pointers + machine outputs:\n"
    "  - goal_path: {goal_path}\n"
    "  - fingerprint: {fingerprint}\n"
    "  - deterministic_results: {deterministic}\n"
    "  - unresolved_judge_ids: {judge_ids}\n"
    "  - evidence_pointers: cite file paths / `git diff --stat` summaries "
    "only — do NOT narrate what you did or claim success in prose; the "
    "evaluator is instructed to disregard natural-language success claims "
    "and judge ONLY from disk evidence (ADR-0018 D6).\n\n"
    "The evaluator returns per-criterion PASS / FAIL / INSUFFICIENT-EVIDENCE "
    "and appends its verdict to the goal file's evaluations[] trail itself "
    "(its Write is hook-narrowed to goal.json — SD-1). Do NOT transcribe or "
    "edit its verdict. Do NOT commit anything on its behalf.\n\n"
    "Override clause: if you believe this dispatch is misrouted (no goal "
    "work actually happened, or the goal is stale), do NOT spawn — state the "
    "misroute in a short reply so Cray can review; the gate re-arms on the "
    "next Stop."
)

# PLAN-0069 L-3: the ONE bounded enforce block. Fixed in-module (same posture as
# the dispatch template). States the failing criteria verbatim and the two exits
# — remediate, or obtain a TYPED Cray sign-off recorded as an amendment. A
# Stop-hook "proceed" or the agent's own inference is NOT a ratification.
_ENFORCE_BLOCK_TEMPLATE = (
    "GOAL-GATE ENFORCE (ADR-0018 V2 / PLAN-0069 L-3). The active goal is "
    "enforce:true and is NOT satisfied:\n"
    "  {detail}\n\n"
    "Two ways forward:\n"
    "  1. Remediate the failing criteria, then Stop again.\n"
    "  2. If this divergence is a DELIBERATE redirect, obtain a TYPED Cray "
    "sign-off and record it as an amendment (`/goal` amend) — a Stop-hook "
    '"proceed" or your own inference is NOT a ratification.\n\n'
    "This is ONE bounded block. On the next Stop still failing (or under "
    "chain-cap pressure), the Stop fires and the goal parks at "
    "blocked-pending-human — a human must clear, re-declare, or ratify. "
    "Never an unbounded loop.\n\n"
    "Override clause: if this is misrouted (the goal is stale or the failure "
    "is spurious), say so in a short reply so Cray can review."
)


def _dispatch_directive(
    goal: Goal, fingerprint: str, deterministic: dict[str, str]
) -> dict[str, Any]:
    from _goal_state import goal_path

    judge_ids = [c.id for c in goal.judge_criteria()]
    instruction = _EVALUATOR_DISPATCH_TEMPLATE.format(
        goal_path=str(goal_path()),
        fingerprint=fingerprint or "(unavailable)",
        deterministic=json.dumps(deterministic, sort_keys=True),
        judge_ids=", ".join(judge_ids),
    )
    return {
        "decision": "block",
        "reason": instruction,
        "hookSpecificOutput": {"hookEventName": "Stop"},
    }


def _last_was_enforce_block(goal: Goal) -> bool:
    """True iff the last trail entry is the enforce-block marker — i.e. this
    Stop is the re-Stop AFTER a block was already issued for a failing state.
    The ladder's bound: a block is issued at most once per failing state (the
    marker is the last entry only until new work re-dispatches), so the next
    failing Stop parks instead of re-blocking (AC-5: never blocks twice for the
    same state)."""
    last = goal.last_evaluation()
    return last is not None and last.evaluator == GATE_ENFORCE_BLOCK_MARKER


def _issue_enforce_block(
    goal: Goal, fingerprint: str, deterministic: dict[str, str], detail: str
) -> dict[str, Any]:
    """Ladder rung 1 — record the block marker (so the next Stop parks even if
    chain-cap pressure suppresses this directive) and return the block."""
    record_evaluation(
        goal,
        Evaluation(
            ts=_now_iso(),
            fingerprint=fingerprint,
            deterministic=deterministic,
            amendments_seen=len(goal.amendments),
            evaluator=GATE_ENFORCE_BLOCK_MARKER,
        ),
    )
    save_goal(goal)
    return {
        "decision": "block",
        "reason": _ENFORCE_BLOCK_TEMPLATE.format(detail=detail),
        "hookSpecificOutput": {"hookEventName": "Stop"},
    }


def _park_blocked_pending_human(
    goal: Goal, fingerprint: str, deterministic: dict[str, str], detail: str
) -> None:
    """Ladder rung 2 / V2-D4 — transition to ``blocked-pending-human`` + a loud
    Telegram. NEVER a silent pass, NEVER ``released-unevaluated`` under enforce.
    The parked status is not ``active``, so the gate self-quiesces on the next
    Stop until a human clears / re-declares / ratifies."""
    goal.status = STATUS_BLOCKED_PENDING_HUMAN
    record_evaluation(
        goal,
        Evaluation(
            ts=_now_iso(),
            fingerprint=fingerprint,
            deterministic=deterministic,
            amendments_seen=len(goal.amendments),
            evaluator=GATE_BLOCKED_MARKER,
        ),
    )
    save_goal(goal)
    _ping_telegram(
        "blocked_pending_human",
        goal.goal,
        f"LOUD: goal PARKED at blocked-pending-human under enforce — {detail}. "
        "A human must clear, re-declare, or ratify (a Stop-hook proceed is not enough).",
    )


def _failing_consequence(
    goal: Goal, fingerprint: str, deterministic: dict[str, str], detail: str
) -> dict[str, Any] | None:
    """The consequence for a failing state (a check failed, OR judge residue /
    unredirected drift with no new work): the enforce ladder (block once via
    rung 1, then park via rung 2) under ``enforce: true``, else warn-only (v1 —
    the stop fires). Returns a block directive, or ``None``."""
    if goal.enforce:
        if _last_was_enforce_block(goal):
            _park_blocked_pending_human(goal, fingerprint, deterministic, detail)
            return None
        return _issue_enforce_block(goal, fingerprint, deterministic, detail)
    _ping_telegram("warn", goal.goal, f"{detail} (warn-only, stop fires)")
    return None


def _summarize(results: dict[str, str]) -> str:
    return ", ".join(f"{k}={v}" for k, v in sorted(results.items())) or "(no check criteria)"


def run_goal_gate(payload: dict[str, Any]) -> dict[str, Any] | None:
    """The D4 gate. ``None`` = fall through to the classifier unchanged.

    ``payload`` is accepted for signature parity with ``_classify`` and
    future use; the gate keys off ``goal.json`` state, not the Stop payload.
    """
    del payload  # unused — see docstring
    goal = load_goal()
    if goal is None or goal.status != STATUS_ACTIVE:
        return None

    deterministic = _run_checks(goal)
    checks_all_pass = all(v == CHECK_PASS for v in deterministic.values())
    judges_all_pass = _judges_all_pass(goal)
    fingerprint = work_fingerprint()
    last = goal.last_evaluation()

    # Step 3 — everything green: goal passed. (drift is only assessable once a
    # divergence verdict exists; a "drift" reading here means judge residue is
    # not truly clean, so it is handled in the failing paths below.)
    if checks_all_pass and judges_all_pass and _divergence_decision(goal) != "drift":
        goal.status = STATUS_PASSED
        record_evaluation(
            goal,
            Evaluation(
                ts=_now_iso(),
                fingerprint=fingerprint,
                deterministic=deterministic,
                amendments_seen=len(goal.amendments),
                evaluator=GATE_PASSED_MARKER,
            ),
        )
        save_goal(goal)
        _ping_telegram("passed", goal.goal, f"checks: {_summarize(deterministic)}; judge: all PASS")
        return None

    # Step 5 (spec "FAIL recorded, either layer") — a deterministic failure is
    # un-arguable; the evaluator cannot overrule an exit code, so no dispatch.
    if not checks_all_pass:
        return _failing_consequence(
            goal, fingerprint, deterministic, f"checks NOT green: {_summarize(deterministic)}"
        )

    # Checks green, judge residue needs evaluation (no verdict / FAIL / IE /
    # unredirected drift).
    work_changed = not fingerprint or last is None or fingerprint != last.fingerprint
    if work_changed:
        # Step 4 — dispatch the evaluator (marker entry guards re-dispatch).
        # Dispatch is enforce-agnostic: enforcement needs a verdict first.
        record_evaluation(
            goal,
            Evaluation(
                ts=_now_iso(),
                fingerprint=fingerprint,
                deterministic=deterministic,
                amendments_seen=len(goal.amendments),
                evaluator=GATE_DISPATCH_MARKER,
            ),
        )
        save_goal(goal)
        return _dispatch_directive(goal, fingerprint, deterministic)

    if last is not None and last.evaluator == GATE_DISPATCH_MARKER:
        # Step 6 — dispatch went unanswered with no new work: the evaluator
        # path failed (API dead / spawn failure / malformed verdict).
        detail = (
            "evaluator dispatch produced no verdict (API/spawn failure?); "
            f"checks: {_summarize(deterministic)}"
        )
        if goal.enforce:
            # V2-D4: evidence-missing under enforce PARKS — never released.
            _park_blocked_pending_human(goal, fingerprint, deterministic, detail)
            return None
        # FAIL-OPEN: release, loudly (D4, enforce:false).
        goal.status = STATUS_RELEASED_UNEVALUATED
        record_evaluation(
            goal,
            Evaluation(
                ts=_now_iso(),
                fingerprint=fingerprint,
                deterministic=deterministic,
                evaluator=GATE_RELEASED_MARKER,
            ),
        )
        save_goal(goal)
        _ping_telegram(
            "released_unevaluated",
            goal.goal,
            "LOUD: goal released WITHOUT evaluation — the evaluator "
            "dispatch produced no verdict (API/spawn failure?). "
            f"checks: {_summarize(deterministic)}",
        )
        return None

    # Step 5 — judge FAIL / INSUFFICIENT-EVIDENCE / unredirected drift recorded
    # and no new work. (A v2 divergence verdict cannot occur in a pure v1
    # replay, so enforce:false preserves v1 behavior exactly.)
    decision = _divergence_decision(goal)
    if goal.enforce and decision == "redirect":
        # A typed ratification post-dates the divergence flag: pass freely (the
        # anchor is already updated; the stale verdict does not park).
        _ping_telegram(
            "redirect",
            goal.goal,
            "divergence explained by a fresher ratified amendment — passing freely",
        )
        return None
    detail = (
        "work DIVERGES from the goal anchor with no ratifying amendment (drift)"
        if decision == "drift"
        else "judge residue not PASS and no work since last evaluation"
    )
    return _failing_consequence(goal, fingerprint, deterministic, detail)
