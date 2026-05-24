"""Tests for ``.claude/hooks/_loop_counter.py`` (PLAN-0008 Step 1).

Covers:

- Schema round-trip (LoopCounter <-> JSON)
- Atomic write (tmpfile + os.replace; no partial-write window)
- Concurrent-write tolerance (last writer wins; no corruption)
- Load tolerance (missing file, empty file, malformed JSON, wrong root)
- Normalization helpers (file path / pytest nodeid / error signature
  / bash command)
- Counter ops (increment, reset, get_count, has_triggered, ring buffer)
- Session-ID resolution (env -> PID -> UUID fallback chain)
"""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parents[2] / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from _loop_counter import (  # noqa: E402  — sys.path manipulation above
    LOOP_TRIGGER_THRESHOLD,
    MAX_RECENT_ACTIONS,
    ActionRecord,
    CounterEntry,
    LoopCounter,
    LoopType,
    counter_key,
    get_count,
    has_triggered,
    increment,
    load_counter,
    new_counter,
    normalize_error_signature,
    normalize_file_path,
    normalize_pytest_nodeid,
    reset,
    resolve_session_id,
    save_counter,
    tokenize_bash_command,
)

# --- Schema round-trip ---


def test_action_record_round_trip() -> None:
    a = ActionRecord(ts="2026-05-24T15:00:00+0000", tool="Edit", target="x.py", result="ok")
    assert ActionRecord.from_json(a.to_json()) == a


def test_counter_entry_round_trip() -> None:
    e = CounterEntry(
        count=3,
        last_6_actions=[ActionRecord(ts="t", tool="Edit", target="x", result="r")],
        last_updated="t",
    )
    assert CounterEntry.from_json(e.to_json()) == e


def test_loop_counter_round_trip() -> None:
    c = new_counter(session_id="test-session")
    increment(c, LoopType.FILE_EDIT, "x.py", ActionRecord("t", "Edit", "x.py"))
    increment(c, LoopType.TEST_FAIL, "tests/foo.py::test_bar")
    restored = LoopCounter.from_json(c.to_json())
    assert restored.session_id == c.session_id
    assert restored.started_at == c.started_at
    assert set(restored.counters) == set(c.counters)
    assert restored.counters[counter_key(LoopType.FILE_EDIT, "x.py")].count == 1


def test_loop_counter_unknown_fields_ignored() -> None:
    raw = {
        "session_id": "s",
        "started_at": "t",
        "counters": {"L1:foo": {"count": 2}},
        "unexpected_field": "junk",
    }
    c = LoopCounter.from_json(raw)
    assert c.session_id == "s"
    assert c.counters["L1:foo"].count == 2


# --- counter_key ---


def test_counter_key_format() -> None:
    assert counter_key(LoopType.FILE_EDIT, "docs/STATUS.md") == "L1:docs/STATUS.md"
    assert counter_key(LoopType.BASH_PATTERN, "pytest <arg>") == "L4:pytest <arg>"


# --- File-path normalization (L1) ---


def test_normalize_file_path_relative_posix() -> None:
    assert normalize_file_path("docs/STATUS.md") == "docs/STATUS.md"


def test_normalize_file_path_backslash() -> None:
    assert normalize_file_path("docs\\STATUS.md") == "docs/STATUS.md"


def test_normalize_file_path_wsl_unc() -> None:
    p = "\\\\wsl.localhost\\Ubuntu-24.04\\home\\crayj\\work\\vero-lite\\docs\\STATUS.md"
    assert normalize_file_path(p) == "docs/STATUS.md"


def test_normalize_file_path_posix_absolute_inside_repo() -> None:
    p = "/home/crayj/work/vero-lite/docs/STATUS.md"
    assert normalize_file_path(p) == "docs/STATUS.md"


def test_normalize_file_path_empty() -> None:
    assert normalize_file_path("") == ""


def test_normalize_file_path_outside_repo_kept_normalized() -> None:
    # External absolute path with no vero-lite marker -> slash-normalized
    # fallback (we don't drop it; callers can decide to ignore).
    result = normalize_file_path("/etc/hosts")
    assert "/" in result  # forward slashes preserved


# --- Pytest nodeid normalization (L2) ---


def test_normalize_pytest_nodeid_plain() -> None:
    n = "tests/handoffs/test_loop_counter_state.py::test_round_trip"
    assert normalize_pytest_nodeid(n) == n


def test_normalize_pytest_nodeid_strips_param() -> None:
    base = "tests/handoffs/test_foo.py::test_bar"
    assert normalize_pytest_nodeid(f"{base}[2026-05-24]") == base


def test_normalize_pytest_nodeid_strips_complex_param() -> None:
    base = "tests/handoffs/test_foo.py::test_bar"
    assert normalize_pytest_nodeid(f"{base}[case-1-x-y-z]") == base


def test_normalize_pytest_nodeid_empty() -> None:
    assert normalize_pytest_nodeid("") == ""


def test_normalize_pytest_nodeid_only_inner_brackets_preserved() -> None:
    # Only the *trailing* [param] suffix is stripped; brackets in the
    # middle of the nodeid stay intact (defensive, unlikely in practice).
    n = "tests/foo.py::TestClass[edge]::test_bar"
    assert normalize_pytest_nodeid(n) == n


# --- Error-signature normalization (L3) ---


def test_normalize_error_signature_strips_timestamp() -> None:
    a = normalize_error_signature("RuntimeError at 2026-05-24T15:00:00+07:00: oops")
    b = normalize_error_signature("RuntimeError at 2026-05-25T08:30:42Z: oops")
    assert a == b
    assert "<ts>" in a


def test_normalize_error_signature_strips_hex_address() -> None:
    a = normalize_error_signature("<Foo object at 0x7fbabcdef012>")
    b = normalize_error_signature("<Foo object at 0x7fbabcdef999>")
    assert a == b


def test_normalize_error_signature_strips_tmp_path() -> None:
    a = normalize_error_signature("OSError: /tmp/abc123/scratch.txt missing")
    b = normalize_error_signature("OSError: /tmp/xyz999/scratch.txt missing")
    assert a == b


def test_normalize_error_signature_strips_pid() -> None:
    a = normalize_error_signature("connection refused pid=12345 to upstream")
    b = normalize_error_signature("connection refused pid=99999 to upstream")
    assert a == b


def test_normalize_error_signature_strips_uuid() -> None:
    a = normalize_error_signature("UUID 12345678-1234-1234-1234-123456789abc not found")
    b = normalize_error_signature("UUID abcdef01-2345-6789-abcd-ef0123456789 not found")
    assert a == b


def test_normalize_error_signature_collapses_whitespace() -> None:
    assert normalize_error_signature("foo    bar\t\tbaz") == "foo bar baz"


def test_normalize_error_signature_empty() -> None:
    assert normalize_error_signature("") == ""


# --- Bash command tokenization (L4) ---


def test_tokenize_bash_pytest_path_collapses() -> None:
    a = tokenize_bash_command("pytest tests/foo.py")
    b = tokenize_bash_command("pytest tests/bar.py")
    assert a == b
    assert a == "pytest <arg>"


def test_tokenize_bash_preserves_bare_flags() -> None:
    assert tokenize_bash_command("pytest -v tests/foo.py") == "pytest -v <arg>"


def test_tokenize_bash_collapses_flag_with_value() -> None:
    a = tokenize_bash_command("git log --format=%h -10")
    b = tokenize_bash_command("git log --format=%an -20")
    assert a == b


def test_tokenize_bash_handles_quoted_args() -> None:
    a = tokenize_bash_command("bash -c 'foo bar'")
    b = tokenize_bash_command("bash -c 'baz qux'")
    assert a == b


def test_tokenize_bash_collapses_run_of_args() -> None:
    # Multiple consecutive args collapse to a single <arg> token.
    out = tokenize_bash_command("cmd /a/b /c/d /e/f")
    assert out == "cmd <arg>"


def test_tokenize_bash_empty() -> None:
    assert tokenize_bash_command("") == ""


# --- Session-ID resolution (OQ-A) ---


def test_resolve_session_id_prefers_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_SESSION_ID", "harness-supplied-id")
    assert resolve_session_id() == "harness-supplied-id"


def test_resolve_session_id_falls_back_to_pid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
    sid = resolve_session_id()
    assert sid.startswith("pid-")
    assert sid[4:].isdigit()


def test_resolve_session_id_uuid_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
    monkeypatch.setattr("_loop_counter.os.getpid", lambda: 0)
    sid = resolve_session_id()
    assert sid.startswith("uuid-")


# --- Counter ops ---


def test_increment_creates_then_grows() -> None:
    c = new_counter("s")
    increment(c, LoopType.FILE_EDIT, "x.py", ActionRecord("t", "Edit", "x.py"))
    assert get_count(c, LoopType.FILE_EDIT, "x.py") == 1
    increment(c, LoopType.FILE_EDIT, "x.py", ActionRecord("t", "Edit", "x.py"))
    assert get_count(c, LoopType.FILE_EDIT, "x.py") == 2
    assert get_count(c, LoopType.FILE_EDIT, "other.py") == 0


def test_increment_independent_per_loop_type() -> None:
    c = new_counter("s")
    increment(c, LoopType.FILE_EDIT, "x.py")
    increment(c, LoopType.TEST_FAIL, "x.py")
    assert get_count(c, LoopType.FILE_EDIT, "x.py") == 1
    assert get_count(c, LoopType.TEST_FAIL, "x.py") == 1


def test_last_6_actions_ring_buffer_caps() -> None:
    c = new_counter("s")
    for i in range(10):
        increment(
            c,
            LoopType.FILE_EDIT,
            "x.py",
            ActionRecord(ts=f"t{i}", tool="Edit", target="x.py", result=str(i)),
        )
    entry = c.counters[counter_key(LoopType.FILE_EDIT, "x.py")]
    assert entry.count == 10
    assert len(entry.last_6_actions) == MAX_RECENT_ACTIONS
    # Tail of ring buffer retained: t4..t9
    assert [a.result for a in entry.last_6_actions] == ["4", "5", "6", "7", "8", "9"]


def test_reset_removes_entry() -> None:
    c = new_counter("s")
    increment(c, LoopType.FILE_EDIT, "x.py")
    reset(c, LoopType.FILE_EDIT, "x.py")
    assert get_count(c, LoopType.FILE_EDIT, "x.py") == 0
    assert counter_key(LoopType.FILE_EDIT, "x.py") not in c.counters


def test_reset_idempotent_on_missing() -> None:
    c = new_counter("s")
    reset(c, LoopType.FILE_EDIT, "never-was-there.py")  # must not raise


def test_has_triggered_at_threshold() -> None:
    c = new_counter("s")
    for _ in range(LOOP_TRIGGER_THRESHOLD - 1):
        increment(c, LoopType.FILE_EDIT, "x.py")
    assert not has_triggered(c, LoopType.FILE_EDIT, "x.py")
    increment(c, LoopType.FILE_EDIT, "x.py")
    assert has_triggered(c, LoopType.FILE_EDIT, "x.py")


def test_has_triggered_custom_threshold() -> None:
    c = new_counter("s")
    increment(c, LoopType.FILE_EDIT, "x.py")
    assert has_triggered(c, LoopType.FILE_EDIT, "x.py", threshold=1)
    assert not has_triggered(c, LoopType.FILE_EDIT, "x.py", threshold=2)


# --- Atomic load/save ---


def test_save_and_load_round_trip(tmp_path: Path) -> None:
    state_path = tmp_path / "loop-counter.json"
    c = new_counter("test-session")
    increment(c, LoopType.FILE_EDIT, "docs/STATUS.md", ActionRecord("t", "Edit", "docs/STATUS.md"))
    save_counter(c, state_path)
    loaded = load_counter(state_path)
    assert loaded.session_id == "test-session"
    assert get_count(loaded, LoopType.FILE_EDIT, "docs/STATUS.md") == 1


def test_load_missing_file_returns_fresh(tmp_path: Path) -> None:
    state_path = tmp_path / "nope.json"
    c = load_counter(state_path)
    assert c.counters == {}
    assert c.session_id  # populated by resolve_session_id


def test_load_empty_file_returns_fresh(tmp_path: Path) -> None:
    state_path = tmp_path / "empty.json"
    state_path.write_text("", encoding="utf-8")
    c = load_counter(state_path)
    assert c.counters == {}


def test_load_malformed_json_returns_fresh(tmp_path: Path) -> None:
    state_path = tmp_path / "bad.json"
    state_path.write_text("{not json", encoding="utf-8")
    c = load_counter(state_path)
    assert c.counters == {}


def test_load_wrong_root_type_returns_fresh(tmp_path: Path) -> None:
    state_path = tmp_path / "list.json"
    state_path.write_text("[1, 2, 3]", encoding="utf-8")
    c = load_counter(state_path)
    assert c.counters == {}


def test_save_creates_parent_dir(tmp_path: Path) -> None:
    state_path = tmp_path / "nested" / "deep" / "loop-counter.json"
    c = new_counter("s")
    save_counter(c, state_path)
    assert state_path.exists()


def test_save_leaves_no_tmpfile(tmp_path: Path) -> None:
    state_path = tmp_path / "loop-counter.json"
    c = new_counter("s")
    save_counter(c, state_path)
    leftovers = list(tmp_path.glob("*.tmp"))
    assert leftovers == [], f"tmpfile leak: {leftovers}"


def test_save_overwrites_previous(tmp_path: Path) -> None:
    state_path = tmp_path / "loop-counter.json"
    c1 = new_counter("s")
    increment(c1, LoopType.FILE_EDIT, "a.py")
    save_counter(c1, state_path)
    c2 = new_counter("s")
    increment(c2, LoopType.FILE_EDIT, "b.py")
    save_counter(c2, state_path)
    loaded = load_counter(state_path)
    assert get_count(loaded, LoopType.FILE_EDIT, "a.py") == 0
    assert get_count(loaded, LoopType.FILE_EDIT, "b.py") == 1


def test_save_atomic_no_partial_read(tmp_path: Path) -> None:
    """Concurrent saves never leave the canonical file unreadable.

    Drives a writer thread that saves N times; the reader thread re-loads
    in a tight loop. Every load must succeed (no exception, valid
    LoopCounter); the final loaded counter must match one of the saves.
    """
    state_path = tmp_path / "loop-counter.json"
    save_counter(new_counter("s"), state_path)  # seed

    failures: list[Exception] = []
    write_count = 50

    def writer() -> None:
        for i in range(write_count):
            c = new_counter("s")
            increment(c, LoopType.FILE_EDIT, f"file-{i}.py")
            save_counter(c, state_path)

    def reader() -> None:
        for _ in range(write_count * 2):
            try:
                load_counter(state_path)
            except Exception as e:
                failures.append(e)

    t1 = threading.Thread(target=writer)
    t2 = threading.Thread(target=reader)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert failures == [], f"reader saw partial writes: {failures}"
    final = load_counter(state_path)
    assert final.session_id == "s"  # something landed; canonical file readable


def test_save_serializes_sorted_keys(tmp_path: Path) -> None:
    state_path = tmp_path / "loop-counter.json"
    c = new_counter("s")
    increment(c, LoopType.FILE_EDIT, "z.py")
    increment(c, LoopType.FILE_EDIT, "a.py")
    save_counter(c, state_path)
    raw = json.loads(state_path.read_text(encoding="utf-8"))
    keys = list(raw["counters"].keys())
    assert keys == sorted(keys), "keys must be deterministically ordered for diff-friendliness"
