"""Action-loop endpoint tests (PLAN-0005 §7.5).

Lesson #7 §3: every assertion is on response JSON + HTTP status via
httpx.ASGITransport — never a shell exit code.
"""

from __future__ import annotations

from datetime import datetime

from httpx import AsyncClient

from services.api.config import settings


async def test_health_still_ok(client: AsyncClient) -> None:
    """Regression: GET /health is preserved by the three-layer wiring."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_list_objects_returns_assets(client: AsyncClient) -> None:
    """The ingress endpoint returns Asset objects from the energy adapter."""
    response = await client.get("/objects/Asset")
    assert response.status_code == 200
    body = response.json()
    assert body["object_type"] == "Asset"
    assert body["count"] >= 1


async def test_list_recommendations_has_proposed(client: AsyncClient) -> None:
    """GET /recommendations derives at least one proposed action."""
    response = await client.get("/recommendations")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] >= 1
    assert all(rec["status"] == "proposed" for rec in body["recommendations"])


async def test_approve_transitions_to_approved(client: AsyncClient) -> None:
    """POST .../approve moves a recommendation proposed -> approved."""
    recs = (await client.get("/recommendations")).json()["recommendations"]
    action_id = recs[0]["action_id"]
    response = await client.post(f"/recommendations/{action_id}/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


async def test_approve_unknown_returns_404(client: AsyncClient) -> None:
    """Approving an unknown action id is a 404."""
    response = await client.post("/recommendations/nonexistent/approve")
    assert response.status_code == 404


async def test_execute_without_approval_returns_409(client_with_db: AsyncClient) -> None:
    """Executing a still-proposed action is a documented 409."""
    recs = (await client_with_db.get("/recommendations")).json()["recommendations"]
    action_id = recs[0]["action_id"]
    response = await client_with_db.post(f"/recommendations/{action_id}/execute")
    assert response.status_code == 409


async def test_execute_transitions_to_executed(client_with_db: AsyncClient) -> None:
    """The full approve -> execute path ends executed with a handler receipt."""
    recs = (await client_with_db.get("/recommendations")).json()["recommendations"]
    action_id = recs[0]["action_id"]
    await client_with_db.post(f"/recommendations/{action_id}/approve")
    response = await client_with_db.post(f"/recommendations/{action_id}/execute")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "executed"
    assert body["handler_receipt"]["executed"] is True


async def test_recommendations_start_without_decision_timestamps(client: AsyncClient) -> None:
    """PLAN-0015 D3: a proposed recommendation has no approved/executed time yet."""
    rec = (await client.get("/recommendations")).json()["recommendations"][0]
    assert rec["approved_at"] is None
    assert rec["executed_at"] is None


async def test_decision_timestamps_recorded_on_approve_execute(
    client_with_db: AsyncClient,
) -> None:
    """PLAN-0015 AC-decision-time: approve + execute stamp real, ordered times."""
    recs = (await client_with_db.get("/recommendations")).json()["recommendations"]
    action_id = recs[0]["action_id"]
    await client_with_db.post(f"/recommendations/{action_id}/approve")
    await client_with_db.post(f"/recommendations/{action_id}/execute")

    after = (await client_with_db.get("/recommendations")).json()["recommendations"]
    rec = next(r for r in after if r["action_id"] == action_id)
    assert rec["status"] == "executed"
    assert rec["approved_at"] is not None
    assert rec["executed_at"] is not None
    approved = datetime.fromisoformat(rec["approved_at"])
    executed = datetime.fromisoformat(rec["executed_at"])
    assert approved <= executed


async def test_recovery_reading_injected_on_execute(client_with_db: AsyncClient) -> None:
    """PLAN-0015 AC-recovery-on-execute: no recovery before, present after."""
    before = (await client_with_db.get("/objects/OperationalEvent")).json()["objects"]
    assert all(e.get("event_id") != "event-recovery-01" for e in before)

    recs = (await client_with_db.get("/recommendations")).json()["recommendations"]
    action_id = recs[0]["action_id"]
    await client_with_db.post(f"/recommendations/{action_id}/approve")
    await client_with_db.post(f"/recommendations/{action_id}/execute")

    after = (await client_with_db.get("/objects/OperationalEvent")).json()["objects"]
    recovery = [e for e in after if e.get("event_id") == "event-recovery-01"]
    assert len(recovery) == 1
    assert recovery[0]["measured_value"] == settings.oct_recovery_value
    assert recovery[0]["severity"] == "info"
    # the recovery lands on the breach event's asset (energy: Battery Bank A)
    assert recovery[0]["asset_id"] == "asset-battery-01"


async def test_openapi_lists_action_routes(client: AsyncClient) -> None:
    """GET /openapi.json advertises the new action-loop routes."""
    paths = (await client.get("/openapi.json")).json()["paths"]
    assert "/objects/{object_type}" in paths
    assert "/recommendations" in paths
    assert "/recommendations/{action_id}/approve" in paths
    assert "/recommendations/{action_id}/execute" in paths


async def test_recommendations_carry_reasoning_trace_and_entities(client: AsyncClient) -> None:
    """PLAN-0013 1a: /recommendations exposes the reasoning trace + affected entities."""
    body = (await client.get("/recommendations")).json()
    rec = body["recommendations"][0]
    assert isinstance(rec["reasoning_trace"], list) and len(rec["reasoning_trace"]) >= 1
    assert {"step_id", "kind", "summary"} <= set(rec["reasoning_trace"][0])
    assert isinstance(rec["affected_entities"], list) and len(rec["affected_entities"]) >= 1
    assert {"object_type", "primary_key"} <= set(rec["affected_entities"][0])


async def test_meta_returns_ontology_driven_types(client: AsyncClient) -> None:
    """PLAN-0013 1b: GET /meta serves ontology metadata (types/title_key/enums/links)."""
    body = (await client.get("/meta")).json()
    assert body["vertical"] == "energy"
    types = {t["name"]: t for t in body["object_types"]}
    assert {"Asset", "Site"} <= set(types)
    asset = types["Asset"]
    assert asset["title_key"] == "name"
    assert asset["primary_key"] == "asset_id"
    props = {p["name"]: p for p in asset["properties"]}
    # energy-v1 (PLAN-0049 Step 1, F9): distribution-utility asset types added.
    assert props["asset_type"]["enum"] == [
        "battery",
        "inverter",
        "meter",
        "transformer",
        "feeder",
        "cap_bank",
        "gas_engine",
    ]
    assert any(
        link["from_type"] == "Asset" and link["to_type"] == "Site" for link in body["link_types"]
    )


async def test_meta_advertised_in_openapi(client: AsyncClient) -> None:
    """GET /openapi.json advertises the new /meta route."""
    paths = (await client.get("/openapi.json")).json()["paths"]
    assert "/meta" in paths
