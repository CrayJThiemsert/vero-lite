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


async def test_impact_endpoint_carries_economic_facet(client: AsyncClient) -> None:
    """PLAN-0073 AC-1 (SD-2b): ``GET /demo/hero/impact`` additively carries the typed Box-4
    ``economic_impact`` facet (kind / provisional / assumptions / basis_refs) alongside the
    byte-identical ledger; the facet's ``net_benefit_thb`` EQUALS the ledger's (same
    computation — the producer reuses ``build_hero_impact_ledger``, no drift)."""
    body = (await client.get("/demo/hero/impact")).json()
    facet = body["economic_impact"]
    assert facet is not None
    assert facet["kind"] == "expedite_tradeoff"  # ADR-0030 D3 table
    assert facet["provisional"] is True
    assert facet["assumptions"]  # non-empty disclosed modelling assumptions
    assert len(facet["basis_refs"]) == 4  # the four source CSV columns (OQ-C provenance)
    # the facet ฿ equals the ledger ฿ from the SAME response cycle (validator-backed, no drift)
    assert _money(facet["net_benefit_thb"]) == _money(body["net_benefit_thb"])
    # AC-3 coexistence: the ledger fields are unchanged (the existing exact-ledger test still holds)
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


async def test_governance_endpoint_live_derives_the_same_moment(client: AsyncClient) -> None:
    """``?live=true`` runs the REAL procedure (host-state-free advisory stub) and returns the SAME
    contract with ``source: "live-run"`` — the governance moment DERIVED by the run (the scored_rule
    selects + emits the spend the doa_tier resolves), not the offline shortcut."""
    response = await client.get("/demo/hero/governance?live=true")
    assert response.status_code == 200
    body = response.json()
    assert body["provisional"] is True
    assert body["source"] == "live-run"
    hero = body["hero"]
    assert hero["supplier_id"] == "SUP-RAPIDMRO"  # selected by the scored rule, not the LLM
    assert hero["doa_tier"][0]["resolved_tier_id"] == "CONTROLLER"
    assert hero["amount"] == {"value": "288000", "currency": "THB"}
    kinds = {gd["control_ref"]["kind"] for gd in hero["governed_decision"]}
    assert kinds == {"doa_tier", "sod"}
    # the contrast is the reused deterministic offline case (99k -> MANAGER)
    assert body["contrast"]["doa_tier"][0]["resolved_tier_id"] == "MANAGER"


async def test_demo_routes_advertised_in_openapi(client: AsyncClient) -> None:
    paths = (await client.get("/openapi.json")).json()["paths"]
    assert "/demo/hero/governance" in paths
    assert "/demo/hero/impact" in paths
    assert "/demo/hero/event" in paths


async def test_event_route_wired_as_post(client: AsyncClient) -> None:
    """PLAN-0057 (SD-5, thin route smoke): the event opener is wired as a POST returning the
    HeroGovernanceAudit contract, and it does NOT add mutation to the read-only GET prefix (SD-2).
    Its fire → park → project behaviour is proven at the service layer by
    ``tests/services/db/test_event_hero_opener.py`` — not re-proved over HTTP here."""
    paths = (await client.get("/openapi.json")).json()["paths"]
    event = paths["/demo/hero/event"]
    assert set(event) == {"post"}
    assert event["post"]["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("HeroGovernanceAudit")
    # the read views stay GET-only — the event opener did not mutate the read-only contract.
    assert set(paths["/demo/hero/governance"]) == {"get"}
    assert set(paths["/demo/hero/impact"]) == {"get"}
