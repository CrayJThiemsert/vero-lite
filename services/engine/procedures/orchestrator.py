"""Procedure orchestrator — the linear, set-valued, sequential control plane
(ADR-016 D2/D3/D4; PLAN-0019 Part A, Steps A-3 / A-4 / A-6).

The generic, vertical-agnostic executor that runs a ``Procedure``'s steps in
order. It owns the **control plane** only — sequencing, set-valued threading
(each step's output set becomes the next step's input set), the D3 autonomy
model, the agent blast-radius bound (step-kind + action-handler allowlist), and
D4 fail-and-divert — and delegates each step's actual *work* to a pluggable
:class:`StepExecutor` resolved by ``kind``. Concrete executors are provided by
the caller; the real ``action`` executor (the ADR-007 ``RecommendedAction``
envelope + the approve->execute gate, verbatim) + ``goal`` injection land in a
later step, and durable suspend/resume across a process restart lands in the
next step. This step keeps the run **in-memory**: it builds (but does not
persist) the ``PipelineRun`` / ``StepResult`` records.

Phase-1 scope (L-1): only ``trigger: manual`` is runnable — a ``schedule``
procedure raises rather than running (the scheduler is a deferred PLAN-0010
reuse). A ``gated`` ``action`` step or a ``human_task`` step **suspends** the run
at ``waiting_human`` and the orchestrator returns; resuming the suspended run is
a later step.
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

from services.engine.procedures.draft import (
    unfilled_governance,
    unfilled_procedure_governance,
)
from services.engine.procedures.runs import (
    PipelineRun,
    PipelineRunStatus,
    StepResult,
    StepResultStatus,
)
from services.engine.procedures.spec import (
    Agent,
    Autonomy,
    OnFailure,
    Procedure,
    Step,
    StepKind,
    Trigger,
)


class ProcedureError(Exception):
    """Raised on a configuration / pre-flight violation that makes a procedure
    un-runnable under its agent — a wrong trigger, a step kind or action handler
    outside the agent allowlist, or an autonomy above the agent ceiling.

    Distinct from a *runtime* step failure (which is handled by D4
    fail-and-divert, not raised): a ``ProcedureError`` means the spec + agent
    pairing is invalid, so the run never starts.
    """


@dataclass(frozen=True)
class StepOutcome:
    """What a :class:`StepExecutor` produces for one step.

    ``output`` is the produced object **set** (threaded into the next step as its
    input set). ``reasoning_trace`` + ``audit`` feed the per-step telemetry seam.
    An executor signals failure by **raising** (caught by fail-and-divert), not by
    a flag.
    """

    output: list[Any] = field(default_factory=list)
    reasoning_trace: list[dict[str, Any]] = field(default_factory=list)
    audit: dict[str, Any] | None = None


@dataclass(frozen=True)
class RunContext:
    """Read-only context handed to every executor for one run.

    ``goal`` is the running ``Procedure``'s trusted directive (ADR-016 D5;
    PLAN-0019 A-8) — an LLM-backed executor (``evaluate`` / ``action`` reasoning)
    passes it to :func:`generate_judgment` so it steers the system prompt. It is
    ``None`` when the procedure declares no goal.
    """

    agent: Agent
    vertical: str
    trigger_context: dict[str, Any] | None = None
    goal: str | None = None


class StepExecutor(Protocol):
    """Does the actual work of one step. The orchestrator owns control flow;
    the executor owns the step's domain work (read, judgment, write, human task).
    """

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome: ...


@dataclass(frozen=True)
class RunResult:
    """The in-memory result of a run: the ``PipelineRun`` record + its per-step
    ``StepResult`` records (unpersisted — a later step adds persistence)."""

    run: PipelineRun
    step_results: list[StepResult]


_AUTONOMY_RANK = {Autonomy.GATED: 0, Autonomy.AUTO: 1}
"""Autonomy ordering for the ceiling check: ``gated`` < ``auto`` (``auto`` is the
*more* autonomous — it acts without a human gate). ``autonomy_ceiling`` is the
MAX a step may exercise, so a step is allowed iff rank(step) <= rank(ceiling)."""


def validate_runnable(procedure: Procedure, agent: Agent) -> None:
    """Raise :class:`ProcedureError` unless ``procedure`` is runnable under ``agent``.

    Enforces (ADR-016 D3): only ``manual`` trigger runs in Phase 1 (L-1); every
    step kind is within the agent's ``allowed.step_kinds`` (an **empty** list is
    unconstrained — kinds are the coarse filter); every ``action`` step's
    autonomy is at or below ``autonomy_ceiling``; and every ``action`` step's
    named ``handler`` is in ``allowed.action_handlers`` (the fine blast-radius
    bound — an **empty** handler list therefore admits no handler-bearing action).
    """
    if procedure.trigger is not Trigger.MANUAL:
        raise ProcedureError(
            f"procedure '{procedure.procedure_id}': trigger '{procedure.trigger.value}' is not "
            "runnable in Phase 1 — only 'manual' (schedule is a deferred PLAN-0010 reuse, L-1)"
        )
    # ADR-0024 D6 / OQ-1: a generated skeleton LOADS (load_procedures = shape only)
    # but must NOT RUN until a human authors its gates. Safe-defaults alone do not make
    # a skeleton un-runnable — a stub action with handler=None passes the handler guard
    # below, and autonomy defaults to `gated` so a stub LOOKS authored — so an explicit
    # stub-rejecting check is required.
    validate_governance_complete(procedure)
    allowed_kinds = set(agent.allowed.step_kinds)
    ceiling = _AUTONOMY_RANK[agent.autonomy_ceiling]
    seen_ids: set[str] = set()
    for step in procedure.steps:
        # Named-input references must be LINEAR — a step may only consume the output
        # of an EARLIER step (no forward / unknown references). Caught at pre-flight
        # so a bad reference fails the run before it starts, not mid-execution.
        if step.input is not None and step.input.from_step is not None:
            if step.input.from_step not in seen_ids:
                raise ProcedureError(
                    f"step '{step.step_id}': input.from '{step.input.from_step}' is not an "
                    "earlier step (named-input references must be linear / backward)"
                )
        seen_ids.add(step.step_id)
        if allowed_kinds and step.kind not in allowed_kinds:
            raise ProcedureError(
                f"step '{step.step_id}': kind '{step.kind.value}' is outside agent "
                f"'{agent.agent_id}' allowed.step_kinds {sorted(k.value for k in allowed_kinds)}"
            )
        if step.kind is not StepKind.ACTION:
            continue
        if step.autonomy is not None and _AUTONOMY_RANK[step.autonomy] > ceiling:
            raise ProcedureError(
                f"step '{step.step_id}': autonomy '{step.autonomy.value}' exceeds agent "
                f"'{agent.agent_id}' autonomy_ceiling '{agent.autonomy_ceiling.value}'"
            )
        if step.handler is not None and step.handler not in agent.allowed.action_handlers:
            raise ProcedureError(
                f"step '{step.step_id}': handler '{step.handler}' is outside agent "
                f"'{agent.agent_id}' allowed.action_handlers {agent.allowed.action_handlers}"
            )


def validate_governance_complete(procedure: Procedure) -> None:
    """Raise :class:`ProcedureError` if any step carries an unfilled governance stub
    (ADR-0024 D6 / OQ-1; PLAN-0040 Step A4).

    The D6 two-state gate: a generated skeleton is **draft-loadable** (``load_procedures``
    validates shape + cross-refs only) but must be **NOT run-loadable** until a human
    authors the gates. Re-derives each step's obligation set from ``(gate_kind, kind)``
    via :func:`unfilled_governance` — it does NOT trust a stored worklist — and raises
    on the first step with an unfilled obligation (a ``handler`` on an ``action``; the
    band value on a ``judge``). Closes the verified hole: a stub ``action`` with
    ``handler=None`` passes the ``validate_runnable`` handler guard, and ``autonomy``
    defaults to ``gated`` so a stub *looks* authored — safe-defaults alone do not make a
    skeleton un-runnable. Invoked by :func:`validate_runnable`.

    A complete (hand-authored) procedure raises nothing — every shipped vertical's
    procedures pass unchanged (the generator-support layer adds a gate, not a new
    constraint on authored specs).

    **AT-2 awareness (ADR-0025 D5):** a step on an AT-2 gate kind
    (``scored_rule`` / ``rule_gate`` / ``doa_tier``) also owes its typed
    ``governance_content`` (re-derived per step above), and a ``doa_tier``-bearing
    procedure owes a ``separation_of_duties`` constraint (the procedure-level check
    below). This closes the run-gate's AT-2 blindness — an empty-DOA / no-criteria /
    no-compliance-rule / no-SoD AT-2 procedure is no longer judged run-loadable."""
    for step in procedure.steps:
        missing = unfilled_governance(step)
        if missing:
            raise ProcedureError(
                f"step '{step.step_id}': unfilled governance stub(s) {missing} — a generated "
                f"skeleton is draft-loadable but NOT run-loadable until a human authors the "
                f"gates (ADR-0024 D6 / OQ-1; AT-2 content per ADR-0025 D5)"
            )
    proc_missing = unfilled_procedure_governance(procedure)
    if proc_missing:
        raise ProcedureError(
            f"procedure '{procedure.procedure_id}': unfilled procedure-level governance "
            f"{proc_missing} — a doa_tier procedure requires a separation_of_duties "
            f"constraint (ADR-0025 D5)"
        )


def _suspends(step: Step) -> bool:
    """Whether this step suspends the run at ``waiting_human`` — a ``gated`` action
    (the human go/no-go) or a ``human_task``.

    SAFETY: for a ``gated`` action the executor must only *propose* (produce the
    ``RecommendedAction`` at status ``proposed``) and must NOT perform the
    irreversible write before approval. That invariant is enforced by the ADR-007
    approve->execute gate (``execute`` requires ``approved``), not by the
    orchestrator; the write runs on resume after a human approves.
    """
    if step.kind is StepKind.HUMAN_TASK:
        return True
    return step.kind is StepKind.ACTION and step.autonomy is Autonomy.GATED


def _matches(entity: Any, where: Mapping[str, Any]) -> bool:
    """True iff ``entity`` is a mapping with ``entity[field] == value`` for EVERY
    pair in ``where`` (the field-equality fan-out filter). A non-mapping entity
    has no fields, so it never matches."""
    if not isinstance(entity, Mapping):
        return False
    return all(entity.get(field) == value for field, value in where.items())


def _resolve_input(
    step: Step, outputs: Mapping[str, list[Any]], prev_step_id: str | None
) -> list[Any]:
    """Resolve a step's input set from the named-output bag (PLAN-0019 A-ζ-prep).

    ``input.from`` names the source step (default = the immediately prior step,
    ``prev_step_id``); ``input.where`` narrows it by field-equality. A reference to
    a step with no recorded output (it suspended / failed before producing one)
    resolves to the empty set. References are pre-validated linear by
    :func:`validate_runnable`, so ``from`` always names an earlier step.
    """
    spec_input = step.input
    if spec_input is not None and spec_input.from_step is not None:
        base: list[Any] = list(outputs.get(spec_input.from_step, []))
    elif prev_step_id is not None:
        base = list(outputs.get(prev_step_id, []))
    else:
        base = []
    if spec_input is not None and spec_input.where:
        base = [entity for entity in base if _matches(entity, spec_input.where)]
    return base


def _make_step_result(
    run_id: str,
    step: Step,
    status: StepResultStatus,
    started_at: datetime,
    duration_ms: int,
    *,
    artifact: dict[str, Any] | None,
    reasoning_trace: list[dict[str, Any]],
    audit: dict[str, Any] | None,
) -> StepResult:
    return StepResult(
        step_result_id=f"{run_id}:{step.step_id}",
        run_id=run_id,
        step_id=step.step_id,
        status=status.value,
        duration_ms=duration_ms,
        artifact=artifact,
        reasoning_trace=reasoning_trace,
        audit=audit,
        created_at=started_at,
    )


async def run_procedure(
    procedure: Procedure,
    agent: Agent,
    executors: Mapping[StepKind, StepExecutor],
    *,
    vertical: str,
    run_id: str,
    trigger_context: dict[str, Any] | None = None,
) -> RunResult:
    """Run ``procedure`` under ``agent`` over the given per-kind ``executors``.

    Validates runnability first (raises :class:`ProcedureError`), then executes
    steps linearly: each step's output set is threaded into the next step; a
    ``gated`` action or ``human_task`` suspends the run at ``waiting_human`` and
    returns; a raising executor triggers D4 fail-and-divert (the run aborts —
    ``failed``, or ``waiting_human`` when ``on_failure = escalate_to_human``).
    Every step records a ``StepResult`` carrying the telemetry seam.

    The orchestrator threads the FULL prior output set into the next step; a
    step's ``input`` / ``output`` are executor-interpreted hints (any per-entity
    narrowing — e.g. the breach subset — is the executor's job, not the engine's).
    On suspend, the suspended step's output set is preserved in
    ``StepResult.artifact["output_set"]`` so a later resume can thread it forward.
    A misbehaving executor (raising, or returning a non-``StepOutcome``) is
    diverted via fail-and-divert, never crashing the run loop.
    """
    validate_runnable(procedure, agent)

    opened = datetime.now(UTC)
    run = PipelineRun(
        run_id=run_id,
        procedure_id=procedure.procedure_id,
        agent_id=agent.agent_id,
        trigger_context=trigger_context,
        status=PipelineRunStatus.RUNNING.value,
        started_at=opened,
        updated_at=opened,
    )
    ctx = RunContext(
        agent=agent,
        vertical=vertical,
        trigger_context=trigger_context,
        goal=procedure.goal or None,
    )
    step_results, final_status = await execute_steps(procedure.steps, executors, ctx, run_id)
    run.status = final_status.value
    run.updated_at = datetime.now(UTC)
    return RunResult(run=run, step_results=step_results)


async def execute_steps(
    steps: list[Step],
    executors: Mapping[StepKind, StepExecutor],
    ctx: RunContext,
    run_id: str,
    *,
    prior_outputs: Mapping[str, list[Any]] | None = None,
    start_index: int = 0,
) -> tuple[list[StepResult], PipelineRunStatus]:
    """Run ``steps[start_index:]`` over ``executors`` against a named-output bag.

    The shared control-plane core used by both :func:`run_procedure` (from step 0,
    empty bag) and resume (from a given index with the bag rebuilt from the DB).
    Each step's input set is resolved from the bag via its ``input`` spec
    (:func:`_resolve_input`) — a named prior step (default: the immediately prior
    one) narrowed by an optional field-equality ``where`` filter — and each step's
    output is recorded back into the bag under its ``step_id`` so a LATER step can
    reference it (the breach/watch/ok fan-out). Returns the new ``StepResult``s +
    the resulting run status; it does NOT create or persist the ``PipelineRun``.
    """
    engine_audit: dict[str, Any] = {"actor": ctx.agent.agent_id, "actor_kind": "engine"}
    step_results: list[StepResult] = []
    outputs: dict[str, list[Any]] = dict(prior_outputs) if prior_outputs else {}
    final_status = PipelineRunStatus.COMPLETED
    prev_step_id = steps[start_index - 1].step_id if start_index > 0 else None

    for step in steps[start_index:]:
        executor = executors.get(step.kind)
        if executor is None:
            raise ProcedureError(
                f"step '{step.step_id}': no executor registered for kind '{step.kind.value}'"
            )
        input_set = _resolve_input(step, outputs, prev_step_id)
        started_at = datetime.now(UTC)
        t0 = time.perf_counter()
        try:
            outcome = await executor.execute(step, input_set, ctx)
            if not isinstance(outcome, StepOutcome):
                # A misbehaving executor (wrong return type) is diverted, not
                # crashed: the orchestrator never lets one executor take down the
                # whole run loop. Funnel it into the same fail-and-divert path.
                raise TypeError(
                    f"step executor returned {type(outcome).__name__}, expected StepOutcome"
                )
        except Exception as exc:  # fail-and-divert catches ANY step failure (D4)
            duration_ms = int((time.perf_counter() - t0) * 1000)
            # D4: escalate_to_human routes the STEP (and the run) to waiting_human
            # instead of failed — a human takes over rather than the run dying.
            escalate = step.on_failure is OnFailure.ESCALATE_TO_HUMAN
            step_results.append(
                _make_step_result(
                    run_id,
                    step,
                    StepResultStatus.WAITING_HUMAN if escalate else StepResultStatus.FAILED,
                    started_at,
                    duration_ms,
                    artifact=None,
                    reasoning_trace=[{"kind": "error", "summary": f"{type(exc).__name__}: {exc}"}],
                    audit=engine_audit,
                )
            )
            final_status = PipelineRunStatus.WAITING_HUMAN if escalate else PipelineRunStatus.FAILED
            break

        duration_ms = int((time.perf_counter() - t0) * 1000)
        suspends = _suspends(step)
        step_results.append(
            _make_step_result(
                run_id,
                step,
                StepResultStatus.WAITING_HUMAN if suspends else StepResultStatus.COMPLETE,
                started_at,
                duration_ms,
                artifact={"output_set": outcome.output},
                reasoning_trace=outcome.reasoning_trace,
                audit=outcome.audit or engine_audit,
            )
        )
        outputs[step.step_id] = outcome.output
        if suspends:
            final_status = PipelineRunStatus.WAITING_HUMAN
            break
        prev_step_id = step.step_id

    return step_results, final_status
