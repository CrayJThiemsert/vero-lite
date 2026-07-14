"""Response models for the hero-demo read-only endpoints (PLAN-0045 Step 3 wiring).

**Demo-scoped by construction (SD-3 guards):** the routes live under ``/demo/hero/``, every payload
carries a ``provisional`` flag, and the figures are DEMO-GRADE / PROVISIONAL (dossier §10). A
production ledger over real ERP data (B2, real Fastenal numbers) is a SEPARATE endpoint — nothing
here is a business surface, so it cannot be promoted to production by accident.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from services.engine.economic_impact import EconomicImpact


class ImpactSide(BaseModel):
    """One side of the ฿-impact ledger (a sourcing path: on-AVL wait vs off-AVL emergency)."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(description="the sourcing path this side models")
    supplier_id: str = Field(description="the supplier for this path")
    lead_time_days: int = Field(description="replenishment lead time in days")
    downtime_thb: Decimal = Field(
        description="downtime exposure over the lead time (THB, demo-grade)"
    )
    part_cost_thb: Decimal = Field(description="part cost for the order (THB, demo-grade)")
    exposure_thb: Decimal = Field(description="total THB exposure = downtime + part cost")


class HeroImpactLedger(BaseModel):
    """The ฿-impact ledger (baseline vs governed). ALL FIGURES DEMO-GRADE / PROVISIONAL."""

    model_config = ConfigDict(extra="forbid")

    provisional: bool = Field(
        description="always true — demo-grade figures, NOT real Fastenal data"
    )
    currency: str = Field(description="ISO currency for every figure (THB)")
    asset_id: str = Field(description="the failed asset driving the downtime exposure")
    part_id: str = Field(description="the critical part being sourced")
    qty: int = Field(description="order quantity")
    productive_hours_per_day: Decimal = Field(
        description="demo modelling assumption (productive hours lost per day; not a CSV column)"
    )
    baseline: ImpactSide = Field(
        description="wait for the on-AVL preferred supplier (the slow path)"
    )
    governed: ImpactSide = Field(
        description="the governed off-AVL emergency decision (the fast path)"
    )
    expedite_premium_thb: Decimal = Field(
        description="the price of speed: governed part cost over the baseline part cost"
    )
    avoided_downtime_thb: Decimal = Field(description="downtime avoided vs the baseline wait")
    net_benefit_thb: Decimal = Field(description="the baseline exposure less the governed exposure")
    economic_impact: EconomicImpact | None = Field(
        default=None,
        description=(
            "PLAN-0073 (SD-2b): the typed Box-4 economic-impact facet — the same ฿ figures as "
            "the ledger plus audit-grade provenance (kind / basis_refs / assumptions / "
            "provisional). Additive + optional (None when no producer grounds a figure); the "
            "ledger fields above stay byte-identical (ADR-0030 D2 coexist)."
        ),
    )


class HeroGovernanceAudit(BaseModel):
    """The governance-moment gate audit (hero + contrast) — SHIPPED A1b shapes, no reshape."""

    model_config = ConfigDict(extra="forbid")

    provisional: bool = Field(description="always true — demo-grade dataset")
    source: str = Field(
        description="capture arm: 'offline-fixture' (deterministic engine capture) or 'live-ms-s1'"
    )
    hero: dict[str, Any] = Field(
        description="the hero PO gate audit — the shipped doa_tier / sod / governed_decision shapes"
    )
    contrast: dict[str, Any] = Field(
        description="the contrast PO audit (THB 99k resolves to MANAGER — no Controller escalation)"
    )
