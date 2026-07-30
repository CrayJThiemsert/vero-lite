"""repair_case_accepted_quote — ใบที่ตกลง, the governed amount's provenance

Revision ID: 0019
Revises: 0018
Create Date: 2026-07-30

PLAN-0096 Step 8, on Cray's typed decisions (s191): the accepted quote is
referenced by a REQUIRED foreign key to a keyed quote row, and its ``reason`` is
required only when the accepted quote is not the cheapest on file.

**Why this table exists — it is the root cause behind two earlier gaps.** The DOA
ladder routes on the ฿ figure of a repair, and before this row nothing recorded
that figure at the moment it was agreed. ``repair_case_closeout.total_thb`` is
written after the work — i.e. after the gate it would have fed — and the evidence
pack's ``lowest_amount_thb`` is the cheapest quote, which is explicitly disclaimed
for the gate (``services/db/evidence_pack.py``) because an approved higher quote is
a normal governed outcome. The same absence forced migration ``0018``: nothing
recorded WHICH garage was used, so ``vendor`` had to be keyed a second time off the
invoice. An accepted quote answers both at once, since a quote row already carries
the amount and the vendor together.

**Two schema changes, not one.** The new table's ``quote_id`` is half of a
COMPOSITE foreign key onto ``(case_id, quote_id)``, which needs a unique constraint
on the parent to point at. ``repair_case_quote.quote_id`` is already the primary
key, so the pair is unique anyway and the constraint adds no new invariant to that
table — it exists purely to be a FK target. The payoff is that "case A accepted a
quote belonging to case B" becomes impossible in the schema rather than a check the
write path has to remember, which is the same discipline ``0017`` applied to the
repair-order number.

``reason`` is nullable here on purpose. Whether it is required depends on the OTHER
quote rows at the moment of acceptance — a fact no column-level CHECK can see — so
the rule is enforced at the write path and the column records the outcome.

No ``server_default`` anywhere: this table is new and empty, and a default would
exist only to invent values for rows that do not exist.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_repair_case_quote_case_quote", "repair_case_quote", ["case_id", "quote_id"]
    )
    op.create_table(
        "repair_case_accepted_quote",
        sa.Column("accepted_id", sa.Text(), primary_key=True),
        sa.Column("case_id", sa.Text(), sa.ForeignKey("repair_case.case_id"), nullable=False),
        sa.Column("quote_id", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("accepted_by", sa.Text(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_id", "quote_id"],
            ["repair_case_quote.case_id", "repair_case_quote.quote_id"],
            name="fk_repair_case_accepted_quote_quote",
        ),
    )
    op.create_index(
        "idx_repair_case_accepted_quote_case_id", "repair_case_accepted_quote", ["case_id"]
    )


def downgrade() -> None:
    op.drop_index("idx_repair_case_accepted_quote_case_id", table_name="repair_case_accepted_quote")
    op.drop_table("repair_case_accepted_quote")
    op.drop_constraint("uq_repair_case_quote_case_quote", "repair_case_quote", type_="unique")
