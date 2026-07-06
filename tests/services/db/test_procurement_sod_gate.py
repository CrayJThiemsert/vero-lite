"""PLAN-0044 A1b Step 1 — the LIVE fail-closed principal-SoD run-check, DB-backed.

The run-side complement to the pure ``check_principal_sod`` tests
(``tests/services/engine/procedures/test_principal_sod.py``): this drives a real
suspended-gate resolution through :func:`resolve_gated_step` and proves the wiring
ADR-0026 D4 adds — the orchestrator records the REQUESTER principal on the run
(``PipelineRun.step_principals``, the typed seam — never ``trigger_context``), the
gate assembles the full ``step_principals`` (requester + the explicit APPROVER arg),
and the check fires **unconditionally** + **fails CLOSED** (raises
:class:`PrincipalSoDError` BEFORE any approve/execute — no handler fires, no governed
verdict) on every violation kind. DB-backed (skips without Postgres), LLM stubbed.

Two surfaces:

* an **inline** minimal SoD procedure (``req`` query -> ``appr`` gated action) isolates
  the wiring across all violation kinds (happy / unresolved / role-mismatch / collapse
  by PK / collapse by alias) + the non-skippability guard;
* the **real** ``verticals/procurement`` hero procedure proves the authored principals
  resolve a genuinely-distinct pair on the happy path (the demo "live run hitting the
  SoD gate"), and that the requester cannot self-approve (fails closed live).
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.db.base import Base
from services.engine.llm.client import ChatResult
from services.engine.procedures.action_step import (
    ActionStepExecutor,
    GateApproverError,
    PrincipalSoDError,
    resolve_gated_step,
)
from services.engine.procedures.evaluate_step import EvaluateStepExecutor
from services.engine.procedures.orchestrator import (
    ProcedureError,
    RunContext,
    StepExecutor,
    StepOutcome,
    run_procedure,
)
from services.engine.procedures.persistence import persist_run
from services.engine.procedures.principal_sod import SoDViolationKind
from services.engine.procedures.runs import PipelineRunStatus, StepResultStatus
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    Person,
    PrincipalAlias,
    Procedure,
    SoDConstraint,
    Step,
    StepKind,
    load_procedures,
)
from services.engine.registry import registry
from tests.db_support import create_test_engine
from verticals.procurement.data_adapter import synthetic

# --------------------------------------------------------------------------- #
# Offline LLM-free fakes (mirrors test_procedure_action_gate / _headline)
# --------------------------------------------------------------------------- #


class _CyclingChat:
    """Mock ChatClient sized to any entity count: a draft on call-1 (no
    ``response_format``), a canned judgment on call-2 (with ``response_format``)."""

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        if response_format is not None:
            return ChatResult(content=_judgment_json(), thinking=None, model="gpt-oss:20b", raw={})
        return ChatResult(content="draft", thinking="t", model="gpt-oss:20b", raw={})


def _judgment_json() -> str:
    return json.dumps(
        {
            "title": "Proposed action",
            "description": "A governed proposal awaiting the human gate.",
            "rationale": "Deterministic verdict routed this here.",
            "confidence": 0.9,
            "affected_entities": [{"object_type": "PurchaseOrder", "primary_key": "po"}],
            "suggested_handler": "echo",
            "handler_payload": {},
        }
    )


class _SpyHandler:
    """Records every action it executes — proves whether the gate fired."""

    def __init__(self) -> None:
        self.calls: list[Any] = []

    async def __call__(self, action: Any) -> dict[str, Any]:
        self.calls.append(action)
        return {"ok": True, "executed": action.id}


class _Query:
    """Fixed-output query executor (the canned requester-step seed)."""

    def __init__(self, output: list[Any]) -> None:
        self.output = output

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(output=self.output, reasoning_trace=[{"kind": "query", "summary": "r"}])


class _Evaluate:
    """Dispatch: a banded evaluate (``judge``) uses the REAL deterministic executor;
    the band-less ``compliance`` evaluate tags each entity ``compliant`` (harness seam)."""

    def __init__(self) -> None:
        self._band = EvaluateStepExecutor()

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        if step.threshold is not None:
            return await self._band.execute(step, input_set, ctx)
        return StepOutcome(
            output=[{**e, "compliant": True} for e in input_set],
            reasoning_trace=[{"kind": "rule", "summary": "compliance (harness)"}],
        )


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


# --------------------------------------------------------------------------- #
# Inline minimal SoD procedure — isolates the wiring across all violation kinds
# --------------------------------------------------------------------------- #

_VERTICAL = "sodtest"
_SEED: list[Any] = [{"event_id": "e1", "object_type": "PurchaseOrder", "primary_key": "po1"}]


def _sod_procedure() -> Procedure:
    """req (query, the REQUESTER step) -> appr (gated action, the APPROVER gate),
    bound by an SoD constraint mapping each step to the role its Person must hold."""
    return Procedure(
        procedure_id="sod-round",
        title="SoD Round",
        run_by="sod_agent",
        steps=[
            Step(step_id="req", name="Request", kind=StepKind.QUERY),
            Step(step_id="appr", name="Approve", kind=StepKind.ACTION, handler="echo"),
        ],
        separation_of_duties=[
            SoDConstraint(
                distinct_steps=frozenset({"req", "appr"}),
                required_roles={"req": "requester", "appr": "approver"},
            )
        ],
    )


def _sod_agent() -> Agent:
    return Agent(
        agent_id="sod_agent",
        name="SoD Agent",
        autonomy_ceiling=Autonomy.AUTO,
        allowed=AgentAllowed(action_handlers=["echo"]),
    )


def _inline_executors() -> dict[StepKind, StepExecutor]:
    return {
        StepKind.QUERY: _Query(_SEED),
        StepKind.ACTION: ActionStepExecutor(client_factory=lambda _m: _CyclingChat()),
    }


async def _run_to_gate(maker: Any, run_id: str, requester: Person | None) -> _SpyHandler:
    """Run the inline SoD procedure to the suspended ``appr`` gate + persist; returns
    the handler spy (calls stay empty until/unless the gate is governed + approved)."""
    spy = _SpyHandler()
    registry.register_handler(_VERTICAL, "echo", spy)
    result = await run_procedure(
        _sod_procedure(),
        _sod_agent(),
        _inline_executors(),
        vertical=_VERTICAL,
        run_id=run_id,
        principal=requester,
    )
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    # The requester half is recorded on the run via the TYPED seam, never trigger_context.
    assert result.run.step_principals == {"req": requester.person_id if requester else None}
    assert result.run.trigger_context is None
    async with maker() as session:
        await persist_run(session, result)
    return spy


async def test_happy_two_distinct_principals_proceeds(db_engine: AsyncEngine) -> None:
    """AC-4 — requester + approver resolve to two DISTINCT Persons -> the gate passes the
    live SoD check and proceeds (the handler fires on approve)."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    alice = Person(person_id="alice", name="Alice", roles=frozenset({"requester"}))
    bob = Person(person_id="bob", name="Bob", roles=frozenset({"approver"}))
    spy = await _run_to_gate(maker, "sod-ok", alice)
    async with maker() as session:
        resolved = await resolve_gated_step(
            session,
            "sod-ok",
            "appr",
            {"action-e1": "approve"},
            principal=bob,
            procedure=_sod_procedure(),
            principals=[alice, bob],
        )
    assert len(spy.calls) == 1, "a governed gate executes the approved handler"
    assert resolved.artifact["output_set"][0]["status"] == "executed"
    # AC-8 (A1b Step 6): the governed SoD gate emits the typed audit-to-control tie on the
    # resolved step — control_ref {kind:'sod', id: the sorted distinct_steps} + the approver PK.
    assert resolved.audit is not None
    assert resolved.audit["governed_decision"] == [
        {"control_ref": {"kind": "sod", "id": "appr+req"}, "principal_id": "bob"}
    ]


async def test_missing_approver_fails_closed(db_engine: AsyncEngine) -> None:
    """AC-3 — principal=None on a SoD-constrained gate -> UNRESOLVED_PRINCIPAL -> blocked
    (the check is NOT skipped when the approver is absent; the handler never fires)."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    alice = Person(person_id="alice", name="Alice", roles=frozenset({"requester"}))
    bob = Person(person_id="bob", name="Bob", roles=frozenset({"approver"}))
    spy = await _run_to_gate(maker, "sod-noappr", alice)
    # ADR-016 S2 RF-1 / PLAN-0053 AC-1: a None approver is caught by the broad library
    # guard before the SoD verdict machinery.
    async with maker() as session:
        with pytest.raises(GateApproverError):
            await resolve_gated_step(
                session,
                "sod-noappr",
                "appr",
                {"action-e1": "approve"},
                principal=None,
                procedure=_sod_procedure(),
                principals=[alice, bob],
            )
    assert spy.calls == [], "a blocked gate must not execute the handler"


async def test_role_mismatch_fails_closed(db_engine: AsyncEngine) -> None:
    """AC-3 — the approver does not hold the required approver role -> ROLE_MISMATCH ->
    blocked (the requester cannot self-approve when they lack approver authority)."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    alice = Person(person_id="alice", name="Alice", roles=frozenset({"requester"}))
    spy = await _run_to_gate(maker, "sod-mismatch", alice)
    async with maker() as session:
        with pytest.raises(PrincipalSoDError) as exc:
            await resolve_gated_step(
                session,
                "sod-mismatch",
                "appr",
                {"action-e1": "approve"},
                principal=alice,  # holds requester, NOT approver
                procedure=_sod_procedure(),
                principals=[alice],
            )
    kinds = {v.kind for v in exc.value.verdict.violations}
    assert SoDViolationKind.ROLE_MISMATCH in kinds
    assert spy.calls == []


async def test_collapse_by_pk_fails_closed(db_engine: AsyncEngine) -> None:
    """AC-2 — the two constrained steps resolve to ONE human (a person_id PK match) ->
    PRINCIPAL_COLLAPSE -> blocked. The dual-role Person resolves BOTH steps, then collapses."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    dup = Person(person_id="dup", name="Dup", roles=frozenset({"requester", "approver"}))
    spy = await _run_to_gate(maker, "sod-pk", dup)
    async with maker() as session:
        with pytest.raises(PrincipalSoDError) as exc:
            await resolve_gated_step(
                session,
                "sod-pk",
                "appr",
                {"action-e1": "approve"},
                principal=dup,
                procedure=_sod_procedure(),
                principals=[dup],
            )
    kinds = {v.kind for v in exc.value.verdict.violations}
    assert SoDViolationKind.PRINCIPAL_COLLAPSE in kinds
    assert spy.calls == []


async def test_collapse_by_alias_fails_closed(db_engine: AsyncEngine) -> None:
    """AC-2 — two DISTINCT person_ids that share a declared PrincipalAlias link are ONE
    human -> PRINCIPAL_COLLAPSE -> blocked (both resolve their roles, then collapse)."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    a = Person(person_id="a-sso", name="A (SSO id)", roles=frozenset({"requester"}))
    b = Person(person_id="a-erp", name="A (ERP id)", roles=frozenset({"approver"}))
    alias = PrincipalAlias(alias_id="same-human", members=frozenset({"a-sso", "a-erp"}))
    spy = await _run_to_gate(maker, "sod-alias", a)
    async with maker() as session:
        with pytest.raises(PrincipalSoDError) as exc:
            await resolve_gated_step(
                session,
                "sod-alias",
                "appr",
                {"action-e1": "approve"},
                principal=b,
                procedure=_sod_procedure(),
                principals=[a, b],
                principal_aliases=[alias],
            )
    kinds = {v.kind for v in exc.value.verdict.violations}
    assert SoDViolationKind.PRINCIPAL_COLLAPSE in kinds
    assert spy.calls == []


async def test_sod_check_is_not_skippable(db_engine: AsyncEngine) -> None:
    """AC-2 — on a run that recorded step_principals (a SoD run), omitting the
    procedure/principals context RAISES rather than silently bypassing the check."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    alice = Person(person_id="alice", name="Alice", roles=frozenset({"requester"}))
    spy = await _run_to_gate(maker, "sod-skip", alice)
    async with maker() as session:
        with pytest.raises(ProcedureError, match="cannot be skipped"):
            await resolve_gated_step(
                session, "sod-skip", "appr", {"action-e1": "approve"}, principal=alice
            )
    assert spy.calls == [], "the gate must not execute when the SoD context is withheld"


# --------------------------------------------------------------------------- #
# The REAL procurement hero procedure — a live run hitting the SoD gate
# --------------------------------------------------------------------------- #


def _procurement() -> tuple[Procedure, Agent, list[Person], list[PrincipalAlias]]:
    spec = load_procedures("procurement")
    proc = next(p for p in spec.procedures if p.procedure_id == "emergency_sourcing_round")
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    return proc, agent, spec.principals, spec.principal_aliases


def _failure_events() -> list[Any]:
    # JSON-sanitise (datetimes -> ISO strings) so the persisted intake artifact is
    # JSONB-safe — mirrors the real enriched-PR records intake would emit + persist
    # (the synthetic events carry a raw datetime the in-memory test never persisted).
    raw = [e for e in synthetic.operational_events() if e["event_type"] == "failure"]
    return list(json.loads(json.dumps(raw, default=str)))


def _procurement_executors() -> dict[StepKind, StepExecutor]:
    return {
        StepKind.QUERY: _Query(_failure_events()),
        StepKind.EVALUATE: _Evaluate(),
        StepKind.ACTION: ActionStepExecutor(client_factory=lambda _m: _CyclingChat()),
    }


async def _run_procurement_to_approve(maker: Any, run_id: str, requester: Person) -> list[str]:
    """Drive the real hero procedure to the suspended ``approve`` gate; persist; return
    the proposed action_ids (the requester recorded on the run via the typed seam)."""
    spy = _SpyHandler()
    for handler in ("emergency_source", "request_approval", "issue_po", "echo"):
        registry.register_handler("procurement", handler, spy)
    proc, agent, _principals, _aliases = _procurement()
    result = await run_procedure(
        proc,
        agent,
        _procurement_executors(),
        vertical="procurement",
        run_id=run_id,
        principal=requester,
    )
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    approve_sr = next(sr for sr in result.step_results if sr.step_id == "approve")
    assert approve_sr.status == StepResultStatus.WAITING_HUMAN.value
    # The requester (intake) was recorded on the run from the typed ambient principal.
    assert result.run.step_principals == {"intake": requester.person_id}
    async with maker() as session:
        await persist_run(session, result)
    return [p["action_id"] for p in (approve_sr.artifact or {}).get("output_set", [])]


async def test_procurement_distinct_principals_proceeds(db_engine: AsyncEngine) -> None:
    """AC-4 / AC-10 — the REAL hero procedure with its AUTHORED principals: requester
    (req-planner) + a distinct approver (appr-director) pass the live SoD gate."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    proc, _agent, principals, aliases = _procurement()
    by_id = {p.person_id: p for p in principals}
    requester, approver = by_id["req-planner"], by_id["appr-director"]
    action_ids = await _run_procurement_to_approve(maker, "proc-ok", requester)
    async with maker() as session:
        resolved = await resolve_gated_step(
            session,
            "proc-ok",
            "approve",
            {aid: "approve" for aid in action_ids},
            principal=approver,
            procedure=proc,
            principals=principals,
            principal_aliases=aliases,
        )
    assert all(e["status"] == "executed" for e in resolved.artifact["output_set"])
    # AC-8 (A1b Step 6) — the REAL hero gate emits the audit-to-control tie: the procurement SoD
    # constraint is [intake, approve] (sorted id 'approve+intake'), the approver appr-director.
    assert resolved.audit is not None
    assert resolved.audit["governed_decision"] == [
        {"control_ref": {"kind": "sod", "id": "approve+intake"}, "principal_id": "appr-director"}
    ]


async def test_procurement_requester_cannot_self_approve(db_engine: AsyncEngine) -> None:
    """AC-3 (live) — the requester (req-planner, holds only `requester`) tries to approve
    their own PO -> ROLE_MISMATCH on the approver step -> blocked, no PO governed."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    proc, _agent, principals, aliases = _procurement()
    by_id = {p.person_id: p for p in principals}
    requester = by_id["req-planner"]
    action_ids = await _run_procurement_to_approve(maker, "proc-self", requester)
    async with maker() as session:
        with pytest.raises(PrincipalSoDError) as exc:
            await resolve_gated_step(
                session,
                "proc-self",
                "approve",
                {aid: "approve" for aid in action_ids},
                principal=requester,  # the requester cannot self-approve
                procedure=proc,
                principals=principals,
                principal_aliases=aliases,
            )
    kinds = {v.kind for v in exc.value.verdict.violations}
    assert SoDViolationKind.ROLE_MISMATCH in kinds
