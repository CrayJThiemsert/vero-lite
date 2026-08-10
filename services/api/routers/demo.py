"""Hero-demo read-only endpoints (PLAN-0045 Steps 1b + 3; vertical seam PLAN-0098 D-B).

Three derived views the hero-demo screen (View G) binds to:

* ``GET /demo/hero/governance`` — the governance-moment gate audit (the shipped A1b
  ``doa_tier`` / ``sod`` / ``governed_decision`` shapes, no reshape), captured
  deterministically from the real engine;
* ``GET /demo/hero/impact`` — the money beat, computed server-side so the math is
  unit-testable;
* ``POST /demo/hero/event`` — the EVENT-triggered opener (PLAN-0057), procurement-only.

**The vertical seam (PLAN-0098 D-B).** Until PLAN-0098 this router imported six
``verticals.procurement.*`` symbols at module scope and passed the literal
``"procurement"`` to the ฿ producer, so booting any other vertical still served
procurement's hero. It now dispatches on ``settings.oct_vertical`` through
``_HERO_BUILDERS``, with imports LAZY inside each builder — the same shape already
proven by ``main.py``'s ``_PROCEDURE_EXECUTOR_REGISTRARS``. Booting
``OCT_VERTICAL=fleet_maintenance`` therefore no longer imports procurement's 802-line
``hero_demo/run.py`` at router-import time.

This seam is **not** cited on ADR-0031 alone, which that ADR forbids (D4 corollary 1,
``0031-core-lifecycle-architecture.md:148-149``: "No PLAN may cite this ADR alone as
justification to build a seam; it must also show its trigger fired"). The trigger is
**FIRED at N=2**: procurement (shipped) and fleet_maintenance (PLAN-0098) both need a
hero-demo binding on these same routes. A third vertical adds one ``hero_demo/`` package
and one registry entry.

**A vertical with no hero of its own gets a typed 404** — PLAN-0103 Step 3, Cray typed
s219. This reverses the earlier SD-1 ruling (a) of 2026-07-31, which fell back to the
procurement hero so the ``energy`` boot default kept rendering what it always had. That
was the right call while exactly one published system existed; multi-system inverts it,
because the fallback's failure mode is serving one design partner's bespoke hero under
another's banner (ADR-0032 D1.2). See ``_builders`` for the full reasoning.

⚠️ Consequence worth knowing before booting a heroless vertical: the boot default is
``energy``, which ships **no** hero package, so ``GET /demo/hero/{governance,impact}``
now 404 on a default boot. Tests that assert procurement's ledger must pin
``OCT_VERTICAL=procurement`` explicitly — several did not, and were reaching Fastenal's
numbers through the fallback while appearing to run on the default.

**SD-3 demo guards:** the ``/demo/hero/`` prefix + the ``provisional`` flag on every
payload + this clearly-named demo router make these demo-scoped by construction — never
a business surface. The two READ views are deterministic + offline (no mutation, no DB,
no LLM). The PLAN-0057 event view is an explicit **POST** because it persists a governed
run via the bridge (PLAN-0057 SD-2) — still demo-scoped + provisional + MS-S1-free.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated, Any, NamedTuple

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.config import settings
from services.api.models.demo import FleetHeroImpact, HeroGovernanceAudit, HeroImpactLedger
from services.db.session import get_session

router = APIRouter(prefix="/demo/hero", tags=["demo"])

# PLAN-0073 (SD-2b): the hero's emergency-sourcing context for the read-time facet. The
# producer emits the representative emergency-sourcing ฿ exemplar (the hero PO) for a
# critical-failure trigger and None otherwise (OQ-C) — the hero's asset-failure scenario.
_HERO_IMPACT_TRIGGER = {"event_type": "failure"}

#: PLAN-0103 Step 3 (Cray, typed, s219) — the request-time hero fallback is CLOSED.
#:
#: This was ``_FALLBACK_VERTICAL = "procurement"``: a vertical with no registered hero
#: served procurement's (SD-1 = (a), Cray 2026-07-31), which kept the energy boot default
#: working while exactly one published system existed. Multi-system makes that resolve the
#: wrong way. The hero is BESPOKE PER DESIGN PARTNER (ADR-0032 D1.2), so the fallback's
#: failure mode is serving a **Fastenal procurement hero under an energy banner** — a
#: mismatch a partner reads as a bug, and the reason PLAN-0100 had to edge-exclude Tab G
#: from the published energy system rather than simply not render it.
#:
#: Closing it moves the refusal from the EDGE (an allowlist that must remember to exclude
#: G for every future heroless vertical) to the ROUTE (which knows). A 404 is the honest
#: answer: this deployment has no hero, which is different from "your request was wrong".


class _HeroBuilders(NamedTuple):
    """One vertical's View G surface. Imports stay lazy INSIDE each callable."""

    governance: Callable[[bool], Awaitable[dict[str, Any]]]
    impact: Callable[[], Awaitable[HeroImpactLedger | FleetHeroImpact]]


async def _procurement_governance(live: bool) -> dict[str, Any]:
    """Procurement's gate audit — offline fixture, or the live-run derivation."""
    if live:
        from verticals.procurement.hero_demo.run import (
            advisory_stub_factory,
            build_live_hero_governance_audit,
        )

        return await build_live_hero_governance_audit(client_factory=advisory_stub_factory)
    from verticals.procurement.hero_demo.governance_audit import build_hero_governance_audit

    return await build_hero_governance_audit()


async def _procurement_impact() -> HeroImpactLedger | FleetHeroImpact:
    """Procurement's ฿-impact ledger PLUS the typed Box-4 facet (PLAN-0073 SD-2b).

    The facet reuses the SAME ``build_hero_impact_ledger`` computation, so its figures
    equal the ledger's (no drift), while adding audit-grade provenance. The ledger fields
    stay byte-identical (ADR-0030 D2 coexist).
    """
    from verticals.procurement.economic_impact import procurement_economic_impact
    from verticals.procurement.hero_demo.ledger import build_hero_impact_ledger

    ledger = await build_hero_impact_ledger()
    ledger["economic_impact"] = await procurement_economic_impact(
        _HERO_IMPACT_TRIGGER, "procurement"
    )
    return HeroImpactLedger.model_validate(ledger)


async def _fleet_governance(live: bool) -> dict[str, Any]:
    """Fleet's gate audit. Offline only in v1 — ``live=true`` is refused, not faked.

    Serving the deterministic capture under ``source: live-*`` would be the one thing a
    provenance-carrying demo must not do: claim a derivation it did not perform.
    """
    if live:
        raise HTTPException(
            status_code=400,
            detail=(
                "no live arm is registered for fleet_maintenance — View G's fleet hero "
                "ships the deterministic offline capture only (PLAN-0098). Request "
                "live=false; the offline arm is the gate, and a live run would be "
                "evidence, not a different contract."
            ),
        )
    from verticals.fleet_maintenance.hero_demo.governance_audit import (
        build_fleet_governance_audit,
    )

    return await build_fleet_governance_audit()


async def _fleet_impact() -> HeroImpactLedger | FleetHeroImpact:
    """Fleet's money beat — the shipped ฿ producer, not a supplier ledger (PLAN-0098 D-A)."""
    from verticals.fleet_maintenance.hero_demo.impact import build_fleet_hero_impact

    return await build_fleet_hero_impact()


_HERO_BUILDERS: dict[str, _HeroBuilders] = {
    "procurement": _HeroBuilders(_procurement_governance, _procurement_impact),
    "fleet_maintenance": _HeroBuilders(_fleet_governance, _fleet_impact),
}
"""Per-vertical View G surface. Imports stay LAZY inside each builder so booting one
vertical never imports another's hero package (the ``main.py``
``_PROCEDURE_EXECUTOR_REGISTRARS`` shape). Two of six verticals ship a hero: a governed
hero is bespoke per design partner (ADR-0032 D1.2), never scaffolded."""


def _builders() -> _HeroBuilders:
    """The active vertical's OWN builders, or a typed 404 — never another vertical's.

    Read at REQUEST time, not import time: a settings override in a test must take
    effect, and the router must not bake in whatever vertical happened to be active when
    the module was first imported.
    """
    builders = _HERO_BUILDERS.get(settings.oct_vertical)
    if builders is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"vertical '{settings.oct_vertical}' ships no governed hero. A hero is "
                "bespoke per design partner (ADR-0032 D1.2) and is never borrowed from "
                "another vertical — serving one would put a different partner's story "
                "under this deployment's banner."
            ),
        )
    return builders


@router.get("/governance", response_model=HeroGovernanceAudit)
async def hero_governance_moment(live: bool = False) -> HeroGovernanceAudit:
    """Return the governance-moment gate audit the render binds to.

    ``live=false`` (default): the deterministic OFFLINE-FIXTURE capture. ``live=true``:
    where the active vertical registers a live arm, the SAME contract DERIVED by a real
    procedure run (``source: "live-run"``), host-state-free with an advisory-LLM stub —
    the governed decision is the rule, not the LLM. A vertical with no live arm returns
    a typed 400 rather than relabelling its offline capture.
    """
    audit = await _builders().governance(live)
    return HeroGovernanceAudit.model_validate(audit)


@router.get("/impact", response_model=HeroImpactLedger | FleetHeroImpact)
async def hero_impact_ledger() -> HeroImpactLedger | FleetHeroImpact:
    """Return the active vertical's View G money payload. ALL FIGURES DEMO-GRADE.

    A **union at the decorator**, not a widened model: ADR-0030 D2 pins
    ``HeroImpactLedger`` as "stays exactly as built" and its Alternative 3 explicitly
    rejects generalizing it, so fleet gets its own ``FleetHeroImpact`` instead. The two
    are disjoint by construction — both ``extra="forbid"``, ``FleetHeroImpact`` requires
    a ``vertical`` discriminant, and ``HeroImpactLedger`` requires supplier fields fleet
    never emits.
    """
    return await _builders().impact()


@router.post("/event", response_model=HeroGovernanceAudit)
async def hero_event_moment(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> HeroGovernanceAudit:
    """PLAN-0057 — the EVENT-triggered opener, procurement-only.

    Fire ``event_emergency_sourcing_round`` via the shipped event bridge (ADR-0029) to a
    persisted run parked at the ``doa_tier`` DOA gate, and return the parked governance
    moment in the SAME ``HeroGovernanceAudit`` contract as ``GET /governance``
    (``source: "event-fired"``).

    A **POST**, not a param on the read-only GET: it WRITES/persists a governed run
    (PLAN-0057 SD-2). Requires the procurement executor factory registered (app startup
    when ``OCT_VERTICAL=procurement``); the fire is deterministic + MS-S1-free
    (CLAUDE.md §8). Deliberately NOT vertical-dispatched — PLAN-0098 keeps a fleet event
    arm out of scope, and a fleet boot cannot serve this route anyway.
    """
    from verticals.procurement.hero_demo.run import build_event_hero_governance_audit

    return HeroGovernanceAudit.model_validate(await build_event_hero_governance_audit(session))
