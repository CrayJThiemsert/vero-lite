"""PM data import API — measured, then confirmed (PLAN-0096 Step 9 / AC-10).

Three routes, and the shape of them is the governance:

* ``POST /api/pm/imports``            — upload a CSV; every row lands ``proposed``
* ``POST /api/pm/imports/{id}/decisions`` — a human confirms or declines rows
* ``GET  /api/pm/imports/{id}``       — review one batch
* ``GET  /api/pm/overrides``          — what the ontology actually sees today

**There is no route that applies a reading without a decision**, and that is the
requirement (Q4/LOCKED). The partner's telematics figures are approximate; an import
that wrote straight through would make every truck's service-due date move on its own,
and the calm path's whole value is that เมย์ can answer "why is this truck flagged?"
with a number a person agreed to.

**Upload is a file, not JSON.** What the partner has is an export he can save and
mail; asking him for a JSON body would mean building the converter he is trying to
avoid. The bytes are read once, bounded by the same ceiling the case photos use, and
parsed in memory — a PM sheet for thirty trucks is a few kilobytes.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.auth import AuthContext, get_current_principal
from services.api.config import settings
from services.api.models.pm import (
    PmDecisionRequest,
    PmImportBatchResponse,
    PmImportRowResponse,
    PmOverridesResponse,
    PmTruckOverrideResponse,
    PmViewStatus,
)
from services.db.pm_import import (
    PM_STATUS_CONFIRMED,
    PM_STATUS_PROPOSED,
    PM_STATUS_REJECTED,
    REASON_UNKNOWN_PLATE,
    PmImportRow,
    confirmed_truck_values,
)
from services.db.session import get_session
from services.engine.registry import RegistryError, registry
from verticals.fleet_maintenance import pm_projection
from verticals.fleet_maintenance.pm_import import PmImportError, parse_pm_csv

router = APIRouter(prefix="/api/pm", tags=["pm-import"])

_VERTICAL = "fleet_maintenance"

#: Same fallback actor the case surface uses: "we do not know who did this" is a fact
#: the traceability KPI must be able to see, never a blank that reads as clean data.
_UNATTRIBUTED = "unattributed"


def _to_response(row: PmImportRow) -> PmImportRowResponse:
    return PmImportRowResponse(
        import_row_id=row.import_row_id,
        row_number=row.row_number,
        plate=row.plate,
        truck_id=row.truck_id,
        odometer_km=row.odometer_km,
        last_service_odometer_km=row.last_service_odometer_km,
        next_service_due_km=row.next_service_due_km,
        status=row.status,
        reason=row.reason,
        decided_by=row.decided_by,
        decided_at=row.decided_at,
    )


def _batch_response(rows: list[PmImportRow]) -> PmImportBatchResponse:
    first = rows[0]
    return PmImportBatchResponse(
        batch_id=first.batch_id,
        imported_by=first.imported_by,
        imported_at=first.imported_at,
        rows=[_to_response(row) for row in rows],
        proposed_count=sum(1 for row in rows if row.status == PM_STATUS_PROPOSED),
        rejected_count=sum(1 for row in rows if row.status == PM_STATUS_REJECTED),
    )


async def _plates_to_truck_ids() -> dict[str, str]:
    """Map plate -> truck_id from the live fleet adapter.

    Read through the registry rather than from a table: the fleet's Truck objects are
    served by the vertical's adapter, so this resolves against the same fleet the calm
    path reads. Plates are compared case-folded and space-collapsed — the partner's
    sheet will not spell a plate the way our fixture does, and failing every row over
    a double space would be a data-entry trap, not a governance control.
    """
    adapter = registry.get_adapter(_VERTICAL)
    trucks = await adapter.fetch_objects("Truck")
    return {
        _plate_key(str(truck["plate"])): str(truck["truck_id"])
        for truck in trucks
        if truck.get("plate") and truck.get("truck_id")
    }


def _plate_key(plate: str) -> str:
    return " ".join(plate.split()).casefold()


@router.post("/imports", response_model=PmImportBatchResponse, status_code=201)
async def import_pm_csv(
    file: Annotated[UploadFile, File(description="the exported PM CSV")],
    auth: Annotated[AuthContext, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PmImportBatchResponse:
    """Parse an uploaded PM CSV into PROPOSED rows. Nothing reaches the ontology here."""
    limit = settings.repair_case_photo_max_bytes
    raw = await file.read(limit + 1)
    if len(raw) > limit:
        raise HTTPException(status_code=413, detail=f"upload exceeds the {limit} byte limit")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=422,
            detail="the file is not UTF-8 text — refusing it rather than guessing an encoding",
        ) from exc

    try:
        proposals = parse_pm_csv(text)
    except PmImportError as exc:
        # 422, not 500: the file is the client's, and the message names the row. Failing
        # the WHOLE upload is deliberate — a half-imported fleet is worse than none.
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        by_plate = await _plates_to_truck_ids()
    except RegistryError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"the {_VERTICAL} adapter is not registered, so plates cannot be matched",
        ) from exc

    batch_id = f"pmb-{uuid.uuid4().hex[:12]}"
    actor = auth.person_id or _UNATTRIBUTED
    now = datetime.now(UTC)
    rows: list[PmImportRow] = []
    for proposal in proposals:
        truck_id = by_plate.get(_plate_key(proposal.plate))
        matched = truck_id is not None
        rows.append(
            PmImportRow(
                import_row_id=f"pmr-{uuid.uuid4().hex[:12]}",
                batch_id=batch_id,
                row_number=proposal.row_number,
                plate=proposal.plate,
                truck_id=truck_id,
                odometer_km=proposal.odometer_km,
                last_service_odometer_km=proposal.last_service_odometer_km,
                next_service_due_km=proposal.next_service_due_km,
                status=PM_STATUS_PROPOSED if matched else PM_STATUS_REJECTED,
                reason=None if matched else REASON_UNKNOWN_PLATE,
                imported_by=actor,
                imported_at=now,
                # An unmatched row is decided BY THE IMPORT, so it is stamped here: a
                # rejected row with no decider would read as awaiting someone.
                decided_by=None if matched else actor,
                decided_at=None if matched else now,
            )
        )
    session.add_all(rows)
    await session.commit()
    for row in rows:
        await session.refresh(row)
    return _batch_response(rows)


async def _load_batch(
    session: AsyncSession, batch_id: str, *, for_update: bool = False
) -> list[PmImportRow]:
    """The batch's rows in spreadsheet order, optionally locked for a decision.

    ``for_update`` is **opt-in per call site, and defaults off on purpose**. The row
    lock belongs to the decide path, which reads a row's status and then writes it; the
    review GET reads and returns, and locking rows there would both mean something the
    endpoint does not intend and make a read contend with a decision in flight.

    **Why the existing ``order_by`` is load-bearing once locking is on.** Two decisions
    against the same batch acquire the same rows in the same order — ``row_number``,
    which is stable — so they queue behind each other instead of deadlocking. A lock
    added to an unordered select would have introduced that hazard silently.
    """
    statement = (
        select(PmImportRow).where(PmImportRow.batch_id == batch_id).order_by(PmImportRow.row_number)
    )
    if for_update:
        statement = statement.with_for_update()
    rows = list((await session.execute(statement)).scalars().all())
    if not rows:
        raise HTTPException(status_code=404, detail=f"pm import batch '{batch_id}' not found")
    return rows


@router.get("/imports/{batch_id}", response_model=PmImportBatchResponse)
async def get_pm_import(
    batch_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PmImportBatchResponse:
    """One uploaded batch and the standing of every row in it."""
    return _batch_response(await _load_batch(session, batch_id))


@router.post("/imports/{batch_id}/decisions", response_model=PmImportBatchResponse)
async def decide_pm_import(
    batch_id: str,
    payload: PmDecisionRequest,
    auth: Annotated[AuthContext, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PmImportBatchResponse:
    """Confirm or decline proposed rows. Only a confirm makes a value visible."""
    # Locked read: the status check below decides whether to write, so an unlocked read
    # would let two concurrent deciders both observe `proposed` and both pass the guard,
    # and the later commit would silently overwrite the earlier decision — stamping the
    # loser's `decided_by` on a row the winner had already ruled on. The guard is a
    # check-then-act, so the read it acts on has to be the locked one.
    rows = await _load_batch(session, batch_id, for_update=True)
    by_id = {row.import_row_id: row for row in rows}
    actor = payload.decided_by or auth.person_id or _UNATTRIBUTED
    now = datetime.now(UTC)

    for decision in payload.decisions:
        row = by_id.get(decision.import_row_id)
        if row is None:
            raise HTTPException(
                status_code=404,
                detail=f"row '{decision.import_row_id}' is not in batch '{batch_id}'",
            )
        if row.status != PM_STATUS_PROPOSED:
            # Idempotent BY STATE, like the gate drivers: a row already decided is not
            # re-decidable, so a replayed request cannot silently flip a rejection into
            # a confirmation. Under the locked read above this now also holds for a
            # CONCURRENT decision, not just a replayed one: the second decider blocks
            # until the first commits, then re-reads the decided status and lands here.
            raise HTTPException(
                status_code=409,
                detail=(
                    f"row '{row.import_row_id}' is already '{row.status}' — only a "
                    "proposed row can be decided"
                ),
            )
        row.status = PM_STATUS_CONFIRMED if decision.confirm else PM_STATUS_REJECTED
        row.reason = None if decision.confirm else "declined"
        row.decided_by = actor
        row.decided_at = now

    await session.commit()
    # Refresh the Truck view in the SAME request that confirmed the rows. A confirm
    # whose effect only appeared after a restart would be indistinguishable, to เมย์,
    # from one that did nothing — and she would confirm it again.
    await pm_projection.refresh(session)
    return _batch_response(await _load_batch(session, batch_id))


@router.get("/overrides", response_model=PmOverridesResponse)
async def get_pm_overrides(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PmOverridesResponse:
    """What confirmed imports currently contribute to the Truck projection.

    Separate from the batch view on purpose: "what did this file say" and "what have we
    accepted" are different questions, and conflating them is how a proposal starts
    being read as a fact.
    """
    values = await confirmed_truck_values(session)
    return PmOverridesResponse(
        overrides=[
            PmTruckOverrideResponse(
                truck_id=truck_id,
                odometer_km=fields.get("odometer_km"),
                next_service_due_km=fields.get("next_service_due_km"),
            )
            for truck_id, fields in sorted(values.items())
        ],
        view=PmViewStatus(**pm_projection.status()),
    )
