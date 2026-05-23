"""Tests for .claude/hooks/pretooluse_git_deny.py (PLAN-0007 AC-2)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / ".claude" / "hooks" / "pretooluse_git_deny.py"

Payload = dict[str, Any]
Parsed = dict[str, Any] | None


def _run(payload: Payload, env_override: dict[str, str] | None = None) -> tuple[int, Parsed]:
    env = os.environ.copy()
    env.pop("CLAUDE_TIER", None)
    if env_override:
        env.update(env_override)
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


def _bash(command: str) -> Payload:
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def test_plain_commit_denied_without_env() -> None:
    rc, out = _run(_bash("git commit -m foo"))
    assert rc == 0
    assert _is_deny(out)


def test_plain_commit_allowed_with_code_tier() -> None:
    rc, out = _run(_bash("git commit -m foo"), {"CLAUDE_TIER": "code"})
    assert rc == 0
    assert not _is_deny(out)
    assert out is None or "hookSpecificOutput" not in out


def test_cd_and_commit_denied() -> None:
    _, out = _run(_bash("cd /tmp && git commit"))
    assert _is_deny(out)


def test_env_prefixed_push_denied() -> None:
    _, out = _run(_bash("FOO=bar git push origin main"))
    assert _is_deny(out)


def test_git_dash_c_commit_denied() -> None:
    _, out = _run(_bash("git -C /tmp commit -m x"))
    assert _is_deny(out)


def test_chained_merge_denied() -> None:
    _, out = _run(_bash("ls && git merge feat"))
    assert _is_deny(out)


def test_git_status_allowed() -> None:
    _, out = _run(_bash("git status"))
    assert not _is_deny(out)


def test_substring_no_boundary_allowed() -> None:
    # `longit commit` must not match — boundary anchor.
    _, out = _run(_bash("echo longit commit"))
    assert not _is_deny(out)


def test_non_bash_tool_skipped(tmp_path: Path) -> None:
    _, out = _run({"tool_name": "Read", "tool_input": {"file_path": str(tmp_path / "x")}})
    assert not _is_deny(out)


def test_inline_env_spoof_does_not_bypass() -> None:
    # The bypass attempt: inject CLAUDE_TIER=code into the command itself.
    # The hook reads its OWN env, not the tool_input string — must still deny.
    _, out = _run(_bash("CLAUDE_TIER=code git commit -m spoof"))
    assert _is_deny(out)


def test_wrong_tier_value_denied() -> None:
    _, out = _run(_bash("git commit"), {"CLAUDE_TIER": "chat"})
    assert _is_deny(out)


def test_uppercase_tier_allowed() -> None:
    # Case-insensitive tier check (`.strip().lower() == "code"`).
    _, out = _run(_bash("git commit"), {"CLAUDE_TIER": "CODE"})
    assert not _is_deny(out)


def test_backtick_chain_denied() -> None:
    _, out = _run(_bash("echo `git commit -m x`"))
    assert _is_deny(out)


def test_bash_wrapper_denied() -> None:
    _, out = _run(_bash('bash -c "git commit"'))
    assert _is_deny(out)


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


def test_deny_reason_mentions_claude_tier() -> None:
    _, out = _run(_bash("git commit"))
    assert _is_deny(out)
    assert out is not None
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "CLAUDE_TIER" in reason
    assert "code" in reason.lower()
