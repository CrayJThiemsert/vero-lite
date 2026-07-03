"""PLAN-0047 Step 5 tests (AC-7) — the append-only, hash-chained audit log.

DB-backed (skips without Postgres). Proves:

* UPDATE / DELETE on a committed audit row fails AT THE DATABASE LAYER
  (the block trigger — installed by migration 0007; mirrored here on the
  create_all schema from the module's frozen DDL constants);
* every row hash-chains to its predecessor, and the verifier detects a
  tampered row even when the tamperer is strong enough to disable the
  trigger (the superuser path);
* the governed loop (run → gate decision → handler receipt → resume)
  emits its transitions into the chain, intact.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.db.audit_log import (
    AUDIT_BLOCK_FUNCTION_SQL,
    AUDIT_BLOCK_TRIGGER_SQL,
    GENESIS_HASH,
    AuditLog,
    append_audit,
    verify_chain,
)
from services.db.base import Base
from services.engine.llm.client import ChatResult
from services.engine.procedures.action_step import ActionStepExecutor, resolve_gated_step
from services.engine.procedures.orchestrator import RunContext, StepExecutor, StepOutcome
from services.engine.procedures.persistence import resume_run, run_procedure_persisted
from services.engine.procedures.runs import PipelineRunStatus
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    Procedure,
    Step,
    StepKind,
)
from services.engine.registry import registry
from tests.db_support import create_test_engine


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # create_all builds tables only — install the migration-0007 guard from
        # the module's frozen DDL so AC-7 exercises the REAL trigger.
        await conn.execute(sa.text(AUDIT_BLOCK_FUNCTION_SQL))
        await conn.execute(sa.text(AUDIT_BLOCK_TRIGGER_SQL))
    yield eng
    async with eng.begin() as conn:
        await conn.execute(sa.text("DROP TRIGGER IF EXISTS audit_log_no_mutation ON audit_log"))
        await conn.execute(sa.text("DROP FUNCTION IF EXISTS audit_log_block_mutation()"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


async def _append(engine: AsyncEngine, action: str, **kwargs: Any) -> None:
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        await append_audit(session, action=action, **kwargs)
        await session.commit()


async def test_chain_links_and_verifies(db_engine: AsyncEngine) -> None:
    await _append(db_engine, "run_started", run_id="al-1")
    await _append(db_engine, "gate_decision", run_id="al-1", step_id="approve")
    await _append(db_engine, "handler_receipt", run_id="al-1", payload={"receipt": {"ok": True}})

    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        rows = (
            (await session.execute(sa.select(AuditLog).order_by(AuditLog.audit_id))).scalars().all()
        )
        assert [r.action for r in rows] == ["run_started", "gate_decision", "handler_receipt"]
        assert rows[0].prev_hash == GENESIS_HASH
        assert rows[1].prev_hash == rows[0].row_hash
        assert rows[2].prev_hash == rows[1].row_hash
        assert await verify_chain(session) == []


async def test_update_and_delete_blocked_at_database_layer(db_engine: AsyncEngine) -> None:
    """AC-7 rejection half: mutation dies in the DATABASE, not in app code."""
    await _append(db_engine, "run_started", run_id="al-2")
    maker = async_sessionmaker(db_engine, expire_on_commit=False)

    async with maker() as session:
        with pytest.raises(DBAPIError, match="append-only"):
            await session.execute(sa.text("UPDATE audit_log SET action = 'forged'"))
    async with maker() as session:
        with pytest.raises(DBAPIError, match="append-only"):
            await session.execute(sa.text("DELETE FROM audit_log"))

    async with maker() as fresh:
        row = (await fresh.execute(sa.select(AuditLog))).scalars().one()
        assert row.action == "run_started", "the committed row survives both attempts"


async def test_tampered_row_detected_by_chain_verifier(db_engine: AsyncEngine) -> None:
    """AC-7 tamper half: an actor strong enough to DISABLE the trigger (the
    dev superuser path) still cannot mutate silently — the chain catches it."""
    await _append(db_engine, "run_started", run_id="al-3")
    await _append(db_engine, "gate_decision", run_id="al-3", step_id="approve")

    async with db_engine.begin() as conn:
        await conn.execute(sa.text("ALTER TABLE audit_log DISABLE TRIGGER audit_log_no_mutation"))
        await conn.execute(
            sa.text("UPDATE audit_log SET action = 'forged' WHERE action = 'gate_decision'")
        )
        await conn.execute(sa.text("ALTER TABLE audit_log ENABLE TRIGGER audit_log_no_mutation"))

    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        breaks = await verify_chain(session)
    assert breaks and "mutated" in breaks[0]


# --- the governed loop emits its transitions into the chain ------------------


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


async def test_governed_loop_emits_chained_audit_trail(db_engine: AsyncEngine) -> None:
    registry.register_handler("aquaculture", "aerate", _SpyHandler())
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    procedure = Procedure(
        procedure_id="al-round",
        title="Round",
        goal="Act on DO breaches.",
        run_by="pond_agent",
        steps=[
            Step(step_id="read", name="Read", kind=StepKind.QUERY),
            Step(step_id="aerate", name="Aerate", kind=StepKind.ACTION, handler="aerate"),
        ],
    )
    agent = Agent(
        agent_id="pond_agent",
        name="Pond Agent",
        autonomy_ceiling=Autonomy.GATED,
        allowed=AgentAllowed(action_handlers=["aerate"]),
    )

    async with maker() as session:
        result = await run_procedure_persisted(
            session, procedure, agent, _executors(1), vertical="aquaculture", run_id="al-run"
        )
    proposals = (result.step_results[-1].artifact or {})["output_set"]
    action_id = str(proposals[0]["action_id"])

    async with maker() as session:
        await resolve_gated_step(session, "al-run", "aerate", {action_id: "approve"})
    async with maker() as fresh:
        resumed = await resume_run(
            fresh, procedure, agent, _executors(0), "al-run", vertical="aquaculture"
        )
    assert resumed.run.status == PipelineRunStatus.COMPLETED.value

    async with maker() as session:
        actions = (
            (
                await session.execute(
                    sa.select(AuditLog.action)
                    .where(AuditLog.run_id == "al-run")
                    .order_by(AuditLog.audit_id)
                )
            )
            .scalars()
            .all()
        )
        assert list(actions) == [
            "run_started",
            "gate_decision",
            "handler_receipt",
            "run_resumed",
        ]
        assert await verify_chain(session) == []
