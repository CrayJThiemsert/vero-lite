"""The live-case view over the OperationalEvent stream (PLAN-0096 Step 8, item 2).

Shaped deliberately like :mod:`verticals.fleet_maintenance.pm_projection`, which is
the repo's sanctioned DB → object-source overlay, for the same reason it exists: an
adapter object source is a plain synchronous callable, and the rows we want to layer
over it live in Postgres.

**Why a cached view instead of reading per fetch.** ``fetch_objects`` runs on every
query step of every run. A session opened there would put a database round-trip on
the hot path and — the deciding reason — would make the DB-LESS demo and the whole
offline suite depend on a live Postgres. PLAN-0095 exists so the image boots and
serves the synthetic demo with no database at all. So the database is touched at two
moments only: app startup, and immediately after a human records something.

**The `demo_events` cache is the subtle part.** ``demo_events.events`` builds its live
list ONCE per process and returns the same mutable list forever, so a changed overlay
is invisible until that cache is dropped. But the list also holds two things this
module did not put there: the real-time anchor shift, and the recovery reading
``inject_recovery`` appends when Execute runs (PLAN-0015 D2). A blanket reset on every
refresh would silently delete the recovery from the demo timeline.

So the reset is **fingerprinted**: it fires only when the loaded case facts actually
differ from what the view already held. In the demo's real order every refresh
happens before Execute, so the recovery survives; and when a genuine case change does
land after Execute, dropping a stale recovery is the correct answer anyway — the
picture it described has changed. :func:`status` reports the fingerprint's age and
the last reset so this is visible rather than folklore.

**The honest cost, stated rather than hidden.** This view is per-process, exactly like
``pm_projection``. Two API processes each hold their own copy. Acceptable for a
single-process pilot, and NOT acceptable silently — :func:`status` says what is held
and when it was loaded.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from services.db.case_events import CaseFacts, governed_case_facts
from services.engine import demo_events
from verticals.fleet_maintenance.case_events import build_event

_VERTICAL = "fleet_maintenance"

#: The loaded facts. Empty until a refresh runs, and empty is the correct starting
#: state: before anyone has accepted a quote the stream must look exactly as it did
#: before this feature existed.
_facts: list[CaseFacts] = []

#: A content digest of ``_facts``. ``None`` means "never loaded", which is distinct
#: from "loaded and empty" — the first refresh must be able to tell those apart.
_fingerprint: tuple[tuple[str, ...], ...] | None = None

_loaded: bool = False
_last_error: str | None = None
_last_reset_at: datetime | None = None
_trucks_not_found: tuple[str, ...] = ()


def _digest(facts: list[CaseFacts]) -> tuple[tuple[str, ...], ...]:
    """Everything about a fact set that can change the emitted event.

    Built from the fields :func:`build_event` actually reads. A digest over fewer
    fields would let a real change (เมย์ switching to a dearer garage) slip past the
    reset and leave the gate judging a superseded figure; a digest over more would
    fire resets for changes nobody can see.
    """
    return tuple(
        (
            f.case_id,
            f.truck_id,
            f.work_type,
            f.description or "",
            str(f.accepted_amount_thb),
            f.accepted_vendor,
            f.accepted_at.isoformat(),
            f.accepted_reason or "",
            str(f.distinct_vendor_count),
            str(f.has_sole_source_justification),
        )
        for f in facts
    )


async def refresh(session: AsyncSession, *, now: datetime | None = None) -> list[CaseFacts]:
    """Reload the view from open, accepted cases. Returns what it loaded.

    Drops ``demo_events``' cached live list only when the content actually changed —
    see the module docstring on why a blanket reset would eat the recovery reading.
    """
    global _loaded, _last_error, _fingerprint, _last_reset_at
    facts = await governed_case_facts(session)
    digest = _digest(facts)
    changed = digest != _fingerprint

    _facts.clear()
    _facts.extend(facts)
    _fingerprint = digest
    _loaded = True
    _last_error = None

    if changed:
        demo_events.reset(_VERTICAL)
        _last_reset_at = now if now is not None else datetime.now(UTC)
    return list(_facts)


def record_unavailable(error: str) -> None:
    """Note that a refresh could not run (no database at startup, say).

    The view keeps whatever it already had — a stale real case on the timeline beats
    silently reverting the fleet to a pure fixture — and says so through
    :func:`status`.
    """
    global _last_error
    _last_error = error


def apply(events: list[dict[str, Any]], trucks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Overlay the live case events onto the synthetic stream.

    Returns a new list and never mutates either argument. It is not strictly pure —
    it records which trucks it could not resolve, for :func:`status` — and that write
    is the point rather than an oversight: see below.

    ``trucks`` is passed in rather than imported so this module never depends on
    ``synthetic`` — which imports THIS one. It supplies the two facts an event needs
    that live on the asset: the truck's site, and its own repair ceiling.

    A case whose truck is not in the fleet is SKIPPED and named in :func:`status`.
    Emitting it would produce a row the ``event_for_truck`` join silently drops, so
    the case would vanish between the operator recording it and the gate seeing it
    with nothing anywhere saying why — the confidently-empty failure this whole path
    exists to close.
    """
    global _trucks_not_found
    by_id = {truck["truck_id"]: truck for truck in trucks}
    overlay: list[dict[str, Any]] = []
    missing: list[str] = []
    for facts in _facts:
        truck = by_id.get(facts.truck_id)
        if truck is None:
            missing.append(facts.truck_id)
            continue
        overlay.append(
            build_event(
                facts,
                site_id=truck["site_id"],
                ceiling_thb=float(truck["minor_repair_ceiling_thb"]),
            )
        )
    _trucks_not_found = tuple(sorted(set(missing)))
    return [*events, *overlay]


def facts() -> list[CaseFacts]:
    """The loaded facts, for tests and the health check."""
    return list(_facts)


def status() -> dict[str, Any]:
    """What this view holds and whether it is trustworthy, for ``health_check``."""
    return {
        "loaded": _loaded,
        "cases_with_accepted_quote": len(_facts),
        "last_error": _last_error,
        "last_reset_at": _last_reset_at.isoformat() if _last_reset_at else None,
        "trucks_not_found": list(_trucks_not_found),
    }


def reset() -> None:
    """Drop the view AND the live event list. Tests call this between cases."""
    global _loaded, _last_error, _fingerprint, _last_reset_at, _trucks_not_found
    _facts.clear()
    _fingerprint = None
    _loaded = False
    _last_error = None
    _last_reset_at = None
    _trucks_not_found = ()
    demo_events.reset(_VERTICAL)
