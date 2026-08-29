"""Scenario: an Ollama envelope reaches the JSONL dump with its generation accounting.

Deliberately NOT built on ``FakeChatClient``. The seam under test is
"what Ollama returned" -> "what the run wrote down", and a fake chat client
hand-builds ``ChatResult.raw``, which stubs the producer side of exactly that
seam: it would prove the record-builder copies a dict someone typed in the test,
never that the client extracts the field from a real response body. So these
drive a real :class:`OllamaClient` over ``httpx.MockTransport`` — the injection
seam the client documents — through the real ``generate_judgment`` and the real
``evaluate_item`` into the real ``_item_record``. Only the network is simulated.

The envelopes replicate the two shapes session 261 measured on ``fleet-001``:
at ``num_predict=1024`` call 1 returned nothing and the item came back unscored;
at 4096 the same item produced a 7,528-char draft and a complete judgment. The
run recorded neither ``done_reason`` nor ``eval_count``, so the only way to tell
the two apart was to run both and compare — which is the gap these tests close.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from benchmarks.procedure_baseline.harness import evaluate_item
from benchmarks.procedure_baseline.run_benchmark import _item_record
from benchmarks.procedure_baseline.schema import BenchmarkItem, Expected, Scenario
from services.engine.llm.client import OllamaClient
from services.engine.registry import registry

_VERTICAL = "aquaculture"

#: The s261 measurement: qwen's fleet reasoning draft ran to 7,528 characters.
_LONG_DRAFT = "the quote sits exactly at the ceiling; " * 193


async def _noop_handler(_action: Any) -> dict[str, Any]:
    return {}


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
        id="t-demand",
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


def _envelope(
    content: str,
    *,
    done_reason: str | None,
    eval_count: int | None,
    thinking: str | None = None,
) -> httpx.Response:
    """One realistic Ollama ``/api/chat`` body.

    ``done_reason=None`` omits the key entirely rather than sending a null, which
    is how an older server that never reports it actually behaves — the case the
    truncation report must not mistake for a clean run.
    """
    message: dict[str, Any] = {"role": "assistant", "content": content}
    if thinking is not None:
        message["thinking"] = thinking
    body: dict[str, Any] = {
        "model": "qwen3.8:27b-mtp-q4_K_M",
        "message": message,
        "done": True,
        "prompt_eval_count": 1_120,
    }
    if done_reason is not None:
        body["done_reason"] = done_reason
    if eval_count is not None:
        body["eval_count"] = eval_count
    return httpx.Response(200, json=body)


def _two_call_client(call1: httpx.Response, call2: httpx.Response) -> OllamaClient:
    """A real client whose transport serves call 1 vs call 2 by the request body.

    Routed on the presence of ``format`` — the actual thing that distinguishes
    the structuring call from the reasoning call on the wire — rather than on a
    call counter, so a retry of call 2 is served the call-2 response instead of
    running off the end of a fixed list.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        return call2 if "format" in body else call1

    return OllamaClient(
        base_url="http://ollama.test",
        model="qwen3.8:27b-mtp-q4_K_M",
        transport=httpx.MockTransport(handler),
    )


async def test_a_truncated_reasoning_call_reaches_the_dump_as_truncated() -> None:
    """The s261 run-A shape: call 1 hits the cap and produces nothing.

    What the dump said at the time was only ``draft: null`` — indistinguishable
    from a model that legitimately returned an empty draft. ``done_reason`` is
    what separates "the cap cut it" from "the model had nothing to say", and it
    has to survive all the way into the record to be of any use offline.
    """
    registry.register_handler(_VERTICAL, "echo", _noop_handler)
    client = _two_call_client(
        _envelope("", done_reason="length", eval_count=1024),
        _envelope("not json at all", done_reason="stop", eval_count=12),
    )

    result = await evaluate_item(_breach_item(), client, vertical=_VERTICAL, retry_budget=1)
    record = _item_record(result)

    reasoning = [c for c in record["calls"] if c["role"] == "reasoning"]
    assert reasoning, "the reasoning call left no metrics in the record"
    assert reasoning[0]["truncated"] is True, (
        "a call Ollama ended with done_reason='length' is not marked truncated in "
        "the dump, so an offline reader cannot tell a cut draft from a short one"
    )
    assert reasoning[0]["done_reason"] == "length"
    assert reasoning[0]["eval_count"] == 1024


async def test_metrics_survive_the_failure_path() -> None:
    """A judgment that never validated still has to carry its accounting.

    This is the case that matters most: an exhausted retry budget is precisely
    what a starved reasoning pass produces, so metrics attached only to a
    successful exchange would be missing from every run worth diagnosing. The
    item is unscored here — and the record must still say why.
    """
    registry.register_handler(_VERTICAL, "echo", _noop_handler)
    client = _two_call_client(
        _envelope("", done_reason="length", eval_count=1024),
        _envelope("not json at all", done_reason="stop", eval_count=12),
    )

    result = await evaluate_item(_breach_item(), client, vertical=_VERTICAL, retry_budget=1)
    record = _item_record(result)

    assert record["error"] is not None, "precondition: this exchange must have failed"
    assert record["judgment"] is None
    assert len(record["calls"]) == 2, (
        f"the failed exchange recorded {len(record['calls'])} calls; both the "
        "reasoning call and the structuring attempt must be accounted for"
    )
    assert [c["role"] for c in record["calls"]] == ["reasoning", "structuring"]


async def test_the_reasoning_draft_survives_the_failure_path() -> None:
    """A failed exchange must still say WHAT call 1 produced.

    This is the misreading session 261 actually made. Run A recorded
    ``draft: null`` and it was read as "call 1 produced nothing" — but the harness
    assigned ``draft`` only on the success path, so that null was written whether
    call 1 emitted nothing or emitted seven thousand characters that call 2 then
    failed to structure. The two states were indistinguishable, and the mechanism
    story built on the null was wrong.

    Call 1 here returns a full draft and call 2 returns unparseable output, which
    is exactly that shape: the item ends unscored, and the draft must survive
    anyway.
    """
    registry.register_handler(_VERTICAL, "echo", _noop_handler)
    client = _two_call_client(
        _envelope(_LONG_DRAFT, done_reason="stop", eval_count=1_893),
        _envelope("not json at all", done_reason="stop", eval_count=12),
    )

    result = await evaluate_item(_breach_item(), client, vertical=_VERTICAL, retry_budget=1)
    record = _item_record(result)

    assert record["error"] is not None, "precondition: this exchange must have failed"
    assert record["judgment"] is None, "precondition: a failed exchange has no judgment"
    assert record["draft"] == _LONG_DRAFT, (
        "the reasoning draft did not survive the failure path, so an unscored item "
        "cannot be told apart from one whose reasoning pass produced nothing"
    )


async def test_a_healthy_exchange_records_demand_and_no_truncation() -> None:
    """The s261 run-B shape: a long draft that ended on its own, and a valid judgment.

    The positive control for the two tests above. It is what makes their
    assertions mean something: ``truncated`` has to be able to come back False on
    a real envelope, or marking it True proves nothing.
    """
    registry.register_handler(_VERTICAL, "echo", _noop_handler)
    client = _two_call_client(
        _envelope(_LONG_DRAFT, done_reason="stop", eval_count=1_893),
        _envelope(_judgment_json(), done_reason="stop", eval_count=220),
    )

    result = await evaluate_item(_breach_item(), client, vertical=_VERTICAL, retry_budget=1)
    record = _item_record(result)

    assert record["judgment"] is not None, "precondition: this exchange must have succeeded"
    assert [c["truncated"] for c in record["calls"]] == [False, False]
    assert [c["eval_count"] for c in record["calls"]] == [1_893, 220]
    # Demand is only interpretable next to the input that produced it.
    assert all(c["prompt_eval_count"] == 1_120 for c in record["calls"])


async def test_a_missing_done_reason_is_recorded_as_absent_not_as_clean() -> None:
    """A server that never reports done_reason must not read as a clean run.

    Every call scores ``truncated=False`` when the field is absent, so a
    truncation count alone would print a reassuring zero that actually means
    "not measured". The record has to preserve the difference, and it does so by
    keeping ``done_reason`` null — which the test above, on identical wiring but
    with the field present, shows is a real distinction and not a constant.
    """
    registry.register_handler(_VERTICAL, "echo", _noop_handler)
    client = _two_call_client(
        _envelope(_LONG_DRAFT, done_reason=None, eval_count=None),
        _envelope(_judgment_json(), done_reason=None, eval_count=None),
    )

    result = await evaluate_item(_breach_item(), client, vertical=_VERTICAL, retry_budget=1)
    record = _item_record(result)

    assert record["judgment"] is not None, "precondition: this exchange must have succeeded"
    assert all(c["done_reason"] is None for c in record["calls"]), (
        "an absent done_reason was not preserved as null, so 'unmeasured' and "
        "'measured clean' collapse into the same record"
    )
    assert all(c["eval_count"] is None for c in record["calls"])
    # Not vacuous: the content still arrived, so the exchange really ran and the
    # nulls above are the absent ORACLE, not an absent response.
    assert all(c["content_chars"] > 0 for c in record["calls"])
