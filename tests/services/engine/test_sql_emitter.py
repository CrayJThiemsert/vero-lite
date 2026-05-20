"""Tests for the SQL emitter in ``services.engine.code_generator``.

Lesson #7 §3.3 behavioral assertions: structural shape checks via
in-process Python ``text.count`` and substring negations. No
``subprocess`` against ``psql`` (the test environment doesn't include
a Postgres binary).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.engine.code_generator import emit_sql


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
