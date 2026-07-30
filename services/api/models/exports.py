"""Response models for the month-end export surface (PLAN-0096 Step 8 / AC-9)."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class ExportExceptionResponse(BaseModel):
    """One repair that took the emergency path — the E-2 exception report.

    Carried on the cover rather than as extra CSV columns. AC-9's row-content list
    names the exception label, the justification ref and the run id, and the s190
    amendment maps them onto "the 15 columns + the cover summary"; putting them in the
    file would mean the Express-keyable export stopped being keyable and an accountant
    would have to strip columns before importing.
    """

    case_id: str = Field(description="the repair case this exception is about")
    repair_order_no: str | None = Field(
        description="เลขที่ใบแจ้งซ่อม — the number on the paper, NULL before close-out"
    )
    state: str = Field(
        description="the E-2 standing at report time: pending | overdue | ratified | refused"
    )
    approver: str | None = Field(
        description="who authorised the spend — the ATTESTED approver on this path, never "
        "the recorder. NULL once a ratification is refused: the authorisation was withdrawn"
    )
    total_thb: Decimal | None = Field(description="what it cost, NULL before close-out")
    justification_ref: str | None = Field(
        description="the tamper-evident hash of the audit row holding the run-time "
        "justification — if that row is ever edited the ref stops resolving AND the "
        "chain verification breaks, so the reason cannot be quietly rewritten later"
    )
    run_id: str | None = Field(description="the governed run that decided it")


class ExportCoverResponse(BaseModel):
    """The cover summary — AC-9's KPI and the audit-answer proxy beside it.

    Served as its own resource rather than prepended to the CSV: the file is keyed
    into Express, and a preamble above the header row would force every importer to
    be told how many lines to skip — a number that goes silently wrong the first time
    the cover grows a line.
    """

    year: int = Field(description="accounting year of the month reported")
    month: int = Field(ge=1, le=12, description="accounting month, 1-12, Asia/Bangkok")
    row_count: int = Field(description="Express entries in the file — one per repair")
    traceable_row_count: int = Field(
        description="rows that answer the audit question end to end: governed AND fully documented"
    )
    traceability_pct: float | None = Field(
        description="AC-9's KPI — % of rows fully traceable. NULL for a month with no "
        "spend, never 100: a month nobody spent in has no traceability to report"
    )
    audit_answer_pct: float | None = Field(
        description="the companion proxy — of every audit question askable of this month, "
        "the share that have an answer. Moves where the all-or-nothing KPI cannot"
    )
    ungoverned_row_count: int = Field(
        description="rows whose spend never passed a governed run — the money that escaped"
    )
    ungoverned_thb: Decimal = Field(
        description="the same escape measured in baht, because ten small escapes and one "
        "large one are the same count and a very different problem"
    )
    total_thb: Decimal = Field(description="total repair spend filed to this month")
    outstanding_ratification_count: int = Field(
        description="rows where somebody still owes a signature — pending OR overdue"
    )
    exceptions: list[ExportExceptionResponse] = Field(
        default_factory=list,
        description="every repair that took the emergency path this month, labelled. "
        "Bounded by construction — a waiver-invoked approval is the rare path, and a "
        "month where this list is long is a month somebody should be asked about",
    )
