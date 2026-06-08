"""PLAN-0019 A-10 — the three authored example procedures.yaml load + validate.

Pure-Python (no DB): asserts each shipped ``verticals/<name>/procedures.yaml``
parses, its cross-references resolve (``run_by`` -> a defined agent; ids unique),
and every procedure is RUNNABLE under its agent — kinds allowlisted, autonomy
within ceiling, handlers allowlisted, and **named-input references linear/backward**
(``validate_runnable`` raises ``ProcedureError`` otherwise). The aquaculture headline
additionally carries the breach/watch fan-out shape the A-η integration test drives.

Relative paths resolve against the repo root (pytest cwd), mirroring
``tests/services/engine/test_aquaculture_vertical.py``.
"""

from __future__ import annotations

import pytest

from services.engine.procedures.orchestrator import validate_runnable
from services.engine.procedures.spec import (
    Agent,
    Autonomy,
    StepKind,
    Trigger,
    VerticalProcedures,
    load_procedures,
)

VERTICALS = ["aquaculture", "energy", "supply_chain"]


def _agent_for(spec: VerticalProcedures, agent_id: str) -> Agent:
    return next(a for a in spec.agents if a.agent_id == agent_id)


@pytest.mark.parametrize("vertical", VERTICALS)
def test_example_procedures_load_and_validate(vertical: str) -> None:
    """Each vertical's procedures.yaml loads, and every procedure validates runnable
    under its agent (cross-refs + named-input references all check out)."""
    spec = load_procedures(vertical)
    assert isinstance(spec, VerticalProcedures)
    assert spec.vertical == vertical
    assert spec.agents, f"{vertical}: expected at least one agent"
    assert spec.procedures, f"{vertical}: expected at least one procedure"
    for proc in spec.procedures:
        agent = _agent_for(spec, proc.run_by)  # raises StopIteration if run_by is dangling
        validate_runnable(proc, agent)  # raises ProcedureError on any pre-flight violation


@pytest.mark.parametrize("vertical", VERTICALS)
def test_example_has_query_evaluate_gated_action_path(vertical: str) -> None:
    """A-10: each vertical has at least one ``query`` -> ``evaluate`` -> gated
    ``action`` path."""
    spec = load_procedures(vertical)
    kinds_seen = {s.kind for p in spec.procedures for s in p.steps}
    assert {StepKind.QUERY, StepKind.EVALUATE, StepKind.ACTION} <= kinds_seen
    gated_actions = [
        s
        for p in spec.procedures
        for s in p.steps
        if s.kind is StepKind.ACTION and s.autonomy is Autonomy.GATED
    ]
    assert gated_actions, f"{vertical}: expected at least one gated action step"


@pytest.mark.parametrize("vertical", VERTICALS)
def test_example_action_handlers_within_allowlist(vertical: str) -> None:
    """Every action step's handler is in its agent's allowlist (blast-radius bound)."""
    spec = load_procedures(vertical)
    for proc in spec.procedures:
        agent = _agent_for(spec, proc.run_by)
        for step in proc.steps:
            if step.kind is StepKind.ACTION:
                assert step.handler is not None, f"{vertical}/{step.step_id}: needs a handler"
                assert step.handler in agent.allowed.action_handlers


def test_aquaculture_headline_fan_out_shape() -> None:
    """The headline 'Morning Pond Health Round' carries the breach/watch named-input
    fan-out: gated aerate over the breach set, human_task visual over the watch set,
    auto summary over the whole verdict set."""
    spec = load_procedures("aquaculture")
    proc = next(p for p in spec.procedures if p.procedure_id == "morning_pond_health_round")
    assert proc.trigger is Trigger.MANUAL  # only manual is runnable in Phase 1 (L-1)
    assert proc.terminal == "summary"
    by_id = {s.step_id: s for s in proc.steps}

    aerate = by_id["aerate"]
    assert aerate.kind is StepKind.ACTION
    assert aerate.autonomy is Autonomy.GATED
    assert aerate.handler == "echo"
    assert aerate.input is not None
    assert aerate.input.from_step == "judge"
    assert aerate.input.where == {"verdict": "breach"}

    visual = by_id["visual"]
    assert visual.kind is StepKind.HUMAN_TASK
    assert visual.input is not None
    assert visual.input.from_step == "judge"
    assert visual.input.where == {"verdict": "watch"}

    summary = by_id["summary"]
    assert summary.kind is StepKind.ACTION
    assert summary.autonomy is Autonomy.AUTO
    assert summary.input is not None
    assert summary.input.from_step == "judge"
    assert summary.input.where is None  # the whole verdict set
