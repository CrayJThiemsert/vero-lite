"""Box-4 economic-impact (฿) facet — engine-owned models + the advisory,
never-raise, trace-carried emission helper (ADR-0030, PLAN-0071).

The facet ties a governed action to its ฿ impact as an **advisory**
``ReasoningStep(kind="economic_impact")`` appended to the ``RecommendedAction``
reasoning trace. It NEVER alters the action, gates, reorders, or overrides
(ADR-0030 D5) — mirroring the PLAN-0035 / ADR-0022 advisory-judge discipline
(``action_verification.augment_with_advisory_judge``). Every ฿ figure is
``provisional`` and ``Decimal``-never-float (CLAUDE.md §8 assistive discipline;
the ``ledger.py`` money invariant generalized).

**Placement (ADR-0030 D1 / SD-1, PLAN-0071).** The ``EconomicImpact`` payload
rides the trace step's ``detail`` dict — it is **NOT** part of the ADR-007 D2
``RecommendedAction`` envelope contract (``services/engine/actions.py``), which
stays verbatim. The models live HERE, co-located with the helper (PLAN-0071
OQ-A resolved: keep ``actions.py`` byte-pristine), precisely because the facet
is trace-payload, not envelope contract.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Mapping
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from services.engine.actions import ReasoningStep

logger = logging.getLogger(__name__)


class EconomicExposure(BaseModel):
    """One side (baseline vs governed) of the ฿-impact ledger — generalizes the
    demo ``ImpactSide`` (``services/api/models/demo.py``) for the production facet."""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(description="what this side models, e.g. 'unmitigated over-current outage'")
    exposure_thb: Decimal = Field(
        description="total ฿ exposure on this side (Decimal — never float on money)"
    )
    components: dict[str, Decimal] = Field(
        default_factory=dict,
        description="named ฿ parts, e.g. {'downtime_thb': ..., 'part_cost_thb': ...}",
    )


class EconomicImpact(BaseModel):
    """The typed, advisory Box-4 economic-impact facet — the ``detail`` payload of
    an ``economic_impact`` ``ReasoningStep``. This is a **trace-step payload, NOT
    part of the ADR-007 D2 ``RecommendedAction`` envelope contract** (ADR-0030
    D1/SD-1); it is carried inside the step's ``detail`` dict, so the envelope
    stays verbatim. Producer-validated (the ``net_benefit_thb`` arithmetic is
    enforced below), so a producer cannot emit an inconsistent figure."""

    model_config = ConfigDict(extra="forbid")

    provisional: bool = Field(
        description="always True in v1 — a modelled estimate, never authoritative (ADR-0030 D5, §8)"
    )
    currency: str = Field(description="ISO currency code; THB-only in v1 (ADR-0030 OQ-4)")
    kind: str = Field(
        description="per-vertical semantic label (avoided_outage / expedite_tradeoff / "
        "spoilage_avoided / mortality_avoided)"
    )
    baseline: EconomicExposure = Field(description="the ungoverned / do-nothing exposure")
    governed: EconomicExposure = Field(description="the governed action's exposure")
    net_benefit_thb: Decimal = Field(
        description="baseline.exposure_thb - governed.exposure_thb (validated below)"
    )
    assumptions: list[str] = Field(
        description="disclosed modelling assumptions — every non-column input, named (ADR-0030 D3)"
    )
    basis_refs: list[str] = Field(
        default_factory=list,
        description="entity/column refs the figures derive from (e.g. CSV columns)",
    )

    @model_validator(mode="after")
    def _check_net_benefit(self) -> EconomicImpact:
        """The net benefit MUST equal baseline-minus-governed exposure — a producer
        cannot emit an inconsistent ฿ figure (a mismatch raises ``ValidationError``)."""
        expected = self.baseline.exposure_thb - self.governed.exposure_thb
        if self.net_benefit_thb != expected:
            raise ValueError(
                f"net_benefit_thb ({self.net_benefit_thb}) must equal baseline.exposure_thb "
                f"- governed.exposure_thb ({expected})"
            )
        return self


# A producer computes a vertical's EconomicImpact for a trigger event, or returns
# None when it cannot ground a ฿ figure (never guess). Async: procurement fetches
# adapter objects; assumption-based producers are pure but keep the async signature
# uniform so the helper awaits every producer identically.
EconomicProducer = Callable[[Mapping[str, Any], str], Awaitable["EconomicImpact | None"]]

_PRODUCERS: dict[str, EconomicProducer] = {}


def register_economic_producer(vertical: str, producer: EconomicProducer) -> None:
    """Register the ฿-impact producer for a vertical (ADR-0023 registry discipline)."""
    _PRODUCERS[vertical] = producer


def clear_economic_producers() -> None:
    """Test-only: reset the producer registry (mirrors the discovery-registry disciplines)."""
    _PRODUCERS.clear()


def registered_economic_verticals() -> frozenset[str]:
    """The verticals with a registered ฿-impact producer (read-only snapshot)."""
    return frozenset(_PRODUCERS)


async def build_economic_steps(event: Mapping[str, Any], vertical: str) -> list[ReasoningStep]:
    """Advisory, **never-raise** emission of the ``economic_impact`` facet.

    Returns exactly one ``economic_impact`` ``ReasoningStep`` on success, or ``[]``
    when: no producer is registered for the vertical, the producer returns ``None``
    (a ฿ figure could not be grounded — never guessed), **or the producer raises**.

    The raise branch is load-bearing. This helper is awaited **inside**
    ``recommender.recommend()``'s IN-4 ``try`` (``recommender.py``), so a propagating
    exception would be caught by that fail-safe and **demote a good LLM judgment to
    the deterministic ``_rule_recommend`` path** — strictly worse than losing an
    advisory facet. So, exactly like the advisory judge
    (``action_verification.augment_with_advisory_judge``; the never-raise contract
    documented at ``recommender.py`` around the judge call), this function NEVER
    raises: it logs a warning and returns ``[]``. The facet is advisory (ADR-0030
    D5) — its absence never harms the action.
    """
    producer = _PRODUCERS.get(vertical)
    if producer is None:
        return []
    try:
        impact = await producer(event, vertical)
    except Exception as exc:  # advisory must never harm the action (ADR-0030 D5; IN-4 protection)
        logger.warning(
            "economic-impact producer for vertical '%s' raised; omitting the advisory facet "
            "(never demote the action to the rule fail-safe): %s",
            vertical,
            exc,
            exc_info=True,
        )
        return []
    if impact is None:
        return []
    net = impact.net_benefit_thb
    return [
        ReasoningStep(
            step_id="economic-impact-0",
            kind="economic_impact",
            summary=(
                f"Economic impact ({impact.kind}): net benefit ~฿{net:,} vs the ungoverned "
                f"baseline (provisional estimate)."
            ),
            detail=impact.model_dump(mode="json"),
        )
    ]
