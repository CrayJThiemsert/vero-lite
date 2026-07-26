"""The observer's shell-hygiene advisory — catch a masked failure before it is believed.

Guards three command shapes that make a FAILED command report SUCCESS, all three
measured in this harness on 2026-07-26 and recorded in
``docs/lessons/0007-harness-exit-code-artifact.md``:

1. ``cmd | tail -N`` — the pipeline's status is the truncator's, so a failing
   ``cmd`` reports 0, and the truncation cuts the traceback that would have shown
   it. This is the shape that actually bit session 175: a Python script aborted on
   an assertion, the traceback was cut, the exit code was swallowed, and the run
   was reported as successful.
2. ``cmd | head`` **under** ``pipefail`` — the opposite error. ``head`` closes the
   pipe early, so the producer dies of SIGPIPE and the pipeline reports 141: a
   SUCCESSFUL command turned into a spurious failure.
3. An unescaped ``$?`` / ``$(...)`` inside a ``bash -c`` string — under
   ``wsl bash -lc`` this expands one shell layer early. Measured: ``$?`` reports 0
   for a failed command; ``$(pwd)`` resolves before a preceding ``cd``.

Why the advisory is PostToolUse rather than a PreToolUse deny: the harm is not
running the command, it is *believing* its output. That is knowable only after it
has run, which is when this fires — and it costs no false-positive tax, because a
warn cannot block legitimate work.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
OBSERVER = HOOKS_DIR / "posttooluse_progress_observer.py"

sys.path.insert(0, str(HOOKS_DIR))

from posttooluse_progress_observer import _shell_hygiene_warning  # noqa: E402

# --- shapes that MUST warn -------------------------------------------------- #

MASKED_EXIT = [
    "pytest tests/ -q | tail -5",
    "python script.py | tail -20",
    "wsl bash -lc 'make build' 2>&1 | tail -n 30",
    "grep -rn foo services/ |tail -3",
    "./run.sh | head -40",
]

SIGPIPE_RISK = [
    "set -o pipefail; seq 1 100000 | head -3",
    "bash -o pipefail -c 'cmd' | head -c 200",
]

EARLY_EXPANSION = [
    "wsl bash -lc 'false; echo rc=$?'",
    "wsl bash -lc 'cd /etc; echo $(pwd)'",
    "bash -c 'echo $(date)'",
]

# --- shapes that MUST NOT warn ---------------------------------------------- #

CLEAN = [
    # The prescribed replacement: file capture, real exit code, bounded slice.
    "wsl bash -lc 'set -uo pipefail; ( pytest tests/ ) >/tmp/r.log 2>&1; "
    "rc=\\$?; echo EXIT=\\$rc; tail -30 /tmp/r.log; exit \\$rc'",
    # Truncation WITH pipefail, using tail (drains, no SIGPIPE).
    "set -o pipefail; pytest tests/ -q 2>&1 | tail -5",
    # Ordinary commands with no pipe and no bash -c wrapper.
    "git status --short",
    "wsl bash -lc 'cd /home/crayj/work/vero-lite && git log --oneline -3'",
    # head/tail as the SOLE command (no pipe) is not a masking shape.
    "tail -30 /tmp/run.log",
    "head -20 README.md",
    # Escaped expansion inside bash -c is the CORRECT form.
    "wsl bash -lc 'false; echo rc=\\$?'",
]


@pytest.mark.parametrize("command", MASKED_EXIT)
def test_pipe_to_truncator_without_pipefail_warns(command: str) -> None:
    warning = _shell_hygiene_warning(command)
    assert warning is not None, f"no advisory for a masked-exit shape: {command!r}"
    assert "pipefail" in warning


@pytest.mark.parametrize("command", SIGPIPE_RISK)
def test_head_under_pipefail_warns_about_sigpipe(command: str) -> None:
    """The inverse hazard: a SUCCESS reported as failure 141."""
    warning = _shell_hygiene_warning(command)
    assert warning is not None, f"no advisory for a SIGPIPE shape: {command!r}"
    assert "141" in warning


@pytest.mark.parametrize("command", EARLY_EXPANSION)
def test_unescaped_expansion_in_bash_c_warns(command: str) -> None:
    warning = _shell_hygiene_warning(command)
    assert warning is not None, f"no advisory for early expansion: {command!r}"
    assert "one shell layer EARLY" in warning


@pytest.mark.parametrize("command", CLEAN)
def test_clean_commands_do_not_warn(command: str) -> None:
    """Non-vacuity + false-positive guard.

    An advisory that fires on everything is noise, and noise gets ignored --
    which would leave the real signal unread. The prescribed replacement idiom
    must itself be silent, or the rule would contradict its own remedy.
    """
    assert _shell_hygiene_warning(command) is None, f"false positive on: {command!r}"


def test_advisory_names_the_remedy_not_just_the_problem() -> None:
    """A warning that does not say what to do instead gets worked around, not fixed."""
    warning = _shell_hygiene_warning("pytest -q | tail -5")
    assert warning is not None
    assert "2>&1" in warning
    assert "exit code" in warning
    assert "0007" in warning  # points at the lesson carrying the measured evidence


def test_hook_emits_the_advisory_end_to_end(tmp_path: Path) -> None:
    """Through a real subprocess invocation, in the PostToolUse advisory shape.

    The unit tests above exercise the predicate; this pins that the hook actually
    SPEAKS -- the defect class PLAN-0094 F3c was about (a handler that worked
    perfectly and was never reachable).
    """
    env: dict[str, Any] = os.environ.copy()
    env["CLAUDE_LOOP_COUNTER_PATH"] = str(tmp_path / "loop-counter.json")
    env["CLAUDE_TELEGRAM_SCRIPT"] = str(tmp_path / "absent.sh")
    env.pop("TELEGRAM_BOT_TOKEN", None)
    env.pop("TELEGRAM_CHAT_ID", None)

    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "pytest tests/ -q | tail -5"},
        "tool_response": {"stdout": "3 passed", "stderr": ""},
    }
    result = subprocess.run(
        [sys.executable, str(OBSERVER)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=15,
    )

    assert result.returncode == 0, "the observer must never fail the tool call"
    parsed = json.loads(result.stdout.strip())
    assert parsed["decision"] == "block"
    assert "pipefail" in parsed["reason"]


def test_clean_command_stays_silent_end_to_end(tmp_path: Path) -> None:
    """The same path with a clean command emits nothing at all."""
    env: dict[str, Any] = os.environ.copy()
    env["CLAUDE_LOOP_COUNTER_PATH"] = str(tmp_path / "loop-counter.json")
    env["CLAUDE_TELEGRAM_SCRIPT"] = str(tmp_path / "absent.sh")

    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "git status --short"},
        "tool_response": {"stdout": "", "stderr": ""},
    }
    result = subprocess.run(
        [sys.executable, str(OBSERVER)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=15,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "", f"unexpected output: {result.stdout!r}"
