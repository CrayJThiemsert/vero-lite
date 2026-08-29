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

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Literal

import httpx

from services.api.config import settings


class OllamaError(RuntimeError):
    """Raised when an Ollama chat call fails.

    Covers transport failures (connection refused, timeout), non-2xx HTTP
    responses, and malformed response envelopes. The recommender fail-safe
    (PLAN-0006 §6.6 / ADR-010 IN-4) catches this to fall back to the
    deterministic rule path — it must never escape into the runtime loop.
    """


class OllamaUnreachableError(OllamaError):
    """The Ollama host could not be reached — connection refused / connect
    timeout (i.e. MS-S1 MAX is powered off / unreachable), as distinct from a
    reachable host that returned bad JSON or timed out mid-generation.

    It **is an** :class:`OllamaError`, so every existing ``except OllamaError``
    site (the recommender fail-safe, the nl_query translate-catch) keeps
    working unchanged — this is purely additive to the hierarchy. PLAN-0014
    uses the narrower type to drive the "power MS-S1 on" Telegram notification
    while preserving the fail-safe (ADR-010 IN-4).
    """


class OllamaBusyError(OllamaError):
    """The process-wide in-flight cap was already full (PLAN-0100 Step 6, D5(3)).

    A **subclass of** :class:`OllamaError` on purpose: every existing
    ``except OllamaError`` site — the recommender fail-safe, the ``nl_query``
    translate-catch, the phrasing degrade — already routes to the deterministic
    arm and already emits a PLAN-0093 disclosure carrying the exception text. So
    the cap needs no new degrade path; it reuses the one whose whole purpose is
    "the LLM arm did not author this, and here is why".

    That is also why the message below is written for a reader: it is not a log
    line, it lands verbatim in the disclosure a demo visitor can see.
    """


#: Requests currently inside :meth:`OllamaClient.chat`, process-wide.
#:
#: A plain int, not an ``asyncio.Semaphore``, for two reasons. The cap must
#: **fast-fail**, never queue — a visitor who waits behind someone else's
#: 30-second generation experiences a hang, which is the outcome D5(3) exists to
#: prevent; a semaphore's natural verb is ``acquire`` and waiting is its default.
#: And a semaphore is bound to the loop it was created on, so a module-level one
#: breaks across the fresh event loop each test gets.
#:
#: The check-then-increment below is atomic because there is no ``await``
#: between them: asyncio cannot preempt a coroutine mid-statement-sequence.
_inflight: int = 0


def _current_inflight() -> int:
    """Test seam — the live in-flight count."""
    return _inflight


@asynccontextmanager
async def _inflight_slot(limit: int) -> AsyncIterator[None]:
    """Hold one of ``limit`` process-wide LLM slots, or fail fast.

    ``limit <= 0`` disables the cap entirely (the dev default).
    """
    global _inflight
    if limit > 0 and _inflight >= limit:
        raise OllamaBusyError(
            "another request is already using the demo's single LLM slot; "
            "answered from the deterministic path instead"
        )
    _inflight += 1
    try:
        yield
    finally:
        _inflight -= 1


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


#: Which of the two Pattern B calls a :class:`CallMetrics` describes. A literal
#: rather than a free string because the whole point of the record is to keep the
#: reasoning pass and the structuring pass apart — a mistyped role silently merges
#: two profiles that differ by an order of magnitude.
CallRole = Literal["reasoning", "structuring"]


@dataclass(frozen=True)
class CallMetrics:
    """Per-call generation accounting, read off the Ollama response envelope.

    ``done_reason`` is the TRUNCATION ORACLE, and it is why this record exists.
    Ollama reports ``"stop"`` when the model ended on its own and ``"length"``
    when generation ran into ``num_predict``. Without it the only available
    signal is a character count, and a character count cannot tell "the model
    finished and was brief" apart from "the model was cut mid-sentence" — the
    two readings session 261 could only separate by running the same item twice
    at two different caps, because nothing on disk said which had happened.
    ``ChatResult.raw`` already carried this; every consumer dropped it, so no
    artifact in the repo could answer the question.

    The distinction matters beyond tuning. A cap low enough to EMPTY the draft
    fails loudly — no JSON, an unscored item. A cap that merely CLIPS the draft
    lets call 2 structure a partial reasoning into a well-formed envelope: a
    judgment that grades as an ordinary pass or fail while resting on reasoning
    that was cut off. The second failure is the dangerous one precisely because
    it is quiet, and ``done_reason`` is the only thing that makes it visible.

    ``eval_count`` is generated tokens — the model's actual DEMAND, which is what
    a cap should be chosen from. Measuring demand directly beats searching over
    caps: a search returns one pass/fail bit per run and converges on the
    smallest value that happens to work, which is exactly the clipping cap above.
    ``prompt_eval_count`` rides along because a demand number is only
    interpretable next to the input that produced it.

    ``thinking_chars`` is kept apart from ``content_chars`` because in ``full``
    mode the reasoning lands in its own channel; the split is what tells a reader
    whether a long call was long from thinking or from prose.
    """

    role: CallRole
    done_reason: str | None
    eval_count: int | None
    prompt_eval_count: int | None
    content_chars: int
    thinking_chars: int | None

    @property
    def truncated(self) -> bool:
        """True when generation stopped because it hit the cap, not because the model did.

        Keyed on the string Ollama actually returns rather than on a comparison
        against the configured ``num_predict``: the configured value and the
        value the server applied can differ (an env override, a per-model
        default), and a derived answer would then report a truncation the server
        never performed — or miss one it did.
        """
        return self.done_reason == "length"


def call_metrics(result: ChatResult, *, role: CallRole) -> CallMetrics:
    """Read the generation accounting out of one chat response.

    Every field is optional-tolerant. Ollama versions differ in what they put in
    the envelope, and a missing counter must degrade to ``None`` — a metrics
    record that raised would turn a benchmark sweep into a crash over a field
    nothing scores. ``None`` is honest and reads as absent downstream; a zero
    would be a measurement that never happened wearing the shape of one that did.
    """
    raw = result.raw
    done_reason = raw.get("done_reason")
    eval_count = raw.get("eval_count")
    prompt_eval_count = raw.get("prompt_eval_count")
    return CallMetrics(
        role=role,
        done_reason=done_reason if isinstance(done_reason, str) else None,
        eval_count=eval_count if isinstance(eval_count, int) else None,
        prompt_eval_count=prompt_eval_count if isinstance(prompt_eval_count, int) else None,
        content_chars=len(result.content),
        thinking_chars=len(result.thinking) if result.thinking is not None else None,
    )


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
        think: bool | str | None = None,
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
            # `num_predict` bounds generation SERVER-side. Without it Ollama
            # generates until the context is exhausted, so the only thing bounding
            # a call was the client-side timeout — which aborts and DISCARDS every
            # token already produced. That is why phase 1.6's deadline breaches
            # recorded no answer at all instead of a short one that could still be
            # graded: the run was cut, not bounded, and what it would have said is
            # unknowable. Sits beside `temperature` rather than in a per-call
            # argument for the same reason the in-flight cap is read here — eight
            # call sites construct a client, and a bound that must be passed
            # correctly at each of them is one forgotten argument from being off.
            "options": {
                "temperature": temperature,
                "num_predict": settings.llm_max_output_tokens,
            },
            # Nothing set this before, so every chat call inherited Ollama's own
            # 5-minute default and the model was evicted between visitors. On the
            # published demo that is not a latency detail: PLAN-0100 Step 11
            # measured a ~22 s cold load against a 25 s request timeout, so the
            # first visitor after any quiet spell waited the whole timeout and
            # then got a DEGRADED, ungrounded answer — on the one surface whose
            # headline is natural-language query.
            #
            # Reuses `ollama_keep_alive` — the knob /warm and the Telegram ping
            # already drive — rather than adding a chat-specific twin. A warm that
            # says 30m while chat says something else is a warm that ordinary
            # traffic can silently undo.
            "keep_alive": settings.ollama_keep_alive,
        }
        if think is not None:
            body["think"] = think
        if response_format is not None:
            body["format"] = response_format

        # The in-flight cap is read HERE rather than injected per client, because
        # eight call sites construct an OllamaClient and a cap that has to be
        # passed correctly at each of them is a cap that is one forgotten argument
        # away from being silently off. One chokepoint cannot be bypassed.
        #
        # Pattern B's two calls (reason, then structure) each take and release a
        # slot in turn; they are sequential, so a request never blocks itself.
        async with _inflight_slot(settings.llm_max_inflight):
            payload = await self._request_json("POST", "/api/chat", json=body)
        return _parse_chat_payload(payload, self._model)

    async def _request_json(
        self, method: str, path: str, *, json: dict[str, Any] | None = None
    ) -> Any:
        """Issue one request to the Ollama host and return the parsed JSON body.

        Connection failures (host down / connect timeout) map to
        :class:`OllamaUnreachableError`; every other transport, HTTP-status, or
        JSON failure maps to :class:`OllamaError`. Callers can therefore tell
        "MS-S1 is unreachable" (PLAN-0014 notify) apart from "reachable but
        errored", while the single ``except OllamaError`` contract still holds.
        """
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                transport=self._transport,
            ) as client:
                response = await client.request(method, path, json=json)
                response.raise_for_status()
                return response.json()
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            raise OllamaUnreachableError(
                f"Ollama host {self._base_url!r} is unreachable: {exc}"
            ) from exc
        except httpx.HTTPError as exc:
            raise OllamaError(f"Ollama call to {path} failed: {exc}") from exc
        except ValueError as exc:  # json.JSONDecodeError is a ValueError
            raise OllamaError(f"Ollama returned a non-JSON body: {exc}") from exc

    async def warm(self, *, keep_alive: str | int) -> dict[str, Any]:
        """Load the model into memory via ``/api/generate`` with no prompt.

        Ollama loads the model and returns immediately (``done_reason="load"``)
        without generating; ``keep_alive`` sets how long it stays resident.
        Raises :class:`OllamaUnreachableError` when the host is unreachable.
        """
        payload = await self._request_json(
            "POST", "/api/generate", json={"model": self._model, "keep_alive": keep_alive}
        )
        return payload if isinstance(payload, dict) else {}

    async def unload(self) -> dict[str, Any]:
        """Evict the model from memory immediately (``keep_alive=0``).

        Ollama returns ``done_reason="unload"``. Raises
        :class:`OllamaUnreachableError` when the host is unreachable.
        """
        payload = await self._request_json(
            "POST", "/api/generate", json={"model": self._model, "keep_alive": 0}
        )
        return payload if isinstance(payload, dict) else {}

    async def ps(self) -> list[dict[str, Any]]:
        """Return the models currently resident in memory (``GET /api/ps``)."""
        payload = await self._request_json("GET", "/api/ps")
        models = payload.get("models") if isinstance(payload, dict) else None
        return models if isinstance(models, list) else []


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
