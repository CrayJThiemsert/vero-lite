#!/usr/bin/env python3
"""PreToolUse hook — gate on the L4 loop-detect counter (PLAN-0008 Step 2).

Reads ``.claude/state/loop-counter.json`` via the Step 1 module and checks the
**L4** counter for ``Bash`` (same tokenized command pattern failed >= 6 times —
the counter is incremented in Step 3 on non-zero exit). When the bar trips,
fires ``tools/notify/telegram.sh`` with the payload contract
``{loop_type, target, last_6_actions}`` and emits a ``deny`` decision asking
Cray to intervene.

**L1 (same file edited repeatedly) was RETIRED by PLAN-0102.** Across its entire
live history it recorded zero true positives while hard-walling legitimate
construction sequences, so ``Write``/``Edit`` no longer map to any loop type
here and the harness no longer registers this hook for those tools at all.
Retiring it also narrows the implementation back to what ADR-013 E.4 actually
ratified — "the same **problem**", which is what L2/L3/L4 key on; L1 keyed on
the same **file**. **L4 is unchanged** and still denies at the flat 6: its unit
is already failure-based, so it never had a false-fire series to grant grace for.

**L2** (test_fail) and **L3** (error_signature) are inherently
PostToolUse-fed and fire from Step 3 directly — they are NOT enforced
here because a PreToolUse hook cannot predict pytest nodeids or error
signatures from the pending tool call.

This hook is **read-only** against the state file;
``posttooluse_progress_observer.py`` is the writer. (It was briefly a narrow
writer, for L1's acknowledged-pause arm — PLAN-0094 P3 — which retired with L1.)

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
    load_counter,
    main_session_id,
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
) -> dict[str, Any]:
    """Build the PreToolUse deny payload.

    **The standing rule this message is written under (PLAN-0094 P2, kept):
    it may name only reset paths that actually exist.** The rule was written
    after a message described the reset in terms of the ``Agent`` tool
    returning — a path that had been dead code for seven weeks while three
    documents advertised it live (the F3c finding). That phrase must not
    reappear anywhere in this file, **including in a comment**, which is why it
    is described here rather than quoted.

    **PLAN-0102 applied that same rule to this message rather than preserving
    it verbatim.** Only L4 reaches here now, and the reset paths the message
    used to list — an untouched turn boundary, a ``git commit`` containing the
    target, a subagent's own ``SubagentStop`` — were all **L1** paths, every one
    of them deleted with L1. Shipping them on an L4 deny would have told the
    agent to do three things that cannot clear its counter: precisely the defect
    the rule above exists to prevent, pointed the other way. L4's real reset is
    the one named below — :func:`_apply_l4` increments on a failing exit and
    resets on a successful one.
    """
    reason = (
        f"Loop-detect ({loop_type.value}) DENIED: same target `{target}` "
        f"hit {count} times (deny threshold = {threshold}, Cray E.4). "
        f"Last 6 actions captured in the Telegram payload. "
        f"The counter clears when this command pattern actually SUCCEEDS — a "
        f"non-zero exit is what increments it and a clean run resets it, so "
        f"retrying the same failing command cannot clear it. "
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

    ``Bash`` is now the ONLY mapping. PLAN-0102 removed the ``Write``/``Edit``
    -> ``FILE_EDIT`` branch with the rest of L1; the harness also stopped
    registering this hook for those tools, so a Write/Edit payload should never
    reach here at all — this function returning ``None`` for them is the second
    of the two independent guarantees, not the only one.
    """
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
    # L4 keeps the flat base threshold: its unit is already failure-based, so it
    # has no false-fire series to grant grace for. The path-class + grace-budget
    # branch that used to stand here was L1's alone (PLAN-0094 P2), and retired
    # with it in PLAN-0102 — as did the acknowledged-pause arm that made this
    # hook a narrow writer, which is why nothing below saves state any more.
    threshold = LOOP_TRIGGER_THRESHOLD
    if not has_triggered(counter, loop_type, target, threshold):
        return 0

    key = counter_key(loop_type, target)
    entry = counter.counters.get(key)
    if entry is None:  # defensive — has_triggered True implies entry exists
        return 0

    last_6 = [a.to_json() for a in entry.last_6_actions]
    # ``threshold`` is the bar this branch applied, so AC-11's count line names
    # the wall that just fell.
    _ping_telegram(loop_type, target, last_6, entry.count, threshold)
    print(json.dumps(_deny_decision(loop_type, target, entry.count, threshold)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
