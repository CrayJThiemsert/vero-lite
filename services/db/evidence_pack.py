"""The quote evidence pack — the read model Step 4 computes its signal from.

PLAN-0096 Step 3 exposes exactly two facts to Step 4 (`quote_count` and whether a
sole-source justification exists), and this module is deliberately the whole of that
seam. Step 4 will turn those into `compliance.three_quote` + `three_quote_basis`
against the partner's ฿30,000 threshold (Q10); it is NOT decided here.

**Why the split matters.** Keeping the count-and-presence facts separate from the
pass/fail decision means the threshold can move — it is authored config, and the
partner may well revise it after a month of real cases — without touching how
evidence is read. It also means this module has no opinion to get wrong: it reports
what was recorded, and a governance rule elsewhere judges whether that is enough.

``distinct_vendor_count`` is reported alongside the raw count because they answer
different questions, and the difference is the interesting one. Three quotes from
the same vendor is not a price comparison; the partner's rule (Q10) is "สามเจ้า" —
three PLACES. Which of the two Step 4 should read is Step 4's decision to make
explicitly, with both numbers in front of it, rather than a silent consequence of
which one this module happened to return.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.db.repair_case_evidence import RepairCaseJustification, RepairCaseQuote


@dataclass(frozen=True)
class EvidencePack:
    """What a case's sourcing evidence amounts to, as facts rather than a verdict."""

    case_id: str
    quote_count: int
    distinct_vendor_count: int
    vendors: tuple[str, ...]
    #: Lowest quoted amount, or None when no quote is recorded. The export's
    #: "bought from whom / why" narrative leans on this; the gate does not.
    lowest_amount_thb: Decimal | None
    has_sole_source_justification: bool
    #: The most recent justification's vendor + reason, when one exists. Append-only
    #: storage means an earlier attempt stays on the record; the latest is the one
    #: that describes the current position.
    sole_source_vendor: str | None
    sole_source_reason: str | None
    attachment_count: int

    @property
    def quotes_on_file(self) -> bool:
        """True when anything at all was recorded — distinct from 'enough'."""
        return self.quote_count > 0


async def load_evidence_pack(session: AsyncSession, case_id: str) -> EvidencePack:
    """Read one case's evidence pack.

    Returns a pack with zeroed counts for a case that has no evidence yet — an
    ABSENT pack and an EMPTY pack are the same fact here ("nothing was recorded"),
    and Step 4 fails CLOSED on that rather than treating it as a pass. Raising
    instead would push that decision into exception handling, where a caller's
    ``except`` could quietly turn 'no evidence' into 'carry on'.
    """
    quotes = list(
        (
            await session.execute(
                select(RepairCaseQuote)
                .where(RepairCaseQuote.case_id == case_id)
                .order_by(RepairCaseQuote.entered_at)
            )
        ).scalars()
    )
    justifications = list(
        (
            await session.execute(
                select(RepairCaseJustification)
                .where(RepairCaseJustification.case_id == case_id)
                .order_by(RepairCaseJustification.entered_at)
            )
        ).scalars()
    )

    # Vendor identity is compared case-insensitively on trimmed text: เมย์ types
    # these by hand from whatever the paperwork says, so "อู่ช่างเล็ก" and
    # "อู่ช่างเล็ก " are one vendor. Anything cleverer (fuzzy matching, aliases)
    # would start MERGING vendors the operator meant to keep apart, which would
    # inflate nothing but could hide a real single-source situation.
    vendors = tuple(q.vendor for q in quotes)
    distinct = {q.vendor.strip().casefold() for q in quotes if q.vendor.strip()}
    latest_justification = justifications[-1] if justifications else None

    return EvidencePack(
        case_id=case_id,
        quote_count=len(quotes),
        distinct_vendor_count=len(distinct),
        vendors=vendors,
        lowest_amount_thb=min((q.amount_thb for q in quotes), default=None),
        has_sole_source_justification=bool(justifications),
        sole_source_vendor=latest_justification.vendor if latest_justification else None,
        sole_source_reason=latest_justification.reason if latest_justification else None,
        attachment_count=sum(1 for q in quotes if q.attachment),
    )
