"""The tenant key on every table, and every natural key re-scoped to it —
PLAN-0101 Steps 3-5 (ADR-0035 D7(ii)/(iii)/(vi)).

Revision ID: 0024
Revises: 0023
Create Date: 2026-08-04

**Why now, when nothing needs it yet.** One deployment serves one customer out of
one database (ADR-0035's L4 frame), so every change here is a behavioural no-op
today. That is the point: Cray's SD-3 ruling took the cost now, against the Code
recommendation, so that the arrival of a second concurrently-hosted customer is a
configuration change rather than a migration over tables that will by then hold
production rows. A column added to an empty-ish dev database is cheap; the same
column added later, under load, with a NOT NULL backfill over real rows, is not.

**The measured-safe shape, three phases per column.** ``add_column(nullable=True)``
-> backfill -> ``alter_column(nullable=False)``. Adding a NOT NULL column in one
statement would have to invent a value for existing rows, which either fails or
requires a DEFAULT — and a DEFAULT is exactly what SD-1 ruled against (below).

**``audit_log`` is the one exception, and it is forced, not chosen (amended
2026-08-04, session 205).** That table carries the ``audit_log_no_mutation``
trigger from revision ``0007`` — ``BEFORE UPDATE OR DELETE ... FOR EACH ROW``,
raising ``audit_log is append-only`` — so phase two above is not merely
inadvisable there, it is *impossible*: the backfill aborts the whole migration
the moment the table holds a single row.

As first shipped, this revision therefore could not traverse ANY database with
audit history — which is every real deployment at pilot cutover. It passed CI
only because a row-level trigger never fires on zero rows and the fixture never
seeded one, so the failure was structurally invisible to the suite. Reproduced
deterministically offline with one seeded row before this amendment; the
regression test that seeds one is in ``tests/services/db/test_tenant_key_migration.py``.

The amendment gives ``audit_log`` a **transient** default instead:
``ADD COLUMN ... NOT NULL DEFAULT 'default'`` immediately followed by
``DROP DEFAULT``. Three properties make this the right shape rather than a
workaround:

* **No ``UPDATE`` is ever issued**, so the trigger never fires and the
  append-only guarantee is never even momentarily suspended. Disabling the
  trigger around a backfill would have opened a window in which the audit log
  was mutable — weakening precisely the tamper-evidence the table exists to
  provide, in the one table where that guarantee is the whole point.
* **SD-1(b) is satisfied, not bent.** The ruling forbids a *persistent*
  ``server_default`` that a future insert site could silently hide behind. This
  default does not survive the migration: the end state is NOT NULL with
  ``column_default`` NULL and ``is_identity`` NO, byte-identical to every other
  table here — which ``test_0024_puts_a_defaultless_not_null_tenant_key_on_every_table``
  already asserts for all twenty-one, and is the oracle for this claim.
* **The hash chain is untouched.** ``tenant_id`` is not among
  ``compute_row_hash``'s ``canonical_fields`` (``services/db/audit_log.py``), so
  populating it cannot invalidate a stored ``row_hash`` or break
  ``verify_chain``. Had it been hashed, no backfill of any shape would have been
  safe and the column would have needed a different design entirely.

Amending a shipped revision is against this codebase's own rule and was ratified
by Cray on that basis (session 205): no later revision can rescue ``0024``,
because ``0024`` blocks the chain before any successor is reached; and because
the revision never once ran to completion over audit data anywhere, there is no
recorded history being rewritten. On a database where it already succeeded the
amended path produces an identical end state, so re-running is a no-op.

**No ``server_default``, anywhere, deliberately (SD-1 ruling (b)).** The write stamp
is a Python-side column default in ``services/db/tenant.py``, which covers ORM *and*
Core inserts, so the session-seam bypass that would have justified a database-side
default does not exist. An unstamped write must fail NOT NULL **loudly** rather than
land under a value nobody chose.

That absence is asserted by tests rather than by tooling, and PLAN-0101 Step 1.4 is
why: measured on a throwaway database at head, with a positive control, ``alembic
check`` does **not** detect ``server_default`` drift (a new column IS detected, exit
255; a ``server_default`` present on the model and absent in the database is NOT,
exit 0) and ``--autogenerate`` emits a revision with ``pass`` in both directions. So
"no server_default" is a claim the migration tooling cannot check for anyone. If a
future revision adds one, only a test will catch it.

**Every unique constraint is re-scoped, all twelve (SD-3).** Widening a unique key
can only ever weaken it, never strengthen it, so none of these can reject a row the
old key accepted. Two families needed their own reasoning and got it in the PLAN:

* The six ``Identity``-backed ``seq`` keys now read ``(tenant_id, seq)``. The counter
  is per-TABLE, not per-tenant, so this is **not** a promise of gap-free per-tenant
  monotonicity — under a future shared database the tenants interleave one sequence
  and each tenant's view of ``seq`` is gap-ful. See ``services/db/tenant.py``.
* ``uq_audit_log_prev_hash`` becomes ``(tenant_id, prev_hash)``, which turns one
  global hash chain into one chain **per tenant**. Identical today under one database
  per deployment. The application's two reads of that chain — ``append_audit``'s head
  lookup and ``verify_chain``'s walk — are tenant-scoped in the same change, because
  a scoped walk over an unscoped head would report every tenant crossing as a break.

**``pm_import_row``'s key changes SHAPE, not just membership.** It was a column-level
``unique=True`` from revision 0015, which PostgreSQL named itself
``pm_import_row_seq_key`` (read from the live catalogue, not guessed from the
convention). It becomes an explicitly named composite ``uq_pm_import_row_seq``. The
old anonymous form is why a ``UniqueConstraint(`` census of this codebase returns 11
and looks complete.

**One foreign key moves with them, and it is not optional.**
``fk_repair_case_accepted_quote_quote`` references
``uq_repair_case_quote_case_quote``; a composite FK must match a unique constraint
EXACTLY, so widening the target without widening the FK makes PostgreSQL refuse the
table outright. It is dropped before its target and recreated after, now carrying
``tenant_id`` on both sides — which also makes a cross-tenant quote reference
impossible in the schema rather than merely discouraged in the write path.

**Additive and reversible.** ``downgrade`` restores every original constraint by its
original name (including the server-assigned ``pm_import_row_seq_key``) and drops
only what ``upgrade`` added.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0024"
down_revision: str | None = "0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


#: The value every pre-existing row is stamped with. A LITERAL, deliberately not an
#: import of ``settings.tenant_id``: a migration records what it did on the day it
#: ran, and reading the live setting would let a deployment's environment silently
#: rewrite this revision's meaning on a future re-run. PLAN-0101 puts backfilling
#: any other value out of scope — no existing deployment carries a non-default key.
_BACKFILL_TENANT = "default"

#: Tables whose rows cannot be UPDATEd at all, so the three-phase backfill above is
#: impossible and the transient-default path is used instead (see the docstring).
#: Membership is a schema fact, not a preference: a table belongs here iff it carries
#: a trigger blocking UPDATE. Today exactly one — ``audit_log``'s
#: ``audit_log_no_mutation`` from revision ``0007``. A future append-only table with
#: its own block trigger must be added here, or this revision stops being replayable
#: on a populated database in exactly the way it did the first time.
_UPDATE_BLOCKED_TABLES: frozenset[str] = frozenset({"audit_log"})

#: Every mapped table, in a fixed order so the migration is deterministic. Twenty-one:
#: the seven generated from ontology YAML plus the fourteen hand-written ones.
_TABLES: tuple[str, ...] = (
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

#: ``(old name, new name, table, columns AFTER tenant_id)`` for all twelve unique
#: constraints. Old and new names differ for exactly one entry — ``pm_import_row``,
#: whose column-level constraint PostgreSQL had named itself. The five ``*_seq``
#: constraints from revision 0023 keep their names; their membership widens.
_UNIQUES: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    (
        "uq_audit_log_prev_hash",
        "uq_audit_log_prev_hash",
        "audit_log",
        ("prev_hash",),
    ),
    (
        "pm_import_row_seq_key",
        "uq_pm_import_row_seq",
        "pm_import_row",
        ("seq",),
    ),
    (
        "uq_repair_case_accepted_quote_seq",
        "uq_repair_case_accepted_quote_seq",
        "repair_case_accepted_quote",
        ("seq",),
    ),
    (
        "uq_repair_case_closeout_seq",
        "uq_repair_case_closeout_seq",
        "repair_case_closeout",
        ("seq",),
    ),
    (
        "uq_repair_case_justification_seq",
        "uq_repair_case_justification_seq",
        "repair_case_justification",
        ("seq",),
    ),
    (
        "uq_repair_case_order_number_no",
        "uq_repair_case_order_number_no",
        "repair_case_order_number",
        ("repair_order_no",),
    ),
    (
        "uq_repair_case_order_number_year_seq",
        "uq_repair_case_order_number_year_seq",
        "repair_case_order_number",
        ("year", "seq"),
    ),
    (
        "uq_repair_case_quote_case_quote",
        "uq_repair_case_quote_case_quote",
        "repair_case_quote",
        ("case_id", "quote_id"),
    ),
    (
        "uq_repair_case_run_link_decision",
        "uq_repair_case_run_link_decision",
        "repair_case_run_link",
        ("case_id", "run_id", "step_id", "outcome"),
    ),
    (
        "uq_repair_case_run_link_seq",
        "uq_repair_case_run_link_seq",
        "repair_case_run_link",
        ("seq",),
    ),
    (
        "uq_schedule_states_vertical_procedure",
        "uq_schedule_states_vertical_procedure",
        "schedule_states",
        ("vertical", "procedure_id"),
    ),
    (
        "uq_step_results_seq",
        "uq_step_results_seq",
        "step_results",
        ("seq",),
    ),
)

#: The one composite FK whose target this revision widens. It must be dropped BEFORE
#: ``uq_repair_case_quote_case_quote`` and recreated AFTER, in both directions.
_FK_NAME = "fk_repair_case_accepted_quote_quote"
_FK_TABLE = "repair_case_accepted_quote"
_FK_TARGET = "repair_case_quote"
_FK_COLS_OLD = ["case_id", "quote_id"]
_FK_COLS_NEW = ["tenant_id", "case_id", "quote_id"]


def upgrade() -> None:
    # --- The UPDATE-blocked tables, via a transient default ----------------------
    #
    # One statement adds the column already populated for existing rows, and the
    # next takes the default away again. Postgres 11+ fills existing rows from the
    # catalogue rather than by rewriting them, so this is neither a table rewrite
    # nor a row mutation — the block trigger has nothing to fire on. The DROP is
    # what keeps SD-1(b) intact; see the docstring.
    for table in sorted(_UPDATE_BLOCKED_TABLES):
        op.execute(
            f"ALTER TABLE {table} ADD COLUMN tenant_id TEXT NOT NULL "
            f"DEFAULT '{_BACKFILL_TENANT}'"
        )
        op.execute(f"ALTER TABLE {table} ALTER COLUMN tenant_id DROP DEFAULT")

    # --- D7(ii)/(iii): the column, in the measured-safe three-phase shape --------
    backfilled = [table for table in _TABLES if table not in _UPDATE_BLOCKED_TABLES]
    for table in backfilled:
        op.add_column(table, sa.Column("tenant_id", sa.Text(), nullable=True))
    for table in backfilled:
        op.execute(f"UPDATE {table} SET tenant_id = '{_BACKFILL_TENANT}'")  # noqa: S608
    for table in backfilled:
        op.alter_column(table, "tenant_id", nullable=False)

    # --- D7(vi): every natural key re-scoped -------------------------------------
    # The FK comes off first: its target constraint is about to be dropped, and
    # PostgreSQL will not let a referenced unique constraint go while a foreign key
    # depends on it.
    op.drop_constraint(_FK_NAME, _FK_TABLE, type_="foreignkey")
    for old_name, new_name, table, cols in _UNIQUES:
        op.drop_constraint(old_name, table, type_="unique")
        op.create_unique_constraint(new_name, table, ["tenant_id", *cols])
    op.create_foreign_key(_FK_NAME, _FK_TABLE, _FK_TARGET, _FK_COLS_NEW, _FK_COLS_NEW)


def downgrade() -> None:
    op.drop_constraint(_FK_NAME, _FK_TABLE, type_="foreignkey")
    for old_name, new_name, table, cols in reversed(_UNIQUES):
        op.drop_constraint(new_name, table, type_="unique")
        # Restored under its ORIGINAL name — including the server-assigned
        # ``pm_import_row_seq_key``, so a re-``upgrade`` finds exactly what it expects
        # to drop rather than a name this revision invented.
        op.create_unique_constraint(old_name, table, list(cols))
    op.create_foreign_key(_FK_NAME, _FK_TABLE, _FK_TARGET, _FK_COLS_OLD, _FK_COLS_OLD)

    for table in reversed(_TABLES):
        op.drop_column(table, "tenant_id")
