"""Revision ``0024`` — the tenant key on every table, and every natural key
re-scoped to it (PLAN-0101 Step 5 / AC-3, ADR-0035 D7(ii)/(iii)/(vi)).

Three claims the revision makes, each with its own oracle here:

1. **Every mapped table gains ``tenant_id``, NOT NULL, with no default at any
   layer.** The absence of a default is the load-bearing half — PLAN-0101 SD-1
   ruled (b), a Python-side ORM default, precisely so that an unstamped write dies
   loudly instead of landing under a value nobody chose. Step 1.4 measured that
   neither ``alembic check`` nor ``--autogenerate`` can see a ``server_default``
   drift back in, so this file is the only thing that would ever notice.
2. **All twelve unique constraints carry ``tenant_id``**, including the one that
   changed shape: ``pm_import_row``'s column-level ``unique=True`` became the named
   composite ``uq_pm_import_row_seq``.
3. **It reverses cleanly.** Asserted by running the reverse and looking, in the
   shape ``test_0023_is_additive_only_proven_by_reversing_it`` established — the
   second half (nothing was OVER-dropped) is the one that catches real mistakes,
   because an over-dropping downgrade looks identical to a correct one until
   somebody runs it against data.
4. **It runs over a POPULATED ``audit_log``** — added 2026-08-04 (session 205)
   after the shipped revision was found unable to. Claims 1-3 were all proven
   against an EMPTY database, and that is exactly why the defect shipped green:
   ``audit_log_no_mutation`` is a ``FOR EACH ROW`` trigger, so it never fires on
   zero rows, and the original ``UPDATE audit_log SET tenant_id`` backfill was
   therefore never once executed against a row by this suite. One seeded row is
   the whole difference between a vacuous pass and a real one — the same
   agrees-with-itself-by-construction shape CLAUDE.md §8 exists to catch, in a
   migration fixture rather than in a mock.

DB-backed: SKIPS when Postgres is down (``create_test_engine``), and a skip is
never counted as satisfaction.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, create_async_engine

from services.api.config import settings
from services.db.audit_log import GENESIS_HASH, AuditLog, compute_row_hash, verify_chain
from tests.db_support import create_test_engine

_REPO_ROOT = Path(__file__).resolve().parents[3]

#: Fixed instant for the seeded chain — timestamptz round-trips microseconds
#: losslessly, which is what lets ``verify_chain`` recompute byte-identically.
_AUDIT_T0 = datetime(2026, 7, 20, 3, 0, tzinfo=UTC)

#: The twenty-one mapped tables, copied as a LITERAL rather than derived from
#: ``Base.metadata``. Deriving it would make this test agree with the ORM by
#: construction — it would pass even if the migration added the column to none of
#: them. The set-equality guard (AC-5) is what holds the ORM's own census honest;
#: this list is what holds the MIGRATION to it.
_TABLES = (
    "action_identity",
    "alert",
    "alert_event_link",
    "asset",
    "audit_log",
    "operational_event",
    "person",
    "pipeline_runs",
    "pm_import_row",
    "recommended_action",
    "repair_case",
    "repair_case_accepted_quote",
    "repair_case_closeout",
    "repair_case_justification",
    "repair_case_order_number",
    "repair_case_quote",
    "repair_case_run_link",
    "repair_case_task_event",
    "schedule_states",
    "site",
    "step_results",
)

#: ``constraint name -> the columns it must cover, in order`` — the FULL census at
#: head, which is why it outgrows the twelve 0024 itself re-scoped. Entries added by
#: a later revision are born tenant-scoped and never needed re-scoping; they are
#: listed here because this census is what stops an untenanted natural key appearing
#: anywhere in the schema, not only in 0024's diff.
_EXPECTED_UNIQUES = {
    "uq_audit_log_prev_hash": ["tenant_id", "prev_hash"],
    "uq_pm_import_row_seq": ["tenant_id", "seq"],
    "uq_repair_case_accepted_quote_seq": ["tenant_id", "seq"],
    "uq_repair_case_closeout_seq": ["tenant_id", "seq"],
    "uq_repair_case_justification_seq": ["tenant_id", "seq"],
    "uq_repair_case_order_number_no": ["tenant_id", "repair_order_no"],
    "uq_repair_case_order_number_year_seq": ["tenant_id", "year", "seq"],
    "uq_repair_case_quote_case_quote": ["tenant_id", "case_id", "quote_id"],
    "uq_repair_case_run_link_decision": [
        "tenant_id",
        "case_id",
        "run_id",
        "step_id",
        "outcome",
    ],
    "uq_repair_case_run_link_seq": ["tenant_id", "seq"],
    # Added by 0025 (the task-chain latest-wins fix), born tenant-scoped.
    "uq_repair_case_task_event_seq": ["tenant_id", "seq"],
    "uq_schedule_states_vertical_procedure": ["tenant_id", "vertical", "procedure_id"],
    "uq_step_results_seq": ["tenant_id", "seq"],
}

_TENANT_COLUMNS_SQL = sa.text("""
    SELECT table_name, is_nullable, column_default, is_identity
    FROM information_schema.columns
    WHERE column_name = 'tenant_id' AND table_schema = 'public'
""")

_UNIQUE_DEF_SQL = sa.text("""
    SELECT c.conname, pg_get_constraintdef(c.oid)
    FROM pg_constraint c
    JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname = 'public' AND c.contype = 'u'
""")

_ALL_COLUMNS_SQL = sa.text("""
    SELECT table_name, column_name FROM information_schema.columns
    WHERE table_schema = 'public'
""")


def _alembic(*args: str) -> subprocess.CompletedProcess[str]:
    """Run alembic against the DISPOSABLE test DB, never the dev database."""
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=_REPO_ROOT,
        env={**os.environ, "DATABASE_URL": settings.test_database_url},
        capture_output=True,
        text=True,
        check=False,
    )


async def test_0024_puts_a_defaultless_not_null_tenant_key_on_every_table() -> None:
    """Claim 1 — the column, on all twenty-one, NOT NULL, with nowhere to hide.

    ``column_default`` NULL **and** ``is_identity`` NO together are the assertion:
    they leave no layer a value could arrive from except an insert site stating it.
    A ``server_default`` added here later would be invisible to ``alembic check``
    (measured, PLAN-0101 Step 1.4) — this is the check that would see it.
    """
    engine = await create_test_engine()
    await engine.dispose()

    up = _alembic("upgrade", "head")
    assert up.returncode == 0, f"alembic upgrade head failed:\n{up.stderr}"

    verify = create_async_engine(settings.test_database_url, poolclass=NullPool)
    try:
        async with verify.connect() as conn:
            rows = (await conn.execute(_TENANT_COLUMNS_SQL)).all()
    finally:
        await verify.dispose()

    found = {row[0]: (row[1], row[2], row[3]) for row in rows}
    assert set(found) == set(_TABLES), (
        "tenant_id is not on exactly the expected tables — "
        f"missing={sorted(set(_TABLES) - set(found))} "
        f"unexpected={sorted(set(found) - set(_TABLES))}"
    )
    for table, (is_nullable, column_default, is_identity) in sorted(found.items()):
        assert is_nullable == "NO", f"{table}.tenant_id must be NOT NULL"
        assert column_default is None, (
            f"{table}.tenant_id has a column default ({column_default!r}) — SD-1(b) "
            "ruled the stamp Python-side so an unstamped write fails LOUDLY"
        )
        assert is_identity == "NO", f"{table}.tenant_id must not be an identity column"


async def test_0024_re_scopes_all_twelve_unique_constraints() -> None:
    """Claim 2 — every natural key carries the tenant, by NAME and by MEMBERSHIP.

    Reading ``pg_get_constraintdef`` rather than counting: a constraint could exist
    under the right name and cover the wrong columns, which a name-only check would
    bless. ``uq_pm_import_row_seq`` also proves the shape change landed — before
    0024 that key was an anonymous column-level ``unique=True`` named
    ``pm_import_row_seq_key`` by the server.
    """
    engine = await create_test_engine()
    await engine.dispose()

    up = _alembic("upgrade", "head")
    assert up.returncode == 0, f"alembic upgrade head failed:\n{up.stderr}"

    verify = create_async_engine(settings.test_database_url, poolclass=NullPool)
    try:
        async with verify.connect() as conn:
            rows = (await conn.execute(_UNIQUE_DEF_SQL)).all()
    finally:
        await verify.dispose()

    defs = {row[0]: row[1] for row in rows}
    assert set(defs) == set(_EXPECTED_UNIQUES), (
        f"unique-constraint census drifted — missing="
        f"{sorted(set(_EXPECTED_UNIQUES) - set(defs))} "
        f"unexpected={sorted(set(defs) - set(_EXPECTED_UNIQUES))}"
    )
    for name, columns in sorted(_EXPECTED_UNIQUES.items()):
        expected = f"UNIQUE ({', '.join(columns)})"
        assert defs[name] == expected, f"{name}: {defs[name]!r} != {expected!r}"

    assert "pm_import_row_seq_key" not in defs, (
        "the server-named column-level constraint survived — 0024 must REPLACE it "
        "with the named composite, not add alongside it"
    )


async def test_0024_reverses_cleanly_proven_by_reversing_it() -> None:
    """Claim 3 — the downgrade, as an oracle rather than as a docstring promise.

    Three halves, and the middle one catches the real mistakes: the tenant columns
    must be GONE; every pre-0024 column must still be THERE (an over-dropping
    downgrade is indistinguishable from a correct one until it meets data); and the
    chain must walk FORWARD again, which is what would catch a constraint or index
    left behind for the re-upgrade to collide with.
    """
    engine = await create_test_engine()
    await engine.dispose()

    up = _alembic("upgrade", "head")
    assert up.returncode == 0, f"alembic upgrade head failed:\n{up.stderr}"
    down = _alembic("downgrade", "0023")
    assert down.returncode == 0, f"alembic downgrade 0023 failed:\n{down.stderr}"

    verify = create_async_engine(settings.test_database_url, poolclass=NullPool)
    try:
        async with verify.connect() as conn:
            remaining = {(r[0], r[1]) for r in (await conn.execute(_ALL_COLUMNS_SQL)).all()}
            uniques = {r[0] for r in (await conn.execute(_UNIQUE_DEF_SQL)).all()}
    finally:
        await verify.dispose()

    added = {(table, "tenant_id") for table in _TABLES}
    assert added.isdisjoint(
        remaining
    ), f"downgrade left tenant_id behind on: {sorted(t for t, _ in added & remaining)}"

    # The over-drop half — one column per table, each the one whose loss the rest of
    # the subsystem would notice immediately.
    assert {
        ("audit_log", "prev_hash"),
        ("pm_import_row", "seq"),
        ("repair_case", "case_id"),
        ("repair_case_quote", "quote_id"),
        ("repair_case_order_number", "repair_order_no"),
        ("schedule_states", "procedure_id"),
        ("step_results", "run_id"),
    } <= remaining, "downgrade over-dropped a pre-0024 column"

    # The original names are back — including the server-assigned one, which the
    # downgrade has to restore under its OLD name or a re-upgrade finds nothing to
    # drop and dies.
    assert "pm_import_row_seq_key" in uniques
    assert "uq_pm_import_row_seq" not in uniques

    again = _alembic("upgrade", "head")
    assert (
        again.returncode == 0
    ), f"the chain no longer walks forward after a downgrade — 0024 left residue:\n{again.stderr}"


async def _seed_audit_chain(conn: AsyncConnection) -> list[tuple[str, str]]:
    """Two REAL chained audit rows at revision 0023, hashed with the real function.

    Hand-rolled hashes would let this fixture agree with itself: the point is that
    ``verify_chain`` — the actual tamper-evidence consumer — still passes AFTER the
    migration, and that is only meaningful if it would have passed before.
    """
    rows: list[tuple[str, str]] = []
    prev = GENESIS_HASH
    for index, action in enumerate(("run.start", "gate.decision")):
        occurred_at = _AUDIT_T0 + timedelta(seconds=index)
        payload = {"note": f"seed-{index}"}
        row_hash = compute_row_hash(
            prev_hash=prev,
            occurred_at=occurred_at,
            actor_person_id="person-may",
            action=action,
            run_id="run-1",
            step_id="gate",
            payload=payload,
        )
        await conn.execute(
            sa.text(
                "INSERT INTO audit_log (occurred_at, actor_person_id, action, run_id, "
                "step_id, payload, prev_hash, row_hash) VALUES (:t, 'person-may', "
                ":action, 'run-1', 'gate', CAST(:payload AS jsonb), :prev, :rh)"
            ),
            {
                "t": occurred_at,
                "action": action,
                "payload": json.dumps(payload),
                "prev": prev,
                "rh": row_hash,
            },
        )
        rows.append((prev, row_hash))
        prev = row_hash
    return rows


async def test_0024_migrates_a_populated_audit_log_without_breaking_its_chain() -> None:
    """Claim 4 — the one an empty database structurally cannot make.

    ``audit_log`` carries a ``BEFORE UPDATE ... FOR EACH ROW`` block trigger, so the
    three-phase backfill every other table uses is not merely slow there, it aborts
    the migration outright. With zero rows the trigger never fires, which is why the
    original revision passed this suite while being unable to migrate any real
    deployment. One seeded row is the entire difference.

    The oracle is ``verify_chain``, the real tamper-evidence consumer, not a column
    comparison: it recomputes every ``row_hash`` from stored fields and walks the
    ``prev_hash`` linkage, so it fails if the backfill altered anything hashed. The
    row count is asserted first because a walk over zero rows returns "intact"
    vacuously — the exact hole this test was written to close.
    """
    engine = await create_test_engine()
    await engine.dispose()

    to_0023 = _alembic("upgrade", "0023")
    assert to_0023.returncode == 0, f"alembic upgrade 0023 failed:\n{to_0023.stderr}"

    seed = create_async_engine(settings.test_database_url, poolclass=NullPool)
    try:
        async with seed.begin() as conn:
            seeded = await _seed_audit_chain(conn)
    finally:
        await seed.dispose()

    to_head = _alembic("upgrade", "head")
    assert to_head.returncode == 0, (
        "0024 could not migrate a populated audit_log — this is the shipped defect "
        f"(one row is enough to trigger it):\n{to_head.stderr}"
    )

    verify = create_async_engine(settings.test_database_url, poolclass=NullPool)
    try:
        async with verify.connect() as conn:
            stored = [
                (row[0], row[1], row[2])
                for row in (
                    await conn.execute(
                        sa.text(
                            "SELECT tenant_id, prev_hash, row_hash FROM audit_log "
                            "ORDER BY audit_id"
                        )
                    )
                ).all()
            ]
            default_after = (
                await conn.execute(
                    sa.text(
                        "SELECT column_default FROM information_schema.columns "
                        "WHERE table_name = 'audit_log' AND column_name = 'tenant_id'"
                    )
                )
            ).scalar_one()
        async with AsyncSession(verify) as session:
            walked = (
                await session.execute(
                    sa.select(sa.func.count())
                    .select_from(AuditLog)
                    .where(AuditLog.tenant_id == settings.tenant_id)
                )
            ).scalar_one()
            breaks = await verify_chain(session)
    finally:
        await verify.dispose()

    assert walked == 2, (
        "verify_chain walks only THIS tenant's rows, and over zero rows it reports "
        "'intact' vacuously — the backfilled tenant_id must match settings.tenant_id "
        "or the assertion below proves nothing"
    )
    assert breaks == [], f"the backfill broke the tamper-evident chain: {breaks}"
    # Byte-identical hashes: tenant_id is not among compute_row_hash's canonical
    # fields, so populating it must leave every stored hash untouched.
    assert [(prev, rh) for _tenant, prev, rh in stored] == seeded
    assert {tenant for tenant, _prev, _rh in stored} == {"default"}
    # The transient default did not survive — SD-1(b)'s requirement, on the one
    # table that had to reach it by a different route than the other twenty.
    assert default_after is None, (
        "audit_log.tenant_id kept a server_default — the DROP DEFAULT after the "
        "transient-default ADD COLUMN is what keeps SD-1(b) intact"
    )

    # Replayable WITH the rows still there. The revision's own comment claims a
    # future append-only table missing from _UPDATE_BLOCKED_TABLES would break this
    # "in exactly the way it did the first time" — that claim needs an oracle, and a
    # cycle run on an empty database would not be one.
    down = _alembic("downgrade", "0023")
    assert down.returncode == 0, f"downgrade over a populated audit_log failed:\n{down.stderr}"
    replay = _alembic("upgrade", "head")
    assert replay.returncode == 0, f"re-upgrade over a populated audit_log failed:\n{replay.stderr}"

    replayed = create_async_engine(settings.test_database_url, poolclass=NullPool)
    try:
        async with AsyncSession(replayed) as session:
            assert await verify_chain(session) == [], "the replay broke the chain"
    finally:
        await replayed.dispose()
