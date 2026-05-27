#!/usr/bin/env python3
"""Stop hook — turn-boundary L1 reset + chain-cap fail-safe + auto-handoff
dispatch (PLAN-0008 Step 4 + PLAN-0009 Step 5c-1).

Fires on every ``Stop`` event. Three responsibilities:

1. **Turn-boundary reset (priority).** Reads ``turn_touched`` from the
   loop-counter state file (recorded by Step 3's
   ``posttooluse_progress_observer.py`` on each Write/Edit) and resets
   L1 counters whose targets were NOT touched this turn. Implements
   the "target untouched on the next turn-boundary marker" rule from
   PLAN §Step 1 / §Step 3. **Closes the 🔴 L1 reset gap** surfaced in
   the L1/L4 asymmetry ELI-CTO (Cray's iterative STATUS-editing
   workflow would otherwise false-positive at 6 edits per session).
2. **Chain-cap fail-safe (PLAN §Step 4).** Tracks consecutive
   ``proceed`` / ``dispatch`` decisions in ``.claude/state/stop-chain.json``
   against ``$CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`` (default 8). On cap-hit:
   emits no block (lets the stop fire), pings Telegram with
   ``"cap reached"`` per OQ-E option (b), and resets the chain.
   Re-entry guarded by the harness ``stop_hook_active`` flag.
3. **Auto-handoff dispatch (PLAN-0009 Step 5c-1).** When the Sonnet
   classifier returns ``decision == "dispatch"`` (governance-drafting
   need matching a D-row in the registry), the hook emits a ``block``
   directive whose ``reason`` instructs the main Code agent to spawn
   the ``plan-drafter`` subagent via the Step 4 §1 R4 routing + §5
   budget reminder template. The main agent invokes the ``Agent`` tool
   on its next turn (the hook itself cannot spawn — only the main
   agent in its own loop can). Counts toward chain-cap same as
   ``proceed`` (a dispatch is semantically a continuation + instruction).

The Sonnet pause/proceed/dispatch classifier is invoked via
``_sonnet_classifier.classify`` (PLAN §Step 5 + PLAN-0009 Step 5c-1).
The classifier reads ``.claude/autonomy-triggers.md`` verbatim, calls
the Anthropic Messages API (stdlib urllib), parses JSON, and is
fail-closed: any infrastructure failure returns ``pause``. The hook
flow here therefore never mis-proceeds because of an API outage, and
never mis-dispatches on malformed dispatch metadata (the classifier
demotes a bad dispatch to ``pause`` before returning).

State file paths and Telegram script honor the env-var overrides
shared with Step 2/3 for testability
(``CLAUDE_LOOP_COUNTER_PATH``, ``CLAUDE_TELEGRAM_SCRIPT``,
``CLAUDE_STOP_CHAIN_PATH``, ``CLAUDE_CODE_STOP_HOOK_BLOCK_CAP``).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from _loop_counter import (  # noqa: E402  — sys.path manipulation above
    DEFAULT_COUNTER_PATH,
    STATE_DIR,
    clear_turn_touched,
    load_counter,
    reset_untouched_l1,
    save_counter,
)
from _wsl_bridge import bash_argv, env_with_wslenv_passthrough  # noqa: E402

DEFAULT_TELEGRAM_SCRIPT = REPO_ROOT / "tools" / "notify" / "telegram.sh"
DEFAULT_CHAIN_PATH = STATE_DIR / "stop-chain.json"
DEFAULT_CAP = 8
TELEGRAM_TIMEOUT_SEC = 5

_FORWARDED_ENV = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")


def _state_path() -> Path:
    override = os.environ.get("CLAUDE_LOOP_COUNTER_PATH")
    return Path(override) if override else DEFAULT_COUNTER_PATH


def _chain_path() -> Path:
    override = os.environ.get("CLAUDE_STOP_CHAIN_PATH")
    return Path(override) if override else DEFAULT_CHAIN_PATH


def _telegram_script() -> Path:
    override = os.environ.get("CLAUDE_TELEGRAM_SCRIPT")
    return Path(override) if override else DEFAULT_TELEGRAM_SCRIPT


def _cap() -> int:
    raw = os.environ.get("CLAUDE_CODE_STOP_HOOK_BLOCK_CAP")
    if not raw:
        return DEFAULT_CAP
    try:
        v = int(raw)
        return v if v > 0 else DEFAULT_CAP
    except ValueError:
        return DEFAULT_CAP


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S%z")


def _load_chain() -> dict[str, Any]:
    p = _chain_path()
    if not p.exists():
        return {"depth": 0, "last_proceed_ts": ""}
    try:
        data = json.loads(p.read_text(encoding="utf-8") or "{}")
    except (OSError, json.JSONDecodeError):
        return {"depth": 0, "last_proceed_ts": ""}
    if not isinstance(data, dict):
        return {"depth": 0, "last_proceed_ts": ""}
    depth = data.get("depth", 0)
    return {
        "depth": depth if isinstance(depth, int) else 0,
        "last_proceed_ts": str(data.get("last_proceed_ts", "")),
    }


def _save_chain(data: dict[str, Any]) -> None:
    p = _chain_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, sort_keys=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(p.parent),
        delete=False,
        prefix=p.name + ".",
        suffix=".tmp",
    ) as tmp:
        tmp.write(payload)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, p)


def _reset_chain() -> None:
    _save_chain({"depth": 0, "last_proceed_ts": ""})


def _format_cap_message(payload: dict[str, Any]) -> str:
    """Build the human-readable Telegram body from the cap-reached payload."""
    event = str(payload.get("event") or "stop_continuation_event")
    depth = payload.get("depth", "?")
    cap = payload.get("cap", "?")
    ts = str(payload.get("ts") or "")
    reason = str(payload.get("reason") or "").strip()
    return f"[vero-lite/{event}] depth={depth} / cap={cap}\n" f"ts: {ts}\n" f"{reason}"


def _ping_telegram(message: dict[str, Any]) -> None:
    """Best-effort Telegram ping. Never raises; the hook flow continues.

    Cross-platform invocation + WSLENV passthrough delegated to
    :mod:`_wsl_bridge` (Pattern A). The formatted message is delivered as a
    single argv element (per ``telegram.sh`` contract — argv, never stdin).
    """
    script = _telegram_script()
    if not script.exists():
        return
    body = _format_cap_message(message)
    cmd = bash_argv(script, body)
    env = env_with_wslenv_passthrough(_FORWARDED_ENV)

    try:
        # S603: cmd elements come from hook-controlled script path
        # (constant or env-override) + the formatted message; no shell
        # interpolation.
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


def _apply_turn_boundary_reset() -> list[str]:
    """Read state, reset untouched L1 counters, clear turn_touched.

    Returns the list of L1 targets that were reset (informational —
    Step 4 does not fire Telegram for reset events; they are by
    definition healthy progress signals).
    """
    counter = load_counter(_state_path())
    reset_targets = reset_untouched_l1(counter)
    clear_turn_touched(counter)
    save_counter(counter, _state_path())
    return reset_targets


def _classify(payload: dict[str, Any]) -> dict[str, Any]:
    """Dispatch to the Sonnet classifier with fail-closed pause.

    Imports lazily so a missing ``_sonnet_classifier`` module (unlikely
    in production, but defensive) does not break the hook flow. Any
    transport or schema error inside ``classify()`` is already
    converted to a pause by the helper — this wrapper adds a final
    catch-all so the Stop hook can never raise into the harness.
    """
    try:
        from _sonnet_classifier import classify  # local import: tolerant to absence
    except ImportError as exc:
        return {
            "decision": "pause",
            "matched_rows": [],
            "reason": f"classifier helper unavailable: {exc}",
        }
    try:
        return classify(payload)
    except Exception as exc:  # final safety net; helper should already fail-closed
        return {
            "decision": "pause",
            "matched_rows": [],
            "reason": f"classifier raised unexpectedly: {exc}",
        }


def _proceed_block(reason: str) -> dict[str, Any]:
    """`decision: block` on Stop = continuation loop (per Anthropic
    stop-hook docs: blocking returns the agent to the loop).
    """
    return {
        "decision": "block",
        "reason": reason,
        "hookSpecificOutput": {"hookEventName": "Stop"},
    }


# PLAN-0009 Step 4 §5 budget reminder template (verbatim) — kept in this
# module so the dispatch instruction is self-contained. If Step 4 §5 is
# ever edited, mirror the change here AND update test_stop_continuation
# fixtures asserting the template content.
_PLAN_DRAFTER_BUDGET_REMINDER = (
    "OUTPUT BUDGET REMINDER: per the plan-drafter output schema, your "
    "final message should be ≤ 1k tokens total — use the artifact-path-"
    "only pattern (cite the path you wrote; do NOT inline the artifact "
    "body). The disclosure stamp and surfaced-decisions section are "
    "mandatory; do not silently downgrade either."
)


def _build_dispatch_instruction(
    dispatch: dict[str, str],
    matched_rows: list[str],
    classifier_reason: str,
) -> str:
    """Build the continuation instruction the main agent reads on its next turn.

    The instruction encodes:
    * **Why** dispatch fired (matched D-rows + classifier reason)
    * **What** subagent to spawn + artifact_kind + task_summary
    * **Pre-spawn** discipline (enumerate ``docs/{adr,plans}/`` first
      to pick a free ``NNNN``) per Step 4 §4 "Pre-spawn validation"
    * **Budget reminder** verbatim from Step 4 §5
    * **Commit boundary** reminder: subagent cannot commit; main agent
      handles PR-flow per CLAUDE.md §7
    * **Override** clause: if the agent's judgment differs from the
      classifier (e.g., the dispatch is misrouted), fall back to a
      plain pause (do NOT spawn) — the classifier is conservative-by-
      default but the main agent owns the final routing call.
    """
    subagent = dispatch["subagent"]
    artifact_kind = dispatch["artifact_kind"]
    task_summary = dispatch["task_summary"]
    matched_str = ", ".join(matched_rows) if matched_rows else "(none cited)"
    artifact_dir = "docs/adr" if artifact_kind == "adr" else "docs/plans"

    return (
        f"AUTO-HANDOFF DISPATCH (PLAN-0009 Step 5c). The classifier "
        f"matched {matched_str} and identified a governance-drafting need:\n"
        f'  "{classifier_reason}"\n\n'
        f"Per Step 4 §1 R4 routing, spawn the `{subagent}` subagent via "
        f"the Agent tool with the following parameters:\n"
        f"  - subagent_type: {subagent}\n"
        f"  - artifact_kind: {artifact_kind}\n"
        f"  - task_summary: {task_summary}\n\n"
        f"Pre-spawn discipline (Step 4 §4):\n"
        f"  1. Enumerate `{artifact_dir}/` to pick the next free NNNN; pass "
        f"it down as target_number (subagent does NOT enumerate).\n"
        f"  2. Construct scoped_context from prior explore-research findings "
        f"or facts already in your context — do NOT inline full file contents "
        f"(the subagent has Read).\n"
        f"  3. Include the budget reminder verbatim in the dispatch payload:\n\n"
        f"{_PLAN_DRAFTER_BUDGET_REMINDER}\n\n"
        f"Post-spawn discipline (Step 4 §3):\n"
        f"  - The subagent returns a final message with the artifact path + "
        f"a bounded summary. Reference the path in your reply; do NOT echo "
        f"the artifact body.\n"
        f"  - YOU commit the draft via PR per CLAUDE.md §7. The subagent "
        f"cannot commit (G5 binds — composed identity gate denies any git "
        f"op from a subagent regardless of CLAUDE_TIER inheritance).\n\n"
        f"Override clause: if you believe the classifier misrouted this "
        f"(e.g., the task is not actually governance-drafting, or no D-row "
        f"actually fits), do NOT spawn — instead, surface the misroute in a "
        f"short reply so Cray can review the trigger. Spurious dispatches "
        f"are worse than spurious pauses (they consume a subagent spawn)."
    )


def _cap_reached_payload(depth: int, cap: int) -> dict[str, Any]:
    return {
        "event": "stop_continuation_cap_reached",
        "depth": depth,
        "cap": cap,
        "ts": _now_iso(),
        "reason": (
            f"Stop hook chain depth {depth} reached cap {cap}. "
            "Releasing agent to Cray (no block). Chain counter reset."
        ),
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # fail-open

    # Re-entry guard: if the harness reports we are already inside a
    # stop-hook chain, do not re-enter (no reset, no classifier dispatch,
    # no chain increment). Let the stop fire normally.
    if payload.get("stop_hook_active") is True:
        return 0

    # Always run the turn-boundary reset first — it is independent of the
    # chain-cap / classifier flow and is the load-bearing Step 4 benefit.
    try:
        _apply_turn_boundary_reset()
    except Exception as exc:  # observer must not block on internal errors
        print(f"stop_continuation: turn-boundary reset failed: {exc}", file=sys.stderr)

    # Chain-cap fail-safe (OQ-E option b).
    cap = _cap()
    chain = _load_chain()
    if chain["depth"] >= cap:
        _ping_telegram(_cap_reached_payload(chain["depth"], cap))
        _reset_chain()
        return 0  # do not block; let Cray see the stop event

    # Classifier dispatch (real Sonnet via _sonnet_classifier, fail-closed pause).
    decision = _classify(payload)
    verdict = decision.get("decision")

    if verdict == "proceed":
        chain["depth"] += 1
        chain["last_proceed_ts"] = _now_iso()
        _save_chain(chain)
        print(json.dumps(_proceed_block(decision.get("reason", "continue"))))
        return 0

    if verdict == "dispatch":
        # PLAN-0009 Step 5c-1 auto-handoff arm. Defensive: the classifier
        # already validates dispatch metadata + fails closed to pause on any
        # schema violation, but if a malformed dispatch reaches here (e.g.,
        # future classifier-helper regression), demote to pause locally so
        # the hook never emits a malformed instruction.
        dispatch_meta = decision.get("dispatch")
        if not isinstance(dispatch_meta, dict):
            _reset_chain()
            return 0
        matched_rows_raw = decision.get("matched_rows") or []
        matched_rows = [str(r) for r in matched_rows_raw if isinstance(matched_rows_raw, list)]
        classifier_reason = decision.get("reason", "")
        instruction = _build_dispatch_instruction(
            dispatch_meta,
            matched_rows,
            str(classifier_reason),
        )
        chain["depth"] += 1
        chain["last_proceed_ts"] = _now_iso()
        _save_chain(chain)
        print(json.dumps(_proceed_block(instruction)))
        return 0

    # "pause" (or any unrecognized verdict, fail-closed) → no block; reset the
    # chain so the next session starts fresh.
    _reset_chain()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
