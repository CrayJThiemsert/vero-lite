"""Cross-run read/aggregate substrate over ``pipeline_runs`` / ``step_results``.

PLAN-0088 Step 1 — the L3 centre of gravity. Every Group-A run-insight reader
(A2 ฿ ROI, A3 flow, A4 audit-readiness, A1 NL-over-runs) is a thin consumer of
the primitives here, and Group B will consume the same substrate later. This
module owns **all** the cross-run SQL; readers add no SQL of their own.

Disciplines this module holds (each pinned by a static guard test):

* **Layering (S1).** SQL lives here in ``services/db``, sibling to
  ``audit_log.py``. Every function is ``async`` and is **passed** an
  ``AsyncSession`` — it opens no session and owns no transaction/commit (the
  caller does), mirroring ``audit_log.append_audit`` / ``verify_chain``.

* **Read-only (L1 / AC-11).** Nothing here writes: no ``session.add`` / ``insert``
  / ``update`` / ``delete``, and no import of the proposal / write-path
  deny-list (``RecommendedAction``, ``resolve_gated_step``, ``persist_run``,
  ``resume_run``). ``test_run_analytics_readonly_guard.py`` holds this
  statically — Group A only reads and reports.

* **Ordering soundness (S4 / AC-3).** This box's ``datetime.now(UTC)`` was
  measured stepping BACKWARDS (worst -555 ms per the ``load_run`` guard's
  doctrine), so a raw wall clock is not a sound sort key. The substrate
  therefore **never** emits ``ORDER BY`` on a raw wall-clock column
  (``started_at`` / ``created_at`` / ``updated_at``); ``test_run_analytics_
  ordering_guard.py`` fails the build if it ever does. Time-series rollups
  bucket by ``date_trunc`` at **day or coarser** — the skew is immaterial at
  that granularity (a ±1 s tolerance covers the observed step) — and any
  ordering is by the bucket label or applied in Python, never by the raw
  column. Any future reader needing strict adjacent-row ordering triggers the
  monotonic-``sequence``-column PLAN **first** (the pinned deferral,
  ``tests/services/db/test_load_run_ordering_guard.py:47-49``).

* **฿ extract-on-read (S2).** The economic-impact facet rides
  ``StepResult.reasoning_trace`` as an entry ``{"kind": "economic_impact",
  "detail": {...}}`` whose ``detail`` is ``EconomicImpact.model_dump(mode=
  "json")`` — so ``net_benefit_thb`` is a JSON **string** (Decimal never
  float). It is extracted on read (``elem->'detail'->>'net_benefit_thb'`` cast
  to numeric), never projected into a write-time column (ADR-0030 keeps the
  facet advisory / trace-carried). Extraction is **never-raise**: a facet whose
  figure is absent or non-numeric is skipped and *counted* (``figures_missing``),
  never an error.

* **Currency safety (S7).** ฿ sums exist **only per-currency**; the substrate
  never sums across currencies (no cross-currency total is representable — the
  reader-side analog of ``doa_tier``'s fail-closed currency discipline).

* **No listing primitive (SD-8 (a), ruled 2026-07-24).** The substrate ships
  aggregate primitives only. Run-listing pagination is **not** here; it is
  sequenced into the future monotonic-``sequence``-column PLAN.

Every read primitive is O(groups) in the rows it returns, never O(runs): the
aggregation happens in SQL (``GROUP BY``), and ``test_run_analytics.py``'s
statement-capture fixture pins that it stays that way.
"""

from __future__ import annotations

from decimal import Decimal

import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from services.engine.procedures.runs import PipelineRun, StepResult, StepResultStatus

# A JSON string that is a plain integer or decimal literal — the only shape the ฿
# extract-on-read will cast. Anything else (absent, non-numeric, an object) is
# skipped and counted as ``figures_missing`` (S2 never-raise).
_NUMERIC_TEXT = r"^-?[0-9]+(\.[0-9]+)?$"

# The reasoning-trace discriminators the substrate reads (never writes).
_ECONOMIC_IMPACT = "economic_impact"
_READ_REFUSED = "read_refused"


class StatusCount(BaseModel):
    """Run count for one lifecycle status (``running`` / ``completed`` / …)."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(description="PipelineRun lifecycle status")
    run_count: int = Field(description="number of runs in this status")


class ProcedureCount(BaseModel):
    """Run count for one ``procedure_id``."""

    model_config = ConfigDict(extra="forbid")

    procedure_id: str = Field(description="the procedure these runs executed")
    run_count: int = Field(description="number of runs of this procedure")


class PeriodCount(BaseModel):
    """Run count for one day-or-coarser time bucket (never a raw wall-clock sort)."""

    model_config = ConfigDict(extra="forbid")

    period: str = Field(description="ISO date of the day bucket (date_trunc('day', started_at))")
    run_count: int = Field(description="number of runs started in this bucket")


class DurationStat(BaseModel):
    """Per-``procedure_id`` x per-``step_id`` step-latency stats from ``duration_ms``."""

    model_config = ConfigDict(extra="forbid")

    procedure_id: str = Field(description="the procedure the step belongs to")
    step_id: str = Field(description="the step within the procedure")
    sample_count: int = Field(description="number of step results with a non-null duration_ms")
    avg_ms: float = Field(description="mean step latency in milliseconds")
    max_ms: int = Field(description="maximum step latency in milliseconds")


class BenefitBucket(BaseModel):
    """Per-``currency`` x per-``procedure_id`` ฿ rollup (S2/S7; provisional per ADR-0030)."""

    model_config = ConfigDict(extra="forbid")

    currency: str | None = Field(
        description="ISO currency of the facet; None if the facet omits it"
    )
    procedure_id: str = Field(description="the procedure whose runs carry the facet")
    facet_count: int = Field(description="economic_impact facets seen in this bucket")
    figures_missing: int = Field(
        description="facets whose net_benefit_thb was absent or non-numeric (skipped from the sums)"
    )
    net_benefit_thb_sum: Decimal = Field(
        description="sum of the extracted net_benefit_thb (per-currency only)"
    )
    net_benefit_thb_avg: Decimal = Field(
        description="mean of the extracted net_benefit_thb (per-currency only)"
    )
    provisional: bool = Field(
        default=True,
        description="always True — a modelled estimate, never authoritative (ADR-0030 D5)",
    )


class RefusalCount(BaseModel):
    """Read-refusal count for one ``refusal_kind`` (from the run corpus, not the audit log)."""

    model_config = ConfigDict(extra="forbid")

    refusal_kind: str | None = Field(description="the refusal kind; None if the fact omits it")
    count: int = Field(description="number of read_refused facts of this kind")


class GateCount(BaseModel):
    """Resolved-gate count for one ``procedure_id`` (steps that reached status ``resolved``)."""

    model_config = ConfigDict(extra="forbid")

    procedure_id: str = Field(description="the procedure whose gate steps resolved")
    resolved_count: int = Field(description="number of gate steps that reached status 'resolved'")


def _trace_elements() -> sa.TableValuedAlias:
    """A LATERAL over ``StepResult.reasoning_trace``'s array elements (``value`` column).

    ``jsonb_array_elements`` raises on a scalar/NULL input, so every caller pairs
    this with ``reasoning_trace IS NOT NULL``; an empty ``[]`` trace yields no rows.

    The ``value`` column is typed ``JSONB`` explicitly — an untyped table-valued
    column rejects ``[...]`` subscripting (``Operator 'getitem' is not supported``).
    """
    return sa.func.jsonb_array_elements(StepResult.reasoning_trace).table_valued(
        sa.column("value", JSONB)
    )


async def status_rollup(session: AsyncSession) -> list[StatusCount]:
    """Run counts grouped by lifecycle status (O(statuses) rows)."""
    stmt = (
        sa.select(PipelineRun.status, sa.func.count())
        .group_by(PipelineRun.status)
        .order_by(PipelineRun.status)  # a status label, never a wall clock (AC-3)
    )
    rows = (await session.execute(stmt)).all()
    return [StatusCount(status=status, run_count=count) for status, count in rows]


async def procedure_rollup(session: AsyncSession) -> list[ProcedureCount]:
    """Run counts grouped by ``procedure_id`` (O(procedures) rows)."""
    stmt = (
        sa.select(PipelineRun.procedure_id, sa.func.count())
        .group_by(PipelineRun.procedure_id)
        .order_by(PipelineRun.procedure_id)
    )
    rows = (await session.execute(stmt)).all()
    return [
        ProcedureCount(procedure_id=procedure_id, run_count=count) for procedure_id, count in rows
    ]


async def period_rollup(session: AsyncSession) -> list[PeriodCount]:
    """Run counts grouped by the **day** ``started_at`` bucket (O(days) rows).

    Buckets by ``date_trunc('day', …)`` — day granularity swamps the sub-second
    clock skew — and never orders by the raw column: results are sorted in Python
    by the bucket label (AC-3).
    """
    bucket = sa.func.date_trunc("day", PipelineRun.started_at)
    stmt = sa.select(bucket, sa.func.count()).group_by(bucket)
    rows = (await session.execute(stmt)).all()
    counts = [PeriodCount(period=day.date().isoformat(), run_count=count) for day, count in rows]
    return sorted(counts, key=lambda c: c.period)


async def duration_stats(session: AsyncSession) -> list[DurationStat]:
    """Per-procedure x per-step ``duration_ms`` count/avg/max (O(procedurexstep) rows)."""
    stmt = (
        sa.select(
            PipelineRun.procedure_id,
            StepResult.step_id,
            sa.func.count(StepResult.duration_ms),
            sa.func.avg(StepResult.duration_ms),
            sa.func.max(StepResult.duration_ms),
        )
        .join(StepResult, StepResult.run_id == PipelineRun.run_id)
        .where(StepResult.duration_ms.isnot(None))
        .group_by(PipelineRun.procedure_id, StepResult.step_id)
        .order_by(PipelineRun.procedure_id, StepResult.step_id)
    )
    rows = (await session.execute(stmt)).all()
    return [
        DurationStat(
            procedure_id=procedure_id,
            step_id=step_id,
            sample_count=count,
            avg_ms=float(avg),
            max_ms=int(maximum),
        )
        for procedure_id, step_id, count, avg, maximum in rows
    ]


async def benefit_rollup(session: AsyncSession) -> list[BenefitBucket]:
    """Per-currency x per-procedure ฿ rollup, extract-on-read + never-raise (S2/S7).

    Facets are ``economic_impact`` entries in ``reasoning_trace``; the figure is
    ``detail->>'net_benefit_thb'`` (a JSON string). A figure absent or non-numeric
    is skipped from the sums and counted in ``figures_missing``. Sums are
    per-currency only — no cross-currency total is produced (S7).
    """
    elem = _trace_elements()
    net_text = elem.c.value["detail"]["net_benefit_thb"].astext
    # Only cast a numeric-literal string; anything else -> NULL -> ignored by
    # sum/avg/count(expr), and surfaced via figures_missing = facet_count - valued.
    net_numeric = sa.cast(
        sa.case((net_text.op("~")(_NUMERIC_TEXT), net_text), else_=None),
        sa.Numeric,
    )
    currency = elem.c.value["detail"]["currency"].astext
    stmt = (
        sa.select(
            currency.label("currency"),
            PipelineRun.procedure_id,
            sa.func.count(),
            sa.func.count(net_numeric),
            sa.func.coalesce(sa.func.sum(net_numeric), 0),
            sa.func.coalesce(sa.func.avg(net_numeric), 0),
        )
        .select_from(StepResult)
        .join(PipelineRun, PipelineRun.run_id == StepResult.run_id)
        .join(elem, sa.true())
        .where(StepResult.reasoning_trace.isnot(None))
        .where(elem.c.value["kind"].astext == _ECONOMIC_IMPACT)
        .group_by(currency, PipelineRun.procedure_id)
        .order_by(PipelineRun.procedure_id)
    )
    rows = (await session.execute(stmt)).all()
    buckets = [
        BenefitBucket(
            currency=cur,
            procedure_id=procedure_id,
            facet_count=facet_count,
            figures_missing=facet_count - valued,
            net_benefit_thb_sum=Decimal(total),
            net_benefit_thb_avg=Decimal(avg),
        )
        for cur, procedure_id, facet_count, valued, total, avg in rows
    ]
    return sorted(buckets, key=lambda b: (b.procedure_id, b.currency or ""))


async def refusal_counts(session: AsyncSession) -> list[RefusalCount]:
    """Read-refusal counts grouped by ``refusal_kind`` from the run corpus (O(kinds) rows)."""
    elem = _trace_elements()
    refusal_kind = elem.c.value["refusal_kind"].astext
    stmt = (
        sa.select(refusal_kind.label("refusal_kind"), sa.func.count())
        .select_from(StepResult)
        .join(elem, sa.true())
        .where(StepResult.reasoning_trace.isnot(None))
        .where(elem.c.value["kind"].astext == _READ_REFUSED)
        .group_by(refusal_kind)
    )
    rows = (await session.execute(stmt)).all()
    counts = [RefusalCount(refusal_kind=kind, count=count) for kind, count in rows]
    return sorted(counts, key=lambda c: c.refusal_kind or "")


async def gate_counts(session: AsyncSession) -> list[GateCount]:
    """Resolved-gate counts grouped by ``procedure_id`` (O(procedures) rows)."""
    stmt = (
        sa.select(PipelineRun.procedure_id, sa.func.count())
        .join(StepResult, StepResult.run_id == PipelineRun.run_id)
        .where(StepResult.status == StepResultStatus.RESOLVED.value)
        .group_by(PipelineRun.procedure_id)
        .order_by(PipelineRun.procedure_id)
    )
    rows = (await session.execute(stmt)).all()
    return [
        GateCount(procedure_id=procedure_id, resolved_count=count) for procedure_id, count in rows
    ]
