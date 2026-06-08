"""Per-item evaluation flow + run summary (PLAN-0019 B-β; SD-B1).

The harness threads one scenario through the design's two-stage grading and
aggregates a run. Pure control logic + an injected :class:`ChatClient` (the
``generate_judgment`` seam), so the whole flow is exercised offline with a mock
client; only the live RUN binds a real ``gpt-oss:20b`` (``run_benchmark.py``).

Per item:

1. deterministic :func:`grader.classify_disposition` -> the ~100% sanity verdict;
2. if (and only if) the item is a **breach**, run the live ``generate_judgment``
   two-call path and grade the :class:`LlmJudgment` proposal (the headline);
   non-breach items are the deterministic false-positive guard (no LLM call).

A scenario is fed to the model as a plain event mapping (the DB/orchestrator are
bypassed to isolate the LLM variable).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from benchmarks.procedure_baseline.grader import GradeResult, classify_disposition, grade_proposal
from benchmarks.procedure_baseline.schema import BenchmarkItem, Disposition, Scenario
from services.engine.llm.structured import (
    ChatClient,
    StructuredOutputError,
    generate_judgment,
)


def scenario_to_event(scenario: Scenario) -> dict[str, Any]:
    """Project a :class:`Scenario` into the event mapping ``generate_judgment``
    consumes — the entity + reading + threshold context, plus any extra
    ``context`` fields verbatim."""
    return {
        "event_id": scenario.event_id,
        "event_type": "reading",
        "object_type": scenario.entity_type,
        "primary_key": scenario.primary_key,
        "measured_value": scenario.measured_value,
        "unit": scenario.unit,
        "threshold": scenario.threshold,
        "direction": scenario.direction,
        **scenario.context,
    }


@dataclass(frozen=True)
class ItemResult:
    """The graded outcome of one item.

    ``disposition_correct`` is the deterministic sanity result (all items);
    ``proposal_correct`` is the headline LLM grade (breach items only — ``None``
    for the non-breach false-positive guard). ``error`` is set when the judgment
    path raised (a failed proposal = incorrect).
    """

    item_id: str
    vertical: str
    disposition_expected: Disposition
    disposition_actual: Disposition
    disposition_correct: bool
    graded: bool
    proposal_correct: bool | None
    grade: GradeResult | None
    error: str | None = None


async def evaluate_item(
    item: BenchmarkItem,
    client: ChatClient,
    *,
    vertical: str,
    goal: str | None = None,
    retry_budget: int = 3,
) -> ItemResult:
    """Evaluate one item: deterministic disposition, then (on breach) grade the
    live LLM proposal.

    Transport failures (``OllamaError``) are intentionally NOT swallowed — they
    bubble to the live runner. A :class:`StructuredOutputError` (the model never
    produced a valid judgment within the retry budget) is recorded as an incorrect
    proposal.
    """
    actual = classify_disposition(item.scenario)
    disposition_correct = actual == item.expected.disposition

    if item.expected.disposition is not Disposition.BREACH:
        # Non-breach: the engine must NOT fire an action. Deterministic guard only;
        # no LLM call (the LLM proposal path does not run for watch/ok).
        return ItemResult(
            item_id=item.id,
            vertical=vertical,
            disposition_expected=item.expected.disposition,
            disposition_actual=actual,
            disposition_correct=disposition_correct,
            graded=False,
            proposal_correct=None,
            grade=None,
        )

    event = scenario_to_event(item.scenario)
    try:
        result = await generate_judgment(
            client, event, vertical, retry_budget=retry_budget, goal=goal
        )
    except StructuredOutputError as exc:
        return ItemResult(
            item_id=item.id,
            vertical=vertical,
            disposition_expected=item.expected.disposition,
            disposition_actual=actual,
            disposition_correct=disposition_correct,
            graded=True,
            proposal_correct=False,
            grade=None,
            error=str(exc),
        )

    grade = grade_proposal(result.judgment, item.expected)
    return ItemResult(
        item_id=item.id,
        vertical=vertical,
        disposition_expected=item.expected.disposition,
        disposition_actual=actual,
        disposition_correct=disposition_correct,
        graded=True,
        proposal_correct=grade.passed,
        grade=grade,
    )


@dataclass(frozen=True)
class Summary:
    """Aggregate over a run.

    ``headline_accuracy`` (over graded breach items) is the SD-B1 ≥ 85% headline;
    ``deterministic_accuracy`` (over all items) is the separately-reported ~100%
    sanity number — the two are NOT combined.
    """

    total: int
    graded: int
    headline_correct: int
    headline_accuracy: float | None
    deterministic_correct: int
    deterministic_accuracy: float
    by_disposition: dict[str, int]


def summarize(results: Sequence[ItemResult]) -> Summary:
    """Aggregate per-item results into the two separately-reported metrics."""
    total = len(results)
    graded = [result for result in results if result.graded]
    headline_correct = sum(1 for result in graded if result.proposal_correct)
    deterministic_correct = sum(1 for result in results if result.disposition_correct)

    by_disposition: dict[str, int] = {disposition.value: 0 for disposition in Disposition}
    for result in results:
        by_disposition[result.disposition_expected.value] += 1

    return Summary(
        total=total,
        graded=len(graded),
        headline_correct=headline_correct,
        headline_accuracy=(headline_correct / len(graded)) if graded else None,
        deterministic_correct=deterministic_correct,
        deterministic_accuracy=(deterministic_correct / total) if total else 0.0,
        by_disposition=by_disposition,
    )
