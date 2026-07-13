"""Energy vertical — Box-4 economic-impact (฿) producer (ADR-0030 / PLAN-0071).

Assumptions-first v1 (PLAN-0071 SD-B): energy carries no committed ฿ cost-carrier
property (its ORM/Alembic weight makes real properties a clean v2 —
``project_only_energy_has_committed_orm_no_alembic_for_others``), so every ฿ input
is a **named, disclosed assumption** (ADR-0030 D3), never event-derived. The
figures are the ratified SD-G ``avoided_outage`` scenario: a feeder-overload
over-current outage the governed intervention shortens.

The producer is a pure function over the SD-G constants — deterministic, offline,
no ontology edit / regen / migration. It is advisory + ``provisional`` (ADR-0030
D5): the engine helper appends it as a trace step that never alters the action.
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

# Ratified SD-G (PLAN-0071) — plausibility-grade v1 constants, every one disclosed
# below in ``assumptions``. feeder-overload outage cost ฿120,000/hr; unmitigated 4h
# vs governed 0.5h + ฿15,000 crew/switching → baseline ฿480,000 vs governed ฿75,000.
_OUTAGE_THB_PER_HOUR = Decimal("120000")
_UNMITIGATED_HOURS = Decimal("4")
_GOVERNED_HOURS = Decimal("0.5")
_CREW_SWITCHING_THB = Decimal("15000")


async def energy_economic_impact(event: Mapping[str, Any], vertical: str) -> EconomicImpact | None:
    """Compute the energy ``avoided_outage`` ฿ facet from the SD-G assumptions."""
    baseline_downtime = _OUTAGE_THB_PER_HOUR * _UNMITIGATED_HOURS
    governed_downtime = _OUTAGE_THB_PER_HOUR * _GOVERNED_HOURS
    baseline = EconomicExposure(
        label="unmitigated feeder-overload over-current outage",
        exposure_thb=baseline_downtime,
        components={"outage_downtime_thb": baseline_downtime},
    )
    governed = EconomicExposure(
        label="governed intervention (early trip + crew/switching)",
        exposure_thb=governed_downtime + _CREW_SWITCHING_THB,
        components={
            "residual_downtime_thb": governed_downtime,
            "crew_switching_thb": _CREW_SWITCHING_THB,
        },
    )
    return EconomicImpact(
        provisional=True,
        currency="THB",
        kind="avoided_outage",
        baseline=baseline,
        governed=governed,
        net_benefit_thb=baseline.exposure_thb - governed.exposure_thb,
        assumptions=[
            "feeder-overload outage cost ฿120,000/hr (modelled, not a data column)",
            "unmitigated over-current outage duration 4h",
            "governed intervention duration 0.5h",
            "crew/switching cost ฿15,000 per governed intervention",
        ],
    )


def register_energy_economic_impact() -> None:
    """Register the energy ฿-impact producer (ADR-0023 registry discipline; the
    guarded optional import in ``discovery._register_vertical`` calls this)."""
    register_economic_producer("energy", energy_economic_impact)
