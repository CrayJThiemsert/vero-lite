"""Tests for the rule-based recommender + approval gate (PLAN-0005 §7.4).

Lesson #7 §3: in-process probes on returned objects, pytest.raises for
the documented transition errors, and a recorded-call side-effect
assertion for handler execution.
"""

from __future__ import annotations

from typing import Any

import pytest

from services.engine.actions import RecommendedAction
from services.engine.recommender import (
    ActionRecord,
    ActionStatus,
    ApprovalError,
    approve,
    execute,
    recommend,
    reject,
)
from services.engine.registry import registry


def _crossing_event() -> dict[str, Any]:
    """A reading event whose measured_value crosses the threshold."""
    return {
        "event_id": "event-reading-03",
        "event_type": "reading",
        "measured_value": 96.5,
        "unit": "celsius",
        "asset_id": "asset-battery-01",
        "site_id": "site-substation-01",
    }


def _normal_event() -> dict[str, Any]:
    """A reading event safely below the threshold."""
    return {
        "event_id": "event-reading-01",
        "event_type": "reading",
        "measured_value": 32.4,
        "unit": "celsius",
        "asset_id": "asset-battery-01",
    }


def _proposed_record() -> ActionRecord:
    record = recommend(_crossing_event(), "energy")
    assert record is not None
    return record


def test_recommend_returns_proposed_action_for_crossing_event() -> None:
    """§7.4 read -> recommend: a crossing event yields a proposed action."""
    record = _proposed_record()
    assert record.status is ActionStatus.PROPOSED
    assert record.action.requires_approval is True
    assert record.action.reasoning_trace
    assert record.action.vertical == "energy"


def test_recommend_reasoning_trace_is_rule_check() -> None:
    record = _proposed_record()
    assert [step.kind for step in record.action.reasoning_trace] == ["rule_check", "rule_check"]


def test_recommend_returns_none_for_normal_reading() -> None:
    assert recommend(_normal_event(), "energy") is None


def test_recommend_returns_none_for_non_reading_event() -> None:
    alarm = {"event_id": "event-alarm-01", "event_type": "alarm", "asset_id": "asset-inverter-01"}
    assert recommend(alarm, "energy") is None


def test_approve_transitions_proposed_to_approved() -> None:
    record = _proposed_record()
    approve(record)
    assert record.status is ActionStatus.APPROVED


def test_approve_on_non_proposed_raises() -> None:
    record = _proposed_record()
    approve(record)
    with pytest.raises(ApprovalError):
        approve(record)


def test_reject_transitions_proposed_to_rejected() -> None:
    record = _proposed_record()
    reject(record)
    assert record.status is ActionStatus.REJECTED


def test_reject_on_rejected_raises() -> None:
    record = _proposed_record()
    reject(record)
    with pytest.raises(ApprovalError):
        reject(record)


async def test_execute_requires_approval() -> None:
    """Executing a proposed (un-approved) action raises a documented error."""
    record = _proposed_record()
    with pytest.raises(ApprovalError):
        await execute(record)


async def test_execute_invokes_registered_handler() -> None:
    """§7.4 execute: an approved action invokes the registered handler."""
    calls: list[RecommendedAction] = []

    async def _handler(action: RecommendedAction) -> dict[str, Any]:
        calls.append(action)
        return {"executed": True, "action_id": action.id}

    registry.register_handler("energy", "echo", _handler)
    record = _proposed_record()
    approve(record)
    receipt = await execute(record)

    assert record.status is ActionStatus.EXECUTED
    assert calls == [record.action]
    assert receipt["executed"] is True


async def test_execute_on_executed_raises() -> None:
    """A second execute fails — the record is no longer approved."""

    async def _handler(action: RecommendedAction) -> dict[str, Any]:
        return {"ok": True}

    registry.register_handler("energy", "echo", _handler)
    record = _proposed_record()
    approve(record)
    await execute(record)
    with pytest.raises(ApprovalError):
        await execute(record)
