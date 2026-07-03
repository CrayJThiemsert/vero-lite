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
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from services.api.auth import AuthContext, get_current_principal
from services.api.config import settings
from services.api.models.runs import (
    GateResolveRequest,
    GateResolveResponse,
    ProposalView,
    RunProcedureRequest,
    RunProcedureResponse,
    StepResultView,
)
from services.db.session import get_session
from services.engine.procedures.action_step import PrincipalSoDError, resolve_gated_step
from services.engine.procedures.orchestrator import ProcedureError, run_procedure
from services.engine.procedures.persistence import load_run, persist_run, resume_run
from services.engine.procedures.runs import PipelineRunStatus, StepResult
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
    if run_status != PipelineRunStatus.WAITING_HUMAN.value or not step_results:
        return None
    return step_results[-1]


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
        result = await run_procedure(
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
    await persist_run(session, result)

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
        result = await resume_run(session, procedure, agent, factory(), run_id, vertical=vertical)
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
