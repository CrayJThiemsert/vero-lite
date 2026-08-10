"""PLAN-0103 Step 3 — the newly-reachable published surfaces, audited per system.

Step 2 made the published tab set per-system. This module covers what that exposes:
view code written under PLAN-0100, when exactly ONE system (energy) was published, some
of which has never run on a published profile before.

⚠️ **Step 3's own text names the wrong targets, and the corrected scope is what is
tested here.** It says to audit "Tab G's published branch" plus "the
monitor/procedures/flow published behaviours [that] were unreachable because H was
filtered". Checked against the source: ``view-flow.js`` is Tab **D**, which energy has
published all along, so its branch was never unreachable; and ``view-monitor.js``
contains no ``isPublished()`` at all, so it has no published behaviour to audit. This is
the same shape as Step 2's census, which also disagreed with the PLAN's snapshot.

The real audit, from the ruled tab sets (SD-3: energy ``A,B,C,D,F`` · procurement
``G,F`` · fleet ``A,C,F,H,I,J``):

===================  ====  ============  ==========================================
module               tab   new on        published-profile branch?
===================  ====  ============  ==========================================
``view-hero.js``     G     procurement   YES — ``:606``, dead code today because
                                         energy edge-excludes G. Goes live here.
``view-monitor.js``  H     fleet         none
``view-case.js``     I     fleet         none
``view-export.js``   J     fleet         none
===================  ====  ============  ==========================================

"No branch" is the CORRECT state for H/I/J rather than a gap: PLAN-0100 excluded them
because their backends were off the allowlist (DB-backed / default-deny), and fleet has
a Postgres, so Step 5 puts those routes back on fleet's own allowlist. What must hold is
that publishing them adds no UNGUARDED excluded-backend call — asserted below, so it
reddens if a future edit adds one.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx import AsyncClient

from services.api.config import settings
from tests.api.js_source import strip_js_comments

_ASSETS = Path("services/api/static/assets")

#: The excluded-backend wrappers, mirroring ``test_ui_profile.py``'s guard registry.
#: Duplicated deliberately rather than imported: that registry answers "is every call
#: guarded somewhere", this asks "does a module fleet is about to publish call one at
#: all". Importing it would couple two guards that must be able to fail independently.
_EXCLUDED_WRAPPERS = (
    "O.Llm.warm",
    "O.Llm.sleep",
    "O.Intake.defaults",
    "O.Intake.extract",
    "O.Intake.generate",
    "O.Draft.classify",
    "O.Draft.build",
    "O.Draft.instantiate",
    "O.Hero.event",
    "O.API.execute",
)

#: Modules fleet publishes for the first time (tabs H, I, J).
_FLEET_NEWLY_PUBLISHED = ("view-monitor.js", "view-case.js", "view-export.js")


# --------------------------------------------------------------------------- #
# The hero fallback, CLOSED (Step 3's optional item — taken, Cray typed s219)
# --------------------------------------------------------------------------- #


async def test_a_vertical_with_no_hero_of_its_own_gets_a_404(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Energy ships no hero package, and must not be served procurement's.

    This is the defect the fallback made *structural*: a hero is bespoke per design
    partner (ADR-0032 D1.2), so falling back served a Fastenal procurement hero under an
    energy banner. PLAN-0100 could only work around it at the EDGE, by edge-excluding
    Tab G from the published energy system — a workaround every future heroless vertical
    would have had to remember. The route knows; the allowlist had to be told.
    """
    monkeypatch.setattr(settings, "oct_vertical", "energy")
    for route in ("/demo/hero/governance", "/demo/hero/impact"):
        response = await client.get(route)
        assert response.status_code == 404, f"{route} served a hero to a heroless vertical"
        assert "ships no governed hero" in response.json()["detail"]


async def test_procurement_gets_its_own_hero_not_a_borrowed_one(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The other half of the same property — closing the fallback broke nothing real.

    Asserted on a value only procurement's builders produce, not on a 200: a 200 alone
    would also be returned by any fallback that happened to still be wired.
    """
    monkeypatch.setattr(settings, "oct_vertical", "procurement")
    body = (await client.get("/demo/hero/impact")).json()
    assert body["asset_id"] == "AST-CNC-014"


async def test_fleet_gets_fleets_hero_not_procurements(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fleet ships its own hero, and the two payloads are disjoint by construction.

    ``FleetHeroImpact`` requires a ``vertical`` discriminant that ``HeroImpactLedger``
    forbids, so this assertion cannot pass on a borrowed procurement payload.
    """
    monkeypatch.setattr(settings, "oct_vertical", "fleet_maintenance")
    body = (await client.get("/demo/hero/impact")).json()
    assert body.get("vertical") == "fleet_maintenance"
    assert "asset_id" not in body


# --------------------------------------------------------------------------- #
# Tab G's published branch — dead code today, live on procurement
# --------------------------------------------------------------------------- #


def test_tab_g_published_branch_gates_both_toggles() -> None:
    """``view-hero.js``'s published branch must hide BOTH toggles, not just one.

    The branch has never run on a published profile: energy edge-excludes G, so under
    today's only published system this code is unreachable. It goes live on procurement,
    whose allowlist carries the two hero READS and not ``POST /demo/hero/event``.

    Both toggles matter and they were added at different times — the event toggle with
    PLAN-0100 Step 3, the live toggle in s207 after an adversarial review, because
    ``?live=true`` drives a full procedure run that raises on a non-suspending gate (an
    unhandled 500 in front of a design partner) and is an anonymous uncapped MS-S1 call.
    A published branch that hid only the first would look correct and still expose the
    worse of the two.
    """
    source = strip_js_comments((_ASSETS / "view-hero.js").read_text(encoding="utf-8"))
    assert "const published = O.isPublished();" in source
    assert "if (!published) {" in source, "the event-opener toggle is not gated on the profile"
    assert "if (mode !== 'event' && !published) {" in source, (
        "the live-run toggle is not gated on the profile — ?live=true is an anonymous, "
        "uncapped MS-S1 call that 500s when the gate does not suspend"
    )


def test_the_event_wrapper_is_called_only_behind_that_branch() -> None:
    """``O.Hero.event`` is the one excluded-backend call Tab G carries."""
    source = strip_js_comments((_ASSETS / "view-hero.js").read_text(encoding="utf-8"))
    assert source.count("O.Hero.event(") == 1
    assert "O.isPublished()" in source


# --------------------------------------------------------------------------- #
# Fleet's three newly-published modules — no branch, and none owed
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("module", _FLEET_NEWLY_PUBLISHED)
def test_fleet_newly_published_modules_call_no_excluded_backend(module: str) -> None:
    """Publishing H/I/J on fleet must add no unguarded excluded-backend call.

    These modules carry no ``isPublished()`` guard, which is correct — their routes are
    on fleet's own allowlist because fleet has a Postgres. That correctness rests
    entirely on them calling nothing that is excluded, which is a property of today's
    source and not a guarantee. This is the tripwire: add such a call to Tab H, I or J
    and it reddens here rather than 404ing in front of a visitor.
    """
    source = strip_js_comments((_ASSETS / module).read_text(encoding="utf-8"))
    called = [wrapper for wrapper in _EXCLUDED_WRAPPERS if wrapper + "(" in source]
    assert not called, (
        f"{module} is published on fleet (tabs H/I/J) and calls excluded backends "
        f"{called} — either guard the call with O.isPublished() and register it in "
        "test_ui_profile.py's _GUARD_REGISTRY, or put the route on fleet's allowlist"
    )


# --------------------------------------------------------------------------- #
# The ruled tab sets, exercised through the Step 2 mechanism
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("vertical", "declared", "default_tab"),
    [
        ("energy", "A,B,C,D,F", "A"),
        ("procurement", "G,F", "G"),
        ("fleet_maintenance", "A,C,F,H,I,J", "A"),
    ],
)
async def test_each_ruled_tab_set_reaches_the_browser_with_its_landing_tab(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    vertical: str,
    declared: str,
    default_tab: str,
) -> None:
    """SD-3's three ruled sets survive the Step 2 carriage end to end.

    The sets are passed IN rather than read from a committed file on purpose: the
    per-system profiles are Step 4's, so no artifact holds them yet, and a test that
    pinned them here would be asserting against its own constant. What is under test is
    the mechanism — that a declared set arrives intact on both carriers and that the
    FIRST key becomes the landing tab.

    Procurement is the case that motivated ordering at all: its Tab A is structurally
    blank (its adapter's ``stream_events`` is an empty iterator by design), so landing
    there would open the public demo on an empty screen.
    """
    monkeypatch.setattr(settings, "oct_vertical", vertical)
    monkeypatch.setattr(settings, "ui_profile", "published")
    monkeypatch.setattr(settings, "ui_published_views", declared)

    index = (await client.get("/")).text
    assert f'<meta name="ui-views" content="{declared}" />' in index

    meta = (await client.get("/meta")).json()
    assert meta["ui_published_views"] == declared.split(",")
    assert meta["ui_published_views"][0] == default_tab
