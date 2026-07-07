"""PLAN-0055 Step 4 (ADR-0028) — the pure "fire due schedules" function.

DB-backed (disposable ``<db>_test``, skips without Postgres). Uses the REAL
``cron.next_fire`` (croniter, Step 3) with an INJECTED ``now`` — deterministic, no daemon.
Covers AC-6 (due/not-due/init + advance), AC-4 (service-actor audit), AC-5 (gated-park),
AC-9 (trigger_context stamp), SD-P3 (skip-if-in-flight), SD-P2/AC-8 (missed-round audit).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from services.db.audit_log import AuditLog
from services.db.base import Base
from services.engine.procedures.orchestrator import RunContext, StepExecutor, StepOutcome
from services.engine.procedures.runs import PipelineRun, PipelineRunStatus
from services.engine.procedures.scheduler import (
    FireResult,
    ScheduledRun,
    fire_due_schedules,
)
from services.engine.procedures.schedules import ScheduleState
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    Procedure,
    Schedule,
    ServicePrincipal,
    Step,
    StepKind,
    Trigger,
)
from tests.db_support import create_test_engine

CRON = "0 6 * * *"  # daily 06:00
TZ = "Asia/Bangkok"
BKK = ZoneInfo(TZ)
SP_ID = "svc-scheduler"
EPOCH = datetime(2026, 7, 1, 0, 0, tzinfo=UTC)


class _Exec:
    """Fixed-output executor (+ call counter)."""

    def __init__(self, output: list[Any]) -> None:
        self.output = output
        self.calls = 0

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        self.calls += 1
        return StepOutcome(output=self.output, reasoning_trace=[{"summary": step.step_id}])


def _executors() -> dict[StepKind, StepExecutor]:
    return {
        StepKind.QUERY: _Exec([{"pond": "p7"}]),
        StepKind.ACTION: _Exec([{"action": "aerate"}]),
    }


def _agent() -> Agent:
    return Agent(
        agent_id="pond_agent",
        name="Pond Agent",
        autonomy_ceiling=Autonomy.AUTO,
        allowed=AgentAllowed(action_handlers=["echo"]),
        service_principal_ids=[SP_ID],
    )


def _procedure(*, gated: bool) -> Procedure:
    """A schedule-trigger procedure (Step-2 invariant requires the descriptor). ``gated``
    makes the action step park at ``waiting_human``; otherwise it runs auto to completion."""
    action = (
        Step(step_id="aerate", name="Aerate", kind=StepKind.ACTION, handler="echo")
        if gated
        else Step(
            step_id="aerate",
            name="Aerate",
            kind=StepKind.ACTION,
            autonomy=Autonomy.AUTO,
            handler="echo",
        )
    )
    return Procedure(
        procedure_id="morning_round",
        title="Morning Round",
        run_by="pond_agent",
        trigger=Trigger.SCHEDULE,
        schedule=Schedule(cron=CRON, timezone=TZ),
        steps=[Step(step_id="read", name="Read", kind=StepKind.QUERY), action],
    )


def _scheduled_run(*, gated: bool = False) -> ScheduledRun:
    return ScheduledRun(
        procedure=_procedure(gated=gated),
        agent=_agent(),
        executors=_executors(),
        vertical="aquaculture",
        service_principal=ServicePrincipal(service_principal_id=SP_ID, name="Scheduler"),
    )


def _resolver(sr: ScheduledRun) -> Any:
    def resolve(state: ScheduleState) -> ScheduledRun:
        return sr

    return resolve


def _state(*, next_fire: datetime | None, schedule_id: str = "aqua:morning") -> ScheduleState:
    return ScheduleState(
        schedule_id=schedule_id,
        vertical="aquaculture",
        procedure_id="morning_round",
        cron=CRON,
        timezone=TZ,
        last_fired=None,
        next_fire=next_fire,
        created_at=EPOCH,
        updated_at=EPOCH,
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


@pytest.fixture
async def session(db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as s:
        yield s


async def _audit_rows(session: AsyncSession, action: str) -> list[AuditLog]:
    rows = await session.execute(sa.select(AuditLog).where(AuditLog.action == action))
    return list(rows.scalars().all())


async def test_due_schedule_fires_and_advances(session: AsyncSession) -> None:
    """AC-6: a due schedule fires a completed run + advances next_fire to a future slot."""
    now = datetime(2026, 7, 7, 6, 30, tzinfo=BKK)  # just past the 06:00 slot
    state = _state(next_fire=datetime(2026, 7, 7, 6, 0, tzinfo=BKK))
    session.add(state)
    await session.commit()

    [outcome] = await fire_due_schedules(
        session, [state], now=now, resolve=_resolver(_scheduled_run())
    )
    assert outcome.result is FireResult.FIRED
    assert outcome.missed is False
    assert outcome.run_status == PipelineRunStatus.COMPLETED.value

    run = await session.get(PipelineRun, outcome.run_id)
    assert run is not None and run.status == PipelineRunStatus.COMPLETED.value
    assert state.last_fired == now
    assert state.next_fire is not None and state.next_fire > now  # advanced to the future


async def test_not_due_schedule_does_not_fire(session: AsyncSession) -> None:
    """AC-6: a schedule whose next_fire is in the future is left untouched."""
    now = datetime(2026, 7, 7, 6, 30, tzinfo=BKK)
    future = datetime(2026, 7, 8, 6, 0, tzinfo=BKK)
    state = _state(next_fire=future)
    session.add(state)
    await session.commit()

    [outcome] = await fire_due_schedules(
        session, [state], now=now, resolve=_resolver(_scheduled_run())
    )
    assert outcome.result is FireResult.NOT_DUE
    assert state.next_fire == future and state.last_fired is None
    assert (
        await session.execute(sa.select(sa.func.count()).select_from(PipelineRun))
    ).scalar() == 0


async def test_uninitialized_schedule_initializes_without_firing(session: AsyncSession) -> None:
    """AC-6: a freshly-registered schedule (next_fire None) gets a first next_fire, no run."""
    now = datetime(2026, 7, 7, 10, 0, tzinfo=BKK)
    state = _state(next_fire=None)
    session.add(state)
    await session.commit()

    [outcome] = await fire_due_schedules(
        session, [state], now=now, resolve=_resolver(_scheduled_run())
    )
    assert outcome.result is FireResult.INITIALIZED
    assert state.next_fire == datetime(2026, 7, 8, 6, 0, tzinfo=BKK)  # next 06:00 after 10:00
    assert state.last_fired is None
    assert (
        await session.execute(sa.select(sa.func.count()).select_from(PipelineRun))
    ).scalar() == 0


async def test_fired_run_binds_service_principal_actor(session: AsyncSession) -> None:
    """AC-4: the run_started audit carries actor_kind:service + the SP id + on_behalf_of."""
    now = datetime(2026, 7, 7, 6, 30, tzinfo=BKK)
    state = _state(next_fire=datetime(2026, 7, 7, 6, 0, tzinfo=BKK))
    session.add(state)
    await session.commit()

    [outcome] = await fire_due_schedules(
        session, [state], now=now, resolve=_resolver(_scheduled_run())
    )
    started = [r for r in await _audit_rows(session, "run_started") if r.run_id == outcome.run_id]
    assert len(started) == 1
    row = started[0]
    assert row.actor_service_principal_id == SP_ID
    assert row.payload is not None
    assert row.payload["actor_kind"] == "service"
    assert row.payload["on_behalf_of"]["service_principal_id"] == SP_ID


async def test_gated_scheduled_run_parks_at_waiting_human(session: AsyncSession) -> None:
    """AC-5: a scheduled run reaching a gated step parks — the service actor never approves."""
    now = datetime(2026, 7, 7, 6, 30, tzinfo=BKK)
    state = _state(next_fire=datetime(2026, 7, 7, 6, 0, tzinfo=BKK))
    session.add(state)
    await session.commit()

    [outcome] = await fire_due_schedules(
        session, [state], now=now, resolve=_resolver(_scheduled_run(gated=True))
    )
    assert outcome.result is FireResult.FIRED
    assert outcome.run_status == PipelineRunStatus.WAITING_HUMAN.value
    run = await session.get(PipelineRun, outcome.run_id)
    assert run is not None and run.status == PipelineRunStatus.WAITING_HUMAN.value


async def test_trigger_context_is_stamped(session: AsyncSession) -> None:
    """AC-9: the SD-P6 trigger_context rides on the persisted run."""
    now = datetime(2026, 7, 7, 6, 30, tzinfo=BKK)
    scheduled_for = datetime(2026, 7, 7, 6, 0, tzinfo=BKK)
    state = _state(next_fire=scheduled_for)
    session.add(state)
    await session.commit()

    [outcome] = await fire_due_schedules(
        session, [state], now=now, resolve=_resolver(_scheduled_run())
    )
    run = await session.get(PipelineRun, outcome.run_id)
    assert run is not None and run.trigger_context is not None
    tc = run.trigger_context
    assert tc["trigger"] == Trigger.SCHEDULE.value
    assert tc["cron"] == CRON
    assert tc["timezone"] == TZ
    assert tc["scheduled_for"] == scheduled_for.isoformat()
    assert tc["fired_at"] == now.isoformat()
    assert tc["actor"] == SP_ID


async def test_skip_if_in_flight(session: AsyncSession) -> None:
    """SD-P3: a schedule whose procedure already has a parked run is skipped (audited), and
    its clock advances — no second concurrent run is started for the due slot."""
    now = datetime(2026, 7, 7, 6, 30, tzinfo=BKK)
    scheduled_for = datetime(2026, 7, 7, 6, 0, tzinfo=BKK)
    # a prior run of the SAME procedure, still parked at a gate.
    session.add(
        PipelineRun(
            run_id="prior-parked",
            procedure_id="morning_round",
            agent_id="pond_agent",
            status=PipelineRunStatus.WAITING_HUMAN.value,
            started_at=EPOCH,
            updated_at=EPOCH,
        )
    )
    state = _state(next_fire=scheduled_for)
    session.add(state)
    await session.commit()

    [outcome] = await fire_due_schedules(
        session, [state], now=now, resolve=_resolver(_scheduled_run())
    )
    assert outcome.result is FireResult.SKIPPED_IN_FLIGHT
    assert state.next_fire is not None and state.next_fire > now  # advanced, no spin
    assert state.last_fired is None
    # no NEW run created for this slot (only the pre-existing parked run exists).
    slot_run_id = f"aqua:morning@{scheduled_for.isoformat()}"
    assert await session.get(PipelineRun, slot_run_id) is None
    skipped = await _audit_rows(session, "schedule_skipped")
    assert len(skipped) == 1
    assert skipped[0].payload is not None and skipped[0].payload["reason"] == "in_flight"


async def test_missed_round_is_audited_and_fires_once(session: AsyncSession) -> None:
    """SD-P2 / AC-8: after downtime the due slot fires once (SD-P4 at-most-once), the elapsed
    intermediate slots are skipped (not backfilled), and a schedule_missed row records the gap."""
    now = datetime(2026, 7, 7, 6, 30, tzinfo=BKK)
    scheduled_for = datetime(2026, 7, 4, 6, 0, tzinfo=BKK)  # 3 days stale (2 slots skipped)
    state = _state(next_fire=scheduled_for)
    session.add(state)
    await session.commit()

    outcomes = await fire_due_schedules(
        session, [state], now=now, resolve=_resolver(_scheduled_run())
    )
    [outcome] = outcomes
    assert outcome.result is FireResult.FIRED
    assert outcome.missed is True
    # fired exactly ONCE (at-most-once) — a single run row.
    assert (
        await session.execute(sa.select(sa.func.count()).select_from(PipelineRun))
    ).scalar() == 1
    # advanced to the next FUTURE slot (no backfill of the elapsed days).
    assert state.next_fire == datetime(2026, 7, 8, 6, 0, tzinfo=BKK)
    missed = await _audit_rows(session, "schedule_missed")
    assert len(missed) == 1
    assert missed[0].payload is not None and missed[0].payload["policy"] == "skip_no_backfill"
