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
from services.engine.procedures.ratification import RATIFICATION_KEY
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

    Ordered by ``seq`` — the database-assigned insertion key added in migration
    ``0023`` (PLAN-0099 D3). This used to order by ``created_at``, a wall-clock stamp
    that is not monotonic: a backward step (an NTP correction, a VM/WSL2 host resync;
    measured on this box at >= 400 ms roughly every 15 s) stamps a later step with an
    earlier time, and the run then reads back out of the order it actually executed
    in. Execution order IS insertion order, and ``seq`` says so directly instead of
    inferring it from a clock.

    ``step_result_id`` is retained as a tiebreak although ``seq`` is UNIQUE, so that
    the order stays total if a future writer ever assigns ``seq`` explicitly.

    Even so, never infer *which* step a run is suspended at from this order — use
    :func:`suspended_step_result`, which reads the STATUS. That rule is about
    expressing intent, not about distrusting the ordering (SD-4).
    """
    run = await session.get(PipelineRun, run_id)
    if run is None:
        return None
    rows = await session.execute(
        select(StepResult)
        .where(StepResult.run_id == run_id)
        .order_by(StepResult.seq, StepResult.step_result_id)
    )
    return RunResult(run=run, step_results=list(rows.scalars().all()))


# The statuses a not-yet-resumed step can hold: ``waiting_human`` (suspended at
# a gate, or escalated on failure with no artifact), ``resolved`` (its gate was
# decided; awaiting the resume that threads the decision forward), and
# ``resolved_provisional`` (decided FIRST under an authored ratification window —
# ADR-0034 D3(5); the run advances on it exactly as on ``resolved``, because the
# effects have already executed and holding the run hostage to a signature that is
# days out is the precise thing decide-first exists to avoid). Every other step of
# a resumable run is ``complete``, so exactly one step matches.
_UNRESUMED_STATUSES = frozenset(
    {
        StepResultStatus.WAITING_HUMAN.value,
        StepResultStatus.RESOLVED.value,
        StepResultStatus.RESOLVED_PROVISIONAL.value,
    }
)

# The statuses that advance a decidable gate. Provisional is here for the reason above;
# the outstanding obligation rides the step audit and stays queryable after the step is
# marked ``complete`` (ADR-0034 D3(6)), so advancing does not lose it.
_ADVANCING_STATUSES = frozenset(
    {StepResultStatus.RESOLVED.value, StepResultStatus.RESOLVED_PROVISIONAL.value}
)


def suspended_step_result(step_results: list[StepResult]) -> StepResult | None:
    """The step a ``waiting_human`` run is suspended at — identified by STATUS.

    Never by list position — and the rule is RETAINED now that :func:`load_run` orders
    by the monotonic ``seq`` rather than by ``created_at`` (PLAN-0099 D3 discharges the
    deferral; SD-4 keeps this rule with a rewritten rationale). Selecting by STATUS
    expresses what the caller actually means — "the step a human has not yet decided"
    — whereas selecting by position means it only as long as the ordering happens to
    agree. The static guard in
    ``tests/services/db/test_load_run_ordering_guard.py`` still forbids the positional
    read across the tree.

    What the wall clock used to cost, kept as the reason the rule exists: a backward
    step between two steps of one run sorted the later one first, ``step_results[-1]``
    then named a *completed* step, and resuming from it re-ran an already-executed
    gate (duplicate side effects) or failed closed on its undecided proposals.

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
    audit = suspended.audit or {}
    # A PROVISIONAL resolution satisfies this guard through its attestation block instead of a
    # tie (ADR-0034 D3(2)/D3(5)). The guard's purpose is to prove the gate came through the
    # governed resolution path rather than being written directly — and the ratification block
    # is written by exactly one code path, the provisional branch of ``resolve_gated_step``,
    # which runs the SAME live SoD check before it. So the evidence is equally strong; demanding
    # a `governed_decision` here instead would demand the one thing the ADR deliberately
    # withholds until ratification, and no provisional run could ever advance.
    if not audit.get("governed_decision") and not audit.get(RATIFICATION_KEY):
        raise ProcedureError(
            f"run '{run.run_id}': resolved step '{suspended.step_id}' is SoD-constrained but "
            "carries neither a governed_decision audit tie nor a provisional ratification "
            "attestation — refusing to resume (PLAN-0047 Step 3 fail-closed; resolve the gate "
            "through resolve_gated_step)"
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
            if suspended.status not in _ADVANCING_STATUSES:
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


class NoDecisionApproverError(ProcedureError):
    """RF-1 refusal from the PLAN-0114 continue seam: no identified human acknowledger.

    Defined HERE, not reused from ``action_step.GateApproverError``, and not added to
    ``orchestrator.py`` beside :class:`ProcedureError` — both of which look like the
    tidier home and are both wrong:

    * ``action_step`` already imports FROM this module (``assert_governance_pin``,
      ``load_run``), so importing its exception back would be a circular import.
    * ``orchestrator.py`` must stay byte-identical under PLAN-0114 AC-4, which is how
      that AC proves ``_suspends`` was never touched. Adding a class there would
      dirty the very diff the AC reads.

    A ``ProcedureError`` subclass, so any caller already mapping ``ProcedureError``
    keeps working; the HTTP layer maps this arm to 403 rather than 409.
    """


#: The gate step's own ``audit`` key carrying the PLAN-0114 acknowledgment (SD-2 level 2).
NO_DECISION_ACK_KEY = "no_decision_continuation"


def _no_decision_acknowledgment(
    *,
    actor_person_id: str,
    acknowledged_at: datetime,
    step_id: str,
    proposal_count: int,
    vertical: str,
    procedure: Procedure,
    governance_hash: str | None,
    step_results: list[StepResult],
) -> dict[str, Any]:
    """The acknowledgment block written into the gate step's own ``audit`` dict.

    SD-2 level 2 (ruled: dual audit). The chain row is tamper-evidence; THIS is the
    half a human reads, through surfaces that already exist — the run detail
    (``GET /runs/{run_id}``) and the monitor's "Show audit" toggle. PLAN-0113 SD-3's
    artifact argument is the acceptance test: a later reader must be able to
    reconstruct *"checked — nothing to approve, acknowledged by X"*, not merely
    *"completed"*.

    **Why the procedure's shape is REFERENCED, not copied (Cray, s253).** The obvious
    way to make the block self-describing is to embed the vertical's procedure shape.
    The engine already builds exactly that — :func:`build_governance_snapshot` pins
    ``procedure_id``, ``separation_of_duties`` and every step's ``step_id`` / ``kind``
    / ``autonomy`` / ``handler`` / ``governance_content`` / ``reads`` / ``join`` /
    ``project`` (plus ``transform`` / ``scope_by`` / ``when_absent`` when supplied) —
    and persists it per run on ``PipelineRun.governance_snapshot`` with
    ``governance_hash`` as its fingerprint. Copying it here would duplicate a record
    that can then disagree with itself, and would bloat every gate's step row. So the
    block carries the HASH: the acknowledgment is tied to the exact governed shape
    that produced it, tamper-evidently, in one string.

    **But a hash is not retrieval.** ``governance_snapshot`` and ``governance_hash``
    appear NOWHERE in ``services/api/`` (measured, s253) — the pin is recorded and not
    fetchable over HTTP. A reader holding only the API therefore cannot resolve step
    ids against it. That is why ``upstream`` entries are self-describing (``step_id`` +
    declared ``kind`` + ``output_count``) rather than being left to a snapshot lookup:
    the block must read correctly on the surface SD-2 actually chose. The hash serves
    the reader who DOES have the run row, and this block is the first place the pin is
    exposed on a retrievable surface at all.

    Universal across verticals by construction: every field comes from data the engine
    holds for every vertical — no per-vertical branch, nothing authored per procedure.
    """
    kinds = {step.step_id: step.kind.value for step in procedure.steps}
    upstream: list[dict[str, Any]] = []
    for result in step_results:
        if result.step_id == step_id:
            break
        artifact = result.artifact or {}
        upstream.append(
            {
                "step_id": result.step_id,
                "kind": kinds.get(result.step_id),
                "output_count": len(artifact.get("output_set", []))
                if "output_set" in artifact
                else None,
            }
        )
    return {
        "acknowledged_by": actor_person_id,
        "acknowledged_at": acknowledged_at.isoformat(),
        "step_id": step_id,
        "proposal_count": proposal_count,
        "vertical": vertical,
        # The tie to PipelineRun.governance_snapshot — which config shape governed the
        # run this was acknowledged on. None only on a pre-pin / legacy run row.
        "governance_hash": governance_hash,
        "upstream": upstream,
    }


async def continue_no_decision_run(
    session: AsyncSession,
    procedure: Procedure,
    agent: Agent,
    executors: Mapping[StepKind, StepExecutor],
    run_id: str,
    step_id: str,
    *,
    vertical: str,
    actor_person_id: str | None,
    principal: Person | None = None,
) -> RunResult:
    """Acknowledge a gate holding nothing decidable, then continue the run (PLAN-0114).

    PLAN-0113 SD-3 ruled (b): a run whose gate carries nothing decidable must reach
    ``completed`` rather than sit unresolvable. The engine already sanctions that exit
    — :func:`resume_run`'s no-decision branch completes such a run on a plain resume
    (PLAN-0022 parity) — but nothing on the product surface could reach it, because
    ``/gate/resolve`` raises on an empty ``output_set`` before ``resume_run`` is called.
    This is the missing chokepoint, and the ONLY surface PLAN-0114 exposes.

    It decides nothing. It records that an accountable human LOOKED at a gate with no
    proposals and found nothing to approve, then delegates. ``_suspends``,
    ``resolve_gated_step`` and ADR-0016 D4 are untouched — the gated step still
    suspends at ``waiting_human`` and the run still resumes when the human acts; the
    act is an acknowledgment instead of an approval.

    Fails CLOSED five ways, each one its own probe in the Step 1 battery:

    * **RF-1** — ``actor_person_id is None`` -> :class:`GateApproverError`. Keyed on the
      ID, mirroring :func:`cancel_run`, NOT on a resolved ``Person``. SD-3 ruled the
      cancel posture ("any authenticated human"), and ``auth.person`` is ``None`` in any
      vertical shipping no ``principals:`` block — 2 of 6 today (aquaculture, energy),
      carrying 3 of the 18 gated steps. A ``Person``-keyed guard would refuse those
      permanently, which is a defect rather than a floor. A service actor cannot be
      recorded here by construction: this seam takes no ``service_principal`` at all.
    * **not parked** — a run whose status is not ``waiting_human`` has no gate to
      acknowledge.
    * **step mismatch** — the caller names the step they believe they are acknowledging;
      a mismatch with the actually-suspended step means the run moved between the read
      and the POST. (Concurrent WRITERS are covered as today, by the optimistic lock.)
    * **escalated failure** — ``artifact is None`` is the ``on_failure =
      escalate_to_human`` suspend. Its honest exit is a *retry*, a different semantic
      (``resume_run`` would re-run the failed step). Out of scope, recorded as OQ-1.
    * **decidable proposals** — the security boundary. Because SD-3 admits any
      authenticated human, this guard is what stops ``/continue`` being a resolve
      bypass. Note the refusal names its OWN mechanism: ``resume_run`` carries an
      independent second guard that refuses the same case with a different message, so
      a caller (or a test) must be able to tell the two layers apart.
    """
    # RF-1 first: no accountable human means nothing else is worth doing, and the
    # refusal must not depend on the run loading successfully.
    if actor_person_id is None:
        raise NoDecisionApproverError(
            f"run '{run_id}': acknowledging a gate requires an identified human "
            "(ADR-016 S2 RF-1, PLAN-0114 SD-3 the cancel posture); none was supplied"
        )

    loaded = await load_run(session, run_id)
    if loaded is None:
        raise ProcedureError(f"run '{run_id}' not found")
    if loaded.run.status != PipelineRunStatus.WAITING_HUMAN.value:
        raise ProcedureError(
            f"run '{run_id}' is not parked at a gate — status "
            f"'{loaded.run.status}' (expected waiting_human); there is nothing to "
            "acknowledge"
        )

    # Exactly-one is enforced inside; a run with two unresumed steps raises rather
    # than letting us guess which gate the human meant.
    suspended = suspended_step_result(loaded.step_results)
    if suspended is None:
        raise ProcedureError(
            f"run '{run_id}' is waiting_human but carries no unresumed step result — "
            "the persisted run is inconsistent and cannot be acknowledged"
        )
    if suspended.step_id != step_id:
        raise ProcedureError(
            f"run '{run_id}': step '{step_id}' is not the step this run is suspended "
            f"at (that is '{suspended.step_id}') — reload the run and retry"
        )

    if suspended.artifact is None:
        raise ProcedureError(
            f"run '{run_id}': step '{step_id}' is an escalated FAILURE suspend, not a "
            "no-decision gate — it carries no artifact. Its exit is a retry, not an "
            "acknowledgment (PLAN-0114 OQ-1); acknowledging it would record that a "
            "broken step was 'checked and cleared'"
        )

    if _has_decidable_proposals(suspended.artifact):
        raise ProcedureError(
            f"run '{run_id}': step '{step_id}' holds decidable proposals — resolve it "
            "through resolve_gated_step. The continue seam acknowledges an EMPTY gate "
            "and is never a resolve bypass (PLAN-0114 fail-closed guard 1)"
        )

    proposal_count = len(suspended.artifact.get("output_set", []))

    # SD-2 level 2: the human-readable half, on the step's own audit dict. Reassign
    # rather than mutating in place — `audit` is a JSON column and an in-place mutation
    # is not seen by the session (the house idiom, mirroring resolve_gated_step's
    # `governed_decision` write).
    suspended.audit = {
        **(suspended.audit or {}),
        NO_DECISION_ACK_KEY: _no_decision_acknowledgment(
            actor_person_id=actor_person_id,
            acknowledged_at=datetime.now(UTC),
            step_id=step_id,
            proposal_count=proposal_count,
            vertical=vertical,
            procedure=procedure,
            governance_hash=loaded.run.governance_hash,
            step_results=loaded.step_results,
        ),
    }
    await session.merge(suspended)

    # SD-2 level 1: the tamper-evident chain row, beside the `run_resumed` row
    # resume_run appends. `audit_log` treats `action` as an opaque string, so this
    # rides the existing chain without touching GET /audit/verify.
    await append_audit(
        session,
        action="run_continued_no_decision",
        actor_person_id=actor_person_id,
        run_id=run_id,
        step_id=step_id,
        payload={"proposal_count": proposal_count, "actor_kind": "human"},
    )
    await session.commit()

    # Delegate to the engine's OWN sanctioned exit. `principal` is threaded when it
    # resolves so PLAN-0053 AC-3's non-null `run_resumed` actor is preserved wherever
    # it can hold; attribution never depends on it, because the chain row above always
    # carries the id.
    return await resume_run(
        session,
        procedure,
        agent,
        executors,
        run_id,
        vertical=vertical,
        principal=principal,
    )
