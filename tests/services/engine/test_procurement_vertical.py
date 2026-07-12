"""End-to-end + governance tests for the procurement vertical (PLAN-0036 Step 7).

Offline and LLM-free (AC-15): the hero "emergency sourcing" + calm-path "low-stock
reorder" procedures run in-memory through the shipped orchestrator over FAKE
executors (no DB, no MS-S1) — the deterministic judge band is the REAL
``EvaluateStepExecutor``; the band-less ``compliance`` step uses a small per-criterion
dispatch executor (the Step-3 seam, harness-side, not an engine edit); the action
executor is a pass-through (the orchestrator's gated-suspend does the governance work).

The assertions pin **governed ≠ generated** (L-3 / AC-7) and the **credibility musts**
(L-6 / AC-8): the LLM never sets the threshold (authored band), never selects the
supplier (the scored rule's pick is recorded in the data), and never approves (the
run suspends at the human gate); DOA tiers in ฿, the emergency waiver escalates +
forces a justification, SoD, on-contract default / RFQ exception, and per-criterion
compliance blocks a cert-expired supplier. Routing is by deterministic verdict, not
a confidence badge (AC-9). The git-level engine-zero-diff (AC-6, Option-A reading) is
checked by command in the PR, not here; this asserts the registration invariant.
"""

from __future__ import annotations

from typing import Any

from services.engine.discovery import discover_and_register
from services.engine.procedures.evaluate_step import EvaluateStepExecutor
from services.engine.procedures.orchestrator import (
    RunContext,
    StepOutcome,
    run_procedure,
)
from services.engine.procedures.runs import PipelineRunStatus, StepResultStatus
from services.engine.procedures.spec import Person, Step, StepKind, load_procedures
from services.engine.registry import registry
from verticals.procurement.data_adapter import synthetic

# --------------------------------------------------------------------------- #
# Fake executors (offline, LLM-free)
# --------------------------------------------------------------------------- #


class _Query:
    """Fixed-output query executor (the canned ``intake`` / ``read_stock`` seed)."""

    def __init__(self, output: list[Any]) -> None:
        self.output = output

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(
            output=self.output, reasoning_trace=[{"kind": "query", "summary": "read"}]
        )


class _Evaluate:
    """Dispatch: a banded ``evaluate`` (judge) uses the REAL deterministic executor;
    the band-less ``compliance`` evaluate tags each entity ``compliant`` (the Step-3
    seam — the per-criterion gate is asserted separately over the supplier data)."""

    def __init__(self) -> None:
        self._band = EvaluateStepExecutor()

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        if step.threshold is not None or step.threshold_field is not None:
            return await self._band.execute(step, input_set, ctx)
        return StepOutcome(
            output=[{**e, "compliant": True} for e in input_set],
            reasoning_trace=[{"kind": "rule", "summary": "per-criterion compliance (harness)"}],
        )


class _Action:
    """Pass-through action executor — it PROPOSES (returns the set); the orchestrator
    suspends a ``gated`` action at ``waiting_human`` (the human gate). The LLM never
    approves: there is no auto-approval path here."""

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(
            output=input_set,
            reasoning_trace=[{"kind": "rule", "summary": f"propose {step.handler}"}],
        )


def _proc(procedure_id: str) -> tuple[Any, Any]:
    spec = load_procedures("procurement")
    proc = next(p for p in spec.procedures if p.procedure_id == procedure_id)
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    return proc, agent


def _executors(query_output: list[Any]) -> dict[StepKind, Any]:
    return {
        StepKind.QUERY: _Query(query_output),
        StepKind.EVALUATE: _Evaluate(),
        StepKind.ACTION: _Action(),
    }


def _events(event_type: str) -> list[dict[str, Any]]:
    return [e for e in synthetic.operational_events() if e["event_type"] == event_type]


def _po(po_id: str) -> dict[str, Any]:
    return next(p for p in synthetic.purchase_order_records() if p["po_id"] == po_id)


def _suppliers() -> dict[str, dict[str, Any]]:
    return {s["supplier_id"]: s for s in synthetic.supplier_records()}


def _tier_for(tiers: list[dict[str, Any]], amount: float) -> dict[str, Any]:
    """The DOA tier that approves ``amount`` — the lowest tier whose ฿ ceiling still
    covers it; an amount above every finite ceiling escalates to the top tier."""
    for t in sorted(tiers, key=lambda x: x["max_amount"]):
        if amount <= t["max_amount"]:
            return t
    return tiers[-1]


def _criteria(supplier: dict[str, Any]) -> dict[str, bool]:
    """The per-criterion compliance gate (harness-side): a failed criterion blocks."""
    return {
        "avl": supplier["avl_status"] in ("approved", "pending"),  # pending = logged AVL exception
        "tax": bool(supplier.get("tax_id")),
        "cert": supplier["cert_status"] == "valid",
        "sanctions": supplier["sanctions_flag"] is False,
        "single_source": True,
    }


# --------------------------------------------------------------------------- #
# AC-6 — registration invariant (auto-discovery)
# --------------------------------------------------------------------------- #


def test_procurement_auto_discovers() -> None:
    """The vertical registers via the import-scan with no services/api/main.py edit."""
    discover_and_register()
    assert "procurement" in registry.verticals()


# --------------------------------------------------------------------------- #
# AC-2 / AC-7 — the hero runs end-to-end and SUSPENDS at the human gate
# --------------------------------------------------------------------------- #


async def test_hero_runs_and_suspends_at_human_gate() -> None:
    """The hero: intake → judge(breach) → source(auto) → compliance → approve(gated)
    SUSPENDS at waiting_human. The LLM never approves; the run never auto-completes."""
    proc, agent = _proc("emergency_sourcing_round")
    result = await run_procedure(
        proc, agent, _executors(_events("failure")), vertical="procurement", run_id="proc-hero"
    )
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    last = result.step_results[-1]
    assert last.step_id == "approve"
    assert last.status == StepResultStatus.WAITING_HUMAN.value
    # issue_po + audit never ran (suspended before them) — no auto-issue past the gate
    ran = {sr.step_id for sr in result.step_results}
    assert "issue_po" not in ran and "audit" not in ran
    # the deterministic judge tagged the CNC failure (criticality 0.92 ≥ 0.8) breach
    judge_sr = next(sr for sr in result.step_results if sr.step_id == "judge")
    assert judge_sr.artifact is not None
    assert [e["verdict"] for e in judge_sr.artifact["output_set"]] == ["breach"]
    # AC-7: the verdict is engine-deterministic (no LLM, no confidence input)
    assert judge_sr.audit is not None
    assert judge_sr.audit.get("deterministic") is True
    assert judge_sr.audit.get("actor_kind") == "engine"


async def test_calm_path_runs_and_suspends_at_reorder() -> None:
    """The calm-path: read_stock → judge_stock(breach: 40 ≤ reorder_point 100) →
    reorder(gated) suspends. PLAN-0066: judge_stock now bands per-part vs reorder_point
    (ADR-016 TF-1), so the projected rows must carry it (the production read_stock keeps
    it; this event-based test feeds it explicitly)."""
    proc, agent = _proc("low_stock_reorder_round")
    rows = [{**e, "reorder_point": synthetic.FILTER_REORDER_POINT} for e in _events("low_stock")]
    result = await run_procedure(
        proc, agent, _executors(rows), vertical="procurement", run_id="proc-calm"
    )
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    assert result.step_results[-1].step_id == "reorder"
    judge_sr = next(sr for sr in result.step_results if sr.step_id == "judge_stock")
    assert judge_sr.artifact is not None
    assert [e["verdict"] for e in judge_sr.artifact["output_set"]] == ["breach"]


# --------------------------------------------------------------------------- #
# AC-7 — governed ≠ generated: LLM never sets threshold / selects supplier / approves
# --------------------------------------------------------------------------- #


def test_judge_threshold_is_authored_not_llm() -> None:
    proc, _ = _proc("emergency_sourcing_round")
    judge = next(s for s in proc.steps if s.step_id == "judge")
    assert judge.kind is StepKind.EVALUATE  # deterministic engine executor, no model signal
    assert judge.threshold == 0.8
    assert judge.direction == "above"


def test_supplier_selection_is_the_rule_not_llm() -> None:
    """The source handler is fixed in the spec (not LLM-chosen); the scored rule's
    selection is recorded deterministically in the PO (the RFQ supplier)."""
    proc, _ = _proc("emergency_sourcing_round")
    source = next(s for s in proc.steps if s.step_id == "source")
    assert source.handler == "emergency_source"
    po = _po("po-spindle-01")
    assert po["supplier_id"] == "sup-rfq-01"
    assert po["quote_id"] == "quote-spindle-rfq"


def test_approve_and_issue_po_are_human_gated() -> None:
    proc, _ = _proc("emergency_sourcing_round")
    by_id = {s.step_id: s for s in proc.steps}
    assert by_id["approve"].autonomy.value == "gated"
    assert by_id["issue_po"].autonomy.value == "gated"


# --------------------------------------------------------------------------- #
# AC-8 — credibility musts (DOA · waiver · SoD · on-contract/RFQ · compliance)
# --------------------------------------------------------------------------- #


def test_doa_tier_for_hero_amount_is_director() -> None:
    """฿2.15M exceeds the ฿2M plant-manager ceiling → escalates to ผอ. (director)."""
    po = _po("po-spindle-01")
    assert po["amount"] == 2_150_000.0
    tier = _tier_for(synthetic.approval_tier_records(), po["amount"])
    assert tier["approver_role"] == "ผอ."
    # and the calm-path PO (฿45k) sits in tier-1
    calm_tier = _tier_for(synthetic.approval_tier_records(), _po("po-filter-02")["amount"])
    assert calm_tier["approver_role"] == "หน.จัดซื้อ"


def test_emergency_waiver_escalates_with_forced_justification() -> None:
    po = _po("po-spindle-01")
    assert po["waiver_applied"] is True
    assert po["justification"].strip()  # forced, non-empty
    assert "ผอ." in po["justification"] or "escalate" in po["justification"].lower()
    # the calm path takes no waiver
    assert _po("po-filter-02")["waiver_applied"] is False


def test_separation_of_duties_chain_is_distinct() -> None:
    roles = [a["role"] for a in _po("po-spindle-01")["approver_chain"]]
    assert len(roles) == len(set(roles))  # requester ≠ approver ≠ …
    assert "requester" in roles and any(r != "requester" for r in roles)


def test_on_contract_default_with_logged_rfq_exception() -> None:
    spindle = [q for q in synthetic.quotation_records() if q["part_no"] == "part-spindle-01"]
    assert any(q["on_contract"] for q in spindle)  # the on-contract default exists
    po = _po("po-spindle-01")
    chosen = next(q for q in spindle if q["quote_id"] == po["quote_id"])
    assert chosen["on_contract"] is False  # the RFQ exception was taken (faster)
    j = po["justification"].lower()
    assert "rfq" in j and ("exception" in j or "logged" in j)  # exception is LOGGED


def test_per_criterion_compliance_blocks_cert_expired() -> None:
    sup = _suppliers()
    # the alternative supplier's certificate is expired → the cert criterion fails → blocked
    assert sup["sup-rfq-02"]["cert_status"] == "expired"
    assert _criteria(sup["sup-rfq-02"])["cert"] is False
    assert not all(_criteria(sup["sup-rfq-02"]).values())  # blocked on ≥1 failed criterion
    # the selected RFQ supplier is not sanctioned, cert valid, tax id present
    sel = sup["sup-rfq-01"]
    assert sel["cert_status"] == "valid" and sel["sanctions_flag"] is False and sel["tax_id"]


# --------------------------------------------------------------------------- #
# AC-9 — no confidence theater: routing is by deterministic verdict
# --------------------------------------------------------------------------- #


def test_routing_is_by_verdict_not_confidence() -> None:
    proc, _ = _proc("emergency_sourcing_round")
    source = next(s for s in proc.steps if s.step_id == "source")
    assert source.input is not None
    assert source.input.where == {"verdict": "breach"}  # deterministic verdict, not confidence
    for s in proc.steps:
        if s.input and s.input.where:
            assert "confidence" not in s.input.where


# --------------------------------------------------------------------------- #
# AC-1 (A1b Step 1) — the requester principal is recorded on the run (typed seam)
# --------------------------------------------------------------------------- #


async def test_run_records_requester_principal() -> None:
    """The orchestrator records the resolving Person for each SoD-constrained step it
    completes into the run-level ``step_principals`` map, from the TYPED
    ``RunContext.principal`` ambient seam — NEVER ``trigger_context`` (OQ-2). The gated
    ``approve`` step suspends, so its approver is recorded later at the gate, not here."""
    proc, agent = _proc("emergency_sourcing_round")
    requester = Person(person_id="req-planner", name="ผู้ขอซื้อ", roles=frozenset({"requester"}))
    result = await run_procedure(
        proc,
        agent,
        _executors(_events("failure")),
        vertical="procurement",
        run_id="proc-rec",
        principal=requester,
    )
    # intake is SoD-constrained + completes -> recorded; approve suspends (recorded at gate).
    assert result.run.step_principals == {"intake": "req-planner"}
    assert result.run.trigger_context is None  # the carrier is the typed seam, not the blob


async def test_run_without_principal_records_none() -> None:
    """No ambient principal -> the constrained requester step records ``None`` (a present
    key signalling SoD), which fails the run-check CLOSED at the gate (AC-3) rather than
    silently passing."""
    proc, agent = _proc("emergency_sourcing_round")
    result = await run_procedure(
        proc, agent, _executors(_events("failure")), vertical="procurement", run_id="proc-none"
    )
    assert result.run.step_principals == {"intake": None}
