---
last_updated: 2026-07-01T14:19:28+07:00
session: 91
current_batch: "hero-demo v1 governed→run→฿ COMPLETE (#495 scored_rule · #496 live layer C-1/C-2/C-3 · #497 C-4 toggle · C-5 live MS-S1 smoke Cray-approved, governed outcome == offline). Demo path done offline + live-verified."
current_actor: code
blocked_on: "Nothing blocking. hero-demo v1 complete. Remaining A1b (Steps 2/4 + AC-9) is offline (the offline tests are the gate, §8); any further live MS-S1 run is host-state — explicit Cray go. loop-dispatcher DISABLED."
next_action: "Close-out: PLAN-0044 A1b is NOT complete (Steps 2 [OQ-6 N≥2 marker] + 4 [rule_gate executor] + AC-9 remain) → the remaining non-demo-critical A1b work; verify PLAN-0045 AC then git mv → done/; the eventual PLAN-0044 Completion note + full-body STATUS reconcile at A1b CLOSE. Phase-3 product ADRs (generalize scored_rule data-access = the Q3 ontology-binding gap) deferred."
head_commit: b4c03a9
recent_commits: [b4c03a9, 0a48542, 52523df, 00b9a3c, 75e7e69, bfc4844, b8bbf03, ce15d59, 2ebe851, 1047499]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 91 (head_commit `b4c03a9`) — HERO-DEMO v1 "governed → run → ฿"
> path COMPLETE (offline + LIVE-verified) — three PRs merged (#495 `scored_rule`
> executor / #496 the live-run layer C-1/C-2/C-3 / #497 the C-4 live toggle) +
> a Cray-approved C-5 live MS-S1 smoke.** MILESTONE — the *demo path* is done;
> **A1b is NOT complete** (PLAN-0044 Steps 2/4 + AC-9 remain). **#495 (`2ebe851`,
> PLAN-0044 A1b Step 5) — the `scored_rule` per-kind executor:**
> `GovernanceActionExecutor._scored_rule` (SD-1=(a), mirrors `_doa_tier`) scores
> an emergency-sourcing step's candidate quotes by the typed `ScoredRule` and
> selects the winner **DETERMINISTICALLY** (same inputs → same pick; the LLM
> never selects) — and, unlike `_doa_tier` (which keeps base envelopes),
> **REPLACES the output with the selected entity carrying `amount` (unit_price ×
> qty) + currency**, closing the **§3 ฿-threading finding** (the shipped
> `ActionStepExecutor` dropped the entity's spend so the `approve` `doa_tier`
> had no amount). Scoring = criticality-as-event-weight amplifier (v1; weights
> provisional per ADR-0025 D2). **17 new tests.** **#496 (`52523df`) — the
> live-run layer (C-1+C-2+C-3):** C-1 (`bfc4844`) the Fastenal dataset
> (`operational_event.csv` + `quotation.csv` + adapter types); C-2 (`75e7e69`)
> the in-code Fastenal hero procedure (ladder-swap → **฿288k crosses into
> CONTROLLER**); C-3 (`00b9a3c`) `hero_demo/run.py` —
> `run_hero_governance_moment` drives the **REAL** loop
> (intake→judge→source→compliance→approve) through the orchestrator + AT-2
> executors, so the moment is **DERIVED by the run** (same audit contract as the
> offline builder, `source: "live-run"`). **3 new stub-client tests.** **#497
> (`b4c03a9`) — C-4 the live toggle:** `GET /demo/hero/governance?live=true`
> returns the live-run audit; `view-hero.js` gains a "Run live"/"Offline
> fixture" toggle + source-aware badge. **Host-state-FREE:** the `?live` path
> uses a deterministic advisory-LLM stub (`advisory_stub_factory`) — the
> *governed* decision is LLM-independent, so no MS-S1 hit per request.
> Preview-verified; **+1 endpoint test.** **C-5 live MS-S1 smoke — HOST-STATE
> EVIDENCE (this session, Cray-approved via AskUserQuestion):** warmed
> `gpt-oss:20b` on MS-S1 (192.168.1.133, verified present) and ran
> `run_hero_governance_moment` **ONCE** with the real `OllamaClient`. **Result
> (fresh on-disk this session — a live run, NOT re-derived):** the governed
> outcome is **IDENTICAL to the offline gate** — `SUP-RAPIDMRO → ฿288,000 →
> CONTROLLER (appr-controller)`, `sod.governed: true`, `scored_path:
> exception_policy`, `governed_decision: [doa_tier, sod]`. This confirms
> **governed ≠ generated LIVE** — the real LLM (advisory prose only) does not
> change the governed decision. This is **EVIDENCE** (the offline oracle stays
> the gate, CLAUDE.md §8); **no code shipped for C-5.** **NEXT (close-out):**
> A1b's remaining **non-demo-critical** work — **Steps 2** (`OQ-6` N≥2 marker) +
> **4** (`rule_gate` executor) + **AC-9**; verify PLAN-0045 AC then `git mv` →
> `done/`. **Owed at A1b CLOSE (not per-step):** the PLAN-0044 Completion note +
> a STATUS full-body reconcile. Phase-3 product ADRs (generalize the
> `scored_rule` data-access = the Q3 ontology-binding gap) deferred.
> **Standing:** `loop-dispatcher` stays **DISABLED**; MS-S1 cold (remaining A1b
> is offline, §8); AI-assisted (Claude Code, session 91), no `Co-Authored-By`
> per CLAUDE.md §7.

> **Session 91 (head_commit `788994d`) — HERO-DEMO PHASE 1 (the offline
> foundation) SHIPPED + MERGED (#492 session-90 reconcile / #493 Phase-1
> foundation) → the "governed → run → ฿" demo path has a working offline
> spine.** MILESTONE, not closure — Phase 1 is the offline foundation only;
> the SD-1 live layer (C-full) is still WIP on `feat/hero-demo-v1-live` and
> **A1b is NOT complete** (AC-9 + PLAN-0044 Steps 2/4/5 remain). **#493
> shipped four commits (PLAN-0045):** **Step 1 (`85eafaa` — C1
> `FastenalCsvAdapter`):** a CSV-backed hero-demo `DataAdapter` in `verticals/`
> only, **zero `services/` core edit**. **Step 1b (`6fb7b2b`):** the
> governance-moment audit capture — `resolve_doa_tier` + `check_principal_sod`
> pulled from the **real engine** (not a re-implementation). **Step 3
> (`b76c080` — B1):** the ฿-impact ledger + the `/demo/hero/{governance,impact}`
> **derived API views** behind **4 demo guards**. **Step 2 (`f310778`):** the
> governance-moment render screen `view-hero.js` (render tab **G**).
> **Verification (attributed to the session-90 handoff evidence, NOT re-run
> this session — CLAUDE.md §6):** the offline gate was green (~2005 tests) and
> the change was verified live on the `oct-demo` preview — all 4 cards, both
> `governed_decision` joins JOIN, the contrast case = MANAGER, the ฿-ledger
> ฿9.76M → ฿1.65M. **§3 ฿-threading finding (the next move's driver):** the
> shipped `source` `ActionStepExecutor` returns action envelopes and **drops
> the input entity's amount**, so the `approve` `doa_tier` fails CLOSED at
> approve (no threaded ฿). **NEXT (Phase 2):** build **PLAN-0044 A1b Step 5**
> (`GovernanceActionExecutor._scored_rule` branch) on `feat/a1b-scored-rule` —
> score candidate quotes deterministically (LLM summarises only), select the
> winner, emit `amount`+`currency` onto the threaded entity so the `approve`
> `doa_tier` resolves; offline gate = **AC-7** (deterministic pick) + a
> full-loop stub-client test threading **฿288,000 → CONTROLLER**. Then merge →
> rebase `feat/hero-demo-v1-live` → **C-3** live runner → **C-4**
> endpoint/toggle → **C-5** live MS-S1 smoke (host-state, Cray go). **Owed at
> A1b CLOSE (not per-step):** the PLAN-0044 Completion note + `git mv` →
> `done/` + a STATUS full-body reconcile. **Standing:** `loop-dispatcher` stays
> **DISABLED**; MS-S1 cold (Phase-1/Step-5 build is offline, §8); AI-assisted
> (Claude Code, session 91), no `Co-Authored-By` per CLAUDE.md §7.

> **Session 89 (head_commit `f5527d9`) — A1b STEPS 3 + 6 (the rest of the
> demo-critical path) SHIPPED + MERGED (#488 `doa_tier` / #489
> `governed_decision`) + INDEPENDENTLY VERIFIED (J1/J2 PASS) → the
> DEMO-CRITICAL PATH IS COMPLETE ON MAIN.** MILESTONE, not closure — **A1b is
> NOT complete** (AC-9 + Steps 2/4/5 remain). With **Step 1 (#486, the live
> fail-closed SoD gate)**, all three structured fields the hero render joins on
> are now on main. **Step 3 (#488, `34be3a5` — AC-5):** a deterministic
> `doa_tier` per-kind executor — `resolve_doa_tier` walks the `DoaLadder`
> half-open band (`Decimal` spend → tier), resolves the tier's `approver_role`
> → a `Person`, and **fails CLOSED on a currency mismatch (OQ-4)**; the
> **SD-1 = (a) `GovernanceActionExecutor` wrapper** dispatches on
> `governance_content.kind` **without a new `StepKind`**. **Step 6 (#489,
> `f5527d9` — AC-8):** the typed, minimal **`governed_decision`
> audit-to-control field (SD-3 = (a))** — `ControlRef{kind,id}` +
> `GovernedDecision{control_ref, principal_id}` on `AuditMetadata`, emitted as
> an **ENGINE side-effect** by the `doa_tier` route
> (`{kind:'doa_tier', id:resolved_tier_id}`) and the SoD gate
> (`{kind:'sod', id:sorted distinct_steps}`); **join-stable keys** (the
> `Person` PK + the verdict-emitted control id). **Gate (offline = the binding
> bar, §8):** both ruff + mypy clean — **Step 3: 19 new `doa_tier` tests, full
> suite 1968 passed**; **Step 6: 5 new `governed_decision` tests + the SoD-gate
> DB emission** (the real hero gate emits
> `{kind:'sod', id:'approve+intake', principal_id:'appr-director'}`), **full
> suite 1973 passed / 5 skipped**. **Axis-B goal-gate: J1 PASS + J2 PASS**
> (independent goal-evaluator, creator≠critic intact, both steps). **AC-9
> DEFERRAL (surfaced for Cray, NOT silently applied):** the procurement
> `audit` step is authored `autonomy: auto` AND is downstream of the
> `approve` / `issue_po` gates, so the AC-9 "auto-downstream-of-a-gate"
> assertion would **restructure the hero procedure itself** — that is a Cray
> decision (restructure the procurement audit terminal vs exempt no-op
> terminals), not a mechanical assertion, so it is **held for adjudication**.
> **NEXT (the convergence move):** signal the parallel hero-demo session to
> converge — the demo-critical path is on main, so the
> `services/engine/procedures/*` hold releases and it can build the read-only
> governance-moment render. Then A1b's remaining **non-demo-critical** work:
> **AC-9** (the Cray option pick) + **Steps 2/4/5** (`OQ-6` N≥2 marker ·
> `rule_gate` · `scored_rule`). **Owed at A1b CLOSE (not per-step):** the
> PLAN-0044 Completion note + `git mv` → `done/` + a STATUS full-body
> reconcile. **Standing:** `loop-dispatcher` stays **DISABLED**; MS-S1 cold
> (A1b is offline, §8); AI-assisted (Claude Code, session 89), no
> `Co-Authored-By` per CLAUDE.md §7.


> _Rotation note (session-89 cont. reconcile, 2026-06-30): the **Session 87
> (head_commit `de36c2b`)** Current Focus block (PLAN-0041 — the classify-prompt
> enrichment lever — COMPLETE: offline gate #475/#476 + the Cray-gated live AC-7
> PASS on MS-S1 `gpt-oss:20b`; PLAN `git mv` → `done/`; the oldest in-window
> substantive block) was rotated to hold STATUS under the **R1 64 KB hard
> ceiling** (the file was at ~61.3 KB and the two new Session-89 A1b-Steps-3+6
> blocks — the CF block + the Recent-Decisions row — would cross it; R1 overrides
> the R2 4-session window) — moved verbatim to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md), per
> the STATUS.md Rotation Policy (R1/R2/R4). Resulting Current-Focus window = {89
> (Steps 3+6 `f5527d9`), 89 (Step 1 `719ea78`), 88}._

> _Rotation note (session-89 reconcile, 2026-06-30): the **Session 86 (head_commit
> `973ba69`)** Current Focus block (PLAN-0042 v1 — the O-3 AT-2 / managerial-layer
> BUILD — OFFLINE TAIL COMPLETE #470/#471/#472, Steps 1–3 + 5; the oldest in-window
> substantive block) was rotated to hold STATUS under the **R1 64 KB hard ceiling**
> (the file was at ~62 KB and the new Session-89 A1b-Step-1 block would cross it; R1
> overrides the R2 4-session window) — moved verbatim to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md), per
> the STATUS.md Rotation Policy (R1/R2/R4). Resulting Current-Focus window = {89, 88,
> 87}._

> _Rotation note (session-88 reconcile, 2026-06-30): the **Session 85 (cont.;
> head_commit `059c6ea`)** Current Focus block (PLAN-0042 — the O-3 AT-2 /
> managerial-layer BUILD — Steps 1–2 SHIPPED + MERGED #467/#468, closing the live
> run-gate blindness defect; the oldest in-window substantive block) was rotated to
> hold STATUS under the **R1 64 KB hard ceiling** (the file was at ~64.1 KB and the
> new Session-88 A1 block would cross it; R1 overrides the R2 4-session window) —
> moved verbatim to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md), per
> the STATUS.md Rotation Policy (R1/R2/R4). Resulting Current-Focus window = {88, 87,
> 86}._

> _Rotation note (session-87 reconcile, 2026-06-29): the **Session 85 (head_commit
> `21d7669`)** Current Focus block (PLAN-0042 — the O-3 follow-on AT-2 / managerial-layer
> BUILD PLAN — DRAFTED → Code R2 → Cray-RATIFIED → committed + merged #465; the oldest
> in-window substantive block) was rotated to hold STATUS under the **R1 64 KB hard
> ceiling** (the file was at ~63 KB and adding the new Session-87 PLAN-0041-COMPLETE block
> would cross it; R1 overrides the R2 4-session window) — moved verbatim to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md), per the
> STATUS.md Rotation Policy (R1/R2/R4). Resulting Current-Focus window = {87, 86, 85
> (cont. `059c6ea`)}._

> _Rotation note (session-86 reconcile, 2026-06-29): the **Session 84 (cont.;
> head_commit `f56a6e8`)** Current Focus block (the O-1 → O-3 arc off the Rock-4 research
> — Rock-4 deep research delivered, Cray locked O-1→O-3→O-2→O-4, O-1 Box-4 ฿ pitch DONE,
> **O-3 AT-2/managerial layer RATIFIED + COMMITTED as ADR-0025 #463 `f56a6e8` Accepted**;
> the oldest in-window substantive block) was rotated to hold STATUS under the **R1 64 KB
> hard ceiling** (the file was at ~61.7 KB and the new Session-86 PLAN-0042-v1-COMPLETE
> block would approach/cross it; R1 overrides the R2 4-session window) — moved verbatim to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md), per the
> STATUS.md Rotation Policy (R1/R2/R4). Resulting Current-Focus window = {86, 85 (cont.),
> 85}._

> _Rotation note (session-85 cont. reconcile, 2026-06-29): the **Session 84 (current;
> head_commit `7601174`)** Current Focus block (PLAN-0041 — the classify-prompt
> enrichment lever — RATIFIED + COMMITTED #461, plus the Four-Box strategy consultation
> that set the 4-rock roadmap; the oldest in-window block) was rotated to hold STATUS
> under the **R1 64 KB hard ceiling** (the file was at ~61.7 KB and adding the new
> Session-85-cont PLAN-0042-build block would approach/cross it; R1 overrides the R2
> 4-session window) — moved verbatim to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md), per the
> STATUS.md Rotation Policy (R1/R2/R4). Resulting Current-Focus window = {85 (cont.), 85,
> 84 (cont. `f56a6e8`)}._

> _Rotation-note ledger pruned (session-88 reconcile, 2026-06-30; extends the
> session-86 ledger-prune): the **session-85 / session-84-cont / session-83 /
> session-82 / session-81 reconcile** rotation notes (the Session-83 PLAN-0040 AC-B5
> live-intake block `ef46ea0`; the Session-82 PLAN-0040 Phase-C gate-UI block
> `d3c2279`; the Session-81/80 PLAN-0040 Phase-B+A blocks `8e11f82`/`42a0aa0`; the
> Session-79 PLAN-0039 viewer + harness-sharpening block `3eaf881`; the Session-78
> Stage-3-KICKOFF block `4e56d4b`) were removed from this live file to hold STATUS
> under the **R1 64 KB hard ceiling** and back toward the soft ceiling as the
> Session-88 A1 block landed. Like the session-79-and-earlier and the
> session-80-reconcile notes pruned at the session-83 / session-86 reconciles, they
> were pure archive-POINTER bookkeeping — the session blocks/rows they reference
> already live verbatim in
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md) and git
> history (Tier 3), so no content was lost. The session-88 / session-87 / session-86 /
> session-85-cont reconcile notes are retained above for continuity. Per the STATUS.md
> Rotation Policy (R1/R4)._

> _Rotation-note ledger pruned (session-86 reconcile, 2026-06-29; extends the
> session-83 ledger-prune): the two **session-80 reconcile** rotation notes (the
> Session-77 batch-2 + batch-3 CF blocks — Stage 2 ADR-016 D2 `facet:` amendment #428 +
> PLAN-0038 minted #429 `b2f19bc`; PLAN-0038 EXECUTED `777393c` #431/#432) were removed
> from this live file to hold STATUS under the **R1 64 KB hard ceiling** and back toward
> the soft ceiling. Like the session-79-and-earlier notes pruned at the session-83
> reconcile, they were pure archive-POINTER bookkeeping — the session blocks/rows they
> reference already live verbatim in
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md) and in git
> history (Tier 3), so no content was lost. The session-81/82/83/84-cont/85/85-cont/86
> reconcile notes are retained above for continuity; older notes remain in git history per
> the STATUS.md Rotation Policy (R1/R4)._
> _Rotation note (session-91 demo-close reconcile, 2026-07-01): the oldest
> **Recent Decisions** row — **2026-06-28 PLAN-0041 (classify-prompt enrichment
> lever) RATIFIED + COMMITTED (`7601174`, #461)** — was rotated out of the RD
> 10-row window to make room for the new session-91 hero-demo-v1-COMPLETE row,
> and moved verbatim to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md),
> per the STATUS.md Rotation Policy (R2/R4). No Current-Focus block was rotated
> this reconcile — the new session-91 demo-close block keeps the CF window at
> {91 (demo-close `b4c03a9`), 91 (Phase-1 `788994d`), 89, 89, 88} = 3 distinct
> sessions / 5 blocks, within the R2 4-session / 8-block window._

> _Older content rotates out of this file per the **STATUS.md Rotation Policy (R1-R6)** in [`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md) (Lesson #23): Current Focus keeps the 4 newest sessions (<=8 blocks); Recent Decisions keeps the last 10 rows. Rotated blocks/rows live in [`docs/status-archive/`](status-archive/) (sessions <=46: `2026-h1-current-focus.md`; 2026-06-10 onward: `2026-h1-status.md`) and git history (Tier 3)._

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

## Recent Decisions (last 10)

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-01 | **HERO-DEMO v1 "governed → run → ฿" path COMPLETE — offline + LIVE-verified (session 91)** — three PRs merged (#495/#496/#497) + a Cray-approved C-5 live MS-S1 smoke; MILESTONE (the demo path is done) NOT closure — **A1b is NOT complete** (PLAN-0044 Steps 2/4 + AC-9 remain). **#495 (`2ebe851`, A1b Step 5) `scored_rule` executor:** `GovernanceActionExecutor._scored_rule` (SD-1=(a), mirrors `_doa_tier`) scores an emergency-sourcing step's candidate quotes by the typed `ScoredRule`, selects the winner **DETERMINISTICALLY** (same inputs→same pick; LLM never selects) and — unlike `_doa_tier` — **REPLACES the output with the selected entity carrying `amount` (unit_price × qty) + currency**, closing the **§3 ฿-threading finding** (the shipped `ActionStepExecutor` dropped the entity's spend so `approve` `doa_tier` had no amount); scoring = criticality-as-event-weight amplifier (v1 weights provisional, ADR-0025 D2); **17 new tests.** **#496 (`52523df`) the live-run layer:** C-1 (`bfc4844`) Fastenal dataset (`operational_event.csv`+`quotation.csv`+adapter types); C-2 (`75e7e69`) the in-code Fastenal hero procedure (ladder-swap → **฿288k → CONTROLLER**); C-3 (`00b9a3c`) `hero_demo/run.py` `run_hero_governance_moment` drives the **REAL** loop (intake→judge→source→compliance→approve) through the orchestrator + AT-2 executors — the moment is **DERIVED by the run** (same audit contract, `source: "live-run"`); **3 new stub-client tests.** **#497 (`b4c03a9`) C-4 live toggle:** `GET /demo/hero/governance?live=true` returns the live-run audit; `view-hero.js` gains a "Run live"/"Offline fixture" toggle + source-aware badge; **HOST-STATE-FREE** (the `?live` path uses a deterministic advisory-LLM stub `advisory_stub_factory` — the governed decision is LLM-independent, no MS-S1 hit per request); preview-verified, **+1 endpoint test.** **C-5 live MS-S1 smoke (this session, Cray-approved via AskUserQuestion, HOST-STATE EVIDENCE):** warmed `gpt-oss:20b` on MS-S1 (192.168.1.133, verified present) + ran `run_hero_governance_moment` **ONCE** with the real `OllamaClient` — **result (fresh on-disk this session, a live run NOT re-derived): governed outcome IDENTICAL to the offline gate** (`SUP-RAPIDMRO → ฿288,000 → CONTROLLER (appr-controller)`, `sod.governed: true`, `scored_path: exception_policy`, `governed_decision: [doa_tier, sod]`) → **governed ≠ generated confirmed LIVE** (the real LLM = advisory prose only, does not change the governed decision). Live = **EVIDENCE** (the offline oracle stays the gate, §8); **no code shipped for C-5.** **NEXT (close-out):** A1b's remaining non-demo-critical work = Steps 2 (`OQ-6` N≥2) + 4 (`rule_gate`) + AC-9; verify PLAN-0045 AC then `git mv` → `done/`. **Owed at A1b CLOSE (not per-step):** PLAN-0044 Completion note + a STATUS full-body reconcile. `loop-dispatcher` stays DISABLED; MS-S1 cold (remaining A1b offline) | `b4c03a9` (#497) / `2ebe851` (#495) / `52523df`·`00b9a3c`·`75e7e69`·`bfc4844` (#496) / `services/engine/procedures/{scored_rule,governance_step}.py` (`select_scored_supplier` + the `_scored_rule` branch) + `verticals/procurement/hero_demo/run.py` (`run_hero_governance_moment`) + `verticals/procurement/data/hero/{operational_event,quotation}.csv` + `services/api/routers/demo.py` (`/demo/hero/governance?live=true`) + `services/api/static/assets/view-hero.js` |
| 2026-07-01 | **HERO-DEMO PHASE 1 (offline foundation) SHIPPED + MERGED (#492 session-90 reconcile / #493 Phase-1 foundation) (session 91)** — MILESTONE, not closure: the SD-1 live layer (C-full) is still WIP on `feat/hero-demo-v1-live` and **A1b is NOT complete** (AC-9 + PLAN-0044 Steps 2/4/5 remain). **#493 = four PLAN-0045 commits:** **Step 1 (`85eafaa`)** C1 `FastenalCsvAdapter` (CSV-backed hero-demo `DataAdapter`, `verticals/` only, **zero `services/` core edit**); **Step 1b (`6fb7b2b`)** the governance-moment audit capture (`resolve_doa_tier` + `check_principal_sod` from the **real engine**); **Step 3 (`b76c080`, B1)** the ฿-impact ledger + the `/demo/hero/{governance,impact}` **derived API views** behind **4 demo guards**; **Step 2 (`f310778`)** the governance-moment render screen `view-hero.js` (render tab **G**). **Verification (attributed to the session-90 handoff evidence, NOT re-run this reconcile — CLAUDE.md §6):** offline gate green (~2005 tests) + verified live on the `oct-demo` preview (all 4 cards, both `governed_decision` joins JOIN, contrast case = MANAGER, ฿-ledger ฿9.76M → ฿1.65M). **§3 ฿-threading finding:** the shipped `source` `ActionStepExecutor` returns action envelopes + **drops the input entity's amount** → the `approve` `doa_tier` fails CLOSED at approve. **NEXT (Phase 2):** PLAN-0044 A1b Step 5 (`GovernanceActionExecutor._scored_rule`) on `feat/a1b-scored-rule` — deterministic quote scoring (LLM summarises only), select winner, emit amount+currency so `approve` resolves; offline gate = AC-7 + a full-loop stub-client test threading ฿288,000 → CONTROLLER; then merge → rebase `feat/hero-demo-v1-live` → C-3 runner → C-4 endpoint/toggle → C-5 live MS-S1 smoke (host-state, Cray go). **Owed at A1b CLOSE (not per-step):** PLAN-0044 Completion note + `git mv` → `done/` + a STATUS full-body reconcile. `loop-dispatcher` stays DISABLED; MS-S1 cold (offline) | `788994d` (#493) / `85eafaa`·`6fb7b2b`·`b76c080`·`f310778` / `verticals/procurement/data_adapter/fastenal_csv.py` + `verticals/procurement/hero_demo/{governance_audit,ledger}.py` + `services/api/{models,routers}/demo.py` (`/demo/hero/{governance,impact}`) + `services/api/static/assets/view-hero.js` |
| 2026-06-30 | **A1b STEPS 3 + 6 (the rest of the demo-critical path) SHIPPED + MERGED (#488 `doa_tier` / #489 `governed_decision`) + independently verified (J1/J2 PASS) → the DEMO-CRITICAL PATH IS COMPLETE ON MAIN (session 89)** — MILESTONE, not closure: **A1b is NOT complete** (AC-9 + Steps 2/4/5 remain). With **Step 1 (#486, the live SoD gate)**, the hero render now has all three structured fields it joins on. **Step 3 (#488, `34be3a5`, AC-5):** a deterministic `doa_tier` per-kind executor — `resolve_doa_tier` over the `DoaLadder` half-open band (`Decimal` spend → tier), resolves the tier's `approver_role` → a `Person`, **fails CLOSED on a currency mismatch (OQ-4)**; the **SD-1=(a) `GovernanceActionExecutor` wrapper** dispatches on `governance_content.kind` **without a new `StepKind`**. **Step 6 (#489, `f5527d9`, AC-8):** the typed minimal **`governed_decision` audit-to-control field (SD-3=(a))** — `ControlRef{kind,id}` + `GovernedDecision{control_ref, principal_id}` on `AuditMetadata`, emitted as an **ENGINE side-effect** by the `doa_tier` route (`{kind:'doa_tier', id:resolved_tier_id}`) and the SoD gate (`{kind:'sod', id:sorted distinct_steps}`); **join-stable keys** (the `Person` PK + the verdict-emitted control id). **Gate (offline = binding bar):** both ruff + mypy clean — Step 3: **19 new `doa_tier` tests, full suite 1968 passed**; Step 6: **5 new `governed_decision` tests + the SoD-gate DB emission** (real hero gate emits `{kind:'sod', id:'approve+intake', principal_id:'appr-director'}`), **full suite 1973 passed / 5 skipped**. **Axis-B goal-gate: J1 PASS + J2 PASS** (independent goal-evaluator, creator≠critic intact, both steps). **AC-9 DEFERRAL (surfaced for Cray, NOT silently applied):** the procurement `audit` step is authored `autonomy: auto` AND downstream of the `approve`/`issue_po` gates, so the AC-9 auto-downstream-of-a-gate assertion would **restructure the hero procedure** — a Cray decision (restructure the audit terminal vs exempt no-op terminals), held for adjudication. **NEXT:** signal the hero-demo session to converge (the `services/engine/procedures/*` hold releases — it can build the read-only governance-moment render); then A1b's remaining non-demo-critical work = AC-9 (the Cray pick) + Steps 2/4/5 (`OQ-6` N≥2 marker · `rule_gate` · `scored_rule`). **Owed at A1b CLOSE (not per-step):** PLAN-0044 Completion note + `git mv` → `done/` + a STATUS full-body reconcile. `loop-dispatcher` stays DISABLED; MS-S1 cold (A1b offline) | `34be3a5` (#488) / `f5527d9` (#489) / `services/engine/procedures/{action_step,orchestrator}.py` + `services/db/models.py` (`AuditMetadata`/`GovernedDecision`/`ControlRef`) + `verticals/procurement/procedures.yaml` |
| 2026-06-30 | **A1b STEP 1 (demo-critical LIVE fail-closed principal-SoD run enforcement) SHIPPED + MERGED (#486) + independently verified (J1/J2 PASS) (session 89)** — INTERIM (1 of A1b's 6 steps; A1b NOT complete). Makes the A1a pure `check_principal_sod` fire on a REAL suspended-gate resolution. `spec.parse_procedures` now reads `principals`/`principal_aliases` (were silently dropped); procurement ships **5 authored principals + `required_roles`** (AC-10); a **`step_principals` JSONB column on `PipelineRun` (+ Alembic `0004`)**; `orchestrator.run_procedure(principal=…)` records the requester per SoD step (**SD-2=(a)**); `action_step.resolve_gated_step` invokes the check **unconditionally**, fails **CLOSED** (raises `PrincipalSoDError` with the structured verdict) **BEFORE** any approve/execute, **non-skippable**. **Inert for non-SoD procedures** (only procurement carries SoD; aquaculture inert-reconcile proves no behavior change). **Gate (offline = binding bar):** ruff + mypy clean; **1921 offline + 27 DB tests green** incl. **8 NEW live-SoD DB tests** + `alembic upgrade head` (0004) + aquaculture inert-reconcile. **Axis-B goal-gate: J1 PASS + J2 PASS** (high, independent goal-evaluator, creator≠critic intact). **Demo-convergence:** 1 of 3 demo-critical pieces of the hero-demo "governed→run→฿" path; **A1b Steps 3 (`doa_tier` executor) + 6 (`governed_decision` audit-to-control) next** = the rest of that path (offline-pure); Steps 2/4/5 (`OQ-6`·`rule_gate`·`scored_rule`) after; hero-demo session converges once the path is in. **Owed at A1b CLOSE (not per-step):** PLAN-0044 SD-1/SD-2/SD-3-as-rec disposition + a PLAN-0044 Completion note + a STATUS full-body reconcile. `loop-dispatcher` stays DISABLED; MS-S1 cold (A1b offline) | `719ea78` (#486) / `services/engine/procedures/{spec,orchestrator,action_step}.py` + `services/db/models.py` + `services/db/migrations/versions/0004_*.py` + `verticals/procurement/procedures.yaml` |
| 2026-06-30 | **A1 (run-time moat enforcement — Cray's #1 rock) LANDED (session 88): ADR-0026 Accepted #479 + A1a COMPLETE #481/#482 + A1b planned PLAN-0044 #484** — builds the principal-identity capability the AT-2 layer's run-time SoD was deferred on (the s85/s86 AC-13-ALT carry). **ADR-0026 Accepted (#479, `620d799`):** principal-identity + AT-2 run-time enforcement; all **6 OQs Cray-adjudicated as-recommended**. **PLAN-0043 (A1a) drafted + SD-1/SD-2 folded (#480, `05243eb`/`af0d882`):** Cray adjudicated **SD-1 = `required_roles` on `SoDConstraint`** + **SD-2 = a `PrincipalAlias` link object** (deviating from the drafted rec). **A1a COMPLETE end-to-end:** **Steps 1-3 (#481, `f1e7afa`)** = the `Person` / `PrincipalAlias` construct + `SoDConstraint.required_roles` + H-governance (new fields are governance, never on a draft type); **Steps 4-6 (#482, `f5c6342`)** = `services/engine/procedures/principal_sod.py`, the **fail-closed principal-SoD run-check** emitting a **STRUCTURED `PrincipalSoDVerdict`** + the `RunContext.principal` / `resolve_gated_step(principal=…)` seam + the offline oracle. **Gate: offline green — the full procedures suite 344 passed.** **A1a/A1b boundary (Cray s88):** the live invocation needs per-step principal RECORDING = the A1b executors' job; A1a ships construct + run-check + seam, A1b wires live enforcement. **A1b drafted = PLAN-0044 (in-flight, #484):** live run enforcement + per-kind executors (`doa_tier`/`rule_gate`/`scored_rule`) + audit-to-control (OQ-5); **3 SDs surfaced for Cray.** **Hero-demo dependency (parallel session):** A1's structured `PrincipalSoDVerdict` + the A1b OQ-5 audit field feed the hero-demo's read-only "governance moment" render (convergence ask #1 MET, #2 lands with A1b). In-flight PRs awaiting Cray merge: **#483** (PLAN-0043 → `done/`) + **#484** (PLAN-0044). `loop-dispatcher` stays DISABLED; MS-S1 cold (A1a offline) | `620d799` (#479) / `f1e7afa` (#481) / `f5c6342` (#482) / `docs/adr/0026-principal-identity-run-enforcement.md` + `docs/plans/done/0043-a1a-principal-identity-sod-runcheck.md` + `services/engine/procedures/principal_sod.py` |
| 2026-06-29 | **PLAN-0041 (classify-prompt enrichment lever) COMPLETE (session 87, #475/#476 + live AC-7 PASS)** — the fix for the PLAN-0040 AC-B5 ~1-in-3 false-abstain on a textbook AT-1/AT-3; a **PROMPT-ONLY** lever to lift the live AT-1-family classify match-rate. **Moat byte-identical** — the abstain-guard (`_archetype_disagreement`/`_AT2_ONLY_KINDS`/`_BAND_KINDS`, ADR-0024 D4/D7) unchanged; no schema change; **no new ADR**. **Steps 1-3 (#475, feat `035af38`):** `ArchetypeTemplate.description` (value-free, from the canonical catalog) + a 3-tuple classify catalog + a value-free `_BAND_EXPLAINER` into `build_classify_messages` (ends "When unsure … abstain" = the R2 moat-safety brake); offline gate AC-1..5 (guard byte-identity introspection; AT-2-only-abstain generalized to scored_rule/rule_gate/doa_tier; enriched-prompt introspection; descriptions-carry-no-AT2-vocab; schema pins the closed enum). **Step 4 (#476, test `d06d420`):** the OQ-C 26-narrative labelled fixture set + offline validators + a `@live`-gated before/after A/B harness routing both arms through the byte-identical imported guard (no production change); an independent adversarial moat-safety reviewer judged the set trustworthy; the pre-committed pass/fail read embedded in the harness (a docs/plans/ evidence doc was G2-gated → relocated into the test module). **Step 5 (live, AC-7, host-state — Cray go via AskUserQuestion):** the live before/after on MS-S1 `gpt-oss:20b`, N=3, worst reported — **PASS:** Arm A gated AT-1+AT-3 **8→11/11 (perfect, all 3 reps)** vs the ~7/11 PLAN-0040 reference; Arm B **11/11 abstain every rep** (zero AT-2 regression); **Arm-B guard paths = {label_abstain: 33}** (step_disagreement = 0 — the model labels AT-2 out-of-scope ITSELF, the deterministic backstop never needed to fire = no silent label→backstop shift); AT-1b 11/12 (reported, not gated). Live = **confirming evidence; the offline gate is the binding bar** (OQ-D). Raw log gitignored at `.claude/benchmark-results/plan0041-step5-live-ab.log`; thin tracked summary at `docs/logs/2026-06-29-plan0041-step5-live-ab.md` (two-artifact model). Gate (every step, offline): ruff + ruff-format + `mypy --strict services/` clean, **pytest 1891 passed / 25 skipped** (1877 baseline + 7 Steps-1-3 + 7 Step-4 validators; live test skipped offline). PLAN `git mv` → `done/`. `loop-dispatcher` stays DISABLED | `de36c2b` (#475/#476) / `services/engine/procedures/{archetypes/template,generator/{pipeline,prompts}}.py` + `tests/services/engine/procedures/{test_generator_pipeline,classify_enrichment_fixtures,test_classify_enrichment_fixtures,test_classify_enrichment_live}.py` + `docs/plans/done/0041-classify-prompt-enrichment.md` + `docs/logs/2026-06-29-plan0041-step5-live-ab.md` |
| 2026-06-29 | **PLAN-0042 v1 (O-3 AT-2/managerial layer) OFFLINE TAIL COMPLETE → v1 (Steps 1–3 + 5) COMPLETE (session 86, #470/#471/#472, all Cray-merged)** — the offline A1 tail of the AT-2/managerial build; PLAN `git mv` → `done/`. The AT-2 layer is now typed + run-gated + rendered authoritative (with the advisory band) + red-teamed offline. **Step 3a (#470, feat `4ff1180`):** the scoped value-only prose-lint over AT-2 free-text (`governance_prose_lint` = value classes + an approver-role-token check; OMITS the decision-verb + broad-identifier classes, finding 6) + a LOAD gate (`Procedure._validate_at2_free_text` blocks load on a ฿-amount/weight/role token smuggled into AT-2 free-text) + the 3 ADR-0025-D4 advisory NON-AUTHORITATIVE free-text fields (`EmergencyWaiverPolicy.justification`, `DoaTier.note`, `ScoredCriterion.note`); one reword (`"3-bid"`→`"three-bid"`). **Step 3b (#471, feat `5fac5d2`):** the PLAN-0039 read-only viewer renders the typed AT-2 content (DOA ladder/scored rule/compliance gate/SoD) as AUTHORITATIVE (the Box-3 "the gate is no longer blind" artifact, AC-13) + bands the AT-2 free-text "ADVISORY — NOT A CONTROL" (OQ-D); no API change (`model_dump` serializes it), verified live on the preview. **Step 4 (AC-13) = author + render only (A1)** — delivered by Step 3's render, no separate build. **Step 5 (#472, test `5464831`):** the D8 offline oracle `tests/services/engine/procedures/test_red_team_at2.py` consolidates the 3 red-team fixtures (hollow-but-complete → refused; leak-in-free-text → blocks load; identity-collapse role-level = single-step SoD rejected at construction + a missing-SoD `doa_tier` proc refused at the gate) + a positive control; PRINCIPAL-level collapse / literal `approver_role==requester_role` / un-gated-audit are A2-deferred (AC-13-ALT), documented + intentionally NOT asserted (no false coverage). Gate (every step, offline): ruff + ruff-format + `mypy --strict services/` (64 files) clean, **pytest 1877 passed / 24 skipped**, no live MS-S1. **AC-13-ALT (the A2 run path)** deferred to a follow-on PLAN, gated on a principal-identity-resolution capability the engine lacks today. OQ-B placeholder control values stay provisional (real Fastenal figures fold in via a small `verticals/`-only PR, B1; blocks nothing). `loop-dispatcher` stays DISABLED | `973ba69` (#470/#471/#472) / `services/engine/procedures/{spec,draft,orchestrator}.py` + `tests/services/engine/procedures/test_red_team_at2.py` + `services/api/static/assets/view-procedures.js` + `docs/plans/done/0042-at2-managerial-build.md` |
| 2026-06-29 | **PLAN-0042 (O-3 AT-2/managerial layer) Steps 1-2 SHIPPED + MERGED (session 85 cont., #467/#468)** — typed AT-2 content (D2) + the AT-2-aware run-gate (D5) closing the live blindness defect; the procurement AT-2 migrated prose→typed behind a green golden test; OQ-B=B2 values mirror the data adapter (provisional, pending Cray sign-off). **Step 1 (#467, `6176b18`):** discriminated `Step.governance_content` (`DoaLadder`\|`ScoredRule`\|`ComplianceGate`, keyed on `kind`) + `Procedure.separation_of_duties`; D3 bypass unrepresentable (`Decimal` money; closed `RelaxableConstraint` enum can't name compliance/SoD; `blocks_po`/`requires_justification` `Literal[True]`; total strictly-monotonic DOA ladder); D4 H-field invariants (new fields in `GOVERNANCE_FIELDS`, never on a draft type; draft-disjointness + `StepFacet`-unreachability CI). Finding 1 honored (DOA tiers nest in `DoaLadder`, no 2nd `Step.tiers`). **Step 2 (#468, `059c6ea`):** the AT-2-aware run-gate + the prose→typed migration in ONE PR behind the golden test — `validate_governance_complete` now owes typed `governance_content` on the AT-2 kinds + a `doa_tier` proc owes `separation_of_duties`; an empty-DOA/no-criteria/no-SoD AT-2 is no longer run-loadable (the negative hollow-but-complete regression = the D5 ratification gate). **Build interps:** principal-level SoD + resolved-tier strict-escalation deferred to **A2 (AC-13-ALT)** — no engine principal/role-rank layer; the author-time gate enforces the STRUCTURAL form (≥2 distinct steps; ladder totality). Gate: mypy --strict + ruff clean, **pytest 1843/24**; no live MS-S1. Remaining: Steps 3 (prose-lint + "ADVISORY — NOT A CONTROL" banding) + 5 (offline oracle), A1 | `059c6ea` (#467/#468) / `services/engine/procedures/{spec,draft,orchestrator}.py` + `verticals/procurement/procedures.yaml` |
| 2026-06-29 | **PLAN-0042 (the O-3 follow-on AT-2 / managerial-layer BUILD PLAN) DRAFTED + RATIFIED + MERGED (session 85, #465)** — the build PLAN ADR-0025 OQ-5 named; renders ADR-0025 (Accepted #463) D1–D8 + owns migration sequencing. **Build PLAN — no new ADR.** **Primary deliverable = closing a LIVE shipped defect:** `validate_governance_complete` is blind to AT-2 *content* (`rule_gate` evaluate → `[]`; `scored_rule`/`doa_tier` action → `[handler,autonomy]`, both filled → no AT-2-content obligation) → the build **types the AT-2 content** (D2 discriminated `Step.governance_content` union + `Procedure.separation_of_duties`), makes the **run-gate AT-2-aware** (D5), and **migrates the procurement AT-2 prose→typed in ONE PR behind a green golden test** (the migration trap). **Cray-ratified:** **OQ-A = A1** (author + render only — no principal-identity layer for run-time SoD, so D6 author+render fallback; the A2 run path deferred to a follow-on PLAN); **OQ-B = B2** (labelled-provisional placeholder control values + Cray sign-off — typing D2 is authoring not transcription); **OQ-C/D/E confirmed** (golden test + D5 migration in ONE PR; scoped value-only prose-lint + "ADVISORY — NOT A CONTROL" band; no per-spec `schema_version`). **Process:** Cowork-drafted (ADR-009 D1) → **Code R2** re-verified the fact-pack on HEAD `1305b32` + surfaced two substrate items: **finding 1** (a `Step.tiers` collision — `StepTiers` = PLAN-0022 handler taxonomy at `spec.py:264`, in `STEP_GOVERNANCE_FIELDS` → DOA tiers must nest in `DoaLadder`, never a 2nd top-level `Step.tiers`) and the **SoD principal-vs-role scoping finding** (A1 = author-time structural+role-level SoD; principal-identity SoD is run-time → relocated to the deferred **AC-13-ALT**, lineage = superseded-by-A1, not an ADR amendment) → Code revision dispatch → Cowork applied 3 surgical deltas → Cray-ratified → Code R2 + committed (#465). **v1 build surface = Steps 1–3 + 5** (A2 / AC-13-ALT deferred). `loop-dispatcher` stays DISABLED; MS-S1 cold, no live run (offline oracle is the gate). NEXT = execute Step 1 (D2 union + SoD + D3/D4) then Step 2 (D5 gate + migration in ONE PR; author the B2 placeholders) | `21d7669` (#465) / `docs/plans/0042-at2-managerial-build.md` |
| 2026-06-29 | **ADR-0025 (AT-2 / managerial-process layer) RATIFIED + ACCEPTED (session 84, #463)** — makes DOA/SoD/scored-rule/compliance governance first-class (the Box-3 "Action = contract" story the Rock-4 research found is vero-lite's strongest sellable box; Palantir's Apr-2026 "each Action is a contract" ≈ our `Agent.allowed` + gate + audit); **revisits ADR-0024 D7** (AT-2 deferral) + **decides ADR-0024 OQ-8** (typed content sub-model). **Re-framed around a SHIPPED DEFECT Code R2 verified live on HEAD:** `derive_governance_todo` owes no obligation for `scored_rule`/`rule_gate`/`doa_tier` → `validate_governance_complete` is blind to AT-2 content (an empty-DOA AT-2 is run-loadable today). **D2** authoritative discriminated `Step.governance_content` keyed to `gate_kind` (not the non-authoritative facet; D2-A4 held); **D3** bypass structurally unrepresentable (`Decimal` money; total-cover DOA ladder; strict-escalate waiver; compliance+SoD non-waivable); **D5** run-gate becomes AT-2-aware (closes the defect, + a negative regression test); **D7** the AT-2 generator stays deferred under a CI-enforced N≥2 re-trigger (AT-2 = N=1). **Cowork-drafted + a Cowork-run panel (disclosed self-review, NOT independent of the drafter) → Code R2 = the independent check (substrate fact-pack independently verified) → Cray-ratified per the recs** (OQ-1=(c) build-layer/defer-generator [the N=1 "(b)-minus-codegen" trade accepted because the defect forces typing the obligation regardless]; OQ-2=(b)-in-(a); OQ-3=D6 boundary [concrete run-vs-author → the follow-on PLAN]; OQ-4/5 per rec). A harness Stop-hook said "commit as Accepted" pre-ratification — Code **declined** (false attribution on the permanent record), held, committed on Cray's actual ratify. NEXT = the follow-on build PLAN (OQ-5, separate dispatch). Also s84: O-1 (Box-4 ฿ pitch artifact) done; the Rock-4 research delivered + the O-sequence locked | `f56a6e8` (#463) / `docs/adr/0025-at2-managerial-layer.md` |

## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13 (ratified `4d1347b`, #302; committed Proposed `e25281d`, #297 + instruction `e387a63`, #298 + R1 errata `655344d`, #300) — guarded trial under observation (parallel to ADR-012). A specialist Cowork project role-plays a Thai operator and emits a "partner profile package" to rehearse the intake+PDPA pipeline before a real partner; venue OUTSIDE the governance tiers (no commits / no repo mount / enters via Code receive). Three BINDING anti-circularity rules R1/R2/R3 (R3 SYNTHETIC provenance → never trips PLAN-0005 §8.1 / ADR-011 first-real-data trigger). All four venue SDs + dispatch-SD-1 ratified per Cowork rec (SD-1 N=3; SD-2 one-project-per-business-type; SD-3 size/region/maturity enums w/ energy·mid·th-regional·mixed-legacy default; SD-4 "what we refused to share" now required). D4 guarded-trial mirrors ADR-012 D5; regression triggers R-PS1..R-PS4 are the exit criteria; run 1 = energy operator (ADR-005 primary). **Now live-able: Cray launches run-1 (paste the R1-clean seed NOT the one-pager); ADR-011 audit framework stays gated on a partner conversation — the synthetic run INFORMS but never TRIGGERS it.**
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **Procurement vertical — GO + IN MOTION: PLAN-0036 (Fastenal, Stage 1) drafted + merged Draft (#412, `7a7c036`):** **GO** — Cray greenlit the 4th vertical (Procurement) and **PLAN-0036 (Fastenal procurement vertical, Stage 1) is drafted + merged Draft** (#412, head_commit `7a7c036`; Cowork-D1 + Code-R2 + committed D2, session 75). **Cray adjudicated SD-1…SD-5 = confirm-all** (2026-06-24, as-recommended). **Demo target = Fastenal Thailand** — automotive/auto-parts in the EEC; **hero** = asset-failure → governed emergency sourcing, **calm-path** = low-stock reorder. Stage 1 = a **PLAN-only, no-ADR pure-config plugin** on the shipped ADR-016 engine, **zero `services/` core edit** (CQ-1 confirmed, ADR-0023); the **SD-4 catch** = `services/engine/procedures/spec.py` `Step = ConfigDict(extra="forbid")` → Stage-1 facet annotations are **comment-only** (a first-class `facet` field = a Stage-2 ADR-016 amendment). It is the **proving ground** for the ultimate **3-phase generative-procedure platform** (generate / run / monitor); per Rule-of-Three it builds **no generic generator** (hand-author → extract schema Stage 2 → generator Stage 3). **NEXT = a new session flips PLAN-0036 Draft → Ready for execution (SDs confirm-all) then executes Stage 1.** *Supporting de-risk dossier (Cowork, session 72, 2026-06-22, `docs/research/private/`)* — **(1)** `2026-06-22-procurement-spec-expressiveness-probe.md` (procurement is **config-layer**, **0 new core amendments**; only engine pulls are the already-deferred ADR-016 Phase 2 / Phase 4+ items); **(2)** `2026-06-22-procurement-gtm-commercial-validation.md` (wedge = ops-triggered asset-aware procurement; econ buyer = CFO/Controller, champion = ops/procurement mgr; metric = **cycle-time**; ~$40K–150K/yr; 6-wk paid pilot); **(3)** `2026-06-22-procurement-asset-aware-incumbent-scan.md` (de-risk #1 — EAM/CMMS = nearest incumbent on the *trigger* only; white space = the **triple intersection** asset-trigger × governed sourcing × cross-vertical); **(4)** `2026-06-22-ai-sourcing-competitor-teardown.md` (de-risk #2 — Verusen/Keelvar/Fairmarkit/Arkestro/… triple intersection unoccupied; defensibility on **axis (a) asset-event trigger**; watchlist: **Verusen #1**, Fairmarkit, Coupa); **(5)** `2026-06-22-platform-incumbent-deepdive.md` (de-risk #3 — Palantir/Maximo/GE Vernova/SAP = capability-yes / product-no; moat = **packaging × ICP × price** = the **"Palantir-lite"** thesis, ADR-005, **governed ≠ generated**). **Pitch:** lead with asset-ontology-triggered governed sourcing + the native ontology (ADR-008) + engine (ADR-016) combination — **NOT** "governed"/"cross-vertical" (now commoditized claims).
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [x] **PLAN-0041 (classify-prompt enrichment lever — Rock 1) — COMPLETE (s87, offline gate #475/#476 + live AC-7 PASS, moat byte-identical).** The prompt-only fix for the s83 AC-B5 ~1-in-3 false-abstain: offline gate (#475 Steps 1-3 + #476 Step 4) + the Cray-gated live before/after on MS-S1 `gpt-oss:20b` (Arm A 8→11/11 all reps; Arm B 11/11 abstain; label_abstain 33/33, step_disagreement 0); the AT-2 cross-check stayed byte-identical, no schema change, no new ADR; the offline gate is the binding bar, live = confirming. PLAN `git mv` → `done/`. *(Cowork-D1 → Code-R2 → Cray-ratified → committed #461; executed Steps 1-5 Code-direct s87)*
- [ ] **Rock 2 / O-3 — AT-2 / managerial layer — ADR-0025 RATIFIED + ACCEPTED (#463, s84); next = the follow-on build PLAN.** The Box-3 "Action = contract" layer (DOA/SoD/scored-rule/compliance). **ADR-0025 (Accepted)** decided: type AT-2 content (D2 authoritative discriminated `Step.governance_content` keyed to `gate_kind`, not the facet), bypass structurally unrepresentable (D3), **close the live run-gate AT-2-blindness defect** (D5), **defer the generator** under a CI-enforced N≥2 re-trigger (D7; AT-2 = N=1). **NEXT = the follow-on build PLAN (OQ-5, separate Cowork dispatch):** type the content + the D5 gate-extension + the prose→typed migration of the existing procurement AT-2 in **ONE PR behind a green golden test** (⚠ the shipped AT-2 fails `validate_governance_complete` until typed). OQ-3 (run vs author-only) concrete v1 call lands in that PLAN. *(s84; ADR-0025; [[project_vero_ultimate_target_generative_procedures]])*
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (prepare-now / build-later, s84 roadmap).** (1) **Box 4 (Profit Formula):** the reasoning trace is operational, not economic — tie each action to ฿ impact (avoided outage / margin / ROI). Prepare by capturing the economic dimension as prose when hand-authoring Fastenal + proving the ฿ framing in the demo; type an economic-impact facet only after N≥3 verticals triangulate it. (2) **Q3 data-access gap:** a `query` step has no typed binding to an ontology object (today `input.from_step` is intra-step only; no read-side `Agent.allowed.object_types`) — the right design binds query steps to **ontology objects** (the mapping layer absorbs source diversity), NOT connectors-in-the-procedure. Both = generalized-schema work, post-Fastenal. *(s84 strategy discussion + the 3-layer / ontology-binding diagram)*
- [ ] **Rock 4 — Cowork deep research DELIVERED → O-sequence locked, O-1 done, O-3 Accepted (s84).** The 4-box + Palantir + agentic research landed (`docs/research/private/2026-06-28-rock4-4box-palantir-agentic-research.md`; ~48 sources, vendor-vs-independent tagged, adversarially balanced; central finding = the evidence asymmetry [bullish ROI all vendor, independent mostly skeptical]) → Cray **locked O-1 → O-3 → O-2 → O-4**. **O-1 (Box-4 ฿ pitch artifact) DONE** (conservative ฿ + impact-ledger mock; `docs/strategy/private/2026-06-28-box4-roi-spine-impact-ledger-pitch.md`). **O-3 = ADR-0025 Accepted** (see Rock 2). **Remaining:** **O-2** (economic-impact facet + Q3 ontology data-binding = Rock 3, after N≥3) · **O-4** (agent-interop North-Star, vision only). [[reference_rock4_4box_palantir_demo_research]]. *(s84 Cray ask)*
- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten (full table: PLAN-0005 §8.1): rule-based recommender → **ADR-010 ACCEPTED (2026-05-22) → PLAN-0006 next** (LLM reasoning hook); minimal approval gate → **ADR-011+** (audit framework — trigger: first design-partner data / PDPA review); no mapping layer → **dbt/SQLMesh** (trigger: first non-synthetic source); hand-authored ORM → **"ORM emitter"** Rule-of-Three candidate (trigger: 3rd vertical / DDL↔ORM parity-test drift); base Postgres only → **PLAN-002** (pgvector/AGE — trigger: semantic + graph features); explicit registry → **ADR-006 D3 L2** (trigger: vertical #2/#3 or `new-vertical` generator). *(per Cray note 2026-05-21)*
- [ ] **Demo card UX — "trust shape", NO operator confidence badge (s74 design, Cray-approved).** For the next demo round's operator recommendation card: show **what / grounded-why / approve gate** + a **"show full reasoning trace" toggle** that reveals the engine-view (where the floor-vs-judge agreement lives, labelled *audit/QA — not the operator*; reuses the scene-6 why-toggle pattern). **No operator-facing confidence badge** — the floor-vs-judge `confidence_signal` (PLAN-0035 Phase 2) is an **engine-internal QA/audit signal kept trace-only (SD-3 option A)**; surfacing it as a badge mis-reads as "the action might be wrong" (it is **not** — member (b) is advisory, never changes the action). The **(B) first-class `verification` envelope field is NOT needed for the operator UI** — reconsider **only** if a future internal audit/QA dashboard wants confidence as a first-class field (trace stays sufficient otherwise). Settled via a show_widget design review (s74; Cray: "ตรงใจ ตอบโจทย์"). The reframe: users want *what was decided · is it right · why* — answered by the action + grounding (real entity, allow-listed handler, deterministic detection, human approve) + the reasoning trace, **not** a self-reported confidence number. *(Trigger: the next demo / UI round; pairs with any (B) reconsideration.)*
- [ ] **PLAN-004 Phase C — OPTIONAL POLISH (forward-declared; "may never land"):** HTML/markdown handoff dashboard under `docs/` + references-graph (mermaid dispatch chains) + `render_transcript.py` unified session export (PLAN-0004 §"Phase C"). *(Phase A + B both COMPLETE — session 35; the prior TODO's validator **warning-swallow bug was FIXED #312**, s58. Minor never-formally-scoped sub-ideas — README/`_rename-map` walk-exclusion, Cat G `references_*` autofix, OQ-2 effective-vs-authored `status:` dashboard flag — fold in only if Phase C lands. Reconciled 2026-06-16 s65 audit.)*
- [x] **A1 — verify+reshape governance demo (B-γ moat successor) — DONE (s74).** The heaviest moat-proof: prove the moat IS governance — verify an LLM step's output for semantic consistency + reshape to the next step's contract (what arm (c) structurally lacks; ADR-016 area; the B-3 REPORT forward-points to it). **Scope together with the Phase-2 governed-entity-resolution ADR** — one ADR-016-area construct, not two overlapping ADRs. **UPDATE (s71):** that consolidation is DONE — **ADR-0022 (Accepted) D3-α already houses verify+reshape as member (b)**, so A1 = a PLAN to build member (b) (like PLAN-0030 built member (a)), at most an ADR-0022 amendment if a member-(b) design fork surfaces — NOT a new ADR. A2's residual decomposition (s71) shows the concrete A1 target: the 5 correct-action "assessment-prose" cases (verify the proposal states the action, reshape from the resolved handler). Sequenced AFTER the G2 root-fix (Cray, s71). **UPDATE (s73, cont.):** advanced END-TO-END — **SD-1 adjudicated = (c) Hybrid, phased** (Cray); **Phase 1 floor SHIPPED** (#403 `1c34125` — `services/engine/action_verification.py` at the `_compose_llm_record` seam; 1629 passed/22 skipped; AC-5 wrong-handler-not-rescued + D-6 held); the **(c) hybrid governance RATIFIED** (#404 ADR-0022 amendment [member (b) = hybrid, 7 constraints, local-LLM pin, scope = mechanism-only] + PLAN-0035 revision [Phase 1/2 restructure]; #405 `3625ea4` amendment ratified, SD-A1 = (i) inline). **UPDATE (s74) — DONE:** **Phase 2 (the advisory local-LLM-judge, Steps 8–12) SHIPPED** (#407, feat `5c7c175`) on the Phase-1 floor — the advisory judge (never overrides the surfaced action, ②) + deterministic agreement (③) + `verification_mode` degradation disclosure reusing the IN-4 / OllamaUnreachable path (④), gated behind `verification_judge_enabled` default-off (①); tests fake the judge (1639 passed/22 skipped). **PLAN-0035 flipped Draft → Complete + `git mv` to `done/` (`805f5d2`) — both phases of member (b) verify+reshape now shipped, the A1 arc closed end-to-end.** *(folded from §7 handoff, s67; PLAN drafted+merged s73; Phase 1 shipped + (c) ratified s73; Phase 2 shipped + A1 closed s74)*
- [x] **A2 — equal-rubric arm-(a) re-grade — DONE (s71, #392 + `2463229`).** Committed reproducible harness `benchmarks/procedure_comparison/regrade_arm_a.py` reproduces the full §B-3 A2 table (hardened 24→33/39→39/40→40; nudged 40/40/40), all-120 sanity assert green (every recomputed full-key grade matches the stored `proposal_correct`). §B-3 enriched with the handler-verified residual decomposition: the 7 hardened-reduced aquaculture misses = **5 correct-action** (`start_emergency_aerator`, prose framed as an "assessment" omitting the verb → the prose `action_keywords` check misses it) + **2 genuine wrong-action** (`increase_water_exchange`) → true wrong-action **2/40**. Finding: arm (a) ties-or-exceeds arm (c) once the rubric + prompt confounds are removed; the 5 prose-omission cases are the A1 verify+reshape target. *(folded from §7 handoff, s67; closed s71)*
- [ ] **ORM-emitter per-vertical layout (B1-DP-1 follow-up; Cray-deferred s67).** B1 (PLAN-0031, #370) ships the ORM emitter writing energy's ORM to the **committed** `services/db/models.py` (via `code_generator._ORM_COMMITTED_DEST`) — the gitignored `verticals/<ns>/generated/` cannot host a runtime dependency. When a **2nd vertical needs its own ORM** (the Rule-of-Three trigger), decide the per-vertical layout: extend `_ORM_COMMITTED_DEST` to per-vertical committed modules **vs** un-ignore a per-vertical `generated/orm.py` (gitignore negation) + re-export. Premature to design now (one ORM today). *(Cray-deferred 2026-06-18)*
- [x] **G2 drafting-friction root-fix — PLAN-0034 FULLY COMPLETE — DONE (s72).** Step-5 prong-2 scope annotation merged (#399, `.claude/autonomy-triggers.md`; annotation `5daa0e0` / merge `0f56d24`) — Cowork-drafted (ADR-009 D1, K-1/K-2; Code declined the Stop-hook Code-direct override, applied byte-identical edits, committed). PLAN-0034 flipped **Ready for execution → Complete** + `git mv docs/plans/0034-*.md → docs/plans/done/` (`72f0deb`). SD-3 = (a) PLAN-only (no ADR amendment). The only residual is the **optional, non-blocking** Cray-gated live gold re-score (prong-1 behavioral proof, host-state — **NOT** an acceptance gate; the offline gate, green at #397, is the sole acceptance condition). Parked s63; hit AGAIN s66 + s67 + s68; DRAFTED s71 (#394); ratified all four SDs = (a) + core-implemented s71 (#396/#397). *(folded from §7 handoff, s67; s68 instance + classifier prong; drafted s71; ratified+implemented s71; closed s72)*
- [x] **Promote the "proceed vs Cowork-dispatch-file" routing standard — DONE (s68).** Promoted into **CLAUDE.md §6** ("Routing: proceed vs Cowork-dispatch", #376 / commit `1963282`) — **home changed from the tentative `docs/conventions/` to CLAUDE.md per Cray's 2026-06-19 decision** (strong binding). Cowork-drafted (ADR-009 D1), Code R2-reviewed + committed (D2). Private Auto-Memory slimmed to a pointer (SD-C); parked G2 root-fix preserved separately (line above, SD-D). *(folded from §7 handoff, s67; closed s68)*
- [ ] **ADR-NN (TBD, ≥ ADR-014) + PLAN-002** — Custom Postgres image with extensions (ADR-011 earmarked for the audit framework, ADR-012 taken, ADR-013 taken by autonomy axis relocation; floor bumped from ≥0013 to ≥0014 on 2026-05-23 per ADR-013 T6)
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (low priority)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)

## Next Steps

1. **PLAN-0005 §8.1 revisit register** — remaining deferred-foundational simplifications at their batch boundaries (audit framework → ADR-011+, mapping layer, ORM emitter, base-Postgres → PLAN-002 (≥ADR-014), registry discovery).
2. **Partner-trial readiness gaps** — `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` awaits a dedicated Cray discussion.
3. **Deferred (backlog)** — PLAN-004 Phase C only (optional polish: handoff dashboard / references-graph / unified export — Phase B complete s35, warning-swallow fixed #312); PLAN-002 custom Postgres image (≥ADR-014).
4. **Ongoing** — Continue exercising the file-based handoff mechanism (Chat ↔ Code ↔ Cowork) across batches.

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
