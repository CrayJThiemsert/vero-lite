# PLAN-0039: Read-only 5-facet procedure viewer (ADR-0024 PLAN-α)

**Status:** Ready for execution (Cray-ratified 2026-06-25, session 78; the 7 Open Questions adjudicated — all recommendations ACCEPTED)
**Owner:** Claude Code
**Created:** 2026-06-25
**Related ADRs:** ADR-0024 (D8 one review surface, read-mode ↔ edit-mode, read-only ships first; D2-A2 facet non-authoritative; D6 draft-/read-loadable framing), ADR-016 (D2 `Step` grammar + the 2026-06-25 typed-`facet:` amendment — the data this renders), ADR-0019 (watch→gated / determinism invariant — **rendered, not enforced** here), ADR-006 (D4 Rule-of-Three), PLAN-0017/PLAN-0033 (the console + colour-legend precedent), PLAN-0038 (the typed `facet:` field this viewer reads).

> **Provenance / author≠reviewer disclosure (ADR-012 D4.3).** Outline originator = Cray (session-78 sequencing, ratified: PLAN-0039 read-only viewer first, then PLAN-0040 generator) + ADR-0024 **D8** (one surface, read-only-first). Drafter = Cowork (Tier-1 governance authoring, ADR-009 D1 interim per ADR-013 phased relocation). Reviewers = Cray (ratification) + Code R2 (commit). The substance was **not** self-deliberated in Cowork's own free-form mode — it descends from ADR-0024 D8 + the Code-run panel + Cray's scope calls — so the independent-deliberation check is exercised. Drafted **uncommitted**; Code commits via a `docs/*` PR (ADR-009 D2). **Cowork does not git.**

---

## Goal

Ship a **read-only, zero-LLM** view in the oct-demo console (`services/api/static/`) that renders **every shipped procedure** — all five across the four verticals (`energy`, `supply_chain`, `aquaculture`, `procurement`) — loaded via `load_procedures` (`services/engine/procedures/spec.py`), **decomposed by its five facets per step** (`input · decision_condition · llm_assist · output · governance`), with the **authoritative typed band visually distinguished from non-authoritative prose** (ADR-016 D2-A2), served by a new read-only `GET /procedures` JSON endpoint. No mutation, no persistence, no model call. It is built as the **read-mode of the one component** PLAN-0040 extends to edit-mode (ADR-0024 D8), so the rendering it de-risks is reused, not thrown away.

## Fact-pack findings (verified against the live repo — Tier-1 rule #4)

These shape the acceptance criteria and correct two count/scope assumptions; surfaced rather than silently absorbed.

1. **Five procedures, not four.** `procurement/procedures.yaml` ships **two** procedures — `emergency_sourcing_round` (AT-2, 7 steps) **and** `low_stock_reorder_round` (AT-3, 3 steps). The render target is **5 procedures across 4 verticals**, not "the four procedures." Energy / supply_chain / aquaculture ship one each. AC and the demo evidence use the count **5**.
2. **AT-2 is rendered here, even though AT-2 *generation* is deferred (ADR-0024 D7).** D7 defers AT-2 *generation* to a future PLAN; the read-only viewer must still **display** the existing `procurement.emergency_sourcing_round` AT-2 spec (it is real, shipped data). "AT-2 deferred" ≠ "don't render AT-2." This viewer is the one place AT-2's 7-step governance ladder is shown end-to-end.
3. **This is the console's first multi-vertical surface.** The runtime console is **single-vertical**: `/meta`, `/objects`, `/recommendations` all serve the `OCT_VERTICAL`-selected vertical. The procedure viewer is explicitly **all four** — it must iterate `registry.verticals()` (the ADR-0023 discovery registry), not key off `OCT_VERTICAL`.
4. **All six `gate_kind`s appear in the live data** — `env_band` (energy/supply_chain judge), `in_file_band` (aquaculture/procurement judge), `scored_rule` (procurement source), `rule_gate` (procurement compliance), `doa_tier` (procurement approve), `none` (every query/most actions). The renderer's `gate_kind` handling gets full real-data coverage with zero fixtures.
5. **`facet.input` (prose `str`) is distinct from `Step.input` (`StepInput` `from`/`where`).** `spec.py` flags this type difference intentionally. The "input" facet cell must show **both**: the typed `from`/`where` fan-out (authoritative structure) and the prose `facet.input` note (non-authoritative) — a concrete instance of the typed-vs-prose split (LOCKED-4).

## Acceptance Criteria

- [ ] **AC-1 — read-only endpoint.** A new `GET /procedures` (FastAPI, `services/api/`) returns every discovered vertical's procedures by looping `registry.verticals()` → `load_procedures(v)`. JSON, **read-only — no DB, no mutation, no LLM**. It carries a Pydantic **response model** with `Field(description=...)` on its fields (CLAUDE.md §8 code-quality), mounted via `app.include_router` **before** the static catch-all mount.
- [ ] **AC-2 — real data, all five.** All **5** procedures render (`energy`×1, `supply_chain`×1, `aquaculture`×1, `procurement`×2) from the real `verticals/*/procedures.yaml` — **no fixtures, no synthetic procedures** (LOCKED-2).
- [ ] **AC-3 — per-step 5-facet decomposition.** Every `Step` is shown by its five facets — `input · decision_condition · llm_assist · output · governance` (LOCKED-3).
- [ ] **AC-4 — typed-authoritative vs prose-non-authoritative, first-class.** The typed source-of-truth fields (`threshold`/`direction`/`watch_margin`/`handler`/`autonomy`/`tiers`/`facet.decision_condition.gate_kind` + `Step.input` `from`/`where`) render as **authoritative**, visually distinct from the non-authoritative facet prose (`facet.input`/`output`/`governance`, `facet.llm_assist`) — ADR-016 D2-A2 / LOCKED-4. Concretely: aquaculture (`4.0`/`below`/`1.0`) and procurement (`0.8`/`above`/`0.2`; `100.0`/`below`) `judge` steps show the in-file band as authoritative; energy/supply_chain `judge` show `env_band` + `env_var: OCT_RECOMMEND_THRESHOLD`; the prose notes render as secondary/advisory.
- [ ] **AC-5 — all six gate_kinds.** `env_band`, `in_file_band`, `rule_gate`, `scored_rule`, `doa_tier`, `none` all render correctly (full coverage is present in the live data, finding #4).
- [ ] **AC-6 — zero-LLM, no mutation.** The view loads and renders with **MS-S1 cold** — no `/warm`, no `/llm/*`, no model dependency; and performs **no write / mutation / persistence** anywhere (LOCKED-1). `facet` is rendered as loaded; the engine still does **not** consume it at runtime (D2-A4 holds).
- [ ] **AC-7 — the edit-mode seam is explicit (the de-risk deliverable).** The component exposes a `mode: 'read' | 'edit'` parameter **and** a pure `facetModel(step)` decomposition that tags each field with its provenance class — so PLAN-0040 grafts edit-mode onto the **same** component without a rewrite (LOCKED-5). v1 ships **read-mode only**; the edit path is structurally present but inert.
- [ ] **AC-8 — reuse the colour legend.** Reuses the existing provenance/kind palette (`s-crit`/`s-warn`/`s-ok`/`s-info`/`s-neutral`; `O.badge`, `Onto.statusClass`, the `view-flow`/`view-anomaly` `kindClass` family) — **no new palette invented**; at most **one** added "authority vs advisory" distinction if the typed-vs-prose split genuinely needs it (LOCKED-6).
- [ ] **AC-9 — archetype header.** Each procedure shows its archetype label (`AT-1` / `AT-1b` / `AT-2` / `AT-3`) as a header, sourced explicitly from the catalog mapping (`docs/conventions/procedure-archetypes.md`) — see OQ-5 for the *how*.
- [ ] **AC-10 — offline oracle is the gate.** A backend test asserts `GET /procedures` returns every discovered vertical's procedures and that each payload round-trips `load_procedures` (CLAUDE.md §8 — the offline test is the gate; a live preview/screenshot is **evidence**, not the gate).

## Out of Scope

- ❌ Edit mode / any mutation / write-back into `verticals/<name>/procedures.yaml` (→ PLAN-0040).
- ❌ Any LLM call / generation / archetype *classification* (→ PLAN-0040). This viewer **displays** the catalogued archetype; it does not infer it.
- ❌ The `ArchetypeTemplate` artifact, the restricted draft type (`StepDraft`/`ProcedureDraft`), the prose-lint, the `governance_todo` worklist (→ PLAN-0040).
- ❌ Running a procedure / orchestrator changes / any `validate_runnable` / `validate_governance_complete` work (read-only viewer; OQ-1 of ADR-0024 is PLAN-0040's).
- ❌ Facet **runtime consumption** — the engine still does not read `facet` to drive behaviour (D2-A4 holds).
- ❌ A template-management / CRUD UI; persisting view state; any DB.
- ❌ AT-2 *generation* (D7) — note this is distinct from **rendering** the existing AT-2 spec, which is **IN** scope (finding #2).

## Surfaced — Open Questions for Cray (options + recommendation; Cray ratifies)

Per ADR-0024 D8 most of the shape is LOCKED; these are the residual UI/endpoint forks. **Disposition (Cray, 2026-06-25 ratification): all seven recommendations below are ACCEPTED** — they are the decisions PLAN-0039 builds to (a recommendation stands unless the build surfaces new evidence to revisit it).

- **OQ-1 — view slot.** A new console view vs extending an existing one. **Recommendation: a NEW view, key `F`, label "Procedures"** in the nav (`app.js` `VIEWS` map). Verified: **no** existing view renders procedures/facets (Views A–E = Map / Anomaly / Ask / Flow / Intake), the registration pattern is cheap (a `VIEWS` entry + a `window.OCT.ViewProcedures` module + an `index.html` include), it leaves A–E untouched, and it gives PLAN-0040 a stable home to graft edit-mode.
- **OQ-2 — per-step facet layout.** A 5-column table per step vs a per-step **card** with five facet rows vs another shape. **Recommendation: a per-step card with five facet rows**, each row provenance-tagged. Rationale: a card pre-figures PLAN-0040's three-zone edit layout (LLM-drafted / author-required / archetype-expectation) far better than a flat 5-column table, which cramps the typed-vs-prose distinction (AC-4). The `decision_condition` and `governance` rows surface the typed authoritative values prominently with the prose note secondary; `llm_assist` reads as advisory.
- **OQ-3 — multi-vertical presentation.** All four verticals in one view with a selector, vs one at a time. **Recommendation: a two-level nav — a vertical selector (default = the active `OCT_VERTICAL`) → the vertical's procedure list → one procedure's steps rendered at a time.** Rationale: the unit is the **procedure**, not the vertical (procurement has two — finding #1), and AT-2 is dense (7 steps × 5 facets); one-procedure-at-a-time keeps the surface focused (mirrors ADR-0024 D8's "one review surface").
- **OQ-4 — the "one component, two modes" SEAM (load-bearing — the de-risk deliverable).** What is the explicit structural contract that lets PLAN-0040 add edit-mode without a rewrite? **Recommendation: name two things — (a) a `mode: 'read' | 'edit'` parameter on `ViewProcedures.mount` and on the step renderer; (b) a pure `facetModel(step)` function that maps a `Step` → the five-facet view-model, tagging each field with a `provenance` class (`authoritative-typed` | `advisory-prose` | `llm-assist`) and an `editable` flag (always `false` in v1).** Read-mode renders every field static; PLAN-0040 sets `mode: 'edit'`, flips `editable` on the H-class (human-author) governance fields, and reuses `facetModel` unchanged. The seam is `facetModel` + the `mode`-parameterized renderer — built in v1, exercised in PLAN-0040.
- **OQ-5 — archetype label (the *how*).** Show the per-procedure archetype as a header (recommended), but the archetype is **not** stored in `procedures.yaml` — it lives in the catalog (`docs/conventions/procedure-archetypes.md`). Options: (a) an explicit `procedure_id → archetype` map **in the backend endpoint**, sourced from the catalog; (b) a heuristic derivation from the `gate_kind` sequence; (c) a hard-coded map in the JS. **Recommendation: (a)** — a small explicit map in the `/procedures` endpoint, cited to the catalog, surfaced read-only. It keeps the derived fact server-side in one place and avoids the fragility of (b). **Flag:** the archetype is a **catalog-derived annotation** (canonical = the catalog, CLAUDE.md §4 canonical→derived); the map is a derived mirror — if the catalog grows (a 5th vertical), the map is updated additively, never the reverse.
- **OQ-6 — backend endpoint shape.** One endpoint (all verticals) vs per-vertical; where it mounts. **Recommendation: ONE `GET /procedures`** returning `{ verticals: [ { vertical, namespace, version, agents, procedures: [ { …procedure…, archetype } ] } ] }` — the per-vertical `VerticalProcedures` model dumped (`.model_dump()`) plus the archetype label per procedure (OQ-5). New router `services/api/routers/procedures.py`, `app.include_router`'d in `main.py` alongside the others (before the static catch-all). Read-only, JSON, no DB. The frontend gets one fetch and does its own vertical/procedure nav (OQ-3).
- **OQ-7 — acceptance / demo evidence.** What proves PLAN-0039 done. **Recommendation:** (i) all **5** procedures render decomposed by their five facets on real data; (ii) typed-authoritative vs prose-non-authoritative visually distinct (AC-4); (iii) zero-LLM — renders with MS-S1 cold (AC-6); (iv) the `mode`/`facetModel` seam is present and a read render path PLAN-0040 can extend (AC-7); (v) the offline gate — the `GET /procedures` test (AC-10) is the **gate**; a preview/screenshot of the four verticals' procedures is **evidence**, not the gate (CLAUDE.md §8). Tie demo sign-off to (i)–(iv), CI to (v).

## Steps

### Step 1: Read-only `/procedures` backend endpoint
- New `services/api/routers/procedures.py` with `router = APIRouter(tags=["procedures"])` and `@router.get("/procedures", response_model=ProceduresResponse)`.
- Handler loops `registry.verticals()` (ADR-0023 discovery registry) → `load_procedures(v)` → serialize each `VerticalProcedures` (`.model_dump()`), attaching the `archetype` label per procedure from the catalog map (OQ-5).
- Define `ProceduresResponse` (+ nested models) as Pydantic with `Field(description=...)` per CLAUDE.md §8. **Read-only — no DB, no mutation, no LLM.**
- `app.include_router(procedures_router)` in `services/api/main.py`, before the `StaticFiles` catch-all mount (so the API route wins, matching the existing `/meta`/`/objects`/`/recommendations` pattern).

### Step 2: `ViewProcedures` component (read-mode) + the `facetModel` seam
- New `services/api/static/assets/view-procedures.js` — an IIFE exposing `window.OCT.ViewProcedures = { mount }`, `mount(container, { mode = 'read' } = {})`.
- Implement the pure `facetModel(step)` → the five-facet view-model, each field tagged `{ provenance, editable: false }` (OQ-4). `renderStep(stepModel, { mode })` renders static text in read-mode; the `edit` branch is the inert seam.
- Add `O.API.procedures = () => request('GET', '/procedures')` in `api.js` (and, to keep the degraded-mode demo honest, an optional `mock.js` entry returning the bundled four verticals — or explicitly no mock if the view should show a clean "backend required" state offline; Code's call at build, note it).

### Step 3: Register the view (nav + include)
- Add a `VIEWS` entry `F: { key: 'F', label: 'Procedures', icon: '<icon>', mod: () => O.ViewProcedures }` in `app.js` (OQ-1). Add a `procedures`/`workflow` icon to `components.js` if none fits; otherwise reuse `flow`/`spark`.
- Add `<script src="assets/view-procedures.js?v=cNN"></script>` before `app.js` in `index.html`, and **bump the shared `?v=` cache-bust token** (currently `c13`) on this and the co-edited assets (per the index.html cache-bust note).

### Step 4: Typed-vs-prose + archetype rendering
- Per-vertical selector (default active vertical) → per-procedure list → a procedure card with the **archetype header** (AC-9) + per-step facet cards (OQ-2).
- Render the authoritative typed band first-class (the `judge` step's `threshold`/`direction`/`watch_margin` or `env_band`+`env_var`; the action step's `handler`/`autonomy`/`tiers`; each step's `gate_kind`) and the facet prose notes as secondary (AC-4). Reuse the colour legend; add at most one "authority vs advisory" affordance (AC-8).
- Show both the typed `Step.input` (`from`/`where`) and the prose `facet.input` in the input facet (finding #5).

### Step 5: Offline tests + preview verification
- Backend test (AC-10): assert `GET /procedures` returns all `registry.verticals()` procedures and each round-trips `load_procedures`; assert the archetype label is attached for each of the 5 procedures. Offline, no LLM.
- Frontend preview (evidence): render the console, switch across the four verticals, confirm all 5 procedures decompose by facet, the typed band is visually distinct, and the view loads with **MS-S1 cold** (zero-LLM). Capture a screenshot for the demo sign-off.

## Verification

How we know it worked, mapped to the gate-vs-evidence split (CLAUDE.md §8):

- **Gate (CI / offline):** the `GET /procedures` test is green — every discovered vertical's procedures are returned and round-trip `load_procedures`; the endpoint performs no mutation and needs no LLM. `ruff` + `mypy` clean on the new router + response model; the new view passes the offline bundle/preview build.
- **Evidence (live preview):** a screenshot showing all **5** procedures (across the 4 verticals) decomposed by their five facets, with the typed authoritative band visually distinct from the prose notes, the archetype header per procedure, and the page rendering with MS-S1 **cold** (zero-LLM).
- **Seam check:** `facetModel(step)` exists as a pure decomposition and `ViewProcedures.mount` accepts `mode` — confirmed by a read-mode render path PLAN-0040 can extend to edit-mode without a rewrite (AC-7). This is the load-bearing de-risk; if it is not present, PLAN-0039 is not done even if the pixels render.
- **No-regression:** Views A–E and their endpoints are untouched; `spec.py`, `orchestrator.py`, and `verticals/*/procedures.yaml` are unchanged (the viewer only reads them).

---

*PLAN-0039 drafted (uncommitted) by Cowork (session 78), Tier-1 governance authoring (ADR-009 D1). Its shape is LOCKED by ADR-0024 D8 (one surface, read-only-first) — a focused execution PLAN, not a new design fork. Code R2-reviews + commits via a `docs/*` PR after Cray ratifies (ADR-009 D2). AI-assisted; no `Co-Authored-By` per CLAUDE.md §7.*
