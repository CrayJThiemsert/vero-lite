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
from services.engine.action_verification import (
    augment_with_advisory_judge,
    verify_action_expression,
)
from services.engine.actions import AuditMetadata, EntityRef, ReasoningStep, RecommendedAction
from services.engine.economic_impact import build_economic_steps
from services.engine.entity_resolution import event_subject_ref, resolve_affected_entities
from services.engine.llm.client import OllamaClient, OllamaUnreachableError
from services.engine.llm.structured import ChatClient, JudgmentResult, generate_judgment
from services.engine.llm.trace import build_llm_audit_metadata, build_llm_reasoning_trace
from services.engine.registry import registry

logger = logging.getLogger(__name__)

OVERTEMP_THRESHOLD_CELSIUS = 90.0
"""Energy default for the escalation threshold — the value ``settings.oct_recommend_threshold``
defaults to. The runtime trigger reads the (per-vertical, env-driven) setting so a
second vertical can escalate at its own threshold (PLAN-0013 AC-template); this
constant is retained as the documented energy baseline."""

RULE_CONFIDENCE = 0.8
"""Fixed confidence for rule-based (fail-safe) recommendations — no model inference."""


def crosses_threshold(measured: float, threshold: float, direction: str) -> bool:
    """True when ``measured`` breaches ``threshold`` in the configured direction.

    ``direction='above'`` (default): ``measured >= threshold`` — the energy
    over-temperature semantics. ``direction='below'``: ``measured <= threshold``
    — e.g. an aquaculture dissolved-oxygen crash (PLAN-0016 Step 0). Normalized
    case/space-insensitively; anything other than ``'below'`` means ``'above'``,
    so an unset/garbled ``OCT_RECOMMEND_DIRECTION`` fails safe to the historical
    behavior. The single source of truth shared by the trigger
    (``_is_recommendation_trigger``), the fail-safe rule (``_rule_recommend``),
    and the demo-anchor breach selector (``demo_events._breach_event``).
    """
    if direction.strip().lower() == "below":
        return measured <= threshold
    return measured >= threshold


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
    # PLAN-0047 Step 1: server-resolved caller identity (the authn dependency) —
    # None when api_auth_enabled=false; projected to action_identity at persist.
    approved_by: str | None = None
    executed_by: str | None = None


def _is_recommendation_trigger(event: dict[str, Any]) -> bool:
    """Return True when an event warrants engaging the recommender.

    The deterministic detector — a reading whose ``measured_value`` is at
    or above the active vertical's ``settings.oct_recommend_threshold``
    (energy default 90 °C). Shares its intent with the retained rule body's
    guards (``_rule_recommend``).
    """
    if event.get("event_type") != "reading":
        return False
    measured = event.get("measured_value")
    return measured is not None and crosses_threshold(
        measured, settings.oct_recommend_threshold, settings.oct_recommend_direction
    )


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
    affected_entities: list[EntityRef],
    resolution_steps: list[ReasoningStep],
    verification_steps: list[ReasoningStep],
    economic_steps: list[ReasoningStep],
) -> ActionRecord:
    """Compose the ADR-007 D2 envelope from the LLM judgment (SC-1).

    The model owns the judgment fields; the harness owns ``id``,
    ``vertical``, ``created_at``, ``requires_approval`` (default True),
    ``audit_metadata`` and the reasoning trace. ``affected_entities`` are the
    **governed-resolved** entities (PLAN-0030 / ADR-0022 member (a)) -- each
    model-emitted ``primary_key`` resolved against the declared object universe
    (kept canonical) or replaced by the deterministic event subject anchor on a
    non-match -- NOT the model's verbatim list; ``resolution_steps`` records each
    outcome, appended to the hybrid trace. ``verification_steps`` records the
    ADR-0022 member (b) action verify+reshape outcome (PLAN-0035 Phase 1),
    likewise appended. ``economic_steps`` is the advisory, trace-carried Box-4
    economic-impact facet (ADR-0030 / PLAN-0071), appended LAST — it never
    changes the action. The ADR-007 D2 envelope class is unchanged.
    """
    judgment = result.judgment
    event_id = str(event.get("event_id", "unknown"))
    action = RecommendedAction(
        id=f"action-{event_id}",
        title=judgment.title,
        description=judgment.description,
        vertical=vertical,
        reasoning_trace=build_llm_reasoning_trace(event, vertical, result)
        + resolution_steps
        + verification_steps
        + economic_steps,
        confidence=judgment.confidence,
        affected_entities=affected_entities,
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
            client,
            event,
            vertical,
            retry_budget=settings.llm_retry_budget,
            include_handler_catalog=settings.handler_catalog_enabled,
        )
        # ADR-0022 member (a) / PLAN-0030: resolve the model-emitted entity refs
        # against the declared object universe before the governed record trusts
        # them. Any resolution error propagates to the fail-safe below (IN-4).
        affected_entities, resolution_steps = await resolve_affected_entities(
            event, vertical, result.judgment.affected_entities
        )
        # ADR-0022 member (b) / PLAN-0035 Phase 1: verify the proposal prose expresses
        # the action its structured handler names; reshape (authoritatively surface it)
        # on a mismatch + trace. The deterministic floor (the (a) mechanism of SD-1=(c));
        # any error here propagates to the fail-safe below (ADR-010 IN-4) — AC-7.
        verification_steps = verify_action_expression(result.judgment, vertical)
        # PLAN-0035 Phase 2: layer the ADVISORY local-LLM-judge onto the floor — a
        # confidence + agreement signal that NEVER overrides the surfaced action
        # (constraint ②) and degrades to "(a)-only" disclosed when MS-S1 is unreachable
        # (constraint ④). Gated behind verification_judge_enabled (default off — a live
        # judge is host-state, CLAUDE.md §8); this call never raises (advisory must not
        # harm the load-bearing floor result), so it stays out of the IN-4 contract.
        judge_client = client if settings.verification_judge_enabled else None
        verification_steps = await augment_with_advisory_judge(
            verification_steps, result.judgment, judge_client=judge_client
        )
        # ADR-0030 / PLAN-0071: the advisory, trace-carried Box-4 economic-impact facet.
        # build_economic_steps NEVER raises (ADR-0030 D5) — like the advisory judge above it
        # stays OUT of the IN-4 contract: a raising producer must not demote this good LLM
        # judgment to the _rule_recommend fail-safe. Absent producer / ungroundable ฿ -> [].
        economic_steps = await build_economic_steps(event, vertical)
        return _compose_llm_record(
            event,
            vertical,
            result,
            affected_entities,
            resolution_steps,
            verification_steps,
            economic_steps,
        )
    except Exception as exc:  # fail-safe must catch everything — §6.6 / ADR-010 IN-4
        if isinstance(exc, OllamaUnreachableError):
            # PLAN-0014: MS-S1 is unreachable — best-effort ping (never raises),
            # then continue to the deterministic fail-safe below, unchanged.
            from services.notify.telegram import notify_llm_unreachable

            await notify_llm_unreachable()
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
    measured_value is at or above ``settings.oct_recommend_threshold``,
    else None. The affected-entity object_type, its event key, and the
    anomaly label are read from the active vertical's
    ``settings.oct_recommend_*`` policy (energy defaults reproduce the
    original over-temperature wording), so the offline fail-safe stays
    coherent across verticals (PLAN-0013 AC-template). The record carries
    ``actor_kind="engine"`` and a rule_check-only trace, so the audit
    record shows the path actually taken.
    """
    if event.get("event_type") != "reading":
        return None
    measured = event.get("measured_value")
    threshold = settings.oct_recommend_threshold
    if measured is None or not crosses_threshold(
        measured, threshold, settings.oct_recommend_direction
    ):
        return None

    # SD-2 (Cray-approved): the LLM-path resolution fall-back and this deterministic
    # fail-safe converge on ONE subject-anchor source via event_subject_ref so they
    # cannot drift. Behavior-identical to the prior inline EntityRef construction.
    subject_ref = event_subject_ref(event)
    entity_type = subject_ref.object_type
    label = settings.oct_recommend_label
    subject_id = subject_ref.primary_key
    event_id = str(event.get("event_id", "unknown"))
    unit = str(event.get("unit", ""))
    below = settings.oct_recommend_direction.strip().lower() == "below"
    op = "<=" if below else ">="
    verb = "fell below" if below else "rose above"
    trace = [
        ReasoningStep(
            step_id="threshold-check",
            kind="rule_check",
            summary=f"measured_value {measured} {unit} {op} threshold {threshold}",
            detail={
                "measured_value": measured,
                "threshold": threshold,
                "unit": unit,
                "direction": "below" if below else "above",
                "crossed": True,
            },
        ),
        ReasoningStep(
            step_id="alert-derivation",
            kind="rule_check",
            summary=f"Derived {label} alert for {entity_type.lower()} {subject_id}",
            detail={"event_id": event_id, "entity_type": entity_type, "entity_id": subject_id},
        ),
    ]
    action = RecommendedAction(
        id=f"action-{event_id}",
        title=f"Investigate {label} on {subject_id}",
        description=(
            f"Reading {measured} {unit} on {entity_type} {subject_id} {verb} the "
            f"{threshold} {unit} threshold."
        ),
        vertical=vertical,
        reasoning_trace=trace,
        confidence=RULE_CONFIDENCE,
        affected_entities=[subject_ref],
        suggested_handler="echo",
        handler_payload={"event_id": event_id, "entity_id": subject_id, "measured_value": measured},
        audit_metadata=AuditMetadata(actor="engine", actor_kind="engine"),
        created_at=datetime.now(UTC),
    )
    return ActionRecord(action=action)


def approve(record: ActionRecord) -> ActionRecord:
    """Transition a proposed action to approved."""
    if record.status is not ActionStatus.PROPOSED:
        raise ApprovalError(f"cannot approve an action in status '{record.status.value}'")
    record.status = ActionStatus.APPROVED
    record.action.approved_at = datetime.now(UTC)  # PLAN-0015 D3
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
    action.executed_at = datetime.now(UTC)  # PLAN-0015 D3
    return receipt
