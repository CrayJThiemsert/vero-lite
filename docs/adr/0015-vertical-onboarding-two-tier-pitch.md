# ADR-015: Assisted / Self-Serve Vertical Onboarding as a 2-Tier Pitch Artifact

**Status:** Accepted (ratified by Cray — 2026-06-04, session 36)
**Date:** 2026-06-04
**Deciders:** Jirachai Thiemsert (founder)
**Related:** ADR-005 (vertical roster / vet park — see OQ-1), ADR-006 (vertical plugin architecture; D4 Rule of Three; L2 `new-vertical` forward-declaration), ADR-008 (YAML ontology contract; D1 five base types; D3 geo deferral), ADR-009 (D1 Cowork drafts / D2 Code commits), ADR-010 (LLM reasoning hook; IN-4 rule fail-safe), ADR-013 (phased advisory relocation — interim authoring applies). Companion builds: **PLAN-0016** (engine), **PLAN-0017** (intake face — forward-declared, see D5), **PLAN-0018** (demo-shell LLM status — forward-declared, see Consequences). Source artifacts: `docs/research/private/2026-06-04-vertical3-pick.md` (pick + partner-input package), `.claude/handoffs/session-35/2026-06-04-0944-code-design-partner-demo-gen-feasibility.md` (feasibility fact-pack), `.claude/handoffs/session-36/2026-06-04-1438-code-cowork-taskB-adr-plan-dispatch.md` (authoring dispatch), `.claude/handoffs/session-36/2026-06-04-1521-code-cowork-taskB-live-co-creation-addendum.md` (live-co-creation addendum).

> **Drafting provenance.** Cowork-drafted (uncommitted) under ADR-009 D1
> interim authoring per ADR-013's phased relocation; Code commits via PR
> (ADR-009 D2). Four framing decisions were **Cray-ratified in session 36**
> and are codified, not re-litigated, here: (1) demo audience = SE-Asian
> aquaculture, pick locked; (2) OQ-1 carried as an open question, not silently
> resolved; (3) the recommender threshold-direction gap is a REQUIRED
> PLAN-0016 step; (4) demo strategy = **(ii) live co-creation** (1521
> addendum) — codified as D5. **Author≠reviewer disclosure (ADR-012 D4.3):** the
> vertical-pick research grounding D4 below was also Cowork-authored
> (research-with-recommendation, dispatched); the pick was Cray-ratified and
> Code's PR review remains the independent check.

## Context

### The idea and the feasibility verdict

A design partner supplies four inputs — **ontology, data, problem,
decision** — and vero-lite auto-builds a working 3-feature OCT demo skinned
to their domain. Session-35 feasibility analysis (fact-pack §1–§4) returned
**YES — the engine is ~80% there**:

- Two of three OCT features are already 100% ontology/config-driven with
  zero per-vertical code: the map (`view-map.js` +
  `services/engine/ontology_meta.py:88-127`) and NL query
  (`services/engine/nl_query.py:159-174, 434-508`). The third
  (anomaly→decision) is half config: detection = pure env config
  (`OCT_RECOMMEND_*` / `OCT_RECOVERY_*`), execution = a handler, where the
  shipped `echo` stub already closes the propose→approve→execute lifecycle.
- The generator (the moat) is complete and CLI-driven: `vero-lite generate`
  emits all 5 artifacts (`services/engine/code_generator.py:360-369`,
  `services/engine/cli.py:36-51`).
- Remaining per-vertical hand-written code is small and fully templatable
  (fact-pack §3): `synthetic.py` (LLM-generatable), `__init__.py` (~60
  lines), `handlers.py` (~30-line echo stub), one registrar row
  (`services/api/main.py:36-39`), 7 env values.

### Already on the roadmap — Rule-of-Three timing

`vero-lite new-vertical <name>` is **already forward-declared** as the
ADR-006 L2 / Phase-2 CLI generator in `verticals/_template/README.md`
(verified at HEAD). ADR-006 D4 says the `_template/` abstraction is
extracted from real patterns at the **3rd vertical**. Building the demo
generator **is** minting that 3rd-vertical capability — the aquaculture test
case in PLAN-0016 is the 3rd concrete vertical. This pulls a roadmap item
forward and reframes it as a **sales/pitch artifact**; it is on-pattern, not
premature abstraction.

### The market frame (2026)

- B2B AI POC best practice is unambiguous: the highest-converting POCs run
  on the customer's **real** data (~75% conversion; fact-pack §5–§6) — but
  real data means a real `DataAdapter`, a mapping layer, and PDPA
  governance, none of which exist today (vero-lite is synthetic-only; no
  real-data adapter seam).
- The ratified showcase audience is **SE-Asian aquaculture**, where the 2026
  eFishery fraud collapse (founder sentenced Apr–May 2026; ~US$600M inflated
  revenue) froze the sector's funding and trust, leaving a
  credibility-vacuum that a small, **reasoning-trace-first, auditable**
  mid-market product is well-shaped to fill (research §0–§1, §7 sources).
- The one real engine gap the concrete pick surfaced: the recommender only
  fires on **above**-threshold readings (`services/engine/recommender.py:94`,
  `199-204`; no `oct_recommend_direction` setting exists), while an
  aquaculture dissolved-oxygen crash breaches **below** (3.2 < 4 mg/L).
  PLAN-0016 carries this as a required engine step.

## Decision

### D1: Onboarding is productized as a 2-tier pitch artifact

| Tier | What | Data posture | Status |
|---|---|---|---|
| **Tier 1 — "Mirror demo"** | partner describes domain/problem → we generate a **synthetic** OCT demo skinned to them | no data sharing, no PDPA friction | **build first** (PLAN-0016) |
| **Tier 2 — "Real-data POC"** | partner ships a real data extract → demo runs on their actual operation | real `DataAdapter` + mapping layer + PDPA/data-residency governance required | **gated behind Tier 1**; design = task (C) deep-research, future ADR/PLAN |

Tier 1 is the first-pitch artifact; Tier 2 is the conversion artifact. Tier 2
work does not start until Tier 1 ships and the task (C) research lands.

### D2: Tier-1 vehicle = the `vero-lite new-vertical` scaffolding command

One command stitches the BUILD steps (LLM-gen synthetic adapter, templated
boilerplate, env config, registration) around the existing AUTO generator,
which plugs in unchanged. The build is specified in PLAN-0016 with
aquaculture as the concrete end-to-end test case. This command is the
**engine layer** of D5's two-layer split; the intake face (PLAN-0017) sits
on top of it.

### D3: ICP / strategic frame = mid-market beachhead, disrupt-from-below

The target is the **right-sized mid-market operator**: good-enough + faster
+ cheaper than big-name incumbents (Palantir-class platforms are
acknowledged slow/complex to onboard even for engineers — fact-pack §6), yet
worthwhile revenue for a solo-founder product, with a scale-up path. The
demo generator is the embodiment: **fast, vertical-scoped onboarding** is
the edge. Worked justification: research §1.5 lens + the eFishery-whitespace
findings (§0/§1).

### D4: First showcase audience + pick are locked (Cray-ratified)

Demo audience = **SE-Asian aquaculture**; the pick is locked to
**aquaculture pond water-quality control tower** (namespace candidate
`aquaculture`; partner-input package in research §4). **Fuel-retail
wetstock (#2)** is recorded as the *audience-dependent alternate* — to be
revisited only if the audience shifts to the existing
energy/supply-chain partner network. It is a noted alternate, **not** the
recommendation.

### D5: Demo strategy = (ii) live co-creation — engine + intake face (Cray-ratified)

The demo is **not** "watch our polished aquaculture demo." It is: (1)
showcase the pre-built aquaculture vertical #3 — credibility + the three
OCT features working; then (2) **"…and what's *your* operation?"** — the
stakeholder describes their domain **live**, and a Mirror demo of *their*
vertical #4 is generated on the spot. The live #4 moment manufactures
decision urgency by letting the stakeholder see their own operation running
in minutes — it productizes the vertical-#4 hook (research §5). This
refines, not changes, D1: both layers below are inside the **Tier-1
Mirror** tier.

| Layer | What | Where it lives |
|---|---|---|
| **Engine (plumbing)** | `vero-lite new-vertical` — partner-input package → running vertical (validate+generate → synthetic adapter → templates → registration + the recommender-direction step) | **PLAN-0016** |
| **Face (intake)** | guided-form (A2) and/or conversational (A3) intake that turns a live human domain description into the partner-input package, then invokes the engine | **PLAN-0017** — forward-declared only; full draft is its own dispatch after this ADR is accepted |

The layers are **separable builds** and stay in separate PLANs. The intake
mechanism — **A2 guided form vs A3 conversational vs hybrid — is a design
choice recorded as OQ-4**, with one hard requirement either way: a **human
review/edit step of the LLM-drafted ontology before generation**. The
intake must *show* the proposed ontology and let the operator correct it —
never silently auto-generate (SOTA consensus; fact-pack §6).

**Scope boundaries (Cray's phasing):**

- **Demo-scope (Tier-1 Mirror — built for the showcase):** the engine
  (PLAN-0016) + the intake face (PLAN-0017) + the pre-built aquaculture #3.
  Enough to run "show #3 → build #4 live."
- **Post-demo / longer (explicitly OUT of scope for the demo):** the real
  production implementation for the chosen partner — real-data ingestion,
  **multiple input types (A4 document/schema upload, API, existing-system
  connectors)**, the dbt/SQLMesh mapping layer, Tier-2 / PDPA governance.
  This takes materially longer and happens **after** the stakeholder
  decides; task (C) deep-researches the path (the D1 Tier-2 boundary — the
  demo must not over-promise it).

## Consequences

### Positive

- A repeatable first-pitch artifact with zero data-sharing friction; usable
  the day a partner describes their domain.
- Mints the 3rd-vertical capability on-pattern (ADR-006 D4); the
  `_template/` extraction gets three real verticals to generalize from.
- Tier-1 demo exercises all three OCT features end-to-end on a new domain,
  hardening the config-driven claims (map/NL-query zero-code; recommender
  config-only after the direction fix).
- The aquaculture showcase doubles as the vertical-#4 stakeholder hook
  ("that's exactly my problem, but my assets are ___" — research §5).

### Negative / risks

- `statusClass()` is an English-enum regex
  (`services/api/static/assets/api.js:113-120`); unusual enum vocabulary
  renders `s-neutral` until extended (one-line fix per odd vocab).
- NL-query quality = ontology-description quality — a data-quality risk,
  not a code risk; LLM-drafted ontologies need human review (2026 SOTA
  consensus, fact-pack §6).
- Real action handlers are partner-specific; the `echo` stub is sufficient
  for demos but a real Tier-2 engagement needs real handlers.
- A synthetic Mirror demo converts weaker than a real-data POC (~75%
  benchmark is Tier-2's, not Tier-1's) — Tier 1 opens doors, Tier 2 closes.
- **Tier 2 requires PDPA / data-residency design before touching any real
  data** (CLAUDE.md §8): real partner data is treated as PII → local MS-S1
  LLM only, never the hosted API. This is a hard gate, not a TODO.

### Neutral

- This is a strategic-posture change (productize onboarding) — hence an ADR
  + PLAN rather than ad-hoc code.
- Two PRs: this ADR merges **before** PLAN-0016's implementation PR
  (CLAUDE.md §8 "ADRs merged before related implementation").
- **Demo-shell affordance (consequence of D5):** live co-creation requires
  the OCT shell to expose **local-LLM (MS-S1) status + warm/sleep control
  in-UI** to the demo operator — vertical #4 needs MS-S1 *on* (NL query +
  rich reasoning) to land, and the operator must warm it and confirm it is
  resident *before* the stakeholder types. Building blocks verified in
  `services/api/routers/admin.py`: `GET /warm` with `?wait=false`
  background path (lines 53-69), `GET /sleep` (line 99), `client.ps()` via
  `_ps_safe` (line 40). The only new backend is a small **read-only,
  non-destructive `GET /llm/status`** (reachable + resident-from-`ps`,
  pollable — a poll must **never** call `/warm`); no such route exists
  today (verified). **Forward-declared as a small PLAN-0018, or folded
  into PLAN-0017** (Code/Cray call at dispatch time) — not drafted this
  round.

## Alternatives Considered

### Alternative A: Real-data-POC-first (skip the synthetic tier)
- Pros: highest conversion per engagement; no synthetic-credibility risk.
- Cons: no real-data adapter seam exists; mapping layer unbuilt; PDPA
  governance unbuilt; months before the first pitch artifact exists.
- Why rejected: sequencing — Tier 1 is shippable now (~80% there); Tier 2
  needs task (C) design first. Rejected as *first* step, retained as Tier 2.

### Alternative B: Hand-build each partner demo without a scaffolding command
- Pros: no engine/CLI work; fastest single demo.
- Cons: not repeatable; per-demo cost stays flat instead of amortizing;
  does not mint the 3rd-vertical capability or feed `_template/` extraction.
- Why rejected: the repeatability *is* the product thesis (D3); a one-off
  contradicts the forward-declared roadmap item.

### Alternative C: Defer until a 3rd vertical arrives organically
- Pros: purist Rule-of-Three reading; zero risk of premature abstraction.
- Cons: inverts the actual dependency — the generator's test case *is* the
  3rd vertical; deferring also forfeits the 2026 aquaculture
  competitive window (research §0).
- Why rejected: ADR-006 D4 is satisfied, not violated, by building now.

### Alternative D: Fuel-retail wetstock as the first showcase
- Pros: strongest measurable-$ baseline; resonates with the existing
  energy/supply-chain partner network.
- Cons: weaker 2026 whitespace (top of market saturated); audience is not
  the ratified one.
- Disposition: **not rejected — recorded as the audience-dependent
  alternate** per Cray's ratified decision (D4).

## Open Questions

- **OQ-1 (Cray adjudicates — carried, not resolved):** aquaculture is a
  "biological-asset cousin" of the parked Phase-2 vet vertical (ADR-005)
  but carries **no PII/PDPA burden** (sensor/operational data only — no
  clinical records). Does the roster framing need an ADR-005 note (e.g. a
  remark that the biological-asset family now has an active, non-clinical
  member), or does the resemblance not matter to the roster?
- **OQ-2 (recorded as resolved for this audience):** pick = aquaculture for
  the SE-Asian aquaculture audience; fuel-retail wetstock is the noted
  audience-dependent alternate (D4). Reopens only if the audience changes.
- **OQ-3 (recommender-direction generalization):** `OCT_RECOMMEND_DIRECTION`
  ships as an env knob (consistent with the other `OCT_RECOMMEND_*`
  settings; default `above` preserves existing verticals exactly). Does
  threshold direction belong in the **ontology/config contract** long-term
  (e.g. per-object-type alert semantics in YAML), or stay an env knob?
  Decide at `_template/` extraction time at the latest.
- **OQ-4 (intake mechanism — design choice for PLAN-0017's dispatch):**
  A2 guided form vs A3 conversational intake vs hybrid. Either way the
  human review/edit step of the LLM-drafted ontology is a **hard
  requirement** (D5), so the choice is about live-demo ergonomics and
  build cost, not about whether a human gates generation.

## References

- `docs/research/private/2026-06-04-vertical3-pick.md` — pick, rubric,
  partner-input package, full 2026 source list (~30 URLs).
- `.claude/handoffs/session-35/2026-06-04-0944-code-design-partner-demo-gen-feasibility.md`
  — feasibility fact-pack (file:line evidence; 2-tier refinement).
- `.claude/handoffs/session-36/2026-06-04-1438-code-cowork-taskB-adr-plan-dispatch.md`
  — authoring dispatch (Cray-ratified decisions).
- Engine evidence (verified live 2026-06-04): `services/engine/recommender.py:94,
  199-204, 215, 233-235`; `services/api/main.py:36-39`;
  `services/api/static/assets/api.js:113-120`; `services/api/config.py:114-172`;
  `verticals/_template/README.md`.
- External (key claims): eFishery sentencing —
  [SeafoodSource](https://www.seafoodsource.com/news/aquaculture/efishery-founder-sentenced-to-nine-years-in-jail) ·
  [Undercurrent News](https://www.undercurrentnews.com/2026/05/01/indonesian-court-sentences-efishery-founder-to-9-years-jail-time/);
  DO-crash physics — [Global Seafood](https://www.globalseafood.org/advocate/dissolved-oxygen-is-a-major-concern-in-aquaculture-heres-why/).

## Implementation Notes

- **PLAN-0016** builds the engine layer (Tier-1 Mirror-demo generator;
  aquaculture end-to-end as the headline acceptance criterion; the
  threshold-direction engine step is REQUIRED and PR-able on its own).
- **PLAN-0017 (forward-declared, not drafted):** the live-co-creation
  intake face — A2/A3(/hybrid) design per OQ-4, the LLM-extraction
  approach, and the mandatory ontology review/edit UX, invoking the
  PLAN-0016 engine. Its full draft is **its own dispatch after this ADR is
  accepted**.
- **PLAN-0018 (forward-declared, not drafted; may fold into PLAN-0017):**
  the small demo-shell build for the D5 consequence — read-only
  `GET /llm/status` + in-UI MS-S1 warm/sleep + residency indicator for the
  demo operator.
- Task (C) deep-research (Tier-2 real-data path: adapters, mapping layer,
  PDPA-safe ingestion) runs alongside and feeds the future Tier-2 ADR/PLAN.
- Status flips Proposed → Accepted on Cray ratification; Code applies the
  edit + commits (ADR-009 D2; CLAUDE.md §6 Decision Flow).
