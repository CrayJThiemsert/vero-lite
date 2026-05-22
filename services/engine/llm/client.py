"""Async Ollama chat client for the LLM reasoning hook (PLAN-0006 Step 1).

A thin wrapper over the Ollama ``/api/chat`` endpoint (ADR-002 — the
MS-S1 MAX local server). It is **Pattern B capable** (PLAN-0006 SD-2): a
single :meth:`OllamaClient.chat` carries both an optional ``think`` flag
(call 1 reasons) and an optional ``response_format`` JSON Schema (call 2
emits the constrained envelope). Orchestrating the two calls is the job of
the higher layers (``structured.py`` / ``recommender.py``), not of this
client.

CHECKPOINT-0 caller contract (PLAN-0006 Step 0 / ADR-010 IN-1)
--------------------------------------------------------------
The Step 0 spike verified, on Ollama 0.24.0, that the pinned model
``gpt-oss:20b`` honours the ``format`` JSON-schema constraint under every
``think`` setting — but that the Qwen3.x family still exhibits Ollama
issue #15260 (``think=false`` together with ``format`` silently drops the
schema constraint, yielding free-text prose). The structuring call must
therefore **never pair ``think=False`` with ``response_format``**; callers
omit ``think`` on the structuring call. This client does not enforce the
rule — it is a documented caller contract, repeated in ``structured.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


class OllamaError(RuntimeError):
    """Raised when an Ollama chat call fails.

    Covers transport failures (connection refused, timeout), non-2xx HTTP
    responses, and malformed response envelopes. The recommender fail-safe
    (PLAN-0006 §6.6 / ADR-010 IN-4) catches this to fall back to the
    deterministic rule path — it must never escape into the runtime loop.
    """


@dataclass(frozen=True)
class ChatResult:
    """The parsed result of one Ollama chat call.

    ``thinking`` is populated only when the model ran with thinking enabled
    (Pattern B call 1); it becomes the ``llm_inference`` reasoning
    narrative (ADR-010 D3). ``content`` is the assistant message body — a
    draft on call 1, the schema-constrained envelope JSON on call 2.
    """

    content: str
    thinking: str | None
    model: str
    raw: dict[str, Any]


class OllamaClient:
    """Async Ollama ``/api/chat`` wrapper bound to one model + base URL."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout: float = 120.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """Create a client.

        ``transport`` is an injection seam for tests — pass an
        :class:`httpx.MockTransport` to exercise the client offline; the
        production path leaves it ``None`` (httpx's default transport).
        """
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._transport = transport

    @property
    def model(self) -> str:
        """The model this client is bound to."""
        return self._model

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        """Run one chat completion against the Ollama server.

        ``think`` toggles the model's reasoning pass (Pattern B call 1 sets
        it ``True``). ``response_format`` is a JSON Schema supplied as the
        Ollama ``format`` field for constrained generation (Pattern B call
        2). Per the CHECKPOINT-0 contract above, callers must not pass
        ``think=False`` together with ``response_format``.

        Raises :class:`OllamaError` on any transport, HTTP, or
        response-envelope failure.
        """
        body: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if think is not None:
            body["think"] = think
        if response_format is not None:
            body["format"] = response_format

        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                transport=self._transport,
            ) as client:
                response = await client.post("/api/chat", json=body)
                response.raise_for_status()
                payload: Any = response.json()
        except httpx.HTTPError as exc:
            raise OllamaError(f"Ollama chat call failed: {exc}") from exc
        except ValueError as exc:  # json.JSONDecodeError is a ValueError
            raise OllamaError(f"Ollama returned a non-JSON body: {exc}") from exc

        return _parse_chat_payload(payload, self._model)


def _parse_chat_payload(payload: Any, model: str) -> ChatResult:
    """Validate the Ollama ``/api/chat`` response shape into a ChatResult."""
    if not isinstance(payload, dict):
        raise OllamaError(f"Ollama returned an unexpected body type: {type(payload).__name__}")
    message = payload.get("message")
    if not isinstance(message, dict):
        raise OllamaError("Ollama response is missing a 'message' object")

    content = message.get("content")
    if not isinstance(content, str):
        raise OllamaError("Ollama response 'message.content' is not a string")

    thinking_raw = message.get("thinking")
    thinking = thinking_raw if isinstance(thinking_raw, str) and thinking_raw else None

    return ChatResult(content=content, thinking=thinking, model=model, raw=payload)
