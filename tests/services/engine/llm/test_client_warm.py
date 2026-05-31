"""Tests for OllamaClient.warm/unload/ps + OllamaUnreachableError (PLAN-0014).

Same offline `httpx.MockTransport` seam as test_client.py. The load-bearing
checks: warm/unload hit `/api/generate` with the right `keep_alive`; a connect
failure raises the **narrower** `OllamaUnreachableError` (still an
`OllamaError`), while an HTTP 500 / read-timeout raises only the base
`OllamaError` — so a reachable-but-slow (warming) box never looks "unreachable".
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from services.engine.llm.client import OllamaClient, OllamaError, OllamaUnreachableError

Handler = Callable[[httpx.Request], httpx.Response]


def _client(handler: Handler, *, base_url: str = "http://ollama.test") -> OllamaClient:
    return OllamaClient(
        base_url=base_url, model="gpt-oss:20b", transport=httpx.MockTransport(handler)
    )


async def test_warm_posts_generate_with_model_and_keep_alive() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200, json={"model": "gpt-oss:20b", "done": True, "done_reason": "load"}
        )

    result = await _client(handler).warm(keep_alive="30m")

    assert captured["url"] == "http://ollama.test/api/generate"
    assert captured["body"] == {"model": "gpt-oss:20b", "keep_alive": "30m"}
    assert result["done_reason"] == "load"


async def test_unload_posts_generate_keep_alive_zero() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200, json={"model": "gpt-oss:20b", "done": True, "done_reason": "unload"}
        )

    result = await _client(handler).unload()

    assert captured["body"] == {"model": "gpt-oss:20b", "keep_alive": 0}
    assert result["done_reason"] == "unload"


async def test_ps_returns_models_list() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "http://ollama.test/api/ps"
        return httpx.Response(200, json={"models": [{"name": "gpt-oss:20b"}]})

    assert await _client(handler).ps() == [{"name": "gpt-oss:20b"}]


async def test_ps_empty_when_no_models() -> None:
    assert await _client(lambda _r: httpx.Response(200, json={"models": []})).ps() == []


async def test_connect_error_on_warm_raises_unreachable() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    with pytest.raises(OllamaUnreachableError):
        await _client(handler).warm(keep_alive="30m")


async def test_connect_timeout_on_ps_raises_unreachable() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("connect timed out")

    with pytest.raises(OllamaUnreachableError):
        await _client(handler).ps()


async def test_unreachable_is_an_ollama_error_on_chat() -> None:
    """OllamaUnreachableError is an OllamaError — existing except sites still catch it."""

    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    with pytest.raises(OllamaError):
        await _client(handler).chat([{"role": "user", "content": "hi"}])


async def test_http_500_raises_base_error_not_unreachable() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    with pytest.raises(OllamaError) as exc_info:
        await _client(handler).warm(keep_alive="30m")
    assert not isinstance(exc_info.value, OllamaUnreachableError)


async def test_read_timeout_is_not_unreachable() -> None:
    """A reachable-but-slow (warming) box read-times-out — base error, NOT unreachable."""

    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("read timed out")

    with pytest.raises(OllamaError) as exc_info:
        await _client(handler).warm(keep_alive="30m")
    assert not isinstance(exc_info.value, OllamaUnreachableError)
