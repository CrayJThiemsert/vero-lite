"""End-to-end action-loop integration test (PLAN-0006 §7.5).

Drives read -> recommend (LLM, faked) -> approve -> execute through the
API. The autouse ``_offline_llm`` fixture (tests/api/conftest.py) forces
recommend() onto a deterministic offline LLM, so the loop exercises the
LLM path with no live Ollama call. ``test_full_action_loop`` additionally
verifies the persisted recommended_action row and requires a live
postgres:16-alpine (skips gracefully otherwise via client_with_db).
"""

from __future__ import annotations

import sqlalchemy as sa
from httpx import AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import create_async_engine

from services.api.config import settings


async def test_recommendations_use_the_faked_llm_path(client: AsyncClient) -> None:
    """§7.5: GET /recommendations derives actions via the faked LLM path.

    No database needed — this always runs and proves the LLM path (not
    the rule fail-safe) produced the recommendations: the title is the
    one the offline LLM stub emits, distinct from the rule path's.
    """
    listing = await client.get("/recommendations")
    assert listing.status_code == 200
    recommendations = listing.json()["recommendations"]
    assert recommendations, "expected at least one recommendation from synthetic data"
    for rec in recommendations:
        assert rec["status"] == "proposed"
        assert "LLM assessment" in rec["title"], "recommendation must come from the LLM path"
        assert rec["confidence"] == 0.88


async def test_full_action_loop_read_recommend_approve_execute(
    client_with_db: AsyncClient,
) -> None:
    """One case drives the whole LLM-path loop; the persisted row ends 'executed'."""
    # read -> recommend (LLM, faked)
    listing = await client_with_db.get("/recommendations")
    assert listing.status_code == 200
    recommendations = listing.json()["recommendations"]
    assert recommendations, "expected at least one recommendation from synthetic data"
    proposed = recommendations[0]
    assert proposed["status"] == "proposed"
    assert proposed["requires_approval"] is True
    assert "LLM assessment" in proposed["title"], "loop must run on the LLM path"
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
