"""Tests for ``.claude/hooks/posttooluse_progress_observer.py`` (PLAN-0008 Step 3).

Covers:

**PLAN-0102 removed the L1 sections** — the Write/Edit increment, the
non-progress scoring (PLAN-0094 AC-7/AC-8), the commit-boundary reset and the
SubagentStop reset. Every one of them was L1 at both ends. The Bash path is
what survives, and PLAN-0102 AC-11 (b) guards the subtlest thing the excision
could have broken there: the commit reset lived ON the Bash path, so deleting
it wrong would have silently stopped L2/L3/L4 counters persisting while the
hook still exited 0.

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
import shutil
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

_GIT = shutil.which("git") or "git"


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run([_GIT, *args], cwd=repo, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")


def _commit_file(repo: Path, relpath: str, content: str, msg: str) -> None:
    path = repo / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _git(repo, "add", relpath)
    _git(repo, "commit", "-q", "-m", msg)


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
    """A run that CHANGES a counter must leave a loadable state file.

    Driven by a failing Bash call rather than a Write: PLAN-0102 retired the
    Write/Edit path, so a Write now correctly writes nothing at all — which
    would have made this assertion fail for a reason that has nothing to do
    with atomicity. The producing call has to be one that still produces.
    """
    _run(_bash("pytest tests/x.py", exit_code=1), stub_env)
    state_path = _state(stub_env)
    assert state_path.exists()
    # Should round-trip via load_counter without exception
    c = load_counter(state_path)
    assert c.counters


def test_state_file_no_leftover_tmp(stub_env: dict[str, str], tmp_path: Path) -> None:
    _run(_bash("pytest tests/x.py", exit_code=1), stub_env)
    leftovers = list(tmp_path.glob("*.tmp"))
    assert leftovers == []


# --- PLAN-0102 AC-11 (b): the Bash path still PERSISTS across a git commit ---


def test_ac11b_git_commit_still_persists_l3_to_the_state_file_on_disk(
    stub_env: dict[str, str],
) -> None:
    """A successful ``git commit`` must not stop the surviving counters saving.

    **This asserts the FILE, not the return value, and that is the whole
    point.** The commit-boundary L1 reset used to run on this exact path, and
    its body referenced ``LoopType.FILE_EDIT``. Removing the enum member while
    leaving the call would raise ``AttributeError`` inside ``_handle_bash`` —
    which ``main()``'s blanket ``except Exception`` **swallows**. The hook would
    still print nothing, still exit 0, and ``save_counter`` would simply never
    run: L2, L3 and L4 would quietly stop persisting with no visible symptom at
    all. Nothing that checks an exit code can see that; only reading the file
    can.

    The payload is realistic rather than synthetic: a commit that succeeds while
    a non-blocking hook prints a traceback into the output is an ordinary
    pre-commit shape, and it is exactly the combination — commit path plus a
    countable signature — that the swallowed error would have eaten.

    RED when: any statement that can raise is reintroduced between the counter
    mutations and ``save_counter`` in ``_handle_bash``.
    """
    hook_noise = (
        "detect-secrets....................................................Passed\n"
        "Traceback (most recent call last):\n"
        '  File "/hooks/plugin.py", line 12, in <module>\n'
        "    warn()\n"
        "DeprecationWarning: plugin API v1 is deprecated\n"
        "[main 1a2b3c4] chore: a real commit\n"
        " 1 file changed, 2 insertions(+)\n"
    )
    payload = _bash("git commit -F /tmp/msg.txt", exit_code=0, stdout=hook_noise, stderr="")
    rc = _run(payload, stub_env)
    assert rc == 0

    state_path = _state(stub_env)
    assert state_path.exists(), (
        "no state file after a git-commit Bash call — save_counter did not run, "
        "which is the swallowed-AttributeError shape this guard exists for"
    )
    raw = json.loads(state_path.read_text(encoding="utf-8"))
    l3_keys = [k for k in raw.get("counters", {}) if k.startswith("L3:")]
    assert l3_keys, f"the L3 signature never reached disk; counters={raw.get('counters')}"
    assert raw["counters"][l3_keys[0]]["count"] == 1
