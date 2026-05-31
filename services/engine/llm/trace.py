"""Hybrid reasoning-trace assembly for the LLM reasoning hook (PLAN-0006 Step 4).

ADR-010 D3: the LLM path's ``reasoning_trace`` is **hybrid** —

- one ``ReasoningStep(kind="llm_inference")`` carrying the model-asserted
  rationale, explicitly labelled as model-asserted: it is the model's own
  account of its reasoning, **not** a verified explanation of its
  computation (research brief #3 §4.2 — "chain-of-thought is not
  explainability"); plus
- **harness-emitted** ``ReasoningStep(kind="ontology_query")`` and
  ``ReasoningStep(kind="rule_check")`` steps recording what the engine
  ACTUALLY did — the event it ingested and the deterministic semantic
  checks it ran on the model output.

``audit_metadata.actor_kind`` is ``"llm"`` on this path. ``confidence``
is **advisory only** (ADR-010 IN-3): surfaced in the trace and the
envelope, never used to gate automation.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from services.engine.actions import AuditMetadata, ReasoningStep
from services.engine.llm.structured import JudgmentResult, LlmJudgment

MODEL_ASSERTED_NOTE = (
    "MODEL-ASSERTED — this narrative is the model's own account of its "
    "reasoning, not a verified explanation of its computation (ADR-010 D3 / "
    "research brief #3 §4.2). Treat it as a review aid, not as ground truth."
)

CONFIDENCE_ADVISORY_NOTE = (
    "advisory only — surfaced for the human reviewer, never used to gate "
    "approval or execution (ADR-010 IN-3)"
)


def build_llm_reasoning_trace(
    event: Mapping[str, Any],
    vertical: str,
    result: JudgmentResult,
) -> list[ReasoningStep]:
    """Assemble the hybrid trace for a successful LLM-path recommendation.

    Order narrates the engine's actual flow: evidence ingested
    (``ontology_query``) -> model reasoning (``llm_inference``) ->
    deterministic verification (``rule_check``).
    """
    return [
        _ontology_query_step(event, vertical),
        _llm_inference_step(result),
        _rule_check_step(result.judgment, vertical),
    ]


def build_llm_audit_metadata(model: str) -> AuditMetadata:
    """Audit metadata for the LLM path — ``actor_kind="llm"`` (ADR-010 D3)."""
    return AuditMetadata(
        actor=model,
        actor_kind="llm",
        notes=(
            "LLM reasoning path (PLAN-0006 / ADR-010 D3). The reasoning trace "
            "is a human-review artifact; confidence is advisory only (IN-3)."
        ),
    )


def _ontology_query_step(event: Mapping[str, Any], vertical: str) -> ReasoningStep:
    """Harness-emitted: the evidence the engine actually ingested.

    Vertical-agnostic: the summary names only the event id (the full event
    dict — whatever entity refs it carries — is preserved in ``detail``),
    so the step reads correctly for any ontology, not just energy's
    ``asset_id`` shape (PLAN-0013 AC-template).
    """
    event_id = str(event.get("event_id", "unknown"))
    return ReasoningStep(
        step_id="ontology-query",
        kind="ontology_query",
        summary=f"Ingested operational event '{event_id}' from the {vertical} data adapter",
        detail={"vertical": vertical, "event": dict(event)},
    )


def _llm_inference_step(result: JudgmentResult) -> ReasoningStep:
    """Model-asserted: the model's rationale + raw thinking narrative."""
    return ReasoningStep(
        step_id="llm-inference",
        kind="llm_inference",
        summary=result.judgment.rationale,
        detail={
            "label": MODEL_ASSERTED_NOTE,
            "model": result.model,
            "thinking": result.thinking,
            "draft": result.draft,
            "structuring_attempts": result.attempts,
            "confidence": result.judgment.confidence,
            "confidence_note": CONFIDENCE_ADVISORY_NOTE,
        },
    )


def _rule_check_step(judgment: LlmJudgment, vertical: str) -> ReasoningStep:
    """Harness-emitted: the deterministic semantic checks the engine ran.

    By the time the trace is built the judgment has already passed these
    checks in ``structured.generate_judgment`` — this step records what was
    verified, faithfully.
    """
    entity_count = len(judgment.affected_entities)
    return ReasoningStep(
        step_id="semantic-checks",
        kind="rule_check",
        summary=(
            f"Verified suggested_handler '{judgment.suggested_handler}' resolves "
            f"in the registry for vertical '{vertical}'; {entity_count} "
            f"affected-entity primary key(s) non-empty"
        ),
        detail={
            "vertical": vertical,
            "suggested_handler": judgment.suggested_handler,
            "handler_registered": True,
            "affected_entity_count": entity_count,
        },
    )
