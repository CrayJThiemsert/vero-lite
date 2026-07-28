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


class CaseResponse(BaseModel):
    """A repair case as stored."""

    case_id: str = Field(description="Stable case id — the value that rides the governed run")
    truck_id: str = Field(description="The truck this case is about")
    opened_by: str = Field(description="person_id of the human who opened it")
    opened_at: datetime = Field(description="When it was opened (UTC) — the 'minute 1' timestamp")
    description: str | None = Field(default=None, description="Optional free text")
    status: str = Field(description="Case lifecycle state: open | closed")
    photos: list[CasePhoto] = Field(
        default_factory=list, description="Attached photo metadata, oldest first"
    )


class CaseListResponse(BaseModel):
    """A page of cases, newest first."""

    cases: list[CaseResponse] = Field(description="The cases, newest-opened first")
    total: int = Field(description="Number of cases returned")
