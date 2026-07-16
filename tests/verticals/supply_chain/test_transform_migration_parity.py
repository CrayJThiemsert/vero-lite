"""PLAN-0078 PR-2 (AC-3, AC-4, AC-5, AC-6): the supply_chain intake seed-migration parity harness.

**Oracle-first** (PLAN-0077 SD-5 / Lesson #0026): a hand-coded FROZEN reference of the CURRENT
enriched disposition intake row + the downstream governed verdicts, asserted byte-equal against
the production factory run. Green against the pre-flip world (the ``_intake_seed`` still emits
``excursion_magnitude_c`` / ``excursion_duration_h`` / ``stability_budget_ch`` / ``compliance``)
in one commit, and stays green UNCHANGED after the flip moves those into a declared ``enrich``
transform between ``intake`` and ``assess`` — byte-equal or the flip does not land (L-2).

The reference is hand-coded from the cold-chain demo contract (not by calling ``_intake_seed``),
so slimming the seed cannot silently drift it (the PLAN-0062 property).

**Flip-robust anchor.** The enriched row is asserted at the step FEEDING ``assess`` — read from
``assess.input.from_step`` — which is ``intake`` pre-flip and ``enrich`` post-flip. The SAME
assertion holds across the flip: the row reaching ``assess`` (where the severity stamp reads its
scalars) is byte-identical to the frozen reference either way.

**Phase-1 tier** (L-2): FULL byte parity incl. the run record — the enriched row + the severity
STAMP (which PR-2 leaves in the ``assess`` executor, Phase 2 territory) reading the enrich's
scalars identically (magnitude 6.6 → ratio 2.475 → CRITICAL), the scored_rule lane selection, the
GDP rule_gate, the severity_tier routing (ผอ.ฝ่ายคุณภาพ / appr-qdir), and the run status.

Deterministic, offline, no MS-S1, no DB (the synthetic adapter + the registered factory).
"""

from __future__ import annotations

from typing import Any

import pytest

from services.api.config import settings
from services.engine.discovery import discover_and_register
from services.engine.procedures.governance_pin import (
    build_governance_snapshot,
    compute_governance_hash,
)
from services.engine.procedures.orchestrator import RunContext, RunResult, run_procedure
from services.engine.procedures.runs import PipelineRunStatus, StepResultStatus
from services.engine.procedures.spec import Agent, AgentAllowed, Autonomy, load_procedures
from services.engine.procedures.transform_step import TransformRefusal, TransformStepExecutor
from services.engine.registry import ExecutorFactory, registry
from verticals.supply_chain.procedures_factory import register_supply_chain_procedure_executors

_VERTICAL = "supply_chain"
_PROC = "cold_chain_excursion_disposition"
_COLD_CHAIN_CEILING = 8.0

# The FROZEN reference: the CURRENT enriched disposition intake row as it feeds ``assess`` (JSONB-
# safe forms exactly as the registered factory json-safes its seed). Hand-coded from the cold-chain
# demo contract; the four MIGRATED fields are marked.
_FROZEN_ENRICHED_INTAKE: dict[str, Any] = {
    "shipment_id": "shipment-pharma-01",
    "batch_id": "Vaccine Lot VX-1188",
    "cargo_type": "pharma",
    "facility_id": "facility-coldhub-01",
    "temp_ceiling": "8.0",
    "reading_c": "14.6",
    "event_id": "event-reading-03",
    # MIGRATED: derive sub(reading_c, temp_ceiling) then coerce->string (14.6 - 8.0 = 6.6)
    "excursion_magnitude_c": "6.6",
    "excursion_duration_h": 9,  # MIGRATED: default (authored)
    "stability_budget_ch": 24,  # MIGRATED: default (authored)
    "qty": "420.0",
    "currency": "THB",
    "candidate_quotes": [
        {
            "quote_id": "lane-quarantine-rework",
            "supplier_id": "reworker-bkk-01",
            "unit_price": "60.00",
            "currency": "THB",
            "lead_time_days": 21,
            "on_contract": True,
        },
        {
            "quote_id": "lane-licensed-destruction",
            "supplier_id": "disposal-licensed-01",
            "unit_price": "150.00",
            "currency": "THB",
            "lead_time_days": 3,
            "on_contract": True,
        },
    ],
    "quarantine_status": "quarantined",
    "compliance": {  # MIGRATED: default(object) — the GDP rule_gate signal map
        "stability_budget": True,
        "batch_quarantine": True,
        "licensed_disposal_vendor": True,
        "coa_customs": True,
    },
}


@pytest.fixture
async def supply_chain_factory(monkeypatch: pytest.MonkeyPatch) -> ExecutorFactory:
    """The registered supply_chain factory — the same registration path ``services/api/main.py``
    runs at startup (the disposition and the sweep share it)."""
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    monkeypatch.setattr(settings, "oct_recommend_threshold", _COLD_CHAIN_CEILING)
    monkeypatch.setattr(settings, "oct_recommend_direction", "above")
    discover_and_register()
    await register_supply_chain_procedure_executors()
    return registry.get_procedure_executors(_VERTICAL)


async def _run_disposition(factory: ExecutorFactory) -> RunResult:
    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == _PROC)
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    return await run_procedure(proc, agent, factory(), vertical=_VERTICAL, run_id="pr2-parity")


async def test_disposition_intake_enrichment_and_verdicts_parity(
    supply_chain_factory: ExecutorFactory,
) -> None:
    """AC-3: the enriched disposition intake row + every downstream governed verdict is byte-equal
    to the frozen pre-flip reference. Proven against the CURRENT (seed-emitted) world in this
    commit; unchanged after the ``enrich`` flip."""
    result = await _run_disposition(supply_chain_factory)
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    by_step = {s.step_id: s for s in result.step_results}

    # (1) the enriched intake row at the step FEEDING assess — flip-robust (intake -> enrich).
    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == _PROC)
    assess_step = next(s for s in proc.steps if s.step_id == "assess")
    assert assess_step.input is not None and assess_step.input.from_step is not None
    feeder_artifact = by_step[assess_step.input.from_step].artifact
    assert feeder_artifact is not None
    [feeder_row] = feeder_artifact["output_set"]
    # Every Phase-1 field, byte-equal. Asserted per-field rather than as whole-row equality:
    # PLAN-0078 PR-3 legitimately ADDS derived fields to this row (the severity + the OQ-5
    # `dose_ch`/`ratio`), which the ratified SD-1 (B) is precisely the decision to do. AC-7(i)
    # states the Phase-2 bar in exactly these per-field terms ("output-row byte parity on
    # excursion_severity + criticality and every Phase-1 field"), so this is the same bar, not a
    # relaxed one — what is dropped is only "and nothing else", which (B) makes false by design.
    # The added fields have their own frozen reference in `test_severity_transform_parity.py`.
    assert {k: feeder_row[k] for k in _FROZEN_ENRICHED_INTAKE} == _FROZEN_ENRICHED_INTAKE

    # (2) the enrich's scalars still dose to the same severity: magnitude 6.6, dose 59.4,
    # ratio 2.475 -> CRITICAL. This is the Phase-1 concern the assertion was always making — the
    # enriched magnitude is right BECAUSE it doses to this — so it survives PR-3 by following the
    # values to their new home. PR-2 read them from the assess executor's `severity_derivation`
    # audit projection and labelled that "Phase 2 territory"; PR-3 arrived, and the declared
    # transform now derives them onto the ROW (the executor slimmed to its scalar guard, SD-7).
    # Authoritative Phase-2 coverage — byte parity + the SD-6 two-tier bar + the OQ-5 value-level
    # provenance contract — lives in `test_severity_transform_parity.py`; this stays a Phase-1
    # sanity tie so a magnitude drift cannot pass here and fail only there.
    assess_artifact = by_step["assess"].artifact
    assert assess_artifact is not None
    [assessed] = assess_artifact["output_set"]
    assert assessed["excursion_magnitude_c"] == "6.6"
    assert assessed["dose_ch"] == "59.4"
    assert assessed["ratio"] == "2.475"
    assert assessed["excursion_severity"] == "critical"

    assess_audit = by_step["assess"].audit
    assert assess_audit is not None

    # (3) scored_rule: the RULE selected the licensed-destruction lane (governed != generated)
    [scored] = assess_audit["scored_rule"]
    assert scored["selected_quote_id"] == "lane-licensed-destruction"
    assert scored["amount"] == {"value": "63000.000", "currency": "THB"}
    assert scored["source_path"] == "default_source"
    assert scored["override_required"] is False

    # (4) gdp_gate: every GDP criterion cleared (a failed one would block the disposition)
    gdp_audit = by_step["gdp_gate"].audit
    assert gdp_audit is not None
    [compliance] = gdp_audit["rule_gate"]
    assert compliance["compliant"] is True
    assert compliance["failed_criteria"] == []

    # (5) severity_tier: CRITICAL routes to the top quality authority (money never routes it)
    approve_audit = by_step["approve"].audit
    assert approve_audit is not None
    [verdict] = approve_audit["severity_tier"]
    assert verdict["severity"] == "critical"
    assert verdict["required_role"] == "ผอ.ฝ่ายคุณภาพ"
    assert verdict["resolved_approver_id"] == "appr-qdir"
    assert verdict["sod_required"] is True

    # (6) the run parks at the human gate; fulfill never ran
    assert by_step["intake"].status == StepResultStatus.COMPLETE.value
    assert by_step["assess"].status == StepResultStatus.COMPLETE.value
    assert by_step["gdp_gate"].status == StepResultStatus.COMPLETE.value
    assert by_step["approve"].status == StepResultStatus.WAITING_HUMAN.value
    assert "fulfill" not in by_step


async def test_enrich_transform_fails_closed_on_missing_source_field() -> None:
    """AC-4: a missing derive source on the migrated ``enrich`` transform refuses the WHOLE step
    typed (PLAN-0077 SD-7 fail-closed) — it never silently emits a row with no
    ``excursion_magnitude_c`` that would fail-DANGEROUS at the severity stamp. Demonstrated by
    running the SHIPPED ``enrich`` step's executor on a row dropping ``reading_c`` (the
    ``sub``-derive's source)."""
    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == _PROC)
    enrich_step = next(s for s in proc.steps if s.step_id == "enrich")
    agent = Agent(agent_id="t", name="t", autonomy_ceiling=Autonomy.GATED, allowed=AgentAllowed())
    ctx = RunContext(agent=agent, vertical=_VERTICAL)
    bad_row = {k: v for k, v in _FROZEN_ENRICHED_INTAKE.items() if k != "reading_c"}
    with pytest.raises(TransformRefusal):
        await TransformStepExecutor().execute(enrich_step, [bad_row], ctx)


def test_enrich_transform_pinned_sweep_byte_identical() -> None:
    """AC-5 / AC-6: the disposition's governance snapshot carries the declared ``enrich`` transform
    canonically — it is part of the config hash, so a mid-flight transform edit changes the hash
    and fails CLOSED at resume (``governance_pin.py:96-98``). The ``cold_chain_excursion_sweep``
    (no transform) pins with NO ``transform`` key — byte-identical to before the migration."""
    spec = load_procedures(_VERTICAL)
    by_id = {p.procedure_id: p for p in spec.procedures}

    # AC-5: the disposition's enrich transform is present + contributes to the config hash
    disposition = by_id[_PROC]
    snapshot = build_governance_snapshot(disposition)
    [enrich_snap] = [s for s in snapshot["steps"] if s["step_id"] == "enrich"]
    assert enrich_snap["transform"] is not None
    assert enrich_snap["transform"]["ops"]  # the ops are pinned canonically

    stripped_steps = [
        s.model_copy(update={"transform": None}) if s.step_id == "enrich" else s
        for s in disposition.steps
    ]
    stripped = disposition.model_copy(update={"steps": stripped_steps})
    assert compute_governance_hash(snapshot) != compute_governance_hash(
        build_governance_snapshot(stripped)
    )

    # AC-6: the sweep declares no transform -> no `transform` key on any step (byte-identical)
    sweep_snapshot = build_governance_snapshot(by_id["cold_chain_excursion_sweep"])
    assert all("transform" not in step for step in sweep_snapshot["steps"])
