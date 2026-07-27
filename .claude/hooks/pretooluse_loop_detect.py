#!/usr/bin/env python3
"""PreToolUse hook — gate on L1/L4 loop-detect counters (PLAN-0008 Step 2).

Reads ``.claude/state/loop-counter.json`` via the Step 1 module; for
``Write``/``Edit`` checks the **L1** counter (same file edited repeatedly);
for ``Bash`` checks the **L4** counter (same tokenized command pattern failed
>= 6 times — counter is incremented in Step 3 on non-zero exit). When the bar
trips, fires ``tools/notify/telegram.sh`` with the payload contract
``{loop_type, target, last_6_actions}`` and emits a ``deny`` decision asking
Cray to intervene.

**L1 is warn-first since PLAN-0094 P2.** Its path-class threshold
(``l1_threshold_for`` — 6 code / 15 doc) is now the WARN bar, owned by the
observer, which pings and hands the agent an advisory but ALLOWS the edit.
This hook's deny bar is ``l1_deny_threshold_for`` = that threshold plus
``L1_GRACE_BUDGET`` (3, Cray-ratified OQ-1) — so 9 / 18. **L4 is unchanged**
and still denies at the flat 6: its unit is already failure-based, so unlike
L1 it has no false-fire series to grant grace for.

**L2** (test_fail) and **L3** (error_signature) are inherently
PostToolUse-fed and fire from Step 3 directly — they are NOT enforced
here because a PreToolUse hook cannot predict pytest nodeids or error
signatures from the pending tool call.

Step 2 was **read-only** against the state file until PLAN-0094 Step 5 (P3),
which makes it a **narrow writer**: on the L1 deny branch only, it arms
``awaiting_ack`` for the denied target so a ``Stop`` that actually fires can
grant a deterministic, human-in-the-loop exit. Nothing else here writes, and a
lost write self-heals — the deny re-fires on the next attempt and re-arms.
``posttooluse_progress_observer.py`` remains the general writer.

Bypass-immunity: the hook reads its own process env for
``CLAUDE_LOOP_COUNTER_PATH`` / ``CLAUDE_TELEGRAM_SCRIPT`` overrides,
not the ``tool_input``, so an inline command spoof cannot redirect the
state file. The deterministic ``deny`` decision beats
``bypassPermissions`` (same property as the Phase 1 G5 commit-deny
hook, ADR-013 D2 rationale).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from _loop_counter import (  # noqa: E402  — sys.path manipulation above
    DEFAULT_COUNTER_PATH,
    LOOP_TRIGGER_THRESHOLD,
    LoopType,
    counter_key,
    has_triggered,
    l1_deny_threshold_for,
    l1_threshold_for,
    load_counter,
    main_session_id,
    normalize_file_path,
    record_awaiting_ack,
    save_counter,
    tokenize_bash_command,
)
from _wsl_bridge import bash_argv, env_with_wslenv_passthrough  # noqa: E402

DEFAULT_TELEGRAM_SCRIPT = REPO_ROOT / "tools" / "notify" / "telegram.sh"
TELEGRAM_TIMEOUT_SEC = 5

_FORWARDED_ENV = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")


def _state_path() -> Path:
    override = os.environ.get("CLAUDE_LOOP_COUNTER_PATH")
    if override:
        return Path(override)
    return DEFAULT_COUNTER_PATH


def _telegram_script() -> Path:
    override = os.environ.get("CLAUDE_TELEGRAM_SCRIPT")
    if override:
        return Path(override)
    return DEFAULT_TELEGRAM_SCRIPT


def _format_message(
    loop_type: LoopType,
    target: str,
    last_6_actions: list[dict[str, Any]],
    count: int | None = None,
    threshold: int | None = None,
) -> str:
    """Build the human-readable Telegram body from the Cray-E.4 payload contract.

    Sent as a single ``$1`` argv to ``telegram.sh`` (see Lesson #14 — the
    script reads argv, never stdin). Lines stay short so Cray can scan
    on a phone lock-screen preview.

    ``count`` / ``threshold`` are optional and additive (PLAN-0094 AC-11): supply
    both and the body gains a ``count: N/T`` line. **T is the DENY bar — the
    wall — not the warn bar** (Cray-ratified s180): AC-11 exists so the ping
    says how close the wall is, and on the warn body the warn bar would render
    the uninformative ``6/6`` while the deny body would render ``9/6``, which
    reads as an overflow and never names 9 at all. Passing the bar the caller
    actually applied keeps both bodies reading ``N/9``.

    Omitting both reproduces the pre-AC-11 body byte-for-byte.
    """
    actions_block = (
        "\n".join(
            f"  {a.get('ts', '?')} {a.get('tool', '?')} {a.get('target', '?')[:60]}"
            f"{(' [' + a['result'] + ']') if a.get('result') else ''}"
            for a in last_6_actions
        )
        or "  (none)"
    )
    count_line = (
        f"count: {count}/{threshold}\n" if count is not None and threshold is not None else ""
    )
    return (
        f"[vero-lite/loop-detect] {loop_type.value} triggered\n"
        f"target: {target}\n"
        f"{count_line}"
        f"last 6 actions:\n{actions_block}\n"
        f"Cray: pause + reassess — see .claude/autonomy-triggers.md row {loop_type.value}"
    )


def _ping_telegram(
    loop_type: LoopType,
    target: str,
    last_6_actions: list[dict[str, Any]],
    count: int | None = None,
    threshold: int | None = None,
) -> None:
    """Fire Telegram alert with the Cray-E.4 payload contract.

    Graceful no-op if the script is missing or fails — the gate must
    still ``deny`` even if the AFK channel is down. Cross-platform
    invocation + WSLENV passthrough delegated to :mod:`_wsl_bridge`
    (Pattern A). The message is delivered as a single argv element (per
    ``telegram.sh`` contract — argv, never stdin).
    """
    script = _telegram_script()
    if not script.exists():
        return
    message = _format_message(loop_type, target, last_6_actions, count, threshold)
    cmd = bash_argv(script, message)
    env = env_with_wslenv_passthrough(_FORWARDED_ENV)

    try:
        # S603: cmd elements come from hook-controlled script path
        # (constant or env-override read at startup) + the formatted
        # message; no shell interpolation, no user-controlled args.
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


def _deny_decision(
    loop_type: LoopType,
    target: str,
    count: int,
    threshold: int = LOOP_TRIGGER_THRESHOLD,
    warn_threshold: int | None = None,
) -> dict[str, Any]:
    """Build the PreToolUse deny payload.

    PLAN-0094 P2 rewrote this message wholesale. Two things it must not do, both
    learned the hard way: it must not describe the reset paths in terms of the
    ``Agent`` tool returning (that path was dead code for seven weeks while three
    documents advertised it live — the F3c finding), and it must not name an exit
    that has not shipped (the P3 stop-ack is Step 5's; naming it here would
    recreate the very defect AC-3 closes).

    The AC-3 grep oracle keys on the old message's anchor phrase — the clause
    that attributed the reset to a subagent's edits landing when the Agent tool
    returned. That phrase must not reappear anywhere in this file, **including
    in a comment**, which is why it is described here rather than quoted. The
    oracle found exactly that mistake in an earlier draft of this docstring.
    """
    if warn_threshold is not None and warn_threshold < threshold:
        stage = (
            f"You were already warned at {warn_threshold} and had "
            f"{threshold - warn_threshold} more edits of grace; this is the wall. "
        )
    else:
        stage = ""
    reason = (
        f"Loop-detect ({loop_type.value}) DENIED: same target `{target}` "
        f"hit {count} times (deny threshold = {threshold}, Cray E.4). {stage}"
        f"Last 6 actions captured in the Telegram payload. "
        f"The counter clears when any of these actually happen: a turn boundary "
        f"that does NOT touch this target (touching it again keeps the count "
        f"alive), a git commit containing it, or — for edits a SUBAGENT made — "
        f"that subagent's own SubagentStop, which clears only the targets it "
        f"edited itself. Spawning a subagent does NOT clear edits YOU made. "
        f"Pause and reassess the approach with Cray before retrying — see "
        f".claude/autonomy-triggers.md row {loop_type.value}."
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def _resolve_target(tool_name: str, tool_input: dict[str, Any]) -> tuple[LoopType, str] | None:
    """Map ``(tool_name, tool_input)`` to the ``(loop_type, target)`` key.

    Returns ``None`` for tools / payloads that do not map to a
    PreToolUse-enforceable loop type (L2 / L3 are PostToolUse-fed,
    Read / Glob / Grep / Task / etc. are not gated here).
    """
    if tool_name in ("Write", "Edit"):
        file_path = tool_input.get("file_path")
        if not isinstance(file_path, str):
            return None
        target = normalize_file_path(file_path)
        if not target:
            return None
        return (LoopType.FILE_EDIT, target)
    if tool_name == "Bash":
        command = tool_input.get("command")
        if not isinstance(command, str):
            return None
        target = tokenize_bash_command(command)
        if not target:
            return None
        return (LoopType.BASH_PATTERN, target)
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # fail-open on malformed input (protocol expects valid JSON)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return 0

    match = _resolve_target(tool_name, tool_input)
    if match is None:
        return 0

    loop_type, target = match
    counter = load_counter(_state_path(), session_id=main_session_id(payload))
    # PLAN-0094 P2: for L1 the DENY bar is the warn bar plus the grace budget --
    # the observer owns the warn at ``l1_threshold_for``, this hook owns the wall
    # at ``l1_deny_threshold_for``. L4 keeps the flat base threshold: its unit is
    # already failure-based, so it has no false-fire series to grant grace for.
    if loop_type is LoopType.FILE_EDIT:
        warn_threshold: int | None = l1_threshold_for(target)
        threshold = l1_deny_threshold_for(target)
    else:
        warn_threshold = None
        threshold = LOOP_TRIGGER_THRESHOLD
    if not has_triggered(counter, loop_type, target, threshold):
        return 0

    key = counter_key(loop_type, target)
    entry = counter.counters.get(key)
    if entry is None:  # defensive — has_triggered True implies entry exists
        return 0

    # PLAN-0094 D5: arm the acknowledged-pause exit, L1 ONLY. L4 keeps the flat
    # threshold and has no false-fire series, so granting it this reset path
    # would hand a failing-command loop an exit the PLAN never priced. Wrapped
    # because the deny is the load-bearing behavior: a state-write failure must
    # never swallow the wall.
    if loop_type is LoopType.FILE_EDIT:
        try:
            record_awaiting_ack(counter, target)
            save_counter(counter, _state_path())
        except OSError as exc:
            print(f"pretooluse_loop_detect: could not arm awaiting_ack: {exc}", file=sys.stderr)

    last_6 = [a.to_json() for a in entry.last_6_actions]
    # ``threshold`` here is already the bar this branch applied — the L1 deny bar
    # (T + G) or L4's flat base — so AC-11's line names the wall that just fell.
    _ping_telegram(loop_type, target, last_6, entry.count, threshold)
    print(json.dumps(_deny_decision(loop_type, target, entry.count, threshold, warn_threshold)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
