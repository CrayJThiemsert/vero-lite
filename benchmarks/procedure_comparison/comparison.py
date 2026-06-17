"""B-γ comparison harness (PLAN-0027 Step 2 / AC-4).

Runs arm (b) raw text-to-SQL + arm (c) lean RAG over the energy **breach subset**
(D-5), joins arm (a)'s **reused** REPORT numbers (D-2 — arm (a) is NOT re-run),
and emits per-arm **accuracy / failure-mode / latency**. ``comparison_records``
captures every per-item judgment for offline VERIFY (``--dump-json``; the
session-46 "confirm, don't infer" discipline).

Reports-not-gates (B-3/B-6): the summaries below are evidence, not bars — a
baseline matching or beating arm (a) is a finding, never a build failure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from benchmarks.procedure_baseline.harness import percentile
from benchmarks.procedure_baseline.schema import BenchmarkItem, Dataset, Disposition
from benchmarks.procedure_comparison.rag_arm import (
    ArmCResult,
    Snippet,
    run_item_c,
)
from benchmarks.procedure_comparison.text_to_sql_arm import (
    ACTION_CLASS_NA,
    ArmBResult,
    run_item_b,
)
from services.engine.llm.structured import ChatClient


def breach_items(dataset: Dataset) -> list[BenchmarkItem]:
    """The energy breach subset (D-5) — the graded mass, commensurable with arm
    (a)'s β headline (which is also breach-scoped)."""
    return [item for item in dataset.items if item.expected.disposition is Disposition.BREACH]


# --- arm (a): REUSED from REPORT.md (D-2 — NOT re-run) ------------------------


@dataclass(frozen=True)
class ArmAReference:
    """Arm (a) governed-procedure stack — REUSED from
    ``benchmarks/procedure_baseline/REPORT.md`` (D-2; arm (a) is NOT re-run in
    B-γ). The energy breach β headline (entity + action-class — the D-1 common
    sub-task) and the SD-2 per-judgment latency, from the Cray-approved host-state
    runs. These are joined into the comparison output; the authoritative figures
    live in the REPORT (the Step-5 join finalises the framing)."""

    headline_label: str
    headline_note: str
    latency_note: str
    source: str


_ARM_A_LATENCY_NOTE = (
    "SD-2 per-judgment p95 ≈ 28.7 to 31.8 s (full mode, aggregate across verticals) / "
    "21.6 s (skip lever); reports-not-gates."
)


ARM_A_ENERGY = ArmAReference(
    headline_label="97.5% to 100% (energy breach, 39-40 / 40)",
    headline_note=(
        "entity + action-class on the energy breach subset: 39/40 = 97.5% on the "
        "hardened run (2026-06-09); 40/40 = 100% with the Phase-1 prompt nudge "
        "(PLAN-0020 R1, 2026-06-11). gpt-oss:20b on MS-S1."
    ),
    latency_note="SD-2 per-judgment p95 ≈ 28.7 to 31.8 s (full mode) / 21.6 s (skip lever); "
    "reports-not-gates.",
    source="benchmarks/procedure_baseline/REPORT.md",
)


ARM_A_AQUACULTURE = ArmAReference(
    headline_label="100% (aquaculture breach, 40/40; hardened 24/40 = 60.0%)",
    headline_note=(
        "entity + action-class on the aquaculture breach subset: 24/40 = 60.0% on the "
        "hardened run (2026-06-09); 40/40 = 100% with the Phase-1 prompt nudge (PLAN-0020 "
        "R1, 2026-06-11). The OQ-3-ratified headline reads the nudged 100% AND reports the "
        "60 to 100 range + nudge dependency (PLAN-0028 §1.2). gpt-oss:20b on MS-S1."
    ),
    latency_note=_ARM_A_LATENCY_NOTE,
    source="benchmarks/procedure_baseline/REPORT.md",
)


ARM_A_SUPPLY_CHAIN = ArmAReference(
    headline_label="100% (supply_chain breach, 40/40)",
    headline_note=(
        "entity + action-class on the supply_chain breach subset: 40/40 = 100% on BOTH "
        "the hardened run (2026-06-09) and the nudged run (PLAN-0020 R1, 2026-06-11). "
        "gpt-oss:20b on MS-S1."
    ),
    latency_note=_ARM_A_LATENCY_NOTE,
    source="benchmarks/procedure_baseline/REPORT.md",
)


ARM_A_BY_VERTICAL: dict[str, ArmAReference] = {
    "energy": ARM_A_ENERGY,
    "aquaculture": ARM_A_AQUACULTURE,
    "supply_chain": ARM_A_SUPPLY_CHAIN,
}


# --- per-arm summaries -------------------------------------------------------


@dataclass(frozen=True)
class ArmBSummary:
    """Arm (b) aggregate: entity-ID accuracy + the failure-mode outcome split +
    latency. Action-class is structurally N/A (D-3)."""

    n: int
    entity_correct: int
    entity_accuracy: float | None
    outcomes: dict[str, int]
    action_class: str
    latency_p50_s: float
    latency_p95_s: float
    latency_max_s: float


@dataclass(frozen=True)
class ArmCSummary:
    """Arm (c) aggregate: the D-1 sub-task headline (entity AND action) + the
    entity / action breakdown + error count + latency."""

    n: int
    headline_correct: int
    headline_accuracy: float | None
    entity_correct: int
    entity_accuracy: float | None
    action_correct: int
    action_accuracy: float | None
    errors: int
    latency_p50_s: float
    latency_p95_s: float
    latency_max_s: float


def _latency_stats(results: list[float]) -> tuple[float, float, float]:
    return (
        round(percentile(results, 50.0), 2),
        round(percentile(results, 95.0), 2),
        round(max(results), 2) if results else 0.0,
    )


def summarize_arm_b(results: list[ArmBResult]) -> ArmBSummary:
    outcomes = {"correct": 0, "wrong": 0, "invalid": 0}
    for result in results:
        outcomes[result.outcome] += 1
    entity_correct = sum(1 for result in results if result.entity_correct)
    p50, p95, maximum = _latency_stats([result.latency_s for result in results])
    return ArmBSummary(
        n=len(results),
        entity_correct=entity_correct,
        entity_accuracy=(entity_correct / len(results)) if results else None,
        outcomes=outcomes,
        action_class=ACTION_CLASS_NA,
        latency_p50_s=p50,
        latency_p95_s=p95,
        latency_max_s=maximum,
    )


def summarize_arm_c(results: list[ArmCResult]) -> ArmCSummary:
    entity_correct = sum(1 for result in results if result.entity_correct)
    action_correct = sum(1 for result in results if result.action_correct)
    headline_correct = sum(1 for result in results if result.passed)
    errors = sum(1 for result in results if result.error)
    n = len(results)
    p50, p95, maximum = _latency_stats([result.latency_s for result in results])
    return ArmCSummary(
        n=n,
        headline_correct=headline_correct,
        headline_accuracy=(headline_correct / n) if results else None,
        entity_correct=entity_correct,
        entity_accuracy=(entity_correct / n) if results else None,
        action_correct=action_correct,
        action_accuracy=(action_correct / n) if results else None,
        errors=errors,
        latency_p50_s=p50,
        latency_p95_s=p95,
        latency_max_s=maximum,
    )


# --- run orchestration -------------------------------------------------------


async def run_arm_b(
    items: list[BenchmarkItem], client: ChatClient, reading_parameter: str
) -> list[ArmBResult]:
    """Run arm (b) over the breach items (sequential — one MS-S1 GPU serializes)."""
    return [await run_item_b(item.id, item.scenario, client, reading_parameter) for item in items]


async def run_arm_c(
    items: list[BenchmarkItem],
    client: ChatClient,
    corpus: list[Snippet],
    reading_parameter: str,
    *,
    k: int,
    vertical: str = "energy",
) -> list[ArmCResult]:
    """Run arm (c) over the breach items (sequential — one MS-S1 GPU serializes).

    ``vertical`` drives the data-derived RAG persona (``persona_for``); the entity
    word is derived per-item from the scenario. ``vertical="energy"`` is
    byte-identical to the pre-data-driven prompt."""
    return [
        await run_item_c(item, client, corpus, reading_parameter, k=k, vertical=vertical)
        for item in items
    ]


def comparison_records(arm_b: list[ArmBResult], arm_c: list[ArmCResult]) -> list[dict[str, Any]]:
    """One per-item record per breach item (joined on ``item_id``): both arms'
    verdicts + the raw evidence (SQL / answer / judgment) for offline VERIFY."""
    by_id_c = {result.item_id: result for result in arm_c}
    records: list[dict[str, Any]] = []
    for result_b in arm_b:
        result_c = by_id_c.get(result_b.item_id)
        records.append(
            {
                "item_id": result_b.item_id,
                "arm_b": {
                    "outcome": result_b.outcome,
                    "entity_correct": result_b.entity_correct,
                    "action_class": result_b.action_class,
                    "sql": result_b.sql,
                    "row_count": result_b.row_count,
                    "result_preview": result_b.result_preview,
                    "latency_s": round(result_b.latency_s, 3),
                    "error": result_b.error,
                },
                "arm_c": None
                if result_c is None
                else {
                    "entity_correct": result_c.entity_correct,
                    "action_correct": result_c.action_correct,
                    "passed": result_c.passed,
                    "retrieved_ids": result_c.retrieved_ids,
                    "answer": result_c.answer,
                    "latency_s": round(result_c.latency_s, 3),
                    "error": result_c.error,
                    "judgment": result_c.judgment.model_dump()
                    if result_c.judgment is not None
                    else None,
                },
            }
        )
    return records


__all__ = [
    "ARM_A_AQUACULTURE",
    "ARM_A_BY_VERTICAL",
    "ARM_A_ENERGY",
    "ARM_A_SUPPLY_CHAIN",
    "ArmAReference",
    "ArmBSummary",
    "ArmCSummary",
    "breach_items",
    "comparison_records",
    "run_arm_b",
    "run_arm_c",
    "summarize_arm_b",
    "summarize_arm_c",
]
