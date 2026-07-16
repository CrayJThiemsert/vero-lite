"""The deterministic ``supply_chain`` procedure-executor factory (PLAN-0062 Step 2, AC-5;
extended to the AT-2 disposition by PLAN-0074 Step 4, AC-10).

Originally the exact shape of ``verticals/energy/procedures_factory.py`` over the cold-chain
ontology — which was the point: two verticals, one grammar, one band executor, one advisory stub,
zero new engine surface. PLAN-0074 adds the vertical's **second** procedure — the AT-2 governed
``cold_chain_excursion_disposition`` (the 2nd AT-2 signature, non-money authority) — so this
factory now binds the AT-2 governance wrappers too. ``discover_and_register`` registers adapters +
handlers only (OQ-6), so the HTTP run/resume surface 409s ("no procedure-executor factory") until a
vertical registers one explicitly. This is that registration for ``supply_chain``, wired
active-vertical-scoped at API startup (``services/api/main.py``).

**Both procedures run through ONE factory** (the orchestrator's ``StepKind``-keyed contract is
per-run, not per-procedure), so every slot is a DELEGATING wrapper that falls through untouched for
the step it does not govern — the AT-3 sweep is byte-identical (PLAN-0074 AC-9):

* ``QUERY`` — :class:`QueryStepRouter` (PLAN-0064's declaration-presence routing): the sweep's
  ``read_temps`` DECLARES ``input.reads``, so it dispatches to the shipped
  :class:`QueryStepExecutor` over the registry's warmed adapter and the REAL supply_chain ontology
  meta (unchanged). The disposition's ``intake`` declares none, so it takes the seed leg — the
  enriched excursion intake below (data-access = (a), the procurement ``_SeedQuery`` precedent:
  a relational read cannot produce the DERIVED intake fields without a transform grammar, which
  is ADR-0031 D3 row-1 and deliberately out of scope).
* ``EVALUATE`` — :class:`GovernanceEvaluateExecutor` over the existing
  :class:`EnvBandEvaluateExecutor`: the disposition's band-less ``gdp_gate`` carries
  ``rule_gate`` content and dispatches to the deterministic compliance gate; the sweep's banded
  ``judge`` carries none, so it falls through to the env-band wrapper exactly as before (and its
  authored ``threshold_field`` makes THAT wrapper delegate straight to the shipped band executor —
  PLAN-0067).
* ``ACTION`` — :class:`ColdChainAssessExecutor` (the vertical's SD-2 severity action-stamp, which
  only touches ``assess``) over the shipped :class:`GovernanceActionExecutor` (``scored_rule`` at
  ``assess``, ``severity_tier`` at ``approve``) over the shipped :class:`ActionStepExecutor` bound
  to :func:`advisory_stub_factory` (OQ-1: no live MS-S1 call). The sweep's ``hold_breaches``
  carries no governance content and is not a stamp step, so it reaches the base executor
  unchanged. Every gated action still SUSPENDS at ``waiting_human`` — nothing is executed.

``sod_steps`` is DERIVED from the spec's own ``separation_of_duties`` constraints, not hardcoded
(procurement hardcodes ``frozenset({"intake","approve"})`` at ``hero_demo/run.py:278`` — a named
drift point in PLAN-0074's coordination-point list: a renamed step there silently drops the
``sod_required`` flag. Deriving it cannot drift on a RENAME.) One residual limitation, recorded for
the gate-seam follow-on: the registry contract is ``factory() -> Mapping[StepKind, StepExecutor]``
with no ``procedure`` argument, so both ``sod_steps`` and ``stamp_steps`` are VERTICAL-scoped
(unioned across every procedure) while the thing they configure is procedure-scoped. Today no
``step_id`` collides across supply_chain's two procedures, so this is inert; a second procedure
reusing a step name (``approve`` / ``assess``) would over-mark ``sod_required`` (an audit-flag
over-mark, never an enforcement gap — the live SoD check reads ``procedure.separation_of_duties``
directly) or route a stray ``assess`` through the severity stamp (which fails CLOSED). The proper
fix is to key both on ``(procedure_id, step_id)``, which needs the executor to know its procedure —
an engine-contract change (the ADR-0031 gate-plugin seam), out of scope here.

Deterministic and host-state-free end to end (PLAN-0062 SD-6; CLAUDE.md §8): synthetic adapter,
pure band math, pure AT-2 resolution, stubbed advisory prose. Idempotent: a no-op when a
``supply_chain`` factory is already registered.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from services.engine.ontology_meta import load_ontology_meta
from services.engine.procedures.action_step import ActionStepExecutor
from services.engine.procedures.advisory_stub import advisory_stub_factory
from services.engine.procedures.env_band_step import EnvBandEvaluateExecutor
from services.engine.procedures.evaluate_step import EvaluateStepExecutor
from services.engine.procedures.governance_step import (
    GovernanceActionExecutor,
    GovernanceEvaluateExecutor,
)
from services.engine.procedures.orchestrator import RunContext, StepExecutor, StepOutcome
from services.engine.procedures.query_router import QueryStepRouter
from services.engine.procedures.query_step import QueryStepExecutor
from services.engine.procedures.spec import Person, Step, StepKind, load_procedures
from services.engine.procedures.transform_step import TransformStepExecutor
from services.engine.registry import RegistryError, registry
from verticals.supply_chain.cold_chain_assess import (
    ColdChainAssessExecutor,
)
from verticals.supply_chain.cold_chain_assess import (
    derivation_hash as cold_chain_derivation_hash,
)

_VERTICAL = "supply_chain"
_ASSESS_STEP = "assess"
_INCIDENT_SHIPMENT = "shipment-pharma-01"
_CURRENCY = "THB"


@dataclass(frozen=True)
class _DispositionSeed:
    """The QUERY executor for the disposition's ``intake`` — the enriched excursion the run threads
    forward (the procurement ``_SeedQuery`` precedent, data-access = (a)).

    Why a seed and not a declared read: the gates downstream consume DERIVED intake fields the
    relational grammar cannot produce — the excursion's duration + the cargo's stability budget (the
    severity derivation's inputs), the candidate disposition lanes (the ``scored_rule``'s
    ``candidate_quotes``), and the per-criterion GDP signal map (the ``rule_gate``'s
    ``compliance``). Producing them from a join needs a transform StepKind — ADR-0031 D3 row-1,
    deliberately deferred. The seed's MEASURED half is real adapter data (see :func:`_intake_seed`);
    only the derived/authored half is synthesised here, and it is labelled as such."""

    seed: list[Any]

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(
            output=list(self.seed),
            reasoning_trace=[
                {"kind": "query", "summary": "intake: the enriched cold-chain excursion seed"}
            ],
        )


def _latest_breach_reading(
    events: list[dict[str, Any]], shipment_id: str
) -> Mapping[str, Any] | None:
    """The latest ``reading`` for ``shipment_id`` (by ``occurred_at``) — the excursion the sweep
    would have flagged. ``event_type`` is filtered exactly as the sweep's declared query does: the
    door-open ALARM is newer and carries no ``measured_value``, so an unfiltered latest-per-group
    would read the wrong row (the load-bearing filter, ``procedures.yaml``)."""
    readings = [
        e
        for e in events
        if e.get("event_type") == "reading"
        and e.get("shipment_id") == shipment_id
        and e.get("measured_value") is not None
    ]
    if not readings:
        return None

    def _occurred(e: dict[str, Any]) -> tuple[int, Any]:
        # Order by the datetime itself (a lexicographic str() sort mis-picks across mixed tz
        # offsets / naive-vs-aware). A non-datetime column falls back to its string form, ranked
        # AFTER every real datetime so a malformed row never wins "latest".
        occurred = e.get("occurred_at")
        if isinstance(occurred, datetime):
            return (0, occurred)
        return (1, str(occurred))

    return max(readings, key=_occurred)


async def _intake_seed(adapter: Any) -> list[dict[str, Any]]:
    """Build the disposition intake for the breaching pharma batch — deterministic, offline.

    MEASURED (real adapter data): the shipment, its per-cargo ``temp_ceiling``, and the latest
    reading — so ``excursion_magnitude_c`` is the REAL breach height (reading minus the cargo's own
    ceiling), the same number the sweep's judge bands on.

    AUTHORED (the derived/enrichment half a relational read cannot produce — see the
    :class:`_DispositionSeed` docstring): the excursion's duration, the cargo's stability budget,
    the ELIGIBLE disposition lanes, and the GDP compliance signals. Provisional until a design
    partner signs the real cold-chain figures — the same standing as procurement's provisional
    DOA/scoring values.

    **Lane ELIGIBILITY is upstream of the rule** (data-access = (a)): a batch whose stability budget
    is spent does not carry the release lane among its candidates — releasing a compromised pharma
    batch is not a cheaper option, it is an unlawful one. The scored rule RANKS eligible lanes; it
    never decides eligibility. (A declarative eligibility predicate is a follow-on — it would want
    the same grammar row-1 wants.)"""
    shipments = await adapter.fetch_objects("Shipment")
    events = await adapter.fetch_objects("OperationalEvent")
    shipment = next(
        (s for s in shipments if s.get("shipment_id") == _INCIDENT_SHIPMENT),
        None,
    )
    reading = _latest_breach_reading(events, _INCIDENT_SHIPMENT)
    if shipment is None or reading is None:
        return []  # no excursion in the dataset — the run intakes nothing (never a fabricated one)

    def _num(row: Mapping[str, Any], key: str) -> Decimal | None:
        # A required scalar off an adapter row, as an EXACT Decimal. Returns None (-> the seed
        # intakes nothing, like an absent shipment above) rather than KeyError-ing: this runs
        # inside the awaited API-lifespan registration, so a raise here would kill startup for an
        # ontology-legal row that merely omits an OPTIONAL property.
        if key not in row:
            return None
        try:
            return Decimal(str(row[key]))
        except (InvalidOperation, TypeError, ValueError):
            return None

    reading_c = _num(reading, "measured_value")
    ceiling = _num(shipment, "temp_ceiling")
    if reading_c is None or ceiling is None:
        return []
    magnitude_c = reading_c - ceiling  # EXACT Decimal, never a rounded binary float
    if magnitude_c <= 0:
        return []  # the latest reading is within the cargo's band — nothing to dispose of

    return [
        {
            # --- identity (measured) ---
            "shipment_id": shipment.get("shipment_id"),
            "batch_id": shipment.get("reference"),
            "cargo_type": shipment.get("cargo_type"),
            "facility_id": shipment.get("facility_id"),
            "temp_ceiling": str(ceiling),
            "reading_c": str(reading_c),
            "event_id": reading.get("event_id"),
            # --- the severity derivation's inputs (magnitude measured; the rest authored) ---
            "excursion_magnitude_c": str(magnitude_c),
            "excursion_duration_h": 9,  # authored: how long the reefer stayed out of band
            "stability_budget_ch": 24,  # authored: the vaccine lot's remaining MKT dose budget
            # --- the scored_rule's candidates (authored; ELIGIBLE lanes only — see docstring) ---
            "qty": str(
                shipment.get("payload_kg", 1)
            ),  # optional ontology prop -> .get, never KeyError
            "currency": _CURRENCY,
            "candidate_quotes": [
                {
                    # the CHEAP, SLOW lane: rework is inexpensive but takes weeks — the calm choice
                    # for a mild drift where the batch can wait.
                    "quote_id": "lane-quarantine-rework",
                    "supplier_id": "reworker-bkk-01",
                    "unit_price": "60.00",
                    "currency": _CURRENCY,
                    "lead_time_days": 21,
                    "on_contract": True,
                },
                {
                    # the FAST, DEAR lane: licensed destruction is quick but costly — chosen
                    # when the excursion is critical enough that speed (the criticality amplifier)
                    # outweighs cost. Pricier than rework is what keeps the amplifier load-bearing.
                    "quote_id": "lane-licensed-destruction",
                    "supplier_id": "disposal-licensed-01",
                    "unit_price": "150.00",
                    "currency": _CURRENCY,
                    "lead_time_days": 3,
                    "on_contract": True,
                },
            ],
            # --- the rule_gate's per-criterion GDP signal map (authored) ---
            "quarantine_status": "quarantined",
            "compliance": {
                "stability_budget": True,
                "batch_quarantine": True,
                "licensed_disposal_vendor": True,
                "coa_customs": True,
            },
        }
    ]


def _sod_steps(procedures: Any) -> frozenset[str]:
    """Every SoD-constrained step across the vertical's procedures — DERIVED, never hardcoded (the
    ``sod_required`` flag on a verdict cannot drift when a step is renamed)."""
    return frozenset(
        step_id
        for procedure in procedures
        for constraint in procedure.separation_of_duties
        for step_id in constraint.distinct_steps
    )


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

    spec = load_procedures(_VERTICAL)
    principals: list[Person] = list(spec.principals)
    sod_steps = _sod_steps(spec.procedures)
    # JSONB-safe (project memory: a raw Decimal / datetime fails the JSONB column on a persisted
    # run — the disposition's `intake` executes live on any fresh run through this factory).
    seed: list[Any] = json.loads(json.dumps(await _intake_seed(adapter), default=str))

    def factory() -> Mapping[StepKind, StepExecutor]:
        # Built fresh per run/resume request (the registry Step-2 contract — a stateful
        # executor must never leak across requests); adapter + meta + principals + seed are
        # immutable read-only data captured once at registration.
        return {
            StepKind.QUERY: QueryStepRouter(
                declared=QueryStepExecutor(
                    adapter=adapter, object_type_names=object_type_names, meta=meta
                ),
                fallback=_DispositionSeed(seed),
            ),
            StepKind.EVALUATE: GovernanceEvaluateExecutor(
                base=EnvBandEvaluateExecutor(base=EvaluateStepExecutor())
            ),
            StepKind.ACTION: ColdChainAssessExecutor(
                inner=GovernanceActionExecutor(
                    base=ActionStepExecutor(client_factory=advisory_stub_factory),
                    principals=principals,
                    sod_steps=sod_steps,
                ),
                stamp_steps=frozenset({_ASSESS_STEP}),
            ),
            # PLAN-0078 Step 1 (SD-3): the shared fieldless transform executor, registered
            # uniformly across all 4 factories. Pure-additive — supply_chain declares no transform
            # step today (the PR-2 intake flip adds the first); inert until then.
            StepKind.TRANSFORM: TransformStepExecutor(),
        }

    registry.register_procedure_executors(_VERTICAL, factory)
    # PLAN-0075 AC-13 (SD-5): pin the severity-DERIVATION constants into every supply_chain run's
    # governance snapshot — the live provider (never a cached string) so a run-start↔resolve edit
    # to `_DOSE_LADDER` / `_TOP_SEVERITY` fails closed at the pin. Registered beside the factory
    # (same idempotency gate); the engine pulls it back by vertical (`registry.derivation_hash`)
    # without importing this vertical's constants.
    registry.register_derivation_hash(_VERTICAL, cold_chain_derivation_hash)
