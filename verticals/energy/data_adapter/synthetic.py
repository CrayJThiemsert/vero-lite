"""Deterministic synthetic dataset for the energy vertical (ADR-006 §5 #4).

No external I/O and no randomness — every call returns the same data, so
demos and tests are reproducible. All identifiers are abstract (the
"regional energy operator" framing); no design-partner brand names or
internal codes appear here (PLAN-0005 PD-5 / §7.2).

Shapes match ``verticals/energy/ontology/energy_v0.yaml``: Site, Asset,
and OperationalEvent. The reading events include one battery
over-temperature crossing the rule-based recommender escalates.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

OVERTEMP_READING_CELSIUS = 96.5
"""An over-temperature battery reading — well above any sane threshold so
the synthetic adapter and the commit-5 recommender stay decoupled."""


def sites() -> list[dict[str, Any]]:
    """Return the synthetic Site records."""
    return [
        {
            "site_id": "site-substation-01",
            "name": "North Substation",
            "site_type": "substation",
            "lat": 13.75,
            "lng": 100.50,
        },
        {
            "site_id": "site-microgrid-01",
            "name": "Riverside Microgrid",
            "site_type": "microgrid",
            "lat": 13.81,
            "lng": 100.56,
        },
    ]


def assets() -> list[dict[str, Any]]:
    """Return the synthetic Asset records."""
    return [
        {
            "asset_id": "asset-battery-01",
            "name": "Battery Bank A",
            "asset_type": "battery",
            "capacity_kw": 250.0,
            "status": "active",
            "install_date": date(2024, 3, 15),
            "site_id": "site-substation-01",
        },
        {
            "asset_id": "asset-inverter-01",
            "name": "Inverter Unit A",
            "asset_type": "inverter",
            "capacity_kw": 500.0,
            "status": "active",
            "install_date": date(2024, 4, 1),
            "site_id": "site-substation-01",
        },
        {
            "asset_id": "asset-battery-02",
            "name": "Battery Bank B",
            "asset_type": "battery",
            "capacity_kw": 250.0,
            "status": "active",
            "install_date": date(2024, 5, 20),
            "site_id": "site-microgrid-01",
        },
        {
            "asset_id": "asset-meter-01",
            "name": "Feeder Meter A",
            "asset_type": "meter",
            "status": "active",
            "install_date": date(2024, 2, 10),
            "site_id": "site-microgrid-01",
        },
    ]


def operational_events() -> list[dict[str, Any]]:
    """Return the synthetic OperationalEvent records (readings + one alarm)."""
    return [
        {
            "event_id": "event-reading-01",
            "event_type": "reading",
            "severity": "info",
            "measured_value": 32.4,
            "unit": "celsius",
            "description": "Battery Bank A temperature nominal.",
            "occurred_at": datetime(2026, 5, 21, 8, 0, tzinfo=UTC),
            "asset_id": "asset-battery-01",
            "site_id": "site-substation-01",
        },
        {
            "event_id": "event-reading-02",
            "event_type": "reading",
            "severity": "info",
            "measured_value": 41.7,
            "unit": "celsius",
            "description": "Battery Bank B temperature nominal.",
            "occurred_at": datetime(2026, 5, 21, 8, 5, tzinfo=UTC),
            "asset_id": "asset-battery-02",
            "site_id": "site-microgrid-01",
        },
        {
            "event_id": "event-reading-03",
            "event_type": "reading",
            "severity": "warn",
            "measured_value": OVERTEMP_READING_CELSIUS,
            "unit": "celsius",
            "description": "Battery Bank A temperature above the safe operating range.",
            "occurred_at": datetime(2026, 5, 21, 8, 10, tzinfo=UTC),
            "asset_id": "asset-battery-01",
            "site_id": "site-substation-01",
        },
        {
            "event_id": "event-alarm-01",
            "event_type": "alarm",
            "severity": "error",
            "description": "Inverter Unit A communication loss.",
            "occurred_at": datetime(2026, 5, 21, 8, 12, tzinfo=UTC),
            "asset_id": "asset-inverter-01",
            "site_id": "site-substation-01",
        },
    ]
