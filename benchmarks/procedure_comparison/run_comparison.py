"""Live runner for the B-γ comparison (PLAN-0027 Step 4 — MANUAL, host-state).

⚠️  MANUAL ONLY — hits the live ``gpt-oss:20b`` on MS-S1; a host-state change
(**ASK Cray before warming / running** — CLAUDE.md §8). It is **NOT collected by
CI** (``pytest`` ``testpaths = ["tests"]``). The arms + harness this drives are
unit-tested offline under ``tests/benchmark/`` with a mock ``ChatClient``; this
module only binds the real client and warms.

Arm (a) is **NOT re-run** (D-2) — its energy breach numbers are reused from
``benchmarks/procedure_baseline/REPORT.md`` and joined into the output.

Usage (after Cray go-ahead; warm first per the MS-S1 note)::

    uv run python -m benchmarks.procedure_comparison.run_comparison --warm --limit 3
    uv run python -m benchmarks.procedure_comparison.run_comparison \\
        --model gpt-oss:20b --dump-json .claude/benchmark-results/bgamma.jsonl
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from benchmarks.procedure_baseline.loader import DATASET_DIR, load_dataset
from benchmarks.procedure_comparison.comparison import (
    ARM_A_ENERGY,
    ArmBSummary,
    ArmCSummary,
    breach_items,
    comparison_records,
    run_arm_b,
    run_arm_c,
    summarize_arm_b,
    summarize_arm_c,
)
from benchmarks.procedure_comparison.rag_arm import DEFAULT_CORPUS, DEFAULT_TOP_K, load_corpus
from services.api.config import settings
from services.engine.llm.client import OllamaClient

_DEFAULT_MODEL = "gpt-oss:20b"  # ADR-001 pin
_DEFAULT_KEEP_ALIVE = "10m"
_DEFAULT_DATASET = DATASET_DIR / "energy.yaml"


def _fmt_pct(value: float | None) -> str:
    return f"{value:.1%}" if value is not None else "n/a"


def _print_arm_b(summary: ArmBSummary) -> None:
    print(
        f"\narm (b) raw text-to-SQL: entity-ID {_fmt_pct(summary.entity_accuracy)} "
        f"({summary.entity_correct}/{summary.n}) | "
        f"failure-mode {summary.outcomes} | action-class: {summary.action_class} | "
        f"latency p50={summary.latency_p50_s}s p95={summary.latency_p95_s}s "
        f"max={summary.latency_max_s}s"
    )


def _print_arm_c(summary: ArmCSummary) -> None:
    print(
        f"\narm (c) lean RAG: headline {_fmt_pct(summary.headline_accuracy)} "
        f"({summary.headline_correct}/{summary.n} entity+action) | "
        f"entity {_fmt_pct(summary.entity_accuracy)} ({summary.entity_correct}/{summary.n}) | "
        f"action {_fmt_pct(summary.action_accuracy)} ({summary.action_correct}/{summary.n}) | "
        f"errors {summary.errors} | "
        f"latency p50={summary.latency_p50_s}s p95={summary.latency_p95_s}s "
        f"max={summary.latency_max_s}s"
    )


def _print_arm_a() -> None:
    print(
        f"\narm (a) governed-procedure stack (REUSED from REPORT — D-2, NOT re-run): "
        f"{ARM_A_ENERGY.headline_label}\n"
        f"        headline: {ARM_A_ENERGY.headline_note}\n"
        f"        latency:  {ARM_A_ENERGY.latency_note}\n"
        f"        source:   {ARM_A_ENERGY.source}"
    )


async def _main(args: argparse.Namespace) -> None:
    dataset = load_dataset(args.dataset)
    items = breach_items(dataset)
    if args.limit is not None:
        items = items[: args.limit]
    corpus = load_corpus(args.corpus)
    print(
        f"=== B-γ comparison (energy breach subset) — {len(items)} items, "
        f"top-k={args.k}, corpus={args.corpus.name} ({len(corpus)} snippets) ==="
    )

    base = OllamaClient(
        base_url=args.ollama_host, model=args.model, timeout=settings.llm_request_timeout_s
    )
    if args.warm:
        await base.warm(keep_alive=_DEFAULT_KEEP_ALIVE)

    arm_b = await run_arm_b(items, base, dataset.reading_parameter)
    arm_c = await run_arm_c(items, base, corpus, dataset.reading_parameter, k=args.k)

    _print_arm_a()
    _print_arm_b(summarize_arm_b(arm_b))
    _print_arm_c(summarize_arm_c(arm_c))

    if args.dump_json is not None:
        records = comparison_records(arm_b, arm_c)
        args.dump_json.write_text(
            "\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8"
        )
        print(f"\nDUMP: wrote {len(records)} item records -> {args.dump_json}")

    print(
        "\nNOTE: arm (a) entity+action is REUSED from REPORT.md (D-2 — not re-run); arm "
        "(b) is graded entity-ID only (action-class structurally N/A — D-3); arm (c) is "
        "graded entity-ID + action-class via the same grade_proposal checks (D-1). "
        "Reports-not-gates (B-3/B-6): a baseline matching arm (a) is a finding, not a "
        "build failure."
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="B-γ comparison baselines (live; manual).")
    parser.add_argument("--dataset", type=Path, default=_DEFAULT_DATASET)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--model", default=_DEFAULT_MODEL, help="ADR-001 pin: gpt-oss:20b.")
    parser.add_argument("--ollama-host", default=settings.ollama_host, help="MS-S1 Ollama URL.")
    parser.add_argument("--warm", action="store_true", help="Warm the model first (MS-S1 note).")
    parser.add_argument("--limit", type=int, default=None, help="Cap breach items (smoke).")
    parser.add_argument("--k", type=int, default=DEFAULT_TOP_K, help="Retriever top-k (arm c).")
    parser.add_argument(
        "--dump-json",
        type=Path,
        default=None,
        help="Write per-item JSONL (both arms' verdicts + evidence) for offline VERIFY.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(_main(_parse_args()))
