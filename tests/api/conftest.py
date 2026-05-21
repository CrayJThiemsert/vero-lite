"""Fixtures for the action-loop API tests.

The autouse _reset_registry fixture (tests/conftest.py) wipes the
registry before each test; the energy_vertical fixture then re-registers
the energy adapter + handlers (the app lifespan does not run under
httpx.ASGITransport). client_with_db overrides get_session with a
per-test NullPool engine and skips when Postgres is unreachable.
"""

from collections.abc import AsyncIterator, Iterator

import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from services.api.config import settings
from services.api.main import app
from services.api.routers.actions import reset_action_store
from services.db.base import Base
from services.db.session import get_session
from verticals.energy.data_adapter import register_energy_adapter
from verticals.energy.handlers import register_energy_handlers


@pytest.fixture
def energy_vertical() -> Iterator[None]:
    """Register the energy adapter + handlers and reset the action store."""
    register_energy_adapter()
    register_energy_handlers()
    reset_action_store()
    yield
    reset_action_store()


@pytest.fixture
async def client(energy_vertical: None) -> AsyncIterator[AsyncClient]:
    """An httpx client bound to the app (no database)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


@pytest.fixture
async def client_with_db(energy_vertical: None) -> AsyncIterator[AsyncClient]:
    """An httpx client with get_session overridden by a per-test engine."""
    eng = create_async_engine(settings.database_url, poolclass=NullPool)
    try:
        async with eng.connect() as conn:
            await conn.execute(sa.text("SELECT 1"))
    except Exception:
        await eng.dispose()
        pytest.skip("Postgres not reachable — start docker compose / set DATABASE_URL")
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(eng, expire_on_commit=False)

    async def _override_session() -> AsyncIterator[AsyncSession]:
        async with maker() as session:
            yield session

    app.dependency_overrides[get_session] = _override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()
