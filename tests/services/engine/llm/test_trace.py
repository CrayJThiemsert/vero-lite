"""Tests for hybrid reasoning-trace assembly (PLAN-0006 Step 4 / §7.3).

Lesson #7 §3: in-process assertions on the assembled ReasoningStep list
and AuditMetadata — the load-bearing checks are that the trace pairs a
model-asserted ``llm_inference`` step with harness-emitted steps and that
``actor_kind`` is ``"llm"``.
"""

from __future__ import annotations

from typing import Any

from services.engine.actions import EntityRef, ReasoningStep
from services.engine.llm.structured import JudgmentResult, LlmJudgment
from services.engine.llm.trace import build_llm_audit_metadata, build_llm_reasoning_trace

_EVENT: dict[str, Any] = {
    "event_id": "event-reading-07",
    "event_type": "reading",
    "measured_value": 96.5,
    "asset_id": "asset-battery-07",
}


def _judgment() -> LlmJudgment:
    return LlmJudgment(
        title="Investigate over-temperature on asset-battery-07",
        description="Reading 96.5 celsius crossed the 90.0 celsius threshold.",
        rationale="Temperature exceeds the safe threshold; escalate for human review.",
        confidence=0.87,
        affected_entities=[EntityRef(object_type="Asset", primary_key="asset-battery-07")],
        suggested_handler="echo",
        handler_payload={},
    )


def _result(
    *, thinking: str | None = "step-by-step narrative", attempts: int = 1
) -> JudgmentResult:
    return JudgmentResult(
        judgment=_judgment(),
        thinking=thinking,
        draft="draft text",
        model="gpt-oss:20b",
        attempts=attempts,
    )


def _steps_by_kind(trace: list[ReasoningStep]) -> dict[str, ReasoningStep]:
    return {step.kind: step for step in trace}


def test_trace_has_llm_inference_and_harness_steps() -> None:
    """§7.3: >=1 llm_inference step AND >=1 harness-emitted step."""
    trace = build_llm_reasoning_trace(_EVENT, "energy", _result())
    kinds = [step.kind for step in trace]

    assert kinds.count("llm_inference") >= 1
    harness = [k for k in kinds if k in {"ontology_query", "rule_check"}]
    assert len(harness) >= 1
    assert all(isinstance(step, ReasoningStep) for step in trace)


def test_trace_step_order_narrates_engine_flow() -> None:
    trace = build_llm_reasoning_trace(_EVENT, "energy", _result())
    assert [step.kind for step in trace] == ["ontology_query", "llm_inference", "rule_check"]


def test_llm_inference_step_is_labelled_model_asserted() -> None:
    """ADR-010 D3: the llm_inference narrative is labelled, not ground truth."""
    step = _steps_by_kind(build_llm_reasoning_trace(_EVENT, "energy", _result()))["llm_inference"]
    assert step.detail is not None
    assert "MODEL-ASSERTED" in step.detail["label"]


def test_llm_inference_summary_is_the_model_rationale() -> None:
    result = _result()
    step = _steps_by_kind(build_llm_reasoning_trace(_EVENT, "energy", result))["llm_inference"]
    assert step.summary == result.judgment.rationale


def test_llm_inference_carries_thinking_and_advisory_confidence() -> None:
    step = _steps_by_kind(build_llm_reasoning_trace(_EVENT, "energy", _result()))["llm_inference"]
    assert step.detail is not None
    assert step.detail["thinking"] == "step-by-step narrative"
    assert step.detail["confidence"] == 0.87
    assert "advisory" in step.detail["confidence_note"].lower()
    assert step.detail["model"] == "gpt-oss:20b"


def test_llm_inference_handles_absent_thinking() -> None:
    step = _steps_by_kind(build_llm_reasoning_trace(_EVENT, "energy", _result(thinking=None)))[
        "llm_inference"
    ]
    assert step.detail is not None
    assert step.detail["thinking"] is None


def test_ontology_query_step_records_ingested_event() -> None:
    step = _steps_by_kind(build_llm_reasoning_trace(_EVENT, "energy", _result()))["ontology_query"]
    assert step.detail is not None
    assert step.detail["event"] == _EVENT
    assert "event-reading-07" in step.summary


def test_rule_check_step_records_the_verified_handler() -> None:
    step = _steps_by_kind(build_llm_reasoning_trace(_EVENT, "energy", _result()))["rule_check"]
    assert "echo" in step.summary
    assert step.detail is not None
    assert step.detail["handler_registered"] is True
    assert step.detail["affected_entity_count"] == 1


def test_audit_metadata_actor_kind_is_llm() -> None:
    """§7.3: actor_kind == 'llm' on the LLM path."""
    metadata = build_llm_audit_metadata("gpt-oss:20b")
    assert metadata.actor_kind == "llm"
    assert metadata.actor == "gpt-oss:20b"
