"""Tests for structured-output generation + retry + semantic checks.

PLAN-0006 Step 3 / §7.2. Lesson #7 §3: in-process assertions on returned
objects and on a fake chat client — no live LLM, deterministic, offline.
The fake returns canned ``ChatResult`` objects in order (call 1 reasons,
call 2+ structure), so malformed-then-valid recovery and retry counts are
asserted directly.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from services.engine.llm.client import ChatResult
from services.engine.llm.structured import (
    LlmJudgment,
    StructuredOutputError,
    generate_judgment,
)
from services.engine.registry import registry

_EVENT: dict[str, Any] = {
    "event_id": "event-reading-07",
    "event_type": "reading",
    "measured_value": 96.5,
    "unit": "celsius",
    "asset_id": "asset-battery-07",
}


class FakeChatClient:
    """A ChatClient stand-in that replays canned ChatResults in order."""

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
        self.calls.append(
            {
                "think": think,
                "has_format": response_format is not None,
                "response_format": response_format,
                "messages": messages,
            }
        )
        if not self._results:
            raise AssertionError("FakeChatClient exhausted its canned results")
        return self._results.pop(0)


async def _noop_handler(_action: Any) -> dict[str, Any]:
    return {}


def _result(content: str, *, thinking: str | None = None, model: str = "gpt-oss:20b") -> ChatResult:
    return ChatResult(content=content, thinking=thinking, model=model, raw={})


def _judgment_dict(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "title": "Investigate over-temperature on asset-battery-07",
        "description": "Reading 96.5 celsius crossed the 90.0 celsius threshold.",
        "rationale": "Temperature exceeds the safe threshold; escalate for human review.",
        "confidence": 0.9,
        "affected_entities": [{"object_type": "Asset", "primary_key": "asset-battery-07"}],
        "suggested_handler": "echo",
        "handler_payload": {"event_id": "event-reading-07"},
    }
    base.update(overrides)
    return base


def _valid_json(**overrides: Any) -> str:
    return json.dumps(_judgment_dict(**overrides))


async def test_valid_json_first_try() -> None:
    """§7.2: a schema-valid response yields a JudgmentResult on attempt 1."""
    registry.register_handler("energy", "echo", _noop_handler)
    client = FakeChatClient([_result("draft", thinking="reasoned"), _result(_valid_json())])

    out = await generate_judgment(client, _EVENT, "energy", retry_budget=3)

    assert out.attempts == 1
    assert out.judgment.suggested_handler == "echo"
    assert out.judgment.confidence == 0.9
    assert out.thinking == "reasoned"
    assert out.draft == "draft"
    assert out.model == "gpt-oss:20b"


async def test_reasoning_mode_full_is_two_calls_with_think_on() -> None:
    """PLAN-0020 lever, default `full`: call 1 reasons (think=True), call 2 structures."""
    registry.register_handler("energy", "echo", _noop_handler)
    client = FakeChatClient([_result("draft", thinking="r"), _result(_valid_json())])

    out = await generate_judgment(client, _EVENT, "energy", reasoning_mode="full")

    assert len(client.calls) == 2
    assert client.calls[0]["think"] is True  # call 1 reasons with extended thinking
    assert client.calls[0]["has_format"] is False
    assert client.calls[1]["has_format"] is True  # call 2 is the constrained emit
    assert out.draft == "draft" and out.thinking == "r"


async def test_reasoning_mode_think_off_keeps_two_calls_but_call1_think_false() -> None:
    """`think_off`: the two-call shape is retained, but call 1 drops extended thinking
    (think=False) — and call 1 has no format, so Ollama #15260 does not apply."""
    registry.register_handler("energy", "echo", _noop_handler)
    client = FakeChatClient([_result("draft", thinking=None), _result(_valid_json())])

    out = await generate_judgment(client, _EVENT, "energy", reasoning_mode="think_off")

    assert len(client.calls) == 2
    assert client.calls[0]["think"] is False  # call 1 reasons WITHOUT extended thinking
    assert client.calls[0]["has_format"] is False
    assert client.calls[1]["has_format"] is True
    assert out.draft == "draft"


async def test_reasoning_mode_skip_is_a_single_structured_call() -> None:
    """`skip`: call 1 is omitted entirely — exactly one (structured) call, and the
    returned draft/thinking are empty since no reasoning output existed."""
    registry.register_handler("energy", "echo", _noop_handler)
    client = FakeChatClient([_result(_valid_json())])  # only ONE canned result

    out = await generate_judgment(client, _EVENT, "energy", reasoning_mode="skip")

    assert len(client.calls) == 1
    assert client.calls[0]["has_format"] is True  # the lone call is the constrained emit
    assert client.calls[0]["think"] is None  # the structured call never sets think
    assert out.draft == "" and out.thinking is None
    assert out.judgment.suggested_handler == "echo"  # still a valid judgment


async def test_malformed_then_valid_recovers_within_budget() -> None:
    """§7.2: malformed-then-valid recovers; the retry count is asserted."""
    registry.register_handler("energy", "echo", _noop_handler)
    client = FakeChatClient(
        [_result("draft", thinking="r"), _result("not json at all"), _result(_valid_json())]
    )

    out = await generate_judgment(client, _EVENT, "energy", retry_budget=3)
    assert out.attempts == 2


async def test_retry_budget_exhausted_raises() -> None:
    """§7.2: the budget bounds the loop — 1 reasoning + 3 structuring calls."""
    registry.register_handler("energy", "echo", _noop_handler)
    client = FakeChatClient(
        [_result("draft", thinking="r"), _result("x"), _result("x"), _result("x")]
    )

    with pytest.raises(StructuredOutputError):
        await generate_judgment(client, _EVENT, "energy", retry_budget=3)
    assert len(client.calls) == 4


async def test_unregistered_handler_is_rejected() -> None:
    """§7.2: a handler not in the registry fails the semantic check."""
    # no handler registered for 'energy' — 'ghost' cannot resolve
    client = FakeChatClient(
        [
            _result("draft", thinking="r"),
            _result(_valid_json(suggested_handler="ghost")),
            _result(_valid_json(suggested_handler="ghost")),
            _result(_valid_json(suggested_handler="ghost")),
        ]
    )

    with pytest.raises(StructuredOutputError) as exc:
        await generate_judgment(client, _EVENT, "energy", retry_budget=3)
    assert "ghost" in str(exc.value)


async def test_schema_violation_recovers_within_budget() -> None:
    """An out-of-range confidence fails Pydantic validation, then recovers."""
    registry.register_handler("energy", "echo", _noop_handler)
    client = FakeChatClient(
        [
            _result("draft", thinking="r"),
            _result(_valid_json(confidence=1.7)),
            _result(_valid_json()),
        ]
    )

    out = await generate_judgment(client, _EVENT, "energy", retry_budget=3)
    assert out.attempts == 2


async def test_empty_affected_entities_is_rejected() -> None:
    registry.register_handler("energy", "echo", _noop_handler)
    bad = _valid_json(affected_entities=[])
    client = FakeChatClient(
        [_result("draft", thinking="r"), _result(bad), _result(bad), _result(bad)]
    )

    with pytest.raises(StructuredOutputError):
        await generate_judgment(client, _EVENT, "energy", retry_budget=3)


async def test_empty_primary_key_is_rejected() -> None:
    registry.register_handler("energy", "echo", _noop_handler)
    bad = _valid_json(affected_entities=[{"object_type": "Asset", "primary_key": "   "}])
    client = FakeChatClient(
        [_result("draft", thinking="r"), _result(bad), _result(bad), _result(bad)]
    )

    with pytest.raises(StructuredOutputError) as exc:
        await generate_judgment(client, _EVENT, "energy", retry_budget=3)
    assert "primary_key" in str(exc.value)


async def test_call1_thinks_and_call2_omits_think() -> None:
    """CHECKPOINT-0 contract: call 1 reasons, call 2 never pairs think with format."""
    registry.register_handler("energy", "echo", _noop_handler)
    client = FakeChatClient([_result("draft", thinking="r"), _result(_valid_json())])

    await generate_judgment(client, _EVENT, "energy")

    assert client.calls[0]["think"] is True
    assert client.calls[0]["has_format"] is False
    assert client.calls[1]["think"] is None
    assert client.calls[1]["has_format"] is True


async def test_retry_feeds_validator_error_back() -> None:
    """§6.4: the validator error is fed back into the next structuring call."""
    registry.register_handler("energy", "echo", _noop_handler)
    client = FakeChatClient(
        [_result("draft", thinking="r"), _result("bad json"), _result(_valid_json())]
    )

    await generate_judgment(client, _EVENT, "energy")

    retry_messages = client.calls[2]["messages"]
    joined = " ".join(m["content"] for m in retry_messages)
    assert "failed validation" in joined


async def test_suggested_handler_is_enum_constrained_to_registered_handlers() -> None:
    """The format schema constrains suggested_handler to the registry's handlers."""
    registry.register_handler("energy", "echo", _noop_handler)
    registry.register_handler("energy", "notify", _noop_handler)
    client = FakeChatClient([_result("draft", thinking="r"), _result(_valid_json())])

    await generate_judgment(client, _EVENT, "energy")

    schema = client.calls[1]["response_format"]
    assert schema["properties"]["suggested_handler"]["enum"] == ["echo", "notify"]


async def test_goal_threads_into_both_calls_system_messages() -> None:
    """A8: the Procedure.goal steers the system prompt of call 1 AND call 2."""
    registry.register_handler("energy", "echo", _noop_handler)
    goal = "Run the morning round; judge each reading against its threshold."
    client = FakeChatClient([_result("draft", thinking="r"), _result(_valid_json())])

    await generate_judgment(client, _EVENT, "energy", goal=goal)

    call1_system = client.calls[0]["messages"][0]
    call2_system = client.calls[1]["messages"][0]
    assert call1_system["role"] == "system" and goal in call1_system["content"]
    assert call2_system["role"] == "system" and goal in call2_system["content"]


async def test_no_goal_leaves_system_prompt_ungoverned() -> None:
    """A8: omitting goal keeps the reactive system prompt free of a goal directive."""
    registry.register_handler("energy", "echo", _noop_handler)
    client = FakeChatClient([_result("draft", thinking="r"), _result(_valid_json())])

    await generate_judgment(client, _EVENT, "energy")

    assert "PROCEDURE GOAL" not in client.calls[0]["messages"][0]["content"]


# --- PLAN-0060: the handler catalog threads into the reactive prompt behind a flag ---


async def test_handler_catalog_threads_into_both_calls_when_enabled() -> None:
    """AC-3: with include_handler_catalog=True the catalog rides in call 1 AND call 2's
    system message (via the build_structuring_messages composition)."""
    registry.register_handler(
        "energy", "restart", _noop_handler, description="Controlled restart of the asset."
    )
    registry.register_handler("energy", "echo", _noop_handler, description="Diagnostic no-op.")
    client = FakeChatClient([_result("draft", thinking="r"), _result(_valid_json())])

    await generate_judgment(client, _EVENT, "energy", include_handler_catalog=True)

    for call in (client.calls[0], client.calls[1]):
        system = call["messages"][0]
        assert system["role"] == "system"
        assert "AVAILABLE ACTIONS" in system["content"]
        assert "restart — Controlled restart of the asset." in system["content"]


async def test_handler_catalog_absent_by_default() -> None:
    """AC-4: the default path (flag off) never renders the catalog block."""
    registry.register_handler("energy", "echo", _noop_handler, description="Diagnostic no-op.")
    client = FakeChatClient([_result("draft", thinking="r"), _result(_valid_json())])

    await generate_judgment(client, _EVENT, "energy")

    assert "AVAILABLE ACTIONS" not in client.calls[0]["messages"][0]["content"]
    assert "AVAILABLE ACTIONS" not in client.calls[1]["messages"][0]["content"]


async def test_handler_catalog_leaves_enum_unchanged() -> None:
    """AC-5: enabling the catalog does NOT change the suggested_handler enum constraint."""
    registry.register_handler("energy", "restart", _noop_handler, description="Controlled restart.")
    registry.register_handler("energy", "echo", _noop_handler, description="Diagnostic no-op.")
    client = FakeChatClient([_result("draft", thinking="r"), _result(_valid_json())])

    await generate_judgment(client, _EVENT, "energy", include_handler_catalog=True)

    schema = client.calls[1]["response_format"]
    assert schema["properties"]["suggested_handler"]["enum"] == ["echo", "restart"]


async def test_handler_catalog_threads_on_skip_single_call() -> None:
    """AC-3: the PLAN-0020 `skip` single-call path also carries the catalog."""
    registry.register_handler("energy", "echo", _noop_handler, description="Diagnostic no-op.")
    client = FakeChatClient([_result(_valid_json())])  # only the lone structured call

    await generate_judgment(
        client, _EVENT, "energy", reasoning_mode="skip", include_handler_catalog=True
    )

    assert len(client.calls) == 1
    assert "AVAILABLE ACTIONS" in client.calls[0]["messages"][0]["content"]


async def test_judgment_round_trips() -> None:
    """§7.2: the judgment survives model_validate(model_dump())."""
    registry.register_handler("energy", "echo", _noop_handler)
    client = FakeChatClient([_result("draft", thinking="r"), _result(_valid_json())])

    out = await generate_judgment(client, _EVENT, "energy")
    assert LlmJudgment.model_validate(out.judgment.model_dump()) == out.judgment
