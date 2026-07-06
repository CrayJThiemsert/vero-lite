"""UserPromptSubmit hook — soft nudge toward the ``next-work-analyst`` skill.

When Cray opens a new session by pointing it at a handoff (the confirmed
orientation pattern — the prompt references a ``.claude/handoffs/...`` path),
inject a **non-blocking** ``additionalContext`` nudge so the main agent OFFERS
the ``next-work-analyst`` skill (rank the next work, ELI-CRAY) after it summarizes
where things stand. It never auto-runs the skill and never blocks the prompt.

Design (Cray-ratified 2026-07-06 via AskUserQuestion — "on-demand skill + soft
hook-nudge"): ``UserPromptSubmit`` (not ``PostToolUse:Read``) so the tax is one
cheap check per user turn, not a python spawn on every Read. Fires **once per
session** (a gitignored marker under ``.claude/state/``). Fail-open by
construction: any error / any non-orientation prompt exits 0 with no output, so
the prompt always proceeds unchanged.

Not a governance hook (no G1/G2/L1/goal-gate semantics) — purely advisory.
Stdlib-only for cross-platform robustness (Cray on Windows; repo in WSL).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_DIR = REPO_ROOT / ".claude" / "state"

# The orientation signal: the prompt references a handoff path (handoffs/ or handoffs\).
_HANDOFF_RE = re.compile(r"handoffs[/\\]", re.IGNORECASE)

_NUDGE = (
    "[orientation nudge — soft, once per session] The prompt references a handoff, "
    "so this looks like new-session orientation. After you summarize where things "
    "stand, OFFER the `next-work-analyst` skill (do NOT auto-run it): it ranks the "
    "candidate next-work items by value x effort x dependency x design-readiness — "
    "grounded against the actual code/ADRs (full Explore fan-out), delivered "
    "ELI-CRAY — and ends with a recommendation + a question. Mention it in one line; "
    "let Cray opt in."
)


def _already_nudged(session_id: str) -> bool:
    """True (and mark) once per session. Any FS error → treat as not-yet, fail-open."""
    if not session_id:
        return False
    marker = STATE_DIR / f".next_work_nudge.{re.sub(r'[^A-Za-z0-9_.-]', '_', session_id)}"
    try:
        if marker.exists():
            return True
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        marker.write_text("1", encoding="utf-8")
    except OSError:
        return False
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    prompt = payload.get("prompt") or ""
    if not isinstance(prompt, str) or not _HANDOFF_RE.search(prompt):
        return 0

    session_id = str(payload.get("session_id") or "")
    if _already_nudged(session_id):
        return 0

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": _NUDGE,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:  # a nudge hook must never break a prompt — swallow everything
        raise SystemExit(0) from None
