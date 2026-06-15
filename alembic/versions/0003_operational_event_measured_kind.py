"""add OperationalEvent.measured_kind (ADR-0021 / PLAN-0026 Phase A)

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-15

Adds the ADR-0021 ``measured_kind`` enum column to ``operational_event`` so the
DB schema stays in parity with the ontology-generated DDL and the ORM model
(``services/db/models.py``). Nullable — non-reading events (transition/alarm)
carry no metric kind. The enum value space is carried by the generated
``TEXT CHECK`` + the application layer; like the existing ``event_type`` /
``severity`` columns it is stored as plain ``Text`` here. Purely additive.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("operational_event", sa.Column("measured_kind", sa.Text()))


def downgrade() -> None:
    op.drop_column("operational_event", "measured_kind")
