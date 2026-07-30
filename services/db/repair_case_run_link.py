"""Which governed run decided which repair case (PLAN-0096 Step 8, build item 3).

The table that lets the month-end export fill AC-9's two approval columns —
วันที่อนุมัติ and ผู้อนุมัติ — for a real repair. Without it the only path from a
case to its approval is a full JSONB scan of every run's artifact, matching a
``case_id`` buried in an action's reasoning trace, with a string-vs-string amount
join as the fallback.

**Why a join table and not a ``run_id`` column on ``repair_case``.** Session 190
typed the scalar column; session 191 grounding refuted it on three measured
reasons, and each one is a way the scalar silently loses the answer:

1. A manual run is **re-fireable without limit** — ``POST /procedures/{id}/run``
   has no idempotency key and no in-flight guard. Fire the hero twice and one
   still-open case appears in run A and run B; a scalar column is last-write-wins,
   quietly overwriting the run that actually approved the spend.
2. **"The run that approved" is per-PROPOSAL, not per-run.** One run can approve
   one case and reject another in the same gate resolution
   (``action_step.py`` pairs each proposal with its own disposition). A run
   pointer cannot tell them apart; a row per (case, run, step) can.
3. The **provisional branch splits the moment in two** — the step lands
   ``RESOLVED_PROVISIONAL`` and ``ratify_gated_step`` completes it days later
   (ADR-0034 E-2). One value written at first resolve cannot express both.

**Append-only, like every other trail in this flow.** A ratification does not
UPDATE the provisional row; it adds a second row with its own ``outcome``, so the
export can show that a repair was authorised on the shoulder and signed for on
Tuesday — which is the whole point of the deferred-ratification mechanism. The
export reads the newest row per case; the earlier one stays visible.
"""

from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from services.db.base import Base

#: What a link row records about how the run treated this case. Closed set, and
#: deliberately NOT the step's status: a step is one thing, but a gate resolution
#: decides each proposal separately, so the outcome that matters to the export is
#: the one this CASE received.
LINK_OUTCOME_APPROVED = "approved"
LINK_OUTCOME_REJECTED = "rejected"
LINK_OUTCOME_PROVISIONAL = "provisional"
LINK_OUTCOME_RATIFIED = "ratified"
LINK_OUTCOME_REFUSED = "refused"
LINK_OUTCOMES = (
    LINK_OUTCOME_APPROVED,
    LINK_OUTCOME_REJECTED,
    LINK_OUTCOME_PROVISIONAL,
    LINK_OUTCOME_RATIFIED,
    LINK_OUTCOME_REFUSED,
)


class RepairCaseRunLink(Base):
    """One (case, run, step) decision. Append-only; newest row is the position.

    **Neither key carries a foreign key, and that is one decision, not two.** This
    row is written by a hook that fires AFTER the gate has committed, precisely so
    an audit convenience can never roll back a human's approval. A hard FK would
    reintroduce that coupling through the back door: the write would fail — noisily
    in the log, silently in the data — whenever the referent is not a row in this
    database.

    Both referents legitimately are not, and for different reasons. A run may be
    archived or pruned on its own lifecycle. And the **synthetic demo cases are real
    decisions about ids that were never inserted** — `case-demo-truck01-axle` exists
    only in the fixture, yet the gate genuinely resolves it, and an export demo that
    could not show approval columns for the demo rows would be showing the wrong
    product. Measured s191: with a `case_id` FK in place, every existing
    ratification test would have driven the hook into a fail-soft
    `ForeignKeyViolation` — recorded, but a link table that cannot record the demo
    is not one worth having.

    Both ids are still real ids and the export joins on them; what changes is only
    that a missing referent degrades the export rather than the gate.
    """

    __tablename__ = "repair_case_run_link"
    __table_args__ = (
        sa.Index("idx_repair_case_run_link_case_id", "case_id"),
        sa.Index("idx_repair_case_run_link_run_id", "run_id"),
        # One decision per (case, run, step, outcome). A gate driver that fired its
        # callback twice — a retry, a re-resolve of an already-resolved step — must
        # not double-count a case in the KPI, and the constraint says so rather than
        # asking the callback to be careful. A RATIFICATION is a different outcome
        # on the same three keys, so it still lands.
        sa.UniqueConstraint(
            "case_id", "run_id", "step_id", "outcome", name="uq_repair_case_run_link_decision"
        ),
    )

    link_id: Mapped[str] = mapped_column(sa.Text, primary_key=True)
    case_id: Mapped[str] = mapped_column(sa.Text, nullable=False)
    run_id: Mapped[str] = mapped_column(sa.Text, nullable=False)
    step_id: Mapped[str] = mapped_column(sa.Text, nullable=False)
    outcome: Mapped[str] = mapped_column(sa.Text, nullable=False)
    #: AC-9's "why did this pass sourcing?" — the ``three_quote_basis`` the gate
    #: ACTUALLY SAW, captured at the moment of decision (Cray, typed s193).
    #:
    #: It is stored rather than recomputed at report time because
    #: ``compute_three_quote`` says so in its own words: the basis is recorded
    #: "rather than recomputing it later against a threshold that may since have
    #: moved". A month-end export that re-derived it would answer last month's audit
    #: question with this month's threshold — and look completely filled in doing it,
    #: which is the failure mode a completeness KPI structurally cannot see.
    #:
    #: The value is not new information: it already rides the persisted step artifact
    #: inside the ingested event dict, in the same trace step the case id is read
    #: from. This column only makes it QUERYABLE — a report should not have to walk
    #: JSONB reasoning traces to answer a standing audit question.
    #:
    #: Nullable, because a proposal that is not case-derived carries no event and the
    #: demo fixtures legitimately have none. NULL means "no sourcing basis was
    #: recorded for this decision", which is a different fact from any of the four
    #: real bases and must stay distinguishable from them.
    three_quote_basis: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    linked_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
