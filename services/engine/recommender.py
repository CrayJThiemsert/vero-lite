"""LLM-backed recommender + minimal approval gate.

PLAN-0006 (the "brain swap", ADR-010 D5): ``recommend()`` is LLM-backed.
It runs the two-call Pattern B exchange (``services/engine/llm/``) to
produce a RecommendedAction envelope (ADR-007 D2) wrapped in an
ActionRecord at status 'proposed'. The deterministic threshold rule is
**retained** as the fail-safe (``_rule_recommend``): on any LLM-path
failure ``recommend()`` falls back to it (or ``None``) and never raises
into the runtime loop (ADR-010 IN-4 / PLAN-0006 §6.6) — which keeps the
swap fully reversible.

The reduced "LLM-judgment" sub-schema (SC-1, see ``llm/structured.py``)
cannot express "no action", so ``recommend()`` engages the LLM only for
events the deterministic trigger flags — a reading at or above
``OVERTEMP_THRESHOLD_CELSIUS`` — and returns ``None`` for the rest
without an LLM call. This keeps the trigger/detector deterministic, lets
the LLM own the *reasoning* (the actual "brain"), and bounds token cost
(research R6).

OQ-2: the approval gate is minimal — it enforces the
proposed -> approved -> executed / rejected lifecycle. It is NOT the
full audit framework (ADR-011+): no correlation-id propagation, no
approval-chain enforcement, no immutable audit log.

OQ-1: ActionRecord.status is the in-memory form of the ontology
RecommendedAction entity's status; ActionRecord.action stays the
ADR-007 D2 runtime envelope. The two are projected, not unified, at the
persistence boundary (services/db/).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from services.api.config import settings
from services.engine.actions import AuditMetadata, EntityRef, ReasoningStep, RecommendedAction
from services.engine.llm.client import OllamaClient
from services.engine.llm.structured import ChatClient, JudgmentResult, generate_judgment
from services.engine.llm.trace import build_llm_audit_metadata, build_llm_reasoning_trace
from services.engine.registry import registry

logger = logging.getLogger(__name__)

OVERTEMP_THRESHOLD_CELSIUS = 90.0
"""Reading value at or above which the engine escalates to a RecommendedAction."""

RULE_CONFIDENCE = 0.8
"""Fixed confidence for rule-based (fail-safe) recommendations — no model inference."""


class ActionStatus(StrEnum):
    """Lifecycle status — mirrors the ontology RecommendedAction.status enum."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"


class ApprovalError(Exception):
    """Raised on an illegal approval-gate transition."""


@dataclass
class ActionRecord:
    """A RecommendedAction envelope plus its mutable lifecycle status.

    The in-memory form of the ontology RecommendedAction projection
    (OQ-1); persisted by services/db/ in commit 6.
    """

    action: RecommendedAction
    status: ActionStatus = ActionStatus.PROPOSED


def _is_recommendation_trigger(event: dict[str, Any]) -> bool:
    """Return True when an event warrants engaging the recommender.

    The deterministic detector — a reading whose ``measured_value`` is at
    or above ``OVERTEMP_THRESHOLD_CELSIUS``. Shares its intent with the
    retained rule body's guards (``_rule_recommend``).
    """
    if event.get("event_type") != "reading":
        return False
    measured = event.get("measured_value")
    return measured is not None and measured >= OVERTEMP_THRESHOLD_CELSIUS


def _build_chat_client() -> ChatClient:
    """Select and build the reasoning-hook chat backend (PLAN-0006 SD-5).

    ``llm_backend="local"`` -> the Ollama client on MS-S1 MAX (ADR-010 D1
    default). ``llm_backend="hosted"`` is a seam-only stub (SD-5): it
    raises ``NotImplementedError`` until local quality is shown
    insufficient on real data — ``recommend()`` catches that and falls
    back to the rule path. Tests monkeypatch this factory.
    """
    if settings.llm_backend == "local":
        return OllamaClient(
            base_url=settings.ollama_host,
            model=settings.recommender_model,
            timeout=settings.llm_request_timeout_s,
        )
    if settings.llm_backend == "hosted":
        raise NotImplementedError(
            "the hosted Claude backend is a seam-only stub (PLAN-0006 SD-5) — "
            "set llm_backend='local'"
        )
    raise ValueError(f"unknown llm_backend '{settings.llm_backend}'")


def _compose_llm_record(
    event: dict[str, Any],
    vertical: str,
    result: JudgmentResult,
) -> ActionRecord:
    """Compose the ADR-007 D2 envelope from the LLM judgment (SC-1).

    The model owns the judgment fields; the harness owns ``id``,
    ``vertical``, ``created_at``, ``requires_approval`` (default True),
    ``audit_metadata`` and the reasoning trace. The ADR-007 D2 envelope
    class is unchanged.
    """
    judgment = result.judgment
    event_id = str(event.get("event_id", "unknown"))
    action = RecommendedAction(
        id=f"action-{event_id}",
        title=judgment.title,
        description=judgment.description,
        vertical=vertical,
        reasoning_trace=build_llm_reasoning_trace(event, vertical, result),
        confidence=judgment.confidence,
        affected_entities=judgment.affected_entities,
        suggested_handler=judgment.suggested_handler,
        handler_payload=judgment.handler_payload,
        audit_metadata=build_llm_audit_metadata(result.model),
        created_at=datetime.now(UTC),
    )
    return ActionRecord(action=action)


async def recommend(event: dict[str, Any], vertical: str) -> ActionRecord | None:
    """Recommend an action for an OperationalEvent — LLM-backed (ADR-010 D5).

    Returns a proposed ActionRecord for a triggering event, or ``None``
    when the event does not trip the deterministic detector.

    On any LLM-path failure — connection error, timeout, unparseable
    output, exhausted retry budget, failed semantic checks, or the
    seam-only hosted backend — it falls back to the deterministic rule
    path (``_rule_recommend``) and **never raises into the runtime loop**
    (ADR-010 IN-4 / PLAN-0006 §6.6).
    """
    if not _is_recommendation_trigger(event):
        return None
    try:
        client = _build_chat_client()
        result = await generate_judgment(
            client, event, vertical, retry_budget=settings.llm_retry_budget
        )
        return _compose_llm_record(event, vertical, result)
    except Exception as exc:  # fail-safe must catch everything — §6.6 / ADR-010 IN-4
        logger.warning(
            "LLM recommend() path failed for vertical '%s'; falling back to the "
            "deterministic rule path: %s",
            vertical,
            exc,
        )
        return _rule_recommend(event, vertical)


def _rule_recommend(event: dict[str, Any], vertical: str) -> ActionRecord | None:
    """Deterministic threshold rule — the retained fail-safe (ADR-010 IN-4).

    Returns a proposed ActionRecord when the event is a reading whose
    measured_value is at or above OVERTEMP_THRESHOLD_CELSIUS, else None.
    The record carries ``actor_kind="engine"`` and a rule_check-only
    trace, so the audit record shows the path actually taken.
    """
    if event.get("event_type") != "reading":
        return None
    measured = event.get("measured_value")
    if measured is None or measured < OVERTEMP_THRESHOLD_CELSIUS:
        return None

    asset_id = str(event.get("asset_id", "unknown"))
    event_id = str(event.get("event_id", "unknown"))
    unit = str(event.get("unit", ""))
    trace = [
        ReasoningStep(
            step_id="threshold-check",
            kind="rule_check",
            summary=f"measured_value {measured} {unit} >= threshold {OVERTEMP_THRESHOLD_CELSIUS}",
            detail={
                "measured_value": measured,
                "threshold": OVERTEMP_THRESHOLD_CELSIUS,
                "unit": unit,
                "crossed": True,
            },
        ),
        ReasoningStep(
            step_id="alert-derivation",
            kind="rule_check",
            summary=f"Derived over-temperature alert for asset {asset_id}",
            detail={"event_id": event_id, "asset_id": asset_id},
        ),
    ]
    action = RecommendedAction(
        id=f"action-{event_id}",
        title=f"Investigate over-temperature on {asset_id}",
        description=(
            f"Reading {measured} {unit} on asset {asset_id} crossed the "
            f"{OVERTEMP_THRESHOLD_CELSIUS} {unit} threshold."
        ),
        vertical=vertical,
        reasoning_trace=trace,
        confidence=RULE_CONFIDENCE,
        affected_entities=[EntityRef(object_type="Asset", primary_key=asset_id)],
        suggested_handler="echo",
        handler_payload={"event_id": event_id, "asset_id": asset_id, "measured_value": measured},
        audit_metadata=AuditMetadata(actor="engine", actor_kind="engine"),
        created_at=datetime.now(UTC),
    )
    return ActionRecord(action=action)


def approve(record: ActionRecord) -> ActionRecord:
    """Transition a proposed action to approved."""
    if record.status is not ActionStatus.PROPOSED:
        raise ApprovalError(f"cannot approve an action in status '{record.status.value}'")
    record.status = ActionStatus.APPROVED
    return record


def reject(record: ActionRecord) -> ActionRecord:
    """Transition a proposed action to rejected."""
    if record.status is not ActionStatus.PROPOSED:
        raise ApprovalError(f"cannot reject an action in status '{record.status.value}'")
    record.status = ActionStatus.REJECTED
    return record


async def execute(record: ActionRecord) -> dict[str, Any]:
    """Execute an approved action via its registered handler.

    The minimal gate requires the approved state — every Phase 2
    recommendation carries requires_approval=True, so approve() must run
    first. Invokes the handler registered for (vertical, suggested_handler),
    transitions the record to executed, and returns the handler receipt.
    """
    if record.status is not ActionStatus.APPROVED:
        raise ApprovalError(
            f"cannot execute an action in status '{record.status.value}'; it must be approved first"
        )
    action = record.action
    handler = registry.get_handler(action.vertical, action.suggested_handler)
    receipt = await handler(action)
    record.status = ActionStatus.EXECUTED
    return receipt
