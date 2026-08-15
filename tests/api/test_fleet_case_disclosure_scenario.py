"""PLAN-0106 Step 3 — the fleet case-persistence disclosure, end to end (AC-4, AC-5).

CLAUDE.md §8 scenario test. It drives the **real producer into the real consumer**:
the real FastAPI app, configured from the values **parsed out of the committed
`published.env` files** — not retyped constants — through the real index rewrite
and the real static mount, to the bytes a visitor's browser would actually
receive.

⚠️ **Why the config is parsed rather than typed.** A test that hardcoded
`UI_PUBLISHED_VIEWS="A,C,F,H,I,J"` would agree with itself forever: it would stay
green the day someone edits fleet's committed profile and removes Tab I, which is
precisely the change that would make the disclosure render on a system with no
case dataset — or stop rendering on the one that has it. Parsing the committed
file makes the profile itself part of the system under test.

**What this test can and cannot prove.** The disclosure is client-rendered and
this repo has no JS runtime in CI, so this asserts the served **bytes** and the
**gate condition the server declares** — the established D6 / PLAN-0103 AC-8 bar.
That the browser paints it is the one-time visual check in the PR (Step 4).
Stated plainly because the gap is the point: the assertions below are about the
contract between the server's declared state and the asset's gate, which is
exactly the seam that broke silently in PLAN-0103's earlier tabs.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx import AsyncClient

from services.api.config import settings

_PROFILES = Path("deploy/published")

#: The system under test. ONE label is a reference; a second would make this file
#: a registry, which `test_ac5_no_file_outside_a_profile_lists_two_system_labels`
#: fails the build over (ADR-0036 D2 puts the cross-system map in the portal repo).
#: So the counter-example below is DISCOVERED, never named.
_FLEET = "oct-fleet-maintenance"


def _a_published_system_without_the_case_surface() -> str:
    """A real published profile that does NOT publish Tab I — found, not named.

    🔴 Two reasons this is discovery rather than a constant, and the second is the
    one that bit:

    1. It stays correct when a fourth system arrives. A named counter-example
       silently stops testing anything the day that system starts publishing Tab I.
    2. Naming it would put a **second** system label in this file, which is exactly
       the shadow-ingress-map shape ADR-0036 D2 forbids. Measured s232: the first
       draft of this module named both and reddened the AC-5 guard **in CI but not
       locally** — that guard scans COMMITTED files, and an untracked new file is
       invisible to it, so a pre-commit run cannot see its own violation.
    """
    for profile in sorted(p for p in _PROFILES.iterdir() if p.is_dir()):
        if not (profile / "published.env").exists():
            continue
        env = _committed_env(profile.name)
        if env.get("UI_PROFILE") != "published":
            continue
        if "I" not in env["UI_PUBLISHED_VIEWS"].split(","):
            return profile.name
    raise AssertionError(
        "no published profile lacks Tab I — the absence half of AC-4 has no "
        "real system to assert against and would be vacuous"
    )


def _committed_env(system: str) -> dict[str, str]:
    """The system's COMMITTED `published.env`, comments and blanks discarded.

    Deliberately mirrors `tests/deploy/test_published_profiles.py::_read_env_file`
    rather than importing it — this module must not break when that one is
    refactored, and the parse is four lines. A commented-out assignment must not
    register, and must not hide a real one either.
    """
    out: dict[str, str] = {}
    path = _PROFILES / system / "published.env"
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if sep:
            out[key.strip()] = value.strip()
    assert out, f"{path} parsed to nothing — the scenario would be vacuous"
    return out


def _apply(monkeypatch: pytest.MonkeyPatch, env: dict[str, str]) -> None:
    """Configure the running app exactly as that profile's compose would."""
    monkeypatch.setattr(settings, "ui_profile", env["UI_PROFILE"])
    monkeypatch.setattr(settings, "oct_vertical", env["OCT_VERTICAL"])
    monkeypatch.setattr(settings, "ui_published_views", env["UI_PUBLISHED_VIEWS"])


async def test_the_committed_fleet_profile_still_publishes_the_case_surface() -> None:
    """Precondition, asserted rather than assumed — everything below rests on it.

    If fleet ever stops publishing Tab I, the disclosure SHOULD stop rendering and
    the presence assertions below would be wrong to keep passing. Failing here
    names that cause directly instead of leaving a downstream assertion to fail
    for a reason nobody can read.
    """
    fleet = _committed_env(_FLEET)
    assert "I" in fleet["UI_PUBLISHED_VIEWS"].split(","), (
        "fleet's committed profile no longer publishes Tab I — the case-persistence "
        "disclosure has nothing to disclose, and this whole module needs revisiting"
    )
    # Raises with its own message if no such system exists — the absence half of
    # AC-4 would then be asserting against nothing.
    _a_published_system_without_the_case_surface()


async def test_fleet_serves_a_document_whose_declared_state_turns_the_gate_on(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-5 presence: real config → real rewrite → the served document declares Tab I."""
    _apply(monkeypatch, _committed_env(_FLEET))

    meta = await client.get("/meta")
    assert meta.status_code == 200
    assert meta.json()["ui_profile"] == "published"

    index = await client.get("/")
    assert index.status_code == 200
    html = index.text

    assert '<meta name="ui-profile" content="published"' in html, (
        "the served index still declares the dev profile — the boot injection did "
        "not apply, and every client-side gate would read the wrong state"
    )
    declared = _declared_views(html)
    assert "I" in declared, (
        f"the served document declares views {declared} — without I the persistent "
        "line's gate is false and fleet would publish a case surface with no disclosure"
    )


async def test_the_served_assets_carry_the_disclosure_gated_on_that_state(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-5 — the consumer half: the bytes actually served, not the files on disk.

    Reads the assets back through the app's own static mount, so a mount
    misconfiguration or a CSP-layer rewrite would show up here rather than in a
    file-system read that bypasses the server entirely.
    """
    _apply(monkeypatch, _committed_env(_FLEET))

    case_js = await client.get("/assets/view-case.js")
    assert case_js.status_code == 200
    assert (
        "ผู้เข้าชมทุกคนของระบบนี้อ่านได้" in case_js.text
    ), "the served view-case.js does not carry the reader-set disclosure"
    assert "ถูกลบภายใน 90 วัน" in case_js.text
    assert (
        "ข้อมูลสาธิตเป็นข้อมูลสังเคราะห์" in case_js.text
    ), "the point-of-capture synthetic restatement is missing (SD-1 sub-question 1)"
    assert "O.isPublished()" in case_js.text

    app_js = await client.get("/assets/app.js")
    assert app_js.status_code == 200
    assert "case-persist-notice" in app_js.text
    assert "ผู้เข้าชมทุกคนของระบบนี้อ่านข้อความนั้นได้" in app_js.text

    # 🔴 The gate, not just the text. The asset is static, so its bytes are
    # identical on every system — what differs is the state the server declares.
    # Asserting the gate reads the DECLARED view set is what makes the absence
    # direction below meaningful rather than a claim about a different file.
    assert "hasOwnProperty.call(VIEWS, 'I')" in app_js.text, (
        "the persistent line is no longer gated on Tab I being declared — it would "
        "render on any published system, including the DB-less ones where it is false"
    )


async def test_a_published_system_without_the_case_surface_turns_the_gate_off(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-4 absence — driven by a REAL published system, discovered from the profiles.

    The counter-example is a live, published, DB-less system. Telling its visitors
    their case text is stored for 90 days would be false, and the failure would be
    invisible: a plausible sentence on a system that has no such dataset.

    Which system it is comes from the filesystem, not from a constant here — see
    `_a_published_system_without_the_case_surface` for the two reasons.
    """
    system = _a_published_system_without_the_case_surface()
    _apply(monkeypatch, _committed_env(system))

    index = await client.get("/")
    assert index.status_code == 200
    assert '<meta name="ui-profile" content="published"' in index.text

    declared = _declared_views(index.text)
    assert declared, "a published system declared no views at all"
    assert "I" not in declared, (
        f"{system} declares views {declared}, which includes I — the case-persistence "
        "disclosure's gate would turn ON for a system with no case dataset"
    )


async def test_the_dev_console_never_declares_the_published_profile(
    client: AsyncClient,
) -> None:
    """AC-4 absence, the other direction: the dev fast path rewrites nothing.

    Uses the fixture's own default rather than setting anything, because the claim
    under test is precisely what an UNCONFIGURED app serves.
    """
    index = await client.get("/")
    assert index.status_code == 200
    assert '<meta name="ui-profile" content="dev"' in index.text, (
        "the dev console is serving a non-dev profile tag — both disclosure gates "
        "read that tag, so they would fire on a console where every claim is false"
    )
    assert '<meta name="ui-views"' not in index.text, (
        "the dev page carries a view-set tag — it renders the full census and the "
        "tag's presence would make the persistent line's gate reachable"
    )


def _declared_views(html: str) -> list[str]:
    """The view keys the served document actually declares, parsed from the tag."""
    marker = '<meta name="ui-views" content="'
    if marker not in html:
        return []
    start = html.index(marker) + len(marker)
    return [k for k in html[start : html.index('"', start)].split(",") if k]
