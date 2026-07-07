"""Deploy-time wiring for the scheduler daemon (PLAN-0055 Step 7 — the ops posture).

Connects a REAL vertical spec to the pure Step-4 fire function + the Step-5 daemon. The daemon
holds none of this — it drives :func:`fire_due_schedules` through the resolver these build.

* :func:`sync_schedule_states` — the REGISTRATION step. Reads the loaded vertical spec, selects
  its ``schedule``-trigger procedures, and upserts one :class:`ScheduleState` per
  ``(vertical, procedure_id)`` from each ``Procedure.schedule`` (cron + tz). Closes the gap
  where nothing populated ``schedule_states`` in production (tests seeded rows directly). The
  spec is the source of truth for cron/tz; the live clock (``last_fired``/``next_fire``) is the
  daemon's and is preserved across a re-sync.
* :func:`build_resolver` — the REAL :data:`ScheduleResolver`. Reproduces the HTTP run-path
  assembly (procedure by id + its ``run_by`` agent + a fresh executor map from the registry
  factory) and adds the ``ServicePrincipal`` lookup a scheduled run needs (the service actor,
  SP-4/5).

Injected-spec by design: both take an already-loaded :class:`VerticalProcedures` (not a vertical
name) so they are unit-testable with an in-memory spec — no disk fixture, no CWD dependency. The
CLI (``vero-lite scheduler``) loads the spec once, registers the vertical's executor factory,
calls :func:`sync_schedule_states`, then runs the daemon with :func:`build_resolver`.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from services.engine.procedures.scheduler import ScheduledRun, ScheduleResolver
from services.engine.procedures.schedules import ScheduleState
from services.engine.procedures.spec import (
    Agent,
    Person,
    Procedure,
    ServicePrincipal,
    Trigger,
    VerticalProcedures,
)
from services.engine.registry import ExecutorFactory


class SchedulerWiringError(Exception):
    """Raised when a schedule cannot be resolved into a runnable — a spec misconfiguration
    (procedure/agent/service-principal absent). Surfaces at fire time via the daemon's
    tick-failure isolation, not silently."""


def schedule_id_for(vertical: str, procedure_id: str) -> str:
    """The deterministic schedule identity ``"<vertical>:<procedure_id>"`` — unique per
    ``(vertical, procedure_id)`` (matches the ``schedule_states`` unique constraint)."""
    return f"{vertical}:{procedure_id}"


def schedule_procedures(spec: VerticalProcedures) -> list[Procedure]:
    """Every ``schedule``-trigger procedure in ``spec`` (the set the daemon drives)."""
    return [p for p in spec.procedures if p.trigger is Trigger.SCHEDULE]


async def sync_schedule_states(
    session: AsyncSession, spec: VerticalProcedures, *, now: datetime | None = None
) -> list[ScheduleState]:
    """Upsert a :class:`ScheduleState` per ``schedule``-trigger procedure in ``spec`` (the
    registration step). Returns the rows for the vertical's schedules; commits.

    Idempotent — a re-sync updates ``cron``/``timezone`` if the spec changed (dropping the stale
    ``next_fire`` so the next tick recomputes against the new expression) but NEVER resets
    ``last_fired``/``next_fire`` otherwise (the daemon owns the live clock). A new row starts
    with ``next_fire=None`` so the daemon's first tick computes it WITHOUT firing (INITIALIZED —
    the first fire is a future slot). ``now`` is injectable for deterministic tests.

    Note: this is upsert-only — it does not delete rows for procedures removed from the spec
    (an orphan row would fail to resolve at fire time; clean it up manually / defer to a future
    reconcile step).
    """
    stamp = now if now is not None else datetime.now(UTC)
    vertical = spec.vertical
    rows: list[ScheduleState] = []
    for proc in schedule_procedures(spec):
        # invariant (spec load): trigger==schedule => the descriptor is present.
        assert proc.schedule is not None
        sid = schedule_id_for(vertical, proc.procedure_id)
        existing = await session.get(ScheduleState, sid)
        if existing is None:
            row = ScheduleState(
                schedule_id=sid,
                vertical=vertical,
                procedure_id=proc.procedure_id,
                cron=proc.schedule.cron,
                timezone=proc.schedule.timezone,
                last_fired=None,
                next_fire=None,
                created_at=stamp,
                updated_at=stamp,
            )
            session.add(row)
            rows.append(row)
        else:
            if existing.cron != proc.schedule.cron or existing.timezone != proc.schedule.timezone:
                existing.cron = proc.schedule.cron
                existing.timezone = proc.schedule.timezone
                existing.next_fire = None  # recompute against the new cron next tick
                existing.updated_at = stamp
            rows.append(existing)
    await session.commit()
    return rows


def _find_procedure(spec: VerticalProcedures, procedure_id: str) -> Procedure:
    proc = next((p for p in spec.procedures if p.procedure_id == procedure_id), None)
    if proc is None:
        raise SchedulerWiringError(
            f"vertical '{spec.vertical}': no procedure '{procedure_id}' in spec"
        )
    return proc


def _find_agent(spec: VerticalProcedures, procedure: Procedure) -> Agent:
    agent = next((a for a in spec.agents if a.agent_id == procedure.run_by), None)
    if agent is None:
        raise SchedulerWiringError(
            f"vertical '{spec.vertical}': procedure '{procedure.procedure_id}' is run_by unknown "
            f"agent '{procedure.run_by}'"
        )
    return agent


def _resolve_service_principal(spec: VerticalProcedures, agent: Agent) -> ServicePrincipal:
    """The service actor a scheduled run acts as (SP-4). Uses the agent's FIRST declared
    ``service_principal_id`` (an agent typically declares one; a multi-SP agent uses the first
    for scheduled runs — a future refinement could let the schedule pick)."""
    if not agent.service_principal_ids:
        raise SchedulerWiringError(
            f"vertical '{spec.vertical}': agent '{agent.agent_id}' declares no "
            "service_principal_ids — a scheduled run needs a service actor (SP-4)"
        )
    sp_id = agent.service_principal_ids[0]
    sp = next((s for s in spec.service_principals if s.service_principal_id == sp_id), None)
    if sp is None:  # unreachable for a validated spec (cross-ref checked at load) — defensive
        raise SchedulerWiringError(
            f"vertical '{spec.vertical}': agent '{agent.agent_id}' service_principal_id "
            f"'{sp_id}' is not in spec.service_principals"
        )
    return sp


def _resolve_owning_person(spec: VerticalProcedures, procedure: Procedure) -> Person | None:
    """The SP-5 human a headless scheduled run acts ON BEHALF OF (PLAN-0055 Step 8), resolved from
    ``procedure.schedule.owning_person_id`` (cross-ref validated at load). Recorded as the run's
    SoD requester so a distinct downstream human approver satisfies separation of duties. ``None``
    when the schedule declares no owning person — a fully headless run (valid only for a procedure
    with no SoD requester to resolve; a ``doa_tier`` procedure requires SoD, ADR-0025 D5)."""
    oref = procedure.schedule.owning_person_id if procedure.schedule is not None else None
    if oref is None:
        return None
    person = next((p for p in spec.principals if p.person_id == oref), None)
    if person is None:  # unreachable for a validated spec (cross-ref checked at load) — defensive
        raise SchedulerWiringError(
            f"vertical '{spec.vertical}': procedure '{procedure.procedure_id}' "
            f"schedule.owning_person_id '{oref}' is not in spec.principals"
        )
    return person


def build_resolver(spec: VerticalProcedures, executor_factory: ExecutorFactory) -> ScheduleResolver:
    """Build the REAL resolver: a :class:`ScheduleState` -> :class:`ScheduledRun` mirroring the
    HTTP run-path assembly plus the service-principal lookup a scheduled run needs, and (PLAN-0055
    Step 8) the SP-5 owning-person lookup a SoD-carrying scheduled procedure needs.

    ``executor_factory`` is the vertical's registered factory
    (``registry.get_procedure_executors(vertical)``) — called fresh per fire so stateful
    executors never leak across runs. The resolver is called ONLY on the fire path (never for a
    not-due / skipped schedule), so a missing-procedure misconfiguration surfaces only when a
    run would actually start.
    """
    vertical = spec.vertical

    def resolve(state: ScheduleState) -> ScheduledRun:
        procedure = _find_procedure(spec, state.procedure_id)
        agent = _find_agent(spec, procedure)
        service_principal = _resolve_service_principal(spec, agent)
        return ScheduledRun(
            procedure=procedure,
            agent=agent,
            executors=executor_factory(),
            vertical=vertical,
            service_principal=service_principal,
            # SP-5: the human the service acts on behalf of (the SoD requester), or None if the
            # schedule is fully headless (no SoD to satisfy). PLAN-0055 Step 8 lifted the prior
            # hard-coded None once the procurement demo needed a doa_tier gate (=> SoD => a
            # requester).
            owning_person=_resolve_owning_person(spec, procedure),
        )

    return resolve
