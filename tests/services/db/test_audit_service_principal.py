"""PLAN-0053 Phase B — the audit-layer service actor (AC-9/10/11).

DB-backed (skips without Postgres). Proves the SD-2 **omit-when-None** property on the
tamper-evident hash-chain (a service=None row recomputes byte-identically, so no
pre-migration row breaks; a service id IS hashed) and the service-triggered
``run_started`` wiring (actor_kind:"service" + never-null service actor + on-behalf-of).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.db.audit_log import (
    GENESIS_HASH,
    AuditLog,
    append_audit,
    compute_row_hash,
    verify_chain,
)
from services.db.base import Base
from services.engine.procedures.orchestrator import RunContext, StepExecutor, StepOutcome
from services.engine.procedures.persistence import run_procedure_persisted
from services.engine.procedures.spec import (
    Agent,
    Procedure,
    ServicePrincipal,
    Step,
    StepKind,
)
from tests.db_support import create_test_engine


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


class _NoopQuery:
    """A query executor that produces an empty output set (the run completes, no gate)."""

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(output=[])


# --- AC-11: omit-when-None keeps the chain byte-recomputable across the boundary --


def test_service_none_row_hashes_identically_to_pre_migration() -> None:
    """SD-2 omit-when-None: a row with ``actor_service_principal_id=None`` hashes
    BYTE-IDENTICALLY to the pre-migration 7-field canonical (the key is omitted), so no
    pre-migration row's stored hash breaks after the column is added."""
    t = datetime(2026, 7, 6, 12, 0, 0, 123456, tzinfo=UTC)
    common: dict[str, Any] = dict(
        prev_hash=GENESIS_HASH,
        occurred_at=t,
        actor_person_id="appr-pm",
        action="gate_decision",
        run_id="r1",
        step_id="approve",
        payload={"x": 1},
    )
    assert compute_row_hash(**common, actor_service_principal_id=None) == compute_row_hash(**common)


def test_service_id_is_part_of_the_hash() -> None:
    """A non-None service id IS in the canonical hash — presence changes the hash, so
    tampering with it (change or hide) is detected by ``verify_chain``."""
    t = datetime(2026, 7, 6, 12, 0, 0, 0, tzinfo=UTC)
    common: dict[str, Any] = dict(
        prev_hash=GENESIS_HASH,
        occurred_at=t,
        actor_person_id=None,
        action="run_started",
        run_id="r2",
        step_id=None,
        payload=None,
    )
    with_id = compute_row_hash(**common, actor_service_principal_id="svc-x")
    without_id = compute_row_hash(**common)
    assert with_id != without_id


async def test_mixed_human_and_service_chain_verifies_intact(db_engine: AsyncEngine) -> None:
    """AC-11: a chain mixing human rows (service=None) and a service row verifies with 0 breaks
    — the migration boundary never breaks the tamper-evident chain."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        await append_audit(session, action="run_started", actor_person_id="appr-pm", run_id="r")
        await append_audit(session, action="gate_decision", actor_person_id="appr-pm", run_id="r")
        await append_audit(
            session, action="run_started", run_id="r2", actor_service_principal_id="svc-scheduler"
        )
        await session.commit()
    async with maker() as session:
        assert await verify_chain(session) == []
    async with maker() as session:
        row = (
            await session.execute(sa.select(AuditLog).where(AuditLog.run_id == "r2"))
        ).scalar_one()
        assert row.actor_service_principal_id == "svc-scheduler"


# --- AC-9/AC-10: a service-triggered run_started records the service actor -------


async def test_service_triggered_run_started_records_service_actor(db_engine: AsyncEngine) -> None:
    """AC-10 (never-null service actor) + AC-9 (actor_kind:'service' + on-behalf-of lineage):
    a service-triggered ``run_procedure_persisted`` writes a ``run_started`` row naming the
    service id in the new column and both lineage keys in ``on_behalf_of``."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    sp = ServicePrincipal(service_principal_id="svc-nightly", name="Nightly Scheduler")
    procedure = Procedure(
        procedure_id="p",
        title="P",
        run_by="a",
        steps=[Step(step_id="read", name="Read", kind=StepKind.QUERY)],
    )
    executors: dict[StepKind, StepExecutor] = {StepKind.QUERY: _NoopQuery()}
    async with maker() as session:
        await run_procedure_persisted(
            session,
            procedure,
            Agent(agent_id="a", name="A"),
            executors,
            vertical="aquaculture",
            run_id="svc-run",
            service_principal=sp,
        )
    async with maker() as session:
        row = (
            await session.execute(
                sa.select(AuditLog).where(
                    AuditLog.action == "run_started", AuditLog.run_id == "svc-run"
                )
            )
        ).scalar_one()
        assert row.actor_service_principal_id == "svc-nightly"  # AC-10: never null
        assert (row.payload or {}).get("actor_kind") == "service"  # AC-9
        assert (row.payload or {}).get("on_behalf_of") == {
            "service_principal_id": "svc-nightly",
            "owning_person_id": None,
        }
