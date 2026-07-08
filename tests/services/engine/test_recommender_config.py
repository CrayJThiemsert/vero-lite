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
    crosses_threshold,
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


# --- PLAN-0016 Step 0: threshold direction (below-breach support) ---


def _do_crash_event() -> dict[str, Any]:
    """An aquaculture dissolved-oxygen crash — breaches BELOW threshold."""
    return {
        "event_id": "event-reading-07",
        "event_type": "reading",
        "measured_value": 3.2,
        "unit": "mg/L",
        "pond_id": "POND-07",
    }


def test_crosses_threshold_above_default() -> None:
    """Default 'above': at-or-above the threshold crosses (energy over-temp)."""
    assert crosses_threshold(96.5, 90.0, "above") is True
    assert crosses_threshold(90.0, 90.0, "above") is True  # inclusive
    assert crosses_threshold(58.0, 90.0, "above") is False


def test_crosses_threshold_below() -> None:
    """'below': at-or-below the threshold crosses (DO crash)."""
    assert crosses_threshold(3.2, 4.0, "below") is True
    assert crosses_threshold(4.0, 4.0, "below") is True  # inclusive
    assert crosses_threshold(6.5, 4.0, "below") is False


def test_crosses_threshold_normalizes_and_fails_safe() -> None:
    """Case/space-insensitive; anything but 'below' means 'above' (fail-safe)."""
    assert crosses_threshold(3.2, 4.0, " Below ") is True
    assert crosses_threshold(96.5, 90.0, "garbage") is True  # != 'below' → 'above'
    assert crosses_threshold(3.2, 4.0, "above") is False


def test_below_direction_trigger(monkeypatch: pytest.MonkeyPatch) -> None:
    """Direction 'below': a DO crash below threshold fires; a healthy reading does not."""
    monkeypatch.setattr(settings, "oct_recommend_threshold", 4.0)
    monkeypatch.setattr(settings, "oct_recommend_direction", "below")
    assert _is_recommendation_trigger(_do_crash_event()) is True

    healthy = _do_crash_event()
    healthy["measured_value"] = 6.5
    assert _is_recommendation_trigger(healthy) is False


def test_below_direction_failsafe_wording(monkeypatch: pytest.MonkeyPatch) -> None:
    """The fail-safe fires below threshold; trace/description read 'below', never '>='."""
    monkeypatch.setattr(settings, "oct_recommend_threshold", 4.0)
    monkeypatch.setattr(settings, "oct_recommend_direction", "below")
    monkeypatch.setattr(settings, "oct_recommend_entity_type", "Pond")
    monkeypatch.setattr(settings, "oct_recommend_entity_id_field", "pond_id")
    monkeypatch.setattr(settings, "oct_recommend_label", "dissolved-oxygen crash")

    record = _rule_recommend(_do_crash_event(), "aquaculture")

    assert record is not None
    action = record.action
    assert action.affected_entities[0].object_type == "Pond"
    assert action.affected_entities[0].primary_key == "POND-07"
    assert "dissolved-oxygen crash" in action.title
    summary = action.reasoning_trace[0].summary
    assert "<=" in summary and ">=" not in summary
    assert "fell below" in action.description
    assert "rose above" not in action.description


def test_below_direction_silent_above(monkeypatch: pytest.MonkeyPatch) -> None:
    """Symmetry guard: under 'below', a reading ABOVE threshold must NOT fire."""
    monkeypatch.setattr(settings, "oct_recommend_threshold", 4.0)
    monkeypatch.setattr(settings, "oct_recommend_direction", "below")
    healthy = _do_crash_event()
    healthy["measured_value"] = 7.0
    assert _is_recommendation_trigger(healthy) is False
    assert _rule_recommend(healthy, "aquaculture") is None


def test_above_default_wording_unchanged() -> None:
    """Default 'above' direction keeps direction-correct wording ('rose above', '>=')."""
    record = _rule_recommend(_energy_overtemp_event(), "energy")
    assert record is not None
    action = record.action
    assert ">=" in action.reasoning_trace[0].summary
    assert "rose above" in action.description


# --- PLAN-0060 SD-4: the handler-catalog ship-dark flag defaults off ---


def test_handler_catalog_flag_defaults_off() -> None:
    """The reactive-prompt catalog is off by default → byte-identical to before (AC-4)."""
    assert settings.handler_catalog_enabled is False
