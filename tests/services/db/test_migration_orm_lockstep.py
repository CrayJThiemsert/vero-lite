"""The migration<->ORM lockstep, proven locally instead of only in CI.

CI has run ``alembic upgrade head`` + ``alembic check`` since PLAN-0049 Step 5.
Nothing offline did — so PR #965's unregistered-module bug survived a full green
3528-test suite and was caught only after a push, costing a CI round.

This module closes that specific gap. It drives the **real migration chain** into
a **real Postgres** and asks alembic whether the resulting schema still matches
``Base.metadata`` — the same question CI asks, one step earlier.

**What this catches that the rest of the suite structurally cannot.** Every other
DB test builds its schema with ``Base.metadata.create_all``, which reads the ORM
directly. The ORM is therefore correct *by construction* in those tests, and the
migration chain — the only path production takes — is never walked. A column added
to an ORM class with no migration written is invisible to all of them.

**Why a test rather than a pre-commit hook** (Cray, typed, 2026-07-29, after the
cost was measured at 1.75 s): a hook would run ``upgrade head`` against the
one-per-checkout test database, which collides with a concurrent ``pytest``
process' ``DROP SCHEMA public CASCADE`` — and running the suite in the background
while continuing to edit is a normal working pattern here. Inside the suite,
pytest serialises it for free. The suite is run before every push, so the catch
still lands before CI either way.

**Disposable DB only.** ``DATABASE_URL`` is overridden to the worktree-scoped test
database for the subprocesses, so the dev/demo DB is never migrated by a test run
— migrating it is a host-state change requiring an explicit go (CLAUDE.md §8).
Skips when Postgres is unreachable, like every other DB-backed test; a skip is
never counted as satisfaction.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from services.api.config import settings
from tests.db_support import create_test_engine

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _alembic(*args: str) -> subprocess.CompletedProcess[str]:
    """Run alembic against the DISPOSABLE test database."""
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=_REPO_ROOT,
        env={**os.environ, "DATABASE_URL": settings.test_database_url},
        capture_output=True,
        text=True,
        check=False,
    )


async def test_the_migration_chain_still_matches_the_orm() -> None:
    """``alembic check`` after ``upgrade head`` — CI's lockstep guard, run locally.

    A failure here means one of two things, and the alembic output says which:

    * an ORM change shipped without its migration (add the migration), or
    * a model module is missing from ``alembic/env.py`` (the #965 shape — the
      pre-commit guard ``tools/check_alembic_model_registration.py`` normally
      catches that one first, offline and without a database).

    The engine fixture is what resets the schema and skips when Postgres is down;
    the migration then builds the whole chain from empty.
    """
    engine = await create_test_engine()
    await engine.dispose()

    upgrade = _alembic("upgrade", "head")
    assert upgrade.returncode == 0, f"alembic upgrade head failed:\n{upgrade.stderr}"

    check = _alembic("check")
    assert check.returncode == 0, (
        "the migration chain has drifted from the ORM — autogenerate would emit "
        "operations that no migration in the chain performs:\n"
        f"{check.stdout}{check.stderr}"
    )
