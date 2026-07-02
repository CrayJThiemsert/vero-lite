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
    validate_read_bindings_for_vertical,
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
    """Resume a ``waiting_human`` run, reconstructing state purely from the DB.

    Two cases, distinguished by whether the suspended step recorded an artifact:

    * **Gated action / human_task suspend** (artifact present): the step is
      resolved by the human — mark it ``complete``, thread its persisted
      ``artifact["output_set"]`` forward, and continue from the NEXT step (the
      completed prefix is never re-executed).
    * **Escalated failure** (``on_failure = escalate_to_human``; no artifact): the
      step failed and a human took over — **re-run that step** from its original
      input (the prior step's output), overwriting the stale failed record, so a
      human can fix the cause and retry without rewinding the whole run.

    Persists the updated run + the new step results. Raises :class:`ProcedureError`
    if the run is absent, not ``waiting_human``, or its suspended step is not in
    ``procedure``.
    """
    validate_runnable(procedure, agent)
    validate_read_bindings_for_vertical(procedure, agent, vertical)
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

    ctx = RunContext(
        agent=agent,
        vertical=vertical,
        trigger_context=run.trigger_context,
        goal=procedure.goal or None,
    )
    # Rebuild the named-output bag from every completed step that recorded an
    # output, so a resumed step can reference ANY earlier named step (the
    # breach/watch/ok fan-out), not just the one immediately before it.
    prior_outputs: dict[str, list[Any]] = {
        sr.step_id: sr.artifact["output_set"]
        for sr in loaded.step_results
        if sr.artifact and "output_set" in sr.artifact
    }

    if suspended.artifact is None:
        # Escalated failure (no artifact): re-run the failed step from its resolved
        # input; the stale failed record (same step_result_id) is overwritten on merge.
        prior_results = loaded.step_results[:-1]
        start_index = index
    else:
        # Gated action / human_task suspend: the human resolved it — mark complete
        # (its output is already in the bag) and continue from the NEXT step.
        suspended.status = StepResultStatus.COMPLETE.value
        prior_results = loaded.step_results
        start_index = index + 1

    new_results, final_status = await execute_steps(
        procedure.steps,
        executors,
        ctx,
        run_id,
        prior_outputs=prior_outputs,
        start_index=start_index,
    )
    run.status = final_status.value
    run.updated_at = datetime.now(UTC)
    for step_result in new_results:
        await session.merge(step_result)
    await session.commit()
    return RunResult(run=run, step_results=prior_results + new_results)
