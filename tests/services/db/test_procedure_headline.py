"""PLAN-0019 A-11 — the aquaculture "Morning Pond Health Round" headline, end-to-end.

Drives the REAL shipped ``verticals/aquaculture/procedures.yaml`` headline (A-ζ)
manually, DB-backed (skips without Postgres), with a FAKE ``query`` executor + the
**REAL** ``EvaluateStepExecutor`` (PLAN-0022 Phase 2a — reading the REAL authored
band) + the **REAL** ``ActionStepExecutor`` (mock ``ChatClient`` — no live LLM;
Lesson #7 §3 behavioural assertions). Proves the ENGINE orchestrates the
named-input fan-out + the durable suspend/resolve/resume lifecycle, including the
ADR-0019 ``watch -> gated`` escalation (PLAN-0022 Phase 2b, SD-1=a):

  read_do -> judge (deterministic verdicts) -> aerate (gated, breach subset) SUSPEND
    -> resolve_gated_step(approve) -> resume
    -> escalate_watch (gated proposal, watch subset) SUSPEND
    -> resolve_gated_step(approve) -> resume
    -> summary (auto action, whole verdict set) -> COMPLETED

A second case asserts **reject = continue + record** on BOTH gates: rejected breach
and watch proposals never fire their handlers, yet the run still completes.
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
from services.engine.procedures.evaluate_step import EvaluateStepExecutor
from services.engine.procedures.orchestrator import (
    RunContext,
    StepExecutor,
    StepOutcome,
    run_procedure,
)
from services.engine.procedures.persistence import load_run, persist_run, resume_run
from services.engine.procedures.runs import PipelineRunStatus, StepResultStatus
from services.engine.procedures.spec import Agent, Person, Step, StepKind, load_procedures
from services.engine.registry import registry
from tests.db_support import create_test_engine

_APPROVER = Person(person_id="approver", name="Approver", roles=frozenset({"approver"}))

# Canned pond set: two breaches (DO crashed below the floor), one watch (floor..+1), one
# ok — `measured_value` is the reading field the REAL EvaluateStepExecutor judges, and
# (PLAN-0068) `do_floor` is the per-entity band it reads via `threshold_field: do_floor`
# — the shipped read_do join brings each pond's own floor onto its reading (uniform 4.0
# here so the breach/watch/ok split is unchanged from the pre-migration blanket 4.0).
PONDS: list[dict[str, Any]] = [
    {"pond_id": "p1", "event_id": "e1", "measured_value": 3.2, "do_floor": 4.0},  # breach
    {"pond_id": "p2", "event_id": "e2", "measured_value": 2.8, "do_floor": 4.0},  # breach
    {"pond_id": "p3", "event_id": "e3", "measured_value": 4.5, "do_floor": 4.0},  # watch
    {"pond_id": "p4", "event_id": "e4", "measured_value": 6.1, "do_floor": 4.0},  # ok
]
BREACH_IDS = {"action-e1", "action-e2"}
WATCH_ID = "action-e3"


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


def _headline() -> tuple[Any, Agent]:
    """Load the REAL shipped aquaculture headline procedure + its agent."""
    spec = load_procedures("aquaculture")
    proc = next(p for p in spec.procedures if p.procedure_id == "morning_pond_health_round")
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    return proc, agent


def _outputs(sr: Any) -> list[dict[str, Any]]:
    """A StepResult's recorded ``output_set`` (asserts the artifact exists)."""
    assert sr.artifact is not None, f"{sr.step_id}: no artifact recorded"
    out: list[dict[str, Any]] = sr.artifact["output_set"]
    return out


def _executors() -> dict[StepKind, StepExecutor]:
    """The REAL judge (deterministic, reads the authored band from the spec) + the
    REAL action executor; only the query is canned."""
    return {
        StepKind.QUERY: _Query(PONDS),
        StepKind.EVALUATE: EvaluateStepExecutor(),
        StepKind.ACTION: ActionStepExecutor(client_factory=lambda _m: _CyclingChat()),
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
    """The full headline: gated aerate over the breach set -> approve -> gated
    escalation proposal over the watch set (ADR-0019) -> approve -> auto summary
    over the whole verdict set -> completed."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    spy = _SpyHandler()
    # The gated aerate step fixes handler=start_emergency_aerator (PLAN-0019 B); the
    # watch escalation fixes increase_water_exchange (PLAN-0022 2b); the auto summary
    # keeps echo. Bind the spy to ALL so it records every gate firing.
    registry.register_handler("aquaculture", "echo", spy)
    registry.register_handler("aquaculture", "start_emergency_aerator", spy)
    registry.register_handler("aquaculture", "increase_water_exchange", spy)
    procedure, agent = _headline()
    executors = _executors()

    # 1. Run -> the REAL judge tags verdicts -> aerate (gated) PROPOSES on the
    #    breach subset only -> SUSPEND.
    result = await run_procedure(
        procedure, agent, executors, vertical="aquaculture", run_id="hl-ap"
    )
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    judge_sr = next(sr for sr in result.step_results if sr.step_id == "judge")
    assert [e["verdict"] for e in _outputs(judge_sr)] == [
        "breach",
        "breach",
        "watch",
        "ok",
    ], "the REAL deterministic judge tagged the authored band's verdicts"
    aerate_sr = next(sr for sr in result.step_results if sr.step_id == "aerate")
    proposals = _outputs(aerate_sr)
    assert {p["action_id"] for p in proposals} == BREACH_IDS, "fan-out: only the breach subset"
    assert all(p["status"] == "proposed" for p in proposals)
    assert spy.calls == [], "a gated action must not execute before human approval"
    async with maker() as session:
        await persist_run(session, result)

    # 2. External gate: approve both breaches -> the aerator handler fires once per pond.
    async with maker() as session:
        resolved = await resolve_gated_step(
            session,
            "hl-ap",
            "aerate",
            {"action-e1": "approve", "action-e2": "approve"},
            principal=_APPROVER,
        )
    assert len(spy.calls) == 2, "approve must execute the handler once per breach pond"
    assert all(e["status"] == "executed" for e in _outputs(resolved))

    # 3. Resume -> escalate_watch (gated proposal, ADR-0019) over the WATCH subset
    #    -> SUSPEND again with a CONCRETE recommendation (not a bare "go look").
    async with maker() as fresh:
        after_escalate = await resume_run(
            fresh, procedure, agent, executors, "hl-ap", vertical="aquaculture"
        )
    assert after_escalate.run.status == PipelineRunStatus.WAITING_HUMAN.value
    escalate_sr = next(sr for sr in after_escalate.step_results if sr.step_id == "escalate_watch")
    watch_proposals = _outputs(escalate_sr)
    assert [p["action_id"] for p in watch_proposals] == [WATCH_ID], "only the watch subset"
    assert watch_proposals[0]["status"] == "proposed"
    assert watch_proposals[0]["action"]["suggested_handler"] == "increase_water_exchange"
    assert len(spy.calls) == 2, "the watch proposal must not execute before approval"

    # 4. External gate: approve the watch proposal -> the water-exchange handler fires.
    async with maker() as session:
        await resolve_gated_step(
            session, "hl-ap", "escalate_watch", {WATCH_ID: "approve"}, principal=_APPROVER
        )
    assert len(spy.calls) == 3, "approving the escalation executes its handler"

    # 5. Resume -> summary (auto action) over the WHOLE verdict set -> COMPLETED.
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
    assert len(_outputs(summary)) == len(PONDS)
    assert all(e["status"] == "executed" for e in _outputs(summary))
    # Telemetry seam (AC A-9): every step carries duration_ms + a trace + an audit record.
    for sr in reloaded.step_results:
        assert sr.duration_ms is not None, f"{sr.step_id}: duration_ms"
        assert sr.reasoning_trace, f"{sr.step_id}: reasoning_trace"
        assert sr.audit, f"{sr.step_id}: audit"


async def test_headline_reject_breach_continues(db_engine: AsyncEngine) -> None:
    """Reject = continue + record on BOTH gates: rejected breach AND watch proposals
    never fire their handlers, yet the run still continues to completion."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    spy = _SpyHandler()
    registry.register_handler("aquaculture", "echo", spy)
    registry.register_handler("aquaculture", "start_emergency_aerator", spy)
    registry.register_handler("aquaculture", "increase_water_exchange", spy)
    procedure, agent = _headline()
    executors = _executors()

    result = await run_procedure(
        procedure, agent, executors, vertical="aquaculture", run_id="hl-rej"
    )
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    async with maker() as session:
        await persist_run(session, result)

    # External gate: reject both breaches -> the handler must NOT fire.
    async with maker() as session:
        resolved = await resolve_gated_step(
            session,
            "hl-rej",
            "aerate",
            {"action-e1": "reject", "action-e2": "reject"},
            principal=_APPROVER,
        )
    assert spy.calls == [], "a rejected breach action must never execute its handler"
    assert _outputs(resolved) == [], "nothing executed -> nothing threaded forward"
    assert sum(1 for t in resolved.reasoning_trace or [] if t["kind"] == "action_rejected") == 2

    # Resume past the rejected step -> escalate_watch (gated proposal) suspends;
    # reject it too -> its handler must NOT fire either (reject = continue + record).
    async with maker() as fresh:
        after_escalate = await resume_run(
            fresh, procedure, agent, executors, "hl-rej", vertical="aquaculture"
        )
    assert after_escalate.run.status == PipelineRunStatus.WAITING_HUMAN.value
    escalate_sr = next(sr for sr in after_escalate.step_results if sr.step_id == "escalate_watch")
    assert [p["action_id"] for p in _outputs(escalate_sr)] == [WATCH_ID]
    async with maker() as session:
        await resolve_gated_step(
            session, "hl-rej", "escalate_watch", {WATCH_ID: "reject"}, principal=_APPROVER
        )
    assert spy.calls == [], "a rejected watch proposal must never execute its handler"

    async with maker() as fresh:
        done = await resume_run(
            fresh, procedure, agent, executors, "hl-rej", vertical="aquaculture"
        )
    assert done.run.status == PipelineRunStatus.COMPLETED.value, "a reject is not a failure"
