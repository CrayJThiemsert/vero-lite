"""AC-11 of PLAN-0120 — the creation race is REPORTED, and a real error is not hidden.

🔴 **The old code was wrong in both directions, and this file pins both.** Measured
(Code, s277): a losing ``CREATE DATABASE`` has three shapes, and
``except ProgrammingError: pass`` caught the wrong two —

======================  ======================  =========  ===============================
shape                   exception               SQLSTATE   old behaviour
======================  ======================  =========  ===============================
plain duplicate         ``ProgrammingError``    ``42P04``  swallowed — correct
**concurrent race**     ``IntegrityError``      ``23505``  **escaped — crashed the caller**
**malformed statement**  ``ProgrammingError``   ``42704``  **swallowed — silently wrong**
======================  ======================  =========  ===============================

So one test here is not enough: a fix that merely swapped the class would satisfy the
race test and still hide a genuine failure. The second test is what stops that.

⚠️ Every test carries its own **outer** ``asyncio.wait_for``, the
``test_teardown_bound_reddens.py`` rule: a regression must redden in seconds rather
than hang the suite.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator

import asyncpg
import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DatabaseError

from services.api.config import settings
from tests import db_guard, db_support

OUTER_TIMEOUT_S = 45.0

#: Forces the existence short-circuit to miss, so the CREATE is actually attempted —
#: which is what a second arriver experiences.
_NEVER_EXISTS_SQL = "SELECT 1 WHERE false"


async def _always_absent(admin: object, db_name: str) -> bool:
    """Re-check stand-in answering "the database is NOT there" — a genuine failure."""
    return False


async def _always_present(admin: object, db_name: str) -> bool:
    """Re-check stand-in answering "the database IS there" — a race someone else won."""
    return True


def _admin_dsn() -> str:
    return (
        make_url(settings.test_database_url)
        .set(drivername="postgresql", database="postgres")
        .render_as_string(hide_password=False)
    )


@pytest.fixture
async def admin_conn() -> AsyncIterator[asyncpg.Connection]:
    try:
        conn = await asyncio.wait_for(asyncpg.connect(_admin_dsn()), OUTER_TIMEOUT_S)
    except Exception:
        pytest.skip("Postgres not reachable — start docker compose / set DATABASE_URL")
    try:
        yield conn
    finally:
        await conn.close()


@pytest.fixture
async def fresh_name(admin_conn: asyncpg.Connection) -> AsyncIterator[str]:
    """A database name that does not exist yet, dropped again afterwards.

    Derived through :func:`db_guard.role_suffixed` — the same lever the goal gate and
    per-role children use — so the window this test opens is the same window SD-A opens
    in production, not one invented for the test.
    """
    role = f"r{os.getpid() % 100000}"
    url = db_guard.role_suffixed(settings.test_database_url, role)
    name = make_url(url).database
    await admin_conn.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
    try:
        yield url
    finally:
        await admin_conn.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        left = await admin_conn.fetchval(
            "SELECT count(*) FROM pg_database WHERE datname = $1", name
        )
        print(f"cleanup dropped={name} remaining={left} (must be 0)")
        assert left == 0


async def test_two_concurrent_creators_of_a_fresh_name_report_one_race(
    admin_conn: asyncpg.Connection, fresh_name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """🔴 AC-11. The race is counted, and it resolves to exactly one database.

    Measured at P-VX-6 as ``races=10/10`` on this box, so ``asyncio.gather`` is the
    driver and the ``Barrier``-synchronised fallback the PLAN pre-committed is not
    taken.

    The counter is read as a **delta**, never as an absolute: another test in the same
    session may legitimately have raced, and asserting ``post == 1`` would turn that
    into a failure. The database count is the control — a race that resolved to two
    databases, or none, would be a different defect and must not read as success.
    """
    monkeypatch.setattr(settings, "test_database_url", fresh_name)
    guard = db_support.session_guard()
    name = make_url(fresh_name).database

    pre = guard.create_race
    await asyncio.wait_for(
        asyncio.gather(db_support.ensure_test_database(), db_support.ensure_test_database()),
        OUTER_TIMEOUT_S,
    )
    post = guard.create_race
    rows = await admin_conn.fetchval("SELECT count(*) FROM pg_database WHERE datname = $1", name)
    print(f"create_race pre={pre} post={post} datname_rows={rows} name={name}")
    assert post - pre >= 1
    assert rows == 1


async def test_a_single_creator_of_a_fresh_name_reports_no_race(
    admin_conn: asyncpg.Connection, fresh_name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """🟢 POSITIVE CONTROL for the counter, and the load-bearing one.

    A counter incremented unconditionally — on every call, or in the wrong branch —
    would satisfy the race test perfectly and report a contention on every clean run.
    One creator must move it by zero.
    """
    monkeypatch.setattr(settings, "test_database_url", fresh_name)
    guard = db_support.session_guard()
    name = make_url(fresh_name).database

    pre = guard.create_race
    await asyncio.wait_for(db_support.ensure_test_database(), OUTER_TIMEOUT_S)
    post = guard.create_race
    rows = await admin_conn.fetchval("SELECT count(*) FROM pg_database WHERE datname = $1", name)
    print(f"control create_race pre={pre} post={post} datname_rows={rows}")
    assert post - pre == 0
    assert rows == 1


async def test_a_create_failure_that_is_not_a_race_is_raised_not_swallowed(
    admin_conn: asyncpg.Connection, fresh_name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """🔴 The half a class-swap fix would miss.

    Shape C: ``CREATE DATABASE`` fails for a reason that is **not** contention, so the
    database is not there afterwards. The old clause swallowed exactly this and let the
    caller go on to connect to a database that was never created.

    The failure is a real Postgres error — the name already exists, so ``CREATE`` really
    does raise ``42P04`` — while the existence re-check is forced to answer "not there".
    That is the precise conjunct under test: *the decision to re-raise is made by the
    re-check's answer, not by the exception's class.*

    This test and its control below differ in **exactly one input** — what the re-check
    answers. Everything else, including the real Postgres error, is identical.
    """
    monkeypatch.setattr(settings, "test_database_url", fresh_name)
    name = make_url(fresh_name).database
    await admin_conn.execute(f'CREATE DATABASE "{name}"')

    monkeypatch.setattr(db_support, "_DB_EXISTS_SQL", _NEVER_EXISTS_SQL)
    monkeypatch.setattr(db_support, "_database_exists", _always_absent)
    with pytest.raises(DatabaseError) as excinfo:
        await asyncio.wait_for(db_support.ensure_test_database(), OUTER_TIMEOUT_S)
    sqlstate = getattr(getattr(excinfo.value, "orig", None), "sqlstate", None)
    print(f"raised={type(excinfo.value).__name__} sqlstate={sqlstate} (expect 42P04)")
    assert sqlstate == "42P04"


async def test_the_same_failure_with_the_database_present_is_counted_not_raised(
    admin_conn: asyncpg.Connection, fresh_name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """🟢 POSITIVE CONTROL for the test above, and it is what makes it mean anything.

    Byte-for-byte the same setup as the test above — an existing name, so ``CREATE``
    raises the same real ``42P04`` — with **one input changed**: the re-check answers
    "the database IS there". The call must then return quietly and count a race.

    Without this control, an ``ensure_test_database`` that re-raised **everything**
    would satisfy the test above perfectly and break every first run in the repo.
    """
    monkeypatch.setattr(settings, "test_database_url", fresh_name)
    name = make_url(fresh_name).database
    await admin_conn.execute(f'CREATE DATABASE "{name}"')

    guard = db_support.session_guard()
    pre = guard.create_race
    monkeypatch.setattr(db_support, "_DB_EXISTS_SQL", _NEVER_EXISTS_SQL)
    monkeypatch.setattr(db_support, "_database_exists", _always_present)
    await asyncio.wait_for(db_support.ensure_test_database(), OUTER_TIMEOUT_S)
    post = guard.create_race
    print(f"control create_race pre={pre} post={post} (must move by 1, no raise)")
    assert post - pre == 1
