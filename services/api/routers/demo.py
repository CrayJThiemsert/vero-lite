"""Hero-demo read-only endpoints (PLAN-0045 Steps 1b + 3).

Two derived read-only views the hero-demo screen binds to:

* ``GET /demo/hero/governance`` — the governance-moment gate audit (the shipped A1b ``doa_tier`` /
  ``sod`` / ``governed_decision`` shapes, no reshape), captured deterministically from the real
  engine (SD-1 Layered = the offline-fixture arm; the live MS-S1 runner, Step 4b, will return the
  same contract with ``source: live-ms-s1``);
* ``GET /demo/hero/impact`` — the ฿-impact ledger (baseline on-AVL wait vs governed off-AVL
  emergency), computed server-side so the money math is unit-testable (SD-3 = the derived API view).

**SD-3 demo guards:** the ``/demo/hero/`` prefix + the ``provisional`` flag on every payload +
this clearly-named demo router make these demo-scoped by construction — never a business surface
(a production ledger over real ERP data is B2, a separate endpoint). No mutation, no DB, no LLM;
the governance audit is deterministic + offline.
"""

from __future__ import annotations

from fastapi import APIRouter

from services.api.models.demo import HeroGovernanceAudit, HeroImpactLedger
from verticals.procurement.hero_demo.governance_audit import build_hero_governance_audit
from verticals.procurement.hero_demo.ledger import build_hero_impact_ledger
from verticals.procurement.hero_demo.run import (
    advisory_stub_factory,
    build_live_hero_governance_audit,
)

router = APIRouter(prefix="/demo/hero", tags=["demo"])


@router.get("/governance", response_model=HeroGovernanceAudit)
async def hero_governance_moment(live: bool = False) -> HeroGovernanceAudit:
    """Return the governance-moment gate audit the render binds to.

    ``live=false`` (default): the deterministic OFFLINE-FIXTURE capture (``resolve_doa_tier`` over
    the PO total). ``live=true``: the SAME contract DERIVED by a real procedure run (the scored_rule
    selects + emits the spend the doa_tier resolves), ``source: "live-run"``. The live path runs
    HOST-STATE-FREE with an advisory-LLM stub (the governed decision is the rule, not the LLM); the
    real MS-S1 model is the C-5 smoke (settings-gated), never a per-request host-state hit here."""
    audit = (
        await build_live_hero_governance_audit(client_factory=advisory_stub_factory)
        if live
        else await build_hero_governance_audit()
    )
    return HeroGovernanceAudit.model_validate(audit)


@router.get("/impact", response_model=HeroImpactLedger)
async def hero_impact_ledger() -> HeroImpactLedger:
    """Return the ฿-impact ledger (baseline vs governed). ALL FIGURES DEMO-GRADE / PROVISIONAL."""
    return HeroImpactLedger.model_validate(await build_hero_impact_ledger())
