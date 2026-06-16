"""Offline tests for B-γ arm (c) — lean RAG (PLAN-0027 AC-3).

Pure, no network: the corpus loads, the retriever is deterministic top-k, the
SD-1↔SD-2 joint binding holds (every energy breach action_keywords lemma is
covered by >=1 snippet AND surfaces for the question), the free-text answer is
adapted into the grader's shape and scored via the EXISTING ``grade_proposal``,
and the D-6 contamination guard holds (no ``services.engine.procedures`` import;
exactly one LLM call per item; no second "verify" call).
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import Any

from benchmarks.procedure_baseline.loader import DATASET_DIR, load_dataset
from benchmarks.procedure_baseline.schema import BenchmarkItem, Expected, Scenario, SiblingReading
from benchmarks.procedure_comparison import rag_arm
from benchmarks.procedure_comparison.questions import render_rag_question
from benchmarks.procedure_comparison.rag_arm import (
    DEFAULT_CORPUS,
    answer_to_judgment,
    build_rag_messages,
    load_corpus,
    retrieve,
    run_item_c,
)
from services.engine.llm.client import ChatResult, OllamaError


def _energy_breach_items() -> list[BenchmarkItem]:
    dataset = load_dataset(DATASET_DIR / "energy.yaml")
    return [item for item in dataset.items if item.expected.disposition.value == "breach"]


def _item(**scenario_overrides: Any) -> BenchmarkItem:
    base: dict[str, Any] = {
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
    base.update(scenario_overrides)
    return BenchmarkItem(
        id="energy-h01",
        description="98.0 C breach amid two safe siblings.",
        scenario=Scenario.model_validate(base),
        expected=Expected.model_validate(
            {
                "disposition": "breach",
                "action_expected": True,
                "affected_primary_key": "asset-E101",
                "action_keywords": ["restart", "reset", "reboot"],
            }
        ),
    )


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


class _BoomClient:
    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        raise OllamaError("call to /api/chat failed: timeout")


# --- corpus + the SD-1 ↔ SD-2 joint binding ----------------------------------


def test_corpus_loads() -> None:
    corpus = load_corpus()
    assert len(corpus) >= 8  # SD-1: ~8-15 snippets
    assert all(snippet.id and snippet.text for snippet in corpus)


def test_joint_binding_every_breach_action_lemma_is_covered() -> None:
    """SD-1↔SD-2 binding: every energy breach item's expected action_keywords lemma
    must appear in >=1 corpus snippet — else an arm (c) miss is a retrieval artifact,
    not a naive-RAG limit."""
    corpus_text = " ".join(snippet.text.lower() for snippet in load_corpus())
    lemmas = {
        keyword.lower()
        for item in _energy_breach_items()
        for keyword in (item.expected.action_keywords or [])
    }
    assert lemmas == {"restart", "reset", "reboot"}  # the energy breach action class
    missing = {lemma for lemma in lemmas if lemma not in corpus_text}
    assert not missing, f"action lemmas not covered by the corpus: {missing}"


def test_retriever_is_deterministic_and_topk() -> None:
    corpus = load_corpus()
    question = render_rag_question(_item().scenario, "temperature")
    first = retrieve(question, corpus, k=3)
    second = retrieve(question, corpus, k=3)
    assert len(first) == 3
    assert [s.id for s in first] == [s.id for s in second]  # deterministic


def test_retriever_surfaces_an_action_snippet_for_a_breach_question() -> None:
    """The joint binding at retrieval time: a temperature-breach question must
    surface a snippet that names the restart action lemma (so it reaches the prompt)."""
    corpus = load_corpus()
    question = render_rag_question(_item().scenario, "temperature")
    retrieved_text = " ".join(snippet.text.lower() for snippet in retrieve(question, corpus, k=4))
    assert "restart" in retrieved_text


def test_build_rag_messages_has_no_response_format_path() -> None:
    """The prompt is a system+user pair with the retrieved snippets as context —
    a freeform answer (naive RAG), never a schema-constrained call."""
    messages = build_rag_messages("Which asset breached?", load_corpus()[:2])
    assert [m["role"] for m in messages] == ["system", "user"]
    assert "Context:" in messages[0]["content"]


# --- the free-text -> grader adapter (reuses grade_proposal) -----------------


def test_answer_to_judgment_finds_named_entity() -> None:
    judgment = answer_to_judgment(
        "Restart asset-E101 (reset / reboot) after a go/no-go.",
        ["asset-E101", "asset-E102", "asset-E103"],
    )
    keys = {entity.primary_key for entity in judgment.affected_entities}
    assert keys == {"asset-E101"}  # only the named candidate, not the unnamed decoys


def test_answer_to_judgment_falls_back_when_no_entity_named() -> None:
    judgment = answer_to_judgment("Everything looks nominal.", ["asset-E101"])
    assert len(judgment.affected_entities) == 1
    assert judgment.affected_entities[0].primary_key == "∅"  # graded as an entity miss


async def test_correct_answer_grades_pass() -> None:
    client = _RagClient("Restart asset-E101 (reset / reboot) the affected asset.")

    result = await run_item_c(_item(), client, load_corpus(), "temperature", k=4)

    assert result.entity_correct is True
    assert result.action_correct is True
    assert result.passed is True
    assert result.judgment is not None  # carried for --dump-json VERIFY


async def test_wrong_entity_or_action_grades_fail() -> None:
    # names a decoy + no action verb -> both checks fail
    client = _RagClient("Asset asset-E102 looks worth a glance; continue monitoring.")

    result = await run_item_c(_item(), client, load_corpus(), "temperature", k=4)

    assert result.entity_correct is False
    assert result.action_correct is False
    assert result.passed is False


# --- D-6 contamination guard (BINDING) ---------------------------------------


async def test_d6_exactly_one_llm_call_per_item() -> None:
    """D-6: arm (c) makes exactly ONE chat call per item — no second 'verify' call,
    and the single call is freeform (no response_format)."""
    client = _RagClient("Restart asset-E101 (reset).")

    await run_item_c(_item(), client, load_corpus(), "temperature", k=4)

    assert len(client.calls) == 1
    assert client.calls[0]["has_format"] is False  # freeform naive-RAG shape


def test_d6_arm_c_imports_no_procedure_engine_symbol() -> None:
    """D-6: arm (c)'s IMPORT statements pull NO ``services.engine.procedures`` symbol
    — it stays a CLEAN naive RAG baseline (no procedure/ontology/verify/reshape/
    governance layer). Checked on the parsed AST, not the docstring text (which
    legitimately names the guarded module)."""
    tree = ast.parse(inspect.getsource(rag_arm))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
    offenders = [module for module in imported if module.startswith("services.engine.procedures")]
    assert not offenders, f"D-6 violation: arm (c) imports {offenders}"


async def test_error_is_recorded_not_raised() -> None:
    result = await run_item_c(_item(), _BoomClient(), load_corpus(), "temperature", k=4)

    assert result.error != "" and "timeout" in result.error
    assert result.passed is False
    assert result.judgment is None


def test_default_corpus_path_exists() -> None:
    assert Path(DEFAULT_CORPUS).exists()
