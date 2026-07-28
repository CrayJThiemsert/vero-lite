"""PLAN-0096 Step 2 / AC-3: the ``repair_case`` table's 13th Alembic revision.

Same shape as ``test_person_migration.py`` (the 12th): ``alembic upgrade head``
applies cleanly under the disposable test-DB pattern and produces the table the
hand-authored ORM ``services/db/repair_case.py`` declares. DB-backed — SKIPS when
Postgres is down, and a skip is never counted as satisfaction.

The column assertion is exact rather than a spot-check for a specific reason: this
table is the first one PLAN-0096 adds, and the PLAN's Out of Scope had (as a ⊕
drafter addition) forbidden migrations outright before Cray ratified this one. A
migration that drifts from its ORM is the failure that would justify that caution,
so the guard against it is the strict form.
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

_COLUMNS_SQL = (
    "SELECT column_name, data_type, is_nullable "
    "FROM information_schema.columns WHERE table_name = 'repair_case'"
)
_INDEX_SQL = "SELECT indexname FROM pg_indexes WHERE tablename = 'repair_case'"


async def test_repair_case_migration_applies_and_matches_orm() -> None:
    """The 13th revision creates ``repair_case`` with the ORM's exact column set."""
    engine = await create_test_engine()
    await engine.dispose()

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
            columns = {
                row[0]: (row[1], row[2])
                for row in (await conn.execute(sa.text(_COLUMNS_SQL))).all()
            }
            indexes = {row[0] for row in (await conn.execute(sa.text(_INDEX_SQL))).all()}
    finally:
        await verify.dispose()

    assert columns == {
        "case_id": ("text", "NO"),
        "truck_id": ("text", "NO"),
        "opened_by": ("text", "NO"),
        "opened_at": ("timestamp with time zone", "NO"),
        # the ONLY nullable column: AC-3 requires a case openable with the truck
        # pick alone, so free text must never be mandatory.
        "description": ("text", "YES"),
        "status": ("text", "NO"),
        "photos": ("jsonb", "NO"),
    }
    assert {"idx_repair_case_truck_id", "idx_repair_case_status"} <= indexes
