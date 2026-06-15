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

from services.api.config import settings
from services.engine.llm.client import ChatResult, OllamaClient, OllamaError
from services.engine.nl_query import (
    AggregateResult,
    QueryFilter,
    QueryOperation,
    QueryTranslationError,
    StructuredQuery,
    _build_chat_client,
    _compute_aggregate,
    _filter_matches,
    _fmt_num,
    _matches,
    _object_id,
    _object_title,
    _parse_query,
    _scalar_equal,
    _to_number,
    _translate,
    _validate_query,
    answer_question,
)
from services.engine.ontology_meta import ObjectTypeMeta, load_ontology_meta
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


# --- backend selection (config-driven; construction touches no network) ----


def test_build_chat_client_selects_local_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "llm_backend", "local")
    client = _build_chat_client()
    assert isinstance(client, OllamaClient)


def test_build_chat_client_hosted_backend_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "llm_backend", "hosted")
    with pytest.raises(NotImplementedError):
        _build_chat_client()


def test_build_chat_client_unknown_backend_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "llm_backend", "wat")
    with pytest.raises(ValueError, match="unknown llm_backend"):
        _build_chat_client()


# --- translate response parsing (deterministic) ----------------------------


def test_parse_query_rejects_non_json() -> None:
    meta = load_ontology_meta("energy")
    type_index = {t.name: t for t in meta.object_types}
    query, error = _parse_query("not json {", type_index)
    assert query is None
    assert "not valid JSON" in error


def test_parse_query_rejects_schema_violation() -> None:
    meta = load_ontology_meta("energy")
    type_index = {t.name: t for t in meta.object_types}
    # Valid JSON but missing the required object_type field.
    query, error = _parse_query('{"operation": "list"}', type_index)
    assert query is None
    assert "did not satisfy the schema" in error


# --- numeric coercion + comparison helpers ---------------------------------


def test_to_number_rejects_bool() -> None:
    """bool is an int subclass; it must never coerce to a filter number."""
    assert _to_number(True) is None
    assert _to_number(False) is None


def test_scalar_equal_numeric_path() -> None:
    assert _scalar_equal(90, "90") is True
    assert _scalar_equal(90, "91") is False


def test_filter_matches_numeric_operator_edges() -> None:
    assert _filter_matches({"v": 10}, QueryFilter(property="v", op="gt", value="5"))
    assert _filter_matches({"v": 5}, QueryFilter(property="v", op="lte", value="5"))
    # a non-numeric actual against a numeric operator never matches
    assert not _filter_matches({"v": "abc"}, QueryFilter(property="v", op="gt", value="5"))


# --- object id / title display fallbacks -----------------------------------


def _asset_meta() -> ObjectTypeMeta:
    return ObjectTypeMeta(name="Asset", primary_key="asset_id", title_key="label", properties=[])


def test_object_id_falls_back_to_title_key() -> None:
    # primary_key absent on the object → fall back to title_key
    assert _object_id({"label": "Battery 1"}, _asset_meta()) == "Battery 1"


def test_object_id_empty_when_no_key_present() -> None:
    assert _object_id({}, _asset_meta()) == ""
    assert _object_id({"asset_id": "x"}, None) == ""


def test_object_title_falls_back_to_primary_key() -> None:
    # title_key absent on the object → fall back to primary_key
    assert _object_title({"asset_id": "asset-01"}, _asset_meta()) == "asset-01"


def test_object_title_empty_when_no_key_present() -> None:
    assert _object_title({}, _asset_meta()) == ""
    assert _object_title({"label": "x"}, None) == ""


# --- orchestrator degrade paths (real answer_question behavior) ------------


async def test_count_query_phrase_failure_falls_back(energy_adapter: None) -> None:
    """A count query whose phrasing LLM fails still returns a grounded,
    deterministic count answer (the _fallback_answer count branch)."""
    client = _StubQueryClient(
        query={"object_type": "Asset", "operation": "count"}, raise_on="phrase"
    )
    answer = await answer_question("how many assets?", "energy", client=client)
    assert answer.grounded is True
    assert "Asset record(s) match that query" in answer.answer


async def test_retrieval_failure_is_ungrounded_but_keeps_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the data adapter raises during retrieval, the answer degrades to
    ungrounded while preserving the translated query (never a 500)."""

    def _boom(_vertical: str) -> Any:
        raise RuntimeError("adapter exploded")

    monkeypatch.setattr("services.engine.nl_query.registry.get_adapter", _boom)
    client = _StubQueryClient(query={"object_type": "Asset", "operation": "list"})
    answer = await answer_question("which assets?", "energy", client=client)
    assert answer.grounded is False
    assert answer.query is not None
    assert "retrieve" in answer.answer.lower()


# --- aggregates: deterministic execute-stage compute (PLAN-0024 AC-1) -------


def test_compute_aggregate_reduces_min_max_avg_sum() -> None:
    rows = [{"v": 10}, {"v": 20}, {"v": 30}]

    def value_for(operation: QueryOperation) -> float | None:
        query = StructuredQuery(object_type="X", operation=operation, aggregate_property="v")
        result = _compute_aggregate(query, rows)
        return result.value if result is not None else None

    assert value_for("max") == 30
    assert value_for("min") == 10
    assert value_for("sum") == 60
    assert value_for("avg") == 20


def test_compute_aggregate_over_no_numeric_is_none() -> None:
    """No numeric value for the property -> None (caller degrades to no-data)."""
    query = StructuredQuery(object_type="X", operation="max", aggregate_property="v")
    assert _compute_aggregate(query, [{"other": 1}, {"v": "n/a"}]) is None


def test_compute_aggregate_groups_by_property() -> None:
    rows = [{"g": "a", "v": 1}, {"g": "a", "v": 9}, {"g": "b", "v": 5}]
    query = StructuredQuery(object_type="X", operation="max", aggregate_property="v", group_by="g")
    result = _compute_aggregate(query, rows)
    assert isinstance(result, AggregateResult)
    assert result.value == 9
    assert result.groups == {"a": 9, "b": 5}


def test_fmt_num_strips_float_noise() -> None:
    assert _fmt_num(96.5) == "96.5"
    assert _fmt_num(250.0) == "250"
    assert _fmt_num(123.9 / 3) == "41.3"
    assert _fmt_num(None) == "n/a"


# --- aggregates end-to-end (answer_question; PLAN-0024 nl-08/09/10/11) ------


async def test_avg_with_name_resolve_grounds_to_battery_b_mean(energy_adapter: None) -> None:
    """nl-10: avg of Battery Bank B's celsius readings = 41.3 (resolve + avg)."""
    client = _StubQueryClient(
        query={
            "object_type": "OperationalEvent",
            "operation": "avg",
            "aggregate_property": "measured_value",
            "filters": [{"property": "unit", "op": "eq", "value": "celsius"}],
            "resolve": {
                "name": "Battery Bank B",
                "target_type": "Asset",
                "filter_property": "asset_id",
            },
        },
        raise_on="phrase",  # exercise the deterministic aggregate phrasing
    )
    answer = await answer_question(
        "average temperature of Battery Bank B?", "energy", client=client
    )
    assert answer.grounded is True
    assert answer.result_count == 3
    assert answer.aggregate is not None
    assert answer.aggregate.operation == "avg"
    assert answer.aggregate.value == pytest.approx(41.3)
    assert "41.3" in answer.answer


async def test_max_groupby_relabels_id_to_entity_name(energy_adapter: None) -> None:
    """nl-08/nl-11: hottest battery -> Battery Bank A at 96.5 (group_by + relabel)."""
    client = _StubQueryClient(
        query={
            "object_type": "OperationalEvent",
            "operation": "max",
            "aggregate_property": "measured_value",
            "group_by": "asset_id",
            "filters": [{"property": "unit", "op": "eq", "value": "celsius"}],
        },
        raise_on="phrase",
    )
    answer = await answer_question("which battery is hottest?", "energy", client=client)
    assert answer.grounded is True
    assert answer.result_count == 7  # all celsius readings across both batteries
    assert answer.aggregate is not None
    assert answer.aggregate.value == 96.5
    # group keys relabelled from asset_id -> the Asset's title (name)
    assert answer.aggregate.groups == {"Battery Bank A": 96.5, "Battery Bank B": 43.2}
    assert "Battery Bank A" in answer.answer
    assert "96.5" in answer.answer


async def test_count_with_name_resolve_grounds_to_five_events(energy_adapter: None) -> None:
    """nl-09: events for Battery Bank A = 5 (cross-type name->id resolve)."""
    client = _StubQueryClient(
        query={
            "object_type": "OperationalEvent",
            "operation": "count",
            "resolve": {
                "name": "Battery Bank A",
                "target_type": "Asset",
                "filter_property": "asset_id",
            },
        }
    )
    answer = await answer_question("how many events for Battery Bank A?", "energy", client=client)
    assert answer.grounded is True
    assert answer.result_count == 5
    assert set(answer.source_object_ids) == {
        "event-transition-01",
        "event-reading-01",
        "event-reading-05",
        "event-reading-06",
        "event-reading-03",
    }


# --- aggregates + resolve preserve the anti-hallucination guard (AC-5) ------


async def test_aggregate_over_no_numeric_match_is_no_invention(energy_adapter: None) -> None:
    """max over a property the matched rows lack -> deterministic no-data, no LLM."""
    client = _StubQueryClient(
        query={
            "object_type": "OperationalEvent",
            "operation": "max",
            "aggregate_property": "measured_value",
            "filters": [{"property": "event_type", "op": "eq", "value": "alarm"}],
        }
    )
    answer = await answer_question("highest value among alarms?", "energy", client=client)
    assert answer.grounded is False
    assert answer.aggregate is None
    assert "No OperationalEvent records" in answer.answer
    assert client.phrase_calls == 0  # the LLM got no chance to invent a number


async def test_name_resolve_miss_is_no_invention(energy_adapter: None) -> None:
    """A name that resolves to nothing -> honest no-records, never a fabricated match."""
    client = _StubQueryClient(
        query={
            "object_type": "OperationalEvent",
            "operation": "count",
            "resolve": {
                "name": "Battery Bank Z",
                "target_type": "Asset",
                "filter_property": "asset_id",
            },
        }
    )
    answer = await answer_question("events for Battery Bank Z?", "energy", client=client)
    assert answer.grounded is False
    assert answer.result_count == 0
    assert "No OperationalEvent records" in answer.answer
    assert client.phrase_calls == 0


# --- aggregate validation feeds the translate retry loop (PLAN-0024 AC-1) ---


async def test_aggregate_without_property_is_rejected_then_retried() -> None:
    """An aggregate op missing aggregate_property is invalid; the retry corrects it."""
    meta = load_ontology_meta("energy")
    type_index = {t.name: t for t in meta.object_types}
    bad = json.dumps({"object_type": "OperationalEvent", "operation": "max"})
    good = json.dumps(
        {
            "object_type": "OperationalEvent",
            "operation": "max",
            "aggregate_property": "measured_value",
        }
    )
    client = _StubQueryClient(translate_outputs=[bad, good])
    query = await _translate(client, "q", "energy", meta, type_index, retry_budget=3)
    assert query.operation == "max"
    assert query.aggregate_property == "measured_value"
    assert client.translate_calls == 2


async def test_non_numeric_aggregate_property_is_rejected() -> None:
    """aggregate_property must be numeric; a string property exhausts the budget."""
    meta = load_ontology_meta("energy")
    type_index = {t.name: t for t in meta.object_types}
    bad = json.dumps(
        {"object_type": "OperationalEvent", "operation": "avg", "aggregate_property": "unit"}
    )
    client = _StubQueryClient(translate_outputs=[bad])
    with pytest.raises(QueryTranslationError):
        await _translate(client, "q", "energy", meta, type_index, retry_budget=2)


# --- aggregate-intent / non-aggregate-operation coherence guard (nl-08/nl-11) ---


def test_aggregate_property_with_list_operation_is_rejected() -> None:
    """aggregate_property set with operation 'list' is the nl-08/nl-11 translate gap:
    the aggregate would never be computed. The guard rejects it so the retry loop
    nudges the model to an aggregate op."""
    meta = load_ontology_meta("energy")
    type_index = {t.name: t for t in meta.object_types}
    query = StructuredQuery(
        object_type="OperationalEvent", operation="list", aggregate_property="measured_value"
    )
    errors = _validate_query(query, type_index)
    assert any("aggregate_property" in e and "max" in e for e in errors)


def test_group_by_with_count_operation_is_rejected() -> None:
    """group_by with a non-aggregate operation ('count') is the superlative miss
    (group_by set, operation not an aggregate) — rejected for retry."""
    meta = load_ontology_meta("energy")
    type_index = {t.name: t for t in meta.object_types}
    query = StructuredQuery(object_type="OperationalEvent", operation="count", group_by="asset_id")
    errors = _validate_query(query, type_index)
    assert any("group_by" in e and "max" in e for e in errors)


def test_aggregate_op_with_property_and_group_by_is_accepted() -> None:
    """The coherent combo (operation 'max' + aggregate_property + group_by) passes."""
    meta = load_ontology_meta("energy")
    type_index = {t.name: t for t in meta.object_types}
    query = StructuredQuery(
        object_type="OperationalEvent",
        operation="max",
        aggregate_property="measured_value",
        group_by="asset_id",
    )
    assert _validate_query(query, type_index) == []


async def test_list_with_aggregate_intent_is_rejected_then_retried() -> None:
    """The nl-11 pattern end-to-end: 'list' + group_by + aggregate_property is
    rejected; the retry corrects operation to 'max' and is accepted."""
    meta = load_ontology_meta("energy")
    type_index = {t.name: t for t in meta.object_types}
    bad = json.dumps(
        {
            "object_type": "OperationalEvent",
            "operation": "list",
            "aggregate_property": "measured_value",
            "group_by": "asset_id",
            "limit": 1,
        }
    )
    good = json.dumps(
        {
            "object_type": "OperationalEvent",
            "operation": "max",
            "aggregate_property": "measured_value",
            "group_by": "asset_id",
        }
    )
    client = _StubQueryClient(translate_outputs=[bad, good])
    query = await _translate(client, "q", "energy", meta, type_index, retry_budget=3)
    assert query.operation == "max"
    assert query.group_by == "asset_id"
    assert client.translate_calls == 2
