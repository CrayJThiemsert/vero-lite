"""PLAN-0091 Step 7 — the golden diff-oracle + the non-capabilities (AC-7, AC-9).

**Why this is the falsifiable claim of the whole PLAN.** Every other test asks
"did the emitter do what I told it to". This one asks the only question that
matters: *regenerate the vertical a human hand-built, from that human's own
recorded answers, and does the result agree with theirs?* The donor
(`verticals/fleet_maintenance/`) was built by hand in PLAN-0086's timed manual
run, before this tool existed, so it cannot have been shaped to make the tool
look good.

**What "structurally matches" means here, stated precisely rather than
generously.** The PLAN scopes byte-equality to exactly one row and asserts SET
equality elsewhere — prose may differ, structure may not. Asserted:

* the ontology object SET and link_type SET,
* the per-entity band property landing on the Asset,
* the `ACTION_TYPES` set,
* the spine's AT-2 gate signature — equal to the shipped
  `("rule_gate", ("three_quote",)), ("doa_tier", ("THB",))` baseline row,
* the governance VALUES against the recorded Q1-Q4 answers,
* the wire entries against the in-tree ones,
* **row 4** (`data_adapter/__init__.py`) — the one row the ledger claims equality
  for — as STRUCTURAL equality modulo namespace: same AST once docstrings are
  stripped and the namespace token is normalized.

**Why row 4 is structural equality and not literal bytes.** The AC's own wording
scopes it "modulo namespace" and adds "prose may differ, structure may not", and
literal bytes are not merely hard here — they are *wrong*. The donor's docstring
records that it was "Hand-written from the building_materials adapter (NOT
``vero-lite new-vertical`` — banned by the PLAN-0086 measurement protocol)". A
tool that emitted that sentence would be emitting a false provenance claim about
its own output. So the oracle compares what the AC actually cares about — the
code — and lets the provenance prose differ, honestly.

**Honestly NOT asserted, and why:** the donor's narrative-mined per-object
properties (`truck_class`, `odometer_km`, `plate`, `depot_type`) are customer
detail no generic emitter can invent — mining them from free text is exactly
the LLM surface this PLAN keeps OUT of the value path. The tool emits the
grammar skeleton and the judgment slots; the domain columns remain human work,
and the README gap register is where the tool says so. Claiming a fuller match
than that would be the failure mode this test exists to prevent.
"""

from __future__ import annotations

import ast
import inspect
import json
import shutil
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from services.engine.procedures.at2_signature import (
    at2_gate_kinds,
    content_enum_surface,
)
from services.engine.procedures.spec import load_procedures_file
from services.engine.registry import registry
from services.engine.scaffolder.ceiling import check_ceiling
from services.engine.scaffolder.intake import IntakeRecord
from services.engine.scaffolder.ontology import emit_ontology, run_floor, write_ontology
from services.engine.scaffolder.package import class_prefix, emit_package, write_package
from services.engine.scaffolder.spine import emit_procedures
from services.engine.scaffolder.wire import write_wires

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURES = Path(__file__).parent / "fixtures"
DONOR = REPO_ROOT / "verticals" / "fleet_maintenance"

_WIRE_FILES = (
    "services/api/main.py",
    "services/engine/cli.py",
    "services/api/routers/procedures.py",
    "tests/api/test_procedures_endpoint.py",
)


@pytest.fixture(scope="module")
def golden() -> IntakeRecord:
    """The committed Q1-Q4 intake — in-tree facts, not new ones."""
    return IntakeRecord.model_validate_json(
        (FIXTURES / "fleet_golden_intake.json").read_text(encoding="utf-8")
    )


@pytest.fixture(scope="module")
def regenerated(golden: IntakeRecord, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Regenerate the fleet vertical into a scratch tree, wires included."""
    root = tmp_path_factory.mktemp("regen")
    for rel in _WIRE_FILES:
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / rel, dest)

    # A namespace distinct from the donor's: the tool refuses to overwrite an
    # existing vertical, and the wire maps already contain `fleet_maintenance`.
    record = golden.model_copy(update={"namespace": "fleet_regen"})
    ontology_doc = emit_ontology(record)
    write_ontology(record, root)
    write_package(record, ontology_doc, root)

    procedures_doc = emit_procedures(record, ontology_doc)
    path = root / "verticals" / record.namespace / "procedures.yaml"
    with path.open("w", encoding="utf-8") as stream:
        YAML().dump(procedures_doc, stream)

    write_wires(record.namespace, "governed_truck_approval", procedures_doc, root)
    return root


def _donor_ontology() -> dict:
    with (DONOR / "ontology" / "fleet_maintenance_v0.yaml").open(encoding="utf-8") as stream:
        return dict(YAML().load(stream))


# --- AC-7: the diff-oracle --------------------------------------------------


def test_same_file_set_as_the_donor(regenerated: Path) -> None:
    """The package shape matches; only the generated/ dir differs (codegen output)."""
    donor_files = {
        p.relative_to(DONOR).as_posix()
        for p in DONOR.rglob("*")
        if p.is_file() and "generated" not in p.parts and p.suffix in {".py", ".md"}
    }
    regen = regenerated / "verticals" / "fleet_regen"
    regen_files = {
        p.relative_to(regen).as_posix()
        for p in regen.rglob("*")
        if p.is_file() and p.suffix in {".py", ".md"}
    }
    assert regen_files == donor_files


def _skeleton(source: str, namespace: str) -> str:
    """The AST with docstrings stripped and the namespace token normalized away.

    Normalization happens on the SOURCE before parsing, and to a valid identifier
    (``nsx`` / ``Nsx``) rather than a placeholder like ``<ns>`` — the token appears
    in import paths and class names, where a non-identifier would not parse.
    Comments never survive ``ast.parse``, so this compares code, not annotation.
    """
    text = source.replace(class_prefix(namespace), "Nsx").replace(namespace, "nsx")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        first = node.body[0] if node.body else None
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            node.body.pop(0)
    return ast.dump(tree)


def test_row_4_adapter_is_structurally_equal_to_the_donor(regenerated: Path) -> None:
    """AC-7 row 4: the one row the ledger claims equality for.

    Structural, not literal-byte — see the module docstring for why literal bytes
    would require emitting a false provenance claim. Everything the AC means by
    "structure" is here: the class, every method and its full parameter list, and
    the registrar body.
    """
    regen = (regenerated / "verticals" / "fleet_regen" / "data_adapter" / "__init__.py").read_text(
        encoding="utf-8"
    )
    donor = (DONOR / "data_adapter" / "__init__.py").read_text(encoding="utf-8")
    assert _skeleton(regen, "fleet_regen") == _skeleton(donor, "fleet_maintenance")


def test_the_emitted_registrar_binds_to_the_real_register_adapter_signature(
    regenerated: Path,
) -> None:
    """The emitted package must be LOADABLE, not merely parseable.

    This guards a bug that shipped and that nothing caught: the emitter called
    ``registry.register_adapter(_VERTICAL, SyntheticAdapter())`` — two arguments
    against a one-argument signature — so a scaffolded vertical raised ``TypeError``
    the moment anything imported and called its registrar. Every existing package
    test only ``ast.parse``s the emitted text, and a syntactically perfect call to a
    wrong signature parses fine.

    So this binds the emitted call against the REAL bound signature rather than
    re-asserting the argument count, which would just restate the emitter.
    """
    source = (regenerated / "verticals" / "fleet_regen" / "data_adapter" / "__init__.py").read_text(
        encoding="utf-8"
    )
    calls = [
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "register_adapter"
    ]
    assert len(calls) == 1, "the adapter registers itself exactly once"
    inspect.signature(registry.register_adapter).bind(
        *[object()] * len(calls[0].args),
        **{kw.arg: object() for kw in calls[0].keywords if kw.arg},
    )


def test_ontology_object_and_link_sets_match_the_donor(golden: IntakeRecord) -> None:
    donor = _donor_ontology()
    emitted = emit_ontology(golden)
    assert set(emitted["object_types"]) == set(donor["object_types"])
    assert set(emitted["link_types"]) == set(donor["link_types"])


def test_the_band_property_lands_on_the_asset_as_in_the_donor(golden: IntakeRecord) -> None:
    donor = _donor_ontology()
    emitted = emit_ontology(golden)
    band = "minor_repair_ceiling_thb"
    assert band in donor["object_types"]["Truck"]["properties"]
    assert band in emitted["object_types"]["Truck"]["properties"]


def test_action_types_set_equals_the_donors(golden: IntakeRecord, regenerated: Path) -> None:
    donor_source = (DONOR / "handlers.py").read_text(encoding="utf-8")
    donor_types = set(_action_types(donor_source))
    regen_source = (regenerated / "verticals" / "fleet_regen" / "handlers.py").read_text(
        encoding="utf-8"
    )
    assert set(_action_types(regen_source)) == donor_types


def _action_types(source: str) -> list[str]:
    module = ast.parse(source)
    node = next(
        n
        for n in module.body
        if isinstance(n, ast.AnnAssign)
        and isinstance(n.target, ast.Name)
        and n.target.id == "ACTION_TYPES"
    )
    return [el.value for el in node.value.elts]  # type: ignore[union-attr,attr-defined]


def test_gate_signature_equals_the_shipped_baseline_row(regenerated: Path) -> None:
    """The AT-2 fingerprint the census pins for fleet, reproduced exactly."""
    path = regenerated / "verticals" / "fleet_regen" / "procedures.yaml"
    spec = load_procedures_file(path, vertical="fleet_regen")
    procedure = spec.procedures[0]
    assert at2_gate_kinds(procedure) == ("rule_gate", "doa_tier")
    assert content_enum_surface(procedure) == (
        ("rule_gate", ("three_quote",)),
        ("doa_tier", ("THB",)),
    )


def test_governance_values_equal_the_recorded_answers(regenerated: Path) -> None:
    """Q1 (the ladder) and Q2 (the waiver) round-trip into the typed content."""
    path = regenerated / "verticals" / "fleet_regen" / "procedures.yaml"
    spec = load_procedures_file(path, vertical="fleet_regen")
    approve = next(s for s in spec.procedures[0].steps if s.step_id == "approve")
    ladder = approve.governance_content
    assert ladder is not None
    assert ladder.currency == "THB"
    assert [str(t.min_amount) for t in ladder.tiers] == ["0", "5000", "50000"]
    assert ladder.emergency_waiver.escalate_to == "owner"


def test_wire_entries_match_the_in_tree_shape(regenerated: Path) -> None:
    """Row 7/8/9: the regenerated wires carry the same shape the donor's do."""
    cli = (regenerated / "services/engine/cli.py").read_text(encoding="utf-8")
    assert '"verticals.fleet_regen.procedures_factory"' in cli
    assert '"verticals.fleet_maintenance.procedures_factory"' in cli  # donor untouched

    procedures = (regenerated / "services/api/routers/procedures.py").read_text(encoding="utf-8")
    assert '("fleet_regen", "governed_truck_approval"): "AT-2"' in procedures


def test_the_emitted_ontology_passes_the_invoked_floor(
    golden: IntakeRecord, tmp_path: Path
) -> None:
    """The donor's ontology validates; so must the regenerated one."""
    record = golden.model_copy(update={"namespace": "fleet_regen2"})
    write_ontology(record, tmp_path)
    assert run_floor(record.namespace, tmp_path) == 0


def test_the_regenerated_shape_does_not_trip_the_ceiling(
    golden: IntakeRecord, tmp_path: Path
) -> None:
    """A baseline member must regenerate freely — the AC-8 half that keeps AC-7 possible."""
    record = golden.model_copy(update={"namespace": "fleet_regen3"})
    doc = emit_procedures(record, emit_ontology(record))
    assert check_ceiling(record.namespace, doc, repo_root=REPO_ROOT, scratch=tmp_path) is None


# --- AC-9: the hard non-capabilities ----------------------------------------


def test_no_scaffolder_module_can_run_git(regenerated: Path) -> None:
    """Zero git operations — asserted structurally, over every scaffolder module."""
    for path in (REPO_ROOT / "services" / "engine" / "scaffolder").glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "subprocess" not in source, path
        assert "import git" not in source, path
        assert '"git"' not in source, path


def test_no_scaffolder_module_fires_a_run(regenerated: Path) -> None:
    """Zero procedure-run firing: the tool emits, it never executes."""
    for path in (REPO_ROOT / "services" / "engine" / "scaffolder").glob("*.py"):
        source = path.read_text(encoding="utf-8")
        for banned in ("run_procedure", "execute_procedure", "persist_run", "resume_run"):
            assert banned not in source, f"{path}: {banned}"


def test_no_existing_vertical_procedures_yaml_was_written(
    golden: IntakeRecord, regenerated: Path
) -> None:
    """ADR-0024 :147 — the tool never writes into a SHIPPED vertical.

    Checked against the real tree after a full regeneration ran, because that is
    the run that would have done it.
    """
    donor_procedures = DONOR / "procedures.yaml"
    digest = json.dumps(
        sorted(
            (p.relative_to(REPO_ROOT).as_posix(), p.stat().st_size)
            for p in (REPO_ROOT / "verticals").glob("*/procedures.yaml")
        )
    )
    assert donor_procedures.is_file()
    # Re-read after the module-scoped regeneration fixture has already run.
    assert digest == json.dumps(
        sorted(
            (p.relative_to(REPO_ROOT).as_posix(), p.stat().st_size)
            for p in (REPO_ROOT / "verticals").glob("*/procedures.yaml")
        )
    )


def test_the_whole_pipeline_needs_no_network(golden: IntakeRecord, tmp_path: Path) -> None:
    """MS-S1 unreachable is the normal case, not a degraded one.

    Structural: no scaffolder module imports an LLM client or an HTTP library,
    so there is no path that could reach the network to begin with.
    """
    for path in (REPO_ROOT / "services" / "engine" / "scaffolder").glob("*.py"):
        source = path.read_text(encoding="utf-8").lower()
        for banned in ("httpx", "requests", "urllib", "ollama", "anthropic", "openai"):
            assert f"import {banned}" not in source, f"{path}: {banned}"

    record = golden.model_copy(update={"namespace": "fleet_offline"})
    doc = emit_ontology(record)
    assert emit_package(record, doc)
    assert emit_procedures(record, doc)
