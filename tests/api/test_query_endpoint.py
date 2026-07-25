"""NL-query endpoint tests (PLAN-0013 Step 2).

Drives ``POST /query`` end-to-end through the ASGI app with the LLM
backend monkeypatched to a deterministic stub — no live Ollama. Asserts
on response JSON + status only (Lesson #7 §3).
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from httpx import AsyncClient

from services.engine.llm.client import ChatResult, OllamaError


class _StubQueryClient:
    """Translate (carries response_format) → query JSON; phrase → text."""

    def __init__(self, query: dict[str, Any], phrase: str = "Grounded answer.") -> None:
        self._query_json = json.dumps(query)
        self._phrase = phrase

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        content = self._query_json if response_format is not None else self._phrase
        return ChatResult(content=content, thinking=None, model="stub", raw={})


def _use_stub(
    monkeypatch: pytest.MonkeyPatch, query: dict[str, Any], phrase: str = "Grounded answer."
) -> None:
    stub = _StubQueryClient(query, phrase)
    monkeypatch.setattr("services.engine.nl_query._build_chat_client", lambda: stub)


async def test_query_returns_grounded_answer(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """POST /query answers from real data and returns the grounding receipt."""
    _use_stub(
        monkeypatch,
        {"object_type": "Asset", "operation": "count"},
        phrase="There are 4 assets under management.",
    )
    response = await client.post("/query", json={"question": "how many assets are there?"})
    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is True
    assert body["result_count"] == 4
    assert body["structured_query"]["object_type"] == "Asset"
    assert len(body["source_object_ids"]) == 4
    assert body["answer"] == "There are 4 assets under management."


async def test_query_no_data_returns_no_invented_fact(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A question with no supporting data returns a no-data answer, never invention."""
    _use_stub(
        monkeypatch,
        {
            "object_type": "Asset",
            "operation": "list",
            "filters": [{"property": "status", "op": "eq", "value": "maintenance"}],
        },
    )
    response = await client.post("/query", json={"question": "which assets are in maintenance?"})
    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is False
    assert body["result_count"] == 0
    assert body["source_object_ids"] == []
    assert "No Asset records" in body["answer"]


async def test_query_rejects_empty_question(client: AsyncClient) -> None:
    """An empty question is a 422 from request validation."""
    response = await client.post("/query", json={"question": ""})
    assert response.status_code == 422


async def test_query_advertised_in_openapi(client: AsyncClient) -> None:
    """GET /openapi.json advertises the new /query route."""
    paths = (await client.get("/openapi.json")).json()["paths"]
    assert "/query" in paths


# --- PLAN-0093 AC-2 / AC-5: outcome + arm provenance cross the HTTP boundary ---


class _DegradedPhraseClient(_StubQueryClient):
    """Translates fine, then fails the phrase call — the degrade AC-5 asserts on."""

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        if response_format is None:  # phrase stage
            raise OllamaError("forced phrase transport failure")
        return await super().chat(
            messages, think=think, response_format=response_format, temperature=temperature
        )


async def test_query_outcome_crosses_the_http_boundary(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-2: `outcome` was already computed by the engine and then dropped by the
    router's response mapping. It now ships."""
    _use_stub(monkeypatch, {"object_type": "Asset", "operation": "count"})
    answered = (await client.post("/query", json={"question": "how many assets?"})).json()
    assert answered["outcome"] == "answered"

    _use_stub(
        monkeypatch,
        {
            "object_type": "Asset",
            "operation": "list",
            "filters": [{"property": "status", "op": "eq", "value": "maintenance"}],
        },
    )
    empty = (
        await client.post("/query", json={"question": "which assets are in maintenance?"})
    ).json()
    assert empty["outcome"] == "no_data"
    assert empty["grounded"] is False


async def test_query_discloses_which_arm_phrased_the_answer(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-5: over the SAME records a healthy run and a degraded run are both
    grounded with the same count, and differ only in the arm — the discrimination
    `grounded` never provided and was never meant to."""
    query = {"object_type": "Asset", "operation": "count"}
    _use_stub(monkeypatch, query, phrase="There are 4 assets under management.")
    healthy = (await client.post("/query", json={"question": "how many assets?"})).json()

    monkeypatch.setattr(
        "services.engine.nl_query._build_chat_client", lambda: _DegradedPhraseClient(query)
    )
    degraded = (await client.post("/query", json={"question": "how many assets?"})).json()

    assert healthy["grounded"] is True
    assert degraded["grounded"] is True
    assert healthy["result_count"] == degraded["result_count"] == 4
    assert healthy["phrased_by"] == "stub"  # the model authored it
    assert healthy["phrase_disclosure"] is None
    assert degraded["phrased_by"] == "deterministic"
    assert degraded["phrase_disclosure"] is not None
    assert "degraded to deterministic template" in degraded["phrase_disclosure"]
