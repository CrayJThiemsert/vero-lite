"""Alembic migration environment — async engine (PLAN-0005 §6.6).

The database URL comes from ``services.api.config.settings``
(DATABASE_URL / .env); the target metadata is
``services.db.base.Base.metadata``.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from services.api.config import settings
from services.db import audit_log as _audit_log  # noqa: F401  (registers audit_log)
from services.db import identity as _identity  # noqa: F401  (registers action_identity)
from services.db import models as _models  # noqa: F401  (registers tables on Base.metadata)
from services.db.base import Base
from services.engine.procedures import runs as _procedure_runs  # noqa: F401  (registers run tables)

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live connection (emit SQL)."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations against the async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
