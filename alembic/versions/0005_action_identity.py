"""action_identity — reactive-loop approver/executor identity

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-03

PLAN-0047 Step 1 (AC-1 identity recording): one merge-idempotent row per
executed reactive-loop action carrying the SERVER-resolved ``approved_by``
/ ``executed_by`` person_ids from the authn dependency. Hand-authored
engine-governance table like the ``pipeline_runs`` family — NOT part of
the generated energy ontology schema (the YAML→ORM parity suite scopes to
YAML tables only, so the generated ``recommended_action`` table stays
byte-pinned to the ontology). Nullable identity columns: a deployment may
run with ``api_auth_enabled=false``. Purely additive.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "action_identity",
        sa.Column("action_id", sa.Text(), primary_key=True),
        sa.Column("approved_by", sa.Text(), nullable=True),
        sa.Column("executed_by", sa.Text(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("action_identity")
