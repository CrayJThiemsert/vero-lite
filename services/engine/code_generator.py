"""Code generator: emits 5 artifacts per vertical from an ontology YAML.

Implements ADR-008 D5. Each emitter is a pure-Python structured
builder — no Jinja2 (consultation reply Q6: the project is dep-
conservative). Outputs are deterministic given the same input doc,
ordered by ``object_types`` insertion order from the parsed YAML.

This commit (PLAN-003 commit 4) ships the orchestrator plus the
Pydantic + SQL emitters. Commit 5 lands JSON Schema, MCP, and
TypeScript emitters.

Type mappings (per ADR-008 D3 + PLAN-003 §6):

| YAML type | Pydantic field | Postgres column |
| --------- | -------------- | --------------- |
| string    | str            | TEXT            |
| int       | int            | BIGINT          |
| float     | float          | DOUBLE PRECISION|
| bool      | bool           | BOOLEAN         |
| timestamp | datetime       | TIMESTAMPTZ     |
| date      | date           | DATE            |
| enum      | Literal[...]   | TEXT CHECK (...)|
| json      | dict[str, Any] | JSONB           |
| ref       | str (FK value) | TEXT REFERENCES |

``int → BIGINT`` follows PLAN-003 §6.2 (Postgres-native default for
entity IDs; ADR-008 D3 narrative says ``INTEGER`` but PLAN-003 §6.2
is the more recent binding spec for Phase 1).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

_PY_SCALAR_TYPE: dict[str, str] = {
    "string": "str",
    "int": "int",
    "float": "float",
    "bool": "bool",
    "timestamp": "datetime",
    "date": "date",
    "json": "dict[str, Any]",
    "ref": "str",
}

_SQL_SCALAR_TYPE: dict[str, str] = {
    "string": "TEXT",
    "int": "BIGINT",
    "float": "DOUBLE PRECISION",
    "bool": "BOOLEAN",
    "timestamp": "TIMESTAMPTZ",
    "date": "DATE",
    "json": "JSONB",
}

_CAMEL_BOUNDARY = re.compile(r"(.)([A-Z][a-z]+)")
_LOWER_UPPER = re.compile(r"([a-z0-9])([A-Z])")


def _snake(name: str) -> str:
    """``AssetEventLink`` -> ``asset_event_link``."""
    interim = _CAMEL_BOUNDARY.sub(r"\1_\2", name)
    return _LOWER_UPPER.sub(r"\1_\2", interim).lower()


def load_doc(yaml_path: Path) -> dict[str, Any]:
    """Parse an ontology YAML file into a plain dict (safe loader)."""
    yaml = YAML(typ="safe")
    with yaml_path.open() as fh:
        loaded: dict[str, Any] = yaml.load(fh)
    return loaded


# ---------------------------------------------------------------------------
# Pydantic emitter
# ---------------------------------------------------------------------------


def _py_field_type(prop_def: dict[str, Any]) -> str:
    ptype = prop_def["type"]
    if ptype == "enum":
        values = prop_def["values"]
        literals = ", ".join(f'"{v}"' for v in values)
        return f"Literal[{literals}]"
    return _PY_SCALAR_TYPE[ptype]


def _py_used_imports(object_types: dict[str, Any]) -> tuple[set[str], set[str]]:
    """Return (datetime_imports, typing_imports) actually used by the doc."""
    datetime_set: set[str] = set()
    typing_set: set[str] = set()
    for obj_def in object_types.values():
        for prop_def in (obj_def.get("properties") or {}).values():
            ptype = prop_def["type"]
            if ptype == "timestamp":
                datetime_set.add("datetime")
            elif ptype == "date":
                datetime_set.add("date")
            elif ptype == "enum":
                typing_set.add("Literal")
            elif ptype == "json":
                typing_set.add("Any")
    return datetime_set, typing_set


def emit_pydantic(doc: dict[str, Any], output_path: Path) -> Path:
    """Write Pydantic v2 models for every object_type to ``output_path``."""
    object_types = doc.get("object_types") or {}
    datetime_imports, typing_imports = _py_used_imports(object_types)

    lines: list[str] = [
        '"""Generated Pydantic models from ontology YAML — do not edit by hand."""',
        "",
        "from __future__ import annotations",
        "",
    ]
    if datetime_imports:
        lines.append(f"from datetime import {', '.join(sorted(datetime_imports))}")
    if typing_imports:
        lines.append(f"from typing import {', '.join(sorted(typing_imports))}")
    if datetime_imports or typing_imports:
        lines.append("")
    lines.append("from pydantic import BaseModel")
    lines.append("")

    for obj_name, obj_def in object_types.items():
        lines.append("")
        lines.append(f"class {obj_name}(BaseModel):")
        props = obj_def.get("properties") or {}
        if not props:
            lines.append("    pass")
            continue
        for prop_name, prop_def in props.items():
            py_type = _py_field_type(prop_def)
            if prop_def.get("required", False):
                lines.append(f"    {prop_name}: {py_type}")
            else:
                lines.append(f"    {prop_name}: {py_type} | None = None")
    body = "\n".join(lines).rstrip() + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(body)
    return output_path


# ---------------------------------------------------------------------------
# SQL emitter (Postgres-specific per ADR-008 D3 + PLAN-003 §6.2)
# ---------------------------------------------------------------------------


def _sql_type(prop_name: str, prop_def: dict[str, Any], object_types: dict[str, Any]) -> str:
    ptype = prop_def["type"]
    if ptype == "enum":
        values = prop_def["values"]
        choices = ", ".join(f"'{v}'" for v in values)
        return f"TEXT CHECK ({prop_name} IN ({choices}))"
    if ptype == "ref":
        target = prop_def["target"]
        target_def = object_types[target]
        target_pk = target_def["primary_key"]
        return f"TEXT REFERENCES {_snake(target)}({target_pk})"
    return _SQL_SCALAR_TYPE[ptype]


def _sql_column_line(
    prop_name: str,
    prop_def: dict[str, Any],
    primary_key: str,
    object_types: dict[str, Any],
) -> str:
    sql_type = _sql_type(prop_name, prop_def, object_types)
    parts = [f"  {prop_name} {sql_type}"]
    if prop_name == primary_key:
        parts.append("PRIMARY KEY")
    elif prop_def.get("required", False):
        parts.append("NOT NULL")
    return " ".join(parts)


def emit_sql(doc: dict[str, Any], output_path: Path) -> Path:
    """Write Postgres DDL (CREATE TABLE + CREATE INDEX) to ``output_path``."""
    object_types = doc.get("object_types") or {}
    lines: list[str] = [
        "-- Generated PostgreSQL DDL from ontology YAML — do not edit by hand.",
        "",
    ]
    index_lines: list[str] = []
    for obj_name, obj_def in object_types.items():
        table = _snake(obj_name)
        pk = obj_def.get("primary_key", "")
        props = obj_def.get("properties") or {}
        lines.append(f"CREATE TABLE {table} (")
        col_lines = [
            _sql_column_line(prop_name, prop_def, pk, object_types)
            for prop_name, prop_def in props.items()
        ]
        lines.append(",\n".join(col_lines))
        lines.append(");")
        lines.append("")
        for prop_name, prop_def in props.items():
            if prop_def["type"] == "ref":
                index_lines.append(f"CREATE INDEX idx_{table}_{prop_name} ON {table}({prop_name});")
    lines.extend(index_lines)
    body = "\n".join(lines).rstrip() + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(body)
    return output_path


# ---------------------------------------------------------------------------
# JSON Schema emitter (draft 2020-12)
# ---------------------------------------------------------------------------


def _jsonschema_field(prop_def: dict[str, Any]) -> dict[str, Any]:
    ptype = prop_def["type"]
    if ptype == "string":
        return {"type": "string"}
    if ptype == "int":
        return {"type": "integer"}
    if ptype == "float":
        return {"type": "number"}
    if ptype == "bool":
        return {"type": "boolean"}
    if ptype == "timestamp":
        return {"type": "string", "format": "date-time"}
    if ptype == "date":
        return {"type": "string", "format": "date"}
    if ptype == "enum":
        return {"type": "string", "enum": list(prop_def["values"])}
    if ptype == "json":
        return {"type": "object"}
    # ref
    return {"type": "string"}


def emit_jsonschema(doc: dict[str, Any], output_path: Path) -> Path:
    """Write per-object JSON Schemas (draft 2020-12) to ``output_path``."""
    object_types = doc.get("object_types") or {}
    bundle: dict[str, Any] = {}
    for obj_name, obj_def in object_types.items():
        props = obj_def.get("properties") or {}
        properties = {pn: _jsonschema_field(pd) for pn, pd in props.items()}
        required = [pn for pn, pd in props.items() if pd.get("required", False)]
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": obj_name,
            "type": "object",
            "properties": properties,
        }
        if required:
            schema["required"] = required
        bundle[obj_name] = schema
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(bundle, indent=2) + "\n")
    return output_path


# ---------------------------------------------------------------------------
# MCP tool-definition emitter
# ---------------------------------------------------------------------------


def _mcp_tools_for(obj_name: str) -> list[dict[str, Any]]:
    snake = _snake(obj_name)
    return [
        {
            "name": f"list_{snake}",
            "description": f"List {obj_name} records.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 100},
                },
                "required": [],
            },
        },
        {
            "name": f"get_{snake}_by_id",
            "description": f"Fetch a single {obj_name} by primary key.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                },
                "required": ["id"],
            },
        },
    ]


def emit_mcp(doc: dict[str, Any], output_path: Path) -> Path:
    """Write MCP tool definitions to ``output_path``.

    Action-bearing tools (mutations) are deferred to Phase 2 when the
    `RecommendedAction` runtime lands (PLAN-003 §6.4 + consultation Q8).
    """
    object_types = doc.get("object_types") or {}
    tools: list[dict[str, Any]] = []
    for obj_name in object_types:
        tools.extend(_mcp_tools_for(obj_name))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(tools, indent=2) + "\n")
    return output_path


# ---------------------------------------------------------------------------
# TypeScript emitter (light path — no tsc compile per PLAN-003 §6.5)
# ---------------------------------------------------------------------------

_TS_SCALAR_TYPE: dict[str, str] = {
    "string": "string",
    "int": "number",
    "float": "number",
    "bool": "boolean",
    "timestamp": "string",
    "date": "string",
    "json": "Record<string, unknown>",
    "ref": "string",
}


def _ts_field_type(prop_def: dict[str, Any]) -> str:
    ptype = prop_def["type"]
    if ptype == "enum":
        return " | ".join(f"'{v}'" for v in prop_def["values"])
    return _TS_SCALAR_TYPE[ptype]


def emit_typescript(doc: dict[str, Any], output_path: Path) -> Path:
    """Write TS interface declarations to ``output_path``."""
    object_types = doc.get("object_types") or {}
    lines: list[str] = [
        "// Generated TypeScript types from ontology YAML — do not edit by hand.",
        "",
    ]
    for obj_name, obj_def in object_types.items():
        lines.append(f"export interface {obj_name} {{")
        for prop_name, prop_def in (obj_def.get("properties") or {}).items():
            ts_type = _ts_field_type(prop_def)
            sep = ":" if prop_def.get("required", False) else "?:"
            lines.append(f"  {prop_name}{sep} {ts_type};")
        lines.append("}")
        lines.append("")
    body = "\n".join(lines).rstrip() + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(body)
    return output_path


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def generate_all(yaml_path: Path, output_dir: Path) -> dict[str, Path]:
    """Run every emitter against ``yaml_path``; return name -> output path map."""
    doc = load_doc(yaml_path)
    outputs: dict[str, Path] = {}
    outputs["pydantic"] = emit_pydantic(doc, output_dir / "models.py")
    outputs["sql"] = emit_sql(doc, output_dir / "schema.sql")
    outputs["jsonschema"] = emit_jsonschema(doc, output_dir / "schema.json")
    outputs["mcp"] = emit_mcp(doc, output_dir / "mcp_tools.json")
    outputs["typescript"] = emit_typescript(doc, output_dir / "types.ts")
    return outputs
