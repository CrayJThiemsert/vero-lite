"""Cross-doc shared-ontology mechanism (ADR-0033 D2 / PLAN-0082 Step 3b).

The `imports:` grammar + qualified `core.<Type>` ref resolution, exercised at the
GENERATOR layer: ``emit_sql`` / ``emit_orm`` resolve a cross-doc ref against the
imported shared ontology WITHOUT the shipped within-doc ``KeyError``
(``code_generator.py`` SQL/ORM ref emitters). The L2-validation half of the same
mechanism lives in ``test_ontology_validator.py``.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from services.engine.code_generator import (
    _load_imports,
    emit_orm,
    emit_pydantic,
    emit_sql,
    generate_all,
    load_doc,
)

_CORE_ONTOLOGY = Path(__file__).parents[3] / "ontology" / "core_v0.yaml"


def _importing_doc() -> dict[str, Any]:
    """A vertical importing the shared `core` ontology and referencing `core.Person`."""
    return {
        "version": 0,
        "namespace": "procurement",
        "imports": ["core"],
        "object_types": {
            "PurchaseOrder": {
                "primary_key": "po_id",
                "properties": {
                    "po_id": {"type": "string", "required": True},
                    "approver": {"type": "ref", "target": "core.Person"},
                },
            },
        },
    }


def test_load_imports_reads_shared_core() -> None:
    """ADR-0033 D2: `_load_imports` resolves the reserved `core` token to the shipped
    shared doc (`ontology/core_v0.yaml`) and exposes its `Person` object_type."""
    imported = _load_imports(_importing_doc())
    assert "core" in imported
    assert imported["core"]["Person"]["primary_key"] == "person_id"


def test_sql_resolves_qualified_cross_doc_ref(tmp_path: Path) -> None:
    """ADR-0033 D2: emit_sql resolves `core.Person` -> `REFERENCES person(person_id)`
    (the bare type name, never the qualified string) with no KeyError."""
    doc = _importing_doc()
    out = tmp_path / "schema.sql"
    emit_sql(doc, out, _load_imports(doc))
    text = out.read_text()
    assert "REFERENCES person(person_id)" in text
    assert "core.person" not in text


def test_orm_resolves_qualified_cross_doc_ref(tmp_path: Path) -> None:
    """ADR-0033 D2: emit_orm resolves `core.Person` -> `ForeignKey("person.person_id")`."""
    doc = _importing_doc()
    out = tmp_path / "orm.py"
    emit_orm(doc, out, _load_imports(doc))
    text = out.read_text()
    assert 'ForeignKey("person.person_id")' in text


def test_within_doc_ref_still_resolves(tmp_path: Path) -> None:
    """Backward-compat: an unqualified (within-doc) ref resolves as before — no
    `imported` map, resolution against the local doc's object_types."""
    doc: dict[str, Any] = {
        "version": 0,
        "namespace": "energy",
        "object_types": {
            "Asset": {
                "primary_key": "asset_id",
                "properties": {
                    "asset_id": {"type": "string", "required": True},
                    "site_ref": {"type": "ref", "target": "Site"},
                },
            },
            "Site": {
                "primary_key": "site_id",
                "properties": {"site_id": {"type": "string", "required": True}},
            },
        },
    }
    out = tmp_path / "schema.sql"
    emit_sql(doc, out)
    assert "REFERENCES site(site_id)" in out.read_text()


# ---------- ADR-0033 D3: set -> JSONB across the emitters (PLAN-0082 Step 4a) ----------


def test_shared_person_generates_full_artifact_set(tmp_path: Path) -> None:
    """PLAN-0082 Step 4a: generating the shipped ontology/core_v0.yaml emits every
    artifact with the `set` roles handled per emitter — SQL JSONB + jsonb_array_length
    CHECK, ORM Mapped[list[str]] over JSONB, JSON Schema unique array + minItems, TS
    string[]. The generated ORM parses as valid Python."""
    out = tmp_path / "core" / "generated"
    outputs = generate_all(_CORE_ONTOLOGY, out)

    sql = outputs["sql"].read_text()
    assert "roles JSONB CHECK (jsonb_array_length(roles) >= 1) NOT NULL" in sql

    orm = outputs["orm"].read_text()
    ast.parse(orm)
    assert "from sqlalchemy.dialects.postgresql import JSONB" in orm
    assert "roles: Mapped[list[str]] = mapped_column(JSONB, nullable=False)" in orm

    js = outputs["jsonschema"].read_text()
    assert '"uniqueItems": true' in js
    assert '"minItems": 1' in js

    ts = outputs["typescript"].read_text()
    assert "roles: string[];" in ts


# ---------- ADR-0033 D5 / SD-I=(b): the committed shared Person ORM (PLAN-0082 Step 4b) ----------

_COMMITTED_PERSON_ORM = Path(__file__).parents[3] / "services" / "db" / "person.py"


def test_committed_person_orm_is_reproducible(tmp_path: Path) -> None:
    """AC-3: the committed services/db/person.py is byte-reproducible from
    ontology/core_v0.yaml — idempotent regeneration, no hand edits (the shared ORM
    lands at a COMMITTED path, ADR-0033 D5, but stays generator-owned)."""
    committed = _COMMITTED_PERSON_ORM.read_text()
    fresh = tmp_path / "person.py"
    emit_orm(load_doc(_CORE_ONTOLOGY), fresh)
    assert fresh.read_text() == committed


def test_core_orm_columns_match_generated_ddl(tmp_path: Path) -> None:
    """Core parity (mirrors the energy DDL<->ORM guard, core-scoped): the shared
    Person ORM's columns match core's generated DDL; roles is a JSONB column."""
    from services.db.person import Person

    out = tmp_path / "schema.sql"
    emit_sql(load_doc(_CORE_ONTOLOGY), out)
    ddl = out.read_text()

    assert {c.name for c in Person.__table__.columns} == {"person_id", "name", "roles"}
    assert str(Person.__table__.c.roles.type) == "JSONB"
    assert Person.__table__.c.roles.nullable is False
    assert "CREATE TABLE person (" in ddl
    assert "roles JSONB" in ddl


# ---------- ADR-0033 D4 / SD-H=(a): the committed shared Person PYDANTIC re-export
# (PLAN-0082 Step 5) ----------

_REPO_ROOT = Path(__file__).parents[3]
_COMMITTED_PERSON_MODEL = _REPO_ROOT / "services" / "engine" / "procedures" / "person_model.py"


def test_committed_person_pydantic_is_reproducible(tmp_path: Path) -> None:
    """AC-3 (Step 5, SD-H=(a)): the committed services/engine/procedures/person_model.py is
    byte-reproducible from ontology/core_v0.yaml — the RE-EXPORTED shared Person stays
    generator-owned (no hand edits), mirroring the committed-ORM guard above
    (test_committed_person_orm_is_reproducible). The Pydantic emitter routes here via
    _PYDANTIC_COMMITTED_DEST["core"] under generate_all."""
    committed = _COMMITTED_PERSON_MODEL.read_text()
    fresh = tmp_path / "person_model.py"
    emit_pydantic(load_doc(_CORE_ONTOLOGY), fresh)
    assert fresh.read_text() == committed


def test_exactly_one_pydantic_person_definition() -> None:
    """AC-4 (SD-H=(a)): after the spec-layer Person is deleted + re-exported, EXACTLY ONE
    Pydantic ``class Person(BaseModel)`` definition exists in committed source — the generated
    shared type at services/engine/procedures/person_model.py. A regression that reintroduces a
    second independent Person (a per-vertical copy, or un-deleting the spec-layer class) fails
    here. (The SQLAlchemy ``class Person(Base)`` ORM is a different base and is not matched;
    gitignored ``generated/`` reference artifacts are excluded.)"""
    needle = "class Person(BaseModel)"
    hits = sorted(
        p.relative_to(_REPO_ROOT).as_posix()
        for root in ("services", "verticals")
        for p in (_REPO_ROOT / root).rglob("*.py")
        if "/generated/" not in p.as_posix() and needle in p.read_text(encoding="utf-8")
    )
    assert hits == ["services/engine/procedures/person_model.py"], hits


def test_spec_person_is_the_generated_shared_type() -> None:
    """AC-4/AC-2 (SD-H=(a)): ``spec.Person`` resolves to the generated shared type (the
    re-export), NOT a second hand-written definition — and the re-exported type still enforces
    the load-bearing constraints the shipped spec Person carried (``roles`` non-empty +
    unknown-field rejection), now EMITTER-expressed from core_v0.yaml, never a hand shim."""
    from services.engine.procedures import person_model, spec

    assert spec.Person is person_model.Person
    with pytest.raises(ValidationError):  # roles min_length>=1
        spec.Person(person_id="p1", name="A", roles=frozenset())
    with pytest.raises(ValidationError):  # extra="forbid"
        spec.Person(person_id="p1", name="A", roles=frozenset({"approver"}), rank="x")
    ok = spec.Person(person_id="p1", name="A", roles=frozenset({"approver"}))
    assert ok.roles == frozenset({"approver"})
