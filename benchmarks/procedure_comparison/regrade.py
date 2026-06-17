"""Offline re-grade of a B-γ comparison ``--dump-json`` file under the patched key
normalizer (PLAN-0029 Step 2 — measurement calibration; no live model, no host-state).

Reads each dump record's raw ``arm_c.answer`` + the dataset item's candidate keys,
re-runs the SAME grading the live run used (``answer_to_judgment`` →
``grade_proposal`` on the D-1 ``_reduced_expected``), and prints a per-item flip
list + a per-vertical before→after summary. The "before" values are read from the
dump (graded at run time with the pre-PLAN-0029 normalizer); the "after" values are
this re-grade under the patched ``normalize_primary_key``.

Arm (b) is **not** re-graded: the dump stores only ``result_preview`` (truncated),
not the full SQL rows, so its entity blob cannot be faithfully reconstructed. It is
whitespace-invariant by construction — stored PKs carry ASCII hyphens, and the
whitespace fold only rewrites inter-cell separators (never creating a new PK
substring) — so its dump values carry forward unchanged.

Usage (offline)::

    uv run python -m benchmarks.procedure_comparison.regrade \\
        --dataset benchmarks/procedure_baseline/dataset/aquaculture.yaml \\
        --dump .claude/benchmark-results/2026-06-17-bgamma-aquaculture.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmarks.procedure_baseline.grader import grade_proposal
from benchmarks.procedure_baseline.loader import load_dataset
from benchmarks.procedure_baseline.schema import Scenario
from benchmarks.procedure_comparison.comparison import breach_items
from benchmarks.procedure_comparison.rag_arm import (
    _check_passed,
    _reduced_expected,
    answer_to_judgment,
)


def _candidate_keys(scenario: Scenario) -> list[str]:
    """The scenario's known entity universe (subject + distractors) — the same
    candidate set ``run_item_c`` builds for the arm-(c) entity check."""
    return [scenario.primary_key, *(decoy.primary_key for decoy in scenario.distractors)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline re-grade of a B-γ dump (PLAN-0029).")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--dump", type=Path, required=True)
    args = parser.parse_args()

    dataset = load_dataset(args.dataset)
    items = {item.id: item for item in breach_items(dataset)}
    records = [
        json.loads(line)
        for line in args.dump.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    n = len(records)
    before = {"headline": 0, "entity": 0, "action": 0}
    after = {"headline": 0, "entity": 0, "action": 0}
    flips: list[str] = []

    for record in records:
        item = items[record["item_id"]]
        arm_c = record["arm_c"]
        judgment = answer_to_judgment(arm_c["answer"], _candidate_keys(item.scenario))
        grade = grade_proposal(judgment, _reduced_expected(item))
        new_entity = _check_passed(grade, "affected_primary_key")
        new_action = _check_passed(grade, "action_keywords")
        new_passed = grade.passed

        before["headline"] += int(bool(arm_c["passed"]))
        before["entity"] += int(bool(arm_c["entity_correct"]))
        before["action"] += int(bool(arm_c["action_correct"]))
        after["headline"] += int(new_passed)
        after["entity"] += int(new_entity)
        after["action"] += int(new_action)

        old = (bool(arm_c["entity_correct"]), bool(arm_c["action_correct"]), bool(arm_c["passed"]))
        new = (new_entity, new_action, new_passed)
        if old != new:
            matched = [entity.primary_key for entity in judgment.affected_entities]
            flips.append(
                f"  {record['item_id']}: entity {old[0]}->{new[0]}  "
                f"action {old[1]}->{new[1]}  passed {old[2]}->{new[2]}  matched={matched}"
            )

    print(f"=== re-grade {dataset.vertical} ({args.dump.name}) — {n} items ===")
    print("FLIPS (before -> after):" if flips else "FLIPS: none")
    for line in flips:
        print(line)
    print("arm (c) summary:")
    print(
        f"  before: headline {before['headline']}/{n}  "
        f"entity {before['entity']}/{n}  action {before['action']}/{n}"
    )
    print(
        f"  after:  headline {after['headline']}/{n}  "
        f"entity {after['entity']}/{n}  action {after['action']}/{n}"
    )


if __name__ == "__main__":
    main()
