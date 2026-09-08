"""Intake-extraction benchmark runner — the shipped seam on a local model (PLAN-0118 AC-4).

⚠️  The CLI is **MANUAL ONLY**: it drives the live MS-S1 Ollama server, which is a
host-state change and needs its own typed CLAUDE.md §8 go at the time it is fired
(SD-4 ruled the run's *scope*; that is not the go to fire it). NOT collected by CI
(``pytest`` ``testpaths = ["tests"]``). Everything below the CLI is offline-testable
and is exercised by ``tests/benchmark/test_intake_extraction_scenario.py``.

What it does, per gold case: invoke the **shipped** ``extract_package``
(``services/engine/llm/intake.py:155``) — real prompt assembly, real retry loop, real
validation, real ``source`` stamping — capture the ``ExtractionResult`` **or** the typed
failure, score via the pure ``score_case``, and write a per-case artifact.

**Why the artifact carries the raw attempts.** Live runs are minimised (F3), so a
scoring dispute must be re-adjudicable *without* a re-run. The raw ``content`` of every
attempt is the only record of what the model actually emitted; the validated package has
already been through ``model_copy`` and cannot answer "did the model omit ``confidence``
or set it to 1.0?" — a question ``score_case`` reports as a diagnostic and which is
computable **only** from the raw attempt. That is what the recording client is for.

🔴 **The two failure kinds are DISTINCT and must stay so.** ``intake.py:166-169``
deliberately does not retry a transport error, so it propagates as ``OllamaError`` while
a schema failure exhausts the budget and raises ``IntakeExtractionError``. Cray's typed
SD-5 ruling scores them **differently** — validation exhaustion is ``wrong`` and stays in
the denominator (model capability); a transport error is ``unscored`` and leaves it (the
pipe's fault). Collapsing them is therefore a **correctness** bug, not a cosmetic one.

Usage (after the ms-s1-ollama skill's warm.sh, or with --warm)::

    uv run python -m benchmarks.intake_extraction.run_benchmark \\
        --model gpt-oss:20b --warm \\
        --artifact-dir .claude/benchmark-results/intake-<run>/
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from benchmarks.intake_extraction.harness import (
    AxisSummary,
    CaseFailure,
    ScoredCase,
    Tally,
    injection_cases,
    load_gold,
    score_case,
    score_injection_case,
    scored_cases,
    summarize,
    summarize_injection,
)
from services.engine.llm.client import (
    _WORKLOAD_NUM_PREDICT,
    ChatResult,
    OllamaClient,
    OllamaError,
    Workload,
    call_metrics,
)
from services.engine.llm.intake import (
    ChatClient,
    ExtractionResult,
    IntakeExtractionError,
    extract_package,
)


@dataclass(frozen=True)
class AttemptRecord:
    """One call through the seam, as it happened — raw, before any validation.

    ``content`` is the model's unparsed message body. ``error`` is set instead when
    the call itself raised (a transport failure), so an artifact distinguishes "the
    model emitted this and it was rejected" from "there was no answer at all".

    🔴 **The generation-accounting fields exist because the s273 live run could not
    explain its own headline result** (PLAN-0118 AC-6): **11 of 20 attempts returned
    an EMPTY body**, and the loop reported *"output was not valid JSON"* — which is
    what parsing ``""`` raises, so the message read as a JSON-quality problem when
    the body was simply blank. Nothing on disk could separate the two candidate
    causes: the model ran into the shared ``num_predict`` cap while reasoning
    (``gpt-oss:20b`` discards a boolean ``think`` and reasons anyway — measured s261),
    or it genuinely chose to emit nothing. ``ChatResult.raw`` carried the answer the
    whole time and this recorder dropped it.

    ``done_reason`` is the **truncation oracle** — ``"length"`` iff generation hit the
    cap, ``"stop"`` iff the model ended on its own — and ``eval_count`` is the tokens
    it actually generated, i.e. its DEMAND. Together with ``content_chars`` they
    discriminate: a large ``eval_count`` beside an empty body says the model generated
    plenty and none of it was content; a small one beside ``"stop"`` says it chose
    silence. ``thinking_chars`` says how much of that generation was reasoning.
    Durations stay in **nanoseconds exactly as Ollama reports them** (the
    ``CallMetrics`` discipline: the envelope is the measurement, and a converted
    number cannot be checked back against it) — ``total_duration_ns`` is the per-call
    latency AC-6 asks for.

    🔴 **``load_duration_ns``, ``prompt_eval_duration_ns`` and the raw ``thinking``
    string are what PLAN-0119 Step 2 adds, and they exist to make OQ-1 answerable.**
    The residual ``total_duration - eval_duration`` implied ~1,089-1,292 tokens on
    delivering calls — above the 1024 cap, which would mean the reasoning and content
    channels hold SEPARATE budgets — while Ollama's own splitter implies ONE shared
    budget. The reconstruction cannot settle it because that residual silently mixes
    three different things: a cold model load, prompt prefill, and grammar
    compilation. Recording load and prefill SEPARATELY is what turns the residual
    from one unattributable number into terms that can be subtracted. **Nothing may
    be built on the reconstruction until this measures it.**

    The two durations come off ``CallMetrics`` (``client.py:191-192``, computed there
    and dropped here until now). The raw ``thinking`` string does **not** — that
    record carries only ``thinking_chars``, an ``int``, and a character count cannot
    say whether the reasoning was cut mid-sentence. The string comes off
    ``ChatResult.thinking`` instead, which this recorder already holds. Two sources,
    not one; the distinction is recorded because PLAN-0119's first draft implied one
    and was corrected at s274.

    ``prompt_eval_duration_ns`` also earns its place on its own: with
    ``prompt_eval_count`` it yields a PREFILL RATE, and ``prefill`` is an unmeasured
    term in the budget rule ``cap / decode_rate + load + prefill < timeout`` that
    PLAN-0119 AC-4 makes checkable. Until it is measured, that rule is not evaluable.

    Every field is ``None``-tolerant by construction (``call_metrics`` degrades rather
    than raises on an envelope that omits a counter), and all of them are ``None`` on
    a transport failure, where there is no envelope at all.
    """

    index: int
    content: str | None
    model: str | None
    error: str | None = None
    done_reason: str | None = None
    eval_count: int | None = None
    prompt_eval_count: int | None = None
    thinking_chars: int | None = None
    #: The reasoning channel's RAW text, not just its length. A count says how much
    #: was reasoned; only the string says whether it ended mid-sentence — which is
    #: the observation that separates "clipped by the cap" from "reasoned briefly".
    thinking: str | None = None
    total_duration_ns: int | None = None
    eval_duration_ns: int | None = None
    #: Cold-load and prefill, split out of the residual so OQ-1 can be settled.
    load_duration_ns: int | None = None
    prompt_eval_duration_ns: int | None = None

    @property
    def truncated(self) -> bool:
        """True iff generation stopped on the cap rather than on the model.

        Keyed on the string the server returned, never on a comparison against the
        configured ``num_predict``: the configured value and the value the server
        applied can differ (an env override, a per-model default), so a derived
        answer could report a truncation that never happened — or miss one that did.
        """
        return self.done_reason == "length"

    def as_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "content": self.content,
            "model": self.model,
            "error": self.error,
            "done_reason": self.done_reason,
            "truncated": self.truncated,
            "eval_count": self.eval_count,
            "prompt_eval_count": self.prompt_eval_count,
            "content_chars": len(self.content) if self.content is not None else None,
            "thinking_chars": self.thinking_chars,
            "thinking": self.thinking,
            "total_duration_ns": self.total_duration_ns,
            "eval_duration_ns": self.eval_duration_ns,
            "load_duration_ns": self.load_duration_ns,
            "prompt_eval_duration_ns": self.prompt_eval_duration_ns,
        }


class RecordingChatClient:
    """A pass-through ``ChatClient`` that records every attempt's raw content.

    It delegates to the real client and returns its result unchanged — observation
    is **transport-level**, so the seam under measurement stays the shipped one
    (``intake.py:39-50``). It adds no retry, no parsing and no repair: anything it
    caught, it re-raises.
    """

    def __init__(self, inner: ChatClient, *, think_override: str | None = None) -> None:
        """``think_override`` is the ``--think`` arm's lever (PLAN-0119 Step 2).

        Intake's shipped call passes no ``think`` at all, so there is otherwise no way
        to ask the model for a different reasoning effort without editing the shipped
        prompt path — which would change the demand and confound every later arm.
        The override is applied ONLY where the caller passed nothing, so it can add a
        knob but can never silently overrule a call site that made its own choice.

        ``think=False`` is refused rather than supported. Per the CHECKPOINT-0 contract
        (ADR-001, ``client.py:16-18``) a caller must not pass ``think=False`` together
        with a ``response_format``, and intake's call always carries one — so the flag
        would construct exactly the combination the contract forbids. Ollama #18044 is
        the second reason: ``think: false`` disables the thinking PARSER, not the
        thinking generation, leaving ``eval_count`` unchanged. It is not a lever, and
        offering it would produce a measurement that looks like an intervention and
        is not one.
        """
        if think_override is not None and think_override.strip().lower() in {"false", "0", "no"}:
            raise ValueError(
                "think=False is not a lever: it disables the thinking PARSER, not the "
                "generation (Ollama #18044, eval_count unchanged), and pairing it with "
                "intake's response_format violates the CHECKPOINT-0 contract (ADR-001)"
            )
        self._inner = inner
        self._think_override = think_override
        self.attempts: list[AttemptRecord] = []

    def reset(self) -> None:
        """Drop the recorded attempts — called between cases by the runner."""
        self.attempts = []

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | str | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        index = len(self.attempts) + 1
        # Applied only where the call site passed nothing, so `--think` can ADD a knob
        # to intake's shipped no-think call but can never overrule an explicit choice.
        effective_think = think if think is not None else self._think_override
        try:
            result = await self._inner.chat(
                messages,
                think=effective_think,
                response_format=response_format,
                temperature=temperature,
            )
        except Exception as exc:
            detail = f"{type(exc).__name__}: {exc}"
            self.attempts.append(AttemptRecord(index=index, content=None, model=None, error=detail))
            raise
        # The generation accounting rides on the SAME result the seam already
        # returned — `call_metrics` only reads `ChatResult.raw`, so this stays a
        # transport-level observation and the measured seam is untouched. Role is
        # "structuring": the intake call carries a `response_format` (`intake.py:182`).
        metrics = call_metrics(result, role="structuring")
        self.attempts.append(
            AttemptRecord(
                index=index,
                content=result.content,
                model=result.model,
                done_reason=metrics.done_reason,
                eval_count=metrics.eval_count,
                prompt_eval_count=metrics.prompt_eval_count,
                thinking_chars=metrics.thinking_chars,
                # NOT from `metrics` — `CallMetrics` carries only `thinking_chars`,
                # an int. The raw string lives on the ChatResult this method already
                # holds. Two sources, deliberately (PLAN-0119 AC-2, clarified s274).
                thinking=result.thinking,
                total_duration_ns=metrics.total_duration_ns,
                eval_duration_ns=metrics.eval_duration_ns,
                load_duration_ns=metrics.load_duration_ns,
                prompt_eval_duration_ns=metrics.prompt_eval_duration_ns,
            )
        )
        return result


def confidence_was_omitted(attempts: list[AttemptRecord]) -> bool | None:
    """Did the model leave ``confidence`` out of the JSON it actually emitted?

    Computable ONLY from the raw attempt: ``IntakePackage.confidence`` carries
    ``default=1.0`` (``intake_assembler.py:183-184``), so by the time a package
    exists an omitting model is indistinguishable from a confident one. The
    omission RATE is a legitimate diagnostic; the value is not an accuracy axis
    (harness ``REFUSED_AXES``).

    Returns ``None`` when no attempt produced parseable JSON — absence of evidence,
    which must not be reported as evidence of omission.
    """
    for record in reversed(attempts):
        if record.content is None:
            continue
        try:
            parsed = json.loads(record.content)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return "confidence" not in parsed
    return None


@dataclass(frozen=True)
class CaseOutcome:
    """What one case produced: an extraction or a typed failure, plus its attempts."""

    case_id: str
    result: ExtractionResult | CaseFailure
    attempts: tuple[AttemptRecord, ...]
    confidence_omitted: bool | None

    @property
    def failed(self) -> bool:
        return isinstance(self.result, CaseFailure)


async def run_case(
    case: dict[str, Any], client: RecordingChatClient, *, retry_budget: int = 3
) -> CaseOutcome:
    """Drive one gold case through the shipped ``extract_package``.

    The two exception paths are kept apart deliberately — see the module docstring.
    ``IntakeExtractionError`` is caught first because both it and ``OllamaError``
    derive from ``RuntimeError``, so a single broad handler would silently merge the
    two SD-5 outcomes.
    """
    client.reset()
    result: ExtractionResult | CaseFailure
    try:
        result = await extract_package(client, str(case["description"]), retry_budget=retry_budget)
    except IntakeExtractionError as exc:
        result = CaseFailure(
            kind="validation_exhausted", detail=str(exc), attempts=len(client.attempts)
        )
    except OllamaError as exc:
        result = CaseFailure(
            kind="transport_error",
            detail=f"{type(exc).__name__}: {exc}",
            attempts=len(client.attempts),
        )
    attempts = tuple(client.attempts)
    return CaseOutcome(
        case_id=str(case["id"]),
        result=result,
        attempts=attempts,
        confidence_omitted=confidence_was_omitted(list(attempts)),
    )


def case_artifact(
    case: dict[str, Any],
    outcome: CaseOutcome,
    *,
    scored: ScoredCase | None = None,
    injection_verdict: bool | None = None,
) -> dict[str, Any]:
    """The per-case record written to disk, complete enough to re-adjudicate offline.

    Carries the description and the expectations alongside the raw attempts, so a
    dispute about a score can be settled from this file alone — no re-run, no §8 go.
    """
    record: dict[str, Any] = {
        "case_id": str(case["id"]),
        "domain": case.get("domain"),
        "description": case.get("description"),
        "expected": case.get("expected"),
        "attempts": [a.as_dict() for a in outcome.attempts],
        "attempt_count": len(outcome.attempts),
        "confidence_omitted": outcome.confidence_omitted,
    }
    if isinstance(outcome.result, CaseFailure):
        record["failure"] = {
            "kind": outcome.result.kind,
            "detail": outcome.result.detail,
            "attempts": outcome.result.attempts,
        }
        record["package"] = None
    else:
        record["failure"] = None
        record["package"] = outcome.result.package.model_dump(mode="json")
        record["model"] = outcome.result.model
    if scored is not None:
        record["axes"] = dict(scored.axes)
        record["band_detail"] = list(scored.band_detail)
    if "injected_field" in case:
        record["injection"] = {
            "injected_field": case["injected_field"],
            "injected_value": case["injected_value"],
            "counts_in_fraction": case.get("counts_in_fraction", True),
            "obeyed": injection_verdict,
        }
    return record


@dataclass
class BenchmarkRun:
    """Everything one pass over the gold set produced."""

    scored: list[ScoredCase] = field(default_factory=list)
    summaries: list[AxisSummary] = field(default_factory=list)
    injection: Tally | None = None
    injection_excluded: tuple[str, ...] = ()
    artifacts: list[dict[str, Any]] = field(default_factory=list)


async def run_benchmark(
    gold: dict[str, Any], client: RecordingChatClient, *, retry_budget: int = 3
) -> BenchmarkRun:
    """Run the whole gold set — scored band then injection band — and aggregate.

    Offline-identical to the live run: the only thing the CLI adds is which client
    is wrapped, so a canned transport here produces the same artifact shape and the
    same summary the live run will.
    """
    run = BenchmarkRun()
    for case in scored_cases(gold):
        outcome = await run_case(case, client, retry_budget=retry_budget)
        scored = score_case(case, outcome.result, confidence_omitted=outcome.confidence_omitted)
        run.scored.append(scored)
        run.artifacts.append(case_artifact(case, outcome, scored=scored))
    run.summaries = summarize(run.scored)

    inj_cases = injection_cases(gold)
    verdicts: dict[str, bool | None] = {}
    for case in inj_cases:
        outcome = await run_case(case, client, retry_budget=retry_budget)
        verdict = score_injection_case(case, outcome.result)
        verdicts[str(case["id"])] = verdict
        run.artifacts.append(case_artifact(case, outcome, injection_verdict=verdict))
    run.injection, run.injection_excluded = summarize_injection(inj_cases, verdicts)
    return run


def write_artifacts(run: BenchmarkRun, directory: Path) -> list[Path]:
    """Write one JSON file per case. Returns the paths, in the order written."""
    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for record in run.artifacts:
        path = directory / f"{record['case_id']}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(path)
    return written


def _print_run(run: BenchmarkRun) -> None:
    for summary in run.summaries:
        print(f"  {summary}")
    if run.injection is not None:
        excluded = ", ".join(run.injection_excluded) or "none"
        print(f"  obeyed_injection: {run.injection} (excluded from fraction: {excluded})")


#: The class this benchmark's calls belong to — intake extraction is S Structure
#: (PLAN-0119 §3, the row for ``intake.py:182``).
_BENCH_WORKLOAD: Workload = "S"


def _apply_num_predict(cap: int | None) -> int:
    """Point the chokepoint at ``cap`` for this process, and report what moved.

    ⚠️ **Corrected at Step 3 — the Step 2 version of this function is now WRONG, and
    the prediction in its docstring was wrong too.** It moved
    ``settings.llm_max_output_tokens``, which was what the chokepoint read at the time.
    Step 3's seam derives ``num_predict`` from the constructing client's workload class
    instead, so that setting is no longer consulted for chat: the flag would have kept
    printing a confident before/after while changing NOTHING on the wire. That is the
    inert-flag failure this module's own battery exists to catch, arriving by a
    different route — a seam moved underneath a caller that still looked correct.

    Step 2's docstring predicted this function would be DELETED when the seam landed,
    "in favour of declaring a ``Workload``". That was wrong on the facts: every class
    ships at the same 1024 in Step 3 (a pure refactor, deliberately), so declaring a
    class gives a run no way to ask for 4096. The live arms still need a per-run knob,
    so the function is REWIRED to the seam rather than removed — it now overrides the
    class's entry in the budget table the chokepoint actually reads.

    **What it still costs, stated rather than hidden.** This mutates a process-global
    table. It is contained because the benchmark is a standalone CLI that serves no
    requests, and it is not a pattern to copy into anything long-lived.

    Returns the cap actually in force, so the caller can record it beside the numbers
    it produces: a recorded duration is uninterpretable without the cap that bounded it.
    """
    before = _WORKLOAD_NUM_PREDICT[_BENCH_WORKLOAD]
    if cap is not None:
        _WORKLOAD_NUM_PREDICT[_BENCH_WORKLOAD] = cap
    after = _WORKLOAD_NUM_PREDICT[_BENCH_WORKLOAD]
    print(
        f"num_predict[{_BENCH_WORKLOAD}]: before={before} after={after} "
        f"(override={'none' if cap is None else cap})"
    )
    return after


async def _main(args: argparse.Namespace) -> None:
    gold = load_gold() if args.gold is None else load_gold(args.gold)
    applied_cap = _apply_num_predict(args.num_predict)
    inner = OllamaClient(
        # S Structure -- intake extraction (PLAN-0119 §3, row for intake.py:182).
        workload=_BENCH_WORKLOAD,
        base_url=args.ollama_host,
        model=args.model,
        timeout=args.timeout,
    )
    client = RecordingChatClient(inner, think_override=args.think)
    print(f"think: {args.think or 'not requested (intake ships no think)'}  cap={applied_cap}")
    n_scored = len(scored_cases(gold))
    n_inj = len(injection_cases(gold))
    print(f"intake-extraction benchmark: {n_scored} scored + {n_inj} injection cases")
    print(f"model={args.model} @ {args.ollama_host}\n")
    if args.warm:
        print("warming model ...")
        await inner.warm(keep_alive="15m")

    run = await run_benchmark(gold, client, retry_budget=args.retry_budget)
    _print_run(run)

    if args.artifact_dir is not None:
        written = write_artifacts(run, args.artifact_dir)
        print(f"\nARTIFACTS: wrote {len(written)} per-case records -> {args.artifact_dir}")

    print(
        "\nNOTE: raw fractions only — the gold set is deliberately small (SD-1). "
        "Accuracy is reported PER DIRECTION; a blended headline would hide a model "
        "that always answers one way. Validation exhaustion scores wrong and stays "
        "in the denominator; a transport error is unscored and leaves it (SD-5)."
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Intake-extraction benchmark (LIVE; manual; needs a typed §8 go)."
    )
    parser.add_argument("--gold", type=Path, default=None)
    parser.add_argument("--model", default="gpt-oss:20b", help="Ollama model tag.")
    parser.add_argument("--ollama-host", default="http://192.168.1.133:11434")
    parser.add_argument("--warm", action="store_true", help="Warm the model first.")
    parser.add_argument("--timeout", type=float, default=120.0, help="Per-call Ollama timeout (s).")
    parser.add_argument(
        "--retry-budget",
        type=int,
        default=3,
        help="Validation retries per case (intake default 3).",
    )
    parser.add_argument("--artifact-dir", type=Path, default=None)
    parser.add_argument(
        "--num-predict",
        type=int,
        default=None,
        help=(
            "Override the server-side generation cap for this run. Default: leave the "
            "workload class's own budget (1024) alone. See _apply_num_predict for why "
            "this overrides the seam's budget table rather than a setting."
        ),
    )
    parser.add_argument(
        "--think",
        default=None,
        help=(
            "Reasoning effort to request on intake's otherwise no-think call, e.g. "
            "'low'. `false` is REFUSED — it disables the thinking parser, not the "
            "generation (Ollama #18044), so it is not a lever."
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    try:
        asyncio.run(_main(_parse_args()))
    except KeyboardInterrupt:  # pragma: no cover
        sys.exit(130)
