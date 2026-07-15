"""Pure, offline tests for the AT-2 tier-authority run-check (PLAN-0075 Steps 2 + AC-1/2/3) and
its native-tier routing companion. No DB / LLM / network — the offline gate (CLAUDE.md §8)."""

from __future__ import annotations

from decimal import Decimal

from services.engine.procedures.spec import (
    DoaLadder,
    DoaTier,
    EmergencyWaiverPolicy,
    ExcursionSeverity,
    Person,
    RelaxableConstraint,
    SeverityLadder,
    SeverityTier,
)
from services.engine.procedures.tier_authority import (
    TierAuthorityViolationKind,
    check_tier_authority,
    native_approver,
)

# --- the procurement ladder + its CUMULATIVE principals (PLAN-0075, Cray s132) ----------------
# roles are cumulative: each tier holds its own role AND every lower tier's, so a senior may
# approve downward (enforcement) while native-tier routing still names the tier's own approver.
_BUYER = Person(person_id="appr-buyer", name="buyer", roles=["approver", "หน.จัดซื้อ"])
_PM = Person(person_id="appr-pm", name="pm", roles=["approver", "ผจก.จัดซื้อ", "หน.จัดซื้อ"])
_PLANT = Person(
    person_id="appr-plant",
    name="plant",
    roles=["approver", "ผจก.โรงงาน", "ผจก.จัดซื้อ", "หน.จัดซื้อ"],
)
_DIRECTOR = Person(
    person_id="appr-director",
    name="director",
    roles=["approver", "ผอ.", "ผจก.โรงงาน", "ผจก.จัดซื้อ", "หน.จัดซื้อ"],
)
_REQUESTER = Person(person_id="req-planner", name="planner", roles=["requester"])
_PRINCIPALS = [_BUYER, _PM, _PLANT, _DIRECTOR, _REQUESTER]

_LADDER = DoaLadder(
    currency="THB",
    tiers=[
        DoaTier(min_amount=Decimal("0"), approver_role="หน.จัดซื้อ"),
        DoaTier(min_amount=Decimal("50000"), approver_role="ผจก.จัดซื้อ"),
        DoaTier(min_amount=Decimal("500000"), approver_role="ผจก.โรงงาน"),
        DoaTier(min_amount=Decimal("2000000"), approver_role="ผอ."),
    ],
    emergency_waiver=EmergencyWaiverPolicy(
        relaxes=[RelaxableConstraint.THREE_BID], escalate_to="ผอ."
    ),
)


def _verdict(required_role: str, resolved: str | None = "appr-pm") -> dict[str, object]:
    """A persisted doa_tier verdict (the ``to_audit()`` shape the gate reads)."""
    return {"required_role": required_role, "resolved_approver_id": resolved}


# =============================================================== native_approver (routing)
def test_native_approver_non_cumulative_is_the_sole_holder() -> None:
    """With non-cumulative roles (the pre-PLAN-0075 authoring) the native holder is the sole one."""
    pm = Person(person_id="appr-pm", name="pm", roles=["approver", "ผจก.จัดซื้อ"])
    assert (
        native_approver("ผจก.จัดซื้อ", higher_roles=frozenset({"ผจก.โรงงาน", "ผอ."}), principals=[pm])
        == "appr-pm"
    )


def test_native_approver_excludes_cumulative_seniors() -> None:
    """The whole point (Cray s132): ผจก.จัดซื้อ routes to appr-pm even though appr-plant /
    appr-director ALSO hold it cumulatively — the audit names the tier's own approver, not a
    senior who merely may approve downward."""
    resolved = native_approver(
        "ผจก.จัดซื้อ", higher_roles=frozenset({"ผจก.โรงงาน", "ผอ."}), principals=_PRINCIPALS
    )
    assert resolved == "appr-pm"


def test_native_approver_top_tier_has_no_higher_roles() -> None:
    """The top tier (ผอ.) has an empty ``higher_roles`` — its native holder is the sole ผอ.
    holder."""
    assert (
        native_approver("ผอ.", higher_roles=frozenset(), principals=_PRINCIPALS) == "appr-director"
    )


def test_native_approver_none_when_nobody_holds_it() -> None:
    assert native_approver("ผอ.", higher_roles=frozenset(), principals=[_BUYER, _REQUESTER]) is None


def test_native_approver_falls_back_when_no_strictly_native_holder() -> None:
    """Degenerate authoring: every holder of the role ALSO holds a higher role (nobody is native)
    — fall back to the sorted-first holder rather than returning None (still routes to a holder)."""
    only_seniors = [_PLANT, _DIRECTOR]  # both hold ผจก.จัดซื้อ, both also hold higher roles
    resolved = native_approver(
        "ผจก.จัดซื้อ", higher_roles=frozenset({"ผจก.โรงงาน", "ผอ."}), principals=only_seniors
    )
    assert resolved == "appr-director"  # sorted-first fallback


# =============================================================== check_tier_authority (AC-1/2/3)
def test_inert_on_non_authority_content() -> None:
    """AC-1: a non-authority step (or no content) is vacuously governed — the check is safe to
    invoke unconditionally at the gate."""
    verdict = check_tier_authority(
        principal=_BUYER,
        step_id="approve",
        governance_content=None,
        persisted_verdicts=[],
        declared_principals=_PRINCIPALS,
    )
    assert verdict.governed is True
    assert verdict.violations == ()


def test_exact_tier_holder_passes() -> None:
    """AC-2: the ladder-resolved tier holder (appr-pm at ฿288k -> ผจก.จัดซื้อ) passes."""
    verdict = check_tier_authority(
        principal=_PM,
        step_id="approve",
        governance_content=_LADDER,
        persisted_verdicts=[_verdict("ผจก.จัดซื้อ")],
        declared_principals=_PRINCIPALS,
    )
    assert verdict.governed is True


def test_cumulative_senior_approves_downward() -> None:
    """AC-2 (the Cray-s132 Policy-B variant): a SENIOR (appr-director) holds ผจก.จัดซื้อ
    cumulatively, so they PASS the ฿288k gate — 'senior can approve downward'. This is the
    behaviour the cumulative role authoring exists to grant."""
    verdict = check_tier_authority(
        principal=_DIRECTOR,
        step_id="approve",
        governance_content=_LADDER,
        persisted_verdicts=[_verdict("ผจก.จัดซื้อ")],
        declared_principals=_PRINCIPALS,
    )
    assert verdict.governed is True


def test_junior_is_refused_upward() -> None:
    """AC-2: the bug this PLAN closes — appr-buyer (holds only หน.จัดซื้อ, the ฿0-50k tier)
    is REFUSED at the ฿288k gate the ladder routed to ผจก.จัดซื้อ. A lower tier cannot resolve a
    higher-tier gate."""
    verdict = check_tier_authority(
        principal=_BUYER,
        step_id="approve",
        governance_content=_LADDER,
        persisted_verdicts=[_verdict("ผจก.จัดซื้อ")],
        declared_principals=_PRINCIPALS,
    )
    assert verdict.governed is False
    assert [v.kind for v in verdict.violations] == [TierAuthorityViolationKind.TIER_ROLE_MISMATCH]
    assert verdict.violations[0].required_role == "ผจก.จัดซื้อ"


def test_missing_verdict_fails_closed() -> None:
    """AC-3: an authority step with NO persisted verdict is refused (the plain-executor bypass —
    an executor binding that skips the governance wrapper would otherwise pass silently)."""
    verdict = check_tier_authority(
        principal=_PM,
        step_id="approve",
        governance_content=_LADDER,
        persisted_verdicts=[],
        declared_principals=_PRINCIPALS,
    )
    assert verdict.governed is False
    assert [v.kind for v in verdict.violations] == [TierAuthorityViolationKind.VERDICT_MISSING]


def test_unknown_principal_fails_closed() -> None:
    """AC-9(3): an undeclared acting principal is refused independently of the SoD check (which is
    inert on a non-SoD authority gate)."""
    stranger = Person(person_id="ghost", name="ghost", roles=["approver", "ผจก.จัดซื้อ"])
    verdict = check_tier_authority(
        principal=stranger,
        step_id="approve",
        governance_content=_LADDER,
        persisted_verdicts=[_verdict("ผจก.จัดซื้อ")],
        declared_principals=_PRINCIPALS,
    )
    assert verdict.governed is False
    assert TierAuthorityViolationKind.UNKNOWN_PRINCIPAL in {v.kind for v in verdict.violations}


def test_every_verdict_must_be_satisfied_fan_out() -> None:
    """SD-2(i): on a multi-entity fan-out the principal must satisfy EVERY verdict. appr-pm holds
    ผจก.จัดซื้อ but NOT ผจก.โรงงาน, so a mixed [฿288k, ฿600k] set refuses appr-pm on the higher one."""
    verdict = check_tier_authority(
        principal=_PM,
        step_id="approve",
        governance_content=_LADDER,
        persisted_verdicts=[_verdict("ผจก.จัดซื้อ"), _verdict("ผจก.โรงงาน", resolved="appr-plant")],
        declared_principals=_PRINCIPALS,
    )
    assert verdict.governed is False
    mismatches = [
        v for v in verdict.violations if v.kind == TierAuthorityViolationKind.TIER_ROLE_MISMATCH
    ]
    assert [v.required_role for v in mismatches] == ["ผจก.โรงงาน"]


def test_cumulative_senior_satisfies_a_mixed_fan_out() -> None:
    """The Policy-B payoff on a fan-out: a director holds BOTH ผจก.จัดซื้อ and ผจก.โรงงาน
    cumulatively, so they satisfy the whole mixed set (which no exact-tier junior could)."""
    verdict = check_tier_authority(
        principal=_DIRECTOR,
        step_id="approve",
        governance_content=_LADDER,
        persisted_verdicts=[_verdict("ผจก.จัดซื้อ"), _verdict("ผจก.โรงงาน", resolved="appr-plant")],
        declared_principals=_PRINCIPALS,
    )
    assert verdict.governed is True


# --- a severity (non-money) authority ladder enforces identically -----------------------------
_SEV_LADDER = SeverityLadder(
    tiers=[
        SeverityTier(min_severity=ExcursionSeverity.NEGLIGIBLE, approver_role="จนท.ประกันคุณภาพ"),
        SeverityTier(min_severity=ExcursionSeverity.CRITICAL, approver_role="ผอ.ฝ่ายคุณภาพ"),
    ]
)


def test_severity_junior_refused_at_critical() -> None:
    """AC-2 on S3: appr-qa (holds only จนท.ประกันคุณภาพ) is refused a `critical` disposition the
    ladder routed to ผอ.ฝ่ายคุณภาพ — the non-money analog of the doa_tier junior refusal."""
    qa = Person(person_id="appr-qa", name="qa", roles=["approver", "จนท.ประกันคุณภาพ"])
    qdir = Person(
        person_id="appr-qdir",
        name="qdir",
        roles=["approver", "ผอ.ฝ่ายคุณภาพ", "จนท.ประกันคุณภาพ"],
    )
    verdict = check_tier_authority(
        principal=qa,
        step_id="approve",
        governance_content=_SEV_LADDER,
        persisted_verdicts=[{"required_role": "ผอ.ฝ่ายคุณภาพ", "resolved_approver_id": "appr-qdir"}],
        declared_principals=[qa, qdir],
    )
    assert verdict.governed is False
    assert [v.kind for v in verdict.violations] == [TierAuthorityViolationKind.TIER_ROLE_MISMATCH]
