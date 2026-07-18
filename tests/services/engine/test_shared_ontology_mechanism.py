"""Cross-doc shared-ontology mechanism (ADR-0033 D2 / PLAN-0082 Step 3b).

The `imports:` grammar + qualified `core.<Type>` ref resolution, exercised at the
GENERATOR layer: ``emit_sql`` / ``emit_orm`` resolve a cross-doc ref against the
imported shared ontology WITHOUT the shipped within-doc ``KeyError``
(``code_generator.py`` SQL/ORM ref emitters). The L2-validation half of the same
mechanism lives in ``test_ontology_validator.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.engine.code_generator import _load_imports, emit_orm, emit_sql


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
