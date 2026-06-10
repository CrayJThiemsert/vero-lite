#!/usr/bin/env python3
"""PreToolUse hook — restrict ``goal-evaluator`` writes to ``.claude/state/goal.json``.

Subagent-scoped hook wired in ``.claude/agents/goal-evaluator.md`` frontmatter
under ``hooks.PreToolUse`` with matcher ``Write|Edit`` — frontmatter-only
wiring per PLAN-0021 F-1 (``settings.json`` untouched; the exact
``status-scribe`` exemplar). Implements **ADR-0018 SD-1 = narrowed Write**
(Cray-ratified): the critic's verdict reaches the record without passing
through the creator's pen, at the cost of exactly this one deny hook.

Allowed write/edit target (exactly one path):

* ``.claude/state/goal.json``

Everything else is denied. Per ADR-013 D2 the hook is **fail-closed**:
malformed stdin and malformed ``tool_input`` deny the call rather than pass
through. The evaluator appends verdicts to the ``evaluations[]`` trail of the
goal file; every other surface — prior session narrative, plans, code, the
loop-counter/stop-chain state siblings — stays off this subagent by
construction.

Bypass-immunity: the hook fires regardless of ``permissionMode`` (including
``bypassPermissions``).

This hook intentionally does **not** inspect ``agent_id`` / ``agent_type``.
Subagent scoping comes from the frontmatter wiring; if a future change moves
the hook to project-level the test suite must fail loudly so the boundary
inversion is caught at review time.

NOTE on the env override: the *gate* honors ``CLAUDE_GOAL_PATH`` for test
isolation, but this hook deliberately allowlists only the canonical repo
path — a spawned evaluator must never be talked into writing "the goal file"
at an attacker-chosen location (the override is a test seam, not a contract).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ALLOWED_PATH = ".claude/state/goal.json"
WATCHED_TOOLS = ("Write", "Edit")


def _normalize_to_repo_relative(path_str: str) -> str | None:
    """Return a POSIX path relative to REPO_ROOT, or None if the path is
    outside the repo.

    Mirrors ``pretooluse_status_scribe_write_deny.py`` /
    ``pretooluse_plan_subagent_write_deny.py`` so cross-platform inputs
    (Windows UNC, drive-letter, absolute POSIX) behave identically across the
    H2-family hooks.
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
        f"goal-evaluator (SD-1 narrowed Write): the `goal-evaluator` subagent "
        f"may only `Write`/`Edit` `.claude/state/goal.json` (its verdict "
        f"trail). Target `{rel}` is outside the allowlist. The evaluator is a "
        f"read-only critic everywhere else by design (ADR-0018 D3/SD-1): it "
        f"never edits the work it judges, never touches sibling state files, "
        f"and never commits (ADR-009 D2 / ADR-013 D2)."
    )


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        return _deny(
            "goal-evaluator (SD-1): malformed JSON on hook stdin. Fail-closed "
            "deny per ADR-013 D2 — an invalid payload cannot be reasoned "
            "about, so the write is blocked rather than passed through."
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
            "goal-evaluator (SD-1): missing or non-object `tool_input`. "
            "Fail-closed deny — well-formed Write/Edit calls always carry a "
            "`tool_input` object with `file_path`."
        )

    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or not file_path:
        return _deny(
            "goal-evaluator (SD-1): missing or non-string `file_path`. "
            "Fail-closed deny — a Write/Edit without a parseable path cannot "
            "be checked against the goal.json allowlist."
        )

    rel = _normalize_to_repo_relative(file_path)
    if rel is None:
        return _deny(
            f"goal-evaluator (SD-1): path `{file_path}` resolves outside the "
            f"vero-lite repo root. Fail-closed deny — the evaluator may only "
            f"write the repo's `.claude/state/goal.json`."
        )

    if _is_allowed_path(rel):
        return 0

    return _deny(_reason_outside_allowlist(rel))


if __name__ == "__main__":
    raise SystemExit(main())
