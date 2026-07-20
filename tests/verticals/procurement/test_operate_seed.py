"""PLAN-0054 Step 6c — the operate-demo seed persists a reachable, governed-resolvable run.

The Control-leg operate demo (View H) needs a persisted ``waiting_human`` procurement run the
Monitor can show + a DISTINCT approver can resolve under SoD. ``seed_operate_waiting_human_run``
drives the shipped YAML ``emergency_sourcing_round`` to its ``approve`` gate through the
deterministic hero executors (the ``advisory_stub`` LLM seam -- NO MS-S1), persisted with
``req-planner`` as the intake requester. DB-backed (skips without Postgres); MS-S1-free.

The two tests prove (c): the seed (1) persists a run reachable by ``load_run`` with the right
shape (status / suspended step / proposals / the SoD requester half), and (2) resolves GOVERNED
when a distinct approver (``appr-pm``, matching the ฿288,000 DOA tier) acts.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.db.base import Base
from services.engine.procedures.action_step import resolve_gated_step
from services.engine.procedures.persistence import load_run
from services.engine.procedures.runs import PipelineRunStatus, StepResultStatus
from services.engine.procedures.spec import load_procedures
from tests.db_support import create_test_engine
from verticals.procurement.hero_demo.run import seed_operate_waiting_human_run


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


async def test_seed_persists_reachable_waiting_human_run(db_engine: AsyncEngine) -> None:
    """(c) — the seed persists an ``emergency_sourcing_round`` run suspended at the ``approve``
    gate, reachable by ``load_run``, with ``req-planner`` recorded as the intake requester and
    >=1 decidable proposal for the Monitor to render."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        result = await seed_operate_waiting_human_run(session, run_id="operate-seed")
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value

    async with maker() as session:
        loaded = await load_run(session, "operate-seed")
    assert loaded is not None, "the seeded run is reachable by GET /runs/{id}"
    # the YAML procedure the resolve endpoint looks up in the vertical spec (NOT the re-id'd hero)
    assert loaded.run.procedure_id == "emergency_sourcing_round"
    assert loaded.run.status == PipelineRunStatus.WAITING_HUMAN.value
    # the requester half of the SoD map, recorded from the typed principal (never trigger_context)
    assert loaded.run.step_principals == {"intake": "req-planner"}
    approve_sr = next(sr for sr in loaded.step_results if sr.step_id == "approve")
    assert approve_sr.status == StepResultStatus.WAITING_HUMAN.value
    proposals = (approve_sr.artifact or {}).get("output_set", [])
    assert proposals and all(
        isinstance(p.get("action"), dict) for p in proposals
    ), "the approve gate carries >=1 decidable proposal for the Monitor to render"


async def test_seeded_run_is_governed_resolvable_by_distinct_approver(
    db_engine: AsyncEngine,
) -> None:
    """(c) — a DISTINCT approver (``appr-pm``, matching the ฿288,000 DOA tier) resolves the
    seeded gate GOVERNED: ``req-planner`` (intake) != ``appr-pm`` (approve), the handler executes,
    and the SoD audit-to-control tie names the approver. This is the operate demo's core moment."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        result = await seed_operate_waiting_human_run(session, run_id="operate-gov")

    spec = load_procedures("procurement")
    proc = next(p for p in spec.procedures if p.procedure_id == "emergency_sourcing_round")
    approver = next(p for p in spec.principals if p.person_id == "appr-pm")
    approve_sr = next(sr for sr in result.step_results if sr.step_id == "approve")
    action_ids = [p["action_id"] for p in (approve_sr.artifact or {})["output_set"]]

    async with maker() as session:
        resolved = await resolve_gated_step(
            session,
            "operate-gov",
            "approve",
            {aid: "approve" for aid in action_ids},
            principal=approver,
            procedure=proc,
            principals=spec.principals,
            principal_aliases=spec.principal_aliases,
        )
    assert resolved.status == StepResultStatus.RESOLVED.value
    assert resolved.artifact is not None
    assert all(e["status"] == "executed" for e in resolved.artifact["output_set"])
    assert resolved.audit is not None
    # At GATE resolution the audit ties name the ACTING approver (PLAN-0075 SD-6a): the SoD tie
    # (constraint 'approve+intake') AND the authority tie (the ladder-resolved doa_tier, now that
    # the tier-authority check confirmed appr-pm holds ผจก.จัดซื้อ). Engine order: SoD then authority.
    assert resolved.audit["governed_decision"] == [
        {"control_ref": {"kind": "sod", "id": "approve+intake"}, "principal_id": "appr-pm"},
        {"control_ref": {"kind": "doa_tier", "id": "ผจก.จัดซื้อ"}, "principal_id": "appr-pm"},
    ]


# --------------------------------------------------------------------------- #
# PLAN-0084 — AC-3 (default byte-compat + subject stamp) and AC-7 (rotation).
# --------------------------------------------------------------------------- #


async def test_intake_seed_default_is_hero_and_asset_keyed() -> None:
    """AC-3 (no DB needed) — the DEFAULT intake seed is the hero requisition, its
    failure event picked by ASSET KEY (``EVT-CNC-014-FAIL``) even though the fixture
    now ships one failure event per rotatable asset — never by row order."""
    from verticals.procurement.data_adapter.fastenal_csv import FastenalCsvAdapter
    from verticals.procurement.hero_demo.run import _intake_seed

    seed = await _intake_seed(FastenalCsvAdapter())
    assert seed["primary_key"] == "PO-2026-0412"
    assert seed["asset_id"] == "AST-CNC-014"
    assert seed["event_id"] == "EVT-CNC-014-FAIL"
    assert seed["event_type"] == "failure"
    assert seed["qty"] == 3  # the hero knob: 3 x 96,000 = ฿288,000
    assert seed["measured_value"] == 0.92


async def test_seed_default_trigger_context_is_additive_only(db_engine: AsyncEngine) -> None:
    """AC-3 — the default invocation's ``trigger_context`` is today's, plus ONLY the
    additive ``subject`` stamp (from the computed seed, not a literal)."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        result = await seed_operate_waiting_human_run(session, run_id="operate-ac3")
    tc = result.run.trigger_context or {}
    assert tc["source"] == "operate-demo-seed"
    assert tc["triggered_by"] == "req-planner"
    assert tc["subject"] == {"object_type": "Equipment", "primary_key": "AST-CNC-014"}
    assert set(tc) == {"source", "triggered_by", "subject"}, "additive ONLY — no other new keys"


async def test_seed_rotation_parks_every_rotatable_asset(db_engine: AsyncEngine) -> None:
    """AC-7 — every rotatable asset (exactly one PO — DATA-DRIVEN, never a hardcoded
    list) seeds end-to-end to ``waiting_human`` with its own subject stamp, and the
    parked doa audit names the tier + approver the seed script's stdout reports."""
    from verticals.procurement.data_adapter.fastenal_csv import FastenalCsvAdapter

    pos = await FastenalCsvAdapter().fetch_objects("PurchaseOrder")
    assets = sorted({p["equipment_id"] for p in pos})
    assert len(assets) == 5, "4 original + the PLAN-0084 CNC-009 fixture PO"
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    for i, asset in enumerate(assets):
        async with maker() as session:
            result = await seed_operate_waiting_human_run(
                session, run_id=f"operate-rot-{i}", asset_id=asset
            )
        assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value, asset
        tc = result.run.trigger_context or {}
        assert tc["subject"] == {"object_type": "Equipment", "primary_key": asset}
        approve_sr = next(sr for sr in result.step_results if sr.step_id == "approve")
        [doa] = (approve_sr.audit or {})["doa_tier"]
        assert doa["resolved_tier_id"], asset
        assert doa["resolved_approver_id"], asset


async def test_seed_unknown_asset_fails_listing_rotatable(db_engine: AsyncEngine) -> None:
    """AC-7 — an unknown asset id fails with a clear error listing the rotatable ids."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        with pytest.raises(ValueError, match="rotatable assets"):
            await seed_operate_waiting_human_run(session, run_id="operate-bad", asset_id="AST-NOPE")
