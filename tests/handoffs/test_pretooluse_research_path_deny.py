"""Tests for .claude/hooks/pretooluse_research_path_deny.py.

Enforces ``cowork_tab_instructions.md`` line 192 + ``.gitignore`` lines 49-51:
writes under ``docs/research/`` are restricted to ``docs/research/private/**``.
N=2 incident pattern motivates deterministic enforcement; see hook docstring.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / ".claude" / "hooks" / "pretooluse_research_path_deny.py"

Payload = dict[str, Any]
Parsed = dict[str, Any] | None


def _run(payload: Payload) -> tuple[int, Parsed]:
    env = os.environ.copy()
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
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


def _write(file_path: str) -> Payload:
    return {"tool_name": "Write", "tool_input": {"file_path": file_path, "content": "x"}}


def _edit(file_path: str) -> Payload:
    return {
        "tool_name": "Edit",
        "tool_input": {"file_path": file_path, "old_string": "a", "new_string": "b"},
    }


# --- Allow cases (private/ + outside research/ entirely) ---


def test_private_subdir_allowed() -> None:
    rc, out = _run(_write("docs/research/private/2026-05-24-foo.md"))
    assert rc == 0
    assert not _is_deny(out)


def test_private_nested_allowed() -> None:
    _, out = _run(_write("docs/research/private/sub/deep/note.md"))
    assert not _is_deny(out)


def test_strategy_public_allowed() -> None:
    _, out = _run(_write("docs/strategy/public/brief.md"))
    assert not _is_deny(out)


def test_strategy_private_allowed() -> None:
    _, out = _run(_write("docs/strategy/private/note.md"))
    assert not _is_deny(out)


def test_docs_root_allowed() -> None:
    _, out = _run(_write("docs/STATUS.md"))
    assert not _is_deny(out)


def test_services_path_allowed() -> None:
    _, out = _run(_write("services/api/main.py"))
    assert not _is_deny(out)


# --- Deny cases (the N=2 pattern + variants) ---


def test_research_public_denied() -> None:
    # The exact 2026-05-23 incident path.
    _, out = _run(_write("docs/research/public/chat_harness_extension_points_analyzed.md"))
    assert _is_deny(out)


def test_research_bare_file_denied() -> None:
    # No subdir at all — also forbidden.
    _, out = _run(_write("docs/research/random-note.md"))
    assert _is_deny(out)


def test_research_arbitrary_subdir_denied() -> None:
    _, out = _run(_write("docs/research/drafts/foo.md"))
    assert _is_deny(out)


def test_edit_tool_also_denied() -> None:
    _, out = _run(_edit("docs/research/public/oldfile.md"))
    assert _is_deny(out)


# --- Path normalization ---


def test_absolute_repo_path_denied() -> None:
    abs_path = str(REPO_ROOT / "docs" / "research" / "public" / "foo.md")
    _, out = _run(_write(abs_path))
    assert _is_deny(out)


def test_absolute_repo_path_private_allowed() -> None:
    abs_path = str(REPO_ROOT / "docs" / "research" / "private" / "foo.md")
    _, out = _run(_write(abs_path))
    assert not _is_deny(out)


def test_windows_unc_research_public_denied() -> None:
    # Simulate Claude Code on Windows writing through the WSL UNC mount.
    unc = r"\\wsl.localhost\ubuntu-24.04\home\crayj\work\vero-lite\docs\research\public\x.md"
    _, out = _run(_write(unc))
    assert _is_deny(out)


def test_windows_unc_research_private_allowed() -> None:
    unc = r"\\wsl.localhost\ubuntu-24.04\home\crayj\work\vero-lite\docs\research\private\x.md"
    _, out = _run(_write(unc))
    assert not _is_deny(out)


# --- Tool-name filter + payload edge cases ---


def test_non_write_tool_skipped() -> None:
    _, out = _run({"tool_name": "Read", "tool_input": {"file_path": "docs/research/public/x.md"}})
    assert not _is_deny(out)


def test_bash_tool_skipped() -> None:
    # Even if a Bash command writes to a research path, this hook does not fire
    # (other guards: shell-level writes aren't the Cowork failure mode this row
    # targets; the git-deny hook handles Bash separately).
    _, out = _run({"tool_name": "Bash", "tool_input": {"command": "echo > docs/research/x"}})
    assert not _is_deny(out)


def test_missing_file_path_allowed() -> None:
    _, out = _run({"tool_name": "Write", "tool_input": {}})
    assert not _is_deny(out)


def test_non_string_file_path_allowed() -> None:
    _, out = _run({"tool_name": "Write", "tool_input": {"file_path": 42}})
    assert not _is_deny(out)


def test_malformed_stdin_does_not_block() -> None:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_deny_reason_cites_authoritative_sources() -> None:
    _, out = _run(_write("docs/research/public/x.md"))
    assert _is_deny(out)
    assert out is not None
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "cowork_tab_instructions" in reason
    assert "private" in reason
    assert "autonomy-triggers" in reason
