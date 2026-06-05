"""Tests for the read-only GET /llm/status residency probe (PLAN-0018).

The route's `_status_client()` is monkeypatched to an OllamaClient wired to an
`httpx.MockTransport`, so the full route → client → transport path runs offline.
Proves the PLAN-0018 acceptance criteria:

- AC-1 / INV-1 — the poll issues **only** GET /api/ps, never /api/generate.
- AC-2 / INV-2 — non-destructive + idempotent across repeated polls.
- AC-3 / R1+R10 — unreachable / cold / resident / error disambiguated; a
  reachable-but-errored host is never reported `cold`.
- AC-4 / R2 — residency is judged for the configured model with tolerant tag
  matching; a foreign model is not `resident`.
- AC-5 / R3 — the probe uses a short, dedicated timeout decoupled from the
  generation timeout.
- AC-6 / R8 — an expired keep_alive entry is reported `cold`, not `resident`;
  a live one surfaces remaining time.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from services.api.config import settings
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


# --- AC-1 / INV-1: the poll only ever hits GET /api/ps -----------------------


async def test_status_polls_only_ps_never_generate(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        if request.url.path == "/api/ps":
            return httpx.Response(200, json={"models": [{"name": "gpt-oss:20b"}]})
        return httpx.Response(404)

    monkeypatch.setattr(admin, "_status_client", lambda: _ollama(handler))
    res = await http.get("/llm/status")

    assert res.status_code == 200
    assert seen == [("GET", "/api/ps")]
    assert all(path != "/api/generate" for _, path in seen)


# --- AC-2 / INV-2: idempotent + non-destructive across repeated polls ---------


async def test_status_idempotent_across_polls(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        return httpx.Response(200, json={"models": [{"name": "gpt-oss:20b"}]})

    monkeypatch.setattr(admin, "_status_client", lambda: _ollama(handler))
    first = (await http.get("/llm/status")).json()
    second = (await http.get("/llm/status")).json()

    assert first["state"] == second["state"] == "resident"
    assert set(seen) == {"/api/ps"}  # only the read path, both polls


# --- AC-3 / R1+R10: state disambiguation, never a false cold ------------------


async def test_status_unreachable(monkeypatch: pytest.MonkeyPatch, http: AsyncClient) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("MS-S1 down")

    monkeypatch.setattr(admin, "_status_client", lambda: _ollama(handler))
    body = (await http.get("/llm/status")).json()

    assert body["state"] == "unreachable"
    assert body["reachable"] is False
    assert body["detail"]


async def test_status_cold_when_no_model_resident(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    monkeypatch.setattr(
        admin,
        "_status_client",
        lambda: _ollama(lambda _r: httpx.Response(200, json={"models": []})),
    )
    body = (await http.get("/llm/status")).json()

    assert body["state"] == "cold"
    assert body["reachable"] is True


async def test_status_resident_when_model_loaded(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    monkeypatch.setattr(
        admin,
        "_status_client",
        lambda: _ollama(lambda _r: httpx.Response(200, json={"models": [{"name": "gpt-oss:20b"}]})),
    )
    body = (await http.get("/llm/status")).json()

    assert body["state"] == "resident"
    assert body["reachable"] is True


async def test_status_bad_json_is_error_not_cold(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    monkeypatch.setattr(
        admin,
        "_status_client",
        lambda: _ollama(lambda _r: httpx.Response(200, content=b"not json")),
    )
    body = (await http.get("/llm/status")).json()

    assert body["state"] == "error"
    assert body["state"] != "cold"  # R10: reachable-but-errored is never painted cold
    assert body["reachable"] is True
    assert body["detail"]


async def test_status_5xx_is_error_not_cold(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    monkeypatch.setattr(
        admin,
        "_status_client",
        lambda: _ollama(lambda _r: httpx.Response(503)),
    )
    body = (await http.get("/llm/status")).json()

    assert body["state"] == "error"
    assert body["state"] != "cold"
    assert body["reachable"] is True


# --- AC-4 / R2: right-model residency with tolerant tag matching --------------


async def test_status_foreign_model_is_cold(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    monkeypatch.setattr(
        admin,
        "_status_client",
        lambda: _ollama(lambda _r: httpx.Response(200, json={"models": [{"name": "llama3:8b"}]})),
    )
    body = (await http.get("/llm/status")).json()

    assert body["state"] == "cold"  # a foreign resident model is not "resident"


@pytest.mark.parametrize("resident_name", ["gpt-oss:20b", "gpt-oss", "gpt-oss:latest"])
async def test_status_tolerant_tag_match_is_resident(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient, resident_name: str
) -> None:
    monkeypatch.setattr(
        admin,
        "_status_client",
        lambda: _ollama(lambda _r: httpx.Response(200, json={"models": [{"name": resident_name}]})),
    )
    body = (await http.get("/llm/status")).json()

    assert body["state"] == "resident"


async def test_status_matches_on_model_field_too(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    # Some Ollama versions key the entry as "model" rather than "name".
    monkeypatch.setattr(
        admin,
        "_status_client",
        lambda: _ollama(
            lambda _r: httpx.Response(200, json={"models": [{"model": "gpt-oss:20b"}]})
        ),
    )
    body = (await http.get("/llm/status")).json()

    assert body["state"] == "resident"


# --- AC-5 / R3: short, dedicated probe timeout decoupled from generation ------


def test_status_client_uses_short_decoupled_timeout() -> None:
    client = admin._status_client()
    assert client._timeout == settings.llm_status_timeout_s
    assert settings.llm_status_timeout_s < settings.llm_request_timeout_s


# --- AC-6 / R8: expiry honesty -----------------------------------------------


async def test_status_expired_entry_is_cold(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    monkeypatch.setattr(
        admin,
        "_status_client",
        lambda: _ollama(
            lambda _r: httpx.Response(
                200,
                json={
                    "models": [{"name": "gpt-oss:20b", "expires_at": "2020-01-01T00:00:00+00:00"}]
                },
            )
        ),
    )
    body = (await http.get("/llm/status")).json()

    assert body["state"] == "cold"  # listed but past keep_alive → honest cold


async def test_status_resident_surfaces_remaining(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    monkeypatch.setattr(
        admin,
        "_status_client",
        lambda: _ollama(
            lambda _r: httpx.Response(
                200,
                json={
                    "models": [{"name": "gpt-oss:20b", "expires_at": "2099-01-01T00:00:00+00:00"}]
                },
            )
        ),
    )
    body = (await http.get("/llm/status")).json()

    assert body["state"] == "resident"
    assert body["expires_at"] == "2099-01-01T00:00:00+00:00"
    assert body["seconds_remaining"] is not None
    assert body["seconds_remaining"] > 0
