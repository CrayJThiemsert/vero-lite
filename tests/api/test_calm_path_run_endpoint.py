"""PLAN-0065 (SD-1(b)(i), AC-3) — the calm-path ``low_stock_reorder_round`` runs END-TO-END
from the production HTTP entry point.

The generic manual-run endpoint ``POST /procedures/{id}/run`` has no trigger guard (a
``manual`` procedure runs fine), so it already invokes this procedure. Over the REAL
procurement factory + registry-registered adapter, the projected ``read_stock`` ->
``judge_stock`` -> gated ``reorder`` chain runs to the human gate and parks ``waiting_human``
(a machine never reorders — RF-3). The run's identity is SERVER-resolved: a spoofed
``triggered_by`` in the body is overwritten by the authenticated principal.

DB-backed (disposable per-checkout test DB; skips without Postgres). MS-S1-free — the calm
path has no LLM step (L-1). procurement declares principals, so the bearer resolves against
the REAL ``req-planner`` principal (no ``_principal_index`` monkeypatch — it is a member).
"""

from __future__ import annotations

import hashlib
from collections.abc import AsyncIterator

import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.config import settings
from services.api.main import app
from services.db.base import Base
from services.db.session import get_session
from services.engine.discovery import discover_and_register
from tests.db_support import create_test_engine
from verticals.procurement.hero_demo.run import register_procurement_procedure_executors

_PROC_ID = "low_stock_reorder_round"
_GATED_STEP = "reorder"
RAW_KEY = "test-key-req-planner"
DIGEST = hashlib.sha256(RAW_KEY.encode("utf-8")).hexdigest()
HEADERS = {"Authorization": f"Bearer {RAW_KEY}"}


@pytest.fixture
async def procurement_client(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncClient]:
    """A DB-backed client bound to the procurement vertical with the SHIPPED factory
    registered; authn ON with one key -> the declared ``req-planner`` principal."""
    monkeypatch.setattr(settings, "oct_vertical", "procurement")
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", {DIGEST: "req-planner"})

    discover_and_register()
    await register_procurement_procedure_executors()

    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(eng, expire_on_commit=False)

    async def _override_session() -> AsyncIterator[AsyncSession]:
        async with maker() as session:
            yield session

    app.dependency_overrides[get_session] = _override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


async def test_calm_path_run_endpoint_parks_at_reorder(procurement_client: AsyncClient) -> None:
    """AC-3: the endpoint runs the chain end-to-end over HTTP to the gated ``reorder`` and
    parks ``waiting_human``; identity is server-resolved (spoofed body overwritten)."""
    response = await procurement_client.post(
        f"/procedures/{_PROC_ID}/run",
        json={"trigger_context": {"source": "test", "triggered_by": "spoofed-person"}},
        headers=HEADERS,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "waiting_human"
    assert body["suspended_step"] == _GATED_STEP
    assert body["triggered_by"] == "req-planner"  # server-resolved, not the spoofed body
    # both low-stock parts breach -> the gated reorder produced decidable proposals
    assert body["proposals"], "the gated reorder produced no decidable proposals"

    # the persisted run carries the server-resolved identity (the spoof is overwritten)
    run_id = body["run_id"]
    eng = await create_test_engine()
    try:
        async with eng.connect() as conn:
            tc = (
                await conn.execute(
                    sa.text("SELECT trigger_context FROM pipeline_runs WHERE run_id = :rid"),
                    {"rid": run_id},
                )
            ).scalar_one()
    finally:
        await eng.dispose()
    assert tc["triggered_by"] == "req-planner"
    assert tc["source"] == "test"


async def test_calm_path_run_requires_auth(procurement_client: AsyncClient) -> None:
    """AC-3: no bearer -> 401 (the production entry point is authenticated)."""
    response = await procurement_client.post(f"/procedures/{_PROC_ID}/run", json={})
    assert response.status_code == 401
