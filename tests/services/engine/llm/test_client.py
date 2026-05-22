"""Tests for the async Ollama client (PLAN-0006 Step 1 / §7.2 client construction).

Lesson #7 §3: in-process assertions on returned objects and on the
request body captured by a fake transport — no live network, no ``$?``.
``httpx.MockTransport`` is the offline injection seam built into the
client.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from services.engine.llm.client import ChatResult, OllamaClient, OllamaError

Handler = Callable[[httpx.Request], httpx.Response]


def _client(
    handler: Handler,
    *,
    model: str = "gpt-oss:20b",
    base_url: str = "http://ollama.test",
) -> OllamaClient:
    """Build an OllamaClient wired to a fake transport."""
    return OllamaClient(base_url=base_url, model=model, transport=httpx.MockTransport(handler))


def _ok_response(content: str = "draft text", thinking: str | None = None) -> httpx.Response:
    """A well-formed Ollama /api/chat 200 response."""
    message: dict[str, Any] = {"role": "assistant", "content": content}
    if thinking is not None:
        message["thinking"] = thinking
    return httpx.Response(200, json={"model": "gpt-oss:20b", "message": message, "done": True})


async def test_chat_parses_content_thinking_and_model() -> None:
    """§7.2: a well-formed response round-trips into a ChatResult."""
    client = _client(lambda _req: _ok_response(content="hello", thinking="because reasons"))
    result = await client.chat([{"role": "user", "content": "hi"}])

    assert isinstance(result, ChatResult)
    assert result.content == "hello"
    assert result.thinking == "because reasons"
    assert result.model == "gpt-oss:20b"
    assert result.raw["done"] is True


async def test_chat_posts_to_api_chat_with_model_and_stream_false() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return _ok_response()

    await _client(handler).chat([{"role": "user", "content": "hi"}])

    assert captured["url"] == "http://ollama.test/api/chat"
    assert captured["body"]["model"] == "gpt-oss:20b"
    assert captured["body"]["stream"] is False
    assert captured["body"]["messages"] == [{"role": "user", "content": "hi"}]


async def test_chat_includes_think_only_when_set() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return _ok_response()

    client = _client(handler)
    await client.chat([{"role": "user", "content": "hi"}], think=True)
    assert captured["body"]["think"] is True

    await client.chat([{"role": "user", "content": "hi"}])
    assert "think" not in captured["body"]


async def test_chat_includes_format_only_when_set() -> None:
    captured: dict[str, Any] = {}
    schema: dict[str, Any] = {"type": "object", "properties": {"x": {"type": "string"}}}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return _ok_response()

    client = _client(handler)
    await client.chat([{"role": "user", "content": "hi"}], response_format=schema)
    assert captured["body"]["format"] == schema

    await client.chat([{"role": "user", "content": "hi"}])
    assert "format" not in captured["body"]


async def test_chat_thinking_is_none_when_absent() -> None:
    """A non-thinking call (no 'thinking' field) yields thinking=None."""
    client = _client(lambda _req: _ok_response(content="draft"))
    result = await client.chat([{"role": "user", "content": "hi"}])
    assert result.thinking is None


async def test_chat_raises_ollama_error_on_http_status_error() -> None:
    client = _client(lambda _req: httpx.Response(500, text="internal error"))
    with pytest.raises(OllamaError):
        await client.chat([{"role": "user", "content": "hi"}])


async def test_chat_raises_ollama_error_on_transport_error() -> None:
    """A connection failure surfaces as OllamaError, never a raw httpx error."""

    def handler(_req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    with pytest.raises(OllamaError):
        await _client(handler).chat([{"role": "user", "content": "hi"}])


async def test_chat_raises_ollama_error_on_missing_message() -> None:
    client = _client(lambda _req: httpx.Response(200, json={"done": True}))
    with pytest.raises(OllamaError):
        await client.chat([{"role": "user", "content": "hi"}])


async def test_chat_raises_ollama_error_on_non_string_content() -> None:
    client = _client(lambda _req: httpx.Response(200, json={"message": {"content": 123}}))
    with pytest.raises(OllamaError):
        await client.chat([{"role": "user", "content": "hi"}])


async def test_base_url_trailing_slash_is_normalised() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return _ok_response()

    await _client(handler, base_url="http://ollama.test/").chat([{"role": "user", "content": "hi"}])
    assert captured["url"] == "http://ollama.test/api/chat"
