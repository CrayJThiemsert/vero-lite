#!/usr/bin/env python3
"""PostToolUse hook — feed the loop-counter from tool outcomes (PLAN-0008 Step 3).

Observes ``Bash``/``Write``/``Edit`` outcomes and writes the state file
that Step 2 (``pretooluse_loop_detect.py``) reads. Never blocks — this
hook is observation-only; the deny gate lives in Step 2.

Counter ops by loop type:

- **L1 (Write/Edit)** — increment on every Write/Edit of the same
  normalized ``file_path``. Reset on "target untouched next turn" is
  **deferred to Step 4** (the Stop hook is the natural turn-boundary
  observer; PostToolUse cannot see turn boundaries). **Commit-boundary
  reset (follow-up, 2026-05-29):** a successful ``git commit`` observed in
  the Bash path resets the L1 counters for the files in the new HEAD commit
  — a commit is unambiguous observable progress and a reliable reset point
  independent of the Stop-hook turn boundary (which, across a long-lived
  multi-PR session, was empirically not catching legitimate repeated edits
  to the same file across separate PRs). Resets ONLY the committed files,
  so an unrelated in-flight edit loop is not masked.
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
import shutil
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
    get_count,
    has_triggered,
    increment,
    load_counter,
    normalize_error_signature,
    normalize_file_path,
    normalize_pytest_nodeid,
    record_turn_touched,
    reset,
    reset_l1_for_targets,
    save_counter,
    tokenize_bash_command,
)
from _wsl_bridge import bash_argv, env_with_wslenv_passthrough  # noqa: E402

DEFAULT_TELEGRAM_SCRIPT = REPO_ROOT / "tools" / "notify" / "telegram.sh"
TELEGRAM_TIMEOUT_SEC = 5

#: Resolved ``git`` executable (absolute path; avoids a partial-path argv).
#: Falls back to the bare name — a missing git surfaces as an OSError in
#: :func:`_committed_files`, which fails closed (no reset).
_GIT = shutil.which("git") or "git"

#: Matches a ``git commit`` invocation anywhere in a (possibly chained /
#: wsl-wrapped) Bash command, excluding ``git commit-tree`` / ``commit-graph``
#: via the negative-lookahead on word-char / hyphen.
_GIT_COMMIT_RE = re.compile(r"\bgit\s+commit(?![\w-])")

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


def _format_message(loop_type: LoopType, target: str, last_6_actions: list[dict[str, Any]]) -> str:
    """Build the human-readable Telegram body from the Cray-E.4 payload contract.

    Mirrors Step 2's formatter so both inline (L2/L3 here) and gated
    (L1/L4 in Step 2) alerts present a consistent shape to Cray.
    """
    actions_block = (
        "\n".join(
            f"  {a.get('ts', '?')} {a.get('tool', '?')} {a.get('target', '?')[:60]}"
            f"{(' [' + a['result'] + ']') if a.get('result') else ''}"
            for a in last_6_actions
        )
        or "  (none)"
    )
    return (
        f"[vero-lite/loop-detect] {loop_type.value} triggered\n"
        f"target: {target}\n"
        f"last 6 actions:\n{actions_block}\n"
        f"Cray: pause + reassess — see .claude/autonomy-triggers.md row {loop_type.value}"
    )


def _ping_telegram(loop_type: LoopType, target: str, last_6_actions: list[dict[str, Any]]) -> None:
    """Fire Telegram alert with the Cray-E.4 payload contract.

    Graceful no-op if the script is missing or fails — observer never
    blocks. Cross-platform invocation + WSLENV passthrough delegated to
    :mod:`_wsl_bridge` (Pattern A) — same idiom as Step 2's
    ``_ping_telegram`` so the same test-stub plays for both hooks.
    """
    script = _telegram_script()
    if not script.exists():
        return
    message = _format_message(loop_type, target, last_6_actions)
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


def _handle_write_or_edit(payload: dict[str, Any]) -> None:
    """L1: increment per Write/Edit + record the target as touched this turn.

    The turn-touched marker is consumed by Step 4's ``stop_continuation.py``
    on every Stop event to reset L1 counters whose targets were NOT
    touched this turn — the "target untouched on the next turn-boundary
    marker" rule from PLAN §Step 1. Without this, L1 counters grow
    unbounded across legitimate iterative editing (Cray's STATUS workflow
    risk surfaced in the L1/L4 asymmetry ELI-CTO).
    """
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return
    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str):
        return
    target = normalize_file_path(file_path)
    if not target:
        return

    counter = load_counter(_state_path())
    increment(
        counter,
        LoopType.FILE_EDIT,
        target,
        _now_action(payload.get("tool_name", "Edit"), target),
    )
    record_turn_touched(counter, target)
    # L1 trigger is gated by Step 2 on the NEXT Write/Edit — we do not fire
    # Telegram inline here (Step 2 is the gate).
    save_counter(counter, _state_path())


def _handle_agent_completion(payload: dict[str, Any]) -> None:
    """Subagent (Agent/Task) completion = an L1 reset boundary.

    A subagent's ``Write``/``Edit`` calls increment the SAME loop-counter as the
    main agent (they run in the parent session, sharing the state file). Without
    this, a subagent that makes several edits to one file pre-exhausts the main
    agent's L1 budget for that file (observed 2026-06-08: a ``plan-drafter``
    subagent made 6 edits to a PLAN and the main agent could then not add even
    one). On the Agent/Task tool completing, reset the L1 counters for the files
    touched so far this turn — symmetric with the commit-boundary and Stop
    turn-boundary resets. ``turn_touched`` is left intact so the Stop hook still
    tracks any main-agent edits made afterwards.
    """
    counter = load_counter(_state_path())
    cleared = reset_l1_for_targets(counter, list(counter.turn_touched))
    if cleared:
        save_counter(counter, _state_path())


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


def _is_git_commit(command: str) -> bool:
    """True iff the Bash command invokes ``git commit`` (not ``commit-tree``)."""
    return bool(_GIT_COMMIT_RE.search(command))


def _committed_files(repo_root: Path) -> list[str]:
    """Repo-relative paths in the current HEAD commit (the just-made commit).

    Read-only ``git diff-tree`` query. Fails closed to ``[]`` on any git error
    (missing binary, not a repo, timeout) or an empty/merge commit — a missing
    file list simply means no reset.
    """
    try:
        # S603: fixed argv, no shell; read-only query against HEAD.
        result = subprocess.run(  # noqa: S603
            [_GIT, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _apply_commit_reset(counter: Any, command: str, tool_response: dict[str, Any]) -> bool:
    """Commit-boundary L1 reset. Returns True if any counter changed.

    A successful ``git commit`` is unambiguous observable progress: the
    committed files reached a persisted boundary, so their L1 edit counters
    reset. Independent of (and more robust than) the Stop-hook turn-boundary
    reset — it fires in the PostToolUse Bash path, which runs reliably on every
    Bash call. Resets ONLY the files in the new HEAD commit, so an unrelated
    in-flight edit loop is not masked. A failed/ambiguous commit does not reset.
    """
    if not _is_git_commit(command):
        return False
    if _bash_outcome(tool_response) != "success":
        return False
    changed = False
    for path in _committed_files(REPO_ROOT):
        target = normalize_file_path(path)
        if target and get_count(counter, LoopType.FILE_EDIT, target) > 0:
            reset(counter, LoopType.FILE_EDIT, target)
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

    counter = load_counter(_state_path())
    changed = False
    changed |= _apply_l4(counter, command, tool_response)
    changed |= _apply_l2(counter, combined)
    changed |= _apply_l3(counter, combined)
    changed |= _apply_commit_reset(counter, command, tool_response)
    if changed:
        save_counter(counter, _state_path())


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # fail-open

    tool_name = payload.get("tool_name", "")
    try:
        if tool_name in ("Write", "Edit"):
            _handle_write_or_edit(payload)
        elif tool_name == "Bash":
            _handle_bash(payload)
        elif tool_name in ("Task", "Agent"):
            _handle_agent_completion(payload)
    except Exception as exc:  # observer must never block on internal error
        print(f"posttooluse_progress_observer: internal error: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
