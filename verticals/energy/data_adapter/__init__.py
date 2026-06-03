"""Energy vertical — synthetic DataAdapter (ADR-006 §5 #4, PLAN-0005 §6.2).

A deterministic, no-network DataAdapter implementation for the energy
vertical. It serves the synthetic dataset in ``synthetic.py`` as raw
object dicts and streams OperationalEvent dicts — including one
over-temperature reading for the rule-based recommender to escalate.

``register_energy_adapter`` registers an instance on the process-wide
registry (OQ-6: explicit registration).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from services.engine import demo_events
from services.engine.registry import registry
from verticals.energy.data_adapter import synthetic

_VERTICAL = "energy"


def _operational_events() -> list[dict[str, Any]]:
    """The per-process live OperationalEvent view (PLAN-0015 D1/D2).

    Routes the synthetic events through ``demo_events`` so real-time anchoring
    and the execute-time recovery reading apply; with the anchor flag off and no
    execution it equals ``synthetic.operational_events()`` (deterministic).
    """
    return demo_events.events(_VERTICAL, synthetic.operational_events)


_OBJECT_SOURCES = {
    "Asset": synthetic.assets,
    "Site": synthetic.sites,
    "OperationalEvent": _operational_events,
}


class EnergySyntheticAdapter:
    """Deterministic synthetic DataAdapter for the energy vertical.

    Conforms structurally to ``services.engine.data_adapter.DataAdapter``.
    No external I/O — every call returns the synthetic dataset, so demos
    and tests are reproducible.
    """

    vertical_name = "energy"

    async def fetch_objects(
        self,
        object_type: str,
        filter_expr: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Return synthetic object dicts for ``object_type`` (unknown -> empty).

        ``filter_expr`` is accepted for protocol conformance but ignored by
        the Phase 2 synthetic adapter; ``limit`` truncates the result.
        """
        source = _OBJECT_SOURCES.get(object_type)
        if source is None:
            return []
        return source()[:limit]

    async def fetch_links(
        self,
        link_type: str,
        from_pk: str | None = None,
        to_pk: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return link dicts for ``link_type``.

        The Phase 2 synthetic adapter does not materialise links — every
        relationship is derivable from the foreign-key fields on the
        objects themselves — so this returns an empty list.
        """
        return []

    async def stream_events(
        self,
        event_type: str,
        since: datetime | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield synthetic OperationalEvent dicts of ``event_type``.

        When ``since`` (a timezone-aware datetime) is given, only events
        at or after it are yielded.
        """
        for event in _operational_events():
            if event["event_type"] != event_type:
                continue
            if since is not None and event["occurred_at"] < since:
                continue
            yield event

    async def health_check(self) -> dict[str, Any]:
        """Report adapter status and the synthetic record counts."""
        return {
            "status": "ok",
            "vertical": self.vertical_name,
            "synthetic": True,
            "object_counts": {name: len(src()) for name, src in _OBJECT_SOURCES.items()},
        }


def register_energy_adapter() -> EnergySyntheticAdapter:
    """Register a fresh EnergySyntheticAdapter on the process-wide registry."""
    adapter = EnergySyntheticAdapter()
    registry.register_adapter(adapter)
    return adapter
