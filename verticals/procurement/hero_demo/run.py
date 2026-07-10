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
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from services.engine.actions import ControlRef, GovernedDecision
from services.engine.llm.client import ChatResult
from services.engine.llm.structured import ChatClient
from services.engine.procedures.action_step import ActionStepExecutor, ClientFactory
from services.engine.procedures.evaluate_step import EvaluateStepExecutor
from services.engine.procedures.event_bridge import build_event_resolver, fire_event
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
from services.engine.procedures.runs import PipelineRunStatus, StepResultStatus
from services.engine.procedures.spec import Person, Step, StepKind, load_procedures
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
    FLAT rows and cannot produce the seed's DERIVED fields -- ``compliance`` (the
    rule_gate signal), the ``criticality`` amplification, the nested
    ``candidate_quotes`` reshape -- without inventing a transform StepKind (out of
    scope). So ``intake`` is declared-expressible for the join half (proven) while its
    production execution stays here, and it is labelled **execution-bound (no)** for the
    derived fields (LOCKED-9 -- no over-claim).

    NEW plain single-type declared reads go through the engine default:
    ``services/engine/procedures/query_step.py`` (declared==dispatched). The three OCT
    verticals' read steps migrated there in PLAN-0062 PR1-PR3."""

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
            "unit_price": q["price_thb"],
            "currency": q.get("currency", _CURRENCY),
            "lead_time_days": q["lead_time_days"],
            "on_contract": q["on_contract"],
        }
        for q in quotes
    ]


async def _intake_seed(adapter: FastenalCsvAdapter) -> dict[str, Any]:
    """Assemble the enriched purchase-requisition the run scores (data-access = (a), Cray-confirmed
    s91): the failure event supplies the criticality reading; the hero PO row supplies the
    requisition metadata (part / asset / qty -- the GOVERNED supplier + amount + tier are
    RE-DERIVED by the run, never read from the PO); the quotes are normalised to the rule shape."""
    events = await adapter.fetch_objects("OperationalEvent")
    failure = next(e for e in events if e["event_type"] == "failure")
    pos = {p["po_id"]: p for p in await adapter.fetch_objects("PurchaseOrder")}
    req = pos[_HERO_PO]
    quotes = [q for q in await adapter.fetch_objects("Quotation") if q["part_id"] == req["part_id"]]
    return {
        "event_id": failure["event_id"],
        "object_type": "PurchaseOrder",
        "primary_key": req["po_id"],
        "asset_id": req["asset_id"],
        "part_id": req["part_id"],
        # the reading the judge bands (>= 0.8 -> breach -> the emergency-sourcing path)
        "measured_value": failure["measured_value"],
        "unit": failure.get("unit", "criticality"),
        # the event criticality that amplifies the scored_rule criticality criterion
        "criticality": failure["measured_value"],
        "qty": req["qty"],  # the hero-knob qty (3) -> 96,000 x 3 = 288,000
        "candidate_quotes": _normalize_quotes(quotes),
        # the per-criterion compliance signal the shipped rule_gate enforces (data-access = (a),
        # mirroring candidate_quotes -- rule_gate.COMPLIANCE_FIELD = "compliance"). The hero passes
        # every criterion, so the gate does not block the PO. NARRATIVE: RapidMRO is OFF_AVL and is
        # selected via the logged RFQ->AVL exception (the scored_rule's source_path:
        # exception_policy). The `avl` spec explicitly allows "a logged emergency AVL exception", so
        # the `avl` signal is True VIA that documented exception -- NOT because RapidMRO is on-AVL
        # (the exception is the reason it passes; coherent with the off-AVL story).
        "compliance": {
            "avl": True,  # True via the logged RFQ->AVL emergency exception (off-AVL)
            "tax": True,
            "cert": True,
            "sanctions": True,
            "single_source": True,
        },
        # requisition metadata for the audit contract (the governed fields are re-derived)
        "order_type": req["order_type"],
        "is_off_avl_override": req["is_off_avl_override"],
        "declared_tier_id": req["required_tier_id"],
    }


def _executors(
    client_factory: ClientFactory, principals: list[Person], seed: list[Any]
) -> dict[StepKind, StepExecutor]:
    """The per-kind executors for the live run: QUERY seeds the requisition; EVALUATE is the AT-2
    governance wrapper (``rule_gate`` at ``compliance``, falling through to the shipped
    :class:`EvaluateStepExecutor` for the banded ``judge``); ACTION is the AT-2 governance wrapper
    (scored_rule at ``source``, doa_tier at ``approve``) over the shipped
    :class:`ActionStepExecutor` base. The band-less ``compliance`` step now runs the SHIPPED
    ``rule_gate`` gate end-to-end (no stub) -- :class:`GovernanceEvaluateExecutor` dispatches its
    ``ComplianceGate`` content to the deterministic
    :func:`~services.engine.procedures.rule_gate.evaluate_compliance`."""
    action = GovernanceActionExecutor(
        base=ActionStepExecutor(client_factory=client_factory),
        principals=principals,
        sod_steps=frozenset({"intake", "approve"}),
    )
    return {
        StepKind.QUERY: _SeedQuery(seed),
        StepKind.EVALUATE: GovernanceEvaluateExecutor(base=EvaluateStepExecutor()),
        StepKind.ACTION: action,
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
        # The SoD audit-to-control tie is emitted at gate RESOLUTION (resolve_gated_step); the run
        # only suspends here, so derive it from the pure run-check (mirrors the offline builder).
        governed_decision.append(
            GovernedDecision(
                control_ref=ControlRef(kind="sod", id=_SOD_CONSTRAINT_ID),
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
_EVENT_ASSET_ID = "CNC-Line-07"  # OQ-1 (PLAN-0057): the detected asset (spindle-bearing seizure)
_EVENT_REQUESTER_ID = "req-planner"  # SP-5: the owning human = the SoD requester on `intake`
_EVENT_SOURCE = "event-fired"
# Fixed demo-grade timestamps (deterministic render; the run is event-keyed + idempotent, so a
# re-fire returns the SAME parked run rather than piling up demo runs).
_EVENT_DETECTED = datetime(2026, 7, 8, 9, 41, tzinfo=UTC)
_EVENT_NOW = datetime(2026, 7, 8, 9, 43, tzinfo=UTC)


async def run_hero_event_governance_moment(
    session: AsyncSession,
    adapter: FastenalCsvAdapter | None = None,
    *,
    entity_ids: list[str] | None = None,
    detected_at: datetime = _EVENT_DETECTED,
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

    seed_req = await _intake_seed(adapter)
    tc = loaded.run.trigger_context or {}
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
    detected_at: datetime = _EVENT_DETECTED,
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

    def factory() -> dict[StepKind, StepExecutor]:
        # Built fresh per run/resume request (stateful executors never leak across
        # requests -- the registry Step-2 contract); the principals + seed are
        # immutable read-only data captured once at registration.
        return _executors(advisory_stub_factory, principals, seed)

    registry.register_procedure_executors(_VERTICAL, factory)


async def seed_operate_waiting_human_run(
    session: AsyncSession,
    *,
    run_id: str = "run-operate-demo",
    adapter: FastenalCsvAdapter | None = None,
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
    seed = json.loads(json.dumps([await _intake_seed(adapter)], default=str))
    return await run_procedure_persisted(
        session,
        proc,
        agent,
        _executors(advisory_stub_factory, principals, seed),
        vertical=_VERTICAL,
        run_id=run_id,
        trigger_context={"source": "operate-demo-seed", "triggered_by": requester.person_id},
        principal=requester,
    )
