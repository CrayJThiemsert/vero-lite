"""The task-chain staleness sweep — stale item → LINE nudge (PLAN-0096 Step 6 / AC-7).

The producer for ``LineEvent.TASK_CHAIN_STALE``. It reads open cases, asks the
fleet's authored chain which items are past THEIR OWN deadline, and pushes one
nudge per stale item.

**Why it lives beside the run family and not in the router.** A nudge must fire
when nobody is looking at a screen — that is the entire point of it. This is a
plain async function so the 06:00 sweep, a test, or a future scheduler entry can
all drive it identically (the PLAN-0090 ride-along precedent), with the clock and
the transport injected so the offline suite makes no network call (AC-11).

**Never raises.** A notification failure must not break a caller, and a sweep that
died on case #3 would silently stop chasing cases #4 onward — the failure mode
where the channel looks healthy and simply stops working.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.db.repair_case import CASE_STATUS_OPEN, RepairCase
from services.db.repair_case_task import RepairCaseTaskEvent
from services.notify.line import LineEvent, notify
from verticals.fleet_maintenance.task_chain import stale_items

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SweepReport:
    """What one sweep did — returned so a caller can log or assert on it.

    ``nudged`` counts pushes actually delivered, ``stale_found`` counts items over
    their deadline. They differ whenever LINE is disarmed (the pilot's normal state
    until the partner supplies a token) or a recipient role is unmapped, and
    collapsing them into one number would make a disarmed channel look like a quiet
    week.
    """

    cases_scanned: int = 0
    stale_found: int = 0
    nudged: int = 0


async def sweep_stale_tasks(
    session: AsyncSession,
    *,
    now: datetime | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> SweepReport:
    """Push one nudge per stale checklist item across all open cases."""
    moment = now or datetime.now(UTC)
    cases = list(
        (
            await session.execute(select(RepairCase).where(RepairCase.status == CASE_STATUS_OPEN))
        ).scalars()
    )

    scanned = 0
    found = 0
    nudged = 0
    for case in cases:
        scanned += 1
        events = list(
            (
                await session.execute(
                    select(RepairCaseTaskEvent).where(RepairCaseTaskEvent.case_id == case.case_id)
                )
            ).scalars()
        )
        for item in stale_items(events, work_type=case.work_type, now=moment):
            found += 1
            delivery = await notify(
                LineEvent.TASK_CHAIN_STALE,
                {
                    "truck": case.truck_id,
                    "case_id": case.case_id,
                    # The partner's own label for the step, not our key: the person
                    # reading this on a phone has never seen "arrange_tow".
                    "task": item.label_th,
                    "stale_days": max(1, item.overdue_by.days),
                },
                transport=transport,
            )
            if delivery.delivered:
                nudged += 1

    logger.info(
        "task-chain sweep: %d open case(s), %d stale item(s), %d nudge(s) delivered",
        scanned,
        found,
        nudged,
    )
    return SweepReport(cases_scanned=scanned, stale_found=found, nudged=nudged)
