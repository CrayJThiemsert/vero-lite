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
