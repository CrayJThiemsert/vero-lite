"""Tests for the Pydantic emitter in ``services.engine.code_generator``.

Lesson #7 §3.3 behavioral side-effects: emitted models.py is parsed
via ``ast.parse`` (in-process) AND linted via ``ruff check`` (subprocess
to an external linter — behavioral-side-effect class). Class count
checked via Python ``text.count`` (in-process), not subprocess grep.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path
from typing import Any

from services.engine.code_generator import emit_pydantic


def _doc() -> dict[str, Any]:
    return {
        "version": 0,
        "namespace": "test",
        "object_types": {
            "Asset": {
                "primary_key": "asset_id",
                "properties": {
                    "asset_id": {"type": "string", "required": True},
                    "name": {"type": "string"},
                    "status": {"type": "enum", "values": ["active", "retired"]},
                    "capacity_kw": {"type": "float"},
                    "install_date": {"type": "date"},
                    "meta": {"type": "json"},
                    "site_ref": {"type": "ref", "target": "Site"},
                },
            },
            "Site": {
                "primary_key": "site_id",
                "properties": {
                    "site_id": {"type": "string", "required": True},
                    "opened_at": {"type": "timestamp"},
                },
            },
        },
        "link_types": {},
    }


def test_pydantic_emitter_parses_and_classes(tmp_path: Path) -> None:
    out = tmp_path / "models.py"
    emit_pydantic(_doc(), out)
    text = out.read_text()

    ast.parse(text)

    assert text.count("\nclass ") == 2
    assert "class Asset(BaseModel):" in text
    assert "class Site(BaseModel):" in text
    assert "Literal[" in text
    assert "from datetime import date, datetime" in text
    assert "from typing import Any, Literal" in text


def test_pydantic_emitter_required_optionality(tmp_path: Path) -> None:
    out = tmp_path / "models.py"
    emit_pydantic(_doc(), out)
    text = out.read_text()
    assert "asset_id: str" in text
    assert "name: str | None = None" in text
    assert "capacity_kw: float | None = None" in text


def test_pydantic_emitter_passes_ruff(tmp_path: Path) -> None:
    out = tmp_path / "models.py"
    emit_pydantic(_doc(), out)
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert (
        "All checks passed!" in result.stdout or result.stdout == ""
    ), f"ruff stdout: {result.stdout!r}; stderr: {result.stderr!r}"
    assert result.returncode == 0
