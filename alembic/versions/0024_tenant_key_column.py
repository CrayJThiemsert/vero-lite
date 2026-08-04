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
    # --- D7(ii)/(iii): the column, in the measured-safe three-phase shape --------
    for table in _TABLES:
        op.add_column(table, sa.Column("tenant_id", sa.Text(), nullable=True))
    for table in _TABLES:
        op.execute(f"UPDATE {table} SET tenant_id = '{_BACKFILL_TENANT}'")  # noqa: S608
    for table in _TABLES:
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
