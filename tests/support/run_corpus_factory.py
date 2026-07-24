"""Deterministic run-corpus factory (PLAN-0088 AC-2).

Generalizes the ``test_monitor_runs.py`` direct-ORM ``_seed_rows`` into a
**seeded-RNG** corpus large enough to exercise the cross-run substrate
(``services/db/run_analytics.py``): ≥ 3 procedures, all run statuses, resolved
gates, ฿ ``economic_impact`` facets (with a non-THB sub-subset and a malformed
sub-subset), ``read_refused`` facts, and band-verdict artifacts.

The expected aggregate values are computed **from the same seeded specs** that
materialize the ORM rows (``_expected`` iterates the specs in plain Python),
NOT reverse-fitted to the substrate's SQL — so a test comparing substrate output
to ``Corpus.expected`` is an independent oracle, not a mirror of the code under
test. Same ``seed`` ⇒ byte-identical corpus and expectations.

The economic-impact facet shape is produced through the real
``EconomicImpact`` model (``services/engine/economic_impact.py``) +
``model_dump(mode="json")``, so ``net_benefit_thb`` is the same JSON-string form
the orchestrator persists (Decimal→string); the malformed sub-subset is
hand-built to model a facet whose figure the never-raise extraction must skip
and count.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from services.engine.economic_impact import EconomicExposure, EconomicImpact
from services.engine.procedures.runs import (
    PipelineRun,
    PipelineRunStatus,
    StepResult,
    StepResultStatus,
)

_PROCEDURES = ("emergency_sourcing", "morning_round", "pm_service_round", "reorder_calm_path")
_STATUSES = tuple(s.value for s in PipelineRunStatus)  # all five lifecycle statuses
_SPINE = ("intake", "judge", "reshape", "rule_gate", "approve", "fulfill")  # 6 steps/run
_REFUSAL_KINDS = ("ontology_scope", "permission_denied")
_BASE_DAY = datetime(2026, 6, 1, 8, 0, tzinfo=UTC)
_N_DAYS = 5  # runs spread across five day-buckets (period_rollup)


@dataclass(frozen=True)
class _StepSpec:
    step_id: str
    status: str
    duration_ms: int
    reasoning_trace: list[dict[str, Any]] | None = None
    artifact: dict[str, Any] | None = None
    audit: dict[str, Any] | None = None


@dataclass(frozen=True)
class _RunSpec:
    run_id: str
    procedure_id: str
    status: str
    started_at: datetime
    updated_at: datetime
    steps: tuple[_StepSpec, ...]
    step_principals: dict[str, str | None] | None = None


@dataclass
class Corpus:
    """Materialized ORM rows + the independently-computed expected aggregates."""

    rows: list[PipelineRun | StepResult]
    run_count: int
    step_row_count: int
    # status -> run count
    status_counts: dict[str, int]
    # procedure_id -> run count
    procedure_counts: dict[str, int]
    # ISO day -> run count
    period_counts: dict[str, int]
    # (procedure_id, step_id) -> list of duration_ms samples
    durations: dict[tuple[str, str], list[int]]
    # (currency | None, procedure_id, facet_kind | None, ISO day)
    #   -> {run_ids: set[str], facet_count, valued, sum: Decimal}  (the AC-4 grouping)
    benefit: dict[tuple[str | None, str, str | None, str], dict[str, Any]]
    # refusal_kind -> count
    refusals: dict[str, int]
    # procedure_id -> resolved-gate count
    gates: dict[str, int]
    # procedure_id -> resolved gates carrying an approver principal in the step trace
    #   (gate_principal_recorded). NOT step_principals — that column holds the
    #   REQUESTER half; see the seeding site + the AC-2 wording note.
    gate_approvers: dict[str, int]
    # the DISTINCT union of every disclosed ฿ assumption (ADR-0030 D3)
    assumptions: list[str]
    # procedure_id -> {run_count, spans: list[float] (clamped >= 0), negatives: int}
    #   over the waiting_human runs only (AC-6)
    dwell: dict[str, dict[str, Any]]
    # band verdict label -> count (across artifacts) — carried for AC-10 later
    verdicts: dict[str, int] = field(default_factory=dict)


def _economic_detail(rng: random.Random, currency: str) -> dict[str, Any]:
    """A well-formed ``economic_impact`` ``detail`` dict via the real model."""
    governed = Decimal(rng.randint(1, 40)) * Decimal(50_000)
    net = Decimal(rng.randint(1, 30)) * Decimal(100_000)
    baseline = governed + net
    impact = EconomicImpact(
        provisional=True,
        currency=currency,
        kind="avoided_outage",
        baseline=EconomicExposure(label="ungoverned exposure", exposure_thb=baseline),
        governed=EconomicExposure(label="governed exposure", exposure_thb=governed),
        net_benefit_thb=net,
        assumptions=["seeded synthetic corpus"],
    )
    return impact.model_dump(mode="json")


def _make_specs(rng: random.Random, n_runs: int) -> list[_RunSpec]:
    specs: list[_RunSpec] = []
    for i in range(n_runs):
        procedure = _PROCEDURES[i % len(_PROCEDURES)]
        status = _STATUSES[i % len(_STATUSES)]
        started_at = _BASE_DAY + timedelta(days=i % _N_DAYS, minutes=rng.randint(0, 600))
        # A backward-clock subset, deliberately intersected with waiting_human
        # (i % 5 == 1) so AC-6's negative_clock_spans counter is exercised at all:
        # 6 % 5 == 1, and every i ≡ 6 (mod 25) keeps that residue.
        if i % 25 == 6:
            updated_at = started_at - timedelta(seconds=2)
        else:
            updated_at = started_at + timedelta(minutes=5)
        steps: list[_StepSpec] = []
        step_principals: dict[str, str | None] | None = None
        for step_id in _SPINE:
            duration = rng.randint(1, 500)
            trace: list[dict[str, Any]] | None = None
            artifact: dict[str, Any] | None = None
            audit: dict[str, Any] | None = None
            step_status = StepResultStatus.COMPLETE.value

            if step_id == "judge" and i % 2 == 0:
                # ฿ facet: THB, with a USD sub-subset and a malformed sub-subset.
                currency = "USD" if i % 10 == 0 else "THB"
                if i % 14 == 0:  # malformed: figure absent -> figures_missing, never-raise
                    trace = [
                        {
                            "step_id": "economic-impact-0",
                            "kind": "economic_impact",
                            "summary": "malformed",
                            "detail": {"currency": currency},
                        }
                    ]
                else:
                    trace = [
                        {
                            "step_id": "economic-impact-0",
                            "kind": "economic_impact",
                            "summary": "impact",
                            "detail": _economic_detail(rng, currency),
                        }
                    ]
            elif step_id == "intake" and i % 5 == 0:
                trace = [
                    {
                        "step_id": "intake",
                        "kind": "read_refused",
                        "refusal_kind": _REFUSAL_KINDS[(i // 5) % len(_REFUSAL_KINDS)],
                        "object_type": "Asset",
                    }
                ]
            elif step_id == "reshape" and i % 7 == 0:
                verdict = ("breach", "watch", "ok")[i % 3]
                artifact = {"output_set": [{"entity": f"e-{i}", "verdict": verdict}]}
                trace = [
                    {
                        "step_id": "reshape",
                        "kind": "verdict_computed",
                        "summary": "band",
                        "counts": {verdict: 1},
                    }
                ]
            elif step_id == "approve" and i % 3 == 0:
                # resolved gate: approver recorded the way action_step.py records it
                # (trace gate_principal_recorded + audit governed_decision), requester
                # in run.step_principals. NOTE: the approver half is NOT in
                # step_principals — see the module note + the PR (AC-2 wording corrected).
                step_status = StepResultStatus.RESOLVED.value
                approver = f"person-approver-{i % 4}"
                requester = f"person-requester-{i % 4}"
                trace = [
                    {
                        "step_id": "approve",
                        "kind": "gate_principal_recorded",
                        "principal_id": approver,
                        "summary": "gate approved",
                    }
                ]
                audit = {
                    "governed_decision": {
                        "control_ref": {"kind": "doa_tier", "id": "t1"},
                        "principal_id": approver,
                    }
                }
                step_principals = {"approve": requester}

            steps.append(
                _StepSpec(
                    step_id=step_id,
                    status=step_status,
                    duration_ms=duration,
                    reasoning_trace=trace,
                    artifact=artifact,
                    audit=audit,
                )
            )
        specs.append(
            _RunSpec(
                run_id=f"run-{i:04d}",
                procedure_id=procedure,
                status=status,
                started_at=started_at,
                updated_at=updated_at,
                steps=tuple(steps),
                step_principals=step_principals,
            )
        )
    return specs


def _to_rows(specs: list[_RunSpec]) -> list[PipelineRun | StepResult]:
    rows: list[PipelineRun | StepResult] = []
    for spec in specs:
        rows.append(
            PipelineRun(
                run_id=spec.run_id,
                procedure_id=spec.procedure_id,
                agent_id="synthetic_agent",
                trigger_context={"triggered_by": "corpus-factory"},
                step_principals=spec.step_principals,
                status=spec.status,
                started_at=spec.started_at,
                updated_at=spec.updated_at,
            )
        )
        for idx, step in enumerate(spec.steps):
            rows.append(
                StepResult(
                    step_result_id=f"{spec.run_id}-{step.step_id}",
                    run_id=spec.run_id,
                    step_id=step.step_id,
                    status=step.status,
                    duration_ms=step.duration_ms,
                    reasoning_trace=step.reasoning_trace,
                    artifact=step.artifact,
                    audit=step.audit,
                    created_at=spec.started_at + timedelta(seconds=idx),
                )
            )
    return rows


def _tally_benefit(
    entry: dict[str, Any],
    spec: _RunSpec,
    benefit: dict[tuple[str | None, str, str | None, str], dict[str, Any]],
    assumptions: set[str],
) -> None:
    """Fold one ``economic_impact`` trace entry into the AC-4 grouping tallies."""
    detail = entry.get("detail", {})
    key = (
        detail.get("currency"),
        spec.procedure_id,
        detail.get("kind"),
        spec.started_at.date().isoformat(),
    )
    bucket = benefit.setdefault(
        key, {"run_ids": set(), "facet_count": 0, "valued": 0, "sum": Decimal(0)}
    )
    bucket["run_ids"].add(spec.run_id)
    bucket["facet_count"] += 1
    net = detail.get("net_benefit_thb")
    if isinstance(net, str) and _is_numeric(net):
        bucket["valued"] += 1
        bucket["sum"] += Decimal(net)
    for assumption in detail.get("assumptions") or []:
        assumptions.add(str(assumption))


def _tally_dwell(spec: _RunSpec, dwell: dict[str, dict[str, Any]]) -> None:
    """Fold one ``waiting_human`` run's SAME-ROW span into the AC-6 tallies.

    Clamped at >= 0, with the backward-clock rows counted rather than averaged in —
    the same contract ``waiting_dwell_stats`` holds in SQL.
    """
    raw = (spec.updated_at - spec.started_at).total_seconds()
    entry = dwell.setdefault(spec.procedure_id, {"run_count": 0, "spans": [], "negatives": 0})
    entry["run_count"] += 1
    entry["spans"].append(max(raw, 0.0))
    if raw < 0:
        entry["negatives"] += 1


def _tally_gate(
    spec: _RunSpec,
    step: _StepSpec,
    gates: dict[str, int],
    gate_approvers: dict[str, int],
) -> None:
    """Fold one resolved gate into the AC-7 tallies: the count and the approver half.

    The approver is a ``gate_principal_recorded`` trace entry carrying a
    ``principal_id`` — the way ``resolve_gated_step`` actually records it, and
    deliberately **not** ``step_principals``, which holds the REQUESTER half (the
    AC-2 wording correction; see the seeding site).

    Extracted rather than inlined for the same reason ``_tally_benefit`` and
    ``_tally_dwell`` are: the two extra branches tip ``_expected``'s loop body past
    ruff's ``C901`` ceiling of 10.
    """
    if step.status != StepResultStatus.RESOLVED.value:
        return
    gates[spec.procedure_id] += 1
    if any(
        entry.get("kind") == "gate_principal_recorded" and entry.get("principal_id")
        for entry in step.reasoning_trace or []
    ):
        gate_approvers[spec.procedure_id] += 1


def _expected(specs: list[_RunSpec]) -> Corpus:
    status_counts: dict[str, int] = defaultdict(int)
    procedure_counts: dict[str, int] = defaultdict(int)
    period_counts: dict[str, int] = defaultdict(int)
    durations: dict[tuple[str, str], list[int]] = defaultdict(list)
    benefit: dict[tuple[str | None, str, str | None, str], dict[str, Any]] = {}
    refusals: dict[str, int] = defaultdict(int)
    gates: dict[str, int] = defaultdict(int)
    gate_approvers: dict[str, int] = defaultdict(int)
    verdicts: dict[str, int] = defaultdict(int)
    assumptions: set[str] = set()
    dwell: dict[str, dict[str, Any]] = {}
    step_row_count = 0

    for spec in specs:
        status_counts[spec.status] += 1
        procedure_counts[spec.procedure_id] += 1
        period_counts[spec.started_at.date().isoformat()] += 1
        if spec.status == PipelineRunStatus.WAITING_HUMAN.value:
            _tally_dwell(spec, dwell)
        for step in spec.steps:
            step_row_count += 1
            durations[(spec.procedure_id, step.step_id)].append(step.duration_ms)
            _tally_gate(spec, step, gates, gate_approvers)
            for entry in step.reasoning_trace or []:
                kind = entry.get("kind")
                if kind == "economic_impact":
                    _tally_benefit(entry, spec, benefit, assumptions)
                elif kind == "read_refused":
                    refusals[str(entry.get("refusal_kind"))] += 1
                elif kind == "verdict_computed":
                    for label, n in (entry.get("counts") or {}).items():
                        verdicts[label] += n

    return Corpus(
        rows=_to_rows(specs),
        run_count=len(specs),
        step_row_count=step_row_count,
        status_counts=dict(status_counts),
        procedure_counts=dict(procedure_counts),
        period_counts=dict(period_counts),
        durations=dict(durations),
        benefit=benefit,
        refusals=dict(refusals),
        gates=dict(gates),
        gate_approvers=dict(gate_approvers),
        assumptions=sorted(assumptions),
        dwell=dwell,
        verdicts=dict(verdicts),
    )


def _is_numeric(text: str) -> bool:
    try:
        Decimal(text)
    except Exception:
        return False
    return True


def build_corpus(seed: int = 0, n_runs: int = 250) -> Corpus:
    """Build a deterministic run corpus + its independently-computed expectations.

    ``n_runs`` defaults to 250 (x 6 spine steps = 1,500 step rows) — the AC-1
    floor (≥ 250 runs / ≥ 1,250 step rows). Same ``seed`` ⇒ identical corpus.
    """
    rng = random.Random(seed)  # noqa: S311 — synthetic test corpus, not cryptographic
    specs = _make_specs(rng, n_runs)
    return _expected(specs)
