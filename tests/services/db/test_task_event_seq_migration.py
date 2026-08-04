"""Migration ``0025`` — a ``seq`` for the task-chain flip trail, proven on legacy rows.

Same shape as the ``0023`` test, and for the same reason: this migration backfills,
so asserting the column list would prove almost nothing. The interesting claim is
about VALUES — specifically that existing rows keep the answer they already give.

That claim is only worth testing if the fixture can distinguish a correct backfill
from a lazy one, so the legacy rows are adversarial on three axes at once:

* **Physical insert order disagrees** with ``(at, event_id)`` — the rows go in
  newest-first, so numbering by insertion would invert them.
* **Primary-key order disagrees** too — ``ev-x``/``ev-y``/``ev-z`` sort by id in
  exactly the reverse of their chronological order, so numbering by ``event_id``
  alone would also invert them.
* **An exact ``at`` tie** — ``ev-m`` and ``ev-n`` share an instant, so the backfill
  has to apply the same ``event_id`` tiebreak the pre-``0025`` reader applied, not
  just sort by ``at`` and hope.

The last assertion is the one that matters operationally: the migrated rows are fed
through the REAL ``chain_state`` and must reduce to the status the old reader
reduced them to. Column order is a proxy; the reduced status is the thing the nudge
sweep actually acts on.

DB-backed — SKIPS when Postgres is down; a skip is never satisfaction.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy import NullPool, select
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, create_async_engine

from services.api.config import settings
from services.db.repair_case_task import TASK_STATUS_DONE, RepairCaseTaskEvent
from tests.db_support import create_test_engine
from verticals.fleet_maintenance.task_chain import chain_state

_REPO_ROOT = Path(__file__).resolve().parents[3]

_TABLE = "repair_case_task_event"
_CASE = "case-legacy-tasks"
_T0 = datetime(2026, 7, 20, 3, 0, tzinfo=UTC)

#: ``(event_id, minutes after T0, status)`` in the order they are INSERTED —
#: deliberately not the order they must end up in. The expected ``seq`` order is
#: ``(at, event_id)``: ev-z, ev-y, ev-x, ev-m, ev-n.
_LEGACY_FLIPS: tuple[tuple[str, int, str], ...] = (
    ("ev-x", 10, "pending"),
    ("ev-z", 0, "pending"),
    ("ev-n", 20, "done"),
    ("ev-y", 5, "pending"),
    ("ev-m", 20, "pending"),
)

_EXPECTED_ORDER = ["ev-z", "ev-y", "ev-x", "ev-m", "ev-n"]


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
    """Write the pre-``0025`` fixture with raw SQL, at revision ``0024``.

    Raw SQL and not the ORM: ``RepairCaseTaskEvent`` already declares ``seq``, so an
    ORM insert here would either fail against the ``0024`` schema or — worse — quietly
    prove that ``create_all`` works, which is not the path production takes.

    ``tenant_id`` is stated explicitly because PLAN-0101 SD-1(b) put the stamp on the
    ORM column default rather than a ``server_default``, so a raw write has no layer
    to fall back on.
    """
    await conn.execute(
        sa.text(
            "INSERT INTO repair_case (case_id, truck_id, opened_by, opened_at, status, "
            "work_type, photos, tenant_id) VALUES (:cid, 'truck-07', 'somchai', :t, "
            "'open', 'breakdown', '[]'::jsonb, 'default')"
        ),
        {"cid": _CASE, "t": _T0},
    )
    await conn.execute(
        sa.text(
            f"INSERT INTO {_TABLE} (event_id, case_id, item_key, status, actor, at, "  # noqa: S608
            "tenant_id) VALUES (:eid, :cid, 'notify_garage', :status, 'person-may', :t, "
            "'default')"
        ),
        [
            {
                "eid": event_id,
                "cid": _CASE,
                "status": status,
                "t": _T0 + timedelta(minutes=offset),
            }
            for event_id, offset, status in _LEGACY_FLIPS
        ],
    )


async def test_0025_numbers_legacy_flips_in_the_old_readers_order() -> None:
    """Behavioural continuity: migrated rows reduce to the status they already did."""
    engine = await create_test_engine()
    await engine.dispose()

    to_0024 = _alembic("upgrade", "0024")
    assert to_0024.returncode == 0, f"alembic upgrade 0024 failed:\n{to_0024.stderr}"

    seed = create_async_engine(settings.test_database_url, poolclass=NullPool)
    try:
        async with seed.begin() as conn:
            await _seed_legacy_rows(conn)
    finally:
        await seed.dispose()

    to_head = _alembic("upgrade", "head")
    assert to_head.returncode == 0, f"alembic upgrade head failed:\n{to_head.stderr}"

    verify = create_async_engine(settings.test_database_url, poolclass=NullPool)
    try:
        async with verify.connect() as conn:
            by_seq = [
                row[0]
                for row in (
                    await conn.execute(
                        sa.text(f"SELECT event_id FROM {_TABLE} ORDER BY seq")  # noqa: S608
                    )
                ).all()
            ]
            by_old_reader = [
                row[0]
                for row in (
                    await conn.execute(
                        sa.text(f"SELECT event_id FROM {_TABLE} ORDER BY at, event_id")  # noqa: S608
                    )
                ).all()
            ]
            legacy_max_seq = (
                await conn.execute(sa.text(f"SELECT MAX(seq) FROM {_TABLE}"))  # noqa: S608
            ).scalar_one()

        # A flip written the way the POST handler writes it: ``seq`` left to the
        # database. This is also the oracle for the migration's ``setval`` — without
        # it the identity sequence still starts at 1 and this insert dies on
        # ``uq_repair_case_task_event_seq``.
        async with verify.begin() as conn:
            await conn.execute(
                sa.text(
                    f"INSERT INTO {_TABLE} (event_id, case_id, item_key, status, "  # noqa: S608
                    "actor, at, tenant_id) VALUES ('ev-fresh', :cid, 'notify_garage', "
                    "'done', 'person-tom', :t, 'default')"
                ),
                {"cid": _CASE, "t": _T0 + timedelta(minutes=30)},
            )

        # The claim that matters operationally, made through the REAL reducer rather
        # than through a column comparison: what the sweep would act on.
        async with AsyncSession(verify) as session:
            events = list(
                (
                    await session.execute(
                        select(RepairCaseTaskEvent).where(RepairCaseTaskEvent.case_id == _CASE)
                    )
                ).scalars()
            )
            reduced = chain_state(events)["notify_garage"]

        async with verify.connect() as conn:
            fresh_seq = (
                await conn.execute(
                    sa.text(
                        f"SELECT seq FROM {_TABLE} WHERE event_id = 'ev-fresh'"  # noqa: S608
                    )
                )
            ).scalar_one()
    finally:
        await verify.dispose()

    assert by_seq == by_old_reader == _EXPECTED_ORDER, (
        "the backfill must reproduce the pre-0025 reader's (at, event_id) order — "
        "insert order and primary-key order both disagree with it in this fixture"
    )
    assert fresh_seq > legacy_max_seq, "setval did not advance past the backfilled high-water mark"
    assert reduced.status == TASK_STATUS_DONE, "ev-fresh is the latest insert and it is done"
    assert reduced.actor == "person-tom"
    assert reduced.activated_at == _T0, "the FIRST flip in seq order is when the item entered"


async def test_0025_gives_seq_no_default_to_hide_behind() -> None:
    """Schema half: NOT NULL identity bigint, no column default, tenant-scoped unique."""
    engine = await create_test_engine()
    await engine.dispose()

    upgrade = _alembic("upgrade", "head")
    assert upgrade.returncode == 0, f"alembic upgrade head failed:\n{upgrade.stderr}"

    verify = create_async_engine(settings.test_database_url, poolclass=NullPool)
    try:
        async with verify.connect() as conn:
            column = (
                await conn.execute(
                    sa.text(
                        "SELECT data_type, is_nullable, column_default, is_identity "
                        "FROM information_schema.columns "
                        "WHERE table_name = :t AND column_name = 'seq'"
                    ),
                    {"t": _TABLE},
                )
            ).one()
            unique_def = (
                await conn.execute(
                    sa.text(
                        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                        "WHERE conname = 'uq_repair_case_task_event_seq'"
                    )
                )
            ).scalar_one()
    finally:
        await verify.dispose()

    assert tuple(column) == ("bigint", "NO", None, "YES")
    # PLAN-0101 SD-3: the pair, not a bare ``seq``. Asserted on the live constraint
    # rather than on the ORM so a migration/ORM divergence cannot pass.
    assert "tenant_id" in unique_def and "seq" in unique_def


async def test_0025_is_additive_only_proven_by_reversing_it() -> None:
    """Additive-only as an oracle, not as a docstring claim.

    The table is append-only and may hold live dev/demo rows, so the promise is that
    ``0025`` adds and never rewrites. The honest test is to run the reverse and see
    what is left — and the second half is the one that catches real mistakes: ``seq``
    must be GONE and every ``0024`` column must still be THERE. A downgrade that
    over-drops looks identical to a correct one until somebody runs it against data.

    Walking forward again is the third claim: dropping an identity column leaves its
    sequence and its unique constraint to Postgres to clean up, and if either
    survived the re-``upgrade`` would collide with the leftover.
    """
    engine = await create_test_engine()
    await engine.dispose()

    up = _alembic("upgrade", "head")
    assert up.returncode == 0, f"alembic upgrade head failed:\n{up.stderr}"
    down = _alembic("downgrade", "0024")
    assert down.returncode == 0, f"alembic downgrade 0024 failed:\n{down.stderr}"

    verify = create_async_engine(settings.test_database_url, poolclass=NullPool)
    try:
        async with verify.connect() as conn:
            remaining = {
                row[0]
                for row in (
                    await conn.execute(
                        sa.text(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_name = :t"
                        ),
                        {"t": _TABLE},
                    )
                ).all()
            }
    finally:
        await verify.dispose()

    assert "seq" not in remaining, "downgrade left 0025's column behind"
    assert {
        "event_id",
        "case_id",
        "item_key",
        "status",
        "actor",
        "at",
        "variant",
        "note",
        "tenant_id",
    } <= remaining, "downgrade over-dropped — it removed columns 0025 never added"

    again = _alembic("upgrade", "head")
    assert (
        again.returncode == 0
    ), f"the chain no longer walks forward after a downgrade — 0025 left residue:\n{again.stderr}"
