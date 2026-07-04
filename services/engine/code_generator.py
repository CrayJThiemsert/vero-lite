"""Code generator: emits artifacts per vertical from an ontology YAML.

Implements ADR-008 D5. Each emitter is a pure-Python structured
builder — no Jinja2 (consultation reply Q6: the project is dep-
conservative). Outputs are deterministic given the same input doc,
ordered by ``object_types`` insertion order from the parsed YAML.

Emitters: Pydantic + SQL (PLAN-003 commit 4), JSON Schema + MCP +
TypeScript (commit 5), the SQLAlchemy ORM (PLAN-0031, the 6th), and the
R1 semantic context pack (PLAN-0049 Step 4, the 7th).

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
# SQLAlchemy ORM emitter (PLAN-0031 / Group B B1)
# ---------------------------------------------------------------------------

_ORM_PY_TYPE: dict[str, str] = {
    "string": "str",
    "int": "int",
    "float": "float",
    "bool": "bool",
    "timestamp": "datetime",
    "date": "date",
    "json": "dict[str, Any]",
    "ref": "str",
    "enum": "str",
}

# The ``mapped_column(...)`` type expression per YAML type (``ref``/``json`` handled
# specially). ``enum`` maps to ``Text`` — CHECK validity lives at the Pydantic layer,
# and the parity guard covers types not constraints (matches the prior ORM).
_ORM_COLUMN_TYPE: dict[str, str] = {
    "string": "Text",
    "int": "BigInteger",
    "float": "Double",
    "bool": "Boolean",
    "timestamp": "DateTime(timezone=True)",
    "date": "Date",
    "enum": "Text",
}

# The bare SQLAlchemy import name per YAML type (sans constructor args).
_ORM_SQLALCHEMY_IMPORT: dict[str, str] = {
    "string": "Text",
    "int": "BigInteger",
    "float": "Double",
    "bool": "Boolean",
    "timestamp": "DateTime",
    "date": "Date",
    "enum": "Text",
    "ref": "Text",
}


def _orm_used_imports(object_types: dict[str, Any]) -> tuple[set[str], bool, set[str]]:
    """Return (datetime_imports, needs_any, sqlalchemy_imports) the doc actually uses.

    ``json`` needs ``typing.Any`` (for ``dict[str, Any]``) + ``JSONB`` (from the
    postgresql dialect, emitted separately when ``needs_any``). Each ``ref`` pulls in
    ``ForeignKey`` + ``Index``.
    """
    datetime_set: set[str] = set()
    needs_any = False
    sqlalchemy_set: set[str] = set()
    for obj_def in object_types.values():
        for prop_def in (obj_def.get("properties") or {}).values():
            ptype = prop_def["type"]
            if ptype == "timestamp":
                datetime_set.add("datetime")
            elif ptype == "date":
                datetime_set.add("date")
            elif ptype == "json":
                needs_any = True
                continue  # JSONB import handled separately (needs_any)
            sqlalchemy_set.add(_ORM_SQLALCHEMY_IMPORT[ptype])
            if ptype == "ref":
                sqlalchemy_set.update({"ForeignKey", "Index"})
    return datetime_set, needs_any, sqlalchemy_set


def _orm_column_def(
    prop_name: str,
    prop_def: dict[str, Any],
    primary_key: str,
    object_types: dict[str, Any],
) -> list[str]:
    """One ``mapped_column`` field as a list of source lines (wrapped if > 100 cols,
    mirroring the hand-authored ORM's ruff-clean formatting)."""
    ptype = prop_def["type"]
    py_type = _ORM_PY_TYPE[ptype]
    if ptype == "ref":
        target = prop_def["target"]
        target_pk = object_types[target]["primary_key"]
        col_args = [f'Text, ForeignKey("{_snake(target)}.{target_pk}")']
    elif ptype == "json":
        col_args = ["JSONB"]
    else:
        col_args = [_ORM_COLUMN_TYPE[ptype]]
    if prop_name == primary_key:
        col_args.append("primary_key=True")
        annotation = py_type
    elif prop_def.get("required", False):
        col_args.append("nullable=False")
        annotation = py_type
    else:
        annotation = f"{py_type} | None"
    args = ", ".join(col_args)
    single = f"    {prop_name}: Mapped[{annotation}] = mapped_column({args})"
    if len(single) <= 100:
        return [single]
    return [
        f"    {prop_name}: Mapped[{annotation}] = mapped_column(",
        f"        {args}",
        "    )",
    ]


def _orm_table_args(table: str, ref_cols: list[str]) -> list[str]:
    """The ``__table_args__`` index tuple as source lines (single-line if it fits in
    100 cols, else one ``Index`` per line — matching the hand-authored ORM)."""
    if not ref_cols:
        return []
    entries = [f'Index("idx_{table}_{col}", "{col}")' for col in ref_cols]
    trailing = "," if len(entries) == 1 else ""
    single = f"    __table_args__ = ({', '.join(entries)}{trailing})"
    if len(single) <= 100:
        return [single]
    return ["    __table_args__ = (", *[f"        {entry}," for entry in entries], "    )"]


def emit_orm(doc: dict[str, Any], output_path: Path) -> Path:
    """Write SQLAlchemy 2.0 declarative ORM models for every object_type.

    PLAN-0031 (Group B / B1) — the 6th emitter. Generates the SQLAlchemy ORM from the
    ontology so it is no longer hand-authored; DDL<->ORM parity then holds **by
    construction** (``tests/services/db/test_schema_parity.py``). Bound to the shared
    ``services.db.base.Base``. CHECK constraints are omitted (enum validity at the
    Pydantic layer; the parity guard covers types, not constraints) — schema-equivalent
    to the prior hand-authored ORM. Deterministic, ordered by ``object_types`` insertion
    order, like the other five emitters.
    """
    object_types = doc.get("object_types") or {}
    datetime_imports, needs_any, sqlalchemy_imports = _orm_used_imports(object_types)

    lines: list[str] = [
        '"""Generated SQLAlchemy ORM models from ontology YAML — do not edit by hand."""',
        "",
    ]
    if datetime_imports:
        lines.append(f"from datetime import {', '.join(sorted(datetime_imports))}")
    if needs_any:
        lines.append("from typing import Any")
    if datetime_imports or needs_any:
        lines.append("")
    lines.append(f"from sqlalchemy import {', '.join(sorted(sqlalchemy_imports))}")
    if needs_any:
        lines.append("from sqlalchemy.dialects.postgresql import JSONB")
    lines.append("from sqlalchemy.orm import Mapped, mapped_column")
    lines.append("")
    lines.append("from services.db.base import Base")

    for obj_name, obj_def in object_types.items():
        table = _snake(obj_name)
        pk = obj_def.get("primary_key", "")
        props = obj_def.get("properties") or {}
        lines.append("")
        lines.append("")
        lines.append(f"class {obj_name}(Base):")
        lines.append(f'    __tablename__ = "{table}"')
        ref_cols = [pn for pn, pd in props.items() if pd["type"] == "ref"]
        lines.extend(_orm_table_args(table, ref_cols))
        lines.append("")
        if not props:
            lines.append("    pass")
            continue
        for prop_name, prop_def in props.items():
            lines.extend(_orm_column_def(prop_name, prop_def, pk, object_types))

    body = "\n".join(lines).rstrip() + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(body)
    return output_path


# ---------------------------------------------------------------------------
# Semantic context-pack emitter (PLAN-0049 Step 4 / R1)
# ---------------------------------------------------------------------------

# The R1 "semantic context pack" (PLAN-0049 Step 4; semantic-foundation research
# 2026-07-03, F1/R1): a compact markdown compilation of a vertical's ontology —
# object types, closed enum value-sets, measured-quantity conventions, and
# relationships — for grounding NL-query + anomaly-reasoning (the best-evidenced
# 2026 intervention: +17-23pp, model-independent). It is the 7th emitter, sharing
# the ``(doc, output_path) -> Path`` shape. Deterministic (object_types insertion
# order), pure-Python (no Jinja), gitignored like the other reference artifacts.
#
# R2 DEGRADE PATH (SD-1 carve-out): the convergent semantic-enrichment fields
# (``synonyms`` th/en, ``sample_values``, ``verified_queries``, metric ``grain``)
# are a carved-out ADR-008 grammar amendment (R2, a separate prerequisite ADR),
# absent from the ontology today. This emitter reads them WHEN PRESENT and omits
# their sections when absent — so it ships now on structural + measure content and
# gains the enrichment automatically once R2 lands. No hard dependency on R2.

# Fixed per-vertical token budget (semantic-foundation research: 32K = the
# industry context-ceiling tripwire; the pack target is ~4KB). ``vero-lite
# generate`` does not enforce it (deterministic emit only); the budget is asserted
# by the emitter's tests. Exposed here so the test and the emitter share one source.
CONTEXT_PACK_CHAR_BUDGET = 32_000


def _synonyms_phrase(syn_def: Any) -> str:
    """Render a ``{th, en}`` synonyms mapping as ``th: a, b; en: c, d`` (empty if none)."""
    if not isinstance(syn_def, dict):
        return ""
    bits: list[str] = []
    for lang in ("th", "en"):
        vals = syn_def.get(lang)
        if isinstance(vals, list) and vals:
            bits.append(f"{lang}: {', '.join(str(v) for v in vals)}")
    return "; ".join(bits)


def _doc_has_enrichment(doc: dict[str, Any]) -> bool:
    """True if any object/property carries an ADR-0027 enrichment construct — drives
    the conditional degrade note (which fires only when the ontology declares none)."""
    for obj_def in (doc.get("object_types") or {}).values():
        obj = obj_def or {}
        if obj.get("synonyms") or obj.get("verified_queries"):
            return True
        for prop_def in (obj.get("properties") or {}).values():
            prop = prop_def or {}
            if prop.get("synonyms") or prop.get("sample_values"):
                return True
        for binding in obj.get("quantity_bindings") or []:
            if isinstance(binding, dict) and (binding.get("grain") or binding.get("join_path")):
                return True
    return False


def _context_pack_property_line(prop_name: str, prop_def: dict[str, Any]) -> str:
    parts = [f"- `{prop_name}` ({prop_def.get('type', 'string')})"]
    if prop_def.get("type") == "enum":
        values = prop_def.get("values") or []
        parts.append(f" — closed set: {{{', '.join(str(v) for v in values)}}}")
    if prop_def.get("type") == "ref" and prop_def.get("target"):
        parts.append(f" -> {prop_def['target']}")
    if prop_def.get("required"):
        parts.append(" (required)")
    desc = prop_def.get("description")
    if desc:
        parts.append(f" — {' '.join(str(desc).split())}")
    syn = _synonyms_phrase(prop_def.get("synonyms"))
    if syn:
        parts.append(f" — aka {syn}")
    samples = prop_def.get("sample_values")
    if isinstance(samples, list) and samples:
        parts.append(f" — sample values: {{{', '.join(str(v) for v in samples)}}}")
    return "".join(parts)


def _context_pack_verified_query_lines(obj: dict[str, Any]) -> list[str]:
    """Render an object's ADR-0027 ``verified_queries`` as Q/A lines (empty if none)."""
    queries = obj.get("verified_queries")
    if not isinstance(queries, list) or not queries:
        return []
    lines = ["Verified queries:"]
    for query in queries:
        if isinstance(query, dict):
            question = str(query.get("question", "")).strip()
            answer = str(query.get("answer", "")).strip()
            lines.append(f"- Q: {question} -> A: {answer}")
    return lines


def _context_pack_object_lines(object_types: dict[str, Any]) -> list[str]:
    """The ``## Object types`` body — one block per type (heading + meta + ADR-0027
    synonyms + props + verified queries)."""
    lines: list[str] = []
    for obj_name, obj_def in object_types.items():
        obj = obj_def or {}
        desc = obj.get("description")
        heading = f"### {obj_name}"
        if desc:
            heading += f" — {' '.join(str(desc).split())}"
        lines.append("")
        lines.append(heading)
        meta_bits = []
        if obj.get("primary_key"):
            meta_bits.append(f"primary key `{obj['primary_key']}`")
        if obj.get("title_key"):
            meta_bits.append(f"title `{obj['title_key']}`")
        if meta_bits:
            lines.append(f"{'; '.join(meta_bits).capitalize()}.")
        obj_syn = _synonyms_phrase(obj.get("synonyms"))
        if obj_syn:
            lines.append(f"Synonyms — {obj_syn}.")
        for prop_name, prop_def in (obj.get("properties") or {}).items():
            lines.append(_context_pack_property_line(prop_name, prop_def or {}))
        lines.extend(_context_pack_verified_query_lines(obj))
    return lines


def _context_pack_measure_lines(object_types: dict[str, Any]) -> list[str]:
    """The ``## Measured quantities`` body — the ADR-0021 kind->unit conventions."""
    lines: list[str] = []
    for obj_name, obj_def in object_types.items():
        bindings = (obj_def or {}).get("quantity_bindings") or []
        if not bindings:
            continue
        rendered: list[str] = []
        for binding in bindings:
            if not isinstance(binding, dict):
                continue
            piece = f"{binding.get('kind')}→{binding.get('unit')}"
            if binding.get("grain"):
                piece += f" @{binding['grain']}"
            if binding.get("join_path"):
                piece += f" via {binding['join_path']}"
            rendered.append(piece)
        lines.append(f"- {obj_name}: {', '.join(rendered)} (one unit per kind, ADR-0021)")
    return lines


def emit_context_pack(doc: dict[str, Any], output_path: Path) -> Path:
    """Write the R1 semantic context pack (markdown) to ``output_path``.

    See the module-section header: a compact, LLM-facing compilation of the
    ontology for NL-query / anomaly grounding, degrading gracefully in the
    absence of the carved-out R2 enrichment fields.
    """
    namespace = doc.get("namespace", "")
    version = doc.get("version", 0)
    object_types: dict[str, Any] = doc.get("object_types") or {}
    link_types: dict[str, Any] = doc.get("link_types") or {}

    lines: list[str] = [
        f"# Semantic context pack — {namespace}",
        "",
        f"Ontology revision {version}. Compiled, LLM-facing summary of the "
        f"`{namespace}` ontology — object types, closed enum value-sets, "
        "measured-quantity conventions, and relationships — for grounding "
        "natural-language query and anomaly reasoning. **Enum value-sets are "
        "CLOSED**: a value outside a listed set is out of coverage — refuse, do "
        "not guess.",
        "",
        "## Object types",
    ]
    lines.extend(_context_pack_object_lines(object_types))

    # Measured quantities (the ADR-0021 measured_kind -> unit conventions).
    measure_lines = _context_pack_measure_lines(object_types)
    if measure_lines:
        lines.append("")
        lines.append("## Measured quantities (conventions)")
        lines.extend(measure_lines)

    # Relationships (the link_types).
    if link_types:
        lines.append("")
        lines.append("## Relationships")
        for link_name, link_def in link_types.items():
            link = link_def or {}
            lines.append(
                f"- {link.get('from')} —{link.get('cardinality')}→ {link.get('to')} "
                f"(`{link_name}`)"
            )

    lines.append("")
    lines.append("## Notes")
    if _doc_has_enrichment(doc):
        lines.append(
            "- Semantic enrichment (synonyms th/en, sample values, verified queries, "
            "metric grain) is populated inline above where the ontology declares it "
            "(ADR-0027 R2)."
        )
    else:
        lines.append(
            "- Semantic enrichment (synonyms th/en, sample values, verified queries) is "
            "not yet populated — this ontology declares none of the ADR-0027 R2 fields; "
            "the pack degrades to the structural + measure content available today."
        )

    body = "\n".join(lines).rstrip() + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(body, encoding="utf-8")
    return output_path


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


# Committed-ORM destinations (PLAN-0031 B1 / B1-DP-1, resolved Option B 2026-06-18).
# The SQLAlchemy ORM is a RUNTIME dependency (services/db + alembic import it), so —
# unlike the other five gitignored reference artifacts under verticals/<ns>/generated/ —
# it must be generated to a COMMITTED path. Energy's ORM is services/db/models.py. How a
# 2nd vertical's ORM is laid out (central per-vertical module vs a committed per-vertical
# generated file) is a deferred Rule-of-Three decision — the B1-DP-1 follow-up.
_ORM_COMMITTED_DEST: dict[str, Path] = {"energy": Path("services/db/models.py")}


def generate_all(yaml_path: Path, output_dir: Path) -> dict[str, Path]:
    """Run every emitter against ``yaml_path``; return name -> output path map.

    The ORM emitter writes to the vertical's **committed** ORM destination
    (``_ORM_COMMITTED_DEST``) when one is registered — it is runtime code, not a
    gitignored reference artifact like the other five (falls back to
    ``output_dir / 'orm.py'`` for a vertical with no committed ORM yet).
    """
    doc = load_doc(yaml_path)
    vertical = output_dir.parent.name
    outputs: dict[str, Path] = {}
    outputs["pydantic"] = emit_pydantic(doc, output_dir / "models.py")
    outputs["sql"] = emit_sql(doc, output_dir / "schema.sql")
    outputs["jsonschema"] = emit_jsonschema(doc, output_dir / "schema.json")
    outputs["mcp"] = emit_mcp(doc, output_dir / "mcp_tools.json")
    outputs["typescript"] = emit_typescript(doc, output_dir / "types.ts")
    outputs["orm"] = emit_orm(doc, _ORM_COMMITTED_DEST.get(vertical, output_dir / "orm.py"))
    outputs["context_pack"] = emit_context_pack(doc, output_dir / "context_pack.md")
    return outputs
