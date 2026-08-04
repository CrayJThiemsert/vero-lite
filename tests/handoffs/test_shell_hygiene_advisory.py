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
4. Any ``$`` inside a **double-quoted** ``bash -c`` argument, escaped or not (added
   2026-08-04, session 204). Lesson 0007 §1.1 already recorded that the outer quote
   style is load-bearing — the outer layer eats one level of backslash, so
   ``"... \\$? ..."`` reaches the inner bash bare — but shape 3's predicate requires
   the ``$`` to carry NO backslash, so the dutifully-escaped-under-double-quotes form
   sailed past silently. That is the half of the remedy nobody enforced, and a whole
   session ran on it: escaping added, quotes left double, fabricated zeros read over
   two RED tests, and the conclusion drawn that the *rule* was broken. Lesson #0024 —
   a rule has to live where the enforcer looks, and half a remedy is the half that
   gets followed.

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

# A DOUBLE-quoted outer argument, where the backslash escape is eaten before WSL
# re-assembles the argv — so `\$?` behaves exactly like a bare `$?`. Escaping is
# necessary but NOT sufficient; the quote style is the other half of the remedy.
# Measured 2026-08-04 (session 204): with a double-quoted outer, `\$?` after a
# failing command printed 0 and `\$V` after `V=hello` printed empty; the identical
# text under a SINGLE-quoted outer printed 1 and `hello`.
DOUBLE_QUOTED_OUTER = [
    'wsl bash -lc "false; echo rc=\\$?"',
    'wsl bash -lc "V=hello; echo v=\\$V"',
    'wsl bash -lc "pytest -q > /tmp/r.log 2>&1; echo EXIT=\\$?"',
    # Bare `$` under a double-quoted outer is broken for the same reason; this one
    # is caught by BOTH predicates, which is fine — the advisory lists all problems.
    'wsl bash -lc "cd /etc && echo $(pwd)"',
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
    # Escaped expansion inside bash -c is the CORRECT form — but ONLY because the
    # outer argument is SINGLE-quoted. The same text with double quotes is broken
    # and must warn (see DOUBLE_QUOTED_OUTER).
    "wsl bash -lc 'false; echo rc=\\$?'",
    # A double-quoted outer with NO `$` at all is perfectly fine — the hazard is the
    # expansion, not the quote style on its own. Without this case the new predicate
    # would be free to fire on most ordinary commands and become noise.
    'wsl bash -lc "cd /home/crayj/work/vero-lite && git log --oneline -3"',
    'wsl bash -lc "grep -rn needle services/ > /tmp/out.txt 2>&1"',
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


@pytest.mark.parametrize("command", DOUBLE_QUOTED_OUTER)
def test_double_quoted_outer_with_a_dollar_warns(command: str) -> None:
    """Escaping alone is NOT the remedy — the outer quote style is the other half.

    This is the shape the advisory was blind to: ``_UNESCAPED_EXPANSION_RE`` requires
    the ``$`` to carry no backslash, so a dutifully-escaped ``"... \\$? ..."`` under
    double quotes slipped through silently while behaving exactly like the unescaped
    form. A session read fabricated zeros over two RED tests on this shape and then
    concluded the *rule* was broken rather than its own usage of it.
    """
    warning = _shell_hygiene_warning(command)
    assert warning is not None, f"no advisory for a double-quoted outer: {command!r}"
    assert "SINGLE-quoted" in warning


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
