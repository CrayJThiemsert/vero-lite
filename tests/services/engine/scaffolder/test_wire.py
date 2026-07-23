"""PLAN-0091 Step 5 — the wire-writer (oracles AC-6, AC-10).

Every transform is exercised against the **real shipped file content**, copied
into a scratch tree. A wire-writer tested against a hand-made fixture would pass
while failing on the files it actually has to edit — the anchors are the point.

The emitted results are then re-parsed (`ast.parse`) and, for the maps, the
entry is read back structurally rather than string-matched, so a transform that
produced syntactically valid but semantically wrong output still fails.
"""

from __future__ import annotations

import ast
import shutil
from pathlib import Path

import pytest

from services.engine.scaffolder.wire import (
    WireError,
    add_census_entry,
    add_procedure_archetype,
    add_registrar_entry,
    bump_total,
    classify_archetype,
    dispose_counted_prose,
    residual_counted_prose,
    write_wires,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
_WIRE_FILES = (
    "services/api/main.py",
    "services/engine/cli.py",
    "services/api/routers/procedures.py",
    "tests/api/test_procedures_endpoint.py",
)


def _source(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


@pytest.fixture
def staged(tmp_path: Path) -> Path:
    """A scratch root carrying real copies of the four wire targets."""
    for rel in _WIRE_FILES:
        dest = tmp_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / rel, dest)
    return tmp_path


_AT2_DOC = {
    "procedures": {
        "governed_truck_approval": {
            "steps": [
                {"facet": {"decision_condition": {"gate_kind": "in_file_band"}}},
                {"facet": {"decision_condition": {"gate_kind": "rule_gate"}}},
                {"facet": {"decision_condition": {"gate_kind": "doa_tier"}}},
            ]
        }
    }
}


# --- row 8: the label is CLASSIFIED from gate content -----------------------


def test_authority_gate_classifies_at2() -> None:
    assert classify_archetype(_AT2_DOC) == "AT-2"


def test_a_lone_band_classifies_at3() -> None:
    doc = {
        "procedures": {
            "p": {"steps": [{"facet": {"decision_condition": {"gate_kind": "in_file_band"}}}]}
        }
    }
    assert classify_archetype(doc) == "AT-3"


def test_severity_tier_is_also_an_authority_gate() -> None:
    """The 2nd AT-2 signature is NON-money (PLAN-0074) — the label must follow the
    gate class, not the currency."""
    doc = {
        "procedures": {
            "p": {"steps": [{"facet": {"decision_condition": {"gate_kind": "severity_tier"}}}]}
        }
    }
    assert classify_archetype(doc) == "AT-2"


# --- rows 7/8/9 against the REAL shipped sources ----------------------------


def test_registrar_entry_lands_in_the_api_map() -> None:
    out = add_registrar_entry(_source("services/api/main.py"), "fleet_demo", mirror=False)
    ast.parse(out)
    assert '"fleet_demo": _fleet_demo_registrar,' in out


def test_mirror_entry_lands_in_the_cli_map_with_the_lazy_tuple_shape() -> None:
    """The CLI mirror resolves lazily by name — the tuple form, not a callable."""
    out = add_registrar_entry(_source("services/engine/cli.py"), "fleet_demo", mirror=True)
    ast.parse(out)
    assert '"verticals.fleet_demo.procedures_factory"' in out
    assert '"register_fleet_demo_procedure_executors"' in out


def test_registrar_entry_refuses_a_duplicate() -> None:
    """Fail loudly: appending a second entry for a wired vertical corrupts the map."""
    with pytest.raises(WireError):
        add_registrar_entry(_source("services/engine/cli.py"), "fleet_maintenance", mirror=True)


def test_archetype_entry_is_readable_back_as_a_dict_entry() -> None:
    out = add_procedure_archetype(
        _source("services/api/routers/procedures.py"),
        "fleet_demo",
        "governed_truck_approval",
        "AT-2",
    )
    tree = ast.parse(out)
    mapping = next(
        node
        for node in tree.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "PROCEDURE_ARCHETYPES"
    )
    keys = {
        tuple(el.value for el in k.elts)  # type: ignore[attr-defined]
        for k in mapping.value.keys  # type: ignore[union-attr]
        if isinstance(k, ast.Tuple)
    }
    assert ("fleet_demo", "governed_truck_approval") in keys


def test_archetype_entry_refuses_a_duplicate() -> None:
    with pytest.raises(WireError):
        add_procedure_archetype(
            _source("services/api/routers/procedures.py"),
            "fleet_maintenance",
            "governed_repair_approval",
            "AT-2",
        )


def test_census_entry_and_total_bump_move_together() -> None:
    """Row 9: a census entry without the pin bump leaves the suite red — both or neither."""
    source = _source("tests/api/test_procedures_endpoint.py")
    before = int(
        next(line for line in source.splitlines() if "assert total ==" in line).split("==")[1]
    )
    out = bump_total(add_census_entry(source, "fleet_demo", "governed_truck_approval", "AT-2"))
    ast.parse(out)
    after = int(next(line for line in out.splitlines() if "assert total ==" in line).split("==")[1])
    assert after == before + 1
    assert '"fleet_demo": {"governed_truck_approval": "AT-2"}' in out


# --- AC-10: SD-4 counted-prose disposition ----------------------------------


def test_counted_prose_is_disposed_not_recounted() -> None:
    """SD-4: the narrative tally is REPLACED by a pointer, never incremented.

    Recounting is the failure mode the ruling exists to end — the prose had
    already gone stale on disk while the executable pin stayed honest.

    The assertion is per-SHAPE rather than the old ``replaced >= 1``. That threshold
    was satisfied by the per-member tallies alone, so it stayed green while the
    collection counts in this very file went untouched — an oracle that cannot fail
    for the thing it is supposed to check.
    """
    source = _source("tests/api/test_procedures_endpoint.py")
    out, replaced = dispose_counted_prose(source)
    assert replaced >= 1, "the stale narrative tally was not found"
    assert "ships two" not in out
    assert "ships its own procedures" in out
    # the collection count in the same file ("across six verticals")
    assert "six verticals" not in out
    assert "across verticals" in out
    ast.parse(out)


def test_the_fourth_site_in_main_py_is_disposed() -> None:
    """AC-10's fourth site, and the reason it was reported as untouched.

    ``services/api/main.py``'s registrar docstring says "All six PROCEDURE-SHIPPING
    verticals register a factory". The per-member pattern scores **zero** on it, so
    adding main.py to the wire-writer's targets without the collection shape would
    have been a no-op that looked like a fix.
    """
    source = _source("services/api/main.py")
    assert "All six PROCEDURE-SHIPPING verticals" in source, "the counted site moved"
    out, replaced = dispose_counted_prose(source)
    assert replaced >= 1
    assert "All PROCEDURE-SHIPPING verticals register a factory" in out
    assert "six PROCEDURE-SHIPPING" not in out
    ast.parse(out)


def test_the_wire_writer_actually_applies_it_to_main_py(staged: Path) -> None:
    """Disposing in the FUNCTION is not the AC — the AC is that the wire-writer runs it
    on the file it touches. The two were separate for a whole PLAN."""
    write_wires("fleet_demo", "governed_truck_approval", _AT2_DOC, staged)
    out = (staged / "services" / "api" / "main.py").read_text(encoding="utf-8")
    assert "All PROCEDURE-SHIPPING verticals register a factory" in out
    assert "six PROCEDURE-SHIPPING" not in out


def test_irregular_counted_prose_is_reported_not_rewritten() -> None:
    """The census comment carries four interlocking counts in one free-form narrative,
    each encoding which PLAN contributed which procedure.

    A regex that rewrote it would mangle the grammar or delete the provenance, so the
    tool reports it instead — the same stance it takes at a governance tripwire:
    detect, hand a human the specifics, never clear it yourself. This asserts the
    residue is SURFACED, which is the difference between a known gap and a silent one.
    """
    out, _ = dispose_counted_prose(_source("tests/api/test_procedures_endpoint.py"))
    residual = residual_counted_prose(out)
    assert residual, "the irregular census narrative was neither disposed nor reported"
    assert any("procedures" in item for item in residual)


def test_disposition_is_idempotent() -> None:
    """Running the wire-writer twice must not degrade the prose further."""
    once, first = dispose_counted_prose(_source("tests/api/test_procedures_endpoint.py"))
    twice, second = dispose_counted_prose(once)
    assert second == 0
    assert twice == once


def test_the_executable_pin_survives_disposition() -> None:
    """SD-4 keeps the count that CANNOT go silently stale."""
    out, _ = dispose_counted_prose(_source("tests/api/test_procedures_endpoint.py"))
    assert "assert total ==" in out


# --- the whole write, under an explicit root --------------------------------


def test_write_wires_edits_only_the_staged_root(staged: Path) -> None:
    """AC-6 end to end — and the repo tree is never touched.

    The wire-writer code-mods files that also exist in this checkout, so an
    emitter that inherited the CWD would edit the running repo. This asserts the
    staged copies changed and the real ones did not.
    """
    originals = {rel: _source(rel) for rel in _WIRE_FILES}

    written = write_wires("fleet_demo", "governed_truck_approval", _AT2_DOC, staged)
    assert set(written) == set(_WIRE_FILES)

    for rel in _WIRE_FILES:
        staged_text = (staged / rel).read_text(encoding="utf-8")
        assert staged_text != originals[rel], f"{rel} was not wired"
        ast.parse(staged_text)
        assert _source(rel) == originals[rel], f"{rel} in the REPO was modified"


def test_write_wires_refuses_a_missing_target(tmp_path: Path) -> None:
    """A partial stage must fail loudly, not wire three of four points."""
    with pytest.raises(WireError):
        write_wires("fleet_demo", "governed_truck_approval", _AT2_DOC, tmp_path)
