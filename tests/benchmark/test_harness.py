"""Harness end-to-end unit tests (PLAN-0019 B-β) — offline, mock ``ChatClient``.

The thin slice that proves the whole design works without MS-S1: a breach item
runs the two-call judgment path (mocked) and is graded; a watch/ok item is the
deterministic guard and never calls the model; a judgment that never validates is
recorded as an incorrect proposal; and ``summarize`` keeps the headline and the
deterministic sanity number separate (SD-B1).
"""

from __future__ import annotations

import json
from typing import Any

from benchmarks.procedure_baseline.grader import GradeResult, classify_disposition
from benchmarks.procedure_baseline.harness import (
    ItemResult,
    evaluate_item,
    scenario_to_event,
    summarize,
)
from benchmarks.procedure_baseline.schema import (
    BenchmarkItem,
    Disposition,
    Expected,
    Scenario,
)
from services.engine.llm.client import ChatResult
from services.engine.registry import registry

_VERTICAL = "aquaculture"


class FakeChatClient:
    """Replays canned ChatResults in order; records every call (house pattern)."""

    def __init__(self, results: list[ChatResult]) -> None:
        self._results = list(results)
        self.calls: list[dict[str, Any]] = []

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        self.calls.append({"think": think, "has_format": response_format is not None})
        if not self._results:
            raise AssertionError("FakeChatClient exhausted its canned results")
        return self._results.pop(0)


async def _noop_handler(_action: Any) -> dict[str, Any]:
    return {}


def _result(content: str, *, thinking: str | None = None) -> ChatResult:
    return ChatResult(content=content, thinking=thinking, model="gpt-oss:20b", raw={})


def _judgment_json(**overrides: Any) -> str:
    base: dict[str, Any] = {
        "title": "Start emergency aerator on pond-A1",
        "description": "DO crashed below the 4 mg/L floor; aerate to recover oxygen.",
        "rationale": "Breach reading; aerate immediately.",
        "confidence": 0.9,
        "affected_entities": [{"object_type": "Pond", "primary_key": "pond-A1"}],
        "suggested_handler": "echo",
        "handler_payload": {"pond_id": "pond-A1"},
    }
    base.update(overrides)
    return json.dumps(base)


def _breach_item(**expected_overrides: Any) -> BenchmarkItem:
    expected: dict[str, Any] = {
        "disposition": "breach",
        "action_expected": True,
        "affected_primary_key": "pond-A1",
        "valid_handlers": ["echo"],
        "action_keywords": ["aerat"],
    }
    expected.update(expected_overrides)
    return BenchmarkItem(
        id="t-breach",
        description="DO 2.1 — breach",
        scenario=Scenario(
            event_id="evt-1",
            entity_type="Pond",
            primary_key="pond-A1",
            measured_value=2.1,
            unit="mg/L",
            threshold=4.0,
            direction="below",
            watch_margin=1.0,
        ),
        expected=Expected.model_validate(expected),
    )


def _watch_item() -> BenchmarkItem:
    return BenchmarkItem(
        id="t-watch",
        description="DO 4.5 — watch",
        scenario=Scenario(
            event_id="evt-2",
            entity_type="Pond",
            primary_key="pond-A4",
            measured_value=4.5,
            unit="mg/L",
            threshold=4.0,
            direction="below",
            watch_margin=1.0,
        ),
        expected=Expected(disposition=Disposition.WATCH, action_expected=False),
    )


def test_scenario_to_event_carries_entity_and_reading() -> None:
    event = scenario_to_event(_breach_item().scenario)
    assert event["event_id"] == "evt-1"
    assert event["primary_key"] == "pond-A1"
    assert event["measured_value"] == 2.1
    assert event["threshold"] == 4.0
    assert "parameter" not in event  # omitted when no reading_parameter supplied


def test_scenario_to_event_injects_reading_parameter() -> None:
    """The domain parameter is injected so the model knows WHAT is measured."""
    event = scenario_to_event(_breach_item().scenario, "dissolved_oxygen")
    assert event["parameter"] == "dissolved_oxygen"


async def test_breach_item_runs_the_llm_and_grades_pass() -> None:
    registry.register_handler(_VERTICAL, "echo", _noop_handler)
    client = FakeChatClient([_result("draft", thinking="r"), _result(_judgment_json())])

    result = await evaluate_item(_breach_item(), client, vertical=_VERTICAL)

    assert result.disposition_actual is Disposition.BREACH
    assert result.disposition_correct is True
    assert result.graded is True
    assert result.proposal_correct is True
    assert isinstance(result.grade, GradeResult) and result.grade.passed
    assert len(client.calls) == 2  # two-call Pattern B ran


async def test_breach_item_with_wrong_entity_grades_fail() -> None:
    registry.register_handler(_VERTICAL, "echo", _noop_handler)
    wrong = _judgment_json(affected_entities=[{"object_type": "Pond", "primary_key": "pond-WRONG"}])
    client = FakeChatClient([_result("draft", thinking="r"), _result(wrong)])

    result = await evaluate_item(_breach_item(), client, vertical=_VERTICAL)

    assert result.graded is True
    assert result.proposal_correct is False


async def test_non_breach_item_is_not_graded_and_never_calls_the_model() -> None:
    client = FakeChatClient([])  # would raise on any chat() call

    result = await evaluate_item(_watch_item(), client, vertical=_VERTICAL)

    assert result.disposition_actual is Disposition.WATCH
    assert result.disposition_correct is True
    assert result.graded is False
    assert result.proposal_correct is None
    assert client.calls == [], "watch/ok items must not invoke the LLM"


async def test_structured_output_failure_is_an_incorrect_proposal() -> None:
    registry.register_handler(_VERTICAL, "echo", _noop_handler)
    # one reasoning draft + 3 un-parseable structuring attempts exhausts the budget
    client = FakeChatClient(
        [_result("draft", thinking="r"), _result("nope"), _result("nope"), _result("nope")]
    )

    result = await evaluate_item(_breach_item(), client, vertical=_VERTICAL, retry_budget=3)

    assert result.graded is True
    assert result.proposal_correct is False
    assert result.grade is None
    assert result.error is not None


def test_summarize_separates_headline_from_deterministic_sanity() -> None:
    """Headline = mean over graded breach items; deterministic = mean over all.
    A correct deterministic disposition on a FAILED proposal must not inflate the
    headline (the two metrics are independent)."""
    results = [
        ItemResult("a", _VERTICAL, Disposition.BREACH, Disposition.BREACH, True, True, True, None),
        ItemResult("b", _VERTICAL, Disposition.BREACH, Disposition.BREACH, True, True, False, None),
        ItemResult("c", _VERTICAL, Disposition.WATCH, Disposition.WATCH, True, False, None, None),
        ItemResult("d", _VERTICAL, Disposition.OK, Disposition.OK, True, False, None, None),
    ]

    summary = summarize(results)

    assert summary.total == 4
    assert summary.graded == 2
    assert summary.headline_correct == 1
    assert summary.headline_accuracy == 0.5  # 1 of 2 breach proposals
    assert summary.deterministic_correct == 4
    assert summary.deterministic_accuracy == 1.0
    assert summary.by_disposition == {"breach": 2, "watch": 1, "ok": 1}


def test_summarize_handles_no_graded_items() -> None:
    results = [
        ItemResult("c", _VERTICAL, Disposition.OK, Disposition.OK, True, False, None, None),
    ]
    summary = summarize(results)
    assert summary.graded == 0
    assert summary.headline_accuracy is None
    assert summary.deterministic_accuracy == 1.0


def test_dataset_scenarios_classify_as_authored() -> None:
    """Sanity bridge: the harness's classifier and the schema agree on a known item."""
    item = _breach_item()
    assert classify_disposition(item.scenario) is item.expected.disposition
