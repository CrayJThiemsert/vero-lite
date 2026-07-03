"""pipeline_runs governance_snapshot + governance_hash — per-run config pinning

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-03

PLAN-0047 Step 6 (AC-8): the resolved governance config (SoD constraints +
per-step governance surface incl. typed AT-2 content) is snapshotted onto
the run at start with its canonical sha256; resume/resolve recompute from
the caller-supplied procedure and FAIL CLOSED on mismatch — a mid-flight
DOA-ladder / SoD / rule edit can never silently govern an old run. Both
columns nullable: pre-0008 rows (and legacy library runs) carry no pin and
skip the check (backward compat). Purely additive.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("pipeline_runs", sa.Column("governance_snapshot", postgresql.JSONB()))
    op.add_column("pipeline_runs", sa.Column("governance_hash", sa.Text()))


def downgrade() -> None:
    op.drop_column("pipeline_runs", "governance_hash")
    op.drop_column("pipeline_runs", "governance_snapshot")
