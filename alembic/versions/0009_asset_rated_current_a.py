"""add Asset.rated_current_a (PLAN-0049 Step 1 — energy-v1, SD-6)

Adds the PLAN-0049 Step-1 distinct current-rating property to ``asset`` so the DB
schema stays in parity with the ontology-generated DDL and the regenerated ORM
model (``services/db/models.py``). ``rated_current_a`` is the rated current in
amperes for current-rated assets (feeders, etc.) — distinct from ``capacity_kw``,
which misfits assets rated in A (partner-sim run-1 F9; SD-6). Nullable, purely
additive; ``DOUBLE PRECISION`` to match the generated ``capacity_kw`` column.

The v1 enum-value additions (``asset_type`` += feeder/cap_bank/gas_engine,
``measured_kind`` += current/voltage) and the new ``quantity_bindings`` need NO
migration: enums are stored as plain ``Text`` (their value space lives in the
generated CHECK + the application layer, like ``event_type`` / ``severity``), and
``quantity_bindings`` is ontology metadata, not a DB column.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("asset", sa.Column("rated_current_a", sa.Double()))


def downgrade() -> None:
    op.drop_column("asset", "rated_current_a")
