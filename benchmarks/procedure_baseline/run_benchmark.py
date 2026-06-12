"""Live runner for the procedure-baseline benchmark (PLAN-0019 B-β skeleton).

⚠️  MANUAL ONLY — hits the live ``gpt-oss:20b`` on MS-S1 and is **NOT collected
by CI** (``pytest`` ``testpaths = ["tests"]``). The benchmark RUN is a host-state
change: per the handoff, **ASK Cray before warming / running**. The grader /
loader / harness this drives are unit-tested offline under ``tests/benchmark/``
with a mock ``ChatClient``; this module only binds the real client.

Scope: it runs the SD-B1 graded unit A — deterministic disposition (~100%
sanity) + the headline LLM action-proposal grade on the breach subset — plus
the PLAN-0022 Phase-3 watch-tier lane (escalation correctness on the watch
subset; calibration-only distribution under M-2=b) — over the authored dataset
and prints the separately-reported metrics. The B-gamma comparison baselines
(raw text-to-SQL + RAG) and the B-delta per-model latency sweep are
deliberately TODO here; they land in their own steps.

Usage (after Cray go-ahead; warm first per the MS-S1 note)::

    uv run python -m benchmarks.procedure_baseline.run_benchmark --warm
    uv run python -m benchmarks.procedure_baseline.run_benchmark --model gpt-oss:20b --limit 5
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from benchmarks.procedure_baseline.harness import (
    ItemResult,
    LatencyRecorder,
    LatencySummary,
    Summary,
    TimingChatClient,
    evaluate_item,
    summarize,
    summarize_latency,
)
from benchmarks.procedure_baseline.loader import DATASET_DIR, load_all
from benchmarks.procedure_baseline.schema import Dataset
from services.api.config import settings
from services.engine.llm.client import OllamaClient
from services.engine.llm.structured import ReasoningMode
from services.engine.procedures.spec import Procedure, load_procedures
from verticals.aquaculture.handlers import register_aquaculture_handlers
from verticals.energy.handlers import register_energy_handlers
from verticals.supply_chain.handlers import register_supply_chain_handlers

_DEFAULT_MODEL = "gpt-oss:20b"  # ADR-001 pin
_DEFAULT_KEEP_ALIVE = "10m"


def _register_all_handlers() -> None:
    """Register the three example verticals' action handlers on the registry so
    ``suggested_handler`` enum-constraint + the semantic check resolve."""
    register_aquaculture_handlers()
    register_energy_handlers()
    register_supply_chain_handlers()


def _resolve_goal_and_model(dataset: Dataset) -> tuple[str | None, str]:
    """Resolve the procedure ``goal`` (A-8 directive) + the bound agent
    ``llm_model`` from the vertical's real ``procedures.yaml``."""
    spec = load_procedures(dataset.vertical)
    procedure: Procedure | None = next(
        (proc for proc in spec.procedures if proc.procedure_id == dataset.procedure), None
    )
    if procedure is None:
        raise SystemExit(
            f"dataset '{dataset.vertical}': procedure '{dataset.procedure}' not found in spec"
        )
    agent = next((a for a in spec.agents if a.agent_id == procedure.run_by), None)
    model = agent.llm_model if agent is not None else _DEFAULT_MODEL
    return (procedure.goal or None), model


async def run_dataset(
    dataset: Dataset,
    *,
    model_override: str | None,
    host: str,
    warm: bool,
    limit: int | None,
    recorder: LatencyRecorder,
    judgment_recorder: LatencyRecorder,
    watch_judgment_recorder: LatencyRecorder,
    reasoning_mode: ReasoningMode,
) -> list[ItemResult]:
    """Evaluate every item in one vertical's dataset against the live model.

    The client is wrapped in a :class:`TimingChatClient` so every LLM call's
    wall-clock duration lands in the shared ``recorder`` (B-δ per-call latency,
    retained as a lever diagnostic — since Phase 3 it covers breach AND watch
    calls). The full per-judgment exchange wall-clock lands in
    ``judgment_recorder`` for breach items — the unit of the re-ratified SD-2
    ≤ 30 s p95 per-judgment acceptance bar (PLAN-0020), which stays
    breach-scoped — and in ``watch_judgment_recorder`` for watch items (the
    M-4 own-lane diagnostic, no bar)."""
    goal, agent_model = _resolve_goal_and_model(dataset)
    model = model_override or agent_model
    base = OllamaClient(base_url=host, model=model, timeout=settings.llm_request_timeout_s)
    if warm:
        await base.warm(keep_alive=_DEFAULT_KEEP_ALIVE)
    client = TimingChatClient(base, recorder)
    items = dataset.items[:limit] if limit is not None else dataset.items
    results: list[ItemResult] = []
    for item in items:
        result = await evaluate_item(
            item,
            client,
            vertical=dataset.vertical,
            goal=goal,
            reading_parameter=dataset.reading_parameter,
            judgment_recorder=judgment_recorder,
            watch_judgment_recorder=watch_judgment_recorder,
            reasoning_mode=reasoning_mode,
        )
        results.append(result)
        _print_item(result)
    return results


def _print_item(result: ItemResult) -> None:
    sanity = "ok" if result.disposition_correct else "MISMATCH"
    if result.watch_graded:
        # Watch-tier lane (PLAN-0022 Phase 3, M-1): unscored = the M-2=b
        # calibration state (distribution evidence, no pass/fail to pin).
        if result.error is not None:
            lane = f"watch-lane ERROR ({result.error})"
        elif result.watch_pass is None:
            lane = f"watch-lane handler={result.watch_handler!r} (calibration: unscored)"
        else:
            verdict = "PASS" if result.watch_pass else "FAIL"
            tier = result.watch_tier.value if result.watch_tier is not None else "n/a"
            lane = f"watch-lane {verdict} ({result.watch_handler!r} -> {tier})"
        print(
            f"  {result.item_id:<16} {result.disposition_expected.value:<7} "
            f"sanity={sanity} {lane}"
        )
        return
    if not result.graded:
        print(f"  {result.item_id:<16} {result.disposition_expected.value:<7} sanity={sanity}")
        return
    headline = "PASS" if result.proposal_correct else "FAIL"
    suffix = f" ({result.error})" if result.error else ""
    print(
        f"  {result.item_id:<16} {result.disposition_expected.value:<7} "
        f"sanity={sanity} proposal={headline}{suffix}"
    )


def _print_summary(label: str, summary: Summary) -> None:
    headline = (
        f"{summary.headline_accuracy:.1%}" if summary.headline_accuracy is not None else "n/a"
    )
    probe = f"{summary.probe_accuracy:.1%}" if summary.probe_accuracy is not None else "n/a"
    tiers = summary.probe_tiers
    print(
        f"\n{label}: β headline {headline} "
        f"({summary.headline_correct}/{summary.graded} graded breach proposals) | "
        f"α handler-probe {probe} "
        f"({summary.probe_correct}/{summary.probe_graded} reactive-path handler picks: "
        f"canonical {tiers['canonical']} / acceptable {tiers['acceptable']} / "
        f"forbidden {tiers['forbidden']} + other {tiers['other']}) | "
        f"deterministic {summary.deterministic_accuracy:.1%} "
        f"({summary.deterministic_correct}/{summary.total} dispositions) | "
        f"by-disposition {summary.by_disposition}"
    )
    if summary.watch_graded:
        _print_watch_lane(label, summary)


def _print_watch_lane(label: str, summary: Summary) -> None:
    """The PLAN-0022 Phase-3 watch-tier lane (M-1), on its own line so it can
    never read as part of β/α. While no watch ground truth is authored (M-2=b
    calibration-first) the lane reports the suggested-handler DISTRIBUTION —
    counts only, no pass/fail, no bar."""
    errors = f", errors {summary.watch_errors}" if summary.watch_errors else ""
    if summary.watch_scored == 0:
        print(
            f"{label}: watch-lane CALIBRATION (M-2=b — no ground truth pinned): "
            f"{summary.watch_graded} judged{errors} | "
            f"handler distribution {summary.watch_handlers}"
        )
        return
    accuracy = f"{summary.watch_accuracy:.1%}" if summary.watch_accuracy is not None else "n/a"
    tiers = summary.watch_tiers
    print(
        f"{label}: watch-lane {accuracy} "
        f"({summary.watch_correct}/{summary.watch_scored} scored escalation proposals: "
        f"canonical {tiers['canonical']} / acceptable {tiers['acceptable']} / "
        f"forbidden {tiers['forbidden']} + other {tiers['other']}{errors}) | "
        f"handler distribution {summary.watch_handlers}"
    )


def _item_record(result: ItemResult) -> dict[str, Any]:
    """One JSONL record for ``--dump-json``: the item's verdicts, the per-field check
    breakdown (name / passed / detail / lane), and the raw model judgment — the
    evidence to VERIFY a score is a real model verdict, not a grader artifact (the
    session-46 ``44% -> 100%`` mis-calibration lesson). The ``detail`` strings already
    name the offenders (e.g. ``"decoy(s) named: [pond-A102]"``, ``"'inspect' in
    ['hold']"``); the raw ``judgment`` lets a reviewer read the actual title / rationale."""
    checks = (
        [
            {
                "name": check.name,
                "passed": check.passed,
                "detail": check.detail,
                "advisory": check.advisory,
                "probe": check.probe,
            }
            for check in result.grade.checks
        ]
        if result.grade is not None
        else None
    )
    return {
        "item_id": result.item_id,
        "vertical": result.vertical,
        "disposition_expected": result.disposition_expected.value,
        "graded": result.graded,
        "proposal_correct": result.proposal_correct,
        "probe_correct": result.probe_correct,
        "probe_tier": result.probe_tier.value if result.probe_tier is not None else None,
        "watch_graded": result.watch_graded,
        "watch_pass": result.watch_pass,
        "watch_tier": result.watch_tier.value if result.watch_tier is not None else None,
        "watch_handler": result.watch_handler,
        "error": result.error,
        "checks": checks,
        "judgment": result.judgment.model_dump() if result.judgment is not None else None,
    }


def _print_latency(model: str, latency: LatencySummary) -> None:
    """Per-LLM-call latency — now a lever DIAGNOSTIC (the SD-B1 8 s-per-call bar
    was superseded by the SD-2 per-judgment bar; this number still localises which
    call dominates)."""
    print(
        f"\nLATENCY [{model}] per LLM call (lever diagnostic): "
        f"n={latency.calls} mean={latency.mean_s:.2f}s p50={latency.p50_s:.2f}s "
        f"p95={latency.p95_s:.2f}s max={latency.max_s:.2f}s"
    )


def _print_judgment_latency(latency: LatencySummary) -> None:
    """Per-JUDGMENT latency — the re-ratified SD-2 acceptance bar (PLAN-0020): the
    end-to-end two-call exchange wall-clock a human waits on, p95 ≤ 30 s.
    Breach items only (the bar stays breach-scoped — M-4). Reports-not-gates: a
    p95 over the bar is a logged finding, never a build fail."""
    verdict = "PASS" if latency.within_threshold else "OVER"
    print(
        f"\nLATENCY per BREACH judgment (end-to-end exchange — SD-2 acceptance bar): "
        f"n={latency.calls} mean={latency.mean_s:.2f}s p50={latency.p50_s:.2f}s "
        f"p95={latency.p95_s:.2f}s max={latency.max_s:.2f}s | "
        f"SD-2 p95 <= {latency.threshold_s:.0f}s -> {verdict}"
    )


def _print_watch_judgment_latency(latency: LatencySummary) -> None:
    """Per-WATCH-judgment latency — the M-4 own-lane diagnostic (PLAN-0022
    Phase 3): recorded and reported separately; there is NO bar on it and it is
    never folded into the SD-2 breach-scoped p95 (no bar moves — B-3/B-6)."""
    print(
        f"\nLATENCY per WATCH judgment (M-4 diagnostic — own lane, no bar): "
        f"n={latency.calls} mean={latency.mean_s:.2f}s p50={latency.p50_s:.2f}s "
        f"p95={latency.p95_s:.2f}s max={latency.max_s:.2f}s"
    )


async def _main(args: argparse.Namespace) -> None:
    _register_all_handlers()
    datasets = load_all(args.dataset_dir)
    recorder = LatencyRecorder()
    judgment_recorder = LatencyRecorder()
    watch_judgment_recorder = LatencyRecorder()
    all_results: list[ItemResult] = []
    print(f"REASONING MODE (PLAN-0020 think-trim lever): {args.reasoning_mode}")
    for dataset in datasets:
        print(f"\n=== {dataset.vertical} ({dataset.procedure}) ===")
        results = await run_dataset(
            dataset,
            model_override=args.model,
            host=args.ollama_host,
            warm=args.warm,
            limit=args.limit,
            recorder=recorder,
            judgment_recorder=judgment_recorder,
            watch_judgment_recorder=watch_judgment_recorder,
            reasoning_mode=args.reasoning_mode,
        )
        all_results.extend(results)
        _print_summary(dataset.vertical, summarize(results))
    _print_summary("OVERALL", summarize(all_results))
    latency = summarize_latency(recorder.durations, threshold_s=args.latency_threshold)
    _print_latency(args.model or "per-agent", latency)
    judgment_latency = summarize_latency(
        judgment_recorder.durations, threshold_s=args.judgment_latency_threshold
    )
    _print_judgment_latency(judgment_latency)
    watch_judgment_latency = summarize_latency(watch_judgment_recorder.durations)
    _print_watch_judgment_latency(watch_judgment_latency)
    if args.dump_json is not None:
        lines = [json.dumps(_item_record(result)) for result in all_results]
        args.dump_json.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nDUMP: wrote {len(lines)} item records -> {args.dump_json}")
    print(
        "\nNOTE: β headline = LLM action-proposal correctness (affected entity + action "
        "class) on breach items; α handler-probe = reactive-path handler-selection "
        "(suggested_handler tiered canonical / acceptable / forbidden-or-other, "
        "PLAN-0022 Step 1; pass = canonical or acceptable — NOT a procedure-path "
        "decision, ADR-016 fixes that via step.handler); watch-lane = escalation "
        "correctness on watch items (PLAN-0022 Phase 3, M-1; calibration-only "
        "distribution until ground truth is pinned — M-2=b); deterministic "
        "disposition is a separate ~100% sanity number. The four are NOT folded "
        "together. Mis-routing columns (acted-on-watch / escalated-on-breach) are "
        "STRUCTURAL — the harness routes by the same classify_verdict on both sides "
        "(M-3), so the deterministic sanity lane covers them. Latency: per-BREACH-"
        "judgment p95 is the SD-2 acceptance bar (<= 30 s; breach-scoped — M-4); "
        "watch-judgment latency is its own diagnostic (no bar); per-call p95 is "
        "retained as a lever diagnostic. B-gamma (text-to-SQL + RAG baselines) is "
        "TODO."
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Procedure-baseline benchmark (live; manual).")
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--model", default=None, help="Override the per-agent llm_model (B-δ).")
    parser.add_argument("--ollama-host", default=settings.ollama_host, help="MS-S1 Ollama URL.")
    parser.add_argument("--warm", action="store_true", help="Warm the model first (MS-S1 note).")
    parser.add_argument("--limit", type=int, default=None, help="Cap items per vertical (smoke).")
    parser.add_argument(
        "--latency-threshold",
        type=float,
        default=8.0,
        help="Per-call p95 lever diagnostic (seconds; was the superseded SD-B1 bar).",
    )
    parser.add_argument(
        "--judgment-latency-threshold",
        type=float,
        default=30.0,
        help="SD-2 p95 per-judgment acceptance bar (seconds; PLAN-0020 re-ratified).",
    )
    parser.add_argument(
        "--reasoning-mode",
        choices=["full", "think_off", "skip"],
        default="full",
        help="PLAN-0020 think-trim lever (AC-1a): full (shipped) | think_off | skip.",
    )
    parser.add_argument(
        "--dump-json",
        type=Path,
        default=None,
        help="Write per-item JSONL (verdicts + check details + raw judgment) for offline VERIFY.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(_main(_parse_args()))
