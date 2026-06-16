"""B-γ comparison harness end-to-end smoke + summaries (PLAN-0027 AC-4 / AC-5).

The offline mock gate: arms (b) + (c) run end-to-end over the REAL energy breach
subset with a deterministic mock ``ChatClient`` (one client serving both arms),
the per-arm summaries compute accuracy / failure-mode / latency, the dump records
join both arms per item, and arm (a) is REUSED (not re-run — D-2).
"""

from __future__ import annotations

import json
import re
from typing import Any

from benchmarks.procedure_baseline.loader import DATASET_DIR, load_dataset
from benchmarks.procedure_baseline.schema import Dataset
from benchmarks.procedure_comparison.comparison import (
    ARM_A_ENERGY,
    breach_items,
    comparison_records,
    run_arm_b,
    run_arm_c,
    summarize_arm_b,
    summarize_arm_c,
)
from benchmarks.procedure_comparison.rag_arm import load_corpus
from services.engine.llm.client import ChatResult


def _energy() -> Dataset:
    return load_dataset(DATASET_DIR / "energy.yaml")


class _SmokeClient:
    """One deterministic client serving both arms by branching on ``response_format``:

    * arm (b) (``response_format`` set) -> a generic correct discovery SELECT
      (every breach value is >= the 90 ceiling, every distractor below it);
    * arm (c) (freeform) -> echoes the FIRST asset key in the question (the breached
      entity is rendered first, mirroring ``scenario_to_event``) + the restart verb.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        self.calls.append({"has_format": response_format is not None})
        if response_format is not None:
            sql = "SELECT asset_id FROM operational_event WHERE measured_value >= 90"
            return ChatResult(content=json.dumps({"sql": sql}), thinking=None, model="mock", raw={})
        user = messages[-1]["content"]
        match = re.search(r"asset-\S+", user)
        primary_key = match.group(0).rstrip(".;,") if match else "the affected asset"
        answer = f"Restart {primary_key} (reset / reboot) after a human go/no-go."
        return ChatResult(content=answer, thinking=None, model="mock", raw={})


def test_breach_items_filters_to_the_forty_breach() -> None:
    items = breach_items(_energy())
    assert len(items) == 40  # 28 boundary cluster + 12 hard
    assert all(item.expected.disposition.value == "breach" for item in items)


async def test_comparison_smoke_runs_end_to_end_green() -> None:
    dataset = _energy()
    items = breach_items(dataset)
    client = _SmokeClient()
    corpus = load_corpus()

    arm_b = await run_arm_b(items, client, dataset.reading_parameter)
    arm_c = await run_arm_c(items, client, corpus, dataset.reading_parameter, k=4)

    assert len(arm_b) == 40
    assert len(arm_c) == 40
    # one arm-(b) call + one arm-(c) call per item, no second "verify" call (D-6)
    assert len(client.calls) == 80

    summary_b = summarize_arm_b(arm_b)
    summary_c = summarize_arm_c(arm_c)

    # the deterministic mocks resolve every item correctly -> a green end-to-end path
    assert summary_b.entity_accuracy == 1.0
    assert summary_b.outcomes == {"correct": 40, "wrong": 0, "invalid": 0}
    assert summary_c.entity_accuracy == 1.0
    assert summary_c.action_accuracy == 1.0
    assert summary_c.headline_accuracy == 1.0
    assert summary_c.errors == 0


async def test_comparison_records_join_both_arms_per_item() -> None:
    dataset = _energy()
    items = breach_items(dataset)[:5]
    client = _SmokeClient()

    arm_b = await run_arm_b(items, client, dataset.reading_parameter)
    arm_c = await run_arm_c(items, client, load_corpus(), dataset.reading_parameter, k=4)
    records = comparison_records(arm_b, arm_c)

    assert len(records) == 5
    first = records[0]
    assert set(first) == {"item_id", "arm_b", "arm_c"}
    assert first["arm_b"]["outcome"] == "correct"
    assert first["arm_c"]["passed"] is True
    assert first["arm_c"]["judgment"] is not None  # raw evidence carried
    # every record is JSON-serialisable (the --dump-json contract)
    assert json.loads(json.dumps(records)) == records


def test_summaries_are_empty_safe() -> None:
    summary_b = summarize_arm_b([])
    summary_c = summarize_arm_c([])
    assert summary_b.entity_accuracy is None
    assert summary_b.outcomes == {"correct": 0, "wrong": 0, "invalid": 0}
    assert summary_c.headline_accuracy is None
    assert summary_c.latency_p95_s == 0.0


def test_arm_a_reference_is_reused_from_report_not_run() -> None:
    """D-2: arm (a) is REUSED from REPORT.md — the harness joins its numbers, it
    never executes arm (a)."""
    assert ARM_A_ENERGY.source == "benchmarks/procedure_baseline/REPORT.md"
    assert "97.5" in ARM_A_ENERGY.headline_label
