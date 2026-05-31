"""API-level proof that OCT_VERTICAL swaps the served vertical (PLAN-0013 AC-template).

With ``settings.oct_vertical = "supply_chain"`` and the matching recommend
policy, the SAME routers serve the supply_chain ontology + data and derive a
recommendation from the cold-chain breach — no router or engine code change.
The autouse ``_offline_llm`` fixture (tests/api/conftest.py) keeps the LLM
path offline; the autouse registry reset (tests/conftest.py) isolates state.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from services.api.config import settings
from services.api.main import app
from services.api.routers.actions import reset_action_store
from verticals.supply_chain.data_adapter import register_supply_chain_adapter
from verticals.supply_chain.handlers import register_supply_chain_handlers


@pytest.fixture
async def supply_chain_client(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncClient]:
    """An httpx client with the app configured for the supply_chain vertical."""
    monkeypatch.setattr(settings, "oct_vertical", "supply_chain")
    monkeypatch.setattr(settings, "oct_recommend_threshold", 8.0)
    monkeypatch.setattr(settings, "oct_recommend_entity_type", "Shipment")
    monkeypatch.setattr(settings, "oct_recommend_entity_id_field", "shipment_id")
    monkeypatch.setattr(settings, "oct_recommend_label", "cold-chain temperature breach")
    register_supply_chain_adapter()
    register_supply_chain_handlers()
    reset_action_store()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    reset_action_store()


async def test_meta_serves_supply_chain_ontology(supply_chain_client: AsyncClient) -> None:
    res = await supply_chain_client.get("/meta")
    assert res.status_code == 200
    meta = res.json()
    assert meta["vertical"] == "supply_chain"
    names = {t["name"] for t in meta["object_types"]}
    assert {"Shipment", "Facility"} <= names


async def test_objects_serve_supply_chain_data(supply_chain_client: AsyncClient) -> None:
    shipments = (await supply_chain_client.get("/objects/Shipment")).json()
    assert shipments["count"] == 4
    facilities = (await supply_chain_client.get("/objects/Facility")).json()
    assert facilities["count"] == 2


async def test_recommendations_derived_for_cold_chain_breach(
    supply_chain_client: AsyncClient,
) -> None:
    res = await supply_chain_client.get("/recommendations")
    assert res.status_code == 200
    body = res.json()
    assert body["count"] >= 1
    rec = body["recommendations"][0]
    assert rec["vertical"] == "supply_chain"
    assert rec["status"] == "proposed"
    assert rec["reasoning_trace"]  # the "show me WHY" trace is surfaced
