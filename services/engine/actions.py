"""RecommendedAction runtime envelope (ADR-007 D2).

The in-flight runtime object the engine produces when it derives an
action from an Alert. Per PLAN-0005 OQ-1 this is distinct from the
``RecommendedAction`` *ontology entity* in ``energy_v0.yaml``: this
envelope is the runtime object, the ontology entity is its persisted
projection. The two schemas are deliberately not unified — the
envelope-to-entity mapping happens at the persistence boundary
(``services/db/``).

The four models are the ADR-007 D2 contract verbatim.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ReasoningStep(BaseModel):
    step_id: str
    kind: str = Field(..., description="e.g., 'ontology_query', 'llm_inference', 'rule_check'")
    summary: str
    detail: dict[str, Any] | None = None


class EntityRef(BaseModel):
    object_type: str
    primary_key: str
    title: str | None = None


class ControlRef(BaseModel):
    """A reference to the governing control a decision fired under (ADR-0026 D6 / OQ-5;
    PLAN-0044 A1b Step 6, SD-3=(a)). ``id`` is the control's STABLE id — matching the id the
    governing verdict emits so a read-only render joins audit -> control EXACTLY (no fuzzy
    match): the ``resolved_tier_id`` for a ``doa_tier`` control, the sorted-distinct-steps SoD
    constraint id for a ``sod`` control."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["doa_tier", "sod"] = Field(
        description="the control family that governed the decision (doa_tier route | SoD gate)"
    )
    id: str = Field(
        description="the control's stable id — the resolved_tier_id (doa_tier) or the sorted "
        "distinct_steps SoD constraint id; matches the id the verdict emits (exact join)"
    )


class GovernedDecision(BaseModel):
    """The OQ-5-minimal audit-to-control tie (ADR-0026 D6; PLAN-0044 A1b Step 6, AC-8 / SD-3=(a)).

    One governing-control reference + one resolved-principal identity key — TYPED + queryable,
    never free prose, emitted by the engine as a SIDE-EFFECT of a governed route / block / select
    (it cannot be authored ``auto`` / omitted). Deliberately MINIMAL: it does NOT pre-empt the
    deferred ADR-011 audit framework (no actor chain, no attestation provenance). A read-only
    render joins 'this decision -> this control -> this owning principal' on these two keys."""

    model_config = ConfigDict(extra="forbid")

    control_ref: ControlRef = Field(description="the governing control the decision fired under")
    principal_id: str = Field(
        description="the resolved-principal identity key — a canonical Person ``person_id`` (the "
        "same PK the PrincipalSoDVerdict / DoaTierVerdict reference), never a role label or alias"
    )


class AuditMetadata(BaseModel):
    """Initial scope; expanded in future audit-framework ADR."""

    actor: str
    actor_kind: str = Field(..., description="'engine', 'llm', 'human'")
    correlation_id: str | None = None
    notes: str | None = None
    governed_decision: GovernedDecision | None = Field(
        default=None,
        description="the OQ-5-minimal audit-to-control tie (decision -> governing control + "
        "resolved principal), emitted by the engine on a governed route/gate (A1b Step 6); None "
        "for a non-governed action. Does not pre-empt the ADR-011 audit framework.",
    )


class RecommendedAction(BaseModel):
    """Generic envelope; vertical-specific handler interpretation lives
    in registered handlers, NOT in this schema."""

    id: str
    title: str
    description: str
    vertical: str = Field(..., description="Originating vertical name")
    reasoning_trace: list[ReasoningStep]
    confidence: float = Field(..., ge=0.0, le=1.0)
    affected_entities: list[EntityRef]
    suggested_handler: str = Field(..., description="Registered handler name")
    handler_payload: dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = True
    approval_chain: list[str] = Field(default_factory=list, description="Role names")
    audit_metadata: AuditMetadata
    created_at: datetime
    expires_at: datetime | None = None
    # Real, server-side decision timestamps (PLAN-0015 D3) — set by the approval
    # gate when the human approves / executes; None until then.
    approved_at: datetime | None = None
    executed_at: datetime | None = None
