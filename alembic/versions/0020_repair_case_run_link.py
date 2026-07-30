"""repair_case_run_link — which governed run decided which repair case

Revision ID: 0020
Revises: 0019
Create Date: 2026-07-30

PLAN-0096 Step 8, build-order item 3. The table AC-9's two approval columns
(วันที่อนุมัติ, ผู้อนุมัติ) are filled from for a real repair.

**A join table, not the scalar `run_id` on `repair_case` that session 190 typed.**
Three measured reasons, each a way the scalar loses the answer silently: a manual
run is re-fireable without limit so a scalar is last-write-wins; "the run that
approved" is per-PROPOSAL, not per-run, because one resolution can approve one
case and reject another; and the provisional branch splits the moment in two
(`RESOLVED_PROVISIONAL` now, `ratify_gated_step` days later, ADR-0034 E-2).

**Neither key carries a foreign key, deliberately — one decision, not two.** The
link is written by a hook that fires AFTER the gate has committed, precisely so an
audit convenience can never roll back a human's approval; a hard FK would
reintroduce that coupling through the back door. A run may be archived on its own
lifecycle, and the synthetic demo cases are real decisions about ids that were
never inserted (`case-demo-truck01-axle` exists only in the fixture, yet the gate
genuinely resolves it). Measured s191: with a `case_id` FK in place, every existing
ratification test would have driven the hook into a fail-soft
`ForeignKeyViolation`. Both ids are still real and the export joins on them; a
missing referent degrades the export instead of the gate.

The unique constraint is on the four decision keys rather than three: a
ratification is a genuinely different outcome on the same (case, run, step), so it
must still land, while a re-fired callback for the SAME outcome must not
double-count the case in the KPI.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "repair_case_run_link",
        sa.Column("link_id", sa.Text(), primary_key=True),
        sa.Column("case_id", sa.Text(), nullable=False),
        sa.Column("run_id", sa.Text(), nullable=False),
        sa.Column("step_id", sa.Text(), nullable=False),
        sa.Column("outcome", sa.Text(), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "case_id", "run_id", "step_id", "outcome", name="uq_repair_case_run_link_decision"
        ),
    )
    op.create_index("idx_repair_case_run_link_case_id", "repair_case_run_link", ["case_id"])
    op.create_index("idx_repair_case_run_link_run_id", "repair_case_run_link", ["run_id"])


def downgrade() -> None:
    op.drop_index("idx_repair_case_run_link_run_id", table_name="repair_case_run_link")
    op.drop_index("idx_repair_case_run_link_case_id", table_name="repair_case_run_link")
    op.drop_table("repair_case_run_link")
