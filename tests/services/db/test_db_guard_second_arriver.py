"""AC-4 of PLAN-0120 — a child session with its OWN role acquires and runs.

The second arriver is a **real child pytest**, never an in-process stand-in: the whole
mechanism is about two processes, and a stand-in would prove only that the guard object
can be called twice.

⚠️ **AC-4 is the "not unconditional" control for AC-3.** A guard that refused *every*
arriver would satisfy AC-3's "the lock is really held" perfectly and make the suite
unrunnable. This file is what proves acquisition still succeeds.

This file now also carries **AC-6** (the second arriver errors, names the holder, and
skips nothing) and the child-side halves of **AC-7** (the token reports measured values
on clean runs as well as dirty ones) — PLAN-0120 Step 2. The refusal branch was
exercised here from Step 1 rather than waiting, because shipping ``tests/db_guard.py``
with its refusal path never once executed would have been shipping an untested guard;
Step 2 added the parts that need the session hooks: the ``skipped`` count, the parsed
token fields, and the xdist refusal.
"""

from __future__ import annotations

import asyncio
import os
import re
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


def _token_fields(stdout: str) -> dict[str, str]:
    """The child's single ``TEST-DB-GUARD`` line, parsed into its fields.

    Parsing rather than substring-matching so an assertion about ``foreign_backends``
    cannot be satisfied by the string turning up inside the contention *reason* — which
    also carries a copy of the token, prefixed by pytest's ``! …Exit:`` marker and
    therefore not matched by the line filter below.
    """
    lines = [ln for ln in stdout.splitlines() if ln.startswith("TEST-DB-GUARD ")]
    assert len(lines) == 1, f"expected exactly one token line, got {len(lines)}: {stdout[-800:]}"
    fields: dict[str, str] = {}
    for part in lines[0].removeprefix("TEST-DB-GUARD ").split(" "):
        key, sep, value = part.partition("=")
        if sep:
            fields[key] = value
    return fields


def _skipped_count(stdout: str) -> int:
    """How many tests the child reported as skipped. Absent from the summary means 0."""
    match = re.search(r"(\d+) skipped", stdout)
    return int(match.group(1)) if match else 0


def _run_child_as_xdist_worker() -> subprocess.CompletedProcess[str]:
    """A child that believes it is an xdist worker, on a node that needs no database."""
    env = dict(os.environ)
    env.pop(db_guard.ROLE_ENV, None)
    env["PYTEST_XDIST_WORKER"] = "gw0"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/tools/test_db_guard.py",
            "-q",
            "-p",
            "no:cacheprovider",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=CHILD_TIMEOUT_S,
        check=False,
    )


async def test_an_xdist_worker_is_refused_outright() -> None:
    """🔴 The guard binds ONE process to one database; xdist workers are many.

    Without a role each worker would contend on a single name, and — far worse — a guard
    that quietly let them share would report ``ACQUIRED`` while three other workers
    dropped the schema underneath it. PLAN-0120 puts xdist out of scope with the
    instruction to make the future failure loud, so the session refuses at
    ``pytest_sessionstart`` rather than guessing at a design.

    The node chosen needs no database, so a refusal here cannot be confused with
    Postgres being unreachable.
    """
    proc = await asyncio.to_thread(_run_child_as_xdist_worker)
    combined = proc.stdout + proc.stderr
    print(
        f"rc={proc.returncode} (pytest usage-error is 4) named_xdist={'xdist worker' in combined}"
    )
    assert proc.returncode == 4, combined[-800:]
    assert "pytest-xdist worker" in combined, combined[-800:]


async def test_the_same_child_without_the_xdist_marker_runs_normally() -> None:
    """🟢 POSITIVE CONTROL for the test above, and it is what makes it mean anything.

    A ``pytest_sessionstart`` that raised unconditionally — a typo'd condition, an
    inverted check — would satisfy the refusal assertions perfectly and break every run
    in the repo. This proves the refusal is caused by the marker and by nothing else.
    """
    env = dict(os.environ)
    env.pop(db_guard.ROLE_ENV, None)
    env.pop("PYTEST_XDIST_WORKER", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = await asyncio.to_thread(
        lambda: subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/tools/test_db_guard.py",
                "-q",
                "-p",
                "no:cacheprovider",
            ],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=CHILD_TIMEOUT_S,
            check=False,
        )
    )
    print(f"control_rc={proc.returncode} (must be 0)")
    assert proc.returncode == 0, (proc.stdout + proc.stderr)[-800:]


async def test_a_second_session_on_the_same_name_exits_contended_naming_the_holder(
    parent_guard: db_guard.TestDbGuard,
) -> None:
    """🔴 AC-6. The second arriver ERRORS and names the holder — it never skips.

    No role, so the child resolves the SAME database the parent is holding.

    The ``skipped`` half is the one that matters most and is easiest to lose: a mass
    skip reads as a pass on the summary line, so a guard that skipped would look green
    to every reader and to CI. The three values are printed together because "it exited
    75" and "it skipped nothing" are separate facts and a reader needs both.
    """
    proc = await asyncio.to_thread(_run_child, None)
    fields = _token_fields(proc.stdout)
    holder_named = f"holder_pid={parent_guard.holder_pid}" in proc.stdout
    skipped = _skipped_count(proc.stdout)
    print(f"rc={proc.returncode} holder_named={holder_named} skipped={skipped}")
    print(f"child_token={fields}")
    # 🔴 The ORDER is deliberate and load-bearing for witnessability, not style.
    # pytest stops at the first failing assert, so a mutation that turns the refusal
    # into a skip would redden `rc == 75` first and leave `skipped == 0` NOT-REACHED —
    # state unknown, never green — and that claim would have no witness at all.
    # Asserting the skip count first gives each claim its own reddening mutation:
    # exit→skip reddens this line, while returncode→0 reddens the one below and leaves
    # this one green.
    assert skipped == 0, proc.stdout[-800:]
    assert proc.returncode == db_guard.CONTENDED_EXIT, proc.stdout + proc.stderr
    assert fields["outcome"] == db_guard.CONTENDED, fields
    assert holder_named, proc.stdout[-800:]


async def test_the_contended_childs_token_reports_a_foreign_backend_count(
    parent_guard: db_guard.TestDbGuard,
) -> None:
    """AC-7(c). The dirty run's token carries ``foreign_backends`` with an integer.

    🔴 Deliberately **not** asserted equal to a particular number. §4.2.5: the refused
    ``pg_try_advisory_lock`` answers *whether*, while this count is a point-in-time
    measurement that can legitimately read ``0`` under real contention, because the
    other session's per-test engines are ``NullPool`` and may be between connections at
    that instant. Pinning it to a value would make a true reading a failure.
    """
    proc = await asyncio.to_thread(_run_child, None)
    fields = _token_fields(proc.stdout)
    print(f"rc={proc.returncode} outcome={fields.get('outcome')} token={fields}")
    assert fields["outcome"] == db_guard.CONTENDED, fields
    assert fields["foreign_backends"].isdigit(), fields


async def test_the_clean_childs_token_reports_its_measured_values(
    parent_guard: db_guard.TestDbGuard, child_role: str
) -> None:
    """AC-7(b). A CLEAN child prints values, not a verdict.

    ``foreign_backends=0`` is asserted exactly here and nowhere else: the child's
    database is freshly created for its own role, so nothing else can be connected to
    it, which makes ``0`` a real prediction rather than a hopeful one. ``db_tests=1``
    is what proves the child actually reached a live engine — without it the token
    could read ``ACQUIRED`` on a session that skipped everything.
    """
    proc = await asyncio.to_thread(_run_child, child_role)
    fields = _token_fields(proc.stdout)
    print(f"rc={proc.returncode} token={fields}")
    assert fields["outcome"] == db_guard.ACQUIRED, fields
    assert fields["foreign_backends"] == "0", fields
    assert fields["db_tests"] == "1", fields
