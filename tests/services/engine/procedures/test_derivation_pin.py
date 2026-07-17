"""PLAN-0078 PR-5 (AC-10, AC-11) — the DECLARED-derivation pin marker.

**What this module used to be, and why it changed.** Under PLAN-0075 AC-13 (the ratified
SD-5 provenance fold-in) the supply_chain severity ladder lived in vertical CODE, so the
governance pin — a snapshot of the DECLARATION — could not reach it. The workaround was a
side-channel ``sha256`` of the code constants, threaded by vertical through a registry hook
and folded into the snapshot. PLAN-0078 promoted BOTH shipped derivations to declared data
(supply_chain's severity ladder, PR-3; procurement's ฿ spend, PR-4), so the per-step
``transform`` key now pins the governing datum itself and the code-hash was retired
end-to-end in PR-5 (AC-10). This module is its replacement, and it must keep the two
guarantees the retired suite bought:

* **mid-flight tamper-evidence** — a run-start↔resolve edit to a derivation fails CLOSED at
  the pin. Preserved here at FULL strength: the tests below drive
  :func:`assert_governance_pin` until it RAISES, exactly as the retired
  ``test_mutated_dose_ladder_fails_closed_at_the_pin`` did. (A test that merely compares two
  config hashes — ``test_transform_grammar.py``'s pin block — proves the hash MOVES, not that
  the run REFUSES; it does not discharge this.)
* **the un-bounded top band is covered** — the AC-13 drafter finding, preserved: a ladder that
  pinned only its enumerated bands would let an edit re-point the unbounded top band
  silently. The declared form's mandatory ``above`` is asserted to trip the pin too.

**The marker (AC-11, the rewritten SD-5 self-canceller).** The retired marker asserted an
ASYMMETRY: supply_chain pinned its derivation, procurement did not, because procurement's
imperative ฿ math had "no clean datum to hash". PLAN-0078 dissolved that premise — the ฿ is
now ``derive_spend``, declared. So the marker no longer tracks a residual; it asserts the
END STATE both PRs bought: **every shipped derivation rides the pin as declared data, and no
code-hash seam survives to compete with it** (:func:`test_declared_derivation_marker`).

**F-PIN is NOT closed by any of this (PLAN-0078 L-4).** The new-run re-routing threat — a
fresh run on already-changed declared data pins the change without complaint — is an
architectural property of per-run pinning, orthogonal to where the derivation lives.
PLAN-0076 Step T2 (the remainder fold-in: retire the code-hash, rewrite this marker) is what
closes here; the threat itself stays open and tracked, and PLAN-0076 does NOT archive.

Pure + offline (CLAUDE.md §8 — the offline oracle is the gate): no DB, no LLM, no MS-S1.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from services.engine.procedures.governance_pin import build_governance_snapshot, governance_pin_for
from services.engine.procedures.orchestrator import ProcedureError
from services.engine.procedures.persistence import assert_governance_pin
from services.engine.procedures.runs import PipelineRun, PipelineRunStatus
from services.engine.procedures.spec import (
    MapValueBody,
    Procedure,
    StepKind,
    load_procedures,
)

_SUPPLY_CHAIN_PROC = "cold_chain_excursion_disposition"

_ALL_VERTICALS = ["supply_chain", "procurement", "energy", "aquaculture"]

# AC-6's non-participant VERTICAL set: the verticals that declare no transform at all, and so
# must pin byte-identically to before the migration. Pinned as data (not prose) by
# `test_the_non_participant_vertical_set_holds` — if a later phase migrates one of these, the
# census goes RED and forces the sweep to be re-run rather than assumed.
_NON_PARTICIPANT_VERTICALS = {"energy", "aquaculture"}

_TS = datetime(2026, 1, 1, tzinfo=UTC)  # fixed — never the (non-monotonic WSL2) wall clock

# The GOVERNING ladder, hand-written from `verticals/supply_chain/procedures.yaml` — NOT
# imported from `cold_chain_assess._DOSE_LADDER`. That tuple is a test-only reference since
# PR-5 (it governs nothing); importing it here would let a yaml edit and a code edit drift
# together unnoticed — the exact hole PLAN-0075 AC-13 closed by hashing the constants
# THEMSELVES, and the reason `test_severity_transform_pin_coverage` states the same rule.
_GOVERNING_BANDS = [("0.25", "negligible"), ("0.50", "minor"), ("1.00", "major")]
_GOVERNING_ABOVE = "critical"


def _procedure(vertical: str, procedure_id: str) -> Procedure:
    spec = load_procedures(vertical)
    return next(p for p in spec.procedures if p.procedure_id == procedure_id)


def _run(snapshot: dict[str, object], config_hash: str) -> PipelineRun:
    """A suspended run pinned at ``config_hash`` — constructed in memory (no session, no DB)."""
    return PipelineRun(
        run_id="run-pr5",
        procedure_id=_SUPPLY_CHAIN_PROC,
        agent_id="a",
        status=PipelineRunStatus.WAITING_HUMAN.value,
        started_at=_TS,
        updated_at=_TS,
        governance_snapshot=snapshot,
        governance_hash=config_hash,
    )


def _severity_ladder(procedure: Procedure) -> MapValueBody:
    """The declared severity ladder of ``procedure`` — the map_value targeting the field the
    ``severity_tier`` gate reads. Fails the test loudly if the declaration moved."""
    for step in procedure.steps:
        if step.transform is None:
            continue
        for op in step.transform.ops:
            body = getattr(op, "map_value", None)
            if body is not None and body.target == "excursion_severity":
                return body
    raise AssertionError(
        f"{procedure.procedure_id} declares no 'excursion_severity' map_value — the severity "
        "derivation left the declaration (PLAN-0078 PR-3 flip regressed, or the step moved)"
    )


def _transform_targets(procedure: Procedure) -> set[str]:
    """Every field written by any declared transform op on ``procedure``."""
    targets: set[str] = set()
    for step in procedure.steps:
        if step.transform is None:
            continue
        for op in step.transform.ops:
            for body in vars(op).values():
                target = getattr(body, "target", None)
                if target is not None:
                    targets.add(target)
    return targets


# --------------------------------------------------------------------------- #
# The governing datum rides the pin (what replaced the code-hash)
# --------------------------------------------------------------------------- #


def test_supply_chain_severity_ladder_rides_the_pin() -> None:
    """The ladder the ``severity_tier`` gate ultimately routes on is IN the run's governance
    snapshot, canonically — so "which derivation governed THIS run?" is answered by the run
    record itself, which is the provenance half of what AC-13's code-hash bought."""
    procedure = _procedure("supply_chain", _SUPPLY_CHAIN_PROC)
    snapshot = build_governance_snapshot(procedure)

    ladders = [
        op["map_value"]
        for step in snapshot["steps"]
        if step.get("transform")
        for op in step["transform"]["ops"]
        if "map_value" in op and op["map_value"]["target"] == "excursion_severity"
    ]
    assert len(ladders) == 1, "exactly one step must declare the severity ladder"
    [ladder] = ladders
    assert [(b["ceiling"], b["value"]) for b in ladder["bands"]] == _GOVERNING_BANDS
    assert ladder["above"] == _GOVERNING_ABOVE, "the unbounded top band must stay total-cover"


def test_procurement_spend_derivation_rides_the_pin() -> None:
    """The ฿ the ``doa_tier`` gate routes on is declared + pinned in EVERY procurement
    procedure that scores a supplier — the PR-4 (SD-8 (a) "one derivation home") end state,
    and the reason the retired marker's supply_chain-vs-procurement asymmetry is gone."""
    spec = load_procedures("procurement")
    scoring = [p for p in spec.procedures if any(s.step_id == "source" for s in p.steps)]
    assert scoring, "no procurement procedure scores a supplier — the fixture moved"

    for procedure in scoring:
        snapshot = build_governance_snapshot(procedure)
        pinned_targets = {
            body["target"]
            for step in snapshot["steps"]
            if step.get("transform")
            for op in step["transform"]["ops"]
            for body in op.values()
            if isinstance(body, dict) and "target" in body
        }
        assert "amount" in pinned_targets, (
            f"{procedure.procedure_id}: the spend the doa_tier gate reads is not pinned as a "
            "declared derivation (PLAN-0078 AC-8 regressed)"
        )


# --------------------------------------------------------------------------- #
# Mid-flight tamper-evidence — preserved at FULL strength (the pin REFUSES)
# --------------------------------------------------------------------------- #


def test_unmutated_derivation_does_not_trip_the_pin() -> None:
    """The control: an unchanged declaration between run-start and resolve is inert — the pin
    only fires on a MISMATCH, never on every gate."""
    procedure = _procedure("supply_chain", _SUPPLY_CHAIN_PROC)
    snapshot, pinned = governance_pin_for(procedure)
    assert_governance_pin(_run(snapshot, pinned), procedure, context="test")


def test_midflight_ladder_band_edit_fails_closed_at_the_pin() -> None:
    """A mid-flight ladder edit (a re-pointed band ceiling) recomputes to a different config
    hash at resolve, so the pin REFUSES — the sanctioned cancel-and-restart path.

    This is the declared-data successor to the retired
    ``test_mutated_dose_ladder_fails_closed_at_the_pin``, and it drives the same assertion
    (``assert_governance_pin`` raises), not a weaker hash comparison."""
    procedure = _procedure("supply_chain", _SUPPLY_CHAIN_PROC)
    snapshot, pinned = governance_pin_for(procedure)
    run = _run(snapshot, pinned)

    mutated = procedure.model_copy(deep=True)
    ladder = _severity_ladder(mutated)
    assert ladder.bands[-1].ceiling == "1.00"  # the band being re-pointed, pinned explicitly
    ladder.bands[-1].ceiling = "0.99"  # a batch at ratio 1.00 is no longer 'major'

    with pytest.raises(ProcedureError, match="governance-config pin mismatch"):
        assert_governance_pin(run, mutated, context="gate resolution")


def test_midflight_top_band_edit_fails_closed_at_the_pin() -> None:
    """The AC-13 drafter finding, PRESERVED across the migration: the unbounded top band is a
    SEPARATE datum from the enumerated bands. Under the code-hash a ladder-tuple-only hash
    would not have moved when only ``_TOP_SEVERITY`` was re-pointed; under the declared form
    the mandatory ``above`` is part of the pinned transform, so the same weakening — the top
    band no longer meaning CRITICAL — fails closed here too."""
    procedure = _procedure("supply_chain", _SUPPLY_CHAIN_PROC)
    snapshot, pinned = governance_pin_for(procedure)
    run = _run(snapshot, pinned)

    mutated = procedure.model_copy(deep=True)
    ladder = _severity_ladder(mutated)
    assert ladder.above == _GOVERNING_ABOVE  # the band being weakened, pinned explicitly
    ladder.above = "major"  # a batch past its whole stability budget would stop being critical

    with pytest.raises(ProcedureError, match="governance-config pin mismatch"):
        assert_governance_pin(run, mutated, context="gate resolution")


# --------------------------------------------------------------------------- #
# AC-11 — the rewritten marker (supersedes the F-PIN residual self-canceller)
# --------------------------------------------------------------------------- #


def test_declared_derivation_marker() -> None:
    """The AC-11 marker. The retired form asserted supply_chain-pins / procurement-does-not —
    an asymmetry that rested on procurement's ฿ having "no clean datum to hash". PLAN-0078
    dissolved that premise by declaring BOTH derivations, so this asserts the end state:

    * supply_chain's severity ladder is declared (its WHY values, ``dose_ch`` / ``ratio``,
      materialized per the ratified OQ-5 — so the audit surface the retired
      ``severity_derivation`` payload carried survives the change of form);
    * procurement's ฿ spend is declared;
    * and no snapshot carries a competing code-side derivation key
      (:func:`test_every_snapshot_carries_exactly_the_declared_surface`).

    If a future vertical derives an authority quantity in CODE again, that is not this
    marker's failure — it is a new ADR-0031 D3 row-1 case-2 signature, and it routes to a
    PLAN, not to a resurrection of the retired code-hash."""
    supply_chain = _procedure("supply_chain", _SUPPLY_CHAIN_PROC)
    assert {"dose_ch", "ratio", "excursion_severity", "criticality"} <= _transform_targets(
        supply_chain
    ), "supply_chain's severity derivation (incl. the OQ-5 WHY values) must be declared data"

    spec = load_procedures("procurement")
    hero = next(p for p in spec.procedures if any(s.step_id == "source" for s in p.steps))
    assert "amount" in _transform_targets(hero), "procurement's ฿ spend must be declared data"

    for procedure in (supply_chain, hero):
        assert any(
            step.kind is StepKind.TRANSFORM for step in procedure.steps
        ), f"{procedure.procedure_id} declares no transform step"


@pytest.mark.parametrize("vertical", _ALL_VERTICALS)
def test_every_snapshot_carries_exactly_the_declared_surface(vertical: str) -> None:
    """AC-10 + AC-5's "asserted, intended pin change" leg: the governance snapshot's top-level
    surface is EXACTLY the declared config — procedure id, SoD, steps — and nothing else.

    This is the assertion that makes supply_chain's config-hash change at PR-5 **intended
    rather than silently absorbed**. Retiring the PLAN-0075 AC-13 code-hash removed a key
    that supply_chain's snapshot (alone) used to carry; its hash therefore MOVED, and a
    persisted mid-flight run of that procedure fails closed at resume — the pin working as
    designed, disclosed in PLAN-0078's "Pin consequence of migrating" section.

    Asserted as an EXACT key set, not as the absence of the retired name: the retired key is
    one of infinitely many that must not be here, and pinning the whole surface also catches a
    NEW side-channel key being folded in later — the same failure class, next time round. The
    derivation itself is pinned one level down, inside ``steps[].transform`` (PLAN-0077)."""
    spec = load_procedures(vertical)
    assert spec.procedures, f"{vertical} declares no procedures — the fixture moved"
    for procedure in spec.procedures:
        assert set(build_governance_snapshot(procedure)) == {
            "procedure_id",
            "separation_of_duties",
            "steps",
        }, f"{vertical}/{procedure.procedure_id}: unexpected top-level governance-snapshot key"


@pytest.mark.parametrize("vertical", _ALL_VERTICALS)
def test_transform_pins_exactly_when_the_step_declares_one(vertical: str) -> None:
    """AC-6 (byte-identical non-participants) at the STEP level, on SHIPPED yaml.

    The sibling above pins the TOP-LEVEL surface; this pins the level AC-6 actually speaks
    about. AC-6's guarantee is the only-when-supplied property (``governance_pin.py:98-99``):
    a step that declares no transform gets no ``transform`` key, so its snapshot — and
    therefore its config hash — is byte-identical to the pre-PLAN-0077 world and no persisted
    run refuses at resume.

    Why this existed nowhere before Step 7, despite two sweeps and a grammar test already
    asserting something adjacent (the AC-6 hole, found by grounding the PLAN against code
    rather than by reading its Phase-1 "leg GREEN" note):

    * ``test_transform_grammar.py:308`` asserts it on a SYNTHETIC procedure built in-test —
      it proves the projection function's behaviour, never that the shipped yaml still has
      the shape the projection was proved against;
    * the two migration-parity sweeps
      (``test_transform_migration_parity.py``, supply_chain ``:236`` + procurement ``:244``)
      assert it only for the non-participant PROCEDURES *inside the two migrated verticals*;
    * nothing at all covered energy and aquaculture — the two verticals AC-6 names FIRST.

    Asserted as an IFF over every step of every shipped procedure, so it is one property
    rather than two lists to keep in sync: the negative arm carries AC-6's claim for the
    non-participants, and the positive arm is what keeps this test from passing vacuously in
    a world where the projection silently stopped emitting the key at all (which would take
    AC-5's pin coverage down with it, unnoticed)."""
    spec = load_procedures(vertical)
    assert spec.procedures, f"{vertical} declares no procedures — the fixture moved"
    for procedure in spec.procedures:
        snapshot = build_governance_snapshot(procedure)
        for step, step_snapshot in zip(procedure.steps, snapshot["steps"], strict=True):
            assert ("transform" in step_snapshot) is (step.transform is not None), (
                f"{vertical}/{procedure.procedure_id}/{step.step_id}: the `transform` key must "
                f"be present in the governance snapshot EXACTLY when the step declares a "
                f"transform (only-when-supplied, governance_pin.py:98-99)"
            )


def test_the_non_participant_vertical_set_holds() -> None:
    """AC-6's tripwire: WHICH verticals are the non-participants is pinned as data.

    PLAN-0078 predicted that Phase 2 would shrink this set ("Phase 2 adds transforms, so the
    non-participant set shrinks and must be re-swept", AC-6's original parenthetical). That
    prediction was **superseded by how Phase 2 actually landed** (CLAUDE.md §6 — evolution,
    not an error): PR-3 and PR-4 added transforms only to procedures that ALREADY carried a
    Phase-1 ``enrich`` — procurement's three ``emergency_sourcing_round`` variants and
    supply_chain's ``cold_chain_excursion_disposition`` — so the set never moved.

    It is pinned here rather than re-argued in prose because the prediction was reasonable and
    could come true next time. A later phase that migrates energy or aquaculture turns this
    RED, which forces the sweep above to be genuinely re-run rather than assumed still-covered
    — the house rule that location is convention and only a failing test is a tripwire
    (PLAN-0076 AC-6's reasoning, applied to the set AC-6 itself enumerates)."""
    census = {
        vertical: sum(
            1
            for procedure in load_procedures(vertical).procedures
            for step in procedure.steps
            if step.transform is not None
        )
        for vertical in _ALL_VERTICALS
    }

    assert {v for v, n in census.items() if n == 0} == _NON_PARTICIPANT_VERTICALS, (
        f"AC-6's non-participant vertical set moved: {census}. If a vertical was deliberately "
        f"migrated, re-run the AC-6 sweep and update _NON_PARTICIPANT_VERTICALS in the same "
        f"pass — do not just widen the constant."
    )
    # Non-vacuity: the participants must genuinely declare transforms, else the IFF sweep above
    # would be asserting the negative arm everywhere and proving nothing about AC-5's coverage.
    assert census["supply_chain"] and census["procurement"], (
        f"both migrated verticals must declare transforms — the Phase-1/Phase-2 flips are the "
        f"reason this module exists: {census}"
    )
