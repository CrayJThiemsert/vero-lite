"""Response models for the read-only procedure viewer API (PLAN-0039 Step 1).

Surfaces every shipped procedure across all discovered verticals, decomposed
exactly as ``load_procedures`` loads it (ADR-016 D2 typed spec + the typed
``facet:`` amendment), plus the catalog **archetype** label per procedure
(``docs/conventions/procedure-archetypes.md``; OQ-5). Read-only — no mutation,
no DB, no LLM (PLAN-0039 AC-1/AC-6).

The procedure / step / agent shapes are **reused** from
``services.engine.procedures.spec`` (single source of truth) — the viewer never
re-models the spec. This layer adds only the per-procedure ``archetype``
annotation (a catalog-derived mirror; canonical = the catalog, CLAUDE.md §4
canonical→derived) and the vertical wrapper.
"""

from pydantic import BaseModel, ConfigDict, Field

from services.engine.procedures.spec import Agent, Procedure


class ProcedureView(Procedure):
    """A loaded :class:`Procedure` plus its catalog archetype label.

    Subclasses the engine ``Procedure`` so every typed field — the linear
    ``steps`` with their typed ``facet`` decomposition, the authored band, the
    handler/autonomy/tiers — is byte-for-byte the same shape the engine
    validates; the viewer never duplicates the spec grammar. ``archetype`` is the
    only addition.
    """

    archetype: str = Field(
        ...,
        description="Catalog archetype label (AT-1 / AT-1b / AT-2 / AT-3) from "
        "docs/conventions/procedure-archetypes.md (OQ-5; canonical = the catalog, "
        "this is a read-only derived mirror).",
    )


class VerticalProceduresView(BaseModel):
    """One vertical's agents + archetype-annotated procedures (read-only)."""

    model_config = ConfigDict(extra="forbid")

    vertical: str = Field(..., description="The vertical name (the registry discovery key).")
    namespace: str | None = Field(
        default=None, description="The vertical's procedures.yaml namespace (if declared)."
    )
    version: int | None = Field(
        default=None, description="The procedures.yaml spec version (if declared)."
    )
    agents: list[Agent] = Field(
        ..., description="The vertical's procedure agents — the actors that run the procedures."
    )
    procedures: list[ProcedureView] = Field(
        ...,
        description="Every procedure in the vertical, each annotated with its catalog archetype.",
    )


class ProceduresResponse(BaseModel):
    """The read-only ``GET /procedures`` payload: every discovered vertical's procedures."""

    model_config = ConfigDict(extra="forbid")

    verticals: list[VerticalProceduresView] = Field(
        ...,
        description="Every discovered vertical (registry.verticals()) with its "
        "archetype-annotated procedures; a read-only projection of load_procedures.",
    )
