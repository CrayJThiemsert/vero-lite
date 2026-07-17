# OCT UI conventions — vero-lite

> **Canonical, tracked.** The single home for how the Operational Control Tower
> (OCT) demo UI is built — design tokens, the component contract, the security
> rule, the no-build-step workflow, the ontology-driven principle, the
> control-tower tone, and the reasoning-trace attribution channel. Agents doing
> UI work read this first. Everything under `services/api/static/` obeys it.
>
> **Scope.** The OCT console (`services/api/static/`) — a single-page, no-build,
> IIFE/`window.OCT` app served static from FastAPI. Not the handoff tooling, not
> the benchmark HTML.
>
> **Why this is canonical, not derived (ADR-0017 D5 / ADR-0032 OQ-2).** A
> convention you look up deliberately routes to `docs/conventions/` (D5). OQ-2's
> "Rule of Three applies to docs too" wants a second real consumer before a new
> doc exists; the honest accounting: the design opinion already lived, un-homed,
> in the [0013 design prompt](../design/0013-oct-demo-claude-design-prompt.md)
> (consumer #1), and agent-driven per-partner hero UI under ADR-0032 D1
> guarantees consumer #2+. Cray ratified proceeding in-session (PLAN-0080 L-3).

---

## 1. Design tokens (`theme.css`)

The `:root` token vocabulary at
[`theme.css:50-93`](../../services/api/static/assets/theme.css) is the source of
every colour, type, radius and shadow. **Never hard-code a hex** — reference a
token.

- **Surfaces** `--bg-0..--bg-3`, `--bg-inset` (deep charcoal-navy, deepest first).
- **Lines** `--line`, `--line-soft`, `--line-strong`.
- **Text ramp** `--tx-0` (primary) → `--tx-3` (faint).
- **Accent** `--accent` (+ `-soft`/`-line`) — links, active, focus.
- **Semantic status** `--ok/--info/--warn/--crit/--neutral`, each with a `-bg`
  and `-line` companion. Severity == entity status: the SAME five classes colour
  a badge, a node, a timeline marker. Use them consistently — a calm/ok state, a
  warn state, a crit state — never a bespoke colour for a one-off.
- **Type** `--sans` / `--mono` (IBM Plex, vendored under `assets/fonts/` — no CDN).
- **Radii** `--r-sm/md/lg`; **shadow** `--shadow`.

The status **badge** classes are `.badge.s-{ok,info,warn,crit,neutral}` (+
`.badge.solid.*`) at [`theme.css:289-305`](../../services/api/static/assets/theme.css).

## 2. The component contract (`window.OCT`)

`components.js` is the de-facto component library. Its public contract is
exported on `window.OCT` at
[`components.js:239-242`](../../services/api/static/assets/components.js):
`h, clear, icon, badge, typeTag, entityChip, fmtValue, fmtTimestamp,
detailRows, reasoningTrace, traceKind, traceBadge, kvDump, loadingState,
errorState`.

**Use it, don't re-invent it.** `h(tag, attrs, children)` is the only DOM
constructor; `icon(name)` draws from the in-repo stroke set
(`components.js` `ICONS`, 24-grid, `currentColor`) — add a new glyph as an
in-repo SVG path string, never an icon dependency. Components are
ontology-aware (vocabulary from `GET /meta`, §7).

## 3. Security — `html:` is the only innerHTML sink

[`components.js:15-19`](../../services/api/static/assets/components.js): in `h()`,
`html:` is the **only** attribute that writes `innerHTML`. **Never** pass
draft/LLM-sourced or otherwise untrusted text through it — it is parsed as
markup (XSS). Pass such text as a child (`textContent`, safe) or via `text:`.
`html:` is used today only for static SVG/icon strings. Backed by the strict CSP
at [`main.py:68-94`](../../services/api/main.py) (no inline handlers, no remote
origins — offline-safe by construction).

## 4. The reasoning-trace attribution channel (PLAN-0080)

The trace badge tells a reader **who or what produced a step**. It is driven by
one registry, **not** by sniffing the kind string.

- **The registry:**
  [`trace-kinds.js`](../../services/api/static/assets/trace-kinds.js) —
  `window.OCT_TRACE_KINDS`, a strict-JSON block (between the
  `TRACE_KINDS_JSON_BEGIN/END` delimiters) read by BOTH the browser and the CI
  tripwire. Every engine-emitted kind has one `{label, cls, actor}` row.
- **Two axes, two channels (L-4, Cray-ratified):**
  - `cls` = **mechanism / severity** — the existing `theme.css` semantic classes
    (§1). The demo's current look does not shift.
  - `actor` = **who/what** — carried by a small glyph on the badge, from the
    closed set `{human, llm, engine}`, driven by the `data-actor` attribute.
    Colour NEVER carries the actor.
- **Unmapped degrades honestly (AC-4):** a kind with no row renders its raw token
  in the `.badge.unmapped` style (dashed outline), with **no glyph** and
  `data-actor="unknown"` — an unknown kind has no known actor, and defaulting to
  a machine glyph would assert an attribution we do not have.
- **The rule:** adding an engine trace emission (a raw-dict `{"kind": "..."}` or
  a `ReasoningStep(kind="...")`) **requires** adding a registry row. The CI
  tripwire [`tests/api/test_trace_kind_labels.py`](../../tests/api/test_trace_kind_labels.py)
  AST-scans `services/engine/` + `verticals/` and turns RED on a mismatch — the
  vocabulary cannot rot silently the way the old substring sniff did (14 of 16
  procedure-engine kinds fell to an unattributed neutral badge).

Render via `O.traceBadge(kind)` / the shared `O.reasoningTrace(steps)`; never
re-introduce a local `kindClass`-style sniff.

## 5. No build step + the `?v=` cache-bust

There is **no build step**: edit `services/api/static/` directly — no
`package.json`, no bundler, no JS/CSS linter, no frontend test runner
([`0013-oct-ui-provenance.md:64-65`](../design/0013-oct-ui-provenance.md)). A CI
tripwire for the UI must therefore be a **Python test** (as §4's is).

Because the browser caches the static assets, **bump the `?v=` token in
[`index.html`](../../services/api/static/index.html) on every `assets/*` edit**
(runbook [§6c](../runbooks/run-oct-demo.md), `:700-705`), else a normal reload
serves the stale file. Verify with a cache-busted `fetch` + a runtime probe
(e.g. `window.OCT.ViewStory._probe()`), never "reload = fresh".

## 6. Ontology-driven, not hard-coded

The make-or-break principle
([0013 prompt `:14-18`](../design/0013-oct-demo-claude-design-prompt.md)): entity
types, field labels and enums render from `GET /meta`, **never** from
vertical-specific strings. Swapping the vertical = swapping the ontology +
adapter, with **zero UI-code change**. Energy is only the data that happens to
come back in v1.

## 7. Control-tower tone

A professional **control-tower** product the way a working operator expects one
to feel — **dense, glanceable, calm under load, trustworthy. Not playful, not a
toy dashboard** ([0013 prompt `:37-39`](../design/0013-oct-demo-claude-design-prompt.md)).
High information density without clutter; semantic status colours used
consistently (§1).

## 8. Provenance-class labelling

When a facet field's authority matters, tag it with one of the three provenance
classes at
[`view-procedures.js:23-25`](../../services/api/static/assets/view-procedures.js):
`authoritative-typed` (the typed source of truth, ADR-016 D2-A2),
`advisory-prose` (a non-authoritative note), `llm-assist` (what the LLM
drafts/summarises — advisory). This is the precedent an
LLM-narration layer would extend (PLAN-0080 OQ-1), not the attribution channel.

## 9. The 0013 design prompt (SD-2)

[`docs/design/0013-oct-demo-claude-design-prompt.md`](../design/0013-oct-demo-claude-design-prompt.md)
is a **dated historical record** — the one-shot generation prompt that produced
the UI (its generation-provenance value, PLAN-0013 Steps 3–5, is real). It is
**not** derived (ADR-0017 D6 "derived" = corrected-against-canonical forever,
which inverts reality — the prompt is the *source* of the tone). Its header
carries a one-line pointer to this file as the living home of the design
opinion; its body is untouched (PLAN-0080 SD-2 (iii)).

## 10. Glossary — two different `kind` fields

Do not conflate them:

- **Definition-side `Step.kind`**
  ([`spec.py:54-61`](../../services/engine/procedures/spec.py)) — a `StrEnum`
  (`QUERY = "query"`, …) naming a step's *type*. It **IS** hashed into the
  governance/config pin ([`governance_pin.py:71`](../../services/engine/procedures/governance_pin.py)).
- **Trace-entry `kind`** — the string on a `reasoning_trace` entry, keyed to the
  §4 registry. It feeds **no** hash. (Note: `verticals/` seed executors emit the
  literal `"query"` here — the definition-side token leaking into the trace
  channel; labelled in the registry, tracked as PLAN-0080 F-4, not yet fixed.)
