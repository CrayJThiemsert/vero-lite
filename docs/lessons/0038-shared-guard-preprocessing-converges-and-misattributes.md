# Lesson #0038 — Preprocessing that every guard reuses has no owner: it recurs by convergence, and it reddens in someone else's name

**Date:** 2026-08-06 (session 207)
**Class:** advisory (guard design / test infrastructure)
**Trigger:** Four independent test modules had each written the same JavaScript
comment stripper, and all four had the same defect. Fixed in
[#1053](https://github.com/CrayJThiemsert/vero-lite/pull/1053) /
[#1054](https://github.com/CrayJThiemsert/vero-lite/pull/1054).

## The lesson

**A transform every guard runs *before* asserting is a shared dependency with no
shared home. That gives it two properties nothing else in the suite has: its
defects arrive by convergence rather than by copying, and its failures are always
reported under the caller's name — in whatever file the caller happened to scan.**

Both halves were live here at once, and they compound: because the failure never
names the transform, no author who hit it went looking at the transform. Each
wrote a fresh copy instead.

## Half one — convergence, not copy-paste

The repo has no build step and no JS test runner (`docs/conventions/ui.md` §5), so
every UI tripwire is a Python test that reads `services/api/static/assets/*.js` as
text. Each such test must first drop comment CONTENT, or a class name (or a route,
or a field) *mentioned in prose* reads as if the code used it.

Four modules had written that stripper:

| module | form |
|---|---|
| `tests/api/test_css_class_contract.py` | blanked, preserving lines |
| `tests/api/test_export_cover_ui_contract.py` | replaced with `" "` |
| `tests/api/test_view_hero_fleet_ui_contract.py` | `_BLOCK_COMMENT` / `_LINE_COMMENT` pair |
| `tests/api/test_ui_profile.py` | deleted, with `(?<!:)` sparing `://` |

Four different authors, four different blanking policies, one identical defect —
**block comments stripped first, then line comments**:

```python
without_block = re.sub(r"/\*.*?\*/", ..., src, flags=re.DOTALL)
return re.sub(r"//[^\n]*", ..., without_block)
```

JavaScript tokenises the other way round. Whichever opener appears FIRST wins and
the other is then ordinary text — once `//` starts a line comment, everything to
the newline is comment, *including* a `/*` inside it. Two sequential `re.sub`
passes cannot express that, because each pass sees the whole string in the "code"
state. It is not a subtle bug so much as a category error: a tokenizer problem
written as two independent regexes.

**The fourth copy is the one that makes the point.** It was added by
[#1052](https://github.com/CrayJThiemsert/vero-lite/pull/1052) (PLAN-0100 Step 3),
landing on main *while this very fix was being written, in the same session*.
Nobody copied a known-bad function. Each author independently reached for the same
obvious two-line regex pair, because it is the obvious thing to reach for.

That is the whole argument for consolidating rather than correcting in place: a
defect that four people reproduce without contact is a property of the **problem**,
and correcting four copies leaves the fifth author to re-derive it next month.

## Half two — the failure reddens in someone else's name

Session 207's account of the original incident: a line comment in `app.js`
mentioned a route glob reading as `/intake/` + `*`. The block pass took that `/*`
for a real opener and blanked to the next `*/` roughly 150 lines below, which
removed a `class: 'strip-msg'` application from the scan. The result:

> `test_the_allowlist_is_exactly_the_undefined_set` FAILED —
> the allowlist names classes that are no longer undefined: `['strip-msg']`

Read that failure as a reviewer. It names **the allowlist**, in
`test_css_class_contract.py`. It points at `app.js` — **a file the change under
test had never touched**. It suggests the remedy "delete the stale entry", which
would have been wrong. The actual cause is in neither file: it is the preprocessing
step both of them run before anything is compared. The browser was fine throughout;
it parses the file correctly. Only the guard was fooled.

The workaround applied at the time was to reword the comment in `app.js`. That
made the suite green and left the trap armed.

**The measured second instance.** Grepping for the shape found it still live in a
different file — `api.js:87` (as of `bac8f69`; it was `:74` before
[#1052](https://github.com/CrayJThiemsert/vero-lite/pull/1052) shifted the file):

```js
// fallback. A mocked copy would drift from the live verticals/*/procedures.yaml
```

That `/*` opened a phantom block that ran to the `*/` closing the real banner
comment on line 105. **Lines 87–105 of `api.js` — the `procedures` fetch and its
whole function — were invisible to every scan built on the stripper**, including
`test_the_export_ui_never_reaches_the_csv_route`, the structural guard on a typed
Cray decision. Nothing was red. The guard was simply not looking at that region,
and had not been for as long as the comment had said what it said.

## What the fix had to get right, measured rather than assumed

Two design choices looked obvious and were wrong; both were caught by measuring
the delta across all 42 assets before changing any test.

**1. "An unterminated `/*` is a syntax error, so blank to EOF and fail loud."**
Wrong here. Two shipped assets carry `/*` inside a **string literal**:

| file (at `bac8f69`) | literal |
|---|---|
| `view-case.js:250` and `:297` | `accept: 'image/*,application/pdf'` |
| `view-hero.js:678` | the `/demo/hero/*` route glob |

Blanking to EOF removed 82 lines of one and 8 of the other, taking **11 class
applications** out of the scan. Both files parse perfectly in the browser.
Requiring a closer is what keeps them visible.

**2. "Deleting the comment is the same as blanking it."** It is not. Delete, and
`O.View/* note */Export` becomes `O.ViewExport` — an identifier present nowhere in
the file, and exactly the string `test_export_cover_ui_contract` reads to prove the
SPA registers a view. The fourth copy deleted; migrating it to a blanking helper
closed a fabrication path that had never fired.

**3. The property that was dropped on purpose, and measured first.** The fourth
copy's `(?<!:)` spared `://` so a URL would not truncate a line before a real call.
The shared helper does not reproduce that literally. Rather than wave it through,
the registry scan was run under all three strippers — the local one, the shared
one, and the string-aware follow-up — and all three produce the same twelve
observed entries matching `_GUARD_REGISTRY` exactly; no line in today's assets puts
a registered wrapper call after a `://` at all. #1054 then reaches the same end
structurally, by treating quoted strings as opaque.

## The probe discipline earned its keep three times

Every new regression test was run against a deliberately broken stripper to
confirm it goes RED for its stated reason. **Three of the tests written across the
two PRs were vacuous, and two of them asserted the wrong consequence entirely:**

- One claimed collapsing a comment would move a reported `file:line`. It cannot —
  `_applied_classes` derives a line by counting **newlines** up to an offset, so
  collapsing a comment's other characters moves nothing. Deleted; the existing
  preserves-every-line test already covered the real failure.
- One put its class *outside* the span the bug swallows, so it passed with the fix
  disabled.
- One asserted that an over-long string span makes code disappear. It does not —
  skipping a string blanks nothing. What is actually lost is the scanner's view of
  the comment openers *inside* the skipped span, which leaves the block comment
  below unstripped and its quoted prose read as an applied class.

Without the probes, all three would have shipped as guards that advertise coverage
they do not have.

## How to apply

- **When two or more guards run the same transform before asserting, give it one
  home.** Not because duplication is untidy — because the duplicate copies will
  converge on the same defect and be corrected one at a time forever.
- **When a guard reddens naming a file your change never touched, suspect its
  preprocessing before you touch the thing it names.** The assertion names what it
  compared, not what corrupted the input. Rewording the source until the guard goes
  quiet is the failure mode to watch for in yourself.
- **Measure the delta of a preprocessing change across the whole scanned corpus
  before adjusting any test.** Both wrong turns above were caught this way, and
  neither would have been caught by the suite — it was green for both.
- **Preprocessing has to be blame-neutral in both directions.** Removing too little
  scans prose as code; removing too much makes the guard vacuous while staying
  green. The second is the dangerous one, because nothing reports it.
- **Probe a new guard against the mutation it defends against, not just for a
  green run.** Ask what output the mutation changes — a test that cannot name that
  is likely asserting the wrong consequence.

Related: [`#0035`](0035-negative-measurement-needs-a-positive-control.md) — the
probe requirement this leans on; [`#0037`](0037-a-scans-blind-spot-is-the-intersection-of-its-axes.md)
— a guard's coverage claim being narrower than it reads;
[`#0024`](0024-rules-must-live-where-the-enforcer-looks.md) — the same
"lives where nobody looks for it" shape one level up.
