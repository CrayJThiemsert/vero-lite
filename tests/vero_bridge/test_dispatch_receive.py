"""Tests for ``dispatch_receive`` — PLAN-0012 Step 2b (tool 4/4).

``dispatch_receive`` is a receive-only inbox: it appends a dispatch envelope to
a gitignored queue and returns a content-addressed ``received_id`` + ``ts_ns``.
No commit, no bind-on-Cray (authority stays not-on-bridge). No new
``ErrorCode`` — only a non-dict / non-JSON-serializable ``envelope`` is a
transport ``MALFORMED_FRAME``.

Coverage:

- **Queue module** (``tools.vero_bridge._dispatch_queue``): deterministic
  content-addressed ``received_id``; the appended JSONL record shape; the
  best-effort write (OSError swallowed, no crash).
- **Server handler** (``_handle_dispatch_receive``): happy enqueue + response
  shape; received_id matches the content hash; ts_ns is a decimal string
  matching the queue/audit int; non-dict + non-JSON rejection; envelope
  round-trips into the queue; envelope fail-closed; audit side-effects; AC-7
  parity (stable portion identical; only the per-call ts_ns varies).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.vero_bridge import _audit_log, _dispatch_queue
from tools.vero_bridge._audit_log import reset_counter_for_test
from tools.vero_bridge._dispatch_queue import compute_received_id, enqueue_dispatch
from tools.vero_bridge.server import _handle_dispatch_receive

_ENVELOPE: dict[str, object] = {
    "from": "code-session-25",
    "to": "cowork-session-25",
    "actor": "code",
    "phase": "dispatch",
    "title": "dispatch sample",
}


@pytest.fixture(autouse=True)
def _reset_counter() -> None:
    reset_counter_for_test()


@pytest.fixture
def queue_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "dispatch-queue.jsonl"
    monkeypatch.setattr(_dispatch_queue, "DEFAULT_QUEUE_PATH", path)
    return path


@pytest.fixture
def audit_log_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(_audit_log, "DEFAULT_LOG_PATH", path)
    return path


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


# ---------------------------------------------------------------------------
# Queue module — compute_received_id + enqueue_dispatch
# ---------------------------------------------------------------------------


def test_received_id_is_deterministic_and_content_addressed() -> None:
    a = compute_received_id(_ENVELOPE)
    b = compute_received_id(dict(reversed(list(_ENVELOPE.items()))))  # key order irrelevant
    assert a == b  # canonical (sort_keys) → order-independent
    assert a.startswith("rcv-")
    assert compute_received_id({"different": "envelope"}) != a


def test_enqueue_writes_one_record(tmp_path: Path) -> None:
    qp = tmp_path / "q.jsonl"
    received_id = enqueue_dispatch(_ENVELOPE, claimed_tag="cowork", ts_ns=123, queue_path=qp)
    assert received_id == compute_received_id(_ENVELOPE)
    records = _read_jsonl(qp)
    assert len(records) == 1
    assert records[0] == {
        "received_id": received_id,
        "ts_ns": 123,  # queue keeps the int (source of truth)
        "claimed_tag": "cowork",
        "envelope": _ENVELOPE,
    }


def test_enqueue_write_failure_is_swallowed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Best-effort (mirrors the audit log): an OSError on write must not raise
    — the content-addressed received_id is still returned."""

    def _boom(*_args: object, **_kwargs: object) -> object:
        raise PermissionError("simulated queue write failure")

    monkeypatch.setattr(Path, "open", _boom)
    qp = tmp_path / "q.jsonl"
    received_id = enqueue_dispatch(_ENVELOPE, claimed_tag="cowork", ts_ns=1, queue_path=qp)
    assert received_id == compute_received_id(_ENVELOPE)
    assert not qp.exists()


# ---------------------------------------------------------------------------
# Server handler — happy
# ---------------------------------------------------------------------------


def test_handler_happy_returns_documented_shape(queue_path: Path, audit_log_path: Path) -> None:
    response = _handle_dispatch_receive(version=1, claimed_tag="cowork", envelope=_ENVELOPE)
    assert response["ok"] is True
    assert set(response) == {"ok", "received_id", "ts_ns"}
    assert response["received_id"] == compute_received_id(_ENVELOPE)
    assert isinstance(response["ts_ns"], str) and response["ts_ns"].isdigit()


def test_handler_enqueues_envelope_and_matches_ts(queue_path: Path, audit_log_path: Path) -> None:
    response = _handle_dispatch_receive(version=1, claimed_tag="cowork", envelope=_ENVELOPE)
    queued = _read_jsonl(queue_path)
    assert len(queued) == 1
    assert queued[0]["envelope"] == _ENVELOPE
    assert queued[0]["received_id"] == response["received_id"]
    # The returned decimal-string ts_ns is the stringified queue int (FINDING-2).
    assert response["ts_ns"] == str(queued[0]["ts_ns"])


def test_handler_writes_ok_audit_record(queue_path: Path, audit_log_path: Path) -> None:
    _handle_dispatch_receive(version=1, claimed_tag="cowork", envelope=_ENVELOPE)
    records = _read_jsonl(audit_log_path)
    assert len(records) == 1
    assert records[0]["tool_name"] == "dispatch_receive"
    assert records[0]["claimed_tag"] == "cowork"
    assert records[0]["outcome"] == "ok"
    assert records[0]["error_code"] is None


# ---------------------------------------------------------------------------
# Server handler — fail-closed
# ---------------------------------------------------------------------------


def test_handler_non_dict_envelope_returns_malformed_frame(
    queue_path: Path, audit_log_path: Path
) -> None:
    response = _handle_dispatch_receive(
        version=1,
        claimed_tag="cowork",
        envelope="not-a-dict",  # type: ignore[arg-type]
    )
    assert response["ok"] is False
    assert response["error_code"] == "malformed-frame"
    assert _read_jsonl(queue_path) == []  # nothing enqueued on rejection
    records = _read_jsonl(audit_log_path)
    assert records[0]["outcome"] == "error"
    assert records[0]["error_code"] == "malformed-frame"


def test_handler_non_json_serializable_envelope_returns_malformed_frame(
    queue_path: Path, audit_log_path: Path
) -> None:
    response = _handle_dispatch_receive(
        version=1,
        claimed_tag="cowork",
        envelope={"bad": {1, 2, 3}},  # a set is not JSON
    )
    assert response["ok"] is False
    assert response["error_code"] == "malformed-frame"
    assert _read_jsonl(queue_path) == []


def test_handler_version_mismatch_returns_error(queue_path: Path, audit_log_path: Path) -> None:
    response = _handle_dispatch_receive(version=99, claimed_tag="cowork", envelope=_ENVELOPE)
    assert response["ok"] is False
    assert response["error_code"] == "version-mismatch"
    records = _read_jsonl(audit_log_path)
    assert records[0]["outcome"] == "error"
    assert records[0]["error_code"] == "version-mismatch"


def test_handler_empty_claimed_tag_returns_malformed_frame(
    queue_path: Path, audit_log_path: Path
) -> None:
    response = _handle_dispatch_receive(version=1, claimed_tag="", envelope=_ENVELOPE)
    assert response["ok"] is False
    assert response["error_code"] == "malformed-frame"


# ---------------------------------------------------------------------------
# AC-7 cross-client parity (stable portion; ts_ns varies per call)
# ---------------------------------------------------------------------------


def test_handler_ac7_parity_across_clients(queue_path: Path, audit_log_path: Path) -> None:
    """Same envelope from Chat vs Cowork → identical stable portion (ok +
    content-addressed received_id). Only the per-call ts_ns differs."""
    chat = _handle_dispatch_receive(version=1, claimed_tag="chat", envelope=_ENVELOPE)
    cowork = _handle_dispatch_receive(version=1, claimed_tag="cowork", envelope=_ENVELOPE)
    assert chat["ok"] is cowork["ok"] is True
    assert chat["received_id"] == cowork["received_id"]  # content-addressed → identical
    records = _read_jsonl(audit_log_path)
    assert [r["claimed_tag"] for r in records] == ["chat", "cowork"]
