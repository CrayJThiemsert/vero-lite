"""AC-5 (ADR-0035 D7(v)) — a new table cannot silently opt out of the tenant key.

D7(v) verbatim: *"add a set-equality guard test asserting every ``__tablename__``
model carries ``tenant_id`` (a new table cannot silently opt out)"*.

**Why this shape and not the obvious one.** Two simpler guards were considered and
REJECTED, both recorded in PLAN-0101 AC-5 as counterexamples:

* A hardcoded list of the 21 tables passes today and still passes when a 22nd ships
  without the column — vacuous.
* A walk over ``Base.registry.mappers`` alone misses a model module that no test
  imports, because ``Base.metadata`` is populated purely by import side effect —
  the exact failure class that shipped twice already (``action_identity``, then
  PR #965) and that ``tools/check_alembic_model_registration.py`` exists for.

The pairing closes both holes. Set **A** is every table declared ON DISK, found by
AST so that a ``__tablename__`` appearing inside a string template does not count —
``code_generator.emit_orm`` builds one with an f-string, and a text search would
count it as a 22nd table that exists nowhere. Set **B** is every table the process
actually mapped. ``A == B`` means a new un-imported model file breaks the guard by
growing A; the per-table column assertion means a new imported table without the
column breaks it too.
"""

from __future__ import annotations

import ast
from pathlib import Path

from services.db.base import Base

# Registration-only import: populates Base.metadata with every ORM module, the same
# way alembic/env.py does. Without it set B would describe only what this test file
# happened to import, which is the vacuity the A==B pairing exists to prevent.
import tests.db_support  # noqa: F401  isort:skip

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SERVICES = _REPO_ROOT / "services"


def _declared_tablenames(source: str) -> set[str]:
    """Every ``__tablename__`` declared as a real CLASS attribute in ``source``.

    The ``tools/check_alembic_model_registration.py:_defines_a_table`` idiom, widened
    from "does this module declare one" to "which names does it declare". Only a
    ``ClassDef`` body counts, and only a literal string value — so the emitter's
    ``lines.append(f'    __tablename__ = "{table}"')`` contributes nothing, because
    that name lives inside a function, inside a string.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # A file that does not parse is ruff's and mypy's problem; both fail first
        # and say so far better than a table census could.
        return set()

    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for statement in node.body:
            targets: list[ast.expr] = []
            value: ast.expr | None = None
            if isinstance(statement, ast.Assign):
                targets, value = list(statement.targets), statement.value
            elif isinstance(statement, ast.AnnAssign):
                targets, value = [statement.target], statement.value
            for target in targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == "__tablename__"
                    and isinstance(value, ast.Constant)
                    and isinstance(value.value, str)
                ):
                    names.add(value.value)
    return names


def _tables_on_disk() -> set[str]:
    """Set A — every table declared under ``services/``, found without importing."""
    found: set[str] = set()
    for path in _SERVICES.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        found |= _declared_tablenames(path.read_text(encoding="utf-8"))
    return found


def _tables_mapped() -> set[str]:
    """Set B — every table this process actually mapped onto ``Base``."""
    return {str(mapper.class_.__tablename__) for mapper in Base.registry.mappers}


def test_every_table_on_disk_is_a_table_the_process_mapped() -> None:
    """A == B. A model module nobody imports grows A and reddens here.

    This half is what makes the column assertion below non-vacuous: without it, a
    new table could carry no tenant key and escape simply by never being imported.
    """
    on_disk, mapped = _tables_on_disk(), _tables_mapped()
    assert on_disk == mapped, (
        "the tables declared on disk and the tables mapped by this process differ — "
        f"declared but not mapped (missing registration): {sorted(on_disk - mapped)}; "
        f"mapped but not declared: {sorted(mapped - on_disk)}"
    )


def test_every_mapped_table_carries_the_tenant_key() -> None:
    """Every mapped table has ``tenant_id``: TEXT, NOT NULL, no server default.

    The ``server_default is None`` clause is not decoration. PLAN-0101 SD-1 ruled (b)
    — a Python-side default — and Step 1.4 MEASURED that ``alembic check`` cannot see
    a ``server_default`` drifting back in. Between this and the migration oracle,
    nothing else in the repo would notice.
    """
    offenders: list[str] = []
    for mapper in sorted(Base.registry.mappers, key=lambda m: str(m.class_.__tablename__)):
        table = mapper.local_table
        name = str(mapper.class_.__tablename__)
        column = table.columns.get("tenant_id") if table is not None else None
        if column is None:
            offenders.append(f"{name}: no tenant_id column")
            continue
        if column.nullable:
            offenders.append(f"{name}: tenant_id is nullable")
        if str(column.type) != "TEXT":
            offenders.append(f"{name}: tenant_id is {column.type}, expected TEXT")
        if column.server_default is not None:
            offenders.append(f"{name}: tenant_id carries a server_default (SD-1 forbids it)")
    assert offenders == [], "tables failing the tenant-key contract:\n  " + "\n  ".join(offenders)


def test_the_ast_walk_ignores_a_tablename_inside_a_string() -> None:
    """The emitter's f-string must not be counted — asserted, not assumed.

    ``code_generator.emit_orm`` writes ``__tablename__`` into generated source as
    string content. A text search would read that as a table declaration and inflate
    set A by one phantom, so the guard would redden forever and get deleted. This
    pins the property that makes the AST walk the right tool.
    """
    source = """
def emit(table: str) -> list[str]:
    lines = []
    lines.append(f'    __tablename__ = "{table}"')
    return lines


class Real:
    __tablename__ = "genuinely_declared"
"""
    assert _declared_tablenames(source) == {"genuinely_declared"}
