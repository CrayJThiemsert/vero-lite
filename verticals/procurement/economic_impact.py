"""Procurement vertical — Box-4 economic-impact (฿) producer (ADR-0030 / PLAN-0071).

**Real-column v1** (PLAN-0071 SD-B): unlike the three assumptions-first verticals,
procurement's ฿ figures come from committed CSV columns
(``fastenal_csv.py``: ``Asset.downtime_cost_per_hour_thb``,
``part_suppliable_by_supplier.quoted_unit_price_thb`` / ``lead_time_days``,
``PurchaseOrder.total_thb``). The producer reuses the proven demo ledger
computation (``hero_demo/ledger.py:39-95``, byte-untouched per ADR-0030 D2
coexist) and maps its Decimal-exact baseline/governed exposure into the engine's
``EconomicImpact`` shape, with ``basis_refs`` citing the source columns.

**OQ-C — anchor resolution (disclosed).** The trigger events carry criticality,
not a resolvable PO/asset ฿ anchor (``synthetic.py`` ``measured_value`` = a
criticality score), so v1 does NOT resolve an arbitrary event to its own PO.
Instead the producer emits the representative **emergency-sourcing** ฿ exemplar
(the hero PO, from committed CSVs) for the critical-failure trigger the ledger
models, and returns ``None`` for any non-failure event (a calm-path reorder has
no baseline-vs-governed ฿ tradeoff to model — the facet is absent, never guessed).
Per-event PO anchor resolution is a clean v2 once a pilot supplies the link.

The producer is deterministic + offline (reads committed CSVs) and its output is
advisory + ``provisional`` (ADR-0030 D5), the single disclosed assumption
(``productive_hours_per_day``) generalized from ``ledger.py:28-29``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from services.engine.economic_impact import (
    EconomicExposure,
    EconomicImpact,
    register_economic_producer,
)
from verticals.procurement.hero_demo.ledger import build_hero_impact_ledger

# The CSV columns the ฿ figures derive from (basis_refs provenance; ADR-0030 D3).
_BASIS_REFS = [
    "Asset.downtime_cost_per_hour_thb",
    "part_suppliable_by_supplier.quoted_unit_price_thb",
    "part_suppliable_by_supplier.lead_time_days",
    "PurchaseOrder.total_thb",
]


def _is_emergency_trigger(event: Mapping[str, Any]) -> bool:
    """Only the critical-failure / emergency-sourcing trigger has the baseline-vs-governed
    ฿ tradeoff the ledger models (OQ-C: never emit a ฿ figure for a calm-path event)."""
    return "failure" in str(event.get("event_type", "")) or event.get("severity") == "critical"


async def procurement_economic_impact(
    event: Mapping[str, Any], vertical: str
) -> EconomicImpact | None:
    """Compute the procurement ``expedite_tradeoff`` ฿ facet from committed CSV columns.

    Returns ``None`` for a non-emergency event (OQ-C — no anchor, no guess)."""
    if not _is_emergency_trigger(event):
        return None
    ledger = await build_hero_impact_ledger()
    base = ledger["baseline"]
    gov = ledger["governed"]
    baseline = EconomicExposure(
        label="on-AVL wait, preferred supplier (downtime + on-contract part cost)",
        exposure_thb=base["exposure_thb"],
        components={
            "downtime_thb": base["downtime_thb"],
            "part_cost_thb": base["part_cost_thb"],
        },
    )
    governed = EconomicExposure(
        label="off-AVL emergency sourcing (short-lead downtime + premium part cost)",
        exposure_thb=gov["exposure_thb"],
        components={
            "downtime_thb": gov["downtime_thb"],
            "part_cost_thb": gov["part_cost_thb"],
        },
    )
    return EconomicImpact(
        provisional=True,
        currency="THB",
        kind="expedite_tradeoff",
        baseline=baseline,
        governed=governed,
        net_benefit_thb=ledger["net_benefit_thb"],
        assumptions=[
            f"productive_hours_per_day = {ledger['productive_hours_per_day']} "
            "(modelling assumption; the CSVs carry cost/hour + lead-days, not a shift calendar)",
            "figures from the representative emergency-sourcing hero PO "
            "(OQ-C v1: per-event PO anchor resolution deferred to v2)",
        ],
        basis_refs=_BASIS_REFS,
    )


def register_procurement_economic_impact() -> None:
    """Register the procurement ฿-impact producer (the guarded optional import in
    ``discovery._register_vertical`` calls this)."""
    register_economic_producer("procurement", procurement_economic_impact)
