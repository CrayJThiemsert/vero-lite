"""PLAN-0019 A-11 — the aquaculture "Morning Pond Health Round" headline, end-to-end.

Drives the REAL shipped ``verticals/aquaculture/procedures.yaml`` headline (A-ζ)
manually, DB-backed (skips without Postgres), with FAKE ``query`` / ``evaluate`` /
``human_task`` executors + the **REAL** ``ActionStepExecutor`` (mock ``ChatClient`` —
no live LLM; Lesson #7 §3 behavioural assertions). Proves the ENGINE orchestrates
the named-input fan-out + the durable suspend/resolve/resume lifecycle:

  read_do -> judge -> aerate (gated, breach subset) SUSPEND
    -> resolve_gated_step(approve) -> resume
    -> visual (human_task, watch subset) SUSPEND -> resume
    -> summary (auto action, whole verdict set) -> COMPLETED

A second case asserts **reject = continue + record**: a rejected breach action never
fires its handler, yet the run still continues to completion.
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
    run_procedure,
)
from services.engine.procedures.persistence import load_run, persist_run, resume_run
from services.engine.procedures.runs import PipelineRunStatus, StepResultStatus
from services.engine.procedures.spec import Agent, Step, StepKind, load_procedures
from services.engine.recommender import crosses_threshold
from services.engine.registry import registry
from tests.db_support import create_test_engine

# Canned pond set: two breaches (DO crashed below 4 mg/L), one watch (4-5), one ok.
PONDS: list[dict[str, Any]] = [
    {"pond_id": "p1", "event_id": "e1", "do": 3.2},  # breach
    {"pond_id": "p2", "event_id": "e2", "do": 2.8},  # breach
    {"pond_id": "p3", "event_id": "e3", "do": 4.5},  # watch
    {"pond_id": "p4", "event_id": "e4", "do": 6.1},  # ok
]
BREACH_IDS = {"action-e1", "action-e2"}


def _verdict(do: float) -> str:
    """The 4 mg/L breach rule, reusing the shipped threshold helper (below = a crash):
    breach (<= 4), watch (4 < do <= 5), ok (> 5)."""
    if crosses_threshold(do, 4.0, "below"):  # do <= 4.0 — a DO crash below the floor
        return "breach"
    if crosses_threshold(do, 5.0, "below"):  # 4 < do <= 5 — borderline
        return "watch"
    return "ok"


class _CyclingChat:
    """A mock ChatClient sized to ANY entity count: returns a reasoning draft on the
    call-1 (no ``response_format``) and a canned judgment on the call-2 (with
    ``response_format``), so one instance serves both the 2-pond aerate step and the
    4-pond summary step."""

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        if response_format is not None:  # call 2 — the structured judgment
            return ChatResult(content=_judgment_json(), thinking=None, model="gpt-oss:20b", raw={})
        return ChatResult(content="reasoning draft", thinking="t", model="gpt-oss:20b", raw={})


def _judgment_json() -> str:
    return json.dumps(
        {
            "title": "Start emergency aerator",
            "description": "Dissolved oxygen fell below the 4 mg/L breach threshold.",
            "rationale": "DO is a crash signal; aerate to recover oxygen.",
            "confidence": 0.9,
            "affected_entities": [{"object_type": "Pond", "primary_key": "p"}],
            "suggested_handler": "echo",  # must be a REGISTERED handler (semantic check)
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
    """Fixed-output query executor (the FAKE ``read_do``)."""

    def __init__(self, output: list[Any]) -> None:
        self.output = output

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(
            output=self.output, reasoning_trace=[{"kind": "query", "summary": "read"}]
        )


class _Evaluate:
    """FAKE ``judge``: tags each entity's ``verdict`` via the 4 mg/L rule."""

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        tagged = [{**e, "verdict": _verdict(e["do"])} for e in input_set]
        return StepOutcome(
            output=tagged, reasoning_trace=[{"kind": "evaluate", "summary": "tagged verdicts"}]
        )


class _HumanTask:
    """FAKE ``human_task``: records the set it received and echoes it as its output."""

    def __init__(self) -> None:
        self.received: list[list[Any]] = []

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        self.received.append(list(input_set))
        return StepOutcome(
            output=list(input_set),
            reasoning_trace=[{"kind": "human_task", "summary": "visual check queued"}],
        )


def _headline() -> tuple[Any, Agent]:
    """Load the REAL shipped aquaculture headline procedure + its agent."""
    spec = load_procedures("aquaculture")
    proc = next(p for p in spec.procedures if p.procedure_id == "morning_pond_health_round")
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    return proc, agent


def _executors(human: _HumanTask) -> dict[StepKind, StepExecutor]:
    return {
        StepKind.QUERY: _Query(PONDS),
        StepKind.EVALUATE: _Evaluate(),
        StepKind.ACTION: ActionStepExecutor(client_factory=lambda _m: _CyclingChat()),
        StepKind.HUMAN_TASK: human,
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


async def test_headline_end_to_end_approve(db_engine: AsyncEngine) -> None:
    """The full headline: gated aerate over the breach set -> approve -> human_task
    over the watch set -> auto summary over the whole verdict set -> completed."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    spy = _SpyHandler()
    # The gated aerate step now fixes handler=start_emergency_aerator (PLAN-0019 B);
    # the auto summary step keeps echo. Bind the spy to BOTH so it records the gate.
    registry.register_handler("aquaculture", "echo", spy)
    registry.register_handler("aquaculture", "start_emergency_aerator", spy)
    procedure, agent = _headline()
    human = _HumanTask()
    executors = _executors(human)

    # 1. Run -> aerate (gated) PROPOSES on the breach subset only -> SUSPEND.
    result = await run_procedure(
        procedure, agent, executors, vertical="aquaculture", run_id="hl-ap"
    )
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    aerate_sr = next(sr for sr in result.step_results if sr.step_id == "aerate")
    proposals = aerate_sr.artifact["output_set"]
    assert {p["action_id"] for p in proposals} == BREACH_IDS, "fan-out: only the breach subset"
    assert all(p["status"] == "proposed" for p in proposals)
    assert spy.calls == [], "a gated action must not execute before human approval"
    async with maker() as session:
        await persist_run(session, result)

    # 2. External gate: approve both breaches -> the aerator handler fires once per pond.
    async with maker() as session:
        resolved = await resolve_gated_step(
            session, "hl-ap", "aerate", {"action-e1": "approve", "action-e2": "approve"}
        )
    assert len(spy.calls) == 2, "approve must execute the handler once per breach pond"
    assert all(e["status"] == "executed" for e in resolved.artifact["output_set"])

    # 3. Resume -> visual (human_task) over the WATCH subset -> SUSPEND again.
    async with maker() as fresh:
        after_visual = await resume_run(
            fresh, procedure, agent, executors, "hl-ap", vertical="aquaculture"
        )
    assert after_visual.run.status == PipelineRunStatus.WAITING_HUMAN.value
    assert human.received == [[{**PONDS[2], "verdict": "watch"}]], "fan-out: only the watch subset"

    # 4. Resume -> summary (auto action) over the WHOLE verdict set -> COMPLETED.
    async with maker() as fresh:
        done = await resume_run(fresh, procedure, agent, executors, "hl-ap", vertical="aquaculture")
    assert done.run.status == PipelineRunStatus.COMPLETED.value

    async with maker() as third:
        reloaded = await load_run(third, "hl-ap")
    assert reloaded is not None
    by_id = {sr.step_id: sr for sr in reloaded.step_results}
    # The terminal auto summary ran over all four ponds and executed each.
    summary = by_id["summary"]
    assert summary.status == StepResultStatus.COMPLETE.value
    assert len(summary.artifact["output_set"]) == len(PONDS)
    assert all(e["status"] == "executed" for e in summary.artifact["output_set"])
    # Telemetry seam (AC A-9): every step carries duration_ms + a trace + an audit record.
    for sr in reloaded.step_results:
        assert sr.duration_ms is not None, f"{sr.step_id}: duration_ms"
        assert sr.reasoning_trace, f"{sr.step_id}: reasoning_trace"
        assert sr.audit, f"{sr.step_id}: audit"


async def test_headline_reject_breach_continues(db_engine: AsyncEngine) -> None:
    """Reject = continue + record: a rejected breach action never fires its handler,
    yet the run still continues through the watch human_task to completion."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    spy = _SpyHandler()
    # The gated aerate step now fixes handler=start_emergency_aerator (PLAN-0019 B);
    # the auto summary step keeps echo. Bind the spy to BOTH so it records the gate.
    registry.register_handler("aquaculture", "echo", spy)
    registry.register_handler("aquaculture", "start_emergency_aerator", spy)
    procedure, agent = _headline()
    human = _HumanTask()
    executors = _executors(human)

    result = await run_procedure(
        procedure, agent, executors, vertical="aquaculture", run_id="hl-rej"
    )
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    async with maker() as session:
        await persist_run(session, result)

    # External gate: reject both breaches -> the handler must NOT fire.
    async with maker() as session:
        resolved = await resolve_gated_step(
            session, "hl-rej", "aerate", {"action-e1": "reject", "action-e2": "reject"}
        )
    assert spy.calls == [], "a rejected breach action must never execute its handler"
    assert resolved.artifact["output_set"] == [], "nothing executed -> nothing threaded forward"
    assert sum(1 for t in resolved.reasoning_trace if t["kind"] == "action_rejected") == 2

    # Resume past the rejected step -> visual (watch) suspends -> resume -> completed.
    async with maker() as fresh:
        after_visual = await resume_run(
            fresh, procedure, agent, executors, "hl-rej", vertical="aquaculture"
        )
    assert after_visual.run.status == PipelineRunStatus.WAITING_HUMAN.value
    assert human.received == [[{**PONDS[2], "verdict": "watch"}]]

    async with maker() as fresh:
        done = await resume_run(
            fresh, procedure, agent, executors, "hl-rej", vertical="aquaculture"
        )
    assert done.run.status == PipelineRunStatus.COMPLETED.value, "a reject is not a failure"
