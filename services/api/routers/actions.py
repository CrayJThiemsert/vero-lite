"""Action-loop API router — three-layer wiring (ADR-007 D3/D4, PLAN-0005 §6.7).

Exposes the read -> recommend -> approve -> execute loop over the energy
vertical: object listing (ingress), recommendation listing, and the
approve / execute gate endpoints. Recommendations are held in a
process-local store keyed by action_id; executing an action also
persists it (the OQ-1 projection) via services/db/persistence.py.
"""

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.auth import AuthContext, get_current_principal
from services.api.config import settings
from services.api.models.actions import (
    ExecuteResponse,
    ObjectListResponse,
    RecommendationListResponse,
    RecommendationResponse,
)
from services.db.audit_log import append_audit
from services.db.persistence import persist_executed_action
from services.db.session import async_session, get_session
from services.engine import demo_events
from services.engine.ontology_meta import OntologyMeta, load_ontology_meta
from services.engine.procedures.event_bridge import (
    EventBridgeError,
    EventFireOutcome,
    EventRunRequest,
    build_event_resolver,
    fire_event,
)
from services.engine.procedures.spec import load_procedures
from services.engine.recommender import ActionRecord, ApprovalError, approve, execute, recommend
from services.engine.registry import RegistryError, registry
from services.notify.telegram import notify_event_fire_failed

logger = logging.getLogger(__name__)

router = APIRouter(tags=["action-loop"])

_action_store: dict[str, ActionRecord] = {}


def reset_action_store() -> None:
    """Clear the process-local recommendation store (used by tests)."""
    _action_store.clear()


def _to_response(record: ActionRecord) -> RecommendationResponse:
    action = record.action
    return RecommendationResponse(
        action_id=action.id,
        title=action.title,
        description=action.description,
        vertical=action.vertical,
        status=record.status.value,
        confidence=action.confidence,
        requires_approval=action.requires_approval,
        suggested_handler=action.suggested_handler,
        reasoning_trace=action.reasoning_trace,
        affected_entities=action.affected_entities,
        approved_at=action.approved_at,
        executed_at=action.executed_at,
    )


async def _load_event_bridge(vertical: str) -> Callable[..., EventRunRequest] | None:
    """Build the event resolver for ``vertical`` once per populate, or ``None`` when the vertical
    is not wired for the bridge (PLAN-0056 Step 6, SD-P3).

    ``None`` (a clean no-op, not a failure) when the vertical declares **no** ``event``-trigger
    procedure — e.g. energy, the default demo vertical — or has no registered procedure-executor
    factory (OQ-6: ``discover_and_register`` registers adapters + handlers only). Called only under
    the ship-dark flag, so a vertical without the bridge pays nothing when the flag is off.
    """
    try:
        spec = load_procedures(vertical)
    except FileNotFoundError:
        return None  # the vertical ships no procedures.yaml — nothing to bridge
    if not any(p.event_trigger is not None for p in spec.procedures):
        return None  # not an event-bridge vertical — no fire, no alert
    try:
        factory = registry.get_procedure_executors(vertical)
    except RegistryError:
        return None  # no registered executor factory (OQ-6) — cannot fire a governed run
    return build_event_resolver(spec, factory)


async def _alert_event_fire_failure(
    action: str, *, procedure_id: str | None, event_kind: str, reason: str
) -> None:
    """LOUD-on-failure for a dropped/failed event fire (PLAN-0056 Step 7 / ADR-0028 D4 mirror /
    AC-10): a WARN log + an ``event_fire_missed``/``event_fire_failed`` audit row + a best-effort
    Telegram alert (a distinct cooldown gate). **Never raises** into the fire/read path — both the
    audit write and the alert are best-effort, so a broken DB or a dead Telegram cannot turn a
    detection into a crash. Distinct from ``event_skipped`` (an idempotent/in-flight *skip* is a
    healthy no-op the fire fn already audits, Step 5); this is a *failure* to fire an actionable
    event.
    """
    logger.warning(
        "event bridge %s: event_kind=%r procedure=%r: %s", action, event_kind, procedure_id, reason
    )
    try:
        async with async_session() as session:
            await append_audit(
                session,
                action=action,
                payload={
                    "procedure_id": procedure_id,
                    "event_kind": event_kind,
                    "reason": reason,
                },
            )
            await session.commit()
    except Exception:  # audit is best-effort — a broken DB must not break the read path
        logger.exception("event bridge: failed to write %s audit", action)
    # notify_* is itself never-raise; the reason text stays out of the (no-PII) Telegram body.
    await notify_event_fire_failed(procedure_id=procedure_id, event_kind=event_kind)


async def _fire_event_for_record(
    resolve: Callable[..., EventRunRequest], record: ActionRecord
) -> EventFireOutcome | None:
    """FEED one actionable recommendation INTO the governed engine (ADR-0029 SD-1 / PLAN-0056
    Step 6). The ``event_kind`` is the recommender's ``suggested_handler`` (its semantic
    action label — ``RecommendedAction`` has no ``action_type``; SD-3 authors the vertical's
    ``event_trigger.event_kind`` to match it); ``entity_ids`` = the affected-entity primary keys;
    ``detected_at`` = the recommendation's ``created_at``.

    A dropped/failed fire is made LOUD (Step 7 / AC-10): an unmapped ``event_kind`` →
    ``event_fire_missed``; a fire that maps but errors mid-flight → ``event_fire_failed``. Both
    audit + best-effort-alert, then return ``None`` so the read path never breaks.
    """
    action = record.action
    try:
        request = resolve(
            event_kind=action.suggested_handler,
            entity_ids=[e.primary_key for e in action.affected_entities],
            detected_at=action.created_at,
        )
    except EventBridgeError as exc:
        # REACHABLE: an actionable recommendation whose kind maps to no event procedure.
        await _alert_event_fire_failure(
            "event_fire_missed",
            procedure_id=None,
            event_kind=action.suggested_handler,
            reason=str(exc),
        )
        return None
    try:
        async with async_session() as session:
            return await fire_event(session, request, now=datetime.now(UTC))
    except Exception as exc:  # defensive: the kind mapped but the governed fire errored
        await _alert_event_fire_failure(
            "event_fire_failed",
            procedure_id=request.procedure.procedure_id,
            event_kind=action.suggested_handler,
            reason=str(exc),
        )
        return None


async def _populate_store() -> None:
    """Read reading events from the active vertical's adapter and derive recommendations.

    PLAN-0056 Step 6 (ship-dark, SD-P3): when ``event_bridge_enabled`` is on **and** the active
    vertical maps a recommendation's ``suggested_handler`` to an ``event``-trigger procedure, the
    actionable recommendation is ALSO FED INTO the governed engine in-process (ADR-0029 SD-1/SD-4)
    — a real governed ``PipelineRun``, alongside (never replacing) the ``ActionRecord`` store
    write. Flag **off** (default) = zero behavior change: the resolver is never loaded and the
    fire branch is never reached.
    """
    vertical = settings.oct_vertical
    adapter = registry.get_adapter(vertical)
    resolve = await _load_event_bridge(vertical) if settings.event_bridge_enabled else None
    async for event in adapter.stream_events("reading"):
        record = await recommend(event, vertical)
        if record is not None:
            _action_store[record.action.id] = record
            if resolve is not None:
                await _fire_event_for_record(resolve, record)


def _get_record(action_id: str) -> ActionRecord:
    record = _action_store.get(action_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"no recommendation '{action_id}'")
    return record


@router.get("/objects/{object_type}", response_model=ObjectListResponse)
async def list_objects(object_type: str) -> ObjectListResponse:
    """List raw objects of one type from the active vertical's DataAdapter (ingress layer)."""
    adapter = registry.get_adapter(settings.oct_vertical)
    objects = await adapter.fetch_objects(object_type)
    return ObjectListResponse(object_type=object_type, count=len(objects), objects=objects)


@router.get("/meta", response_model=OntologyMeta)
async def get_meta() -> OntologyMeta:
    """Return the active vertical's ontology metadata (drives the ontology-driven UI)."""
    return load_ontology_meta(settings.oct_vertical)


@router.get("/recommendations", response_model=RecommendationListResponse)
async def list_recommendations() -> RecommendationListResponse:
    """List the current RecommendedActions, deriving them on the first call."""
    if not _action_store:
        await _populate_store()
    items = [_to_response(record) for record in _action_store.values()]
    return RecommendationListResponse(count=len(items), recommendations=items)


@router.post("/recommendations/{action_id}/approve", response_model=RecommendationResponse)
async def approve_recommendation(
    action_id: str,
    auth: Annotated[AuthContext, Depends(get_current_principal)],
) -> RecommendationResponse:
    """Approve a proposed recommendation (proposed -> approved).

    PLAN-0047 Step 1: the approver identity comes from the authn dependency
    (server-resolved from the bearer key — never the request body) and is
    recorded on the record for the execute-time identity projection.
    """
    record = _get_record(action_id)
    try:
        approve(record)
    except ApprovalError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    record.approved_by = auth.person_id
    return _to_response(record)


@router.post("/recommendations/{action_id}/execute", response_model=ExecuteResponse)
async def execute_recommendation(
    action_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    auth: Annotated[AuthContext, Depends(get_current_principal)],
) -> ExecuteResponse:
    """Execute an approved recommendation and persist it (approved -> executed).

    PLAN-0047 Step 1: the executor identity is server-resolved by the authn
    dependency and persisted with the projection (action_identity sidecar).
    """
    record = _get_record(action_id)
    try:
        receipt = await execute(record)
    except ApprovalError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    record.executed_by = auth.person_id
    await persist_executed_action(session, record)
    # PLAN-0015 D2: the recovery reading is the modeled effect of Execute —
    # injected into the live OperationalEvent view at real execute-time, on the
    # breach's asset, so Screen A resolves only after the operator acts. The
    # action id is ``action-<breach_event_id>`` (both LLM + rule paths), so the
    # breach event is identified without coupling to the handler payload shape.
    breach_event_id = record.action.id.removeprefix("action-")
    demo_events.inject_recovery(
        settings.oct_vertical,
        breach_event_id=breach_event_id,
        occurred_at=datetime.now(UTC),
    )
    return ExecuteResponse(
        action_id=record.action.id,
        status=record.status.value,
        handler_receipt=receipt,
    )
