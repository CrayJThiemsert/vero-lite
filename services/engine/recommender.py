"""Rule-based recommender + minimal approval gate (PLAN-0005 §6.5).

OQ-3: the recommender is a deterministic threshold rule — no LLM. It
turns a threshold-crossing OperationalEvent into a RecommendedAction
envelope (ADR-007 D2) wrapped in an ActionRecord at status 'proposed'.

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

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from services.engine.actions import AuditMetadata, EntityRef, ReasoningStep, RecommendedAction
from services.engine.registry import registry

OVERTEMP_THRESHOLD_CELSIUS = 90.0
"""Reading value at or above which the rule escalates to a RecommendedAction."""

RULE_CONFIDENCE = 0.8
"""Fixed confidence for rule-based recommendations (OQ-3: no model inference)."""


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


def recommend(event: dict[str, Any], vertical: str) -> ActionRecord | None:
    """Apply the threshold rule to an OperationalEvent.

    Returns a proposed ActionRecord when the event is a reading whose
    measured_value is at or above OVERTEMP_THRESHOLD_CELSIUS, else None.
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
