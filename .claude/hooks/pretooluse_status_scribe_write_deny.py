#!/usr/bin/env python3
"""PreToolUse hook — restrict ``status-scribe`` subagent writes to ``docs/STATUS.md``.

Subagent-scoped hook wired in ``.claude/agents/status-scribe.md`` frontmatter
under ``hooks.PreToolUse`` with matcher ``Write|Edit``. Mirrors the H2
write-path allowlist pattern established by
``pretooluse_plan_subagent_write_deny.py`` (PLAN-0009 Step 1b §5), narrowed to
the single file ``status-scribe`` is allowed to touch.

Allowed write/edit target (exactly one path):

* ``docs/STATUS.md``

Everything else is denied. Like its ``plan-drafter`` sibling and per ADR-013
D2 the hook is **fail-closed**: malformed stdin and malformed ``tool_input``
deny the call rather than passing through. ``status-scribe`` reconciles the
single volatile state file; the autonomy-governance write-path boundary must
default to deny when the harness contract is violated.

Rationale for a single-file allowlist (not a ``docs/`` prefix): STATUS
reconciliation is the only artifact this subagent authors. Archival
(``git mv`` to ``done/``), ADR/PLAN drafting (``plan-drafter``), and every
*commit* (Code via PR per CLAUDE.md §7 / ADR-009 D2) stay off this surface by
construction.

Bypass-immunity: the hook fires regardless of ``permissionMode`` (including
``bypassPermissions``).

This hook intentionally does **not** inspect ``agent_id`` / ``agent_type``.
Subagent scoping comes from the frontmatter wiring; if a future change moves
the hook to project-level the test suite must fail loudly so the boundary
inversion is caught at review time.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ALLOWED_PATH = "docs/STATUS.md"
WATCHED_TOOLS = ("Write", "Edit")


def _normalize_to_repo_relative(path_str: str) -> str | None:
    """Return a POSIX path relative to REPO_ROOT, or None if the path is
    outside the repo.

    Mirrors the normalization in ``pretooluse_plan_subagent_write_deny.py``
    so cross-platform inputs (Windows UNC, drive-letter, absolute POSIX) are
    handled identically by both hooks.
    """
    if not path_str:
        return None
    normalized = path_str.replace("\\", "/")
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


def _is_allowed_path(rel_posix: str) -> bool:
    return rel_posix == ALLOWED_PATH


def _deny(reason: str) -> int:
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


def _reason_outside_allowlist(rel: str) -> str:
    return (
        f"status-scribe (H2-derived): the `status-scribe` subagent may only "
        f"`Write`/`Edit` `docs/STATUS.md`. Target `{rel}` is outside the "
        f"allowlist. STATUS reconciliation is this subagent's only artifact; "
        f"ADR/PLAN drafts belong to `plan-drafter`, archival (`git mv`) and "
        f"all commits belong to the main Code agent via a `docs/*` branch + "
        f"PR (CLAUDE.md §7 / ADR-009 D2). `status-scribe` is author-bounded "
        f"by ADR-013 D2 / ADR-012 D4.3 by design."
    )


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        return _deny(
            "status-scribe (H2-derived): malformed JSON on hook stdin. "
            "Fail-closed deny per ADR-013 D2 — the hook contract requires "
            "valid JSON; an invalid payload cannot be reasoned about, so "
            "the write is blocked rather than pass through."
        )

    tool_name = payload.get("tool_name")
    if tool_name not in WATCHED_TOOLS:
        # Subagent-scoped matcher should prevent non-Write/Edit calls from
        # reaching this hook; if one does, pass through (the matcher is the
        # selector, not this hook).
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return _deny(
            "status-scribe (H2-derived): missing or non-object `tool_input`. "
            "Fail-closed deny — well-formed Write/Edit calls always carry a "
            "`tool_input` object with `file_path`."
        )

    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or not file_path:
        return _deny(
            "status-scribe (H2-derived): missing or non-string `file_path`. "
            "Fail-closed deny — a Write/Edit without a parseable path "
            "cannot be checked against the docs/STATUS.md allowlist."
        )

    rel = _normalize_to_repo_relative(file_path)
    if rel is None:
        return _deny(
            f"status-scribe (H2-derived): path `{file_path}` resolves outside "
            f"the vero-lite repo root. Fail-closed deny — `status-scribe` "
            f"may only write the repo-tracked `docs/STATUS.md`."
        )

    if _is_allowed_path(rel):
        return 0

    return _deny(_reason_outside_allowlist(rel))


if __name__ == "__main__":
    raise SystemExit(main())
