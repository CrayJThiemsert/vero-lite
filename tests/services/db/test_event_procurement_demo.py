"""PLAN-0056 Step 8 (ADR-0029 event-trigger bridge) — the procurement `event`-trigger demo.

The end-to-end wiring of the **REAL procurement spec** through the whole event-bridge chain:
``load_procedures`` → ``build_event_resolver`` → ``fire_event`` → a persisted ``waiting_human`` run
parked at the DOA gate → a **human** resolves it → ``COMPLETED``.

Mirrors the PLAN-0055 Step 8 scheduled demo (``test_scheduled_procurement_demo.py``) but on the
`event`-trigger path: a detected asset-failure event (the recommender proposing
``emergency_source``, PLAN-0056 Step 6: ``event_kind = suggested_handler``) FEEDS INTO the governed
engine and fires the DISTINCT ``event_emergency_sourcing_round`` procedure. It drives the SHIPPED
procurement executor factory (``register_procurement_procedure_executors``), so it catches the same
integration gotchas (Decimal→JSONB fresh-fire seed; the on-behalf-of SoD posture) as the scheduled
demo.

DB-backed (disposable ``<db>_test``, skips without Postgres); **MS-S1-free** — the factory's
``advisory_stub_factory`` is deterministic (the bridge exercises the recommender's rule path, not a
live model call, CLAUDE.md §8). A live end-to-end smoke (real detector → real fire) is host-state
(§8); this offline test is the gate (AC-12).
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
from services.engine.procedures.action_step import resolve_gated_step
from services.engine.procedures.event_bridge import (
    EventFireResult,
    build_event_resolver,
    fire_event,
)
from services.engine.procedures.persistence import load_run, resume_run, suspended_step_result
from services.engine.procedures.runs import PipelineRun, PipelineRunStatus, StepResultStatus
from services.engine.procedures.spec import Person, load_procedures
from services.engine.registry import registry
from tests.db_support import create_test_engine

_VERTICAL = "procurement"
_PROC_ID = "event_emergency_sourcing_round"
_GATED_STEP = "approve"
_SP_ID = "svc-buyer"
_EVENT_KIND = "emergency_source"  # = RecommendedAction.suggested_handler (PLAN-0056 Step 6)
_ENTITY_IDS = ["pump-7"]
# A detected asset-failure event + an observation just past it (the fire's `now`).
DETECTED = datetime(2026, 7, 7, 6, 0, tzinfo=UTC)
NOW = datetime(2026, 7, 7, 6, 30, tzinfo=UTC)


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
    """Register EXACTLY what the API lifespan registers — ``discover_and_register`` (adapters +
    action handlers, OQ-6) + the procedure-executor factory — so a fired event run's action steps
    (``source`` / ``emergency_source``, the ``audit`` echo) resolve their handlers. The autouse
    registry reset (tests/conftest.py) wipes the registry per test, so this re-registers cleanly."""
    from services.engine.discovery import discover_and_register
    from verticals.procurement.hero_demo.run import register_procurement_procedure_executors

    discover_and_register()
    await register_procurement_procedure_executors()
    yield


async def _audit_rows(session: AsyncSession, action: str, run_id: str) -> list[AuditLog]:
    rows = await session.execute(
        sa.select(AuditLog).where(AuditLog.action == action, AuditLog.run_id == run_id)
    )
    return list(rows.scalars().all())


def _resolve_event() -> Any:
    """Resolve the detected asset-failure event → an EventRunRequest against the REAL spec."""
    spec = load_procedures(_VERTICAL)
    resolve = build_event_resolver(spec, registry.get_procedure_executors(_VERTICAL))
    return resolve(event_kind=_EVENT_KIND, entity_ids=_ENTITY_IDS, detected_at=DETECTED)


async def test_event_procurement_run_parks_at_doa_gate(
    session: AsyncSession, procurement_registered: None
) -> None:
    """AC-12 on the REAL spec: a detected asset-failure event auto-fires as the service principal,
    runs the auto steps, and PARKS at the DOA ``approve`` gate (a machine never approves — RF-3)."""
    request = _resolve_event()
    outcome = await fire_event(session, request, now=NOW)

    # FIRED, and parked at the human gate (not auto-completed — the service actor cannot approve).
    assert outcome.result is EventFireResult.FIRED
    assert outcome.run_status == PipelineRunStatus.WAITING_HUMAN.value

    loaded = await load_run(session, outcome.run_id)
    assert loaded is not None
    assert loaded.run.status == PipelineRunStatus.WAITING_HUMAN.value
    suspended = suspended_step_result(loaded.step_results)  # by STATUS, never by position
    assert suspended is not None
    assert suspended.step_id == _GATED_STEP  # suspended AT the DOA gate

    # The ฿288,000 hero spend resolves to the [50k,500k) DOA tier → ผจก.จัดซื้อ → appr-pm.
    doa = (suspended.audit or {}).get("doa_tier")
    assert doa and doa[0]["required_role"] == "ผจก.จัดซื้อ"
    assert doa[0]["resolved_approver_id"] == "appr-pm"

    # AC-7 — the run acts as the declared service principal (actor_kind:"service") ON BEHALF OF the
    # owning human (SP-5), recorded as the SoD requester on intake.
    [started] = await _audit_rows(session, "run_started", outcome.run_id)
    assert started.actor_service_principal_id == _SP_ID
    assert started.payload is not None
    assert started.payload["actor_kind"] == "service"
    assert started.payload["on_behalf_of"]["service_principal_id"] == _SP_ID
    assert started.payload["on_behalf_of"]["owning_person_id"] == "req-planner"  # SP-5

    # SoD requester half recorded at fire (a doa_tier procedure carries SoD, ADR-0025 D5).
    assert loaded.run.step_principals is not None
    assert loaded.run.step_principals.get("intake") == "req-planner"

    # AC-9 — the event trigger_context stamp rides on the persisted run.
    tc = loaded.run.trigger_context
    assert tc is not None
    assert tc["trigger"] == "event"
    assert tc["event_kind"] == _EVENT_KIND
    assert tc["entity_ids"] == _ENTITY_IDS
    assert tc["detected_at"] == DETECTED.isoformat()
    assert "fired_at" in tc


async def test_gate_is_found_by_status_under_a_backward_clock_step(
    session: AsyncSession, procurement_registered: None
) -> None:
    """Regression pin for an intermittent, full-suite-only failure of the two tests either side
    of this one. ``load_run`` orders step results by ``created_at`` — a WALL-CLOCK column, and
    this box's ``datetime.now(UTC)`` was measured stepping BACKWARDS (2 backward steps per 20 s
    sample, worst -555 ms). Invert it on purpose here: the ``approve`` gate no longer sorts last,
    so reading ``step_results[-1]`` names the *completed* ``compliance`` step — whose artifact
    carries no decidable proposal. Selecting by STATUS finds the gate regardless (#678's
    ``suspended_step_result``, which production already uses).
    """
    outcome = await fire_event(session, _resolve_event(), now=NOW)
    assert outcome.run_status == PipelineRunStatus.WAITING_HUMAN.value

    # The clock jumps backwards between `compliance` and the `approve` gate it suspended at.
    await session.execute(
        sa.text(
            "UPDATE step_results SET created_at = created_at - interval '1 second' "
            "WHERE run_id = :run_id AND step_id = :step_id"
        ),
        {"run_id": outcome.run_id, "step_id": _GATED_STEP},
    )
    await session.commit()
    session.expire_all()  # re-read the rewritten stamps, not the identity map's

    loaded = await load_run(session, outcome.run_id)
    assert loaded is not None
    order = [sr.step_id for sr in loaded.step_results]

    # Precondition: the wall-clock ORDER BY no longer yields execution order. The OLD positional
    # read would have picked `compliance` here and failed on its empty proposal set.
    assert order[-1] != _GATED_STEP, "precondition: the inversion must move the gate off last"
    assert order.index(_GATED_STEP) < order.index("compliance")

    # By STATUS the gate is still the one step that is unresumed.
    suspended = suspended_step_result(loaded.step_results)
    assert suspended is not None
    assert suspended.step_id == _GATED_STEP
    assert suspended.status == StepResultStatus.WAITING_HUMAN.value
    proposals = (suspended.artifact or {}).get("output_set", [])
    assert any(isinstance(p.get("action"), dict) for p in proposals), "the gate stays decidable"


async def test_event_run_resolves_through_to_completed(
    session: AsyncSession, procurement_registered: None
) -> None:
    """The on-behalf-of (SoD) design resolves cleanly: with the owning human req-planner recorded as
    the intake requester, a DISTINCT human DOA approver (appr-pm) decides the parked gate — SoD
    governed (requester ≠ approver) — and the run resumes to ``COMPLETED`` (the ``audit`` terminal).
    """
    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == _PROC_ID)
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)

    outcome = await fire_event(session, _resolve_event(), now=NOW)
    assert outcome.run_status == PipelineRunStatus.WAITING_HUMAN.value

    # The human approver: the ฿288,000 hero spend lands in the [50k,500k) DOA tier → ผจก.จัดซื้อ.
    approver: Person = next(p for p in spec.principals if "ผจก.จัดซื้อ" in p.roles)
    assert approver.person_id == "appr-pm"

    loaded = await load_run(session, outcome.run_id)
    assert loaded is not None
    suspended = suspended_step_result(loaded.step_results)  # by STATUS, never by position
    assert suspended is not None
    assert suspended.step_id == _GATED_STEP
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
