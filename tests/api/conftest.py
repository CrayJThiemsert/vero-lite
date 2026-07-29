"""Fixtures for the action-loop API tests.

The autouse _reset_registry fixture (tests/conftest.py) wipes the
registry before each test; the energy_vertical fixture then re-registers
the energy adapter + handlers (the app lifespan does not run under
httpx.ASGITransport). client_with_db overrides get_session with a
per-test NullPool engine and skips when Postgres is unreachable.
"""

import json
from collections.abc import AsyncIterator, Iterator

import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.main import app
from services.api.routers.actions import reset_action_store
from services.db.base import Base
from services.db.session import get_session
from services.engine.llm.client import ChatResult
from tests.db_support import create_test_engine
from verticals.energy.data_adapter import register_energy_adapter
from verticals.energy.handlers import register_energy_handlers

# --- offline LLM (PLAN-0006 Step 6) ---------------------------------------

_STUB_JUDGMENT = json.dumps(
    {
        "title": "LLM assessment: thermal excursion on the battery asset",
        "description": "The reading is above the safe operating temperature threshold.",
        "rationale": "Sustained over-temperature risks cell damage; escalate for review.",
        "confidence": 0.88,
        "affected_entities": [{"object_type": "Asset", "primary_key": "asset-energy-01"}],
        "suggested_handler": "echo",
        "handler_payload": {"source": "llm-stub"},
    }
)


class _StubChatClient:
    """Deterministic offline LLM — call 1 reasons, call 2 emits a judgment.

    Stateless: it decides by request shape, so one instance serves every
    recommend() call across a streamed batch of events.
    """

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, object] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        if response_format is not None:
            return ChatResult(content=_STUB_JUDGMENT, thinking=None, model="gpt-oss:20b", raw={})
        return ChatResult(
            content="draft assessment",
            thinking="reasoned step by step about the operational event",
            model="gpt-oss:20b",
            raw={},
        )


_STUB_CLIENT = _StubChatClient()


@pytest.fixture(autouse=True)
def _offline_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force recommend() onto the offline faked LLM for every API test.

    Each API test then drives read -> recommend (LLM, faked) -> approve ->
    execute with no live Ollama call (PLAN-0006 Step 6 / §7.5).
    """
    monkeypatch.setattr("services.engine.recommender._build_chat_client", lambda: _STUB_CLIENT)


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
async def api_db_maker() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """A per-test engine on the disposable test DB, as a sessionmaker.

    Factored out of ``client_with_db`` so a test can hold a session on the SAME
    engine the API is writing through (PLAN-0096 Step 6's scenario suite needs to
    drive a server-side sweep over rows the HTTP routes just wrote). A second
    independent engine would work too, but sharing this one keeps the whole
    scenario inside one create_all/drop_all lifecycle.
    """
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(eng, expire_on_commit=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


@pytest.fixture
async def client_with_db(
    energy_vertical: None, api_db_maker: async_sessionmaker[AsyncSession]
) -> AsyncIterator[AsyncClient]:
    """An httpx client with get_session overridden by a per-test engine.

    Binds to the disposable test DB (settings.test_database_url), never the
    dev/demo DB — the create_all/drop_all round-trip in ``api_db_maker`` owns its
    schema.
    """

    async def _override_session() -> AsyncIterator[AsyncSession]:
        async with api_db_maker() as session:
            yield session

    app.dependency_overrides[get_session] = _override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


@pytest.fixture
async def db_session(
    api_db_maker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """A session on the same engine the API client writes through.

    For server-side code a test needs to drive directly — a sweep, a report — over
    rows the HTTP routes created.
    """
    async with api_db_maker() as session:
        yield session
