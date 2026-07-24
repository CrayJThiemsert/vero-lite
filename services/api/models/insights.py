"""Response models for the Group-A run-insight readers (PLAN-0088).

Group A **reads and reports** — it emits no typed improvement proposal and feeds
nothing back into governance config, which is what keeps it outside the ADR-0032
D2 pilot gate (L1). These models are therefore report shapes only.

**Currency safety is structural, not conventional (S7).** ``ImpactReport`` carries
no cross-currency total field and must never gain one: ฿ sums exist only inside a
per-currency ``ImpactBucket``, so "the wrong sum" is unrepresentable rather than
merely discouraged. This mirrors ``doa_tier``'s fail-closed currency discipline on
the write path.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ImpactBucket(BaseModel):
    """One ``currency`` x ``procedure_id`` x facet ``kind`` x day bucket of the ฿ rollup."""

    model_config = ConfigDict(extra="forbid")

    currency: str | None = Field(
        description="ISO currency of the facets in this bucket; None if a facet omitted it"
    )
    procedure_id: str = Field(description="the procedure whose runs carry these facets")
    facet_kind: str | None = Field(
        description="per-vertical semantic label of the impact "
        "(avoided_outage / expedite_tradeoff / …); None if a facet omitted it"
    )
    period: str = Field(description="ISO date of the day bucket the runs started in")
    run_count: int = Field(description="distinct runs contributing a facet to this bucket")
    facet_count: int = Field(description="economic_impact facets seen in this bucket")
    figures_missing: int = Field(
        description="facets whose ฿ figure was absent or unreadable — excluded from the sums"
    )
    net_benefit_sum: Decimal = Field(
        description="sum of the readable net_benefit figures in this bucket's currency"
    )
    net_benefit_avg: Decimal = Field(
        description="mean of the readable net_benefit figures in this bucket's currency"
    )


class ImpactReport(BaseModel):
    """The A2 ฿ ROI rollup — provisional, per-currency, assumption-disclosing.

    Deliberately has **no** cross-currency total (S7); see the module docstring.
    """

    model_config = ConfigDict(extra="forbid")

    vertical: str = Field(
        description="the deployment vertical this report was produced under (S7 stamp)"
    )
    provisional: bool = Field(
        default=True,
        description="always True — every figure is a modelled estimate, "
        "never an authoritative accounting figure (ADR-0030 D5)",
    )
    buckets: list[ImpactBucket] = Field(
        description="per-currency x procedure x facet-kind x day rollup buckets"
    )
    figures_missing_total: int = Field(
        description="facets across all buckets whose ฿ figure could not be read"
    )
    assumptions: list[str] = Field(
        description="the DISTINCT union of every modelling assumption disclosed by the "
        "facets behind this report (ADR-0030 D3 — an aggregate discloses no less "
        "than its parts)"
    )
    narrative: str = Field(
        description="a deterministic, template-rendered summary of this report — "
        "no LLM is involved and every figure it cites is a value on this model"
    )
