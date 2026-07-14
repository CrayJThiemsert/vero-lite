# PLAN-0073: Box-4 `economic_impact` facet into the hero-demo UI

**Status:** Complete
**Owner:** Claude Code
**Created:** 2026-07-14
**Related ADRs:** ADR-0030 (ledger+facet coexist, D2; trust-shape D5 — **no ADR change**), ADR-007 (D2 envelope — **unchanged**, facet stays trace-carried)

> **Author≠reviewer disclosure (ADR-012 D4.3 / ADR-013 OQ-1):** drafted by the
> in-harness `plan-drafter` subagent under ADR-013 D1 phased authority from a
> Code-originated dispatch (target_number 0073, caller-enumerated). Independent
> review: Code R2 + Cray ratification at PR merge. Separation: INTACT.
> All file:line anchors below were re-verified against disk on `main` @ `eeae1c6`
> before citing — every dispatch anchor **confirmed — prior intact** (§6
> verify-loop hygiene; two trivial offsets noted in Grounding).

## Goal

Surface the typed Box-4 `EconomicImpact` facet — with its audit-grade provenance
(`kind` / `basis_refs` / `assumptions` / `provisional`) — in the hero demo's
beat-4 (฿), so the flagship pitch shows the ฿ number **with** its governed
provenance instead of the bare demo ledger. Today beat-4 renders only
`HeroImpactLedger` (`GET /demo/hero/impact` → `build_hero_impact_ledger`); the
facet exists, reuses the *same* ledger computation (numbers already match —
this is provenance wiring, **not new math**), but rides only the reactive and
governed recommender paths — the hero UI render was explicitly deferred by
PLAN-0071 Out-of-Scope. Deterministic-offline throughout; no MS-S1 / host-state
(CLAUDE.md §8). No new ADR: ADR-0030 D2 already ratifies coexistence.

## Grounding (anchors verified on disk, main @ eeae1c6)

- **Beat-4 today = demo ledger only:** `GET /demo/hero/impact`
  (`services/api/routers/demo.py:65`) → `build_hero_impact_ledger`
  (`verticals/procurement/hero_demo/ledger.py:39-95`), typed `HeroImpactLedger`
  (`services/api/models/demo.py:32-57`), rendered by
  `renderLedger`/`ledgerSide` (`services/api/static/assets/view-hero.js:175-202`),
  fetched via `O.Hero.impact()` (`services/api/static/assets/api.js:97`).
- **Hero governance dict carries NO facet:** the projection at
  `verticals/procurement/hero_demo/run.py:546-570` emits governance fields only
  (`run_id`, `po_id`, …, `sod`, `trigger`); model `HeroGovernanceAudit`
  (`services/api/models/demo.py:60-75`) = hero + contrast dicts.
- **The producer reuses the ledger:** `procurement_economic_impact`
  (`verticals/procurement/economic_impact.py:53`) imports (`:36`) and calls
  (`:61`) `build_hero_impact_ledger`, mapping into the engine `EconomicImpact`
  shape (`services/engine/economic_impact.py:50-91`) with `basis_refs` = the
  CSV columns (`:39-44`; comment `:38`), `kind="expedite_tradeoff"`,
  `provisional=True`. Registered via `register_procurement_economic_impact`
  (`:97`). The `net_benefit_thb` validator (`services/engine/economic_impact.py:81-91`)
  enforces the arithmetic.
- **Facet surfaces only on:** reactive — `services/engine/recommender.py:242`
  (`build_economic_steps` appended to the LLM RecommendedAction trace); governed
  — `services/engine/procedures/action_step.py:287-290` (via
  `_compose_action(..., economic_steps=...)`).
- **Why it does NOT reach the hero (two independent reasons):**
  1. The hero-dict projection (`run.py:546-570`) never reads the
     RecommendedAction reasoning trace; the scored-rule wrapper
     (`services/engine/procedures/governance_step.py:222-233`) replaces the
     base output with enriched entities and only appends its own trace entries.
  2. The producer guard `_is_emergency_trigger`
     (`verticals/procurement/economic_impact.py:47-50`) requires
     `event_type~"failure"` OR `severity=="critical"`, but the hero intake seed
     (`run.py:212-243`) carries **neither key** (it has `event_id` /
     `measured_value` / `criticality`) → producer returns `None` →
     `build_economic_steps` returns `[]` on the hero path.
- **No frontend renders the facet today:** grep `economic` across
  `services/api/static/` = zero matches. PLAN-0071 explicitly deferred "any
  operator-UI render of the ฿ step"
  (`docs/plans/done/0071-box4-economic-impact-facet-build.md:247-248`) and kept
  ledger + facet coexisting byte-identical (`:236-238`; ADR-0030 D2).
- **Effort:** S/M. UI risk = static-asset cache → bump `?v=` per touched asset.

## Surfaced decisions (RATIFIED)

> **Ratified by Cray 2026-07-14 via AskUserQuestion, all three as-recommended:**
> **SD-1 = (a) fire for real** · **SD-2 = (b) additive optional field on
> `GET /demo/hero/impact`** · **SD-3 = coexist + provenance toggle +
> always-visible `PROVISIONAL` badge**. SD-4 is a confirm-only contract
> tripwire (no ADR change). The Steps below already reflect these arms.
> Author≠reviewer: `plan-drafter` authored → Code R2 (anchors re-verified on
> disk @ `eeae1c6`; SD-1(a) "one line" confirmed — `event_type` datum already in
> scope at `run.py:208`) → Cray ratified.

### SD-1 — Fire-vs-render: does the facet genuinely FIRE on the hero run path?

- **(a) Fire for real** — enrich the hero intake seed (`run.py:212-243`) with
  `event_type` (and/or `severity`) from the failure event it *already* fetches
  (`run.py:207-208` selects `e["event_type"] == "failure"` — the datum is on
  hand, just not carried into the seed). The producer then fires inside the
  governed run and the facet lands in the persisted run's reasoning trace.
- **(b) Render-side call** — the hero endpoint calls the producer (or
  `build_economic_steps`) directly at read time; numbers already match the
  ledger; cheaper, but the facet never actually rides the hero's governed run.
- **Recommendation: (a)** — consistent with PLAN-0072's "render persisted
  truth" precedent (beat 3 genuinely resolves the gate rather than staging it).
  The seed change is one honest line; (b) would make beat-4's provenance claim
  cosmetically true but path-false. Tradeoff surfaced: (a) touches the run seed
  (regression surface = hero governance tests), (b) touches only the read path.
  **Cray decision because:** it sets the demo's honesty bar — a pitch-narrative
  judgment, not an engineering one.

### SD-2 — Transport: how does the typed facet reach the FE?

- **(a)** Additive field on `HeroGovernanceAudit` / the hero dict
  (`models/demo.py:60-75` + `run.py:546-570`) — PLAN-0072 precedent (`run_id`
  additive at `run.py:547`).
- **(b)** Extend `GET /demo/hero/impact` to return the typed facet alongside
  the ledger (additive optional field on the response model).
- **(c)** New endpoint.
- *(interplay)* Under SD-1(a) the facet also exists in the persisted run's
  trace, reachable via the existing `O.Hero.runDetail()` (`api.js:103`) — the
  maximal render-persisted-truth variant, at the cost of coupling beat-4 to the
  beat-3 run fetch.
- **Recommendation: (b)** — beat-4 already binds to the impact fetch; one
  additive optional field (`economic_impact: EconomicImpact | None`) keeps one
  fetch per beat, `extra="forbid"` models stay honest, and the ledger fields
  stay byte-identical (ADR-0030 D2). (c) is over-machinery. **Cray decision
  because:** (a) vs (b) changes which demo surface carries the ฿ provenance
  story, and the runDetail variant trades simplicity for narrative purity.

### SD-3 — UI render: coexist vs supersede; how much provenance inline?

- **Coexist (recommended):** the ledger card stays (ADR-0030 D2 says coexist;
  PLAN-0071 kept `view-hero.js` byte-identical); add a typed-provenance strip
  under it — `kind` chip, always-visible `PROVISIONAL` badge (s74 trust-shape
  rule inherited per ADR-0030 D5 / PLAN-0071 `:247-248`), and a "show
  provenance" toggle (reuse the existing reasoning-trace toggle idiom) revealing
  `assumptions[]` + `basis_refs` in full.
- **Alternatives:** facet supersedes the ledger card (contradicts D2 coexist —
  would need explicit ratification); full provenance inline, no toggle (heavier
  card, but nothing hidden in a pitch).
- **Recommendation:** coexist + toggle + always-visible badge. **Cray decision
  because:** it is the pitch-facing look of the flagship's ฿ beat.

### SD-4 — Contract-change tripwire (confirm-only)

Draft-time check says **no ADR-007 / ADR-0030 contract change is needed**: the
facet stays a trace-step payload (ADR-0030 D1/SD-1 — engine docstring
`economic_impact.py:50-56` confirms non-envelope), and every transport option
above is additive on demo-scoped models. **Binding tripwire:** if execution
finds any step requiring an ADR-007 D2 envelope change or an ADR-0030 edit, the
PLAN **halts** and routes to ADR drafting (G1/G2; Cowork/plan-drafter path) —
no silent contract drift.

## Acceptance Criteria

- [ ] **AC-1 (facet served + correct ฿):** deterministic test — the SD-2 chosen
  transport returns a typed `EconomicImpact` with `kind="expedite_tradeoff"`,
  `provisional=True`, non-empty `assumptions` + `basis_refs` (the 4 CSV
  columns), and `net_benefit_thb` **equal to** the ledger's `net_benefit_thb`
  from the same response cycle (validator-backed; no float drift).
- [ ] **AC-2 (fires on hero path — applies iff SD-1 = (a)):** deterministic
  test — `build_economic_steps(seed, "procurement")` on the *actual* hero
  intake seed returns exactly one `economic_impact` step; plus the hero run's
  persisted trace carries it (regression: contrast/calm paths still facet-free
  per OQ-C — a non-emergency event still yields `None`).
- [ ] **AC-3 (coexistence / no regression):** the existing `HeroImpactLedger`
  fields are byte-identical in the response; `tests/api/test_demo_hero_routes.py`,
  `tests/verticals/procurement/test_hero_ledger.py`, and
  `tests/services/engine/test_economic_impact_producers.py` pass **unmodified**
  (except additive new cases).
- [ ] **AC-4 (FE render):** beat-4 shows the ฿ figure with `PROVISIONAL` badge
  + provenance per SD-3; verified via `preview_snapshot` + `preview_eval`
  (NOT `preview_screenshot` — known timeout on oct-demo); every touched static
  asset gets a `?v=` bump.
- [ ] **AC-5 (hygiene):** full suite + `ruff` + `mypy` green on the branch;
  after merge, full suite re-run on the **merge commit** (CI is PR-only — the
  merge commit is never tested by CI).

## Out of Scope

- ❌ Beat-1 NL query — untouched.
- ❌ **Any ADR change** — ADR-0030 and ADR-007 stay verbatim (SD-4 tripwire
  halts the PLAN if that proves false).
- ❌ Retiring / generalizing `HeroImpactLedger` — unless SD-3 explicitly picks
  supersede (which would itself need ADR-0030 D2 re-ratification).
- ❌ New auth surface — beat-4 stays read-only demo-scoped.
- ❌ Non-procurement verticals' ฿ facets in any UI; multi-currency (ADR-0030
  OQ-4); ROI aggregation; per-event PO anchor resolution (OQ-C v2).
- ❌ Operator-UI (non-hero) render of the facet — still deferred.

## Steps

### Step 1: Plan-first read + pre-committed pass/fail read
Read the result-producing code end-to-end (`demo.py` route, `run.py` seed +
projection, `economic_impact.py` producer + helper, `view-hero.js` beat-4).
Fix the pass/fail read **before** any run: AC-1..AC-3 test names + the exact
grep/assert per SD outcome. Cheapest gate first (unit tests, no server).

### Step 2: RED tests
Write AC-1/AC-2/AC-3 tests per the ratified SD-1/SD-2 arms; confirm RED for
the new behavior and GREEN for the untouched ledger baseline.

### Step 3: Backend wiring
Per SD-1(a): carry `event_type` from the already-fetched failure event into the
intake seed (`run.py:212-243`). Per SD-2(b): additive optional
`economic_impact` field on the impact response model + route (`demo.py:65`),
sourced per the ratified arm. Decimal serialization parity with the ledger
(pydantic Decimal→str) asserted in AC-1.

### Step 4: Frontend render
`view-hero.js` beat-4 provenance strip per SD-3 (badge + toggle + `kind` chip);
`api.js` unchanged if SD-2(b) (same fetch). Bump `?v=` on every touched asset.
Verify via `preview_snapshot` + `preview_eval` geometry/content checks.

### Step 5: GREEN + evidence + PR
Full suite + ruff + mypy; capture fresh on-disk evidence (test output paths) in
the PR body (`--body-file`); feature branch → PR → merge; re-run the full suite
on the merge commit (AC-5).

## Verification

AC-1..AC-3 are deterministic pytest (offline, no MS-S1); AC-4 is a
preview_eval-verified render check; AC-5 is suite + lint + type + merge-commit
re-run. Pass/fail reads are fixed in Step 1 before any run; a passed re-check
of prior ledger behavior is logged `confirmed — prior intact`.

## Open Questions (R2)

- **OQ-1:** Does the event-fired hero path (`build_event_hero_governance_audit`,
  `run.py:573-584`, PLAN-0057) need the same seed/trigger enrichment for the
  producer to fire there too, or is beat-4 fed only by the offline builder?
  Probe empirically in Step 1 (don't infer from shape).
- **OQ-2:** Under SD-1(a), does enriching the seed with `event_type` perturb
  any shipped executor/rule that reads unknown seed keys? (Expected no —
  additive key; confirm via the full-suite RED baseline.)
- **OQ-3:** Should the FE provenance toggle share state with the existing
  reasoning-trace toggle or be independent? (Cosmetic; default independent.)
