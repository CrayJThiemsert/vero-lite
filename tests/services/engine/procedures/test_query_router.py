"""PLAN-0064 Step 1 — :class:`QueryStepRouter` unit pins (AC-1).

Both dispatch legs (SD-1 declaration-presence), plus the SD-0 tripwire made
executable: the router lives INSIDE one ``StepKind`` slot, so the orchestrator's
``Mapping[StepKind, StepExecutor]`` contract is untouched — proven by running a
procedure through the REAL ``run_procedure`` with the router in the QUERY slot.

Deterministic, offline, no LLM, no DB.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from services.engine.procedures.orchestrator import RunContext, StepOutcome, run_procedure
from services.engine.procedures.query_router import QueryStepRouter
from services.engine.procedures.runs import PipelineRunStatus
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    Procedure,
    Step,
    StepInput,
    StepKind,
)


@dataclass
class _RecordingExecutor:
    """A stub leg that records the steps it served and returns a tagged output."""

    tag: str
    served: list[str] = field(default_factory=list)

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        self.served.append(step.step_id)
        return StepOutcome(
            output=[{"served_by": self.tag}],
            reasoning_trace=[{"kind": "query", "summary": f"stub leg '{self.tag}'"}],
        )


def _agent() -> Agent:
    return Agent(
        agent_id="router_test_agent",
        name="Router Test Agent",
        autonomy_ceiling=Autonomy.GATED,
        allowed=AgentAllowed(),  # unconstrained reads (OQ-6)
    )


def _ctx(agent: Agent) -> RunContext:
    return RunContext(agent=agent, vertical="router-test")


def _declared_step() -> Step:
    return Step(
        step_id="declared_read",
        name="A step WITH a declared read",
        kind=StepKind.QUERY,
        input=StepInput(reads=["Part"]),
    )


def _undeclared_step() -> Step:
    return Step(step_id="seeded_read", name="A step WITHOUT a declared read", kind=StepKind.QUERY)


async def test_declared_reads_route_to_the_declared_leg() -> None:
    """SD-1: ``input.reads`` non-empty ⇒ the declared executor serves the step."""
    declared = _RecordingExecutor(tag="declared")
    fallback = _RecordingExecutor(tag="fallback")
    router = QueryStepRouter(declared=declared, fallback=fallback)

    outcome = await router.execute(_declared_step(), [], _ctx(_agent()))

    assert declared.served == ["declared_read"]
    assert fallback.served == []
    assert outcome.output == [{"served_by": "declared"}]


async def test_undeclared_steps_route_to_the_fallback_leg() -> None:
    """SD-1: no declaration ⇒ the fallback (seed) executor serves the step."""
    declared = _RecordingExecutor(tag="declared")
    fallback = _RecordingExecutor(tag="fallback")
    router = QueryStepRouter(declared=declared, fallback=fallback)

    outcome = await router.execute(_undeclared_step(), [], _ctx(_agent()))

    assert fallback.served == ["seeded_read"]
    assert declared.served == []
    assert outcome.output == [{"served_by": "fallback"}]


async def test_from_step_only_input_is_not_a_declaration() -> None:
    """A ``from``-threading input with no ``reads`` is NOT a declaration — it stays
    on the fallback leg (SD-1 keys on ``reads`` presence, nothing else)."""
    declared = _RecordingExecutor(tag="declared")
    fallback = _RecordingExecutor(tag="fallback")
    router = QueryStepRouter(declared=declared, fallback=fallback)

    threaded = Step(
        step_id="threaded_read",
        name="A step threading a prior output, no declared read",
        kind=StepKind.QUERY,
        input=StepInput.model_validate({"from": "declared_read"}),
    )
    await router.execute(threaded, [], _ctx(_agent()))

    assert fallback.served == ["threaded_read"]
    assert declared.served == []


async def test_router_serves_one_stepkind_slot_through_the_real_orchestrator() -> None:
    """The SD-0 tripwire, executable: the router is a plain ``StepExecutor`` in ONE
    ``StepKind.QUERY`` slot of the unchanged ``Mapping[StepKind, StepExecutor]``
    contract — the REAL ``run_procedure`` routes two query steps to two different
    legs without any orchestrator/registry/spec change."""
    declared = _RecordingExecutor(tag="declared")
    fallback = _RecordingExecutor(tag="fallback")
    agent = _agent()
    procedure = Procedure(
        procedure_id="router-contract-pin",
        title="Router contract pin",
        goal="Two query steps, one slot, two legs.",
        run_by=agent.agent_id,
        steps=[_undeclared_step(), _declared_step()],
    )

    # A REAL vertical: the pre-flight load gate resolves the declared read against
    # the vertical's ontology, and procurement declares `Part` (PLAN-0064 fact 6).
    result = await run_procedure(
        procedure,
        agent,
        {StepKind.QUERY: QueryStepRouter(declared=declared, fallback=fallback)},
        vertical="procurement",
        run_id="run-router-contract-pin",
    )

    assert result.run.status == PipelineRunStatus.COMPLETED
    assert fallback.served == ["seeded_read"]
    assert declared.served == ["declared_read"]


def test_router_is_frozen() -> None:
    """The router is immutable — a factory builds it fresh per run/resume request
    (the registry Step-2 contract) and nothing can rebind a leg mid-run."""
    router = QueryStepRouter(
        declared=_RecordingExecutor(tag="declared"), fallback=_RecordingExecutor(tag="fallback")
    )
    with pytest.raises(AttributeError):
        router.declared = _RecordingExecutor(tag="other")  # type: ignore[misc]
