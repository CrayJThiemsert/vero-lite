"""Static-UI serving tests (PLAN-0013 Step 5).

The Claude-Design OCT demo UI is served same-origin from FastAPI (OQ-4 —
one process, one URL, no CORS). These assert the static mount serves the
SPA + its assets, and — critically — that mounting it at "/" did NOT
shadow the API routes the UI fetches (Lesson #7 §3: assert on response
status + content-type, not shell exit codes).
"""

from __future__ import annotations

from httpx import AsyncClient


async def test_root_serves_the_oct_ui(client: AsyncClient) -> None:
    """GET / serves the OCT single-page UI (index.html)."""
    response = await client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert "OCT" in body
    assert "assets/app.js" in body  # the SPA bootstraps its asset bundle


async def test_assets_are_served(client: AsyncClient) -> None:
    """The UI's JS/CSS bundle is reachable under /assets/."""
    js = await client.get("/assets/app.js")
    assert js.status_code == 200
    assert "OCT" in js.text  # the app bootstrap
    css = await client.get("/assets/theme.css")
    assert css.status_code == 200


async def test_static_mount_does_not_shadow_api(client: AsyncClient) -> None:
    """The "/" static mount must NOT shadow the JSON API routes the UI calls."""
    health = await client.get("/health")
    assert health.status_code == 200
    assert health.headers["content-type"].startswith("application/json")
    assert health.json()["status"] == "ok"

    meta = await client.get("/meta")
    assert meta.status_code == 200
    assert meta.headers["content-type"].startswith("application/json")
    assert meta.json()["vertical"] == "energy"


async def test_openapi_still_reachable(client: AsyncClient) -> None:
    """The OpenAPI schema (and the routes it lists) survive the static mount."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert {"/meta", "/recommendations", "/query"} <= set(paths)


async def test_unknown_path_is_404_not_500(client: AsyncClient) -> None:
    """An unknown path falls through the static mount to a clean 404."""
    response = await client.get("/no-such-asset.js")
    assert response.status_code == 404
