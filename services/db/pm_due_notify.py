"""The ``pm_due`` producer — the 06:00 sweep's due set, pushed to กลุ่มช่าง (AC-8, amended).

The partner's A3 answer asked for one more notification than the pilot had:
"PM ถึงกำหนด → กลุ่มช่าง". This is that producer, and it deliberately rides the
EXISTING 06:00 ``scheduled_pm_service_round`` rather than adding a scheduler — the
sweep already reads every truck's odometer and bands it against that truck's own
``next_service_due_km``, so the due set is a fact the run has already computed.

**Keyed to a run, not to a scan.** The caller passes the run the sweep just fired,
so a truck is announced exactly once per round. A "find everything due" scan would
have to remember what it already said, and the state it would need is precisely
what the run id already is.

**Reads the ENGINE's verdicts.** The due set comes from the persisted
``judge_service_due`` step artifact — the same rows the human approves at the gate.
Nothing here re-derives "due" from odometers: a second implementation of that
comparison would be free to disagree with the one the governed run acted on, and
the message would then name a different set of trucks than the screen.

Best-effort and never raises: a notification failure must not affect a run that
has already been recorded.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from services.engine.procedures.persistence import load_run
from services.notify.line import LineDelivery, LineEvent, notify

logger = logging.getLogger(__name__)

#: The step whose verdicts define "due". Named here rather than passed in: this
#: producer is about ONE procedure, and a caller free to point it at another step
#: could silently announce a set that means something else.
_JUDGE_STEP = "judge_service_due"

#: The verdict the evaluate step stamps on a truck at/above its own due point.
_DUE = "breach"


def _plate_of(row: dict[str, Any]) -> str:
    """How a truck should be named to a mechanic.

    The plate, because that is what is painted on the vehicle in the yard. The
    ``truck_id`` is a fallback for a row that somehow carries no plate — a message
    naming an internal id is poor, but a message that silently drops a due truck is
    worse.
    """
    plate = row.get("plate") or row.get("title") or row.get("truck_id") or row.get("primary_key")
    return str(plate) if plate else "—"


async def notify_pm_due_for_run(
    session: AsyncSession,
    run_id: str,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> LineDelivery | None:
    """Push one ``pm_due`` message for the trucks this run found due.

    Returns ``None`` when there is nothing to say — the run is missing, it has no
    judge step, or no truck is due. Silence on a morning when nothing is due is
    correct: a daily "0 trucks due" push is how a group learns to ignore the
    channel, which is the failure A3 was explicitly worried about.
    """
    loaded = await load_run(session, run_id)
    if loaded is None:
        logger.warning("pm_due: run %s not found — nothing pushed", run_id)
        return None

    judge = next((sr for sr in loaded.step_results if sr.step_id == _JUDGE_STEP), None)
    if judge is None or not judge.artifact:
        logger.warning("pm_due: run %s has no %s artifact — nothing pushed", run_id, _JUDGE_STEP)
        return None

    due = [row for row in judge.artifact.get("output_set", []) if row.get("verdict") == _DUE]
    if not due:
        logger.info("pm_due: run %s found no truck due — staying quiet", run_id)
        return None

    plates = sorted(_plate_of(row) for row in due)
    logger.info("pm_due: run %s found %d truck(s) due", run_id, len(plates))
    return await notify(
        LineEvent.PM_DUE,
        {"plates": plates, "run_id": run_id},
        transport=transport,
    )
