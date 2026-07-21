"""Live governance-moment runner for the Fastenal hero demo (PLAN-0045 Step 4b / C-3).

**SD-1 = Layered -- this is the LIVE-RUN arm** (the offline-fixture arm is
:mod:`verticals.procurement.hero_demo.governance_audit`). It runs the REAL Fastenal hero
procedure (``intake -> judge -> source -> compliance -> approve``) through the SHIPPED
orchestrator with the per-kind AT-2 executors, so the governance moment is **DERIVED by the run**
-- the ``scored_rule`` executor selects RapidMRO and EMITS 288,000 THB (unit_price x qty), which the
``doa_tier`` executor then resolves to ``CONTROLLER`` -- rather than read from a fixture PO total.
It produces the SAME audit contract as the offline builder, with ``source: "live-run"``.

The LLM is injected via ``client_factory`` (ADR-016 OQ-1): a stub (the offline CI gate, no
MS-S1) or the real :class:`~services.engine.llm.client.OllamaClient` (C-5, host-state -- explicit
Cray go, CLAUDE.md #8). The LLM only drafts advisory judgment / summary; the selection is the
scored rule and the tier is the doa ladder (governed != generated, ADR-0019 IN-3).

The run SUSPENDS at the ``approve`` gate (``waiting_human``); the governance moment is captured at
that suspended gate -- no PO is issued, no ``resolve_gated_step`` is called (LOCKED #3). The SoD tie
is derived from the pure :func:`~services.engine.procedures.principal_sod.check_principal_sod` (the
approver half comes from the resolved DOA approver), mirroring the offline builder. All figures are
DEMO-GRADE / PROVISIONAL (the C1 dataset).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from services.engine.actions import ControlRef, GovernedDecision
from services.engine.llm.client import ChatResult
from services.engine.llm.structured import ChatClient
from services.engine.ontology_meta import load_ontology_meta
from services.engine.procedures.action_step import ActionStepExecutor, ClientFactory
from services.engine.procedures.evaluate_step import EvaluateStepExecutor
from services.engine.procedures.event_bridge import build_event_resolver, fire_event
from services.engine.procedures.gate_advisory import GateAdvisoryBuilder
from services.engine.procedures.governance_step import (
    GovernanceActionExecutor,
    GovernanceEvaluateExecutor,
)
from services.engine.procedures.orchestrator import (
    ProcedureError,
    RunContext,
    RunResult,
    StepExecutor,
    StepOutcome,
    run_procedure,
)
from services.engine.procedures.persistence import load_run, run_procedure_persisted
from services.engine.procedures.principal_sod import PrincipalSoDVerdict, check_principal_sod
from services.engine.procedures.query_router import QueryStepRouter
from services.engine.procedures.query_step import QueryStepExecutor
from services.engine.procedures.runs import PipelineRun, PipelineRunStatus, StepResultStatus
from services.engine.procedures.spec import Person, Step, StepKind, load_procedures
from services.engine.procedures.transform_step import TransformStepExecutor
from services.engine.registry import RegistryError, registry
from verticals.procurement.data_adapter.fastenal_csv import FastenalCsvAdapter
from verticals.procurement.handlers import register_procurement_handlers
from verticals.procurement.hero_demo.governance_audit import build_hero_governance_audit
from verticals.procurement.hero_demo.procedure import (
    fastenal_hero_procedure,
    load_fastenal_principals,
)

_VERTICAL = "procurement"
_CURRENCY = "THB"
_HERO_PO = "PO-2026-0412"
_REQUESTER_ID = "req-maint-planner"
_LIVE_SOURCE = "live-run"

# The hero procedure's SoD constraint id (sorted '+'-joined distinct_steps) -- the exact SoD
# control id the engine emits + the offline builder ties on (intake != approve).
_SOD_CONSTRAINT_ID = "approve+intake"


# --------------------------------------------------------------------------- #
# The offline-safe advisory-LLM default (the C-4 endpoint client; C-5 = real MS-S1)
# --------------------------------------------------------------------------- #

_STUB_JUDGMENT = json.dumps(
    {
        "title": "Emergency source the critical set",
        "description": "A governed sourcing proposal awaiting the human DOA gate.",
        "rationale": "The scored rule selected the supplier; the LLM only summarises.",
        "confidence": 0.9,
        "affected_entities": [{"object_type": "PurchaseOrder", "primary_key": _HERO_PO}],
        "suggested_handler": "emergency_source",
        "handler_payload": {},
    }
)


class _AdvisoryStubClient:
    """A deterministic advisory-prose stub ``ChatClient`` -- the offline-safe default for the
    live-run endpoint (C-4). The run's GOVERNED decision (the scored_rule selection + the doa_tier
    resolution) is INDEPENDENT of the LLM (governed != generated, ADR-0019 IN-3), so stubbing the
    advisory prose keeps the ``?live=true`` endpoint deterministic + HOST-STATE-FREE. The C-5 live
    smoke swaps the real :class:`~services.engine.llm.client.OllamaClient` (settings-gated) for the
    live MS-S1 prose (CLAUDE.md #8)."""

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        if response_format is not None:
            return ChatResult(content=_STUB_JUDGMENT, thinking=None, model="stub", raw={})
        return ChatResult(
            content="advisory draft -- LLM prose stubbed; the governed decision is the rule",
            thinking=None,
            model="stub",
            raw={},
        )


def advisory_stub_factory(_model: str) -> ChatClient:
    """The demo-default ``client_factory`` for the live-run endpoint -- a deterministic advisory
    stub (see :class:`_AdvisoryStubClient`). Host-state-free; the live MS-S1 client is C-5."""
    return _AdvisoryStubClient()


# --------------------------------------------------------------------------- #
# Run-harness executors — the intake seed (the QUERY seam); the EVALUATE (judge /
# compliance) now uses the SHIPPED :class:`GovernanceEvaluateExecutor` (see :func:`_executors`)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class _SeedQuery:
    """The QUERY executor for ``intake`` -- returns the enriched purchase-requisition seed the run
    threads forward (the failure signal already enriched, data-access = (a)).

    CO-EXIST, not deprecated-pending-migration (PLAN-0062 SD-C / OQ-3; supersedes the
    PLAN-0048 SD-3 "nothing migrates" note, which predated the grammar). The
    join/projection grammar HAS since shipped (PLAN-0061), and
    ``tests/verticals/procurement/test_intake_shadow_parity.py`` proves the JOIN HALF of
    this seed is grammar-expressible and information-identical over the REAL
    ``FastenalCsvAdapter``: `reads: [OperationalEvent, PurchaseOrder, Quotation]`, the
    hero PO ``fuse``, quotes ``on: part_id``.

    What keeps this seed in production is the OTHER half. A relational join emits three
    FLAT rows and cannot produce the seed's derived fields. PLAN-0078 PR-1 moved the two
    that the transform grammar CAN express -- the flat ``criticality`` amplification and
    the ``unit`` / ``compliance`` defaults -- into the declared ``enrich`` transform step
    (now execution-bound ✔). The residue that keeps this seed is the cardinality-changing
    nested ``candidate_quotes`` reshape (execution-bound ✖, the PLAN-0077 SD-8 wall, L-3
    partial). So ``intake`` is declared-expressible for the join half (proven) + the flat
    derivations (migrated), while the nest keeps its production execution here.

    NEW plain single-type declared reads go through the engine default:
    ``services/engine/procedures/query_step.py`` (declared==dispatched). The three OCT
    verticals' read steps migrated there in PLAN-0062 PR1-PR3 -- and since PLAN-0064 the
    production procurement factory routes per step too: this seed is the router's
    FALLBACK leg (undeclared steps only); the declared ``read_stock`` dispatches to the
    shipped executor over the registry-registered adapter."""

    seed: list[Any]

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(
            output=list(self.seed),
            reasoning_trace=[{"kind": "query", "summary": "intake: enriched requisition seed"}],
        )


def _ensure_handlers() -> None:
    """Register the procurement no-op action handlers if absent (idempotent) -- the shipped
    ``emergency_source`` / ``request_approval`` / ``issue_po`` / ``echo`` stubs the auto/gated
    action steps resolve via the gate. A no-op when they are already registered (a live app
    registers them at startup)."""
    try:
        registry.get_handler(_VERTICAL, "echo")
        return
    except RegistryError:
        pass
    try:
        register_procurement_handlers()
    except RegistryError:
        pass  # a partial/concurrent registration already covers them — idempotent


def _normalize_quotes(quotes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map the adapter's ``Quotation`` rows to the ``scored_rule`` candidate-quote shape (the
    intake enrichment, data-access = (a)): ``price_thb`` -> ``unit_price`` (Decimal, kept exact)."""
    return [
        {
            "quote_id": q["quote_id"],
            "supplier_id": q["supplier_id"],
            "unit_price": q["price"],  # PLAN-0083: canonical (was price_thb)
            "currency": q.get("currency", _CURRENCY),
            "lead_time_days": q["lead_time"],  # PLAN-0083: canonical (was lead_time_days)
            "on_contract": q["on_contract"],
        }
        for q in quotes
    ]


async def _intake_seed(adapter: FastenalCsvAdapter, *, po_id: str = _HERO_PO) -> dict[str, Any]:
    """Assemble the purchase-requisition the run scores (data-access = (a), Cray-confirmed s91):
    the failure event supplies the reading; the ``po_id`` row supplies the requisition metadata
    (part / asset / qty -- the GOVERNED supplier + amount + tier are RE-DERIVED by the run, never
    read from the PO); the quotes are normalised to the rule shape. ``po_id`` defaults to the
    hero PO (PLAN-0084 Step 5 rotation: a rotated seed passes another asset's PO; every other
    caller -- including the event/sharing builders -- keeps today's hero behaviour untouched).

    PLAN-0078 PR-1: the three DERIVED intake fields the seed used to emit -- ``criticality``
    (execution-bound ✔), ``unit`` (✔), and the per-criterion ``compliance`` map (✔) -- are now the
    declared ``enrich`` transform step's data (``procedures.yaml``, between ``intake`` and
    ``judge``), NOT hand-coded here. The remaining seed residue is the nested ``candidate_quotes``
    reshape (a cardinality-changing nest the v1 grammar cannot express -- execution-bound ✖, L-3
    partial) + the raw adapter reads."""
    events = await adapter.fetch_objects("OperationalEvent")
    pos = {p["po_id"]: p for p in await adapter.fetch_objects("PurchaseOrder")}
    req = pos[po_id]
    # PLAN-0084 Step 5: the failure pick is ASSET-KEYED (the PO's equipment), never first-row —
    # the fixture now ships one failure event per rotatable asset, so a positional pick would
    # be row-order-dependent. The default path still lands EVT-CNC-014-FAIL, by key (AC-3).
    failure = next(
        e
        for e in events
        if e["event_type"] == "failure" and e["equipment_id"] == req["equipment_id"]
    )
    quotes = [q for q in await adapter.fetch_objects("Quotation") if q["part_no"] == req["part_no"]]
    return {
        "event_id": failure["event_id"],
        # PLAN-0073 SD-1a: carry the failure event_type forward so the Box-4 economic-impact
        # producer's emergency-trigger guard (economic_impact._is_emergency_trigger) FIRES on the
        # governed run's `source` action (event_type threads intake -> judge -> source). Additive
        # key; the scored_rule / doa_tier / rule_gate steps never read it (no behaviour change).
        "event_type": failure["event_type"],
        "object_type": "PurchaseOrder",
        "primary_key": req["po_id"],
        # PLAN-0083 (c1): the seed's OWN output keys ("asset_id"/"part_id") stay as this seed's
        # downstream contract (Out of Scope); only the adapter READS flip to canonical names.
        "asset_id": req["equipment_id"],  # SD-4a
        "part_id": req["part_no"],
        # the reading the judge bands (>= 0.8 -> breach -> the emergency-sourcing path). Also the
        # SOURCE the declared `enrich` transform copies into `criticality` (PLAN-0078 PR-1): the
        # derived `criticality` + `unit` default + per-criterion `compliance` map are NO LONGER
        # emitted here — they are the `enrich` transform step's declared data (procedures.yaml,
        # between `intake` and `judge`). NARRATIVE (now expressed by the transform's compliance
        # default = all True): the hero passes every criterion, so the rule_gate does not block the
        # PO. RapidMRO is OFF_AVL and is selected via the logged RFQ->AVL exception (the
        # scored_rule's source_path: exception_policy); the `avl` spec allows "a logged emergency
        # AVL exception", so `avl` passes VIA that documented exception (coherent with off-AVL).
        "measured_value": failure["measured_value"],
        "qty": req["qty"],  # the hero-knob qty (3) -> 96,000 x 3 = 288,000
        "candidate_quotes": _normalize_quotes(quotes),  # the nested reshape stays seed-side (L-3)
        # requisition metadata for the audit contract (the governed fields are re-derived)
        "order_type": req["order_type"],
        "is_off_avl_override": req["is_off_avl_override"],
        "declared_tier_id": req["required_tier_id"],
    }


# PLAN-0085 SD-3 (as ratified): the advisory fires at EVERY doa_tier gate this
# vertical runs — seed, HTTP, scheduled, event — because every entrypoint builds its
# executors HERE. Default = on (the frozen builder is immutable/shareable); passing
# advisory_builder=None explicitly disables it (the AC-4 baseline arm in tests).
_DEFAULT_GATE_ADVISORY = GateAdvisoryBuilder()


def _executors(
    client_factory: ClientFactory,
    principals: list[Person],
    seed: list[Any],
    *,
    declared_query: StepExecutor | None = None,
    advisory_builder: GateAdvisoryBuilder | None = _DEFAULT_GATE_ADVISORY,
) -> dict[StepKind, StepExecutor]:
    """The per-kind executors for the live run: QUERY seeds the requisition (routed per step
    when a ``declared_query`` leg is supplied -- PLAN-0064, below); EVALUATE is the AT-2
    governance wrapper (``rule_gate`` at ``compliance``, falling through to the shipped
    :class:`EvaluateStepExecutor` for the banded ``judge``); ACTION is the AT-2 governance wrapper
    (scored_rule at ``source``, doa_tier at ``approve``) over the shipped
    :class:`ActionStepExecutor` base. The band-less ``compliance`` step now runs the SHIPPED
    ``rule_gate`` gate end-to-end (no stub) -- :class:`GovernanceEvaluateExecutor` dispatches its
    ``ComplianceGate`` content to the deterministic
    :func:`~services.engine.procedures.rule_gate.evaluate_compliance`.

    PLAN-0064 (SD-1/SD-2): when ``declared_query`` is supplied (the production factory,
    :func:`register_procurement_procedure_executors`), the QUERY slot is the per-step
    :class:`QueryStepRouter` -- a step DECLARING ``input.reads`` (the calm-path ``read_stock``)
    dispatches to the shipped declared-grammar executor, while an undeclared step (``intake``)
    keeps the co-existing :class:`_SeedQuery` byte-identically (PLAN-0062 SD-C carried). The
    offline hero/demo helpers pass no declared leg and keep the bare seed slot (their
    procedures declare no reads)."""
    action = GovernanceActionExecutor(
        base=ActionStepExecutor(client_factory=client_factory),
        principals=principals,
        sod_steps=frozenset({"intake", "approve"}),
        # PLAN-0085 SD-1(b)/SD-3: procurement is the only vertical supplying the
        # advisory builder in v1 — other verticals pass None and stay byte-identical.
        advisory_builder=advisory_builder,
    )
    seed_query: StepExecutor = _SeedQuery(seed)
    query: StepExecutor = (
        QueryStepRouter(declared=declared_query, fallback=seed_query)
        if declared_query is not None
        else seed_query
    )
    return {
        StepKind.QUERY: query,
        StepKind.EVALUATE: GovernanceEvaluateExecutor(base=EvaluateStepExecutor()),
        StepKind.ACTION: action,
        # PLAN-0078 Step 1 (SD-3): the shared fieldless transform executor, registered uniformly
        # across all 4 factories. Pure-additive at Step 1 — no procedure declares a transform yet;
        # the PR-1 intake flip adds the first (the `enrich` step between `intake` and `judge`).
        StepKind.TRANSFORM: TransformStepExecutor(),
    }


def _sod_projection(
    verdict: PrincipalSoDVerdict,
    *,
    requester_id: str,
    approver_id: str | None,
    by_id: dict[str, Person],
) -> dict[str, Any]:
    """The render-friendly SoD projection (who requested vs approved + whether the distinct-
    principals constraint held) -- the same structured field the offline builder emits (no
    reshape)."""

    def _who(person_id: str | None) -> dict[str, Any] | None:
        if person_id is None:
            return None
        person = by_id.get(person_id)
        return {
            "person_id": person_id,
            "name": person.name if person else None,
            "roles": sorted(person.roles) if person else [],
        }

    return {
        "governed": verdict.governed,
        "constraint_id": _SOD_CONSTRAINT_ID,
        "requester": _who(requester_id),
        "approver": _who(approver_id),
        "violations": [
            {"kind": str(v.kind), "detail": v.detail, "steps": list(v.steps)}
            for v in verdict.violations
        ],
    }


async def run_hero_governance_moment(
    adapter: FastenalCsvAdapter | None = None,
    *,
    client_factory: ClientFactory,
    run_id: str = "hero-live",
) -> dict[str, Any]:
    """Run the Fastenal hero procedure to the suspended ``approve`` gate and capture the LIVE
    governance-moment audit (PLAN-0045 C-3).

    Returns the hero audit in the offline builder's ``_audit_for_po`` shape -- but every governed
    field is DERIVED by the run: ``supplier_id`` + ``amount`` come from the ``scored_rule``
    selection, ``doa_tier`` from the ``approve`` gate's resolved tier, and the SoD tie from the
    pure run-check. Raises :class:`ProcedureError` if the run does not suspend at ``approve`` with a
    doa_tier audit (the section-3 threading would be broken)."""
    adapter = adapter or FastenalCsvAdapter()
    _ensure_handlers()
    proc, agent = fastenal_hero_procedure()
    principals = await load_fastenal_principals(adapter)
    by_id = {p.person_id: p for p in principals}
    requester = by_id[_REQUESTER_ID]

    seed = [await _intake_seed(adapter)]
    result = await run_procedure(
        proc,
        agent,
        _executors(client_factory, principals, seed),
        vertical=_VERTICAL,
        run_id=run_id,
        principal=requester,
    )

    source_sr = next(s for s in result.step_results if s.step_id == "source")
    approve_sr = next(s for s in result.step_results if s.step_id == "approve")
    if approve_sr.status != StepResultStatus.WAITING_HUMAN.value:
        raise ProcedureError(
            f"hero live run '{run_id}': the approve gate did not suspend at waiting_human "
            f"(status '{approve_sr.status}') -- the scored_rule -> doa_tier spend threading is "
            "broken"
        )
    source_audit = source_sr.audit or {}
    approve_audit = approve_sr.audit or {}
    if "scored_rule" not in source_audit or "doa_tier" not in approve_audit:
        raise ProcedureError(
            f"hero live run '{run_id}': missing scored_rule / doa_tier audit — the AT-2 executors "
            "did not annotate the run (section-3 finding)"
        )
    [scored] = source_audit["scored_rule"]
    [doa_verdict] = approve_audit["doa_tier"]
    approver_id = doa_verdict["resolved_approver_id"]

    step_principals: dict[str, str | None] = {"intake": _REQUESTER_ID, "approve": approver_id}
    sod_verdict = check_principal_sod(
        proc, principals=principals, principal_aliases=[], step_principals=step_principals
    )

    governed_decision = list(approve_audit.get("governed_decision", []))
    if approver_id is not None and sod_verdict.governed:
        # Both audit-to-control ties are emitted at gate RESOLUTION (resolve_gated_step); the run
        # only suspends here, so derive them from the pure checks (mirrors the offline builder).
        governed_decision.append(
            GovernedDecision(
                control_ref=ControlRef(kind="sod", id=_SOD_CONSTRAINT_ID),
                principal_id=approver_id,
            ).model_dump(mode="json")
        )
        # PLAN-0075 SD-6(a): the AUTHORITY tie names the acting approver (who holds the resolved
        # tier role). The run-time audit no longer carries it, so derive it here to match the
        # engine's gate-time emission (the suspended run itself has no principal-naming tie).
        governed_decision.append(
            GovernedDecision(
                control_ref=ControlRef(kind="doa_tier", id=doa_verdict["resolved_tier_id"]),
                principal_id=approver_id,
            ).model_dump(mode="json")
        )

    seed_req = seed[0]
    return {
        "po_id": seed_req["primary_key"],
        "part_id": seed_req["part_id"],
        "supplier_id": scored["selected_supplier_id"],  # DERIVED by the scored rule
        "asset_id": seed_req["asset_id"],
        "order_type": seed_req["order_type"],
        "is_off_avl_override": seed_req["is_off_avl_override"],
        "amount": doa_verdict["amount"],  # DERIVED (scored_rule spend the doa_tier resolved)
        "declared_tier_id": seed_req["declared_tier_id"],
        "doa_tier": [doa_verdict],
        "governed_kind": "doa_tier",
        "governed_decision": governed_decision,
        "scored_rule": [scored],  # the sourcing selection provenance (beyond the offline contract)
        "sod": _sod_projection(
            sod_verdict, requester_id=_REQUESTER_ID, approver_id=approver_id, by_id=by_id
        ),
    }


async def build_live_hero_governance_audit(
    adapter: FastenalCsvAdapter | None = None,
    *,
    client_factory: ClientFactory,
) -> dict[str, Any]:
    """The live analogue of :func:`build_hero_governance_audit` -- the SAME contract shape with the
    HERO derived by a live run (``source: "live-run"``) and the CONTRAST reused from the
    deterministic offline builder (its ฿99,000 -> MANAGER verdict is identical live or offline)."""
    adapter = adapter or FastenalCsvAdapter()
    hero = await run_hero_governance_moment(adapter, client_factory=client_factory)
    offline = await build_hero_governance_audit(adapter)
    return {
        "provisional": True,
        "source": _LIVE_SOURCE,
        "hero": hero,
        "contrast": offline["contrast"],
    }


# --------------------------------------------------------------------------- #
# PLAN-0057 — the EVENT-triggered hero opener: the shipped event bridge (ADR-0029 /
# PLAN-0056) made VISIBLE in the hero-demo governance-moment surface. Mirrors
# run_hero_governance_moment, but the parked run is DERIVED by fire_event (not a
# manual in-memory run) — a detected asset-failure event auto-fires the governed
# emergency-sourcing procedure. Demo composition over shipped plumbing (no engine change).
# --------------------------------------------------------------------------- #

_EVENT_KIND = "emergency_source"  # = RecommendedAction.suggested_handler (PLAN-0056 Step 6)
_EVENT_PROC_ID = "event_emergency_sourcing_round"
# PLAN-0084 Step 4b (SD-D (d), Cray-ratified s155): the detected-entity id IS the ontology pk
# (Equipment ``AST-CNC-014``) — superseding PLAN-0057 OQ-1's opaque ``"CNC-Line-07"`` so the
# bridge's engine-stamped ``entity_ids`` become honest ontology references the ``/runs``
# subject projection resolves data-driven (the bridge builder itself is untouched).
_EVENT_ASSET_ID = "AST-CNC-014"
_EVENT_REQUESTER_ID = "req-planner"  # SP-5: the owning human = the SoD requester on `intake`
_EVENT_SOURCE = "event-fired"
# Fixed demo-grade timestamps (deterministic render; the run is event-keyed + idempotent, so a
# re-fire returns the SAME parked run rather than piling up demo runs).
_EVENT_DETECTED = datetime(2026, 7, 8, 9, 41, tzinfo=UTC)
_EVENT_NOW = datetime(2026, 7, 8, 9, 43, tzinfo=UTC)


async def _generation_detected_at(session: AsyncSession) -> datetime:
    """Deterministic replay generation (PLAN-0072 SD-C) — advance the fixed demo event key by
    one minute per ALREADY-DECIDED run of the event procedure, so a resolved/rejected showing
    re-fires a FRESH parked run while a still-parked run keeps returning itself (fire_event
    ALREADY_FIRED). Generation 0 == the base moment (the PLAN-0057 openers stay unchanged).
    Clock-free — a COUNT of decided runs, never a wall-clock read (the WSL clock is
    non-monotonic, project memory project_wsl2_wall_clock_non_monotonic)."""
    decided = await session.scalar(
        sa.select(sa.func.count())
        .select_from(PipelineRun)
        .where(
            PipelineRun.procedure_id == _EVENT_PROC_ID,
            PipelineRun.status != PipelineRunStatus.WAITING_HUMAN.value,
        )
    )
    return _EVENT_DETECTED + timedelta(
        hours=int(decided or 0)
    )  # +1 h/gen crosses the 3600 s dedup bucket


async def run_hero_event_governance_moment(
    session: AsyncSession,
    adapter: FastenalCsvAdapter | None = None,
    *,
    entity_ids: list[str] | None = None,
    detected_at: datetime | None = None,
    now: datetime = _EVENT_NOW,
) -> dict[str, Any]:
    """Fire the EVENT-triggered emergency-sourcing procedure and capture the parked governance
    moment in the SAME hero contract the manual opener draws (PLAN-0057, ADR-0029).

    A detected asset-failure event (``event_kind=emergency_source``, entity ``CNC-Line-07``)
    auto-fires ``event_emergency_sourcing_round`` via ``fire_event`` → a persisted run parks at the
    ``approve`` DOA gate (``waiting_human``). Projects the parked run's ``source`` scored_rule +
    ``approve`` doa_tier (+ the derived SoD tie) into the hero contract dict — the EXACT shape
    :func:`run_hero_governance_moment` returns — and folds the persisted ``trigger_context``
    (event_kind / entity_ids / detected_at / fired_at) in as the beat-1 "sense" cue under
    ``hero.trigger`` (AC-3b; render-only, no contract reshape). Deterministic (advisory stub via the
    shipped factory), MS-S1-free.

    Idempotent + replayable: the run is event-keyed, so a re-fire returns the SAME parked run and it
    NEVER auto-resolves — like the manual opener (which also stops at the parked moment,
    governance_audit.py LOCKED #3), the approve→COMPLETED beat is the demo's front-end reveal. The
    governed resolve capability is proven separately by the integration test.

    Requires the procurement executor factory registered (API startup / test fixture)."""
    adapter = adapter or FastenalCsvAdapter()
    if detected_at is None:  # PLAN-0072 SD-C: generation-aware replay (deterministic, clock-free)
        detected_at = await _generation_detected_at(session)
        now = detected_at + (_EVENT_NOW - _EVENT_DETECTED)
    spec = load_procedures(_VERTICAL)
    resolve = build_event_resolver(spec, registry.get_procedure_executors(_VERTICAL))
    request = resolve(
        event_kind=_EVENT_KIND,
        entity_ids=entity_ids or [_EVENT_ASSET_ID],
        detected_at=detected_at,
    )
    outcome = await fire_event(session, request, now=now)

    loaded = await load_run(session, outcome.run_id)
    if loaded is None or loaded.run.status != PipelineRunStatus.WAITING_HUMAN.value:
        raise ProcedureError(
            f"event hero opener '{outcome.run_id}': the event run did not park at waiting_human "
            f"(outcome '{outcome.result}', status "
            f"'{loaded.run.status if loaded else None}') — the fire path is broken"
        )
    source_sr = next(s for s in loaded.step_results if s.step_id == "source")
    approve_sr = next(s for s in loaded.step_results if s.step_id == "approve")
    source_audit = source_sr.audit or {}
    approve_audit = approve_sr.audit or {}
    if "scored_rule" not in source_audit or "doa_tier" not in approve_audit:
        raise ProcedureError(
            f"event hero opener '{outcome.run_id}': missing scored_rule / doa_tier audit — the "
            "AT-2 executors did not annotate the fired run"
        )
    [scored] = source_audit["scored_rule"]
    [doa_verdict] = approve_audit["doa_tier"]
    approver_id = doa_verdict["resolved_approver_id"]

    principals = list(spec.principals)
    by_id = {p.person_id: p for p in principals}
    proc = next(p for p in spec.procedures if p.procedure_id == _EVENT_PROC_ID)
    step_principals: dict[str, str | None] = {"intake": _EVENT_REQUESTER_ID, "approve": approver_id}
    sod_verdict = check_principal_sod(
        proc,
        principals=principals,
        principal_aliases=list(spec.principal_aliases),
        step_principals=step_principals,
    )

    governed_decision = list(approve_audit.get("governed_decision", []))
    if approver_id is not None and sod_verdict.governed:
        governed_decision.append(
            GovernedDecision(
                control_ref=ControlRef(kind="sod", id=_SOD_CONSTRAINT_ID),
                principal_id=approver_id,
            ).model_dump(mode="json")
        )
        # PLAN-0075 SD-6(a): authority tie names the acting approver (see the live-hero builder).
        governed_decision.append(
            GovernedDecision(
                control_ref=ControlRef(kind="doa_tier", id=doa_verdict["resolved_tier_id"]),
                principal_id=approver_id,
            ).model_dump(mode="json")
        )

    seed_req = await _intake_seed(adapter)
    tc = loaded.run.trigger_context or {}
    return {
        "run_id": outcome.run_id,  # PLAN-0072 Step 3: additive — the run the FE resolves
        "po_id": seed_req["primary_key"],
        "part_id": seed_req["part_id"],
        "supplier_id": scored["selected_supplier_id"],  # DERIVED by the scored rule
        "asset_id": seed_req["asset_id"],
        "order_type": seed_req["order_type"],
        "is_off_avl_override": seed_req["is_off_avl_override"],
        "amount": doa_verdict["amount"],  # DERIVED (scored_rule spend the doa_tier resolved)
        "declared_tier_id": seed_req["declared_tier_id"],
        "doa_tier": [doa_verdict],
        "governed_kind": "doa_tier",
        "governed_decision": governed_decision,
        "scored_rule": [scored],
        "sod": _sod_projection(
            sod_verdict, requester_id=_EVENT_REQUESTER_ID, approver_id=approver_id, by_id=by_id
        ),
        # AC-3b (PLAN-0057) — the beat-1 "sense" cue: the event trigger provenance (render-only).
        "trigger": {
            "event_kind": tc.get("event_kind"),
            "entity_ids": tc.get("entity_ids"),
            "detected_at": tc.get("detected_at"),
            "fired_at": tc.get("fired_at"),
        },
    }


async def build_event_hero_governance_audit(
    session: AsyncSession,
    adapter: FastenalCsvAdapter | None = None,
    *,
    entity_ids: list[str] | None = None,
    detected_at: datetime | None = None,
    now: datetime = _EVENT_NOW,
) -> dict[str, Any]:
    """The EVENT analogue of :func:`build_live_hero_governance_audit` — the SAME HeroGovernanceAudit
    contract with the HERO derived by an event-fired persisted run (``source: "event-fired"``, the
    trigger sense cue folded into ``hero.trigger``) and the CONTRAST reused from the deterministic
    offline builder (PLAN-0057 AC-1/AC-3b/AC-4)."""
    adapter = adapter or FastenalCsvAdapter()
    hero = await run_hero_event_governance_moment(
        session, adapter, entity_ids=entity_ids, detected_at=detected_at, now=now
    )
    offline = await build_hero_governance_audit(adapter)
    return {
        "provisional": True,
        "source": _EVENT_SOURCE,
        "hero": hero,
        "contrast": offline["contrast"],
    }


# --------------------------------------------------------------------------- #
# PLAN-0054 Step 6b — the deterministic procurement procedure-executor factory
# for the Control-leg operate demo (the HTTP resolve/resume path)
# --------------------------------------------------------------------------- #


async def register_procurement_procedure_executors(
    adapter: FastenalCsvAdapter | None = None,
) -> None:
    """Register a DETERMINISTIC ``procurement`` procedure-executor factory (PLAN-0054 Step 6b).

    The Control-leg operate demo resolves a ``waiting_human`` gate over HTTP
    (``POST /runs/{run_id}/gate/resolve``), which resumes the run via
    ``registry.get_procedure_executors("procurement")`` -- a lookup that 409s ("no
    procedure-executor factory") until a factory is registered. ``register_procedure_executors``
    has no live caller: the import-scan discovery deliberately registers adapters + handlers
    only (OQ-6, no executor-factory discovery). This is that explicit, active-vertical-scoped
    registration (wired at startup in ``services/api/main.py`` when ``OCT_VERTICAL=procurement``).

    The registered factory REUSES the hero harness's per-kind :func:`_executors` bound to the
    deterministic :func:`advisory_stub_factory` -- NOT the real ``OllamaClient``-backed
    ``ActionStepExecutor`` -- so resolve->resume (the ``source`` auto step + the post-``approve``
    ``issue_po`` ACTION) fires NO live MS-S1 call (host-state, CLAUDE.md #8). The SAME executors
    seed the ``waiting_human`` run and resolve it -- one consistent factory for ``procurement``.

    Idempotent: a no-op when a ``procurement`` factory is already registered.
    """
    try:
        registry.get_procedure_executors(_VERTICAL)
        return  # already registered -- idempotent
    except RegistryError:
        pass

    adapter = adapter or FastenalCsvAdapter()
    # Roster reconciliation (PLAN-0055 Step 8): the S1 scheduler fires the schedule procedure
    # THROUGH this factory, and its doa_tier executor resolves the tier's approver_role against
    # `principals` at fire time. Use the SPEC's authored principals (Thai DOA roles: req-planner /
    # appr-pm / …) — NOT the Fastenal person.csv roster (English roles) — so the ฿288k tier resolves
    # to `appr-pm` (ผจก.จัดซื้อ), matching the human who resolves the gate AND
    # seed_operate_waiting_human_run's own roster. The Fastenal CSV still supplies the requisition
    # DATA via `_intake_seed`; only the SoD/DOA principal roster is the spec's. Harmless to the HTTP
    # resolve/resume path (its resume runs no doa_tier step; the SoD check there already uses
    # spec.principals).
    principals = list(load_procedures(_VERTICAL).principals)
    # JSONB-safe seed (PLAN-0055 Step 8). The HTTP resolve/resume path never re-runs `intake`
    # (it resumes a run already seeded past it), so a raw Decimal `unit_price` here was latent.
    # But the S1 scheduler daemon fires a FRESH run through this factory: `intake` executes live,
    # `run_procedure_persisted` persists its output, and a raw Decimal fails the JSONB column
    # (project memory project_procurement_synthetic_events_datetime_jsonb). Sanitising Decimal ->
    # str is loss-free — the scored_rule re-parses via Decimal(str(...)) (scored_rule.py) — and
    # mirrors seed_operate_waiting_human_run's own sanitisation.
    seed = json.loads(json.dumps([await _intake_seed(adapter)], default=str))

    # PLAN-0064 (SD-5): declared reads are served by the REGISTRY-registered adapter
    # (`ProcurementSyntheticAdapter` -- the only adapter carrying Part.stock_qty /
    # reorder_point), NEVER the hero FastenalCsvAdapter above (its part.csv lacks the
    # columns; binding it would re-create ERRATUM 2's declaration theater through the
    # adapter choice). The seed keeps its Fastenal requisition untouched. A missing
    # registered adapter raises loudly (the energy-factory precedent): the API lifespan
    # and every registering caller run `discover_and_register()` first.
    registered_adapter = registry.get_adapter(_VERTICAL)
    meta = load_ontology_meta(_VERTICAL)
    object_type_names = frozenset(object_type.name for object_type in meta.object_types)

    def factory() -> dict[StepKind, StepExecutor]:
        # Built fresh per run/resume request (stateful executors never leak across
        # requests -- the registry Step-2 contract); the principals + seed are
        # immutable read-only data captured once at registration.
        return _executors(
            advisory_stub_factory,
            principals,
            seed,
            declared_query=QueryStepExecutor(
                adapter=registered_adapter, object_type_names=object_type_names, meta=meta
            ),
            # PLAN-0085 SD-2(b): the _executors default supplies the deterministic-arm
            # GateAdvisoryBuilder (grounded reasons, no network, no MS-S1); the live
            # arm stays opt-in behind the seam and is NEVER wired here.
        )

    registry.register_procedure_executors(_VERTICAL, factory)


async def seed_operate_waiting_human_run(
    session: AsyncSession,
    *,
    run_id: str = "run-operate-demo",
    adapter: FastenalCsvAdapter | None = None,
    asset_id: str | None = None,
) -> RunResult:
    """Seed a PERSISTED procurement ``waiting_human`` run for the Control-leg operate demo
    (PLAN-0054 Step 6c) -- the gate the Monitor (View H) shows + a distinct approver resolves.

    Runs the SHIPPED YAML ``emergency_sourcing_round`` to its ``approve`` gate through the
    deterministic hero ``_executors`` (scored_rule -> doa_tier, the ``advisory_stub_factory`` LLM
    seam -- NO MS-S1), persisted via ``run_procedure_persisted`` with the REQUESTER
    (``req-planner``) as the intake principal. The ``approve`` gate suspends at ``waiting_human``;
    the requester half of the SoD map (``{intake: req-planner}``) is recorded on the run, so a
    DISTINCT ``approver`` (e.g. ``appr-pm``, matching the ฿288,000 DOA tier) keeps SoD GOVERNED
    at resolve. Returns the persisted ``RunResult`` (reachable by ``GET /runs/{run_id}``).

    Two deliberate choices for the resolve endpoint's benefit:

    * the YAML ``emergency_sourcing_round`` (NOT the re-id'd Fastenal hero procedure) is seeded,
      so the resolve endpoint -- which looks the procedure up in the vertical's spec -- can find it;
    * the roster is the SPEC's authored ``principals`` (``req-planner`` / ``appr-*``), NOT the
      Fastenal ``person.csv`` roster, so the run-check + doa_tier resolve against the SAME set the
      resolve endpoint's SoD check uses.

    JSONB-safe: the Fastenal requisition carries ``Decimal`` ``unit_price`` (kept exact for the
    scored_rule); persisting it raw fails JSONB (project memory
    ``project_procurement_synthetic_events_datetime_jsonb``). Sanitising ``Decimal`` -> ``str``
    is loss-free here -- the scored_rule re-parses via ``Decimal(str(...))`` (``scored_rule.py``).
    """
    adapter = adapter or FastenalCsvAdapter()
    _ensure_handlers()
    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == "emergency_sourcing_round")
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    principals = list(spec.principals)
    requester = next(p for p in principals if "requester" in p.roles)
    # PLAN-0084 Step 5 rotation: an explicit asset resolves to ITS PurchaseOrder row
    # (data-driven from the adapter -- rotatable = exactly one PO; never a hardcoded list).
    po_id = _HERO_PO
    if asset_id is not None:
        pos = await adapter.fetch_objects("PurchaseOrder")
        matches = [p["po_id"] for p in pos if p["equipment_id"] == asset_id]
        if len(matches) != 1:
            rotatable = sorted({p["equipment_id"] for p in pos})
            raise ValueError(
                f"asset {asset_id!r} matches {len(matches)} PurchaseOrder rows -- "
                f"rotatable assets (exactly one PO each): {rotatable}"
            )
        po_id = matches[0]
    seed_dict = await _intake_seed(adapter, po_id=po_id)
    seed = json.loads(json.dumps([seed_dict], default=str))
    return await run_procedure_persisted(
        session,
        proc,
        agent,
        _executors(advisory_stub_factory, principals, seed),
        vertical=_VERTICAL,
        run_id=run_id,
        trigger_context={
            "source": "operate-demo-seed",
            "triggered_by": requester.person_id,
            # PLAN-0084 Step 1: the map<->monitor linkage subject -- the ontology ref of
            # the asset this run concerns, from the COMPUTED intake seed (never a literal
            # id). Additive; every pre-existing key above is untouched (AC-3).
            "subject": {"object_type": "Equipment", "primary_key": seed_dict["asset_id"]},
        },
        principal=requester,
    )
