"""PLAN-0040 Phase A (Step A3) — the deterministic prose-lint (AC-A5 / ADR-0024 D3
mechanism 2).

Offline gate (zero-LLM) for the prose-smuggling guard: numeric / currency /
percentage / handler-name / selection-or-approval-verb values in generated prose
are flagged (positive cases), clean advisory prose is not (negative cases), and the
real shipped ``facet.llm_assist`` advisory prose stays clean (a no-false-positive
guard on the exact prose the generator drafts).
"""

from __future__ import annotations

import pytest

from services.engine.procedures.prose_lint import governance_prose_lint, prose_lint
from services.engine.procedures.spec import DoaLadder, load_procedures

REAL_VERTICALS = ["energy", "supply_chain", "aquaculture", "procurement"]


# --- positive: governance values smuggled into prose are flagged -----------------


@pytest.mark.parametrize(
    "text",
    [
        "set the threshold to 4.0 on a breach",  # decimal + set-threshold
        "the reorder point is 100",  # standalone integer
        "auto-approve anything under ฿50,000",  # currency + approve verb
        "escalate amounts above 50k to the senior tier",  # magnitude amount
        "block candidates scoring below 80%",  # percentage
        "the model should select the cheapest supplier",  # selection verb
        "choose the on-contract vendor automatically",  # selection verb
    ],
)
def test_flags_smuggled_governance_values(text: str) -> None:
    assert prose_lint(text), f"expected a violation for: {text!r}"


def test_flags_registered_handler_name() -> None:
    """A handler NAME in generated prose is a human-authored binding (leak)."""
    v = prose_lint(
        "if it fails, fall back to the wire_transfer handler",
        handlers=frozenset({"wire_transfer", "issue_po"}),
    )
    assert any(x.kind == "handler" and x.match == "wire_transfer" for x in v)


def test_violation_carries_kind_and_match() -> None:
    v = prose_lint("set threshold 0.8")
    kinds = {x.kind for x in v}
    assert "numeric" in kinds  # 0.8
    assert any(x.kind == "decision_verb" for x in v)  # set ... threshold


# --- negative: clean advisory prose is not flagged ------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "draft the round summary (advisory)",
        "summarise the candidate quotes (advisory)",
        "propose a precautionary water-exchange action (advisory)",
        "enrich the purchase requisition from the work-order (advisory draft)",
        "",  # empty prose
    ],
)
def test_clean_advisory_prose_passes(text: str) -> None:
    assert prose_lint(text) == []


def test_identifier_strings_are_not_numeric_values() -> None:
    """ADR / PLAN / model identifiers carry digits but are not governance values —
    they must not trip the numeric checks (a false positive would make the lint
    un-usable on real prose)."""
    assert prose_lint("see ADR-007 and PLAN-0022; runs on gpt-oss:20b") == []


# --- no-FP guard: the real shipped advisory prose stays clean --------------------


@pytest.mark.parametrize("vertical", REAL_VERTICALS)
def test_shipped_llm_assist_prose_is_clean(vertical: str) -> None:
    """Every shipped ``facet.llm_assist`` string (the advisory-role prose the
    generator drafts) passes the lint — no false positives on real data."""
    spec = load_procedures(vertical)
    for proc in spec.procedures:
        for step in proc.steps:
            if step.facet is not None and step.facet.llm_assist is not None:
                assert prose_lint(step.facet.llm_assist) == [], (
                    f"{vertical}/{step.step_id}: llm_assist tripped the lint: "
                    f"{step.facet.llm_assist!r}"
                )


# --- hardening: the bypass classes the PR-B1 security audit found are now closed --


@pytest.mark.parametrize(
    "text",
    [
        "set the operating band to " + chr(0xFF14) + chr(0xFF0E) + chr(0xFF10),  # C1 fullwidth
        "the band sits at four point zero on the meter",  # C2 spelled-out decimal
        "the ceiling is fifty thousand baht for this route",  # C2 spelled-out magnitude
        "keep dissolved oxygen above 4 at all times",  # C3 single-digit threshold
        "flag invoices over 50-baht each",  # C3 hyphen-adjacent integer
        "set the band to 4​.​0 on a breach",  # M1 zero-width-split decimal
        "the threshold is 4e0 units",  # M2 scientific notation
        "the threshold is 0x32 on the meter",  # M2 hex
        "drop candidates scoring below eighty percent",  # spelled-out percentage
    ],
)
def test_flags_obfuscated_numeric_values(text: str) -> None:
    """NFKC + zero-width strip + single-digit/hyphen + scientific/hex + spelled-out
    numbers — none of these display-equivalent obfuscations evade the lint anymore."""
    assert prose_lint(text), f"expected a violation for: {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        "a supervisor will green-light each remediation",
        "the shift lead must sign off on every breach",
        "operations ratify the proposed reorder list",
        "a manager may override the standing band",
        "the desk can waive the hold for trusted vendors",
        "the reviewer will grant or deny each request",
    ],
)
def test_flags_expanded_decision_verbs(text: str) -> None:
    """The approval verbs the original set missed (ratify/permit/grant/deny/override/
    waive/sign-off/green-light) are caught — the LLM may only draft/summarise."""
    assert any(v.kind == "decision_verb" for v in prose_lint(text)), text


def test_flags_invented_snake_case_handler() -> None:
    """A handler name NOT in the passed registry (invented or cross-vertical) is caught by
    the snake_case structural rule — a code identifier never appears in advisory prose."""
    v = prose_lint("dispatch via the swift_payout handler", handlers=frozenset())
    assert any(x.kind == "handler" and x.match == "swift_payout" for x in v)


@pytest.mark.parametrize(
    "text",
    [
        "review each of the two proposed actions for the operator",
        "propose one corrective action per breach (advisory)",
    ],
)
def test_lone_small_number_words_are_not_flagged(text: str) -> None:
    """A lone ones-word (one..ten) stays clean — only specific magnitudes (teens / tens /
    scales) and explicit decimals are values; flagging "two" everywhere would be unusable."""
    assert prose_lint(text) == []


# --- re-verify round 2: the two HIGH gaps the second audit pass found ------------


def test_flags_upper_snake_env_var_binding() -> None:
    """An UPPER_SNAKE env-var binding (the literal env-band governance value a judge owes)
    is caught — the case-insensitive snake_case rule (re-verify HIGH #1)."""
    v = prose_lint("read the band from OCT_RECOMMEND_THRESHOLD at runtime")
    assert any(x.kind == "handler" and x.match == "OCT_RECOMMEND_THRESHOLD" for x in v)


@pytest.mark.parametrize(
    "text, handlers",
    [
        ("dispatch via swiftPayout urgently", frozenset()),  # camelCase invented name
        ("use the wire transfer handler", frozenset({"wire_transfer"})),  # spaced registered
        ("use the wire-transfer handler", frozenset({"wire_transfer"})),  # kebab registered
        ("use the WireTransfer handler", frozenset({"wire_transfer"})),  # Pascal registered
    ],
)
def test_flags_non_underscore_handler_spellings(text: str, handlers: frozenset[str]) -> None:
    """A handler named in camelCase / spaced / kebab / Pascal form is caught — the
    camelCase structural rule + the flexible-separator registered match (re-verify HIGH #2)."""
    assert any(v.kind == "handler" for v in prose_lint(text, handlers=handlers)), text


@pytest.mark.parametrize(
    "text",
    [
        "the manager will accept the breach set",
        "the desk may decline the request",
        "operations disapprove the reorder list",
    ],
)
def test_flags_more_approval_verbs(text: str) -> None:
    """accept / decline / disapprove are approval decisions the LLM may not make."""
    assert any(v.kind == "decision_verb" for v in prose_lint(text)), text


# === PLAN-0042 Step 3 — the SCOPED governance prose-lint (AC-11 / ADR-0025 D4 / OQ-D) ===
#
# governance_prose_lint runs over HAND-AUTHORED AT-2 free-text: value classes only +
# an approver-role-token check; it OMITS the decision-verb / approval-phrase classes and
# the broad snake/camel identifier catch (which legitimately appear in hand-authored
# governance notes — finding 6). A ฿-amount / weight / role token blocks load; a decision
# verb / handler name in a hand-authored note does not.


@pytest.mark.parametrize(
    "text",
    [
        "auto-approve anything under ฿50,000",  # currency
        "weight criticality at 0.5 in the score",  # decimal (a leaked weight)
        "escalate amounts above 2M to the director",  # magnitude amount
        "block candidates scoring below 80%",  # percentage
        "the ceiling is fifty thousand baht for this route",  # spelled-out magnitude
        "the floor is 50000 baht",  # bare integer
    ],
)
def test_governance_lint_flags_value_leaks(text: str) -> None:
    """A ฿-amount / weight / magnitude / percent in AT-2 free-text is a smuggled value (AC-11)."""
    assert governance_prose_lint(text), text


@pytest.mark.parametrize(
    "text",
    [
        # the EXACT finding-6 hand-authored notes the generated-prose lint over-flags:
        "SELECTION = a scored RULE, never the LLM (governed != generated)",
        "blocks the PO on ANY failed criterion (hard gate)",
        "tiered DOA + emergency waiver (escalate, never skip) + SoD; HUMAN approves",
        "on-contract default; RFQ->AVL only as a logged exception",
        "the emergency waiver escalates the approver and forces a logged justification",
        "fall back to the request_approval handler on a timeout",  # registered handler name
    ],
)
def test_governance_lint_passes_handauthored_decision_prose(text: str) -> None:
    """Decision verbs / approval phrases / handler-ish identifiers in a HAND-AUTHORED note are
    legitimate — the scoped variant omits _VERB_SCANS + the broad identifier catch (finding 6)."""
    assert governance_prose_lint(text) == [], text


def test_governance_lint_flags_approver_role_token() -> None:
    """An approver-role token in free-text belongs in the typed DOA field, not prose (AC-11)."""
    roles = frozenset({"ผอ.", "ผจก.จัดซื้อ"})
    v = governance_prose_lint("route straight to ผอ. on a breach", roles=roles)
    assert any(x.kind == "role" and x.match == "ผอ." for x in v)


def test_governance_lint_clean_when_role_not_present() -> None:
    """The role check only fires on an actual token occurrence — clean prose stays clean."""
    roles = frozenset({"ผอ.", "ผจก.จัดซื้อ"})
    assert governance_prose_lint("route the compliant set to the human approver", roles=roles) == []


def test_governance_lint_passes_shipped_at2_free_text() -> None:
    """The shipped procurement AT-2's real free-text (goal + the AT-2-step descriptions) passes
    the scoped lint — no false positives on real hand-authored governance prose (AC-11). The
    load itself runs this validator, so a successful load is the standing proof; this asserts it
    directly on the surfaces."""
    spec = load_procedures("procurement")
    proc = next(p for p in spec.procedures if p.procedure_id == "emergency_sourcing_round")
    roles: set[str] = set()
    for step in proc.steps:
        if isinstance(step.governance_content, DoaLadder):
            roles.update(t.approver_role for t in step.governance_content.tiers)
            roles.add(step.governance_content.emergency_waiver.escalate_to)
    role_set = frozenset(roles)
    assert governance_prose_lint(proc.goal, roles=role_set) == [], "goal"
    for step in proc.steps:
        if step.governance_content is not None:
            assert governance_prose_lint(step.description, roles=role_set) == [], step.step_id
