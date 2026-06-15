"""Prompt-escalation experiment for the aggregate filter-omission gap (nl-08/nl-11).

⚠️  MANUAL ONLY — warms + queries the live MS-S1 Ollama server (host-state; run
only with Cray's go). NOT collected by CI.

Question this answers: can a STRONGER translate prompt make `gpt-oss:20b` (or any
model) stop dropping the implied filter on a superlative *aggregate* question?
Post-PR #320 the model emits `operation:max` + `aggregate_property` correctly but
`filters:[]`, so it matches all 11 OperationalEvents instead of the 7 celsius
readings (`result_count 11 ≠ gold 7`) even though the computed aggregate
(96.5 / Battery Bank A) is right. Memory `project_nl_query_aggregate_framing_drops_filter`
records 4 prior live runs of prompt tuning that did not overcome it; this script
re-tries with *escalating* variants and shows exactly which fail.

Design: each variant monkeypatches the module-level
`services.engine.nl_query._translate_messages` to inject an extra instruction
(and optionally a few-shot exchange) onto the BASELINE system prompt — every
variant therefore differs from baseline by ONLY the added text — then runs the
focus cases through the REAL `answer_question` path so the execute/score stages
are unchanged.

Variants are deliberately graded from a GENERAL principle (no gold answer
leaked) to a near-answer sibling hint, so Cray can see at what hint-strength (if
any) the model complies — a fix that needs the near-answer hint is not a
generalizable fix.

Usage::

    uv run python -m benchmarks.nl_query_feasibility.experiment_prompt_variants \
        --model gpt-oss:20b --warm \
        --dump-json .claude/benchmark-results/2026-06-15-nl-prompt-variants.jsonl
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import services.engine.nl_query as nlq
from benchmarks.nl_query_feasibility.harness import CaseResult, load_gold, run_case
from services.engine.llm.client import OllamaClient
from services.engine.llm.prompt import render_untrusted_block
from services.engine.ontology_meta import OntologyMeta
from verticals.energy.data_adapter import register_energy_adapter

# The default focus set: the two failing superlatives + one PASSING aggregate
# (nl-10, avg-by-resolve) as a regression control — a variant must not break it.
DEFAULT_ONLY = "nl-08,nl-11,nl-10"

MessageBuilder = Callable[..., list[dict[str, str]]]

_ORIG_TRANSLATE_MESSAGES: MessageBuilder = nlq._translate_messages


# --- escalating instruction blocks (general -> near-answer hint) -------------

_V1_GENERAL = (
    "AGGREGATE FILTERS (important): an aggregate question (max/min/avg/sum) STILL "
    "requires the filter its wording implies — exactly like a list/count would. If "
    "the question names a measurement KIND, a unit, a type, or a status, encode it "
    "as a filter even under an aggregate operation. NEVER emit an aggregate with an "
    "empty filters list unless the question explicitly aggregates over EVERY record "
    "of the type."
)

_V2_UNITS = _V1_GENERAL + (
    "\nUNITS COHERENCE: a numeric property (e.g. measured_value) may hold values in "
    "DIFFERENT units across records (a temperature in celsius, a frequency in hz). "
    "Aggregating it across units is meaningless. When the question asks for a "
    "quantity of one specific kind, add the matching unit/type filter so the "
    "aggregate runs over a single coherent unit."
)

# A near-answer SIBLING few-shot: same ontology, a unit (hz) that is NOT the gold
# answer's unit (celsius), and a question NOT in the gold set. Teaches the exact
# shape (aggregate + implied unit filter + group_by) one step from the answer.
# If only THIS strength works, the fix is not generalizable (it is gold-shaped
# prompting).
_V3_FEWSHOT_USER = (
    "Translate this operator question into the structured query JSON:\n\n"
    + render_untrusted_block(
        "operator question", "What is the highest frequency reading across the grid?"
    )
)
_V3_FEWSHOT_ASSISTANT = json.dumps(
    {
        "object_type": "OperationalEvent",
        "operation": "max",
        "filters": [{"property": "unit", "op": "eq", "value": "hz"}],
        "aggregate_property": "measured_value",
        "group_by": "asset_id",
        "limit": 50,
    }
)


def _augment(extra_system: str, *, few_shot: list[dict[str, str]] | None = None) -> MessageBuilder:
    """Build a variant that appends ``extra_system`` to the baseline system prompt
    (and optionally injects a few-shot exchange before the real user turn)."""

    def builder(
        question: str,
        vertical: str,
        meta: OntologyMeta,
        *,
        retry_feedback: str | None,
    ) -> list[dict[str, str]]:
        messages = _ORIG_TRANSLATE_MESSAGES(question, vertical, meta, retry_feedback=retry_feedback)
        system = {**messages[0], "content": messages[0]["content"] + "\n\n" + extra_system}
        rest = messages[1:]
        if few_shot is not None:
            return [system, *few_shot, *rest]
        return [system, *rest]

    return builder


VARIANTS: dict[str, MessageBuilder] = {
    "baseline": _ORIG_TRANSLATE_MESSAGES,
    "v1_general": _augment(_V1_GENERAL),
    "v2_units": _augment(_V2_UNITS),
    "v3_fewshot": _augment(
        _V2_UNITS,
        few_shot=[
            {"role": "user", "content": _V3_FEWSHOT_USER},
            {"role": "assistant", "content": _V3_FEWSHOT_ASSISTANT},
        ],
    ),
}


def _print_case(variant: str, r: CaseResult) -> None:
    query: dict[str, Any] = json.loads(r.query_json) if r.query_json else {}
    flt = query.get("filters", [])
    flt_str = ", ".join(f"{f['property']}{f['op']}{f['value']}" for f in flt) or "(none)"
    snippet = r.answer.replace("\n", " ")[:60]
    print(
        f"  [{variant:<11}] {r.qid:<6} {r.outcome:<8} n={r.got_count:<3} "
        f"filters=[{flt_str}] op={query.get('operation', '—'):<5} "
        f"{r.latency_s:5.1f}s | {snippet}"
    )


async def _main(args: argparse.Namespace) -> None:
    vertical, all_cases = load_gold(args.gold)
    wanted = [c.strip() for c in args.only.split(",") if c.strip()]
    by_id = {str(c["id"]): c for c in all_cases}
    cases = [by_id[q] for q in wanted if q in by_id]
    register_energy_adapter()
    client = OllamaClient(base_url=args.ollama_host, model=args.model, timeout=args.timeout)

    variant_names = list(VARIANTS) if args.variants == "all" else args.variants.split(",")
    print(f"prompt-variant experiment: model={args.model} @ {args.ollama_host}")
    print(f"focus cases: {wanted}  variants: {variant_names}\n")
    if args.warm:
        print("warming model ...")
        await client.warm(keep_alive="15m")

    records: list[dict[str, Any]] = []
    for variant in variant_names:
        builder = VARIANTS[variant]
        nlq._translate_messages = builder
        try:
            print(f"--- variant: {variant} ---")
            for case in cases:
                r = await run_case(case, vertical, client)
                _print_case(variant, r)
                records.append({**vars(r), "got_ids": list(r.got_ids), "variant": variant})
        finally:
            nlq._translate_messages = _ORIG_TRANSLATE_MESSAGES

    if args.dump_json is not None:
        args.dump_json.write_text(
            "\n".join(json.dumps(rec, ensure_ascii=False) for rec in records) + "\n",
            encoding="utf-8",
        )
        print(f"\nDUMP: wrote {len(records)} records -> {args.dump_json}")

    print(
        "\nNOTE: reports, does not gate. The fix is generalizable only if a GENERAL "
        "variant (v1/v2) makes the model emit the unit filter; if only v3_fewshot "
        "(near-answer sibling hint) works, prompting cannot close it cleanly."
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NL-query prompt-escalation experiment (live).")
    parser.add_argument("--gold", type=Path, default=None)
    parser.add_argument("--model", default="gpt-oss:20b")
    parser.add_argument("--ollama-host", default="http://192.168.1.133:11434")
    parser.add_argument("--warm", action="store_true")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--only", default=DEFAULT_ONLY, help="Comma-separated focus case ids.")
    parser.add_argument("--variants", default="all", help="'all' or comma-separated variant names.")
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
