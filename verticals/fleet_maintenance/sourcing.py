"""The fleet's sourcing-hygiene signal — E-1's computed half (PLAN-0096 Step 4).

The partner's rule (Q10) has two parts, and only one of them was ever representable
in the engine: *"เทียบราคาเกินสามหมื่น สามเจ้า"* — compare across three places, above
฿30,000. A ``rule_gate`` criterion is pass/fail on a supplied signal and carries no
threshold field, and ADR-0025 D4 forbids smuggling the ฿ figure into the rule's
authored prose. So the ฿ half lives HERE: typed fleet-side config, in the vertical
that owns the rule, read by the feed that computes the signal.

**Why this module is not in the engine.** A threshold that moved into
``services/engine`` would become every vertical's threshold, and this one is one
operator's answer to one question on one day. He may well revise it after a month of
real cases. Keeping it vertical-side means that revision is a one-line edit here
with its provenance beside it, not an engine change with six verticals' worth of
blast radius (ADR-006).

**Three ways to satisfy the rule, and they are not equal.** They are checked in the
order below, and the order is the explanation:

1. ``under_threshold`` — the repair is small enough that the rule never applied. Not
   an exception; the rule simply has no purchase here.
2. ``three_quotes`` — the comparison actually happened, across three distinct
   vendors. This is the rule being satisfied as written.
3. ``sole_source_justified`` — no comparison was possible and a human wrote down
   why (ADR-0034 D4, the evidence ALTERNATIVE). The rule is satisfied a DIFFERENT
   way, never relaxed: someone is on the record.

Anything else FAILS, with basis ``quotes_required``. Failing is the normal, expected
outcome for a large repair nobody has price-compared yet — it is not an error, it is
the gate doing its job, and the case becomes passable the moment เมย์ records the
missing quotes or วิรัช writes the justification.

**Three DISTINCT vendors, not three quotes** (Cray-ratified 2026-07-28; the PLAN's
Step 4 text is amended to match). Three quotes from the same garage is not a price
comparison, and counting them as one would let a repair that was never compared
satisfy a rule the partner adopted after being defrauded on parts.

Pure + deterministic: no DB, no network, no LLM. The caller supplies the counts; how
they were obtained is the evidence pack's business, not this function's.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

#: The ฿ threshold above which a repair must be price-compared. Design partner's own
#: answer (Q10, 2026-07-28 discovery): ">30,000 — and it happens to coincide with my
#: own approval tier". The coincidence is his, not a modelling shortcut: the gate and
#: the DOA ladder are independent, and either can move without the other.
THREE_QUOTE_THRESHOLD_THB = Decimal("30000")

#: How many DIFFERENT vendors constitute a comparison (Q10: "สามเจ้า").
MIN_DISTINCT_VENDORS = 3

ThreeQuoteBasis = Literal[
    "under_threshold",
    "three_quotes",
    "sole_source_justified",
    "quotes_required",
]

#: The bases that mean the criterion PASSED. Declared as data rather than re-derived
#: at each call site: a reader answering "which of these is a pass?" should not have
#: to reconstruct the branch order of the function below.
PASSING_BASES: frozenset[str] = frozenset(
    {"under_threshold", "three_quotes", "sole_source_justified"}
)


def compute_three_quote(
    *,
    amount_thb: Decimal,
    distinct_vendor_count: int,
    has_sole_source_justification: bool,
) -> tuple[bool, ThreeQuoteBasis]:
    """Return ``(signal, basis)`` for the ``three_quote`` compliance criterion.

    ``signal`` is what the ``rule_gate`` reads; ``basis`` is stamped on the row so the
    month-end export can answer "why did this pass?" without re-running the logic —
    which is the whole point of recording it rather than recomputing it later against
    a threshold that may since have moved.

    Keyword-only by design. The two counts are both plain integers and the boolean
    reads like either of them at a call site; a positional call that transposed them
    would compute a wrong governance signal silently.
    """
    if amount_thb <= THREE_QUOTE_THRESHOLD_THB:
        return True, "under_threshold"
    if distinct_vendor_count >= MIN_DISTINCT_VENDORS:
        return True, "three_quotes"
    if has_sole_source_justification:
        return True, "sole_source_justified"
    return False, "quotes_required"


def compliance_signal_map(basis_signal: tuple[bool, ThreeQuoteBasis]) -> dict[str, bool]:
    """The ``compliance`` map shape the gate reads, from a computed ``(signal, basis)``.

    Trivial, and deliberately the only place that shape is constructed: the gate fails
    CLOSED on a missing or malformed map, so every producer of one — the live case
    feed and the synthetic demo fixture alike — goes through here rather than each
    spelling out the literal.
    """
    signal, _ = basis_signal
    return {"three_quote": signal}
