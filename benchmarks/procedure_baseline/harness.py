"""Per-item evaluation flow + run summary (PLAN-0019 B-β; SD-B1).

The harness threads one scenario through the design's two-stage grading and
aggregates a run. Pure control logic + an injected :class:`ChatClient` (the
``generate_judgment`` seam), so the whole flow is exercised offline with a mock
client; only the live RUN binds a real ``gpt-oss:20b`` (``run_benchmark.py``).

Per item:

1. deterministic :func:`grader.classify_disposition` -> the ~100% sanity verdict;
2. if the item is a **breach**, run the live ``generate_judgment`` two-call path
   and grade the :class:`LlmJudgment` proposal (the β headline + α probe);
3. if the item is a **watch**, run the SAME ``generate_judgment`` path and grade
   it on the **watch-tier lane** (PLAN-0022 Phase 3, M-1 — escalation
   correctness: proposed handler ∈ {canonical, acceptable}; unscored
   distribution under M-2=b while no watch ground truth is authored). Its
   per-judgment latency lands in its OWN recorder (M-4) — the SD-2 ≤ 30 s p95
   bar stays breach-scoped;
4. **ok** items stay the deterministic false-positive guard (no LLM call).

The watch lane never contaminates β (``graded``/``proposal_correct`` stay the
breach-only headline) or α. A scenario is fed to the model as a plain event
mapping (the DB/orchestrator are bypassed to isolate the LLM variable).
"""

from __future__ import annotations

import asyncio
import math
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from benchmarks.procedure_baseline.grader import (
    GradeResult,
    HandlerTier,
    classify_disposition,
    declares_handler_tiers,
    grade_proposal,
    grade_watch_proposal,
)
from benchmarks.procedure_baseline.schema import BenchmarkItem, Disposition, Scenario
from services.engine.llm.client import CallMetrics, ChatResult, OllamaError
from services.engine.llm.structured import (
    ChatClient,
    LlmJudgment,
    ReasoningMode,
    StructuredOutputError,
    generate_judgment,
)


def scenario_to_event(scenario: Scenario, reading_parameter: str | None = None) -> dict[str, Any]:
    """Project a :class:`Scenario` into the event mapping ``generate_judgment``
    consumes — the entity + reading + threshold context, plus any extra
    ``context`` fields verbatim.

    ``reading_parameter`` (the dataset's domain parameter, e.g. ``dissolved_oxygen``)
    is injected as a ``parameter`` field so the model knows WHAT is being measured —
    faithful to a real ontology-projected event (B-β calibration). Omitted when
    ``None`` (keeps the event minimal for callers that don't supply it).
    """
    event: dict[str, Any] = {
        "event_id": scenario.event_id,
        "event_type": "reading",
        "object_type": scenario.entity_type,
        "primary_key": scenario.primary_key,
        "measured_value": scenario.measured_value,
        "unit": scenario.unit,
        "threshold": scenario.threshold,
        "direction": scenario.direction,
    }
    if reading_parameter is not None:
        event["parameter"] = reading_parameter
    if scenario.distractors:
        # PR2 multi-entity hardening: sibling readings the model must NOT name as
        # affected (they sit on the safe side of the threshold). Injected as event
        # context so they reach the model inside the untrusted block.
        event["other_readings"] = [
            {"primary_key": sibling.primary_key, "measured_value": sibling.measured_value}
            for sibling in scenario.distractors
        ]
    event.update(scenario.context)
    return event


@dataclass(frozen=True)
class ItemResult:
    """The graded outcome of one item.

    ``disposition_correct`` is the deterministic sanity result (all items);
    ``proposal_correct`` is the **β headline** LLM grade (breach items only —
    ``None`` for the non-breach false-positive guard); ``probe_correct`` is the **α
    handler-selection probe** (``None`` when not graded or the item declares no
    probe field) and ``probe_tier`` its three-way classification (canonical /
    acceptable / forbidden-or-other — PLAN-0022 Step 1; ``None`` exactly when
    ``probe_correct`` is). ``error`` is set when the judgment path raised (a failed
    proposal = incorrect; the probe is ``None`` since no judgment exists to score).
    The ``watch_*`` fields are the PLAN-0022 Phase-3 **watch-tier lane** (M-1),
    populated only for watch items: ``watch_graded`` marks that the LLM judgment
    ran; ``watch_handler`` is the model's proposed handler (the M-2=b
    distribution evidence); ``watch_tier`` / ``watch_pass`` are the scored
    classification — ``None`` when the item declares no handler tiers (unscored
    calibration) or the judgment errored. They never feed ``proposal_correct``
    (β) or ``probe_correct`` (α) — lane isolation.

    ``judgment`` is the raw :class:`LlmJudgment` the proposal was graded against
    (``None`` for the ok guard or an errored call), carried so a run can
    persist it (``--dump-json``) for offline VERIFY — confirming a score is a real
    model verdict, not a grader artifact.
    """

    item_id: str
    vertical: str
    disposition_expected: Disposition
    disposition_actual: Disposition
    disposition_correct: bool
    graded: bool
    proposal_correct: bool | None
    grade: GradeResult | None
    error: str | None = None
    probe_correct: bool | None = None
    probe_tier: HandlerTier | None = None
    judgment: LlmJudgment | None = None
    watch_graded: bool = False
    watch_pass: bool | None = None
    watch_tier: HandlerTier | None = None
    watch_handler: str | None = None
    #: Wall-clock of THIS item's full judgment exchange, in seconds — ``None`` for
    #: an ok-guard item that ran no LLM call. The aggregate recorders answer "what
    #: is the p95"; only a per-item number answers "WHICH task was slow", which is
    #: what a per-judgment deadline breach has to be able to name.
    judgment_latency_s: float | None = None
    #: The call-1 reasoning output (``draft``) and the model's own thinking trace.
    #: ``None`` when no call 1 ran (``reasoning_mode="skip"``, the ok guard) or the
    #: exchange errored before producing one. Carried because a claim about what
    #: the reasoning pass DID is otherwise reconstructed from the call-2 rationale,
    #: which is a downstream echo of the draft rather than the draft — the product
    #: path already persists both (``services/engine/llm/trace.py``).
    draft: str | None = None
    thinking: str | None = None
    #: Per-call generation accounting for this item's exchange (PLAN — session
    #: 262). Empty for an ok-guard item that ran no LLM call, and for a deadline
    #: breach: the cut discards the in-flight call, so there is no envelope to
    #: account. Non-empty on the FAILURE path too — an exhausted retry budget is
    #: the shape a starved reasoning pass produces, and those attempts are the
    #: ones worth reading.
    calls: tuple[CallMetrics, ...] = ()


@dataclass(frozen=True)
class JudgmentRun:
    """One item's LLM exchange, as returned by :func:`_run_judgment`.

    Exactly one of ``judgment`` / ``error`` is ``None``. A record rather than a
    tuple because ``draft`` and ``thinking`` joined it: three call sites unpack
    this, and two same-typed optional strings sitting next to each other are two
    positions to swap silently.
    """

    judgment: LlmJudgment | None
    error: str | None
    latency_s: float
    draft: str | None = None
    thinking: str | None = None
    calls: tuple[CallMetrics, ...] = ()


class ReasoningModeInexpressibleError(RuntimeError):
    """The configured ``reasoning_mode`` is not expressible for the model under test.

    Raised — never caught into a per-item ``error`` string — because the failure
    is a property of the RUN's configuration, not of one item: every remaining
    item would be mislabelled the same way. Deliberately NOT a subclass of
    ``StructuredOutputError`` or ``OllamaError``, the two the per-item handler
    absorbs, so it propagates and stops the sweep.
    """


async def _run_judgment(
    item: BenchmarkItem,
    client: ChatClient,
    *,
    vertical: str,
    goal: str | None,
    reading_parameter: str | None,
    retry_budget: int,
    recorder: LatencyRecorder | None,
    reasoning_mode: ReasoningMode,
    deadline_s: float | None = None,
    include_handler_catalog: bool = False,
) -> JudgmentRun:
    """Run the live ``generate_judgment`` exchange for one item.

    Returns a :class:`JudgmentRun` — exactly one of ``judgment`` / ``error`` is
    ``None`` — rather than a positional tuple, because the reasoning ``draft``
    and ``thinking`` now ride back with it and three call sites unpack this.

    Both a :class:`StructuredOutputError` (the model never produced a valid
    judgment within the retry budget) and an ``OllamaError`` (a transport failure
    — e.g. a slow model exceeding the per-call timeout) are returned as the
    ``error`` string so a sweep over a slow/flaky model completes and reports
    rather than crashing mid-run (B-δ robustness). The per-judgment wall-clock —
    the full exchange (both Pattern-B calls + any retries), the end-to-end
    latency a human waits on — is recorded into ``recorder`` on BOTH the success
    and the error path (a failed judgment still cost wall-clock), and times only
    the LLM exchange, never the local grading. Shared by the breach (β) and
    watch (M-1) lanes; each passes its OWN recorder (M-4 lane separation).
    """
    event = scenario_to_event(item.scenario, reading_parameter)
    start = time.perf_counter()
    judgment: LlmJudgment | None = None
    error: str | None = None
    draft: str | None = None
    thinking: str | None = None
    calls: tuple[CallMetrics, ...] = ()
    try:
        if deadline_s is None:
            result = await generate_judgment(
                client,
                event,
                vertical,
                retry_budget=retry_budget,
                goal=goal,
                reasoning_mode=reasoning_mode,
                include_handler_catalog=include_handler_catalog,
            )
        else:
            # The deadline bounds the WHOLE exchange — both Pattern-B calls plus
            # every retry — because the thing a bar is set on is one task, not one
            # call. A per-call timeout cannot express "this judgment took too long":
            # three retries of a call that each finish just inside their own limit
            # produce a judgment far past any per-call number.
            async with asyncio.timeout(deadline_s):
                result = await generate_judgment(
                    client,
                    event,
                    vertical,
                    retry_budget=retry_budget,
                    goal=goal,
                    reasoning_mode=reasoning_mode,
                    include_handler_catalog=include_handler_catalog,
                )
        judgment = result.judgment
        # The call-1 reasoning output, carried back so a run can persist it. Without
        # it, any account of what the reasoning pass DID is reconstructed from the
        # call-2 rationale — a downstream echo, not the draft. Phase 1.6's causal
        # story was built that way and could not be checked.
        draft = result.draft
        thinking = result.thinking
        calls = result.calls
        # A `think_off` run that comes back WITH a reasoning trace did not run
        # with reasoning off — the model ignored the flag, and this cell's
        # numbers are a second sample of `full`, not a think-off measurement.
        # Phase 1.6 reported exactly that as a finding ("think_off is SLOWER"),
        # because nothing checked. Deliberately keyed on what the MODEL returned
        # rather than on a roster of model names: a roster is a list to keep
        # up to date, and the next un-listed model reintroduces the same silent
        # mislabelling. Raised, not recorded — a mislabelled cell is worse than
        # an absent one, and failing on item 1 beats ten mislabelled records.
        #
        # One direction only, and deliberately so: a returned trace PROVES the
        # flag was ignored. The converse does not hold — an absent trace is not
        # proof the reasoning pass was off (a model may reason inside `content`),
        # so this never certifies a think_off run as valid.
        if reasoning_mode == "think_off" and thinking:
            raise ReasoningModeInexpressibleError(
                # The mode is interpolated from the variable, not written as a
                # literal: a hardcoded name can drift from the mode actually in
                # force and report a mode that did not run. It also appears
                # exactly ONCE, so a claim about the message naming the mode has
                # a single site that can be probed — three literal copies made
                # that claim unwitnessable, since removing any one left the
                # other two satisfying it.
                f"item {item.id!r}: reasoning_mode={reasoning_mode!r} but the model "
                f"returned a {len(thinking)}-char reasoning trace, so it ignored "
                f"think=False. That mode is INEXPRESSIBLE for this model — its "
                f"results would duplicate 'full'. Use a model that honours the "
                f"flag, or drop that cell for this model and say why."
            )
    except TimeoutError:
        # Named distinctly so a breach is never read as a model failure: the run
        # was CUT, and what it would have produced is unknown.
        error = f"DEADLINE-BREACH: judgment exceeded {deadline_s:.0f}s"
    except (StructuredOutputError, OllamaError) as exc:
        error = str(exc)
        # StructuredOutputError carries the attempts it burned; OllamaError does
        # not, because the transport failed and there is no envelope to account.
        # `getattr` rather than an isinstance branch so a future third exception
        # type degrades to "no metrics" instead of an AttributeError mid-sweep —
        # the whole point of this record is to survive the runs that go wrong.
        calls = getattr(exc, "calls", ())
        # The draft too, and by the same `getattr` route. Without this the record
        # for a failed item says `draft: null` whether call 1 wrote nothing or
        # wrote 7,000 characters that call 2 then failed to structure — session
        # 261 could not tell those apart and concluded the wrong one.
        draft = getattr(exc, "draft", None)
        thinking = getattr(exc, "thinking", None)
    finally:
        # ``finally`` still runs before any return above, so a judgment that cost
        # wall-clock is recorded even when it produced nothing.
        elapsed = time.perf_counter() - start
        if recorder is not None:
            recorder.record(elapsed)
    return JudgmentRun(
        judgment=judgment,
        error=error,
        latency_s=elapsed,
        draft=draft,
        thinking=thinking,
        calls=calls,
    )


async def evaluate_item(
    item: BenchmarkItem,
    client: ChatClient,
    *,
    vertical: str,
    goal: str | None = None,
    reading_parameter: str | None = None,
    retry_budget: int = 3,
    judgment_recorder: LatencyRecorder | None = None,
    watch_judgment_recorder: LatencyRecorder | None = None,
    reasoning_mode: ReasoningMode = "full",
    judgment_deadline_s: float | None = None,
    include_handler_catalog: bool = False,
) -> ItemResult:
    """Evaluate one item: deterministic disposition, then grade the live LLM
    proposal on the lane the item's disposition selects — **breach** -> the β
    headline + α probe; **watch** -> the watch-tier lane (PLAN-0022 Phase 3,
    M-1); **ok** -> deterministic guard only, no LLM call.

    ``reading_parameter`` (the dataset's domain parameter) is injected into the
    event so the model knows the domain (B-β calibration).

    ``judgment_recorder`` (PLAN-0020 SD-2) records the **per-judgment** wall-clock
    for BREACH items only — the unit of the re-ratified **≤ 30 s p95
    per-judgment** acceptance bar, which stays breach-scoped (M-4).
    ``watch_judgment_recorder`` records watch items' judgment wall-clock as its
    OWN diagnostic (M-4) — never folded into the SD-2 bar. Both are distinct
    from the per-LLM-call timing the :class:`TimingChatClient` records (retained
    as a lever diagnostic).
    """
    actual = classify_disposition(item.scenario)
    disposition_correct = actual == item.expected.disposition

    if item.expected.disposition is Disposition.OK:
        # ok: the engine must NOT fire. Deterministic guard only; no LLM call —
        # and so no per-judgment latency to record.
        return ItemResult(
            item_id=item.id,
            vertical=vertical,
            disposition_expected=item.expected.disposition,
            disposition_actual=actual,
            disposition_correct=disposition_correct,
            graded=False,
            proposal_correct=None,
            grade=None,
        )

    if item.expected.disposition is Disposition.WATCH:
        # watch (PLAN-0022 Phase 3, M-1): the LLM judgment RUNS — the escalation
        # path's proposal — and is graded on the watch-tier lane, never β/α.
        # The deterministic disposition stays the routing truth (AC-3): this lane
        # grades WHAT the model proposed on an item the watch band routed, not
        # whether to route (M-3 — mis-routing is structurally impossible here).
        run = await _run_judgment(
            item,
            client,
            vertical=vertical,
            goal=goal,
            reading_parameter=reading_parameter,
            retry_budget=retry_budget,
            recorder=watch_judgment_recorder,
            reasoning_mode=reasoning_mode,
            deadline_s=judgment_deadline_s,
            include_handler_catalog=include_handler_catalog,
        )
        judgment, error, latency = run.judgment, run.error, run.latency_s
        if judgment is None:
            # A failed judgment is loud: scored items fail the lane; unscored
            # (M-2=b calibration) items carry the error with no pass/fail to pin.
            return ItemResult(
                item_id=item.id,
                vertical=vertical,
                disposition_expected=item.expected.disposition,
                disposition_actual=actual,
                disposition_correct=disposition_correct,
                graded=False,
                proposal_correct=None,
                grade=None,
                error=error,
                watch_graded=True,
                watch_pass=False if declares_handler_tiers(item.expected) else None,
                judgment_latency_s=latency,
                draft=run.draft,
                thinking=run.thinking,
                calls=run.calls,
            )
        watch = grade_watch_proposal(judgment, item.expected)
        return ItemResult(
            item_id=item.id,
            vertical=vertical,
            disposition_expected=item.expected.disposition,
            disposition_actual=actual,
            disposition_correct=disposition_correct,
            graded=False,
            proposal_correct=None,
            grade=None,
            judgment=judgment,
            watch_graded=True,
            watch_pass=watch.passed,
            watch_tier=watch.tier,
            watch_handler=watch.handler,
            judgment_latency_s=latency,
            draft=run.draft,
            thinking=run.thinking,
            calls=run.calls,
        )

    run = await _run_judgment(
        item,
        client,
        vertical=vertical,
        goal=goal,
        reading_parameter=reading_parameter,
        retry_budget=retry_budget,
        recorder=judgment_recorder,
        reasoning_mode=reasoning_mode,
        deadline_s=judgment_deadline_s,
        include_handler_catalog=include_handler_catalog,
    )
    judgment, error, latency = run.judgment, run.error, run.latency_s
    if judgment is None:
        # NOT a wrong answer — an ABSENT one. `proposal_correct=False` here made a
        # deadline cut arithmetically identical to a model that answered and got it
        # wrong, so latency leaked into the accuracy column: measured s260, the
        # cells with cuts were the slow model's, and only its. `None` keeps the item
        # attempted-but-unscored, which is what the watch lane beside this one has
        # always done, and what compare.py's own docstring already claims it
        # receives ("kept so they are never silently counted as failures").
        return ItemResult(
            item_id=item.id,
            vertical=vertical,
            disposition_expected=item.expected.disposition,
            disposition_actual=actual,
            disposition_correct=disposition_correct,
            graded=True,
            proposal_correct=None,
            grade=None,
            error=error,
            judgment_latency_s=latency,
            draft=run.draft,
            thinking=run.thinking,
            calls=run.calls,
        )

    grade = grade_proposal(judgment, item.expected)
    return ItemResult(
        item_id=item.id,
        vertical=vertical,
        disposition_expected=item.expected.disposition,
        disposition_actual=actual,
        disposition_correct=disposition_correct,
        graded=True,
        proposal_correct=grade.passed,
        grade=grade,
        probe_correct=grade.probe_passed,
        probe_tier=grade.handler_tier,
        judgment=judgment,
        judgment_latency_s=latency,
        draft=run.draft,
        thinking=run.thinking,
        calls=run.calls,
    )


@dataclass(frozen=True)
class Summary:
    """Aggregate over a run.

    Four independent metrics, never combined:

    * ``headline_accuracy`` (over graded breach items) — the SD-B1 ≥ 85% **β
      headline** (entity + action class);
    * ``probe_accuracy`` (over graded breach items that declare a handler probe) —
      the **α** reactive-path handler-selection signal, reported on its own lane
      (``None`` when no item declared a probe field). ``probe_tiers`` breaks the
      probed items down by their three-way classification (PLAN-0022 Step 1):
      counts keyed by :class:`HandlerTier` value, with ``forbidden`` split from
      ``other`` so a dangerous pick is named explicitly (SD-4=a reporting);
      pass = ``canonical`` + ``acceptable``;
    * the **watch-tier lane** (PLAN-0022 Phase 3, M-1 — escalation correctness):
      ``watch_graded`` watch items ran the LLM judgment; of those,
      ``watch_scored`` declare handler tiers and grade pass/fail
      (``watch_correct`` / ``watch_accuracy``; ``watch_tiers`` are their tier
      counts — errored items carry no tier). ``watch_accuracy`` is ``None``
      while nothing is scored — the M-2=b calibration state, where
      ``watch_handlers`` (suggested-handler counts over the successfully-judged
      watch items) is the reported evidence and ``watch_errors`` names the
      failed judgments. Never folded into β, α, or any bar (B-3/B-6);
    * ``deterministic_accuracy`` (over all items) — the separately-reported ~100%
      sanity number.
    """

    total: int
    graded: int
    #: Of the ``graded`` (attempted) breach items, how many produced a judgment to
    #: score, and how many did not. Reported as a PAIR with ``headline_accuracy``
    #: on purpose: accuracy-of-scored conditions on the items the model could
    #: finish, so it is only honest beside the count it excluded. The watch lane
    #: has always reported ``watch_errors`` this way; this is the breach lane
    #: catching up.
    headline_scored: int
    headline_errors: int
    headline_correct: int
    headline_accuracy: float | None
    probe_graded: int
    probe_correct: int
    probe_accuracy: float | None
    probe_tiers: dict[str, int]
    watch_graded: int
    watch_scored: int
    watch_correct: int
    watch_accuracy: float | None
    watch_tiers: dict[str, int]
    watch_handlers: dict[str, int]
    watch_errors: int
    deterministic_correct: int
    deterministic_accuracy: float
    by_disposition: dict[str, int]


def summarize(results: Sequence[ItemResult]) -> Summary:
    """Aggregate per-item results into the separately-reported metrics
    (β / α / watch lane / sanity)."""
    total = len(results)
    graded = [result for result in results if result.graded]
    # ATTEMPTED vs SCORED. An errored/cut judgment carries `proposal_correct=None`;
    # it was attempted but produced nothing to grade. Dividing by `len(graded)`
    # counted it as a wrong answer, which made the accuracy column a function of
    # how slow the model was — and in the s260 matrix every cut belonged to one
    # model, so the confound ran one way only.
    headline_basis = [result for result in graded if result.proposal_correct is not None]
    headline_errors = len(graded) - len(headline_basis)
    headline_correct = sum(1 for result in headline_basis if result.proposal_correct)
    probed = [result for result in graded if result.probe_correct is not None]
    probe_correct = sum(1 for result in probed if result.probe_correct)
    deterministic_correct = sum(1 for result in results if result.disposition_correct)

    by_disposition: dict[str, int] = {disposition.value: 0 for disposition in Disposition}
    for result in results:
        by_disposition[result.disposition_expected.value] += 1

    probe_tiers: dict[str, int] = {tier.value: 0 for tier in HandlerTier}
    for result in probed:
        if result.probe_tier is not None:
            probe_tiers[result.probe_tier.value] += 1

    watch_results = [result for result in results if result.watch_graded]
    watch_scored = [result for result in watch_results if result.watch_pass is not None]
    watch_correct = sum(1 for result in watch_scored if result.watch_pass)
    watch_tiers: dict[str, int] = {tier.value: 0 for tier in HandlerTier}
    for result in watch_scored:
        if result.watch_tier is not None:
            watch_tiers[result.watch_tier.value] += 1
    watch_handlers: dict[str, int] = {}
    for result in watch_results:
        if result.watch_handler is not None:
            watch_handlers[result.watch_handler] = watch_handlers.get(result.watch_handler, 0) + 1
    watch_errors = sum(1 for result in watch_results if result.error is not None)

    return Summary(
        total=total,
        graded=len(graded),
        headline_scored=len(headline_basis),
        headline_errors=headline_errors,
        headline_correct=headline_correct,
        headline_accuracy=(headline_correct / len(headline_basis)) if headline_basis else None,
        probe_graded=len(probed),
        probe_correct=probe_correct,
        probe_accuracy=(probe_correct / len(probed)) if probed else None,
        probe_tiers=probe_tiers,
        watch_graded=len(watch_results),
        watch_scored=len(watch_scored),
        watch_correct=watch_correct,
        watch_accuracy=(watch_correct / len(watch_scored)) if watch_scored else None,
        watch_tiers=watch_tiers,
        watch_handlers=watch_handlers,
        watch_errors=watch_errors,
        deterministic_correct=deterministic_correct,
        deterministic_accuracy=(deterministic_correct / total) if total else 0.0,
        by_disposition=by_disposition,
    )


# --- Latency (SD-B1 ≤ 8 s p95 per LLM call; B-δ) -----------------------------


@dataclass
class LatencyRecorder:
    """Accumulates per-LLM-call wall-clock durations (seconds) for one run."""

    durations: list[float] = field(default_factory=list)

    def record(self, seconds: float) -> None:
        self.durations.append(seconds)


class TimingChatClient:
    """A :class:`ChatClient` decorator that times each ``chat`` call into a
    :class:`LatencyRecorder` — the SD-B1 unit is **per LLM call** (a breach item =
    2 Pattern-B calls), so timing wraps the client, not the per-item flow. The
    duration is recorded even when the inner call raises (the call still cost time).
    """

    def __init__(self, inner: ChatClient, recorder: LatencyRecorder) -> None:
        self._inner = inner
        self._recorder = recorder

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        # Mirrors the ChatClient Protocol exactly, `str` included. A decorator
        # narrower than the thing it decorates stops satisfying the Protocol and
        # silently rejects a value the inner client accepts — which is what
        # happened when `think` was widened to `bool | str | None` and this
        # signature was not carried along.
        think: bool | str | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        start = time.perf_counter()
        try:
            return await self._inner.chat(
                messages, think=think, response_format=response_format, temperature=temperature
            )
        finally:
            self._recorder.record(time.perf_counter() - start)


def percentile(values: Sequence[float], pct: float) -> float:
    """The ``pct``-th percentile (0-100) by the nearest-rank method on sorted
    values. Empty input -> 0.0. Simple + defensible for a p95 latency bar."""
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(1, math.ceil(pct / 100.0 * len(ordered)))
    return ordered[rank - 1]


@dataclass(frozen=True)
class LatencySummary:
    """Per-LLM-call latency aggregate for one model's run (SD-B1 p95 ≤ threshold)."""

    calls: int
    mean_s: float
    p50_s: float
    p95_s: float
    max_s: float
    threshold_s: float
    within_threshold: bool


def summarize_latency(durations: Sequence[float], *, threshold_s: float = 8.0) -> LatencySummary:
    """Aggregate per-call durations into the SD-B1 latency report (p95 vs the bar)."""
    if not durations:
        return LatencySummary(0, 0.0, 0.0, 0.0, 0.0, threshold_s, True)
    p95 = percentile(durations, 95.0)
    return LatencySummary(
        calls=len(durations),
        mean_s=sum(durations) / len(durations),
        p50_s=percentile(durations, 50.0),
        p95_s=p95,
        max_s=max(durations),
        threshold_s=threshold_s,
        within_threshold=p95 <= threshold_s,
    )
