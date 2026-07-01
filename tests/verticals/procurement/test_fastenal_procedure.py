"""PLAN-0045 Step 4b / C-2 — the in-code Fastenal hero procedure (ladder-swap).

Offline. Proves the shipped emergency_sourcing_round shape reused with the Fastenal DOA ladder
swapped into the approve step still validates as runnable, and that the swapped ladder resolves
the hero ฿288,000 to CONTROLLER (the approver role) → appr-controller.
"""

from __future__ import annotations

from decimal import Decimal

from services.engine.procedures.doa_tier import resolve_doa_tier
from services.engine.procedures.orchestrator import validate_runnable
from services.engine.procedures.spec import DoaLadder
from verticals.procurement.hero_demo.procedure import (
    fastenal_hero_procedure,
    load_fastenal_principals,
)


def test_procedure_swaps_ladder_and_stays_runnable() -> None:
    proc, agent = fastenal_hero_procedure()
    assert proc.procedure_id == "fastenal_emergency_sourcing"
    approve = next(s for s in proc.steps if s.step_id == "approve")
    ladder = approve.governance_content
    assert isinstance(ladder, DoaLadder)
    assert ladder.currency == "THB"
    assert [t.approver_role for t in ladder.tiers] == [
        "SUPERVISOR",
        "MANAGER",
        "CONTROLLER",
        "VP_OPERATIONS",
    ]
    validate_runnable(proc, agent)  # reuses the shipped validated shape — must not raise


async def test_swapped_ladder_resolves_hero_to_controller() -> None:
    proc, _ = fastenal_hero_procedure()
    principals = await load_fastenal_principals()
    approve = next(s for s in proc.steps if s.step_id == "approve")
    ladder = approve.governance_content
    assert isinstance(ladder, DoaLadder)
    verdict = resolve_doa_tier(
        ladder,
        amount=Decimal("288000"),
        currency="THB",
        principals=principals,
        sod_required=True,
    )
    assert verdict.resolved_tier_id == "CONTROLLER"
    assert verdict.resolved_approver_id == "appr-controller"
