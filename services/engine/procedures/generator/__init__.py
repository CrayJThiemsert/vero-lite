"""Archetype-first procedure generator (ADR-0024; PLAN-0040 Phase B).

A vertical's stakeholder NARRATIVE → an LLM classifies it to one catalogued archetype
(closed enum) → deterministic code instantiates that archetype's template → the LLM
drafts only advisory prose → a ``load_procedures``-valid skeleton behind the human-review
gate, where every governance value is an unfilled human-author stub. "governed ≠
generated" is mechanical: a typed leak is a type error (the restricted draft type), a
prose leak is a lint failure, and a stub skeleton refuses to run
(``validate_governance_complete``). See :mod:`.pipeline` for the S0-S6 stages.
"""

from __future__ import annotations

from services.engine.procedures.generator.pipeline import (
    Abstained,
    GeneratedSkeleton,
    ProposedMatch,
    build_governance_todo,
    build_skeleton,
    classify_narrative,
    generate,
)
from services.engine.procedures.generator.schemas import (
    ABSTAIN,
    ARCHETYPE_CHOICES,
    Classification,
    ProseResponse,
    StepGate,
    StepProse,
)

__all__ = [
    "ABSTAIN",
    "ARCHETYPE_CHOICES",
    "Abstained",
    "Classification",
    "GeneratedSkeleton",
    "ProposedMatch",
    "ProseResponse",
    "StepGate",
    "StepProse",
    "build_governance_todo",
    "build_skeleton",
    "classify_narrative",
    "generate",
]
