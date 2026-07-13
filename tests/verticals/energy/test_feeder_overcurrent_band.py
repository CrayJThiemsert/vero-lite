"""PLAN-0070 — the energy over-current re-theme end-to-end (AC-2 flip + AC-6 in-memory run).

The migrated ``substation_health_sweep`` bands each feeder's latest CURRENT (ampere)
reading against its OWN ``Asset.rated_current_a`` (joined via ``event_emitted_by_asset``),
instead of the blanket over-temperature ``env_band``. The demo-visible flip: Feeder Meter A
at 84 A is ``ok`` under the old blanket env 90 band but ``breach`` at 105% of its OWN 80 A
rating (the missed-overload class — s121's frozen-cargo / s123's tiger-prawn analog).

Offline and host-state-free (CLAUDE.md §8): the QUERY step reads the synthetic adapter, the
EVALUATE step is deterministic per-row band math delegated through the env-band wrapper (the
guard passes a ``threshold_field`` judge through untouched, #709), the ACTION step's advisory
prose is stubbed — no MS-S1 call. Mirrors ``test_energy_procedure_factory.py``'s full run.
"""

from __future__ import annotations

import pytest

from services.api.config import settings
from services.engine.discovery import discover_and_register
from services.engine.procedures.orchestrator import run_procedure
from services.engine.procedures.runs import PipelineRunStatus
from services.engine.procedures.spec import load_procedures
from services.engine.registry import ExecutorFactory, registry
from verticals.energy.procedures_factory import register_energy_procedure_executors

_VERTICAL = "energy"
_PROCEDURE_ID = "substation_health_sweep"
_OVERLOADED_FEEDER = "asset-meter-01"  # 84 A latest reading vs its OWN 80 A rating → breach


@pytest.fixture
async def energy_factory(monkeypatch: pytest.MonkeyPatch) -> ExecutorFactory:
    """The registered energy factory over a fixed (un-anchored) clock + the pinned env band
    (kept ONLY to prove the per-feeder verdict is independent of the blanket env threshold —
    the migrated judge no longer reads it)."""
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    monkeypatch.setattr(settings, "oct_recommend_threshold", 90.0)
    monkeypatch.setattr(settings, "oct_recommend_direction", "above")
    discover_and_register()
    await register_energy_procedure_executors()
    return registry.get_procedure_executors(_VERTICAL)


async def test_overcurrent_run_bands_each_feeder_vs_its_own_rating(
    energy_factory: ExecutorFactory,
) -> None:
    """AC-2 / AC-6: the narrowed current read feeds the per-feeder judge in situ; the feeder
    meter breaches its OWN 80 A rating while the inverter stays under its 722 A rating, and the
    run suspends at the gated restart (a machine never restarts the feeder — human go/no-go)."""
    spec = load_procedures(_VERTICAL)
    procedure = next(p for p in spec.procedures if p.procedure_id == _PROCEDURE_ID)
    agent = next(a for a in spec.agents if a.agent_id == procedure.run_by)

    result = await run_procedure(
        procedure, agent, energy_factory(), vertical=_VERTICAL, run_id="energy-plan0070-e2e"
    )

    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    by_step = {step.step_id: step for step in result.step_results}
    assert set(by_step) == {"read_readings", "judge", "restart_breaches"}

    # The narrowing where kept only the CURRENT (ampere) readings — one latest per feeder.
    readings = by_step["read_readings"].artifact["output_set"]
    assert readings, "the declared current-narrowed read produced no rows"
    assert all(row["measured_kind"] == "current" for row in readings)
    assert {row["asset_id"] for row in readings} == {"asset-inverter-01", "asset-meter-01"}
    # each row carries its Asset's rated_current_a joined on (FK-parent join)
    assert all("rated_current_a" in row for row in readings)

    # The per-feeder verdict: only the meter (84 A > its own 80 A) breaches; the inverter
    # (61 A < its own 722 A) is ok — the flip a blanket 90 A band would MISS.
    judged = by_step["judge"].artifact["output_set"]
    assert {row["asset_id"] for row in judged} == {row["asset_id"] for row in readings}
    breaches = [row for row in judged if row["verdict"] == "breach"]
    assert [row["asset_id"] for row in breaches] == [_OVERLOADED_FEEDER]

    # The verdict came from the per-entity (in_file) band, NOT the blanket env threshold:
    # the migrated judge records its threshold_field and carries NO band_source="env" stamp.
    judge_audit = by_step["judge"].audit
    assert judge_audit.get("threshold_field") == "rated_current_a"
    assert judge_audit.get("band_source") != "env"

    # The gated restart fanned out over the breach subset ONLY, and proposed (not executed).
    actions = by_step["restart_breaches"].artifact["output_set"]
    assert len(actions) == 1
    assert actions[0]["status"] == "proposed"
    assert actions[0]["action"]["suggested_handler"] == "restart"
