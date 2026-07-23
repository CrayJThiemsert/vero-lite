"""Narrative → vertical scaffolder (PLAN-0091).

Engine-generic machinery for the FDE-style intake motion: an operator arrives
with a customer narrative and leaves with an uncommitted `verticals/<ns>/`
package. Placement mirrors the ADR-0024 OQ-2 reasoning that put `archetypes/`
under `services/engine/procedures/` — the tool is vertical-agnostic engine
code, never per-vertical config.

**The compliance story, by construction (PLAN-0091 §Deliverable shape).** Every
governance *value* — ฿ tiers, roles, waiver content, criterion ids, thresholds,
synthetic-fixture numbers — enters through the typed :class:`~.intake.IntakeRecord`,
whose value slots are **operator-input-only**: this package imports no LLM
client and exposes no path from a model emission into an answer. The LLM's
surface here is unchanged from the shipped pipeline (draft-typed structure +
closed-enum classification + advisory prose behind ``prose_lint``), so
"governed ≠ generated" stays a type-level property rather than a prompt hope.
"""

from __future__ import annotations
