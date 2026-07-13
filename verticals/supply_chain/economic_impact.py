"""Supply-chain vertical — Box-4 economic-impact (฿) producer (ADR-0030 / PLAN-0071).

Assumptions-first v1 (PLAN-0071 SD-B): supply_chain is in-memory synthetic with no
committed ฿ cost-carrier property, so every ฿ input is a **named, disclosed
assumption** (ADR-0030 D3), never event-derived. The figures are the ratified SD-G
``spoilage_avoided`` scenario: a pharma cold-chain excursion the governed re-route /
re-ice caps at a residual loss.

Pure function over the SD-G constants — deterministic, offline, no ontology edit /
regen / migration. Advisory + ``provisional`` (ADR-0030 D5).
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from services.engine.economic_impact import (
    EconomicExposure,
    EconomicImpact,
    register_economic_producer,
)

# Ratified SD-G (PLAN-0071) — cargo value ฿2,400,000; unmitigated 100% loss vs
# governed 10% loss + ฿40,000 re-route/re-ice → baseline ฿2,400,000 vs governed ฿280,000.
_CARGO_VALUE_THB = Decimal("2400000")
_UNMITIGATED_LOSS_FRACTION = Decimal("1.00")
_GOVERNED_LOSS_FRACTION = Decimal("0.10")
_REROUTE_REICE_THB = Decimal("40000")


async def supply_chain_economic_impact(
    event: Mapping[str, Any], vertical: str
) -> EconomicImpact | None:
    """Compute the supply-chain ``spoilage_avoided`` ฿ facet from the SD-G assumptions."""
    baseline_loss = _CARGO_VALUE_THB * _UNMITIGATED_LOSS_FRACTION
    governed_loss = _CARGO_VALUE_THB * _GOVERNED_LOSS_FRACTION
    baseline = EconomicExposure(
        label="unmitigated cold-chain excursion (total cargo loss)",
        exposure_thb=baseline_loss,
        components={"spoiled_cargo_thb": baseline_loss},
    )
    governed = EconomicExposure(
        label="governed re-route / re-ice (residual loss + intervention)",
        exposure_thb=governed_loss + _REROUTE_REICE_THB,
        components={
            "residual_spoilage_thb": governed_loss,
            "reroute_reice_thb": _REROUTE_REICE_THB,
        },
    )
    return EconomicImpact(
        provisional=True,
        currency="THB",
        kind="spoilage_avoided",
        baseline=baseline,
        governed=governed,
        net_benefit_thb=baseline.exposure_thb - governed.exposure_thb,
        assumptions=[
            "pharma cold-chain cargo value ฿2,400,000 (modelled, not a data column)",
            "unmitigated excursion = 100% cargo loss",
            "governed re-route / re-ice = 10% residual loss",
            "re-route / re-ice intervention cost ฿40,000",
        ],
    )


def register_supply_chain_economic_impact() -> None:
    """Register the supply-chain ฿-impact producer (the guarded optional import in
    ``discovery._register_vertical`` calls this)."""
    register_economic_producer("supply_chain", supply_chain_economic_impact)
