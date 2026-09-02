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
from services.engine.llm.client import ChatResult, OllamaClient, OllamaError, call_metrics
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
    total_duration_ns: int | None = None
    eval_duration_ns: int | None = None

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
            "total_duration_ns": self.total_duration_ns,
            "eval_duration_ns": self.eval_duration_ns,
        }


class RecordingChatClient:
    """A pass-through ``ChatClient`` that records every attempt's raw content.

    It delegates to the real client and returns its result unchanged — observation
    is **transport-level**, so the seam under measurement stays the shipped one
    (``intake.py:39-50``). It adds no retry, no parsing and no repair: anything it
    caught, it re-raises.
    """

    def __init__(self, inner: ChatClient) -> None:
        self._inner = inner
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
        try:
            result = await self._inner.chat(
                messages,
                think=think,
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
                total_duration_ns=metrics.total_duration_ns,
                eval_duration_ns=metrics.eval_duration_ns,
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


async def _main(args: argparse.Namespace) -> None:
    gold = load_gold() if args.gold is None else load_gold(args.gold)
    inner = OllamaClient(base_url=args.ollama_host, model=args.model, timeout=args.timeout)
    client = RecordingChatClient(inner)
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
    return parser.parse_args()


if __name__ == "__main__":
    try:
        asyncio.run(_main(_parse_args()))
    except KeyboardInterrupt:  # pragma: no cover
        sys.exit(130)
