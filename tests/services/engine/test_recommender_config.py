"""Per-vertical recommender policy is data-driven (PLAN-0013 AC-template).

The deterministic trigger threshold and the fail-safe rule's affected-entity
type / event key / anomaly label are read from ``settings.oct_recommend_*``
(env-driven), so a second vertical escalates at its own threshold and the
offline fail-safe stays coherent — with NO recommender code change. The
defaults reproduce the energy vertical exactly (Rule-of-Three: a data-driven
2nd instance, not a meta-framework).
"""

from __future__ import annotations

from typing import Any

import pytest

from services.api.config import settings
from services.engine.recommender import (
    RULE_CONFIDENCE,
    _is_recommendation_trigger,
    _rule_recommend,
)


def _cold_chain_breach_event() -> dict[str, Any]:
    return {
        "event_id": "event-reading-03",
        "event_type": "reading",
        "measured_value": 14.6,
        "unit": "celsius",
        "shipment_id": "shipment-pharma-01",
        "facility_id": "facility-coldhub-01",
    }


def _energy_overtemp_event() -> dict[str, Any]:
    return {
        "event_id": "event-reading-03",
        "event_type": "reading",
        "measured_value": 96.5,
        "unit": "celsius",
        "asset_id": "asset-battery-01",
    }


def test_trigger_fires_at_configured_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    """A 14.6 °C reading trips the trigger at threshold 8, not at 90."""
    monkeypatch.setattr(settings, "oct_recommend_threshold", 8.0)
    assert _is_recommendation_trigger(_cold_chain_breach_event()) is True

    monkeypatch.setattr(settings, "oct_recommend_threshold", 90.0)
    assert _is_recommendation_trigger(_cold_chain_breach_event()) is False


def test_failsafe_uses_supply_chain_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    """The fail-safe rule targets the configured entity type / id field / label."""
    monkeypatch.setattr(settings, "oct_recommend_threshold", 8.0)
    monkeypatch.setattr(settings, "oct_recommend_entity_type", "Shipment")
    monkeypatch.setattr(settings, "oct_recommend_entity_id_field", "shipment_id")
    monkeypatch.setattr(settings, "oct_recommend_label", "cold-chain temperature breach")

    record = _rule_recommend(_cold_chain_breach_event(), "supply_chain")

    assert record is not None
    action = record.action
    assert action.confidence == RULE_CONFIDENCE
    assert action.affected_entities[0].object_type == "Shipment"
    assert action.affected_entities[0].primary_key == "shipment-pharma-01"
    assert "cold-chain temperature breach" in action.title
    assert "shipment-pharma-01" in action.title
    assert {step.kind for step in action.reasoning_trace} == {"rule_check"}


def test_failsafe_energy_defaults_unchanged() -> None:
    """With default settings the fail-safe reproduces the energy wording exactly."""
    record = _rule_recommend(_energy_overtemp_event(), "energy")

    assert record is not None
    action = record.action
    assert action.affected_entities[0].object_type == "Asset"
    assert action.affected_entities[0].primary_key == "asset-battery-01"
    assert "over-temperature" in action.title
    assert action.confidence == RULE_CONFIDENCE
