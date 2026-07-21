"""PLAN-0074 AC-11 — the ADR-0025 D7 AT-2-generator re-trigger (this PLAN owns the marker).

ADR-0025 D7 defers the **AT-2 generator** (the generator ships AT-1 only and ABSTAINS on
AT-2-class narratives) on an explicit Rule-of-Three argument: at N=1 there was exactly ONE
governance-heavy instance to generalise from, and a generator extracted from a single instance
generalises that instance's accidents (procurement's money authority, its vendor-hygiene criteria,
its emergency waiver) into the engine. The deferral is not a silent ``# TODO`` that rots under
delivery pressure — ADR-0031 OQ-4 assigned this marker to the PLAN that adds the 2nd signature.
This module is it:

* it counts **distinct AT-2 SIGNATURES** shipped across ``verticals/*/procedures.yaml``, and
* it **FAILS when a THIRD appears** — forcing the AT-2-generator deferral to be re-argued rather
  than accreting a third hand-authored copy in silence.

**Signatures, not procedure entries (the counting trap this marker exists to avoid).** Procurement
ships THREE AT-2 procedure entries — ``emergency_sourcing_round`` plus its schedule- and
event-triggered variants — but they are the SAME governance signature fired three ways (the
archetype catalog says so explicitly: "the schedule-triggered variant is the same archetype, not a
second instance", ``docs/conventions/procedure-archetypes.md``). A naive per-entry count would read
N>=3 today and fire this marker on a vertical that taught us nothing new about AT-2. The dedup key
(Code judgment, PLAN-0074 AC-11 — veto-open) is therefore:

    (vertical, the ordered tuple of the procedure's AT-2 gate kinds)

— the vertical (a signature is a vertical's governance shape) and WHICH gates it composes, in step
order. Procurement's three entries all key to ``("procurement", ("scored_rule", "rule_gate",
"doa_tier"))``; supply_chain's disposition keys to ``("supply_chain", ("scored_rule", "rule_gate",
"severity_tier"))`` — genuinely different, because its authority gate is NON-MONEY.

**N=2 REACHED — and the re-evaluation was performed, not deferred again (PLAN-0074 SD-3).** The
D7 re-trigger's whole point is that N>=2 forces the question. It was asked at this PLAN's review:

* **Resolution: the AT-2 generator STAYS deferred and abstaining; the D2 content types stay
  instance-scoped.** N>=2 *permits* genericization, it does not mandate it. What the second
  signature actually revealed is that the parts a generator would have to emit are still
  per-instance — the authority QUANTITY (baht spend vs excursion severity; ``DoaLadder`` cannot
  represent the latter, which is why a 4th gate kind exists at all), the compliance CRITERION
  vocabulary (vendor hygiene vs GDP/GxP), and even the scored-rule provenance policy
  (``SourcePolicy`` turned out NOT to be freely extensible — the run executor keys on the member
  itself, so a third member would invert a vertical's provenance). What DID
  generalise, unchanged, is the GATE SHAPE: a scored rule selects, a rule gate blocks, a tiered
  human gate authorises, SoD holds. That is a real finding, and it is the input to the follow-on
  genericization/gate-plugin-seam PLAN (ADR-0031 D3) — not something to bolt into a gate-kind PLAN.
* The generator's abstain guard grew to cover the new kind instead (``generator/pipeline.py``
  ``_AT2_ONLY_KINDS``, PLAN-0074 Step 3) — proven by ``test_generator_pipeline.py``.

**N=3 REACHED — re-evaluated again, not deferred in silence (PLAN-0081 Step 8, Cray SD-C).**
``building_materials.governed_credit_release`` (the governed-credit hero) shipped the 3rd
distinct signature. The re-trigger FIRED and the question was asked a second time:

* **Resolution: the AT-2 generator STAYS deferred and abstaining; the marker re-arms at N=4.**
  The 3rd signature is the WEAKEST possible extraction datum, so it does not disturb the N=2
  finding — it is the argument FOR staying deferred, not against. It introduces NO new gate kind
  and NO new authority quantity: it REUSES the money ``doa_tier`` ladder unchanged (THB and all),
  pairs it with a rule_gate whose composition is a strict SUBSET of procurement's (``rule_gate
  -> doa_tier``, no scored_rule), and grows only the criterion vocabulary (``ComplianceCriterion
  += {kyc, overdue_ar, blacklist}``) — the exact axis N=2 already established as per-instance
  forever. What DID generalise is again the GATE SHAPE (a rule gate blocks, a tiered human gate
  authorises, SoD holds).
* It also FIRES PLAN-0076 T1's own named trigger ("a third AT-2 signature fires the N=3
  re-trigger marker") — so the AT-2-generator / gate-plugin-seam extraction question now has a
  live owner (PLAN-0076 T1) and does not need this marker to force it. Rule-of-Three (ADR-006 D4)
  is honoured by the WEAKNESS of this datum, not violated: three hand-authored shapes, yes, but
  the third taught the engine nothing a generator could extract that the first two had not
  already shown to be per-instance.

So the marker re-armed at **N=4**: a fourth distinct signature would exhaust these two answers and
make the extraction due under Rule-of-Three.

**N=4 REACHED — and the deferral is CANCELLED, not re-armed a third time (PLAN-0086, Cray-ratified
2026-07-21).** ``fleet_maintenance.governed_repair_approval`` shipped the 4th distinct signature.
The re-trigger FIRED and the question was put to Cray with BOTH readings laid out, because this
firing is not like the two before it:

* **The reading that says fleet should NOT count.** By gate SHAPE fleet teaches nothing: its
  composition ``(rule_gate, doa_tier)`` is byte-identical to building_materials', its authority
  quantity is the same THB ``doa_tier``, and the only delta is one criterion (``three_quote``). By
  the N=3 wording above — "a genuinely NEW gate kind or authority quantity, not another
  criterion-vocabulary variant" — fleet is excluded. It is a strictly WEAKER datum than N=3, which
  was itself argued as the weakest possible.
* **The reading that won.** The marker's mechanical key counts the governed-enum SURFACE
  deliberately (the reviewer-F4 fix), and the surface is where the pressure actually shows: shipping
  fleet REQUIRED extending the closed shared ``ComplianceCriterion`` enum in engine code. That is
  **four consecutive verticals, four engine-level enum extensions**. The one thing that recurred in
  ALL FOUR instances is not a gate composition — it is the engine bending to admit an instance's
  vocabulary. Rule-of-Three is about repeated PRESSURE on shared code, and by that measure the
  evidence is now overwhelming rather than thin.

* **Resolution (Cray, typed, 2026-07-21): the AT-2-generator deferral is CANCELLED. The extraction
  is DUE.** Rationale as given: accept the cost now in exchange for future flexibility. The
  best-evidenced extraction is NOT "build an AT-2 generator" in the abstract — it is to stop
  requiring an engine edit per vertical (open / per-vertical criterion vocabulary), with the
  ADR-0031 D3 gate-plugin seam as the wider frame.
* **Owner: PLAN-0076 Step T1 (F-FACTORY)**, the standing owner of the gate-plugin-seam work
  (ADR-0031 D4.2). Its trigger is recorded as having pressed a second time, this time cancelling
  rather than re-arming. PLAN-0086 deliberately did NOT perform the extraction: it is a
  vertical-scaffold PLAN, and doing framework surgery inside it would have been both out of scope
  and destructive to its own measurement.
* Consequently the ``len(signatures) < _RETRIGGER_N`` guard is RETIRED (there is no threshold left
  to stay under) and REPLACED, never deleted, by
  :func:`test_at2_extraction_obligation_is_owned` — which fails if the owning PLAN is archived or
  loses its record of this firing. The census pin above stays armed for signature #5.

Pure-offline (no DB, no LLM, no MS-S1 — CLAUDE.md §8). The failing assertion is the deferral
SELF-CANCELLING, not a test bug.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from services.engine.procedures.orchestrator import _is_at2_procedure
from services.engine.procedures.spec import (
    ComplianceCriterion,
    ComplianceGate,
    ComplianceRule,
    DecisionCondition,
    DoaLadder,
    DoaTier,
    EmergencyWaiverPolicy,
    ExceptionPolicy,
    GateKind,
    Procedure,
    RelaxableConstraint,
    ScoredCriterion,
    ScoredRule,
    SourcePolicy,
    Step,
    StepFacet,
    StepKind,
    load_procedures_file,
)

_RETRIGGER_N = 4
"""The distinct-signature count at which the AT-2-generator deferral self-cancels (ADR-0025 D7).

**REACHED, and the deferral is CANCELLED** (PLAN-0086, Cray-ratified 2026-07-21). This constant is
retained as the historical threshold that fired; it no longer guards anything, because there is
nothing left to defer. The obligation it used to hold is now OWNED — see
:func:`test_at2_extraction_obligation_is_owned` and the module docstring's N=4 section."""

_OWNING_PLAN = Path("docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md")
"""The PLAN that owns the extraction now that the deferral has self-cancelled. PLAN-0076 Step T1
(F-FACTORY) is the standing owner of the gate-plugin-seam / AT-2-extraction work (ADR-0031 D4.2);
its trigger fired once at N=3 (recorded, deferral re-armed) and again at N=4 (recorded, deferral
CANCELLED). Kept as a path so the guard below fails if the PLAN is archived to ``done/`` while the
obligation is still open — an unowned obligation is exactly how a deferral rots."""

_BASELINE_SIGNATURES = [
    (
        "building_materials",
        ("rule_gate", "doa_tier"),
        (
            ("rule_gate", ("blacklist", "kyc", "overdue_ar")),
            ("doa_tier", ("THB",)),
        ),
    ),
    (
        "fleet_maintenance",
        ("rule_gate", "doa_tier"),
        (
            ("rule_gate", ("three_quote",)),
            ("doa_tier", ("THB",)),
        ),
    ),
    (
        "procurement",
        ("scored_rule", "rule_gate", "doa_tier"),
        (
            ("scored_rule", ("on_contract", "rfq_avl_logged")),
            ("rule_gate", ("avl", "cert", "sanctions", "single_source", "tax")),
            ("doa_tier", ("THB",)),
        ),
    ),
    (
        "supply_chain",
        ("scored_rule", "rule_gate", "severity_tier"),
        (
            ("scored_rule", ("deviation_quarantine_logged", "on_contract")),
            (
                "rule_gate",
                ("batch_quarantine", "coa_customs", "licensed_disposal_vendor", "stability_budget"),
            ),
            ("severity_tier", ("critical", "major", "minor", "negligible")),
        ),
    ),
]
"""The N=3 baseline the D7 re-evaluation was performed against (PLAN-0081 Step 8; sorted by
vertical, so building_materials leads). Three distinct signatures: the SHARED finding is that the
GATE COMPOSITION generalises while the per-instance surfaces do not. building_materials REUSES the
money ``doa_tier`` (THB) unchanged and pairs it with a rule_gate on a NEW criterion vocabulary
(credit: blacklist/kyc/overdue_ar) — no scored_rule, a strictly SIMPLER shape than procurement's,
which is exactly why it is the weakest extraction datum (no new gate kind, no new authority
quantity). Keying on the governed-enum SURFACE (not just the gate composition) is the reviewer-F4
fix: a procedure reusing an existing gate composition but pressing a NEW criterion/policy/severity
vocabulary would otherwise key identically to an existing signature and never trip the
re-trigger."""


def _at2_gate_kinds(procedure: Procedure) -> tuple[str, ...]:
    """The AT-2 gate kinds this procedure composes, in step order — the shape half of its
    signature. Read off the TYPED ``governance_content`` (the authoritative field), never the
    non-authoritative facet prose."""
    return tuple(
        step.governance_content.kind
        for step in procedure.steps
        if step.governance_content is not None
    )


def _content_enum_surface(procedure: Procedure) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """The GOVERNED-ENUM SURFACE each AT-2 content presses, per step — its kind plus the sorted
    closed-enum member VALUES it names (the reviewer-F4 discriminator). This is the D2 type-system
    footprint Rule-of-Three actually cares about: two procedures sharing a gate composition but
    naming different criteria / policies / severity floors are DIFFERENT signatures. Deliberately
    excludes free instance detail (weights, Thai role strings, tier count) so trigger variants of
    ONE signature — identical content — collapse to an identical surface and never over-split."""
    surface: list[tuple[str, tuple[str, ...]]] = []
    for step in procedure.steps:
        gc = step.governance_content
        if gc is None:
            continue
        if gc.kind == "rule_gate":
            members = tuple(sorted(rule.criterion.value for rule in gc.rules))
        elif gc.kind == "scored_rule":
            members = tuple(sorted((gc.default_source.value, gc.exception_policy.value)))
        elif gc.kind == "doa_tier":
            members = (gc.currency,)  # the money surface; a new currency = new pressure
        elif gc.kind == "severity_tier":
            members = tuple(sorted(tier.min_severity.value for tier in gc.tiers))
        else:
            members = ()
        surface.append((gc.kind, members))
    return tuple(surface)


def _distinct_at2_signatures() -> (
    list[tuple[str, tuple[str, ...], tuple[tuple[str, tuple[str, ...]], ...]]]
):
    """Every distinct AT-2 signature shipped, sorted. Globs only ``verticals/*`` (never the
    ``.claude/worktrees`` copies), and dedups trigger variants of one signature (see module
    docstring). A procedure that :func:`_is_at2_procedure` calls AT-2 but that carries no typed
    governance content (an SoD-only procedure) keys to an empty gate tuple — counted, but never
    silently merged with a gate-bearing one."""
    signatures: set[tuple[str, tuple[str, ...], tuple[tuple[str, tuple[str, ...]], ...]]] = set()
    for path in sorted(Path("verticals").glob("*/procedures.yaml")):
        vertical = path.parent.name
        spec = load_procedures_file(path, vertical=vertical)
        for procedure in spec.procedures:
            if _is_at2_procedure(procedure):
                signatures.add(
                    (vertical, _at2_gate_kinds(procedure), _content_enum_surface(procedure))
                )
    return sorted(signatures)


def test_trigger_variants_are_one_signature_not_three() -> None:
    """The counting trap, pinned: procurement ships THREE AT-2 procedure ENTRIES (manual +
    schedule- + event-triggered) that are ONE governance signature. A per-entry count would read
    N>=3 and false-fire the re-trigger below on a vertical that added no new AT-2 knowledge."""
    spec = load_procedures_file(
        Path("verticals/procurement/procedures.yaml"), vertical="procurement"
    )
    at2_entries = [p for p in spec.procedures if _is_at2_procedure(p)]
    assert len(at2_entries) == 3, "procurement's three AT-2 entries (manual / schedule / event)"

    signatures = {("procurement", _at2_gate_kinds(p)) for p in at2_entries}
    assert signatures == {("procurement", ("scored_rule", "rule_gate", "doa_tier"))}


def test_the_two_signatures_differ_in_their_authority_gate() -> None:
    """WHY N=2 is a real second data point (and not a copy): both signatures compose the same three
    gates, but the AUTHORITY gate differs — ``doa_tier`` (a Decimal spend) vs ``severity_tier`` (an
    ordinal excursion severity). That difference is the whole Rule-of-Three argument: a generator
    extracted from procurement alone would have baked "authority means money" into the engine."""
    gate_kinds = {vertical: kinds for vertical, kinds, _surface in _distinct_at2_signatures()}

    assert gate_kinds["procurement"][-1] == "doa_tier"
    assert gate_kinds["supply_chain"][-1] == "severity_tier"
    # everything upstream of the authority gate generalised unchanged
    assert gate_kinds["procurement"][:-1] == gate_kinds["supply_chain"][:-1]


def test_at2_generator_deferral_retrigger() -> None:
    """AC-11 (ADR-0025 D7 / ADR-0031 OQ-4): the AT-2 signature census, pinned.

    The deferral this marker used to guard is CANCELLED (N=4 reached, PLAN-0086) — so this test no
    longer asks "have we hit N yet". It still pins the CENSUS, because the next signature to ship
    must be argued against a current baseline, not a stale one. A moved baseline still means: stop,
    and re-argue what the new signature teaches."""
    signatures = _distinct_at2_signatures()
    assert signatures == _BASELINE_SIGNATURES, (
        "the AT-2 signature baseline moved — the D7 re-evaluation recorded in this module's "
        f"docstring was performed against {_BASELINE_SIGNATURES}, so it no longer holds. Re-argue "
        "it (do not just update this list)."
    )


def test_at2_extraction_obligation_is_owned() -> None:
    """The replacement for the retired ``len(signatures) < _RETRIGGER_N`` guard (PLAN-0086).

    N=4 fired and the deferral self-cancelled, so there is no longer a threshold to stay under —
    the extraction is DUE. What must not rot now is its OWNERSHIP. PLAN-0076 Step T1 (F-FACTORY) is
    the standing owner of the gate-plugin-seam / AT-2-extraction work; this guard fails if that
    PLAN is archived to ``done/`` (T1 discharged only on paper) or if its record of the N=4 firing
    is removed. A cancelled deferral with no owner is strictly worse than the deferral was."""
    assert _OWNING_PLAN.exists(), (
        f"{_OWNING_PLAN} is gone from docs/plans/ — the ADR-0025 D7 deferral was CANCELLED at N=4 "
        "(PLAN-0086, Cray-ratified 2026-07-21) and PLAN-0076 Step T1 owns the extraction that "
        "resulted. If T1 has genuinely been discharged by a landed gate-plugin-seam PLAN, re-home "
        "this guard onto that PLAN in the SAME change that archives this one — never delete it."
    )
    text = _OWNING_PLAN.read_text(encoding="utf-8")
    assert "N=4" in text, (
        f"{_OWNING_PLAN} no longer records the N=4 firing. Step T1's trigger pressed a SECOND time "
        "when fleet_maintenance shipped (PLAN-0086) and, unlike the N=3 pressing, that firing "
        "CANCELLED the deferral rather than re-arming it. That distinction is the whole reason the "
        "extraction is now due — it must stay written down."
    )


def _gate_step(
    step_id: str,
    kind: StepKind,
    gate: GateKind,
    content: DoaLadder | ScoredRule | ComplianceGate,
) -> Step:
    return Step(
        step_id=step_id,
        name=step_id,
        kind=kind,
        handler="request_approval" if kind is StepKind.ACTION else None,
        governance_content=content,
        facet=StepFacet(decision_condition=DecisionCondition(gate_kind=gate)),
    )


def _procurement_shaped_procedure(criteria: list[str]) -> Procedure:
    """A procurement-SHAPED AT-2 (scored_rule -> rule_gate -> doa_tier), parametrised by the
    rule_gate criterion vocabulary — the axis the reviewer's capex counterexample varies."""
    scored = ScoredRule(
        criteria=[ScoredCriterion(name="price", weight=Decimal("1"))],
        default_source=SourcePolicy.ON_CONTRACT,
        exception_policy=ExceptionPolicy.RFQ_AVL_LOGGED,
    )
    gate = ComplianceGate(
        rules=[ComplianceRule(criterion=ComplianceCriterion(c), spec="x") for c in criteria]
    )
    ladder = DoaLadder(
        currency="THB",
        tiers=[DoaTier(min_amount=Decimal("0"), approver_role="dept_head")],
        emergency_waiver=EmergencyWaiverPolicy(
            relaxes=[RelaxableConstraint.THREE_BID], escalate_to="director"
        ),
    )
    return Procedure(
        procedure_id="p",
        title="P",
        run_by="a",
        steps=[
            Step(step_id="intake", name="Intake", kind=StepKind.QUERY),
            _gate_step("source", StepKind.ACTION, GateKind.SCORED_RULE, scored),
            _gate_step("compliance", StepKind.EVALUATE, GateKind.RULE_GATE, gate),
            _gate_step("approve", StepKind.ACTION, GateKind.DOA_TIER, ladder),
        ],
    )


def test_f4_new_criteria_same_composition_is_a_distinct_signature() -> None:
    """The reviewer-F4 fix, PROVEN (not just asserted): a procedure that reuses the exact gate
    COMPOSITION (scored_rule -> rule_gate -> doa_tier) but presses a NEW criterion vocabulary is a
    DISTINCT signature. Keying on gate kinds ALONE (the old key) would collide them and the marker
    would stay silent at a genuine third hand-authored governance shape; the enum-surface
    fingerprint separates them, so the trip-wire fires."""
    existing = _procurement_shaped_procedure(["avl", "tax", "cert", "sanctions", "single_source"])
    capex = _procurement_shaped_procedure(["avl", "tax"])  # a different (smaller) criterion block

    # the OLD discriminator (gate kinds) collides — this is exactly the blindness F4 named
    assert _at2_gate_kinds(existing) == _at2_gate_kinds(capex)

    # the NEW discriminator (enum surface) separates them -> distinct signatures -> the marker fires
    assert _content_enum_surface(existing) != _content_enum_surface(capex)
    sig_existing = ("procurement", _at2_gate_kinds(existing), _content_enum_surface(existing))
    sig_capex = ("procurement", _at2_gate_kinds(capex), _content_enum_surface(capex))
    assert sig_existing != sig_capex
