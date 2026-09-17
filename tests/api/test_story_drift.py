"""PLAN-0126 AC-4 — the story's data block equals the REAL ontology, procedure, rules and seed.

The explainer (``services/api/static/story/``) narrates the fleet's governed repair path
from one strict-JSON block in ``story-data.js``. The page evaluates no business rule
(SD-3 = b): it renders whatever the block says. So the block is only honest while it
equals the system, and this module is what holds it there — every assertion reads a
REAL producer, never a copy of the block:

* the ontology through ``code_generator.load_doc`` (and ``generate_all`` for the emitters),
* the procedure through ``load_procedures("fleet_maintenance")``,
* the sourcing rule through ``sourcing.compute_three_quote`` and its constants,
* the seed through ``synthetic.truck_records()`` / ``synthetic._fixture_events()``.

A self-consistency check (a count agreeing with its own list) would stay green on a
wrong value, so there is exactly one of those here — (k), the well-formedness of the
block itself — and it is not what closes AC-4.

One assertion per test, so a mutation's RED names the claim it broke (PLAN-0126 §4.1).
Each test prints what it measured.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

from services.engine.code_generator import (
    _ORM_COMMITTED_DEST,
    _PYDANTIC_COMMITTED_DEST,
    generate_all,
    load_doc,
)
from services.engine.procedures.spec import Procedure, load_procedures
from tests.api.story_source import BLOCK_BEGIN, BLOCK_END, REPO_ROOT, STORY_DIR, extract_block
from verticals.fleet_maintenance import sourcing
from verticals.fleet_maintenance.data_adapter import synthetic

_STORY_DATA = STORY_DIR / "story-data.js"
_ONTOLOGY = REPO_ROOT / "verticals/fleet_maintenance/ontology/fleet_maintenance_v0.yaml"
_VERTICAL = "fleet_maintenance"
_PROCEDURE_ID = "governed_repair_approval"


def _block() -> dict[str, Any]:
    return extract_block(_STORY_DATA.read_text(encoding="utf-8"))


def _ontology() -> dict[str, Any]:
    return load_doc(_ONTOLOGY)


def _procedure() -> Procedure:
    matches = [p for p in load_procedures(_VERTICAL).procedures if p.procedure_id == _PROCEDURE_ID]
    assert len(matches) == 1, f"{_PROCEDURE_ID} occurs {len(matches)}x in the fleet procedures"
    return matches[0]


def _step(procedure: Procedure, step_id: str) -> Any:
    return next(step for step in procedure.steps if step.step_id == step_id)


def _real_ladder() -> list[tuple[int, str]]:
    content = _step(_procedure(), "approve").governance_content
    return [(int(tier.min_amount), str(tier.approver_role)) for tier in content.tiers]


def _real_ceiling() -> float:
    ceilings = {truck["minor_repair_ceiling_thb"] for truck in synthetic.truck_records()}
    assert len(ceilings) == 1, f"the seed trucks no longer share one ceiling: {ceilings}"
    return float(ceilings.pop())


# (a)
def test_object_types_equal_the_ontology() -> None:
    real = list(_ontology()["object_types"])
    pinned = _block()["ontology"]["object_types"]
    print(f"real={len(real)} pinned={len(pinned)}")
    assert (sorted(pinned), len(pinned)) == (sorted(real), len(real))


# (b)
def test_link_types_equal_the_ontology() -> None:
    real = sorted(
        (name, spec["from"], spec["to"]) for name, spec in _ontology()["link_types"].items()
    )
    pinned = sorted(tuple(row) for row in _block()["ontology"]["link_types"])
    print(f"real={len(real)} pinned={len(pinned)}")
    assert pinned == real


# (c)
def test_undeclared_refs_equal_the_refs_the_ontology_leaves_undeclared() -> None:
    """``type: ref`` properties between this ontology's own types with no link_types pair."""
    doc = _ontology()
    types = doc["object_types"]
    declared = {(spec["from"], spec["to"]) for spec in doc["link_types"].values()}
    refs = {
        (type_name, prop["target"])
        for type_name, spec in types.items()
        for prop in (spec.get("properties") or {}).values()
        if prop.get("type") == "ref" and prop.get("target") in types
    }
    real = sorted(refs - declared)
    pinned = sorted(tuple(row) for row in _block()["ontology"]["undeclared_refs"])
    print(f"refs={len(refs)} declared={len(declared)} undeclared_real={real}")
    assert real, "the computed undeclared set is empty — the reading found no refs at all"
    assert pinned == real


# (d)
def test_steps_and_gates_equal_the_loaded_procedure() -> None:
    procedure = _procedure()
    block = _block()["procedure"]
    real_steps = [step.step_id for step in procedure.steps]
    real_gates = {
        step.step_id: step.governance_content.kind
        for step in procedure.steps
        if step.governance_content is not None
    }
    quote_gate = _step(procedure, "quote_gate").governance_content
    approve = _step(procedure, "approve")
    print(f"real_steps={real_steps} real_gates={real_gates} approve_autonomy={approve.autonomy}")
    assert (
        [s["id"] for s in block["steps"]],
        {k: v["kind"] for k, v in block["gates"].items()},
        block["gates"]["quote_gate"]["criterion"] in [rule.criterion for rule in quote_gate.rules],
        block["gates"]["approve"]["autonomy"],
    ) == (real_steps, real_gates, True, str(approve.autonomy))


# (d2) — s309: act 4's sub-line named `fulfill` as the step with llm_assist, by hand, while the
# real llm_assist sits on `approve` and fulfill's is null. The page now reads the step from here.
def test_llm_assist_steps_equal_the_loaded_procedure() -> None:
    real = [
        step.step_id
        for step in _procedure().steps
        if step.facet is not None and step.facet.llm_assist is not None
    ]
    pinned = _block()["procedure"]["llm_assist_steps"]
    print(f"real={real} pinned={pinned}")
    assert pinned == real


# (e)
def test_tiers_equal_the_loaded_doa_ladder() -> None:
    real = _real_ladder()
    pinned = [(tier["min_amount"], tier["role"]) for tier in _block()["rules"]["tiers"]]
    print(f"real={real}")
    assert pinned == real


# (f)
def test_sod_and_event_kind_equal_the_loaded_procedure() -> None:
    procedure = _procedure()
    block = _block()["procedure"]
    real_sod = [sorted(constraint.distinct_steps) for constraint in procedure.separation_of_duties]
    real_kind = procedure.event_trigger.event_kind if procedure.event_trigger else None
    print(f"real_sod={real_sod} real_event_kind={real_kind}")
    assert (
        block["id"],
        block["event_kind"],
        sorted(block["sod"]["distinct_steps"]) in real_sod,
    ) == (
        _PROCEDURE_ID,
        real_kind,
        True,
    )


# (g)
def test_rule_constants_equal_sourcing_and_the_seed() -> None:
    rules = _block()["rules"]
    ceiling = _real_ceiling()
    print(
        f"threshold real={sourcing.THREE_QUOTE_THRESHOLD_THB} "
        f"pinned={rules['three_quote_threshold_thb']} "
        f"vendors real={sourcing.MIN_DISTINCT_VENDORS} pinned={rules['min_distinct_vendors']} "
        f"ceiling seed={ceiling} pinned={rules['minor_repair_ceiling_thb']}"
    )
    assert (
        Decimal(rules["three_quote_threshold_thb"]),
        rules["min_distinct_vendors"],
        float(rules["minor_repair_ceiling_thb"]),
    ) == (sourcing.THREE_QUOTE_THRESHOLD_THB, sourcing.MIN_DISTINCT_VENDORS, ceiling)


# (h)
def test_every_case_outcome_is_the_real_rules_outcome() -> None:
    """``expected`` is PINNED: each value is what the real functions produce for the case."""
    ladder = _real_ladder()
    ceiling = _real_ceiling()
    mismatches = []
    for index, case in enumerate(_block()["cases"]):
        passed, basis = sourcing.compute_three_quote(
            amount_thb=Decimal(case["amount_thb"]),
            distinct_vendor_count=case["distinct_vendors"],
            has_sole_source_justification=case["sole_source"],
        )
        breach = case["amount_thb"] >= ceiling
        role = [r for floor, r in ladder if case["amount_thb"] >= floor][-1]
        outcome = "ok" if not breach else ("approved" if passed else "fail")
        real = {
            "breach": breach,
            "sourcing_pass": passed,
            "basis": basis,
            "tier_role": role,
            "outcome": outcome,
        }
        print(f"case[{index}] {case['truck']} {case['amount_thb']} real={real}")
        if case["expected"] != real:
            mismatches.append((index, case["expected"], real))
    assert mismatches == [], f"pinned vs real: {mismatches}"


# (i)
def test_non_illustrative_cases_are_seeded_and_the_illustrative_one_is_not() -> None:
    """Matched against the SEED alone (``_fixture_events``), never ``operational_events()``.

    ``operational_events()`` overlays live cases from ``case_projection``'s module-level
    view, which ``refresh(session)`` fills — so its content depends on which tests ran
    first. The seed does not.
    """
    rows = synthetic._fixture_events()
    cases = _block()["cases"]

    def seeded(case: dict[str, Any]) -> bool:
        return any(
            row.get("truck_id") == case["truck"]
            and row.get("measured_value") == float(case["amount_thb"])
            and row.get("three_quote_basis") == case["expected"]["basis"]
            for row in rows
        )

    real_cases = [c for c in cases if not c["illustrative"]]
    seed_matches = sum(1 for c in real_cases if seeded(c))
    illustrative_matches = sum(1 for c in cases if c["illustrative"] and seeded(c))
    print(
        f"seed_rows={len(rows)} seed_matches={seed_matches} "
        f"illustrative_matches={illustrative_matches}"
    )
    # One comparison, not `a and b`: a conjunction stops at its first false operand, so a
    # single probe could only ever witness one half of it (tools/probe_coverage.py flags it).
    assert (seed_matches > 0, seed_matches, illustrative_matches) == (True, len(real_cases), 0)


# (j)
def test_emitter_keys_equal_generate_all(tmp_path: Path) -> None:
    outputs = generate_all(_ONTOLOGY, tmp_path)
    pinned = set(_block()["emitters"])
    outside = [name for name, path in outputs.items() if tmp_path not in Path(path).parents]
    print(f"real={sorted(outputs)} outside_tmp={outside}")
    assert (
        pinned,
        outside,
        _VERTICAL in _ORM_COMMITTED_DEST,
        _VERTICAL in _PYDANTIC_COMMITTED_DEST,
    ) == (
        set(outputs),
        [],
        False,
        False,
    )


# (k)
def test_the_block_is_well_formed() -> None:
    """Well-formedness only — this is the one self-referential check, and closes nothing."""
    source = _STORY_DATA.read_text(encoding="utf-8")
    counts = (source.count(BLOCK_BEGIN), source.count(BLOCK_END))
    block = extract_block(source)
    empties = [
        key
        for key, value in {
            "object_types": block["ontology"]["object_types"],
            "link_types": block["ontology"]["link_types"],
            "undeclared_refs": block["ontology"]["undeclared_refs"],
            "emitters": block["emitters"],
            "steps": block["procedure"]["steps"],
            "tiers": block["rules"]["tiers"],
            "cases": block["cases"],
        }.items()
        if not value
    ]
    print(f"delimiters={counts} empties={empties} cases={len(block['cases'])}")
    assert (counts, empties, len(block["cases"]) >= 3) == ((1, 1), [], True)
