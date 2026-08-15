"""PLAN-0096 Step 4 / AC-4 — the computed sourcing signal, on the REAL gate.

This is the step that retires a fail-open default, so the tests are written around
one question: *would this still pass if the governance were silently broken?*

The AC-4 matrix runs against ``evaluate_compliance`` itself — the shipped
``rule_gate`` function, with the shipped fleet YAML's authored rule. Nothing is
mocked: mocking the gate under test is a rejection condition in PLAN-0096's own
oracle contract, and it would make every row below vacuous.

**The counterexample the PLAN names**, verified this session: restoring the reshape
``default: {compliance: {three_quote: true}}`` makes the no-evidence case pass. That
one line was the difference between a governed sourcing rule and a decoration.

Offline + host-state-free (CLAUDE.md §8): pure functions and the shipped spec — no
DB, no network, no LLM.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from services.engine import demo_events
from services.engine.procedures.rule_gate import RuleGateError, evaluate_compliance
from services.engine.procedures.spec import ComplianceGate, load_procedures
from verticals.fleet_maintenance import case_projection
from verticals.fleet_maintenance.sourcing import (
    MIN_DISTINCT_VENDORS,
    PASSING_BASES,
    THREE_QUOTE_THRESHOLD_THB,
    compliance_signal_map,
    compute_three_quote,
)

_VERTICAL = "fleet_maintenance"


def _shipped_gate() -> ComplianceGate:
    """The quote_gate's authored content from the REAL shipped YAML."""
    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == "governed_repair_approval")
    gate = next(s.governance_content for s in proc.steps if s.step_id == "quote_gate")
    assert isinstance(gate, ComplianceGate)
    return gate


def _row(amount: int, *, vendors: int, sole_source: bool) -> dict[str, Any]:
    """A breach row as the evidence feed builds it — signal map + stamped basis."""
    result = compute_three_quote(
        amount_thb=Decimal(amount),
        distinct_vendor_count=vendors,
        has_sole_source_justification=sole_source,
    )
    _, basis = result
    return {
        "amount": str(amount),
        "currency": "THB",
        "compliance": compliance_signal_map(result),
        "three_quote_basis": basis,
    }


# --------------------------------------------------------------------------- #
# AC-4 — the decision matrix, on the real gate
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("amount", "vendors", "sole_source", "compliant", "basis"),
    [
        # A big repair nobody compared, with nothing written down. The case the old
        # fail-open default waved through, and the reason this step exists.
        pytest.param(48_000, 1, False, False, "quotes_required", id="48k-1-quote-blocked"),
        # The comparison actually happened.
        pytest.param(48_000, 3, False, True, "three_quotes", id="48k-3-vendors-pass"),
        # No comparison was possible and a human wrote why (ADR-0034 D4, E-3).
        pytest.param(48_000, 1, True, True, "sole_source_justified", id="48k-sole-source-pass"),
        # Small enough that the rule never applied.
        pytest.param(25_000, 1, False, True, "under_threshold", id="25k-under-threshold"),
        # The boundary, both sides. The partner said ">30,000", so 30,000 itself is
        # still under and 30,001 is the first ฿ that must be compared.
        pytest.param(30_000, 1, False, True, "under_threshold", id="30000-still-under"),
        pytest.param(30_001, 1, False, False, "quotes_required", id="30001-must-compare"),
    ],
)
def test_ac4_decision_matrix_on_the_real_gate(
    amount: int, vendors: int, sole_source: bool, compliant: bool, basis: str
) -> None:
    """Each row: compute the signal, then run the SHIPPED gate over the SHIPPED rule.

    Both halves are asserted because they fail differently. A wrong ``basis`` with a
    right ``compliant`` is a correct decision the export cannot explain; a wrong
    ``compliant`` is real money moving without the comparison the partner asked for."""
    row = _row(amount, vendors=vendors, sole_source=sole_source)
    assert row["three_quote_basis"] == basis

    verdict = evaluate_compliance(_shipped_gate(), row)
    assert verdict.compliant is compliant
    assert (verdict.failed_criteria == []) is compliant
    if not compliant:
        assert verdict.failed_criteria == ["three_quote"]


def test_a_row_with_no_signal_map_fails_closed() -> None:
    """AC-4's last row, and the one the retired default made UNREACHABLE.

    A breach row that reaches the gate carrying no ``compliance`` map is a wiring
    error — the feed did not run, or ran and produced nothing. The gate raises rather
    than deciding, because the one thing it must never do is treat "I could not tell"
    as "yes". While the reshape default existed, no row could ever arrive without a
    map, so this failure mode was untestable and unnoticed."""
    with pytest.raises(RuleGateError):
        evaluate_compliance(_shipped_gate(), {"amount": "48000", "currency": "THB"})


def test_the_retired_default_is_gone_from_the_shipped_yaml() -> None:
    """The structural half of the same claim.

    The matrix above proves the gate behaves correctly on rows the feed builds; this
    proves the YAML no longer manufactures a passing row for everything else. Both
    are needed — a re-added default would leave every test above green while
    restoring exactly the hole they were written to close."""
    from pathlib import Path

    yaml_text = Path("verticals/fleet_maintenance/procedures.yaml").read_text(encoding="utf-8")
    reshape = yaml_text.split("step_id: reshape", 1)[1].split("step_id: quote_gate", 1)[0]
    assert (
        "target: compliance" not in reshape
    ), "the fail-open compliance default is back in the reshape transform"


# --------------------------------------------------------------------------- #
# end to end — the matrix above proves the FUNCTION and the GATE; this proves the
# PIPELINE, which is a different claim and fails differently
# --------------------------------------------------------------------------- #


@pytest.fixture
async def fleet_factory(monkeypatch: pytest.MonkeyPatch):
    from services.api.config import settings
    from services.engine.discovery import discover_and_register
    from services.engine.registry import registry
    from verticals.fleet_maintenance.procedures_factory import (
        register_fleet_maintenance_procedure_executors,
    )

    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    return registry.get_procedure_executors(_VERTICAL)


@pytest.fixture(autouse=True)
def _fixture_only_stream():
    """Measure the SHIPPED FIXTURE, not whatever cases a shared database happens to hold.

    🔴 Added s233 after a full-suite-only RED that no isolated run reproduced. The
    assertions below pin the demo's two breach rows **by equality**, but the rows come
    through ``case_projection``, a process-wide singleton that overlays live cases read
    from the test database. Any earlier test that seeds an OPEN case with an accepted
    quote therefore adds a third breach row here, and this module reddens for a reason
    that has nothing to do with sourcing.

    Resetting is the honest fix rather than loosening the equality: this module's
    subject IS the fixture's own evidence, so depending on ambient database state was a
    latent defect that a real case was always going to expose.
    """
    case_projection.reset()
    demo_events.reset(_VERTICAL)
    yield
    case_projection.reset()
    demo_events.reset(_VERTICAL)


async def _run(factory, run_id: str):
    from services.engine.procedures.orchestrator import run_procedure

    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == "governed_repair_approval")
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    result = await run_procedure(proc, agent, factory(), vertical=_VERTICAL, run_id=run_id)
    return {step.step_id: step for step in result.step_results}


async def test_the_shipped_demo_passes_the_gate_on_its_own_evidence(fleet_factory) -> None:
    """The demo still works — and now for an honest reason.

    Both breach rows reach the DOA gate, and they pass on DIFFERENT bases: ฿48,000
    because เมย์ collected three separate quotes, ฿15,000 because it never crossed
    the threshold. Before this step both passed because a YAML default said ``true``.
    Asserting the two distinct bases is what proves the signal is computed rather
    than assumed — a fixture that hard-coded a pass would show one basis, or none."""
    by_step = await _run(fleet_factory, "fleet-step4-e2e")

    gate_audit = by_step["quote_gate"].audit or {}
    assert all(c["compliant"] is True for c in gate_audit["rule_gate"])

    rows = by_step["quote_gate"].artifact["output_set"]
    bases = {Decimal(r["amount"]): r["three_quote_basis"] for r in rows}
    assert bases == {Decimal("48000.0"): "three_quotes", Decimal("15000.0"): "under_threshold"}
    assert "approve" in by_step, "the run must still reach the human gate"


async def test_a_breach_row_whose_feed_did_not_run_fails_closed_in_a_real_run(
    fleet_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The end-to-end half of the fail-closed claim, and the one the matrix cannot make.

    The matrix calls ``evaluate_compliance`` directly; the structural test reads the
    YAML. Neither proves what happens when a breach row travels the ACTUAL pipeline —
    intake, judge, reshape — carrying no computed signal, which is precisely the
    shape a broken or unwired feed produces. With the old default in place the
    reshape manufactured a passing map at this exact point, so this run could not
    have failed however broken the feed was.

    A missing map is 'I could not tell', and the one thing a governance gate must
    never do is read that as 'yes'.

    Note what is asserted, and why it is not ``pytest.raises``. The gate DOES raise
    ``RuleGateError`` — but the orchestrator catches every step failure by design
    (fail-and-divert, ADR-016 D4) and records it rather than letting one executor take
    down the run loop. So the observable, and the thing that actually protects the
    partner's money, is that the gate step FAILED and the run never reached the human
    approval step. That is a stronger claim than 'an exception was raised somewhere':
    it says no spend was ever put in front of anyone to approve."""
    from services.engine.procedures.runs import StepResultStatus
    from verticals.fleet_maintenance.data_adapter import synthetic

    shipped = synthetic.operational_events  # bind BEFORE patching, or this recurses

    def _unfed_events() -> list[dict[str, Any]]:
        """The shipped events with the computed sourcing fields stripped."""
        return [
            {k: v for k, v in event.items() if k not in {"compliance", "three_quote_basis"}}
            for event in shipped()
        ]

    monkeypatch.setattr(synthetic, "operational_events", _unfed_events)

    by_step = await _run(fleet_factory, "fleet-step4-unfed")

    assert by_step["quote_gate"].status == StepResultStatus.FAILED.value
    assert "approve" not in by_step, "an unverifiable spend must never reach the human gate"
    assert "fulfill" not in by_step


# --------------------------------------------------------------------------- #
# the config the rule reads, and where it is allowed to live
# --------------------------------------------------------------------------- #


def test_the_threshold_is_not_smuggled_into_the_rule_prose() -> None:
    """ADR-0025 D4: the ฿ figure and the vendor count are typed config, and the
    authored rule text must name the PATHS without naming the numbers.

    Asserted on the shipped rule rather than trusting the load-time lint, because the
    lint protects against a generated leak — this guards a human editing the YAML and
    "helpfully" adding the threshold back for readability."""
    [rule] = _shipped_gate().rules
    prose = rule.spec
    assert "฿" not in prose
    assert "30" not in prose and "3" not in prose
    # the rule must still describe BOTH ways it can be satisfied
    assert "sole-source" in prose or "sole source" in prose


def test_the_partner_answer_is_encoded_once() -> None:
    """The threshold and the vendor count live in exactly one place.

    A second copy is how a revised answer gets applied in one file and forgotten in
    another — and this one WILL be revised: it is one operator's answer on one day."""
    assert THREE_QUOTE_THRESHOLD_THB == Decimal("30000")
    assert MIN_DISTINCT_VENDORS == 3
    assert "quotes_required" not in PASSING_BASES


def test_a_pass_always_carries_a_passing_basis_and_a_block_never_does() -> None:
    """The basis and the signal can never disagree — the export reads the basis to
    explain a decision the gate made from the signal, so a row that passed with a
    failing basis would be an audit answer that contradicts its own outcome."""
    for amount in (1, 25_000, 30_000, 30_001, 48_000, 500_000):
        for vendors in (0, 1, 3, 5):
            for sole_source in (False, True):
                signal, basis = compute_three_quote(
                    amount_thb=Decimal(amount),
                    distinct_vendor_count=vendors,
                    has_sole_source_justification=sole_source,
                )
                assert signal is (basis in PASSING_BASES), (amount, vendors, sole_source, basis)
