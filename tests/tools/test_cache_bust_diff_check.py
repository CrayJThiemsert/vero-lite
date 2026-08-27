"""The diff-aware cache-bust gate, driven to BOTH verdicts (PLAN-0107 AC-14).

The guard this replaces (``test_every_edited_asset_got_a_cache_bust``) asserted
per-file token *floors* over 9 of 21 JS files and 0 of 4 CSS files. It passed, and it
would have kept passing with the property it existed to protect broken — editing
``views.css`` without bumping its token was outside its reach. So the first test here
is that exact shape, and it must be RED-able: if PR #1190's mistake cannot fail this
module, the replacement inherits the defect it was written to remove.

``check`` is pure, so every case below drives it with literal inputs and no git. The
last test is deliberately not synthetic: it reads the **shipped** ``index.html``, so
the token grammar this module asserts is the grammar the repo actually serves rather
than one this file invented and then agreed with.
"""

from __future__ import annotations

import re
from pathlib import Path

from tools.ci.cache_bust_diff_check import ASSET_PREFIX, INDEX_PATH, check, token_for

_REPO_ROOT = Path(__file__).resolve().parents[2]

_OLD = """
  <link rel="stylesheet" href="assets/views.css?v=c43" />
  <script src="assets/api.js?v=c48"></script>
"""

_NEW_UNBUMPED = """
  <link rel="stylesheet" href="assets/views.css?v=c43" />
  <script src="assets/api.js?v=c48"></script>
"""

_NEW_BUMPED = """
  <link rel="stylesheet" href="assets/views.css?v=c44" />
  <script src="assets/api.js?v=c48"></script>
"""


def _changed(*names: str) -> list[str]:
    return [f"{ASSET_PREFIX}{n}" for n in names]


def test_pr_1190_shape_is_red() -> None:
    """THE case the retired guard could not see: CSS edited, token left alone.

    PR #1190 bumped ``views.css`` c43→c44 by hand precisely because nothing checked
    it. This asserts the check now fails when that hand-bump is forgotten.
    """
    findings = check(_changed("views.css"), _OLD, _NEW_UNBUMPED)

    assert findings.stale == ["views.css (still ?v=c43)"], (
        "a changed asset whose token did not move must be STALE — if this passes, "
        "the replacement has the same blind spot as the guard it retired"
    )
    assert findings.bumped == []
    assert findings.unversioned == []


def test_the_same_edit_with_the_bump_is_green() -> None:
    """The positive control for the test above — identical but for the token.

    Without it, `stale == [...]` could be produced by a check that flags every
    changed asset, which would be red for the wrong reason and unusable in CI.
    """
    findings = check(_changed("views.css"), _OLD, _NEW_BUMPED)

    assert findings.stale == []
    assert findings.bumped == ["views.css"]


def test_an_asset_with_no_version_reference_is_reported_not_failed() -> None:
    """``favicon.svg`` ships without a ``?v=`` tag — measured, 26 on disk / 25 versioned.

    Treating "absent from the HTML" as a failure would redden CI on a favicon edit
    with no fix available, so it is a distinct, reported outcome.
    """
    findings = check(_changed("favicon.svg"), _OLD, _NEW_BUMPED)

    assert findings.unversioned == ["favicon.svg"]
    assert findings.stale == [], "an unversioned asset is not a stale one"


def test_a_brand_new_asset_counts_as_bumped() -> None:
    """First token = first bump. Absent from the old HTML, present in the new."""
    new = _NEW_BUMPED + '  <script src="assets/view-brand-new.js?v=c1"></script>\n'

    findings = check(_changed("view-brand-new.js"), _OLD, new)

    assert findings.bumped == ["view-brand-new.js"]
    assert findings.stale == []


def test_non_asset_changes_are_ignored() -> None:
    """A Python edit in the same PR must not be dragged into the asset verdict."""
    findings = check(
        ["services/api/routers/runs.py", "docs/STATUS.md", INDEX_PATH],
        _OLD,
        _NEW_UNBUMPED,
    )

    assert findings == type(findings)(), "nothing outside the assets prefix is checked"


def test_the_token_grammar_matches_the_shipped_index_html() -> None:
    """Read the real artifact, not a fixture this module wrote and then agreed with.

    A parser validated only against its own synthetic HTML is green by construction.
    This asserts that every versioned reference the shipped page actually serves is
    one ``token_for`` can resolve — so a future change to the reference form (a new
    tag, a moved query string) reddens here instead of silently disarming the gate.
    """
    html = (_REPO_ROOT / INDEX_PATH).read_text(encoding="utf-8")
    # Same character class the tool uses, deliberately: a looser one (`[^"'?]+`)
    # spans newlines and swallows the explanatory comment at :23-27, which itself
    # contains both `assets/*` and `?v=`. That is a fixture bug, not a tool bug —
    # `token_for` anchors on a concrete filename and cannot over-match this way.
    referenced = re.findall(r"assets/([A-Za-z0-9._-]+)\?v=", html)

    assert len(referenced) >= 20, (
        f"expected the shipped page to version ~25 assets, found {len(referenced)} — "
        "either the page changed shape or this regex no longer matches it"
    )
    unresolved = [name for name in referenced if token_for(html, name) is None]
    assert unresolved == [], f"token_for cannot read its own repo's references: {unresolved}"
