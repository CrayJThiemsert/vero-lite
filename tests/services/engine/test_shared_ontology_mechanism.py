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

from services.engine.code_generator import (
    _load_imports,
    emit_orm,
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
