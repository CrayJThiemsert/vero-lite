"""NL-query engine tests (PLAN-0013 Step 2).

The grounding logic (executor) is deterministic and fully tested offline;
the LLM translate/phrase calls are exercised through an injected stub
ChatClient, so no live Ollama is touched. Every assertion is on the
returned :class:`NlAnswer`, never on incidental shape.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import pytest

from services.engine.llm.client import ChatResult, OllamaError
from services.engine.nl_query import (
    QueryFilter,
    QueryTranslationError,
    _filter_matches,
    _matches,
    _translate,
    answer_question,
)
from services.engine.ontology_meta import load_ontology_meta
from verticals.energy.data_adapter import register_energy_adapter


@pytest.fixture
def energy_adapter() -> Iterator[None]:
    """Register the energy synthetic adapter for the duration of a test."""
    register_energy_adapter()
    yield


class _StubQueryClient:
    """Deterministic offline LLM for the NL-query path.

    A call carrying ``response_format`` is the translate stage → it returns
    ``query_json``; a call without one is the phrase stage → it returns
    ``phrase``. ``translate_outputs`` (when given) overrides ``query_json``
    per translate attempt, to drive the retry loop. ``raise_on`` lets a
    test force a transport failure on either stage.
    """

    def __init__(
        self,
        *,
        query: dict[str, Any] | None = None,
        translate_outputs: list[str] | None = None,
        phrase: str = "Grounded answer from the data.",
        raise_on: str | None = None,
    ) -> None:
        self._query_json = json.dumps(query) if query is not None else None
        self._translate_outputs = list(translate_outputs) if translate_outputs is not None else None
        self._phrase = phrase
        self._raise_on = raise_on
        self.translate_calls = 0
        self.phrase_calls = 0

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        if response_format is not None:  # translate stage
            if self._raise_on == "translate":
                raise OllamaError("forced translate transport failure")
            content = self._next_translate_output()
            self.translate_calls += 1
            return ChatResult(content=content, thinking=None, model="stub", raw={})
        # phrase stage
        if self._raise_on == "phrase":
            raise OllamaError("forced phrase transport failure")
        self.phrase_calls += 1
        return ChatResult(content=self._phrase, thinking=None, model="stub", raw={})

    def _next_translate_output(self) -> str:
        if self._translate_outputs is not None:
            index = min(self.translate_calls, len(self._translate_outputs) - 1)
            return self._translate_outputs[index]
        assert self._query_json is not None
        return self._query_json


# --- executor (deterministic grounding) ------------------------------------


def test_filter_matches_numeric_and_string() -> None:
    obj = {"asset_type": "battery", "capacity_kw": 250.0}
    assert _filter_matches(obj, QueryFilter(property="asset_type", op="eq", value="battery"))
    assert _filter_matches(obj, QueryFilter(property="capacity_kw", op="gte", value="200"))
    assert not _filter_matches(obj, QueryFilter(property="capacity_kw", op="lt", value="200"))
    assert _filter_matches(obj, QueryFilter(property="asset_type", op="contains", value="batt"))
    assert not _filter_matches(obj, QueryFilter(property="missing", op="eq", value="x"))


def test_matches_is_conjunctive() -> None:
    obj = {"asset_type": "battery", "status": "active"}
    both = [
        QueryFilter(property="asset_type", op="eq", value="battery"),
        QueryFilter(property="status", op="eq", value="active"),
    ]
    one_off = [
        QueryFilter(property="asset_type", op="eq", value="battery"),
        QueryFilter(property="status", op="eq", value="maintenance"),
    ]
    assert _matches(obj, both)
    assert not _matches(obj, one_off)


# --- orchestrator: grounded answers ----------------------------------------


async def test_count_assets_is_grounded(energy_adapter: None) -> None:
    """'How many assets?' → count Asset, grounded in the 4 synthetic assets."""
    client = _StubQueryClient(query={"object_type": "Asset", "operation": "count"})
    answer = await answer_question("how many assets?", "energy", client=client)
    assert answer.grounded is True
    assert answer.result_count == 4
    assert len(answer.source_object_ids) == 4
    assert answer.query is not None and answer.query.object_type == "Asset"
    assert client.phrase_calls == 1


async def test_filter_batteries_grounds_to_two(energy_adapter: None) -> None:
    client = _StubQueryClient(
        query={
            "object_type": "Asset",
            "operation": "list",
            "filters": [{"property": "asset_type", "op": "eq", "value": "battery"}],
        }
    )
    answer = await answer_question("which assets are batteries?", "energy", client=client)
    assert answer.grounded is True
    assert answer.result_count == 2
    assert set(answer.source_object_ids) == {"asset-battery-01", "asset-battery-02"}


async def test_overtemp_reading_grounds_to_the_killer_event(energy_adapter: None) -> None:
    """The NL path can surface the same over-temp event that drives Screen B."""
    client = _StubQueryClient(
        query={
            "object_type": "OperationalEvent",
            "operation": "list",
            "filters": [{"property": "measured_value", "op": "gte", "value": "90"}],
        }
    )
    answer = await answer_question("any over-temperature readings?", "energy", client=client)
    assert answer.grounded is True
    assert answer.source_object_ids == ["event-reading-03"]


# --- orchestrator: anti-hallucination (no data → no invented fact) ----------


async def test_no_matching_data_returns_no_invention(energy_adapter: None) -> None:
    """An empty result short-circuits to a deterministic no-data answer.

    The phrasing LLM is never called, so it cannot invent a record.
    """
    client = _StubQueryClient(
        query={
            "object_type": "Asset",
            "operation": "list",
            "filters": [{"property": "status", "op": "eq", "value": "maintenance"}],
        }
    )
    answer = await answer_question("which assets are in maintenance?", "energy", client=client)
    assert answer.grounded is False
    assert answer.result_count == 0
    assert answer.source_object_ids == []
    assert "No Asset records" in answer.answer
    assert client.phrase_calls == 0  # the LLM got no chance to hallucinate


# --- orchestrator: graceful degradation ------------------------------------


async def test_translation_failure_is_ungrounded_not_an_error(energy_adapter: None) -> None:
    """A transport failure on translate yields an ungrounded answer, not a 500."""
    client = _StubQueryClient(raise_on="translate")
    answer = await answer_question("anything", "energy", client=client)
    assert answer.grounded is False
    assert answer.query is None
    assert "couldn't translate" in answer.answer.lower()


async def test_phrasing_failure_falls_back_deterministically(energy_adapter: None) -> None:
    """A phrasing failure still returns a grounded, templated answer."""
    client = _StubQueryClient(query={"object_type": "Site", "operation": "list"}, raise_on="phrase")
    answer = await answer_question("which sites?", "energy", client=client)
    assert answer.grounded is True
    assert answer.result_count == 2
    assert "Site record(s)" in answer.answer  # deterministic fallback phrasing


async def test_unavailable_backend_is_ungrounded(
    energy_adapter: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When no chat backend can be built, the answer is ungrounded, not a crash."""

    def _boom() -> Any:
        raise NotImplementedError("hosted seam-only stub")

    monkeypatch.setattr("services.engine.nl_query._build_chat_client", _boom)
    answer = await answer_question("how many assets?", "energy")
    assert answer.grounded is False
    assert "unavailable" in answer.answer.lower()


# --- translate: validate-and-retry -----------------------------------------


async def test_translate_retries_then_succeeds() -> None:
    """An invalid object_type is fed back; the corrected query is accepted."""
    meta = load_ontology_meta("energy")
    type_index = {t.name: t for t in meta.object_types}
    bad = json.dumps({"object_type": "Widget", "operation": "count"})
    good = json.dumps({"object_type": "Asset", "operation": "count"})
    client = _StubQueryClient(translate_outputs=[bad, good])
    query = await _translate(client, "q", "energy", meta, type_index, retry_budget=3)
    assert query.object_type == "Asset"
    assert client.translate_calls == 2


async def test_translate_exhausts_budget_and_raises() -> None:
    """A persistently invalid property exhausts the budget → QueryTranslationError."""
    meta = load_ontology_meta("energy")
    type_index = {t.name: t for t in meta.object_types}
    bad = json.dumps(
        {
            "object_type": "Asset",
            "filters": [{"property": "nonexistent", "op": "eq", "value": "x"}],
        }
    )
    client = _StubQueryClient(translate_outputs=[bad])
    with pytest.raises(QueryTranslationError):
        await _translate(client, "q", "energy", meta, type_index, retry_budget=2)
    assert client.translate_calls == 2
