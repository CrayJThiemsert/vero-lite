"""Contract tests for the Chat-tab bridge client (Phase 1 Step 3a).

Step 3a ships **no** ``tools/vero_bridge/clients/`` module: per the
ratified design (wire-format §7.4), Chat (and Cowork) invoke
``mcp__vero-bridge__*`` directly from their deferred-tool list — a raw
invocation, not a Python wrapper. The deliverable is therefore (1) the
documented invocation pattern in
``docs/conventions/vero-bridge-wire-format.md`` §7 and (2) the doc-rot
guard in this file.

This module is the doc-rot guard. It asserts:

- **Surface parity** — the documented §7.2 invocation table matches the
  live FastMCP-registered tool surface (``mcp.list_tools()``). A
  ``server.py`` signature change (rename/add/drop a kwarg) turns these
  red, forcing the doc to be updated in the same PR.
- **`message_type` is server-side** — no documented tool exposes
  ``message_type`` (or a raw ``payload``) as a client kwarg (§7.3).
- **Doc tie** — every documented tool + kwarg name actually appears in
  the wire-format doc §7, so updating the code/test without updating
  the prose also turns red.
- **Fake-transport round-trip** — invoking the registered tool the way
  a Chat tab would (``claimed_tag="chat"``) produces the documented
  response shape and audit behaviour. The audit log is redirected to a
  temp path so these tests never touch the real
  ``docs/research/private/`` baseline.

Live cross-client wire parity (byte-for-byte Chat vs Cowork) and the
captured AC-3/AC-6/AC-7 evidence are owned by Steps 3b + 4; this file
only proves the documented Chat surface matches the server.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from tools.vero_bridge import _audit_log
from tools.vero_bridge._audit_log import reset_counter_for_test
from tools.vero_bridge.server import (
    bridge_status,
    bridge_whoami,
    echo,
    mcp,
)

#: The Chat tab's self-asserted identity (audit-only per OQ-T3 Option I).
CHAT_CLAIMED_TAG = "chat"

#: The documented Phase 1 invocation surface — the machine-checkable
#: mirror of wire-format §7.2. Keys are the registered MCP tool names;
#: values are the *complete* set of client-supplied kwargs. If you change
#: a tool's signature in ``server.py``, update this dict AND §7.2 of
#: ``docs/conventions/vero-bridge-wire-format.md`` together.
DOCUMENTED_TOOL_CONTRACT: dict[str, set[str]] = {
    "echo": {"version", "claimed_tag", "name"},
    "bridge_status": {"version", "claimed_tag"},
    "bridge_whoami": {"version", "claimed_tag"},
    "read_repo_path": {"version", "claimed_tag", "path"},
    "validate_handoff_frontmatter": {"version", "claimed_tag", "content"},
    "lint_status": {"version", "claimed_tag"},
}

#: Envelope fields a tab MUST NOT pass as kwargs — they are supplied
#: server-side (``message_type``) or split into named kwargs
#: (``payload``). See wire-format §7.3.
SERVER_SIDE_ENVELOPE_FIELDS = ("message_type", "payload")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WIRE_FORMAT_DOC = _REPO_ROOT / "docs" / "conventions" / "vero-bridge-wire-format.md"


@pytest.fixture(autouse=True)
def _reset_counter() -> None:
    reset_counter_for_test()


@pytest.fixture
def audit_log_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the audit log writer to a per-test temp path so these
    tests never append to the real ``docs/research/private/`` baseline."""
    path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(_audit_log, "DEFAULT_LOG_PATH", path)
    return path


def _registered_surface() -> dict[str, tuple[set[str], set[str]]]:
    """Return ``{tool_name: (property_names, required_names)}`` from the
    live FastMCP tool registry — the exact surface a tab sees."""
    tools = asyncio.run(mcp.list_tools())
    surface: dict[str, tuple[set[str], set[str]]] = {}
    for tool in tools:
        schema = tool.inputSchema or {}
        props = set(schema.get("properties", {}).keys())
        required = set(schema.get("required", []))
        surface[tool.name] = (props, required)
    return surface


def _read_audit_lines(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _doc_section_7() -> str:
    """Extract the §7 'Client invocation from Chat tab' body from the
    wire-format doc (up to the §8 change log)."""
    doc = _WIRE_FORMAT_DOC.read_text(encoding="utf-8")
    start = doc.index("## 7. Client invocation from Chat tab")
    end = doc.index("## 8. Change log", start)
    return doc[start:end]


# ---------------------------------------------------------------------------
# Surface parity — documented contract matches the live registered tools
# ---------------------------------------------------------------------------


def test_documented_tools_are_all_registered() -> None:
    """Every tool named in §7.2 exists in the live FastMCP surface."""
    surface = _registered_surface()
    for name in DOCUMENTED_TOOL_CONTRACT:
        assert name in surface, f"{name} documented in §7.2 but not registered in server.py"


@pytest.mark.parametrize("tool_name", sorted(DOCUMENTED_TOOL_CONTRACT))
def test_documented_kwargs_match_registered_signature(tool_name: str) -> None:
    """The §7.2 kwarg set for each tool matches the registered input
    schema property set exactly. Doc-rot guard: renaming/adding/dropping
    a kwarg in server.py turns this red."""
    props, _required = _registered_surface()[tool_name]
    assert props == DOCUMENTED_TOOL_CONTRACT[tool_name], (
        f"{tool_name}: documented kwargs {DOCUMENTED_TOOL_CONTRACT[tool_name]} "
        f"diverge from server.py surface {props} — update §7.2 + this contract"
    )


@pytest.mark.parametrize("tool_name", sorted(DOCUMENTED_TOOL_CONTRACT))
def test_version_and_claimed_tag_required(tool_name: str) -> None:
    """Both envelope fields a tab passes are mandatory on every tool."""
    _props, required = _registered_surface()[tool_name]
    assert {"version", "claimed_tag"} <= required


@pytest.mark.parametrize("tool_name", sorted(DOCUMENTED_TOOL_CONTRACT))
def test_message_type_and_payload_not_client_kwargs(tool_name: str) -> None:
    """§7.3: ``message_type`` is supplied server-side and ``payload`` is
    split into named kwargs — neither is ever a tab-supplied kwarg."""
    props, _required = _registered_surface()[tool_name]
    for field in SERVER_SIDE_ENVELOPE_FIELDS:
        assert field not in props, f"{tool_name} must not expose {field!r} as a client kwarg"


# ---------------------------------------------------------------------------
# Doc tie — the documented contract appears in the prose
# ---------------------------------------------------------------------------


def test_documented_tools_and_kwargs_appear_in_doc_section_7() -> None:
    """Every contract tool (as its ``mcp__vero-bridge__*`` name) and every
    kwarg appears in wire-format §7. Closes the other doc-rot direction:
    updating the code/test without updating the prose turns this red."""
    section = _doc_section_7()
    for name, kwargs in DOCUMENTED_TOOL_CONTRACT.items():
        assert f"mcp__vero-bridge__{name}" in section, f"§7 omits mcp__vero-bridge__{name}"
        for kwarg in kwargs:
            assert kwarg in section, f"§7 omits the {kwarg!r} kwarg for {name}"


def test_doc_states_no_python_client_wrapper() -> None:
    """§7.4 records the ratified Raw-over-wrapper decision; assert the
    load-bearing claim (no clients/ module) is present so a future PR
    that adds a wrapper must consciously revise this section."""
    section = _doc_section_7()
    assert "tools/vero_bridge/clients/" in section
    assert "Rule of Three" in section


# ---------------------------------------------------------------------------
# Fake-transport round-trip — the documented Chat invocation works
# ---------------------------------------------------------------------------


def test_chat_echo_round_trip_matches_documented_shape(audit_log_path: Path) -> None:
    """Invoke ``echo`` the way a Chat tab would and assert the §7.2
    response shape."""
    token = "step3a-chat-contract-token"
    response = echo(version=1, claimed_tag=CHAT_CLAIMED_TAG, name=token)
    assert response == {
        "ok": True,
        "echoed": token,
        "ts_ns": response["ts_ns"],
    }
    # ts_ns is a decimal string (FINDING-2) so it survives JSON-double clients.
    assert isinstance(response["ts_ns"], str) and int(response["ts_ns"]) > 0


def test_chat_claimed_tag_logged_verbatim(audit_log_path: Path) -> None:
    """OQ-T3 Option I: the Chat tab's ``claimed_tag`` is logged verbatim
    (audit-only; never authorized against)."""
    echo(version=1, claimed_tag=CHAT_CLAIMED_TAG, name="x")
    records = _read_audit_lines(audit_log_path)
    assert len(records) == 1
    assert records[0]["claimed_tag"] == CHAT_CLAIMED_TAG
    assert records[0]["outcome"] == "ok"


def test_chat_bridge_status_round_trip(audit_log_path: Path) -> None:
    response = bridge_status(version=1, claimed_tag=CHAT_CLAIMED_TAG)
    assert response["ok"] is True
    assert response["protocol_version"] == 1
    assert set(response) == {
        "ok",
        "protocol_version",
        "uptime_s",
        "pid",
        "ppid",
        "last_call_ts_ns",
    }


def test_chat_bridge_whoami_round_trip(audit_log_path: Path) -> None:
    response = bridge_whoami(version=1, claimed_tag=CHAT_CLAIMED_TAG)
    assert response["ok"] is True
    assert response["claimed_tag"] == CHAT_CLAIMED_TAG
    assert set(response) == {
        "ok",
        "claimed_tag",
        "pid",
        "ppid",
        "stdin_fd",
        "stdout_fd",
        "ts_ns",
        "env_keys_seen",
    }


def test_chat_fail_closed_version_mismatch(audit_log_path: Path) -> None:
    """A malformed Chat call returns the §3.1 error envelope (not a raw
    exception), and the rejected call is still audit-logged."""
    response = echo(version=2, claimed_tag=CHAT_CLAIMED_TAG, name="x")
    assert response["ok"] is False
    assert response["error_code"] == "version-mismatch"
    assert set(response) == {"ok", "error_code", "error_message"}
    records = _read_audit_lines(audit_log_path)
    assert records[0]["outcome"] == "error"
    assert records[0]["error_code"] == "version-mismatch"
    assert records[0]["claimed_tag"] == CHAT_CLAIMED_TAG


# ---------------------------------------------------------------------------
# AC-7 parity prerequisite — surface is identical regardless of claimed_tag
# ---------------------------------------------------------------------------


def test_response_shape_identical_across_claimed_tags(audit_log_path: Path) -> None:
    """Foreshadows AC-7: the same logical ``echo`` call from ``chat`` vs
    ``cowork`` yields an identically-shaped response and the same echoed
    value (claimed_tag does not alter the wire surface). Full byte-for-byte
    cross-client parity + live evidence are asserted in Steps 3b + 4."""
    name = "parity-probe"
    chat_resp = echo(version=1, claimed_tag="chat", name=name)
    cowork_resp = echo(version=1, claimed_tag="cowork", name=name)
    assert set(chat_resp) == set(cowork_resp)
    assert chat_resp["echoed"] == cowork_resp["echoed"] == name
    assert chat_resp["ok"] is cowork_resp["ok"] is True
