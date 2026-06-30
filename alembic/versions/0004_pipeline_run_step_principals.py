"""pipeline_runs.step_principals — the SoD run-check principal map

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-30

Adds the additive PLAN-0044 (A1b Step 1) ``step_principals`` JSONB column to
``pipeline_runs``: the run-level ``{step_id -> person_id | None}`` map the
fail-closed principal-SoD run-check resolves against (ADR-0026 D4 / SD-2=(a)).
It records the REQUESTER half from the typed ``RunContext.principal`` ambient
resolution — NOT the untyped ``trigger_context`` blob (OQ-2). Nullable: every
non-SoD procedure leaves it empty, so the live check stays inert for them. The
energy ontology tables (revision 0001) and the run tables (revision 0002) are
otherwise untouched — purely additive.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("pipeline_runs", sa.Column("step_principals", postgresql.JSONB()))


def downgrade() -> None:
    op.drop_column("pipeline_runs", "step_principals")
