"""PLAN-0100 Step 2 — the ``ui_profile`` setting and its two delivery seams.

Step 2 ships plumbing, not gating: it makes the profile *knowable*, and nothing
yet renders differently. The gating itself is Step 3, which is BLOCKED-ON-SD-1
and SD-2. So what these tests pin is the contract Step 3 will build on, plus the
two structural properties that make that contract trustworthy:

* the profile reaches the browser **before the first paint** (the injected
  ``<meta>`` tag), because ``app.js`` calls ``buildTabs()`` before ``initMeta()``;
* the profile is **API-visible** (``/meta``), so it is assertable over HTTP and
  readable by a non-browser client.

Two guards here look like paranoia and are not. The anchor guard exists because
the injection is a string substitution: edit that tag in ``index.html`` and the
rewrite stops matching, which would leave a *published* deployment serving a page
marked ``dev`` — a failure with no visible symptom. The inline-script guard exists
because the meta carrier is not a style preference: ``_OCT_CSP`` pins
``script-src 'self'``, so an inline script would be silently blocked and the UI
would fall back to the FULL console. Both failures resolve toward EXPOSURE, which
is why each gets a test rather than a comment.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from services.api.config import ALL_VIEW_KEYS, Settings, settings
from services.api.demo_personas import DemoPersonaError, resolve_demo_personas
from services.api.main import _UI_PROFILE_META_DEV
from tests.api.js_source import strip_js_comments

_STATIC = Path("services/api/static")
_INDEX = _STATIC / "index.html"
_API_JS = _STATIC / "assets/api.js"
_APP_JS = _STATIC / "assets/app.js"

#: AC-9 — the six elements ADR-0035 D6 obliges the persistent notice to carry,
#: each pinned by its own substring. Seven entries, not six: D6's sixth element
#: ("the demo is synthetic — enter no real personal data") is two independent
#: claims, and a reword can drop either one alone.
#:
#: Individually, not as one "is there a banner" check, because the realistic
#: failure is a REWORD that drops one line — most likely the Cloudflare sentence,
#: which reads like vendor detail rather than an obligation. Keyed by the
#: obligation so the assertion message names what went missing, not just that
#: something did.
#:
#: ⚠️ Each substring pins the OBLIGATION, never a token that survives the
#: obligation being dropped (s208 R2). Two originally did not: pinning
#: ``"Cloudflare"`` stayed green through a reword to "Access is gated by
#: Cloudflare." — which deletes *"which processes your email address"*, the
#: actual D6 duty — and ``"real personal data"`` survives the sentence being
#: negated. A tripwire for a reword must pin the words a reword would take.
_D6_NOTICE_ELEMENTS = {
    "what is retained (typed text)": "What you type is retained",
    "for how long (90 days)": "90 days",
    "who reads it (the operator)": "read only by the operator",
    "the gate processes the email via Cloudflare": "Cloudflare, which processes your email address",
    "traffic transits the vendor edge": "vendor edge",
    "the demo is synthetic": "Demo data is synthetic",
    "enter no real personal data": "do not enter real personal data",
}


# --------------------------------------------------------------------------- #
# The /meta contract (AC-1(a) — API-visible), and the dev default (AC-2)
# --------------------------------------------------------------------------- #


async def test_meta_serves_the_dev_profile_by_default(client: AsyncClient) -> None:
    """Unset ``UI_PROFILE`` means today's console — the AC-2 no-change guarantee."""
    response = await client.get("/meta")
    assert response.status_code == 200
    assert response.json()["ui_profile"] == "dev"


async def test_meta_serves_the_configured_profile(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``UI_PROFILE=published`` reaches the API surface (AC-1(a))."""
    monkeypatch.setattr(settings, "ui_profile", "published")
    response = await client.get("/meta")
    assert response.status_code == 200
    assert response.json()["ui_profile"] == "published"


async def test_an_unrecognised_profile_fails_loudly(monkeypatch: pytest.MonkeyPatch) -> None:
    """A typo must stop the process, not fall back.

    This is the asymmetry the ``Literal`` encodes: a fallback would resolve toward
    the FULL console, so a mistyped profile on the PUBLIC box is precisely the
    case that must not start.
    """
    monkeypatch.setenv("UI_PROFILE", "publishd")
    with pytest.raises(ValidationError):
        Settings()


# --------------------------------------------------------------------------- #
# The boot injection (AC-1 — before the first paint)
# --------------------------------------------------------------------------- #


async def test_index_carries_the_dev_profile_untouched(client: AsyncClient) -> None:
    """The dev profile takes the no-rewrite fast path and still declares itself."""
    response = await client.get("/")
    assert response.status_code == 200
    assert _UI_PROFILE_META_DEV in response.text


async def test_index_is_rewritten_for_the_published_profile(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The served document carries ``published`` — and no longer carries ``dev``.

    The second half is the load-bearing one. A rewrite that ADDED a published tag
    while leaving the dev tag in place would leave two conflicting declarations,
    and ``querySelector`` takes the FIRST — so the page would still boot dev.
    """
    monkeypatch.setattr(settings, "ui_profile", "published")
    response = await client.get("/")
    assert response.status_code == 200
    assert '<meta name="ui-profile" content="published" />' in response.text
    assert _UI_PROFILE_META_DEV not in response.text
    assert response.headers["cache-control"] == "no-store"


async def test_the_two_view_set_carriers_agree(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-1: the injected tag and ``/meta`` must never disagree.

    One fact with two carriers is a disagreement waiting to happen, and the two
    are not interchangeable — the tag is what the first paint reads, ``/meta`` is
    what an HTTP client can assert. A drift between them would show as a UI that
    renders one tab set while the API reports another, which is unfalsifiable from
    either side alone.

    Set to a NON-default value on purpose: with the default in place both
    carriers would agree by accident even if one were hardwired.
    """
    monkeypatch.setattr(settings, "ui_profile", "published")
    monkeypatch.setattr(settings, "ui_published_views", "G,F")

    index = (await client.get("/")).text
    tag = re.search(r'<meta name="ui-views" content="([^"]*)" />', index)
    assert tag, "the published index carries no ui-views tag"

    meta = (await client.get("/meta")).json()
    assert tag.group(1).split(",") == meta["ui_published_views"] == ["G", "F"]


async def test_the_dev_index_carries_no_view_set(client: AsyncClient) -> None:
    """The dev profile keeps its no-rewrite fast path, so no tag is emitted.

    Load-bearing rather than incidental: the dev page renders the full census, and
    a view-set tag on it would be a second, silent way to strip a developer's
    console.
    """
    assert 'name="ui-views"' not in (await client.get("/")).text


async def test_the_published_index_keeps_its_csp(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rewriting the body must not drop the header the rewrite depends on.

    The injected response is a different object from the ``FileResponse`` the
    parent class returned, so the CSP is easy to lose here without noticing.
    """
    monkeypatch.setattr(settings, "ui_profile", "published")
    response = await client.get("/")
    assert "script-src 'self'" in response.headers["content-security-policy"]


# --------------------------------------------------------------------------- #
# Structural guards — the two silent-failure shapes
# --------------------------------------------------------------------------- #


def test_the_index_anchor_the_injection_substitutes_still_exists() -> None:
    """The rewrite is a string substitution; this is its anchor.

    Without this test, editing the tag in ``index.html`` — reformatting it, adding
    an attribute, dropping the self-closing slash — would silently disable the
    injection for the published profile only, which is the profile nobody runs
    locally.
    """
    html = _INDEX.read_text(encoding="utf-8")
    assert html.count(_UI_PROFILE_META_DEV) == 1, (
        f"expected exactly one {_UI_PROFILE_META_DEV!r} in {_INDEX} — the "
        "PLAN-0100 boot injection substitutes this exact literal"
    )


async def test_the_served_index_contains_no_inline_script(client: AsyncClient) -> None:
    """The reason the profile rides a ``<meta>`` and not a ``<script>``.

    ``_OCT_CSP`` pins ``script-src 'self'``. If a later change carries the profile
    (or anything else) in an inline script, the browser blocks it silently and the
    UI falls back to the full console. This asserts the invariant the CSP comment
    claims is grep-verified, so it cannot rot.
    """
    body = (await client.get("/")).text
    # Strip HTML comments first. The invariant is about EXECUTABLE script tags,
    # and this page documents its own no-inline-script rule in prose — a scan
    # that counted the explanation as a violation would be asserting on prose,
    # and would redden for whoever next explains the rule.
    body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    inline = [m.group(0) for m in re.finditer(r"<script(?![^>]*\ssrc=)[^>]*>", body)]
    assert not inline, f"inline <script> found in the served index: {inline}"


# --------------------------------------------------------------------------- #
# AC-9 — the D6 persistent notice
# --------------------------------------------------------------------------- #


def _notice_block() -> str:
    """The banner's source block, from the profile guard to its closing brace.

    Sliced rather than searched whole-file so the element assertions cannot be
    satisfied by the same words appearing somewhere else in ``app.js`` — and so
    the guard and the text are proven to be in the SAME block, which is the
    property AC-9 actually needs.
    """
    source = _APP_JS.read_text(encoding="utf-8")
    marker = "if (O.State.uiProfile === 'published') {"
    assert marker in source, (
        f"the D6 notice must be guarded by {marker!r} in {_APP_JS} — without the "
        "guard it would render on the dev console too, and AC-9 requires it absent there"
    )
    start = source.index(marker)
    end = source.index("\n    }", start)
    return source[start:end]


def test_the_d6_notice_carries_all_six_elements() -> None:
    """Every D6 obligation appears inside the profile-guarded banner block.

    A source-level tripwire, per `docs/conventions/ui.md:104` — this repo has no
    build step and no JS test runner, so a UI tripwire must be a Python test.
    Stated plainly because it matters for what this proves: the banner is
    client-rendered, so this asserts the SOURCE carries the six elements. That the
    browser actually paints them is verified live in the PR, not here.
    """
    block = _notice_block()
    missing = [name for name, text in _D6_NOTICE_ELEMENTS.items() if text not in block]
    assert not missing, f"the D6 notice is missing these obligations: {missing}"


def test_the_d6_notice_is_not_dismissable() -> None:
    """No close control inside the notice block.

    D6 makes the in-app notice the load-bearing consent-capture point precisely
    because the vendor gate page cannot be relied on to render text this repo can
    verify. A dismiss button would turn a required disclosure into an optional one
    — and would look like a UX improvement in review.
    """
    block = _notice_block()
    for control in ("onClick", "dismiss", "close", "hidden"):
        assert (
            control not in block
        ), f"the D6 notice block contains {control!r} — it must be persistent"


def test_the_dev_profile_renders_no_notice() -> None:
    """AC-9's absence half: the guard is an equality against 'published'.

    Asserted on the guard rather than by rendering, for the same reason as above.
    A truthiness check (`if (O.State.uiProfile)`) would render the banner on the
    dev console, where 'dev' is also truthy — which is the one way this could be
    wrong while still looking guarded.
    """
    source = _APP_JS.read_text(encoding="utf-8")
    assert "if (O.State.uiProfile === 'published') {" in source
    assert "if (O.State.uiProfile)" not in source


def test_the_ui_profile_is_read_before_the_first_paint() -> None:
    """``uiProfile`` must be initialised in the ``State`` literal, not fetched.

    Per ``docs/conventions/ui.md`` this is a Python tripwire over the asset source:
    the ordering hazard is that ``app.js`` builds the header before ``initMeta()``
    resolves, so a profile read that moved into an async path would be too late —
    and would look fine in dev, where the answer is the default either way.
    """
    source = _API_JS.read_text(encoding="utf-8")
    state_literal = source.split("const State = {", 1)[1].split("};", 1)[0]
    assert "uiProfile:" in state_literal, (
        "uiProfile must be initialised synchronously in the State literal in "
        f"{_API_JS} — a later, async read would land after buildTabs()"
    )
    assert 'meta[name="ui-profile"]' in state_literal


# --------------------------------------------------------------------------- #
# AC-1(b) — the guard registry (PLAN-0100 Step 3)
# --------------------------------------------------------------------------- #

_ASSETS = Path("services/api/static/assets")

#: Every call site of an excluded-backend wrapper, and WHERE its published-profile
#: guard lives. The guard is often in a different file from the call — hiding Tab E
#: guards ``intake-view.js``'s three calls from ``app.js`` — so each entry names its
#: guard file explicitly rather than assuming the two coincide.
#:
#: Keyed by (wrapper, call file) -> (call count, guard file). The COUNT is
#: load-bearing: set-equality on files alone would stay green if a second,
#: unguarded call to the same wrapper were added to a file already on the list.
#:
#: ``O.API.execute`` is here because of SD-1's C-3 disposition, and it is the entry
#: that justifies the whole mechanism: PLAN-0100's drafted Step-3 list named only
#: Tab B's Execute. Grepping the wrapper found a SECOND call site in Tab D
#: (``view-flow.js``) — a tab that stays on the published surface — which the
#: drafted list would have left rendering a control whose backend 500s.
_GUARD_REGISTRY: dict[tuple[str, str], tuple[int, str]] = {
    ("O.Llm.warm", "llm-control.js"): (1, "app.js"),
    ("O.Llm.sleep", "llm-control.js"): (1, "app.js"),
    ("O.Intake.defaults", "intake-view.js"): (1, "app.js"),
    ("O.Intake.extract", "intake-view.js"): (1, "app.js"),
    ("O.Intake.extract", "view-story.js"): (1, "view-story.js"),
    ("O.Intake.generate", "intake-view.js"): (1, "app.js"),
    ("O.Draft.classify", "intake-procedures.js"): (1, "view-procedures.js"),
    ("O.Draft.build", "intake-procedures.js"): (1, "view-procedures.js"),
    ("O.Draft.instantiate", "intake-procedures.js"): (1, "view-procedures.js"),
    ("O.Hero.event", "view-hero.js"): (1, "view-hero.js"),
    ("O.API.execute", "view-anomaly.js"): (1, "view-anomaly.js"),
    ("O.API.execute", "view-flow.js"): (1, "view-flow.js"),
}

#: The ten-tab census, and the five keys energy does NOT publish.
#:
#: PLAN-0103 Step 2 deleted ``app.js``'s ``PUBLISHED_EXCLUDED_VIEWS`` in favour of
#: a server-declared positive set, so the second name here is no longer a mirror
#: of a constant in the source — it is the HISTORICAL PIN. AC-1 requires the new
#: default to render energy's tabs bit-identically to what the deleted constant
#: produced, and the assertion below states exactly that (default == census minus
#: these five) rather than restating the new default value, which would make the
#: test agree with itself.
_ALL_VIEW_KEYS = set("ABCDEFGHIJ")
_ENERGY_UNPUBLISHED_VIEWS = {"E", "G", "H", "I", "J"}


def _wrappers() -> set[str]:
    return {wrapper for wrapper, _ in _GUARD_REGISTRY}


#: Comment stripping is ``tests.api.js_source.strip_js_comments``, shared with the
#: three other modules that scan these assets as text. The reason this scan needs
#: it at all is worth keeping: session 206 shipped a no-inline-script guard that
#: matched ``<script>`` inside its own HTML comment, and this very registry first
#: counted four ``O.Intake.extract`` "call sites" in ``view-story.js`` when three
#: of them were the comments explaining why the fourth is guarded. A tripwire that
#: counts its own documentation is measuring the wrong thing.
#:
#: The local copy this replaces removed block comments BEFORE line comments, which
#: is the reverse of how JavaScript tokenises — a ``/*`` written inside a ``//``
#: comment opened a phantom block that ran to the next ``*/``. It also DELETED
#: comments rather than blanking them, which can splice ``O.Hero.event/*x*/(`` into
#: a call site that exists in no file; the shared helper blanks, so it cannot.
#:
#: The local copy also carried a ``(?<!:)`` that spared ``://`` so a URL would not
#: truncate the line before a real call. The shared helper reaches that end
#: structurally instead, by treating single- and double-quoted strings as opaque —
#: which covers the case that actually occurs (a URL in a string literal) rather
#: than any ``://`` anywhere. Measured, not assumed: on today's assets no line puts
#: a registered wrapper call after a ``://`` at all, and the local stripper, the
#: shared one, and the shared one WITHOUT string opacity all produce the same twelve
#: observed entries.


def test_excluded_wrapper_call_sites_exactly_equal_the_registry() -> None:
    """A new call site to an excluded backend reddens this — that is the point.

    Scans every ``assets/*.js`` for each registered wrapper and compares the
    observed (wrapper, file, count) triples against the pinned registry. Adding a
    call in a NEW file changes the key set; adding a SECOND call in a file already
    listed changes its count. Both are caught.
    """
    observed: dict[tuple[str, str], int] = {}
    scanned = 0
    for path in sorted(_ASSETS.glob("*.js")):
        source = strip_js_comments(path.read_text(encoding="utf-8"))
        scanned += 1
        for wrapper in _wrappers():
            # Require call syntax, not a mention: `O.Hero.event(` is a call,
            # `O.Hero.event` in prose is not.
            n = source.count(wrapper + "(")
            if n:
                observed[(wrapper, path.name)] = n

    # Non-vacuity: if the glob matched nothing, every set below is trivially equal.
    assert scanned > 10, f"expected the asset directory to be populated, scanned {scanned}"

    expected = {key: count for key, (count, _) in _GUARD_REGISTRY.items()}
    assert observed == expected, (
        "excluded-backend call sites drifted from the pinned registry.\n"
        f"  unregistered / changed: {sorted(set(observed.items()) - set(expected.items()))}\n"
        f"  registered but missing: {sorted(set(expected.items()) - set(observed.items()))}\n"
        "Every call to an excluded backend must be guarded by O.isPublished() and "
        "recorded here — see PLAN-0100 Step 3 and finding C-3."
    )


def test_every_registered_guard_file_actually_carries_the_guard() -> None:
    """The registry names a guard file per call site; the token must be there."""
    for (wrapper, call_file), (_, guard_file) in sorted(_GUARD_REGISTRY.items()):
        source = (_ASSETS / guard_file).read_text(encoding="utf-8")
        assert "O.isPublished()" in source, (
            f"{wrapper} is called from {call_file} and the registry says its "
            f"published-profile guard lives in {guard_file}, but that file does "
            "not call O.isPublished()"
        )


def test_the_single_guard_predicate_is_exported_and_reads_the_profile() -> None:
    """One predicate, not a literal comparison scattered across the assets.

    If a guard were written as ``State.uiProfile === 'published'`` inline, the
    registry test above would still pass while the guard became invisible to any
    future audit that greps for the token.
    """
    api_source = _API_JS.read_text(encoding="utf-8")
    assert "function isPublished()" in api_source
    assert "State.uiProfile === 'published'" in api_source
    assert "isPublished," in api_source, "isPublished must be exported on window.OCT"


# --------------------------------------------------------------------------- #
# PLAN-0103 Step 2 — the server-declared per-system view set
#
# What replaced PUBLISHED_EXCLUDED_VIEWS. The old test read that constant out of
# app.js by name; deleting the constant is AC-1's headline, so that test could not
# survive the change it was verifying. These read the artifacts instead — the
# census in each of its two homes, the shipped default, and the two carriers.
# --------------------------------------------------------------------------- #


def test_the_n1_exclusion_constant_is_gone_from_every_asset() -> None:
    """AC-1's headline: the N=1 hardcode does not survive anywhere under assets/.

    Scanned across every asset rather than app.js alone — a constant that moved to
    a neighbouring file would satisfy a file-scoped check while re-creating
    exactly the coupling Step 2 removed.

    Comments are stripped first, and that is not a loosening. app.js now EXPLAINS
    what the constant was and why it went, so a raw substring scan reddens against
    a correct file for the crime of documenting itself — measured here, on the
    first run of this test. The property AC-1 wants is that no CODE reads the
    constant, and prose about a retired identifier is how the next reader learns
    it was retired.
    """
    offenders = [
        path.name
        for path in sorted(_ASSETS.glob("*.js"))
        if "PUBLISHED_EXCLUDED_VIEWS" in strip_js_comments(path.read_text(encoding="utf-8"))
    ]
    assert not offenders, (
        f"PUBLISHED_EXCLUDED_VIEWS is still live code in {offenders} — PLAN-0103 "
        "Step 2 replaces it with the server-declared ui_published_views set"
    )


def test_the_ten_tab_census_agrees_in_both_of_its_homes() -> None:
    """``config.ALL_VIEW_KEYS`` and ``app.js``'s ``ALL_VIEWS`` are one list, twice.

    The duplication is deliberate — a tab's label, icon and mounting module are
    JS closures with no Python form, while the boot validation must run where the
    setting is parsed — so the drift it invites gets a tripwire rather than a
    comment. Adding an eleventh tab in the browser without adding its key here
    reddens on the commit that opens the gap.
    """
    app_source = _APP_JS.read_text(encoding="utf-8")
    registered = set(re.findall(r"^\s{4}([A-J]): \{ key:", app_source, re.M))
    assert registered == _ALL_VIEW_KEYS, f"the ten-tab census drifted: {sorted(registered)}"
    assert set(ALL_VIEW_KEYS) == registered, (
        f"services/api/config.py ALL_VIEW_KEYS is {sorted(ALL_VIEW_KEYS)} but "
        f"app.js registers {sorted(registered)} — the boot validator would accept "
        "a key the browser cannot render, or reject one it can"
    )


def test_the_shipped_default_renders_energys_published_tabs_unchanged() -> None:
    """AC-1's bit-identical clause, as a property rather than a repeated value.

    Asserted against the FIELD DEFAULT, not a constructed ``Settings()``: an
    instance picks up any ambient ``.env``, so a local override would silently
    turn this into a test of the developer's machine.
    """
    default = str(Settings.model_fields["ui_published_views"].default)
    keys = {part.strip().upper() for part in default.split(",") if part.strip()}
    assert keys == _ALL_VIEW_KEYS - _ENERGY_UNPUBLISHED_VIEWS, (
        f"the default published set is {sorted(keys)}, which does not render "
        "energy's tabs — SD-1(a) drops I/J (DB-backed), SD-2 context drops E "
        "(the intake routes), H's last two allowed routes moved to the excluded "
        "table under C-3, and Step 8 drops G because the hero is bespoke per "
        "design partner (ADR-0032 D1.2) while system #1 pins OCT_VERTICAL=energy, "
        "which owns no hero builder"
    )


def test_an_unknown_published_view_key_fails_the_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The ``ui_profile`` Literal's asymmetry, one level down.

    This value is hand-typed into a per-system ``published.env``. A tab set the
    browser cannot render must stop the process rather than reach a public page.
    """
    monkeypatch.setenv("UI_PUBLISHED_VIEWS", "A,B,Z")
    with pytest.raises(ValidationError):
        Settings()


def test_an_empty_published_view_set_fails_the_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two layers, deliberately, and this is the OUTER one.

    ``app.js`` refuses to render a published page that declared no views and says
    so on screen (Cray's s219 ruling). That refusal fires in a visitor's browser;
    this one fires in the operator's terminal at deploy time. Keeping only the
    inner layer would mean the earliest anyone learns of a blank system is when
    somebody visits it.
    """
    monkeypatch.setenv("UI_PUBLISHED_VIEWS", "")
    with pytest.raises(ValidationError):
        Settings()


def test_a_repeated_published_view_key_fails_the_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A repeat is always a typo, and the browser would hide it.

    ``Object.fromEntries`` collapses duplicate keys silently, so the tab set would
    look right while the declaration was wrong — and the NEXT edit to that
    declaration would be made against a value nobody had reason to doubt.
    """
    monkeypatch.setenv("UI_PUBLISHED_VIEWS", "A,B,A")
    with pytest.raises(ValidationError):
        Settings()


def test_the_view_set_is_filtered_at_definition_and_drives_the_default_tab() -> None:
    """The two structural properties the old exclusion test protected.

    Filtering VIEWS itself keeps containers, ``buildTabs()``, ``go()``'s
    unknown-key fallback and the ``oct:goto`` listener correct by construction.
    The default-tab half is new: ``go()`` used to fall back to a hardcoded ``'A'``,
    which is right for energy and wrong for procurement, whose Tab A is
    structurally blank — so the landing tab must come from the declared order.
    """
    app_source = strip_js_comments(_APP_JS.read_text(encoding="utf-8"))
    assert "const VIEWS = DECLARED" in app_source
    assert (
        "const DEFAULT_VIEW = Object.keys(VIEWS)[0]" in app_source
    ), "the default landing tab must be the FIRST declared key, not a constant"
    assert (
        "k = 'A'" not in app_source
    ), "go() still hardcodes 'A' as its fallback view — procurement lands on G"


def test_a_published_page_with_no_declared_set_refuses_to_render() -> None:
    """Cray's ruling (s219): refuse visibly, never guess.

    Both meta tags ride one substitution, so reaching this branch means a premise
    broke. Guessing is wrong in either direction — the full census renders
    controls whose backends the allowlist 404s, and a hardcoded set is a guess
    about which system this is. Pinned at source level because the alternative
    (falling back to ``ALL_VIEWS``) is a one-word edit that would look harmless.
    """
    app_source = strip_js_comments(_APP_JS.read_text(encoding="utf-8"))
    assert (
        "if (O.isPublished() && !Object.keys(VIEWS).length)" in app_source
    ), "boot() must refuse to render a published page that declared no views"
    assert "function renderUnconfigured" in app_source


def test_every_edited_asset_got_a_cache_bust() -> None:
    """A stale ``?v=`` serves the OLD file, so a browser check would verify nothing.

    Each floor is the token the asset carried when a PLAN last edited it — a
    per-file counter, not a build number, so the values differing from each other
    is normal and not drift. ``api.js`` and ``app.js`` were raised by PLAN-0103
    Step 2; the rest still hold PLAN-0100 Step 3's floors.
    """
    index = _INDEX.read_text(encoding="utf-8")
    for name, minimum in (
        ("api.js", 48),
        ("app.js", 49),
        ("view-anomaly.js", 26),
        ("view-flow.js", 38),
        ("view-procedures.js", 26),
        ("view-story.js", 39),
        # PLAN-0103 Step 6 raised these three.
        ("view-hero.js", 49),
        ("auth.js", 34),
        ("view-monitor.js", 41),
    ):
        match = re.search(rf"assets/{re.escape(name)}\?v=c(\d+)", index)
        assert match, f"{name} is not versioned in index.html"
        assert int(match.group(1)) >= minimum, (
            f"{name} is served at ?v=c{match.group(1)} but was edited at "
            f"c{minimum} — a stale cache-bust serves the pre-edit file"
        )


def test_sd8_iii_narrative_copy_is_published_only() -> None:
    """SD-8's ruled option (iii), asserted at the only level it HAS an oracle.

    🔴 What is deliberately NOT asserted: the wording. The ruling's accepted cost
    is "copy with no oracle" — no test can say the sentence is the right sentence,
    and one that pinned a string it also defined would be vacuous by construction
    while looking rigorous. Softening that cost by inventing an oracle would
    quietly overturn what Cray accepted.

    What IS assertable, and is: the copy is reachable on the published profile and
    unreachable on dev. Read off the shipped source, so a call site deleted or
    moved out from behind the profile guard reddens this.
    """
    src = strip_js_comments((_ASSETS / "view-hero.js").read_text(encoding="utf-8"))
    assert "renderApproveBeatNote" in src, "the SD-8 (iii) copy has no producer"
    assert "if (O.isPublished()) container.appendChild(renderApproveBeatNote());" in src, (
        "the copy must render on the PUBLISHED profile and only there — an "
        "unguarded call would put it on the dev console too, and a guard on "
        "anything but the profile would not be SD-8's answer"
    )
    assert "hero-approve-beat" in src, (
        "the block needs a stable test id, or the browser check that it actually "
        "paints has nothing to look for"
    )


# --------------------------------------------------------------------------- #
# PLAN-0103 Step 6 — the published persona picker.
#
# The picker hands RAW credentials to a browser (Cray, typed s224, credential
# option (a)), so every assertion below is about a boundary rather than a
# nicety: which profile may emit them, which person_ids may be offered, and
# whether the name on screen is the one the audit trail will record.
# --------------------------------------------------------------------------- #

_RAW_TOM = "test-raw-tom"
_RAW_WIRAT = "test-raw-wirat"
_DIG_TOM = hashlib.sha256(_RAW_TOM.encode()).hexdigest()
_DIG_WIRAT = hashlib.sha256(_RAW_WIRAT.encode()).hexdigest()
_AUTH_JS = _ASSETS / "auth.js"
_MONITOR_JS = _ASSETS / "view-monitor.js"


def test_personas_configured_without_api_keys_fails_the_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A picker with no digests behind it offers three logins that all 401.

    Caught at boot rather than at the first click, because the click happens in
    a visitor's browser on the one system whose whole story is the approve beat.
    """
    monkeypatch.setenv("UI_DEMO_PERSONA_KEYS", f'{{"req-mechanic-tom": "{_RAW_TOM}"}}')
    monkeypatch.setenv("API_KEYS", "{}")
    with pytest.raises(ValidationError):
        Settings()


def test_a_persona_key_absent_from_api_keys_fails_the_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The raw key and its digest are typed in from two places; they can drift."""
    monkeypatch.setenv("UI_DEMO_PERSONA_KEYS", f'{{"req-mechanic-tom": "{_RAW_TOM}"}}')
    monkeypatch.setenv("API_KEYS", f'{{"{_DIG_WIRAT}": "appr-fleet-manager-wirat"}}')
    with pytest.raises(ValidationError):
        Settings()


def test_a_crossed_persona_pair_fails_the_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The failure mode nothing downstream would look wrong for.

    A crossed pair logs in successfully. The card says one persona, the audit
    trail records the other, and the on-screen disclosure — "recorded under this
    name" — becomes false while every surface still looks healthy. That is worse
    than a missing pair, which merely refuses.
    """
    monkeypatch.setenv("UI_DEMO_PERSONA_KEYS", f'{{"req-mechanic-tom": "{_RAW_WIRAT}"}}')
    monkeypatch.setenv("API_KEYS", f'{{"{_DIG_WIRAT}": "appr-fleet-manager-wirat"}}')
    with pytest.raises(ValidationError):
        Settings()


def test_a_correctly_paired_persona_boots(monkeypatch: pytest.MonkeyPatch) -> None:
    """The positive control for the three refusals above.

    Without it, all three would also pass in a world where ``Settings()`` raised
    for some unrelated reason — an absence oracle needs a matching presence one
    (Lesson #0040).
    """
    monkeypatch.setenv("UI_DEMO_PERSONA_KEYS", f'{{"req-mechanic-tom": "{_RAW_TOM}"}}')
    monkeypatch.setenv("API_KEYS", f'{{"{_DIG_TOM}": "req-mechanic-tom"}}')
    assert Settings().ui_demo_persona_keys == {"req-mechanic-tom": _RAW_TOM}


def test_an_unauthored_persona_is_refused_at_boot() -> None:
    """The picker may only offer principals the vertical actually authors.

    Resolved through the same ``_principal_index`` ``get_current_principal``
    uses, so a card cannot exist for a persona auth would 403. Asserting the
    refusal here is what keeps that reuse from being quietly replaced by a
    second, more permissive lookup.
    """
    with pytest.raises(DemoPersonaError):
        resolve_demo_personas("fleet_maintenance", {"appr-nobody": _RAW_TOM})


def test_personas_on_a_vertical_that_authors_none_is_refused() -> None:
    """energy ships no principals, so a picker there would offer nobody."""
    with pytest.raises(DemoPersonaError):
        resolve_demo_personas("energy", {"req-mechanic-tom": _RAW_TOM})


def test_no_personas_configured_resolves_empty_rather_than_raising() -> None:
    """OFF is the correct posture for every system but fleet, not an error."""
    assert resolve_demo_personas("energy", {}) == []


def test_the_offer_set_is_in_authored_order_not_env_order() -> None:
    """The three cards ARE the authority ladder, so their order carries meaning.

    Deliberately fed in shuffled: an operator re-ordering a JSON object in a
    deployment file must not re-order the ladder a visitor reads.
    """
    personas = resolve_demo_personas(
        "fleet_maintenance",
        {"appr-owner": "k3", "req-mechanic-tom": "k1", "appr-fleet-manager-wirat": "k2"},
    )
    assert [p.person_id for p in personas] == [
        "req-mechanic-tom",
        "appr-fleet-manager-wirat",
        "appr-owner",
    ]


def test_the_persona_name_is_the_authored_name_never_the_config_key() -> None:
    """The card's label is projected from procedures.yaml, not from the env.

    So the name on the card cannot drift from the name the SoD ladder enforces —
    they are the same string, read once.
    """
    personas = resolve_demo_personas("fleet_maintenance", {"appr-owner": "k"})
    assert personas[0].name == "เฮีย — เจ้าของกิจการ"
    assert personas[0].roles == sorted(
        personas[0].roles
    ), "roles must be sorted for a stable wire shape"


@pytest.mark.anyio
async def test_the_dev_profile_emits_no_personas(
    monkeypatch: pytest.MonkeyPatch, client: AsyncClient
) -> None:
    """Direction one of two: raw credentials never leave a dev process.

    The picker's own gate in ``view-monitor.js`` is ``O.isPublished() &&
    demoPersonas().length`` — two independent reasons it cannot render here, and
    this asserts the SERVER-side one so the browser is never the only thing
    standing between a dev box and a credential in a response body.
    """
    monkeypatch.setattr(settings, "ui_profile", "dev")
    monkeypatch.setattr(settings, "ui_demo_persona_keys", {"appr-owner": "k"})
    body = (await client.get("/meta")).json()
    assert body["ui_demo_personas"] == []


@pytest.mark.anyio
async def test_the_published_profile_emits_the_configured_personas(
    monkeypatch: pytest.MonkeyPatch, client: AsyncClient
) -> None:
    """Direction two: the same configuration DOES reach a published response.

    Without this the emptiness above would also pass in the world where the
    field was never wired to anything at all.
    """
    monkeypatch.setattr(settings, "ui_profile", "published")
    monkeypatch.setattr(settings, "oct_vertical", "fleet_maintenance")
    monkeypatch.setattr(settings, "ui_demo_persona_keys", {"appr-owner": "k-owner"})
    body = (await client.get("/meta")).json()
    assert [p["person_id"] for p in body["ui_demo_personas"]] == ["appr-owner"]
    assert body["ui_demo_personas"][0]["key"] == "k-owner", (
        "the raw key must reach the browser — that is the ruled credential path, "
        "and a picker without it would offer a card that cannot log in"
    )


def test_the_stored_identity_prefers_the_server_over_anything_typed() -> None:
    """The display-honesty fix, asserted over the shipped source.

    Before Step 6 ``auth.js`` stored the operator's TYPED identity while
    ``/whoami`` was already returning the authored ``Person.name`` for the key it
    resolved. On a public surface that gap let a visitor's own words render
    beside a governed decision. The ordering below is the fix: ``served`` first,
    the typed value only as the auth-disabled fallback.
    """
    src = strip_js_comments(_AUTH_JS.read_text(encoding="utf-8"))
    assert (
        "served.display_name || served.person_id" in src
    ), "auth.js must resolve the identity from /whoami's answer"
    resolved_at = src.index("const resolved =")
    fallback_at = src.index("(ident || '').trim()")
    assert resolved_at < fallback_at, (
        "the typed value must be the FALLBACK, not the preference — if it is "
        "read first the server's answer can never win"
    )


def test_the_disclosure_is_gated_on_the_server_having_resolved_the_name() -> None:
    """SD-4(b)'s promise is only true when the server said the name.

    On an auth-disabled dev box the identity is whatever was typed, so claiming
    it is the audited one would be the same dishonesty this Step removes,
    pointing the other way.
    """
    src = strip_js_comments(_MONITOR_JS.read_text(encoding="utf-8"))
    assert "O.Auth.serverResolved && O.Auth.serverResolved()" in src
    assert "operate-disclosure" in src


def test_the_picker_replaces_the_key_form_rather_than_joining_it() -> None:
    """Asking a public visitor for a key they do not have is the dead control.

    The branch must RETURN, so the raw key + free-text identity inputs cannot
    render underneath the cards.
    """
    src = strip_js_comments(_MONITOR_JS.read_text(encoding="utf-8"))
    gate = src.index("if (O.isPublished() && demoPersonas().length)")
    key_input = src.index("'operate-key'")
    assert gate < key_input, "the picker branch must precede the key form"
    assert "return bar;" in src[gate:key_input], (
        "the published branch must return — otherwise the key form renders below "
        "the cards, which is the dead-control shape SD-3 called worse than absence"
    )
