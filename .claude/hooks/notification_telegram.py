#!/usr/bin/env python3
"""Notification hook — forward permission_prompt / idle_prompt events to Telegram.

ADR-013 D5 / PLAN-0007 Step 3 / AC-1.

The settings.json matcher narrows to ``permission_prompt|idle_prompt`` so this
script never fires on routine tool use (per AC-1 "no spurious pings"). The
script extracts ``{session_id, notification_type, message}`` from the hook
payload and forwards a formatted line to ``tools/notify/telegram.sh``.

Cross-platform bridge: ``telegram.sh`` is a POSIX shell script (PLAN-0007
Step 2 requires shell). Cross-platform invocation + WSLENV passthrough is
delegated to :mod:`_wsl_bridge` (Pattern A — rule-of-three extraction).

Failure mode: never block the Claude Code event loop — the Notification event
type cannot block (Claude Code hooks reference, "Exit code 2 behavior per
event"), and the telegram bridge is best-effort (env-unset → no-op,
network/API errors → logged, never raised).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from _wsl_bridge import bash_argv, env_with_wslenv_passthrough

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TELEGRAM_SH_POSIX = "tools/notify/telegram.sh"

_FORWARDED_ENV = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")


def _build_message(payload: dict[str, object]) -> str:
    session = str(payload.get("session_id") or "<unknown>")
    ntype = str(payload.get("notification_type") or "<unknown>")
    msg = str(payload.get("message") or "").strip() or "(no message body)"
    cwd = str(payload.get("cwd") or "")
    return f"[vero-lite/{ntype}] session={session[:8]} cwd={cwd}\n{msg}"


def _invoke_telegram(message: str) -> None:
    cmd = bash_argv(REPO_ROOT / TELEGRAM_SH_POSIX, message)
    env = env_with_wslenv_passthrough(_FORWARDED_ENV)
    try:
        # S603: argv built from REPO_ROOT-derived constants + Telegram message
        # text; no shell interpolation, no user-controlled args (the message is
        # forwarded as a single argv element to bash, never as a shell command).
        subprocess.run(  # noqa: S603
            cmd,
            env=env,
            timeout=15,
            check=False,
            capture_output=True,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        # Best-effort only; never raise into the Claude Code event loop.
        print(f"notification_telegram: bridge invocation failed: {exc}", file=sys.stderr)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    _invoke_telegram(_build_message(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
