"""Offline gate for the read-only ``GET /procedures`` viewer endpoint (PLAN-0039).

The offline test is the GATE (CLAUDE.md §8): ``GET /procedures`` returns every
discovered vertical's procedures, each round-trips ``load_procedures``, and the
catalog archetype label is attached for all **five** shipped procedures across
the four verticals (fact-pack #1: procurement ships two; energy / supply_chain /
aquaculture one each). No LLM, no DB, no mutation. A live preview is *evidence*
(Step 5), not the gate.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from services.api.main import app
from services.engine.discovery import discover_and_register
from services.engine.procedures.spec import load_procedures
from services.engine.registry import registry

# The eight shipped procedures, vertical → {procedure_id: archetype} (fact-pack
# #1 / docs/conventions/procedure-archetypes.md). procurement ships five:
# two manual + the PLAN-0055 Step 8 schedule-triggered AT-2 variant + the
# PLAN-0056 Step 8 event-triggered AT-2 variant + the PLAN-0065 Step 4
# schedule-triggered AT-3 calm-path variant.
_EXPECTED: dict[str, dict[str, str]] = {
    "energy": {"substation_health_sweep": "AT-1"},
    "supply_chain": {"cold_chain_excursion_sweep": "AT-1"},
    "aquaculture": {"morning_pond_health_round": "AT-1b"},
    "procurement": {
        "emergency_sourcing_round": "AT-2",
        "low_stock_reorder_round": "AT-3",
        # PLAN-0055 Step 8 — the schedule-triggered AT-2 variant (nightly, headless).
        "scheduled_emergency_sourcing_round": "AT-2",
        # PLAN-0065 Step 4 — the schedule-triggered AT-3 calm-path variant (nightly, headless).
        "scheduled_low_stock_reorder_round": "AT-3",
        # PLAN-0056 Step 8 — the event-triggered AT-2 variant (asset-failure auto-fire).
        "event_emergency_sourcing_round": "AT-2",
    },
}

# Full coverage of all six gate_kinds is present in the live data, with zero
# fixtures (PLAN-0039 finding #4 / AC-5).
_ALL_GATE_KINDS = {"env_band", "in_file_band", "rule_gate", "scored_rule", "doa_tier", "none"}


@pytest.fixture
async def all_verticals_client() -> AsyncIterator[AsyncClient]:
    """A client with EVERY discovered vertical registered.

    The app lifespan (which calls ``discover_and_register``) does not run under
    httpx.ASGITransport — so we discover explicitly here. The autouse
    ``_reset_registry`` fixture (tests/conftest.py) wipes the registry first, so
    this re-discovers deterministically.
    """
    discover_and_register()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


async def test_procedures_returns_all_discovered_verticals_and_archetypes(
    all_verticals_client: AsyncClient,
) -> None:
    """Every discovered vertical's procedures round-trip load_procedures, each
    carrying the correct catalog archetype — all eight across the four verticals
    (procurement ships five: two manual + scheduled AT-2 + event AT-2 + scheduled AT-3)."""
    response = await all_verticals_client.get("/procedures")
    assert response.status_code == 200
    payload = response.json()

    returned = {v["vertical"] for v in payload["verticals"]}
    # the endpoint loops registry.verticals() (ADR-0023 discovery), not OCT_VERTICAL
    assert returned == set(registry.verticals())
    assert returned == set(_EXPECTED)

    total = 0
    for ventry in payload["verticals"]:
        vname = ventry["vertical"]
        spec = load_procedures(vname)
        # the payload round-trips load_procedures: same procedure ids, in order
        assert [p["procedure_id"] for p in ventry["procedures"]] == [
            p.procedure_id for p in spec.procedures
        ]
        for proc in ventry["procedures"]:
            assert proc["archetype"] == _EXPECTED[vname][proc["procedure_id"]]
            total += 1
    # eight procedures across four verticals: fact-pack #1's five + the PLAN-0055
    # Step 8 scheduled AT-2 + the PLAN-0056 Step 8 event AT-2 + the PLAN-0065 Step 4
    # scheduled AT-3 calm-path variant (all procurement variants)
    assert total == 8


async def test_procedures_all_six_gate_kinds_present(
    all_verticals_client: AsyncClient,
) -> None:
    """The typed facet decomposition serializes through, and all six gate_kinds
    appear in the real data with zero fixtures (AC-5 / finding #4)."""
    payload = (await all_verticals_client.get("/procedures")).json()
    gate_kinds = {
        step["facet"]["decision_condition"]["gate_kind"]
        for ventry in payload["verticals"]
        for proc in ventry["procedures"]
        for step in proc["steps"]
        if (step.get("facet") or {}).get("decision_condition")
    }
    assert gate_kinds == _ALL_GATE_KINDS


async def test_procedures_typed_authoritative_band_passes_through(
    all_verticals_client: AsyncClient,
) -> None:
    """The authoritative typed band (the source of truth, AC-4) is rendered as
    loaded — in-file bands carry their threshold/direction/watch_margin, env
    bands carry their env_var — distinct from the non-authoritative facet prose."""
    payload = (await all_verticals_client.get("/procedures")).json()
    by_vertical = {v["vertical"]: v for v in payload["verticals"]}

    # aquaculture judge: in-file authored band (the source of truth on the Step)
    aqua = by_vertical["aquaculture"]["procedures"][0]
    aqua_judge = next(s for s in aqua["steps"] if s["step_id"] == "judge")
    assert aqua_judge["threshold"] == 4.0
    assert aqua_judge["direction"] == "below"
    assert aqua_judge["watch_margin"] == 1.0
    assert aqua_judge["facet"]["decision_condition"]["gate_kind"] == "in_file_band"

    # energy judge: env band — no in-file threshold, the band source is the env var
    energy_judge = next(
        s for s in by_vertical["energy"]["procedures"][0]["steps"] if s["step_id"] == "judge"
    )
    assert energy_judge["threshold"] is None
    energy_dc = energy_judge["facet"]["decision_condition"]
    assert energy_dc["gate_kind"] == "env_band"
    assert energy_dc["env_var"] == "OCT_RECOMMEND_THRESHOLD"


async def test_procedures_advertised_in_openapi(all_verticals_client: AsyncClient) -> None:
    """GET /openapi.json advertises the new read-only /procedures route."""
    paths = (await all_verticals_client.get("/openapi.json")).json()["paths"]
    assert "/procedures" in paths
