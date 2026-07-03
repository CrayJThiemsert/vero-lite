"""PLAN-0047 Step 3 tests (AC-4 + AC-5) — the gate state machine, DB-backed.

Proves, against a real Postgres round-trip (skips without one):

* AC-4 — resolving the same gate twice executes the handler EXACTLY once;
  the second resolve dies on the ``waiting_human`` precondition (the step is
  ``resolved`` — idempotent BY STATE, not by caller discipline);
* AC-5 — a gate suspended with REAL (decidable) proposals is REFUSED by a
  bare ``resume_run`` (fail-closed — artifact presence no longer advances a
  gate); a properly resolved gate passes; a no-decision suspend (empty
  proposal set) keeps the documented plain-resume contract; and on a
  SoD-carrying run the resume re-asserts the ``governed_decision`` audit tie
  (a tampered/absent tie refuses);
* the ``pipeline_runs.version`` optimistic lock makes a concurrent stale
  writer lose cleanly (``StaleDataError``).
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from sqlalchemy.orm.exc import StaleDataError

from services.db.base import Base
from services.engine.llm.client import ChatResult
from services.engine.procedures.action_step import ActionStepExecutor, resolve_gated_step
from services.engine.procedures.orchestrator import (
    ProcedureError,
    RunContext,
    StepExecutor,
    StepOutcome,
    run_procedure,
)
from services.engine.procedures.persistence import persist_run, resume_run
from services.engine.procedures.runs import (
    PipelineRun,
    PipelineRunStatus,
    StepResult,
    StepResultStatus,
)
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    Person,
    Procedure,
    SoDConstraint,
    Step,
    StepKind,
)
from services.engine.registry import registry
from tests.db_support import create_test_engine


class _FakeChat:
    """Replays canned ChatResults (call-1 draft + call-2 judgment per entity)."""

    def __init__(self, results: list[ChatResult]) -> None:
        self._results = list(results)

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        return self._results.pop(0)


class _SpyHandler:
    def __init__(self) -> None:
        self.calls: list[Any] = []

    async def __call__(self, action: Any) -> dict[str, Any]:
        self.calls.append(action)
        return {"ok": True, "executed": action.id}


class _Query:
    """Fixed-output query executor."""

    def __init__(self, output: list[Any]) -> None:
        self.output = output

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(
            output=self.output, reasoning_trace=[{"kind": "query", "summary": "read"}]
        )


def _judgment_json() -> str:
    return json.dumps(
        {
            "title": "Start emergency aerator on pond p7",
            "description": "DO fell below the 4 mg/L breach threshold.",
            "rationale": "DO 3.2 mg/L is a breach; aerate.",
            "confidence": 0.92,
            "affected_entities": [{"object_type": "Pond", "primary_key": "p7"}],
            "suggested_handler": "aerate",
            "handler_payload": {"pond_id": "p7"},
        }
    )


def _chat_results(n: int) -> list[ChatResult]:
    out: list[ChatResult] = []
    for _ in range(n):
        out.append(ChatResult(content="draft", thinking="t", model="gpt-oss:20b", raw={}))
        out.append(ChatResult(content=_judgment_json(), thinking=None, model="gpt-oss:20b", raw={}))
    return out


def _agent() -> Agent:
    return Agent(
        agent_id="pond_agent",
        name="Pond Agent",
        autonomy_ceiling=Autonomy.GATED,
        allowed=AgentAllowed(action_handlers=["aerate"]),
    )


def _procedure(procedure_id: str) -> Procedure:
    return Procedure(
        procedure_id=procedure_id,
        title="Round",
        goal="Act on DO breaches.",
        run_by="pond_agent",
        steps=[
            Step(step_id="read", name="Read", kind=StepKind.QUERY),
            Step(step_id="aerate", name="Aerate", kind=StepKind.ACTION, handler="aerate"),
        ],
    )


def _sod_procedure(procedure_id: str) -> Procedure:
    return Procedure(
        procedure_id=procedure_id,
        title="Governed Round",
        goal="Act on DO breaches under SoD.",
        run_by="pond_agent",
        steps=[
            Step(step_id="read", name="Read", kind=StepKind.QUERY),
            Step(step_id="aerate", name="Aerate", kind=StepKind.ACTION, handler="aerate"),
        ],
        separation_of_duties=[
            SoDConstraint(
                distinct_steps=frozenset({"read", "aerate"}),
                required_roles={"read": "requester", "aerate": "approver"},
            )
        ],
    )


_REQUESTER = Person(person_id="p-req", name="Requester", roles=frozenset({"requester"}))
_APPROVER = Person(person_id="p-app", name="Approver", roles=frozenset({"approver"}))


def _executors(chat_entities: int, breach: list[Any]) -> dict[StepKind, StepExecutor]:
    return {
        StepKind.QUERY: _Query(breach),
        StepKind.ACTION: ActionStepExecutor(
            client_factory=lambda _m: _FakeChat(_chat_results(chat_entities))
        ),
    }


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


async def _run_and_persist(
    db_engine: AsyncEngine,
    procedure: Procedure,
    run_id: str,
    *,
    principal: Person | None = None,
) -> str:
    """Run to the gated suspend and persist; returns the proposal's action_id."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    result = await run_procedure(
        procedure,
        _agent(),
        _executors(1, [{"pond": "p7", "event_id": "e7"}]),
        vertical="aquaculture",
        run_id=run_id,
        principal=principal,
    )
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    async with maker() as session:
        await persist_run(session, result)
    proposals = (result.step_results[-1].artifact or {})["output_set"]
    return str(proposals[0]["action_id"])


async def test_double_resolve_executes_handler_exactly_once(db_engine: AsyncEngine) -> None:
    """AC-4: the second resolve dies on the state machine; the handler never refires."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    spy = _SpyHandler()
    registry.register_handler("aquaculture", "aerate", spy)
    action_id = await _run_and_persist(db_engine, _procedure("sm-round"), "sm-1")

    async with maker() as session:
        resolved = await resolve_gated_step(session, "sm-1", "aerate", {action_id: "approve"})
    assert resolved.status == StepResultStatus.RESOLVED.value
    assert len(spy.calls) == 1

    async with maker() as session:
        with pytest.raises(ProcedureError, match="not awaiting a human decision"):
            await resolve_gated_step(session, "sm-1", "aerate", {action_id: "approve"})
    assert len(spy.calls) == 1, "the handler must never refire on a replayed resolve"


async def test_bare_resume_refuses_undecided_proposals(db_engine: AsyncEngine) -> None:
    """AC-5 fail-closed half: artifact presence no longer advances a proposal gate."""
    spy = _SpyHandler()
    registry.register_handler("aquaculture", "aerate", spy)
    procedure = _procedure("sm-bare")
    action_id = await _run_and_persist(db_engine, procedure, "sm-2")

    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        with pytest.raises(ProcedureError, match="undecided proposals"):
            await resume_run(
                session, procedure, _agent(), _executors(0, []), "sm-2", vertical="aquaculture"
            )
    assert spy.calls == [], "nothing may execute on a refused resume"

    # The governed path still works: resolve -> resume -> completed.
    async with maker() as session:
        await resolve_gated_step(session, "sm-2", "aerate", {action_id: "approve"})
    async with maker() as fresh:
        resumed = await resume_run(
            fresh, procedure, _agent(), _executors(0, []), "sm-2", vertical="aquaculture"
        )
    assert resumed.run.status == PipelineRunStatus.COMPLETED.value
    assert len(spy.calls) == 1


async def test_empty_proposal_suspend_keeps_plain_resume(db_engine: AsyncEngine) -> None:
    """AC-5 scope guard: a no-decision suspend (empty proposal set — the empty
    watch set contract) still advances on a plain resume, unchanged."""
    registry.register_handler("aquaculture", "aerate", _SpyHandler())
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    procedure = _procedure("sm-empty")
    result = await run_procedure(
        procedure,
        _agent(),
        _executors(0, []),  # empty read -> zero proposals at the gate
        vertical="aquaculture",
        run_id="sm-3",
    )
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    assert (result.step_results[-1].artifact or {})["output_set"] == []
    async with maker() as session:
        await persist_run(session, result)

    async with maker() as fresh:
        resumed = await resume_run(
            fresh, procedure, _agent(), _executors(0, []), "sm-3", vertical="aquaculture"
        )
    assert resumed.run.status == PipelineRunStatus.COMPLETED.value


async def test_resume_reasserts_sod_tie(db_engine: AsyncEngine) -> None:
    """AC-5 SoD half: a resolved SoD gate whose governed_decision tie is gone
    (tampered/bypassed) refuses to resume; the intact twin passes."""
    spy = _SpyHandler()
    registry.register_handler("aquaculture", "aerate", spy)
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    procedure = _sod_procedure("sm-sod")
    principals = [_REQUESTER, _APPROVER]

    action_id = await _run_and_persist(db_engine, procedure, "sm-4", principal=_REQUESTER)
    async with maker() as session:
        resolved = await resolve_gated_step(
            session,
            "sm-4",
            "aerate",
            {action_id: "approve"},
            principal=_APPROVER,
            procedure=procedure,
            principals=principals,
        )
    assert (resolved.audit or {}).get("governed_decision"), "the SoD tie must be recorded"

    # Tamper: strip the governed_decision tie off the resolved step.
    async with maker() as session:
        row = (
            await session.execute(
                sa.select(StepResult).where(
                    StepResult.run_id == "sm-4", StepResult.step_id == "aerate"
                )
            )
        ).scalar_one()
        row.audit = {k: v for k, v in (row.audit or {}).items() if k != "governed_decision"}
        await session.commit()

    async with maker() as fresh:
        with pytest.raises(ProcedureError, match="governed_decision audit tie"):
            await resume_run(
                fresh, procedure, _agent(), _executors(0, []), "sm-4", vertical="aquaculture"
            )

    # The intact twin resumes normally.
    action_id_2 = await _run_and_persist(db_engine, procedure, "sm-5", principal=_REQUESTER)
    async with maker() as session:
        await resolve_gated_step(
            session,
            "sm-5",
            "aerate",
            {action_id_2: "approve"},
            principal=_APPROVER,
            procedure=procedure,
            principals=principals,
        )
    async with maker() as fresh:
        resumed = await resume_run(
            fresh, procedure, _agent(), _executors(0, []), "sm-5", vertical="aquaculture"
        )
    assert resumed.run.status == PipelineRunStatus.COMPLETED.value


async def test_optimistic_lock_makes_stale_writer_lose(db_engine: AsyncEngine) -> None:
    """The pipeline_runs.version column: a stale concurrent writer gets
    StaleDataError instead of silently double-writing run state."""
    registry.register_handler("aquaculture", "aerate", _SpyHandler())
    await _run_and_persist(db_engine, _procedure("sm-lock"), "sm-6")
    maker = async_sessionmaker(db_engine, expire_on_commit=False)

    async with maker() as s1, maker() as s2:
        r1 = await s1.get(PipelineRun, "sm-6")
        r2 = await s2.get(PipelineRun, "sm-6")
        assert r1 is not None and r2 is not None
        r2.status = PipelineRunStatus.CANCELLED.value
        await s2.commit()
        r1.status = PipelineRunStatus.FAILED.value
        with pytest.raises(StaleDataError):
            await s1.commit()
