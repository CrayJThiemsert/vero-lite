"""PLAN-0114 Step 1 — the ``continue_no_decision_run`` chokepoint, DB-backed.

Proves, against a real Postgres round-trip (skips without one), that a gate holding
nothing decidable can be acknowledged by an accountable human and reach ``completed``
— PLAN-0113 SD-3 ruled (b) — while the seam refuses, fail-closed, every case that is
NOT a no-decision gate.

**Probe predictions (CLAUDE.md §8; one probe per assertion).** Each entry names the
mutation, the ONE assertion it must redden, and the assertion that must stay GREEN
under it — that green is what rules out "something unrelated broke". P1..P8 were
written BEFORE the first run; P9's provenance is recorded honestly below.

* **P1** disable the ``_has_decidable_proposals`` guard
  -> reddens ``..._refused_by_its_own_mechanism`` | green: ``..._completes_through_...``
* **P2** disable the ``artifact is None`` guard
  -> reddens ``..._escalated_failure_suspend_...`` | green: ``..._completes_through_...``
* **P3** disable the ``actor_person_id is None`` guard
  -> reddens ``..._without_an_identified_human_...`` | green: ``..._completes_through_...``
* **P4** disable the ``suspended.step_id != step_id`` guard
  -> reddens ``..._naming_a_step_other_than_...`` | green: ``..._completes_through_...``
* **P5** disable the ``status != waiting_human`` guard
  -> reddens ``..._is_not_parked_has_nothing_...`` | green: ``..._completes_through_...``
* **P6** rename the audited action
  -> reddens ``..._chain_row_records_...`` | green: ``..._step_block_records_...``
* **P7** change the key at the ``suspended.audit`` write site
  -> reddens ``..._step_block_records_...`` | green: ``..._chain_row_records_...``
* **P8** hard-code ``upstream`` to ``[]``
  -> reddens ``..._block_records_the_upstream_shape`` | green: ``..._step_block_records_...``
* **P9** return the pre-resume result instead of the resumed one
  -> reddens ``..._completes_through_...`` | green: ``..._refused_by_its_own_mechanism``

**P9 was NOT predicted before the run.** It was added after
``tools/probe_coverage.py`` (lesson #0047 §6) named the happy-path claim as
never-reddened: that claim is every other probe's CONTROL, and a control is by
construction never witnessed. Being AC-1's DB-level half, it earns a probe rather
than an exemption. Recorded rather than back-dated.

**On P1, the mandatory one** (PLAN-0114 AC-2(a), the security boundary under SD-3):
note what its test does NOT assert — a bare ``ProcedureError``. ``resume_run`` carries
a second, pre-existing guard that refuses the same case with the SAME exception type,
so an assertion on the type (or on an HTTP status once the route lands) cannot tell
the two layers apart and would stay green under P1. The test matches the chokepoint's
OWN detail string instead. The two layers are close enough that P1's first anchor
matched both sites and the probe refused to run until it was narrowed.

**P6/P7 are a mutually-isolating pair**: each drops one half of the SD-2 dual audit,
and the other half's test is the control proving the write path still ran at all.

**Never reddened, named** (lesson #0047 §6 clause 4): ``_park``'s precondition assert
that the fixture parked the run. It guards the fixture, not the subject; no mutation
of ``continue_no_decision_run`` can reach it. If it reddens, the fixture broke — which
is what it is there to say.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from sqlalchemy.orm.exc import StaleDataError

from services.db.audit_log import AuditLog
from services.db.base import Base
from services.engine.procedures.orchestrator import (
    ProcedureError,
    RunContext,
    StepExecutor,
    StepOutcome,
    run_procedure,
)
from services.engine.procedures.persistence import (
    NO_DECISION_ACK_KEY,
    NoDecisionApproverError,
    continue_no_decision_run,
    persist_run,
)
from services.engine.procedures.runs import (
    PipelineRun,
    PipelineRunStatus,
    StepResult,
    StepResultStatus,
)
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    Procedure,
    Step,
    StepKind,
)
from tests.db_support import create_test_engine

_ACTOR = "appr-fleet-manager-wirat"


class _Query:
    """Fixed-output query executor."""

    def __init__(self, output: list[Any]) -> None:
        self.output = output

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(
            output=self.output, reasoning_trace=[{"kind": "query", "summary": "read"}]
        )


class _EmptyAction:
    """An action executor that proposes nothing — the no-decision gate."""

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(output=[], reasoning_trace=[{"kind": "judge", "summary": "nothing"}])


class _ProposingAction:
    """An action executor that proposes ONE real ADR-007 envelope — the control run.

    Its presence is what makes the empty-gate assertions non-vacuous: the same
    fixtures CAN produce a proposal, so "zero proposals" is a measured outcome rather
    than a fixture that could never produce one.
    """

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(
            output=[
                {
                    "action_id": "act-1",
                    "action": {"handler": "aerate", "payload": {"pond_id": "p7"}},
                    "title": "Aerate p7",
                }
            ],
            reasoning_trace=[{"kind": "judge", "summary": "one"}],
        )


def _agent() -> Agent:
    return Agent(
        agent_id="pond_agent",
        name="Pond Agent",
        autonomy_ceiling=Autonomy.GATED,
        allowed=AgentAllowed(action_handlers=["aerate"]),
    )


def _procedure(procedure_id: str) -> Procedure:
    return Procedure(
        procedure_id=procedure_id,
        title="Round",
        goal="Act on DO breaches.",
        run_by="pond_agent",
        steps=[
            Step(step_id="read", name="Read", kind=StepKind.QUERY),
            Step(step_id="aerate", name="Aerate", kind=StepKind.ACTION, handler="aerate"),
        ],
    )


def _executors(proposing: bool, rows: list[Any]) -> dict[StepKind, StepExecutor]:
    action: StepExecutor = _ProposingAction() if proposing else _EmptyAction()
    return {StepKind.QUERY: _Query(rows), StepKind.ACTION: action}


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        # BOUND THE TEARDOWN. drop_all needs ACCESS EXCLUSIVE; a session this module
        # left `idle in transaction` holds a conflicting lock and drop_all then waits
        # FOREVER — measured s253: a 67-minute hang whose head of the queue was one
        # un-rolled-back session in this file, with a second pytest process queued
        # behind it. Unbounded, that failure mode never reddens; it just stops. With a
        # timeout it becomes a loud, ordinary test failure that names the right file.
        await conn.execute(sa.text("SET lock_timeout = '20s'"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


async def _park(
    db_engine: AsyncEngine, procedure: Procedure, run_id: str, *, proposing: bool = False
) -> None:
    """Run to the gated suspend and persist it."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    result = await run_procedure(
        procedure,
        _agent(),
        _executors(proposing, [{"pond": "p7", "event_id": "e7"}]),
        vertical="aquaculture",
        run_id=run_id,
    )
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    async with maker() as session:
        await persist_run(session, result)


async def _continue(
    db_engine: AsyncEngine,
    procedure: Procedure,
    run_id: str,
    step_id: str = "aerate",
    *,
    actor: str | None = _ACTOR,
) -> Any:
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        return await continue_no_decision_run(
            session,
            procedure,
            _agent(),
            _executors(False, []),
            run_id,
            step_id,
            vertical="aquaculture",
            actor_person_id=actor,
        )


async def _audit_actions(db_engine: AsyncEngine, run_id: str) -> list[str]:
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        rows = await session.execute(
            sa.select(AuditLog.action).where(AuditLog.run_id == run_id).order_by(AuditLog.audit_id)
        )
        return [str(r[0]) for r in rows]


async def _step_audit(db_engine: AsyncEngine, run_id: str, step_id: str) -> dict[str, Any]:
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        row = await session.execute(
            sa.select(StepResult).where(StepResult.run_id == run_id, StepResult.step_id == step_id)
        )
        result = row.scalar_one()
        return dict(result.audit or {})


async def _audit_payload(db_engine: AsyncEngine, run_id: str, action: str) -> dict[str, Any]:
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        row = await session.execute(
            sa.select(AuditLog).where(AuditLog.run_id == run_id, AuditLog.action == action)
        )
        return dict(row.scalars().one().payload or {})


async def _audit_step_ids(db_engine: AsyncEngine, run_id: str, action: str) -> list[str | None]:
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        rows = await session.execute(
            sa.select(AuditLog.step_id).where(AuditLog.run_id == run_id, AuditLog.action == action)
        )
        return [r[0] for r in rows]


async def _seed_parked(
    db_engine: AsyncEngine, run_id: str, procedure_id: str, *, artifact: dict[str, Any] | None
) -> None:
    """Seed a waiting_human run + one suspended step with a caller-chosen artifact.

    Direct seeding, because the two cases below cannot be reached by running the
    procedure: an escalated-failure suspend (``artifact is None``) and a non-proposal
    suspend carrying rows.
    """
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    now = datetime.now(UTC)
    async with maker() as session:
        session.add(
            PipelineRun(
                run_id=run_id,
                procedure_id=procedure_id,
                agent_id="pond_agent",
                status=PipelineRunStatus.WAITING_HUMAN.value,
                started_at=now,
                updated_at=now,
            )
        )
        session.add(
            StepResult(
                step_result_id=f"{run_id}:aerate",
                run_id=run_id,
                step_id="aerate",
                status=StepResultStatus.WAITING_HUMAN.value,
                artifact=artifact,
                created_at=now,
            )
        )
        await session.commit()


# --------------------------------------------------------------------------- happy path


async def test_the_empty_gate_completes_through_the_chokepoint(db_engine: AsyncEngine) -> None:
    """PLAN-0113 SD-3 (b): a gate with nothing decidable reaches completed."""
    procedure = _procedure("cnd-happy")
    await _park(db_engine, procedure, "cnd-1")
    resumed = await _continue(db_engine, procedure, "cnd-1")
    assert resumed.run.status == PipelineRunStatus.COMPLETED.value


# ------------------------------------------------------------------------- fail-closed


async def test_a_gate_holding_decidable_proposals_is_refused_by_its_own_mechanism(
    db_engine: AsyncEngine,
) -> None:
    """AC-2(a), the security boundary: /continue is never a resolve bypass.

    Matched on the chokepoint's OWN detail string. ``resume_run``'s second guard
    refuses the same case with the same exception type, so a type-only assertion
    would stay green with this guard deleted and would witness nothing.
    """
    procedure = _procedure("cnd-decidable")
    await _park(db_engine, procedure, "cnd-2", proposing=True)
    with pytest.raises(ProcedureError, match="holds decidable proposals"):
        await _continue(db_engine, procedure, "cnd-2")


async def test_an_escalated_failure_suspend_is_refused_as_a_retry_surface(
    db_engine: AsyncEngine,
) -> None:
    """Guard 2 (OQ-1): ``artifact is None`` is a retry surface, not an acknowledgment."""
    procedure = _procedure("cnd-escalated")
    await _seed_parked(db_engine, "cnd-3", "cnd-escalated", artifact=None)
    with pytest.raises(ProcedureError, match="escalated FAILURE suspend"):
        await _continue(db_engine, procedure, "cnd-3")


async def test_acknowledging_without_an_identified_human_is_refused(
    db_engine: AsyncEngine,
) -> None:
    """Guard 3 (RF-1, keyed on actor_person_id per the corrected PLAN)."""
    procedure = _procedure("cnd-rf1")
    await _park(db_engine, procedure, "cnd-4")
    with pytest.raises(NoDecisionApproverError, match="requires an identified human"):
        await _continue(db_engine, procedure, "cnd-4", actor=None)


async def test_naming_a_step_other_than_the_suspended_one_is_refused(
    db_engine: AsyncEngine,
) -> None:
    """The acknowledging human names what they believe they are acknowledging."""
    procedure = _procedure("cnd-mismatch")
    await _park(db_engine, procedure, "cnd-5")
    with pytest.raises(ProcedureError, match="is not the step this run is suspended at"):
        await _continue(db_engine, procedure, "cnd-5", step_id="read")


async def test_a_run_that_is_not_parked_has_nothing_to_acknowledge(
    db_engine: AsyncEngine,
) -> None:
    """A settled run is not a gate."""
    procedure = _procedure("cnd-settled")
    await _park(db_engine, procedure, "cnd-6")
    await _continue(db_engine, procedure, "cnd-6")  # -> completed
    with pytest.raises(ProcedureError, match="is not parked at a gate"):
        await _continue(db_engine, procedure, "cnd-6")


# ------------------------------------------------------------------ SD-2 dual audit


async def test_the_chain_row_records_the_acknowledgment(db_engine: AsyncEngine) -> None:
    """SD-2 level 1: the tamper-evident chain carries run_continued_no_decision."""
    procedure = _procedure("cnd-chain")
    await _park(db_engine, procedure, "cnd-7")
    await _continue(db_engine, procedure, "cnd-7")
    assert "run_continued_no_decision" in await _audit_actions(db_engine, "cnd-7")


async def test_the_step_audit_carries_the_acknowledgment_key(db_engine: AsyncEngine) -> None:
    """SD-2 level 2, half one: the block is stored where the readers look.

    Split from the assertion below deliberately. Both facts used to ride on one
    test, and the KEY half was carried by a bare dict subscript rather than by an
    assertion — so a mutation of the key reddened the test with a ``KeyError``
    raised BEFORE the tracked assertion ran, and the battery credited a claim that
    had never executed. One claim per test; the subscript is now an assertion.
    """
    procedure = _procedure("cnd-key")
    await _park(db_engine, procedure, "cnd-14")
    await _continue(db_engine, procedure, "cnd-14")
    assert NO_DECISION_ACK_KEY in await _step_audit(db_engine, "cnd-14", "aerate")


async def test_the_step_block_records_the_acknowledging_human(db_engine: AsyncEngine) -> None:
    """SD-2 level 2, half two: the block names the accountable human.

    ``.get`` rather than ``[]`` so this assertion can only fail as an assertion —
    a missing key yields ``None`` and reddens the comparison, never a ``KeyError``
    short-circuiting it (the defect the test above was split out to close).
    """
    procedure = _procedure("cnd-block")
    await _park(db_engine, procedure, "cnd-8")
    await _continue(db_engine, procedure, "cnd-8")
    audit = await _step_audit(db_engine, "cnd-8", "aerate")
    assert audit.get(NO_DECISION_ACK_KEY, {}).get("acknowledged_by") == _ACTOR


async def test_the_block_records_the_upstream_shape(db_engine: AsyncEngine) -> None:
    """The universal block (Cray, s253): a reader reconstructs WHY it was empty.

    The positive control is the ``read`` step: it produced one row, so an assertion
    that the upstream list is populated cannot be satisfied by an empty list.
    """
    procedure = _procedure("cnd-upstream")
    await _park(db_engine, procedure, "cnd-9")
    await _continue(db_engine, procedure, "cnd-9")
    block = (await _step_audit(db_engine, "cnd-9", "aerate"))[NO_DECISION_ACK_KEY]
    assert [(u["step_id"], u["kind"], u["output_count"]) for u in block["upstream"]] == [
        ("read", "query", 1)
    ]


async def test_the_chain_row_names_the_acknowledged_step(db_engine: AsyncEngine) -> None:
    """SD-2 level 1 carries the step, not just the action name."""
    procedure = _procedure("cnd-chainstep")
    await _park(db_engine, procedure, "cnd-10")
    await _continue(db_engine, procedure, "cnd-10")
    assert await _audit_step_ids(db_engine, "cnd-10", "run_continued_no_decision") == ["aerate"]


async def test_the_chain_row_records_zero_decidable_proposals(db_engine: AsyncEngine) -> None:
    """SD-2 level 1 carries proposal_count.

    The positive control is the ``read`` step's one row: the run genuinely produced
    output, so a zero here is a measured property of the GATE, not of an empty run.
    """
    procedure = _procedure("cnd-chaincount")
    await _park(db_engine, procedure, "cnd-11")
    await _continue(db_engine, procedure, "cnd-11")
    payload = await _audit_payload(db_engine, "cnd-11", "run_continued_no_decision")
    assert payload["proposal_count"] == 0


async def test_a_non_proposal_suspend_records_zero_proposals_beside_its_row_count(
    db_engine: AsyncEngine,
) -> None:
    """proposal_count counts PROPOSALS, not rows — the case where the two diverge.

    A non-proposal suspend (the ``human_task`` / empty-watch-set shape) can hold rows
    in ``output_set`` while holding nothing decidable. Recording ``len(output_set)``
    as "proposal_count" would state a non-zero number of proposals for a gate that has
    none. Both numbers are asserted together here because the claim IS their
    divergence: 0 proposals beside 2 rows.
    """
    procedure = _procedure("cnd-nonproposal")
    await _seed_parked(
        db_engine,
        "cnd-12",
        "cnd-nonproposal",
        artifact={"output_set": [{"id": "r1"}, {"id": "r2"}]},
    )
    await _continue(db_engine, procedure, "cnd-12")
    block = (await _step_audit(db_engine, "cnd-12", "aerate"))[NO_DECISION_ACK_KEY]
    assert (block["proposal_count"], block["output_set_size"]) == (0, 2)


async def test_a_concurrent_writer_loses_cleanly(db_engine: AsyncEngine) -> None:
    """The optimistic lock: a stale acknowledger never double-writes run state.

    PLAN-0114 Step 1 names this explicitly. The stale session holds the run at its
    pre-bump version, so it passes every guard on stale data and is refused at COMMIT
    — which is the only place it can be caught.
    """
    procedure = _procedure("cnd-race")
    await _park(db_engine, procedure, "cnd-13")
    maker = async_sessionmaker(db_engine, expire_on_commit=False)

    async with maker() as stale, maker() as winner:
        # KEEP `held` BOUND. SQLAlchemy's identity map holds WEAK references, so
        # dropping this name lets the instance be collected — `load_run`'s select
        # inside the chokepoint then returns FRESH data, the run reads `cancelled`,
        # and the test refuses on the status guard instead of losing at the optimistic
        # lock. Measured s253: removing this binding turned the test green-for-the-
        # wrong-reason into an outright failure. The staleness under test IS this
        # reference.
        held = await stale.get(PipelineRun, "cnd-13")
        assert held is not None
        fresh = await winner.get(PipelineRun, "cnd-13")
        assert fresh is not None
        fresh.status = PipelineRunStatus.CANCELLED.value
        await winner.commit()

        with pytest.raises(StaleDataError):
            await continue_no_decision_run(
                stale,
                procedure,
                _agent(),
                _executors(False, []),
                "cnd-13",
                "aerate",
                vertical="aquaculture",
                actor_person_id=_ACTOR,
            )
        # RELEASE THE LOCKS. A StaleDataError leaves this session's transaction open
        # and holding `pipeline_runs`; without this rollback the fixture's drop_all
        # blocks behind it indefinitely (measured s253 — see the fixture's note). The
        # assertion above is the test; this is the cleanup it cannot skip.
        await stale.rollback()
