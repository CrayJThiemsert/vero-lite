"""Live runner for the procedure-baseline benchmark (PLAN-0019 B-β skeleton).

⚠️  MANUAL ONLY — hits the live ``gpt-oss:20b`` on MS-S1 and is **NOT collected
by CI** (``pytest`` ``testpaths = ["tests"]``). The benchmark RUN is a host-state
change: per the handoff, **ASK Cray before warming / running**. The grader /
loader / harness this drives are unit-tested offline under ``tests/benchmark/``
with a mock ``ChatClient``; this module only binds the real client.

Scope (skeleton): it runs the SD-B1 graded unit A — deterministic disposition
(~100% sanity) + the headline LLM action-proposal grade on the breach subset —
over the authored dataset and prints the two separately-reported metrics. The
B-gamma comparison baselines (raw text-to-SQL + RAG) and the B-delta per-model
latency sweep are deliberately TODO here; they land in their own steps.

Usage (after Cray go-ahead; warm first per the MS-S1 note)::

    uv run python -m benchmarks.procedure_baseline.run_benchmark --warm
    uv run python -m benchmarks.procedure_baseline.run_benchmark --model gpt-oss:20b --limit 5
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from benchmarks.procedure_baseline.harness import ItemResult, Summary, evaluate_item, summarize
from benchmarks.procedure_baseline.loader import DATASET_DIR, load_all
from benchmarks.procedure_baseline.schema import Dataset
from services.api.config import settings
from services.engine.llm.client import OllamaClient
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
    dataset: Dataset, *, model_override: str | None, host: str, warm: bool, limit: int | None
) -> list[ItemResult]:
    """Evaluate every item in one vertical's dataset against the live model."""
    goal, agent_model = _resolve_goal_and_model(dataset)
    model = model_override or agent_model
    client = OllamaClient(base_url=host, model=model, timeout=settings.llm_request_timeout_s)
    if warm:
        await client.warm(keep_alive=_DEFAULT_KEEP_ALIVE)
    items = dataset.items[:limit] if limit is not None else dataset.items
    results: list[ItemResult] = []
    for item in items:
        result = await evaluate_item(
            item,
            client,
            vertical=dataset.vertical,
            goal=goal,
            reading_parameter=dataset.reading_parameter,
        )
        results.append(result)
        _print_item(result)
    return results


def _print_item(result: ItemResult) -> None:
    sanity = "ok" if result.disposition_correct else "MISMATCH"
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
    print(
        f"\n{label}: headline {headline} "
        f"({summary.headline_correct}/{summary.graded} graded breach proposals) | "
        f"deterministic {summary.deterministic_accuracy:.1%} "
        f"({summary.deterministic_correct}/{summary.total} dispositions) | "
        f"by-disposition {summary.by_disposition}"
    )


async def _main(args: argparse.Namespace) -> None:
    _register_all_handlers()
    datasets = load_all(args.dataset_dir)
    all_results: list[ItemResult] = []
    for dataset in datasets:
        print(f"\n=== {dataset.vertical} ({dataset.procedure}) ===")
        results = await run_dataset(
            dataset,
            model_override=args.model,
            host=args.ollama_host,
            warm=args.warm,
            limit=args.limit,
        )
        all_results.extend(results)
        _print_summary(dataset.vertical, summarize(results))
    _print_summary("OVERALL", summarize(all_results))
    print(
        "\nNOTE: SD-B1 headline = LLM action-proposal correctness on breach items; "
        "deterministic disposition is a separate ~100% sanity number (NOT folded in). "
        "B-gamma (text-to-SQL + RAG baselines) and B-delta (latency sweep) are TODO."
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Procedure-baseline benchmark (live; manual).")
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--model", default=None, help="Override the per-agent llm_model (B-δ).")
    parser.add_argument("--ollama-host", default=settings.ollama_host, help="MS-S1 Ollama URL.")
    parser.add_argument("--warm", action="store_true", help="Warm the model first (MS-S1 note).")
    parser.add_argument("--limit", type=int, default=None, help="Cap items per vertical (smoke).")
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(_main(_parse_args()))
