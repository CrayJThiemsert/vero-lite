"""PLAN-0126 — the story-mode explainer page: serving, origin, wording, files, edge, link.

The explainer is a standalone page at ``/story/`` (Cray's ruling L1): opened in a new
tab from the console, never a tab in the strip. Every guard here reads the REAL files or
drives the REAL static mount; none stubs the mount, the config or the page.

Each negative assertion carries a positive control, because "nothing found" is also
what a checker that reads nothing reports:

* AC-1 / AC-5 — the checker is shown to flag a known-bad string before its clean
  reading of the page is trusted.
* AC-3 — a path that must NOT be admitted is shown to match no row.
* AC-6 — the parse must find at least one reference of each kind.
* AC-11 — the relative checker is shown to flag a root-relative font URL.
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import yaml
from httpx import ASGITransport, AsyncClient
from starlette.responses import FileResponse

from services.api.config import settings
from services.api.main import _OCT_CSP, _StaticFilesWithCSP, app
from tests.api.js_source import strip_js_comments
from tests.api.story_source import (
    AUTHORED_FILES,
    REPO_ROOT,
    STATIC_DIR,
    STORY_DIR,
    VENDORED_FILES,
    authored_text,
    external_references,
    extract_block,
    references,
)
from tests.api.test_static_ui import MEASURED_TAB_CENSUS, _registered_view_keys

_FLEET_INGRESS = REPO_ROOT / "deploy/published/oct-fleet-maintenance/cloudflared/config.yml"
_APP_JS = STATIC_DIR / "assets" / "app.js"
_FONTS_DIR = STATIC_DIR / "assets" / "fonts"

#: A font URL that works at /story/ and 404s in the multi-file Artifact (PLAN-0126 G32).
_KNOWN_ROOT_RELATIVE_URL = "@font-face{src:url('/assets/fonts/x.woff2') format('woff2')}"

#: The stage-1 prototype's own CDN import — the exact line AC-1 exists to keep out.
_KNOWN_CDN_IMPORT = (
    "import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';"
)

#: Literals the intro-video rulings keep off screen (docs/strategy/public/
#: intro-video-production-rulings.md §2-§3; PLAN-0126 L2). Lexical only — meaning is
#: Cray's semantic read at the PR (§8), because no test can read a caption's intent.
_RULED_OUT_LITERALS = (
    "http://",
    "https://",
    "www.",
    "30,001",
    "฿30,001",
    "สามหมื่นเอ็ด",
    "immutable",
    "ไม่ให้โมเดลตัดสินอะไรเลย",
    "12/12",
)

#: `.js`/`.css` files in story/ allowed to be referenced by nothing. Written, not
#: computed — and empty: every script and stylesheet the page ships is loaded.
_UNREFERENCED_STORY_FILES: dict[str, str] = {}


@pytest.fixture
async def story_client() -> AsyncIterator[AsyncClient]:
    """The real app over ASGI, with app exceptions returned as 500 rather than raised.

    A fail-loud raise in the index rewrite must read as a status the assertion can
    name, not as a test crash that looks like an unrelated error.
    """
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


def _authored_texts() -> dict[str, str]:
    missing = [name for name in AUTHORED_FILES if not (STORY_DIR / name).is_file()]
    assert not missing, f"authored story files missing: {missing}"
    return {name: authored_text(name) for name in AUTHORED_FILES}


# --------------------------------------------------------------------------- #
# AC-1 — the served story loads nothing from outside the origin
# --------------------------------------------------------------------------- #


def test_story_files_reference_no_external_origin() -> None:
    """No script, stylesheet, module or font leaves the origin (console CSP, G1)."""
    texts = _authored_texts()
    all_refs = {name: references(name, text) for name, text in texts.items()}
    external = {name: external_references(name, text) for name, text in texts.items()}
    total = sum(len(refs) for refs in all_refs.values())
    print(f"files={len(texts)} refs={total} external={sum(len(v) for v in external.values())}")
    assert not any(external.values()), f"external references: {external}"
    assert (
        total >= 4
    ), f"only {total} references parsed across {sorted(texts)} — the scan read nothing"


def test_the_origin_checker_flags_a_known_cdn_import() -> None:
    """Positive control: the checker AC-1 trusts does find the stage-1 CDN import."""
    flagged = external_references("story.js", _KNOWN_CDN_IMPORT)
    print(f"flagged={flagged}")
    assert flagged == ["https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js"]


# --------------------------------------------------------------------------- #
# AC-2 — /story/ is served under the CSP on the published profile, unprofiled,
#        and PLAN-0100's fail-loud root stays intact
# --------------------------------------------------------------------------- #


async def test_story_index_is_served_unprofiled_on_the_published_profile(
    story_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The nested index is a plain file: no profile rewrite, no raise, the CSP stamped."""
    monkeypatch.setattr(settings, "ui_profile", "published")
    response = await story_client.get("/story/")
    csp = response.headers.get("content-security-policy") == _OCT_CSP
    profile_meta = 'name="ui-profile"' in response.text
    cache = response.headers.get("cache-control", "")
    print(
        f"status={response.status_code} csp={'match' if csp else 'MISMATCH'} "
        f"profile_meta={'present' if profile_meta else 'absent'} cache_control={cache!r}"
    )
    assert response.status_code == 200
    assert csp
    assert 'type="module" src="story.js' in response.text
    assert not profile_meta
    assert cache != "no-store"


async def test_root_index_is_still_profiled(
    story_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Control: narrowing the match did not stop the CONSOLE's index being rewritten."""
    monkeypatch.setattr(settings, "ui_profile", "published")
    response = await story_client.get("/")
    published_tag = '<meta name="ui-profile" content="published" />' in response.text
    print(f"status={response.status_code} published_tag={published_tag}")
    assert response.status_code == 200
    assert published_tag


def test_profiled_index_still_raises_without_the_anchor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Control: an index that IS profiled and lacks the anchor still fails loud."""
    monkeypatch.setattr(settings, "ui_profile", "published")
    page = tmp_path / "index.html"
    page.write_text("<!doctype html><title>no anchor</title>", encoding="utf-8")
    mount = _StaticFilesWithCSP(directory=tmp_path, html=True)
    with pytest.raises(RuntimeError, match="ui-profile anchor"):
        mount._profiled_index(FileResponse(page))


# --------------------------------------------------------------------------- #
# AC-3 — the edge admits exactly the story's files, and nothing deeper
# --------------------------------------------------------------------------- #


def _story_ingress_rows() -> list[str]:
    doc = yaml.safe_load(_FLEET_INGRESS.read_text(encoding="utf-8"))
    return [rule["path"] for rule in doc["ingress"] if "path" in rule and "/story" in rule["path"]]


def test_every_story_file_is_admitted_by_a_story_ingress_row() -> None:
    """Every shipped story file is reachable at the edge; a deeper path is not.

    Matched with ``re.search``, cloudflared's own (unanchored) semantics — the same
    choice ``tests/deploy/test_published_profiles.py`` makes, so a row that lost an
    anchor could not pass here while leaking in production.
    """
    rows = _story_ingress_rows()
    entries = sorted(STORY_DIR.iterdir())
    subdirs = [p.name for p in entries if p.is_dir()]
    files = [p.name for p in entries if p.is_file()]
    admitted = [name for name in files if any(re.search(row, f"/story/{name}") for row in rows)]
    page_admitted = any(re.search(row, "/story/") for row in rows)
    control_admitted = sum(1 for row in rows if re.search(row, "/story/sub/x.js"))
    print(
        f"rows={rows} files={len(files)} admitted={len(admitted)} "
        f"page_admitted={page_admitted} control_admitted={control_admitted}"
    )
    assert len(rows) == 2, f"expected the two story rows, found {rows}"
    assert not subdirs, f"story/ must stay flat (the `[^/]+` row admits nothing deeper): {subdirs}"
    assert sorted(admitted) == sorted(files)
    assert page_admitted
    assert control_admitted == 0


# --------------------------------------------------------------------------- #
# AC-5 — no ruled-out literal in the authored story text
# --------------------------------------------------------------------------- #


def _ruled_out_literals(text: str) -> list[str]:
    return [literal for literal in _RULED_OUT_LITERALS if literal in text]


def test_story_text_carries_no_ruled_out_literal() -> None:
    """The intro-video rulings, as far as a string search can hold them (§3.6)."""
    texts = _authored_texts()
    combined = "\n".join(texts.values())
    found = _ruled_out_literals(combined)
    tiers = extract_block((STORY_DIR / "story-data.js").read_text(encoding="utf-8"))["rules"][
        "tiers"
    ]
    band_tiers = sum(1 for tier in tiers if tier["min_amount"] == 30001)
    band_numeral = len(re.findall(r"(?<!\d)30001(?!\d)", combined))
    ai_tokens = len(re.findall(r"\bAI\b", combined))
    print(
        f"ruled_out_found={found} band_numeral_in_text={band_numeral} band_tiers={band_tiers} "
        f"ai_tokens={ai_tokens} tamper_evident={combined.count('tamper-evident')}"
    )
    # The absence assertion runs FIRST, so a mutation that swaps tamper-evident for
    # immutable fails on the literal it introduced (PLAN-0126 probe P5c).
    assert not found, f"ruled-out literals on the page: {found}"
    assert band_numeral == band_tiers == 1, "the band numeral may appear only as its tier row"
    assert ai_tokens <= 1, "R3 — barely say AI"
    assert "tamper-evident" in combined


def test_the_literal_checker_flags_a_known_numeral() -> None:
    """Positive control: the same function finds a band numeral written for the screen."""
    flagged = _ruled_out_literals("ด่านอนุมัติเกิน ฿30,001 ไปที่เจ้าของกิจการ")
    print(f"flagged={flagged}")
    assert "฿30,001" in flagged


# --------------------------------------------------------------------------- #
# AC-6 — story references and story files are a bijection
# --------------------------------------------------------------------------- #


def _resolved_references() -> list[tuple[str, str, Path]]:
    out: list[tuple[str, str, Path]] = []
    for name in ("index.html", "story.js", "story.css"):
        for ref in references(name, authored_text(name)):
            out.append((name, ref, (STORY_DIR / ref.split("?", 1)[0]).resolve()))
    return out


def test_every_story_reference_resolves() -> None:
    """Forward: nothing the page loads is missing, and nothing escapes static/."""
    resolved = _resolved_references()
    dangling = [f"{owner} -> {ref}" for owner, ref, path in resolved if not path.is_file()]
    escaping = [
        f"{owner} -> {ref}"
        for owner, ref, path in resolved
        if STATIC_DIR.resolve() not in path.parents
    ]
    print(f"refs={len(resolved)} dangling={dangling} escaping={escaping}")
    assert dangling == []
    assert escaping == []


def test_every_story_file_is_referenced_or_exempt() -> None:
    """Reverse: every script and stylesheet in story/ is loaded, or exempt in writing."""
    referenced = {path for _, _, path in _resolved_references()}
    shipped = [p for p in sorted(STORY_DIR.iterdir()) if p.suffix in {".js", ".css"}]
    orphans = [
        p.name
        for p in shipped
        if p.resolve() not in referenced and p.name not in _UNREFERENCED_STORY_FILES
    ]
    stale = [
        name for name in _UNREFERENCED_STORY_FILES if (STORY_DIR / name).resolve() in referenced
    ]
    print(f"shipped_js_css={len(shipped)} orphans={orphans} stale_exemptions={stale}")
    assert orphans == []
    assert stale == []


def test_the_story_parse_is_not_vacuous() -> None:
    """Anti-vacuity for both directions: the parse found scripts AND styles to check."""
    resolved = _resolved_references()
    refs_js = sum(1 for _, _, path in resolved if path.suffix == ".js")
    refs_css = sum(1 for _, _, path in resolved if path.suffix == ".css")
    files = [p for p in STORY_DIR.iterdir() if p.is_file()]
    print(f"refs_js={refs_js} refs_css={refs_css} files={len(files)} vendored={VENDORED_FILES}")
    assert refs_js >= 1
    assert refs_css >= 1
    assert files


# --------------------------------------------------------------------------- #
# AC-7 — the console offers the link, in a new tab, and no tab was added
# --------------------------------------------------------------------------- #


def test_console_offers_the_story_link_in_a_new_tab() -> None:
    """An anchor to /story/ with target _blank and rel noopener — never a view key."""
    source = strip_js_comments(_APP_JS.read_text(encoding="utf-8"))
    anchors = [m.start() for m in re.finditer(r"href:\s*'/story/'", source)]
    assert len(anchors) == 1, f"expected one href: '/story/' in app.js, found {len(anchors)}"
    open_brace = source.rindex("{", 0, anchors[0])
    close_brace = source.index("}", anchors[0])
    attrs = source[open_brace : close_brace + 1]
    tag_call = source[max(0, open_brace - 12) : open_brace]
    gate = source[max(0, open_brace - 400) : open_brace]
    gated = bool(
        re.search(r"hasOwnProperty\.call\(VIEWS,\s*'I'\)", gate)
        and re.search(r"hasOwnProperty\.call\(VIEWS,\s*'H'\)", gate)
    )
    print(f"tag_call={tag_call.strip()!r} attrs={attrs!r} gated_on_I_and_H={gated}")
    assert re.search(r"h\(\s*'a'\s*,\s*$", tag_call), "the link must be an anchor element"
    assert re.search(r"target:\s*'_blank'", attrs)
    assert re.search(r"rel:\s*'noopener'", attrs)
    assert gated, "the link must be gated on the SERVER-DECLARED view set holding I and H"


def test_the_story_link_added_no_tab() -> None:
    """Control: the A-J census the header ladder was measured for is unchanged."""
    registered = _registered_view_keys()
    print(f"registered={sorted(registered)}")
    assert registered == MEASURED_TAB_CENSUS


def test_the_link_and_the_edge_agree_on_every_published_system() -> None:
    """Where the console offers the link (views I and H declared), the edge serves the page.

    And the reverse: a system that declares neither is not given an ingress row for a
    page nothing links to. Read from each profile's own ``published.env`` and
    ``cloudflared/config.yml``, so a future system that publishes I and H without the
    story rows reddens here instead of shipping a header link to a 404.
    """
    rows = []
    for profile in sorted((REPO_ROOT / "deploy" / "published").iterdir()):
        env_file = profile / "published.env"
        if not env_file.is_file():
            continue
        match = re.search(
            r"^UI_PUBLISHED_VIEWS=([A-Z,]*)\s*$", env_file.read_text(encoding="utf-8"), re.M
        )
        views = set(match.group(1).split(",")) if match else set()
        doc = yaml.safe_load((profile / "cloudflared" / "config.yml").read_text(encoding="utf-8"))
        admits = any(
            re.search(rule["path"], "/story/") for rule in doc["ingress"] if "path" in rule
        )
        rows.append((profile.name, sorted(views), {"I", "H"} <= views, admits))
    print(f"systems={rows}")
    assert any(
        links for _, _, links, _ in rows
    ), "no system declares I and H — the check read nothing"
    assert [row for row in rows if row[2] != row[3]] == []


# --------------------------------------------------------------------------- #
# AC-11 — every story reference is relative and stays inside story/ or assets/fonts/,
#         so the multi-file Artifact's files map is derivable from the files themselves
# --------------------------------------------------------------------------- #


def _non_relative_references(name: str, text: str) -> list[str]:
    """References the Artifact host cannot serve: a scheme, ``//``, or a leading ``/``."""
    external = set(external_references(name, text))
    return [ref for ref in references(name, text) if ref in external or ref.startswith("/")]


def test_every_story_reference_is_relative_and_in_bounds() -> None:
    """The page's own references name every file the multi-file Artifact must publish.

    The Artifact host serves no root-relative path (PLAN-0126 SD-5 = d, G32), so a
    ``/assets/...`` URL that works at ``/story/`` would 404 there. Each reference must
    also land in ``story/`` or ``assets/fonts/`` — the two places the files map
    publishes. The printed map is the Step 9 files map; the page and the licence
    travel with it by name.
    """
    texts = _authored_texts()
    story, fonts = STORY_DIR.resolve(), _FONTS_DIR.resolve()
    refs = [(name, ref) for name, text in texts.items() for ref in references(name, text)]
    not_relative = [
        f"{name} -> {ref}"
        for name, text in texts.items()
        for ref in _non_relative_references(name, text)
    ]
    files_map: dict[str, str] = {}
    out_of_bounds = []
    for name, ref in refs:
        path = (STORY_DIR / ref.split("?", 1)[0]).resolve()
        if not path.is_file() or path.parent not in (story, fonts):
            out_of_bounds.append(f"{name} -> {ref}")
            continue
        key = (
            path.name if path.parent == story else path.relative_to(STATIC_DIR.resolve()).as_posix()
        )
        files_map[key] = path.relative_to(REPO_ROOT.resolve()).as_posix()
    owners = sorted({name for name, _ in refs})
    print(
        f"refs={len(refs)} relative={len(refs) - len(not_relative)} "
        f"out_of_bounds={out_of_bounds} owners={owners} files_map={sorted(files_map)}"
    )
    assert not_relative == [], f"references the Artifact host cannot serve: {not_relative}"
    assert out_of_bounds == [], f"references outside story/ and assets/fonts/: {out_of_bounds}"
    assert set(owners) >= {"index.html", "story.js", "story.css"}, "the scan read no references"


def test_the_relative_checker_flags_a_root_relative_url() -> None:
    """Positive control: the checker AC-11 trusts does find a root-relative font URL."""
    flagged = _non_relative_references("story.css", _KNOWN_ROOT_RELATIVE_URL)
    print(f"flagged={flagged}")
    assert flagged == ["/assets/fonts/x.woff2"]
