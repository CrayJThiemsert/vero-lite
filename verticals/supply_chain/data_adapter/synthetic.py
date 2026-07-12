"""Deterministic synthetic dataset for the supply_chain vertical (ADR-006 §5 #4).

No external I/O and no randomness — every call returns the same data, so
demos and tests are reproducible. All identifiers are abstract (a generic
cold-chain logistics operator); no design-partner brand names or internal
codes appear here (PLAN-0005 PD-5 / §7.2; PLAN-0013 AC-safety).

Shapes match ``verticals/supply_chain/ontology/supply_chain_v0.yaml``:
Facility, Shipment, and OperationalEvent. Each Shipment carries a per-cargo-type
``temp_ceiling`` (ADR-016 FKP amendment 2026-07-12) — the judge bands each
shipment's latest reading against its OWN ceiling, not one blanket limit. Two
excursions land: the pharma shipment crosses its 8 °C ceiling (14.6 °C), and —
the per-cargo demo point — the frozen shipment WARMS to -11.8 °C after a
door-open alarm, above its -15 °C frozen ceiling though a blanket 8 °C limit
would clear it. The frozen warming reading is the timeline's **final beat** so
real-time anchoring (PLAN-0015 D1) leaves nothing dangling in the future.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

COLD_CHAIN_BREACH_CELSIUS = 14.6
"""A cold-chain temperature excursion on a pharma shipment — well above the
2-8 °C pharma limit (OCT_RECOMMEND_THRESHOLD=8 for the demo), so the synthetic
adapter and the recommender stay decoupled."""


def facilities() -> list[dict[str, Any]]:
    """Return the synthetic Facility records (geo-bearing — map-plottable)."""
    return [
        {
            "facility_id": "facility-coldhub-01",
            "name": "Central Cold Hub",
            "facility_type": "cold_storage",
            "lat": 13.69,
            "lng": 100.75,
        },
        {
            "facility_id": "facility-dc-01",
            "name": "Northern Distribution Center",
            "facility_type": "distribution_center",
            "lat": 13.92,
            "lng": 100.52,
        },
    ]


def shipments() -> list[dict[str, Any]]:
    """Return the synthetic Shipment records."""
    return [
        {
            "shipment_id": "shipment-pharma-01",
            "reference": "Vaccine Lot VX-1188",
            "cargo_type": "pharma",
            "temp_ceiling": 8.0,
            "payload_kg": 420.0,
            "status": "in_transit",
            "dispatched_date": date(2026, 5, 29),
            "facility_id": "facility-coldhub-01",
        },
        {
            "shipment_id": "shipment-produce-01",
            "reference": "Fresh Produce Pallet FP-204",
            "cargo_type": "produce",
            "temp_ceiling": 12.0,
            "payload_kg": 1200.0,
            "status": "at_facility",
            "dispatched_date": date(2026, 5, 30),
            "facility_id": "facility-coldhub-01",
        },
        {
            "shipment_id": "shipment-frozen-01",
            "reference": "Frozen Goods FZ-77",
            "cargo_type": "frozen",
            "temp_ceiling": -15.0,
            "payload_kg": 800.0,
            "status": "in_transit",
            "dispatched_date": date(2026, 5, 30),
            "facility_id": "facility-dc-01",
        },
        {
            "shipment_id": "shipment-biologic-01",
            "reference": "Biologic Sample BS-9",
            "cargo_type": "biologic",
            "temp_ceiling": 6.0,
            "payload_kg": 35.0,
            "status": "delayed",
            "dispatched_date": date(2026, 5, 28),
            "facility_id": "facility-dc-01",
        },
    ]


def operational_events() -> list[dict[str, Any]]:
    """Return the synthetic OperationalEvent records (readings + one alarm).

    The door-open alarm precedes the frozen shipment's warming
    reading (`event-reading-04`, the per-cargo flip), which is the last beat so
    real-time anchoring leaves no event in the future.
    """
    return [
        {
            "event_id": "event-reading-01",
            "event_type": "reading",
            "severity": "info",
            "measured_value": 4.2,
            "unit": "celsius",
            "description": "Vaccine Lot VX-1188 within the 2-8 °C pharma range.",
            "occurred_at": datetime(2026, 5, 31, 7, 0, tzinfo=UTC),
            "shipment_id": "shipment-pharma-01",
            "facility_id": "facility-coldhub-01",
        },
        {
            "event_id": "event-reading-02",
            "event_type": "reading",
            "severity": "info",
            "measured_value": -18.5,
            "unit": "celsius",
            "description": "Frozen Goods FZ-77 holding nominal frozen temperature.",
            "occurred_at": datetime(2026, 5, 31, 7, 5, tzinfo=UTC),
            "shipment_id": "shipment-frozen-01",
            "facility_id": "facility-dc-01",
        },
        {
            "event_id": "event-alarm-01",
            "event_type": "alarm",
            "severity": "error",
            "description": "Reefer door-open alarm on Frozen Goods FZ-77.",
            "occurred_at": datetime(2026, 5, 31, 8, 8, tzinfo=UTC),
            "shipment_id": "shipment-frozen-01",
            "facility_id": "facility-dc-01",
        },
        {
            "event_id": "event-reading-03",
            "event_type": "reading",
            "severity": "warn",
            "measured_value": COLD_CHAIN_BREACH_CELSIUS,
            "unit": "celsius",
            "description": "Vaccine Lot VX-1188 temperature above the 2-8 °C cold-chain limit.",
            "occurred_at": datetime(2026, 5, 31, 8, 10, tzinfo=UTC),
            "shipment_id": "shipment-pharma-01",
            "facility_id": "facility-coldhub-01",
        },
        {
            "event_id": "event-reading-04",
            "event_type": "reading",
            "severity": "warn",
            "measured_value": -11.8,
            "unit": "celsius",
            "description": "Frozen Goods FZ-77 warming after the door-open alarm — above "
            "its -15 °C frozen ceiling though still cold (a blanket 8 °C limit misses it).",
            "occurred_at": datetime(2026, 5, 31, 8, 12, tzinfo=UTC),
            "shipment_id": "shipment-frozen-01",
            "facility_id": "facility-dc-01",
        },
    ]
