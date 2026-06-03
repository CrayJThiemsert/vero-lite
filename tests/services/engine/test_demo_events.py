"""Tests for the per-process live OperationalEvent view (PLAN-0015 D1/D2).

Covers the AC-anchor determinism gate (flag off → fixed datetimes; flag on →
breach anchored to ~now, spacing preserved) and the execute-time recovery
injection. Pure in-process probes — no network, no DB (Lesson #7 §3).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from services.api.config import settings
from services.engine import demo_events


def _base() -> list[dict[str, Any]]:
    """A minimal 3-beat incident: nominal reading, breach reading, alarm."""
    return [
        {
            "event_id": "e-1",
            "event_type": "reading",
            "severity": "info",
            "measured_value": 30.0,
            "unit": "celsius",
            "occurred_at": datetime(2026, 5, 21, 8, 0, tzinfo=UTC),
            "asset_id": "asset-1",
            "site_id": "site-1",
        },
        {
            "event_id": "e-2",
            "event_type": "reading",
            "severity": "critical",
            "measured_value": 96.5,
            "unit": "celsius",
            "occurred_at": datetime(2026, 5, 21, 8, 10, tzinfo=UTC),
            "asset_id": "asset-1",
            "site_id": "site-1",
        },
        {
            "event_id": "e-3",
            "event_type": "alarm",
            "severity": "error",
            "occurred_at": datetime(2026, 5, 21, 8, 12, tzinfo=UTC),
            "asset_id": "asset-2",
            "site_id": "site-1",
        },
    ]


def test_flag_off_serves_base_datetimes(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-anchor (off): with the flag off the fixed synthetic datetimes survive."""
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    demo_events.reset()
    out = demo_events.events("t", _base)
    assert [e["occurred_at"] for e in out] == [e["occurred_at"] for e in _base()]


def test_flag_off_copies_source(monkeypatch: pytest.MonkeyPatch) -> None:
    """The module never mutates the synthetic source dicts (shallow-copies them)."""
    monkeypatch.setattr(settings, "oct_demo_time_anchor", True)
    monkeypatch.setattr(settings, "oct_recommend_threshold", 90.0)
    demo_events.reset()
    source = _base()
    original = source[1]["occurred_at"]
    demo_events.events("t", lambda: source)
    # anchoring shifted the live copy, not the caller's source list
    assert source[1]["occurred_at"] == original


def test_flag_on_anchors_breach_to_now(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-anchor (on): the breach lands ~now, original spacing preserved."""
    monkeypatch.setattr(settings, "oct_demo_time_anchor", True)
    monkeypatch.setattr(settings, "oct_recommend_threshold", 90.0)
    demo_events.reset()
    before = datetime.now(UTC)
    out = demo_events.events("t", _base)
    after = datetime.now(UTC)

    by_id = {e["event_id"]: e["occurred_at"] for e in out}
    assert before - timedelta(seconds=2) <= by_id["e-2"] <= after + timedelta(seconds=2)
    # relative spacing preserved (e-1 ten minutes before, e-3 two minutes after)
    assert by_id["e-2"] - by_id["e-1"] == timedelta(minutes=10)
    assert by_id["e-3"] - by_id["e-2"] == timedelta(minutes=2)


def test_anchor_threshold_aware(monkeypatch: pytest.MonkeyPatch) -> None:
    """The breach is the reading crossing the active threshold — not 'critical'.

    A lower threshold makes the 30 °C reading the (only) crossing; the breach is
    chosen by ``oct_recommend_threshold``, so a second vertical anchors on its
    own breach with zero per-vertical code (PLAN-0013 AC-template).
    """
    monkeypatch.setattr(settings, "oct_demo_time_anchor", True)
    monkeypatch.setattr(settings, "oct_recommend_threshold", 1000.0)  # nothing crosses
    demo_events.reset()
    out = demo_events.events("t", _base)
    # no breach → no anchor → base datetimes unchanged
    assert [e["occurred_at"] for e in out] == [e["occurred_at"] for e in _base()]


def test_events_cached_per_process(monkeypatch: pytest.MonkeyPatch) -> None:
    """events() returns the same mutable list so an injected recovery persists."""
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    demo_events.reset()
    assert demo_events.events("t", _base) is demo_events.events("t", _base)


def test_inject_recovery_lands_on_breach_asset(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-recovery: the recovery inherits the breach's asset, at execute-time."""
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    monkeypatch.setattr(settings, "oct_recommend_threshold", 90.0)
    monkeypatch.setattr(settings, "oct_recovery_value", 58.0)
    monkeypatch.setattr(settings, "oct_recovery_description", "back to safe range")
    demo_events.reset()
    demo_events.events("t", _base)

    ts = datetime.now(UTC)
    rec = demo_events.inject_recovery("t", breach_event_id="e-2", occurred_at=ts)
    assert rec is not None
    assert rec["event_id"] == "event-recovery-01"
    assert rec["measured_value"] == 58.0
    assert rec["severity"] == "info"
    assert rec["description"] == "back to safe range"
    assert rec["asset_id"] == "asset-1"  # inherited from the breach event
    assert rec["site_id"] == "site-1"
    assert rec["occurred_at"] == ts
    live = demo_events.events("t", _base)
    assert [e["event_id"] for e in live if e["event_id"] == "event-recovery-01"] == [
        "event-recovery-01"
    ]


def test_inject_recovery_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    """Re-executing never duplicates the recovery (one resolution per run)."""
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    monkeypatch.setattr(settings, "oct_recommend_threshold", 90.0)
    demo_events.reset()
    demo_events.events("t", _base)
    demo_events.inject_recovery("t", breach_event_id="e-2", occurred_at=datetime.now(UTC))
    demo_events.inject_recovery("t", breach_event_id="e-2", occurred_at=datetime.now(UTC))
    live = demo_events.events("t", _base)
    recoveries = [e for e in live if e["event_id"] == "event-recovery-01"]
    assert len(recoveries) == 1


def test_inject_recovery_noop_before_build() -> None:
    """Injecting before the live view exists is a graceful no-op."""
    demo_events.reset()
    out = demo_events.inject_recovery(
        "never-built", breach_event_id="e-2", occurred_at=datetime.now(UTC)
    )
    assert out is None
