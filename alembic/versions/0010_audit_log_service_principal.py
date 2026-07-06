"""add audit_log.actor_service_principal_id (ADR-016 S2 / PLAN-0053 Phase B, AC-11)

Adds the never-null service actor of a service-triggered run to the tamper-evident
``audit_log`` (NULL on a human-triggered row). Nullable + purely additive; existing
rows are unaffected. The append-only mutation-block trigger (``audit_log.py`` —
``audit_log_no_mutation``) forbids UPDATE/DELETE, so this migration only ADDs a
column and never touches a stored row.

SD-2 (RATIFIED = omit-when-None): ``compute_row_hash`` includes the new field in the
canonical hash ONLY when non-None, so pre-migration rows (whose column is NULL)
recompute BYTE-IDENTICALLY to their stored hash and the tamper-evident chain never
needs a migration epoch boundary.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("audit_log", sa.Column("actor_service_principal_id", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("audit_log", "actor_service_principal_id")
