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

_INDEX = Path("services/api/static/index.html")
_API_JS = Path("services/api/static/assets/api.js")


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
