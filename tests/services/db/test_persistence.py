"""§7.6 persistence acceptance — Alembic migration + ORM round-trip.

These tests require a live postgres:16-alpine (OQ-4). They skip
gracefully when the database in settings.database_url is unreachable,
so the suite stays green without Docker.

Each test gets a fresh NullPool engine (PLAN-0005 R4 — async test
ergonomics): a per-test engine avoids reusing connections across
pytest-asyncio's per-test event loops.
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
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from services.api.config import settings
from services.db.base import Base
from services.db.models import Alert, RecommendedAction
from tests.db_support import create_test_engine

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
        # This module does not import services.db.identity, so `action_identity`
        # (created by the alembic migration this test runs) is absent from this
        # process's Base.metadata and survives drop_all — leaking into the next
        # alembic test as a DuplicateTableError. Drop it explicitly.
        await conn.execute(sa.text("DROP TABLE IF EXISTS action_identity CASCADE"))


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    """A fresh NullPool engine per test, bound to the disposable test DB.

    Targets settings.test_database_url (a sibling <db>_test), never the
    dev/demo DB; skips when Postgres is unreachable so the suite stays green
    without Docker.
    """
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


async def test_alembic_upgrade_creates_energy_tables(db_engine: AsyncEngine) -> None:
    """§7.6: `alembic upgrade head` materialises the six energy tables."""
    await _drop_everything(db_engine)
    # Override DATABASE_URL so alembic/env.py (which reads settings.database_url)
    # migrates the disposable test DB, not the dev/demo DB. Env vars take
    # precedence over .env in pydantic-settings.
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
