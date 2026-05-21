"""Async SQLAlchemy engine + session factory (PLAN-0005 §6.6).

The engine binds to ``settings.database_url`` (asyncpg driver). Engine
creation is lazy — importing this module does not open a connection —
so model and parity tests can import it without a live database.
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from services.api.config import settings

engine = create_async_engine(settings.database_url, echo=False)
"""Process-wide async engine bound to settings.database_url."""

async_session = async_sessionmaker(engine, expire_on_commit=False)
"""Async session factory."""


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield an AsyncSession, closing it on exit (FastAPI dependency)."""
    async with async_session() as session:
        yield session
