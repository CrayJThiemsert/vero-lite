"""Request / response models for the PM data import surface (PLAN-0096 Step 9 / AC-10)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PmImportRowResponse(BaseModel):
    """One proposed PM value, and where it stands."""

    model_config = ConfigDict(extra="forbid")

    import_row_id: str = Field(description="stable id of this proposed row")
    row_number: int = Field(
        description="the line number in the uploaded spreadsheet (header = 1), so a "
        "reviewer is pointed at the row they can actually see"
    )
    plate: str = Field(description="the truck plate as written in the imported file")
    truck_id: str | None = Field(
        default=None,
        description="the matched truck; null when the plate matches no truck in the "
        "fleet, which is a rejection reason rather than an error",
    )
    odometer_km: float | None = Field(
        default=None, description="proposed current odometer reading (km)"
    )
    last_service_odometer_km: float | None = Field(
        default=None, description="proposed last-service odometer (km), from the paper PM folder"
    )
    next_service_due_km: float | None = Field(
        default=None,
        description="ABSOLUTE next-service point, computed at load as last service + the "
        "100,000 km interval; null when the row carried no last-service figure",
    )
    status: str = Field(description="proposed | confirmed | rejected")
    reason: str | None = Field(default=None, description="why this row was rejected, when it was")
    decided_by: str | None = Field(default=None, description="who confirmed or rejected it")
    decided_at: datetime | None = Field(default=None, description="when that decision was made")


class PmImportBatchResponse(BaseModel):
    """One uploaded file and every proposal it produced."""

    model_config = ConfigDict(extra="forbid")

    batch_id: str = Field(description="groups the rows that came from one uploaded file")
    imported_by: str = Field(description="who uploaded it")
    imported_at: datetime = Field(description="when it was uploaded")
    rows: list[PmImportRowResponse] = Field(description="every parsed row, in file order")
    proposed_count: int = Field(description="rows still awaiting a human decision")
    rejected_count: int = Field(description="rows rejected at import — today only unmatched plates")


class PmDecision(BaseModel):
    """A human's decision about one proposed row."""

    model_config = ConfigDict(extra="forbid")

    import_row_id: str = Field(description="the row being decided")
    confirm: bool = Field(
        description="true accepts the reading into the truck's projection; false records "
        "a decline. There is no third option: leaving a row undecided is the default, and "
        "it already means 'not applied'."
    )


class PmDecisionRequest(BaseModel):
    """Confirm or decline a set of proposed rows in one reviewed pass."""

    model_config = ConfigDict(extra="forbid")

    decisions: list[PmDecision] = Field(
        min_length=1,
        description="the rows being decided; rows omitted here stay proposed and stay "
        "invisible to the ontology",
    )
    decided_by: str | None = Field(
        default=None,
        description="the deciding person_id; falls back to the authenticated principal",
    )


class PmTruckOverrideResponse(BaseModel):
    """What the ontology currently sees for one truck as a result of confirmed imports."""

    model_config = ConfigDict(extra="forbid")

    truck_id: str = Field(description="the truck these confirmed values apply to")
    odometer_km: float | None = Field(default=None, description="confirmed odometer (km)")
    next_service_due_km: float | None = Field(
        default=None, description="confirmed absolute next-service point (km)"
    )


class PmViewStatus(BaseModel):
    """Whether the confirmed-PM view is trustworthy right now.

    Carried beside the overrides because "nobody has confirmed anything" and "we could
    not read what was confirmed" are different answers, and an evidence surface that
    rendered them identically would be telling a reassuring lie."""

    model_config = ConfigDict(extra="forbid")

    loaded: bool = Field(description="true once a refresh has successfully completed")
    trucks_with_confirmed_values: int = Field(description="how many trucks the view covers")
    last_error: str | None = Field(
        default=None,
        description="why the last refresh failed, if it did — e.g. the database was "
        "unreachable at startup, in which case trucks are serving fixture values",
    )


class PmOverridesResponse(BaseModel):
    """Every confirmed override currently in force — the honest answer to 'what did we
    actually accept?', separate from what any file proposed."""

    model_config = ConfigDict(extra="forbid")

    overrides: list[PmTruckOverrideResponse] = Field(
        description="one entry per truck with at least one confirmed value"
    )
    view: PmViewStatus = Field(
        description="the standing of the process-local view the ontology reads through"
    )
