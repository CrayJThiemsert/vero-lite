"""The DB half of the case → event path (PLAN-0096 Step 8, corrected build order item 2).

Until this module existed, a real repair case **never reached a governed run**. เมย์
opened a case, keyed quotes, accepted one — and none of it was visible to the
procedure that routes spend, because the only ``case_id`` that ever reached a run
was a hardcoded fixture. The export's approval columns (วันที่อนุมัติ, ผู้อนุมัติ)
therefore had no source for any real row, whatever join shape was chosen downstream.

This module reads the facts; :mod:`verticals.fleet_maintenance.case_events` turns
them into an event. The split is the same one the quote pack makes: reading what was
recorded and deciding what it means are different jobs, and only the second is
vertical-specific.

**Only cases with an ACCEPTED quote are returned, and that is the design.** The
governed figure is the accepted quote's amount — the DOA ladder routes authority on
it, so a case with quotes but no acceptance has no number to be judged on. Emitting
one anyway would mean either inventing a figure (the cheapest quote, which is not
what was agreed) or handing the ladder a row with no ``amount``, which fails closed
inside the engine where the operator cannot see why. A case waiting for its
acceptance is simply not ready for the gate, and :func:`governed_case_facts`'s
caller reports the count so "why is my case not in the queue" has an answer.

**Plain frozen dataclasses, never ORM rows.** The caller caches what it gets for the
life of the process, and a detached ORM instance whose session has closed raises on
attribute access — the exact shape of bug that would surface as an unrelated
``DetachedInstanceError`` inside a query step. ``pm_import.confirmed_truck_values``
returns plain values for the same reason.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from services.db.evidence_pack import load_evidence_pack
from services.db.repair_case import CASE_STATUS_OPEN, RepairCase


@dataclass(frozen=True)
class CaseFacts:
    """One open, accepted repair case — everything the event needs, nothing more.

    Deliberately flat and JSON-shaped rather than an object graph: the consumer
    builds a dict, and every field here is one the event contract names.
    """

    case_id: str
    truck_id: str
    work_type: str
    description: str | None
    opened_at: datetime
    #: The governed figure — the accepted quote's amount. Never the cheapest.
    accepted_amount_thb: Decimal
    accepted_vendor: str
    accepted_at: datetime
    #: Why this one and not the cheapest, when it was not the cheapest.
    accepted_reason: str | None
    #: The sourcing-hygiene inputs, carried verbatim from the evidence pack so the
    #: vertical can run the REAL ``compute_three_quote`` rather than a copy of it.
    distinct_vendor_count: int
    has_sole_source_justification: bool


async def governed_case_facts(session: AsyncSession) -> list[CaseFacts]:
    """Every OPEN case that has an accepted quote, oldest case first.

    Closed cases are excluded: the work is done and the paperwork is keyed, so
    re-presenting one to the gate would ask for authority over spend that has already
    happened. Ordering is by ``opened_at`` so the list is stable across refreshes —
    the projection fingerprints it to decide whether anything actually changed, and a
    set that reshuffled on every read would look like a change every time.
    """
    cases = list(
        (
            await session.execute(
                sa.select(RepairCase)
                .where(RepairCase.status == CASE_STATUS_OPEN)
                .order_by(RepairCase.opened_at, RepairCase.case_id)
            )
        ).scalars()
    )

    facts: list[CaseFacts] = []
    for case in cases:
        pack = await load_evidence_pack(session, case.case_id)
        # The three accepted_* reads move together — the pack sets them from one row
        # or leaves all of them None — but mypy cannot know that, and asserting it
        # here would turn "nothing accepted yet" into a crash. Skipping is the same
        # answer with none of the risk.
        if (
            pack.accepted_amount_thb is None
            or pack.accepted_vendor is None
            or pack.accepted_at is None
        ):
            continue
        facts.append(
            CaseFacts(
                case_id=case.case_id,
                truck_id=case.truck_id,
                work_type=case.work_type,
                description=case.description,
                opened_at=case.opened_at,
                accepted_amount_thb=pack.accepted_amount_thb,
                accepted_vendor=pack.accepted_vendor,
                accepted_at=pack.accepted_at,
                accepted_reason=pack.accepted_reason,
                distinct_vendor_count=pack.distinct_vendor_count,
                has_sole_source_justification=pack.has_sole_source_justification,
            )
        )
    return facts
