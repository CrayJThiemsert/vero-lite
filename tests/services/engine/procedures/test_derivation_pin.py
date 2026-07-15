"""PLAN-0075 AC-13 (SD-5 provenance fold-in) — the supply_chain severity-DERIVATION
constants are hashed into the run's governance snapshot.

PROVENANCE-ONLY (the ratified SD-5 split): folding the derivation hash into the pin buys
(i) mid-flight tamper-evidence — a run-start↔resolve edit to ``_DOSE_LADDER`` OR
``_TOP_SEVERITY`` fails CLOSED at the pin — and (ii) audit provenance (which derivation
governed THIS run). It does NOT close the new-run re-routing threat: F-PIN stays open
(procurement's imperative ฿ derivation has no clean datum — the tracked follow-on).

Pure + offline (CLAUDE.md §8 — the offline oracle is the gate): no DB, no LLM, no MS-S1.
The pass/fail reads are AC-13 (a)-(d):

* (a) the supply_chain snapshot carries a deterministic derivation hash, stable across
  processes (proved by a pinned golden sha256 + a within-process re-compute);
* (b) a mutated ``_DOSE_LADDER`` OR ``_TOP_SEVERITY`` between run-start and resolve fails
  closed at the pin (the ``_TOP_SEVERITY`` case is why the hash covers BOTH constants — a
  ladder-tuple-only hash would leave the unbounded critical band un-pinned);
* (c) procurement + energy + aquaculture snapshots are byte-identical to before (a vertical
  that pins no derivation passes ``None`` — no key added, no cross-vertical bleed);
* (d) a SELF-CANCELLING marker documents the F-PIN residual (procurement un-pinned),
  tripping when a procurement derivation hash lands and pointing at the follow-on.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from services.engine.discovery import discover_and_register
from services.engine.procedures.governance_pin import (
    build_governance_snapshot,
    compute_governance_hash,
    governance_pin_for,
)
from services.engine.procedures.orchestrator import ProcedureError
from services.engine.procedures.persistence import assert_governance_pin
from services.engine.procedures.runs import PipelineRun, PipelineRunStatus
from services.engine.procedures.spec import (
    ExcursionSeverity,
    Procedure,
    Step,
    StepKind,
    load_procedures_file,
)
from services.engine.registry import RegistryError, registry
from verticals.procurement.hero_demo.run import register_procurement_procedure_executors
from verticals.supply_chain import cold_chain_assess
from verticals.supply_chain.procedures_factory import register_supply_chain_procedure_executors

# The cross-PROCESS stability proof (AC-13 a): the canonical sha256 of the SHIPPED
# ``_DOSE_LADDER`` + ``_TOP_SEVERITY`` at this baseline. Pinned as a literal because a
# process-stable hash is exactly what a governance pin needs — if this drifts, either the
# constants changed (intended: bump this + re-argue) or the serialisation stopped being
# canonical (a real bug: str-hash randomisation, float, set ordering).
_GOLDEN = (
    "5db13dfce2bec97d81326252a2a1a7ec2828ac688c95a732510265c15a5557cc"  # pragma: allowlist secret
)

_TS = datetime(2026, 1, 1, tzinfo=UTC)  # fixed — never the (non-monotonic WSL2) wall clock


def _proc() -> Procedure:
    """A minimal procedure — ``build_governance_snapshot`` only reads its id / steps / SoD, so a
    one-step stub is enough to exercise the derivation-hash fold-in without any adapter."""
    return Procedure(
        procedure_id="cold_chain_excursion_disposition",
        title="Cold-chain disposition",
        run_by="a",
        steps=[Step(step_id="intake", name="Intake", kind=StepKind.QUERY)],
    )


def _run(snapshot: dict[str, object], config_hash: str) -> PipelineRun:
    """A suspended run pinned at ``config_hash`` — constructed in memory (no session, no DB)."""
    return PipelineRun(
        run_id="run-ac13",
        procedure_id="cold_chain_excursion_disposition",
        agent_id="a",
        status=PipelineRunStatus.WAITING_HUMAN.value,
        started_at=_TS,
        updated_at=_TS,
        governance_snapshot=snapshot,
        governance_hash=config_hash,
    )


# --------------------------------------------------------------------------- #
# AC-13 (a) — a deterministic derivation hash, stable across processes
# --------------------------------------------------------------------------- #


def test_derivation_hash_is_deterministic_and_golden() -> None:
    """The hash is stable within a process AND equals a pinned golden literal — the constants
    are serialised THEMSELVES (never a hand-maintained version string), Decimal->exact str,
    enum->.value, ordered tuple, no clock/set/float, so it reproduces byte-for-byte across
    processes."""
    assert cold_chain_assess.derivation_hash() == cold_chain_assess.derivation_hash()
    assert cold_chain_assess.derivation_hash() == _GOLDEN


def test_supply_chain_snapshot_carries_the_derivation_hash() -> None:
    """The resolved hash rides in the snapshot under ``derivation_hash`` and changes the config
    hash — so a run pinned WITH it and re-checked WITH it matches, but the un-pinned shape does
    not (proving the fold-in is load-bearing, not cosmetic)."""
    h = cold_chain_assess.derivation_hash()
    proc = _proc()
    snap = build_governance_snapshot(proc, derivation_hash=h)

    assert snap["derivation_hash"] == h
    # deterministic: folding the same hash in twice yields the same config hash (the pin invariant)
    assert compute_governance_hash(snap) == compute_governance_hash(
        build_governance_snapshot(proc, derivation_hash=h)
    )
    # load-bearing: the folded-in hash makes the config hash differ from the un-pinned snapshot
    assert compute_governance_hash(snap) != compute_governance_hash(build_governance_snapshot(proc))


# --------------------------------------------------------------------------- #
# AC-13 (b) — a mid-flight derivation edit fails closed at the pin
# --------------------------------------------------------------------------- #


def test_unmutated_derivation_does_not_trip_the_pin() -> None:
    """The control for (b): an unchanged derivation between run-start and resolve is inert — the
    pin only fires on a MISMATCH, never on every gate."""
    proc = _proc()
    h1 = cold_chain_assess.derivation_hash()
    snap, pinned = governance_pin_for(proc, derivation_hash=h1)
    # the same derivation recomputed at resolve (== h1) must NOT raise
    assert_governance_pin(_run(snap, pinned), proc, context="test", derivation_hash=h1)


def test_mutated_dose_ladder_fails_closed_at_the_pin(monkeypatch: pytest.MonkeyPatch) -> None:
    """A mid-flight ``_DOSE_LADDER`` edit (a re-pointed band ceiling) recomputes to a different
    hash at resolve, so the pin refuses — the sanctioned cancel-and-restart path."""
    proc = _proc()
    h1 = cold_chain_assess.derivation_hash()
    snap, pinned = governance_pin_for(proc, derivation_hash=h1)
    run = _run(snap, pinned)

    # re-point the top ladder band's ceiling (0.25/0.50/1.00 -> 0.25/0.50/0.99)
    mutated = cold_chain_assess._DOSE_LADDER[:-1] + ((Decimal("0.99"), ExcursionSeverity.MAJOR),)
    monkeypatch.setattr(cold_chain_assess, "_DOSE_LADDER", mutated)
    h2 = cold_chain_assess.derivation_hash()
    assert h2 != h1

    with pytest.raises(ProcedureError, match="governance-config pin mismatch"):
        assert_governance_pin(run, proc, context="gate resolution", derivation_hash=h2)


def test_mutated_top_severity_fails_closed_at_the_pin(monkeypatch: pytest.MonkeyPatch) -> None:
    """The drafter finding, PROVEN: the SEPARATE ``_TOP_SEVERITY`` top-band constant is hashed
    too. A ladder-tuple-only hash would NOT change when only the unbounded critical band is
    re-pointed, and this run would silently resolve under a changed disposition — here it fails
    closed."""
    proc = _proc()
    h1 = cold_chain_assess.derivation_hash()
    snap, pinned = governance_pin_for(proc, derivation_hash=h1)
    run = _run(snap, pinned)

    # the top band no longer means CRITICAL — a real weakening of the disposition ladder
    monkeypatch.setattr(cold_chain_assess, "_TOP_SEVERITY", ExcursionSeverity.MAJOR)
    h2 = cold_chain_assess.derivation_hash()
    assert h2 != h1

    with pytest.raises(ProcedureError, match="governance-config pin mismatch"):
        assert_governance_pin(run, proc, context="gate resolution", derivation_hash=h2)


# --------------------------------------------------------------------------- #
# AC-13 (c) — no cross-vertical bleed
# --------------------------------------------------------------------------- #


def test_no_derivation_hash_is_byte_identical() -> None:
    """The mechanism guaranteeing (c): with no derivation hash supplied (the default, every
    vertical that pins none), NO key is added — so ``None`` reproduces the pre-AC-13 snapshot
    exactly."""
    proc = _proc()
    assert "derivation_hash" not in build_governance_snapshot(proc)
    assert build_governance_snapshot(proc) == build_governance_snapshot(proc, derivation_hash=None)


def test_other_verticals_snapshots_unchanged() -> None:
    """(c) against the REAL shipped specs: procurement / energy / aquaculture carry NO
    derivation hash (their caller resolves ``None``), so every one of their procedure snapshots
    is byte-identical to before — no cross-vertical bleed from the supply_chain fold-in."""
    for vertical in ("procurement", "energy", "aquaculture"):
        spec = load_procedures_file(
            Path(f"verticals/{vertical}/procedures.yaml"), vertical=vertical
        )
        for procedure in spec.procedures:
            snap = build_governance_snapshot(procedure)  # None default = the pre-AC-13 shape
            assert "derivation_hash" not in snap, f"{vertical}/{procedure.procedure_id} bled a hash"


# --------------------------------------------------------------------------- #
# AC-13 (d) — the self-cancelling F-PIN-residual marker
# --------------------------------------------------------------------------- #


async def test_fpin_residual_procurement_unpinned_marker() -> None:
    """SELF-CANCELLING F-PIN marker (PLAN-0075 AC-13(d) / SD-5). supply_chain pins its severity
    derivation into the run snapshot; procurement does NOT (its imperative ฿ derivation —
    ``unit_price`` times ``qty`` — has no clean datum to hash). This asserts BOTH, so it FAILS the
    moment a procurement derivation hash lands — forcing the F-PIN follow-on tracking to be closed
    and this marker updated. The failing assertion is the deferral self-cancelling, not a bug."""
    discover_and_register()
    await register_supply_chain_procedure_executors()
    await register_procurement_procedure_executors()

    assert (
        registry.derivation_hash("supply_chain") is not None
    ), "supply_chain must pin its severity-derivation constants into the run snapshot (AC-13)"
    assert registry.derivation_hash("procurement") is None, (
        "F-PIN RESIDUAL SELF-CANCELLED: a procurement derivation hash now registers. The SD-5 "
        "deferral rested on procurement's imperative ฿ derivation having no clean datum to hash; "
        "if one has landed (the follow-on's proper form is 'declare the derivation as data' — see "
        "PLAN-0075 SD-5 / Out of Scope), close the F-PIN follow-on tracking and update this "
        "marker. This failure is the deferral self-cancelling, not a test bug."
    )


# --------------------------------------------------------------------------- #
# The registry vertical hook (the inversion-of-control seam) behaves
# --------------------------------------------------------------------------- #


def test_registry_derivation_hash_hook() -> None:
    """The engine pulls a vertical's derivation hash by name (``None`` when unregistered), and a
    duplicate registration is a ``RegistryError`` — the same posture as the other registrars."""
    assert registry.derivation_hash("nonesuch") is None
    registry.register_derivation_hash("v", lambda: "abc123")
    assert registry.derivation_hash("v") == "abc123"
    with pytest.raises(RegistryError, match="already registered"):
        registry.register_derivation_hash("v", lambda: "def456")
