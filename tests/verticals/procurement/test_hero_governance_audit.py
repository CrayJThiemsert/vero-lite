"""PLAN-0045 Step 1b — the offline governance-moment audit capture (the render-contract oracle).

Offline + deterministic (CLAUDE.md §8). Asserts the builder emits the EXACT shipped A1b shapes the
governance-moment render binds to — bound to the real engine output, no reshape:

* AC-3: the ``doa_tier`` verdict — ฿288,000 crosses the ฿200,000 Manager ceiling → the resolved
  tier is the approver **role** ``CONTROLLER`` (never the CSV ``tier_id`` ``TIER-CTRL``), with the
  shipped ``amount{value,currency}`` / ``band{min,max}`` (Decimal-as-str) shape;
* AC-4: the SoD verdict — requester (MAINT_PLANNER) ≠ approver (CONTROLLER) → ``governed``;
* AC-5: the ``governed_decision`` ties join on the shipped keys
  (``control_ref.id == resolved_tier_id``; the ``approve+intake`` SoD id; ``principal_id`` = a
  canonical ``Person`` PK);
* AC-7: the contrast PO (฿99,000) resolves to ``MANAGER`` — no Controller escalation (data-driven).

The pre-committed pass/fail reads are PLAN-0045 AC-3..7, fixed before this test was authored.
"""

from __future__ import annotations

from typing import Any

import pytest

from verticals.procurement.hero_demo.governance_audit import build_hero_governance_audit


@pytest.fixture
async def audit() -> dict[str, Any]:
    return await build_hero_governance_audit()


def _sole(items: list[dict[str, Any]], **match: Any) -> dict[str, Any]:
    hits = [it for it in items if all(it.get(k) == v for k, v in match.items())]
    assert len(hits) == 1, f"expected exactly one {match}, got {len(hits)}"
    return hits[0]


async def test_source_is_the_offline_fixture_arm(audit: dict[str, Any]) -> None:
    assert audit["source"] == "offline-fixture"  # SD-1 Layered: deterministic capture
    assert audit["provisional"] is True


# --------------------------------------------------------------------------- #
# AC-3 — the doa_tier verdict (resolved_tier_id is the ROLE, not the CSV tier_id)
# --------------------------------------------------------------------------- #


async def test_hero_doa_tier_resolves_to_controller(audit: dict[str, Any]) -> None:
    [doa] = audit["hero"]["doa_tier"]
    assert (
        doa["resolved_tier_id"] == "CONTROLLER"
    )  # the approver ROLE (PLAN-0044 D1), NOT TIER-CTRL
    assert doa["required_role"] == "CONTROLLER"
    assert doa["amount"] == {"value": "288000", "currency": "THB"}
    assert doa["band"] == {"min": "200001", "max": "1000001"}  # half-open [CTRL floor, VP floor)
    assert doa["sod_required"] is True
    assert doa["resolved_approver_id"] == "appr-controller"


async def test_declared_tier_id_is_display_only(audit: dict[str, Any]) -> None:
    """The CSV TIER-CTRL label is a display handle; the authoritative value is the role."""
    assert audit["hero"]["declared_tier_id"] == "TIER-CTRL"
    assert audit["hero"]["doa_tier"][0]["resolved_tier_id"] == "CONTROLLER"


# --------------------------------------------------------------------------- #
# AC-4 — the SoD verdict (requester ≠ approver → governed)
# --------------------------------------------------------------------------- #


async def test_hero_sod_is_governed_by_distinct_principals(audit: dict[str, Any]) -> None:
    sod = audit["hero"]["sod"]
    assert sod["governed"] is True
    assert sod["constraint_id"] == "approve+intake"
    assert sod["requester"]["person_id"] == "req-maint-planner"
    assert "MAINT_PLANNER" in sod["requester"]["roles"]
    assert sod["approver"]["person_id"] == "appr-controller"
    assert "CONTROLLER" in sod["approver"]["roles"]
    assert sod["requester"]["person_id"] != sod["approver"]["person_id"]
    assert sod["violations"] == []


# --------------------------------------------------------------------------- #
# AC-5 — governed_decision ties, joined on the shipped keys (no fuzzy match)
# --------------------------------------------------------------------------- #


async def test_hero_governed_decision_ties_join_exactly(audit: dict[str, Any]) -> None:
    hero = audit["hero"]
    gds = hero["governed_decision"]
    doa_tie = _sole([g for g in gds if g["control_ref"]["kind"] == "doa_tier"])
    sod_tie = _sole([g for g in gds if g["control_ref"]["kind"] == "sod"])
    # doa_tier tie joins on control_ref.id == resolved_tier_id
    assert doa_tie["control_ref"]["id"] == hero["doa_tier"][0]["resolved_tier_id"] == "CONTROLLER"
    assert doa_tie["principal_id"] == "appr-controller"
    # sod tie joins on the sorted distinct_steps id + the approver PK
    assert sod_tie["control_ref"]["id"] == hero["sod"]["constraint_id"] == "approve+intake"
    assert sod_tie["principal_id"] == "appr-controller"


# --------------------------------------------------------------------------- #
# AC-7 — the contrast PO stays at MANAGER (governance is data-driven, not hardcoded)
# --------------------------------------------------------------------------- #


async def test_contrast_po_resolves_to_manager_no_escalation(audit: dict[str, Any]) -> None:
    contrast = audit["contrast"]
    [doa] = contrast["doa_tier"]
    assert doa["resolved_tier_id"] == "MANAGER"
    assert doa["amount"] == {"value": "99000", "currency": "THB"}
    assert doa["band"] == {"min": "15001", "max": "200001"}
    assert doa["resolved_approver_id"] == "appr-manager"
    assert contrast["declared_tier_id"] == "TIER-MGR"
    # no Controller anywhere in the contrast audit — the ฿99k PO never escalates
    assert "CONTROLLER" not in doa["resolved_tier_id"]
    assert all(g["principal_id"] != "appr-controller" for g in contrast["governed_decision"])
