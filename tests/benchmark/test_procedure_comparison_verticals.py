"""Offline tests for the B-γ extension to aquaculture + supply_chain (PLAN-0028).

Pure, no network. Parametrized over the two new verticals: the corpus loads, the
SD-1↔SD-2 joint binding holds (UNDER-cover — every breach ``action_keywords`` lemma
is covered by a snippet AND surfaces under the k=4 retriever; OVER-cover — no snippet
leaks a dataset entity key, R-OQ1-4), the **data-driven** prompt renders the vertical's
own persona + entity word (not energy's), a correct free-text answer grades pass via
the EXISTING ``grade_proposal``, and the D-6 one-call guard holds. A separate energy
regression block asserts the data-driven templates leave the energy output
**byte-identical** (PLAN-0028 AC-4).
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from benchmarks.procedure_baseline.loader import DATASET_DIR, load_dataset
from benchmarks.procedure_baseline.schema import BenchmarkItem, Scenario, SiblingReading
from benchmarks.procedure_comparison.questions import render_rag_question, render_sql_question
from benchmarks.procedure_comparison.rag_arm import (
    CORPUS_DIR,
    build_rag_messages,
    load_corpus,
    persona_for,
    retrieve,
    run_item_c,
)
from benchmarks.procedure_comparison.text_to_sql_arm import ACTION_CLASS_NA, run_item_b
from services.engine.llm.client import ChatResult


class _RagClient:
    """Returns one canned freeform answer; records every call (the D-6 one-call check)."""

    def __init__(self, answer: str) -> None:
        self._answer = answer
        self.calls: list[dict[str, Any]] = []

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        self.calls.append({"has_format": response_format is not None})
        return ChatResult(content=self._answer, thinking=None, model="mock", raw={})


def _breach_items(vertical: str) -> list[BenchmarkItem]:
    dataset = load_dataset(DATASET_DIR / f"{vertical}.yaml")
    return [item for item in dataset.items if item.expected.disposition.value == "breach"]


# (vertical, corpus_file, reading_parameter, lemmas, entity_word, direction, action_phrase)
_VERTICALS = [
    pytest.param(
        "aquaculture",
        "aquaculture_v0.yaml",
        "dissolved_oxygen",
        {"aerat", "oxygenat"},
        "pond",
        "below",
        "Start emergency aeration to aerate and oxygenate",
        id="aquaculture",
    ),
    pytest.param(
        "supply_chain",
        "supply_chain_v0.yaml",
        "temperature",
        {"hold", "inspect", "quarantine", "divert"},
        "shipment",
        "above",
        "Hold and inspect",
        id="supply_chain",
    ),
]

_param = pytest.mark.parametrize(
    "vertical,corpus_file,param,lemmas,entity_word,direction,action_phrase", _VERTICALS
)


@_param
def test_corpus_loads_and_is_sized(
    vertical: str,
    corpus_file: str,
    param: str,
    lemmas: set[str],
    entity_word: str,
    direction: str,
    action_phrase: str,
) -> None:
    corpus = load_corpus(CORPUS_DIR / corpus_file)
    assert 8 <= len(corpus) <= 15  # structural parity (R-OQ1-1), sized to the action vocabulary
    assert all(snippet.id and snippet.text for snippet in corpus)


@_param
def test_dataset_lemmas_match_declared(
    vertical: str,
    corpus_file: str,
    param: str,
    lemmas: set[str],
    entity_word: str,
    direction: str,
    action_phrase: str,
) -> None:
    """The dataset's actual breach lemma set matches what the corpus is built to cover."""
    actual = {
        keyword.lower()
        for item in _breach_items(vertical)
        for keyword in (item.expected.action_keywords or [])
    }
    assert actual == lemmas


@_param
def test_joint_binding_under_cover_every_lemma(
    vertical: str,
    corpus_file: str,
    param: str,
    lemmas: set[str],
    entity_word: str,
    direction: str,
    action_phrase: str,
) -> None:
    """SD-1↔SD-2 UNDER-cover: every breach action lemma appears in >=1 corpus snippet."""
    corpus_text = " ".join(
        snippet.text.lower() for snippet in load_corpus(CORPUS_DIR / corpus_file)
    )
    missing = {lemma for lemma in lemmas if lemma not in corpus_text}
    assert not missing, f"{vertical}: action lemmas not covered by the corpus: {missing}"


@_param
def test_retriever_surfaces_an_action_snippet(
    vertical: str,
    corpus_file: str,
    param: str,
    lemmas: set[str],
    entity_word: str,
    direction: str,
    action_phrase: str,
) -> None:
    """SD-1↔SD-2 at retrieval time: a breach question surfaces an action-lemma snippet
    in the k=4 retrieved set (else an arm (c) miss would be a retrieval artifact)."""
    corpus = load_corpus(CORPUS_DIR / corpus_file)
    question = render_rag_question(_breach_items(vertical)[0].scenario, param)
    retrieved_text = " ".join(snippet.text.lower() for snippet in retrieve(question, corpus, k=4))
    assert any(
        lemma in retrieved_text for lemma in lemmas
    ), f"{vertical}: no action lemma in the k=4 retrieved snippets"


@_param
def test_over_cover_no_entity_key_literal(
    vertical: str,
    corpus_file: str,
    param: str,
    lemmas: set[str],
    entity_word: str,
    direction: str,
    action_phrase: str,
) -> None:
    """R-OQ1-4 OVER-cover guard: no snippet names a dataset entity key (the model must
    still pick the breached entity from the readings, not read it off the corpus)."""
    corpus_text = " ".join(
        snippet.text.lower() for snippet in load_corpus(CORPUS_DIR / corpus_file)
    )
    keys: set[str] = set()
    for item in load_dataset(DATASET_DIR / f"{vertical}.yaml").items:
        keys.add(item.scenario.primary_key.lower())
        keys |= {decoy.primary_key.lower() for decoy in item.scenario.distractors}
    leaked = {key for key in keys if key in corpus_text}
    assert not leaked, f"{vertical}: corpus leaks dataset entity keys: {leaked}"


@_param
def test_data_driven_prompt_uses_vertical_persona_and_entity(
    vertical: str,
    corpus_file: str,
    param: str,
    lemmas: set[str],
    entity_word: str,
    direction: str,
    action_phrase: str,
) -> None:
    """The RAG prompt's persona + entity word are DERIVED from the vertical/scenario
    (data-driven), not the hardcoded energy literals."""
    messages = build_rag_messages(
        "Which entity breached?",
        load_corpus(CORPUS_DIR / corpus_file)[:2],
        persona=persona_for(vertical),
        entity_word=entity_word,
    )
    system = messages[0]["content"]
    assert vertical.replace("_", " ") in system  # persona names this domain
    assert f"affected {entity_word}" in system  # entity word derived, not "asset"
    assert "energy operations assistant" not in system


@_param
def test_threshold_noun_renders_by_direction(
    vertical: str,
    corpus_file: str,
    param: str,
    lemmas: set[str],
    entity_word: str,
    direction: str,
    action_phrase: str,
) -> None:
    """The threshold noun is derived from the breach direction: above->ceiling,
    below->floor (the R-OQ1-3 template-neutrality fix)."""
    expected_noun = "ceiling" if direction == "above" else "floor"
    question = render_rag_question(_breach_items(vertical)[0].scenario, param)
    assert expected_noun in question
    assert (expected_noun == "floor") == ("floor" in question)


@_param
async def test_correct_answer_grades_pass(
    vertical: str,
    corpus_file: str,
    param: str,
    lemmas: set[str],
    entity_word: str,
    direction: str,
    action_phrase: str,
) -> None:
    """A correct free-text answer (names the breached entity + the action class) grades
    pass via the EXISTING grade_proposal, with exactly one (freeform) LLM call (D-6)."""
    item = _breach_items(vertical)[0]
    client = _RagClient(f"{action_phrase} {item.scenario.primary_key}.")

    result = await run_item_c(
        item, client, load_corpus(CORPUS_DIR / corpus_file), param, k=4, vertical=vertical
    )

    assert result.entity_correct is True
    assert result.action_correct is True
    assert result.passed is True
    assert len(client.calls) == 1  # D-6: exactly one call
    assert client.calls[0]["has_format"] is False  # freeform naive-RAG shape


@_param
async def test_wrong_action_grades_action_fail(
    vertical: str,
    corpus_file: str,
    param: str,
    lemmas: set[str],
    entity_word: str,
    direction: str,
    action_phrase: str,
) -> None:
    """Naming the right entity but no action lemma fails the action check (and so the
    headline) — the grader still discriminates per vertical."""
    item = _breach_items(vertical)[0]
    client = _RagClient(f"{item.scenario.primary_key} looks worth a glance; keep monitoring.")

    result = await run_item_c(
        item, client, load_corpus(CORPUS_DIR / corpus_file), param, k=4, vertical=vertical
    )

    assert result.entity_correct is True
    assert result.action_correct is False
    assert result.passed is False


# --- energy regression: the data-driven refactor leaves energy byte-identical (AC-4) --


def _energy_scenario() -> Scenario:
    return Scenario.model_validate(
        {
            "event_id": "energy-evt-h01",
            "entity_type": "Asset",
            "primary_key": "asset-E101",
            "measured_value": 98.0,
            "unit": "celsius",
            "threshold": 90.0,
            "direction": "above",
            "watch_margin": 5.0,
            "distractors": [
                SiblingReading(primary_key="asset-E102", measured_value=88.0),
                SiblingReading(primary_key="asset-E103", measured_value=86.5),
            ],
        }
    )


def test_energy_sql_question_byte_identical() -> None:
    assert render_sql_question(_energy_scenario(), "temperature") == (
        "Which asset has a temperature reading at or above the 90 °C ceiling? "
        "Return the affected asset."
    )


def test_energy_rag_question_byte_identical() -> None:
    question = render_rag_question(_energy_scenario(), "temperature")
    assert question == (
        "Asset temperature readings — asset-E101 = 98 °C; asset-E102 = 88 °C; "
        "asset-E103 = 86.5 °C. The temperature ceiling is 90 °C (a breach is a reading "
        "at or above the ceiling). Which asset has a temperature breach, and what should "
        "we do about it?"
    )
    assert "floor" not in question


def test_energy_rag_prompt_persona_byte_identical() -> None:
    """The default build_rag_messages (energy) is byte-identical to the pre-data-driven
    prompt — the persona + entity word defaults reproduce 'an energy operations
    assistant' + 'affected asset'."""
    system = build_rag_messages("Which asset breached?", load_corpus()[:1])[0]["content"]
    assert system.startswith(
        "You are an energy operations assistant. Use ONLY the context snippets below to "
        "answer the operator. Name the specific affected asset and state the single "
        "recommended action.\n\nContext:\n"
    )


@pytest.mark.parametrize(
    "vertical,expected", [("energy", "an"), ("aquaculture", "an"), ("supply_chain", "a")]
)
def test_persona_for_article_and_domain(vertical: str, expected: str) -> None:
    persona = persona_for(vertical)
    assert persona == f"{expected} {vertical.replace('_', ' ')} operations assistant"


# --- arm (b) raw text-to-SQL per vertical (AC-2; below-floor + above-ceiling) ------


class _SqlClient:
    """Returns one canned ``{"sql": ...}`` for the generate call (the D-3 one-call check)."""

    def __init__(self, content: str) -> None:
        self._content = content
        self.calls: list[dict[str, Any]] = []

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        self.calls.append({"has_format": response_format is not None})
        return ChatResult(content=self._content, thinking=None, model="mock", raw={})


def _sql_json(sql: str) -> str:
    return json.dumps({"sql": sql})


@_param
async def test_arm_b_correct_discovery_select_scores_entity(
    vertical: str,
    corpus_file: str,
    param: str,
    lemmas: set[str],
    entity_word: str,
    direction: str,
    action_phrase: str,
) -> None:
    """A correct discovery SELECT finds the breached entity and scores entity-ID PASS —
    including aquaculture's BELOW-floor breach (``<=`` not ``>=``). Action-class is the
    structural D-3 N/A note, never a wrong answer."""
    item = _breach_items(vertical)[0]
    op = "<=" if direction == "below" else ">="
    where = f"measured_value {op} {item.scenario.threshold}"
    sql = f"SELECT asset_id FROM operational_event WHERE {where}"  # noqa: S608 (test fixture SQL)
    client = _SqlClient(_sql_json(sql))

    result = await run_item_b(item.id, item.scenario, client, param)

    assert result.outcome == "correct"
    assert result.entity_correct is True
    assert result.action_class == ACTION_CLASS_NA  # D-3: SQL returns data, not an action
    assert result.error == ""
    assert len(client.calls) == 1
    assert client.calls[0]["has_format"] is True  # generate_sql constrains {"sql": ...}


@_param
async def test_arm_b_non_select_is_refused(
    vertical: str,
    corpus_file: str,
    param: str,
    lemmas: set[str],
    entity_word: str,
    direction: str,
    action_phrase: str,
) -> None:
    """A non-read-only statement is refused → invalid (the read-only SQL guard holds
    per vertical)."""
    item = _breach_items(vertical)[0]
    client = _SqlClient(_sql_json("DELETE FROM asset"))

    result = await run_item_b(item.id, item.scenario, client, param)

    assert result.outcome == "invalid"
    assert result.entity_correct is False
    assert "refused" in result.error
