"""Hero-demo read-only endpoints (PLAN-0045 Steps 1b + 3).

Two derived read-only views the hero-demo screen binds to:

* ``GET /demo/hero/governance`` — the governance-moment gate audit (the shipped A1b ``doa_tier`` /
  ``sod`` / ``governed_decision`` shapes, no reshape), captured deterministically from the real
  engine (SD-1 Layered = the offline-fixture arm; the live MS-S1 runner, Step 4b, will return the
  same contract with ``source: live-ms-s1``);
* ``GET /demo/hero/impact`` — the ฿-impact ledger (baseline on-AVL wait vs governed off-AVL
  emergency), computed server-side so the money math is unit-testable (SD-3 = the derived API view).

* ``POST /demo/hero/event`` — the EVENT-triggered opener (PLAN-0057): the SAME governance-moment
  contract, but DERIVED by the shipped event bridge (ADR-0029) — a detected asset-failure event
  auto-fires the governed procedure to a persisted run parked at the DOA gate (``source:
  "event-fired"``, the beat-1 "sense" cue on ``hero.trigger``).

**SD-3 demo guards:** the ``/demo/hero/`` prefix + the ``provisional`` flag on every payload +
this clearly-named demo router make these demo-scoped by construction — never a business surface
(a production ledger over real ERP data is B2, a separate endpoint). The two READ views are
deterministic + offline (no mutation, no DB, no LLM). The PLAN-0057 event view is an explicit
**POST** — it persists a governed run via the bridge (hence a new POST route, NOT a param on the
read-only GET; PLAN-0057 SD-2) — still demo-scoped + provisional + MS-S1-free.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.models.demo import HeroGovernanceAudit, HeroImpactLedger
from services.db.session import get_session
from verticals.procurement.hero_demo.governance_audit import build_hero_governance_audit
from verticals.procurement.hero_demo.ledger import build_hero_impact_ledger
from verticals.procurement.hero_demo.run import (
    advisory_stub_factory,
    build_event_hero_governance_audit,
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


@router.post("/event", response_model=HeroGovernanceAudit)
async def hero_event_moment(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> HeroGovernanceAudit:
    """PLAN-0057 — the EVENT-triggered opener. Fire ``event_emergency_sourcing_round`` via the
    shipped event bridge (ADR-0029) to a persisted run parked at the ``doa_tier`` DOA gate, and
    return the parked governance moment in the SAME ``HeroGovernanceAudit`` contract as
    ``GET /governance`` (``source: "event-fired"``, the beat-1 "sense" cue on ``hero.trigger``).

    A **POST**, not a param on the read-only ``/governance`` GET: it WRITES/persists a governed run
    (PLAN-0057 SD-2). Requires the procurement executor factory registered (app startup when
    ``OCT_VERTICAL=procurement``); the fire is deterministic + MS-S1-free (CLAUDE.md §8)."""
    return HeroGovernanceAudit.model_validate(await build_event_hero_governance_audit(session))
