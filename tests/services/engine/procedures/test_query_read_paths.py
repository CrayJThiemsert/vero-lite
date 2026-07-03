"""PLAN-0048 Step 3 — AC-10: the in-memory production path end-to-end.

A purpose-built fixture (agent opts in via ``object_types``; the procedure
declares ``reads`` on its query step; a fake adapter is injected) runs
query → evaluate → gated action to ``waiting_human`` through the REAL
``run_procedure`` pre-flight — proving the PLAN-0046 load gate and the Q4
executor agree on the plain-read shape: nothing the gate accepted is refused
at run time (the shared-bound tripwire in ``test_query_step.py`` pins the
converse). Ontology names are the REAL aquaculture set via
``load_ontology_meta`` (the Step-3 wiring bullet), so the gate does real
ontology I/O, not a fixture registry.
"""

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from services.engine.ontology_meta import load_ontology_meta
from services.engine.procedures.evaluate_step import EvaluateStepExecutor
from services.engine.procedures.orchestrator import (
    RunContext,
    StepExecutor,
    StepOutcome,
    run_procedure,
)
from services.engine.procedures.query_step import QueryStepExecutor
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    Procedure,
    Step,
    StepInput,
    StepKind,
    Trigger,
)

_EVENT_ROWS = [
    {"event_id": "e1", "measured_value": 95.0},
    {"event_id": "e2", "measured_value": 10.0},
]


class _FakeAdapter:
    """Protocol-complete fake serving OperationalEvent rows."""

    vertical_name = "aquaculture"

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def fetch_objects(
        self, object_type: str, filter_expr: str | None = None, limit: int = 1000
    ) -> list[dict[str, Any]]:
        self.calls.append(object_type)
        return list(_EVENT_ROWS) if object_type == "OperationalEvent" else []

    async def fetch_links(
        self, link_type: str, from_pk: str | None = None, to_pk: str | None = None
    ) -> list[dict[str, Any]]:
        return []

    def stream_events(
        self, event_type: str, since: datetime | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        raise NotImplementedError


class _GatedAction:
    """Stub gated-action executor — records its input, emits a plain artifact."""

    def __init__(self) -> None:
        self.inputs: list[list[Any]] = []

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        self.inputs.append(list(input_set))
        return StepOutcome(output=[{"action": "aerate"}])


def _agent() -> Agent:
    return Agent(
        agent_id="pond_agent",
        name="Pond Agent",
        autonomy_ceiling=Autonomy.GATED,
        allowed=AgentAllowed(
            step_kinds=[],
            action_handlers=["start_aerator"],
            object_types=["OperationalEvent"],
        ),
    )


def _procedure() -> Procedure:
    return Procedure(
        procedure_id="read_bound_round",
        title="Read-bound Round",
        run_by="pond_agent",
        trigger=Trigger.MANUAL,
        steps=[
            Step(
                step_id="read",
                name="Read events",
                kind=StepKind.QUERY,
                input=StepInput(reads=["OperationalEvent"]),
            ),
            Step(
                step_id="judge",
                name="Judge",
                kind=StepKind.EVALUATE,
                threshold=90.0,
                direction="above",
            ),
            Step(
                step_id="act",
                name="Aerate",
                kind=StepKind.ACTION,
                handler="start_aerator",
                input=StepInput(where={"verdict": "breach"}),
            ),
        ],
    )


async def test_in_memory_path_end_to_end_reads_judges_and_suspends() -> None:
    """AC-10: load gate (real aquaculture ontology) + executor agree; the run
    reads via the declared binding, judges the FETCHED set, and suspends at
    the gated action with only the breach entity threaded through."""
    adapter = _FakeAdapter()
    ontology_names = frozenset(m.name for m in load_ontology_meta("aquaculture").object_types)
    action = _GatedAction()
    executors: dict[StepKind, StepExecutor] = {
        StepKind.QUERY: QueryStepExecutor(adapter=adapter, object_type_names=ontology_names),
        StepKind.EVALUATE: EvaluateStepExecutor(),
        StepKind.ACTION: action,
    }
    result = await run_procedure(
        _procedure(), _agent(), executors, vertical="aquaculture", run_id="run-ac10"
    )
    assert result.run.status == "waiting_human"  # suspended at the gated action
    assert adapter.calls == ["OperationalEvent"]  # declared==dispatched through the real path
    statuses = [sr.step_id for sr in result.step_results]
    assert statuses == ["read", "judge", "act"]
    read_result = result.step_results[0]
    assert read_result.artifact == {"output_set": _EVENT_ROWS}
    [provenance] = read_result.reasoning_trace
    assert provenance["kind"] == "read_provenance"
    assert provenance["fetched_count"] == 2
    # the judge saw the FETCHED set; only the breach entity reaches the gate
    assert action.inputs == [[{"event_id": "e1", "measured_value": 95.0, "verdict": "breach"}]]


class _DatetimeAdapter(_FakeAdapter):
    """Rows carrying a datetime — the known JSONB-persistence trap."""

    async def fetch_objects(
        self, object_type: str, filter_expr: str | None = None, limit: int = 1000
    ) -> list[dict[str, Any]]:
        self.calls.append(object_type)
        return [{"event_id": "e1", "measured_value": 95.0, "ts": datetime(2026, 7, 4, 1, 0)}]


async def test_fetched_rows_are_json_normalized_at_the_adapter_boundary() -> None:
    """Disclosed Step-3 coercion: a real adapter's datetime-carrying rows are
    JSON-normalized once at the boundary, so the write-ahead JSONB artifact can
    persist any adapter's output (keys/shape unchanged; scalar TYPE coerces)."""
    adapter = _DatetimeAdapter()
    ontology_names = frozenset(m.name for m in load_ontology_meta("aquaculture").object_types)
    executor = QueryStepExecutor(adapter=adapter, object_type_names=ontology_names)
    outcome = await executor.execute(
        Step(
            step_id="read",
            name="Read",
            kind=StepKind.QUERY,
            input=StepInput(reads=["OperationalEvent"]),
        ),
        [],
        RunContext(agent=_agent(), vertical="aquaculture"),
    )
    [row] = outcome.output
    assert row["measured_value"] == 95.0  # numeric values untouched
    assert row["ts"] == "2026-07-04 01:00:00"  # datetime coerced to its str
    import json as _json

    _json.dumps(outcome.output)  # the whole set is JSONB-safe by construction
