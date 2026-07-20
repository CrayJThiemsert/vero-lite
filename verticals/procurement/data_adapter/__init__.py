"""Procurement vertical — DataAdapters (PLAN-0016 scaffold; PLAN-0084 SD-F primary swap).

Two adapters live here:

* ``FastenalCsvAdapter`` (``fastenal_csv.py``) — the PRIMARY adapter since
  PLAN-0084 SD-F (Cray-ratified s155): the hero-demo CSV dataset (AST-* assets,
  the Rayong plant) that the hero surfaces, the operate seed and the runbook
  narrate. ``register_procurement_adapter`` (the discovery entry point) now
  registers THIS, so the map/objects/NL-query and the run ``subject`` linkage
  share one vocabulary.
* ``ProcurementSyntheticAdapter`` (below, over ``synthetic.py``) — the original
  scaffold-generated synthetic set (equip-*), retained for direct-module test
  harnesses; no longer what discovery serves.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from services.engine import demo_events
from services.engine.registry import registry
from verticals.procurement.data_adapter import synthetic

_VERTICAL = "procurement"


def _operational_events() -> list[dict[str, Any]]:
    """The per-process live OperationalEvent view (PLAN-0015 D1/D2).

    Routes synthetic events through ``demo_events`` so real-time anchoring and
    the execute-time recovery reading apply; with the anchor flag off and no
    execution it equals ``synthetic.operational_events()`` (deterministic).
    """
    return demo_events.events(_VERTICAL, synthetic.operational_events)


_OBJECT_SOURCES = {
    **synthetic.OBJECT_SOURCES,
    "OperationalEvent": _operational_events,
}


class ProcurementSyntheticAdapter:
    """Deterministic synthetic DataAdapter for the procurement vertical.

    Conforms structurally to ``services.engine.data_adapter.DataAdapter``.
    No external I/O — every call returns the synthetic dataset, so demos
    and tests are reproducible.
    """

    vertical_name = "procurement"

    async def fetch_objects(
        self,
        object_type: str,
        filter_expr: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Return synthetic object dicts for ``object_type`` (unknown -> empty)."""
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
        """Return link dicts for ``link_type`` (Phase 2 synthetic: none)."""
        return []

    async def stream_events(
        self,
        event_type: str,
        since: datetime | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield synthetic OperationalEvent dicts of ``event_type``."""
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


def register_procurement_adapter() -> Any:
    """Register procurement's PRIMARY adapter on the process-wide registry.

    PLAN-0084 SD-F (Cray-ratified s155): the primary adapter is the
    ``FastenalCsvAdapter`` — the SAME dataset the hero demo, the operate seed and
    the runbook narrate (AST-* assets, the Rayong plant), so the map, /objects,
    NL-query grounding and the run ``subject`` linkage all share ONE vocabulary.
    The synthetic adapter above stays in-tree for direct-module test harnesses
    (e.g. ``test_procurement_vertical``), but is no longer what discovery serves.
    """
    from verticals.procurement.data_adapter.fastenal_csv import FastenalCsvAdapter

    adapter = FastenalCsvAdapter()
    registry.register_adapter(adapter)
    return adapter
