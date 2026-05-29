"""Contract + AC-7 parity tests for the Cowork-tab bridge client (Step 3b).

Like Step 3a (Chat), Step 3b ships **no** Python client wrapper: Cowork
invokes ``mcp__vero-bridge__*`` directly, byte-for-byte identically to
Chat bar ``claimed_tag="cowork"`` (wire-format §7.5). The tab-facing
surface is tab-agnostic, so the registered-surface / doc-rot assertions
live in ``test_chat_client.py`` and are not duplicated here.

This module focuses on the two things that are genuinely Cowork-specific:

- **Cowork-path round-trip** — invoking each tool the way a Cowork tab
  would (``claimed_tag="cowork"``) yields the documented response shape
  and logs ``claimed_tag`` verbatim (OQ-T3 Option I).
- **AC-7 cross-client parity** — for the same logical call, the Chat
  path and the Cowork path produce responses that are identical in
  shape and byte-for-byte identical on the stable portion. The only
  permitted differences are fields that are *meant* to vary: the echoed
  ``claimed_tag`` (reflects the caller) and per-call / per-process
  observables (``ts_ns``, ``uptime_s``, ``last_call_ts_ns``, ``pid``,
  ``ppid``, ``stdin_fd``, ``stdout_fd``).

The audit log is redirected to a temp path so these tests never touch
the real ``docs/research/private/`` baseline. Live cross-client evidence
(AC-3 / AC-6) is captured separately in Step 4.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from tools.vero_bridge import _audit_log
from tools.vero_bridge._audit_log import reset_counter_for_test
from tools.vero_bridge.server import bridge_status, bridge_whoami, echo

#: The Cowork tab's self-asserted identity (audit-only per OQ-T3 Option I).
COWORK_CLAIMED_TAG = "cowork"

#: A fixed payload token so both client paths echo the same value — any
#: difference in the stable portion then signals a real parity break.
_PARITY_NAME = "parity-probe"

#: Response keys that are *meant* to differ between (or within) clients:
#: the echoed caller identity plus per-call / per-process observables.
#: Stripping these leaves the portion that AC-7 requires to be identical.
_PARITY_VARYING_KEYS = frozenset(
    {
        "claimed_tag",
        "ts_ns",
        "uptime_s",
        "last_call_ts_ns",
        "pid",
        "ppid",
        "stdin_fd",
        "stdout_fd",
    }
)

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


#: Map a tool name to a 1-arg caller that invokes it the way a tab would
#: (only ``claimed_tag`` varies; payload is fixed for parity comparison).
_CALLERS: dict[str, Callable[[str], dict[str, Any]]] = {
    "echo": lambda tag: echo(version=1, claimed_tag=tag, name=_PARITY_NAME),
    "bridge_status": lambda tag: bridge_status(version=1, claimed_tag=tag),
    "bridge_whoami": lambda tag: bridge_whoami(version=1, claimed_tag=tag),
}


def _read_audit_lines(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _stable_portion(response: dict[str, Any]) -> dict[str, Any]:
    """Drop the meant-to-vary keys, leaving the portion AC-7 requires to
    be byte-for-byte identical across clients."""
    return {k: v for k, v in response.items() if k not in _PARITY_VARYING_KEYS}


def _doc_section_7_5() -> str:
    doc = _WIRE_FORMAT_DOC.read_text(encoding="utf-8")
    start = doc.index("### 7.5 Cowork tab")
    end = doc.index("## 8. Change log", start)
    return doc[start:end]


# ---------------------------------------------------------------------------
# Cowork-path round-trip
# ---------------------------------------------------------------------------


def test_cowork_echo_round_trip_matches_documented_shape(audit_log_path: Path) -> None:
    token = "step3b-cowork-contract-token"
    response = echo(version=1, claimed_tag=COWORK_CLAIMED_TAG, name=token)
    assert response == {"ok": True, "echoed": token, "ts_ns": response["ts_ns"]}
    # ts_ns is a decimal string (FINDING-2) so it survives JSON-double clients.
    assert isinstance(response["ts_ns"], str) and int(response["ts_ns"]) > 0


def test_cowork_claimed_tag_logged_verbatim(audit_log_path: Path) -> None:
    echo(version=1, claimed_tag=COWORK_CLAIMED_TAG, name="x")
    records = _read_audit_lines(audit_log_path)
    assert len(records) == 1
    assert records[0]["claimed_tag"] == COWORK_CLAIMED_TAG
    assert records[0]["outcome"] == "ok"


def test_cowork_whoami_echoes_cowork_tag(audit_log_path: Path) -> None:
    response = bridge_whoami(version=1, claimed_tag=COWORK_CLAIMED_TAG)
    assert response["ok"] is True
    assert response["claimed_tag"] == COWORK_CLAIMED_TAG


def test_cowork_fail_closed_version_mismatch(audit_log_path: Path) -> None:
    response = echo(version=2, claimed_tag=COWORK_CLAIMED_TAG, name="x")
    assert response["ok"] is False
    assert response["error_code"] == "version-mismatch"
    assert set(response) == {"ok", "error_code", "error_message"}
    records = _read_audit_lines(audit_log_path)
    assert records[0]["outcome"] == "error"
    assert records[0]["claimed_tag"] == COWORK_CLAIMED_TAG


# ---------------------------------------------------------------------------
# AC-7 cross-client parity (Chat path vs Cowork path)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tool_name", sorted(_CALLERS))
def test_ac7_shape_parity_across_clients(audit_log_path: Path, tool_name: str) -> None:
    """The wire shape (response key set) is identical regardless of which
    tab calls — there is no per-tab branch in the surface."""
    chat = _CALLERS[tool_name]("chat")
    cowork = _CALLERS[tool_name]("cowork")
    assert set(chat) == set(cowork)


@pytest.mark.parametrize("tool_name", sorted(_CALLERS))
def test_ac7_stable_portion_byte_for_byte_identical(audit_log_path: Path, tool_name: str) -> None:
    """After removing the meant-to-vary fields, the Chat-path and
    Cowork-path responses serialize to identical bytes — the AC-7
    byte-for-byte parity guarantee on the stable portion."""
    chat = _stable_portion(_CALLERS[tool_name]("chat"))
    cowork = _stable_portion(_CALLERS[tool_name]("cowork"))
    assert json.dumps(chat, sort_keys=True) == json.dumps(cowork, sort_keys=True)


def test_ac7_claimed_tag_is_the_only_by_design_difference_in_whoami(audit_log_path: Path) -> None:
    """whoami is the only Phase 1 tool that echoes ``claimed_tag``. Assert
    it is the *sole* by-design divergence: it differs as expected, and
    once removed the remaining stable portion is identical."""
    chat = bridge_whoami(version=1, claimed_tag="chat")
    cowork = bridge_whoami(version=1, claimed_tag="cowork")
    assert chat["claimed_tag"] == "chat"
    assert cowork["claimed_tag"] == "cowork"
    assert _stable_portion(chat) == _stable_portion(cowork)


def test_ac7_echo_payload_round_trips_identically(audit_log_path: Path) -> None:
    """The echoed payload is independent of the caller — the same ``name``
    comes back unchanged from both client paths."""
    chat = echo(version=1, claimed_tag="chat", name=_PARITY_NAME)
    cowork = echo(version=1, claimed_tag="cowork", name=_PARITY_NAME)
    assert chat["echoed"] == cowork["echoed"] == _PARITY_NAME


# ---------------------------------------------------------------------------
# Doc tie — §7.5 records the Cowork-specific contract
# ---------------------------------------------------------------------------


def test_doc_section_7_5_documents_cowork_invocation_and_parity() -> None:
    """§7.5 must show the Cowork invocation, reference this parity test,
    and record the load-bearing Code/Cowork indistinguishability fact."""
    section = _doc_section_7_5()
    assert 'claimed_tag="cowork"' in section
    assert "tests/vero_bridge/test_cowork_client.py" in section
    assert "instance B" in section
    assert "AC-7" in section
