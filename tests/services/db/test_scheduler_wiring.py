"""PLAN-0055 Step 7b (ADR-0028) — deploy-time scheduler wiring.

Covers the two wiring seams the ``vero-lite scheduler`` CLI composes:
* ``sync_schedule_states`` (DB-backed) — the registration step: spec -> schedule_states rows,
  idempotent, spec-owns-cron / daemon-owns-clock.
* ``build_resolver`` (pure) — the real ScheduleState -> ScheduledRun assembly + the
  service-principal lookup, and its fail-loud misconfiguration guards.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from services.db.base import Base
from services.engine.cli import app
from services.engine.procedures.orchestrator import StepExecutor
from services.engine.procedures.scheduler_wiring import (
    SchedulerWiringError,
    build_resolver,
    schedule_id_for,
    schedule_procedures,
    sync_schedule_states,
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
    VerticalProcedures,
)
from tests.db_support import create_test_engine

TZ = "Asia/Bangkok"
BKK = ZoneInfo(TZ)
EPOCH = datetime(2026, 7, 1, 0, 0, tzinfo=UTC)
LATER = datetime(2026, 7, 2, 0, 0, tzinfo=UTC)
SID = "procurement:reorder_round"


def _spec(*, cron: str = "0 6 * * *", sp_ids: list[str] | None = None) -> VerticalProcedures:
    """A procurement-shaped spec: one schedule-trigger procedure + one manual (must be skipped),
    an agent bound to a service principal, and that principal declared."""
    sched = Procedure(
        procedure_id="reorder_round",
        title="Reorder Round",
        run_by="buyer_agent",
        trigger=Trigger.SCHEDULE,
        schedule=Schedule(cron=cron, timezone=TZ),
        steps=[Step(step_id="read", name="Read", kind=StepKind.QUERY)],
    )
    manual = Procedure(
        procedure_id="manual_thing",
        title="Manual Thing",
        run_by="buyer_agent",
        trigger=Trigger.MANUAL,
        steps=[Step(step_id="read", name="Read", kind=StepKind.QUERY)],
    )
    agent = Agent(
        agent_id="buyer_agent",
        name="Auto Buyer",
        autonomy_ceiling=Autonomy.AUTO,
        allowed=AgentAllowed(action_handlers=["echo"]),
        service_principal_ids=["svc-buyer"] if sp_ids is None else sp_ids,
    )
    return VerticalProcedures(
        vertical="procurement",
        agents=[agent],
        procedures=[sched, manual],
        service_principals=[ServicePrincipal(service_principal_id="svc-buyer", name="Auto Buyer")],
    )


def _state(procedure_id: str = "reorder_round", schedule_id: str = SID) -> ScheduleState:
    return ScheduleState(
        schedule_id=schedule_id,
        vertical="procurement",
        procedure_id=procedure_id,
        cron="0 6 * * *",
        timezone=TZ,
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


# --- pure helpers --------------------------------------------------------------------------


def test_schedule_id_for_is_vertical_scoped() -> None:
    assert schedule_id_for("procurement", "reorder_round") == SID


def test_schedule_procedures_selects_only_schedule_trigger() -> None:
    procs = schedule_procedures(_spec())
    assert [p.procedure_id for p in procs] == ["reorder_round"]  # manual excluded


# --- sync_schedule_states (registration) ---------------------------------------------------


async def test_sync_creates_rows_for_schedule_procedures_only(session: AsyncSession) -> None:
    rows = await sync_schedule_states(session, _spec(), now=EPOCH)
    assert [r.schedule_id for r in rows] == [SID]  # the manual proc has no row
    r = rows[0]
    assert (r.vertical, r.procedure_id, r.cron, r.timezone) == (
        "procurement",
        "reorder_round",
        "0 6 * * *",
        TZ,
    )
    # a fresh schedule is INITIALIZED on the first tick (no fire) — next_fire starts None.
    assert r.next_fire is None and r.last_fired is None
    assert await session.get(ScheduleState, SID) is not None


async def test_sync_is_idempotent_and_preserves_the_live_clock(session: AsyncSession) -> None:
    await sync_schedule_states(session, _spec(), now=EPOCH)
    # the daemon advanced the clock between syncs.
    row = await session.get(ScheduleState, SID)
    assert row is not None
    row.next_fire = datetime(2026, 7, 8, 6, 0, tzinfo=BKK)
    row.last_fired = datetime(2026, 7, 7, 6, 0, tzinfo=BKK)
    await session.commit()

    rows = await sync_schedule_states(session, _spec(), now=LATER)  # same spec
    assert len(rows) == 1
    row2 = await session.get(ScheduleState, SID)
    assert row2 is not None
    assert row2.next_fire == datetime(2026, 7, 8, 6, 0, tzinfo=BKK)  # clock preserved
    assert row2.last_fired == datetime(2026, 7, 7, 6, 0, tzinfo=BKK)
    n = (await session.execute(sa.select(sa.func.count()).select_from(ScheduleState))).scalar()
    assert n == 1  # no duplicate


async def test_sync_cron_change_updates_and_resets_next_fire(session: AsyncSession) -> None:
    await sync_schedule_states(session, _spec(), now=EPOCH)
    row = await session.get(ScheduleState, SID)
    assert row is not None
    row.next_fire = datetime(2026, 7, 8, 6, 0, tzinfo=BKK)
    await session.commit()

    await sync_schedule_states(session, _spec(cron="0 12 * * *"), now=LATER)
    row2 = await session.get(ScheduleState, SID)
    assert row2 is not None
    assert row2.cron == "0 12 * * *"
    assert row2.next_fire is None  # dropped so the next tick recomputes against the new cron
    assert row2.updated_at == LATER


# --- build_resolver (the real ScheduleState -> ScheduledRun) --------------------------------


def test_build_resolver_produces_a_scheduled_run() -> None:
    spec = _spec()
    calls: list[int] = []

    def factory() -> dict[StepKind, StepExecutor]:
        calls.append(1)  # proves a FRESH executor map is built per fire
        return {}

    resolve = build_resolver(spec, factory)
    sr = resolve(_state())
    assert sr.procedure.procedure_id == "reorder_round"
    assert sr.agent.agent_id == "buyer_agent"
    assert sr.vertical == "procurement"
    assert sr.service_principal.service_principal_id == "svc-buyer"
    assert sr.owning_person is None  # headless schedule (S1)
    assert calls == [1]


def test_build_resolver_raises_on_missing_procedure() -> None:
    resolve = build_resolver(_spec(), lambda: {})
    with pytest.raises(SchedulerWiringError, match="no procedure 'ghost'"):
        resolve(_state(procedure_id="ghost", schedule_id="procurement:ghost"))


def test_build_resolver_raises_when_agent_has_no_service_principal() -> None:
    resolve = build_resolver(_spec(sp_ids=[]), lambda: {})
    with pytest.raises(SchedulerWiringError, match="service_principal_ids"):
        resolve(_state())


# --- CLI command registration --------------------------------------------------------------


def test_scheduler_cli_command_is_registered() -> None:
    names = {c.callback.__name__ for c in app.registered_commands if c.callback is not None}
    assert "scheduler" in names
