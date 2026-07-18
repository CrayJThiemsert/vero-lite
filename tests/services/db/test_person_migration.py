"""AC-7 (PLAN-0082 Step 4b / ADR-0033 D5 / SD-I=(b)): the shared `person` table.

The 12th Alembic revision (``0012_person_table``) applies cleanly under the
disposable test-DB pattern and creates the ``person`` table matching the generated
committed ORM (``services/db/person.py``). DB-backed — SKIPS when Postgres is down
(``create_test_engine``), but the check is RUN green on the PR head; a skip is never
counted as satisfaction (AC-7).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import create_async_engine

from services.api.config import settings
from tests.db_support import create_test_engine

_REPO_ROOT = Path(__file__).resolve().parents[3]

_PERSON_COLUMNS_SQL = (
    "SELECT column_name, data_type, is_nullable "
    "FROM information_schema.columns WHERE table_name = 'person'"
)


async def test_person_migration_applies_and_matches_orm() -> None:
    """``alembic upgrade head`` applies the 12th revision cleanly and creates the
    ``person`` table with person_id/name (TEXT) + roles (JSONB), all NOT NULL —
    the shape of the generated committed ORM services/db/person.py."""
    # Resets the test DB's public schema (or skips when Postgres is unreachable),
    # then release the connection so the alembic subprocess gets its own.
    engine = await create_test_engine()
    await engine.dispose()

    # Run every migration (0001..0012) against the disposable test DB. alembic/env.py
    # reads settings.database_url from DATABASE_URL, so point it at the test DB.
    env = {**os.environ, "DATABASE_URL": settings.test_database_url}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"alembic upgrade head failed:\n{result.stderr}"

    verify = create_async_engine(settings.test_database_url, poolclass=NullPool)
    try:
        async with verify.connect() as conn:
            rows = (await conn.execute(sa.text(_PERSON_COLUMNS_SQL))).all()
    finally:
        await verify.dispose()

    columns = {row[0]: (row[1], row[2]) for row in rows}
    assert columns == {
        "person_id": ("text", "NO"),
        "name": ("text", "NO"),
        "roles": ("jsonb", "NO"),
    }
