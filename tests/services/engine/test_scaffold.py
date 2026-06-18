"""Tests for the ``vero-lite new-vertical`` scaffolding engine (PLAN-0016).

Unit tests exercise role detection and the direction-aware synthetic breach
against the real energy/supply_chain ontologies. The end-to-end test runs the
CLI in-process (Typer
CliRunner) against a staged copy of the supply_chain ontology renamed to a
fresh namespace, proving domain-renamed scaffolding + the clobber guard
without dirtying the working tree (Lesson #7 §3.2 in-process pattern).
"""

from __future__ import annotations

import ast
import os
import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from services.engine import code_generator, scaffold
from services.engine.cli import app
from services.engine.scaffold import RecommendConfig, ScaffoldError

_SRC_ROOT = Path(__file__).resolve().parents[3]


def _load(namespace: str) -> dict[str, Any]:
    return code_generator.load_doc(
        _SRC_ROOT / "verticals" / namespace / "ontology" / f"{namespace}_v0.yaml"
    )


# --------------------------------------------------------------------------- #
# Role detection
# --------------------------------------------------------------------------- #


def test_detect_roles_energy_canonical_names() -> None:
    roles = scaffold.detect_roles(_load("energy"))
    assert roles.namespace == "energy"
    assert roles.site_type == "Site"
    assert roles.asset_type == "Asset"
    assert roles.asset_site_ref == "site_id"
    assert roles.event_asset_ref == "asset_id"
    assert roles.event_site_ref == "site_id"
    assert roles.event_type_value == "reading"
    assert roles.severity_baseline == "info"
    assert roles.severity_breach == "critical"


def test_detect_roles_supply_chain_domain_renamed() -> None:
    """The Asset/Site roles are domain-renamed (Shipment/Facility) — proving the
    scaffolder is not hardcoded to the energy names."""
    roles = scaffold.detect_roles(_load("supply_chain"))
    assert roles.site_type == "Facility"
    assert roles.asset_type == "Shipment"
    assert roles.asset_site_ref == "facility_id"
    assert roles.event_asset_ref == "shipment_id"
    assert roles.event_site_ref == "facility_id"


def test_detect_roles_requires_geo_site() -> None:
    doc = _load("energy")
    del doc["object_types"]["Site"]["properties"]["lat"]
    with pytest.raises(ScaffoldError, match="geo-bearing Site-role"):
        scaffold.detect_roles(doc)


def test_detect_roles_requires_operational_event() -> None:
    doc = _load("energy")
    del doc["object_types"]["OperationalEvent"]
    with pytest.raises(ScaffoldError, match="OperationalEvent"):
        scaffold.detect_roles(doc)


# --------------------------------------------------------------------------- #
# Direction-aware synthetic breach
# --------------------------------------------------------------------------- #


def _config(direction: str, threshold: float) -> RecommendConfig:
    return RecommendConfig(
        threshold=threshold,
        direction=direction,
        label="dissolved-oxygen",
        unit="mg/L",
        recovery_value=5.5,
        recovery_description="recovered",
    )


@pytest.mark.parametrize(
    ("direction", "threshold", "breach_value"),
    [("below", 4.0, "3.2"), ("above", 90.0, "99.0")],
)
def test_render_synthetic_breach_respects_direction(
    direction: str, threshold: float, breach_value: str
) -> None:
    """A below-direction config breaches *under* the threshold (3.2 < 4); an
    above-direction config breaches *over* it (99 > 90). The rendered module is
    valid Python and self-describes its sources via OBJECT_SOURCES."""
    doc = _load("energy")
    roles = scaffold.detect_roles(doc)
    source = scaffold.render_synthetic(
        roles,
        _config(direction, threshold),
        doc["object_types"]["Site"],
        doc["object_types"]["Asset"],
    )
    ast.parse(source)  # must be valid Python
    assert breach_value in source
    assert "OBJECT_SOURCES" in source
    assert "def operational_events()" in source
    assert "def site_records()" in source
    assert "def asset_records()" in source


# --------------------------------------------------------------------------- #
# End-to-end CLI (staged repo)
# --------------------------------------------------------------------------- #


@pytest.fixture
def scaffold_repo(tmp_path: Path) -> Iterator[Path]:
    """Stage a temp repo with the supply_chain ontology renamed to ``cold_demo``
    + a copy of main.py, and chdir into it. Proves the domain-renamed path."""
    staged = tmp_path / "repo"
    onto_dir = staged / "verticals" / "cold_demo" / "ontology"
    onto_dir.mkdir(parents=True)
    src_onto = (
        _SRC_ROOT / "verticals" / "supply_chain" / "ontology" / "supply_chain_v0.yaml"
    ).read_text(encoding="utf-8")
    (onto_dir / "cold_demo_v0.yaml").write_text(
        src_onto.replace("namespace: supply_chain", "namespace: cold_demo"), encoding="utf-8"
    )
    api_dir = staged / "services" / "api"
    api_dir.mkdir(parents=True)
    shutil.copy2(_SRC_ROOT / "services" / "api" / "main.py", api_dir / "main.py")

    old_cwd = Path.cwd()
    os.chdir(staged)
    try:
        yield staged
    finally:
        os.chdir(old_cwd)


def _new_vertical_args() -> list[str]:
    return [
        "new-vertical",
        "cold_demo",
        "--threshold",
        "8",
        "--direction",
        "below",
        "--label",
        "cold-chain breach",
        "--unit",
        "celsius",
        "--recovery-value",
        "4",
        "--recovery-description",
        "Shipment temperature recovered to the safe range.",
    ]


def test_new_vertical_scaffolds_full_vertical(scaffold_repo: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, _new_vertical_args())
    assert result.exit_code == 0, f"stderr={result.stderr!r}"

    base = scaffold_repo / "verticals" / "cold_demo"
    for rel in (
        "__init__.py",
        "data_adapter/__init__.py",
        "data_adapter/synthetic.py",
        "handlers.py",
        "README.md",
    ):
        path = base / rel
        assert path.exists(), f"missing {rel}"
        assert path.stat().st_size > 0, f"{rel} is empty"

    # The three Python files parse as valid source.
    for rel in ("data_adapter/__init__.py", "data_adapter/synthetic.py", "handlers.py"):
        ast.parse((base / rel).read_text(encoding="utf-8"))

    # The AUTO generator emitted the five artifacts (gitignored output dir).
    generated = base / "generated"
    for name in ("models.py", "schema.sql", "schema.json", "mcp_tools.json", "types.ts"):
        assert (generated / name).exists(), f"missing generated/{name}"

    # The synthetic adapter is domain-renamed (Facility/Shipment, not Asset/Site).
    synthetic_src = (base / "data_adapter" / "synthetic.py").read_text(encoding="utf-8")
    assert "def facility_records()" in synthetic_src
    assert "def shipment_records()" in synthetic_src
    assert "OBJECT_SOURCES" in synthetic_src

    # The README carries the env block with the derived entity + direction.
    readme = (base / "README.md").read_text(encoding="utf-8")
    assert "OCT_VERTICAL=cold_demo" in readme
    assert "OCT_RECOMMEND_DIRECTION=below" in readme
    assert "OCT_RECOMMEND_ENTITY_TYPE=Shipment" in readme
    assert "OCT_RECOMMEND_ENTITY_ID_FIELD=shipment_id" in readme


def test_new_vertical_does_not_code_mod_main(scaffold_repo: Path) -> None:
    """PLAN-0032 (B2): the scaffold no longer edits main.py — the vertical is
    auto-discovered at runtime via the registry import-scan (ADR-0023). main.py is
    unchanged; the conventional ``register_<ns>_handlers`` entry function discovery
    rides on was written."""
    runner = CliRunner()
    main_path = scaffold_repo / "services" / "api" / "main.py"
    original_main = main_path.read_text(encoding="utf-8")
    assert runner.invoke(app, _new_vertical_args()).exit_code == 0
    assert main_path.read_text(encoding="utf-8") == original_main  # NOT code-modded
    handlers = (scaffold_repo / "verticals" / "cold_demo" / "handlers.py").read_text(
        encoding="utf-8"
    )
    assert "def register_cold_demo_handlers(" in handlers


def test_new_vertical_refuses_to_clobber(scaffold_repo: Path) -> None:
    runner = CliRunner()
    assert runner.invoke(app, _new_vertical_args()).exit_code == 0
    # Second run without --force must refuse.
    again = runner.invoke(app, _new_vertical_args())
    assert again.exit_code == 1
    assert "refusing to clobber" in again.stderr
    # With --force it overwrites cleanly.
    forced = runner.invoke(app, [*_new_vertical_args(), "--force"])
    assert forced.exit_code == 0, f"stderr={forced.stderr!r}"


def test_new_vertical_rejects_bad_namespace(scaffold_repo: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "new-vertical",
            "Cold-Demo",
            "--threshold",
            "8",
            "--label",
            "x",
            "--recovery-value",
            "4",
            "--recovery-description",
            "y",
        ],
    )
    assert result.exit_code == 1
    assert "invalid" in result.stderr
