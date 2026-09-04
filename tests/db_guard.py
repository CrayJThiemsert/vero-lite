"""Bind one pytest process to the test database it is about to drop schemas in.

PLAN-0120 Step 1, the pytest-owned half of ADR-0018 **D8.4**. The gate's half (an
identity marker injected into every ``check`` subprocess) makes the goal gate stop
sharing a database with the session that spawned it; this module stops two *pytest*
processes in one checkout from doing the same.

**The mechanism (SD-B, ruled (b)).** A Postgres **session-level advisory lock**, keyed
by a digest of the target database name, taken on the ``postgres`` maintenance
database (SD-2) so the key is load-bearing — advisory-lock namespaces are per
database, and every session shares the maintenance one. A second arriver's
``pg_try_advisory_lock`` returns ``false``, the guard names the holder from
``pg_locks`` joined to ``pg_stat_activity``, and the session **errors** with
:data:`CONTENDED_EXIT`. Never ``pytest.skip``: a mass skip reads as a pass on the
summary line, which is the failure this whole PLAN exists to remove.

🔴 **The central risk is the opposite direction, and this module is shaped around it.**
Postgres releases a session advisory lock the instant its backend dies. A holder lost
mid-session — an exception, a closed loop, a ``pg_terminate_backend`` — makes the
guard stop guarding while reporting **exactly what a working guard reports on a clean
run**. "No contention" is therefore never evidence that the guard works. Two
consequences are built in rather than documented:

* the holder's liveness is re-proven at the chokepoint on **every** DB test
  (:data:`LIVENESS_SQL`, one query that also serves as the reachability probe, so it
  costs no extra round-trip), and a vanished holder is a distinct, loud
  :data:`LOST` outcome;
* :meth:`TestDbGuard.token` prints the values it measured on clean runs as well as
  dirty ones (CLAUDE.md §8) — never a bare PASS/FAIL.

🔴 **Measured, not assumed (Code, s277, PLAN-0120 Step 1 pre-flight).**
``_pytest.outcomes.Exit`` is a subclass of ``Exception`` and a bare
``except Exception`` **does** swallow ``pytest.exit`` — demonstrated, not inferred.
Every ``pytest.exit`` driven by this guard therefore has to sit *outside* the
``try/except Exception`` blocks in ``tests/db_support.py``; inside one, the guard
degrades silently into a skip. That is why this module never raises ``pytest.exit``
itself: :meth:`TestDbGuard.acquire` *returns* an outcome and
:meth:`TestDbGuard.contention_reason` / :meth:`TestDbGuard.lost_reason` build the
text, leaving the one caller that knows where the ``try`` blocks are — the chokepoint
in ``tests/db_support.py`` — to raise it from a safe position.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
import threading
from typing import Final

import asyncpg
from sqlalchemy.engine import make_url

#: ``EX_TEMPFAIL`` from ``sysexits.h`` — "temporary failure, invited to retry", which is
#: exactly what a second arriver should do. pytest reserves 0-5 for its own verdicts, and
#: 128+ is signal death, so 75 can never be mistaken for either. A **literal** on both
#: sides of the Windows/WSL boundary because the goal gate cannot import ``tests/``;
#: ``tests/handoffs/test_goal_gate_contended_exit_pins_the_guard.py`` pins the two equal.
CONTENDED_EXIT: Final = 75

#: The environment variable that gives a pytest process its own database. Free-form by
#: design: the gate uses ``gate``, and a test that needs a genuinely separate child
#: session uses ``t<pid>`` — so the isolation lever is exercised by the suite, not only
#: by the hook.
ROLE_ENV: Final = "VERO_TEST_DB_ROLE"

#: A typo must not silently mean "no isolation", so the role is validated and a bad one
#: raises at import rather than resolving to the unsuffixed name.
_ROLE_RE: Final = re.compile(r"^[a-z0-9_]{1,16}$")

# Guard outcomes. Strings rather than an enum so they survive into the printed token and
# into a child process's stdout unchanged.
ACQUIRED: Final = "ACQUIRED"
CONTENDED: Final = "CONTENDED"
ABSENT: Final = "ABSENT"
LOST: Final = "LOST"
NOT_NEEDED: Final = "NOT-NEEDED"

#: The chokepoint probe. It replaces the old ``SELECT 1`` reachability check and proves
#: two things in one round-trip: Postgres answers, **and** the holder's backend is still
#: there. ``0`` rows is :data:`LOST` — the fail-open case.
LIVENESS_SQL: Final = "SELECT count(*) FROM pg_stat_activity WHERE pid = :holder_pid"

#: How long :meth:`TestDbGuard.acquire` waits for the holder thread's first answer. One
#: connect plus one round-trip; generous, but bounded so a wedged Postgres reddens
#: instead of hanging the session.
ACQUIRE_TIMEOUT_S: Final = 20.0

#: How long :meth:`TestDbGuard.release` waits for the holder thread to unwind. A missed
#: join is printed as ``release=timeout``, never swallowed.
RELEASE_TIMEOUT_S: Final = 5.0


def validated_role(raw: str | None) -> str | None:
    """The role, or ``None`` when unset. Raises on anything that is set but malformed."""
    if raw is None or raw == "":
        return None
    if not _ROLE_RE.match(raw):
        raise RuntimeError(
            f"{ROLE_ENV}={raw!r} is not a valid role — expected {_ROLE_RE.pattern}. "
            "Refusing to continue: a typo here would silently mean 'no isolation', "
            "which is the one outcome this marker exists to prevent."
        )
    return raw


def role_from_env() -> str | None:
    """The validated role for this process, read once by ``tests/db_support``."""
    return validated_role(os.environ.get(ROLE_ENV))


def role_suffixed(url: str, role: str) -> str:
    """Append a validated ``role`` to the database name in ``url``.

    Pure. Composes with whatever name already resolved — the per-checkout digest or an
    explicit ``TEST_DATABASE_URL`` — because a dev box that pins the latter would
    otherwise leave the gate un-isolated with no signal (SD-1).
    """
    validated_role(role)
    parsed = make_url(url)
    # render_as_string(hide_password=False): str(URL) masks the password as "***",
    # which would corrupt the connection string.
    return parsed.set(database=f"{parsed.database}_{role}").render_as_string(hide_password=False)


def advisory_key(db_name: str) -> int:
    """A deterministic signed ``bigint`` for ``pg_try_advisory_lock(bigint)``.

    Computed in Python so the gate-side tests and the session agree without a Postgres
    round-trip, and printed in the token so a human can join it to ``pg_locks``.
    """
    return int.from_bytes(hashlib.sha256(db_name.encode()).digest()[:8], "big", signed=True)


def lock_halves(key: int) -> tuple[int, int]:
    """``(classid, objid)`` as ``pg_locks`` stores a bigint advisory key.

    Postgres splits the 64-bit key into two ``oid`` columns. Getting this wrong makes
    the CONTENDED path find no holder and report ``holder_pid=-`` forever — which reads
    exactly like a clean run, so it is derived here once and measured by AC-3.
    """
    unsigned = key & 0xFFFFFFFFFFFFFFFF
    return (unsigned >> 32) & 0xFFFFFFFF, unsigned & 0xFFFFFFFF


_HOLDER_SQL: Final = (
    "SELECT a.pid, a.application_name, a.backend_start "
    "FROM pg_locks l JOIN pg_stat_activity a ON a.pid = l.pid "
    "WHERE l.locktype = 'advisory' AND l.granted AND l.classid = $1 AND l.objid = $2"
)

_FOREIGN_SQL: Final = (
    "SELECT count(*) FROM pg_stat_activity WHERE datname = $1 AND pid <> pg_backend_pid()"
)


class TestDbGuard:
    """One session's claim on one test database, held for the session's lifetime.

    The holder lives on a **dedicated daemon thread running its own event loop** with a
    single raw ``asyncpg`` connection (SD-3). It has to: the suite builds a fresh
    ``NullPool`` engine per test so nothing holds a connection between tests, and
    pytest-asyncio gives each test its own loop — a lock parked on any of those would be
    released the moment that test ended. Everything this class exposes to the suite is
    **synchronous and thread-safe**; no per-test loop ever awaits the holder.
    """

    def __init__(self, test_url: str, role: str | None) -> None:
        parsed = make_url(test_url)
        self.db_name: str = parsed.database or ""
        self.role: str | None = role
        self.key: int = advisory_key(self.db_name)
        # Raw asyncpg wants a plain postgresql:// DSN, and the lock lives on the
        # maintenance database (SD-2) so it PRECEDES CREATE DATABASE and never sits on
        # the target a cleanup may want to drop.
        self._admin_dsn: str = parsed.set(
            drivername="postgresql", database="postgres"
        ).render_as_string(hide_password=False)

        self.state: str = NOT_NEEDED
        self.holder_pid: int | None = None
        self.foreign_backends: int = 0
        self.create_race: int = 0
        self.release_state: str = "-"
        self.error: str | None = None
        #: Populated only on CONTENDED — who is holding it, so the report names a pid to reap.
        self.holder_app: str | None = None
        self.holder_since: str | None = None

        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._stop: asyncio.Event | None = None
        self._answered = threading.Event()
        self._lock = threading.Lock()

    # ---------------------------------------------------------------- acquisition

    def application_name(self) -> str:
        return f"vero-pytest-guard pid={os.getpid()} role={self.role or '-'}"

    def acquire(self) -> str:
        """Take the lock (idempotent). Returns the outcome; never raises on contention.

        Acquisition is **lazy** (SD-4) — the first ``create_test_engine()`` of the
        session calls this. That keeps acquisition and the liveness check in one place,
        leaves a session that runs no DB test without a Postgres connection, and — the
        reason that decided it — stops the battery's own pytest children, which run no
        DB test, from becoming false second arrivers.
        """
        with self._lock:
            if self.state is not NOT_NEEDED:
                return self.state
            self._thread = threading.Thread(
                target=self._run, name="vero-test-db-guard", daemon=True
            )
            self._thread.start()

        if not self._answered.wait(timeout=ACQUIRE_TIMEOUT_S):
            self.state = ABSENT
            self.error = f"the guard thread did not answer within {ACQUIRE_TIMEOUT_S}s"
        return self.state

    def _run(self) -> None:
        loop = asyncio.new_event_loop()
        self._loop = loop
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._hold())
        except Exception as exc:  # pragma: no cover — the thread must never raise
            # An exception escaping here becomes a PytestUnhandledThreadExceptionWarning
            # that names the guard while saying nothing useful about the session. Record
            # it where the token can print it instead.
            self.error = f"holder thread: {type(exc).__name__}: {exc}"
        finally:
            # Never leave `_answered` unset: acquire() would then block for the full
            # timeout and report ABSENT for what was really a crash, hiding the cause.
            self._answered.set()
            loop.close()

    async def _hold(self) -> None:
        self._stop = asyncio.Event()
        try:
            conn = await asyncpg.connect(
                self._admin_dsn,
                server_settings={"application_name": self.application_name()},
            )
        except Exception as exc:
            self.state = ABSENT
            self.error = f"{type(exc).__name__}: {exc}"
            self._answered.set()
            return

        try:
            got = await conn.fetchval("SELECT pg_try_advisory_lock($1)", self.key)
            if got:
                self.state = ACQUIRED
                self.holder_pid = await conn.fetchval("SELECT pg_backend_pid()")
                self.foreign_backends = await conn.fetchval(_FOREIGN_SQL, self.db_name) or 0
            else:
                self.state = CONTENDED
                classid, objid = lock_halves(self.key)
                row = await conn.fetchrow(_HOLDER_SQL, classid, objid)
                if row is not None:
                    self.holder_pid = row["pid"]
                    self.holder_app = row["application_name"]
                    self.holder_since = str(row["backend_start"])
                self.foreign_backends = await conn.fetchval(_FOREIGN_SQL, self.db_name) or 0
            self._answered.set()

            if self.state is ACQUIRED:
                # Park until release(). The lock lives exactly as long as this backend.
                await self._stop.wait()
                try:
                    await conn.fetchval("SELECT pg_advisory_unlock($1)", self.key)
                except Exception as exc:
                    # 🔴 Expected on the LOST path and it must not raise. If the backend
                    # is gone, Postgres has ALREADY released the lock — that is the very
                    # property §4.3's liveness check relies on — so there is nothing left
                    # to unlock and the connection is in an unusable state. Recorded, not
                    # swallowed: the token prints it. Found by AC-5, which terminates the
                    # holder on purpose; before that test this path had never run.
                    self.error = (
                        f"unlock skipped ({type(exc).__name__}) — the holder backend was "
                        "already gone, which is how Postgres released the lock"
                    )
        finally:
            try:
                await conn.close()
            except Exception:  # pragma: no cover — a dead backend cannot close cleanly
                conn.terminate()

    # ---------------------------------------------------------------- release

    def release(self) -> None:
        """Drop the lock and join the holder thread within a bound.

        A missed join is recorded as ``release=timeout`` in the token rather than
        swallowed. Postgres is the backstop either way — the backend dies with the
        process, so a stuck holder can wedge nothing; the hazard runs the other way.
        """
        thread, loop, stop = self._thread, self._loop, self._stop
        if thread is None:
            self.release_state = "-"
            return
        if self.state is ACQUIRED and loop is not None and stop is not None:
            try:
                loop.call_soon_threadsafe(stop.set)
            except RuntimeError:  # pragma: no cover — loop already closed
                pass
        thread.join(timeout=RELEASE_TIMEOUT_S)
        self.release_state = "timeout" if thread.is_alive() else "clean"

    # ---------------------------------------------------------------- reporting

    def token(self, db_tests: int) -> str:
        """The one line printed at ``pytest_sessionfinish``, on every run.

        Values, never a verdict. ``foreign_backends`` is deliberately sourced separately
        from the lock's answer: the refused ``pg_try_advisory_lock`` says *whether*,
        while the count is a point-in-time measurement that can legitimately read ``0``
        under real contention because the other session's per-test engines are
        ``NullPool`` and may be between connections at that instant. A reader who sees
        ``CONTENDED holder_pid=12345 foreign_backends=0`` has learned something true
        about NullPool, not found a contradiction.
        """
        return (
            f"TEST-DB-GUARD db={self.db_name} role={self.role or '-'} key={self.key} "
            f"outcome={self.state} holder_pid={self.holder_pid if self.holder_pid else '-'} "
            f"foreign_backends={self.foreign_backends} create_race={self.create_race} "
            f"release={self.release_state} db_tests={db_tests}"
        )

    def contention_reason(self) -> str:
        """Why a second arriver is stopping, naming the pid a human can reap."""
        return (
            f"{self.token(0)} holder_app={self.holder_app or '-'} "
            f"holder_since={self.holder_since or '-'} — another pytest already holds "
            f"{self.db_name}. One pytest per test database: this session refuses to run "
            "rather than drop that one's schema mid-test. Wait for it, or give this "
            f"session its own database with {ROLE_ENV}=<role>."
        )

    def lost_reason(self, why: str) -> str:
        """🔴 The fail-OPEN witness. A guard that stopped guarding is not a clean run.

        The caller sets ``state = LOST`` before calling, so the token already carries
        ``outcome=LOST`` — it is not repeated here. A reason that says the same thing
        twice invites a reader to wonder which one is the real reading.
        """
        return (
            f"{self.token(0)} — {why}. The guard stopped guarding, so nothing after "
            "this point is protected; refusing to run unguarded rather than continuing "
            "and reporting a clean run."
        )
