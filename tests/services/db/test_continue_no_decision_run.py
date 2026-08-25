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
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    now = datetime.now(UTC)
    async with maker() as session:
        session.add(
            PipelineRun(
                run_id="cnd-3",
                procedure_id="cnd-escalated",
                agent_id="pond_agent",
                status=PipelineRunStatus.WAITING_HUMAN.value,
                started_at=now,
                updated_at=now,
            )
        )
        session.add(
            StepResult(
                step_result_id="cnd-3:aerate",
                run_id="cnd-3",
                step_id="aerate",
                status=StepResultStatus.WAITING_HUMAN.value,
                artifact=None,
                created_at=now,
            )
        )
        await session.commit()

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


async def test_the_step_block_records_the_acknowledging_human(db_engine: AsyncEngine) -> None:
    """SD-2 level 2: the readable half, on the gate step's own audit dict."""
    procedure = _procedure("cnd-block")
    await _park(db_engine, procedure, "cnd-8")
    await _continue(db_engine, procedure, "cnd-8")
    block = (await _step_audit(db_engine, "cnd-8", "aerate"))[NO_DECISION_ACK_KEY]
    assert block["acknowledged_by"] == _ACTOR


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
