"""PLAN-0096 Step 3 / AC-4: the 14th revision — the quote-evidence tables.

Same shape as the 0013 test. The column assertion is exact, and ``amount_thb`` is
checked as ``numeric`` specifically: money on an authority threshold is Decimal end
to end, and a ``double precision`` column here would silently reintroduce binary
float on the figure the DOA ladder routes on.

DB-backed — SKIPS when Postgres is down; a skip is never satisfaction.
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
    "SELECT table_name, column_name, data_type, is_nullable "
    "FROM information_schema.columns "
    "WHERE table_name IN ('repair_case_quote', 'repair_case_justification')"
)
_FK_SQL = (
    "SELECT tc.table_name FROM information_schema.table_constraints tc "
    "WHERE tc.constraint_type = 'FOREIGN KEY' "
    "AND tc.table_name IN ('repair_case_quote', 'repair_case_justification')"
)


async def test_evidence_migration_applies_and_matches_the_orm() -> None:
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
            rows = (await conn.execute(sa.text(_COLUMNS_SQL))).all()
            fks = {r[0] for r in (await conn.execute(sa.text(_FK_SQL))).all()}
    finally:
        await verify.dispose()

    quote = {r[1]: (r[2], r[3]) for r in rows if r[0] == "repair_case_quote"}
    justification = {r[1]: (r[2], r[3]) for r in rows if r[0] == "repair_case_justification"}

    assert quote == {
        "quote_id": ("text", "NO"),
        "case_id": ("text", "NO"),
        "vendor": ("text", "NO"),
        # NUMERIC, not double precision — the money invariant, asserted.
        "amount_thb": ("numeric", "NO"),
        "entered_by": ("text", "NO"),
        "entered_at": ("timestamp with time zone", "NO"),
        "note": ("text", "YES"),
        "attachment": ("jsonb", "YES"),
    }
    assert justification == {
        "justification_id": ("text", "NO"),
        "case_id": ("text", "NO"),
        "vendor": ("text", "NO"),
        "reason": ("text", "NO"),
        "entered_by": ("text", "NO"),
        "entered_at": ("timestamp with time zone", "NO"),
    }
    # Both hang off repair_case: evidence for a case that does not exist is evidence
    # that counts toward nothing and appears in no UI.
    assert fks == {"repair_case_quote", "repair_case_justification"}
