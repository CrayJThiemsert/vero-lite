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

from services.engine.ontology_meta import load_ontology_meta
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
    Person,
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

    ``principal`` is the resolved HUMAN principal on the approval path (ADR-0026
    D3, OQ-2 — the *ambient* resolution; the *load-bearing* "who approved THIS
    gate" is the explicit ``principal`` arg on :func:`resolve_gated_step`). It is
    the typed identity carrier the principal-SoD run-check consumes — NOT the
    untyped ``trigger_context`` blob (rejected as the carrier, OQ-2). ``None``
    until a principal is resolved.
    """

    agent: Agent
    vertical: str
    trigger_context: dict[str, Any] | None = None
    goal: str | None = None
    principal: Person | None = None


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


def has_read_bindings(procedure: Procedure) -> bool:
    """True iff any ``query`` step declares a typed read binding (``input.reads``).

    The read-binding gate's trigger predicate: a reads-absent procedure (every
    shipped vertical today) never invokes the gate at all — and, via
    :func:`validate_read_bindings_for_vertical`, never loads the ontology
    registry either (ADR-016 Q3 OQ-6 backward-compat).
    """
    return any(
        step.kind is StepKind.QUERY and step.input is not None and bool(step.input.reads)
        for step in procedure.steps
    )


def validate_read_bindings(
    procedure: Procedure, agent: Agent, object_type_names: frozenset[str]
) -> None:
    """Raise :class:`ProcedureError` unless every ``query`` step's ``input.reads``
    is consistent with the ontology AND the agent's read allowlist.

    The ADR-016 Q3 **load-time consistency & scoping gate** (PLAN-0046 Step 2,
    SD-1 = a separate entry point beside :func:`validate_runnable`, whose
    ``(procedure, agent)`` signature is untouched): each object_type a query step
    declares MUST (a) exist in the vertical's ontology (``object_type_names``)
    AND (b) — when the agent opts in with a non-empty ``allowed.object_types``
    (OQ-6: empty = unconstrained, mirroring ``step_kinds``, NOT
    ``action_handlers``' fail-closed) — be inside that read allowlist. Mirrors
    the write-side ``action_handlers`` pre-flight bound. Enforcement status
    (the ADR's honest frame): declared ✔ · consistency-gated at load ✔ ·
    execution-bound ✖ — execution-binding arrives with the Q4 generic executor
    (a separate PLAN). Pure: the caller supplies the registry — no filesystem
    I/O here (testable with a fixture registry).
    """
    allowed_object_types = agent.allowed.object_types
    for step in procedure.steps:
        if step.kind is not StepKind.QUERY or step.input is None or not step.input.reads:
            continue
        for object_type in step.input.reads:
            if object_type not in object_type_names:
                raise ProcedureError(
                    f"step '{step.step_id}': reads object_type '{object_type}' does not "
                    f"exist in the vertical's ontology (ADR-016 Q3 load-gate)"
                )
            if allowed_object_types and object_type not in allowed_object_types:
                raise ProcedureError(
                    f"step '{step.step_id}': reads object_type '{object_type}' is outside "
                    f"agent '{agent.agent_id}' allowed.object_types {allowed_object_types}"
                )


def validate_read_bindings_for_vertical(procedure: Procedure, agent: Agent, vertical: str) -> None:
    """Build the vertical's object-type registry and run the read-binding gate.

    The production pre-flight wrapper (PLAN-0046 AC-7): threads
    ``load_ontology_meta(vertical)`` — the call-sites already own the vertical
    string — into the pure :func:`validate_read_bindings`. **Skipped entirely
    (no ontology I/O) when no query step declares** ``reads`` (OQ-6
    backward-compat: every shipped procedure is reads-absent, so existing runs
    are byte-identical and never touch the ontology loader).
    """
    if not has_read_bindings(procedure):
        return
    meta = load_ontology_meta(vertical)
    validate_read_bindings(procedure, agent, frozenset(m.name for m in meta.object_types))


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
    no-compliance-rule / no-SoD AT-2 procedure is no longer judged run-loadable.

    **AC-9 (ADR-0026 D6 hard guarantee 2 / red-team Attack-5; PLAN-0044):** an AT-2
    procedure may not run an ``autonomy: auto`` OPERATIONAL action downstream of a gate
    — the un-gated-audit / bypass surface — with a verified no-op audit-receipt terminal
    exempt (:func:`_check_no_auto_downstream_of_gate`, Option 2)."""
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
    _check_no_auto_downstream_of_gate(procedure)


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


_AUDIT_TERMINAL_HANDLERS = frozenset({"echo"})
"""The verified no-op / audit-receipt handlers EXEMPT from the AC-9 auto-downstream-of-a-gate
guarantee (ADR-0026 D6 hard guarantee 2; PLAN-0044 AC-9, Option 2). An ``autonomy: auto`` step
downstream of a gate is a bypass surface only if it performs an OPERATIONAL action; a step whose
handler is a known side-effect-free receipt (``echo`` — the cross-vertical no-op audit handler in
``verticals/*/handlers.py``) merely RECORDS the decision, so it is allowed to run auto after a
gate. The exemption is tied to the VERIFIED handler name — forge-proof: routing an operational
action through ``echo`` yields a no-op, and any other handler is NOT exempt — NEVER to an author's
self-declaration. Instance-scoped / provisional-until-N>=2: a second vertical's distinct audit
handler EXTENDS this set (mirroring the AT-2 content instance-scoping, ADR-0025)."""


def _is_at2_procedure(procedure: Procedure) -> bool:
    """Whether ``procedure`` carries AT-2 managerial governance (ADR-0025 D2) — typed
    ``governance_content`` on some step (a DOA ladder / scored rule / compliance gate) or a
    ``separation_of_duties`` constraint. AC-9 (below) is scoped to AT-2 procedures — the
    red-team Attack-5 surface (PLAN-0044 AC-9)."""
    return bool(procedure.separation_of_duties) or any(
        step.governance_content is not None for step in procedure.steps
    )


def _check_no_auto_downstream_of_gate(procedure: Procedure) -> None:
    """Raise :class:`ProcedureError` if an AT-2 procedure runs an ``autonomy: auto`` OPERATIONAL
    action downstream of a gate (AC-9 — ADR-0026 D6 hard guarantee 2 / red-team Attack-5).

    A human gate (a ``gated`` action / ``human_task``, per :func:`_suspends`) exists to impose
    oversight; an ``auto`` action that runs AFTER it would act un-attended, bypassing that
    oversight. **Option 2 exemption (Cray, session 92):** a step whose handler is a VERIFIED no-op
    audit-receipt (:data:`_AUDIT_TERMINAL_HANDLERS`) only RECORDS the decision — it does not act —
    so it may run auto after a gate (the authoritative, non-omittable audit is the engine-emitted
    ``governed_decision`` side-effect, A1b Step 6; this exempt terminal is a cosmetic receipt).
    The exemption is verified against the handler name, never an author flag. Non-AT-2 procedures
    are out of scope (PLAN-0044 AC-9). Invoked by :func:`validate_governance_complete`, so a
    violating AT-2 procedure is NOT run-loadable."""
    if not _is_at2_procedure(procedure):
        return
    seen_gate = False
    for step in procedure.steps:
        if _suspends(step):
            seen_gate = True
            continue
        if (
            seen_gate
            and step.kind is StepKind.ACTION
            and step.autonomy is Autonomy.AUTO
            and step.handler not in _AUDIT_TERMINAL_HANDLERS
        ):
            raise ProcedureError(
                f"step '{step.step_id}': an autonomy:auto action (handler '{step.handler}') is "
                f"downstream of a gate in an AT-2 procedure — an unattended operational action "
                f"after a human gate is a bypass surface (ADR-0026 D6 hard guarantee 2 / red-team "
                f"Attack-5; PLAN-0044 AC-9). Only a verified no-op audit-receipt handler "
                f"{sorted(_AUDIT_TERMINAL_HANDLERS)} may run auto after a gate (it records, it "
                f"does not act) — gate the step, move it before the gate, or route it through the "
                f"audit handler."
            )


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


def _record_requester_principals(
    procedure: Procedure,
    step_results: list[StepResult],
    principal: Person | None,
) -> dict[str, str | None] | None:
    """The REQUESTER half of the SoD ``step_principals`` map (ADR-0026 D4; PLAN-0044
    A1b Step 1, SD-2=(a)).

    For each SoD-constrained step the run **completed**, record the ambient acting
    principal's ``person_id`` — sourced from the typed ``RunContext.principal`` seam,
    NEVER the untyped ``trigger_context`` blob (OQ-2). ``None`` when no principal was
    resolved (the run-check then fails closed, AC-3). The gated approver step suspends
    at ``waiting_human`` before its human acts, so its principal is recorded later by
    :func:`resolve_gated_step`, not here.

    Returns ``None`` for a procedure with **no** SoD constraint (the live check stays
    inert), and a dict (possibly empty, if no constrained step completed yet) when the
    procedure HAS a constraint — so ``run.step_principals is not None`` is the durable
    "this run carried SoD" signal the gate resolution relies on (non-skippable, AC-2).
    """
    constrained: set[str] = set()
    for sod in procedure.separation_of_duties:
        constrained |= set(sod.distinct_steps)
    if not constrained:
        return None
    pid = principal.person_id if principal is not None else None
    return {
        sr.step_id: pid
        for sr in step_results
        if sr.step_id in constrained and sr.status == StepResultStatus.COMPLETE.value
    }


async def run_procedure(
    procedure: Procedure,
    agent: Agent,
    executors: Mapping[StepKind, StepExecutor],
    *,
    vertical: str,
    run_id: str,
    trigger_context: dict[str, Any] | None = None,
    principal: Person | None = None,
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

    ``principal`` is the resolved HUMAN who triggered the run (the REQUESTER /
    ambient resolution, ADR-0026 D3 OQ-2). It is recorded against each SoD-
    constrained step the run completes — the requester half of the run-level
    ``step_principals`` map the fail-closed principal-SoD run-check resolves against
    (A1b Step 1, SD-2=(a)); the approver half is recorded at the gate by
    :func:`resolve_gated_step`. ``None`` (the default) leaves a SoD-constrained
    requester step unresolved, which fails the run-check closed at the gate (AC-3).
    """
    validate_runnable(procedure, agent)
    validate_read_bindings_for_vertical(procedure, agent, vertical)

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
        principal=principal,
    )
    step_results, final_status = await execute_steps(procedure.steps, executors, ctx, run_id)
    run.status = final_status.value
    run.updated_at = datetime.now(UTC)
    # Record the requester half of the SoD principal map from the typed ambient
    # principal (ADR-0026 D4 / A1b Step 1) — None for a non-SoD procedure (inert).
    run.step_principals = _record_requester_principals(procedure, step_results, ctx.principal)
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
