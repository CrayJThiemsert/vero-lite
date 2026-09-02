#!/usr/bin/env python3
"""PreToolUse hook — settings-level dispatcher for the three subagent write guards.

Registered in ``.claude/settings.json`` under ``PreToolUse`` / ``Write|Edit``,
beside ``pretooluse_research_path_deny.py`` and
``pretooluse_governance_gate_deny.py``.

Why a dispatcher exists (measured, session 272 — Lesson #0057 "Resolution,
part 2"): the three guard scripts were wired ONLY in their agents' frontmatter
``hooks:`` block, and in this harness that block never runs. An instrumented
``pretooluse_goal_evaluator_write_deny.py`` recorded **zero** invocations while
``goal-evaluator``'s allowed ``goal.json`` write succeeded — in a NEW
conversation that had loaded the nested-shape (valid) agent files fresh.
Settings-level hooks, by contrast, fire for subagent tool calls, and their stdin
payload carries the caller's identity: ``agent_id`` (the harness's real agent
id, equal to the Agent tool's returned id) and ``agent_type`` (the
``subagent_type`` name) — verified the same session through
``pretooluse_git_deny.py``'s own deny text. So the identity that frontmatter
wiring merely implied is now read from the payload, and each allowlist stays
exactly where it was.

Contract:

* ``agent_type`` names one of the three guarded agents → the raw stdin payload
  is handed byte-for-byte to that agent's guard script in a subprocess, and the
  guard's stdout (empty = allow, or its deny JSON) is forwarded verbatim. The
  guard scripts are UNCHANGED and stay frontmatter-wired as well — harmless,
  and double coverage if a future client starts applying frontmatter hooks.
* Fail-closed wherever identity IS known: a guard script that is missing,
  cannot be launched, times out, or exits non-zero → deny (ADR-013 D2).
* Pass-through wherever the caller is NOT one of the three: the main Code
  agent (no ``agent_type``), every other subagent, non-Write/Edit tools.
  Malformed stdin also passes through — the harness, not the agent, serialises
  this payload, so no agent reaches a bypass through it, and a fail-closed
  reading here would deny every Write/Edit of every actor on a harness glitch.

Bypass-immunity: hook decisions run regardless of ``permissionMode``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

HOOKS_DIR = Path(__file__).resolve().parent
WATCHED_TOOLS = ("Write", "Edit")
GUARD_TIMEOUT_S = 30

# agent_type (the subagent_type name, as the harness sends it) -> guard script,
# a sibling of this file. Keys are the agents' frontmatter ``name`` values.
GUARDS: dict[str, str] = {
    "goal-evaluator": "pretooluse_goal_evaluator_write_deny.py",
    "plan-drafter": "pretooluse_plan_subagent_write_deny.py",
    "status-scribe": "pretooluse_status_scribe_write_deny.py",
}


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


def guard_for(payload: dict[str, Any]) -> str | None:
    """Name of the guard script for this payload's ``agent_type``, or ``None``."""
    agent_type = payload.get("agent_type")
    if not isinstance(agent_type, str):
        return None
    return GUARDS.get(agent_type.strip())


def _fail_closed(agent_type: str, detail: str) -> int:
    return _deny(
        f"subagent write guard ({agent_type}): the guard script could not decide — "
        f"{detail}. Fail-closed deny per ADR-013 D2: a `{agent_type}` Write/Edit is "
        f"blocked rather than passed through unguarded. The guards are dispatched "
        f"from .claude/settings.json (PreToolUse Write|Edit) because agent-"
        f"frontmatter hooks do not run in this harness (Lesson #0057, Resolution "
        f"part 2)."
    )


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload: Any = json.loads(raw)
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict):
        return 0
    if payload.get("tool_name") not in WATCHED_TOOLS:
        return 0

    guard = guard_for(payload)
    if guard is None:
        return 0
    agent_type = str(payload.get("agent_type")).strip()

    script = HOOKS_DIR / guard
    if not script.is_file():
        return _fail_closed(agent_type, f"guard script `{guard}` is missing from `{HOOKS_DIR}`")

    try:
        result = subprocess.run(  # noqa: S603 — fixed argv: this interpreter + a sibling script, no shell
            [sys.executable, str(script)],
            input=raw,
            capture_output=True,
            text=True,
            timeout=GUARD_TIMEOUT_S,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return _fail_closed(
            agent_type, f"guard script `{guard}` timed out after {GUARD_TIMEOUT_S}s"
        )
    except OSError as exc:
        return _fail_closed(agent_type, f"guard script `{guard}` could not be launched: {exc}")

    if result.stderr:
        sys.stderr.write(result.stderr)
    if result.returncode != 0:
        return _fail_closed(agent_type, f"guard script `{guard}` exited {result.returncode}")

    # The guard's verdict, verbatim: nothing (allow) or its own deny JSON.
    sys.stdout.write(result.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
