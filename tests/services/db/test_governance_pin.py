"""PLAN-0047 Step 6 tests (AC-8) — per-run governance-config pinning.

DB-backed (skips without Postgres). Proves: a governance-config edit made
between suspend and resume is REFUSED fail-closed at both the gate and the
resume (never silently applied to the in-flight run); the unedited config
proceeds normally; a legacy un-pinned row skips the check; and the pin
hash is deterministic for equal configs.
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
from services.engine.procedures.governance_pin import governance_pin_for
from services.engine.procedures.orchestrator import (
    ProcedureError,
    RunContext,
    StepExecutor,
    StepOutcome,
)
from services.engine.procedures.persistence import resume_run, run_procedure_persisted
from services.engine.procedures.runs import PipelineRunStatus
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    Procedure,
    SoDConstraint,
    Step,
    StepKind,
)
from services.engine.registry import registry
from tests.db_support import create_test_engine


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


class _Query:
    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(
            output=[{"pond": "p7", "event_id": "e7"}],
            reasoning_trace=[{"kind": "query", "summary": "read"}],
        )


class _SpyHandler:
    async def __call__(self, action: Any) -> dict[str, Any]:
        return {"ok": True, "executed": action.id}


def _executors(n: int) -> dict[StepKind, StepExecutor]:
    return {
        StepKind.QUERY: _Query(),
        StepKind.ACTION: ActionStepExecutor(client_factory=lambda _m: _FakeChat(_chat_results(n))),
    }


def _agent() -> Agent:
    return Agent(
        agent_id="pond_agent",
        name="Pond Agent",
        autonomy_ceiling=Autonomy.GATED,
        allowed=AgentAllowed(action_handlers=["aerate"]),
    )


def _procedure(*, with_sod: bool = False) -> Procedure:
    """The same 2-step gated round; ``with_sod=True`` = the governance EDIT."""
    return Procedure(
        procedure_id="pin-round",
        title="Pinned Round",
        goal="Act on DO breaches.",
        run_by="pond_agent",
        steps=[
            Step(step_id="read", name="Read", kind=StepKind.QUERY),
            Step(step_id="aerate", name="Aerate", kind=StepKind.ACTION, handler="aerate"),
        ],
        separation_of_duties=(
            [SoDConstraint(distinct_steps=frozenset({"read", "aerate"}))] if with_sod else []
        ),
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


async def _run_to_suspend(db_engine: AsyncEngine, run_id: str) -> str:
    registry.register_handler("aquaculture", "aerate", _SpyHandler())
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        result = await run_procedure_persisted(
            session, _procedure(), _agent(), _executors(1), vertical="aquaculture", run_id=run_id
        )
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    assert result.run.governance_hash is not None, "the pin must be recorded at run start"
    proposals = (result.step_results[-1].artifact or {})["output_set"]
    return str(proposals[0]["action_id"])


async def test_mid_flight_governance_edit_refused_at_gate_and_resume(
    db_engine: AsyncEngine,
) -> None:
    """AC-8 fail-closed half: the edited config is refused at BOTH seams."""
    action_id = await _run_to_suspend(db_engine, "pin-1")
    edited = _procedure(with_sod=True)  # the between-suspend-and-resume edit
    maker = async_sessionmaker(db_engine, expire_on_commit=False)

    async with maker() as session:
        with pytest.raises(ProcedureError, match="pin mismatch"):
            await resolve_gated_step(
                session, "pin-1", "aerate", {action_id: "approve"}, procedure=edited
            )
    async with maker() as session:
        with pytest.raises(ProcedureError, match="pin mismatch"):
            await resume_run(
                session, edited, _agent(), _executors(0), "pin-1", vertical="aquaculture"
            )


async def test_unedited_config_resolves_and_resumes(db_engine: AsyncEngine) -> None:
    """AC-8 clean half: the pinned config proceeds normally end-to-end."""
    action_id = await _run_to_suspend(db_engine, "pin-2")
    procedure = _procedure()
    maker = async_sessionmaker(db_engine, expire_on_commit=False)

    async with maker() as session:
        await resolve_gated_step(
            session, "pin-2", "aerate", {action_id: "approve"}, procedure=procedure
        )
    async with maker() as fresh:
        resumed = await resume_run(
            fresh, procedure, _agent(), _executors(0), "pin-2", vertical="aquaculture"
        )
    assert resumed.run.status == PipelineRunStatus.COMPLETED.value


async def test_legacy_unpinned_run_skips_the_check(db_engine: AsyncEngine) -> None:
    """Backward compat: a pre-0008 row (no pin) resumes under any config."""
    action_id = await _run_to_suspend(db_engine, "pin-3")
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.text(
                "UPDATE pipeline_runs SET governance_hash = NULL, governance_snapshot = NULL "
                "WHERE run_id = 'pin-3'"
            )
        )
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        await resolve_gated_step(
            session, "pin-3", "aerate", {action_id: "approve"}, procedure=_procedure(with_sod=False)
        )
    async with maker() as fresh:
        resumed = await resume_run(
            fresh,
            _procedure(with_sod=False),
            _agent(),
            _executors(0),
            "pin-3",
            vertical="aquaculture",
        )
    assert resumed.run.status == PipelineRunStatus.COMPLETED.value


def test_pin_hash_is_deterministic_and_config_sensitive() -> None:
    """Equal configs hash identically (fresh objects); a governance change
    (SoD added) changes the hash; prose (title) does NOT."""
    snap_a, hash_a = governance_pin_for(_procedure())
    snap_b, hash_b = governance_pin_for(_procedure())
    assert snap_a == snap_b and hash_a == hash_b

    _, hash_sod = governance_pin_for(_procedure(with_sod=True))
    assert hash_sod != hash_a

    retitled = _procedure().model_copy(update={"title": "A different title"})
    _, hash_retitled = governance_pin_for(retitled)
    assert hash_retitled == hash_a, "prose edits must not trip the governance pin"
