"""Fleet's registered DataAdapter: the synthetic adapter plus the three DB-backed types.

PLAN-0109 Step 3 — SD-A RULED (b), the session-owning fleet adapter (Cray, typed
2026-08-18). For ``RepairCase``, ``RepairCaseQuote`` and ``RepairCaseAcceptedQuote``
(``db_projection.DB_BACKED_TYPES``) the adapter opens one short-lived session from an
injectable factory and reads the hand-written tables; every other type falls through to
the synthetic adapter unchanged. The ``DataAdapter`` protocol, ADR-007, the engine and the
other verticals are untouched — the protocol carries no session, so this adapter owns one.

**Why a subclass in its own module, not an edit to ``__init__.py``.** The scaffolder's
golden oracle (``tests/services/engine/scaffolder/test_golden_e2e.py`` row 4) holds
``data_adapter/__init__.py`` structurally equal to what ``vero-lite new-vertical`` emits.
The DB branch is this vertical's post-scaffold extension — a scaffolded vertical has no
such tables — so it lives here, and the registrar instantiates it: a two-line difference
the oracle can name exactly, instead of a rewritten class it would have to excuse.

**What leaves the row: an ALLOWLIST (PLAN-0109 AC-10).** Each row is projected onto
exactly the property names the ontology declares for its type, read from the real YAML —
never "every column minus a denylist". A column added to a table later is therefore
excluded here by default, and the ``ontology-orm-lockstep`` guard reddens until someone
declares it or writes its reason into ``db_projection.EXCLUDED_COLUMNS``. Datetimes leave as
ISO-8601 strings and ``Decimal`` as ``float``, the shapes the synthetic rows already use.

**A failure is the engine's to phrase, not this adapter's.** A connection error propagates
out of ``fetch_objects``; ``answer_question`` turns any retrieval exception into the honest
"couldn't retrieve" answer (AC-9). Catching it here and returning ``[]`` would turn "the
database is down" into "there are no repair cases" — a confident wrong answer.

Rows are read with no tenant filter, the same as ``GET /api/cases``: the published
deployment has one tenant, and nothing on the read side of this repo resolves one per
request (ADR-0035 D7). ``tenant_id`` itself is never projected.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from services.engine.ontology_meta import load_ontology_meta
from verticals.fleet_maintenance.data_adapter import FleetMaintenanceSyntheticAdapter
from verticals.fleet_maintenance.data_adapter.db_projection import DB_BACKED_TYPES

#: A zero-argument callable whose result is used as ``async with`` — an
#: ``async_sessionmaker`` is exactly that.
SessionFactory = Callable[[], AsyncSession]

_VERTICAL = "fleet_maintenance"

#: The timestamp each DB-backed type is read newest-first by, so a ``limit`` keeps the
#: most recent rows. The primary key breaks ties, which keeps the order deterministic when
#: two rows share an instant.
NEWEST_FIRST_COLUMN: dict[str, str] = {
    "RepairCase": "opened_at",
    "RepairCaseQuote": "entered_at",
    "RepairCaseAcceptedQuote": "accepted_at",
}


def declared_properties(object_type: str) -> list[str]:
    """AC-10's allowlist: the property names the ontology declares, in declaration order."""
    declared = next(
        (o for o in load_ontology_meta(_VERTICAL).object_types if o.name == object_type), None
    )
    if declared is None:
        raise LookupError(
            f"{object_type} is DB-backed but not declared in the {_VERTICAL} ontology"
        )
    return [prop.name for prop in declared.properties]


def project_row(row: object, allowlist: list[str]) -> dict[str, Any]:
    """One ORM row as the dict the engine reads: allowlisted names only, JSON-shaped values."""
    projected: dict[str, Any] = {}
    for name in allowlist:
        value = getattr(row, name)
        if isinstance(value, datetime):
            value = value.isoformat()
        elif isinstance(value, Decimal):
            value = float(value)
        projected[name] = value
    return projected


async def read_db_objects(
    factory: SessionFactory, object_type: str, limit: int
) -> list[dict[str, Any]]:
    """Read one DB-backed type newest-first through one short-lived session."""
    mapped = DB_BACKED_TYPES[object_type]
    allowlist = declared_properties(object_type)
    newest = getattr(mapped, NEWEST_FIRST_COLUMN[object_type])
    tiebreak = [column.desc() for column in sa.inspect(mapped).primary_key]
    async with factory() as session:
        result = await session.execute(
            sa.select(mapped).order_by(newest.desc(), *tiebreak).limit(limit)
        )
        rows = result.scalars().all()
    return [project_row(row, allowlist) for row in rows]


def _default_session_factory() -> SessionFactory:
    # Imported on first READ, not at module import: importing `services.db.session` builds
    # the process-wide engine object, and registering this adapter — which discovery does in
    # every process, including tests with no database — should not be what builds it.
    from services.db.session import async_session

    return async_session


class FleetMaintenanceAdapter(FleetMaintenanceSyntheticAdapter):
    """The synthetic fleet adapter, plus the three DB-backed governance types."""

    def __init__(self, session_factory: SessionFactory | None = None) -> None:
        # Injectable so a test binds the disposable test database — configuration, not a
        # stub: the real query path still runs against a real database.
        self._session_factory = session_factory

    async def fetch_objects(
        self,
        object_type: str,
        filter_expr: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """DB-backed types from their tables; everything else from the synthetic dataset."""
        if object_type not in DB_BACKED_TYPES:
            return await super().fetch_objects(object_type, filter_expr, limit)
        factory = self._session_factory or _default_session_factory()
        return await read_db_objects(factory, object_type, limit)

    async def health_check(self) -> dict[str, Any]:
        """The synthetic report, unchanged, plus which types are read from the database.

        Additive only (PLAN-0109 AC-7): every existing key keeps its value. The DB-backed
        types are LISTED, not pinged — a health check that opened a connection would turn a
        database blip into an unhealthy report for the synthetic types too.
        """
        report = await super().health_check()
        return {**report, "db_backed_types": sorted(DB_BACKED_TYPES)}
