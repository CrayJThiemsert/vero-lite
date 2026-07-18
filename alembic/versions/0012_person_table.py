"""shared core person table

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-18

Creates the shared ``person`` table (ADR-0033 D5 / SD-I=(b), PLAN-0082 Step 4) —
the repo's FIRST ontology-object table outside the energy schema. Matches the
generated committed ORM ``services/db/person.py`` (the shared ``Person`` promoted
from the procedures spec layer to an ADR-0008 ontology object_type).

``roles`` persists as JSONB (ADR-0033 OQ-1=(a), Cray s149). The jsonb_array_length
CHECK is omitted here to match the generated ORM (like the enum-CHECK omission the
committed ORM already carries — the generated Pydantic layer is the load-bearing
min>=1 enforcement, ADR-0033 D3). The table ships EMPTY; runtime principal
resolution stays roster-fed — the population story is PLAN-0082 OQ-2.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "person",
        sa.Column("person_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("roles", postgresql.JSONB(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("person")
