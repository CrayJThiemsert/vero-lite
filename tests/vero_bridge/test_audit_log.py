"""Tests for the vero-bridge audit log writer (AC-4 (b))."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from tools.vero_bridge._audit_log import (
    _OBSERVABLE_ENV_PREFIXES,
    DEFAULT_LOG_PATH,
    build_record,
    log_call,
    reset_counter_for_test,
    write_record,
)


@pytest.fixture(autouse=True)
def _reset_counter() -> None:
    """Each test starts with monotonic_counter == 1 so assertions are
    deterministic across runs."""
    reset_counter_for_test()


@pytest.fixture
def log_path(tmp_path: Path) -> Path:
    return tmp_path / "audit.jsonl"


# ---------------------------------------------------------------------------
# build_record — record shape
# ---------------------------------------------------------------------------


def test_record_carries_all_required_fields() -> None:
    record = build_record(
        tool_name="echo",
        claimed_tag="code",
        version=1,
        outcome="ok",
    )
    # AC-4 (b) required fields
    required = {
        "ts_ns",
        "ts_iso",
        "monotonic_counter",
        "tool_name",
        "claimed_tag",
        "version",
        "outcome",
        "error_code",
        "pid",
        "ppid",
        "stdin_fd",
        "stdout_fd",
        "env_keys_seen",
    }
    assert required.issubset(record.keys())


def test_monotonic_counter_increments_per_call() -> None:
    a = build_record(tool_name="echo", claimed_tag="code", version=1, outcome="ok")
    b = build_record(tool_name="echo", claimed_tag="code", version=1, outcome="ok")
    c = build_record(tool_name="echo", claimed_tag="code", version=1, outcome="ok")
    assert (a["monotonic_counter"], b["monotonic_counter"], c["monotonic_counter"]) == (
        1,
        2,
        3,
    )


def test_record_includes_observable_signals() -> None:
    record = build_record(tool_name="echo", claimed_tag="code", version=1, outcome="ok")
    assert record["pid"] == os.getpid()
    assert record["ppid"] == os.getppid()
    # On Linux /proc is available; on other platforms a sentinel.
    assert isinstance(record["stdin_fd"], str)
    assert isinstance(record["stdout_fd"], str)
    assert isinstance(record["env_keys_seen"], list)


def test_env_keys_seen_is_filtered_by_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_TIER", "code")
    monkeypatch.setenv("MCP_SOMETHING", "x")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setenv("UNRELATED_VAR", "x")
    record = build_record(tool_name="echo", claimed_tag="code", version=1, outcome="ok")
    keys = set(record["env_keys_seen"])
    assert "CLAUDE_TIER" in keys
    assert "MCP_SOMETHING" in keys
    assert "ANTHROPIC_API_KEY" in keys
    assert "UNRELATED_VAR" not in keys


def test_env_keys_seen_is_sorted() -> None:
    record = build_record(tool_name="echo", claimed_tag="code", version=1, outcome="ok")
    assert record["env_keys_seen"] == sorted(record["env_keys_seen"])


def test_observable_env_prefixes_match_probe_filter() -> None:
    """Audit log + bridge_whoami should report the same env-key set
    (so cross-referencing the two outputs is meaningful)."""
    assert _OBSERVABLE_ENV_PREFIXES == ("CLAUDE_", "MCP_", "ANTHROPIC_")


# ---------------------------------------------------------------------------
# claimed_tag + version safe rendering (audit-log-on-reject path)
# ---------------------------------------------------------------------------


def test_claimed_tag_string_kept_verbatim() -> None:
    record = build_record(tool_name="echo", claimed_tag="code", version=1, outcome="ok")
    assert record["claimed_tag"] == "code"


@pytest.mark.parametrize(
    "bad,expected_substring",
    [
        (None, "None"),
        (42, "42"),
        ([], "[]"),
        ({"x": 1}, "{"),
        (b"code", "b'"),
    ],
)
def test_claimed_tag_non_string_is_repr(bad: object, expected_substring: str) -> None:
    """Malformed claimed_tag must still be loggable — render via repr
    rather than crash. Spoof attempts with malformed tags must show up
    in the audit log."""
    record = build_record(tool_name="echo", claimed_tag=bad, version=1, outcome="error")
    assert isinstance(record["claimed_tag"], str)
    assert expected_substring in record["claimed_tag"]


def test_version_bool_rendered_with_label() -> None:
    """bool sneaks through int isinstance checks in Python — the audit
    log labels it so reviewers spot the type confusion."""
    record = build_record(tool_name="echo", claimed_tag="code", version=True, outcome="error")
    assert record["version"] == "<bool:True>"


def test_version_int_kept_verbatim() -> None:
    record = build_record(tool_name="echo", claimed_tag="code", version=1, outcome="ok")
    assert record["version"] == 1


@pytest.mark.parametrize("bad", [object(), [1, 2], {"v": 1}])
def test_version_non_primitive_is_repr(bad: object) -> None:
    record = build_record(tool_name="echo", claimed_tag="code", version=bad, outcome="error")
    assert isinstance(record["version"], str)


# ---------------------------------------------------------------------------
# write_record — file I/O
# ---------------------------------------------------------------------------


def test_write_record_appends_one_line(log_path: Path) -> None:
    record = build_record(tool_name="echo", claimed_tag="code", version=1, outcome="ok")
    write_record(record, log_path=log_path)
    assert log_path.exists()
    content = log_path.read_text(encoding="utf-8")
    assert content.endswith("\n")
    assert content.count("\n") == 1


def test_write_record_creates_parent_dir(tmp_path: Path) -> None:
    nested = tmp_path / "deep" / "deeper" / "audit.jsonl"
    record = build_record(tool_name="echo", claimed_tag="code", version=1, outcome="ok")
    write_record(record, log_path=nested)
    assert nested.exists()


def test_write_record_multiple_calls_append(log_path: Path) -> None:
    for tag in ["code", "chat", "cowork"]:
        record = build_record(tool_name="echo", claimed_tag=tag, version=1, outcome="ok")
        write_record(record, log_path=log_path)
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    parsed = [json.loads(line) for line in lines]
    assert [r["claimed_tag"] for r in parsed] == ["code", "chat", "cowork"]
    # Counter monotonically increases across writes from the same process.
    assert [r["monotonic_counter"] for r in parsed] == [1, 2, 3]


def test_write_record_produces_valid_jsonl(log_path: Path) -> None:
    """Each line MUST parse as standalone JSON — the audit log is a
    JSONL stream, not a JSON array."""
    record = build_record(tool_name="echo", claimed_tag="code", version=1, outcome="ok")
    write_record(record, log_path=log_path)
    line = log_path.read_text(encoding="utf-8").strip()
    parsed = json.loads(line)  # raises if invalid
    assert parsed["tool_name"] == "echo"


def test_write_record_keys_are_sorted(log_path: Path) -> None:
    """``json.dumps(sort_keys=True)`` produces stable line ordering —
    helpful for diff-based audit-log review + AC-6 evidence comparison."""
    record = build_record(tool_name="echo", claimed_tag="code", version=1, outcome="ok")
    write_record(record, log_path=log_path)
    line = log_path.read_text(encoding="utf-8").strip()
    # First few keys should appear in alphabetical order.
    assert line.find('"claimed_tag"') < line.find('"env_keys_seen"')
    assert line.find('"env_keys_seen"') < line.find('"monotonic_counter"')


# ---------------------------------------------------------------------------
# log_call — convenience entry point
# ---------------------------------------------------------------------------


def test_log_call_writes_and_returns_record(log_path: Path) -> None:
    record = log_call(
        tool_name="echo",
        claimed_tag="code",
        version=1,
        outcome="ok",
        log_path=log_path,
    )
    assert log_path.exists()
    on_disk = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert on_disk["tool_name"] == "echo"
    assert on_disk["monotonic_counter"] == record["monotonic_counter"]


def test_log_call_error_outcome_carries_error_code(log_path: Path) -> None:
    record = log_call(
        tool_name="echo",
        claimed_tag="code",
        version=99,
        outcome="error",
        error_code="version-mismatch",
        log_path=log_path,
    )
    assert record["outcome"] == "error"
    assert record["error_code"] == "version-mismatch"
    on_disk = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert on_disk["error_code"] == "version-mismatch"


def test_log_call_swallows_io_error_via_audit_io_error_field(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An audit-log I/O failure MUST NOT take down the call path. It
    must surface in the returned record so test + server stderr see it."""
    # Point the log at a path whose parent is a *file*, not a directory —
    # mkdir(parents=True) will raise NotADirectoryError on the open().
    blocker = tmp_path / "blocker"
    blocker.write_text("not a dir")
    bad_path = blocker / "audit.jsonl"
    record = log_call(
        tool_name="echo",
        claimed_tag="code",
        version=1,
        outcome="ok",
        log_path=bad_path,
    )
    assert "audit_io_error" in record
    # The exact OSError subclass varies by platform / Python version
    # (FileExistsError on Linux when mkdir hits a file; NotADirectoryError
    # when open hits a non-dir parent; FileNotFoundError on Windows). All
    # are acceptable — the contract is "some OSError surfaces in the
    # returned record".
    assert record["audit_io_error"] in {
        "FileExistsError",
        "NotADirectoryError",
        "FileNotFoundError",
        "PermissionError",
    }


# ---------------------------------------------------------------------------
# Sanity: default log path
# ---------------------------------------------------------------------------


def test_default_log_path_under_research_private() -> None:
    """Phase 1 audit log lives under docs/research/private/ which is
    gitignored — see AC-4 (b)."""
    assert DEFAULT_LOG_PATH.parts[:3] == ("docs", "research", "private")
    assert DEFAULT_LOG_PATH.suffix == ".jsonl"


# ---------------------------------------------------------------------------
# JSON serializability of the full record
# ---------------------------------------------------------------------------


def test_record_is_json_serializable_with_malformed_inputs() -> None:
    """A record built from any caller input — including malformed
    spoof attempts — MUST be JSON-serializable. If json.dumps raises,
    the audit log silently drops calls and the AC-4 (c) anti-spoof
    matrix becomes blind."""
    record = build_record(
        tool_name="echo",
        claimed_tag=b"binary",  # malformed
        version=[1, 2, 3],  # malformed
        outcome="error",
        error_code="malformed-frame",
    )
    # Must not raise.
    serialized = json.dumps(record, sort_keys=True)
    assert isinstance(serialized, str)
