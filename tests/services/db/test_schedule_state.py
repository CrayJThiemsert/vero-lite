"""PLAN-0055 Step 2 (ADR-0028 SD-P5) — schedule_states migration + ORM round-trip.

Mirrors ``test_procedure_runs.py``: requires a live Postgres and skips gracefully when
unreachable, binding to the disposable ``<db>_test`` (never the dev/demo DB). Asserts the
0011 Alembic migration materialises the additive ``schedule_states`` table, that a
schedule row (incl. the nullable ``last_fired`` / ``next_fire`` tz-aware timestamps)
round-trips through the ORM, and that ``(vertical, procedure_id)`` is unique.
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
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from services.api.config import settings
from services.db.base import Base
from services.engine.procedures.schedules import ScheduleState
from tests.db_support import create_test_engine

_REPO_ROOT = Path(__file__).resolve().parents[3]


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


async def test_alembic_upgrade_creates_schedule_states(db_engine: AsyncEngine) -> None:
    """`alembic upgrade head` materialises the additive schedule_states table (0011)."""
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
    assert "schedule_states" in present
    await _drop_everything(db_engine)


async def test_schedule_state_round_trip(db_session: AsyncSession) -> None:
    """A schedule row — incl. the nullable tz-aware fire timestamps — reads back intact."""
    now = datetime(2026, 7, 7, 6, 0, tzinfo=UTC)
    next_fire = datetime(2026, 7, 8, 6, 0, tzinfo=UTC)
    db_session.add(
        ScheduleState(
            schedule_id="aquaculture:morning_round",
            vertical="aquaculture",
            procedure_id="morning_round",
            cron="0 6 * * *",
            timezone="Asia/Bangkok",
            last_fired=None,
            next_fire=next_fire,
            created_at=now,
            updated_at=now,
        )
    )
    await db_session.commit()

    row = await db_session.get(ScheduleState, "aquaculture:morning_round")
    assert row is not None
    assert row.vertical == "aquaculture"
    assert row.procedure_id == "morning_round"
    assert row.cron == "0 6 * * *"
    assert row.timezone == "Asia/Bangkok"
    assert row.last_fired is None  # a freshly-registered schedule has no fire history
    assert row.next_fire == next_fire  # tz-aware timestamp round-trips (== compares the instant)


async def test_schedule_state_vertical_procedure_is_unique(db_session: AsyncSession) -> None:
    """`(vertical, procedure_id)` is unique — a second row for the same pair is rejected."""
    now = datetime(2026, 7, 7, 6, 0, tzinfo=UTC)

    def _row(schedule_id: str) -> ScheduleState:
        return ScheduleState(
            schedule_id=schedule_id,
            vertical="aquaculture",
            procedure_id="morning_round",
            cron="0 6 * * *",
            timezone="Asia/Bangkok",
            created_at=now,
            updated_at=now,
        )

    db_session.add(_row("sched-a"))
    await db_session.commit()

    db_session.add(_row("sched-b"))  # same (vertical, procedure_id), different PK
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()
