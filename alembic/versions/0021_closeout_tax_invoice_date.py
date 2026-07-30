"""repair_case_closeout.tax_invoice_date — AC-9 column 1, วันที่เอกสาร

Revision ID: 0021
Revises: 0020
Create Date: 2026-07-30

PLAN-0096 Step 8, build-order item 5 (the month-end export). AC-9's first column
is วันที่เอกสาร and nothing in the schema could fill it: the close-out record
carried `tax_invoice_no` but never the date printed beside it.

**Why not reuse `entered_at`** (Cray, typed s192 — the option was offered and
declined). `entered_at` is when เมย์ keyed the paperwork, which is routinely days
after the invoice date: a 28 July invoice keyed on 3 August would be exported as
an August document. That row would look completely filled in, so the KPI — which
counts completeness — could never flag it. A wrong date that passes every check
is worse than a blank one.

**A `Date`, not a `DateTime`.** The vendor's paper carries a calendar date and no
time. Storing a timestamp would invent an hour, and month-end boundaries would
then turn on a value nobody wrote down.

**Nullable**, exactly like `tax_invoice_no`: a repair can close before the invoice
arrives. The export reports that as an incomplete row — the honest answer, and the
thing the KPI exists to count.

Backfill is deliberately NOT attempted. Existing close-out rows have no recorded
invoice date, and deriving one from `entered_at` would manufacture precisely the
wrong-month rows this column exists to prevent. They stay NULL and read as
incomplete, which is true.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "repair_case_closeout",
        sa.Column("tax_invoice_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("repair_case_closeout", "tax_invoice_date")
