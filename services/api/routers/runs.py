"""Procedure run + gate-resolve endpoints (PLAN-0047 Step 2; AC-2 / AC-3).

The two seams the engine already ships — ``run_procedure`` (suspends at a
gated step) and ``resolve_gated_step`` + ``resume_run`` (the human decision
+ continuation) — exposed over HTTP for the ACTIVE vertical
(``settings.oct_vertical``), with:

* **identity server-side only** (AC-2): the caller's ``Person`` comes from
  the Step-1 authn dependency; request bodies carry no principal field and
  a client-supplied ``triggered_by`` is OVERWRITTEN;
* **SoD context server-side** (non-skippable, ``action_step.py``): the
  resolve endpoint supplies the procedure + the vertical's authored
  principals + alias groups from the spec — the client cannot omit them;
* **executor wiring via the registry**: a vertical opts in by registering
  a procedure-executor factory (``registry.register_procedure_executors``,
  the explicit ADR-0023 pattern) — an unwired vertical gets 409, never a
  half-wired run.

The resolve endpoint applies the decisions and then RESUMES the run in the
same call (the human's single "submit decisions" action); the
escalated-failure resume (re-run a failed step) is NOT exposed in v1.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from services.api.auth import AuthContext, get_current_principal
from services.api.config import settings
from services.api.models.runs import (
    CancelRunResponse,
    GateResolveRequest,
    GateResolveResponse,
    ProposalView,
    RunDetailView,
    RunProcedureRequest,
    RunProcedureResponse,
    RunsListResponse,
    RunSummaryView,
    StepDetailView,
    StepResultView,
)
from services.db.session import get_session
from services.engine.procedures.action_step import PrincipalSoDError, resolve_gated_step
from services.engine.procedures.orchestrator import ProcedureError
from services.engine.procedures.persistence import (
    cancel_run,
    load_run,
    resume_run,
    run_procedure_persisted,
    suspended_step_result,
)
from services.engine.procedures.runs import (
    PipelineRun,
    PipelineRunStatus,
    StepResult,
    StepResultStatus,
)
from services.engine.procedures.spec import (
    Agent,
    Procedure,
    VerticalProcedures,
    load_procedures,
)
from services.engine.registry import ExecutorFactory, RegistryError, registry

router = APIRouter(tags=["runs"])


def _spec_for(vertical: str) -> VerticalProcedures:
    try:
        return load_procedures(vertical)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail=f"vertical '{vertical}' ships no procedures file"
        ) from exc


def _find_procedure(spec: VerticalProcedures, procedure_id: str) -> Procedure:
    procedure = next((p for p in spec.procedures if p.procedure_id == procedure_id), None)
    if procedure is None:
        raise HTTPException(
            status_code=404,
            detail=f"no procedure '{procedure_id}' in vertical '{spec.vertical}'",
        )
    return procedure


def _find_agent(spec: VerticalProcedures, procedure: Procedure) -> Agent:
    agent = next((a for a in spec.agents if a.agent_id == procedure.run_by), None)
    if agent is None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"procedure '{procedure.procedure_id}' names run_by "
                f"'{procedure.run_by}' but the vertical ships no such agent"
            ),
        )
    return agent


def _executor_factory(vertical: str) -> ExecutorFactory:
    try:
        return registry.get_procedure_executors(vertical)
    except RegistryError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def _step_views(step_results: list[StepResult]) -> list[StepResultView]:
    return [StepResultView(step_id=s.step_id, status=s.status) for s in step_results]


def _suspended_step(step_results: list[StepResult], run_status: str) -> StepResult | None:
    # By status, never by list position — load_run orders on a wall-clock column
    # that a backward clock step can invert (see suspended_step_result).
    if run_status != PipelineRunStatus.WAITING_HUMAN.value or not step_results:
        return None
    return suspended_step_result(step_results)


def _proposals(suspended: StepResult | None) -> list[ProposalView]:
    if suspended is None:
        return []
    output_set: list[dict[str, Any]] = (suspended.artifact or {}).get("output_set", [])
    views: list[ProposalView] = []
    for proposal in output_set:
        action = proposal.get("action")
        if not isinstance(action, dict):
            continue  # a human_task / non-proposal artifact — nothing decidable
        views.append(
            ProposalView(
                action_id=str(action.get("id", "")),
                title=str(action.get("title", "")),
                suggested_handler=action.get("suggested_handler"),
            )
        )
    return views


def _trigger_of(trigger_context: dict[str, Any] | None) -> str:
    """The trigger discriminator recorded on the run — ``manual`` when unstamped
    (forward-compat: the S1 scheduler will stamp ``schedule``)."""
    return str((trigger_context or {}).get("trigger") or "manual")


def _triggered_by(trigger_context: dict[str, Any] | None) -> str | None:
    """The actor recorded on the run, displayed GENERICALLY (a person_id today; a
    service-principal id post-ADR-016 S2) — never assumed to be a ``Person``."""
    value = (trigger_context or {}).get("triggered_by")
    return str(value) if value is not None else None


def _detail_step_views(step_results: list[StepResult]) -> list[StepDetailView]:
    return [
        StepDetailView(
            step_id=s.step_id,
            status=s.status,
            duration_ms=s.duration_ms,
            artifact=s.artifact,
            reasoning_trace=s.reasoning_trace,
            audit=s.audit,
        )
        for s in step_results
    ]


# --- PLAN-0052 Phase-3 OCT monitor (v1): READ-ONLY list + detail endpoints. ---
# No mutation, no LLM call, no executor — only SELECTs (AC-3). These are the
# mirror-image GET of the existing POST run/gate-resolve seams: the monitor
# reads the same persisted records the Control write path acts on, so
# "approve/reject/cancel from the UI" later is an extension, not a rewrite (L4).


@router.get("/runs", response_model=RunsListResponse)
async def list_runs(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RunsListResponse:
    """List persisted runs, newest-first — a READ-ONLY projection (AC-1 / AC-3).

    Runs are scoped by the single active vertical (``settings.oct_vertical``);
    ``steps_total`` is the current spec's declared step count when the procedure
    still ships.
    """
    vertical = settings.oct_vertical
    declared: dict[str, int] = {}
    try:
        spec = load_procedures(vertical)
        declared = {p.procedure_id: len(p.steps) for p in spec.procedures}
    except FileNotFoundError:
        declared = {}  # a vertical shipping no procedures file still lists its runs

    runs = (
        (await session.execute(select(PipelineRun).order_by(PipelineRun.started_at.desc())))
        .scalars()
        .all()
    )
    run_ids = [r.run_id for r in runs]
    recorded: dict[str, int] = {}
    waiting: dict[str, int] = {}
    if run_ids:
        rows = await session.execute(
            select(StepResult.run_id, StepResult.status).where(StepResult.run_id.in_(run_ids))
        )
        for sr_run_id, sr_status in rows.all():
            recorded[sr_run_id] = recorded.get(sr_run_id, 0) + 1
            if sr_status == StepResultStatus.WAITING_HUMAN.value:
                waiting[sr_run_id] = waiting.get(sr_run_id, 0) + 1

    summaries = [
        RunSummaryView(
            run_id=r.run_id,
            procedure_id=r.procedure_id,
            agent_id=r.agent_id,
            status=r.status,
            trigger=_trigger_of(r.trigger_context),
            triggered_by=_triggered_by(r.trigger_context),
            started_at=r.started_at,
            updated_at=r.updated_at,
            steps_recorded=recorded.get(r.run_id, 0),
            steps_total=declared.get(r.procedure_id),
            steps_waiting=waiting.get(r.run_id, 0),
        )
        for r in runs
    ]
    waiting_human_count = sum(1 for r in runs if r.status == PipelineRunStatus.WAITING_HUMAN.value)
    return RunsListResponse(runs=summaries, waiting_human_count=waiting_human_count)


@router.get("/runs/{run_id}", response_model=RunDetailView)
async def get_run(
    run_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RunDetailView:
    """One run's full read projection: ordered steps + per-step trace/audit, plus
    the ``waiting_human`` gate + its pending proposals exposed READ-ONLY
    (AC-2 / AC-7). Reuses the existing ``load_run`` — no new query layer, no
    mutation.
    """
    loaded = await load_run(session, run_id)
    if loaded is None:
        raise HTTPException(status_code=404, detail=f"run '{run_id}' not found")
    run = loaded.run
    suspended = _suspended_step(loaded.step_results, run.status)
    return RunDetailView(
        run_id=run.run_id,
        procedure_id=run.procedure_id,
        agent_id=run.agent_id,
        status=run.status,
        trigger=_trigger_of(run.trigger_context),
        triggered_by=_triggered_by(run.trigger_context),
        started_at=run.started_at,
        updated_at=run.updated_at,
        suspended_step=suspended.step_id if suspended is not None else None,
        proposals=_proposals(suspended),
        steps=_detail_step_views(loaded.step_results),
    )


@router.post("/procedures/{procedure_id}/run", response_model=RunProcedureResponse)
async def run_procedure_endpoint(
    procedure_id: str,
    req: RunProcedureRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    auth: Annotated[AuthContext, Depends(get_current_principal)],
) -> RunProcedureResponse:
    """Run a shipped procedure of the active vertical; suspends at the first gate.

    The run is persisted with the SERVER-resolved identity: ``triggered_by``
    in the trigger context is always the authenticated person_id (a spoofed
    value in the request body is overwritten — AC-2), and the ambient SoD
    requester principal is the authenticated ``Person``.
    """
    vertical = settings.oct_vertical
    spec = _spec_for(vertical)
    procedure = _find_procedure(spec, procedure_id)
    agent = _find_agent(spec, procedure)
    factory = _executor_factory(vertical)

    trigger_context: dict[str, Any] = dict(req.trigger_context or {})
    trigger_context["triggered_by"] = auth.person_id  # server-owned; never client-supplied

    run_id = f"run-{uuid4().hex[:12]}"
    try:
        # PLAN-0047 Step 4 (AC-6): the WRITE-AHEAD driver — the running row is
        # durable before step 1 executes; each StepResult commits as it lands.
        result = await run_procedure_persisted(
            session,
            procedure,
            agent,
            factory(),
            vertical=vertical,
            run_id=run_id,
            trigger_context=trigger_context,
            principal=auth.person,
        )
    except ProcedureError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    suspended = _suspended_step(result.step_results, result.run.status)
    return RunProcedureResponse(
        run_id=run_id,
        procedure_id=procedure.procedure_id,
        status=result.run.status,
        triggered_by=auth.person_id,
        suspended_step=suspended.step_id if suspended is not None else None,
        proposals=_proposals(suspended),
        steps=_step_views(result.step_results),
    )


@router.post("/runs/{run_id}/gate/resolve", response_model=GateResolveResponse)
async def resolve_gate_endpoint(
    run_id: str,
    req: GateResolveRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    auth: Annotated[AuthContext, Depends(get_current_principal)],
) -> GateResolveResponse:
    """Apply a human's decisions to a suspended gate, then resume the run.

    The approving principal is the authenticated ``Person`` (server-resolved);
    the SoD resolution context (procedure + authored principals + alias
    groups) is supplied server-side from the vertical's spec — the
    non-skippable principal-SoD run-check fails CLOSED (403) on a violation.
    """
    # RF-1 (ADR-016 S2, PLAN-0053 AC-1): a gated step's approver MUST be an
    # authenticated human. When api_auth_enabled is off (auth.py -> person_id None)
    # or no valid credential was presented, there is no accountable approver -> fail
    # closed (403), INDEPENDENT of the authn toggle (closing the amendment's
    # motivating hole: authn-off gate-resolve silently applying decisions with no
    # human). This is the Phase-A human path; Phase B adds the library-level
    # rejection of a non-human (service) approver at the resolve_gated_step
    # chokepoint (the scheduler path, which bypasses this HTTP surface).
    if auth.person_id is None:
        raise HTTPException(
            status_code=403,
            detail=(
                "a gated step requires an authenticated human approver (ADR-016 S2 "
                "RF-1) — api_auth_enabled is off or no valid credential was presented"
            ),
        )

    vertical = settings.oct_vertical
    loaded = await load_run(session, run_id)
    if loaded is None:
        raise HTTPException(status_code=404, detail=f"run '{run_id}' not found")

    spec = _spec_for(vertical)
    procedure = next(
        (p for p in spec.procedures if p.procedure_id == loaded.run.procedure_id), None
    )
    if procedure is None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"run '{run_id}' references procedure '{loaded.run.procedure_id}' "
                f"which vertical '{vertical}' no longer ships"
            ),
        )
    agent = _find_agent(spec, procedure)
    factory = _executor_factory(vertical)

    try:
        await resolve_gated_step(
            session,
            run_id,
            req.step_id,
            dict(req.decisions),
            principal=auth.person,
            procedure=procedure,
            principals=spec.principals,
            principal_aliases=spec.principal_aliases,
        )
    except PrincipalSoDError as exc:
        detail: dict[str, Any] = {"error": str(exc)}
        if is_dataclass(exc.verdict) and not isinstance(exc.verdict, type):
            detail["verdict"] = asdict(exc.verdict)
        raise HTTPException(status_code=403, detail=detail) from exc
    except ProcedureError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except StaleDataError as exc:
        # PLAN-0047 Step 3: the optimistic-lock version says another writer got
        # here first — the concurrent resolver loses cleanly, never double-writes.
        raise HTTPException(
            status_code=409, detail=f"run '{run_id}' was updated concurrently — reload and retry"
        ) from exc

    try:
        result = await resume_run(
            session,
            procedure,
            agent,
            factory(),
            run_id,
            vertical=vertical,
            principal=auth.person,  # PLAN-0053 AC-3: never-null actor on the resumed continuation
        )
    except ProcedureError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except StaleDataError as exc:
        raise HTTPException(
            status_code=409, detail=f"run '{run_id}' was updated concurrently — reload and retry"
        ) from exc

    suspended = _suspended_step(result.step_results, result.run.status)
    return GateResolveResponse(
        run_id=run_id,
        resolved_step=req.step_id,
        run_status=result.run.status,
        suspended_step=suspended.step_id if suspended is not None else None,
        steps=_step_views(result.step_results),
    )


@router.post("/runs/{run_id}/cancel", response_model=CancelRunResponse)
async def cancel_run_endpoint(
    run_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    auth: Annotated[AuthContext, Depends(get_current_principal)],
) -> CancelRunResponse:
    """Cancel a run parked at a human gate — a governed human action (PLAN-0054
    Control-leg v1, SD-B). Requires an authenticated human (RF-1, mirrors the
    resolve endpoint); v1 cancels ONLY a ``waiting_human`` run (parked = no
    in-flight effect) — any other state is a 409. Writes ``status = cancelled`` +
    a ``run_cancelled`` audit row naming the human actor.
    """
    # RF-1 (ADR-016 S2): cancelling a governed run is a consequential action —
    # require an authenticated human (authn off -> no accountable actor -> 403),
    # mirroring the resolve endpoint's guard.
    if auth.person_id is None:
        raise HTTPException(
            status_code=403,
            detail=(
                "cancelling a run requires an authenticated human (ADR-016 S2 RF-1) "
                "— api_auth_enabled is off or no valid credential was presented"
            ),
        )

    loaded = await load_run(session, run_id)
    if loaded is None:
        raise HTTPException(status_code=404, detail=f"run '{run_id}' not found")

    # SD-B: v1 cancels ONLY a parked (waiting_human) run — a run mid-execution
    # (running) or already settled (completed/failed/cancelled) is NOT cancellable.
    if loaded.run.status != PipelineRunStatus.WAITING_HUMAN.value:
        raise HTTPException(
            status_code=409,
            detail=(
                f"run '{run_id}' is not cancellable — status '{loaded.run.status}' "
                "(v1 cancels only a waiting_human run)"
            ),
        )

    try:
        run = await cancel_run(session, loaded.run, actor_person_id=auth.person_id)
    except StaleDataError as exc:
        raise HTTPException(
            status_code=409,
            detail=f"run '{run_id}' was updated concurrently — reload and retry",
        ) from exc

    return CancelRunResponse(run_id=run_id, run_status=run.status)
