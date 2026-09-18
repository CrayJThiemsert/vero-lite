"""The diff-aware cache-bust gate, driven to BOTH verdicts on BOTH surfaces.

The guard this replaces (``test_every_edited_asset_got_a_cache_bust``) asserted
per-file token *floors* over 9 of 21 JS files and 0 of 4 CSS files. It passed, and it
would have kept passing with the property it existed to protect broken — editing
``views.css`` without bumping its token was outside its reach. So the first test here
is that exact shape, and it must be RED-able: if PR #1190's mistake cannot fail this
module, the replacement inherits the defect it was written to remove.

s310 found the same defect one level up. The check's *scope* was hard-coded to a single
pair, so when the story page shipped at ``static/story/`` with its own ``index.html``
it was simply outside the gate: a measured s309 run over a PR that changed ``story.js``
and ``story-data.js`` printed ``0 bumped, 0 unversioned, 0 stale``. The second block of
tests is that shape, and the scope itself is now locked against a committed list — a
page added tomorrow either enters the gate or reddens
:func:`test_discovered_surfaces_match_the_committed_expectation`, and cannot quietly do
neither.

``check`` is pure, so every case below drives it with literal inputs and no git. The
last block is deliberately not synthetic: it reads the **shipped** pages and asserts
every reference resolves to a file that exists on disk, so the resolution this module
asserts is the one the repo actually serves rather than one this file invented and then
agreed with.
"""

from __future__ import annotations

from pathlib import Path

from tools.ci.cache_bust_diff_check import (
    STATIC_ROOT,
    Findings,
    check,
    discover_indexes,
    references,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]

_CONSOLE = "services/api/static/index.html"
_STORY = "services/api/static/story/index.html"

#: The committed scope (Cray's s310 ruling: discover, then lock). Widening the gate is
#: allowed — silently widening or narrowing it is not.
_EXPECTED_SURFACES = [_CONSOLE, _STORY]

_VIEWS_CSS = "services/api/static/assets/views.css"
_FAVICON = "services/api/static/assets/favicon.svg"
_CONSOLE_STORY_CSS = "services/api/static/assets/story.css"
_STORY_CSS = "services/api/static/story/story.css"
_STORY_JS = "services/api/static/story/story.js"
_STORY_DATA_JS = "services/api/static/story/story-data.js"
_THREE_JS = "services/api/static/story/three.module.min.js"
_FONT = "services/api/static/assets/fonts/IBMPlexSans-Regular.woff2"

# The comment line is kept in the fixture on purpose: it carries both `assets/*` and a
# bare `?v=`, the shape that would mint a phantom reference under a looser href class.
_CONSOLE_OLD = """
  <!-- Asset cache-busting: bump the ?v= token on ANY assets/* edit so a NORMAL
       browser reload picks up the change. The cached ?v=<token> URL is reused. -->
  <link rel="stylesheet" href="assets/views.css?v=c43" />
  <link rel="stylesheet" href="assets/story.css?v=c25" />
  <script src="assets/api.js?v=c48"></script>
"""

_CONSOLE_UNBUMPED = _CONSOLE_OLD

_CONSOLE_BUMPED = _CONSOLE_OLD.replace("views.css?v=c43", "views.css?v=c44")

# Bare hrefs, exactly as the shipped story page writes them — this is the layout the
# single-pair predecessor could not express.
_STORY_OLD = """
  <link rel="stylesheet" href="story.css?v=c1" />
  <script src="story-data.js?v=c1"></script>
  <script type="module" src="story.js?v=c1"></script>
"""

_STORY_UNBUMPED = _STORY_OLD

_STORY_BUMPED = _STORY_OLD.replace("story.js?v=c1", "story.js?v=c2")


def _revisions(
    console_new: str = _CONSOLE_BUMPED,
    story_new: str = _STORY_BUMPED,
) -> dict[str, tuple[str, str]]:
    """Both surfaces, each as ``(old, new)``. Defaults are the quiet, all-bumped state."""
    return {_CONSOLE: (_CONSOLE_OLD, console_new), _STORY: (_STORY_OLD, story_new)}


# --------------------------------------------------------------------------------
# The console shape the predecessor was written for (PLAN-0107 AC-14) — regression.
# --------------------------------------------------------------------------------


def test_pr_1190_shape_is_red() -> None:
    """THE case the retired guard could not see: CSS edited, token left alone.

    PR #1190 bumped ``views.css`` c43→c44 by hand precisely because nothing checked
    it. This asserts the check still fails when that hand-bump is forgotten.
    """
    findings = check([_VIEWS_CSS], _revisions(console_new=_CONSOLE_UNBUMPED))

    assert findings.stale == [f"{_VIEWS_CSS} (still ?v=c43)"], (
        "a changed asset whose token did not move must be STALE — if this passes, "
        "the replacement has the same blind spot as the guard it retired"
    )
    assert findings.bumped == []
    assert findings.unversioned == []


def test_the_same_console_edit_with_the_bump_is_green() -> None:
    """The positive control for the test above — identical but for the token.

    Without it, `stale == [...]` could be produced by a check that flags every
    changed asset, which would be red for the wrong reason and unusable in CI.
    """
    findings = check([_VIEWS_CSS], _revisions())

    assert findings.stale == []
    assert findings.bumped == [_VIEWS_CSS]


# --------------------------------------------------------------------------------
# The story shape the SCOPE could not see (s309) — the reason this module changed.
# --------------------------------------------------------------------------------


def test_s309_story_shape_is_red() -> None:
    """A changed story asset behind an unchanged token, the measured s309 blind spot.

    On branch ``fix/story-v2a`` (e0d1d041) this exact edit printed
    ``CACHE_BUST: OK — 0 bumped, 0 unversioned, 0 stale``: the page was outside the
    gate's hard-coded pair, so the guard was serene about an asset it never looked at.
    """
    findings = check([_STORY_JS], _revisions(story_new=_STORY_UNBUMPED))

    assert findings.stale == [f"{_STORY_JS} (still ?v=c1)"], (
        "a changed STORY asset whose token did not move must be STALE — if this "
        f"passes, /story/ is still outside the gate; got {findings.stale}"
    )
    assert findings.bumped == []


def test_the_same_story_edit_with_the_bump_is_green() -> None:
    """Positive control for the story surface: same edit, token moved c1→c2."""
    findings = check([_STORY_JS], _revisions())

    assert findings.stale == []
    assert findings.bumped == [_STORY_JS]


def test_a_story_asset_resolves_against_its_own_page_not_the_console() -> None:
    """``story.css`` exists TWICE, and keying on the filename reads the wrong one.

    ``static/assets/story.css`` is the console's story view at ``?v=c25``;
    ``static/story/story.css`` is the story page's at ``?v=c1``. A check that keys
    references by basename resolves the story page's file against the console's token
    — and then reports nothing at all, because the changed path matches no key. The
    token named in the message is what distinguishes the two: c1 is the story page's.
    """
    findings = check([_STORY_CSS], _revisions(story_new=_STORY_UNBUMPED))

    assert findings.stale == [f"{_STORY_CSS} (still ?v=c1)"], (
        "the story page's story.css must resolve to ITS OWN ?v=c1, not the console's "
        f"?v=c25, and must not vanish; got {findings.stale}"
    )
    assert _CONSOLE_STORY_CSS not in findings.bumped + findings.unversioned, (
        "the console's story.css was never changed — if it appears, the two files "
        "are being conflated in the other direction"
    )


def test_the_two_shipped_surfaces_version_disjoint_assets() -> None:
    """``check`` merges the surfaces' reference maps, and first-sorted-index wins.

    That is only safe while no asset is versioned by two pages. It is not today, and
    this locks it: if a shared asset ever appears, the merge silently picks one token
    and this reddens first.
    """
    maps = {
        index_path: set(
            references(index_path, (_REPO_ROOT / index_path).read_text(encoding="utf-8"))
        )
        for index_path in discover_indexes(_REPO_ROOT)
    }
    console, story = maps[_CONSOLE], maps[_STORY]

    assert (
        console & story == set()
    ), f"{len(console & story)} asset(s) versioned by BOTH pages: {sorted(console & story)}"


# --------------------------------------------------------------------------------
# Reported-not-failed, and the things that must stay silent.
# --------------------------------------------------------------------------------


def test_an_asset_with_no_version_reference_is_reported_not_failed() -> None:
    """``favicon.svg`` ships without a ``?v=`` tag — referenced by convention.

    Treating "absent from the HTML" as a failure would redden CI on a favicon edit
    with no fix available, so it is a distinct, reported outcome.
    """
    findings = check([_FAVICON], _revisions())

    assert findings.unversioned == [_FAVICON]
    assert findings.stale == [], "an unversioned asset is not a stale one"


def test_an_unversioned_story_asset_is_reported_not_failed() -> None:
    """``three.module.min.js`` sits in a versioned dir but carries no token.

    It is imported by ``story.js`` rather than referenced from the page, so there is
    no token to bump — the favicon precedent, one directory over. Reported, not failed.
    """
    findings = check([_THREE_JS], _revisions())

    assert findings.unversioned == [_THREE_JS]
    assert findings.stale == []


def test_nested_asset_dirs_stay_silent() -> None:
    """``assets/fonts/`` versions nothing, so a font edit is not the gate's business.

    Reporting it would be noise on every webfont bump with no available fix, and the
    predecessor was silent here too — this pins that the widened scope did not widen
    into the nested directories.
    """
    findings = check([_FONT], _revisions())

    assert findings == Findings(), f"a nested-dir change must produce nothing; got {findings}"


def test_an_index_html_is_not_itself_a_versioned_asset() -> None:
    """The story index lives INSIDE the directory it versions — it is not an asset.

    Without the exclusion, every story-page edit would report its own ``index.html``
    as unversioned, which is noise attached to the most common story change there is.
    """
    findings = check([_STORY, _CONSOLE], _revisions())

    assert findings == Findings(), f"the versioning surfaces are not versioned; got {findings}"


def test_non_asset_changes_are_ignored() -> None:
    """A Python edit in the same PR must not be dragged into the asset verdict."""
    findings = check(["services/api/routers/runs.py", "docs/STATUS.md"], _revisions())

    assert findings == Findings(), "nothing outside a versioned directory is checked"


def test_a_brand_new_asset_counts_as_bumped() -> None:
    """First token = first bump. Absent from the old HTML, present in the new."""
    new = _CONSOLE_BUMPED + '  <script src="assets/view-brand-new.js?v=c1"></script>\n'

    findings = check(["services/api/static/assets/view-brand-new.js"], _revisions(console_new=new))

    assert findings.bumped == ["services/api/static/assets/view-brand-new.js"]
    assert findings.stale == []


def test_a_surface_added_in_this_pr_counts_as_all_bumped() -> None:
    """A page with no old revision: ``git show base:`` is empty, not an error.

    Every reference is then a first bump. Erroring instead would make the gate refuse
    the very PR that adds a page — which is when it first has something to say.
    """
    findings = check([_STORY_JS], {_STORY: ("", _STORY_OLD)})

    assert findings.bumped == [_STORY_JS]
    assert findings.stale == []


# --------------------------------------------------------------------------------
# Scope: discovered, then locked against a committed list (Cray's s310 ruling).
# --------------------------------------------------------------------------------


def test_discovered_surfaces_match_the_committed_expectation() -> None:
    """The gate finds its own surfaces — and may not change scope without a diff.

    Discovery is what stops the next page repeating /story/'s three unguarded months.
    This assertion is the other half: a page entering or leaving the gate reddens here,
    so the scope change arrives as a reviewable line rather than as silence.
    """
    found = discover_indexes(_REPO_ROOT)

    assert found == _EXPECTED_SURFACES, (
        f"cache-bust scope moved: found {found}, committed {_EXPECTED_SURFACES}. "
        "If a page was added, add it here; if one was removed, remove it here."
    )


def test_an_empty_tree_discovers_no_surfaces() -> None:
    """The positive control for discovery: it finds pages because they are there.

    Without this, ``found == _EXPECTED_SURFACES`` above could be satisfied by a walk
    that returns a hard-coded list, which is the very thing s310 removed.
    """
    assert discover_indexes(Path("/nonexistent-repo-root-for-this-test")) == []


# --------------------------------------------------------------------------------
# The shipped pages, not a fixture this module wrote and then agreed with.
# --------------------------------------------------------------------------------


def test_every_shipped_reference_resolves_to_a_file_that_exists() -> None:
    """Read the real artifacts and check the resolution against the filesystem.

    A parser validated only against its own synthetic HTML is green by construction.
    This asserts that every versioned reference the shipped pages serve resolves to a
    path that is actually there — so a broken join (basename-only, or joined against
    the wrong directory) reddens here instead of silently disarming the gate, and so
    does a reference to a file someone deleted.
    """
    resolved: dict[str, str] = {}
    for index_path in discover_indexes(_REPO_ROOT):
        html = (_REPO_ROOT / index_path).read_text(encoding="utf-8")
        refs = references(index_path, html)
        assert refs, f"{index_path} versions nothing — the gate would be silent for it"
        resolved.update(dict.fromkeys(refs, index_path))

    assert len(resolved) >= 25, (
        f"expected the shipped pages to version ~28 assets, found {len(resolved)} — "
        "either the pages changed shape or the reference regex no longer matches them"
    )
    missing = sorted(path for path in resolved if not (_REPO_ROOT / path).is_file())
    assert missing == [], f"reference(s) resolve to nothing on disk: {missing}"


def test_the_shipped_story_page_is_in_scope_and_versions_its_three_assets() -> None:
    """The concrete end state of s310, asserted against the page as shipped.

    Named separately from the aggregate above because "28 references exist somewhere"
    is satisfied by the console alone — the count cannot tell whether /story/ is in.
    """
    html = (_REPO_ROOT / _STORY).read_text(encoding="utf-8")
    resolved = set(references(_STORY, html))

    assert resolved == {
        _STORY_CSS,
        _STORY_DATA_JS,
        _STORY_JS,
    }, f"the story page's versioned set is not what the gate resolves: {sorted(resolved)}"


def test_the_static_root_is_where_the_pages_actually_are() -> None:
    """A mistyped STATIC_ROOT discovers nothing, and nothing-found is silent by nature."""
    assert (_REPO_ROOT / STATIC_ROOT).is_dir(), f"{STATIC_ROOT} is not a directory"
