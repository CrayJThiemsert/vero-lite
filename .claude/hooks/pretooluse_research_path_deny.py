#!/usr/bin/env python3
"""PreToolUse hook — deny Write/Edit under docs/research/ outside private/.

Enforces ``cowork_tab_instructions.md`` line 192 ("any file in
``docs/research/`` outside ``private/`` subdirectory" is a forbidden landing
zone) and the ``.gitignore`` policy comment at lines 49-51 (Cowork research
briefs land in ``docs/research/private/``; polished output is lifted to
``docs/strategy/public/`` via a separate Cray-mediated promotion step, never
to ``docs/research/<not-private>/``).

Motivation: same rule has been violated twice in 8 days despite explicit
documentation — Lesson #5 §10.5 (2026-05-15 audit baseline, prior incident)
and 2026-05-23 (`docs/research/public/chat_harness_extension_points_analyzed.md`).
N=2 of a documented rule meets the same threshold ADR-013 D2 applied to the
``git commit`` boundary: deterministic hook reinforcement, not another doc tweak.

Allowed targets under ``docs/research/``:

* ``docs/research/private/**`` — gitignored Cowork working notes.

Anything else under ``docs/research/`` is denied. To promote a brief, ``git mv``
to ``docs/strategy/public/`` (Cray's call) rather than dropping a fresh file
into an ad-hoc ``docs/research/<other>/`` subdir.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RESEARCH_PREFIX = "docs/research/"
PRIVATE_PREFIX = "docs/research/private/"


def _normalize_to_repo_relative(path_str: str) -> str | None:
    """Return a POSIX path relative to REPO_ROOT, or None if the path is
    outside the repo (in which case this hook has nothing to say).

    Normalization order matters: backslashes -> forward slashes BEFORE any
    pathlib op, so Windows / UNC inputs parse correctly regardless of host.
    Claude Code may launch this hook on Windows (Cray's host runs the CLI;
    file_path arrives in Windows form), while tests run on Linux.
    """
    if not path_str:
        return None
    normalized = path_str.replace("\\", "/")
    # If the path passes through a `/vero-lite/` segment (UNC, drive-letter,
    # or absolute POSIX), slice from the segment after the repo root.
    marker = "/vero-lite/"
    idx = normalized.rfind(marker)
    if idx >= 0:
        return normalized[idx + len(marker) :]
    p = Path(normalized)
    if p.is_absolute():
        try:
            return p.resolve().relative_to(REPO_ROOT).as_posix()
        except (ValueError, OSError):
            return None
    return p.as_posix()


def _is_forbidden_research_path(rel_posix: str) -> bool:
    if not rel_posix.startswith(RESEARCH_PREFIX):
        return False
    if rel_posix.startswith(PRIVATE_PREFIX):
        return False
    # Bare `docs/research/foo.md` (no subdir) and `docs/research/<anything>/...`
    # other than `private/` are both forbidden.
    return True


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Malformed input — don't block (fail-open; protocol expects valid JSON).
        return 0

    if payload.get("tool_name") not in ("Write", "Edit"):
        return 0

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str):
        return 0

    rel = _normalize_to_repo_relative(file_path)
    if rel is None or not _is_forbidden_research_path(rel):
        return 0

    reason = (
        f"cowork_tab_instructions.md line 192 + .gitignore lines 49-51: "
        f"writes under `docs/research/` are restricted to "
        f"`docs/research/private/**`. Target `{rel}` is outside the allowed "
        f"subtree. Either (a) re-target under `docs/research/private/` "
        f"(gitignored Cowork working notes), or (b) if this is a polished "
        f"deliverable for the public repo, write under `docs/strategy/public/` "
        f"instead. Motivation: same rule violated twice (Lesson #5 §10.5 + "
        f"2026-05-23 incident) — deterministic enforcement per the ADR-013 D2 "
        f"precedent. See `.claude/autonomy-triggers.md` row C4."
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
