"""The two narrow LLM-call schemas for the procedure generator (ADR-0024 D1;
PLAN-0040 Phase B, Step B1).

The generator makes **two** narrow LLM calls per successful run (LOCKED-1 / D1) — one
classify + one prose (a repair retry adds further prose calls) — each emitting a small
TYPED JSON object, never YAML, never structure:

* **S1 classify** (:class:`Classification`) — the LLM SELECTS one archetype from the
  closed catalog enum (classify-don't-synthesize, ADR-0021): ``archetype_id`` is the
  whole-procedure label that drives instantiation; ``step_gates`` is the per-step
  ``gate_kind`` emitted *and* checked against the template oracle (OQ-3 both
  granularities). ``confidence`` is **advisory only** (ADR-010 IN-3) — recorded, never
  routed on (the determinism invariant, LOCKED-5).
* **S5 prose** (:class:`ProseResponse`) — advisory prose ONLY (``description`` + facet
  notes + a title). It carries **zero governance fields** by construction, so a typed
  governance value cannot ride this schema; a value smuggled into the *prose* is caught
  by ``prose_lint`` (D3 mechanism 2). Per OQ-B (B2-ratified) the generator leaves
  ``goal`` empty in Phase B — goal generation rides with Phase C's elevated-scrutiny
  zone — so this schema does NOT draft a goal.

Both calls are STRUCTURING calls (they pass Ollama ``format``), so callers OMIT
``think`` — never ``think=False`` together with ``format`` (the CHECKPOINT-0 / Ollama
#15260 caller contract, ADR-001).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from services.engine.procedures.archetypes.template import REGISTRY
from services.engine.procedures.spec import GateKind

ABSTAIN = "abstain"
"""The explicit abstain label. Abstaining is the LLM *picking this enum member* (no
catalogued archetype fits) — NOT the harness thresholding a confidence float (LOCKED-5
/ ADR-0019: the route never depends on model confidence)."""

ARCHETYPE_CHOICES: tuple[str, ...] = (*REGISTRY, ABSTAIN)
"""The closed enum handed to the classify call: the v1 catalog (the AT-1 family, D7)
plus ``abstain``. AT-2 is absent by construction — an AT-2-class narrative routes to
``abstain`` (LOCKED-7), never a down-classified AT-3 skeleton."""


class StepGate(BaseModel):
    """One per-step ``gate_kind`` the LLM infers from the narrative — the OQ-3 cross-check
    signal. The *structure* still comes from the template (code synthesizes, D1); this is
    only checked against the template oracle, and a disagreement (or any AT-2-only kind)
    is a deterministic abstain (LOCKED-4 / AC-A8)."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(description="the step this gate classification refers to")
    gate_kind: GateKind = Field(
        description="the decision-condition kind the narrative implies for this step "
        "(checked against the archetype oracle; 'none' for read/act, a band kind for the judge)"
    )


class Classification(BaseModel):
    """S1 output — the closed-enum archetype pick + the per-step gate cross-check.

    ``archetype_id`` is one of :data:`ARCHETYPE_CHOICES`; the *route* is a deterministic
    function of this label (LOCKED-5). ``confidence`` is advisory metadata only — it is
    recorded in provenance and NEVER appears in a routing branch."""

    model_config = ConfigDict(extra="forbid")

    archetype_id: str = Field(
        description="the single best-fit catalogued archetype_id, or 'abstain' (closed enum)"
    )
    step_gates: list[StepGate] = Field(
        default_factory=list,
        description="per-step gate_kind classification (OQ-3 cross-check; may be empty)",
    )
    rationale: str = Field(default="", description="why this archetype fits — advisory prose")
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="model-asserted confidence — ADVISORY ONLY (ADR-010 IN-3); NEVER routes",
    )


class StepProse(BaseModel):
    """Advisory prose for one step — ``description`` + the three non-authoritative facet
    notes (G, D3). No governance field exists on this type, so a typed value cannot ride
    it; a value laundered into the prose strings is caught by ``prose_lint`` (D3 mech 2)."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(description="the step this prose describes")
    description: str = Field(
        default="", description="advisory description — NO values / handlers / decisions"
    )
    input_note: str | None = Field(default=None, description="non-authoritative facet note")
    output_note: str | None = Field(default=None, description="non-authoritative facet note")
    governance_note: str | None = Field(default=None, description="non-authoritative facet note")


class ProseResponse(BaseModel):
    """S5 output — a title + per-step advisory prose. Carries NO ``goal`` (OQ-B B2: goal
    generation defers to Phase C's elevated-scrutiny zone) and no governance value."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(default="", description="advisory procedure title prose")
    steps: list[StepProse] = Field(default_factory=list)


def classification_schema() -> dict[str, Any]:
    """The JSON Schema handed to Ollama ``format`` for S1 — ``archetype_id`` constrained
    to the closed :data:`ARCHETYPE_CHOICES` enum so constrained generation cannot invent
    an archetype (classify-don't-synthesize). ``gate_kind`` is already enum-constrained by
    the :class:`GateKind` ``StrEnum``."""
    schema: dict[str, Any] = Classification.model_json_schema()
    schema["properties"]["archetype_id"]["enum"] = list(ARCHETYPE_CHOICES)
    return schema


def prose_schema() -> dict[str, Any]:
    """The JSON Schema handed to Ollama ``format`` for S5 (advisory prose only)."""
    return ProseResponse.model_json_schema()
