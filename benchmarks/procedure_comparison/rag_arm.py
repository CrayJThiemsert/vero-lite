"""Arm (c) of the B-γ comparison — lean-but-real RAG (PLAN-0027 D-4; SD-5).

A small STATIC energy corpus (ontology threshold rule + action-playbook snippets,
``corpus/energy_v0.yaml``) + a **deterministic top-k lexical retriever** (query/
snippet term overlap — NO vector store, NO embeddings) → retrieved context into
the prompt → ONE freeform LLM answer → graded **entity-ID + action-class** with
the SAME procedure-baseline grader checks (``grade_proposal``), adapting the
free-text answer into the minimal ``LlmJudgment`` shape the checks consume
(PLAN-0027 §3.1) — the grading logic is REUSED, never forked.

D-6 CONTAMINATION GUARD (BINDING). Arm (c) is a CLEAN naive RAG baseline: it
imports NO ``services.engine.procedures`` symbol, runs NO second "verify" LLM
call, and adds NO semantic-consistency / output-reshape / governance layer. Any
such layer needs procedure/ontology awareness and would import vero-lite's
structure into the baseline, destroying the comparison's ability to isolate what
governance adds over RAG. Fairness is corpus richness (SD-1) + prompt (SD-2) ONLY.
The joint SD-1↔SD-2 binding (every breach ``action_keywords`` lemma covered by ≥1
snippet; shared surface vocabulary) keeps an arm-(c) miss a naive-RAG limit, not a
retrieval artifact.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path

from ruamel.yaml import YAML

from benchmarks.procedure_baseline.grader import (
    GradeResult,
    grade_proposal,
    normalize_primary_key,
)
from benchmarks.procedure_baseline.schema import BenchmarkItem, Expected
from benchmarks.procedure_comparison.questions import render_rag_question
from services.engine.actions import EntityRef
from services.engine.llm.client import OllamaError
from services.engine.llm.structured import ChatClient, LlmJudgment

CORPUS_DIR = Path(__file__).parent / "corpus"
DEFAULT_CORPUS = CORPUS_DIR / "energy_v0.yaml"
DEFAULT_TOP_K = 4

_NO_ENTITY = "∅"  # placeholder PK when the answer named no recognised entity

# A small stopword set so the lexical overlap favours content terms (entity-type
# words + action verbs) over function words — keeps the retriever deterministic
# while not letting "the"/"a"/"what" dominate the score.
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "the",
        "is",
        "are",
        "was",
        "to",
        "on",
        "of",
        "at",
        "it",
        "its",
        "we",
        "do",
        "what",
        "should",
        "about",
        "has",
        "have",
        "be",
        "or",
        "in",
        "that",
        "this",
        "by",
        "with",
        "as",
        "for",
        "not",
        "no",
        "i",
    }
)


@dataclass(frozen=True)
class Snippet:
    """One static corpus snippet (an ontology rule or an action-playbook entry)."""

    id: str
    text: str


def load_corpus(path: Path = DEFAULT_CORPUS) -> list[Snippet]:
    """Load the static energy RAG corpus YAML into ``Snippet``\\ s (deterministic)."""
    yaml = YAML(typ="safe")
    with path.open(encoding="utf-8") as handle:
        raw = yaml.load(handle)
    return [
        Snippet(id=str(entry["id"]), text=str(entry["text"]).strip()) for entry in raw["snippets"]
    ]


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if token not in _STOPWORDS}


def retrieve(question: str, corpus: list[Snippet], k: int = DEFAULT_TOP_K) -> list[Snippet]:
    """Deterministic top-k by query/snippet token overlap, ties broken by corpus
    order. No embeddings — reproducible offline, so the comparison isolates the LLM
    variable, not retriever nondeterminism."""
    query = _tokens(question)
    ranked = sorted(
        enumerate(corpus),
        key=lambda pair: (-len(query & _tokens(pair[1].text)), pair[0]),
    )
    return [snippet for _index, snippet in ranked[:k]]


def build_rag_messages(question: str, retrieved: list[Snippet]) -> list[dict[str, str]]:
    """Compose the single freeform RAG prompt — retrieved snippets as context +
    the operator question. NO ``response_format`` (the honest naive-RAG shape)."""
    context = "\n".join(f"- {snippet.text}" for snippet in retrieved)
    system = (
        "You are an energy operations assistant. Use ONLY the context snippets "
        "below to answer the operator. Name the specific affected asset and state "
        "the single recommended action.\n\nContext:\n" + context
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]


def answer_to_judgment(answer: str, candidate_keys: list[str]) -> LlmJudgment:
    """Adapt arm (c)'s free-text answer into the minimal ``LlmJudgment`` the grader
    checks consume (PLAN-0027 §3.1): the entity keys from the scenario's known
    universe that appear in the answer (the entity check), and the answer text as
    the action-keyword haystack. Reuses ``grade_proposal`` unchanged — never forks
    grading. A placeholder entity is used when the answer named none, so a vague
    answer grades as an entity miss (not a validation error).

    The free-text entity match is **hyphen- and case-normalized** on both sides: a
    naive-RAG answer legitimately re-cases the key (``Asset-E01`` at the start of a
    label) and emits the U+2011 non-breaking hyphen — neither is a model error
    identifying the wrong entity. This is a measurement-correctness calibration
    (Cray-ratified before the scored run, 2026-06-16), the free-text analogue of
    the procedure-baseline grader's ``normalize_primary_key`` hyphen calibration;
    it only governs how arm (c)'s text is adapted, never the shared
    ``grade_proposal`` logic, and it tightens nothing in the baseline's favour
    (it can only *recover* a correctly-named entity, never invent one)."""
    normalized = normalize_primary_key(answer).lower()
    found = [key for key in candidate_keys if normalize_primary_key(key).lower() in normalized]
    entities = [EntityRef(object_type="Asset", primary_key=key) for key in found]
    if not entities:
        entities = [EntityRef(object_type="Asset", primary_key=_NO_ENTITY)]
    body = answer.strip() or "(empty answer)"
    return LlmJudgment(
        title="(rag freeform answer)",
        description=body,
        rationale=body,
        confidence=0.0,
        affected_entities=entities,
        suggested_handler="(rag-freeform)",
        handler_payload={},
    )


def _reduced_expected(item: BenchmarkItem) -> Expected:
    """The D-1 sub-task ``Expected`` for arm (c): declares ONLY the entity +
    action-class scoring fields, so ``grade_proposal`` scores exactly those two (no
    forbidden_* precision add-ons, no handler probe — arm (c) is graded on the
    common sub-task, not arm (a)'s full hardened key)."""
    return Expected(
        disposition=item.expected.disposition,
        action_expected=item.expected.action_expected,
        affected_primary_key=item.expected.affected_primary_key,
        action_keywords=item.expected.action_keywords,
    )


def _check_passed(grade: GradeResult, name: str) -> bool:
    return any(check.name == name and check.passed for check in grade.checks)


@dataclass(frozen=True)
class ArmCResult:
    """One breach item's lean-RAG outcome.

    ``passed`` (the D-1 sub-task) = entity AND action-class both correct.
    ``judgment`` is the adapter's ``LlmJudgment`` carried for offline VERIFY
    (``--dump-json``); ``retrieved_ids`` records what the retriever surfaced (the
    joint-binding evidence)."""

    item_id: str
    answer: str
    retrieved_ids: list[str]
    entity_correct: bool
    action_correct: bool
    passed: bool
    latency_s: float
    error: str
    judgment: LlmJudgment | None


async def run_item_c(
    item: BenchmarkItem,
    client: ChatClient,
    corpus: list[Snippet],
    reading_parameter: str,
    *,
    k: int = DEFAULT_TOP_K,
) -> ArmCResult:
    """Retrieve → prompt → ONE freeform answer → grade one breach item.

    Exactly ONE ``client.chat`` call per item (D-6: no second "verify" call). A
    transport failure is recorded, never raised, so a sweep completes."""
    scenario = item.scenario
    question = render_rag_question(scenario, reading_parameter)
    retrieved = retrieve(question, corpus, k)
    messages = build_rag_messages(question, retrieved)
    retrieved_ids = [snippet.id for snippet in retrieved]
    start = time.perf_counter()
    try:
        result = await client.chat(messages)
    except OllamaError as exc:
        return ArmCResult(
            item.id,
            "",
            retrieved_ids,
            False,
            False,
            False,
            time.perf_counter() - start,
            str(exc),
            None,
        )
    latency = time.perf_counter() - start
    answer = result.content
    candidate_keys = [scenario.primary_key, *(decoy.primary_key for decoy in scenario.distractors)]
    judgment = answer_to_judgment(answer, candidate_keys)
    grade = grade_proposal(judgment, _reduced_expected(item))
    return ArmCResult(
        item_id=item.id,
        answer=answer,
        retrieved_ids=retrieved_ids,
        entity_correct=_check_passed(grade, "affected_primary_key"),
        action_correct=_check_passed(grade, "action_keywords"),
        passed=grade.passed,
        latency_s=latency,
        error="",
        judgment=judgment,
    )


__all__ = [
    "DEFAULT_CORPUS",
    "DEFAULT_TOP_K",
    "ArmCResult",
    "Snippet",
    "answer_to_judgment",
    "build_rag_messages",
    "load_corpus",
    "retrieve",
    "run_item_c",
]
