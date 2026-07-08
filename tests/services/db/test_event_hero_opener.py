"""PLAN-0057 — the event-triggered hero-demo opener (the demo PROJECTION layer).

Proves the demo projection (AC-1 / AC-3b / AC-4): a detected asset-failure event auto-fires
``event_emergency_sourcing_round`` via the shipped event bridge (``build_event_resolver`` →
``fire_event``) to a persisted ``waiting_human`` run, and ``build_event_hero_governance_audit``
projects that parked run into the SAME ``HeroGovernanceAudit`` contract the manual opener draws
(``source: "event-fired"``), with the ``trigger_context`` sense cue folded into ``hero.trigger``.

Scoped to the demo projection only (PLAN-0057 SD-5): the engine-level fire → park → resolve →
``COMPLETED`` path is ALREADY proven by ``test_event_procurement_demo.py`` (the SAME procedure) and
is NOT re-proved here — the demo opener stops at the parked moment (like the manual opener,
``governance_audit.py`` LOCKED #3); the approve→COMPLETED beat is the front-end reveal (Step 4).

DB-backed (disposable ``<db>_test``, skips without Postgres); MS-S1-free — the shipped factory's
``advisory_stub_factory`` is deterministic (CLAUDE.md §8).
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from services.api.models.demo import HeroGovernanceAudit
from services.db.base import Base
from tests.db_support import create_test_engine
from verticals.procurement.hero_demo.run import (
    _EVENT_ASSET_ID,
    _EVENT_DETECTED,
    _EVENT_KIND,
    build_event_hero_governance_audit,
)


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


@pytest.fixture
async def session(db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as s:
        yield s


@pytest.fixture
async def procurement_registered() -> AsyncIterator[None]:
    """Register EXACTLY what the API lifespan registers — ``discover_and_register`` (adapters +
    handlers) + the procedure-executor factory — so the fired event run's action steps resolve."""
    from services.engine.discovery import discover_and_register
    from verticals.procurement.hero_demo.run import register_procurement_procedure_executors

    discover_and_register()
    await register_procurement_procedure_executors()
    yield


async def test_event_hero_opener_projects_parked_moment(
    session: AsyncSession, procurement_registered: None
) -> None:
    """AC-1 / AC-3b / AC-4 — the event opener fires, parks, and projects the hero contract + the
    beat-1 sense cue, reusing the offline contrast unchanged."""
    audit = await build_event_hero_governance_audit(session)

    # AC-1 — the shipped HeroGovernanceAudit contract validates, marked the event arm (no reshape).
    model = HeroGovernanceAudit.model_validate(audit)
    assert model.provisional is True
    assert model.source == "event-fired"

    hero = audit["hero"]
    # The ฿288,000 hero spend resolves to the [50k,500k) DOA tier → ผจก.จัดซื้อ → appr-pm.
    assert hero["governed_kind"] == "doa_tier"
    [doa] = hero["doa_tier"]
    assert doa["required_role"] == "ผจก.จัดซื้อ"
    assert doa["resolved_approver_id"] == "appr-pm"
    # SoD governed: the owning human req-planner requested; a DISTINCT approver appr-pm governs.
    assert hero["sod"]["governed"] is True
    assert hero["sod"]["requester"]["person_id"] == "req-planner"
    assert hero["sod"]["approver"]["person_id"] == "appr-pm"

    # AC-3b — the beat-1 "sense" cue rides on hero.trigger (render-only, from trigger_context).
    trig = hero["trigger"]
    assert trig["event_kind"] == _EVENT_KIND
    assert trig["entity_ids"] == [_EVENT_ASSET_ID]
    assert trig["detected_at"] == _EVENT_DETECTED.isoformat()
    assert trig["fired_at"]  # stamped by fire_event

    # AC-4 — the contrast is reused unchanged from the offline builder (฿99k → MANAGER).
    assert audit["contrast"]["po_id"]


async def test_event_opener_is_idempotent_and_replayable(
    session: AsyncSession, procurement_registered: None
) -> None:
    """The event run is event-keyed: a re-fire returns the SAME parked moment (never auto-resolves),
    so a presenter can replay the demo (the approve→COMPLETED beat is the front-end reveal)."""
    first = await build_event_hero_governance_audit(session)
    second = await build_event_hero_governance_audit(session)

    assert first["hero"]["po_id"] == second["hero"]["po_id"]
    assert second["source"] == "event-fired"
    assert second["hero"]["doa_tier"][0]["resolved_approver_id"] == "appr-pm"
