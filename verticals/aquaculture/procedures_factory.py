"""The deterministic ``aquaculture`` procedure-executor factory (PLAN-0062 Step 3, AC-5).

The third OCT factory, and the one that proves the shape is a **choice, not a funnel**.
``discover_and_register`` registers adapters + handlers only (OQ-6), so the HTTP
run/resume surface 409s ("no procedure-executor factory") until a vertical registers one
explicitly. This is that registration for ``aquaculture``, wired active-vertical-scoped at
API startup (``services/api/main.py``).

**It does NOT bind :class:`EnvBandEvaluateExecutor`.** aquaculture's ``judge`` is an
ADR-016 D2-A3 ``in_file_band``: it authors ``threshold: 4.0`` / ``direction: below`` /
``watch_margin: 1.0`` on the ``Step`` itself (DO is a crash signal — it breaches BELOW the
floor, and the 4-5 mg/L watch band is the ADR-0019 escalate zone). The shipped
:class:`EvaluateStepExecutor` reads exactly that, so the env-band wrapper energy and
supply_chain need would be dead weight here — and binding it anyway would blur an honest
ADR-016 distinction into an accidental default. The wrapper stays what PR1b claimed it
was: the ``env`` half of a two-way split, not a mandatory pass-through.

Deterministic and host-state-free end to end (PLAN-0062 SD-6; CLAUDE.md §8):

* ``QUERY`` — the shipped generic :class:`QueryStepExecutor` over the registry's warmed
  adapter and the REAL aquaculture ontology meta, so the declared latest-per-group grammar
  (``project: {latest_per: event_emitted_by_pond, order_by: occurred_at}``) executes on
  the production path.
* ``EVALUATE`` — the shipped :class:`EvaluateStepExecutor`, unwrapped, reading the
  step-authored three-band config (breach / watch / ok).
* ``ACTION`` — the shipped :class:`ActionStepExecutor` bound to
  :func:`advisory_stub_factory` (OQ-1): no live MS-S1 call. ``aerate`` is ``gated``, so a
  run suspends at ``waiting_human`` there; the downstream ``escalate_watch`` (the ADR-0019
  watch→gated proposal) and the ``auto`` ``summary`` terminal run only **after** a human
  resolves that gate and the run resumes.

Idempotent: a no-op when an ``aquaculture`` factory is already registered.
"""

from __future__ import annotations

from collections.abc import Mapping

from services.engine.ontology_meta import load_ontology_meta
from services.engine.procedures.action_step import ActionStepExecutor
from services.engine.procedures.advisory_stub import advisory_stub_factory
from services.engine.procedures.evaluate_step import EvaluateStepExecutor
from services.engine.procedures.orchestrator import StepExecutor
from services.engine.procedures.query_step import QueryStepExecutor
from services.engine.procedures.spec import StepKind
from services.engine.procedures.transform_step import TransformStepExecutor
from services.engine.registry import RegistryError, registry

_VERTICAL = "aquaculture"


async def register_aquaculture_procedure_executors() -> None:
    """Register the deterministic ``aquaculture`` procedure-executor factory.

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

    def factory() -> Mapping[StepKind, StepExecutor]:
        # Built fresh per run/resume request (the registry Step-2 contract — a stateful
        # executor must never leak across requests); adapter + meta are immutable
        # read-only data captured once at registration.
        return {
            StepKind.QUERY: QueryStepExecutor(
                adapter=adapter, object_type_names=object_type_names, meta=meta
            ),
            StepKind.EVALUATE: EvaluateStepExecutor(),  # in_file_band — no env wrapper
            StepKind.ACTION: ActionStepExecutor(client_factory=advisory_stub_factory),
            # PLAN-0078 Step 1 (SD-3): the shared fieldless transform executor, registered
            # uniformly across all 4 factories. Pure-additive — aquaculture declares no transform
            # step today, so this is inert until a future flip.
            StepKind.TRANSFORM: TransformStepExecutor(),
        }

    registry.register_procedure_executors(_VERTICAL, factory)
