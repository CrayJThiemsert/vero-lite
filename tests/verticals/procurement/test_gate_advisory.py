"""PLAN-0085 — the advisory gate recommendation (AI-Transition Rung 1), offline gate.

Covers AC-2 (advisory persisted in the parked approve step's trace), AC-3 (never-raise:
a raising builder cannot fail/park/divert the run), AC-4 (the L-B fence as a test —
advisory-on vs advisory-off runs differ in NOTHING but the one trace entry; the approve
audit is byte-identical), AC-6 (hash discipline, the SD-1(b) arm: the governance pins
of all three touched procedures are unchanged by the wiring), and the builder's L-C
conformance (no numeric confidence anywhere in the entry).

Offline + LLM-free: the run uses the production ``advisory_stub_factory`` ChatClient
(no network, no MS-S1) — the same client the registered procurement factory binds.
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from services.engine.procedures.advisory_stub import advisory_stub_factory
from services.engine.procedures.doa_tier import resolve_doa_tier
from services.engine.procedures.gate_advisory import (
    ADVISORY_TRACE_KIND,
    GateAdvisoryBuilder,
)
from services.engine.procedures.governance_pin import governance_pin_for
from services.engine.procedures.orchestrator import RunResult, run_procedure
from services.engine.procedures.spec import DoaLadder, load_procedures
from verticals.procurement.data_adapter.fastenal_csv import FastenalCsvAdapter
from verticals.procurement.hero_demo.procedure import (
    fastenal_hero_procedure,
    load_fastenal_principals,
)
from verticals.procurement.hero_demo.run import _ensure_handlers, _executors, _intake_seed

_VERTICAL = "procurement"


class _ExplodingBuilder(GateAdvisoryBuilder):
    """AC-3 test double: the builder's entry construction ALWAYS raises."""

    async def _entry(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("forced advisory failure (AC-3)")


def _assert_no_confidence(node: Any) -> None:
    """L-C: no key named 'confidence' anywhere in the advisory entry (recursive)."""
    if isinstance(node, dict):
        assert "confidence" not in node
        for value in node.values():
            _assert_no_confidence(value)
    elif isinstance(node, list):
        for item in node:
            _assert_no_confidence(item)


async def _run_hero(run_id: str, advisory_builder: GateAdvisoryBuilder | None) -> RunResult:
    """The test_hero_run harness shape: the full Fastenal loop in memory, parked at
    the approve gate, with the advisory builder under test (or None = baseline)."""
    adapter = FastenalCsvAdapter()
    _ensure_handlers()  # the run_hero_governance_moment precondition (handler registry)
    proc, agent = fastenal_hero_procedure()
    principals = await load_fastenal_principals(adapter)
    requester = next(p for p in principals if p.person_id == "req-maint-planner")
    seed = [await _intake_seed(adapter)]
    return await run_procedure(
        proc,
        agent,
        _executors(advisory_stub_factory, principals, seed, advisory_builder=advisory_builder),
        vertical=_VERTICAL,
        run_id=run_id,
        principal=requester,
    )


def _approve(result: RunResult) -> Any:
    return next(s for s in result.step_results if s.step_id == "approve")


def _advisory_entries(step_result: Any) -> list[dict[str, Any]]:
    return [e for e in (step_result.reasoning_trace or []) if e.get("kind") == ADVISORY_TRACE_KIND]


# ---------------------------------------------------------------- unit: the builder


async def test_builder_grounds_reasons_in_the_verdict() -> None:
    """The deterministic arm derives every reason from the gate verdict/ladder —
    band + role, SoD, the escalate-never-skip waiver posture (no model output)."""
    proc, _ = fastenal_hero_procedure()
    approve = next(s for s in proc.steps if s.step_id == "approve")
    ladder = approve.governance_content
    assert isinstance(ladder, DoaLadder)
    principals = await load_fastenal_principals()
    verdict = resolve_doa_tier(
        ladder,
        amount=Decimal("288000"),
        currency="THB",
        principals=principals,
        sod_required=True,
    )
    builder = GateAdvisoryBuilder()
    [entry] = await builder.build(
        step=approve,
        ladder=ladder,
        verdicts=[verdict],
        input_set=[],
        ctx=None,  # type: ignore[arg-type]
    )
    assert entry["kind"] == ADVISORY_TRACE_KIND
    assert "288000" in entry["summary"]
    detail = entry["detail"]
    assert detail["model"] == "deterministic"  # SD-2 arm disclosure
    assert detail["tier"] == verdict.resolved_tier_id
    assert detail["approver_role"] == verdict.required_role
    reasons = detail["reasons"]
    assert any("band" in r for r in reasons)  # amount-vs-band grounding
    assert any("Separation of duties" in r for r in reasons)  # SoD (sod_required=True)
    assert any("never skipped" in r for r in reasons)  # waiver posture
    _assert_no_confidence(entry)  # L-C / AC-8


async def test_builder_never_raises_on_empty_verdicts() -> None:
    """No verdicts -> the internal ValueError is swallowed -> [] (never-raise)."""
    proc, _ = fastenal_hero_procedure()
    approve = next(s for s in proc.steps if s.step_id == "approve")
    ladder = approve.governance_content
    assert isinstance(ladder, DoaLadder)
    out = await GateAdvisoryBuilder().build(
        step=approve,
        ladder=ladder,
        verdicts=[],
        input_set=[],
        ctx=None,  # type: ignore[arg-type]
    )
    assert out == []


# ------------------------------------------------------- AC-2: persisted at the park


async def test_advisory_rides_the_parked_approve_trace() -> None:
    result = await _run_hero("adv-on", GateAdvisoryBuilder())
    approve_sr = _approve(result)
    assert approve_sr.status == "waiting_human"  # the gate still parks (L-B)
    [entry] = _advisory_entries(approve_sr)  # exactly one advisory entry
    assert entry["detail"]["model"] == "deterministic"
    assert len(entry["detail"]["reasons"]) >= 3
    _assert_no_confidence(entry)
    # Trace-only by construction: the advisory writes nothing to the audit block.
    assert "advisory" not in json.dumps(approve_sr.audit or {}).lower()


# ------------------------------------------------- AC-3 + AC-4: the fences as tests


async def test_raising_builder_cannot_harm_the_run_and_no_routing_delta() -> None:
    """Three runs — baseline (no builder), advisory-on, exploding builder — must be
    identical in statuses, gate, tier resolution, and the approve step's AUDIT bytes;
    the ONLY delta anywhere is the single advisory trace entry on the on-run."""
    baseline = await _run_hero("adv-off", None)
    on = await _run_hero("adv-on-2", GateAdvisoryBuilder())
    exploding = await _run_hero("adv-boom", _ExplodingBuilder())

    # AC-3: the raising builder changed nothing vs baseline.
    for a, b in ((baseline, exploding), (baseline, on)):
        assert [s.status for s in a.step_results] == [s.status for s in b.step_results]
        assert [s.step_id for s in a.step_results] == [s.step_id for s in b.step_results]
    assert _advisory_entries(_approve(exploding)) == []  # degraded to absent, never an error

    # AC-4: byte-identical approve audit (the doa_tier routing record) across all arms.
    base_audit = json.dumps(_approve(baseline).audit, sort_keys=True)
    assert json.dumps(_approve(on).audit, sort_keys=True) == base_audit
    assert json.dumps(_approve(exploding).audit, sort_keys=True) == base_audit

    # AC-4: the on-run's approve trace = baseline's trace + exactly the one advisory
    # entry appended (kind-sequence comparison — volatile per-run ids stay out of it).
    base_kinds = [e.get("kind") for e in _approve(baseline).reasoning_trace or []]
    on_kinds = [e.get("kind") for e in _approve(on).reasoning_trace or []]
    assert on_kinds == [*base_kinds, ADVISORY_TRACE_KIND]


# ------------------------------------------------------------- AC-6: hash discipline


def test_governance_pins_unchanged_by_the_advisory_wiring() -> None:
    """SD-1(b): the advisory is executor wiring, not governance content — the pinned
    hashes of all three touched procedures stay the documented values (runbook §3c).
    If this test goes RED the wiring leaked into the governance surface — stop."""
    # Not secrets: the PUBLIC pinned governance-hash prefixes, already documented in
    # docs/runbooks/run-oct-demo.md §3c (detect-secrets false-positives on hex).
    pinned = {
        "emergency_sourcing_round": "eb4aa90c3496",  # pragma: allowlist secret
        "event_emergency_sourcing_round": "594596cccc6a",  # pragma: allowlist secret
        "scheduled_emergency_sourcing_round": "5cb26744115a",  # pragma: allowlist secret
    }
    spec = load_procedures(_VERTICAL)
    seen = {
        p.procedure_id: governance_pin_for(p)[1][:12]
        for p in spec.procedures
        if p.procedure_id in pinned
    }
    assert seen == pinned
