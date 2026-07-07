"""PLAN-0056 Step 5 (ADR-0029 SD-1 FEED-INTO / SD-4; SD-P4) — the in-process event fire fn.

DB-backed: an actionable event is FED INTO the governed engine — a REAL persisted PipelineRun
via run_procedure_persisted, NOT the lightweight ActionRecord path. Asserts the governed-engine
fire (AC-9), the service-actor audit (AC-7), the gated-park posture (AC-8), and the two skips
(SD-2 re-detect idempotency, SD-P4 skip-if-in-flight).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from services.db.audit_log import AuditLog
from services.db.base import Base
from services.engine.procedures.event_bridge import (
    EventFireResult,
    EventRunRequest,
    build_event_resolver,
    fire_event,
)
from services.engine.procedures.orchestrator import RunContext, StepExecutor, StepOutcome
from services.engine.procedures.runs import PipelineRun, PipelineRunStatus
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    EventTrigger,
    Person,
    Procedure,
    ServicePrincipal,
    Step,
    StepKind,
    Trigger,
    VerticalProcedures,
)
from tests.db_support import create_test_engine

SP_ID = "svc-buyer"
PROC_ID = "event_emergency_sourcing_round"
DETECTED = datetime(2026, 7, 7, 6, 0, tzinfo=UTC)
NOW = datetime(2026, 7, 7, 6, 30, tzinfo=UTC)


class _Exec:
    def __init__(self, output: list[Any]) -> None:
        self.output = output

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(output=self.output, reasoning_trace=[{"summary": step.step_id}])


def _executors() -> dict[StepKind, StepExecutor]:
    return {StepKind.QUERY: _Exec([{"asset": "pump-7"}]), StepKind.ACTION: _Exec([{"po": 1}])}


def _spec(*, gated: bool = False, owning: str | None = "req-planner") -> VerticalProcedures:
    action = (
        Step(step_id="source", name="Source", kind=StepKind.ACTION, handler="echo")
        if gated
        else Step(
            step_id="source",
            name="Source",
            kind=StepKind.ACTION,
            autonomy=Autonomy.AUTO,
            handler="echo",
        )
    )
    return VerticalProcedures(
        vertical="procurement",
        agents=[
            Agent(
                agent_id="buyer_agent",
                name="Buyer Agent",
                autonomy_ceiling=Autonomy.AUTO,
                allowed=AgentAllowed(action_handlers=["echo"]),
                service_principal_ids=[SP_ID],
            )
        ],
        service_principals=[ServicePrincipal(service_principal_id=SP_ID, name="Buyer Bot")],
        principals=[Person(person_id="req-planner", name="Req Planner", roles=frozenset({"req"}))],
        procedures=[
            Procedure(
                procedure_id=PROC_ID,
                title="Event Emergency Sourcing",
                run_by="buyer_agent",
                trigger=Trigger.EVENT,
                event_trigger=EventTrigger(event_kind="asset_failure", owning_person_id=owning),
                steps=[Step(step_id="read", name="Read", kind=StepKind.QUERY), action],
            )
        ],
    )


def _request(spec: VerticalProcedures, *, detected_at: datetime = DETECTED) -> EventRunRequest:
    resolver = build_event_resolver(spec, _executors)
    return resolver(event_kind="asset_failure", entity_ids=["pump-7"], detected_at=detected_at)


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


@pytest.fixture
async def session(db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as s:
        yield s


async def _audit_rows(session: AsyncSession, action: str) -> list[AuditLog]:
    rows = await session.execute(sa.select(AuditLog).where(AuditLog.action == action))
    return list(rows.scalars().all())


async def test_event_fires_a_governed_run(session: AsyncSession) -> None:
    # AC-9: an actionable event FEEDS INTO the governed engine — a REAL PipelineRun completes
    # (the ActionRecord path has no PipelineRun; a persisted completed run IS the proof).
    req = _request(_spec())
    outcome = await fire_event(session, req, now=NOW)
    assert outcome.result is EventFireResult.FIRED
    assert outcome.run_status == PipelineRunStatus.COMPLETED.value
    run = await session.get(PipelineRun, req.run_id)
    assert run is not None
    assert run.status == PipelineRunStatus.COMPLETED.value


async def test_fired_run_binds_service_principal_actor(session: AsyncSession) -> None:
    # AC-7: the run_started audit carries actor_kind:service + the SP-5 on-behalf-of lineage;
    # the run's trigger_context is the AC-9 event stamp (+ fired_at).
    req = _request(_spec())
    await fire_event(session, req, now=NOW)
    [row] = await _audit_rows(session, "run_started")
    pl = row.payload
    assert pl is not None
    assert pl["actor_kind"] == "service"
    assert pl["on_behalf_of"]["service_principal_id"] == SP_ID
    assert pl["on_behalf_of"]["owning_person_id"] == "req-planner"
    run = await session.get(PipelineRun, req.run_id)
    assert run is not None
    tc = run.trigger_context
    assert tc is not None
    assert tc["trigger"] == "event"
    assert tc["event_kind"] == "asset_failure"
    assert "fired_at" in tc


async def test_gated_event_run_parks_at_waiting_human(session: AsyncSession) -> None:
    # AC-8: a gated step parks — the service actor cannot approve (RF-3), inherited verbatim.
    outcome = await fire_event(session, _request(_spec(gated=True)), now=NOW)
    assert outcome.run_status == PipelineRunStatus.WAITING_HUMAN.value


async def test_re_detected_event_is_idempotent_noop(session: AsyncSession) -> None:
    # SD-2: the same event (same run_id) fired twice — the second is an ALREADY_FIRED no-op,
    # and only ONE governed run row exists (the write-ahead PK is the dedup).
    req = _request(_spec())
    await fire_event(session, req, now=NOW)
    again = _request(_spec())  # same key inputs => same run_id
    assert again.run_id == req.run_id
    outcome = await fire_event(session, again, now=NOW)
    assert outcome.result is EventFireResult.ALREADY_FIRED
    assert len(await _audit_rows(session, "event_skipped")) == 1
    rows = await session.execute(sa.select(PipelineRun).where(PipelineRun.procedure_id == PROC_ID))
    assert len(list(rows.scalars().all())) == 1


async def test_skip_if_in_flight(session: AsyncSession) -> None:
    # SD-P4: a gated run parks (waiting_human); a DISTINCT event-key for the same procedure is
    # skipped-in-flight (a gated run legitimately parks for days).
    parked = _request(_spec(gated=True))
    await fire_event(session, parked, now=NOW)  # parks at waiting_human
    later = _request(_spec(gated=True), detected_at=datetime(2026, 7, 8, 6, 0, tzinfo=UTC))
    assert later.run_id != parked.run_id
    outcome = await fire_event(session, later, now=datetime(2026, 7, 8, 6, 30, tzinfo=UTC))
    assert outcome.result is EventFireResult.SKIPPED_IN_FLIGHT
