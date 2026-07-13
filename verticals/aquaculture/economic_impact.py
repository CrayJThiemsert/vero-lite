"""Aquaculture vertical — Box-4 economic-impact (฿) producer (ADR-0030 / PLAN-0071).

Assumptions-first v1 (PLAN-0071 SD-B): aquaculture is in-memory synthetic with no
committed ฿ cost-carrier property, so every ฿ input is a **named, disclosed
assumption** (ADR-0030 D3), never event-derived. The figures are the ratified SD-G
``mortality_avoided`` scenario: a low-DO event on a tiger-prawn pond near harvest
(the s123 narrative) the governed aeration caps at a residual mortality.

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

# Ratified SD-G (PLAN-0071) — pond biomass value ฿850,000; unmitigated low-DO
# mortality 35% vs governed aeration 5% + ฿8,000 energy/ops → baseline ฿297,500 vs
# governed ฿50,500.
_POND_BIOMASS_THB = Decimal("850000")
_UNMITIGATED_MORTALITY_FRACTION = Decimal("0.35")
_GOVERNED_MORTALITY_FRACTION = Decimal("0.05")
_AERATION_ENERGY_OPS_THB = Decimal("8000")


async def aquaculture_economic_impact(
    event: Mapping[str, Any], vertical: str
) -> EconomicImpact | None:
    """Compute the aquaculture ``mortality_avoided`` ฿ facet from the SD-G assumptions."""
    baseline_loss = _POND_BIOMASS_THB * _UNMITIGATED_MORTALITY_FRACTION
    governed_loss = _POND_BIOMASS_THB * _GOVERNED_MORTALITY_FRACTION
    baseline = EconomicExposure(
        label="unmitigated low-DO event (35% biomass mortality)",
        exposure_thb=baseline_loss,
        components={"mortality_loss_thb": baseline_loss},
    )
    governed = EconomicExposure(
        label="governed aeration (residual mortality + energy/ops)",
        exposure_thb=governed_loss + _AERATION_ENERGY_OPS_THB,
        components={
            "residual_mortality_thb": governed_loss,
            "aeration_energy_ops_thb": _AERATION_ENERGY_OPS_THB,
        },
    )
    return EconomicImpact(
        provisional=True,
        currency="THB",
        kind="mortality_avoided",
        baseline=baseline,
        governed=governed,
        net_benefit_thb=baseline.exposure_thb - governed.exposure_thb,
        assumptions=[
            "tiger-prawn pond biomass value ฿850,000 near harvest (modelled, not a data column)",
            "unmitigated low-DO mortality 35% of biomass",
            "governed aeration residual mortality 5% of biomass",
            "aeration energy/ops cost ฿8,000 per governed intervention",
        ],
    )


def register_aquaculture_economic_impact() -> None:
    """Register the aquaculture ฿-impact producer (the guarded optional import in
    ``discovery._register_vertical`` calls this)."""
    register_economic_producer("aquaculture", aquaculture_economic_impact)
