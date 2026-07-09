"""PLAN-0062 Step 1 (AC-1, AC-2): the shared run-semantics **parity** harness +
the energy ``read_readings`` migration parity, over the REAL energy ontology.

The SD-C guard, made executable: a declared join/projection-grammar query step
run through the production ``run_procedure`` path must produce the SAME output
set as an INDEPENDENT, hand-coded reference of the intended seed semantics on
the same fixture — order-insensitive, key-complete, **zero tolerance**. The
reference is coded here from the SD-5 contract (argmax ``order_by`` per group,
ties broken by max ``tie_break``, rows missing either field excluded), NOT by
calling the executor's own ``_latest_per_group`` — so the grammar and the
reference can only agree by computing the same semantics.

Deterministic, offline, no LLM anywhere (LOCKED-6 / SD-6): no MS-S1, no DB.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from services.engine.ontology_meta import load_ontology_meta
from services.engine.procedures.orchestrator import (
    run_procedure,
    validate_read_bindings_for_vertical,
)
from services.engine.procedures.query_step import QueryStepExecutor
from services.engine.procedures.runs import PipelineRunStatus
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    Procedure,
    Step,
    StepInput,
    StepKind,
    load_procedures,
)
from verticals.energy.data_adapter.synthetic import operational_events

# The energy ``read_readings`` migration (mirrors verticals/energy/procedures.yaml
# after PLAN-0062): latest OperationalEvent (event_type=reading) per Asset via the
# declared ``event_emitted_by_asset`` link, by ``occurred_at``.
_ENERGY_READ_INPUT: dict[str, Any] = {
    "reads": ["OperationalEvent"],
    "where": {"event_type": "reading"},
    "project": {"latest_per": "event_emitted_by_asset", "order_by": "occurred_at"},
}
# Resolved by the executor from the ontology: group_by = the FK from_property
# (OperationalEvent.asset_id), tie_break = the base type's primary_key (event_id).
_GROUP_KEY = "asset_id"
_ORDER_BY = "occurred_at"
_TIE_BREAK = "event_id"


class _FakeAdapter:
    """Duck-typed adapter: the executor only calls ``fetch_objects``."""

    def __init__(self, data: dict[str, list[dict[str, Any]]]) -> None:
        self.vertical_name = "energy"
        self._data = data

    async def fetch_objects(self, object_type: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self._data.get(object_type, [])]


def _agent() -> Agent:
    return Agent(
        agent_id="parity_agent",
        name="Parity Agent",
        autonomy_ceiling=Autonomy.GATED,
        allowed=AgentAllowed(),  # unconstrained reads (OQ-6)
    )


def _read_step_procedure(step_input: dict[str, Any]) -> Procedure:
    return Procedure(
        procedure_id="parity-read-round",
        title="Parity read round",
        goal="Exercise a declared latest-per-group read for the SD-C parity guard.",
        run_by="parity_agent",
        steps=[
            Step(
                step_id="read",
                name="Declared latest-per-group read",
                kind=StepKind.QUERY,
                input=StepInput.model_validate(step_input),
            )
        ],
    )


def _reference_latest_per_group(
    rows: list[dict[str, Any]],
    *,
    where: dict[str, Any],
    group_key: str,
    order_by: str,
    tie_break: str,
) -> dict[Any, dict[str, Any]]:
    """The INDEPENDENT reference — the SD-5 semantics coded by hand (not the executor).

    Base ``where`` (field-equality, all keys) pre-filters; then argmax ``order_by``
    per ``group_key``, ties broken by max ``str(tie_break)``; rows missing the group
    key or the order field are excluded. Returns ``group_key -> winning row``.
    """
    filtered = [r for r in rows if all(r.get(k) == v for k, v in where.items())]
    best: dict[Any, dict[str, Any]] = {}
    for row in filtered:
        group = row.get(group_key)
        order_value = row.get(order_by)
        if group is None or order_value is None:
            continue
        current = best.get(group)
        if current is None:
            best[group] = row
        elif order_value > current[order_by]:
            best[group] = row
        elif order_value == current[order_by] and str(row.get(tie_break, "")) > str(
            current.get(tie_break, "")
        ):
            best[group] = row
    return best


async def assert_read_step_parity(
    step_input: dict[str, Any],
    data: dict[str, list[dict[str, Any]]],
    *,
    where: dict[str, Any],
    group_key: str,
    order_by: str,
    tie_break: str,
) -> dict[Any, dict[str, Any]]:
    """Run ``step_input`` through the production ``run_procedure`` path over the real
    energy ontology + ``data``, and assert its output == the independent reference
    (order-insensitive, key-complete, identical rows). Returns the reference for
    edge-specific follow-up assertions."""
    meta = load_ontology_meta("energy")  # the REAL shipped ontology, read-only
    executors = {
        StepKind.QUERY: QueryStepExecutor(
            adapter=_FakeAdapter(data),
            object_type_names=frozenset(t.name for t in meta.object_types),
            meta=meta,
        )
    }
    result = await run_procedure(
        _read_step_procedure(step_input),
        _agent(),
        executors,
        vertical="energy",
        run_id="parity-read",
    )
    assert result.run.status == PipelineRunStatus.COMPLETED.value
    artifact = result.step_results[-1].artifact
    assert artifact is not None
    got = artifact["output_set"]
    reference = _reference_latest_per_group(
        data[step_input["reads"][0]],
        where=where,
        group_key=group_key,
        order_by=order_by,
        tie_break=tie_break,
    )
    got_by_group = {row[group_key]: row for row in got}
    assert set(got_by_group) == set(reference)  # key-complete
    assert got_by_group == reference  # identical rows, zero tolerance
    return reference


# --------------------------------------------------------------------------- #
# AC-1 — the harness on SD-5 determinism edges (hand-authored fixture)
# --------------------------------------------------------------------------- #


async def test_energy_read_readings_parity_sd5_edges() -> None:
    """Multiple readings per group, an order-by tie (primary-key tie-break), a
    missing-group-key row and a missing-order row (both excluded), and a
    non-reading event filtered out by ``where`` — grammar == reference."""
    data = {
        "OperationalEvent": [
            # asset-01: three readings — latest by occurred_at is evt-a3 (08:10)
            {
                "event_id": "evt-a1",
                "event_type": "reading",
                "measured_value": 32.4,
                "occurred_at": "2026-05-21T08:00:00Z",
                "asset_id": "asset-01",
            },
            {
                "event_id": "evt-a2",
                "event_type": "reading",
                "measured_value": 61.5,
                "occurred_at": "2026-05-21T08:07:00Z",
                "asset_id": "asset-01",
            },
            {
                "event_id": "evt-a3",
                "event_type": "reading",
                "measured_value": 96.5,
                "occurred_at": "2026-05-21T08:10:00Z",
                "asset_id": "asset-01",
            },
            # asset-02: an order-by TIE at 08:05 — tie-break picks max event_id (evt-b2)
            {
                "event_id": "evt-b1",
                "event_type": "reading",
                "measured_value": 40.0,
                "occurred_at": "2026-05-21T08:05:00Z",
                "asset_id": "asset-02",
            },
            {
                "event_id": "evt-b2",
                "event_type": "reading",
                "measured_value": 41.7,
                "occurred_at": "2026-05-21T08:05:00Z",
                "asset_id": "asset-02",
            },
            # a non-reading event on asset-01 — filtered out by where before grouping
            {
                "event_id": "evt-x1",
                "event_type": "alarm",
                "occurred_at": "2026-05-21T09:00:00Z",
                "asset_id": "asset-01",
            },
            # missing group key (no asset_id) — excluded, never guessed
            {
                "event_id": "evt-miss-key",
                "event_type": "reading",
                "measured_value": 1.0,
                "occurred_at": "2026-05-21T09:30:00Z",
            },
            # missing order field (no occurred_at) — excluded
            {
                "event_id": "evt-miss-order",
                "event_type": "reading",
                "measured_value": 2.0,
                "asset_id": "asset-03",
            },
        ]
    }
    reference = await assert_read_step_parity(
        _ENERGY_READ_INPUT,
        data,
        where={"event_type": "reading"},
        group_key=_GROUP_KEY,
        order_by=_ORDER_BY,
        tie_break=_TIE_BREAK,
    )
    # explicit edge assertions (belt-and-suspenders on top of the parity equality)
    assert set(reference) == {"asset-01", "asset-02"}  # asset-03 excluded (missing order)
    assert reference["asset-01"]["event_id"] == "evt-a3"  # latest reading, not the alarm
    assert reference["asset-02"]["event_id"] == "evt-b2"  # order-by tie -> max event_id


# --------------------------------------------------------------------------- #
# AC-2 — parity over the REAL energy synthetic data
# --------------------------------------------------------------------------- #


async def test_energy_read_readings_parity_real_synthetic_data() -> None:
    """The declared grammar over the REAL ``operational_events()`` synthetic set
    (JSON-safed exactly as the executor coerces at the adapter boundary) equals the
    reference: one latest reading per asset, non-reading events (transition/alarm)
    filtered out."""
    events = json.loads(json.dumps(operational_events(), default=str))
    data = {"OperationalEvent": events}
    reference = await assert_read_step_parity(
        _ENERGY_READ_INPUT,
        data,
        where={"event_type": "reading"},
        group_key=_GROUP_KEY,
        order_by=_ORDER_BY,
        tie_break=_TIE_BREAK,
    )
    # the incident asset's latest reading is the over-temperature breach (event-reading-03)
    assert reference["asset-battery-01"]["event_id"] == "event-reading-03"
    # every kept row is a reading (the where filter held), one per asset
    assert all(row["event_type"] == "reading" for row in reference.values())
    assert len(reference) == len(
        {e["asset_id"] for e in events if e.get("event_type") == "reading" and e.get("asset_id")}
    )


# --------------------------------------------------------------------------- #
# AC-2 — the shipped-YAML load-gate pin (the migration must resolve; no regression)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("vertical", ["energy", "supply_chain", "aquaculture", "procurement"])
def test_all_shipped_procedures_pass_read_binding_gate(vertical: str) -> None:
    """Every shipped procedure passes the ADR-016 Q3/Q4 load gate
    (:func:`validate_read_bindings_for_vertical`): the energy ``read_readings``
    migration's declared ``reads``/``project`` must resolve against the REAL energy
    ontology (link + FK + latest_per), and no other vertical regressed. A
    reads-absent procedure is a no-op (never loads the ontology); a declaring one
    resolves or the gate raises — this pins the migration honest at load time."""
    vertical_procedures = load_procedures(vertical)
    agents_by_id = {agent.agent_id: agent for agent in vertical_procedures.agents}
    for procedure in vertical_procedures.procedures:
        agent = agents_by_id[procedure.run_by]
        validate_read_bindings_for_vertical(procedure, agent, vertical)  # raises on any violation
