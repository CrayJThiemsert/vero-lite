"""PLAN-0019 Part A — pipeline_runs + step_results migration + ORM round-trip.

Mirrors ``test_persistence.py``: requires a live Postgres and skips gracefully
when unreachable, binding to the disposable ``<db>_test`` (never the dev/demo
DB). Asserts the Alembic migration materialises the two additive tables and that
a run + step-result round-trips — including the AC A-9 telemetry seam
(``duration_ms`` + ``reasoning_trace`` + ``audit``) and the JSONB set-valued
artifact.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from services.api.config import settings
from services.db.base import Base
from services.engine.procedures.runs import (
    PipelineRun,
    PipelineRunStatus,
    StepResult,
    StepResultStatus,
)
from tests.db_support import create_test_engine

_REPO_ROOT = Path(__file__).resolve().parents[3]
_PROCEDURE_TABLES = {"pipeline_runs", "step_results"}
_TRACE = [{"step_id": "judge", "kind": "evaluate", "summary": "DO 3.2 mg/L < 4 floor"}]
_AUDIT = {"actor": "engine", "actor_kind": "engine"}
_ARTIFACT = {"breach_ponds": ["pond-3", "pond-7"]}


async def _drop_everything(eng: AsyncEngine) -> None:
    """Drop the ORM tables plus Alembic's version table."""
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    """A fresh NullPool engine per test, bound to the disposable test DB."""
    eng = await create_test_engine()
    yield eng
    await eng.dispose()


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Create the schema, yield a session, drop the schema."""
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        yield session
    await _drop_everything(db_engine)


async def test_alembic_upgrade_creates_procedure_tables(db_engine: AsyncEngine) -> None:
    """`alembic upgrade head` materialises the two additive procedure tables."""
    await _drop_everything(db_engine)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=_REPO_ROOT,
        env={**os.environ, "DATABASE_URL": settings.test_database_url},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    async with db_engine.connect() as conn:
        rows = await conn.execute(
            sa.text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )
        )
        present = {row[0] for row in rows}
    assert _PROCEDURE_TABLES <= present
    await _drop_everything(db_engine)


async def test_run_and_step_result_round_trip(db_session: AsyncSession) -> None:
    """A suspended run + its telemetry-bearing step result read back intact (AC A-9)."""
    started = datetime(2026, 6, 7, 6, 0, tzinfo=UTC)
    db_session.add(
        PipelineRun(
            run_id="run-1",
            procedure_id="morning_pond_health_round",
            agent_id="pond_health_agent",
            trigger_context={"trigger": "manual", "actor": "cray"},
            status=PipelineRunStatus.WAITING_HUMAN.value,
            started_at=started,
            updated_at=started,
        )
    )
    db_session.add(
        StepResult(
            step_result_id="run-1:aerate",
            run_id="run-1",
            step_id="aerate",
            status=StepResultStatus.WAITING_HUMAN.value,
            duration_ms=1234,
            artifact=_ARTIFACT,
            reasoning_trace=_TRACE,
            audit=_AUDIT,
            created_at=started,
        )
    )
    await db_session.commit()

    run = await db_session.get(PipelineRun, "run-1")
    assert run is not None
    assert run.status == PipelineRunStatus.WAITING_HUMAN.value
    assert run.trigger_context == {"trigger": "manual", "actor": "cray"}

    step = await db_session.get(StepResult, "run-1:aerate")
    assert step is not None
    # AC A-9 — the per-step telemetry seam persists for Part B to consume.
    assert step.duration_ms == 1234
    assert step.reasoning_trace == _TRACE
    assert step.audit == _AUDIT
    # set-valued artifact (the breach subset) round-trips through JSONB.
    assert step.artifact == _ARTIFACT
