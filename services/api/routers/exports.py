"""The month-end export surface — AC-9's payoff moment (PLAN-0096 Step 8).

Two routes, and the split between them is the design:

* ``GET /api/exports/repair-spend/{year}/{month}.csv`` — the Express-keyable file
* ``GET /api/exports/repair-spend/{year}/{month}/cover`` — the KPI + the proxy, JSON

**Why the cover is not inside the file** (Code's call, veto open). A preamble above
the header row is what makes a CSV human-friendly and machine-hostile: this file is
keyed into Express, and any importer would have to be told how many lines to skip — a
number that goes silently wrong the first time the cover grows a line. Keeping them
apart means the file is exactly what it claims to be, and the numbers stay
machine-readable instead of being parsed back out of prose.

**GET, and a downloadable file** (Cray, typed s192 — a CLI and a UI button were both
offered and declined). The month is fully derived from what is already recorded, so
producing it changes nothing and re-running it must be free: an export somebody is
afraid to re-run is an export nobody checks against the paper.

This is the repo's FIRST export surface. There was no `csv.writer`, no
`StreamingResponse` and no `text/csv` response anywhere before it, so the rendering
lives in `services/db/repair_spend_export.py` beside the column order it depends on
rather than here — the router's whole job is the HTTP shape.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.models.exports import ExportCoverResponse, ExportExceptionResponse
from services.db.repair_spend_export import (
    CSV_ENCODING,
    load_monthly_export,
    to_csv,
)
from services.db.session import get_session

router = APIRouter(prefix="/api/exports", tags=["exports"])

#: Bounds on the accounting year. Not a business rule — a guard against a path
#: segment like `/api/exports/repair-spend/0/1/cover` reaching `ZoneInfo` arithmetic
#: and surfacing a 500 where a 422 is the honest answer.
_MIN_YEAR = 2000
_MAX_YEAR = 2100

YearPath = Annotated[int, Path(ge=_MIN_YEAR, le=_MAX_YEAR, description="accounting year")]
MonthPath = Annotated[int, Path(ge=1, le=12, description="accounting month, 1-12")]


@router.get(
    "/repair-spend/{year}/{month}.csv",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}, "description": "the Express-keyable file"}},
)
async def repair_spend_csv(
    year: YearPath,
    month: MonthPath,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    """Download one accounting month of repair spend as CSV.

    The bytes are UTF-8 **with a BOM**. เมย์ opens this by double-clicking it, and
    Excel on Windows reads a BOM-less UTF-8 file as the system codepage — which turns
    every Thai header and vendor name into mojibake while the file stays perfectly
    valid UTF-8 to any tool used to check it.

    Rendered in memory rather than streamed: a month of a thirty-truck fleet is a few
    dozen rows, and `StreamingResponse` would buy nothing but a harder failure mode —
    an error raised mid-stream after a 200 has already been sent cannot be reported.
    """
    export = await load_monthly_export(session, year=year, month=month, now=datetime.now(UTC))
    body = to_csv(export).encode(CSV_ENCODING)
    filename = f"repair-spend-{year}-{month:02d}.csv"
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/repair-spend/{year}/{month}/cover", response_model=ExportCoverResponse)
async def repair_spend_cover(
    year: YearPath,
    month: MonthPath,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ExportCoverResponse:
    """The cover summary for the same month — AC-9's KPI and the audit-answer proxy.

    Derived from the same :func:`load_monthly_export` and the same
    :func:`is_fully_traceable` the file is built from, so the cover and the rows can
    never disagree about the RULE. They are still two requests at two instants: a
    close-out keyed between them moves the numbers, exactly as re-downloading the
    file a minute later would. Anyone reconciling the two should download both from
    the same session and treat a difference as new data, not as a defect.
    """
    export = await load_monthly_export(session, year=year, month=month, now=datetime.now(UTC))
    return ExportCoverResponse(
        **asdict(export.cover_summary()),
        exceptions=[
            ExportExceptionResponse(
                case_id=row.case_id,
                repair_order_no=row.repair_order_no,
                # `exception_label` is non-None for every row in `exception_rows` —
                # that is the property's filter — but narrowing it explicitly keeps
                # the response model's `str` honest rather than relying on a
                # `type: ignore` to paper over a guarantee made elsewhere.
                state=row.exception_label or "unknown",
                approver=row.approver,
                total_thb=row.total_thb,
                justification_ref=row.justification_ref,
                run_id=row.run_id,
            )
            for row in export.exception_rows
        ],
    )
