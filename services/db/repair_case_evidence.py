"""Hand-authored quote-evidence tables (PLAN-0096 Step 3 / AC-4 data half).

This is the artifact that replaces the partner's actual three-quote process, which
he described in Q5 as **scrolling LINE, sometimes lost**. น้องเมย์ receives quotes as
PDFs, LINE-exported photos and photographs of paper, prints them, files them — and
when accounting asks two months later which vendors were compared, the answer is an
archaeology dig through a chat group. The pack makes "were three vendors compared?"
a COUNT instead of a search.

Three tables, not one, because they are three different facts:

* :class:`RepairCaseQuote` — a vendor quoted this much for this repair. Has money.
* :class:`RepairCaseJustification` — no comparison was possible and here is why
  (rare part, single vendor). Has no money; it is the E-3 evidence-ALTERNATIVE
  (ADR-0034), the other legitimate way past the sourcing rule.
* :class:`RepairCaseAcceptedQuote` — ใบที่ตกลง: which of the quotes was actually
  agreed to. Has no money of its own; it POINTS at the quote that carries it.

Conflating the first two into one table with a nullable amount would have made
``quote_count`` — the number Step 4's threshold reads — depend on remembering to
filter by a discriminator. A count that is one forgotten ``WHERE`` away from
counting justifications as quotes is exactly the wrong shape for a governance
signal.

**Why acceptance is a third table rather than a flag on the quote.** A flag would
have to be UPDATEd — set on one row, cleared on another when เมย์ changes her mind
— and these tables are append-only precisely so the trail cannot be quietly
rewritten. It would also permit two rows flagged at once, a state with no meaning.
A pointer row keeps the append-only rule and makes "we first agreed with อู่ A,
then switched to อู่ B" a readable history instead of a lost intermediate state.

**Append-only, both of them.** There is no update or delete path. The trail is
framed to the partner as PROTECTING ต้อม and วิรัช — evidence that their decisions
were sound — and a trail that can be quietly rewritten protects nobody. A correction
is a new row; the export reads the latest and the earlier one stays visible.

**Money is Numeric, never float.** The amount เมย์ types is what the DOA ladder will
route on downstream, and a binary-float ฿ figure on an authority threshold is the
defect the PLAN-0078 byte-form discipline exists to prevent.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from services.db.base import Base

#: How a row's ``lowest_amount_at_acceptance_thb`` came to be there (PLAN-0099 D1
#: §Provenance, on Cray's SD-2 ruling). Closed set, pinned by a CHECK constraint
#: rather than by convention — the whole point of the marker is that it cannot be
#: quietly widened into meaninglessness.
#:
#: ``recorded`` — the write path computed the figure at the instant of acceptance,
#: when it was trivially correct, and stored it. ``reconstructed`` — migration
#: ``0023`` derived it afterwards from the append-only quote rows, which is a good
#: guess and NOT a record: under a backward clock step the derivation can pick the
#: wrong quote, which is the defect PLAN-0099 exists to retire.
LOWEST_AT_ACCEPTANCE_RECORDED = "recorded"
LOWEST_AT_ACCEPTANCE_RECONSTRUCTED = "reconstructed"
LOWEST_AT_ACCEPTANCE_BASES = (
    LOWEST_AT_ACCEPTANCE_RECORDED,
    LOWEST_AT_ACCEPTANCE_RECONSTRUCTED,
)


class RepairCaseQuote(Base):
    """One vendor's quote for one repair case.

    ``attachment`` is a single JSONB metadata record (the same shape a case photo
    carries) whose bytes live on disk, and it is NULLABLE on purpose: เมย์ often
    keys the amount off a phone call or a LINE message before the paper arrives.
    Refusing the quote until a file exists would push her back to the notebook,
    which is the behaviour this table is meant to replace. A quote without an
    attachment is weaker evidence, and the export can say so — but it is still
    better than a quote nobody recorded.
    """

    __tablename__ = "repair_case_quote"
    __table_args__ = (
        sa.Index("idx_repair_case_quote_case_id", "case_id"),
        # Redundant against the primary key on its own — ``quote_id`` is already
        # unique, so ``(case_id, quote_id)`` cannot repeat. It exists to be a
        # FOREIGN KEY TARGET: it lets :class:`RepairCaseAcceptedQuote` carry a
        # composite FK, which makes "accepted a quote belonging to a different
        # case" impossible in the schema rather than a check application code has
        # to remember. Same discipline as ``repair_case_order_number``'s keys —
        # state the invariant as a constraint, not as a comment asking future code
        # to be careful.
        sa.UniqueConstraint("case_id", "quote_id", name="uq_repair_case_quote_case_quote"),
    )

    quote_id: Mapped[str] = mapped_column(sa.Text, primary_key=True)
    case_id: Mapped[str] = mapped_column(
        sa.Text, sa.ForeignKey("repair_case.case_id"), nullable=False
    )
    vendor: Mapped[str] = mapped_column(sa.Text, nullable=False)
    #: Typed by เมย์ (Q15 — OCR is assistive at most, never the source of record).
    amount_thb: Mapped[Decimal] = mapped_column(sa.Numeric(14, 2), nullable=False)
    entered_by: Mapped[str] = mapped_column(sa.Text, nullable=False)
    entered_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    note: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    # ``none_as_null=True`` is load-bearing, not tidiness. SQLAlchemy's JSONB
    # default renders Python ``None`` as the JSON value ``null``, which is NOT SQL
    # NULL — so a quote with no document would satisfy ``attachment IS NOT NULL``
    # while Python read it back as ``None``. Measured on the dev DB: three rows,
    # one without a document, and all three reported ``attachment IS NULL = false``.
    # The Python-side pack was right; any SQL asking "which quotes are missing their
    # paperwork" would have silently returned nothing, and Step 8's export is
    # exactly that query.
    attachment: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB(none_as_null=True), nullable=True
    )


class RepairCaseJustification(Base):
    """A written reason why this repair could not be three-quote compared.

    The partner's Q10 answer named this himself: a rare part or a single vendor gets
    a written justification instead of a comparison. ADR-0034 D4 models it as the
    evidence-ALTERNATIVE rather than a waiver — the sourcing rule is not relaxed, it
    is satisfied a different way, which is why this is a first-class row and not a
    flag on the gate.

    ``vendor`` is the sole source being justified. ``reason`` is free text in the
    operator's own words; nothing parses it, and nothing should — it exists to be
    read by a human answering an audit question two months later.
    """

    __tablename__ = "repair_case_justification"
    __table_args__ = (
        sa.Index("idx_repair_case_justification_case_id", "case_id"),
        sa.UniqueConstraint("seq", name="uq_repair_case_justification_seq"),
    )

    justification_id: Mapped[str] = mapped_column(sa.Text, primary_key=True)
    case_id: Mapped[str] = mapped_column(
        sa.Text, sa.ForeignKey("repair_case.case_id"), nullable=False
    )
    vendor: Mapped[str] = mapped_column(sa.Text, nullable=False)
    reason: Mapped[str] = mapped_column(sa.Text, nullable=False)
    entered_by: Mapped[str] = mapped_column(sa.Text, nullable=False)
    entered_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    #: Insertion order, assigned by the database (PLAN-0099 D2 / SD-3(b)). The
    #: "current position" pick reads the LAST justification, and reading it off
    #: ``entered_at`` means a backward clock step returns an earlier attempt as
    #: though the operator had just written it. Severity here is narrative-only —
    #: the gate-relevant ``has_sole_source_justification`` is a bare existence check
    #: and order-insensitive — but the pick is the same disease as the rest of this
    #: migration wave, and fixing four of five sites would leave the fifth to be
    #: rediscovered by whoever reads the export next.
    seq: Mapped[int] = mapped_column(sa.BigInteger, sa.Identity(always=False), nullable=False)


class RepairCaseAcceptedQuote(Base):
    """ใบที่ตกลง — which quote this repair was actually agreed at.

    **The primitive whose absence caused two separate gaps.** The DOA ladder routes
    on the ฿ of the repair, and until this row existed nothing recorded that number
    before the work was done: ``RepairCaseCloseout.total_thb`` only exists AFTER the
    repair the gate was supposed to authorise, and ``EvidencePack.lowest_amount_thb``
    is the cheapest quote, which is explicitly not what was agreed (an approved
    higher quote is a normal, governed outcome). The same absence is why migration
    ``0018`` had to add ``RepairCaseCloseout.vendor`` — nothing recorded WHICH garage
    was chosen. One accepted quote answers both questions, because a quote carries
    the amount and the vendor together.

    **``quote_id`` is a required composite FK** (Cray's typed decision, s191). The
    accepted amount is what an authority threshold routes on, so it must trace to
    evidence somebody actually recorded — a free-typed vendor and figure would
    reopen the exact hole this table closes. When the chosen garage's quote was
    never keyed, เมย์ keys it first through the existing quote route; that costs one
    call and buys a number with provenance. The composite target
    ``(case_id, quote_id)`` means the database, not this docstring, is what stops a
    case from accepting another case's quote.

    **``reason`` is nullable in the schema and conditionally required at the API**
    (same typed decision). The audit question is never "why did you accept a quote",
    it is "why did you not take the cheapest one" — so the write path refuses a
    non-lowest acceptance that carries no reason, and stays out of the way when the
    cheapest quote was chosen. The rule lives at the API rather than in a CHECK
    constraint because "lowest" is a fact about the OTHER rows at that moment, which
    is not something a column constraint can see.

    **Append-only; latest row wins.** Changing the agreed garage is a new row, and
    the earlier one stays readable. The trail is framed to the partner as protecting
    ต้อม and วิรัช, and one that can be rewritten protects nobody.
    """

    __tablename__ = "repair_case_accepted_quote"
    __table_args__ = (
        sa.Index("idx_repair_case_accepted_quote_case_id", "case_id"),
        sa.ForeignKeyConstraint(
            ["case_id", "quote_id"],
            ["repair_case_quote.case_id", "repair_case_quote.quote_id"],
            name="fk_repair_case_accepted_quote_quote",
        ),
        # The provenance vocabulary, stated as a constraint rather than as a
        # docstring asking future write paths to be careful. A marker that can hold
        # any string is not a marker: one typo — ``'Recorded'``, ``'derived'`` — and
        # a reader filtering for reconstructed rows silently misses them, which is
        # the same class of quiet-wrong-answer the stored figure exists to end.
        sa.CheckConstraint(
            "lowest_at_acceptance_basis IN ('recorded', 'reconstructed')",
            name="ck_repair_case_accepted_quote_basis",
        ),
        # ``seq`` is the latest-wins key, and it is declared UNIQUE so that
        # ``ORDER BY seq DESC LIMIT 1`` is a single-row answer by SCHEMA rather than
        # by hope. Identity is ``BY DEFAULT``, not ``ALWAYS`` — migration ``0023``
        # has to write explicit values to backfill legacy rows in the old reader's
        # order — so an explicit write remains possible, and this constraint is what
        # stops one from ever landing on a value that already exists.
        sa.UniqueConstraint("seq", name="uq_repair_case_accepted_quote_seq"),
    )

    accepted_id: Mapped[str] = mapped_column(sa.Text, primary_key=True)
    case_id: Mapped[str] = mapped_column(
        sa.Text, sa.ForeignKey("repair_case.case_id"), nullable=False
    )
    #: The quote that was agreed to. Its ``amount_thb`` is the governed figure and
    #: its ``vendor`` is the garage — read through the join, never copied here, so
    #: the two can never disagree.
    quote_id: Mapped[str] = mapped_column(sa.Text, nullable=False)
    #: Why this quote and not the cheapest one on file. NULL is meaningful and
    #: common: it means the cheapest WAS chosen (the API enforces that reading).
    reason: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    accepted_by: Mapped[str] = mapped_column(sa.Text, nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    #: The cheapest quote on file AT THIS INSTANT — stored, not re-derived
    #: (PLAN-0099 D1 / SD-1).
    #:
    #: **This does not break the join-not-copy rule above.** That rule protects the
    #: accepted quote's OWN amount and vendor from drifting away from the quote row
    #: they belong to. This column is different in kind: it is an aggregate over the
    #: OTHER quote rows at one instant, and it cannot go stale by construction —
    #: ``repair_case_quote`` and this table are both append-only with no update path,
    #: so the set of quotes existing at the moment of acceptance is frozen the
    #: instant this row is written.
    #:
    #: Re-deriving it instead — ``min(amount) WHERE entered_at <= accepted_at`` — was
    #: measured wrong in ~0.9 % of executions on this box, because the two stamps
    #: come from a wall clock that steps backwards ≥ 400 ms roughly every 15 s. The
    #: write path already computes the right number (``cases.py``, no timestamp
    #: filter, measured immune) at the only instant it is trivially correct.
    #:
    #: NOT NULL, and that is a decision: an acceptance always carries a required
    #: composite FK to a quote, so the set aggregated over is never empty and NULL
    #: could only ever mean "somebody forgot". Allowing it would reopen the exact
    #: shape PLAN-0099 AC-2 forbids — a case that HAS an acceptance reading ``None``,
    #: which ``accepted_the_cheapest`` then reports as "nothing accepted yet".
    lowest_amount_at_acceptance_thb: Mapped[Decimal] = mapped_column(
        sa.Numeric(14, 2), nullable=False
    )
    #: Whether the figure above was RECORDED at acceptance or RECONSTRUCTED by
    #: migration ``0023`` (Cray's SD-2 ruling, s196). NOT NULL with **no default at
    #: any layer** — no ORM default, no ``server_default`` — so every insert site
    #: must state provenance out loud. A default of ``'recorded'`` would let a
    #: reconstructed row pass itself off as a record, which is precisely the lie the
    #: ruling exists to prevent; a default of ``'reconstructed'`` would be a
    #: different lie. The absence of a default is the mechanism, so removing it
    #: later is a governance change, not a tidy-up.
    #:
    #: It governs ``accepted_the_cheapest`` too, deliberately with no second marker:
    #: the boolean is computed from the figure, there is exactly ONE stored fact
    #: behind both, and two markers could disagree — which would be a new way to lie
    #: rather than a second safeguard.
    lowest_at_acceptance_basis: Mapped[str] = mapped_column(sa.Text, nullable=False)
    #: Insertion order, assigned by the database (PLAN-0099 D2). ``latest_accepted_quote``
    #: feeds the DOA gate, and keying "current" on ``accepted_at`` was measured to
    #: report the SUPERSEDED acceptance under a backward step: a dearer garage chosen
    #: WITH a written reason reads back as "accepted the cheapest, no reason needed",
    #: so the audit trail inverts its own meaning. A same-instant tie is genuinely
    #: ambiguous on a clock; under a backward step the operator's intent is still
    #: recoverable, because it is insertion order — and this column is that.
    seq: Mapped[int] = mapped_column(sa.BigInteger, sa.Identity(always=False), nullable=False)
