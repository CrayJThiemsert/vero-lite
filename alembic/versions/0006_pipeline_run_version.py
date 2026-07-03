"""pipeline_runs.version — optimistic-lock column for the gate state machine

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-03

PLAN-0047 Step 3: SQLAlchemy ``version_id_col`` optimistic concurrency on
``pipeline_runs`` — every ORM UPDATE bumps + checks it, so concurrent
resolve/resume writers lose cleanly (``StaleDataError``) instead of
silently double-writing run state. ``server_default '1'`` backfills every
existing row. Purely additive.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "pipeline_runs",
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
    )


def downgrade() -> None:
    op.drop_column("pipeline_runs", "version")
