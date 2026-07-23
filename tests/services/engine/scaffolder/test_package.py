"""PLAN-0091 Step 3 — the package emitter (oracle AC-4).

The claim under test is "no fabricated numbers", and the whole point of AC-4 is
that the claim is **falsifiable**: :func:`untraced_numerics` is run against the
emitted `synthetic.py`, so a future emitter that quietly inlines a plausible
demo number fails here rather than shipping a file where a guess is
indistinguishable from a customer answer.

The scanner itself is tested against known-bad input first — a scanner that
returned `[]` unconditionally would make every other assertion in this module
pass while checking nothing.
"""

from __future__ import annotations

import ast
from pathlib import Path

from services.engine.scaffolder.intake import IntakeAnswer, IntakeRecord
from services.engine.scaffolder.ontology import emit_ontology
from services.engine.scaffolder.package import (
    GUESS_MARKER,
    TRACE_PREFIX,
    emit_package,
    registrar_name,
    untraced_numerics,
    write_package,
)

_JUDGMENTS = {
    "ontology.asset_noun": "Truck",
    "ontology.site_noun": "Depot",
    "ontology.band_property": "minor_repair_ceiling_thb",
    "ontology.action_types": "approve_repair_spend, tow_to_partner_garage, escalate",
}


def _record(**extra: str) -> IntakeRecord:
    answers = dict(_JUDGMENTS)
    answers.update(extra)
    return IntakeRecord(
        namespace="fleet_demo",
        answers=[IntakeAnswer(slot_id=k, value=v) for k, v in answers.items()],
    )


def _fully_answered() -> IntakeRecord:
    return _record(
        **{
            "fixture.asset_count": "6",
            "fixture.band_value": "20000",
            "fixture.breach_value": "48000",
            "fixture.normal_value": "1200",
        }
    )


# --- the scanner is itself tested first -------------------------------------


def test_scanner_flags_a_bare_number() -> None:
    assert untraced_numerics("x = 42\n") == ["x = 42"]


def test_scanner_accepts_a_traced_or_marked_number() -> None:
    assert untraced_numerics(f"x = 42  {TRACE_PREFIX} fixture.asset_count") == []
    assert untraced_numerics(f"x = 42  {GUESS_MARKER}") == []


def test_scanner_ignores_numbers_in_comments_and_identifiers() -> None:
    assert untraced_numerics("# we saw 3 of these\n") == []
    assert untraced_numerics("value = obj.field_2\n") == []


# --- AC-4: the emitted package ----------------------------------------------


def test_emits_rows_1_3_4_5_and_the_readme() -> None:
    record = _fully_answered()
    files = emit_package(record, emit_ontology(record))
    assert set(files) == {
        "__init__.py",
        "handlers.py",
        "data_adapter/__init__.py",
        "data_adapter/synthetic.py",
        "README.md",
    }


def test_every_emitted_python_file_parses() -> None:
    """Emitted code must be code — a template typo is a syntax error, not a review note."""
    record = _fully_answered()
    for name, content in emit_package(record, emit_ontology(record)).items():
        if name.endswith(".py"):
            ast.parse(content)


def test_action_types_is_the_ontology_enum() -> None:
    record = _fully_answered()
    doc = emit_ontology(record)
    handlers = emit_package(record, doc)["handlers.py"]
    module = ast.parse(handlers)
    action_types = next(
        node
        for node in module.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "ACTION_TYPES"
    )
    emitted = {el.value for el in action_types.value.elts}  # type: ignore[union-attr,attr-defined]
    assert emitted == set(
        doc["object_types"]["RecommendedAction"]["properties"]["action_type"]["values"]
    )


def test_registrar_names_follow_the_convention() -> None:
    """Step 5's registrar maps key on these names — a mismatch registers nothing."""
    record = _fully_answered()
    files = emit_package(record, emit_ontology(record))
    assert registrar_name("fleet_demo", "handlers") in files["handlers.py"]
    assert registrar_name("fleet_demo", "adapter") in files["data_adapter/__init__.py"]


def test_synthetic_has_no_untraced_numerics_when_fully_answered() -> None:
    """AC-4's core: every number traces to a confirmed answer."""
    record = _fully_answered()
    synthetic = emit_package(record, emit_ontology(record))["data_adapter/synthetic.py"]
    assert untraced_numerics(synthetic) == []

    # Assert on the CODE lines, not the whole file: the module docstring
    # legitimately names the GUESS marker while explaining the convention, so a
    # whole-file `GUESS_MARKER not in ...` would be checking the prose.
    value_lines = [
        line
        for line in synthetic.splitlines()
        if line.startswith(("_ASSET_COUNT", "_BAND_VALUE", "_BREACH_VALUE", "_NORMAL_VALUE"))
    ]
    assert len(value_lines) == 4
    for line in value_lines:
        assert TRACE_PREFIX in line, line
        assert GUESS_MARKER not in line, line


def test_unanswered_fixture_values_are_marked_not_invented() -> None:
    """The load-bearing half: a missing answer still emits, but visibly as a guess.

    Non-vacuity: an emitter that invented a number silently would pass the
    "no untraced numerics" test above by simply never leaving a slot empty —
    this asserts the marker is present precisely when the answer is absent.
    """
    record = _record()  # no fixture answers at all
    synthetic = emit_package(record, emit_ontology(record))["data_adapter/synthetic.py"]
    assert untraced_numerics(synthetic) == []
    assert synthetic.count(GUESS_MARKER) >= 4
    assert "fixture.asset_count unanswered" in synthetic


def test_an_operator_marked_guess_stays_marked() -> None:
    """A value the operator supplied AS a guess must not be laundered into a trace."""
    record = _record()
    record.answers.append(
        IntakeAnswer(slot_id="fixture.asset_count", value="6", guess=True),
    )
    synthetic = emit_package(record, emit_ontology(record))["data_adapter/synthetic.py"]
    assert "fixture.asset_count, operator-marked" in synthetic
    assert GUESS_MARKER in synthetic


# --- the README register ----------------------------------------------------


def test_readme_register_names_the_answered_schemaless_facts() -> None:
    """The customer's un-modellable rule must appear as a stated fact, not silence."""
    record = _record()
    record.answers.append(
        IntakeAnswer(slot_id="governance.approve.waiver.cap", value="10000"),
    )
    readme = emit_package(record, emit_ontology(record))["README.md"]
    assert "Stated but NOT enforced" in readme
    assert "governance.approve.waiver.cap" in readme
    assert "10000" in readme
    assert "No schema field exists for it" in readme


def test_readme_register_also_names_the_unanswered_schemaless_slots() -> None:
    readme = emit_package(_record(), emit_ontology(_record()))["README.md"]
    assert "governance.approve.waiver.window" in readme
    assert "governance.rule_gate.criteria.threshold" in readme


def test_readme_human_parts_are_visibly_stubbed() -> None:
    readme = emit_package(_fully_answered(), emit_ontology(_fully_answered()))["README.md"]
    assert "TODO — the customer's problem in their own words" in readme
    assert "OCT_VERTICAL=fleet_demo" in readme  # the mechanical half IS generated


# --- writing -----------------------------------------------------------------


def test_write_package_lands_only_under_the_given_root(tmp_path: Path) -> None:
    record = _fully_answered()
    written = write_package(record, emit_ontology(record), tmp_path)
    assert len(written) == 5
    for path in written:
        assert tmp_path in path.parents
    repo_root = Path(__file__).resolve().parents[4]
    assert not (repo_root / "verticals" / "fleet_demo").exists()
