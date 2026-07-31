"""Offline gate for fleet's View G hero endpoints (PLAN-0098 AC-1/2/3/5).

The offline test is the GATE (CLAUDE.md §8), inherited verbatim from the procurement
donor (``test_demo_hero_routes.py:1-8``): no mutation, no DB, no LLM, no MS-S1. A live
preview is evidence, never the gate. Every test here is DB-free by construction — the two
fleet GETs take no ``Depends(get_session)`` — so none of them can silently no-op into a
green run when Postgres is absent, which is the failure mode a DB-dependent AC would have.

The scenario test (AC-1) drives the REAL chain end to end with no stub anywhere in it:
``FleetMaintenanceSyntheticAdapter`` → the registered ``fleet_maintenance_economic_impact``
producer → ``FleetHeroImpact`` → a plain ASGI client. It pins expected literals rather than
recomputing them from the producer's own constants — a test that recomputes agrees with the
implementation by construction and would survive the constants changing underneath it.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import AsyncIterator
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from services.api.config import settings
from services.api.main import app
from services.api.models.demo import FleetHeroImpact
from services.engine.economic_impact import EconomicExposure, EconomicImpact
from services.engine.procedures.spec import DoaLadder, load_procedures

_REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
async def fleet_client(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncClient]:
    """An ASGI client with the active vertical pinned to fleet_maintenance.

    Patched on the shared ``settings`` object rather than an env var: the router reads
    ``settings.oct_vertical`` at REQUEST time precisely so an override takes effect
    without a re-import, and this fixture is what proves that read is live.
    """
    monkeypatch.setattr(settings, "oct_vertical", "fleet_maintenance")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


def _money(value: object) -> Decimal:
    return Decimal(str(value))


def _spec_ladder() -> DoaLadder:
    """The authored ladder, loaded independently of the code under test."""
    spec = load_procedures("fleet_maintenance")
    procedure = next(p for p in spec.procedures if p.procedure_id == "governed_repair_approval")
    ladder = next(s.governance_content for s in procedure.steps if s.step_id == "approve")
    assert isinstance(ladder, DoaLadder)
    return ladder


def _authored_tier_for(amount: Decimal) -> tuple[Decimal, str]:
    """``(floor, approver_role)`` the AUTHORED spec assigns to ``amount``.

    Derived here from the YAML rather than restated, so this helper cannot drift into
    agreeing with a builder that hardcoded a rung — which is the whole point of AC-2.
    """
    tiers = sorted(_spec_ladder().tiers, key=lambda t: t.min_amount)
    winner = [t for t in tiers if amount >= t.min_amount][-1]
    return winner.min_amount, winner.approver_role


# --------------------------------------------------------------------------- #
# AC-1 — the scenario test: real adapter → real producer → real model → ASGI.
# --------------------------------------------------------------------------- #


async def test_the_fleet_impact_endpoint_returns_the_real_producers_figures(
    fleet_client: AsyncClient,
) -> None:
    """AC-1. Literals pinned, not recomputed from the producer's constants."""
    response = await fleet_client.get("/demo/hero/impact")
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["provisional"] is True
    assert body["vertical"] == "fleet_maintenance"
    assert body["currency"] == "THB"
    assert body["truck_id"] == "truck-01"
    assert body["case_id"] == "case-demo-truck01-axle"
    assert _money(body["quoted_repair_thb"]) == Decimal("48000")

    impact = body["impact"]
    assert impact["kind"] == "overpay_avoided"
    assert impact["provisional"] is True
    assert _money(impact["baseline"]["exposure_thb"]) == Decimal("48000")
    assert _money(impact["governed"]["exposure_thb"]) == Decimal("40800")
    assert _money(impact["net_benefit_thb"]) == Decimal("7200")
    assert impact["assumptions"], "the modelled ฿ arrived with no disclosed assumptions"
    assert impact["basis_refs"], "the modelled ฿ arrived with no provenance refs"


async def test_the_measured_and_modelled_figures_are_separate_fields(
    fleet_client: AsyncClient,
) -> None:
    """PLAN-0098 D-A. The quote is measured; everything derived lives under `impact`.

    A reader must be able to tell the two apart from the payload's SHAPE. If a derived
    figure ever migrates to the top level it stops being qualified by ``assumptions``,
    and the screen most likely to be believed starts presenting a model as a measurement.
    """
    body = (await fleet_client.get("/demo/hero/impact")).json()
    derived = {"net_benefit_thb", "baseline", "governed", "assumptions", "basis_refs"}
    assert not derived & set(
        body
    ), f"derived economic fields leaked to the payload's top level: {sorted(derived & set(body))}"
    assert derived <= set(body["impact"]), "the impact facet lost a field the disclosure needs"


# --------------------------------------------------------------------------- #
# AC-2 — the governance moment, with the parity tripwire against the spec.
# --------------------------------------------------------------------------- #


async def test_the_fleet_governance_moment_tiers_two_repairs_differently(
    fleet_client: AsyncClient,
) -> None:
    """AC-2. ฿48,000 → เจ้าของกิจการ, ฿15,000 → ผจก.เดินรถ, both SoD-governed."""
    response = await fleet_client.get("/demo/hero/governance")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["provisional"] is True
    assert body["source"] == "offline-fixture"

    hero, contrast = body["hero"], body["contrast"]
    assert _money(hero["amount"]["value"]) == Decimal("48000")
    assert hero["doa_tier"][0]["resolved_tier_id"] == "เจ้าของกิจการ"
    assert _money(contrast["amount"]["value"]) == Decimal("15000")
    assert contrast["doa_tier"][0]["resolved_tier_id"] == "ผจก.เดินรถ"

    for side in (hero, contrast):
        sod = side["sod"]
        assert sod["governed"] is True
        assert sod["requester"] is not None and sod["approver"] is not None
        assert sod["requester"]["person_id"] != sod["approver"]["person_id"], (
            "the requester and the approver resolved to the SAME principal — the "
            "partner's own กฎเหล็ก is that whoever files the claim must not approve it"
        )


async def test_the_resolved_bands_match_the_authored_ladder(
    fleet_client: AsyncClient,
) -> None:
    """AC-2's parity tripwire: the response's bands come from the YAML, not from code.

    Deviation from the AC's literal wording, stated rather than hidden: the AC describes
    "set-equality against the authored source", but the response carries two resolved
    bands while the ladder has three rungs, so set equality cannot hold. This is the
    stronger check it was reaching for — for each side, the floor and approver role are
    derived HERE from the loaded spec and must equal what the builder returned. A builder
    that restates a rung goes RED the moment the YAML moves.
    """
    body = (await fleet_client.get("/demo/hero/governance")).json()
    for side_name in ("hero", "contrast"):
        side = body[side_name]
        amount = _money(side["amount"]["value"])
        floor, role = _authored_tier_for(amount)
        audit = side["doa_tier"][0]
        assert _money(audit["band"]["min"]) == floor, (
            f"{side_name}: response band floor {audit['band']['min']} != the authored "
            f"spec's floor {floor} for ฿{amount}"
        )
        assert (
            audit["resolved_tier_id"] == role
        ), f"{side_name}: resolved {audit['resolved_tier_id']!r}, spec says {role!r}"


async def test_the_fleet_moment_carries_the_three_quote_rule_gate(
    fleet_client: AsyncClient,
) -> None:
    """AC-2's fleet-only beat: same signal, two different reasons.

    The hero EARNED its pass by collecting three quotes; the contrast got it free because
    ฿15,000 never crossed the partner's ฿30,000 threshold. A card showing only the boolean
    would render those as the same thing, which is exactly the reading the stamped basis
    exists to prevent.
    """
    body = (await fleet_client.get("/demo/hero/governance")).json()
    hero_gate, contrast_gate = body["hero"]["three_quote"], body["contrast"]["three_quote"]
    assert hero_gate["signal"] is True and contrast_gate["signal"] is True
    assert hero_gate["basis"] == "three_quotes"
    assert contrast_gate["basis"] == "under_threshold"
    assert hero_gate["spec"], "the rule-gate card lost the authored rule text"
    assert hero_gate["blocks_po"] is True


async def test_the_fleet_hero_has_no_live_arm_and_says_so(
    fleet_client: AsyncClient,
) -> None:
    """PLAN-0098 D-C. ``live=true`` is refused, not served under a label it did not earn."""
    response = await fleet_client.get("/demo/hero/governance", params={"live": "true"})
    assert response.status_code == 400, response.text
    assert "no live arm" in response.json()["detail"]


# --------------------------------------------------------------------------- #
# AC-3 — the honesty gate, both directions.
# --------------------------------------------------------------------------- #


def _impact(**overrides: Any) -> EconomicImpact:
    base: dict[str, Any] = {
        "provisional": True,
        "currency": "THB",
        "kind": "overpay_avoided",
        "baseline": EconomicExposure(label="b", exposure_thb=Decimal("48000"), components={}),
        "governed": EconomicExposure(label="g", exposure_thb=Decimal("40800"), components={}),
        "net_benefit_thb": Decimal("7200"),
        "assumptions": ["a disclosed modelling input"],
        "basis_refs": ["event.measured_value"],
    }
    return EconomicImpact(**{**base, **overrides})


def test_a_fleet_payload_cannot_be_built_without_its_assumptions() -> None:
    """AC-3a. Stripping the disclosure is a construction error, not a quieter payload."""
    with pytest.raises(ValidationError, match="assumptions is empty"):
        FleetHeroImpact(
            provisional=True,
            vertical="fleet_maintenance",
            currency="THB",
            truck_id="truck-01",
            case_id="case-demo-truck01-axle",
            quoted_repair_thb=Decimal("48000"),
            impact=_impact(assumptions=[]),
        )


def test_a_fleet_payload_cannot_mix_two_currencies() -> None:
    """The second validator arm — a ledger reading THB beside something else."""
    with pytest.raises(ValidationError, match="currency mismatch"):
        FleetHeroImpact(
            provisional=True,
            vertical="fleet_maintenance",
            currency="THB",
            truck_id="truck-01",
            case_id="case-demo-truck01-axle",
            quoted_repair_thb=Decimal("48000"),
            impact=_impact(currency="USD"),
        )


async def test_an_ungroundable_hero_event_fails_loudly_rather_than_fabricating(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-3b. The producer's None is propagated as an error, never as a zero side.

    Re-pinned to the ฿15,000 contrast event, which sits UNDER the partner's ฿30,000
    comparison threshold — so the real producer genuinely returns ``None`` there. The
    failure is raised rather than rendered: a demo showing a confident ฿0 where the rule
    never applied is worse than one that breaks, because only one of them gets noticed.
    """
    from verticals.fleet_maintenance.hero_demo import impact as impact_module

    monkeypatch.setattr(impact_module, "_HERO_EVENT_ID", "event-reading-05")
    with pytest.raises(ValueError, match="returned None"):
        await impact_module.build_fleet_hero_impact()


# --------------------------------------------------------------------------- #
# AC-5 — the seam is real, not cosmetic.
# --------------------------------------------------------------------------- #


def test_the_demo_router_imports_no_vertical_at_module_scope() -> None:
    """AC-5. Importing the router must not drag a vertical's hero package in with it.

    Run in a SUBPROCESS on purpose: inside the pytest process a dozen other tests have
    already imported half the repo, so ``sys.modules`` there says nothing about what this
    module costs to import. A fresh interpreter is the only honest measurement.

    This is the check that keeps the seam from being cosmetic. Dispatching at request
    time while still importing both heroes at module scope would satisfy every other test
    here and leave the actual cost — and the actual coupling — exactly where it was.
    """
    probe = (
        "import sys\n"
        "import services.api.routers.demo\n"
        "leaked = sorted(m for m in sys.modules if m.startswith('verticals.'))\n"
        "print(repr(leaked))\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        cwd=_REPO_ROOT,
        timeout=120,
    )
    assert proc.returncode == 0, f"the probe itself failed:\n{proc.stderr}"
    leaked = eval(proc.stdout.strip())  # noqa: S307 - a repr(list[str]) this test produced
    assert leaked == [], (
        f"importing services.api.routers.demo pulled in vertical modules: {leaked}\n\n"
        "Every hero import must stay INSIDE its builder. A module-scope import means "
        "booting fleet_maintenance still loads procurement's 802-line hero_demo/run.py, "
        "which is the coupling PLAN-0098's seam exists to remove."
    )
