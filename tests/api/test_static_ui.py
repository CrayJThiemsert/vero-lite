"""Static-UI serving tests (PLAN-0013 Step 5).

The Claude-Design OCT demo UI is served same-origin from FastAPI (OQ-4 —
one process, one URL, no CORS). These assert the static mount serves the
SPA + its assets, and — critically — that mounting it at "/" did NOT
shadow the API routes the UI fetches (Lesson #7 §3: assert on response
status + content-type, not shell exit codes).
"""

from __future__ import annotations

import mimetypes
import re
from pathlib import Path

from httpx import AsyncClient

from services.api import main


async def test_root_serves_the_oct_ui(client: AsyncClient) -> None:
    """GET / serves the OCT single-page UI (index.html)."""
    response = await client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert "OCT" in body
    assert "assets/app.js" in body  # the SPA bootstraps its asset bundle


async def test_assets_are_served(client: AsyncClient) -> None:
    """The UI's JS/CSS bundle is reachable under /assets/."""
    js = await client.get("/assets/app.js")
    assert js.status_code == 200
    assert "OCT" in js.text  # the app bootstrap
    css = await client.get("/assets/theme.css")
    assert css.status_code == 200


async def test_static_mount_does_not_shadow_api(client: AsyncClient) -> None:
    """The "/" static mount must NOT shadow the JSON API routes the UI calls."""
    health = await client.get("/health")
    assert health.status_code == 200
    assert health.headers["content-type"].startswith("application/json")
    assert health.json()["status"] == "ok"

    meta = await client.get("/meta")
    assert meta.status_code == 200
    assert meta.headers["content-type"].startswith("application/json")
    assert meta.json()["vertical"] == "energy"


async def test_openapi_still_reachable(client: AsyncClient) -> None:
    """The OpenAPI schema (and the routes it lists) survive the static mount."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert {"/meta", "/recommendations", "/query"} <= set(paths)


async def test_unknown_path_is_404_not_500(client: AsyncClient) -> None:
    """An unknown path falls through the static mount to a clean 404."""
    response = await client.get("/no-such-asset.js")
    assert response.status_code == 404


# --- header geometry census (session 202) -----------------------------------
#
# The nav bar overflowed because `theme.css`'s responsive ladder was written for
# a five-tab header ("A-E nav", its own comment) while `app.js` grew to ten
# registered views. Nothing connected the two, so each added tab silently ate
# headroom until the header ran 443px past the viewport (s197: scrollWidth 1825
# vs clientWidth 1382).
#
# The fix re-measured the ladder against the real census. This pins the census
# the measurement was taken against, so the NEXT added tab reddens a test
# instead of silently re-breaking the bar. It is deliberately a set-equality
# assertion, not a count: swapping one tab for another still changes what was
# measured.

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS = REPO_ROOT / "services" / "api" / "static" / "assets"

#: The tab census `theme.css`'s breakpoints were measured against (2026-08-03).
#: Changing this set REQUIRES re-running the geometry measurement and updating
#: the breakpoint block in theme.css — see its comment for the recorded numbers.
MEASURED_TAB_CENSUS = frozenset("ABCDEFGHIJ")


def _registered_view_keys() -> frozenset[str]:
    """The view keys `app.js` actually registers, read from source.

    Reads ``ALL_VIEWS`` — the full ten-tab census — deliberately, not the profile
    filtered ``VIEWS`` that PLAN-0100 Step 3 derives from it. The ladder this
    census guards has to accommodate the WIDEST header the app can render, which
    is the dev profile's ten tabs; measuring it against the published profile's
    six would let a tab be added to the census unnoticed as long as the published
    profile happened to drop it.

    (Before Step 3 the literal was ``const VIEWS = {``. The rename is why this
    helper changed — the census itself did not.)
    """
    source = (ASSETS / "app.js").read_text(encoding="utf-8")
    start = source.index("const ALL_VIEWS = {")
    # The block ends at the first line that closes it at column 2 ("  };").
    end = source.index("\n  };", start)
    return frozenset(re.findall(r"key:\s*'([A-Z])'", source[start:end]))


def test_tab_census_matches_the_measured_header_ladder() -> None:
    """The registered tabs must equal the census the CSS ladder was measured for.

    Fails loudly on an added, removed, or renamed tab — the exact drift that
    produced the overflow, and which no existing test could see.
    """
    registered = _registered_view_keys()
    assert registered == MEASURED_TAB_CENSUS, (
        f"app.js registers {sorted(registered)} but theme.css's responsive "
        f"ladder was measured against {sorted(MEASURED_TAB_CENSUS)}. Re-run the "
        f"header geometry measurement at 1280/1366/1440/1680/1920, update the "
        f"breakpoint block in theme.css (and its recorded numbers), then update "
        f"MEASURED_TAB_CENSUS. Do not just widen this set."
    )


def test_header_ladder_collapses_inactive_tab_labels_by_default() -> None:
    """The inactive-label collapse must stay a default, not a small-screen rung.

    Measured at ten tabs: the full-label header needs 2253px, so it fits no
    ordinary desktop (1920 overflowed by 95px, 1440 by 411px). The collapse
    therefore fires below 2300px rather than the original 1360px. If someone
    restores a narrow breakpoint, the bar silently overflows again at 1440 —
    which is the single most common demo width.
    """
    css = (ASSETS / "theme.css").read_text(encoding="utf-8")
    match = re.search(
        r"@media \(max-width: (\d+)px\) \{[^}]*\.tab:not\(\.active\)[^}]*"
        r"span:not\(\.key\):not\(\.badge-dot\)[^}]*display:\s*none",
        css,
        re.DOTALL,
    )
    assert match is not None, (
        "theme.css no longer collapses inactive tab labels at any breakpoint — "
        "with ten tabs the header cannot fit without it."
    )
    breakpoint_px = int(match.group(1))
    assert breakpoint_px >= 2253, (
        f"the inactive-tab-label collapse fires at max-width {breakpoint_px}px, "
        f"but the measured full-label header width is 2253px. Between those two "
        f"widths every tab renders its label and the bar overflows (measured: "
        f"411px at 1440, 95px at 1920)."
    )


def test_static_types_do_not_depend_on_the_base_images_mime_files() -> None:
    """Every served extension must type correctly in the DEPLOYED image, not just here.

    Starlette types a static file with ``guess_type(...)[0] or "text/plain"``, and
    ``mimetypes`` seeds itself from the OS's mime files. The runtime image
    (``python:3.12-slim``) ships none — ``mimetypes.knownfiles`` resolves to ``[]``
    inside the container — so anything the built-in table does not know is served
    as ``text/plain``. PLAN-0100 Step 11 measured exactly that against the live
    edge: the bundled IBM Plex ``.woff2`` fonts came back
    ``content-type: text/plain; charset=utf-8`` (D-3).

    ⚠️ A naive version of this test — serve a font, assert the header — passes on a
    developer box WITHOUT the fix, because this box HAS ``/etc/mime.types``. That
    is why the check runs against a pristine ``MimeTypes()``, which seeds from the
    built-in table alone and therefore reproduces the image's condition rather
    than this machine's.
    """
    image_like = mimetypes.MimeTypes()  # built-in table only == the slim image

    extensions = {
        path.suffix.lower() for path in (ASSETS.parent).rglob("*") if path.is_file() and path.suffix
    }
    assert extensions, f"no static files found under {ASSETS.parent} — guard would be vacuous"

    unresolved = {
        extension for extension in extensions if image_like.guess_type(f"x{extension}")[0] is None
    }
    registered = {extension for _type, extension in main._STATIC_MIME_TYPES}

    uncovered = sorted(unresolved - registered)
    assert not uncovered, (
        f"static file extension(s) {uncovered} are served from this tree, cannot be "
        f"typed by a mimetypes seeded only from Python's built-in table — which is "
        f"what the deployed image has — and are not registered in "
        f"main._STATIC_MIME_TYPES. Starlette will serve them as text/plain. "
        f"Registered today: {sorted(registered)}."
    )


async def test_a_bundled_font_is_served_with_a_font_content_type(
    client: AsyncClient,
) -> None:
    """The end-to-end half: drive the real static mount and read the real header.

    Weaker than the guard above on its own (it cannot fail on a box that has
    /etc/mime.types), but it is the only check that proves the registration is
    actually reached by the serving path rather than merely present in a module.
    """
    fonts = sorted((ASSETS / "fonts").glob("*.woff2"))
    assert fonts, "no bundled .woff2 fonts found — the CSP sets font-src 'self'"

    response = await client.get(f"/assets/fonts/{fonts[0].name}")
    assert response.status_code == 200
    content_type = response.headers["content-type"]
    assert content_type.startswith("font/"), (
        f"{fonts[0].name} is served as {content_type!r}. `font-src 'self'` allows it "
        f"today only because no X-Content-Type-Options: nosniff header is set; "
        f"adding that ordinary hardening step would break every bundled font."
    )
