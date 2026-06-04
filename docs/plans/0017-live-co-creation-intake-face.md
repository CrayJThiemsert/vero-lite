# PLAN-0017: Live Co-Creation Intake Face — "Describe Your Operation" → Mirror Demo

**Status:** Draft
**Owner:** Claude Code (Tier 2 executes; Cowork drafted per ADR-009 D1)
**Created:** 2026-06-04
**Related ADRs:** ADR-015 (D5 live co-creation two-layer split — this is the
**face** layer; OQ-4 intake mechanism — resolved below as
recommend-with-rationale; Consequences §Neutral — PLAN-0018 forward-decl),
ADR-008 (D1 five base types + D4 `AlertEventLink`; D3 geo = lat/lng floats),
ADR-010 (IN-4 rule fail-safe — the deterministic anomaly→action path),
ADR-009 (D1 Cowork drafts / D2 Code commits)
**Related PLANs:** **PLAN-0016** (the scaffolding **engine** this face
invokes — implementation dependency, see Goal), **PLAN-0018**
(demo-shell MS-S1 status/warm affordance — **standalone, cross-referenced
only**, not drafted here)

> **Layering (ADR-015 D5).** PLAN-0016 is the **engine**: `vero-lite
> new-vertical <ns>` takes the partner-input package → a running vertical.
> This plan is the **face**: it turns a **live human domain description**
> into that package and **invokes the engine unchanged**. Everything
> downstream of "invoke" (codegen, synthetic adapter, templates,
> registration, direction step) is PLAN-0016's contract and is **not
> re-specified here**.
> **Sequencing:** *drafts now, implements after the engine.* The face's
> implementation gates on PLAN-0016 Steps 1–6 (the `new-vertical` command
> must exist to be called — verified absent at draft time:
> `services/engine/cli.py` holds only `validate`/`generate`, lines 29–37).
> Drafting in parallel is deliberate (Cowork lane) while Code builds the
> engine (Code lane); no engine work is blocked by this draft.
> **Drafted uncommitted** by Cowork (ADR-009 D1); no code/YAML/.env written
> during drafting. File:line evidence verified live 2026-06-04 against the
> WSL working tree (dispatch reference HEAD `5267b14`; PLAN-0016 Step 0
> shipped — `oct_recommend_direction` live at `services/api/config.py:144`,
> `services/engine/recommender.py:112, 223, 232`,
> `services/engine/demo_events.py:56`).

## Goal

Ship the **intake face** of ADR-015 D5 live co-creation: after the pre-built
aquaculture vertical #3 showcase, the demo operator asks **"…and what's
*your* operation?"** — the stakeholder describes their domain **live**, an
MS-S1-local LLM extracts a draft **partner-input package** (ontology +
problem + decision + threshold/direction), a **mandatory human review/edit
gate** lets the operator correct and explicitly confirm it, and the face
invokes the PLAN-0016 engine to boot a runnable **vertical #4** with the
three OCT features — the live "show #3 → build #4" moment that manufactures
decision urgency (research §5 hook). The face is a **caller**: it produces
the package and invokes `new-vertical`; it generates nothing itself.

## OQ-4 resolution — intake mechanism (recommend-with-rationale; **Cray ratifies**)

**Recommendation: HYBRID** — A3-style **free-text capture** feeding MS-S1
LLM extraction, surfacing into an A2-style **structured review/edit gate**.

| Lens | Pure A2 (guided form) | Pure A3 (conversational) | **Hybrid (recommended)** |
|---|---|---|---|
| Live-demo ergonomics | weakest wow — stakeholder fills a form; feels like configuration | highest wow, but multi-turn dialogue can meander live | one natural ask ("describe your operation") = the wow; the gate doubles as a co-creation beat (operator + stakeholder correct the draft together) |
| Build cost | form UI + *still* needs LLM drafting of ontology properties/enums from field text | conversational turn-management (state, clarifying-question policy) — the expensive bit | marginal: one textarea + one extraction call **on top of the gate UI that is mandatory anyway** (D5) |
| Demo robustness | most deterministic | largest live-failure surface (LLM quality, latency, dialogue dead-ends) | degrades gracefully: bad extraction → operator fixes in the gate; MS-S1 cold → manual-entry fallback **is** the A2 form (see AC-4) |

**Rationale.** The mandatory review gate (D5 hard requirement) already
forces an A2-style structured, editable surface to exist. Given that surface
is built regardless, hybrid is not extra scope — it is the honest
decomposition of D5: **conversational capture for the wow, structured review
for the safety**. Pure A2's deterministic core survives *inside* the hybrid
as the manual-entry fallback path, so the demo never depends on extraction
succeeding. Extraction is **single-shot with at most one bounded
re-prompt** — no open-ended dialogue (that is where A3's live-failure risk
lives). **Runner-up: pure A2** (most demo-robust; effectively contained
within the hybrid as its fallback). Voice capture is **out of scope**
(typed free text only — browser speech-to-text adds live failure surface
for marginal wow).

> **Adjudication transparency.** This concurs with Code's advisory lean in
> the dispatch (input, not a decision). Since Code is also the PR reviewer,
> **Cray's ratification is the independent check on OQ-4**, not Code review.

## Acceptance Criteria

- [ ] **AC-1 (headline — live #4 end-to-end):** starting from the pre-built
      aquaculture #3 showcase, a **live free-text domain description** of a
      *different* distributed-asset operation produces — through capture →
      MS-S1 extraction → **human review/confirm** → invoke — a runnable
      vertical #4 where (a) the map renders from ontology lat/lng; (b) NL
      query answers from live state (MS-S1 **on**); (c) the threshold breach
      triggers the recommender with a direction-correct trace on the
      **deterministic rule path** (ADR-010 IN-4) and approve → execute
      (echo) completes the lifecycle.
- [ ] **AC-2 (the human gate is real):** generation **cannot** proceed
      without an explicit human confirm of the reviewed ontology +
      threshold/direction — there is no code path from extraction to
      `new-vertical` that bypasses the gate. **An edit made in the gate is
      provably reflected in the generated vertical** (test the edit path,
      not just the happy path: e.g. rename a property / change an enum in
      the gate → assert the generated artifacts carry it).
- [ ] **AC-3 (direction inferred + confirmable):** the gate surfaces
      `OCT_RECOMMEND_DIRECTION` as an editable field; a **below-breach
      domain** (a crash, not an overrun — e.g. pressure/oxygen/level falling)
      is captured correctly end-to-end and the recommender **fires** (leans
      on PLAN-0016 Step 0, shipped #154). Wrong direction = the recommender
      silently never fires, so this is gate-critical, not cosmetic.
- [ ] **AC-4 (MS-S1 extraction + graceful degradation):** extraction runs on
      **MS-S1 (local)** — never the hosted API (CLAUDE.md §8 posture: the
      stakeholder's domain description is treated as theirs). If MS-S1 is
      cold/unreachable or extraction is low-confidence/unparseable, the
      operator sees a **clear, non-silent state** (ties to the PLAN-0018
      status affordance) and can fall back to **manual entry directly in the
      gate fields** — a silently wrong ontology is never pushed to
      generation.
- [ ] **AC-5 (engine untouched):** the face invokes `vero-lite new-vertical`
      **unchanged** — no new engine/generator features (mirrors PLAN-0016
      AC-5; the face is a caller). The engine's refuse-to-clobber guard is
      honored and surfaced, not bypassed.
- [ ] **AC-6 (quality bar):** new endpoints carry Pydantic request/response
      models with `Field(description=...)`; type hints + tests + ruff clean
      + mypy clean (CLAUDE.md §8).

## Out of Scope

- ❌ **The engine** — `new-vertical` orchestration, synthetic adapter,
  templates, registration, the recommender-direction step: **PLAN-0016**.
- ❌ **The MS-S1 status/warm backend + UI** (read-only `GET /llm/status`,
  in-UI warm/sleep/residency indicator) — **PLAN-0018, standalone** (kept
  separate per the dispatch call: independently PR-able, does not depend on
  the OQ-4 resolution). This plan **consumes** that affordance (Step 5) but
  does not build it. No `/llm/status` route exists today (verified).
- ❌ **Tier-2 / real-data / multi-input** — A4 document/schema upload, API,
  existing-system connectors, dbt/SQLMesh mapping layer, PDPA ingestion:
  post-demo, task (C) deep-research → future ADR/PLAN (ADR-015 D1 boundary).
- ❌ **Productionizing extraction accuracy** beyond demo-grade — the human
  review gate stays mandatory regardless of extraction quality.
- ❌ Real (non-echo) action handlers — partner-specific Tier-2 work.
- ❌ **Voice capture** — typed free text only (OQ-4 resolution note).
- ❌ Persisting intake sessions beyond the demo run (no intake history
  store; the output *is* the generated vertical).

## Steps

### Step 1: Capture surface (hybrid — per the OQ-4 resolution above)

An intake page in the OCT demo shell: a single free-text **"describe your
operation"** surface with a short prompt scaffold steering the stakeholder
toward the four package dimensions (what are your assets and where do they
sit; what breaks and why it hurts; what reading crosses what threshold,
crash or overrun; what is the corrective action). One bounded re-prompt
("anything about thresholds or the corrective action?") is allowed;
no open-ended dialogue. Entry affordance lives in the shell as the
"…and what's *your* operation?" moment (Step 5).

### Step 2: MS-S1 extraction → draft partner-input package

One extraction call against the MS-S1 Ollama host drafting the four
generator inputs (research §4 shape):

1. **Ontology** — the ADR-008 D1 five base types mapped onto the domain
   (`Asset`/`Site`/`OperationalEvent`/`Alert`/`RecommendedAction` + the
   `AlertEventLink` join per D4), properties/enums/refs, **geo as
   `lat`/`lng` floats on the Site** (D3 — no `geo` type).
2. **Problem statement** (free text).
3. **Decision / action** (free text → the `echo`-stub handler +
   `OCT_RECOVERY_*` values).
4. **Threshold→action config** — the `OCT_RECOMMEND_*` block including
   **`OCT_RECOMMEND_DIRECTION ∈ {above, below}`** inferred from breach
   physics (crash = below, overrun = above) and always shown for confirm.

Constrain output to a structured schema (JSON-schema-constrained decode or
strict parse-and-reject); attach a coarse confidence signal. Pre-validate
the drafted ontology with `vero-lite validate` *before* the gate renders,
so schema errors surface to the operator pre-confirm — never mid-generation
during the live moment. Low-confidence/unparseable → the AC-4 fallback.

### Step 3: The review/edit gate (MANDATORY — the one non-negotiable)

A structured editor rendering the full proposed package: the five types with
properties/enums/refs, the problem/decision texts, threshold, **direction**,
and recovery values — all editable. **Generation is blocked until an
explicit human confirm**; there is no auto-proceed path (AC-2). The same
surface doubles as **manual-entry mode** when extraction is degraded (AC-4)
— the gate pre-filled by the LLM in the happy path, blank-editable in the
fallback path. Edits feed the *confirmed* package; the confirmed package —
not the raw extraction — is what Step 4 hands to the engine.

### Step 4: Namespace + invoke the engine

Pick/confirm the namespace (slug-validated); call PLAN-0016's
`vero-lite new-vertical <ns>` with the confirmed package, **unchanged**
(AC-5). Surface the engine's refuse-to-clobber guard as an operator-visible
choice (pick a new namespace), never an override-by-default. Relay the
engine's run checklist into the face. **Demo-boot mechanics** (how #4 comes
up while #3 stays showable — e.g. second uvicorn instance on a separate port
with `OCT_VERTICAL=<ns>` vs restart-in-place): implementation call for Code
in the PR, with a lean toward the separate-port instance (keeps #3 alive for
side-by-side); either way the boot procedure lands in the runbook (Step 6).

### Step 5: Wire the live flow into the OCT shell

The "show #3 → build #4 live" path: showcase #3 → the intake entry
affordance → capture → extract → gate → invoke → open #4. **Depends on the
PLAN-0018 MS-S1 warm/status affordance** (the operator must confirm MS-S1 is
resident *before* the stakeholder types — extraction and NL query both need
it): this plan **consumes** `GET /llm/status` + the warm control, building
neither (Out-of-Scope; building blocks verified at
`services/api/routers/admin.py:40, 53–69, 99` — `_ps_safe` / `GET /warm` /
`GET /sleep`). If PLAN-0018 has not landed, the interim is the operator
hitting `GET /warm` manually pre-demo — degraded but not blocking.

### Step 6: Verification + docs + closeout

Run-oct-demo runbook entry for the live co-creation walkthrough (incl. the
boot mechanics from Step 4 and the MS-S1 pre-warm checklist), STATUS update,
`git mv` this plan to `done/` on completion (Code's lane throughout,
ADR-009 D2).

## Verification

- **AC-1:** scripted live walkthrough per the runbook entry: #3 showcase →
  typed description of a different domain → gate → invoke → #4 boots; map +
  NL query (MS-S1 on) + breach→recommend→approve→echo observed.
- **AC-2:** `pytest` — (a) the invoke endpoint/path refuses an unconfirmed
  package (no bypass route); (b) edit-propagation: gate-edited field present
  in the generated artifacts.
- **AC-3:** end-to-end test with a below-direction domain description —
  direction lands as `below` in the env block and the recommender fires on
  the rule path (extends PLAN-0016 Step 0 coverage to the face).
- **AC-4:** extraction-degradation tests — MS-S1 unreachable + unparseable
  output both surface the non-silent state and enable manual-entry; no
  generation occurs from a degraded extraction without human-entered +
  confirmed content.
- **AC-5:** diff shows no `services/engine/` behavior changes; clobber-guard
  exercised in a test.
- **AC-6:** `ruff` + `mypy` clean; pre-commit passes.

---

*Drafter numbering check (Cowork, 2026-06-04): `docs/plans/` active =
0004/0010/0012/0016, `done/` tops at 0015 → **0017 free**, no collision
(matches the ADR-015 D5 forward-declaration). Dispatch:
`.claude/handoffs/session-37/2026-06-04-2022-code-plan0017-intake-face-dispatch.md`.*
