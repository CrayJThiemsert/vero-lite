"""PLAN-0062 Step 3 (PR3) — the aquaculture production factory + full-procedure run (AC-4, AC-5).

The third OCT migration, and the one that tests the OTHER half of the ADR-016 D2-A3 split:
aquaculture's ``judge`` is an ``in_file_band`` (typed ``threshold``/``direction``/
``watch_margin`` on the Step), so its factory binds the SHIPPED ``EvaluateStepExecutor``
**unwrapped** — PR1b's ``EnvBandEvaluateExecutor`` is a choice for the env half, not a
funnel every vertical must pass through.

**Where the run actually stops.** ``_suspends`` is a function of the STEP, not of its
input set: ``aerate`` is a ``gated`` action, so the run suspends there on every pass. The
downstream ``escalate_watch`` (the ADR-0019 watch→gated proposal) and the ``auto``
``summary`` terminal are reachable only AFTER a human resolves that gate — via the
DB-backed ``resolve_gated_step`` resume path, which is out of this offline PR's frame
(SD-6). So these tests assert the watch band where it is genuinely observable in one
pass: on the ``judge`` step's verdict tags, and by its ABSENCE from ``aerate``'s
breach-only fan-out. Nothing here claims the escalation executed.

Offline and host-state-free (SD-6): synthetic/fixture adapters, deterministic band math,
stubbed advisory prose — no MS-S1 call anywhere (CLAUDE.md §8).
"""

from __future__ import annotations

from typing import Any

import pytest

from services.api.config import settings
from services.engine.discovery import discover_and_register
from services.engine.ontology_meta import load_ontology_meta
from services.engine.procedures.action_step import ActionStepExecutor
from services.engine.procedures.advisory_stub import advisory_stub_factory
from services.engine.procedures.env_band_step import EnvBandEvaluateExecutor
from services.engine.procedures.evaluate_step import EvaluateStepExecutor
from services.engine.procedures.orchestrator import run_procedure
from services.engine.procedures.query_step import QueryStepExecutor
from services.engine.procedures.runs import PipelineRunStatus
from services.engine.procedures.spec import Procedure, StepKind, load_procedures
from services.engine.registry import ExecutorFactory, RegistryError, registry
from verticals.aquaculture.data_adapter.synthetic import DO_CRASH_MG_L
from verticals.aquaculture.procedures_factory import register_aquaculture_procedure_executors

_VERTICAL = "aquaculture"
_PROCEDURE_ID = "morning_pond_health_round"
_CRASH_POND = "pond-07"


class _FixtureAdapter:
    """Duck-typed adapter: the query executor calls ``fetch_objects`` for the base
    OperationalEvent rows and (post-PLAN-0068 read_do join) the Pond band rows that
    carry each pond's ``do_floor`` — without Pond rows the inner join empties."""

    vertical_name = _VERTICAL

    def __init__(
        self, events: list[dict[str, Any]], ponds: list[dict[str, Any]] | None = None
    ) -> None:
        self._events = events
        self._ponds = ponds or []

    async def fetch_objects(self, object_type: str) -> list[dict[str, Any]]:
        source = {"OperationalEvent": self._events, "Pond": self._ponds}.get(object_type, [])
        return [dict(row) for row in source]


def _procedure() -> tuple[Procedure, Any]:
    spec = load_procedures(_VERTICAL)
    procedure = next(p for p in spec.procedures if p.procedure_id == _PROCEDURE_ID)
    agent = next(a for a in spec.agents if a.agent_id == procedure.run_by)
    return procedure, agent


def _executors_over(adapter: Any) -> dict[StepKind, Any]:
    """The factory's executor map, re-pointed at a fixture adapter (same classes)."""
    meta = load_ontology_meta(_VERTICAL)
    return {
        StepKind.QUERY: QueryStepExecutor(
            adapter=adapter,
            object_type_names=frozenset(t.name for t in meta.object_types),
            meta=meta,
        ),
        StepKind.EVALUATE: EvaluateStepExecutor(),
        StepKind.ACTION: ActionStepExecutor(client_factory=advisory_stub_factory),
    }


@pytest.fixture
async def aquaculture_factory(monkeypatch: pytest.MonkeyPatch) -> ExecutorFactory:
    """The registered aquaculture factory over a fixed (un-anchored) clock — the same
    registration path ``services/api/main.py`` runs at startup. No band env vars: the
    band is authored in the YAML."""
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    discover_and_register()  # adapters + handlers only (OQ-6) — no executor factory
    await register_aquaculture_procedure_executors()
    return registry.get_procedure_executors(_VERTICAL)


async def test_registration_is_required_then_idempotent() -> None:
    """``discover_and_register`` alone leaves the vertical without a factory (the 409 the
    resolve endpoint raises); registering twice is a no-op, never a RegistryError."""
    discover_and_register()
    with pytest.raises(RegistryError, match="no procedure-executor factory"):
        registry.get_procedure_executors(_VERTICAL)

    await register_aquaculture_procedure_executors()
    await register_aquaculture_procedure_executors()  # idempotent

    assert registry.get_procedure_executors(_VERTICAL) is not None


async def test_factory_binds_the_base_evaluate_executor_not_the_env_wrapper(
    aquaculture_factory: ExecutorFactory,
) -> None:
    """AC-5 + the ADR-016 D2-A3 split made executable: an ``in_file_band`` vertical binds
    the SHIPPED base evaluate executor directly. The env-band wrapper must NOT appear —
    it is the ``env`` half, not a default every factory funnels through."""
    executors = aquaculture_factory()

    # PLAN-0078 Step 1: TRANSFORM joins the exact key set (shared fieldless executor, all 4
    # factories, pure-additive — inert until a procedure declares a transform).
    assert set(executors) == {
        StepKind.QUERY,
        StepKind.EVALUATE,
        StepKind.ACTION,
        StepKind.TRANSFORM,
    }
    query = executors[StepKind.QUERY]
    assert isinstance(query, QueryStepExecutor)
    assert query.meta is not None
    assert "Pond" in query.object_type_names

    evaluate = executors[StepKind.EVALUATE]
    assert isinstance(evaluate, EvaluateStepExecutor)
    assert not isinstance(evaluate, EnvBandEvaluateExecutor)

    assert aquaculture_factory()[StepKind.QUERY] is not query, "executors are per-request"


async def test_full_procedure_run_suspends_at_the_gated_aerate(
    aquaculture_factory: ExecutorFactory,
) -> None:
    """AC-4 (the full-run half): read_do -> judge -> aerate over the REAL aquaculture YAML
    + ontology + synthetic adapter. The run suspends at ``waiting_human``; the gated
    aerator is PROPOSED, never executed. The migrated per-species grammar decides each
    verdict — pond-07's 4.6 mg/L watch reading is superseded by its 3.2 mg/L crash
    (breach vs its 4.0 floor), and pond-11's 4.2 mg/L flip breaches its OWN 4.5
    tiger-prawn floor (a `watch` a blanket 4.0 would have missed), so the breach set
    is {pond-07, pond-11} (PLAN-0068 SD-3)."""
    procedure, agent = _procedure()

    result = await run_procedure(
        procedure, agent, aquaculture_factory(), vertical=_VERTICAL, run_id="aq-pr3-e2e"
    )

    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    by_step = {step.step_id: step for step in result.step_results}
    # escalate_watch + summary are POST-RESUME (aerate is a gated action -> _suspends)
    assert set(by_step) == {"read_do", "judge", "aerate"}

    readings = by_step["read_do"].artifact["output_set"]
    assert all(row["event_type"] == "reading" for row in readings)
    assert all("measured_value" in row for row in readings), "an alarm row would break the judge"

    judged = by_step["judge"].artifact["output_set"]
    crash = next(row for row in judged if row["pond_id"] == _CRASH_POND)
    assert crash["measured_value"] == DO_CRASH_MG_L
    assert crash["verdict"] == "breach", "the 3.2 crash must not be downgraded to the 4.6 watch"

    # the band came from the YAML, not the environment (in_file_band); PLAN-0068
    # migrated it to the per-entity `threshold_field: do_floor`, so the scalar
    # `threshold` is None and the audit names the per-entity column instead.
    judge_audit = by_step["judge"].audit
    assert judge_audit["threshold"] is None
    assert judge_audit["threshold_field"] == "do_floor"
    assert judge_audit["direction"] == "below"
    assert judge_audit["watch_margin"] == 1.0
    assert "band_source" not in judge_audit

    # PLAN-0068 SD-3: pond-11's 4.2 flip breaches its OWN 4.5 tiger-prawn floor, so the
    # breach set grows to {pond-07, pond-11} and the gated aerate fans out over both.
    breached = {row["pond_id"] for row in judged if row["verdict"] == "breach"}
    assert breached == {"pond-07", "pond-11"}
    actions = by_step["aerate"].artifact["output_set"]
    assert len(actions) == 2
    assert all(a["status"] == "proposed" for a in actions)
    assert all(a["action"]["suggested_handler"] == "start_emergency_aerator" for a in actions)


async def test_three_band_judge_and_breach_only_fan_out_over_the_migrated_grammar() -> None:
    """AC-4's three-band half, in situ. A fixture pond set lands one reading in each band;
    the migrated grammar feeds the judge, which tags breach / watch / ok, and ``aerate``'s
    ``where: {verdict: breach}`` fan-out proposes for the breach pond ONLY. The watch pond
    is judged but NOT aerated — its escalation waits behind the gate."""
    discover_and_register()
    events = [
        # breach: 3.5 < 4.0 floor
        {
            "event_id": "e-breach",
            "event_type": "reading",
            "measured_value": 3.5,
            "occurred_at": "2026-06-02T02:00:00Z",
            "pond_id": "pond-breach",
        },
        # watch: 4.0 < 4.5 <= 5.0 (floor + watch_margin)
        {
            "event_id": "e-watch",
            "event_type": "reading",
            "measured_value": 4.5,
            "occurred_at": "2026-06-02T02:00:00Z",
            "pond_id": "pond-watch",
        },
        # ok: 6.2 > 5.0
        {
            "event_id": "e-ok",
            "event_type": "reading",
            "measured_value": 6.2,
            "occurred_at": "2026-06-02T02:00:00Z",
            "pond_id": "pond-ok",
        },
    ]
    # PLAN-0068: each pond carries its OWN do_floor (joined onto the reading by read_do).
    # Uniform 4.0 here isolates the three-band math; the per-species "same reading, two
    # verdicts" point is pinned in test_pond_per_species_floor.py.
    ponds = [
        {
            "pond_id": "pond-breach",
            "do_floor": 4.0,
            "species": "whiteleg_shrimp",
            "site_id": "farm-x",
        },
        {
            "pond_id": "pond-watch",
            "do_floor": 4.0,
            "species": "whiteleg_shrimp",
            "site_id": "farm-x",
        },
        {"pond_id": "pond-ok", "do_floor": 4.0, "species": "whiteleg_shrimp", "site_id": "farm-x"},
    ]
    procedure, agent = _procedure()

    result = await run_procedure(
        procedure,
        agent,
        _executors_over(_FixtureAdapter(events, ponds)),
        vertical=_VERTICAL,
        run_id="aq-pr3-three-band",
    )

    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    by_step = {step.step_id: step for step in result.step_results}
    judged = {row["pond_id"]: row["verdict"] for row in by_step["judge"].artifact["output_set"]}
    assert judged == {"pond-breach": "breach", "pond-watch": "watch", "pond-ok": "ok"}

    proposed = by_step["aerate"].artifact["output_set"]
    assert len(proposed) == 1, "only the breach subset reaches the gated aerator"
    assert proposed[0]["action"]["affected_entities"][0]["primary_key"] == "e-breach"
