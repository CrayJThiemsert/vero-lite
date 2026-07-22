"""AC-3 (PLAN-0090) — the fleet AT-3 calm path fires itself on a clock and PARKS for a human.

The demo beat this proves: **nobody pushed a button, and nothing was decided without a person.**
The run fires as the declared `svc-fleet-scheduler` service principal on behalf of the head
mechanic, reads every truck's odometer, bands each against THAT truck's own service-due point,
and then stops at the gated `schedule_service` — because RF-3 keeps the approver seam typed
`Person`, so a service actor cannot resolve its own go/no-go by construction.

Mirrors the procurement donor (`test_scheduled_procurement_demo.py`, PLAN-0065) deliberately:
this is the SECOND scheduled AT-3 instance, and the value of a second instance is largely that
it exercises the same shipped machinery from a different vertical.

DB-marked: needs Postgres. A ~141-skip run means the DB is not connected (dev Postgres is on
host port 5442, and a worktree ships no `.env`) — that is not a pass.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from services.db.audit_log import AuditLog
from services.db.base import Base
from services.engine.procedures.persistence import load_run, suspended_step_result
from services.engine.procedures.runs import PipelineRunStatus
from services.engine.procedures.scheduler import FireResult, fire_due_schedules
from services.engine.procedures.scheduler_wiring import (
    build_resolver,
    schedule_id_for,
    sync_schedule_states,
)
from services.engine.procedures.schedules import ScheduleState
from services.engine.procedures.spec import Trigger, load_procedures
from services.engine.registry import registry
from tests.db_support import create_test_engine

_VERTICAL = "fleet_maintenance"
_PROC_ID = "scheduled_pm_service_round"
_GATED_STEP = "schedule_service"
_SP_ID = "svc-fleet-scheduler"
_OWNER = "req-mechanic-tom"

BKK = ZoneInfo("Asia/Bangkok")
EPOCH = datetime(2026, 7, 1, 0, 0, tzinfo=UTC)
# The L1 06:00 slot, and an observation just past it (the daemon's `now`).
SLOT = datetime(2026, 7, 7, 6, 0, tzinfo=BKK)
NOW = datetime(2026, 7, 7, 6, 30, tzinfo=BKK)


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


@pytest.fixture
async def fleet_registered() -> AsyncIterator[None]:
    """Register EXACTLY what the scheduler daemon registers — ``discover_and_register``
    (adapters + action handlers) AND the procedure-executor factory — so this exercises the same
    registration path ``cli._run_scheduler`` uses.

    Registering handlers explicitly instead would MASK the very class of bug PLAN-0090 fixes:
    the daemon's factory dispatch was procurement-hardcoded, so fleet raised ``RegistryError`` at
    startup. Going through the real pair is what makes this test speak to the live daemon.
    """
    from services.engine.discovery import discover_and_register
    from verticals.fleet_maintenance.procedures_factory import (
        register_fleet_maintenance_procedure_executors,
    )

    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    yield


async def _audit_rows(session: AsyncSession, action: str, run_id: str) -> list[AuditLog]:
    rows = await session.execute(
        sa.select(AuditLog).where(AuditLog.action == action, AuditLog.run_id == run_id)
    )
    return list(rows.scalars().all())


async def _sync_and_arm(session: AsyncSession) -> ScheduleState:
    """Register the vertical's schedules, then arm the slot as DUE."""
    spec = load_procedures(_VERTICAL)
    rows = await sync_schedule_states(session, spec, now=EPOCH)
    # sync creates a ScheduleState only for `schedule`-trigger procedures: fleet ships exactly
    # ONE, and the two manual procedures are skipped. That asymmetry is the distinct-procedure_id
    # decision paying off — a trigger flip would have made the manual path un-runnable instead.
    assert [r.procedure_id for r in rows] == [_PROC_ID]
    state = rows[0]
    assert state.schedule_id == schedule_id_for(_VERTICAL, _PROC_ID)
    assert state.next_fire is None  # fresh registration — the daemon's first tick initializes it
    state.next_fire = SLOT
    await session.commit()
    return state


async def test_scheduled_fleet_calm_path_fires_and_parks_at_the_service_gate(
    session: AsyncSession, fleet_registered: None
) -> None:
    """The whole AC-3 claim in one run: fires headless, bands per truck, stops for a human."""
    spec = load_procedures(_VERTICAL)
    resolve = build_resolver(spec, registry.get_procedure_executors(_VERTICAL))
    state = await _sync_and_arm(session)

    [outcome] = await fire_due_schedules(session, [state], now=NOW, resolve=resolve)

    assert outcome.result is FireResult.FIRED
    assert outcome.run_status == PipelineRunStatus.WAITING_HUMAN.value

    loaded = await load_run(session, outcome.run_id)
    assert loaded is not None
    suspended = suspended_step_result(loaded.step_results)  # by STATUS, never by position
    assert suspended is not None
    assert suspended.step_id == _GATED_STEP

    # Fired as the service principal, on behalf of the accountable human (L2 / PLAN-0065 SD-5(b)).
    [started] = await _audit_rows(session, "run_started", outcome.run_id)
    assert started.actor_service_principal_id == _SP_ID
    assert started.payload is not None
    assert started.payload["actor_kind"] == "service"
    assert started.payload["on_behalf_of"]["service_principal_id"] == _SP_ID
    assert started.payload["on_behalf_of"]["owning_person_id"] == _OWNER

    # AT-3: the owning person is an accountability principal, NOT an SoD requester — nothing
    # consumes it as a role, so no requester principal is recorded.
    assert not (loaded.run.step_principals or {}).get("intake")

    # Per-truck banding against each truck's OWN next_service_due_km (ADR-016 TF-1), direction
    # `above`: one of the three synthetic trucks is past its service point.
    judge_sr = next(sr for sr in loaded.step_results if sr.step_id == "judge_service_due")
    assert judge_sr.artifact is not None
    assert sorted(e["verdict"] for e in judge_sr.artifact["output_set"]) == ["breach", "ok", "ok"]

    # SD-P6: the trigger_context stamp rides on the persisted run — the clock is auditable.
    tc = loaded.run.trigger_context
    assert tc is not None
    assert tc["trigger"] == Trigger.SCHEDULE.value
    assert tc["cron"] == "0 6 * * *"
    assert tc["actor"] == _SP_ID


async def test_scheduled_fleet_run_carries_no_at2_apparatus(
    session: AsyncSession, fleet_registered: None
) -> None:
    """Hard rule 3: putting the calm path on a clock must not smuggle in governance.

    The gate advisory is absent BY CONSTRUCTION, not by never-raising — ``GovernanceActionExecutor``
    branches on ``step.governance_content`` and only ``_doa_tier`` invokes the advisory builder.
    This asserts the *observable* consequence so the construction argument stays honest.
    """
    spec = load_procedures(_VERTICAL)
    resolve = build_resolver(spec, registry.get_procedure_executors(_VERTICAL))
    state = await _sync_and_arm(session)

    [outcome] = await fire_due_schedules(session, [state], now=NOW, resolve=resolve)
    loaded = await load_run(session, outcome.run_id)
    assert loaded is not None

    gate_sr = next(sr for sr in loaded.step_results if sr.step_id == _GATED_STEP)
    trace_kinds = {entry.get("kind") for entry in (gate_sr.reasoning_trace or [])}
    assert "advisory_recommendation" not in trace_kinds
    assert "doa_tier_resolved" not in trace_kinds
    assert "governed_kind" not in (gate_sr.audit or {})
