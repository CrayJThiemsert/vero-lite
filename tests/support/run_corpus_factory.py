"""Deterministic run-corpus factory (PLAN-0088 AC-2, extended for AC-10).

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

Step 6 (AC-10) reopened this factory for the four Group-B shapes. Four of the
changes are **fidelity corrections**, not new dimensions — the shapes seeded
here were shapes the engine never writes, which would have let a Group-B query
pass against a fixture while being wrong against production (the AC-2 class of
error, and the reason the s170 mutation probe exists):

1. ``audit["governed_decision"]`` is a **LIST**, not a dict.
   ``_record_governed_decision`` (``action_step.py``) concatenates two
   list-returning helpers, and ``test_procurement_sod_gate`` asserts
   ``resolved.audit["governed_decision"] == [...]`` against engine-produced
   rows. B2 reads the DoA tier out of this structure, so the array shape is
   load-bearing.
2. ``refusal_kind`` values now come from the shipped ``ReadRefusalKind`` enum.
   The previous ``ontology_scope`` / ``permission_denied`` pair existed in no
   enum in ``services/`` — a vocabulary the engine cannot emit.
3. An evaluate step's ``counts`` object carries **every** ``Verdict`` label,
   zeros included (``evaluate_step.py`` seeds ``{v.value: 0 for v in Verdict}``
   before incrementing), and its ``output_set`` entries are ``{**entity,
   "verdict": ...}`` — so each carries the reading under ``VALUE_FIELD``
   (``measured_value``). B1's "measured value vs its band verdict" reads it.
4. ``trigger_context`` carries the real ``trigger`` key, whose vocabulary is the
   shipped ``Trigger`` enum (``manual`` / ``schedule`` / ``event``) — stamped by
   ``scheduler._trigger_context`` and by the event bridge. B4 groups on it.
   (PLAN-0088 SD-9's aside called ``trigger`` "undefined"; the enum and both
   stamping sites shipped before this PLAN. What was missing was corpus
   variation and a primitive that reads it — not a definition.)

Plus one new-dimension change and one **independence** fix:

5. Resolved gates now carry a varying DoA tier and a **reject** sub-subset
   (the real ``action_rejected`` trace entry), because B2 groups approval
   OUTCOME by tier and neither existed.
6. The refusal kind was a bijection of ``procedure_id``: refusals fall on
   ``i % 5 == 0``, so for ``i = 5k`` the procedure index was ``k % 4`` and the
   kind index ``k % 2`` — parity of the procedure index DETERMINED the kind.
   B3 groups by kind x procedure, and against that corpus a query that dropped
   the kind dimension entirely would have produced identical numbers. Every new
   dimension below is checked for the same collapse, and each seeding helper
   records the residue arithmetic that rules it out.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from services.engine.economic_impact import EconomicExposure, EconomicImpact
from services.engine.procedures.query_step import ReadRefusalKind
from services.engine.procedures.runs import (
    PipelineRun,
    PipelineRunStatus,
    StepResult,
    StepResultStatus,
)
from services.engine.procedures.spec import Trigger

_PROCEDURES = ("emergency_sourcing", "morning_round", "pm_service_round", "reorder_calm_path")
_STATUSES = tuple(s.value for s in PipelineRunStatus)  # all five lifecycle statuses
_SPINE = ("intake", "judge", "reshape", "rule_gate", "approve", "fulfill")  # 6 steps/run
# The SHIPPED read-refusal vocabulary (services/engine/procedures/query_step.py).
_REFUSAL_KINDS = tuple(k.value for k in ReadRefusalKind)
# The SHIPPED trigger vocabulary (services/engine/procedures/spec.py).
_TRIGGERS = tuple(t.value for t in Trigger)
_DOA_TIERS = ("t1", "t2", "t3")
_VERDICTS = ("breach", "watch", "ok")
_BASE_DAY = datetime(2026, 6, 1, 8, 0, tzinfo=UTC)
_N_DAYS = 5  # runs spread across five day-buckets (period_rollup)

# Per-verdict reading bands, so B1's per-verdict summary stats DIFFER by verdict:
# a query that grouped the readings under the wrong verdict would move the means.
_VERDICT_BASE = {"breach": 90, "watch": 60, "ok": 20}

_RESOLVED_GATE = 3  # a gate resolves on i % 3 == 0
_REJECT_IN_GATES = 5  # of the resolved gates, m = i // 3 with m % 5 == 1 rejects


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
    trigger: str = Trigger.MANUAL.value


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
    # band verdict label -> summed count across verdict_computed `counts` objects (AC-10 B1)
    verdicts: dict[str, int] = field(default_factory=dict)
    # (procedure_id, status) -> run count — the CONJUNCTIVE grouping neither
    #   procedure_rollup nor status_rollup can express (Step 4.5 / SD-9 (a2))
    run_status_counts: dict[tuple[str, str], int] = field(default_factory=dict)
    # (procedure_id, status) -> list of PER-RUN summed duration_ms
    run_duration_totals: dict[tuple[str, str], list[int]] = field(default_factory=dict)
    # ISO date of the week's MONDAY -> run count (date_trunc('week') semantics)
    week_counts: dict[str, int] = field(default_factory=dict)
    # --- AC-10 Group-B expectations ---
    # verdict label -> {entity_count, readings: list[int], readings_missing} (B1)
    verdict_readings: dict[str, dict[str, Any]] = field(default_factory=dict)
    # (doa_tier, outcome) -> {gate_count, durations: list[int]} (B2)
    gate_tier_outcomes: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)
    # (refusal_kind, procedure_id) -> count (B3)
    refusals_by_procedure: dict[tuple[str, str], int] = field(default_factory=dict)
    # (procedure_id, trigger, status) -> run count (B4)
    trigger_outcomes: dict[tuple[str, str, str], int] = field(default_factory=dict)


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


def _gate_approver(i: int) -> str | None:
    """Run ``i``'s gate approver, or ``None`` for the UNATTRIBUTED sub-subset.

    Resolved gates are ``i % 3 == 0``. If every one of them carried an approver,
    ``gate_approvers`` would equal ``gates`` identically and AC-7's approver-half
    assertion could not tell a real extraction from a plain resolved-count — a
    mutation probe proved exactly that (deleting the approver FILTER left both
    value oracles GREEN). So a sub-subset resolves with no approver recorded.

    ``i % 15 == 6`` is a proper subset of ``i % 3 == 0`` (6 % 3 == 0), and its
    ``i mod 4`` varies across 6, 21, 36, 51 -> 2, 1, 0, 3 — so the gap lands on
    every procedure rather than pooling on one (the Step-3 intersection lesson).

    Returning ``None`` also exercises the JSONB sharp edge the substrate module
    documents: a Python ``None`` lands as the JSON scalar ``null``, and
    ``->>'principal_id'`` yields SQL ``NULL``, which is what the ``IS NOT NULL``
    test in ``gate_counts`` must exclude.
    """
    return None if i % 15 == 6 else f"person-approver-{i % 4}"


def _doa_tier(i: int) -> str:
    """The resolved DoA tier of run ``i``'s gate (B2 groups on this).

    Indexed by ``(i // 3) % 3`` rather than by ``i`` directly: gates resolve on
    ``i % 3 == 0``, so ``i = 3m`` and the tier index becomes ``m % 3`` while the
    procedure index is ``3m % 4``. Over ``m mod 12`` all twelve (procedure, tier)
    pairs appear uniformly — the tier is INDEPENDENT of the procedure, so a query
    that lost the tier dimension cannot reproduce the same numbers.
    """
    return _DOA_TIERS[(i // _RESOLVED_GATE) % len(_DOA_TIERS)]


def _gate_outcome(i: int) -> str:
    """``"rejected"`` for the reject sub-subset of resolved gates, else ``"approved"``.

    ``m = i // 3`` with ``m % 5 == 1``. Checked for collapse the same way: over
    ``m in (1, 6, 11, 16)`` the procedure index ``3m % 4`` runs 3, 2, 1, 0 and the
    tier index ``m % 3`` runs 1, 0, 2, 1 — so rejects land on every procedure AND
    every tier, rather than pooling. It is also disjoint from the approver-less
    subset (``i % 15 == 6`` gives ``m % 5 == 2``), which matches the engine: the
    ``gate_principal_recorded`` trace and the ``governed_decision`` tie are
    recorded whether the human approved OR rejected — only the ``action_rejected``
    entry distinguishes them.
    """
    return "rejected" if (i // _RESOLVED_GATE) % _REJECT_IN_GATES == 1 else "approved"


def _reading(i: int, verdict: str) -> int | None:
    """Run ``i``'s ``measured_value`` for a band artifact, or ``None`` when omitted.

    Band artifacts fall on ``i % 7 == 0``. ``i % 21 == 0`` is a proper subset of
    that (21 = 3 x 7) whose reading is ABSENT — so B1's never-raise extraction has
    something to skip and count, and an assertion on the reading stats cannot pass
    by vacuously seeing every entity.
    """
    if i % 21 == 0:
        return None
    return _VERDICT_BASE[verdict] + (i % 10)


def _verdict_trace(verdict: str) -> dict[str, Any]:
    """The ``verdict_computed`` trace entry as ``evaluate_step`` writes it.

    ``counts`` is seeded with EVERY ``Verdict`` label at zero and then incremented,
    so the real object always carries all three keys. The previous fixture wrote a
    single key, which a summing query and a key-counting query cannot be told apart
    against.
    """
    counts = dict.fromkeys(_VERDICTS, 0)
    counts[verdict] = 1
    return {"step_id": "reshape", "kind": "verdict_computed", "summary": "band", "counts": counts}


def _band_seed(i: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """A band step's ``artifact`` + ``reasoning_trace``, as ``evaluate_step`` writes them.

    Extracted rather than inlined: the absent-reading branch tips ``_make_specs``
    past ruff's ``C901`` ceiling of 10. Moving the BRANCH, not merely its condition,
    is what actually lowers the score (the s170 lesson).
    """
    verdict = _VERDICTS[i % 3]
    # {**entity, "verdict": ...} is the shape evaluate_step writes, so the reading
    # rides on the SAME entity dict the verdict does.
    entity: dict[str, Any] = {"entity_id": f"e-{i}", "verdict": verdict}
    reading = _reading(i, verdict)
    if reading is not None:
        entity["measured_value"] = reading
    return {"output_set": [entity]}, [_verdict_trace(verdict)]


def _gate_seed(i: int) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, str | None]]:
    """A resolved gate's trace + audit + the run's REQUESTER ``step_principals``.

    Records the gate the way ``action_step.py`` does: the ``gate_principal_recorded``
    trace entry and the ``governed_decision`` tie are emitted whether the human
    approved OR rejected, and only an ``action_rejected`` entry distinguishes the
    two. The approver half is deliberately **not** in ``step_principals``, which
    holds the REQUESTER half (the AC-2 wording correction).

    ``governed_decision`` is a **LIST** — the shape ``_record_governed_decision``
    persists and ``test_procurement_sod_gate`` asserts against engine-produced rows.
    A dict here would let B2's tier extraction pass against a fixture the engine
    never writes.
    """
    approver = _gate_approver(i)
    trace: list[dict[str, Any]] = [
        {
            "step_id": "approve",
            "kind": "gate_principal_recorded",
            "principal_id": approver,
            "summary": "gate approved",
        }
    ]
    if _gate_outcome(i) == "rejected":
        trace.append(
            {
                "kind": "action_rejected",
                "action_id": f"act-{i}",
                "summary": (
                    "human-rejected handler 'seed_handler'; not executed "
                    "(run continues — a reject is a recorded decision, not a failure)"
                ),
            }
        )
    audit = {
        "governed_decision": [
            {
                "control_ref": {"kind": "doa_tier", "id": _doa_tier(i)},
                "principal_id": approver,
            }
        ]
    }
    return trace, audit, {"approve": f"person-requester-{i % 4}"}


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
                # The kind index is (i // 5) % 5 = k % 5 against a procedure index of
                # k % 4 (i = 5k), so kind and procedure are independent over k mod 20.
                # Indexing by k % 2 (the previous shape) made the procedure's parity
                # DETERMINE the kind, which would let B3 pass without its kind dimension.
                trace = [
                    {
                        "step_id": "intake",
                        "kind": "read_refused",
                        "refusal_kind": _REFUSAL_KINDS[(i // 5) % len(_REFUSAL_KINDS)],
                        "object_type": "Asset",
                    }
                ]
            elif step_id == "reshape" and i % 7 == 0:
                artifact, trace = _band_seed(i)
            elif step_id == "approve" and i % _RESOLVED_GATE == 0:
                step_status = StepResultStatus.RESOLVED.value
                trace, audit, step_principals = _gate_seed(i)

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
                # (i // 5) % 3 keeps the trigger independent of the procedure (i % 4),
                # the status (i % 5) and the gate residue (i % 3) alike — indexing by
                # i % 3 would have made "manual" mean "has a resolved gate".
                trigger=_TRIGGERS[(i // 5) % len(_TRIGGERS)],
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
                # "trigger" is the key both shipped stampers use (scheduler +
                # event bridge); "triggered_by" is what persistence reads for the
                # actor. B4 groups on "trigger".
                trigger_context={"trigger": spec.trigger, "triggered_by": "corpus-factory"},
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


def _tally_refusal(
    entry: dict[str, Any],
    spec: _RunSpec,
    refusals: dict[str, int],
    by_procedure: dict[tuple[str, str], int],
) -> None:
    """Fold one ``read_refused`` fact into the kind tally AND the B3 kind x procedure tally."""
    kind = str(entry.get("refusal_kind"))
    refusals[kind] += 1
    key = (kind, spec.procedure_id)
    by_procedure[key] = by_procedure.get(key, 0) + 1


def _tally_verdict(
    step: _StepSpec,
    verdicts: dict[str, int],
    readings: dict[str, dict[str, Any]],
) -> None:
    """Fold one band step into the B1 tallies: label counts (trace) + readings (artifact).

    Both halves live on the same step, which is why this reads the step rather than a
    single trace entry: the label counts come from ``verdict_computed.counts`` and the
    readings from ``artifact["output_set"]``, exactly the two places ``evaluate_step``
    writes them. An entity with no ``measured_value`` is COUNTED as missing, never
    silently dropped — the never-raise contract the ฿ extraction already holds.
    """
    for entry in step.reasoning_trace or []:
        if entry.get("kind") != "verdict_computed":
            continue
        for label, n in (entry.get("counts") or {}).items():
            verdicts[label] = verdicts.get(label, 0) + n
    for entity in (step.artifact or {}).get("output_set", []):
        label = str(entity.get("verdict"))
        bucket = readings.setdefault(
            label, {"entity_count": 0, "readings": [], "readings_missing": 0}
        )
        bucket["entity_count"] += 1
        value = entity.get("measured_value")
        if isinstance(value, int):
            bucket["readings"].append(value)
        else:
            bucket["readings_missing"] += 1


def _tally_gate(
    spec: _RunSpec,
    step: _StepSpec,
    gates: dict[str, int],
    gate_approvers: dict[str, int],
    tier_outcomes: dict[tuple[str, str], dict[str, Any]],
) -> None:
    """Fold one resolved gate into the AC-7 tallies + the B2 tier x outcome tally.

    The approver is a ``gate_principal_recorded`` trace entry carrying a
    ``principal_id`` — the way ``resolve_gated_step`` actually records it, and
    deliberately **not** ``step_principals``, which holds the REQUESTER half (the
    AC-2 wording correction; see the seeding site).

    B2's tier comes from the ``governed_decision`` ARRAY in the step audit, and its
    outcome from the presence of an ``action_rejected`` trace entry — the only thing
    that distinguishes a reject, since the principal tie is recorded either way. The
    dwell half is the gate step's own ``duration_ms``: a SAME-ROW datum, the only
    kind S4 sanctions.

    Extracted rather than inlined for the same reason ``_tally_benefit`` and
    ``_tally_dwell`` are: the extra branches tip ``_expected``'s loop body past
    ruff's ``C901`` ceiling of 10.
    """
    if step.status != StepResultStatus.RESOLVED.value:
        return
    gates[spec.procedure_id] += 1
    trace = step.reasoning_trace or []
    if any(
        entry.get("kind") == "gate_principal_recorded" and entry.get("principal_id")
        for entry in trace
    ):
        gate_approvers[spec.procedure_id] += 1
    outcome = "rejected" if any(e.get("kind") == "action_rejected" for e in trace) else "approved"
    for decision in (step.audit or {}).get("governed_decision", []):
        control = decision.get("control_ref") or {}
        if control.get("kind") != "doa_tier":
            continue
        bucket = tier_outcomes.setdefault(
            (str(control.get("id")), outcome), {"gate_count": 0, "durations": []}
        )
        bucket["gate_count"] += 1
        bucket["durations"].append(step.duration_ms)


def _tally_run(
    spec: _RunSpec,
    run_status_counts: dict[tuple[str, str], int],
    run_duration_totals: dict[tuple[str, str], list[int]],
    week_counts: dict[str, int],
    trigger_outcomes: dict[tuple[str, str, str], int],
) -> None:
    """Fold one run into the Step-4.5 tallies (SD-9 (a2)) + the B4 trigger tally.

    Extracted rather than inlined for the reason ``_tally_gate`` was: extra
    branches in ``_expected``'s loop tip it past ruff's ``C901`` ceiling of 10.

    The week label must match Postgres ``date_trunc('week', …)``, which returns
    the **Monday** of the week — ``d - timedelta(days=d.weekday())``. Getting
    this wrong would make the oracle agree with a *different* bucketing than the
    SQL under test, which is the failure mode an independent oracle exists to
    prevent.
    """
    key = (spec.procedure_id, spec.status)
    run_status_counts[key] = run_status_counts.get(key, 0) + 1
    total = sum(step.duration_ms for step in spec.steps)
    run_duration_totals.setdefault(key, []).append(total)
    day = spec.started_at.date()
    monday = day - timedelta(days=day.weekday())
    week_counts[monday.isoformat()] = week_counts.get(monday.isoformat(), 0) + 1
    b4 = (spec.procedure_id, spec.trigger, spec.status)
    trigger_outcomes[b4] = trigger_outcomes.get(b4, 0) + 1


def _expected(specs: list[_RunSpec]) -> Corpus:
    status_counts: dict[str, int] = defaultdict(int)
    procedure_counts: dict[str, int] = defaultdict(int)
    period_counts: dict[str, int] = defaultdict(int)
    durations: dict[tuple[str, str], list[int]] = defaultdict(list)
    benefit: dict[tuple[str | None, str, str | None, str], dict[str, Any]] = {}
    refusals: dict[str, int] = defaultdict(int)
    gates: dict[str, int] = defaultdict(int)
    gate_approvers: dict[str, int] = defaultdict(int)
    verdicts: dict[str, int] = {}
    assumptions: set[str] = set()
    dwell: dict[str, dict[str, Any]] = {}
    step_row_count = 0

    run_status_counts: dict[tuple[str, str], int] = {}
    run_duration_totals: dict[tuple[str, str], list[int]] = {}
    week_counts: dict[str, int] = {}
    verdict_readings: dict[str, dict[str, Any]] = {}
    gate_tier_outcomes: dict[tuple[str, str], dict[str, Any]] = {}
    refusals_by_procedure: dict[tuple[str, str], int] = {}
    trigger_outcomes: dict[tuple[str, str, str], int] = {}

    for spec in specs:
        status_counts[spec.status] += 1
        procedure_counts[spec.procedure_id] += 1
        period_counts[spec.started_at.date().isoformat()] += 1
        _tally_run(spec, run_status_counts, run_duration_totals, week_counts, trigger_outcomes)
        if spec.status == PipelineRunStatus.WAITING_HUMAN.value:
            _tally_dwell(spec, dwell)
        for step in spec.steps:
            step_row_count += 1
            durations[(spec.procedure_id, step.step_id)].append(step.duration_ms)
            _tally_gate(spec, step, gates, gate_approvers, gate_tier_outcomes)
            _tally_verdict(step, verdicts, verdict_readings)
            for entry in step.reasoning_trace or []:
                kind = entry.get("kind")
                if kind == "economic_impact":
                    _tally_benefit(entry, spec, benefit, assumptions)
                elif kind == "read_refused":
                    _tally_refusal(entry, spec, refusals, refusals_by_procedure)

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
        verdicts=verdicts,
        run_status_counts=run_status_counts,
        run_duration_totals=run_duration_totals,
        week_counts=week_counts,
        verdict_readings=verdict_readings,
        gate_tier_outcomes=gate_tier_outcomes,
        refusals_by_procedure=refusals_by_procedure,
        trigger_outcomes=trigger_outcomes,
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
