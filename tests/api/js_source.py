"""One order-correct JavaScript comment stripper, shared by the UI source guards.

Several tests in this package scan ``services/api/static/assets/*.js`` as text —
the repo has no build step and no JS test runner (``docs/conventions/ui.md`` §5),
so a CI tripwire for the UI has to be a Python test that reads the source. Every
one of those scans must first drop comment CONTENT, or a class name (or a route,
or a field) merely *mentioned in prose* reads as if the code used it.

FOUR modules had each grown their own copy of that stripper, and all four had the
same defect: they removed block comments first, then line comments.

The fourth is worth naming, because it says something about the shape of this bug:
``test_ui_profile.py`` grew its copy in PLAN-0100 Step 3, *while this fix was being
written*, in the same session. Nobody copied a known-bad function — each author
independently reached for the obvious two-line regex pair, which is exactly why the
right fix is one shared helper rather than four corrected copies.

    without_block = re.sub(r"/\\*.*?\\*/", ..., src, flags=re.DOTALL)
    return re.sub(r"//[^\\n]*", ..., without_block)

JavaScript's tokenizer does the opposite. Whichever opener appears FIRST wins, and
the other is then ordinary text: once ``//`` starts a line comment, everything to
the newline is comment — including a ``/*`` inside it.

Measured, in session 207: a line comment in ``app.js`` mentioned a route glob that
read as ``/intake/`` + ``*``. The block pass ran first, took that ``/*`` for a real
block opener, and blanked everything down to the next ``*/`` — roughly 150 lines
below — which deleted a ``class: 'strip-msg'`` application from the scan.
``test_the_allowlist_is_exactly_the_undefined_set`` went red saying ``strip-msg``
was "no longer undefined", in a file the change under test had never touched, with
a message pointing at the allowlist instead of at the stripper. The browser was
never affected — it parses the file correctly; only the guard was fooled. The fix
applied then was to reword the comment, which left the trap armed for the next
person. This module is the actual fix.

Scope, stated honestly — this models comments and QUOTED STRINGS, not the full JS
grammar. Three cases, and the split between them is deliberate:

* Single- and double-quoted strings are OPAQUE: a ``//`` or ``/*`` inside one is
  data. This is what makes ``'http://…'`` and ``'image/*,application/pdf'`` safe.
* TEMPLATE literals are deliberately NOT opaque. Three assets build stylesheets
  inside backticks, and the callers rely on this function to strip the ``/* … */``
  comments in that CSS — ``test_the_stripper_removes_comments_without_eating_code``
  asserts exactly that. Opacity cannot be applied uniformly for that reason.
* REGEX literals are not modelled. Telling ``/re/`` from division needs parser
  context, and no asset currently contains a regex literal carrying a comment
  marker. This is the remaining gap, and it is small: a regex would have to embed
  ``//`` or ``/*`` to matter.
"""

from __future__ import annotations

__all__ = ["strip_js_comments"]


def strip_js_comments(src: str) -> str:
    """Blank every comment in ``src``, preserving its exact length and newlines.

    Single left-to-right pass, so the two comment forms cannot mis-nest: a ``/*``
    seen inside a line comment is text, and a ``//`` seen inside a block comment
    is text.

    Comments are replaced character-for-character with spaces rather than removed,
    for two reasons — one of which is weaker than it looks, and is written down that
    way so nobody re-derives it as load-bearing:

    * Newlines survive, so ``file:line`` in the callers' failure messages still
      points at the right code. This is the load-bearing half, and note that it is
      the NEWLINES that carry it: ``test_css_class_contract`` derives a line by
      counting newlines up to a character offset, so collapsing a comment's other
      characters would not actually move a line number. Preserving the full width
      is a stronger invariant than that caller strictly needs.
    * Blanking rather than DELETING keeps the surrounding tokens apart, and this
      one is load-bearing on its own: cut ``O.View/* note */Export`` down to
      ``O.ViewExport`` and a scan is handed an identifier present nowhere in the
      file — which is exactly the string ``test_export_cover_ui_contract`` reads to
      prove the SPA registers the view.

    A ``/*`` with no ``*/`` after it is left alone rather than blanked to end of
    file. In JavaScript an unterminated block comment is a syntax error, so the
    tempting reading is that blanking to EOF is the "loud" response — but measured
    against the real assets it is the opposite. Two of them carry ``/*`` inside a
    STRING LITERAL, neither of them a comment:

        view-case.js:250   accept: 'image/*,application/pdf'
        view-hero.js:678   '… the hero-demo endpoints (/demo/hero/*) require …'

    Blanking from there to EOF deleted 82 lines of ``view-case.js`` and 8 of
    ``view-hero.js`` from the scan, taking 11 class applications with them. Those
    files parse fine in the browser; only a stripper with no model of string
    literals sees an opener. Requiring a closer is what keeps them visible.

    Quoted strings are skipped whole, so a comment marker inside one is data and
    survives into the output. That is what closes the remaining trap of the s207
    shape: a ``/*`` inside a string that DOES have a later ``*/`` would otherwise
    blank the span between them. Neither live instance has a closer today, so that
    was latent rather than firing — it is fixed here on purpose, not by accident.

    The consequence to know about: ``'/*' not in strip_js_comments(src)`` is no
    longer a valid way to ask "were the block comments removed?". Three lines in
    the shipped assets legitimately keep a ``/*`` after stripping (``view-case.js``
    250 and 297, ``view-hero.js`` 664). Two tests make that assertion and both are
    scoped to files with no such literal, so both still hold — but a third file
    added to either list would need the question asked a different way.
    """
    out = list(src)
    i = 0
    while i < len(src):
        comment = _comment_span(src, i)
        if comment is not None:
            start, stop = comment
            for k in range(start, stop):
                if out[k] != "\n":
                    out[k] = " "
            i = stop
            continue
        if src[i] in "'\"":
            closer = _closing_quote(src, i)
            if closer != -1:
                i = closer + 1
                continue
        i += 1
    return "".join(out)


def _comment_span(src: str, start: int) -> tuple[int, int] | None:
    """``(start, stop)`` of the comment opening at ``start``, or ``None`` if none does.

    Split out from the scan loop so each function stays readable — and so the two
    comment forms' end conditions sit side by side, where the asymmetry between
    them is visible: a line comment runs to the newline OR to end of file, while a
    block comment requires its ``*/`` and otherwise does not open at all.
    """
    if src[start] != "/" or start + 1 >= len(src):
        return None
    following = src[start + 1]
    if following == "/":
        newline = src.find("\n", start)
        return (start, len(src) if newline == -1 else newline)
    if following == "*":
        closer = src.find("*/", start + 2)
        return None if closer == -1 else (start, closer + 2)
    return None


def _closing_quote(src: str, opener: int) -> int:
    """Index of the quote closing the literal opened at ``opener``, or -1 if none.

    Bounded to the opener's own LINE, and that bound is the whole reason quote
    handling is safe to add without a JavaScript parser: a single- or
    double-quoted JS string cannot contain a raw newline. So a quote character
    that is not really opening a string — an apostrophe in ``don't`` inside a
    template literal, say — can never make this function skip past the end of the
    line it sits on, and the worst case is that one line is not scanned for
    comment openers.

    ``\\'`` and ``\\\\`` are honoured, so ``'it\\'s'`` closes at the last quote
    rather than the middle one.
    """
    quote = src[opener]
    i = opener + 1
    while i < len(src):
        char = src[i]
        if char == "\\":
            i += 2
            continue
        if char == "\n":
            return -1
        if char == quote:
            return i
        i += 1
    return -1
