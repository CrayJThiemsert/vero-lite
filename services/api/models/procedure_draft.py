"""Request / response models for the procedure-draft intake routes (PLAN-0040
Phase B, Step B3 / AC-B5; LOCKED-9 / D9 — the PLAN-0017 intake face reused for the
archetype-first procedure generator).

The generator classifies a free-text narrative to one catalogued archetype, then
instantiates + drafts a governed SKELETON behind the human-review gate. These models
carry that across the HTTP boundary in the **same envelope shape** the edit-mode gate
already renders (``gate-fixture.js``): a ``GET /procedures``-shaped ``{verticals: [...]}``
plus the net-new per-procedure ``governance_todo`` (the "YOU must author" worklist,
OQ-C / AC-A7) and the top-level ``governance_options`` (the LEGAL authoring allowlist —
a domain a human picks from, never a recommended value, D4). Identical shape ⇒ the gate
renderer reuses its read-mode path verbatim (LOCKED-8: no second renderer).

The classify ↔ build split mirrors ``intake.py``'s extract ↔ generate: classify proposes
an archetype (no skeleton yet — the human-confirm boundary, LOCKED-5); build runs only on
an explicitly confirmed archetype; instantiate is the deterministic, zero-LLM fallback
(manual archetype-pick on a cold/unreachable MS-S1, the D9 graceful degradation).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from services.api.models.procedures import ProcedureView
from services.engine.procedures.draft import GovernanceStub


def _empty_allowed() -> dict[str, list[str]]:
    """The empty agent allowlist a fresh draft carries — an agent-side H stub (D3)."""
    return {"step_kinds": [], "action_handlers": []}


class ArchetypeChoice(BaseModel):
    """One catalogued archetype the operator may pick manually (the D9 fallback)."""

    model_config = ConfigDict(extra="forbid")

    archetype_id: str = Field(description="the catalogued archetype id, e.g. 'AT-1'")
    title: str = Field(description="the archetype's human-readable title")


class ProposedMatchView(BaseModel):
    """A classify proposal awaiting human confirmation (LOCKED-5) — no skeleton yet."""

    model_config = ConfigDict(extra="forbid")

    archetype_id: str = Field(description="the proposed catalogued archetype id")
    title: str = Field(description="the proposed archetype's title")
    confidence: float = Field(
        description="model-asserted confidence — ADVISORY ONLY (ADR-010 IN-3); NEVER routes"
    )
    rationale: str = Field(default="", description="why this archetype fits — advisory prose")


class DraftAgentView(BaseModel):
    """The placeholder agent on a generated draft. Its governance bindings
    (``llm_model`` / ``autonomy_ceiling`` / ``allowed``) are agent-side H stubs the human
    authors — emitted ABSENT (null / empty), never a spec default value (D3). (The runtime
    :class:`~services.engine.procedures.spec.Agent` defaults ``llm_model`` to a real model,
    so the draft cannot reuse it without masking the stub.)"""

    model_config = ConfigDict(extra="forbid")

    agent_id: str = Field(description="the placeholder agent slug the human binds")
    name: str = Field(description="placeholder agent name (a human authoring prompt)")
    llm_model: str | None = Field(
        default=None, description="bound model — an H stub the human binds"
    )
    autonomy_ceiling: str | None = Field(
        default=None, description="autonomy ceiling — an H stub the human binds"
    )
    allowed: dict[str, list[str]] = Field(
        default_factory=_empty_allowed,
        description="blast-radius allowlist — an H stub the human authors (empty on a fresh draft)",
    )


class DraftProcedureView(ProcedureView):
    """A generated procedure skeleton + its archetype label + the "YOU must author"
    worklist (OQ-C / AC-A7), keyed by step_id. Subclasses the read-mode
    :class:`ProcedureView` so every typed step/facet field is byte-identical to the read
    surface — the edit-mode renderer reuses the same decomposition (LOCKED-8)."""

    governance_todo: dict[str, list[GovernanceStub]] = Field(
        default_factory=dict,
        description="per-step unfilled governance obligations driving the gate's author zone",
    )


class DraftVerticalView(BaseModel):
    """One vertical wrapper for a generated draft (mirrors the read-mode vertical view)."""

    model_config = ConfigDict(extra="forbid")

    vertical: str = Field(description="the target vertical the procedure will run in")
    namespace: str | None = Field(default=None, description="the draft's namespace")
    version: int | None = Field(default=None, description="the draft's spec version (0 = a draft)")
    agents: list[DraftAgentView] = Field(description="the placeholder agent the human binds")
    procedures: list[DraftProcedureView] = Field(description="the one generated draft procedure")


class DraftEnvelope(BaseModel):
    """The gate-render payload — ``GET /procedures``-shaped + ``governance_options``.
    Byte-shape-identical to ``gate-fixture.js`` so the edit-mode renderer reuses its path
    verbatim (LOCKED-8)."""

    model_config = ConfigDict(extra="forbid")

    verticals: list[DraftVerticalView] = Field(description="one vertical, one generated draft")
    governance_options: dict[str, list[str]] = Field(
        description="the LEGAL authoring domains (the allowlist a human picks from — never a "
        "value, D4): direction / autonomy / handler"
    )


# --------------------------------------------------------------------------- #
# request / response wrappers
# --------------------------------------------------------------------------- #


class ClassifyRequest(BaseModel):
    narrative: str = Field(min_length=1, description="operator's free-text procedure narrative")
    vertical: str = Field(min_length=1, description="the target vertical the procedure will run in")


class ClassifyResponse(BaseModel):
    state: Literal["match", "abstain", "degraded"] = Field(
        description="match = a proposed archetype awaiting confirm; abstain = no catalogued fit "
        "(hand-author); degraded = MS-S1 unavailable (pick an archetype manually)"
    )
    match: ProposedMatchView | None = Field(
        default=None, description="the proposed archetype (present when state=match)"
    )
    reason: str | None = Field(default=None, description="abstain/degrade machine code")
    detail: str | None = Field(default=None, description="human-readable why (abstain/degraded)")
    catalog: list[ArchetypeChoice] = Field(
        default_factory=list,
        description="the manual-pick catalog — ALWAYS present (the D9 fallback)",
    )


class BuildRequest(BaseModel):
    narrative: str = Field(
        min_length=1, description="the same narrative the archetype was proposed from"
    )
    vertical: str = Field(min_length=1, description="the target vertical")
    archetype_id: str = Field(description="the human-CONFIRMED archetype id (LOCKED-5)")
    confirmed: bool = Field(
        description="explicit human confirmation — build REFUSES unless true (no-bypass, LOCKED-5)"
    )
    band_source: Literal["in_file", "env"] = Field(
        default="in_file", description="the judge's band mechanism (in-file value vs env binding)"
    )


class BuildResponse(BaseModel):
    state: Literal["ok", "abstain", "degraded"] = Field(
        description="ok = a draft behind the gate; abstain = the generator declined "
        "(hand-author); degraded = MS-S1 unavailable"
    )
    draft: DraftEnvelope | None = Field(
        default=None, description="the gate-render envelope (present when state=ok)"
    )
    reason: str | None = Field(default=None, description="abstain/degrade machine code")
    detail: str | None = Field(default=None, description="human-readable why (abstain/degraded)")
    prose_attempts: int | None = Field(
        default=None, description="prose-call attempts consumed (present when state=ok)"
    )


class InstantiateRequest(BaseModel):
    archetype_id: str = Field(description="the manually-picked catalogued archetype id")
    vertical: str = Field(min_length=1, description="the target vertical")
    title: str = Field(default="", description="optional draft title (defaults to archetype title)")
    band_source: Literal["in_file", "env"] = Field(
        default="in_file", description="the judge's band mechanism"
    )


class InstantiateResponse(BaseModel):
    state: Literal["ok"] = Field(description="always ok — a deterministic, zero-LLM skeleton")
    draft: DraftEnvelope = Field(description="the deterministic gate-render envelope (zero-LLM)")
