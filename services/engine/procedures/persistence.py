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

from services.db.audit_log import append_audit
from services.engine.procedures.governance_pin import governance_pin_for
from services.engine.procedures.orchestrator import (
    ProcedureError,
    RunContext,
    RunResult,
    StepExecutor,
    _record_requester_principals,
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
from services.engine.procedures.spec import Agent, Person, Procedure, ServicePrincipal, StepKind


async def persist_run(session: AsyncSession, result: RunResult) -> None:
    """Persist a run + its step results (idempotent via ``merge``)."""
    await session.merge(result.run)
    for step_result in result.step_results:
        await session.merge(step_result)
    await session.commit()


def _read_refusal_entry(step_result: StepResult) -> dict[str, Any] | None:
    """The structured ``read_refused`` trace entry on a diverted step, if any.

    PLAN-0048 SD-5(a): the persistence seam — not the DB-free executor —
    turns a typed read refusal into a first-class, hash-chained audit fact.
    The entry shape is the orchestrator's D4 structured divert (AC-8).
    """
    for entry in step_result.reasoning_trace or []:
        if isinstance(entry, dict) and entry.get("kind") == "read_refused":
            return entry
    return None


async def _append_read_refusal_audit(
    session: AsyncSession, run_id: str, step_result: StepResult
) -> None:
    """Append the ``read_refused`` audit row when a refusal StepResult lands
    (same transaction as the step-result commit — the caller owns the commit)."""
    refusal = _read_refusal_entry(step_result)
    if refusal is None:
        return
    await append_audit(
        session,
        action="read_refused",
        run_id=run_id,
        step_id=step_result.step_id,
        payload={
            "refusal_kind": refusal.get("refusal_kind"),
            "object_type": refusal.get("object_type"),
        },
    )


async def run_procedure_persisted(
    session: AsyncSession,
    procedure: Procedure,
    agent: Agent,
    executors: Mapping[StepKind, StepExecutor],
    *,
    vertical: str,
    run_id: str,
    trigger_context: dict[str, Any] | None = None,
    principal: Person | None = None,
    service_principal: ServicePrincipal | None = None,
) -> RunResult:
    """WRITE-AHEAD run driver (PLAN-0047 Step 4, AC-6).

    The ``running`` :class:`PipelineRun` row is COMMITTED before step 1
    executes, and every :class:`StepResult` is committed as it completes
    (success, suspend, and failure) via the ``on_step_complete`` seam — so a
    crash mid-run leaves a queryable, resumable record instead of an
    invisible in-memory run. Mirrors :func:`orchestrator.run_procedure`
    exactly otherwise (same validation, same SoD requester recording); the
    DB-free ``run_procedure`` stays for library callers, the HTTP run
    surface uses this wrapper.
    """
    validate_runnable(procedure, agent)
    validate_read_bindings_for_vertical(procedure, agent, vertical)
    opened = datetime.now(UTC)
    # PLAN-0047 Step 6 (AC-8): pin the resolved governance config at run start.
    snapshot, config_hash = governance_pin_for(procedure)
    run = PipelineRun(
        run_id=run_id,
        procedure_id=procedure.procedure_id,
        agent_id=agent.agent_id,
        trigger_context=trigger_context,
        status=PipelineRunStatus.RUNNING.value,
        started_at=opened,
        updated_at=opened,
        governance_snapshot=snapshot,
        governance_hash=config_hash,
    )
    session.add(run)
    # PLAN-0047 Step 5: the run-start audit row lands in the SAME transaction
    # as the write-ahead run row (one durable fact, one commit).
    # PLAN-0053 AC-9/AC-10 (Phase B, OQ-3 audit-only): classify the trigger's actor. A
    # human-triggered run records actor_kind="human". A service-triggered run
    # (service_principal supplied — the forward-looking S1 scheduler path) records
    # actor_kind="service", a NEVER-null service actor in the new
    # actor_service_principal_id column (SP-4), and the on-behalf-of lineage (SP-5) —
    # BOTH who fired (the service id) and who owns/scheduled it (the human, if any).
    run_started_payload: dict[str, Any] = {
        "procedure_id": procedure.procedure_id,
        "agent_id": agent.agent_id,
        "actor_kind": "service" if service_principal is not None else "human",
    }
    if service_principal is not None:
        run_started_payload["on_behalf_of"] = {
            "service_principal_id": service_principal.service_principal_id,
            "owning_person_id": principal.person_id if principal is not None else None,
        }
    await append_audit(
        session,
        action="run_started",
        actor_person_id=(
            principal.person_id
            if principal is not None
            else (trigger_context or {}).get("triggered_by")
        ),
        actor_service_principal_id=(
            service_principal.service_principal_id if service_principal is not None else None
        ),
        run_id=run_id,
        payload=run_started_payload,
    )
    await session.commit()  # the write-ahead: the run is durable BEFORE any effect

    ctx = RunContext(
        agent=agent,
        vertical=vertical,
        trigger_context=trigger_context,
        goal=procedure.goal or None,
        principal=principal,
        service_principal=service_principal,
    )

    async def _persist_step(step_result: StepResult) -> None:
        await session.merge(step_result)
        # PLAN-0048 SD-5(a): a refusal StepResult lands with its audit row in
        # ONE transaction — refusal-safety becomes a tamper-evident audit fact.
        await _append_read_refusal_audit(session, run_id, step_result)
        await session.commit()

    step_results, final_status = await execute_steps(
        procedure.steps, executors, ctx, run_id, on_step_complete=_persist_step
    )
    run.status = final_status.value
    run.updated_at = datetime.now(UTC)
    run.step_principals = _record_requester_principals(procedure, step_results, ctx.principal)
    await session.commit()
    return RunResult(run=run, step_results=step_results)


async def load_run(session: AsyncSession, run_id: str) -> RunResult | None:
    """Load a persisted run + its step results (execution order), or ``None``.

    ``created_at`` is a WALL-CLOCK stamp, so this order is best-effort: a backward
    clock step (an NTP correction, a VM/WSL2 host resync) can stamp a later step
    with an earlier time. Never infer *which* step a run is suspended at from this
    order — use :func:`suspended_step_result`, which reads the status.
    """
    run = await session.get(PipelineRun, run_id)
    if run is None:
        return None
    rows = await session.execute(
        select(StepResult)
        .where(StepResult.run_id == run_id)
        .order_by(StepResult.created_at, StepResult.step_result_id)
    )
    return RunResult(run=run, step_results=list(rows.scalars().all()))


# The two statuses a not-yet-resumed step can hold: ``waiting_human`` (suspended at
# a gate, or escalated on failure with no artifact) and ``resolved`` (its gate was
# decided; awaiting the resume that threads the decision forward). Every other step
# of a resumable run is ``complete``, so exactly one step matches.
_UNRESUMED_STATUSES = frozenset(
    {StepResultStatus.WAITING_HUMAN.value, StepResultStatus.RESOLVED.value}
)


def suspended_step_result(step_results: list[StepResult]) -> StepResult | None:
    """The step a ``waiting_human`` run is suspended at — identified by STATUS.

    Never by list position. :func:`load_run` orders by ``created_at``, a wall-clock
    stamp that is not monotonic: a backward clock step between two steps of the same
    run sorts the later one first, and ``step_results[-1]`` then names a *completed*
    step. Resuming from it re-runs an already-executed gate (duplicate side effects)
    or fails closed on its undecided proposals.

    That ordering is left on the wall clock **by design** — the root fix (a monotonic
    per-run ``sequence`` column) needs a migration and its own PLAN. The deferral and
    why it stands are recorded in ``tests/services/db/test_load_run_ordering_guard.py``,
    which also statically forbids the positional read across the tree.

    Fails CLOSED on ambiguity. A run advances one gate at a time, so at most one
    step result is unresumed; two means the persisted rows are inconsistent. Picking
    either would resume from the wrong step — firing a handler a human never
    approved, or silently skipping one they did. Raise instead of guessing.
    """
    unresumed = [s for s in step_results if s.status in _UNRESUMED_STATUSES]
    if len(unresumed) > 1:
        run_id = unresumed[0].run_id
        names = ", ".join(f"{s.step_id}({s.status})" for s in unresumed)
        raise ProcedureError(
            f"run '{run_id}': {len(unresumed)} step results are unresumed [{names}] — "
            "exactly one is expected. The persisted run is inconsistent; it cannot be "
            "resumed or projected without guessing which gate a human decided."
        )
    return unresumed[0] if unresumed else None


def _has_decidable_proposals(artifact: dict[str, Any]) -> bool:
    """True when a suspended artifact carries >=1 REAL proposal (an ADR-007
    envelope whose ``action`` is a dict) — the only content
    :func:`resolve_gated_step` can decide. An empty watch set / non-proposal
    artifact has nothing to decide, so the documented plain-resume continuation
    contract holds for it (PLAN-0022 human_task parity)."""
    output_set = artifact.get("output_set", [])
    return any(
        isinstance(entry, dict) and isinstance(entry.get("action"), dict) for entry in output_set
    )


def assert_governance_pin(run: PipelineRun, procedure: Procedure, *, context: str) -> None:
    """PLAN-0047 Step 6 (AC-8): fail CLOSED when the caller-supplied procedure's
    governance config no longer matches the config pinned at run start.

    A mid-flight DOA-ladder / SoD / rule edit must never silently govern an
    old run — the ONLY sanctioned path is the refusal below: the operator
    cancels the stale run and starts a fresh one under the new config (no
    silent re-pin). A run with no pin (pre-0008 row / legacy library run)
    skips the check — backward compat.

    A vertical's DERIVED authority quantities are covered here through their declaring
    step's pinned ``transform`` (PLAN-0077/0078): a mid-flight edit to a declared
    severity ladder or spend derivation changes the config hash and trips this same
    refusal. PLAN-0078 PR-5 retired the PLAN-0075 AC-13 code-hash side-channel once the
    last code-side derivation became declared data (AC-10).
    """
    if run.governance_hash is None:
        return
    _, current_hash = governance_pin_for(procedure)
    if current_hash != run.governance_hash:
        raise ProcedureError(
            f"run '{run.run_id}': governance-config pin mismatch at {context} — the "
            f"procedure's governance config (hash {current_hash[:12]}…) no longer matches "
            f"the config this run was started under (hash {run.governance_hash[:12]}…). "
            "Refusing to proceed (PLAN-0047 Step 6 fail-closed): cancel this run and start "
            "a fresh one under the current config; the pinned snapshot on the run row "
            "records exactly which config governed it."
        )


def _assert_sod_tie_present(run: PipelineRun, procedure: Procedure, suspended: StepResult) -> None:
    """PLAN-0047 Step 3 (AC-5): re-assert the SoD verdict before advancing a
    resolved gate on a SoD-carrying run. The ``governed_decision`` audit tie
    ``resolve_gated_step`` records (A1b Step 6) must be present on a
    constrained step; its absence means the gate did not pass through the
    governed resolution path (or the record was tampered) — fail closed."""
    if run.step_principals is None:
        return
    constrained: set[str] = set()
    for sod in procedure.separation_of_duties:
        constrained |= set(sod.distinct_steps)
    if suspended.step_id not in constrained:
        return
    if not (suspended.audit or {}).get("governed_decision"):
        raise ProcedureError(
            f"run '{run.run_id}': resolved step '{suspended.step_id}' is SoD-constrained but "
            "carries no governed_decision audit tie — refusing to resume (PLAN-0047 Step 3 "
            "fail-closed; resolve the gate through resolve_gated_step)"
        )


async def resume_run(
    session: AsyncSession,
    procedure: Procedure,
    agent: Agent,
    executors: Mapping[StepKind, StepExecutor],
    run_id: str,
    *,
    vertical: str,
    principal: Person | None = None,
    service_principal: ServicePrincipal | None = None,
) -> RunResult:
    """Resume a ``waiting_human`` run, reconstructing state purely from the DB.

    Three cases (PLAN-0047 Step 3 — the gate state machine):

    * **Decided proposal gate** (artifact carries real proposals AND the step is
      ``resolved`` — the status :func:`resolve_gated_step` sets): mark it
      ``complete``, thread its rewritten ``artifact["output_set"]`` forward, and
      continue from the NEXT step. A proposal gate still ``waiting_human`` is
      **refused fail-closed** — artifact presence proves nothing (the proposals
      were recorded AT suspend time); on a SoD-carrying run the
      ``governed_decision`` audit tie is re-asserted before advancing.
    * **No-decision suspend** (artifact present but no real proposals — an empty
      watch set / non-proposal ``human_task`` artifact): nothing was decidable,
      so the documented plain-resume continuation holds unchanged.
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
    # PLAN-0047 Step 6 (AC-8): a mid-flight governance edit fails closed here — incl. an
    # edit to a DECLARED derivation (a severity ladder / spend transform), which rides the
    # pin through its step's `transform` key (PLAN-0078 PR-5 retired the AC-13 code-hash).
    assert_governance_pin(run, procedure, context="resume")

    suspended = suspended_step_result(loaded.step_results)
    if suspended is None:
        raise ProcedureError(
            f"run '{run_id}' is waiting_human but no step result is waiting_human or "
            "resolved — the run row and its step results disagree"
        )
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
        # PLAN-0053 AC-3 (SP-4, human path): thread the resolved human through the
        # continuation context. resume_run previously passed NO principal -> the
        # RunContext defaulted to None, so a resumed step's requester-principal
        # recording lost the actor. The HTTP resume call-site passes auth.person.
        principal=principal,
        # PLAN-0053 AC-8 (Phase B): the service actor threads BESIDE the human on a
        # service-triggered resume (None on a human resume; RF-3 keeps them separate).
        service_principal=service_principal,
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
        prior_results = [
            s for s in loaded.step_results if s.step_result_id != suspended.step_result_id
        ]
        start_index = index
    else:
        # PLAN-0047 Step 3 — the gate state machine: a suspend carrying REAL
        # proposals advances ONLY from RESOLVED; a no-decision suspend (empty
        # watch set / non-proposal artifact) keeps the plain-resume contract.
        if _has_decidable_proposals(suspended.artifact):
            if suspended.status != StepResultStatus.RESOLVED.value:
                raise ProcedureError(
                    f"run '{run_id}': step '{suspended.step_id}' suspended with undecided "
                    "proposals — resolve it through resolve_gated_step before resuming "
                    "(PLAN-0047 Step 3 fail-closed; artifact presence no longer advances "
                    "a gate)"
                )
            _assert_sod_tie_present(run, procedure, suspended)
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
        # PLAN-0048 SD-5(a): refusals on the resume path are audited too.
        await _append_read_refusal_audit(session, run_id, step_result)
    # PLAN-0047 Step 5: the resume transition is audited in the same commit.
    # PLAN-0053 AC-3/AC-4: the resume is a HUMAN-driven continuation (the human who
    # resolved the gate) — stamp the resolvable actor + actor_kind so the row is no
    # longer actor-less (SP-4 never-null on resume). Phase B classifies a
    # scheduler-driven resume as actor_kind "service".
    await append_audit(
        session,
        action="run_resumed",
        actor_person_id=principal.person_id if principal is not None else None,
        run_id=run_id,
        step_id=suspended.step_id,
        payload={"final_status": final_status.value, "actor_kind": "human"},
    )
    await session.commit()
    return RunResult(run=run, step_results=prior_results + new_results)


async def cancel_run(
    session: AsyncSession, run: PipelineRun, *, actor_person_id: str | None = None
) -> PipelineRun:
    """Cancel a run parked at a human gate (PLAN-0054 SD-B).

    Sets ``status = cancelled`` + bumps the optimistic-lock version (a concurrent
    resolver/canceller loses cleanly with ``StaleDataError``) and audits
    ``run_cancelled`` with the human actor + ``actor_kind:"human"`` — persist +
    audit in ONE commit (mirrors the ``run_resumed`` idiom). ``actor_person_id`` is
    the AUTHENTICATED canceller's id (``auth.person_id``) — non-null past the
    endpoint's RF-1 guard even in a vertical that authors no ``Person`` set, so the
    cancel is always attributable (cancel has no SoD check, so it needs the id, not
    the resolved ``Person``). The caller enforces cancellability (v1 = only
    ``waiting_human``, SD-B). ``PipelineRunStatus.CANCELLED`` was defined but set by
    no transition until now — this is its first writer.
    """
    run.status = PipelineRunStatus.CANCELLED.value
    run.updated_at = datetime.now(UTC)
    await session.merge(run)
    await append_audit(
        session,
        action="run_cancelled",
        actor_person_id=actor_person_id,
        run_id=run.run_id,
        payload={"actor_kind": "human"},
    )
    await session.commit()
    return run
