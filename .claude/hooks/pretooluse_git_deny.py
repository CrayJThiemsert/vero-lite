#!/usr/bin/env python3
"""PreToolUse hook — deny `git commit|push|merge` unless CLAUDE_TIER=code.

Enforces ADR-009 D2 ("only Code commits") deterministically per ADR-013 D2.
Session-identity signal (ADR-013 OQ-3, Code-decided 2026-05-23): the
environment variable ``CLAUDE_TIER`` must equal ``code``. Cray sets it in the
launching shell for Code-tier Claude Code sessions; any other session (or a
session launched without the marker) is denied at the hook layer.

The hook is bypass-immune against ``permission_mode=bypassPermissions`` because
hook decisions run regardless of permission mode (Claude Code hooks reference,
"Exit code 2 behavior per event" table). It is also immune to inline command
spoofing (e.g. ``bash -c 'CLAUDE_TIER=code git commit'``) because the hook
reads its OWN process env, not the tool_input's command string.

Phase 1 scope: deterministic deny only. Phase 2 (PLAN-0008+) adds the Sonnet
classifier reading ``.claude/autonomy-triggers.md``.
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


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Malformed input — don't block (fail-open for non-blocking parse errors;
        # the hook protocol expects valid JSON, so this should not happen).
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = payload.get("tool_input", {}).get("command", "")
    if not isinstance(command, str) or not _GIT_DANGER_RE.search(command):
        return 0

    if _is_code_tier():
        return 0

    current = os.environ.get("CLAUDE_TIER", "<unset>") or "<empty>"
    reason = (
        "ADR-009 D2 / ADR-013 D2: git commit/push/merge is gated to "
        f"Code-tier sessions. CLAUDE_TIER is '{current}', expected 'code'. "
        "Launch a Code-tier Claude Code session (set CLAUDE_TIER=code in "
        "the launching shell, propagate via WSLENV on Windows) or surface "
        "the change via a handoff for the Code tier to commit."
    )
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


if __name__ == "__main__":
    raise SystemExit(main())
