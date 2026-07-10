"""The deterministic ``supply_chain`` procedure-executor factory (PLAN-0062 Step 2, AC-5).

The exact shape of ``verticals/energy/procedures_factory.py`` (PLAN-0062 PR1b) over the
cold-chain ontology — which is the point: two verticals, one grammar, one band executor,
one advisory stub, zero new engine surface. ``discover_and_register`` registers adapters +
handlers only (OQ-6), so the HTTP run/resume surface 409s ("no procedure-executor factory")
until a vertical registers one explicitly. This is that registration for ``supply_chain``,
wired active-vertical-scoped at API startup (``services/api/main.py``). With it,
supply_chain's migrated ``read_temps`` is declared ✔ · load-gated ✔ · **execution-bound ✔
on the production HTTP path**.

Deterministic and host-state-free end to end (PLAN-0062 SD-6; CLAUDE.md §8):

* ``QUERY`` — the shipped generic :class:`QueryStepExecutor` over the registry's warmed
  adapter and the REAL supply_chain ontology meta, so the declared latest-per-group
  grammar (``project: {latest_per: event_concerns_shipment, order_by: occurred_at}``)
  executes on the production path.
* ``EVALUATE`` — supply_chain's ``judge`` is an ADR-016 D2-A3 ``env_band``, exactly like
  energy's, so it reuses :class:`EnvBandEvaluateExecutor` **unchanged**: the band binds
  from ``OCT_RECOMMEND_THRESHOLD`` / ``OCT_RECOMMEND_DIRECTION`` and the shipped
  :class:`EvaluateStepExecutor` does the math. A cold-chain deployment sets the threshold
  to its ceiling (e.g. 8 °C) rather than energy's 90 °C — same executor, different env.
* ``ACTION`` — the shipped :class:`ActionStepExecutor` bound to
  :func:`advisory_stub_factory` (OQ-1): no live MS-S1 call. ``hold_breaches`` is ``gated``,
  so a run suspends at ``waiting_human`` for the operator's go/no-go rather than executing
  the irreversible hold.

Idempotent: a no-op when a ``supply_chain`` factory is already registered.
"""

from __future__ import annotations

from collections.abc import Mapping

from services.engine.ontology_meta import load_ontology_meta
from services.engine.procedures.action_step import ActionStepExecutor
from services.engine.procedures.advisory_stub import advisory_stub_factory
from services.engine.procedures.env_band_step import EnvBandEvaluateExecutor
from services.engine.procedures.evaluate_step import EvaluateStepExecutor
from services.engine.procedures.orchestrator import StepExecutor
from services.engine.procedures.query_step import QueryStepExecutor
from services.engine.procedures.spec import StepKind
from services.engine.registry import RegistryError, registry

_VERTICAL = "supply_chain"


async def register_supply_chain_procedure_executors() -> None:
    """Register the deterministic ``supply_chain`` procedure-executor factory.

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
            StepKind.EVALUATE: EnvBandEvaluateExecutor(base=EvaluateStepExecutor()),
            StepKind.ACTION: ActionStepExecutor(client_factory=advisory_stub_factory),
        }

    registry.register_procedure_executors(_VERTICAL, factory)
