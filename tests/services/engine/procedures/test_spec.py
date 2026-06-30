"""PLAN-0019 Part A — Procedure / Step / Agent spec models + loader (ADR-016 D2).

Pure-Python (no DB): exercises the validated spec shapes, the D3 autonomy
invariant (autonomy on ``action`` only, default ``gated``), cross-reference
validation (``run_by`` resolves), and malformed-spec rejection (the A-1 negative
cases). The example procedures.yaml per vertical is authored later (a later step);
these tests use inline fixtures.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from services.engine.procedures.spec import (
    Autonomy,
    BandSource,
    ComplianceCriterion,
    ComplianceGate,
    ComplianceRule,
    DecisionCondition,
    DoaLadder,
    DoaTier,
    EmergencyWaiverPolicy,
    ExceptionPolicy,
    GateKind,
    Person,
    PrincipalAlias,
    Procedure,
    RelaxableConstraint,
    ScoredRule,
    SoDConstraint,
    SourcePolicy,
    Step,
    StepFacet,
    StepKind,
    StepTiers,
    Trigger,
    VerticalProcedures,
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


# --- ADR-0025 Step 1: the AT-2 typed governance content + D3 unrepresentable-bypass ---
#
# D2 = the discriminated `Step.governance_content` union + `Procedure.separation_of_duties`;
# D3 = bypass is UNREPRESENTABLE (no skip flag; closed waiver enum; Literal[True] guards;
# total strictly-monotonic DOA ladder). The amount/principal/role-rank-dependent SEMANTIC
# checks (resolved-tier strict escalation; requester != approver principal) are the deferred
# A2 run path (OQ-A=A1) — these tests exercise the author-time structural invariants only.


def _valid_ladder() -> DoaLadder:
    return DoaLadder(
        currency="THB",
        tiers=[
            DoaTier(min_amount=Decimal("0"), approver_role="dept_head"),
            DoaTier(min_amount=Decimal("500000"), approver_role="manager"),
            DoaTier(min_amount=Decimal("5000000"), approver_role="director"),
        ],
        emergency_waiver=EmergencyWaiverPolicy(
            relaxes=[RelaxableConstraint.THREE_BID], escalate_to="director"
        ),
    )


def test_doa_ladder_valid_total_monotonic_cover() -> None:
    ladder = _valid_ladder()
    assert ladder.kind == "doa_tier"
    assert ladder.currency == "THB"
    assert [t.min_amount for t in ladder.tiers] == [
        Decimal("0"),
        Decimal("500000"),
        Decimal("5000000"),
    ]
    assert isinstance(ladder.tiers[0].min_amount, Decimal)  # money is Decimal, never float


def test_doa_ladder_first_tier_must_start_at_zero() -> None:
    with pytest.raises(ValidationError, match="first tier's min_amount must be 0"):
        DoaLadder(
            currency="THB",
            tiers=[DoaTier(min_amount=Decimal("100"), approver_role="dept_head")],
            emergency_waiver=EmergencyWaiverPolicy(
                relaxes=[RelaxableConstraint.THREE_BID], escalate_to="director"
            ),
        )


def test_doa_ladder_floors_must_strictly_increase() -> None:
    with pytest.raises(ValidationError, match="STRICTLY increasing"):
        DoaLadder(
            currency="THB",
            tiers=[
                DoaTier(min_amount=Decimal("0"), approver_role="dept_head"),
                DoaTier(min_amount=Decimal("0"), approver_role="manager"),  # equal -> overlap
            ],
            emergency_waiver=EmergencyWaiverPolicy(
                relaxes=[RelaxableConstraint.THREE_BID], escalate_to="director"
            ),
        )


def test_doa_ladder_rejects_empty_tiers() -> None:
    with pytest.raises(ValidationError):
        DoaLadder(
            currency="THB",
            tiers=[],
            emergency_waiver=EmergencyWaiverPolicy(
                relaxes=[RelaxableConstraint.THREE_BID], escalate_to="director"
            ),
        )


def test_doa_tier_rejects_negative_amount() -> None:
    with pytest.raises(ValidationError):
        DoaTier(min_amount=Decimal("-1"), approver_role="dept_head")


def test_waiver_requires_at_least_one_relaxable() -> None:
    with pytest.raises(ValidationError):
        EmergencyWaiverPolicy(relaxes=[], escalate_to="director")


def test_waiver_cannot_name_compliance_or_sod() -> None:
    """D3: RelaxableConstraint is a CLOSED enum that cannot name compliance / SoD — so
    'waiving compliance' is structurally unrepresentable."""
    with pytest.raises(ValidationError):
        EmergencyWaiverPolicy.model_validate({"relaxes": ["compliance"], "escalate_to": "director"})


def test_waiver_justification_cannot_be_disabled() -> None:
    """D3: requires_justification is Literal[True] — omitting it is unrepresentable."""
    with pytest.raises(ValidationError):
        EmergencyWaiverPolicy.model_validate(
            {"relaxes": ["three_bid"], "escalate_to": "director", "requires_justification": False}
        )


def test_compliance_rule_always_blocks_po() -> None:
    rule = ComplianceRule(criterion=ComplianceCriterion.AVL, spec="supplier on the AVL")
    assert rule.blocks_po is True
    with pytest.raises(ValidationError):
        # D3: a non-blocking 'compliance' rule is unrepresentable (blocks_po is Literal[True])
        ComplianceRule.model_validate({"criterion": "avl", "spec": "x", "blocks_po": False})


def test_compliance_gate_requires_at_least_one_rule() -> None:
    with pytest.raises(ValidationError):
        ComplianceGate(rules=[])


def test_scored_rule_requires_at_least_one_criterion() -> None:
    with pytest.raises(ValidationError):
        ScoredRule(
            criteria=[],
            default_source=SourcePolicy.ON_CONTRACT,
            exception_policy=ExceptionPolicy.RFQ_AVL_LOGGED,
        )


def test_at2_governance_union_discriminates_on_kind() -> None:
    """The discriminated union routes each `kind` to its variant (ADR-0025 D2)."""
    step = Step.model_validate(
        {
            "step_id": "approve",
            "name": "Approve",
            "kind": "action",
            "governance_content": {
                "kind": "doa_tier",
                "currency": "THB",
                "tiers": [{"min_amount": "0", "approver_role": "dept_head"}],
                "emergency_waiver": {"relaxes": ["three_bid"], "escalate_to": "director"},
            },
        }
    )
    assert isinstance(step.governance_content, DoaLadder)
    assert step.governance_content.currency == "THB"


def test_step_governance_content_defaults_absent() -> None:
    """A step without AT-2 content carries governance_content = None (additive; AC-6)."""
    step = Step(step_id="q", name="Q", kind=StepKind.QUERY)
    assert step.governance_content is None


def test_at2_content_extra_forbid_bites() -> None:
    with pytest.raises(ValidationError):
        DoaTier.model_validate({"min_amount": "0", "approver_role": "x", "bogus": 1})


def test_sod_constraint_requires_two_distinct_steps() -> None:
    with pytest.raises(ValidationError):
        SoDConstraint(distinct_steps=frozenset({"intake"}))  # < 2 -> degenerate


def test_sod_constraint_accepts_two_steps() -> None:
    sod = SoDConstraint(distinct_steps=frozenset({"intake", "approve"}))
    assert sod.distinct_steps == frozenset({"intake", "approve"})


def test_procedure_separation_of_duties_defaults_empty() -> None:
    proc = Procedure(
        procedure_id="p",
        title="P",
        run_by="a",
        steps=[Step(step_id="s", name="S", kind=StepKind.QUERY)],
    )
    assert proc.separation_of_duties == []


def test_procedure_sod_rejects_dangling_step_reference() -> None:
    with pytest.raises(ValidationError, match="references unknown step_id"):
        Procedure(
            procedure_id="p",
            title="P",
            run_by="a",
            steps=[
                Step(step_id="intake", name="Intake", kind=StepKind.QUERY),
                Step(step_id="approve", name="Approve", kind=StepKind.ACTION),
            ],
            separation_of_duties=[SoDConstraint(distinct_steps=frozenset({"intake", "ghost"}))],
        )


def test_procedure_sod_accepts_valid_step_references() -> None:
    proc = Procedure(
        procedure_id="p",
        title="P",
        run_by="a",
        steps=[
            Step(step_id="intake", name="Intake", kind=StepKind.QUERY),
            Step(step_id="approve", name="Approve", kind=StepKind.ACTION),
        ],
        separation_of_duties=[SoDConstraint(distinct_steps=frozenset({"intake", "approve"}))],
    )
    assert len(proc.separation_of_duties) == 1


# --- ADR-0026 A1a (PLAN-0043 Steps 1-2): principal identity + the step->required-role map ---


def test_sod_constraint_required_roles_defaults_empty() -> None:
    """SD-1=(b): required_roles is optional (default empty) so author-time load stays
    backward-compatible; an unmapped constrained step is unresolvable -> the run-check fails
    closed (ADR-0026 D4), which is a run-time concern, not an author-time one."""
    sod = SoDConstraint(distinct_steps=frozenset({"intake", "approve"}))
    assert sod.required_roles == {}


def test_sod_constraint_required_roles_accepts_constrained_steps() -> None:
    """SD-1=(b): the step->required-role map names the RoleId each constrained step requires."""
    sod = SoDConstraint(
        distinct_steps=frozenset({"intake", "approve"}),
        required_roles={"intake": "requester", "approve": "dept_head"},
    )
    assert sod.required_roles == {"intake": "requester", "approve": "dept_head"}


def test_sod_constraint_required_roles_rejects_dangling_key() -> None:
    """ADR-0026 D2: a required_role naming a step outside distinct_steps is an authoring error."""
    with pytest.raises(ValidationError, match="not in distinct_steps"):
        SoDConstraint(
            distinct_steps=frozenset({"intake", "approve"}),
            required_roles={"ghost": "dept_head"},
        )


def test_person_requires_at_least_one_role() -> None:
    """ADR-0026 D1/D2: a principal with no role binding cannot be resolved against a
    required_role — the role->principal binding must carry >=1 role."""
    with pytest.raises(ValidationError):
        Person(person_id="alice", name="Alice", roles=frozenset())


def test_person_accepts_pk_and_role_binding() -> None:
    p = Person(person_id="alice", name="Alice", roles=frozenset({"requester", "dept_head"}))
    assert p.person_id == "alice"
    assert p.roles == frozenset({"requester", "dept_head"})


def test_principal_alias_requires_two_members() -> None:
    """OQ-3=(c)/SD-2=(b): an alias group declares >=2 identity keys denote ONE human (a
    single-member 'alias' collapses nothing and is degenerate)."""
    with pytest.raises(ValidationError):
        PrincipalAlias(alias_id="g1", members=frozenset({"alice"}))


def test_principal_alias_accepts_two_members() -> None:
    alias = PrincipalAlias(alias_id="g1", members=frozenset({"alice", "alice_oncall"}))
    assert alias.members == frozenset({"alice", "alice_oncall"})


def test_vertical_principals_default_empty_backward_compatible() -> None:
    """A vertical that declares no principals loads unchanged (AC-8 spirit — additive)."""
    vp = VerticalProcedures(vertical="v", agents=[], procedures=[])
    assert vp.principals == []
    assert vp.principal_aliases == []


def test_vertical_rejects_duplicate_person_id() -> None:
    with pytest.raises(ValidationError, match="duplicate person_id"):
        VerticalProcedures(
            vertical="v",
            agents=[],
            procedures=[],
            principals=[
                Person(person_id="alice", name="Alice", roles=frozenset({"requester"})),
                Person(person_id="alice", name="Alias", roles=frozenset({"dept_head"})),
            ],
        )


def test_vertical_rejects_alias_member_unknown_person() -> None:
    """ADR-0026 D4: a typo'd alias member is an authoring error, not a collapse that never
    fires (a fail-closed trigger that silently references nobody is worse than a load error)."""
    with pytest.raises(ValidationError, match="unknown person_id"):
        VerticalProcedures(
            vertical="v",
            agents=[],
            procedures=[],
            principals=[Person(person_id="alice", name="Alice", roles=frozenset({"requester"}))],
            principal_aliases=[
                PrincipalAlias(alias_id="g1", members=frozenset({"alice", "ghost"}))
            ],
        )


def test_vertical_accepts_valid_principals_and_aliases() -> None:
    vp = VerticalProcedures(
        vertical="v",
        agents=[],
        procedures=[],
        principals=[
            Person(person_id="alice", name="Alice", roles=frozenset({"requester"})),
            Person(
                person_id="alice_oncall",
                name="Alice (on-call)",
                roles=frozenset({"dept_head"}),
            ),
        ],
        principal_aliases=[
            PrincipalAlias(alias_id="g1", members=frozenset({"alice", "alice_oncall"}))
        ],
    )
    assert len(vp.principals) == 2
    assert vp.principal_aliases[0].members == frozenset({"alice", "alice_oncall"})


def test_procurement_at2_carries_typed_governance_content() -> None:
    """AC-8 (PLAN-0042 Step 2): the shipped procurement AT-2 was migrated prose->typed — each
    AT-2 step carries its MATCHING governance_content variant + the procedure carries the SoD
    constraint. Values are OQ-B B2 (DOA tiers + compliance predicates mirror the data adapter;
    scored-rule weights provisional), pending Cray sign-off."""
    spec = load_procedures("procurement")
    proc = next(p for p in spec.procedures if p.procedure_id == "emergency_sourcing_round")
    by_id = {s.step_id: s for s in proc.steps}
    assert isinstance(by_id["source"].governance_content, ScoredRule)
    assert isinstance(by_id["compliance"].governance_content, ComplianceGate)
    ladder = by_id["approve"].governance_content
    assert isinstance(ladder, DoaLadder)
    assert ladder.currency == "THB"
    assert ladder.tiers[0].min_amount == Decimal("0")  # total cover from zero spend (D3)
    assert proc.separation_of_duties  # >=1 SoD constraint (D5)
    # finding 5: low_stock_reorder_round (AT-3, no AT-2 gates) carries NO AT-2 content
    calm = next(p for p in spec.procedures if p.procedure_id == "low_stock_reorder_round")
    assert all(s.governance_content is None for s in calm.steps)
    assert calm.separation_of_duties == []


# --- PLAN-0042 Step 3: the scoped-prose-lint LOAD gate over AT-2 free-text (AC-11 / D4) ---
#
# An AT-2 procedure whose NON-AUTHORITATIVE free-text (goal / governance-bearing step
# description / tier-criterion note / waiver justification) smuggles a ฿-amount, a weight,
# or an approver-role token is REFUSED at load (Procedure._validate_at2_free_text). The
# scoped variant omits decision verbs / handler identifiers, so a hand-authored note that
# says "HUMAN approves" / names a handler still loads (finding 6).


def _doa_ladder(*, tier_note: str = "", justification: str = "") -> DoaLadder:
    return DoaLadder(
        currency="THB",
        tiers=[
            DoaTier(min_amount=Decimal("0"), approver_role="dept_head", note=tier_note),
            DoaTier(min_amount=Decimal("500000"), approver_role="director"),
        ],
        emergency_waiver=EmergencyWaiverPolicy(
            relaxes=[RelaxableConstraint.THREE_BID],
            escalate_to="director",
            justification=justification,
        ),
    )


def _at2_proc(
    *,
    goal: str = "route the compliant set to the human approver",
    desc: str = "the human gate over the compliant set",
    ladder: DoaLadder | None = None,
) -> Procedure:
    return Procedure(
        procedure_id="p",
        title="P",
        run_by="a",
        goal=goal,
        steps=[
            Step(step_id="intake", name="Intake", kind=StepKind.QUERY),
            Step(
                step_id="approve",
                name="Approve",
                kind=StepKind.ACTION,
                description=desc,
                governance_content=ladder if ladder is not None else _doa_ladder(),
            ),
        ],
        separation_of_duties=[SoDConstraint(distinct_steps=frozenset({"intake", "approve"}))],
    )


def test_at2_free_text_clean_procedure_loads() -> None:
    """A clean AT-2 procedure (no smuggled values in its free-text) constructs fine."""
    assert _at2_proc().procedure_id == "p"


def test_at2_free_text_blocks_currency_in_description() -> None:
    with pytest.raises(ValidationError, match="smuggles a governance value"):
        _at2_proc(desc="auto-approve anything under ฿50,000 without escalation")


def test_at2_free_text_blocks_weight_in_tier_note() -> None:
    with pytest.raises(ValidationError, match="smuggles a governance value"):
        _at2_proc(ladder=_doa_ladder(tier_note="weight this tier at 0.5 of the score"))


def test_at2_free_text_blocks_amount_in_waiver_justification() -> None:
    with pytest.raises(ValidationError, match="smuggles a governance value"):
        _at2_proc(ladder=_doa_ladder(justification="waive only when the spend exceeds 2M"))


def test_at2_free_text_blocks_role_token_in_goal() -> None:
    """An approver-role token (a typed DOA value) leaked into the goal prose is refused."""
    with pytest.raises(ValidationError, match="smuggles a governance value"):
        _at2_proc(goal="always route straight to director regardless of the band")


def test_at2_free_text_allows_handauthored_decision_prose() -> None:
    """A hand-authored description with decision verbs / a handler name LOADS — the scoped
    variant omits those classes; only smuggled VALUES block (AC-11 / finding 6)."""
    proc = _at2_proc(
        desc="HUMAN approves; blocks the PO on any failed criterion; handler request_approval"
    )
    assert proc.steps[1].governance_content is not None


def test_at2_free_text_gate_skipped_for_non_at2_procedure() -> None:
    """A procedure with NO AT-2 governance content is not scanned — a value in its prose is
    fine (the gate is scoped to AT-2 procedures; e.g. an in_file_band threshold echoed in a
    calm-path description)."""
    proc = Procedure(
        procedure_id="calm",
        title="Calm",
        run_by="a",
        goal="reorder anything at or below the reorder point of 100 units",
        steps=[Step(step_id="read", name="Read", kind=StepKind.QUERY, description="stock at 50")],
    )
    assert proc.procedure_id == "calm"
