"""AC-3 and AC-5 of PLAN-0120 — the lock is real, and a LOST holder is loud.

🔴 **The bar this file is written against is the fail-OPEN direction.** Postgres
releases a session advisory lock the instant its backend dies, so a guard whose holder
is gone reports **exactly what a working guard reports on a clean run**. "No contention
observed" is therefore never evidence the guard works. AC-5 is the only test here that
can tell the two apart, and it does it by killing the holder on purpose and asserting
the session refuses to continue.

⚠️ Every test carries its own **outer** ``asyncio.wait_for`` (the
``test_teardown_bound_reddens.py`` rule). A regression must redden *this test* in
seconds — never hang the suite.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator

import asyncpg
import pytest
from _pytest.outcomes import Exit
from sqlalchemy.engine import make_url

from services.api.config import settings
from tests import db_guard, db_support

#: Comfortably above one connect + one round-trip, far below "forever".
OUTER_TIMEOUT_S = 30.0


def _admin_dsn() -> str:
    """The maintenance-DB DSN, derived the same way the guard derives it (SD-2)."""
    return (
        make_url(settings.test_database_url)
        .set(drivername="postgresql", database="postgres")
        .render_as_string(hide_password=False)
    )


@pytest.fixture
async def admin_conn() -> AsyncIterator[asyncpg.Connection]:
    """A second connection, independent of the guard's holder — the only vantage point
    from which "is the lock really held" is a measurement rather than a self-report."""
    try:
        conn = await asyncio.wait_for(asyncpg.connect(_admin_dsn()), OUTER_TIMEOUT_S)
    except Exception:
        pytest.skip("Postgres not reachable — start docker compose / set DATABASE_URL")
    try:
        yield conn
    finally:
        await conn.close()


@pytest.fixture
async def live_guard() -> db_guard.TestDbGuard:
    """The session's own guard, acquired. Going through ``create_test_engine`` rather
    than acquiring by hand is deliberate: it proves the CHOKEPOINT acquires, which is
    the property SD-4 rests on."""
    eng = await db_support.create_test_engine()
    await eng.dispose()
    return db_support.session_guard()


# --------------------------------------------------------------------- AC-3


async def test_the_guard_holder_really_holds_the_advisory_lock(
    live_guard: db_guard.TestDbGuard, admin_conn: asyncpg.Connection
) -> None:
    """🔴 AC-3. Postgres itself must agree that the holder holds the key.

    Without this, every other assertion in this PLAN rests on the guard's own
    bookkeeping — a guard that set ``state = ACQUIRED`` and locked nothing would satisfy
    them all.
    """
    assert live_guard.state == db_guard.ACQUIRED, live_guard.token(0)
    classid, objid = db_guard.lock_halves(live_guard.key)
    granted = await asyncio.wait_for(
        admin_conn.fetchval(
            "SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND granted "
            "AND pid = $1 AND classid = $2 AND objid = $3",
            live_guard.holder_pid,
            classid,
            objid,
        ),
        OUTER_TIMEOUT_S,
    )
    print(f"granted_rows={granted} holder_pid={live_guard.holder_pid} key={live_guard.key}")
    assert granted > 0


async def test_a_second_connection_is_refused_the_same_key(
    live_guard: db_guard.TestDbGuard, admin_conn: asyncpg.Connection
) -> None:
    """🔴 AC-3's other half — the lock EXCLUDES, which is the whole mechanism.

    A shared lock would show up in ``pg_locks`` as granted and let every arriver in, so
    the row count above would pass while the guard guarded nothing.
    """
    got = await asyncio.wait_for(
        admin_conn.fetchval("SELECT pg_try_advisory_lock($1)", live_guard.key), OUTER_TIMEOUT_S
    )
    if got:  # pragma: no cover — only on a regression; never leave the lock behind
        await admin_conn.fetchval("SELECT pg_advisory_unlock($1)", live_guard.key)
    print(f"second_connection_acquired={got} (must be False) key={live_guard.key}")
    assert got is False


async def test_an_unheld_key_is_available_to_that_same_connection(
    admin_conn: asyncpg.Connection,
) -> None:
    """🟢 POSITIVE CONTROL, and the load-bearing one for the test above. A connection
    that could never take *any* advisory lock — wrong database, wrong privileges, a
    typo'd call — would report ``False`` for the guarded key too, and the refusal test
    would be measuring nothing."""
    spare = db_guard.advisory_key(f"vero_lite_test_ac3_control_{os.getpid()}")
    got = await asyncio.wait_for(
        admin_conn.fetchval("SELECT pg_try_advisory_lock($1)", spare), OUTER_TIMEOUT_S
    )
    try:
        print(f"control_acquired_unheld_key={got} (must be True) key={spare}")
        assert got is True
    finally:
        await admin_conn.fetchval("SELECT pg_advisory_unlock($1)", spare)


# --------------------------------------------------------------------- AC-5


async def test_a_terminated_holder_is_detected_as_lost_not_as_clean(
    admin_conn: asyncpg.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    """🔴 AC-5 — the fail-OPEN witness, and the reason this PLAN exists in this shape.

    A scratch guard (its own database name, so its key cannot collide with the session's
    own) is acquired, proven alive, then its backend is terminated from another
    connection. The chokepoint must then report the holder ABSENT and refuse to run —
    not sail on reporting a clean session, which is what it did before this guard and
    what a dead guard would do again.

    The values are printed because ``alive_pre=1 alive_post=0`` is the whole evidence:
    a bare pass here would be satisfied by a chokepoint that always raises.
    """
    scratch_url = db_guard.role_suffixed(settings.test_database_url, f"ac5{os.getpid() % 100000}")
    scratch = db_guard.TestDbGuard(scratch_url, None)
    try:
        outcome = await asyncio.to_thread(scratch.acquire)
        assert outcome == db_guard.ACQUIRED, scratch.token(0)

        alive_pre = await asyncio.wait_for(
            admin_conn.fetchval(
                "SELECT count(*) FROM pg_stat_activity WHERE pid = $1", scratch.holder_pid
            ),
            OUTER_TIMEOUT_S,
        )

        await asyncio.wait_for(
            admin_conn.fetchval("SELECT pg_terminate_backend($1)", scratch.holder_pid),
            OUTER_TIMEOUT_S,
        )
        alive_post = await asyncio.wait_for(
            admin_conn.fetchval(
                "SELECT count(*) FROM pg_stat_activity WHERE pid = $1", scratch.holder_pid
            ),
            OUTER_TIMEOUT_S,
        )
        print(f"alive_pre={alive_pre} alive_post={alive_post} holder_pid={scratch.holder_pid}")
        assert alive_pre == 1
        assert alive_post == 0

        # Drive the REAL chokepoint with the dead guard. Catching Exit here keeps the
        # session alive; uncaught, this is what would stop the run.
        monkeypatch.setattr(db_support, "_SESSION_GUARD", scratch)
        with pytest.raises(Exit) as excinfo:
            await asyncio.wait_for(db_support.create_test_engine(), OUTER_TIMEOUT_S)
        reason = str(excinfo.value)
        print(f"chokepoint_reason={reason}")
        assert f"outcome={db_guard.LOST}" in reason
        assert f"holder_pid={scratch.holder_pid}" in reason
    finally:
        scratch.release()


async def test_a_live_holder_lets_the_chokepoint_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """🟢 POSITIVE CONTROL for AC-5, and it is what makes that test mean anything. A
    chokepoint that raised ``Exit`` unconditionally — a typo'd comparison, an inverted
    ``not`` — would satisfy the LOST assertions perfectly. This proves the raise is
    caused by the terminated holder and by nothing else."""
    scratch_url = db_guard.role_suffixed(settings.test_database_url, f"ac5ok{os.getpid() % 10000}")
    scratch = db_guard.TestDbGuard(scratch_url, None)
    try:
        outcome = await asyncio.to_thread(scratch.acquire)
        assert outcome == db_guard.ACQUIRED, scratch.token(0)
        monkeypatch.setattr(db_support, "_SESSION_GUARD", scratch)
        eng = await asyncio.wait_for(db_support.create_test_engine(), OUTER_TIMEOUT_S)
        print(f"chokepoint_passed_with_live_holder holder_pid={scratch.holder_pid}")
        await eng.dispose()
    finally:
        scratch.release()
