"""The ฿ facet a REAL governed run produces reaches the REAL rollup Tab J reads.

``tests/services/db/test_run_analytics_roundtrip.py`` already pins the Decimal -> JSON -> JSONB ->
numeric-cast round trip, but it does so through a hand-written ``_ImpactExec`` that writes the
facet straight onto the step trace. That harness agrees with itself by construction: it proves the
SQL, and it cannot see whether the shipped executors ever put a facet on that surface. They did
not — measured session 244, ``fleet_maintenance/governed_repair_approval`` produced a grounded
฿7,200 ``overpay_avoided`` facet on every run and ``benefit_rollup`` returned zero buckets for it,
because ``GovernanceActionExecutor._doa_tier`` left the facet nested inside the action envelope
(``StepResult.artifact["output_set"][*]["action"]["reasoning_trace"]``) while the rollup reads
``StepResult.reasoning_trace``.

So these are the scenario cases (CLAUDE.md §8): the real vertical YAML, the real ontology, the
real synthetic adapter, the real executors, the real ``persist_run``, and the real
``benefit_rollup`` SQL — producer driven into consumer, with nothing stubbed on either side of the
seam under test.

Two claims, and the second is not optional. The fleet ฿ must ARRIVE; and procurement's ฿ must not
DOUBLE — its ``emergency_sourcing_round`` carries two action steps over one event (``source``'s
``scored_rule`` and ``approve``'s ``doa_tier``), each of which builds the identical figure, so a
lift without a run-scoped ledger silently reports twice the benefit.

Offline apart from the disposable per-checkout test DB: synthetic adapters, committed CSVs, stubbed
advisory prose — no MS-S1, no live LLM.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from decimal import Decimal

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.api.config import settings
from services.db.base import Base
from services.db.run_analytics import BenefitBucket, benefit_rollup
from services.engine.discovery import discover_and_register
from services.engine.procedures.action_step import WaiverInvocation, resolve_gated_step
from services.engine.procedures.orchestrator import run_procedure
from services.engine.procedures.persistence import persist_run, resume_run
from services.engine.procedures.runs import PipelineRunStatus
from services.engine.procedures.spec import Person, load_procedures
from services.engine.registry import registry
from tests.db_support import create_test_engine

# The shipped fleet breach the partner's ฿30,000 comparison threshold applies to, and the ฿ the
# producer grounds off it: ฿48,000 quote x the disclosed 15% comparison-recovery fraction
# (Cray-ruled conservative, s195 — ``verticals/fleet_maintenance/economic_impact.py``).
_FLEET_NET = Decimal("7200")
# The representative emergency-sourcing hero PO's net benefit (procurement's committed-CSV ledger).
_PROCUREMENT_NET = Decimal("8107500")


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


async def _rollup(engine: AsyncEngine) -> list[BenefitBucket]:
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as fresh:
        return await benefit_rollup(fresh)


async def _run_and_persist(
    engine: AsyncEngine,
    vertical: str,
    procedure_id: str,
    run_id: str,
    *,
    principal: Person | None = None,
) -> list[BenefitBucket]:
    """Drive the vertical's REAL procedure through the REAL persistence path, then roll up."""
    spec = load_procedures(vertical)
    procedure = next(p for p in spec.procedures if p.procedure_id == procedure_id)
    agent = next(a for a in spec.agents if a.agent_id == procedure.run_by)
    factory = registry.get_procedure_executors(vertical)

    result = await run_procedure(
        procedure, agent, factory(), vertical=vertical, run_id=run_id, principal=principal
    )
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value, (
        "both heroes suspend at their human gate — a run that did not reach the gate would make "
        "an empty rollup meaningless"
    )

    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        await persist_run(session, result)
    return await _rollup(engine)


async def test_fleet_governed_repair_lands_its_baht_in_the_benefit_rollup(
    db_engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE fix. A real ``governed_repair_approval`` run — the breaching ฿48,000 quote routed to the
    owner's tier — puts its ``overpay_avoided`` facet where ``benefit_rollup`` reads, so Tab J's ฿
    figure is fed by the hero rather than by nothing.

    The run's SECOND breach is the negative control and it is grounded, not assumed: the ฿15,000
    mid-ladder quote sits under the partner's ฿30,000 comparison threshold, where the three-quote
    rule never applied, so the producer returns ``None`` and no facet exists to lift. That absence
    claim is only readable because the SAME instrument, in the SAME run, finds the ฿48,000 facet —
    ``facet_count == 1`` is one found and one correctly absent, never two silent misses."""
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    from verticals.fleet_maintenance.procedures_factory import (
        register_fleet_maintenance_procedure_executors,
    )

    discover_and_register()
    await register_fleet_maintenance_procedure_executors()

    buckets = await _run_and_persist(
        db_engine, "fleet_maintenance", "governed_repair_approval", "rollup-fleet-hero"
    )

    assert len(buckets) == 1, f"expected one ฿ bucket for the fleet hero, got {buckets!r}"
    bucket = buckets[0]
    assert bucket.procedure_id == "governed_repair_approval"
    assert bucket.currency == "THB"
    assert bucket.facet_kind == "overpay_avoided"
    assert bucket.facet_count == 1
    assert bucket.figures_missing == 0
    assert bucket.net_benefit_thb_sum == _FLEET_NET
    assert isinstance(bucket.net_benefit_thb_sum, Decimal)


async def test_the_figure_does_not_grow_when_the_gate_is_resolved_and_the_run_resumes(
    db_engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The same claim on a run driven PAST its gate, because that is the run Tab J reports on.

    Resume rebuilds the executors from the factory, so the run-scoped ledger starts empty again —
    if anything downstream of ``approve`` re-lifted, the ฿ would grow on resume and the suspended
    arm above would never catch it.

    ⚠️ **The two halves of the closing assertion are not equally attested, and saying so is the
    point.** That the figure is PRESENT and correct after the resume is witnessed RED (removing
    the ``_doa_tier`` lift empties this rollup too). That it is not DOUBLED is a forward-only
    guard: ``fulfill`` is an ``action`` step, but it runs over ``approve``'s action ENVELOPES,
    which carry no ``unit`` / ``measured_value``, so the fleet producer returns ``None`` there
    and no second facet exists to lift — measured, session 244. No mutation available today
    reddens that half, so it is registered here as INEXPRESSIBLE-BY-CONSTRUCTION rather than
    counted as evidence (CLAUDE.md §8). It becomes live the moment the plain fall-through branch
    of ``GovernanceActionExecutor.execute`` starts lifting, which is the deliberately-deferred
    other half of this defect."""
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    from verticals.fleet_maintenance.procedures_factory import (
        register_fleet_maintenance_procedure_executors,
    )

    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    spec = load_procedures("fleet_maintenance")
    procedure = next(p for p in spec.procedures if p.procedure_id == "governed_repair_approval")
    agent = next(a for a in spec.agents if a.agent_id == procedure.run_by)
    factory = registry.get_procedure_executors("fleet_maintenance")
    # The requester must be threaded through the run, or the live SoD check at the gate fails
    # closed on an unresolved requester and the resolve below never happens.
    mechanic = next(p for p in spec.principals if p.person_id == "req-mechanic-tom")
    run_id = "rollup-fleet-resume"

    result = await run_procedure(
        procedure, agent, factory(), vertical="fleet_maintenance", run_id=run_id, principal=mechanic
    )
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        await persist_run(session, result)
    assert [b.facet_count for b in await _rollup(db_engine)] == [
        1
    ], "the suspended baseline, before the resume"

    gate = next(s for s in result.step_results if s.step_id == "approve")
    action_ids = [str(p["action_id"]) for p in (gate.artifact or {})["output_set"]]
    async with maker() as session:
        await resolve_gated_step(
            session,
            run_id,
            "approve",
            dict.fromkeys(action_ids, "approve"),
            mechanic,
            procedure=procedure,
            principals=list(spec.principals),
            # The authored roadside waiver — the shipped path a recorder can take the whole set
            # through in one call, so this test stays about the ฿ and not about the ladder.
            waiver_invocation=WaiverInvocation(
                justification="รถเสียหน้างาน โทรหาเฮียแล้วเคาะมาว่าให้ซ่อมเลย"
            ),
        )
    async with maker() as session:
        resumed = await resume_run(
            session, procedure, agent, factory(), run_id, vertical="fleet_maintenance"
        )
    assert "fulfill" in {s.step_id for s in resumed.step_results}, "the run advanced past the gate"

    after = await _rollup(db_engine)
    assert len(after) == 1
    assert after[0].facet_count == 1, "resuming the run must not re-lift the same ฿ figure"
    assert after[0].net_benefit_thb_sum == _FLEET_NET


async def test_procurement_emergency_sourcing_is_not_double_counted(
    db_engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The hazard the fleet fix opens, held shut.

    ``emergency_sourcing_round`` runs TWO action steps over one failure event, and the base
    executor builds the identical ``expedite_tradeoff`` figure at both: ``source`` (a
    ``scored_rule`` gate, which lifts because it REPLACES the output and would otherwise destroy
    the facet) and ``approve`` (a ``doa_tier`` gate, which now lifts too). Without the run-scoped
    ledger this rollup reports ``facet_count=2`` and ฿16,215,000 — double the real benefit, on the
    shipped hero, with nothing on screen to indicate it.

    The exact ฿ is asserted, not just the count: a ledger that deduped by dropping the wrong one
    would keep the count right and the figure wrong."""
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    from verticals.procurement.hero_demo.run import register_procurement_procedure_executors

    discover_and_register()
    await register_procurement_procedure_executors()

    buckets = await _run_and_persist(
        db_engine, "procurement", "emergency_sourcing_round", "rollup-proc-hero"
    )

    assert len(buckets) == 1, f"expected one ฿ bucket for the procurement hero, got {buckets!r}"
    bucket = buckets[0]
    assert bucket.procedure_id == "emergency_sourcing_round"
    assert bucket.facet_kind == "expedite_tradeoff"
    assert bucket.facet_count == 1, "the same event's figure must be rolled up ONCE per run"
    assert bucket.net_benefit_thb_sum == _PROCUREMENT_NET
