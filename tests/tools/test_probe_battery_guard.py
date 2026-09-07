"""AC-9 of PLAN-0120 — a probe-battery child that loses the test-DB guard credits nothing.

🔴 **What this file exists to make impossible.** The probe battery spawns one pytest per
probe (``_battery.py`` ``_make_pytest_runner``). Those children inherit the agent's
environment, so they resolve the *same* per-checkout test database the parent session is
already bound to, and before PLAN-0120 the second arriver simply dropped the first one's
schema mid-run. PLAN-0120's guard makes that arriver **exit** instead. AC-9 is the
consequence-side claim: when it does, the battery must not turn that infrastructure event
into a *credited* claim — because a credited claim is the driver saying "this assertion was
witnessed RED", i.e. the exact fabrication CLAUDE.md §8 exists to prevent.

⚠️ **Why this is not already covered by ``test_probe_battery_contention.py``.** That module
(PLAN-0121) pins the *classifier* against **synthetic** abort shapes — a fixture project
whose test calls ``pytest.exit(reason, returncode=75)`` with a hard-coded
``holder_pid=424242``. It never binds a database and no guard is ever held. This file
drives the **real seam** CLAUDE.md §8 requires: a real parent holding a real advisory lock
on a real Postgres, the real ``_make_pytest_runner``, a real child pytest on a real
DB-backed node, and the real classifier. A mock-fed suite agrees with itself by
construction; only this shape can tell you the guard and the battery still meet.

✎ **PLAN-0120's AC-9 names an outcome set this build measures to be stale —
``superseded by new info``, not ``was an error`` (CLAUDE.md §6).** AC-9's pass read was
pinned at s277 as ``outcome in {NO-TESTS, GREEN}``, and the reasoning recorded with it —
that the outcome conjunct could not be witnessed, because a child mutated into running
unguarded may itself report ``GREEN``, which is *inside* the accepted set — was
**correct against the classifier that existed then**. PLAN-0121 has since landed
(Complete, s282) and added :attr:`~tools.probe_battery.Outcome.ABORTED` for exactly this
shape: a child that ended before reaching a verdict. Under that classifier the accepted set
collapses to ``{ABORTED}``, ``WITNESSED`` falls outside it, and the conjunct s277 could not
witness **becomes witnessable**. The s277 reasoning is preserved rather than deleted: a
reader who finds this file asserting ``ABORTED`` where the PLAN says ``{NO-TESTS, GREEN}``
is looking at a premise that changed under the PLAN, not at a contradiction.

**One claim per test, and the order inside the contention test is load-bearing.** A pytest
run stops at the first failed assertion, so a mutation can only ever witness one of them.
``credited`` is asserted **first** and ``outcome`` second, which is what lets the two AC-9
probes separate:

* **9a** (the chokepoint's ``pytest.exit`` removed, so the child proceeds unguarded) — the
  child runs the mutation for real, reports ``WITNESSED``, and reddens **``credited``**.
  ``outcome`` is NOT-REACHED under it and is exempted as such, never claimed green.
* **9b** (the chokepoint's ``pytest.exit`` replaced by ``pytest.skip``) — the child reports
  ``SKIPPED``, so ``credited`` stays **green as the sibling** and **``outcome``** reddens.

🔴 **The probes mutate ``tests/db_support.py``, NOT ``tests/db_guard.py``** as AC-9's text
says. Measured: ``tests/db_guard.py`` contains no ``pytest.exit`` at all, and its own
docstring records why — ``_pytest.outcomes.Exit`` subclasses ``Exception``, so a bare
``except Exception`` swallows it and degrades the guard into a skip. Every guard-driven
exit therefore sits *outside* those blocks, in the ``tests/db_support.py`` chokepoint.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from pathlib import Path

import asyncpg
import pytest
import sqlalchemy as sa
from sqlalchemy.engine import make_url

from services.api.config import settings
from tests import db_guard, db_support
from tools.probe_battery import Battery, Outcome, Probe
from tools.probe_battery._battery import (
    _classify_probe,
    _index_claims,
    _make_pytest_runner,
    _terminating_signals,
)
from tools.probe_battery._outcome import CREDITING_OUTCOMES
from tools.probe_battery._snapshot import RunStore

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The value :func:`test_the_child_node_binds_the_database` asserts against, and the single
#: token the inner probe flips to make that child go genuinely RED.
#:
#: 🔴 It lives HERE, in this module, deliberately. The obvious alternative — mutate some
#: production symbol the child node depends on — would put the inner mutation in
#: ``tests/db_support.py``, which is the very file AC-9's own outer probes (9a/9b) mutate.
#: Two nested :class:`RunStore` instances would then snapshot and restore the same path,
#: and while each restores to the state *it* found, the inner probe's ``old`` text may not
#: even exist under the outer mutation. Keeping the inner mutation in a file no outer probe
#: touches makes the two levels independent by construction rather than by argument.
CHILD_EXPECTED_ROWS = 1

#: The node the battery child runs. It must reach a live engine — a node that skips for
#: want of Postgres never takes the guard, and this whole file would pass vacuously.
CHILD_NODE = "tests/tools/test_probe_battery_guard.py::test_the_child_node_binds_the_database"

#: A child pytest imports the whole conftest tree. Generous, but bounded: a regression must
#: redden rather than hang the suite.
CHILD_TIMEOUT_S = 300

#: Comfortably above one connect plus one round-trip, far below "forever".
OUTER_TIMEOUT_S = 60.0


def _admin_dsn() -> str:
    """The maintenance-DB DSN, derived the way the guard derives it (PLAN-0120 SD-2)."""
    return (
        make_url(settings.test_database_url)
        .set(drivername="postgresql", database="postgres")
        .render_as_string(hide_password=False)
    )


async def test_the_child_node_binds_the_database() -> None:
    """The node the battery child runs — and an ordinary DB test in its own right.

    Its only requirements are that it genuinely binds an engine (so the chokepoint in
    ``tests/db_support.py`` runs and the guard is taken or refused) and that it carries
    exactly one cheap, mutable assertion for the inner probe to flip.
    """
    eng = await db_support.create_test_engine()
    try:
        async with eng.connect() as conn:
            rows = await asyncio.wait_for(conn.scalar(sa.text("SELECT 1")), OUTER_TIMEOUT_S)
    finally:
        await eng.dispose()
    print(f"child_rows={rows} expected={CHILD_EXPECTED_ROWS}")
    assert rows == CHILD_EXPECTED_ROWS


@pytest.fixture
async def parent_guard() -> AsyncIterator[db_guard.TestDbGuard]:
    """Ensure the PARENT holds its lock before any child is spawned.

    Without this the contention case would be a race — the child might arrive first and
    *acquire*, and the test would report a clean run as evidence of a guard.
    """
    eng = await db_support.create_test_engine()
    await eng.dispose()
    guard = db_support.session_guard()
    assert guard.state == db_guard.ACQUIRED, guard.token(0)
    yield guard


@pytest.fixture
async def child_role() -> AsyncIterator[str]:
    """A role unique to this process, with the database it creates dropped afterwards.

    Cleanup is asserted rather than hoped for: a leaked ``…_b<pid>`` database per run would
    accumulate silently on the dev cluster.
    """
    role = f"b{os.getpid() % 100000}"
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


#: The mutation's ``old``/``new`` are ASSEMBLED rather than written out, and that is a
#: correctness requirement, not a style choice. :meth:`RunStore.apply` refuses any ``old``
#: that does not occur **exactly once** in the subject — and this module is its own subject,
#: so spelling the assignment out here as a literal would make it occur twice (the constant,
#: and the probe that names it) and the mutation would refuse. Measured, not foreseen: the
#: first run of this file failed with `the mutation's 'old' text occurs 2 times`.
_CONST = "CHILD_EXPECTED_ROWS"


def _child_probe() -> tuple[Probe, Battery]:
    """One probe pointing at :data:`CHILD_NODE`, and the battery that declares its claim."""
    probe = Probe(
        name="AC9",
        subject=Path("tests/tools/test_probe_battery_guard.py"),
        old=f"{_CONST} = 1",
        new=f"{_CONST} = 99",
        node_id=CHILD_NODE,
        expect_claim="test_the_child_node_binds_the_database|rows == CHILD_EXPECTED_ROWS|#0",
    )
    return probe, Battery(
        claim_sources=(REPO_ROOT / "tests" / "tools" / "test_probe_battery_guard.py",),
        probes=(probe,),
    )


def _run_child_through_the_battery(state_base: Path) -> tuple[Outcome, bool, str]:
    """Drive the REAL battery runner once and classify what came back.

    Mirrors ``_battery._run_one`` — mutate, run, classify, restore, in that order, always —
    rather than calling :func:`~tools.probe_battery.run_battery`, and that choice is not
    cosmetic. ``run_battery`` takes a :class:`~tools.probe_battery._lock.LockHandle` on the
    project root; called from inside a probe child of an outer battery on the same root, it
    would contend with its own parent and report a lock failure rather than the guard
    outcome this test is about. AC-9's text names ``_make_pytest_runner`` for that reason.

    The runner is called **synchronously**, on the main thread. Two consequences, both
    wanted: :func:`~tools.probe_battery._battery._terminating_signals` can genuinely install
    its handlers (a non-main thread cannot), and blocking this test's event loop is
    harmless — PLAN-0120 SD-3 puts the guard's holder on its own dedicated thread and loop,
    so the lock is not released by anything happening here.
    """
    probe, battery = _child_probe()
    store = RunStore.begin(REPO_ROOT, state_base)
    index = _index_claims(battery)
    subject = REPO_ROOT / probe.subject
    store.apply(subject, probe.old, probe.new)
    try:
        with _terminating_signals() as interrupts:
            runner = _make_pytest_runner(store, interrupts)
            record = runner(probe, REPO_ROOT, CHILD_TIMEOUT_S)
        classification = _classify_probe(probe, index, REPO_ROOT, record, CHILD_TIMEOUT_S)
    finally:
        # Non-negotiable: this mutation is on a REAL repo file. Without the restore the
        # working tree keeps a planted defect that every later test would run against.
        store.restore(subject)
    # The reason travels with the outcome deliberately. `ABORTED` alone says only "ended
    # without a verdict"; the reason carries the child's own last line, which is where the
    # `TEST-DB-GUARD … outcome=CONTENDED holder_pid=…` token shows WHY. Printing it is what
    # makes a disagreement one step to diagnose instead of a hunt (CLAUDE.md §8).
    return (
        classification.outcome,
        classification.outcome in CREDITING_OUTCOMES,
        classification.reason,
    )


async def test_a_battery_child_under_contention_never_credits_a_claim(
    parent_guard: db_guard.TestDbGuard,
    tmp_path: Path,
) -> None:
    """🔴 AC-9 — the safety claim, driven through the whole real seam.

    The child inherits this session's environment, so it resolves the same database the
    parent already holds the advisory lock on, is refused by the guard, and exits before it
    can reach the planted mutation. The battery must report that as an infrastructure event
    and credit nothing.

    ⚠️ Assertion order is load-bearing — see the module docstring. ``credited`` first
    (probe 9a's claim), ``outcome`` second (probe 9b's).
    """
    outcome, credited, reason = _run_child_through_the_battery(tmp_path / "state")
    print(f"outcome={outcome} credited={credited} holder_pid={parent_guard.holder_pid}")
    print(f"reason={reason!r}")
    assert credited is False
    assert outcome is Outcome.ABORTED


async def test_a_battery_child_with_its_own_role_reaches_a_verdict(
    parent_guard: db_guard.TestDbGuard,
    child_role: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """🟢 THE POSITIVE CONTROL, and the load-bearing one.

    Without it, a battery path that was simply broken — a bad node id, a child that cannot
    start, a classifier wired to a constant — would satisfy the test above perfectly:
    ``ABORTED`` and ``credited is False`` is also exactly what "nothing works" reports.

    Same probe, same node, same runner; the only difference is that the child carries its
    own :data:`~tests.db_guard.ROLE_ENV`, resolves a database of its own, acquires cleanly,
    and therefore *reaches* the planted mutation and goes RED on it. ``WITNESSED`` here is
    what makes the ``ABORTED`` above attributable to the guard and to nothing else.

    The role is set on this process's environment because the battery's ``_child_env`` is
    built from :data:`os.environ`; the parent's own guard is untouched by it, having been
    acquired before this test ran.
    """
    monkeypatch.setenv(db_guard.ROLE_ENV, child_role)
    outcome, credited, reason = _run_child_through_the_battery(tmp_path / "state")
    print(f"control outcome={outcome} credited={credited} role={child_role}")
    print(f"control reason={reason!r}")
    assert outcome is Outcome.WITNESSED
