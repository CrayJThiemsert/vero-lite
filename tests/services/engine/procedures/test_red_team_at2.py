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
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from services.engine.procedures.orchestrator import ProcedureError, validate_governance_complete
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
    GateKind,
    Procedure,
    RelaxableConstraint,
    ScoredCriterion,
    ScoredRule,
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

GovContent = DoaLadder | ScoredRule | ComplianceGate


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
    gate_kind <-> content.kind correspondence)."""
    wrong = ScoredRule(
        criteria=[ScoredCriterion(name="price", weight=Decimal("1"))],
        default_source=SourcePolicy.ON_CONTRACT,
        exception_policy=ExceptionPolicy.RFQ_AVL_LOGGED,
    )
    with pytest.raises(ProcedureError, match="governance_content"):
        validate_governance_complete(_doa_only_procedure(content=wrong, sod=_SOD))


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
