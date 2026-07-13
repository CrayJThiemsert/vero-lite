"""Deterministic synthetic dataset for the aquaculture vertical (PLAN-0016 Step 5).

Scaffolded by ``vero-lite new-vertical`` (PLAN-0016) then **human-reviewed +
enriched** (ADR-0015 D5) into the demo timeline below. No external I/O and no
randomness — every call returns the same data, so demos and tests are
reproducible. All identifiers are abstract (a generic SE-Asian shrimp/finfish
operator); no design-partner brand names appear here.

Shapes match ``verticals/aquaculture/ontology/aquaculture_v0.yaml``: Farm, Pond,
and OperationalEvent. The events trace a single nighttime dissolved-oxygen (DO)
incident on POND-07 — a baseline, a declining DO trend (info -> warn), a
concurrent paddlewheel-aerator alarm, and — as the timeline's **final beat** —
the DO crash the rule-based recommender escalates, so the demo reads as
build-up -> climax. Unlike energy/supply_chain (which breach *above* a
threshold), aquaculture breaches **below** it: a DO reading of 3.2 mg/L falls
under the 4 mg/L safe threshold (``OCT_RECOMMEND_DIRECTION=below``,
PLAN-0016 Step 0). The breach is the **latest** event so real-time anchoring
(PLAN-0015 D1) leaves nothing in the future. **Only** the crash trips an action:
the recommender escalates any reading whose ``measured_value`` is <= the
threshold, so every non-breach reading is kept strictly above it.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

DO_CRASH_MG_L = 3.2
"""The breaching dissolved-oxygen reading on POND-07 — below the 4 mg/L safe
threshold (OCT_RECOMMEND_THRESHOLD=4, direction=below) so a single nighttime
crash escalates while every nominal reading (kept > 4 mg/L) stays silent."""


def farms() -> list[dict[str, Any]]:
    """Return the synthetic Farm records (geo-bearing — map-plottable)."""
    return [
        {
            "farm_id": "farm-bayfront-01",
            "name": "Bayfront Shrimp Farm",
            "farm_type": "coastal",
            "lat": 13.52,
            "lng": 100.27,
        },
        {
            "farm_id": "farm-inland-01",
            "name": "Riverside Tilapia Farm",
            "farm_type": "inland",
            "lat": 14.21,
            "lng": 100.58,
        },
    ]


def ponds() -> list[dict[str, Any]]:
    """Return the synthetic Pond records."""
    return [
        {
            "pond_id": "pond-07",
            "name": "Pond 07",
            "pond_type": "grow_out",
            "area_sqm": 4000.0,
            "stocking_density": 85.0,
            "do_floor": 4.0,
            "species": "whiteleg_shrimp",
            "status": "active",
            "site_id": "farm-bayfront-01",
        },
        {
            "pond_id": "pond-03",
            "name": "Pond 03",
            "pond_type": "grow_out",
            "area_sqm": 4200.0,
            "stocking_density": 80.0,
            "do_floor": 4.0,
            "species": "whiteleg_shrimp",
            "status": "active",
            "site_id": "farm-bayfront-01",
        },
        {
            "pond_id": "pond-11",
            "name": "Pond 11",
            "pond_type": "nursery",
            "area_sqm": 1200.0,
            "stocking_density": 140.0,
            "do_floor": 4.5,
            "species": "tiger_prawn",
            "status": "active",
            "site_id": "farm-inland-01",
        },
        {
            "pond_id": "pond-05",
            "name": "Pond 05",
            "pond_type": "grow_out",
            "area_sqm": 3800.0,
            "stocking_density": 0.0,
            "do_floor": 3.0,
            "species": "tilapia",
            "status": "fallow",
            "site_id": "farm-inland-01",
        },
    ]


def operational_events() -> list[dict[str, Any]]:
    """Return the synthetic OperationalEvent records, in chronological order.

    One nighttime DO incident on POND-07: nominal baselines on healthy ponds, a
    declining DO trend (info -> warn), a paddlewheel-aerator alarm, and — last —
    the DO crash (``event-reading-do-crash``, 3.2 mg/L <= the 4 mg/L threshold ->
    drives the recommender). The crash is the final beat so real-time anchoring
    (PLAN-0015 D1) leaves no event in the future; the recovery reading is
    injected on execute (PLAN-0015 D2), not returned here. Every non-breach
    reading is > the threshold so only the crash escalates (see module docstring).
    """
    return [
        # Healthy ponds — a normal operational stream so the per-site timeline is
        # populated for healthy ponds too (mirrors the energy healthy-site beat).
        {
            "event_id": "event-reading-03",
            "event_type": "reading",
            "severity": "info",
            "measured_value": 6.9,
            "unit": "mg/L",
            "description": "Pond 03 dissolved oxygen nominal.",
            "occurred_at": datetime(2026, 6, 1, 23, 30, tzinfo=UTC),
            "pond_id": "pond-03",
            "site_id": "farm-bayfront-01",
        },
        {
            "event_id": "event-reading-11",
            "event_type": "reading",
            "severity": "info",
            "measured_value": 6.5,
            "unit": "mg/L",
            "description": "Pond 11 dissolved oxygen nominal.",
            "occurred_at": datetime(2026, 6, 1, 23, 40, tzinfo=UTC),
            "pond_id": "pond-11",
            "site_id": "farm-inland-01",
        },
        # POND-07 incident build-up.
        {
            "event_id": "event-reading-01",
            "event_type": "reading",
            "severity": "info",
            "measured_value": 6.8,
            "unit": "mg/L",
            "description": "Pond 07 dissolved oxygen nominal at dusk.",
            "occurred_at": datetime(2026, 6, 1, 23, 50, tzinfo=UTC),
            "pond_id": "pond-07",
            "site_id": "farm-bayfront-01",
        },
        {
            "event_id": "event-reading-02",
            "event_type": "reading",
            "severity": "info",
            "measured_value": 5.4,
            "unit": "mg/L",
            "description": "Pond 07 dissolved oxygen dipping after the night feed.",
            "occurred_at": datetime(2026, 6, 2, 0, 40, tzinfo=UTC),
            "pond_id": "pond-07",
            "site_id": "farm-bayfront-01",
        },
        {
            "event_id": "event-reading-04",
            "event_type": "reading",
            "severity": "warn",
            "measured_value": 4.6,
            "unit": "mg/L",
            "description": "Pond 07 dissolved oxygen approaching the 4 mg/L safe limit.",
            "occurred_at": datetime(2026, 6, 2, 1, 30, tzinfo=UTC),
            "pond_id": "pond-07",
            "site_id": "farm-bayfront-01",
        },
        {
            "event_id": "event-alarm-01",
            "event_type": "alarm",
            "severity": "error",
            "description": "Pond 07 paddlewheel aerator stalled (motor fault).",
            "occurred_at": datetime(2026, 6, 2, 1, 45, tzinfo=UTC),
            "pond_id": "pond-07",
            "site_id": "farm-bayfront-01",
        },
        # PLAN-0068 PR2 SD-3 flip seed: pond-11 (tiger_prawn) warms to 4.2 mg/L —
        # only `watch` under the retired blanket 4.0 floor but `breach` under its
        # OWN per-species 4.5 floor (the demo-visible per-species win). Timed 01:55,
        # BEFORE the 02:00 pond-07 crash, so the crash stays the timeline's final
        # beat (real-time anchoring PLAN-0015 D1 intact); 4.2 > 4.0 so the reactive
        # recommender (env threshold) still does NOT trip on it.
        {
            "event_id": "event-reading-12",
            "event_type": "reading",
            "severity": "warn",
            "measured_value": 4.2,
            "unit": "mg/L",
            "description": "Pond 11 dissolved oxygen dipped after a warm night.",
            "occurred_at": datetime(2026, 6, 2, 1, 55, tzinfo=UTC),
            "pond_id": "pond-11",
            "site_id": "farm-inland-01",
        },
        {
            "event_id": "event-reading-do-crash",
            "event_type": "reading",
            "severity": "critical",
            "measured_value": DO_CRASH_MG_L,
            "unit": "mg/L",
            "description": "Pond 07 dissolved oxygen crashed below the 4 mg/L safe threshold.",
            "occurred_at": datetime(2026, 6, 2, 2, 0, tzinfo=UTC),
            "pond_id": "pond-07",
            "site_id": "farm-bayfront-01",
        },
        # The post-mitigation recovery reading is NOT pre-baked here (PLAN-0015
        # D2): it is injected as the effect of executing the decision (start the
        # emergency aerator) at real execute-time, so the timeline only resolves
        # after the operator acts.
    ]


OBJECT_SOURCES = {
    "Farm": farms,
    "Pond": ponds,
}
