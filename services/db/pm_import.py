"""Hand-authored PM import rows — the measured-then-confirmed table (PLAN-0096 Step 9 / AC-10).

A sidecar beside ``repair_case`` and the quote-evidence tables, for the same reason
they are sidecars: the generated ORM is pinned to the ontology by a parity suite, and
this table is not an ontology object. It is the **staging area between a machine's
reading and a human's agreement**.

**Why the staging area exists at all (Q4).** The partner's telematics figures are
approximate — he said so unprompted — and PLAN-0096 locks the integration to CSV
export plus human confirm for exactly that reason. So an imported odometer is not a
fact about a truck; it is a *claim* about a truck, and the difference has to be
representable or the claim quietly becomes the fact. Every row here starts
``proposed`` and nothing downstream reads it until someone moves it to ``confirmed``.

**Why the ordering column is not a timestamp.** ``imported_at`` / ``decided_at`` are
recorded for humans, but the "which confirmed reading is the current one" question is
answered by ``seq``, a database-assigned identity. Wall-clock ordering is not safe in
this project — the WSL2 clock has been measured stepping backwards, which is why
``load_run`` refuses to order step results by ``created_at`` — and picking the wrong
"latest" odometer would move a truck's service due date to a stale number without
anything looking wrong. Insertion order is monotonic by construction; the clock is not.

**Why not simply take the highest odometer.** It is tempting — an odometer only goes
up — but it makes a correction impossible: if a wrong high reading is ever confirmed,
MAX would pin the truck to it forever and the honest fix (confirm the right number
afterwards) would silently do nothing. Latest-confirmed-wins is what a correction
needs.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from services.db.base import Base
from services.db.tenant import TenantKeyMixin

#: Imported, awaiting a human. Invisible to the ontology.
PM_STATUS_PROPOSED = "proposed"
#: A human agreed. This is the only status the Truck projection reads.
PM_STATUS_CONFIRMED = "confirmed"
#: Declined by a human, or unmatchable to a truck at import time. Kept, never deleted:
#: "this reading was offered and refused" is the answer to a later question about why
#: a truck's odometer did not move.
PM_STATUS_REJECTED = "rejected"
PM_STATUSES = (PM_STATUS_PROPOSED, PM_STATUS_CONFIRMED, PM_STATUS_REJECTED)

#: Why a row was rejected at import time rather than by a person.
REASON_UNKNOWN_PLATE = "unknown_plate"


class PmImportRow(TenantKeyMixin, Base):
    """One proposed PM value for one truck, from one imported file.

    ``truck_id`` is nullable because a row can name a plate the fleet does not have —
    a truck sold last month, a typo, a plate from another operator's sheet. That is an
    ordinary onboarding event, not a corrupt file, so the row is kept and rejected
    rather than aborting the import (the parser handles genuinely mangled files by
    refusing the whole thing).

    ``imported_by`` / ``decided_by`` are ``person_id``-shaped and carry no foreign key,
    matching ``repair_case.opened_by``: the principal roster is resolved live from the
    procedures spec, and เมย์ confirming an odometer must not fail because a roster row
    has not been synced.
    """

    __tablename__ = "pm_import_row"
    __table_args__ = (
        sa.Index("idx_pm_import_row_batch_id", "batch_id"),
        # The projection's read: confirmed rows for a truck, newest first by seq.
        sa.Index("idx_pm_import_row_truck_status", "truck_id", "status"),
    )

    import_row_id: Mapped[str] = mapped_column(sa.Text, primary_key=True)
    #: Database-assigned monotonic order — see the module docstring on why this is not
    #: a timestamp. ``always=True`` so no caller can supply one and break monotonicity.
    seq: Mapped[int] = mapped_column(
        sa.BigInteger, sa.Identity(always=True), nullable=False, unique=True
    )
    #: Groups the rows that came from one uploaded file, so a human reviews an import
    #: as the document it was rather than as loose readings.
    batch_id: Mapped[str] = mapped_column(sa.Text, nullable=False)
    #: The line number in เมย์'s spreadsheet (header = 1), not a list index.
    row_number: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    plate: Mapped[str] = mapped_column(sa.Text, nullable=False)
    truck_id: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    odometer_km: Mapped[float | None] = mapped_column(sa.Double, nullable=True)
    last_service_odometer_km: Mapped[float | None] = mapped_column(sa.Double, nullable=True)
    #: Absolute, computed at load by ``pm_import.next_service_due_from`` — never an
    #: interval, because the projection grammar downstream has no arithmetic.
    next_service_due_km: Mapped[float | None] = mapped_column(sa.Double, nullable=True)
    status: Mapped[str] = mapped_column(sa.Text, nullable=False)
    reason: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    imported_by: Mapped[str] = mapped_column(sa.Text, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    decided_by: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)


#: The Truck fields a confirmed row may override. Declared as data so the projection
#: and the confirm surface cannot disagree about what an import is allowed to change —
#: notably `minor_repair_ceiling_thb` and `status` are NOT here: an odometer import has
#: no business moving a truck's authority band or its operational state.
OVERRIDABLE_FIELDS = ("odometer_km", "next_service_due_km")


async def confirmed_truck_values(session: AsyncSession) -> dict[str, dict[str, float]]:
    """The confirmed PM overrides per ``truck_id`` — latest confirmed wins.

    Returns ``{truck_id: {field: value}}`` covering only ``OVERRIDABLE_FIELDS`` that a
    human has actually confirmed. A truck nobody has confirmed anything for is absent,
    which is what keeps an unconfirmed import invisible to the ontology.

    Reads every confirmed row and folds them in ``seq`` order rather than issuing a
    per-truck "latest" query. The scale makes that the right trade — this is a fleet of
    a few dozen trucks importing monthly, so the whole table is smaller than the query
    plan for the clever version — and the fold is obviously correct on inspection,
    which the window function would not be.
    """
    rows = (
        await session.execute(
            sa.select(PmImportRow)
            .where(PmImportRow.status == PM_STATUS_CONFIRMED)
            .where(PmImportRow.truck_id.isnot(None))
            .order_by(PmImportRow.seq)
        )
    ).scalars()

    overrides: dict[str, dict[str, float]] = {}
    for row in rows:
        truck_id = row.truck_id
        if truck_id is None:  # already excluded by the query; belt-and-braces for mypy
            continue
        target = overrides.setdefault(truck_id, {})
        for field in OVERRIDABLE_FIELDS:
            value = getattr(row, field)
            # A row that says nothing about a field must not erase what an earlier
            # confirmed row said about it: the paper-folder sheet carries no telematics
            # reading, and importing it should not blank every truck's odometer.
            if value is not None:
                target[field] = float(value)
    return overrides


def apply_overrides(
    trucks: list[dict[str, Any]], overrides: Mapping[str, Mapping[str, float]]
) -> list[dict[str, Any]]:
    """Overlay confirmed PM values onto truck records, leaving the input untouched.

    Pure, so the projection's behaviour is testable without a database. Returns new
    dicts: the synthetic source hands out its module-level records, and mutating them
    in place would let one request's overlay leak into the next.
    """
    return [{**truck, **overrides.get(str(truck.get("truck_id")), {})} for truck in trucks]
