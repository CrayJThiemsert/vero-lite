"""Step 5 — adversarial cross-tab anti-spoof matrix (AC-4 (c)) + AC-8
capability-by-tool-design negative test + AC-4 (a) git-over-transport
negative + AC-5 boundary/encoding gaps.

Companion to ``test_server.py`` (happy / fail-closed / audit side-effects).
This file adds the *adversarial* and *negative* dimensions of the AC-5
case-coverage matrix:

- **Adversarial spoof (AC-4 (c), unit level).** The server accepts ANY
  ``claimed_tag`` (Option I — claimed_tag is audit-only, never
  authorization), echoes it verbatim, and the observable signals
  (pid/ppid/fd) are *independent* of ``claimed_tag``. The audit log
  captures the spoofed tag alongside the real signals (the discrepancy).
  The cross-*instance* discrimination (Chat instance A vs Code+Cowork
  instance B) requires multiple Desktop-spawned processes and is proven
  by the **live** evidence matrix
  (``docs/research/private/2026-05-29-vero-bridge-step5-spoof-matrix.md``),
  not unit tests — a single pytest process cannot reproduce the tab-group
  routing.
- **AC-8 negative (capability-by-tool-design).** The registered MCP tool
  surface is exactly the safe-for-all set (the §2.1-§2.3 introspection
  tools plus §2.4 ``read_repo_path``). Every not-on-bridge operation
  (commit_to_main, write_file, run_shell, …) is refused at the FastMCP
  framework layer with ``ToolError: Unknown tool`` — the call never
  reaches a handler, so there is no tier-bypass surface.

  **FINDING-3 (AC-8 contract accuracy).** The capability inventory §4
  originally described the negative result as a server-emitted
  ``{"ok": False, "error_code": "tool-not-found", ...}`` JSON body. The
  decorator-based FastMCP architecture has no generic dispatcher to emit
  that body — an unregistered tool name is rejected by the framework with
  a ``ToolError`` *before* any server code runs. That is a strictly
  stronger boundary (nothing to bypass). ``ErrorCode.TOOL_NOT_FOUND``
  remains reserved in the schema for a future generic-dispatcher surface.
  Inventory §4 amended to match in this PR.
- **AC-4 (a) git-over-transport negative.** git-flavored op names
  (``git_commit`` / ``git_push`` / ``commit_to_main``) are not-on-bridge,
  so a transport request for a git operation is refused at the framework
  layer — it never reaches the ADR-013 D2 deny hook because it is never
  dispatched. The standalone G5 bypass-immune suite
  (``tests/handoffs/test_pretooluse_git_deny.py``) stays green
  independently (full-suite re-run).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from tools.vero_bridge import _audit_log
from tools.vero_bridge._audit_log import reset_counter_for_test
from tools.vero_bridge.server import _handle_bridge_whoami, _handle_echo, mcp

#: The safe-for-all tools currently registered — a growing subset of the
#: capability inventory §2 planned surface (§2.1-§2.3 introspection +
#: §2.4 ``read_repo_path`` + §2.5 ``validate_handoff_frontmatter``, added in
#: Step 2b). Any drift here is a capability-surface change that MUST go
#: through the inventory's "Rule" gate (§3) — this test is the tripwire.
SAFE_FOR_ALL_TOOLS = {
    "echo",
    "bridge_status",
    "bridge_whoami",
    "read_repo_path",
    "validate_handoff_frontmatter",
}

#: Representative not-on-bridge operations per the capability inventory
#: §3 exclusion list. Each MUST be unregistered (calling it raises
#: ToolError "Unknown tool"). git-flavored names double as the AC-4 (a)
#: git-over-transport negative.
NOT_ON_BRIDGE_OPS = [
    "commit_to_main",
    "git_commit",
    "git_push",
    "dispatch_bind_on_cray",
    "write_file",
    "run_shell",
    "set_status",
    "modify_settings",
    "kill_server",
    "restart_server",
]


@pytest.fixture(autouse=True)
def _reset_counter() -> None:
    reset_counter_for_test()


@pytest.fixture
def audit_log_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the audit log writer to a per-test temp path (never touch
    the real ``docs/research/private/`` log)."""
    path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(_audit_log, "DEFAULT_LOG_PATH", path)
    return path


def _read_audit_lines(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


# ---------------------------------------------------------------------------
# AC-4 (c) — adversarial spoof matrix (unit level)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "claimed_tag",
    ["code", "chat", "cowork", "cray", "code ", "../../etc", "definitely-not-a-tab"],
)
def test_whoami_accepts_any_claimed_tag_no_rejection(
    audit_log_path: Path, claimed_tag: str
) -> None:
    """Option I: the server NEVER rejects a call on the basis of which
    identity ``claimed_tag`` asserts — spoofing is always accepted (and
    audited). claimed_tag is echoed verbatim."""
    response = _handle_bridge_whoami(version=1, claimed_tag=claimed_tag)
    assert response["ok"] is True
    assert response["claimed_tag"] == claimed_tag


def test_whoami_observable_signals_independent_of_claimed_tag(audit_log_path: Path) -> None:
    """The anti-spoof core: the observable fingerprint (pid/ppid/fd) is
    produced from the real process and does NOT vary with ``claimed_tag``.
    A caller cannot forge a different observable identity by changing the
    tag it claims."""
    honest = _handle_bridge_whoami(version=1, claimed_tag="code")
    spoof_chat = _handle_bridge_whoami(version=1, claimed_tag="chat")
    spoof_cowork = _handle_bridge_whoami(version=1, claimed_tag="cowork")

    for spoof in (spoof_chat, spoof_cowork):
        assert spoof["pid"] == honest["pid"]
        assert spoof["ppid"] == honest["ppid"]
        assert spoof["stdin_fd"] == honest["stdin_fd"]
        assert spoof["stdout_fd"] == honest["stdout_fd"]
    # Only the (spoofable, audit-only) claimed_tag differs.
    assert {honest["claimed_tag"], spoof_chat["claimed_tag"], spoof_cowork["claimed_tag"]} == {
        "code",
        "chat",
        "cowork",
    }


def test_whoami_audit_captures_spoofed_tag_with_real_signals(audit_log_path: Path) -> None:
    """AC-4 (c) discrepancy capture: a call claiming ``chat`` from this
    (non-chat) process logs ``claimed_tag == "chat"`` (the spoof, verbatim)
    alongside the REAL pid (``os.getpid()``). The audit record holds both
    sides of the discrepancy."""
    _handle_bridge_whoami(version=1, claimed_tag="chat")
    records = _read_audit_lines(audit_log_path)
    assert len(records) == 1
    rec = records[0]
    assert rec["claimed_tag"] == "chat"  # spoofed identity, logged verbatim
    assert rec["pid"] == os.getpid()  # real, non-spoofable signal
    assert rec["outcome"] == "ok"  # accepted, not rejected


def test_echo_accepts_spoofed_tag_too(audit_log_path: Path) -> None:
    """Spoofing is not whoami-specific — every safe tool echoes/logs the
    claimed_tag verbatim regardless of identity."""
    response = _handle_echo(version=1, claimed_tag="cowork", name="spoof-probe")
    assert response["ok"] is True
    records = _read_audit_lines(audit_log_path)
    assert records[0]["claimed_tag"] == "cowork"
    assert records[0]["outcome"] == "ok"


# ---------------------------------------------------------------------------
# AC-8 — capability-by-tool-design negative (framework-level)
# ---------------------------------------------------------------------------


async def test_registered_tool_surface_is_exactly_safe_for_all() -> None:
    """The exposed MCP tool surface is EXACTLY the safe-for-all set
    (capability inventory §2 — introspection §2.1-§2.3 + ``read_repo_path``
    §2.4). A new tool appearing here without an inventory entry is a
    capability-surface regression."""
    tools = await mcp.list_tools()
    assert {t.name for t in tools} == SAFE_FOR_ALL_TOOLS


@pytest.mark.parametrize("op", NOT_ON_BRIDGE_OPS)
async def test_not_on_bridge_op_is_refused_at_framework_layer(op: str) -> None:
    """AC-8 negative + AC-4 (a) git-over-transport negative: every
    not-on-bridge operation is unregistered, so invoking it raises a
    framework ``ToolError`` ("Unknown tool") BEFORE any handler runs —
    there is no dispatch path, hence no tier-bypass surface.

    (FINDING-3: this is the actual enforcement — a framework rejection,
    not a server-emitted ``tool-not-found`` JSON body. Inventory §4
    amended to match.)"""
    with pytest.raises(ToolError) as excinfo:
        await mcp.call_tool(op, {"version": 1, "claimed_tag": "code"})
    assert "Unknown tool" in str(excinfo.value)


async def test_git_op_never_reaches_a_handler() -> None:
    """AC-4 (a): a git-over-transport request is refused at the framework
    layer (unregistered tool) — it never reaches the ADR-013 D2 deny hook
    because it is never dispatched to any implementation. The deny hook's
    own bypass-immune matrix (tests/handoffs/test_pretooluse_git_deny.py)
    stays green independently."""
    with pytest.raises(ToolError):
        await mcp.call_tool("git_commit", {"version": 1, "claimed_tag": "code"})


# ---------------------------------------------------------------------------
# AC-5 — boundary / encoding gaps
# ---------------------------------------------------------------------------


def test_echo_long_name_roundtrips(audit_log_path: Path) -> None:
    """Boundary: a large payload echoes back byte-for-byte."""
    big = "x" * 10_000
    response = _handle_echo(version=1, claimed_tag="code", name=big)
    assert response["echoed"] == big


def test_echo_unicode_name_and_tag_roundtrip(audit_log_path: Path) -> None:
    """Encoding: non-ASCII name + claimed_tag survive round-trip + audit."""
    name = "ออทำงาน-🛰️-ünïcode"
    tag = "cowork-ไทย"
    response = _handle_echo(version=1, claimed_tag=tag, name=name)
    assert response["echoed"] == name
    records = _read_audit_lines(audit_log_path)
    assert records[0]["claimed_tag"] == tag


def test_echo_empty_name_is_accepted(audit_log_path: Path) -> None:
    """Boundary: an empty payload value (``name=""``) is valid — only an
    empty *claimed_tag* (envelope field) is malformed, not an empty
    payload value."""
    response = _handle_echo(version=1, claimed_tag="code", name="")
    assert response["ok"] is True
    assert response["echoed"] == ""


def test_version_bool_is_rejected_malformed(audit_log_path: Path) -> None:
    """Boundary: ``version=True`` (bool ⊆ int in Python) is rejected as
    malformed-frame — booleans are categorically not version numbers."""
    response = _handle_echo(version=True, claimed_tag="code", name="x")
    assert response["ok"] is False
    assert response["error_code"] == "malformed-frame"
