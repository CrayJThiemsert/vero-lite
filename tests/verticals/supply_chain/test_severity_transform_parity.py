"""PLAN-0078 PR-3 (AC-7, AC-12): the supply_chain severity re-sequencing parity harness.

**Oracle-first** (PLAN-0077 SD-5 / Lesson #0026): every assertion here is proven GREEN against
the CURRENT (``ColdChainAssessExecutor``-stamped) world in the oracle commit, and must stay green
UNCHANGED after the flip moves the derivation into the declared ``enrich`` transform — or the flip
does not land (L-2 / the ratified SD-6 bar).

**The SD-6 two-tier bar** — a byte-equal whole run record is impossible BY DESIGN once the
derivation moves (the executor's ``severity_derivation`` audit + ``severity_derived`` trace become
the transform's ``transform_provenance``). So this harness proves the two tiers SD-6 ratified:

* **(i) output-ROW byte parity** — every governance-relevant field the gates read
  (``excursion_severity``, ``criticality``) plus every Phase-1 field, byte-equal in its exact
  string form.
* **(ii) semantic run-record equivalence** — the scored-selection verdict, the GDP gate outcome,
  the severity_tier resolution (tier / required role / resolved approver), and the final run
  status are identical.
* **(iii) provenance completeness at the VALUE level** — the ratified OQ-5 (Cray, 2026-07-16:
  (a) materialize). Every value the retired ``severity_derivation`` audit carried is still
  recoverable FROM THE RECORD, not just re-derivable from the pinned spec.

**Flip-robust anchors — the assertions do not move when the derivation does.**

* The row is asserted at ``assess``'s OUTPUT, not ``enrich``'s. Pre-flip the executor stamps
  ``excursion_severity`` / ``criticality`` onto the row inside ``assess``; post-flip the transform
  writes them upstream and they flow THROUGH ``assess``. Both worlds carry them at the same
  anchor, so the same assertion holds across the flip.
* The six derivation values are recovered by ``_recover_derivation_values``, which reads the
  executor's audit projection pre-flip and the materialized row fields post-flip. The CONTRACT is
  "the WHY values are in the record" (``cold_chain_assess.SeverityDerivation``:
  "show WHY a batch is CRITICAL without re-deriving the math") — not "in this exact location".
  Values are compared Decimal-normalized because the two homes carry the same value in different
  JSON types (the audit projects ``duration_h`` as ``"9"``; the row defaults it as the int ``9``).

Why value-level and not op-level (the OQ-5 grounds, verified at revision): ``transform_provenance``
carries the op name, target and row count ONLY, never values (``transform_step.py:244-253``;
``_op_summary`` is "a display concern only", ``:184``), and ``_eval_expr`` returns just the tree's
final value (``:332``). Under the rejected alternative ``dose_ch`` / ``ratio`` would be computed
and DISCARDED, and answering "why CRITICAL?" would require re-running the pinned spec — a
re-derivation resting on the one guarantee F-PIN leaves open (L-4 / AC-11).

The references are hand-coded from the cold-chain demo contract (not read back from the
executor), so slimming the executor cannot silently drift them (the PLAN-0062 property).

Deterministic, offline, no MS-S1, no DB (the synthetic adapter + the registered factory).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from services.api.config import settings
from services.engine.discovery import discover_and_register
from services.engine.procedures.orchestrator import RunContext, RunResult, run_procedure
from services.engine.procedures.runs import PipelineRunStatus, StepResultStatus
from services.engine.procedures.spec import StepKind, load_procedures
from services.engine.registry import ExecutorFactory, registry
from tests.verticals.supply_chain.test_transform_migration_parity import _FROZEN_ENRICHED_INTAKE
from verticals.supply_chain.cold_chain_assess import ColdChainAssessError
from verticals.supply_chain.procedures_factory import register_supply_chain_procedure_executors

_VERTICAL = "supply_chain"
_PROC = "cold_chain_excursion_disposition"
_COLD_CHAIN_CEILING = 8.0

# (i) The gate-read + amplifier fields, frozen in their EXACT string forms.
#
#   magnitude 6.6 C x duration 9 h = dose 59.4 C*h; 59.4 / 24 C*h budget = ratio 2.475.
#   2.475 exceeds every _DOSE_LADDER ceiling (0.25 / 0.50 / 1.00) -> the unbounded top band.
#   criticality = str(min(Decimal(1), 2.475)) = "1" (the scored rule's [0,1] amplifier, clamped).
_FROZEN_SEVERITY_FIELDS: dict[str, Any] = {
    "excursion_severity": "critical",
    "criticality": "1",
}

# (iii) Every value the retired `severity_derivation` audit projection carried (OQ-5 = materialize).
# Decimal-normalized: the two homes agree on VALUE, not on JSON type (see the module docstring).
_FROZEN_DERIVATION_VALUES: dict[str, str] = {
    "magnitude_c": "6.6",
    "duration_h": "9",
    "dose_ch": "59.4",
    "budget_ch": "24",
    "ratio": "2.475",
}

# Where each derivation value lives on the ROW post-flip (the OQ-5 materialization targets).
# `dose_ch` / `ratio` are the two the flip must ADD; the other three already ride the Phase-1 row.
_ROW_FIELD_BY_DERIVATION_KEY = {
    "magnitude_c": "excursion_magnitude_c",
    "duration_h": "excursion_duration_h",
    "dose_ch": "dose_ch",
    "budget_ch": "stability_budget_ch",
    "ratio": "ratio",
}


@pytest.fixture
async def supply_chain_factory(monkeypatch: pytest.MonkeyPatch) -> ExecutorFactory:
    """The registered supply_chain factory — the same registration path ``services/api/main.py``
    runs at startup."""
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    monkeypatch.setattr(settings, "oct_recommend_threshold", _COLD_CHAIN_CEILING)
    monkeypatch.setattr(settings, "oct_recommend_direction", "above")
    discover_and_register()
    await register_supply_chain_procedure_executors()
    return registry.get_procedure_executors(_VERTICAL)


async def _run_disposition(factory: ExecutorFactory, run_id: str = "pr3-parity") -> RunResult:
    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == _PROC)
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    return await run_procedure(proc, agent, factory(), vertical=_VERTICAL, run_id=run_id)


def _norm(value: Any) -> str:
    """Decimal-normalize a JSON-carried numeric to its exact string form.

    The audit projection and the row carry the SAME value in different JSON types (``"9"`` vs
    ``9``), so the flip-robust comparison is on the Decimal value, never the JSON type."""
    return str(Decimal(str(value)))


def _recover_derivation_values(result: RunResult) -> dict[str, str]:
    """Recover the six derivation values FROM THE RUN RECORD, wherever this world homes them.

    Pre-flip: the ``ColdChainAssessExecutor``'s ``severity_derivation`` audit projection.
    Post-flip: the materialized row fields on the step feeding ``assess`` (OQ-5 = materialize).

    Deliberately NOT a re-derivation — recovering by recomputing would assert nothing about
    whether the record can answer "why CRITICAL?" on its own, which is the whole OQ-5 contract."""
    by_step = {s.step_id: s for s in result.step_results}
    assess_audit = by_step["assess"].audit or {}

    if "severity_derivation" in assess_audit:  # pre-flip: the executor's audit projection
        [derivation] = assess_audit["severity_derivation"]
        return {key: _norm(derivation[key]) for key in _FROZEN_DERIVATION_VALUES}

    # post-flip: the materialized fields on the row feeding `assess`
    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == _PROC)
    assess_step = next(s for s in proc.steps if s.step_id == "assess")
    assert assess_step.input is not None and assess_step.input.from_step is not None
    feeder = by_step[assess_step.input.from_step].artifact
    assert feeder is not None
    [row] = feeder["output_set"]
    missing = [k for k, f in _ROW_FIELD_BY_DERIVATION_KEY.items() if f not in row]
    assert not missing, (
        f"OQ-5 (materialize) regression: the row feeding 'assess' carries no {missing} — the WHY "
        "values vanished from the record, so it can no longer answer 'why CRITICAL?' without "
        "re-running the pinned spec. See the module docstring."
    )
    return {key: _norm(row[_ROW_FIELD_BY_DERIVATION_KEY[key]]) for key in _FROZEN_DERIVATION_VALUES}


async def test_severity_row_parity_at_the_assess_anchor(
    supply_chain_factory: ExecutorFactory,
) -> None:
    """AC-7(i): output-ROW byte parity. ``excursion_severity`` + ``criticality`` carry their exact
    frozen string forms, and every Phase-1 field is byte-equal, on the row ``assess`` outputs —
    the anchor both worlds share (executor-stamped pre-flip, transform-threaded post-flip)."""
    result = await _run_disposition(supply_chain_factory)
    by_step = {s.step_id: s for s in result.step_results}
    artifact = by_step["assess"].artifact
    assert artifact is not None
    [row] = artifact["output_set"]

    for field, expected in _FROZEN_SEVERITY_FIELDS.items():
        assert row[field] == expected, f"{field}: {row[field]!r} != frozen {expected!r}"

    # every Phase-1 field survives the re-sequencing byte-for-byte (the PR-2 frozen reference is
    # the source of truth — importing it means a Phase-1 drift breaks HERE too, not silently).
    for field, expected in _FROZEN_ENRICHED_INTAKE.items():
        assert row[field] == expected, f"Phase-1 field {field}: {row[field]!r} != {expected!r}"


async def test_semantic_run_record_equivalence(supply_chain_factory: ExecutorFactory) -> None:
    """AC-7(ii): semantic run-record equivalence — the scored selection, the GDP gate outcome, the
    severity_tier resolution, and the final run status are identical across the flip. These are the
    GOVERNED verdicts: if the re-sequencing moved a single one, the flip changed who decides."""
    result = await _run_disposition(supply_chain_factory)
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    by_step = {s.step_id: s for s in result.step_results}

    assess_audit = by_step["assess"].audit
    assert assess_audit is not None
    [scored] = assess_audit["scored_rule"]
    assert scored["selected_quote_id"] == "lane-licensed-destruction"
    # PLAN-0078 PR-4 re-sequenced the spend: the verdict carries the two FACTORS where it carried
    # `{"amount": {"value": "63000.000", "currency": "THB"}}`, and the declared `derive_spend`
    # transform now multiplies them (SD-8(a) one derivation home; the audit form change is
    # SD-6(ii)). The ฿ itself is still pinned byte-equal — on the ROW, at the gate anchor, in
    # `test_amount_transform_parity.py`. PR-3's severity assertions below are untouched.
    assert scored["selected_unit_price"] == "150.00"
    assert scored["qty"] == "420.0"
    assert scored["currency"] == "THB"
    assert scored["source_path"] == "default_source"
    assert scored["override_required"] is False

    gdp_audit = by_step["gdp_gate"].audit
    assert gdp_audit is not None
    [compliance] = gdp_audit["rule_gate"]
    assert compliance["compliant"] is True
    assert compliance["failed_criteria"] == []

    # the severity the transform derives must route to the SAME authority (money never routes it)
    approve_audit = by_step["approve"].audit
    assert approve_audit is not None
    [verdict] = approve_audit["severity_tier"]
    assert verdict["severity"] == "critical"
    assert verdict["required_role"] == "ผอ.ฝ่ายคุณภาพ"
    assert verdict["resolved_approver_id"] == "appr-qdir"
    assert verdict["sod_required"] is True

    assert by_step["assess"].status == StepResultStatus.COMPLETE.value
    assert by_step["gdp_gate"].status == StepResultStatus.COMPLETE.value
    assert by_step["approve"].status == StepResultStatus.WAITING_HUMAN.value
    assert "fulfill" not in by_step


async def test_provenance_completeness_at_the_value_level(
    supply_chain_factory: ExecutorFactory,
) -> None:
    """AC-7(iii) + the ratified OQ-5: every value the ``severity_derivation`` audit carried is
    still recoverable FROM THE RECORD after the flip — the "show WHY without re-deriving" contract
    (``cold_chain_assess.SeverityDerivation``) survives the change of FORM that SD-6(ii) permits.

    Pre-flip this reads the executor's audit; post-flip the materialized row fields. Green both
    ways, or the flip regressed a shipped audit surface."""
    result = await _run_disposition(supply_chain_factory)
    assert _recover_derivation_values(result) == _FROZEN_DERIVATION_VALUES


async def test_non_positive_scalar_refuses_at_assess(
    supply_chain_factory: ExecutorFactory,
) -> None:
    """AC-12 (the ratified SD-7): a non-positive excursion scalar REFUSES at ``assess``, which sits
    upstream of the ``approve`` severity gate — so a severity the engine had to guess never routes.

    This is the door SD-7 keeps rather than retires: the transform grammar CANNOT express the
    positivity guard — its ``_to_decimal`` accepts negatives (``transform_step.py:360-388``) and a
    negative ratio bands to the LOWEST severity (fail-DANGEROUS, the exact shape PLAN-0074 fixed).
    Post-flip the executor slims to exactly this guard; the assertion is unchanged either way.

    Driven on a MUTATED FIXTURE ROW against the shipped ``StepKind.ACTION`` executor (the AC-4
    pattern), NOT through a full run: ``_intake_seed``'s own magnitude<=0 eligibility guard
    (``procedures_factory.py:151``) filters a within-band batch out before intake, so a full-run
    mutation proves nothing about THIS door — it never reaches it. (Verified: an earlier full-run
    form of this test passed vacuously.) The two guards are independent closed doors by design."""
    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == _PROC)
    step_ids = [s.step_id for s in proc.steps]
    assert step_ids.index("assess") < step_ids.index(
        "approve"
    ), "AC-12 rests on 'assess' preceding the severity gate — the procedure re-ordered"

    assess_step = next(s for s in proc.steps if s.step_id == "assess")
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    ctx = RunContext(agent=agent, vertical=_VERTICAL)
    action_executor = supply_chain_factory()[StepKind.ACTION]

    # a reading BELOW the cargo's ceiling -> a negative magnitude -> a negative dose and ratio
    bad_row = {**_FROZEN_ENRICHED_INTAKE, "excursion_magnitude_c": "-58.0"}
    with pytest.raises(ColdChainAssessError):
        await action_executor.execute(assess_step, [bad_row], ctx)


def test_severity_transform_pin_coverage() -> None:
    """AC-5's Phase-2 leg: once the severity derivation is declared, it rides the governance
    snapshot — so a mid-flight ladder edit changes the config hash and fails CLOSED at resume
    (``governance_pin.py``), which is what made retiring the PLAN-0075 AC-13 code-hash honest in
    PR-5 (AC-10). That refusal is driven to its raise in ``test_derivation_pin.py``.

    Asserted structurally (the declared ops carry the ladder), NOT by importing ``_DOSE_LADDER`` —
    importing the constants would let a ladder edit drift both sides together, the exact hole
    PLAN-0075 AC-13 closed by hashing the constants THEMSELVES."""
    from services.engine.procedures.governance_pin import build_governance_snapshot

    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == _PROC)
    snapshot = build_governance_snapshot(proc)
    feeder_id = next(s for s in proc.steps if s.step_id == "assess").input.from_step  # type: ignore[union-attr]
    [feeder_snap] = [s for s in snapshot["steps"] if s["step_id"] == feeder_id]
    transform = feeder_snap.get("transform")
    assert transform is not None, "the step feeding 'assess' declares no transform"

    targets = {
        body["target"]
        for op in transform["ops"]
        for key, body in op.items()
        if isinstance(body, dict) and "target" in body
    }
    # The oracle-first skip this carried during the PR-3 two-commit flip is REMOVED (PR-5): the
    # flip landed, so a missing declaration is now a REGRESSION, and skipping on it would pass
    # vacuously — the one failure mode this test exists to catch.
    assert "excursion_severity" in targets, "the severity derivation is no longer declared"

    [map_op] = [op["map_value"] for op in transform["ops"] if "map_value" in op]
    assert map_op["target"] == "excursion_severity"
    assert [(b["ceiling"], b["value"]) for b in map_op["bands"]] == [
        ("0.25", "negligible"),
        ("0.50", "minor"),
        ("1.00", "major"),
    ]
    assert map_op["above"] == "critical", "the unbounded top band must stay total-cover (PLAN-0074)"
    assert {"dose_ch", "ratio", "criticality"} <= targets, "OQ-5: the WHY values must be declared"
