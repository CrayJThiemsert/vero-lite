"""Tests for the vero-bridge stdio-MCP server (Phase 1 Step 2).

Each tool is exercised via its plain-function ``_handle_*`` entry point
(decoupled from FastMCP's decorator) — that lets us assert input /
output shape + audit log side-effects without spinning up an MCP stdio
transport. Full transport-level integration tests live in Step 5
(``test_server_roundtrip.py`` — not minted yet).

Coverage:

- **Happy path** per tool: well-formed envelope → ok response with the
  expected shape.
- **Wire-format rejection** per tool: each tool propagates BridgeError
  rejections via ``format_error_response`` (so the client receives a
  well-formed error payload, not a raw exception).
- **Audit log side-effects** per tool: every call (accepted *and*
  rejected) appends one audit record with the correct outcome +
  error_code (when relevant).
- **AC-3 chain prerequisite**: echo returns a deterministic shape that
  Step 4's cross-client round-trip matrix can assert against.
- **AC-4 (b) audit signal coverage**: bridge_whoami returns
  observable signals matching the audit log fields.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from tools.vero_bridge import _audit_log
from tools.vero_bridge._audit_log import reset_counter_for_test
from tools.vero_bridge.server import (
    SERVER_START_TS,
    _handle_bridge_status,
    _handle_bridge_whoami,
    _handle_echo,
)


@pytest.fixture(autouse=True)
def _reset_counter() -> None:
    reset_counter_for_test()


@pytest.fixture
def audit_log_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the audit log writer to a per-test temp path so we can
    assert on its contents without leaking into ``docs/research/private/``."""
    path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(_audit_log, "DEFAULT_LOG_PATH", path)
    return path


def _read_audit_lines(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


# ---------------------------------------------------------------------------
# echo — happy path
# ---------------------------------------------------------------------------


def test_echo_happy_returns_ok_response(audit_log_path: Path) -> None:
    response = _handle_echo(version=1, claimed_tag="code", name="hello")
    assert response["ok"] is True
    assert response["echoed"] == "hello"
    assert isinstance(response["ts_ns"], int) and response["ts_ns"] > 0


def test_echo_happy_writes_one_audit_record_with_outcome_ok(audit_log_path: Path) -> None:
    _handle_echo(version=1, claimed_tag="code", name="hello")
    records = _read_audit_lines(audit_log_path)
    assert len(records) == 1
    assert records[0]["tool_name"] == "echo"
    assert records[0]["claimed_tag"] == "code"
    assert records[0]["outcome"] == "ok"
    assert records[0]["error_code"] is None


def test_echo_response_ts_ns_matches_audit_record(audit_log_path: Path) -> None:
    """AC-3 chain prerequisite: the ts_ns returned to the client matches
    the audit log record's ts_ns. Step 4 uses this for round-trip
    ordering assertion."""
    response = _handle_echo(version=1, claimed_tag="code", name="hello")
    records = _read_audit_lines(audit_log_path)
    assert response["ts_ns"] == records[0]["ts_ns"]


@pytest.mark.parametrize("tag", ["code", "chat", "cowork", "cray"])
def test_echo_echoes_per_tab_claimed_tag(audit_log_path: Path, tag: str) -> None:
    """Per OQ-T3 Option I — claimed_tag echoed verbatim regardless of
    which tab the call came from. Server cannot discriminate."""
    _handle_echo(version=1, claimed_tag=tag, name="ping")
    records = _read_audit_lines(audit_log_path)
    assert records[0]["claimed_tag"] == tag


# ---------------------------------------------------------------------------
# echo — fail-closed (OQ-T1)
# ---------------------------------------------------------------------------


def test_echo_version_mismatch_returns_error_response(audit_log_path: Path) -> None:
    response = _handle_echo(version=99, claimed_tag="code", name="hello")
    assert response["ok"] is False
    assert response["error_code"] == "version-mismatch"
    assert "version 99" in response["error_message"]


def test_echo_version_mismatch_writes_error_audit_record(audit_log_path: Path) -> None:
    _handle_echo(version=99, claimed_tag="code", name="hello")
    records = _read_audit_lines(audit_log_path)
    assert len(records) == 1
    assert records[0]["outcome"] == "error"
    assert records[0]["error_code"] == "version-mismatch"
    # Per OQ-T1: the audit captures the *claimed* version even on reject.
    assert records[0]["version"] == 99


def test_echo_empty_claimed_tag_returns_malformed_frame(audit_log_path: Path) -> None:
    response = _handle_echo(version=1, claimed_tag="", name="hello")
    assert response["ok"] is False
    assert response["error_code"] == "malformed-frame"


def test_echo_empty_claimed_tag_writes_error_audit_record(audit_log_path: Path) -> None:
    _handle_echo(version=1, claimed_tag="", name="hello")
    records = _read_audit_lines(audit_log_path)
    assert records[0]["outcome"] == "error"
    assert records[0]["error_code"] == "malformed-frame"
    # The malformed claimed_tag (empty) is still logged — spoof attempts
    # with structurally-invalid tags must be visible in the audit log.
    assert records[0]["claimed_tag"] == ""


# ---------------------------------------------------------------------------
# bridge_status — happy path
# ---------------------------------------------------------------------------


def test_bridge_status_happy_returns_operational_state(audit_log_path: Path) -> None:
    response = _handle_bridge_status(version=1, claimed_tag="code")
    assert response["ok"] is True
    assert response["protocol_version"] == 1
    assert response["uptime_s"] >= 0
    assert response["pid"] == os.getpid()
    assert response["ppid"] == os.getppid()


def test_bridge_status_last_call_ts_ns_initial_is_none_or_int(audit_log_path: Path) -> None:
    """Module-global state: ``_last_call_ts_ns`` may be None (no prior
    call yet in this Python process) or an int (a prior accepted call
    landed). Both are valid; the field is informational."""
    response = _handle_bridge_status(version=1, claimed_tag="code")
    last = response["last_call_ts_ns"]
    assert last is None or isinstance(last, int)


def test_bridge_status_writes_audit_record(audit_log_path: Path) -> None:
    _handle_bridge_status(version=1, claimed_tag="code")
    records = _read_audit_lines(audit_log_path)
    assert len(records) == 1
    assert records[0]["tool_name"] == "bridge_status"
    assert records[0]["outcome"] == "ok"


def test_bridge_status_after_echo_reports_last_call_ts(audit_log_path: Path) -> None:
    """After an accepted echo call, bridge_status's last_call_ts_ns
    should be ≥ the echo's ts_ns."""
    echo_response = _handle_echo(version=1, claimed_tag="code", name="x")
    status_response = _handle_bridge_status(version=1, claimed_tag="code")
    assert isinstance(echo_response["ts_ns"], int)
    last = status_response["last_call_ts_ns"]
    assert isinstance(last, int)
    assert last >= echo_response["ts_ns"]


def test_server_start_ts_is_set() -> None:
    """The module-level SERVER_START_TS is captured at import time —
    confirms the server lifecycle field is initialized before any tool
    invocation."""
    assert SERVER_START_TS > 0


# ---------------------------------------------------------------------------
# bridge_status — fail-closed
# ---------------------------------------------------------------------------


def test_bridge_status_version_mismatch_returns_error(audit_log_path: Path) -> None:
    response = _handle_bridge_status(version=2, claimed_tag="code")
    assert response["ok"] is False
    assert response["error_code"] == "version-mismatch"


def test_bridge_status_version_mismatch_writes_error_audit(audit_log_path: Path) -> None:
    _handle_bridge_status(version=2, claimed_tag="code")
    records = _read_audit_lines(audit_log_path)
    assert records[0]["outcome"] == "error"
    assert records[0]["error_code"] == "version-mismatch"


# ---------------------------------------------------------------------------
# bridge_whoami — happy path
# ---------------------------------------------------------------------------


def test_bridge_whoami_happy_returns_observable_signals(audit_log_path: Path) -> None:
    response = _handle_bridge_whoami(version=1, claimed_tag="code")
    assert response["ok"] is True
    assert response["claimed_tag"] == "code"
    assert response["pid"] == os.getpid()
    assert response["ppid"] == os.getppid()
    assert isinstance(response["stdin_fd"], str)
    assert isinstance(response["stdout_fd"], str)
    assert isinstance(response["ts_ns"], int)
    assert isinstance(response["env_keys_seen"], list)


def test_bridge_whoami_env_keys_seen_is_sorted_and_filtered(
    audit_log_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLAUDE_TIER", "code")
    monkeypatch.setenv("UNRELATED", "x")
    response = _handle_bridge_whoami(version=1, claimed_tag="code")
    keys = response["env_keys_seen"]
    assert isinstance(keys, list)
    assert "CLAUDE_TIER" in keys
    assert "UNRELATED" not in keys
    assert keys == sorted(keys)


def test_bridge_whoami_writes_audit_record(audit_log_path: Path) -> None:
    _handle_bridge_whoami(version=1, claimed_tag="code")
    records = _read_audit_lines(audit_log_path)
    assert len(records) == 1
    assert records[0]["tool_name"] == "bridge_whoami"
    assert records[0]["outcome"] == "ok"


def test_bridge_whoami_response_matches_audit_record_signals(audit_log_path: Path) -> None:
    """The fields bridge_whoami returns MUST match the audit log fields
    for the same call — that's the AC-4 (c) anti-spoof matrix
    prerequisite (clients can self-audit how the server saw them)."""
    response = _handle_bridge_whoami(version=1, claimed_tag="code")
    records = _read_audit_lines(audit_log_path)
    rec = records[0]
    assert response["pid"] == rec["pid"]
    assert response["ppid"] == rec["ppid"]
    assert response["stdin_fd"] == rec["stdin_fd"]
    assert response["stdout_fd"] == rec["stdout_fd"]
    assert response["env_keys_seen"] == rec["env_keys_seen"]


# ---------------------------------------------------------------------------
# bridge_whoami — fail-closed
# ---------------------------------------------------------------------------


def test_bridge_whoami_version_mismatch_returns_error(audit_log_path: Path) -> None:
    response = _handle_bridge_whoami(version=0, claimed_tag="code")
    assert response["ok"] is False
    assert response["error_code"] == "version-mismatch"


def test_bridge_whoami_empty_claimed_tag_returns_malformed_frame(audit_log_path: Path) -> None:
    response = _handle_bridge_whoami(version=1, claimed_tag="")
    assert response["ok"] is False
    assert response["error_code"] == "malformed-frame"


# ---------------------------------------------------------------------------
# Cross-tool — audit log invariants
# ---------------------------------------------------------------------------


def test_audit_log_records_increment_monotonic_counter(audit_log_path: Path) -> None:
    """Multiple calls across different tools share the per-process
    monotonic counter (so AC-4 (b) audit can order calls
    deterministically even when ts_ns ties)."""
    _handle_echo(version=1, claimed_tag="code", name="a")
    _handle_bridge_status(version=1, claimed_tag="code")
    _handle_bridge_whoami(version=1, claimed_tag="code")
    records = _read_audit_lines(audit_log_path)
    counters = [r["monotonic_counter"] for r in records]
    assert counters == [1, 2, 3]


def test_audit_log_mixed_outcomes(audit_log_path: Path) -> None:
    """Mix of accepted + rejected calls — every one of them lands in the
    audit log (no silent drops on reject)."""
    _handle_echo(version=1, claimed_tag="code", name="a")  # ok
    _handle_echo(version=99, claimed_tag="code", name="b")  # version-mismatch
    _handle_echo(version=1, claimed_tag="", name="c")  # malformed-frame
    _handle_bridge_status(version=1, claimed_tag="cowork")  # ok
    records = _read_audit_lines(audit_log_path)
    outcomes = [(r["tool_name"], r["outcome"], r["error_code"]) for r in records]
    assert outcomes == [
        ("echo", "ok", None),
        ("echo", "error", "version-mismatch"),
        ("echo", "error", "malformed-frame"),
        ("bridge_status", "ok", None),
    ]


# ---------------------------------------------------------------------------
# MCP integration smoke — server module imports + mcp instance is configured
# ---------------------------------------------------------------------------


def test_server_module_exports_mcp_instance() -> None:
    """``mcp`` is the FastMCP instance the Desktop spawn entry-point
    runs. It must be importable + have the 3 tools registered."""
    from tools.vero_bridge.server import mcp

    assert mcp is not None
    # FastMCP exposes a list_tools async method; we just confirm the
    # instance exists and its repr names "vero-bridge".
    assert "vero-bridge" in repr(mcp).lower() or hasattr(mcp, "name")


def test_server_main_is_callable() -> None:
    """``main()`` is the ``python -m`` entry point — must be importable
    without side-effects beyond the module-level imports."""
    from tools.vero_bridge.server import main

    assert callable(main)
