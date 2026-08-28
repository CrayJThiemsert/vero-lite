"""The per-judgment deadline and per-item latency (FDE program phase 1.6).

Cray's rule, typed 2026-08-28: *one task should not take more than five minutes;
past that, treat it as something being wrong and keep the log*. That makes the
ceiling a **tripwire**, not merely a timeout — a breach has to be nameable
afterwards, which an aggregate p95 can never do.

Offline: the model is a mock ``ChatClient`` that sleeps, so the deadline is
exercised without touching MS-S1.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from benchmarks.procedure_baseline.harness import evaluate_item
from benchmarks.procedure_baseline.run_benchmark import _item_record, _print_deadline_breaches
from benchmarks.procedure_baseline.schema import BenchmarkItem, Expected, Scenario
from services.engine.llm.client import ChatResult
from services.engine.registry import registry

_VERTICAL = "aquaculture"


async def _noop_handler(_action: Any) -> dict[str, Any]:
    return {}


class SlowChatClient:
    """Replays canned results, but each call takes ``delay`` seconds."""

    def __init__(self, results: list[ChatResult], *, delay: float) -> None:
        self._results = list(results)
        self._delay = delay
        self.calls = 0

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        self.calls += 1
        await asyncio.sleep(self._delay)
        if not self._results:
            raise AssertionError("SlowChatClient exhausted its canned results")
        return self._results.pop(0)


def _result(content: str, *, thinking: str | None = None) -> ChatResult:
    return ChatResult(content=content, thinking=thinking, model="stub", raw={})


def _judgment_json() -> str:
    return json.dumps(
        {
            "title": "Start emergency aerator on pond-A1",
            "description": "DO crashed below the 4 mg/L floor; aerate to recover oxygen.",
            "rationale": "Breach reading; aerate immediately.",
            "confidence": 0.9,
            "affected_entities": [{"object_type": "Pond", "primary_key": "pond-A1"}],
            "suggested_handler": "echo",
            "handler_payload": {"pond_id": "pond-A1"},
        }
    )


def _breach_item() -> BenchmarkItem:
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
        expected=Expected.model_validate(
            {
                "disposition": "breach",
                "action_expected": True,
                "affected_primary_key": "pond-A1",
                "canonical_handler": "echo",
                "action_keywords": ["aerat"],
            }
        ),
    )


@pytest.fixture(autouse=True)
def _register_echo() -> None:
    registry.register_handler(_VERTICAL, "echo", _noop_handler)


def _client(delay: float) -> SlowChatClient:
    return SlowChatClient(
        [_result("reasoning draft", thinking="t"), _result(_judgment_json())], delay=delay
    )


# --- the tripwire -------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_judgment_past_the_deadline_is_cut_and_named(tmp_path: Any) -> None:
    """The whole exchange is bounded, not one call — a task is the unit."""
    result = await evaluate_item(
        _breach_item(),
        _client(delay=0.2),
        vertical=_VERTICAL,
        judgment_deadline_s=0.05,
    )

    assert result.error is not None
    assert result.error.startswith("DEADLINE-BREACH")


@pytest.mark.asyncio
async def test_a_breach_is_not_reported_as_a_model_failure() -> None:
    """The run was CUT; what it would have produced is unknown, and the wording
    has to keep those apart or a slow box reads as a bad model."""
    result = await evaluate_item(
        _breach_item(), _client(delay=0.2), vertical=_VERTICAL, judgment_deadline_s=0.05
    )

    assert "DEADLINE" in (result.error or "")
    assert "Ollama" not in (result.error or "")


@pytest.mark.asyncio
async def test_a_judgment_inside_the_deadline_is_untouched() -> None:
    """Positive control: the deadline does not cut a task that fits."""
    result = await evaluate_item(
        _breach_item(), _client(delay=0.0), vertical=_VERTICAL, judgment_deadline_s=30.0
    )

    assert result.error is None
    assert result.judgment is not None


@pytest.mark.asyncio
async def test_no_deadline_leaves_the_previous_behaviour_unchanged() -> None:
    """The flag is additive — omitting it must not bound anything."""
    result = await evaluate_item(_breach_item(), _client(delay=0.05), vertical=_VERTICAL)

    assert result.error is None
    assert result.judgment is not None


# --- per-item latency ---------------------------------------------------------


@pytest.mark.asyncio
async def test_every_judged_item_carries_its_own_wall_clock() -> None:
    result = await evaluate_item(_breach_item(), _client(delay=0.0), vertical=_VERTICAL)

    assert result.judgment_latency_s is not None
    assert result.judgment_latency_s >= 0.0


@pytest.mark.asyncio
async def test_a_cut_item_still_reports_how_long_it_ran() -> None:
    """A breach with no elapsed time would be unusable as investigation evidence."""
    result = await evaluate_item(
        _breach_item(), _client(delay=0.3), vertical=_VERTICAL, judgment_deadline_s=0.05
    )

    assert result.judgment_latency_s is not None
    assert result.judgment_latency_s > 0.0


@pytest.mark.asyncio
async def test_the_latency_reaches_the_dump_record() -> None:
    """Through the SHIPPED record builder, not a local copy of its shape."""
    result = await evaluate_item(_breach_item(), _client(delay=0.0), vertical=_VERTICAL)

    record = _item_record(result)

    assert "judgment_latency_s" in record
    assert record["judgment_latency_s"] is not None


# --- reporting ----------------------------------------------------------------


def test_a_clean_run_says_zero_breaches_rather_than_printing_nothing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Absence must be RENDERED: a missing line is indistinguishable from a run
    where the flag was never passed."""
    _print_deadline_breaches([], 300.0)

    assert "0 breaches" in capsys.readouterr().out


def test_no_deadline_set_says_so(capsys: pytest.CaptureFixture[str]) -> None:
    _print_deadline_breaches([], None)

    assert "none set" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_a_breached_run_names_the_offending_item(
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = await evaluate_item(
        _breach_item(), _client(delay=0.3), vertical=_VERTICAL, judgment_deadline_s=0.05
    )

    _print_deadline_breaches([result], 0.05)

    out = capsys.readouterr().out
    assert "1 BREACHES" in out
    assert "t-breach" in out
