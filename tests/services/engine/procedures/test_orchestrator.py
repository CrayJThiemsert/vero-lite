"""PLAN-0019 Part A — the Procedure orchestrator control plane (ADR-016 D2/D3/D4).

Pure-Python (no DB, no LLM): fake :class:`StepExecutor`s drive the orchestrator so
the control plane is asserted in isolation — sequencing + set-valued threading
(A-3), the autonomy model + agent allowlist / ceiling (A-4), fail-and-divert
(A-6), the gated/human_task suspend, and the per-step telemetry seam. Concrete
executors (the real ADR-007 action path, query via adapter) are separate steps.
"""

from __future__ import annotations

from typing import Any

import pytest

from services.engine.ontology_meta import (
    JoinKeyMeta,
    LinkTypeMeta,
    ObjectTypeMeta,
    OntologyMeta,
    PropertyMeta,
)
from services.engine.procedures.orchestrator import (
    ProcedureError,
    RunContext,
    StepExecutor,
    StepOutcome,
    has_read_bindings,
    run_procedure,
    validate_read_bindings,
    validate_read_bindings_for_vertical,
    validate_runnable,
)
from services.engine.procedures.runs import PipelineRunStatus, StepResultStatus
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    EventTrigger,
    JoinSpec,
    OnFailure,
    Procedure,
    ProjectSpec,
    Schedule,
    Step,
    StepInput,
    StepKind,
    Trigger,
)


class _RecordingExecutor:
    """Records each (step_id, input_set) it is called with; returns a fixed set."""

    def __init__(self, output: list[Any] | None = None) -> None:
        self.output = output if output is not None else []
        self.calls: list[tuple[str, list[Any]]] = []

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        self.calls.append((step.step_id, list(input_set)))
        return StepOutcome(
            output=self.output,
            reasoning_trace=[{"kind": step.kind.value, "summary": f"ran {step.step_id}"}],
            audit={"actor": "exec", "actor_kind": "engine"},
        )


class _ContextCapturingExecutor:
    """Records the RunContext it was handed — used to assert goal threading (A-8)."""

    def __init__(self) -> None:
        self.contexts: list[RunContext] = []

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        self.contexts.append(ctx)
        return StepOutcome(output=[])


class _RaisingExecutor:
    """Always raises — exercises D4 fail-and-divert."""

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        raise RuntimeError("boom")


class _MalformedExecutor:
    """Returns the wrong type — must be diverted, never crash the orchestrator."""

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return None  # type: ignore[return-value]


def _agent(
    *,
    ceiling: Autonomy = Autonomy.GATED,
    kinds: list[StepKind] | None = None,
    handlers: list[str] | None = None,
    object_types: list[str] | None = None,
) -> Agent:
    return Agent(
        agent_id="a1",
        name="Agent One",
        autonomy_ceiling=ceiling,
        allowed=AgentAllowed(
            step_kinds=kinds or [],
            action_handlers=handlers or [],
            object_types=object_types or [],
        ),
    )


def _proc(steps: list[Step], *, trigger: Trigger = Trigger.MANUAL) -> Procedure:
    # A `schedule`-trigger procedure requires a schedule descriptor (ADR-0028 SD-P1 /
    # PLAN-0055 Step 2); an `event`-trigger one requires an event_trigger (ADR-0029 SD-3 /
    # PLAN-0056 Step 2); a `manual` one carries neither.
    schedule = Schedule(cron="0 6 * * *") if trigger is Trigger.SCHEDULE else None
    event_trigger = EventTrigger(event_kind="asset_failure") if trigger is Trigger.EVENT else None
    return Procedure(
        procedure_id="p1",
        title="P",
        run_by="a1",
        trigger=trigger,
        schedule=schedule,
        event_trigger=event_trigger,
        steps=steps,
    )


async def test_happy_path_completes_and_threads_sets() -> None:
    query = _RecordingExecutor(output=[{"pond": "p3"}, {"pond": "p7"}])
    evaluate = _RecordingExecutor(output=[{"pond": "p7", "verdict": "breach"}])
    action = _RecordingExecutor(output=[{"action": "aerate"}])
    executors = {
        StepKind.QUERY: query,
        StepKind.EVALUATE: evaluate,
        StepKind.ACTION: action,
    }
    proc = _proc(
        [
            Step(step_id="read", name="Read DO", kind=StepKind.QUERY),
            Step(step_id="judge", name="Judge", kind=StepKind.EVALUATE),
            Step(
                step_id="summary",
                name="Summary",
                kind=StepKind.ACTION,
                autonomy=Autonomy.AUTO,
                handler="echo",
            ),
        ]
    )
    agent = _agent(ceiling=Autonomy.AUTO, handlers=["echo"])

    result = await run_procedure(proc, agent, executors, vertical="v", run_id="run-1")

    assert result.run.status == PipelineRunStatus.COMPLETED.value
    assert [s.step_id for s in result.step_results] == ["read", "judge", "summary"]
    assert all(s.status == StepResultStatus.COMPLETE.value for s in result.step_results)
    # set-valued threading: each step's input is the prior step's output set.
    assert evaluate.calls[0][1] == [{"pond": "p3"}, {"pond": "p7"}]
    assert action.calls[0][1] == [{"pond": "p7", "verdict": "breach"}]
    # telemetry seam: every StepResult carries duration_ms + trace + audit + artifact.
    for sr in result.step_results:
        assert sr.duration_ms is not None and sr.duration_ms >= 0
        assert sr.reasoning_trace
        assert sr.audit == {"actor": "exec", "actor_kind": "engine"}
        assert sr.artifact is not None and "output_set" in sr.artifact


async def test_gated_action_suspends_and_halts_remainder() -> None:
    executors = {
        StepKind.QUERY: _RecordingExecutor(output=[{"x": 1}]),
        StepKind.ACTION: _RecordingExecutor(output=[{"done": 1}]),
    }
    proc = _proc(
        [
            Step(step_id="read", name="Read", kind=StepKind.QUERY),
            Step(step_id="aerate", name="Aerate", kind=StepKind.ACTION, handler="echo"),  # gated
            Step(step_id="after", name="After", kind=StepKind.QUERY),  # must NOT run
        ]
    )
    agent = _agent(handlers=["echo"])  # ceiling gated by default

    result = await run_procedure(proc, agent, executors, vertical="v", run_id="run-2")

    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    assert [s.step_id for s in result.step_results] == ["read", "aerate"]
    assert result.step_results[-1].status == StepResultStatus.WAITING_HUMAN.value


async def test_human_task_suspends() -> None:
    executors = {
        StepKind.HUMAN_TASK: _RecordingExecutor(),
        StepKind.QUERY: _RecordingExecutor(),
    }
    proc = _proc(
        [
            Step(step_id="visual", name="Visual check", kind=StepKind.HUMAN_TASK),
            Step(step_id="after", name="After", kind=StepKind.QUERY),  # must NOT run
        ]
    )
    result = await run_procedure(proc, _agent(), executors, vertical="v", run_id="run-3")

    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    assert [s.step_id for s in result.step_results] == ["visual"]


async def test_fail_and_divert_aborts_run() -> None:
    executors: dict[StepKind, StepExecutor] = {
        StepKind.QUERY: _RaisingExecutor(),
        StepKind.EVALUATE: _RecordingExecutor(),
    }
    proc = _proc(
        [
            Step(step_id="read", name="Read", kind=StepKind.QUERY, on_failure=OnFailure.FAIL),
            Step(step_id="judge", name="Judge", kind=StepKind.EVALUATE),  # must NOT run
        ]
    )
    result = await run_procedure(proc, _agent(), executors, vertical="v", run_id="run-4")

    assert result.run.status == PipelineRunStatus.FAILED.value
    assert [s.step_id for s in result.step_results] == ["read"]
    assert result.step_results[0].status == StepResultStatus.FAILED.value
    trace = result.step_results[0].reasoning_trace
    assert trace is not None and trace[0]["kind"] == "error"
    assert "RuntimeError" in trace[0]["summary"]  # error type retained for observability


async def test_malformed_executor_output_is_diverted_not_crashed() -> None:
    proc = _proc([Step(step_id="read", name="Read", kind=StepKind.QUERY)])
    # A wrong-type return must NOT crash the run loop — it diverts like any failure.
    result = await run_procedure(
        proc, _agent(), {StepKind.QUERY: _MalformedExecutor()}, vertical="v", run_id="run-6"
    )
    assert result.run.status == PipelineRunStatus.FAILED.value
    trace = result.step_results[0].reasoning_trace
    assert trace is not None and "StepOutcome" in trace[0]["summary"]


async def test_escalate_to_human_diverts_instead_of_failing() -> None:
    executors = {StepKind.QUERY: _RaisingExecutor()}
    proc = _proc(
        [
            Step(
                step_id="read",
                name="Read",
                kind=StepKind.QUERY,
                on_failure=OnFailure.ESCALATE_TO_HUMAN,
            )
        ]
    )
    result = await run_procedure(proc, _agent(), executors, vertical="v", run_id="run-5")

    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    # D4: the step is routed to waiting_human, not failed.
    assert result.step_results[0].status == StepResultStatus.WAITING_HUMAN.value


async def test_run_context_carries_procedure_goal() -> None:
    """A-8: run_procedure threads Procedure.goal onto RunContext for every executor."""
    capture = _ContextCapturingExecutor()
    proc = Procedure(
        procedure_id="p1",
        title="P",
        goal="Run the morning pond health round.",
        run_by="a1",
        steps=[Step(step_id="read", name="Read", kind=StepKind.QUERY)],
    )
    await run_procedure(proc, _agent(), {StepKind.QUERY: capture}, vertical="v", run_id="run-goal")

    assert capture.contexts[0].goal == "Run the morning pond health round."


async def test_run_context_goal_is_none_when_procedure_has_no_goal() -> None:
    """A-8: an empty goal normalises to None (the reactive prompt path)."""
    capture = _ContextCapturingExecutor()
    proc = _proc([Step(step_id="read", name="Read", kind=StepKind.QUERY)])  # goal defaults ""
    await run_procedure(
        proc, _agent(), {StepKind.QUERY: capture}, vertical="v", run_id="run-nogoal"
    )

    assert capture.contexts[0].goal is None


async def test_schedule_trigger_is_runnable() -> None:
    # ADR-0028 S1 / PLAN-0055 Step 1 (AC-1): a `schedule`-trigger procedure is now
    # runnable — validate_runnable no longer blocks it. (The scheduler that FIRES it
    # on a clock is a separate worker built later in PLAN-0055; here we prove only
    # that the trigger gate admits it.)
    proc = _proc([Step(step_id="read", name="Read", kind=StepKind.QUERY)], trigger=Trigger.SCHEDULE)
    result = await run_procedure(
        proc, _agent(), {StepKind.QUERY: _RecordingExecutor()}, vertical="v", run_id="x"
    )
    assert result.run.status == PipelineRunStatus.COMPLETED.value


def test_schedule_trigger_still_enforces_governance() -> None:
    # AC-2: lifting the trigger block does not weaken any OTHER governance check. A
    # schedule proc whose action names a handler outside the agent allowlist still
    # raises — the handler guard sits BELOW the trigger check in validate_runnable and
    # applies regardless of trigger.
    proc = _proc(
        [Step(step_id="act", name="Act", kind=StepKind.ACTION, handler="danger")],
        trigger=Trigger.SCHEDULE,
    )
    agent = _agent(ceiling=Autonomy.GATED, handlers=["echo"])
    with pytest.raises(ProcedureError, match="outside agent"):
        validate_runnable(proc, agent)


async def test_event_trigger_is_runnable() -> None:
    # ADR-0029 / PLAN-0056 Step 1 (AC-1): an `event`-trigger procedure is now runnable —
    # validate_runnable no longer blocks it. (The bridge that FIRES it from a detected
    # anomaly is built later in PLAN-0056; here we prove only that the trigger gate admits
    # it. An event procedure carries no schedule descriptor — the descriptor invariant only
    # requires one for `schedule`.)
    proc = _proc([Step(step_id="read", name="Read", kind=StepKind.QUERY)], trigger=Trigger.EVENT)
    result = await run_procedure(
        proc, _agent(), {StepKind.QUERY: _RecordingExecutor()}, vertical="v", run_id="x"
    )
    assert result.run.status == PipelineRunStatus.COMPLETED.value


def test_event_trigger_still_enforces_governance() -> None:
    # AC-2: lifting the `event` trigger block does not weaken any OTHER governance check. An
    # event proc whose action names a handler outside the agent allowlist still raises — the
    # handler guard sits BELOW the trigger check in validate_runnable and applies regardless
    # of trigger.
    proc = _proc(
        [Step(step_id="act", name="Act", kind=StepKind.ACTION, handler="danger")],
        trigger=Trigger.EVENT,
    )
    agent = _agent(ceiling=Autonomy.GATED, handlers=["echo"])
    with pytest.raises(ProcedureError, match="outside agent"):
        validate_runnable(proc, agent)


async def test_missing_executor_for_kind_raises() -> None:
    proc = _proc([Step(step_id="read", name="Read", kind=StepKind.QUERY)])
    with pytest.raises(ProcedureError, match="no executor registered"):
        await run_procedure(proc, _agent(), {}, vertical="v", run_id="x")


def test_validate_rejects_kind_outside_allowlist() -> None:
    proc = _proc([Step(step_id="act", name="Act", kind=StepKind.ACTION, handler="echo")])
    agent = _agent(kinds=[StepKind.QUERY, StepKind.EVALUATE], handlers=["echo"])
    with pytest.raises(ProcedureError, match="outside agent"):
        validate_runnable(proc, agent)


def test_validate_rejects_autonomy_above_ceiling() -> None:
    proc = _proc(
        [
            Step(
                step_id="act",
                name="Act",
                kind=StepKind.ACTION,
                autonomy=Autonomy.AUTO,
                handler="echo",
            )
        ]
    )
    agent = _agent(ceiling=Autonomy.GATED, handlers=["echo"])
    with pytest.raises(ProcedureError, match="exceeds agent"):
        validate_runnable(proc, agent)


def test_validate_rejects_handler_outside_allowlist() -> None:
    proc = _proc([Step(step_id="act", name="Act", kind=StepKind.ACTION, handler="danger")])
    agent = _agent(ceiling=Autonomy.GATED, handlers=["echo"])
    with pytest.raises(ProcedureError, match="outside agent"):
        validate_runnable(proc, agent)


def test_validate_empty_step_kinds_is_unconstrained() -> None:
    proc = _proc(
        [
            Step(step_id="read", name="Read", kind=StepKind.QUERY),
            Step(step_id="act", name="Act", kind=StepKind.ACTION, handler="echo"),
        ]
    )
    # empty step_kinds = unconstrained; the action handler is still allowlisted.
    validate_runnable(proc, _agent(kinds=[], handlers=["echo"]))


# --- A-ζ-prep: named-input + field-equality filter -------------------------------


def test_step_input_from_alias_parses() -> None:
    """The YAML key `from` maps onto StepInput.from_step (alias)."""
    step = Step(
        step_id="x",
        name="X",
        kind=StepKind.QUERY,
        input={"from": "judge", "where": {"verdict": "breach"}},
    )
    assert step.input is not None
    assert step.input.from_step == "judge"
    assert step.input.where == {"verdict": "breach"}


async def test_named_input_references_an_earlier_step() -> None:
    """`input.from` pulls a NAMED earlier step's output, not the immediate prior."""
    read = _RecordingExecutor(output=[{"id": "a"}])
    judge = _RecordingExecutor(output=[{"id": "b"}])
    act = _RecordingExecutor(output=[])
    executors = {StepKind.QUERY: read, StepKind.EVALUATE: judge, StepKind.ACTION: act}
    proc = _proc(
        [
            Step(step_id="read", name="Read", kind=StepKind.QUERY),
            Step(step_id="judge", name="Judge", kind=StepKind.EVALUATE),
            Step(
                step_id="act",
                name="Act",
                kind=StepKind.ACTION,
                autonomy=Autonomy.AUTO,
                handler="echo",
                input=StepInput(from_step="read"),  # references READ, skipping JUDGE
            ),
        ]
    )
    await run_procedure(
        proc,
        _agent(ceiling=Autonomy.AUTO, handlers=["echo"]),
        executors,
        vertical="v",
        run_id="r-named",
    )

    assert act.calls[0][1] == [{"id": "a"}], "act must see READ's output, not JUDGE's"


async def test_where_filter_narrows_to_subset() -> None:
    """`input.where` keeps only entities matching every field-equality pair."""
    judge = _RecordingExecutor(
        output=[
            {"pond": "p1", "verdict": "breach"},
            {"pond": "p2", "verdict": "ok"},
            {"pond": "p3", "verdict": "breach"},
        ]
    )
    act = _RecordingExecutor(output=[])
    executors = {StepKind.QUERY: judge, StepKind.ACTION: act}
    proc = _proc(
        [
            Step(step_id="judge", name="Judge", kind=StepKind.QUERY),
            Step(
                step_id="act",
                name="Act",
                kind=StepKind.ACTION,
                autonomy=Autonomy.AUTO,
                handler="echo",
                input=StepInput(where={"verdict": "breach"}),  # immediate prior + filter
            ),
        ]
    )
    await run_procedure(
        proc,
        _agent(ceiling=Autonomy.AUTO, handlers=["echo"]),
        executors,
        vertical="v",
        run_id="r-where",
    )

    assert act.calls[0][1] == [
        {"pond": "p1", "verdict": "breach"},
        {"pond": "p3", "verdict": "breach"},
    ]


async def test_fan_out_breach_and_watch_from_one_evaluate() -> None:
    """The headline pattern: one evaluate set fans out to a breach action + a watch
    human_task, each pulling its subset from `judge` via named-input + where."""
    judge = _RecordingExecutor(
        output=[
            {"pond": "p1", "verdict": "breach"},
            {"pond": "p2", "verdict": "watch"},
            {"pond": "p3", "verdict": "ok"},
        ]
    )
    action = _RecordingExecutor(output=[])
    human = _RecordingExecutor(output=[])
    executors = {
        StepKind.EVALUATE: judge,
        StepKind.ACTION: action,
        StepKind.HUMAN_TASK: human,
    }
    proc = _proc(
        [
            Step(step_id="judge", name="Judge", kind=StepKind.EVALUATE),
            Step(
                step_id="aerate",
                name="Aerate",
                kind=StepKind.ACTION,
                autonomy=Autonomy.AUTO,
                handler="echo",
                input=StepInput(from_step="judge", where={"verdict": "breach"}),
            ),
            Step(
                step_id="visual",
                name="Visual check",
                kind=StepKind.HUMAN_TASK,
                input=StepInput(from_step="judge", where={"verdict": "watch"}),
            ),
        ]
    )
    result = await run_procedure(
        proc,
        _agent(ceiling=Autonomy.AUTO, handlers=["echo"]),
        executors,
        vertical="v",
        run_id="r-fan",
    )

    assert action.calls[0][1] == [{"pond": "p1", "verdict": "breach"}]
    assert human.calls[0][1] == [{"pond": "p2", "verdict": "watch"}]
    # the human_task suspends the run (still pulled its watch subset from judge).
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value


def test_validate_rejects_forward_reference() -> None:
    proc = _proc(
        [
            Step(step_id="a", name="A", kind=StepKind.QUERY, input=StepInput(from_step="b")),
            Step(step_id="b", name="B", kind=StepKind.QUERY),  # 'b' is LATER than 'a'
        ]
    )
    with pytest.raises(ProcedureError, match="not an earlier step"):
        validate_runnable(proc, _agent())


def test_validate_rejects_unknown_reference() -> None:
    proc = _proc(
        [
            Step(step_id="a", name="A", kind=StepKind.QUERY),
            Step(step_id="b", name="B", kind=StepKind.QUERY, input=StepInput(from_step="ghost")),
        ]
    )
    with pytest.raises(ProcedureError, match="not an earlier step"):
        validate_runnable(proc, _agent())


# --- ADR-016 Q3: the read-binding load-gate (PLAN-0046 Step 2) --------------------
#
# Pre-committed pass/fail read (AC-5, fixed BEFORE these tests were written):
# REFUSE-1 reads=["Ghost"] vs registry {Pond, Reading} -> ProcedureError naming the
#   step, 'Ghost', and the ontology condition. REFUSE-2 reads=["Pond"], registry
#   {Pond, Reading}, allowlist ["Reading"] -> ProcedureError naming 'Pond' + the
#   allowlist condition. REFUSE-3 a mixed list with ANY failing element -> refuse.
# ACCEPT single + multi-object consistent bindings -> no raise. OQ-6 empty
#   object_types -> no raise (unconstrained). SKIP a reads-absent procedure -> the
#   gate (and the ontology I/O) never fire.

_REGISTRY = frozenset({"Pond", "Reading"})


def _read_proc(reads: list[str]) -> Procedure:
    return _proc(
        [Step(step_id="read", name="Read", kind=StepKind.QUERY, input=StepInput(reads=reads))]
    )


def test_read_gate_accepts_consistent_binding() -> None:
    """AC-4: reads ∈ ontology ∩ allowlist loads without error."""
    validate_read_bindings(_read_proc(["Pond"]), _agent(object_types=["Pond"]), _REGISTRY)


def test_read_gate_accepts_multi_object_binding() -> None:
    """AC-4 / OQ-5: reads is a LIST — every element gated; all-consistent loads."""
    validate_read_bindings(
        _read_proc(["Pond", "Reading"]), _agent(object_types=["Pond", "Reading"]), _REGISTRY
    )


def test_read_gate_refuses_object_not_in_ontology() -> None:
    """AC-5 REFUSE-1: an object_type outside the vertical's ontology refuses to load."""
    with pytest.raises(ProcedureError, match="'Ghost' does not exist in the vertical's ontology"):
        validate_read_bindings(_read_proc(["Ghost"]), _agent(object_types=["Ghost"]), _REGISTRY)


def test_read_gate_refuses_object_outside_allowlist() -> None:
    """AC-5 REFUSE-2: in-ontology but outside a NON-EMPTY agent allowlist refuses."""
    with pytest.raises(ProcedureError, match="'Pond' is outside agent .* allowed.object_types"):
        validate_read_bindings(_read_proc(["Pond"]), _agent(object_types=["Reading"]), _REGISTRY)


def test_read_gate_refuses_mixed_list_on_any_failing_element() -> None:
    """AC-5 REFUSE-3: a multi-object list refuses when ANY element fails a condition."""
    with pytest.raises(ProcedureError, match="'Ghost' does not exist"):
        validate_read_bindings(
            _read_proc(["Pond", "Ghost"]), _agent(object_types=["Pond", "Ghost"]), _REGISTRY
        )


def test_read_gate_empty_object_types_is_unconstrained() -> None:
    """AC-6 / OQ-6: empty object_types = UNCONSTRAINED (mirrors step_kinds, NOT
    action_handlers' fail-closed) — the gate only bites when the agent opts in."""
    validate_read_bindings(_read_proc(["Pond"]), _agent(), _REGISTRY)


def test_read_gate_ignores_non_query_steps() -> None:
    """The v1 gate scopes to QUERY steps (ADR-016 Q3): a reads on another kind is
    not gated and does not count as a read binding."""
    proc = _proc(
        [Step(step_id="judge", name="J", kind=StepKind.EVALUATE, input=StepInput(reads=["Ghost"]))]
    )
    validate_read_bindings(proc, _agent(), _REGISTRY)  # no raise — out of the v1 gate's scope
    assert has_read_bindings(proc) is False


def test_read_gate_skipped_when_no_reads_declared() -> None:
    """AC-3/AC-6 backward-compat: a reads-absent procedure NEVER invokes the gate —
    proven with a vertical that has no ontology on disk (any registry I/O would raise)."""
    proc = _proc([Step(step_id="read", name="Read", kind=StepKind.QUERY)])
    validate_read_bindings_for_vertical(proc, _agent(), "no-such-vertical")  # no raise


# --- ADR-016 TF-3: threshold_field load gate (seam (a) trace-to-reads + c1-c4) ----

_PART_META = OntologyMeta(
    vertical="fixture",
    object_types=[
        ObjectTypeMeta(
            name="Part",
            primary_key="part_no",
            properties=[
                PropertyMeta(name="part_no", type="string"),
                PropertyMeta(name="stock_qty", type="int"),
                PropertyMeta(name="reorder_point", type="int"),
            ],
        )
    ],
    link_types=[],
)
_PART_NAMES = frozenset(t.name for t in _PART_META.object_types)


def _band_proc(
    *,
    threshold_field: str = "reorder_point",
    reads: tuple[str, ...] | None = ("Part",),
    project: ProjectSpec | None = None,
) -> Procedure:
    """A read_stock QUERY (reads Part, optional project) feeding a judge_stock EVALUATE
    that bands on threshold_field — the migrated procurement shape. judge_stock threads
    from the preceding step by default (no explicit input)."""
    read_input = None if reads is None else StepInput(reads=list(reads), project=project)
    return _proc(
        [
            Step(step_id="read_stock", name="Read", kind=StepKind.QUERY, input=read_input),
            Step(
                step_id="judge_stock",
                name="Judge",
                kind=StepKind.EVALUATE,
                threshold_field=threshold_field,
                direction="below",
            ),
        ]
    )


def test_threshold_field_gate_accepts_declared_same_row_column() -> None:
    """AC-4: threshold_field naming a declared property of the traced query step's base
    read loads (the migrated procurement shape: reorder_point rides through the rename)."""
    proc = _band_proc(project=ProjectSpec(fields={"stock_qty": "measured_value"}))
    validate_read_bindings(proc, _agent(), _PART_NAMES, meta=_PART_META)


def test_threshold_field_gate_refuses_non_ontology_column() -> None:
    """AC-4: a band column that is not a declared property of the base read refuses."""
    proc = _band_proc(threshold_field="ghost_col")
    with pytest.raises(ProcedureError, match="'ghost_col' is not a declared property of 'Part'"):
        validate_read_bindings(proc, _agent(), _PART_NAMES, meta=_PART_META)


def test_threshold_field_gate_c1_no_reads_provenance_fails_closed() -> None:
    """AC-4 c1: the traced query step declares no reads -> the band column cannot be
    ontology-validated -> fail CLOSED."""
    proc = _band_proc(reads=None)
    with pytest.raises(ProcedureError, match="declares no reads.*fail closed"):
        validate_read_bindings(proc, _agent(), _PART_NAMES, meta=_PART_META)


def test_threshold_field_gate_c1_entry_point_evaluate_fails_closed() -> None:
    """AC-4 c1: an evaluate step with no prior step (entry point) has no query
    provenance to validate against -> fail CLOSED."""
    proc = _proc(
        [
            Step(
                step_id="judge_stock",
                name="Judge",
                kind=StepKind.EVALUATE,
                threshold_field="reorder_point",
                direction="below",
            )
        ]
    )
    with pytest.raises(ProcedureError, match="entry-point step has no query provenance"):
        validate_read_bindings(proc, _agent(), _PART_NAMES, meta=_PART_META)


def test_threshold_field_gate_c3_refuses_rename_source() -> None:
    """AC-4 c3: a band column the query renames away (a project.fields rename SOURCE) is
    refused — it passes declared-props but would be absent from the rows at run."""
    proc = _band_proc(project=ProjectSpec(fields={"reorder_point": "rp2"}))
    with pytest.raises(ProcedureError, match="renamed away by query step .* project.fields"):
        validate_read_bindings(proc, _agent(), _PART_NAMES, meta=_PART_META)


def test_threshold_field_gate_c4_has_read_bindings_fires() -> None:
    """AC-4 c4: a threshold_field procedure trips has_read_bindings even when the query
    step declares no reads — so a field-only procedure cannot silently skip the gate."""
    assert has_read_bindings(_band_proc(reads=None)) is True


def test_threshold_field_gate_requires_meta() -> None:
    """A threshold_field step with no ontology meta supplied fails loudly (fail-loud,
    mirroring the join/project meta requirement)."""
    proc = _band_proc(project=ProjectSpec(fields={"stock_qty": "measured_value"}))
    with pytest.raises(ProcedureError, match="no ontology meta was supplied"):
        validate_read_bindings(proc, _agent(), _PART_NAMES)


# --- ADR-016 FKP (2026-07-12): threshold_field on a JOINED FK-parent column ------

_FKP_META = OntologyMeta(
    vertical="fkp-fixture",
    object_types=[
        ObjectTypeMeta(
            name="OperationalEvent",
            primary_key="event_id",
            properties=[
                PropertyMeta(name="event_id", type="string"),
                PropertyMeta(name="asset_id", type="string"),
                PropertyMeta(name="measured_value", type="float"),
                PropertyMeta(name="site_id", type="string"),  # declared collision w/ Asset
            ],
        ),
        ObjectTypeMeta(
            name="Asset",
            primary_key="asset_id",
            properties=[
                PropertyMeta(name="asset_id", type="string"),
                PropertyMeta(name="rated_current_a", type="float"),  # the joined-parent band
                PropertyMeta(name="site_id", type="string"),  # the collision counterpart
            ],
        ),
    ],
    link_types=[
        LinkTypeMeta(
            name="event_emitted_by_asset",
            from_type="OperationalEvent",
            to_type="Asset",
            foreign_key=JoinKeyMeta(from_property="asset_id", to_property="asset_id"),
        ),
    ],
)
_FKP_NAMES = frozenset(t.name for t in _FKP_META.object_types)
# the declared site_id collision must be renamed away for a clean load
_FKP_RENAME = ProjectSpec(fields={"site_id": "asset_site_id"})


def _fkp_band_proc(
    *,
    threshold_field: str = "rated_current_a",
    join: bool = True,
    project: ProjectSpec | None = _FKP_RENAME,
) -> Procedure:
    """The FK-parent shape: a read QUERY reads [OperationalEvent, Asset] and joins Asset
    via event_emitted_by_asset; the judge bands on a JOINED-parent column (ADR-016 FKP
    amendment 2026-07-12). ``join=False`` drops the join (the same-row-only rule case)."""
    reads = ["OperationalEvent", "Asset"] if join else ["OperationalEvent"]
    joins = [JoinSpec(with_read="Asset", link="event_emitted_by_asset")] if join else None
    return _proc(
        [
            Step(
                step_id="read_readings",
                name="Read",
                kind=StepKind.QUERY,
                input=StepInput(reads=reads, join=joins, project=project if join else None),
            ),
            Step(
                step_id="judge",
                name="Judge",
                kind=StepKind.EVALUATE,
                threshold_field=threshold_field,
                direction="above",
            ),
        ]
    )


def test_threshold_field_gate_accepts_joined_parent_column() -> None:
    """FKP-2: a threshold_field naming a declared property of a JOINED FK-parent loads —
    the join delivers the parent's band column onto the merged rows."""
    validate_read_bindings(_fkp_band_proc(), _agent(), _FKP_NAMES, meta=_FKP_META)


def test_threshold_field_gate_accepts_base_column_under_join() -> None:
    """FKP-2: the widened domain is base + joined — a base-read column still accepts when
    the step also declares a join."""
    validate_read_bindings(
        _fkp_band_proc(threshold_field="measured_value"), _agent(), _FKP_NAMES, meta=_FKP_META
    )


def test_threshold_field_gate_refuses_parent_column_without_join() -> None:
    """FKP-2: the same-row rule stands — a parent column named while the query declares NO
    join refuses (the domain is the base read alone)."""
    proc = _fkp_band_proc(join=False)
    with pytest.raises(ProcedureError, match="'rated_current_a' is not a declared property"):
        validate_read_bindings(proc, _agent(), _FKP_NAMES, meta=_FKP_META)


def test_threshold_field_gate_refuses_undeclared_column_under_join() -> None:
    """FKP-2: a band column on neither the base read nor any joined parent refuses."""
    proc = _fkp_band_proc(threshold_field="ghost_col")
    with pytest.raises(ProcedureError, match="'ghost_col' is not a declared property"):
        validate_read_bindings(proc, _agent(), _FKP_NAMES, meta=_FKP_META)


def test_threshold_field_gate_collision_refused_before_threshold() -> None:
    """FKP-2 g2: an un-renamed declared property collision between the joined types refuses
    at the join/collision gate — which runs BEFORE the threshold gate
    (orchestrator.py :311-312) — so no new band-column ambiguity rule is needed."""
    proc = _fkp_band_proc(project=None)  # drop the site_id rename → collision survives
    with pytest.raises(ProcedureError, match="declared property collision.*site_id"):
        validate_read_bindings(proc, _agent(), _FKP_NAMES, meta=_FKP_META)


async def test_run_procedure_wires_read_gate_accept_and_refuse() -> None:
    """AC-7: the gate fires at the run_procedure pre-flight against the REAL
    aquaculture ontology registry — accept completes; refuse raises BEFORE any
    executor runs (validate_runnable's signature + call-sites untouched)."""
    query = _RecordingExecutor(output=[{"pond": "p1"}])
    result = await run_procedure(
        _read_proc(["Pond"]),
        _agent(object_types=["Pond"]),
        {StepKind.QUERY: query},
        vertical="aquaculture",
        run_id="run-reads-ok",
    )
    assert result.run.status == PipelineRunStatus.COMPLETED.value
    assert query.calls  # the accepted run actually executed

    refused = _RecordingExecutor()
    with pytest.raises(ProcedureError, match="'Ghost' does not exist"):
        await run_procedure(
            _read_proc(["Ghost"]),
            _agent(),
            {StepKind.QUERY: refused},
            vertical="aquaculture",
            run_id="run-reads-bad",
        )
    assert refused.calls == []  # refused at pre-flight — no step ever ran
