"""PLAN-0048 Step 2 — the execute half: ``QueryStepExecutor`` + the structured
refusal divert (AC-4..AC-9).

ORACLE-FIRST DISCIPLINE (AC-7 / Lesson #0026, mirroring the Step-1 oracle in
``test_query_step.py``): the pass/fail matrix below is COMMITTED BEFORE any
executor or test code exists. The tests in this module must implement EXACTLY
this matrix; deviations are surfaced, never silently absorbed.
"""

# ---------------------------------------------------------------------------
# PRE-COMMITTED PASS/FAIL MATRIX (PLAN-0048 AC-4..AC-9; SD-1..SD-5 ratified
# as-recommended 2026-07-04). Counting fake adapter records every
# fetch_objects(object_type, filter_expr) call. Fixture ontology =
# {Pond, Reading}; step_id = "read".
#
# EXECUTE (AC-4 — declared==dispatched, positively):
#   EXEC-1   reads=["Pond"], adapter has 3 Pond rows          -> dispatches
#            fetch_objects("Pond") EXACTLY; output == the 3 rows; trace carries
#            ONE read-provenance entry {kind: "read_provenance",
#            object_type: "Pond", fetched_count: 3, post_where_count: 3}
#   EXEC-2   reads=["Pond"], where={"status": "active"}, rows 2-active/1-not
#            -> output == the 2 active rows (post-fetch narrowing via the
#            SHARED matches_where predicate — LOCKED-3); provenance
#            fetched_count: 3, post_where_count: 2
#   EXEC-3   filter_expr is None on EVERY dispatch (LOCKED-3 — the engine keeps
#            the narrowing; nothing is pushed down to the adapter)
#
# ADVERSARIAL declared==dispatched (AC-5 — property over a matrix):
#   PROP-1   matrix varying reads/where/allowlist/adapter contents (incl. an
#            adapter whose store also holds rows of OTHER object_types):
#            adapter.calls == [declared object_type] — never one more, never a
#            substitute, and never the other types present in the store
#
# BOUNDED DISPATCH (AC-6):
#   BOUND-1  exactly ONE fetch_objects call per execute() (len(calls) == 1)
#   BOUND-2  an adapter that RAISES propagates the exception with NO re-fetch
#            (len(calls) == 1 after the raise — no retry loop exists)
#
# REFUSAL vs NO-DATA (AC-7 — the pre-committed read):
#   REF-1    out-of-coverage read (reads=["Ghost"]) RAISES ReadRefusal
#            (unknown_object_type) BEFORE any dispatch (len(calls) == 0)
#   REF-2    in-coverage read whose fetch yields ZERO post-where rows COMPLETES
#            with output == [] + provenance trace (fetched_count/post_where_count
#            recorded) — refusal and no-data are distinguishable from the
#            recorded StepResult alone: a refusal has NO completed StepResult
#            with output (it diverts via D4); no-data has a COMPLETED StepResult
#            with artifact output_set == [] and a read_provenance trace entry
#
# PASS-THROUGH (SD-1 — the executor's case, NOT plan_read's):
#   PASS-1   reads absent + from present -> execute() returns the
#            orchestrator-resolved input_set IDENTITY (no dispatch,
#            len(calls) == 0) + a read_passthrough trace entry
#
# D4 STRUCTURED DIVERT (AC-8 — run_procedure level):
#   D4-1     an entry-point query step with NO reads under the generic executor
#            + on_failure: escalate_to_human -> the run lands waiting_human and
#            the step's reasoning_trace carries a STRUCTURED entry
#            {kind: "read_refused", refusal_kind: "unbound_query",
#            step_id: "read", object_type: None} (no ontology I/O needed —
#            the load gate skips reads-absent procedures, so this exercises the
#            runtime refusal path in isolation)
#   D4-2     a multi-read step (BOTH types in ontology + allowlist, so the LOAD
#            GATE ACCEPTS it) refuses AT RUN TIME (SD-1 shape refusal is
#            runtime-only in v1) -> waiting_human + read_refused trace entry
#            with refusal_kind: "unsupported_read_shape"
#   D4-3     every NON-refusal exception keeps the byte-identical legacy trace
#            entry {kind: "error", summary: f"{type}: {exc}"} — asserted by an
#            executor raising RuntimeError through the same run path
#
# NO-REGRESSION (AC-9):
#   REG-1    no existing test file is modified by this step; the full
#            procedures suite (orchestrator D4 cases included) stays green;
#            hero_demo/run.py is byte-unchanged (asserted by the suite itself —
#            no new test needed, recorded here for the record)
# ---------------------------------------------------------------------------

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

import pytest

from services.engine.procedures.orchestrator import (
    RunContext,
    run_procedure,
    validate_read_bindings,
)
from services.engine.procedures.query_step import (
    QueryStepExecutor,
    ReadRefusal,
    ReadRefusalKind,
)
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    OnFailure,
    Procedure,
    Step,
    StepInput,
    StepKind,
    Trigger,
)

_ONTOLOGY = frozenset({"Pond", "Reading"})


class _CountingAdapter:
    """Protocol-complete counting fake: records every ``fetch_objects`` dispatch."""

    vertical_name = "fixture"

    def __init__(
        self, store: dict[str, list[dict[str, Any]]], *, raise_on_fetch: bool = False
    ) -> None:
        self._store = store
        self._raise = raise_on_fetch
        self.calls: list[tuple[str, str | None]] = []

    async def fetch_objects(
        self, object_type: str, filter_expr: str | None = None, limit: int = 1000
    ) -> list[dict[str, Any]]:
        self.calls.append((object_type, filter_expr))
        if self._raise:
            raise RuntimeError("adapter boom")
        return list(self._store.get(object_type, []))

    async def fetch_links(
        self, link_type: str, from_pk: str | None = None, to_pk: str | None = None
    ) -> list[dict[str, Any]]:
        return []

    def stream_events(
        self, event_type: str, since: datetime | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        raise NotImplementedError("not part of the v1 read surface (LOCKED-2)")


def _agent(object_types: list[str] | None = None) -> Agent:
    return Agent(
        agent_id="a1",
        name="Agent One",
        autonomy_ceiling=Autonomy.GATED,
        allowed=AgentAllowed(step_kinds=[], action_handlers=[], object_types=object_types or []),
    )


def _step(
    *,
    reads: list[str] | None = None,
    where: dict[str, str] | None = None,
    from_step: str | None = None,
    on_failure: OnFailure | None = None,
) -> Step:
    return Step(
        step_id="read",
        name="Read",
        kind=StepKind.QUERY,
        input=StepInput(reads=reads, where=where, from_step=from_step),
        on_failure=on_failure or OnFailure.FAIL,
    )


def _ctx(agent: Agent | None = None) -> RunContext:
    return RunContext(agent=agent or _agent(), vertical="fixture")


_POND_ROWS = [
    {"pond_id": "p1", "status": "active"},
    {"pond_id": "p2", "status": "active"},
    {"pond_id": "p3", "status": "fallow"},
]


def _executor(
    store: dict[str, list[dict[str, Any]]] | None = None, **kwargs: Any
) -> tuple[QueryStepExecutor, _CountingAdapter]:
    adapter = _CountingAdapter(store if store is not None else {"Pond": _POND_ROWS}, **kwargs)
    return QueryStepExecutor(adapter=adapter, object_type_names=_ONTOLOGY), adapter


# --- EXECUTE (AC-4) -----------------------------------------------------------


async def test_executor_dispatches_exactly_declared_and_traces() -> None:
    """EXEC-1 + BOUND-1: one dispatch of exactly the declared type; provenance trace."""
    executor, adapter = _executor()
    outcome = await executor.execute(_step(reads=["Pond"]), [], _ctx())
    assert adapter.calls == [("Pond", None)]
    assert outcome.output == _POND_ROWS
    [entry] = outcome.reasoning_trace
    assert entry["kind"] == "read_provenance"
    assert entry["object_type"] == "Pond"
    assert entry["fetched_count"] == 3
    assert entry["post_where_count"] == 3


async def test_executor_narrows_post_fetch_via_shared_where() -> None:
    """EXEC-2: where narrows the FETCHED set engine-side (shared matches_where)."""
    executor, adapter = _executor()
    outcome = await executor.execute(_step(reads=["Pond"], where={"status": "active"}), [], _ctx())
    assert outcome.output == _POND_ROWS[:2]
    [entry] = outcome.reasoning_trace
    assert entry["fetched_count"] == 3
    assert entry["post_where_count"] == 2


async def test_executor_never_pushes_filter_expr_down() -> None:
    """EXEC-3 / LOCKED-3: filter_expr is None on every dispatch — no push-down."""
    executor, adapter = _executor()
    await executor.execute(_step(reads=["Pond"], where={"status": "active"}), [], _ctx())
    assert all(filter_expr is None for _, filter_expr in adapter.calls)


# --- ADVERSARIAL declared==dispatched (AC-5) -----------------------------------


async def test_declared_equals_dispatched_adversarial_matrix() -> None:
    """PROP-1: across reads/where/allowlist/store variations — incl. a store
    holding OTHER object_types — the dispatched set == exactly the declared read."""
    poisoned_store = {
        "Pond": _POND_ROWS,
        "Reading": [{"reading_id": "r1"}],
        "Ghost": [{"ghost_id": "g1"}],
    }
    matrix: list[tuple[list[str], dict[str, str] | None, list[str] | None]] = [
        (["Pond"], None, None),
        (["Pond"], {"status": "active"}, ["Pond"]),
        (["Reading"], None, ["Pond", "Reading"]),
        (["Reading"], {"reading_id": "r1"}, None),
    ]
    for reads, where, allowlist in matrix:
        executor, adapter = _executor(poisoned_store)
        await executor.execute(
            _step(reads=reads, where=where), [], _ctx(_agent(object_types=allowlist))
        )
        assert [
            object_type for object_type, _ in adapter.calls
        ] == reads, f"dispatch drift for reads={reads}: {adapter.calls}"


# --- BOUNDED DISPATCH (AC-6) ---------------------------------------------------


async def test_adapter_exception_propagates_with_no_refetch() -> None:
    """BOUND-2: an adapter raise propagates (to D4 upstream) with NO retry."""
    executor, adapter = _executor(raise_on_fetch=True)
    with pytest.raises(RuntimeError, match="adapter boom"):
        await executor.execute(_step(reads=["Pond"]), [], _ctx())
    assert len(adapter.calls) == 1


# --- REFUSAL vs NO-DATA (AC-7 — pre-committed) ----------------------------------


async def test_out_of_coverage_refuses_before_any_dispatch() -> None:
    """REF-1: an out-of-coverage read raises typed BEFORE the adapter is touched."""
    executor, adapter = _executor()
    with pytest.raises(ReadRefusal) as excinfo:
        await executor.execute(_step(reads=["Ghost"]), [], _ctx())
    assert excinfo.value.refusal_kind is ReadRefusalKind.UNKNOWN_OBJECT_TYPE
    assert adapter.calls == []


async def test_zero_row_fetch_completes_with_provenance() -> None:
    """REF-2: in-coverage zero-row fetch COMPLETES with output=[] + provenance —
    no-data is a result, refusal is a raise; distinguishable from the record alone."""
    executor, adapter = _executor({"Pond": []})
    outcome = await executor.execute(_step(reads=["Pond"]), [], _ctx())
    assert outcome.output == []
    [entry] = outcome.reasoning_trace
    assert entry["kind"] == "read_provenance"
    assert entry["fetched_count"] == 0
    assert entry["post_where_count"] == 0
    assert adapter.calls == [("Pond", None)]


# --- PASS-THROUGH (SD-1) --------------------------------------------------------


async def test_passthrough_identity_no_dispatch() -> None:
    """PASS-1: reads absent + from present = identity pass-through, zero dispatch."""
    executor, adapter = _executor()
    threaded = [{"pond_id": "p7", "verdict": "breach"}]
    outcome = await executor.execute(_step(from_step="judge"), threaded, _ctx())
    assert outcome.output == threaded
    assert adapter.calls == []
    [entry] = outcome.reasoning_trace
    assert entry["kind"] == "read_passthrough"


# --- D4 STRUCTURED DIVERT (AC-8, run_procedure level) ----------------------------


def _run_proc(steps: list[Step]) -> Procedure:
    return Procedure(procedure_id="p1", title="P", run_by="a1", trigger=Trigger.MANUAL, steps=steps)


async def test_run_unbound_query_escalates_with_structured_refusal() -> None:
    """D4-1: an unbound entry-point query + escalate_to_human -> waiting_human with
    a structured read_refused trace entry (no ontology I/O — the load gate skips)."""
    executor, _ = _executor()
    proc = _run_proc([_step(on_failure=OnFailure.ESCALATE_TO_HUMAN)])
    result = await run_procedure(
        proc, _agent(), {StepKind.QUERY: executor}, vertical="fixture", run_id="r1"
    )
    assert result.run.status == "waiting_human"
    [step_result] = result.step_results
    [entry] = step_result.reasoning_trace
    assert entry["kind"] == "read_refused"
    assert entry["refusal_kind"] == "unbound_query"
    assert entry["step_id"] == "read"
    assert entry["object_type"] is None


async def test_run_multi_read_gate_accepts_but_runtime_refuses() -> None:
    """D4-2: a multi-read the LOAD GATE ACCEPTS (both types real + allowlisted,
    vertical=aquaculture) refuses AT RUN TIME (SD-1 shape refusal is runtime-only
    in v1) -> waiting_human + structured unsupported_read_shape entry."""
    agent = _agent(object_types=["Pond", "Farm"])
    step = Step(
        step_id="read",
        name="Read",
        kind=StepKind.QUERY,
        input=StepInput(reads=["Pond", "Farm"]),
        on_failure=OnFailure.ESCALATE_TO_HUMAN,
    )
    proc = _run_proc([step])
    # The real aquaculture ontology carries Pond + Farm — the gate accepts.
    validate_read_bindings(proc, agent, frozenset({"Pond", "Farm"}))
    adapter = _CountingAdapter({})
    executor = QueryStepExecutor(adapter=adapter, object_type_names=frozenset({"Pond", "Farm"}))
    result = await run_procedure(
        proc, agent, {StepKind.QUERY: executor}, vertical="aquaculture", run_id="r2"
    )
    assert result.run.status == "waiting_human"
    [step_result] = result.step_results
    [entry] = step_result.reasoning_trace
    assert entry["kind"] == "read_refused"
    assert entry["refusal_kind"] == "unsupported_read_shape"
    assert adapter.calls == []


class _BoomExecutor:
    """A non-refusal raiser — pins the byte-identical legacy D4 entry (D4-3)."""

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> Any:
        raise RuntimeError("boom")


async def test_run_non_refusal_exception_keeps_legacy_error_entry() -> None:
    """D4-3: every non-refusal exception keeps EXACTLY the legacy error entry."""
    proc = _run_proc([_step(on_failure=OnFailure.ESCALATE_TO_HUMAN)])
    result = await run_procedure(
        proc, _agent(), {StepKind.QUERY: _BoomExecutor()}, vertical="fixture", run_id="r3"
    )
    [step_result] = result.step_results
    assert step_result.reasoning_trace == [{"kind": "error", "summary": "RuntimeError: boom"}]
