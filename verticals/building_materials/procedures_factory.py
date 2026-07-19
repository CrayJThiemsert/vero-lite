"""The deterministic ``building_materials`` procedure-executor factory (PLAN-0081 — the
governed-credit HERO; the 3rd AT-2 signature).

``discover_and_register`` registers adapters + handlers only (OQ-6), so the HTTP run/resume surface
409s ("no procedure-executor factory") until a vertical registers one explicitly. This is that
registration for ``building_materials``, wired active-vertical-scoped at API startup
(``services/api/main.py``).

The vertical ships ONE procedure — the AT-2 governed ``governed_credit_release`` — so every slot is
a wrapper that governs the step it owns and falls through untouched for the rest:

* ``QUERY`` — the shipped generic :class:`QueryStepExecutor` over the registry's warmed adapter and
  the REAL building_materials ontology meta: the ``intake`` step DECLARES ``input.reads`` +
  ``join`` + ``project`` (the ADR-016 FKP latest-per-group grammar — latest OperationalEvent per
  CustomerAccount, its ``credit_limit_thb`` joined on), so it executes on the production path. No
  seed (the aquaculture pattern, NOT the supply_chain disposition's ``_SeedQuery``: this intake is a
  pure relational read — nothing here is a DERIVED intake field a join cannot produce).
* ``EVALUATE`` — :class:`GovernanceEvaluateExecutor` over the shipped :class:`EvaluateStepExecutor`
  (no env-band wrapper — the ``judge`` authors an in-file ``threshold_field: credit_limit_thb``
  per-entity band, read directly, the aquaculture precedent). The band-less ``credit_gate`` carries
  ``rule_gate`` content and dispatches to the deterministic credit-compliance gate; the banded
  ``judge`` carries no governance content, so it falls through to the base band executor exactly.
* ``ACTION`` — :class:`GovernanceActionExecutor` over the shipped :class:`ActionStepExecutor` bound
  to :func:`advisory_stub_factory` (OQ-1: no live MS-S1 call). ``approve`` carries ``doa_tier``
  content, so the wrapper resolves the DOA tier + the SoD run-check; ``fulfill`` carries none and
  reaches the base executor unchanged. Every gated action SUSPENDS at ``waiting_human`` — nothing is
  executed until a human decides (ADR-0007 approve->execute, the only external write path).
* ``TRANSFORM`` — :class:`TransformStepExecutor`: the ``reshape`` step (measured_value ->
  amount/currency + the compliance signal map, the L-2 seam) runs as declared transform data.

``sod_steps`` is DERIVED from the spec's own ``separation_of_duties`` constraints, not hardcoded (a
renamed step cannot silently drop the ``sod_required`` flag). The residual VERTICAL-scoping
limitation the supply_chain factory records applies equally (the registry contract is
``factory() -> Mapping[StepKind, StepExecutor]`` with no ``procedure`` argument) but is inert here:
building_materials ships ONE procedure, so no ``step_id`` collides.

Deterministic and host-state-free end to end (PLAN-0062 SD-6; CLAUDE.md §8): synthetic adapter, pure
band math, pure AT-2 resolution, stubbed advisory prose. Idempotent: a no-op when a
``building_materials`` factory is already registered.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from services.engine.ontology_meta import load_ontology_meta
from services.engine.procedures.action_step import ActionStepExecutor
from services.engine.procedures.advisory_stub import advisory_stub_factory
from services.engine.procedures.evaluate_step import EvaluateStepExecutor
from services.engine.procedures.governance_step import (
    GovernanceActionExecutor,
    GovernanceEvaluateExecutor,
)
from services.engine.procedures.orchestrator import StepExecutor
from services.engine.procedures.query_step import QueryStepExecutor
from services.engine.procedures.spec import Person, StepKind, load_procedures
from services.engine.procedures.transform_step import TransformStepExecutor
from services.engine.registry import RegistryError, registry

_VERTICAL = "building_materials"


def _sod_steps(procedures: Any) -> frozenset[str]:
    """Every SoD-constrained step across the vertical's procedures — DERIVED, never hardcoded (the
    ``sod_required`` flag on a verdict cannot drift when a step is renamed)."""
    return frozenset(
        step_id
        for procedure in procedures
        for constraint in procedure.separation_of_duties
        for step_id in constraint.distinct_steps
    )


async def register_building_materials_procedure_executors() -> None:
    """Register the deterministic ``building_materials`` procedure-executor factory.

    See module docstring."""
    try:
        registry.get_procedure_executors(_VERTICAL)
        return  # already registered — idempotent
    except RegistryError:
        pass

    # The registry's adapter, not a fresh construction: the lifespan warms it
    # (``fetch_objects("OperationalEvent")``) so the demo time-anchor is process-stable.
    adapter = registry.get_adapter(_VERTICAL)
    meta = load_ontology_meta(_VERTICAL)
    object_type_names = frozenset(object_type.name for object_type in meta.object_types)

    spec = load_procedures(_VERTICAL)
    principals: list[Person] = list(spec.principals)
    sod_steps = _sod_steps(spec.procedures)

    def factory() -> Mapping[StepKind, StepExecutor]:
        # Built fresh per run/resume request (the registry Step-2 contract — a stateful executor
        # must never leak across requests); adapter + meta + principals are immutable read-only
        # data captured once at registration.
        return {
            StepKind.QUERY: QueryStepExecutor(
                adapter=adapter, object_type_names=object_type_names, meta=meta
            ),
            StepKind.EVALUATE: GovernanceEvaluateExecutor(
                base=EvaluateStepExecutor()  # in_file threshold_field band — no env wrapper
            ),
            StepKind.ACTION: GovernanceActionExecutor(
                base=ActionStepExecutor(client_factory=advisory_stub_factory),
                principals=principals,
                sod_steps=sod_steps,
            ),
            # PLAN-0078 Step 1 (SD-3): the shared fieldless transform executor. Here it runs the
            # `reshape` L-2 seam (measured_value -> amount/currency + compliance map).
            StepKind.TRANSFORM: TransformStepExecutor(),
        }

    registry.register_procedure_executors(_VERTICAL, factory)
