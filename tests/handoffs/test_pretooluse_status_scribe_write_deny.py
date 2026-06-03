"""Tests for .claude/hooks/pretooluse_status_scribe_write_deny.py.

This hook enforces the `status-scribe` subagent write-path allowlist,
mirroring the H2 pattern of `pretooluse_plan_subagent_write_deny.py`
(PLAN-0009 Step 1b §5) but narrowed to a **single file**: `docs/STATUS.md`.

Two boundaries differ from the `plan-drafter` sibling and are asserted here:

* The allowlist is exactly `docs/STATUS.md` — `docs/adr/*.md` and
  `docs/plans/*.md` (which the `plan-drafter` hook *allows*) are **denied**
  here, because STATUS reconciliation is `status-scribe`'s only artifact.
* Like H2 and per ADR-013 D2 the hook is **fail-CLOSED**: malformed JSON,
  missing `tool_input`, or a non-string `file_path` all deny the call.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / ".claude" / "hooks" / "pretooluse_status_scribe_write_deny.py"

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


# --- Allow cases (exactly docs/STATUS.md) ---


def test_status_write_allowed() -> None:
    rc, out = _run(_write("docs/STATUS.md"))
    assert rc == 0
    assert not _is_deny(out)


def test_status_edit_allowed() -> None:
    _, out = _run(_edit("docs/STATUS.md"))
    assert not _is_deny(out)


# --- Deny cases: the plan-drafter ALLOW surface is DENIED here ---


def test_adr_write_denied() -> None:
    # docs/adr/*.md is the plan-drafter surface, NOT status-scribe's.
    _, out = _run(_write("docs/adr/0014-new-decision.md"))
    assert _is_deny(out)


def test_plan_write_denied() -> None:
    _, out = _run(_write("docs/plans/0011-new-plan.md"))
    assert _is_deny(out)


def test_plan_edit_denied() -> None:
    _, out = _run(_edit("docs/plans/0009-subagent-topology.md"))
    assert _is_deny(out)


def test_plan_done_subdir_denied() -> None:
    # status-scribe must never `git mv` / write under done/; the direct
    # write is denied because it is not docs/STATUS.md.
    _, out = _run(_write("docs/plans/done/0007-foo.md"))
    assert _is_deny(out)


# --- Deny cases: general out-of-scope paths ---


def test_services_write_denied() -> None:
    _, out = _run(_write("services/api/main.py"))
    assert _is_deny(out)


def test_tests_write_denied() -> None:
    _, out = _run(_write("tests/test_foo.py"))
    assert _is_deny(out)


def test_claude_md_write_denied() -> None:
    _, out = _run(_write("CLAUDE.md"))
    assert _is_deny(out)


def test_lessons_write_denied() -> None:
    _, out = _run(_write("docs/lessons/0011-new-lesson.md"))
    assert _is_deny(out)


def test_runbooks_write_denied() -> None:
    _, out = _run(_write("docs/runbooks/foo.md"))
    assert _is_deny(out)


def test_conventions_write_denied() -> None:
    _, out = _run(_write("docs/conventions/foo.md"))
    assert _is_deny(out)


def test_edit_outside_allowed_denied() -> None:
    _, out = _run(_edit("services/api/main.py"))
    assert _is_deny(out)


# --- Deny cases: near-miss paths against the single-file allowlist ---


def test_status_backup_suffix_denied() -> None:
    # docs/STATUS.md.bak is NOT docs/STATUS.md (exact match only).
    _, out = _run(_write("docs/STATUS.md.bak"))
    assert _is_deny(out)


def test_status_alt_extension_denied() -> None:
    _, out = _run(_write("docs/STATUS.markdown"))
    assert _is_deny(out)


def test_status_at_repo_root_denied() -> None:
    # STATUS.md at repo root (not under docs/) is a different path.
    _, out = _run(_write("STATUS.md"))
    assert _is_deny(out)


def test_status_in_other_subdir_denied() -> None:
    _, out = _run(_write("docs/archive/STATUS.md"))
    assert _is_deny(out)


def test_status_lowercase_denied() -> None:
    # Path comparison is exact/case-sensitive; docs/status.md != docs/STATUS.md.
    _, out = _run(_write("docs/status.md"))
    assert _is_deny(out)


# --- Path normalization (cross-platform) — the one allowed file ---


def test_absolute_repo_path_status_allowed() -> None:
    abs_path = str(REPO_ROOT / "docs" / "STATUS.md")
    _, out = _run(_write(abs_path))
    assert not _is_deny(out)


def test_absolute_repo_path_services_denied() -> None:
    abs_path = str(REPO_ROOT / "services" / "api" / "main.py")
    _, out = _run(_write(abs_path))
    assert _is_deny(out)


def test_windows_unc_status_allowed() -> None:
    unc = r"\\wsl.localhost\ubuntu-24.04\home\crayj\work\vero-lite\docs\STATUS.md"
    _, out = _run(_write(unc))
    assert not _is_deny(out)


def test_windows_unc_services_denied() -> None:
    unc = r"\\wsl.localhost\ubuntu-24.04\home\crayj\work\vero-lite\services\api\main.py"
    _, out = _run(_write(unc))
    assert _is_deny(out)


def test_windows_unc_plans_denied() -> None:
    unc = r"\\wsl.localhost\ubuntu-24.04\home\crayj\work\vero-lite\docs\plans\0011-foo.md"
    _, out = _run(_write(unc))
    assert _is_deny(out)


# --- Tool-name filter (matcher should keep these out, but defensive pass-through) ---


def test_read_tool_passed_through() -> None:
    # If the matcher misfires and Read reaches the hook, allow.
    _, out = _run({"tool_name": "Read", "tool_input": {"file_path": "services/api/main.py"}})
    assert not _is_deny(out)


def test_bash_tool_passed_through() -> None:
    # Bash is in disallowedTools at the subagent level; if it somehow reaches
    # this hook, this hook does not opine — Bash deny lives in the allowlist
    # + G5, not here.
    _, out = _run({"tool_name": "Bash", "tool_input": {"command": "git commit"}})
    assert not _is_deny(out)


# --- Fail-closed discipline (mirrors the H2 boundary) ---


def test_malformed_stdin_denies() -> None:
    """Fail-CLOSED: malformed JSON → deny."""
    rc, out = _run("not json")
    assert rc == 0
    assert _is_deny(out)
    assert out is not None
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "malformed JSON" in reason
    assert "Fail-closed" in reason


def test_missing_tool_input_denies() -> None:
    _, out = _run({"tool_name": "Write"})
    assert _is_deny(out)


def test_non_object_tool_input_denies() -> None:
    _, out = _run({"tool_name": "Write", "tool_input": "not-a-dict"})
    assert _is_deny(out)


def test_missing_file_path_denies() -> None:
    _, out = _run({"tool_name": "Write", "tool_input": {"content": "x"}})
    assert _is_deny(out)


def test_non_string_file_path_denies() -> None:
    _, out = _run(_write(42))
    assert _is_deny(out)


def test_empty_file_path_denies() -> None:
    _, out = _run(_write(""))
    assert _is_deny(out)


# --- Deny reason citations ---


def test_deny_reason_cites_status_scribe_and_target() -> None:
    _, out = _run(_write("docs/plans/0011-foo.md"))
    assert _is_deny(out)
    assert out is not None
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "status-scribe" in reason
    assert "docs/STATUS.md" in reason


def test_deny_reason_cites_adr_authority() -> None:
    """Outside-allowlist deny references ADR-013 D2 / ADR-012 D4.3."""
    _, out = _run(_write("services/api/main.py"))
    assert out is not None
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "ADR-013" in reason or "ADR-012" in reason


# --- ADR-013 D2 bypass-immunity regression guard ---


def test_bypass_permissions_still_denies_outside_allowlist() -> None:
    """ADR-013 D2 binding: ``PreToolUse deny`` is deterministic and bypass-immune.

    The harness ``permission_mode: bypassPermissions`` flag must NOT
    short-circuit this hook's allowlist decision. Mirrors the
    `plan-drafter` H2 guard
    (`test_pretooluse_plan_subagent_write_deny.py::test_bypass_permissions_still_denies_outside_allowlist`).
    """
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": "services/api/main.py", "content": "x"},
        "permission_mode": "bypassPermissions",
    }
    _, out = _run(payload)
    assert _is_deny(out)


def test_bypass_permissions_still_allows_status_md() -> None:
    """Bypass-immunity cuts both ways: the allowed file stays allowed."""
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": "docs/STATUS.md", "content": "x"},
        "permission_mode": "bypassPermissions",
    }
    _, out = _run(payload)
    assert not _is_deny(out)
