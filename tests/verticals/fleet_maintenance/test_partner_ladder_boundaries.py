"""PLAN-0096 Step 1 / AC-1 — the fleet governance numbers are the DESIGN PARTNER's,
and the boundary semantics are PROVED rather than restated.

Until this step the ladder and the per-truck repair ceiling carried the PLAN-0086
*synthetic* customer's answers (a dirtied narrative persona: ฿5,000 / ฿50,000 rungs,
a ฿5,000 ceiling). A real design partner has since answered an 18-question discovery
round (2026-07-28), and three of those answers land directly on the authored numbers:

* **Q9** — "≤5,000 ต้อม / 5,001-30,000 วิรัช / >30,000 owner". The partner states his
  ladder with INCLUSIVE ceilings; the engine's :class:`DoaLadder` bands are half-open
  ``[min, next)`` with INCLUSIVE floors (``doa_tier.resolve_doa_tier`` takes the
  rightmost tier whose ``min_amount <= amount``). The two phrasings meet at floors
  ``"0"`` / ``"5001"`` / ``"30001"`` — which is why the encoded rungs are the partner's
  numbers PLUS ONE, and why that off-by-one is a TRANSLATION, not a typo. This module
  is the artifact that keeps a later reader from "tidying" it back.
* **Q8** — "ต้อม ~5,000; some tractor heads stretch a bit". ``minor_repair_ceiling_thb``
  is already per-truck (ADR-016 FKP), so the stretch needs no engine change: the
  DEFAULT becomes 5001 (breach ⇔ quote > ฿5,000 — the same inclusive-ceiling
  translation) and the real per-truck stretch values are a named partner intake
  question, not a value this repo may invent.
* **Q10** — the three-quote threshold is >30,000, not the synthetic ฿20,000. The feed
  that COMPUTES that signal lands in PLAN-0096 Step 4; Step 1 only corrects the
  provenance so no reader is told ฿20,000 came from this partner.

**The counterexample (the PLAN's own, and it is the reason this module exists).**
Floors ``"5000"`` / ``"30000"`` would pull a ฿5,000 quote into a governed run at all
and route a ฿30,000 quote to the OWNER — one tier too high in both cases. Both rows
below go RED under that mutation, so this test cannot pass by merely echoing the YAML.

Offline + deterministic (CLAUDE.md §8): the shipped YAML, the shipped synthetic
fixture, and the REAL ``resolve_doa_tier`` / ``classify_verdict`` — no mocks, no DB,
no MS-S1 call.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from services.engine.procedures.doa_tier import resolve_doa_tier
from services.engine.procedures.spec import (
    DoaLadder,
    Procedure,
    VerticalProcedures,
    load_procedures,
)
from services.engine.procedures.verdict import Verdict, classify_verdict
from verticals.fleet_maintenance.data_adapter.synthetic import truck_records

_VERTICAL = "fleet_maintenance"
_PROCEDURE_ID = "governed_repair_approval"
_YAML_PATH = Path("verticals/fleet_maintenance/procedures.yaml")
_ONTOLOGY_PATH = Path("verticals/fleet_maintenance/ontology/fleet_maintenance_v0.yaml")

# Q8: the partner's ungoverned floor is "up to about 5,000" — INCLUSIVE. The engine
# breaches at/above the ceiling (`direction: above` -> `measured >= threshold`), so the
# authored ceiling is his number PLUS ONE.
_CEILING_DEFAULT = 5001.0


def _spec() -> VerticalProcedures:
    return load_procedures(_VERTICAL)


def _hero(spec: VerticalProcedures) -> Procedure:
    return next(p for p in spec.procedures if p.procedure_id == _PROCEDURE_ID)


def _ladder(spec: VerticalProcedures) -> DoaLadder:
    ladder = next(s.governance_content for s in _hero(spec).steps if s.step_id == "approve")
    assert isinstance(ladder, DoaLadder)
    return ladder


# --------------------------------------------------------------------------- #
# AC-1 (a) — the per-truck ceiling default IS the partner's answer
# --------------------------------------------------------------------------- #


def test_every_shipped_truck_carries_the_partner_ceiling_default() -> None:
    """Q8: ต้อม settles up to ~฿5,000, so the authored default ceiling is 5001 on every
    truck. Asserted over the SHIPPED fixture rather than a literal in one place, because
    the per-truck stretch values are the partner intake question — the day a real stretch
    value arrives for one tractor head, this test is the thing that forces a deliberate
    edit here rather than a silent divergence between trucks."""
    ceilings = {t["truck_id"]: t["minor_repair_ceiling_thb"] for t in truck_records()}
    assert ceilings, "the synthetic fleet must not be empty"
    assert set(ceilings.values()) == {_CEILING_DEFAULT}


# --------------------------------------------------------------------------- #
# AC-1 (b) — the four boundary cases (the oracle)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("quote", "governed", "required_role", "approver_id"),
    [
        # ≤5,000 is ต้อม's own call — it never becomes a governed run at all.
        pytest.param(Decimal("5000"), False, None, None, id="5000-stays-ungoverned"),
        # 5,001-30,000 is วิรัช's band, at BOTH ends.
        pytest.param(
            Decimal("5001"), True, "ผจก.เดินรถ", "appr-fleet-manager-wirat", id="5001-wirat-floor"
        ),
        pytest.param(
            Decimal("30000"),
            True,
            "ผจก.เดินรถ",
            "appr-fleet-manager-wirat",
            id="30000-wirat-ceiling",
        ),
        # >30,000 is the owner's.
        pytest.param(Decimal("30001"), True, "เจ้าของกิจการ", "appr-owner", id="30001-owner-floor"),
    ],
)
def test_partner_ladder_boundary_semantics(
    quote: Decimal,
    governed: bool,
    required_role: str | None,
    approver_id: str | None,
) -> None:
    """AC-1's oracle, both halves of the journey a ฿ figure actually takes.

    Half one is the CEILING (the ``judge`` step's per-truck band): does this quote enter
    a governed run at all? Half two is the LADDER (the ``approve`` step's doa_tier): once
    governed, whose desk does it land on? A boundary bug in either half is a real-money
    routing error, and the two halves fail differently — ฿5,000 wrongly governed is
    ceremony where the partner wants none; ฿30,000 wrongly escalated is the owner's phone
    ringing for a repair he delegated away.

    Both halves run the REAL engine functions over the REAL shipped ladder."""
    breached = classify_verdict(float(quote), _CEILING_DEFAULT, "above") is Verdict.BREACH
    assert breached is governed

    if not governed:
        # There is no tier to resolve: an ungoverned repair never reaches the gate.
        return

    spec = _spec()
    verdict = resolve_doa_tier(
        _ladder(spec),
        amount=quote,
        currency="THB",
        principals=list(spec.principals),
        sod_required=True,
    )
    assert verdict.required_role == required_role
    assert verdict.resolved_approver_id == approver_id


def test_the_bands_are_contiguous_and_meet_the_partner_phrasing() -> None:
    """The translation itself, asserted as a property rather than a table: วิรัช's band is
    exactly ``[5001, 30001)`` and the owner's is ``[30001, ∞)``. Half-open + contiguous is
    what makes "≤5,000 / 5,001-30,000 / >30,000" total-cover with no gap and no overlap —
    the property a hand-edited floor silently breaks."""
    spec = _spec()
    mid = resolve_doa_tier(
        _ladder(spec),
        amount=Decimal("15000"),
        currency="THB",
        principals=list(spec.principals),
        sod_required=True,
    )
    top = resolve_doa_tier(
        _ladder(spec),
        amount=Decimal("48000"),
        currency="THB",
        principals=list(spec.principals),
        sod_required=True,
    )
    assert (mid.band.min, mid.band.max) == (Decimal("5001"), Decimal("30001"))
    assert (top.band.min, top.band.max) == (Decimal("30001"), None)


# --------------------------------------------------------------------------- #
# AC-1 (c) — the GUESS stamps the partner's answers retired
# --------------------------------------------------------------------------- #


def test_the_repair_ceiling_property_no_longer_carries_a_guess_stamp() -> None:
    """``minor_repair_ceiling_thb`` was marked ``GUESS — รอแก้`` because its value came
    from a simulated customer. Q8 answered it for real, so the stamp must go — that marker
    is the partner's own "correct me" surface (ADR-0032 D1) and leaving it on a confirmed
    number teaches the partner to ignore it everywhere else.

    Asserted against the parsed property description, not the whole file: the file still
    legitimately carries GUESS stamps for the last-service odometers (PLAN-0096 Step 9),
    and a whole-file check would be answering a different question."""
    with _ONTOLOGY_PATH.open(encoding="utf-8") as stream:
        ontology = dict(YAML().load(stream))
    description = ontology["object_types"]["Truck"]["properties"]["minor_repair_ceiling_thb"][
        "description"
    ]
    assert "GUESS" not in description
    assert "Q8" in description, "the confirmed value must cite the answer that confirmed it"


def test_every_surviving_guess_marker_belongs_to_a_named_later_step() -> None:
    """The set-equality tripwire, and it has already earned its keep.

    Step 1 left TWO stamps standing, each owned by a later PLAN-0096 step: the ``reshape``
    fail-open ``compliance.three_quote`` default (Step 4) and the per-truck PM due points
    (Step 9). When Step 4 landed and deleted the first one, THIS TEST FAILED — which is
    exactly what it was written to do. The anti-rot signal is a failing test, not a comment
    nobody reads, and the update below is the deliberate act it forced.

    **Step 9 landed, and this test failed for the second time — as designed.** The last
    surviving stamp was the per-truck PM due points, and AC-10 replaced it with a real load
    path: the paper PM folder + the Wialon CSV export, imported and human-confirmed
    (``pm_import.py`` -> ``pm_projection.py``). So the assertion is now ``== 0``, which the
    previous revision of this docstring named in advance as the exact next move. Both of this
    file's guess stamps are gone, each retired by the step that owned it — `superseded by new
    info`, not an error in either direction.

    An empty set is the strongest state this tripwire can be in, and also the easiest to
    weaken by accident, so the two named assertions BELOW outlive it: a re-added stamp for
    either retired concern fails here even though the count assertion alone would have caught
    it, because a future step that legitimately adds a NEW stamp would move the count and could
    otherwise quietly restore an old one in the same edit.

    The match is the BARE token, deliberately. A cleverer matcher that exempted "explanatory
    mentions" would be exactly the loophole a stamp could later hide in, so the rule for this file
    is simply: prose about the convention writes `รอแก้`, and the uppercase token means an actual
    unresolved value. (Both of this module's own stamps-are-gone assertions were caught by that
    rule when first written — the check works.)"""
    guess_lines = [
        line for line in _YAML_PATH.read_text(encoding="utf-8").splitlines() if "GUESS" in line
    ]
    assert len(guess_lines) == 0, guess_lines
    # Step 9's stamp is gone WITH a real load path behind the value, and Step 4's is gone WITH
    # its fail-open default. Named individually so that a later step which adds its OWN stamp
    # (moving the count) cannot restore either of these in the same edit and still pass.
    assert not any("per-truck due points" in line for line in guess_lines), guess_lines
    assert not any("sourcing-hygiene signal map" in line for line in guess_lines), guess_lines
