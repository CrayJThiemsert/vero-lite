"""repair_case_order_number + repair_case_closeout — the month-end export's source

Revision ID: 0017
Revises: 0016
Create Date: 2026-07-29

PLAN-0096 Step 8 / AC-9, on Cray's typed Decision A (s190: the repair-order number
is human-readable ``RC-<year>-<NNNN>``, reset per year, issued at ปิดงาน) and
Decision B (s189: the invoice quartet, keyed by เมย์ at ``close_case``, with 7% VAT
back-computation explicitly rejected).

Two tables because they are two different facts, and because one table does not
survive the append-only rule:

* ``repair_case_order_number`` — one row per case, ``case_id`` as the primary key.
  A repair cannot acquire a second number, and the key says so.
* ``repair_case_closeout`` — append-only keying rows, many per case. A correction
  is a new row; the export reads the latest.

Had the number lived on the keying row, a correction would either invent a second
number for one repair or be blocked by the very ``UNIQUE`` that stops two repairs
sharing one. Splitting them lets both invariants hold in the schema at once.

``vat_thb`` is nullable on purpose — a vendor who charges no VAT has no VAT line,
which the export must be able to distinguish from a VAT line of zero.

Money is ``Numeric(14, 2)`` throughout: these are the figures accounting reconciles
against paper, and a binary float there is a rounding defect with a delay fuse.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "repair_case_order_number",
        sa.Column(
            "case_id",
            sa.Text(),
            sa.ForeignKey("repair_case.case_id"),
            primary_key=True,
        ),
        sa.Column("repair_order_no", sa.Text(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("allocated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("repair_order_no", name="uq_repair_case_order_number_no"),
        # The allocator computes MAX(seq) + 1 without a lock; this is what makes a
        # concurrent double-allocation fail closed and retry rather than issue the
        # same number twice.
        sa.UniqueConstraint("year", "seq", name="uq_repair_case_order_number_year_seq"),
    )
    op.create_table(
        "repair_case_closeout",
        sa.Column("closeout_id", sa.Text(), primary_key=True),
        sa.Column("case_id", sa.Text(), sa.ForeignKey("repair_case.case_id"), nullable=False),
        sa.Column("tax_invoice_no", sa.Text(), nullable=True),
        sa.Column("amount_pre_vat_thb", sa.Numeric(14, 2), nullable=False),
        sa.Column("vat_thb", sa.Numeric(14, 2), nullable=True),
        sa.Column("total_thb", sa.Numeric(14, 2), nullable=False),
        sa.Column("entered_by", sa.Text(), nullable=False),
        sa.Column("entered_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_repair_case_closeout_case_id", "repair_case_closeout", ["case_id"])


def downgrade() -> None:
    op.drop_index("idx_repair_case_closeout_case_id", table_name="repair_case_closeout")
    op.drop_table("repair_case_closeout")
    op.drop_table("repair_case_order_number")
