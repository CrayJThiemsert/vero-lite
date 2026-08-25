"""Fixtures for the action-loop API tests.

The autouse _reset_registry fixture (tests/conftest.py) wipes the
registry before each test; the energy_vertical fixture then re-registers
the energy adapter + handlers (the app lifespan does not run under
httpx.ASGITransport). client_with_db overrides get_session with a
per-test NullPool engine and skips when Postgres is unreachable.
"""

import json
import re
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
from tests.db_support import create_test_engine, drop_all_bounded
from verticals.energy.data_adapter import register_energy_adapter
from verticals.energy.handlers import register_energy_handlers

# --- offline LLM (PLAN-0006 Step 6) ---------------------------------------

#: The judgment the stub emits when it cannot recover the triggering event from the
#: prompt — a caller that passes no event, or a prompt shape that changed. Kept
#: identical to the pre-PLAN-0107 constant so that path is a true fallback and not a
#: second behaviour to reason about.
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

#: ``format_event`` renders the event as ``key: value`` lines inside the untrusted
#: block, so the stub can recover the fields a real model would have read. Anchored
#: to line starts so a value containing ``asset_id:`` cannot forge a field.
_EVENT_FIELD = re.compile(
    r"^(event_id|asset_id|truck_id|measured_kind|measured_value|unit): (.+)$", re.MULTILINE
)

#: The entity a vertical's events are ABOUT, keyed by the id field the event carries.
#: ``resolve_affected_entities`` resolves the emitted ref against the vertical's
#: declared object universe, so the object_type has to be that vertical's real one —
#: energy's ``Asset`` and fleet's ``Truck`` are different types, and emitting the
#: wrong one falls the whole record back to the deterministic path, silently changing
#: what every API test exercises.
_ENTITY_BY_ID_FIELD: tuple[tuple[str, str], ...] = (
    ("asset_id", "Asset"),
    ("truck_id", "Truck"),
)


def _triggering_event(messages: list[dict[str, str]]) -> dict[str, str]:
    """Recover the triggering event's fields from the rendered prompt.

    Returns ``{}`` when no user turn carries an ``event_id`` — the caller then
    falls back to the canned judgment.
    """
    for message in messages:
        if message.get("role") != "user":
            continue
        fields = dict(_EVENT_FIELD.findall(message.get("content", "")))
        if "event_id" in fields:
            return fields
    return {}


def _judgment_for(messages: list[dict[str, str]]) -> str:
    """A judgment DERIVED from the triggering event (PLAN-0107 AC-8).

    🔴 **Why this is a factory and not a constant.** The previous stub returned ONE
    canned object for every event in a streamed batch — same title, same confidence,
    same ``affected_entities`` — as its own docstring admitted. That makes a whole
    class of defect invisible: a recommend fan-out that maps every event to the FIRST
    event's judgment, or drops the event→judgment correspondence entirely, produces
    byte-identical output under the old stub and cannot be reddened by any assertion
    written against it. The judgments agreed with each other by construction.

    ``affected_entities`` carries the event's OWN ``asset_id`` rather than a fixed
    one, which matters twice over: it is what makes the per-event mapping assertable,
    and the id must be real because ``resolve_affected_entities`` resolves it against
    the declared object universe — a fabricated key would fall the record back to the
    deterministic path and quietly change what every API test exercises.
    """
    fields = _triggering_event(messages)
    if not fields:
        return _STUB_JUDGMENT
    event_id = fields["event_id"]
    entity_type, entity_key = "Asset", "asset-energy-01"
    for id_field, object_type in _ENTITY_BY_ID_FIELD:
        if id_field in fields:
            entity_type, entity_key = object_type, fields[id_field]
            break
    kind = fields.get("measured_kind", "reading")
    unit = fields.get("unit", "")
    value = fields.get("measured_value", "")
    reading = f"{value} {unit}".strip() or "the reported value"
    # ``event_id`` rides in the TITLE, not only in handler_payload: the title is on
    # RecommendationResponse and the payload is not, so this is the only field a
    # scenario can use to assert judgment -> event correspondence over HTTP.
    return json.dumps(
        {
            "title": f"LLM assessment: escalate {kind} excursion on {entity_key} [{event_id}]",
            "description": f"{event_id} reports {reading} on {entity_key}, outside its safe band.",
            "rationale": (
                f"Sustained {kind} excursion on {entity_key} risks damage; escalate for review."
            ),
            "confidence": 0.88,
            "affected_entities": [{"object_type": entity_type, "primary_key": entity_key}],
            "suggested_handler": "echo",
            "handler_payload": {"source": "llm-stub", "event_id": event_id},
        }
    )


class _StubChatClient:
    """Deterministic offline LLM — call 1 reasons, call 2 emits a judgment.

    Stateless, and deliberately so: it decides by request shape plus the event the
    prompt carries, so one instance serves every recommend() call across a streamed
    batch **while still answering each event differently**. Statefulness (a counter,
    a queue of scripted replies) would make the reply depend on call ORDER, which is
    the one thing a fan-out test must be free to change.
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
            return ChatResult(
                content=_judgment_for(messages), thinking=None, model="gpt-oss:20b", raw={}
            )
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
        await drop_all_bounded(conn)
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
