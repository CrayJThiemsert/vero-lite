"""Shared helpers for DB-backed tests — target a disposable test DB.

The DB test layer calls ``Base.metadata.create_all`` then ``drop_all`` (+
``DROP TABLE alembic_version``) on teardown, so it must own its database
outright. These helpers bind every DB test to ``settings.test_database_url``
(a sibling ``<db>_test``, e.g. ``vero_lite_test``) and create it on first
use — the dev/demo DB pointed at by ``DATABASE_URL`` is never touched.

Two invariants keep that ownership hermetic:

* **Complete metadata.** ``Base.metadata`` is populated by *import side effect*,
  so it only describes the ORM modules a given test process happened to import.
  ``tests/services/db`` never imports ``services.db.identity`` (only
  ``services/api/routers/actions.py`` does), so ``action_identity`` was missing
  from the metadata: ``create_all`` skipped it and ``drop_all`` left it standing
  for the next ``alembic upgrade head`` to trip over with a DuplicateTableError.
  The import block below mirrors ``alembic/env.py`` so every test process sees
  the full table set.
* **A clean schema per test.** ``create_all`` is ``checkfirst=True``, so a table
  (or a row) surviving an aborted run is silently adopted rather than recreated.
  ``create_test_engine`` therefore drops and recreates the ``public`` schema on
  its first call within each test — no residue can cross a test boundary, and
  fixed ``run_id`` literals (``hl-ap``, ``run-rej``, …) cannot collide with rows
  left behind by an earlier test or an earlier run.

* **One test database per checkout.** That schema reset is a ``DROP SCHEMA public
  CASCADE``: two ``pytest`` processes sharing one test DB would wipe each other's
  tables mid-test. Several git worktrees of this repo live side by side under
  ``.claude/worktrees/`` and are worked on concurrently, so the derived
  ``<db>_test`` is scoped per checkout — ``vero_lite_test_<8-hex of repo root>``.
  An explicit ``TEST_DATABASE_URL`` (env or ``.env``) always wins verbatim, so CI
  — which sets it — is unaffected.

See project memory ``project_test_suite_drops_demo_db``.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy import NullPool
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from services.api.config import _derive_test_database_url, settings
from services.db import audit_log as _audit_log  # noqa: F401  (registers audit_log)
from services.db import identity as _identity  # noqa: F401  (registers action_identity)
from services.db import models as _models  # noqa: F401  (registers the ontology tables)
from services.db import person as _person  # noqa: F401  (registers the shared `person` table)
from services.db import pm_import as _pm_import  # noqa: F401  (registers pm_import_row)
from services.db import repair_case as _repair_case  # noqa: F401  (registers repair_case)
from services.db import (  # noqa: F401  (registers the close-out + order-number tables)
    repair_case_closeout as _repair_case_closeout,
)
from services.db import (  # noqa: F401  (registers the quote-evidence tables)
    repair_case_evidence as _repair_case_evidence,
)
from services.db import (  # noqa: F401  (registers repair_case_run_link)
    repair_case_run_link as _repair_case_run_link,
)
from services.db import (  # noqa: F401  (registers repair_case_task_event)
    repair_case_task as _repair_case_task,
)

# Registration-only imports — keep in lockstep with ``alembic/env.py`` so that
# ``Base.metadata`` in a test process always matches the migration head.
# ENFORCED, no longer a convention: ``tools/check_alembic_model_registration.py``
# (pre-commit) fails if a module declaring a ``__tablename__`` is missing from
# either list. It was added after this block silently drifted from env.py for a
# whole PR — the second time this exact class of gap shipped, the first being the
# ``action_identity`` omission described above.
# (isort places the next line inside the block above; it is NOT a registration-only
# import — it is the declarative base itself, used by `drop_all_bounded`.)
from services.db.base import Base
from services.engine.procedures import runs as _procedure_runs  # noqa: F401  (registers run tables)
from services.engine.procedures import (  # noqa: F401  (registers schedule_states)
    schedules as _procedure_schedules,
)
from tests import db_guard

_UNREACHABLE = "Postgres not reachable — start docker compose / set DATABASE_URL"

#: Node ids of tests that got a LIVE engine — the population PLAN-0107 AC-12's floor
#: counts. Written here rather than inferred from pytest reports because this function
#: is the single chokepoint: ``git ls-files | grep conftest`` returns two files, and the
#: only other route into an engine (``tests/api/conftest.py:199``) calls straight into
#: it. A test that skipped never reaches the recording line, so membership means
#: "executed against a real database", not "asked for one".
EXECUTED_DB_TESTS: set[str] = set()


def _record_executed_db_test() -> None:
    """Note that the CURRENT test reached a live engine (AC-12's counted population).

    ``PYTEST_CURRENT_TEST`` is pytest's own per-test env var; its value carries a
    trailing phase marker (``… (call)``) which is stripped so setup and call phases
    of one test count once. Absent outside a pytest run, in which case nothing is
    recorded and the floor check simply sees no population.
    """
    current = os.environ.get("PYTEST_CURRENT_TEST", "")
    if current:
        EXECUTED_DB_TESTS.add(current.split(" (")[0])


# A DDL lock is held by any live connection to the test DB. Fail loudly rather
# than hang forever if a prior test leaked one.
_LOCK_TIMEOUT = "10s"

# The TEARDOWN bound (PLAN-0115 Step 3 / SD-1). Deliberately longer than the setup
# bound above: teardown runs after a test's own work, so a legitimately busy table can
# take longer to quiesce than a fresh schema reset. Rationale for bounding at all —
# and the 67-minute incident behind it — is on `drop_all_bounded`.
_TEARDOWN_LOCK_TIMEOUT = "20s"

# This file lives at <repo root>/tests/db_support.py.
_REPO_ROOT = Path(__file__).resolve().parent.parent


def worktree_scoped_test_url(test_database_url: str, repo_root: Path) -> str:
    """Append a short digest of ``repo_root`` to the test DB name.

    Deterministic per checkout, so a worktree always reuses its own database
    rather than accumulating a new one per run. The digest keeps the identifier
    well inside Postgres' 63-character limit (``vero_lite_test_a1b2c3d4``).
    """
    digest = hashlib.sha256(str(repo_root).encode()).hexdigest()[:8]
    url = make_url(test_database_url)
    # render_as_string(hide_password=False): str(URL) masks the password as
    # "***", which would corrupt the connection string.
    return url.set(database=f"{url.database}_{digest}").render_as_string(hide_password=False)


#: This process's role, validated at import. A malformed value raises here rather than
#: resolving to the unsuffixed name — a typo must never silently mean "no isolation".
_ROLE: str | None = db_guard.role_from_env()


def _isolate_test_database_per_worktree() -> None:
    """Scope the test DB to this checkout, then to this process's ROLE.

    ``Settings._fill_test_database_url`` leaves ``test_database_url`` at the
    derived ``<db>_test`` when nothing supplied one. Comparing against that
    derivation is how we tell "nobody chose a test DB" from "someone did":
    an explicit ``TEST_DATABASE_URL`` (env var or ``.env``) is honoured verbatim,
    which is what keeps CI — where it is set — on the plain ``vero_lite_test``.

    **The role suffix applies to whichever name resolved** — derived or explicit
    (PLAN-0120 SD-1, ruled). A dev box whose ``.env`` pins ``TEST_DATABASE_URL``
    would otherwise leave the goal gate sharing this session's database with no
    signal at all, which is the defect ADR-0018 D8 exists to close. CI pins the URL
    but never runs the Stop hook, so its plain ``vero_lite_test`` is untouched either
    way. With ``VERO_TEST_DB_ROLE`` unset — the default everywhere — this function
    behaves exactly as it did before.
    """
    if settings.test_database_url == _derive_test_database_url(settings.database_url):
        settings.test_database_url = worktree_scoped_test_url(
            settings.test_database_url, _REPO_ROOT
        )
    if _ROLE:
        settings.test_database_url = db_guard.role_suffixed(settings.test_database_url, _ROLE)


_isolate_test_database_per_worktree()

# Armed by the autouse ``_arm_schema_reset`` fixture (tests/conftest.py) at the
# start of every test; disarmed by the first ``create_test_engine`` call. Tests
# that build a *second* engine mid-test (to read back rows the fixture engine
# wrote) must not have the schema pulled out from under them.
_schema_reset_armed = True

#: The one guard for this pytest process. Constructed on first use and acquired lazily
#: at the chokepoint (SD-4), so a session that runs no DB test never opens a Postgres
#: connection and the battery's own pytest children never become false second arrivers.
_SESSION_GUARD: db_guard.TestDbGuard | None = None


def session_guard() -> db_guard.TestDbGuard:
    """This process's guard, created on first ask. Not yet acquired."""
    global _SESSION_GUARD
    if _SESSION_GUARD is None:
        _SESSION_GUARD = db_guard.TestDbGuard(settings.test_database_url, _ROLE)
    return _SESSION_GUARD


def _assert_not_dev_db() -> None:
    """Refuse to run if the test URL resolves to the dev/demo database.

    The suite drops its schema on teardown; sharing a (host, port, database)
    with ``DATABASE_URL`` would wipe the dev/demo DB. This guard turns a
    misconfigured ``TEST_DATABASE_URL`` into a loud failure instead of silent
    data loss.
    """
    dev = make_url(settings.database_url)
    test = make_url(settings.test_database_url)
    if (dev.host, dev.port, dev.database) == (test.host, test.port, test.database):
        raise RuntimeError(
            "test_database_url must differ from database_url — the test suite "
            f"drops its schema on teardown (both resolve to {dev.database!r} on "
            f"{dev.host}:{dev.port}). Set TEST_DATABASE_URL to a disposable DB."
        )


async def ensure_test_database() -> None:
    """Create the disposable test database if it does not exist (idempotent).

    ``CREATE DATABASE`` cannot run inside a transaction, so connect to the
    ``postgres`` maintenance DB in AUTOCOMMIT and guard on ``pg_database``.
    Raises if the Postgres server is unreachable (callers translate that into
    a skip).
    """
    _assert_not_dev_db()
    test_url = make_url(settings.test_database_url)
    db_name = test_url.database
    admin_url = test_url.set(database="postgres")
    admin = create_async_engine(admin_url, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    try:
        async with admin.connect() as conn:
            exists = await conn.scalar(
                sa.text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            )
            if not exists:
                try:
                    await conn.execute(sa.text(f'CREATE DATABASE "{db_name}"'))
                except ProgrammingError:
                    # Raced with a concurrent creator — the DB now exists.
                    pass
    finally:
        await admin.dispose()


def arm_schema_reset() -> None:
    """Re-arm the once-per-test schema reset. Called by an autouse fixture."""
    global _schema_reset_armed
    _schema_reset_armed = True


async def _reset_public_schema_once(engine: AsyncEngine) -> None:
    """Drop and recreate ``public`` — but only on the first engine of a test.

    ``DROP SCHEMA ... CASCADE`` removes *every* object, not merely the tables
    this process happens to have registered on ``Base.metadata``: tables created
    by an ``alembic upgrade head`` subprocess, ``alembic_version``, and any rows
    an aborted run left behind.
    """
    global _schema_reset_armed
    if not _schema_reset_armed:
        return
    _schema_reset_armed = False
    async with engine.begin() as conn:
        await conn.execute(sa.text(f"SET LOCAL lock_timeout = '{_LOCK_TIMEOUT}'"))
        await conn.execute(sa.text("DROP SCHEMA public CASCADE"))
        await conn.execute(sa.text("CREATE SCHEMA public"))


async def drop_all_bounded(conn: AsyncConnection, timeout: str = _TEARDOWN_LOCK_TIMEOUT) -> None:
    """``Base.metadata.drop_all``, but it reddens instead of hanging.

    🔴 **The bound does not PREVENT the failure — it changes its KIND.** ``drop_all``
    needs ``ACCESS EXCLUSIVE`` on every table, and a session another test left
    ``idle in transaction`` holds a conflicting lock. Unbounded, ``drop_all`` then waits
    **forever**: measured s253 as a **67-minute hang** whose head of queue was one
    un-rolled-back session, with a second pytest process queued behind it — and the test
    DB is scoped per *checkout*, not per process, so that second pytest shares the first
    one's database by design. A failure that never reddens is a failure the test system
    cannot see. With the bound it becomes a loud, ordinary test failure in 20 seconds
    that names the operation.

    The leaked session is the root cause, and a missing ``rollback()`` fixes *that one
    test*. This helper bounds the whole **class**, because leaks cannot be prevented in
    the general case — which is why it ships with the guard in
    ``tests/tools/test_teardown_bound_guard.py`` and neither is severable (PLAN-0115
    SD-1, ruled (b)).
    """
    await conn.execute(sa.text(f"SET lock_timeout = '{timeout}'"))
    await conn.run_sync(Base.metadata.drop_all)


async def create_test_engine() -> AsyncEngine:
    """Ensure the test DB exists, reset its schema, return a NullPool engine.

    Skips the calling test when Postgres is unreachable (mirrors the prior
    ``SELECT 1`` probe), so the suite stays green without Docker. A fresh
    NullPool engine per test avoids reusing connections across
    pytest-asyncio's per-test event loops (PLAN-0005 R4).

    The ``public`` schema is dropped and recreated on the first call within each
    test, so every DB test starts from an empty database regardless of what the
    previous test — or a previous, aborted ``pytest`` process — left behind.
    """
    # Guard outside the try: a misconfigured test URL (== dev DB) must fail
    # loudly, never be swallowed into a skip.
    _assert_not_dev_db()
    try:
        await ensure_test_database()
    except Exception:
        pytest.skip(_UNREACHABLE)

    # SD-4: acquisition is LAZY and lives HERE, so an engine without a held guard is
    # impossible by construction.
    #
    # 🔴 Every ``pytest.exit`` below sits OUTSIDE the ``except Exception`` blocks, and
    # that placement is load-bearing rather than stylistic: ``_pytest.outcomes.Exit``
    # is a subclass of ``Exception`` and a bare ``except Exception`` swallows it
    # (measured, s277). One inside would turn every guard refusal into a skip — a mass
    # skip that reads as a pass on the summary line, which is precisely the fail-open
    # this guard exists to prevent.
    guard = session_guard()
    if guard.acquire() == db_guard.CONTENDED:
        pytest.exit(guard.contention_reason(), returncode=db_guard.CONTENDED_EXIT)

    eng = create_async_engine(settings.test_database_url, poolclass=NullPool)
    holder_alive: int | None = None
    try:
        async with eng.connect() as conn:
            if guard.state == db_guard.ACQUIRED:
                # One query, two facts: Postgres answers AND the holder backend is
                # still there. Replaces the old ``SELECT 1`` at zero extra cost.
                holder_alive = await conn.scalar(
                    sa.text(db_guard.LIVENESS_SQL), {"holder_pid": guard.holder_pid}
                )
            else:
                await conn.execute(sa.text("SELECT 1"))
    except Exception:
        await eng.dispose()
        pytest.skip(_UNREACHABLE)

    # Reached only when the database ANSWERS. So a guard that could not be established
    # is not "Postgres is down" — it is the LOST family, the one combination that must
    # never pass quietly (§4.3).
    if guard.state == db_guard.ABSENT:
        # Same LOST family (§4.3): the guard could not be established but the database
        # can be reached — the one combination that must never pass quietly. Restated as
        # LOST so the printed token names the family rather than the symptom; the reason
        # below keeps the ABSENT cause verbatim.
        absent_error = guard.error
        guard.state = db_guard.LOST
        await eng.dispose()
        pytest.exit(
            guard.lost_reason(
                f"the guard could not be established ({absent_error}) yet the database answers"
            ),
            returncode=db_guard.CONTENDED_EXIT,
        )
    if guard.state == db_guard.ACQUIRED and not holder_alive:
        guard.state = db_guard.LOST
        await eng.dispose()
        pytest.exit(
            guard.lost_reason(
                f"holder backend pid={guard.holder_pid} is gone from pg_stat_activity"
            ),
            returncode=db_guard.CONTENDED_EXIT,
        )

    await _reset_public_schema_once(eng)
    # AC-12: recorded AFTER both skip paths above, so the count is of tests that
    # actually reached a live database — never of tests that merely wanted one.
    _record_executed_db_test()
    return eng
