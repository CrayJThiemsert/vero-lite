"""Tests for ``.claude/hooks/posttooluse_progress_observer.py`` (PLAN-0008 Step 3).

Covers:

- L1 (Write/Edit): increment per call, no Telegram fire here (gate at Step 2)
- L4 (Bash): increment on failure (interrupted / explicit exit code / is_error
  / stderr-only with error marker), reset on success, no-op on ambiguous
- L2 (pytest): parse FAILED/PASSED nodeids, increment/reset per nodeid,
  fire Telegram inline on trigger (count >= 6)
- L3 (traceback): hash signature, increment, fire Telegram inline on trigger
- State persistence via the Step 1 module (atomic write)
- Malformed inputs fail-open (never block, never raise)
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
HOOK = REPO_ROOT / ".claude" / "hooks" / "posttooluse_progress_observer.py"
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from _loop_counter import (  # noqa: E402  — sys.path manipulation above
    ActionRecord,
    LoopType,
    get_count,
    increment,
    load_counter,
    new_counter,
    save_counter,
)

Payload = dict[str, Any]

STUB_TELEGRAM = """#!/usr/bin/env bash
# Stub that writes $1 (argv message) to $TELEGRAM_STUB_CAPTURE.
# Matches real telegram.sh contract — message via argv, never stdin
# (see Lesson #14 / session-15 Path C step 3 fix).
set -eu
printf '%s' "$1" > "$TELEGRAM_STUB_CAPTURE"
"""


@pytest.fixture
def stub_env(tmp_path: Path) -> dict[str, str]:
    state_path = tmp_path / "loop-counter.json"
    stub_script = tmp_path / "telegram_stub.sh"
    capture_file = tmp_path / "telegram_capture.json"
    stub_script.write_text(STUB_TELEGRAM, encoding="utf-8")
    stub_script.chmod(0o755)
    env = os.environ.copy()
    env["CLAUDE_LOOP_COUNTER_PATH"] = str(state_path)
    env["CLAUDE_TELEGRAM_SCRIPT"] = str(stub_script)
    env["TELEGRAM_STUB_CAPTURE"] = str(capture_file)
    env.pop("TELEGRAM_BOT_TOKEN", None)
    env.pop("TELEGRAM_CHAT_ID", None)
    return env


def _run(payload: Payload, env: dict[str, str]) -> int:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=15,
    )
    return result.returncode


def _state(env: dict[str, str]) -> Path:
    return Path(env["CLAUDE_LOOP_COUNTER_PATH"])


def _capture(env: dict[str, str]) -> Path:
    return Path(env["TELEGRAM_STUB_CAPTURE"])


def _write(file_path: str) -> Payload:
    return {
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": "x"},
        "tool_response": {},
    }


def _edit(file_path: str) -> Payload:
    return {
        "tool_name": "Edit",
        "tool_input": {"file_path": file_path, "old_string": "a", "new_string": "b"},
        "tool_response": {},
    }


def _bash(command: str, **resp: Any) -> Payload:
    return {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "tool_response": resp,
    }


# --- L1: Write/Edit increment ---


def test_l1_write_increments_counter(stub_env: dict[str, str]) -> None:
    assert _run(_write("docs/STATUS.md"), stub_env) == 0
    c = load_counter(_state(stub_env))
    assert get_count(c, LoopType.FILE_EDIT, "docs/STATUS.md") == 1


def test_l1_edit_increments_same_counter_as_write(stub_env: dict[str, str]) -> None:
    _run(_write("docs/STATUS.md"), stub_env)
    _run(_edit("docs/STATUS.md"), stub_env)
    c = load_counter(_state(stub_env))
    assert get_count(c, LoopType.FILE_EDIT, "docs/STATUS.md") == 2


def test_l1_path_normalization_windows_unc(stub_env: dict[str, str]) -> None:
    unc = "\\\\wsl.localhost\\Ubuntu-24.04\\home\\crayj\\work\\vero-lite\\docs\\STATUS.md"
    _run(_write(unc), stub_env)
    _run(_write("docs/STATUS.md"), stub_env)
    c = load_counter(_state(stub_env))
    # Both paths collapse to the same normalized target
    assert get_count(c, LoopType.FILE_EDIT, "docs/STATUS.md") == 2


def test_l1_does_not_fire_telegram_inline(stub_env: dict[str, str]) -> None:
    """L1 trigger is gated by Step 2 on the NEXT attempt — Step 3 must NOT
    fire Telegram for L1, even at count >= 6.
    """
    # Pre-seed L1 to 5, run one more Write → count becomes 6 but no Telegram
    seed = new_counter("s")
    for _ in range(5):
        increment(seed, LoopType.FILE_EDIT, "docs/STATUS.md", ActionRecord("t", "Edit", "x"))
    save_counter(seed, _state(stub_env))
    _run(_write("docs/STATUS.md"), stub_env)
    assert not _capture(stub_env).exists(), "L1 must not fire Telegram inline (Step 2's job)"
    c = load_counter(_state(stub_env))
    assert get_count(c, LoopType.FILE_EDIT, "docs/STATUS.md") == 6


def test_l1_ignores_missing_file_path(stub_env: dict[str, str]) -> None:
    _run({"tool_name": "Write", "tool_input": {}, "tool_response": {}}, stub_env)
    c = load_counter(_state(stub_env))
    assert c.counters == {}


def test_l1_records_turn_touched(stub_env: dict[str, str]) -> None:
    """Step 4 dependency: every Write/Edit records the normalized target
    in turn_touched so Stop hook can reset untouched L1 counters.
    """
    _run(_write("docs/STATUS.md"), stub_env)
    _run(_edit("docs/STATUS.md"), stub_env)  # dedup
    _run(_write("x.py"), stub_env)
    c = load_counter(_state(stub_env))
    assert c.turn_touched == ["docs/STATUS.md", "x.py"]


# --- L4: Bash command pattern ---


def test_l4_increment_on_interrupted(stub_env: dict[str, str]) -> None:
    _run(_bash("pytest tests/foo.py", interrupted=True, stdout="", stderr=""), stub_env)
    c = load_counter(_state(stub_env))
    assert get_count(c, LoopType.BASH_PATTERN, "pytest <arg>") == 1


def test_l4_increment_on_explicit_exit_code_nonzero(stub_env: dict[str, str]) -> None:
    _run(_bash("pytest tests/foo.py", exit_code=1, stdout="", stderr="boom"), stub_env)
    c = load_counter(_state(stub_env))
    assert get_count(c, LoopType.BASH_PATTERN, "pytest <arg>") == 1


def test_l4_reset_on_explicit_exit_code_zero(stub_env: dict[str, str]) -> None:
    # Seed L4 to 3 first
    seed = new_counter("s")
    for _ in range(3):
        increment(seed, LoopType.BASH_PATTERN, "pytest <arg>", ActionRecord("t", "Bash", "x"))
    save_counter(seed, _state(stub_env))
    _run(_bash("pytest tests/foo.py", exit_code=0, stdout="3 passed", stderr=""), stub_env)
    c = load_counter(_state(stub_env))
    assert get_count(c, LoopType.BASH_PATTERN, "pytest <arg>") == 0


def test_l4_increment_on_is_error_field(stub_env: dict[str, str]) -> None:
    _run(_bash("git status", is_error=True, stdout="", stderr="fatal: not a git repo"), stub_env)
    c = load_counter(_state(stub_env))
    assert get_count(c, LoopType.BASH_PATTERN, "git status") == 1


def test_l4_increment_on_stderr_only_with_error_marker(stub_env: dict[str, str]) -> None:
    # Use a path with / so the tokenizer collapses the arg to <arg>
    _run(_bash("python /tmp/script.py", stdout="", stderr="Error: file missing"), stub_env)
    c = load_counter(_state(stub_env))
    assert get_count(c, LoopType.BASH_PATTERN, "python <arg>") == 1


def test_l4_reset_on_clean_success_no_stderr(stub_env: dict[str, str]) -> None:
    seed = new_counter("s")
    increment(seed, LoopType.BASH_PATTERN, "ls", ActionRecord("t", "Bash", "x"))
    save_counter(seed, _state(stub_env))
    _run(_bash("ls", stdout="file1.txt\nfile2.txt", stderr=""), stub_env)
    c = load_counter(_state(stub_env))
    assert get_count(c, LoopType.BASH_PATTERN, "ls") == 0


def test_l4_ambiguous_does_not_change_counter(stub_env: dict[str, str]) -> None:
    """Both stdout and stderr present, no error markers → ambiguous → no-op."""
    seed = new_counter("s")
    increment(seed, LoopType.BASH_PATTERN, "make build", ActionRecord("t", "Bash", "x"))
    save_counter(seed, _state(stub_env))
    _run(_bash("make build", stdout="Compiling...", stderr="warning: deprecated"), stub_env)
    c = load_counter(_state(stub_env))
    assert get_count(c, LoopType.BASH_PATTERN, "make build") == 1  # unchanged


def test_l4_empty_output_treated_as_success(stub_env: dict[str, str]) -> None:
    # tokenize_bash_command preserves bare flags like -p; the path /tmp/foo
    # collapses to <arg>, so the L4 key is "mkdir -p <arg>".
    seed = new_counter("s")
    increment(seed, LoopType.BASH_PATTERN, "mkdir -p <arg>", ActionRecord("t", "Bash", "x"))
    save_counter(seed, _state(stub_env))
    _run(_bash("mkdir -p /tmp/foo", stdout="", stderr=""), stub_env)
    c = load_counter(_state(stub_env))
    assert get_count(c, LoopType.BASH_PATTERN, "mkdir -p <arg>") == 0


def test_l4_does_not_fire_telegram_inline(stub_env: dict[str, str]) -> None:
    """L4 trigger is gated by Step 2 — Step 3 must NOT fire Telegram for L4."""
    seed = new_counter("s")
    for _ in range(5):
        increment(seed, LoopType.BASH_PATTERN, "pytest <arg>", ActionRecord("t", "Bash", "x"))
    save_counter(seed, _state(stub_env))
    _run(_bash("pytest tests/foo.py", interrupted=True), stub_env)
    assert not _capture(stub_env).exists(), "L4 must not fire Telegram inline (Step 2's job)"


# --- L2: pytest test failures (inline Telegram fire on trigger) ---


def test_l2_increments_per_failed_nodeid(stub_env: dict[str, str]) -> None:
    output = "FAILED tests/handoffs/test_foo.py::test_bar - assertion failed"
    payload = _bash("pytest tests/handoffs/test_foo.py", exit_code=1, stdout=output, stderr="")
    _run(payload, stub_env)
    c = load_counter(_state(stub_env))
    assert get_count(c, LoopType.TEST_FAIL, "tests/handoffs/test_foo.py::test_bar") == 1


def test_l2_resets_on_passing_nodeid(stub_env: dict[str, str]) -> None:
    seed = new_counter("s")
    for _ in range(3):
        increment(
            seed,
            LoopType.TEST_FAIL,
            "tests/handoffs/test_foo.py::test_bar",
            ActionRecord("t", "Bash", "x"),
        )
    save_counter(seed, _state(stub_env))
    output = "tests/handoffs/test_foo.py::test_bar PASSED [100%]"
    payload = _bash("pytest -v tests/handoffs/test_foo.py", exit_code=0, stdout=output, stderr="")
    _run(payload, stub_env)
    c = load_counter(_state(stub_env))
    assert get_count(c, LoopType.TEST_FAIL, "tests/handoffs/test_foo.py::test_bar") == 0


def test_l2_multiple_failures_in_one_run(stub_env: dict[str, str]) -> None:
    output = (
        "FAILED tests/foo.py::test_a - msg\n"
        "FAILED tests/foo.py::test_b - msg\n"
        "FAILED tests/foo.py::test_c - msg\n"
    )
    _run(_bash("pytest tests/foo.py", exit_code=1, stdout=output, stderr=""), stub_env)
    c = load_counter(_state(stub_env))
    assert get_count(c, LoopType.TEST_FAIL, "tests/foo.py::test_a") == 1
    assert get_count(c, LoopType.TEST_FAIL, "tests/foo.py::test_b") == 1
    assert get_count(c, LoopType.TEST_FAIL, "tests/foo.py::test_c") == 1


def test_l2_fires_telegram_inline_on_trigger(stub_env: dict[str, str]) -> None:
    """6th observed failure of same nodeid fires Telegram with Cray-E.4 payload."""
    seed = new_counter("s")
    for i in range(5):
        increment(
            seed,
            LoopType.TEST_FAIL,
            "tests/foo.py::test_bar",
            ActionRecord(f"t{i}", "Bash", "tests/foo.py::test_bar", result="failed"),
        )
    save_counter(seed, _state(stub_env))
    output = "FAILED tests/foo.py::test_bar - assertion failed"
    _run(_bash("pytest tests/foo.py", exit_code=1, stdout=output, stderr=""), stub_env)
    cap = _capture(stub_env)
    assert cap.exists(), "Telegram stub was not invoked on L2 trigger"
    body = cap.read_text(encoding="utf-8")
    # Human-readable body (per Lesson #14): argv message, not JSON-on-stdin.
    assert "L2" in body
    assert "tests/foo.py::test_bar" in body
    # All 6 timestamps present → action lines round-tripped through formatter
    for i in range(5):
        assert f"t{i}" in body


def test_l2_parametrized_nodeid_collapses(stub_env: dict[str, str]) -> None:
    output1 = "FAILED tests/foo.py::test_bar[case1] - msg"
    output2 = "FAILED tests/foo.py::test_bar[case2] - msg"
    _run(_bash("pytest tests/foo.py", exit_code=1, stdout=output1, stderr=""), stub_env)
    _run(_bash("pytest tests/foo.py", exit_code=1, stdout=output2, stderr=""), stub_env)
    c = load_counter(_state(stub_env))
    assert get_count(c, LoopType.TEST_FAIL, "tests/foo.py::test_bar") == 2


# --- L3: traceback signature (inline Telegram fire on trigger) ---


def test_l3_extracts_traceback_signature(stub_env: dict[str, str]) -> None:
    output = (
        "Traceback (most recent call last):\n"
        '  File "script.py", line 10, in <module>\n'
        "    raise RuntimeError('foo missing')\n"
        "RuntimeError: foo missing"
    )
    _run(_bash("python script.py", exit_code=1, stdout="", stderr=output), stub_env)
    c = load_counter(_state(stub_env))
    keys = [k for k in c.counters if k.startswith("L3:")]
    assert len(keys) == 1
    assert "RuntimeError" in keys[0]


def test_l3_volatile_bits_normalized(stub_env: dict[str, str]) -> None:
    output_a = (
        "Traceback (most recent call last):\n"
        '  File "x.py", line 1, in <module>\n'
        "RuntimeError: error at 2026-05-24T15:00:00+07:00"
    )
    output_b = (
        "Traceback (most recent call last):\n"
        '  File "x.py", line 1, in <module>\n'
        "RuntimeError: error at 2026-05-25T08:30:42Z"
    )
    _run(_bash("python a.py", exit_code=1, stdout="", stderr=output_a), stub_env)
    _run(_bash("python b.py", exit_code=1, stdout="", stderr=output_b), stub_env)
    c = load_counter(_state(stub_env))
    l3_keys = [k for k in c.counters if k.startswith("L3:")]
    assert len(l3_keys) == 1  # both collapsed to one normalized signature
    assert c.counters[l3_keys[0]].count == 2


def test_l3_fires_telegram_inline_on_trigger(stub_env: dict[str, str]) -> None:
    sig = "RuntimeError: persistent failure"
    seed = new_counter("s")
    for i in range(5):
        increment(seed, LoopType.ERROR_SIGNATURE, sig, ActionRecord(f"t{i}", "Bash", sig, "error"))
    save_counter(seed, _state(stub_env))
    output = (
        "Traceback (most recent call last):\n"
        '  File "x.py", line 1, in <module>\n'
        "RuntimeError: persistent failure"
    )
    _run(_bash("python x.py", exit_code=1, stdout="", stderr=output), stub_env)
    cap = _capture(stub_env)
    assert cap.exists()
    body = cap.read_text(encoding="utf-8")
    # Human-readable body (per Lesson #14): argv message, not JSON-on-stdin.
    assert "L3" in body
    assert "RuntimeError" in body


def test_l3_no_traceback_no_op(stub_env: dict[str, str]) -> None:
    _run(_bash("echo hello", exit_code=0, stdout="hello", stderr=""), stub_env)
    c = load_counter(_state(stub_env))
    assert not any(k.startswith("L3:") for k in c.counters)


# --- Combined: one bash call that triggers L2 + L4 + L3 ---


def test_combined_pytest_failure_increments_l2_l3_l4(stub_env: dict[str, str]) -> None:
    output = (
        "FAILED tests/foo.py::test_bar - assertion\n"
        "Traceback (most recent call last):\n"
        '  File "tests/foo.py", line 5, in test_bar\n'
        "    assert 1 == 2\n"
        "AssertionError: 1 != 2"
    )
    _run(_bash("pytest tests/foo.py", exit_code=1, stdout=output, stderr=""), stub_env)
    c = load_counter(_state(stub_env))
    assert get_count(c, LoopType.TEST_FAIL, "tests/foo.py::test_bar") == 1
    assert get_count(c, LoopType.BASH_PATTERN, "pytest <arg>") == 1
    assert any(k.startswith("L3:") and "AssertionError" in k for k in c.counters)


# --- Malformed inputs / non-target tools ---


def test_malformed_json_fails_open(stub_env: dict[str, str]) -> None:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json",
        capture_output=True,
        text=True,
        env=stub_env,
        check=False,
        timeout=15,
    )
    assert result.returncode == 0


def test_non_target_tool_ignored(stub_env: dict[str, str]) -> None:
    _run({"tool_name": "Read", "tool_input": {"file_path": "x.py"}, "tool_response": {}}, stub_env)
    c = load_counter(_state(stub_env))
    assert c.counters == {}


def test_missing_tool_response_no_crash(stub_env: dict[str, str]) -> None:
    payload = {"tool_name": "Bash", "tool_input": {"command": "ls"}}
    rc = _run(payload, stub_env)
    assert rc == 0  # graceful


def test_non_dict_tool_input_no_crash(stub_env: dict[str, str]) -> None:
    payload = {"tool_name": "Bash", "tool_input": "not-a-dict", "tool_response": {}}
    rc = _run(payload, stub_env)
    assert rc == 0


def test_non_dict_tool_response_no_crash(stub_env: dict[str, str]) -> None:
    payload = {"tool_name": "Bash", "tool_input": {"command": "ls"}, "tool_response": "not-a-dict"}
    rc = _run(payload, stub_env)
    assert rc == 0


# --- Wiring sanity: state file is atomic + readable after run ---


def test_state_file_is_valid_json_after_run(stub_env: dict[str, str]) -> None:
    _run(_write("docs/STATUS.md"), stub_env)
    state_path = _state(stub_env)
    assert state_path.exists()
    # Should round-trip via load_counter without exception
    c = load_counter(state_path)
    assert c.counters


def test_state_file_no_leftover_tmp(stub_env: dict[str, str], tmp_path: Path) -> None:
    _run(_write("docs/STATUS.md"), stub_env)
    leftovers = list(tmp_path.glob("*.tmp"))
    assert leftovers == []
