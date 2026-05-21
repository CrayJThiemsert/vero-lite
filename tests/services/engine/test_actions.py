"""Tests for the RecommendedAction runtime envelope (ADR-007 D2, PLAN-0005 §7.3).

Lesson #7 §3 reliable methods: in-process construction probes,
``pytest.raises(ValidationError)`` for the confidence bound, and a
behavioral equality assertion for the dump/validate round-trip.
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from services.engine.actions import (
    AuditMetadata,
    EntityRef,
    ReasoningStep,
    RecommendedAction,
)


def _valid_action(confidence: float = 0.8) -> RecommendedAction:
    """Build a fully-populated RecommendedAction with a tunable confidence."""
    return RecommendedAction(
        id="act-1",
        title="Throttle asset",
        description="Reading exceeded the configured threshold.",
        vertical="energy",
        reasoning_trace=[
            ReasoningStep(step_id="s1", kind="rule_check", summary="threshold crossed"),
        ],
        confidence=confidence,
        affected_entities=[EntityRef(object_type="Asset", primary_key="asset-1")],
        suggested_handler="energy.echo",
        audit_metadata=AuditMetadata(actor="engine", actor_kind="engine"),
        created_at=datetime(2026, 5, 21, 12, 0, tzinfo=UTC),
    )


def test_recommended_action_constructs_from_valid_payload() -> None:
    """A valid payload constructs and applies the ADR-007 D2 defaults."""
    action = _valid_action()
    assert action.requires_approval is True
    assert action.handler_payload == {}
    assert action.approval_chain == []


def test_confidence_above_range_raises() -> None:
    """confidence > 1.0 fails validation."""
    with pytest.raises(ValidationError):
        _valid_action(confidence=1.5)


def test_confidence_below_range_raises() -> None:
    """confidence < 0.0 fails validation."""
    with pytest.raises(ValidationError):
        _valid_action(confidence=-0.1)


def test_envelope_round_trips() -> None:
    """model_validate(model_dump()) reproduces an equal envelope."""
    action = _valid_action()
    restored = RecommendedAction.model_validate(action.model_dump())
    assert restored == action
