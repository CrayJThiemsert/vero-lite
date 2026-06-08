"""Persistence + resume for Procedure runs (ADR-016 D4; PLAN-0019 Part A, A-delta).

Durable / resumable runs (ADR-016 D4): a ``gated`` action or ``human_task`` step
suspends the run at ``waiting_human``; this module persists the in-memory
``PipelineRun`` / ``StepResult`` records the orchestrator produces and, after the
human acts, **resumes** the run from the step AFTER the suspended one —
reconstructing engine state purely from the DB, so a fresh process can resume a
run another process started. The suspended step's persisted
``artifact["output_set"]`` is threaded forward, so no completed step is ever
re-executed (no duplicate side effects).

Layering: the orchestrator (``orchestrator.py``) stays DB-free; this module is
the DB + resume seam. Executing a ``gated`` action's effect on approval is the
action executor's job (a later step) + the ADR-007 approve->execute gate; resume
here drives the control-plane continuation.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.engine.procedures.orchestrator import (
    ProcedureError,
    RunContext,
    RunResult,
    StepExecutor,
    execute_steps,
    validate_runnable,
)
from services.engine.procedures.runs import (
    PipelineRun,
    PipelineRunStatus,
    StepResult,
    StepResultStatus,
)
from services.engine.procedures.spec import Agent, Procedure, StepKind


async def persist_run(session: AsyncSession, result: RunResult) -> None:
    """Persist a run + its step results (idempotent via ``merge``)."""
    await session.merge(result.run)
    for step_result in result.step_results:
        await session.merge(step_result)
    await session.commit()


async def load_run(session: AsyncSession, run_id: str) -> RunResult | None:
    """Load a persisted run + its step results (execution order), or ``None``."""
    run = await session.get(PipelineRun, run_id)
    if run is None:
        return None
    rows = await session.execute(
        select(StepResult)
        .where(StepResult.run_id == run_id)
        .order_by(StepResult.created_at, StepResult.step_result_id)
    )
    return RunResult(run=run, step_results=list(rows.scalars().all()))


async def resume_run(
    session: AsyncSession,
    procedure: Procedure,
    agent: Agent,
    executors: Mapping[StepKind, StepExecutor],
    run_id: str,
    *,
    vertical: str,
) -> RunResult:
    """Resume a ``waiting_human`` run from the step AFTER its suspended one.

    Reconstructs state from the DB (a fresh process can resume), marks the
    suspended step ``complete`` (the human acted), threads its persisted
    ``artifact["output_set"]`` forward, runs the remaining steps, and persists the
    updated run + new step results. Raises :class:`ProcedureError` if the run is
    absent, not ``waiting_human``, or its suspended step is not in ``procedure``.
    """
    validate_runnable(procedure, agent)
    loaded = await load_run(session, run_id)
    if loaded is None:
        raise ProcedureError(f"run '{run_id}' not found")
    run = loaded.run
    if run.status != PipelineRunStatus.WAITING_HUMAN.value:
        raise ProcedureError(
            f"run '{run_id}' is not resumable — status '{run.status}' (expected waiting_human)"
        )
    if not loaded.step_results:
        raise ProcedureError(f"run '{run_id}' has no step results to resume from")

    suspended = loaded.step_results[-1]
    index = next((i for i, s in enumerate(procedure.steps) if s.step_id == suspended.step_id), None)
    if index is None:
        raise ProcedureError(
            f"run '{run_id}': suspended step '{suspended.step_id}' is not in "
            f"procedure '{procedure.procedure_id}'"
        )

    # The human resolved the suspended step; thread its output set forward and
    # continue from the NEXT step (the completed prefix is never re-executed).
    suspended.status = StepResultStatus.COMPLETE.value
    artifact: dict[str, Any] = suspended.artifact or {}
    input_set: list[Any] = artifact.get("output_set", [])
    ctx = RunContext(agent=agent, vertical=vertical, trigger_context=run.trigger_context)
    new_results, final_status = await execute_steps(
        procedure.steps, executors, ctx, run_id, input_set=input_set, start_index=index + 1
    )
    run.status = final_status.value
    run.updated_at = datetime.now(UTC)
    for step_result in new_results:
        session.add(step_result)
    await session.commit()
    return RunResult(run=run, step_results=loaded.step_results + new_results)
