"""The ``event``/Alert-trigger bridge — pure, DB-free helpers (ADR-0029 / PLAN-0056).

The recommender's actionable detection feeds INTO the governed Procedure engine (ADR-0029
SD-1): an actionable event maps to and fires a governed ``PipelineRun`` — not the lightweight
``ActionRecord`` execute path. This module holds the deterministic dedup key + run-id
composition (Step 3); the event resolver (Step 4) and the in-process fire function (Step 5)
build on it. Everything here is pure + offline-testable — no DB, no model call.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import UTC, datetime

_KEY_HEX_LEN = 16
"""sha256 hexdigest truncated to 16 chars (64 bits) — ample for per-vertical event dedup,
short enough to keep the ``<procedure_id>@<event_key>`` run-id compact."""


def event_key(
    *,
    vertical: str,
    event_kind: str,
    entity_ids: Sequence[str],
    detected_at: datetime,
    window_seconds: int,
) -> str:
    """The deterministic dedup key of an event-fired run (ADR-0029 SD-2 / PLAN-0056 SD-P1).

    Hashes ``(vertical, event_kind, sorted primary affected-entity ids, detection-window
    bucket)``. The window bucket truncates ``detected_at`` to ``window_seconds`` granularity,
    so a steady-state anomaly re-detected each poll collapses to ONE key (=> one run — an
    idempotent no-op re-fire), while the same condition recurring in a LATER window yields a
    fresh key (=> a new run). Entity ids are sorted so detection ordering never splits the key.
    A naive ``detected_at`` is read as UTC so the bucket is machine-independent (never the
    host's local tz). ``window_seconds`` is per-mapping (SD-P1) — wired from the
    :class:`EventTrigger` descriptor by the Step-5 fire function; a slow-moving asset anomaly
    wants a wide window, a transient one a narrow one.
    """
    if window_seconds <= 0:
        raise ValueError(f"event_key: window_seconds must be > 0 (got {window_seconds})")
    if detected_at.tzinfo is None:
        detected_at = detected_at.replace(tzinfo=UTC)
    bucket = int(detected_at.timestamp()) // window_seconds
    # \x1f (unit separator) is an unambiguous field boundary so a split shift can never collide
    # (e.g. vertical="a"+kind="bc" must not hash the same as vertical="ab"+kind="c").
    payload = "\x1f".join([vertical, event_kind, *sorted(entity_ids), str(bucket)])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:_KEY_HEX_LEN]


def event_run_id(procedure_id: str, key: str) -> str:
    """Compose the per-event ``run_id`` ``<procedure_id>@<event_key>`` — the ``pipeline_runs``
    PK whose write-ahead insert makes a re-detected event an idempotent no-op (ADR-0029 SD-2;
    mirrors the schedule ``<schedule_id>@<scheduled_for>`` key, PLAN-0055 Step 6)."""
    return f"{procedure_id}@{key}"
