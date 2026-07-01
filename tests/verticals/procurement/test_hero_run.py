"""PLAN-0045 Step 4b / C-3 — the LIVE governance-moment runner (offline stub-client gate).

Offline + LLM-free: the runner is exercised with a STUB ``ChatClient`` (mirrors
``test_procurement_sod_gate._CyclingChat``) so the full Fastenal hero loop
(intake -> judge -> source -> compliance -> approve) runs deterministically with NO MS-S1 -- this
IS the CI gate for C-3 (the C-5 live smoke swaps in the real OllamaClient, host-state).

Proves the governance moment is DERIVED by the run, not read from a fixture: the ``scored_rule``
executor selects RapidMRO and emits 288,000 THB (unit_price x qty), which threads to the ``approve``
gate's ``doa_tier`` and resolves CONTROLLER + the SoD tie -- the section-3 fix, end to end.
"""

from __future__ import annotations

import json
from typing import Any

from services.engine.llm.client import ChatResult
from verticals.procurement.data_adapter.fastenal_csv import FastenalCsvAdapter
from verticals.procurement.hero_demo.run import (
    build_live_hero_governance_audit,
    run_hero_governance_moment,
)


class _CyclingChat:
    """Stub ChatClient: a draft on call-1 (no ``response_format``), a canned judgment on call-2
    (with ``response_format``) -- the LLM path is advisory only; it never selects or routes."""

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        if response_format is not None:
            return ChatResult(content=_judgment_json(), thinking=None, model="gpt-oss:20b", raw={})
        return ChatResult(content="draft", thinking="t", model="gpt-oss:20b", raw={})


def _judgment_json() -> str:
    return json.dumps(
        {
            "title": "Emergency source the critical set",
            "description": "A governed sourcing proposal awaiting the human DOA gate.",
            "rationale": "The deterministic scored rule selected the supplier.",
            "confidence": 0.9,
            "affected_entities": [{"object_type": "PurchaseOrder", "primary_key": "PO-2026-0412"}],
            "suggested_handler": "emergency_source",
            "handler_payload": {},
        }
    )


def _stub_factory(_model: str) -> _CyclingChat:
    return _CyclingChat()


async def test_live_run_derives_the_hero_governance_moment() -> None:
    """The full loop with a stub LLM: the scored_rule selects RapidMRO + emits 288,000, and the
    approve doa_tier resolves CONTROLLER -- the governance moment, derived by the run."""
    hero = await run_hero_governance_moment(
        FastenalCsvAdapter(), client_factory=_stub_factory, run_id="test-hero-live"
    )
    # The sourcing SELECTION is the scored rule (never the LLM) -> the off-AVL RapidMRO.
    assert hero["supplier_id"] == "SUP-RAPIDMRO"
    assert hero["po_id"] == "PO-2026-0412"
    # The spend is DERIVED (96,000 x 3) and threaded to the DOA gate, not read from the PO total.
    assert hero["amount"] == {"value": "288000", "currency": "THB"}
    [doa] = hero["doa_tier"]
    assert doa["resolved_tier_id"] == "CONTROLLER"
    assert doa["resolved_approver_id"] == "appr-controller"
    assert doa["amount"] == {"value": "288000", "currency": "THB"}
    # SoD held: requester (maint planner) != approver (controller) -> governed.
    assert hero["sod"]["governed"] is True
    assert hero["sod"]["requester"]["person_id"] == "req-maint-planner"
    assert hero["sod"]["approver"]["person_id"] == "appr-controller"
    # Both audit-to-control ties: the doa_tier route + the SoD gate.
    kinds = {gd["control_ref"]["kind"] for gd in hero["governed_decision"]}
    assert kinds == {"doa_tier", "sod"}
    # The scored_rule provenance rode along: an off-contract (off-AVL) exception pick.
    [scored] = hero["scored_rule"]
    assert scored["source_path"] == "exception_policy"


async def test_live_run_is_json_safe() -> None:
    """The derived audit is JSONB-safe (Decimal already projected to str) so the endpoint can
    return it without a serialisation shim."""
    hero = await run_hero_governance_moment(
        FastenalCsvAdapter(), client_factory=_stub_factory, run_id="test-hero-json"
    )
    json.dumps(hero)  # must not raise


async def test_build_live_contract_hero_live_contrast_offline() -> None:
    """The full render contract: source 'live-run', the HERO derived by the run, and the CONTRAST
    reused from the deterministic offline builder (99,000 -> MANAGER, no Controller escalation)."""
    audit = await build_live_hero_governance_audit(
        FastenalCsvAdapter(), client_factory=_stub_factory
    )
    assert audit["provisional"] is True
    assert audit["source"] == "live-run"
    assert audit["hero"]["supplier_id"] == "SUP-RAPIDMRO"
    [contrast_doa] = audit["contrast"]["doa_tier"]
    assert contrast_doa["resolved_tier_id"] == "MANAGER"  # the data-driven contrast (AC-7)
