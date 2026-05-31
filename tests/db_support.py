"""Shared helpers for DB-backed tests — target a disposable test DB.

The DB test layer calls ``Base.metadata.create_all`` then ``drop_all`` (+
``DROP TABLE alembic_version``) on teardown, so it must own its database
outright. These helpers bind every DB test to ``settings.test_database_url``
(a sibling ``<db>_test``, e.g. ``vero_lite_test``) and create it on first
use — the dev/demo DB pointed at by ``DATABASE_URL`` is never touched.

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

_UNREACHABLE = "Postgres not reachable — start docker compose / set DATABASE_URL"


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


async def create_test_engine() -> AsyncEngine:
    """Ensure the test DB exists and return a NullPool engine bound to it.

    Skips the calling test when Postgres is unreachable (mirrors the prior
    ``SELECT 1`` probe), so the suite stays green without Docker. A fresh
    NullPool engine per test avoids reusing connections across
    pytest-asyncio's per-test event loops (PLAN-0005 R4).
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
    return eng
