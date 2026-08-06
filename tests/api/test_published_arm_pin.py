"""PLAN-0100 OI-1 — the published-profile arm pin.

Cray's typed ruling, 2026-08-06: **option (b), in PRINCIPLE form** — on the
published profile an LLM call the visitor did not ask for is not made; any route
whose LLM invocation is involuntary runs the deterministic arm instead. The ฿
facet (ADR-0030) is deterministic and rides the pinned path (same ruling).

What these tests are built to catch, and how they stay non-vacuous:

* The absence assertion is made by **RECORDING**, never by raising. ``recommend()``
  wraps everything in a blanket ``except`` (ADR-010 IN-4), so a builder that
  raised would be swallowed and the fail-safe would produce a record that looks
  almost exactly like the pinned one — the test would pass for the wrong reason.
  The recorder therefore wraps whatever ``_build_chat_client`` the autouse
  ``_offline_llm`` fixture installed and appends to a list.
* Only the **upstream dependency** (Ollama) is stood in for — never the route,
  the recommender, or the pin. ``test_the_route_makes_no_llm_client_...`` drives
  the real ``GET /recommendations`` into the real ``_populate_store`` over the
  real energy adapter's synthetic events (CLAUDE.md §8 scenario rule).
* Every profile assertion is paired with its **dev control**, so a pin that
  never fired could not read as a pass.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from httpx import AsyncClient

from services.api.config import settings
from services.engine import economic_impact, recommender
from services.engine.economic_impact import EconomicImpact
from services.engine.recommender import recommend
from verticals.energy.economic_impact import register_energy_economic_impact

_PIN_STEP_ID = "arm-pin-disclosure"
_DEGRADE_STEP_ID = "llm-degrade-disclosure"


def _record_client_builds(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Wrap the installed offline stub factory so builds are COUNTED, not blocked.

    Returns the list the wrapper appends to. Wrapping (rather than replacing)
    keeps the dev control working end-to-end: the LLM path still gets its
    upstream stand-in, we only learn whether it was reached.
    """
    built: list[str] = []
    installed = recommender._build_chat_client

    def _recording() -> Any:
        built.append("built")
        return installed()

    monkeypatch.setattr(recommender, "_build_chat_client", _recording)
    return built


def _crossing_event() -> dict[str, Any]:
    """An energy reading above the 90 °C escalation threshold."""
    return {
        "event_id": "event-reading-oi1",
        "event_type": "reading",
        "measured_value": 96.5,
        "unit": "celsius",
        "asset_id": "asset-battery-01",
    }


def _steps(record: Any, step_id: str) -> list[Any]:
    return [s for s in record.action.reasoning_trace if s.step_id == step_id]


async def test_the_route_makes_no_llm_client_on_the_published_profile(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SCENARIO — the real involuntary fan-out, end to end, on the published profile.

    Drives ``GET /recommendations`` (the Tab A landing-view call that OI-1 is
    about) into the real recommender over the real energy synthetic events.
    Nothing on either side of the pin is stubbed.
    """
    built = _record_client_builds(monkeypatch)
    monkeypatch.setattr(settings, "ui_profile", "published")

    listing = await client.get("/recommendations")

    assert listing.status_code == 200
    recommendations = listing.json()["recommendations"]
    assert recommendations, "expected at least one recommendation from synthetic data"
    assert built == [], "the published profile must not build an LLM client for this route"
    for rec in recommendations:
        assert rec["confidence"] == recommender.RULE_CONFIDENCE
        assert "LLM assessment" not in rec["title"], "the LLM path must not have run"
        pin = [s for s in rec["reasoning_trace"] if s["step_id"] == _PIN_STEP_ID]
        assert len(pin) == 1, "the pinned record must DISCLOSE that the arm was pinned"
        assert pin[0]["detail"]["recommendation_mode"] == "rule-by-design"
        assert not [s for s in rec["reasoning_trace"] if s["step_id"] == _DEGRADE_STEP_ID]


async def test_the_route_still_builds_the_llm_client_on_the_dev_profile(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DEV CONTROL — proves the recorder above can observe a build at all.

    Without this, ``built == []`` would also hold for a recorder that was never
    wired, and the pin assertion would be vacuous.
    """
    built = _record_client_builds(monkeypatch)
    assert settings.ui_profile == "dev", "the default profile is the control condition"

    listing = await client.get("/recommendations")

    assert listing.status_code == 200
    assert built, "the dev profile must still take the LLM path"
    for rec in listing.json()["recommendations"]:
        assert not [s for s in rec["reasoning_trace"] if s["step_id"] == _PIN_STEP_ID]


async def test_a_visitor_initiated_call_is_not_pinned(monkeypatch: pytest.MonkeyPatch) -> None:
    """The discriminator is VOLUNTARINESS, not merely the profile.

    A published-profile call that the visitor did initiate (a future ``/query``-shaped
    caller) must still reach the LLM arm — otherwise the principle would read as
    "published means never any LLM", which is not what was ruled.
    """
    built = _record_client_builds(monkeypatch)
    monkeypatch.setattr(settings, "ui_profile", "published")

    record = await recommend(_crossing_event(), "energy", visitor_initiated=True)

    assert built, "an explicitly visitor-initiated call must not be pinned"
    assert record is not None
    assert _steps(record, _PIN_STEP_ID) == []


async def test_the_pin_disclosure_is_distinguishable_from_the_degrade_disclosure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The two rule-path records must not be confusable.

    ``_rule_recommend`` produces a byte-identical body either way — same two
    ``rule_check`` steps, same ``RULE_CONFIDENCE`` — so "rule because the profile
    pins it" and "rule because the model died" are separable ONLY by the
    disclosure. Asserted by name on both, in both directions.
    """
    monkeypatch.setattr(settings, "ui_profile", "published")
    pinned = await recommend(_crossing_event(), "energy")

    monkeypatch.setattr(settings, "ui_profile", "dev")

    def _boom() -> Any:
        raise RuntimeError("MS-S1 is down")

    monkeypatch.setattr(recommender, "_build_chat_client", _boom)
    degraded = await recommend(_crossing_event(), "energy")

    assert pinned is not None and degraded is not None
    assert len(_steps(pinned, _PIN_STEP_ID)) == 1
    assert _steps(pinned, _DEGRADE_STEP_ID) == []
    assert len(_steps(degraded, _DEGRADE_STEP_ID)) == 1
    assert _steps(degraded, _PIN_STEP_ID) == []

    assert _steps(pinned, _PIN_STEP_ID)[0].detail["recommendation_mode"] == "rule-by-design"
    assert _steps(degraded, _DEGRADE_STEP_ID)[0].detail["recommendation_mode"] == "rule-fail-safe"
    # Both records are engine-authored; actor_kind alone cannot separate them.
    assert pinned.action.audit_metadata.actor_kind == "engine"
    assert degraded.action.audit_metadata.actor_kind == "engine"
    assert "pins the deterministic arm" in (pinned.action.audit_metadata.notes or "")
    assert "attempted and failed" in (degraded.action.audit_metadata.notes or "")


async def test_the_economic_facet_rides_the_pinned_path_and_stays_last(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cray's ruling: keep ฿ under the pin — it is deterministic, not an LLM call.

    Uses the REAL energy producer (the same call discovery makes), so the figure
    asserted is the ratified SD-G arithmetic rather than a fake. The producer
    registry is swapped for a copy first, so registering here cannot leak into
    the AC-9 RED assertion in ``test_economic_impact_wiring``.
    """
    monkeypatch.setattr(economic_impact, "_PRODUCERS", dict(economic_impact._PRODUCERS))
    register_energy_economic_impact()
    built = _record_client_builds(monkeypatch)
    monkeypatch.setattr(settings, "ui_profile", "published")

    record = await recommend(_crossing_event(), "energy")

    assert record is not None
    assert built == [], "the ฿ facet must not smuggle an LLM call onto the pinned path"
    econ = [s for s in record.action.reasoning_trace if s.kind == "economic_impact"]
    assert len(econ) == 1, "the pinned record must still carry the ฿ facet"
    assert record.action.reasoning_trace[-1].kind == "economic_impact", "appended LAST"
    impact = EconomicImpact.model_validate(econ[0].detail)
    assert impact.net_benefit_thb == Decimal("405000")  # SD-G arithmetic
    assert impact.provisional is True
