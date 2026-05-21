"""Persistence projection — RecommendedAction envelope to ontology rows.

OQ-1: the ADR-007 D2 runtime envelope is projected to the energy
ontology entities at the persistence boundary. ``persist_executed_action``
writes the executed action as a ``recommended_action`` row plus the
``alert`` row its required foreign key needs.

``target_asset_id`` is left NULL: Phase 2 persists the action and its
alert; assets are served from the synthetic adapter, not the database.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from services.db.models import Alert, RecommendedAction
from services.engine.recommender import ActionRecord


async def persist_executed_action(session: AsyncSession, record: ActionRecord) -> None:
    """Project an executed ActionRecord to ontology rows and persist them.

    Uses ``merge`` so re-persisting the same action is idempotent rather
    than a duplicate-key error.
    """
    action = record.action
    alert_id = f"alert-{action.id}"
    await session.merge(
        Alert(
            alert_id=alert_id,
            title=action.title,
            status="open",
            opened_at=action.created_at,
            reasoning=action.description,
        )
    )
    await session.merge(
        RecommendedAction(
            action_id=action.id,
            confidence_score=action.confidence,
            status=record.status.value,
            parameters=action.handler_payload,
            alert_id=alert_id,
            target_asset_id=None,
        )
    )
    await session.commit()
