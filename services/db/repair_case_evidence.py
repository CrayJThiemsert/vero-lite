"""Hand-authored quote-evidence tables (PLAN-0096 Step 3 / AC-4 data half).

This is the artifact that replaces the partner's actual three-quote process, which
he described in Q5 as **scrolling LINE, sometimes lost**. น้องเมย์ receives quotes as
PDFs, LINE-exported photos and photographs of paper, prints them, files them — and
when accounting asks two months later which vendors were compared, the answer is an
archaeology dig through a chat group. The pack makes "were three vendors compared?"
a COUNT instead of a search.

Two tables, not one, because they are two different facts:

* :class:`RepairCaseQuote` — a vendor quoted this much for this repair. Has money.
* :class:`RepairCaseJustification` — no comparison was possible and here is why
  (rare part, single vendor). Has no money; it is the E-3 evidence-ALTERNATIVE
  (ADR-0034), the other legitimate way past the sourcing rule.

Conflating them into one table with a nullable amount would have made
``quote_count`` — the number Step 4's threshold reads — depend on remembering to
filter by a discriminator. A count that is one forgotten ``WHERE`` away from
counting justifications as quotes is exactly the wrong shape for a governance
signal.

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
    __table_args__ = (sa.Index("idx_repair_case_quote_case_id", "case_id"),)

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
    __table_args__ = (sa.Index("idx_repair_case_justification_case_id", "case_id"),)

    justification_id: Mapped[str] = mapped_column(sa.Text, primary_key=True)
    case_id: Mapped[str] = mapped_column(
        sa.Text, sa.ForeignKey("repair_case.case_id"), nullable=False
    )
    vendor: Mapped[str] = mapped_column(sa.Text, nullable=False)
    reason: Mapped[str] = mapped_column(sa.Text, nullable=False)
    entered_by: Mapped[str] = mapped_column(sa.Text, nullable=False)
    entered_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
