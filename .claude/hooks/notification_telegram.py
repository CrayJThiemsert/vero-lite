#!/usr/bin/env python3
"""Notification hook — forward permission_prompt / idle_prompt events to Telegram.

ADR-013 D5 / PLAN-0007 Step 3 / AC-1.

The settings.json matcher narrows to ``permission_prompt|idle_prompt`` so this
script never fires on routine tool use (per AC-1 "no spurious pings"). The
script extracts ``{session_id, notification_type, message}`` from the hook
payload and forwards a formatted line to ``tools/notify/telegram.sh``.

Cross-platform bridge: ``telegram.sh`` is a POSIX shell script (PLAN-0007
Step 2 requires shell). On Windows, Claude Code runs the hook command in
Windows Python, so we re-shell via ``wsl.exe`` and propagate
``TELEGRAM_BOT_TOKEN`` + ``TELEGRAM_CHAT_ID`` through ``WSLENV``. On Linux,
``bash`` is invoked directly.

Failure mode: never block the Claude Code event loop — the Notification event
type cannot block (Claude Code hooks reference, "Exit code 2 behavior per
event"), and the telegram bridge is best-effort (env-unset → no-op,
network/API errors → logged, never raised).
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

_FORWARDED_ENV = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")


def _build_message(payload: dict[str, object]) -> str:
    session = str(payload.get("session_id") or "<unknown>")
    ntype = str(payload.get("notification_type") or "<unknown>")
    msg = str(payload.get("message") or "").strip() or "(no message body)"
    cwd = str(payload.get("cwd") or "")
    return f"[vero-lite/{ntype}] session={session[:8]} cwd={cwd}\n{msg}"


def _wsl_path(win_path: Path) -> str:
    """Translate a Windows path under \\\\wsl.localhost\\<distro>\\... to a WSL path."""
    s = str(win_path)
    if not s.lower().startswith("\\\\wsl"):
        return s.replace("\\", "/")
    parts = s.split("\\")
    # \\wsl.localhost\ubuntu-24.04\home\crayj\... -> /home/crayj/...
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
        # S603: cmd elements come from REPO_ROOT-derived constants + Telegram message text;
        # no shell interpolation, no user-controlled args (the message is forwarded as a
        # single argv element to bash, never as a shell command). Safe by construction.
        subprocess.run(  # noqa: S603
            cmd,
            env=_forwarded_env(),
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
