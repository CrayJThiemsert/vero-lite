"""Unit tests for the Box-4 economic-impact facet models + never-raise helper
(ADR-0030 / PLAN-0071 AC-1, AC-2). Deterministic-offline — no MS-S1, no DB."""

from __future__ import annotations

import logging
from decimal import Decimal

import pytest
from pydantic import ValidationError

from services.engine.actions import ReasoningStep
from services.engine.economic_impact import (
    EconomicExposure,
    EconomicImpact,
    build_economic_steps,
    clear_economic_producers,
    register_economic_producer,
    registered_economic_verticals,
)


@pytest.fixture(autouse=True)
def _reset_producers() -> None:
    """Every test starts + ends with an empty producer registry (module-global)."""
    clear_economic_producers()
    yield
    clear_economic_producers()


def _impact(net: str = "405000") -> EconomicImpact:
    """A valid EconomicImpact whose net_benefit matches the baseline-governed delta."""
    return EconomicImpact(
        provisional=True,
        currency="THB",
        kind="avoided_outage",
        baseline=EconomicExposure(
            label="unmitigated over-current outage",
            exposure_thb=Decimal("480000"),
            components={"downtime_thb": Decimal("480000")},
        ),
        governed=EconomicExposure(
            label="governed intervention",
            exposure_thb=Decimal("480000") - Decimal(net),
        ),
        net_benefit_thb=Decimal(net),
        assumptions=["outage cost ฿120,000/hr", "unmitigated 4h vs governed 0.5h"],
        basis_refs=[],
    )


# --- AC-1: the typed models ---------------------------------------------------


def test_economic_impact_constructs_and_holds_fields() -> None:
    impact = _impact()
    assert impact.provisional is True
    assert impact.currency == "THB"
    assert impact.kind == "avoided_outage"
    assert impact.net_benefit_thb == Decimal("405000")
    assert impact.baseline.exposure_thb == Decimal("480000")


def test_economic_impact_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        EconomicImpact(  # type: ignore[call-arg]
            provisional=True,
            currency="THB",
            kind="avoided_outage",
            baseline=EconomicExposure(label="b", exposure_thb=Decimal("1")),
            governed=EconomicExposure(label="g", exposure_thb=Decimal("0")),
            net_benefit_thb=Decimal("1"),
            assumptions=[],
            surprise="not allowed",
        )


def test_economic_exposure_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        EconomicExposure(label="b", exposure_thb=Decimal("1"), surprise="no")  # type: ignore[call-arg]


def test_net_benefit_must_equal_baseline_minus_governed() -> None:
    with pytest.raises(ValidationError, match="net_benefit_thb"):
        EconomicImpact(
            provisional=True,
            currency="THB",
            kind="avoided_outage",
            baseline=EconomicExposure(label="b", exposure_thb=Decimal("480000")),
            governed=EconomicExposure(label="g", exposure_thb=Decimal("75000")),
            net_benefit_thb=Decimal("999999"),  # != 480000 - 75000
            assumptions=[],
        )


def test_json_dump_serializes_decimal_as_string_and_round_trips() -> None:
    impact = _impact()
    dumped = impact.model_dump(mode="json")
    assert dumped["net_benefit_thb"] == "405000"  # Decimal -> string (Pydantic v2 JSON mode)
    assert dumped["baseline"]["exposure_thb"] == "480000"
    assert EconomicImpact.model_validate(dumped) == impact  # round-trips equal


# --- AC-2: the never-raise emission helper ------------------------------------


async def test_build_economic_steps_no_producer_returns_empty() -> None:
    assert await build_economic_steps({"event_id": "e1"}, "energy") == []


async def test_build_economic_steps_producer_none_returns_empty() -> None:
    async def _none_producer(event: object, vertical: str) -> None:
        return None

    register_economic_producer("energy", _none_producer)
    assert await build_economic_steps({"event_id": "e1"}, "energy") == []


async def test_build_economic_steps_success_emits_one_typed_step() -> None:
    impact = _impact()

    async def _producer(event: object, vertical: str) -> EconomicImpact:
        return impact

    register_economic_producer("energy", _producer)
    steps = await build_economic_steps({"event_id": "e1"}, "energy")
    assert len(steps) == 1
    step = steps[0]
    assert isinstance(step, ReasoningStep)
    assert step.kind == "economic_impact"
    assert step.step_id == "economic-impact-0"
    assert "provisional estimate" in step.summary
    assert step.detail is not None
    # the detail round-trips as EconomicImpact (producer-side type enforcement)
    assert EconomicImpact.model_validate(step.detail) == impact


async def test_build_economic_steps_never_raises_on_producer_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def _boom(event: object, vertical: str) -> EconomicImpact:
        raise RuntimeError("adapter exploded")

    register_economic_producer("energy", _boom)
    with caplog.at_level(logging.WARNING):
        steps = await build_economic_steps({"event_id": "e1"}, "energy")
    assert steps == []  # advisory: absence, never a propagated exception
    assert any("economic-impact producer" in rec.message for rec in caplog.records)


def test_registered_economic_verticals_snapshot() -> None:
    async def _producer(event: object, vertical: str) -> None:
        return None

    register_economic_producer("energy", _producer)
    register_economic_producer("procurement", _producer)
    assert registered_economic_verticals() == frozenset({"energy", "procurement"})
