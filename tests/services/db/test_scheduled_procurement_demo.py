"""PLAN-0055 Step 8 (ADR-0028 S1) — the procurement `schedule`-trigger integration demo.

The FIRST end-to-end wiring of the **REAL procurement spec** through the whole scheduler chain:
``load_procedures`` → ``sync_schedule_states`` → ``build_resolver`` → ``fire_due_schedules`` → a
persisted ``waiting_human`` run parked at the DOA gate → a **human** resolves it → ``COMPLETED``.

Unlike the Step-4/7b unit tests (synthetic in-memory specs), this drives the **SHIPPED**
procurement executor factory (``register_procurement_procedure_executors``) + the real
``scheduled_emergency_sourcing_round`` procedure, so it catches the integration gotchas the
in-memory tests could not:

* **Decimal→JSONB fresh-fire seed** — a daemon-fired run executes ``intake`` LIVE, so the factory's
  seed must be JSONB-safe (the Step-8 fix at ``run.py``; the HTTP resolve path never re-ran intake
  so it was latent). If the seed were raw ``Decimal`` the persisted ``intake`` output would fail the
  JSONB column and this test would error at fire time.
* **On-behalf-of SoD posture** — a ``doa_tier`` procedure REQUIRES a ``separation_of_duties``
  constraint (ADR-0025 D5), and SoD needs a human requester on ``intake``. A scheduled run fires as
  the service principal (the actor) but ON BEHALF OF the schedule's ``owning_person_id``
  (``req-planner``, SP-5), which the orchestrator records as the SoD requester — so a DISTINCT human
  DOA approver (``appr-pm``) satisfies SoD (requester ≠ approver) at gate resolution. A fully
  headless run (``owning_person=None``) would record ``{intake: None}`` and fail the principal-SoD
  run-check CLOSED. Proven here by resolving through to ``COMPLETED`` with a governed SoD tie.

DB-backed (disposable ``<db>_test``, skips without Postgres); **MS-S1-free** — the factory's
``advisory_stub_factory`` is deterministic (the scheduler is a clock, not a model caller,
CLAUDE.md §8).
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
from services.engine.procedures.action_step import resolve_gated_step
from services.engine.procedures.persistence import load_run, resume_run
from services.engine.procedures.runs import PipelineRun, PipelineRunStatus
from services.engine.procedures.scheduler import FireResult, fire_due_schedules
from services.engine.procedures.scheduler_wiring import build_resolver, schedule_id_for
from services.engine.procedures.schedules import ScheduleState
from services.engine.procedures.spec import Person, Trigger, load_procedures
from services.engine.registry import RegistryError, registry
from tests.db_support import create_test_engine

_VERTICAL = "procurement"
_PROC_ID = "scheduled_emergency_sourcing_round"
_GATED_STEP = "approve"
_SP_ID = "svc-buyer"
BKK = ZoneInfo("Asia/Bangkok")
EPOCH = datetime(2026, 7, 1, 0, 0, tzinfo=UTC)
# A due 06:00 slot + an observation just past it (the daemon's `now`).
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
async def procurement_registered() -> AsyncIterator[None]:
    """Register the procurement handlers + the deterministic procedure-executor factory (the
    autouse registry reset in tests/conftest.py wipes the registry per test)."""
    from verticals.procurement.handlers import register_procurement_handlers
    from verticals.procurement.hero_demo.run import register_procurement_procedure_executors

    try:
        register_procurement_handlers()
    except RegistryError:
        pass  # already registered (idempotent)
    await register_procurement_procedure_executors()
    yield


async def _audit_rows(session: AsyncSession, action: str, run_id: str) -> list[AuditLog]:
    rows = await session.execute(
        sa.select(AuditLog).where(AuditLog.action == action, AuditLog.run_id == run_id)
    )
    return list(rows.scalars().all())


async def _sync_and_arm(session: AsyncSession) -> ScheduleState:
    """Register the procurement schedules, then arm the one schedule procedure's slot as DUE."""
    from services.engine.procedures.scheduler_wiring import sync_schedule_states

    spec = load_procedures(_VERTICAL)
    rows = await sync_schedule_states(session, spec, now=EPOCH)
    # sync creates a ScheduleState only for `schedule`-trigger procedures — procurement ships
    # exactly one (the Step-8 demo procedure); the two manual procedures are skipped.
    assert [r.procedure_id for r in rows] == [_PROC_ID]
    state = rows[0]
    assert state.schedule_id == schedule_id_for(_VERTICAL, _PROC_ID)
    assert state.next_fire is None  # fresh registration — not yet armed
    state.next_fire = SLOT  # arm the due slot (the daemon's first tick would INITIALIZE this)
    await session.commit()
    return state


async def test_scheduled_procurement_run_parks_at_doa_gate(
    session: AsyncSession, procurement_registered: None
) -> None:
    """AC-4/5/9 on the REAL spec: the nightly schedule fires as the service principal, runs the
    auto steps, and PARKS at the DOA ``approve`` gate (a machine never approves — RF-3)."""
    spec = load_procedures(_VERTICAL)
    resolve = build_resolver(spec, registry.get_procedure_executors(_VERTICAL))
    state = await _sync_and_arm(session)

    [outcome] = await fire_due_schedules(session, [state], now=NOW, resolve=resolve)

    # FIRED, and parked at the human gate (not auto-completed — the service actor cannot approve).
    assert outcome.result is FireResult.FIRED
    assert outcome.run_status == PipelineRunStatus.WAITING_HUMAN.value

    loaded = await load_run(session, outcome.run_id)
    assert loaded is not None
    assert loaded.run.status == PipelineRunStatus.WAITING_HUMAN.value
    suspended = loaded.step_results[-1]
    assert suspended.step_id == _GATED_STEP  # suspended AT the DOA gate

    # The ฿288,000 hero spend resolved to the [50k,500k) DOA tier → ผจก.จัดซื้อ → appr-pm (the
    # roster-reconciled factory resolves the SAME person who will approve — a coherent audit).
    doa = (suspended.audit or {}).get("doa_tier")
    assert doa and doa[0]["required_role"] == "ผจก.จัดซื้อ"
    assert doa[0]["resolved_approver_id"] == "appr-pm"

    # AC-4 — the run acts as the declared service principal (actor_kind:"service") ON BEHALF OF
    # the owning human (SP-5), who is recorded as the SoD requester on intake.
    [started] = await _audit_rows(session, "run_started", outcome.run_id)
    assert started.actor_service_principal_id == _SP_ID
    assert started.payload is not None
    assert started.payload["actor_kind"] == "service"
    assert started.payload["on_behalf_of"]["service_principal_id"] == _SP_ID
    assert started.payload["on_behalf_of"]["owning_person_id"] == "req-planner"  # SP-5

    # SoD requester half recorded at fire (a doa_tier procedure carries SoD, ADR-0025 D5): the
    # constrained `intake` step completed as the owning human req-planner, so the gate resolves
    # with a DISTINCT approver.
    assert loaded.run.step_principals is not None  # this run carried a SoD constraint
    assert loaded.run.step_principals.get("intake") == "req-planner"

    # AC-9 — the SD-P6 trigger_context stamp rides on the persisted run.
    tc = loaded.run.trigger_context
    assert tc is not None
    assert tc["trigger"] == Trigger.SCHEDULE.value
    assert tc["cron"] == "0 6 * * *"
    assert tc["timezone"] == "Asia/Bangkok"
    assert tc["actor"] == _SP_ID
    assert tc["scheduled_for"] == SLOT.isoformat()


async def test_scheduled_run_resolves_through_to_completed(
    session: AsyncSession, procurement_registered: None
) -> None:
    """The on-behalf-of (SoD) design resolves cleanly: with the owning human req-planner recorded
    as the intake requester, a DISTINCT human DOA approver (appr-pm) decides the parked gate — SoD
    governed (requester ≠ approver) — and the run resumes to ``COMPLETED`` (the ``audit`` terminal).
    """
    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == _PROC_ID)
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    resolve = build_resolver(spec, registry.get_procedure_executors(_VERTICAL))
    state = await _sync_and_arm(session)

    [outcome] = await fire_due_schedules(session, [state], now=NOW, resolve=resolve)
    assert outcome.run_status == PipelineRunStatus.WAITING_HUMAN.value

    # The human approver: the ฿288,000 hero spend lands in the [50k,500k) DOA tier → ผจก.จัดซื้อ
    # (นรี / appr-pm). RF-1 needs a real authored Person; SoD is inert (no constraint).
    approver: Person = next(p for p in spec.principals if "ผจก.จัดซื้อ" in p.roles)
    assert approver.person_id == "appr-pm"

    # Approve every proposal on the parked gate (action_id → "approve").
    loaded = await load_run(session, outcome.run_id)
    assert loaded is not None
    suspended = loaded.step_results[-1]
    output_set: list[dict[str, Any]] = (suspended.artifact or {}).get("output_set", [])
    decisions = {
        p["action"]["id"]: "approve" for p in output_set if isinstance(p.get("action"), dict)
    }
    assert decisions, "the DOA gate produced no decidable proposals"

    await resolve_gated_step(
        session,
        outcome.run_id,
        _GATED_STEP,
        decisions,
        principal=approver,
        procedure=proc,
        principals=spec.principals,
        principal_aliases=spec.principal_aliases,
    )
    result = await resume_run(
        session,
        proc,
        agent,
        registry.get_procedure_executors(_VERTICAL)(),
        outcome.run_id,
        vertical=_VERTICAL,
        principal=approver,
    )
    assert result.run.status == PipelineRunStatus.COMPLETED.value

    run = await session.get(PipelineRun, outcome.run_id)
    assert run is not None and run.status == PipelineRunStatus.COMPLETED.value
