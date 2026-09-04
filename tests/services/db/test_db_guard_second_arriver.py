"""AC-4 of PLAN-0120 — a child session with its OWN role acquires and runs.

The second arriver is a **real child pytest**, never an in-process stand-in: the whole
mechanism is about two processes, and a stand-in would prove only that the guard object
can be called twice.

⚠️ **AC-4 is the "not unconditional" control for AC-3.** A guard that refused *every*
arriver would satisfy AC-3's "the lock is really held" perfectly and make the suite
unrunnable. This file is what proves acquisition still succeeds.

📌 The CONTENDED case below is **AC-6's claim, which PLAN-0120 assigns to Step 2**. It is
landed here anyway, deliberately: the two children cost one spawn each and share this
file's cleanup, and shipping ``tests/db_guard.py`` with its refusal branch never once
executed would be shipping an untested guard. Step 2 still owns AC-6's full pass read
(the `skipped` count and the holder-naming probe); what is closed here is only that the
branch runs and returns the reserved code.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import asyncpg
import pytest
from sqlalchemy.engine import make_url

from services.api.config import settings
from tests import db_guard, db_support

REPO_ROOT = Path(__file__).resolve().parents[3]

#: One cheap, genuinely DB-backed node. The child must reach a live engine — otherwise
#: it never acquires and the token would read NOT-NEEDED, passing this test vacuously.
CHILD_NODE = (
    "tests/services/db/test_teardown_bound_reddens.py" "::test_an_unblocked_teardown_still_succeeds"
)

#: A child pytest imports the whole conftest tree; generous, but bounded so a regression
#: reddens instead of hanging the suite.
CHILD_TIMEOUT_S = 300.0


def _admin_dsn() -> str:
    return (
        make_url(settings.test_database_url)
        .set(drivername="postgresql", database="postgres")
        .render_as_string(hide_password=False)
    )


def _run_child(role: str | None) -> subprocess.CompletedProcess[str]:
    """Spawn a real pytest child, optionally with its own database role."""
    env = dict(os.environ)
    if role is None:
        env.pop(db_guard.ROLE_ENV, None)
    else:
        env[db_guard.ROLE_ENV] = role
    # PYTHONDONTWRITEBYTECODE mirrors the probe battery's child env so the two agree.
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "pytest", CHILD_NODE, "-q", "-p", "no:cacheprovider"],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=CHILD_TIMEOUT_S,
        check=False,
    )


@pytest.fixture
async def parent_guard() -> AsyncIterator[db_guard.TestDbGuard]:
    """Ensure the PARENT holds its lock before any child is spawned — otherwise the
    contention case below would be a race rather than a test."""
    eng = await db_support.create_test_engine()
    await eng.dispose()
    guard = db_support.session_guard()
    assert guard.state == db_guard.ACQUIRED, guard.token(0)
    yield guard


@pytest.fixture
async def child_role() -> AsyncIterator[str]:
    """A role unique to this process, with the database it creates dropped afterwards.

    Cleanup is asserted rather than hoped for: a leaked ``…_t<pid>`` database per run
    would accumulate silently on the dev cluster.
    """
    role = f"t{os.getpid() % 100000}"
    yield role
    name = make_url(db_guard.role_suffixed(settings.test_database_url, role)).database
    try:
        conn = await asyncio.wait_for(asyncpg.connect(_admin_dsn()), 30.0)
    except Exception:
        return
    try:
        await conn.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        left = await conn.fetchval("SELECT count(*) FROM pg_database WHERE datname = $1", name)
        print(f"cleanup dropped={name} remaining={left} (must be 0)")
        assert left == 0
    finally:
        await conn.close()


async def test_a_child_session_with_its_own_role_acquires_and_runs(
    parent_guard: db_guard.TestDbGuard, child_role: str
) -> None:
    """🔴 AC-4 / 🟢 the "not unconditional" control.

    The child resolves a DIFFERENT database because of its role, so it acquires its own
    lock and runs to a normal green — while the parent still holds its own.
    """
    proc = await asyncio.to_thread(_run_child, child_role)
    print(f"child_rc={proc.returncode} role={child_role}")
    print(f"child_tail={proc.stdout.strip()[-400:]!r}")
    assert proc.returncode == 0, proc.stdout + proc.stderr


async def test_the_childs_token_shows_it_acquired_its_own_database(
    parent_guard: db_guard.TestDbGuard, child_role: str
) -> None:
    """The child must report ACQUIRED **on its own name** — the claim that proves the
    role marker reached the CHILD, not merely that the parent set an env var.

    A child that ignored the role would still exit 0 (it would just contend, or share),
    so the return code alone cannot carry this.

    🔴 **The load-bearing assertion is the INEQUALITY, not the equality.** An earlier
    draft compared the child's reported name against
    ``db_guard.role_suffixed(...)`` — the very function under test — so a mutation to
    the suffixing moved BOTH sides together and the assertion could not redden. That is
    a guard reading its own constant. The child's name is therefore checked against the
    **parent's** name, a value the mutation cannot follow.
    """
    proc = await asyncio.to_thread(_run_child, child_role)
    parent_db = make_url(settings.test_database_url).database
    reported = [ln for ln in proc.stdout.splitlines() if ln.startswith("TEST-DB-GUARD ")]
    print(f"child_rc={proc.returncode} parent_db={parent_db} child_token={reported}")
    assert len(reported) == 1, proc.stdout[-800:]
    child_db = reported[0].split("db=", 1)[1].split(" ", 1)[0]
    assert child_db != parent_db, f"child_db={child_db} parent_db={parent_db}"
    assert child_db.endswith(f"_{child_role}"), f"child_db={child_db} role={child_role}"
    assert f"outcome={db_guard.ACQUIRED}" in reported[0], reported[0]


async def test_a_second_session_on_the_same_name_is_refused_with_the_reserved_code(
    parent_guard: db_guard.TestDbGuard,
) -> None:
    """📌 AC-6's branch, landed early so the refusal path is not shipped unexecuted.

    No role, so the child resolves the SAME database the parent is holding. It must exit
    with the reserved code and name the holder — never skip, because a mass skip reads
    as a pass on the summary line.
    """
    proc = await asyncio.to_thread(_run_child, None)
    print(f"child_rc={proc.returncode} expected={db_guard.CONTENDED_EXIT}")
    print(f"child_tail={proc.stdout.strip()[-500:]!r}")
    assert proc.returncode == db_guard.CONTENDED_EXIT, proc.stdout + proc.stderr
    assert f"outcome={db_guard.CONTENDED}" in proc.stdout, proc.stdout[-800:]
    assert f"holder_pid={parent_guard.holder_pid}" in proc.stdout, proc.stdout[-800:]
