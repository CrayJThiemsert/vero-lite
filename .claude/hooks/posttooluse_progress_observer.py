#!/usr/bin/env python3
"""PostToolUse hook — feed the loop-counter from tool outcomes (PLAN-0008 Step 3).

Observes ``Bash`` outcomes and writes the state file that Step 2
(``pretooluse_loop_detect.py``) reads. **Never denies a pending tool call; may
attach advisory feedback** — the deny gate lives in Step 2.

The wording above is deliberate. This hook used to say "never blocks", which
stopped being true in letter once it began emitting the PostToolUse
``{"decision": "block", "reason": …}`` shape — today that shape carries the
shell-hygiene advisory described below. It does NOT undo the tool call it
observes: the call has already happened, and ``block`` is the documented
channel for feeding a reason back into the agent's context. So the hook still
never *denies* anything, and the docstring says that instead of the thing that
would read as false.

**L1 (same file edited repeatedly) was RETIRED by PLAN-0102**, and with it this
hook's ``Write``/``Edit`` and ``SubagentStop`` registrations — both surfaces
existed only to serve L1, so once L1 went they would have spawned a Python
process per Write to compute a guaranteed no-op. The commit-boundary reset went
with them: it was an L1 reset living on the Bash path, not a Bash behaviour.
What survives is the Bash path proper — L2, L3, L4, and the shell-hygiene
advisory.

Counter ops by loop type:

- **L2 (pytest)** — parses Bash output for ``FAILED``/``PASSED`` lines
  (pytest "short test summary" + verbose mode). Increments L2 per
  failing nodeid; resets L2 per passing nodeid. **Fires Telegram inline
  on trigger** (count >= 6) because PreToolUse cannot predict the
  nodeid pre-execution.
- **L3 (error signature)** — hashes the first non-volatile line of any
  Python traceback in stdout/stderr; increments L3 per signature.
  **Fires Telegram inline on trigger**. Automatic reset (signature
  absent from next N outputs) is deferred — Step 4 can layer that on
  if needed.
- **L4 (Bash command)** — increments on observed failure
  (``interrupted`` true, or stderr-only output with common error
  markers), resets on observed success (no stderr, no interruption).
  Does NOT fire Telegram (PreToolUse Step 2's gate fires on the next
  attempt with same tokenized command). Ambiguous outcomes (both
  stdout and stderr present, no error markers) are **no-op** — counter
  unchanged — so noise does not pollute the L4 signal.

Bash exit-code detection is defensive: Claude Code's ``tool_response``
shape for Bash is not formally specced in repo as of Step 3 landing,
so the hook checks common field names
(``exit_code``/``returncode``/``exitCode``/``is_error``/``interrupted``)
and falls back to stderr-vs-stdout heuristics. Ambiguous → no-op,
never spurious increment.

State file path / Telegram script path / threshold all honor the same
env-var overrides as Step 2 for parity in test harnesses
(``CLAUDE_LOOP_COUNTER_PATH`` / ``CLAUDE_TELEGRAM_SCRIPT``).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from _loop_counter import (  # noqa: E402  — sys.path manipulation above
    DEFAULT_COUNTER_PATH,
    ActionRecord,
    LoopType,
    has_triggered,
    increment,
    load_counter,
    main_session_id,
    normalize_error_signature,
    normalize_pytest_nodeid,
    reset,
    save_counter,
    tokenize_bash_command,
)
from _wsl_bridge import bash_argv, env_with_wslenv_passthrough  # noqa: E402

DEFAULT_TELEGRAM_SCRIPT = REPO_ROOT / "tools" / "notify" / "telegram.sh"
TELEGRAM_TIMEOUT_SEC = 5

_FORWARDED_ENV = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")

# pytest "FAILED" / "PASSED" markers — covers both the short-summary section
# ("FAILED tests/foo.py::test_bar - reason") and verbose mode line endings
# ("tests/foo.py::test_bar PASSED [ 50%]"). The nodeid pattern is intentionally
# permissive on the file part (paths with /), strict on :: separators.
_PYTEST_FAILED_RE = re.compile(r"^FAILED\s+(\S+::\S+?)(?:\s+-|\s*$)", re.MULTILINE)
_PYTEST_PASSED_RE = re.compile(r"^(\S+::\S+?)\s+PASSED\b", re.MULTILINE)

# Python traceback first-line indicators. We capture the LAST line of the
# traceback (the actual exception type + message), which is the most stable
# signature; intervening frames vary by call site / path.
_TRACEBACK_BLOCK_RE = re.compile(
    r"Traceback \(most recent call last\):.*?\n"
    r"([A-Za-z_][\w.]*(?:Error|Exception|Warning|Exit)[^\n]*)",
    re.DOTALL,
)

# Heuristics for stderr-only failure detection when no explicit exit_code.
_BASH_ERROR_MARKERS = (
    "error:",
    "ERROR:",
    "Error:",
    "Traceback",
    "fatal:",
    "FATAL",
    "command not found",
    "No such file or directory",
    "Permission denied",
)


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

    Mirrors Step 2's formatter so both inline (L2/L3 here) and gated
    (L4 in Step 2) alerts present a consistent shape to Cray. **That mirror
    is asserted by a test** (PLAN-0094 AC-11 iii), not merely by this docstring:
    called with identical arguments, this and Step 2's formatter must return
    byte-identical strings. PLAN-0102 dropped the ``stage`` parameter — it
    existed only for L1's warn body — which leaves the two signatures identical
    rather than merely compatible, so the mirror is now harder to break.

    ``count`` / ``threshold`` stay optional and additive (AC-11) because Step 2
    still passes them on the L4 deny. The L2/L3 callers here deliberately do
    not: those fire exactly AT their threshold, so the line could only ever
    render ``6/6`` and would carry no information.
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

    Graceful no-op if the script is missing or fails — observer never
    blocks. Cross-platform invocation + WSLENV passthrough delegated to
    :mod:`_wsl_bridge` (Pattern A) — same idiom as Step 2's
    ``_ping_telegram`` so the same test-stub plays for both hooks.
    """
    script = _telegram_script()
    if not script.exists():
        return
    message = _format_message(loop_type, target, last_6_actions, count, threshold)
    cmd = bash_argv(script, message)
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


def _now_action(tool: str, target: str, result: str = "") -> ActionRecord:
    # Use a non-locale ISO-8601 stamp; matches _loop_counter._now_iso style.
    from datetime import UTC, datetime

    return ActionRecord(
        ts=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S%z"),
        tool=tool,
        target=target,
        result=result,
    )


def _check_and_fire(counter: Any, loop_type: LoopType, target: str) -> None:
    """If the counter just crossed the trigger threshold, fire Telegram."""
    if not has_triggered(counter, loop_type, target):
        return
    from _loop_counter import counter_key  # local import to keep top tidy

    entry = counter.counters.get(counter_key(loop_type, target))
    if entry is None:
        return
    last_6 = [a.to_json() for a in entry.last_6_actions]
    _ping_telegram(loop_type, target, last_6)


def _bash_outcome(tool_response: dict[str, Any]) -> str:
    """Return 'failure' / 'success' / 'ambiguous' from tool_response.

    Order of preference:
    1. Explicit interrupt flag
    2. Explicit exit-code-like field (exit_code / returncode / exitCode)
    3. Anthropic-style ``is_error`` boolean
    4. Heuristic: stderr present with error markers + empty stdout
    5. Heuristic: no stderr + non-error stdout → success
    6. Ambiguous (both present, no error markers) → no-op
    """
    if tool_response.get("interrupted") is True:
        return "failure"
    for key in ("exit_code", "returncode", "exitCode"):
        if key in tool_response and isinstance(tool_response[key], int):
            return "success" if tool_response[key] == 0 else "failure"
    if tool_response.get("is_error") is True:
        return "failure"

    stderr = (tool_response.get("stderr") or "").strip()
    stdout = (tool_response.get("stdout") or tool_response.get("output") or "").strip()

    has_error_marker = any(m in stderr for m in _BASH_ERROR_MARKERS)
    if stderr and (not stdout or has_error_marker):
        return "failure"
    if not stderr and stdout:
        return "success"
    if not stderr and not stdout:
        # Empty output is usually a no-op command (mkdir -p, etc.) — assume success.
        return "success"
    return "ambiguous"


def _extract_failed_nodeids(text: str) -> list[str]:
    if not text:
        return []
    return [m.group(1) for m in _PYTEST_FAILED_RE.finditer(text)]


def _extract_passed_nodeids(text: str) -> list[str]:
    if not text:
        return []
    return [m.group(1) for m in _PYTEST_PASSED_RE.finditer(text)]


def _extract_traceback_signature(text: str) -> str | None:
    if not text:
        return None
    m = _TRACEBACK_BLOCK_RE.search(text)
    if m is None:
        return None
    return m.group(1).strip()


def _apply_l4(counter: Any, command: str, tool_response: dict[str, Any]) -> bool:
    """L4: Bash command pattern. Returns True if counter changed.

    Does NOT fire Telegram — Step 2's gate fires on the next attempt
    when count >= 6.
    """
    target = tokenize_bash_command(command)
    if not target:
        return False
    outcome = _bash_outcome(tool_response)
    if outcome == "failure":
        increment(
            counter,
            LoopType.BASH_PATTERN,
            target,
            _now_action("Bash", target, result="failure"),
        )
        return True
    if outcome == "success":
        reset(counter, LoopType.BASH_PATTERN, target)
        return True
    return False  # ambiguous → no-op


def _apply_l2(counter: Any, combined_output: str) -> bool:
    """L2: pytest FAILED/PASSED per nodeid. Fires Telegram inline on trigger."""
    changed = False
    for raw_nodeid in _extract_failed_nodeids(combined_output):
        nodeid = normalize_pytest_nodeid(raw_nodeid)
        if not nodeid:
            continue
        increment(
            counter,
            LoopType.TEST_FAIL,
            nodeid,
            _now_action("Bash", nodeid, result="failed"),
        )
        changed = True
        _check_and_fire(counter, LoopType.TEST_FAIL, nodeid)
    for raw_nodeid in _extract_passed_nodeids(combined_output):
        nodeid = normalize_pytest_nodeid(raw_nodeid)
        if not nodeid:
            continue
        reset(counter, LoopType.TEST_FAIL, nodeid)
        changed = True
    return changed


def _apply_l3(counter: Any, combined_output: str) -> bool:
    """L3: traceback signature. Fires Telegram inline on trigger."""
    sig_raw = _extract_traceback_signature(combined_output)
    if not sig_raw:
        return False
    sig = normalize_error_signature(sig_raw)
    if not sig:
        return False
    increment(
        counter,
        LoopType.ERROR_SIGNATURE,
        sig,
        _now_action("Bash", sig, result="error"),
    )
    _check_and_fire(counter, LoopType.ERROR_SIGNATURE, sig)
    return True


#: A pipe into ``head``/``tail`` — the shape that discards the producer's exit status.
_PIPE_TO_TRUNCATOR_RE = re.compile(r"\|\s*(?:head|tail)\b")

#: ``$?`` / ``$(...)`` inside a ``bash -c`` / ``bash -lc`` string with NO backslash
#: escape. Under ``wsl bash -lc`` these expand one shell layer too early.
_UNESCAPED_EXPANSION_RE = re.compile(r"(?<!\\)\$(?:\?|\()")
_WSL_BASH_C_RE = re.compile(r"\bbash\s+-[a-z]*c\b")

#: A ``bash -c`` / ``bash -lc`` argument opened with a DOUBLE quote, which makes any
#: ``$`` inside it unsafe *whether or not* it is backslash-escaped — the outer layer
#: strips one level of escaping before WSL re-assembles the argv, so ``"... \$? ..."``
#: reaches the inner bash as a bare ``$?`` and expands a layer early exactly like the
#: unescaped form. Lesson 0007 §1.1 states the remedy in two halves ("a SINGLE-quoted
#: outer argument AND ``\$`` for every ``$``"); this pattern exists because the half
#: about quote style was enforced nowhere, and a session that dutifully added ``\$``
#: while keeping double quotes read fabricated zeros over two RED tests and went on to
#: diagnose the rule itself as broken. Lesson #0024: a rule has to live where the
#: enforcer looks, and half a remedy is the half that gets followed.
_BASH_C_DOUBLE_QUOTED_RE = re.compile(r"\bbash\s+-[a-z]*c\s+\"")
_ANY_DOLLAR_RE = re.compile(r"\$")


def _shell_hygiene_warning(command: str) -> str | None:
    """Advisory for Bash command shapes that make a FAILURE look like a SUCCESS.

    Every check here fires on a *deliberately typed* shape, never on incidental
    output, so false positives are cheap and rare. All three were measured in this
    harness on 2026-07-26 — see ``docs/lessons/0007-harness-exit-code-artifact.md``.

    This lives in the observer rather than a PreToolUse gate on purpose. The harm
    is not running the command, it is *believing* its output — which is knowable
    only once the command has run, and is exactly when this fires. It is also
    self-defence: a masked failure means :func:`_apply_l3` / :func:`_apply_l4` see
    exit 0 and a truncated body with the traceback cut off, so the masking silently
    disarms the very loop detection this module exists to provide.
    """
    problems: list[str] = []
    has_pipefail = "pipefail" in command

    if _PIPE_TO_TRUNCATOR_RE.search(command) and not has_pipefail:
        problems.append(
            "pipes into head/tail without `set -o pipefail`, so the reported exit "
            "status is the TRUNCATOR's (~always 0) and a failure reads as success; "
            "the truncation also cuts the traceback that would have shown it"
        )
    if "| head" in command.replace("|head", "| head") and has_pipefail:
        problems.append(
            "pipes into `head` under pipefail, which reports 141 (SIGPIPE) when head "
            "closes the pipe early — that turns a SUCCESSFUL command into a spurious "
            "failure; use `tail`, which drains its input"
        )
    if _WSL_BASH_C_RE.search(command) and _UNESCAPED_EXPANSION_RE.search(command):
        problems.append(
            "contains an unescaped `$?`/`$(...)` inside a `bash -c` string; under "
            "`wsl bash -lc` that expands one shell layer EARLY (measured: `$?` "
            "reports 0 for a failed command, `$(pwd)` resolves before a preceding "
            "`cd`) — the remedy has TWO halves and needs BOTH: a SINGLE-quoted outer "
            "argument AND `\\$` for every `$`"
        )
    if _BASH_C_DOUBLE_QUOTED_RE.search(command) and _ANY_DOLLAR_RE.search(command):
        problems.append(
            "puts a `$` inside a DOUBLE-quoted `bash -c` argument, where escaping "
            "does NOT save you: the outer layer eats one level of backslash, so "
            "`\\$?` arrives at the inner bash as a bare `$?` and expands a layer "
            "early anyway — a FAILED command still reports 0 and `\\$VAR` still "
            "comes back empty (measured). Use a SINGLE-quoted outer argument "
            "(`bash -lc '...'`) AND keep `\\$` for every `$` — both halves, neither "
            "alone; for anything whose output is evidence, write a script with the "
            "Write tool and run that instead"
        )

    if not problems:
        return None
    return (
        "Shell-hygiene advisory — the command you just ran "
        + "; ".join(problems)
        + ". Do not treat its exit status or output as trustworthy evidence. "
        "Re-run as: redirect to a file with `2>&1`, echo the real exit code, then "
        "read a bounded slice of the file (docs/lessons/0007)."
    )


def _handle_bash(payload: dict[str, Any]) -> None:
    """L2/L3/L4: parse Bash output to feed counters + fire L2/L3 Telegram inline."""
    tool_input = payload.get("tool_input") or {}
    tool_response = payload.get("tool_response") or {}
    if not isinstance(tool_input, dict) or not isinstance(tool_response, dict):
        return
    command = tool_input.get("command")
    if not isinstance(command, str):
        return

    stdout = tool_response.get("stdout") or tool_response.get("output") or ""
    stderr = tool_response.get("stderr") or ""
    combined = f"{stdout}\n{stderr}" if stderr else stdout

    counter = load_counter(_state_path(), session_id=main_session_id(payload))
    changed = False
    changed |= _apply_l4(counter, command, tool_response)
    changed |= _apply_l2(counter, combined)
    changed |= _apply_l3(counter, combined)
    if changed:
        save_counter(counter, _state_path())

    # Emitted last, and independent of the counters: this is about whether the
    # evidence just produced can be trusted at all, not about loop state.
    hygiene = _shell_hygiene_warning(command)
    if hygiene is not None:
        print(json.dumps({"decision": "block", "reason": hygiene}))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # fail-open

    # Bash is the only dispatch left. PLAN-0094 D1 had added a ``SubagentStop``
    # branch (and an event-first check to reach it, since a SubagentStop payload
    # carries no meaningful ``tool_name``) alongside a ``Write``/``Edit`` branch;
    # PLAN-0102 retired both with L1, and deregistered the two harness surfaces
    # that fed them, so neither payload reaches this process any more. Guarding
    # on ``tool_name`` here is the second of the two independent barriers.
    tool_name = payload.get("tool_name", "")
    try:
        if tool_name == "Bash":
            _handle_bash(payload)
    except Exception as exc:  # observer must never block on internal error
        print(f"posttooluse_progress_observer: internal error: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
