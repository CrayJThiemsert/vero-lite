"""Request/response models for repair-case capture (PLAN-0096 Step 2 / AC-3).

Every field carries a ``description`` (CLAUDE.md §8) — these are the models the
partner's own admin (น้องเมย์) and a roadside mechanic (ต้อม) drive from a phone,
so the OpenAPI text is the closest thing to a user manual this surface has.

The shape encodes one AC-3 requirement structurally rather than by convention:
**the truck pick is the only required input.** ``description`` is optional and
photos arrive on a separate endpoint, so a case can be opened one-handed on the
hard shoulder with zero typing beyond choosing the truck. Any field that becomes
required later is a decision to make a roadside human type more, which is exactly
the trade-off the persona constraints say to refuse by default.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CasePhoto(BaseModel):
    """One photo attached to a case — metadata only; the bytes are on disk."""

    photo_id: str = Field(description="Stable id for this photo within its case")
    filename: str = Field(description="Original client filename, kept for the audit trail")
    content_type: str = Field(description="Client-declared MIME type, e.g. image/jpeg")
    size_bytes: int = Field(description="Stored size in bytes")
    stored_path: str = Field(
        description=(
            "Path of the stored file RELATIVE to the configured photo directory. "
            "Relative so the trail survives moving or re-mounting that directory."
        )
    )
    uploaded_at: datetime = Field(description="Server time the upload was stored (UTC)")
    caption: str | None = Field(
        default=None,
        description=(
            "Optional label ('ใบเสนอราคาจากอู่'). What lets the evidence pack tell a "
            "quote apart from a damage photo without opening either."
        ),
    )
    uploaded_by: str | None = Field(
        default=None,
        description=(
            "person_id of the uploader when authentication is enabled; None when it "
            "is off. Part of answering 'who' per baht."
        ),
    )


class OpenCaseRequest(BaseModel):
    """Open a repair case. Human-initiated only — there is no auto-detect path."""

    truck_id: str = Field(description="The truck this case is about — the ONE required input")
    description: str | None = Field(
        default=None,
        description=(
            "Optional free text ('เพลาขาดแถวปากช่อง'). Deliberately optional: a "
            "roadside case must be openable with a photo and no typing at all."
        ),
    )
    opened_by: str | None = Field(
        default=None,
        description=(
            "person_id of the human opening the case. Server-resolved from the authn "
            "dependency when authentication is enabled; accepted from the client only "
            "when it is not, which is how the offline demo and the test suite run."
        ),
    )
    work_type: str = Field(
        default="breakdown",
        description=(
            "What kind of work this is: breakdown | pm | accident (the partner's "
            "ประเภทงาน). Defaults to breakdown — the roadside case is the one nobody "
            "stops to categorise. Drives the task-chain's context SLAs (แจ้งอู่ is 30 "
            "minutes on a breakdown, a day on PM) and the month-end export column."
        ),
    )


class CaseResponse(BaseModel):
    """A repair case as stored."""

    case_id: str = Field(description="Stable case id — the value that rides the governed run")
    truck_id: str = Field(description="The truck this case is about")
    opened_by: str = Field(description="person_id of the human who opened it")
    opened_at: datetime = Field(description="When it was opened (UTC) — the 'minute 1' timestamp")
    description: str | None = Field(default=None, description="Optional free text")
    status: str = Field(description="Case lifecycle state: open | closed")
    work_type: str = Field(description="breakdown | pm | accident (ประเภทงาน)")
    photos: list[CasePhoto] = Field(
        default_factory=list, description="Attached photo metadata, oldest first"
    )


class CaseListResponse(BaseModel):
    """A page of cases, newest first."""

    cases: list[CaseResponse] = Field(description="The cases, newest-opened first")
    total: int = Field(description="Number of cases returned")


# --------------------------------------------------------------------------- #
# PLAN-0096 Step 3 — the quote evidence pack (AC-4's data half)
# --------------------------------------------------------------------------- #


class AddQuoteRequest(BaseModel):
    """Record one vendor's quote against a case. เมย์ types the amount (Q15)."""

    vendor: str = Field(description="Who quoted — the garage / parts shop / dealer")
    amount_thb: Decimal = Field(
        description=(
            "The quoted figure in THB. Decimal, never float: this is what the DOA "
            "ladder routes on downstream, and money on an authority threshold is "
            "exact or it is wrong."
        )
    )
    note: str | None = Field(default=None, description="Optional free text")
    entered_by: str | None = Field(
        default=None,
        description=(
            "person_id of whoever keyed it. Server-resolved when authentication is "
            "enabled; the client value is honoured only when it is off."
        ),
    )


class QuoteResponse(BaseModel):
    """A recorded quote."""

    quote_id: str = Field(description="Stable id for this quote")
    case_id: str = Field(description="The case it belongs to")
    vendor: str = Field(description="Who quoted")
    amount_thb: Decimal = Field(description="The quoted figure in THB")
    entered_by: str = Field(description="person_id of whoever keyed it")
    entered_at: datetime = Field(description="When it was keyed (UTC)")
    note: str | None = Field(default=None, description="Optional free text")
    attachment: CasePhoto | None = Field(
        default=None,
        description=(
            "The quote document (PDF / LINE-exported photo / photographed paper), or "
            "None when the amount was keyed ahead of the paperwork arriving."
        ),
    )


class AddJustificationRequest(BaseModel):
    """Record why this repair could not be three-quote compared (ADR-0034 E-3)."""

    vendor: str = Field(description="The sole source being justified")
    reason: str = Field(
        description=(
            "Why, in the operator's own words — rare part, only dealer who stocks it, "
            "the one shop open at that hour. Nothing parses this; a human reads it."
        )
    )
    entered_by: str | None = Field(
        default=None, description="person_id; server-resolved when authn is enabled"
    )


class JustificationResponse(BaseModel):
    """A recorded sole-source justification."""

    justification_id: str = Field(description="Stable id")
    case_id: str = Field(description="The case it belongs to")
    vendor: str = Field(description="The sole source being justified")
    reason: str = Field(description="The written reason")
    entered_by: str = Field(description="person_id of whoever wrote it")
    entered_at: datetime = Field(description="When it was written (UTC)")


class FlipTaskRequest(BaseModel):
    """Move one post-approval checklist item (PLAN-0096 Step 6 / AC-7).

    One shape for every movement — activating an item, completing it, skipping it.
    They are the same act (a human reporting what is true now) and the append-only
    trail records them identically, so a separate "activate" endpoint would only be
    a second way to write the same row.
    """

    item_key: str = Field(
        description=(
            "Which checklist step: notify_garage | arrange_tow | arrange_cargo_transfer "
            "| order_parts | wait_parts | start_repair | test_drive | close_case. "
            "An unknown key is refused — the chain is authored config, not free text."
        )
    )
    status: str = Field(
        description=(
            "pending = this item is now live on this case · done = finished · "
            "skipped = this case does not need it (a tow for a truck that can still "
            "drive). There is no in_progress: the team tracks 'ค้างอยู่ไหม', and a "
            "status nobody would flip is a status that lies."
        )
    )
    variant: str | None = Field(
        default=None,
        description=(
            "Flip-time context that changes the deadline — today only 'major_part' on "
            "the parts steps (ordinary parts wait ~2 days, big ones ~5). Only the "
            "person doing the flip knows this, which is why it is supplied here and "
            "not derived."
        ),
    )
    note: str | None = Field(default=None, description="Optional free text; nothing parses it")
    actor: str | None = Field(
        default=None, description="person_id; server-resolved when authn is enabled"
    )


class TaskItemResponse(BaseModel):
    """One checklist item's current state on one case."""

    item_key: str = Field(description="The step key")
    label_th: str = Field(description="The partner's own label for this step")
    mandatory: bool = Field(
        description=(
            "Whether every case has this step. The four conditional ones are absent "
            "until a human adds them; a case that skipped all four is complete, not "
            "incomplete."
        )
    )
    status: str = Field(description="pending | done | skipped — the latest flip")
    actor: str = Field(description="person_id behind that latest flip")
    activated_at: datetime = Field(description="When this item entered the chain (UTC)")
    last_flip_at: datetime = Field(description="When it last moved (UTC)")
    variant: str | None = Field(default=None, description="Latest variant supplied, if any")
    is_stale: bool = Field(
        description=(
            "Whether this item is past ITS OWN deadline right now. Computed against "
            "the authored per-item SLA, and only ever true for a pending item whose "
            "prerequisites are settled — a repair waiting on a legitimate 5-day parts "
            "order is not late."
        )
    )


class TaskChainResponse(BaseModel):
    """A case's post-approval checklist — the state humans read and flip."""

    case_id: str = Field(description="The case")
    work_type: str = Field(description="breakdown | pm | accident — selects the context SLAs")
    items: list[TaskItemResponse] = Field(
        description="Items present on this case, in the partner's chain order"
    )
    stale_item_keys: list[str] = Field(
        default_factory=list,
        description="Keys currently past deadline — what the LINE nudge is built from",
    )


class EvidencePackResponse(BaseModel):
    """A case's sourcing evidence as FACTS — deliberately not a verdict.

    PLAN-0096 Step 4 turns these into `compliance.three_quote` + `three_quote_basis`
    against the partner's ฿30,000 threshold. Nothing here decides pass or fail, so
    that the threshold can move without changing how evidence is read.
    """

    case_id: str = Field(description="The case")
    quote_count: int = Field(description="How many quotes are recorded")
    distinct_vendor_count: int = Field(
        description=(
            "How many DIFFERENT vendors those quotes came from. Reported separately "
            "because three quotes from one vendor is not a price comparison — the "
            "partner's rule (Q10) is three PLACES."
        )
    )
    vendors: list[str] = Field(description="Vendor names as entered, in entry order")
    lowest_amount_thb: Decimal | None = Field(
        default=None, description="Lowest quoted figure, or None when nothing is recorded"
    )
    has_sole_source_justification: bool = Field(
        description="Whether a written sole-source justification exists (ADR-0034 E-3)"
    )
    sole_source_vendor: str | None = Field(
        default=None, description="Vendor named by the most recent justification"
    )
    sole_source_reason: str | None = Field(
        default=None, description="The most recent justification's written reason"
    )
    attachment_count: int = Field(description="How many quotes carry a document")
    quotes: list[QuoteResponse] = Field(
        default_factory=list, description="The quotes themselves, oldest first"
    )
    justifications: list[JustificationResponse] = Field(
        default_factory=list, description="Every justification, oldest first (append-only)"
    )


# --------------------------------------------------------------------------- #
# PLAN-0096 Step 8 — the close-out record (AC-9's source)
# --------------------------------------------------------------------------- #


class CloseOutRequest(BaseModel):
    """Key the paperwork at ปิดงาน / เก็บเอกสาร (Cray's typed Decision B, s189).

    All three money figures are supplied; none is derived. Back-computing VAT at 7%
    was explicitly rejected, because not every vendor in this fleet is
    VAT-registered and a computed rate would invent tax on the ones that are not.
    """

    tax_invoice_no: str | None = Field(
        default=None,
        description=(
            "เลขที่ใบกำกับภาษี from the vendor's document, or None when the repair "
            "closed before the invoice arrived. Nullable rather than refused: the "
            "export reports a missing invoice as an incomplete row, which is the "
            "honest answer and the thing the KPI is designed to count."
        ),
    )
    amount_pre_vat_thb: Decimal = Field(description="จำนวนเงินก่อน VAT, in THB")
    vat_thb: Decimal | None = Field(
        default=None,
        description=(
            "The VAT line, or None when the vendor charges no VAT at all. None is "
            "NOT the same as 0.00 — one means 'not VAT-registered', the other means "
            "'VAT-registered and this line was exempt', and accounting reads them "
            "differently."
        ),
    )
    total_thb: Decimal = Field(
        description=(
            "จำนวนเงินรวม as printed on the invoice. Refused when it does not equal "
            "pre-VAT + VAT: a mismatch at this point is a typo, and catching it while "
            "เมย์ still has the paper in her hand is far cheaper than discovering it "
            "during a month-end reconciliation against Express."
        )
    )
    entered_by: str | None = Field(
        default=None, description="Fallback attribution when no authenticated principal is present"
    )


class CloseOutResponse(BaseModel):
    """A case's close-out, carrying the repair-order number the export keys on."""

    case_id: str = Field(description="The case")
    repair_order_no: str = Field(
        description=(
            "เลขที่ใบแจ้งซ่อม — RC-<year>-<NNNN>, the running sequence reset per year "
            "(Cray's typed Decision A). Allocated once per case on its first close-out "
            "and reused by every correction, so the number written on the paper in the "
            "folder never changes."
        )
    )
    tax_invoice_no: str | None = Field(default=None, description="เลขที่ใบกำกับภาษี, if keyed")
    amount_pre_vat_thb: Decimal = Field(description="จำนวนเงินก่อน VAT")
    vat_thb: Decimal | None = Field(default=None, description="VAT, or None for a non-VAT vendor")
    total_thb: Decimal = Field(description="จำนวนเงินรวม")
    entered_by: str = Field(description="person_id of whoever keyed it")
    entered_at: datetime = Field(description="When it was keyed (UTC)")
