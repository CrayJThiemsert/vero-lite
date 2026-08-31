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

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

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
# A human reject. The principal tie is recorded on BOTH outcomes, so its presence
# cannot discriminate approve from reject — only this entry can (action_step.py).
_ACTION_REJECTED = "action_rejected"

# Step-audit / step-artifact keys the substrate reads (Step 6 / AC-10).
# ``governed_decision`` is an ARRAY of ties, each naming the control it resolved
# and the principal who acted; ``output_set`` is the judged-entity list an
# evaluate step writes, each entity carrying its own verdict + reading.
_GOVERNED_DECISION = "governed_decision"
_DOA_TIER = "doa_tier"
_OUTPUT_SET = "output_set"


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


class ProjectedByRun(BaseModel):
    """The PROJECTED side of the realized-vs-projected join, aggregated over a run set.

    The per-run ``net_benefit_thb`` sum is an **inner subquery** (``GROUP BY
    run_id``); only these aggregates escape, so the result stays O(1) and SD-8 (a)
    holds — the same ordering ``run_duration_totals`` uses, and the reason this is
    a new primitive rather than a reuse of ``benefit_rollup`` (which groups by
    currency x procedure x facet-kind x day and yields no per-run figure at all).

    🔴 **Read ``projected_net_benefit_thb`` as a MODELLED AVOIDED COST, not as
    money that moved.** Every fleet facet is ``overpay_avoided`` — a fraction of
    the quoted amount that a price comparison is assumed to recover
    (``verticals/fleet_maintenance/economic_impact.py``), and ``provisional`` is
    ``True`` by construction for every producer (ADR-0030 D5). Pairing it against
    an invoice total would compare a modelled *benefit* against an actual *cost*:
    two different quantities. What the realized side can honestly be paired with
    is ``projected_governed_exposure_thb`` — the price the model expected to be
    paid — which is why that field is carried separately rather than derived by
    the reader.
    """

    model_config = ConfigDict(extra="forbid")

    run_count: int = Field(
        description="runs in the requested set that carry any economic_impact facet"
    )
    figures_missing: int = Field(
        description="facets whose net_benefit_thb was absent or non-numeric (skipped from the sums)"
    )
    projected_net_benefit_thb: Decimal = Field(
        description="sum of per-run modelled net benefit — an AVOIDED cost, never money that moved"
    )
    projected_governed_exposure_thb: Decimal = Field(
        description="sum of per-run governed.exposure_thb — the price the model EXPECTED to be "
        "paid, and the only projected figure an invoice total is comparable with"
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


class RunStatusCount(BaseModel):
    """Run count for one ``procedure_id`` x lifecycle-status pair (Step 4.5 / SD-9 (a2)).

    The conjunctive grouping the shipped Step-1 rollups could not express: neither
    ``procedure_rollup`` nor ``status_rollup`` can answer "how many runs of
    procedure X failed?", because each collapses the other dimension. Grouping on
    both keeps the answer a row lookup and the statement O(procedures x statuses)
    — no caller-supplied filter, so nothing here weakens AC-1's O(groups) proof.
    """

    model_config = ConfigDict(extra="forbid")

    procedure_id: str = Field(description="the procedure these runs executed")
    status: str = Field(description="PipelineRun lifecycle status")
    run_count: int = Field(description="runs of this procedure in this status")


class RunDurationTotal(BaseModel):
    """Per-run ``duration_ms`` totals, aggregated per procedure x status (Step 4.5).

    ``duration_stats`` is per-**step** across runs, so a single run's total is not
    recoverable from it. Here the per-run SUM is computed in an **inner subquery**
    and only its aggregate escapes: the outer statement returns
    O(procedures x statuses) rows, never one per run, so no listing shape appears
    (SD-8 (a) stays intact) and the statement-capture fixture keeps holding.
    """

    model_config = ConfigDict(extra="forbid")

    procedure_id: str = Field(description="the procedure these runs executed")
    status: str = Field(description="PipelineRun lifecycle status")
    run_count: int = Field(description="runs contributing a duration total to this bucket")
    avg_total_ms: float = Field(description="mean of the per-run summed duration_ms")
    max_total_ms: int = Field(description="largest per-run summed duration_ms")


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


class VerdictReadingStat(BaseModel):
    """Band-verdict distribution + the measured readings behind it (AC-10 B1).

    The pairing is the point: a verdict label alone is a bare count, but the
    reading that PRODUCED it is what band recalibration needs. Both live on the
    same judged entity (``evaluate_step`` writes ``{**entity, "verdict": ...}``),
    so neither has to be joined back to the other.
    """

    model_config = ConfigDict(extra="forbid")

    verdict: str | None = Field(
        description="band verdict label (breach / watch / ok); None if the entity omits it"
    )
    entity_count: int = Field(description="entities judged into this verdict across all band steps")
    reading_count: int = Field(description="entities whose measured_value was present and numeric")
    readings_missing: int = Field(
        description="entities whose measured_value was absent or non-numeric — skipped "
        "from the stats and counted here, never an error (the S2 never-raise contract)"
    )
    avg_reading: Decimal = Field(description="mean measured_value of this verdict's entities")
    max_reading: Decimal = Field(description="maximum measured_value of this verdict's entities")


class GateTierOutcome(BaseModel):
    """Approval outcome + gate dwell for one resolved DoA tier x outcome (AC-10 B2)."""

    model_config = ConfigDict(extra="forbid")

    doa_tier: str | None = Field(
        description="resolved doa_tier control id, from the step audit's governed_decision "
        "tie; None if the tie omits it"
    )
    outcome: str = Field(
        description="approved or rejected. A reject is an action_rejected trace entry — "
        "the gate_principal_recorded tie is written on BOTH outcomes, so it cannot "
        "discriminate them"
    )
    gate_count: int = Field(description="resolved gate steps tied to this tier with this outcome")
    avg_duration_ms: float = Field(
        description="mean gate-step duration_ms — a SAME-ROW datum, the only dwell "
        "measure S4 sanctions (no cross-row wall-clock arithmetic)"
    )
    max_duration_ms: int = Field(description="maximum gate-step duration_ms")


class RefusalProcedureCount(BaseModel):
    """Read-refusal count for one ``refusal_kind`` x ``procedure_id`` pair (AC-10 B3)."""

    model_config = ConfigDict(extra="forbid")

    refusal_kind: str | None = Field(description="the refusal kind; None if the fact omits it")
    procedure_id: str = Field(description="the procedure whose run carried the refusal")
    count: int = Field(description="number of read_refused facts of this kind in this procedure")


class TriggerOutcomeCount(BaseModel):
    """Run count for one ``procedure_id`` x trigger x terminal status triple (AC-10 B4)."""

    model_config = ConfigDict(extra="forbid")

    procedure_id: str = Field(description="the procedure these runs executed")
    trigger: str | None = Field(
        description="how the run started, from trigger_context->>'trigger' — the shipped "
        "Trigger vocabulary (manual / schedule / event); None for a run stamped without it"
    )
    status: str = Field(description="PipelineRun lifecycle status")
    run_count: int = Field(description="runs matching this procedure x trigger x status")


def _jsonb_array(source: sa.ColumnElement[Any]) -> sa.TableValuedAlias:
    """A LATERAL over a JSONB array-valued expression (``value`` column).

    The array-guard + explicit ``JSONB`` typing rationale is
    ``_trace_elements``'; this is the same contract for the step ``audit`` and
    ``artifact`` sub-arrays the Group-B shapes read. A missing key yields SQL
    ``NULL`` -> ``jsonb_typeof`` NULL -> the empty-array fallback, so an absent
    or scalar value contributes zero rows rather than raising.
    """
    array_only = sa.case(
        (sa.func.jsonb_typeof(source) == "array", source),
        else_=sa.cast(sa.literal("[]"), JSONB),
    )
    return sa.func.jsonb_array_elements(array_only).table_valued(sa.column("value", JSONB))


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


async def run_status_rollup(session: AsyncSession) -> list[RunStatusCount]:
    """Run counts grouped by ``procedure_id`` x ``status`` (O(procedures x statuses) rows).

    Step 4.5 / SD-9 (a2). Ordering is by the two label columns, never a wall clock.
    """
    stmt = (
        sa.select(PipelineRun.procedure_id, PipelineRun.status, sa.func.count())
        .group_by(PipelineRun.procedure_id, PipelineRun.status)
        .order_by(PipelineRun.procedure_id, PipelineRun.status)
    )
    rows = (await session.execute(stmt)).all()
    return [
        RunStatusCount(procedure_id=procedure_id, status=status, run_count=count)
        for procedure_id, status, count in rows
    ]


async def week_rollup(session: AsyncSession) -> list[PeriodCount]:
    """Run counts grouped by the **ISO week** ``started_at`` bucket (O(weeks) rows).

    Symmetric with ``period_rollup`` and coarser than it, so the S4 skew argument
    holds a fortiori (a ±1 s clock step cannot move a run across a week boundary
    that a day bucket would already have absorbed). ``date_trunc('week', …)``
    yields the Monday of the week; the label is that Monday's ISO date. Sorted in
    Python by label — never ``ORDER BY`` on the raw column (AC-3).
    """
    bucket = sa.func.date_trunc("week", PipelineRun.started_at)
    stmt = sa.select(bucket, sa.func.count()).group_by(bucket)
    rows = (await session.execute(stmt)).all()
    counts = [PeriodCount(period=week.date().isoformat(), run_count=count) for week, count in rows]
    return sorted(counts, key=lambda c: c.period)


async def run_duration_totals(session: AsyncSession) -> list[RunDurationTotal]:
    """Per-run ``duration_ms`` totals, aggregated per procedure x status (Step 4.5).

    The per-run SUM is an **inner subquery** (`GROUP BY run_id`); the outer
    statement aggregates *those* totals per procedure x status. That ordering
    matters: summing in the outer query would multiply nothing but would also
    never yield a per-run figure, and returning the inner rows directly would be
    a listing shape — O(runs) — which SD-8 (a) eliminated. Only the aggregate
    escapes, so fetched rows stay O(groups) and AC-1's statement-capture proof is
    unweakened.
    """
    per_run = (
        sa.select(
            StepResult.run_id.label("run_id"),
            sa.func.sum(StepResult.duration_ms).label("total_ms"),
        )
        .where(StepResult.duration_ms.isnot(None))
        .group_by(StepResult.run_id)
        .subquery()
    )
    stmt = (
        sa.select(
            PipelineRun.procedure_id,
            PipelineRun.status,
            sa.func.count(),
            sa.func.avg(per_run.c.total_ms),
            sa.func.max(per_run.c.total_ms),
        )
        .join(per_run, per_run.c.run_id == PipelineRun.run_id)
        .group_by(PipelineRun.procedure_id, PipelineRun.status)
        .order_by(PipelineRun.procedure_id, PipelineRun.status)
    )
    rows = (await session.execute(stmt)).all()
    return [
        RunDurationTotal(
            procedure_id=procedure_id,
            status=status,
            run_count=count,
            avg_total_ms=float(avg),
            max_total_ms=int(maximum),
        )
        for procedure_id, status, count, avg, maximum in rows
    ]


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

    🔴 **DO NOT reuse this for the ฿ realized-vs-projected join.** A framing that
    circulated for several sessions said this primitive "already extracts
    ``net_benefit_thb`` by ``run_id``". **It does not** — it groups by currency x
    procedure x facet-kind x day and touches ``run_id`` only inside a
    ``count(distinct ...)``, so it yields **no per-run figure at all**. The join
    needs a **NEW per-run aggregation**; the pattern to copy is the per-run
    ``GROUP BY`` inner subquery in ``run_duration_totals`` above, not this.

    Three constraints on that work, all TEST-PINNED, measured s226 and corrected
    s232 (re-priced honestly: ~150-250 lines across 6-7 files, ONE PR — the
    circulating "~40 lines by reusing benefit_rollup" figure was checked and is
    WRONG):

    (a) **SD-8(a) forbids O(runs) result shapes**, pinned by
        ``tests/services/db/test_run_analytics.py::test_aggregation_is_pushed_to_sql_not_python``
        with statement capture. ⚠️ That pin holds only for the **eleven
        primitives hard-coded in its own tuple**, and only when Postgres is
        reachable — a *new* O(runs) reader would **not** automatically redden CI.
        So "per-run rows on screen" is a design decision, not a mechanical add.
    (b) ``tests/api/test_export_cover_ui_contract.py`` asserts **set equality**
        against an **empty** ``_UNREAD_COVER_FIELDS``, so a new
        ``ExportCoverResponse`` field **must ship with its ``view-export.js``
        tile in the SAME PR** or CI reddens.
    (c) ``/insights/impact`` is **ABSENT from fleet's Cloudflare allowlist**, so
        the figure must ride the existing cover response. _[Corrected s232,
        ``was an error``: the older note called that route "the only existing
        consumer of the projected side". It is not — ``_aggregate_benefit`` in
        ``services/engine/run_query.py`` consumes this function and **is**
        reachable on fleet via the allowlisted ``^/query$``. The conclusion
        survives; the premise under it was false.]_

    ✅ **No migration is needed:** the realized side already carries ``total_thb``
    and ``run_id`` on the **same** ``ExportRow`` (``services/db/repair_spend_export.py``,
    linked via ``RepairCaseRunLink``). Lands on Tab J, which fleet publishes.

    🔴 **A FOURTH constraint, measured s265 and missing from the three above: the
    join is not expressible yet at all.** Everything this docstring says about the
    REALIZED side and the pattern to copy is correct and still stands. What it
    never surfaced is that ONE RUN CARRIES MANY ``economic_impact`` FACETS, one
    per priced repair — the seeded history run carries two — while an
    ``ExportRow`` is one invoice for ONE repair. Pairing at ``run_id`` grain
    therefore mixes an unrelated repair's projection into the figure (measured:
    off by ฿40,800 on a ฿31,500 row), and the facet carries **no case reference**
    to pair at case grain instead. Read the block above ``benefit_assumptions``
    for the measurement and Cray's s265 ruling — attribute the facet first.

    _[Rehomed from ``docs/STATUS.md`` at session 235 under R2's carve-out.]_
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


async def projected_by_run(
    session: AsyncSession, run_ids: Sequence[str] | None = None
) -> ProjectedByRun:
    """The projected ฿ side, summed per run then aggregated over ``run_ids``.

    ``run_ids=None`` means the whole corpus, which is what lets this primitive join
    the SD-8 (a) statement-capture tuple in
    ``tests/services/db/test_run_analytics.py::test_aggregation_is_pushed_to_sql_not_python``
    — that guard calls every primitive as ``primitive(session)``. A new O(runs)
    reader would NOT redden CI on its own (the tuple is hard-coded), so this
    function is added to it in the same change that adds the function.

    The per-run SUM is the inner subquery; the outer statement aggregates *those*
    totals. Absent or non-numeric figures are skipped from the sums and counted in
    ``figures_missing`` — never an error (S2 never-raise), and never coerced to
    zero, which would silently report a missing model as a break-even one.
    """
    elem = _trace_elements()
    net_text = elem.c.value["detail"]["net_benefit_thb"].astext
    governed_text = elem.c.value["detail"]["governed"]["exposure_thb"].astext
    # Only cast a numeric-literal string; anything else -> NULL -> ignored by
    # sum/count(expr), and surfaced via figures_missing. Same guard as benefit_rollup.
    net_numeric = sa.cast(
        sa.case((net_text.op("~")(_NUMERIC_TEXT), net_text), else_=None), sa.Numeric
    )
    governed_numeric = sa.cast(
        sa.case((governed_text.op("~")(_NUMERIC_TEXT), governed_text), else_=None), sa.Numeric
    )
    per_run = (
        sa.select(
            StepResult.run_id.label("run_id"),
            sa.func.count().label("facet_count"),
            sa.func.count(net_numeric).label("valued"),
            sa.func.coalesce(sa.func.sum(net_numeric), 0).label("net_thb"),
            sa.func.coalesce(sa.func.sum(governed_numeric), 0).label("governed_thb"),
        )
        .select_from(StepResult)
        .join(elem, sa.true())
        .where(elem.c.value["kind"].astext == _ECONOMIC_IMPACT)
    )
    if run_ids is not None:
        per_run = per_run.where(StepResult.run_id.in_(run_ids))
    per_run_sub = per_run.group_by(StepResult.run_id).subquery()
    stmt = sa.select(
        sa.func.count(),
        sa.func.coalesce(sa.func.sum(per_run_sub.c.facet_count - per_run_sub.c.valued), 0),
        sa.func.coalesce(sa.func.sum(per_run_sub.c.net_thb), 0),
        sa.func.coalesce(sa.func.sum(per_run_sub.c.governed_thb), 0),
    )
    row = (await session.execute(stmt)).one()
    run_count, missing, net_total, governed_total = row
    return ProjectedByRun(
        run_count=int(run_count),
        figures_missing=int(missing),
        projected_net_benefit_thb=Decimal(net_total),
        projected_governed_exposure_thb=Decimal(governed_total),
    )


# --------------------------------------------------------------------------- #
# 🔴 `realized_vs_projected` IS NOT BUILT, and the reason is not effort — the
# join is NOT EXPRESSIBLE over the data on disk today (CLAUDE.md §8: a case the
# system cannot express is registered as inexpressible, in writing, with its
# reason). MEASURED s265 against the real seed driven through the real engine,
# NOT reasoned about:
#
#   realized side  — the month-end export carries ONE row for the settled demo
#                    case: pre-VAT ฿31,500.00 / VAT ฿2,205.00 / total ฿33,705.00.
#   projected side — the SAME run carries TWO `overpay_avoided` facets:
#                      #1  baseline ฿48,000 -> governed ฿40,800  (net ฿7,200)
#                      #2  baseline ฿31,500 -> governed ฿26,775  (net ฿4,725)
#                    Facet #2 is this repair (฿31,500 matches the accepted quote
#                    and `amount_pre_vat_thb` exactly). Facet #1 is a DIFFERENT
#                    repair that happens to share the run.
#
# So a pairing at RUN grain — which is the only grain `projected_by_run` above
# can offer — reports ฿31,500 - ฿67,575 = **-฿36,075**, wrong by ฿40,800, i.e.
# by one whole unrelated repair. The VAT question that looked like the hard part
# is ฿2,205 — a rounding error against that.
#
# Case grain is the correct grain and CANNOT BE RESOLVED: the facet carries no
# case reference. Its keys are {detail, kind, step_id, summary}; `detail` holds
# {assumptions, baseline, basis_refs, currency, governed, kind, net_benefit_thb,
# provisional}; and BOTH facets above share `step_id == "economic-impact-0"`, so
# step_id does not disambiguate them either. The only discriminator left is
# `detail.baseline.components.quoted_repair_thb` — i.e. an exact-match join on a
# money amount, which is a coincidence detector, not an identity.
#
# RULED (Cray, typed, s265): make it expressible first — attribute the facet to
# its case at emission time — THEN build the pairing. That is a change to a
# persisted trace shape (historical traces stay unattributed), so it is its own
# PLAN, not a follow-up commit here. `benefit_rollup`'s three test-pinned
# constraints below still govern whatever is eventually built.
# --------------------------------------------------------------------------- #


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


async def verdict_reading_stats(session: AsyncSession) -> list[VerdictReadingStat]:
    """Band-verdict distribution + per-verdict reading stats (O(verdicts) rows) — AC-10 B1.

    Reads the judged entities out of ``artifact->'output_set'``, where an evaluate
    step writes ``{**entity, "verdict": ...}`` — so the verdict and the reading that
    produced it ride the same object and need no join. The reading is extracted with
    the same never-raise numeric guard the ฿ figure uses (S2): a ``measured_value``
    that is absent or non-numeric casts to NULL, is ignored by ``avg``/``max``, and
    is surfaced as ``readings_missing`` rather than raising or silently vanishing.
    """
    entity = _jsonb_array(StepResult.artifact[_OUTPUT_SET])
    verdict = entity.c.value["verdict"].astext
    reading_text = entity.c.value["measured_value"].astext
    reading = sa.cast(
        sa.case((reading_text.op("~")(_NUMERIC_TEXT), reading_text), else_=None),
        sa.Numeric,
    )
    stmt = (
        sa.select(
            verdict.label("verdict"),
            sa.func.count(),
            sa.func.count(reading),
            sa.func.coalesce(sa.func.avg(reading), 0),
            sa.func.coalesce(sa.func.max(reading), 0),
        )
        .select_from(StepResult)
        .join(entity, sa.true())
        .group_by(verdict)
        .order_by(verdict)  # a verdict label, never a wall clock (AC-3)
    )
    rows = (await session.execute(stmt)).all()
    return [
        VerdictReadingStat(
            verdict=label,
            entity_count=entities,
            reading_count=valued,
            readings_missing=entities - valued,
            avg_reading=Decimal(avg),
            max_reading=Decimal(maximum),
        )
        for label, entities, valued, avg, maximum in rows
    ]


async def gate_tier_outcomes(session: AsyncSession) -> list[GateTierOutcome]:
    """Approval outcome + gate dwell grouped by resolved DoA tier (O(tiers x 2) rows) — AC-10 B2.

    The tier comes from the step audit's ``governed_decision`` **array** — the shape
    ``_record_governed_decision`` persists — filtered to ``control_ref.kind ==
    'doa_tier'`` so SoD ties in the same array do not leak into the tier grouping.

    The outcome is an ``EXISTS`` over the trace lateral, not a join to it, for the
    reason ``gate_counts`` documents: a joined lateral yields one row per trace entry
    and would multiply the gate row, inflating ``gate_count`` and skewing the dwell
    average — silently, since the inflated figure still looks plausible. It tests for
    ``action_rejected`` specifically because the ``gate_principal_recorded`` tie is
    written whether the human approved OR rejected, so presence of a principal cannot
    discriminate the two.

    Dwell is the gate step's own ``duration_ms`` — a SAME-ROW datum. S4 permits no
    cross-row wall-clock arithmetic, so this is the only gate-dwell measure available
    until the monotonic-``sequence``-column PLAN lands.
    """
    decision = _jsonb_array(StepResult.audit[_GOVERNED_DECISION])
    tier = decision.c.value["control_ref"]["id"].astext
    elem = _trace_elements()
    rejected = (
        sa.select(sa.literal(1))
        .select_from(elem)
        .where(elem.c.value["kind"].astext == _ACTION_REJECTED)
        .correlate(StepResult)
        .exists()
    )
    outcome = sa.case((rejected, sa.literal("rejected")), else_=sa.literal("approved"))
    stmt = (
        sa.select(
            tier.label("doa_tier"),
            outcome.label("outcome"),
            sa.func.count(),
            sa.func.coalesce(sa.func.avg(StepResult.duration_ms), 0),
            sa.func.coalesce(sa.func.max(StepResult.duration_ms), 0),
        )
        .select_from(StepResult)
        .join(decision, sa.true())
        .where(StepResult.status == StepResultStatus.RESOLVED.value)
        .where(decision.c.value["control_ref"]["kind"].astext == _DOA_TIER)
        .group_by(tier, outcome)
        .order_by(tier, outcome)  # control-id + outcome labels, never a wall clock (AC-3)
    )
    rows = (await session.execute(stmt)).all()
    return [
        GateTierOutcome(
            doa_tier=doa_tier,
            outcome=str(result),
            gate_count=gate_count,
            avg_duration_ms=float(avg),
            max_duration_ms=int(maximum),
        )
        for doa_tier, result, gate_count, avg, maximum in rows
    ]


async def refusal_counts_by_procedure(session: AsyncSession) -> list[RefusalProcedureCount]:
    """Read-refusal counts grouped by kind x ``procedure_id`` (O(kinds x procedures)) — AC-10 B3.

    The procedure dimension is what makes this a refusal-MINING input rather than a
    total: "which procedure keeps hitting the allowlist" is the improvable question,
    and ``refusal_counts`` (kind only) cannot express it.
    """
    elem = _trace_elements()
    refusal_kind = elem.c.value["refusal_kind"].astext
    stmt = (
        sa.select(
            refusal_kind.label("refusal_kind"),
            PipelineRun.procedure_id,
            sa.func.count(),
        )
        .select_from(StepResult)
        .join(PipelineRun, PipelineRun.run_id == StepResult.run_id)
        .join(elem, sa.true())
        .where(StepResult.reasoning_trace.isnot(None))
        .where(elem.c.value["kind"].astext == _READ_REFUSED)
        .group_by(refusal_kind, PipelineRun.procedure_id)
        .order_by(refusal_kind, PipelineRun.procedure_id)  # labels, never a wall clock (AC-3)
    )
    rows = (await session.execute(stmt)).all()
    return [
        RefusalProcedureCount(refusal_kind=kind, procedure_id=procedure_id, count=count)
        for kind, procedure_id, count in rows
    ]


async def trigger_outcome_counts(session: AsyncSession) -> list[TriggerOutcomeCount]:
    """Run counts grouped by procedure x trigger x status (O(the triple)) — AC-10 B4.

    The trigger is ``trigger_context->>'trigger'``, the key both shipped stampers
    write (``scheduler._trigger_context`` and the event bridge), carrying the
    ``Trigger`` enum vocabulary. A run stamped without the key groups under NULL
    rather than being dropped — the frequency of un-stamped runs is itself a fact
    a procedure-generation input should not hide.
    """
    trigger = PipelineRun.trigger_context["trigger"].astext
    stmt = (
        sa.select(
            PipelineRun.procedure_id,
            trigger.label("trigger"),
            PipelineRun.status,
            sa.func.count(),
        )
        .group_by(PipelineRun.procedure_id, trigger, PipelineRun.status)
        .order_by(PipelineRun.procedure_id, trigger, PipelineRun.status)  # labels only (AC-3)
    )
    rows = (await session.execute(stmt)).all()
    return [
        TriggerOutcomeCount(
            procedure_id=procedure_id,
            trigger=trigger_value,
            status=status,
            run_count=run_count,
        )
        for procedure_id, trigger_value, status, run_count in rows
    ]
