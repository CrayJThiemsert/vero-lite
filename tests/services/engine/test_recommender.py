"""Tests for the LLM-backed recommender + approval gate (PLAN-0006 Step 5).

The LLM path is exercised with a fake chat client injected by
monkeypatching ``_build_chat_client`` — no live LLM, deterministic,
offline (Lesson #7 §3). The load-bearing checks are §7.4: a forced
client error falls back to a valid rule-path record and no exception
escapes. The approval-gate tests are unchanged Phase-2 behaviour.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from services.api.config import settings
from services.engine.llm.client import ChatResult, OllamaError
from services.engine.recommender import (
    RULE_CONFIDENCE,
    ActionRecord,
    ActionStatus,
    ApprovalError,
    _rule_recommend,
    approve,
    execute,
    recommend,
    reject,
)
from services.engine.registry import registry

_BUILD_CLIENT = "services.engine.recommender._build_chat_client"


def _crossing_event() -> dict[str, Any]:
    """A reading event whose measured_value crosses the threshold."""
    return {
        "event_id": "event-reading-03",
        "event_type": "reading",
        "measured_value": 96.5,
        "unit": "celsius",
        "asset_id": "asset-battery-01",
        "site_id": "site-substation-01",
    }


def _normal_event() -> dict[str, Any]:
    """A reading event safely below the threshold."""
    return {
        "event_id": "event-reading-01",
        "event_type": "reading",
        "measured_value": 32.4,
        "unit": "celsius",
        "asset_id": "asset-battery-01",
    }


class _FakeChatClient:
    """A ChatClient stand-in: replays canned ChatResults, or always raises."""

    def __init__(
        self,
        *,
        results: list[ChatResult] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._results = list(results or [])
        self._error = error

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        if self._error is not None:
            raise self._error
        return self._results.pop(0)


def _chat(content: str, *, thinking: str | None = None) -> ChatResult:
    return ChatResult(content=content, thinking=thinking, model="gpt-oss:20b", raw={})


def _judgment_json(*, handler: str = "echo", confidence: float = 0.9) -> str:
    return json.dumps(
        {
            "title": "Investigate over-temperature on asset-battery-01",
            "description": "Reading 96.5 celsius crossed the 90.0 celsius threshold.",
            "rationale": "Temperature is above the safe threshold; escalate for review.",
            "confidence": confidence,
            "affected_entities": [{"object_type": "Asset", "primary_key": "asset-battery-01"}],
            "suggested_handler": handler,
            "handler_payload": {"event_id": "event-reading-03"},
        }
    )


async def _echo_handler(_action: Any) -> dict[str, Any]:
    return {"executed": True}


def _proposed_record() -> ActionRecord:
    """A proposed record via the deterministic rule path — for gate tests."""
    record = _rule_recommend(_crossing_event(), "energy")
    assert record is not None
    return record


# --- LLM path -------------------------------------------------------------


async def test_recommend_llm_path_returns_proposed_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """§7.2/§7.4: a crossing event on the LLM path yields a proposed action."""
    registry.register_handler("energy", "echo", _echo_handler)
    fake = _FakeChatClient(results=[_chat("draft", thinking="reasoned"), _chat(_judgment_json())])
    monkeypatch.setattr(_BUILD_CLIENT, lambda: fake)

    record = await recommend(_crossing_event(), "energy")

    assert record is not None
    assert record.status is ActionStatus.PROPOSED
    assert record.action.requires_approval is True
    assert record.action.vertical == "energy"
    assert record.action.audit_metadata.actor_kind == "llm"
    assert "asset-battery-01" in record.action.title


async def test_recommend_llm_trace_has_llm_inference_step(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """§7.3: the LLM path produces a hybrid trace with an llm_inference step."""
    registry.register_handler("energy", "echo", _echo_handler)
    fake = _FakeChatClient(results=[_chat("draft", thinking="reasoned"), _chat(_judgment_json())])
    monkeypatch.setattr(_BUILD_CLIENT, lambda: fake)

    record = await recommend(_crossing_event(), "energy")

    assert record is not None
    kinds = [step.kind for step in record.action.reasoning_trace]
    assert "llm_inference" in kinds
    assert any(k in {"ontology_query", "rule_check"} for k in kinds)


async def test_recommend_returns_none_for_normal_reading() -> None:
    """A sub-threshold reading never engages the LLM — returns None."""
    assert await recommend(_normal_event(), "energy") is None


async def test_recommend_returns_none_for_non_reading_event() -> None:
    alarm = {"event_id": "event-alarm-01", "event_type": "alarm", "asset_id": "asset-inverter-01"}
    assert await recommend(alarm, "energy") is None


# --- Fail-safe (§7.4 — the load-bearing safety criterion) -----------------


async def test_recommend_failsafe_on_client_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """§7.4: a forced client error falls back to a valid rule-path record."""
    fake = _FakeChatClient(error=OllamaError("connection refused"))
    monkeypatch.setattr(_BUILD_CLIENT, lambda: fake)

    record = await recommend(_crossing_event(), "energy")

    assert record is not None
    assert record.status is ActionStatus.PROPOSED


async def test_recommend_failsafe_record_is_the_rule_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """§7.4: the fail-safe record carries actor_kind=engine + rule_check-only trace."""
    fake = _FakeChatClient(error=OllamaError("timeout"))
    monkeypatch.setattr(_BUILD_CLIENT, lambda: fake)

    record = await recommend(_crossing_event(), "energy")

    assert record is not None
    assert record.action.audit_metadata.actor_kind == "engine"
    assert {step.kind for step in record.action.reasoning_trace} == {"rule_check"}
    assert record.action.confidence == RULE_CONFIDENCE


async def test_recommend_failsafe_on_exhausted_retry_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A structuring failure that exhausts the retry budget falls back, no raise."""
    fake = _FakeChatClient(
        results=[_chat("draft", thinking="r"), _chat("garbage"), _chat("garbage"), _chat("garbage")]
    )
    monkeypatch.setattr(_BUILD_CLIENT, lambda: fake)

    record = await recommend(_crossing_event(), "energy")

    assert record is not None
    assert record.action.audit_metadata.actor_kind == "engine"


async def test_recommend_hosted_backend_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    """SD-5: the seam-only hosted backend stub falls back to the rule path."""
    monkeypatch.setattr(settings, "llm_backend", "hosted")

    record = await recommend(_crossing_event(), "energy")

    assert record is not None
    assert record.action.audit_metadata.actor_kind == "engine"


# --- confidence is advisory only (§7.3 / ADR-010 IN-3) --------------------


@pytest.mark.parametrize("confidence", [0.03, 0.5, 0.99])
async def test_confidence_does_not_gate_approve_or_execute(
    monkeypatch: pytest.MonkeyPatch, confidence: float
) -> None:
    """§7.3: an action approves + executes regardless of the confidence value."""
    registry.register_handler("energy", "echo", _echo_handler)
    fake = _FakeChatClient(
        results=[
            _chat("draft", thinking="r"),
            _chat(_judgment_json(confidence=confidence)),
        ]
    )
    monkeypatch.setattr(_BUILD_CLIENT, lambda: fake)

    record = await recommend(_crossing_event(), "energy")
    assert record is not None
    assert record.action.confidence == confidence

    approve(record)
    receipt = await execute(record)
    assert record.status is ActionStatus.EXECUTED
    assert receipt["executed"] is True


# --- approval gate (unchanged Phase-2 behaviour) --------------------------


def test_approve_transitions_proposed_to_approved() -> None:
    record = _proposed_record()
    approve(record)
    assert record.status is ActionStatus.APPROVED


def test_approve_on_non_proposed_raises() -> None:
    record = _proposed_record()
    approve(record)
    with pytest.raises(ApprovalError):
        approve(record)


def test_reject_transitions_proposed_to_rejected() -> None:
    record = _proposed_record()
    reject(record)
    assert record.status is ActionStatus.REJECTED


def test_reject_on_rejected_raises() -> None:
    record = _proposed_record()
    reject(record)
    with pytest.raises(ApprovalError):
        reject(record)


async def test_execute_requires_approval() -> None:
    """Executing a proposed (un-approved) action raises a documented error."""
    record = _proposed_record()
    with pytest.raises(ApprovalError):
        await execute(record)


async def test_execute_invokes_registered_handler() -> None:
    """An approved action invokes the registered handler."""
    calls: list[Any] = []

    async def _handler(action: Any) -> dict[str, Any]:
        calls.append(action)
        return {"executed": True, "action_id": action.id}

    registry.register_handler("energy", "echo", _handler)
    record = _proposed_record()
    approve(record)
    receipt = await execute(record)

    assert record.status is ActionStatus.EXECUTED
    assert calls == [record.action]
    assert receipt["executed"] is True


async def test_execute_on_executed_raises() -> None:
    """A second execute fails — the record is no longer approved."""
    registry.register_handler("energy", "echo", _echo_handler)
    record = _proposed_record()
    approve(record)
    await execute(record)
    with pytest.raises(ApprovalError):
        await execute(record)
