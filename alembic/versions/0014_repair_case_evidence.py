"""repair-case quote evidence pack

Revision ID: 0014
Revises: 0013
Create Date: 2026-07-28

Creates ``repair_case_quote`` and ``repair_case_justification`` (PLAN-0096 Step 3 /
AC-4 data half), matching the hand-authored ORM
``services/db/repair_case_evidence.py``. Both hang off ``repair_case`` by foreign
key; both are append-only by convention (no update/delete path exists in the API).

``amount_thb`` is ``NUMERIC(14, 2)`` rather than double precision: this is the
figure the DOA ladder routes on downstream, and money on an authority threshold is
``Decimal`` end to end (PLAN-0078 byte-form discipline). 14 digits carries a ฿
figure far past any repair a truck can accrue.

Scope note: PLAN-0096's Out of Scope no longer forbids migrations — see the amended
entry there, ratified by Cray 2026-07-28 for Step 2's ``repair_case``. This revision
extends the same ratified surface. Step 5 still adds no migration and no
``PipelineRunStatus`` member (ADR-0034 D3/Alt-6).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "repair_case_quote",
        sa.Column("quote_id", sa.Text(), primary_key=True),
        sa.Column(
            "case_id",
            sa.Text(),
            sa.ForeignKey("repair_case.case_id"),
            nullable=False,
        ),
        sa.Column("vendor", sa.Text(), nullable=False),
        sa.Column("amount_thb", sa.Numeric(14, 2), nullable=False),
        sa.Column("entered_by", sa.Text(), nullable=False),
        sa.Column("entered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("attachment", postgresql.JSONB(), nullable=True),
    )
    op.create_index("idx_repair_case_quote_case_id", "repair_case_quote", ["case_id"])

    op.create_table(
        "repair_case_justification",
        sa.Column("justification_id", sa.Text(), primary_key=True),
        sa.Column(
            "case_id",
            sa.Text(),
            sa.ForeignKey("repair_case.case_id"),
            nullable=False,
        ),
        sa.Column("vendor", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("entered_by", sa.Text(), nullable=False),
        sa.Column("entered_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "idx_repair_case_justification_case_id", "repair_case_justification", ["case_id"]
    )


def downgrade() -> None:
    op.drop_index("idx_repair_case_justification_case_id", table_name="repair_case_justification")
    op.drop_table("repair_case_justification")
    op.drop_index("idx_repair_case_quote_case_id", table_name="repair_case_quote")
    op.drop_table("repair_case_quote")
