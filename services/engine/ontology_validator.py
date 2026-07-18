"""L1 + L2 validator for vertical ontology YAML files.

Implements ADR-008 D6:

- L1 (schema validation): JSON Schema draft 2020-12 — conformance to
  ADR-008 D2 grammar. Backed by ``services/engine/ontology_schema.json``
  via the ``jsonschema`` library.
- L2 (semantic validation): cross-reference integrity. Custom Python:
  every ``link_types.<X>.from``/``.to`` resolves to a defined
  ``object_types`` key; every property ``type: ref`` carries a
  ``target:`` that resolves; every property ``type: enum`` carries a
  non-empty ``values:`` list; ``primary_key`` (and ``title_key`` when
  present) resolves to a declared property; ``foreign_key`` parses as
  ``<FromObject>.<from_field> -> <ToObject>.<to_field>`` and both
  endpoints resolve to declared properties.

The validator parses with ruamel.yaml round-trip mode so dict/list
nodes retain source ``line:col`` data via ``.lc``. Error rendering
emits ``<file>:<line>:<col>: <context>: <message>`` per
``errors.OntologyError.render``.

CLI contract (Lesson #7 §3.1 stderr-summary):

- success → ``OK: <N> file(s) valid`` on stderr, returns 0
- failure → one error line per finding + ``<E> error(s) across <M>
  file(s)`` summary on stderr, returns 1

Mirrors ``tools/handoffs/validate_handoff.py:main()`` signature so
cross-tool test harnesses can use a single in-process invocation
pattern (Lesson #7 §3.2).
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from ruamel.yaml import YAML

from services.engine.errors import (
    OntologyError,
    SchemaValidationError,
    SemanticValidationError,
)

_SCHEMA_PATH = Path(__file__).parent / "ontology_schema.json"
_FK_RE = re.compile(
    r"([A-Z][A-Za-z0-9]*)\.([a-z][a-z0-9_]*)\s*->\s*([A-Z][A-Za-z0-9]*)\.([a-z][a-z0-9_]*)"
)

# ADR-0033 D1/D2: the reserved shared-ontology namespaces and their doc homes.
# v0 ships exactly one — `core` at the repo-level shared home. A vertical may not
# claim a reserved token (the reservation is validator/CLI-enforced, not L1).
_SHARED_NAMESPACES: dict[str, Path] = {
    "core": Path(__file__).parents[2] / "ontology" / "core_v0.yaml",
}


def _load_imported_object_types(
    imports: Any,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """ADR-0033 D2: load ``object_types`` for each declared import namespace.
    Returns ``(namespace -> object_types, illegal-tokens)`` — a token that is not
    a known reserved shared namespace (v0: only ``core``) is illegal (fail closed)."""
    imported: dict[str, dict[str, Any]] = {}
    illegal: list[str] = []
    if not isinstance(imports, list):
        return imported, illegal
    for raw in imports:
        token = str(raw)
        path = _SHARED_NAMESPACES.get(token)
        if path is None or not path.is_file():
            illegal.append(token)
            continue
        try:
            shared = _load_yaml(path)
        except Exception:
            illegal.append(token)
            continue
        objs = shared.get("object_types") if isinstance(shared, dict) else None
        imported[token] = objs if isinstance(objs, dict) else {}
    return imported, illegal


def _load_schema() -> dict[str, Any]:
    with _SCHEMA_PATH.open() as fh:
        loaded: dict[str, Any] = json.load(fh)
    return loaded


def _load_yaml(path: Path) -> Any:
    yaml = YAML(typ="rt")
    with path.open() as fh:
        return yaml.load(fh)


def _node_lc(node: Any) -> tuple[int, int]:
    """Return 1-based ``(line, col)`` from a ruamel.yaml CommentedBase node."""
    lc = getattr(node, "lc", None)
    if lc is None:
        return (0, 0)
    return (int(lc.line) + 1, int(lc.col) + 1)


def _value_lc(parent: Any, key: str | int) -> tuple[int, int]:
    """Return ``(line, col)`` of ``parent[key]``'s value when available."""
    lc = getattr(parent, "lc", None)
    if lc is None or not hasattr(lc, "data") or lc.data is None:
        return _node_lc(parent)
    entry = lc.data.get(key)
    if entry is None:
        return _node_lc(parent)
    return (int(entry[2]) + 1, int(entry[3]) + 1)


def _walk_lc(doc: Any, path: Sequence[Any]) -> tuple[int, int]:
    """Walk ``doc`` along ``path`` and return the deepest available line:col."""
    node = doc
    line, col = _node_lc(node)
    for key in path:
        try:
            child = node[key]
        except (KeyError, IndexError, TypeError):
            break
        node_lc = _node_lc(child)
        if node_lc != (0, 0):
            line, col = node_lc
        else:
            line, col = _value_lc(node, key)
        node = child
    return line, col


def _ctx_from_path(path: list[Any]) -> tuple[str, str]:
    """Derive ``(object_type, property)`` context from a JSON Schema error path."""
    object_type = ""
    prop = ""
    if path and path[0] == "object_types" and len(path) >= 2:
        object_type = str(path[1])
        if len(path) >= 4 and path[2] == "properties":
            prop = str(path[3])
    elif path and path[0] == "link_types" and len(path) >= 2:
        object_type = str(path[1])
        if len(path) >= 3:
            prop = str(path[2])
    return object_type, prop


def _validate_l1(file: str, doc: Any) -> list[OntologyError]:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    findings: list[OntologyError] = []
    for err in validator.iter_errors(doc):
        path = list(err.absolute_path)
        line, col = _walk_lc(doc, path)
        object_type, prop = _ctx_from_path(path)
        findings.append(
            SchemaValidationError(
                file=file,
                object_type=object_type,
                property=prop,
                yaml_line=line,
                yaml_col=col,
                message=err.message,
            )
        )
    return findings


def _props_of(obj_def: Any) -> dict[str, Any]:
    props = obj_def.get("properties") if isinstance(obj_def, dict) else None
    return props if isinstance(props, dict) else {}


def _check_link_endpoints(
    file: str, link_name: str, link_def: dict[str, Any], object_types: dict[str, Any]
) -> list[OntologyError]:
    line, col = _node_lc(link_def)
    findings: list[OntologyError] = []
    for end in ("from", "to"):
        target = link_def.get(end)
        if isinstance(target, str) and target and target not in object_types:
            findings.append(
                SemanticValidationError(
                    file=file,
                    object_type=link_name,
                    property=end,
                    yaml_line=line,
                    yaml_col=col,
                    message=(
                        f"link_types.{link_name}.{end} = {target!r} does not "
                        f"resolve to a defined object_type"
                    ),
                )
            )
    return findings


def _check_foreign_key(
    file: str, link_name: str, link_def: dict[str, Any], object_types: dict[str, Any]
) -> list[OntologyError]:
    fk = link_def.get("foreign_key")
    if not isinstance(fk, str) or not fk:
        return []
    line, col = _node_lc(link_def)
    match = _FK_RE.fullmatch(fk)
    if match is None:
        return [
            SemanticValidationError(
                file=file,
                object_type=link_name,
                property="foreign_key",
                yaml_line=line,
                yaml_col=col,
                message=(
                    f"foreign_key {fk!r} does not match "
                    f"'<FromObject>.<from_field> -> <ToObject>.<to_field>'"
                ),
            )
        ]
    from_obj, from_field, to_obj, to_field = match.groups()
    findings: list[OntologyError] = []
    for obj, field, side in (
        (from_obj, from_field, "from"),
        (to_obj, to_field, "to"),
    ):
        if obj not in object_types:
            findings.append(
                SemanticValidationError(
                    file=file,
                    object_type=link_name,
                    property="foreign_key",
                    yaml_line=line,
                    yaml_col=col,
                    message=f"foreign_key {side}-side object_type {obj!r} undefined",
                )
            )
            continue
        if field not in _props_of(object_types[obj]):
            findings.append(
                SemanticValidationError(
                    file=file,
                    object_type=link_name,
                    property="foreign_key",
                    yaml_line=line,
                    yaml_col=col,
                    message=(f"foreign_key {side}-side {obj}.{field!r} not declared in properties"),
                )
            )
    return findings


def _check_object_type(
    file: str,
    obj_name: str,
    obj_def: dict[str, Any],
    object_types: dict[str, Any],
    imported: dict[str, dict[str, Any]],
) -> list[OntologyError]:
    findings: list[OntologyError] = []
    props = _props_of(obj_def)
    line, col = _node_lc(obj_def)
    for key in ("primary_key", "title_key"):
        value = obj_def.get(key)
        if isinstance(value, str) and value and value not in props:
            findings.append(
                SemanticValidationError(
                    file=file,
                    object_type=obj_name,
                    property=key,
                    yaml_line=line,
                    yaml_col=col,
                    message=f"{key} {value!r} not declared in properties of {obj_name}",
                )
            )
    for prop_name, prop_def in props.items():
        findings.extend(
            _check_property(file, obj_name, prop_name, prop_def, object_types, imported)
        )
    findings.extend(_check_quantity_bindings(file, obj_name, obj_def))
    findings.extend(_check_enrichment(file, obj_name, obj_def, object_types))
    return findings


def _check_ref_target(
    file: str,
    obj_name: str,
    prop_name: str,
    target: str,
    object_types: dict[str, Any],
    imported: dict[str, dict[str, Any]],
    line: int,
    col: int,
) -> list[OntologyError]:
    """Resolve a ``ref`` target. ADR-0033 D2: a qualified ``<ns>.<Type>`` resolves
    against an imported shared doc (the ns must be declared in ``imports:`` and the
    type must exist there); an unqualified target resolves within the local doc.
    Fail closed here — never the shipped codegen ``KeyError``."""
    if "." in target:
        ns, type_name = target.split(".", 1)
        if ns not in imported:
            msg = f"ref target {target!r} references namespace {ns!r} not declared in imports:"
        elif type_name not in imported[ns]:
            msg = (
                f"ref target {target!r} does not resolve to an object_type in the "
                f"{ns!r} shared ontology"
            )
        else:
            return []
    elif target in object_types:
        return []
    else:
        msg = f"ref target {target!r} does not resolve to a defined object_type"
    return [
        SemanticValidationError(
            file=file,
            object_type=obj_name,
            property=prop_name,
            yaml_line=line,
            yaml_col=col,
            message=msg,
        )
    ]


def _check_property(
    file: str,
    obj_name: str,
    prop_name: str,
    prop_def: Any,
    object_types: dict[str, Any],
    imported: dict[str, dict[str, Any]],
) -> list[OntologyError]:
    if not isinstance(prop_def, dict):
        return []
    findings: list[OntologyError] = []
    pl, pc = _node_lc(prop_def)
    ptype = prop_def.get("type")
    if ptype == "ref":
        target = prop_def.get("target")
        if isinstance(target, str) and target:
            findings.extend(
                _check_ref_target(file, obj_name, prop_name, target, object_types, imported, pl, pc)
            )
    if ptype == "enum":
        values = prop_def.get("values")
        if not isinstance(values, list) or not values:
            findings.append(
                SemanticValidationError(
                    file=file,
                    object_type=obj_name,
                    property=prop_name,
                    yaml_line=pl,
                    yaml_col=pc,
                    message=f"enum property {prop_name!r} requires non-empty values list",
                )
            )
    if ptype == "set":
        findings.extend(_check_set_constraints(file, obj_name, prop_name, prop_def, pl, pc))
    return findings


def _check_set_constraints(
    file: str,
    obj_name: str,
    prop_name: str,
    prop_def: dict[str, Any],
    line: int,
    col: int,
) -> list[OntologyError]:
    """ADR-0033 D3 (L2): a ``set`` property's collection-cardinality constraints
    (``min_length`` / ``max_length``, when present) must be non-negative integers,
    and ``max_length`` must not fall below ``min_length``. The ``items`` scalar
    element type + its presence are enforced at L1; the emitter maps ``set`` ->
    ``frozenset[<item>]`` with the ``min_length`` bound (ADR-0033 D3)."""
    constraints = prop_def.get("constraints")
    if not isinstance(constraints, dict):
        return []
    findings: list[OntologyError] = []
    bounds: dict[str, int] = {}
    for key in ("min_length", "max_length"):
        val = constraints.get(key)
        if val is None:
            continue
        if not isinstance(val, int) or isinstance(val, bool) or val < 0:
            findings.append(
                SemanticValidationError(
                    file=file,
                    object_type=obj_name,
                    property=prop_name,
                    yaml_line=line,
                    yaml_col=col,
                    message=(
                        f"set property {prop_name!r} constraint {key} must be a "
                        f"non-negative integer, got {val!r}"
                    ),
                )
            )
        else:
            bounds[key] = val
    if (
        "min_length" in bounds
        and "max_length" in bounds
        and bounds["max_length"] < bounds["min_length"]
    ):
        findings.append(
            SemanticValidationError(
                file=file,
                object_type=obj_name,
                property=prop_name,
                yaml_line=line,
                yaml_col=col,
                message=(
                    f"set property {prop_name!r} max_length {bounds['max_length']} "
                    f"is below min_length {bounds['min_length']}"
                ),
            )
        )
    return findings


def _check_quantity_bindings(
    file: str, obj_name: str, obj_def: dict[str, Any]
) -> list[OntologyError]:
    """ADR-0021 (D6 L2): each ``quantity_bindings`` kind must be a value of the
    type's ``measured_kind`` enum, and no kind may be bound more than once."""
    bindings = obj_def.get("quantity_bindings")
    if not isinstance(bindings, list):
        return []
    line, col = _node_lc(obj_def)
    props = _props_of(obj_def)
    mk = props.get("measured_kind")
    enum_values = mk.get("values") if isinstance(mk, dict) else None
    valid_kinds = {str(v) for v in enum_values} if isinstance(enum_values, list) else set()
    findings: list[OntologyError] = []
    seen: set[str] = set()
    for binding in bindings:
        if not isinstance(binding, dict):
            continue
        kind = str(binding.get("kind", ""))
        if valid_kinds and kind not in valid_kinds:
            findings.append(
                SemanticValidationError(
                    file=file,
                    object_type=obj_name,
                    property="quantity_bindings",
                    yaml_line=line,
                    yaml_col=col,
                    message=(
                        f"quantity_bindings kind {kind!r} is not a value of the "
                        f"measured_kind enum {sorted(valid_kinds)}"
                    ),
                )
            )
        if kind in seen:
            findings.append(
                SemanticValidationError(
                    file=file,
                    object_type=obj_name,
                    property="quantity_bindings",
                    yaml_line=line,
                    yaml_col=col,
                    message=f"quantity_bindings binds kind {kind!r} more than once",
                )
            )
        seen.add(kind)
    return findings


def _check_synonyms(
    file: str, obj_name: str, prop_name: str | None, syn_def: dict[str, Any]
) -> list[OntologyError]:
    """ADR-0027 R2 (SD-2) L2: reject a synonym repeated within a language list."""
    findings: list[OntologyError] = []
    line, col = _node_lc(syn_def)
    owner = prop_name if prop_name is not None else obj_name
    for lang in ("th", "en"):
        values = syn_def.get(lang)
        if not isinstance(values, list):
            continue
        seen: set[str] = set()
        for raw in values:
            value = str(raw)
            if value in seen:
                findings.append(
                    SemanticValidationError(
                        file=file,
                        object_type=obj_name,
                        property=prop_name or "synonyms",
                        yaml_line=line,
                        yaml_col=col,
                        message=(f"synonyms.{lang} for {owner!r} lists {value!r} more than once"),
                    )
                )
            seen.add(value)
    return findings


def _check_sample_values(
    file: str, obj_name: str, prop_name: str, prop_def: dict[str, Any]
) -> list[OntologyError]:
    """ADR-0027 R2 (SD-3 / SD-C) L2: no duplicate sample; and when the property is
    also an enum, every ``sample_values`` entry must be a declared enum ``value``."""
    samples = prop_def.get("sample_values")
    if not isinstance(samples, list):
        return []
    findings: list[OntologyError] = []
    line, col = _node_lc(prop_def)
    enum_values: set[str] | None = None
    if prop_def.get("type") == "enum":
        vals = prop_def.get("values")
        if isinstance(vals, list):
            enum_values = {str(v) for v in vals}
    seen: set[str] = set()
    for raw in samples:
        value = str(raw)
        if value in seen:
            findings.append(
                SemanticValidationError(
                    file=file,
                    object_type=obj_name,
                    property=prop_name,
                    yaml_line=line,
                    yaml_col=col,
                    message=(f"sample_values for {prop_name!r} lists {value!r} more than once"),
                )
            )
        seen.add(value)
        if enum_values is not None and value not in enum_values:
            findings.append(
                SemanticValidationError(
                    file=file,
                    object_type=obj_name,
                    property=prop_name,
                    yaml_line=line,
                    yaml_col=col,
                    message=(
                        f"sample_value {value!r} for enum property {prop_name!r} is not "
                        f"a declared enum value {sorted(enum_values)}"
                    ),
                )
            )
    return findings


def _check_verified_queries(
    file: str, obj_name: str, obj_def: dict[str, Any]
) -> list[OntologyError]:
    """ADR-0027 R2 (SD-4) L2: ``question``/``answer`` must be non-blank and no
    ``question`` may repeat. v1 is the least-coupling ``{question, answer}`` NL
    pair, so there is no referent check into the NL-query IR."""
    queries = obj_def.get("verified_queries")
    if not isinstance(queries, list):
        return []
    findings: list[OntologyError] = []
    line, col = _node_lc(obj_def)
    seen: set[str] = set()
    for entry in queries:
        if not isinstance(entry, dict):
            continue
        question = str(entry.get("question", "")).strip()
        answer = str(entry.get("answer", "")).strip()
        if not question or not answer:
            findings.append(
                SemanticValidationError(
                    file=file,
                    object_type=obj_name,
                    property="verified_queries",
                    yaml_line=line,
                    yaml_col=col,
                    message=(f"verified_queries for {obj_name!r} has a blank question/answer"),
                )
            )
            continue
        if question in seen:
            findings.append(
                SemanticValidationError(
                    file=file,
                    object_type=obj_name,
                    property="verified_queries",
                    yaml_line=line,
                    yaml_col=col,
                    message=(f"verified_queries for {obj_name!r} repeats question {question!r}"),
                )
            )
        seen.add(question)
    return findings


def _check_quantity_binding_paths(
    file: str, obj_name: str, obj_def: dict[str, Any], object_types: dict[str, Any]
) -> list[OntologyError]:
    """ADR-0027 R2 (SD-5) L2: a quantity-binding ``join_path`` (when present) must
    parse as ``<Obj>.<field> -> <Obj>.<field>`` with both endpoints resolving to a
    declared object_type + property; ``grain`` (when present) must be non-blank."""
    bindings = obj_def.get("quantity_bindings")
    if not isinstance(bindings, list):
        return []
    findings: list[OntologyError] = []
    line, col = _node_lc(obj_def)
    for binding in bindings:
        if not isinstance(binding, dict):
            continue
        kind = str(binding.get("kind", ""))
        grain = binding.get("grain")
        if grain is not None and not str(grain).strip():
            findings.append(
                SemanticValidationError(
                    file=file,
                    object_type=obj_name,
                    property="quantity_bindings",
                    yaml_line=line,
                    yaml_col=col,
                    message=f"quantity_bindings grain for kind {kind!r} is blank",
                )
            )
        join_path = binding.get("join_path")
        if not isinstance(join_path, str) or not join_path:
            continue
        match = _FK_RE.fullmatch(join_path)
        if match is None:
            findings.append(
                SemanticValidationError(
                    file=file,
                    object_type=obj_name,
                    property="quantity_bindings",
                    yaml_line=line,
                    yaml_col=col,
                    message=(
                        f"quantity_bindings join_path {join_path!r} for kind {kind!r} "
                        f"does not match '<FromObject>.<from_field> -> <ToObject>.<to_field>'"
                    ),
                )
            )
            continue
        from_obj, from_field, to_obj, to_field = match.groups()
        for endpoint_obj, endpoint_field, side in (
            (from_obj, from_field, "from"),
            (to_obj, to_field, "to"),
        ):
            if endpoint_obj not in object_types:
                findings.append(
                    SemanticValidationError(
                        file=file,
                        object_type=obj_name,
                        property="quantity_bindings",
                        yaml_line=line,
                        yaml_col=col,
                        message=(f"join_path {side}-side object_type {endpoint_obj!r} undefined"),
                    )
                )
            elif endpoint_field not in _props_of(object_types[endpoint_obj]):
                findings.append(
                    SemanticValidationError(
                        file=file,
                        object_type=obj_name,
                        property="quantity_bindings",
                        yaml_line=line,
                        yaml_col=col,
                        message=(
                            f"join_path {side}-side {endpoint_obj}.{endpoint_field!r} "
                            f"not declared in properties"
                        ),
                    )
                )
    return findings


def _check_enrichment(
    file: str, obj_name: str, obj_def: dict[str, Any], object_types: dict[str, Any]
) -> list[OntologyError]:
    """ADR-0027 R2 (PLAN-0050 Step 3) L2 orchestrator: run each enrichment-construct
    consistency pass. Each pass no-ops when its construct is absent (the D2 invariant)."""
    findings: list[OntologyError] = []
    obj_syn = obj_def.get("synonyms")
    if isinstance(obj_syn, dict):
        findings.extend(_check_synonyms(file, obj_name, None, obj_syn))
    findings.extend(_check_verified_queries(file, obj_name, obj_def))
    for prop_name, prop_def in _props_of(obj_def).items():
        if not isinstance(prop_def, dict):
            continue
        prop_syn = prop_def.get("synonyms")
        if isinstance(prop_syn, dict):
            findings.extend(_check_synonyms(file, obj_name, str(prop_name), prop_syn))
        findings.extend(_check_sample_values(file, obj_name, str(prop_name), prop_def))
    findings.extend(_check_quantity_binding_paths(file, obj_name, obj_def, object_types))
    return findings


def _check_imports(file: str, doc: Any, illegal_imports: list[str]) -> list[OntologyError]:
    """ADR-0033 D1/D2 L2: each ``imports:`` token must be a known reserved shared
    namespace (v0: only ``core``); and a vertical doc may not claim the reserved
    ``core`` namespace — only the shared home declares it."""
    findings: list[OntologyError] = []
    if illegal_imports:
        line, col = _walk_lc(doc, ["imports"])
        for token in illegal_imports:
            findings.append(
                SemanticValidationError(
                    file=file,
                    object_type="",
                    property="imports",
                    yaml_line=line,
                    yaml_col=col,
                    message=(
                        f"imports token {token!r} is not a known shared namespace "
                        f"(ADR-0033 v0: only 'core')"
                    ),
                )
            )
    if doc.get("namespace") == "core" and "verticals" in Path(file).parts:
        line, col = _walk_lc(doc, ["namespace"])
        findings.append(
            SemanticValidationError(
                file=file,
                object_type="",
                property="namespace",
                yaml_line=line,
                yaml_col=col,
                message=(
                    "namespace 'core' is reserved for the shared ontology "
                    "(ADR-0033 D1); a vertical may not claim it"
                ),
            )
        )
    return findings


def _validate_l2(file: str, doc: Any) -> list[OntologyError]:
    findings: list[OntologyError] = []
    raw_objects = doc.get("object_types")
    raw_links = doc.get("link_types")
    object_types: dict[str, Any] = raw_objects if isinstance(raw_objects, dict) else {}
    link_types: dict[str, Any] = raw_links if isinstance(raw_links, dict) else {}

    # ADR-0033 D1/D2: resolve declared imports + guard the reserved `core` namespace.
    imported, illegal_imports = _load_imported_object_types(doc.get("imports"))
    findings.extend(_check_imports(file, doc, illegal_imports))

    for link_name, link_def in link_types.items():
        if not isinstance(link_def, dict):
            continue
        findings.extend(_check_link_endpoints(file, link_name, link_def, object_types))
        findings.extend(_check_foreign_key(file, link_name, link_def, object_types))
    for obj_name, obj_def in object_types.items():
        if not isinstance(obj_def, dict):
            continue
        findings.extend(_check_object_type(file, obj_name, obj_def, object_types, imported))
    return findings


def validate_file(path: Path) -> list[OntologyError]:
    """Full L1 + L2 validation of one ontology YAML."""
    try:
        doc = _load_yaml(path)
    except Exception as exc:
        return [
            SchemaValidationError(
                file=str(path),
                object_type="",
                property="",
                yaml_line=0,
                yaml_col=0,
                message=f"YAML parse failed: {exc}",
            )
        ]
    if not isinstance(doc, dict):
        return [
            SchemaValidationError(
                file=str(path),
                object_type="",
                property="",
                yaml_line=0,
                yaml_col=0,
                message="top-level YAML must be a mapping",
            )
        ]
    findings = _validate_l1(str(path), doc)
    findings.extend(_validate_l2(str(path), doc))
    return findings


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry. Returns 0 on success, 1 on validation errors."""
    args = list(argv) if argv is not None else sys.argv[1:]
    if not args:
        sys.stderr.write("usage: ontology_validator <file.yaml> [<file2.yaml> ...]\n")
        return 1
    total_errors = 0
    failed_files = 0
    for arg in args:
        path = Path(arg)
        findings = validate_file(path)
        if findings:
            failed_files += 1
            total_errors += len(findings)
            for err in findings:
                sys.stderr.write(err.render() + "\n")
    if total_errors:
        sys.stderr.write(f"{total_errors} error(s) across {failed_files} file(s)\n")
        return 1
    sys.stderr.write(f"OK: {len(args)} file(s) valid\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
