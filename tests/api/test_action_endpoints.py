"""Action-loop endpoint tests (PLAN-0005 §7.5).

Lesson #7 §3: every assertion is on response JSON + HTTP status via
httpx.ASGITransport — never a shell exit code.
"""

from __future__ import annotations

from httpx import AsyncClient


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


async def test_openapi_lists_action_routes(client: AsyncClient) -> None:
    """GET /openapi.json advertises the new action-loop routes."""
    paths = (await client.get("/openapi.json")).json()["paths"]
    assert "/objects/{object_type}" in paths
    assert "/recommendations" in paths
    assert "/recommendations/{action_id}/approve" in paths
    assert "/recommendations/{action_id}/execute" in paths
