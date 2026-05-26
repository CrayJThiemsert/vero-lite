#!/usr/bin/env python3
"""PreToolUse hook — restrict ``plan-drafter`` subagent writes to ``docs/{adr,plans}/*.md``.

Subagent-scoped hook wired in ``.claude/agents/plan-drafter.md`` frontmatter
under ``hooks.PreToolUse`` with matcher ``Write|Edit``. Implements the H2
contract specified in `docs/plans/0009-step1b-contract-design.md` §5
(write-path allowlist for the ``plan-drafter`` subagent).

Allowed write/edit targets:

* Paths under ``docs/adr/`` ending in ``.md``
* Paths under ``docs/plans/`` ending in ``.md``

Everything else is denied. Per Step 1b §5 + ADR-013 D2 the hook is
**fail-closed**: malformed stdin and malformed ``tool_input`` deny the
call rather than passing through (the C4 ``pretooluse_research_path_deny``
sibling is fail-open because it covers a documentation policy boundary;
H2 covers an autonomy-governance write-path boundary and must default to
deny when the harness contract is violated).

Bypass-immunity: the hook fires regardless of ``permissionMode``
(including ``bypassPermissions``); AC-3 of PLAN-0009 Step 6 includes a
negative test combining ``bypassPermissions`` with a ``plan-drafter``
Write-outside-allowlist call.

This hook intentionally does **not** inspect ``agent_id`` / ``agent_type``.
Subagent scoping comes from the frontmatter wiring; if a future change
moves the hook to project-level the test suite must fail loudly so the
boundary inversion is caught at review time.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ALLOWED_PREFIXES: tuple[str, ...] = ("docs/adr/", "docs/plans/")
ALLOWED_SUFFIX = ".md"
WATCHED_TOOLS = ("Write", "Edit")


def _normalize_to_repo_relative(path_str: str) -> str | None:
    """Return a POSIX path relative to REPO_ROOT, or None if the path is
    outside the repo.

    Mirrors the normalization in ``pretooluse_research_path_deny.py`` so
    cross-platform inputs (Windows UNC, drive-letter, absolute POSIX) are
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
    if not rel_posix.endswith(ALLOWED_SUFFIX):
        return False
    return any(rel_posix.startswith(p) for p in ALLOWED_PREFIXES)


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
        f"PLAN-0009 Step 1b §5 (H2): `plan-drafter` subagent may only "
        f"`Write`/`Edit` under `docs/adr/*.md` or `docs/plans/*.md`. "
        f"Target `{rel}` is outside the allowlist. If this is a genuine "
        f"governance draft, re-target under `docs/adr/NNNN-name.md` or "
        f"`docs/plans/NNNN-name.md`. If it is non-governance work, the "
        f"main Code agent must own the write — `plan-drafter` is "
        f"author-bounded by ADR-013 D2 / ADR-012 D4.3 by design."
    )


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        return _deny(
            "PLAN-0009 Step 1b §5 (H2): malformed JSON on hook stdin. "
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
            "PLAN-0009 Step 1b §5 (H2): missing or non-object `tool_input`. "
            "Fail-closed deny — well-formed Write/Edit calls always carry a "
            "`tool_input` object with `file_path`."
        )

    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or not file_path:
        return _deny(
            "PLAN-0009 Step 1b §5 (H2): missing or non-string `file_path`. "
            "Fail-closed deny — a Write/Edit without a parseable path "
            "cannot be checked against the docs/{adr,plans}/ allowlist."
        )

    rel = _normalize_to_repo_relative(file_path)
    if rel is None:
        return _deny(
            f"PLAN-0009 Step 1b §5 (H2): path `{file_path}` resolves outside "
            f"the vero-lite repo root. Fail-closed deny — `plan-drafter` "
            f"may only write to repo-tracked governance artifacts."
        )

    if _is_allowed_path(rel):
        return 0

    return _deny(_reason_outside_allowlist(rel))


if __name__ == "__main__":
    raise SystemExit(main())
