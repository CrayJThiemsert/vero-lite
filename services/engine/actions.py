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
from typing import Any

from pydantic import BaseModel, Field


class ReasoningStep(BaseModel):
    step_id: str
    kind: str = Field(..., description="e.g., 'ontology_query', 'llm_inference', 'rule_check'")
    summary: str
    detail: dict[str, Any] | None = None


class EntityRef(BaseModel):
    object_type: str
    primary_key: str
    title: str | None = None


class AuditMetadata(BaseModel):
    """Initial scope; expanded in future audit-framework ADR."""

    actor: str
    actor_kind: str = Field(..., description="'engine', 'llm', 'human'")
    correlation_id: str | None = None
    notes: str | None = None


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
