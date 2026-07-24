"""A1 — NL query over the RUN corpus (PLAN-0088 Step 5).

Run records are not ontology objects, so this does **not** widen the ontology
corpus (S5). Instead a static, code-owned **run-corpus descriptor** declares one
pseudo-object-type, ``pipeline_run``, in the same ``ObjectTypeMeta`` shape
``nl_query``'s validator already checks against — and the validator itself is
**reused, not reimplemented**. That is what makes S5's "all three
provable-grounding properties are preserved *by construction*" literally true
rather than a claim two copies of a validator would slowly falsify.

Layering (S1, held statically by AC-11): this module owns **no SQL**, opens no
session, and imports no ``sqlalchemy`` symbol. It reaches data only through
``services.db.run_analytics`` — exactly as ``nl_query`` reaches data only
through the ``DataAdapter``.

That last rule is why the session parameter is annotated ``Any`` rather than
``AsyncSession``: the AC-11 guard walks this module's AST and fails on **any**
``sqlalchemy`` import, including one guarded by ``TYPE_CHECKING``. The session is
opaque here by design — it is accepted and handed straight to the substrate,
never used, so the engine side genuinely cannot reach the database itself.

**The v1 property set is the trimmed one (SD-9 ruled (a2), 2026-07-24).**
``agent_id`` and ``trigger`` were ELIMINATED: no primitive reads them and the
AC-2 corpus factory seeds both constant, so neither is measurable by this PLAN's
own exact-value standard. Each returns as one grouped-count primitive plus a
descriptor row when a real question appears.

**``operation='list'`` is excluded** under LOCKED SD-8 (a): the substrate ships
aggregate primitives only, so there is no listing shape to serve. The rejection
is a validation error, which means it flows back through the same
validate-and-retry loop as any other correctable mistake rather than surfacing
as a crash.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.db import run_analytics
from services.engine.nl_query import (
    AggregateResult,
    QueryFilter,
    StructuredQuery,
    _validate_query,
)
from services.engine.ontology_meta import ObjectTypeMeta, PropertyMeta
from services.engine.procedures.runs import PipelineRunStatus

RUN_CORPUS_TYPE = "pipeline_run"

#: Properties that identify a *bucket* rather than a measure. Filters are served
#: by picking rows out of an O(groups) rollup in Python — never by pushing a
#: caller-supplied WHERE into SQL, which no substrate primitive accepts anyway.
DIMENSIONS = ("procedure_id", "status", "started_week")

#: Numeric properties an aggregate operation may target.
MEASURES = ("duration_ms_total", "net_benefit_thb")


def run_corpus_meta() -> dict[str, ObjectTypeMeta]:
    """The run-corpus type index, in the shape ``_validate_query`` expects.

    Static and code-owned: run records have no authored ontology YAML, and
    inventing one would put operational telemetry into the customer's semantic
    layer, which S5 explicitly refuses.
    """
    return {
        RUN_CORPUS_TYPE: ObjectTypeMeta(
            name=RUN_CORPUS_TYPE,
            primary_key="run_id",
            title_key="run_id",
            description="One governed procedure run recorded by the engine.",
            properties=[
                PropertyMeta(name="procedure_id", type="string"),
                PropertyMeta(
                    name="status",
                    type="enum",
                    enum=[s.value for s in PipelineRunStatus],
                ),
                PropertyMeta(name="started_week", type="string"),
                PropertyMeta(name="duration_ms_total", type="int"),
                PropertyMeta(name="net_benefit_thb", type="float"),
            ],
        )
    }


@dataclass(frozen=True)
class RunQueryResult:
    """A deterministically-computed answer over the run corpus.

    ``count`` is set for a count operation; ``aggregate`` for max/min/avg/sum.
    ``matched`` is the number of runs behind the figure — 0 means the honest
    no-matching-records path, never a fabricated zero-valued answer.
    """

    matched: int = 0
    count: int | None = None
    aggregate: AggregateResult | None = None


def validate_run_query(query: StructuredQuery) -> list[str]:
    """Semantic validation, reusing ``nl_query``'s own checker plus two run-corpus rules.

    Reuse is the point: a second copy of the property/aggregate checks would
    drift from the original, and AC-8's parity claim would quietly stop being
    true. The two additional rules are the ones only this corpus has.
    """
    errors = _validate_query(query, run_corpus_meta())
    if errors:
        return errors
    if query.operation == "list":
        errors.append(
            "operation 'list' is not available over the run corpus; the run substrate "
            "exposes aggregate primitives only. Use 'count' or an aggregate "
            "(max/min/avg/sum) over duration_ms_total or net_benefit_thb."
        )
    for index, flt in enumerate(query.filters):
        if flt.op != "eq":
            errors.append(
                f"filters[{index}].op '{flt.op}' is not supported over the run corpus; "
                "only 'eq' is, because filters are served by selecting from a "
                "pre-aggregated rollup rather than by a pushed-down comparison."
            )
        if flt.property in MEASURES:
            errors.append(
                f"filters[{index}].property '{flt.property}' is a measure, not a "
                f"dimension; filter on one of: {', '.join(DIMENSIONS)}."
            )
    return errors


def _wanted(filters: list[QueryFilter], prop: str) -> str | None:
    """The requested value for a dimension, or None when unfiltered."""
    for flt in filters:
        if flt.property == prop:
            return flt.value
    return None


def _keep(filters: list[QueryFilter], procedure_id: str, status: str) -> bool:
    """Whether a (procedure, status) rollup row satisfies the query's filters."""
    want_proc = _wanted(filters, "procedure_id")
    want_status = _wanted(filters, "status")
    if want_proc is not None and want_proc != procedure_id:
        return False
    return not (want_status is not None and want_status != status)


async def _count(session: Any, query: StructuredQuery) -> RunQueryResult:
    """Count runs, optionally grouped by the ISO-week bucket."""
    if query.group_by == "started_week" or _wanted(query.filters, "started_week") is not None:
        weeks = await run_analytics.week_rollup(session)
        wanted = _wanted(query.filters, "started_week")
        week_rows = [w for w in weeks if wanted is None or w.period == wanted]
        week_total = sum(w.run_count for w in week_rows)
        return RunQueryResult(matched=week_total, count=week_total)
    status_rows = [
        r
        for r in await run_analytics.run_status_rollup(session)
        if _keep(query.filters, r.procedure_id, r.status)
    ]
    total = sum(r.run_count for r in status_rows)
    return RunQueryResult(matched=total, count=total)


async def _aggregate_duration(session: Any, query: StructuredQuery) -> RunQueryResult:
    """max/min/avg/sum over PER-RUN duration totals, from the grouped substrate rows.

    ``sum`` and ``max`` recombine exactly from group aggregates; ``avg`` is
    recovered as a run-count-weighted mean, which equals the mean over runs.
    ``min`` is NOT recoverable — the substrate publishes no per-group minimum —
    and saying so is better than returning the smallest *group average* dressed
    up as the smallest run.
    """
    rows = [
        r
        for r in await run_analytics.run_duration_totals(session)
        if _keep(query.filters, r.procedure_id, r.status)
    ]
    matched = sum(r.run_count for r in rows)
    if not matched:
        return RunQueryResult(matched=0)
    op = query.operation
    value: float | None
    if op == "max":
        value = float(max(r.max_total_ms for r in rows))
    elif op == "avg":
        value = sum(r.avg_total_ms * r.run_count for r in rows) / matched
    elif op == "sum":
        value = sum(r.avg_total_ms * r.run_count for r in rows)
    else:  # min
        value = None
    return RunQueryResult(
        matched=matched,
        aggregate=AggregateResult(operation=op, property="duration_ms_total", value=value),
    )


async def _aggregate_benefit(session: Any, query: StructuredQuery) -> RunQueryResult:
    """sum/avg/max over the ฿ facet, folded from the per-currency benefit buckets.

    **Per-currency only (S7).** A bucket whose currency is not THB is excluded
    rather than converted or silently added: the substrate never produces a
    cross-currency figure and neither may this compiler.
    """
    buckets = [
        b
        for b in await run_analytics.benefit_rollup(session)
        if b.currency in (None, "THB") and _wanted(query.filters, "status") is None
    ]
    want_proc = _wanted(query.filters, "procedure_id")
    if want_proc is not None:
        buckets = [b for b in buckets if b.procedure_id == want_proc]
    matched = sum(b.run_count for b in buckets)
    if not matched:
        return RunQueryResult(matched=0)
    op = query.operation
    value: float | None
    if op == "sum":
        value = float(sum(b.net_benefit_thb_sum for b in buckets))
    elif op == "avg":
        value = float(sum(b.net_benefit_thb_sum for b in buckets)) / matched
    elif op == "max":
        value = float(max(b.net_benefit_thb_sum for b in buckets))
    else:  # min
        value = None
    return RunQueryResult(
        matched=matched,
        aggregate=AggregateResult(operation=op, property="net_benefit_thb", value=value),
    )


async def execute_run_query(session: Any, query: StructuredQuery) -> RunQueryResult:
    """Compile a VALIDATED query to substrate calls and run it. Deterministic, LLM-free.

    No LLM is reachable from here — that is the property AC-8 (ii) pins by
    monkeypatching the chat client to raise and asserting this path still
    answers. The caller owns the session (S1), and every figure comes from
    ``run_analytics``; this module computes only the Python-side fold across
    already-aggregated groups.
    """
    if query.operation == "count":
        return await _count(session, query)
    if query.aggregate_property == "net_benefit_thb":
        return await _aggregate_benefit(session, query)
    return await _aggregate_duration(session, query)
