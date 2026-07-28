"""repair_case table — case capture from minute 1

Revision ID: 0013
Revises: 0012
Create Date: 2026-07-28

Creates the ``repair_case`` table (PLAN-0096 Step 2 / AC-3), matching the
hand-authored ORM ``services/db/repair_case.py``. A sidecar table like
``action_identity`` — NOT part of the generated energy ontology schema, so the
YAML→ORM parity suite is unaffected.

Scope note, recorded because the merged PLAN says otherwise. PLAN-0096's Out of
Scope carries "⊕ Any new PipelineRunStatus member or DB migration". That line is
marked ⊕ = drafter addition (the PLAN's own legend: unmarked items are LOCKED by
the dispatch, ⊕ items are Cowork's judgment), and its parenthetical cites ADR-0034
D3/Alt-6 — which is about the E-2 ratification status, i.e. Step 5. Cray was shown
the two readings and ratified the table + this migration for Step 2 (2026-07-28);
the PLAN's Out of Scope is amended in the same change. ADR-0034 D3/Alt-6 still
holds where it was aimed: Step 5 adds NO PipelineRunStatus member and NO migration
— Text status + JSONB audit suffice there.

``photos`` is JSONB with a ``'[]'`` server default so a row inserted without it is
an empty list rather than NULL — the API layer then never has to distinguish "no
photos" from "unknown".
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "repair_case",
        sa.Column("case_id", sa.Text(), primary_key=True),
        sa.Column("truck_id", sa.Text(), nullable=False),
        sa.Column("opened_by", sa.Text(), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("photos", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.create_index("idx_repair_case_truck_id", "repair_case", ["truck_id"])
    op.create_index("idx_repair_case_status", "repair_case", ["status"])


def downgrade() -> None:
    op.drop_index("idx_repair_case_status", table_name="repair_case")
    op.drop_index("idx_repair_case_truck_id", table_name="repair_case")
    op.drop_table("repair_case")
