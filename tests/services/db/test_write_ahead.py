"""PLAN-0047 Step 4 tests (AC-6) — write-ahead runs + decision-before-effect.

DB-backed (skips without Postgres). Proves:

* the ``running`` PipelineRun row is COMMITTED before step 1 executes, and
  each StepResult is committed as it completes (a later step can see the
  earlier step's row from a separate connection);
* a handler that raises mid-resolve leaves a committed decision record
  (``pending_execution``) and NO phantom executed effect — the step stays
  ``waiting_human`` with the ORIGINAL proposals intact, and a retry resolve
  completes the gate normally after the cause is fixed.
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
from services.engine.procedures.action_step import ActionStepExecutor, resolve_gated_step
from services.engine.procedures.orchestrator import (
    RunContext,
    StepExecutor,
    StepOutcome,
)
from services.engine.procedures.persistence import (
    load_run,
    resume_run,
    run_procedure_persisted,
)
from services.engine.procedures.runs import PipelineRunStatus, StepResultStatus
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    Person,
    Procedure,
    Step,
    StepKind,
)
from services.engine.registry import registry
from tests.db_support import create_test_engine

_APPROVER = Person(person_id="approver", name="Approver", roles=frozenset({"approver"}))


class _FakeChat:
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


class _FlakyHandler:
    """Raises on the first call (the injected crash), succeeds afterwards."""

    def __init__(self) -> None:
        self.calls: list[Any] = []
        self.fail_next = True

    async def __call__(self, action: Any) -> dict[str, Any]:
        self.calls.append(action)
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("boom — injected handler crash (AC-6)")
        return {"ok": True, "executed": action.id}


class _ProbingQuery:
    """Step-1 executor that PROVES the write-ahead: the run row is already
    durable (status running) when the first step executes."""

    def __init__(self, probe_engine: AsyncEngine, run_id: str) -> None:
        self._engine = probe_engine
        self._run_id = run_id
        self.observed_status: str | None = None

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        async with self._engine.connect() as conn:
            self.observed_status = (
                await conn.execute(
                    sa.text("SELECT status FROM pipeline_runs WHERE run_id = :run_id"),
                    {"run_id": self._run_id},
                )
            ).scalar_one_or_none()
        return StepOutcome(
            output=[{"pond": "p7", "event_id": "e7"}],
            reasoning_trace=[{"kind": "query", "summary": "read"}],
        )


class _ProbingJudge:
    """Step-2 executor that PROVES per-step persistence: step 1's StepResult
    row is already committed when step 2 executes."""

    def __init__(self, probe_engine: AsyncEngine, run_id: str) -> None:
        self._engine = probe_engine
        self._run_id = run_id
        self.observed_prior_steps: int | None = None

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        async with self._engine.connect() as conn:
            self.observed_prior_steps = (
                await conn.execute(
                    sa.text(
                        "SELECT count(*) FROM step_results "
                        "WHERE run_id = :run_id AND status = 'complete'"
                    ),
                    {"run_id": self._run_id},
                )
            ).scalar_one()
        return StepOutcome(
            output=list(input_set),
            reasoning_trace=[{"kind": "evaluate", "summary": "judged"}],
        )


def _agent() -> Agent:
    return Agent(
        agent_id="pond_agent",
        name="Pond Agent",
        autonomy_ceiling=Autonomy.GATED,
        allowed=AgentAllowed(action_handlers=["aerate"]),
    )


def _procedure() -> Procedure:
    return Procedure(
        procedure_id="wa-round",
        title="Write-ahead Round",
        goal="Act on DO breaches.",
        run_by="pond_agent",
        steps=[
            Step(step_id="read", name="Read", kind=StepKind.QUERY),
            Step(step_id="judge", name="Judge", kind=StepKind.EVALUATE),
            Step(step_id="aerate", name="Aerate", kind=StepKind.ACTION, handler="aerate"),
        ],
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


async def test_write_ahead_run_row_and_per_step_persistence(db_engine: AsyncEngine) -> None:
    """AC-6 write-ahead half: the run row is durable BEFORE step 1 runs, and
    step 1's result row is durable BEFORE step 2 runs."""
    registry.register_handler("aquaculture", "aerate", _FlakyHandler())
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    run_id = "wa-1"
    probe_query = _ProbingQuery(db_engine, run_id)
    probe_judge = _ProbingJudge(db_engine, run_id)
    executors: dict[StepKind, StepExecutor] = {
        StepKind.QUERY: probe_query,
        StepKind.EVALUATE: probe_judge,
        StepKind.ACTION: ActionStepExecutor(client_factory=lambda _m: _FakeChat(_chat_results(1))),
    }

    async with maker() as session:
        result = await run_procedure_persisted(
            session, _procedure(), _agent(), executors, vertical="aquaculture", run_id=run_id
        )

    assert probe_query.observed_status == "running", "run row must be durable before step 1"
    assert probe_judge.observed_prior_steps == 1, "step 1's row must be durable before step 2"
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value

    # The suspend itself is durable too — a fresh session sees the full record.
    async with maker() as fresh:
        loaded = await load_run(fresh, run_id)
    assert loaded is not None
    assert loaded.run.status == PipelineRunStatus.WAITING_HUMAN.value
    # sorted: load_run orders on a wall clock — the durable record is a step SET, not an order.
    assert sorted(sr.step_id for sr in loaded.step_results) == ["aerate", "judge", "read"]


async def test_handler_crash_leaves_decision_no_phantom_effect(db_engine: AsyncEngine) -> None:
    """AC-6 crash-injection half: a handler raising mid-resolve leaves a
    committed pending_execution decision, the original proposals, and NO
    executed effect — and the gate is retryable once the cause is fixed."""
    flaky = _FlakyHandler()
    registry.register_handler("aquaculture", "aerate", flaky)
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    run_id = "wa-2"
    executors: dict[StepKind, StepExecutor] = {
        StepKind.QUERY: _ProbingQuery(db_engine, run_id),
        StepKind.EVALUATE: _ProbingJudge(db_engine, run_id),
        StepKind.ACTION: ActionStepExecutor(client_factory=lambda _m: _FakeChat(_chat_results(1))),
    }
    procedure = _procedure()

    async with maker() as session:
        result = await run_procedure_persisted(
            session, procedure, _agent(), executors, vertical="aquaculture", run_id=run_id
        )
    proposals = (result.step_results[-1].artifact or {})["output_set"]
    action_id = str(proposals[0]["action_id"])

    # The injected crash: the handler raises AFTER the decision commit.
    async with maker() as session:
        with pytest.raises(RuntimeError, match="injected handler crash"):
            await resolve_gated_step(
                session, run_id, "aerate", {action_id: "approve"}, principal=_APPROVER
            )
    assert len(flaky.calls) == 1

    # Post-crash DB state (fresh session): decision committed, no phantom effect.
    async with maker() as fresh:
        loaded = await load_run(fresh, run_id)
    assert loaded is not None
    # By step_id, not by position (wall-clock order) and not by status — the status is what
    # this test asserts, so selecting on it would make the assertion below circular.
    crashed = next(sr for sr in loaded.step_results if sr.step_id == "aerate")
    assert crashed.status == StepResultStatus.WAITING_HUMAN.value, "gate must NOT be resolved"
    artifact = crashed.artifact or {}
    assert artifact["output_set"] == proposals, "original proposals intact (retryable)"
    decisions = artifact["decisions"]
    assert decisions and decisions[0]["status"] == "pending_execution"
    assert all(entry.get("receipt") is None for entry in decisions), "no phantom receipt"

    # Recovery: the cause is fixed -> the SAME gate resolves + resumes normally.
    async with maker() as session:
        resolved = await resolve_gated_step(
            session, run_id, "aerate", {action_id: "approve"}, principal=_APPROVER
        )
    assert resolved.status == StepResultStatus.RESOLVED.value
    assert len(flaky.calls) == 2
    async with maker() as fresh:
        resumed = await resume_run(
            fresh,
            procedure,
            _agent(),
            {
                StepKind.QUERY: _ProbingQuery(db_engine, run_id),
                StepKind.EVALUATE: _ProbingJudge(db_engine, run_id),
                StepKind.ACTION: ActionStepExecutor(
                    client_factory=lambda _m: _FakeChat(_chat_results(0))
                ),
            },
            run_id,
            vertical="aquaculture",
        )
    assert resumed.run.status == PipelineRunStatus.COMPLETED.value
    final = next(sr for sr in resumed.step_results if sr.step_id == "aerate")
    receipts = [entry.get("receipt") for entry in (final.artifact or {})["output_set"]]
    assert receipts and receipts[0] is not None, "the executed effect carries its receipt"
