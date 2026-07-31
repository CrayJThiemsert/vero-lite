"""Response models for the hero-demo read-only endpoints (PLAN-0045 Step 3 wiring).

**Demo-scoped by construction (SD-3 guards):** the routes live under ``/demo/hero/``, every payload
carries a ``provisional`` flag, and the figures are DEMO-GRADE / PROVISIONAL (dossier §10). A
production ledger over real ERP data (B2, real Fastenal numbers) is a SEPARATE endpoint — nothing
here is a business surface, so it cannot be promoted to production by accident.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

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


class FleetHeroImpact(BaseModel):
    """Fleet's View G money payload — a mirror of the donor by FUNCTION, not by shape.

    ``HeroImpactLedger`` above models procurement's two sourcing paths, and every one of
    its ``ImpactSide`` fields (``supplier_id`` / ``lead_time_days`` / ``downtime_thb`` /
    ``part_cost_thb``) is a column of a committed CSV. Fleet ships one synthetic adapter
    and no CSV at all, so filling that shape would mean inventing three modelling inputs
    with no partner provenance. This model exists instead of a fleet ``ImpactSide``
    (PLAN-0098 D-A), and ``HeroImpactLedger`` is left byte-for-byte untouched — ADR-0030
    D2 pins it "stays exactly as built", and that ADR's Alternative 3 explicitly rejects
    generalizing it.

    **Measured and modelled ฿ are different fields, and that is the whole design.**
    ``quoted_repair_thb`` is the amount the garage actually quoted — it comes off the
    event's own ``measured_value`` where ``unit == "THB"``. Every ฿ figure that was
    *derived* lives inside ``impact``, which is the only model here carrying
    ``assumptions`` (ADR-0030 D3). A reader can therefore tell, from the shape alone,
    which number was observed and which was modelled — without trusting a docstring.

    Two structural consequences, both enforced below rather than documented:

    * ``impact`` is **required**, not ``EconomicImpact | None``. A fleet hero payload
      without its disclosed assumptions cannot be constructed at all.
    * the validator rejects an empty ``assumptions`` list. Stripping the disclosed 15%
      comparison-recovery assumption makes this endpoint fail validation instead of
      quietly rendering a modelled ฿ as though it were measured.

    ALL DERIVED FIGURES ARE PROVISIONAL — advisory, never authoritative (ADR-0030 D5).
    """

    model_config = ConfigDict(extra="forbid")

    provisional: Literal[True] = Field(
        description="always true — the derived figures are modelled estimates (ADR-0030 D5)"
    )
    vertical: Literal["fleet_maintenance"] = Field(
        description=(
            "the vertical this payload describes — also the discriminant the /impact route's "
            "union and the View G frontend branch on. HeroImpactLedger carries no such field "
            "by design (ADR-0030 D2 forbids editing it), so procurement is the absence case."
        )
    )
    currency: str = Field(description="ISO currency for every figure (THB)")
    truck_id: str = Field(description="the truck whose repair is being approved")
    case_id: str = Field(description="the repair case the quote belongs to")
    quoted_repair_thb: Decimal = Field(
        description=(
            "the MEASURED anchor — the amount the garage quoted, read off the event's own "
            "measured_value (unit=THB). Not derived, not modelled, not an exemplar."
        )
    )
    impact: EconomicImpact = Field(
        description=(
            "the typed Box-4 facet from the registered fleet producer — every DERIVED ฿ "
            "lives here, alongside the assumptions and basis_refs that disclose how it was "
            "reached. Required: the money never travels without its provenance."
        )
    )

    @model_validator(mode="after")
    def _money_travels_with_its_disclosure(self) -> FleetHeroImpact:
        """Reject a payload whose modelled ฿ has lost the assumptions that qualify it.

        The producer names its modelling inputs (`verticals/fleet_maintenance/
        economic_impact.py`), but nothing downstream forced them to survive. Without this,
        a refactor that dropped ``assumptions`` would still serve a 200 carrying a
        confident-looking ฿ figure with no statement that it was modelled at all — which
        is precisely the failure ADR-0030 D3's disclosure requirement exists to prevent.
        """
        if not self.impact.assumptions:
            raise ValueError(
                "impact.assumptions is empty — a modelled ฿ figure must ship the modelling "
                "inputs that produced it (ADR-0030 D3). An unqualified figure reads as "
                "measured data."
            )
        if self.impact.currency != self.currency:
            raise ValueError(
                f"currency mismatch: the payload declares {self.currency!r} but the "
                f"economic-impact facet is in {self.impact.currency!r}. Two currencies in "
                "one ledger is a rendering bug waiting to be believed."
            )
        return self


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
