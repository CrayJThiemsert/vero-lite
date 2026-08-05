"""PLAN-0096 AC-5 — the E-2 deferred-ratification state machine, full case-coverage matrix.

The component AC-12's rigor standard binds hardest ("we are confident it does what we intend",
not "tests pass"), so this module drives the REAL ``resolve_gated_step`` / ``ratify_gated_step``
over the REAL ``verticals/fleet_maintenance`` hero — its authored ladder, its authored waiver,
its authored principals, its own ``ratification_window_days: 7`` — against a real Postgres
round-trip. Nothing about the gate or the waiver is mocked; the only fakes are the LLM stub the
factory already installs offline and the two ways the window boundary is made addressable
without reading a live clock (CLAUDE.md §8): ``ratify_gated_step`` takes an injected ``now``,
while ``resolve_gated_step`` — which has no such parameter — is driven against a frozen
``tests.clock_support.Clock`` patched over its module's ``datetime``.

Why the fleet hero rather than an inline fixture: the run carries TWO breaches that resolve to
DIFFERENT rungs (฿48,000 → เจ้าของกิจการ, ฿15,000 → ผจก.เดินรถ), so the tier checks below have
something real to discriminate. A single-rung fixture would pass against an implementation that
ignored the ladder entirely.

The matrix, per AC-5:

* **happy** — waiver-invoked provisional resolve → effects execute → ``RESOLVED_PROVISIONAL``
  + the ratification audit block + **no** ``governed_decision`` tie → the owner ratifies inside
  the window → ``RESOLVED`` + the tie, naming the ratifier;
* **boundary** — ``due_at`` is exactly ``decided_at + window_days``; the instant past it reads
  ``overdue`` and is STILL ratifiable; a ``window_days=1`` vertical works;
* **fail-closed** — no authored window ⇒ the branch is unreachable; an unresolvable attested
  approver ⇒ refused; RF-1 on the recorder; an empty justification ⇒ refused;
* **adversarial** — the requester tries to ratify ⇒ SoD block; a lower tier tries ⇒
  tier-authority block; a second ratify ⇒ refused BY STATE; a provisional attempt on a
  non-waiver gate ⇒ refused;
* **refusal** — recorded as a terminal disposition, no tie, and nothing un-executes;
* **resume** — a run advances from ``RESOLVED_PROVISIONAL`` exactly as from ``RESOLVED``, and
  the obligation survives into the ``complete`` step (ADR-0034 D3(6));
* **concurrency** — a ratify bumps the optimistic lock, so a concurrent stale writer loses with
  ``StaleDataError``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from sqlalchemy.orm.exc import StaleDataError

from services.api.config import settings
from services.db.audit_log import AuditLog
from services.db.base import Base
from services.engine.discovery import discover_and_register
from services.engine.procedures import action_step
from services.engine.procedures.action_step import (
    GateApproverError,
    PrincipalSoDError,
    RatificationError,
    TierAuthorityError,
    WaiverInvocation,
    ratify_gated_step,
    resolve_gated_step,
)
from services.engine.procedures.orchestrator import run_procedure
from services.engine.procedures.persistence import persist_run, resume_run
from services.engine.procedures.ratification import RATIFICATION_KEY, ratification_state
from services.engine.procedures.runs import PipelineRun, PipelineRunStatus, StepResultStatus
from services.engine.procedures.spec import (
    Agent,
    DoaLadder,
    Person,
    Procedure,
    load_procedures,
)
from services.engine.registry import ExecutorFactory, registry
from tests.clock_support import Clock, utc
from tests.db_support import create_test_engine
from verticals.fleet_maintenance.procedures_factory import (
    register_fleet_maintenance_procedure_executors,
)

_VERTICAL = "fleet_maintenance"
_PROCEDURE_ID = "governed_repair_approval"
_GATE_STEP = "approve"
#: The partner's Q11 reconciliation window, as authored in the shipped YAML.
_AUTHORED_WINDOW_DAYS = 7
_OWNER = "appr-owner"
_FLEET_MANAGER = "appr-fleet-manager-wirat"
_MECHANIC = "req-mechanic-tom"
_OWNER_ROLE = "เจ้าของกิจการ"


# --------------------------------------------------------------------------- #
# Fixtures + helpers
# --------------------------------------------------------------------------- #


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
async def fleet_factory(monkeypatch: pytest.MonkeyPatch) -> ExecutorFactory:
    """The registered fleet factory — the same path ``services/api/main.py`` runs at startup."""
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    return registry.get_procedure_executors(_VERTICAL)


def _hero(procedure_id: str = _PROCEDURE_ID) -> Procedure:
    return next(p for p in load_procedures(_VERTICAL).procedures if p.procedure_id == procedure_id)


def _agent(proc: Procedure) -> Agent:
    return next(a for a in load_procedures(_VERTICAL).agents if a.agent_id == proc.run_by)


def _principals() -> list[Person]:
    return list(load_procedures(_VERTICAL).principals)


def _person(person_id: str) -> Person:
    return next(p for p in _principals() if p.person_id == person_id)


def _ladder(proc: Procedure) -> DoaLadder:
    ladder = next(s.governance_content for s in proc.steps if s.step_id == _GATE_STEP)
    assert isinstance(ladder, DoaLadder)
    return ladder


def _reauthored_window(days: int | None) -> Procedure:
    """A DEEP COPY of the hero whose waiver authors a different window (or none).

    Re-authoring the vertical's config is the honest way to exercise the entry condition — the
    alternative would be patching the gate under test, which AC-5's own oracle rule rejects. The
    copy matters twice over: ``load_procedures`` hands back a shared spec, and the run's
    governance pin is taken from whatever procedure the run was STARTED with, so each arm must
    both run and resolve through the same re-authored object or the pin fails first and the test
    would be measuring the pin rather than the window."""
    proc = _hero().model_copy(deep=True)
    _ladder(proc).emergency_waiver.ratification_window_days = days
    return proc


async def _run_to_gate(
    db_engine: AsyncEngine,
    factory: ExecutorFactory,
    run_id: str,
    *,
    procedure: Procedure | None = None,
) -> tuple[Procedure, list[str]]:
    """Run the hero to its ``waiting_human`` suspend at ``approve``, persist, return action ids.

    The requester principal is threaded through ``run_procedure`` deliberately: it is what makes
    the orchestrator record ``PipelineRun.step_principals``, and without that half the live SoD
    check at the gate fails closed on an unresolved requester — a headless run cannot be
    approved, provisionally or otherwise."""
    proc = procedure if procedure is not None else _hero()
    result = await run_procedure(
        proc,
        _agent(proc),
        factory(),
        vertical=_VERTICAL,
        run_id=run_id,
        principal=_person(_MECHANIC),
    )
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        await persist_run(session, result)
    gate = next(s for s in result.step_results if s.step_id == _GATE_STEP)
    proposals = (gate.artifact or {})["output_set"]
    assert len(proposals) == 2, "the two-rung run is what gives the tier checks something to bite"
    return proc, [str(p["action_id"]) for p in proposals]


async def _resolve_provisionally(
    db_engine: AsyncEngine,
    run_id: str,
    proc: Procedure,
    action_ids: list[str],
    *,
    recorder: Person | None = None,
    justification: str = "รถเสียหน้างาน โทรหาเฮียแล้วเคาะมาว่าให้ซ่อมเลย",
    step_id: str = _GATE_STEP,
) -> Any:
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        return await resolve_gated_step(
            session,
            run_id,
            step_id,
            dict.fromkeys(action_ids, "approve"),
            recorder if recorder is not None else _person(_MECHANIC),
            procedure=proc,
            principals=_principals(),
            waiver_invocation=WaiverInvocation(justification=justification),
        )


async def _ratify(
    db_engine: AsyncEngine,
    run_id: str,
    proc: Procedure,
    *,
    principal: Person,
    decision: str = "ratify",
    now: datetime | None = None,
    step_id: str = _GATE_STEP,
) -> Any:
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        return await ratify_gated_step(
            session,
            run_id,
            step_id,
            principal,
            decision=decision,  # type: ignore[arg-type]
            procedure=proc,
            principals=_principals(),
            now=now,
        )


async def _audit_actions(db_engine: AsyncEngine, run_id: str) -> list[str]:
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        rows = await session.execute(
            sa.select(AuditLog.action).where(AuditLog.run_id == run_id).order_by(AuditLog.audit_id)
        )
        return list(rows.scalars().all())


# --------------------------------------------------------------------------- #
# HAPPY — the roadside round trip
# --------------------------------------------------------------------------- #


async def test_provisional_resolve_executes_effects_and_withholds_the_tie(
    db_engine: AsyncEngine, fleet_factory: ExecutorFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-5 happy, first half: the record says a decision was made, and is honest about who has
    NOT yet acted.

    Everything that makes this useful is asserted together, because the value is in the
    combination: the effects DID execute (the truck gets fixed — deferring that is the whole
    point), the step is ``RESOLVED_PROVISIONAL`` rather than ``RESOLVED``, the obligation is
    on the audit with the owner named as the ATTESTED authority and the mechanic as the
    recorder, and there is **no** ``governed_decision`` tie. That last one is the load-bearing
    absence: a tie here would assert the owner acted in-system when all he did was answer a
    phone (PLAN-0075 SD-6(a))."""
    proc, action_ids = await _run_to_gate(db_engine, fleet_factory, "rat-happy")
    # ``resolve_gated_step`` takes no ``now=`` (unlike its ``ratify`` sibling), so the
    # deadline was previously bracketed between two wall-clock reads. Under WSL2 that
    # clock steps BACKWARDS — measured in PLAN-0099 at ~0.067/s, and observed here as a
    # ``due_at`` landing 1.69 s BEFORE the ``before`` that precedes it in program order.
    # The bracket was never the property under test: what this asserts is that the
    # deadline is exactly one authored window past the decision instant.
    clock = Clock(utc())
    monkeypatch.setattr(action_step, "datetime", clock.datetime_class())
    target = await _resolve_provisionally(db_engine, "rat-happy", proc, action_ids)

    assert target.status == StepResultStatus.RESOLVED_PROVISIONAL.value
    assert len(target.artifact["output_set"]) == 2, "the approved effects executed"
    assert all(e["receipt"] is not None for e in target.artifact["output_set"])

    assert "governed_decision" not in (
        target.audit or {}
    ), "the audit-to-control tie must NOT exist yet — the attested authority has not acted"
    block = target.audit[RATIFICATION_KEY]
    assert block["attested_approver_id"] == _OWNER
    assert block["recorded_by"] == _MECHANIC
    assert block["ratify_by_role"] == _OWNER_ROLE
    assert block["justification_ref"], "the obligation must point at its stated reason"

    assert clock.calls, (
        "fixture precondition: the patched clock was never read, so the equality below "
        "would hold for any implementation — the patch missed its target module"
    )
    due_at = datetime.fromisoformat(block["due_at"])
    assert due_at == clock.now_value + timedelta(days=_AUTHORED_WINDOW_DAYS)

    view = ratification_state(target.audit, clock.now_value)
    assert view.state == "pending"
    assert view.is_outstanding


async def test_justification_is_durably_audited_and_referenced_by_the_obligation(
    db_engine: AsyncEngine, fleet_factory: ExecutorFactory
) -> None:
    """AC-5 happy: the run-time justification the waiver forces is not a field that evaporates.

    It lands in the tamper-evident audit chain, and the obligation's ``justification_ref`` is
    that row's ``row_hash`` — so "why did we spend this before anyone signed?" is answerable from
    the record months later, which is precisely the audit question the 1-KPI charter is about."""
    proc, action_ids = await _run_to_gate(db_engine, fleet_factory, "rat-just")
    reason = "ยางระเบิดที่สระบุรี เฮียสั่งทางโทรศัพท์ให้ซ่อมก่อน"
    target = await _resolve_provisionally(
        db_engine, "rat-just", proc, action_ids, justification=reason
    )

    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        row = (
            await session.execute(
                sa.select(AuditLog).where(
                    AuditLog.row_hash == target.audit[RATIFICATION_KEY]["justification_ref"]
                )
            )
        ).scalar_one()
    assert row.action == "gate_decision"
    assert row.payload["kind"] == "provisional"
    assert row.payload["justification"] == reason
    assert row.actor_person_id == _MECHANIC, "the audit names who ACTED, not who was attested"


async def test_ratify_within_window_resolves_and_emits_the_tie_naming_the_ratifier(
    db_engine: AsyncEngine, fleet_factory: ExecutorFactory
) -> None:
    """AC-5 happy, second half: the record catches up.

    The step reaches ``RESOLVED``, the obligation reads ``ratified``, and the
    ``governed_decision`` tie appears NOW — naming the owner, who by then really has acted. The
    tie's timing is the entire contract: emitted at the moment authority is exercised in-system,
    never before (ADR-0034 D3(3))."""
    proc, action_ids = await _run_to_gate(db_engine, fleet_factory, "rat-ok")
    await _resolve_provisionally(db_engine, "rat-ok", proc, action_ids)

    target = await _ratify(db_engine, "rat-ok", proc, principal=_person(_OWNER))

    assert target.status == StepResultStatus.RESOLVED.value
    block = target.audit[RATIFICATION_KEY]
    assert block["ratified_by"] == _OWNER
    assert block["attested_approver_id"] == _OWNER, "the attestation record survives ratification"
    assert ratification_state(target.audit, datetime.now(UTC)).state == "ratified"

    ties = target.audit["governed_decision"]
    assert ties, "the withheld tie must be emitted at ratification"
    assert {t["principal_id"] for t in ties} == {_OWNER}
    assert {t["control_ref"]["kind"] for t in ties} == {"sod", "doa_tier"}

    assert "gate_ratified" in await _audit_actions(db_engine, "rat-ok")


# --------------------------------------------------------------------------- #
# BOUNDARY — the window's edges
# --------------------------------------------------------------------------- #


async def test_overdue_at_the_instant_past_due_and_still_ratifiable(
    db_engine: AsyncEngine, fleet_factory: ExecutorFactory
) -> None:
    """AC-5 boundary: ``due_at`` itself is not yet overdue; a microsecond later is. And overdue
    is urgency, NOT expiry — the signature is still owed, so a late ratification must succeed.

    Refusing it would strand exactly the cases that most need clearing, and would also invent a
    terminal state no principal ever performed (ADR-0034 Alt-3, D3(6))."""
    proc, action_ids = await _run_to_gate(db_engine, fleet_factory, "rat-late")
    target = await _resolve_provisionally(db_engine, "rat-late", proc, action_ids)
    due_at = datetime.fromisoformat(target.audit[RATIFICATION_KEY]["due_at"])

    assert ratification_state(target.audit, due_at).state == "pending"
    assert ratification_state(target.audit, due_at + timedelta(microseconds=1)).state == "overdue"

    late = due_at + timedelta(days=30)
    ratified = await _ratify(db_engine, "rat-late", proc, principal=_person(_OWNER), now=late)
    assert ratified.status == StepResultStatus.RESOLVED.value
    assert ratification_state(ratified.audit, late).state == "ratified"

    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        row = (
            await session.execute(
                sa.select(AuditLog).where(
                    AuditLog.run_id == "rat-late", AuditLog.action == "gate_ratified"
                )
            )
        ).scalar_one()
    assert row.payload["was_overdue"] is True, "lateness must be recorded, not silently absorbed"


async def test_minimum_authored_window_of_one_day(
    db_engine: AsyncEngine, fleet_factory: ExecutorFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-5 boundary: ``ge=1`` is the floor, and a vertical that authors it gets a one-day
    deadline computed through the same helper — no off-by-one, no special case.

    Asserted as an EQUALITY against a frozen clock. The previous form allowed anything in
    ``(23h, 24h]``, which is a whole hour of slack in a test whose stated subject is an
    off-by-one — and its upper bound was a zero-margin wall-clock read that a backward
    step alone could redden."""
    proc = _reauthored_window(1)
    _, action_ids = await _run_to_gate(db_engine, fleet_factory, "rat-one", procedure=proc)
    clock = Clock(utc())
    monkeypatch.setattr(action_step, "datetime", clock.datetime_class())
    target = await _resolve_provisionally(db_engine, "rat-one", proc, action_ids)

    assert clock.calls, "fixture precondition: the patched clock was never read"
    block = target.audit[RATIFICATION_KEY]
    due_at = datetime.fromisoformat(block["due_at"])
    assert due_at == clock.now_value + timedelta(days=1)


# --------------------------------------------------------------------------- #
# FAIL-CLOSED — the branch must be unreachable where the ADR says it is
# --------------------------------------------------------------------------- #


async def test_no_authored_window_makes_the_provisional_branch_unreachable(
    db_engine: AsyncEngine, fleet_factory: ExecutorFactory
) -> None:
    """AC-5 fail-closed: without an authored window there is no bound on the catch-up, so
    decide-first is not representable — and the refusal is LOUD.

    Silently falling back to an ordinary firsthand resolution would be the worst outcome
    available: it would record the recorder as having approved a spend at a tier they may not
    hold, from a caller that explicitly said they were only relaying someone else's decision."""
    proc = _reauthored_window(None)
    _, action_ids = await _run_to_gate(db_engine, fleet_factory, "rat-nowin", procedure=proc)

    with pytest.raises(RatificationError, match="authors no ratification_window_days"):
        await _resolve_provisionally(db_engine, "rat-nowin", proc, action_ids)

    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        run = await session.get(PipelineRun, "rat-nowin")
        assert run is not None
        step = (
            await session.execute(
                sa.text(
                    "SELECT status FROM step_results WHERE run_id = :r AND step_id = :s"
                ).bindparams(r="rat-nowin", s=_GATE_STEP)
            )
        ).scalar_one()
    assert step == StepResultStatus.WAITING_HUMAN.value, "nothing may have been decided"


async def test_unresolvable_attested_approver_refuses(
    db_engine: AsyncEngine, fleet_factory: ExecutorFactory
) -> None:
    """AC-5 fail-closed: if the waiver's ``escalate_to`` role resolves to no declared Person,
    there is nobody the attestation could be ABOUT — so the path refuses rather than recording
    an attestation naming nobody."""
    proc, action_ids = await _run_to_gate(db_engine, fleet_factory, "rat-noattest")
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    without_owner = [p for p in _principals() if p.person_id != _OWNER]

    async with maker() as session:
        with pytest.raises(RatificationError, match="resolves to no declared Person"):
            await resolve_gated_step(
                session,
                "rat-noattest",
                _GATE_STEP,
                dict.fromkeys(action_ids, "approve"),
                _person(_MECHANIC),
                procedure=proc,
                principals=without_owner,
                waiver_invocation=WaiverInvocation(justification="เฮียเคาะทางโทรศัพท์"),
            )


async def test_rf1_the_recorder_must_be_an_identified_human(
    db_engine: AsyncEngine, fleet_factory: ExecutorFactory
) -> None:
    """AC-5 fail-closed: RF-1 binds to the RECORDER. Deferring whose signature is owed never
    defers the requirement that a named human filed the record."""
    proc, action_ids = await _run_to_gate(db_engine, fleet_factory, "rat-rf1")
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        with pytest.raises(GateApproverError):
            await resolve_gated_step(
                session,
                "rat-rf1",
                _GATE_STEP,
                dict.fromkeys(action_ids, "approve"),
                None,
                procedure=proc,
                principals=_principals(),
                waiver_invocation=WaiverInvocation(justification="เฮียเคาะแล้ว"),
            )


def test_empty_justification_is_refused_at_construction() -> None:
    """AC-5 fail-closed: the waiver's ``requires_justification`` is ``Literal[True]``, so an
    invocation carrying only whitespace is refused before it can reach a gate at all."""
    with pytest.raises(RatificationError, match="non-empty run-time justification"):
        WaiverInvocation(justification="   ")


# --------------------------------------------------------------------------- #
# ADVERSARIAL — the ways someone would try to get a spend past the rule
# --------------------------------------------------------------------------- #


async def test_requester_cannot_ratify_his_own_claim(
    db_engine: AsyncEngine, fleet_factory: ExecutorFactory
) -> None:
    """AC-5 adversarial: the partner's กฎเหล็ก survives the deferral. The mechanic who filed the
    claim may RECORD the owner's phone decision, but he can never be the one who signs it off —
    the live SoD check binds the ratifier exactly as it binds a firsthand approver."""
    proc, action_ids = await _run_to_gate(db_engine, fleet_factory, "rat-selfsign")
    await _resolve_provisionally(db_engine, "rat-selfsign", proc, action_ids)

    with pytest.raises(PrincipalSoDError):
        await _ratify(db_engine, "rat-selfsign", proc, principal=_person(_MECHANIC))

    assert "gate_refused" in await _audit_actions(db_engine, "rat-selfsign")


async def test_lower_tier_cannot_ratify_what_the_waiver_escalated(
    db_engine: AsyncEngine, fleet_factory: ExecutorFactory
) -> None:
    """AC-5 adversarial: วิรัช holds ``approver`` and clears SoD, so only the tier check stands
    between him and signing off a decision the waiver escalated to the OWNER. He does not hold
    ``เจ้าของกิจการ``, so it blocks.

    This is the case that would quietly rot if ``ratify_by_role`` were never enforced: the SoD
    check alone would let any approver ratify anything."""
    proc, action_ids = await _run_to_gate(db_engine, fleet_factory, "rat-lowtier")
    await _resolve_provisionally(db_engine, "rat-lowtier", proc, action_ids)

    with pytest.raises(TierAuthorityError, match=_OWNER_ROLE):
        await _ratify(db_engine, "rat-lowtier", proc, principal=_person(_FLEET_MANAGER))

    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        row = (
            await session.execute(
                sa.select(AuditLog).where(
                    AuditLog.run_id == "rat-lowtier", AuditLog.action == "gate_refused"
                )
            )
        ).scalar_one()
    assert row.payload["kind"] == "ratification_authority"
    assert row.actor_person_id == _FLEET_MANAGER


async def test_second_ratification_is_refused_by_state(
    db_engine: AsyncEngine, fleet_factory: ExecutorFactory
) -> None:
    """AC-5 adversarial: idempotent BY STATE. The second attempt finds the obligation already
    settled and is refused — not because the caller was disciplined, but because there is
    nothing outstanding left to sign."""
    proc, action_ids = await _run_to_gate(db_engine, fleet_factory, "rat-twice")
    await _resolve_provisionally(db_engine, "rat-twice", proc, action_ids)
    await _ratify(db_engine, "rat-twice", proc, principal=_person(_OWNER))

    with pytest.raises(RatificationError, match="no outstanding ratification obligation"):
        await _ratify(db_engine, "rat-twice", proc, principal=_person(_OWNER))


async def test_ratify_on_a_step_that_was_never_provisional_is_refused(
    db_engine: AsyncEngine, fleet_factory: ExecutorFactory
) -> None:
    """AC-5 adversarial: an ordinary firsthand resolution carries no obligation, so it cannot be
    'ratified' into anything. Conflating "already fully governed" with "not yet ratified" would
    make every normal approval look like an outstanding exception on the export."""
    proc, action_ids = await _run_to_gate(db_engine, fleet_factory, "rat-plain")
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        resolved = await resolve_gated_step(
            session,
            "rat-plain",
            _GATE_STEP,
            dict.fromkeys(action_ids, "approve"),
            _person(_OWNER),
            procedure=proc,
            principals=_principals(),
        )
    assert resolved.status == StepResultStatus.RESOLVED.value
    assert RATIFICATION_KEY not in (resolved.audit or {})
    assert resolved.audit["governed_decision"], "the ordinary path still ties at gate time"

    with pytest.raises(RatificationError, match="state 'none'"):
        await _ratify(db_engine, "rat-plain", proc, principal=_person(_OWNER))


async def test_provisional_attempt_on_a_non_waiver_gate_is_refused(
    db_engine: AsyncEngine, fleet_factory: ExecutorFactory
) -> None:
    """AC-5 adversarial: ``fulfill`` is gated but carries no DOA ladder and therefore no waiver.
    A provisional invocation there has no authored window to stand on, and is refused — the
    decide-first path can never be reached by pointing it at a different gate."""
    proc, action_ids = await _run_to_gate(db_engine, fleet_factory, "rat-nonwaiver")
    await _resolve_provisionally(db_engine, "rat-nonwaiver", proc, action_ids)
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        await resume_run(
            session, proc, _agent(proc), fleet_factory(), "rat-nonwaiver", vertical=_VERTICAL
        )

    async with maker() as session:
        run = await session.get(PipelineRun, "rat-nonwaiver")
        assert run is not None and run.status == PipelineRunStatus.WAITING_HUMAN.value
        rows = (
            await session.execute(
                sa.text(
                    "SELECT artifact FROM step_results WHERE run_id = :r AND step_id = 'fulfill'"
                ).bindparams(r="rat-nonwaiver")
            )
        ).scalar_one()
    fulfil_ids = [str(p["action_id"]) for p in rows["output_set"]]

    with pytest.raises(RatificationError, match="not a DOA-ladder gate"):
        await _resolve_provisionally(
            db_engine, "rat-nonwaiver", proc, fulfil_ids, step_id="fulfill"
        )


# --------------------------------------------------------------------------- #
# REFUSAL — the honest opposite of a signature
# --------------------------------------------------------------------------- #


async def test_refusal_records_a_terminal_disposition_and_un_executes_nothing(
    db_engine: AsyncEngine, fleet_factory: ExecutorFactory
) -> None:
    """AC-5 refusal (ADR-0034 D3(4)): the owner declines to stand behind the decision.

    Three things must hold together, and each is a deliberate design choice rather than a
    convenience: the disposition is recorded as terminal, **no** ``governed_decision`` tie is
    emitted (a refusal is the assertion that this authority did NOT govern the spend), and the
    executed effects are untouched — the money is already spent, so fail-closed is not on the
    menu and the honest response is to make the exception VISIBLE."""
    proc, action_ids = await _run_to_gate(db_engine, fleet_factory, "rat-refuse")
    provisional = await _resolve_provisionally(db_engine, "rat-refuse", proc, action_ids)
    effects_before = provisional.artifact["output_set"]

    target = await _ratify(
        db_engine, "rat-refuse", proc, principal=_person(_OWNER), decision="refuse"
    )

    block = target.audit[RATIFICATION_KEY]
    assert block["refused_by"] == _OWNER
    assert "ratified_by" not in block
    assert ratification_state(target.audit, datetime.now(UTC)).state == "refused"
    assert "governed_decision" not in (
        target.audit or {}
    ), "a refusal must NOT tie the refuser to the control — they declined to govern it"
    assert target.artifact["output_set"] == effects_before, "nothing un-executes on a refusal"
    assert "ratification_refused" in await _audit_actions(db_engine, "rat-refuse")


async def test_a_refused_obligation_cannot_be_ratified_afterwards(
    db_engine: AsyncEngine, fleet_factory: ExecutorFactory
) -> None:
    """AC-5 refusal: refusal is TERMINAL. Allowing a later ratify to overwrite it would let the
    record be walked back to a happier answer after the fact."""
    proc, action_ids = await _run_to_gate(db_engine, fleet_factory, "rat-refuse2")
    await _resolve_provisionally(db_engine, "rat-refuse2", proc, action_ids)
    await _ratify(db_engine, "rat-refuse2", proc, principal=_person(_OWNER), decision="refuse")

    with pytest.raises(RatificationError, match="state 'refused'"):
        await _ratify(db_engine, "rat-refuse2", proc, principal=_person(_OWNER))


# --------------------------------------------------------------------------- #
# RESUME — ADR-0034 D3(5) and D3(6)
# --------------------------------------------------------------------------- #


async def test_resume_advances_from_resolved_provisional(
    db_engine: AsyncEngine, fleet_factory: ExecutorFactory
) -> None:
    """AC-5 / ADR-0034 D3(5): the run advances on a provisional resolution exactly as on a
    firsthand one. Holding the run hostage to a signature that is days out is the precise
    behaviour decide-first exists to avoid — the truck is already being repaired."""
    proc, action_ids = await _run_to_gate(db_engine, fleet_factory, "rat-resume")
    await _resolve_provisionally(db_engine, "rat-resume", proc, action_ids)

    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        resumed = await resume_run(
            session, proc, _agent(proc), fleet_factory(), "rat-resume", vertical=_VERTICAL
        )
    by_step = {s.step_id: s for s in resumed.step_results}
    assert by_step[_GATE_STEP].status == StepResultStatus.COMPLETE.value
    assert "fulfill" in by_step, "the run moved on to the next step"


async def test_the_obligation_survives_resume_and_is_ratifiable_afterwards(
    db_engine: AsyncEngine, fleet_factory: ExecutorFactory
) -> None:
    """ADR-0034 D3(6), and the reason the precondition is the OBLIGATION rather than the step
    status (Cray, typed pick, session 187).

    ``resume_run`` marks every advanced step ``complete``, and in this hero the step after the
    gate is itself gated — so the run ALWAYS moves past ``approve`` within minutes while the
    authored window is seven days. A status-keyed precondition would therefore make the owner's
    signature impossible in exactly the flow the window exists for. The obligation rides the
    step audit instead, stays queryable on an advanced run, and can still be settled.

    Note the step keeps its ``complete`` status through ratification: moving it back to
    ``resolved`` would re-enter it into the unresumed set and make a finished step look like the
    one the run is suspended at."""
    proc, action_ids = await _run_to_gate(db_engine, fleet_factory, "rat-after")
    await _resolve_provisionally(db_engine, "rat-after", proc, action_ids)
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        await resume_run(
            session, proc, _agent(proc), fleet_factory(), "rat-after", vertical=_VERTICAL
        )

    target = await _ratify(db_engine, "rat-after", proc, principal=_person(_OWNER))

    assert (
        target.status == StepResultStatus.COMPLETE.value
    ), "an advanced step must NOT be walked back to 'resolved' by a ratification"
    assert ratification_state(target.audit, datetime.now(UTC)).state == "ratified"
    assert {t["principal_id"] for t in target.audit["governed_decision"]} == {_OWNER}


# --------------------------------------------------------------------------- #
# CONCURRENCY
# --------------------------------------------------------------------------- #


async def test_ratification_bumps_the_optimistic_lock_so_a_stale_writer_loses(
    db_engine: AsyncEngine, fleet_factory: ExecutorFactory
) -> None:
    """AC-5 concurrency: a ratify is a run-state write, so it participates in the
    ``pipeline_runs.version`` lock — a concurrent writer holding a pre-ratification snapshot
    loses cleanly with ``StaleDataError`` instead of silently overwriting the settled record."""
    proc, action_ids = await _run_to_gate(db_engine, fleet_factory, "rat-race")
    await _resolve_provisionally(db_engine, "rat-race", proc, action_ids)

    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as stale:
        snapshot = await stale.get(PipelineRun, "rat-race")
        assert snapshot is not None

        await _ratify(db_engine, "rat-race", proc, principal=_person(_OWNER))

        snapshot.status = PipelineRunStatus.CANCELLED.value
        with pytest.raises(StaleDataError):
            await stale.commit()
