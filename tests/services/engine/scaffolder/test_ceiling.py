"""PLAN-0091 Step 6 — the governance-ceiling detector (oracle AC-8).

AC-8's two halves, both asserted:

* a candidate that would be a **5th signature** stops the run, produces the
  comparison table, and writes **nothing** under ``tests/``;
* the **fleet golden shape** — already a baseline member — passes straight
  through without firing, so the detector is not merely "always stop".

The second is what keeps the first from being vacuous: a detector that raised
unconditionally would satisfy "stops on a new signature" while making the tool
unusable.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from services.engine.procedures.at2_signature import distinct_at2_signatures
from services.engine.scaffolder.ceiling import (
    CENSUS_ASSERTION,
    CENSUS_TEST,
    GovernanceCeilingError,
    check_ceiling,
    predict_signature,
)
from services.engine.scaffolder.intake import IntakeAnswer, IntakeRecord
from services.engine.scaffolder.ontology import emit_ontology
from services.engine.scaffolder.spine import emit_procedures

REPO_ROOT = Path(__file__).resolve().parents[4]

_FLEET_SHAPED = {
    "ontology.asset_noun": "Truck",
    "ontology.site_noun": "Depot",
    "ontology.band_property": "minor_repair_ceiling_thb",
    "ontology.action_types": "approve_repair_spend, escalate",
    # the fleet baseline row's enum surface: rule_gate {three_quote} + doa_tier THB
    "governance.rule_gate.criteria": "three_quote",
    "governance.approve.currency": "THB",
    "governance.approve.tiers": "0:head_mechanic, 5000:fleet_manager, 50000:owner",
    "governance.approve.waiver.relaxes": "three_bid",
    "governance.approve.waiver.ratifier": "owner",
    "governance.approve.sod.requester": "head_mechanic",
    "band.judge.direction": "above",
}


def _doc(**overrides: str) -> tuple[str, dict]:
    answers = dict(_FLEET_SHAPED)
    answers.update(overrides)
    record = IntakeRecord(
        namespace="fleet_demo",
        answers=[IntakeAnswer(slot_id=k, value=v) for k, v in answers.items()],
    )
    return record.namespace, emit_procedures(record, emit_ontology(record))


# --- the fingerprint is the census's, not a copy ----------------------------


def test_prediction_uses_the_shipped_loader(tmp_path: Path) -> None:
    """Predicting from the raw dict would fingerprint a shape the loader might reject."""
    namespace, doc = _doc()
    signature = predict_signature(namespace, doc, tmp_path)
    assert signature[0] == "fleet_demo"
    assert signature[1] == ("rule_gate", "doa_tier")
    assert dict(signature[2])["doa_tier"] == ("THB",)


def test_the_baseline_read_matches_the_census_source(tmp_path: Path) -> None:
    """The detector scans the same shipped verticals the census test does."""
    baseline = distinct_at2_signatures(REPO_ROOT)
    assert baseline, "no AT-2 signatures found — the scan is broken, not the repo"
    assert any(row[0] == "fleet_maintenance" for row in baseline)


# --- AC-8 half 1: a 5th signature STOPS -------------------------------------


def test_a_new_enum_surface_stops_before_any_wire(tmp_path: Path) -> None:
    """A criterion vocabulary nobody ships is a genuinely new signature."""
    namespace, doc = _doc(**{"governance.rule_gate.criteria": "roadside_photo_evidence"})
    with pytest.raises(GovernanceCeilingError) as exc:
        check_ceiling(namespace, doc, repo_root=REPO_ROOT, scratch=tmp_path)

    report = exc.value.report.render()
    assert "GOVERNANCE CEILING" in report
    assert CENSUS_TEST in report
    assert CENSUS_ASSERTION in report
    assert "Re-argue it" in report
    assert "did NOT write any wire edit" in report


def test_the_stop_report_shows_a_per_axis_delta_per_baseline_row(tmp_path: Path) -> None:
    namespace, doc = _doc(**{"governance.rule_gate.criteria": "roadside_photo_evidence"})
    with pytest.raises(GovernanceCeilingError) as exc:
        check_ceiling(namespace, doc, repo_root=REPO_ROOT, scratch=tmp_path)

    report = exc.value.report
    assert len(report.deltas) == len(report.baseline)
    for delta in report.deltas:
        assert delta.gate_composition
        assert delta.authority_quantity
        assert delta.enum_surface
    rendered = report.render()
    assert "gate composition" in rendered
    assert "authority quantity" in rendered
    assert "enum surface" in rendered


def test_a_new_currency_is_a_new_signature(tmp_path: Path) -> None:
    """The doa_tier surface IS the currency — a new one is new authority pressure."""
    namespace, doc = _doc(**{"governance.approve.currency": "USD"})
    with pytest.raises(GovernanceCeilingError):
        check_ceiling(namespace, doc, repo_root=REPO_ROOT, scratch=tmp_path)


def test_the_stop_writes_nothing_under_tests(tmp_path: Path) -> None:
    """AC-8: zero writes to `tests/` — the tool never touches the baseline.

    Asserted against the REPO, because that is where the baseline it must not
    edit actually lives.
    """
    census = REPO_ROOT / CENSUS_TEST
    before = census.read_text(encoding="utf-8")
    namespace, doc = _doc(**{"governance.rule_gate.criteria": "roadside_photo_evidence"})
    with pytest.raises(GovernanceCeilingError):
        check_ceiling(namespace, doc, repo_root=REPO_ROOT, scratch=tmp_path)
    assert census.read_text(encoding="utf-8") == before


def test_no_flag_can_move_the_baseline() -> None:
    """The ceiling is structural: there is no override parameter to find.

    A scaffolder that could quietly extend the baseline would convert a
    governance tripwire into a formality.
    """
    import ast
    import inspect

    from services.engine.scaffolder import ceiling

    # No override parameter to reach for.
    assert set(inspect.signature(check_ceiling).parameters) == {
        "namespace",
        "procedures_doc",
        "repo_root",
        "scratch",
    }

    # And structurally: the module opens exactly ONE file for writing, and it is
    # the scratch staging inside `predict_signature`. Asserted over the AST
    # rather than the source text, because the docstring legitimately NAMES the
    # baseline while explaining the rule — a text scan would be checking prose.
    tree = ast.parse(inspect.getsource(ceiling))
    writers = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"open", "write_text", "write_bytes", "unlink"}
        and any(isinstance(a, ast.Constant) and a.value == "w" for a in node.args)
    ]
    assert len(writers) == 1, f"expected one scratch write, found {len(writers)}"

    enclosing = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and any(w is inner for w in writers for inner in ast.walk(node))
    ]
    assert enclosing == ["predict_signature"]


# --- AC-8 half 2: a baseline member passes through --------------------------


def test_the_fleet_shape_passes_through_without_firing(tmp_path: Path) -> None:
    """Non-vacuity for every stop above: the detector is not "always raise".

    The fleet-shaped intake reproduces a signature already in the baseline
    (rule_gate {three_quote} + doa_tier THB), so regenerating it must NOT fire —
    otherwise the golden AC-7 regeneration could never run.
    """
    namespace, doc = _doc()
    assert check_ceiling(namespace, doc, repo_root=REPO_ROOT, scratch=tmp_path) is None
