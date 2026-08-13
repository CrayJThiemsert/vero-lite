"""Scenario — "how many operational events per asset?" end to end (PLAN-0104 AC-2).

CLAUDE.md §8, binding: a scenario test drives the **real producer into the real
consumer on realistic simulated data**. Here that means the only thing stubbed is
the *model transport*; every stage that touches or shapes data is the shipped one:

    translate  -> canned constrained-JSON response (the transport stub, and the
                  established offline pattern for this module)
    execute    -> real ``_compute_group_count`` over the real energy synthetic
                  adapter's 13 events
    relabel    -> real ``_relabel_groups``, which really fetches the Asset records
                  to map ``asset_id`` -> the asset's title
    phrase     -> real deterministic fallback (``_phrase_aggregate``'s count
                  branch), reached by failing the phrase transport

A test that stubbed either side of the execute/phrase seam would agree with
itself by construction; this one can only pass if the engine really computes the
cardinalities and really names them.

⚠️ **This scenario makes NO claim that the live model emits `count` + `group_by`.**
The translate JSON is canned by design. That claim is AC-7's alone and is settled
only by the gated MS-S1 run in Step 7 — a fixture can never settle it.

Expected per-asset counts are hand-verified against
``verticals/energy/data_adapter/synthetic.py`` (the gold set's own stated bar):
Battery Bank A 5, Inverter Unit A 3, Battery Bank B 3, Feeder Meter A 2 = 13.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import pytest

from services.engine.llm.client import ChatResult, OllamaError
from services.engine.nl_query import answer_question
from verticals.energy.data_adapter import register_energy_adapter

QUESTION = "How many operational events are recorded for each asset?"

#: The per-asset cardinalities the engine must produce, hand-derived from
#: ``synthetic.py``. Keys are asset TITLES, not ids — proving the relabel ran.
EXPECTED_GROUPS = {
    "Battery Bank A": 5.0,
    "Inverter Unit A": 3.0,
    "Battery Bank B": 3.0,
    "Feeder Meter A": 2.0,
}


@pytest.fixture
def energy_adapter() -> Iterator[None]:
    """Register the real energy synthetic adapter for the duration of a test."""
    register_energy_adapter()
    yield


class _TranslateOnlyStub:
    """Stubs the MODEL TRANSPORT and nothing else.

    A call carrying ``response_format`` is the translate stage and returns the
    canned query JSON; the phrase call raises, which routes phrasing to the real
    deterministic template. Both are transport behaviours — no engine seam is
    replaced.
    """

    def __init__(self, query: dict[str, Any]) -> None:
        self._query_json = json.dumps(query)
        self.translate_calls = 0

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        if response_format is not None:
            self.translate_calls += 1
            return ChatResult(content=self._query_json, thinking=None, model="stub", raw={})
        raise OllamaError("forced phrase transport failure — exercise the deterministic answer")


async def test_events_per_asset_is_counted_relabelled_and_named(energy_adapter: None) -> None:
    """The flagship grouped-count question, end to end on the real dataset."""
    client = _TranslateOnlyStub(
        {"object_type": "OperationalEvent", "operation": "count", "group_by": "asset_id"}
    )

    answer = await answer_question(QUESTION, "energy", client=client)

    assert answer.grounded is True
    assert answer.aggregate is not None
    assert answer.aggregate.operation == "count"
    # SD-1 (a): a count names no property — the receipt says so rather than
    # carrying a property the figure was never computed over.
    assert answer.aggregate.property is None

    # The per-group cardinalities, keyed by the asset TITLE (the relabel really ran
    # — an unrelabelled result would be keyed 'asset-battery-01' and fail here).
    assert answer.aggregate.groups == EXPECTED_GROUPS

    # The receipt is the FULL matched set for a count, never a limit-truncated slice.
    assert answer.result_count == 13
    assert len(answer.source_object_ids) == 13
    assert answer.aggregate.value == 13.0

    # Nothing is lost or double-counted: every event joins exactly one group.
    assert sum(answer.aggregate.groups.values()) == answer.aggregate.value

    # The phrased answer names EVERY group with its exact cardinality.
    for title, cardinality in EXPECTED_GROUPS.items():
        assert f"{title} = {int(cardinality)}" in answer.answer


async def test_the_grouped_answer_differs_from_the_ungrouped_one(energy_adapter: None) -> None:
    """The grouping must change the OUTPUT, not merely the query.

    Asking the same corpus without ``group_by`` yields the same total and no
    breakdown. If the grouped branch were severed — or never wired — both answers
    would be this flat sentence, and the scenario above could pass on the total
    alone. This is the paired read that makes that impossible.
    """
    flat = await _answer_with(
        {"object_type": "OperationalEvent", "operation": "count"},
    )
    grouped = await _answer_with(
        {"object_type": "OperationalEvent", "operation": "count", "group_by": "asset_id"},
    )

    assert flat.result_count == grouped.result_count == 13
    assert flat.aggregate is None
    assert grouped.aggregate is not None
    assert flat.answer != grouped.answer
    assert "Battery Bank A" not in flat.answer
    assert "Battery Bank A" in grouped.answer


async def _answer_with(query: dict[str, Any]) -> Any:
    """Run one question through the real engine with a canned translate output."""
    return await answer_question(QUESTION, "energy", client=_TranslateOnlyStub(query))
