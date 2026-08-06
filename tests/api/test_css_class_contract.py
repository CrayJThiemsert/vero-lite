"""Every CSS class any front-end asset applies is defined somewhere that styles it.

The motivating bug is recorded in ``test_export_cover_ui_contract.py``: the first
Month-End KPI view used ``.hero-sub``, which existed in no stylesheet. The element
inherited ``white-space: nowrap`` from an ancestor with nothing to override it and
rendered as ONE unwrapped line — measured at 1121px inside a 980px column, pushing
the whole document into horizontal scroll. Nothing errored; the console was clean.

That guard was scoped to a single asset (``view-export.js``) because that is the
view the bug appeared in. This module is the widening: **every** ``assets/*.js``
file, discovered by glob rather than by a hand-kept list, so a new view is covered
the day it lands instead of the day someone remembers to add it.

Why a Python test and not a linter: ``docs/conventions/ui.md`` §5 — "There is **no
build step**: edit ``services/api/static/`` directly — no ``package.json``, no
bundler, no JS/CSS linter, no frontend test runner … A CI tripwire for the UI must
therefore be a **Python test**."

Scope + limits, stated honestly:

* This is a **name-existence** guard, not a rendering test. It proves a class has
  a rule somewhere; it cannot prove the rule is correct, that the selector's
  specificity wins, or that the element is visible. Rendering is verified in the
  browser preview — evidence, not the gate.
* It reads only single-quoted literals. Verified at authoring time: the repo uses
  the single-quote form exclusively (no ``class="…"``, no template-literal class
  attributes), and ``test_the_codebase_still_uses_only_single_quoted_classes``
  keeps that assumption from rotting silently.
* A class assembled entirely at runtime (``'urg-' + level``) is invisible to any
  static scan. The trailing-hyphen rule below drops those prefixes rather than
  reporting them as undefined, which means such classes are **unguarded** — a
  real hole, named here rather than hidden.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from tests.api.js_source import strip_js_comments

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STATIC = _REPO_ROOT / "services" / "api" / "static"
_ASSETS = _STATIC / "assets"
_INDEX_HTML = _STATIC / "index.html"

# --------------------------------------------------------------------------- #
# Where class names are APPLIED to an element.
# --------------------------------------------------------------------------- #
#: ``h('div', { class: 'a b' })`` — the repo's dominant form.
_CLASS_PROP = r"class:\s*'([^']*)'"
#: ``el.className = 'a b'`` and ``el.className += ' c'``.
_CLASS_NAME = r"className\s*\+?=\s*'([^']*)'"
#: ``el.setAttribute('class', 'a b')`` — the SVG path, which has no className.
_SET_ATTR = r"setAttribute\(\s*'class'\s*,\s*'([^']*)'"
#: ``classList.add('a', 'b')`` / ``.remove(…)`` — variadic; every arg is a token.
_CLASS_LIST_VARIADIC = r"classList\.(?:add|remove)\(([^)]*)\)"
#: ``classList.toggle(token, force)`` — ONLY the first argument is a class name.
#: The second is a boolean. Scanning the whole argument list reported `matrix`
#: and `swap` as undefined classes, because ``view-story.js:1222`` reads
#: ``classList.toggle('mode-matrix', m === 'matrix')``. Two phantom entries in a
#: debt list is how an allowlist starts rotting.
_CLASS_LIST_TOGGLE = r"classList\.toggle\(\s*'([^']*)'"
#: ``return 's-warn'`` — a status-class factory. The name never appears in a
#: ``class:`` position in its own file; a caller concatenates it. Three assets do
#: this (``api.js``, ``view-export.js``, ``view-procedures.js``), and ``api.js``
#: applies no classes at all, so without this pattern its whole status vocabulary
#: is invisible to the scan. Restricted to the ``s-`` prefix — the repo's semantic
#: status vocabulary — because an unrestricted ``return '<string>'`` would sweep
#: in every non-class string a function returns.
_RETURNED_STATUS_CLASS = r"return\s+'(s-[a-z][\w-]*)'"

# --------------------------------------------------------------------------- #
# Where class names are READ back as a lookup key rather than styled.
# --------------------------------------------------------------------------- #
_SELECTOR = r"(?:querySelector(?:All)?|closest|matches)\(\s*'[^']*?\.([\w-]+)"
_BY_CLASS_NAME = r"getElementsByClassName\(\s*'([\w-]+)'"


# --------------------------------------------------------------------------- #
# The allowlist, in TWO categories — ruled by Cray when this guard was widened.
#
# The split is not cosmetic: the two categories have opposite trajectories. A
# lookup hook is permanent and healthy — it will never have a CSS rule and does
# not want one. Inert debt should trend to zero. Flattening them into one set
# makes a stable allowlist indistinguishable from a rotting one, which is
# exactly the reading a future session needs to make.
#
# `test_the_allowlist_is_exactly_the_undefined_set` asserts SET EQUALITY against
# what the scan finds, in both directions: the list cannot silently absorb a new
# undefined class, and cannot keep an entry after the debt is paid.
# --------------------------------------------------------------------------- #

#: Applied AND read back through a selector — a lookup key, not a style target.
#: Verified: each appears in a ``querySelector``/``closest`` call in the same
#: view that applies it. These are correct as they are; they are not debt.
_JS_HOOK_CLASSES: frozenset[str] = frozenset(
    {
        "inbox-txt",  # view-story.js:568 reads it back to retarget the inbox line
        "pill-txt",  # view-story.js:808 rewrites the pill's text node in place
        "strip-msg",  # app.js:38 updates the global status strip's message
        "task-chip",  # view-story.js:690 re-reads the chip to restamp its state
    }
)

#: Pre-existing INERT classes: applied to an element, defined by no stylesheet
#: (linked or injected), and read back by no selector. Measured — not assumed:
#: the CSS was searched for ``[class*=…]`` attribute selectors (none exist) and
#: the JS for runtime-assembled selector strings (none exist), so nothing can be
#: styling or reading these through a path the scan cannot see.
#:
#: "Inert" here means precisely one thing — NO CSS RULE DEFINES THIS NAME. It does
#: not mean the element is unstyled, and the difference was measured, not assumed:
#: three of these sit on elements that carry a full inline ``style:`` object, so
#: the panel renders correctly and the class is a semantic marker. Adding a
#: stylesheet rule for those would introduce a second source of truth competing
#: with the inline style, which is a regression, not a fix. The comments below
#: record which is which so the next reader does not "pay down" the wrong ones.
#:
#: The rest are genuinely bare, and the three state toggles are the likeliest
#: real defects: ``view-story.js`` flips them on the view root as a step counter
#: advances, and no rule anywhere reacts, so the state change is invisible.
#:
#: This list exists so that population is countable for the first time. Paying it
#: down is a separate pass, and this set should shrink.
_INERT_CLASSES: frozenset[str] = frozenset(
    {
        # --- styled INLINE; the class is a semantic marker, not a defect. ---
        # Do not "fix" these by adding a rule — see view-monitor.js:284-299.
        "mon-advisory",  # view-monitor.js:285 — inline border/radius/padding
        "mon-advisory-top",  # view-monitor.js:289 — inline flex row
        "mon-advisory-reasons",  # view-monitor.js:296 — inline list spacing
        # --- state toggles nothing reacts to: flipped, then ignored. ---
        "is-awake",  # view-story.js:196  root.classList.toggle('is-awake', k >= 1)
        "raw-on",  # view-story.js:1019 toggled at step 1
        "grounded-on",  # view-story.js:1020 toggled at step 2
        # --- bare: applied, styled by nothing, read by nothing. ---
        "mon-audit",  # view-monitor.js:379 — only .mon-audit-wrap is defined
        "mon-trust-wrap",  # view-monitor.js:679
        "anomview",  # view-anomaly.js:16 — view-root wrapper
        "flowview",  # view-flow.js:14 — view-root wrapper
        "proc-body",  # view-flow.js:133
        "gq",  # view-ask.js:126 — Ask's grounding surface
        "gq-filter",  # view-ask.js:133
        "gsrc",  # view-ask.js:147
        "prop-name",  # intake-view.js:320 — property-editor rows
        "prop-type",  # intake-view.js:323
        "prop-values",  # intake-view.js:329
        "prop-values-spacer",  # intake-view.js:333
        "pv-busy",  # intake-procedures.js:148
        "pv-step-titles",  # view-procedures.js:484
        "apc-doa-m",  # view-story.js:1582 — narrative chrome
        "apc-q-na",  # view-story.js:1594
        "pt-node-l",  # view-story.js:1517
        "pw-task-l",  # view-story.js:1470
        "state-badge",  # view-story.js:543
        "asset",  # view-map.js:212 — SVG node, via setAttribute
        "site",  # view-map.js:249 — SVG node, via setAttribute
        "hero-contrast-lbl",  # view-hero.js:168
        "llm-state",  # llm-control.js:37
    }
)


def _allowed_undefined() -> frozenset[str]:
    """Every class permitted to have no styling rule."""
    return _JS_HOOK_CLASSES | _INERT_CLASSES


# --------------------------------------------------------------------------- #


#: Comment stripping lives in ``tests.api.js_source`` — shared with the other two
#: modules that scan these assets as text. It blanks comments character-for-
#: character rather than removing them, which is what keeps the ``file:line`` in
#: the failure messages below pointing at the right code: those line numbers are
#: derived from a character OFFSET into the stripped source, so a stripper that
#: collapses a comment makes every report after it wrong by that comment's size.


def _class_selectors_in(css: str) -> set[str]:
    """Every ``.name`` class selector in a CSS source."""
    return set(
        re.findall(r"\.(-?[_a-zA-Z][\w-]*)", re.sub(r"/\*.*?\*/", " ", css, flags=re.DOTALL))
    )


@lru_cache(maxsize=1)
def _defined_css_classes() -> frozenset[str]:
    """Classes defined by a linked stylesheet OR by a JS-injected ``<style>``.

    The second source is not an edge case: ``view-monitor.js`` builds its own
    stylesheet in a template literal and appends it to ``<head>`` at mount, so 43
    ``mon-*`` classes are defined in no ``.css`` file at all. A scan that reads
    only the linked sheets reports every one of them as undefined — 43 false
    positives from one view, which is enough noise to make the whole guard useless.
    """
    html = _INDEX_HTML.read_text(encoding="utf-8")
    names: set[str] = set()
    for sheet in re.findall(r'<link rel="stylesheet" href="assets/([^"?]+)', html):
        names |= _class_selectors_in((_ASSETS / sheet).read_text(encoding="utf-8"))
    for js in _asset_files():
        for block in re.finditer(
            r"const\s+css\s*=\s*`(.*?)`", js.read_text(encoding="utf-8"), flags=re.DOTALL
        ):
            names |= _class_selectors_in(block.group(1))
    return frozenset(names)


@lru_cache(maxsize=1)
def _asset_files() -> tuple[Path, ...]:
    """Every front-end JS asset, by glob — a new view needs no edit here."""
    return tuple(sorted(_ASSETS.glob("*.js")))


def _applied_classes(src: str) -> dict[str, int]:
    """``{class name: 1-based line of its first application}`` for one asset."""
    found: dict[str, int] = {}

    def record(token: str, offset: int) -> None:
        found.setdefault(token, src.count("\n", 0, offset) + 1)

    for pattern in (
        _CLASS_PROP,
        _CLASS_NAME,
        _SET_ATTR,
        _CLASS_LIST_TOGGLE,
        _RETURNED_STATUS_CLASS,
    ):
        for match in re.finditer(pattern, src):
            for token in match.group(1).split():
                record(token, match.start())
    for match in re.finditer(_CLASS_LIST_VARIADIC, src):
        for literal in re.findall(r"'([^']*)'", match.group(1)):
            for token in literal.split():
                record(token, match.start())
    return found


def _lookup_hook_classes(src: str) -> set[str]:
    """Classes this asset READS through a selector rather than applies."""
    return set(re.findall(_SELECTOR, src)) | set(re.findall(_BY_CLASS_NAME, src))


@lru_cache(maxsize=1)
def _undefined_classes() -> dict[str, str]:
    """``{class name: "file:line"}`` for every applied class nothing defines.

    A token ending in ``-`` is the literal half of a runtime-built name
    (``'urg-' + level``), not a class. Reporting those would train the reader to
    ignore this test's output, which is worse than the gap they represent.
    """
    defined = _defined_css_classes()
    undefined: dict[str, str] = {}
    for js in _asset_files():
        src = strip_js_comments(js.read_text(encoding="utf-8"))
        for token, line in _applied_classes(src).items():
            if token in defined or token.endswith("-"):
                continue
            undefined.setdefault(token, f"{js.name}:{line}")
    return undefined


# --------------------------------------------------------------------------- #
# The guard.
# --------------------------------------------------------------------------- #


def test_every_applied_css_class_is_defined_or_allowlisted() -> None:
    """A class no rule styles renders unstyled and inherits whatever ancestors set."""
    unexpected = {
        name: site
        for name, site in _undefined_classes().items()
        if name not in _allowed_undefined()
    }
    assert not unexpected, (
        "front-end assets apply CSS classes no stylesheet (linked or injected) defines:\n"
        + "\n".join(f"  .{name:24} {site}" for name, site in sorted(unexpected.items()))
        + "\n\nThese render unstyled and silently inherit whatever the ancestors set — the "
        "failure mode is a broken layout with a clean console, not an error. Either define "
        "the class, use one that exists, or drop the attribute if it does nothing. If it is "
        "deliberately unstyled (a JS lookup hook), add it to the allowlist WITH a reason."
    )


def test_the_allowlist_is_exactly_the_undefined_set() -> None:
    """Set equality both ways — this is what stops the allowlist becoming a junk drawer.

    Without it the allowlist only ever grows: a new undefined class gets appended
    to silence a red build, and a class that has since been defined stays listed
    forever, so the list stops describing reality. Both directions are bugs.
    """
    undefined = set(_undefined_classes())
    allowed = _allowed_undefined()

    stale = allowed - undefined
    assert not stale, (
        f"the allowlist names classes that are no longer undefined: {sorted(stale)}\n\n"
        "The debt was paid (or the class was removed) but the entry stayed. Delete it — "
        "an allowlist that outlives its reason is how a guard quietly stops guarding."
    )
    unlisted = undefined - allowed
    assert not unlisted, (
        f"undefined classes not accounted for in the allowlist: {sorted(unlisted)}\n\n"
        "Every one must be either fixed or listed with the reason it is deliberately "
        "unstyled. Silence is not one of the options."
    )


def test_no_allowlisted_class_is_both_inert_and_a_lookup_hook() -> None:
    """The two categories must stay distinguishable, or the split means nothing."""
    overlap = _JS_HOOK_CLASSES & _INERT_CLASSES
    assert not overlap, (
        f"classes listed in BOTH allowlist categories: {sorted(overlap)}\n\n"
        "A class is either read back as a lookup key (permanent, healthy) or inert "
        "(debt that should trend to zero). Listing one as both makes the distinction "
        "unreadable, which is the only thing the split buys."
    )


# --------------------------------------------------------------------------- #
# Guarding the guard — every one of these caught a real defect while this
# module was being written, except where noted.
# --------------------------------------------------------------------------- #


def test_the_class_scan_sees_the_real_stylesheets() -> None:
    """An empty class registry would make the guard above pass on anything."""
    defined = _defined_css_classes()
    assert len(defined) > 500, (
        f"only {len(defined)} CSS classes parsed — the parser or the <link> scan is "
        "broken. A pass above would prove nothing."
    )
    # One anchor per linked sheet: if any is missing, that sheet was skipped.
    for anchor in ("faint", "hero-kpi-tile", "hero-sub"):
        assert anchor in defined, (
            f"'{anchor}' was not found — at least one sheet linked by index.html is "
            "not being read."
        )


def test_the_scan_reads_javascript_injected_stylesheets() -> None:
    """``view-monitor.js`` defines 43 ``mon-*`` classes in no .css file at all.

    Pinned by name rather than by count: if the injection is refactored away the
    classes must move to a real sheet, and either way these names stay defined.
    """
    defined = _defined_css_classes()
    for anchor in ("mon-audit-wrap", "mon-run", "mon-trust"):
        assert anchor in defined, (
            f"'{anchor}' is defined in view-monitor.js's injected <style> block but the "
            "scan did not find it. Every mon-* class now reads as undefined — 43 false "
            "positives that make this module's output worthless."
        )


def test_every_asset_that_builds_dom_contributes_class_tokens() -> None:
    """A per-file floor: one asset silently scanning to nothing must not pass.

    A union-level floor cannot see this — ``view-story.js`` alone contributes
    enough tokens to keep any global count healthy while another file's classes
    go entirely unread.

    Stated as a PROPERTY rather than a list of expected filenames. Six assets
    legitimately produce no classes (``api.js``, ``auth.js``, ``gate-fixture.js``,
    ``mock.js``, ``motion.js``, ``trace-kinds.js`` — verified to contain no DOM
    call at all), and a hardcoded roster of those would need editing every time a
    helper is added, which is how a guard acquires a reputation for false alarms.
    The invariant that cannot rot is: *if it builds DOM, it must be scanned.*
    """
    silent_but_building: list[str] = []
    for js in _asset_files():
        src = strip_js_comments(js.read_text(encoding="utf-8"))
        if _applied_classes(src):
            continue
        if re.search(r"createElement|innerHTML|appendChild", src):
            silent_but_building.append(js.name)
    assert not silent_but_building, (
        f"assets that build DOM but contributed no class tokens: {silent_but_building}\n\n"
        "Either the usage patterns above stopped matching that file's style, or its "
        "classes moved to a form this scan cannot see. Until it is fixed, that asset is "
        "being guarded vacuously — it passes because nothing was looked at."
    )


def test_the_scan_sees_status_classes_returned_by_a_factory() -> None:
    """``api.js`` applies no class anywhere — it only RETURNS status names.

    Without ``_RETURNED_STATUS_CLASS`` that whole file contributes nothing and is
    guarded vacuously, and the failure is silent: the module still passes, it just
    stops covering the vocabulary every view concatenates onto its elements.
    """
    src = strip_js_comments((_ASSETS / "api.js").read_text(encoding="utf-8"))
    applied = _applied_classes(src)
    for status in ("s-ok", "s-warn", "s-crit", "s-neutral"):
        assert status in applied, (
            f"'{status}' is returned by api.js's status-class factory but the scan did "
            "not find it. api.js applies no classes directly, so this pattern is the "
            "only thing that covers it — the file is now guarded vacuously."
        )


def test_the_comment_stripper_preserves_every_line() -> None:
    """A stripper that eats newlines makes every reported file:line point at the wrong code."""
    for js in _asset_files():
        raw = js.read_text(encoding="utf-8")
        assert strip_js_comments(raw).count("\n") == raw.count("\n"), (
            f"the comment stripper changed {js.name}'s line count. Every file:line this "
            "module reports is now off by the size of the comments above it."
        )


def test_the_stripper_removes_comments_without_eating_code() -> None:
    """The other direction: if it ate the code, every scan built on it is vacuous."""
    src = strip_js_comments((_ASSETS / "view-monitor.js").read_text(encoding="utf-8"))
    assert "/*" not in src and "*/" not in src, "block comments survived the stripper"
    # view-monitor.js is the hard case: its injected stylesheet is a template
    # literal full of CSS, and CSS comments use the same delimiters as JS ones.
    # These two anchors bracket that block — the function that builds it and the
    # append that installs it.
    for anchor in ("injectStyles", "document.head.appendChild"):
        assert anchor in src, (
            f"the stripper removed {anchor!r} from view-monitor.js — it ate real code "
            "around the injected stylesheet, and every guard in this module built on "
            "the stripped source is now unfalsifiable."
        )


def test_a_block_opener_inside_a_line_comment_does_not_blank_the_code_below() -> None:
    """Regression for s207: this cost a session, and the failure named the wrong thing.

    The stripper used to run two passes — block comments, then line comments. That
    is the reverse of how JavaScript tokenises: whichever opener comes FIRST wins,
    so a ``/*`` written inside a ``//`` comment is prose, not a block opener.

    A line comment in ``app.js`` mentioning a route glob (``/intake/`` + ``*``) was
    therefore read as opening a block, which ran on to the next ``*/`` about 150
    lines below and deleted a ``class: 'strip-msg'`` application from the scan.
    ``test_the_allowlist_is_exactly_the_undefined_set`` went red claiming
    ``strip-msg`` was "no longer undefined" — in a file the change under test had
    never touched, pointing at the allowlist rather than at the stripper. The
    browser was fine throughout; only the guard was fooled. The fix at the time was
    to reword the comment, which left the trap armed for whoever came next.

    Both orderings are asserted, because each is a way for one comment form to eat
    the other, and fixing only the first would leave the guard half-blind.
    """
    line_comment_first = (
        "// see the /intake/* route family for the other half of this\n"
        "h('span', { class: 'after-line-comment' }, msg);\n"
        "/* a genuine block comment, whose */\n"
        "h('span', { class: 'after-real-block' }, msg);\n"
    )
    applied = _applied_classes(strip_js_comments(line_comment_first))
    assert "after-line-comment" in applied, (
        "a `/*` inside a `//` comment swallowed the code below it. The stripper is "
        "removing block comments before line comments again — the s207 bug. Classes "
        "vanish from the scan in files nobody edited, and the allowlist equality "
        "test blames the allowlist for it."
    )
    assert (
        "after-real-block" in applied
    ), "the phantom block ran past a REAL block comment's closer and kept eating."

    block_comment_first = (
        "/* a banner mentioning a // line comment, then showing the old markup:\n"
        "   h('span', { class: 'quoted-in-block' }, msg)  <- prose, not code */\n"
        "h('span', { class: 'after-block-comment' }, msg);\n"
    )
    applied = _applied_classes(strip_js_comments(block_comment_first))
    assert "after-block-comment" in applied, (
        "a `//` inside a block comment ended the block early, so the block never "
        "closed where it should and ate the code after it."
    )
    assert "quoted-in-block" not in applied, (
        "a class name quoted inside a block comment reached the scan as if the code "
        "applied it. The `//` in that comment terminated the block early."
    )


def test_the_stripper_needs_a_closer_before_it_treats_a_slash_star_as_a_comment() -> None:
    """``'image/*,application/pdf'`` is a MIME type, not an unterminated comment.

    Measured, not hypothetical: treating a ``/*`` with no ``*/`` after it as a
    comment running to end of file blanked 82 lines of ``view-case.js`` (whose
    file-input ``accept`` attribute carries that literal) and 8 of ``view-hero.js``
    (the ``/demo/hero/*`` route glob), taking 11 class applications out of the scan
    with them. Both files parse perfectly in the browser.
    """
    src = (
        "h('input', { class: 'up', accept: 'image/*,application/pdf' });\n"
        "h('b', { class: 'below' });\n"
    )
    applied = _applied_classes(strip_js_comments(src))
    assert {"up", "below"} <= set(applied), (
        f"a `/*` inside a string literal with no closer was treated as a comment and "
        f"blanked the rest of the source; found only {sorted(applied)}"
    )


def test_a_block_opener_inside_a_string_literal_does_not_open_a_block() -> None:
    """The trap the previous fix left latent, closed: a quoted string is DATA.

    ``view-case.js`` carries ``accept: 'image/*,application/pdf'`` and
    ``view-hero.js`` the ``/demo/hero/*`` route glob, both inside string literals.
    Neither has a ``*/`` after it today, which is the only reason a stripper with
    no model of strings survived them — add one block comment below either line and
    the span in between silently leaves the scan, which is precisely the s207
    failure wearing a different opener.
    """
    src = (
        "h('input', { accept: 'image/*,application/pdf' });\n"
        "h('b', { class: 'inside-the-span' });\n"
        "/* an ordinary block comment further down the file */\n"
        "h('i', { class: 'after-the-block' });\n"
    )
    applied = _applied_classes(strip_js_comments(src))
    assert "inside-the-span" in applied, (
        "a `/*` inside a string literal reached forward to a real block comment's "
        "`*/` and blanked everything between them. Quoted strings must be opaque to "
        "the comment scanner."
    )
    assert "after-the-block" in applied, "the scan lost the code below the real block comment"


def test_a_line_comment_marker_inside_a_string_literal_is_not_a_comment() -> None:
    """``'http://www.w3.org/2000/svg'`` is an SVG namespace, not a comment.

    Measured: this exact literal appears in ``components.js``, ``view-map.js`` and
    ``view-story.js``. Without string opacity the ``//`` in it blanks the rest of
    its line, so anything applied after the URL on that line is invisible to every
    scan built on this stripper.
    """
    src = "h('div', { xmlns: 'http://www.w3.org/2000/svg', class: 'after-url' });\n"
    applied = _applied_classes(strip_js_comments(src))
    assert "after-url" in applied, (
        "the `//` inside a URL string was read as a line comment and blanked the "
        "rest of the line, hiding the class applied after it."
    )


def test_string_opacity_is_bounded_to_one_line() -> None:
    """An apostrophe that is not a string opener must not run past its own line.

    A single- or double-quoted JS string cannot contain a raw newline, so the
    search for a closing quote stops at the line end. That bound is what makes
    quote handling safe without a real parser: prose like ``don't`` inside a
    TEMPLATE literal (which this stripper deliberately does not treat as opaque)
    would otherwise pair with the next apostrophe anywhere below it.

    Note what actually goes wrong when the bound is missing, because it is not the
    obvious thing: skipping a string does not BLANK anything, so no code vanishes.
    What is lost is the comment scanner's view of the openers inside the skipped
    span — the block comment below is never stripped, and the class name quoted in
    its prose is then read as an applied class. That is the assertion here.
    """
    src = (
        "const s = `don't`;\n"
        "/* the old markup was h('b', { class: 'quoted-in-prose' }) */\n"
        "h('i', { class: 'real' });\n"
    )
    applied = _applied_classes(strip_js_comments(src))
    assert "quoted-in-prose" not in applied, (
        "an unmatched apostrophe opened a string span that ran past the end of its "
        "line and swallowed the `/*` below it, so the block comment was never "
        "stripped and its prose was scanned as code."
    )
    assert "real" in applied, "the scan lost the genuine class application"


def test_an_escaped_quote_does_not_close_the_string_early() -> None:
    """``'don\\'t /*'`` is one string, not a string followed by a block opener.

    Without escape handling the literal closes at the escaped quote, the scanner
    resumes mid-string, and the ``/*`` it then finds opens a phantom block that
    runs to the next real ``*/``. Same failure as s207, reached through the quote
    branch instead of the comment branch.
    """
    src = (
        "h('b', { title: 'don\\'t /*', class: 'has-escape' });\n"
        "h('i', { class: 'inside-span' });\n"
        "/* a real block comment, whose closer the phantom would reach */\n"
    )
    applied = _applied_classes(strip_js_comments(src))
    assert {"has-escape", "inside-span"} <= set(applied), (
        f"an escaped quote closed the string early and the `/*` after it opened a "
        f"phantom block; found only {sorted(applied)}"
    )


def test_a_quoted_comment_marker_survives_the_strip_on_purpose() -> None:
    """Pins the behaviour change, so nobody 'fixes' it back.

    Before quoted strings were opaque, ``'/*' not in stripped`` was a fair proxy
    for "block comments were removed". It is not any more: three lines in the
    shipped assets legitimately keep a ``/*`` (``view-case.js`` 250 and 297,
    ``view-hero.js`` 664). Two tests still make that assertion and both are scoped
    to files with no such literal — this records WHY that scoping now matters.
    """
    src = (
        "h('input', { accept: 'image/*,application/pdf' });\n"
        "/* a real block comment, whose closer the marker above would reach */\n"
    )
    stripped = strip_js_comments(src)
    assert "image/*" in stripped, (
        "a comment marker inside a string literal was blanked. It is data — the "
        "browser sends it as a MIME type — and blanking it is how the scan loses "
        "the code around it."
    )


def test_the_stripper_blanks_a_comment_rather_than_deleting_it() -> None:
    """Deleting a comment FABRICATES identifiers out of the code on either side.

    ``test_export_cover_ui_contract`` proves the SPA registers the Month-End KPI
    view by asserting ``'O.ViewExport' in app_js``. A stripper that removed a
    comment instead of blanking it would let ``O.View/* … */Export`` satisfy that —
    a token present nowhere in the file, evidencing a registration that does not
    exist. Blanking is what keeps the two halves apart.
    """
    stripped = strip_js_comments("O.View/* a note between the halves */Export")
    assert "O.ViewExport" not in stripped, (
        "the stripper deleted a comment instead of blanking it, gluing the code on "
        "either side into an identifier that appears in no asset."
    )
    assert (
        "O.View" in stripped and "Export" in stripped
    ), "the stripper ate the real code around the comment, not just the comment."


def test_the_scan_ignores_the_toggle_force_argument() -> None:
    """``classList.toggle(token, force)`` takes a BOOLEAN second argument.

    Regression guard for a real defect in this module's first draft: scanning the
    whole argument list pulled ``'matrix'`` and ``'swap'`` out of
    ``view-story.js``'s ``classList.toggle('mode-matrix', m === 'matrix')`` and
    reported them as undefined classes. Two phantom entries would have been
    written into the allowlist as debt that never existed.
    """
    applied = _applied_classes("root.classList.toggle('mode-matrix', m === 'matrix');")
    assert "mode-matrix" in applied, "the toggle scan lost the class name itself"
    assert "matrix" not in applied, (
        "the scan read toggle()'s `force` argument as a class name. Any string compared "
        "inside a toggle call now shows up as phantom CSS debt."
    )


def test_the_codebase_still_uses_only_single_quoted_classes() -> None:
    """This module reads single-quoted literals only; that must stay true.

    A view written with ``class="a b"`` or a template literal would be scanned as
    having no classes at all — the guard would pass while covering nothing.
    """
    offenders: list[str] = []
    for js in _asset_files():
        src = strip_js_comments(js.read_text(encoding="utf-8"))
        if re.search(r"class:\s*[\"`]", src) or re.search(r"className\s*\+?=\s*[\"`]", src):
            offenders.append(js.name)
    assert not offenders, (
        f"assets applying classes with double quotes or template literals: {offenders}\n\n"
        "This module's scan only reads single-quoted literals, so those classes are "
        "invisible to it. Either normalise the quoting or widen the patterns above — "
        "but do not leave the guard silently blind to a whole file."
    )
