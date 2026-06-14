"""NL-query feasibility spike — run the shipped engine-A path on a local model.

⚠️  MANUAL ONLY — warms + queries the live MS-S1 Ollama server (host-state
change; run only with Cray's go). NOT collected by CI (``pytest`` ``testpaths =
["tests"]``); the offline scorer + gold-set checks live in
``tests/benchmark/test_nl_query_feasibility_gold.py``.

What it measures: feed ~12 plain-language operator questions to the shipped
``services.engine.nl_query.answer_question`` (translate -> execute -> phrase)
over the deterministic energy synthetic data, and report:

* **expressible accuracy** — questions a single-object-type ``StructuredQuery``
  can express (filters + list/count); scored on the deterministic executed
  result (ids/count) vs hand-verified gold;
* **ceiling rescue** — questions the ``StructuredQuery`` layer CANNOT express
  (superlative / join / aggregate-beyond-count); scored on whether the phrase
  step's answer still carries the right facts;
* **latency** p50/p95/max per question (translate + phrase = 2 calls each).

This reports; it does not gate. The T2 (NL-query) vs T3 (real-data) roadmap
call is Cray's, made on this evidence.

Usage (after the ms-s1-ollama skill's warm.sh, or with --warm)::

    uv run python -m benchmarks.nl_query_feasibility.run_benchmark \
        --model gpt-oss:20b --warm \
        --dump-json .claude/benchmark-results/<run>.jsonl
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from benchmarks.nl_query_feasibility.harness import CaseResult, load_gold, run_case, summarize
from services.engine.llm.client import OllamaClient
from verticals.energy.data_adapter import register_energy_adapter


def _print_case(r: CaseResult) -> None:
    lane = "ceiling" if r.ceiling else "express"
    got = r.got_object_type or "—"
    snippet = r.answer.replace("\n", " ")[:70]
    print(
        f"  [{lane:<7}] {r.qid:<6} {r.category:<18} -> {r.outcome:<8} "
        f"obj={got:<16} n={r.got_count:<3} {r.latency_s:5.1f}s | {snippet}"
    )


def _print_summary(row: dict[str, Any]) -> None:
    def pct(v: float | None) -> str:
        return f"{v:.0%}" if v is not None else "—"

    print(
        f"\n== {row['correct']}/{row['n']} correct | "
        f"expressible {pct(row['expressible_acc'])} | "
        f"ceiling-rescue {pct(row['ceiling_rescue'])} | "
        f"wrong {row['wrong'] or '[]'} | invalid {row['invalid'] or '[]'} | "
        f"latency p50 {row['latency_p50_s']}s p95 {row['latency_p95_s']}s "
        f"max {row['latency_max_s']}s"
    )


async def _main(args: argparse.Namespace) -> None:
    vertical, cases = load_gold(args.gold)
    register_energy_adapter()
    client = OllamaClient(base_url=args.ollama_host, model=args.model, timeout=args.timeout)
    print(f"NL-query feasibility spike: {len(cases)} questions, vertical '{vertical}'")
    print(f"model={args.model} @ {args.ollama_host}\n")
    if args.warm:
        print("warming model ...")
        await client.warm(keep_alive="15m")

    results: list[CaseResult] = []
    for case in cases:
        result = await run_case(case, vertical, client)
        results.append(result)
        _print_case(result)

    row = summarize(results)
    _print_summary(row)

    if args.dump_json is not None:
        records = [{**vars(r), "got_ids": list(r.got_ids), "model": args.model} for r in results]
        args.dump_json.write_text(
            "\n".join(json.dumps(rec, ensure_ascii=False) for rec in records) + "\n",
            encoding="utf-8",
        )
        print(f"\nDUMP: wrote {len(records)} case records -> {args.dump_json}")

    print(
        "\nNOTE: reports, does not gate. 'expressible' = StructuredQuery can "
        "express it (deterministic result check); 'ceiling-rescue' = the phrase "
        "step answered a query StructuredQuery alone cannot (superlative/join/"
        "aggregate). The NL-query (T2) vs real-data (T3) call is Cray's, on this "
        "evidence."
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NL-query feasibility spike (live; manual).")
    parser.add_argument("--gold", type=Path, default=None)
    parser.add_argument("--model", default="gpt-oss:20b", help="Ollama model tag.")
    parser.add_argument("--ollama-host", default="http://192.168.1.133:11434")
    parser.add_argument("--warm", action="store_true", help="Warm the model first.")
    parser.add_argument("--timeout", type=float, default=120.0, help="Per-call Ollama timeout (s).")
    parser.add_argument("--dump-json", type=Path, default=None)
    args = parser.parse_args()
    if args.gold is None:
        from benchmarks.nl_query_feasibility.harness import GOLD_PATH

        args.gold = GOLD_PATH
    return args


if __name__ == "__main__":
    try:
        asyncio.run(_main(_parse_args()))
    except KeyboardInterrupt:  # pragma: no cover
        sys.exit(130)
