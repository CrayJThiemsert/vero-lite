"""DDL/ORM parity test (PLAN-0005 C-1 / R6).

Asserts the hand-authored ORM (services/db/models.py, via Base.metadata)
agrees with the emitted DDL (verticals/energy/generated/schema.sql) on
table names, column names, and column types. Guards the DDL <-> ORM
drift risk PLAN-0005 R6 flags. DB-free — pure metadata + text compare.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.dialects import postgresql

from services.db import models as _models  # noqa: F401  (registers tables on Base.metadata)
from services.db.base import Base
from services.engine.code_generator import emit_sql, load_doc

_ENERGY_YAML = Path("verticals/energy/ontology/energy_v0.yaml")

_TYPE_ALIASES = {
    "TEXT": "text",
    "DATE": "date",
    "JSONB": "jsonb",
    "DOUBLE PRECISION": "double",
    "TIMESTAMPTZ": "timestamptz",
    "TIMESTAMP WITH TIME ZONE": "timestamptz",
}


def _normalize(sql_type: str) -> str:
    """Collapse Postgres type spellings to a single comparison token."""
    token = " ".join(sql_type.strip().upper().split())
    return _TYPE_ALIASES.get(token, token.lower())


def _parse_ddl(ddl: str) -> dict[str, dict[str, str]]:
    """Parse generated CREATE TABLE statements into {table: {column: type}}."""
    tables: dict[str, dict[str, str]] = {}
    current: str | None = None
    for raw in ddl.splitlines():
        line = raw.strip()
        if line.startswith("CREATE TABLE "):
            current = line.removeprefix("CREATE TABLE ").rstrip(" (")
            tables[current] = {}
            continue
        if line == ");":
            current = None
            continue
        if current is None or not line or line.startswith("--"):
            continue
        tokens = line.rstrip(",").split()
        if tokens[1:3] == ["DOUBLE", "PRECISION"]:
            tables[current][tokens[0]] = _normalize("DOUBLE PRECISION")
        else:
            tables[current][tokens[0]] = _normalize(tokens[1])
    return tables


def _orm_schema() -> dict[str, dict[str, str]]:
    """Build {table: {column: type}} from the hand-authored ORM metadata."""
    dialect = postgresql.dialect()  # type: ignore[no-untyped-call]
    return {
        table.name: {
            column.name: _normalize(column.type.compile(dialect=dialect))
            for column in table.columns
        }
        for table in Base.metadata.tables.values()
    }


def _generated_schema(tmp_path: Path) -> dict[str, dict[str, str]]:
    out = tmp_path / "schema.sql"
    emit_sql(load_doc(_ENERGY_YAML), out)
    return _parse_ddl(out.read_text(encoding="utf-8"))


def test_orm_tables_match_generated_ddl(tmp_path: Path) -> None:
    """Every generated table exists in the ORM and vice versa."""
    assert set(_orm_schema()) == set(_generated_schema(tmp_path))


def test_orm_columns_match_generated_ddl(tmp_path: Path) -> None:
    """Per table, ORM column names match the generated DDL."""
    ddl = _generated_schema(tmp_path)
    orm = _orm_schema()
    for table, columns in ddl.items():
        assert set(orm[table]) == set(columns), f"column mismatch in '{table}'"


def test_orm_column_types_match_generated_ddl(tmp_path: Path) -> None:
    """Per column, the ORM type agrees with the generated DDL (C-1)."""
    ddl = _generated_schema(tmp_path)
    orm = _orm_schema()
    mismatches = [
        f"{table}.{col}: orm={orm[table][col]} ddl={ddl_type}"
        for table, columns in ddl.items()
        for col, ddl_type in columns.items()
        if orm[table][col] != ddl_type
    ]
    assert mismatches == []
