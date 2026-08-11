"""PLAN-0103 Step 7 — fleet's operate-demo seed parks a real gate for Tab H's first paint.

Toward AC-8's **first clause**: Tab H's backing read returns >= 1 waiting run at boot.

This module drives the REAL seeder — the shipped ``governed_repair_approval`` through the
registry's real executor factory over a REAL (disposable) Postgres — and reads the result
back with ``load_run``, the same loader ``GET /runs/{id}`` uses.
``tests/api/test_monitor_runs.py`` seeds ``PipelineRun`` rows by hand, which is right for
testing the *projection*; it would be wrong here, because what is under test is whether
the **procedure actually parks**, and a hand-written row parks by construction.

MS-S1-free and deterministic: the registered fleet factory wires the synthetic adapter,
pure band math, pure AT-2 resolution and the stubbed advisory prose (CLAUDE.md §8).
DB-backed, so it skips gracefully when Postgres is unreachable.

⚠️ **Two gaps, named rather than papered over — AC-8 is NOT closed by this module.**

1. It does not drive the HTTP ``GET /runs`` route; it asserts the persisted run the route
   reads. The route's own projection is covered by ``tests/api/test_monitor_runs.py``, but
   the two have not been joined end to end here.
2. AC-8's **second clause** — a case opened via Tab I's backend appearing in H's list —
   is not covered at all. It runs through the case → accepted-quote → event-stream →
   ``case_projection`` bridge, which is its own scenario.

Leaving both unwritten and saying so is the honest state; asserting the seed alone and
calling the AC closed is exactly the shape this PLAN has already caught twice.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.api.config import settings
from services.db.base import Base
from services.engine.discovery import discover_and_register
from services.engine.procedures.orchestrator import ProcedureError
from services.engine.procedures.persistence import load_run
from services.engine.procedures.runs import PipelineRunStatus, StepResultStatus
from tests.db_support import create_test_engine
from verticals.fleet_maintenance.operate_seed import (
    DEMO_RUN_ID,
    seed_repair_gate_waiting_human_run,
)
from verticals.fleet_maintenance.procedures_factory import (
    register_fleet_maintenance_procedure_executors,
)


@pytest.fixture
async def fleet_registered(monkeypatch: pytest.MonkeyPatch) -> None:
    """The same registration path ``services/api/main.py`` runs at startup, in the same
    order: the executor factory is registered BEFORE the seed block runs. The seeder
    reads its executors from the registry, so this ordering is load-bearing rather than
    incidental setup."""
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    discover_and_register()
    await register_fleet_maintenance_procedure_executors()


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


async def test_seed_parks_a_real_repair_gate(
    fleet_registered: None, db_engine: AsyncEngine
) -> None:
    """The seed drives the SHIPPED ``governed_repair_approval`` to its ``approve`` gate and
    persists it parked, with the head mechanic recorded as the intake requester — the half
    of the SoD map that makes the refused-then-granted moment possible."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        result = await seed_repair_gate_waiting_human_run(session)
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value

    async with maker() as session:
        loaded = await load_run(session, DEMO_RUN_ID)
    assert loaded is not None, "the seeded run is reachable by GET /runs/{id}"
    assert loaded.run.procedure_id == "governed_repair_approval"
    assert loaded.run.status == PipelineRunStatus.WAITING_HUMAN.value
    # Recorded from the typed principal, never from trigger_context — a distinct approver
    # is what keeps SoD governed when the gate is resolved.
    assert loaded.run.step_principals == {"intake": "req-mechanic-tom"}
    approve = next(sr for sr in loaded.step_results if sr.step_id == "approve")
    assert approve.status == StepResultStatus.WAITING_HUMAN.value
    proposals = (approve.artifact or {}).get("output_set", [])
    assert proposals and all(
        isinstance(p.get("action"), dict) for p in proposals
    ), "the parked gate carries >=1 decidable proposal for the Monitor to render"


async def test_the_parked_gate_routes_two_spends_to_two_different_humans(
    fleet_registered: None, db_engine: AsyncEngine
) -> None:
    """The gate parked because the AUTHORITY LADDER routed it, not merely because the run
    stopped — and it routes **by amount**, which is the sentence fleet's card copy makes to
    a visitor: *where it stops is decided by the number, not by who you know.*

    The shipped fixture breaches the ฿5,000 ceiling on exactly two trucks, and the two
    spends fall in different bands, so one parked gate carries two proposals resolving to
    two DIFFERENT tiers and two DIFFERENT approvers. Asserting only "a tier was resolved"
    would pass just as happily if both landed on the same human — which would silently
    destroy the demo's whole teaching moment while every status line stayed green."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        result = await seed_repair_gate_waiting_human_run(session, run_id="fleet-seed-doa")
    approve = next(sr for sr in result.step_results if sr.step_id == "approve")
    verdicts = (approve.audit or {})["doa_tier"]

    assert len(verdicts) >= 2, "the fixture breaches the ceiling on more than one truck"
    assert all(v["resolved_tier_id"] for v in verdicts), "every breach resolved a tier"
    assert all(v["resolved_approver_id"] for v in verdicts), "every tier named a human"
    assert (
        len({v["resolved_tier_id"] for v in verdicts}) >= 2
    ), "the ladder ROUTES — the parked gate must span more than one tier"
    assert (
        len({v["resolved_approver_id"] for v in verdicts}) >= 2
    ), "two tiers must resolve to two different people, or the routing is invisible"
    # Every proposal on the gate is accounted for by a verdict: a proposal with no verdict
    # would be an un-routed spend sitting on a governance gate.
    proposals = (approve.artifact or {}).get("output_set", [])
    assert len(verdicts) == len(proposals)


async def test_seed_trigger_context_is_the_operate_demo_contract(
    fleet_registered: None, db_engine: AsyncEngine
) -> None:
    """The seeded run announces itself as the demo seed and names the human it acts for.
    No ``subject`` key: fleet's breaching truck is chosen by the declared query during the
    run, so it is not knowable beforehand — asserting its absence keeps a future addition
    an explicit decision rather than a silent one."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        result = await seed_repair_gate_waiting_human_run(session, run_id="fleet-seed-tc")
    tc = result.run.trigger_context or {}
    assert tc["source"] == "operate-demo-seed"
    assert tc["triggered_by"] == "req-mechanic-tom"
    assert set(tc) == {"source", "triggered_by"}


async def test_seed_raises_when_the_gate_does_not_park(
    fleet_registered: None, db_engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The seeder REFUSES to report success for a run that did not park. Without that check
    the boot log would say "seeded" while Tab H opened empty — the silent-success shape
    this PLAN has now caught twice.

    ⚠️ **What this probe does and does not prove, stated rather than implied.** All three
    fleet procedures park by design, so there is no natural non-parking run to drive; this
    patches the status constant the guard compares against, which proves the comparison is
    LIVE and its error is reachable. It does not prove the guard fires on a genuinely
    unparked run, because no such run exists to produce. A stronger probe would need a
    procedure that completes — if one is ever authored here, replace this."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    monkeypatch.setattr(
        "verticals.fleet_maintenance.operate_seed.StepResultStatus",
        type("_S", (), {"WAITING_HUMAN": type("_V", (), {"value": "not-a-real-status"})}),
    )
    async with maker() as session:
        with pytest.raises(ProcedureError, match="did not park at waiting_human"):
            await seed_repair_gate_waiting_human_run(session, run_id="fleet-seed-noprk")
