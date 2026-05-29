"""Receive-only dispatch queue for the ``dispatch_receive`` bridge tool.

PLAN-0012 Step 2b (capability inventory §2.7). ``dispatch_receive`` surfaces a
dispatch handoff envelope to a client tab **without carrying authority**: the
envelope is appended to a gitignored receive-queue as an informational,
durable record (a receive-side "inbox"). **No commit, no bind-on-Cray** —
authority-bearing operations stay not-on-bridge (AC-8 / ADR-013 D2); a binding
dispatch is ratified only through Code's internal mechanism, never here.

The queue write is the **same already-sanctioned write-class** as the AC-4 (b)
audit log: append-only JSONL under the gitignored ``docs/research/private/``
directory. Like the audit log, the write is **best-effort** — an I/O failure
is swallowed so it cannot take down the call (the envelope is still
acknowledged; ``received_id`` is content-addressed and exists regardless of
persistence).

``received_id`` is the SHA-256 content address of the canonical envelope —
deterministic and stateless (identical envelopes get the same id; no counter,
clock, or randomness needed). ``ts_ns`` distinguishes repeated receives of the
same envelope in the queue.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from threading import Lock
from typing import Any

#: Phase 1 default queue path (gitignored, same directory as the audit log).
#: Relative to the server's working directory (repo root under the Desktop
#: spawn), mirroring :data:`tools.vero_bridge._audit_log.DEFAULT_LOG_PATH`.
#: Tests monkeypatch this to a temp path.
DEFAULT_QUEUE_PATH: Path = Path("docs/research/private/vero-bridge-dispatch-queue.jsonl")

#: Serialize concurrent appends from the same process (belt-and-braces; the
#: OQ-T4 serial-per-instance discipline already prevents concurrency).
_write_lock = Lock()


def compute_received_id(envelope: dict[str, Any]) -> str:
    """Deterministic, content-addressed id for a dispatch envelope.

    ``rcv-<first 16 hex of sha256(canonical-json)>``. Stateless — no clock or
    randomness — so it is reproducible and testable. Raises ``TypeError`` /
    ``ValueError`` if ``envelope`` is not JSON-serializable (the caller
    validates serializability fail-closed before calling).
    """
    canonical = json.dumps(envelope, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"rcv-{digest[:16]}"


def enqueue_dispatch(
    envelope: dict[str, Any],
    *,
    claimed_tag: str,
    ts_ns: int,
    queue_path: Path | None = None,
) -> str:
    """Append one dispatch envelope to the receive-queue; return ``received_id``.

    Receive-only: writes an informational record, never commits or binds. The
    write is best-effort (OSError swallowed, like the audit log) — the returned
    ``received_id`` is valid regardless of whether persistence succeeded. The
    queue keeps ``ts_ns`` as an int (full precision; the client-facing tool
    stringifies it per FINDING-2).
    """
    received_id = compute_received_id(envelope)
    record = {
        "received_id": received_id,
        "ts_ns": ts_ns,
        "claimed_tag": claimed_tag,
        "envelope": envelope,
    }
    path = queue_path if queue_path is not None else DEFAULT_QUEUE_PATH
    line = json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n"
    try:
        with _write_lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fp:
                fp.write(line)
                fp.flush()
    except OSError:
        # Best-effort durable record (mirrors the audit log): a queue-write
        # failure must not take down the call. The envelope is still
        # acknowledged via the content-addressed received_id.
        pass
    return received_id
