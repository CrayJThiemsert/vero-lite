"""PLAN-0040 Phase A (Step A1) — archetype templates load + instantiate.

The offline gate for the ``ArchetypeTemplate`` artifact (ADR-0024 D2). Pure-Python
(no DB, no LLM):

* **AC-A2** — every template in the registry instantiates to a skeleton that
  round-trips ``load_procedures`` (shape + cross-ref clean) for BOTH band-authoring
  sources (the env / in_file split).
* **AC-A8 / D4** — each template's ``gate_kind`` sequence matches the AT-1-family
  governance signature: the sole ``judge`` (evaluate) slot is a band kind, every
  other slot is ``none``, and NO AT-2-only kind (``scored_rule`` / ``rule_gate`` /
  ``doa_tier`` / ``severity_tier``) appears (a v1 skeleton that would need one is an
  abstain, never a down-classified AT-3).
* The instantiated skeleton leaves every human-author (H) governance value ABSENT
  (OQ-C C1: the schema-correct stub, never an in-field sentinel).
"""

from __future__ import annotations

import pytest

from services.engine.procedures.archetypes.template import REGISTRY, instantiate
from services.engine.procedures.generator import pipeline
from services.engine.procedures.spec import (
    BandSource,
    GateKind,
    StepKind,
    VerticalProcedures,
    parse_procedures,
)

AT1_FAMILY = ["AT-1", "AT-1b", "AT-3"]
AT2_ONLY_KINDS = {
    GateKind.SCORED_RULE,
    GateKind.RULE_GATE,
    GateKind.DOA_TIER,
    GateKind.SEVERITY_TIER,
}


def test_registry_is_the_at1_family_with_variant_bases() -> None:
    """v1 = the AT-1 family only (D7); AT-1b / AT-3 declare their AT-1 base (D2)."""
    assert set(REGISTRY) == set(AT1_FAMILY)
    assert REGISTRY["AT-1"].base is None
    assert REGISTRY["AT-1b"].base == "AT-1"
    assert REGISTRY["AT-3"].base == "AT-1"


def test_at2_only_kinds_mirrors_the_classify_abstain_guard() -> None:
    """Anti-drift tripwire: this module's ``AT2_ONLY_KINDS`` is a local copy of the
    classify-time abstain guard's set, and must never silently diverge from it.

    It drifted once already — ``severity_tier`` (the 4th AT-2 gate kind, PLAN-0074)
    was added to ``pipeline._AT2_ONLY_KINDS`` but not here, leaving
    ``test_archetype_agreement_signature`` under-strength for two PLANs. Prose in the
    module docstring did not catch it; this assertion does.

    Deliberately NOT asserted against ``draft._AT2_GATE_KINDS``: that is a *distinct*
    concept (the obligation side — which kinds owe typed ``governance_content``), as
    ``draft.py`` says in its own docstring, and PLAN-0074 grew the two under separate
    ACs. They happen to hold the same members today; pinning them equal would encode
    an invariant the design explicitly denies.
    """
    assert AT2_ONLY_KINDS == set(pipeline._AT2_ONLY_KINDS)


@pytest.mark.parametrize("archetype_id", AT1_FAMILY)
@pytest.mark.parametrize("band_source", [BandSource.IN_FILE, BandSource.ENV])
def test_template_instantiates_load_procedures_valid(
    archetype_id: str, band_source: BandSource
) -> None:
    """AC-A2: every instantiated template round-trips ``load_procedures`` (via
    ``parse_procedures``, the loader's core) for both band-authoring sources."""
    tmpl = REGISTRY[archetype_id]
    doc = instantiate(
        tmpl, procedure_id="draft_proc", title="Draft procedure", band_source=band_source
    )
    spec = parse_procedures(doc, vertical="draft")
    assert isinstance(spec, VerticalProcedures)
    assert len(spec.procedures) == 1
    proc = spec.procedures[0]
    assert proc.procedure_id == "draft_proc"
    assert proc.run_by in {a.agent_id for a in spec.agents}  # cross-ref resolves
    assert proc.terminal == tmpl.terminal_slot
    assert len(proc.steps) == len(tmpl.slots)


@pytest.mark.parametrize("archetype_id", AT1_FAMILY)
def test_skeleton_leaves_every_governance_value_absent(archetype_id: str) -> None:
    """OQ-C C1: the skeleton is a STUB — every H governance value is ABSENT (None),
    never an in-field sentinel. The judge has no band value; actions have no handler
    or tiers."""
    tmpl = REGISTRY[archetype_id]
    spec = parse_procedures(instantiate(tmpl, procedure_id="p", title="P"), vertical="draft")
    for step in spec.procedures[0].steps:
        if step.kind is StepKind.EVALUATE:
            assert (step.threshold, step.direction, step.watch_margin) == (None, None, None)
            assert step.facet is not None and step.facet.decision_condition is not None
            assert step.facet.decision_condition.env_var is None
        if step.kind is StepKind.ACTION:
            assert step.handler is None
            assert step.tiers is None


@pytest.mark.parametrize("archetype_id", AT1_FAMILY)
def test_archetype_agreement_signature(archetype_id: str) -> None:
    """AC-A8 / D4: the gate_kind sequence matches the AT-1-family signature — exactly
    one band ``judge``, every other slot ``none``, no AT-2-only kind anywhere."""
    tmpl = REGISTRY[archetype_id]
    for slot in tmpl.slots:
        assert slot.gate_kind not in AT2_ONLY_KINDS
        if slot.kind is StepKind.EVALUATE:
            assert slot.gate_kind in (GateKind.ENV_BAND, GateKind.IN_FILE_BAND)
        else:
            assert slot.gate_kind is GateKind.NONE
    judges = [s for s in tmpl.slots if s.kind is StepKind.EVALUATE]
    assert len(judges) == 1, "an AT-1-family template has exactly one band judge"


@pytest.mark.parametrize("archetype_id", AT1_FAMILY)
def test_env_band_instantiation_emits_env_gate(archetype_id: str) -> None:
    """The band-authoring split is a per-instance G/lean choice: instantiating with
    band_source=ENV emits an ``env_band`` judge (env_var still an absent H stub)."""
    tmpl = REGISTRY[archetype_id]
    spec = parse_procedures(
        instantiate(tmpl, procedure_id="p", title="P", band_source=BandSource.ENV),
        vertical="draft",
    )
    judge = next(s for s in spec.procedures[0].steps if s.kind is StepKind.EVALUATE)
    assert judge.facet is not None and judge.facet.decision_condition is not None
    assert judge.facet.decision_condition.gate_kind is GateKind.ENV_BAND
    assert judge.facet.decision_condition.band_source is BandSource.ENV
    assert judge.facet.decision_condition.env_var is None
