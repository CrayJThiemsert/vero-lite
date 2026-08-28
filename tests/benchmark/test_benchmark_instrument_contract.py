"""Scenario tests for the benchmark instrument's contract (CLAUDE.md §8).

These drive the REAL producer into the REAL consumer on REAL dataset items —
``evaluate_item`` (the shipped harness) into ``run_benchmark._item_record`` (the
shipped dump serialiser), over items loaded from the shipped
``fleet_maintenance.yaml`` rather than hand-built stubs. A mock-fed unit suite
agrees with itself by construction: it proves the contract its author imagined,
never the one the system produces.

Every claim here was made false first, on purpose, and watched go red.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from benchmarks.procedure_baseline.harness import evaluate_item, summarize
from benchmarks.procedure_baseline.loader import DATASET_DIR, load_dataset
from benchmarks.procedure_baseline.run_benchmark import _item_record, _register_all_handlers
from benchmarks.procedure_baseline.schema import BenchmarkItem, Disposition
from services.engine.llm.client import ChatResult

_VERTICAL = "fleet_maintenance"


class RecordingChatClient:
    """Replays canned results and keeps every message list it was handed.

    Records the messages — not just the flags — because the catalog assertion is
    about what actually reached the model's context, and a client that only
    remembers ``think`` cannot answer that.
    """

    def __init__(self, results: list[ChatResult]) -> None:
        self._results = list(results)
        self.messages: list[list[dict[str, str]]] = []

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        self.messages.append([dict(message) for message in messages])
        if not self._results:
            raise AssertionError("RecordingChatClient exhausted its canned results")
        return self._results.pop(0)


def _chat(content: str, *, thinking: str | None = None) -> ChatResult:
    return ChatResult(content=content, thinking=thinking, model="gpt-oss:20b", raw={})


def _first_breach_item() -> BenchmarkItem:
    """A real authored item from the shipped fleet dataset."""
    dataset = load_dataset(DATASET_DIR / "fleet_maintenance.yaml")
    return next(item for item in dataset.items if item.expected.disposition is Disposition.BREACH)


def _judgment_for(item: BenchmarkItem) -> str:
    return json.dumps(
        {
            "title": f"Escalate the repair quote for {item.scenario.primary_key}",
            "description": "The quote is above the truck's minor-repair ceiling.",
            "rationale": "Authority for this spend sits above the requester.",
            "confidence": 0.9,
            "affected_entities": [
                {"object_type": "Truck", "primary_key": item.scenario.primary_key}
            ],
            "suggested_handler": "escalate",
            "handler_payload": {"truck_id": item.scenario.primary_key},
        }
    )


@pytest.fixture(autouse=True)
def _registered() -> None:
    _register_all_handlers([_VERTICAL])


async def test_the_reasoning_draft_reaches_the_dump() -> None:
    """The call-1 draft is persisted, so a run can be re-read offline.

    Phase 1.6 concluded things about what the reasoning pass did to the decision
    while the dumps carried no draft at all — the account rested on the call-2
    rationale, which is the draft's downstream echo. Persisting it is what makes
    the next matrix run explainable.
    """
    item = _first_breach_item()
    client = RecordingChatClient(
        [
            _chat("the quote exceeds this truck's own ceiling", thinking="weighing authority"),
            _chat(_judgment_for(item)),
        ]
    )

    result = await evaluate_item(item, client, vertical=_VERTICAL, reasoning_mode="full")
    record = _item_record(result)

    assert record["draft"] == "the quote exceeds this truck's own ceiling"
    assert record["thinking"] == "weighing authority"


async def test_the_dump_carries_this_run_s_draft_not_a_constant() -> None:
    """Positive control for the assertion above.

    A test that pins one draft string cannot tell "the dump carries the draft"
    from "the dump carries a hard-coded string that happens to match". Running the
    same path with a DIFFERENT draft must move the dump.
    """
    item = _first_breach_item()
    drafts = []
    for text in ("first reasoning pass", "an entirely different second pass"):
        client = RecordingChatClient([_chat(text, thinking=None), _chat(_judgment_for(item))])
        result = await evaluate_item(item, client, vertical=_VERTICAL, reasoning_mode="full")
        drafts.append(_item_record(result)["draft"])

    # One assertion, not two: `drafts[0] != drafts[1]` is implied by the equality
    # above and could never redden on its own, so it would be a claim no probe can
    # witness — decoration in the shape of evidence.
    assert drafts == ["first reasoning pass", "an entirely different second pass"]


async def test_skip_mode_records_no_draft() -> None:
    """The absence claim carries its own control.

    "No draft in the dump" is satisfied by a dump that never records one, so this
    is only meaningful beside the two tests above, which show the same path DOES
    record one when a call 1 ran.
    """
    item = _first_breach_item()
    # Two canned results although skip should consume ONE, so a mutation that
    # wrongly runs call 1 fails the call-count ASSERTION rather than crashing the
    # client — a crash is not a witnessed red, and the driver refuses to credit it.
    client = RecordingChatClient([_chat(_judgment_for(item)), _chat(_judgment_for(item))])

    result = await evaluate_item(item, client, vertical=_VERTICAL, reasoning_mode="skip")
    record = _item_record(result)

    # Call count first: a mutation that reinstates call 1 changes the draft too, so
    # this claim is only independently witnessable while it is the first to fail.
    assert len(client.messages) == 1, "skip runs exactly one call"
    assert record["draft"] == ""
    assert record["thinking"] is None


async def test_the_handler_catalog_reaches_the_model_when_enabled() -> None:
    """With the catalog on, the model is told what each handler MEANS.

    The benchmark hardcoded this off while the product ships it on, so every
    matrix number was measured with the model choosing between bare enum names
    and no description of any of them. Both directions are asserted: a green here
    with no off-case would not distinguish "the catalog is threaded" from "this
    text is always present".
    """
    item = _first_breach_item()

    on_client = RecordingChatClient([_chat("draft"), _chat(_judgment_for(item))])
    await evaluate_item(
        item, on_client, vertical=_VERTICAL, reasoning_mode="full", include_handler_catalog=True
    )
    on_system = on_client.messages[0][0]["content"]

    off_client = RecordingChatClient([_chat("draft"), _chat(_judgment_for(item))])
    await evaluate_item(
        item, off_client, vertical=_VERTICAL, reasoning_mode="full", include_handler_catalog=False
    )
    off_system = off_client.messages[0][0]["content"]

    assert "AVAILABLE ACTIONS" in on_system
    assert "tow_to_partner_garage" in on_system
    assert "AVAILABLE ACTIONS" not in off_system
    assert "tow_to_partner_garage" not in off_system


async def test_an_unanswered_item_is_unscored_in_the_dump_and_the_summary() -> None:
    """End-to-end: a judgment that never arrived must not read as a wrong answer.

    Driven through the real harness and the real serialiser rather than by
    constructing an ItemResult, because the defect being fixed lived in the path
    between them.
    """
    item = _first_breach_item()
    client = RecordingChatClient([_chat("draft"), _chat("this is not json")])

    result = await evaluate_item(item, client, vertical=_VERTICAL, retry_budget=1)
    record = _item_record(result)

    assert record["graded"] is True, "attempted"
    assert record["proposal_correct"] is None, "attempted but unscored — NOT False"
    assert record["error"] is not None

    summary = summarize([result])
    assert summary.headline_errors == 1
    assert summary.headline_scored == 0
    assert summary.headline_accuracy is None
