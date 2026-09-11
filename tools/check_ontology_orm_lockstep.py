#!/usr/bin/env python3
"""Guard: fleet's DB-backed ontology types and their hand-written tables stay in lockstep.

PLAN-0109 AC-3 — mechanism per SD-C (Code-adopted, open to Cray's countermand).

**What drifts, and why nothing else sees it.** ``fleet_maintenance_v0.yaml`` declares
``RepairCase``, ``RepairCaseQuote`` and ``RepairCaseAcceptedQuote`` so that ``GET /meta``
advertises them and the NL-query translator can name them. Their rows live in
HAND-WRITTEN SQLAlchemy models under ``services/db/`` — fleet has no committed generated
ORM (PLAN-0109 F8), so codegen ties the two sides to nothing. The one ontology hook that
existed before this, ``check-jsonschema``, compares the YAML to its *schema*, never to a
table (F9). So a column added to ``repair_case`` stays invisible to the translator, and a
property renamed in the YAML makes every question about it come back empty — both
silently, with every suite green.

**It compares two REAL artifacts, never a list against itself.** The YAML is parsed from
disk; the column set is read from each mapped model's ``__table__``. The mapping module
(``verticals/fleet_maintenance/data_adapter/db_projection.py``) says only *which* pairs to
compare and *which* columns are deliberately undeclared — never what either set contains.

Offender kinds, each printed with the consequence it prevents (``_WHY``):

* ``undeclared-type`` — a mapped type the YAML does not declare at all.
* ``undeclared-column`` (AC-3 i) — a table column neither declared nor excluded.
* ``column-less-property`` (AC-3 ii) — a declared property with no column behind it.
* ``stale-exclusion`` (AC-3 iii) — an exclusion ``(type, column)`` whose table lacks the
  column, or whose type is not mapped. Keyed per pair on purpose: ``seq``, ``photos``,
  ``note`` and ``attachment`` each exist on ONE of the three tables.
* ``type-incompatible`` / ``unmapped-sql-type`` (AC-3 iv) — see ``_TYPE_MAP``.
* ``excluded-and-declared`` — the exclusion says *never*, the YAML says *queryable*. The
  adapter projects the declared set, so the YAML would win silently while the exclusion
  still read as protection.

**Why a ``Text`` column may declare ``ref`` or ``enum``.** AC-3 (iv)'s map read
``Text→string``, while AC-1 requires ``truck_id`` / ``case_id`` — both ``Text`` — to be
``ref`` properties; a guard built to that letter reddens on AC-1's own declaration
(PLAN-0109, ✎ s294 Step 2). A ref and an enum are strings with more meaning, stored as text.

**Why the mapping module is loaded by PATH.** So a test can point ``ONTOLOGY_GUARD_ROOT``
at a fixture tree whose projection module defines its own tables — the same override
family as ``ALEMBIC_GUARD_ROOT``. On the real tree it imports the real ``services.db``
models, which is the point.

**Missing inputs REFUSE (exit 2); they never pass.** A guard that exits 0 because the
files it compares have gone is the vacuous green CLAUDE.md §8 forbids.

Exit codes: 0 = lockstep · 1 = at least one offender · 2 = refused (inputs missing or
malformed). The last stdout line is always ``VERDICT: <PASS|FAIL|REFUSED> exit=<n>``.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from ruamel.yaml import YAML

if __package__ in (None, ""):  # pragma: no cover - `python tools/check_...py`, not `-m`
    # The real projection module imports `services.db`; a path-script invocation puts
    # `tools/` on sys.path, not the repo root.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_YAML_RELATIVE = Path("verticals") / "fleet_maintenance" / "ontology" / "fleet_maintenance_v0.yaml"
_PROJECTION_RELATIVE = Path("verticals") / "fleet_maintenance" / "data_adapter" / "db_projection.py"

#: SQL column type -> the ontology property types allowed to declare it. The FIRST
#: ``isinstance`` match wins, so a subclass sits before its base where their answers
#: would differ (``Text`` is a ``String``; ``Float`` is a ``Numeric``; ``JSONB`` is a
#: ``JSON``). A column type absent from this table is refused, never guessed.
_TYPE_MAP: tuple[tuple[type[Any], frozenset[str]], ...] = (
    (sa.BigInteger, frozenset({"int"})),
    (sa.Integer, frozenset({"int"})),
    (sa.Boolean, frozenset({"bool"})),
    (sa.DateTime, frozenset({"timestamp"})),
    (sa.Date, frozenset({"date"})),
    (sa.Numeric, frozenset({"float"})),
    (sa.JSON, frozenset({"json"})),
    (sa.String, frozenset({"string", "enum", "ref"})),
)

_WHY: Mapping[str, str] = {
    "undeclared-type": (
        "a mapped type the ontology never declares is compared against nothing, so every "
        "other check on it passes silently"
    ),
    "undeclared-column": (
        "the column is invisible to /meta and the translator, and the adapter's allowlist "
        "will never emit it — declare it in the YAML (a reviewable diff) or give it a "
        "reasoned (type, column) entry in db_projection.EXCLUDED_COLUMNS"
    ),
    "column-less-property": (
        "the ontology advertises a property no row can carry — the translator will filter "
        "on it and every answer comes back confidently empty"
    ),
    "stale-exclusion": (
        "an exclusion naming a column its table does not have hides nothing today, and "
        "would silently cover a future column of that name"
    ),
    "excluded-and-declared": (
        "the adapter projects the DECLARED set, so this column would reach the model while "
        "its exclusion still reads as protection"
    ),
    "type-incompatible": (
        "the translator is told a type the stored value does not have, so its filters "
        "compare the wrong kind of value"
    ),
    "unmapped-sql-type": (
        "this guard cannot say which ontology type the column may declare — it refuses "
        "rather than guesses; extend _TYPE_MAP with a reason"
    ),
}


class InputsRefusedError(Exception):
    """The inputs are missing or malformed — neither a pass nor a fail (exit 2)."""


@dataclass(frozen=True)
class Offender:
    kind: str
    type_name: str
    name: str
    detail: str


@dataclass
class Report:
    """Counts printed as values (§8), the offenders, and each type's allowlist.

    ``allowlists`` is AC-10's allowlist made visible: exactly the property names the
    ontology declares per type — what the adapter projection emits, and therefore what a
    column outside it is excluded from by default.
    """

    types: int = 0
    declared: int = 0
    columns: int = 0
    excluded: int = 0
    offenders: list[Offender] = field(default_factory=list)
    allowlists: dict[str, frozenset[str]] = field(default_factory=dict)


def _allowed_types(sql_type: object) -> frozenset[str] | None:
    for sql_class, allowed in _TYPE_MAP:
        if isinstance(sql_type, sql_class):
            return allowed
    return None


def _table_of(mapped: Any) -> Any:
    """A declarative class carries ``__table__``; a bare ``sa.Table`` is its own table."""
    return getattr(mapped, "__table__", mapped)


def _type_offender(
    type_name: str, table_name: str, prop: str, declared: str, sql_type: object
) -> Offender | None:
    """AC-3 (iv): the declared ontology type must be one the column's SQL type admits."""
    allowed = _allowed_types(sql_type)
    if allowed is None:
        return Offender(
            "unmapped-sql-type",
            type_name,
            prop,
            f"{table_name}.{prop} is {type(sql_type).__name__}",
        )
    if declared not in allowed:
        return Offender(
            "type-incompatible",
            type_name,
            prop,
            f"declared {declared!r}; {type(sql_type).__name__} admits {sorted(allowed)}",
        )
    return None


def _compare_type(
    report: Report,
    type_name: str,
    table: Any,
    block: object,
    exclusions: Mapping[tuple[str, str], str],
) -> None:
    """One mapped type against its declaration: AC-3 (i), (ii), (iv) and the two extras."""
    columns = {str(column.name): column.type for column in table.columns}
    report.columns += len(columns)
    if not isinstance(block, Mapping):
        report.offenders.append(
            Offender(
                "undeclared-type",
                type_name,
                type_name,
                f"table {table.name!r} is mapped but {type_name} is not in object_types",
            )
        )
        return

    raw_properties: Mapping[str, Any] = block.get("properties") or {}
    properties = {
        str(name): str((spec or {}).get("type", "string")) for name, spec in raw_properties.items()
    }
    report.declared += len(properties)
    report.allowlists[type_name] = frozenset(properties)
    excluded = {column for (owner, column) in exclusions if owner == type_name}
    add = report.offenders.append

    for column in sorted(set(columns) - set(properties) - excluded):
        add(
            Offender(
                "undeclared-column",
                type_name,
                column,
                f"{table.name}.{column} is neither declared nor excluded",
            )
        )
    for prop in sorted(set(properties) - set(columns)):
        add(
            Offender(
                "column-less-property", type_name, prop, f"{table.name} has no column {prop!r}"
            )
        )
    for column in sorted(excluded & set(properties)):
        add(
            Offender(
                "excluded-and-declared",
                type_name,
                column,
                f"excluded as {exclusions[(type_name, column)]!r} "
                f"but declared as {properties[column]!r}",
            )
        )
    for prop in sorted(set(properties) & set(columns)):
        offender = _type_offender(type_name, str(table.name), prop, properties[prop], columns[prop])
        if offender is not None:
            add(offender)


def _check_exclusions(
    report: Report, types: Mapping[str, Any], exclusions: Mapping[tuple[str, str], str]
) -> None:
    """AC-3 (iii): every exclusion names a mapped type AND a column that type's table has."""
    for owner, column in sorted(exclusions):
        if owner not in types:
            report.offenders.append(
                Offender(
                    "stale-exclusion",
                    owner,
                    column,
                    f"({owner}, {column}) names a type no table is mapped for",
                )
            )
            continue
        table = _table_of(types[owner])
        if column not in {str(c.name) for c in table.columns}:
            report.offenders.append(
                Offender("stale-exclusion", owner, column, f"{table.name} has no column {column!r}")
            )


def compare(
    doc: Mapping[str, Any],
    types: Mapping[str, Any],
    exclusions: Mapping[tuple[str, str], str],
) -> Report:
    """Compare the parsed ontology to the mapped tables. Pure — no I/O."""
    report = Report(types=len(types), excluded=len(exclusions))
    object_types: Mapping[str, Any] = doc.get("object_types") or {}
    for type_name in sorted(types):
        _compare_type(
            report, type_name, _table_of(types[type_name]), object_types.get(type_name), exclusions
        )
    _check_exclusions(report, types, exclusions)
    return report


def load_inputs(
    root: Path,
) -> tuple[Mapping[str, Any], Mapping[str, Any], Mapping[tuple[str, str], str]]:
    """Read the ontology YAML and load the projection module by path, under ``root``."""
    yaml_path = root / _YAML_RELATIVE
    projection_path = root / _PROJECTION_RELATIVE
    missing = [
        path.relative_to(root).as_posix()
        for path in (yaml_path, projection_path)
        if not path.is_file()
    ]
    if missing:
        raise InputsRefusedError(f"missing input(s) under {root}: {missing}")

    with yaml_path.open(encoding="utf-8") as stream:
        doc = YAML(typ="safe").load(stream)
    if not isinstance(doc, Mapping):
        raise InputsRefusedError(f"{_YAML_RELATIVE.as_posix()} did not parse to a mapping")

    # A name unique to the file loaded, so a fixture tree and the real tree never share a
    # module object (and nothing here is left behind in sys.modules).
    digest = hashlib.sha256(str(projection_path).encode("utf-8")).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(
        f"_ontology_orm_lockstep_projection_{digest}", projection_path
    )
    if spec is None or spec.loader is None:
        raise InputsRefusedError(f"cannot load {_PROJECTION_RELATIVE.as_posix()}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    types = getattr(module, "DB_BACKED_TYPES", None)
    exclusions = getattr(module, "EXCLUDED_COLUMNS", None)
    if not isinstance(types, Mapping) or not isinstance(exclusions, Mapping):
        raise InputsRefusedError(
            f"{_PROJECTION_RELATIVE.as_posix()} must define DB_BACKED_TYPES and "
            "EXCLUDED_COLUMNS as mappings"
        )
    return doc, types, exclusions


def main() -> int:
    root = Path(os.environ.get("ONTOLOGY_GUARD_ROOT") or ".").resolve()
    try:
        doc, types, exclusions = load_inputs(root)
    except InputsRefusedError as exc:
        print(f"ontology-orm-lockstep: REFUSED — {exc}", file=sys.stderr)
        print("ontology-orm-lockstep: VERDICT: REFUSED exit=2")
        return 2

    report = compare(doc, types, exclusions)
    print(
        f"ontology-orm-lockstep: types={report.types} declared={report.declared} "
        f"columns={report.columns} excluded={report.excluded} "
        f"offenders={len(report.offenders)}"
    )
    if not report.offenders:
        print("ontology-orm-lockstep: VERDICT: PASS exit=0")
        return 0

    lines = [
        f"ontology-orm-lockstep: {len(report.offenders)} offender(s) between "
        f"{_YAML_RELATIVE.as_posix()} and the ORM:"
    ]
    for offender in report.offenders:
        lines.append(
            f"  - [{offender.kind}] {offender.type_name}.{offender.name} — {offender.detail}"
        )
        lines.append(f"    why it matters: {_WHY[offender.kind]}")
    print("\n".join(lines), file=sys.stderr)
    print("ontology-orm-lockstep: VERDICT: FAIL exit=1")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
