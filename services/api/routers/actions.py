"""Action-loop API router — three-layer wiring (ADR-007 D3/D4, PLAN-0005 §6.7).

Exposes the read -> recommend -> approve -> execute loop over the energy
vertical: object listing (ingress), recommendation listing, and the
approve / execute gate endpoints. Recommendations are held in a
process-local store keyed by action_id; executing an action also
persists it (the OQ-1 projection) via services/db/persistence.py.
"""

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
from services.db.persistence import persist_executed_action
from services.db.session import get_session
from services.engine import demo_events
from services.engine.ontology_meta import OntologyMeta, load_ontology_meta
from services.engine.recommender import ActionRecord, ApprovalError, approve, execute, recommend
from services.engine.registry import registry

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


async def _populate_store() -> None:
    """Read reading events from the active vertical's adapter and derive recommendations."""
    vertical = settings.oct_vertical
    adapter = registry.get_adapter(vertical)
    async for event in adapter.stream_events("reading"):
        record = await recommend(event, vertical)
        if record is not None:
            _action_store[record.action.id] = record


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
