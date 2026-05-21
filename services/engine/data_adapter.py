"""DataAdapter Protocol — per-vertical data ingress contract (ADR-007 D1).

An async-first, ``@runtime_checkable`` Protocol that every vertical
implements under ``verticals/<name>/data_adapter/``. The engine never
instantiates a DataAdapter directly — verticals register an
implementation through ``services/engine/registry.py``.

The ADR-007 D1 code block uses bare ``dict`` / ``list[dict]``; those are
parameterised to ``dict[str, Any]`` here because ``mypy --strict``
forbids unparameterised generics. ``stream_events`` is a plain method
returning an ``AsyncIterator`` (consumed with ``async for``), not a
coroutine — matching the ADR docstring "async iterator" and the
PLAN-0005 §7.2 usage (``stream_events("reading")`` is iterated, not
awaited).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DataAdapter(Protocol):
    """Per-vertical data ingress contract (ADR-007 D1).

    Implementations live in ``verticals/<name>/data_adapter/``. The
    engine maps the returned raw dicts to typed entities via the
    generated ontology models.
    """

    vertical_name: str
    """Stable identifier matching the ``verticals/<name>/`` directory."""

    async def fetch_objects(
        self,
        object_type: str,
        filter_expr: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Return raw object dicts; engine maps them to typed entities via ontology."""
        ...

    async def fetch_links(
        self,
        link_type: str,
        from_pk: str | None = None,
        to_pk: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return raw link dicts (``from_pk``, ``to_pk``, metadata)."""
        ...

    def stream_events(
        self,
        event_type: str,
        since: datetime | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Async iterator over OperationalEvent-shaped dicts.

        Implementations may poll or subscribe; the engine treats both
        uniformly. Consumed with ``async for`` — the call itself is not
        awaited.
        """
        ...

    async def health_check(self) -> dict[str, Any]:
        """Return adapter status; the engine surfaces it in the operational map."""
        ...
