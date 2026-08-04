"""PLAN-0099 Step 2 / AC-6 — the 23rd revision, proven against real legacy rows.

Same shape as the ``0014`` test, with one difference that carries the whole point:
this migration does not merely ADD columns, it **backfills** them, so asserting the
column list would prove almost nothing. The interesting claims are about VALUES.

The fixture is therefore built at revision ``0022`` — through raw SQL, because the
ORM already carries the new columns — and ``0023`` is then run over it. Two of the
legacy rows are adversarial on purpose:

* **A quote that arrived after the acceptance.** ``case-legacy-a`` accepts a
  ฿45,500.50 quote and a cheaper ฿39,000.00 one lands five minutes later. The
  reconstruction must report 45,500.50; reporting 39,000.00 would mean the
  at-acceptance figure had been computed against today's quotes rather than the
  ones that existed then — the exact defect this revision retires.
* **An acceptance stamped BEFORE its own quote.** ``case-legacy-b`` is what a
  backward clock step leaves behind. Its quote's ``entered_at`` is one minute
  AFTER ``accepted_at``, so the ``entered_at <= accepted_at`` half of the
  reconstruction matches nothing at all. Only the UNION-with-the-accepted-quote
  disjunct saves it — and without that disjunct this test does not fail on an
  assertion, it fails on ``SET NOT NULL`` inside the migration, which is the
  strongest form the oracle could take.

DB-backed — SKIPS when Postgres is down; a skip is never satisfaction (AC-9).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy import NullPool
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from services.api.config import settings
from services.db.repair_case_evidence import (
    LOWEST_AT_ACCEPTANCE_BASES,
    LOWEST_AT_ACCEPTANCE_RECONSTRUCTED,
    RepairCaseAcceptedQuote,
)
from tests.db_support import create_test_engine

_REPO_ROOT = Path(__file__).resolve().parents[3]

#: Every table ``0023`` gives a ``seq``. Named here rather than imported from the
#: migration so that dropping a table from the migration's own list is a test
#: failure rather than a silently narrowed scope.
_SEQ_TABLES = (
    "repair_case_accepted_quote",
    "repair_case_closeout",
    "repair_case_justification",
    "repair_case_run_link",
    "step_results",
)

_T0 = datetime(2026, 7, 20, 3, 0, tzinfo=UTC)


def _alembic(*args: str) -> subprocess.CompletedProcess[str]:
    """Run alembic against the DISPOSABLE test database."""
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=_REPO_ROOT,
        env={**os.environ, "DATABASE_URL": settings.test_database_url},
        capture_output=True,
        text=True,
        check=False,
    )


async def _seed_legacy_rows(conn: AsyncConnection) -> None:
    """Write the pre-``0023`` fixture with raw SQL, at revision ``0022``.

    Raw SQL and not the ORM: the ORM classes already declare the new columns, so an
    ORM insert here would either fail against the ``0022`` schema or — worse — quietly
    prove that ``create_all`` works, which is not the path production takes.

    ``acc-a`` is inserted FIRST and sorts LAST by ``(accepted_at, accepted_id)``, so
    a backfill that numbered rows by physical or primary-key order would redden the
    continuity assertion instead of passing by luck.
    """
    await conn.execute(
        sa.text(
            "INSERT INTO repair_case (case_id, truck_id, opened_by, opened_at, status, "
            "work_type, photos) VALUES (:cid, 'truck-01', 'somchai', :t, 'open', "
            "'breakdown', '[]'::jsonb)"
        ),
        [{"cid": "case-legacy-a", "t": _T0}, {"cid": "case-legacy-b", "t": _T0}],
    )
    await conn.execute(
        sa.text(
            "INSERT INTO repair_case_quote (quote_id, case_id, vendor, amount_thb, "
            "entered_by, entered_at) VALUES (:qid, :cid, :vendor, :amt, 'may', :t)"
        ),
        [
            # The accepted one, and the only quote on file when it was accepted.
            {
                "qid": "q-a-first",
                "cid": "case-legacy-a",
                "vendor": "ส.เจริญยนต์",
                "amt": Decimal("45500.50"),
                "t": _T0,
            },
            # Cheaper, but it arrived AFTER the acceptance — it must not be counted.
            {
                "qid": "q-a-later-cheaper",
                "cid": "case-legacy-a",
                "vendor": "อู่ริมทางปากช่อง",
                "amt": Decimal("39000.00"),
                "t": _T0 + timedelta(minutes=10),
            },
            # Stamped one minute AFTER the acceptance that points at it — the shape a
            # backward clock step leaves on disk.
            {
                "qid": "q-b",
                "cid": "case-legacy-b",
                "vendor": "อู่ช่างเล็ก",
                "amt": Decimal("51000.00"),
                "t": _T0 + timedelta(minutes=1),
            },
        ],
    )
    await conn.execute(
        sa.text(
            "INSERT INTO repair_case_accepted_quote (accepted_id, case_id, quote_id, "
            "reason, accepted_by, accepted_at) VALUES (:aid, :cid, :qid, NULL, 'tom', :t)"
        ),
        [
            {
                "aid": "acc-a",
                "cid": "case-legacy-a",
                "qid": "q-a-first",
                "t": _T0 + timedelta(minutes=5),
            },
            {"aid": "acc-b", "cid": "case-legacy-b", "qid": "q-b", "t": _T0},
            # Same instant as ``acc-b`` — the primary-key tiebreak decides, and the
            # backfill has to apply the same tiebreak the current reader does.
            {"aid": "acc-b2", "cid": "case-legacy-b", "qid": "q-b", "t": _T0},
        ],
    )
    await conn.execute(
        sa.text(
            "INSERT INTO repair_case_run_link (link_id, case_id, run_id, step_id, "
            "outcome, linked_at) VALUES (:lid, 'case-legacy-a', 'run-1', 'gate', :o, :t)"
        ),
        [
            # The provisional decision, stamped LATER than the ratification that
            # supersedes it — AC-4(b)'s inversion, as legacy data.
            {"lid": "link-prov", "o": "provisional", "t": _T0 + timedelta(minutes=2)},
            {"lid": "link-ratified", "o": "ratified", "t": _T0 + timedelta(minutes=1)},
        ],
    )


async def test_0023_backfills_the_legacy_reading_and_marks_it_reconstructed() -> None:
    """The value claims: reconstruction, provenance, order continuity, monotonicity."""
    engine = await create_test_engine()
    await engine.dispose()

    to_0022 = _alembic("upgrade", "0022")
    assert to_0022.returncode == 0, f"alembic upgrade 0022 failed:\n{to_0022.stderr}"

    seed = create_async_engine(settings.test_database_url, poolclass=NullPool)
    try:
        async with seed.begin() as conn:
            await _seed_legacy_rows(conn)
    finally:
        await seed.dispose()

    # The migration under test. A reconstruction that came back NULL for the
    # inverted pair would abort here, inside ``SET NOT NULL``.
    to_head = _alembic("upgrade", "head")
    assert to_head.returncode == 0, f"alembic upgrade head failed:\n{to_head.stderr}"

    verify = create_async_engine(settings.test_database_url, poolclass=NullPool)
    try:
        async with verify.connect() as conn:
            backfilled = {
                row[0]: (row[1], row[2])
                for row in (
                    await conn.execute(
                        sa.text(
                            "SELECT accepted_id, lowest_amount_at_acceptance_thb, "
                            "lowest_at_acceptance_basis FROM repair_case_accepted_quote"
                        )
                    )
                ).all()
            }
            by_seq = [
                row[0]
                for row in (
                    await conn.execute(
                        sa.text("SELECT accepted_id FROM repair_case_accepted_quote ORDER BY seq")
                    )
                ).all()
            ]
            by_old_reader = [
                row[0]
                for row in (
                    await conn.execute(
                        sa.text(
                            "SELECT accepted_id FROM repair_case_accepted_quote "
                            "ORDER BY accepted_at, accepted_id"
                        )
                    )
                ).all()
            ]
            links_by_seq = [
                row[0]
                for row in (
                    await conn.execute(
                        sa.text("SELECT link_id FROM repair_case_run_link ORDER BY seq")
                    )
                ).all()
            ]
            legacy_max_seq = (
                await conn.execute(sa.text("SELECT MAX(seq) FROM repair_case_accepted_quote"))
            ).scalar_one()

        # A new acceptance written the way Step 3's POST handler will write it:
        # provenance stated explicitly, ``seq`` left to the database. This is also
        # the oracle for the migration's ``setval`` — without it the identity
        # sequence still starts at 1 and this insert dies on ``uq_..._seq``.
        async with verify.begin() as conn:
            await conn.execute(
                sa.text(
                    # ``tenant_id`` is stated because this is a RAW insert and PLAN-0101
                    # SD-1(b) put the stamp on the ORM column default, not on a
                    # server_default — so a raw write has no layer to fall back on and
                    # dies on NOT NULL. That is the ruling working, not a test needing a
                    # workaround: the same failure is what a forgotten stamp in
                    # production code would look like.
                    "INSERT INTO repair_case_accepted_quote (accepted_id, case_id, "
                    "quote_id, reason, accepted_by, accepted_at, "
                    "lowest_amount_at_acceptance_thb, lowest_at_acceptance_basis, "
                    "tenant_id) "
                    "VALUES ('acc-new', 'case-legacy-a', 'q-a-later-cheaper', NULL, "
                    "'tom', :t, 39000.00, 'recorded', 'default')"
                ),
                {"t": _T0 + timedelta(minutes=20)},
            )
        async with verify.connect() as conn:
            fresh_seq = (
                await conn.execute(
                    sa.text(
                        "SELECT seq FROM repair_case_accepted_quote WHERE accepted_id = 'acc-new'"
                    )
                )
            ).scalar_one()
    finally:
        await verify.dispose()

    assert backfilled == {
        # The cheaper quote arrived ten minutes later and is correctly excluded.
        "acc-a": (Decimal("45500.50"), LOWEST_AT_ACCEPTANCE_RECONSTRUCTED),
        # Both survive only through the UNION-with-the-accepted-quote disjunct:
        # their quote's ``entered_at`` is one minute after ``accepted_at``.
        "acc-b": (Decimal("51000.00"), LOWEST_AT_ACCEPTANCE_RECONSTRUCTED),
        "acc-b2": (Decimal("51000.00"), LOWEST_AT_ACCEPTANCE_RECONSTRUCTED),
    }
    # Behavioural continuity: existing data keeps the answer it already gave. The
    # fixture makes this non-trivial — insertion order and primary-key order both
    # disagree with it.
    assert by_seq == by_old_reader == ["acc-b", "acc-b2", "acc-a"]
    assert links_by_seq == ["link-ratified", "link-prov"]
    assert fresh_seq > legacy_max_seq


async def test_0023_leaves_the_provenance_column_with_no_default_to_hide_behind() -> None:
    """The schema half of the SD-2 ruling: NOT NULL, no default, closed vocabulary."""
    engine = await create_test_engine()
    await engine.dispose()

    upgrade = _alembic("upgrade", "head")
    assert upgrade.returncode == 0, f"alembic upgrade head failed:\n{upgrade.stderr}"

    verify = create_async_engine(settings.test_database_url, poolclass=NullPool)
    try:
        async with verify.connect() as conn:
            columns = {
                (row[0], row[1]): (row[2], row[3], row[4], row[5])
                for row in (
                    await conn.execute(
                        sa.text(
                            "SELECT table_name, column_name, data_type, is_nullable, "
                            "column_default, is_identity FROM information_schema.columns "
                            "WHERE table_name = ANY(:tables) AND column_name = ANY(:cols)"
                        ),
                        {
                            "tables": list(_SEQ_TABLES),
                            "cols": [
                                "seq",
                                "lowest_amount_at_acceptance_thb",
                                "lowest_at_acceptance_basis",
                            ],
                        },
                    )
                ).all()
            }
            check_clause = (
                await conn.execute(
                    sa.text(
                        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                        "WHERE conname = 'ck_repair_case_accepted_quote_basis'"
                    )
                )
            ).scalar_one()

        # The vocabulary is CLOSED, and it is closed by the database rather than by
        # the write path remembering. Asserted live, not by reading the DDL back: a
        # constraint that exists and does not fire is the same as no constraint.
        async with verify.begin() as conn:
            await conn.execute(
                sa.text(
                    # ``tenant_id`` stated on every raw insert past 0024 — see the note
                    # on the ``acc-new`` insert above.
                    "INSERT INTO repair_case (case_id, truck_id, opened_by, opened_at, "
                    "status, work_type, photos, tenant_id) VALUES ('case-ck', 'truck-01', "
                    "'somchai', :t, 'open', 'breakdown', '[]'::jsonb, 'default')"
                ),
                {"t": _T0},
            )
            await conn.execute(
                sa.text(
                    "INSERT INTO repair_case_quote (quote_id, case_id, vendor, amount_thb, "
                    "entered_by, entered_at, tenant_id) VALUES ('q-ck', 'case-ck', "
                    "'อู่ช่างเล็ก', 1000.00, 'may', :t, 'default')"
                ),
                {"t": _T0},
            )
        with pytest.raises(IntegrityError) as rejected:
            async with verify.begin() as conn:
                await conn.execute(
                    sa.text(
                        # ``tenant_id`` is supplied HERE for a reason beyond making the
                        # insert legal: without it this statement would still raise
                        # IntegrityError, but for NOT NULL rather than for the CHECK this
                        # test exists to prove — the assertion at the end of the test
                        # names the constraint precisely so that substitution cannot
                        # pass silently, and this keeps it from having to fire at all.
                        "INSERT INTO repair_case_accepted_quote (accepted_id, case_id, "
                        "quote_id, reason, accepted_by, accepted_at, "
                        "lowest_amount_at_acceptance_thb, lowest_at_acceptance_basis, "
                        "tenant_id) "
                        "VALUES ('acc-ck', 'case-ck', 'q-ck', NULL, 'tom', :t, 1000.00, "
                        "'derived', 'default')"
                    ),
                    {"t": _T0},
                )
    finally:
        await verify.dispose()

    for table in _SEQ_TABLES:
        assert columns[(table, "seq")] == (
            "bigint",
            "NO",
            None,
            "YES",
        ), f"{table}.seq must be a NOT NULL identity BIGINT with no column default"
    assert columns[("repair_case_accepted_quote", "lowest_amount_at_acceptance_thb")] == (
        # NUMERIC, not double precision — the money invariant, asserted.
        "numeric",
        "NO",
        None,
        "NO",
    )
    # The SD-2 ruling's requirement 2, as a schema fact: NOT NULL, ``column_default``
    # NULL, and not an identity column either — there is no layer left for a value to
    # come from except an insert site stating it.
    assert columns[("repair_case_accepted_quote", "lowest_at_acceptance_basis")] == (
        "text",
        "NO",
        None,
        "NO",
    )
    # ...and the ORM agrees, which is the half a database query cannot see.
    orm_basis = RepairCaseAcceptedQuote.__table__.c.lowest_at_acceptance_basis
    assert orm_basis.default is None and orm_basis.server_default is None

    # The migration writes the vocabulary as a frozen literal rather than importing
    # the application constant, deliberately — a migration records what it did on the
    # day it ran. This is the tripwire that keeps the two in lockstep anyway: widen
    # the constant without a new migration and it reddens here.
    assert set(re.findall(r"'([^']*)'", check_clause)) == set(LOWEST_AT_ACCEPTANCE_BASES)
    assert "ck_repair_case_accepted_quote_basis" in str(rejected.value)


async def test_0023_is_additive_only_proven_by_reversing_it() -> None:
    """Additive-only, as an oracle rather than as a claim in a docstring.

    These tables may hold live dev/demo rows, so the promise is that ``0023`` adds
    and never rewrites — and the honest test of that is to run the reverse and see
    what is left. Two halves, and the second is the one that catches real mistakes:
    the new columns must all be GONE, and every ``0022`` column must still be THERE.
    A downgrade that over-drops looks identical to a correct one until somebody runs
    it against data.

    Walking forward again afterwards is the third claim. Dropping an identity column
    leaves its sequence to Postgres to clean up, and a unique constraint likewise; if
    either survived, the re-``upgrade`` would collide with the leftover instead of
    silently appearing to work.
    """
    engine = await create_test_engine()
    await engine.dispose()

    up = _alembic("upgrade", "head")
    assert up.returncode == 0, f"alembic upgrade head failed:\n{up.stderr}"
    down = _alembic("downgrade", "0022")
    assert down.returncode == 0, f"alembic downgrade 0022 failed:\n{down.stderr}"

    verify = create_async_engine(settings.test_database_url, poolclass=NullPool)
    try:
        async with verify.connect() as conn:
            remaining = {
                (row[0], row[1])
                for row in (
                    await conn.execute(
                        sa.text(
                            "SELECT table_name, column_name FROM information_schema.columns "
                            "WHERE table_name = ANY(:tables)"
                        ),
                        {"tables": list(_SEQ_TABLES)},
                    )
                ).all()
            }
    finally:
        await verify.dispose()

    added = {(table, "seq") for table in _SEQ_TABLES} | {
        ("repair_case_accepted_quote", "lowest_amount_at_acceptance_thb"),
        ("repair_case_accepted_quote", "lowest_at_acceptance_basis"),
    }
    assert added.isdisjoint(
        remaining
    ), f"downgrade left 0023 columns behind: {sorted(added & remaining)}"
    # The over-drop half. One column per touched table, each the one whose loss the
    # rest of the subsystem would notice immediately.
    assert {
        ("repair_case_accepted_quote", "accepted_at"),
        ("repair_case_closeout", "total_thb"),
        ("repair_case_justification", "reason"),
        ("repair_case_run_link", "three_quote_basis"),
        ("step_results", "created_at"),
    } <= remaining

    again = _alembic("upgrade", "head")
    assert (
        again.returncode == 0
    ), f"the chain no longer walks forward after a downgrade — 0023 left residue:\n{again.stderr}"
