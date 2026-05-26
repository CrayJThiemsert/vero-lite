"""Tests for .claude/hooks/pretooluse_plan_subagent_write_deny.py (H2).

H2 enforces the `plan-drafter` subagent write-path allowlist per PLAN-0009
Step 1b §5. Unlike the C4 sibling (`pretooluse_research_path_deny`) which
is fail-OPEN on malformed input, H2 is **fail-CLOSED**: malformed JSON,
missing `tool_input`, or non-string `file_path` all deny the call.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / ".claude" / "hooks" / "pretooluse_plan_subagent_write_deny.py"

Payload = dict[str, Any]
Parsed = dict[str, Any] | None


def _run(payload: Payload | str) -> tuple[int, Parsed]:
    env = os.environ.copy()
    stdin = payload if isinstance(payload, str) else json.dumps(payload)
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    out = result.stdout.strip()
    parsed = json.loads(out) if out else None
    return result.returncode, parsed


def _is_deny(parsed: Parsed) -> bool:
    if not parsed:
        return False
    decision = parsed.get("hookSpecificOutput", {}).get("permissionDecision")
    return bool(decision == "deny")


def _write(file_path: Any) -> Payload:
    return {"tool_name": "Write", "tool_input": {"file_path": file_path, "content": "x"}}


def _edit(file_path: Any) -> Payload:
    return {
        "tool_name": "Edit",
        "tool_input": {"file_path": file_path, "old_string": "a", "new_string": "b"},
    }


# --- Allow cases (within docs/{adr,plans}/*.md) ---


def test_adr_write_allowed() -> None:
    rc, out = _run(_write("docs/adr/0014-new-decision.md"))
    assert rc == 0
    assert not _is_deny(out)


def test_plan_write_allowed() -> None:
    _, out = _run(_write("docs/plans/0011-new-plan.md"))
    assert not _is_deny(out)


def test_adr_edit_allowed() -> None:
    _, out = _run(_edit("docs/adr/0013-autonomy-axis-relocation.md"))
    assert not _is_deny(out)


def test_plan_edit_allowed() -> None:
    _, out = _run(_edit("docs/plans/0009-subagent-topology.md"))
    assert not _is_deny(out)


def test_plan_done_subdir_allowed_by_prefix() -> None:
    # docs/plans/done/ passes the prefix check; archival is a separate
    # concern handled by Code-tab `git mv` and prompt discipline, not
    # this hook (Step 1b §5 spec is prefix+suffix only).
    _, out = _run(_write("docs/plans/done/0007-foo.md"))
    assert not _is_deny(out)


# --- Deny cases (outside allowlist) ---


def test_services_write_denied() -> None:
    _, out = _run(_write("services/api/main.py"))
    assert _is_deny(out)


def test_tests_write_denied() -> None:
    _, out = _run(_write("tests/test_foo.py"))
    assert _is_deny(out)


def test_status_md_write_denied() -> None:
    # docs/STATUS.md is governance-adjacent but not under adr/ or plans/.
    # Code-tab owns STATUS updates per the closeout pattern.
    _, out = _run(_write("docs/STATUS.md"))
    assert _is_deny(out)


def test_claude_md_write_denied() -> None:
    _, out = _run(_write("CLAUDE.md"))
    assert _is_deny(out)


def test_lessons_write_denied() -> None:
    # Lessons live at docs/lessons/, outside the plan-drafter scope.
    _, out = _run(_write("docs/lessons/0011-new-lesson.md"))
    assert _is_deny(out)


def test_runbooks_write_denied() -> None:
    _, out = _run(_write("docs/runbooks/foo.md"))
    assert _is_deny(out)


def test_non_md_extension_denied() -> None:
    # Suffix check: .yaml / .py / no-extension under docs/adr/ still denies.
    _, out = _run(_write("docs/adr/0014-config.yaml"))
    assert _is_deny(out)


def test_no_extension_denied() -> None:
    _, out = _run(_write("docs/plans/0011-foo"))
    assert _is_deny(out)


def test_md_outside_allowed_dirs_denied() -> None:
    _, out = _run(_write("docs/conventions/foo.md"))
    assert _is_deny(out)


def test_edit_outside_allowed_dirs_denied() -> None:
    _, out = _run(_edit("services/api/main.py"))
    assert _is_deny(out)


# --- Path normalization (cross-platform) ---


def test_absolute_repo_path_adr_allowed() -> None:
    abs_path = str(REPO_ROOT / "docs" / "adr" / "0014-foo.md")
    _, out = _run(_write(abs_path))
    assert not _is_deny(out)


def test_absolute_repo_path_services_denied() -> None:
    abs_path = str(REPO_ROOT / "services" / "api" / "main.py")
    _, out = _run(_write(abs_path))
    assert _is_deny(out)


def test_windows_unc_adr_allowed() -> None:
    unc = r"\\wsl.localhost\ubuntu-24.04\home\crayj\work\vero-lite\docs\adr\0014-foo.md"
    _, out = _run(_write(unc))
    assert not _is_deny(out)


def test_windows_unc_services_denied() -> None:
    unc = r"\\wsl.localhost\ubuntu-24.04\home\crayj\work\vero-lite\services\api\main.py"
    _, out = _run(_write(unc))
    assert _is_deny(out)


def test_windows_unc_plans_allowed() -> None:
    unc = r"\\wsl.localhost\ubuntu-24.04\home\crayj\work\vero-lite\docs\plans\0011-foo.md"
    _, out = _run(_write(unc))
    assert not _is_deny(out)


# --- Tool-name filter (matcher should keep these out, but defensive pass-through) ---


def test_read_tool_passed_through() -> None:
    # If the matcher misfires and Read reaches the hook, allow.
    _, out = _run({"tool_name": "Read", "tool_input": {"file_path": "services/api/main.py"}})
    assert not _is_deny(out)


def test_bash_tool_passed_through() -> None:
    # Bash is in disallowedTools at the subagent level; if it somehow
    # reaches this hook, this hook does not opine — Bash deny lives in
    # the allowlist + G5, not here.
    _, out = _run({"tool_name": "Bash", "tool_input": {"command": "git commit"}})
    assert not _is_deny(out)


# --- Fail-closed discipline (THIS IS THE H2 DIFFERENCE FROM C4) ---


def test_malformed_stdin_denies() -> None:
    """H2 is fail-CLOSED: malformed JSON → deny (C4 by contrast is fail-OPEN)."""
    rc, out = _run("not json")
    assert rc == 0
    assert _is_deny(out)
    assert out is not None
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "malformed JSON" in reason
    assert "Fail-closed" in reason


def test_missing_tool_input_denies() -> None:
    """Missing `tool_input` → deny (fail-closed)."""
    _, out = _run({"tool_name": "Write"})
    assert _is_deny(out)


def test_non_object_tool_input_denies() -> None:
    """Non-object `tool_input` → deny (fail-closed)."""
    _, out = _run({"tool_name": "Write", "tool_input": "not-a-dict"})
    assert _is_deny(out)


def test_missing_file_path_denies() -> None:
    """Missing `file_path` → deny (fail-closed, differs from C4)."""
    _, out = _run({"tool_name": "Write", "tool_input": {"content": "x"}})
    assert _is_deny(out)


def test_non_string_file_path_denies() -> None:
    """Non-string `file_path` → deny (fail-closed, differs from C4)."""
    _, out = _run(_write(42))
    assert _is_deny(out)


def test_empty_file_path_denies() -> None:
    _, out = _run(_write(""))
    assert _is_deny(out)


# --- Deny reason citations ---


def test_deny_reason_cites_plan_step() -> None:
    _, out = _run(_write("services/api/main.py"))
    assert _is_deny(out)
    assert out is not None
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "PLAN-0009" in reason
    assert "Step 1b" in reason
    assert "docs/adr" in reason
    assert "docs/plans" in reason


def test_deny_reason_cites_adr_authority() -> None:
    """Outside-allowlist deny references ADR-013 D2 / ADR-012 D4.3."""
    _, out = _run(_write("services/api/main.py"))
    assert out is not None
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "ADR-013" in reason or "ADR-012" in reason


# --- ADR-013 D2 bypass-immunity regression guard (Step 6 Phase 1.5) ---


def test_bypass_permissions_still_denies_outside_allowlist() -> None:
    """ADR-013 D2 binding: ``PreToolUse deny`` is deterministic and bypass-immune.

    The harness ``permission_mode: bypassPermissions`` flag must NOT short-circuit
    this hook's allowlist decision. Asserts the hook reads its own logic
    (file_path vs allowlist) and ignores permission_mode entirely — this is
    cheap insurance against a future implementation that accidentally
    short-circuits on bypass. The G5 sibling carries the same guard
    (`test_pretooluse_git_deny.py::test_subagent_bypass_permissions_still_denied`);
    H2 was uncovered until session-14 Step 6 Phase 1.5 closeout.
    """
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": "services/api/main.py", "content": "x"},
        "permission_mode": "bypassPermissions",
    }
    _, out = _run(payload)
    assert _is_deny(out)
