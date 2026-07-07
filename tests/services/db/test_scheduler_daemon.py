"""PLAN-0055 Step 5 (ADR-0028 SD-1) — the scheduler daemon scaffold (AC-11).

DB-backed (disposable ``<db>_test``, skips without Postgres). Proves the daemon's entrypoint
+ run loop + graceful stop + structured logging: a tick fires a due schedule, ``run()`` loops
then exits cleanly on a stop request (the start→tick→shutdown smoke), a raising tick is
swallowed (the loop survives), and the default loader returns the persisted schedule set.
The loop is bounded DETERMINISTICALLY (a loader that requests stop) — no wall-clock sleeps.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest
import sqlalchemy as sa
import structlog
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from services.db.base import Base
from services.engine.procedures.orchestrator import RunContext, StepOutcome
from services.engine.procedures.runs import PipelineRun
from services.engine.procedures.scheduler import ScheduledRun
from services.engine.procedures.scheduler_daemon import (
    SchedulerDaemon,
    load_all_schedules,
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

CRON = "0 6 * * *"
TZ = "Asia/Bangkok"
BKK = ZoneInfo(TZ)
SP_ID = "svc-scheduler"
EPOCH = datetime(2026, 7, 1, 0, 0, tzinfo=UTC)
NOW = datetime(2026, 7, 7, 6, 30, tzinfo=BKK)  # just past the daily 06:00 slot


class _Exec:
    def __init__(self, output: list[Any]) -> None:
        self.output = output

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(output=self.output, reasoning_trace=[{"summary": step.step_id}])


def _scheduled_run() -> ScheduledRun:
    procedure = Procedure(
        procedure_id="morning_round",
        title="Morning Round",
        run_by="pond_agent",
        trigger=Trigger.SCHEDULE,
        schedule=Schedule(cron=CRON, timezone=TZ),
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
    agent = Agent(
        agent_id="pond_agent",
        name="Pond Agent",
        autonomy_ceiling=Autonomy.AUTO,
        allowed=AgentAllowed(action_handlers=["echo"]),
        service_principal_ids=[SP_ID],
    )
    return ScheduledRun(
        procedure=procedure,
        agent=agent,
        executors={StepKind.QUERY: _Exec([{"p": 1}]), StepKind.ACTION: _Exec([{"a": 1}])},
        vertical="aquaculture",
        service_principal=ServicePrincipal(service_principal_id=SP_ID, name="Scheduler"),
    )


def _resolver() -> Any:
    sr = _scheduled_run()
    return lambda state: sr


def _due_state(
    schedule_id: str = "aqua:morning", procedure_id: str = "morning_round"
) -> ScheduleState:
    return ScheduleState(
        schedule_id=schedule_id,
        vertical="aquaculture",
        procedure_id=procedure_id,
        cron=CRON,
        timezone=TZ,
        next_fire=datetime(2026, 7, 7, 6, 0, tzinfo=BKK),
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


async def _seed(maker: async_sessionmaker[AsyncSession], *states: ScheduleState) -> None:
    async with maker() as s:
        for st in states:
            s.add(st)
        await s.commit()


async def test_tick_fires_due_schedule(db_engine: AsyncEngine) -> None:
    """AC-11: one tick loads the schedule set + fires the due one via the pure function."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    await _seed(maker, _due_state())
    daemon = SchedulerDaemon(
        session_factory=maker, resolve=_resolver(), clock=lambda: NOW, interval_seconds=0.01
    )
    with structlog.testing.capture_logs() as logs:
        outcomes = await daemon.tick()
    assert [o.result.value for o in outcomes] == ["fired"]
    events = [entry["event"] for entry in logs]
    assert "scheduler.tick" in events
    assert "scheduler.fired" in events
    # the run was persisted (committed inside the tick's session)
    async with maker() as s:
        n = (await s.execute(sa.select(sa.func.count()).select_from(PipelineRun))).scalar()
    assert n == 1


async def test_run_loops_then_stops_gracefully(db_engine: AsyncEngine) -> None:
    """AC-11 smoke: run() starts, does a firing tick, then exits cleanly on a stop request."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    await _seed(maker, _due_state())
    ref: list[SchedulerDaemon] = []
    calls = {"n": 0}

    async def loader(session: AsyncSession) -> list[ScheduleState]:
        calls["n"] += 1
        if calls["n"] == 1:
            return list(await load_all_schedules(session))  # tick 1: fire the due schedule
        ref[0].request_stop()  # tick 2: ask the loop to exit
        return []

    daemon = SchedulerDaemon(
        session_factory=maker,
        load_schedules=loader,
        resolve=_resolver(),
        clock=lambda: NOW,
        interval_seconds=0.01,
    )
    ref.append(daemon)
    with structlog.testing.capture_logs() as logs:
        await asyncio.wait_for(daemon.run(), timeout=5.0)
    events = [entry["event"] for entry in logs]
    assert events[0] == "scheduler.start"
    assert "scheduler.fired" in events  # tick 1 fired
    assert events[-1] == "scheduler.stop"  # graceful exit
    assert calls["n"] >= 2


async def test_tick_failure_does_not_kill_the_loop(db_engine: AsyncEngine) -> None:
    """A raising tick is logged (scheduler.tick_failed) and swallowed — the loop survives."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    ref: list[SchedulerDaemon] = []
    calls = {"n": 0}

    async def loader(session: AsyncSession) -> list[ScheduleState]:
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("transient DB blip")
        ref[0].request_stop()
        return []

    daemon = SchedulerDaemon(
        session_factory=maker,
        load_schedules=loader,
        resolve=_resolver(),
        clock=lambda: NOW,
        interval_seconds=0.01,
    )
    ref.append(daemon)
    with structlog.testing.capture_logs() as logs:
        await asyncio.wait_for(daemon.run(), timeout=5.0)  # must NOT raise
    events = [entry["event"] for entry in logs]
    assert "scheduler.tick_failed" in events
    assert events[-1] == "scheduler.stop"
    assert calls["n"] >= 2  # survived tick 1's failure and ticked again


async def test_load_all_schedules_returns_persisted_set(db_engine: AsyncEngine) -> None:
    """The default loader returns every persisted schedule, ordered by schedule_id."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    # distinct procedure_ids — (vertical, procedure_id) is unique (Step-2 constraint).
    await _seed(maker, _due_state("aqua:b", "round_b"), _due_state("aqua:a", "round_a"))
    async with maker() as s:
        loaded = await load_all_schedules(s)
    assert [st.schedule_id for st in loaded] == ["aqua:a", "aqua:b"]


async def test_request_stop_before_run_exits_after_zero_or_more_ticks(
    db_engine: AsyncEngine,
) -> None:
    """request_stop() honoured — a daemon stopped up front exits its loop promptly."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)

    async def empty_loader(session: AsyncSession) -> list[ScheduleState]:
        return []

    daemon = SchedulerDaemon(
        session_factory=maker,
        load_schedules=empty_loader,
        resolve=_resolver(),
        clock=lambda: NOW,
        interval_seconds=0.01,
    )
    daemon.request_stop()
    with structlog.testing.capture_logs() as logs:
        await asyncio.wait_for(daemon.run(), timeout=5.0)
    events = [entry["event"] for entry in logs]
    assert events[0] == "scheduler.start"
    assert events[-1] == "scheduler.stop"
