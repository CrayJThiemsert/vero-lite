"""End-to-end action-loop integration test (PLAN-0005 §7.4).

Drives read -> recommend -> approve -> execute through the API and
verifies both the terminal status and the persisted recommended_action
row. Requires a live postgres:16-alpine; skips gracefully otherwise via
the client_with_db fixture.
"""

from __future__ import annotations

import sqlalchemy as sa
from httpx import AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import create_async_engine

from services.api.config import settings


async def test_full_action_loop_read_recommend_approve_execute(
    client_with_db: AsyncClient,
) -> None:
    """One case drives the whole loop; the persisted row ends 'executed'."""
    # read -> recommend
    listing = await client_with_db.get("/recommendations")
    assert listing.status_code == 200
    recommendations = listing.json()["recommendations"]
    assert recommendations, "expected at least one recommendation from synthetic data"
    proposed = recommendations[0]
    assert proposed["status"] == "proposed"
    assert proposed["requires_approval"] is True
    action_id = proposed["action_id"]

    # approve
    approved = await client_with_db.post(f"/recommendations/{action_id}/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    # execute
    executed = await client_with_db.post(f"/recommendations/{action_id}/execute")
    assert executed.status_code == 200
    body = executed.json()
    assert body["status"] == "executed"
    assert body["handler_receipt"]["executed"] is True

    # the persisted row reflects the executed action (OQ-4)
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                sa.text("SELECT status FROM recommended_action WHERE action_id = :aid"),
                {"aid": action_id},
            )
            row = result.first()
    finally:
        await engine.dispose()
    assert row is not None, f"no persisted recommended_action row for {action_id}"
    assert row[0] == "executed"
