"""PLAN-0042 Step 5 — the offline oracle: the three D8 red-team fixtures (LOCKED-8 / AC-14).

THE explicit, greppable D8 oracle for the AT-2 managerial layer (ADR-0025 D8): the three
adversarial fixtures, consolidated in one place so the offline merge gate reads as a unit.
Each fixture is self-contained here AND cross-references the dispersed coverage it
consolidates (the Step-2 gate tests in ``test_draft_lift_governance.py``; the Step-3
scoped-lint load gate in ``test_spec.py`` / ``test_prose_lint.py``). The LLM is not invoked —
zero host-state, no MS-S1 (CLAUDE.md §8).

  Fixture 1 — hollow-but-complete:  a skeleton that passes the OLD (pre-AT-2) gate but whose
              AT-2 content is ABSENT / MISMATCHED / SoD-less -> ``validate_governance_complete``
              REFUSES (the live blindness defect, now closed).
  Fixture 2 — leak-in-free-text:    a ฿-amount / weight / approver-role token smuggled into the
              waiver justification, a tier note, or a criterion note -> the scoped prose-lint
              BLOCKS LOAD (the control is the typed value, never the prose; D4).
  Fixture 3 — identity-collapse:    under A1 the author-time testable form is the role-level /
              structural collapse — a single-step SoD (rejected at construction) and a
              doa_tier procedure with no SoD (refused at the gate).
  AC-9       — un-gated-audit:      an ``autonomy: auto`` OPERATIONAL action downstream of a gate
              is refused at the run-loadability gate (ADR-0026 D6 hard guarantee 2 / Attack-5;
              PLAN-0044, Option 2), with a verified no-op audit-receipt handler (``echo``)
              exempt. Formerly A2-deferred here; now enforced in ``validate_governance_complete``.
              (The PRINCIPAL-level collapse now ships as LIVE run enforcement — ADR-0026 D4 /
              PLAN-0044 A1b Step 1, ``check_principal_sod`` — exercised in the principal-SoD run
              tests, not this author-time oracle. The literal ``approver_role == requester_role``
              check remains A2-deferred, intentionally NOT asserted here — no false coverage.)

PLAN-0074 Step 6 (AC-14) re-aims all three fixtures at the **4th gate kind** (``severity_tier`` /
``SeverityLadder`` — the 2nd AT-2 signature's NON-MONEY authority), in the section at the bottom.
That is not a copy: every guard above is written against ``DoaLadder`` / ``ScoredRule`` /
``ComplianceGate`` BY NAME (the obligation gate's ``_AT2_GATE_KINDS``, the prose-lint's role
vocabulary and free-text surface walker), so a new content model is precisely where these attacks
would silently stop applying. The re-run is the proof that the guards were EXTENDED, not left
blind — and fixture 3 there drives the LIVE principal-SoD check against the REAL shipped
supply_chain procedure, so a severity gate provably gets no weaker identity check than a money one.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from services.engine.procedures.orchestrator import ProcedureError, validate_governance_complete
from services.engine.procedures.principal_sod import check_principal_sod
from services.engine.procedures.spec import (
    Autonomy,
    ComplianceCriterion,
    ComplianceGate,
    ComplianceRule,
    DecisionCondition,
    DoaLadder,
    DoaTier,
    EmergencyWaiverPolicy,
    ExceptionPolicy,
    ExcursionSeverity,
    GateKind,
    Person,
    PrincipalAlias,
    Procedure,
    RelaxableConstraint,
    ScoredCriterion,
    ScoredRule,
    SeverityLadder,
    SeverityTier,
    SoDConstraint,
    SourcePolicy,
    Step,
    StepFacet,
    StepKind,
    load_procedures,
)

# the requester step (intake) must differ from the approver step (approve) — the author-time
# STRUCTURAL separation of duties (>=2 distinct steps; ADR-0025 D5, A1).
_SOD = [SoDConstraint(distinct_steps=frozenset({"intake", "approve"}))]

# Every AT-2 content variant a step may carry — including the PLAN-0074 `severity_tier` arm,
# so the fixtures can hand a SeverityLadder (or, adversarially, the WRONG variant) to a gate.
GovContent = DoaLadder | ScoredRule | ComplianceGate | SeverityLadder


def _gate_step(
    step_id: str,
    kind: StepKind,
    gate_kind: GateKind,
    *,
    handler: str | None = None,
    governance_content: GovContent | None = None,
) -> Step:
    """A step carrying a facet ``gate_kind`` (the discriminator the gate reads) + its typed
    AT-2 ``governance_content``."""
    return Step(
        step_id=step_id,
        name=step_id,
        kind=kind,
        handler=handler,
        governance_content=governance_content,
        facet=StepFacet(decision_condition=DecisionCondition(gate_kind=gate_kind)),
    )


def _at2_procedure(
    *,
    waiver_justification: str = "",
    tier_note: str = "",
    criterion_note: str = "",
    sod: list[SoDConstraint] | None = None,
    goal: str = "route the compliant set to the human approver",
    trailing_auto_handler: str | None = None,
) -> Procedure:
    """A fully-valid AT-2 procedure: the three AT-2 gate kinds (scored_rule / rule_gate /
    doa_tier) + a >=2-step SoD. Perturbable via the free-text kwargs (fixture 2), ``sod``
    (fixture 3), and ``trailing_auto_handler`` (fixture 3 / AC-9 — append an ``autonomy: auto``
    action AFTER the ``approve`` gate; an operational handler is the bypass, ``echo`` is the
    exempt no-op receipt). With no perturbation it loads AND passes the gate (the positive
    control)."""
    ladder = DoaLadder(
        currency="THB",
        tiers=[
            DoaTier(min_amount=Decimal("0"), approver_role="dept_head", note=tier_note),
            DoaTier(min_amount=Decimal("500000"), approver_role="director"),
        ],
        emergency_waiver=EmergencyWaiverPolicy(
            relaxes=[RelaxableConstraint.THREE_BID],
            escalate_to="director",
            justification=waiver_justification,
        ),
    )
    scored = ScoredRule(
        criteria=[ScoredCriterion(name="price", weight=Decimal("1"), note=criterion_note)],
        default_source=SourcePolicy.ON_CONTRACT,
        exception_policy=ExceptionPolicy.RFQ_AVL_LOGGED,
    )
    gate = ComplianceGate(
        rules=[ComplianceRule(criterion=ComplianceCriterion.AVL, spec="supplier on the AVL")]
    )
    steps = [
        Step(step_id="intake", name="Intake", kind=StepKind.QUERY),
        _gate_step(
            "source",
            StepKind.ACTION,
            GateKind.SCORED_RULE,
            handler="emergency_source",
            governance_content=scored,
        ),
        _gate_step("compliance", StepKind.EVALUATE, GateKind.RULE_GATE, governance_content=gate),
        _gate_step(
            "approve",
            StepKind.ACTION,
            GateKind.DOA_TIER,
            handler="request_approval",
            governance_content=ladder,
        ),
    ]
    if trailing_auto_handler is not None:
        # an autonomy:auto action AFTER the approve gate — the AC-9 surface (gate_kind none;
        # governance-complete since a handler is set, so AC-9 is the check that fires).
        steps.append(
            Step(
                step_id="audit",
                name="Audit",
                kind=StepKind.ACTION,
                autonomy=Autonomy.AUTO,
                handler=trailing_auto_handler,
            )
        )
    return Procedure(
        procedure_id="emergency",
        title="Emergency",
        run_by="a",
        goal=goal,
        steps=steps,
        separation_of_duties=_SOD if sod is None else sod,
    )


def _doa_only_procedure(*, content: GovContent | None, sod: list[SoDConstraint]) -> Procedure:
    """A minimal doa_tier procedure (intake + a doa_tier approval) with a perturbable
    ``content`` on the approval step — fixture 1's hollow / wrong-variant cases."""
    return Procedure(
        procedure_id="p",
        title="P",
        run_by="a",
        steps=[
            Step(step_id="intake", name="Intake", kind=StepKind.QUERY),
            _gate_step(
                "approve",
                StepKind.ACTION,
                GateKind.DOA_TIER,
                handler="request_approval",
                governance_content=content,
            ),
        ],
        separation_of_duties=sod,
    )


# --- the positive control: a fully-authored AT-2 procedure loads + passes the gate ----------


def test_d8_valid_at2_procedure_loads_and_passes_gate() -> None:
    """The control: a fully-authored AT-2 procedure (typed content on all three AT-2 gates, a
    >=2-step SoD, clean free-text) loads AND passes ``validate_governance_complete`` — so the
    three fixtures isolate the defect, not an over-strict gate."""
    validate_governance_complete(_at2_procedure())  # no raise


# --- D8 fixture 1 — hollow-but-complete (the closed live blindness defect; AC-9) ------------


def test_d8_fixture1_hollow_missing_content_refused() -> None:
    """handler + autonomy filled, gate_kind set, but ``governance_content`` ABSENT -> refused.
    Consolidates ``test_draft_lift_governance.test_hollow_at2_missing_content_is_refused``."""
    with pytest.raises(ProcedureError, match="governance_content"):
        validate_governance_complete(_doa_only_procedure(content=None, sod=_SOD))


def test_d8_fixture1_wrong_variant_refused() -> None:
    """A present-but-mismatched variant (a ScoredRule on a doa_tier step) -> refused (the D4
    gate_kind <-> content.kind correspondence).

    PLAN-0074 AC-16 moved this refusal to LOAD: the mismatched procedure is now unconstructable
    (a pydantic ValidationError from ``Procedure``), rather than constructable-but-refused by the
    run gate. Strictly stronger — the authoring error surfaces where it is made."""
    wrong = ScoredRule(
        criteria=[ScoredCriterion(name="price", weight=Decimal("1"))],
        default_source=SourcePolicy.ON_CONTRACT,
        exception_policy=ExceptionPolicy.RFQ_AVL_LOGGED,
    )
    with pytest.raises(ValidationError, match="governance_content"):
        _doa_only_procedure(content=wrong, sod=_SOD)


# --- D8 fixture 2 — leak-in-free-text (the scoped prose-lint blocks load; AC-11) ------------

_LEAK_SURFACE = {
    "waiver": "waiver_justification",
    "tier": "tier_note",
    "criterion": "criterion_note",
}


@pytest.mark.parametrize(
    "surface, leak",
    [
        ("waiver", "waive only above ฿50,000"),  # a currency amount in the waiver justification
        ("waiver", "the spend cap is 2M baht"),  # a magnitude amount in the waiver justification
        ("tier", "weight this tier at 0.5 of the score"),  # a weight (decimal) in a tier note
        ("tier", "always route to director on a breach"),  # an approver-role token in a tier note
        ("criterion", "this is 80% of the decision"),  # a percentage in a criterion note
        ("criterion", "escalate straight to director here"),  # a role token in a criterion note
    ],
)
def test_d8_fixture2_leak_in_free_text_blocks_load(surface: str, leak: str) -> None:
    """A ฿-amount / weight / magnitude / percent / approver-role token smuggled into the waiver
    justification, a tier note, or a criterion note BLOCKS LOAD (the scoped prose-lint, D4) —
    the dedicated free-text fields, complementing the description / goal surfaces covered in
    ``test_spec.py``. The control is the typed value, never the prose."""
    fields = {"waiver_justification": "", "tier_note": "", "criterion_note": ""}
    fields[_LEAK_SURFACE[surface]] = leak
    with pytest.raises(ValidationError, match="smuggles a governance value"):
        _at2_procedure(
            waiver_justification=fields["waiver_justification"],
            tier_note=fields["tier_note"],
            criterion_note=fields["criterion_note"],
        )


def test_d8_fixture2_clean_free_text_loads() -> None:
    """The control for fixture 2: hand-authored notes WITHOUT a smuggled value load fine — the
    scoped variant does not over-flag (a decision verb / handler name in a note is legitimate)."""
    _at2_procedure(
        waiver_justification="HUMAN approves the waiver; never skips a gate",
        tier_note="the department-head tier; escalates above the band",
        criterion_note="the on-contract preference, summarised by the LLM",
    )  # no raise


# --- D8 fixture 3 — identity-collapse + un-gated-audit (A1 author-time form; AC-9) ----------


def test_d8_fixture3_single_step_sod_rejected_at_construction() -> None:
    """A single-step SoD (requester == approver — the role-level identity collapse) is
    structurally unrepresentable: ``SoDConstraint`` requires >=2 distinct steps, so it is
    rejected at construction (the bypass cannot even be authored)."""
    with pytest.raises(ValidationError):
        SoDConstraint(distinct_steps=frozenset({"approve"}))


def test_d8_fixture3_doa_procedure_missing_sod_refused() -> None:
    """A doa_tier procedure with NO SoD cannot separate requester from approver -> refused at
    the gate (D5). Consolidates
    ``test_draft_lift_governance.test_doa_procedure_missing_sod_is_refused``."""
    with pytest.raises(ProcedureError, match="separation_of_duties"):
        validate_governance_complete(_at2_procedure(sod=[]))


# --- AC-9 — the un-gated-audit guarantee (`autonomy: auto` forbidden downstream of a gate) ---
# (ADR-0026 D6 hard guarantee 2 / red-team Attack-5; PLAN-0044 A1b, Option 2). Formerly A2-deferred
# in this file's fixture-3 note — now IMPLEMENTED in `validate_governance_complete`.


def test_ac9_auto_operational_action_downstream_of_gate_refused() -> None:
    """An `autonomy: auto` OPERATIONAL action (a real handler) downstream of the `approve`
    gate is a bypass surface — it would act un-attended after the human gate — so it is REFUSED
    at the run-loadability gate (ADR-0026 D6 hard guarantee 2 / Attack-5)."""
    with pytest.raises(ProcedureError, match="downstream of a gate"):
        validate_governance_complete(_at2_procedure(trailing_auto_handler="issue_po"))


def test_ac9_auto_audit_receipt_downstream_of_gate_allowed() -> None:
    """Option 2 exemption: the SAME shape but the auto step's handler is the verified no-op
    audit receipt (`echo`) — it records, it does not act — so it PASSES the gate. The exemption
    is tied to the handler name, not an author flag (route an operational action through `echo`
    and you get a no-op)."""
    validate_governance_complete(_at2_procedure(trailing_auto_handler="echo"))  # no raise


def test_ac9_shipped_procurement_procedure_passes() -> None:
    """The AC-9 regression guard on the SHIPPED authored content: the procurement
    `emergency_sourcing_round` (its `audit` step is `autonomy: auto` + `handler: echo`,
    downstream of the `approve`/`issue_po` gates) is exempt and loads run-loadable — so an edit
    that flipped the audit terminal to an operational auto handler after a gate would be caught."""
    spec = load_procedures("procurement")
    proc = next(p for p in spec.procedures if p.procedure_id == "emergency_sourcing_round")
    validate_governance_complete(proc)  # no raise — the auto echo audit terminal is exempt


# NOTE (STILL A2-deferred, AC-13-ALT — intentionally NOT asserted, no false coverage): the
# PRINCIPAL-level collapse (the SoD's two roles resolving to a single human) and the literal
# `approver_role == requester_role` check remain RUN-time checks. The principal-collapse check
# now ships as the LIVE run enforcement (ADR-0026 D4 / PLAN-0044 A1b Step 1, `check_principal_sod`)
# — exercised in the principal-SoD run tests, not this author-time oracle.


# ============================================================================================
# PLAN-0074 Step 6 (AC-14) — the SAME D8 oracle, aimed at the 4th gate kind (`severity_tier`)
# ============================================================================================
#
# The 2nd AT-2 signature added a gate kind with a NON-MONEY authority (`SeverityLadder`, an
# ordinal severity ladder — supply_chain's cold-chain disposition). A new typed content model is
# exactly where the D8 attacks silently stop applying: every guard above is written against
# DoaLadder / ScoredRule / ComplianceGate by NAME (`isinstance` in the obligation gate, in the
# prose-lint's role vocabulary, in the free-text surface walker). So the three fixtures are
# re-run against the new model — not as a copy, but as the proof that the guards were EXTENDED
# rather than left silently blind to it (the three governance holes PLAN-0074 closed).
#
# Fixture 1 — hollow-but-complete:  a severity_tier gate with ABSENT / WRONG-VARIANT content, a
#             structurally invalid ladder (empty / non-covering / non-monotonic tiers), or no SoD
#             -> REFUSED (at construction, or by `validate_governance_complete`).
# Fixture 2 — leak-in-free-text:    a severity/role token smuggled into a SeverityTier note or the
#             AT-2 step description -> the scoped prose-lint BLOCKS LOAD.
# Fixture 3 — identity-collapse:    the LIVE principal-SoD run-check, driven against the REAL
#             SHIPPED disposition procedure — two roles resolving to one human (by PK or by a
#             declared alias), or an approver who does not hold the required role, is NOT governed.


def _severity_ladder(*, tier_note: str = "") -> SeverityLadder:
    """A valid severity ladder: total-cover from the lowest severity, strictly-increasing ordinal
    floors. ``tier_note`` is the fixture-2 free-text surface."""
    return SeverityLadder(
        tiers=[
            SeverityTier(
                min_severity=ExcursionSeverity.NEGLIGIBLE,
                approver_role="qa_officer",
                note=tier_note,
            ),
            SeverityTier(min_severity=ExcursionSeverity.MAJOR, approver_role="qp_release"),
        ]
    )


def _severity_procedure(
    *,
    content: GovContent | None = None,
    hollow: bool = False,
    sod: list[SoDConstraint] | None = None,
    description: str = "route the disposition to the human quality authority",
    tier_note: str = "",
) -> Procedure:
    """A minimal severity_tier procedure (intake + a severity_tier approval). Unperturbed it loads
    AND passes the gate — the positive control that keeps the fixtures below honest.

    ``hollow=True`` strips the governance_content entirely (fixture 1's empty-gate attack) — a
    distinct knob from ``content`` (which SUBSTITUTES a variant), because "absent" and "wrong" are
    two different attacks and must not be conflated by the fixture itself."""
    governance_content = None if hollow else (content or _severity_ladder(tier_note=tier_note))
    approve = _gate_step(
        "approve",
        StepKind.ACTION,
        GateKind.SEVERITY_TIER,
        handler="request_approval",
        governance_content=governance_content,
    )
    return Procedure(
        procedure_id="disposition",
        title="Disposition",
        run_by="a",
        goal="dispose of the affected batch under the quality authority its severity demands",
        steps=[
            Step(step_id="intake", name="Intake", kind=StepKind.QUERY),
            approve.model_copy(update={"description": description}),
        ],
        separation_of_duties=_SOD if sod is None else sod,
    )


def test_d8_severity_valid_procedure_loads_and_passes_gate() -> None:
    """The control for the new model: a fully-authored severity_tier procedure (typed ladder +
    a >=2-step SoD + clean free-text) loads AND passes ``validate_governance_complete`` — so the
    fixtures below isolate the defect, not an over-strict gate."""
    validate_governance_complete(_severity_procedure())  # no raise


# --- fixture 1 — hollow-but-complete (the obligation gate SEES the new kind) -----------------


def test_d8_severity_fixture1_hollow_missing_content_refused() -> None:
    """The hole PLAN-0074 Step 2 closed: a severity_tier gate with NO governance_content. Had
    ``_AT2_GATE_KINDS`` not grown, this skeleton would owe nothing and the gate would ACCEPT an
    empty authority gate — a procedure that looks governed and authorises nobody."""
    with pytest.raises(ProcedureError, match="governance_content"):
        validate_governance_complete(_severity_procedure(hollow=True, sod=_SOD))


def test_d8_severity_fixture1_wrong_variant_refused() -> None:
    """A severity_tier gate carrying the WRONG typed variant (a money ladder) — the exact
    confusion the 4th kind exists to prevent — is refused: the content's ``kind`` discriminator
    must match the step's gate kind."""
    money = DoaLadder(
        currency="THB",
        tiers=[DoaTier(min_amount=Decimal("0"), approver_role="dept_head")],
        emergency_waiver=EmergencyWaiverPolicy(
            relaxes=[RelaxableConstraint.THREE_BID], escalate_to="director"
        ),
    )
    with pytest.raises(ValidationError, match="governance_content"):
        _severity_procedure(content=money)


def test_d8_severity_fixture1_missing_sod_refused() -> None:
    """A severity_tier procedure with NO separation_of_duties is refused (PLAN-0074 Step 2): the
    new authority kind owes SoD exactly as doa_tier does — a human authority gate whose requester
    may also be its approver is not a gate."""
    with pytest.raises(ProcedureError, match="separation_of_duties"):
        validate_governance_complete(_severity_procedure(sod=[]))


@pytest.mark.parametrize(
    ("tiers", "why"),
    [
        ([], "an EMPTY ladder authorises nobody"),
        (
            [SeverityTier(min_severity=ExcursionSeverity.MINOR, approver_role="qa_officer")],
            "a ladder that does not cover the LOWEST severity leaves a severity unrouted",
        ),
        (
            [
                SeverityTier(min_severity=ExcursionSeverity.NEGLIGIBLE, approver_role="qa_officer"),
                SeverityTier(min_severity=ExcursionSeverity.NEGLIGIBLE, approver_role="qp_release"),
            ],
            "DUPLICATE floors make the routing ambiguous (two approvers for one severity)",
        ),
        (
            [
                SeverityTier(min_severity=ExcursionSeverity.NEGLIGIBLE, approver_role="qa_officer"),
                SeverityTier(min_severity=ExcursionSeverity.CRITICAL, approver_role="qp_release"),
                SeverityTier(min_severity=ExcursionSeverity.MINOR, approver_role="qa_manager"),
            ],
            "NON-MONOTONIC floors would let a worse excursion route to a lower authority",
        ),
    ],
)
def test_d8_severity_fixture1_structurally_hollow_ladder_rejected(
    tiers: list[SeverityTier], why: str
) -> None:
    """A ladder that is *present* but structurally hollow is unrepresentable — rejected at
    CONSTRUCTION (the total-cover + strict-monotonicity validator), so it can never reach a run.
    This is the ordinal analog of DoaLadder's floor-at-zero + strictly-increasing invariant."""
    with pytest.raises(ValidationError):
        SeverityLadder(tiers=tiers)


@pytest.mark.parametrize(
    "facet",
    [
        # the CONTRADICTION half: a facet declaring `none` while carrying a severity ladder.
        StepFacet(decision_condition=DecisionCondition(gate_kind=GateKind.NONE)),
        # the OMISSION half (the s131 review finding — the dangerous direction the first version
        # missed): NO facet at all. The obligation gate keys on the facet, so a facet-less gate
        # owes neither content NOR SoD; the run dispatches on the content type, so it gates anyway
        # — an authority gate invisible to every facet reader, with no separation of duties.
        None,
    ],
)
def test_d8_ac16_severity_content_without_a_matching_facet_is_refused_at_load(
    facet: StepFacet | None,
) -> None:
    """AC-16: a step CARRYING a severity ladder whose facet does not declare `severity_tier` — by
    contradiction (`gate_kind: none`) or by omission (no facet) — is refused at LOAD. A gate no
    facet reader can see is a smuggled control: the obligation gate would owe nothing (no content,
    no SoD) while the run resolves the ladder and routes an approver anyway. Both halves are now
    unrepresentable, so the fixture builds the procedure with NO separation_of_duties to prove the
    load validator — not a downstream SoD check — is what refuses it."""
    smuggled = Step(
        step_id="approve",
        name="approve",
        kind=StepKind.ACTION,
        handler="request_approval",
        governance_content=_severity_ladder(),
        facet=facet,
    )
    with pytest.raises(ValidationError, match="governance_content"):
        Procedure(
            procedure_id="smuggled",
            title="Smuggled",
            run_by="a",
            steps=[Step(step_id="intake", name="Intake", kind=StepKind.QUERY), smuggled],
            separation_of_duties=[],  # NONE — the load validator must fire on its own
        )


# --- fixture 2 — leak-in-free-text (the prose-lint SEES the new model's surfaces) ------------


@pytest.mark.parametrize(
    ("surface", "leak"),
    [
        ("tier_note", "escalate anything at or above qp_release"),  # an approver-ROLE token
        ("tier_note", "the tolerance is 24 degree-hours"),  # a NUMERIC authority value
        ("description", "route to qp_release when the budget is spent"),  # role token in prose
        ("description", "escalate above 24 degree-hours of dose"),  # numeric in prose
    ],
)
def test_d8_severity_fixture2_leak_in_free_text_blocks_load(surface: str, leak: str) -> None:
    """The hole PLAN-0074 Step 1 closed: ``_at2_role_vocab`` / ``_at2_free_text_surfaces`` were
    hardcoded to ``DoaLadder | ScoredRule``, so a SeverityLadder's notes were INVISIBLE to the
    scoped prose-lint — an approver-ROLE token or a NUMERIC authority value could be smuggled
    into the prose a human then copies into the typed field (ADR-0025 D4 leak class 1). Now the
    surfaces are scanned and those value classes block load. (The ordinal severity WORD itself
    is DELIBERATELY not denylisted — see the ordinal-word pin test below.)
    """
    with pytest.raises(ValidationError, match="smuggles a governance value"):
        if surface == "tier_note":
            _severity_procedure(tier_note=leak)
        else:
            _severity_procedure(description=leak)


def test_d8_severity_fixture2_clean_free_text_loads() -> None:
    """The control: prose that names no role token and no authority value loads fine — the lint
    is scoped (it is not banning ordinary governance language)."""
    _severity_procedure(
        tier_note="a drift well inside the cargo's budget — the quality officer dispositions it",
        description="route the disposition to the human quality authority the severity demands",
    )


def test_d8_severity_fixture2_ordinal_word_is_deliberately_not_denylisted() -> None:
    """A DELIBERATE, recorded gap (PLAN-0074 Step-1 call, re-affirmed under s131 review): the scoped
    prose-lint does NOT flag the ordinal severity WORD (``critical`` / ``major`` / ...) in a note.
    Unlike a role token (a domain-specific string) or a ฿ amount (a number), a severity word is
    ordinary English with a dual meaning — 'a critical excursion' is normal prose — so denylisting
    it globally false-positives so hard an author cannot write a goal. The typed ``min_severity``
    field is the single source of truth and the run gate is the backstop (a word in an unread
    note is inert), so the residual is acceptable. This test PINS the choice so it is a
    documented gap, not a silent one — flip it the day a closed-ordinal-word scan proves
    feasible."""
    # a tier note naming the ordinal word loads (NOT blocked) — the run-gate-backstopped residual
    _severity_procedure(tier_note="reserved for a critical excursion that has spent its budget")


# --- fixture 3 — identity-collapse (the LIVE run check, on the REAL shipped procedure) -------


def _shipped_disposition() -> tuple[Procedure, list[Person]]:
    """The REAL supply_chain disposition + its REAL principals — the fixtures below attack what
    actually ships, not a synthetic stand-in."""
    spec = load_procedures("supply_chain")
    proc = next(p for p in spec.procedures if p.procedure_id == "cold_chain_excursion_disposition")
    return proc, list(spec.principals)


def test_d8_severity_fixture3_governed_control() -> None:
    """The control: the shipped disposition, with the requester and the severity-resolved approver
    as DISTINCT humans holding their required roles, IS governed."""
    proc, principals = _shipped_disposition()
    verdict = check_principal_sod(
        proc,
        principals=principals,
        principal_aliases=[],
        step_principals={"intake": "req-coldchain", "approve": "appr-qdir"},
    )
    assert verdict.governed is True


@pytest.mark.parametrize(
    ("step_principals", "aliases", "why"),
    [
        (
            {"intake": "req-coldchain", "approve": "req-coldchain"},
            [],
            "PK collapse — one human both raises the excursion and dispositions it",
        ),
        (
            {"intake": "req-coldchain", "approve": None},
            [],
            "an UNRESOLVED approver never gets waved through",
        ),
        (
            {"intake": "req-coldchain", "approve": "appr-qa"},
            [
                PrincipalAlias(
                    alias_id="same-human", members=frozenset({"req-coldchain", "appr-qa"})
                )
            ],
            "ALIAS collapse — two ids declared to be the same human",
        ),
    ],
)
def test_d8_severity_fixture3_identity_collapse_is_not_governed(
    step_principals: dict[str, str | None], aliases: list[PrincipalAlias], why: str
) -> None:
    """The LIVE fail-closed run-check (ADR-0026 D4) on the shipped severity_tier procedure: a
    two-into-one collapse (by PK or by declared alias) or an unresolvable approver yields NO
    governed verdict — and the gate's caller (``action_step._check_principal_sod``) raises rather
    than approving. A severity gate does not get a weaker identity check than a money gate."""
    proc, principals = _shipped_disposition()
    verdict = check_principal_sod(
        proc,
        principals=principals,
        principal_aliases=aliases,
        step_principals=step_principals,
    )
    assert verdict.governed is False, why
    assert verdict.violations, "a refusal must say WHY (the structured violation trail)"


def test_d8_severity_fixture3_wrong_role_is_not_governed() -> None:
    """The requester cannot be laundered into the approver slot by identity alone: the approving
    Person must HOLD the role the SoD constraint binds to ``approve`` (`approver`). req-coldchain
    holds only `requester`, so resolving it there fails closed on the ROLE — not merely on the
    two-into-one collapse."""
    proc, principals = _shipped_disposition()
    verdict = check_principal_sod(
        proc,
        principals=principals,
        principal_aliases=[],
        step_principals={"intake": "appr-qa", "approve": "req-coldchain"},
    )
    assert verdict.governed is False


# --- F3 (PLAN-0075 AC-5) — an AT-2 AUTHORITY step must be a GATED action -----------------------
# An auto authority step never reaches the human gate, so the tier-authority run-check (which
# lives only at resolve_gated_step) never fires — a one-word gated->auto flip on the very step the
# control hangs on (ADR-016 SP-1). The load-time check makes it unrepresentable.


def test_f3_shipped_gated_authority_step_loads() -> None:
    """Positive control: a valid AT-2 procedure whose doa_tier ``approve`` is a GATED action
    passes validate_governance_complete (so the negatives below are not vacuous)."""
    validate_governance_complete(_at2_procedure())  # no raise
    validate_governance_complete(_severity_procedure())  # the severity_tier surface too


def test_f3_auto_doa_authority_step_is_refused_at_load() -> None:
    """S1: an auto doa_tier ``approve`` fails load via F3 specifically — the step is the ONLY gate
    (intake + approve), so the sibling auto-downstream-of-a-gate guard does NOT fire; F3 is what
    catches it. This is F3's unique contribution: an auto authority step with no prior gate."""
    proc = _at2_procedure()
    intake = next(s for s in proc.steps if s.step_id == "intake")
    approve = next(s for s in proc.steps if s.step_id == "approve")
    bad = proc.model_copy(
        update={"steps": [intake, approve.model_copy(update={"autonomy": Autonomy.AUTO})]}
    )
    with pytest.raises(ProcedureError, match="not a GATED action"):
        validate_governance_complete(bad)


def test_f3_auto_severity_authority_step_is_refused_at_load() -> None:
    """S3: the same for a severity_tier disposition ``approve`` flipped to auto."""
    proc = _severity_procedure()
    steps = [
        s.model_copy(update={"autonomy": Autonomy.AUTO}) if s.step_id == "approve" else s
        for s in proc.steps
    ]
    bad = proc.model_copy(update={"steps": steps})
    with pytest.raises(ProcedureError, match="not a GATED action"):
        validate_governance_complete(bad)
