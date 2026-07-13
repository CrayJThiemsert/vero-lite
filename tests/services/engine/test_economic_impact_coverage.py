"""AC-5 — the ADR-0030 D4-3 ≥3-vertical economic-facet build-completion marker
(PLAN-0071). THE enforcement test.

This is the enforcement that replaces ADR-016's promised-but-**never-built** N≥3
economic marker (ADR-0030 D4; the D4-4 lesson — an owned marker, named by THIS
AC, in the same breath as the promise). It asserts that ≥3 shipped verticals emit
the typed ``economic_impact`` facet.

Lifecycle: lands **RED** here (``xfail(strict=True)``) in PLAN-0071 **PR1** — no
per-vertical ฿ producers exist yet — and flips **GREEN** in **PR2 (Step 6)** when
the four producers register via discovery (the guard is removed there). A strict
xfail proves the assertion genuinely fails today, so the erosion class ADR-0030 D4
records cannot silently recur between this PLAN's acceptance and its build.

Deterministic-offline — assumption producers are pure; procurement reads committed
CSVs; no MS-S1, no live LLM.
"""

from __future__ import annotations

import pytest

from services.engine.discovery import discover_and_register
from services.engine.economic_impact import EconomicImpact, build_economic_steps

# A minimal representative trigger event per shipped vertical. In PR1 no producer is
# registered, so every ``build_economic_steps`` returns ``[]`` regardless of the event;
# in PR2 the producers (assumption-based for energy/supply_chain/aquaculture; anchor- or
# assumption-based for procurement) compute the facet from these.
_VERTICAL_EVENTS: dict[str, dict[str, object]] = {
    "energy": {
        "event_id": "cov-energy",
        "event_type": "reading",
        "measured_value": 105.0,
        "unit": "ampere",
        "asset_id": "asset-meter-01",
    },
    "supply_chain": {
        "event_id": "cov-sc",
        "event_type": "reading",
        "measured_value": -11.8,
        "unit": "celsius",
    },
    "aquaculture": {
        "event_id": "cov-aqua",
        "event_type": "reading",
        "measured_value": 3.4,
        "unit": "mg_per_l",
    },
    "procurement": {
        "event_id": "cov-proc",
        "event_type": "asset_failure",
        "equipment_id": "cnc-01",
    },
}


@pytest.mark.xfail(
    strict=True,
    reason="AC-5 RED in PLAN-0071 PR1 — the per-vertical economic producers land in PR2 "
    "(Step 5); this marker's guard is removed there and it flips GREEN at N=4.",
)
async def test_at_least_three_verticals_emit_the_economic_facet() -> None:
    discover_and_register()
    emitting = 0
    for vertical, event in _VERTICAL_EVENTS.items():
        steps = await build_economic_steps(event, vertical)
        econ = [s for s in steps if s.kind == "economic_impact"]
        if econ:
            # producer-side type enforcement: the detail MUST validate as EconomicImpact
            EconomicImpact.model_validate(econ[0].detail)
            emitting += 1
    assert emitting >= 3, f"only {emitting} vertical(s) emit the economic_impact facet (need ≥3)"
