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

from services.engine.procedures.prose_lint import prose_lint
from services.engine.procedures.spec import load_procedures

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
