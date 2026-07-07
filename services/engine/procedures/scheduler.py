"""The pure "fire due schedules" function for the S1 scheduler (ADR-0028; PLAN-0055 Step 4).

Given a set of persisted :class:`ScheduleState` rows and an **injected** ``now`` (no
wall-clock read — deterministic + unit-testable, AC-6), decide per schedule whether to
fire, then drive the run through the already-shipped persisted path. This module owns the
scheduling POLICY (the ratified SD-P2/P3/P4/P6 decisions); the Phase-B daemon (Step 5) is
a thin loop that supplies ``now`` + resolves each schedule and calls this — it holds NO
scheduling logic of its own.

Ratified policy (ADR-0028 §157-173, PLAN-0055 SD-P2..P6):

* **SD-P3 skip-if-in-flight** — a schedule whose procedure already has a ``running`` /
  ``waiting_human`` run is skipped this tick (a gated run legitimately parks for days); its
  clock still advances so the daemon does not spin. Emits a ``schedule_skipped`` audit row.
* **SD-P2 skip-with-audit for missed rounds** — after downtime the clock is advanced to the
  next FUTURE slot (no backfill); if intermediate slots elapsed, a ``schedule_missed`` audit
  row records the gap. The due slot itself still fires once (SD-P4 at-most-once).
* **SD-P6 trigger_context** — every fired run is stamped
  ``{trigger, cron, timezone, scheduled_for, fired_at, actor:<service-principal-id>}``.

The service-actor audit (``actor_kind:"service"`` + ``actor_service_principal_id`` +
on-behalf-of lineage, AC-4) and the gated-park posture (AC-5) are inherited verbatim from
:func:`run_procedure_persisted` — S1 is a pure client of the S2 actor plumbing, it rebuilds
none of it.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from services.db.audit_log import append_audit
from services.engine.procedures.cron import next_fire
from services.engine.procedures.orchestrator import StepExecutor
from services.engine.procedures.persistence import run_procedure_persisted
from services.engine.procedures.runs import PipelineRun, PipelineRunStatus
from services.engine.procedures.schedules import ScheduleState
from services.engine.procedures.spec import (
    Agent,
    Person,
    Procedure,
    ServicePrincipal,
    StepKind,
    Trigger,
)

NextFireFn = Callable[[str, str, datetime], datetime]
"""Signature of the cron next-fire calculator (``cron.next_fire``) — injected so a test can
substitute a deterministic clock without importing croniter."""


@dataclass(frozen=True)
class ScheduledRun:
    """Everything needed to fire ONE schedule's run — the daemon resolves a
    :class:`ScheduleState` into this from the loaded vertical spec (procedure by
    ``procedure_id``, its ``run_by`` agent, the executor map, the declared service
    principal). ``owning_person`` is the optional human the service acts on behalf of
    (SP-5 lineage); ``None`` for a headless schedule."""

    procedure: Procedure
    agent: Agent
    executors: Mapping[StepKind, StepExecutor]
    vertical: str
    service_principal: ServicePrincipal
    owning_person: Person | None = None


ScheduleResolver = Callable[[ScheduleState], ScheduledRun]
"""Resolve a due schedule into its runnable inputs. Called ONLY on the fire path (never for
a not-due / skipped schedule), so resolution cost is paid only when a run actually starts."""


class FireResult(StrEnum):
    """The outcome of evaluating one schedule against ``now``."""

    FIRED = "fired"
    SKIPPED_IN_FLIGHT = "skipped_in_flight"
    INITIALIZED = "initialized"
    NOT_DUE = "not_due"


@dataclass(frozen=True)
class FireOutcome:
    """The per-schedule result of one :func:`fire_due_schedules` pass (the return the daemon
    logs). ``missed`` marks a fired slot that also skipped ≥1 elapsed intermediate slot."""

    schedule_id: str
    result: FireResult
    scheduled_for: datetime | None = None
    run_id: str | None = None
    run_status: str | None = None
    missed: bool = False


async def _in_flight(session: AsyncSession, procedure_id: str) -> bool:
    """True iff a prior run of ``procedure_id`` is still ``running`` / ``waiting_human``
    (SD-P3). Scoped by ``procedure_id`` (a run row carries no vertical) — adequate for S1
    where a daemon owns one vertical; a cross-vertical id collision is a documented edge."""
    row = await session.execute(
        sa.select(PipelineRun.run_id)
        .where(
            PipelineRun.procedure_id == procedure_id,
            PipelineRun.status.in_(
                [PipelineRunStatus.RUNNING.value, PipelineRunStatus.WAITING_HUMAN.value]
            ),
        )
        .limit(1)
    )
    return row.scalar_one_or_none() is not None


def _trigger_context(
    state: ScheduleState, scheduled_for: datetime, now: datetime, sp_id: str
) -> dict[str, Any]:
    """The SD-P6 stamp recorded on the fired run (AC-9) — all datetimes ISO strings so the
    JSONB column round-trips them."""
    return {
        "trigger": Trigger.SCHEDULE.value,
        "cron": state.cron,
        "timezone": state.timezone,
        "scheduled_for": scheduled_for.isoformat(),
        "fired_at": now.isoformat(),
        "actor": sp_id,
    }


async def fire_due_schedules(
    session: AsyncSession,
    schedules: Sequence[ScheduleState],
    *,
    now: datetime,
    resolve: ScheduleResolver,
    next_fire_fn: NextFireFn = next_fire,
) -> list[FireOutcome]:
    """Evaluate every schedule against ``now`` and fire the due ones (AC-6).

    Deterministic given ``now`` — no wall-clock read, no ``sleep``, no daemon. Per schedule:

    * ``next_fire is None`` (freshly registered) → compute the first ``next_fire`` and record
      it WITHOUT firing (``INITIALIZED``) — the first fire is a future tick.
    * ``next_fire > now`` → ``NOT_DUE``, untouched.
    * due (``next_fire <= now``) → skip-if-in-flight (SD-P3) else fire once (SD-P4), emitting a
      ``schedule_missed`` audit first if intermediate slots elapsed (SD-P2). Either way the
      clock advances to the next FUTURE slot so the daemon never spins or backfills.

    Commits per schedule (a fire's own write-ahead commits live in ``run_procedure_persisted``;
    an init/skip is committed here) so one schedule's failure never loses another's progress.
    """
    outcomes: list[FireOutcome] = []
    for state in schedules:
        if state.next_fire is None:
            state.next_fire = next_fire_fn(state.cron, state.timezone, now)
            state.updated_at = now
            await session.merge(state)
            await session.commit()
            outcomes.append(FireOutcome(state.schedule_id, FireResult.INITIALIZED))
            continue

        if state.next_fire > now:
            outcomes.append(FireOutcome(state.schedule_id, FireResult.NOT_DUE))
            continue

        scheduled_for = state.next_fire

        # SD-P3 — skip when a prior run of the same procedure is still in flight.
        if await _in_flight(session, state.procedure_id):
            await append_audit(
                session,
                action="schedule_skipped",
                payload={
                    "schedule_id": state.schedule_id,
                    "procedure_id": state.procedure_id,
                    "scheduled_for": scheduled_for.isoformat(),
                    "reason": "in_flight",
                },
            )
            state.next_fire = next_fire_fn(state.cron, state.timezone, now)
            state.updated_at = now
            await session.merge(state)
            await session.commit()
            outcomes.append(
                FireOutcome(state.schedule_id, FireResult.SKIPPED_IN_FLIGHT, scheduled_for)
            )
            continue

        # SD-P2 — a missed round (≥1 slot elapsed AFTER the due slot) is skipped, not
        # backfilled; audit the gap. The due slot itself still fires once (SD-P4).
        following = next_fire_fn(state.cron, state.timezone, scheduled_for)
        missed = following <= now
        if missed:
            await append_audit(
                session,
                action="schedule_missed",
                payload={
                    "schedule_id": state.schedule_id,
                    "procedure_id": state.procedure_id,
                    "scheduled_for": scheduled_for.isoformat(),
                    "skipped_from": following.isoformat(),
                    "observed_at": now.isoformat(),
                    "policy": "skip_no_backfill",
                },
            )

        run = resolve(state)
        run_id = f"{state.schedule_id}@{scheduled_for.isoformat()}"
        trigger_context = _trigger_context(
            state, scheduled_for, now, run.service_principal.service_principal_id
        )
        result = await run_procedure_persisted(
            session,
            run.procedure,
            run.agent,
            run.executors,
            vertical=run.vertical,
            run_id=run_id,
            trigger_context=trigger_context,
            principal=run.owning_person,
            service_principal=run.service_principal,
        )

        state.last_fired = now
        state.next_fire = next_fire_fn(state.cron, state.timezone, now)
        state.updated_at = now
        await session.merge(state)
        await session.commit()
        outcomes.append(
            FireOutcome(
                state.schedule_id,
                FireResult.FIRED,
                scheduled_for,
                run_id=run_id,
                run_status=result.run.status,
                missed=missed,
            )
        )
    return outcomes
