---
last_updated: 2026-07-03T12:34:11+07:00
session: 94
current_batch: "SESSION 94 CLOSED (2026-07-03) — ADR-0020 partner-sim trial COMPLETE end-to-end across both verticals (run-1 + run-2, receive+screen+rehearsal ×2, C-1..C-3 confirmed). Plus a concurrent-session demo-honesty fix (#520, ORM-not-Alembic). No open partner-sim debt."
current_actor: code
blocked_on: "Nothing blocking. Any live MS-S1 run is host-state — explicit Cray go. loop-dispatcher DISABLED."
next_action: "Session 94 closed; pick up at the session-94 CLOSE handoff. C-1..C-3 CONFIRMED (partner-sim run-2 open item closed). Next capability = a Cray pick: (b) the Q4 generic query executor PLAN · the paired v1 ontology batches (energy-v1 + supply-chain-v1, specs ready from both rehearsals) · the [GTM] pack (customer-demanded templates) · the standard-intake-form TODO (11 additions) · or other backlog."
head_commit: f63c975
recent_commits: [f63c975, 255627b, eb63692, 878b517, d544414]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 94 CLOSE, 2026-07-03 (head_commit `255627b` → `f63c975` — #520
> `fix(demo)` is SUBSTANTIVE per lint policy, merge `9314100`) — ADR-0020
> PARTNER-SIM TRIAL COMPLETE END-TO-END ACROSS BOTH VERTICALS; C-1..C-3
> input-state check now CONFIRMED, closing the last run-2 open item.**
> Session 94 (2026-07-01 → 2026-07-03) delivered the entire trial: run-1
> rehearsal (fork a, energy; #515), the D4 post-run-1 review →
> continue-with-adjustments + the #516/#517 R1-tighten, run-2 receive
> (supply-chain, S-1..S-6 PASS incl. the first live R-PS4 screen; #518), the
> run-2 rehearsal + 2-run cross-vertical synthesis (#519), and now C-1..C-3.
> **C-1..C-3 CONFIRMED 2026-07-03 (Cray Path-1 UI check, evidence-backed —
> `confirmed — prior intact`, not from memory):** C-1 no repo mount (the
> Cowork Context is the project's own workspace; only file = the project's
> CLAUDE.md-style instruction memory = the post-#516 persona contract, NOT the
> vero-lite repo CLAUDE.md; no ontology/schema; Memory empty; referenced files
> = the Cray-pasted, R1-permitted run inputs); C-2 post-#516 instructions
> (all 3 current fingerprints present, both old FAIL fingerprints absent); C-3
> no past-chats/knowledge (no reference-past-chats capability in this Desktop
> build; project-knowledge empty); identity = the project's latest batch reply
> is the landed run-2 package verbatim (already-screened + already-rehearsed).
> Full record: gitignored `docs/research/private/2026-07-02-partnersim-run2-receive-checklist.md`
> §C-1..C-3 addendum + the probe protocol `2026-07-03-partnersim-c123-probe-protocol.md`.
> **Trial durable outputs:** a designed-in-advance mapping-layer core spec (9
> classes recurring 2/2 verticals), two v1 ontology-batch specs (energy-v1 +
> supply-chain-v1), 6 band-expressiveness requirements → the generalized-schema
> thread, a GTM pack now carrying customer-demanded templates, and an 11-item
> intake-form addition set. Rule-of-Three holds (3rd data point = procurement
> or a first real partner before abstraction). **Concurrent-session fix (NOT
> this session's work — attributed factually):** #520 `fix(demo)` (`f63c975`,
> merge `9314100`) corrected the demo story appendix's generated-artifacts
> fan-out — it claimed a non-existent "Alembic migrations" emitter, but
> `generate_all()` in `services/engine/code_generator.py` has six emitters
> (pydantic/sql/jsonschema/mcp/typescript/orm) and no migration emitter, so the
> false `alembic` node was swapped for the real `orm` emitter
> (`services/db/models.py`); Alembic migrations stay hand-authored, kept in
> lockstep by the schema-parity test. Touched `view-story.js` + `index.html`
> (cache token c24→c25); stakeholder-facing honesty fix, no engine/schema
> change. Session-94 CLOSE handoff:
> `.claude/handoffs/session-94/2026-07-03-1234-code-session94-CLOSE-partnersim-trial-both-verticals.md`.
> **Standing:** `loop-dispatcher` stays **DISABLED**; MS-S1 cold (nothing
> touched it); AI-assisted (Claude Code, session 94), no `Co-Authored-By` per
> CLAUDE.md §7.

> **Session 94 cont., 2026-07-03 (head_commit `255627b` unchanged —
> WORKING-TREE EVENT, no commit; #518 was a `docs(status)` merge, excluded) —
> ADR-0020 PARTNER-SIM RUN-2 REHEARSAL COMPLETE — the run-1 fork-(a) pattern
> (intake/mapping/PDPA-RoPA) run FOR REAL against the cold-chain package + the
> 2-run cross-vertical synthesis; findings G1–G11 decomposed into tagged work
> items.** **Cray pick, 2026-07-03.** Deliverable (gitignored +
> SYNTHETIC-bannered, R3):
> `docs/research/private/2026-07-03-partnersim-run2-rehearsal-intake-mapping-pdpa.md`;
> offline throughout — no MS-S1 (stays cold), no server/port. **§1 Intake
> (round 2):** 6 asks survive 2/2 — **5 DELIVERED + ask-6
> CONDITIONAL-with-RECIPROCAL-ASKS** (they explicitly request our LI
> balancing-test + 72h processor→controller notification templates → run-1
> [GTM] items graduate to customer-demanded deliverables); identity wall +
> one-owner failure both recur (2/2); NEW: authority is ATTRIBUTE-CONDITIONAL
> (cargo value ≤฿300k, งานยา carve-out, release-on-gap data-quality rule).
> **§2 Mapping vs `supply_chain_v0.yaml` — the headline gap: NO equipment
> entity** (รถ 62 / ตู้ reefer 38 / logger ~140 homeless; ปรับ-setpoint actions
> homeless) → v1 needs `Equipment`/`Device` + link (G1); NO
> `measured_kind`/`quantity_bindings` at all (ADR-0021 Phase A landed
> energy-only, G2); BUT `cargo_type`/`facility_type`/`action_type` enums
> largely FIT (contrast with energy's failed `asset_type`). **4 NEW band-gap
> classes** (duration-qualified −15.5°C เกิน 45 นาที · two-sided corridor 2–8 ·
> per-contract SLA timers แจ้งลูกค้า ≤4 ชม. · context-scoped during-loading) →
> 6 band-expressiveness requirements across 2 runs route to the
> generalized-schema thread (G3); calibration/bias registry (per-device
> ×scale−offset paper cal, probe +0.4, room −1.2 "บวกในใจ") with a WORKED
> dual-stream example computed from the package's own RF-21 slice (~2.4–2.7°C
> systematic offset, trend agreement) (G6); multi-latency fusion +
> retro-reaudit policy (late TL-2/paper data can contradict a released verdict
> — the QA-07 release-on-gap case) (G5). §8.1 mapping trigger NOT tripped
> (synthetic). **§3 PDPA-RoPA (round 2):** RoPA-lite builds cleanly again; GPS
> = PII hard-bar → column-drop round 1 accepted + a prepared "เสนอวิธีมา"
> answer (15-min downsample + stop-strip + geofence-derived events only) (G8);
> role-level-audit pre-clearance posture now validated against a SECOND
> instrument type (contractual driver-agent agreement vs run-1's
> worker-committee); **cross-border payoff as designed** — the SG vendor-cloud
> transfer already exists on the controller side → DPA musts: ingest-source
> pinning (controller-pulled files), deletion-scope honesty (vendor-cloud
> copies non-guaranteeable), sub-processor disclosure (G7). **§4:** G1–G11
> tagged [MAP]/[ENG]/[GTM]/[INTAKE]/[DEFER] + routed; nothing starts a build;
> the paired v1 ontology batches (energy-v1 from run 1 + supply-chain-v1 =
> G1/G2/G11) are a natural small PLAN when scheduled. **§5 Cross-run synthesis
> (the trial's compounding payoff):** 9 classes recur 2/2 verticals =
> mapping-layer CORE (unresolvable principals, era-PK renumber+reuse, clock
> chaos, unit/calibration chaos, mutable/late history, single-person
> knowledge, multi-channel telemetry rows, structured refusals, 4–6-wk
> external-counsel window); vertical-specific kept 1/2 (watch, don't
> generalize); Rule-of-Three — the third data point comes from procurement or
> the first REAL partner before abstraction (ADR-006). **§6:** intake-form
> additions 8–11 (source ownership, sub-processor inventory, undocumented
> mental corrections, band-shape probes) extend run-1's seven → the
> standard-intake-form TODO. **R2:** an independent reviewer verified
> facts/arithmetic/schema/R3/consistency — **0 BLOCKER / 0 FIX / 4 NITs
> applied** (quote exactness, enum completeness, the partner's own
> inconsistent asset-count noted as an intake datum, refusal-count
> cross-reference pinned to the run-1 S-4 record). **NEXT (Cray-owned):**
> C-1..C-3 for the supply-chain project (still open, benign) + the next pick —
> (b) the Q4 generic query executor PLAN, the paired v1 ontology batches
> (energy-v1 + supply-chain-v1), the [GTM] pack (now customer-demanded
> templates), or other backlog. **Standing:** `loop-dispatcher` stays
> **DISABLED**; MS-S1 cold (nothing touched it); AI-assisted (Claude Code,
> session 94), no `Co-Authored-By` per CLAUDE.md §7.

> **Session 94 cont., 2026-07-02 (head_commit `255627b` unchanged —
> WORKING-TREE EVENT, no commit; #517 was a `docs(status)` merge, excluded) —
> ADR-0020 PARTNER-SIM RUN 2 (supply-chain) COMPLETE — synthetic cold-chain
> package received + screened: S-1..S-6 ALL PASS vs a pre-committed oracle,
> incl. the FIRST live R-PS4 context-bleed screen (clean); first-pass findings
> drafted (gitignored, R3).** Run launched by Cray in a FRESH project per SD-2
> with ALL THREE D4 adjustments applied: (i) the #516-tightened instruction,
> (ii) the R1-STRIPPED PDPA paste-variant, (iii) fresh project + a
> Code-authored run-start assembly
> (`docs/research/private/2026-07-02-partnersim-run2-runstart-paste.md`).
> Parameters: supply-chain / mid / **multi-site-sea** / mixed-legacy
> (multi-site-sea = Code's pick to force the cross-border PDPA surface run 1
> never touched). **Screen — S-1..S-6 ALL PASS vs the PRE-COMMITTED oracle**
> (`...run2-receive-checklist.md`, criteria fixed before the package existed):
> R3 banner verbatim ×2; S-2 under the SHARPER post-#516 detector found
> nothing (own duration-qualified rules, own action verbs "ปล่อย/กัก/ตีกลับ",
> own fields, decidedly non-schema-shaped); S-3 = 5 unsolicited facts (≥N=3) +
> heavy flaw classes; S-4 = 7 refusals w/ blockers; S-5 K-1 re-stamps; **S-6
> R-PS4 (first live context-bleed screen, run-2-specific): zero run-1/TWP
> specifics — clean.** No R-PS trigger fired. **Landed (gitignored, R3):**
> package
> `docs/research/private/2026-07-02-partnersim-run2-supply-chain-package.md`
> (fictional cold-chain operator "สุวรรณเย็น ทรานส์") + oracle/verdicts
> `...run2-receive-checklist.md` + the completion handoff (session-94, 1825).
> **First-pass value — new finding classes run 1 could not surface:**
> cross-border transfer ALREADY in flight (logger-vendor cloud @ Singapore, no
> PDPA terms; deletion non-guaranteeable → the DPA must handle third-party
> processor chains; the residency story flips from run-1's "straight win" to a
> real ss.28/29 design question); duration-qualified thresholds (−15.5°C เกิน
> 45 นาที, door >12 min, pharma no-grace) vs our instantaneous
> `in_file_band`; per-CONTRACT (not per-asset-class) bands; a per-device
> calibration registry (raw 0–4095 × paper cal sheets); GPS-as-PII w/ a
> column-drop counter-proposal + re-identification honesty; third-party
> data-ownership boundaries (JV board / shipping agent / vendor cloud).
> **Cross-run signal (2/2 verticals):** identity-unresolvable principals, PK
> renumber+reuse, clock chaos, single-person knowledge bottleneck, batch-only
> export — these graduate from energy quirks to the mapping-layer's
> must-handle core. **Watch items:** repeated messiness ARCHETYPES across runs
> (below the R-PS4 bar, partly instruction-example-driven — fixture-diversity
> watch for any run 3); the "unannotated bulk slice" ask only partially met
> (curated small samples again); C-1..C-3 for the NEW project requested from
> Cray, UNCONFIRMED — benign (no S-2/S-6 indicator fired). **NEXT
> (Cray-owned):** confirm C-1..C-3 for the new supply-chain project (2-min
> Desktop check, carried open) + the next pick — a full run-2 rehearsal (the
> run-1 fork-(a) pattern: intake/mapping/PDPA vs the cold-chain package), (b)
> the Q4 generic query executor PLAN, or the rehearsal-enriched backlog.
> **Standing:** `loop-dispatcher` stays **DISABLED**; MS-S1 cold (nothing
> touched it); AI-assisted (Claude Code, session 94), no `Co-Authored-By` per
> CLAUDE.md §7.

> _Rotation note (session-94 CLOSE reconcile, 2026-07-03): to hold STATUS
> under the **R1 64 KB hard ceiling** as the new Session-94 CLOSE CF block
> landed (the file was at ~63.6 KB before the addition; R1 overrides the R2
> 4-session window — the s93/s94 precedents accepted a narrowed window), one
> Current Focus block was rotated verbatim to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md):
> the **Session 94 (head_commit `eb63692` → `255627b`)** ADR-0020 D4
> POST-RUN-1 REVIEW block (#516 substantive, merge `cb161a4`). Resulting
> Current-Focus window = {94 CLOSE `f63c975`, 94 run-2 rehearsal, 94 run-2
> receive}; RD table = 9 rows (untouched). **Prior (session-94 run-2
> rehearsal reconcile, 2026-07-03):** rotated the **Session 94 (head_commit
> `eb63692`)** ADR-0020 partner-sim RUN-1 REHEARSAL (fork a) block
> (working-tree event, reconciled #515) to the same archive. Per the
> STATUS.md Rotation Policy (R1/R2/R4)._

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
| 2026-07-02 | **PLAN-0046 (Q3 read-side ontology-binding build) EXECUTED + COMPLETE + CLOSED (session 93 cont., #511 feat + #512 close; PLAN → `done/`)** — renders the Accepted ADR-016 Q3 amendment into code; **all 11 ACs met.** `StepInput.reads: list[str]` + `AgentAllowed.object_types` (both `extra="forbid"`, backward-compat: absent/empty = loads as today) + the NEW pure `validate_read_bindings` load-gate (SD-1 Option A — `validate_runnable` + its ~12 call-sites untouched) wired at both production pre-flight sites (`run_procedure` + `persistence.resume_run`; skipped, no ontology I/O, for reads-absent procedures); `reads` → `STEP_GOVERNANCE_FIELDS` (OQ-A) + a disclosed `lift_to_step` strip-hardening (`StepDraft` reuses `StepInput` → generated drafts physically strip `reads` to ABSENT, OQ-C C1 pattern) + CI tripwire. 12 new tests; ruff + `mypy --strict` clean; **full offline suite 2066 passed / 5 skipped.** Zero runtime-data-flow change; honest frame (LOCKED-9): declared ✔ · load-gated ✔ · execution-bound ✖. SD-2 = Option A (verticals stay absent; gate inert until opt-in). The Q4 generic run-consume query executor = a SEPARATE later PLAN. Offline-only, no host-state | `eb63692` (#512 close) / `878b517` (#511 feat) / `services/engine/procedures/` (spec + orchestrator + draft-lift) + `docs/plans/done/0046-*.md` |
| 2026-07-01 | **ADR-016 Q3 READ-SIDE ONTOLOGY OBJECT-BINDING AMENDMENT ACCEPTED (Rock 3 / O-2, #505) (session 93)** — an in-place ADR-016 D2+D3 amendment closing the read-side governance gap that mirrors the shipped write-side. Two commits: `915c344` (Proposed) + `cb7eb05` (fold ratified decisions → Accepted). **Decision (contract-first):** a typed `StepInput.reads: list[str]` read entry point (OQ-5: list not `str` — procurement `intake` reads 3 object types + joins); `Agent.allowed.object_types` mirroring `action_handlers`; **LOAD-time enforcement** (`reads ∈ ontology ∩ allowlist`, else refuse load) — **zero runtime-data-flow change.** **Honest enforcement frame (Cowork caught, Code-verified):** v1 = a typed read contract + a load-time consistency/scoping gate, **NOT** runtime-enforced parity — even write-side `action_handlers` is only pre-flight-checked in `validate_runnable`; teeth = declared==dispatched, gained read-side only at **Q4**. **Deferred:** the generic run-consume query executor → a fast-follow build PLAN (touches runtime flow + enrich/join steps); the Box-4 economic-impact facet → a self-cancelling **N≥3** marker (typed facet only; economic dimension prose-captured at authoring). **OQ-1..6/A ratified:** OQ-1 `StepInput.reads` · OQ-2 load-gate+reframe · OQ-3 `object_types` bounds `fetch_objects` only (links/events out of v1) · OQ-4 `where`=post-fetch · OQ-5 `reads:list[str]` · OQ-A `reads`/`object_types` H-governed (`object_types` auto-covered; add `reads` to `STEP_GOVERNANCE_FIELDS` = build-PLAN task) · OQ-6 `object_types` empty=unconstrained (backward-compat). **Three-lens process:** `plan-drafter` AUTHORED the amendment + folded the ratified decisions; Cowork Tier-1b independent second-perspective review (caught the parity over-claim + surfaced OQ-5); Code R2-verified on disk + committed; Cray ratified OQ-1..6/A. **Context:** the parallel hero compliance-swap (#506, `0b7efe4`) landed last session (swapped the hero-demo compliance stub for the shipped `rule_gate` executor; governed outcome unchanged). **Impl note for the build PLAN:** the load-gate must thread the vertical `OntologyMeta` into pre-flight (`validate_runnable(procedure, agent)` doesn't carry it today). **NEXT = the fast-follow build PLAN** (`StepInput.reads` + `Agent.allowed.object_types` + load-gate + `reads`→`STEP_GOVERNANCE_FIELDS` + tests); the generic query executor (Q4) = a separate later PLAN. **Routing:** the ADR-016 amendment authored by the in-harness `plan-drafter` (prong-2 exempt) → Code R2 + committed via `docs/adr` PR. `loop-dispatcher` stays DISABLED; MS-S1 cold (offline) | `cb7eb05` (#505 fold→Accepted) / `915c344` (#505 Proposed) / `docs/adr/0016-*.md` (D2 `StepInput.reads` + `Agent.allowed.object_types` + D3 load-gate) |
| 2026-07-01 | **PLAN-0044 A1b STEPS 2 + 4 MERGED (offline close-out; A1b STILL OPEN) (session 92)** — two PRs (#499 Step 4 / #500 Step 2); INTERIM, not closure — remaining A1b = **AC-9** (Cray decision owed) + the hero-demo compliance-harness→`rule_gate`-executor swap. **#499 (feat `a458142`, merge `05c9541`, A1b Step 4 / AC-6) the `rule_gate` per-kind executor:** NEW `services/engine/procedures/rule_gate.py` — pure `evaluate_compliance(gate, candidate)` reads the candidate's per-criterion `compliance` signal map (data-access = (a), mirrors `scored_rule`'s `candidate_quotes`) and **blocks the PO on ANY failed criterion** (candidate tagged non-`compliant` → dropped by the downstream `approve` `where: {compliant: true}` fan-out). **Non-waivable by type** (`blocks_po` `Literal[True]`; no pass-a-failed-rule path); **fails CLOSED** (non-mapping candidate / no `compliance` map → `RuleGateError`; absent-OR-false per-criterion signal fails that criterion). v1 does NOT evaluate the prose `spec` predicate (deferred to the A2 run path, ADR-0025 D2) — it enforces the GATE. NEW **`GovernanceEvaluateExecutor`** in `governance_step.py` (SD-1=(a) dispatching wrapper for the EVALUATE StepKind, sibling of `GovernanceActionExecutor`): its `rule_gate` branch tags each candidate `compliant` + audits (`governed_kind: rule_gate`), never the base (compliance has no numeric band) nor the LLM (governed ≠ generated, ADR-0019 IN-3); a banded `judge` step falls through to the shipped `EvaluateStepExecutor`; **17 new tests.** **#500 (test `12ac1dd`, merge `4f22602`, A1b Step 2 / AC-10 re-trigger half; mirrors ADR-0025 D7) the OQ-6 N≥2 shared-`Person` re-trigger marker:** NEW `test_principal_identity_retrigger.py` counts the verticals whose `procedures.yaml` ships `principals` and **FAILS the moment a SECOND vertical ships principals (N≥2)** — making the shared/core `Person` extraction deferral (ADR-0026 OQ-6=(b)) **self-cancelling** rather than a silent `# TODO`; currently N=1 (procurement only); **3 tests.** **Verification:** ruff + mypy clean; full offline suite **2020 passed / 5 skipped** (on merged main `4f22602`); offline-only, no host-state, **no PO issued** (render / block only, ADR-0007 LOCKED #3). **Routing:** both non-gated Code `feat/*`/`chore/*` PRs executing the already-accepted PLAN-0044 (no new PLAN/ADR). **NEXT:** AC-9 (Cray pick — the `audit` step is `autonomy:auto` AND downstream of `approve`/`issue_po`, so the assertion would restructure the hero procedure) + the hero compliance-swap follow-up; then the PLAN-0044 Completion note + `git mv` → `done/` + a STATUS full-body reconcile at A1b CLOSE. `loop-dispatcher` stays DISABLED; MS-S1 cold (remaining A1b offline) | `4f22602` (#500) / `05c9541`·`a458142` (#499 Step 4) / `services/engine/procedures/rule_gate.py` + `services/engine/procedures/governance_step.py` (`GovernanceEvaluateExecutor`) + `tests/services/engine/procedures/test_rule_gate.py` (Step 4) · `12ac1dd` (#500 Step 2) / `tests/services/engine/procedures/test_principal_identity_retrigger.py` |
| 2026-07-01 | **HERO-DEMO v1 "governed → run → ฿" path COMPLETE — offline + LIVE-verified (session 91)** — three PRs merged (#495/#496/#497) + a Cray-approved C-5 live MS-S1 smoke; MILESTONE (the demo path is done) NOT closure — **A1b is NOT complete** (PLAN-0044 Steps 2/4 + AC-9 remain). **#495 (`2ebe851`, A1b Step 5) `scored_rule` executor:** `GovernanceActionExecutor._scored_rule` (SD-1=(a), mirrors `_doa_tier`) scores an emergency-sourcing step's candidate quotes by the typed `ScoredRule`, selects the winner **DETERMINISTICALLY** (same inputs→same pick; LLM never selects) and — unlike `_doa_tier` — **REPLACES the output with the selected entity carrying `amount` (unit_price × qty) + currency**, closing the **§3 ฿-threading finding** (the shipped `ActionStepExecutor` dropped the entity's spend so `approve` `doa_tier` had no amount); scoring = criticality-as-event-weight amplifier (v1 weights provisional, ADR-0025 D2); **17 new tests.** **#496 (`52523df`) the live-run layer:** C-1 (`bfc4844`) Fastenal dataset (`operational_event.csv`+`quotation.csv`+adapter types); C-2 (`75e7e69`) the in-code Fastenal hero procedure (ladder-swap → **฿288k → CONTROLLER**); C-3 (`00b9a3c`) `hero_demo/run.py` `run_hero_governance_moment` drives the **REAL** loop (intake→judge→source→compliance→approve) through the orchestrator + AT-2 executors — the moment is **DERIVED by the run** (same audit contract, `source: "live-run"`); **3 new stub-client tests.** **#497 (`b4c03a9`) C-4 live toggle:** `GET /demo/hero/governance?live=true` returns the live-run audit; `view-hero.js` gains a "Run live"/"Offline fixture" toggle + source-aware badge; **HOST-STATE-FREE** (the `?live` path uses a deterministic advisory-LLM stub `advisory_stub_factory` — the governed decision is LLM-independent, no MS-S1 hit per request); preview-verified, **+1 endpoint test.** **C-5 live MS-S1 smoke (this session, Cray-approved via AskUserQuestion, HOST-STATE EVIDENCE):** warmed `gpt-oss:20b` on MS-S1 (192.168.1.133, verified present) + ran `run_hero_governance_moment` **ONCE** with the real `OllamaClient` — **result (fresh on-disk this session, a live run NOT re-derived): governed outcome IDENTICAL to the offline gate** (`SUP-RAPIDMRO → ฿288,000 → CONTROLLER (appr-controller)`, `sod.governed: true`, `scored_path: exception_policy`, `governed_decision: [doa_tier, sod]`) → **governed ≠ generated confirmed LIVE** (the real LLM = advisory prose only, does not change the governed decision). Live = **EVIDENCE** (the offline oracle stays the gate, §8); **no code shipped for C-5.** **NEXT (close-out):** A1b's remaining non-demo-critical work = Steps 2 (`OQ-6` N≥2) + 4 (`rule_gate`) + AC-9; verify PLAN-0045 AC then `git mv` → `done/`. **Owed at A1b CLOSE (not per-step):** PLAN-0044 Completion note + a STATUS full-body reconcile. `loop-dispatcher` stays DISABLED; MS-S1 cold (remaining A1b offline) | `b4c03a9` (#497) / `2ebe851` (#495) / `52523df`·`00b9a3c`·`75e7e69`·`bfc4844` (#496) / `services/engine/procedures/{scored_rule,governance_step}.py` (`select_scored_supplier` + the `_scored_rule` branch) + `verticals/procurement/hero_demo/run.py` (`run_hero_governance_moment`) + `verticals/procurement/data/hero/{operational_event,quotation}.csv` + `services/api/routers/demo.py` (`/demo/hero/governance?live=true`) + `services/api/static/assets/view-hero.js` |
| 2026-07-01 | **HERO-DEMO PHASE 1 (offline foundation) SHIPPED + MERGED (#492 session-90 reconcile / #493 Phase-1 foundation) (session 91)** — MILESTONE, not closure: the SD-1 live layer (C-full) is still WIP on `feat/hero-demo-v1-live` and **A1b is NOT complete** (AC-9 + PLAN-0044 Steps 2/4/5 remain). **#493 = four PLAN-0045 commits:** **Step 1 (`85eafaa`)** C1 `FastenalCsvAdapter` (CSV-backed hero-demo `DataAdapter`, `verticals/` only, **zero `services/` core edit**); **Step 1b (`6fb7b2b`)** the governance-moment audit capture (`resolve_doa_tier` + `check_principal_sod` from the **real engine**); **Step 3 (`b76c080`, B1)** the ฿-impact ledger + the `/demo/hero/{governance,impact}` **derived API views** behind **4 demo guards**; **Step 2 (`f310778`)** the governance-moment render screen `view-hero.js` (render tab **G**). **Verification (attributed to the session-90 handoff evidence, NOT re-run this reconcile — CLAUDE.md §6):** offline gate green (~2005 tests) + verified live on the `oct-demo` preview (all 4 cards, both `governed_decision` joins JOIN, contrast case = MANAGER, ฿-ledger ฿9.76M → ฿1.65M). **§3 ฿-threading finding:** the shipped `source` `ActionStepExecutor` returns action envelopes + **drops the input entity's amount** → the `approve` `doa_tier` fails CLOSED at approve. **NEXT (Phase 2):** PLAN-0044 A1b Step 5 (`GovernanceActionExecutor._scored_rule`) on `feat/a1b-scored-rule` — deterministic quote scoring (LLM summarises only), select winner, emit amount+currency so `approve` resolves; offline gate = AC-7 + a full-loop stub-client test threading ฿288,000 → CONTROLLER; then merge → rebase `feat/hero-demo-v1-live` → C-3 runner → C-4 endpoint/toggle → C-5 live MS-S1 smoke (host-state, Cray go). **Owed at A1b CLOSE (not per-step):** PLAN-0044 Completion note + `git mv` → `done/` + a STATUS full-body reconcile. `loop-dispatcher` stays DISABLED; MS-S1 cold (offline) | `788994d` (#493) / `85eafaa`·`6fb7b2b`·`b76c080`·`f310778` / `verticals/procurement/data_adapter/fastenal_csv.py` + `verticals/procurement/hero_demo/{governance_audit,ledger}.py` + `services/api/{models,routers}/demo.py` (`/demo/hero/{governance,impact}`) + `services/api/static/assets/view-hero.js` |
| 2026-06-30 | **A1b STEPS 3 + 6 (the rest of the demo-critical path) SHIPPED + MERGED (#488 `doa_tier` / #489 `governed_decision`) + independently verified (J1/J2 PASS) → the DEMO-CRITICAL PATH IS COMPLETE ON MAIN (session 89)** — MILESTONE, not closure: **A1b is NOT complete** (AC-9 + Steps 2/4/5 remain). With **Step 1 (#486, the live SoD gate)**, the hero render now has all three structured fields it joins on. **Step 3 (#488, `34be3a5`, AC-5):** a deterministic `doa_tier` per-kind executor — `resolve_doa_tier` over the `DoaLadder` half-open band (`Decimal` spend → tier), resolves the tier's `approver_role` → a `Person`, **fails CLOSED on a currency mismatch (OQ-4)**; the **SD-1=(a) `GovernanceActionExecutor` wrapper** dispatches on `governance_content.kind` **without a new `StepKind`**. **Step 6 (#489, `f5527d9`, AC-8):** the typed minimal **`governed_decision` audit-to-control field (SD-3=(a))** — `ControlRef{kind,id}` + `GovernedDecision{control_ref, principal_id}` on `AuditMetadata`, emitted as an **ENGINE side-effect** by the `doa_tier` route (`{kind:'doa_tier', id:resolved_tier_id}`) and the SoD gate (`{kind:'sod', id:sorted distinct_steps}`); **join-stable keys** (the `Person` PK + the verdict-emitted control id). **Gate (offline = binding bar):** both ruff + mypy clean — Step 3: **19 new `doa_tier` tests, full suite 1968 passed**; Step 6: **5 new `governed_decision` tests + the SoD-gate DB emission** (real hero gate emits `{kind:'sod', id:'approve+intake', principal_id:'appr-director'}`), **full suite 1973 passed / 5 skipped**. **Axis-B goal-gate: J1 PASS + J2 PASS** (independent goal-evaluator, creator≠critic intact, both steps). **AC-9 DEFERRAL (surfaced for Cray, NOT silently applied):** the procurement `audit` step is authored `autonomy: auto` AND downstream of the `approve`/`issue_po` gates, so the AC-9 auto-downstream-of-a-gate assertion would **restructure the hero procedure** — a Cray decision (restructure the audit terminal vs exempt no-op terminals), held for adjudication. **NEXT:** signal the hero-demo session to converge (the `services/engine/procedures/*` hold releases — it can build the read-only governance-moment render); then A1b's remaining non-demo-critical work = AC-9 (the Cray pick) + Steps 2/4/5 (`OQ-6` N≥2 marker · `rule_gate` · `scored_rule`). **Owed at A1b CLOSE (not per-step):** PLAN-0044 Completion note + `git mv` → `done/` + a STATUS full-body reconcile. `loop-dispatcher` stays DISABLED; MS-S1 cold (A1b offline) | `34be3a5` (#488) / `f5527d9` (#489) / `services/engine/procedures/{action_step,orchestrator}.py` + `services/db/models.py` (`AuditMetadata`/`GovernedDecision`/`ControlRef`) + `verticals/procurement/procedures.yaml` |
| 2026-06-30 | **A1b STEP 1 (demo-critical LIVE fail-closed principal-SoD run enforcement) SHIPPED + MERGED (#486) + independently verified (J1/J2 PASS) (session 89)** — INTERIM (1 of A1b's 6 steps; A1b NOT complete). Makes the A1a pure `check_principal_sod` fire on a REAL suspended-gate resolution. `spec.parse_procedures` now reads `principals`/`principal_aliases` (were silently dropped); procurement ships **5 authored principals + `required_roles`** (AC-10); a **`step_principals` JSONB column on `PipelineRun` (+ Alembic `0004`)**; `orchestrator.run_procedure(principal=…)` records the requester per SoD step (**SD-2=(a)**); `action_step.resolve_gated_step` invokes the check **unconditionally**, fails **CLOSED** (raises `PrincipalSoDError` with the structured verdict) **BEFORE** any approve/execute, **non-skippable**. **Inert for non-SoD procedures** (only procurement carries SoD; aquaculture inert-reconcile proves no behavior change). **Gate (offline = binding bar):** ruff + mypy clean; **1921 offline + 27 DB tests green** incl. **8 NEW live-SoD DB tests** + `alembic upgrade head` (0004) + aquaculture inert-reconcile. **Axis-B goal-gate: J1 PASS + J2 PASS** (high, independent goal-evaluator, creator≠critic intact). **Demo-convergence:** 1 of 3 demo-critical pieces of the hero-demo "governed→run→฿" path; **A1b Steps 3 (`doa_tier` executor) + 6 (`governed_decision` audit-to-control) next** = the rest of that path (offline-pure); Steps 2/4/5 (`OQ-6`·`rule_gate`·`scored_rule`) after; hero-demo session converges once the path is in. **Owed at A1b CLOSE (not per-step):** PLAN-0044 SD-1/SD-2/SD-3-as-rec disposition + a PLAN-0044 Completion note + a STATUS full-body reconcile. `loop-dispatcher` stays DISABLED; MS-S1 cold (A1b offline) | `719ea78` (#486) / `services/engine/procedures/{spec,orchestrator,action_step}.py` + `services/db/models.py` + `services/db/migrations/versions/0004_*.py` + `verticals/procurement/procedures.yaml` |
| 2026-06-30 | **A1 (run-time moat enforcement — Cray's #1 rock) LANDED (session 88): ADR-0026 Accepted #479 + A1a COMPLETE #481/#482 + A1b planned PLAN-0044 #484** — builds the principal-identity capability the AT-2 layer's run-time SoD was deferred on (the s85/s86 AC-13-ALT carry). **ADR-0026 Accepted (#479, `620d799`):** principal-identity + AT-2 run-time enforcement; all **6 OQs Cray-adjudicated as-recommended**. **PLAN-0043 (A1a) drafted + SD-1/SD-2 folded (#480, `05243eb`/`af0d882`):** Cray adjudicated **SD-1 = `required_roles` on `SoDConstraint`** + **SD-2 = a `PrincipalAlias` link object** (deviating from the drafted rec). **A1a COMPLETE end-to-end:** **Steps 1-3 (#481, `f1e7afa`)** = the `Person` / `PrincipalAlias` construct + `SoDConstraint.required_roles` + H-governance (new fields are governance, never on a draft type); **Steps 4-6 (#482, `f5c6342`)** = `services/engine/procedures/principal_sod.py`, the **fail-closed principal-SoD run-check** emitting a **STRUCTURED `PrincipalSoDVerdict`** + the `RunContext.principal` / `resolve_gated_step(principal=…)` seam + the offline oracle. **Gate: offline green — the full procedures suite 344 passed.** **A1a/A1b boundary (Cray s88):** the live invocation needs per-step principal RECORDING = the A1b executors' job; A1a ships construct + run-check + seam, A1b wires live enforcement. **A1b drafted = PLAN-0044 (in-flight, #484):** live run enforcement + per-kind executors (`doa_tier`/`rule_gate`/`scored_rule`) + audit-to-control (OQ-5); **3 SDs surfaced for Cray.** **Hero-demo dependency (parallel session):** A1's structured `PrincipalSoDVerdict` + the A1b OQ-5 audit field feed the hero-demo's read-only "governance moment" render (convergence ask #1 MET, #2 lands with A1b). In-flight PRs awaiting Cray merge: **#483** (PLAN-0043 → `done/`) + **#484** (PLAN-0044). `loop-dispatcher` stays DISABLED; MS-S1 cold (A1a offline) | `620d799` (#479) / `f1e7afa` (#481) / `f5c6342` (#482) / `docs/adr/0026-principal-identity-run-enforcement.md` + `docs/plans/done/0043-a1a-principal-identity-sod-runcheck.md` + `services/engine/procedures/principal_sod.py` |
| 2026-06-29 | **PLAN-0041 (classify-prompt enrichment lever) COMPLETE (session 87, #475/#476 + live AC-7 PASS)** — the fix for the PLAN-0040 AC-B5 ~1-in-3 false-abstain on a textbook AT-1/AT-3; a **PROMPT-ONLY** lever to lift the live AT-1-family classify match-rate. **Moat byte-identical** — the abstain-guard (`_archetype_disagreement`/`_AT2_ONLY_KINDS`/`_BAND_KINDS`, ADR-0024 D4/D7) unchanged; no schema change; **no new ADR**. **Steps 1-3 (#475, feat `035af38`):** `ArchetypeTemplate.description` (value-free, from the canonical catalog) + a 3-tuple classify catalog + a value-free `_BAND_EXPLAINER` into `build_classify_messages` (ends "When unsure … abstain" = the R2 moat-safety brake); offline gate AC-1..5 (guard byte-identity introspection; AT-2-only-abstain generalized to scored_rule/rule_gate/doa_tier; enriched-prompt introspection; descriptions-carry-no-AT2-vocab; schema pins the closed enum). **Step 4 (#476, test `d06d420`):** the OQ-C 26-narrative labelled fixture set + offline validators + a `@live`-gated before/after A/B harness routing both arms through the byte-identical imported guard (no production change); an independent adversarial moat-safety reviewer judged the set trustworthy; the pre-committed pass/fail read embedded in the harness (a docs/plans/ evidence doc was G2-gated → relocated into the test module). **Step 5 (live, AC-7, host-state — Cray go via AskUserQuestion):** the live before/after on MS-S1 `gpt-oss:20b`, N=3, worst reported — **PASS:** Arm A gated AT-1+AT-3 **8→11/11 (perfect, all 3 reps)** vs the ~7/11 PLAN-0040 reference; Arm B **11/11 abstain every rep** (zero AT-2 regression); **Arm-B guard paths = {label_abstain: 33}** (step_disagreement = 0 — the model labels AT-2 out-of-scope ITSELF, the deterministic backstop never needed to fire = no silent label→backstop shift); AT-1b 11/12 (reported, not gated). Live = **confirming evidence; the offline gate is the binding bar** (OQ-D). Raw log gitignored at `.claude/benchmark-results/plan0041-step5-live-ab.log`; thin tracked summary at `docs/logs/2026-06-29-plan0041-step5-live-ab.md` (two-artifact model). Gate (every step, offline): ruff + ruff-format + `mypy --strict services/` clean, **pytest 1891 passed / 25 skipped** (1877 baseline + 7 Steps-1-3 + 7 Step-4 validators; live test skipped offline). PLAN `git mv` → `done/`. `loop-dispatcher` stays DISABLED | `de36c2b` (#475/#476) / `services/engine/procedures/{archetypes/template,generator/{pipeline,prompts}}.py` + `tests/services/engine/procedures/{test_generator_pipeline,classify_enrichment_fixtures,test_classify_enrichment_fixtures,test_classify_enrichment_live}.py` + `docs/plans/done/0041-classify-prompt-enrichment.md` + `docs/logs/2026-06-29-plan0041-step5-live-ab.md` |

## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13 (ratified `4d1347b`, #302; committed Proposed `e25281d`, #297 + instruction `e387a63`, #298 + R1 errata `655344d`, #300) — guarded trial under observation (parallel to ADR-012). A specialist Cowork project role-plays a Thai operator and emits a "partner profile package" to rehearse the intake+PDPA pipeline before a real partner; venue OUTSIDE the governance tiers (no commits / no repo mount / enters via Code receive). Three BINDING anti-circularity rules R1/R2/R3 (R3 SYNTHETIC provenance → never trips PLAN-0005 §8.1 / ADR-011 first-real-data trigger). All four venue SDs + dispatch-SD-1 ratified per Cowork rec (SD-1 N=3; SD-2 one-project-per-business-type; SD-3 size/region/maturity enums w/ energy·mid·th-regional·mixed-legacy default; SD-4 "what we refused to share" now required). D4 guarded-trial mirrors ADR-012 D5; regression triggers R-PS1..R-PS4 are the exit criteria; run 1 = energy operator (ADR-005 primary). **RUN 1 (energy / mid / th-regional / mixed-legacy) COMPLETE 2026-07-02 (session 93):** synthetic partner profile package (fictional TWP operator) received via Cray relay + Code-screened **S-1..S-5 ALL PASS** against a **pre-committed** oracle (R1 no schema echo · R2 six unsolicited inconvenient facts + heavy data flaws · R3 SYNTHETIC banner intact · SD-4 refused-to-share present); no R-PS trigger fired. Landed (gitignored, R3): package `docs/research/private/2026-07-02-partnersim-run1-energy-package.md` + oracle/verdicts `...-run1-receive-checklist.md` + completion handoff (session-93). First-pass value: **8 schema-mismatch findings** for the intake/mapping/PDPA path (unstable asset PKs, unresolvable principal identity vs ADR-0026 SoD + the worker-committee PDPA angle, multi-unit columns vs ADR-0021, per-source TZ chaos, action-events-in-status + seasonal thresholds vs in_file_band, mutable history, residency = our on-prem fit, DPA 4–6-wk timeline). **ADR-0020 D4 post-run-1 review DONE 2026-07-02 (s94): verdict continue-with-adjustments (no R-PS trigger fired; C-1..C-3 confirmed; #516 R1-tighten + stripped paste-variant landed; run-2 preconditions recorded — re-paste instruction to UI, fresh project per SD-2, unannotated bulk ask, persona fix). RUN 2 (supply-chain / mid / multi-site-sea / mixed-legacy) COMPLETE 2026-07-02 (s94): fresh project + all 3 D4 adjustments; S-1..S-6 ALL PASS pre-committed (first live R-PS4 screen clean); cross-run signal — identity/PK/clock/bottleneck/batch-only recur in 2/2 verticals (mapping-layer core, not energy quirks); new classes: cross-border-already-in-flight, duration-qualified + per-contract bands, per-device calibration, GPS-as-PII column-drop. C-1..C-3 (new project) carried open. RUN-2 REHEARSAL done 2026-07-03 (s94 cont.): G1–G11 (headline: supply_chain_v0 lacks an equipment entity + measured_kind; 4 new band-gap classes; cross-border DPA musts; GTM templates now customer-demanded); §5 cross-run synthesis = 9 classes recur 2/2 verticals (mapping-layer core; Rule-of-Three holds — no abstraction yet). C-1..C-3 input-state check CONFIRMED 2026-07-03 (Cray Path-1 UI: no repo mount, post-#516 instructions, no past-chats) — run-2 open item CLOSED; the trial has no open partner-sim debt. ADR-011 audit framework stays gated on a REAL partner conversation — the synthetic run INFORMS but never TRIGGERS it (R3).**
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **Procurement vertical — GO + IN MOTION: PLAN-0036 (Fastenal, Stage 1) drafted + merged Draft (#412, `7a7c036`):** **GO** — Cray greenlit the 4th vertical (Procurement) and **PLAN-0036 (Fastenal procurement vertical, Stage 1) is drafted + merged Draft** (#412, head_commit `7a7c036`; Cowork-D1 + Code-R2 + committed D2, session 75). **Cray adjudicated SD-1…SD-5 = confirm-all** (2026-06-24, as-recommended). **Demo target = Fastenal Thailand** — automotive/auto-parts in the EEC; **hero** = asset-failure → governed emergency sourcing, **calm-path** = low-stock reorder. Stage 1 = a **PLAN-only, no-ADR pure-config plugin** on the shipped ADR-016 engine, **zero `services/` core edit** (CQ-1 confirmed, ADR-0023); the **SD-4 catch** = `services/engine/procedures/spec.py` `Step = ConfigDict(extra="forbid")` → Stage-1 facet annotations are **comment-only** (a first-class `facet` field = a Stage-2 ADR-016 amendment). It is the **proving ground** for the ultimate **3-phase generative-procedure platform** (generate / run / monitor); per Rule-of-Three it builds **no generic generator** (hand-author → extract schema Stage 2 → generator Stage 3). **NEXT = a new session flips PLAN-0036 Draft → Ready for execution (SDs confirm-all) then executes Stage 1.** *Supporting de-risk dossier (Cowork, session 72, 2026-06-22, `docs/research/private/`)* — **(1)** `2026-06-22-procurement-spec-expressiveness-probe.md` (procurement is **config-layer**, **0 new core amendments**; only engine pulls are the already-deferred ADR-016 Phase 2 / Phase 4+ items); **(2)** `2026-06-22-procurement-gtm-commercial-validation.md` (wedge = ops-triggered asset-aware procurement; econ buyer = CFO/Controller, champion = ops/procurement mgr; metric = **cycle-time**; ~$40K–150K/yr; 6-wk paid pilot); **(3)** `2026-06-22-procurement-asset-aware-incumbent-scan.md` (de-risk #1 — EAM/CMMS = nearest incumbent on the *trigger* only; white space = the **triple intersection** asset-trigger × governed sourcing × cross-vertical); **(4)** `2026-06-22-ai-sourcing-competitor-teardown.md` (de-risk #2 — Verusen/Keelvar/Fairmarkit/Arkestro/… triple intersection unoccupied; defensibility on **axis (a) asset-event trigger**; watchlist: **Verusen #1**, Fairmarkit, Coupa); **(5)** `2026-06-22-platform-incumbent-deepdive.md` (de-risk #3 — Palantir/Maximo/GE Vernova/SAP = capability-yes / product-no; moat = **packaging × ICP × price** = the **"Palantir-lite"** thesis, ADR-005, **governed ≠ generated**). **Pitch:** lead with asset-ontology-triggered governed sourcing + the native ontology (ADR-008) + engine (ADR-016) combination — **NOT** "governed"/"cross-vertical" (now commoditized claims).
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [x] **PLAN-0041 (classify-prompt enrichment lever — Rock 1) — COMPLETE (s87, offline gate #475/#476 + live AC-7 PASS, moat byte-identical).** The prompt-only fix for the s83 AC-B5 ~1-in-3 false-abstain: offline gate (#475 Steps 1-3 + #476 Step 4) + the Cray-gated live before/after on MS-S1 `gpt-oss:20b` (Arm A 8→11/11 all reps; Arm B 11/11 abstain; label_abstain 33/33, step_disagreement 0); the AT-2 cross-check stayed byte-identical, no schema change, no new ADR; the offline gate is the binding bar, live = confirming. PLAN `git mv` → `done/`. *(Cowork-D1 → Code-R2 → Cray-ratified → committed #461; executed Steps 1-5 Code-direct s87)*
- [ ] **Rock 2 / O-3 — AT-2 / managerial layer — ADR-0025 RATIFIED + ACCEPTED (#463, s84); next = the follow-on build PLAN.** The Box-3 "Action = contract" layer (DOA/SoD/scored-rule/compliance). **ADR-0025 (Accepted)** decided: type AT-2 content (D2 authoritative discriminated `Step.governance_content` keyed to `gate_kind`, not the facet), bypass structurally unrepresentable (D3), **close the live run-gate AT-2-blindness defect** (D5), **defer the generator** under a CI-enforced N≥2 re-trigger (D7; AT-2 = N=1). **NEXT = the follow-on build PLAN (OQ-5, separate Cowork dispatch):** type the content + the D5 gate-extension + the prose→typed migration of the existing procurement AT-2 in **ONE PR behind a green golden test** (⚠ the shipped AT-2 fails `validate_governance_complete` until typed). OQ-3 (run vs author-only) concrete v1 call lands in that PLAN. *(s84; ADR-0025; [[project_vero_ultimate_target_generative_procedures]])*
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2; Q3 ADR Accepted + BUILD COMPLETE s93 — open only for the residues).** (1) **Q3 ontology data-binding — DONE end-to-end:** the ADR-016 D2+D3 amendment (Accepted s93, #505) is now **BUILT + CLOSED** (PLAN-0046 → `done/`; #511 feat `878b517` / #512 close `eb63692`, s93 cont. 2026-07-02): `StepInput.reads: list[str]` + `Agent.allowed.object_types` + the `validate_read_bindings` **LOAD-time consistency/scoping gate** (`reads ∈ ontology ∩ allowlist`, SD-1 Option A) wired at both production pre-flight sites; `reads` H-governed via `STEP_GOVERNANCE_FIELDS` + the `lift_to_step` draft-strip hardening; 12 new tests, offline suite 2066 passed / 5 skipped. v1 = a typed read contract + load-gate, **NOT** runtime-enforced parity — declared==dispatched teeth arrive with the **Q4 generic run-consume query executor = a SEPARATE later PLAN (remaining Rock-3 build residue)**. (2) **Box 4 (Profit Formula) — STILL DEFERRED (N≥3, unchanged).** The reasoning trace is operational, not economic — tie each action to ฿ impact (avoided outage / margin / ROI). Prepare by capturing the economic dimension as prose when hand-authoring verticals + proving the ฿ framing in the demo; type an economic-impact facet only after **N≥3** verticals triangulate it (the ADR-016 Q3 amendment left it a self-cancelling N≥3 marker). *(s84 strategy discussion + the 3-layer / ontology-binding diagram; Q3 ADR Accepted s93 #505; Q3 build complete + PLAN-0046 closed s93 cont. #511/#512 — TODO stays open ONLY for the Q4 executor + the Box-4 facet)*
- [ ] **Standard partner-intake form (template candidate — Cray observation, s93 partner-sim run-1).** Generalize the 6-ask structure (+ the TWP package's §1–§10 answer shape as a SYNTHETIC-bannered worked example) into a stakeholder-facing standard intake form per vertical, so partners can prepare narrative context for vero-lite to generate workflow pipelines more accurately. Template lineage = the partner-facing ONE-PAGER (full taxonomy allowed for real partners), NOT the R1-clean variant (partner-sim-only screen). Pairs with the partner-trial-readiness discussion + ADR-016 Phase 2 intake. *(s93; ADR-0020 run-1)*
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
