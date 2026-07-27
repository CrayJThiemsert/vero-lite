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

import hashlib
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

import posttooluse_progress_observer as obs  # noqa: E402  — sys.path manipulation above
from _loop_counter import (  # noqa: E402  — sys.path manipulation above
    ActionRecord,
    LoopType,
    counter_key,
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


# --- L1: Write/Edit increment ---


def test_l1_forward_write_is_recorded_without_counting(
    stub_env: dict[str, str], tmp_path: Path
) -> None:
    """PLAN-0094 Step 4 replaced the unit: a forward write is seen, not scored.

    Until Step 4 this asserted ``count == 1`` — it was the canonical statement
    of the OLD unit (touches). AC-7 makes that assertion wrong on purpose.
    """
    target = tmp_path / "notes.md"
    target.write_text("v1\n", encoding="utf-8")
    assert _run(_write_at(target, "v1\n"), stub_env) == 0

    counter = load_counter(_state(stub_env))
    key = str(target)
    assert get_count(counter, LoopType.FILE_EDIT, key) == 0
    assert len(counter.counters[counter_key(LoopType.FILE_EDIT, key)].last_6_actions) == 1


def test_l1_write_and_edit_share_one_counter(stub_env: dict[str, str], tmp_path: Path) -> None:
    """A Write and an Edit of one target land on ONE entry, whatever they score."""
    target = tmp_path / "notes.md"
    target.write_text("v1\n", encoding="utf-8")
    _run(_write_at(target, "v1\n"), stub_env)
    target.write_text("v2\n", encoding="utf-8")
    _run(_edit_at(target, "anchor", "x"), stub_env)

    counter = load_counter(_state(stub_env))
    key = counter_key(LoopType.FILE_EDIT, str(target))
    assert list(counter.counters) == [key]
    assert len(counter.counters[key].last_6_actions) == 2


def test_l1_path_normalization_windows_unc(stub_env: dict[str, str]) -> None:
    unc = "\\\\wsl.localhost\\Ubuntu-24.04\\home\\crayj\\work\\vero-lite\\docs\\STATUS.md"
    _run(_write(unc), stub_env)
    _run(_write("docs/STATUS.md"), stub_env)
    counter = load_counter(_state(stub_env))
    # Both paths collapse to the same normalized target: ONE entry, both actions.
    # Asserted on the key rather than the count so this stays a test of path
    # normalization and says nothing about what scores.
    key = counter_key(LoopType.FILE_EDIT, "docs/STATUS.md")
    assert list(counter.counters) == [key]
    assert len(counter.counters[key].last_6_actions) == 2


def test_l1_does_not_fire_telegram_inline(stub_env: dict[str, str], tmp_path: Path) -> None:
    """L1's deny is gated by Step 2 on the NEXT attempt — this hook must NOT
    fire Telegram for L1 below the path-class warn bar.
    """
    # Pre-seed L1 to 5, then one more Write — no Telegram either way.
    target = tmp_path / "notes.md"  # .md → doc class, warn bar 15
    target.write_text("v1\n", encoding="utf-8")
    seed = new_counter("s")
    for _ in range(5):
        increment(seed, LoopType.FILE_EDIT, str(target), ActionRecord("t", "Edit", "x"))
    save_counter(seed, _state(stub_env))
    _run(_write_at(target, "v1\n"), stub_env)
    assert not _capture(stub_env).exists(), "L1 must not fire Telegram inline (Step 2's job)"
    counter = load_counter(_state(stub_env))
    # The write is forward progress, so the seeded count is unchanged (AC-7).
    assert get_count(counter, LoopType.FILE_EDIT, str(target)) == 5


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


# --- PLAN-0094 Step 4: L1 counts NON-PROGRESS, not touches (AC-7 / AC-8) ---
#
# Every target here is a real file under ``tmp_path``, never a repo path. (c)
# hashes the file ON DISK, so pointing these at ``docs/STATUS.md`` would couple
# the assertions to that file's live content — the trap the s179 handoff flagged.


def _write_at(path: Path, content: str) -> Payload:
    """A successful Write payload; the caller must have already written `content`."""
    return {
        "tool_name": "Write",
        "tool_input": {"file_path": str(path), "content": content},
        "tool_response": {},
    }


def _edit_at(path: Path, old: str, new: str) -> Payload:
    """A successful Edit payload with an EXPLICIT ``old_string``.

    Deliberately not the module-level ``_edit`` helper, whose ``old_string`` is
    the constant ``"a"`` — under (b) that constant makes every second call a
    "repeat", which would silently turn a forward-progress fixture into a
    thrash fixture.
    """
    return {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(path), "old_string": old, "new_string": new},
        "tool_response": {},
    }


def _entry(env: dict[str, str], target: str) -> Any:
    return load_counter(_state(env)).counters[counter_key(LoopType.FILE_EDIT, target)]


def _sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8"), usedforsecurity=False).hexdigest()


def test_ac7_six_distinct_forward_edits_score_zero(
    stub_env: dict[str, str], tmp_path: Path
) -> None:
    """AC-7 — the s168/s172 regression: distinct forward progress must not count.

    Six successful Edits, each with a distinct ``old_string`` and each advancing
    the file to new content, leave ``count == 0`` while the evidence ring and
    ``turn_touched`` still hold everything.
    """
    target = tmp_path / "module.py"
    for i in range(6):
        target.write_text(f"revision {i}\n" * (i + 1), encoding="utf-8")
        assert _run(_edit_at(target, f"anchor-{i}", f"replacement-{i}"), stub_env) == 0

    key = str(target)
    counter = load_counter(_state(stub_env))
    assert get_count(counter, LoopType.FILE_EDIT, key) == 0
    entry = counter.counters[counter_key(LoopType.FILE_EDIT, key)]
    assert len(entry.last_6_actions) == 6, "all six must still be in the evidence ring"
    # R3 (OQ-3) — a forward edit records the EMPTY result, not "forward": both
    # formatters bracket ``result`` only when non-empty, so emptiness is what
    # keeps "[...]" meaning "this row is why you were interrupted".
    assert [a.result for a in entry.last_6_actions] == [""] * 6
    assert counter.turn_touched == [key]


def test_ac8i_repeated_old_string_counts_once(stub_env: dict[str, str], tmp_path: Path) -> None:
    """AC-8(i) — the same ``old_string`` re-applied is churn, not progress.

    Content advances between the two calls, so (c) cannot fire and the single
    increment is attributable to (b) alone.
    """
    target = tmp_path / "module.py"
    target.write_text("first\n", encoding="utf-8")
    _run(_edit_at(target, "same-anchor", "x"), stub_env)
    target.write_text("second\n", encoding="utf-8")
    _run(_edit_at(target, "same-anchor", "y"), stub_env)

    key = str(target)
    assert get_count(load_counter(_state(stub_env)), LoopType.FILE_EDIT, key) == 1
    entry = _entry(stub_env, key)
    assert entry.last_6_actions[-1].result == "repeat x2"
    # OQ-3 R2 — a dict, not a set: the tally is what the recorded count reads.
    assert entry.attempted_edits[_sha1("same-anchor")] == 2


def test_ac8iii_content_returning_to_prior_state_counts(
    stub_env: dict[str, str], tmp_path: Path
) -> None:
    """AC-8(iii) — oscillation: the file returns to a state it already held.

    Every ``old_string`` is distinct, so (b) cannot fire and the single
    increment is attributable to (c) alone.
    """
    target = tmp_path / "module.py"
    for i, content in enumerate(("A\n", "B\n", "A\n")):
        target.write_text(content, encoding="utf-8")
        _run(_edit_at(target, f"anchor-{i}", "z"), stub_env)

    key = str(target)
    assert get_count(load_counter(_state(stub_env)), LoopType.FILE_EDIT, key) == 1
    entry = _entry(stub_env, key)
    assert entry.last_6_actions[-1].result == "osc x2"


def test_ac8_unreadable_target_fails_open(stub_env: dict[str, str], tmp_path: Path) -> None:
    """(c) must never raise: it runs on EVERY Write/Edit.

    A payload naming a file that does not exist on disk yields no content
    digest. The hook must still exit 0 and still record the action — losing an
    oscillation signal is a rounding error next to breaking every edit in the
    session, which is what a raise in this path would do.
    """
    missing = tmp_path / "never-created.py"
    assert _run(_write_at(missing, "irrelevant"), stub_env) == 0
    entry = _entry(stub_env, str(missing))
    assert entry.count == 0
    assert len(entry.last_6_actions) == 1


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


# --- Commit-boundary L1 reset (follow-up, 2026-05-29) ---


@pytest.mark.parametrize(
    "command",
    [
        "git commit",
        "git commit -F /tmp/m.txt",
        "cd ~/work/vero-lite && git commit -m y",
        'wsl bash -lc "cd ~/work/vero-lite && git commit -F /tmp/commit-message.txt"',
    ],
)
def test_is_git_commit_positive(command: str) -> None:
    assert obs._is_git_commit(command) is True


@pytest.mark.parametrize(
    "command",
    ["git commit-tree abc123", "git status", "git log --grep=commit", "git add ."],
)
def test_is_git_commit_negative(command: str) -> None:
    assert obs._is_git_commit(command) is False


def test_committed_files_lists_head_commit_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    _commit_file(repo, "README.md", "base\n", "feat: base")  # parent so diff-tree works
    _commit_file(repo, "tools/foo.py", "x\n", "feat: add foo")
    assert obs._committed_files(repo) == ["tools/foo.py"]


def test_committed_files_fails_closed_outside_repo(tmp_path: Path) -> None:
    """A non-git directory yields [] (fail-closed), never raises."""
    assert obs._committed_files(tmp_path) == []


def test_git_commit_resets_only_committed_file_l1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A successful git commit resets the L1 counter for the committed file
    but leaves an unrelated file's counter untouched (no masking)."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    _commit_file(repo, "README.md", "base\n", "feat: base")
    _commit_file(repo, "tools/foo.py", "x\n", "feat: add foo")  # HEAD touches tools/foo.py
    monkeypatch.setattr(obs, "REPO_ROOT", repo)

    state_path = tmp_path / "loop-counter.json"
    monkeypatch.setenv("CLAUDE_LOOP_COUNTER_PATH", str(state_path))
    counter = new_counter()
    for _ in range(6):
        increment(counter, LoopType.FILE_EDIT, "tools/foo.py")
    for _ in range(3):
        increment(counter, LoopType.FILE_EDIT, "tools/bar.py")
    save_counter(counter, state_path)

    obs._handle_bash(_bash("git commit -m 'feat: add foo'", exit_code=0))

    after = load_counter(state_path)
    assert get_count(after, LoopType.FILE_EDIT, "tools/foo.py") == 0  # reset (committed)
    assert get_count(after, LoopType.FILE_EDIT, "tools/bar.py") == 3  # untouched


def test_failed_git_commit_does_not_reset_l1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    _commit_file(repo, "README.md", "base\n", "feat: base")
    _commit_file(repo, "tools/foo.py", "x\n", "feat: add foo")
    monkeypatch.setattr(obs, "REPO_ROOT", repo)

    state_path = tmp_path / "loop-counter.json"
    monkeypatch.setenv("CLAUDE_LOOP_COUNTER_PATH", str(state_path))
    counter = new_counter()
    for _ in range(6):
        increment(counter, LoopType.FILE_EDIT, "tools/foo.py")
    save_counter(counter, state_path)

    obs._handle_bash(_bash("git commit -m x", exit_code=1))  # failed commit

    after = load_counter(state_path)
    assert get_count(after, LoopType.FILE_EDIT, "tools/foo.py") == 6  # NOT reset


def test_non_commit_bash_does_not_reset_l1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    _commit_file(repo, "README.md", "base\n", "feat: base")
    _commit_file(repo, "tools/foo.py", "x\n", "feat: add foo")
    monkeypatch.setattr(obs, "REPO_ROOT", repo)

    state_path = tmp_path / "loop-counter.json"
    monkeypatch.setenv("CLAUDE_LOOP_COUNTER_PATH", str(state_path))
    counter = new_counter()
    for _ in range(6):
        increment(counter, LoopType.FILE_EDIT, "tools/foo.py")
    save_counter(counter, state_path)

    obs._handle_bash(_bash("git status", exit_code=0))

    after = load_counter(state_path)
    assert get_count(after, LoopType.FILE_EDIT, "tools/foo.py") == 6  # NOT reset


# --- Subagent-completion L1 reset, on SubagentStop, scoped per agent ---------
#
# PLAN-0094 D1 (AC-2). Replaces the 2026-06-08 block, which drove the handler
# through a ``tool_name in ("Task","Agent")`` PostToolUse branch that
# ``settings.json`` never registered — the tests passed on synthetic payloads
# while the mechanism was unreachable in production. Two things change:
#
#   1. the route is ``SubagentStop`` (pinned as data by
#      ``test_settings_hook_wiring.py`` so it cannot silently vanish again);
#   2. the reset is scoped to the *completing subagent's own* recorded edits,
#      not to ``turn_touched``. Cray ratified the divergence from Lesson #0021
#      §3 (2026-07-25): turn-scoped semantics were never live, and wiring them
#      as written would have let the main agent launder its own exhausted budget
#      through any zero-edit spawn.


def _subagent_stop(agent_id: str | None = "agent-A") -> Payload:
    payload: Payload = {"hook_event_name": "SubagentStop"}
    if agent_id is not None:
        payload["agent_id"] = agent_id
    return payload


def _write_as_subagent(file_path: str, agent_id: str) -> Payload:
    """A Write performed inside a subagent — same shared counter, tagged."""
    payload = _write(file_path)
    payload["agent_id"] = agent_id
    return payload


def _seed_l1(env: dict[str, str], target: str, n: int) -> None:
    """Put ``n`` on an L1 counter directly, merging into existing state.

    Since PLAN-0094 Step 4 a *forward* Write no longer increments, so the old
    idiom of driving a counter up by repeating hook calls would now need
    contrived thrash payloads. These tests are about subagent reset
    ATTRIBUTION — which target clears when which agent finishes — not about
    what scores, so the count is staged directly and the hook is called only
    where the attribution itself is under test.
    """
    counter = load_counter(_state(env))
    for _ in range(n):
        increment(counter, LoopType.FILE_EDIT, target, ActionRecord("t", "Write", target))
    save_counter(counter, _state(env))


def test_subagent_stop_resets_that_agents_own_edits(stub_env: dict[str, str]) -> None:
    """The restored exit: a drafter's edits stop spending the main agent's budget."""
    state = _state(stub_env)
    _run(_write_as_subagent("docs/plans/0019-x.md", "agent-A"), stub_env)  # attribute
    _seed_l1(stub_env, "docs/plans/0019-x.md", 3)
    assert get_count(load_counter(state), LoopType.FILE_EDIT, "docs/plans/0019-x.md") == 3

    _run(_subagent_stop("agent-A"), stub_env)

    after = load_counter(state)
    assert get_count(after, LoopType.FILE_EDIT, "docs/plans/0019-x.md") == 0


def test_subagent_stop_with_no_recorded_edits_resets_nothing(
    stub_env: dict[str, str],
) -> None:
    """A zero-edit spawn must not clear anything at all."""
    state = _state(stub_env)
    _seed_l1(stub_env, "services/x.py", 6)  # main agent, no agent_id
    assert get_count(load_counter(state), LoopType.FILE_EDIT, "services/x.py") == 6

    _run(_subagent_stop("agent-never-edited"), stub_env)

    after = load_counter(state)
    assert get_count(after, LoopType.FILE_EDIT, "services/x.py") == 6


def test_subagent_stop_never_clears_the_main_agents_own_target(
    stub_env: dict[str, str],
) -> None:
    """Anti-self-unlock: the main agent cannot launder its budget via a spawn.

    This is the hazard that turn-scoped semantics would have introduced. The
    subagent's own target clears; the main agent's does not.
    """
    state = _state(stub_env)
    _seed_l1(stub_env, "services/main_owned.py", 6)
    _run(_write_as_subagent("services/agent_owned.py", "agent-A"), stub_env)
    _seed_l1(stub_env, "services/agent_owned.py", 2)

    _run(_subagent_stop("agent-A"), stub_env)

    after = load_counter(state)
    assert get_count(after, LoopType.FILE_EDIT, "services/agent_owned.py") == 0
    assert get_count(after, LoopType.FILE_EDIT, "services/main_owned.py") == 6


def test_subagent_stop_does_not_clear_a_still_running_siblings_edits(
    stub_env: dict[str, str],
) -> None:
    """Per-agent keying (R2-3): A completing must not clear B's in-flight edits."""
    state = _state(stub_env)
    _run(_write_as_subagent("services/a.py", "agent-A"), stub_env)
    _seed_l1(stub_env, "services/a.py", 3)
    _run(_write_as_subagent("services/b.py", "agent-B"), stub_env)
    _seed_l1(stub_env, "services/b.py", 4)

    _run(_subagent_stop("agent-A"), stub_env)

    after = load_counter(state)
    assert get_count(after, LoopType.FILE_EDIT, "services/a.py") == 0
    assert get_count(after, LoopType.FILE_EDIT, "services/b.py") == 4


def test_subagent_stop_without_agent_id_clears_all_subagent_edits(
    stub_env: dict[str, str],
) -> None:
    """Fail-safe: an unpopulated ``agent_id`` over-clears, but only subagent edits.

    Failing toward bounded over-clearing beats leaving a completed drafter's
    budget wedged — but the blast radius stays inside targets a subagent
    actually touched, so the main agent's own counter still survives.
    """
    state = _state(stub_env)
    _seed_l1(stub_env, "services/main_owned.py", 6)
    _run(_write_as_subagent("services/a.py", "agent-A"), stub_env)
    _seed_l1(stub_env, "services/a.py", 3)
    _run(_write_as_subagent("services/b.py", "agent-B"), stub_env)
    _seed_l1(stub_env, "services/b.py", 4)

    _run(_subagent_stop(agent_id=None), stub_env)

    after = load_counter(state)
    assert get_count(after, LoopType.FILE_EDIT, "services/a.py") == 0
    assert get_count(after, LoopType.FILE_EDIT, "services/b.py") == 0
    assert get_count(after, LoopType.FILE_EDIT, "services/main_owned.py") == 6
