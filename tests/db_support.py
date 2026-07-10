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

See project memory ``project_test_suite_drops_demo_db``.
"""

from __future__ import annotations

import pytest
import sqlalchemy as sa
from sqlalchemy import NullPool
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from services.api.config import settings

# Registration-only imports — keep in lockstep with ``alembic/env.py`` so that
# ``Base.metadata`` in a test process always matches the migration head.
from services.db import audit_log as _audit_log  # noqa: F401  (registers audit_log)
from services.db import identity as _identity  # noqa: F401  (registers action_identity)
from services.db import models as _models  # noqa: F401  (registers the ontology tables)
from services.engine.procedures import runs as _procedure_runs  # noqa: F401  (registers run tables)
from services.engine.procedures import (  # noqa: F401  (registers schedule_states)
    schedules as _procedure_schedules,
)

_UNREACHABLE = "Postgres not reachable — start docker compose / set DATABASE_URL"

# A DDL lock is held by any live connection to the test DB. Fail loudly rather
# than hang forever if a prior test leaked one.
_LOCK_TIMEOUT = "10s"

# Armed by the autouse ``_arm_schema_reset`` fixture (tests/conftest.py) at the
# start of every test; disarmed by the first ``create_test_engine`` call. Tests
# that build a *second* engine mid-test (to read back rows the fixture engine
# wrote) must not have the schema pulled out from under them.
_schema_reset_armed = True


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
    eng = create_async_engine(settings.test_database_url, poolclass=NullPool)
    try:
        async with eng.connect() as conn:
            await conn.execute(sa.text("SELECT 1"))
    except Exception:
        await eng.dispose()
        pytest.skip(_UNREACHABLE)
    await _reset_public_schema_once(eng)
    return eng
