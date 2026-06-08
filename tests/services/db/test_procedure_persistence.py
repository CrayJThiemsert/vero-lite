"""PLAN-0019 Part A — durable suspend/resume (ADR-016 D4, AC A-5).

Requires a live Postgres; skips gracefully when unreachable (binds to the
disposable ``<db>_test``). Demonstrates the persist -> (fresh process) -> load ->
resume cycle: a run that suspends at a ``gated`` action is persisted, then a
SEPARATE session reconstructs it from the DB and resumes from the step after the
suspended one to completion — with the completed prefix never re-executed.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.db.base import Base
from services.engine.procedures.orchestrator import (
    ProcedureError,
    RunContext,
    StepExecutor,
    StepOutcome,
    run_procedure,
)
from services.engine.procedures.persistence import load_run, persist_run, resume_run
from services.engine.procedures.runs import PipelineRunStatus, StepResultStatus
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    OnFailure,
    Procedure,
    Step,
    StepKind,
)
from tests.db_support import create_test_engine


class _Exec:
    """A fixed-output executor + a call counter (proves no re-execution on resume).

    Also records the goal it saw on its RunContext, so resume's goal threading
    (A-8) can be asserted across a fresh process.
    """

    def __init__(self, output: list[Any]) -> None:
        self.output = output
        self.calls = 0
        self.goals: list[str | None] = []

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        self.calls += 1
        self.goals.append(ctx.goal)
        return StepOutcome(
            output=self.output,
            reasoning_trace=[{"kind": step.kind.value, "summary": step.step_id}],
        )


class _RaisingExec:
    """Always raises — simulates a step failure (the cause a human later fixes)."""

    def __init__(self) -> None:
        self.calls = 0

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        self.calls += 1
        raise RuntimeError("transient failure")


def _agent() -> Agent:
    return Agent(
        agent_id="pond_agent",
        name="Pond Agent",
        autonomy_ceiling=Autonomy.AUTO,
        allowed=AgentAllowed(action_handlers=["echo"]),
    )


def _executors() -> dict[StepKind, StepExecutor]:
    return {
        StepKind.QUERY: _Exec([{"pond": "p7"}]),
        StepKind.ACTION: _Exec([{"action": "aerate"}]),
    }


def _gated_procedure() -> Procedure:
    """query/auto -> action/gated (suspends) -> action/auto (terminal)."""
    return Procedure(
        procedure_id="morning_round",
        title="Morning Round",
        goal="Run the morning pond health round; act on DO breaches.",
        run_by="pond_agent",
        steps=[
            Step(step_id="read", name="Read DO", kind=StepKind.QUERY),
            Step(step_id="aerate", name="Aerate", kind=StepKind.ACTION, handler="echo"),  # gated
            Step(
                step_id="summary",
                name="Summary",
                kind=StepKind.ACTION,
                autonomy=Autonomy.AUTO,
                handler="echo",
            ),
        ],
    )


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    """A fresh NullPool engine with the schema created; skips without Postgres."""
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


async def test_persist_and_load_round_trip(db_engine: AsyncEngine) -> None:
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    result = await run_procedure(
        _gated_procedure(), _agent(), _executors(), vertical="aquaculture", run_id="run-pl"
    )
    async with maker() as session:
        await persist_run(session, result)

    async with maker() as fresh:
        loaded = await load_run(fresh, "run-pl")
    assert loaded is not None
    assert loaded.run.status == result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    assert [sr.step_id for sr in loaded.step_results] == ["read", "aerate"]
    # the telemetry seam survives the round-trip
    aerate = loaded.step_results[-1]
    assert aerate.status == StepResultStatus.WAITING_HUMAN.value
    assert aerate.artifact == {"output_set": [{"action": "aerate"}]}


async def test_resume_across_fresh_session_completes(db_engine: AsyncEngine) -> None:
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    procedure = _gated_procedure()
    executors = _executors()

    # First process: run -> suspends at the gated action.
    result = await run_procedure(
        procedure, _agent(), executors, vertical="aquaculture", run_id="run-res"
    )
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    async with maker() as session:
        await persist_run(session, result)

    # Fresh "process": reconstruct from the DB + a fresh executor set, then resume.
    fresh_executors = _executors()
    async with maker() as fresh:
        resumed = await resume_run(
            fresh, procedure, _agent(), fresh_executors, "run-res", vertical="aquaculture"
        )
    assert resumed.run.status == PipelineRunStatus.COMPLETED.value
    statuses = {sr.step_id: sr.status for sr in resumed.step_results}
    assert statuses["aerate"] == StepResultStatus.COMPLETE.value  # the human resolved it
    assert statuses["summary"] == StepResultStatus.COMPLETE.value  # the terminal step ran
    # only the post-suspend step ran in the fresh process — the prefix was NOT re-executed.
    assert fresh_executors[StepKind.QUERY].calls == 0  # type: ignore[attr-defined]
    assert fresh_executors[StepKind.ACTION].calls == 1  # type: ignore[attr-defined]
    # A-8: resume threads Procedure.goal onto the RunContext of the resumed step.
    assert fresh_executors[StepKind.ACTION].goals == [  # type: ignore[attr-defined]
        "Run the morning pond health round; act on DO breaches."
    ]

    # durably persisted: a third session sees the completed 3-step run.
    async with maker() as third:
        reloaded = await load_run(third, "run-res")
    assert reloaded is not None
    assert reloaded.run.status == PipelineRunStatus.COMPLETED.value
    assert len(reloaded.step_results) == 3


async def test_resume_reruns_an_escalated_failed_step(db_engine: AsyncEngine) -> None:
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    procedure = Procedure(
        procedure_id="escalating_round",
        title="Escalating",
        run_by="pond_agent",
        steps=[
            Step(
                step_id="read",
                name="Read",
                kind=StepKind.QUERY,
                on_failure=OnFailure.ESCALATE_TO_HUMAN,
            ),
            Step(
                step_id="act",
                name="Act",
                kind=StepKind.ACTION,
                autonomy=Autonomy.AUTO,
                handler="echo",
            ),
        ],
    )
    # First process: the query step fails -> escalate_to_human -> waiting_human.
    failing: dict[StepKind, StepExecutor] = {
        StepKind.QUERY: _RaisingExec(),
        StepKind.ACTION: _Exec([{"act": 1}]),
    }
    result = await run_procedure(
        procedure, _agent(), failing, vertical="aquaculture", run_id="run-esc"
    )
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    suspended = result.step_results[-1]
    assert suspended.step_id == "read"
    assert suspended.status == StepResultStatus.WAITING_HUMAN.value
    assert suspended.artifact is None  # the failure path records no artifact
    async with maker() as session:
        await persist_run(session, result)

    # Fresh process: the human fixed the cause -> a WORKING query executor; resume.
    fixed: dict[StepKind, StepExecutor] = {
        StepKind.QUERY: _Exec([{"pond": "p7"}]),
        StepKind.ACTION: _Exec([{"act": 1}]),
    }
    async with maker() as fresh:
        resumed = await resume_run(
            fresh, procedure, _agent(), fixed, "run-esc", vertical="aquaculture"
        )
    assert resumed.run.status == PipelineRunStatus.COMPLETED.value
    statuses = {sr.step_id: sr.status for sr in resumed.step_results}
    assert statuses["read"] == StepResultStatus.COMPLETE.value  # the failed step RE-RAN + succeeded
    assert statuses["act"] == StepResultStatus.COMPLETE.value
    assert fixed[StepKind.QUERY].calls == 1  # type: ignore[attr-defined]  # the read re-ran

    # the re-run OVERWROTE the stale failed record — no duplicate read row.
    async with maker() as third:
        reloaded = await load_run(third, "run-esc")
    assert reloaded is not None
    assert reloaded.run.status == PipelineRunStatus.COMPLETED.value
    assert len(reloaded.step_results) == 2
    read_row = next(sr for sr in reloaded.step_results if sr.step_id == "read")
    assert read_row.status == StepResultStatus.COMPLETE.value
    assert read_row.artifact == {"output_set": [{"pond": "p7"}]}


async def test_resume_missing_run_raises(db_engine: AsyncEngine) -> None:
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        with pytest.raises(ProcedureError, match="not found"):
            await resume_run(
                session, _gated_procedure(), _agent(), _executors(), "ghost", vertical="aquaculture"
            )


async def test_resume_non_waiting_run_raises(db_engine: AsyncEngine) -> None:
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    # an all-auto procedure completes; resuming a completed run is rejected.
    completed = Procedure(
        procedure_id="auto_round",
        title="Auto",
        run_by="pond_agent",
        steps=[
            Step(step_id="read", name="Read", kind=StepKind.QUERY),
            Step(
                step_id="act",
                name="Act",
                kind=StepKind.ACTION,
                autonomy=Autonomy.AUTO,
                handler="echo",
            ),
        ],
    )
    result = await run_procedure(
        completed, _agent(), _executors(), vertical="aquaculture", run_id="run-done"
    )
    assert result.run.status == PipelineRunStatus.COMPLETED.value
    async with maker() as session:
        await persist_run(session, result)
    async with maker() as fresh:
        with pytest.raises(ProcedureError, match="not resumable"):
            await resume_run(
                fresh, completed, _agent(), _executors(), "run-done", vertical="aquaculture"
            )
