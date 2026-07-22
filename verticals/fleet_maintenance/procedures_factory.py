"""The deterministic ``fleet_maintenance`` procedure-executor factory (PLAN-0086 — the governed
repair-spend HERO; the 6th vertical, hand-written under the timed-scaffold measurement).

``discover_and_register`` registers adapters + handlers only (OQ-6), so the HTTP run/resume surface
409s ("no procedure-executor factory") until a vertical registers one explicitly. This is that
registration for ``fleet_maintenance``, wired active-vertical-scoped at API startup
(``services/api/main.py``).

The vertical ships TWO procedures — the AT-2 governed ``governed_repair_approval`` (PLAN-0086) and
the AT-3 calm path ``pm_service_round`` (PLAN-0089, which discharged the tire/PM follow-on SD-3a
deferred) — so every slot is a wrapper that governs the step it owns and falls through untouched
for the rest. This factory needed NO change to gain the second procedure: it is keyed by StepKind,
not by procedure, and the calm path uses only QUERY / EVALUATE / ACTION, all already registered.
Mirrors the building_materials factory exactly, with ONE deliberate difference:

* ``ACTION`` — :class:`GovernanceActionExecutor` is constructed with
  ``advisory_builder=GateAdvisoryBuilder()`` (PLAN-0086 L-B, the PLAN-0085 wire). This vertical
  ships the gate advisory ON from day one: the parked ``approve`` step carries a grounded,
  never-raise ``advisory_recommendation`` ReasoningStep so the first operator to see the gate can
  read WHY it stopped. The builder never decides — it is trace-only (ADR-0030 D5). Every OTHER
  vertical keeps the default ``None`` and stays byte-identical (PLAN-0086 AC-4).

The rest is the shipped machinery unchanged: ``QUERY`` over the registry's warmed adapter and the
REAL fleet_maintenance ontology meta (the ``intake`` step DECLARES ``input.reads`` + ``join`` +
``project`` — latest OperationalEvent per Truck, its ``minor_repair_ceiling_thb`` joined on);
``EVALUATE`` as :class:`GovernanceEvaluateExecutor` over :class:`EvaluateStepExecutor` (``judge``
authors an in-file ``threshold_field`` per-entity band, read directly; the band-less ``quote_gate``
carries ``rule_gate`` content and dispatches to the deterministic rule gate); ``TRANSFORM`` as the
shared :class:`TransformStepExecutor` running the ``reshape`` L-2 seam (measured_value ->
amount/currency + the compliance signal map).

``sod_steps`` is DERIVED from the spec's own ``separation_of_duties`` constraints, not hardcoded (a
renamed step cannot silently drop the ``sod_required`` flag).

Deterministic and host-state-free end to end (PLAN-0062 SD-6; CLAUDE.md §8): synthetic adapter, pure
band math, pure AT-2 resolution, stubbed advisory prose, deterministic gate advisory. Idempotent: a
no-op when a ``fleet_maintenance`` factory is already registered.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from services.engine.ontology_meta import load_ontology_meta
from services.engine.procedures.action_step import ActionStepExecutor
from services.engine.procedures.advisory_stub import advisory_stub_factory
from services.engine.procedures.evaluate_step import EvaluateStepExecutor
from services.engine.procedures.gate_advisory import GateAdvisoryBuilder
from services.engine.procedures.governance_step import (
    GovernanceActionExecutor,
    GovernanceEvaluateExecutor,
)
from services.engine.procedures.orchestrator import StepExecutor
from services.engine.procedures.query_step import QueryStepExecutor
from services.engine.procedures.spec import Person, StepKind, load_procedures
from services.engine.procedures.transform_step import TransformStepExecutor
from services.engine.registry import RegistryError, registry

_VERTICAL = "fleet_maintenance"


def _sod_steps(procedures: Any) -> frozenset[str]:
    """Every SoD-constrained step across the vertical's procedures — DERIVED, never hardcoded (the
    ``sod_required`` flag on a verdict cannot drift when a step is renamed)."""
    return frozenset(
        step_id
        for procedure in procedures
        for constraint in procedure.separation_of_duties
        for step_id in constraint.distinct_steps
    )


async def register_fleet_maintenance_procedure_executors() -> None:
    """Register the deterministic ``fleet_maintenance`` procedure-executor factory.

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
                # PLAN-0086 L-B: the ONLY structural difference from the building_materials
                # template — day-one readability. Trace-only, never-raise (ADR-0030 D5).
                advisory_builder=GateAdvisoryBuilder(),
            ),
            StepKind.TRANSFORM: TransformStepExecutor(),
        }

    registry.register_procedure_executors(_VERTICAL, factory)
