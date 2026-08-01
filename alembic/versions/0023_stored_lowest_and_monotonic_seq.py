"""Store-at-write for the at-acceptance figure, and a monotonic ``seq`` for
latest-wins — PLAN-0099 Step 2 (D1 / D2 / D3).

Revision ID: 0023
Revises: 0022
Create Date: 2026-07-31

**Why.** Five reads in this subsystem decide *which row is current* — or *what the
cheapest quote was at one instant* — by comparing wall-clock timestamps. Measured
on the dev box over 528M samples across 300 s: ``datetime.now(UTC)`` steps
BACKWARDS 20 times, every step >= 400 ms, worst -592 ms. The acceptance-write ->
next-quote-write gap over 30 real HTTP round trips is 90-166 ms, so a backward
step swallows the whole window: ≈ 0.9 % of executions read the wrong row. That is
not a flaky test, it is a wrong audit answer at the same rate.

Two mechanisms, both additive:

1. **Store what is only cheaply true at write time.** The POST handler already
   computes the at-acceptance lowest quote correctly (no timestamp filter — measured
   immune) and then throws it away, leaving every reader to re-derive it from a
   clock that lies. ``lowest_amount_at_acceptance_thb`` persists it.
2. **Key "current" on insertion order, not on a clock.** ``seq`` is DB-assigned and
   strictly increasing, so a backward step can no longer make a superseded row look
   newest. A same-instant tie is genuinely ambiguous on a clock; under a backward
   step the operator's intent IS recoverable, because it is insertion order.

**``lowest_at_acceptance_basis`` — NOT NULL, no default at any layer** (Cray's SD-2
ruling, s196). Legacy rows are backfilled with the derived figure AND positively
marked ``'reconstructed'``. The reasoning is the ruling's: NULL says "not
captured"; a plain backfilled number speaks with FALSE AUTHORITY, which is strictly
worse for an audit trail; and storing a reconstructed guess as though it had been
recorded would contradict this migration's own thesis, that a recorded claim must
be true at the moment it was recorded. The absence of a default is the enforcement
mechanism — with one, a future insert site could omit provenance and have the
column quietly answer for it. Adding a default later is a governance change, not a
tidy-up.

Note what the backfill can and cannot buy. The reconstruction is the same
``entered_at <= accepted_at`` derivation this migration exists to retire, so it
inherits the same ~0.9 %-per-legacy-pair risk of naming the wrong quote. That risk
is not removed — it is DISCLOSED, at the point of reading, which is the difference
between a number an auditor can weigh and one that lies to them.

**Additive-only.** These tables are append-only and may hold live dev/demo rows.
Nothing existing is rewritten except the new columns' own values, and ``downgrade``
drops only what ``upgrade`` added.

**Why ``BY DEFAULT`` and not ``ALWAYS`` identity.** The backfill below has to write
explicit ``seq`` values, in each table's CURRENT reader's order, so that existing
data keeps the answer it already gives — behavioural continuity is the whole reason
this is one migration and not a behaviour change smuggled into one. ``ALWAYS``
would forbid that write. The UNIQUE constraint added afterwards is what makes the
looser identity safe: an explicit value can still be written, but never onto one
that already exists.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0023"
down_revision: str | None = "0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


#: ``(table, backfill order timestamp, primary key)`` — the ordering column is each
#: table's CURRENT reader's leading key, and the primary key is the deterministic
#: tiebreak. Ordering the backfill globally rather than per case/run is correct and
#: deliberate: a total order over ``(timestamp, pk)`` refines every per-case and
#: per-run order, so each group's relative sequence is preserved exactly.
_SEQ_TABLES: tuple[tuple[str, str, str], ...] = (
    ("repair_case_accepted_quote", "accepted_at", "accepted_id"),
    ("repair_case_closeout", "entered_at", "closeout_id"),
    ("repair_case_justification", "entered_at", "justification_id"),
    ("repair_case_run_link", "linked_at", "link_id"),
    ("step_results", "created_at", "step_result_id"),
)

#: The provenance vocabulary AS OF THIS REVISION. Deliberately a literal rather than
#: an import of ``services.db.repair_case_evidence.LOWEST_AT_ACCEPTANCE_BASES``: a
#: migration records what it did on the day it ran, and importing the live constant
#: would let a future edit to the application silently rewrite this revision's
#: meaning. The two are held in lockstep by the migration test, not by an import.
_BASIS_RECONSTRUCTED = "reconstructed"
_BASIS_CHECK = "lowest_at_acceptance_basis IN ('recorded', 'reconstructed')"

#: The reconstruction, stated once — PLAN-0099's "derive-once UNION {the accepted
#: quote itself}". ``entered_at <= accepted_at`` is the derivation being retired;
#: the ``OR q.quote_id = a.quote_id`` disjunct is the UNION half, and it is what
#: makes the result NON-NULL for every row: an acceptance carries a REQUIRED
#: composite FK to a quote of the same case, so that quote always satisfies the
#: predicate even when a backward clock step has pushed its ``entered_at`` past
#: ``accepted_at``. Without the disjunct an inverted legacy pair reconstructs to
#: NULL and the ``SET NOT NULL`` below fails — which is exactly the "``None`` on a
#: case that HAS an acceptance" shape PLAN-0099 AC-2 forbids, caught by the schema.
#:
#: S608 is suppressed here and below because every interpolated identifier comes
#: from ``_SEQ_TABLES`` / ``_BASIS_RECONSTRUCTED``, module-level literals in this
#: file. There is no caller, no parameter, and no runtime input to inject through.
_BACKFILL_FIGURE = f"""
    UPDATE repair_case_accepted_quote AS a
    SET lowest_amount_at_acceptance_thb = (
            SELECT MIN(q.amount_thb)
            FROM repair_case_quote AS q
            WHERE q.case_id = a.case_id
              AND (q.entered_at <= a.accepted_at OR q.quote_id = a.quote_id)
        ),
        lowest_at_acceptance_basis = '{_BASIS_RECONSTRUCTED}'
"""  # noqa: S608


def upgrade() -> None:
    # --- D1: the stored at-acceptance figure + its provenance -----------------
    #
    # Added nullable, backfilled, then tightened. Adding them NOT NULL outright
    # would need a DEFAULT for the existing rows, and a default on the basis column
    # is the one thing the SD-2 ruling forbids — it would let a reconstructed row
    # pass itself off as a record.
    op.add_column(
        "repair_case_accepted_quote",
        sa.Column("lowest_amount_at_acceptance_thb", sa.Numeric(14, 2), nullable=True),
    )
    op.add_column(
        "repair_case_accepted_quote",
        sa.Column("lowest_at_acceptance_basis", sa.Text(), nullable=True),
    )
    op.execute(_BACKFILL_FIGURE)
    op.alter_column("repair_case_accepted_quote", "lowest_amount_at_acceptance_thb", nullable=False)
    op.alter_column("repair_case_accepted_quote", "lowest_at_acceptance_basis", nullable=False)
    op.create_check_constraint(
        "ck_repair_case_accepted_quote_basis", "repair_case_accepted_quote", _BASIS_CHECK
    )

    # --- D2 + D3: the monotonic insertion key --------------------------------
    for table, order_col, pk in _SEQ_TABLES:
        op.add_column(table, sa.Column("seq", sa.BigInteger(), nullable=True))
        op.execute(
            f"""
            UPDATE {table} AS t
            SET seq = ordered.rn
            FROM (
                SELECT {pk} AS pk,
                       row_number() OVER (ORDER BY {order_col}, {pk}) AS rn
                FROM {table}
            ) AS ordered
            WHERE t.{pk} = ordered.pk
            """  # noqa: S608
        )
        op.alter_column(table, "seq", nullable=False)
        op.execute(f"ALTER TABLE {table} ALTER COLUMN seq ADD GENERATED BY DEFAULT AS IDENTITY")
        # The identity sequence is created starting at 1, which would collide with
        # every row the backfill just numbered. Advance it past the high-water mark;
        # ``is_called => false`` makes the next value exactly ``MAX(seq) + 1`` rather
        # than one beyond it, so the series stays gap-free from the very first insert.
        op.execute(
            f"""
            SELECT setval(
                pg_get_serial_sequence('{table}', 'seq'),
                COALESCE((SELECT MAX(seq) FROM {table}), 0) + 1,
                false
            )
            """  # noqa: S608
        )
        op.create_unique_constraint(f"uq_{table}_seq", table, ["seq"])


def downgrade() -> None:
    for table, _order_col, _pk in reversed(_SEQ_TABLES):
        op.drop_constraint(f"uq_{table}_seq", table, type_="unique")
        # Dropping the column takes its identity sequence with it — Postgres owns
        # that sequence and drops it with the column, so there is nothing left over
        # for a re-``upgrade`` to trip on.
        op.drop_column(table, "seq")

    op.drop_constraint(
        "ck_repair_case_accepted_quote_basis", "repair_case_accepted_quote", type_="check"
    )
    op.drop_column("repair_case_accepted_quote", "lowest_at_acceptance_basis")
    op.drop_column("repair_case_accepted_quote", "lowest_amount_at_acceptance_thb")
