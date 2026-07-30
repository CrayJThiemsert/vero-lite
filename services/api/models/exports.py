"""Response models for the month-end export surface (PLAN-0096 Step 8 / AC-9)."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


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
