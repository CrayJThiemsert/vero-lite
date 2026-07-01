"""The deterministic ``scored_rule`` supplier selection (ADR-0025 D2; PLAN-0044 A1b Step 5).

The RUN-side enforcement of the author-time :class:`~services.engine.procedures.spec.ScoredRule`
(the typed AT-2 scored-selection content): given the candidate quotes an emergency-sourcing
``source`` step carries (data-access = (a) — intake enriches the requisition with the part's
candidate quotes, Cray-confirmed session 91), score every quote by the rule's weighted criteria,
select the winner DETERMINISTICALLY (same inputs -> same pick), and emit the selected quote's
spend (``unit_price x qty``) so the downstream ``approve`` doa_tier can resolve the DOA tier.
The LLM only summarises the quotes (advisory, elsewhere); it NEVER selects (governed != generated,
ADR-0019 IN-3).

Pure + deterministic: no LLM, no DB, no network -- the offline tests are the gate (CLAUDE.md #8).
Money is :class:`~decimal.Decimal`, never ``float`` (no binary-float rounding on a spend that
routes an authority tier). Fails CLOSED (:class:`ScoredRuleError`) on absent/empty candidate
quotes, a malformed quote, or a criterion the executor cannot interpret -- a supplier cannot be
silently selected on a rule / quote set the executor only partially understands.

**The scoring model (v1 -- the authored weights are PROVISIONAL, ADR-0025 D2 / procedures.yaml).**
Each candidate quote scores as a weighted sum of min-normalised per-criterion scores (fastest /
cheapest -> 1.0). The ``criticality`` criterion is scored by lead-time READINESS (a faster supplier
serves a critical / line-down need better) and its weight is AMPLIFIED by the EVENT criticality the
requisition carries -- so the SAME rule picks the cheap on-contract supplier for a routine event and
the fast off-contract supplier for a critical one (the managerial-process story). ``lead_time`` and
``unit_price`` map to the quote's lead-time and unit price. The winner's ``on_contract`` flag vs the
rule's ``default_source`` classifies the pick's PROVENANCE: a winner that satisfies the default is
the ``default_source`` path; one that deviates is the ``exception_policy`` (``rfq_avl_logged``) path
-- an off-AVL override that REQUIRES a logged justification (never a skipped gate, ADR-0025 D3).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from services.engine.procedures.orchestrator import ProcedureError
from services.engine.procedures.spec import ScoredRule, SourcePolicy


class ScoredRuleError(ProcedureError):
    """A ``scored_rule`` step failed CLOSED (PLAN-0044 A1b Step 5).

    Raised on absent / empty candidate quotes, a malformed quote (missing / non-numeric
    ``unit_price`` / ``lead_time_days``), or a criterion name the executor cannot interpret.
    Failing closed blocks the selection BEFORE any downstream tier routing -- no supplier is
    silently selected on a rule / quote set the executor only partially understands."""


# The criterion vocabulary this v1 executor interprets (ADR-0025 D2's authored set). A rule naming
# any other criterion fails CLOSED -- a future AT-2 vertical EXTENDS this map, never a silent
# mis-score (the Rule-of-Three tension ADR-0025 flagged; instance-scoped until N>=2).
_CRITICALITY = "criticality"
_LEAD_TIME = "lead_time"
_UNIT_PRICE = "unit_price"
_KNOWN_CRITERIA = frozenset({_CRITICALITY, _LEAD_TIME, _UNIT_PRICE})


@dataclass(frozen=True)
class QuoteScore:
    """One scored candidate quote -- the stable-keyed per-quote outcome (render / audit)."""

    quote_id: str
    supplier_id: str
    unit_price: Decimal
    currency: str
    lead_time_days: Decimal
    on_contract: bool
    score: Decimal

    def to_audit(self) -> dict[str, Any]:
        """JSON-safe projection (``Decimal`` -> ``str``) for the step audit / output_set (JSONB)."""
        return {
            "quote_id": self.quote_id,
            "supplier_id": self.supplier_id,
            "unit_price": str(self.unit_price),
            "currency": self.currency,
            "lead_time_days": str(self.lead_time_days),
            "on_contract": self.on_contract,
            "score": str(self.score),
        }


@dataclass(frozen=True)
class ScoredRuleVerdict:
    """The structured, stable-keyed ``scored_rule`` outcome (PLAN-0044 A1b Step 5).

    ``selected_*`` name the deterministic winner; ``amount`` is its spend (``unit_price x qty``)
    in the quote currency -- the value the downstream approve doa_tier resolves. ``source_path``
    is the provenance (``default_source`` when the winner satisfies the rule's default policy, else
    ``exception_policy`` -- the off-AVL override), and ``override_required`` marks when that
    override owes a logged justification. ``ranked`` is every quote's score (descending) so a
    read-only render can show WHY the winner won without re-deriving the math."""

    selected_quote_id: str
    selected_supplier_id: str
    amount: Decimal
    currency: str
    qty: Decimal
    on_contract: bool
    source_path: str
    override_required: bool
    ranked: list[QuoteScore]

    def to_audit(self) -> dict[str, Any]:
        """JSON-safe projection for the step audit / output_set (JSONB) -- ``Decimal`` -> ``str``
        so the persisted artifact is serialisable while the authoritative values stay exact."""
        return {
            "selected_quote_id": self.selected_quote_id,
            "selected_supplier_id": self.selected_supplier_id,
            "amount": {"value": str(self.amount), "currency": self.currency},
            "qty": str(self.qty),
            "on_contract": self.on_contract,
            "source_path": self.source_path,
            "override_required": self.override_required,
            "ranked": [q.to_audit() for q in self.ranked],
        }


def _as_bool(value: Any) -> bool:
    """Coerce an ``on_contract`` flag to ``bool`` -- robust to the CSV/JSON string form
    (``"false"`` / ``"true"``): ``bool("false")`` is ``True`` in Python, which would silently
    mislabel an off-contract winner's provenance. A string is truthy only for an explicit truthy
    token; everything else falls back to ``bool``."""
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "on"}
    return bool(value)


def _quote_decimal(quote: Mapping[str, Any], key: str) -> Decimal:
    """Read an EXACT ``Decimal`` off a candidate quote, failing CLOSED on absent / non-numeric."""
    if key not in quote:
        raise ScoredRuleError(
            f"scored_rule: candidate quote {quote.get('quote_id', quote)!r} has no '{key}' "
            "(fail closed -- a quote cannot be scored on a missing field)"
        )
    try:
        return Decimal(str(quote[key]))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ScoredRuleError(
            f"scored_rule: candidate quote '{quote.get('quote_id')}' has a non-Decimal '{key}' "
            f"({quote[key]!r}) -- fail closed"
        ) from exc


def _readiness(value: Decimal, lo: Decimal, hi: Decimal) -> Decimal:
    """Min-better normalisation -> ``1`` for the smallest (best), ``0`` for the largest. All-equal
    -> ``1`` (every candidate is equally best on this axis; no division by a zero range)."""
    if hi == lo:
        return Decimal(1)
    return (hi - value) / (hi - lo)


def _weights(rule: ScoredRule) -> dict[str, Decimal]:
    """The criterion -> weight map, failing CLOSED on a criterion this v1 executor cannot
    interpret (rather than silently dropping it and mis-scoring)."""
    weights: dict[str, Decimal] = {}
    for criterion in rule.criteria:
        if criterion.name not in _KNOWN_CRITERIA:
            raise ScoredRuleError(
                f"scored_rule: criterion '{criterion.name}' is not one this executor interprets "
                f"({sorted(_KNOWN_CRITERIA)}) -- fail closed rather than silently mis-score (a "
                "future AT-2 vertical extends the criterion map, PLAN-0044 A1b Step 5)"
            )
        weights[criterion.name] = criterion.weight
    return weights


def select_scored_supplier(
    rule: ScoredRule,
    quotes: list[Mapping[str, Any]],
    *,
    qty: Decimal,
    event_criticality: Decimal,
) -> ScoredRuleVerdict:
    """Select the winning supplier for ``quotes`` per ``rule``, DETERMINISTICALLY (PLAN-0044 A1b
    Step 5). See the module docstring for the scoring model.

    The pick is the maximum total score; ties break by ``quote_id`` (stable -> reproducible). The
    LLM is not consulted -- selection is this pure function (governed != generated). Fails CLOSED
    (:class:`ScoredRuleError`) on an empty quote set, a malformed quote, or an uninterpretable
    criterion. ``event_criticality`` amplifies the ``criticality`` criterion's weight; ``qty``
    scales the winning unit price to the PO spend the downstream doa_tier resolves.
    """
    if not quotes:
        raise ScoredRuleError(
            "scored_rule: no candidate quotes to score -- a supplier cannot be selected from an "
            "empty set (fail closed)"
        )
    weights = _weights(rule)
    w_crit = weights.get(_CRITICALITY, Decimal(0))
    w_lead = weights.get(_LEAD_TIME, Decimal(0))
    w_price = weights.get(_UNIT_PRICE, Decimal(0))

    prices = [_quote_decimal(q, "unit_price") for q in quotes]
    leads = [_quote_decimal(q, "lead_time_days") for q in quotes]
    p_lo, p_hi = min(prices), max(prices)
    l_lo, l_hi = min(leads), max(leads)

    scored: list[QuoteScore] = []
    for quote, price, lead in zip(quotes, prices, leads, strict=True):
        lead_readiness = _readiness(lead, l_lo, l_hi)
        price_score = _readiness(price, p_lo, p_hi)
        score = (
            w_crit * event_criticality * lead_readiness
            + w_lead * lead_readiness
            + w_price * price_score
        )
        scored.append(
            QuoteScore(
                quote_id=str(quote["quote_id"]),
                supplier_id=str(quote.get("supplier_id", "unknown")),
                unit_price=price,
                currency=str(quote.get("currency", "")),
                lead_time_days=lead,
                on_contract=_as_bool(quote.get("on_contract", False)),
                score=score,
            )
        )

    # Deterministic: highest score first, ties broken by ascending quote_id (stable + reproducible).
    ranked = sorted(scored, key=lambda s: (-s.score, s.quote_id))
    winner = ranked[0]

    default_on_contract = rule.default_source is SourcePolicy.ON_CONTRACT
    satisfies_default = winner.on_contract is default_on_contract
    return ScoredRuleVerdict(
        selected_quote_id=winner.quote_id,
        selected_supplier_id=winner.supplier_id,
        amount=winner.unit_price * qty,
        currency=winner.currency,
        qty=qty,
        on_contract=winner.on_contract,
        source_path="default_source" if satisfies_default else "exception_policy",
        override_required=not satisfies_default,
        ranked=ranked,
    )
