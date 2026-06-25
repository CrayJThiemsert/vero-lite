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
    BandSource,
    DecisionCondition,
    GateKind,
    Procedure,
    Step,
    StepFacet,
    StepKind,
    StepTiers,
    Trigger,
    load_procedures,
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


# --- PLAN-0022 Step 3 (SD-5=a): the authored band + handler-tier taxonomy -----


def test_evaluate_step_accepts_the_authored_band() -> None:
    step = Step(
        step_id="judge",
        name="Judge",
        kind=StepKind.EVALUATE,
        threshold=4.0,
        direction="below",
        watch_margin=1.0,
    )
    assert step.threshold == 4.0
    assert step.direction == "below"
    assert step.watch_margin == 1.0


def test_band_fields_are_optional_on_evaluate() -> None:
    """AC-9: a band-less evaluate step (today's specs) still loads unchanged."""
    step = Step(step_id="judge", name="Judge", kind=StepKind.EVALUATE)
    assert step.threshold is None and step.direction is None and step.watch_margin is None


@pytest.mark.parametrize("field", ["threshold", "direction", "watch_margin"])
@pytest.mark.parametrize("kind", [StepKind.QUERY, StepKind.ACTION, StepKind.HUMAN_TASK])
def test_non_evaluate_step_rejects_band_fields(field: str, kind: StepKind) -> None:
    value: float | str = "below" if field == "direction" else 4.0
    raw = {"step_id": "s", "name": "S", "kind": kind.value, field: value}
    with pytest.raises(ValidationError, match=f"{field} applies to evaluate steps only"):
        Step.model_validate(raw)


def test_watch_margin_without_threshold_rejected() -> None:
    with pytest.raises(ValidationError, match="require a threshold"):
        Step(step_id="judge", name="Judge", kind=StepKind.EVALUATE, watch_margin=1.0)


def test_direction_without_threshold_rejected() -> None:
    with pytest.raises(ValidationError, match="require a threshold"):
        Step(step_id="judge", name="Judge", kind=StepKind.EVALUATE, direction="below")


def test_negative_watch_margin_rejected() -> None:
    with pytest.raises(ValidationError):
        Step(
            step_id="judge",
            name="Judge",
            kind=StepKind.EVALUATE,
            threshold=4.0,
            watch_margin=-0.5,
        )


def test_action_step_accepts_tiers() -> None:
    step = Step(
        step_id="aerate",
        name="Aerate",
        kind=StepKind.ACTION,
        handler="start_emergency_aerator",
        tiers=StepTiers(
            canonical="start_emergency_aerator", acceptable=["increase_water_exchange"]
        ),
    )
    assert step.tiers is not None
    assert step.tiers.canonical == "start_emergency_aerator"
    assert step.tiers.acceptable == ["increase_water_exchange"]
    assert step.tiers.forbidden == []  # optional; defaults empty


@pytest.mark.parametrize("kind", [StepKind.QUERY, StepKind.EVALUATE, StepKind.HUMAN_TASK])
def test_non_action_step_rejects_tiers(kind: StepKind) -> None:
    with pytest.raises(ValidationError, match="tiers applies to action steps only"):
        Step(step_id="s", name="S", kind=kind, tiers=StepTiers(canonical="echo"))


def test_aquaculture_worked_example_loads_with_band_and_tiers() -> None:
    """The PLAN-0022 Step 3 worked example: the real aquaculture spec authors the
    judge step's deterministic band and the aerate step's tier taxonomy."""
    spec = load_procedures("aquaculture")
    procedure = next(p for p in spec.procedures if p.procedure_id == "morning_pond_health_round")
    judge = next(s for s in procedure.steps if s.step_id == "judge")
    assert (judge.threshold, judge.direction, judge.watch_margin) == (4.0, "below", 1.0)
    aerate = next(s for s in procedure.steps if s.step_id == "aerate")
    assert aerate.tiers is not None
    assert aerate.tiers.canonical == "start_emergency_aerator"
    assert aerate.tiers.acceptable == ["increase_water_exchange"]


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


# --- ADR-016 D2 Amendment (2026-06-25): the typed `facet` field (PLAN-0038 Step A) ---

_ALL_GATE_KINDS = [
    (GateKind.ENV_BAND, BandSource.ENV),
    (GateKind.IN_FILE_BAND, BandSource.IN_FILE),
    (GateKind.RULE_GATE, None),
    (GateKind.SCORED_RULE, None),
    (GateKind.DOA_TIER, None),
    (GateKind.NONE, None),
]


@pytest.mark.parametrize("gate_kind, band_source", _ALL_GATE_KINDS)
def test_each_gate_kind_parses(gate_kind: GateKind, band_source: BandSource | None) -> None:
    dc = DecisionCondition(gate_kind=gate_kind, band_source=band_source)
    assert dc.gate_kind is gate_kind
    assert dc.band_source is band_source


def test_env_band_carries_env_var() -> None:
    dc = DecisionCondition(
        gate_kind=GateKind.ENV_BAND,
        band_source=BandSource.ENV,
        env_var="OCT_RECOMMEND_THRESHOLD",
    )
    assert dc.env_var == "OCT_RECOMMEND_THRESHOLD"


def test_band_source_required_for_band_kind() -> None:
    with pytest.raises(ValidationError, match="band_source must be set iff gate_kind is a band"):
        DecisionCondition(gate_kind=GateKind.ENV_BAND)  # band kind, no band_source


@pytest.mark.parametrize(
    "gate_kind", [GateKind.RULE_GATE, GateKind.SCORED_RULE, GateKind.DOA_TIER, GateKind.NONE]
)
def test_band_source_rejected_on_non_band_kind(gate_kind: GateKind) -> None:
    with pytest.raises(ValidationError, match="band_source must be set iff gate_kind is a band"):
        DecisionCondition(gate_kind=gate_kind, band_source=BandSource.IN_FILE)


def test_env_var_requires_env_band_source() -> None:
    with pytest.raises(ValidationError, match="env_var applies only with band_source == env"):
        DecisionCondition(
            gate_kind=GateKind.IN_FILE_BAND, band_source=BandSource.IN_FILE, env_var="X"
        )


def test_in_file_band_stores_no_numeric_band() -> None:
    """An in_file_band facet POINTS AT the typed Step band — it carries no numeric
    value itself (AC-6, single source of truth, no re-store)."""
    dc = DecisionCondition(gate_kind=GateKind.IN_FILE_BAND, band_source=BandSource.IN_FILE)
    dumped = dc.model_dump()
    assert "threshold" not in dumped
    assert "direction" not in dumped
    assert "watch_margin" not in dumped


def test_step_facet_accepts_non_authoritative_notes() -> None:
    facet = StepFacet(
        decision_condition=DecisionCondition(gate_kind=GateKind.NONE),
        llm_assist="draft the decision summary (advisory)",
        input="the prior step's verdict set",
        output="an audit record",
        governance="ties each row to the control that governed it",
    )
    assert facet.input == "the prior step's verdict set"
    assert facet.llm_assist == "draft the decision summary (advisory)"
    assert facet.decision_condition is not None


def test_step_accepts_a_facet() -> None:
    step = Step(
        step_id="judge",
        name="Judge",
        kind=StepKind.EVALUATE,
        threshold=4.0,
        direction="below",
        facet=StepFacet(
            decision_condition=DecisionCondition(
                gate_kind=GateKind.IN_FILE_BAND, band_source=BandSource.IN_FILE
            )
        ),
    )
    assert step.facet is not None
    assert step.facet.decision_condition is not None
    assert step.facet.decision_condition.gate_kind is GateKind.IN_FILE_BAND


def test_absent_facet_is_none_backward_compatible() -> None:
    """A Step with no facet loads with facet is None — behaviour unchanged (AC-4)."""
    step = Step(step_id="q", name="Q", kind=StepKind.QUERY)
    assert step.facet is None


def test_unknown_key_rejected_on_facet_models() -> None:
    """extra='forbid' still bites on Step, StepFacet, and DecisionCondition (AC-2)."""
    with pytest.raises(ValidationError):
        Step.model_validate({"step_id": "q", "name": "Q", "kind": "query", "bogus": 1})
    with pytest.raises(ValidationError):
        StepFacet.model_validate({"bogus": 1})
    with pytest.raises(ValidationError):
        DecisionCondition.model_validate({"gate_kind": "none", "bogus": 1})


# --- PLAN-0038 Step B: the four-vertical comment→`facet:` migration (end-to-end) ---
#
# These exercise the SHIPPED procedures.yaml after the migration: every step now
# carries a typed `facet:` field (was a `# facet[...]` comment block). AC-4/AC-5
# (all four load clean + the migrated facets round-trip) and AC-6 (an in_file_band
# facet POINTS AT the typed band — it never re-stores the numeric values).

_MIGRATED_VERTICALS = ["energy", "supply_chain", "aquaculture", "procurement"]

# (vertical, procedure_id, judge_step_id) for the in-file-band judge steps — the
# facet must point at the typed Step band, not copy it (AC-6).
_IN_FILE_BAND_JUDGES = [
    ("aquaculture", "morning_pond_health_round", "judge"),
    ("procurement", "emergency_sourcing_round", "judge"),
    ("procurement", "low_stock_reorder_round", "judge_stock"),
]


def _step(vertical: str, procedure_id: str, step_id: str) -> Step:
    spec = load_procedures(vertical)
    proc = next(p for p in spec.procedures if p.procedure_id == procedure_id)
    return next(s for s in proc.steps if s.step_id == step_id)


@pytest.mark.parametrize("vertical", _MIGRATED_VERTICALS)
def test_migrated_vertical_loads_clean(vertical: str) -> None:
    """AC-4/AC-5: every shipped procedure still loads via load_procedures post-migration."""
    spec = load_procedures(vertical)
    assert spec.procedures  # at least one procedure


@pytest.mark.parametrize("vertical", _MIGRATED_VERTICALS)
def test_every_step_carries_a_facet(vertical: str) -> None:
    """Migration completeness: every step in every procedure now has a typed facet
    (the `# facet[...]` comment blocks became the real field — SD-1=a / SD-2=a)."""
    spec = load_procedures(vertical)
    for proc in spec.procedures:
        for step in proc.steps:
            assert step.facet is not None, f"{vertical}/{proc.procedure_id}/{step.step_id}"
            # every migrated facet states its decision_condition (uniform 5-facet reading)
            assert step.facet.decision_condition is not None


@pytest.mark.parametrize("vertical", _MIGRATED_VERTICALS)
def test_migrated_facets_round_trip(vertical: str) -> None:
    """AC-5: each migrated facet dumps and re-parses to an identical shape."""
    spec = load_procedures(vertical)
    for proc in spec.procedures:
        for step in proc.steps:
            assert step.facet is not None
            dumped = step.facet.model_dump()
            assert StepFacet.model_validate(dumped).model_dump() == dumped


@pytest.mark.parametrize("vertical", ["energy", "supply_chain"])
def test_env_band_judge_migrated(vertical: str) -> None:
    """The energy / supply_chain judge steps carry the env-authored band (no LLM)."""
    procedure_id = {
        "energy": "substation_health_sweep",
        "supply_chain": "cold_chain_excursion_sweep",
    }[vertical]
    facet = _step(vertical, procedure_id, "judge").facet
    assert facet is not None and facet.decision_condition is not None
    dc = facet.decision_condition
    assert dc.gate_kind is GateKind.ENV_BAND
    assert dc.band_source is BandSource.ENV
    assert dc.env_var == "OCT_RECOMMEND_THRESHOLD"
    assert facet.llm_assist is None  # determinism invariant — no LLM in the judge


@pytest.mark.parametrize("vertical, procedure_id, step_id", _IN_FILE_BAND_JUDGES)
def test_in_file_band_facet_points_at_typed_band(
    vertical: str, procedure_id: str, step_id: str
) -> None:
    """AC-6: an in_file_band facet POINTS AT the typed Step band — the numeric values
    live ONLY on the Step (threshold/direction/...), never re-stored on the facet."""
    step = _step(vertical, procedure_id, step_id)
    # the Step still carries the authored numeric band (single source of truth)
    assert step.threshold is not None
    assert step.facet is not None and step.facet.decision_condition is not None
    dc = step.facet.decision_condition
    assert dc.gate_kind is GateKind.IN_FILE_BAND
    assert dc.band_source is BandSource.IN_FILE
    # the facet's decision_condition carries NO numeric band of its own
    dumped = dc.model_dump()
    for numeric in ("threshold", "direction", "watch_margin"):
        assert numeric not in dumped


def test_procurement_governance_gate_kinds_migrated() -> None:
    """The AT-2 governance gates map to their discriminated gate_kinds (no band_source)."""
    proc_id = "emergency_sourcing_round"
    expected = {
        "source": GateKind.SCORED_RULE,
        "compliance": GateKind.RULE_GATE,
        "approve": GateKind.DOA_TIER,
    }
    for step_id, gate_kind in expected.items():
        facet = _step("procurement", proc_id, step_id).facet
        assert facet is not None and facet.decision_condition is not None
        assert facet.decision_condition.gate_kind is gate_kind
        assert facet.decision_condition.band_source is None  # non-band kinds
    # the scored-rule source step still records its advisory LLM summary (governed ≠ generated)
    source_facet = _step("procurement", proc_id, "source").facet
    assert source_facet is not None and source_facet.llm_assist is not None
    assert "summarise" in source_facet.llm_assist


def test_no_decision_steps_use_gate_kind_none() -> None:
    """Reads / mechanical writes / audit terminals migrate to gate_kind: none."""
    for vertical, proc_id, step_id in [
        ("energy", "substation_health_sweep", "read_readings"),
        ("procurement", "emergency_sourcing_round", "intake"),
        ("procurement", "emergency_sourcing_round", "issue_po"),
        ("aquaculture", "morning_pond_health_round", "summary"),
    ]:
        facet = _step(vertical, proc_id, step_id).facet
        assert facet is not None and facet.decision_condition is not None
        assert facet.decision_condition.gate_kind is GateKind.NONE
        assert facet.decision_condition.band_source is None
