"""Tests for the SQL emitter in ``services.engine.code_generator``.

Lesson #7 §3.3 behavioral assertions: structural shape checks via
in-process Python ``text.count`` and substring negations. No
``subprocess`` against ``psql`` (the test environment doesn't include
a Postgres binary).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from services.engine.code_generator import _load_imports, emit_sql, load_doc
from tests.support.ontology_docs import REPO_ROOT, ontology_docs


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
                    "capacity_kw": {"type": "float"},
                    "install_date": {"type": "date"},
                    "status": {"type": "enum", "values": ["active", "retired"]},
                    "meta": {"type": "json"},
                    "site_ref": {"type": "ref", "target": "Site"},
                },
            },
            "Site": {
                "primary_key": "site_id",
                "properties": {
                    "site_id": {"type": "string", "required": True},
                    "opened_at": {"type": "timestamp"},
                    "open": {"type": "bool"},
                    "count_hint": {"type": "int"},
                },
            },
        },
        "link_types": {},
    }


def test_sql_emitter_table_and_index_count(tmp_path: Path) -> None:
    out = tmp_path / "schema.sql"
    emit_sql(_doc(), out)
    text = out.read_text()
    assert text.count("\nCREATE TABLE ") == 2
    assert text.count("\nCREATE INDEX ") == 1


def test_sql_emitter_postgres_dialect_guards(tmp_path: Path) -> None:
    out = tmp_path / "schema.sql"
    emit_sql(_doc(), out)
    text = out.read_text()
    assert " JSONB" in text
    assert " BIGINT" in text
    assert " DOUBLE PRECISION" in text
    assert " TIMESTAMPTZ" in text
    assert " BOOLEAN" in text
    assert " DATE" in text

    assert " JSON " not in text
    assert " INT " not in text
    assert " FLOAT" not in text


def test_sql_emitter_primary_key_and_constraints(tmp_path: Path) -> None:
    out = tmp_path / "schema.sql"
    emit_sql(_doc(), out)
    text = out.read_text()
    assert "asset_id TEXT PRIMARY KEY" in text
    assert "site_id TEXT PRIMARY KEY" in text
    assert "status TEXT CHECK (status IN ('active', 'retired'))" in text
    assert "REFERENCES site(site_id)" in text
    assert "CREATE INDEX idx_asset_site_ref ON asset(site_ref);" in text


def test_sql_emitter_appends_the_tenant_key_to_every_table(tmp_path: Path) -> None:
    """PLAN-0101 SD-2(b) / AC-1: the tenant key lands on EVERY generated table —
    counted, not spot-checked, so a table added later cannot quietly skip it.

    SD-1(b) rules the stamp Python-side, so the DDL carries NO ``DEFAULT``: an
    unstamped write must fail ``NOT NULL`` loudly. That absence is asserted here
    because the Step-1.4 measurement showed ``alembic check`` cannot see a
    ``server_default`` drift back in — the tooling will never catch it for us.
    """
    out = tmp_path / "schema.sql"
    emit_sql(_doc(), out)
    text = out.read_text()
    assert text.count("  tenant_id TEXT NOT NULL") == text.count("\nCREATE TABLE ")
    assert "tenant_id TEXT NOT NULL DEFAULT" not in text


# ---------- PLAN-0127 PR-1: CREATE TABLE in reference-dependency order ----------

# A whole ``CREATE TABLE <name> (`` line, so ``alert`` never matches ``alert_event_link``.
_CREATE_TABLE = re.compile(r"^CREATE TABLE (\w+) \($", re.MULTILINE)
_REFERENCES = re.compile(r"REFERENCES (\w+)\(")


def _forward_references(ddl: str) -> list[str]:
    """Every ``REFERENCES x(`` that appears before ``CREATE TABLE x (``, as ``owner -> x``.

    Each one is a statement Postgres rejects with ``UndefinedTableError`` when the file is
    applied top to bottom. A target no ``CREATE TABLE`` in the file declares (a qualified
    ``core.X`` ref into another doc's DDL) is external, not forward. A self-reference is
    legal inside its own ``CREATE TABLE`` and is not reported.
    """
    declared = {m.group(1): m.start() for m in _CREATE_TABLE.finditer(ddl)}
    found: list[str] = []
    for ref in _REFERENCES.finditer(ddl):
        target = ref.group(1)
        if target not in declared:
            continue
        owner = max(
            (name for name, start in declared.items() if start < ref.start()),
            key=declared.__getitem__,
        )
        if target != owner and declared[target] > ref.start():
            found.append(f"{owner} -> {target}")
    return found


def test_forward_reference_instrument_control() -> None:
    """The instrument AC-12 rests on, read on known content before its real reading.

    The known-bad file references ``alert`` before declaring it and must read exactly one
    forward reference; the same two tables in dependency order must read none. The pair
    ``alert`` / ``alert_event_link`` is the prefix collision a substring match gets wrong.
    """
    link = "CREATE TABLE alert_event_link (\n  alert_ref TEXT REFERENCES alert(alert_id)\n);\n"
    alert = "CREATE TABLE alert (\n  alert_id TEXT PRIMARY KEY\n);\n"
    assert _forward_references(link + "\n" + alert) == ["alert_event_link -> alert"]
    assert _forward_references(alert + "\n" + link) == []


def test_ontology_doc_enumeration_is_complete() -> None:
    """The per-doc checks run over the whole doc set, never a silently empty one.

    A rule, not a roster: the enumerated docs' namespaces are exactly the names of the
    ``verticals/<d>/ontology/`` directories, one each, followed by the shared ``core``. A
    directory with no doc, a second doc in one directory, a namespace that disagrees with
    its directory, or a missing ``core`` all break the equality.
    """
    ontology_dirs = {
        p.parent.name for p in (REPO_ROOT / "verticals").glob("*/ontology") if p.is_dir()
    }
    # Positive control: an empty tree on both sides would satisfy the equality below.
    assert ontology_dirs, "no verticals/*/ontology/ directory — the enumeration root moved"
    enumerated = [load_doc(path).get("namespace") for path in ontology_docs()]
    assert enumerated == [*sorted(ontology_dirs), "core"]


def test_generated_ddl_declares_every_table_before_it_is_referenced(tmp_path: Path) -> None:
    """AC-12, the DB-free twin of ``test_generated_ddl_applies``: across every real
    ontology doc, no ``REFERENCES`` names a table declared later in the same file.

    Pre-fix (insertion order) this lists all six verticals; ``core`` has no refs.
    """
    forward: dict[str, list[str]] = {}
    references = 0
    docs = ontology_docs()
    for yaml_path in docs:
        doc = load_doc(yaml_path)
        namespace = str(doc.get("namespace", ""))
        ddl = emit_sql(doc, tmp_path / f"{namespace}.sql", _load_imports(doc)).read_text()
        references += len(_REFERENCES.findall(ddl))
        if found := _forward_references(ddl):
            forward[namespace] = found
    print(f"docs={len(docs)} references={references} forward={sum(map(len, forward.values()))}")
    # Positive control: the docs do carry references to order, so an empty result below
    # is a reading, not an instrument that found nothing to look at.
    assert references > 0, "no REFERENCES in any generated DDL — nothing was checked"
    assert forward == {}


def test_sql_emitter_declares_a_referenced_table_first(tmp_path: Path) -> None:
    """The fixture doc lists ``Asset`` (which references ``Site``) before ``Site``; the
    DDL must still create ``site`` first."""
    out = tmp_path / "schema.sql"
    emit_sql(_doc(), out)
    assert _CREATE_TABLE.findall(out.read_text()) == ["site", "asset"]


def _typed(name: str, *refs: str) -> dict[str, Any]:
    """An object type with a string primary key and one ``ref`` property per target."""
    pk = f"{name.lower()}_id"
    props: dict[str, Any] = {pk: {"type": "string", "required": True}}
    for target in refs:
        props[f"{target.lower().replace('.', '_')}_ref"] = {"type": "ref", "target": target}
    return {"primary_key": pk, "properties": props}


def test_sql_emitter_table_order_keeps_insertion_order_between_ties(tmp_path: Path) -> None:
    """Stable order: a table moves only as far as its references force it. ``Charlie``
    and ``Delta`` reference nothing and keep their places; ``Bravo`` is pulled ahead of
    ``Alpha``, which references it."""
    doc = {
        "object_types": {
            "Charlie": _typed("Charlie"),
            "Alpha": _typed("Alpha", "Bravo"),
            "Bravo": _typed("Bravo"),
            "Delta": _typed("Delta"),
        }
    }
    out = tmp_path / "schema.sql"
    emit_sql(doc, out)
    assert _CREATE_TABLE.findall(out.read_text()) == ["charlie", "bravo", "alpha", "delta"]


def _refusal(doc: dict[str, Any], out: Path) -> str | None:
    """Emit ``doc``; return the emitter's refusal message, or ``None`` when it wrote the file.

    Turns a wrongful refusal into a failed ASSERTION at the calling test's own line rather
    than an uncaught ``ValueError`` — a crash names no claim, so no probe could witness it.
    """
    try:
        emit_sql(doc, out, _load_imports(doc))
    except ValueError as exc:
        return str(exc)
    return None


def test_sql_emitter_allows_a_self_reference(tmp_path: Path) -> None:
    """A table referencing itself is legal inside its own ``CREATE TABLE`` — it is not an
    ordering edge, and certainly not a cycle. No real doc has one today."""
    doc = {"object_types": {"Employee": _typed("Employee", "Employee")}}
    out = tmp_path / "schema.sql"
    refused = _refusal(doc, out)
    assert refused is None, f"a self-reference was refused as a cycle: {refused}"
    assert "REFERENCES employee(employee_id)" in out.read_text()


def test_sql_emitter_a_qualified_ref_is_not_an_ordering_edge(tmp_path: Path) -> None:
    """``core.Person`` names a table the imported ``core`` DDL creates, so it is no ordering
    edge in this doc — not even beside a local ``Person``, whose table shares the bare name.
    The emitter neither refuses the doc nor moves ``purchase_order`` behind ``person``. No
    real doc imports ``core`` today, so this fixture is the only guard."""
    doc = {
        "imports": ["core"],
        "object_types": {
            "PurchaseOrder": _typed("PurchaseOrder", "core.Person"),
            "Person": _typed("Person"),
        },
    }
    out = tmp_path / "schema.sql"
    refused = _refusal(doc, out)
    assert refused is None, f"a qualified ref was treated as a local edge: {refused}"
    assert _CREATE_TABLE.findall(out.read_text()) == ["purchase_order", "person"]


def test_sql_emitter_refuses_a_reference_cycle(tmp_path: Path) -> None:
    """Two tables that reference each other have no inline ``REFERENCES`` order that
    applies, so the emitter refuses rather than write DDL that cannot. No real doc has
    a cycle today."""
    doc = {"object_types": {"Alpha": _typed("Alpha", "Bravo"), "Bravo": _typed("Bravo", "Alpha")}}
    out = tmp_path / "schema.sql"
    with pytest.raises(ValueError, match=r"cycle.*'Alpha', 'Bravo'"):
        emit_sql(doc, out)
    assert not out.exists()
