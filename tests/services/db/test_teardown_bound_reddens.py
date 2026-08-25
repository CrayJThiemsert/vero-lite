"""AC-8: a `drop_all` teardown blocked by a leaked session REDDENS instead of hanging.

The s253 incident, replayed as an oracle. `drop_all` needs `ACCESS EXCLUSIVE` on every
table; a session another test left `idle in transaction` holds a conflicting lock, and an
unbounded `drop_all` then waits **forever** — measured as a 67-minute hang whose head of
queue was one un-rolled-back session, with a second pytest queued behind it.

🔴 **The bound does not prevent the failure; it changes its KIND** — from "the suite stops
silently" to "one test reddens in seconds naming the operation". A failure that never
reddens is a failure the test system cannot see, which is why this file asserts on the
*kind* of failure rather than on the absence of one.

⚠️ Every test here carries its own **outer** `asyncio.wait_for`. A regression must hang
*this test* for a few seconds and then fail — never the suite. Bounding a race test from
the outside is the precedent from the DB-race lesson: without it, the failure mode of a
broken bound is an unattended process, not a red.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine

from services.db.base import Base
from tests.db_support import create_test_engine, drop_all_bounded

#: Short enough to keep the suite quick, long enough that ordinary contention does not
#: trip it. The shipped default is 20s; the bound under test is the mechanism, not the
#: number, so the tests pass their own.
PROBE_TIMEOUT = "1s"

#: The outer bound. Comfortably above PROBE_TIMEOUT, far below "forever".
OUTER_TIMEOUT_S = 25.0


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await drop_all_bounded(conn)
    await eng.dispose()


async def _hold_conflicting_lock(engine: AsyncEngine, table: str) -> AsyncIterator[None]:
    """Leave a session `idle in transaction` holding a lock `drop_all` must wait for."""
    conn = await engine.connect()
    await conn.execute(sa.text(f"LOCK TABLE {table} IN ACCESS SHARE MODE"))
    try:
        yield
    finally:
        await conn.rollback()
        await conn.close()


def _first_table() -> str:
    return sorted(Base.metadata.tables)[0]


async def test_a_blocked_teardown_fails_within_the_bound_instead_of_hanging(
    db_engine: AsyncEngine,
) -> None:
    """🔴 The AC. Unbounded, this call never returns; bounded, it raises in ~1s."""
    holder = _hold_conflicting_lock(db_engine, _first_table())
    await holder.__anext__()
    try:
        async with db_engine.connect() as conn:
            async with conn.begin():
                with pytest.raises(DBAPIError):
                    await asyncio.wait_for(
                        drop_all_bounded(conn, timeout=PROBE_TIMEOUT), OUTER_TIMEOUT_S
                    )
    finally:
        with pytest.raises(StopAsyncIteration):
            await holder.__anext__()


async def test_the_blocked_teardowns_error_names_the_lock_timeout(
    db_engine: AsyncEngine,
) -> None:
    """A red that does not say WHY is a red nobody can act on (ADR-0038 C6's legibility
    conjunct). Postgres reports `canceling statement due to lock timeout`."""
    holder = _hold_conflicting_lock(db_engine, _first_table())
    await holder.__anext__()
    try:
        async with db_engine.connect() as conn:
            async with conn.begin():
                with pytest.raises(DBAPIError) as excinfo:
                    await asyncio.wait_for(
                        drop_all_bounded(conn, timeout=PROBE_TIMEOUT), OUTER_TIMEOUT_S
                    )
        assert "lock timeout" in str(excinfo.value).lower()
    finally:
        with pytest.raises(StopAsyncIteration):
            await holder.__anext__()


async def test_an_unblocked_teardown_still_succeeds(db_engine: AsyncEngine) -> None:
    """🟢 POSITIVE CONTROL — and the load-bearing one. Without it, a `drop_all_bounded`
    that raised unconditionally (a typo'd `SET`, an impossible timeout) would satisfy both
    assertions above perfectly. This proves the failures are caused by the held lock."""
    async with db_engine.connect() as conn:
        async with conn.begin():
            await asyncio.wait_for(drop_all_bounded(conn, timeout=PROBE_TIMEOUT), OUTER_TIMEOUT_S)
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def test_the_lock_holder_really_holds_a_conflicting_lock(
    db_engine: AsyncEngine,
) -> None:
    """🟢 The other half of the control: the fixture's session is genuinely visible to
    Postgres as holding a lock on the table. If it were not, the two reds above would be
    caused by something else entirely and the test would be measuring the wrong thing."""
    table = _first_table()
    holder = _hold_conflicting_lock(db_engine, table)
    await holder.__anext__()
    try:
        async with db_engine.connect() as conn:
            rows = await conn.execute(
                sa.text(
                    "SELECT count(*) FROM pg_locks l JOIN pg_class c ON c.oid = l.relation "
                    "WHERE c.relname = :t AND l.granted"
                ),
                {"t": table},
            )
            assert rows.scalar_one() > 0
    finally:
        with pytest.raises(StopAsyncIteration):
            await holder.__anext__()
