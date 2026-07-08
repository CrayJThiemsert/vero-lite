# PLAN-0059: Hero-demo KPI stat-tile panel

**Status:** Ready — SD-1…SD-5 ratified as-recommended by Cray (session 114, AskUserQuestion)
**Owner:** both (Claude Code executes; Cray ratifies the surfaced decisions)
**Created:** 2026-07-08
**Related ADRs:** none new — pure frontend composition over the shipped PLAN-0045 ฿-ledger
surface; no governance fork
**Related PLANs:** PLAN-0045 (hero v1 render + ฿ ledger — the plumbing this composes over);
PLAN-0057 (`docs/plans/done/0057-event-triggered-hero-opener.md` — the "demo composition
over already-shipped plumbing" precedent; note 0057 still added a POST route + DB write —
this PLAN is strictly smaller, render-only); PLAN-0058
(`docs/plans/done/0058-whoami-reject-at-login.md` — the frontend-only SD + verification
style mirrored here)

> Authored by the in-harness `plan-drafter` subagent (ADR-013 D1 phased authority;
> ADR-012 D4.3 author≠reviewer disclosure). Outline originator: Cray (session 114
> next-work pick, relayed via the Code dispatch payload). Independent reviewer: Cray at
> PR merge; Code R2-verifies every code citation + commits (the drafter does not commit).
> Separation: INTACT.
> All five Surfaced Decisions (SD-1…SD-5) were **RATIFIED as-recommended by Cray on
> 2026-07-08 (session 114, via AskUserQuestion)** — the ACs/Steps below are the ratified
> shape (PLAN-0058 pattern).

> **This is a build PLAN — no new ADR.** If execution uncovers a design fork that would
> need an ADR, STOP and surface it; do not bake it in.

## Goal

Promote the hero demo's three headline ฿-impact figures — expedite premium, avoided
downtime, net benefit — from the current small label/value rows into a proper **KPI
stat-tile panel** in the hero view. Every number already ships: the deterministic,
Decimal-exact ledger (`verticals/procurement/hero_demo/ledger.py:39-95`
`build_hero_impact_ledger()` — no LLM, no MS-S1), the typed read-only endpoint
(`GET /demo/hero/impact`, `services/api/routers/demo.py:62-65`,
`response_model=HeroImpactLedger` per `services/api/models/demo.py:32-57`), and the
frontend fetch (`O.Hero.impact()` at `services/api/static/assets/view-hero.js:302`,
rendered by `renderLedger()` at `view-hero.js:167-193`). Today the three figures render as
a `.hero-ledger-foot` grid of `kv()` rows (`view-hero.js:176-180`; CSS proto-tile at
`services/api/static/assets/hero.css:130-134`). The gap is **presentation only**: restyle
that block into stat tiles so the ฿ story reads at a glance. **No new ADR, no backend, no
engine change, no payload change** — the exact PLAN-0057 "compose over shipped plumbing"
pattern, one size smaller (0057 added a POST + DB write; this PLAN touches only
`services/api/static/`). Deterministic-offline throughout; no host-state (§8) surface.

## Acceptance Criteria

- [ ] **AC-1 — the three figures render as tiles, from the live payload.** The hero view
      shows a KPI stat-tile panel with the three headline figures (per SD-1), each tile =
      label + ฿ value (+ at most a one-line sublabel per SD-3), populated from the
      **existing** `O.Hero.impact()` fetch (`view-hero.js:302`) — NOT from any hardcoded
      frontend constant (grep proof: no `52,500` / `8.16` / `8.11` ฿ literals added under
      `services/api/static/assets/`). Expected rendered values are **pre-committed** from
      the shipped exact-figure tests (`tests/verticals/procurement/test_hero_ledger.py:53-56`):
      expedite premium `฿52,500` (`thb()`, `view-hero.js:22-26`), avoided downtime
      `฿8.16M` and net benefit `฿8.11M` (`thbM()`, `view-hero.js:27-30`).
- [ ] **AC-2 — no duplication; the ledger cards stay.** The two baseline/governed
      `ledgerSide()` cards (`view-hero.js:183-193`, showing `exposure_thb` ฿9.76M → ฿1.65M
      + detail) remain unchanged, and each of the three headline figures appears exactly
      **once** in the hero view (the tile panel replaces/upgrades the old foot rows per
      SD-4 — no figure rendered twice).
- [ ] **AC-3 — no empty affordances; demo-grade framing kept.** Tiles carry NO trend
      arrow, target line, spark-line, or delta chip (per SD-3 — the one-shot ledger has no
      such data). The provisional/demo-grade framing already on the surface (payload
      `provisional: true`, `models/demo.py:37-39`; ledger docstring stamp `ledger.py:14`)
      stays visible on the card.
- [ ] **AC-4 — frontend-only diff; offline gate green.** The PR diff is confined to
      `services/api/static/**` (view-hero.js + hero.css + index.html). The FULL offline
      suite + ruff + mypy stay green under the required CI `gate` on a fresh PR — the
      untouched exact-figure tests (`tests/api/test_demo_hero_routes.py:34-44`,
      `tests/verticals/procurement/test_hero_ledger.py`) double as proof that no payload
      or backend contract moved. No MS-S1, no live LLM, no host-state action anywhere.
- [ ] **AC-5 — cache-busted preview verification.** Every edited static asset gets a
      bumped `?v=` token in `services/api/static/index.html` (`hero.css?v=c24` at line 17,
      `view-hero.js?v=c32` at line 51 → next; project memory: the preview serves stale
      assets without it). Render verified via `preview_snapshot` + `preview_eval` DOM/
      geometry assertions against the pre-committed AC-1 strings — **not**
      `preview_screenshot`, which times out in this environment (project memory).

## Out of Scope

- ❌ Any new ADR, backend route, engine change, DB write, or ledger/figure change — the
  ledger computation (`ledger.py`) and the `HeroImpactLedger` API contract
  (`models/demo.py:32-57`) are untouched. (PLAN-0057 added a POST + DB write; this PLAN
  deliberately does neither.)
- ❌ The design dossier's **procedure-level KPI / measurement capability**
  (`docs/research/private/2026-06-30-hero-demo-design-dossier.md` §4/§9 — a gitignored
  DISCUSSION DRAFT, not ratified). That is a heavy engine capability needing its own
  ADR + PLANs. This PLAN is only the demo tile-panel over the already-computed
  provisional figures.
- ❌ Any trend / target / historical-series data source (SD-3) — nothing exists to feed
  one; do not fake it.
- ❌ Reusing or modifying view-story's `.pd-tile` idiom (`view-story.js:1679-1690`) or
  its hardcoded `PROC.kpis` mock (`view-story.js:1426`) — the panel must bind to the live
  ledger, never that mock; view-story.js stays untouched (SD-2).
- ❌ Auth, production/business surfaces, real Fastenal figures — everything stays
  demo-scoped under `/demo/hero/` with the `provisional` stamp (`models/demo.py:1-7`).

## Steps

### Step 1: CSS — hero-scoped stat-tile style (`hero.css`)
Per SD-2 (a): evolve the `.hero-ledger-foot` block (`hero.css:130-134`)
into a stat-tile row — boxed tiles (background/border/radius consistent with the existing
`.hero-ledger-side` treatment, `hero.css:122-125`), label above a larger mono ฿ value
(today 16px/700/mono at `hero.css:134` — step up toward the `.hero-ledger-big` 24px scale,
`hero.css:127`), optional one-line sublabel class. Keep the existing ≤640px single-column
collapse (`hero.css:136-138`) working for the new tiles. Hero-scoped classes only — no
shared/global CSS, no view-story import.

### Step 2: JS — tile markup in `renderLedger()` (`view-hero.js`)
Rework the foot block (`view-hero.js:176-180`) to emit the tile markup: per SD-1 the three
headline figures via the existing `thb`/`thbM` formatters (`view-hero.js:22-30`); per SD-3
label + value, plus the SD-1-ratified exposure context sublabel (`฿9.76M → ฿1.65M`) on the
net-benefit tile; per SD-4 this
**replaces** the old `kv()` rows (no duplicate rendering). `ledgerSide()`
(`view-hero.js:183-193`) and the fetch/join flow (`view-hero.js:301-303`) unchanged. Add a
small `tile()` helper beside `kv()` (`view-hero.js:65`) rather than overloading `kv()`.

### Step 3: Cache token bump (`index.html`)
Bump both edited assets' `?v=` tokens: `assets/hero.css?v=c24` (`index.html:17`) and
`assets/view-hero.js?v=c32` (`index.html:51`) → next. One reviewable `feat` PR for
Steps 1–3 (the whole PLAN is XS).

### Step 4: Verify + closeout
Offline: full suite + ruff + mypy green on the PR's required `gate` (AC-4 — the untouched
exact-figure tests are the payload truth; expected: zero test-file diff). Render:
`preview_snapshot` + `preview_eval` on the hero view (`oct-demo-procurement`, fixed port
8096; cache-busted) asserting the three pre-committed strings from AC-1 render in the tile
panel and appear exactly once (AC-2), with pass/fail read fixed BEFORE the run (Lesson
#0026). Then STATUS reconcile + `git mv docs/plans/0059-*.md docs/plans/done/` per
CLAUDE.md §6 Plan Flow.

## Surfaced Decisions

All five surfaced decisions were **RATIFIED as-recommended by Cray on 2026-07-08
(session 114, via AskUserQuestion)**. The recommendation + rationale text is retained
below with the ratified outcome stamped per entry; the ACs/Steps above are the ratified
shape.

- **SD-1 — which KPIs become tiles.**
  *Recommendation:* the three figures already in the payload and already rendered —
  `net_benefit_thb`, `avoided_downtime_thb`, `expedite_premium_thb`
  (`ledger.py:92-94`, `models/demo.py:53-57`, currently `view-hero.js:177-179`); mention
  the baseline→governed `exposure_thb` headline (฿9.76M → ฿1.65M, `ledger.py:82,90`) as
  optional **context** (e.g. a sublabel on the net-benefit tile), not a 4th tile.
  *Rationale (1-line):* the three deltas ARE the "governed sourcing turned a line-stop
  into a decision" beat, and the exposure pair already headlines the two `ledgerSide`
  cards — a 4th tile would render it twice. *Alternative:* a 4-tile row including the
  exposure delta. *Why Cray:* which numbers headline the pitch surface is a demo-narrative
  call, not an implementation detail.
  ✅ RATIFIED 2026-07-08 (Cray, session 114, via AskUserQuestion — as-recommended: the 3
  payload figures as tiles; exposure `฿9.76M → ฿1.65M` as a context sublabel on the
  net-benefit tile, NOT a 4th tile).
- **SD-2 — layout / styling approach.**
  *Recommendation:* **(a)** upgrade the existing `.hero-ledger-foot` (`hero.css:130-134`)
  in place into the stat-tile row. *Rationale (1-line):* it is already a proto-tile (grid,
  label-above-mono-value) at exactly the right spot under the ledger, so (a) is the
  smallest diff, keeps one source for the three figures (dovetails with SD-4's
  no-duplication), and stays hero-scoped. *Alternatives:* (b) a new `.hero-kpi` block
  above/near the ledger — defensible if Cray wants the ฿ story visually promoted above
  the baseline/governed cards, still hero-scoped, slightly larger diff (add block +
  remove the old foot anyway); (c) reuse view-story's `.pd-tile`
  (`view-story.js:1679-1690`) — **recommend against**: that idiom is bound to the
  hardcoded `PROC.kpis` mock (`view-story.js:1426`) and its CSS lives with another view,
  so (c) couples two views and risks wiring the panel to mock data. *Why Cray:* visual
  hierarchy of the hero demo is a presentation-taste call Cray owns.
  ✅ RATIFIED 2026-07-08 (Cray, session 114, via AskUserQuestion — as-recommended: option
  (a), upgrade `.hero-ledger-foot` in place).
- **SD-3 — trend / target affordances on tiles.**
  *Recommendation:* **OMIT** trend/target — tiles show label + ฿ value (+ at most a
  one-line sublabel). *Rationale (1-line):* the one-shot demo ledger has no trend/target
  data (`ledger.py` computes a single deterministic snapshot), and empty affordances read
  as broken, not aspirational. *Alternative:* render placeholder trend chips à la
  view-story's mock — rejected as fake data on a governed-demo surface. *Why Cray:*
  whether the demo may show aspirational-but-unbacked UI is a credibility/positioning
  call.
  ✅ RATIFIED 2026-07-08 (Cray, session 114, via AskUserQuestion — as-recommended: OMIT
  trend/target).
- **SD-4 — replace vs supplement the current foot.**
  *Recommendation:* **REPLACE/UPGRADE** the 3-item `.hero-ledger-foot`
  (`view-hero.js:176-180`) into the tile panel; keep the two baseline/governed
  `ledgerSide` cards (`view-hero.js:183-193`) unchanged. *Rationale (1-line):* a
  supplemental panel would render the same three figures twice on one card — duplication
  with zero information gain. *Alternative:* keep the foot + add a separate panel
  elsewhere in the view — rejected per the duplication point. *Why Cray:* confirms
  removing an existing (small) render element from the ratified PLAN-0045 surface.
  ✅ RATIFIED 2026-07-08 (Cray, session 114, via AskUserQuestion — as-recommended:
  REPLACE/upgrade the foot; `ledgerSide` cards stay).
- **SD-5 — verification bar.**
  *Recommendation:* (i) **binding:** the FULL offline suite green on the PR — the shipped
  exact-figure tests (`tests/api/test_demo_hero_routes.py:34-44` asserts the endpoint
  payload to the satang; `tests/verticals/procurement/test_hero_ledger.py:53-56` asserts
  `52500` / `8160000` / `8107500`) remain the payload truth and MUST stay untouched-green;
  (ii) **render assertion:** `preview_eval` DOM assertions with the pre-committed expected
  strings (`฿52,500`, `฿8.16M`, `฿8.11M` — deterministic because the ledger is fixed-CSV)
  + `preview_snapshot`, per the two baked-in gotchas: bump the `index.html` `?v=` token on
  any `assets/*` edit (preview caches static JS/CSS), and `preview_screenshot` times out
  in this env → use snapshot + eval geometry instead. *Rationale (1-line):* PLAN-0058 SD-4
  established the repo has no JS unit-test harness and that adding one is out of
  proportion for an XS frontend PLAN — so the deterministic offline anchor is the shipped
  payload tests, and the render check is preview-eval with pre-committed values (a fixed
  pass/fail read, Lesson #0026), matching prior practice. *Alternative:* add a minimal JS
  test harness for `renderLedger()` — rejected on the PLAN-0058 proportionality precedent.
  *Why Cray:* confirms the evidence bar matches prior practice rather than silently
  lowering (or raising) it.
  ✅ RATIFIED 2026-07-08 (Cray, session 114, via AskUserQuestion — as-recommended: full
  offline suite with untouched exact-figure tests + preview_eval render assertion; no JS
  harness).

## Open Questions

None — SD-1…SD-5 are ratified (stamps above); every fact in this draft is grounded in an
on-disk citation listed above; Code R2-verifies each citation before commit.

## Verification

**Binding bar:** AC-4 — full offline suite + ruff + mypy green under the required CI
`gate` on a fresh PR (project memory: CI is PR-only; prove green via the PR's checks, full
suite, not a named subset), with zero diff outside `services/api/static/**` and the
shipped exact-figure tests untouched-green as the payload oracle.
**Confirming evidence (render, not a CI gate):** AC-5 — cache-busted `preview_snapshot` +
`preview_eval` on the hero view asserting the three pre-committed ฿ strings render as
tiles exactly once, pass/fail read fixed before the run. Nothing in this PLAN touches
MS-S1 or any host-state (§8) surface.
