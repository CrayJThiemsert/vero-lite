---
last_updated: 2026-06-07T22:30:23+07:00
session: 42
current_batch: Session 42 — **PLAN-0019 (Core Procedure baseline, Phase 1) earmarked, drafted, reviewed, and committed via #193 (`69c1ddf`, `docs(plans):`).** PLAN-0019 implements **ADR-0016 Phase 1** as a **MERGE-with-guardrails**: one PLAN, two internal Parts, a HARD GATE between them. **Part A — Engine** (deterministic functional acceptance): the `Procedure/Step/PipelineRun/Agent` runtime + a linear, set-valued, sequential orchestrator over `{query, evaluate, action, human_task}`; default-`gated` actions + autonomy-ceiling + handler allowlist; durable suspend→resume; fail-and-divert; **reuses the shipped ADR-007 `RecommendedAction` envelope + approve→execute gate verbatim**; a mandatory per-step telemetry seam feeds Part B; lands via `feat/*` PRs. → **HARD GATE** (Part B may not start until Part A is green) → **Part B — Benchmark** (empirical acceptance): pre-registered absolute thresholds; the text-to-SQL + RAG comparison is **REPORTED, not gated**; below-threshold = a logged finding → a follow-up tuning PLAN that **must not reopen ADR-0016's primitive shape** (ring-fence); closes evidence-gap **G-3** (per-procedure local-LLM model selection); lands via its own `test/*` PR. This folds the former "Thread 2" into PLAN-0019's acceptance under guardrails. **LOCKED scope:** **L-1** `manual` trigger only (orchestrator trigger-agnostic; `schedule` deferred to a PLAN-0010 reuse); **L-2** three OCT example procedures (aquaculture "Morning Pond Health Round" headline + energy + supply_chain; `vet_clinic` excluded, parked ADR-005); **L-3** Postgres persistence via Alembic. **Architectural SDs ratified this session:** **SD-A1** (JSONB `pipeline_runs`/`step_results` schema) + **SD-A2** (engine home `services/engine/procedures/`). **B-side SDs stay OPEN** (resolved at their execution step): **SD-B1** pre-registered thresholds (MUST be Cray-ratified before any Part B run — anti moving-target), **SD-B2** synthetic-dataset size, **SD-B3** the optional G-2 build-cost measure. **Drafted by the `plan-drafter` subagent, reviewed by Code (reuse symbols verified against live `services/engine/{actions,recommender,registry}.py`), G2-approved + ratified by Cray, committed via #193.** Prior context: Session 41 — **strategy/design session that worked Thread 1 (of the two session-41 kickoff strategy threads) all the way to a ratified ADR.** **ADR-0016 — Governed Procedure Engine — ratified Accepted + merged (#190, `949eaea`, `docs(adr):`).** It expands the OCT action layer from reactive-only `anomaly→action` to **`anomaly AND normally→action`** via a governed, human-gated **Procedure engine** — a reusable cross-vertical capability (capability/decision document only; implementation is PLAN-0019). Arc: started from the session-40 dual-track impl-approach research (the action layer is vero-lite's differentiator); worked Cray's vision (stakeholder narrative → ontology → **pipeline** of goal/decision/tool-call/trigger/terminal/human-gate, OCT as the Command/Control/Monitor center, referencing Palantir Foundry pipeline docs, scoped DOWN to a tangible/measurable/extensible baseline) through **path 2 (shape-sharpening)** then **path 3 (stress-test vs the real aquaculture ontology)**, iterating shape v0→**v3.3**. Two design seams caught + resolved: human_gate collapsed into the `gated` autonomy property; human-task relocated from autonomy class → step `kind`. Grounded twice against Palantir — a quick WebSearch/WebFetch pass, then a **`deep-research` workflow** (5 concerns, **25 claims verified 3-0 / 0 killed**, all primary palantir.com/docs) → saved private/gitignored at `docs/research/private/2026-06-07-palantir-5-concerns-pipeline-design.md`: agent-as-actor (→ first-class `Agent`), Automate fail-and-divert failure semantics (NO run-status enum → we add one), per-WRITE approval (autonomy on `action` only), goal = runtime LLM directive, engine-vs-config = Marketplace bundles (validates the `services/` engine + `verticals/<name>/` config split + Rule-of-Three). The ADR records the **`Procedure / Step / PipelineRun / Agent`** primitive (kind = query/evaluate/action/human_task; autonomy auto/gated on `action` only, default gated; set-valued linear steps; durable/resumable runs; goal=LLM directive; local-LLM bindable per Agent, default `gpt-oss:20b`), purely **ADDITIVE** (does NOT touch the ADR-007 `RecommendedAction` envelope nor the ADR-008 six-`object_types` ontology), positioned at the safe end of the agentic spectrum. Drafted by the `plan-drafter` subagent, reviewed by Code, **G2-approved + ratified by Cray**. Prior context (session 40, carried): first item off the session-40 backlog menu shipped: the standing **ADR-0015 §7 citation errata** (J-class, non-blocking) landed as **#175 (`45012de`, `docs(adr):`)** — ADR-0015 Decision **D5**'s human-review citation `research §7 risk` → `fact-pack §6` (research §7 is the Sources URL list, not a risk; the SOTA-consensus human-review substance lives in the session-35 feasibility fact-pack §6, which ADR-0015's own Consequences already cites correctly). One line changed; no decision/substance touched. **G1 always-pause (mutate an Accepted ADR) was explicitly Cray-approved for the exact diff before the edit.** Context (carried from session 39, unchanged): **PLAN-0017 — the OCT Tier-1 Mirror-demo / live co-creation intake FACE — stays Done** (in `done/`), so the Mirror-demo capability is complete. Also session 40: **run-oct-demo §5b reviewed + fixed** (#177, `2219da1`, `docs(runbook):`) — a code-grounded review of the live co-creation walkthrough surfaced one real bug + three completeness notes (**F1** the §5b worked example booted vertical #4 on port 8099, the §3a aquaculture showcase's own port → live-demo collision; moved to free port 8100; **F2** a §8 409-clobber-guard troubleshooting entry; **F3** the `/intake/*` routes added to References; **F4** a header PLAN-0016/0017 lineage note). The live-demo runbook is now collision-free. Plus a UI polish (#179, `7c9c1f2`, `feat(ui)`): surfaced from a live aquaculture-demo log showing repeated `GET /favicon.ico 404` (the harmless browser default-icon probe — StaticFiles at `/` had no favicon), added an OCT favicon (`static/assets/favicon.svg`, reusing the blue operational-grid + green-status-dot shell identity) + a `<link rel="icon">` so modern browsers use it and stop probing `/favicon.ico`; the partner-facing tab now shows a real OCT mark. Then a demo-prep docs add (#181, `3653d13`, `docs(runbook):`): bilingual (ไทย/EN) per-vertical demo narratives for all three pre-built verticals (§6a — scene→A→B→C→D→number, grounded in the verified on-screen values) + a new **§6b Screen E "Build a Vertical"** section (the missing 4th-vertical / live-co-creation narrative — the 8-step show-sequence within the #3 demo, the golden pivot question, the human-gate-as-feature framing, boot #4 on 8100, fallbacks, closing line); §6 also gained the missing Screen E bullet. Finally a header UI fix (#183, `cc7f3d3`, `fix(ui)`): the demo shell's top bar (brand + A–E nav + chips + MS-S1 + Refresh) overflowed ~1280px screens — the MS-S1 residency control (which gates NL query + Build-a-Vertical) clipped off the right edge (surfaced from Cray's live aquaculture demo; full header ~1487px wide). Re-proportioned by importance: pinned the status + nav zones so they never clip, shed least-important-first across breakpoints (≥1500 all shown; 1201–1499 incl. ~1280 drop the context chips + Refresh→icon, keeping full A–E labels + the MS-S1 control; ≤1200 tabs collapse to A–E keys). Live-verified via Preview at 1600/1280/1200 (0 overflow, MS-S1 fully visible). Follow-up **#185** (`3aac38b`, `fix(ui)`) keeps the **VERTICAL identity chip visible at every width** (per Cray: multiple verticals run side-by-side on different ports, so each window must always show which one it is): only the redundant NS/version chips drop on narrow screens, and the room is reclaimed by collapsing the *inactive* tab labels to A–E keys (the active screen keeps its label) — the MS-S1 status still never clips (verified 1600/1440/1280).
current_actor: code
blocked_on: Nothing gates shipped work. main clean @ `24f9ed3` (merge of #193); **0 open PRs**. **ADR-0016 Accepted**; **PLAN-0019 committed (Ready for execution)**. **PLAN-0016 Done**, **PLAN-0017 Done**, **PLAN-0018 Done** (all in `done/`). PLAN-0010 autonomy loop LIVE.
next_action: **→ PLAN-0019 is committed (#193, `69c1ddf`) and Ready for execution.** Next = begin **Part A** build — Step **A-α** spec layer → **A-β** run records / migration → **A-γ** orchestrator → **A-δ** durable suspend/resume → **A-ε** action-step adapter + goal injection → **A-ζ** three example procedures → **A-η** headline integration test + invariants — via `feat/*` PRs. The **HARD GATE** precedes Part B; **SD-B1 thresholds MUST be Cray-ratified before any Part B run** (anti moving-target). Sequencing (start Part A now vs. pause) is **Cray's call**. Reference the still-active handoff `.claude/handoffs/session-42/2026-06-07-1537-code-session42-procedure-engine-kickoff.md`. · **Prior context (SESSION 42 reconcile):** `.claude/handoffs/session-42/2026-06-07-1537-code-session42-procedure-engine-kickoff.md` (locked design shape v3.3 + the two Cray-gated next items). **→ Earmark PLAN-0019 = Phase 1 "Core Procedure baseline"** — the `Procedure/Step/PipelineRun/Agent` runtime + a linear set-valued orchestrator over {query, evaluate, action, human_task} + one hand-authored example procedure per vertical (e.g. aquaculture "Morning Pond Health Round"). Earmarking PLAN-0019 = **G2 always-pause → needs explicit Cray approval** of the number + scope before any `docs/plans/0019-*.md` Write. **Still pending from the kickoff agenda: Thread 2** — empirical gap-testing on synthetic/ungated data (no real data, no PDPA/heavy-spend gate) — and the **per-procedure local-LLM model-selection benchmark** (closes evidence-gap G-3) folds into Thread 2; both feed/shape PLAN-0019's acceptance measures. · **Prior context (Thread 1 now LANDED as ADR-0016):** the session-41 kickoff named two Cray strategy threads gating the PLAN-0019 decision — **(1)** expand the action layer to `anomaly AND normally→action` as a reusable cross-vertical engine (DONE → ADR-0016 Accepted, #190); **(2)** deep-research + **SIMPLE TESTING** to fill the evidence-gaps (benchmark OUR stack vs text-to-SQL/RAG on synthetic ops data; measure local-LLM latency + build-cost) — still open as Thread 2. **Two Cray strategy threads now GATE the PLAN-0019 decision:** **(1)** expand the action layer from `anomaly→action` to **`anomaly AND normally→action`** — governed **agentic** execution of a vertical's NORMAL operating workflow (sequence captured from stakeholder workflow interviews) as a **reusable cross-vertical engine** (likely its own ADR; on-thesis with our safe/human-gated agentic posture vs the agentic "reliability gap"). **(2)** deep-research + **SIMPLE TESTING** to fill the 4 evidence-gaps — benchmark OUR stack vs text-to-SQL/RAG on **synthetic** ops data (gives our own numbers; **ungated — no real data, no PDPA/heavy-spend gate**) + measure local-LLM latency + build-cost via the `new-vertical` demo. Work threads 1+2 THEN lock PLAN-0019 scope (Code leans option **B**; but thread-2 testing may BE PLAN-0019, reframing it from Tier-2-real-data to empirical-validation). Earmarking PLAN-0019 = **G2 always-pause** → explicit Cray approval first. · Prior context: **Dual-track impl-approach research DONE + RECONCILED** (Cray-routed 2026-06-06) — comparing vero-lite's ontology/semantic-layer vs RAG/GraphRAG · text-to-SQL · semantic/metrics layer · fine-tuning/agentic, for a stakeholder **conviction** artifact (the product = an implementation service connecting a customer's structured+unstructured data to LLM/Agentic AI). **Code track DONE** → `docs/research/private/2026-06-06-impl-approach-vs-alternatives-code.md` (private/gitignored; `deep-research` skill, 25 sources / 23 verified claims): text-to-SQL collapses on real enterprise schemas (o1-preview 91→21%, GPT-4o ~0% on BEAVER), a semantic layer adds +17–23pp + flips the failure mode silent-wrong→explicit-error (= our "no data" answer), Dialpad/Palantir endorse the *principle* (LLM-as-planner; Ontology nouns+verbs+human-gate). **Honest caveats:** vendor-biased headline numbers + NO direct benchmark of our exact codegen-YAML stack + NO build-cost / local-LLM / RAG-coexistence numbers. **Cowork track DONE** (`...-cowork.md`, authored independently, **strongly convergent** with Code — same headline numbers + same framing). **Reconciliation** → `docs/research/private/2026-06-06-impl-approach-reconciliation.md`: seams (a) A-vs-D tied-at-5 / (b) keep A unstructured=weak / (c) primary-vs-directional source split — all resolved; **4 evidence-gaps confirmed** (no direct benchmark of our stack; no build-cost / local-LLM / RAG-coexistence numbers) → **task (C) sub-questions**. **AWAITING CRAY:** disposition per ADR-009 D2 (keep private vs lift a sanitized synthesis vs spin the gaps into a committed task-(C) feed — Code recommends the task-(C) feed), conviction-deck greenlight, + a flagged **K-2 harness observation** (Cowork's `.claude/` write-block was not enforced this session — lifted or situational?). — Then the standing backlog: **Task (C)** deep-research the Tier-2 real-data path (real `DataAdapter` CSV/DB/API, dbt/SQLMesh mapping layer, PDPA-safe local-LLM-only ingestion) — heavy spend → Cray green-lights; plus the standing backlog — PLAN-0010 loop handlers (soak-gated), `status_digest` v2, PLAN-004 Phase C, PLAN-0012 Phase 2 (gated). **Highest leverage stays Cray-side: run the live "build your own vertical" demo for a design partner (runbook §5b), and design-partner outreach.**
head_commit: 69c1ddf
recent_commits: [24f9ed3, 69c1ddf, 82d251c, 4bcb1a6, d78ff8a, ce7e7ea, b5d6a99]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 42 (current) — PLAN-0019 (Core Procedure baseline, Phase 1)
> earmarked, drafted, reviewed, and committed via #193 (`69c1ddf`,
> `docs(plans):`).** ADR-0016's Phase 1 now has an executable plan. PLAN-0019
> was G2-approved by Cray, drafted by the `plan-drafter` subagent, reviewed by
> Code (reuse symbols verified against the live
> `services/engine/{actions,recommender,registry}.py`), and committed via #193.
> This PR = the session-42 reconcile (head `69c1ddf`; merge `24f9ed3`).
>
> **Shape: MERGE-with-guardrails.** PLAN-0019 implements ADR-0016 Phase 1 as
> **one PLAN, two internal Parts, a HARD GATE between them** — folding the
> former "Thread 2" empirical work into PLAN-0019's acceptance rather than a
> separate plan, but ring-fenced so the benchmark cannot silently reshape the
> primitive.
>
> **Part A — Engine (deterministic functional acceptance).** The
> `Procedure / Step / PipelineRun / Agent` runtime + a **linear, set-valued,
> sequential orchestrator** over `{query, evaluate, action, human_task}`;
> **default-`gated` actions** + autonomy-ceiling + handler allowlist; **durable
> suspend → resume**; **fail-and-divert**; it **reuses the shipped ADR-007
> `RecommendedAction` envelope + approve→execute gate verbatim** (additive, no
> envelope change); a mandatory **per-step telemetry seam** feeds Part B. Lands
> via `feat/*` PRs.
>
> **HARD GATE → Part B — Benchmark (empirical acceptance).** Part B may not
> start until Part A is green. Pre-registered **absolute** thresholds; the
> text-to-SQL + RAG comparison is **REPORTED, not gated** — below-threshold is
> a logged finding that spawns a follow-up **tuning PLAN that must not reopen
> ADR-0016's primitive shape** (the ring-fence). Closes evidence-gap **G-3**
> (per-procedure local-LLM model selection). Lands via its own `test/*` PR.
>
> **LOCKED scope + ratified decisions.** **L-1** `manual` trigger only
> (orchestrator stays trigger-agnostic; `schedule` deferred to a PLAN-0010
> reuse); **L-2** three OCT example procedures (aquaculture **"Morning Pond
> Health Round"** headline + energy + supply_chain; `vet_clinic` excluded,
> parked ADR-005); **L-3** Postgres persistence via Alembic. **Architectural
> SDs ratified this session:** **SD-A1** (JSONB `pipeline_runs` /
> `step_results` schema) + **SD-A2** (engine home `services/engine/procedures/`).
> **B-side SDs stay OPEN**, resolved at their execution step: **SD-B1**
> pre-registered thresholds (**MUST be Cray-ratified before any Part B run** —
> anti moving-target), **SD-B2** synthetic-dataset size, **SD-B3** the optional
> G-2 build-cost measure.
>
> **Next (gated).** PLAN-0019 is **Ready for execution**. Next = begin **Part A**
> (Step A-α spec → A-β run records/migration → A-γ orchestrator → A-δ durable
> suspend/resume → A-ε action-step adapter + goal injection → A-ζ three example
> procedures → A-η headline integration test + invariants) via `feat/*` PRs;
> the **HARD GATE** precedes Part B; **SD-B1 thresholds must be Cray-ratified
> before any Part B run**. Whether to start Part A now or pause is **Cray's
> call**. Reference the still-active handoff
> `.claude/handoffs/session-42/2026-06-07-1537-code-session42-procedure-engine-kickoff.md`.
>
> **Session 41 — ADR-0016 (Governed Procedure Engine) ratified
> Accepted + merged (#190, `949eaea`, `docs(adr):`).** A strategy/design
> session that worked **Thread 1** of the two session-41 kickoff strategy
> threads all the way to a ratified ADR. ADR-0016 expands the OCT action layer
> from reactive-only `anomaly→action` to **`anomaly AND normally→action`** via
> a governed, human-gated **Procedure engine** — a reusable cross-vertical
> capability. This is a **capability/decision document only**; the
> implementation is PLAN-0019.
>
> **The arc.** Started from the session-40 dual-track impl-approach research
> (the action layer is vero-lite's differentiator). Cray's vision: stakeholder
> narrative → ontology → **pipeline** (goal / decision / tool-call / trigger /
> terminal / human-gate), with OCT as the Command/Control/Monitor center —
> referencing Palantir Foundry pipeline docs, scoped DOWN to a tangible,
> measurable, extensible baseline. Worked the design through **path 2
> (shape-sharpening)** then **path 3 (stress-test vs the real aquaculture
> ontology)**, iterating shape v0 → **v3.3**. Two design seams were caught +
> resolved: **human_gate collapsed into the `gated` autonomy property**, and
> **human-task relocated from autonomy class → step `kind`**.
>
> **Grounded twice against Palantir.** A quick WebSearch/WebFetch pass, then a
> **`deep-research` workflow** (5 concerns, **25 claims verified 3-0 / 0
> killed**, all primary palantir.com/docs) → saved private/gitignored at
> `docs/research/private/2026-06-07-palantir-5-concerns-pipeline-design.md`.
> Findings: agent-as-actor (→ first-class `Agent`); Automate fail-and-divert
> failure semantics (there is **NO run-status enum** in Foundry → we add one);
> per-WRITE approval (autonomy on `action` only); goal = runtime LLM directive;
> engine-vs-config = Marketplace bundles (validates our `services/` engine +
> `verticals/<name>/` config split + the Rule-of-Three).
>
> **What the ADR records.** The **`Procedure / Step / PipelineRun / Agent`**
> primitive: kind = query / evaluate / action / human_task; autonomy auto/gated
> on `action` only, default **gated**; set-valued linear steps; durable /
> resumable runs; goal = LLM directive; local-LLM bindable per Agent (default
> `gpt-oss:20b`). It is purely **ADDITIVE** — it does NOT touch the ADR-007
> `RecommendedAction` envelope nor the ADR-008 six-`object_types` ontology — and
> sits at the safe end of the agentic spectrum. **Drafted by the `plan-drafter`
> subagent, reviewed by Code, G2-approved + ratified by Cray.** This PR = the
> session-41 reconcile (head `949eaea`; merge `b5d6a99`).
>
> **Next (gated).** Earmark **PLAN-0019 = Phase 1 "Core Procedure baseline"**
> (the `Procedure/Step/PipelineRun/Agent` runtime + a linear set-valued
> orchestrator over {query, evaluate, action, human_task} + one hand-authored
> example procedure per vertical — e.g. aquaculture "Morning Pond Health
> Round"). Earmarking PLAN-0019 = **G2 always-pause** → explicit Cray approval
> of the number + scope before any `docs/plans/0019-*.md` Write. Still open from
> the kickoff agenda: **Thread 2** (empirical gap-testing on synthetic/ungated
> data) — and the per-procedure local-LLM **model-selection benchmark** (closes
> evidence-gap G-3) folds into Thread 2; both feed/shape PLAN-0019's acceptance
> measures.
>
> **Session 40 — ADR-0015 §7 citation errata shipped (J-class,
> non-blocking) as #175 (`45012de`, `docs(adr):`).** A one-line fix: ADR-0015
> Decision **D5**'s human-review citation `research §7 risk` → `fact-pack §6`
> — research §7 is the Sources URL list, not a risk; the SOTA-consensus
> human-review substance is in the session-35 feasibility fact-pack §6, which
> ADR-0015's own Consequences already cites correctly. No decision or
> substance touched. **G1 always-pause (mutating an Accepted ADR) was
> explicitly Cray-approved for the exact diff before the edit.** This is the
> first item off the session-40 backlog menu; the OCT **Tier-1 Mirror-demo
> capability** (PLAN-0017) stays **Done** from session 39. This PR = the
> session-40 reconcile (head `7314dc4` → `45012de`; merge `d94c13b`).
>
> **Also session 40 — run-oct-demo §5b reviewed + fixed (#177, `2219da1`,
> `docs(runbook):`).** A code-grounded review of the live co-creation
> walkthrough — the headline Cray-side demo action: the flow + every UI
> label/badge/fallback was verified accurate to `intake-view.js` /
> `routers/intake.py`. Four findings applied (F1–F4): **F1 (bug)** the §5b
> worked example booted vertical #4 on port **8099 — the §3a aquaculture
> showcase's own port** → "Port already in use" in a live demo; moved #4 to
> free port **8100** + a port-choice note (8099 stays §3a); **F2** a §8
> troubleshooting entry for the 409 clobber-guard on re-rehearsing a
> namespace; **F3** the `/intake/*` routes added to the References; **F4** a
> header lineage note (aquaculture #3 = PLAN-0016, the Build-a-Vertical face =
> PLAN-0017). The live-demo runbook is now collision-free.
>
> **Also session 40 — OCT favicon (#179, `7c9c1f2`, `feat(ui)`).** Surfaced
> from a live aquaculture-demo log showing repeated `GET /favicon.ico 404`
> — the harmless browser default-icon probe (`StaticFiles` mounted at `/`
> had no favicon + no `<link rel="icon">`). Added an SVG favicon
> (`static/assets/favicon.svg`, reusing the blue operational-grid +
> green-status-dot shell identity) + a `<link rel="icon">` in `index.html`;
> modern browsers now use it and stop probing `/favicon.ico`, and the
> partner-facing tab shows a real OCT mark. No logic change; verified
> offline (well-formed SVG; serves via the proven `assets/*` static path).
>
> **Also session 40 — demo-prep narratives (#181, `3653d13`,
> `docs(runbook):`).** The runbook had per-screen pitch notes (§6, Screens
> A–D) but no per-vertical *story to tell* and no Screen E coverage. Added
> **§6a** — bilingual (ไทย/EN) scripts for all three pre-built verticals
> (energy / supply_chain / aquaculture), each scene → A → B → C → D → number,
> grounded in the verified on-screen values — and **§6b** — the missing
> **Screen E "Build a Vertical"** narrative: the 8-step show-sequence (where
> the live co-creation moment fits in the #3 demo, the golden pivot question,
> the human-gate-as-feature framing, boot #4 on 8100, fallbacks, closing
> line). §6 gained the missing Screen E bullet.
>
> **Also session 40 — header UI fix (#183, `cc7f3d3`, `fix(ui)`).** Cray's
> live aquaculture demo showed the **MS-S1 status control clipped off the
> right edge** at ~1280px — it gates NL query + Build-a-Vertical, so losing
> it mid-demo is bad. The top bar is one non-wrapping flex row ~1487px wide.
> Re-proportioned by importance: the status + A–E nav zones are pinned (never
> clip), and the header sheds least-important-first across breakpoints (≥1500
> all shown; 1201–1499 — incl. ~1280 — drop the vertical chips + Refresh→icon,
> keeping full tab labels + the MS-S1 control; ≤1200 tabs collapse to A–E
> keys). CSS-only; live-verified via Preview (0 overflow, MS-S1 visible at
> 1600 / 1280 / 1200). **Follow-up #185 (`3aac38b`)** then made the **VERTICAL
> identity chip always-visible** (Cray runs several verticals side-by-side, so
> each window must show which one it is): only the redundant NS/version chips
> drop on narrow screens; the room comes from collapsing *inactive* tab labels
> to A–E keys (the active screen keeps its label). MS-S1 still never clips.
>
> **Session 39 — PLAN-0017 (the live co-creation intake FACE)
> SHIPPED end-to-end and is now Done (in `done/`), across four PRs
> (#170–#173).** The headline next-action from session 38 — the *face* layer
> of ADR-0015 D5 — went from Draft → implemented → archived this session. The
> face turns a live free-text domain description into a runnable "Mirror demo"
> **vertical #4**: it is a **caller** that drafts a partner-input package,
> gates it behind a **mandatory human review/edit**, and invokes the PLAN-0016
> `vero-lite new-vertical` engine **unchanged** (**AC-5**). **#170 (`81792e4`,
> `feat(engine)`) — Step 1:** `services/engine/intake_assembler.py` — the
> `IntakePackage` contract + a deterministic **constrained-slot → canonical
> six-type OCT ontology YAML** assembler (valid by construction — guarantees
> the three `scaffold.detect_roles` invariants, templated off
> `aquaculture_v0.yaml`); `services/engine/llm/intake.py` `extract_package`
> mirroring `structured.py` (MS-S1-local `gpt-oss:20b` **only**, never the
> hosted API — CLAUDE.md §8 / **AC-4**; the stakeholder's **UNTRUSTED** text is
> injection-contained per ADR-010 D4 / **IN-2**; omits `think` per
> **CHECKPOINT-0**); plus two **source-tagged prebaked starter** packages
> (`solar_farm` overrun / `water_utility` crash) as the AC-4 fallback. **20
> tests.** **#171 (`7090775`, `feat(api)`) — Step 2:**
> `services/api/routers/intake.py` — `POST /intake/extract` (graceful,
> non-silent degradation), `GET /intake/defaults`, and `POST /intake/generate`,
> the **server-enforced human gate** that refuses any package not explicitly
> `confirmed` (**AC-2** no-bypass — extract and generate are separate;
> generate never calls extract). **11 tests** incl. the safety-critical **AC-2
> no-bypass + edit-propagation** (a gate edit provably reaches the generated
> artifacts), AC-3 below-direction, AC-5 clobber-guard. **#172 (`a2a9fda`,
> `feat(ui)`) — Step 3:** **View E "Build a Vertical"** in the demo shell
> (`assets/intake-view.js` + the `Intake` api helper, **no mock fallback**) —
> capture (free-text + MS-S1 residency hint consuming `GET /llm/status`) → the
> **source-badged review/edit gate** (`MS-S1 EXTRACTION` / `PREBAKED STARTER`
> / `MANUAL ENTRY`) → the single explicit **"Confirm & build vertical #4"** →
> result. Live-verified via Claude Preview. **#173 (`7314dc4`, `docs(plans)`)
> — Step 6 closeout:** PLAN-0017 → `done/` (Status: Done, all **6 ACs**
> checked) + run-oct-demo runbook **§5b** (the live co-creation walkthrough:
> the separate-port #4 boot mechanics + the AC-4 fallbacks + the ephemeral-#4
> cleanup).
> **Design decisions (this session, Cray-ratified):** (1) **constrained-slot
> extraction** (the LLM fills bounded domain slots; the face assembles the OCT
> skeleton deterministically) over free-form YAML emission — far more robust +
> makes AC-2 edit-propagation provable; (2) a **prebaked-default fallback**
> added as an AC-4 enrichment that holds the §8 no-hosted-extraction line (own
> fixtures, nothing leaves the box).
> **Live AC-1 verification (session 39, MS-S1 resident):** a free-text
> district-heating description → live `gpt-oss:20b` extraction that
> **correctly inferred `direction=below`** for the pressure crash → a
> `recovery_value` edit made in the gate **propagated into the generated env
> block** (live **AC-2** edit-propagation) → Confirm → `vero-lite new-vertical`
> → vertical #4 (`BoilerPlant` / `Neighborhood`) booted on a **separate port**:
> map geo loaded, NL query answered grounded (*"There is one boiler plant:
> BoilerPlant 01"*), and the below-breach fired recommend → approve → execute
> (the `ontology_query → llm_inference → rule_check` trace). #4 was
> **ephemeral** (reverted after — PLAN-0017 out-of-scope "no intake history
> store"). Full suite **1208 passed / 2 skipped**; ruff + `mypy services`
> clean throughout. With PLAN-0017 shipped, the OCT **Tier-1 Mirror-demo
> capability** (ADR-0015 D5 — engine + intake face + the three OCT features +
> the live "show #3 → build #4" moment) is **complete**. **PLAN-0016 stays
> Done; PLAN-0018 stays Done; PLAN-0017 is now Done** (all in `done/`). This PR
> = the session-39 reconcile (head `612601b` → `7314dc4`).
>
> **Session 38 — PLAN-0018 (demo-shell LLM control) SHIPPED
> end-to-end and is now Done (in `done/`), across three PRs (#166–#168).**
> The forward-declared, standalone deliverable from the session-37 next-action
> went from Draft → implemented → archived this session. **#166 (`d0c2e5d`,
> `feat(api)`) — Step 1 backend:** the read-only, pollable **`GET /llm/status`**
> reporting MS-S1 reachability + residency of the pinned recommender
> `gpt-oss:20b` (ADR-0001), built on `OllamaClient.ps()` (`GET /api/ps`) **only**
> — the poll never loads the model (**INV-1**) and is non-destructive (**INV-2**).
> State machine **unreachable / cold / resident / error** (a reachable-but-errored
> host is never a false `cold`); right-model residency with tolerant tag matching;
> a short dedicated `llm_status_timeout_s` (3.0 s) decoupled from the ~120 s
> generation timeout; expiry honesty (an expired `expires_at` → `cold`,
> remaining-time surfaced); a typed Pydantic response model. **15 offline tests**
> prove INV-1/INV-2 via `httpx.MockTransport` request-recording — the requested
> path set is **exactly `{GET /api/ps}`**, never `/api/generate` — plus AC-3…AC-6.
> Suite **1177 passed / 2 skipped**. **#167 (`71e6c2d`, `feat(ui)`) — Step 2
> demo-shell affordance:** an in-header MS-S1 control (`assets/llm-control.js`) —
> a residency indicator polling `/llm/status` every 5 s (**D-1**: documented
> client interval, no server cache; the LLM calls bypass the api.js mock fallback
> so a mocked "resident" can't lie), a **non-blocking Warm** (`GET /warm?wait=false`
> → instant WARMING… overlay → poll-to-resident, never the ~11 s page freeze), and
> a **guarded two-click Sleep** (arm → "Confirm?" → confirm, auto-disarms).
> **Verified live via Claude Preview against the real MS-S1** (`gpt-oss:20b`): the
> full operator cycle RESIDENT → guarded-sleep → COLD → warm (WARMING…) →
> RESIDENT, right-model match proven while `qwen3.6:35b` was *also* resident, a
> real nanosecond `expires_at` parsed, 0 console errors. **#168 (`612601b`,
> `docs(plans)`) — Step 3 closeout:** PLAN-0018 → `done/` with a per-step→PR
> completion table, plus run-oct-demo runbook **§5a** (the in-UI MS-S1 pre-warm
> checklist — the PLAN-0017 Step 6 seam). The session-38 dispatch's risk register
> **R1–R10** + INV-1/INV-2 all landed as test-proven ACs or resolved delegated
> decisions. ruff + `mypy services` clean throughout. **PLAN-0016 stays Done;
> PLAN-0018 is now Done (in `done/`); PLAN-0017 stays Draft** — now UNBLOCKED and
> also building against the shipped `GET /llm/status` route (its AC-4 "non-silent
> state" + Step 5 warm/status substrate). This PR = the session-38 reconcile (head
> `0f4d341` → `612601b`).
> Earlier this session the plan itself was committed as a Draft (the authoring
> beat now superseded by the implementation above).
> **Session 38 (plan-authoring beat) — committed PLAN-0018 (Draft): the
> demo-shell LLM control plan (#164, content `0f4d341`, `docs(plans)`).** The
> forward-declared, standalone deliverable from the session-37 next-action.
> PLAN-0018 specifies a **read-only, pollable `GET /llm/status`** — surfacing
> MS-S1 reachability + the residency of the pinned recommender `gpt-oss:20b`
> (ADR-0001) **without the poll ever loading the model** — plus an **in-UI
> warm/sleep affordance** for the demo operator, composed from the existing
> `GET /warm` / `GET /sleep` (PLAN-0014) plus the new status poll. Two
> non-negotiable, **test-proven invariants** anchor the contract: **INV-1** the
> poll **never warms** (it may hit `GET /api/ps` only, never `/api/generate`);
> **INV-2** read-only / non-destructive. The session-38 dispatch's grounded
> risk register **R1–R10** folds into **AC-1…AC-9** plus two explicit
> **delegated decisions** — **D-1** (poll cache-TTL vs. interval) and **D-2**
> (route shape / field names / enum literals / probe timeout number / UI-CSS)
> — contract specified, implementation left to Code's follow-up PR.
> **Cowork-drafted** (ADR-009 D1), **Code-reviewed on receive** per Lesson #8
> K-1/K-2 (completion-handoff validator-passed; R2 veto clean — every cited
> path resolves at HEAD, the `config.py` line claims verified, risk-register
> coverage **complete**), and **committed** per ADR-009 D2. **Standalone +
> forward-declared** (ADR-0015 Consequences §Neutral); deliberately **ships
> before PLAN-0017** (Cray-ratified) so the intake face builds **once** against
> the real status route — the status contract is exactly PLAN-0017 AC-4's
> "clear, non-silent state" degradation substrate. A drafter erratum was
> corrected in-plan: the warm/sleep recovery substrate is **PLAN-0014** (the
> ADR-0014 slot is the withdrawn tombstone). Plan-only PR — no code/test/schema
> change, suite count unchanged. PLAN-0016 stays **Done**; PLAN-0017 stays
> **Draft** (now also unblocked against the status route); PLAN-0018 is **Draft
> (committed)** with implementation as Code's next lane. This PR = the
> session-38 reconcile (head `1dbd202` → `0f4d341`).
>
> **Session 37 — design-partner demo-generator track, Phase 1
> engine FULLY SHIPPED: PLAN-0016 (`vero-lite new-vertical` scaffolding
> engine) Steps 0–6 done + archived to `done/` (6 PRs, #156–#161).** The
> **engine layer** of ADR-0015 D5 — the substrate the PLAN-0017 intake face
> calls — is complete and dogfooded.
> **#156 (`3b4083f`, `feat(engine)`) — Steps 1+3+4:** the `new-vertical <ns>`
> Typer command + `services/engine/scaffold.py`. Role detection from the
> ontology (Site = the geo-bearing `lat`+`lng` object type; Asset = the other
> `OperationalEvent` ref target — proven against the domain-renamed
> `supply_chain` = Shipment/Facility), a **deterministic minimal-but-runnable**
> `synthetic.py` draft (baseline + the direction-aware breach), templated
> boilerplate (adapter/handlers/README/env block), an **idempotent
> `_VERTICAL_REGISTRARS` code-mod** of `services/api/main.py`, a clobber guard
> (`--force`). Sequencing call: deterministic synthetic ships first (the
> command always produces a runnable vertical, CI stays deterministic); the LLM
> layer is #160.
> **#159 (`5156098`, `feat(verticals)`) — Step 5 / AC-1:** the **aquaculture**
> vertical #3 (the ratified ADR-0015 D4 pick) — the **first *below*-threshold
> breach** vertical (a dissolved-oxygen crash, 3.2 < 4 mg/L,
> `OCT_RECOMMEND_DIRECTION=below`). Authored the ontology (Pond/Farm/…; geo on
> Farm), **dogfooded `vero-lite new-vertical`** to scaffold it, then
> **human-reviewed** (ADR-0015 D5) the draft `synthetic.py` into the POND-07
> DO-crash timeline. **AC-1 proven end-to-end** by unit/integration tests **and
> a live HTTP smoke** (`OCT_VERTICAL=aquaculture`, rule path:
> `GET /recommendations` → exactly one proposed action, "Reading 3.2 mg/L on
> Pond pond-07 fell below the 4.0 mg/L threshold", `<=`/direction=below trace,
> pond-07). Bundled a scaffold-adapter-template mypy fix (drop the over-broad
> `_OBJECT_SOURCES: dict[str, Any]` annotation). `statusClass()` needed no
> extension (fallow/harvested → s-neutral, the accepted fallback).
> **#160 (`860cc58`, `feat(engine)`) — Step 2:** an opt-in **`--llm`** MS-S1
> LLM draft of `synthetic.py` (domain-plausible records from the ontology +
> problem statement), **semantically validated** (PKs/refs/enums + exactly one
> breaching reading that is the latest event), with a **deterministic fallback**
> on any failure (transport/JSON/invariant/non-local backend) so enrichment
> never breaks scaffolding. Extraction is MS-S1-local only (CLAUDE.md §8).
> **Live-verified against the pinned `gpt-oss:20b`** (ADR-0001 — the local model
> that reliably honours the `format` JSON-schema constraint; 2 sites/4 assets/7
> events, a below-direction breach, every semantic check passing). *(Provenance
> correction: the first session-37 smoke mistakenly used `qwen3.6:35b` — which
> ADR-0001 flags `NOT_JSON` under `think=false` — off a truncated `/api/tags`
> read; the shipped code always pinned `gpt-oss:20b`, re-verified clean.)*
> **#161 (`1dbd202`, `docs(plans)`) — Step 6 closeout:** PLAN-0016 → `done/`
> (Status: Done + a per-step→PR completion table), the run-oct-demo runbook
> **§3a aquaculture** walkthrough (env block + the DO-crash below-direction
> known-good baseline), and this STATUS reconcile.
> **Also this session — the PLAN-0017 intake-face governance (the ADR-0015 D5
> *face* layer): #157 (`d68711e`, `docs(plans)`)** committed **PLAN-0017**
> (Cowork-drafted uncommitted per ADR-009 D1; Code-committed per D2) — the
> live-co-creation intake face: capture a live human domain description → MS-S1
> LLM extraction of the partner-input package → a **mandatory human review/edit
> gate** → invoke the PLAN-0016 engine → live vertical #4. Implementation
> **gates on the engine** (now shipped). Dispatched by Code, relayed by Cray to
> Cowork, drafted in parallel with the engine build. **#158 (`03820e3`,
> `docs(plans)`) — OQ-4 ratified = HYBRID** (Cray, 2026-06-04): the intake
> mechanism = A3 free-text capture → A2 structured review/edit gate (runner-up
> pure-A2 embedded as the manual-entry fallback; voice out of scope).
> **Verified:** full suite **1162 passed / 2 skipped**; ruff + `mypy services`
> clean throughout. PLAN-0016 is **Done**; PLAN-0017 implementation is now
> UNBLOCKED. This PR = the session-37 reconcile (head `94c1078` → `1dbd202`).
>
> **Session 36 — Task (B) of the design-partner
> demo-generator track shipped: ADR-0015 + PLAN-0016 (two PRs, #150 + #151).**
> Both Cowork-drafted (ADR-009 D1), Code-committed via PR (ADR-009 D2).
> **ADR-0015 (Status: Proposed; content `4fac30c`, #150)** — "Assisted/
> Self-Serve Vertical Onboarding as a 2-Tier Pitch Artifact." Productizes
> onboarding: a **Tier-1 synthetic "Mirror demo"** (build first) + a **Tier-2
> real-data POC** (gated; design = task C). **D5** adopts **(ii) live
> co-creation** as the demo strategy — showcase the pre-built aquaculture
> vertical #3, then build the stakeholder's vertical #4 LIVE via a guided/
> conversational intake (manufactures decision urgency) — with an **engine /
> intake-face two-layer split**. **D3** ICP = right-sized mid-market beachhead
> (disrupt-from-below). **D4** first showcase audience + pick **locked to
> SE-Asian aquaculture** (fuel-retail wetstock recorded as the
> audience-dependent alternate, not rejected). **OQ-1** (aquaculture as a
> non-PII "biological-asset cousin" of the parked vet vertical) carried
> unresolved for Cray; **OQ-3** (recommender-direction as env-knob vs contract)
> + **OQ-4** (intake A2/A3/hybrid) opened. eFishery (public-record 2026 fraud
> collapse) cited as the whitespace rationale (sources in the gitignored
> private research file).
> **PLAN-0016 (Status: Draft; content `6b1b42f`, #151)** —
> "`vero-lite new-vertical` scaffolding — Tier-1 Mirror-demo generator." The
> **engine layer** of ADR-0015 D5 (the substrate the PLAN-0017 intake face will
> call). Stitches the BUILD steps around the existing AUTO generator; proven
> end-to-end on the aquaculture pick (the 3rd vertical, Rule-of-Three
> on-pattern). Carries a **⭐ REQUIRED Step 0 engine prerequisite**:
> `OCT_RECOMMEND_DIRECTION ∈ {above, below}` (default `above`, no regression)
> so a **below-threshold** breach (the aquaculture DO crash, 3.2 < 4 mg/L)
> fires the recommender — threaded through `recommender.py` (`94`, `199-204`,
> `215`, `233-235`) + `demo_events.py` (`43-64`, the third direction-hardcoded
> site a Cowork review caught beyond the dispatch's two). Step 0 is PR-able
> independently of the scaffolding work.
> **Then this session also ratified the ADR + shipped that Step 0.**
> **ADR-0015 ratified → Accepted (#153, content `5fed749`)** — Cray ratified in
> session 36; Status flipped **Proposed → Accepted** (ADR-009 D2 / CLAUDE.md
> §6). This unblocks the PLAN-0017 intake-face drafting dispatch.
> **PLAN-0016 Step 0 shipped (#154, content `94c1078`, `feat(engine)`)** — the
> **⭐ REQUIRED** engine prerequisite: the new
> **`OCT_RECOMMEND_DIRECTION ∈ {above, below}`** env knob (default `above`,
> normalized + fail-safe) + a single
> `crosses_threshold(measured, threshold, direction)` helper threaded through
> `recommender._is_recommendation_trigger`, `recommender._rule_recommend`
> (guard + the trace-summary operator `>=`/`<=` + the description verb "rose
> above"/"fell below"), and `demo_events._breach_event` (the
> `OCT_DEMO_TIME_ANCHOR` breach/anchor selector — the third
> direction-hardcoded site the Cowork review caught beyond the dispatch's two).
> So a **below-threshold** breach (the aquaculture DO crash, 3.2 < 4 mg/L) now
> fires the recommender — including the demo's clean-render rule path (MS-S1
> off). **Verified:** +9 tests; full suite **1136 passed / 2 skipped**; ruff +
> mypy clean. PLAN-0016 Steps 1–6 (the scaffolding command itself) remain; the
> rest of the design-partner-track work is handed off to a new session.
> **Earlier this session — Phase 0
> vertical-#3 pick research (Cowork)** selected aquaculture from a 5-candidate
> gated shortlist scored on a 2026 competitive-whitespace lens; the research
> file is gitignored (`docs/research/private/`). This PR = the session-36
> reconcile (head `6b1b42f` → `94c1078`).
>
> **Session 35 — PLAN-004 Phase B shipped: handoff
> tooling automation (#148, content `e8bc6c2`).** Landed the three
> forward-declared Phase B deliverables. **(1)** A `repo: local`
> `handoff-frontmatter` **pre-commit hook**
> (`tools/handoffs/precommit_handoffs.py`) that validates the **latest
> session-NN only** against the working tree (handoffs are gitignored → never
> staged) and **blocks** on an error-severity finding. The open design fork —
> latest-only-vs-legacy-drag and block-vs-warn — was resolved Cray-ratified
> this session: latest-only + blocking, no legacy drag. **(2)**
> `handoff_status.py --watch [--interval N]` live re-render. **(3)** An
> idempotent per-session `INDEX.md` auto-table (via `--index` + the hook).
> Shared helpers (`latest_session_dir`, `render_index`, `write_index`,
> `session_md_files`) added to `_schema.py`; `INDEX.md` excluded from all
> handoff walks. **Verified:** 16 new tests; full suite **1127 passed / 2
> skipped**; mypy + ruff clean; the hook was **dogfooded green** in this PR's
> own commits. PLAN-004 stays active as the **Phase C** tracker. Two strategic
> tasks were scoped + captured this session (feasibility findings in
> `.claude/handoffs/session-35/2026-06-04-0944-code-design-partner-demo-gen-feasibility.md`)
> and **deferred to a new session per Cray**: (B) draft an ADR + PLAN for a
> "design-partner demo generator" (assisted/self-serve vertical onboarding as
> a 2-tier pitch artifact — Tier-1 synthetic "mirror demo" first, Tier-2
> real-data POC later; verdict YES/feasible, the engine is ~80% there); (C)
> deep-research the Tier-2 real-data path (real `DataAdapter` impls,
> dbt/SQLMesh mapping layer, PDPA-safe ingestion). This PR = the session-35
> Phase B reconcile (head `6f84bd2` → `e8bc6c2`).
> **Earlier this session — runbook tail-beat note (#146, content
> `6f84bd2`).** A small docs-only follow-up to the session-34 fast-follow
> (#144, `cba80dc`): added a provenance addendum + a tail-beat note to
> `docs/runbooks/run-oct-demo.md` so the runbook reflects that the synthetic
> `occurred_at`s on both verticals were re-timed to make the breach the
> timeline's **tail beat** (→ 0 events anchored into the future under
> `OCT_DEMO_TIME_ANCHOR=true`). Only timestamps moved — measured values, ids,
> units, severities, counts unchanged — so every expected value the runbook
> already documents still holds. 16-line addition; no code/test/schema change.
>
> **Session 34 — PLAN-0015 fast-follow: the breach is now the
> tail beat of the OCT operational timeline (#144, content `cba80dc`).**
> Closes the "known minor artifact" recorded at PLAN-0015 closeout. With
> `OCT_DEMO_TIME_ANCHOR=true`, real-time anchoring shifts every synthetic
> `OperationalEvent` so the breach lands at server-start "now" — but both
> verticals had events occurring *after* the breach, so those markers
> anchored into the future and showed future HH:MM labels on the all-sites
> Operational Timeline. Fix re-times both synthetic datasets so the breach
> is the **latest** event: energy — inverter alarm `8:12 → 8:08` (now a
> precursor symptom before the thermal climax) + Riverside "steady" reading
> `8:20 → 8:06`; supply_chain — reefer door-open alarm `8:12 → 8:08`. Only
> `occurred_at` moved — measured values, asset/shipment ids, units,
> severities unchanged — so the singular-breach recommender contract holds.
> Docstrings updated to record the breach is deliberately the final beat.
> Synthetic data only; no production-code/schema change. **Verified:** full
> suite **1111 passed / 2 skipped** (unchanged), `mypy services verticals`
> clean, `ruff` clean on the diff (the lone E501 is in a gitignored generated
> file); an anchor-path probe over the **real** `demo_events` anchoring
> confirmed **0 events in the future** after anchoring for both verticals
> (breach == max `occurred_at` == now). **Process / meta note:** this
> reconcile is the **first live dispatch of the `status-scribe` subagent** —
> the session-33 reconcile (#143) was hand-authored, and PLAN-0015's
> first-live-use of status-scribe was the next-action validation item. So
> this STATUS entry both records the fast-follow AND validates the
> status-scribe dispatch contract end-to-end (Code supplies the fact-pack →
> status-scribe drafts the edit + a `docs(status):` subject → Code commits
> via a `docs/*` PR). This PR = the session-34 reconcile (head `ae1c38c` →
> `cba80dc`).
>
> **Session 33 — `status-scribe` STATUS-reconciliation subagent
> shipped (#142).** A meta question — how many agents/workflows has this
> project used — turned into infra work. Established that the project has
> two custom drafter subagents (`plan-drafter`, `explore-research`, both
> PLAN-0009) and that **Workflow has never been invoked** (0 `wf_` runIds
> across 129 transcripts). Analyzed the 4-day work pattern — dominant UI
> iteration on the OCT map/timeline, a **~1:1-per-PR `docs(status):`
> reconcile toil**, recurring coverage tests — against the remaining
> backlog. The gap: the two existing agents cover *design + research*
> (upstream); execution/maintenance toil is unagented. Shipped the
> highest-leverage fit — **`status-scribe`**, a third Tier-2 drafter
> modeled exactly on `plan-drafter` (PLAN-0009 Step 3): it reconciles
> `docs/STATUS.md` from a caller-supplied git fact-pack (`head_commit` /
> `recent_commits` / `now_iso` / `session` / `merged_pr` / `what_shipped`,
> optional `next_action`) and returns a proposed `docs(status):` subject.
> **Drafter-not-committer** — no Bash/git/commit path, cannot `git mv` to
> `done/`, cannot spawn nested subagents — so **only-Code-commits**
> (ADR-009 D2 / ADR-013 D2) holds. Three files: `.claude/agents/status-scribe.md`
> (house mold; dispatch contract + output schema + adversarial hardening +
> single-file serialization note), `.claude/hooks/pretooluse_status_scribe_write_deny.py`
> (write-scope hook — allowlist = exactly `docs/STATUS.md`, fail-closed,
> bypass-immune, mirrors the H2 normalization), and
> `tests/handoffs/test_pretooluse_status_scribe_write_deny.py` (35 tests:
> allow/deny incl. the plan-drafter surface *denied* + near-miss cases,
> fail-closed, pass-through, bypass-immunity both directions, reason
> citations). pytest 35 passed; ruff + mypy clean. **No new PLAN/ADR** —
> operationalizes ADR-013 D1 + PLAN-0009 (precedent: PLAN-0012; PLAN-0009
> OQ-3). The PLAN-0016 mint hit the **G2 guardrail** (consuming a PLAN
> number needs Cray ratification — first 529-transient, then the real
> structural verdict); per Cray's call it shipped **without** a separate
> PLAN, the dispatch contract living in the agent file. Process note: this
> very reconcile was **hand-authored** (status-scribe not yet exercised on
> a live reconcile — that is the next-action validation). This PR = the
> session-33 reconcile (head `bbe980c` → `ae1c38c`).
>
> **Session 32 — PLAN-0015 shipped: the live-time decision loop.**
> Cray green-lit execution ("Flip → Ready แล้วลุย"); flipped PLAN-0015
> Draft→Ready (#136) and executed all 4 steps (#137, merge `be470a4`). The OCT
> demo now plays as **live incident → human decision → resolution** end-to-end
> on Screen A's Operational Timeline. **(1) Real-time anchoring (D1/D5)** — a new
> `services/engine/demo_events.py` is the per-process live `OperationalEvent`
> view both synthetic adapters serve through; with `OCT_DEMO_TIME_ANCHOR=true`
> it shifts every event so the **breach ≈ server start** (the breach = the
> latest reading crossing `oct_recommend_threshold`, so it is generic — a
> `warn`-severity cold-chain breach anchors too, not just `critical`), spacing
> preserved; default **off** so the fixed synthetic datetimes (and the whole
> suite) are unchanged. The lifespan warms the view so the base = server start
> (raw read, no LLM call). **(2) Decision timestamps (D3)** —
> `RecommendedAction.approved_at`/`executed_at`, set in `approve()`/`execute()`,
> surfaced on `/recommendations`. **(3) Recovery as the effect of Execute (D2)**
> — the pre-baked 58 °C reading was removed from the energy base events;
> `/execute` injects a recovery reading (safe value, severity `info`, on the
> breach event's asset, `occurred_at` = real execute-time), idempotent. **(4)
> Frontend (D4)** — `view-map.js` `ensureData` re-fetches the decision-sensitive
> data per mount, so returning to Screen A reflects the decision; `renderTimeline`
> merges approve/execute decision beats onto the event time axis and resolves the
> breach marker green/✓ (pulse stops) with a decision-status chip; the map node's
> anomaly ring goes static-green + green glow; the detail banner resolves with the
> recorded Approved/Executed times. **Verified live** — energy via Claude Preview
> DOM (proposed/pulsing → approve → execute → resolved, with the recovery +
> approve/execute markers on the rail) and supply_chain via API probe (cold-chain
> breach anchored ≈ now, recovery injected on `shipment-pharma-01` at env-override
> value 4.2) — proving **zero per-vertical UI/engine code** (AC-template). New
> tests: `test_demo_events.py` + decision-time / recovery-on-execute endpoint
> tests. Suite **1065 → 1076**; ruff + mypy clean. PLAN-0015 archived to `done/`;
> runbook §9 + `.claude/launch.json` document the `OCT_DEMO_TIME_ANCHOR` flag.
> Known minor artifact: anchoring on the breach leaves later unrelated events
> (alarm +2 min, Riverside steady) slightly in the future on the *all-sites*
> view; within the incident scope the story is clean.
>
> **Then #140 (`fix(ui)`)** — knocked out the pre-existing `<980px` responsive map
> bug from the backlog: the side panel (detail card + legend) collapsed to 0px
> and vanished on a narrow viewport (the `<=980px` media query stacked into one
> grid column but `grid-template-rows: 1fr auto` gave the side row 0 height).
> Below 980px View A now flows as a normal scrolling block — a fixed-height map
> (`56vh`), the side cards stacked full-width beneath, then the timeline, with
> the view scrolling vertically + the counts chips wrapping. Verified live at
> 900 / 375 (mobile) / 1280px (desktop 2-column intact); CSS-only, desktop
> untouched.

> **Session 31 — run-oct-demo runbook (#117) + a PLAN-0014
> arm-state boot log (#119).** A short session driven by Cray rehearsing the
> demo. **(1) PR #117** added `docs/runbooks/run-oct-demo.md` — a
> verification-backed guide to bring up the OCT demo on **either vertical**
> (energy or supply_chain) via the `OCT_VERTICAL` config swap and drive all
> three OCT features; it documents the **two run modes** (offline rule
> fail-safe — features A/B/D; vs MS-S1-on grounded NL query — feature C),
> preconditions, per-vertical run commands with known-good baselines, WSL2
> localhost browser access, `GET /warm`, the per-screen design-partner
> narrative, and troubleshooting. Every command + value was run live on `main`
> `508aa90` with MS-S1 off (the NL-query grounded path cites PLAN-0013
> session-28 evidence). **(2) PR #119** (`feat(notify)`) — while rehearsing,
> the MS-S1-unreachable Telegram ping did not fire even though the token + chat
> were set, because `TELEGRAM_NOTIFY_ENABLED` was left `false` and a closed
> gate makes `notify_llm_unreachable()` a **silent** per-call no-op. Root cause
> found by probing the gate booleans (no token exposed); the fix adds
> `telegram.describe_arm_state()` + a one-shot **startup log** (via the
> `uvicorn.error` logger, since the repo applies no logging config so app INFO
> is otherwise dropped) printing `ARMED` / `DISARMED — <reason>` at boot,
> making a mis-arm self-evident. 4 new tests (3 unit incl. a no-token-leak
> assertion + 1 startup integration); verified live under uvicorn for both
> branches. Suite **1060 → 1064**; ruff + mypy clean. PLAN-0014 itself is now
> confirmed working end-to-end live (Cray armed it + received the no-PII ping).
> **(3) PR #121** (`test`) — that same suite run, now that the box is armed,
> made `test_cli_aborts_when_same_fs_check_fails` shell out to the real
> `telegram.sh` and deliver a stray dispatcher alert to Cray's Telegram (the
> dispatcher tests assumed an unset env — false once armed). Fixed with an
> autouse `_no_real_telegram` fixture that neutralizes both notify paths for
> every test (delenv the OS creds → telegram.sh no-ops; close the in-app
> gate) + a contract test proven to hold even with creds exported. Suite
> 1064 → 1065. **(4) PR #123** (`fix(ui)`) — Cray's rehearsal also surfaced
> a UI bug: the Operational Map inspector panel clipped its bottom (the grouped
> “ASSETS AT THIS SITE” list) at 100% zoom — `.map-side` had `overflow:auto`
> but the `.map-body` grid had no row track, so the column grew to content
> height and was clipped by `.view{overflow:hidden}` instead of scrolling.
> Fix (static assets only — served from disk, no restart): bound the grid row
> (`grid-template-rows: minmax(0,1fr)`) + `min-height:0` on `.map-side` so it
> scrolls; render the selected detail card above the legend (inspected record =
> primary reading order); + the missing `overflow-y:auto` on Views B/C.
> Verified live via Claude Preview. **(5) PR #125** (`fix(ui)`) — a
> same-session follow-up: #123's first cut still clipped the detail card and
> the panel still would not scroll, because `.detail-card`'s `overflow:hidden`
> makes its flex `min-height:auto` resolve to 0, so the column squeezed the
> card (clipping the 2nd asset) instead of overflowing. Completed with
> `.map-side > .card { flex-shrink: 0 }` — cards keep full height, the column
> overflows + scrolls; re-verified live (detail un-clipped, both assets shown,
> scroll reaches the legend bottom). **(6) PR #127** (`fix(ui)`) — review of #125
> noticed the legend jumped position between idle (top) and selected (bottom),
> a side-effect of #123's reorder; made consistent (Cray's choice) — the
> contextual panel (detail/hint) is always the top slot, legend anchored below
> in both states (live Preview: idle [map-hint, legend], selected
> [detail-card, legend]). **(7) PR #129 + #130** (`feat`) — gave the
> demo map a story (Cray's ask). #129 expanded the energy synthetic events 4 →
> 9 into a morning thermal-incident arc on Battery Bank A (transition →
> baselines → rising temp info→warn→critical breach → inverter alarm →
> recovery; all 3 event_types + 4 severities; only the 96.5 °C breach is ≥ the
> recommender threshold so the action + NL “≥90” stay singular) and formatted
> timestamp properties in the detail panel (`OCT.fmtTimestamp`). #130 added the
> headline **Incident timeline** rail below the map: one marker per
> OperationalEvent, severity-coloured, the critical breach pulsing, even
> chronological spacing with per-marker HH:MM labels (Cray-chosen over a
> proportional axis that collapsed the incident into 68 % dead space + an
> overlapping climax), click→select the event; ontology-driven (timestamp +
> severity from /meta). An L1 loop-detect fired on the 6th view-map.js edit
> mid-build → paused + reassessed the layout with Cray per the guardrail,
> committed to reset, then continued. Verified live via Claude Preview DOM
> (screenshot blocked — MS-S1 on, /recommendations hangs warming the LLM).
> This PR = the session-31 reconcile (head `cecc028` → `d9f7928`). **(8) PR
> #132** (`feat(ui)`) then scoped the rail to the selected site/asset (rename
> “Incident timeline” → “Operational timeline · <scope>”; +a Riverside
> operational stream so a healthy site isn't empty; events 9 → 12, all new
> readings sub-threshold so the breach + NL “≥90” stay singular) and added a
> pulsing glow on the selected map node (nodeGlow / red nodeGlowCrit when
> flagged) so the active focus is obvious — verified live via Claude Preview
> DOM (Riverside → 4 scoped markers, North → 8, Battery Bank B → 3). That PR =
> the session-31 reconcile (head `d9f7928` → `d150d75`). **(9) PR #134** then
> minted **PLAN-0015** (Draft) — “decision loop on the operational timeline”:
> tie Screen B Approve/Execute to Screen A's timeline with real-time anchoring
> (breach ≈ server-run now, gated for test determinism), recovery as the effect
> of Execute, server-side decision timestamps, and a resolved breach/map state.
> Code-drafted from a Cray-interactive design (forks D1–D5 Cray-ratified);
> awaiting Cray “Ready for execution”. This PR = the session-31 reconcile (head
> `d150d75` → `f8d2e64`). The session 30 / 29 / 27+28 / … narratives below are
> retained for archeology.
>
> **Session 30 — coverage-hardening arc (#107/#109/#110) → backlog
> work: #5 arming runbook (#112) + the loop's first real job, status_digest
> (#113).** After the coverage arc, a grounded backlog discussion routed the work:
> (1) **PR #112** shipped `docs/runbooks/arm-plan-0014-telegram.md` — the
> verification-backed runbook for Cray to *arm* the MS-S1-unreachable Telegram
> ping on the demo box (env vars + tmux restart + the WSL tap-link networking
> fix + a verification ladder). (2) **PR #113** shipped the **`status_digest`
> loop handler** — the live autonomy loop's first beyond-heartbeat job,
> automating the STATUS-reconcile toil. v1 = **detect-and-nudge** (Cray-ratified):
> the consumer computes STATUS freshness (reusing `compute_status_freshness` —
> the same logic as the `lint_status` bridge tool, single source of truth) and,
> only on drift, sends a no-PII Telegram nudge; it never edits/commits STATUS
> (auto-draft is a deferred v2). Producer/consumer split: a Cowork routine is the
> "when" (its message body is never read = no injection); Code is the "what".
> Best-effort/never-raises (cannot poison the loop); argv Telegram contract
> (Lesson #0014). 18 tests = full case-coverage matrix, module 100%. The work
> also **surfaced a latent bug** — the dispatcher's `make_telegram_alert` pipes
> its payload to stdin but `telegram.sh` reads argv[1], so poison/cycle_failures
> alerts never reach Telegram (flagged via a spawn-task chip; the new handler
> uses the correct argv contract). status_digest runs end-to-end once Cray
> registers a Cowork producer routine + live-verifies (non-gating Cray-actions).
> Suite **1040 → 1058 passed / 2 skipped**; ruff + mypy clean. **PR #115**
> (`fix(loop)`) then closed that flagged bug: a **spawned session** (from the
> PR-#113 chip) fixed `make_telegram_alert` to pass the alert as `argv[1]` (not
> stdin) via a human-readable `_format_alert_message` + regression tests; Code
> reviewed the diff vs the chip spec (read-only) → full coverage, nothing to
> graft. Process note: that session ran in the **shared** main checkout (not an
> isolated worktree) — a concurrency hazard (shared HEAD/index; surfaced an
> `index.lock` race), so future spawned work should use a separate worktree.
>
> **Session 30 (coverage arc) — 3 additive-test PRs
> (#107, #109, #110), zero production-code change.** Started from the parked
> session-29 coverage item, then did a *grounded* backlog review (real plan-scope
> via an Explore sweep + per-line triage of each candidate) before picking the
> lowest-risk targets and shipping them in order. **PR #107** — ontology-validator
> negative tests (rejection paths; the gatekeeper for new verticals per ADR-008),
> in-process `main()` + `capsys` (Lesson #7 §3.2), **89% → 96%**, +8. **PR #109**
> — `tools/loop/_schema.py` parser edges (quote-strip, no-closing-fence, list
> break, comment/blank/non-key lines, missing `message_type`, non-int
> `schema_version`, scalar `references`, malformed-filename short-circuit) driven
> entirely through the **public `parse_message_text`/`parse_filename` seam** so
> they survive internal refactors, **94% → 100%**, +8. **PR #110** —
> `services/engine/nl_query.py` (OCT NL-query demo surface): pure helpers
> unit-tested directly (matching repo precedent) + the two *degrade* paths
> (count-fallback, retrieval-failure) driven through the real `answer_question`
> orchestrator so they document behaviour, not just hit a line; offline
> `_StubQueryClient` (no live Ollama), **89% → 100%**, +14. Three sustainability
> guardrails were applied throughout: public-seam-over-private-helper,
> real-orchestrator-over-line-jab, and a Step-5 narrative pointer (the parser
> already accepts the 3 reserved `MessageType` values — the dispatcher no-op
> contract was deliberately **not** front-run while Step 5's scope is open).
> Suite **1010 → 1040 passed / 2 skipped**; ruff + `mypy services` clean. The
> session 29 / 27+28 / 26 / 25 / 23+24 / 22 / 20+21 narratives below are retained
> for archeology.
>
> **Session 29 — STATUS reconcile (PR #102) + PLAN-0010 autonomy loop
> CLOSED.** Reconciled the 2-session STATUS drift (sessions 27+28 → PR #102),
> then ran a live PLAN-0010 loop session. Disambiguated the three Desktop
> routines — the Cowork **producer** (`phase35-smoke-cowork-heartbeat` → writes
> `loop/inbox/`), the deprecated gen-1 observe-only **reader**
> (`phase35-smoke-code-reader`, old `docs/research/private/phase3.5-smoke/inbox/`
> path, left paused), and the gen-2 commit-capable **consumer**
> (`loop-dispatcher`). One-shot-drained 30 stranded inbox messages (30→0; one
> valid-body / bad-filename `parse_failed`), then shipped **PR #103**
> (`feat(loop)` — a `cycle_failures` Telegram summary ping so
> `parse_failed`/`dispatch_failed` are no longer silently quarantined; +4 tests,
> suite 1007; live-verified). Cray then **registered `loop-dispatcher`** in
> Desktop Routines (Local · Hourly · Sonnet 4.6 · Worktree OFF · branch `main`)
> and the first live run verified clean (inbox 1→0, `tier=code branch=main`, no
> error). The autonomy loop now runs producer↔consumer with no human in the
> dispatch path. **Loop tested + hardened:** PR #105 (`test(loop)`) added a
> producer↔consumer round-trip + NONCE-collision regression test; a **live smoke**
> of both routines processed a unique control message clean (`ok=1`) and
> **reproduced the NONCE collision in production** — the Haiku producer could not
> read the clock, guessed `07:00 UTC`, hit an archived name, and its fresh
> heartbeat was silently deduped. **Lesson #0020** codifies this (agent-claimed
> timestamps are an unreliable uniqueness key) and Cray applied the producer
> `-<rand>` fix in the Desktop UI. The sessions 27+28 / 26 / 25 / 23+24 / 22 /
> 20+21 narratives below are retained for archeology.
>
> **Sessions 27 + 28 — OCT stakeholder demo SHIPPED on 2 verticals
> (PLAN-0013, 7/7 ACs) + PLAN-0014 LLM-unreachable recovery loop. Moat phase
> ~complete.** Two long execution sessions closed the demo arc end-to-end, both
> merged + archived to `done/`. **Session 27** (the long one) minted PLAN-0013
> (#90), built Steps 1–6 live on the **energy** vertical (ontology-driven UI —
> operational map / anomaly + reasoning-trace + approve→execute→DB-persist /
> grounded NL query / data→decision flow view), fixed an alembic FK-index drift
> (#97), and switched the test suite to a disposable `vero_lite_test` DB so it no
> longer wipes the demo DB (#98) — leaving PLAN-0013 at 6.5/7 ACs. It also landed
> 2 prerequisite docs PRs: PLAN-004 status reconcile (#88) and the
> `STRATEGIC_CONTEXT_AIP` north-star reference (#89). **Session 28** closed the
> final AC — **AC-template** — via a **`supply_chain` (cold-chain) 2nd vertical**
> (#99): a full A/B/C/D re-skin proving the *same UI build* renders a different
> ontology with **zero UI-code change**, driven by a new `OCT_VERTICAL` config +
> generalized recommender/trace/static coupling (data-driven 2nd instance, no new
> abstraction — Rule-of-Three preserved). PLAN-0013 → 7/7, `done/`. Session 28
> then shipped **PLAN-0014** (drafted #100 by the `plan-drafter` subagent,
> executed #101): an `OllamaUnreachableError` path + best-effort Telegram notify
> (cooldown) when MS-S1 is powered off, plus browser/phone-tappable `GET /warm`
> (blocking + `?wait=false`) and `GET /sleep` endpoints; live-smoked against
> MS-S1. Suite **1003 passed / 2 skipped**; ruff + `mypy services` clean; **0 open
> PRs; main @ `27ea292`**. **This PR = the overdue STATUS reconcile** (sessions 27
> + 28 skipped their end-of-arc reconcile — the drift the `lint_status` bridge
> tool flags). **Carry-over resolved:** PLAN-0011 is now `Complete` (in `done/`),
> so the session-26 "AC-3/AC-7 fresh-trigger re-run" item is closed.
> **Cray-action backlog:** re-paste both tier files into the Desktop UI; PLAN-0010
> loop-dispatcher Desktop one-time setup (verify PR #55); arm PLAN-0014 on the
> demo box. The session 26 / 25 / 23+24 / 22 / 20+21 narratives below are retained
> for archeology.
>
> **Session 26 — OQ-T5 RESOLVED (Chat-as-bridge-client).** The
> governance question Code surfaced at Step 5 (FINDING-4) is closed: **Chat is
> not a sanctioned `vero-bridge` client** (operationally no demand — the Step-4
> Chat round-trip was a replay, never live — + Chat's repo-blind role per
> ADR-012 D2; the repo-grounded bridge surface belongs to Code + Cowork). The
> reconcile is light-touch ("B by decision, C by effort"): both tier files
> reconciled (`chat_tab_instructions.md` = not-a-client + a new spoof-refusal
> rule; `cowork_tab_instructions.md` = sanctioned-client posture), PLAN-0012
> surgically re-characterized (Goal pointer + AC-3 replay note + AC-4(c) OQ-T5
> RESOLVED; the full AC-6/AC-7 sweep skipped as low-payoff), and **Lesson #0019**
> minted (adversarial spoof-tests belong at the unit layer). No new ADR
> (PLAN-0009 OQ-3). **Cray action:** re-paste both tier files into the Desktop
> project-instructions UI (canonical = repo, UI = sync target). The session 25 /
> 23+24 / 22 / 20+21 narratives below are retained for archeology.
>
> **Session 25.** Step 2b (the four integration tools) is COMPLETE —
> PLAN-0012 Phase 1's full safe-for-all tool surface (7/7) is now live, plus an
> L1 loop-detect hardening fix and two lessons. The session 23+24 / 22 / 20+21
> narratives below are retained for archeology; this section + the AC scoreboard
> (still 8/8 from session 24) are current.

### Session 25 — PLAN-0012 Step 2b COMPLETE (4 integration tools) + loop-detect fix + lessons

Autonomous Code-side session; **6 PRs (#80–#85)**, suite **820 → 920 passed /
7 skipped**, ruff + mypy clean throughout. Step 2b adds the four *integration*
tools beyond the three introspection tools — **one substantial PR per tool**
(session-22 review-tractability decision) — completing the Phase 1
safe-for-all surface at **7/7**.

- **PR #80** (`abf453e`) — **`read_repo_path` (§2.4).** Path-sandboxed,
  read-only repo-file reader. The whole design surface is the sandbox
  (`tools/vero_bridge/_repo_read.py`): relative + no `..` + in-tree after
  symlink resolution + not `.git/` + **git-tracked allowlist** (auto-excludes
  every gitignored sensitive path) + regular file ≤2 MiB + UTF-8 → new
  `ErrorCode.PATH_FORBIDDEN`. A review pass added two fail-closed guards
  (NUL-byte path, OSError on read) so no raw exception crosses the MCP
  boundary (`4e0c254`).
- **PR #81** (`af94735`) — **`validate_handoff_frontmatter` (§2.5).** Runs the
  committed handoff schema **in-process** via a new content-based entry point
  `tools/handoffs/_schema.py::parse_frontmatter_text` (path-based
  `parse_frontmatter` refactored to delegate — behaviour-preserving). Closes
  the Lesson #8 K-1 forcing fact (Cowork can now validate handoffs it authors).
  `ok` = transport success, `valid` = content validity; no new `ErrorCode`.
- **PR #82** (`e98aa83`) — **`lint_status` (§2.6).** `docs/STATUS.md` freshness
  vs **local `main`** (real-operation divergence from the `origin/main` spec —
  WSL-local server, no guaranteed network) with **`--no-merges`** (required
  under the merge-commit PR workflow, else a reconcile PR's merge commit reads
  as false drift). Fail-closed. (This very tool reported the drift that
  prompted this reconcile — see Lesson #18.)
- **PR #83** (`1b52e3a`) — **`dispatch_receive` (§2.7).** Receive-only inbox:
  appends the dispatch envelope to a gitignored queue (same write-class as the
  audit log, best-effort) and returns a content-addressed `received_id`.
  **No commit, no bind-on-Cray** — authority stays not-on-bridge.

**Loop-detect hardening — PR #84** (`c7d5896`): the L1 counter accumulated 6
legitimate cross-PR edits to `server.py` and hard-blocked the 5th handler (a
false positive). Fix: `posttooluse_progress_observer.py` now resets a file's
L1 counter on a successful `git commit` (only the committed files; in the
reliable PostToolUse Bash path). See Lesson #12 §7.

**Lessons — PR #85** (`1ec53b0`): amended **Lesson #12** (cross-PR/cross-session
L1 accumulation + the #84 fix + two meta-lessons: verify a handoff's claimed
mitigation against real state/hook; a chat ack does not unblock a deterministic
hook) + new **Lesson #18** (`git log --grep` needs `--no-merges` under a
merge-commit workflow; + the spec→as-built `origin/main`→local-`main` norm).

**Step 2b tool-surface scoreboard (7/7 — Phase 1 complete):**

| Tool | § | Class | PR |
|---|---|---|---|
| `echo` / `bridge_status` / `bridge_whoami` | 2.1–2.3 | introspection | (Step 2, #71) |
| `read_repo_path` | 2.4 | read (sandboxed) | ✅ #80 |
| `validate_handoff_frontmatter` | 2.5 | validate (in-process) | ✅ #81 |
| `lint_status` | 2.6 | read (git query) | ✅ #82 |
| `dispatch_receive` | 2.7 | receive-only (no authority) | ✅ #83 |

**Remaining (non-blocking, out-of-tool):** OQ-T5 governance adjudication
(Cowork/Cray) + carry-overs (PLAN-0011 fresh-trigger re-run, PLAN-0010
loop-dispatcher Desktop setup). **This PR = session-25 STATUS reconcile** (no
code/test/settings touched).

---

#### Prior context — Session 23 + 24 (retained for archeology)

### Session 23 + 24 — Phase 1 client surface + ts_ns fix + cross-client evidence

Sessions 23 (2026-05-29 AM) + 24 (this session, post-Desktop-restart) shipped
**4 PRs (#73–#76)** that took PLAN-0012 Phase 1 from "server + contract live,
AC-3 unblocked" to "client surface complete + ts_ns precision fixed +
cross-client live evidence captured (AC-3/6/7 DONE)":

- **PR #73** (`69b33ff` → merge `7cd56d1`) — **Step 3a Chat-tab client.**
  Chat invokes `mcp__vero-bridge__echo` from its deferred list against the
  Step 1 wire format (raw + doc-rot guard). +356/−1.
- **PR #74** (`ec22162` → merge `69d3be0`) — **Step 3b Cowork-tab client +
  AC-7 cross-client parity.** Identical wire format + tool surface as Step 3a.
  +243/−0.
- **PR #75** (`b90442d` → merge `476e9c7`) — **ts_ns precision fix
  (FINDING-1/2).** FINDING-2: `ts_ns` (int64 ≈ 1.78×10¹⁸ > 2⁵³) was corrupted
  by structuredContent-consuming clients (Code, Cowork) through an IEEE-754
  double → string-typed (`server.py:149` returns `str(record["ts_ns"])`; audit
  log keeps the int as source of truth). FINDING-1: `ts_ns` is wall-clock epoch
  ns, **not** monotonic; ordering key is the per-process `monotonic_counter`
  (resets per respawn) — docstring corrected. +100/−32.
- **PR #76** (`0e60300` → merge `35759cd`) — **Step 4 cross-client live
  evidence. AC-3 / AC-6 / AC-7 DONE**; AC-4(c) basis live-proven (full matrix =
  Step 5). New tracked runbook
  [`docs/runbooks/vero-bridge-cross-client-evidence.md`](runbooks/vero-bridge-cross-client-evidence.md)
  + plan AC marks; verbatim per-cell evidence in the gitignored
  `docs/research/private/2026-05-29-vero-bridge-step4-cross-client-evidence.md`.
  +151/−7.

**Cray-side Action 0 (session 23):** added the production
`mcpServers.vero-bridge` entry to `claude_desktop_config.json` + Desktop
restart — this is what made the live cross-client evidence capturable (the
server now spawns alongside the gitignored probe).

**Post-fix re-smoke (session 24, the AC-3/6/7 proof):** every client's `ts_ns`
round-trips **byte-exact** as a decimal string against the audit int — Chat
`…624177`, Code `…448359`, Cowork `…125591` (Code + Cowork rounded pre-fix;
Chat was already exact via the text-content path). Code + Cowork share server
`pid 1189` with `monotonic_counter` 1→2 — same-instance routing reconfirmed in
a 2nd Desktop epoch (the AC-4(c) basis; full spoof matrix is Step 5).

**Tooling (session 24):** created the user-level `/eli-cray` slash command
(`~/.claude/commands/eli-cray.md` — pull an ELI-CTO explanation of the last
work batch, Thai) + new auto-memory
`feedback_verify_relayed_responses_vs_audit_log` (cross-check Cray-relayed
Chat/Cowork tab responses against the audit log to catch stale replays vs
fresh calls — surfaced when a relayed Chat response turned out to be a replay
of an earlier capture).

**Cumulative test delta (sessions 23+24):** 755 → **794** (+39 from
#73/#74/#75; #76 is docs-only). ruff + mypy clean; no regressions.

**Remaining PLAN-0012 Phase 1:** **Step 5** (full adversarial cross-tab spoof
matrix + AC-8 negative test + case-coverage → closes AC-4(c)/5/8;
Cray-interactive relay) + **Step 2b** (4 integration tools, one PR each;
autonomous). **This PR = session 23+24 STATUS reconcile** (no
code/test/settings touched).

**Phase 1 AC scoreboard (after session 24 — Phase 1 COMPLETE, 8/8):**

| AC | Status |
|---|---|
| AC-1 Transport contract documented | ✅ DONE (Step 1) |
| AC-2 Server lifecycle | ✅ DONE (Step 2) |
| AC-3 Cross-client live evidence | ✅ DONE (Step 4 / PR #76) |
| AC-4 (a) G5 stays green | ✅ PRESERVED |
| AC-4 (b) Audit log | ✅ DONE (Step 2) |
| AC-4 (c) Anti-spoof matrix | ✅ DONE (Step 5 / PR #78) — spoof accepted (Option I); Code/Cowork non-discriminable; Chat discriminable + refused (FINDING-4) |
| AC-5 Test coverage | ✅ DONE (Step 5 / PR #78) — 26 adversarial/negative tests; suite 813 passed / 7 skipped |
| AC-6 Live evidence captured | ✅ DONE (Step 4 / PR #76) |
| AC-7 Cross-client parity | ✅ DONE (Step 4 / PR #76) |
| AC-8 Capability-by-tool-design | ✅ DONE (Step 5 / PR #78) — registered set asserted; not-on-bridge → framework `ToolError` (FINDING-3) |

---

#### Prior context — Session 22 (retained for archeology)

**Session 22 — PLAN-0012 ratified Ready-for-execution + 3 OQs resolved
(OQ-T1 / OQ-T4 / OQ-V2) + Phase 1 Step 1 (wire format contract +
schema + capability inventory) + Phase 1 Step 2 (stdio-MCP server +
audit log + 3 introspection tools).** Session 22 (this session,
2026-05-28 PM late) shipped **4 PRs end-to-end** (#68–#71) in a single
Code-side push that took PLAN-0012 from "Draft awaiting ratification +
2 open OQs" to "Ready for execution + 5 of 8 ACs DONE or DONE-in-docs
+ Step 3+ unblocked":

- **PR #68** (`43370cc`, commit `202cfa1`) — **STATUS reconcile session
  20+21** ledger entries + Current Focus narrative + frontmatter update.
  No code/test/settings touched. Proposed Cray ratification of
  PLAN-0012 Status `Draft` → `Ready for execution` for Phase 1
  green-light.

- **PR #69** (`e2fda26`, commit `7a22066`) — **PLAN-0012 ratified +
  3 OQs resolved.** Cray adjudicated 4 governance decisions in a
  single session-22 routing turn after reviewing PR #68's proposal:
  (1) **PLAN-0012 Status flip `Draft` → `Ready for execution`**;
  (2) **OQ-T1 RESOLVED `fail-closed`** — on connection-drop/timeout/
  malformed-frame/version-mismatch, server drops + logs + does NOT
  retry; no silent degradation; aligns with ADR-013 D2 deterministic
  posture; (3) **OQ-T4 RESOLVED `serial-per-instance`** — server
  queues incoming calls + processes one-at-a-time per instance; Code
  and Cowork (sharing instance B under tab-group routing per Lesson
  #0017 §3.1) get serialized handling; deterministic audit-log
  ordering; (4) **OQ-V2 DEFERRED with `version: int` stub directive**
  — every wire frame carries mandatory `version: int`; Phase 1
  accepts only `version: 1`; full negotiation policy (per-session vs
  per-call vs per-tab) decided when client codepath divergence
  becomes load-bearing.

- **PR #70** (`35f59ad`, commit `61d93fe`) — **Phase 1 Step 1**
  (wire format contract + schema + capability inventory). 4 new
  files; +1,197 LOC; +66 tests (634 → 700, regression-free). New
  modules `tools/vero_bridge/{__init__,_schema}.py` (stdlib-only
  envelope schema mirroring `tools/handoffs/_schema.py` discipline:
  `Envelope` frozen dataclass + `MessageType` enum + `ErrorCode` enum
  + `BridgeError` hierarchy + `parse_envelope()` + `format_error_response()`).
  New convention docs `docs/conventions/vero-bridge-wire-format.md`
  (the human-readable counterpart to the schema) +
  `docs/conventions/vero-bridge-capability-inventory.md` (canonical
  "what is exposed where" — 7 safe-for-all tools + 8 not-on-bridge
  ops materialized from PR #67 Cowork completion handoff §3).
  Coverage: **AC-1 DONE** (transport contract documented +
  machine-checkable) + **AC-8 DONE for docs portion** (capability
  inventory canonicalized; negative test in Step 5).

- **PR #71** (`438e3c5`, commit `99a908f`) — **Phase 1 Step 2**
  (stdio-MCP server + audit log + 3 introspection tools, focused
  scope). 4 new files; +1,147 LOC; +55 tests (700 → 755,
  regression-free). New modules `tools/vero_bridge/server.py`
  (FastMCP `"vero-bridge"` server with `echo` + `bridge_status` +
  `bridge_whoami` tools, each `parse_envelope()` + audit-log + return)
  + `tools/vero_bridge/_audit_log.py` (JSONL append-only writer with
  per-process monotonic counter, malformed-input-safe rendering for
  AC-4 (c) anti-spoof matrix prereq, swallow-OSError-into-record for
  audit-log lossless guarantee). Coverage: **AC-2 DONE** (server
  lifecycle bound to Desktop session under A1 stdio-MCP) + **AC-3
  UNBLOCKED** (`echo` tool ready for Steps 3a + 3b + 4 cross-client
  round-trip matrix) + **AC-4 (a) PRESERVED** (no git path on the 3
  shipped tools; ADR-013 D2 stays binding) + **AC-4 (b) DONE** (full
  audit-log per record; observable signals captured) + **AC-4 (c)
  PREREQ MET** (`bridge_whoami` response signals match audit record
  byte-for-byte — clients can self-audit how the server saw them).

**Phase 1 AC scoreboard (session 22 snapshot — superseded by the "after session 24" scoreboard above):**

| AC | Status |
|---|---|
| AC-1 Transport contract documented | ✅ DONE (Step 1) |
| AC-2 Server lifecycle | ✅ DONE (Step 2) |
| AC-3 Cross-client live evidence | 🟢 UNBLOCKED — Steps 3a + 3b + 4 |
| AC-4 (a) G5 stays green | ✅ PRESERVED |
| AC-4 (b) Audit log | ✅ DONE (Step 2) |
| AC-4 (c) Anti-spoof matrix | 🟢 PREREQ MET; full matrix in Step 5 |
| AC-5 Test coverage | 🟡 121 unit tests; full cross-client + adversarial in Step 5 |
| AC-6 Live evidence captured | ⏳ Step 4 |
| AC-7 Cross-client parity | ⏳ Step 4 + Step 5 |
| AC-8 Capability-by-tool-design | ✅ DONE for docs (Step 1); negative test in Step 5 |

**Deferred to Step 2b** (per session-22 split decision — each integration
tool has its own design surface, one substantial PR per tool keeps review
tractable): `read_repo_path` (path sandbox / allowlist) +
`validate_handoff_frontmatter` (schema import from `tools.handoffs`) +
`lint_status` (git subprocess + STATUS frontmatter parse) +
`dispatch_receive` (receive-queue lifecycle).

**Forward-looking probe `tools/probes/vero_bridge_probe.py`**
(gitignored) still LIVE alongside the new production
`tools.vero_bridge.server` — both can coexist via separate `mcpServers`
entries. Desktop config `mcpServers.vero-bridge-probe` was load-bearing
for OQ-B + OQ-T3 empirical resolution; once `mcpServers.vero-bridge`
production entry lands (Cray-side one-time setup, next session), the
probe stays alive as a forward-looking infrastructure for Phase 2+
design iteration. Restore-from-backup of pre-probe config is post-
Phase-1 cleanup, not now.

**This PR is session-22 closeout** (STATUS-reconcile chore before
session-22 → session-23 handoff). Brings STATUS current from session 21
→ session 22. No code/test/settings touched.

### Context: how session 22 built on sessions 20 + 21

Session 20 minted PLAN-0012 (PR #63 — Cowork-drafted; OQ-A pre-decided
A1 stdio-MCP). Session 21 ran the empirical-probe arc (PRs #64–#67)
that landed OQ-B + OQ-T3 + OQ-V1 + Lessons #0016/#0017 (with the
meta-recursion §3+§5 self-correction precedent). Session 22 picked up
at "PLAN minted + 4 OQs resolved + 2 OQs open" and closed the loop:
ratified the PLAN + adjudicated the 2 remaining OQs + implemented
Phase 1 Steps 1 + 2 against the now-pinned contract. Three sessions
back-to-back compressed what could have been a 5–7 session arc into
1 day — the empirical-probe discipline (Lesson #0017 §5 "link
system-level state to protocol-level evidence") + the schema-mirror
pattern (Lesson #5 §4 — `tools/handoffs/_schema.py` as template) +
the OQ-resolution-batching discipline (one Cray turn → 4 decisions)
made it possible. See the session-20+21 ledger below for the
empirical-probe arc detail.

- **PR #64** (`5be0ec9`, commit `cd670b3`) — **OQ-B RESOLVED YES**
  (Claude Desktop CAN spawn additional MCP servers via
  `mcpServers` config under the UWP sandbox) **+ Lesson #0016 minted**
  (`docs/lessons/0016-claude-desktop-uwp-sandbox-config-path.md` —
  UWP Microsoft Store install config path gotcha:
  `C:\Users\<u>\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`,
  NOT the win32-tradition `%APPDATA%\Claude\claude_desktop_config.json`;
  prerequisite for any Phase 1 deployment instruction). Audit-trail
  research note `docs/research/private/2026-05-28-oq-b-chat-mcp-spawn-probe.md`
  §1–§7 (gitignored) carries the OQ-B probe matrix T1–T7.

- **PR #65** (`c785d90`) — **Lesson #0017 minted** initial draft
  (`docs/lessons/0017-mcp-cross-tab-visibility-empirical-probe.md`):
  cross-tab MCP visibility model + 5-step empirical-probe checklist
  ("probe before infer"). This was the first draft, inference-based
  on protocol shape.

- **PR #66** (`98214fc`, commit `0bbb149`) — **Lesson #0017 §3 + §5
  empirical correction** (the meta-recursion: lesson eats itself).
  Initial §3 inference ("each tab gets its own MCP server instance")
  was empirically falsified via `ps aux` probe after Cray surfaced an
  OQ that could only be answered by checking system-level state.
  Corrected model: **tab-group routing** — Chat alone on instance A
  (PID 613); Code + Cowork share instance B (PID 2092). Server cannot
  discriminate Code from Cowork — by design accepted under Option I
  (see OQ-T3 below). §5 added 5th step: "link system-level state to
  protocol-level evidence" — a rule extracted from the meta-recursion
  itself. New auto-memory `feedback_empirical_probe_before_trivial_oq.md`
  codifies the "probe before infer" rule for future tab sessions.

- **PR #67** (`4ee8987`, commit `b3a6070`) — **PLAN-0012 v1 scope
  expand Cowork-drafted** (Code↔(Chat+Cowork) under A1 stdio-MCP, not
  Code↔Chat-only). Resolves **OQ-T3 Option I** (capability-by-tool-design:
  `claimed_tag` = audit-only, not authorization; bridge surface =
  tab-tier-safe operations only; dangerous ops not-on-bridge — accepts
  that the server cannot cryptographically discriminate Code from Cowork
  under the empirically-corrected tab-group routing model). Resolves
  **OQ-V1** (uniform safe-tool scope for Phase 1). Surfaces 2 new OQs:
  **OQ-T4** (cross-client concurrency / ordering — must adjudicate
  before Step 4/5 AC-5 tests) and **OQ-V2** (wire-format version
  negotiation — safe to defer past Phase 1). Cowork's completion handoff
  §3 also drafted the AC-8 capability inventory (7 safe-for-all tools
  + 8 not-on-bridge ops) — to be materialized as a tracked file
  (`docs/conventions/vero-bridge-capability-inventory.md` likely)
  under Phase 1 Step 1 execution, NOT pre-materialized (per PR #67
  dispatch constraint).

**Forward-looking probe still alive.** The probe
`tools/probes/vero_bridge_probe.py` (gitignored, ~MCP-stdio Python
server) ships 2 tools — `bridge_ping` (echo) + `bridge_whoami`
(reports `claimed_tag` + PID + server-internal identity for the
empirical probe). Desktop config `mcpServers.vero-bridge-probe` is
LIVE; 2 server instances spawned across the Desktop session per
tab-group routing. Probe is forward-looking infrastructure for Phase 1
design iteration (Cray opted-in to keep it alive; restore-from-backup
is post-Phase-1 cleanup, not now).

**PLAN-0012 still Status `Draft`.** This PR (STATUS reconcile)
proposes Cray flip PLAN-0012 Status `Draft` → `Ready for execution`
for Phase 1 implementation green-light. Cray ratifies the flip in
review or in a dedicated follow-on PR. Phase 1 Step 1 (wire format +
capability inventory) is additionally gated on Cray adjudicating
OQ-T1 (transport failure contract — Code recommends fail-closed) and
OQ-T4 (cross-client concurrency — Code recommends serial-per-instance).
OQ-V2 is safe to defer past Phase 1.

**This PR is session-21 closeout** (STATUS-reconcile chore per
session-21 → session-22 kickoff handoff §4 Action 1; high-priority
"close the loop" item). No code/test/settings touched. Cumulative
session 20+21 tests: 634 (unchanged — all 5 PRs in sessions 20+21
were docs/plans/lessons only).

### 2026-06-02 — Session 30 ledger (coverage arc → runbook → status_digest)

Started from the parked session-29 coverage item, then ran a grounded backlog
review (Explore sweep over the 3 active plans + per-line triage) and worked the
backlog in priority order: the 3-PR coverage arc (#107/#109/#110), then the
PLAN-0014 arming runbook (#112), the loop's first real job — the `status_digest`
handler (#113) — and a spawned-session fix for the dispatcher Telegram argv bug
that #113 surfaced (#115, Code-reviewed before merge). Suite **1010 → 1060
passed / 2 skipped**; ruff + `mypy services`/`mypy tools/loop` clean throughout.

| Phase | PR / artifact | Change |
|-------|--------------|--------|
| **Validator negative-test batch** | [#107](https://github.com/CrayJThiemsert/vero-lite/pull/107) (`352ba68` → merge `442d180`) | **`test(engine)`** — 8 additive negative tests in `tests/services/engine/test_ontology_validator.py` covering the validator's rejection paths: malformed `foreign_key` (L180), empty enum `values` (L277), unparseable YAML (L312–313), non-mapping top-level (L324), non-dict `link_def`/`object_def` graceful skip (L298/L303), L1 error under `link_types` → `_ctx_from_path` context (L115–117), CLI `main([])` usage + return 1 (L343–344). Reuses the in-process `main()` + `capsys` pattern (Lesson #7 §3.2). Validator coverage **89% → 96%** (remaining misses are out-of-scope `_value_lc`/`_walk_lc` edges + `__main__`). +8 (1010→1018). |
| **Session-30 reconcile #1** | [#108](https://github.com/CrayJThiemsert/vero-lite/pull/108) (merge `3c23299`) | Brought STATUS current 29 → 30 after PR #107; `head_commit` → `442d180`. `lint_status` verified `fresh:true` post-merge. Docs-only. |
| **Loop schema parser edges** | [#109](https://github.com/CrayJThiemsert/vero-lite/pull/109) (`02ce502` → merge `8786be4`) | **`test(loop)`** — 8 additive tests in `tests/loop/test_schema.py` for `tools/loop/_schema.py`, all via the **public `parse_message_text`/`parse_filename` seam** (refactor-resilient): quoted scalar (L190), no-closing-fence (L218), list-break (L230-233), comment/blank/non-key lines (L244-250), missing `message_type` (L309-310), non-int `schema_version` (L322-323), scalar `references` (L348), malformed-filename short-circuit (L501). Coverage **94% → 100%**. +8 (1018→1026). |
| **NL-query engine coverage** | [#110](https://github.com/CrayJThiemsert/vero-lite/pull/110) (`5f432b4` → merge `05de6d9`) | **`test(engine)`** — 14 tests in `tests/services/engine/test_nl_query.py` for `services/engine/nl_query.py`: `_build_chat_client` config branches (L130-141), `_parse_query` non-JSON/schema errors (L242-247), `_to_number` bool guard (L289), `_scalar_equal` numeric (L300), `_filter_matches` gt/lte/non-numeric edges (L312/314/319), `_object_id`/`_object_title` fallbacks (L336-338/L346-348), and the two degrade paths — count-fallback (L365) + retrieval-failure (L477-479) — driven through the **real `answer_question` orchestrator**. Offline `_StubQueryClient` (no live Ollama). Coverage **89% → 100%**. +14 (1026→1040). |
| **Session-30 coverage reconcile** | [#111](https://github.com/CrayJThiemsert/vero-lite/pull/111) (merge `443ada7`) | Folded #109 + #110 into the ledger; `head_commit` → `05de6d9`. `lint_status` verified `fresh:true`. Docs-only. |
| **PLAN-0014 arming runbook** | [#112](https://github.com/CrayJThiemsert/vero-lite/pull/112) (`9b1010a` → merge `1d1f396`) | **`docs(runbooks)`** — `docs/runbooks/arm-plan-0014-telegram.md`: the verification-backed runbook for Cray to arm the MS-S1-unreachable Telegram ping on the demo box (this WSL machine, bare uvicorn + `.env` + tmux). Grounded in the code (4-condition gate, exact env vars, `/warm`+`/sleep`, `POST /query` trigger); covers the WSL tap-link networking fix + a verification ladder + disarm + no-PII notes. Flags the open port question (README `:8000` vs handoff `:8096`). |
| **status_digest loop handler** | [#113](https://github.com/CrayJThiemsert/vero-lite/pull/113) (`75e1219` → merge `e55c3f3`) | **`feat(loop)`** — PLAN-0010 deferred Step-4 use-case (a). The loop's first beyond-heartbeat job: detect `docs/STATUS.md` drift → no-PII Telegram nudge (v1 = detect-and-nudge, Cray-ratified; no auto-edit/commit). New `tools/loop/_status_digest.py` (reuses `compute_status_freshness` = single source of truth; argv Telegram contract per Lesson #0014; best-effort never-raises); wired into `_build_default_dispatcher`. 18 tests (full case-coverage matrix), module **100%**, +18 (1040→1058). **Found + flagged** (spawn-task chip): `make_telegram_alert` pipes to stdin but `telegram.sh` reads argv[1] → poison/cycle_failures alerts never reach Telegram (Lesson #0014 drift). |
| **Session-30 status_digest reconcile** | [#114](https://github.com/CrayJThiemsert/vero-lite/pull/114) (merge `654c65e`) | Folded #112 + #113 into the ledger; `head_commit` → `e55c3f3`. Docs-only. |
| **Dispatcher Telegram argv fix** | [#115](https://github.com/CrayJThiemsert/vero-lite/pull/115) (`f10cc58` → merge `f18da9b`) | **`fix(loop)`** — resolves the bug flagged in #113: `make_telegram_alert` passed its payload on stdin but `telegram.sh` reads `argv[1]`, so poison/cycle_failures alerts never reached Telegram (Lesson #0014 argv-vs-stdin drift). Now passes the alert as `argv[1]` via a human-readable `_format_alert_message` (mirrors `_status_digest._send_telegram`); +2 regression tests in `test_dispatcher.py`. **Authored by a spawned session** (from the PR-#113 chip), running in the shared main checkout; **Code reviewed the diff vs the chip spec (read-only) → full coverage, nothing to graft** then merged it. Process note: the shared-checkout run was a concurrency hazard (shared HEAD/index; an `index.lock` race) — future spawned work should use an isolated worktree. |
| **Session-30 telegram-fix reconcile** *(this PR)* | this PR | Folds #115 into the ledger; frontmatter (`head_commit` → `f18da9b`, `recent_commits`, `current_batch`, `blocked_on`, `next_action`) + Current Focus blurb. Docs-only. |

### 2026-06-01 (PM) — Session 29 ledger (STATUS reconcile + PLAN-0010 loop closed)

Reconciled the 2-session STATUS drift, then closed + live-tested + hardened the
PLAN-0010 autonomy loop end-to-end (one-shot drain → observability fix → Cray
registers the consumer → live producer↔consumer smoke → round-trip/collision
tests → Lesson #0020 → producer `-<rand>` fix). Suite 1003 → **1010 passed / 2
skipped**; ruff + `mypy services` clean.

| Phase | PR / artifact | Change |
|-------|--------------|--------|
| **STATUS reconcile (sessions 27+28)** | [#102](https://github.com/CrayJThiemsert/vero-lite/pull/102) (`304c6b4` → merge `d80d1e0`) | Brought STATUS current from session 26 → 28 (the PLAN-0013 + PLAN-0014 arc; #88–#101). Docs-only; recorded PLAN-0011 carry-over as RESOLVED. |
| **PLAN-0010 live loop diagnosis** | one-shot drain (no commit) | Disambiguated the 3 Desktop routines — producer `phase35-smoke-cowork-heartbeat` (writes `loop/inbox/`), gen-1 observe-only `phase35-smoke-code-reader` (old `docs/research/private/phase3.5-smoke/inbox/` path, left paused), gen-2 consumer `loop-dispatcher`. Ran `loop-dispatcher` one-shot → drained `loop/inbox/` 30→0 (`scan_cycle: ok=27 parse_failed=1 skipped_idempotent=2`). The `parse_failed` = a stray `heartbeat.msg.md` (valid body, bad filename) — exposed that non-poison failures had no Telegram signal. |
| **`cycle_failures` alert** | [#103](https://github.com/CrayJThiemsert/vero-lite/pull/103) (`9f9f929` → merge `9f07818`) | **`feat(loop)`** — one aggregate `cycle_failures` Telegram ping per cycle when `parse_failed > 0` or `dispatch_failed > 0` (poison keeps its own per-message alert; `expired` benign → excluded). Reuses the existing `alert_callback` (Telegram + stderr + graceful no-op). +4 tests (1003→1007); runbook documents the 3 alert reasons. Live-verified (stderr `{"alert":"cycle_failures",...}` fired on a synthetic bad-filename message, no real Telegram sent). |
| **loop-dispatcher registered (Cray-action)** | Desktop Routines | **PLAN-0010 autonomy loop CLOSED.** Cray registered `loop-dispatcher` (Local · Hourly · Sonnet 4.6 · Worktree OFF · branch `main`; SKILL.md description + Instructions pasted from `~/.claude/scheduled-tasks/loop-dispatcher/SKILL.md`); first live run verified (`tier=code branch=main`, inbox 1→0, no error/ALERT). **Backlog items 1 (tier-file re-paste) + 2 (loop-dispatcher setup; PR #55 was already merged) now DONE.** |
| **Producer↔consumer round-trip + collision regression test** | [#105](https://github.com/CrayJThiemsert/vero-lite/pull/105) (`2a3f942` → merge `4896188`) | **`test(loop)`** — new `tests/loop/test_loop_roundtrip.py` (additive; no prod change): the verbatim live-producer message round-trips through the consumer (`ok=1`); the NONCE collision drops the 2nd body silently (regression for the finding); `-<rand>` prevents it. +3 tests (1007→1010). |
| **Live producer↔consumer smoke (both routines)** | live run (no commit) | Cray Run-now'd both Desktop routines. **Producer** wrote a heartbeat; **consumer** drained inbox 2→0. A Code-injected unique control message (`loop-smoke-test-…-ksmt`) processed clean (`ok=1`). **The NONCE collision reproduced LIVE**: the Haiku producer could not read the clock, *guessed* `07:00 UTC`, hit an archived name, and its fresh heartbeat was silently deduped (`skipped_idempotent=1`; archived copy kept its 00:04 mtime). Both routines verified working end-to-end. |
| **Lesson #0020 minted** | `docs/lessons/0020-…md` (this PR) | **Agent-claimed timestamps are an unreliable uniqueness key** — LLM producers can't self-clock, guess round values, and collide → silent dedup. Convention: collision-resistance must come from non-clock entropy (`-<rand>` for LLM/best-effort producers; monotonic/uuid/content-hash for deterministic Step-5 producers). Reinforces PLAN-0010 AC-2 with empirical evidence. |
| **Producer `-<rand>` fix (Cray-action)** | Desktop Routines | Cray amended the `phase35-smoke-cowork-heartbeat` "Construct the filename" instruction to emit `…-<NONCE>-<RAND>.msg.md` (fresh 4-char `[a-z2-7]` per fire). No consumer-side change; `test_rand_suffix_prevents_collision` (#105) pins it. Fixes both the Step-5 data-loss risk and the smoke-loop observability defect (most fires were being deduped). |
| **STATUS reconcile (sessions 27+28)** | [#104](https://github.com/CrayJThiemsert/vero-lite/pull/104) (`3752871` → merge `25e58db`) | First session-29 reconcile — captured PR #102/#103 + the loop-dispatcher register milestone. Docs-only. |
| **Session-29 close — Lesson #0020 + reconcile** *(this PR)* | this PR | Mints Lesson #0020 + folds PR #105 + the live smoke + the producer `-<rand>` fix into the ledger; frontmatter (`head_commit` → `4896188`, `recent_commits`, `current_batch`, `blocked_on`, `next_action`). Docs-only. |

### 2026-06-01 — Session 28 ledger (AC-template → PLAN-0013 done; PLAN-0014 shipped; reconciled)

AC-template (the last PLAN-0013 AC) closed via a 2nd vertical; PLAN-0013 → 7/7,
archived. Then PLAN-0014 (LLM-unreachable recovery loop) drafted + executed +
archived. Suite 954 → **1003 passed / 2 skipped** (+23 #99, +26 #101); ruff +
`mypy services` clean.

| Phase | PR / artifact | Change |
|-------|--------------|--------|
| **AC-template — `supply_chain` 2nd vertical** | [#99](https://github.com/CrayJThiemsert/vero-lite/pull/99) (`1fa0d53` + `d4bc0a6` → merge `99bee59`) | **PLAN-0013 AC-template DONE → 7/7; closed to `done/`.** Adds the `supply_chain` (cold-chain logistics) vertical + a configurable `OCT_VERTICAL` (default `energy`) + `OCT_RECOMMEND_*` config; generalizes the residual energy-specific coupling in the recommender + `trace.py` + 4 `static/` spots so the diff is vertical-agnostic. Full A/B/C/D re-skin live-captured (all 4 views + approve→execute→DB-persist + grounded NL query) — proves the *same UI build* (`services/api/static/`) renders a different ontology with **zero UI-code change**. Data-driven 2nd instance, no new abstraction (Rule-of-Three preserved). +23 tests. |
| **PLAN-0014 mint (Draft) + `/warm`** | [#100](https://github.com/CrayJThiemsert/vero-lite/pull/100) (`e6a1130` + `bfe6137` → merge `f9f6835`) | **PLAN-0014 (LLM-unreachable Telegram notify) minted Status `Draft`.** `plan-drafter` subagent-authored, Code-reviewed, Cray-ratified at merge (author≠reviewer INTACT per ADR-012 D4.3). Adds a `GET /warm` companion endpoint (Cray-approved) to the plan scope. Docs-only. |
| **PLAN-0014 execution** | [#101](https://github.com/CrayJThiemsert/vero-lite/pull/101) (`d6ef9cb` → merge `27ea292`) | **PLAN-0014 executed → `done/`.** `OllamaUnreachableError` + `services/notify/telegram.py` (best-effort, cooldown) fired when MS-S1 is powered off; `OllamaClient.warm()/unload()/ps()`; browser/phone-tappable `GET /warm` (blocking + `?wait=false`) + `GET /sleep`; recommender + `nl_query` notify wiring. Reuses the existing `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` (ADR-013 D5 — no new bot). Live-smoked `/warm` + `/sleep` against MS-S1. +26 tests (977 → 1003). |
| **STATUS reconcile (sessions 27 + 28)** *(this PR)* | this PR | **Sessions 27 + 28 ledger entries + Current Focus narrative + frontmatter** (`session` → 28, `head_commit` → `27ea292`, `recent_commits`, `current_batch`, `blocked_on`, `next_action`). Brings STATUS current from session 26 → session 28 — the overdue end-of-arc reconcile (the drift `lint_status` reports). Also records the session-26 carry-over PLAN-0011 fresh-trigger re-run as **RESOLVED** (PLAN-0011 now `Complete`, in `done/`). No code/test/settings touched. |
| **Backlog — Cray-action (human)** | next_action (a) | Re-paste both tier files into the Desktop UI (OQ-T5 sync); PLAN-0010 loop-dispatcher Desktop one-time setup + verify PR #55; arm PLAN-0014 on the demo box (`TELEGRAM_*` + `TELEGRAM_NOTIFY_ENABLED=true` + `OCT_PUBLIC_BASE_URL`). |
| **Backlog — Code-executable (active plans)** | next_action (b) | PLAN-0010 (Phase 3.5 scheduled-task autonomy loop — consumer side gated on the Cray Desktop setup); PLAN-004 Phases B + C (handoff dashboard, low priority); PLAN-0012 Phase 2 (vero-bridge — when a concrete capability need lands). |

### 2026-05-31 — Session 27 ledger (PLAN-0013 build → 6.5/7 ACs; closed)

The long session (2026-05-30 → 2026-05-31): PLAN-0013 minted + Steps 1–6 built
live on the **energy** vertical + the alembic/test-DB hardening, leaving the demo
at 6.5/7 ACs (AC-template the only remainder). Plus 2 prerequisite docs PRs.
Suite 794 → **954 passed / 2 skipped** across the arc; ruff + `mypy services`
clean.

| Phase | PR / artifact | Change |
|-------|--------------|--------|
| **PLAN-004 status reconcile** | [#88](https://github.com/CrayJThiemsert/vero-lite/pull/88) (`2daaa74` → merge `5ac77cb`) | Reconcile PLAN-004: **Phase A COMPLETE** (handoff frontmatter + schema + dashboard reader shipped), keep the plan active for forward-declared Phases B + C. Docs-only (+15/−1). |
| **STRATEGIC_CONTEXT_AIP north-star** | [#89](https://github.com/CrayJThiemsert/vero-lite/pull/89) (`5faf086` → merge `cc25515`) | Track `docs/strategy/public/STRATEGIC_CONTEXT_AIP.md` (462 lines) — long-term "operational intelligence platform, not a chatbot" architectural context for future LLM / ADR / planning sessions (per ADR-009 OQ-1). New tracked reference doc. |
| **PLAN-0013 mint** | [#90](https://github.com/CrayJThiemsert/vero-lite/pull/90) (`160a0a2` → merge `6440d11`) | **PLAN-0013 (OCT Stakeholder Demo) minted Status `Draft`.** Cowork-drafted cold from Code's verified dispatch (ADR-009 D1 / ADR-013 OQ-1); 3 OCT features (map / anomaly+trace / NL query) on the energy vertical, ontology-driven UI. 7 ACs incl. AC-template + the Code-authored Screen D (data→decision flow) + AC-flow (Cray-ratified). |
| **Step 1 — backend tweaks** | [#91](https://github.com/CrayJThiemsert/vero-lite/pull/91) (`3686f9c` → merge `2aab473`) | Expose the reasoning trace on recommendations + add a `/meta` endpoint (OntologyMeta — legend + status enums the UI binds to). |
| **Step 2 — grounded NL query** | [#92](https://github.com/CrayJThiemsert/vero-lite/pull/92) (`f27cdef` → merge `e1c1256`) | `POST /query` — grounded natural-language operational query (`{question}` → `{answer, grounded, structured_query, source_object_ids, result_count}`); "not invented" no-data path. |
| **Step 3 — design prompt + tone** | [#93](https://github.com/CrayJThiemsert/vero-lite/pull/93) (`5e18920` → merge `733d5c4`) + [#94](https://github.com/CrayJThiemsert/vero-lite/pull/94) (`2df57db` → merge `1c28e7f`) | Claude Design prompt for the OCT demo UI (#93) + a Cowork operator-voice tone pass (#94). Cray then ran Claude Design (Step 4) to produce the static UI. Docs/design-only. |
| **Step 5 — serve the UI** | [#95](https://github.com/CrayJThiemsert/vero-lite/pull/95) (`ba6b5af` → merge `23d595f`) | Serve the Claude-Design OCT UI static from FastAPI (`app.mount("/", StaticFiles, html=True)`) — one process, one URL (:8096), same-origin. |
| **Step 6 — UI polish** | [#96](https://github.com/CrayJThiemsert/vero-lite/pull/96) (`aff0abb` → merge `214b97b`) | OCT UI polish — strip the "LIVE" strip text + query operator symbols. |
| **alembic FK-index drift fix** | [#97](https://github.com/CrayJThiemsert/vero-lite/pull/97) (`2523418` → merge `23338fa`) | Declare FK indexes in the ORM models to match the migration + DDL (`alembic check` clean) + a regression test. |
| **test-DB isolation (sustainable)** | [#98](https://github.com/CrayJThiemsert/vero-lite/pull/98) (`a673c6a` → merge `f646277`) | Target a disposable `vero_lite_test` DB via `TEST_DATABASE_URL` so the full `pytest` run never wipes the dev/demo DB. Closes the "tests wipe the demo DB" gotcha (memory `project_test_suite_drops_demo_db` = FIXED). |

> **Note on the 26/27 boundary.** PRs #88–#90 merged the morning of 2026-05-30,
> bridging the session-26 OQ-T5 close (#87) into the PLAN-0013 build; grouped here
> with session 27 as one continuous demo-build arc. Session 27 filed no separate
> STATUS reconcile — folded into this sessions-27+28 reconcile.

### 2026-05-30 — Session 26 ledger (OQ-T5 reconcile)

| Phase | PR / artifact | Change |
|-------|--------------|--------|
| **OQ-T5 reconcile** | this PR | **Chat-as-bridge-client RESOLVED — Chat is NOT a sanctioned client.** Advisory chain: Code advisory (`.claude/handoffs/session-26/2026-05-30-0031-code-oq-t5-advisory.md`, gitignored) → Cowork dispatch (`…-1030-cowork-oqt5-chat-bridge-client-dispatch.md`, gitignored) → Cray adjudication ("B by decision, C by effort"). Edits: `docs/conventions/chat_tab_instructions.md` (behavioral rule 7 spoof-refusal + rule 8 not-a-bridge-client + "What you are NOT" bullet); `docs/conventions/cowork_tab_instructions.md` (Bridge-client posture — sanctioned client, truthful-tag-only, no-authority, no-commit); `docs/plans/0012-vero-bridge.md` surgical (Goal OQ-T5 pointer + AC-3 replay re-characterization + AC-4(c) OQ-T5 RESOLVED; full AC-6/AC-7 sweep deliberately skipped); new **Lesson #0019** (`docs/lessons/0019-adversarial-spoof-tests-belong-at-unit-layer.md`); this STATUS update. **No new ADR** (PLAN-0009 OQ-3). Docs-only; no code/test/settings touched. **Cray follow-up:** re-paste both tier files into the Desktop project-instructions UI. |

### 2026-05-29 — Session 25 ledger (Step 2b + follow-ups, closed)

| Phase | PR / artifact | Change |
|-------|--------------|--------|
| **Step 2b tool 1/4 — `read_repo_path`** | [#80](https://github.com/CrayJThiemsert/vero-lite/pull/80) (`b8a1c09`+`4e0c254` → merge `abf453e`) | **§2.4 path-sandboxed read-only repo-file reader.** New `tools/vero_bridge/_repo_read.py`: relative + no `..` + in-tree-after-symlink-resolve + not `.git/` + **git-tracked allowlist** + regular file ≤2 MiB + UTF-8 → new `ErrorCode.PATH_FORBIDDEN`. Review pass added 2 fail-closed guards (NUL-byte path, OSError on read; `4e0c254`). +36 tests. Surface 3→4. |
| **Step 2b tool 2/4 — `validate_handoff_frontmatter`** | [#81](https://github.com/CrayJThiemsert/vero-lite/pull/81) (`5bfd487` → merge `af94735`) | **§2.5 in-process handoff-schema validation.** New content-based entry point `tools/handoffs/_schema.py::parse_frontmatter_text` (path-based `parse_frontmatter` refactored to delegate — behaviour-preserving) + bridge adapter `_handoff_validate.py`. Closes Lesson #8 K-1. `ok`=transport, `valid`=content; no new `ErrorCode`. +24/+3 tests. Surface 4→5. |
| **Step 2b tool 3/4 — `lint_status`** | [#82](https://github.com/CrayJThiemsert/vero-lite/pull/82) (`eb10fc3` → merge `e98aa83`) | **§2.6 STATUS freshness vs local `main`.** New `tools/vero_bridge/_status_lint.py`. Real-operation divergences from spec: baseline = **local `main`** (not `origin/main` — WSL-local, no network) + **`--no-merges`** (merge-commit workflow — see Lesson #18). Fail-closed (`fresh=False`). +12 tests. Surface 5→6. |
| **Step 2b tool 4/4 — `dispatch_receive`** | [#83](https://github.com/CrayJThiemsert/vero-lite/pull/83) (`b3e3d3c` → merge `1b52e3a`) | **§2.7 receive-only dispatch inbox.** New `tools/vero_bridge/_dispatch_queue.py`: appends envelope to a gitignored queue (same write-class as the audit log, best-effort) + content-addressed `received_id`; `ts_ns` decimal string (FINDING-2). **No commit, no bind-on-Cray.** +11 tests. **Surface 6→7 — Phase 1 safe-for-all tool surface COMPLETE.** |
| **Loop-detect commit-boundary reset** | [#84](https://github.com/CrayJThiemsert/vero-lite/pull/84) (`3ea2ac1` → merge `c7d5896`) | **L1 false-positive fix.** `posttooluse_progress_observer.py` resets a file's L1 counter on a successful `git commit` (only the committed files; reliable PostToolUse Bash path). Fixes the 6-legit-cross-PR-edits-to-`server.py` hard-block. Precise (per-file) + fail-closed; no change to the deny gate/threshold. +8 tests. See Lesson #12 §7. |
| **Lessons #12 (amend) + #18 (new)** | [#85](https://github.com/CrayJThiemsert/vero-lite/pull/85) (`1840d3f` → merge `1ec53b0`) | **Lesson #12 §7** (cross-PR/cross-session L1 accumulation + #84 fix + 2 meta-lessons: verify a handoff's claimed mitigation against real state/hook; a chat ack does not unblock a deterministic hook). **Lesson #18** (`git log --grep` needs `--no-merges` under a merge-commit workflow; + spec→as-built `origin/main`→local-`main` norm). Docs-only. |
| **STATUS reconcile (session-25)** *(this PR)* | this PR | **Session 25 ledger + Current Focus narrative + Step-2b 7/7 scoreboard.** Frontmatter (`session` → 25, `head_commit` → `1ec53b0`, `recent_commits`, `current_batch`, `blocked_on`, `next_action`). Brings STATUS current from session 24 → 25 (the drift `lint_status` itself reported). No code/test/settings touched. |

### 2026-05-29 — Session 23 + 24 ledger (closed)

| Phase | PR / artifact | Change |
|-------|--------------|--------|
| **Cray-side Action 0** (session 23) | `claude_desktop_config.json` (UWP path, Lesson #0016) | **Production `mcpServers.vero-bridge` entry added + Desktop restart.** Points to `wsl.exe ... uv run --extra dev python -m tools.vero_bridge.server`; mirrors the existing `mcpServers.vero-bridge-probe`. Both coexist. This unblocked the live cross-client evidence (Steps 3a/3b/4). |
| **Phase 1 Step 3a — Chat client** | [#73](https://github.com/CrayJThiemsert/vero-lite/pull/73) (`69b33ff` → merge `7cd56d1`) | **Chat-tab client invocation** against the Step 1 wire format (raw + doc-rot guard). Chat loads `mcp__vero-bridge__echo` via ToolSearch from its deferred list. +356/−1. New `tests/vero_bridge/test_chat_client.py`; `docs/conventions/vero-bridge-wire-format.md` updated. |
| **Phase 1 Step 3b — Cowork client + AC-7 parity** | [#74](https://github.com/CrayJThiemsert/vero-lite/pull/74) (`ec22162` → merge `69d3be0`) | **Cowork-tab client**, same wire format + tool surface as Step 3a (**AC-7 cross-client parity**). +243/−0. New `tests/vero_bridge/test_cowork_client.py`; wire-format doc updated. |
| **ts_ns precision fix (FINDING-1/2)** | [#75](https://github.com/CrayJThiemsert/vero-lite/pull/75) (`b90442d` → merge `476e9c7`) | **FINDING-2:** `ts_ns` (int64 ≈ 1.78×10¹⁸ > 2⁵³) corrupted by structuredContent-consuming clients (Code, Cowork) via IEEE-754 double → `server.py:149` returns `str(record["ts_ns"])`; audit log keeps the int (source of truth, Python-read). **FINDING-1:** `ts_ns` is wall-clock epoch ns, not monotonic; ordering key = per-process `monotonic_counter` (resets per respawn) — docstring corrected. +100/−32. Touched `server.py`, `_audit_log.py`, `test_server.py`, `test_chat_client.py`, `test_cowork_client.py`, capability-inventory + wire-format docs. |
| **Phase 1 Step 4 — cross-client live evidence** | [#76](https://github.com/CrayJThiemsert/vero-lite/pull/76) (`0e60300` → merge `35759cd`) | **AC-3 / AC-6 / AC-7 DONE; AC-4(c) basis live-proven (full matrix = Step 5).** Post-fix re-smoke: all 3 clients round-trip ts_ns string byte-exact (Chat `…624177`, Code `…448359`, Cowork `…125591`); Code+Cowork share `pid 1189` counter 1→2 (same-instance, 2nd epoch). +151/−7. New tracked runbook [`docs/runbooks/vero-bridge-cross-client-evidence.md`](runbooks/vero-bridge-cross-client-evidence.md) + plan AC marks; verbatim evidence in gitignored `docs/research/private/2026-05-29-vero-bridge-step4-cross-client-evidence.md` (split per PR #61 precedent). |
| **Tooling — /eli-cray + auto-memory** (session 24) | user-level command + auto-memory | Created `~/.claude/commands/eli-cray.md` (`/eli-cray` — pull an ELI-CTO explanation of the last work batch, Thai; optional focus arg). New auto-memory `feedback_verify_relayed_responses_vs_audit_log` (cross-check Cray-relayed Chat/Cowork tab responses against the audit log to catch replays vs fresh calls). No repo files touched. |
| **STATUS reconcile (session 23+24)** | [#77](https://github.com/CrayJThiemsert/vero-lite/pull/77) (`769b408` → merge `c4d10dd`) | **Session 23 + 24 ledger entries added.** Frontmatter + Current Focus narrative (session 23+24 + AC scoreboard) + this ledger sub-section. Brought STATUS current from session 22 → session 24. No code/test/settings touched. |
| **Phase 1 Step 5 — adversarial spoof matrix + AC-8 negative** | [#78](https://github.com/CrayJThiemsert/vero-lite/pull/78) (`a6f43d3` → merge `55a4cf3`) | **AC-4(c) / AC-5 / AC-8 DONE → all 8 Phase 1 ACs COMPLETE.** 26 adversarial/negative/boundary tests (`tests/vero_bridge/test_server_adversarial.py`; suite 813 passed / 7 skipped; ruff + mypy clean; G5 deny suite green). Live spoof matrix: Code self-spoof (epoch A pid 30773) + Cowork spoof claiming chat/code + Code witness (epoch B pid 1138, shared fds) → server accepts spoofs (Option I), Code/Cowork transport-indistinguishable; **Chat refused to self-spoof (FINDING-4)**, Cowork complied. **FINDING-3:** AC-8 enforced by framework `ToolError`, not a `tool-not-found` JSON body (inventory §4 amended; `ErrorCode.TOOL_NOT_FOUND` reserved for Phase 2+). **OQ-T5** (Chat-as-bridge-client vs `chat_tab_instructions.md`) surfaced for Cray — not minted into the plan by Code (author boundary + L1 loop-detect). Evidence: gitignored `docs/research/private/2026-05-29-vero-bridge-step5-spoof-matrix.md` + runbook §5. |
| **STATUS reconcile (session-24 #78 closeout)** *(this PR)* | this PR | **#78 / Step 5 added to ledger; AC scoreboard → 8/8 COMPLETE; frontmatter (`head_commit` → `55a4cf3`, `recent_commits`, `current_batch`).** Step 2b handoff prepared (`.claude/handoffs/session-24/…`). No code/test/settings touched. |
| **Queued — Phase 1 Step 2b** | next_action (b) | **4 integration tools as separate PRs** (autonomous Code-side): `read_repo_path` (path sandbox/allowlist) + `validate_handoff_frontmatter` (schema import from `tools.handoffs`) + `lint_status` (git subprocess + STATUS frontmatter parse) + `dispatch_receive` (receive-queue lifecycle). |
| **Carry-over (independent of PLAN-0012)** | session 18→19 handoff §3 | **PLAN-0011 AC-3/AC-7 fresh-trigger re-run** (~30 min Cray-driven; flip classifier dispatch BLOCKED → PASS with a fresh trigger not in any tracked file) + **loop-dispatcher Desktop UI one-time setup** (PLAN-0010 — verify PR #55 status; plan still `Ready for execution`). |

### 2026-05-28 ~17:30 +07 — Session 22 ledger (closed)

| Phase | PR / artifact | Change |
|-------|--------------|--------|
| **STATUS reconcile (session 20+21)** | [#68](https://github.com/CrayJThiemsert/vero-lite/pull/68) (`202cfa1` → merge `43370cc`) | **Session 20 + 21 ledger entries added.** Frontmatter (`last_updated`, `session` → 21, `head_commit` → `b3a6070`, `recent_commits`, `current_batch`, `blocked_on`, `next_action`) + Current Focus narrative + 2 new ledger sub-sections (session 20+21 closed + session 19 closed reframe with supersession annotation). Brought STATUS current from session 19 → session 21. **Proposed Cray ratification** of PLAN-0012 Status `Draft` → `Ready for execution`. No code/test/settings touched. |
| **PLAN-0012 ratified + OQ-T1/T4/V2 resolved** | [#69](https://github.com/CrayJThiemsert/vero-lite/pull/69) (`7a22066` → merge `e2fda26`) | **Cray adjudicated 4 governance decisions** in a single session-22 routing turn after PR #68 review: (1) **PLAN-0012 Status flipped `Draft` → `Ready for execution`** (header line 3 + Status-vocabulary reconciliation blockquote updated); (2) **OQ-T1 RESOLVED `fail-closed`** — server drops + logs + does NOT retry on transport failure; aligns with ADR-013 D2 deterministic-deny posture; bounded-retry / surface-to-Cray deferred to Phase 2; (3) **OQ-T4 RESOLVED `serial-per-instance`** — server queues incoming calls + processes one-at-a-time per instance; deterministic audit-log ordering; concurrent-per-call deferred to Phase 2 once contention pressure evidence exists; (4) **OQ-V2 DEFERRED with `version: int` stub directive** — every wire frame carries mandatory `version: int`; Phase 1 accepts only `v1`; full negotiation policy (per-session / per-call / per-tab) decided when client codepaths diverge. Single-file edit; +121 / −65; no code/test/settings touched. |
| **Phase 1 Step 1 — wire format + schema + inventory** | [#70](https://github.com/CrayJThiemsert/vero-lite/pull/70) (`61d93fe` → merge `35f59ad`) | **AC-1 + AC-8 (docs portion) DONE.** 4 new files; +1,197 LOC; +66 tests (634 → 700). [`tools/vero_bridge/_schema.py`](../tools/vero_bridge/_schema.py) — stdlib-only envelope schema mirroring `tools/handoffs/_schema.py` discipline: `Envelope` frozen dataclass + `MessageType` enum (ECHO active; SIGNAL + DISPATCH_RECEIVE placeholders for Phase 2+) + `ErrorCode` enum (6 codes per OQ-T1 fail-closed surface) + `BridgeError` hierarchy + `parse_envelope()` (fail-closed first-failure-wins; ordering: version → claimed_tag → message_type → payload) + `format_error_response()` (the only allowed `BridgeError` → client path). [`tools/vero_bridge/__init__.py`](../tools/vero_bridge/__init__.py) — public re-exports. [`docs/conventions/vero-bridge-wire-format.md`](conventions/vero-bridge-wire-format.md) — human-readable counterpart to the schema; transport assumptions (A1 stdio-MCP + tab-group routing per Lesson #0017 §3.1), envelope fields, validation order + failure semantics (OQ-T1), error code catalog, concurrency model (OQ-T4 serial-per-instance), implementation discipline, versioning policy (OQ-V2 deferred). [`docs/conventions/vero-bridge-capability-inventory.md`](conventions/vero-bridge-capability-inventory.md) — canonical "what is exposed where" reference materialized from PR #67 Cowork completion handoff §3: 7 safe-for-all tools (`echo`, `bridge_status`, `bridge_whoami`, `read_repo_path`, `validate_handoff_frontmatter`, `lint_status`, `dispatch_receive`) with per-tool args/returns/side-effects/classification rationale + 8 not-on-bridge ops with the mechanism that handles them instead + AC-8 negative test contract for Step 5. ruff + ruff format + mypy --strict --explicit-package-bases (4 source files) clean. |
| **Phase 1 Step 2 — server + audit log + 3 introspection tools** | [#71](https://github.com/CrayJThiemsert/vero-lite/pull/71) (`99a908f` → merge `438e3c5`) | **AC-2 + AC-4 (a)/(b) DONE + AC-3 chain UNBLOCKED + AC-4 (c) prereq met.** 4 new files; +1,147 LOC; +55 tests (700 → 755). [`tools/vero_bridge/server.py`](../tools/vero_bridge/server.py) — FastMCP `"vero-bridge"` server with 3 introspection tools: `echo(version, claimed_tag, name)` (AC-3 round-trip carrier) + `bridge_status(version, claimed_tag)` (operational state: uptime/pid/last_call_ts_ns) + `bridge_whoami(version, claimed_tag)` (audit fingerprint: PID, ppid, stdin_fd, stdout_fd, ts_ns, env_keys_seen). Each tool: `parse_envelope()` → on `BridgeError`, log + return `format_error_response()`; on success, log + execute. `SERVER_START_TS` captured at module import; `_last_call_ts_ns` module-global updated only on `outcome=="ok"`. `main()` entry-point for `python -m tools.vero_bridge.server` (Desktop spawn target). [`tools/vero_bridge/_audit_log.py`](../tools/vero_bridge/_audit_log.py) — JSONL append-only writer with per-process monotonic counter, malformed-input-safe rendering (`_safe_claimed_tag` + `_safe_version` — audit log captures spoof attempts with structurally-invalid envelope fields), OSError-into-`audit_io_error`-key swallowing (audit-log lossless guarantee — AC-4 (c) anti-spoof matrix depends on it). Default log path `docs/research/private/vero-bridge-audit.jsonl` (gitignored). ruff + ruff format + mypy --strict (8 source files) clean. **Step 2b deferred** (4 integration tools: `read_repo_path` / `validate_handoff_frontmatter` / `lint_status` / `dispatch_receive`) — each has its own design surface; one substantial PR per tool keeps review tractable. |
| **STATUS reconcile (session 22)** *(this PR)* | this PR | **Session 22 ledger entries added.** Frontmatter (`last_updated`, `session` → 22, `head_commit` → `99a908f`, `recent_commits`, `current_batch`, `blocked_on`, `next_action`) + Current Focus narrative covering 4 PRs (#68–#71) + new session 22 ledger sub-section. Brings STATUS current from session 21 → session 22 before session 22 closes. No code/test/settings touched. |
| **Queued — Cray-side one-time setup** | session 23 next_action (a) | **Add `mcpServers.vero-bridge` entry** to `claude_desktop_config.json` (UWP path per Lesson #0016 — `C:\Users\<u>\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`) pointing to `wsl.exe -d Ubuntu-24.04 -- bash -lc 'cd ~/work/vero-lite && uv run --extra dev python -m tools.vero_bridge.server'`. Mirror the existing `mcpServers.vero-bridge-probe` pattern (both can coexist). After Desktop restart, production server is available alongside the gitignored probe. |
| **Queued — Phase 1 Step 3a + 3b** | session 23 next_action (b) | **Chat-side + Cowork-side client wrappers** against the Step 1 wire format. Per OQ-V1 RESOLVED uniform safe-tool scope (same tool set for all tabs in Phase 1). Cross-client parity per AC-7. Each client invokes `mcp__vero-bridge__<tool>` from its deferred list (loaded via ToolSearch) — identical primitive shape across Chat + Cowork. |
| **Queued — Phase 1 Step 2b** | session 23 next_action (c) | **4 integration tools** as separate PRs (one substantial PR per tool — review tractability): `read_repo_path` (path sandbox/allowlist + symlink resolution + size limit) + `validate_handoff_frontmatter` (schema import from `tools.handoffs`) + `lint_status` (git subprocess + STATUS frontmatter parse) + `dispatch_receive` (gitignored receive-queue path + lifecycle). |
| **Queued — Phase 1 Step 4** | session 23 next_action (d) | **Cross-client round-trip echo matrix** — Chat→Code→Chat + Cowork→Code→Cowork; capture live evidence to a named file under `docs/research/private/` (AC-3 + AC-6). |
| **Queued — Phase 1 Step 5** | session 23 next_action (e) | **Full AC-5 cross-client + adversarial matrix + AC-8 negative test** — adversarial cross-tab anti-spoof matrix (AC-4 (c)) + AC-8 not-on-bridge tool-call returns `tool-not-found` (negative test) + case-coverage matrix per the Cray verification-rigor directive. |
| **Deferred (carry-over from session 19)** | session 18→19 handoff §3 #4 + #5 | **AC-3/AC-7 fresh-trigger live re-run for PLAN-0011** (~30 min Cray-driven; meta-awareness contamination per PR #53 §AC-3 — use a NEW trigger not in `scenario3-*.md`/`scenario5-*.md`); capture Telegram `message_id` + Sonnet verdict; flip BLOCKED → PASS. **Cray Desktop UI one-time setup for `loop-dispatcher`** per [`runbooks/loop-dispatcher-scheduled-task.md`](runbooks/loop-dispatcher-scheduled-task.md) §"One-time setup (Cray)" (~5 min). Both independent of PLAN-0012 work. |
| **Deferred (low-value)** | session 22 handoff §4 Actions 5+6 | **ADR-013 amendment for A1 soft-violation** — defer until Phase 1 Step 2b ships (more accurate after living with the soft-violation across the full server surface, not just the introspection arm). **`references_artifacts` schema registration** in `tools/handoffs/_schema.py` OPTIONAL_FIELDS — defer; current non-fatal warning behavior doesn't block any work. |

### 2026-05-28 ~15:30 +07 — Session 20 + 21 ledger (closed)

| Phase | PR / artifact | Change |
|-------|--------------|--------|
| **PLAN-0012 mint** (session 20) | [#63](https://github.com/CrayJThiemsert/vero-lite/pull/63) (`8971074` → merge `04e9e01`) | **PLAN-0012 `vero-bridge` minted Status `Draft`.** Cowork-drafted under ADR-009 D1 interim phasing (ADR-013 OQ-1). OQ-A pre-decided **A1 stdio-MCP transport** (MCP servers wired via `mcpServers` entry in `claude_desktop_config.json`; soft-violation of ADR-013 D1 acknowledged — under A1 the server is owned by Desktop, not by Code; ADR-013 amendment deferred until Phase 1 Step 2 lives in production code). 8 ACs; Phase 1 implementable. v1 scope at mint time = Code↔Chat-only (Cowork-client dropped per OQ-C `cowork-network-locus` ratification — later expanded to Code↔(Chat+Cowork) in PR #67 once OQ-B confirmed Desktop spawn capability under UWP sandbox + OQ-T3 Option I accepted the empirically-corrected tab-group routing model). |
| **OQ-B + Lesson #0016** (session 21) | [#64](https://github.com/CrayJThiemsert/vero-lite/pull/64) (`cd670b3` → merge `5be0ec9`) | **OQ-B RESOLVED YES (FULL).** Claude Desktop CAN spawn additional MCP servers via `mcpServers` config under the UWP Microsoft Store sandbox. **Lesson #0016 minted** ([`docs/lessons/0016-claude-desktop-uwp-sandbox-config-path.md`](lessons/0016-claude-desktop-uwp-sandbox-config-path.md)) — UWP install config path gotcha: `C:\Users\<u>\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`, NOT the win32-tradition `%APPDATA%\Claude\claude_desktop_config.json` (Microsoft Store install redirects under UWP virtualization). Prerequisite for any Phase 1 deployment instruction. Audit trail in gitignored `docs/research/private/2026-05-28-oq-b-chat-mcp-spawn-probe.md` §1–§7 (probe matrix T1–T7). |
| **Lesson #0017 mint** (session 21) | [#65](https://github.com/CrayJThiemsert/vero-lite/pull/65) (`c785d90`) | **Lesson #0017 initial draft** ([`docs/lessons/0017-mcp-cross-tab-visibility-empirical-probe.md`](lessons/0017-mcp-cross-tab-visibility-empirical-probe.md)) — cross-tab MCP visibility model + 5-step empirical-probe checklist ("probe before infer"). Initial §3 was inference-based on MCP protocol shape ("each tab gets its own MCP server instance"). Subsequently empirically falsified — see PR #66 below (meta-recursion: this lesson ate itself). |
| **Lesson #0017 §3+§5 empirical correction** (session 21) | [#66](https://github.com/CrayJThiemsert/vero-lite/pull/66) (`0bbb149` → merge `98214fc`) | **Meta-recursion: lesson eats itself.** Initial §3 inference ("each tab gets its own MCP server instance") falsified via `ps aux` probe after Cray surfaced an OQ that could only be answered by system-level state. **Corrected model: tab-group routing** — Chat alone on instance A (PID 613); Code + Cowork share instance B (PID 2092). Server cannot cryptographically discriminate Code from Cowork — by design accepted under OQ-T3 Option I (capability-by-tool-design). **§5 added 5th step**: "link system-level state to protocol-level evidence" — extracted from the meta-recursion itself. **New auto-memory `feedback_empirical_probe_before_trivial_oq.md`** codifies "probe before infer" for future tab sessions (session-20 OQ-T3 trivial-wrong, session-21 `ps aux` corrected — Lesson #0017 §5). |
| **PLAN-0012 v1 expand** (session 21) | [#67](https://github.com/CrayJThiemsert/vero-lite/pull/67) (`b3a6070` → merge `4ee8987`) | **PLAN-0012 v1 scope expand** Cowork-drafted: Code↔(Chat+Cowork) under A1 stdio-MCP (not Code↔Chat-only). **OQ-T3 RESOLVED Option I** (capability-by-tool-design): `claimed_tag` = audit-only (not authorization); bridge surface = tab-tier-safe operations only; dangerous ops not-on-bridge; accepts that the server cannot discriminate Code from Cowork under tab-group routing. **OQ-V1 RESOLVED** (uniform safe-tool scope for Phase 1). **2 new OQs surfaced**: **OQ-T4** (cross-client concurrency — must adjudicate before Step 4/5 AC-5 tests; options: serial-per-instance / concurrent-per-call / serial-per-tool hybrid; Code recommends serial-per-instance for Phase 1) + **OQ-V2** (wire-format version negotiation — safe to defer past Phase 1; options: per-session / per-call / per-tab). Cowork completion handoff §3 drafted AC-8 capability inventory (7 safe-for-all tools — `echo`, `bridge_status`, `bridge_whoami`, `read_repo_path`, `validate_handoff_frontmatter`, `lint_status`, `dispatch_receive`; + 8 not-on-bridge ops — git writes, dispatch_bind_on_cray, write_file, run_shell, all git_*, set_status, modify_settings, kill/restart_server). Inventory to be materialized under Phase 1 Step 1 execution, NOT pre-materialized. |
| **STATUS reconcile** (session 21) | [#68](https://github.com/CrayJThiemsert/vero-lite/pull/68) (`202cfa1` → merge `43370cc`) | **Session 20 + 21 ledger entries added.** Frontmatter + Current Focus + 2 new ledger sub-sections (session 20+21 closed + session 19 reframe). Brought STATUS current from session 19 → session 21. **Proposed Cray ratification of PLAN-0012 Status `Draft` → `Ready for execution`** — Cray adjudicated 4 governance decisions in PR #69 (next session-22 row above). |

### 2026-05-28 ~09:00 +07 — Session 19 ledger (closed)

| Phase | PR / artifact | Change |
|-------|--------------|--------|
| **OQ-C experiment + runbook** | [#61](https://github.com/CrayJThiemsert/vero-lite/pull/61) (`aab8c84` → merge `23b18c2`) | **PLAN-0012 v1 input locked.** New [`docs/runbooks/cowork-network-locus.md`](runbooks/cowork-network-locus.md) (82 lines, tracked + citable) lifts ratified conclusion from gitignored audit-trail research note `docs/research/private/2026-05-28-oq-c-cowork-mcp-locus-experiment.md`. **Cowork-executed honestly**: `mcp__workspace__bash` → K-1 UNC abort 3× reproduced (deterministic, not a transient boot state); `mcp__workspace__web_fetch` → functional for public URLs (control `https://example.com` returned full body same session) but ALL 4 local URLs (`127.0.0.1`, `localhost`, `host.docker.internal`, `172.22.59.116`) returned no body/status/token; `mcp__Claude_in_Chrome__*` → present but `list_connected_browsers` empty (unexercisable). **Cray-side decisive evidence**: HTTP echo server logged ZERO inbound hits for the entire Cowork run window — server-side corroboration that no Cowork request reached Cray's loopback or WSL bind. **Scenario (i) desktop-proxy ruled out HIGH confidence**. PLAN-0012 v1 implication (at the time): drop Cowork-client; defer to v2 once tunneled rendezvous (ngrok/cloudflared/WAN+port-forward) designed + (ii-a) reachability re-test runs. **Note (session 21 amendment):** the v1-Cowork-drop conclusion was **superseded** by PR #67 (PLAN-0012 v1 expand) — once OQ-B confirmed Desktop CAN spawn extra MCP servers under UWP sandbox + Lesson #0017 §3 corrected the tab-group routing model + OQ-T3 Option I accepted capability-by-tool-design, Cowork-client became viable under A1 stdio-MCP (Cowork uses the same Desktop-spawned server instance B as Code). The `cowork-network-locus` runbook still stands as the load-bearing evidence that Cowork has no outbound IP path — A1 stdio-MCP doesn't need IP. |
| **STATUS reconcile** (session 19) | [#62](https://github.com/CrayJThiemsert/vero-lite/pull/62) (`ee36ede` → merge `4e3a536`) | **Session 18 + 19 ledger entries added.** Frontmatter + Current Focus + 2 new ledger sub-sections. Brought STATUS current from session 17 → session 19. |

### 2026-05-28 ~06:30 +07 — Session 18 ledger (closed)

Session 18 ran ~3 hours (2026-05-27 evening → 2026-05-28 ~06:30 +07);
**3 PRs merged end-to-end + 1 PR closed without merge + 0 Cowork
rounds + 0 open PRs at session close + 0 new auto-memory lessons
codified**. OQ-A resolution was a single Cray-decision question via
AskUserQuestion (not architectural-review), so no Cowork advisory
round was needed. Cumulative session-18 tests: 612 → 634 (+22 from
`test_wsl_bridge.py`; batch-2 added 0 since it deleted only duplication
already covered).

| Phase | PR / artifact | Change |
|-------|--------------|--------|
| **ADR-0014 OQ-A resolution** | [#58](https://github.com/CrayJThiemsert/vero-lite/pull/58) (`df70f83` → merge `5bf161b`) | **OQ-A "ADR-014 vs PLAN-0012-under-ADR-013" resolved.** Cray ratified PLAN-0012-under-ADR-013 per PLAN-0009 OQ-3 precedent ("no new ADR; mint ADR only if a genuinely architecture-level choice surfaces"). New `docs/adr/0014-WITHDRAWN.md` (50-line tombstone: rationale + 4-step author≠reviewer pipeline citation + backlinks to ADR-013 D1, PLAN-0009 §Out-of-Scope, PR #57, both Cowork advisory handoffs, Lessons #8/#15) replaces the take-3 draft (837 lines). PR #57 closed without merge by Cray at 2026-05-27T10:01:21Z during review; take-3 retained on remote branch `chore/adr-0014-cross-tab-mcp-transport` commit `2fde9eb` for archeology (closure comment on PR #57 cites that SHA). `docs/plans/done/0009-subagent-topology.md` §Out-of-Scope annotated per PR #56 preserve-original-fenced-blockquote-supersedes pattern to re-anchor `vero-bridge` Phase-4 earmark from PLAN-0010 → **PLAN-0012**. |
| **`_wsl_bridge.py` extraction** | [#59](https://github.com/CrayJThiemsert/vero-lite/pull/59) (`59797e0` → merge `d75e446`) | **Rule-of-three closed for named 3 hooks.** New `.claude/hooks/_wsl_bridge.py` (~274 LOC) 6-function API: **Pattern A** (`is_windows_with_wsl`, `wsl_path`, `env_with_wslenv_passthrough`, `bash_argv`) + **Pattern B** (`should_use_wsl_https_bridge`, `http_post_via_wsl_bridge`). Migrated `notification_telegram.py` (Pattern A), `subagentstop_notify.py` (Pattern A), `_sonnet_classifier.py` (Pattern B — removed `_WSL_BRIDGE_SCRIPT` constant + `_should_use_wsl_bridge` + `_http_post_via_wsl_bridge` + unused imports `email.message`/`shutil`/`subprocess`/`sys`). 22 new tests in `tests/handoffs/test_wsl_bridge.py` (fake-subprocess injection — no real `wsl.exe` or network). Old `_wsl_path` tests in `test_subagentstop_notify.py` removed (moved to new file). Net diff: +659 / −292 (−85% LOC in touched hook regions). |
| **Pattern-A batch-2 migration** | [#60](https://github.com/CrayJThiemsert/vero-lite/pull/60) (`48ab90a` → merge `d1f3393`) | **Rule-of-three closed for the bonus 3 Pattern-A sites.** Migrated `stop_continuation.py` (`_ping_telegram`), `pretooluse_loop_detect.py` (`_ping_telegram`), `posttooluse_progress_observer.py` (`_ping_telegram`) to use `bash_argv` + `env_with_wslenv_passthrough` from `_wsl_bridge`. Removed inline `_wsl_path` + `_forwarded_env` + `import shutil` from each. Net diff: +23 / −108 across 3 files (−85% in touched regions). No new tests — deletes only duplication already covered by `test_wsl_bridge.py`. **After this PR, no inline WSL-bridge duplication remains in `.claude/hooks/`** — any future hook needing the bridge imports from `_wsl_bridge.py`. |
| **ADR-014 take 3 (PR #57)** | closed without merge | Take-3 draft (837 lines) opened as PR #57 at session 17 close after Cowork take-2 verification round folded fixes. Cray closed at 2026-05-27T10:01:21Z during review when OQ-A resolution was reached. Closure comment cites PR #58 merge + take-3 archeology branch commit `2fde9eb`. Cowork advisory rounds 1 + 2 (session 16 handoffs) contributed Focus-1 fixes that the take-3 draft folded — context still relevant for future PLAN-0012 drafting per session 18→19 handoff §3 references. |

### 2026-05-27 ~14:50 +07 — Session 17 ledger

| Phase | PR / artifact | Change |
|-------|--------------|--------|
| **PLAN-0011 fix** | [#53](https://github.com/CrayJThiemsert/vero-lite/pull/53) (`17eecc7` → merge `8d421fc`) | **Lesson #15 §4 SHIPPED.** `.claude/hooks/_sonnet_classifier.py` +191 LOC: `_summarize_transcript` + `_render_transcript_turn` + `_extract_content_parts` + `_read_transcript_turns` + `_render_content_block` helpers; `## Recent conversation excerpt` section inserted between framing + raw payload JSON dump in `_build_user_message`. 18 new tests (15 summarizer + 4 build-message regression + 2 AC-4 mock-input assertions in `test_stop_continuation.py` + `test_pretooluse_classifier_dispatch.py`) + 1 gated live-API smoke (`test_classifier_live_smoke.py` + `tests/fixtures/transcript_smoke_d1.jsonl`). Live smoke vs real Sonnet: `decision: dispatch, matched_rows: ["D1"]` PASS. AC-3 reframed → fresh-trigger live re-run deferred (meta-awareness contamination per PR body). |
| **PLAN-0011 closeout** | [#54](https://github.com/CrayJThiemsert/vero-lite/pull/54) (`ec47b32` → merge `38a7407`) | Status `Ready for execution` → `Complete`; added `Shipped:` field linking PR #53 + `8d421fc`; `git mv docs/plans/0011-classifier-transcript-load.md docs/plans/done/`. Per PLAN-0011 §Step 6 final bullet. |
| **PLAN-0010 Phase 4** | [#55](https://github.com/CrayJThiemsert/vero-lite/pull/55) (`e1e0395`) — **OPEN, MERGEABLE/CLEAN** | **2 cross-process race fixes + scheduled-task wiring.** Fix 1: `_archive` FileNotFoundError recovery (race-loser returns `None` = `SKIPPED_IDEMPOTENT`; caller doesn't crash, doesn't write log on top of winner's). Fix 2: `save_failure_state` per-pid tmp path (`path.with_suffix(f".{os.getpid()}.tmp")`). 6 new tests (4 `_archive` deterministic + 1 `_process_one` end-to-end + 1 multiprocessing×2 cross-process). New `~/.claude/scheduled-tasks/loop-dispatcher/SKILL.md` carries the dispatcher prompt; new 162-line `docs/runbooks/loop-dispatcher-scheduled-task.md` documents the Cray-side Desktop UI one-time setup + verification + observability + recovery. Manual smoke: 6 inbox → 0, 4 processed → 8 (`ok=4 skipped_idempotent=2 elapsed_ms=2`). |
| **Docs reconcile** *(this PR)* | `docs/plans/done/0011-*.md` §Out-of-Scope + `docs/lessons/0015-*.md` §4 + this STATUS | **N1/N2 lag from Cowork ADR-0014 take-2 verification.** PLAN-0011 §Out-of-Scope's "writing fix code is out of scope — session 17+ branch" language was preserved verbatim through PR #54 closeout (reflects original Draft state) — now annotated as **factually superseded by PR #53's diff**. Lesson #15 §4 "deferred to follow-up chore PR / PLAN — session 17+" annotated as **SHIPPED in PR #53**; original §4 framing preserved as archeology. STATUS Current Focus + frontmatter rewritten for session 17. |
| **ADR-0014 take 2** *(uncommitted)* | `docs/adr/0014-cross-tab-mcp-transport.md` + `.claude/handoffs/session-16/2026-05-27-1145-cowork-adr0014-advisory-pass.md` + `2026-05-27-1330-cowork-adr0014-take2-verification.md` | **Cowork advisory loop in flight.** Take 1 (685 lines) was lost when a contaminated session was closed; recovered from Claude Desktop session JSONL via `de88e2c7-*.jsonl` Read-tool output. Cowork advisory round 1 (1145 +07) flagged C1 (stale Phase-3 premise, PLAN-0009 actually DONE), C2 (D3 localhost-only feasibility gap, Cowork is cloud VM), C3 (slot inventory wrong), C4 (commit attribution wrong), 3 missing OQs (vero-bridge naming + ADR-vs-PLAN governance; Lesson #15 dependency; Cowork client execution locus). Plan-drafter take 2 (727 lines, 5 OQs blocking, L1 loop-detect halt at 6th Edit). Cowork take-2 verification (1330 +07): Focus-1 (C1-C4 fixes) PASS; Focus-3 surfaced N1 (this docs lag) + N2 (PLAN-0011 internal contradiction); Focus-2 OQ A/B/C dimension refinements; Focus-4 attribution should be ADR-013 OQ-1 not ADR-012 D4.3. **Take 3 follows this docs PR.** |

### 2026-05-27 10:50 +07 — Session 15 + 16 closeout (Code-tab session 16)

| Phase | PR / artifact | Change |
|-------|--------------|--------|
| **Path C step 3** (session 15a) | [#45](https://github.com/CrayJThiemsert/vero-lite/pull/45) (`1a5fd68`) | **Argv contract + WSL bridge for 3 Telegram-emitting hooks** (`pretooluse_loop_detect`, `posttooluse_progress_observer`, `stop_continuation`). Stubs ported from "read stdin (impl)" to "read `$1` argv (real `telegram.sh`)." AFK fail-safe restored. 4 test files updated. |
| **Lesson capture** (session 15a) | [#46](https://github.com/CrayJThiemsert/vero-lite/pull/46) (`6dee4bd`) | **Lesson #14** — argv vs stdin contract drift between impl + test stub. Sibling lesson family; auto-memory `feedback-coding-careful-pre-ship-checklist` derived from this. |
| **Lessons capture** (session 15a) | [#47](https://github.com/CrayJThiemsert/vero-lite/pull/47) (`8440924`) | **Lesson #12** (loop-detect L1 vs governance-doc fillup passes — batch or surgical-reset, don't full-reset) + **Lesson #13** (Claude Desktop process-env cache + secret rotation). Closed 0012/0013 numbering gap. |
| **Path A-pre attempt** (session 15b) | [#48](https://github.com/CrayJThiemsert/vero-lite/pull/48) (`885581a`) | *(SUPERSEDED)* Option 3b — route classifier hooks via `.claude/settings.json` `wsl --cd --exec`. Pilot-tested via WSL bash + PowerShell direct; **didn't survive Claude Code's `cmd /c` spawn** under UNC cwd + stdin piping. Regression caught post-restart. |
| **Path A unblock** (session 15b) | **[#49](https://github.com/CrayJThiemsert/vero-lite/pull/49)** (`168baff`) | **Option 2 WSL bridge for classifier HTTPS.** Reverted #48's settings routing; added bridge **inside** `_sonnet_classifier.py` — Windows Python hook spawns `wsl.exe --exec python3 -c BRIDGE_SCRIPT` subprocess for the HTTPS call only (same proven idiom as PR #45's `notification_telegram`). 6 grep hits in `_sonnet_classifier.py` cover the constant + 2 helpers + 1 branch in `_call_api`. |
| **Smoke 1 PASS** (session 15b/16) | evidence file | **G1 Edit-Accepted-ADR.** Cray triggered Edit on ADR-013 §1 (typo fix); classifier denied with real Sonnet reason "ADR-013 อยู่ในสถานะ Accepted (G1 trigger ใน .claude/autonomy-triggers.md)". **First live evidence the PreToolUse classifier arm works end-to-end under the bridge.** |
| **Smoke 2 BLOCKED + finding** (session 16) | evidence file + Lesson #15 | **D1 Stop dispatch — structural finding.** Two attempts (with + without in-flight Reads in turn 1) both returned classifier `proceed`. Direct in-process diagnostic confirmed `_build_user_message` doesn't read `transcript_path`; Sonnet sees only 5 metadata fields on Stop events. **Lesson #15 codified** — sibling antipattern to Lesson #14 one layer up the stack (test stubs mock `_call_api`, never read what the model receives). |
| **Telegram fail-safe E2E** (session 16) | evidence + Telegram message | **PR #45 end-to-end validated** via manual `plan-drafter` Agent spawn (since auto-dispatch arm blocked by Lesson #15). SubagentStop fired → `subagentstop_notify.py` → wsl.exe bridge → `telegram.sh` → bot `@vero_tg_bot` → Cray's phone at 10:36 +07. Telegram `agent_id=ac7d6aac` matches subagent return value. Full chain live. |
| **ADR-0014 artifact** (session 16) | `docs/adr/0014-cross-tab-mcp-transport.md` | Cross-tab MCP transport ADR — 685 lines, Status `Proposed`, **uncommitted**. Produced by `plan-drafter` subagent; author≠reviewer disclosure flags chicken-and-egg ("the cross-tab MCP transport that would make a Cowork advisory pass cheap is the very thing this ADR proposes"); 5 open questions for Cray + 6 follow-on commits T1–T6. Routing decision deferred to Cray. |
| **Lesson + STATUS** *(this PR)* | `0015-classifier-payload-starvation-stop-events.md` + this section | **Lesson #15 codified.** Auto-memory `feedback_coding_careful_pre_ship_checklist` extended with 5th point (payload semantic content / LLM-integration extension). STATUS Current Focus + ledger updated. |

### Session 16 Path A scenarios — final ledger

| Scenario | Trigger | Verdict | Evidence file |
|---|---|---|---|
| **#4 — G1 Edit Accepted ADR** (Smoke 1) | Cray typo-fix request on ADR-013 §1 | ✅ **PASS** | `scenario4-cray-driven-g1-edit-accepted-adr.md` |
| **#3 — D1 Stop dispatch** (Smoke 2) | Cray ADR-0014 ratification | ❌ **BLOCKED + finding** | `scenario3-cray-driven-d1-stop-dispatch.md` (+ `…-attempt1-failed.md` forensic) |
| **#5 — C2 add dependency** (Smoke 3 bonus) | (not run live — inferred BLOCKED by #3 finding) | ⏸️ **DEFERRED** (re-run post-fix) | `scenario5-cray-driven-c2-add-dependency.md` |
| **Telegram fail-safe (PR #45 E2E)** | Manual `plan-drafter` spawn after Smoke 2 BLOCKED | ✅ **PASS** | covered in `scenario3` §Telegram fail-safe end-to-end validation |

### Deferred queue (session 17 reconciled)

- ~~**Lesson #15 fix — `_build_user_message` transcript-load.**~~ **✅ SHIPPED** in PR #53 / `8d421fc` (session 17). See ledger row above + `docs/plans/done/0011-classifier-transcript-load.md`.
- **ADR-0014 ratification.** **IN FLIGHT** — Cowork advisory rounds 1 + 2 done; plan-drafter take 2 in working tree; Code take-3 edits (folding Cowork take-2 feedback) follows this docs-reconcile PR; then commit + PR + Cray ratifies in review (OQ-A ADR-vs-PLAN governance is the load-bearing decision).
- ~~**PLAN-0010 Phase 4 wiring**~~ **✅ IN PR** #55 (`e1e0395`); 2 dispatcher race fixes + scheduled-task SKILL.md + runbook all landed in chore branch; awaiting Cray green-light merge.
- **`_wsl_bridge.py` extraction.** Rule-of-three threshold hit: `notification_telegram` + `subagentstop_notify` + `_sonnet_classifier` now share the `subprocess.run(["wsl.exe", "--exec", ...])` idiom. Session-17 work #3 queued (~1 hr); not blocking.
- **AC-3/AC-7 fresh-trigger live re-run** (PLAN-0011 follow-up). Per PR #53 body: verbatim Smoke 2/3 from `scenario3-*.md` / `scenario5-*.md` is contaminated by agent meta-awareness (agent reads scenario file → recognizes test trigger → behaves cautiously → classifier sees wrong context). Re-run with a **fresh trigger** (not documented in any tracked file) in a future session; capture Telegram `message_id` + Sonnet verdict; flip evidence files BLOCKED → PASS.

### 2026-05-26 22:30 +07 — Step 6 close (Code-tab session 14)

After session 14 §0 env verify (clean main @ `cbe47b9`; classifier
API key file-source `sk-ant`; `CLAUDE_TIER=code`), opened Code-tab
Step 6 closeout work in 4 sequential commits on a single branch:

| Phase | Commit | Change |
|-------|--------|--------|
| **Phase 1** | `db9bbb4` | **§8.1 verification matrix test mapping.** Added per-AC test-mapping sub-sections to both PLAN-0009 Step 1b §8 (30 cells, 6 ACs) and PLAN-0010 Step 1 §8 (20 cells, 4 ACs). Mapped each (AC, case) coordinate to concrete `tests/handoffs/test_*.py::test_*` / `tests/loop/test_*.py::test_*` paths, with `(L)` tags for primitive-controlled live cells and `(RR)` for uncovered cells flagged as residual risk. Surfaced 3 new residual risks for Phase 1.5: bypassPermissions coverage gap on H2/C4/L1–L4/H1; PLAN-0010 §4 spec drift; cross-process race coverage. |
| **Phase 1.5** | `6573ae7` | **Closed 3 new residual risks** before Phase 2. (a) 3 bypassPermissions × deny regression tests added — `test_bypass_permissions_still_denies_outside_allowlist` (H2), `test_bypass_permissions_still_denies_research_public` (C4), `test_bypass_permissions_still_denies_at_threshold` (L1–L4); H1 N/A (PostToolUse — ADR-013 D2 PreToolUse-deny semantics don't bind). (b) PLAN-0010 §4 amended: parser is order-insensitive (strictly more robust than original split-zip spec); earlier text preserved for archeology. (c) PLAN-0010 §5 new "Cross-process consumer safety" sub-section documents Phase 4 unblock criteria; §8.1 cells + residual lists updated. 441 tests pass (was 438; +3). |
| **Phase 2** | `9d86d13` | **Live AC verification updates.** Phase 2 ran 2 Code-only scenarios + 1 bonus organic trigger. Evidence files in `docs/research/private/step6-live-ac/` (gitignored). **#7 PLAN-0010 lifecycle:** 4 archived messages survive across cowork producer fires; filename embedded claimed-time diverges from mtime by +4–13h — strongest possible live evidence of §2 mtime-authoritative binding. **#3b cross-process race:** 2 dispatcher processes on 1-message inbox → filesystem invariant held (1 in processed, 0 in inbox) + **NEW BUG DISCOVERED** in `save_failure_state` shared-tmp path; Phase 4 unblock criteria expanded from 1 fix to 2 fixes. **Bonus L1 trigger:** L1 loop-detect fired live at threshold=6 during Phase 2 doc thrash on Plan-0010; L2 + L3 captured below-threshold; AC-6 regression live-verified. **Cray-driven scenarios 3/4/5 deferred** (handoff §3) — covered by unit tests + layered defense reasoning. |
| **Phase 3** | `e04f0f0` | **Sign-off with confidence statements.** Added "Sign-off (Step 6, session 14)" section to both plans per Cray verification-rigor directive ("we are confident it does what we intend, not just tests pass"). PLAN-0009: 4 open residuals (2 High, 2 Medium); ~30 cells classified (~3 live + ~15 unit + ~10 deferred + ~2 RR). PLAN-0010: 6 open residuals (2 High, 4 Medium); ~20 cells classified (~5 live + ~12 unit + ~3 RR). Overall verdict: both plans meet verification-rigor bar; ready to archive pending Cray PR-merge ratification. |
| **Phase 4** | *(this commit)* | **Archive + STATUS + handoff.** `git mv` 4 plan files to `docs/plans/done/`: `0009-subagent-topology.md`, `0009-step1b-contract-design.md`, `0009-step4-dispatch-protocol.md`, `0010-step1-message-schema.md`. STATUS updated; session-14 → session-15 handoff written. Close PR ready to open. |

### Phase 3 Step 6 sub-phase ledger (now COMPLETE)

| Sub-phase | Commit | Status |
|---|---|---|
| Phase 1 — §8.1 matrix mapping | `db9bbb4` | ✅ session 14 |
| Phase 1.5 — close 3 new residuals | `6573ae7` | ✅ session 14 |
| Phase 2 — live AC verification | `9d86d13` | ✅ session 14 (2 scenarios + L1 bonus + 1 bug surfaced) |
| Phase 3 — sign-off | `e04f0f0` | ✅ session 14 |
| Phase 4 — archive + STATUS + handoff + PR | *(this commit)* | ✅ session 14 |

**Cumulative session 14 impact:** +325 LOC across 5 commits (3 new tests + 2 plan doc sign-offs + 4 archive moves + STATUS + handoff). Suite: **441 passing**, 1 skipped (live API gated).

### Plans archived this session

- [`docs/plans/done/0009-subagent-topology.md`](plans/done/0009-subagent-topology.md) — Phase 3 parent
- [`docs/plans/done/0009-step1b-contract-design.md`](plans/done/0009-step1b-contract-design.md) — subagent contracts (composed G5, H2, SubagentStop)
- [`docs/plans/done/0009-step4-dispatch-protocol.md`](plans/done/0009-step4-dispatch-protocol.md) — dispatch protocol
- [`docs/plans/done/0010-step1-message-schema.md`](plans/done/0010-step1-message-schema.md) — Phase 3.5 message schema + lifecycle

**Still active:** `docs/plans/0010-phase3-5-scheduled-task-autonomy-loop.md` (parent — Phase 4 scheduled-task wiring remains).

### Phase 4 unblock criteria for scheduled-task wiring (documented in archived PLAN-0010 §5)

When Cray queues PLAN-0010 Phase 4 (Code Desktop scheduled task), **2 dispatcher fixes must land first** (~30–45 min, mechanical):

1. **`_archive` FileNotFoundError recovery** (~5 LOC at `tools/loop/dispatcher.py:421-426` + 1 multiprocessing test) — original Phase 1 finding
2. **`save_failure_state` per-process unique tmp path** (~1 LOC at line 216 + 1 test) — **discovered live in Phase 2 #3b cross-process race scenario**

### Cray-driven AC scenarios pending (handoff scenarios 3/4/5)

Non-blocking; can run anytime post-merge:

- **Scenario 3 — AC-5 in-harness end-to-end:** Cray engineers a Stop event the classifier matches a D-row on → observes spawn → draft → Telegram
- **Scenario 4 — AC-3 positive G1:** Cray attempts Edit on accepted ADR → classifier pause/dispatch → deny
- **Scenario 5 — AC-3 positive G2:** Cray attempts Write to fresh `docs/plans/0011-*.md` → classifier dispatch → deny with spawn-redirect

If any scenario surfaces a new bug, recovery = post-merge hardening PR (same shape as Phase 1.5 mini-iteration). Per Cray's session-14 Option-A choice ("close now, iterate on findings").

### Telegram ping investigation (non-blocking session 15 follow-up)

L1 loop-detect fired live during session 14 Phase 2; `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` confirmed SET in WSL env at fire time. Cray reports NOT receiving Telegram ping. Possible causes: telegram.sh ran but failed silently; bot blocked; network issue; missed message. Debug via direct invocation of `tools/notify/telegram.sh` with a test payload; non-blocking for Step 6 close.

### 2026-05-26 19:45 +07 — Step 5c-1 + 5c-2 shipped (Code-tab)

After session 13 §0 env verify (clean main @ `3776480`; classifier
API key file-source `sk-ant`; `CLAUDE_TIER=code`), opened Code-tab
Step 5c work in two PRs:

| PR | Commit | Change |
|----|--------|--------|
| **#41** | `830c3a7` | **Step 5c-1 — Stop-side auto-handoff dispatch.** Extended `_sonnet_classifier.py` with 3rd decision value `dispatch` (+ `DISPATCH_ALLOWED_SUBAGENTS={"plan-drafter"}` + `DISPATCH_ALLOWED_ARTIFACT_KINDS={"adr","plan"}` + `_validate_dispatch_metadata` strict schema). Extended `stop_continuation.py` with `_build_dispatch_instruction` helper that emits `block` with Step 4 §1 R4 routing + §5 budget reminder template + override clause. Added "Auto-handoff triggers" section with D1/D2 rows to `.claude/autonomy-triggers.md`. 30 new tests (16 classifier dispatch + 14 stop_continuation dispatch arm). |
| **#42** | `d4e4dc4` | **Step 5c-2 — PreToolUse classifier dispatch for G1/G2 (PLAN-0008 carry-over closed).** New `.claude/hooks/pretooluse_classifier_dispatch.py` (~315 LOC) with cheap deterministic pre-filter (path pattern + on-disk Status read defeats spoofing) → invoke classifier only on hit → map proceed/pause/dispatch to allow/deny/deny-with-spawn-redirect. Also made `_build_user_message` event-agnostic (was hardcoded "Stop event"). 34 new tests (15 pre-filter unit + 16 in-process decision mapping + 4 e2e subprocess). |

### Phase 3 Step 5 sub-step ledger (now COMPLETE)

| Sub-step | PR | Commit | Status |
|---|---|---|---|
| 5a — composed G5 4-case identity gate | [#38](https://github.com/CrayJThiemsert/vero-lite/pull/38) | `f1d440e` | ✅ session 12 |
| 5b — SubagentStop Telegram notify | [#39](https://github.com/CrayJThiemsert/vero-lite/pull/39) | `79b921d` | ✅ session 12 |
| 5c-1 — Stop-side auto-handoff dispatch | [#41](https://github.com/CrayJThiemsert/vero-lite/pull/41) | `830c3a7` | ✅ session 13 |
| 5c-2 — PreToolUse classifier dispatch (G1/G2) | [#42](https://github.com/CrayJThiemsert/vero-lite/pull/42) | `d4e4dc4` | ✅ session 13 |

**Cumulative impact:** ~1.9k LOC + 64 new tests across 4 PRs covering
the entire Step 5 surface. Phase 2 + Phase 3 classifier surfaces now
unified (3-decision contract `proceed | pause | dispatch` used by both
Stop hook + PreToolUse hook). Phase 1 deterministic G5 preserved +
extended (composed 4-case identity). SubagentStop wired to Telegram
for AC-5 in-harness arm.

### Deferred to session 14 — Step 6 (combined closeout)

**Half (a) — unit-test verification matrix fill-in (Code-driven):**
- PLAN-0009 §Step 1b §8 — 30-cell matrix (AC-1/2/3/4/5/6 × happy/boundary/fail-closed/adversarial/concurrency). Most rows already have unit tests in PRs #30 (`plan-drafter` H2) + #38 (composed G5) + #39 (SubagentStop notify) + #41 (Stop dispatch arm) + #42 (PreToolUse dispatch arm). Step 6 maps each row to its specific test name + flags any uncovered row as residual risk per Cray verification-rigor directive ("we are confident it does what we intend").
- PLAN-0010 §Step 1 §8 — 20-cell matrix. PRs #34 (parser) + #35 (dispatcher) cover most rows. Step 6 adds live producer evidence (already accumulating: `loop/processed/` has 2 archived messages from session 13 fires).

**Half (b) — live AC verification matrix (some Cray-driven):**
- Real classifier API call on a Stop event matching D1/D2 → spawn `plan-drafter` end-to-end → draft → Telegram fires (SubagentStop) → main agent commits via PR (AC-5 full chain)
- Real classifier API call on a PreToolUse Edit of an Accepted ADR → deny with G1 citation (AC-3 negative; PreToolUse arm of 5c-2)
- Real classifier API call on a PreToolUse Write of fresh PLAN-NNNN → deny with G2 + dispatch redirect (AC-3 + AC-5)
- bypassPermissions × subagent commit attempt → still denied (AC-6 negative)
- 18-case bypass-immune G5 matrix re-run with subagent rows (AC-6)

**Closeout output:** STATUS update + final session-14 handoff +
`git mv docs/plans/0009-*.md docs/plans/done/` archive step (Phase 3
+ Phase 3.5 jointly close once both verification matrices sign off).

### Awaiting Cray Cowork-tab action (non-blocking)

During session 13, the Cowork producer (`phase35-smoke-cowork-heartbeat`)
fired twice:

| Fire time | Filename | Landed where | Status |
|---|---|---|---|
| ~18:05 +07 | `cowork-smoke-heartbeat-20260526T070000Z.msg.md` | `loop/inbox/` ✓ | dispatched + archived |
| ~19:05 +07 | `cowork-smoke-heartbeat-20260526T120000Z.msg.md` | **repo root** ✗ | manually moved to inbox; idempotent-skip on dispatch (matching prior archive) |

The 18:05 fire landed correctly; the 19:05 fire landed at repo root.
Pattern suggests intermittent producer config drift, possibly
cwd-resolution-related. The fix is a Cowork-tab editor edit to the
producer prompt — Code Desktop cannot reach Cowork's task config per
K-1/K-2 boundary. Surfaced for Cray review; non-blocking (dispatcher
+ manual move both handled the recovery).

### Session-13 → session-14 handoff document

Full handoff at
[`.claude/handoffs/session-13/2026-05-26-1945-code-session14-kickoff.md`](.claude/handoffs/session-13/2026-05-26-1945-code-session14-kickoff.md)
(gitignored local working note per CLAUDE.md §11). Covers §0 env verify,
§1 state of main, §2 complete/queued, §3 Step 6 plan (half a + half b),
§4 operational notes, §5 deferred items (incl Cowork producer path bug),
§6 first-30-min plan, §7 reference files, §8 predecessor handoff trail.

---

### Prior — Session 12 mega-batch close (demoted for archeology)

**Session 12 mega-batch close — 13 PRs landed (#29–#40; #40 in flight).
Phase 3 Steps 2/3/4 + PLAN-0010 Steps 1+2+3 all DONE; PLAN-0010 cycle
PROVEN LIVE; Step 5a (composed G5) + 5b (SubagentStop notify) DONE.
Step 5c (auto-handoff) + Step 6 (verification) deferred to session 13.
OQ-9.2 RESOLVED.**

### 2026-05-26 17:00 +07 — Step 5a + 5b shipped (Code-tab)

After the OQ-9.2 closeout PR (#37) merged, this session immediately
opened the Code-tab Step 5 work since Cowork producer was now firing
hourly and the consumer side was proven. Split Step 5 into 3
sub-pieces; shipped the first 2:

| PR | Commit | Change |
|----|--------|--------|
| **#38** | `f1d440e` | **Step 5a — composed G5 4-case identity gate.** Extended `.claude/hooks/pretooluse_git_deny.py` from tier-only check to `allow_commit = (agent_id is None) and (CLAUDE_TIER == "code")`. 28/28 tests (16 existing preserved + 12 new subagent cases). Subagent branch checked FIRST so deny reason cites subagent identity, not inherited tier. Bypass-immune (AC-6 negative test). |
| **#39** | `a1f5a71` | **Step 5b — `SubagentStop` Telegram notification.** New `.claude/hooks/subagentstop_notify.py` (~140 lines) + `.claude/settings.json` wiring under new `SubagentStop` event with matcher `"plan-drafter"`. 15/15 tests. Frozenset allowlist (immutable) + defense-in-depth filter at hook layer (even if matcher loosened, hook still rejects non-allowlisted types). Cross-platform Telegram bridge mirroring `notification_telegram.py` pattern. |

### Deferred to session 13 — Step 5c + Step 6

**Step 5c — Auto-handoff dispatch** (largest piece, Phase 2 invasive):
- Extend `.claude/hooks/stop_continuation.py` + `.claude/hooks/_sonnet_classifier.py` to classify "governance-drafting need" → spawn `plan-drafter` via Step 4 §1 R4 routing instead of pausing for Cray paste
- Add the PreToolUse classifier dispatch arm for G1/G2 rows (PLAN-0008 carry-over)
- Closes OQ-D's in-harness arm

**Step 6 — Combined closeout** (after 5c):
- Live AC verification matrices for PLAN-0009 (AC-3/AC-4/AC-5/AC-6 18-case bypass-immune G5) + PLAN-0010 (AC-Step1-2/3/4 with live producer evidence)
- Sign-off on residual risks
- Final session 13 → 14+ handoff (or close Phase 3 + 3.5 entirely)

### Why pause here (Cray-routed via AskUserQuestion)

- 12 PRs of feature work + 2 closeout chore PRs is already mega-batch
- Step 5c modifies Phase 2 logic — riskier than pure new-hook work, deserves fresh-context review in session 13
- 5a + 5b independently usable: composed G5 already gates subagent commits; SubagentStop notification already fires for plan-drafter completions
- Cowork producer is self-sustaining (hourly); no time pressure to ship 5c immediately

### Session-12 → session-13 handoff document

Full handoff at [`.claude/handoffs/session-12/2026-05-26-1730-code-session13-kickoff-v2.md`](.claude/handoffs/session-12/2026-05-26-1730-code-session13-kickoff-v2.md) (gitignored local working note per CLAUDE.md §11; supersedes the earlier `1530` kickoff). Covers §0 env verify, §1 state of main, §2 complete/in-flight/queued, §3 path A (Step 5c) + path B (Step 6) details, §4 operational notes, §5 deferred items, §6 first-30-min plan, §7 out-of-scope, §8 reference files priority.

### Session 12 full PR ledger (13 PRs)

| # | PR | Commit | Topic |
|---|----|--------|-------|
| 1 | [#29](https://github.com/CrayJThiemsert/vero-lite/pull/29) | `32adee3` | PLAN-0009 Step 2 — `explore-research` subagent |
| 2 | [#30](https://github.com/CrayJThiemsert/vero-lite/pull/30) | `6af33d8` | PLAN-0009 Step 3 — `plan-drafter` + H2 hook + tests |
| 3 | [#31](https://github.com/CrayJThiemsert/vero-lite/pull/31) | `b952ad9` | PLAN-0010 Step 1 — schema + lifecycle + `loop/` skeleton |
| 4 | [#32](https://github.com/CrayJThiemsert/vero-lite/pull/32) | `48c9df9` | Closeout #1 — Lesson #11 + CLAUDE.md §7 amendment |
| 5 | [#33](https://github.com/CrayJThiemsert/vero-lite/pull/33) | `34cb50d` | PLAN-0009 Step 4 — dispatch protocol (doc-only) |
| 6 | [#34](https://github.com/CrayJThiemsert/vero-lite/pull/34) | `b8df44b` | PLAN-0010 Step 3a — schema parser (38 tests) |
| 7 | [#35](https://github.com/CrayJThiemsert/vero-lite/pull/35) | `a6baf05` | PLAN-0010 Step 3b — dispatcher (34 tests) |
| 8 | [#36](https://github.com/CrayJThiemsert/vero-lite/pull/36) | `b2083f7` | Closeout #2 — STATUS + session-13 handoff (initial) |
| 9 | [#37](https://github.com/CrayJThiemsert/vero-lite/pull/37) | `b29d789` | Lesson #9 OQ-9.2 RESOLVED + Cowork live AC pass |
| 10 | [#38](https://github.com/CrayJThiemsert/vero-lite/pull/38) | `f1d440e` | PLAN-0009 Step 5a — composed G5 |
| 11 | [#39](https://github.com/CrayJThiemsert/vero-lite/pull/39) | `a1f5a71` | PLAN-0009 Step 5b — SubagentStop notify |
| 12 | **#40** (this) | — | Closeout #3 — STATUS + session-13 handoff v2 |
| — | (also #32 + #36) | — | (chore closeouts counted above; total 13 PRs) |

(Note: PR count of 13 includes #29–#40 = 12 plus #37 — see ledger for the exact mapping; the "13" framing counts each merged PR including the 3 closeout chore PRs.)

### Awaiting Cray adjudication (still non-blocking)

SD-Step1-1 / SD-Step1-2 / SD-Step1-3 / SD-Step1-4. Code-recommended defaults are working in production (parser PR #34 + dispatcher PR #35 + live evidence from Cowork producer).

### Smoke scheduled tasks

**Active** — hourly cadence. Next fire around 18:04 +07 (typical XX:04 offset observed in history). Self-sustaining; no manual intervention needed.

---

### Prior — pre-Step-5 (session 12 mid-batch)

(Demoted; preserved for archeology.)

**Session 12 mega-batch — 9 PRs landed (#29–#37; #37 in flight).
Phase 3 Steps 2/3/4 + PLAN-0010 Steps 1+2+3 all DONE; PLAN-0010
end-to-end producer→consumer→archive cycle PROVEN LIVE 2026-05-26
16:13 Bangkok. OQ-9.2 RESOLVED (no Sonnet floor on Cowork). Only
Phase 3 Step 5 + combined Step 6 remain.**

### 2026-05-26 16:13 +07 — Live AC partial pass (Cowork Step 2)

Cray drove PLAN-0010 Step 2 in Cowork tab during the session-12 pause
(per the AskUserQuestion routing). Producer task
`phase35-smoke-cowork-heartbeat` was edited per the session-12 v3
prompt spec (Haiku 4.5 + Act-without-asking + Hourly + Write-only,
Connectors panel empty) and resumed Active. First fire produced:

```
loop/inbox/cowork-smoke-heartbeat-20260526T120000Z.msg.md  (519 bytes)
```

Schema validation (Code-side manual `python -m tools.loop.dispatcher`):

```
scan_cycle: ok=1 parse_failed=0 expired=0 dispatch_failed=0 poison=0 skipped_idempotent=0 pruned=0 elapsed_ms=1
```

Atomic mv lifecycle confirmed: `inbox/` empty (only `.gitkeep`),
`processed/` contains the archived message with preserved mtime.

**Drift evidence (consistent with prior smoke F2-F4):**
- `claimed_time` in frontmatter: `2026-05-26T12:00:00Z` (= 19:00 Bangkok)
- fs `mtime` actual: 16:13 Bangkok = 09:13 UTC
- **Drift: +2h47m positive** (agent's clock perception ahead of reality)
- **Does not affect dispatching** — the parser accepts the claimed_time
  as informational; the dispatcher orders by fs mtime per Step 1 §2
  binding. This is *exactly* why the design made mtime authoritative.
  Live-validated.

**OQ-9.2 RESOLVED (this PR updates Lesson #9 §7):**
- Toggling Cowork model Haiku 4.5 ↔ Sonnet 4.6 in the task editor
  leaves "Act without asking" mode available on both
- No Sonnet floor on Cowork — Haiku is fine for sustained scheduled
  task autonomy (separate from Code Auto mode's Sonnet-classifier
  floor)
- PLAN-0010 §Step 2 Haiku 4.5 spec validated

### What remains before Phase 3 + 3.5 are fully closed

| Item | Owner | Blocks |
|---|---|---|
| Phase 3 Step 5 — composed G5 + `SubagentStop` + auto-handoff wiring | Code-tab (session 12 continuing) | Step 6 |
| Combined Step 6 — live AC verification matrices + sign-off | Code-tab (after Step 5) | Phase 3 + 3.5 closeout |
| Cray adjudication SD-Step1-1…4 | Cray review | nothing (Code-recommended defaults already shipped + working live) |

---

### Session 12 batch recap (prior — historical reference)

8 prior PRs (before this OQ-9.2/STATUS chore) — see [PR #36 closeout](https://github.com/CrayJThiemsert/vero-lite/pull/36) for the full per-PR table. Pre-Cowork-validation context preserved below.

**Session 12 mega-batch close (2026-05-26) — 8 PRs landed (#29–#36);
both Phase 3 (mid-flight Steps 2/3/4 DONE) and PLAN-0010 (Steps 1
+ 3 Code-side DONE) advanced significantly in one session per Cray's
sequential-#1→#5 directive. Cowork-side Step 2 of PLAN-0010 was the
only remaining unblock for live AC verification.**

Eight PRs merged to main this session, in execution order. PRs #29–#32
were the session-11 kickoff trio + closeout; PRs #33–#36 were the
sequential-#1→#5 follow-on directive (#1 Phase 3 Step 4, #2 PLAN-0010
Step 3 split as #34+#35, and this closeout).

### Session-11-kickoff trio + Lesson capture (PRs #29–#32)

| PR | Commit | Change |
|----|--------|--------|
| **#29** | `32adee3` | **PLAN-0009 Phase 3 Step 2** — `.claude/agents/explore-research.md` (144 lines). Read-only subagent (Read/Grep/Glob/WebFetch; Write/Edit/Bash/Agent denied). |
| **#30** | `6af33d8` | **PLAN-0009 Phase 3 Step 3** — `plan-drafter` subagent + new H2 hook + 30/30 tests. H2 is **fail-CLOSED** (differs from C4 fail-OPEN; load-bearing for AC-3 + ADR-013 D2). |
| **#31** | `b952ad9` | **PLAN-0010 Step 1** — 308-line design doc + `loop/` skeleton + `.gitignore` entries. SD-3 resolved as `loop/` at repo top. 4 sub-decisions (SD-Step1-1…4) surfaced for Cray. |
| **#32** | `48c9df9` | **Closeout #1**: Lesson #11 (`gh pr` body-file backtick trap) + CLAUDE.md §7 "PR / issue / release bodies" amendment + STATUS update. |

### Sequential-#1→#5 follow-on (PRs #33–#36)

| PR | Commit | Change |
|----|--------|--------|
| **#33** | `34cb50d` | **#1 = PLAN-0009 Phase 3 Step 4** — `docs/plans/0009-step4-dispatch-protocol.md` (239 lines). Spawn-vs-inline decision procedure + 6-case routing matrix (3 spawn + 3 inline, AC-4 ≥ 4-cases bar satisfied) + context-propagation discipline + caller-side result reduction (observability rule: flag > 4k token replies) + boundary-enforcement table + budget-reminder injection templates. Doc-only; mirrors Step 1b pattern. |
| **#34** | `b8df44b` | **#2a = PLAN-0010 Step 3 parser** — `tools/loop/_schema.py` + `tools/loop/__init__.py` + 38/38 tests. Mirrors `tools/handoffs/_schema.py` discipline (stdlib YAML subset, dataclass-typed output). Fail-closed on schema_version!=1, time_authority!="mtime", unknown message_type, producer_id/filename mismatch. Section-ordering-insensitive parser (strictly more robust than Step 1 §4 hint). |
| **#35** | `a6baf05` | **#2b = PLAN-0010 Step 3 dispatcher** — `tools/loop/dispatcher.py` + 34/34 tests. End-to-end consumer loop: scan → parse → dispatch → atomically archive → prune. Poison detection (default 3 consecutive failures → archive + alert + clear from inbox) is the dispatcher-local analog of PLAN-0008 L3/L4 (different state mechanism: dispatcher runs as standalone process tree, not in harness). Same-fs check at startup (Step 1 §8 residual risk #1). Telegram alert via existing `tools/notify/telegram.sh`; graceful no-op when env unset. CLI: `python -m tools.loop.dispatcher`. |
| **#36** | (this PR) | **Closeout #2** = STATUS update + session-12 → session-13 handoff. |

### What is now usable end-to-end (Code-side)

- `explore-research` + `plan-drafter` subagent files are on disk; `claude /agents` should list both after merge
- H2 hook enforces `plan-drafter` write-path allowlist (30/30 tests)
- Dispatch protocol is documented for the main Code agent to follow when interacting with either subagent
- Consumer loop (`tools/loop/dispatcher.py`) is fully implemented + tested — it just needs a real producer feeding `loop/inbox/`

### What is NOT yet usable end-to-end

- **PLAN-0010 Step 2 (Cowork producer)** — Cray-tab work; producer prompt + scheduled-task setup must happen in Cowork. Until producer messages exist, the dispatcher idles (and that idling is the AC-Step1-2 "empty inbox no-op" path, which already passes a unit test, but live evidence needs real producer fires).
- **Phase 3 Step 5 (composed G5 + `SubagentStop` wiring)** — Code-tab work; extends `pretooluse_git_deny.py` for the 4-case identity gate (Step 1b §1) and wires `subagentstop_notify.py` for Cray Telegram alerts on `plan-drafter` completion (Step 1b §5). Until Step 5 lands, subagent commit-deny relies on `disallowedTools=[Bash]` only (sufficient because no Bash = no git reach, but G5 extension is the defense-in-depth deliverable).
- **Phase 3 Step 6 + PLAN-0010 Step 6 verification** — both need Steps 2 + 5 first.

### Mid-session lesson captured

**Lesson #11** (PR #32) — `gh pr create --body "$(cat /tmp/pr.md)"` corrupted PR #29's body via bash backtick command substitution; fix is `--body-file PATH`. CLAUDE.md §7 amended. From PR #30 onward all PRs used `--body-file` correctly.

### Next path forward (cross-session)

**Cray-side next (Cowork tab):** PLAN-0010 Step 2 producer setup.

**Code-tab session 13 next:** Phase 3 Step 5 (G5 extension + `SubagentStop`) — does NOT block on Cowork; can ship in parallel with Cray's Step 2 work.

**Combined Step 6 closeout (later):** runs once Step 2 + Step 5 both land — live-verify the AC matrices of both arcs against real producer messages + real subagent dispatches.

### Awaiting Cray adjudication

SD-Step1-1 / SD-Step1-2 / SD-Step1-3 / SD-Step1-4 (PLAN-0010 Step 1 sub-decisions). The parser + dispatcher were built against the Code-recommended defaults; any flip would be a small `chore(loop):` PR to `docs/plans/0010-step1-message-schema.md` + a corresponding adjustment if it touches behavior (only SD-Step1-1 nonce format would; the others are policy values).

### Smoke scheduled tasks

Still **Paused** (same status as session 11 closeout). PLAN-0010 Step 2 work in Cowork will resume the producer task; the consumer dispatcher then has live data.

### Session-12 → session-13 handoff document

Full handoff at [`.claude/handoffs/session-12/2026-05-26-1530-code-session13-kickoff.md`](.claude/handoffs/session-12/2026-05-26-1530-code-session13-kickoff.md).

**Next action:** Cowork (Cray-side) + Code-tab session 13 (Step 5). Both are unblocked and parallel-safe.

---

**Prior — Session 11 productive close (2026-05-26) — 4 PRs landed
(#24/#25/#26/#27); PLAN-0009 Step 1b DONE + PLAN-0010 Ready for
execution + CLAUDE.md §7 PR-only rule codified + Lesson #10 captured;
Phase 3 Step 2 unblocked.**

Four PRs merged to main this session, chained:

| PR | Commit | Change |
|----|--------|--------|
| **#24** | `b5d2489` | PLAN-0010 (Phase 3.5 scheduled-task autonomy loop) — Cowork-drafted under ADR-009 D1 interim; Code-R2-reviewed; Cray ratified SD-1=(b) smoke regression / SD-2=parallel / SD-3=Code-picks-loop-root → Status Draft→Ready for execution |
| **#25** | `8171927` | STATUS update after PR #24 (separate PR per established pattern at the time) |
| **#26** | `5cfce0e` | **CLAUDE.md §7 amendment** — `main` is "protected — no direct push, no exceptions"; new Workflow line ("all commits via PR including single-file `docs(status):` updates"); new Commit + push hygiene line ("never chain commit && push when targeting main"). **Lesson #10** (`docs/lessons/0010-classifier-blocks-direct-push-to-main.md`) — captures the Auto-mode classifier denial that triggered the rule, the chain-rejection footgun, and the 2 rejected alternatives (broad permission rule = unscoped guard relaxation; ask-per-occurrence = accumulating friction). Cray ratified Option 1 (PR-everything) on 2026-05-26. **This very STATUS update is the 3rd test of the new rule** (PRs #25, #27, and this one all PR-flowed STATUS) — rule operates correctly |
| **#27** | `06f8296` | **PLAN-0009 Step 1b — subagent contract design** (`docs/plans/0009-step1b-contract-design.md`, 333 lines, 9 sections). Composed G5 4-case identity gate (§1, shared with PLAN-0010 AC-4) + custom subagent names `explore-research` / `plan-drafter` (§2, avoids built-in shadowing) + per-subagent contracts (§3/§4) + hook architecture (§5: G5 extension + new H2 + `SubagentStop` notification) + result-reduction contract (§6) + state-schema touch decision (§7=omit) + 30-cell verification matrix (§8) + 4 named residual risks + Step 2–6 consumption map (§9). Cray ratified 5 contract decisions (SD1b-1…SD1b-5) — all = Code recommendations |

**Identity unification — final design (composed G5 check, shared
PLAN-0009 §1 + PLAN-0010 AC-4):**

```python
allow_commit = (agent_id is None) and (CLAUDE_TIER == "code")
```

Four cases resolved by one check: main interactive ✅ / main scheduled ✅
(Phase 3.5) / Plan/Explore subagent ❌ (Phase 3) / Cowork ❌. This is the
load-bearing safety primitive Phase 3 + Phase 3.5 both rely on.

**Three execution paths now open (parallel-safe — they don't
interfere; Cray picks priority next session):**

1. **Phase 3 Step 2** — write `.claude/agents/explore-research.md` per Step 1b §3 contract (read-only research subagent, `tools: Read/Grep/Glob/WebFetch`, `maxTurns: 50`, `model: inherit`). Single-session scope.
2. **Phase 3 Step 3** — write `.claude/agents/plan-drafter.md` + new H2 hook `.claude/hooks/pretooluse_plan_subagent_write_deny.py` per Step 1b §4 + §5. Single-session scope. Depends on §5 hook spec (in Step 1b) but not on Step 2's subagent.
3. **PLAN-0010 Step 1 execution** — message schema + lifecycle (incl SD-3 loop-root path choice). Multi-session arc like Phase 2. Independent of Phase 3.

Phase 3 Step 4 (dispatch protocol) requires Steps 2+3 first; Phase 3
Step 5 (auto-handoff + G5 extension + `SubagentStop` notification)
requires Steps 2+3+4; Phase 3 Step 6 (tests + live AC + closeout)
requires all prior steps.

**Smoke scheduled tasks remain Paused.** Safe to resume any time
PLAN-0010 Step 6 verification needs live data; cleanup deferred until
execution captures findings + Cray approves teardown (per session-11
kickoff §5.4 OQ list).

**Next action:** Cray picks priority (Phase 3 Step 2, Phase 3 Step 3,
PLAN-0010 Step 1 — any one, any combination in separate sessions).
No external dependencies. Both Phase 3 + Phase 3.5 unblocked.

---

**Prior — PR #24 merged (`b5d2489`) — PLAN-0010 (Phase 3.5
scheduled-task autonomy loop) Ready for execution; two execution paths
now open in parallel.**

Cowork drafted PLAN-0010 under interim ADR-009 D1 authority (Tier-1
governance authoring, Claude Sonnet 4.6 in Cowork tab — dispatch
`.claude/handoffs/session-10/2026-05-26-1020-code-plan0010-cowork-dispatch.md`;
completion `.claude/handoffs/session-10/2026-05-26-1100-cowork-plan0010-draft-completion.md`).
Code R2-reviewed against the dispatch contract + session-11 kickoff §3
/ §5 caveats; all citations resolve (ADR-009 D1/D2, ADR-013 D1/D2/D5,
ADR-012 D4.3, PLAN-0007/0008/0009, Lesson #8/#9); composed G5 4-case
identity table encoded at AC-4 + Step 3; smoke caveats (filesystem
`mtime` as authoritative fire-time, off-peak Bangkok scheduling guard)
folded into Step 1 + Step 2 + Step 5 + Step 6; Verification ships full
case-coverage matrix (happy / boundary / fail-closed / adversarial /
concurrency) per Cray verification-rigor directive.

**Cray ratified all three Cowork-surfaced decisions 2026-05-26
(in PR #24):**

- **SD-1 = (b) smoke regression** as Phase 3.5 first-ship use case.
  Rationale: directly extends the smoke scaffold (currently Paused;
  resumable), exercises full producer→consumer→alert path, output
  (a reliability number) is the cheapest signal that the loop itself
  is healthy before any higher-value workload rides on it. Candidates
  (a) hourly STATUS digest / (c) governance reminder / (d) deferred-OQ
  rotation all deferred beyond Phase 3.5.
- **SD-2 = parallel** with PLAN-0009 Phase 3 execution. Resolves the
  Phase 3 Step 1b sequencing question carried in session-11 kickoff §4
  — Step 1b (subagent topology contract design) may proceed in parallel
  with PLAN-0010 execution without blocking. The two design spaces
  overlap only at the Step 5 use-case integration layer (deferred
  to "after Phase 3 lands"), so independent progress is safe; identity
  gate composes cleanly with subagents when they arrive.
- **SD-3 = Code picks loop root path** at Step 1 execution (e.g.
  `loop/` at repo top vs `tools/loop/` data dir vs other). K-2 +
  worktree constraints from Step 1 binding regardless.

**Provenance + integrity:**

| Item | Result |
|------|--------|
| PR #24 | https://github.com/CrayJThiemsert/vero-lite/pull/24 — merged via merge commit `b5d2489` |
| Plan commit | `daaa394` — 1 file, 398 insertions; `docs(plans):` Conventional Commits; AI-assistance noted in body (NOT `Co-Authored-By` per CLAUDE.md §7) |
| Pre-commit | detect-secrets passed; ruff/mypy/YAML skipped (no code files in PR) |
| K-1 validator gap | Closed in-process — `validate_handoff.py` green on Cowork completion handoff before commit |
| Author≠reviewer (ADR-012 D4.3) | INTACT — drafter (Cowork) distinct from outline originator (Code dispatch + Cray smoke GO); R2 review = independent check |

**Two execution paths now open in parallel (per ratified SD-2):**

1. **PLAN-0010 execution path** — Step 1 (message schema + lifecycle,
   incl SD-3 loop-root path choice). Will be a multi-session arc like
   Phase 2 was. AC-1…AC-6 + 4 named residual risks all live.
2. **PLAN-0009 Step 1b path** — subagent topology contract design,
   informed by Step 1a survey
   (`docs/research/private/2026-05-25-subagent-primitive-survey.md`,
   8/8 high-confidence answers; key bonus primitives — `isolation`,
   `maxTurns`, `SubagentStart/Stop` hooks, transcript path,
   Plan/Explore name-reservation, result-reduction caveat — all noted
   in session-11 kickoff §5.2 for fold-in).

**Smoke scheduled tasks (Paused):** still safe to resume any time if
PLAN-0010 Step 6 verification needs live data; cleanup deferred until
execution captures findings + Cray approves teardown (per session-11
kickoff §5.4 OQ list).

**Next action:** Cray picks which of the 2 paths to open first next
session (or both in parallel sessions — they don't interfere). Both
are unblocked. No external dependencies in flight.

---

**Prior — Phase 3.5 smoke verdict = GO (early, Cray-ratified
2026-05-26T10:10 +07).** Smoke ran ~18h wall-clock / ~8h awake-time
(observation cut short of nominal 24h plan because all 5 load-bearing
questions answered with high confidence + 2 minor caveats characterized,
per Cray's pragmatic call: "ถ้าเกิด Extra data หลังจากเรา GO ก็น่าจะ
เป็นอะไรที่เราช่วยกันแก้ไขได้").

**Data summary:**

| Side | Runs | Awake-reliability | Notes |
|------|------|-------------------|-------|
| Code Desktop scheduled task (`phase35-smoke-code-reader`, Sonnet 4.6 + Auto) | 8 of 8 expected during ~8h awake | **100%** | Stable `tier=code` across all runs; `bash=ok` all runs; clean ~10h overnight sleep → 1 catch-up run on wake (per Anthropic harness "catch-up latest missed" semantic, live-verified) |
| Cowork scheduled task (`phase35-smoke-cowork-heartbeat`, Haiku 4.5 + Act-without-asking, Write-only) | 11+ successful of 13+ visible attempts (per Cowork history page) | **~85%** | 2 explicit "Skipped" entries (one initial-setup, one sleep-transition); Cowork inbox has 7 files because Cowork agent time-awareness drift causes filename collisions (overwrite), NOT missed fires |

**5 load-bearing questions all ✅:**

1. Primitive mechanics — both sides fire and write expected files
2. `tier=code` env propagates into scheduled Code session (Phase 3.5 G5 commit gate viable; combines cleanly with PLAN-0009 Step 1a Q3 hook-stdin `agent_id` mechanism for unified 4-case identity composition)
3. Cross-task visibility on UNC mount — Code reader sees all Cowork writes
4. Code Desktop bash works on UNC paths (unlike Cowork's broken `mcp__workspace__bash`)
5. Sleep-recovery clean — ~10h overnight machine sleep → wake → both sides resume + 1 catch-up run each (older missed runs silently dropped per research-note caveat #4, confirmed live)

**2 minor caveats encoded for PLAN-0010 design:**

- **Use filesystem `mtime` as authoritative fire-time** — never trust Cowork agent's claimed timestamp. Drift evidence: Cowork's claimed times in inbox filenames vs actual file mtime show errors from -3h 34m (claimed earlier) to +5h 17m (claimed later) across 7 fires. Filename collisions from this drift caused inbox count (7) to under-represent fire count (~11 successful). Filename should include mtime-derived nonce or process-random suffix for collision resistance.
- **Schedule heavy/batch tasks off-peak Bangkok daytime** — NEW finding F10: Cowork scheduled-task detail page surfaces peak-hours warning verbatim "*This task runs during peak hours (weekdays 5:00 AM-11:00 AM PT, 7:00 PM-1:00 AM local time) and will consume your session usage limits faster.*" Translated for Asia/Bangkok: peak ≈ 7 PM – 2 AM Bangkok; off-peak ≈ 7 AM – 6 PM Bangkok. Heartbeat-class workloads (~1k token/run × hourly) negligible in any window; future high-volume Phase 3.5 work (batch operations, long-context tasks) should be scheduled off-peak. Not surfaced in any of 5 Anthropic docs surveyed during Step 1a research spike + 4 docs cross-checked for Step 1 split — UI-only warning. Candidate for `docs/lessons/` promotion if pattern reproduces elsewhere (Code Routines cloud, Mobile, etc.); for now scoped to F10 in findings file + PLAN-0010 design notes.

**Stagger / cadence observations (F-OBSERVED-4):** Both primitives use **per-task deterministic stagger** (not per-fire random delay). Code Desktop = consistent +5min past hour offset across all 8 runs; Cowork = ~+4min past hour offset across visible attempts. PLAN-0010 implication: co-scheduled tasks must plan stagger offsets if coordination needed (or accept near-same-minute fire times).

**Findings durability:** F1–F10 + F-OBSERVED-1..4 fully captured in `docs/research/private/phase3.5-smoke/findings.md` (gitignored, local-durable on Cray's machine). PLAN-0010 drafting references this file as source-of-truth. Smoke scheduled tasks left running post-verdict for extra reliability data points (low cost — Code Sonnet ~$0.07/day, Cowork heartbeat negligible); cleanup deferred until PLAN-0010 captures all needed findings and Cray approves teardown.

**Identity unification across all 4 cases (final design, combining Step 1a Q3 + Phase 3.5 F5):**

| Identity case | `agent_id` in hook stdin | `CLAUDE_TIER` env | G5 verdict |
|---|---|---|---|
| Main Code interactive | absent | `code` | ✅ allow commit |
| **Main Code scheduled (Phase 3.5)** | **absent** | **`code` (verified live)** | **✅ allow commit** |
| Plan/Explore subagent (Phase 3) | PRESENT | (inherited) | ❌ deny commit |
| Cowork (impossible reach) | absent | empty/other | ❌ deny commit |

One combined check, four cases covered — beautifully unified primitive-native design.

**Next action:** Compose Cowork dispatch block for PLAN-0010 drafting per ADR-009 D1 interim phasing (same pattern as PLAN-0009). Phase 3 execution remains HELD pending Cray sequencing decision (parallel-with-PLAN-0010 vs strictly-serial).

**Prior — PLAN-0009 Step 1 split MERGED + Step 1a survey DONE +
Phase 3.5 smoke observation RUNNING.** Three-track day:

1. **PR #22 (PLAN-0009 Phase 3, `fddcf2e`) + PR #23 (Step 1 split,
   `0fb83fb`) MERGED to main.** HEAD `0fb83fb`. PR #23 splits §Step 1
   into Step 1a (research spike, 1–2 hr) + Step 1b (contract design,
   day-scale). Rationale: Code post-merge cross-check of 4 Anthropic
   docs (Cowork Scheduled / Live Artifacts / CC Routines / Desktop
   scheduled tasks) found 3-of-4 had at least one substantive diff vs
   the Cowork research note that informed PLAN-0009 — including
   undocumented `window.cowork.*` JS APIs, stale daily-run-cap numbers,
   and `CLAUDE_TIER` env-var inheritance that was unverified at draft
   time. Verifying live before contract design lock-in matches the
   PLAN-0008 fact-pack-first discipline + Cray's verification-rigor
   directive (PLAN-0009 §Step 6 + Verification).

2. **Step 1a research spike DONE** — background general-purpose subagent
   (8 min, 95k tokens, 17 tool calls — Code's first parallel-agent
   demonstration this project) wrote
   `docs/research/private/2026-05-25-subagent-primitive-survey.md`
   (Tier-0 research note, gitignored) with 8/8 questions high-
   confidence. Verbatim quotes + 5 Anthropic source URLs. Key findings:

   - **Identity signal = `agent_id` + `agent_type` JSON fields in hook
     PreToolUse/PostToolUse stdin** (Q3, load-bearing for AC-3/AC-6).
     **NOT env vars.** G5 `pretooluse_git_deny.py` final design composes
     2 signals into 1 check for 4 identity cases:
     - `agent_id` PRESENT in stdin → subagent invocation → deny commit
     - `agent_id` ABSENT + `CLAUDE_TIER=code` env → main Code
       (interactive OR Phase-3.5 scheduled) → allow commit
     - `agent_id` ABSENT + `CLAUDE_TIER` not `code` → non-Code → deny
       Resolves ADR-013 OQ-3 unification mechanism via documented harness
     primitive (no env-var gymnastics needed).
   - **Tool allowlist enforced at harness layer** (Q1): `tools` /
     `disallowedTools` frontmatter fields gated by harness before
     dispatch. AC-2 negative tests feasible as written.
   - **No native cwd-narrow or write-path-allowlist primitive** (Q2, Q5).
     AC-3's "Plan writes only under `docs/{adr,plans}/`" = new
     `PreToolUse` hook `pretooluse_plan_subagent_write_deny.py`
     extending the C4 `pretooluse_research_path_deny.py` pattern.
     Preferably in Plan subagent's frontmatter `hooks:` field (subagent-
     scoped, auto-cleanup on subagent exit).
   - **Result reduction = "final message verbatim"** (Q4). No hard
     byte/token bound — "bounded summary" output contract must be
     encoded in subagent system prompt. Residual risk: verbose subagent
     leaks final message into main context.
   - **Built-in `Plan` and `Explore` reserve those exact names** (Q6).
     Step 1b custom subagents must pick non-colliding names; recommend
     `plan-drafter` + `explore-research`.
   - **`isolation: worktree`** frontmatter field gives the subagent a
     fresh checkout — conflicts with CLAUDE.md §11 worktree-OFF default
     for single-doc work. Step 1b: omit `isolation` by default for Plan
     (writes to parent cwd; main agent commits).
   - Bonus primitives discovered: `maxTurns` (loop fail-safe),
     `SubagentStart` / `SubagentStop` hook events (clean wire for AC-5
     completion notify), documented subagent transcript path
     (`~/.claude/projects/<project>/<sessionId>/subagents/agent-<id>.jsonl`
     — useful for AC-6 audit trail). All 8 questions answered without
     live verification needed.

3. **Phase 3.5 smoke observation RUNNING** (started 2026-05-25T16:03 →
   +24-48h). Setup complete with 2 Anthropic scheduled tasks (Cowork
   hourly Write-only producer + Code Desktop hourly bash reader/observer;
   both pinned to MAIN checkout via
   `\\wsl.localhost\Ubuntu-24.04\home\crayj\work\vero-lite` UNC path).
   Run 1 answered 4 of 4 load-bearing questions favorably:

   - `tier=code` ✅ — `CLAUDE_TIER` env var propagates into Code Desktop
     scheduled session (load-bearing for OQ-1 ↔ OQ-3 unification + G5
     gate; combines cleanly with Q3 stdin signal above)
   - `bash=ok` ✅ — Code Desktop scheduled task has working bash on UNC
     paths (NOT the broken `mcp__workspace__bash` Cowork uses; different
     sandbox/layer)
   - `inbox=1` + cross-task file visibility ✅ — Code Desktop reader saw
     Cowork's Write-tool output (same UNC mount, both sides)
   - Cowork `Write` tool works on UNC ✅ — K-1 (`mcp__workspace__bash`
     UNC refusal) confirmed live in scheduled-task context but does NOT
     gate Cowork's Write subsystem (separate path-resolution layer)

   9 findings (F1–F9) captured durably in
   `docs/research/private/phase3.5-smoke/findings.md` (gitignored
   working note). F7 (**Auto mode requires Sonnet-tier model** — Mode
   dropdown greys out "Auto" with label "Not available for the selected
   model" when Haiku 4.5 is selected; becomes selectable on Sonnet 4.6)
   is candidate for promotion to `docs/lessons/` (general Anthropic
   Claude Code primitive behavior, not in any doc surveyed). Observation
   continues 24-48h; daily check ~2026-05-26 +07 → GO / NO-GO decision.
   GO opens PLAN-0010 (Phase 3.5 scheduled-task autonomy loop) + Step
   1b contract design + Phase 3 execution. NO-GO pivots to MCP
   `vero-bridge` roadmap (Phase 3 still proceeds; no scheduled-task
   layer).

**Prior — PLAN-0009 (Phase 3 — subagent topology) RATIFIED + Ready
for execution + COMMITTED.** Cowork drafted under interim ADR-009 D1
phasing; Cray adjudicated all 4 OQs (OQ-1…OQ-4) on 2026-05-25 (WebFetch
for Explore; no new ADR — execute ADR-013 D1; subagent identity folds
with ADR-013 OQ-3 in Step 1; PLAN status vocabulary). Code fact-pack /
R2 review clean across 9 citations (0009 next free; ADR-013 D1/OQ-1/OQ-3
quoted verbatim; PLAN-0008 carry-overs accurate; PLAN template structure
intact; Cray verification-rigor directive present); flipped Status Draft
→ Ready for execution; committed `d10073e` on `feat/plan0009-subagent-topology`
(single-doc, worktree-OFF per CLAUDE.md §11). Phase 3 execution gated on
PR merge.

### Cowork → Code dispatch handoff dog-fooded (K-1 / ADR-009 D3 substitute)

`.claude/handoffs/session-10/2026-05-25-1240-cowork-plan0009-review-dispatch.md`
`validate_handoff.py` clean (9 required fields; actor=cowork / phase=dispatch
/ status=READY / suffix=dispatch; ISO-8601 +07:00; filename matches
`_FILENAME_RE`). Cowork could not run the validator (K-1 UNC-bash refusal);
Code ran post-receive — the standing D3 substitute. Gitignored working
note per CLAUDE.md §11 (the `.claude/handoffs/.gitignore` `*` rule).

### Two reconciliation findings folded into project memory

1. **`.claude/` readability vs PLAN-0008 OQ-D (research-note §6).** Cowork
   successfully Read `.claude/autonomy-triggers.md` this session,
   contradicting PLAN-0008 OQ-D's "sandboxes cannot read
   `.claude/handoffs/`" wording. Reconciled: **K-2 is a write block, NOT a
   read block** (Reads are proxied through the Windows Desktop client).
   The load-bearing forcing fact for OQ-D's deferral remains **K-1**
   (Cowork cannot run `validate_handoff.py` or any bash via UNC), which
   is unchanged. OQ-D's substantive deferral stands; only its prose
   mildly conflates the two axes. **No archived-PLAN amendment** —
   surfaced here for project memory + forward-looking guidance ("keep
   any cross-tier inbox outside `.claude/`" still applies, as
   belt-and-suspenders).
2. **Working-tree divergence (research-note §6.1; reproduced live this
   session).** A Code session running from a git worktree sees **neither**
   uncommitted new files in main tree (`docs/plans/0009-subagent-topology.md`
   initial draft) **nor** gitignored paths (`docs/research/private/`). Both
   are present in `~/work/vero-lite` (main checkout). This is **not**
   K-1/K-2 — it is a `git worktree` checkout-resolution mismatch
   (worktrees check out tracked-only files; both uncommitted new files
   and gitignored paths are filtered out by definition). **Design
   implication** for any future producer/consumer loop (relevant to
   Phase 3.5 if approved): inbox must be a tracked path consumed from
   the main tree, OR committed before hand-off. Folds neatly with the
   PLAN-0009 Step 1 worktree-path normalization carry-over.

### CLAUDE_TIER / session-identity unification (PLAN-0009 OQ-1 ↔ ADR-013 OQ-3)

Confirmed correctly folded in PLAN-0009 Step 1. One mechanism must
distinguish **3 identity cases**:

| Identity | G5 commit authority | Tool/path scope |
|---|---|---|
| Main interactive Code agent | ✅ may commit | full main-agent allowlist |
| Plan / Explore subagent | ❌ must NOT commit | Plan: `docs/{adr,plans}/`; Explore: read-only + WebFetch |
| Scheduled Local Code session (Phase 3.5 — HELD) | ✅ may commit (if approved) | same as main agent |

Existing prose mechanism = `CLAUDE_TIER=code` env-var (this commit used
it); ADR-013 D2 promotes it to deterministic via the G5 hook. PLAN-0009
Step 1's design will wire all three identity cases through one
mechanism — the load-bearing deliverable for AC-3 + AC-6.

### Phase 3.5 — SURFACED, HELD

Research-note §7.5 surfaces a "**Phase 3.5: local scheduled-task poller
experiment**" — Cowork Local scheduled task + Code Local Desktop task
over a repo inbox; appears to deliver most of the auto-handoff value at
lower cost/risk than the MCP `vero-bridge` bridge. Operator constraints
(machine-left-on acceptable, 1h cadence acceptable, avoid cloud)
strongly favor this. **HOLD per Cray** — option SURFACED, not decided.
PLAN-0009 Step 6 + Verification verification-rigor directive
(exhaustive case-coverage matrix; "confident it works" not "tests
pass"; mirrors PLAN-0007 G5 16-case precedent) explicitly binds Phase
3.5 if ratified.

### Prior — PLAN-0008 Phase 2 CORROBORATED via 2 independent AC-1 live runs

Phase 2 was already AUDITED + closed (Step 8 + AC-1 verified amendment
PR #19 merged); a follow-on Auto mode run gives a second independent
data point that strengthens AC-1 evidence + adds layer-orthogonality
confirmation:

### AC-1 evidence corpus — 2 independent runs

| Aspect | Run 1 (Accept edits, main repo, 2026-05-25 ~03:00) | **Run 2 (Auto mode, worktree, 2026-05-25 00:30–00:32)** |
|--------|----------------------------------------------------|---------------------------------------------------------|
| Task | "ตรวจ ruff + mypy ทั้ง project, แก้, commit" | **"สร้าง docs/CHANGELOG.md สรุป Phase 2 PRs #9-#17, commit บน branch ใหม่, ไม่ต้อง push"** |
| Cray paste | Single, then unattended | Single, then unattended |
| Auto-continues observed | ≥ 5 | **≥ 4** (Read STATUS → Write CHANGELOG → Write commit-msg → git commit → summary) |
| Per-tool permission prompts | 1 (UNC path file edit) | **0** (Auto mode skipped them all) |
| Telegram pings (cap / L1-4) | 0 | **0** |
| Terminal pause point | `git push` boundary (memory-aware classifier pause) | **commit done — followed explicit "ไม่ต้อง push"** (no over-step) |
| Commit produced | `8fef3a5` (mypy cleanup, side effect) | **`6dc808c` on `chore/phase2-changelog`** (the CHANGELOG) |

### Layer orthogonality CONFIRMED in production

Mode (PreToolUse permission gate, Anthropic harness layer) and PLAN-
0008 (Stop continuation classifier, our layer) operate independently:

- **Switching Mode = Auto eliminates per-tool prompts** (1 → 0) without
  changing Stop-continuation decisions (≥ 5 → ≥ 4 auto-continues both
  satisfy AC-1 spec).
- **PLAN-0008 classifier honors explicit user instructions** ("ไม่ต้อง
  push" → agent stopped at commit, didn't attempt push despite Auto
  mode permitting it).
- **No false-positive triggers in either run** — 0 Telegram pings
  across both = the L1–L4 loop-detect + chain-cap fail-safe correctly
  stayed silent on routine multi-step work.

### Minor finding for PLAN-0009 carry-over

Run 2's L1 counter key showed `.claude/worktrees/busy-bose-eedc8f/docs/CHANGELOG.md`
instead of the cleaner `docs/CHANGELOG.md`. The `_loop_counter._normalize_file_path()`
strips the main repo prefix but does not collapse the worktree path
suffix — works correctly within a worktree session but creates ugly
keys that don't share state across worktrees. Already a non-blocker
(per-session isolation is by design). Carry-over as a small refinement
for PLAN-0009 if the schema is touched anyway.

**Prior — PLAN-0008 Phase 2 FULLY AUDITED (all 4 ACs verified).**
AC-1 was the only PENDING AC after Step 8 merge (`79fe373`); Cray
ran a Cray-supervised live session 2026-05-25 and the autonomy layer
exercised the auto-continue path as designed.

**AC-1 evidence (2026-05-25):**

| Aspect | Observation |
|--------|-------------|
| Task given | `"ตรวจ ruff + mypy ทั้ง project, แก้ warning ถ้ามี, commit"` (Cray pasted once, no further input) |
| Auto-continues observed | **≥ 5 consecutive** (initial scan → file inspection → plan → branch creation → 5 file fixes → re-verify → tests → commit, all without Cray paste between turns) |
| Terminal pause | Agent paused at the `git push` boundary asking Cray for permission ("ต้องการให้ push + เปิด PR ต่อเลยมั้ยครับ?") — classifier correctly identified push as a state change outside the worktree per the existing `feedback_state_change_outside_worktree.md` auto-memory pattern |
| Telegram pings | **0** — no `cap_reached`, no L1–L4 trigger (no false-positives, depth stayed under cap=8) |
| Chain-state at end | `stop-chain.json` `depth: 0` (consistent with the terminal pause resetting chain) |
| Side effect | The session surfaced **21 project-wide mypy errors** in `tools/` + `tests/` (outside the pre-commit gate scope `^(services|verticals|\.claude/hooks)/`) and shipped a cleanup commit `8fef3a5` on branch `chore/mypy-tools-tests-clean` — PR #18 |

**Implications:**
1. **AC-1 VERIFIED.** Phase 2 acceptance criteria all green
   (AC-1/AC-2/AC-3/AC-4).
2. **Classifier conservatism in production: confirmed.** The agent
   paused at `git push` despite this being a routine action *if it
   were inside the worktree*, because the existing feedback memory
   correctly classifies it as "state change outside the worktree".
   Spurious pauses > spurious proceeds — exactly the bias OQ-B
   adjudicated for.
3. **Cost.** A ~5-turn auto-continue session = ~5 Sonnet classifier
   calls ≈ $0.005 (consistent with the Step 5 + Step 5b cost
   baselines). The cost-telemetry pre-filter (OQ-F) remains
   unnecessary in Phase 2.

Closeout handoff `.claude/handoffs/session-10/2026-05-25-0130-code-plan0008-phase2-closeout.md`
§1 (local working note per CLAUDE.md §11) updated to reflect AC-1
VERIFIED. PLAN-0008 already in `docs/plans/done/` per Step 8.

**Prior — PLAN-0008 Phase 2 COMPLETE.** Step 7 MERGED via [PR #16](https://github.com/CrayJThiemsert/vero-lite/pull/16)
(`9100e65`). Step 8 (closeout + AC matrix + PLAN move to `done/`)
IN-FLIGHT on branch `feat/plan0008-step8-closeout`. The 8-step Phase 2
arc (Steps 1, 2, 3, 4, 5, 5b, 6, 7, 8) leaves the harness autonomy
layer fully wired and tested:

- **Probabilistic / classifier-mediated**: `Stop` continuation loop
  + Sonnet pause/proceed classifier + stateful L1–L4 loop-detection
  + cross-env API key fallback (Step 5b)
- **Deterministic floor (Phase 1) preserved**: G5 git-deny, H1
  handoff-validator, C4 research-path-deny — all reachable and
  reflexively exercised every commit in this session
- **Suite end-state**: 216 (Phase 1) → **389 pass / 6 skip** (Phase 2,
  +173 across 5 new test files incl. 17 E2E integration scenarios
  driving real subprocess hook invocations against a local mock HTTP
  Sonnet server)

**AC matrix verification (full detail in closeout handoff):**

| AC | Status | Evidence |
|----|--------|----------|
| AC-1 (Stop self-continues ≥ 3 auto-continuations) | **PENDING live** | Mechanics verified by Step 7 integration tests + chain-depth progression; live observation deferred — requires unattended Cray-supervised session (interactive sessions cannot exercise the auto-continue path) |
| AC-2 (classifier pauses on registry matches, no false-positives on routine) | **VERIFIED 2026-05-24** | Step 5 live conservatism proof 5/5 scenarios (G1/G2/C2 paused with correct `matched_rows` + 1 routine proceed); $0.005 total cost; mocked harness in Step 7 confirms wire integrity |
| AC-3 (L1–L4 fire on trigger + reset on progress) | **VERIFIED 2026-05-25** | Step 7 + Step 8 integration tests cover all 4 patterns + Cray-E.4 Telegram payload assertion; L3 auto-reset deferred per PLAN §Step 4 closeout (multi-tool observation needs schema evolution → PLAN-0009) |
| AC-4 (Phase 1 + C4 deterministic regression-free) | **VERIFIED 2026-05-25** | pytest 389/6 incl. test_pretooluse_git_deny.py (16 bypass-immune cases), test_posttooluse_validate_handoff.py, test_pretooluse_research_path_deny.py (20 cases) all green; in-session production fires (L1-on-self in PR #15 + H1-on-self in this PR's closeout handoff frontmatter) prove the deterministic + classifier-mediated layer is reachable from real agent activity |

**Closeout handoff** at `.claude/handoffs/session-10/2026-05-25-0130-code-plan0008-phase2-closeout.md`
(local working note per CLAUDE.md §11 — `.claude/handoffs/.gitignore`
keeps these out of the repo). Covers all 4 ACs, cost telemetry
baseline, deferred items carry-over (auto-handoff Code→Cowork, L3
auto-reset, PreToolUse classifier dispatch — all to PLAN-0009),
operational findings (Desktop env strip, L1-on-self, cross-env key
file setup), and Phase 3 entry conditions.

**PLAN move:** `docs/plans/0008-...md` → `docs/plans/done/0008-...md`
(`git mv`). Archived alongside PLAN-003 / PLAN-0005 / PLAN-004 / PLAN-0006
/ PLAN-0007.

**Next: PLAN-0009 (Phase 3 — subagent topology, ADR-013 D1 phased
end-state) entry conditions met.** Recommended outline in closeout
§6: subagent contract design → Explore subagent → Plan subagent →
main-agent dispatch protocol → auto-handoff Code→subagent → live
AC. Cowork-drafted under interim ADR-009 D1 phasing per Cray cadence.

**Prior — PLAN-0008 Step 5b MERGED + Step 7 (Phase 2 integration
tests + mypy hook coverage extension) IN-FLIGHT.** Step 5b
(`_sonnet_classifier.py` config-file fallback) merged via [PR #15](https://github.com/CrayJThiemsert/vero-lite/pull/15)
(`3d4f98b`). Cross-env key file setup completed: Code copied
`~/.claude/.anthropic_api_key` to `C:\Users\crayj\.claude\.anthropic_api_key`
with NTFS ACL `crayj:FullControl` only (SYSTEM + Administrators removed
— stricter than chmod 600). Both WSL Python (`/home/crayj/.claude/...`)
and Windows Python (`C:\Users\crayj\.claude\...`) verified to resolve
the key from their respective `Path.home() / ".claude" / ".anthropic_api_key"`.
Hook firing path (Windows-Python) and pytest path (WSL-Python) both
unblocked for live Sonnet calls.

**Step 7 on branch `feat/plan0008-step7-integration-tests`.** Two
deliverables:

1. **`tests/handoffs/test_phase2_integration.py`** (15 E2E scenarios)
   driving real subprocess invocations of `pretooluse_loop_detect.py`
   + `posttooluse_progress_observer.py` + `stop_continuation.py` with
   a local mock HTTP Sonnet server (ephemeral 127.0.0.1 port via
   `socketserver.TCPServer` + threading daemon; `$CLAUDE_SONNET_API_URL`
   override; no live network). Coverage: Stop→proceed→`block` decision
   with reason propagation; Stop→pause→no block + chain reset;
   classifier fail-closed when env+file missing; `stop_hook_active`
   re-entry guard (mock server records zero requests proves
   short-circuit before classifier dispatch); chain-cap fail-safe
   (Telegram `cap_reached` payload + chain reset, classifier
   short-circuited); observer→state→PreToolUse deny on L1 + L4 at
   threshold 6; L4 reset on success; L2 inline Telegram on
   pytest-fail threshold; L1 turn-boundary survive when target in
   `turn_touched` vs reset when not; re-entry guard preserves state;
   chain depth progression proceed→proceed→pause = 0→1→2→0;
   Phase 1 regression test files present (AC-4 scaffold). All 15
   green.
2. **Pre-commit `mypy` glob extended** from `^(services|verticals)/`
   to `^(services|verticals|\.claude/hooks)/` — closes the Step 1
   closeout follow-on. All 9 hook files pass `mypy --strict` cleanly;
   `pre-commit run mypy --all-files` verified.

Suite totals: **372 → 387 pass / 6 skip** (+15 integration). `ruff` +
`mypy --strict` + `detect-secrets` clean. Per-test isolation via
`tmp_path` for state file, classifier fallback path, telegram capture,
chain file — no developer's real `~/.claude/.anthropic_api_key` can
leak the classifier into a live API call.

AC progress: **AC-3 (loop-detection fires + resets) demonstrated
end-to-end** for the first time (previously only per-hook unit cases).
AC-1 happy-path proceed + chain progression demonstrated. AC-2
governance-match harness is ready (canned `pause` + `matched_rows`
mock); formalization of matched_rows→Telegram payload held for **Step
8 live AC**. AC-4 scaffolded via discoverability test; full
bypass-immunity re-run held for Step 8.

**Prior — PLAN-0008 Step 5b (Anthropic API key config-file fallback)
MERGED.** Step 6 (Wave 2 completion —
`autonomy-triggers.md` row flips + PLAN closeout amendment) merged via
[PR #14](https://github.com/CrayJThiemsert/vero-lite/pull/14)
(`626ab23`). Immediately after, env-propagation diagnostic on the new
session surfaced a **Claude Desktop platform behavior**: on Windows
the Desktop wrapper launches `claude.exe` with `ANTHROPIC_API_KEY=""`
(empty, not unset) as deliberate OAuth-subscription / API-key billing
isolation. WSLENV propagation cannot defeat this — User-scope env is
overwritten before the CLI spawn, even after full computer restart.
The Step 5 live conservatism proof (2026-05-24) only passed because
Cray ran the live pytest from a WSL terminal **outside** the Desktop
process tree; any in-session hook invocation of `_sonnet_classifier.py`
would have fail-closed paused on every Stop event due to the empty key.

**Step 5b fix on branch `feat/plan0008-step5b-classifier-config-fallback`.**
`_sonnet_classifier.py::_resolve_api_key()` extended with a chain
fallback: `$ANTHROPIC_API_KEY` (truthy after strip) →
`~/.claude/.anthropic_api_key` (override via
`$CLAUDE_ANTHROPIC_KEY_FILE`; POSIX requires chmod 600; first non-empty
line, whitespace stripped) → fail-closed pause. **+10 unit tests** added
(`test_sonnet_classifier.py` 17 → 27; full suite 362 → 372 pass / 6
skip), all green. autouse `isolated_key_file` fixture prevents tests
from picking up Cray's real key file. `.gitignore` extended with
`.claude/.anthropic_api_key` (belt-and-suspenders; canonical location
is `~/.claude/.anthropic_api_key` outside repo). PLAN-0008 §Step 5
gains the Step 5b amendment box; auto-memory finding saved at
`project_claude_desktop_strips_anthropic_api_key.md` for future
sessions.

**Live verification PASSED inside this Claude Code session
(2026-05-24).** Direct invocation of `sc.classify()` from a Bash tool
call: env `ANTHROPIC_API_KEY=""` (Desktop strip confirmed) →
`_resolve_api_key()` returned `(sk-ant..., file:/home/crayj/.claude/.anthropic_api_key)`
→ real Sonnet round-trip 3.04s → `{decision: "proceed", matched_rows:
[], reason: "..test/verification Stop event with no pending tool
actions.."}`. The same call pre-Step-5b would have returned fail-closed
pause. Proof complete that the fix defeats the Desktop strip.

**Cross-env caveat.** Hooks fire under Windows Python (`Path.home() =
C:\Users\crayj\`); pytest invoked via the Bash tool runs WSL Python
(`Path.home() = /home/crayj/`). Cray must either (a) maintain a copy
of the key file at both paths, (b) symlink one to the other, or (c)
set `$CLAUDE_ANTHROPIC_KEY_FILE` (this var is **not** Desktop-stripped
— verified via `CLAUDE_TIER` + `TELEGRAM_*` propagating intact) to a
single canonical location via WSLENV. Recommendation documented in
the Step 5b PR body.

**Prior — PLAN-0008 Step 6 (Wave 2 completion — autonomy-triggers row
flips) MERGED.** PR #14 landed on `main` as `626ab23` (single `docs(claude)`
commit `aa64d19` + merge commit). Docs-only flip of registry row labels
in `.claude/autonomy-triggers.md` from placeholder / "Phase 2 spec"
wording to **LIVE** with concrete hook attribution: G1/G2/G3/G4 +
C1/C2/C3 → `_sonnet_classifier.py`; L1–L4 → three-hook attribution
(`pretooluse_loop_detect.py` gate + `posttooluse_progress_observer.py`
writer + `stop_continuation.py` reset); "How the classifier reads this
file" §flipped from spec to LIVE with conservatism-probe evidence;
status banner + footer date updated. PLAN-0008 §Step 6 gained the
"Step 6 closeout — Wave 2 completion" amendment with PR #11/#12/#13
lineage. `.claude/settings.json` `_comment` corrected (stub removal
happened in PR #13, not Step 6). 362 pass / 6 skip baseline preserved
(docs-only).

**Prior — PLAN-0008 Step 5 (Sonnet classifier helper + stub swap)
MERGED + LIVE conservatism proof PASSED.** PR #13 landed on `main` as
`3407ae6` (single `feat(claude)` commit `ceebc1a` + merge commit).
4-piece bundle: (1) new `.claude/hooks/_sonnet_classifier.py` (~225
lines) — stdlib urllib + Anthropic Messages API + JSON-in-text +
retry-once + 7 fail-closed pause paths; pin `claude-sonnet-4-6`
(OQ-B); reads `.claude/autonomy-triggers.md` verbatim. Stdlib-only
deviation from PLAN's "SDK preferred" rationalized (avoids C2
chicken-and-egg + matches Phase 1 hooks idiom; retry + markdown-fence
extractor + fail-closed mitigate the structured-output gap). (2)
`stop_continuation.py` amendment — `_classifier_stub()` removed;
`_classify()` wrapper with defensive double-fallback (ImportError +
final catch-all). (3) `tests/handoffs/test_sonnet_classifier.py`
(NEW, 17 cases incl 1 live opt-in via `RUN_LIVE_SONNET_TESTS=1` per
OQ-G). (4) `test_stop_continuation.py` fixture pops
`ANTHROPIC_API_KEY` for determinism. **LIVE verification (Cray
2026-05-24, 20:00–20:25):** opt-in smoke + 4-scenario conservatism
proof passed 5/5 — bare Stop → proceed; G1 (edit Accepted ADR) →
pause with rows `['G1']`; G2 (consume ADR-014) → pause with `['G2']`;
C2 (add `anthropic` dep) → pause with `['C2']`; routine work
(pytest + variable rename) → proceed. Sonnet's plain-English reasons
are informative and accurate. Total live cost ~$0.005. **WSLENV
permanently extended** with `ANTHROPIC_API_KEY/u` via PowerShell
`[Environment]::SetEnvironmentVariable(..., "User")` so fresh Claude
Code sessions inherit the key without manual workaround. `pytest`
362 pass / 6 skip (Step 4 baseline 346/5 → 362/6); `ruff` +
`mypy --strict` + `detect-secrets` clean.

**Session handoff to new Code session.** This session has accumulated
considerable context across Phase 2 Steps 1–5 (PR #8/9/10/11/12/13)
plus the L1/L4 ELI-CTO + Wave 1/2 design + classifier conservatism
validation. Cray-directed handoff to a fresh Code session for **Step
6 (Wave 2 completion)** to preserve context-window headroom and
double as a live verification of the permanent WSLENV propagation
from a clean process tree. Handoff brief:
`.claude/handoffs/session-10/2026-05-24-2030-code-step5-merged-step6-kickoff.md`.

**Prior — PLAN-0008 Step 4 (Stop hook + L1 turn-boundary reset)
MERGED with expanded scope.** PR #12 landed on `main` as `b09bf39`
(single `feat(claude)` commit `010ae1b` + merge commit). 5-piece
bundle per Cray-ratified scope expansion: (1) new
`.claude/hooks/stop_continuation.py` (~200 lines) — Stop hook with
`stop_hook_active` re-entry guard + **L1 turn-boundary reset** (reads
`turn_touched`, resets untouched L1 counters, clears marker) + chain
depth tracking in `.claude/state/stop-chain.json` + cap-hit policy
(OQ-E option b: pause + Telegram `cap_reached` + reset chain) +
classifier dispatch via `_classifier_stub` (pause-by-default until
Step 5 wires real Sonnet helper). (2) `_loop_counter.py` amendment —
`turn_touched: list[str]` field with JSON round-trip + back-compat for
old state files; 3 new helpers (`record_turn_touched`,
`reset_untouched_l1`, `clear_turn_touched`). (3)
`posttooluse_progress_observer.py` amendment — `_handle_write_or_edit`
records turn_touched on every Write/Edit so Stop hook has the touched
signal. (4) `.claude/settings.json` — **early Wave-2-partial wire**
for Stop hook (required for L1 reset to fire; classifier stub keeps
the wire safe to land before Step 5). (5) 26 new tests (18
`test_stop_continuation.py` + 7 `turn_touched` primitives in
`test_loop_counter_state.py` + 1 observer amendment). **🔴 L1 reset
gap CLOSED** — Cray's iterative STATUS-editing workflow no longer at
false-positive risk. `pytest` 346 pass / 5 skip (Step 3 baseline 320
→ 346); `ruff` + `mypy --strict` + `detect-secrets` clean. **Next:
Step 5** — replace `_classifier_stub` with real Sonnet helper
(stdlib urllib + Anthropic Messages API, fail-closed pause).

**Prior — PLAN-0008 Step 3 (PostToolUse progress observer + Wave 1
wire + PLAN amendment) MERGED.** PR #11 landed on `main` as `632a22c`
(single `feat(claude)` commit `1c2a7b6` + merge commit). 4 things
bundled per Option C + documentation option (3): (1) new
`.claude/hooks/posttooluse_progress_observer.py` (~260 lines,
refactored into `_apply_l2`/`_apply_l3`/`_apply_l4` helpers) — the
writer side that feeds the loop-counter from `Bash`/`Write`/`Edit`
outcomes; never blocks; L2/L3 fire Telegram **inline on trigger**
(PreToolUse can't predict nodeid/signature pre-execution) while L1/L4
let Step 2's PreToolUse gate fire on next attempt; defensive Bash
exit-code detection (`interrupted` → explicit `exit_code` →
`is_error` → stderr-with-error-marker → heuristic) so ambiguous
outcomes are no-op (not spurious increment). (2) 31 new tests with
Telegram-stub fixture capturing real Cray-E.4 payload + 2 lock-in
tests for L1/L4 asymmetry. (3) **Wave 1 wire** in
`.claude/settings.json` — registers `pretooluse_loop_detect.py`
alongside `pretooluse_git_deny.py` (Bash) and
`pretooluse_research_path_deny.py` (Write|Edit); registers
`posttooluse_progress_observer.py` alongside
`posttooluse_validate_handoff.py` (Write|Edit) + new PostToolUse Bash
matcher. (4) PLAN-0008 amendment boxes in §Step 3 + §Step 6 codifying
the Wave 1/2 split. `pytest` 320 pass / 5 skip (Step 2 baseline 289 →
320); `ruff` + `mypy --strict` + `detect-secrets` clean.

**L1/L4 asymmetry ELI-CTO + Step 4 prioritization (Cray 2026-05-24).**
During PR #11 review Cray asked for an ELI-CTO breakdown of the L1/L4
asymmetry (Step 3 increments → Step 2 gates on next attempt vs L2/L3
fire inline). Code's analysis: 🟢 the off-by-one + abandoned-loop +
spec-matching are by-design and not problems; 🟡 the L2/L3 vs L1/L4
fire timing is a minor UX inconsistency (deferrable to Step 8); 🔴
**L1 missing reset until Step 4 lands is a real op risk** — Cray's
actual iterative workflow on STATUS.md (already 4 of 6 edits used in
this session before PR #11 merge) would false-positive-deny without
turn-boundary reset. Cray ratified the recommendation: merge PR #11 +
**prioritize Step 4** with proper L1 reset implementation (not just a
Stop-hook stub). Step 4 scope expansion under surface — see
In-Flight Discussions.

**Prior — PLAN-0008 Step 2 (PreToolUse loop-detect hook) MERGED.**
PR #10 landed on `main` as `9494f93` (single `feat(claude)` commit
`ad2c047` + merge commit). New
`.claude/hooks/pretooluse_loop_detect.py` (~185 lines) reads the Step 1
state file and gates on L1 (`Write`/`Edit` with same `file_path` ≥ 6
times) and L4 (`Bash` with same tokenized command ≥ 6 accumulated
non-zero exits from Step 3). On trigger fires `tools/notify/telegram.sh`
with the Cray-E.4 payload contract `{loop_type, target,
last_6_actions}` and emits a `deny` PreToolUse decision asking Cray
to intervene. Env-var overrides (`CLAUDE_LOOP_COUNTER_PATH`,
`CLAUDE_TELEGRAM_SCRIPT`) read from hook process env, not
`tool_input` → spoof-immune. **L2** (test_fail) and **L3**
(error_signature) explicitly NOT enforced at PreToolUse (locked by 2
test cases) — they are inherently post-execution signals and will be
fired by Step 3 inline when their counters trigger. 24 new tests
(`tests/handoffs/test_pretooluse_loop_detect.py`) incl Telegram-stub
fixture that captures the real payload + "deny still fires when
Telegram script missing"; `pytest` 289 pass / 5 skip (Step 1 baseline
265 → 289); `ruff` + `mypy --strict` + `detect-secrets` clean.

**Wave 1/2 settings.json activation decision (Option C — Cray
2026-05-24).** PLAN-0008 §"Step 6" originally said "Register Steps 2–5
hooks in `.claude/settings.json`" as one batch. Code surfaced 3
alternatives during Step 2 PR (#10): A wire per step; B wire all at
Step 6 (PLAN literal); **C phased — Wave 1 wires Step 2 + Step 3
together when Step 3 lands, Wave 2 wires Step 4 + Step 5 at Step 6**.
Cray ratified C. Rationale: (1) L1/L4 loop-detect is standalone
deployable — does not depend on Stop loop + Sonnet classifier;
artificial coupling delays smoke testing. (2) Real Claude Code event
payload (vs test-crafted JSON) may have edge cases unit tests miss;
early smoke catches integration bugs before Step 4–5 development
piles on. (3) Match Phase 1 phased pattern (3 hooks landed
incrementally with smoke each). Cost: 2 `settings.json` edits across
Wave 1 + Wave 2 instead of 1 — minor append/scatter, not load-bearing.
**Step 3 PR will bundle**: writer hook + tests + Wave 1 wire +
PLAN-0008 amendment (note Wave 1/2 split in §Step 3 + §Step 6 — per
documentation option (3) Cray-approved 2026-05-24) — one commit per
the Option C ratification.

**Next: Step 3** — `.claude/hooks/posttooluse_progress_observer.py`
(writer + L2/L3 inline Telegram firing) + Wave 1 wire +
PLAN amendment, on branch `feat/plan0008-step3-posttooluse-progress-observer`.

**Prior — PLAN-0008 Step 1 (loop-counter state module) MERGED.**
PR #9 landed on `main` as `2b303a0` (single `feat(claude)` commit
`e20a6f3` + merge commit). New `.claude/hooks/_loop_counter.py` (~340
lines, stdlib-only) ships the Phase 2 state primitives: `LoopType`
enum (L1–L4 mapping to `.claude/autonomy-triggers.md`),
`LoopCounter`/`CounterEntry`/`ActionRecord` dataclasses with explicit
JSON round-trip, atomic `load_counter`/`save_counter` (tmpfile +
`os.replace`, tolerant of missing/empty/malformed/wrong-root files),
4 normalization helpers (file path reusing C4 hook idiom for
Windows-UNC, pytest nodeid stripping `[param]` suffix, error signature
stripping 6 volatile patterns, bash command tokenization), session-ID
resolution per **OQ-A** (`$CLAUDE_SESSION_ID` → `pid-<PID>` →
`uuid-<UUID>` fallback chain), counter ops (`increment` with
`last_6_actions` ring buffer per Cray E.4 payload contract, `reset`
removes entry, `get_count`, `has_triggered` against
`LOOP_TRIGGER_THRESHOLD=6`). 49 new tests
(`tests/handoffs/test_loop_counter_state.py`) incl concurrent-write
race (writer + reader threads, no partial reads); `pytest` 265 pass /
5 skip (Phase 1+C4 baseline 216 → 265); `ruff` + `mypy --strict` +
`detect-secrets` clean. **Next: Step 2** —
`.claude/hooks/pretooluse_loop_detect.py` (read state, gate on L1/L4
≥6, fire telegram, deny) on branch
`feat/plan0008-step2-pretooluse-loop-detect`.

**Prior — PLAN-0008 (Phase 2 harness autonomy layer) DRAFTED +
MERGED.** PR #8 landed on `main` as `ec5e2ae` (3 commits: draft
`b53763d` + OQ resolutions `5a34ab0` + merge). Phase 2 scope = three
coupled pieces layering the probabilistic / classifier-mediated engine
on top of Phase 1's deterministic hooks: (1) **`Stop` continuation
loop** with `stop_hook_active` re-entry guard +
`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP=8` chain cap; (2) **Sonnet
pause/proceed classifier** reading `.claude/autonomy-triggers.md`
verbatim (fail-closed, model pin `claude-sonnet-4-6`); (3) **stateful
loop-detection L1–L4** via `.claude/state/loop-counter.json`
(gitignored; payload `{loop_type, target, last_6_actions}` per ADR-013
/ Cray E.4). 4 ACs incl **AC-4 Phase 1 regression-free** (16-case
bypass-immune commit-deny + handoff-validator + C4 research-path-deny
all stay green). All 7 OQs (A–G) adjudicated by Cray on 2026-05-24:
A (session-ID = `$CLAUDE_SESSION_ID` → PID → UUID fallback), B
(Sonnet pin), C (registry path-reference, not inline), **D
(auto-handoff DEFERRED to PLAN-0009** — K-1/K-2 forcing fact still
blocks Cowork read-side so auto-draft does not reduce the Cray-paste
relay; Plan subagent = right author per ADR-013 D1; surface bloat),
E (BLOCK_CAP hit → pause + Telegram `"cap reached"`), F (no Phase 2
pre-filter; cost telemetry is the trigger), G (CI mocks Sonnet +
opt-in `RUN_LIVE_SONNET_TESTS=1`). Status: **Ready for execution**.
**Next: Step 1** — `.claude/state/` directory + `loop-counter.json`
schema + `.gitignore` extension + atomic-write tests, on branch
`feat/plan0008-step1-state-design`. Cowork-drafted under interim
ADR-009 D1 (ADR-013 D1 phasing); Code committed per ADR-009 D2.

**Prior — Research-path enforcement (C4 hook) MERGED.** PR #7
landed on `main` as `da4f91d` (single `feat(claude)` commit `21f0f7a`
+ merge commit). Third deterministic Phase-1 row in `.claude/autonomy-triggers.md`
alongside G5 (`pretooluse_git_deny.py`) and H1 (`posttooluse_validate_handoff.py`):
`.claude/hooks/pretooluse_research_path_deny.py` blocks `Write`/`Edit`
under `docs/research/` outside `docs/research/private/**`. Motivation
= N=2 violations of the documented rule (`cowork_tab_instructions.md`
line 192 + `.gitignore` lines 49-51) in 8 days — Lesson #5 §10.5
(2026-05-15 audit baseline, `docs/strategy/public/` drop) +
2026-05-23 `chat_harness_extension_points_analyzed.md` (detected
+ corrected during PLAN-0007 post-merge cleanup). Applies ADR-013 D2
precedent: when documentation alone fails twice, promote to
deterministic hook reinforcement. 20 new unit tests (allow private/
+ strategy/, deny public/ + bare research/ + arbitrary subdirs, path
normalization for Windows UNC both directions, edge cases for non-Write
tools + malformed stdin); `pytest` 216 pass / 5 skip; `ruff` + `mypy`
+ `detect-secrets` clean. Cowork research workflow unchanged for the
happy path (private/ writes allowed); only the off-policy writes are
blocked at the hook layer.

**Prior — Harness autonomy layer (ADR-013 + PLAN-0007) Phase 1
MERGED.** PR #6 landed on `main` as `b2ea9b8` (9 commits: 6 Phase A
governance + 3 Phase B execution). The `.claude/` autonomy layer is
live: deterministic PreToolUse deny on `git commit|push|merge` from
non-Code sessions (CLAUDE_TIER env marker, bypass-immune across 16
test cases incl `bash -c`, backtick, `git -C`, inline env spoof);
Notification hook → `tools/notify/telegram.sh` (env-var-only Telegram
bridge with graceful no-op when unset, live ping verified end-to-end
by Cray); PostToolUse handoff frontmatter auto-validator (Write|Edit
on `.claude/handoffs/**`, blocks on hard error); `.claude/autonomy-triggers.md`
registry (G1–G5 governance, C1–C3 config/dep/wording, H1 handoff,
L1–L4 loop-detect rows flagged "Phase 2 enforcement"). 28 new unit
tests; `pytest` 196 pass / 5 skip; `ruff` + `mypy` + `detect-secrets`
clean.

**OQ-3 resolution (Code-decided, ADR-013).** Session-identity signal =
env var `CLAUDE_TIER=code`, set by Cray on the launching shell.
Bypass-immune against `permission_mode=bypassPermissions` (hook
decisions run regardless of permission_mode) and against inline
command spoofing (hook reads its own process env, not the tool_input
string). Windows-host setup: `setx CLAUDE_TIER code` + `setx WSLENV
CLAUDE_TIER/u:TELEGRAM_BOT_TOKEN/u:TELEGRAM_CHAT_ID/u`. Token rotated
on 2026-05-23 after one-time screenshot leak in chat (Cray-handled
via `@BotFather`).

**Next:** PLAN-0008+ for Phase 2 entry conditions reached
(`Stop` continuation loop + Sonnet pause/proceed classifier reading
`.claude/autonomy-triggers.md` + stateful loop-detection state file +
subagent topology + MCP `vero-bridge` transport). Drafting cadence
per Cray; the deterministic safety pieces (commit deny, handoff
auto-validation) and the AFK channel are now load-bearing — Phase 2
adds the probabilistic / classifier-mediated layer on top.

---

**Prior — PLAN-0006 (LLM reasoning-hook execution) MERGED.** The brain
swap is done: `services/engine/recommender.py::recommend()` is now LLM-backed
(ADR-010 D5) — **merged to `main` via PR #5 (`68053fe`)**, 12 commits incl.
ADR-001 Amendment 1. Steps 0-8 of the Phase-1 kickoff dispatch all landed:
`ruff` + `mypy --strict` clean, **173 passed / 0 skipped** (with live
Postgres), coverage **94.56%** (new `services/engine/llm/` modules 92-100%).

**CHECKPOINT-0 (Step 0 / ADR-010 IN-1)** — verified live on MS-S1 MAX:
Ollama **0.24.0**, pin **`gpt-oss:20b`** (Cray-adjudicated; gpt-oss:20b and
gemma4:26b both honour the `format` schema constraint under every `think`
setting). The Ollama #15260 `think=false`+`format` bug is **still live for
the Qwen3.x family** but absent for gpt-oss:20b + gemma4:26b. Binding rule:
the structuring call omits `think` — never `think=false` with `format`.

New module set (PLAN-0006) — `services/engine/llm/`: `client.py` (async
Ollama wrapper), `prompt.py` (assembly + IN-2 injection containment),
`structured.py` (constrained generation + validate-and-retry + semantic
checks + the SC-1 reduced `LlmJudgment` sub-schema), `trace.py` (hybrid
reasoning trace). `recommender.py` rewired — `async`, with the deterministic
rule body retained as the fail-safe; `config.py` extended; one `await` at
the API call site; an eval harness + golden traces under
`tests/services/engine/eval/`.

**Follow-ons:** **TODO-A is done** — ADR-001 Amendment 1 (`30d2c8e`) pins
`gpt-oss:20b` + Ollama 0.24.0 for the recommender path (superseding
`gemma4:26b` for that path only). TODO-B (config default) is
satisfied — Step 1 added a dedicated `recommender_model` setting. **SC-1**
resolved by Code: constrained generation targets the reduced `LlmJudgment`
sub-schema; the harness composes the full (unchanged) ADR-007 D2 envelope.
A Step-7 live capture surfaced + fixed a `suggested_handler` defect (the
model invented unregistered handlers — now enum-constrained to the registry).

**Prior this session — PLAN-0005 Phase 2 (OCT Engine Runtime Layer) MERGED**
(PR #4, `c646bab`) — the runtime the LLM hook plugs into. **109 passed**,
coverage **95.34%**. Module / endpoint set (PLAN-0005 §11):

- `services/engine/data_adapter.py` — `DataAdapter` Protocol (ADR-007 D1)
- `services/engine/actions.py` — `RecommendedAction` runtime envelope (ADR-007 D2)
- `services/engine/registry.py` — `VerticalRegistry` (OQ-6 explicit registration)
- `services/engine/recommender.py` — rule-based recommender + minimal approval
  gate (`recommend` / `approve` / `reject` / `execute`; OQ-2/OQ-3)
- `verticals/energy/data_adapter/` — `EnergySyntheticAdapter` + synthetic dataset
- `verticals/energy/handlers.py` — energy `echo` action handler
- `services/db/` — async SQLAlchemy ORM (6 energy tables), session, and the
  envelope→entity persistence projection
- `alembic/` — async migration env + first revision (the six energy tables)
- `services/api/` — three-layer wiring: lifespan-registered energy vertical +
  the action-loop router: `GET /objects/{type}`, `GET /recommendations`,
  `POST /recommendations/{id}/approve`, `POST /recommendations/{id}/execute`;
  `/health` preserved

All six §8 Open Questions (Cray-adjudicated 2026-05-21) are honoured. Persistence
(OQ-4) is real `postgres:16-alpine` via SQLAlchemy 2.0 async + Alembic + asyncpg;
the §7.6 tests run against a live DB and the DDL/ORM parity test (C-1/R6) guards
type drift. The §8.1 deferred-foundational revisit register is in Active TODOs.

Tooling note: `ruff` + `mypy` are now pinned in `pyproject.toml` to the
pre-commit gate versions (`9d461f2`) — closes a `.venv`-vs-gate version skew.
The pre-commit `mypy` hook now also covers `^(services|verticals)/`
(`9dd1470`), not just `services/` — closes the flagged coverage gap.

---

## Prior focus (archived)

PLAN-003 Phase 1 (ontology engine + 5 emitters), PLAN-0005 Phase 2
(OCT engine runtime layer), PLAN-0006 (LLM reasoning hook),
PLAN-0007 Phase 1 (harness autonomy layer — deterministic floor),
and **PLAN-0008 Phase 2 (harness autonomy layer — probabilistic /
classifier-mediated engine on top of Phase 1)** are all **merged and
moved to `docs/plans/done/`**. The Cowork-as-Tier-1 trial that ran as
the test-bed across the earlier batches **concluded** — ratified
permanently by **ADR-009** (Cowork = merged Tier 0 + Tier 1 workspace;
commits stay Code-exclusive). PLAN-004 Phase A (handoff frontmatter
schema + tooling) also landed; Phase B/C remain deferred (backlog).
Full detail lives in `docs/plans/done/`, the Recent Decisions table
below, and git history.

## Recent Decisions (last 5)

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-05-25 | **PLAN-0009 (Phase 3 — subagent topology) RATIFIED + Ready for execution + COMMITTED** — Cowork drafted under interim ADR-009 D1 phasing; Cray adjudicated all 4 OQs (OQ-1…OQ-4) 2026-05-25 (WebFetch for Explore; no new ADR — execute ADR-013 D1; subagent identity folds with ADR-013 OQ-3 in Step 1; PLAN status vocabulary). Cowork → Code dispatch handoff at `.claude/handoffs/session-10/2026-05-25-1240-cowork-plan0009-review-dispatch.md` `validate_handoff.py` clean (K-1 / ADR-009 D3 substitute — 9 required fields, actor=cowork / phase=dispatch / status=READY / suffix=dispatch, ISO-8601 +07:00, filename matches `_FILENAME_RE`). Code fact-pack / R2 review clean across 9 citations (0009 next free; ADR-013 D1/OQ-1/OQ-3 quoted verbatim; PLAN-0008 4 carry-overs accurate; PLAN template structure intact; Cray verification-rigor directive present in Step 6 + Verification). Status flipped Draft → Ready for execution in commit `d10073e` on `feat/plan0009-subagent-topology` (single-doc, worktree-OFF per CLAUDE.md §11). **2 reconciliation findings folded** into Current Focus: (1) `.claude/` readability — K-2 is write-block NOT read-block (research-note §6); OQ-D load-bearing forcing fact remains K-1 (Cowork can't run `validate_handoff.py`), substantive deferral stands. (2) Working-tree divergence — git worktree sees neither uncommitted new files nor gitignored paths (research-note §6.1, reproduced live this session); not K-1/K-2 but checkout-resolution mismatch; design implication for Phase 3.5 if approved. **CLAUDE_TIER / session-identity unification** confirmed correctly folded in PLAN-0009 Step 1 (one mechanism, 3 identity cases: main Code may commit, Plan/Explore subagent must NOT, scheduled Local Code session may [Phase 3.5 HELD]). **Phase 3 execution gated on PR merge. HOLD Phase 3.5** (research-note §7.5 local scheduled-task poller option SURFACED, not decided) | `d10073e` / `docs/plans/0009-subagent-topology.md` + `.claude/handoffs/session-10/2026-05-25-1240-cowork-plan0009-review-dispatch.md` |
| 2026-05-25 | **PLAN-0008 AC-1 CORROBORATED via Auto mode bonus run + layer orthogonality CONFIRMED in production** — A second AC-1 live verification run (2026-05-25 00:30–00:32) using **Mode = Auto** in a fresh worktree session: task `"สร้าง docs/CHANGELOG.md สรุป Phase 2 PRs #9-#17, commit บน branch ใหม่, ไม่ต้อง push"`, single Cray paste, no further input. Result: **≥ 4 auto-continues, 0 permission prompts (Auto mode skipped them all), 0 Telegram pings, terminal pause at commit done** (followed explicit "ไม่ต้อง push" instruction — no over-step). Commit `6dc808c` on branch `chore/phase2-changelog` (unpushed per instruction). **Layer orthogonality confirmed**: Mode (PreToolUse harness layer) ↔ PLAN-0008 (Stop classifier layer) operate independently — Auto mode eliminates per-tool prompts without changing Stop-continuation decisions. **Minor finding for PLAN-0009 carry-over**: `_loop_counter._normalize_file_path()` strips main-repo prefix but does not collapse worktree path suffix (L1 counter key showed `.claude/worktrees/busy-bose-eedc8f/docs/CHANGELOG.md` instead of `docs/CHANGELOG.md`). Non-blocking; per-session isolation works correctly. Both AC-1 evidence runs documented in Current Focus comparison table. Cost: ~$0.004 (4 classifier calls × ~$0.001) | PR #20 amendment / `docs/STATUS.md` |
| 2026-05-25 | **PLAN-0008 AC-1 VERIFIED — Phase 2 fully audited** — Cray ran the live AC-1 task in a fresh Code session (task: *"ตรวจ ruff + mypy ทั้ง project, แก้ warning ถ้ามี, commit"*, single Cray paste, no further input). Agent self-continued **≥ 5 consecutive turns** without Cray paste (initial scan → file inspection → plan → branch creation → 5 file fixes → re-verify → tests → commit), then paused at the `git push` boundary asking permission — classifier correctly identified push as state change outside worktree per `feedback_state_change_outside_worktree.md` memory pattern. **0 Telegram pings** (no `cap_reached`, no L1–L4 false-positives). `stop-chain.json` `depth: 0` at end (consistent with terminal pause resetting chain). Side effect: the session surfaced 21 project-wide mypy errors in `tools/` + `tests/` (outside the pre-commit gate scope) and shipped a cleanup commit `8fef3a5` — PR #18 follows separately. Confirms classifier conservatism bias (spurious pauses > spurious proceeds, per OQ-B) works in production. Phase 2 all 4 ACs now VERIFIED; entry conditions for PLAN-0009 (Phase 3 — subagent topology) met | PR #19 amendment / `docs/STATUS.md` + closeout handoff §1 |
| 2026-05-25 | **PLAN-0008 Phase 2 COMPLETE — Step 8 closeout MERGED** — PR #17 → `main` (`79fe373`), single `feat(claude)` commit `b3657d5` + merge. AC matrix at merge time: AC-2/AC-3/AC-4 VERIFIED; AC-1 deferred to live Cray-supervised observation (subsequent AC-1 row above closes this). Step 8 deliverables: +2 E2E tests (test_l3_traceback_inline_fires_on_threshold + test_l2_resets_on_pass_for_same_nodeid; 387 → 389 pass / 6 skip); closeout handoff at `.claude/handoffs/session-10/2026-05-25-0130-code-plan0008-phase2-closeout.md` (gitignored local working note per CLAUDE.md §11); `git mv docs/plans/0008-...md docs/plans/done/`; STATUS final bump. Phase 3 (subagent topology, ADR-013 D1 phased) entry conditions met. **Reflexive H1 hook fire on the closeout handoff frontmatter** (`phase: completion` initially invalid; corrected to `phase: closeout` per enum) — N=3 production-validation events through this session (L1 in PR #15, L1-attempt in PR #16, H1 in this PR) prove the deterministic + classifier-mediated layer is reachable from real agent activity | `79fe373` (PR #17) / `docs/plans/done/0008-harness-autonomy-layer-phase-2.md` |
| 2026-05-25 | **PLAN-0008 Step 7 (Phase 2 integration tests + mypy hook coverage extension) MERGED** — PR #16 → `main` (`9100e65`), single `test(claude)` commit `d870d76` + merge. New `tests/handoffs/test_phase2_integration.py` with 15 E2E scenarios driving real subprocess invocations of all 3 wired Phase 2 hooks against a local mock HTTP Sonnet server (ephemeral 127.0.0.1 port via `socketserver.TCPServer` + threading daemon; `$CLAUDE_SONNET_API_URL` override; no live network). Coverage: Stop↔classifier wiring (proceed→block, pause→no-block, fail-closed, re-entry guard — mock receives 0 requests = negative proof); chain-cap fail-safe + cap_reached Telegram; observer→state→PreToolUse deny on L1+L4 + Cray-E.4 payload assertion; L4 reset on success; L2 inline Telegram on pytest-fail threshold; L1 turn-boundary survive vs reset; chain depth progression. Pre-commit `mypy` glob extended `^(services\|verticals)/` → `^(services\|verticals\|\.claude/hooks)/` (closes Step 1 follow-on; all 9 hooks pass `--strict`). 372 → 387 pass / 6 skip (+15). Per-test isolation via `tmp_path` for state + classifier fallback path + telegram capture + chain file. AC-3 demonstrated E2E for the first time | `9100e65` (PR #16) / `tests/handoffs/test_phase2_integration.py` |
| 2026-05-25 | **Cross-env Anthropic key file setup completed (Step 5b follow-up)** — Code copied WSL `~/.claude/.anthropic_api_key` to Windows `C:\Users\crayj\.claude\.anthropic_api_key` with NTFS ACL tightened to `crayj` user only (SYSTEM + Administrators removed — strictly tighter than chmod 600). Both `Path.home() / ".claude" / ".anthropic_api_key"` resolution paths verified: WSL Python finds at `/home/crayj/.claude/...`, Windows Python finds at `C:\Users\crayj\.claude\...`. Hook firing path (Windows-spawned hooks) and pytest path (WSL-spawned via Bash tool) both unblocked for live Sonnet operations | `C:\Users\crayj\.claude\.anthropic_api_key` (NTFS user-only) |
| 2026-05-24 | **PLAN-0008 Step 5b (Sonnet classifier config-file fallback) MERGED — defeats Claude Desktop ANTHROPIC_API_KEY strip** — PR #15 → `main` (`3d4f98b`), single `fix(claude)` commit `472a91e` + merge. Diagnosed during Step 6 post-merge env-propagation verification: Claude Desktop on Windows launches `claude.exe` with `ANTHROPIC_API_KEY=""` (intentional OAuth/billing isolation); WSLENV cannot defeat even after full computer restart. Step 5 live proof passed only because Cray ran pytest from a terminal launched outside Desktop. Fix: `_sonnet_classifier.py::_resolve_api_key()` chain → env → `~/.claude/.anthropic_api_key` (chmod 600 POSIX, override via `$CLAUDE_ANTHROPIC_KEY_FILE`) → fail-closed. +10 unit tests (372 pass / 6 skip; also fixed `test_stop_continuation.py` fixture to defang via file path too). `.gitignore` extended. PLAN-0008 §Step 5 + STATUS amended. Auto-memory `project_claude_desktop_strips_anthropic_api_key.md` captured. **Live-verified inside Claude Code session**: empty env → file fallback → real Sonnet 3.04s round-trip → `proceed` decision (proof complete). **Bonus event**: my own L1 loop-detect hook (Step 2) fired on me during the 6 pragma-fix Edits — Cray ratified Bash sed workaround; hook works as designed | `3d4f98b` (PR #15) / `.claude/hooks/_sonnet_classifier.py` |
| 2026-05-24 | **PLAN-0008 Step 6 (Wave 2 completion — autonomy-triggers row flips + PLAN closeout) MERGED** — PR #14 → `main` (`626ab23`), single `docs(claude)` commit `aa64d19` + merge. Docs-only flip of `.claude/autonomy-triggers.md` row labels from placeholder / "Phase 2 spec" wording to **LIVE** with concrete hook attribution: G1/G2/G3/G4/C1/C2/C3 → `_sonnet_classifier.py`; L1–L4 → 3-hook attribution (gate + writer + reset); status banner + "How the classifier reads this file" §flipped to LIVE with conservatism-probe evidence; footer date bumped. PLAN-0008 §Step 6 amendment box rewritten as "Step 6 closeout" with PR #11/#12/#13 lineage. `.claude/settings.json` `_comment` corrected (stub removal happened in PR #13). 362 pass / 6 skip baseline preserved (docs-only; ruff/mypy no scope). Closeout: this STATUS row | `626ab23` (PR #14) / `.claude/autonomy-triggers.md` |
| 2026-05-24 | **PLAN-0008 Step 5 (Sonnet classifier + stub swap) MERGED + live conservatism proof + WSLENV permanent fix + session handoff to new Code** — PR #13 → `main` (`3407ae6`), single `feat(claude)` commit `ceebc1a` + merge. New `.claude/hooks/_sonnet_classifier.py` (~225 lines, stdlib urllib + 7 fail-closed paths + retry + markdown-fence extractor; pin `claude-sonnet-4-6` per OQ-B). Stop hook stub replaced via lazy-import `_classify()` wrapper with double-fallback. 17 mocked tests + 1 live opt-in (362 pass / 6 skip). **LIVE conservatism proof (Cray 2026-05-24):** bare Stop = proceed; G1/G2/C2 triggered scenarios = pause with correct row IDs; routine work = proceed. Total ~$0.005 cost. **WSLENV permanently extended** with `ANTHROPIC_API_KEY/u` so future sessions inherit the key without workaround. **Session-10 ↔ next-session handoff** at `.claude/handoffs/session-10/2026-05-24-2030-code-step5-merged-step6-kickoff.md` — Cray-directed to preserve context-window headroom + double-test WSLENV propagation from clean process tree. Closeout: this STATUS row | `3407ae6` (PR #13) / `.claude/hooks/_sonnet_classifier.py` |
| 2026-05-24 | **PLAN-0008 Step 4 (Stop hook + L1 turn-boundary reset, expanded scope) MERGED** — PR #12 → `main` (`b09bf39`), single `feat(claude)` commit `010ae1b` + merge. 5-piece bundle: stop_continuation.py (Stop hook with re-entry guard + L1 turn-boundary reset + chain depth + cap-hit policy + classifier stub) + _loop_counter.py amendment (turn_touched field + 3 helpers) + observer amendment (records turn_touched on Write/Edit) + early Wave-2-partial settings.json wire for Stop + 26 new tests. **🔴 L1 reset gap CLOSED** per Cray-ratified scope expansion (AskUserQuestion "Expanded (Recommended)"): Stop hook reads turn_touched and resets L1 counters whose targets were NOT touched this turn, implementing PLAN §Step 1's "untouched on next turn-boundary marker" semantic. Classifier inside Stop hook is stubbed (pause-by-default) until Step 5 lands real Sonnet helper. 346 pass / 5 skip (was 320 / 5; +26: 18 stop + 7 turn_touched + 1 observer). Closeout: this STATUS row | `b09bf39` (PR #12) / `.claude/hooks/stop_continuation.py` |
| 2026-05-24 | **PLAN-0008 Step 3 (PostToolUse progress observer + Wave 1 wire + PLAN amendment) MERGED + Step 4 prioritization for L1 reset gap** — PR #11 → `main` (`632a22c`), single `feat(claude)` commit `1c2a7b6` + merge. Wave 1 hooks live in `.claude/settings.json` (L1/L4 gate via Step 2 + L2/L3 inline Telegram via Step 3 + L4 increment-on-failure / reset-on-success). PLAN-0008 §Step 3 + §Step 6 amended with Wave 1/2 split rationale. **ELI-CTO review surfaced 🔴 L1 reset gap** (counter grows unbounded within session until Step 4 turn-boundary reset lands; Cray's STATUS.md iterative workflow at risk of false-positive deny — already 4 of 6 edits used pre-merge). Cray prioritized Step 4 with proper turn-boundary reset impl (not just Stop-hook stub). 31 new tests (pytest 320 / 5 skip). Closeout: this STATUS row | `632a22c` (PR #11) / `.claude/hooks/posttooluse_progress_observer.py` |
| 2026-05-24 | **PLAN-0008 Step 2 (PreToolUse loop-detect hook) MERGED + Wave 1/2 settings.json activation decision (Option C) RECORDED** — PR #10 → `main` (`9494f93`), single `feat(claude)` commit `ad2c047` + merge. New `.claude/hooks/pretooluse_loop_detect.py` (~185 lines) reads Step 1 state, gates L1 (Write/Edit ≥ 6 same file) + L4 (Bash ≥ 6 same tokenized command), fires Cray-E.4 Telegram payload + deny on trigger. L2/L3 explicitly NOT enforced at PreToolUse (2 lock-in tests; routed to Step 3 inline firing). Env-var overrides spoof-immune. 24 new tests with Telegram-stub fixture capturing real payload (pytest 289 / 5 skip). **Wave 1/2 decision (Cray-adjudicated 2026-05-24, Option C):** Step 3 PR wires Step 2 + Step 3 hooks together in `.claude/settings.json`; Step 6 PR wires Step 4 + Step 5 hooks. Rationale: L1/L4 standalone deployable + early smoke catches integration bugs + matches Phase 1 phased pattern. PLAN-0008 §Step 3 + §Step 6 will be amended in the Step 3 commit per documentation option (3). Closeout: this STATUS row | `9494f93` (PR #10) / `.claude/hooks/pretooluse_loop_detect.py` |
| 2026-05-24 | **PLAN-0008 Step 1 (loop-counter state module) MERGED** — PR #9 → `main` (`2b303a0`), single `feat(claude)` commit `e20a6f3` + merge. New `.claude/hooks/_loop_counter.py` (~340 lines, stdlib-only) ships the schema + atomic I/O + 4 normalization helpers (file path / pytest nodeid / error signature / bash command) + session-ID resolution per **OQ-A** + counter ops with `last_6_actions` ring buffer per Cray E.4 payload contract. Step 2 (PreToolUse loop-detect hook) READS this module's state; Step 3 (PostToolUse progress observer) WRITES it. 49 new tests (`tests/handoffs/test_loop_counter_state.py`) incl concurrent-write race; pytest 265 pass / 5 skip (was 216 / 5); ruff + mypy --strict + detect-secrets clean. Closeout: this STATUS row | `2b303a0` (PR #9) / `.claude/hooks/_loop_counter.py` |
| 2026-05-24 | **PLAN-0008 (Phase 2 harness autonomy layer) DRAFTED + MERGED** — PR #8 → `main` (`ec5e2ae`), 3 commits (`b53763d` draft + `5a34ab0` OQ resolutions + merge). Phase 2 layers probabilistic / classifier-mediated engine on top of Phase 1 deterministic hooks: `Stop` continuation loop (`stop_hook_active` + `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP=8`) + Sonnet pause/proceed classifier (fail-closed, pin `claude-sonnet-4-6`, reads `.claude/autonomy-triggers.md` verbatim) + stateful loop-detection L1–L4 via `.claude/state/loop-counter.json` (gitignored; payload `{loop_type, target, last_6_actions}` per Cray E.4). 4 ACs incl **AC-4 Phase 1 regression-free** (16-case bypass-immune commit-deny + handoff-validator + C4 stay green). All 7 OQs adjudicated by Cray (A/B/C/E/F/G approve Code recommendations; **D auto-handoff Code→Cowork DEFERRED to PLAN-0009** — K-1/K-2 forcing fact blocks Cowork read-side so auto-draft does not reduce the human-relay bottleneck ADR-013 §Context targets; Plan subagent = right author per ADR-013 D1; surface bloat = step-sized design comparable to classifier). Status: Ready for execution. Step 1 (`.claude/state/` design + loop-counter schema) next on `feat/plan0008-step1-state-design`. Cowork-drafted under interim ADR-009 D1 (ADR-013 D1 phasing); Code committed per ADR-009 D2 | `ec5e2ae` (PR #8) / `docs/plans/0008-harness-autonomy-layer-phase-2.md` |
| 2026-05-24 | **Research-path enforcement (C4 hook) MERGED** — PR #7 → `main` (`da4f91d`). New `.claude/hooks/pretooluse_research_path_deny.py` blocks `Write`/`Edit` under `docs/research/` outside `docs/research/private/**`. Third deterministic Phase-1 row in `.claude/autonomy-triggers.md` (C4, alongside G5 git-deny + H1 handoff-validator). Trigger = N=2 violations of the documented rule (`cowork_tab_instructions.md` line 192 + `.gitignore` lines 49-51) in 8 days: Lesson #5 §10.5 (2026-05-15, `docs/strategy/public/` drop) + 2026-05-23 (`chat_harness_extension_points_analyzed.md`, detected during PLAN-0007 post-merge cleanup). Applies ADR-013 D2 precedent (documented-rule violation twice → promote to deterministic hook). 20 new tests (216 pass / 5 skip total, +20 from baseline); Windows-UNC path-normalization robust to host (backslash→forward-slash before pathlib). Closeout: this STATUS row | `da4f91d` (PR #7) / `.claude/hooks/pretooluse_research_path_deny.py` |
| 2026-05-23 | **PLAN-0007 Phase 1 (Harness autonomy layer) MERGED** — PR #6 → `main` (`b2ea9b8`), 9 commits (6 Phase A + 3 Phase B). All three ACs green incl live: AC-2 bypass-immune commit boundary verified across 16 test cases (inline `CLAUDE_TIER=code` env-spoof attempt, `bash -c`, backtick chains, `git -C path`, env prefix, `&&` chains — all denied; legitimate Code-tier commit allowed); AC-1 AFK Telegram ping verified end-to-end by Cray after token rotation + `WSLENV` setup; AC-3 handoff frontmatter auto-validator blocks on hard errors. OQ-3 resolved by Code: env marker `CLAUDE_TIER=code` (rejected file marker spoofable by `touch && commit`, cwd heuristic too coarse, settings-scope has no per-session distinction). `.claude/autonomy-triggers.md` registry shipped with G1–G5 / C1–C3 / H1 active and L1–L4 loop-detect rows flagged "Phase 2 enforcement". Plan moved to `docs/plans/done/`. Phase 2–4 (Stop continuation loop + Sonnet classifier + stateful loop-detection + subagent topology + MCP bus) → PLAN-0008+ | `b2ea9b8` (PR #6) / `docs/plans/done/0007-harness-autonomy-layer-phase-1.md` |
| 2026-05-23 | **ADR-013 (Autonomy axis relocation, Direction B) ACCEPTED + PLAN-0007 committed + T3–T6 follow-ons landed** — Cray ratified Direction B in free-form and adjudicated E.1–E.5 + OQ-1/2/3 (OQ-3 PreToolUse session-identity mechanism delegated to Code). ADR-013 D1 amends ADR-009 D1 (execution-automation axis relocates to Code + subagents; Cowork retained as advisory governance drafter per OQ-1); D2 preserves + reinforces "only Code commits" via deterministic PreToolUse deny hook (bypass-immune); D3 extends ADR-012 (free-form venues retained); D4 classifier=Sonnet + registry `.claude/autonomy-triggers.md`; D5 Telegram `@vero_tg_bot` env-var token. Branch `feat/plan0007-harness-autonomy-phase1` carries 5 governance commits (`770adf5` ADR-013, `c00dc98` PLAN-0007, `c45526b` CLAUDE.md §6 T3, `e64a4d2` tier instructions T4, `8eebe09` ADR-009/012 pointers T5). CLAUDE.md edit (T3) is constitutional — restart-bridge applies (Lesson #5 §1). Cowork-drafted, Code-committed per ADR-009 D2 | `8eebe09` / `docs/adr/0013-autonomy-axis-relocation.md` + `docs/plans/0007-harness-autonomy-layer-phase-1.md` |
| 2026-05-22 | **PLAN-0006 (LLM reasoning-hook) MERGED** — PR #5 merged to `main` (`68053fe`): `recommend()` is now LLM-backed (`gpt-oss:20b`, two-call Pattern B, deterministic rule fail-safe retained), new `services/engine/llm/` package + eval harness; ADR-001 Amendment 1 rode the same PR. Code-reviewed, no blockers; 173 passed / 0 skipped, coverage 94.56%. Post-merge: worktree + branch cleaned up | `68053fe` (PR #5) |
| 2026-05-22 | **ADR-001 Amendment 1 — `gpt-oss:20b` recommender-path pin (PLAN-0006 TODO-A)** — amends ADR-001's Primary-multimodal row for the OCT recommender path only: `gpt-oss:20b` + Ollama 0.24.0 supersedes `gemma4:26b`. Two independent grounds — `gemma4:26b` cannot complete the recommender's real nested-schema structuring call (>600s timeout vs gpt-oss 41s), and the still-live Ollama #15260 `think`/`format` interaction. gemma4's vision/multimodal role + `qwen2.5-coder:32b` untouched; cloud-fallback posture unchanged. Cowork-drafted (ADR-009 D1), Code-reviewed + committed onto the PLAN-0006 branch (Cray's routing call); live digest `17052f91a42e` captured | `30d2c8e` / `docs/adr/0001-llm-model-baseline.md` |
| 2026-05-22 | **PLAN-0006 (LLM reasoning-hook execution) EXECUTED — the brain swap** — `recommend()` is now LLM-backed (two-call Pattern B on `gpt-oss:20b`, fail-safe to the retained rule path). New `services/engine/llm/` package (client/prompt/structured/trace) + eval harness. CHECKPOINT-0 pinned `gpt-oss:20b` on Ollama 0.24.0 (#15260 still live for Qwen3.x). SC-1 resolved (reduced `LlmJudgment` sub-schema; ADR-007 D2 envelope unchanged). A Step-7 live capture surfaced + fixed a `suggested_handler` defect. 8 commits on `feat/plan0006-llm-reasoning-hook` (unmerged); 168 passed / 5 skipped, coverage 94.56%. TODO-A (ADR-001 amendment for the pin) pending Cray | `4f13b50`..`2fe1056` |
| 2026-05-22 | **PLAN-0006 (LLM reasoning-hook execution) drafted + committed** — the execution plan for the ADR-010 brain swap; Cowork-authored (Tier 1), Code R2-reviewed (fact-pack verified vs the live repo). Cray adjudicated SD-1..SD-5: async `recommend()` + retry 3, two-call Pattern B trace, gpt-oss-20b primary (provisional, Step-0-gated), raw structured-output (no new dep), seam-only hosted fallback. Next = Phase-1 kickoff dispatch | `d3a781e` / `docs/plans/0006-llm-reasoning-hook-execution.md` |
| 2026-05-22 | **C-2 Suffix-enum divergence RESOLVED — option α (expand the enum)** — Cray adjudicated α: `tools/handoffs/_schema.py:Suffix` gains `dispatch`/`completion`/`consultation`; PLAN-004 D4 + `handoff-frontmatter-schema.md` register them; 2 regression tests. Closes the schema ↔ `cowork_tab_instructions.md` divergence. `discussion` deliberately excluded (ADR-012 carries it via `phase:`). | `db9c5ed` |
| 2026-05-22 | **ADR-012 (Cowork second free-form tier) ACCEPTED** — amends ADR-009 D5: Cowork gains a second free-form role (Tier-1b — repo-grounded discussion / thinking-partner / informal code review) alongside Chat, which is **retained** (D5 extended, not revoked). D2 routing: Chat = repo-blind blue-sky, Cowork = repo-grounded. Adopted by Cray as a guarded trial (option α), regression triggers R-FF1..R-FF4 as exit criteria; commit authority stays Code-exclusive. T1 ADR + T2-T6 follow-on amendments (cowork/chat instructions, ADR-009 D5 pointer, CLAUDE.md §6, this STATUS row) committed by Code | `7916b39` / `docs/adr/0012-cowork-second-freeform-tier.md` |
| 2026-05-22 | **ADR-010 (LLM reasoning-hook surface) ACCEPTED** — five decisions fixing how an LLM replaces the rule recommender: D1 local-LLM-default + Claude-API consent-gated fallback (Cray-ratified), D2 schema-constrained output + retry, D3 hybrid reasoning trace, D4 approval gate = guardrail, D5 `recommend()` LLM-backed under the same signature; ADR-007 D2 envelope unchanged. Drafted by Cowork from two Tier-0 briefs; next = PLAN-0006 | `48fe240` / `docs/adr/0010-llm-reasoning-hook-surface.md` |
| 2026-05-21 | **mypy pre-commit gate extended to `verticals/`** — the hook now covers `^(services\|verticals)/`, not just `services/`; closes the flagged coverage gap (verified `pre-commit run mypy --all-files`) | `9dd1470` |
| 2026-05-21 | **PLAN-0005 Phase 2 — OCT Engine Runtime Layer MERGED** (PR #4, 13 commits) — DataAdapter Protocol + RecommendedAction envelope + vertical registry + rule-based recommender/approval gate + energy synthetic adapter + persistence (real `postgres:16-alpine`, SQLAlchemy 2.0 async + Alembic) + three-layer API wiring + end-to-end action loop; 109 tests, coverage 95.34%; six §8 OQs honoured; DDL/ORM parity test (C-1/R6) green; PLAN-003 + PLAN-0005 moved to `done/` | `c646bab` (PR #4) / `docs/plans/done/0005-oct-engine-runtime-layer.md` |
| 2026-05-21 | **ADR-009 ACCEPTED + 7-commit atomic PR #3 MERGED (`08117d5`)** — Cowork becomes Tier-0+1 merged workspace (dispatch/ADR/PLAN authoring), Chat narrows to free-form discussion only (D5 b), commit authority stays Code-exclusive (D2), K-1/K-2 workflow codified durably (Lesson #8). Hypothesis from parent discussion (2026-05-20-1235) supported by round 1 + round 2 trials (PASS / PASS). Commits 7c5c728 (ADR-009) → 601cdd4 (ADR-007 pointer T7) → 6759949 (cowork_tab T3) → dd9fe76 (chat_tab T4) → b6bf400 (Lesson #8 T6) → af6f858 (CLAUDE.md §6 T2) → e9f499b (STATUS T5). **Cray TODO:** re-paste cowork/chat tier instructions into Claude Desktop UI (repo canonical, UI sync target per CLAUDE.md §4) | `08117d5` / `docs/adr/0009-cowork-tier1-tier-topology.md` |
| 2026-05-20 | **PLAN-003 Phase 1 merged** (PR #2) — `services/engine/` package + 5 emitters + `verticals/energy/ontology/energy_v0.yaml` (ADR-008 D2 grammar; 6 object_types + 7 link_types) + L1 commit-time gate + `vero-lite` entry-point; 24 engine tests; coverage 94.06%; ADR-008 D2 binding per dispatch R-K1; PLAN-003 §8.6 list-of-dicts illustration is REJECTED at L1 (schema-fidelity guarantee) | `30619b8` |
| 2026-05-20 | PLAN-003 Phase 1 kickoff dispatch authored by Cowork-as-Tier-1 (trial test-bed); Code R2 pre-execution PASS; mid-execution C4=0 (no Lesson #6 firings during commits 1-7); trial-protocol §7.3 adjudication queued for Cray | `.claude/handoffs/session-10/2026-05-20-1530-cowork-plan003-phase1-kickoff-dispatch.md` |
| 2026-05-20 | PLAN-003 plan doc landed — `docs/plans/0003-ontology-engine.md` (427 lines); Phase 1 only (5 emitters: Pydantic+SQL+JSON Schema+MCP+TS-light); Typer CLI + ruamel.yaml parser + jsonschema; Alert↔OperationalEvent via explicit join object type (ADR-008 D4 stays; `many_to_many` deferred); coverage ≥70% aspirational (R-8); 3 J-class surfaces logged in dispatch closeout | `a7c68a2` |
| 2026-05-20 | PLAN-004 Phase A Batch 2 COMPLETE — Step 2a (20 files) + 2b.1 (12 renames + ref-graph, 5-ratification surface→re-dispatch chain) + 2b.2 (post-recovery, single-pass). Handoff-class schema-FAIL = `{}` | `ad81e7e` (2b.2 anchor), `098f8cd` (2b.1), `7f5035f` (2a) |
| 2026-05-20 | Strategic pivot — Option-1: pause PLAN-004 Phase B/C, prioritize PLAN-003 (Ontology Engine = the moat) | Cray decision 2026-05-20 |
| 2026-05-20 | Chat dispatch tooling/schema pre-verification protocol codified (operational layer; durable Lesson #8 mint deferred post-Phase-A per Q3=A) | `be38bce` `docs/conventions/chat_tab_instructions.md` |
| 2026-05-19 | PLAN-004 v2 Phase A Batch 1 landed | Schema doc + tools/handoffs/{_schema,validate_handoff,handoff_status}.py + ≥14 tests + runbook cross-link + CLAUDE.md §10 widening (docs/ → docs/ + tools/, Option B per Code midflight) | `9afde79` |
| 2026-05-17 | §11 Transcript Handoff ratified — Lesson #5 §2 "Cray-direct constitutional codification path" sub-rule + runbook §4 refresh + runbook §2 helper | `8d570b4` |
| 2026-05-16 | CLAUDE.md §11 "Transcript Handoff" constitutional subsection promoted — first instance of Cray-direct codification path (Lesson #5 §2 sub-rule) | `dd65d9b` |
| 2026-05-16 | Transcript tooling + runbook landed — `tools/handoffs/render_transcript.py` (stdlib-only, mypy-strict) + tests + `docs/runbooks/transcript-handoff.md` | `98e5591` |
| 2026-05-16 | Lesson-numbering offset sweep — `Lesson #12/#13/#14` → `#2/#3/#4` across repo (full normalization) | `c85a595` |
| 2026-05-16 | Lesson #5 audit baseline applied — `docs/lessons/0005-tier-system-audit-2026-05-15.md` (10 findings, tier-system audit); in-repo references normalized | `8274a66` |
| 2026-05-15 | Governance mini-batch — CLAUDE.md §1 precedence + §6 4-tier table + §11 Tier 2 ops; `docs/conventions/{chat,cowork}_tab_instructions.md` canonicalized | `ac3baf3` |
| 2026-05-13 | ADR-007 (OCT engine contracts) + ADR-008 (YAML ontology specification) — both Accepted | `docs/adr/0007-oct-engine-contracts.md`, `docs/adr/0008-yaml-ontology-specification.md` |
| 2026-05-13 | Cowork Tier 0 first deliverable — Palantir Foundry ontology reference brief (validates ADR-008's 4-tier model; cited from ADR-008 §Context as influencing reference) | `docs/research/private/2026-05-13-palantir-ontology-reference.md` |
| 2026-05-11 | ADR-006 — Vertical Plugin Architecture (D1–D4 + 5 core patterns; template-first multi-vertical) | `docs/adr/0006-vertical-plugin-architecture.md` |
| 2026-05-11 | ADR-005 — Strategic Pivot from SMB vet clinic to Operational Control Tower (vet clinic parked as Phase 2) | `docs/adr/0005-strategic-pivot-to-oct.md` |
| 2026-05-10 | ADR-004 closed — GitHub noreply alias as canonical author email (provisional) | `docs/adr/0004-canonical-author-email.md` |
| 2026-05-10 | Worktree mode policy codified in CLAUDE.md §6 (per Lesson #3) | `CLAUDE.md` §6 |
| 2026-05-10 | Handoff rotation policy codified in runbook | `docs/runbooks/claude-code-chat-handoff.md` |

## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [x] **ADR-007** — OCT engine contracts (DataAdapter, RecommendedAction, three-layer wiring) *(Session 10 Batch 3)*
- [x] **ADR-008** — YAML ontology specification (5 base types, JSON Schema validation) *(Session 10 Batch 3)*
- [x] **`.gitignore` extension** — add `docs/research/private/` (Cowork closeout flag #1) *(Session 10 Batch 3-prep)*
- [x] **PLAN-0005 Phase 2 — OCT Engine Runtime Layer** — DataAdapter Protocol + RecommendedAction envelope + vertical registry + rule-based recommender/approval gate + energy synthetic adapter + persistence (postgres:16-alpine, SQLAlchemy/Alembic) + three-layer API wiring + e2e action loop; merged PR #4 (`c646bab`) *(Session 10, 2026-05-21)*
- [x] **ADR-010 — LLM reasoning-hook surface** — D1 inference backend Cray-ratified (local LLM default + Claude API consent-gated fallback); D2–D5 recommended; ADR-007 D2 envelope unchanged *(Session 10, 2026-05-22; commit `48fe240`)*
- [x] **PLAN-0006 — LLM reasoning-hook execution** — EXECUTED. Steps 0-8 of the Phase-1 kickoff dispatch done on `feat/plan0006-llm-reasoning-hook` (8 commits `4f13b50`..`2fe1056`, **unmerged**); CHECKPOINT-0 pinned `gpt-oss:20b` / Ollama 0.24.0; new `services/engine/llm/` package + eval harness; `ruff` + `mypy --strict` clean, 168 passed / 5 skipped, coverage 94.56%. Closeout: `.claude/handoffs/session-10/2026-05-22-2355-code-plan0006-kickoff-dispatch-closeout.md`. *(Session 10, 2026-05-22)*
- [x] **PLAN-0008 Step 5 — Sonnet classifier helper + stub swap (MERGED) + LIVE conservatism proof** — PR #13 → `main` (`3407ae6`); 4-piece bundle: new `_sonnet_classifier.py` (~225 lines stdlib urllib + Anthropic Messages API + 7 fail-closed paths + retry + markdown-fence extractor; pin `claude-sonnet-4-6` per OQ-B) + `stop_continuation.py` stub-swap via lazy-import `_classify()` wrapper + 17 mocked tests + opt-in live via `RUN_LIVE_SONNET_TESTS=1` (OQ-G). 362 pass / 6 skip; ruff + mypy --strict + detect-secrets clean. **LIVE verification:** bare Stop = proceed; G1/G2/C2 = pause with correct row IDs; routine work = proceed. Cost ~$0.005. WSLENV permanently extended with `ANTHROPIC_API_KEY/u`. **Step 6 next (Wave 2 completion):** autonomy-triggers row flips + closeout note — on NEW Code session via handoff `.claude/handoffs/session-10/2026-05-24-2030-code-step5-merged-step6-kickoff.md`. *(Session 10, 2026-05-24)*
- [x] **PLAN-0008 Step 4 — Stop hook + L1 turn-boundary reset, expanded scope (MERGED)** — PR #12 → `main` (`b09bf39`); 5-piece bundle: stop_continuation.py (Stop hook + L1 reset + chain cap + classifier stub) + _loop_counter.py turn_touched primitives + observer amendment + early Wave-2-partial settings.json wire + 26 new tests. **🔴 L1 reset gap CLOSED.** Classifier stub returns pause-by-default; Step 5 swap is single function replacement. 346 pass / 5 skip; ruff + mypy --strict + detect-secrets clean. **Step 5 next:** `_sonnet_classifier.py` (stdlib urllib + Anthropic Messages API + fail-closed pause) on `feat/plan0008-step5-sonnet-classifier`. *(Session 10, 2026-05-24)*
- [x] **PLAN-0008 Step 3 — PostToolUse progress observer + Wave 1 wire + PLAN amendment (MERGED)** — PR #11 → `main` (`632a22c`); bundle of writer hook (`posttooluse_progress_observer.py`, ~260 lines, `_apply_l2`/`_apply_l3`/`_apply_l4` helpers) + Wave 1 `.claude/settings.json` wire (Phase 1 + Step 2/3 hooks live) + PLAN-0008 §Step 3 + §Step 6 amendment boxes. L2/L3 inline Telegram fire on trigger; L1/L4 let Step 2 gate. Defensive Bash exit-code detection. 31 new tests; pytest 320 pass / 5 skip; ruff + mypy --strict + detect-secrets clean. **ELI-CTO surfaced 🔴 L1 reset gap (real op risk).** **Step 4 next (Cray-prioritized):** stop_continuation.py + L1/L3 turn-boundary reset + early Wave-2-partial Stop-hook wire — scope expansion under Cray surface. *(Session 10, 2026-05-24)*
- [x] **PLAN-0008 Step 2 — PreToolUse loop-detect hook (MERGED)** — PR #10 → `main` (`9494f93`); new `.claude/hooks/pretooluse_loop_detect.py` reads Step 1 state + gates L1/L4 ≥ 6 + fires Cray-E.4 Telegram payload + deny. Env-var overrides spoof-immune. L2/L3 explicitly deferred to Step 3 inline firing (2 lock-in tests). 24 new tests with Telegram-stub fixture; pytest 289 pass / 5 skip; ruff + mypy --strict + detect-secrets clean. **Wave 1/2 settings.json activation decision (Cray 2026-05-24, Option C):** Step 3 PR wires Step 2+3 hooks; Step 6 PR wires Step 4+5. **Step 3 next:** posttooluse_progress_observer.py + Wave 1 wire + PLAN amendment in one commit on `feat/plan0008-step3-posttooluse-progress-observer`. *(Session 10, 2026-05-24)*
- [x] **PLAN-0008 Step 1 — loop-counter state module (MERGED)** — PR #9 → `main` (`2b303a0`); new `.claude/hooks/_loop_counter.py` ships stdlib-only schema + atomic I/O + 4 normalization helpers (L1–L4) + session-ID resolution per OQ-A + counter ops with `last_6_actions` ring buffer. 49 new tests; pytest 265 pass / 5 skip; ruff + mypy --strict + detect-secrets clean. **Step 2 next:** `.claude/hooks/pretooluse_loop_detect.py` on `feat/plan0008-step2-pretooluse-loop-detect`. *(Session 10, 2026-05-24)*
- [x] **PLAN-0008 — Harness autonomy layer Phase 2 (DRAFT MERGED)** — PR #8 → `main` (`ec5e2ae`), 3 commits (`b53763d` draft + `5a34ab0` OQ resolutions + merge). Phase 2 scope: `Stop` continuation loop + Sonnet pause/proceed classifier reading `.claude/autonomy-triggers.md` verbatim + stateful loop-detection L1–L4 via `.claude/state/loop-counter.json`. 4 ACs incl AC-4 Phase 1 regression-free. All 7 OQs (A–G) adjudicated by Cray 2026-05-24 (Code recommendations approved; **OQ-D auto-handoff DEFERRED to PLAN-0009** per K-1/K-2 forcing fact + Plan subagent role + surface bloat). Status: Ready for execution. **Step 1 next:** `.claude/state/` design + `loop-counter.json` schema + `.gitignore` extension + atomic-write tests on `feat/plan0008-step1-state-design`. *(Session 10, 2026-05-24)*
- [x] **Research-path enforcement (C4 hook)** — MERGED. PR #7 → `main` (`da4f91d`); new `.claude/hooks/pretooluse_research_path_deny.py` deterministically blocks `Write`/`Edit` under `docs/research/` outside `docs/research/private/**`. Registered as C4 in `.claude/autonomy-triggers.md` next to G5 + H1. Trigger = N=2 documented-rule violations (Lesson #5 §10.5 + 2026-05-23 `chat_harness_extension_points_analyzed.md`) applying ADR-013 D2 precedent. 20 new tests; pytest 216 / 5 skip. *(Session 10, 2026-05-24)*
- [x] **PLAN-0007 — Harness autonomy layer Phase 1** — MERGED. PR #6 → `main` (`b2ea9b8`), 9 commits (6 Phase A governance: `770adf5` ADR-013 Accepted, `c00dc98` PLAN-0007, `c45526b` CLAUDE.md §6 T3, `e64a4d2` tier instructions T4, `8eebe09` ADR-009/012 pointers T5, `c048117` STATUS T6; 3 Phase B execution: `28fac01` telegram.sh, `711971c` settings + hooks + tests, `7c6ae65` autonomy-triggers registry). All ACs green incl live (AC-2: 16/16 bypass-immune tests; AC-1: live Telegram smoke verified by Cray; AC-3: handoff frontmatter auto-validator). OQ-3 resolved (CLAUDE_TIER=code env marker). Plan moved to `docs/plans/done/`. Closeout: `.claude/handoffs/session-10/2026-05-23-1606-code-plan0007-phaseB-closeout.md`. *(Session 10, 2026-05-23)*
- [x] **TODO-A — ADR-001 amendment (PLAN-0006 follow-on)** — DONE. ADR-001 Amendment 1 pins `gpt-oss:20b` + Ollama 0.24.0 for the recommender path (superseding `gemma4:26b` for that path only; gemma4's multimodal role + `qwen2.5-coder:32b` untouched). Cowork-drafted (ADR-009 D1); Code reviewed against the PLAN-0006 fact-pack + committed (ADR-009 D2) with the live `gpt-oss:20b` digest captured; rides the PLAN-0006 branch / PR #5 per Cray's routing call. *(PLAN-0006 kickoff dispatch §7 TODO-A; commit `30d2c8e`)*
- [x] **Suffix-enum vs cowork-instruction divergence** (PLAN-0005 §4 C-2) — RESOLVED via option α (expand the enum): `tools/handoffs/_schema.py:Suffix` gained `dispatch`/`completion`/`consultation`; PLAN-004 D4 + `handoff-frontmatter-schema.md` registered them; 2 regression tests in `test_schema.py`. `discussion` deliberately not added (ADR-012 carries it via `phase: discussion`). *(surfaced 2026-05-21; Cray adjudicated α 2026-05-22; `db9c5ed`)*
- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten (full table: PLAN-0005 §8.1): rule-based recommender → **ADR-010 ACCEPTED (2026-05-22) → PLAN-0006 next** (LLM reasoning hook); minimal approval gate → **ADR-011+** (audit framework — trigger: first design-partner data / PDPA review); no mapping layer → **dbt/SQLMesh** (trigger: first non-synthetic source); hand-authored ORM → **"ORM emitter"** Rule-of-Three candidate (trigger: 3rd vertical / DDL↔ORM parity-test drift); base Postgres only → **PLAN-002** (pgvector/AGE — trigger: semantic + graph features); explicit registry → **ADR-006 D3 L2** (trigger: vertical #2/#3 or `new-vertical` generator). *(per Cray note 2026-05-21)*
- [ ] **Phase-enum amendment** — add `consultation` (or equivalent Q&A-round value) to canonical Phase enum (Q15 of `2026-05-20-0245-code-plan003-pre-draft-consultation-reply.md`); requires touching `tools/handoffs/_schema.py` + `docs/conventions/handoff-frontmatter-schema.md` + validator tests; PLAN-004 Phase B adjacent. *(Deferred per R-9, 2026-05-20)*
- [ ] **Cleanup stale `ontology/README.md`** — 2026-05-05 PLAN-001 artifact; ontology directory canon now lives at `verticals/<name>/ontology/<name>_v0.yaml` per ADR-006 D1 / ADR-008 D5; superseded by PLAN-003. *(Deferred per R-9 cohort, 2026-05-20)*
- [ ] **PLAN-004 Phase B/C — DEFERRED (backlog, post-PLAN-003):** validator-scope exclusion (`README.md` / `_rename-map.md`, manifest §4.2/§6.1) + Cat G `references_*` autofix + Phase C handoff dashboard + OQ-2 systemic candidate (effective-vs-authored `status:` / archival flag so dead handoffs don't surface as actionable in the dashboard) + **validator warning-swallow bug** — `tools/handoffs/_schema.py` `_build()` (lines ~302–306) returns `Frontmatter` and discards its local `errors` list when no hard error exists, so `_check_unknown()` WARNING-severity findings (e.g. unknown field `brief-number`) are unreachable on otherwise-valid files; fix to surface warnings + add a regression test *(found 2026-05-22 dog-fooding the 4 Cowork LLM-hook handoffs; Cray routed → Phase B)*
- [ ] **ADR-NN (TBD, ≥ ADR-014) + PLAN-002** — Custom Postgres image with extensions (ADR-011 earmarked for the audit framework, ADR-012 taken, ADR-013 taken by autonomy axis relocation; floor bumped from ≥0013 to ≥0014 on 2026-05-23 per ADR-013 T6)
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (low priority)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)
- [x] Filesystem cleanup: `.claude/worktrees/sad-northcutt-6a48ff/` removed *(Session 10, 2026-05-21)*
- [x] **ADR-006** — Vertical Plugin Architecture *(Session 10 Batch 2)*
- [x] **ADR-005** — Strategic Pivot to OCT (vet clinic parked Phase 2) *(Session 10 Batch 2)*
- [x] **Directory scaffolds** — `verticals/{_template, energy, supply_chain, vet_clinic}/` + `docs/strategy/{public, private}/` *(Session 10 Batch 2)*
- [x] **Parked-note pass** — 6 vet-mentioning docs annotated *(Session 10 Batch 2)*
- [x] **ADR-004** — Canonical author email (GitHub noreply, provisional) *(Session 10)*
- [x] **Worktree mode policy** — codified in CLAUDE.md §6 *(Session 10)*
- [x] **Handoff rotation policy** — codified in runbook *(Session 10)*
- [x] **Phase G** — commit + PR + merge + cleanup *(Session 9)*
- [x] **Lesson #2 amendment** — Misdiagnosis section *(Session 9)*
- [x] **Lesson #3** — Code Tab worktree lifecycle traps *(Session 9)*
- [x] **File-based handoff mechanism** — `.claude/handoffs/` live *(Session 9)*
- [x] **Setup Claude Code on Windows** *(Session 8)*
- [x] **Cowork Project setup** *(Session 8)*
- [x] **PLAN-001** — Starter pack scaffold *(Session 4)*
- [x] **ADR-003** — Service port strategy *(Session 4)*
- [x] **Memory architecture implementation** *(Session 5)*
- [x] Lesson cleanup batch — Lesson #3 amendment + Lesson #5 §2/§3 amendment + Lesson #6 new *(done `96bf51b`, 2026-05-18)*
- [x] **PLAN-004 Phase A** — Batch 1 (schema + tools) + Batch 2 (2a: 20 files / 2b.1: 12 renames + ref-graph / 2b.2: post-recovery) complete *(Session 10, 2026-05-19/20; anchor `ad81e7e`)*
- [x] **PLAN-003 Phase 1** — Ontology engine + 5 emitters + `energy_v0.yaml` + L1 commit-time gate *(Session 10, 2026-05-20; merge `30619b8`, PR #2)*
- [x] Adopt Q1(b) closeout-template line "STATUS.md updated: yes/no/N/A" — adopted (closeouts carry the line)
- [x] Adopt Q3(b/c) dedicated `docs(status): …` housekeeping commit at batch close — adopted (`894a1e5` first instance; this 2b.2 close repeats)

## Next Steps

1. **PLAN-0008 Phase 2 — Step 6 execution (Wave 2 completion) — IN NEW CODE SESSION.** Step 5 (Sonnet classifier + stub swap) merged (PR #13 `3407ae6`) with live conservatism proof PASSED. **Step 6** per PLAN §Step 6: (a) flip the L1–L4 row entries in `.claude/autonomy-triggers.md` from "Phase 2 enforcement" placeholders to "Enforced via [hook name]" (matches the now-live Wave 1 + Wave-2-partial topology); (b) flip the G1/G2/C1/C2 + H1 row entries similarly where Wave 2 enforcement is now live; (c) confirm `.gitignore` carries `.claude/state/` (already done in Phase 1; verify); (d) update the registry footer line referencing classifier liveness; (e) PLAN-0008 §Step 6 closeout note marking Wave 2 complete. Branch: `feat/plan0008-step6-wave2-completion`. **NEW SESSION first action:** verify permanent WSLENV propagation — `wsl bash -lc '[ -n "$ANTHROPIC_API_KEY" ] && echo SET || echo UNSET'` should report SET (was UNSET in current session before today's setx). Then read handoff `.claude/handoffs/session-10/2026-05-24-2030-code-step5-merged-step6-kickoff.md`. Then Steps 7-8 (broader integration tests + live AC verification).
2. **PLAN-0008 Step 5 — MERGED.** [PR #13](https://github.com/CrayJThiemsert/vero-lite/pull/13) merged to `main` (`3407ae6`); `_sonnet_classifier.py` live; stub swapped; conservatism validated.
3. **PLAN-0008 Step 4 — MERGED.** [PR #12](https://github.com/CrayJThiemsert/vero-lite/pull/12) merged to `main` (`b09bf39`); Stop hook + L1 reset live; classifier stubbed.
4. **PLAN-0008 Step 3 — MERGED.** [PR #11](https://github.com/CrayJThiemsert/vero-lite/pull/11) merged to `main` (`632a22c`); writer hook + Wave 1 wire live; PLAN-0008 amended with Wave 1/2 split.
5. **PLAN-0008 Step 2 — MERGED.** [PR #10](https://github.com/CrayJThiemsert/vero-lite/pull/10) merged to `main` (`9494f93`); `pretooluse_loop_detect.py` gate live.
6. **PLAN-0008 Step 1 — MERGED.** [PR #9](https://github.com/CrayJThiemsert/vero-lite/pull/9) merged to `main` (`2b303a0`); `_loop_counter.py` state primitives live.
7. **PLAN-0008 — DRAFTED + MERGED.** [PR #8](https://github.com/CrayJThiemsert/vero-lite/pull/8) merged to `main` (`ec5e2ae`); plan lives at `docs/plans/0008-harness-autonomy-layer-phase-2.md` (will move to `done/` after Step 8 closeout).
8. **PLAN-0007 — MERGED + closed.** [PR #6](https://github.com/CrayJThiemsert/vero-lite/pull/6) merged to `main` (`b2ea9b8`); plan archived at `docs/plans/done/0007-harness-autonomy-layer-phase-1.md`.
9. **PLAN-0006 — MERGED + closed.** [PR #5](https://github.com/CrayJThiemsert/vero-lite/pull/5) merged to `main` (`68053fe`); plan archived at `docs/plans/done/0006-llm-reasoning-hook-execution.md`.
10. **PLAN-0005 §8.1 revisit register** — remaining deferred-foundational simplifications at their batch boundaries (audit framework → ADR-011+, mapping layer, ORM emitter, base-Postgres → PLAN-002 (≥ADR-014), registry discovery).
11. **Partner-trial readiness gaps** — `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` awaits a dedicated Cray discussion.
12. **Deferred (backlog)** — PLAN-004 Phase B (validator-scope exclusion; Cat G `references_*` autofix; validator warning-swallow bug) + Phase C (handoff dashboard); PLAN-002 custom Postgres image (≥ADR-014).
13. **Ongoing** — Continue exercising the file-based handoff mechanism (Chat ↔ Code ↔ Cowork) across batches.

## Update Workflow

This file is updated when:
- A commit changes project state significantly
- A new ADR/PLAN is minted or completed
- Active priorities shift
- A batch closes (sync `last_updated` + `current_batch` + `head_commit` + `recent_commits` frontmatter)
- A session closes (sync all frontmatter fields; archive batch history if needed)

**Update mechanism (locked per STATUS staleness batch 2026-05-18, Hybrid A+B short-term, C long-term):**

- **Per closeout (Option A + Q1(b) discipline):** Closeout drafter includes the line "STATUS.md updated: yes / no / N/A" in their closeout. If `yes`, the closeout's commit batch should include a dedicated `docs(status): …` housekeeping commit (Q3(b/c) pattern) bumping at minimum the `last_updated` and `head_commit` frontmatter fields.
- **Per batch boundary (Option B full body):** Full body refresh (Current Focus + Recent Decisions + Active TODOs + Next Steps) at batch close, alongside the frontmatter bump.
- **Per session boundary:** Full body + frontmatter sync; consider archive of prior session's batch history.
- **Future (Option C, PLAN-004 Phase A):** Validator will flag stale STATUS.md by comparing **frontmatter `last_updated` field** against newest closeout's `created` timestamp (NOT file mtime — mtime is defeated by side-effect commits, e.g. `c85a595` 2026-05-16 normalization sweep that touched STATUS.md body without bumping `last_updated`).

**Q4 `head_commit` semantics (codified 2026-05-18, locked Cray ratification of midflight `2026-05-18-1049` §4 + closeout `2026-05-18-1202` §6.2):**

- `head_commit` = short SHA of the newest **substantive** commit on
  `origin/main` that STATUS.md content reflects.
- **Excluded from `head_commit`:** `docs(status): …` housekeeping
  commits. These commits encode no new repo state — they ARE the
  STATUS.md freshness marker. Including them in `head_commit` creates
  a self-defeat where every housekeeping commit makes STATUS.md appear
  "fresh" to Q4 detection regardless of substantive backlog.
- **Substantive (included in `head_commit`):** everything else —
  `docs(lessons):`, `docs(adr):`, `docs(runbook):`, `feat:`, `fix:`,
  `chore:` (when changing meaningful state), `refactor:`, `test:`, etc.
  Any commit type that changes durable repo content updates
  `head_commit` at the next STATUS.md edit.
- **Reader recipe (returning after a pause):**

  ```bash
  # Newest substantive commit on origin/main (the value head_commit should hold)
  git log -1 --format=%h --invert-grep --grep='^docs(status):' origin/main

  # Compare to STATUS.md head_commit field
  grep -E '^head_commit:' docs/STATUS.md
  ```

  If the two differ → STATUS.md content is stale relative to substantive
  repo state. If they match → STATUS.md is fresh.

- **Writer rule (at each STATUS.md update):** Set `head_commit` to the
  output of `git log -1 --format=%h --invert-grep --grep='^docs(status):' origin/main`
  *after* the substantive commits of the current batch land but *before*
  any `docs(status):` housekeeping commit (or, if the STATUS.md edit
  itself is in a substantive commit like `docs(lessons):`, set
  `head_commit` to that substantive commit's own SHA — which becomes
  knowable only post-commit, so the writer typically updates
  `head_commit` to the *most-recent prior substantive commit* and lets
  the next batch's first edit catch up).
- **Two failure modes this rule closes:**
  1. **mtime trap** (closeout `2026-05-18-1202` §2): side-effect commits
     that touch STATUS.md body without bumping `last_updated` (e.g.
     `c85a595` 2026-05-16 normalization sweep) leave the file mtime-fresh
     but semantically stale. A SHA in `head_commit` cannot drift this way.
  2. **Housekeeping self-defeat** (closeout `2026-05-18-1202` §6.2 +
     midflight `2026-05-18-1049` §4): if `head_commit` = own SHA, every
     `docs(status):` commit makes Q4 say "fresh" regardless of
     substantive backlog. Excluding `^docs(status):` from the comparison
     baseline closes this loophole.

Manually edited until Option C lands.
