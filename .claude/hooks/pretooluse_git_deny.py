#!/usr/bin/env python3
"""PreToolUse hook — composed G5: deny `git commit|push|merge` unless
the call is from the main Code agent (subagent-aware per PLAN-0009 Step 1b).

Implements the composed G5 identity check shared between Phase 3 (subagents)
and Phase 3.5 (scheduled tasks) per PLAN-0009 Step 1b §1::

    allow_commit = (agent_id is None) and (CLAUDE_TIER == "code")

Four-case identity matrix (binding for AC-3 / AC-4 / AC-6):

================================  ===========  ============  ========
Case                              agent_id     CLAUDE_TIER   Verdict
================================  ===========  ============  ========
Main Code interactive             absent       "code"        allow
Main Code scheduled (Phase 3.5)   absent       "code"        allow
Subagent (plan-drafter, etc)      PRESENT      inherited     DENY
Cowork (impossible reach today)   absent       other/empty   DENY
================================  ===========  ============  ========

The ``agent_id`` field in hook stdin is the load-bearing subagent identity
signal per PLAN-0009 Step 1a Q3 (Anthropic primitive documentation). It is
present (and only when) the hook fires inside a subagent call. The
``CLAUDE_TIER`` env var distinguishes main-Code from Cowork.

Enforces ADR-009 D2 ("only Code commits") deterministically per ADR-013 D2,
extended to cover the subagent case per ADR-013 D1 (autonomy axis
relocation — subagents are in Code's process tree but explicitly write-
bounded + commit-bounded by the harness, not by prompt).

The hook is bypass-immune against ``permission_mode=bypassPermissions``
because hook decisions run regardless of permission mode (Claude Code hooks
reference, "Exit code 2 behavior per event" table). It is also immune to
inline command spoofing (e.g. ``bash -c 'CLAUDE_TIER=code git commit'``)
because the hook reads its OWN process env, not the tool_input's command
string.

Phase 1 shipped the CLAUDE_TIER-only check (PLAN-0007 AC-2). Phase 2 added
the Sonnet classifier reading ``.claude/autonomy-triggers.md`` (PLAN-0008
Step 5). PLAN-0009 Step 5 extends G5 to composed (this file).
"""

from __future__ import annotations

import json
import os
import re
import sys

# Match git commit/push/merge anywhere in the command, tolerating:
#   - leading env-var assignments (FOO=bar git commit ...)
#   - command separators (; && || |)
#   - cd / pushd prefixes (cd path && git commit ...)
#   - git -C <path> commit / push / merge
#   - bash -c '...' wrapping (the inner command is scanned as-is)
# Word boundary anchors prevent matching strings like "longit commit".
_GIT_DANGER_RE = re.compile(
    r"(?:^|[\s;&|`'\"()])"  # boundary: SOL, whitespace, ; & | ` ' " ( )
    r"git\s+"  # the git verb (after env/cd stripping or chaining)
    r"(?:-C\s+\S+\s+)?"  # optional -C <path>
    r"(?:commit|push|merge)"  # the gated subcommands
    r"(?:\s|$|['\")])"  # trailing boundary too (handles `bash -c 'git commit'`)
)


def _is_code_tier() -> bool:
    return os.environ.get("CLAUDE_TIER", "").strip().lower() == "code"


def _is_subagent_call(payload: dict[str, object]) -> bool:
    """A subagent call carries an ``agent_id`` in the hook stdin per
    PLAN-0009 Step 1a Q3 (Anthropic primitive documentation).

    Treats empty-string and falsy ``agent_id`` as "not a subagent" —
    only a present, non-empty identifier means a subagent is the caller.
    This matches the documented primitive behavior: the field is "Present
    only when the hook fires inside a subagent call."
    """
    agent_id = payload.get("agent_id")
    if not isinstance(agent_id, str):
        return False
    return bool(agent_id.strip())


def _emit_deny(reason: str) -> int:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    return 0


def _subagent_deny_reason(payload: dict[str, object]) -> str:
    agent_type_raw = payload.get("agent_type")
    agent_id_raw = payload.get("agent_id")
    agent_type = agent_type_raw if isinstance(agent_type_raw, str) else "<unknown>"
    agent_id = agent_id_raw if isinstance(agent_id_raw, str) else "<unknown>"
    return (
        f"PLAN-0009 Step 1b §1 composed G5: subagent `{agent_type}` "
        f"(agent_id={agent_id}) cannot run git commit/push/merge. Per "
        f"ADR-013 D1+D2, governance subagents (plan-drafter, "
        f"explore-research) are write-bounded by frontmatter and "
        f"commit-bounded at this hook layer regardless of CLAUDE_TIER "
        f"inheritance. The main Code agent commits via PR per CLAUDE.md "
        f"§7. If this subagent legitimately produced a draft that needs "
        f"committing, return the artifact path in the final message and "
        f"let the main agent handle the git operation."
    )


def _tier_deny_reason() -> str:
    current = os.environ.get("CLAUDE_TIER", "<unset>") or "<empty>"
    return (
        "ADR-009 D2 / ADR-013 D2: git commit/push/merge is gated to "
        f"Code-tier sessions. CLAUDE_TIER is '{current}', expected 'code'. "
        "Launch a Code-tier Claude Code session (set CLAUDE_TIER=code in "
        "the launching shell, propagate via WSLENV on Windows) or surface "
        "the change via a handoff for the Code tier to commit."
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Malformed input — don't block (fail-open for non-blocking parse errors;
        # the hook protocol expects valid JSON, so this should not happen).
        return 0

    if not isinstance(payload, dict):
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    command = tool_input.get("command", "")
    if not isinstance(command, str) or not _GIT_DANGER_RE.search(command):
        return 0

    # Composed G5 per PLAN-0009 Step 1b §1:
    #   allow_commit = (agent_id is None) and (CLAUDE_TIER == "code")
    # First check: is this a subagent call? If so, deny regardless of tier
    # (defense-in-depth — subagents inherit CLAUDE_TIER=code from main, so
    # the tier check alone would incorrectly allow). Check subagent FIRST
    # so the deny reason cites the subagent identity, not the tier.
    if _is_subagent_call(payload):
        return _emit_deny(_subagent_deny_reason(payload))

    # Main agent (no agent_id): check tier. Allows interactive + scheduled
    # Code (both have CLAUDE_TIER=code); denies Cowork (empty/other tier).
    if _is_code_tier():
        return 0

    return _emit_deny(_tier_deny_reason())


if __name__ == "__main__":
    raise SystemExit(main())
