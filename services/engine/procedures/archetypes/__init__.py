"""Archetype templates — the machine-readable form of the procedure-archetype
catalog (ADR-0024 D2; PLAN-0040 Phase A). The prose catalog
(``docs/conventions/procedure-archetypes.md``) is canonical; this package is the
derived machine form with slots to instantiate. v1 = the AT-1 family only (D7).

See :mod:`services.engine.procedures.archetypes.template`.
"""

from services.engine.procedures.archetypes.template import (
    REGISTRY,
    ArchetypeTemplate,
    LlmAssist,
    SlotInput,
    StepSlot,
    instantiate,
)

__all__ = [
    "REGISTRY",
    "ArchetypeTemplate",
    "LlmAssist",
    "SlotInput",
    "StepSlot",
    "instantiate",
]
