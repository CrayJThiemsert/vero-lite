"""Goal gate for the Axis-B verification loop (PLAN-0021 Step 2; ADR-0018 D4).

Invoked from ``stop_continuation.py::main()`` at the D4 insertion point —
**after** the chain-cap check, **before** the classifier dispatch — via the
same lazy-import + catch-all wrapper shape as ``_sonnet_classifier`` (the
sibling-module-in-flow precedent). Entrypoint::

    run_goal_gate(payload) -> dict | None

``None`` = fall through to the classifier flow unchanged (the common case —
no active goal costs nothing, AC-2). A dict = a ready-to-print Stop ``block``
directive instructing the main agent to spawn the ``goal-evaluator`` subagent
(the PLAN-0009 Step 5c dispatch-block arm — the hook never spawns).

Control flow (ADR-0018 §spec 2; ordering note: a deterministic ``check``
failure routes to the WARN path per spec step 5's "FAIL verdict recorded
(either layer)" — the evaluator cannot overrule an exit code, so dispatch
fires only when every check passes and judge residue remains):

1. No ``goal.json`` / not ``active`` -> ``None`` (zero delta).
2. Run ``check`` criteria — argv (never shell), per-criterion ``timeout_s``
   (missing -> ``invalid``), total budget ``$CLAUDE_GOAL_CHECK_BUDGET_S``
   (default 600 s; exhausted -> ``skipped``). Unresolved states never pass.
3. All checks pass + all ``judge`` criteria carry a PASS verdict (or none
   exist) -> ``status: "passed"`` + trail entry + Telegram info -> ``None``.
4. Judge residue unresolved + **work since the last trail entry**
   (fingerprint mismatch) -> append a dispatch-marker trail entry + return
   the dispatch directive (counts toward the same chain-cap in M1).
5. Check failure, judge FAIL verdict, or fingerprint unchanged after a
   verdict -> Telegram warn -> ``None`` (D5 warn-only; the stop fires).
6. Fingerprint unchanged after an **unanswered dispatch-marker** (the spawn
   produced no verdict — API dead / spawn failed / malformed verdict) ->
   ``status: "released-unevaluated"`` + trail entry + **loud** Telegram ->
   ``None`` (D4 fail-open; never a wedge).

**Work-state fingerprint** (the re-dispatch guard): sha256 over
``git rev-parse HEAD`` + ``git status --porcelain`` (16 hex chars) — changes
when commits land or the working tree changes; ``goal.json`` itself is
gitignored so gate/evaluator writes never self-trigger. On git failure the
fingerprint is ``""`` and comparisons treat the state as *changed* (fail
toward evaluating, never toward silent release). The ``turn_touched`` marker
was rejected: the L1 turn-boundary reset clears it earlier in the same Stop
flow, before this gate runs.

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
EVALUATOR_NAME = "goal-evaluator"

PASS_VERDICT = "PASS"  # noqa: S105 — verdict label, not a credential

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


# ADR-0018 D6: the spawn-instruction template lives verbatim in-module (the
# _PLAN_DRAFTER_BUDGET_REMINDER precedent) so the dispatch payload contract —
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


def _summarize(results: dict[str, str]) -> str:
    return ", ".join(f"{k}={v}" for k, v in sorted(results.items())) or "(no check criteria)"


def run_goal_gate(payload: dict[str, Any]) -> dict[str, Any] | None:
    """The D4 gate. ``None`` = fall through to the classifier unchanged.

    ``payload`` is accepted for signature parity with ``_classify`` and
    future use; v1 keys off ``goal.json`` state, not the Stop payload.
    """
    del payload  # unused in v1 — see docstring
    goal = load_goal()
    if goal is None or goal.status != STATUS_ACTIVE:
        return None

    deterministic = _run_checks(goal)
    checks_all_pass = all(v == CHECK_PASS for v in deterministic.values())
    judges_all_pass = _judges_all_pass(goal)
    fingerprint = work_fingerprint()
    last = goal.last_evaluation()

    # Step 3 — everything green: goal passed.
    if checks_all_pass and judges_all_pass:
        goal.status = STATUS_PASSED
        record_evaluation(
            goal,
            Evaluation(
                ts=_now_iso(),
                fingerprint=fingerprint,
                deterministic=deterministic,
                evaluator=GATE_PASSED_MARKER,
            ),
        )
        save_goal(goal)
        _ping_telegram("passed", goal.goal, f"checks: {_summarize(deterministic)}; judge: all PASS")
        return None

    # Step 5 (spec "FAIL recorded, either layer") — a deterministic failure is
    # un-arguable; the evaluator cannot overrule an exit code, so no dispatch.
    if not checks_all_pass:
        _ping_telegram(
            "warn",
            goal.goal,
            f"checks NOT green: {_summarize(deterministic)} (warn-only, stop fires)",
        )
        return None

    # Checks green, judge residue needs evaluation (no verdict / FAIL / IE).
    work_changed = not fingerprint or last is None or fingerprint != last.fingerprint
    if work_changed:
        # Step 4 — dispatch the evaluator (marker entry guards re-dispatch).
        record_evaluation(
            goal,
            Evaluation(
                ts=_now_iso(),
                fingerprint=fingerprint,
                deterministic=deterministic,
                evaluator=GATE_DISPATCH_MARKER,
            ),
        )
        save_goal(goal)
        return _dispatch_directive(goal, fingerprint, deterministic)
    if last is not None and last.evaluator == GATE_DISPATCH_MARKER:
        # Step 6 — dispatch went unanswered with no new work: the evaluator
        # path failed (API dead / spawn failure / malformed verdict).
        # FAIL-OPEN: release, loudly (D4).
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
    # Step 5 — judge FAIL / INSUFFICIENT-EVIDENCE recorded and no new work:
    # warn-only; the stop fires (D5).
    _ping_telegram(
        "warn",
        goal.goal,
        "judge residue not PASS and no work since last evaluation (warn-only, stop fires)",
    )
    return None
