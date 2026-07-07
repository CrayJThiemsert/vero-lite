"""PLAN-0056 Step 3 (ADR-0029 SD-2 / SD-P1) — the event dedup key + run-id helpers.

Pure/offline: proves the idempotency semantics (AC-5) — a re-detected event inside the
same detection window collapses to ONE key (=> one governed run), a later window fires a
fresh key, and the key is order-independent + machine-independent (naive datetime = UTC).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from services.engine.procedures.event_bridge import event_key, event_run_id

_T0 = datetime(2026, 7, 7, 6, 0, 0, tzinfo=UTC)


def _key(
    *,
    vertical: str = "procurement",
    event_kind: str = "asset_failure",
    entity_ids: list[str] | None = None,
    detected_at: datetime = _T0,
    window_seconds: int = 3600,
) -> str:
    return event_key(
        vertical=vertical,
        event_kind=event_kind,
        entity_ids=entity_ids if entity_ids is not None else ["pump-7"],
        detected_at=detected_at,
        window_seconds=window_seconds,
    )


def test_event_key_is_deterministic() -> None:
    assert _key() == _key()


def test_event_key_re_detect_same_window_collapses() -> None:
    # AC-5: the same event re-detected 30 min later (same 1h window) yields the SAME key —
    # so the write-ahead run_id insert is an idempotent no-op (no duplicate governed run).
    later = _T0 + timedelta(minutes=30)
    assert _key() == _key(detected_at=later)


def test_event_key_distinct_window_fires_fresh() -> None:
    # The same condition recurring in a LATER window yields a fresh key (a new run).
    next_window = _T0 + timedelta(hours=1, minutes=1)
    assert _key() != _key(detected_at=next_window)


def test_event_key_entity_order_independent() -> None:
    # Entity ordering never splits the key (ids are sorted before hashing).
    assert _key(entity_ids=["a", "b"]) == _key(entity_ids=["b", "a"])


def test_event_key_distinguishes_vertical() -> None:
    assert _key() != _key(vertical="energy")


def test_event_key_distinguishes_event_kind() -> None:
    assert _key() != _key(event_kind="low_stock")


def test_event_key_distinguishes_entity() -> None:
    assert _key() != _key(entity_ids=["pump-8"])


def test_event_key_no_field_boundary_collision() -> None:
    # The unit-separator join means a split shift cannot collide.
    assert _key(vertical="a", event_kind="bc") != _key(vertical="ab", event_kind="c")


def test_event_key_naive_datetime_treated_as_utc() -> None:
    # A naive detected_at is read as UTC — the bucket is machine-independent (not host-local).
    naive = _T0.replace(tzinfo=None)
    assert _key(detected_at=naive) == _key(detected_at=_T0)


def test_event_key_rejects_nonpositive_window() -> None:
    with pytest.raises(ValueError, match="window_seconds must be > 0"):
        _key(window_seconds=0)


def test_event_run_id_format() -> None:
    key = _key()
    assert event_run_id("event_emergency_sourcing_round", key) == (
        f"event_emergency_sourcing_round@{key}"
    )
