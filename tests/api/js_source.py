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

Scope, stated honestly — this reads comments only, not the full JS grammar. It has
no model of string, template, or regex literals, so ``'https://example.com'`` is
treated as starting a line comment and the rest of that line is blanked. That is
the behaviour the previous strippers had too, and it is safe in the direction that
matters here: these guards ask "is this name present in the CODE?", so blanking
too much can only cause a FALSE PASS on the line it eats, never a false failure
elsewhere — whereas the ordering bug above blanked *150 lines at a time* and did
produce a false failure. Widening to literal-awareness is a separate change with a
real blast radius; it is a known gap, not an oversight.
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
        view-hero.js:664   '… the hero-demo endpoints (/demo/hero/*) require …'

    Blanking from there to EOF deleted 82 lines of ``view-case.js`` and 8 of
    ``view-hero.js`` from the scan, taking 11 class applications with them. Those
    files parse fine in the browser; only a stripper with no model of string
    literals sees an opener. Requiring a closer is what keeps them visible.

    Which leaves ONE trap of the s207 shape still armed, named here rather than
    hidden: a ``/*`` inside a string literal that DOES have a later ``*/`` would
    blank the span between them. Today neither instance above has one, so this is
    latent, not live. Closing it means teaching the scanner that a quoted string is
    opaque — a wider change, because three assets build CSS inside TEMPLATE
    literals whose ``/* … */`` comments the callers rely on this stripper to
    remove, so "literals are opaque" cannot be applied uniformly.
    """
    out = list(src)
    end_of_source = len(src)
    i = 0

    def blank(start: int, stop: int) -> None:
        for k in range(start, stop):
            if out[k] != "\n":
                out[k] = " "

    while i < end_of_source:
        if src[i] == "/" and i + 1 < end_of_source:
            nxt = src[i + 1]
            if nxt == "/":
                newline = src.find("\n", i)
                stop = end_of_source if newline == -1 else newline
                blank(i, stop)
                i = stop
                continue
            if nxt == "*":
                closer = src.find("*/", i + 2)
                if closer != -1:
                    blank(i, closer + 2)
                    i = closer + 2
                    continue
        i += 1

    return "".join(out)
