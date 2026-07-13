"""AC-4 / AC-6(a) — the four per-vertical economic-impact producers (PLAN-0071 PR2).

Each producer computes the engine-owned ``EconomicImpact`` for its vertical
(SD-F: vertical-side computation of the engine-owned type). energy / supply_chain /
aquaculture are assumptions-first (SD-B) — every ฿ input a named ``assumptions``
entry, values per ratified SD-G; procurement derives from committed CSV columns via
the demo ledger with ``basis_refs`` citing the columns (OQ-C v1: the hero-PO exemplar
for the emergency trigger, ``None`` for a calm-path event).

Invariants asserted here: the ``detail`` validates as ``EconomicImpact`` (the
arithmetic ``model_validator`` holds), ``provisional is True`` (AC-6a), the ``kind``
label matches the ADR-0030 D3 table, and the SD-G net-benefit arithmetic is exact.
Deterministic-offline — pure functions / committed CSVs, no MS-S1, no live LLM.
"""

from __future__ import annotations

from decimal import Decimal

from services.engine.economic_impact import EconomicImpact
from verticals.aquaculture.economic_impact import aquaculture_economic_impact
from verticals.energy.economic_impact import energy_economic_impact
from verticals.procurement.economic_impact import procurement_economic_impact
from verticals.procurement.hero_demo.ledger import build_hero_impact_ledger
from verticals.supply_chain.economic_impact import supply_chain_economic_impact

_READING = {"event_id": "e1", "event_type": "reading", "measured_value": 1.0}


async def test_energy_producer_avoided_outage_sdg_arithmetic() -> None:
    impact = await energy_economic_impact(_READING, "energy")
    assert impact is not None
    assert impact.provisional is True  # AC-6(a)
    assert impact.currency == "THB"
    assert impact.kind == "avoided_outage"  # ADR-0030 D3 table
    assert impact.baseline.exposure_thb == Decimal("480000")
    assert impact.governed.exposure_thb == Decimal("75000")
    assert impact.net_benefit_thb == Decimal("405000")  # SD-G
    assert impact.assumptions  # assumptions-first: every ฿ input disclosed
    # round-trips through the JSON detail the helper emits (AC-8)
    assert EconomicImpact.model_validate(impact.model_dump(mode="json")) == impact


async def test_supply_chain_producer_spoilage_avoided_sdg_arithmetic() -> None:
    impact = await supply_chain_economic_impact(_READING, "supply_chain")
    assert impact is not None
    assert impact.provisional is True
    assert impact.kind == "spoilage_avoided"
    assert impact.baseline.exposure_thb == Decimal("2400000")
    assert impact.governed.exposure_thb == Decimal("280000")
    assert impact.net_benefit_thb == Decimal("2120000")  # SD-G
    assert impact.assumptions


async def test_aquaculture_producer_mortality_avoided_sdg_arithmetic() -> None:
    impact = await aquaculture_economic_impact(_READING, "aquaculture")
    assert impact is not None
    assert impact.provisional is True
    assert impact.kind == "mortality_avoided"
    assert impact.baseline.exposure_thb == Decimal("297500")
    assert impact.governed.exposure_thb == Decimal("50500")
    assert impact.net_benefit_thb == Decimal("247000")  # SD-G
    assert impact.assumptions


async def test_procurement_producer_expedite_tradeoff_from_csv_columns() -> None:
    event = {"event_id": "p1", "event_type": "failure", "severity": "critical"}
    impact = await procurement_economic_impact(event, "procurement")
    assert impact is not None
    assert impact.provisional is True
    assert impact.kind == "expedite_tradeoff"  # ADR-0030 D3 table
    # real-column v1: the figures equal the committed-CSV ledger computation
    ledger = await build_hero_impact_ledger()
    assert impact.net_benefit_thb == ledger["net_benefit_thb"]
    assert impact.net_benefit_thb > 0
    assert impact.basis_refs  # cites the source CSV columns (OQ-C provenance)
    assert impact.assumptions  # the single disclosed productive_hours_per_day assumption


async def test_procurement_producer_returns_none_for_calm_path_event() -> None:
    """OQ-C: a non-emergency event has no baseline-vs-governed ฿ tradeoff — facet absent,
    never a guessed figure."""
    calm = {"event_id": "p2", "event_type": "low_stock", "severity": "warn"}
    assert await procurement_economic_impact(calm, "procurement") is None
