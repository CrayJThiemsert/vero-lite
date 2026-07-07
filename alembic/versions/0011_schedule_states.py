"""schedule state — schedule_states

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-07

Adds the ADR-0028 SD-P5 / PLAN-0055 Step 2 schedule-state table: one row per
``schedule``-triggered procedure, holding the persisted cron + IANA tz + ``last_fired`` /
``next_fire`` the scheduler daemon (PLAN-0055 Phase B) recovers on restart (AC-7).
``(vertical, procedure_id)`` is unique — a procedure_id is unique only within a vertical.
Purely additive: the ontology (0001) + pipeline_runs (0002) tables are untouched.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "schedule_states",
        sa.Column("schedule_id", sa.Text(), primary_key=True),
        sa.Column("vertical", sa.Text(), nullable=False),
        sa.Column("procedure_id", sa.Text(), nullable=False),
        sa.Column("cron", sa.Text(), nullable=False),
        sa.Column("timezone", sa.Text(), nullable=False),
        sa.Column("last_fired", sa.DateTime(timezone=True)),
        sa.Column("next_fire", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "vertical", "procedure_id", name="uq_schedule_states_vertical_procedure"
        ),
    )


def downgrade() -> None:
    op.drop_table("schedule_states")
