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

import re
from pathlib import Path

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from services.api.config import Settings, settings
from services.api.main import _UI_PROFILE_META_DEV
from tests.api.js_source import strip_js_comments

_INDEX = Path("services/api/static/index.html")
_API_JS = Path("services/api/static/assets/api.js")
_APP_JS = Path("services/api/static/assets/app.js")

#: AC-9 — the six elements ADR-0035 D6 obliges the persistent notice to carry,
#: each pinned by its own substring.
#:
#: Individually, not as one "is there a banner" check, because the realistic
#: failure is a REWORD that drops one line — most likely the Cloudflare sentence,
#: which reads like vendor detail rather than an obligation. Keyed by the
#: obligation so the assertion message names what went missing, not just that
#: something did.
_D6_NOTICE_ELEMENTS = {
    "what is retained (typed text)": "What you type is retained",
    "for how long (90 days)": "90 days",
    "who reads it (the operator)": "read only by the operator",
    "the gate processes the email via Cloudflare": "Cloudflare",
    "traffic transits the vendor edge": "vendor edge",
    "the demo is synthetic": "synthetic",
    "enter no real personal data": "real personal data",
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

#: The ten-tab census, and the four the published profile drops.
_ALL_VIEW_KEYS = set("ABCDEFGHIJ")
_PUBLISHED_EXCLUDED_VIEWS = {"E", "H", "I", "J"}


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


def test_published_profile_drops_exactly_the_four_fully_excluded_tabs() -> None:
    """Tab gating is done by filtering VIEWS itself, so downstream is automatic."""
    app_source = _APP_JS.read_text(encoding="utf-8")

    all_keys = set(re.findall(r"^\s{4}([A-J]): \{ key:", app_source, re.M))
    assert all_keys == _ALL_VIEW_KEYS, f"the ten-tab census drifted: {sorted(all_keys)}"

    excluded_literal = app_source.split("const PUBLISHED_EXCLUDED_VIEWS = ", 1)[1].split("]", 1)[0]
    excluded = set(re.findall(r"'([A-J])'", excluded_literal))
    assert excluded == _PUBLISHED_EXCLUDED_VIEWS, (
        f"published-profile tab exclusions drifted: {sorted(excluded)} != "
        f"{sorted(_PUBLISHED_EXCLUDED_VIEWS)} — SD-1(a) drops I/J (DB-backed), "
        "SD-2 context drops E (/intake/*), and H's last two allowed routes moved "
        "to the excluded table under C-3"
    )
    assert "const VIEWS = O.isPublished()" in app_source, (
        "VIEWS must be filtered at definition so containers, buildTabs(), go()'s "
        "unknown-key fallback and the oct:goto listener are all correct by "
        "construction rather than each needing its own branch"
    )


def test_every_edited_asset_got_a_cache_bust() -> None:
    """A stale ``?v=`` serves the OLD file, so a browser check would verify nothing."""
    index = _INDEX.read_text(encoding="utf-8")
    for name, minimum in (
        ("api.js", 47),
        ("app.js", 47),
        ("view-anomaly.js", 26),
        ("view-flow.js", 38),
        ("view-procedures.js", 26),
        ("view-hero.js", 48),
        ("view-story.js", 39),
    ):
        match = re.search(rf"assets/{re.escape(name)}\?v=c(\d+)", index)
        assert match, f"{name} is not versioned in index.html"
        assert int(match.group(1)) >= minimum, (
            f"{name} is served at ?v=c{match.group(1)} but Step 3 edited it at "
            f"c{minimum} — a stale cache-bust serves the pre-Step-3 file"
        )
