"""Fleet-maintenance vertical — Box-4 economic-impact (฿) producer (ADR-0030 / PLAN-0071).

**Event-anchored v1** — the fifth producer, and the first one whose ฿ figure comes off
the *triggering event itself* rather than an exemplar. Procurement's OQ-C had to fall
back to a representative hero PO because its events carry a criticality score, not a
resolvable ฿ anchor (``economic_impact.py:12-19`` there). Fleet has no such problem: a
repair-quote event IS the money — ``measured_value`` with ``unit == "THB"`` is the
quoted repair amount (``data_adapter/synthetic.py``, and the live case feed writes the
same shape). So this producer resolves each event to its own ฿, and returns ``None``
when it cannot — never an exemplar standing in for a number it does not have.

**What the governance actually buys, in this vertical.** The partner adopted the
three-quote rule after being defrauded on parts (``sourcing.py:33-36``). That is the
baseline: a repair paid at a price nobody compared. The governed side is the same
repair after a comparison across three distinct vendors. The threshold that decides
whether the rule applies at all is the partner's own answer — ฿30,000, Q10, 2026-07-28
— and it is IMPORTED from ``sourcing.py`` rather than restated here, so the producer
and the gate can never drift onto two different numbers.

**The one disclosed assumption (ADR-0030 D3).** How much a price comparison recovers is
not a column anywhere; it is a modelling input, so it is named in ``assumptions`` and
set deliberately LOW (Cray-ruled 15%, session 195, choosing the conservative option over
a fraud-sized one). See ``_COMPARISON_RECOVERY_FRACTION`` for why the direction of the
error is the safe one.

Pure + deterministic + offline: arithmetic over the event's own fields plus two imported
partner constants. No DB, no CSV, no network, no LLM. Advisory + ``provisional``
(ADR-0030 D5).
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from services.engine.economic_impact import (
    EconomicExposure,
    EconomicImpact,
    register_economic_producer,
)
from verticals.fleet_maintenance.sourcing import (
    MIN_DISTINCT_VENDORS,
    THREE_QUOTE_THRESHOLD_THB,
)

#: What a price comparison across three distinct vendors recovers off an uncompared
#: quote. NOT a column — a disclosed modelling input (ADR-0030 D3), ruled by Cray at
#: 15% (session 195) from a menu that also offered a fraud-sized 25%.
#:
#: **Why the low number is the safe one.** The producer anchors on the quote as it
#: stands and models the comparison as recovering this fraction of it. On a row that
#: ALREADY passes on ``three_quotes``, that quote is the *compared* price, so the true
#: uncompared price was higher and the real benefit is larger than what is reported
#: here. The simplification therefore errs by UNDERSTATING the benefit, never by
#: overstating it — the only direction an advisory ฿ figure is allowed to be wrong in
#: (CLAUDE.md §8 assistive discipline). Per-basis anchoring is a clean v2 once a pilot
#: supplies the pre-comparison quote alongside the accepted one.
_COMPARISON_RECOVERY_FRACTION = Decimal("0.15")

#: The event fields + partner constants the ฿ figures derive from (ADR-0030 D3 provenance).
_BASIS_REFS = [
    "event.measured_value (unit=THB) — the quoted repair amount on the case event",
    "fleet_maintenance.sourcing.THREE_QUOTE_THRESHOLD_THB (design partner Q10, 2026-07-28)",
    "fleet_maintenance.sourcing.MIN_DISTINCT_VENDORS (design partner Q10, 'สามเจ้า')",
]


def _quoted_repair_thb(event: Mapping[str, Any]) -> Decimal | None:
    """The event's ฿ anchor, or ``None`` when the event is not a repair quote.

    ``unit`` is checked rather than assumed: the fleet feed also carries odometer and
    PM-interval readings, and reading a kilometre count as baht would emit a confident
    ฿ figure for something that is not money at all. ``str()`` before ``Decimal`` on
    purpose — ``measured_value`` arrives as a float, and ``Decimal(float)`` would carry
    the binary representation error into a money figure (the ledger's Decimal-never-float
    invariant, ADR-0030).
    """
    if str(event.get("unit")) != "THB":
        return None
    raw = event.get("measured_value")
    if raw is None:
        return None
    try:
        return Decimal(str(raw))
    except (ArithmeticError, ValueError):
        return None


async def fleet_maintenance_economic_impact(
    event: Mapping[str, Any], vertical: str
) -> EconomicImpact | None:
    """Compute the fleet ``overpay_avoided`` ฿ facet from the event's own quoted amount.

    Returns ``None`` for a non-quote event, and for a quote at or under the partner's
    ฿30,000 comparison threshold — there the rule never applied, so there is no
    baseline-vs-governed tradeoff to model. That is the same ``under_threshold`` reading
    ``compute_three_quote`` gives (``sourcing.py:88-89``), taken off the same imported
    constant rather than a second copy of the number, and it is the OQ-C discipline
    generalized: a facet that cannot be grounded is absent, never guessed.
    """
    quoted = _quoted_repair_thb(event)
    if quoted is None or quoted <= THREE_QUOTE_THRESHOLD_THB:
        return None
    recovered = quoted * _COMPARISON_RECOVERY_FRACTION
    baseline = EconomicExposure(
        label="uncompared repair quote (the price paid without a comparison on file)",
        exposure_thb=quoted,
        components={"quoted_repair_thb": quoted},
    )
    governed = EconomicExposure(
        label=f"price-compared across {MIN_DISTINCT_VENDORS} distinct vendors (partner rule Q10)",
        exposure_thb=quoted - recovered,
        components={"compared_repair_thb": quoted - recovered},
    )
    return EconomicImpact(
        provisional=True,
        currency="THB",
        kind="overpay_avoided",
        baseline=baseline,
        governed=governed,
        net_benefit_thb=recovered,
        assumptions=[
            f"price comparison across {MIN_DISTINCT_VENDORS} distinct vendors recovers "
            f"{_COMPARISON_RECOVERY_FRACTION:%} of an uncompared quote "
            "(modelling input, not a column — Cray-ruled conservative, s195)",
            f"the rule applies only above ฿{THREE_QUOTE_THRESHOLD_THB:,} "
            "(the partner's own Q10 threshold, imported from sourcing.py)",
            "the event's quote is read as the UNCOMPARED anchor regardless of its "
            "three_quote_basis; on a row already passing on three_quotes the true "
            "uncompared price was higher, so this figure understates the benefit",
        ],
        basis_refs=_BASIS_REFS,
    )


def register_fleet_maintenance_economic_impact() -> None:
    """Register the fleet ฿-impact producer (the guarded optional import in
    ``discovery._register_economic_producer`` calls this)."""
    register_economic_producer("fleet_maintenance", fleet_maintenance_economic_impact)
