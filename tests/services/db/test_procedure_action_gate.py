"""PLAN-0019 A-7 — the gated-action gate driver + resume (ADR-016 D2/D3/D4).

The Option-2 lifecycle end to end, DB-backed (skips without Postgres): a run
suspends at a ``gated`` action that only PROPOSED; the EXTERNAL gate
(:func:`resolve_gated_step`) applies the human's approve/reject via the shipped
``recommender`` gate verbatim and rewrites the step output; a plain
``resume_run`` then continues. Proves: approve -> handler fires + run completes;
**reject -> handler does NOT fire, the run CONTINUES (reject = continue + record)**.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.api.config import settings
from services.db.base import Base
from services.engine.llm.client import ChatResult
from services.engine.procedures.action_step import (
    ActionStepExecutor,
    GateApproverError,
    resolve_gated_step,
)
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
    Person,
    Procedure,
    Step,
    StepKind,
)
from services.engine.registry import registry
from tests.db_support import create_test_engine

# A resolving human for the non-SoD gate tests (ADR-016 S2 RF-1 / PLAN-0053 AC-1: a gate
# resolution now requires an identified approver even on a plain, non-SoD step).
_APPROVER = Person(person_id="pond-lead", name="Pond Lead", roles=frozenset({"pond_lead"}))


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
    """Fixed-output query executor + a call counter (proves resume continuation)."""

    def __init__(self, output: list[Any]) -> None:
        self.output = output
        self.calls = 0

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        self.calls += 1
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
        autonomy_ceiling=Autonomy.AUTO,
        allowed=AgentAllowed(action_handlers=["aerate"]),
    )


def _breach_set() -> list[Any]:
    return [{"pond": "p7", "event_id": "e7"}]


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


async def test_approve_executes_via_gate_then_resume_completes(db_engine: AsyncEngine) -> None:
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    spy = _SpyHandler()
    registry.register_handler("aquaculture", "aerate", spy)
    procedure = Procedure(
        procedure_id="round",
        title="Morning Round",
        goal="Act on DO breaches.",
        run_by="pond_agent",
        steps=[
            Step(step_id="read", name="Read", kind=StepKind.QUERY),
            Step(step_id="aerate", name="Aerate", kind=StepKind.ACTION, handler="aerate"),  # gated
        ],
    )
    action_exec = ActionStepExecutor(client_factory=lambda _m: _FakeChat(_chat_results(1)))
    executors: dict[StepKind, StepExecutor] = {
        StepKind.QUERY: _Query(_breach_set()),
        StepKind.ACTION: action_exec,
    }

    # Run -> the gated action proposes -> suspends; the handler has NOT fired.
    result = await run_procedure(
        procedure, _agent(), executors, vertical="aquaculture", run_id="run-ap"
    )
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    assert spy.calls == [], "the gated action must not execute before human approval"
    async with maker() as session:
        await persist_run(session, result)

    # EXTERNAL gate: approve -> execute() fires the handler verbatim.
    async with maker() as session:
        resolved = await resolve_gated_step(
            session, "run-ap", "aerate", {"action-e7": "approve"}, principal=_APPROVER
        )
    assert len(spy.calls) == 1, "approve must execute the handler via the shipped gate"
    assert resolved.artifact["output_set"][0]["status"] == "executed"

    # Plain resume just continues from the resolved step -> run completes.
    async with maker() as fresh:
        done = await resume_run(
            fresh, procedure, _agent(), executors, "run-ap", vertical="aquaculture"
        )
    assert done.run.status == PipelineRunStatus.COMPLETED.value
    async with maker() as third:
        reloaded = await load_run(third, "run-ap")
    assert reloaded is not None
    aerate = next(sr for sr in reloaded.step_results if sr.step_id == "aerate")
    assert aerate.status == StepResultStatus.COMPLETE.value


async def test_reject_does_not_execute_and_run_continues(db_engine: AsyncEngine) -> None:
    """Reject = continue + record: the handler never fires, the rejection is in the
    trace, and the run CONTINUES to its next step (a reject is not a failure)."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    spy = _SpyHandler()
    registry.register_handler("aquaculture", "aerate", spy)
    after = _Query([{"summary": "done"}])
    procedure = Procedure(
        procedure_id="round",
        title="Morning Round",
        run_by="pond_agent",
        steps=[
            Step(step_id="read", name="Read", kind=StepKind.QUERY),
            Step(step_id="aerate", name="Aerate", kind=StepKind.ACTION, handler="aerate"),  # gated
            Step(step_id="after", name="After", kind=StepKind.QUERY),  # must run after a reject
        ],
    )
    run_execs: dict[StepKind, StepExecutor] = {
        StepKind.QUERY: _Query(_breach_set()),
        StepKind.ACTION: ActionStepExecutor(client_factory=lambda _m: _FakeChat(_chat_results(1))),
    }
    result = await run_procedure(
        procedure, _agent(), run_execs, vertical="aquaculture", run_id="run-rej"
    )
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    async with maker() as session:
        await persist_run(session, result)

    # EXTERNAL gate: reject -> the handler must NOT fire.
    async with maker() as session:
        resolved = await resolve_gated_step(
            session, "run-rej", "aerate", {"action-e7": "reject"}, principal=_APPROVER
        )
    assert spy.calls == [], "a rejected action must never execute its handler"
    assert resolved.artifact["output_set"] == []  # nothing executed -> nothing threaded forward
    assert any(t["kind"] == "action_rejected" for t in resolved.reasoning_trace)

    # Resume continues PAST the rejected step to 'after' (reject != failure).
    resume_execs: dict[StepKind, StepExecutor] = {StepKind.QUERY: after}
    async with maker() as fresh:
        done = await resume_run(
            fresh, procedure, _agent(), resume_execs, "run-rej", vertical="aquaculture"
        )
    assert done.run.status == PipelineRunStatus.COMPLETED.value
    assert after.calls == 1, "the run must continue to the next step after a reject"


async def test_resume_stamps_the_human_actor_on_the_audit(db_engine: AsyncEngine) -> None:
    """PLAN-0053 AC-3 (SP-4, human path): ``resume_run`` threads the resolved human
    into the continuation, and the ``run_resumed`` audit row carries that person as
    a NON-NULL actor (the resume audit was previously actor-less — the never-null
    gap). Resolving + resuming with an explicit principal must record it."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    spy = _SpyHandler()
    registry.register_handler("aquaculture", "aerate", spy)
    approver = Person(person_id="approver-somchai", name="Somchai", roles=frozenset({"pond_lead"}))
    procedure = Procedure(
        procedure_id="round",
        title="Morning Round",
        goal="Act on DO breaches.",
        run_by="pond_agent",
        steps=[
            Step(step_id="read", name="Read", kind=StepKind.QUERY),
            Step(step_id="aerate", name="Aerate", kind=StepKind.ACTION, handler="aerate"),  # gated
        ],
    )
    executors: dict[StepKind, StepExecutor] = {
        StepKind.QUERY: _Query(_breach_set()),
        StepKind.ACTION: ActionStepExecutor(client_factory=lambda _m: _FakeChat(_chat_results(1))),
    }
    result = await run_procedure(
        procedure, _agent(), executors, vertical="aquaculture", run_id="run-actor"
    )
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    async with maker() as session:
        await persist_run(session, result)

    async with maker() as session:
        await resolve_gated_step(
            session, "run-actor", "aerate", {"action-e7": "approve"}, principal=approver
        )
    async with maker() as fresh:
        done = await resume_run(
            fresh,
            procedure,
            _agent(),
            executors,
            "run-actor",
            vertical="aquaculture",
            principal=approver,
        )
    assert done.run.status == PipelineRunStatus.COMPLETED.value

    # AC-3: the run_resumed audit row now carries the human actor (not None).
    async with maker() as session:
        rows = (
            await session.execute(
                sa.text(
                    "SELECT actor_person_id, payload FROM audit_log "
                    "WHERE run_id = 'run-actor' AND action = 'run_resumed'"
                )
            )
        ).all()
    assert len(rows) == 1
    actor_person_id, payload = rows[0]
    assert actor_person_id == "approver-somchai"
    assert payload["actor_kind"] == "human"


async def test_resolve_requires_explicit_decision(db_engine: AsyncEngine) -> None:
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    registry.register_handler("aquaculture", "aerate", _SpyHandler())
    procedure = Procedure(
        procedure_id="round",
        title="Round",
        run_by="pond_agent",
        steps=[
            Step(step_id="read", name="Read", kind=StepKind.QUERY),
            Step(step_id="aerate", name="Aerate", kind=StepKind.ACTION, handler="aerate"),
        ],
    )
    execs: dict[StepKind, StepExecutor] = {
        StepKind.QUERY: _Query(_breach_set()),
        StepKind.ACTION: ActionStepExecutor(client_factory=lambda _m: _FakeChat(_chat_results(1))),
    }
    result = await run_procedure(
        procedure, _agent(), execs, vertical="aquaculture", run_id="run-nd"
    )
    async with maker() as session:
        await persist_run(session, result)
    async with maker() as session:
        with pytest.raises(ProcedureError, match="no decision"):
            await resolve_gated_step(session, "run-nd", "aerate", {}, principal=_APPROVER)


async def test_gate_resolve_requires_identified_approver(
    db_engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-1 (the load-bearing RF-1 LIBRARY guard): resolving a PLAIN, non-SoD gated step with
    NO principal RAISES ``GateApproverError`` — INDEPENDENT of ``api_auth_enabled`` — so a
    non-HTTP caller (a future scheduler / a direct call) cannot silently apply a gate decision
    with no accountable approver. Phase A shipped this guard only at the HTTP endpoint
    (runs.py:337); this closes the library chokepoint (runs.py:334-336)."""
    monkeypatch.setattr(settings, "api_auth_enabled", False)  # the guard does not consult it
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    spy = _SpyHandler()
    registry.register_handler("aquaculture", "aerate", spy)
    procedure = Procedure(
        procedure_id="round",
        title="Morning Round",
        goal="Act on DO breaches.",
        run_by="pond_agent",
        steps=[
            Step(step_id="read", name="Read", kind=StepKind.QUERY),
            Step(step_id="aerate", name="Aerate", kind=StepKind.ACTION, handler="aerate"),
        ],
    )
    execs: dict[StepKind, StepExecutor] = {
        StepKind.QUERY: _Query(_breach_set()),
        StepKind.ACTION: ActionStepExecutor(client_factory=lambda _m: _FakeChat(_chat_results(1))),
    }
    result = await run_procedure(
        procedure, _agent(), execs, vertical="aquaculture", run_id="run-noappr"
    )
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    async with maker() as session:
        await persist_run(session, result)
    # A plain, non-SoD gated step + authn OFF + NO principal -> fail closed at the library.
    async with maker() as session:
        with pytest.raises(GateApproverError, match="identified human approver"):
            await resolve_gated_step(session, "run-noappr", "aerate", {"action-e7": "approve"})
    assert spy.calls == [], "no identified approver -> the handler must never fire (fail closed)"
