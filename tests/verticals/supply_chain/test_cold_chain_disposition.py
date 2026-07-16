"""PLAN-0074 Step 4 (AC-9 / AC-10) — the SECOND AT-2 signature, end to end and offline.

The 2nd governance-heavy ``request->approve->fulfill`` instance (ADR-0025 D7 / ADR-0031 D3 row-3
"Path 2"), on a vertical whose authority quantity is **NOT money**: a cold-chain excursion routes to
the human quality authority its SEVERITY demands (how much of the cargo's stability budget the
breach burned), never its cost. What these tests prove beyond "it runs":

* the derived severity is DETERMINISTIC and fails CLOSED on missing / nonsense scalars — no
  disposition is ever routed on a severity the engine had to guess;
* the ``severity_tier`` gate resolves the approver from that severity (a CRITICAL excursion
  escalates to the top quality authority) — and the SELECTED LANE'S BAHT COST, which the scored
  rule computed on the very same entity, does not touch the routing;
* the run SUSPENDS at ``approve`` (``waiting_human``): the disposition is PROPOSED, never executed
  (ADR-0007 approve->execute, LOCKED #3);
* the AT-1 sweep sharing this factory is unaffected (its own test file is the byte-identical proof).

Offline + host-state-free (CLAUDE.md §8): synthetic adapter, pure AT-2 resolution, stubbed advisory
prose — no MS-S1 call, no DB.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from services.api.config import settings
from services.engine.discovery import discover_and_register
from services.engine.procedures.orchestrator import run_procedure
from services.engine.procedures.runs import PipelineRunStatus, StepResult
from services.engine.procedures.severity_tier import SeverityTierVerdict, resolve_severity_tier
from services.engine.procedures.spec import ExcursionSeverity, SeverityLadder, load_procedures
from services.engine.registry import ExecutorFactory, registry
from verticals.supply_chain.cold_chain_assess import (
    ColdChainAssessError,
    derive_excursion_severity,
)
from verticals.supply_chain.procedures_factory import register_supply_chain_procedure_executors

_VERTICAL = "supply_chain"
_PROCEDURE_ID = "cold_chain_excursion_disposition"
_COLD_CHAIN_CEILING = 8.0


def _audit(step_result: StepResult) -> dict[str, Any]:
    """The step's audit, proven present — a governed step that emits NO audit is a defect (the
    audit is what ties each decision to the control that governed it), so fail loudly here."""
    audit = step_result.audit
    assert audit is not None, f"step '{step_result.step_id}' emitted no audit"
    return audit


def _output_set(step_result: StepResult) -> list[Any]:
    """The step's produced rows, proven present (same discipline as :func:`_audit`)."""
    artifact = step_result.artifact
    assert artifact is not None, f"step '{step_result.step_id}' produced no artifact"
    rows = artifact["output_set"]
    assert isinstance(rows, list)
    return rows


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


# --------------------------------------------------------------------------- #
# The severity derivation (the SD-2 action-stamp's pure core)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("magnitude", "duration", "budget", "expected"),
    [
        # dose = magnitude x duration, as a fraction of the cargo's stability budget
        (1, 1, 24, ExcursionSeverity.NEGLIGIBLE),  # ratio ~0.04 — a blip
        (2, 3, 24, ExcursionSeverity.NEGLIGIBLE),  # ratio 0.25 — the band edge is INCLUSIVE
        (2, 4, 24, ExcursionSeverity.MINOR),  # ratio ~0.33
        (2, 6, 24, ExcursionSeverity.MINOR),  # ratio 0.50 — inclusive edge again
        (3, 5, 24, ExcursionSeverity.MAJOR),  # ratio 0.625
        (4, 6, 24, ExcursionSeverity.MAJOR),  # ratio 1.0 — the budget exactly spent
        (5, 6, 24, ExcursionSeverity.CRITICAL),  # ratio 1.25 — the budget is BLOWN
        (6.6, 9, 24, ExcursionSeverity.CRITICAL),  # the shipped pharma excursion
    ],
)
def test_severity_is_derived_deterministically_from_the_dose(
    magnitude: float, duration: float, budget: float, expected: ExcursionSeverity
) -> None:
    """The ladder is total-cover + ascending: every non-negative dose ratio lands in exactly one
    severity, band edges are inclusive, and the top band is unbounded. Deterministic — same inputs,
    same severity (no LLM, no clock)."""
    entity = {
        "excursion_magnitude_c": magnitude,
        "excursion_duration_h": duration,
        "stability_budget_ch": budget,
    }
    derivation = derive_excursion_severity(entity)
    assert derivation.severity is expected
    assert derivation.dose_ch == derivation.magnitude_c * derivation.duration_h
    assert derivation.ratio == derivation.dose_ch / derivation.budget_ch
    # re-derivation is stable (the run-pin invariant depends on it)
    assert derive_excursion_severity(entity).to_audit() == derivation.to_audit()


@pytest.mark.parametrize(
    ("entity", "match"),
    [
        ({"excursion_duration_h": 9, "stability_budget_ch": 24}, "no 'excursion_magnitude_c'"),
        ({"excursion_magnitude_c": 6, "stability_budget_ch": 24}, "no 'excursion_duration_h'"),
        ({"excursion_magnitude_c": 6, "excursion_duration_h": 9}, "no 'stability_budget_ch'"),
        (
            {
                "excursion_magnitude_c": "warm-ish",
                "excursion_duration_h": 9,
                "stability_budget_ch": 24,
            },
            "not a valid finite Decimal",
        ),
        (
            {"excursion_magnitude_c": 6, "excursion_duration_h": 9, "stability_budget_ch": 0},
            "strictly-positive",
        ),
        # the s131-review fail-DANGEROUS cases: NaN / Infinity are "numeric" to Decimal and would
        # slip a bare `> 0` test — an Infinite budget yields a ~0 dose ratio -> the LOWEST tier (a
        # plausible WRONG authority). The finite-guard fails them CLOSED instead.
        (
            {
                "excursion_magnitude_c": 6,
                "excursion_duration_h": 9,
                "stability_budget_ch": "Infinity",
            },
            "finite, strictly-positive",
        ),
        (
            {"excursion_magnitude_c": "NaN", "excursion_duration_h": 9, "stability_budget_ch": 24},
            "finite, strictly-positive",
        ),
    ],
)
def test_severity_derivation_fails_closed(entity: dict[str, object], match: str) -> None:
    """An absent / non-numeric / non-positive scalar blocks the assess step — a disposition is never
    routed to an approver on a guessed severity (the fail-closed contract, mirroring ``_spend``)."""
    with pytest.raises(ColdChainAssessError, match=match):
        derive_excursion_severity(entity)


# --------------------------------------------------------------------------- #
# AC-10 — the full governed run, offline
# --------------------------------------------------------------------------- #


async def test_disposition_run_suspends_at_the_severity_tiered_human_gate(
    supply_chain_factory: ExecutorFactory,
) -> None:
    """intake -> assess -> gdp_gate -> approve, over the REAL supply_chain YAML + ontology +
    synthetic adapter. The run SUSPENDS at ``approve``: the disposition is proposed to the human
    quality authority the severity demands, and ``fulfill`` never runs."""
    spec = load_procedures(_VERTICAL)
    procedure = next(p for p in spec.procedures if p.procedure_id == _PROCEDURE_ID)
    agent = next(a for a in spec.agents if a.agent_id == procedure.run_by)

    result = await run_procedure(
        procedure, agent, supply_chain_factory(), vertical=_VERTICAL, run_id="sc-at2-e2e"
    )

    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    by_step = {step.step_id: step for step in result.step_results}
    # the gated `approve` suspended the run — `fulfill` (the disposition write) never executed.
    # `enrich` (PLAN-0078 PR-2) is the declared transform that now supplies the excursion scalars.
    assert set(by_step) == {"intake", "enrich", "assess", "gdp_gate", "approve"}
    assert "fulfill" not in by_step
    # the run RECORDED the SoD requester half (reviewer F5): the live principal-SoD check is armed
    # for real, not merely proven via the direct fixture calls — drop the disposition's SoD and this
    # goes None and the gate check goes inert.
    assert result.run.step_principals is not None

    # --- assess: the RULE selected the lane; the severity was DERIVED (not authored, not LLM'd) ---
    assess_audit = _audit(by_step["assess"])
    assert assess_audit["governed_kind"] == "scored_rule"
    [derivation] = assess_audit["severity_derivation"]
    assert derivation["severity"] == ExcursionSeverity.CRITICAL.value
    # the excursion magnitude is REAL adapter data: the pharma reading minus its OWN cargo ceiling
    assert Decimal(derivation["magnitude_c"]) > 0
    [selection] = assess_audit["scored_rule"]
    assert selection["selected_quote_id"] == "lane-licensed-destruction"
    assert selection["source_path"] == "default_source"  # a pre-qualified GDP lane, not a deviation
    assert selection["override_required"] is False

    # --- gdp_gate: the batch cleared every GDP criterion (a failed one would block it) ---
    gdp_audit = _audit(by_step["gdp_gate"])
    assert gdp_audit["governed_kind"] == "rule_gate"
    [compliance] = gdp_audit["rule_gate"]
    assert compliance["compliant"] is True
    assert {r["criterion"] for r in compliance["results"]} == {
        "stability_budget",
        "batch_quarantine",
        "licensed_disposal_vendor",
        "coa_customs",
    }

    # --- approve: the NON-MONEY authority routing (the whole point of the 2nd signature) ---
    approve_audit = _audit(by_step["approve"])
    assert approve_audit["governed_kind"] == "severity_tier"
    [verdict] = approve_audit["severity_tier"]
    assert verdict["severity"] == ExcursionSeverity.CRITICAL.value
    assert verdict["required_role"] == "ผอ.ฝ่ายคุณภาพ"  # the top tier — a blown stability budget
    assert verdict["resolved_approver_id"] == "appr-qdir"
    assert verdict["sod_required"] is True  # `approve` is SoD-constrained vs `intake` (derived)
    assert verdict["band"] == {"min": "critical", "max": None}  # the unbounded top band

    # PLAN-0075 SD-6(a): a SUSPENDED run carries NO principal-naming authority tie — the
    # severity_tier verdict above is the honest ROUTING record (routed to appr-qdir); the
    # actor-named governed_decision is emitted only at GATE resolution, after the tier-authority
    # check confirms the acting approver holds ผอ.ฝ่ายคุณภาพ.
    assert "governed_decision" not in approve_audit

    # the gated action PROPOSED only — nothing was executed (ADR-0007 LOCKED #3)
    proposals = _output_set(by_step["approve"])
    assert all(p["status"] == "proposed" for p in proposals)
    assert all(p["action"]["suggested_handler"] == "escalate" for p in proposals)


def _resolve_over_ladder(severity: ExcursionSeverity) -> SeverityTierVerdict:
    """Resolve the SHIPPED disposition ladder for one severity — the routing under test, isolated
    from the run so a counterfactual can vary ONE input at a time (the reviewer F3 fix)."""
    spec = load_procedures(_VERTICAL)
    procedure = next(p for p in spec.procedures if p.procedure_id == _PROCEDURE_ID)
    ladder = next(s.governance_content for s in procedure.steps if s.step_id == "approve")
    assert isinstance(ladder, SeverityLadder)
    return resolve_severity_tier(
        ladder, severity=severity, principals=list(spec.principals), sod_required=True
    )


async def test_money_is_present_but_never_routes_the_authority(
    supply_chain_factory: ExecutorFactory,
) -> None:
    """The seam the 2nd signature exists to press (PLAN-0074 SD-1). Two counterfactuals, so this
    cannot pass with broken production (the reviewer's F3 — the old version asserted on a
    hardcoded dataclass projection that could never carry money):

    1. the scored rule prices the selected lane in baht ON THE SAME ENTITY the approval gate reads,
       yet the severity_tier verdict is *keyed on the ordinal severity* — vary the SEVERITY and the
       resolved authority role MOVES;
    2. vary the LANE COSTS (which change the baht amount) and the resolved authority role does NOT
       move — money is present but does not route.

    Scope: this asserts what the LADDER RESOLVES (routes + audits). Whether the *gate* then enforces
    that exact tier role against the acting approver is the separate s131 authority-enforcement
    finding (a follow-on), deliberately not claimed here."""
    # (1) severity moves the authority
    assert _resolve_over_ladder(ExcursionSeverity.NEGLIGIBLE).required_role == "จนท.ประกันคุณภาพ"
    assert _resolve_over_ladder(ExcursionSeverity.CRITICAL).required_role == "ผอ.ฝ่ายคุณภาพ"

    # (2) money does not: the run stamps a real baht amount on the gated entity, but the resolved
    # authority for that run's CRITICAL excursion is the top tier regardless of what the lane cost.
    spec = load_procedures(_VERTICAL)
    procedure = next(p for p in spec.procedures if p.procedure_id == _PROCEDURE_ID)
    agent = next(a for a in spec.agents if a.agent_id == procedure.run_by)
    result = await run_procedure(
        procedure, agent, supply_chain_factory(), vertical=_VERTICAL, run_id="sc-at2-money"
    )
    by_step = {step.step_id: step for step in result.step_results}

    approved_entity = _output_set(by_step["gdp_gate"])[0]
    assert Decimal(approved_entity["amount"]) > 0  # money IS on the entity the gate consumed
    assert approved_entity["currency"] == "THB"

    [verdict] = _audit(by_step["approve"])["severity_tier"]
    assert "amount" not in verdict and "currency" not in verdict  # the verdict carries no money
    assert verdict["severity"] == ExcursionSeverity.CRITICAL.value
    assert verdict["required_role"] == "ผอ.ฝ่ายคุณภาพ"  # routed by severity, not by the lane cost
