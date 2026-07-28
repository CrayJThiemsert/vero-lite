"""The confirmed-PM view over the Truck records (PLAN-0096 Step 9 / AC-10).

The seam where a human's confirmation becomes something the calm path can see. It is
deliberately shaped like ``services.engine.demo_events`` — a per-process live view
layered over the otherwise-deterministic synthetic base — because the two solve the
same problem: an adapter object source is a plain synchronous callable, and the thing
we want to layer over it lives elsewhere.

**Why a cached view instead of reading the database per fetch.** ``fetch_objects`` is
called on every query step of every run, and the fleet's Truck source is read by both
procedures. Opening a session there would put a database round-trip on the hot path,
and — the deciding reason — it would make the DB-LESS demo and the whole offline test
suite depend on a live Postgres. PLAN-0095 exists precisely so the image boots and
serves the synthetic OCT demo with no database at all; a Truck read that could not
answer without one would undo it. So the database is touched at exactly two moments:
app startup, and immediately after a human confirms something.

**The honest cost, stated rather than hidden.** This view is per-process. Two API
processes would each hold their own copy until the next refresh, and a confirm made in
one is not visible in the other until then. That is acceptable for a single-process
pilot and it is NOT acceptable silently, so :func:`status` reports what the view holds
and when it was last loaded, and the adapter's ``health_check`` surfaces it. When this
becomes a multi-process deployment the fix is a read-through with a short TTL, not a
bigger cache.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from services.db.pm_import import apply_overrides, confirmed_truck_values

#: {truck_id: {field: value}} — empty until a refresh loads confirmed rows. Empty is
#: the correct starting state: before anyone has confirmed anything, the ontology must
#: show exactly what it showed before this feature existed.
_overrides: dict[str, dict[str, float]] = {}

#: Whether a refresh has ever completed, and whether the last one succeeded. Kept so
#: "no overrides" and "could not read the overrides" are distinguishable — on an
#: evidence surface those are different answers, and a view that reported them
#: identically would be the reassuring-empty-state lie in a new place.
_loaded: bool = False
_last_error: str | None = None


async def refresh(session: AsyncSession) -> dict[str, dict[str, float]]:
    """Reload the view from confirmed ``pm_import_row`` rows. Returns what it loaded."""
    global _loaded, _last_error
    values = await confirmed_truck_values(session)
    _overrides.clear()
    _overrides.update(values)
    _loaded = True
    _last_error = None
    return dict(_overrides)


def record_unavailable(error: str) -> None:
    """Note that a refresh could not run (no database at startup, say).

    The view keeps whatever it already had — a stale confirmed odometer is better than
    silently reverting a truck to a fixture value — and says so through :func:`status`.
    """
    global _last_error
    _last_error = error


def apply(trucks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Overlay the confirmed values onto truck records (pure; input untouched)."""
    return apply_overrides(trucks, _overrides)


def overrides() -> Mapping[str, Mapping[str, float]]:
    """The current view, read-only — for tests and the health check."""
    return {truck_id: dict(fields) for truck_id, fields in _overrides.items()}


def status() -> dict[str, Any]:
    """What this view holds and whether it is trustworthy, for ``health_check``."""
    return {
        "loaded": _loaded,
        "trucks_with_confirmed_values": len(_overrides),
        "last_error": _last_error,
    }


def reset() -> None:
    """Drop the view. Tests call this between cases (mirrors ``demo_events.reset``)."""
    global _loaded, _last_error
    _overrides.clear()
    _loaded = False
    _last_error = None
