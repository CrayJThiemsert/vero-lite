"""Tests for the GET /warm + GET /sleep admin routes (PLAN-0014).

The route's `_client()` is monkeypatched to an OllamaClient wired to an
`httpx.MockTransport`, so the full route → client → transport path runs
offline. Covers blocking warm, `?wait=false`, unload, and the 503-on-
unreachable contract.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from services.api.main import app
from services.api.routers import admin
from services.engine.llm.client import OllamaClient


def _ollama(handler: object) -> OllamaClient:
    return OllamaClient(
        base_url="http://ollama.test",
        model="gpt-oss:20b",
        transport=httpx.MockTransport(handler),  # type: ignore[arg-type]
    )


@pytest.fixture
async def http() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def test_warm_blocking_reports_loaded(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/generate":
            return httpx.Response(200, json={"done_reason": "load"})
        if request.url.path == "/api/ps":
            return httpx.Response(200, json={"models": [{"name": "gpt-oss:20b"}]})
        return httpx.Response(404)

    monkeypatch.setattr(admin, "_client", lambda: _ollama(handler))
    res = await http.get("/warm")

    assert res.status_code == 200
    body = res.json()
    assert body["loaded"] is True
    assert body["done_reason"] == "load"
    assert body["ps"] == [{"name": "gpt-oss:20b"}]


async def test_warm_wait_false_returns_immediately(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    monkeypatch.setattr(
        admin,
        "_client",
        lambda: _ollama(lambda _r: httpx.Response(200, json={"done_reason": "load"})),
    )
    res = await http.get("/warm?wait=false")

    assert res.status_code == 200
    assert res.json()["warming"] is True


async def test_warm_503_when_unreachable(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("MS-S1 down")

    monkeypatch.setattr(admin, "_client", lambda: _ollama(handler))
    res = await http.get("/warm")

    assert res.status_code == 503
    assert res.json()["detail"]["reachable"] is False


async def test_sleep_reports_unloaded(monkeypatch: pytest.MonkeyPatch, http: AsyncClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/generate":
            return httpx.Response(200, json={"done_reason": "unload"})
        if request.url.path == "/api/ps":
            return httpx.Response(200, json={"models": []})
        return httpx.Response(404)

    monkeypatch.setattr(admin, "_client", lambda: _ollama(handler))
    res = await http.get("/sleep")

    assert res.status_code == 200
    body = res.json()
    assert body["unloaded"] is True
    assert body["done_reason"] == "unload"


async def test_sleep_503_when_unreachable(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("MS-S1 down")

    monkeypatch.setattr(admin, "_client", lambda: _ollama(handler))
    res = await http.get("/sleep")

    assert res.status_code == 503
    assert res.json()["detail"]["reachable"] is False
