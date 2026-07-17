"""The ``event``/Alert-trigger bridge — pure, DB-free helpers (ADR-0029 / PLAN-0056).

The recommender's actionable detection feeds INTO the governed Procedure engine (ADR-0029
SD-1): an actionable event maps to and fires a governed ``PipelineRun`` — not the lightweight
``ActionRecord`` execute path. This module holds the deterministic dedup key + run-id
composition (Step 3); the event resolver (Step 4) and the in-process fire function (Step 5)
build on it. Everything here is pure + offline-testable — no DB, no model call.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from services.db.audit_log import append_audit
from services.engine.procedures.orchestrator import StepExecutor
from services.engine.procedures.persistence import run_procedure_persisted
from services.engine.procedures.runs import PipelineRun, PipelineRunStatus
from services.engine.procedures.spec import (
    Agent,
    Person,
    Procedure,
    ServicePrincipal,
    StepKind,
    VerticalProcedures,
)
from services.engine.registry import ExecutorFactory

_KEY_HEX_LEN = 16
"""sha256 hexdigest truncated to 16 chars (64 bits) — ample for per-vertical event dedup,
short enough to keep the ``<procedure_id>@<event_key>`` run-id compact."""


def event_key(
    *,
    vertical: str,
    event_kind: str,
    entity_ids: Sequence[str],
    detected_at: datetime,
    window_seconds: int,
) -> str:
    """The deterministic dedup key of an event-fired run (ADR-0029 SD-2 / PLAN-0056 SD-P1).

    Hashes ``(vertical, event_kind, sorted primary affected-entity ids, detection-window
    bucket)``. The window bucket truncates ``detected_at`` to ``window_seconds`` granularity,
    so a steady-state anomaly re-detected each poll collapses to ONE key (=> one run — an
    idempotent no-op re-fire), while the same condition recurring in a LATER window yields a
    fresh key (=> a new run). Entity ids are sorted so detection ordering never splits the key.
    A naive ``detected_at`` is read as UTC so the bucket is machine-independent (never the
    host's local tz). ``window_seconds`` is per-mapping (SD-P1) — wired from the
    :class:`EventTrigger` descriptor by the Step-5 fire function; a slow-moving asset anomaly
    wants a wide window, a transient one a narrow one.
    """
    if window_seconds <= 0:
        raise ValueError(f"event_key: window_seconds must be > 0 (got {window_seconds})")
    if detected_at.tzinfo is None:
        detected_at = detected_at.replace(tzinfo=UTC)
    bucket = int(detected_at.timestamp()) // window_seconds
    # \x1f (unit separator) is an unambiguous field boundary so a split shift can never collide
    # (e.g. vertical="a"+kind="bc" must not hash the same as vertical="ab"+kind="c").
    payload = "\x1f".join([vertical, event_kind, *sorted(entity_ids), str(bucket)])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:_KEY_HEX_LEN]


def event_run_id(procedure_id: str, key: str) -> str:
    """Compose the per-event ``run_id`` ``<procedure_id>@<event_key>`` — the ``pipeline_runs``
    PK whose write-ahead insert makes a re-detected event an idempotent no-op (ADR-0029 SD-2;
    mirrors the schedule ``<schedule_id>@<scheduled_for>`` key, PLAN-0055 Step 6)."""
    return f"{procedure_id}@{key}"


# --- Step 4: the event resolver (event -> run-request, mirrors scheduler_wiring.build_resolver)


class EventBridgeError(Exception):
    """Raised when a detected event cannot be resolved into a runnable — an unmapped
    ``event_kind`` (the REACHABLE case: a detected condition no procedure claims) or a spec
    misconfiguration (agent / service-principal / owning-person absent; unreachable for a
    load-validated spec — defensive). Mirrors :class:`scheduler_wiring.SchedulerWiringError`;
    surfaces on the fire path, never a silent drop (ADR-0029 D4 loud-on-failure)."""


@dataclass(frozen=True)
class EventRunRequest:
    """Everything the Step-5 fire function needs to start ONE event-triggered run — the resolver
    maps a detected actionable event into this from the loaded vertical spec (procedure by
    ``event_kind``, its ``run_by`` agent, the executor map, the declared ``ServicePrincipal`` +
    the SP-5 ``owning_person``) plus the deterministic event-keyed ``run_id`` (ADR-0029 SD-2) and
    the detection ``trigger_context`` stamp. Mirrors :class:`scheduler.ScheduledRun` and adds
    ``run_id`` + ``trigger_context`` (an event run computes its own dedup key, unlike a schedule
    whose fire-fn computes the per-slot key)."""

    procedure: Procedure
    agent: Agent
    executors: Mapping[StepKind, StepExecutor]
    vertical: str
    service_principal: ServicePrincipal
    run_id: str
    trigger_context: dict[str, Any]
    owning_person: Person | None = None


def _find_event_procedure(spec: VerticalProcedures, event_kind: str) -> Procedure:
    """The single ``event``-trigger procedure whose descriptor claims ``event_kind`` (ADR-0029
    SD-3; uniqueness is a load-time cross-ref, so at most one matches). An unmapped kind is the
    REACHABLE failure — a detected event no procedure handles — and raises loudly."""
    for proc in spec.procedures:
        et = proc.event_trigger
        if et is not None and et.event_kind == event_kind:
            return proc
    known = sorted(
        p.event_trigger.event_kind for p in spec.procedures if p.event_trigger is not None
    )
    raise EventBridgeError(
        f"vertical '{spec.vertical}': no event-triggered procedure maps event_kind "
        f"'{event_kind}' (known: {known})"
    )


def _find_agent(spec: VerticalProcedures, procedure: Procedure) -> Agent:
    # mirrors scheduler_wiring._find_agent (defensive — run_by is cross-ref-validated at load).
    agent = next((a for a in spec.agents if a.agent_id == procedure.run_by), None)
    if agent is None:
        raise EventBridgeError(
            f"vertical '{spec.vertical}': procedure '{procedure.procedure_id}' is run_by unknown "
            f"agent '{procedure.run_by}'"
        )
    return agent


def _resolve_service_principal(spec: VerticalProcedures, agent: Agent) -> ServicePrincipal:
    # mirrors scheduler_wiring._resolve_service_principal — the non-human actor an event-fired
    # run acts as (SP-4), the agent's FIRST declared service_principal_id.
    if not agent.service_principal_ids:
        raise EventBridgeError(
            f"vertical '{spec.vertical}': agent '{agent.agent_id}' declares no "
            "service_principal_ids — an event-fired run needs a service actor (SP-4)"
        )
    sp_id = agent.service_principal_ids[0]
    sp = next((s for s in spec.service_principals if s.service_principal_id == sp_id), None)
    if sp is None:  # unreachable for a validated spec (cross-ref at load) — defensive
        raise EventBridgeError(
            f"vertical '{spec.vertical}': agent '{agent.agent_id}' service_principal_id "
            f"'{sp_id}' is not in spec.service_principals"
        )
    return sp


def _resolve_event_owning_person(spec: VerticalProcedures, procedure: Procedure) -> Person | None:
    # mirrors scheduler_wiring._resolve_owning_person, reading event_trigger.owning_person_id
    # (SP-5 — the human the service acts ON BEHALF OF, recorded as the SoD requester).
    et = procedure.event_trigger
    oref = et.owning_person_id if et is not None else None
    if oref is None:
        return None
    person = next((p for p in spec.principals if p.person_id == oref), None)
    if person is None:  # unreachable for a validated spec — defensive
        raise EventBridgeError(
            f"vertical '{spec.vertical}': procedure '{procedure.procedure_id}' "
            f"event_trigger.owning_person_id '{oref}' is not in spec.principals"
        )
    return person


def build_event_resolver(
    spec: VerticalProcedures, executor_factory: ExecutorFactory
) -> Callable[..., EventRunRequest]:
    """Build the event resolver — a detected actionable event -> :class:`EventRunRequest`,
    mirroring :func:`scheduler_wiring.build_resolver`. ``executor_factory`` is the vertical's
    registered factory (called fresh per fire so stateful executors never leak). Called ONLY on
    the fire path, so an unmapped-kind misconfiguration surfaces only when a run would start.
    """
    vertical = spec.vertical

    def resolve(
        *, event_kind: str, entity_ids: Sequence[str], detected_at: datetime
    ) -> EventRunRequest:
        procedure = _find_event_procedure(spec, event_kind)
        agent = _find_agent(spec, procedure)
        service_principal = _resolve_service_principal(spec, agent)
        owning_person = _resolve_event_owning_person(spec, procedure)
        et = procedure.event_trigger
        assert et is not None  # invariant: trigger==event => descriptor present (load-checked)
        key = event_key(
            vertical=vertical,
            event_kind=event_kind,
            entity_ids=entity_ids,
            detected_at=detected_at,
            window_seconds=et.dedup_window_seconds,
        )
        trigger_context: dict[str, Any] = {
            "trigger": "event",
            "event_kind": event_kind,
            "event_key": key,
            "entity_ids": sorted(entity_ids),
            "detected_at": detected_at.isoformat(),
        }
        return EventRunRequest(
            procedure=procedure,
            agent=agent,
            executors=executor_factory(),
            vertical=vertical,
            service_principal=service_principal,
            run_id=event_run_id(procedure.procedure_id, key),
            trigger_context=trigger_context,
            owning_person=owning_person,
        )

    return resolve


# --- Step 5: the in-process fire function (SD-1 FEED-INTO; SD-4; SD-P4 skip-if-in-flight) ---


class EventFireResult(StrEnum):
    """The outcome of one :func:`fire_event` call."""

    FIRED = "fired"
    ALREADY_FIRED = "already_fired"
    SKIPPED_IN_FLIGHT = "skipped_in_flight"


@dataclass(frozen=True)
class EventFireOutcome:
    """The result of firing (or skipping) ONE event-triggered run."""

    run_id: str
    result: EventFireResult
    run_status: str | None = None


async def _event_run_exists(session: AsyncSession, run_id: str) -> bool:
    # mirrors scheduler._run_exists — the event-keyed run_id is the write-ahead PK, so a row
    # exists IFF this exact event (same key/window) already fired. The SD-2 idempotency guard.
    row = await session.execute(
        sa.select(PipelineRun.run_id).where(PipelineRun.run_id == run_id).limit(1)
    )
    return row.scalar_one_or_none() is not None


async def _procedure_in_flight(session: AsyncSession, procedure_id: str) -> bool:
    # mirrors scheduler._in_flight — a prior run of this procedure is still running /
    # waiting_human (a gated run parks for days). SD-P4 backpressure.
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


async def _audit_event_skipped(
    session: AsyncSession, request: EventRunRequest, reason: str
) -> None:
    """A ``event_skipped`` audit row for observability (a re-detected no-op or an in-flight
    skip). The LOUD-on-failure alert for a mapping/resolve failure is PLAN-0056 Step 7."""
    await append_audit(
        session,
        action="event_skipped",
        payload={
            "procedure_id": request.procedure.procedure_id,
            "run_id": request.run_id,
            "event_kind": request.trigger_context.get("event_kind"),
            "reason": reason,
        },
    )
    await session.commit()


async def fire_event(
    session: AsyncSession, request: EventRunRequest, *, now: datetime
) -> EventFireOutcome:
    """Fire ONE event-triggered governed run in-process (ADR-0029 SD-1 FEED-INTO / SD-4;
    PLAN-0056 Step 5).

    The recommender's actionable detection is FED INTO the governed engine — this drives a REAL
    ``PipelineRun`` via :func:`run_procedure_persisted` (NOT the lightweight ``ActionRecord``
    execute path). Two skips precede the fire, mirroring the scheduler:

    * **SD-2 idempotency** — the event-keyed ``run_id`` already exists (the same event re-detected
      in the same detection window) → no-op (``ALREADY_FIRED``); the write-ahead PK is the dedup.
    * **SD-P4 skip-if-in-flight** — a DIFFERENT run of the same procedure is
      ``running``/``waiting_human`` (a gated run legitimately parks for days) → skip
      (``SKIPPED_IN_FLIGHT``).

    ``now`` is injected (no wall-clock read) so the ``fired_at`` stamp + tests are deterministic.
    The service-actor audit (AC-7), the gated-park posture (AC-8), and the write-ahead durability
    are inherited verbatim from :func:`run_procedure_persisted` — the bridge is a pure client of
    the S2 actor plumbing, it rebuilds none of it.
    """
    if await _event_run_exists(session, request.run_id):
        await _audit_event_skipped(session, request, "already_fired")
        return EventFireOutcome(request.run_id, EventFireResult.ALREADY_FIRED)
    if await _procedure_in_flight(session, request.procedure.procedure_id):
        await _audit_event_skipped(session, request, "in_flight")
        return EventFireOutcome(request.run_id, EventFireResult.SKIPPED_IN_FLIGHT)
    result = await run_procedure_persisted(
        session,
        request.procedure,
        request.agent,
        request.executors,
        vertical=request.vertical,
        run_id=request.run_id,
        trigger_context={**request.trigger_context, "fired_at": now.isoformat()},
        principal=request.owning_person,
        service_principal=request.service_principal,
    )
    return EventFireOutcome(request.run_id, EventFireResult.FIRED, run_status=result.run.status)
