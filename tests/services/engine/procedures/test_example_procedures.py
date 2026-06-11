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
    fan-out: gated aerate over the breach set, a gated escalation proposal over the
    watch set (ADR-0019 / PLAN-0022 SD-1=a — replaced the pre-amendment visual-check
    human_task), auto summary over the whole verdict set."""
    spec = load_procedures("aquaculture")
    proc = next(p for p in spec.procedures if p.procedure_id == "morning_pond_health_round")
    assert proc.trigger is Trigger.MANUAL  # only manual is runnable in Phase 1 (L-1)
    assert proc.terminal == "summary"
    by_id = {s.step_id: s for s in proc.steps}

    judge = by_id["judge"]
    assert judge.kind is StepKind.EVALUATE
    # PLAN-0022 Step 3: the authored band the deterministic evaluate executor reads.
    assert (judge.threshold, judge.direction, judge.watch_margin) == (4.0, "below", 1.0)

    aerate = by_id["aerate"]
    assert aerate.kind is StepKind.ACTION
    assert aerate.autonomy is Autonomy.GATED
    assert aerate.handler == "start_emergency_aerator"  # PLAN-0019 B: the real action_type
    assert aerate.input is not None
    assert aerate.input.from_step == "judge"
    assert aerate.input.where == {"verdict": "breach"}

    escalate = by_id["escalate_watch"]
    assert escalate.kind is StepKind.ACTION
    assert escalate.autonomy is Autonomy.GATED  # the human decides on the ambiguous band
    assert escalate.handler == "increase_water_exchange"  # the author's precautionary handler
    assert escalate.input is not None
    assert escalate.input.from_step == "judge"
    assert escalate.input.where == {"verdict": "watch"}

    summary = by_id["summary"]
    assert summary.kind is StepKind.ACTION
    assert summary.autonomy is Autonomy.AUTO
    assert summary.input is not None
    assert summary.input.from_step == "judge"
    assert summary.input.where is None  # the whole verdict set
