#!/usr/bin/env python3
"""SubagentStop hook — fire Telegram alert when `plan-drafter` completes.

PLAN-0009 Step 1b §5 SubagentStop notification wiring. The matcher in
``.claude/settings.json`` narrows to ``SubagentStop`` events on the
``plan-drafter`` agent type so this hook never fires for the read-only
``explore-research`` subagent (research sweeps are not Cray-actionable on
completion per the §5 design note).

Why notify on plan-drafter:

* The plan-drafter subagent produces a PR-ready uncommitted draft under
  ``docs/{adr,plans}/NNNN-*.md`` and returns the path in its final
  message. The main Code agent then commits via PR per CLAUDE.md §7.
* Cray reviews + ratifies governance drafts at PR merge time. A
  Telegram ping on completion lets Cray know a draft is ready without
  polling the chat.
* Mirrors the AFK-channel discipline established by Phase 1
  ``notification_telegram.py`` (idle_prompt / permission_prompt) and
  Phase 2 ``pretooluse_loop_detect.py`` (loop-detect deny).

Cross-platform invocation + WSLENV passthrough is delegated to
:mod:`_wsl_bridge` (Pattern A — rule-of-three extraction shared with
``notification_telegram.py`` and the classifier's HTTPS bridge).

Defensive parsing: malformed JSON stdin returns 0 silently. Filter at the
hook layer too: even if the settings.json matcher is loose, this hook
checks ``agent_type`` and only fires for the allowlisted types (currently:
``plan-drafter``).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from _wsl_bridge import bash_argv, env_with_wslenv_passthrough

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TELEGRAM_SH_POSIX = "tools/notify/telegram.sh"

# Subagent types that warrant a Telegram ping on completion. Add new
# types here as additional governance-drafting subagents land.
# explore-research is intentionally NOT in this allowlist — research
# sweeps are not Cray-actionable on completion (Step 1b §5 design note).
NOTIFY_AGENT_TYPES: frozenset[str] = frozenset({"plan-drafter"})

_FORWARDED_ENV = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")


def _should_notify(agent_type: object) -> bool:
    if not isinstance(agent_type, str):
        return False
    return agent_type in NOTIFY_AGENT_TYPES


def _build_message(payload: dict[str, object]) -> str:
    session = str(payload.get("session_id") or "<unknown>")
    agent_type = str(payload.get("agent_type") or "<unknown>")
    agent_id = str(payload.get("agent_id") or "<unknown>")
    cwd = str(payload.get("cwd") or "")
    # The primitive does not guarantee a final-message field in the hook
    # input; the subagent's final message is the Agent tool result (returned
    # to the parent), not necessarily replicated into the SubagentStop hook.
    # Keep the alert tight: caller, agent identity, and the cwd so Cray can
    # `git status` to find the new draft path.
    return (
        f"[vero-lite/subagent-stop] {agent_type} (agent_id={agent_id[:8]}) "
        f"completed. session={session[:8]} cwd={cwd}\n"
        f"Check `docs/adr/` or `docs/plans/` for the new draft; the main "
        f"Code agent will surface the path + PR-flow per CLAUDE.md §7."
    )


def _invoke_telegram(message: str) -> None:
    cmd = bash_argv(REPO_ROOT / TELEGRAM_SH_POSIX, message)
    env = env_with_wslenv_passthrough(_FORWARDED_ENV)
    try:
        # S603: argv built from REPO_ROOT-derived constants + formatted alert
        # message; no shell interpolation. Same idiom as notification_telegram.
        subprocess.run(  # noqa: S603
            cmd,
            env=env,
            timeout=15,
            check=False,
            capture_output=True,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        # Best-effort only; never raise into the Claude Code event loop.
        print(f"subagentstop_notify: bridge invocation failed: {exc}", file=sys.stderr)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict):
        return 0
    if not _should_notify(payload.get("agent_type")):
        return 0
    _invoke_telegram(_build_message(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
