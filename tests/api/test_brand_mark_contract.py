"""The header's brand mark: the file the JS names is the file the app serves.

The repo has no build step and no JS test runner (``docs/conventions/ui.md`` §5), so a
CI tripwire for the UI has to be a Python test that reads the shipped source. This
module reads ``services/api/static/assets/app.js`` — the ARTIFACT, never a restatement
of it — following ``test_origin_narrative_contract``'s precedent.

**Why this seam needs a reader.** The mark used to be an inline SVG built by ``icon()``:
a rename there is a JavaScript error somebody notices. It is now a raster referenced by
a *string*, and a wrong string is not an error — the header renders a broken-image glyph,
the console logs a 404 nobody is watching, and every test in the suite stays green.
``test_asset_manifest``'s bijection cannot see it either: that guard globs ``*.js`` and
``*.css`` at the top of ``assets/``, so neither this file's subdirectory nor its
extension is in its scope.

**Why the served bytes are compared to the file on disk.** The published deployment ships
this image *inside the image* (``Dockerfile`` COPYs ``services/``, and pointedly not
``docs/``, where the source artwork lives). "It is on my disk" and "the container serves
it" are different claims, and only the second one matters to a visitor.

**What this cannot prove.** It is a source-and-serving contract, not a rendering test.
That the mark is legible at 28 px, that it sits correctly against the tile, and that the
aspect ratio survives ``object-fit`` are browser observations — evidence, not the gate.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from httpx import AsyncClient

from services.api import main
from tests.api.js_source import strip_js_comments

_STATIC = Path(main.__file__).resolve().parent / "static"
_APP_JS = _STATIC / "assets" / "app.js"

#: ``h('img', { src: 'assets/brand/cray-j.png', … })`` inside the brand block.
_MARK_SRC = re.compile(r"src\s*:\s*'(assets/brand/[^']+)'")


def _declared_src() -> str:
    src = strip_js_comments(_APP_JS.read_text(encoding="utf-8"))
    found = _MARK_SRC.findall(src)
    assert found, (
        "app.js declares no assets/brand/* image src — the brand mark was renamed, "
        "removed, or moved, and every assertion below would parse nothing and pass "
        "vacuously"
    )
    assert len(found) == 1, f"expected exactly one brand mark, found {found}"
    return found[0]


def test_the_parse_finds_the_declared_mark() -> None:
    """Positive control: the instrument reads the artifact at all."""
    assert _declared_src().endswith(".png")


def test_the_mark_is_rendered_inside_the_brand_tile() -> None:
    """A shipped image nothing renders is a file, not a logo."""
    src = strip_js_comments(_APP_JS.read_text(encoding="utf-8"))
    brand = src[src.find("class: 'brand'") :]
    assert brand, "the brand block is gone from app.js"
    mark = brand[: brand.find("wordmark")]
    assert "assets/brand/" in mark, (
        "the brand mark image is no longer inside the .mark tile — it may still be "
        "declared elsewhere in the file while the header renders nothing"
    )


def test_the_mark_declares_alt_text() -> None:
    """A brand mark with no alt text is an unlabelled image in the page's first tab stop."""
    src = strip_js_comments(_APP_JS.read_text(encoding="utf-8"))
    window = src[src.find("assets/brand/") - 200 : src.find("assets/brand/") + 200]
    assert "alt:" in window, "the brand mark image declares no alt attribute"


def test_the_mark_file_exists_on_disk() -> None:
    target = _STATIC / _declared_src()
    assert target.is_file(), f"app.js declares {_declared_src()!r}, absent at {target}"
    assert target.stat().st_size > 0, "the brand mark file is empty"


@pytest.mark.anyio
async def test_the_declared_path_is_the_path_the_server_serves(client: AsyncClient) -> None:
    """The seam: a real GET through the real static mount, at the JS's own string.

    Self-guarded rather than leaning on the positive control above — ``_declared_src``
    raises on an empty parse, so this cannot pass by asking for nothing.
    """
    rel = _declared_src()
    response = await client.get("/" + rel)
    assert response.status_code == 200, (
        f"the brand mark is declared at {rel!r} but the app served HTTP "
        f"{response.status_code} — the header would render a broken image"
    )
    assert (
        response.content == (_STATIC / rel).read_bytes()
    ), f"the bytes served at /{rel} differ from the file on disk"
    assert response.headers["content-type"].startswith("image/"), (
        f"served as {response.headers['content-type']!r}, not an image type — a "
        "browser may refuse to paint it"
    )


@pytest.mark.anyio
async def test_the_mark_is_a_real_png(client: AsyncClient) -> None:
    """Content, not just a 200. A text file at the right path would satisfy the seam."""
    body = (await client.get("/" + _declared_src())).content
    assert body[:8] == b"\x89PNG\r\n\x1a\n", (
        "the served brand mark does not carry a PNG signature — the path resolves to "
        "something that is not the image it claims to be"
    )
