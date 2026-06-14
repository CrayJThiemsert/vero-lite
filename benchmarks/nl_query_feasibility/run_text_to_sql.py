"""Text-to-SQL comparison arm — run the same 12 questions as NL->SQL (MANUAL).

⚠️  MANUAL ONLY — warms + queries the live MS-S1 Ollama server (host-state).
NOT collected by CI; the offline scorer + DB + SELECT-guard tests live in
``tests/benchmark/test_nl_query_text_to_sql.py``. Pair this with
``run_benchmark.py`` (the engine-A arm) to separate StructuredQuery's
architecture ceiling from the model's filter-omission discipline.

Usage::

    uv run python -m benchmarks.nl_query_feasibility.run_text_to_sql \
        --model gpt-oss:20b --warm \
        --dump-json .claude/benchmark-results/<run>-text-to-sql.jsonl
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from benchmarks.nl_query_feasibility.harness import load_gold
from benchmarks.nl_query_feasibility.text_to_sql import (
    SqlResult,
    build_db,
    run_case,
    summarize,
)
from services.engine.llm.client import OllamaClient


def _print_case(r: SqlResult) -> None:
    status = r.error or (r.result_preview or "(empty)")
    print(
        f"  {r.qid:<6} -> {r.outcome:<8} rows={r.row_count:<3} {r.latency_s:5.1f}s\n"
        f"         SQL: {r.sql[:110]}\n"
        f"         got: {status[:110]}"
    )


async def _main(args: argparse.Namespace) -> None:
    _vertical, cases = load_gold(args.gold) if args.gold else load_gold()
    conn = build_db()
    client = OllamaClient(base_url=args.ollama_host, model=args.model, timeout=args.timeout)
    print(f"text-to-SQL arm: {len(cases)} questions  model={args.model} @ {args.ollama_host}\n")
    if args.warm:
        print("warming model ...")
        await client.warm(keep_alive="15m")

    results: list[SqlResult] = []
    for case in cases:
        result = await run_case(conn, case, client)
        results.append(result)
        _print_case(result)

    row = summarize(results)
    print(
        f"\n== text-to-SQL {row['correct']}/{row['n']} correct | "
        f"wrong {row['wrong'] or '[]'} | invalid {row['invalid'] or '[]'} | "
        f"latency p50 {row['latency_p50_s']}s p95 {row['latency_p95_s']}s "
        f"max {row['latency_max_s']}s"
    )

    if args.dump_json is not None:
        records = [vars(r) for r in results]
        args.dump_json.write_text(
            "\n".join(json.dumps(rec, ensure_ascii=False) for rec in records) + "\n",
            encoding="utf-8",
        )
        print(f"\nDUMP: wrote {len(records)} records -> {args.dump_json}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NL-query text-to-SQL arm (live; manual).")
    parser.add_argument("--gold", type=Path, default=None)
    parser.add_argument("--model", default="gpt-oss:20b")
    parser.add_argument("--ollama-host", default="http://192.168.1.133:11434")
    parser.add_argument("--warm", action="store_true")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--dump-json", type=Path, default=None)
    return parser.parse_args()


if __name__ == "__main__":
    try:
        asyncio.run(_main(_parse_args()))
    except KeyboardInterrupt:  # pragma: no cover
        sys.exit(130)
