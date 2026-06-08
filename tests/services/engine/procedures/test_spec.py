"""PLAN-0019 Part A — Procedure / Step / Agent spec models + loader (ADR-016 D2).

Pure-Python (no DB): exercises the validated spec shapes, the D3 autonomy
invariant (autonomy on ``action`` only, default ``gated``), cross-reference
validation (``run_by`` resolves), and malformed-spec rejection (the A-1 negative
cases). The example procedures.yaml per vertical is authored later (a later step);
these tests use inline fixtures.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from services.engine.procedures.spec import (
    Autonomy,
    Procedure,
    Step,
    StepKind,
    Trigger,
    load_procedures_file,
    procedures_path,
)

_VALID_YAML = """\
version: 0
namespace: testvert
agents:
  round_agent:
    name: Round Agent
    llm_model: gpt-oss:20b
    autonomy_ceiling: gated
    allowed:
      step_kinds: [query, evaluate, action, human_task]
      action_handlers: [echo]
procedures:
  morning_round:
    title: Morning Round
    goal: Keep every pond above the dissolved-oxygen floor.
    run_by: round_agent
    trigger: schedule
    steps:
      - step_id: read_do
        name: Read DO per pond
        kind: query
      - step_id: judge
        name: Judge vs threshold
        kind: evaluate
      - step_id: aerate
        name: Propose emergency aerator
        kind: action
      - step_id: visual_check
        name: Technician visual check
        kind: human_task
      - step_id: summary
        name: Write round summary
        kind: action
        autonomy: auto
    terminal: summary
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "procedures.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_loads_valid_spec(tmp_path: Path) -> None:
    spec = load_procedures_file(_write(tmp_path, _VALID_YAML), vertical="testvert")
    assert spec.vertical == "testvert"
    assert spec.namespace == "testvert"
    assert [a.agent_id for a in spec.agents] == ["round_agent"]
    assert spec.agents[0].allowed.action_handlers == ["echo"]

    proc = spec.procedures[0]
    assert proc.procedure_id == "morning_round"
    assert proc.run_by == "round_agent"
    assert proc.trigger is Trigger.SCHEDULE  # schedule LOADS (runnability is enforced later, L-1)
    assert proc.terminal == "summary"
    assert [s.kind for s in proc.steps] == [
        StepKind.QUERY,
        StepKind.EVALUATE,
        StepKind.ACTION,
        StepKind.HUMAN_TASK,
        StepKind.ACTION,
    ]
    # the gated action defaults; the explicit auto action stays auto (D3)
    assert proc.steps[2].autonomy is Autonomy.GATED
    assert proc.steps[4].autonomy is Autonomy.AUTO


def test_action_step_defaults_to_gated() -> None:
    step = Step(step_id="a", name="A", kind=StepKind.ACTION)
    assert step.autonomy is Autonomy.GATED  # D3 safe-by-default (opt-out, not opt-in)


def test_action_step_can_opt_into_auto() -> None:
    step = Step(step_id="a", name="A", kind=StepKind.ACTION, autonomy=Autonomy.AUTO)
    assert step.autonomy is Autonomy.AUTO


def test_query_step_carries_no_autonomy() -> None:
    step = Step(step_id="q", name="Q", kind=StepKind.QUERY)
    assert step.autonomy is None


def test_non_action_step_rejects_explicit_autonomy() -> None:
    with pytest.raises(ValidationError, match="autonomy applies to action steps only"):
        Step(step_id="q", name="Q", kind=StepKind.QUERY, autonomy=Autonomy.GATED)


def test_action_step_accepts_handler() -> None:
    step = Step(step_id="a", name="A", kind=StepKind.ACTION, handler="echo")
    assert step.handler == "echo"


def test_non_action_step_rejects_handler() -> None:
    with pytest.raises(ValidationError, match="handler applies to action steps only"):
        Step(step_id="q", name="Q", kind=StepKind.QUERY, handler="echo")


def test_run_by_must_resolve(tmp_path: Path) -> None:
    bad = _VALID_YAML.replace("run_by: round_agent", "run_by: ghost_agent")
    with pytest.raises(ValidationError, match="run_by 'ghost_agent' is not a"):
        load_procedures_file(_write(tmp_path, bad), vertical="testvert")


def test_unknown_step_kind_rejected(tmp_path: Path) -> None:
    bad = _VALID_YAML.replace("kind: query", "kind: teleport")
    with pytest.raises(ValidationError):
        load_procedures_file(_write(tmp_path, bad), vertical="testvert")


def test_unknown_field_rejected(tmp_path: Path) -> None:
    bad = _VALID_YAML.replace(
        "    run_by: round_agent\n", "    run_by: round_agent\n    bogus_field: 1\n"
    )
    with pytest.raises(ValidationError):
        load_procedures_file(_write(tmp_path, bad), vertical="testvert")


def test_duplicate_step_id_rejected() -> None:
    with pytest.raises(ValidationError, match="duplicate step_id"):
        Procedure(
            procedure_id="p",
            title="P",
            run_by="a",
            steps=[
                Step(step_id="dup", name="one", kind=StepKind.QUERY),
                Step(step_id="dup", name="two", kind=StepKind.EVALUATE),
            ],
        )


def test_empty_steps_rejected() -> None:
    with pytest.raises(ValidationError):
        Procedure(procedure_id="p", title="P", run_by="a", steps=[])


def test_procedures_path() -> None:
    assert procedures_path("aquaculture") == Path("verticals") / "aquaculture" / "procedures.yaml"
