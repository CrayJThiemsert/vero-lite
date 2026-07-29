#!/usr/bin/env python3
"""Guard: every ORM module must be imported by ``alembic/env.py``.

**The failure this exists to prevent** (measured, PR #965). A new hand-authored
table shipped with its migration, its ORM, and two green test suites — but
``alembic/env.py`` never imported the ORM module. ``Base.metadata`` therefore did
not know the table existed, and CI's ``alembic check`` reported that autogenerate
wanted to **DROP** it. Left unnoticed, the next generated migration would have
done exactly that.

**Why the test suite cannot catch it.** DB-backed tests build their schema with
``Base.metadata.create_all``, and ``Base.metadata`` only knows the models that the
*importing test module* pulled in. Both new suites imported the model class
directly, so the table existed for them. Nothing offline ever traverses
``env.py``, which is the only path production migrations take. 3528 passing tests
did not touch it.

**Why not just run ``alembic check`` locally.** It needs a live database at
``DATABASE_URL``. A pre-commit hook that fails whenever Postgres is down (or in a
worktree, which has no ``.env``) is a hook developers learn to bypass, and a
bypassed guard protects nothing. So the two are split by what they can prove
offline: this guard is static, deterministic and needs no database — it catches
the *unregistered module* class; CI's ``alembic check`` keeps catching
column-level drift, which genuinely requires a database to see.

**Why AST rather than grep.** ``services/engine/code_generator.py`` contains the
text ``__tablename__`` inside the source template it emits. A grep counts it as a
model module and demands env.py import a code generator. Parsing finds
``__tablename__`` only where it is really a class attribute.

Exit codes: 0 = every ORM module is registered; 1 = at least one is not.

``ALEMBIC_GUARD_ROOT`` overrides the repo root for tests (mirrors the
``STATUS_SIZE_PATH`` override-family pattern).
"""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

#: Where ORM modules may live. Scoped rather than repo-wide so a fixture or a
#: scratch script that happens to declare a table cannot fail the build.
_MODEL_ROOTS = ("services",)

_ENV_REL = Path("alembic") / "env.py"


def _defines_a_table(source: str) -> bool:
    """True if this module declares a real ``__tablename__`` CLASS attribute.

    Text inside a string template does not count — see the module docstring.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # A file that does not parse is not this guard's problem; ruff and mypy
        # both fail first and say so far better than a table check could.
        return False

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for statement in node.body:
            targets: list[ast.expr] = []
            if isinstance(statement, ast.Assign):
                targets = list(statement.targets)
            elif isinstance(statement, ast.AnnAssign):
                targets = [statement.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id == "__tablename__":
                    return True
    return False


def find_model_modules(root: Path) -> set[str]:
    """Every dotted module path under the model roots that declares a table."""
    found: set[str] = set()
    for model_root in _MODEL_ROOTS:
        for path in (root / model_root).rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            if _defines_a_table(path.read_text(encoding="utf-8")):
                found.add(path.relative_to(root).with_suffix("").as_posix().replace("/", "."))
    return found


def find_registered_modules(env_source: str) -> set[str]:
    """Every dotted module path ``alembic/env.py`` imports.

    Both spellings are resolved, because env.py uses both:
    ``from services.db import repair_case`` -> ``services.db.repair_case``, and
    ``import services.db.repair_case`` -> the same. The ``from X import Y`` form
    is ambiguous in the abstract (``Y`` could be a name, not a module), which is
    harmless here: a name that is not a module simply never matches a discovered
    model module.
    """
    registered: set[str] = set()
    tree = ast.parse(env_source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                registered.add(f"{node.module}.{alias.name}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                registered.add(alias.name)
    return registered


def main() -> int:
    root = Path(os.environ.get("ALEMBIC_GUARD_ROOT") or ".").resolve()
    env_path = root / _ENV_REL
    if not env_path.exists():
        print(
            f"alembic-model-registration: {_ENV_REL} not found under {root} — " "nothing to check.",
            file=sys.stderr,
        )
        return 0

    models = find_model_modules(root)
    registered = find_registered_modules(env_path.read_text(encoding="utf-8"))
    missing = sorted(models - registered)

    if missing:
        print(
            "alembic-model-registration: these ORM modules declare a table but are "
            f"NOT imported by {_ENV_REL}:\n"
            + "".join(f"  - {name}\n" for name in missing)
            + "\nBase.metadata will not know their tables exist, so `alembic check` "
            "fails in CI and the next autogenerated migration proposes DROPPING "
            "them. Add an import to alembic/env.py:\n"
            + "".join(
                f"  from {name.rsplit('.', 1)[0]} import {name.rsplit('.', 1)[1]}"
                f"  # noqa: F401\n"
                for name in missing
            ),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
