"""UI contract for View G's fleet branch — PLAN-0098 AC-7 + AC-9.

There is no build step and no frontend test runner, so a CI tripwire for the UI must be
a Python test (``docs/conventions/ui.md:99-104``). These are lexical checks over the
shipped asset; they are deliberately the *weakest* thing that is still an oracle, and
each one states what it cannot prove.

Two ACs live here:

* **AC-7** — the fleet branch is actually present in ``view-hero.js``, and every asset
  this PLAN edited carries a bumped ``?v=`` token in ``index.html``. Without the bump a
  normal browser reload serves the stale file, so a reviewer would be looking at the old
  screen while believing they were looking at the new one.
* **AC-9** — the SD-3(c) narrative fence. Cray ruled that the owner's fraud origin story
  rides on the screen as narrative copy and **never as a rendered figure**. This module
  is the oracle for that hard edge: no money-shaped literal may appear anywhere inside
  the fleet branch, so every ฿ the screen shows must have flowed from the API payload
  through ``thb()``.

**Honest limits, stated rather than implied.** These are static lexical checks over
source text. They prove no money literal is baked into the fleet branch's *source*; they
cannot prove the rendered DOM shows only payload-derived numbers (a runtime computation
could still synthesise one), and they do not judge copy semantics. Scanning covers
comments as well as string literals — stricter than AC-9's wording, chosen because a
number "documented" in a comment is one copy-paste away from being rendered.

**Vacuity is the real risk here, not strictness.** A marker-delimited scan that silently
finds nothing passes for free, which is exactly how a probe reads GREEN while protecting
nothing (PLAN-0098 Step 6's discipline; two such probes were caught in session 196). So
the slice is asserted to be substantial *and* recognisably the fleet branch, and the
money regex is asserted to fire on a planted sample, before any absence is claimed.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.api.js_source import strip_js_comments

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STATIC = _REPO_ROOT / "services" / "api" / "static"
_VIEW_HERO = _STATIC / "assets" / "view-hero.js"
_INDEX_HTML = _STATIC / "index.html"

#: The sentinels that delimit the fleet branch. They are the AC-7 presence marker and
#: the AC-9 scan boundary at once — one marker, so the two cannot drift apart.
_START_MARKER = "FLEET-BRANCH-START"
_END_MARKER = "FLEET-BRANCH-END"

#: ``view-hero.js``'s cache-bust token on `main` immediately BEFORE this PLAN's Step 5
#: (``index.html:54``, PR #1002 and earlier). Asserting "not this value" rather than
#: pinning the new one keeps the test from false-REDding on every future legitimate bump
#: while still proving the Step 5 bump actually happened.
_PRE_PLAN_TOKEN = "c36"

#: Money-shaped literals. Bare digits are fine (`width: 14`, `slice(0, 3)`); what is
#: forbidden is a figure a reader would read as an amount.
_MONEY_LITERAL = re.compile(
    r"฿\s*[\d,]*\d"  # a ฿ sign adjacent to digits: ฿48000, ฿ 48,000
    r"|\d[\d,]*\s*(?:THB|บาท)"  # digits carrying a currency word: 48000 THB
    r"|\d{1,3}(?:,\d{3})+"  # a comma-grouped amount: 48,000
)

#: Fields only procurement's audit emits. Fleet's audit
#: (`verticals/fleet_maintenance/hero_demo/governance_audit.py`) emits none of them, so
#: reading one in the fleet branch renders the string "undefined" to a live audience.
#: The PLAN's own D-D asserted the donor joiner bound only shared fields; it did not.
_PROCUREMENT_ONLY_FIELDS = ("po_id", "declared_tier_id", "is_off_avl_override")


def _source() -> str:
    return _VIEW_HERO.read_text(encoding="utf-8")


def _fleet_branch(source: str) -> str:
    """The fleet branch slice, or a loud failure — never a silent empty string."""
    start = source.find(_START_MARKER)
    end = source.find(_END_MARKER)
    assert start != -1, (
        f"{_START_MARKER} is not in {_VIEW_HERO.name}. Every check in this module scans "
        "the slice between the two markers; without them there is nothing to scan and "
        "each absence assertion would pass for free."
    )
    assert end != -1, f"{_END_MARKER} is not in {_VIEW_HERO.name} (the slice never closes)."
    assert start < end, (
        f"{_END_MARKER} appears before {_START_MARKER} — the slice is inverted, so the "
        "scan would cover the procurement code instead of the fleet branch."
    )
    return source[start:end]


def _fleet_branch_code(branch: str) -> str:
    """The fleet branch with comment prose removed — what the browser actually executes.

    Two checks below are about what the code *reads*, not about what the file *says*, and
    prose that names a field in order to explain why it is NOT read must not read as
    reading it. (AC-9's money fence deliberately keeps scanning comments — a number
    documented in a comment is one copy-paste from being rendered.)

    The slice begins INSIDE the opening banner comment, because the start marker lives in
    it — so the banner is dropped up to its closing delimiter before the ordinary strip.

    The strip itself is ``tests.api.js_source``, shared with the two other modules that
    scan these assets. This function used to carry its own copy, which removed block
    comments before line comments — the reverse of how JavaScript tokenises, so a ``/*``
    written inside a ``//`` comment opened a phantom block that swallowed everything down
    to the next ``*/``. ``view-hero.js`` is the file this module scans and it does carry a
    ``/*`` inside a string literal (line 678, the ``/demo/hero/*`` route glob), so this
    was one badly-placed comment away from the absence checks below going vacuous.
    Comments are blanked character-for-character rather than removed outright: collapsing
    them would glue the surrounding lines into tokens present in neither.
    """
    banner_end = branch.find("*/")
    body = branch[banner_end + 2 :] if banner_end != -1 else branch
    return strip_js_comments(body)


@pytest.fixture(scope="module")
def fleet_branch() -> str:
    return _fleet_branch(_source())


@pytest.fixture(scope="module")
def fleet_code(fleet_branch: str) -> str:
    return _fleet_branch_code(fleet_branch)


# --------------------------------------------------------------------------- #
# Vacuity guards — these run BEFORE any absence is claimed.
# --------------------------------------------------------------------------- #


def test_the_extracted_fleet_branch_is_substantial_and_recognisable(fleet_branch: str) -> None:
    """The slice is really the fleet branch — not an empty or truncated read.

    This is the guard that makes every "contains no X" assertion below mean something. A
    marker pair that matched an empty region would let the AC-9 fence pass while fencing
    nothing at all.
    """
    assert len(fleet_branch) > 2000, (
        f"the fleet branch slice is only {len(fleet_branch)} chars — too small to be the "
        "branch this module exists to check. Either the markers moved or the branch was "
        "gutted; in both cases the absence checks below would be vacuous."
    )
    for token in ("fleetMoment", "renderFleet", "fleet_maintenance", "three_quote"):
        assert token in fleet_branch, (
            f"the extracted slice does not mention {token!r}, so it is probably not the "
            "fleet branch. Refusing to certify an absence over the wrong text."
        )


def test_the_comment_stripped_fleet_code_is_still_substantial(fleet_branch: str) -> None:
    """The same guard for the CODE region — the two checks below scan it, not the prose.

    An over-eager comment strip that ate the function bodies would leave those checks
    asserting an absence over an empty string, which passes for exactly the wrong reason.
    """
    code = _fleet_branch_code(fleet_branch)
    assert len(code) > 1500, (
        f"the comment-stripped fleet code is only {len(code)} chars — the strip removed "
        "far more than comments, so any absence asserted over it would be vacuous."
    )
    for token in ("function fleetMoment", "function renderFleet", "renderFleetAssumptions"):
        assert token in code, f"comment-stripping removed {token!r} from the fleet code"


def test_the_money_regex_fires_on_a_planted_literal() -> None:
    """The AC-9 fence's own oracle: prove the pattern matches before trusting a no-match.

    A regex that silently matches nothing would let a real ฿ literal through while this
    module reported GREEN — the exact shape of the two defective probes caught in
    session 196.
    """
    for planted in ("฿100,000", "฿48000", "48,000", "40800 THB", "฿ 7,200"):
        assert _MONEY_LITERAL.search(planted), f"the money regex failed to match {planted!r}"
    for benign in ("width: 14", "slice(0, 3)", "PLAN-0098", "2026-07-31", "฿-impact"):
        assert not _MONEY_LITERAL.search(benign), (
            f"the money regex matched {benign!r}, which is not a money literal — an "
            "over-broad fence would force real code to be written around the test"
        )


# --------------------------------------------------------------------------- #
# AC-7 — the presence tripwire + the cache-bust.
# --------------------------------------------------------------------------- #


def test_the_fleet_branch_marker_is_present_in_view_hero() -> None:
    """AC-7a. The branch exists in the shipped asset, not only in the PLAN."""
    source = _source()
    assert _START_MARKER in source and _END_MARKER in source
    assert "vertical === 'fleet_maintenance'" in source, (
        "the fleet branch is present but nothing dispatches to it. The discriminant read "
        "is what makes a fleet boot render fleet's screen instead of procurement's."
    )


def test_view_hero_carries_a_bumped_cache_token(fleet_branch: str) -> None:
    """AC-7b. `view-hero.js` was edited by this PLAN, so its ?v= token must have moved.

    Not pinned to a specific new value on purpose: pinning would turn every future
    legitimate bump into a false RED, and the property worth protecting is "it changed
    when the asset changed", not "it equals c46".
    """
    html = _INDEX_HTML.read_text(encoding="utf-8")
    match = re.search(r"assets/view-hero\.js\?v=([A-Za-z0-9._-]+)", html)
    assert match is not None, (
        "index.html no longer references assets/view-hero.js with a ?v= token — the "
        "cache-bust convention (docs/conventions/ui.md:106-110) is what makes a normal "
        "reload pick up an asset edit."
    )
    assert match.group(1) != _PRE_PLAN_TOKEN, (
        f"view-hero.js still carries ?v={_PRE_PLAN_TOKEN}, the token it had before "
        "PLAN-0098 Step 5 edited it. A reviewer reloading the demo would be served the "
        "pre-fleet-branch file and would report on a screen this PLAN did not build."
    )


# --------------------------------------------------------------------------- #
# AC-9 — the SD-3(c) narrative fence.
# --------------------------------------------------------------------------- #


def test_the_fleet_branch_carries_no_hardcoded_money_literal(fleet_branch: str) -> None:
    """AC-9. Every ฿ the fleet screen renders must come from the payload.

    SD-3(c) (Cray, 2026-07-31) put the owner's fraud origin story on the screen as
    narrative copy. A story about money, rendered next to real figures, is exactly where
    an invented number would be believed — so the fence is lexical and absolute rather
    than a matter of authoring care.
    """
    hits = sorted({m.group(0) for m in _MONEY_LITERAL.finditer(fleet_branch)})
    assert not hits, (
        f"money-shaped literal(s) in the fleet branch: {hits}\n\n"
        "Every ฿ figure on View G's fleet screen must flow from the /demo/hero/impact "
        "payload through thb(). A literal here is a number the API never supplied, "
        "rendered beside numbers it did — which is the reading SD-3(c) exists to "
        "prevent. Render the payload field instead."
    )


def test_the_origin_story_carries_no_numeral(fleet_branch: str) -> None:
    """AC-9's specific case: the Thai origin story is prose, and prose has no digits.

    'เป็นแสน' is a Thai word for the magnitude, not a figure — which is precisely why the
    story can be told without asserting an amount the partner never gave us.
    """
    assert (
        "เคยโดนช่างโกงอะไหล่ไปเป็นแสน" in fleet_branch
    ), "the origin story SD-3(c) ruled onto the screen is not in the fleet branch"
    story_line = next(
        line for line in fleet_branch.splitlines() if "เคยโดนช่างโกงอะไหล่ไปเป็นแสน" in line
    )
    assert not re.search(r"\d", story_line), (
        f"the origin-story line carries a numeral: {story_line.strip()!r}. SD-3(c) rules "
        "the story is narrative copy only — a figure beside it reads as the loss amount."
    )


# --------------------------------------------------------------------------- #
# SD-2 — a typed Cray ruling that otherwise has no oracle at all.
# --------------------------------------------------------------------------- #


def test_the_fleet_assumptions_strip_is_not_hidden_behind_a_toggle(fleet_code: str) -> None:
    """SD-2 (Cray, 2026-07-31): always-visible. Pinned lexically; NOT an AC.

    The donor hides its provenance detail until a button is pressed
    (``view-hero.js:179-193``). Cray ruled that placement wrong for fleet: procurement's
    ledger figures are CSV columns and only the *facet* is provenance, whereas fleet's
    entire governed delta is assumption-derived — so hiding the assumption hides what
    kind of number the reader is looking at. Nothing else in the suite would notice the
    strip quietly acquiring a toggle, which is the only reason this check exists.
    """
    assert "renderFleetAssumptions" in fleet_code
    assert "show provenance" not in fleet_code, (
        "the fleet assumptions strip grew the donor's provenance toggle. SD-2 ruled it "
        "always-visible: fleet's whole ฿ delta is modelled, so the assumptions are not "
        "an optional detail, they are what qualifies the figure."
    )
    assert ".hidden" not in fleet_code, (
        "something in the fleet branch sets .hidden. SD-2 requires the assumptions to "
        "render unconditionally; a hidden default is the ruling reversed."
    )


# --------------------------------------------------------------------------- #
# The regression this branch was one reused function away from shipping.
# --------------------------------------------------------------------------- #


def test_the_fleet_branch_reads_no_procurement_only_field(fleet_code: str) -> None:
    """The fleet audit emits none of these; reading one renders 'undefined' to a room.

    PLAN-0098 §D-D states the donor joiner "binds only doa_tier / sod / governed_decision,
    all of which fleet produces". Measured against `view-hero.js:42,46,49` that is not so,
    and reusing it verbatim would have printed 'undefined — display only' in the DOA card
    and 'Contrast · undefined' in the contrast line. This pins the correction so a later
    simplification cannot quietly undo it.
    """
    leaked = [field for field in _PROCUREMENT_ONLY_FIELDS if field in fleet_code]
    assert not leaked, (
        f"the fleet branch reads procurement-only audit field(s): {leaked}. Fleet's "
        "governance_audit.py emits event_id / truck_id / case_id / site_id / severity / "
        "amount / doa_tier / governed_kind / governed_decision / sod / three_quote and "
        "nothing else, so each of these resolves to undefined at render time."
    )
