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

from services.engine.procedures.runs import (
    PipelineRun,
    PipelineRunStatus,
    StepResult,
    StepResultStatus,
)

# A JSON string that is a plain integer or decimal literal — the only shape the ฿
# extract-on-read will cast. Anything else (absent, non-numeric, an object) is
# skipped and counted as ``figures_missing`` (S2 never-raise).
_NUMERIC_TEXT = r"^-?[0-9]+(\.[0-9]+)?$"

# The reasoning-trace discriminators the substrate reads (never writes).
_ECONOMIC_IMPACT = "economic_impact"
_READ_REFUSED = "read_refused"
_GATE_PRINCIPAL_RECORDED = "gate_principal_recorded"


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
    """฿ rollup for one ``currency`` x ``procedure_id`` x facet ``kind`` x ``period``
    bucket (the AC-4 grouping; S2/S7; provisional per ADR-0030).

    There is deliberately **no** cross-currency total on this model, and no report
    model may add one: a sum across currencies is unrepresentable by construction
    (S7 — the reader-side analog of ``doa_tier``'s fail-closed currency rule).
    """

    model_config = ConfigDict(extra="forbid")

    currency: str | None = Field(
        description="ISO currency of the facet; None if the facet omits it"
    )
    procedure_id: str = Field(description="the procedure whose runs carry the facet")
    facet_kind: str | None = Field(
        description="per-vertical semantic label of the impact "
        "(avoided_outage / expedite_tradeoff / …); None if the facet omits it"
    )
    period: str = Field(description="ISO date of the day bucket (date_trunc('day', started_at))")
    run_count: int = Field(description="distinct runs contributing a facet to this bucket")
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
    """Resolved-gate count for one ``procedure_id`` (steps that reached status ``resolved``).

    ``approver_recorded`` is the **approver half** AC-7 asks for. It is read from
    the step ``reasoning_trace`` — where ``resolve_gated_step`` actually records
    it — and deliberately **not** from ``run.step_principals``: every write to
    that column (``orchestrator.py`` / ``persistence.py``) stores the *requester*
    half, so an approver count sourced there would be silently wrong. AC-2's
    wording says otherwise; that is a known error, flagged for Cray rather than
    self-edited, and it is why this field names its source explicitly.
    """

    model_config = ConfigDict(extra="forbid")

    procedure_id: str = Field(description="the procedure whose gate steps resolved")
    resolved_count: int = Field(description="number of gate steps that reached status 'resolved'")
    approver_recorded: int = Field(
        description="of those resolved gates, how many carry an approver principal in the step "
        "reasoning trace (a 'gate_principal_recorded' entry with a principal_id)"
    )


class DwellStat(BaseModel):
    """Same-row wall span of the runs suspended at ``waiting_human``, per procedure.

    **Read the field descriptions before using this as "how long a human has kept a
    run waiting" — it is not that.** The span is the SAME-ROW
    ``updated_at - started_at`` (S4's only sanctioned wall-clock construct), and for
    a run whose last write was its suspension that measures **start → suspension**,
    not elapsed-since-suspension. Elapsed-since-suspension would need ``now()``,
    which is neither deterministic in a test nor trustworthy on this box's clock.
    """

    model_config = ConfigDict(extra="forbid")

    procedure_id: str = Field(description="the procedure whose runs are suspended")
    run_count: int = Field(description="runs of this procedure currently at waiting_human")
    avg_span_seconds: float = Field(
        description="mean same-row (updated_at - started_at) span, clamped at >= 0"
    )
    max_span_seconds: float = Field(
        description="maximum same-row (updated_at - started_at) span, clamped at >= 0"
    )
    negative_clock_spans: int = Field(
        description="runs whose updated_at precedes started_at — the backward-clock "
        "cases, clamped to 0 in the stats above and surfaced here, never swallowed"
    )


def _trace_elements() -> sa.TableValuedAlias:
    """A LATERAL over ``StepResult.reasoning_trace``'s array elements (``value`` column).

    Two Postgres/SQLAlchemy sharp edges are handled here, not at the call sites:

    * ``jsonb_array_elements`` raises ``cannot extract elements from a scalar`` on
      any non-array input, and a Python ``None`` written to a JSONB column lands as
      the JSON scalar ``null`` — **not** SQL ``NULL`` — so a ``reasoning_trace IS
      NOT NULL`` filter does not exclude it (and a lateral is evaluated before the
      ``WHERE`` anyway). The input is therefore guarded by ``jsonb_typeof(...) =
      'array'``, falling back to an empty array so a non-array trace contributes
      zero rows instead of raising. This is the never-raise contract in SQL form.
    * The ``value`` column is typed ``JSONB`` explicitly — an untyped table-valued
      column rejects ``[...]`` subscripting (``Operator 'getitem' is not supported``).
    """
    array_only = sa.case(
        (
            sa.func.jsonb_typeof(StepResult.reasoning_trace) == "array",
            StepResult.reasoning_trace,
        ),
        else_=sa.cast(sa.literal("[]"), JSONB),
    )
    return sa.func.jsonb_array_elements(array_only).table_valued(sa.column("value", JSONB))


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
    """฿ rollup grouped by currency x procedure x facet kind x day (AC-4 grouping).

    Facets are ``economic_impact`` entries in ``reasoning_trace``; the figure is
    ``detail->>'net_benefit_thb'`` (a JSON string). A figure absent or non-numeric
    is skipped from the sums and counted in ``figures_missing`` — never an error
    (S2 never-raise). Sums are per-currency only; no cross-currency total is
    produced or representable (S7). The period is a ``date_trunc`` **day** bucket,
    and the result is ordered in Python by the bucket labels — never by the raw
    wall clock (S4 / AC-3).
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
    facet_kind = elem.c.value["detail"]["kind"].astext
    day = sa.func.date_trunc("day", PipelineRun.started_at)
    stmt = (
        sa.select(
            currency.label("currency"),
            PipelineRun.procedure_id,
            facet_kind.label("facet_kind"),
            day.label("period"),
            sa.func.count(sa.distinct(PipelineRun.run_id)),
            sa.func.count(),
            sa.func.count(net_numeric),
            sa.func.coalesce(sa.func.sum(net_numeric), 0),
            sa.func.coalesce(sa.func.avg(net_numeric), 0),
        )
        .select_from(StepResult)
        .join(PipelineRun, PipelineRun.run_id == StepResult.run_id)
        .join(elem, sa.true())
        .where(elem.c.value["kind"].astext == _ECONOMIC_IMPACT)
        .group_by(currency, PipelineRun.procedure_id, facet_kind, day)
    )
    rows = (await session.execute(stmt)).all()
    buckets = [
        BenefitBucket(
            currency=cur,
            procedure_id=procedure_id,
            facet_kind=kind,
            period=period.date().isoformat(),
            run_count=run_count,
            facet_count=facet_count,
            figures_missing=facet_count - valued,
            net_benefit_thb_sum=Decimal(total),
            net_benefit_thb_avg=Decimal(avg),
        )
        for cur, procedure_id, kind, period, run_count, facet_count, valued, total, avg in rows
    ]
    return sorted(
        buckets,
        key=lambda b: (b.procedure_id, b.currency or "", b.facet_kind or "", b.period),
    )


async def benefit_assumptions(session: AsyncSession) -> list[str]:
    """The DISTINCT union of every disclosed modelling assumption across ฿ facets.

    ADR-0030 D3 requires each ฿ figure to disclose its assumptions; a rollup that
    aggregates figures must therefore disclose the **union** of theirs, or it
    would present a combined number with less disclosure than its parts. Returns
    O(distinct assumptions) rows, sorted for a deterministic report.

    Never-raise: a facet whose ``assumptions`` is absent or not an array simply
    contributes nothing (the same ``jsonb_typeof`` guard the trace lateral uses).
    """
    elem = _trace_elements()
    raw = elem.c.value["detail"]["assumptions"]
    array_only = sa.case(
        (sa.func.jsonb_typeof(raw) == "array", raw),
        else_=sa.cast(sa.literal("[]"), JSONB),
    )
    assumption = sa.func.jsonb_array_elements_text(array_only).table_valued("value")
    # GROUP BY rather than SELECT DISTINCT: same result set, and it keeps this
    # primitive under the same O(groups) statement-capture proof as the rollups.
    stmt = (
        sa.select(assumption.c.value)
        .select_from(StepResult)
        .join(elem, sa.true())
        .join(assumption, sa.true())
        .where(elem.c.value["kind"].astext == _ECONOMIC_IMPACT)
        .group_by(assumption.c.value)
    )
    rows = (await session.execute(stmt)).all()
    return sorted(str(value) for (value,) in rows)


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
    """Resolved-gate counts per ``procedure_id``, with the approver half (O(procedures) rows).

    The approver test is an ``EXISTS`` over the trace lateral, **not** a join to
    it. A joined lateral yields one row per trace entry, which would multiply the
    step row and inflate ``resolved_count`` — silently, since the inflated number
    still looks plausible. ``EXISTS`` asks the same question without changing the
    row count, so the statement stays O(groups) and AC-1's statement-capture
    fixture keeps holding.
    """
    elem = _trace_elements()
    approver_present = (
        sa.select(sa.literal(1))
        .select_from(elem)
        .where(elem.c.value["kind"].astext == _GATE_PRINCIPAL_RECORDED)
        .where(elem.c.value["principal_id"].astext.isnot(None))
        .correlate(StepResult)
        .exists()
    )
    stmt = (
        sa.select(
            PipelineRun.procedure_id,
            sa.func.count(),
            sa.func.count().filter(approver_present),
        )
        .join(StepResult, StepResult.run_id == PipelineRun.run_id)
        .where(StepResult.status == StepResultStatus.RESOLVED.value)
        .group_by(PipelineRun.procedure_id)
        .order_by(PipelineRun.procedure_id)
    )
    rows = (await session.execute(stmt)).all()
    return [
        GateCount(
            procedure_id=procedure_id,
            resolved_count=resolved,
            approver_recorded=approvers,
        )
        for procedure_id, resolved, approvers in rows
    ]


async def waiting_dwell_stats(session: AsyncSession) -> list[DwellStat]:
    """Same-row wall spans of the ``waiting_human`` runs, per procedure (O(procedures) rows).

    The span is ``updated_at - started_at`` **on one row** — the only wall-clock
    arithmetic S4 sanctions, because subtracting two columns of the same row cannot
    be corrupted by the clock stepping backwards *between* rows. A row whose own
    clock did step backwards (``updated_at < started_at``) still exists: its span is
    **clamped to 0** in the stats and **counted** in ``negative_clock_spans``, so the
    anomaly is reported rather than silently averaged in.
    """
    span = sa.func.extract("epoch", PipelineRun.updated_at - PipelineRun.started_at)
    clamped = sa.func.greatest(span, 0)
    stmt = (
        sa.select(
            PipelineRun.procedure_id,
            sa.func.count(),
            sa.func.coalesce(sa.func.avg(clamped), 0),
            sa.func.coalesce(sa.func.max(clamped), 0),
            sa.func.count(sa.case((span < 0, 1))),
        )
        .where(PipelineRun.status == PipelineRunStatus.WAITING_HUMAN.value)
        .group_by(PipelineRun.procedure_id)
        .order_by(PipelineRun.procedure_id)
    )
    rows = (await session.execute(stmt)).all()
    return [
        DwellStat(
            procedure_id=procedure_id,
            run_count=run_count,
            avg_span_seconds=float(avg),
            max_span_seconds=float(maximum),
            negative_clock_spans=negatives,
        )
        for procedure_id, run_count, avg, maximum, negatives in rows
    ]
