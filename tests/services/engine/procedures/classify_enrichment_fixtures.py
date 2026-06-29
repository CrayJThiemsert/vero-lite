"""PLAN-0041 Step 4 — the labelled classify-enrichment fixture set (OQ-C).

The ~26-narrative twin-metric set the Cray-gated live before/after run (Step 5 / AC-7)
measures the prompt-enrichment lever against. This module is **pure data** (no ``test_``
prefix → not collected): both the OFFLINE validators (``test_classify_enrichment_fixtures``)
and the LIVE A/B harness (``test_classify_enrichment_live``) import ``FIXTURES`` from here.

Two arms (OQ-C):

* **Arm A (lift)** — textbook AT-1-family narratives the live model should MATCH. AT-1 + AT-3
  are GATED (the ``after > before`` + ``≥ 9/11`` metric); AT-1b is **measured + reported but
  NOT gated** (OQ-E scope note — AT-1b's residual false-abstain is a per-step *guard*
  property a prompt-only lever cannot own).
* **Arm B (zero-regression, HARD)** — genuine AT-2-class narratives that must STILL
  ``Abstained``. Sourced from the catalog's own governance-signature language + the live
  ``procurement.emergency_sourcing_round`` (genuine AT-2, not strawmen). Includes ``≥ 2``
  *borderline* cases: an AT-1-looking anomaly→action that HIDES a per-criterion compliance
  gate or a DOA tier mid-flow — the realistic down-classification trap (R1).

Fixture hygiene (the two traps these narratives are written against):
  * a hand-authored fixture can MASK live behaviour — so the AT-2 narratives carry a real
    AT-2 governance signature phrased the way a stakeholder would, never a caricature;
  * the live model (``gpt-oss:20b``) never sees this file, but the borderline cases exist
    precisely so the set is not self-confirming. One live run (Step 5) is the cheapest catch.

The *expected* labels here are the pre-committed read; the route is computed live in Step 5
by the BYTE-IDENTICAL deterministic guard, never by string-matching this module.
"""

from __future__ import annotations

from dataclasses import dataclass

# the closed v1 route space (AT-1 family + abstain); AT-2 is absent by construction
EXPECTED_LABELS = frozenset({"AT-1", "AT-1b", "AT-3", "abstain"})


@dataclass(frozen=True)
class ClassifyFixture:
    """One labelled narrative + its pre-committed expected route.

    ``expected`` is the route the deterministic guard SHOULD produce; ``measured_only`` marks
    the AT-1b cases (reported, not gated — OQ-E); ``borderline`` marks the AT-1-looking AT-2
    down-classification traps (R1). ``arm`` is "A_lift" or "B_abstain"."""

    fixture_id: str
    arm: str
    expected: str
    narrative: str
    measured_only: bool = False
    borderline: bool = False


# --- Arm A (lift): textbook AT-1 — anomaly → judge(one band) → gated action on breach ------
_ARM_A_AT1: tuple[ClassifyFixture, ...] = (
    ClassifyFixture(
        "A-AT1-substation",
        "A_lift",
        "AT-1",
        "Every monitoring cycle, read each substation transformer's temperature, judge it "
        "against the over-temperature limit, and for any transformer above the limit propose "
        "a restart for an operator to review and approve before it runs.",
    ),
    ClassifyFixture(
        "A-AT1-coldchain",
        "A_lift",
        "AT-1",
        "On each sweep, read the current temperature of every in-transit refrigerated "
        "shipment, check it against the cold-chain ceiling, and when a shipment is above the "
        "ceiling propose placing it on hold for a dispatcher to confirm.",
    ),
    ClassifyFixture(
        "A-AT1-pond-do",
        "A_lift",
        "AT-1",
        "Each round, read the dissolved-oxygen level in every pond, judge it against the safe "
        "floor, and for any pond below the floor propose starting the emergency aerator, "
        "pending a farm-hand's go-ahead.",
    ),
    ClassifyFixture(
        "A-AT1-datacenter-humidity",
        "A_lift",
        "AT-1",
        "Sample each server rack's inlet humidity once per interval, compare it to the allowed "
        "band, and where a rack drifts out of band raise a proposed adjustment for a technician "
        "to approve.",
    ),
    ClassifyFixture(
        "A-AT1-water-chlorine",
        "A_lift",
        "AT-1",
        "Read the residual chlorine at each distribution node, evaluate it against the "
        "regulatory minimum, and for any node that falls below it propose a dosing correction "
        "for the duty operator to authorise.",
    ),
    ClassifyFixture(
        "A-AT1-turbine-vibration",
        "A_lift",
        "AT-1",
        "On every health pass, read each wind turbine's gearbox vibration, judge it against the "
        "alarm band, and when a turbine breaches it propose throttling that unit down for an "
        "engineer to confirm.",
    ),
)

# --- Arm A (lift): textbook AT-3 — monitor → judge(reorder point) → gated reorder -----------
_ARM_A_AT3: tuple[ClassifyFixture, ...] = (
    ClassifyFixture(
        "A-AT3-mro-parts",
        "A_lift",
        "AT-3",
        "Read the current stock level of each stocked part, compare it against that part's "
        "reorder point, and for every part at or below its reorder point propose an on-contract "
        "reorder for a buyer to approve.",
    ),
    ClassifyFixture(
        "A-AT3-pharmacy",
        "A_lift",
        "AT-3",
        "Each day, read the on-hand count for every medication, judge it against its par level, "
        "and where a medication is at or under par propose a replenishment order for the "
        "pharmacist to sign off.",
    ),
    ClassifyFixture(
        "A-AT3-storeroom",
        "A_lift",
        "AT-3",
        "Sweep the maintenance storeroom, read each SKU's quantity on hand, check it against the "
        "minimum, and for any SKU below the minimum propose a restock purchase for the storeroom "
        "lead to approve.",
    ),
    ClassifyFixture(
        "A-AT3-retail-shelf",
        "A_lift",
        "AT-3",
        "Pull the inventory position for each shelf item, compare it to its reorder threshold, "
        "and for items at or below it propose a replenishment order for the store manager to "
        "confirm.",
    ),
    ClassifyFixture(
        "A-AT3-fuel-depot",
        "A_lift",
        "AT-3",
        "Read the tank level for each fuel grade, judge it against the reorder point, and when a "
        "grade drops to or below it propose a resupply order for the depot supervisor to approve.",
    ),
)

# --- Arm A (measured-only): AT-1b — AT-1 + watch→gated proposal + auto summary terminal -----
_ARM_A_AT1B: tuple[ClassifyFixture, ...] = (
    ClassifyFixture(
        "A-AT1b-pond-full",
        "A_lift",
        "AT-1b",
        "Each morning, read the dissolved-oxygen in every pond; for ponds below the critical "
        "floor propose starting the emergency aerator, for ponds in the borderline watch zone "
        "propose increasing water exchange, and at the end emit an automatic round-summary "
        "receipt — both actions wait for a farm-hand's approval.",
        measured_only=True,
    ),
    ClassifyFixture(
        "A-AT1b-greenhouse",
        "A_lift",
        "AT-1b",
        "On each climate pass, read every zone's CO2; breach zones get a proposed venting "
        "action, borderline watch zones get a proposed minor adjustment for review, and an "
        "automatic end-of-pass summary is logged. Both proposals are human-approved.",
        measured_only=True,
    ),
    ClassifyFixture(
        "A-AT1b-coldstore",
        "A_lift",
        "AT-1b",
        "Read each freezer room's temperature; rooms above the hard ceiling get a proposed "
        "defrost-halt for approval, rooms in the watch margin get a proposed setpoint nudge for "
        "review, and the round closes with an automatic summary receipt.",
        measured_only=True,
    ),
    ClassifyFixture(
        "A-AT1b-grid-feeder",
        "A_lift",
        "AT-1b",
        "Each cycle, read every feeder's load; over-limit feeders get a proposed load-shed for "
        "an operator, near-limit feeders in the watch margin get a proposed advisory rebalance "
        "to review, and an automatic cycle summary is recorded.",
        measured_only=True,
    ),
)

# --- Arm B (HARD): AT-2 weighted-score sourcing — selection is a SCORED RULE ----------------
_ARM_B_SCORED: tuple[ClassifyFixture, ...] = (
    ClassifyFixture(
        "B-scored-emergency-source",
        "B_abstain",
        "abstain",
        "When a critical asset fails, gather the candidate suppliers for each needed part and "
        "score every supplier on a weighted blend of criticality, lead time, and unit price, "
        "then pick the highest-scoring supplier per item by that rule before raising the order.",
    ),
    ClassifyFixture(
        "B-scored-carrier-rank",
        "B_abstain",
        "abstain",
        "For each urgent shipment, rank the available carriers by a weighted score over transit "
        "time, on-time history, and cost, select the top-ranked carrier per lane by the score, "
        "and book it.",
    ),
    ClassifyFixture(
        "B-scored-bid-award",
        "B_abstain",
        "abstain",
        "Evaluate each bid against a weighted scorecard of technical fit, delivery date, and "
        "price, compute each bid's composite score, and award to the highest composite before "
        "raising the contract.",
    ),
)

# --- Arm B (HARD): AT-2 per-criterion compliance — a hard RULE GATE -------------------------
_ARM_B_COMPLIANCE: tuple[ClassifyFixture, ...] = (
    ClassifyFixture(
        "B-compliance-supplier-gate",
        "B_abstain",
        "abstain",
        "Before any emergency PO is raised, check each candidate supplier against every "
        "compliance criterion — approved-vendor-list status, valid tax id, current "
        "certification, sanctions clear, and single-source justified — and block the order if "
        "any criterion fails.",
    ),
    ClassifyFixture(
        "B-compliance-vendor-onboard",
        "B_abstain",
        "abstain",
        "Screen each new vendor against the full checklist: KYC complete, tax registration "
        "valid, insurance current, no sanctions hit, and conflict-of-interest cleared; any "
        "unmet item halts onboarding.",
    ),
    # BORDERLINE 1 — reads AT-1 (sense → flag → propose hold) but the RELEASE path is a hidden
    # per-criterion compliance RULE GATE → genuine AT-2 (R1 down-classification trap).
    ClassifyFixture(
        "B-borderline-lot-release",
        "B_abstain",
        "abstain",
        "Each cycle, read every incoming material lot, flag any lot that looks off-spec, and "
        "propose holding it — but before releasing any held lot, clear it against the full "
        "per-criterion compliance checklist (certification, tax id, sanctions, approved-vendor "
        "status), releasing only lots that pass every criterion.",
        borderline=True,
    ),
)

# --- Arm B (HARD): AT-2 tiered-DOA approval — an authority-tier (DOA) gate ------------------
_ARM_B_DOA: tuple[ClassifyFixture, ...] = (
    ClassifyFixture(
        "B-doa-tiered-purchase",
        "B_abstain",
        "abstain",
        "Route each approved-for-compliance purchase to the approver whose delegation-of-"
        "authority tier the order's amount requires, escalating to a higher authority as the "
        "amount climbs, with an emergency waiver that bumps the approver up and forces a written "
        "justification rather than skipping the approval.",
    ),
    ClassifyFixture(
        "B-doa-capex-signoff",
        "B_abstain",
        "abstain",
        "Send each capital request to the signing authority its value demands — team lead, "
        "department head, division VP, or the CFO as the amount rises — and require a written "
        "rationale at every escalation.",
    ),
    # BORDERLINE 2 — reads AT-1 (monitor → flag → propose repair) but the spend approval is a
    # hidden tiered-DOA gate → genuine AT-2 (R1 down-classification trap).
    ClassifyFixture(
        "B-borderline-repair-approval",
        "B_abstain",
        "abstain",
        "Monitor each maintenance request, flag the urgent ones, and propose a repair — but "
        "route the spend approval to the authority tier the repair cost demands, escalating "
        "larger repairs to higher sign-off before any work is ordered.",
        borderline=True,
    ),
)

# --- Arm B (HARD): AT-2 full hero — the 7-step governed acquisition -------------------------
_ARM_B_HERO: tuple[ClassifyFixture, ...] = (
    ClassifyFixture(
        "B-hero-emergency-sourcing",
        "B_abstain",
        "abstain",
        "A critical production-line asset has failed. Intake the maintenance request, judge each "
        "item's criticality against the band, source the critical items by a weighted scoring "
        "rule (on-contract by default, a logged RFQ exception otherwise), check each candidate "
        "against the per-criterion compliance gate that blocks the PO on any failure, route the "
        "compliant set to the tiered-DOA approver the amount demands with an escalate-never-skip "
        "emergency waiver and separation of duties, issue the PO on human approval, and write an "
        "audit record tying every decision to the control that governed it.",
    ),
    ClassifyFixture(
        "B-hero-stockout-acquisition",
        "B_abstain",
        "abstain",
        "On a stock-out emergency, enrich the requisition, rate each item's urgency against the "
        "threshold, select suppliers by the weighted sourcing rule, run the compliance checklist "
        "that hard-blocks non-conforming vendors, escalate the spend to the right authority tier "
        "under the delegation matrix with a documented waiver path, place the order once a human "
        "approves, and log a full traceable audit.",
    ),
)

FIXTURES: tuple[ClassifyFixture, ...] = (
    *_ARM_A_AT1,
    *_ARM_A_AT3,
    *_ARM_A_AT1B,
    *_ARM_B_SCORED,
    *_ARM_B_COMPLIANCE,
    *_ARM_B_DOA,
    *_ARM_B_HERO,
)
"""The full 26-narrative set: Arm A = 6 AT-1 + 5 AT-3 (gated) + 4 AT-1b (measured-only);
Arm B = 11 genuine AT-2 (HARD abstain), of which 2 are borderline."""
