"""PLAN-0078 PR-1 (AC-2, AC-4, AC-5): the procurement intake seed-migration parity harness.

**Oracle-first** (PLAN-0077 SD-5 two-commit discipline / Lesson #0026): a hand-coded FROZEN
reference of the CURRENT enriched intake row + the downstream governed verdicts, asserted
byte-equal against the production factory run. This module lands GREEN against the pre-flip
world (the ``_intake_seed`` still emits ``criticality`` / ``unit`` / ``compliance``) in one
commit, and stays green UNCHANGED after the flip commit moves those three fields into a
declared ``enrich`` transform between ``intake`` and ``judge`` — so the migration is proven
byte-equal or it does not land (L-2).

The reference is hand-coded from the seed CONTRACT (the exact demo-grade Fastenal values), NOT
by calling ``_intake_seed`` — so slimming the seed cannot silently drift it (the
``test_seed_migration_parity`` PLAN-0062 property).

**Flip-robust anchor.** The enriched row is asserted where it THREADS DOWNSTREAM — the ``judge``
step's output (the input row + its ``verdict``), not the ``intake`` step's output. Pre-flip the
seed emits the enriched fields at ``intake``; post-flip the ``enrich`` transform emits them one
step later — either way the row REACHING ``judge`` is byte-identical to the frozen reference.

**Phase-1 tier** (L-2): FULL byte parity incl. the run record — the enriched row, every governed
verdict (judge band, scored_rule selection + amount, rule_gate, doa_tier), the resolved tier /
approver, and the run status. The three intake-bearing procedures share ``_intake_seed`` (the
manual hero, the scheduled sibling, and the event-triggered sibling), so all three must migrate
in lockstep — the parametrization proves each still produces the identical enriched row + verdicts.

Deterministic, offline, no MS-S1, no DB (the in-memory ``run_procedure`` path).
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from services.engine.procedures.governance_pin import (
    build_governance_snapshot,
    compute_governance_hash,
)
from services.engine.procedures.orchestrator import RunResult, run_procedure
from services.engine.procedures.runs import PipelineRunStatus, StepResultStatus
from services.engine.procedures.spec import load_procedures
from verticals.procurement.data_adapter.fastenal_csv import FastenalCsvAdapter
from verticals.procurement.hero_demo.run import (
    _ensure_handlers,
    _executors,
    _intake_seed,
    advisory_stub_factory,
)

_VERTICAL = "procurement"

# The three procedures whose ``intake`` step is served by ``_intake_seed`` (via the ``_SeedQuery``
# fallback leg). All three share the ONE seed, so the migration flips them in lockstep. The two
# reorder procedures (`low_stock_reorder_round` / `scheduled_low_stock_reorder_round`) read the
# declared `read_stock` query, NOT the intake seed, so they are untouched by this PR.
_INTAKE_PROCEDURES = [
    "emergency_sourcing_round",
    "scheduled_emergency_sourcing_round",
    "event_emergency_sourcing_round",
]

# The FROZEN reference: the CURRENT enriched intake row as it threads into ``judge`` (JSONB-safe
# string forms exactly as a persisted run forces — the production factory json-safes its seed).
# Hand-coded from the Fastenal demo contract; the three MIGRATED fields are marked.
_FROZEN_ENRICHED_INTAKE: dict[str, Any] = {
    "event_id": "EVT-CNC-014-FAIL",
    "event_type": "failure",
    "object_type": "PurchaseOrder",
    "primary_key": "PO-2026-0412",
    "asset_id": "AST-CNC-014",
    "part_id": "PRT-SPN-700",
    "measured_value": 0.92,
    "unit": "criticality",  # MIGRATED: seed `failure.get("unit", "criticality")` -> enrich default
    "criticality": 0.92,  # MIGRATED: seed copy of measured_value -> enrich derive(field copy)
    "qty": 3,
    "candidate_quotes": [
        {
            "quote_id": "QT-SPN-FASTENAL",
            "supplier_id": "SUP-FASTENAL-TH",
            "unit_price": "78500",
            "currency": "THB",
            "lead_time_days": 14,
            "on_contract": True,
        },
        {
            "quote_id": "QT-SPN-RAPIDMRO",
            "supplier_id": "SUP-RAPIDMRO",
            "unit_price": "96000",
            "currency": "THB",
            "lead_time_days": 2,
            "on_contract": False,
        },
        {
            "quote_id": "QT-SPN-NSK",
            "supplier_id": "SUP-NSKBRG-TH",
            "unit_price": "74000",
            "currency": "THB",
            "lead_time_days": 21,
            "on_contract": False,
        },
    ],
    "compliance": {  # MIGRATED: seed literal map -> enrich default(object)
        "avl": True,
        "tax": True,
        "cert": True,
        "sanctions": True,
        "single_source": True,
    },
    "order_type": "EMERGENCY",
    "is_off_avl_override": True,
    "declared_tier_id": "TIER-CTRL",
}


async def _run_to_gate(procedure_id: str, *, seed_override: list[Any] | None = None) -> RunResult:
    """Run a procurement intake-bearing procedure to its suspended ``approve`` gate through the
    production per-kind ``_executors`` (scored_rule -> doa_tier, the advisory stub — no MS-S1),
    over the JSONB-safe Fastenal intake seed. ``seed_override`` swaps a mutated seed (AC-4)."""
    _ensure_handlers()
    adapter = FastenalCsvAdapter()
    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == procedure_id)
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    principals = list(spec.principals)
    requester = next(p for p in principals if "requester" in p.roles)
    seed = seed_override or json.loads(json.dumps([await _intake_seed(adapter)], default=str))
    return await run_procedure(
        proc,
        agent,
        _executors(advisory_stub_factory, principals, seed),
        vertical=_VERTICAL,
        run_id=f"parity-{procedure_id}",
        principal=requester,
    )


@pytest.mark.parametrize("procedure_id", _INTAKE_PROCEDURES)
async def test_intake_enrichment_and_governed_verdicts_parity(procedure_id: str) -> None:
    """AC-2: the enriched intake row + every downstream governed verdict is byte-equal to the
    frozen pre-flip reference, for each of the three intake-bearing procedures. Proven against
    the CURRENT (seed-emitted) world in this commit; unchanged after the ``enrich`` flip."""
    result = await _run_to_gate(procedure_id)
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    by_step = {s.step_id: s for s in result.step_results}

    # (1) The enriched intake row as it threads downstream — flip-robust (judge's input row +
    # its verdict). This is the byte-parity heart of the migration.
    judge_artifact = by_step["judge"].artifact
    assert judge_artifact is not None
    assert judge_artifact["output_set"] == [{**_FROZEN_ENRICHED_INTAKE, "verdict": "breach"}]

    # (2) scored_rule selection + spend (SELECTION = a rule, never the LLM — governed != generated)
    # PLAN-0078 PR-4: the verdict carries the spend's two FACTORS (the declared `derive_spend`
    # transform multiplies them) where it carried a precomputed `amount` — SD-8(a) / SD-6(ii).
    # The ฿288,000 itself stays pinned byte-equal at (4) below and in the PR-4 parity harness.
    source_audit = by_step["source"].audit
    assert source_audit is not None
    [scored] = source_audit["scored_rule"]
    assert scored["selected_supplier_id"] == "SUP-RAPIDMRO"
    assert scored["selected_quote_id"] == "QT-SPN-RAPIDMRO"
    assert scored["selected_unit_price"] == "96000"
    assert scored["qty"] == "3"
    assert scored["currency"] == "THB"
    assert scored["source_path"] == "exception_policy"
    assert scored["override_required"] is True

    # (3) rule_gate: the hero passes every criterion (the PO is not blocked)
    compliance_artifact = by_step["compliance"].artifact
    assert compliance_artifact is not None
    [compliant_row] = compliance_artifact["output_set"]
    assert compliant_row["compliant"] is True
    assert compliant_row["failed_criteria"] == []

    # (4) doa_tier: ฿288,000 -> the [50k, 500k) tier -> ผจก.จัดซื้อ -> appr-pm
    approve_audit = by_step["approve"].audit
    assert approve_audit is not None
    [doa] = approve_audit["doa_tier"]
    assert doa["resolved_tier_id"] == "ผจก.จัดซื้อ"
    assert doa["required_role"] == "ผจก.จัดซื้อ"
    assert doa["resolved_approver_id"] == "appr-pm"
    assert doa["amount"] == {"value": "288000", "currency": "THB"}
    assert doa["sod_required"] is True

    # (5) the run parks at the human gate; the auto steps completed
    assert by_step["intake"].status == StepResultStatus.COMPLETE.value
    assert by_step["judge"].status == StepResultStatus.COMPLETE.value
    assert by_step["source"].status == StepResultStatus.COMPLETE.value
    assert by_step["compliance"].status == StepResultStatus.COMPLETE.value
    assert by_step["approve"].status == StepResultStatus.WAITING_HUMAN.value


async def test_intake_transform_fails_closed_on_missing_source_field() -> None:
    """AC-4: a missing source field on the migrated ``enrich`` transform refuses the WHOLE step
    typed (PLAN-0077 SD-7 fail-closed) — it never silently emits an un-enriched row that would
    mis-band downstream. Demonstrated with a mutated seed dropping ``measured_value`` (the
    ``criticality`` derive's source): the ``enrich`` step FAILS and the run diverts there, never
    reaching the ``approve`` gate."""
    adapter = FastenalCsvAdapter()
    base = json.loads(json.dumps([await _intake_seed(adapter)], default=str))
    mutated = [{k: v for k, v in base[0].items() if k != "measured_value"}]
    result = await _run_to_gate("emergency_sourcing_round", seed_override=mutated)
    by_step = {s.step_id: s for s in result.step_results}

    assert result.run.status == PipelineRunStatus.FAILED.value
    assert by_step["enrich"].status == StepResultStatus.FAILED.value
    assert "approve" not in by_step  # the run diverted at enrich, never reached the gate
    # the refusal is a TYPED transform refusal, not a silent drop
    enrich_trace = by_step["enrich"].reasoning_trace
    assert enrich_trace is not None
    [trace] = enrich_trace
    assert "TransformRefusal" in trace["summary"]


def test_enrich_transform_pinned_migrated_non_participants_byte_identical() -> None:
    """AC-5 / AC-6: each migrated procedure's governance snapshot carries the declared ``enrich``
    transform canonically — it is part of the config hash, so a mid-flight transform edit changes
    the hash and fails CLOSED at resume, like a ladder edit (``governance_pin.py:96-98``). Every
    procedure declaring no transform pins with NO ``transform`` key (the only-when-supplied
    property), so its config hash is byte-identical to before the migration."""
    spec = load_procedures(_VERTICAL)
    by_id = {p.procedure_id: p for p in spec.procedures}

    # AC-5: the enrich transform is present + canonical in each migrated procedure's snapshot,
    # and it contributes to the config hash (stripping it changes the hash -> resume fails closed).
    for pid in _INTAKE_PROCEDURES:
        proc = by_id[pid]
        snapshot = build_governance_snapshot(proc)
        [enrich_snap] = [s for s in snapshot["steps"] if s["step_id"] == "enrich"]
        assert enrich_snap["transform"] is not None
        assert enrich_snap["transform"]["ops"]  # the ops are pinned canonically

        stripped_steps = [
            s.model_copy(update={"transform": None}) if s.step_id == "enrich" else s
            for s in proc.steps
        ]
        stripped = proc.model_copy(update={"steps": stripped_steps})
        assert compute_governance_hash(snapshot) != compute_governance_hash(
            build_governance_snapshot(stripped)
        )

    # AC-6: the reorder siblings declare no transform -> no `transform` key on any step (their
    # config hash is unchanged by this migration — the only-when-supplied property).
    for pid in ("low_stock_reorder_round", "scheduled_low_stock_reorder_round"):
        snapshot = build_governance_snapshot(by_id[pid])
        assert all("transform" not in step for step in snapshot["steps"])
