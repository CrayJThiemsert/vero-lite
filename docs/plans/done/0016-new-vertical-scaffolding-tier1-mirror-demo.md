# PLAN-0016: `vero-lite new-vertical` Scaffolding — Tier-1 Mirror-Demo Generator

**Status:** Done (2026-06-04, session 37 — see Completion below)
**Owner:** Claude Code (Tier 2 executes; Cowork drafted per ADR-009 D1)
**Created:** 2026-06-04
**Related ADRs:** ADR-015 (2-tier onboarding posture — merge before this plan's implementation PR), ADR-006 (plugin architecture; L2 `new-vertical` forward-declaration; D4 Rule of Three), ADR-008 (YAML contract; D1 five base types; D3 geo = lat/lng floats), ADR-010 (IN-4 rule fail-safe — the path the demo uses with MS-S1 off)

> **Concrete test case:** the Cray-ratified **aquaculture pond water-quality
> control tower** (partner-input package:
> `docs/research/private/2026-06-04-vertical3-pick.md` §4). The plan is
> generic; aquaculture is its end-to-end proof.
> **Layering (ADR-015 D5, live co-creation):** this plan is the
> **scaffolding ENGINE** — the substrate the partner-facing intake face
> calls. The intake UX (A2 guided form / A3 conversational / hybrid, incl.
> the mandatory human review/edit of the LLM-drafted ontology) is
> **forward-declared as PLAN-0017** and is deliberately NOT part of this
> plan; its full draft is its own dispatch after ADR-015 is accepted.
> **Drafted uncommitted** by Cowork (ADR-009 D1); no code/YAML/.env written
> during drafting. All file:line evidence below verified live 2026-06-04
> against the WSL working tree (dispatch reference HEAD `fbbf129`).

## Goal

Ship the Tier-1 "Mirror demo" generator decided in ADR-015 D2: a single
scaffolding command, `vero-lite new-vertical <namespace>`, that takes the
four partner inputs (ontology, data description, problem, decision) and
stitches the BUILD steps around the existing AUTO generator to produce a
runnable, fully-skinned 3-feature OCT demo — proven end-to-end by bringing
up the `aquaculture` vertical from the research §4 package, including the
one real engine gap the pick surfaced (recommender threshold **direction**).

## Acceptance Criteria

- [ ] **AC-1 (headline — aquaculture end-to-end):** with
      `OCT_VERTICAL=aquaculture` and MS-S1 **off** (rule path; ADR-010
      IN-4), `uvicorn` boots and: (a) the map renders the farm geo from
      ontology lat/lng; (b) NL query "which ponds are low on DO right now?"
      answers from live state; (c) the synthetic tail-beat breach
      (`POND-07`, DO **3.2 mg/L**, ~02:00, `severity=critical`) triggers
      the recommender and proposes `start_emergency_aerator` with a
      coherent below-direction reasoning trace; (d) approve → execute
      (echo) completes the lifecycle.
- [ ] **AC-2 (no regression):** `OCT_RECOMMEND_DIRECTION` defaults to
      `above`; energy + supply_chain behavior is preserved exactly —
      existing test suite green with **no** `.env` changes to those
      verticals.
- [ ] **AC-3 (direction tests):** unit tests cover the `below` path
      (fires below threshold, silent above it) and assert the trace
      summary / action description wording is direction-correct (no
      hardcoded `>=` / "crossed").
- [ ] **AC-4 (demo anchor):** under `OCT_DEMO_TIME_ANCHOR=true`, a
      below-direction breach is selected as the anchor event (see Step 0 —
      `demo_events._breach_event`).
- [ ] **AC-5 (generator untouched):** `vero-lite validate` + `generate`
      are invoked unchanged — **no new generator features** (confirms the
      research Gate-3 claim for the codegen path).
- [ ] **AC-6 (scaffold completeness):** the command produces all four
      BUILD outputs (synthetic adapter, adapter `__init__.py`, `handlers.py`
      echo stub, env block) + registration; ruff clean, mypy clean, type
      hints + tests per CLAUDE.md §8.

## Out of Scope

- ❌ **Tier-2 real-data path** — real `DataAdapter` (CSV/DB/API), dbt/SQLMesh
  mapping layer, PDPA-safe ingestion. Task (C) deep-research → future
  ADR/PLAN (ADR-015 D1 gate).
- ❌ Real (non-echo) action handlers — partner-specific Tier-2 work.
- ❌ `statusClass()` regex generalization beyond what aquaculture's enums
  need (`services/api/static/assets/api.js:113-120` — extend for
  aquaculture's enum vocabulary only, e.g. `fallow`/`harvested`; the
  general fix is per-vertical one-liners per ADR-015 risk note).
- ❌ Productionizing the LLM-ontology-drafting step (human review stays
  mandatory).
- ❌ `geo` property type — geo stays lat/lng floats per ADR-008 D3.
- ❌ **The live-co-creation intake face** (A2/A3/hybrid UX, LLM-extraction
  intake, ontology review/edit UX) — **PLAN-0017**, forward-declared only
  (ADR-015 D5 / OQ-4).
- ❌ **Demo-shell LLM-status surface** (read-only `GET /llm/status` + in-UI
  MS-S1 warm/sleep for the demo operator) — **PLAN-0018**, forward-declared
  in ADR-015 Consequences (may fold into PLAN-0017).

## Steps

### Step 0 ⭐ REQUIRED engine prerequisite — recommender threshold direction

**The one real engine gap the pick surfaced.** It is an
**engine/recommender** change, distinct from the generator (codegen) and
the scaffolding command — its own step, PR-able first. Evidence (verified
live 2026-06-04):

| Site | Today | Change |
|---|---|---|
| `services/api/config.py:114-136` (`OCT_RECOMMEND_*` block) | no direction setting exists (grep-confirmed) | add `oct_recommend_direction ∈ {above, below}`, **default `above`** |
| `services/engine/recommender.py:94` (`_is_recommendation_trigger`) | `measured >= settings.oct_recommend_threshold` | direction-aware comparison |
| `services/engine/recommender.py:199-204` (`_rule_recommend` guard) | `if measured is None or measured < threshold: return None` | direction-aware guard |
| `services/engine/recommender.py:215` (trace summary) | hardcodes `>= threshold` | parametrize per direction |
| `services/engine/recommender.py:233-235` (action description) | hardcodes "crossed the … threshold" | direction-correct wording (e.g. "fell below") |
| `services/engine/demo_events.py:43-64` (`_breach_event`, comparison at line 59) | `e["measured_value"] >= threshold` | direction-aware anchor selection |

The `demo_events.py` site is a **drafter-verified addition** beyond the
dispatch's two recommender sites: without it, `OCT_DEMO_TIME_ANCHOR` never
selects a below-direction breach as the anchor, so the demo's "now" beat
breaks (AC-4). Rationale for physics: energy breaches **above** (over-temp
≥ 90 °C); aquaculture DO breaches **below** (3.2 < 4 mg/L) — the current
engine, including the rule path the demo uses with MS-S1 off, will not fire
for a DO crash. Keep it an **env knob** consistent with the other
`OCT_RECOMMEND_*` settings; the contract question is parked as ADR-015
OQ-3. Tests per AC-2/AC-3/AC-4.

### Step 1: Scaffolding command skeleton

`vero-lite new-vertical <namespace>` in `services/engine/cli.py`
(alongside `validate`/`generate`, `cli.py:36-51`). Orchestrates: input
intake (ontology YAML + problem + decision texts) → `validate` + `generate`
(AUTO, unchanged) → Steps 2–4 BUILD outputs → prints the run checklist.
Re-runnable; refuses to clobber an existing `verticals/<namespace>/` without
an explicit flag.

### Step 2: LLM-generated synthetic adapter

Generate `verticals/<ns>/data_adapter/synthetic.py` from ontology +
problem statement — domain-plausible records incl. the **tail-beat breach
event** (aquaculture: `POND-07` DO 3.2 mg/L @ ~02:00, per the run-oct-demo
tail-beat convention). Output is **draft-for-human-review** (SOTA
consensus; ADR-015 risk note). Adapter dict keys MUST match ontology
property names (engine does zero field translation —
`services/engine/data_adapter.py:25-69` Protocol).

### Step 3: Templated boilerplate

From the energy/supply_chain patterns (near-identical today, fact-pack §3):
`data_adapter/__init__.py` (~60 lines), `handlers.py` (~30-line `echo`
stub closing propose→approve→execute), and the env block —
`OCT_VERTICAL`, `OCT_RECOMMEND_THRESHOLD/ENTITY_TYPE/ENTITY_ID_FIELD/LABEL`,
**`OCT_RECOMMEND_DIRECTION`** (aquaculture: `below`), `OCT_RECOVERY_VALUE/
DESCRIPTION` (aquaculture sketch values: research §4(d)).

### Step 4: Registration — trade-off call

Options for `services/api/main.py:36-39` `_VERTICAL_REGISTRARS`:

| Option | Pros | Cons |
|---|---|---|
| **Code-mod the explicit dict (recommended)** | preserves the deliberate OQ-6 "no import-scan discovery" decision; 2 imports + 1 row; trivially idempotent | scaffolder edits engine-owned file |
| Switch to plugin discovery | zero-touch adds | reverses OQ-6 without need; import-scan magic; bigger blast radius |

**Recommendation: code-mod.** Revisit discovery at `_template/` extraction
(Rule of Three) — by then 3+ registrar rows give the pattern. Code may
override in the implementation PR with rationale.

### Step 5: Aquaculture end-to-end instance

Author `verticals/aquaculture/` ontology per the research §4(a) sketch
(5 base types `Pond`/`Farm`/`OperationalEvent`/`Alert`/`RecommendedAction`
+ `AlertEventLink` join per ADR-008 D4; geo = lat/lng floats on `Farm`),
run the command, then execute AC-1 end-to-end. Extend `statusClass()` only
as aquaculture's enums require (Out-of-Scope note).

### Step 6: Docs + closeout

Vertical README (`verticals/aquaculture/README.md`), run-oct-demo runbook
entry for the aquaculture walkthrough, STATUS update, `git mv` this plan to
`done/` on completion (Code's lane throughout, ADR-009 D2).

## Verification

- **AC-1:** scripted/manual demo walkthrough with MS-S1 off (rule path
  first render), per the run-oct-demo runbook; map + NL query + DO-crash
  recommendation w/ trace + approve→echo-execute observed.
- **AC-2/AC-3/AC-4:** `pytest` — existing suite green untouched; new
  direction tests (both directions × trigger/guard/wording/anchor).
- **AC-5:** diff shows no `code_generator.py` feature changes.
- **AC-6:** `ruff` + `mypy` clean; pre-commit (incl. L1 `check-jsonschema`
  on `verticals/aquaculture/ontology/*.yaml`) passes.

## Completion (2026-06-04, session 37)

All steps shipped; the `vero-lite new-vertical` engine is live and proven
end-to-end on the aquaculture pick.

| Step | PR | Notes |
|---|---|---|
| **0** — recommender threshold direction | #154 | `OCT_RECOMMEND_DIRECTION ∈ {above, below}`, threaded + tested (session 36) |
| **1, 3, 4** — command skeleton + templated boilerplate + registration code-mod | #156 | `services/engine/scaffold.py` + the `new-vertical` Typer command; role detection (Site = geo-bearing; Asset = the other event ref target); idempotent `_VERTICAL_REGISTRARS` code-mod; clobber guard |
| **2** — synthetic adapter | #156 (deterministic) + #160 (LLM) | **Sequencing call:** a deterministic, minimal-but-runnable `synthetic.py` ships first (the command always produces a runnable vertical, CI stays deterministic); the **opt-in `--llm`** MS-S1 draft (richer records, semantically validated, deterministic fallback) layers on top — live-verified against `qwen3.6:35b`. Both render through one shared renderer. |
| **5** — aquaculture end-to-end (AC-1) | #159 | `verticals/aquaculture/` authored + scaffolded by the command; the DO-crash timeline human-reviewed (POND-07 DO 3.2 mg/L, below-direction). AC-1 proven by unit/integration tests **and** a live HTTP smoke (`GET /recommendations` → the pond-07 below-direction recommendation). |
| **6** — docs + closeout | this PR | `verticals/aquaculture/README.md` (generated), the run-oct-demo §3a aquaculture walkthrough, STATUS reconcile, and this `git mv` to `done/`. |

**Acceptance criteria:** AC-1 (aquaculture end-to-end) ✅ live; AC-2 (no
regression, default `above`) ✅; AC-3 (direction tests) ✅; AC-4 (demo anchor)
✅ (Step 0); AC-5 (generator untouched — `validate`/`generate` invoked
unchanged) ✅; AC-6 (scaffold completeness; ruff + mypy + tests) ✅. Full suite
**1162 passed / 2 skipped**.

**`statusClass()` note (Out-of-Scope item):** no aquaculture extension was
needed — `fallow`/`harvested` render `s-neutral`, the accepted fallback for
benign non-active states (ADR-0015 risk note).

**Forward:** the live-co-creation intake face that calls this engine is
**PLAN-0017** (drafted, OQ-4 = hybrid ratified); the demo-shell MS-S1 status
surface is **PLAN-0018** (forward-declared, standalone).

---

*Drafter numbering check (Cowork, 2026-06-04): `docs/plans/` active =
0004/0010/0012, `done/` tops at 0015 → **0016 free**, no collision.
ADR side: 0014 is WITHDRAWN, 0013 latest accepted → companion ADR takes
**0015**.*
