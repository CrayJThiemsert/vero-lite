"""AC-4 / AC-6(a) — the per-vertical economic-impact producers (PLAN-0071 PR2; fleet s195).

Each producer computes the engine-owned ``EconomicImpact`` for its vertical
(SD-F: vertical-side computation of the engine-owned type). energy / supply_chain /
aquaculture are assumptions-first (SD-B) — every ฿ input a named ``assumptions``
entry, values per ratified SD-G; procurement derives from committed CSV columns via
the demo ledger with ``basis_refs`` citing the columns (OQ-C v1: the hero-PO exemplar
for the emergency trigger, ``None`` for a calm-path event). fleet_maintenance is
**event-anchored** — the ฿ comes off the triggering repair-quote event itself, gated on
the partner's own ฿30,000 threshold imported from ``sourcing.py``.

Invariants asserted here: the ``detail`` validates as ``EconomicImpact`` (the
arithmetic ``model_validator`` holds), ``provisional is True`` (AC-6a), the ``kind``
label matches the ADR-0030 D3 table, and the SD-G net-benefit arithmetic is exact.
Deterministic-offline — pure functions / committed CSVs, no MS-S1, no live LLM.
"""

from __future__ import annotations

from decimal import Decimal

from services.engine.discovery import discover_and_register
from services.engine.economic_impact import EconomicImpact, build_economic_steps
from verticals.aquaculture.economic_impact import aquaculture_economic_impact
from verticals.energy.economic_impact import energy_economic_impact
from verticals.fleet_maintenance.data_adapter.synthetic import operational_events
from verticals.fleet_maintenance.economic_impact import fleet_maintenance_economic_impact
from verticals.fleet_maintenance.sourcing import THREE_QUOTE_THRESHOLD_THB
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


async def test_procurement_producer_fires_on_the_hero_intake_seed() -> None:
    """PLAN-0073 AC-2 (SD-1a): the ENRICHED hero intake seed carries ``event_type``, so the
    producer FIRES on the actual governed-run entity (not just a hand-built event dict) — the
    facet rides the real hero path, not a render-side fabrication. Before SD-1a the seed carried
    no ``event_type``/``severity`` and the guard returned ``None``."""
    from verticals.procurement.data_adapter.fastenal_csv import FastenalCsvAdapter
    from verticals.procurement.hero_demo.run import _intake_seed

    seed = await _intake_seed(FastenalCsvAdapter())
    impact = await procurement_economic_impact(seed, "procurement")
    assert impact is not None
    assert impact.kind == "expedite_tradeoff"


async def test_procurement_producer_returns_none_for_calm_path_event() -> None:
    """OQ-C: a non-emergency event has no baseline-vs-governed ฿ tradeoff — facet absent,
    never a guessed figure."""
    calm = {"event_id": "p2", "event_type": "low_stock", "severity": "warn"}
    assert await procurement_economic_impact(calm, "procurement") is None


async def test_fleet_producer_overpay_avoided_from_the_events_own_quote() -> None:
    """Event-anchored v1: the ฿ comes off the triggering event, not an exemplar. The
    ฿48,000 axle quote clears the partner's ฿30,000 threshold, so the facet is emitted
    with the Cray-ruled 15% recovery — ฿7,200 — and the arithmetic model_validator holds."""
    event = {"event_id": "f1", "event_type": "reading", "measured_value": 48000.0, "unit": "THB"}
    impact = await fleet_maintenance_economic_impact(event, "fleet_maintenance")
    assert impact is not None
    assert impact.provisional is True  # AC-6(a)
    assert impact.currency == "THB"
    assert impact.kind == "overpay_avoided"
    assert impact.baseline.exposure_thb == Decimal("48000")
    assert impact.governed.exposure_thb == Decimal("40800")
    assert impact.net_benefit_thb == Decimal("7200")  # 15% of the uncompared quote
    assert impact.basis_refs  # cites the event field + the two partner constants
    assert impact.assumptions
    assert EconomicImpact.model_validate(impact.model_dump(mode="json")) == impact


async def test_fleet_producer_reads_the_threshold_from_sourcing_not_a_copy() -> None:
    """The gate boundary is the partner's own ฿30,000 (Q10), IMPORTED from ``sourcing.py``.

    Asserted against the imported constant rather than the literal 30000 on purpose: if
    the partner revises his answer, ``sourcing.py`` is the one place it changes and this
    test follows it instead of pinning a stale number the producer no longer uses.
    """
    at_threshold = {"event_id": "f2", "unit": "THB", "measured_value": THREE_QUOTE_THRESHOLD_THB}
    just_over = {"event_id": "f3", "unit": "THB", "measured_value": THREE_QUOTE_THRESHOLD_THB + 1}
    # at/under the threshold the rule never applied — no tradeoff to model, facet ABSENT
    assert await fleet_maintenance_economic_impact(at_threshold, "fleet_maintenance") is None
    assert await fleet_maintenance_economic_impact(just_over, "fleet_maintenance") is not None


async def test_fleet_producer_never_reads_a_non_money_reading_as_baht() -> None:
    """The ``unit`` guard is load-bearing: the fleet feed also carries odometer readings,
    and a producer that ignored ``unit`` would emit a confident ฿ figure for a kilometre
    count — a large, wrong, entirely plausible-looking number."""
    odometer = {"event_id": "f4", "event_type": "reading", "measured_value": 412000.0, "unit": "km"}
    assert await fleet_maintenance_economic_impact(odometer, "fleet_maintenance") is None
    unitless = {"event_id": "f5", "event_type": "reading", "measured_value": 412000.0}
    assert await fleet_maintenance_economic_impact(unitless, "fleet_maintenance") is None


async def test_fleet_facet_rides_the_real_committed_fixture_events() -> None:
    """REAL producer driven through the REAL consumer on the REAL committed fixture.

    Not a hand-built event dict: ``operational_events()`` is what the fleet adapter
    actually serves, and ``build_economic_steps`` is what ``recommend()`` actually calls.
    The expected set is DERIVED from the fixture rather than pinned to a literal, so a
    new fixture row is covered automatically instead of silently escaping the assertion.
    """
    discover_and_register()
    events = operational_events()
    expected = {
        str(e["event_id"])
        for e in events
        if str(e.get("unit")) == "THB"
        and Decimal(str(e["measured_value"])) > THREE_QUOTE_THRESHOLD_THB
    }
    # anti-vacuity: a fixture that stopped carrying an over-threshold quote would make
    # every assertion below trivially true, so the test would pass while proving nothing.
    assert expected, "the committed fixture carries no over-threshold ฿ quote — test is vacuous"

    emitting: set[str] = set()
    for event in events:
        steps = await build_economic_steps(event, "fleet_maintenance")
        econ = [s for s in steps if s.kind == "economic_impact"]
        if not econ:
            continue
        emitting.add(str(event["event_id"]))
        impact = EconomicImpact.model_validate(econ[0].detail)
        assert impact.kind == "overpay_avoided"
        assert impact.net_benefit_thb > 0
    assert emitting == expected
