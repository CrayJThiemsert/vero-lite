"""PM import rows — the measured-then-confirmed staging table

Revision ID: 0015
Revises: 0014
Create Date: 2026-07-29

Creates ``pm_import_row`` (PLAN-0096 Step 9 / AC-10), matching the hand-authored ORM
``services/db/pm_import.py``. One row per proposed PM value per truck per imported
file; nothing downstream reads a row until a human moves it to ``confirmed`` (Q4:
the telematics figure is approximate, so a machine reading is a claim, not a fact).

``seq`` is ``BIGINT GENERATED ALWAYS AS IDENTITY``, not a timestamp. The
"which confirmed reading is current" question must not be answered by a wall clock:
the WSL2 clock has been measured stepping backwards, which is the same reason
``load_run`` refuses to order step results by ``created_at``. ``ALWAYS`` (rather than
``BY DEFAULT``) so no writer can supply a value and break monotonicity.

``truck_id`` is nullable and carries no foreign key: the fleet's ``truck`` table is
not in this database at all (the vertical's generated ORM is deliberately not
registered on ``Base.metadata`` — fleet objects are served by the synthetic adapter),
and a row naming an unrecognised plate is a normal onboarding event that must be kept
and rejected rather than refused at the schema.

Scope note: PLAN-0096's Out of Scope no longer forbids migrations — see the amended
entry there, ratified by Cray 2026-07-28. The ban still binds where it was aimed:
Step 5 added no ``PipelineRunStatus`` member and no migration.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pm_import_row",
        sa.Column("import_row_id", sa.Text(), primary_key=True),
        sa.Column(
            "seq",
            sa.BigInteger(),
            sa.Identity(always=True),
            nullable=False,
            unique=True,
        ),
        sa.Column("batch_id", sa.Text(), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("plate", sa.Text(), nullable=False),
        sa.Column("truck_id", sa.Text(), nullable=True),
        sa.Column("odometer_km", sa.Double(), nullable=True),
        sa.Column("last_service_odometer_km", sa.Double(), nullable=True),
        sa.Column("next_service_due_km", sa.Double(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("imported_by", sa.Text(), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_by", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_pm_import_row_batch_id", "pm_import_row", ["batch_id"])
    op.create_index("idx_pm_import_row_truck_status", "pm_import_row", ["truck_id", "status"])


def downgrade() -> None:
    op.drop_index("idx_pm_import_row_truck_status", table_name="pm_import_row")
    op.drop_index("idx_pm_import_row_batch_id", table_name="pm_import_row")
    op.drop_table("pm_import_row")
