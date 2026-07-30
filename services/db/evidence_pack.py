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

**The accepted quote (ใบที่ตกลง) joins the pack as facts, on the same terms.** It
reports which quote was agreed to, at what figure, from whom, and — when the
cheapest was not chosen — why. It still judges nothing: whether that figure clears
a DOA tier is the ladder's call, and whether the reason is adequate is a human's.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.db.repair_case_evidence import (
    RepairCaseAcceptedQuote,
    RepairCaseJustification,
    RepairCaseQuote,
)


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
    #: ใบที่ตกลง — the quote actually agreed to, or None when nothing has been
    #: accepted yet. Append-only storage means the LATEST acceptance is the current
    #: position; earlier ones stay on the record as history.
    accepted_quote_id: str | None
    #: The governed figure — what the DOA ladder routes on. Read through the join
    #: rather than copied onto the acceptance row, so it cannot drift from the quote.
    accepted_amount_thb: Decimal | None
    accepted_vendor: str | None
    #: Why not the cheapest. None means the cheapest WAS accepted — the write path
    #: refuses a non-lowest acceptance without one, so the absence carries meaning.
    accepted_reason: str | None
    accepted_by: str | None
    accepted_at: datetime | None
    #: The cheapest quote on file AT THE MOMENT OF ACCEPTANCE, which is not always
    #: ``lowest_amount_thb``: a cheaper quote can arrive afterwards, and then the
    #: acceptance looks unjustified against today's numbers while having been the
    #: cheapest when it was made. Derived here rather than stored — append-only rows
    #: carry ``entered_at``, so the state at any past instant is reconstructable, and
    #: a stored copy would be one more thing that can go stale.
    lowest_amount_at_acceptance_thb: Decimal | None

    @property
    def quotes_on_file(self) -> bool:
        """True when anything at all was recorded — distinct from 'enough'."""
        return self.quote_count > 0

    @property
    def accepted_the_cheapest(self) -> bool | None:
        """Whether the agreed quote was the cheapest then on file.

        None when nothing has been accepted — deliberately three-valued, because
        "no acceptance recorded" and "accepted the cheapest" are different answers
        to the audit question and a bool would collapse them into the reassuring one.
        """
        if self.accepted_amount_thb is None or self.lowest_amount_at_acceptance_thb is None:
            return None
        return self.accepted_amount_thb == self.lowest_amount_at_acceptance_thb


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

    # A composite FK guarantees the accepted quote exists and belongs to this case,
    # so a missing match below would be a schema violation rather than a data state.
    # It is still read defensively — reporting None beats an AttributeError inside a
    # read model whose whole job is to answer "what was recorded".
    accepted = await latest_accepted_quote(session, case_id)
    accepted_quote = (
        next((q for q in quotes if q.quote_id == accepted.quote_id), None) if accepted else None
    )
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
        accepted_quote_id=accepted.quote_id if accepted else None,
        accepted_amount_thb=accepted_quote.amount_thb if accepted_quote else None,
        accepted_vendor=accepted_quote.vendor if accepted_quote else None,
        accepted_reason=accepted.reason if accepted else None,
        accepted_by=accepted.accepted_by if accepted else None,
        accepted_at=accepted.accepted_at if accepted else None,
        lowest_amount_at_acceptance_thb=(
            min(
                (q.amount_thb for q in quotes if q.entered_at <= accepted.accepted_at),
                default=None,
            )
            if accepted
            else None
        ),
    )


async def latest_accepted_quote(
    session: AsyncSession, case_id: str
) -> RepairCaseAcceptedQuote | None:
    """The case's current ใบที่ตกลง, or None.

    Newest wins because the table is append-only: changing the agreed garage is a
    new row, and every consumer — the pack, the endpoint, the month-end export —
    must agree on which row is current. One query in one place is how they stay
    agreed, the same reason the close-out reader is a single function.

    ``accepted_id`` breaks a same-instant tie. Two acceptances sharing a timestamp
    is genuinely ambiguous — no ordering recovers which the operator meant — but an
    arbitrary-yet-STABLE answer is still worth having: without the tiebreak the
    pack, the endpoint and the export could each pick a different row from identical
    data, which is a disagreement no reader could diagnose.
    """
    return (
        (
            await session.execute(
                select(RepairCaseAcceptedQuote)
                .where(RepairCaseAcceptedQuote.case_id == case_id)
                .order_by(
                    RepairCaseAcceptedQuote.accepted_at.desc(),
                    RepairCaseAcceptedQuote.accepted_id.desc(),
                )
                .limit(1)
            )
        )
        .scalars()
        .first()
    )
