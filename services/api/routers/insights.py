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

import logging
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
    RunQueryAnswer,
    RunQueryRequest,
    StatusTally,
    StepLatency,
)
from services.api.routers.query import arm_of
from services.db import run_analytics
from services.db.audit_log import verify_chain
from services.db.session import get_session
from services.engine import nl_query, run_query
from services.engine.llm import prompt_log
from services.engine.nl_query import StructuredQuery

logger = logging.getLogger(__name__)

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


async def translate_run_question(question: str) -> StructuredQuery:
    """Translate stage — PLUGGABLE (AC-9), wired to the local model (AC-9b).

    A module-level seam rather than an inline call, so CI can substitute a
    schema-shaped stub and exercise the whole pipeline offline. The live path
    below runs against **local MS-S1 only** — ``llm_backend='local'`` selects the
    Ollama client, and the ``'hosted'`` branch of the shared factory raises rather
    than reaching the remote API. That is not a preference: run records carry
    ``person_id`` (PII / PDPA), so run data never leaves the local network.

    Failure is a refusal, not a 500. Both ``QueryTranslationError`` (budget
    exhausted) and ``OllamaError`` (transport) subclass ``RuntimeError``, and the
    handler catches it to answer "I couldn't translate that" — so an unreachable
    MS-S1 degrades the endpoint honestly instead of breaking it.
    """
    client = nl_query._build_chat_client()
    return await run_query.translate_run_query(
        client, question, retry_budget=settings.llm_retry_budget
    )


async def phrase_run_answer(
    question: str, query: StructuredQuery, result: run_query.RunQueryResult
) -> nl_query.PhraseResult:
    """Phrase stage — PLUGGABLE (AC-9), and deliberately never reached on empty results.

    Degrades to the deterministic phrasing on any failure — including a backend
    that cannot be constructed at all — because a computed figure is still a
    grounded answer, and the alternative is a 500 on a question the engine has
    already answered correctly.

    This is the FIRST of the three degrade branches on this path (PLAN-0093 AC-8);
    the other two live in ``run_query.phrase_run_answer``. Each names the arm that
    authored the text and discloses when the LLM arm was attempted and did not.

    The model receives only the computed facts, never a run record.
    """
    try:
        client = nl_query._build_chat_client()
    except (NotImplementedError, ValueError) as exc:
        logger.warning(
            "run-corpus phrasing backend unavailable (%s); answering deterministically", exc
        )
        return nl_query.PhraseResult(
            text=run_query.fallback_run_answer(query, result),
            phrased_by=nl_query.PHRASED_BY_DETERMINISTIC,
            disclosure=f"phrasing backend unavailable: {exc}"[: nl_query.DISCLOSURE_CAP],
        )
    return await run_query.phrase_run_answer(client, question, query, result)


@router.post("/query", response_model=RunQueryAnswer)
async def run_corpus_query(
    payload: RunQueryRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RunQueryAnswer:
    """Answer a question about the governed runs, and log what was asked (D6).

    The answering itself is :func:`_answer_run_corpus_query`. The split exists so
    the prompt log has ONE chokepoint: that function has five return points —
    three of them honest refusals — and a log call per return is a log call one
    future early-return away from a silently unrecorded question.
    """
    answer = await _answer_run_corpus_query(payload, session)
    # PLAN-0100 Step 7. No-op unless PROMPT_LOG_ENABLED; never raises.
    prompt_log.record(
        route="/insights/query",
        vertical=settings.oct_vertical,
        text=payload.question,
        # Same correction as POST /query (PLAN-0100 Step 11, D-2): record the model
        # this path actually routes to, not `ollama_default_model`, which nothing
        # on the LLM path reads.
        model=settings.recommender_model,
        outcome="grounded" if answer.grounded else "ungrounded",
        arm=arm_of(answer.phrased_by),
    )
    return answer


async def _answer_run_corpus_query(
    payload: RunQueryRequest,
    session: AsyncSession,
) -> RunQueryAnswer:
    """Answer a plain-language question about the governed runs (A1).

    translate -> validate -> execute -> phrase, with translate and phrase
    pluggable. Only the middle two stages are deterministic, and they are the two
    that touch data: execution reads the substrate and nothing else, so a figure
    in the answer is always a figure the corpus produced.

    Three refusals are honest rather than helpful. A question that will not
    translate returns ungrounded with no query. A query the corpus cannot serve
    returns its validation errors in validate-and-retry form. A query matching
    nothing short-circuits to the no-records answer **without invoking the phrase
    stage at all** — there is nothing to phrase, and asking a model to describe an
    empty result is exactly how a fabricated figure gets in.
    """
    try:
        query = await translate_run_question(payload.question)
    except (NotImplementedError, RuntimeError):
        return RunQueryAnswer(
            question=payload.question,
            answer="I couldn't translate that into a query over the run records.",
            grounded=False,
            matched=0,
            # An honest refusal, deterministic BY DESIGN — the arm is named, and
            # nothing is disclosed because nothing degraded (PLAN-0093 AC-8).
            phrased_by=nl_query.PHRASED_BY_DETERMINISTIC,
        )

    errors = run_query.validate_run_query(query)
    if errors:
        return RunQueryAnswer(
            question=payload.question,
            answer="That question reaches for something the run records don't carry.",
            grounded=False,
            matched=0,
            structured_query=query.model_dump(mode="json"),
            validation_errors=errors,
            phrased_by=nl_query.PHRASED_BY_DETERMINISTIC,
        )

    result = await run_query.execute_run_query(session, query)
    if not result.matched:
        return RunQueryAnswer(
            question=payload.question,
            answer="No runs matched that question.",
            grounded=False,
            matched=0,
            structured_query=query.model_dump(mode="json"),
            phrased_by=nl_query.PHRASED_BY_DETERMINISTIC,
        )

    phrased = await phrase_run_answer(payload.question, query, result)
    return RunQueryAnswer(
        question=payload.question,
        answer=phrased.text,
        grounded=True,
        matched=result.matched,
        structured_query=query.model_dump(mode="json"),
        aggregate_value=result.aggregate.value if result.aggregate else None,
        # The only path here where the arm is not known statically.
        phrased_by=phrased.phrased_by,
        phrase_disclosure=phrased.disclosure,
    )
