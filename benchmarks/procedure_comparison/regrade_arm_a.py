"""Offline equal-rubric re-grade of arm (a) — the governed procedure stack — on
arm (c)'s reduced sub-task key (Group-A **A2**; the B-3 REPORT grading asymmetry).

The B-3 REPORT grades **arm (a)** on its FULL hardened key (entity + action **plus**
the ``forbidden_*`` PR2 precision add-ons) but **arm (c)** on the reduced common
sub-task (``_reduced_expected``: entity + action-class only). That asymmetry is
disclosed in the REPORT; a "60%-basis arm c beats arm a" reading is apples-to-
oranges. This re-grade removes it — it grades the SAME stored arm-(a) judgments on
the SAME reduced key arm (c) used, for a true apples-to-apples number.

No live model, no host-state: reads the stored hardened-run ``--dump-json``
(arm (a)'s ``LlmJudgment`` per item) and re-grades offline. Each judgment is first
re-graded on the FULL key and asserted to reproduce the stored run-time
``proposal_correct`` (a faithfulness sanity check — session-46 "confirm a real
verdict, not a reconstruction artifact"); then re-graded on ``_reduced_expected``.

Scores the **β breach** subset only (the headline graded unit); watch/ok records
in the dump are skipped (not in ``breach_items``).

Usage (offline)::

    uv run python -m benchmarks.procedure_comparison.regrade_arm_a \\
        --dump .claude/benchmark-results/2026-06-09-hardened-dump.jsonl \\
        --dataset benchmarks/procedure_baseline/dataset/aquaculture.yaml \\
        --dataset benchmarks/procedure_baseline/dataset/energy.yaml \\
        --dataset benchmarks/procedure_baseline/dataset/supply_chain.yaml
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from benchmarks.procedure_baseline.grader import GradeResult, grade_proposal
from benchmarks.procedure_baseline.loader import load_dataset
from benchmarks.procedure_baseline.schema import BenchmarkItem
from benchmarks.procedure_comparison.comparison import breach_items
from benchmarks.procedure_comparison.rag_arm import _check_passed, _reduced_expected
from services.engine.llm.structured import LlmJudgment

Tally = dict[str, int]
Record = dict[str, Any]


def _tally() -> Tally:
    return {"headline": 0, "entity": 0, "action": 0, "n": 0}


def _accumulate(tally: Tally, grade: GradeResult) -> None:
    tally["n"] += 1
    tally["headline"] += int(grade.passed)
    tally["entity"] += int(_check_passed(grade, "affected_primary_key"))
    tally["action"] += int(_check_passed(grade, "action_keywords"))


def _build_index(dataset_paths: list[Path]) -> dict[str, BenchmarkItem]:
    items: dict[str, BenchmarkItem] = {}
    for ds_path in dataset_paths:
        for item in breach_items(load_dataset(ds_path)):
            items[item.id] = item
    return items


def _regrade(
    records: list[Record], items: dict[str, BenchmarkItem]
) -> tuple[dict[str, Tally], dict[str, Tally], list[str], int, list[str]]:
    before: dict[str, Tally] = defaultdict(_tally)
    after: dict[str, Tally] = defaultdict(_tally)
    flips: list[str] = []
    sanity: list[str] = []
    skipped = 0

    for record in records:
        item = items.get(record["item_id"])
        if item is None:
            skipped += 1  # watch/ok item — A2 scores the β breach subset only
            continue
        if record.get("error") or "judgment" not in record:
            sanity.append(f"  {record['item_id']}: dump error / no judgment — skipped")
            continue

        vertical = record["vertical"]
        judgment = LlmJudgment.model_validate(record["judgment"])

        # BEFORE — full hardened key, recomputed and asserted == the stored grade.
        full = grade_proposal(judgment, item.expected)
        if full.passed != bool(record["proposal_correct"]):
            sanity.append(
                f"  {record['item_id']}: recomputed full-key passed={full.passed} != "
                f"stored proposal_correct={record['proposal_correct']}"
            )
        # AFTER — arm (c)'s reduced sub-task key (entity + action only).
        reduced = grade_proposal(judgment, _reduced_expected(item))

        _accumulate(before[vertical], full)
        _accumulate(after[vertical], reduced)

        if full.passed != reduced.passed:
            matched = sorted(entity.primary_key for entity in judgment.affected_entities)
            flips.append(
                f"  [{vertical}] {record['item_id']}: passed {full.passed}->{reduced.passed}  "
                f"matched={matched}"
            )

    return before, after, flips, skipped, sanity


def _print_report(
    dump_name: str,
    before: dict[str, Tally],
    after: dict[str, Tally],
    flips: list[str],
    skipped: int,
    sanity: list[str],
) -> None:
    print(f"=== arm (a) equal-rubric re-grade ({dump_name}) ===")
    print(f"skipped non-breach records: {skipped}")
    if sanity:
        print("!! SANITY MISMATCHES (reconstruction != stored grade) — investigate:")
        for line in sanity:
            print(line)
    else:
        print("sanity: every recomputed full-key grade == the stored proposal_correct (OK)")

    print("FLIPS (full key -> reduced key):" if flips else "FLIPS: none")
    for line in flips:
        print(line)

    overall_before, overall_after = _tally(), _tally()
    for vertical in sorted(before):
        b, a = before[vertical], after[vertical]
        for key in ("headline", "entity", "action", "n"):
            overall_before[key] += b[key]
            overall_after[key] += a[key]
        print(f"--- {vertical} ---")
        print(
            f"  BEFORE (full key):    headline {b['headline']}/{b['n']}  "
            f"entity {b['entity']}/{b['n']}  action {b['action']}/{b['n']}"
        )
        print(
            f"  AFTER  (reduced key): headline {a['headline']}/{a['n']}  "
            f"entity {a['entity']}/{a['n']}  action {a['action']}/{a['n']}"
        )
    print("--- overall ---")
    print(f"  BEFORE (full key):    headline {overall_before['headline']}/{overall_before['n']}")
    print(f"  AFTER  (reduced key): headline {overall_after['headline']}/{overall_after['n']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Equal-rubric arm-(a) re-grade on arm (c)'s reduced key (A2)."
    )
    parser.add_argument("--dump", type=Path, required=True)
    parser.add_argument(
        "--dataset",
        type=Path,
        action="append",
        required=True,
        help="procedure_baseline dataset YAML (repeatable, one per vertical)",
    )
    args = parser.parse_args()

    items = _build_index(args.dataset)
    records = [
        json.loads(line)
        for line in args.dump.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    before, after, flips, skipped, sanity = _regrade(records, items)
    _print_report(args.dump.name, before, after, flips, skipped, sanity)


if __name__ == "__main__":
    main()
