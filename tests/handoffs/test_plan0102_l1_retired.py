"""PLAN-0102 — L1 is retired, and the survivors still work.

**Why every absence here is paired with a live positive control.** After
PLAN-0094 AC-7, L1 stopped firing organically: the post-AC-7 measurement window
recorded 0 denies and 0 organic warns over 1,369 Write/Edit operations. So a
test that merely observes "no L1 output" passes *identically* against the guard
being present-but-quiet, against the guard being removed, and against the whole
loop-detect layer being broken. Absence alone carries no information. Each case
below therefore asserts a silence and, in the same run, a noise that must
still happen.

**The pre-change RED baseline (Step 1).** The drivers in this module were run
against the live hooks at HEAD ``c2e3278`` *before* the excision and made L1
fire, which is what makes their silence afterwards meaningful. Captured
verbatim:

    L1 deny (gate, target seeded at 20):
      "Loop-detect (L1) DENIED: same target `services/engine/probe_target.py`
       hit 20 times (deny threshold = 9, Cray E.4). You were already warned at
       6 and had 3 more edits of grace; this is the wall."

    L1 warn (observer, fired on call 7 of 7 — count 6 == the warn bar):
      "L1 warn on `...`: 6 edits of this one target (warn bar = 6). The edit was
       ALLOWED and this is advisory — but 3 more and the gate denies."

    L4 control at the same HEAD (no grace clause, correctly):
      "Loop-detect (L4) DENIED: same target `pytest <arg> -x` hit 6 times
       (deny threshold = 6, Cray E.4)."

After the excision the same drivers produce: L1 deny NO, L1 warn NO, L4 control
YES, hygiene control YES.

**Where the other criteria live.** AC-1 (the deny is extinct) and AC-5 (legacy
state cannot crash or resurrect the guard) are asserted in
``test_pretooluse_loop_detect.py``, beside the gate they constrain; AC-11's two
collateral-damage prongs sit beside the behaviour each protects —
(a) in ``test_stop_continuation.py``, (b) in
``test_posttooluse_progress_observer.py``. AC-4 (the settings excision, pinned
both directions) is ``test_settings_hook_wiring.py``.
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
GATE = HOOKS_DIR / "pretooluse_loop_detect.py"
OBSERVER = HOOKS_DIR / "posttooluse_progress_observer.py"
sys.path.insert(0, str(HOOKS_DIR))

from _loop_counter import LoopType, get_count, load_counter  # noqa: E402

Payload = dict[str, Any]

STUB_TELEGRAM = """#!/usr/bin/env bash
set -eu
printf '%s' "$1" > "$TELEGRAM_STUB_CAPTURE"
"""

# Above every bar L1 ever used: 6 / 15 warn, 9 / 18 deny.
ABOVE_EVERY_HISTORICAL_L1_BAR = 20


@pytest.fixture
def stub_env(tmp_path: Path) -> dict[str, str]:
    stub = tmp_path / "telegram_stub.sh"
    stub.write_text(STUB_TELEGRAM, encoding="utf-8")
    stub.chmod(0o755)
    env = os.environ.copy()
    env["CLAUDE_LOOP_COUNTER_PATH"] = str(tmp_path / "loop-counter.json")
    env["CLAUDE_TELEGRAM_SCRIPT"] = str(stub)
    env["TELEGRAM_STUB_CAPTURE"] = str(tmp_path / "telegram_capture.txt")
    env.pop("TELEGRAM_BOT_TOKEN", None)
    env.pop("TELEGRAM_CHAT_ID", None)
    return env


def _run(hook: Path, payload: Payload, env: dict[str, str]) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=30,
    )
    return result.returncode, result.stdout.strip()


def _state(env: dict[str, str]) -> Path:
    return Path(env["CLAUDE_LOOP_COUNTER_PATH"])


def _edit_payload(path: Path) -> Payload:
    """An Edit that re-applies the SAME ``old_string`` — L1's (b) repeat signal."""
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": str(path), "old_string": "x = 1", "new_string": "x = 2"},
        "tool_response": {"success": True},
    }


def _failing_bash(command: str) -> Payload:
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "tool_response": {"exit_code": 1, "stdout": "", "stderr": "boom"},
    }


# --- AC-2: the warn is extinct ----------------------------------------------


def test_ac2_repeated_same_edit_past_every_bar_emits_nothing(
    stub_env: dict[str, str], tmp_path: Path
) -> None:
    """Re-applying one ``old_string`` 12 times emits no output at all.

    12 is double the warn bar that fired at HEAD. At that bar the observer used
    to emit a ``decision: block`` advisory AND attempt a Telegram ping; both are
    asserted absent — the ping via the stub's capture file, which is the only
    way to catch a fire-and-forget subprocess.

    RED when: any Write/Edit handling path is reintroduced in the observer's
    ``main()`` dispatch.
    """
    target = tmp_path / "probe_target.py"
    target.write_text("x = 1\n", encoding="utf-8")

    emissions = []
    for _ in range(12):
        rc, out = _run(OBSERVER, _edit_payload(target), stub_env)
        assert rc == 0
        if out:
            emissions.append(out)

    assert emissions == [], f"the observer still emits on Write/Edit: {emissions}"
    capture = Path(stub_env["TELEGRAM_STUB_CAPTURE"])
    assert not capture.exists(), f"a Telegram ping fired for an edit: {capture.read_text()}"


def test_ac2_positive_control_hygiene_advisory_still_emits(stub_env: dict[str, str]) -> None:
    """The same stdout channel, in the same harness, must still carry a warning.

    Without this, ``test_ac2_...emits_nothing`` above passes just as well over
    an observer that has stopped emitting anything for any reason.
    """
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "wsl bash -lc 'ls /nope | head -5'"},
        "tool_response": {"stdout": "", "stderr": "no such file", "interrupted": False},
    }
    rc, out = _run(OBSERVER, payload, stub_env)
    assert rc == 0
    assert "Shell-hygiene advisory" in out, "the observer's advisory channel went silent"


# --- AC-3: the counter no longer tracks FILE_EDIT ---------------------------


def test_ac3_no_l1_key_and_no_turn_bookkeeping_after_edits(
    stub_env: dict[str, str], tmp_path: Path
) -> None:
    """After N Write/Edit calls the state file gains no ``L1:`` key.

    The positive control is in the SAME run and the same file: one failing Bash
    call must create an ``L4:`` key. That is what proves the writer wrote — the
    absence of an ``L1:`` key is otherwise indistinguishable from the observer
    never having persisted anything.

    Also asserts the three retired top-level fields do not reappear.
    """
    target = tmp_path / "probe_target.py"
    target.write_text("x = 1\n", encoding="utf-8")
    for _ in range(8):
        _run(OBSERVER, _edit_payload(target), stub_env)

    # The control, same state file.
    _run(OBSERVER, _failing_bash("pytest tests/foo.py"), stub_env)

    raw = json.loads(_state(stub_env).read_text(encoding="utf-8"))
    counters = raw.get("counters", {})
    l1_keys = [k for k in counters if k.startswith("L1:")]
    l4_keys = [k for k in counters if k.startswith("L4:")]

    assert l4_keys, "the control did not write — this run proves nothing about L1"
    assert l1_keys == [], f"an L1 counter key was written: {l1_keys}"
    for retired in ("turn_touched", "subagent_touched", "awaiting_ack"):
        assert retired not in raw, f"{retired} came back into the state document"


# --- AC-6: ADR-013 E.4 still holds ------------------------------------------
#
# The ratified trigger is "pause + Telegram alert when an agent loops > 6 rounds
# on the same PROBLEM". L1 keyed on the same FILE, which is why retiring it
# moves the implementation toward E.4 rather than away from it. These two cases
# drive the real observer into the real gate on realistic simulated output — no
# side of the seam is stubbed (the Telegram transport stub sits BEYOND the
# asserted seam, which is the emitted payload).


def test_ac6_same_failing_test_six_times_still_fires_the_e4_payload(
    stub_env: dict[str, str],
) -> None:
    """L2: the same pytest nodeid failing six times pings Cray.

    RED when: the excision collaterally damages ``_apply_l2``, the shared
    threshold, or the Telegram path.
    """
    nodeid = "tests/services/test_thing.py::test_the_same_problem"
    pytest_output = (
        "=================================== FAILURES ===================================\n"
        f"FAILED {nodeid} - AssertionError: still wrong\n"
        "=========================== short test summary info ============================\n"
    )
    for _ in range(6):
        payload = {
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "python -m pytest tests/services/test_thing.py -q"},
            "tool_response": {"exit_code": 1, "stdout": pytest_output, "stderr": ""},
        }
        rc, _ = _run(OBSERVER, payload, stub_env)
        assert rc == 0

    capture = Path(stub_env["TELEGRAM_STUB_CAPTURE"])
    assert capture.exists(), "L2 never pinged — E.4's alert half is severed"
    body = capture.read_text(encoding="utf-8")
    assert "L2" in body
    assert nodeid in body
    assert "last 6 actions" in body, "the E.4 payload contract lost its action ring"


def test_ac6_same_failing_command_six_times_denies_the_seventh(
    stub_env: dict[str, str],
) -> None:
    """L4: the observer counts six failures, then the gate walls the seventh.

    This is the pause half of E.4, and it is the end-to-end path — one hook
    writes the counter, the other reads it and denies.

    RED when: the excision damages ``_apply_l4``, the L4 branch of
    ``_resolve_target``, or the gate's threshold.
    """
    command = "uv run alembic upgrade head"
    for _ in range(6):
        rc, _ = _run(OBSERVER, _failing_bash(command), stub_env)
        assert rc == 0

    counter = load_counter(_state(stub_env))
    assert get_count(counter, LoopType.BASH_PATTERN, "uv run alembic upgrade head") == 6

    rc, out = _run(
        GATE,
        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command}},
        stub_env,
    )
    assert rc == 0
    decision = json.loads(out)
    assert decision["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "L4" in decision["hookSpecificOutput"]["permissionDecisionReason"]


def test_ac6_control_a_different_problem_is_not_walled(stub_env: dict[str, str]) -> None:
    """The guard must still key on SAMENESS, not merely on count.

    Six failures spread across six DIFFERENT command patterns must not deny —
    otherwise the two cases above would pass over a gate that had degenerated
    into "deny after six of anything", which is not what E.4 ratified.

    ⚠️ The commands must differ AFTER tokenization, which is a stricter
    requirement than differing as strings. A first draft used ``cmd0 --flag`` ..
    ``cmd5 --flag`` and this test caught it: ``tokenize_bash_command`` replaces
    a bare integer with ``<arg>`` — deliberately, so ``pytest tests/foo.py`` and
    ``pytest tests/bar.py`` share one counter — so all six collapsed to
    ``cmd<arg> --flag`` and the gate correctly denied. The six below share no
    tokenized form.
    """
    distinct = ["git status", "npm test", "ruff format", "make clean", "docker ps", "mypy strict"]
    for command in distinct:
        _run(OBSERVER, _failing_bash(command), stub_env)

    counter = load_counter(_state(stub_env))
    keys = {k for k in json.loads(_state(stub_env).read_text(encoding="utf-8"))["counters"]}
    assert len(keys) == len(distinct), (
        f"the six commands did not stay distinct after tokenization ({keys}) — "
        "this control cannot say anything until they do"
    )
    assert get_count(counter, LoopType.BASH_PATTERN, "git status") == 1

    rc, out = _run(
        GATE,
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "git status"},
        },
        stub_env,
    )
    assert rc == 0
    assert out == "", f"a single failure of one pattern was denied: {out}"
