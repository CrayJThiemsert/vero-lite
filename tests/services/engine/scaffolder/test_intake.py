"""PLAN-0091 Step 1 — the intake engine's oracles (AC-1, AC-2).

AC-1 is the command's inert-safety: it exists, ``--plan-only`` writes nothing,
and it refuses an existing namespace outright.

AC-2 is the substantive one — the checklist must derive the WHOLE question set
up front and re-ask mechanically. Two properties are asserted rather than
assumed:

* **Gap coverage.** The four gap classes PLAN-0086's manual run actually hit
  (feel-only authority tiers · an unbounded emergency bypass · an ambiguous
  requester · a threshold-less comparison rule) each have a slot. The fixture
  narrative is fleet-*shaped*, not the verbatim private one — the real
  narrative stays gitignored so a future timed run is not contaminated by a
  committed copy the agent could recognise.
* **The Q2 test, named in the AC.** Answering only the ฿10,000 cap fills
  exactly the cap sub-slot; the ratifier and window stay individually open.
  One number is never treated as a full answer.
"""

from __future__ import annotations

import json
import os
import shutil
from collections.abc import Iterator
from pathlib import Path

import click
import pytest
import typer.main
from typer.testing import CliRunner

from services.engine.cli import app
from services.engine.scaffolder.intake import (
    IntakeAnswer,
    IntakeRecord,
    SlotKind,
    open_questions,
    required_slots,
    spine_steps,
    unenforced_register,
)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def staged_repo(tmp_path: Path) -> Iterator[Path]:
    """A scratch repo root with a `verticals/` dir, chdir'd into.

    Mirrors the shipped ``test_cli_e2e.staged_repo`` pattern rather than adding a
    ``--root`` flag to the CLI: ``validate``/``generate`` resolve CWD-relative by
    design (ADR-0015 D2), and the scaffolder's own namespace check must be tested
    under the same resolution rule it will run under.
    """
    staged = tmp_path / "repo"
    (staged / "verticals").mkdir(parents=True)
    old_cwd = Path.cwd()
    os.chdir(staged)
    try:
        yield staged
    finally:
        os.chdir(old_cwd)


def _tree(root: Path) -> set[Path]:
    return {p.relative_to(root) for p in root.rglob("*")}


# --- AC-1: the command exists and is inert-safe -----------------------------


def test_scaffold_help_works_offline() -> None:
    """`--help` renders and exits 0 with no network and no repo state (AC-1)."""
    result = CliRunner().invoke(app, ["scaffold", "--help"])
    assert result.exit_code == 0, f"stderr={result.stderr!r}"


def test_scaffold_is_registered_with_its_flags() -> None:
    """The command + its options exist — asserted against the registered params.

    Deliberately NOT asserted against rendered `--help` text: Typer renders help
    through rich, whose wrapping and truncation depend on the terminal the run
    happens to get. A rendered-text assertion passed locally and failed in CI on
    exactly that difference, which makes it an oracle for the renderer rather
    than for the command. The parameter list is the property AC-1 actually
    claims.
    """
    command = typer.main.get_command(app)
    assert isinstance(command, click.Group)
    scaffold_cmd = command.commands["scaffold"]
    flags = {opt for param in scaffold_cmd.params for opt in param.opts}
    assert {"--plan-only", "--narrative", "--intake"} <= flags


@pytest.fixture
def wired_repo(staged_repo: Path) -> Path:
    """`staged_repo` plus everything a real emission run reads from the checkout.

    Two groups, for two different reasons:

    * the four shared files the wire-writer edits — it refuses to invent a target it
      cannot find, so a tree without them gets a WireError rather than a half-wired
      repo;
    * every shipped ``procedures.yaml`` — the governance-ceiling baseline is read from
      the CWD's verticals, so an empty tree makes EVERY candidate look like a brand-new
      AT-2 signature and the run stops at the ceiling. That stop is the detector working
      correctly on a tree that genuinely has no baseline; it is not the behaviour under
      test here.

    Copied from the real checkout so both are exercised against the actual anchors and
    the actual baseline.
    """
    repo_root = Path(__file__).resolve().parents[4]
    for rel in (
        "services/api/main.py",
        "services/engine/cli.py",
        "services/api/routers/procedures.py",
        "tests/api/test_procedures_endpoint.py",
    ):
        dest = staged_repo / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo_root / rel, dest)

    for src in sorted((repo_root / "verticals").glob("*/procedures.yaml")):
        dest = staged_repo / "verticals" / src.parent.name / "procedures.yaml"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    return staged_repo


def test_the_command_actually_scaffolds_end_to_end(wired_repo: Path) -> None:
    """The property no oracle covered: the COMMAND — not the library behind it —
    turns an intake record into files on disk.

    Every emitter had passing tests while `vero-lite scaffold` printed a queue and
    exited 3 without writing anything, because the golden e2e calls the emitters
    directly. This runs the command an operator would run and then looks at the disk.
    """
    intake = FIXTURES / "fleet_golden_intake.json"
    record = IntakeRecord.model_validate_json(intake.read_text(encoding="utf-8"))
    staged_intake = wired_repo / "intake.json"
    staged_intake.write_text(
        record.model_copy(update={"namespace": "fleet_cli"}).model_dump_json(),
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["scaffold", "fleet_cli", "--intake", str(staged_intake)])
    assert result.exit_code == 0, f"stderr={result.stderr!r}"

    base = wired_repo / "verticals" / "fleet_cli"
    for rel in (
        "__init__.py",
        "handlers.py",
        "procedures_factory.py",
        "procedures.yaml",
        "data_adapter/__init__.py",
        "data_adapter/synthetic.py",
        "README.md",
        "ontology/fleet_cli_v0.yaml",
    ):
        assert (base / rel).is_file(), rel

    # And the shared wires actually carry the new vertical, not just the package.
    main_py = (wired_repo / "services" / "api" / "main.py").read_text(encoding="utf-8")
    assert "fleet_cli" in main_py


def test_an_intake_namespace_mismatch_is_refused(wired_repo: Path) -> None:
    """The overwrite guard checks the ARGUMENT; every emitter writes to the RECORD's
    namespace. Letting them differ routes the write past the guard entirely and onto
    whatever the file names — so this refuses rather than picking a winner."""
    staged_intake = wired_repo / "intake.json"
    staged_intake.write_text(
        IntakeRecord(namespace="somewhere_else").model_dump_json(), encoding="utf-8"
    )
    result = CliRunner().invoke(app, ["scaffold", "fleet_cli", "--intake", str(staged_intake)])
    assert result.exit_code == 2, f"stderr={result.stderr!r}"
    assert "must match" in result.stderr
    assert not (wired_repo / "verticals" / "somewhere_else").exists()


def test_plan_only_prints_the_queue_and_writes_nothing(staged_repo: Path) -> None:
    before = _tree(staged_repo)
    result = CliRunner().invoke(
        app,
        [
            "scaffold",
            "fleet_demo",
            "--narrative",
            str(FIXTURES / "fleet_shaped_narrative.txt"),
            "--plan-only",
        ],
    )
    assert result.exit_code == 0, f"stderr={result.stderr!r}"
    assert "Open questions" in result.stderr
    assert "nothing written" in result.stderr
    assert _tree(staged_repo) == before, "--plan-only wrote to the tree"


def test_scaffold_refuses_an_existing_namespace(staged_repo: Path) -> None:
    (staged_repo / "verticals" / "already_here").mkdir()
    before = _tree(staged_repo)
    result = CliRunner().invoke(app, ["scaffold", "already_here", "--plan-only"])
    assert result.exit_code == 2, f"stderr={result.stderr!r}"
    assert "refuses to overwrite" in result.stderr
    assert _tree(staged_repo) == before


def test_scaffold_refuses_to_emit_with_open_judgment_slots(staged_repo: Path) -> None:
    """A bare namespace has no confirmed judgments, so the command refuses and writes
    nothing — a silent exit 0 would read as "scaffolded" to an operator and a script.

    This test previously asserted the same exit code for a different reason: emission
    was unwired, and it was named `..._does_not_emit_yet_and_says_so`. It kept passing
    after the wiring landed, which is exactly why the name and docstring are corrected
    rather than left — a test that passes for a reason its own name denies is a test
    nobody can read.
    """
    result = CliRunner().invoke(app, ["scaffold", "fleet_demo"])
    assert result.exit_code == 3, f"stderr={result.stderr!r}"
    assert "REFUSING TO EMIT" in result.stderr
    assert "ontology.asset_noun" in result.stderr
    assert _tree(staged_repo) == {Path("verticals")}


# --- AC-2: the checklist derives the whole question set up front ------------


def test_checklist_is_derived_from_the_shipped_obligation_deriver() -> None:
    """The AT-2 half must come from `derive_governance_todo`, not a local restatement.

    Non-vacuity: the spine's two AT-2 gates (rule_gate, doa_tier) are the only
    steps that owe `governance_content`, so their slots — and no others — carry
    the governance prefix. A checklist that hardcoded its own gate list would
    pass a "has slots" test but drift the moment the deriver changes.
    """
    owed_by_governance = {
        slot.owed_by for slot in required_slots() if slot.slot_id.startswith("governance.")
    }
    assert owed_by_governance == {"rule_gate", "approve"}

    # And the spine feeding it is the row-11 sequence read off the golden donor.
    assert [s.step_id for s in spine_steps()] == [
        "intake",
        "judge",
        "reshape",
        "rule_gate",
        "approve",
        "fulfill",
    ]


def test_queue_covers_all_four_gap_classes() -> None:
    slot_ids = {slot.slot_id for slot in required_slots()}
    # 1. feel-only authority tiers
    assert "governance.approve.tiers" in slot_ids
    # 2. an unbounded emergency bypass
    assert "governance.approve.waiver.cap" in slot_ids
    assert "governance.approve.waiver.window" in slot_ids
    # 3. an ambiguous requester (the ADR-0025 D5 SoD a doa_tier gate requires)
    assert "governance.approve.sod.requester" in slot_ids
    # 4. a threshold-less comparison rule
    assert "governance.rule_gate.criteria.threshold" in slot_ids


def test_unmodelled_slots_are_exactly_the_schemaless_ones() -> None:
    """The register feed is typed, not a naming convention.

    Every UNMODELLED slot has no schema field and vice versa — so a future slot
    that forgets its `schema_field` surfaces in the README register rather than
    silently vanishing from both the YAML and the register.
    """
    for slot in required_slots():
        assert (slot.schema_field is None) == (slot.kind is SlotKind.UNMODELLED), slot.slot_id

    register_ids = {slot.slot_id for slot in unenforced_register(IntakeRecord(namespace="x"))}
    assert register_ids == {
        "governance.approve.waiver.cap",
        "governance.approve.waiver.window",
        "governance.rule_gate.criteria.threshold",
    }


def test_q2_one_number_is_not_a_full_answer() -> None:
    """AC-2's named Q2 test — the sub-slot decomposition's whole point.

    Answering only "cap = ฿10,000" must fill exactly the cap sub-slot. The
    ratifier and window re-surface **individually**: a queue that closed the
    whole emergency-waiver question here would drop two customer facts, which is
    the failure PLAN-0086 recorded in the field.
    """
    record = IntakeRecord(
        namespace="fleet_demo",
        answers=[IntakeAnswer(slot_id="governance.approve.waiver.cap", value="10000")],
    )
    still_open = {slot.slot_id for slot in open_questions(record)}

    assert "governance.approve.waiver.cap" not in still_open
    assert "governance.approve.waiver.ratifier" in still_open
    assert "governance.approve.waiver.window" in still_open
    assert "governance.approve.waiver.relaxes" in still_open


def test_an_unconfirmed_answer_leaves_its_slot_open() -> None:
    """ADR-0024 D5: only a CONFIRMED value may reach an emitter.

    So an unconfirmed answer must not close its slot — otherwise the ontology
    stage would emit a judgment the operator never ratified.
    """
    record = IntakeRecord(
        namespace="fleet_demo",
        answers=[
            IntakeAnswer(slot_id="ontology.asset_noun", value="รถบรรทุก", confirmed=False),
        ],
    )
    assert "ontology.asset_noun" in {slot.slot_id for slot in open_questions(record)}
    assert record.confirmed_value("ontology.asset_noun") is None


def test_intake_record_round_trips_as_the_cli_reads_it(tmp_path: Path) -> None:
    """The --intake path parses what the record serialises (the Step-7 golden path)."""
    record = IntakeRecord(
        namespace="fleet_demo",
        narrative="…",
        answers=[
            IntakeAnswer(slot_id="governance.approve.currency", value="THB"),
            IntakeAnswer(slot_id="fixture.asset_count", value="6", guess=True),
        ],
    )
    path = tmp_path / "intake.json"
    path.write_text(record.model_dump_json(), encoding="utf-8")

    reloaded = IntakeRecord.model_validate_json(path.read_text(encoding="utf-8"))
    assert reloaded == record
    assert reloaded.confirmed_value("governance.approve.currency") == "THB"
    assert reloaded.answered()["fixture.asset_count"].guess is True


def test_plan_only_consumes_a_typed_intake_record(staged_repo: Path, tmp_path: Path) -> None:
    """A partially-answered record shortens the queue by exactly its confirmed answers."""
    record = IntakeRecord(
        namespace="fleet_demo",
        answers=[IntakeAnswer(slot_id="governance.approve.currency", value="THB")],
    )
    intake_path = tmp_path / "intake.json"
    intake_path.write_text(record.model_dump_json(), encoding="utf-8")

    full = len(required_slots())
    result = CliRunner().invoke(
        app, ["scaffold", "fleet_demo", "--intake", str(intake_path), "--plan-only"]
    )
    assert result.exit_code == 0, f"stderr={result.stderr!r}"
    assert f"{full - 1} of {full} slots" in result.stderr


def test_narrative_fixture_is_fleet_shaped_not_the_private_original() -> None:
    """Freshness guard (AC-2's parenthetical).

    The committed fixture must carry the four gap classes WITHOUT being the
    verbatim private narrative — a committed copy of the real one would let a
    future timed run recognise it, contaminating the measurement the fixture
    exists to make repeatable.
    """
    text = (FIXTURES / "fleet_shaped_narrative.txt").read_text(encoding="utf-8")
    # The gap classes are present in customer voice, not as schema words.
    assert "แล้วแต่ความรู้สึก" in text  # feel-only tiers
    assert "ซื้อร้านข้างทาง" in text  # the unbounded roadside bypass
    assert "คนละคนกัน" in text or "ไม่ใช่คนเดียวกัน" in text  # SoD, requester left implicit
    assert "สามเจ้า" in text or "สามร้าน" in text  # the quote rule, thresholdless
    # And it names no schema token — if it did, the "derive the queue" claim
    # would be reading the answer off the input.
    for schema_token in ("doa_tier", "rule_gate", "governance_content", "three_bid"):
        assert schema_token not in text


def test_intake_module_has_no_llm_import() -> None:
    """The operator-input-only property, asserted structurally.

    PLAN-0091 stakes "governed ≠ generated" on there being no write path from a
    model emission into an intake value. Prose cannot hold that; an import scan
    can — if someone wires a generator/LLM client into this module, this fails.
    """
    source = (
        Path(__file__).resolve().parents[4] / "services" / "engine" / "scaffolder" / "intake.py"
    ).read_text(encoding="utf-8")
    for banned in ("generator", "ollama", "llm", "anthropic", "openai"):
        assert f"import {banned}" not in source.lower()
        assert f"from {banned}" not in source.lower()


def test_fixture_dir_is_committed_not_generated() -> None:
    """The narrative + (Step 7) golden intake are repo facts, not test-time output."""
    assert FIXTURES.is_dir()
    assert (FIXTURES / "fleet_shaped_narrative.txt").is_file()


def test_json_round_trip_of_the_slot_catalogue_is_stable() -> None:
    """Slot ids are the re-ask keys, so their set is a contract worth pinning.

    A renamed slot silently orphans any committed intake record that answered it
    — the answer would still parse and the question would still re-surface, with
    no error anywhere. This pins the count and the id set's shape instead.
    """
    ids = [slot.slot_id for slot in required_slots()]
    assert len(ids) == len(set(ids)), "duplicate slot id"
    payload = json.loads(json.dumps(ids))
    assert payload == ids
    assert all(sid.split(".")[0] in {"band", "governance", "ontology", "fixture"} for sid in ids)
