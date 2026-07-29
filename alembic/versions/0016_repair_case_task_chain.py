"""work_type + repair_case_task_event — the thin post-approval task-chain

Revision ID: 0016
Revises: 0015
Create Date: 2026-07-29

PLAN-0096 Step 6 / AC-7, amended 2026-07-29 from the partner's round-2 answers
(A1: the real chain is 8 steps — 4 mandatory, 4 conditional — with a per-step
SLA, not one timeout). Cray approved this migration the same day (typed).

Two changes, one step, one migration:

* ``repair_case.work_type`` — ``breakdown`` / ``pm`` / ``accident``. One column
  serving two consumers: the SLA variants (A1 gives แจ้งอู่ 30 minutes on a
  breakdown but 1 day on PM) and the month-end export's ประเภทงาน column (A2).
  ``server_default='breakdown'`` so every pre-existing case keeps meaning: all
  cases captured so far were breakdown-shaped, and a backfill that guessed
  anything else would be inventing history.

* ``repair_case_task_event`` — append-only flip rows for the checklist, the same
  trail discipline as the quote pack: current state is the LATEST row per
  (case, item); a correction is a new row; nothing is ever updated or deleted.
  AC-7's "actor + timestamp per flip" is therefore not a logging feature bolted
  onto mutable state — the flips ARE the state.

Item semantics (which keys exist, which are mandatory, what the SLAs are) live in
``verticals/fleet_maintenance/task_chain.py``, NOT here: the table stores what
happened; the fleet-side authored config says what it means. A second vertical
with a different chain reuses the table untouched.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "repair_case",
        sa.Column("work_type", sa.Text(), nullable=False, server_default="breakdown"),
    )
    op.create_table(
        "repair_case_task_event",
        sa.Column("event_id", sa.Text(), primary_key=True),
        sa.Column("case_id", sa.Text(), sa.ForeignKey("repair_case.case_id"), nullable=False),
        sa.Column("item_key", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("actor", sa.Text(), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("variant", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
    )
    op.create_index("idx_repair_case_task_event_case_id", "repair_case_task_event", ["case_id"])


def downgrade() -> None:
    op.drop_index("idx_repair_case_task_event_case_id", table_name="repair_case_task_event")
    op.drop_table("repair_case_task_event")
    op.drop_column("repair_case", "work_type")
