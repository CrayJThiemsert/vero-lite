"""Tests for ``.claude/hooks/pretooluse_loop_detect.py`` (PLAN-0008 Step 2).

Covers:

- Tool/target mapping: Write/Edit -> L1, Bash -> L4, Read/Glob/etc -> no-op
- Allow path: count below threshold (0, 1, 5), no counter for target,
  fresh state file, missing state file
- Deny path (path-class thresholds, Cray E.4 refinement 2026-06-08):
  a CODE target denies at the base 6; a DOC / markdown target denies only
  at L1_DOC_THRESHOLD (15) — doc authoring legitimately makes many small
  sequential edits to one file (regression guard for the false-positive
  that blocked PLAN/ADR/STATUS authoring)
- Telegram stub captures the Cray-E.4 payload `{loop_type, target,
  last_6_actions}` when deny fires
- Malformed input (bad JSON, missing tool_name, missing tool_input,
  non-dict tool_input)
- Path normalization parity with the C4 hook (Windows-UNC / backslash)
- Bash tokenization (same command pattern with different args collapses)
- Env-var overrides for state path + telegram script (testability)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, TypeGuard

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / ".claude" / "hooks" / "pretooluse_loop_detect.py"
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from _loop_counter import (  # noqa: E402  — sys.path manipulation above
    L1_DOC_THRESHOLD,
    ActionRecord,
    LoopType,
    increment,
    new_counter,
    save_counter,
)

Payload = dict[str, Any]
Parsed = dict[str, Any] | None

# A canonical CODE-class target (base threshold 6) and DOC-class target
# (L1_DOC_THRESHOLD) used across the deny/allow tests so the path-class split
# is explicit. ``docs/STATUS.md`` is the real-world doc that surfaced the
# false-positive; ``services/api/main.py`` is a representative code path.
CODE_TARGET = "services/api/main.py"
DOC_TARGET = "docs/STATUS.md"

STUB_TELEGRAM = """#!/usr/bin/env bash
# Stub that writes $1 (argv message) to $TELEGRAM_STUB_CAPTURE.
# Matches real telegram.sh contract — message via argv, never stdin
# (see Lesson #14 / session-15 Path C step 3 fix).
set -eu
printf '%s' "$1" > "$TELEGRAM_STUB_CAPTURE"
"""


@pytest.fixture
def stub_env(tmp_path: Path) -> dict[str, str]:
    """Seed env: state path + telegram stub + capture file path."""
    state_path = tmp_path / "loop-counter.json"
    stub_script = tmp_path / "telegram_stub.sh"
    capture_file = tmp_path / "telegram_capture.json"
    stub_script.write_text(STUB_TELEGRAM, encoding="utf-8")
    stub_script.chmod(0o755)
    env = os.environ.copy()
    env["CLAUDE_LOOP_COUNTER_PATH"] = str(state_path)
    env["CLAUDE_TELEGRAM_SCRIPT"] = str(stub_script)
    env["TELEGRAM_STUB_CAPTURE"] = str(capture_file)
    # Defang the real Telegram env so even if the stub leaks, no live call
    env.pop("TELEGRAM_BOT_TOKEN", None)
    env.pop("TELEGRAM_CHAT_ID", None)
    return env


def _run(payload: Payload, env: dict[str, str]) -> tuple[int, Parsed]:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=15,
    )
    out = result.stdout.strip()
    parsed = json.loads(out) if out else None
    return result.returncode, parsed


def _is_deny(parsed: Parsed) -> TypeGuard[dict[str, Any]]:
    if not parsed:
        return False
    decision = parsed.get("hookSpecificOutput", {}).get("permissionDecision")
    return bool(decision == "deny")


def _write(file_path: str) -> Payload:
    return {"tool_name": "Write", "tool_input": {"file_path": file_path, "content": "x"}}


def _edit(file_path: str) -> Payload:
    return {
        "tool_name": "Edit",
        "tool_input": {"file_path": file_path, "old_string": "a", "new_string": "b"},
    }


def _bash(command: str) -> Payload:
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def _seed_counter(state_path: Path, loop_type: LoopType, target: str, count: int) -> None:
    c = new_counter("test-session")
    for i in range(count):
        increment(c, loop_type, target, ActionRecord(ts=f"t{i}", tool="Edit", target=target))
    save_counter(c, state_path)


def _state_path_from(env: dict[str, str]) -> Path:
    return Path(env["CLAUDE_LOOP_COUNTER_PATH"])


# --- Allow path ---


def test_allow_when_no_state_file(stub_env: dict[str, str]) -> None:
    rc, out = _run(_write(DOC_TARGET), stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_allow_when_no_counter_for_target(stub_env: dict[str, str]) -> None:
    _seed_counter(_state_path_from(stub_env), LoopType.FILE_EDIT, "other.py", 10)
    rc, out = _run(_write(DOC_TARGET), stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_allow_when_code_count_below_threshold(stub_env: dict[str, str]) -> None:
    _seed_counter(_state_path_from(stub_env), LoopType.FILE_EDIT, CODE_TARGET, 5)
    rc, out = _run(_write(CODE_TARGET), stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_allow_for_non_matching_tool_read(stub_env: dict[str, str]) -> None:
    rc, out = _run({"tool_name": "Read", "tool_input": {"file_path": "x.py"}}, stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_allow_for_non_matching_tool_glob(stub_env: dict[str, str]) -> None:
    rc, out = _run({"tool_name": "Glob", "tool_input": {"pattern": "**/*.py"}}, stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_allow_when_file_path_missing(stub_env: dict[str, str]) -> None:
    rc, out = _run({"tool_name": "Write", "tool_input": {}}, stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_allow_when_command_missing(stub_env: dict[str, str]) -> None:
    rc, out = _run({"tool_name": "Bash", "tool_input": {}}, stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_allow_when_file_path_not_string(stub_env: dict[str, str]) -> None:
    rc, out = _run({"tool_name": "Edit", "tool_input": {"file_path": 12345}}, stub_env)
    assert rc == 0
    assert not _is_deny(out)


# --- Deny path: L1 code-class target (base threshold 6) ---


def test_deny_l1_code_path_at_threshold(stub_env: dict[str, str]) -> None:
    _seed_counter(_state_path_from(stub_env), LoopType.FILE_EDIT, CODE_TARGET, 6)
    rc, out = _run(_write(CODE_TARGET), stub_env)
    assert rc == 0
    assert _is_deny(out)
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "L1" in reason
    assert CODE_TARGET in reason


def test_deny_l1_code_above_threshold(stub_env: dict[str, str]) -> None:
    _seed_counter(_state_path_from(stub_env), LoopType.FILE_EDIT, CODE_TARGET, 12)
    rc, out = _run(_edit(CODE_TARGET), stub_env)
    assert rc == 0
    assert _is_deny(out)
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "12" in reason


def test_deny_edit_tool_treated_same_as_write(stub_env: dict[str, str]) -> None:
    _seed_counter(_state_path_from(stub_env), LoopType.FILE_EDIT, CODE_TARGET, 6)
    rc_w, out_w = _run(_write(CODE_TARGET), stub_env)
    rc_e, out_e = _run(_edit(CODE_TARGET), stub_env)
    assert _is_deny(out_w) and _is_deny(out_e)


# --- Deny / allow path: L1 doc-class target (path-class threshold = L1_DOC_THRESHOLD) ---


def test_allow_l1_doc_path_at_code_threshold(stub_env: dict[str, str]) -> None:
    """Regression guard (Cray E.4 refinement 2026-06-08): a DOC target at the
    old flat-6 must NOT deny — multi-section governance authoring is the work,
    not a loop. This is the exact false-positive that blocked PLAN authoring.
    """
    _seed_counter(_state_path_from(stub_env), LoopType.FILE_EDIT, DOC_TARGET, 6)
    rc, out = _run(_write(DOC_TARGET), stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_allow_l1_doc_path_just_below_doc_threshold(stub_env: dict[str, str]) -> None:
    _seed_counter(_state_path_from(stub_env), LoopType.FILE_EDIT, DOC_TARGET, L1_DOC_THRESHOLD - 1)
    rc, out = _run(_write(DOC_TARGET), stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_deny_l1_doc_path_at_doc_threshold(stub_env: dict[str, str]) -> None:
    """A doc target STILL trips — at the higher (finite) doc threshold — so a
    genuinely stuck doc-edit loop is not masked.
    """
    _seed_counter(_state_path_from(stub_env), LoopType.FILE_EDIT, DOC_TARGET, L1_DOC_THRESHOLD)
    rc, out = _run(_write(DOC_TARGET), stub_env)
    assert rc == 0
    assert _is_deny(out)
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "L1" in reason
    assert DOC_TARGET in reason
    assert str(L1_DOC_THRESHOLD) in reason  # message reports the path-class threshold


def test_markdown_anywhere_uses_doc_threshold(stub_env: dict[str, str]) -> None:
    """A markdown file outside docs/ (e.g. a root README) is still doc-class."""
    target = "README.md"
    _seed_counter(_state_path_from(stub_env), LoopType.FILE_EDIT, target, 6)
    rc, out = _run(_write(target), stub_env)
    assert rc == 0
    assert not _is_deny(out)  # 6 < doc threshold


def test_deny_l1_with_windows_unc_path(stub_env: dict[str, str]) -> None:
    """Path normalization parity: UNC input lookups the same normalized key.

    Seeded at the doc threshold so the doc-class target denies.
    """
    _seed_counter(_state_path_from(stub_env), LoopType.FILE_EDIT, DOC_TARGET, L1_DOC_THRESHOLD)
    unc = "\\\\wsl.localhost\\Ubuntu-24.04\\home\\crayj\\work\\vero-lite\\docs\\STATUS.md"
    rc, out = _run(_write(unc), stub_env)
    assert rc == 0
    assert _is_deny(out)


def test_deny_l1_with_backslash_path(stub_env: dict[str, str]) -> None:
    _seed_counter(_state_path_from(stub_env), LoopType.FILE_EDIT, DOC_TARGET, L1_DOC_THRESHOLD)
    rc, out = _run(_write("docs\\STATUS.md"), stub_env)
    assert rc == 0
    assert _is_deny(out)


# --- Deny path: L4 (Bash) ---


def test_deny_l4_at_threshold(stub_env: dict[str, str]) -> None:
    target = "pytest <arg>"  # tokenized form
    _seed_counter(_state_path_from(stub_env), LoopType.BASH_PATTERN, target, 6)
    rc, out = _run(_bash("pytest tests/foo.py"), stub_env)
    assert rc == 0
    assert _is_deny(out)
    assert "L4" in out["hookSpecificOutput"]["permissionDecisionReason"]


def test_deny_l4_collapses_variant_args(stub_env: dict[str, str]) -> None:
    """Different paths collapse to the same `pytest <arg>` token."""
    target = "pytest <arg>"
    _seed_counter(_state_path_from(stub_env), LoopType.BASH_PATTERN, target, 6)
    rc1, out1 = _run(_bash("pytest tests/foo.py"), stub_env)
    rc2, out2 = _run(_bash("pytest tests/bar.py"), stub_env)
    assert _is_deny(out1) and _is_deny(out2)


def test_allow_l4_distinct_command_pattern(stub_env: dict[str, str]) -> None:
    """Counter for pytest must NOT trip a different command (e.g., git)."""
    _seed_counter(_state_path_from(stub_env), LoopType.BASH_PATTERN, "pytest <arg>", 10)
    rc, out = _run(_bash("git status"), stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_l4_uses_base_threshold_for_doc_like_command(stub_env: dict[str, str]) -> None:
    """L4 (Bash) is path-class-agnostic: a command that happens to mention a .md
    path still uses the base threshold 6 (path-class applies to L1 file edits only).
    """
    target = "cat <arg>"
    _seed_counter(_state_path_from(stub_env), LoopType.BASH_PATTERN, target, 6)
    rc, out = _run(_bash("cat docs/STATUS.md"), stub_env)
    assert rc == 0
    assert _is_deny(out)


# --- Telegram payload contract (Cray E.4) ---


def test_deny_fires_telegram_with_payload(stub_env: dict[str, str], tmp_path: Path) -> None:
    state_path = _state_path_from(stub_env)
    c = new_counter("test-session")
    for i in range(6):
        increment(
            c,
            LoopType.FILE_EDIT,
            CODE_TARGET,
            ActionRecord(ts=f"t{i}", tool="Edit", target=CODE_TARGET, result=f"attempt-{i}"),
        )
    save_counter(c, state_path)

    rc, out = _run(_write(CODE_TARGET), stub_env)
    assert rc == 0
    assert _is_deny(out)

    capture = Path(stub_env["TELEGRAM_STUB_CAPTURE"])
    assert capture.exists(), "stub telegram script was not invoked"
    body = capture.read_text(encoding="utf-8")
    # Human-readable body (per Lesson #14): argv message, not JSON-on-stdin.
    assert "L1" in body
    assert CODE_TARGET in body
    assert "attempt-5" in body  # newest action present
    assert "attempt-0" in body  # oldest of the 6 still in window
    # All 6 timestamps present → action lines round-tripped through formatter
    for i in range(6):
        assert f"t{i}" in body


def test_deny_still_fires_when_telegram_script_missing(stub_env: dict[str, str]) -> None:
    """Telegram outage must NOT block the gate — deny still emitted."""
    stub_env["CLAUDE_TELEGRAM_SCRIPT"] = "/nonexistent/path/telegram.sh"
    _seed_counter(_state_path_from(stub_env), LoopType.FILE_EDIT, "x.py", 6)
    rc, out = _run(_write("x.py"), stub_env)
    assert rc == 0
    assert _is_deny(out)


# --- Malformed input (fail-open per hook protocol) ---


def test_malformed_json_fails_open(stub_env: dict[str, str]) -> None:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json at all",
        capture_output=True,
        text=True,
        env=stub_env,
        check=False,
        timeout=15,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_missing_tool_name(stub_env: dict[str, str]) -> None:
    rc, out = _run({"tool_input": {"file_path": "x.py"}}, stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_non_dict_tool_input(stub_env: dict[str, str]) -> None:
    rc, out = _run({"tool_name": "Write", "tool_input": "not-a-dict"}, stub_env)
    assert rc == 0
    assert not _is_deny(out)


# --- L2/L3 NOT enforced at PreToolUse (Step 3 responsibility) ---


def test_l2_counter_does_not_gate_bash(stub_env: dict[str, str]) -> None:
    """L2 (test_fail) is keyed by pytest nodeid — PreToolUse cannot predict
    which test the bash command will fail. Step 3 fires L2 Telegram pings
    directly; Step 2 must not also deny on L2-state existing.
    """
    _seed_counter(
        _state_path_from(stub_env),
        LoopType.TEST_FAIL,
        "tests/handoffs/test_foo.py::test_bar",
        10,
    )
    rc, out = _run(_bash("pytest tests/handoffs/test_foo.py"), stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_l3_counter_does_not_gate_bash(stub_env: dict[str, str]) -> None:
    _seed_counter(
        _state_path_from(stub_env),
        LoopType.ERROR_SIGNATURE,
        "RuntimeError: foo missing",
        10,
    )
    rc, out = _run(_bash("python script.py"), stub_env)
    assert rc == 0
    assert not _is_deny(out)


# --- Reason message contract ---


def test_deny_reason_includes_target_and_count_and_registry_pointer(
    stub_env: dict[str, str],
) -> None:
    _seed_counter(_state_path_from(stub_env), LoopType.FILE_EDIT, "x.py", 7)
    _, out = _run(_write("x.py"), stub_env)
    assert _is_deny(out)
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "x.py" in reason
    assert "7" in reason
    assert ".claude/autonomy-triggers.md" in reason
    assert "Cray E.4" in reason or "threshold" in reason


# --- ADR-013 D2 bypass-immunity regression guard (Step 6 Phase 1.5) ---


def test_bypass_permissions_still_denies_at_threshold(stub_env: dict[str, str]) -> None:
    """ADR-013 D2 binding: ``PreToolUse deny`` is deterministic and bypass-immune.

    Adding ``permission_mode: bypassPermissions`` to the payload must not
    short-circuit the L1 loop-detect deny once the counter is at threshold.
    Cheap insurance against a future hook implementation that accidentally
    short-circuits on bypass. Uncovered until session-14 Step 6 Phase 1.5
    closeout.
    """
    _seed_counter(_state_path_from(stub_env), LoopType.FILE_EDIT, CODE_TARGET, 6)
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": CODE_TARGET, "content": "x"},
        "permission_mode": "bypassPermissions",
    }
    rc, out = _run(payload, stub_env)
    assert rc == 0
    assert _is_deny(out)
