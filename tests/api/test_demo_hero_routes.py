"""Offline gate for the hero-demo read-only endpoints (PLAN-0045 Steps 1b + 3 wiring).

The offline test is the GATE (CLAUDE.md §8): ``GET /demo/hero/governance`` returns the shipped
governance-moment audit (CONTROLLER for the hero, MANAGER for the contrast) and
``GET /demo/hero/impact`` returns the exact ฿-impact ledger. The demo endpoints instantiate the
FastenalCsvAdapter directly (no discovery dependency), so a plain ASGI client suffices.
No mutation, no DB, no LLM; a live preview is evidence (Step 4), not the gate.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from services.api.main import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


def _money(value: object) -> Decimal:
    """Normalise a JSON money field (str or number) to Decimal for an exact compare."""
    return Decimal(str(value))


async def test_impact_endpoint_returns_exact_ledger(client: AsyncClient) -> None:
    response = await client.get("/demo/hero/impact")
    assert response.status_code == 200
    body = response.json()
    assert body["provisional"] is True
    assert body["currency"] == "THB"
    assert body["asset_id"] == "AST-CNC-014"
    assert _money(body["baseline"]["exposure_thb"]) == Decimal("9755500")
    assert _money(body["governed"]["exposure_thb"]) == Decimal("1648000")
    assert _money(body["expedite_premium_thb"]) == Decimal("52500")
    assert _money(body["avoided_downtime_thb"]) == Decimal("8160000")
    assert _money(body["net_benefit_thb"]) == Decimal("8107500")


async def test_governance_endpoint_binds_shipped_shapes(client: AsyncClient) -> None:
    response = await client.get("/demo/hero/governance")
    assert response.status_code == 200
    body = response.json()
    assert body["provisional"] is True
    assert body["source"] == "offline-fixture"
    # hero → CONTROLLER (the role), with the SoD + governed_decision ties
    hero = body["hero"]
    assert hero["doa_tier"][0]["resolved_tier_id"] == "CONTROLLER"
    assert hero["sod"]["governed"] is True
    kinds = {gd["control_ref"]["kind"] for gd in hero["governed_decision"]}
    assert kinds == {"doa_tier", "sod"}
    # contrast → MANAGER, no Controller escalation (data-driven, AC-7)
    assert body["contrast"]["doa_tier"][0]["resolved_tier_id"] == "MANAGER"


async def test_demo_routes_advertised_in_openapi(client: AsyncClient) -> None:
    paths = (await client.get("/openapi.json")).json()["paths"]
    assert "/demo/hero/governance" in paths
    assert "/demo/hero/impact" in paths
