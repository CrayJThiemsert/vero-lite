"""repair_case_run_link.three_quote_basis — AC-9's "why did this pass sourcing?"

Revision ID: 0022
Revises: 0021
Create Date: 2026-07-30

PLAN-0096 Step 8, build-order item 5 (the month-end export). AC-9's row content
names ``three_quote_basis`` and nothing in the schema could serve it: the basis was
stamped on the in-memory event and persisted in no column anywhere in the repo.

**Why a column and not a recomputation at report time** (Cray, typed s193 — option
(ก), with (ข) "accept recomputation and name it as residual risk" offered and
declined). ``compute_three_quote`` forbids the alternative in its own docstring: the
basis is recorded "rather than recomputing it later against a threshold that may
since have moved". The partner's ฿30,000 sourcing threshold is authored config and
expected to be revised after real cases; a month-end export that re-derived the
basis would answer last month's audit question with this month's threshold — and
present the answer as completely filled in, which is precisely the failure a
completeness KPI cannot see.

**The value is not new information.** It already rides the persisted step artifact,
inside the ingested event dict, in the same ``kind == "ontology_query"`` trace step
the case id is read from. This column only makes it QUERYABLE: a standing audit
question should not require a report to walk JSONB reasoning traces, and a JSONB
walk is not something an accountant's export can be asked to depend on.

**On the link table, not on the case.** The basis belongs to a DECISION, not to a
repair: it is what the gate saw at the moment it decided, and a case re-fired
through a second run can legitimately carry a different one. The link row is already
per (case, run, step, outcome), which is exactly that grain.

**Nullable, and NULL is meaningful.** A proposal that is not case-derived carries no
event, and the synthetic demo rows legitimately have none. NULL means "no sourcing
basis was recorded for this decision" — a different fact from any of the four real
bases, and one the export must be able to report as unanswered rather than guess.

Backfill is deliberately NOT attempted. The basis for an already-decided run IS
recoverable — it sits in that run's artifact — but recovering it would mean this
migration parsing reasoning traces, and a migration that interprets application
JSONB is a migration that breaks the first time the trace shape moves. Existing rows
stay NULL and read as unanswered, which is true: nothing recorded the basis in a
queryable form at the time. New decisions carry it from the moment the hook lands.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0022"
down_revision: str | None = "0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "repair_case_run_link",
        sa.Column("three_quote_basis", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("repair_case_run_link", "three_quote_basis")
