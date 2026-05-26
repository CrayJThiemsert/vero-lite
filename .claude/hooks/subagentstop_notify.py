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

Implementation pattern mirrors ``notification_telegram.py``:

* Cross-platform: on Windows, re-shell via ``wsl.exe`` and propagate
  ``TELEGRAM_BOT_TOKEN`` + ``TELEGRAM_CHAT_ID`` through ``WSLENV``
* Best-effort: missing env vars, missing script, network errors all
  yield graceful no-ops (the hook never blocks the event loop)
* Defensive parsing: malformed JSON stdin returns 0 silently
* Filter at the hook layer too: even if the settings.json matcher is
  loose, this hook checks ``agent_type`` and only fires for the
  allowlisted types (currently: ``plan-drafter``)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

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


def _wsl_path(win_path: Path) -> str:
    """Translate Windows ``\\\\wsl.localhost\\<distro>\\...`` to a WSL path."""
    s = str(win_path)
    if not s.lower().startswith("\\\\wsl"):
        return s.replace("\\", "/")
    parts = s.split("\\")
    try:
        idx = next(i for i, p in enumerate(parts) if p.startswith("ubuntu") or p.lower() == "wsl$")
    except StopIteration:
        return s.replace("\\", "/")
    return "/" + "/".join(parts[idx + 1 :])


def _forwarded_env() -> dict[str, str]:
    env = os.environ.copy()
    if sys.platform == "win32":
        wslenv = env.get("WSLENV", "")
        existing = {item.split("/", 1)[0] for item in wslenv.split(":") if item}
        additions = [f"{k}/u" for k in _FORWARDED_ENV if k not in existing]
        if additions:
            env["WSLENV"] = ":".join(filter(None, [wslenv, *additions]))
    return env


def _invoke_telegram(message: str) -> None:
    if sys.platform == "win32" and shutil.which("wsl.exe"):
        script = _wsl_path(REPO_ROOT) + "/" + TELEGRAM_SH_POSIX
        cmd = ["wsl.exe", "--exec", "bash", script, message]
    else:
        script = str(REPO_ROOT / TELEGRAM_SH_POSIX)
        cmd = ["bash", script, message]

    try:
        # S603: cmd elements come from REPO_ROOT-derived constants + the
        # formatted alert message; no shell interpolation. Same idiom as
        # notification_telegram.py.
        subprocess.run(  # noqa: S603
            cmd,
            env=_forwarded_env(),
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
