# PLAN-0013: OCT Stakeholder Demo (v1 — 3 OCT features on the energy vertical, ontology-driven UI)

**Status:** Draft
**Owner:** Claude Code (executor) + Cowork (advisory drafter, ADR-009 D1 / ADR-013 OQ-1)
**Created:** 2026-05-30
**Related ADRs:** ADR-005 (OCT pivot — energy first), ADR-006 (vertical plugin architecture / template-first), ADR-007 (RecommendedAction envelope + action loop), ADR-008 (ontology `object_type`), ADR-010 (LLM brain-swap — recommender LLM-backed + rule fail-safe)
**Related Plans:** PLAN-0005 (OCT engine runtime — read→recommend→approve→execute loop, done), PLAN-0006 (LLM reasoning hook, done)
**Related docs:** `docs/strategy/public/STRATEGIC_CONTEXT_AIP.md` (north-star, tracked per OQ-1 / PR #89)

> **Provenance.** Cowork-drafted cold from Code's verified dispatch
> (`.claude/handoffs/session-26/2026-05-30-1148-code-demo-v1-plan-dispatch.md`)
> under ADR-009 D1. Code reviews, commits, and executes (ADR-009 D2 — only
> Code commits). Minted `Status: Draft` per PLAN-0009 OQ-4 + template
> (`docs/plans/0000-template.md`), **not** ADR vocabulary `Proposed`.
>
> **Author≠reviewer note (ADR-012 D4.3).** This PLAN's substance was *not*
> self-deliberated in Cowork free-form mode — it is a cold draft of Code's
> fact-pack. The independent-deliberation check is therefore Code's review +
> the live verification in §Verification.

> **Code-authored addition (2026-05-30, Cray-ratified).** Screen D
> (Data→Decision Flow view) + AC-flow were added by **Code** at commit — *not*
> part of Cowork's cold draft. For that section author = committer; the
> independent check is **Cray's ratification** (the addition was Cray-originated
> and explicitly approved). Flagged for transparency per ADR-012 D4.3.

> **Session-28 scope expansion (2026-05-31, Cray-ratified).** AC-template was
> expanded from a minimal "smoke swap" to a **full A/B/C/D second-vertical story**
> on `supply_chain` (cold-chain logistics), per Cray's decision in the session-28
> kickoff. Delivered by Code (config-driven `OCT_VERTICAL` + the supply_chain
> ontology/adapter/handlers + a one-time generalization of the residual
> energy-specific coupling). Author = committer for this increment; the
> independent check is **Cray's explicit ratification** of the expanded scope
> (ADR-012 D4.3). Rule-of-Three guard preserved — a **data-driven 2nd instance**,
> no new abstraction layer.

## Goal

Ship a **stakeholder-facing demo** of the Operational Control Tower (OCT) on
the **energy vertical** that lets an energy / supply-chain operator *see it and
instantly grasp* how vero-lite turns **data they already have** into **tangible
operational value** — enough to want to engage us as a design partner (CLAUDE.md
strategy: 2 design partners → revenue). v1 surfaces **all three OCT features**
(operational map, anomaly→decision with reasoning trace, NL operational query)
through a **Claude-Design-built UI that is ontology-driven, not hard-coded to
energy**, served by the existing FastAPI engine. The demo leans hard on what is
already built (the engine, recommender, synthetic scenario) so a solo dev can
land it on a short timeline; the genuinely-new build is the NL-query backend
plus two small backend tweaks.

## Context & strategic frame

**North-star (`STRATEGIC_CONTEXT_AIP.md`).** vero-lite is an *agentic
operational platform* (Ontology → Workflow → Governance → Observability →
Evaluation → Agents), not a chat app. This demo instantiates **Pillar 1**
(ontology-driven design), **Pillar 5** (governance — every action explainable
via a reasoning trace), and **Pillar 9** (human-in-the-loop — recommend →
approve → execute) on a real vertical. It **executes ADR-005** (OCT first
instantiated on a regional energy operator).

**Decisions baked in (Cray-ratified 2026-05-30 — not open; do not re-surface):**

| OQ | Resolution baked into this PLAN |
|----|----------------------------------|
| OQ-1 | `STRATEGIC_CONTEXT_AIP.md` is **tracked** (PR #89); cited as a tracked reference. |
| OQ-2 | **No new ADR.** This executes ADR-005; UI/template posture is delivery of existing OCT scope under ADR-006, not an architecture-level decision. (Cowork concurs — the Rule-of-Three guard below keeps v1 from introducing a new abstraction.) |
| OQ-3 | **NL query = engine A** (LLM translates NL → a structured query over the ontology; backend answers from **real `/objects` data**; LLM phrases the reply) surfaced through a **chat panel**. Agentic tool-calling over `mcp_tools.json` (option B) is **deferred to v2**. The AC requires answers **grounded in real ontology data — no canned answers** (anti-hallucination is the credibility point). |
| OQ-4 | **Delivery = FastAPI serves the Claude-Design standalone HTML as static** (one process, one URL, no CORS). A separate frontend dev server is deferred (over-build for v1). |

**Verified fact-pack (Code ran live against `main` `5ac77cb`; Cowork
re-verified the load-bearing claims against source at draft time).**

*Built + live end-to-end* (energy adapter auto-registers on FastAPI startup —
`services/api/main.py` lifespan):

| Endpoint | Returns | Backs |
|----------|---------|-------|
| `GET /objects/{object_type}` | `ObjectListResponse{object_type,count,objects[]}` from `adapter.fetch_objects` | Feature 1 (map **data**) |
| `GET /recommendations` | `RecommendationListResponse{count,recommendations[]}` — first call streams reading events → `recommend()` → stores actions | Feature 3 (anomaly pipeline) |
| `POST /recommendations/{id}/approve` | `RecommendationResponse` (proposed→approved) | Human-in-loop |
| `POST /recommendations/{id}/execute` | `ExecuteResponse{action_id,status,handler_receipt}` + DB persist | Human-in-loop |
| `GET /health` | `HealthResponse` | infra |

- **Recommender** (`services/engine/recommender.py`): deterministic trigger
  (`measured_value ≥ OVERTEMP_THRESHOLD_CELSIUS = 90.0`) → LLM judgment (Ollama
  `gpt-oss:20b`, `llm_backend=local`) → `RecommendedAction`, **with a
  deterministic rule fail-safe** (`_rule_recommend`, `RULE_CONFIDENCE = 0.8`,
  handler `echo`) → the over-temp action is produced **even if MS-S1/Ollama is
  down**.
- **Synthetic scenario** (`verticals/energy/data_adapter/synthetic.py`,
  deterministic, abstract IDs, PDPA/public-safe): 2 Sites (both lat/lng →
  map-plottable), 4 Assets, OperationalEvents incl. the **over-temp 96.5 °C
  reading on Battery Bank A** that fires the recommender.
- **Ontology** (`verticals/energy/ontology/energy_v0.yaml`): object_types with
  `title_key` + `properties` + enums; codegen output already emitted under
  `verticals/energy/generated/` (`models.py`, `schema.sql`, `schema.json`,
  `types.ts`, `mcp_tools.json`).

*Cowork-verified live-smoke evidence (Code, 2026-05-30):* `GET /objects/Site` →
2 sites w/ lat/lng; `GET /objects/Asset` → 4 assets; `GET /recommendations` →
**1 action, the over-temp killer beat** (`status: proposed`, `confidence: 0.8`,
`requires_approval: true`, `suggested_handler: echo`); rule fail-safe fired as
designed → **demo is robust offline**.

*The gap (3 items):*

1. **No UI** (no frontend files anywhere) → Claude Design builds it (Step 3–5).
2. **NL operational query (feature 2) not built** (no module/endpoint) → the one
   genuinely-new backend build. Pieces exist: the LLM layer
   (`services/engine/llm/`) + per-vertical `generated/mcp_tools.json`.
3. **⚠ `reasoning_trace` + `affected_entities` are built in the engine but NOT
   exposed by `/recommendations`.** Cowork confirmed at source:
   `RecommendationResponse` (`services/api/models/actions.py`) + `_to_response`
   (`services/api/routers/actions.py`) return only
   `action_id, title, description, vertical, status, confidence,
   requires_approval, suggested_handler`. The `RecommendedAction` object *does*
   carry `reasoning_trace` (`ReasoningStep[]: step_id, kind, summary, detail`) +
   `affected_entities` (`EntityRef[]: object_type, primary_key`). **The demo's
   "show me WHY" moment needs these surfaced** → small Code change to the
   response model + mapper (backend tweak #1, load-bearing).

**v1 screens (Cray-approved scope):**

- **Screen A — Operational Map** (feature 1): Sites (lat/lng) + Assets + status,
  from `/objects`.
- **Screen B — Anomaly / Decision panel** (feature 3) — *the killer moment*: the
  over-temp Alert → RecommendedAction card (title, confidence, **reasoning-trace
  steps**, affected asset) + **Approve / Reject / Execute**, round-tripped live
  against `/recommendations` + approve/execute.
- **Screen C — NL operational query** (feature 2): plain-language question →
  ontology query → grounded answer (chat panel). New backend build.
- **Screen D — Data→Decision Flow view** (*Code-authored addition, Cray-ratified
  2026-05-30 — see Provenance*): a visible **4-stage pipeline** that ties A/B/C
  into one narrative a stakeholder can follow — **Ingest** (the operator's
  existing data, from `/objects`) → **Condition** (the over-temp trigger *and/or*
  the user's NL-query condition) → **Process** (the recommender's reasoning — the
  `reasoning_trace` steps) → **Result** (the RecommendedAction + approve/execute).
  A **view over existing data — no new backend** (reuses `/objects` + the
  recommendation trace); **vertical-agnostic** (the 4 stages are generic, content
  driven by the ontology). It unifies feature 2 (interactive condition) +
  feature 3 (automatic condition) into one "your data → a governed decision" story.

**Template requirement (Cray-approved: A for v1, B fast-follow).** vero-lite's
thesis is *vertical plugin architecture* (ADR-006; template-first
multi-vertical). The engine is already vertical-agnostic; the demo must honor
this **to the UI layer**:

- **Make-or-break principle — the UI must be ONTOLOGY-DRIVEN, not hard-coded to
  energy.** Render entity types / fields / enums from `/meta` (the new endpoint,
  backend tweak #2), not from energy labels. Then *swapping vertical = swapping
  the ontology + adapter*, no UI rewrite.
- **(A) v1 = architecture-generic now** — ontology-driven UI on energy data.
- **(B) fast-follow "ready if asked"** — a second vertical's ontology + adapter
  (industrial supply-chain operator; `supply_chain/` is a README-only stub
  today) to show "same UI, their domain" right after the demo. **Not built in
  v1.**
- **⚠ Rule-of-Three guard (CLAUDE.md §1).** "Template-ready" means **consume the
  existing abstraction (the ontology) via a data-driven UI** — NOT build a new
  meta-framework. The engine *is* the abstraction. Do not over-abstract in v1.

## Acceptance Criteria

Per-AC evidence style — each AC is satisfied by named, live (not mocked)
evidence captured at Step 6.

- [ ] **AC-map** — Screen A renders Sites (plotted by lat/lng) + Assets with
      status, sourced from `/meta` (entity types / fields) + `/objects` (data).
      Evidence: the map is driven by `/meta` + `/objects` responses, **not**
      hard-coded energy labels (open the served page; show it rendering from the
      API payloads).
- [ ] **AC-anomaly (killer moment)** — Screen B shows the over-temp
      RecommendedAction with **its reasoning-trace steps** and the affected
      asset, and completes an **Approve → Execute round-trip live** against the
      running app (`/recommendations` → `/recommendations/{id}/approve` →
      `/recommendations/{id}/execute`, ending `status: executed` with a handler
      receipt). Evidence: captured request/response flow of the full round-trip,
      trace visible in the UI.
- [ ] **AC-nlquery (grounded, no canned)** — Screen C answers **≥ 5**
      plain-language questions by translating NL → a structured query over the
      ontology and returning facts drawn from **real `/objects` data**. Every
      answer is traceable to the structured query it ran + the source objects it
      read; **a question with no supporting data returns "not found / no data,"
      never an invented fact.** Evidence: the ≥5 Q/A transcript +, for ≥2
      answers, the structured query + source object IDs that grounded them.
- [ ] **AC-flow (Code-authored addition — see Provenance)** — the demo presents
      the **data → condition → process → result** journey as a single visible
      flow (Screen D) a stakeholder can follow end-to-end, each stage showing the
      **real artifact** at that stage (live data counts from `/objects`; the
      over-temp condition *or* an NL-query condition; the reasoning-trace steps;
      the RecommendedAction + approval). Evidence: the served flow view rendered
      from **live API payloads** for the over-temp scenario — no new backend, no
      hard-coded energy labels.
- [x] **AC-template (B-readiness proof)** — ✅ **MET (session 28, Cray-ratified
      scope expansion).** The UI consumes entity types / fields / enums from
      `/meta`; **swapping the ontology + adapter (via `OCT_VERTICAL`) yields a
      working UI with zero per-vertical UI-code change.** Originally scoped as a
      minimal smoke swap; **expanded by Cray (session 28) to a full A/B/C/D
      second-vertical story** — `supply_chain` (cold-chain logistics), shipped as
      a **data-driven 2nd instance** (NOT a meta-framework — Rule-of-Three guard
      intact). The residual energy-specific coupling (the recommender trigger
      threshold + fail-safe wording via `OCT_RECOMMEND_*`, the LLM trace's
      entity phrasing, and three UI strings in Views B/D + C) was generalized
      **once** to be ontology/config-driven; thereafter a new vertical is "swap
      the ontology + adapter + set `OCT_*` env, no engine/UI code change."
      Evidence: see Verification → Template proof (live, all four screens).
- [ ] **AC-safety** — the demo uses **synthetic data only** (no real partner
      data; no partner identifiers/brand codes anywhere), and the **rule
      fail-safe keeps it robust offline** (the over-temp action and Screen B flow
      work with `LLM_BACKEND` forcing the deterministic path / MS-S1 down).
      Evidence: an offline run reproducing the over-temp action.
- [ ] **AC-delivery** — the whole demo runs as a **single FastAPI process
      serving the Claude-Design standalone HTML as static** — one URL, no CORS,
      no separate frontend dev server. Evidence: start one process, open one URL,
      all three screens functional.

## Out of Scope

- ❌ **Real partner data** — synthetic scenario only (AC-safety).
- ⚠️ **The 2nd vertical itself** — ~~supply-chain ontology + adapter is a
      *fast-follow*, not v1~~ **SUPERSEDED (session 28, Cray-ratified):** the
      `supply_chain` (cold-chain) ontology + adapter **is** shipped here as the
      AC-template proof (full A/B/C/D re-skin). It remains a **data-driven 2nd
      instance**, not a new abstraction layer — the Rule-of-Three guard below is
      preserved (no meta-framework introduced).
- ❌ **Any premature meta-framework / new abstraction layer** — Rule-of-Three
      guard; v1 consumes the existing ontology abstraction, full stop. (Still
      enforced: the supply_chain vertical added in session 28 is a 2nd concrete
      instance — ontology YAML + synthetic adapter + handlers + env-driven
      policy — **not** an extracted abstraction. The `_template/` skeleton stays
      empty until a 3rd vertical exists.)
- ❌ **Agentic tool-calling NL query (option B)** over `mcp_tools.json` —
      deferred to v2 (OQ-3); v1 is engine A only.
- ❌ **A separate frontend dev server / SPA build pipeline** — deferred (OQ-4).
- ❌ **Production auth / full audit framework** — the approval gate is the
      minimal proposed→approved→executed lifecycle (ADR-011+ audit framework is
      out of scope).

## Steps

### Step 1 — Backend tweaks (Code)
1a. **Expose `reasoning_trace` + `affected_entities` in `/recommendations`** —
extend `RecommendationResponse` (`services/api/models/actions.py`) + the
`_to_response` mapper (`services/api/routers/actions.py`) to carry the
`ReasoningStep[]` + `EntityRef[]` the `RecommendedAction` already holds. Enables
Screen B's killer moment. *(Load-bearing — live-confirmed gap #3.)*
1b. **Add `GET /meta`** (ontology metadata) — object_types + `title_key` +
properties + enums, served from the generated `schema.json` (data already
exists). **This is the template enabler** for AC-map + AC-template.

### Step 2 — NL-query backend (Code, feature 2)
Build the engine-A NL-query path: NL → structured ontology query (via the
`services/engine/llm/` layer) → answer from real `/objects` data → LLM phrasing.
Bounded: single-operator, **read-only**, grounded (anti-hallucination — return
"no data" rather than invent). New endpoint (e.g. `POST /query`) + response shape
that carries the answer **plus** the structured query + source object refs it
used (so AC-nlquery grounding is provable).

### Step 3 — Author the Claude Design prompt (Code drafts; Cowork refines UX/operator tone)
A **contract-bound, vertical-agnostic** design prompt describing Screens A/B/C + the Screen-D flow view in
generic operational terms (entities / sites / anomalies / recommended-actions-
with-traces), bound to the real API field names (fact-pack above), energy as the
seed content, **layout driven by data (`/meta`), not energy-specific labels**.
Code holds the contracts and offers to draft this; Cowork refines operator tone.

### Step 4 — Run Claude Design (Cray)
Cray runs Claude Design with the Step-3 prompt + theme images → exports the
**standalone HTML**.
(Ref: https://support.claude.com/en/articles/14604416-get-started-with-claude-design)

### Step 5 — Wire HTML → live API (Code)
Code wires the exported HTML to the live endpoints (`/meta`, `/objects`,
`/recommendations` + approve/execute, the NL-query endpoint) and **serves it as
static from the FastAPI app** (OQ-4 — one process, one URL, no CORS).

### Step 6 — Live demo dry-run + evidence
Run the full demo end-to-end **against the running app (not mocked)** and capture
evidence for every AC — especially the over-temp **killer-moment** round-trip
(Screen B) and the AC-template smoke swap. Lesson #15 live-vs-mock discipline:
the evidence must come from the live app.

## Verification

- **Live, not mocked.** The demo runs end-to-end against the FastAPI app; each AC
  is signed off against named live evidence captured at Step 6 (Lesson #15).
- **Killer-moment proof.** Capture the over-temp flow: `/recommendations` returns
  the action **with reasoning trace + affected asset**, then approve → execute
  round-trips to `status: executed` with a handler receipt.
- **Grounding proof (NL query).** For ≥2 of the ≥5 NL answers, record the
  structured query + source object IDs that produced the answer, and show one
  "no data → no invented fact" case.
- **Template proof (session 28, live).** `OCT_VERTICAL=supply_chain` renders the
  **same UI build** across all four screens with **zero per-vertical UI-code
  change** (the `services/api/static/` diff is vertical-agnostic — generalizations
  only, no `supply_chain`/`energy` branching). Live evidence captured via Claude
  Preview against the running app on :8098 (Lesson #15):
  - **View A (map):** 2 Facilities plotted by lat/lng with Shipment satellites;
    LEGEND + STATUS ENUMS from `/meta` (IN_TRANSIT / DELAYED / HELD / COLD_STORAGE
    / …); the breaching shipment ringed red.
  - **View B (anomaly):** live LLM `RecommendedAction` "Temperature Breach
    Response" (conf 0.92, handler `echo`), affected SHIPMENT + FACILITY, a
    cold-chain reasoning trace, and a full **proposed → approved → executed**
    round-trip + handler receipt; persisted to Postgres (`recommended_action`
    status=executed conf 0.92 action=quarantine + `alert` rows) via the same
    vertical-neutral persistence (no schema/migration change).
  - **View C (NL query):** "How many shipments are there?" → grounded answer
    (`COUNT Shipment` → 4) with source-object-id chips; example chips derived
    from `/meta`.
  - **View D (flow):** the 4-stage Ingest → Condition → Process → Result pipeline
    over supply_chain data (THRESHOLD BREACH on shipment-pharma-01 → trace →
    executed action).
- **Offline robustness.** Reproduce the over-temp action with the LLM path forced
  off (rule fail-safe), proving the demo survives MS-S1/Ollama being down.

## References

- **Dispatch:** `.claude/handoffs/session-26/2026-05-30-1148-code-demo-v1-plan-dispatch.md` (verified fact-pack + scope; gitignored working note).
- **North-star:** `docs/strategy/public/STRATEGIC_CONTEXT_AIP.md` (Pillars 1 / 5 / 9).
- **Code (verified at `5ac77cb`):** `services/api/main.py`, `services/api/routers/actions.py`, `services/api/models/actions.py`, `services/engine/recommender.py`.
- **Ontology + scenario:** `verticals/energy/ontology/energy_v0.yaml`, `verticals/energy/data_adapter/synthetic.py`, `verticals/energy/generated/schema.json` (the metadata `/meta` serves).
- **ADRs:** ADR-005 (OCT pivot), ADR-006 (vertical plugin / template-first), ADR-007 (RecommendedAction envelope + action loop), ADR-008 (object_type), ADR-010 (LLM brain-swap + rule fail-safe). CLAUDE.md §1 (template-first / Rule-of-Three), §3 (three-layer ontology engine).
- **Lessons:** #15 (live-vs-mock evidence discipline).

---

*Cowork-drafted (ADR-009 D1) from Code's session-26 dispatch; uncommitted Draft.
Code reviews, commits (ADR-009 D2), and executes. No partner identifiers; synthetic data only.*
