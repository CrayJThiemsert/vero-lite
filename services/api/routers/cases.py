"""Repair-case capture API (PLAN-0096 Step 2 / AC-3).

The surface น้องเมย์ and ต้อม actually touch. Four routes, deliberately:

* ``POST /api/cases`` — open a case (truck pick; everything else optional)
* ``POST /api/cases/{case_id}/photos`` — attach a photo
* ``GET  /api/cases`` — list, newest first (optionally filtered by truck)
* ``GET  /api/cases/{case_id}`` — one case

**There is no auto-detection route, and that is a requirement, not an omission**
(Q1, LOCKED in PLAN-0096's Out of Scope). The partner was asked directly and does
not want breakdowns detected for him; humans open cases. A test asserts the absence
so a future "convenience" endpoint cannot arrive quietly.

**Photo bytes go to disk, metadata to Postgres.** The upload is streamed in bounded
chunks and refused with 413 the moment it crosses ``repair_case_photo_max_bytes``,
so an oversized or lying ``Content-Length`` cannot make the process hold a phone
video in memory. Local disk only — AC-11 forbids any live external call, and object
storage is a live external call.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.auth import AuthContext, get_current_principal
from services.api.config import settings
from services.api.models.cases import (
    CaseListResponse,
    CaseResponse,
    OpenCaseRequest,
)
from services.db.repair_case import CASE_STATUS_OPEN, RepairCase
from services.db.session import get_session

router = APIRouter(prefix="/api/cases", tags=["repair-cases"])

#: Read in bounded chunks so an oversized upload is refused before it is buffered.
_CHUNK_BYTES = 64 * 1024

#: Fallback actor when authn is disabled and the client names nobody. Recorded
#: explicitly rather than left NULL: "we do not know who opened this" is a fact the
#: traceability KPI must be able to SEE, not a blank to be mistaken for clean data.
_UNATTRIBUTED = "unattributed"


def photo_root() -> Path:
    """The configured photo directory, resolved from the repo root when relative."""
    configured = Path(settings.repair_case_photo_dir)
    return configured if configured.is_absolute() else Path.cwd() / configured


def _to_response(case: RepairCase) -> CaseResponse:
    return CaseResponse(
        case_id=case.case_id,
        truck_id=case.truck_id,
        opened_by=case.opened_by,
        opened_at=case.opened_at,
        description=case.description,
        status=case.status,
        photos=list(case.photos or []),
    )


async def _load(session: AsyncSession, case_id: str) -> RepairCase:
    case = await session.get(RepairCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"repair case '{case_id}' not found")
    return case


@router.post("", response_model=CaseResponse, status_code=201)
async def open_case(
    req: OpenCaseRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    auth: Annotated[AuthContext, Depends(get_current_principal)],
) -> CaseResponse:
    """Open a repair case for one truck — the minute-1 record.

    ``opened_by`` is the SERVER-resolved principal whenever authn is on; the
    client-supplied value is honoured only when it is off. That ordering matters
    for the KPI: "who opened this" is part of what the partner wants to answer per
    baht, so a client must not be able to claim to be someone else.
    """
    truck_id = req.truck_id.strip()
    if not truck_id:
        raise HTTPException(status_code=422, detail="truck_id is required to open a case")

    opened_by = auth.person_id or (req.opened_by or "").strip() or _UNATTRIBUTED
    case = RepairCase(
        case_id=f"case-{uuid.uuid4().hex[:12]}",
        truck_id=truck_id,
        opened_by=opened_by,
        opened_at=datetime.now(UTC),
        description=(req.description or None),
        status=CASE_STATUS_OPEN,
        photos=[],
    )
    session.add(case)
    await session.commit()
    return _to_response(case)


@router.post("/{case_id}/photos", response_model=CaseResponse)
async def attach_photo(
    case_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    auth: Annotated[AuthContext, Depends(get_current_principal)],
    file: Annotated[UploadFile, File(description="The photo — PDF, phone photo, or scan")],
    caption: Annotated[str | None, Form(description="Optional caption")] = None,
) -> CaseResponse:
    """Attach one photo to an existing case.

    Written to disk first, recorded in the row second. If the write fails the row
    is untouched, so the metadata never promises a file that is not there — the
    opposite order would leave the evidence pack citing a missing photo, which is
    worse than a failed upload the human can retry.
    """
    case = await _load(session, case_id)

    photo_id = f"photo-{uuid.uuid4().hex[:12]}"
    suffix = Path(file.filename or "").suffix[:16]
    relative = Path(case_id) / f"{photo_id}{suffix}"
    destination = photo_root() / relative
    destination.parent.mkdir(parents=True, exist_ok=True)

    size = 0
    limit = settings.repair_case_photo_max_bytes
    try:
        with destination.open("wb") as sink:
            while chunk := await file.read(_CHUNK_BYTES):
                size += len(chunk)
                if size > limit:
                    raise HTTPException(
                        status_code=413,
                        detail=f"photo exceeds the {limit} byte limit",
                    )
                sink.write(chunk)
    except HTTPException:
        destination.unlink(missing_ok=True)
        raise

    entry: dict[str, Any] = {
        "photo_id": photo_id,
        "filename": file.filename or f"{photo_id}{suffix}",
        "content_type": file.content_type or "application/octet-stream",
        "size_bytes": size,
        "stored_path": relative.as_posix(),
        "uploaded_at": datetime.now(UTC).isoformat(),
    }
    if caption:
        entry["caption"] = caption
    if auth.person_id:
        entry["uploaded_by"] = auth.person_id

    # Reassign rather than append: SQLAlchemy does not track in-place mutation of a
    # plain JSONB list, so an append would commit nothing and the photo would exist
    # on disk with no row pointing at it.
    case.photos = [*(case.photos or []), entry]
    await session.commit()
    return _to_response(case)


@router.get("", response_model=CaseListResponse)
async def list_cases(
    session: Annotated[AsyncSession, Depends(get_session)],
    truck_id: str | None = None,
    limit: int = 50,
) -> CaseListResponse:
    """List cases, newest first, optionally for one truck."""
    stmt = select(RepairCase).order_by(RepairCase.opened_at.desc()).limit(max(1, min(limit, 500)))
    if truck_id:
        stmt = stmt.where(RepairCase.truck_id == truck_id)
    cases = list((await session.execute(stmt)).scalars())
    return CaseListResponse(cases=[_to_response(c) for c in cases], total=len(cases))


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CaseResponse:
    """One case by id."""
    return _to_response(await _load(session, case_id))
