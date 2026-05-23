"""Tests for .claude/hooks/notification_telegram.py (PLAN-0007 AC-1)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / ".claude" / "hooks" / "notification_telegram.py"

Payload = dict[str, Any]


def _run(
    payload: Payload, env_override: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
        env.pop(k, None)
    if env_override:
        env.update(env_override)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_env_unset_graceful_no_op() -> None:
    # AC-1 third bullet: with TELEGRAM_* env unset, the bridge must exit 0
    # and produce no stdout (so the hook doesn't accidentally block).
    result = _run(
        {
            "session_id": "abc12345",
            "notification_type": "permission_prompt",
            "message": "approve git status?",
            "cwd": "/home/crayj/work/vero-lite",
        }
    )
    assert result.returncode == 0
    assert result.stdout == ""


def test_permission_prompt_payload_constructs() -> None:
    result = _run(
        {
            "session_id": "abc12345",
            "notification_type": "permission_prompt",
            "message": "approve git status?",
            "cwd": "/home/crayj/work/vero-lite",
        }
    )
    # Without env vars, telegram.sh logs to stderr and exits 0; hook stays silent.
    assert result.returncode == 0


def test_idle_prompt_payload_constructs() -> None:
    result = _run(
        {
            "session_id": "abc12345",
            "notification_type": "idle_prompt",
            "message": "still waiting on a decision",
            "cwd": "/home/crayj/work/vero-lite",
        }
    )
    assert result.returncode == 0


def test_malformed_stdin_does_not_crash() -> None:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0


def test_missing_fields_does_not_crash() -> None:
    result = _run({})
    assert result.returncode == 0
