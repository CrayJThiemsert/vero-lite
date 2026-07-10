"""The two invariants that make ``tests/db_support.py`` hermetic.

Regression cover for an order-dependent failure: ``pytest tests/services/db``
alone left ``action_identity`` standing (no module in that subset imports
``services.db.identity``, so ``Base.metadata`` omitted it and ``drop_all`` never
touched it), and the next ``alembic upgrade head`` died on a DuplicateTableError.
The full suite hid it — ``tests/api`` imports the router that pulls the model in.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import sqlalchemy as sa

from tests.db_support import arm_schema_reset, create_test_engine

_REPO_ROOT = Path(__file__).resolve().parents[3]

# The migration head's full table set. Must track the registration imports in
# ``alembic/env.py`` — a table missing here is a table ``create_all`` silently
# skips and ``drop_all`` silently leaves behind.
_HEAD_TABLES = {
    "action_identity",
    "alert",
    "alert_event_link",
    "asset",
    "audit_log",
    "operational_event",
    "pipeline_runs",
    "recommended_action",
    "schedule_states",
    "site",
    "step_results",
}

_TABLES_IN_PUBLIC = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"


def test_importing_db_support_registers_every_orm_table() -> None:
    """A fresh interpreter that imports only ``tests.db_support`` sees the full
    ``Base.metadata`` — no test process can get a partial one by import accident."""
    probe = (
        "import json;"
        "import tests.db_support;"
        "from services.db.base import Base;"
        "print(json.dumps(sorted(Base.metadata.tables)))"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert set(json.loads(result.stdout)) == _HEAD_TABLES


async def test_create_test_engine_wipes_residue_from_an_aborted_run() -> None:
    """A table an aborted run left behind — one ``Base.metadata`` knows nothing
    about, so ``drop_all`` cannot reach it — is gone by the next test's engine."""
    engine = await create_test_engine()
    async with engine.begin() as conn:
        await conn.execute(sa.text("CREATE TABLE residue (id TEXT PRIMARY KEY)"))
        await conn.execute(sa.text("INSERT INTO residue VALUES ('leaked')"))
    await engine.dispose()

    arm_schema_reset()  # what the autouse fixture does at the start of each test
    next_engine = await create_test_engine()
    try:
        async with next_engine.connect() as conn:
            present = {row[0] for row in await conn.execute(sa.text(_TABLES_IN_PUBLIC))}
        assert present == set(), f"residue survived into the next test: {sorted(present)}"
    finally:
        await next_engine.dispose()
