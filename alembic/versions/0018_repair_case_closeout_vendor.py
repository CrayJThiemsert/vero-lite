"""repair_case_closeout.vendor — AC-9's ผู้ขาย / อู่ column

Revision ID: 0018
Revises: 0017
Create Date: 2026-07-29

PLAN-0096 Step 8 / AC-9, columns 5 (ผู้ขาย / อู่) and 6 (รหัสผู้ขาย).

**Why this is a second migration rather than part of 0017.** 0017 was built after
grounding the gap at AC-9 column 3 (เลขที่ใบแจ้งซ่อม) — but without sweeping the
other fourteen columns against the schema first. The sweep, run immediately after,
found one more column with no source anywhere: the garage that actually did the
work. That is the same defect class the Step 8 amendment records for column 3, found
one step too late to ride the same migration.

**Why it cannot be derived.** ``RepairCaseQuote.vendor`` records who QUOTED and
``RepairCaseJustification.vendor`` records the sole source being justified; neither
says who was used. Matching a quote to the invoice by amount would be a guess —
quotes are pre-VAT, the invoice total is not, and an approved higher quote breaks
the match outright. เมย์ reads the garage name off the same piece of paper as the
tax-invoice number she is already keying.

``server_default`` is deliberately omitted: there are no rows yet (0017 shipped in
the same session and no close-out has been keyed in a real environment), so a
default would exist only to invent a vendor for rows that do not exist. NOT NULL
without a default is the honest shape, and it fails loudly if that assumption is
ever wrong.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("repair_case_closeout", sa.Column("vendor", sa.Text(), nullable=False))


def downgrade() -> None:
    op.drop_column("repair_case_closeout", "vendor")
