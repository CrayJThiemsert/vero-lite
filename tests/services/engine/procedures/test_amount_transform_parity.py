"""PLAN-0078 PR-4 (AC-8, AC-9): the amount re-sequencing parity harness — all 4 scored_rule steps.

**Oracle-first** (PLAN-0077 SD-5 / Lesson #0026): every assertion here is proven GREEN against the
CURRENT world — where ``_scored_rule`` itself computes ``unit_price x qty`` and stamps ``amount``
(``governance_step.py:324``) — in the oracle commit, and must stay green UNCHANGED after the flip
moves that multiplication into a declared ``derive_spend`` transform, or the flip does not land
(L-2 / the ratified SD-6 bar).

**Cross-vertical by design.** SD-8(a) re-sequences ONE engine chokepoint (``_scored_rule``) that
four shipped scored_rule steps share — procurement's three intake-bearing procedures and
supply_chain's ``assess``. A per-vertical harness would let one vertical's flip drift the other's
amount silently; asserting all four here makes the shared derivation's blast radius explicit.

**The SD-6 two-tier bar** — a byte-equal whole run record is impossible BY DESIGN once the
derivation moves (the ``scored_rule`` audit's precomputed ``amount`` becomes the transform's
inputs). So this harness proves the two tiers SD-6 ratified:

* **(i) output-ROW byte parity** — ``amount`` in its exact string form, plus the non-amount
  scored_rule stamps (``selected_quote_id`` / ``selected_supplier_id`` / ``currency`` /
  ``source_path`` / ``override_required``), byte-equal on the row the authority gate reads.
* **(ii) semantic run-record equivalence** — the doa_tier resolution (procurement) and the
  severity_tier resolution + GDP gate outcome (supply_chain) are identical, and the provenance,
  though changed in FORM, stays complete: the WHY values (unit_price, qty) remain recoverable.

**Flip-robust anchors — the assertions do not move when the derivation does.**

* ``amount`` is asserted on the row the AUTHORITY GATE reads (procurement: ``compliance``'s
  output, which ``approve`` consumes; supply_chain: ``gdp_gate``'s output), NEVER on the
  scored_rule step's own output. Pre-flip ``_scored_rule`` stamps ``amount`` at ``source`` /
  ``assess``; post-flip the ``derive_spend`` transform writes it one step later. Only an anchor
  DOWNSTREAM of both homes carries it in either world — ``source``'s output would pass pre-flip
  and fail post-flip while nothing was actually broken.
* The spend INPUTS are recovered by :func:`_recover_spend_inputs`, which reads the verdict's
  precomputed form pre-flip and the stamped ``selected_unit_price`` post-flip. The CONTRACT is
  "the record can still answer WHY this amount" — not "in this exact location" (SD-6(ii)).
  Compared Decimal-normalized: the two homes carry the same value in different JSON types.

Why the inputs and not just the product: post-flip the multiplication lives ONLY in the pinned
transform, so a reader asking "why 288,000?" needs the two factors FROM THE RECORD. Asserting only
``amount`` would let the flip land while silently dropping the ability to answer that — the same
hole the ratified OQ-5 closed for severity in PR-3.

The references are hand-coded from the demo contracts (not read back from the executor), so
re-shaping ``_scored_rule`` cannot silently drift them (the PLAN-0062 property).

Deterministic, offline, no MS-S1, no DB (the synthetic adapters + the production factories).
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

import pytest

from services.api.config import settings
from services.engine.discovery import discover_and_register
from services.engine.procedures.orchestrator import RunResult, run_procedure
from services.engine.procedures.runs import PipelineRunStatus, StepResultStatus
from services.engine.procedures.spec import load_procedures
from services.engine.registry import ExecutorFactory, registry
from verticals.procurement.data_adapter.fastenal_csv import FastenalCsvAdapter
from verticals.procurement.hero_demo.run import (
    _ensure_handlers,
    _executors,
    _intake_seed,
    advisory_stub_factory,
)
from verticals.supply_chain.procedures_factory import register_supply_chain_procedure_executors

_COLD_CHAIN_CEILING = 8.0

# The three procurement procedures whose `source` step runs the shared scored_rule. All three
# share the ONE seed, so the re-sequencing flips them in lockstep (the PR-1 property).
_PROCUREMENT_PROCEDURES = [
    "emergency_sourcing_round",
    "scheduled_emergency_sourcing_round",
    "event_emergency_sourcing_round",
]

# (i) procurement: the winner is QT-SPN-RAPIDMRO @ 96000/unit x qty 3 -> "288000".
# str(Decimal("96000") * Decimal("3")) == "288000" — an exact Decimal product, never float.
_FROZEN_PROCUREMENT_SPEND: dict[str, Any] = {
    "amount": "288000",
    "currency": "THB",
    "selected_quote_id": "QT-SPN-RAPIDMRO",
    "selected_supplier_id": "SUP-RAPIDMRO",
    "source_path": "exception_policy",
    "override_required": True,
}
_FROZEN_PROCUREMENT_INPUTS: dict[str, str] = {"unit_price": "96000", "qty": "3"}

# (i) supply_chain: the winner is lane-licensed-destruction @ 150.00/unit x qty 420.0.
# str(Decimal("150.00") * Decimal("420.0")) == "63000.000" — Decimal PRESERVES scale through
# multiplication (2 + 1 -> 3 places), which is exactly why the byte form is pinned, not the value.
_FROZEN_SUPPLY_CHAIN_SPEND: dict[str, Any] = {
    "amount": "63000.000",
    "currency": "THB",
    "selected_quote_id": "lane-licensed-destruction",
    "selected_supplier_id": "disposal-licensed-01",
    "source_path": "default_source",
    "override_required": False,
}
_FROZEN_SUPPLY_CHAIN_INPUTS: dict[str, str] = {"unit_price": "150.00", "qty": "420.0"}


def _norm(value: Any) -> str:
    """Decimal-normalize a JSON-carried numeric to its exact string form.

    The verdict audit and the row carry the SAME factor in different JSON types (the seed's
    ``qty`` is the int ``3``; the verdict projects it as ``"3"``), so the flip-robust comparison
    is on the Decimal value, never the JSON type."""
    return str(Decimal(str(value)))


def _recover_spend_inputs(result: RunResult, scored_step_id: str) -> dict[str, str]:
    """Recover the two spend factors FROM THE RUN RECORD, wherever this world homes them.

    Pre-flip: the verdict carries the precomputed ``amount``; the winner's ``unit_price`` is
    recoverable from ``ranked[0]`` (``select_scored_supplier`` sorts the winner first) and ``qty``
    rides the verdict already.
    Post-flip: ``_scored_rule`` stamps the winner's ``selected_unit_price`` and the resolved
    ``qty`` onto the verdict, and the transform multiplies them.

    Deliberately NOT a re-derivation from the row's own fields — recovering by recomputing would
    assert nothing about whether the RECORD can answer "why this amount?", which is the contract
    SD-6(ii) permits the form to change under."""
    by_step = {s.step_id: s for s in result.step_results}
    audit = by_step[scored_step_id].audit or {}
    [verdict] = audit["scored_rule"]

    if "selected_unit_price" in verdict:  # post-flip: the stamped winner price
        unit_price = verdict["selected_unit_price"]
    else:  # pre-flip: the winner is ranked first (scored_rule.py:222-223)
        unit_price = verdict["ranked"][0]["unit_price"]

    return {"unit_price": _norm(unit_price), "qty": _norm(verdict["qty"])}


async def _run_procurement_to_gate(procedure_id: str) -> RunResult:
    """Run a procurement intake-bearing procedure to its suspended ``approve`` gate through the
    production per-kind ``_executors`` (scored_rule -> doa_tier, the advisory stub — no MS-S1)."""
    _ensure_handlers()
    adapter = FastenalCsvAdapter()
    spec = load_procedures("procurement")
    proc = next(p for p in spec.procedures if p.procedure_id == procedure_id)
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    principals = list(spec.principals)
    requester = next(p for p in principals if "requester" in p.roles)
    seed = json.loads(json.dumps([await _intake_seed(adapter)], default=str))
    return await run_procedure(
        proc,
        agent,
        _executors(advisory_stub_factory, principals, seed),
        vertical="procurement",
        run_id=f"pr4-amount-parity-{procedure_id}",
        principal=requester,
    )


@pytest.fixture
async def supply_chain_factory(monkeypatch: pytest.MonkeyPatch) -> ExecutorFactory:
    """The registered supply_chain factory — the same registration path ``services/api/main.py``
    runs at startup."""
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    monkeypatch.setattr(settings, "oct_recommend_threshold", _COLD_CHAIN_CEILING)
    monkeypatch.setattr(settings, "oct_recommend_direction", "above")
    discover_and_register()
    await register_supply_chain_procedure_executors()
    return registry.get_procedure_executors("supply_chain")


async def _run_disposition(factory: ExecutorFactory) -> RunResult:
    spec = load_procedures("supply_chain")
    proc = next(p for p in spec.procedures if p.procedure_id == "cold_chain_excursion_disposition")
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    return await run_procedure(
        proc, agent, factory(), vertical="supply_chain", run_id="pr4-amount-parity-sc"
    )


@pytest.mark.parametrize("procedure_id", _PROCUREMENT_PROCEDURES)
async def test_procurement_amount_row_parity_at_the_gate_anchor(procedure_id: str) -> None:
    """AC-8(i): the ฿ spend + every non-amount scored_rule stamp is byte-equal to the frozen
    reference on the row ``approve`` reads — for each of the three intake-bearing procedures.

    The anchor is ``compliance``'s output (what ``approve`` consumes via
    ``where {compliant: true}``), NOT ``source``'s: post-flip ``amount`` is written by the
    ``derive_spend`` transform that sits between them, so only a downstream anchor holds in both
    worlds."""
    result = await _run_procurement_to_gate(procedure_id)
    by_step = {s.step_id: s for s in result.step_results}
    artifact = by_step["compliance"].artifact
    assert artifact is not None
    [row] = artifact["output_set"]

    for field, expected in _FROZEN_PROCUREMENT_SPEND.items():
        assert row[field] == expected, f"{field}: {row[field]!r} != frozen {expected!r}"


@pytest.mark.parametrize("procedure_id", _PROCUREMENT_PROCEDURES)
async def test_procurement_doa_resolution_equivalence(procedure_id: str) -> None:
    """AC-8(ii): the doa_tier resolution is identical across the flip — ฿288,000 lands in the
    [50k, 500k) tier -> ผจก.จัดซื้อ -> appr-pm, SoD required. This is THE governed verdict the
    re-sequencing must not move: if the declared multiplication produced a different ฿, a
    different human would hold the authority."""
    result = await _run_procurement_to_gate(procedure_id)
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    by_step = {s.step_id: s for s in result.step_results}

    approve_audit = by_step["approve"].audit
    assert approve_audit is not None
    [doa] = approve_audit["doa_tier"]
    assert doa["resolved_tier_id"] == "ผจก.จัดซื้อ"
    assert doa["required_role"] == "ผจก.จัดซื้อ"
    assert doa["resolved_approver_id"] == "appr-pm"
    assert doa["amount"] == {"value": "288000", "currency": "THB"}
    assert doa["sod_required"] is True

    assert by_step["source"].status == StepResultStatus.COMPLETE.value
    assert by_step["compliance"].status == StepResultStatus.COMPLETE.value
    assert by_step["approve"].status == StepResultStatus.WAITING_HUMAN.value


@pytest.mark.parametrize("procedure_id", _PROCUREMENT_PROCEDURES)
async def test_procurement_spend_inputs_recoverable(procedure_id: str) -> None:
    """AC-8(ii) provenance completeness: the two factors behind ฿288,000 stay recoverable FROM THE
    RECORD, and their product is the frozen amount. Post-flip the multiplication lives only in the
    pinned transform, so without the factors on the record no reader could answer "why 288,000?"
    without re-running the spec (the hole OQ-5 closed for severity in PR-3)."""
    result = await _run_procurement_to_gate(procedure_id)
    inputs = _recover_spend_inputs(result, "source")
    assert inputs == _FROZEN_PROCUREMENT_INPUTS
    product = Decimal(inputs["unit_price"]) * Decimal(inputs["qty"])
    assert str(product) == _FROZEN_PROCUREMENT_SPEND["amount"]


async def test_supply_chain_amount_row_parity_at_the_gate_anchor(
    supply_chain_factory: ExecutorFactory,
) -> None:
    """AC-8(i): supply_chain's ``assess`` runs the SAME shared scored_rule, so the re-sequencing
    changes its ฿ too — even though a severity_tier (not the money ladder) routes its authority.
    Asserted on ``gdp_gate``'s output, downstream of both amount homes."""
    result = await _run_disposition(supply_chain_factory)
    by_step = {s.step_id: s for s in result.step_results}
    artifact = by_step["gdp_gate"].artifact
    assert artifact is not None
    [row] = artifact["output_set"]

    for field, expected in _FROZEN_SUPPLY_CHAIN_SPEND.items():
        assert row[field] == expected, f"{field}: {row[field]!r} != frozen {expected!r}"


async def test_supply_chain_semantic_equivalence(supply_chain_factory: ExecutorFactory) -> None:
    """AC-8(ii): the GDP gate outcome and the severity_tier resolution are unchanged — the amount
    re-sequencing must not disturb the NON-money authority path that PR-3 just re-sequenced."""
    result = await _run_disposition(supply_chain_factory)
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    by_step = {s.step_id: s for s in result.step_results}

    gdp_audit = by_step["gdp_gate"].audit
    assert gdp_audit is not None
    [compliance] = gdp_audit["rule_gate"]
    assert compliance["compliant"] is True
    assert compliance["failed_criteria"] == []

    approve_audit = by_step["approve"].audit
    assert approve_audit is not None
    [verdict] = approve_audit["severity_tier"]
    assert verdict["severity"] == "critical"
    assert verdict["required_role"] == "ผอ.ฝ่ายคุณภาพ"
    assert verdict["resolved_approver_id"] == "appr-qdir"


async def test_supply_chain_spend_inputs_recoverable(
    supply_chain_factory: ExecutorFactory,
) -> None:
    """AC-8(ii) provenance completeness for supply_chain — and the scale guard: 150.00 x 420.0
    keeps THREE decimal places by Decimal's scale rules. A float-based or normalizing
    re-implementation would produce "63000.0" or "63000" and silently break the byte form."""
    result = await _run_disposition(supply_chain_factory)
    inputs = _recover_spend_inputs(result, "assess")
    assert inputs == _FROZEN_SUPPLY_CHAIN_INPUTS
    product = Decimal(inputs["unit_price"]) * Decimal(inputs["qty"])
    assert str(product) == _FROZEN_SUPPLY_CHAIN_SPEND["amount"]
