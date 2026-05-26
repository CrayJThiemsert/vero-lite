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


# --- PLAN-0009 Step 5 — composed G5 4-case identity matrix ---
#
# allow_commit = (agent_id is None) and (CLAUDE_TIER == "code")
#
# Case 1 — main Code interactive: agent_id absent + tier=code → allow
# Case 2 — main Code scheduled: agent_id absent + tier=code → allow
# Case 3 — subagent: agent_id PRESENT, regardless of inherited tier → deny
# Case 4 — Cowork: agent_id absent + tier other/empty → deny


def _bash_with_agent(command: str, agent_type: str, agent_id: str = "sub-001") -> Payload:
    return {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "agent_id": agent_id,
        "agent_type": agent_type,
    }


# Case 1 + 2 already covered by test_plain_commit_allowed_with_code_tier.


def test_subagent_plan_drafter_commit_denied_even_with_code_tier() -> None:
    """Case 3 — plan-drafter subagent inherits CLAUDE_TIER=code from main
    but the composed check still denies based on agent_id presence."""
    _, out = _run(
        _bash_with_agent("git commit -m draft", "plan-drafter"),
        {"CLAUDE_TIER": "code"},
    )
    assert _is_deny(out)
    assert out is not None
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "subagent" in reason.lower()
    assert "plan-drafter" in reason
    assert "Step 1b" in reason or "PLAN-0009" in reason


def test_subagent_explore_research_push_denied() -> None:
    """Case 3 (explore-research variant) — the read-only subagent has no
    Bash in its allowlist, but defense-in-depth: even if it somehow
    reached this hook, the composed check still denies."""
    _, out = _run(
        _bash_with_agent("git push origin main", "explore-research"),
        {"CLAUDE_TIER": "code"},
    )
    assert _is_deny(out)
    assert out is not None
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "explore-research" in reason


def test_subagent_denied_regardless_of_tier_value() -> None:
    """Subagent denial does NOT depend on CLAUDE_TIER — present agent_id
    is sufficient. Tests with tier unset, with tier=cowork, with tier=code."""
    for env_override in (None, {"CLAUDE_TIER": "cowork"}, {"CLAUDE_TIER": "code"}):
        _, out = _run(
            _bash_with_agent("git commit -m x", "plan-drafter"),
            env_override,
        )
        assert _is_deny(out), f"subagent with env={env_override} should still deny"


def test_subagent_with_empty_agent_id_treated_as_main() -> None:
    """Defensive — an empty-string agent_id should NOT trigger subagent
    branch (the primitive's contract is "present only when the hook fires
    inside a subagent call"; empty means absent)."""
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "git commit -m foo"},
        "agent_id": "",
        "agent_type": "",
    }
    _, out = _run(payload, {"CLAUDE_TIER": "code"})
    assert not _is_deny(out)


def test_subagent_with_whitespace_only_agent_id_treated_as_main() -> None:
    """Edge case: whitespace-only agent_id is not a real identifier."""
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "git commit -m foo"},
        "agent_id": "   ",
    }
    _, out = _run(payload, {"CLAUDE_TIER": "code"})
    assert not _is_deny(out)


def test_subagent_non_string_agent_id_treated_as_main() -> None:
    """Defensive — non-string agent_id (numeric, null) is not a valid
    subagent identifier per the primitive's documented schema."""
    for bad in (None, 0, [], {}):
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "git commit"},
            "agent_id": bad,
        }
        _, out = _run(payload, {"CLAUDE_TIER": "code"})
        assert not _is_deny(out), f"non-string agent_id={bad!r} should not trigger subagent branch"


def test_subagent_with_git_status_passes() -> None:
    """Subagent calling a non-gated git verb (status / log / diff) → allow.
    The composed check only fires on the gated subcommands."""
    _, out = _run(
        _bash_with_agent("git status", "plan-drafter"),
        {"CLAUDE_TIER": "code"},
    )
    assert not _is_deny(out)


def test_subagent_bypass_permissions_still_denied() -> None:
    """AC-6 bypass-immunity for subagent case — even with bypassPermissions
    in the harness, the hook still fires and the composed check still denies.
    The permission_mode field is informational; the deny is unconditional."""
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "git commit -m x"},
        "agent_id": "sub-002",
        "agent_type": "plan-drafter",
        "permission_mode": "bypassPermissions",
    }
    _, out = _run(payload, {"CLAUDE_TIER": "code"})
    assert _is_deny(out)


def test_main_agent_with_agent_type_but_no_agent_id_treated_as_main() -> None:
    """A payload with `agent_type` (e.g., from a top-level --agent flag) but
    no `agent_id` — the primitive's contract says agent_id is present "only
    when the hook fires inside a subagent call." So agent_type alone is not
    a subagent signal."""
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "git commit -m main"},
        "agent_type": "general-purpose",
    }
    _, out = _run(payload, {"CLAUDE_TIER": "code"})
    assert not _is_deny(out)


def test_subagent_deny_reason_cites_authority() -> None:
    """The deny reason for a subagent must cite the authority chain so a
    reader (or a future Code session debugging the deny) can trace it."""
    _, out = _run(
        _bash_with_agent("git commit", "plan-drafter"),
        {"CLAUDE_TIER": "code"},
    )
    assert out is not None
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    # Must cite the plan + ADR + CLAUDE.md anchors so the deny is auditable
    assert "PLAN-0009" in reason
    assert "ADR-013" in reason
    assert "§7" in reason or "CLAUDE.md" in reason


# --- Robustness against malformed top-level payload ---


def test_non_dict_payload_does_not_block() -> None:
    """Top-level payload that is JSON but not a dict (e.g., a list, a
    bare string) — treat as malformed, do not block."""
    for bad in ("[]", '"string"', "null", "42"):
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=bad,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""


def test_non_dict_tool_input_does_not_match() -> None:
    """tool_input that is not a dict (e.g., a string) — skip cleanly."""
    payload = {"tool_name": "Bash", "tool_input": "not-a-dict"}
    _, out = _run(payload)
    assert not _is_deny(out)
