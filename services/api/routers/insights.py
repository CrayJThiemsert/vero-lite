"""Group-A run-insight readers (PLAN-0088) — reader A2: the ฿ ROI rollup.

Thin by construction: every figure comes from ``services/db/run_analytics.py``
(the L3 substrate); this module adds **no SQL of its own** and holds no write
primitive — ``test_run_analytics_readonly_guard.py`` (AC-11) enforces both
statically, which is what makes L1's "Group A only reads and reports" mechanical
rather than documentary.

Two report properties are load-bearing and are pinned by tests, not by care:

* **Per-currency only (S7).** ``ImpactReport`` has no cross-currency total field,
  so a sum across currencies cannot be expressed even by accident.
* **Deterministic narrative (AC-5).** ``render_impact_narrative`` is a pure
  template over the report — no LLM, no ambient state — and every figure it
  prints is a value already on the report, so the prose cannot drift from the
  numbers it claims to summarise.

Vocabulary: every reader-facing string here obeys the positioning rule at
``docs/adr/0032-strategic-frame-demo-to-pilot-wedge-and-3-shape-roadmap.md:224-226``
(ADR-0032 D5), which names two phrases that must never be said to an operations
buyer. The phrases are deliberately NOT quoted in this module — they live only in
``tests/api/test_insights_narrative.py``, so the grep-style guard can scan this
source without matching its own documentation.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.config import settings
from services.api.models.insights import (
    AuditReadinessReport,
    DwellBucket,
    FlowReport,
    GateReadiness,
    ImpactBucket,
    ImpactReport,
    RefusalTally,
    StatusTally,
    StepLatency,
)
from services.db import run_analytics
from services.db.audit_log import verify_chain
from services.db.session import get_session

router = APIRouter(prefix="/insights", tags=["insights"])


def _money(value: Decimal) -> str:
    """฿ with thousands separators, matching the shipped facet summary style."""
    return f"~฿{value:,}"


def render_impact_narrative(
    report_vertical: str,
    buckets: list[ImpactBucket],
    assumptions: list[str],
    figures_missing_total: int,
) -> str:
    """Render the rollup as deterministic prose — no LLM, no randomness.

    Every figure printed here is read straight off ``buckets`` / the counts passed
    in, so the narrative cannot cite a number the report does not carry (AC-5).
    """
    lines = [
        f"Governed-run economic impact — {report_vertical} (provisional estimate).",
    ]
    if not buckets:
        lines.append("No runs carried an economic-impact figure in this corpus.")
    else:
        currencies = sorted({b.currency or "unspecified" for b in buckets})
        lines.append(
            f"{len(buckets)} bucket(s) across {len(currencies)} currency/currencies: "
            f"{', '.join(currencies)}."
        )
        for bucket in buckets:
            lines.append(
                f"  {bucket.currency or 'unspecified'} · {bucket.procedure_id} · "
                f"{bucket.facet_kind or 'unspecified'} · {bucket.period}: "
                f"{bucket.run_count} run(s), net benefit {_money(bucket.net_benefit_sum)} "
                f"(avg {_money(bucket.net_benefit_avg)})."
            )
    if figures_missing_total:
        lines.append(
            f"{figures_missing_total} facet(s) carried no readable figure and are "
            "excluded from every total above."
        )
    if assumptions:
        lines.append("Assumptions disclosed: " + "; ".join(assumptions) + ".")
    return "\n".join(lines)


@router.get("/impact", response_model=ImpactReport)
async def impact_rollup(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ImpactReport:
    """Report the ฿ ROI of governed runs, grouped by currency, procedure, kind and day.

    Read-only: it calls the substrate's aggregate primitives and shapes the result.
    Figures are provisional modelled estimates (ADR-0030 D5), summed **per
    currency only** (S7), and the union of every assumption behind them is
    disclosed alongside (ADR-0030 D3).
    """
    rollup = await run_analytics.benefit_rollup(session)
    assumptions = await run_analytics.benefit_assumptions(session)
    buckets = [
        ImpactBucket(
            currency=row.currency,
            procedure_id=row.procedure_id,
            facet_kind=row.facet_kind,
            period=row.period,
            run_count=row.run_count,
            facet_count=row.facet_count,
            figures_missing=row.figures_missing,
            net_benefit_sum=row.net_benefit_thb_sum,
            net_benefit_avg=row.net_benefit_thb_avg,
        )
        for row in rollup
    ]
    figures_missing_total = sum(b.figures_missing for b in buckets)
    vertical = settings.oct_vertical
    return ImpactReport(
        vertical=vertical,
        provisional=True,
        buckets=buckets,
        figures_missing_total=figures_missing_total,
        assumptions=assumptions,
        narrative=render_impact_narrative(vertical, buckets, assumptions, figures_missing_total),
    )


@router.get("/flow", response_model=FlowReport)
async def flow_report(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FlowReport:
    """Report where governed runs spend time: per-step latency and suspension spans.

    Zero LLM, read-only. Step latency comes from the per-step ``duration_ms``
    telemetry, never from subtracting timestamps across rows. Suspension spans are
    same-row ``updated_at - started_at``, clamped at >= 0, with the backward-clock
    rows counted in ``negative_clock_spans`` rather than averaged in — this box's
    wall clock is known to step backwards, and the report says so instead of
    quietly absorbing it.
    """
    latency = await run_analytics.duration_stats(session)
    dwell = await run_analytics.waiting_dwell_stats(session)
    steps = [
        StepLatency(
            procedure_id=row.procedure_id,
            step_id=row.step_id,
            sample_count=row.sample_count,
            avg_ms=row.avg_ms,
            max_ms=row.max_ms,
        )
        for row in latency
    ]
    # Slowest-first: a bottleneck report that makes the reader sort it themselves
    # has not reported the bottleneck. Ordering is applied here, in Python, on a
    # latency value — never as SQL ORDER BY on a wall-clock column (S4 / AC-3).
    steps.sort(key=lambda s: (-s.max_ms, s.procedure_id, s.step_id))
    dwell_buckets = [
        DwellBucket(
            procedure_id=row.procedure_id,
            run_count=row.run_count,
            avg_span_seconds=row.avg_span_seconds,
            max_span_seconds=row.max_span_seconds,
            negative_clock_spans=row.negative_clock_spans,
        )
        for row in dwell
    ]
    return FlowReport(
        vertical=settings.oct_vertical,
        steps=steps,
        dwell=dwell_buckets,
        negative_clock_spans=sum(b.negative_clock_spans for b in dwell_buckets),
    )


@router.get("/audit-readiness", response_model=AuditReadinessReport)
async def audit_readiness_report(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuditReadinessReport:
    """Compose what an auditor asks for first: coverage, gates, refusals, chain verdict.

    Three substrate reads plus the shipped ``verify_chain`` seam — no SQL of its
    own (L3), no write primitive (AC-11), zero LLM.

    **Split visibility (AC-7).** ``verify_chain`` returns verbatim break strings.
    They are reduced to a boolean on the next line and never leave this function,
    and ``AuditReadinessReport`` has no field that could carry them — so no
    caller, credentialed or not, can read a break string here. That is strictly
    narrower than ``GET /audit/verify`` (which discloses ``intact`` to everyone
    and the detail to a credentialed caller, SD-2(d)), so this reader widens no
    disclosure and needs no auth dependency of its own.
    """
    statuses = await run_analytics.status_rollup(session)
    gates = await run_analytics.gate_counts(session)
    refusals = await run_analytics.refusal_counts(session)
    breaks = await verify_chain(session)
    return AuditReadinessReport(
        vertical=settings.oct_vertical,
        statuses=[StatusTally(status=row.status, run_count=row.run_count) for row in statuses],
        gates=[
            GateReadiness(
                procedure_id=row.procedure_id,
                resolved_count=row.resolved_count,
                approver_recorded=row.approver_recorded,
            )
            for row in gates
        ],
        refusals=[RefusalTally(refusal_kind=row.refusal_kind, count=row.count) for row in refusals],
        chain_intact=not breaks,
    )
