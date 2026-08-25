"""Concurrent-writer coverage for two check-then-act paths (RR-3 residue, s195).

PLAN-0096 closed with **RR-3** named as a residual risk: its concurrency cells asserted
same-instant *ties* and last-write *ordering*, never a genuine concurrent race. Two paths
carried that gap, and they are NOT the same shape — which is the point of covering them
together:

* ``decide_pm_import`` was a real **production defect**. It read a row's status and then
  wrote it, on an UNLOCKED read, so two deciders could both observe ``proposed``, both
  pass the 409 guard, and the later commit would overwrite the earlier decision —
  stamping the loser's ``decided_by`` on a row someone else had already ruled on. Fixed
  in the same change as this test by making the decide path's read ``FOR UPDATE``; the
  guard's "idempotent by state" comment was true for a *replay* and false for a *race*.
* ``allocate_repair_order_no`` was a **test** gap only. Its production mechanism already
  existed and was already documented — a unique constraint rejects the loser of a
  ``MAX(seq) + 1`` tie, deliberately instead of a lock — but nothing exercised it, so
  "fails closed under a race" was a docstring claim and not a checked one. Exercising it
  immediately corrected the claim: the loser dies on ``uq_repair_case_order_number_no``,
  not on the ``(year, seq)`` constraint the docstring named (both would reject it; only
  one gets there first). That is the whole argument for checking a documented behaviour
  rather than trusting it.

Both cases open two real sessions against a real Postgres (skips without one) and force
the interleaving rather than hoping for it: a race test that merely runs two coroutines
and asserts the outcome can pass because the scheduler happened to serialize them, which
is exactly the vacuous shape RR-3 was raised about.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
import sqlalchemy as sa
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.api.auth import AuthContext
from services.api.models.pm import PmDecision, PmDecisionRequest
from services.api.routers.pm import _load_batch, decide_pm_import
from services.db.base import Base
from services.db.pm_import import PM_STATUS_CONFIRMED, PM_STATUS_PROPOSED, PmImportRow
from services.db.repair_case import RepairCase
from services.db.repair_case_closeout import RepairCaseOrderNumber, allocate_repair_order_no
from tests.db_support import create_test_engine, drop_all_bounded

_BATCH = "batch-race-01"
_ROW = "row-race-01"
_YEAR = 2026
#: The two constraints that make a duplicate order number impossible. Either rejecting
#: the loser is a correct fail-closed, so the assertion below accepts either — but it
#: asserts BY NAME rather than accepting any ``IntegrityError``, because
#: ``repair_case_order_number.case_id`` also carries a foreign key: an unseeded case
#: raises ``IntegrityError`` too, and a bare ``pytest.raises(IntegrityError)`` would go
#: green on a broken fixture while proving nothing about the race. Not hypothetical —
#: this test's first run failed exactly that way.
#:
#: **Which one actually fires: ``..._no``, not ``..._year_seq``.** They are checked in
#: declaration order (``repair_case_closeout.py:74-75``) and the formatted-number index
#: comes first, so the loser dies on the number rather than on ``(year, seq)``. The
#: allocator's docstring named the latter; corrected in the same change as this test.
_UNIQUENESS_CONSTRAINTS = (
    "uq_repair_case_order_number_no",
    "uq_repair_case_order_number_year_seq",
)
#: How long a blocked reader is given to prove it is actually blocked. Generous for a
#: local socket; the assertion is "still pending", so a slow machine makes this test
#: MORE likely to hold, never less.
_BLOCK_WINDOW_S = 0.5
#: Server-side bound on the review read. Only ever reached by a WRONG implementation —
#: the correct unlocked read never waits on a lock at all — so this is a failure-mode
#: bound, not a tolerance the passing path spends.
_LOCK_TIMEOUT_MS = 2000


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await drop_all_bounded(conn)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


def _proposed_row() -> PmImportRow:
    """One PM import row awaiting a human decision — the only state that is decidable."""
    return PmImportRow(
        import_row_id=_ROW,
        batch_id=_BATCH,
        row_number=2,
        plate="80-1234 กรุงเทพมหานคร",
        truck_id="truck-01",
        odometer_km=460_000.0,
        last_service_odometer_km=400_000.0,
        next_service_due_km=500_000.0,
        status=PM_STATUS_PROPOSED,
        imported_by="may",
        imported_at=datetime(2026, 7, 30, 3, 0, tzinfo=UTC),
    )


def _repair_case(case_id: str) -> RepairCase:
    """A closed-enough repair case for the order-number FK to resolve against."""
    return RepairCase(
        case_id=case_id,
        truck_id="truck-01",
        opened_by="may",
        opened_at=datetime(2026, 7, 30, 8, 0, tzinfo=UTC),
    )


def _decision(*, confirm: bool, actor: str) -> tuple[PmDecisionRequest, AuthContext]:
    request = PmDecisionRequest(
        decisions=[PmDecision(import_row_id=_ROW, confirm=confirm)], decided_by=actor
    )
    return request, AuthContext(person_id=actor, person=None)


async def test_the_decide_path_holds_a_row_lock_the_review_read_does_not(
    db_engine: AsyncEngine,
) -> None:
    """The lock is real, and it is scoped to the decide path.

    Two halves, because either alone would pass under a wrong implementation: a
    ``for_update`` read must BLOCK a second one (a missing lock fails the first half),
    and the default read must NOT (a lock pushed into ``_load_batch`` unconditionally,
    which would make the review GET contend with decisions, fails the second).

    **The second half bounds itself with Postgres' ``lock_timeout``, not
    ``asyncio.wait_for``, and that is deliberate.** Cancelling a coroutine parked inside
    asyncpg leaves the statement in flight on the server, so the session teardown then
    waits on the very lock the test was trying to escape and the whole run HANGS instead
    of failing. Measured: the unconditional-lock mutation hung this test under
    ``wait_for`` and reddens cleanly under ``lock_timeout``. A guard whose failure mode
    is a hung CI job reports nothing — the server-side abort keeps it a red test.
    """
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as seed:
        seed.add(_proposed_row())
        await seed.commit()

    async with maker() as holder, maker() as other:
        await _load_batch(holder, _BATCH, for_update=True)  # holds the row lock, uncommitted

        blocked = asyncio.create_task(_load_batch(other, _BATCH, for_update=True))
        try:
            await asyncio.sleep(_BLOCK_WINDOW_S)
            assert not blocked.done(), "second FOR UPDATE read was not blocked — no row lock held"

            async with maker() as reviewer:  # the unlocked review read sails past the lock
                await reviewer.execute(sa.text(f"SET LOCAL lock_timeout = '{_LOCK_TIMEOUT_MS}ms'"))
                rows = await _load_batch(reviewer, _BATCH)
                assert [r.import_row_id for r in rows] == [_ROW]
        finally:
            # Release the lock, THEN let the parked reader finish — in a finally, because
            # this is the difference between a hang and a report. A failing assertion
            # above would otherwise leave `other` closing its session with a statement
            # still in flight against a lock nobody released, and the run would hang with
            # no verdict at all. Measured: the unconditional-lock mutation hung here
            # until the unwind was made unconditional.
            await holder.commit()
            await asyncio.wait_for(blocked, timeout=5)  # released, not deadlocked


async def test_two_concurrent_decisions_cannot_both_win(db_engine: AsyncEngine) -> None:
    """The defect this fix exists for: a confirm and a decline racing on one row.

    The interleaving is forced, not hoped for. The decliner takes the lock first and is
    held open; the confirmer is launched and must block INSIDE its own locked read — the
    exact window where, unlocked, it would have read ``proposed`` and gone on to
    overwrite. Only when the decliner commits does the confirmer proceed, and it must
    then lose on the 409 rather than silently win.
    """
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as seed:
        seed.add(_proposed_row())
        await seed.commit()

    decline, decline_auth = _decision(confirm=False, actor="wirat")
    confirm, confirm_auth = _decision(confirm=True, actor="may")

    async with maker() as loser_session, maker() as winner_session:
        rows = await _load_batch(loser_session, _BATCH, for_update=True)
        rows[0].status = "rejected"
        rows[0].decided_by = "wirat"
        rows[0].decided_at = datetime.now(UTC)

        racer = asyncio.create_task(decide_pm_import(_BATCH, confirm, confirm_auth, winner_session))
        await asyncio.sleep(_BLOCK_WINDOW_S)
        assert not racer.done(), "the concurrent decider was not blocked by the locked read"

        await loser_session.commit()

        with pytest.raises(HTTPException) as excinfo:
            await asyncio.wait_for(racer, timeout=5)
        assert excinfo.value.status_code == 409

    # The decision that committed first is the one on the row — not the later writer's.
    async with maker() as check:
        row = await check.get(PmImportRow, _ROW)
        assert row is not None
        assert row.status == "rejected"
        assert row.decided_by == "wirat"
    assert decline.decisions[0].confirm is False  # the request that won, for the reader


async def test_concurrent_order_number_allocation_fails_the_loser_closed(
    db_engine: AsyncEngine,
) -> None:
    """``allocate_repair_order_no``'s documented race behaviour, exercised.

    Two close-outs in the same year compute the same ``MAX(seq) + 1`` because neither can
    see the other's uncommitted row. The docstring says the ``(year, seq)`` unique
    constraint rejects the loser — "deliberately not a lock" — and that is asserted here
    rather than trusted.

    **The loser blocks before it fails, and the test has to be written for that.** The
    second allocation's INSERT collides with an index entry the winner has written but not
    committed, so Postgres holds it until the winner's transaction resolves. Awaiting the
    two allocations sequentially therefore hangs forever rather than failing — which is
    how this test was first written, and it is a hang, not a red, so nothing would have
    reported it. The loser runs as a task, is asserted to be genuinely parked, and only
    then is the winner committed.
    """
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    now = datetime(2026, 7, 30, 9, 0, tzinfo=UTC)
    async with maker() as seed:
        seed.add_all([_repair_case("case-a"), _repair_case("case-b")])
        await seed.commit()

    async with maker() as s1, maker() as s2:
        first = await allocate_repair_order_no(s1, case_id="case-a", year=_YEAR, now=now)
        assert first.seq == 1  # computed against an empty series

        loser = asyncio.create_task(
            allocate_repair_order_no(s2, case_id="case-b", year=_YEAR, now=now)
        )
        await asyncio.sleep(_BLOCK_WINDOW_S)
        assert not loser.done(), "the colliding insert was not parked on the winner's key"

        await s1.commit()
        with pytest.raises(IntegrityError) as excinfo:
            await asyncio.wait_for(loser, timeout=5)
        # BY NAME: any IntegrityError would pass otherwise, including the foreign-key one
        # a missing seed raises — which would make this a test of the fixture, not the race.
        assert any(name in str(excinfo.value) for name in _UNIQUENESS_CONSTRAINTS)

    async with maker() as check:
        issued = list((await check.execute(sa.select(RepairCaseOrderNumber))).scalars().all())
        assert [(r.case_id, r.seq) for r in issued] == [("case-a", 1)]


async def test_a_retried_loser_gets_the_next_number_not_a_duplicate(
    db_engine: AsyncEngine,
) -> None:
    """The other half of "rejects the loser, whose transaction rolls back and retries".

    Asserting only that the loser fails would leave the recovery path unchecked — and a
    constraint that fails closed is worth little if the retry then allocates the same
    number again. After the winner commits, the retry must see the series move to 2.
    """
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    now = datetime(2026, 7, 30, 9, 0, tzinfo=UTC)
    async with maker() as seed:
        seed.add_all([_repair_case("case-a"), _repair_case("case-b")])
        await seed.commit()

    async with maker() as s1:
        await allocate_repair_order_no(s1, case_id="case-a", year=_YEAR, now=now)
        await s1.commit()

    async with maker() as retry:
        again = await allocate_repair_order_no(retry, case_id="case-b", year=_YEAR, now=now)
        await retry.commit()
        assert again.seq == 2
        assert again.repair_order_no.endswith("0002")

    async with maker() as check:
        rows = list(
            (
                await check.execute(
                    sa.select(RepairCaseOrderNumber).order_by(RepairCaseOrderNumber.seq)
                )
            )
            .scalars()
            .all()
        )
        assert [r.seq for r in rows] == [1, 2]  # gap-free, the property an auditor reads
        assert len({r.repair_order_no for r in rows}) == 2


async def test_a_confirmed_row_is_not_re_decidable_even_without_contention(
    db_engine: AsyncEngine,
) -> None:
    """The replay case the 409 guard already covered, kept explicit.

    The lock changed how the guard behaves under a RACE; it must not have changed the
    plain sequential replay, and a regression there would otherwise be invisible behind
    the concurrency cases above.
    """
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as seed:
        row = _proposed_row()
        row.status = PM_STATUS_CONFIRMED
        row.decided_by = "may"
        row.decided_at = datetime.now(UTC)
        seed.add(row)
        await seed.commit()

    confirm, auth = _decision(confirm=True, actor="may")
    async with maker() as session:
        with pytest.raises(HTTPException) as excinfo:
            await decide_pm_import(_BATCH, confirm, auth, session)
        assert excinfo.value.status_code == 409
