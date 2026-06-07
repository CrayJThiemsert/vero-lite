"""procedure runtime — pipeline_runs + step_results

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-07

Adds the additive PLAN-0019 Part A run-record tables (ADR-016 D2 / SD-A1):
``pipeline_runs`` + ``step_results`` (JSONB ``trigger_context`` / ``artifact`` /
``reasoning_trace`` / ``audit``; BIGINT ``duration_ms``). The energy ontology
tables (revision 0001) are untouched — this migration is purely additive.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pipeline_runs",
        sa.Column("run_id", sa.Text(), primary_key=True),
        sa.Column("procedure_id", sa.Text(), nullable=False),
        sa.Column("agent_id", sa.Text(), nullable=False),
        sa.Column("trigger_context", postgresql.JSONB()),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "step_results",
        sa.Column("step_result_id", sa.Text(), primary_key=True),
        sa.Column("run_id", sa.Text(), sa.ForeignKey("pipeline_runs.run_id"), nullable=False),
        sa.Column("step_id", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("duration_ms", sa.BigInteger()),
        sa.Column("artifact", postgresql.JSONB()),
        sa.Column("reasoning_trace", postgresql.JSONB()),
        sa.Column("audit", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_step_results_run_id", "step_results", ["run_id"])


def downgrade() -> None:
    op.drop_table("step_results")
    op.drop_table("pipeline_runs")
