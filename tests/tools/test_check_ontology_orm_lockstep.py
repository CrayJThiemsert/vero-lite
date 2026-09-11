"""The ontology↔ORM lockstep guard (PLAN-0109 AC-3, AC-4, AC-10).

Every broken case below is a tree built to carry exactly ONE violation, and each
asserts two things: the guard exits 1, and it NAMES the offender with its kind. A guard
that reddens without saying what broke is deleted by the next person who trips it
(Lesson #0043), so the name is part of the contract, not decoration.

The lockstep tree is the positive control for all of them: the same builder, with no
violation, exits 0 — so each red is about its violation, not about the fixture. It also
carries a ``ref`` and an ``enum`` on ``Text`` columns, which is what AC-1 requires of
the real ontology and what a ``Text→string``-only type map would have refused.

Finally the guard runs against the real tree, the way the pre-commit hook does, and its
printed counts are pinned: a guard green only on fixtures proves nothing about the tree
it protects. AC-4's two scratch additions are also asserted BY NAME on the real inputs,
in memory, because the probe driver that makes those edits to the tracked files keeps
only the outcome of each run, not the text that named the offender.
"""

from __future__ import annotations

import copy
import os
import subprocess
import sys
from pathlib import Path

import pytest
import sqlalchemy as sa

from tools.check_ontology_orm_lockstep import compare, load_inputs, main

_REPO_ROOT = Path(__file__).resolve().parents[2]

_YAML_TEMPLATE = """version: 0
namespace: fleet_maintenance
object_types:
  Owner:
    primary_key: owner_id
    properties:
      owner_id: {{type: string, required: true}}
{widget}"""

_WIDGET_BLOCK = """  Widget:
    primary_key: widget_id
    properties:
      widget_id: {{type: string, required: true}}
      owner_id: {{type: ref, target: Owner}}
      status: {{type: enum, values: [a, b]}}
      amount: {{type: {amount_type}}}
      seen_at: {{type: timestamp}}
{extra_properties}"""

_PROJECTION_TEMPLATE = """import sqlalchemy as sa

_META = sa.MetaData()
WIDGET = sa.Table(
    "widget",
    _META,
    sa.Column("widget_id", sa.Text, primary_key=True),
    sa.Column("owner_id", sa.Text),
    sa.Column("status", sa.Text),
    sa.Column("amount", sa.Numeric(14, 2)),
    sa.Column("seen_at", sa.DateTime(timezone=True)),
    sa.Column("secret", sa.Text),
    sa.Column("tenant_id", sa.Text),
{extra_columns})
DB_BACKED_TYPES = {{"Widget": WIDGET}}
EXCLUDED_COLUMNS = {{
{secret_exclusion}    ("Widget", "tenant_id"): "tenancy-key",
{extra_exclusions}}}
"""


def _tree(
    root: Path,
    *,
    declare_widget: bool = True,
    amount_type: str = "float",
    extra_properties: str = "",
    extra_columns: str = "",
    extra_exclusions: str = "",
    exclude_secret: bool = True,
) -> Path:
    """A repo-shaped tree holding the two inputs the guard reads, and nothing else."""
    widget = (
        _WIDGET_BLOCK.format(amount_type=amount_type, extra_properties=extra_properties)
        if declare_widget
        else ""
    )
    ontology = root / "verticals" / "fleet_maintenance" / "ontology" / "fleet_maintenance_v0.yaml"
    ontology.parent.mkdir(parents=True)
    ontology.write_text(_YAML_TEMPLATE.format(widget=widget), encoding="utf-8")

    projection = root / "verticals" / "fleet_maintenance" / "data_adapter" / "db_projection.py"
    projection.parent.mkdir(parents=True)
    projection.write_text(
        _PROJECTION_TEMPLATE.format(
            extra_columns=extra_columns,
            secret_exclusion='    ("Widget", "secret"): "ruled-out",\n' if exclude_secret else "",
            extra_exclusions=extra_exclusions,
        ),
        encoding="utf-8",
    )
    return root


def _run(root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):  # type: ignore[no-untyped-def]
    monkeypatch.setenv("ONTOLOGY_GUARD_ROOT", str(root))
    code = main()
    captured = capsys.readouterr()
    return code, captured.out, captured.err


# --------------------------------------------------------------------------- #
# The positive control
# --------------------------------------------------------------------------- #


def test_a_lockstep_tree_passes_with_its_counts_printed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out, err = _run(_tree(tmp_path), monkeypatch, capsys)
    assert code == 0, err
    assert "types=1 declared=5 columns=7 excluded=2 offenders=0" in out
    assert "VERDICT: PASS exit=0" in out


# --------------------------------------------------------------------------- #
# AC-3 (i)-(iv), each named
# --------------------------------------------------------------------------- #


def test_i_a_column_neither_declared_nor_excluded_fails_and_is_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _tree(tmp_path, extra_columns='    sa.Column("colour", sa.Text),\n')
    code, _, err = _run(root, monkeypatch, capsys)
    assert code == 1
    assert "[undeclared-column] Widget.colour" in err


def test_ii_a_property_with_no_column_fails_and_is_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _tree(tmp_path, extra_properties="      nickname: {type: string}\n")
    code, _, err = _run(root, monkeypatch, capsys)
    assert code == 1
    assert "[column-less-property] Widget.nickname" in err


def test_iii_a_stale_exclusion_fails_and_is_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _tree(tmp_path, extra_exclusions='    ("Widget", "gone"): "was a column once",\n')
    code, _, err = _run(root, monkeypatch, capsys)
    assert code == 1
    assert "[stale-exclusion] Widget.gone" in err


def test_iv_an_incompatible_type_fails_and_is_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _tree(tmp_path, amount_type="string")
    code, _, err = _run(root, monkeypatch, capsys)
    assert code == 1
    assert "[type-incompatible] Widget.amount" in err


# --------------------------------------------------------------------------- #
# The two shapes AC-3's list does not name, and the refusal
# --------------------------------------------------------------------------- #


def test_a_column_both_excluded_and_declared_fails_and_is_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _tree(tmp_path, extra_properties="      secret: {type: string}\n")
    code, _, err = _run(root, monkeypatch, capsys)
    assert code == 1
    assert "[excluded-and-declared] Widget.secret" in err


def test_a_mapped_type_the_ontology_does_not_declare_fails_and_is_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, _, err = _run(_tree(tmp_path, declare_widget=False), monkeypatch, capsys)
    assert code == 1
    assert "[undeclared-type] Widget.Widget" in err


def test_missing_inputs_refuse_rather_than_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out, _ = _run(tmp_path, monkeypatch, capsys)
    assert code == 2
    assert "VERDICT: REFUSED exit=2" in out


# --------------------------------------------------------------------------- #
# AC-10 — the projection is an allowlist, and a quiet leak attempt reddens
# --------------------------------------------------------------------------- #


def test_ac10_a_new_column_is_outside_the_allowlist_and_reddens_the_guard(tmp_path: Path) -> None:
    """(a) default-excluded AND a red guard, from the same new column."""
    root = _tree(tmp_path, extra_columns='    sa.Column("colour", sa.Text),\n')
    report = compare(*load_inputs(root))
    allowlist = report.allowlists["Widget"]
    # Positive control: the allowlist holds what the ontology declares.
    assert "amount" in allowlist
    assert "colour" not in allowlist
    assert ("undeclared-column", "colour") in {(o.kind, o.name) for o in report.offenders}


def test_ac10_deleting_an_exclusion_while_the_yaml_stays_silent_reddens(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """(b) removing the reason for a column's absence forces a visible diff or a red guard."""
    code, _, err = _run(_tree(tmp_path, exclude_secret=False), monkeypatch, capsys)
    assert code == 1
    assert "[undeclared-column] Widget.secret" in err


# --------------------------------------------------------------------------- #
# Against the real repository
# --------------------------------------------------------------------------- #


def test_this_repository_passes_its_own_guard() -> None:
    """Run for real, as the pre-commit hook does, with the counts pinned.

    The counts are the three ruled types' declared properties (7 + 6 + 8) and their
    tables' columns (9 + 9 + 10), and the seven ``(type, column)`` exclusions that
    account for the difference exactly.
    """
    env = {key: value for key, value in os.environ.items() if key != "ONTOLOGY_GUARD_ROOT"}
    result = subprocess.run(
        [sys.executable, "tools/check_ontology_orm_lockstep.py"],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "types=3 declared=21 columns=28 excluded=7 offenders=0" in result.stdout


def test_ac4_a_a_scratch_column_on_the_real_model_is_named() -> None:
    """AC-4 (a)'s NAME half, on the real ontology and the real ``RepairCase`` table.

    The battery's AC4-a probe edits ``services/db/repair_case.py`` itself and witnesses the
    real run going red, but the driver keeps the outcome, not the stderr that named the
    column. Here the scratch column rides a COPY of the real table instead, compared against
    the real YAML — the name is asserted on the real inputs and no tracked file is touched.
    """
    doc, types, exclusions = load_inputs(_REPO_ROOT)
    scratch_table = types["RepairCase"].__table__.to_metadata(sa.MetaData())
    scratch_table.append_column(sa.Column("probe_scratch", sa.Text))
    report = compare(doc, {**types, "RepairCase": scratch_table}, exclusions)
    named = {(o.kind, o.type_name, o.name) for o in report.offenders}
    assert ("undeclared-column", "RepairCase", "probe_scratch") in named


def test_ac4_b_a_scratch_property_on_the_real_yaml_is_named() -> None:
    """AC-4 (b)'s NAME half: one scratch property on a copy of the real declaration."""
    doc, types, exclusions = load_inputs(_REPO_ROOT)
    scratch_doc = copy.deepcopy(dict(doc))
    scratch_doc["object_types"]["RepairCase"]["properties"]["probe_scratch"] = {"type": "string"}
    report = compare(scratch_doc, types, exclusions)
    named = {(o.kind, o.type_name, o.name) for o in report.offenders}
    assert ("column-less-property", "RepairCase", "probe_scratch") in named
