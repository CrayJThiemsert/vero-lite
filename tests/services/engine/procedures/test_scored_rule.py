"""AC-7 (PLAN-0044 A1b Step 5) -- the deterministic ``scored_rule`` executor.

Offline + LLM-free (CLAUDE.md #8 -- the offline oracle is the gate). Four surfaces:

* the pure :func:`select_scored_supplier` -- deterministic weighted selection, the
  event-criticality amplifier, provenance (default vs off-AVL exception), ``Decimal`` spend,
  and the fail-closed edges (empty / malformed quotes, an uninterpretable criterion);
* the SD-1=(a) :class:`GovernanceActionExecutor` dispatch -- a ``scored_rule`` action selects
  the supplier and EMITS the selected spend onto the threaded entity (REPLACING the base
  envelopes -- the whole point of the section-3 finding), records the scoring audit, and the LLM
  (the base) never changes the pick;
* the section-3 threading fix end-to-end at the executor seam -- the emitted spend flows into
  the ``doa_tier`` executor and resolves the tier (the amount the shipped ``ActionStepExecutor``
  dropped, so the approve gate could not route the DOA tier);
* a guard that the SHIPPED procurement ``source`` rule still selects the hero supplier.

The pre-committed pass/fail reads are PLAN-0044 AC-7 + the section-3 finding, fixed before this
test was authored: same inputs -> same pick, the LLM never selects, the selected 288,000 THB
threads source -> approve -> CONTROLLER.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal
from typing import Any

import pytest

from services.engine.procedures.governance_step import GovernanceActionExecutor
from services.engine.procedures.orchestrator import RunContext, StepOutcome
from services.engine.procedures.scored_rule import ScoredRuleError, select_scored_supplier
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    DoaLadder,
    DoaTier,
    EmergencyWaiverPolicy,
    ExceptionPolicy,
    Person,
    ScoredCriterion,
    ScoredRule,
    SourcePolicy,
    Step,
    StepKind,
    load_procedures,
)
from services.engine.procedures.transform_step import TransformStepExecutor

# --------------------------------------------------------------------------- #
# Fixtures — the Fastenal hero quote set + the authored scored_rule
# --------------------------------------------------------------------------- #

# The three PRT-SPN-700 candidate quotes (Fastenal hero dataset, C-1 quotation.csv -- normalised
# to the enriched shape intake produces: unit_price/currency/lead_time_days/on_contract). The
# tension: on-contract Fastenal (14-day) vs the off-AVL RapidMRO (2-day, priciest) vs NSK
# (cheapest, slowest). For a CRITICAL line-down event, speed must win -> RapidMRO.
_HERO_QUOTES: list[Mapping[str, Any]] = [
    {
        "quote_id": "QT-SPN-FASTENAL",
        "supplier_id": "SUP-FASTENAL-TH",
        "unit_price": "78500",
        "currency": "THB",
        "lead_time_days": "14",
        "on_contract": True,
    },
    {
        "quote_id": "QT-SPN-RAPIDMRO",
        "supplier_id": "SUP-RAPIDMRO",
        "unit_price": "96000",
        "currency": "THB",
        "lead_time_days": "2",
        "on_contract": False,
    },
    {
        "quote_id": "QT-SPN-NSK",
        "supplier_id": "SUP-NSKBRG-TH",
        "unit_price": "74000",
        "currency": "THB",
        "lead_time_days": "21",
        "on_contract": False,
    },
]


def _hero_rule() -> ScoredRule:
    """The procurement ``source`` step's authored scored_rule (procedures.yaml): criticality 0.5 /
    lead_time 0.3 / unit_price 0.2, on_contract default, rfq_avl_logged exception."""
    return ScoredRule(
        criteria=[
            ScoredCriterion(name="criticality", weight=Decimal("0.5")),
            ScoredCriterion(name="lead_time", weight=Decimal("0.3")),
            ScoredCriterion(name="unit_price", weight=Decimal("0.2")),
        ],
        default_source=SourcePolicy.ON_CONTRACT,
        exception_policy=ExceptionPolicy.RFQ_AVL_LOGGED,
    )


def _hero_pr() -> dict[str, Any]:
    """The enriched purchase-requisition entity the ``source`` step scores (data-access = (a)):
    the failure context + the requested qty + the part's candidate quotes."""
    return {
        "event_id": "EVT-CNC-014-FAIL",
        "part_id": "PRT-SPN-700",
        "asset_id": "AST-CNC-014",
        "qty": 3,
        "criticality": "0.92",
        "candidate_quotes": _HERO_QUOTES,
    }


# --------------------------------------------------------------------------- #
# The pure select_scored_supplier — deterministic weighted selection
# --------------------------------------------------------------------------- #


def test_hero_selects_rapidmro_and_emits_the_spend_factors() -> None:
    """AC-7 — the critical event picks the fast off-AVL supplier + emits the spend's two FACTORS.

    PLAN-0078 PR-4 (SD-8(a)): the verdict carries ``selected_unit_price`` and ``qty``, never their
    product — the declared ``derive_spend`` transform multiplies them, so the derivation has ONE
    home, as governed data. That the product is still ฿288,000 byte-for-byte is asserted
    end-to-end in ``test_amount_transform_parity.py``, over the real procedure."""
    v = select_scored_supplier(
        _hero_rule(), _HERO_QUOTES, qty=Decimal("3"), event_criticality=Decimal("0.92")
    )
    assert v.selected_supplier_id == "SUP-RAPIDMRO"
    assert v.selected_quote_id == "QT-SPN-RAPIDMRO"
    assert v.selected_unit_price == Decimal("96000")
    assert v.qty == Decimal("3")
    assert v.currency == "THB"
    assert v.on_contract is False
    # RapidMRO is off-contract -> the default (on_contract) was not met -> the logged exception.
    assert v.source_path == "exception_policy"
    assert v.override_required is True


def test_selection_is_deterministic() -> None:
    """AC-7 — same inputs -> same pick + same ranking, every run (no model signal, no float)."""
    runs = [
        select_scored_supplier(
            _hero_rule(), _HERO_QUOTES, qty=Decimal("3"), event_criticality=Decimal("0.92")
        )
        for _ in range(5)
    ]
    first = runs[0]
    for v in runs[1:]:
        assert v.selected_quote_id == first.selected_quote_id
        assert v.selected_unit_price == first.selected_unit_price
        assert v.qty == first.qty
        assert [q.quote_id for q in v.ranked] == [q.quote_id for q in first.ranked]


def test_ranked_order_reflects_the_scores() -> None:
    v = select_scored_supplier(
        _hero_rule(), _HERO_QUOTES, qty=Decimal("3"), event_criticality=Decimal("0.92")
    )
    assert [q.quote_id for q in v.ranked] == [
        "QT-SPN-RAPIDMRO",
        "QT-SPN-FASTENAL",
        "QT-SPN-NSK",
    ]
    # strictly descending by score
    scores = [q.score for q in v.ranked]
    assert scores == sorted(scores, reverse=True)


def test_weights_drive_the_pick_not_a_hardcoded_winner() -> None:
    """A price-dominant rule picks the CHEAPEST supplier -- selection honours the rule, it is not
    hardwired to RapidMRO."""
    price_rule = ScoredRule(
        criteria=[
            ScoredCriterion(name="criticality", weight=Decimal("0.1")),
            ScoredCriterion(name="lead_time", weight=Decimal("0.1")),
            ScoredCriterion(name="unit_price", weight=Decimal("0.8")),
        ],
        default_source=SourcePolicy.ON_CONTRACT,
        exception_policy=ExceptionPolicy.RFQ_AVL_LOGGED,
    )
    v = select_scored_supplier(
        price_rule, _HERO_QUOTES, qty=Decimal("2"), event_criticality=Decimal("0.92")
    )
    assert v.selected_supplier_id == "SUP-NSKBRG-TH"  # cheapest (74000)
    assert v.selected_unit_price == Decimal("74000")


def test_event_criticality_amplifies_lead_time_context_sensitive() -> None:
    """The SAME rule picks the cheap supplier for a routine event and the fast supplier for a
    critical one -- the criticality-as-weight-amplifier model (routine -> NSK, critical ->
    RapidMRO)."""
    rule = ScoredRule(
        criteria=[
            ScoredCriterion(name="criticality", weight=Decimal("0.5")),
            ScoredCriterion(name="lead_time", weight=Decimal("0.1")),
            ScoredCriterion(name="unit_price", weight=Decimal("0.4")),
        ],
        default_source=SourcePolicy.ON_CONTRACT,
        exception_policy=ExceptionPolicy.RFQ_AVL_LOGGED,
    )
    routine = select_scored_supplier(
        rule, _HERO_QUOTES, qty=Decimal("1"), event_criticality=Decimal("0")
    )
    critical = select_scored_supplier(
        rule, _HERO_QUOTES, qty=Decimal("1"), event_criticality=Decimal("1")
    )
    assert routine.selected_supplier_id == "SUP-NSKBRG-TH"  # cheapest wins when not critical
    assert critical.selected_supplier_id == "SUP-RAPIDMRO"  # fastest wins when critical


def test_verdict_carries_the_spend_factors_and_never_the_product() -> None:
    """PLAN-0078 PR-4 (SD-8(a)) — the replacement for ``test_amount_is_unit_price_times_qty``.

    The multiplication this module used to perform is GONE: it is declared data now (the
    ``derive_spend`` transform), so the verdict carries the two factors and nothing derives the
    spend in code. ``qty`` rides through untouched and the winner's unit price is independent of
    it; the product is asserted end-to-end in ``test_amount_transform_parity.py``.

    The ``no amount attribute`` assertion is the STRUCTURAL guard on the re-sequencing itself:
    re-introducing a code-side ``amount`` here would restore SD-8's rejected alternative (b) — the
    derivation living in two homes, code and data, free to drift apart silently."""
    one = select_scored_supplier(
        _hero_rule(), _HERO_QUOTES, qty=Decimal("1"), event_criticality=Decimal("0.92")
    )
    three = select_scored_supplier(
        _hero_rule(), _HERO_QUOTES, qty=Decimal("3"), event_criticality=Decimal("0.92")
    )
    # the winner's unit price is the SAME regardless of qty — only the declared transform scales it
    assert one.selected_unit_price == three.selected_unit_price == Decimal("96000")
    assert (one.qty, three.qty) == (Decimal("1"), Decimal("3"))
    assert not hasattr(three, "amount"), (
        "ScoredRuleVerdict grew an 'amount' back — the spend derivation must live ONLY in the "
        "declared derive_spend transform (SD-8(a) one derivation home), never in code beside it"
    )


def test_tie_breaks_by_quote_id() -> None:
    """Two equal-score quotes break by ascending quote_id (stable + reproducible)."""
    twins: list[Mapping[str, Any]] = [
        {
            "quote_id": "QT-B",
            "supplier_id": "SUP-B",
            "unit_price": "100",
            "currency": "THB",
            "lead_time_days": "5",
            "on_contract": True,
        },
        {
            "quote_id": "QT-A",
            "supplier_id": "SUP-A",
            "unit_price": "100",
            "currency": "THB",
            "lead_time_days": "5",
            "on_contract": True,
        },
    ]
    v = select_scored_supplier(
        _hero_rule(), twins, qty=Decimal("1"), event_criticality=Decimal("0.5")
    )
    assert v.selected_quote_id == "QT-A"


def test_on_contract_string_false_is_off_contract() -> None:
    """A CSV/JSON string ``"false"`` must be off-contract (bool('false') is True in Python)."""
    quotes: list[Mapping[str, Any]] = [
        {
            "quote_id": "QT-X",
            "supplier_id": "SUP-X",
            "unit_price": "100",
            "currency": "THB",
            "lead_time_days": "1",
            "on_contract": "false",
        }
    ]
    v = select_scored_supplier(
        _hero_rule(), quotes, qty=Decimal("1"), event_criticality=Decimal("1")
    )
    assert v.on_contract is False
    assert v.source_path == "exception_policy"


def test_empty_quotes_fails_closed() -> None:
    with pytest.raises(ScoredRuleError, match="no candidate quotes"):
        select_scored_supplier(_hero_rule(), [], qty=Decimal("1"), event_criticality=Decimal("1"))


def test_malformed_quote_fails_closed() -> None:
    bad: list[Mapping[str, Any]] = [
        {"quote_id": "QT-X", "supplier_id": "SUP-X", "currency": "THB", "lead_time_days": "1"}
    ]  # no unit_price
    with pytest.raises(ScoredRuleError, match="unit_price"):
        select_scored_supplier(_hero_rule(), bad, qty=Decimal("1"), event_criticality=Decimal("1"))


def test_unknown_criterion_fails_closed() -> None:
    rogue = ScoredRule(
        criteria=[ScoredCriterion(name="vendor_golf_handicap", weight=Decimal("1"))],
        default_source=SourcePolicy.ON_CONTRACT,
        exception_policy=ExceptionPolicy.RFQ_AVL_LOGGED,
    )
    with pytest.raises(ScoredRuleError, match="not one this executor interprets"):
        select_scored_supplier(
            rogue, _HERO_QUOTES, qty=Decimal("1"), event_criticality=Decimal("1")
        )


def test_verdict_to_audit_is_json_safe() -> None:
    v = select_scored_supplier(
        _hero_rule(), _HERO_QUOTES, qty=Decimal("3"), event_criticality=Decimal("0.92")
    )
    audit = v.to_audit()
    assert audit["selected_supplier_id"] == "SUP-RAPIDMRO"
    # PLAN-0078 PR-4 (SD-8(a) + SD-6(ii)): the projection carries the two FACTORS where it used to
    # carry `{"amount": {"value": "288000", "currency": "THB"}}`. `currency` rode inside that
    # retired key, so it is top-level now. The verdicts stay identical (SD-6(ii)) and the record
    # can still answer "why this amount?" — the form is what changed, not the governance.
    assert audit["selected_unit_price"] == "96000"
    assert audit["qty"] == "3"
    assert audit["currency"] == "THB"
    assert "amount" not in audit
    assert audit["source_path"] == "exception_policy"
    assert len(audit["ranked"]) == 3
    json.dumps(audit)  # must not raise (no Decimal leaks)


def test_shipped_procurement_source_rule_selects_the_hero_supplier() -> None:
    """Guard: the SHIPPED procurement ``source`` scored_rule (procedures.yaml) still resolves the
    hero supplier on the hero quotes -- so a weight edit that would change the demo is caught."""
    spec = load_procedures("procurement")
    proc = next(p for p in spec.procedures if p.procedure_id == "emergency_sourcing_round")
    source = next(s for s in proc.steps if s.step_id == "source")
    rule = source.governance_content
    assert isinstance(rule, ScoredRule)  # the authored source content is a scored_rule
    v = select_scored_supplier(
        rule, _HERO_QUOTES, qty=Decimal("3"), event_criticality=Decimal("0.92")
    )
    assert v.selected_supplier_id == "SUP-RAPIDMRO"
    assert v.selected_unit_price == Decimal("96000")


# --------------------------------------------------------------------------- #
# The GovernanceActionExecutor scored_rule dispatch + the section-3 threading fix
# --------------------------------------------------------------------------- #


class _FakeBase:
    """A fake base ACTION executor -- no LLM, no approve()/execute(). Pass-through output + a
    canned trace/audit; records delegation. The ``scored_rule`` branch REPLACES this output
    (the section-3 fix); the ``doa_tier`` branch KEEPS it."""

    def __init__(self) -> None:
        self.calls = 0

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        self.calls += 1
        return StepOutcome(
            output=list(input_set),
            reasoning_trace=[{"kind": "rule", "summary": f"propose {step.handler}"}],
            audit={"actor": "agent", "actor_kind": "engine"},
        )


class _GarbageBase:
    """A base whose OUTPUT is nonsense -- proves the scored_rule pick ignores the base (the LLM
    can never change the deterministic selection, governed != generated)."""

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(output=[{"garbage": True}], reasoning_trace=[], audit={})


def _ctx() -> RunContext:
    agent = Agent(
        agent_id="hero-agent",
        name="Hero Agent",
        autonomy_ceiling=Autonomy.AUTO,
        allowed=AgentAllowed(action_handlers=["emergency_source", "request_approval"]),
    )
    return RunContext(agent=agent, vertical="procurement")


def _source_step() -> Step:
    return Step(
        step_id="source",
        name="Source the critical set",
        kind=StepKind.ACTION,
        autonomy=Autonomy.AUTO,
        handler="emergency_source",
        governance_content=_hero_rule(),
    )


def _fastenal_ladder() -> DoaLadder:
    """The Fastenal DOA ladder (approval_tier.csv): THB, floors 0 / 15001 / 200001 / 1000001 ->
    SUPERVISOR / MANAGER / CONTROLLER / VP_OPERATIONS. The hero 288,000 crosses the 200,000
    Manager ceiling into the CONTROLLER band."""
    return DoaLadder(
        currency="THB",
        tiers=[
            DoaTier(min_amount=Decimal("0"), approver_role="SUPERVISOR"),
            DoaTier(min_amount=Decimal("15001"), approver_role="MANAGER"),
            DoaTier(min_amount=Decimal("200001"), approver_role="CONTROLLER"),
            DoaTier(min_amount=Decimal("1000001"), approver_role="VP_OPERATIONS"),
        ],
        emergency_waiver=EmergencyWaiverPolicy(relaxes=["three_bid"], escalate_to="CONTROLLER"),
    )


def _approve_step() -> Step:
    return Step(
        step_id="approve",
        name="Tiered DOA approval",
        kind=StepKind.ACTION,
        autonomy=Autonomy.GATED,
        handler="request_approval",
        governance_content=_fastenal_ladder(),
    )


def _controller_principals() -> list[Person]:
    return [
        Person(
            person_id="appr-controller",
            name="Controller",
            roles=frozenset({"approver", "CONTROLLER"}),
        )
    ]


async def test_wrapper_emits_spend_factors_and_replaces_output() -> None:
    """The scored_rule dispatch selects the supplier + writes the spend's two FACTORS
    (``selected_unit_price`` / ``selected_qty``) + ``currency`` onto the threaded entity
    (REPLACING the base envelopes) and records the scoring audit.

    PLAN-0078 PR-4 (SD-8(a)): the step no longer writes ``amount`` — the declared ``derive_spend``
    transform downstream derives it, so the derivation has ONE home, as governed data.
    ``selected_qty`` is stamped (not left for the transform to read off the row) so
    ``_quantity``'s ``qty`` -> ``quantity`` -> ``1`` fallback stays resolved in exactly one
    place — see the stamp's comment in ``governance_step._scored_rule``."""
    ctx = _ctx()
    base = _FakeBase()
    wrapper = GovernanceActionExecutor(base=base, sod_steps=frozenset({"approve"}))
    outcome = await wrapper.execute(_source_step(), [_hero_pr()], ctx)
    assert base.calls == 1  # the base still ran (advisory judgment + auto action)
    [enriched] = outcome.output
    assert enriched["selected_unit_price"] == "96000"  # the winner's price the transform scales
    assert enriched["selected_qty"] == "3"  # the resolved quantity, stamped by _quantity ONCE
    assert "amount" not in enriched  # the spend is declared data now, not this step's product
    assert enriched["currency"] == "THB"
    assert enriched["selected_supplier_id"] == "SUP-RAPIDMRO"
    assert enriched["source_path"] == "exception_policy"
    assert enriched["override_required"] is True
    assert enriched["part_id"] == "PRT-SPN-700"  # the input entity fields are preserved
    assert outcome.audit is not None
    assert outcome.audit["governed_kind"] == "scored_rule"
    [scored] = outcome.audit["scored_rule"]
    assert scored["selected_supplier_id"] == "SUP-RAPIDMRO"
    assert any(t["kind"] == "scored_rule_selected" for t in outcome.reasoning_trace)


async def test_wrapper_pick_ignores_the_base_output() -> None:
    """The base (the LLM path) cannot change the deterministic pick -- a garbage base output is
    discarded; the enriched entity still selects RapidMRO + emits its 96,000/unit x 3 factors."""
    ctx = _ctx()
    wrapper = GovernanceActionExecutor(base=_GarbageBase())
    outcome = await wrapper.execute(_source_step(), [_hero_pr()], ctx)
    [enriched] = outcome.output
    assert "garbage" not in enriched
    assert enriched["selected_supplier_id"] == "SUP-RAPIDMRO"
    assert enriched["selected_unit_price"] == "96000"
    assert enriched["selected_qty"] == "3"


async def test_wrapper_missing_candidate_quotes_fails_closed() -> None:
    ctx = _ctx()
    base = _FakeBase()
    wrapper = GovernanceActionExecutor(base=base)
    with pytest.raises(ScoredRuleError, match="candidate_quotes"):
        await wrapper.execute(_source_step(), [{"part_id": "PRT-SPN-700", "qty": 3}], ctx)
    assert base.calls == 0  # failed closed before delegating to the base


async def test_selected_spend_threads_to_doa_tier_controller() -> None:
    """The section-3 fix, end to end at the executor seam — a THREE-step chain since PLAN-0078
    PR-4: ``_scored_rule`` emits the spend's FACTORS, the declared ``derive_spend`` transform
    multiplies them into the ``amount``, and ``_doa_tier`` consumes it to resolve the tier — the
    amount the shipped ``ActionStepExecutor`` dropped, which left the approve gate unable to route
    the DOA tier.

    The transform step is LOADED FROM the shipped procurement ``procedures.yaml`` rather than
    hand-authored here, so this asserts that the declaration which actually ships wires the seam;
    hand-authored ops would let the yaml drift while this test kept passing."""
    ctx = _ctx()
    wrapper = GovernanceActionExecutor(
        base=_FakeBase(),
        principals=_controller_principals(),
        sod_steps=frozenset({"approve"}),
    )
    # 1. source: scored_rule selects RapidMRO + EMITS the two spend factors onto the entity.
    src = await wrapper.execute(_source_step(), [_hero_pr()], ctx)
    assert src.output[0]["selected_unit_price"] == "96000"
    assert src.output[0]["selected_qty"] == "3"
    assert src.output[0]["currency"] == "THB"
    assert "amount" not in src.output[0]  # the spend is the transform's to derive, not this step's
    # 2. derive_spend: the SHIPPED declared transform multiplies the factors into the ฿ spend.
    spec = load_procedures("procurement")
    proc = next(p for p in spec.procedures if p.procedure_id == "emergency_sourcing_round")
    derive_spend = next(s for s in proc.steps if s.step_id == "derive_spend")
    spend = await TransformStepExecutor().execute(derive_spend, src.output, ctx)
    assert spend.output[0]["amount"] == "288000"
    # 3. approve: doa_tier consumes the DERIVED spend -> resolves the CONTROLLER tier.
    appr = await wrapper.execute(_approve_step(), spend.output, ctx)
    assert appr.audit is not None
    assert appr.audit["governed_kind"] == "doa_tier"
    [verdict] = appr.audit["doa_tier"]
    assert verdict["resolved_tier_id"] == "CONTROLLER"
    assert verdict["amount"] == {"value": "288000", "currency": "THB"}
    assert verdict["resolved_approver_id"] == "appr-controller"
    assert verdict["sod_required"] is True
