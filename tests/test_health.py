"""Smoke test for /health endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from services.api.main import app


@pytest.mark.asyncio
async def test_health_returns_200() -> None:
    """GET /health must return 200 with valid HealthResponse."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert data["version"] == "0.1.0"
