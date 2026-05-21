"""§7.6 persistence acceptance — Alembic migration + ORM round-trip.

These tests require a live postgres:16-alpine (OQ-4). They skip
gracefully when the database in settings.database_url is unreachable,
so the suite stays green without Docker.

Each test gets a fresh NullPool engine (PLAN-0005 R4 — async test
ergonomics): a per-test engine avoids reusing connections across
pytest-asyncio's per-test event loops.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from services.api.config import settings
from services.db.base import Base
from services.db.models import Alert, RecommendedAction

_REPO_ROOT = Path(__file__).resolve().parents[3]
_EXPECTED_TABLES = {
    "site",
    "asset",
    "operational_event",
    "alert",
    "recommended_action",
    "alert_event_link",
}


async def _drop_everything(eng: AsyncEngine) -> None:
    """Drop the ORM tables plus Alembic's version table."""
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    """A fresh NullPool engine per test; skip when Postgres is unreachable."""
    eng = create_async_engine(settings.database_url, poolclass=NullPool)
    try:
        async with eng.connect() as conn:
            await conn.execute(sa.text("SELECT 1"))
    except Exception:
        await eng.dispose()
        pytest.skip("Postgres not reachable — start docker compose / set DATABASE_URL")
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


async def test_alembic_upgrade_creates_energy_tables(db_engine: AsyncEngine) -> None:
    """§7.6: `alembic upgrade head` materialises the six energy tables."""
    await _drop_everything(db_engine)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=_REPO_ROOT,
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
    assert _EXPECTED_TABLES <= present
    await _drop_everything(db_engine)


async def test_executed_action_row_round_trips(db_session: AsyncSession) -> None:
    """§7.6: an executed RecommendedAction row reads back with status executed."""
    db_session.add(
        Alert(
            alert_id="alert-1",
            title="Over-temperature on asset-battery-01",
            opened_at=datetime(2026, 5, 21, 8, 10, tzinfo=UTC),
        )
    )
    db_session.add(
        RecommendedAction(
            action_id="action-1",
            status="executed",
            confidence_score=0.8,
            alert_id="alert-1",
        )
    )
    await db_session.commit()

    loaded = await db_session.get(RecommendedAction, "action-1")
    assert loaded is not None
    assert loaded.status == "executed"
