"""audit_log — append-only, hash-chained governance audit surface

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-03

PLAN-0047 Step 5 (SD-3 ratified = yes-minimal): the ``audit_log`` table +
its append-only guards —

* a BEFORE UPDATE OR DELETE trigger that RAISES (binds even for the
  compose-default owner credential the dev box uses);
* the ``vero_audit_writer`` INSERT-only role (cluster-level, created
  idempotently, NOLOGIN — provisioned for the pilot cutover; switching the
  app's own connection credential is the item-6 deployment remainder);
* UNIQUE(prev_hash) — the hash chain is linear by construction.

The full audit framework (retention, export, external anchoring, PDPA
surface) stays ADR-011, gated on real partner data. Purely additive.
Downgrade drops the table + trigger + function but NOT the cluster-level
role (shared across databases).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("audit_id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_person_id", sa.Text(), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("run_id", sa.Text(), nullable=True),
        sa.Column("step_id", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("prev_hash", sa.Text(), nullable=False),
        sa.Column("row_hash", sa.Text(), nullable=False),
        sa.UniqueConstraint("prev_hash", name="uq_audit_log_prev_hash"),
    )
    op.create_index("idx_audit_log_run_id", "audit_log", ["run_id"])

    # Frozen copy of services/db/audit_log.py AUDIT_BLOCK_* (a shipped migration
    # never changes; the module constants exist for test fixtures).
    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit_log_block_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is append-only (PLAN-0047 Step 5) — % blocked', TG_OP;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_log_no_mutation
        BEFORE UPDATE OR DELETE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION audit_log_block_mutation();
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'vero_audit_writer') THEN
                CREATE ROLE vero_audit_writer NOLOGIN;
            END IF;
        END
        $$;
        """
    )
    op.execute("GRANT SELECT, INSERT ON audit_log TO vero_audit_writer")
    op.execute("GRANT USAGE ON SEQUENCE audit_log_audit_id_seq TO vero_audit_writer")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_log_no_mutation ON audit_log")
    op.execute("DROP FUNCTION IF EXISTS audit_log_block_mutation()")
    op.drop_index("idx_audit_log_run_id", table_name="audit_log")
    op.drop_table("audit_log")
    # The vero_audit_writer role is cluster-level/shared — deliberately retained.
