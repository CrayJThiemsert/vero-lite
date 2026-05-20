"""End-to-end CLI tests via Typer's CliRunner (Lesson #7 §3.2 in-process).

These tests run the CLI in-process against the real
``verticals/energy/ontology/energy_v0.yaml`` and assert the validator
+ generator pipeline behaves correctly. Generated artifacts are
emitted into a tmp_path-rooted copy of the vertical so the repo's
working tree never becomes dirty during test runs.
"""

from __future__ import annotations

import ast
import json
import os
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from typer.testing import CliRunner

from services.engine.cli import app


@pytest.fixture
def staged_repo(tmp_path: Path) -> Iterator[Path]:
    """Stage a minimal copy of the repo at ``tmp_path`` and chdir into it."""
    src_root = Path(__file__).resolve().parents[3]
    staged = tmp_path / "repo"
    (staged / "verticals" / "energy" / "ontology").mkdir(parents=True)
    shutil.copy2(
        src_root / "verticals" / "energy" / "ontology" / "energy_v0.yaml",
        staged / "verticals" / "energy" / "ontology" / "energy_v0.yaml",
    )
    old_cwd = Path.cwd()
    os.chdir(staged)
    try:
        yield staged
    finally:
        os.chdir(old_cwd)


def test_cli_validate_energy_succeeds(staged_repo: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["validate", "energy"])
    assert result.exit_code == 0, f"stderr={result.stderr!r}"
    assert "OK: 1 file(s) valid" in result.stderr


def test_cli_generate_energy_emits_five_artifacts(staged_repo: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["generate", "energy"])
    assert result.exit_code == 0, f"stderr={result.stderr!r}"

    generated = staged_repo / "verticals" / "energy" / "generated"
    expected = ["models.py", "schema.sql", "schema.json", "mcp_tools.json", "types.ts"]
    for name in expected:
        path = generated / name
        assert path.exists(), f"missing {name}"
        assert path.stat().st_size > 0, f"{name} is empty"

    ast.parse((generated / "models.py").read_text())

    sql = (generated / "schema.sql").read_text()
    assert sql.count("\nCREATE TABLE ") == 6
    assert "TEXT REFERENCES site(site_id)" in sql

    bundle = json.loads((generated / "schema.json").read_text())
    assert set(bundle.keys()) == {
        "Asset",
        "Site",
        "OperationalEvent",
        "Alert",
        "RecommendedAction",
        "AlertEventLink",
    }
    for schema in bundle.values():
        Draft202012Validator.check_schema(schema)

    tools = json.loads((generated / "mcp_tools.json").read_text())
    assert len(tools) == 12

    ts = (generated / "types.ts").read_text()
    assert ts.count("export interface ") == 6
    assert ts.count("{") == ts.count("}")
