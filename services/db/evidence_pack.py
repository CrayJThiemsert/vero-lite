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


def compute_accepted_the_cheapest(
    accepted_amount_thb: Decimal | None, lowest_at_acceptance_thb: Decimal | None
) -> bool | None:
    """Was the agreed quote the cheapest then on file? One rule, several readers.

    A free function rather than only a property because the accepted-quote endpoint
    holds the raw acceptance row, not a pack: it passes the quote's amount and the
    stored figure straight in, and could not reach the property below without building
    an evidence pack it has no other use for. So two callers reach this directly — that
    property and the endpoint — serving three read surfaces, because the month-end
    export answers the question through ``EvidencePack.accepted_the_cheapest`` rather
    than calling here itself.

    What lives here is not the comparison but the THREE-VALUED rule around it. The SD-2
    ruling turns on there being exactly ONE stored fact behind the figure, the boolean
    and the provenance marker; private copies of that rule are how an endpoint and an
    export would come to disagree about the same case, and such a disagreement is the
    kind no reader can diagnose from either output.

    Three-valued: None means nothing has been accepted. That is a different answer
    from "no" and collapsing them would give the reassuring one.
    """
    if accepted_amount_thb is None or lowest_at_acceptance_thb is None:
        return None
    return accepted_amount_thb == lowest_at_acceptance_thb


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
    #: cheapest when it was made.
    #:
    #: **Read from the acceptance row, not re-derived** (PLAN-0099 D1 / SD-1). The
    #: derivation this replaced compared two wall-clock stamps, and the wall clock on
    #: this box steps backwards >= 400 ms roughly every 15 s — measured wrong in about
    #: 0.9 % of executions, which is the reported flake and, at the same rate, a wrong
    #: audit answer. The old argument for deriving was that "a stored copy would be
    #: one more thing that can go stale"; both tables are append-only with no update
    #: path, so the set of quotes existing at the instant of acceptance is frozen the
    #: moment the acceptance row lands, and the stored copy cannot go stale by
    #: construction.
    lowest_amount_at_acceptance_thb: Decimal | None
    #: Whether the figure above was RECORDED at acceptance or RECONSTRUCTED by
    #: migration ``0023`` from the append-only rows (Cray's SD-2 ruling). None only
    #: when nothing has been accepted. It qualifies ``accepted_the_cheapest`` too —
    #: that boolean is computed from the figure, so there is one stored fact and one
    #: marker for it.
    lowest_at_acceptance_basis: str | None

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

        Since PLAN-0099 the None case means exactly that and nothing else. It used to
        also fire when the derivation matched no quote at all, which a backward clock
        step could cause on a case that HAD an acceptance — so "we could not compare"
        was reported as "nothing was accepted yet", the reassuring reading, on a case
        where somebody had in fact committed the fleet's money.
        """
        return compute_accepted_the_cheapest(
            self.accepted_amount_thb, self.lowest_amount_at_acceptance_thb
        )


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
    # Ordered by ``seq`` — insertion order — because ``justifications[-1]`` below is a
    # latest-wins PICK, not a display list (PLAN-0099 D2 / SD-3(b)). Under a backward
    # clock step, ordering by ``entered_at`` hands the reader an earlier attempt as
    # though the operator had just written it. Severity is narrative-only here — the
    # gate-relevant ``has_sole_source_justification`` is a bare existence check and
    # order-insensitive — but it is the same disease as the picks around it.
    justifications = list(
        (
            await session.execute(
                select(RepairCaseJustification)
                .where(RepairCaseJustification.case_id == case_id)
                .order_by(RepairCaseJustification.seq)
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
        # Read, not derived. The comparison that used to stand here —
        # ``q.entered_at <= accepted.accepted_at`` — is deleted rather than patched:
        # no operator on two lying stamps produces a true answer, and the write path
        # already knew the right one.
        lowest_amount_at_acceptance_thb=(
            accepted.lowest_amount_at_acceptance_thb if accepted else None
        ),
        lowest_at_acceptance_basis=(accepted.lowest_at_acceptance_basis if accepted else None),
    )


async def latest_accepted_quote(
    session: AsyncSession, case_id: str
) -> RepairCaseAcceptedQuote | None:
    """The case's current ใบที่ตกลง, or None.

    Newest wins because the table is append-only: changing the agreed garage is a
    new row, and every consumer — the pack, the endpoint, the month-end export —
    must agree on which row is current. One query in one place is how they stay
    agreed, the same reason the close-out reader is a single function.

    **Newest means last-INSERTED, not latest-stamped** (PLAN-0099 D2). This pick feeds
    ``services.db.case_events.governed_case_facts``, which is the DOA gate's input, so
    getting it wrong is not a display glitch. Measured s196 on ``accepted_at``: under a
    -5 ms clock step between two acceptances the gate was handed the SUPERSEDED row —
    a dearer garage chosen WITH a written reason read back as "accepted the cheapest,
    no reason needed", so the audit trail inverted its own meaning. With equal stamps
    the old ``accepted_id.desc()`` tiebreak is a random UUID, and the superseded row
    won 20 times out of 40.

    A same-instant tie is genuinely ambiguous on a clock. Under a backward step the
    operator's intent is NOT ambiguous — it is insertion order, and the clock simply
    lied. ``seq`` is that order, and it is UNIQUE, so this needs no tiebreak: one row
    comes back, and the pack, the endpoint and the export all get the same one.
    """
    return (
        (
            await session.execute(
                select(RepairCaseAcceptedQuote)
                .where(RepairCaseAcceptedQuote.case_id == case_id)
                .order_by(RepairCaseAcceptedQuote.seq.desc())
                .limit(1)
            )
        )
        .scalars()
        .first()
    )
