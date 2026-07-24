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


class StepLatency(BaseModel):
    """Per-``procedure_id`` x per-``step_id`` step latency, from ``duration_ms`` telemetry."""

    model_config = ConfigDict(extra="forbid")

    procedure_id: str = Field(description="the procedure the step belongs to")
    step_id: str = Field(description="the step within the procedure")
    sample_count: int = Field(description="step results carrying a duration_ms reading")
    avg_ms: float = Field(description="mean step latency in milliseconds")
    max_ms: int = Field(description="slowest observed step latency in milliseconds")


class DwellBucket(BaseModel):
    """Wall span of one procedure's runs currently suspended at ``waiting_human``.

    **The span is `updated_at - started_at` read off a SINGLE row** — the only
    wall-clock arithmetic this platform trusts, because subtracting two columns of
    the same row cannot be corrupted by the clock stepping backwards between rows.
    For a run whose last write was its suspension, that measures **start ->
    suspension**, NOT elapsed-since-suspension; the latter would need `now()`,
    which is neither reproducible in a test nor trustworthy on this host.
    """

    model_config = ConfigDict(extra="forbid")

    procedure_id: str = Field(description="the procedure whose runs are suspended")
    run_count: int = Field(description="runs of this procedure at waiting_human")
    avg_span_seconds: float = Field(description="mean same-row span in seconds, clamped at >= 0")
    max_span_seconds: float = Field(description="longest same-row span in seconds, clamped at >= 0")
    negative_clock_spans: int = Field(
        description="runs in this bucket whose updated_at precedes started_at"
    )


class FlowReport(BaseModel):
    """The A3 bottleneck / cycle-time report — deterministic, zero LLM."""

    model_config = ConfigDict(extra="forbid")

    vertical: str = Field(
        description="the deployment vertical this report was produced under (S7 stamp)"
    )
    steps: list[StepLatency] = Field(
        description="per-procedure x per-step latency, slowest-first by max_ms"
    )
    dwell: list[DwellBucket] = Field(
        description="per-procedure wall spans of the runs suspended at waiting_human"
    )
    negative_clock_spans: int = Field(
        description="total runs whose updated_at precedes started_at — a backward-clock "
        "anomaly surfaced rather than silently averaged into the spans above"
    )


class StatusTally(BaseModel):
    """Run count for one lifecycle status."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(description="PipelineRun lifecycle status")
    run_count: int = Field(description="number of runs in this status")


class GateReadiness(BaseModel):
    """Resolved-gate counts for one procedure, with the approver half."""

    model_config = ConfigDict(extra="forbid")

    procedure_id: str = Field(description="the procedure whose gate steps resolved")
    resolved_count: int = Field(description="gate steps that reached status 'resolved'")
    approver_recorded: int = Field(
        description="of those, how many carry a recorded approver principal in the step "
        "reasoning trace — the way resolve_gated_step records it, not step_principals "
        "(which holds the requester half)"
    )


class RefusalTally(BaseModel):
    """Read-refusal count for one refusal kind."""

    model_config = ConfigDict(extra="forbid")

    refusal_kind: str | None = Field(description="the refusal kind; None if the fact omits it")
    count: int = Field(description="number of read_refused facts of this kind")


class AuditReadinessReport(BaseModel):
    """The A4 audit-readiness composition — what an auditor asks for first.

    **Split visibility is structural, not conventional (AC-7).** This model
    carries no ``breaks`` field and must never gain one: the chain verdict is
    reduced to ``chain_intact`` at the call site and the verbatim break strings
    are discarded there, so disclosing one through this reader is
    *unrepresentable* rather than merely avoided — the same technique
    ``ImpactReport`` uses for the cross-currency total (S7).

    This is strictly narrower than ``GET /audit/verify``, which already discloses
    ``intact`` to every caller and the verbatim detail only to a credentialed one
    (SD-2(d)). A4 therefore widens no disclosure and needs no auth dependency of
    its own — there is nothing here to split.
    """

    model_config = ConfigDict(extra="forbid")

    vertical: str = Field(
        description="the deployment vertical this report was produced under (S7 stamp)"
    )
    statuses: list[StatusTally] = Field(description="run totals by lifecycle status")
    gates: list[GateReadiness] = Field(
        description="resolved-gate counts per procedure, with the approver half"
    )
    refusals: list[RefusalTally] = Field(description="read-refusal counts by kind")
    chain_intact: bool = Field(
        description="whether the audit hash chain verified end to end; the verbatim break "
        "detail is deliberately not carried on this report (see the class docstring)"
    )
