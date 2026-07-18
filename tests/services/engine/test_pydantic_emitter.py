"""Tests for the Pydantic emitter in ``services.engine.code_generator``.

Lesson #7 §3.3 behavioral side-effects: emitted models.py is parsed
via ``ast.parse`` (in-process) AND linted via ``ruff check`` (subprocess
to an external linter — behavioral-side-effect class). Class count
checked via Python ``text.count`` (in-process), not subprocess grep.
"""

from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any

import pydantic
import pytest

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


# ---------- ADR-0033 D3: the `set` collection + `closed:` knob (PLAN-0082 Step 3) ----------


def _person_doc() -> dict[str, Any]:
    """The shared core `Person` shape (ADR-0033 D3/D4) — a `closed:` object with a
    constrained `set` property; mirrors ontology/core_v0.yaml."""
    return {
        "version": 0,
        "namespace": "core",
        "object_types": {
            "Person": {
                "primary_key": "person_id",
                "closed": True,
                "properties": {
                    "person_id": {"type": "string", "required": True},
                    "name": {"type": "string", "required": True},
                    "roles": {
                        "type": "set",
                        "items": "string",
                        "required": True,
                        "constraints": {"min_length": 1},
                    },
                },
            },
        },
        "link_types": {},
    }


def test_pydantic_emitter_set_and_closed_source(tmp_path: Path) -> None:
    """ADR-0033 D3: a `set` property emits `frozenset[<item>]` + a `Field(min_length=)`,
    and `closed: true` emits `model_config = ConfigDict(extra="forbid")`; the import
    line grows to include ConfigDict + Field."""
    out = tmp_path / "models.py"
    emit_pydantic(_person_doc(), out)
    text = out.read_text()
    ast.parse(text)
    assert "from pydantic import BaseModel, ConfigDict, Field" in text
    assert 'model_config = ConfigDict(extra="forbid")' in text
    assert "roles: frozenset[str] = Field(min_length=1)" in text
    assert "person_id: str" in text


def test_pydantic_emitter_set_closed_passes_ruff(tmp_path: Path) -> None:
    out = tmp_path / "models.py"
    emit_pydantic(_person_doc(), out)
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


def test_pydantic_emitter_constraints_enforce_at_runtime(tmp_path: Path) -> None:
    """AC-2 (the load-bearing half): the EMITTED `Person` enforces its constraints —
    an empty role set (min_length=1) and an unknown field (extra="forbid") are both
    REJECTED by the generated model, never a hand-written shim (ADR-0033 D3)."""
    out = tmp_path / "models.py"
    emit_pydantic(_person_doc(), out)
    spec = importlib.util.spec_from_file_location("gen_core_person", out)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    person = module.Person(person_id="p1", name="A", roles={"dept_head"})
    assert isinstance(person.roles, frozenset)

    with pytest.raises(pydantic.ValidationError):
        module.Person(person_id="p1", name="A", roles=set())  # min_length=1
    with pytest.raises(pydantic.ValidationError):
        module.Person(person_id="p1", name="A", roles={"r"}, bogus=1)  # extra="forbid"
