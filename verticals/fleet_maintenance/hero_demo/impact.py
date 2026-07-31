"""Fleet's View G money beat — the shipped ฿ producer, promoted to a demo payload.

PLAN-0098 D-A. Procurement's hero serves a two-sided supplier ledger whose every field
is a column of a committed CSV. Fleet has no CSV, so rather than invent supplier and
downtime figures to fill that shape, this module returns the facet the engine already
computes: ``fleet_maintenance_economic_impact`` (PR #994), which anchors on the repair
quote carried by the event itself.

**Nothing here recomputes the money.** The producer is imported and called, never
reimplemented, so the demo surface and the trace facet can never disagree about the
same repair. The two figures a reader sees are deliberately different kinds of number:

* ``quoted_repair_thb`` — MEASURED. The amount the garage quoted, off the event's own
  ``measured_value`` where ``unit == "THB"``.
* everything inside ``impact`` — MODELLED, and travelling with the ``assumptions`` that
  say so (ADR-0030 D3).

**No escape hatch.** The producer returns ``None`` when it cannot ground a figure — for
a non-quote event, or a quote at or under the partner's ฿30,000 comparison threshold.
This module does not paper over that with a zero or a placeholder side: it raises. A
demo that shows a confident ฿0 where the rule never applied is worse than a demo that
fails loudly, because only one of them gets noticed.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from services.api.models.demo import FleetHeroImpact
from verticals.fleet_maintenance.data_adapter import FleetMaintenanceSyntheticAdapter
from verticals.fleet_maintenance.economic_impact import fleet_maintenance_economic_impact

_VERTICAL = "fleet_maintenance"
_CURRENCY = "THB"

#: The hero repair — ฿48,000 on truck-01's axle, quoted at the roadside. It clears the
#: partner's ฿30,000 comparison threshold, so the three-quote rule applies AND the
#: doa_tier ladder's top rung resolves to เจ้าของกิจการ. The donor pins its hero the
#: same way (``_HERO_PO``); pinning is what makes the capture deterministic.
_HERO_EVENT_ID = "event-reading-02"


async def _hero_event(
    adapter: FleetMaintenanceSyntheticAdapter | None = None,
) -> dict[str, Any]:
    """The pinned hero event, or a loud failure if the fixture stopped carrying it."""
    adapter = adapter or FleetMaintenanceSyntheticAdapter()
    events = await adapter.fetch_objects("OperationalEvent")
    for event in events:
        if event.get("event_id") == _HERO_EVENT_ID:
            return dict(event)
    raise LookupError(
        f"the pinned hero event {_HERO_EVENT_ID!r} is not in the fleet synthetic dataset "
        f"({len(events)} events read). View G's money beat is anchored to that specific "
        "repair; picking a different event silently would change the demo's numbers."
    )


async def build_fleet_hero_impact(
    adapter: FleetMaintenanceSyntheticAdapter | None = None,
) -> FleetHeroImpact:
    """Fleet's View G money payload, from the real producer over the pinned hero event.

    Raises rather than returning a partial payload when the producer declines to ground
    a figure — see the module docstring on why a fabricated side is the worse failure.
    """
    event = await _hero_event(adapter)
    impact = await fleet_maintenance_economic_impact(event, _VERTICAL)
    if impact is None:
        raise ValueError(
            f"the fleet ฿ producer returned None for the pinned hero event "
            f"{_HERO_EVENT_ID!r} (quote {event.get('measured_value')!r} "
            f"{event.get('unit')!r}). It grounds a figure only for a repair quote above "
            "the partner's ฿30,000 comparison threshold — below it the rule never "
            "applied, so there is no baseline-vs-governed tradeoff to show. Re-pin the "
            "hero event; do not synthesise a side."
        )
    return FleetHeroImpact(
        provisional=True,
        vertical=_VERTICAL,
        currency=_CURRENCY,
        truck_id=str(event["truck_id"]),
        case_id=str(event["case_id"]),
        quoted_repair_thb=Decimal(str(event["measured_value"])),
        impact=impact,
    )
