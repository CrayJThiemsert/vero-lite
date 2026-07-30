"""The ORM-registration guard — the offline half of the migration lockstep.

Two drifts of the same class, both of which shipped, are pinned here:

* **env.py** (PR #965) — a new ORM module was never imported, so ``Base.metadata``
  did not know its table existed and autogenerate wanted to DROP it. 3528 passing
  tests missed it: ``create_all`` knows only what the TEST module imported, and
  nothing offline traverses ``env.py``.
* **db_support.py** — #965's fix patched env.py only, leaving the test-side list
  drifted for a whole PR. ``alembic check`` can never see this one: it compares
  the database against the metadata *env.py* builds, and does not know
  db_support.py exists.

The second drift also defeated the pre-existing guard for it,
``test_db_hermeticity.py``, whose ``_HEAD_TABLES`` was hand-maintained and was
missing the same table — two wrong lists agreeing. This guard DERIVES the model
set from source, so only one side of that comparison can be wrong at a time.

Beyond catching both, these cases pin the guard against the way it would become
useless in the other direction: crying wolf on the code generator, whose
``__tablename__`` lives inside an emitted string template.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tools.check_alembic_model_registration import (
    _defines_a_table,
    find_model_modules,
    find_registered_modules,
    main,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]

_MODEL = """
from services.db.base import Base


class Widget(Base):
    __tablename__ = "widget"
"""

_TEMPLATE_ONLY = '''
TEMPLATE = """
class {name}(Base):
    __tablename__ = "{table}"
"""
'''


def _make_tree(
    root: Path,
    *,
    env_imports: str,
    modules: dict[str, str],
    support_imports: str | None = None,
) -> None:
    """A repo-shaped tree: both registration sites plus services/db modules.

    ``support_imports`` defaults to ``env_imports`` because most cases vary one
    site at a time, and a fixture that silently left the second site empty would
    make every case fail for the wrong reason.
    """
    (root / "alembic").mkdir(parents=True)
    (root / "alembic" / "env.py").write_text(env_imports, encoding="utf-8")
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "db_support.py").write_text(
        env_imports if support_imports is None else support_imports, encoding="utf-8"
    )
    for relative, source in modules.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")


# --------------------------------------------------------------------------- #
# Detection
# --------------------------------------------------------------------------- #


def test_a_class_attribute_counts_but_a_string_template_does_not() -> None:
    """The distinction that forced AST over grep.

    ``services/engine/code_generator.py`` emits ORM source, so the token appears
    in its text. A grep-based guard would demand ``env.py`` import a code
    generator — a false alarm that teaches people to ignore the guard.
    """
    assert _defines_a_table(_MODEL)
    assert not _defines_a_table(_TEMPLATE_ONLY)


def test_an_annotated_tablename_is_still_a_table() -> None:
    """``__tablename__: str = "x"`` is the same declaration with a type on it —
    a guard that only understood plain assignment would miss half the styles the
    codebase could legitimately use."""
    assert _defines_a_table('class Widget(Base):\n    __tablename__: str = "widget"\n')


def test_a_file_that_does_not_parse_is_not_reported_as_a_model() -> None:
    """Broken syntax belongs to ruff and mypy, which say so far more usefully.
    This guard staying quiet keeps one failure from producing three confusing
    error messages."""
    assert not _defines_a_table("class Widget(Base:\n")


def test_both_import_spellings_register_a_module() -> None:
    """``env.py`` uses ``from services.db import x``; ``import services.db.x``
    is equally valid. A guard that understood only one would demand a redundant
    import for a table that is already registered."""
    registered = find_registered_modules(
        "from services.db import repair_case as _rc\nimport services.db.person\n"
    )
    assert "services.db.repair_case" in registered
    assert "services.db.person" in registered


# --------------------------------------------------------------------------- #
# The guard's verdict
# --------------------------------------------------------------------------- #


def test_an_unregistered_model_module_fails_the_guard(tmp_path: Path, monkeypatch) -> None:
    """PR #965's bug, reproduced: the ORM exists, ``env.py`` does not import it.

    This is the case that must go RED. If it ever passes, the guard is decorative
    and the next new table can silently become a DROP.
    """
    _make_tree(
        tmp_path,
        env_imports="from services.db import person as _person\n",
        modules={
            "services/db/person.py": _MODEL,
            "services/db/repair_case_task.py": _MODEL,
        },
    )
    monkeypatch.setenv("ALEMBIC_GUARD_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    assert main() == 1


def test_a_fully_registered_tree_passes(tmp_path: Path, monkeypatch) -> None:
    """The same tree with the import added — the guard must not be a permanent
    red, or it would be disabled within a week."""
    _make_tree(
        tmp_path,
        env_imports=(
            "from services.db import person as _person\n"
            "from services.db import repair_case_task as _rct\n"
        ),
        modules={
            "services/db/person.py": _MODEL,
            "services/db/repair_case_task.py": _MODEL,
        },
    )
    monkeypatch.setenv("ALEMBIC_GUARD_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    assert main() == 0


def test_a_module_registered_in_env_but_not_db_support_still_fails(
    tmp_path: Path, monkeypatch
) -> None:
    """The SECOND drift, reproduced — and the one nothing else can see.

    This is exactly what PR #965's fix left behind: env.py was patched, the
    test-side list was not, and the gap survived a whole PR. ``alembic check``
    would never reveal it — it compares the database against the metadata *env.py*
    builds and does not know db_support.py exists. If this case ever passes, the
    guard covers only half the class it was widened to cover.
    """
    _make_tree(
        tmp_path,
        env_imports=(
            "from services.db import person as _person\n"
            "from services.db import repair_case_task as _rct\n"
        ),
        support_imports="from services.db import person as _person\n",
        modules={
            "services/db/person.py": _MODEL,
            "services/db/repair_case_task.py": _MODEL,
        },
    )
    monkeypatch.setenv("ALEMBIC_GUARD_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    assert main() == 1


def test_a_module_with_no_table_is_never_demanded(tmp_path: Path, monkeypatch) -> None:
    """Only table-declaring modules are required in ``env.py``. Demanding more
    would make the guard a nuisance that gets silenced."""
    _make_tree(
        tmp_path,
        env_imports="from services.db import person as _person\n",
        modules={
            "services/db/person.py": _MODEL,
            "services/db/helpers.py": "def helper() -> int:\n    return 1\n",
            "services/engine/code_generator.py": _TEMPLATE_ONLY,
        },
    )
    monkeypatch.setenv("ALEMBIC_GUARD_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    assert main() == 0


# --------------------------------------------------------------------------- #
# Against the real repository
# --------------------------------------------------------------------------- #


def test_this_repository_passes_its_own_guard() -> None:
    """Run for real, as the pre-commit hook does. A guard green only on fixtures
    proves nothing about the tree it protects."""
    result = subprocess.run(
        [sys.executable, "tools/check_alembic_model_registration.py"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_both_real_registration_sites_list_every_model() -> None:
    """The two real files, checked directly rather than through ``main``.

    A failure here names WHICH site drifted, which ``main``'s exit code alone
    cannot — and the two fail in completely different ways (a CI ``alembic check``
    failure versus a DuplicateTableError in a later test run).
    """
    models = find_model_modules(_REPO_ROOT)
    for relative in (Path("alembic") / "env.py", Path("tests") / "db_support.py"):
        registered = find_registered_modules((_REPO_ROOT / relative).read_text(encoding="utf-8"))
        assert not (
            models - registered
        ), f"{relative.as_posix()} is missing: {sorted(models - registered)}"


def test_every_real_model_module_is_discovered() -> None:
    """The discovery half, against the real tree.

    Pinned as a set rather than a count: a count passes when one module is added
    and another silently drops out of range, which is the drift this whole guard
    family exists to refuse.
    """
    assert find_model_modules(_REPO_ROOT) == {
        "services.db.audit_log",
        "services.db.identity",
        "services.db.models",
        "services.db.person",
        "services.db.pm_import",
        "services.db.repair_case",
        # PLAN-0096 Step 8: the close-out record + the repair-order number that the
        # month-end export keys on (alembic 0017).
        "services.db.repair_case_closeout",
        "services.db.repair_case_evidence",
        # PLAN-0096 Step 8 item 3: which governed run decided which repair case —
        # the table AC-9's approval columns are filled from (alembic 0020).
        "services.db.repair_case_run_link",
        "services.db.repair_case_task",
        "services.engine.procedures.runs",
        "services.engine.procedures.schedules",
    }
