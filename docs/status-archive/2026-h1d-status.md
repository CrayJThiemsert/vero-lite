# STATUS.md rotation archive — 2026 H1 (continuation)

> **Period covered:** 2026-06-29 (session-87) → 2026-07-07 (session-106)
> **Sibling chain (letters ascend with time; the base file holds the RECENT window):** [`2026-h1b-status.md`](2026-h1b-status.md) (2026-05-10 → 2026-06-09) → [`2026-h1c-status.md`](2026-h1c-status.md) → [`2026-h1d-status.md`](2026-h1d-status.md) → [`2026-h1e-status.md`](2026-h1e-status.md) → [`2026-h1f-status.md`](2026-h1f-status.md) → [`2026-h1-status.md`](2026-h1-status.md) (base, newest — rotations append HERE). The separate `2026-h1-current-focus.md` (sessions ≤46, ratified as-is) is a Current-Focus-only artifact predating this chain.


Rotated out of `docs/STATUS.md` per the **STATUS.md Rotation Policy**
(`docs/runbooks/memory-architecture.md`, Lesson #23). Tier-3: **grep + windowed reads
only, never a whole-file Read.**

**Split lineage.** At session 80 the combined `2026-h1-status.md` first crossed R4's
~192 KB bar and was split into a recent-window file and its `-b` sibling. The recent
window then grew back to **592,577 B — 3.01x the split trigger and 2.26x the 256 KB
cap** — because R4 had no mechanism: its responsibility-matrix guard column read `—`
where R1 and R7 read `fail`. Session 144 added that mechanism
(`tools/check_archive_size.py`, #789) and this file is one of the four it forced.
**No content lost:** every section is preserved verbatim and exactly once across the
chain, verified by exact list equality at split time, not by a byte-sum estimate.

**Structural note (honest).** R4 describes an archive as TWO sections — rotated
Current Focus blocks and rotated Recent Decisions rows, *newest at top*. That is not
the shape on disk: the file drifted into **one section per reconcile, appended at the
bottom** (27 of them by session 144), and the old preamble's own "Period covered" had
gone stale years of sessions ago. This split preserves the drifted shape rather than
silently rewriting history to match the spec — reconciling R4's text with the real
convention is separate work, deliberately not done here.

---

## Rotated this reconcile (session-87, 2026-06-29 — PLAN-0041 classify-prompt enrichment COMPLETE #475/#476 + live AC-7 PASS)

_Rotated 2026-06-29 (session-87 reconcile): under the R1 64 KB hard ceiling, the **Session 85 `21d7669`** CF block (PLAN-0042 BUILD PLAN drafted→ratified→merged #465) + the **2026-06-25 PLAN-0037** Recent-Decisions row (Stage 2 PREP complete) were rotated from the live STATUS when the s87 PLAN-0041-COMPLETE block + RD row landed. Verbatim below, per the STATUS.md Rotation Policy (R1/R2/R4)._

### Current-Focus block — Session 85 (head_commit `21d7669`)

> **Session 85 (head_commit `21d7669`) — PLAN-0042 (the O-3 follow-on AT-2 /
> managerial-layer BUILD PLAN) DRAFTED → Code R2 → Cray-RATIFIED → committed + merged
> (#465).** PLAN-0042 (`docs/plans/0042-at2-managerial-build.md`, commit `21d7669`,
> merge `294e7b8`) is the **O-3 follow-on BUILD PLAN** that **ADR-0025 OQ-5** named — it
> renders ADR-0025 (Accepted #463) D1–D8 Implementation Notes + owns the migration
> sequencing. **Build PLAN — no new ADR.** **Primary deliverable = closing a LIVE shipped
> defect:** `validate_governance_complete` is blind to AT-2 *content* today (`rule_gate`
> evaluate → `[]`; `scored_rule`/`doa_tier` action → `[handler,autonomy]`, both already
> filled → no AT-2-content obligation). The build **types the AT-2 content** (D2
> discriminated `Step.governance_content` union + `Procedure.separation_of_duties`),
> makes the **run-gate AT-2-aware** (D5), and **migrates the shipped procurement AT-2
> prose→typed in ONE PR behind a green golden test** (the migration trap). **Cray-ratified
> (s85):** **OQ-A = A1** (author + render only — the engine has no principal-identity
> layer for run-time SoD, so D6 mandates the author+render fallback; the A2 run path is
> deferred to a follow-on PLAN); **OQ-B = B2** (labelled-provisional placeholder control
> values + Cray sign-off — the spec has no ฿ DOA tiers / criteria weights / compliance
> predicates, so typing D2 is *authoring*, not transcription); **OQ-C/D/E confirmed**
> (golden test + D5 migration in ONE PR; scoped value-only prose-lint + "ADVISORY — NOT A
> CONTROL" band; no per-spec `schema_version`). **Process:** Cowork-drafted (ADR-009 D1)
> → **Code R2** independently re-verified the fact-pack on HEAD `1305b32` and surfaced two
> substrate items the dispatch/ADR prose simplified — **finding 1** (a `Step.tiers`
> naming collision: `StepTiers` = PLAN-0022 handler taxonomy already exists at
> `spec.py:264` + is in `STEP_GOVERNANCE_FIELDS` → DOA tiers must nest in `DoaLadder`,
> never a 2nd top-level `Step.tiers`) and the **SoD principal-vs-role scoping finding**
> (under A1 the author-time gate enforces structural+role-level SoD; principal-identity
> SoD is run-time → relocated to the deferred **AC-13-ALT**, lineage note:
> superseded-by-A1, not an ADR amendment) → Code revision dispatch → Cowork applied 3
> surgical deltas → **Cray-ratified** → Code R2 the delta + committed (#465). **v1 build
> surface = Steps 1–3 + 5** (the A2 run path / AC-13-ALT deferred to a follow-on PLAN once
> a principal-identity-resolution capability exists). **Standing:** `loop-dispatcher`
> stays **DISABLED**; **MS-S1 cold — no live run in this PLAN** (offline oracle is the
> gate; generation out of scope). AI-assisted (Claude Code, session 85); no
> `Co-Authored-By` per CLAUDE.md §7.

### Recent-Decisions row — 2026-06-25 (PLAN-0037 / Stage 2 PREP COMPLETE)

| 2026-06-25 | **PLAN-0037 / Stage 2 PREP COMPLETE — 5-facet retrofit (→N=4) + procedure-archetype catalog SHIPPED + PLAN archived (session 77, #424/#425/#426)** — Stage 2 PREP for the generative-procedures target. PLAN-0037 was **`plan-drafter`-authored** (the in-harness subagent, ADR-013 D1 phased authority) → Code R2-reviewed + committed (#424, ADR-009 D2; separation intact); Cray chose the formal-PLAN route (ทาง 1). **Step A (#425, content `31ded05`):** retrofit the SD-4 5-facet annotation (`input · decision-condition · llm-assist · output · governance`) as **YAML comment blocks** onto `energy`/`supply_chain`/`aquaculture` `procedures.yaml` → consistent **N=4** instrumentation (Rule-of-Three substrate). **Provably inert:** `services/engine/procedures/spec.py` `Step` declares `extra="forbid"` (so `facet:` can only be a comment) + the loader uses `YAML(typ="safe")` (discards comments) → Step objects byte-identical, static-JS demos untouched; gate parse-clean all 4 verticals (steps unchanged 3/3/5/10), **66 insertions all-comment / 0 deletion**, **full offline suite 1651 passed/22 skipped** (baseline), no live MS-S1 (§8). Captured the env-vs-in-file judge-band split (energy/supply_chain via `OCT_RECOMMEND_THRESHOLD`; aquaculture/procurement in-file) as the Step-C input. **Step B (#426, content `c3b477a`):** the procedure-archetype catalog at `docs/conventions/procedure-archetypes.md` (AT-1 `anomaly→action`, AT-1b `watch+summary`, AT-2 `request→approve→fulfill`, AT-3 `monitor→reorder`) — the canonical reference the Step-C ADR + Stage-3 generator cite. SD-1=one PR for the 3 verticals / SD-2=Step B follow-on PR / SD-3=catalog home `docs/conventions/` (all Cray-resolved). **`loop-dispatcher` (Cray s77) = keep-disabled + guard** (over fix-hook / delete); the Stop-hook root-fix (scheduled-task auto-continue exemption) is deferred + is the precondition for any re-enable. **Out of scope (forward):** Step C (ADR-016 first-class `facet:` field = a separate **Cowork-drafted ADR**, G2-gated) + Stage 3 (the procedure generator, Rule-of-Three-deferred). PLAN-0037 `git mv` → `done/` | `f029913` (#424/#425/#426) / `verticals/{energy,supply_chain,aquaculture}/procedures.yaml` + `docs/conventions/procedure-archetypes.md` + `docs/plans/done/0037-*.md` |

---

### Current-Focus block — Session 85 (cont., `059c6ea`) [rotated 2026-06-30, session-88 reconcile]

> **Session 85 (cont.; head_commit `059c6ea`) — PLAN-0042 (the O-3 AT-2 /
> managerial-layer BUILD) Steps 1–2 SHIPPED + MERGED (#467/#468) — the AT-2
> managerial layer is typed + the run-gate is AT-2-aware: the LIVE run-gate blindness
> defect is CLOSED.** PLAN-0042 execution (the O-3 AT-2/managerial build, A1 = author +
> render only). **Step 1 (#467, `6176b18`):** the typed AT-2 governance content (D2) — a
> discriminated `Step.governance_content` union (`DoaLadder` | `ScoredRule` |
> `ComplianceGate`, keyed on `kind`) + `Procedure.separation_of_duties`; D3 bypass made
> **unrepresentable** (`Decimal` money; a closed `RelaxableConstraint` enum that can't
> name compliance/SoD; `blocks_po`/`requires_justification` `Literal[True]`; a total
> strictly-monotonic DOA ladder); D4 H-field invariants (the new fields in
> `GOVERNANCE_FIELDS`, never on a draft type; recursive draft-disjointness +
> `StepFacet`-unreachability CI checks). **Finding 1 honored** — DOA tiers nest in
> `DoaLadder`, no 2nd top-level `Step.tiers`. **Step 2 (#468, `059c6ea`):** the
> AT-2-aware run-gate (D5) **+** the procurement prose→typed migration in ONE PR behind a
> green golden test (the migration trap). **CLOSES THE LIVE DEFECT** —
> `validate_governance_complete` now owes typed `governance_content` on the AT-2 gate
> kinds + a `doa_tier` procedure owes `separation_of_duties`; an empty-DOA / no-criteria /
> no-SoD AT-2 is **no longer run-loadable**. The negative hollow-but-complete regression
> is the D5 ratification gate. **OQ-B = B2:** the DOA tiers + compliance predicates MIRROR
> the synthetic data adapter (coherent); the scored-rule weights are provisional — **all
> labelled provisional pending Cray sign-off.** **Build interpretations (consistent with
> the s85 Delta-2 SoD scoping):** principal-level SoD + the resolved-tier strict
> escalation remain **A2 (run-time, deferred AC-13-ALT)** — the engine has no
> principal/role-rank layer; the author-time gate enforces the STRUCTURAL form (≥2 distinct
> steps; ladder totality). **Gate:** ruff + ruff-format + `mypy --strict services/` (64
> files) clean; **pytest 1843 passed / 24 skipped.** No live MS-S1. **Remaining (v1 surface
> Steps 1–3+5, A1):** **Step 3** (scoped value-only prose-lint over AT-2 free-text +
> "ADVISORY — NOT A CONTROL" provenance banding, reuse the PLAN-0039 viewer) + **Step 5**
> (the 3 D8 red-team fixtures, LLM stubbed). **AC-13-ALT (the A2 run path) deferred** to a
> follow-on PLAN. `loop-dispatcher` stays DISABLED. AI-assisted (Claude Code, session 85);
> no `Co-Authored-By` per CLAUDE.md §7.

### Recent-Decisions row — 2026-06-25 (ADR-016 D2 Amendment + PLAN-0038 minted) [rotated 2026-06-30, session-88 reconcile]

| 2026-06-25 | **Stage 2 COMPLETE — ADR-016 D2 Amendment (first-class typed `facet:` Step field) ACCEPTED + merged (#428) + PLAN-0038 impl PLAN minted (#429) (session 77, batch 2)** — Step C promotes the 5-facet annotation from a YAML comment to a **first-class, typed, validated, optional `facet:` field** on `Step`, completing Stage 2 (generalized-schema extraction). **Cowork-drafted** (ADR-009 D1) → Code R2-reviewed (gate_kind↔N=4 split, `spec.py extra="forbid"`+typed fields, `procedures.yaml` engine-read, validator dog-food 0 errors) → **Cray-ratified both forks** → committed (D2). **Fork 1 = Hybrid** (`facet` carries net-new `decision_condition`+`llm_assist` typed; `input`/`output`/`governance` optional non-authoritative notes — one source of truth, `spec.py` already types 4/5 via PLAN-0022). **Fork 2 = discriminated `gate_kind`** (enum over the 6 N=4 kinds `env_band`/`in_file_band`/`rule_gate`/`scored_rule`/`doa_tier`/`none` + `band_source`/`env_var`; `in_file_band` points at the existing typed band, no re-store). **Process note:** the ratify status-flip (Proposed→Accepted) was **G1-blocked for Code** — editing an already-Accepted ADR is denied **even with Cray per-diff approval + a warmed `gpt-oss:20b` classifier** (genuine policy, not a fail-closed infra deny; distinct from the ratify-transition case s40/67) → resolution = chore-PR path: **Cowork applied the flip** (ungated), Code committed, Cray merged (= the G1 review); [[project_g1_adr_gate_override_via_incontext_approval]] updated. **PLAN-0038 MINTED Draft** (#429, `b2f19bc`) — **`plan-drafter`-authored** (ADR-013 D1) → Code R2-reviewed → committed. Scope: the `services/engine/procedures/spec.py` engine edit (typed `facet` per the delta) + migrate the 4 verticals' comment-facets → the real field + load/validation tests — the **first deliberate `spec.py` edit since procurement's zero-engine-edit (CQ-1)**, ADR-sanctioned. **Schema only** (engine still ignores `facet` at run time); **implements nothing on commit**; **3 OPEN SDs** (note-migration / comment-removal / PR-granularity). Gate = offline suite (1651 baseline + new tests) + `mypy --strict`; no live MS-S1. NEXT = Cray merges #429 + adjudicates SD-1/2/3 → execute PLAN-0038 → Stage 3 generator + review UI | `0b56954` (#428) / `b2f19bc` (#429) / `docs/adr/0016-governed-procedure-engine.md` + `docs/plans/0038-*.md` |

### Current-Focus block — Session 86 (head_commit `973ba69`) [rotated 2026-06-30, session-89 reconcile]

> **Session 86 (head_commit `973ba69`) — PLAN-0042 v1 (the O-3 AT-2 /
> managerial-layer BUILD) OFFLINE TAIL COMPLETE (#470/#471/#472, all Cray-merged) →
> PLAN-0042 v1 (Steps 1–3 + 5) is COMPLETE; PLAN `git mv` → `done/`.** Session 86
> continued the s85 closeout handoff and executed the already-ratified build PLAN
> directly (a build PLAN — the Steps were ratified). **Step 3a (#470, feat `4ff1180`):**
> the scoped value-only prose-lint over AT-2 free-text (`governance_prose_lint` = value
> classes + an approver-role-token check; OMITS the decision-verb + broad-identifier
> classes per finding 6) **+** a LOAD gate (`Procedure._validate_at2_free_text` blocks
> load on a ฿-amount / weight / role token smuggled into AT-2 free-text) **+** the 3
> ADR-0025-D4-mandated advisory NON-AUTHORITATIVE free-text fields
> (`EmergencyWaiverPolicy.justification`, `DoaTier.note`, `ScoredCriterion.note`); one
> reword of the shipped procurement AT-2 (`"3-bid"`→`"three-bid"`). **Step 3b (#471, feat
> `5fac5d2`):** the PLAN-0039 read-only viewer now renders the typed AT-2 governance
> content (DOA ladder / scored rule / compliance gate / SoD) as **AUTHORITATIVE** (the
> Box-3 "the gate is no longer blind" artifact, AC-13) + bands the AT-2 free-text
> **"ADVISORY — NOT A CONTROL"** (OQ-D label); no API change (`model_dump` serializes it);
> verified live on the preview (snapshot/eval). **Step 4 (AC-13) = author + render only
> (A1)** — delivered by Step 3's render, no separate build. **Step 5 (#472, test
> `5464831`):** the D8 offline oracle — `tests/services/engine/procedures/test_red_team_at2.py`
> consolidates the 3 red-team fixtures (hollow-but-complete → refused; leak-in-free-text →
> blocks load; identity-collapse role-level = a single-step SoD rejected at construction +
> a missing-SoD `doa_tier` procedure refused at the gate) + a positive control; the
> PRINCIPAL-level collapse / literal `approver_role==requester_role` / un-gated-audit are
> **A2-deferred (AC-13-ALT)** — documented, intentionally NOT asserted (no false coverage).
> **Gate (every step, offline):** ruff + ruff-format + `mypy --strict services/` (64 files)
> clean; **pytest 1877 passed / 24 skipped**; no live MS-S1 (the offline oracle is the
> gate). **AC-13-ALT (the A2 run path: principal-identity SoD + deterministic per-kind
> enforcement executors) deferred** to a follow-on PLAN, gated on a
> principal-identity-resolution capability the engine lacks today. **OQ-B** placeholder
> control values (DOA tiers + compliance predicates mirror the synthetic data adapter;
> scored-rule weights provisional) stay labelled provisional — the real Fastenal figures
> fold in via a small `verticals/`-only PR (B1), blocking nothing. `loop-dispatcher` stays
> **DISABLED** (the Stop-hook root-fix is the re-enable precondition). AI-assisted (Claude
> Code, session 86); no `Co-Authored-By` per CLAUDE.md §7.

### Recent-Decisions row — 2026-06-25 (PLAN-0038 ADR-016 D2 Amendment EXECUTED) [rotated 2026-06-30, session-89 reconcile]

| 2026-06-25 | **PLAN-0038 (ADR-016 D2 Amendment implementation) EXECUTED end-to-end → Complete + archived; Stage 2 (generalized-schema extraction) now COMPLETE on real data (session 77, batch 3, #431/#432)** — completes Stage 2 of the generative-procedures arc, now proven on real data not just the model. **Step A (PR-1, #431, feat `bf7e858`):** the `services/engine/procedures/spec.py` engine edit — the typed `facet` sub-model per the amendment delta (`BandSource`/`GateKind` (6 kinds)/`DecisionCondition` w/ `band_source⇔gate_kind` + `env_var`-only-with-`env` validator/`StepFacet`/`Step.facet`), keeping `extra="forbid"` (facet now a KNOWN key) — the **first deliberate `spec.py` edit since procurement's zero-engine-edit (CQ-1)**, ADR-sanctioned; schema-level facet tests landed here (suite 1669 passed). **Step B (PR-2, #432, feat `777393c`, merge `42a8327`):** migrate the **4 verticals'** comment-facets → the real typed `facet:` field — **config + tests only, no `services/` edit**; +19 end-to-end migration round-trip tests. **SDs (Cray-resolved):** SD-1=(a) populate all 5 facets (`decision_condition`+`llm_assist` typed; `input`/`output`/`governance` str notes from the comment prose); SD-2=(a) remove the comment blocks (single carrier, grep confirms 0 leftover `# facet[`); SD-3=(b) split A/B PRs. **D2-A3 `gate_kind` mapping:** energy/supply_chain `judge`→`env_band` (`OCT_RECOMMEND_THRESHOLD`); aquaculture/procurement `judge`+`judge_stock`→`in_file_band` (points at the typed `threshold`/`direction`/`watch_margin`, no re-store — AC-6); procurement `compliance`→`rule_gate`, `source`→`scored_rule`, `approve`→`doa_tier`; reads/mechanical writes/audit terminals/simple gated actions→`none` (incl. `escalate_watch`=`none`+`decision_condition.note`, Cray-endorsed). Updated the stale "facets are comment-only" framing in `verticals/procurement/README.md` + the procurement `procedures.yaml` header. **`facet` stays non-authoritative** — engine reads but does NOT consume it at run time (D2-A4; grep = 0 `.facet` reads in `services/`). Gates: full offline suite **1688 passed/22 skipped** (1669 baseline + 19 new), ruff + ruff-format clean, mypy --strict `services/` clean, no live MS-S1 (§8 — pure schema/config). `loop-dispatcher` still DISABLED all session (Stop-hook root-fix deferred = precondition for re-enable). PLAN-0038 `git mv` → `done/`. NEXT = Stage 3 (the procedure generator, ADR-016 Phase 2, Rule-of-Three-deferred) + a schema-driven 5-facet review UI | `bf7e858` (#431) / `777393c` (#432) / `services/engine/procedures/spec.py` + `verticals/{energy,supply_chain,aquaculture,procurement}/procedures.yaml` + `docs/plans/done/0038-*.md` |

### Current-Focus block — Session 87 (head_commit `de36c2b`) [rotated 2026-06-30, session-89 reconcile]

> **Session 87 (head_commit `de36c2b`) — PLAN-0041 (the classify-prompt
> enrichment lever — the fix for the PLAN-0040 AC-B5 ~1-in-3 false-abstain) COMPLETE:
> offline gate (#475 Steps 1-3 + #476 Step 4) + the Cray-gated live before/after
> (Step 5 / AC-7) PASSED on MS-S1 `gpt-oss:20b`; PLAN `git mv` → `done/`.** A
> **PROMPT-ONLY** lever to lift the live AT-1-family classify match-rate — the moat
> abstain-guard (`_archetype_disagreement` / `_AT2_ONLY_KINDS` / `_BAND_KINDS`,
> ADR-0024 D4/D7) stayed **byte-identical** throughout; no schema change; **no new
> ADR**. Executed Steps 1-5 this session (the ratified PLAN #461; Code-direct).
> **Steps 1-3 (#475, feat `035af38`):** added `ArchetypeTemplate.description`
> (value-free, derived from the canonical catalog `docs/conventions/procedure-archetypes.md`),
> widened the classify catalog to a 3-tuple, and inserted a value-free
> `_BAND_EXPLAINER` (the positive band-vs-out-of-scope teaching, ending on "When
> unsure … abstain" = the R2 moat-safety brake) into `build_classify_messages`.
> Offline gate AC-1..5: guard byte-identity introspection; the AT-2-only-abstain test
> generalized to all three kinds (scored_rule/rule_gate/doa_tier); enriched-prompt
> introspection; descriptions-carry-no-AT2-vocabulary; schema still pins the closed
> enum. **Step 4 (#476, test `d06d420`):** the OQ-C 26-narrative labelled fixture set
> (`classify_enrichment_fixtures.py` — Arm A: 6 AT-1 + 5 AT-3 gated + 4 AT-1b
> measured-only; Arm B: 11 genuine AT-2, 2 borderline) + offline validators + a
> `@live`-gated before/after A/B harness (`test_classify_enrichment_live.py`) routing
> both arms through the byte-identical imported guard (no production change). An
> independent adversarial moat-safety reviewer judged the set trustworthy, no blocking
> defect. The pre-committed pass/fail read is embedded in the harness (a docs/plans/
> evidence doc was G2-gated → relocated into the test module). **Step 5 (live, AC-7,
> host-state — Cray go via AskUserQuestion):** the live before/after on MS-S1
> `gpt-oss:20b`, N=3 reps, worst reported. **PASS.** Arm A gated AT-1+AT-3 lifted
> **8→11/11 (perfect, all 3 reps)** vs the ~7/11 PLAN-0040 reference; Arm B **11/11
> abstain every rep** (zero AT-2 regression); **Arm-B guard paths = {label_abstain:
> 33}** (step_disagreement = 0 — the model labels AT-2 out-of-scope ITSELF; the
> deterministic backstop never needed to fire = the strongest outcome, no silent
> label→backstop shift); AT-1b 11/12 (reported, not gated). Live = **confirming
> evidence**, the offline gate is the binding bar (OQ-D). Raw log gitignored at
> `.claude/benchmark-results/plan0041-step5-live-ab.log`; thin tracked summary at
> `docs/logs/2026-06-29-plan0041-step5-live-ab.md` (two-artifact model). **Closeout
> (`de36c2b`):** PLAN `git mv` → `done/` + the docs/logs summary. **Gate (offline,
> every step):** ruff + ruff-format + `mypy --strict services/` clean; **pytest 1891
> passed / 25 skipped** (1877 baseline + 7 Steps-1-3 + 7 Step-4 validators; the live
> test skipped offline). **Standing:** `loop-dispatcher` stays **DISABLED**;
> AI-assisted (Claude Code, session 87), no `Co-Authored-By` per CLAUDE.md §7.

### Recent-Decisions row — 2026-06-25 (Stage 3 KICKOFF: ADR-0024 + PLAN-0039) [rotated 2026-06-30, session-89 reconcile]

| 2026-06-25 | **Stage 3 KICKED OFF — ADR-0024 (archetype-first procedure generator) ACCEPTED #434 + PLAN-0039 (read-only 5-facet viewer) Ready #435 + the ADR-0024 OQ-disposition errata (session 78)** — opens Stage 3 of the generative-procedures arc (ADR-016 Phase 2). Both artifacts **Cowork-drafted (ADR-009 D1) → Code R2-reviewed → Cray-ratified → committed (D2)**. **ADR-0024 (#434, add `c90b2d2`):** archetype-first generation **backed by a Code-run 5-specialist design panel** (LLM-pipeline · governance · schema · product-UX · red-team). **D1–D12 locked:** classify narrative → 1 of N archetypes → deterministic-code instantiates → LLM drafts advisory prose only (**exactly 2 narrow LLM calls**, classify-don't-synthesize ADR-0021); **"governed ≠ generated" re-fenced at the AUTHORING surface + made MECHANICAL** = a **restricted draft type** with NO governance fields (leak = type error) + a deterministic prose-lint; generator emits `gate_kind` (closed-enum) but **never a value/handler/threshold/tier/autonomy/env_var** (D4); **abstain never force-fit** (D5); determinism invariant holds at the authoring layer; skeleton **draft-loadable but NOT run-loadable** until a human authors gates (D6); **v1 = AT-1 family (AT-1/AT-1b/AT-3), AT-2 DEFERRED** (only AT-2 = `procurement.emergency_sourcing`, N=1; catalog really N≈2; D7); **one review surface**, read-only viewer ships first (D8); the catalog promotes prose→machine-readable `ArchetypeTemplate` (D2). **9 OQs Cray-ratified ACCEPTED** as standing guidance. **PLAN-0039 (#435, `edd28a6`):** a **zero-LLM** oct-demo view rendering **every shipped procedure (5 across 4 verticals — Cowork corrected the dispatch's "4"→5, procurement ships two)** by its 5 facets per step, authoritative band visually distinct from prose, served by read-only `GET /procedures`; built as the **read-mode of the ONE component PLAN-0040 extends to edit-mode** (`mode:read|edit` + pure `facetModel(step)`, AC-7); **AT-2 RENDERED here though AT-2 generation is deferred (D7)**; **7 UI/endpoint OQs Cray-ratified ACCEPTED**. **ADR-0024 OQ errata (commit `4e56d4b`, bundled into #435):** records the ratified OQ disposition in the Accepted ADR's OQ section — Code could NOT inline it (editing an Accepted ADR is **G1-gated**; **in-context approval does NOT override the local-Ollama classifier**, fail-closed deny → routed via Cowork, the s77 chore-PR precedent); **NO decision changed (D1–D12 byte-identical, diff-verified)**. **Notes:** PLAN-0039 + errata bundled one PR / two commits (#435, Code-judgment, separable in history); **`loop-dispatcher` stays DISABLED**; **no live MS-S1** (docs only, §8); pre-commit detect-secrets + handoff-validation green. NEXT = build PLAN-0039 (the viewer) then dispatch PLAN-0040 (the generator, AT-1 family, G2-gated) | `c90b2d2` (#434) / `edd28a6` + `4e56d4b` (#435) / `docs/adr/0024-procedure-generator.md` + `docs/plans/0039-readonly-facet-viewer.md` |

### Recent-Decisions row — 2026-06-27 (PLAN-0040 AC-B5 live intake face DONE) [rotated 2026-07-01, session-91 reconcile]

| 2026-06-27 | **PLAN-0040 AC-B5 (the live MS-S1 single-shot intake face) SHIPPED + LIVE-VERIFIED → PLAN-0040 (A+B+C + live intake) DONE 100% (session 83, #457/#458/#459)** — the last PLAN-0040 item (LOCKED-9 / D9): narrative → classify → human-confirm → governed skeleton on live MS-S1 `gpt-oss:20b` (local-only, §8). Three **Code-direct per-step PRs off `main`, Cray merged each (no self-merge)**. **#457 server (`0fd0489` merge):** `services/api/routers/procedure_draft.py` — `POST /procedures/draft/{classify,build,instantiate}` (classify = narrative→archetype, no skeleton, LOCKED-5; build = CONFIRMED archetype→governed skeleton, refuses unconfirmed/unknown 422; instantiate = ZERO-LLM manual-pick fallback, D9); model-pinned + local-only; `_governance_todo`→public `build_governance_todo`; **security fold `5c00a76`** = classify rationale now `prose_lint`-gated (was leak-class-1) + degraded detail no longer echoes MS-S1 host/port; offline route tests (recorded-fixture, zero host-state). **#458 front-end (`0dd7693` merge):** `intake-procedures.js` capture (classify→confirm→build + graceful degradation to manual-pick/sample); `view-procedures.js` `mount(opts.draft)` renders via the **existing gate path** (no second renderer, LOCKED-8); `api.js` `O.Draft.*`; `?v=` c19→c20. **#459 prose fix from the live run (`ef46ea0` merge, `751c1e2`):** `_build_procedure_draft` falls back to **POSITIONAL** step pairing when the count matches — the live model does NOT echo template `step_id`s so descriptions dropped to `""`; advisory-prose only, governance untouched, +1 test. **Gate:** ruff+ruff-format+`mypy --strict services/` (64 files) clean; **pytest 1801 passed/24 skipped.** **LIVE (Cray-pre-approved host-state + hands-on UI verify):** **moat HOLDS** — poisoned narrative → build → forced values NOWHERE (leaked `[]`), all governance ABSENT, fails `validate_governance_complete` (D6); classify matches live for clear AT-1/AT-3 (conf 0.9–0.95), happy path = value-free advisory prose + unfilled stubs + empty `goal` (OQ-B B2). **Live findings (honest):** classify is non-deterministic + the strict per-step AT-2 cross-check → ~1-in-3 false-abstain (mis-tag of the judge step with AT-2-only `scored_rule`/`rule_gate` → correct abstain, never down-classify, LOCKED-7; SAFETY signal only, never builds, never leaks); the offline fixture masked the prose step-id-rename gap (live = cheapest catch). NEXT lever = classify-prompt enrichment (G2-gated → Cowork), NO guard relax without data + ADR. `loop-dispatcher` stays DISABLED | `0fd0489` (#457) / `0dd7693` (#458) / `ef46ea0` (#459) / `services/api/routers/procedure_draft.py` + `services/api/static/assets/{intake-procedures,view-procedures,api}.js` |

### Current-Focus blocks — Session 89 (A1b Step 1) + Session 88 (A1 landed) [rotated 2026-07-01, session-91 demo-close reconcile; R1 64 KB ceiling]

> **Session 89 (head_commit `719ea78`) — A1b STEP 1 (the demo-critical LIVE
> fail-closed principal-SoD run enforcement) SHIPPED + MERGED (#486) +
> INDEPENDENTLY VERIFIED (J1/J2 PASS).** INTERIM — one of A1b's six steps landed;
> A1b is NOT complete. This is the step that makes the A1a pure `check_principal_sod`
> actually fire on a REAL suspended-gate resolution (A1a shipped the construct +
> run-check + seam s88; A1b wires the live enforcement). **What it does:**
> `spec.parse_procedures` now reads `principals` / `principal_aliases` (were
> silently dropped on load); procurement ships **5 authored principals +
> `required_roles`** (AC-10); a **`step_principals` JSONB column on `PipelineRun`
> (+ Alembic `0004`)**; `orchestrator.run_procedure(principal=…)` records the
> requester per SoD step (**SD-2 = (a)**); and `action_step.resolve_gated_step`
> invokes `check_principal_sod` **unconditionally**, fails **CLOSED** (raises
> `PrincipalSoDError` carrying the structured verdict) **BEFORE** any approve /
> execute, and is **non-skippable**. **Inert for non-SoD procedures** (only
> procurement carries SoD; the aquaculture inert-reconcile test proves no behavior
> change elsewhere). **Gate (offline = the binding bar, §8):** ruff + mypy clean;
> **1921 offline + 27 DB tests green** incl. **8 NEW live-SoD DB tests** +
> `alembic upgrade head` (0004) + the aquaculture inert-reconcile. **Axis-B
> goal-gate: J1 PASS + J2 PASS** (high confidence, independent goal-evaluator,
> creator≠critic intact). **Demo-convergence framing:** this is **1 of 3
> demo-critical pieces** of the hero-demo's "governed → run → ฿" path; **A1b Steps
> 3 (`doa_tier` executor) + 6 (`governed_decision` audit-to-control) are next** =
> the rest of the demo-critical path (both offline-pure); Steps 2/4/5 (`OQ-6`
> marker · `rule_gate` · `scored_rule`) after; the parallel hero-demo session
> converges once that path is in (procedures/* hold releases). **Owed at A1b CLOSE
> (not per-step):** the PLAN-0044 SD-1/SD-2/SD-3-as-rec disposition + a PLAN-0044
> Completion note + a STATUS full-body reconcile. **Standing:** `loop-dispatcher`
> stays **DISABLED**; MS-S1 cold (A1b is offline, §8); AI-assisted (Claude Code,
> session 89), no `Co-Authored-By` per CLAUDE.md §7.

> **Session 88 (head_commit `f5c6342`) — A1 (run-time moat enforcement —
> Cray's #1 roadmap rock) LANDED end-to-end: ADR-0026 ACCEPTED (#479) → A1a
> (PLAN-0043) COMPLETE (#481/#482) → A1b planned (PLAN-0044).** A1 builds the
> principal-identity capability the AT-2 layer's run-time SoD was deferred on
> (the s85-s86 AC-13-ALT carry); A1a ships the construct + the run-check + the
> seam, A1b wires the live enforcement. **ADR-0026 ACCEPTED (#479, `620d799`):**
> the principal-identity capability + AT-2 run-time enforcement (the deferred
> ADR-0025 AC-13-ALT made concrete); all **6 OQs Cray-adjudicated as-recommended**.
> **PLAN-0043 (A1a) drafted + SD-1/SD-2 folded (#480, `05243eb`/`af0d882`):**
> Cray adjudicated **SD-1 = `required_roles` on `SoDConstraint`** and **SD-2 =
> a `PrincipalAlias` link object** (deviating from the drafted rec). **A1a COMPLETE
> end-to-end:** **Steps 1-3 (#481, `f1e7afa`)** = the `Person` / `PrincipalAlias`
> construct + `SoDConstraint.required_roles` + the H-governance (the new fields are
> governance, never on a draft type); **Steps 4-6 (#482, `f5c6342`)** =
> `services/engine/procedures/principal_sod.py`, the **fail-closed principal-SoD
> run-check** emitting a **STRUCTURED `PrincipalSoDVerdict`** + the
> `RunContext.principal` / `resolve_gated_step(principal=…)` seam + the offline
> oracle. **Gate: offline green throughout — the full procedures suite 344
> passed.** **A1a/A1b boundary confirmed (Cray s88):** the LIVE invocation of the
> run-check needs per-step principal RECORDING = the A1b executors' job; A1a stops
> at the construct + run-check + seam, A1b wires live enforcement. **A1b drafted =
> PLAN-0044 (in-flight, #484):** live run enforcement + per-kind executors
> (`doa_tier` / `rule_gate` / `scored_rule`) + audit-to-control (OQ-5); **3 SDs
> surfaced for Cray.** **Hero-demo dependency (a parallel session):** A1's
> structured `PrincipalSoDVerdict` + the A1b OQ-5 audit field are what the
> hero-demo's read-only "governance moment" render consumes — convergence ask #1
> is MET, #2 lands with A1b. **In-flight PRs awaiting Cray merge:** #483 (PLAN-0043
> `git mv` → `done/`) + #484 (PLAN-0044 A1b draft). **Standing:** `loop-dispatcher`
> stays **DISABLED**; MS-S1 cold (A1a is offline, §8); AI-assisted (Claude Code,
> session 88), no `Co-Authored-By` per CLAUDE.md §7.

### Recent-Decisions row — 2026-06-28 (PLAN-0041 classify-prompt enrichment RATIFIED) [rotated 2026-07-01, session-91 demo-close reconcile]

| 2026-06-28 | **PLAN-0041 (classify-prompt enrichment lever) RATIFIED + COMMITTED (session 84, #461)** — the fix for the PLAN-0040 AC-B5 live finding (~1-in-3 false-abstain on a textbook AT-1/AT-3). A **prompt-only** lever: enrich `build_classify_messages` with per-archetype descriptions (derived from the canonical catalog) + a positive band-vs-out-of-scope-gate explainer that teaches the band case, so the live model stops mis-tagging the judge step with an AT-2-only `gate_kind`. **Moat-safe:** the AT-2 cross-check (`_archetype_disagreement`/`_AT2_ONLY_KINDS`, ADR-0024 D4/D7) stays **byte-identical**; no schema change; **no new ADR**. **OQ-C twin-metric:** Arm B **11/11 AT-2-abstain HARD gate** + a pre-committed pass/fail read; offline tests = the gate, the live hit-rate lift = confirming evidence behind a Cray host-state go (§8). **Cowork-drafted (ADR-009 D1) → Code R2-reviewed (fact-pack byte-verified; LOCKED-7↔D4/D7 mapping confirmed) → Cray-ratified (OQ-A..E recs as-is) → committed → Cray merged (no self-merge).** Also session 84: a **strategy consultation** mapping vero-lite onto the **Four-Box Business Model** → a 4-rock roadmap (Rock 1 = PLAN-0041; Rock 2 = AT-2/managerial; Rock 3 = Box-4 economics + ontology data-binding; **Rock 4 = a Cowork 4-box+Palantir deep-research dispatch**, awaiting relay). NEXT = execute PLAN-0041 (offline Steps 1-4; live Step 5 = Cray go) + relay Rock 4. `loop-dispatcher` stays DISABLED | `7601174` (#461) / `docs/plans/0041-classify-prompt-enrichment.md` |

### Current-Focus block — Session 89 (head_commit `f5527d9`) — A1b Steps 3+6 [rotated 2026-07-01, session-92 reconcile; R1 64 KB ceiling]

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

### Recent-Decisions row — 2026-06-29 (ADR-0025 AT-2 managerial-layer RATIFIED + ACCEPTED) [rotated 2026-07-01, session-92 reconcile]

| 2026-06-29 | **ADR-0025 (AT-2 / managerial-process layer) RATIFIED + ACCEPTED (session 84, #463)** — makes DOA/SoD/scored-rule/compliance governance first-class (the Box-3 "Action = contract" story the Rock-4 research found is vero-lite's strongest sellable box; Palantir's Apr-2026 "each Action is a contract" ≈ our `Agent.allowed` + gate + audit); **revisits ADR-0024 D7** (AT-2 deferral) + **decides ADR-0024 OQ-8** (typed content sub-model). **Re-framed around a SHIPPED DEFECT Code R2 verified live on HEAD:** `derive_governance_todo` owes no obligation for `scored_rule`/`rule_gate`/`doa_tier` → `validate_governance_complete` is blind to AT-2 content (an empty-DOA AT-2 is run-loadable today). **D2** authoritative discriminated `Step.governance_content` keyed to `gate_kind` (not the non-authoritative facet; D2-A4 held); **D3** bypass structurally unrepresentable (`Decimal` money; total-cover DOA ladder; strict-escalate waiver; compliance+SoD non-waivable); **D5** run-gate becomes AT-2-aware (closes the defect, + a negative regression test); **D7** the AT-2 generator stays deferred under a CI-enforced N≥2 re-trigger (AT-2 = N=1). **Cowork-drafted + a Cowork-run panel (disclosed self-review, NOT independent of the drafter) → Code R2 = the independent check (substrate fact-pack independently verified) → Cray-ratified per the recs** (OQ-1=(c) build-layer/defer-generator [the N=1 "(b)-minus-codegen" trade accepted because the defect forces typing the obligation regardless]; OQ-2=(b)-in-(a); OQ-3=D6 boundary [concrete run-vs-author → the follow-on PLAN]; OQ-4/5 per rec). A harness Stop-hook said "commit as Accepted" pre-ratification — Code **declined** (false attribution on the permanent record), held, committed on Cray's actual ratify. NEXT = the follow-on build PLAN (OQ-5, separate dispatch). Also s84: O-1 (Box-4 ฿ pitch artifact) done; the Rock-4 research delivered + the O-sequence locked | `f56a6e8` (#463) / `docs/adr/0025-at2-managerial-layer.md` |

### Current-Focus block — Session 91 (head_commit `b4c03a9`) [rotated 2026-07-01, session-93 reconcile]

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

### Current-Focus block — Session 91 (head_commit `788994d`) [rotated 2026-07-01, session-93 reconcile]

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

### Recent-Decisions row — 2026-06-29 (PLAN-0042 O-3 AT-2 build PLAN DRAFTED+RATIFIED+MERGED, #465) [rotated 2026-07-01, session-93 reconcile]

| 2026-06-29 | **PLAN-0042 (the O-3 follow-on AT-2 / managerial-layer BUILD PLAN) DRAFTED + RATIFIED + MERGED (session 85, #465)** — the build PLAN ADR-0025 OQ-5 named; renders ADR-0025 (Accepted #463) D1–D8 + owns migration sequencing. **Build PLAN — no new ADR.** **Primary deliverable = closing a LIVE shipped defect:** `validate_governance_complete` is blind to AT-2 *content* (`rule_gate` evaluate → `[]`; `scored_rule`/`doa_tier` action → `[handler,autonomy]`, both filled → no AT-2-content obligation) → the build **types the AT-2 content** (D2 discriminated `Step.governance_content` union + `Procedure.separation_of_duties`), makes the **run-gate AT-2-aware** (D5), and **migrates the procurement AT-2 prose→typed in ONE PR behind a green golden test** (the migration trap). **Cray-ratified:** **OQ-A = A1** (author + render only — no principal-identity layer for run-time SoD, so D6 author+render fallback; the A2 run path deferred to a follow-on PLAN); **OQ-B = B2** (labelled-provisional placeholder control values + Cray sign-off — typing D2 is authoring not transcription); **OQ-C/D/E confirmed** (golden test + D5 migration in ONE PR; scoped value-only prose-lint + "ADVISORY — NOT A CONTROL" band; no per-spec `schema_version`). **Process:** Cowork-drafted (ADR-009 D1) → **Code R2** re-verified the fact-pack on HEAD `1305b32` + surfaced two substrate items: **finding 1** (a `Step.tiers` collision — `StepTiers` = PLAN-0022 handler taxonomy at `spec.py:264`, in `STEP_GOVERNANCE_FIELDS` → DOA tiers must nest in `DoaLadder`, never a 2nd top-level `Step.tiers`) and the **SoD principal-vs-role scoping finding** (A1 = author-time structural+role-level SoD; principal-identity SoD is run-time → relocated to the deferred **AC-13-ALT**, lineage = superseded-by-A1, not an ADR amendment) → Code revision dispatch → Cowork applied 3 surgical deltas → Cray-ratified → Code R2 + committed (#465). **v1 build surface = Steps 1–3 + 5** (A2 / AC-13-ALT deferred). `loop-dispatcher` stays DISABLED; MS-S1 cold, no live run (offline oracle is the gate). NEXT = execute Step 1 (D2 union + SoD + D3/D4) then Step 2 (D5 gate + migration in ONE PR; author the B2 placeholders) | `21d7669` (#465) / `docs/plans/0042-at2-managerial-build.md` |

### Current-Focus block — Session 92 (head_commit `4f22602`) [rotated 2026-07-02, session-93 build-close reconcile]

> **Session 92 (head_commit `4f22602`) — PLAN-0044 A1b STEPS 2 + 4 MERGED
> (offline close-out) — two PRs (#499 Step 4 the `rule_gate` per-kind executor
> / #500 Step 2 the OQ-6 N≥2 shared-`Person` re-trigger marker).** INTERIM at
> merge — **then A1b CLOSED later this same session:** AC-9 merged (#502 `ea27b27`,
> Option 2 — a verified no-op audit-receipt terminal (`echo`) is exempt downstream
> of a gate, forge-proof handler-allowlist), and **PLAN-0044 + PLAN-0045 (hero-demo
> v1) Completion-noted + `git mv` → `done/`.** All 12 PLAN-0044 ACs met; offline
> suite 2026 passed. The hero-demo `compliance` harness→`rule_gate`-executor swap is
> an OPTIONAL follow-up (out of scope for both PLANs).
> **#499 (feat `a458142`, merge `05c9541`, A1b Step 4 / AC-6) — the `rule_gate`
> per-kind executor:** NEW `services/engine/procedures/rule_gate.py` — a pure
> `evaluate_compliance(gate, candidate)` reads the candidate's per-criterion
> `compliance` signal map (data-access = (a), mirrors `scored_rule`'s
> `candidate_quotes`) and **blocks the PO on ANY failed criterion** (candidate
> tagged non-`compliant` → dropped by the downstream `approve` `where:
> {compliant: true}` fan-out). **Non-waivable by type** (`blocks_po` is
> `Literal[True]`; no pass-a-failed-rule path). **Fails CLOSED** — non-mapping
> candidate / no `compliance` map → `RuleGateError`; an absent-OR-false
> per-criterion signal fails that criterion. v1 does NOT evaluate the prose
> `spec` predicate (deferred to the A2 run path, ADR-0025 D2) — it enforces the
> GATE. `services/engine/procedures/governance_step.py` gains a NEW
> **`GovernanceEvaluateExecutor`** (SD-1=(a) dispatching wrapper for the
> EVALUATE StepKind, sibling of `GovernanceActionExecutor`): its `rule_gate`
> branch tags each candidate `compliant` + audits (`governed_kind: rule_gate`),
> never calls the base (compliance has no numeric band) nor the LLM (governed ≠
> generated, ADR-0019 IN-3); a banded `judge` step falls through to the shipped
> `EvaluateStepExecutor`. **17 new tests**
> (`tests/services/engine/procedures/test_rule_gate.py`). **#500 (test
> `12ac1dd`, merge `4f22602`, A1b Step 2 / AC-10 re-trigger half; mirrors
> ADR-0025 D7) — the OQ-6 N≥2 shared-`Person` re-trigger marker:** NEW
> `tests/services/engine/procedures/test_principal_identity_retrigger.py`
> counts the verticals whose `procedures.yaml` ships `principals` and **FAILS
> the moment a SECOND vertical ships principals (N≥2)** — making the shared/core
> `Person` extraction deferral (ADR-0026 OQ-6=(b)) **self-cancelling** rather
> than a silent `# TODO`. Currently N=1 (procurement only). **3 tests.**
> **Verification:** ruff + mypy clean; full offline suite **2020 passed / 5
> skipped** (verified on the merged main `4f22602`). Offline-only, no
> host-state; **no PO issued** (render / block only, ADR-0007 LOCKED #3).
> **Routing:** both non-gated Code `feat/*`/`chore/*` feature PRs executing the
> already-accepted PLAN-0044 (no new PLAN/ADR); Code merged per the established
> session-91 workflow. **NEXT (still A1b close-out):** **AC-9** — a Cray
> decision is owed (the procurement `audit` step is authored `autonomy: auto`
> AND downstream of the `approve`/`issue_po` gates, so the AC-9
> "auto-downstream-of-a-gate" assertion would **restructure the hero
> procedure** — restructure the audit terminal vs exempt no-op terminals) PLUS
> the hero-demo `compliance` harness → `rule_gate`-executor swap follow-up
> (needs intake compliance-signal enrichment + the off-AVL-exception narrative
> call). Then the PLAN-0044 Completion note + `git mv` PLAN-0044/0045 →
> `done/` + a full-body STATUS reconcile at A1b CLOSE. Phase-3 product ADRs
> (generalize the `scored_rule`/`rule_gate` data-access = the Q3
> ontology-binding gap) deferred. **Standing:** `loop-dispatcher` stays
> **DISABLED**; MS-S1 cold (remaining A1b is offline, §8); AI-assisted (Claude
> Code, session 92), no `Co-Authored-By` per CLAUDE.md §7.

### Recent-Decisions row — 2026-06-29 (PLAN-0042 v1 OFFLINE TAIL COMPLETE, session 86) [rotated 2026-07-02, session-93 build-close reconcile]

| 2026-06-29 | **PLAN-0042 v1 (O-3 AT-2/managerial layer) OFFLINE TAIL COMPLETE → v1 (Steps 1–3 + 5) COMPLETE (session 86, #470/#471/#472, all Cray-merged)** — the offline A1 tail of the AT-2/managerial build; PLAN `git mv` → `done/`. The AT-2 layer is now typed + run-gated + rendered authoritative (with the advisory band) + red-teamed offline. **Step 3a (#470, feat `4ff1180`):** the scoped value-only prose-lint over AT-2 free-text (`governance_prose_lint` = value classes + an approver-role-token check; OMITS the decision-verb + broad-identifier classes, finding 6) + a LOAD gate (`Procedure._validate_at2_free_text` blocks load on a ฿-amount/weight/role token smuggled into AT-2 free-text) + the 3 ADR-0025-D4 advisory NON-AUTHORITATIVE free-text fields (`EmergencyWaiverPolicy.justification`, `DoaTier.note`, `ScoredCriterion.note`); one reword (`"3-bid"`→`"three-bid"`). **Step 3b (#471, feat `5fac5d2`):** the PLAN-0039 read-only viewer renders the typed AT-2 content (DOA ladder/scored rule/compliance gate/SoD) as AUTHORITATIVE (the Box-3 "the gate is no longer blind" artifact, AC-13) + bands the AT-2 free-text "ADVISORY — NOT A CONTROL" (OQ-D); no API change (`model_dump` serializes it), verified live on the preview. **Step 4 (AC-13) = author + render only (A1)** — delivered by Step 3's render, no separate build. **Step 5 (#472, test `5464831`):** the D8 offline oracle `tests/services/engine/procedures/test_red_team_at2.py` consolidates the 3 red-team fixtures (hollow-but-complete → refused; leak-in-free-text → blocks load; identity-collapse role-level = single-step SoD rejected at construction + a missing-SoD `doa_tier` proc refused at the gate) + a positive control; PRINCIPAL-level collapse / literal `approver_role==requester_role` / un-gated-audit are A2-deferred (AC-13-ALT), documented + intentionally NOT asserted (no false coverage). Gate (every step, offline): ruff + ruff-format + `mypy --strict services/` (64 files) clean, **pytest 1877 passed / 24 skipped**, no live MS-S1. **AC-13-ALT (the A2 run path)** deferred to a follow-on PLAN, gated on a principal-identity-resolution capability the engine lacks today. OQ-B placeholder control values stay provisional (real Fastenal figures fold in via a small `verticals/`-only PR, B1; blocks nothing). `loop-dispatcher` stays DISABLED | `973ba69` (#470/#471/#472) / `services/engine/procedures/{spec,draft,orchestrator}.py` + `tests/services/engine/procedures/test_red_team_at2.py` + `services/api/static/assets/view-procedures.js` + `docs/plans/done/0042-at2-managerial-build.md` |

### Recent-Decisions row — 2026-06-29 (PLAN-0042 Steps 1-2 SHIPPED, session 85 cont.) [rotated 2026-07-02, session-93 build-close reconcile]

| 2026-06-29 | **PLAN-0042 (O-3 AT-2/managerial layer) Steps 1-2 SHIPPED + MERGED (session 85 cont., #467/#468)** — typed AT-2 content (D2) + the AT-2-aware run-gate (D5) closing the live blindness defect; the procurement AT-2 migrated prose→typed behind a green golden test; OQ-B=B2 values mirror the data adapter (provisional, pending Cray sign-off). **Step 1 (#467, `6176b18`):** discriminated `Step.governance_content` (`DoaLadder`\|`ScoredRule`\|`ComplianceGate`, keyed on `kind`) + `Procedure.separation_of_duties`; D3 bypass unrepresentable (`Decimal` money; closed `RelaxableConstraint` enum can't name compliance/SoD; `blocks_po`/`requires_justification` `Literal[True]`; total strictly-monotonic DOA ladder); D4 H-field invariants (new fields in `GOVERNANCE_FIELDS`, never on a draft type; draft-disjointness + `StepFacet`-unreachability CI). Finding 1 honored (DOA tiers nest in `DoaLadder`, no 2nd `Step.tiers`). **Step 2 (#468, `059c6ea`):** the AT-2-aware run-gate + the prose→typed migration in ONE PR behind the golden test — `validate_governance_complete` now owes typed `governance_content` on the AT-2 kinds + a `doa_tier` proc owes `separation_of_duties`; an empty-DOA/no-criteria/no-SoD AT-2 is no longer run-loadable (the negative hollow-but-complete regression = the D5 ratification gate). **Build interps:** principal-level SoD + resolved-tier strict-escalation deferred to **A2 (AC-13-ALT)** — no engine principal/role-rank layer; the author-time gate enforces the STRUCTURAL form (≥2 distinct steps; ladder totality). Gate: mypy --strict + ruff clean, **pytest 1843/24**; no live MS-S1. Remaining: Steps 3 (prose-lint + "ADVISORY — NOT A CONTROL" banding) + 5 (offline oracle), A1 | `059c6ea` (#467/#468) / `services/engine/procedures/{spec,draft,orchestrator}.py` + `verticals/procurement/procedures.yaml` |

### Current-Focus block — Session 93 cont. (head_commit `eb63692`) — PLAN-0046 build-close [rotated 2026-07-02, session-94 run-2 receive reconcile; R1 64 KB ceiling]

> **Session 93 cont., 2026-07-02 (head_commit `eb63692`) — PLAN-0046 (Q3
> READ-SIDE ONTOLOGY-BINDING BUILD) EXECUTED + COMPLETE + CLOSED — one feat PR
> (#511 feat `878b517`, merge `d95f0a2`) + the close PR (#512 docs `eb63692`,
> merge `ac8ad24`); PLAN Completion-noted + `git mv` → `done/`.** Renders the
> Accepted ADR-016 Q3 amendment into code; **all 11 ACs met.** **Step 1
> (AC-1..3):** `StepInput.reads: list[str] | None` (typed data-sourcing entry
> point, OQ-5 list) + `AgentAllowed.object_types: list[str]` (read-side
> blast-radius allowlist mirroring `action_handlers`); both `extra="forbid"`,
> backward-compat (absent/empty = loads as today; OQ-6 empty=unconstrained).
> **Step 2 (AC-4..8):** NEW pure `validate_read_bindings(procedure, agent,
> object_type_names)` in `orchestrator.py` (SD-1 Option A —
> `validate_runnable`'s signature + all ~12 call-sites untouched); each query
> step's `reads` element must ∈ the vertical's ontology AND (when the agent
> opts in) ∈ `allowed.object_types`, else `ProcedureError` naming the object +
> failed condition; wired at the 2 production pre-flight sites
> (`run_procedure` + `persistence.resume_run`) via
> `validate_read_bindings_for_vertical` (builds the registry from
> `load_ontology_meta(vertical)`; SKIPPED entirely — no ontology I/O — for a
> reads-absent procedure). **Zero runtime-data-flow change**
> (`_resolve_input`/seeds untouched). AC-5 refuse pass/fail read pre-committed
> in the test module BEFORE the tests; AC-7 wiring test runs against the REAL
> aquaculture registry. **Step 3 (AC-9/10):** `reads` →
> `STEP_GOVERNANCE_FIELDS` (H, OQ-A); `object_types` confirmed covered via
> `allowed` (asserted, not re-added); PLUS one disclosed build-level hardening
> beyond the PLAN's letter (consistent with OQ-A "never model-emitted", no ADR
> decision changed): `StepDraft` REUSES `StepInput` so a generated draft CAN
> physically carry `reads` — `lift_to_step` now strips it to an ABSENT stub
> (`_strip_read_binding`, the OQ-C C1 inject-absent pattern / `env_var`
> precedent) + a CI tripwire test. **Step 4 (AC-11):** 12 new tests; ruff +
> ruff-format + `mypy --strict services/` clean; **full offline suite 2066
> passed / 5 skipped.** Honest frame delivered (LOCKED-9): declared ✔ ·
> consistency-gated at load ✔ · execution-bound ✖. **SD dispositions:** SD-1 =
> Option A (as ratified); SD-2 = Option A (no vertical migrated; gate inert
> until opt-in). Offline-only — no host-state, no live run. **NEXT:** the Q4
> generic run-consume query executor is a SEPARATE later PLAN (deferred by
> ADR-016 Q3); otherwise the parked backlog (Rock sequence /
> PLAN-0010/0012/0019/0027 / partner-GTM) — a Cray pick. **Standing:**
> `loop-dispatcher` stays **DISABLED**; MS-S1 cold; AI-assisted (Claude Code,
> session 93), no `Co-Authored-By` per CLAUDE.md §7.

### Current-Focus block — Session 93 (head_commit `cb7eb05`) — ADR-016 Q3 amendment + same-session UPDATE [rotated 2026-07-02, session-94 run-2 receive reconcile; R1 64 KB ceiling]

> **Session 93 (head_commit `cb7eb05`) — ADR-016 Q3 READ-SIDE ONTOLOGY
> OBJECT-BINDING AMENDMENT ACCEPTED (Rock 3 / O-2, PR #505) — an in-place
> ADR-016 D2+D3 amendment closing the read-side governance gap that mirrors the
> shipped write-side.** Two commits: `915c344` (Proposed) + `cb7eb05` (fold the
> ratified decisions → **Accepted**). **Decision (contract-first):** a typed
> `StepInput.reads: list[str]` read entry point (OQ-5: **list, not `str`** —
> procurement `intake` reads 3 object types + joins); `Agent.allowed.object_types`
> mirroring `action_handlers`; **LOAD-time enforcement** (`reads ∈ ontology ∩
> allowlist`, else refuse load) — **zero runtime-data-flow change.** **Honest
> enforcement frame (Cowork caught, Code-verified):** v1 = a typed read contract
> + a load-time consistency/scoping gate, **NOT** runtime-enforced parity — even
> write-side `action_handlers` is only pre-flight-checked in `validate_runnable`;
> teeth = declared==dispatched, and the read side gains that only at **Q4**.
> **Deferred:** the generic run-consume **query executor** → a fast-follow build
> PLAN (touches runtime flow + enrich/join steps); the **Box-4 economic-impact
> facet** → a self-cancelling **N≥3** marker (typed facet only; the economic
> dimension is prose-captured at vertical authoring). **Governance decisions
> ratified (OQ-1..6/A):** OQ-1 `StepInput.reads` · OQ-2 load-gate + reframe ·
> OQ-3 `object_types` bounds `fetch_objects` only (links/events out of v1) · OQ-4
> `where` = post-fetch · OQ-5 `reads: list[str]` · OQ-A `reads`/`object_types`
> H-governed (`object_types` auto-covered; add `reads` to
> `STEP_GOVERNANCE_FIELDS` = a build-PLAN task) · OQ-6 `object_types` empty =
> unconstrained (backward-compat). **Three-lens review process:** `plan-drafter`
> **AUTHORED** the amendment + folded the ratified decisions; **Cowork Tier-1b**
> delivered an independent second-perspective review (caught the parity
> over-claim + surfaced OQ-5); **Code R2-verified** every claim on disk +
> committed; **Cray ratified** OQ-1..6/A. **Impl note for the build PLAN:** the
> load-gate must thread the vertical `OntologyMeta` into pre-flight
> (`validate_runnable(procedure, agent)` doesn't carry it today). **NEXT = the
> fast-follow build PLAN** (implement `StepInput.reads` + `Agent.allowed.object_types`
> + the load-gate + `reads`→`STEP_GOVERNANCE_FIELDS` + tests); the generic query
> executor (Q4) is a separate later PLAN. **Standing:** `loop-dispatcher` stays
> **DISABLED**; MS-S1 cold (offline, §8); AI-assisted (Claude Code, session 93),
> no `Co-Authored-By` per CLAUDE.md §7.
>
> **UPDATE (same session):** the fast-follow build PLAN is now **PLAN-0046** —
> drafted → Cowork-lens-informed Code R2 → Cray-ratified (SD-1 separate
> `validate_read_bindings` entry point + SD-2 verticals-stay-absent) → merged
> **Ready for execution** (#509, `d544414`). NEXT = execute Steps 1–4 (offline
> gate; no live run).

### Current-Focus block — Session 94 (head_commit `eb63692`) — partner-sim run-1 rehearsal, fork (a) [rotated 2026-07-03, session-94 run-2 rehearsal reconcile; R1 64 KB ceiling]

> **Session 94, 2026-07-02 (head_commit `eb63692` unchanged — WORKING-TREE
> EVENT, no commit; #513/#514 were `docs(status)` merges, excluded) — ADR-0020
> PARTNER-SIM RUN-1 REHEARSAL (fork a) COMPLETE — the intake/mapping/PDPA-RoPA
> pipeline run FOR REAL against the synthetic TWP package; 8 findings + 3
> net-new decomposed into tagged work items.** **Cray selected fork (a)**
> (explicit AskUserQuestion pick, 2026-07-02) over (b) the Q4 executor PLAN.
> Deliverable (gitignored + SYNTHETIC-bannered per ADR-0020 R3 — NEVER
> unlabeled into benchmark/REPORT/ADR-011 contexts):
> `docs/research/private/2026-07-02-partnersim-run1-rehearsal-intake-mapping-pdpa.md`.
> **§1 Intake rehearsal:** TWP's answers graded vs the one-pager's 6 asks —
> **5 DELIVERED, ask-6 (DPA+pseudonymization) CONDITIONAL**; key result: ask-1
> delivers the artifacts but its engineering purpose FAILS (historical
> principal identity unresolvable: shared OPER1, LINE display-name ≠
> decision-maker). **§2 Mapping rehearsal vs `energy_v0.yaml` — real gaps
> clean fixtures never showed:** `asset_type` enum lacks
> feeder/cap_bank/gas_engine; `measured_kind` lacks current/voltage (+ missing
> `quantity_bindings`); TWP's STATUS column splits 3 ways (verdict →
> recomputed, transitions, actions); band-model gaps = 4-zone top-oil
> (78/87/92) + seasonal 300A vs our 3-zone `in_file_band` (bus-voltage
> 21.4/21.6 kV fits exactly); era-scoped surrogate-PK rule; per-source
> TZ/พ.ศ./dedup rule set; versioned ingest (bitemporal-lite — serves the กกพ.
> as-reported view + PDPA DSR). PLAN-0005 §8.1 mapping trigger NOT tripped
> (synthetic) — the mapping spec is designed in advance, builds at the
> real-data trigger. **§3 PDPA-RoPA:** RoPA-lite built cleanly from TWP §5
> labels; minimization cheap (tokenize 2–3 columns); worker-committee 30+d
> constraint → role-level-audit mode proposed as the pre-clearance posture;
> residency = straight win (their no-foreign-cloud mandate fits our
> on-prem/local-LLM posture verbatim). **§4 Work items:** F1–F8 (the run-1
> findings) + net-new **F9** (energy-v0 enum coverage → an "energy v1 ontology
> batch" candidate), **F10** (instance-scoped authority — per-feeder + ฿ caps
> vs our type-scoped `AgentAllowed.object_types` → generalized-schema input),
> **F11** (refused-field degraded modes → UI backlog, trigger-gated); tags
> [MAP]/[ENG]/[GTM]/[INTAKE]/[DEFER], each routed to its owning thread.
> **Nothing starts a build today.** **§5:** 7 intake-instrument additions for
> the real meeting — validates Cray's standard-intake-form template
> observation (lineage = the partner-facing ONE-PAGER, NOT the R1-clean
> variant). **R2:** an independent reviewer subagent verified the report vs
> all sources (schema/PDPA/R3/arithmetic claims confirmed); 2 findings applied
> (top-oil zone-count phrasing clarified; a §8.1 quote-casing nit). **NEXT
> (Cray-owned):** the ADR-0020 D4 post-run-1 review (owed before any 2nd
> business type) + the next pick — (b) the Q4 generic query executor PLAN, or
> the rehearsal-enriched backlog. **Standing:** `loop-dispatcher` stays
> **DISABLED**; MS-S1 cold (nothing touched it); AI-assisted (Claude Code,
> session 94), no `Co-Authored-By` per CLAUDE.md §7.

### Current-Focus block — Session 94 cont. (head_commit `255627b`) — ADR-0020 D4 post-run-1 review [rotated 2026-07-03, session-94 CLOSE reconcile; R1 64 KB ceiling]

> **Session 94 cont., 2026-07-02 (head_commit `eb63692` → `255627b` — #516
> `docs(conventions):` is SUBSTANTIVE per lint policy, merge `cb161a4`) —
> ADR-0020 D4 POST-RUN-1 REVIEW COMPLETE — verdict: CONTINUE WITH ADJUSTMENTS
> (Cray-ratified, explicit AskUserQuestion pick); 4-lens specialist panel: all
> R-PS triggers NOT-FIRED; C-1..C-3 confirmed; adjustment (i) landed as
> #516.** D4 executed via a 4-lens adversarial (refute-not-bless) specialist
> subagent panel — R-PS1 circularity skeptic / R-PS2 provenance auditor /
> R-PS3 messiness-value judge / domain-realism; findings attributed as agent
> findings, load-bearing instruction quotes code-verified before acting.
> **Verdicts:** R-PS1 NOT-FIRED (HIGH on the trigger; broader R1 assurance
> capped MEDIUM by the input-hygiene finding) · R-PS2 NOT-FIRED (VERY HIGH,
> 6/6 provenance checks clean) · R-PS3 NOT-FIRED (HIGH ~0.9) · domain realism
> SOUND-WITH-CAVEATS (กกพ. quarterly premise web-verified; worker-committee
> 30-d gate down-weighted to partner-conditional — LPA s.96 remit is welfare,
> not monitoring approval; role-level-audit mode retained on independent PDPA
> grounds). **Key panel finding (the material one):** the RATIFIED inputs
> themselves leaked vendor vocabulary — instruction §4.2(4) carried
> "over-threshold (breach), watch/near-threshold, and normal" (2/3 of our
> band labels) and §5 carried "restart / isolate / dispatch a technician"
> (3/4 of the action enum). The run-1 "WATCH = organic SCADA term" narration
> is REFUTED (reclassified `was an error`); the S-2 PASS itself stands
> `confirmed — prior intact` on amended grounds (uptake from a ratified input
> ≠ the R-PS1 breach vector; every one-pager fingerprint affirmatively absent
> — the persona declined "restart" for the organic "reclose"). **C-1..C-3
> input-state deviation: CONFIRMED by Cray** (Desktop check: no connected
> folders / current canonical instructions / no project-knowledge files) —
> the run-1 record is fully closed. **No trigger fired → ADR-0020 unchanged.
> Adjustments:** (i) instruction band-labels + action-menus stripped = **#516
> landed** (Cray must RE-PASTE the updated canonical into the partner-sim
> project UI before any run 2 — repo-canonical / UI-derived); (ii) an
> R1-stripped PDPA-checklist paste-variant created (gitignored:
> `docs/research/private/2026-07-02-pdpa-checklist-partnersim-paste-variant.md`
> — the ONLY PDPA doc cleared for future partner-sim pastes); (iii)
> run-2-time: fresh project per SD-2 + an unannotated bulk sample at a
> realistic historian rate + a persona-brief fix (drop the implausible
> municipal-service claim / model the customer-PII surface). **Record
> hygiene:** the D4 addendum (panel verdicts + record corrections — the "0
> hits" input-screen claim corrected to ~8 benign PDPA-sense "breach" tokens;
> the reclose §5 misattribution; R-PS3 strict count 4+2 ≥ N=3) appended
> APPEND-ONLY to the run-1 receive checklist (gitignored). **New value
> surfaced by the panel:** an unannotated authority violation sits in the
> run-1 package (หัวหน้ากะ reclose-1 on F-07, reserved to วิศวกรเวร+) = a
> ready-made audit-detection test-case fixture; 10 domain blind-spot classes
> listed for run 2 / the real intake form (relay-event reconciliation,
> PEA/EGAT interchange metering, topology drift, customer PII, Thai encoding,
> …). **NEXT (Cray-owned):** the standing pick — (b) the Q4 generic query
> executor PLAN, or the rehearsal-enriched backlog; run-2 preconditions
> recorded, run 2 itself stays unscheduled. **Standing:** `loop-dispatcher`
> stays **DISABLED**; MS-S1 cold (nothing touched it); AI-assisted (Claude
> Code, session 94), no `Co-Authored-By` per CLAUDE.md §7.

### Current-Focus block — Session 94 cont. (head_commit `255627b`) — ADR-0020 partner-sim run-2 receive (supply-chain, S-1..S-6 PASS) [rotated 2026-07-04, session-95 CLOSE reconcile; R1 64 KB ceiling]

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

### Current-Focus block — Session 94 cont. (head_commit `255627b`) — ADR-0020 partner-sim run-2 rehearsal + 2-run cross-vertical synthesis [rotated 2026-07-04, session-95 CLOSE reconcile; R1 64 KB ceiling]

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

### Current-Focus block — Session 94 CLOSE (head_commit `f63c975`) — ADR-0020 partner-sim trial complete both verticals + C-1..C-3 confirmed [rotated 2026-07-04, sessions-96/97 reconcile; R1 64 KB ceiling]

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

## Rotated this reconcile (sessions-96/97 CLOSE, 2026-07-04 — PLAN-0048/0049 COMPLETE + ADR-0027 Accepted #541/#550/#551)

### Current-Focus block — Session 95 CLOSE (head_commit `f63c975` → `28d919c`) — PLAN-0047 pre-pilot hardening sprint COMPLETE [rotated 2026-07-04, sessions-96/97 CLOSE reconcile; R1 64 KB ceiling]

> **Session 95 CLOSE, 2026-07-03 → 2026-07-04 (head_commit `f63c975` →
> `28d919c` — #531 `docs(plans):` close-out is SUBSTANTIVE per lint policy,
> merge `353c04e`) — PLAN-0047 PRE-PILOT HARDENING SPRINT COMPLETE: all 7
> steps + all 10 ACs (PRs #522–#530), +31 tests (suite 2066 → 2097 passed /
> 5 skipped); sales claims (authn / audit / exactly-once / config-pin) now
> code- and CI-backed.** (Reconcile committed by the successor session per
> the s95 CLOSE handoff.) **Arc:** a 3-specialist production-readiness
> audit (in-chat; codegen/governance/compliance lenses) surfaced BLOCKER
> gaps → Cray ratified a 7-item hardening sprint + ordering. **4
> web-research briefs** (gitignored `docs/research/private/`, all
> 2026-07-03): ontology-llm-market-landscape (thesis SUPPORTED;
> commoditized layer ⇒ sell vertical content + generator + governed
> actions, mid-market price); llm-db-reliability-techniques (we ARE the
> CaMeL/OWASP reference architecture; ADOPT reason-then-structure, outbox
> [done in spirit via Step 4], OTel gen_ai.*, OSI export);
> local-llm-stack-viability (local-first stands; pitch "compute never
> leaves"; keep the `gpt-oss:20b` pin; open a Qwen 3.5/3.6-27B Thai eval
> track — host-state, Cray gate); semantic-foundation-build-techniques (R1
> context-pack emitter +17–23pp evidence · R2 meta-schema fields [synonyms
> th/en, sample_values, verified_queries, grain] · R3 schema-guided
> bootstrap · R4 usage-mined loop human-gated; Thai = uncovered moat).
> **5-wave backlog re-order (Cray-agreed):** W1 = PLAN-0047 ✅ · W2 = Q4
> executor PLAN + v1 ontology bundle (energy-v1 + supply-chain-v1 + R1 +
> R2 + migration-autogenerate) + a small reason-then-structure item · W3
> (parallel, Cowork) = GTM pack + standard intake form (11 additions) · W4
> = ADR-016 Phase-3 monitor PLAN + sprint items 5/6-remainder + ops · W5 =
> coverage eval + raw-vs-layer re-benchmark + optional partner-sim run-3 →
> real partner intake. **PLAN-0047 (plan-drafter authored, draft #522
> `b6cb0d5`; SD-1..4 ratified as-recommended #523 `8198548`: SD-1=(a) API
> keys · SD-2 defer · SD-3 yes-minimal · SD-4 CI w/ DB) EXECUTED
> COMPLETE:** Step 7 CI (#524 `0401a0a`) — the repo's FIRST CI gate: ruff
> + ruff-format + `mypy --strict` + full suite w/ postgres container +
> `alembic upgrade head` on every PR; 2066 baseline green; every sprint PR
> from #525 on ran green under it. Step 1 authn (#525 `3b3db46`) —
> `services/api/auth.py` fail-closed API-key gate on state-changing
> routes; `/warm` + `/sleep` + `/intake/generate` also gated (disclosed
> deviation); `action_identity` sidecar table (alembic 0005). Step 2
> endpoints (#526 `5da9e1d`) — POST `/procedures/{id}/run` +
> `/runs/{id}/gate/resolve` (auto-resume); identity recorded server-side
> (AC-2 on the persisted row); registry executor-factory seam. Step 3 gate
> state machine (#527 `a0db450`) — RESOLVED status; resume refuses
> undecided proposal gates + SoD tie re-assert; optimistic lock (alembic
> 0006 `pipeline_runs.version`); AC-5 narrowing disclosed (empty-watch
> contract kept). Step 4 write-ahead (#528 `bafdf92`) —
> `run_procedure_persisted` (write-ahead + per-step commits via
> `on_step_complete`); two-phase resolve — decision committed BEFORE
> effect; version bump AT decision commit = exactly-once under
> concurrency; `pending_execution` entries = the outbox seam. Step 5
> append-only audit (#529 `692f748`) — hash-chained `audit_log` + block
> trigger + INSERT-only `vero_audit_writer` role (alembic 0007);
> run_started/gate_decision/handler_receipt/run_resumed/gate_refused each
> in-transaction; tamper-detect survives a superuser. Step 6 config
> pinning (#530 `6cde2db`) — `governance_pin.py` + snapshot/hash on
> `pipeline_runs` (alembic 0008); fail-closed pin-mismatch at resume +
> gate; prose excluded; people deliberately NOT pinned. Close-out (#531
> `28d919c`, merge `353c04e`) — completion fold (Status → Complete, 10 ACs
> ticked, step→PR table, 5 disclosed deviations) + `git mv` →
> `docs/plans/done/0047-pre-pilot-hardening-authn-gate-audit.md`.
> **Disclosed local dev-box state:** local `.env` gained
> `API_AUTH_ENABLED=false` (code default now ON — preserves demo UX); dev
> DB migrated through alembic 0008 (0005 action_identity · 0006
> `pipeline_runs.version` · 0007 audit_log + trigger + role · 0008
> governance-pin columns). Session-95 CLOSE handoff:
> `.claude/handoffs/session-95/2026-07-04-0014-code-session95-CLOSE-plan0047-hardening-sprint.md`.
> **Standing:** `loop-dispatcher` stays **DISABLED**; MS-S1 cold (the
> entire sprint was offline); AI-assisted (Claude Code, session 95), no
> `Co-Authored-By` per CLAUDE.md §7.

### Recent-Decisions row — 2026-06-29 (PLAN-0041 classify-prompt enrichment lever COMPLETE, session 87) [rotated 2026-07-04, sessions-96/97 CLOSE reconcile]

| 2026-06-29 | **PLAN-0041 (classify-prompt enrichment lever) COMPLETE (session 87, #475/#476 + live AC-7 PASS)** — the fix for the PLAN-0040 AC-B5 ~1-in-3 false-abstain on a textbook AT-1/AT-3; a **PROMPT-ONLY** lever to lift the live AT-1-family classify match-rate. **Moat byte-identical** — the abstain-guard (`_archetype_disagreement`/`_AT2_ONLY_KINDS`/`_BAND_KINDS`, ADR-0024 D4/D7) unchanged; no schema change; **no new ADR**. **Steps 1-3 (#475, feat `035af38`):** `ArchetypeTemplate.description` (value-free, from the canonical catalog) + a 3-tuple classify catalog + a value-free `_BAND_EXPLAINER` into `build_classify_messages` (ends "When unsure … abstain" = the R2 moat-safety brake); offline gate AC-1..5 (guard byte-identity introspection; AT-2-only-abstain generalized to scored_rule/rule_gate/doa_tier; enriched-prompt introspection; descriptions-carry-no-AT2-vocab; schema pins the closed enum). **Step 4 (#476, test `d06d420`):** the OQ-C 26-narrative labelled fixture set + offline validators + a `@live`-gated before/after A/B harness routing both arms through the byte-identical imported guard (no production change); an independent adversarial moat-safety reviewer judged the set trustworthy; the pre-committed pass/fail read embedded in the harness (a docs/plans/ evidence doc was G2-gated → relocated into the test module). **Step 5 (live, AC-7, host-state — Cray go via AskUserQuestion):** the live before/after on MS-S1 `gpt-oss:20b`, N=3, worst reported — **PASS:** Arm A gated AT-1+AT-3 **8→11/11 (perfect, all 3 reps)** vs the ~7/11 PLAN-0040 reference; Arm B **11/11 abstain every rep** (zero AT-2 regression); **Arm-B guard paths = {label_abstain: 33}** (step_disagreement = 0 — the model labels AT-2 out-of-scope ITSELF, the deterministic backstop never needed to fire = no silent label→backstop shift); AT-1b 11/12 (reported, not gated). Live = **confirming evidence; the offline gate is the binding bar** (OQ-D). Raw log gitignored at `.claude/benchmark-results/plan0041-step5-live-ab.log`; thin tracked summary at `docs/logs/2026-06-29-plan0041-step5-live-ab.md` (two-artifact model). Gate (every step, offline): ruff + ruff-format + `mypy --strict services/` clean, **pytest 1891 passed / 25 skipped** (1877 baseline + 7 Steps-1-3 + 7 Step-4 validators; live test skipped offline). PLAN `git mv` → `done/`. `loop-dispatcher` stays DISABLED | `de36c2b` (#475/#476) / `services/engine/procedures/{archetypes/template,generator/{pipeline,prompts}}.py` + `tests/services/engine/procedures/{test_generator_pipeline,classify_enrichment_fixtures,test_classify_enrichment_fixtures,test_classify_enrichment_live}.py` + `docs/plans/done/0041-classify-prompt-enrichment.md` + `docs/logs/2026-06-29-plan0041-step5-live-ab.md` |

## Rotated this reconcile (session-98, 2026-07-04 — PLAN-0050 ADR-0027 R2 build COMPLETE #553-#563)

### Current-Focus block — Sessions 96/97 CLOSE (head_commit `676fbc2` → `d8f9ec5`) — PLAN-0048/0049 COMPLETE + ADR-0027 Accepted [rotated 2026-07-04, session-98 reconcile; R1 64 KB ceiling]

> **Sessions 96/97 CLOSE, 2026-07-04 (head_commit `676fbc2` →
> `d8f9ec5`) — s96/97 GOVERNANCE + ONTOLOGY ARC COMPLETE: PLAN-0048 Q4
> generic query executor COMPLETE + CLOSED, PLAN-0049 v1 ontology bundle
> executable set {1,2,4,5} COMPLETE + CLOSED (R2 carved out), ADR-0027
> semantic-enrichment fields ACCEPTED. Suite 2097 → 2142 passed / 5
> skipped (+45 across both plans); every feature PR green under the
> PLAN-0047 Step-7 CI gate (ruff + ruff-format + `mypy --strict` + full
> suite w/ postgres + `alembic upgrade head`; #548 added an `alembic
> check` drift-guard step).** **PLAN-0048 Q4 executor (Steps 1–3 already
> reconciled in #540):** Step 4 seams/docs #539 (`f7d4972`, merge
> `ab394b0`) — 3-tool seam docs + future-loop contract + SD-3 seed
> annotation; **COMPLETE fold + `git mv` → done/ #541** (`73a6f9c`, merge
> `0215b3a`) → `docs/plans/done/0048-q4-generic-query-executor.md`. Net:
> the read side gains **declared==dispatched** via `QueryStepExecutor`.
> **PLAN-0049 v1 ontology bundle (executable set {1,2,4,5}):** draft #542
> (`6626d97`, merge `37d865f`, SD-1..7 surfaced) → Cray ratified SD-1..7
> as-recommended, flip Draft→Ready + carve out R2 #543 (`c8b48be`, merge
> `b6330e2`). **Step 1 energy-v1 #544** (`69d7759`, merge `9b2fffb`) —
> asset_type += feeder/cap_bank/gas_engine; NEW `rated_current_a` col
> (SD-6); measured_kind += current/voltage; alembic 0009; regen
> `energy/models.py`. **version = content-revision #545** (`aec644d`,
> merge `154e37e`, SD-2 Cray-confirmed) — `ontology_schema.json` `version`
> const 0 → `{integer, minimum 0}` (real finding: the field was the
> GRAMMAR version, repurposed as content-revision); energy→1,
> supply_chain→1. **Step 2 supply-chain-v1 #546** (`37387ed`, merge
> `fd8acd6`) — NEW Equipment entity + `shipment_uses_equipment` link +
> `adjust_setpoint`; measured_kind [temperature, battery]; enum gaps
> returned/release/return; NO committed ORM / no migration (SD-3
> gitignored fallback; SD-4 parity gap documented). **Step 4 R1
> context-pack emitter #547** (`b80dcff`, merge `0d97ae9`) —
> `code_generator.py::emit_context_pack` → gitignored `context_pack.md`
> (7th emitter); closed-set refuse-not-guess; R2 DEGRADE PATH reads
> ADR-0027 fields when present, omits when absent; 32K token-budget
> tripwire. **Step 5 alembic autogenerate #548** (`1a689ef`, merge
> `518d7da`) — `env.py compare_type=True`; CI `alembic check` drift-guard;
> `docs/runbooks/ontology-migration-autogenerate.md`. **COMPLETE fold +
> `git mv` → done/ #550** (`579c5d1`, merge `d7041f4`) →
> `docs/plans/done/0049-v1-ontology-bundle.md`; R2/Step-3 carved out to
> ADR-0027. **ADR-0027 (the R2 grammar amendment) ACCEPTED:** Proposed
> #549 (`a7bd595`, merge `e61c287`) — ADR-008 D2/D3 grammar amendment
> adding 4 OPTIONAL constructs (synonyms th+en · sample_values ·
> verified_queries · metric grain/join-path), mirrors ADR-0021,
> backward-compat HARD INVARIANT, governed≠generated, decides grammar +
> defers build; **Accepted #551** (`d8f9ec5`, merge `9f95942`) — Cray
> ratified ALL SD-1..7 as-recommended (none overridden); **SD-6 follow-up
> build PLAN named PLAN-0050** (amends L1 `ontology_schema.json` +
> `ontology_meta.py` optional attrs on PropertyMeta/ObjectTypeMeta
> [mirroring QuantityBinding] + L2 validators + backfills
> energy-v1/supply-chain-v1; the shipped R1 emitter consumes it for free
> via the degrade path). **#537 fixture-hermeticity fix** (`2c627bb`,
> merge `3b8cfa3`, test-only) isolated `CLAUDE_GOAL_PATH` in the
> in-process Stop-flow fixture (`inproc_env`), closing the #535/#536
> concurrent-pytest disclosures (root cause = an unhermetic fixture, not
> concurrency; same class as #340). **Standing:** `loop-dispatcher` stays
> **DISABLED**; MS-S1 cold (the whole arc offline); AI-assisted (Claude
> Code, sessions 96 + 97), no `Co-Authored-By` per CLAUDE.md §7.

### Recent-Decisions row — 2026-06-30 (A1 run-time moat enforcement / ADR-0026 Accepted, session 88) [rotated 2026-07-04, session-98 reconcile]

| 2026-06-30 | **A1 (run-time moat enforcement — Cray's #1 rock) LANDED (session 88): ADR-0026 Accepted #479 + A1a COMPLETE #481/#482 + A1b planned PLAN-0044 #484** — builds the principal-identity capability the AT-2 layer's run-time SoD was deferred on (the s85/s86 AC-13-ALT carry). **ADR-0026 Accepted (#479, `620d799`):** principal-identity + AT-2 run-time enforcement; all **6 OQs Cray-adjudicated as-recommended**. **PLAN-0043 (A1a) drafted + SD-1/SD-2 folded (#480, `05243eb`/`af0d882`):** Cray adjudicated **SD-1 = `required_roles` on `SoDConstraint`** + **SD-2 = a `PrincipalAlias` link object** (deviating from the drafted rec). **A1a COMPLETE end-to-end:** **Steps 1-3 (#481, `f1e7afa`)** = the `Person` / `PrincipalAlias` construct + `SoDConstraint.required_roles` + H-governance (new fields are governance, never on a draft type); **Steps 4-6 (#482, `f5c6342`)** = `services/engine/procedures/principal_sod.py`, the **fail-closed principal-SoD run-check** emitting a **STRUCTURED `PrincipalSoDVerdict`** + the `RunContext.principal` / `resolve_gated_step(principal=…)` seam + the offline oracle. **Gate: offline green — the full procedures suite 344 passed.** **A1a/A1b boundary (Cray s88):** the live invocation needs per-step principal RECORDING = the A1b executors' job; A1a ships construct + run-check + seam, A1b wires live enforcement. **A1b drafted = PLAN-0044 (in-flight, #484):** live run enforcement + per-kind executors (`doa_tier`/`rule_gate`/`scored_rule`) + audit-to-control (OQ-5); **3 SDs surfaced for Cray.** **Hero-demo dependency (parallel session):** A1's structured `PrincipalSoDVerdict` + the A1b OQ-5 audit field feed the hero-demo's read-only "governance moment" render (convergence ask #1 MET, #2 lands with A1b). In-flight PRs awaiting Cray merge: **#483** (PLAN-0043 → `done/`) + **#484** (PLAN-0044). `loop-dispatcher` stays DISABLED; MS-S1 cold (A1a offline) | `620d799` (#479) / `f1e7afa` (#481) / `f5c6342` (#482) / `docs/adr/0026-principal-identity-run-enforcement.md` + `docs/plans/done/0043-a1a-principal-identity-sod-runcheck.md` + `services/engine/procedures/principal_sod.py` |

### Current-Focus block — Session 98 (PLAN-0050 ADR-0027 R2 build) [rotated 2026-07-05, session-99 reconcile]

> **Session 98, 2026-07-04 (head_commit `d8f9ec5` → `81cd3ff`) —
> PLAN-0050 (ADR-0027 R2 build) DRAFTED → RATIFIED → BUILT COMPLETE (8
> steps / 8 ACs) → CLOSED (#553–#563).** Renders the Accepted ADR-0027
> grammar amendment into code: the four OPTIONAL semantic-enrichment
> ontology constructs — `synonyms` (th/en) · `sample_values` ·
> `verified_queries` · metric `grain`/`join_path` — now flow L1 grammar →
> Pydantic projection → L2 consistency → both v1 verticals → the LLM-facing
> context pack. **Draft #553** (`db8c889`, SD-A..D surfaced) → **Ratify
> #554** (`e9c4e07`) flip Draft→Ready — Cray ratified SD-A..D as-rec (SD-A
> one-PR-per-vertical · SD-B verified_queries object-type-level · SD-C
> samples ⊆ enum · SD-D typed `Synonyms` model). **Step 1 L1 schema #555**
> (`e430d5f`, AC-1) — the 4 optional constructs added to
> `ontology_schema.json`, mirroring `quantityBinding`. **Step 2 projection
> #556** (`3ee691a`, AC-2) — typed `Synonyms`/`VerifiedQuery` models +
> optional attrs on `PropertyMeta`/`ObjectTypeMeta`/`QuantityBinding`
> (`default_factory`). **Step 3 L2 consistency #557** (`6b7cc74`, AC-3) —
> the `_check_enrichment` orchestrator (`_check_synonyms` /
> `_check_sample_values` [SD-C samples ⊆ enum] / `_check_verified_queries`
> / `_check_quantity_binding_paths` [SD-5 join_path resolution]); no-op
> when the fields are absent (D2). **Step 4 D2 backward-compat GATE #558**
> (`f0191b1`, AC-4) — the zero-backfill proof: `generate` byte-identical +
> git-clean with no enrichment present. **Step 5 energy-v1 backfill #559**
> (`1254b2d`, AC-5) — curated th/en synonyms + sample_values (enum-overlap
> + non-enum) + verified_queries + grain + join_path on the energy
> ontology. **Step 6 supply-chain-v1 backfill #560** (`2e2150c`, AC-6) —
> same, cold-chain vertical; completes the v1-batch backfill (ADR-0027
> D5). **ADR-0027 erratum #561** (`c23a7da`) — the Step-7 FINDING: the
> shipped R1 emitter did NOT read the enrichment fields (only a hardcoded
> "not yet populated" degrade note); ADR-0027's "zero emitter change / for
> free" forward-reference was factually WRONG. Corrected in-place; DESIGN
> (D1-D4, SD-1..7) unchanged, Status stayed Accepted. **Step 7 emitter fix
> #562** (`33a2429`, AC-7) — the 3 context-pack helpers now RENDER the
> enrichment (synonyms `aka`, `sample values`, `Verified queries`, `@grain
> via join_path`) + the degrade note is now CONDITIONAL. **DISCLOSED
> DEVIATION:** AC-7 was met via a **Cray-authorized emitter change**
> (erratum #561 → #562), NOT "for free" — the IN-1 escape hatch firing as
> designed (gap surfaced, not silently patched). **COMPLETE fold + `git
> mv` → done/ #563** (`81cd3ff`, merge `81090de`) →
> `docs/plans/done/0050-ontology-semantic-enrichment-build.md`; Status →
> Complete, 8 ACs ticked, completion note carries the deviation
> disclosure. **Outcome:** R2's moat value (th/en synonyms + closed sample
> sets + verified queries + metric grain) now reaches the LLM context
> pack — both real vertical packs populate (Thai synonyms present; the
> degrade note is gone). **Gate (AC-8 / CI):** every step's PR ran green
> under the PLAN-0047 Step-7 CI gate (ruff + ruff-format + `mypy --strict`
> + full suite w/ postgres + `alembic upgrade head` + `alembic check`);
> **no Alembic migration the whole arc** (the four constructs are
> ontology-metadata, both verticals). **Tests:** ~+15 across the arc
> (Step1 +5 validator, Step2 +2 meta, Step3 +4 validator, Step4 +2
> validator, Step7 +2 emitter; baseline 2142 → ~2157, **CI-green per PR**
> — the full suite was NOT re-run locally this reconcile; CI is the gate).
> **Standing:** `loop-dispatcher` stays **DISABLED**; MS-S1 cold (the whole
> arc offline); AI-assisted (Claude Code, session 98), no `Co-Authored-By`
> per CLAUDE.md §7.

### Recent-Decisions row — 2026-06-30 (A1b Step 1 principal-SoD run enforcement, session 89) [rotated 2026-07-05, session-99 reconcile]

| 2026-06-30 | **A1b STEP 1 (demo-critical LIVE fail-closed principal-SoD run enforcement) SHIPPED + MERGED (#486) + independently verified (J1/J2 PASS) (session 89)** — INTERIM (1 of A1b's 6 steps; A1b NOT complete). Makes the A1a pure `check_principal_sod` fire on a REAL suspended-gate resolution. `spec.parse_procedures` now reads `principals`/`principal_aliases` (were silently dropped); procurement ships **5 authored principals + `required_roles`** (AC-10); a **`step_principals` JSONB column on `PipelineRun` (+ Alembic `0004`)**; `orchestrator.run_procedure(principal=…)` records the requester per SoD step (**SD-2=(a)**); `action_step.resolve_gated_step` invokes the check **unconditionally**, fails **CLOSED** (raises `PrincipalSoDError` with the structured verdict) **BEFORE** any approve/execute, **non-skippable**. **Inert for non-SoD procedures** (only procurement carries SoD; aquaculture inert-reconcile proves no behavior change). **Gate (offline = binding bar):** ruff + mypy clean; **1921 offline + 27 DB tests green** incl. **8 NEW live-SoD DB tests** + `alembic upgrade head` (0004) + aquaculture inert-reconcile. **Axis-B goal-gate: J1 PASS + J2 PASS** (high, independent goal-evaluator, creator≠critic intact). **Demo-convergence:** 1 of 3 demo-critical pieces of the hero-demo "governed→run→฿" path; **A1b Steps 3 (`doa_tier` executor) + 6 (`governed_decision` audit-to-control) next** = the rest of that path (offline-pure); Steps 2/4/5 (`OQ-6`·`rule_gate`·`scored_rule`) after; hero-demo session converges once the path is in. **Owed at A1b CLOSE (not per-step):** PLAN-0044 SD-1/SD-2/SD-3-as-rec disposition + a PLAN-0044 Completion note + a STATUS full-body reconcile. `loop-dispatcher` stays DISABLED; MS-S1 cold (A1b offline) | `719ea78` (#486) / `services/engine/procedures/{spec,orchestrator,action_step}.py` + `services/db/models.py` + `services/db/migrations/versions/0004_*.py` + `verticals/procurement/procedures.yaml` |

## Rotated this reconcile (session-100, 2026-07-05 — Wave-3 Cowork content-authoring COMPLETE #572)

### Current-Focus block — Session 99 (head_commit `81cd3ff` → `57a6593`) — PLAN-0051 reason-then-structure A/B COMPLETE [rotated 2026-07-05, session-100 reconcile; R1 64 KB ceiling]

> **Session 99, 2026-07-05 (head_commit `81cd3ff` → `57a6593`) —
> PLAN-0051 (reason-then-structure A/B — Wave-2(c)) DRAFTED → RATIFIED →
> BUILT (6 steps) → LIVE-RUN → COMPLETE + CLOSED (#565–#570).**
> Operationalizes the July-2026 research finding #2 (reason-then-structure
> lifts constrained-decoding accuracy 10-30%) as a **3-arm A/B**
> (`baseline` / `field_order_flip` / `two_pass`) on vero-lite's two
> remaining single-pass structured-output call sites — **classify**
> (`classify_narrative`) + **nl_query** (`_translate`); the anomaly
> recommender was OUT of scope (already two-pass Pattern B). **Draft #565**
> (`db8c889`→`8abdd33`/`bd8e2dc`, plan-drafter) → Cray ratified SD-1..SD-6
> **as-recommended** → Draft→Ready. **Build (6 steps; each offline gate MET,
> both shipped defaults byte-identical, the guard/validator/Phase-B seam
> untouched):** classify `arm` plumbing + the offline A/B driver
> `classify_ab_route` reusing PLAN-0041's 26-narrative corpus (**#566**
> `1e6a121` AC-1 · **#567** `426ebaa` AC-2); nl_query gold corpus (27
> hand-authored energy-ontology questions, all pass `_validate_query`) +
> `score_query` on the RAW `_translate` output (SD-1) + `arm` plumbing with
> the leading advisory `reasoning` field stripped before execute (**#568**
> `b6619fd` AC-3 · **#569** `74760bd` AC-4). Each arm = `baseline` /
> `field_order_flip` (reasoning-first schema) / `two_pass` (free-form
> reasoning call before the constrained call, omits `think` — CHECKPOINT-0). **Step 5a harness + 5b results + Step 6 close #570**
> (`b8ab793` harness skip-by-default → `57a6593` results + `git mv` →
> done/). **Live run (Step 5b — host-state §8, Cray go, full N=3 both
> sites, 2:17:02 on `gpt-oss:20b`):** `2 passed`. **RESULT: NO measurable
> lift on either site.** classify (AC-6): baseline at the **11/11 ceiling**;
> field_order_flip +0, two_pass −1; the **Arm-B moat brake held 11/11 in
> EVERY arm/rep** (the reasoning-order lever did not weaken the AT-2 abstain
> gate; no false-accepts). nl_query (AC-7): worst-rep mean baseline 0.978
> vs variants 0.965–0.978; hard-class 0.844 all arms (Δ +0.000).
> **Recommendation (SD-6): REJECT both `field_order_flip` + `two_pass` on
> both sites — keep the shipped `baseline`; NO production default changed;
> NO new ADR (SD-5).** The arm plumbing + 2 corpora + the A/B harness remain
> behind the `baseline`-default `arm` param as reusable scaffolding. The
> research "10-30% lift" **did not replicate** (both paths already strongly
> prompted; `gpt-oss:20b` extracts structured output well) — a **valid null
> result** (measured, not assumed). **Gate:** offline AC-1..AC-5 (the binding
> bar) MET; AC-6/AC-7 (live) = confirming. Full record:
> `docs/logs/2026-07-05-plan0051-live-ab-results.md`.
> **Standing:** `loop-dispatcher` stayed **DISABLED**; MS-S1 warmed once for
> the Cray-gated run then idle; AI-assisted (Claude Code, session 99), no
> `Co-Authored-By` per CLAUDE.md §7.

### Recent-Decisions row — 2026-06-30 (A1b Steps 3+6 demo-critical path complete, session 89) [rotated 2026-07-05, session-100 reconcile]

| 2026-06-30 | **A1b STEPS 3 + 6 (the rest of the demo-critical path) SHIPPED + MERGED (#488 `doa_tier` / #489 `governed_decision`) + independently verified (J1/J2 PASS) → the DEMO-CRITICAL PATH IS COMPLETE ON MAIN (session 89)** — MILESTONE, not closure: **A1b is NOT complete** (AC-9 + Steps 2/4/5 remain). With **Step 1 (#486, the live SoD gate)**, the hero render now has all three structured fields it joins on. **Step 3 (#488, `34be3a5`, AC-5):** a deterministic `doa_tier` per-kind executor — `resolve_doa_tier` over the `DoaLadder` half-open band (`Decimal` spend → tier), resolves the tier's `approver_role` → a `Person`, **fails CLOSED on a currency mismatch (OQ-4)**; the **SD-1=(a) `GovernanceActionExecutor` wrapper** dispatches on `governance_content.kind` **without a new `StepKind`**. **Step 6 (#489, `f5527d9`, AC-8):** the typed minimal **`governed_decision` audit-to-control field (SD-3=(a))** — `ControlRef{kind,id}` + `GovernedDecision{control_ref, principal_id}` on `AuditMetadata`, emitted as an **ENGINE side-effect** by the `doa_tier` route (`{kind:'doa_tier', id:resolved_tier_id}`) and the SoD gate (`{kind:'sod', id:sorted distinct_steps}`); **join-stable keys** (the `Person` PK + the verdict-emitted control id). **Gate (offline = binding bar):** both ruff + mypy clean — Step 3: **19 new `doa_tier` tests, full suite 1968 passed**; Step 6: **5 new `governed_decision` tests + the SoD-gate DB emission** (real hero gate emits `{kind:'sod', id:'approve+intake', principal_id:'appr-director'}`), **full suite 1973 passed / 5 skipped**. **Axis-B goal-gate: J1 PASS + J2 PASS** (independent goal-evaluator, creator≠critic intact, both steps). **AC-9 DEFERRAL (surfaced for Cray, NOT silently applied):** the procurement `audit` step is authored `autonomy: auto` AND downstream of the `approve`/`issue_po` gates, so the AC-9 auto-downstream-of-a-gate assertion would **restructure the hero procedure** — a Cray decision (restructure the audit terminal vs exempt no-op terminals), held for adjudication. **NEXT:** signal the hero-demo session to converge (the `services/engine/procedures/*` hold releases — it can build the read-only governance-moment render); then A1b's remaining non-demo-critical work = AC-9 (the Cray pick) + Steps 2/4/5 (`OQ-6` N≥2 marker · `rule_gate` · `scored_rule`). **Owed at A1b CLOSE (not per-step):** PLAN-0044 Completion note + `git mv` → `done/` + a STATUS full-body reconcile. `loop-dispatcher` stays DISABLED; MS-S1 cold (A1b offline) | `34be3a5` (#488) / `f5527d9` (#489) / `services/engine/procedures/{action_step,orchestrator}.py` + `services/db/models.py` (`AuditMetadata`/`GovernedDecision`/`ControlRef`) + `verticals/procurement/procedures.yaml` |

### Current-Focus block — Session 100 (Wave-3 Cowork content-authoring) [rotated 2026-07-05, session-101 Wave-4 reconcile]

> **Session 100, 2026-07-05 (head_commit `57a6593` → `05c12c2`) —
> Wave-3 (Cowork content-authoring track, from the session-95 5-wave
> backlog re-order) COMPLETE.** Two Tier-0 deliverables, Cowork-drafted
> (ADR-009 D1) → Code R2 + committed (ADR-009 D2); **no new ADR/PLAN** (no
> architectural decision). **(1) partner-intake-form v2→v3** (PR #572,
> `5ca1c18`) — 11 `[v3]` additions surfaced by the two partner-sim mapping
> rehearsals, folded into the sections they extend (B:1, C:3, F:1, G:1, H:5
> = 11 = 7 run-1 §5 items 1–7 + 4 run-2 §6 items 8–11), each carrying a `Vn`
> ID traceable 1:1 to its rehearsal item. No v2 content removed; questions
> 1–17 unchanged. A `docs/conventions/` edit — **NOT** G1/G2-gated.
> **(2) Wave-3 GTM ammo pack** — 4 new evidence pieces (residency "compute
> never leaves" · Thai AI Act assistive-only keeps us out of the
> high-risk-AI registration bucket · Gartner "60% of agentic analytics
> projects relying solely on MCP will fail by 2028" · refusal-safety
> "governed refusal vs. confident wrong answer", grounded on the shipped
> `_validate_query` seam) layered onto the box4 ROI-spine + b3 moat
> narrative. A **gitignored confidential strategy note**
> (`docs/strategy/private/`) — **NOT committed** (same convention as
> box4/b3). **Code R2:** verified the 11-count + no-question-loss vs the v2
> diff; verified ammo-(d)'s `_validate_query` seam
> (`services/engine/nl_query.py:428`/`:534`) exists; corrected one
> provenance citation typo (V2 cited run-1 §5 #1 → #2). The Stop-hook
> classifier misrouted the dispatch to an ADR draft; Code overrode it
> (content authoring, not governance).
> **Standing:** `loop-dispatcher` stayed **DISABLED**; MS-S1 cold (offline);
> AI-assisted (Claude Code, session 100), no `Co-Authored-By` per §7.

### Recent-Decisions row — 2026-07-01 (HERO-DEMO PHASE 1 offline foundation, session 91) [rotated 2026-07-05, session-101 Wave-4 reconcile]

| 2026-07-01 | **HERO-DEMO PHASE 1 (offline foundation) SHIPPED + MERGED (#492 session-90 reconcile / #493 Phase-1 foundation) (session 91)** — MILESTONE, not closure: the SD-1 live layer (C-full) is still WIP on `feat/hero-demo-v1-live` and **A1b is NOT complete** (AC-9 + PLAN-0044 Steps 2/4/5 remain). **#493 = four PLAN-0045 commits:** **Step 1 (`85eafaa`)** C1 `FastenalCsvAdapter` (CSV-backed hero-demo `DataAdapter`, `verticals/` only, **zero `services/` core edit**); **Step 1b (`6fb7b2b`)** the governance-moment audit capture (`resolve_doa_tier` + `check_principal_sod` from the **real engine**); **Step 3 (`b76c080`, B1)** the ฿-impact ledger + the `/demo/hero/{governance,impact}` **derived API views** behind **4 demo guards**; **Step 2 (`f310778`)** the governance-moment render screen `view-hero.js` (render tab **G**). **Verification (attributed to the session-90 handoff evidence, NOT re-run this reconcile — CLAUDE.md §6):** offline gate green (~2005 tests) + verified live on the `oct-demo` preview (all 4 cards, both `governed_decision` joins JOIN, contrast case = MANAGER, ฿-ledger ฿9.76M → ฿1.65M). **§3 ฿-threading finding:** the shipped `source` `ActionStepExecutor` returns action envelopes + **drops the input entity's amount** → the `approve` `doa_tier` fails CLOSED at approve. **NEXT (Phase 2):** PLAN-0044 A1b Step 5 (`GovernanceActionExecutor._scored_rule`) on `feat/a1b-scored-rule` — deterministic quote scoring (LLM summarises only), select winner, emit amount+currency so `approve` resolves; offline gate = AC-7 + a full-loop stub-client test threading ฿288,000 → CONTROLLER; then merge → rebase `feat/hero-demo-v1-live` → C-3 runner → C-4 endpoint/toggle → C-5 live MS-S1 smoke (host-state, Cray go). **Owed at A1b CLOSE (not per-step):** PLAN-0044 Completion note + `git mv` → `done/` + a STATUS full-body reconcile. `loop-dispatcher` stays DISABLED; MS-S1 cold (offline) | `788994d` (#493) / `85eafaa`·`6fb7b2b`·`b76c080`·`f310778` / `verticals/procurement/data_adapter/fastenal_csv.py` + `verticals/procurement/hero_demo/{governance_audit,ledger}.py` + `services/api/{models,routers}/demo.py` (`/demo/hero/{governance,impact}`) + `services/api/static/assets/view-hero.js` |

### Current-Focus block — Session 101 Wave-4 (ADR-016 Phase-3 OCT Monitor) [rotated 2026-07-06, session-102 S2-track reconcile]

> **Session 101, 2026-07-05 (head_commit `05c12c2` → `b4d312c`) —
> Wave-4 (ADR-016 D7 Phase-3 "OCT Monitor", parallel track, Cray-directed).**
> A PLAN → panel-advised → BUILT → amendment arc, `plan-drafter`-authored,
> Code R2-verified + committed (ADR-009 D1/D2). **(1) PLAN-0052 Draft→Ready
> (#574/#575).** `plan-drafter` authored PLAN-0052 (ADR-016 Phase-3 OCT
> monitor, v1 read-only) — #574 (`ab4c8f9`, merge `b89c4dc`); a **4-lens
> specialist+stakeholder panel** (read-only `explore-research`: S1
> scheduler/SRE · S2 security-IAM/PDPA-DPO · S3 SRE/ops-mgr · S4
> frontend-UX/operator) advised, Code R2-verified every load-bearing on-disk
> claim, the drafter folded the enrichments, Cray ratified S1–S5 as-rec →
> Draft→Ready #575 (`2cae236`, merge `7c3cee0`). No direction reversed; the
> one v1 build-touch (read-only) = widening the list projection with
> `trigger`/step-progress + `data-testid`s.
> **(2) v1 read-only Monitor BUILT — #577** (`febdf7e`, merge `38c277b`).
> Backend `GET /runs` (newest-first list + a `waiting_human` "waiting on you"
> count + step-progress) + `GET /runs/{run_id}` (ordered steps + per-step
> trace/audit/duration + the `waiting_human` gate & proposals exposed
> READ-ONLY) in `services/api/{models,routers}/runs.py` — **reuses
> `load_run`, no new query layer, no mutation.** Front-end **View H
> "Monitor"** (`static/assets/view-monitor.js` + `app.js` VIEWS.H +
> index.html): list + live detail (poll 3s/10s, stop-terminal, pause-hidden),
> gate panel behind a `mode:'read'|'operate'` seam (**inert v1** → the
> Control leg wires the already-shipped `POST /runs/{id}/gate/resolve`, an
> L4 extension-not-rewrite), amber high-salience `waiting_human` badge,
> stable data-testids. **Verified:** new pytest 4 passed + **full suite 2211
> passed / 7 skipped**; ruff + mypy clean; **AC-8 frozen surfaces (spec.py /
> ADR-007 envelope / ontology) UNTOUCHED**; browser-verified end-to-end via
> preview (list → detail → gate proposals read-only; no console/server
> errors).
> **(3) ADR-016 D2+D3 amendment PROPOSED — #576** (`8570c1c`, merge
> `b4d312c`): a typed **service-principal for non-human (`schedule`)
> triggers** (Surfaced-Decision S2). Direction LOCKED — a service-principal
> is a **requester/actor ONLY, NEVER an approver** (SP-1); SP-2..8 + RF-1..3
> (never-null actor, `actor_kind` human|service, on-behalf-of chain,
> least-privilege via existing allowlists, H-governed; **RF-1** = gate-resolve
> rejects a service/None principal for a `gated` step regardless of the
> authn toggle). **Proposed — awaiting Cray ratification** of SP-1..8 + OQ-1
> (identity placement, rec Agent-bound) / OQ-2 (`RunContext.principal`
> union-vs-separate, rec separate) / OQ-3 (`actor_kind` home, rec
> audit-only). **S2-before-S1** (a scheduled run has no human actor → PDPA
> gap).
> **Standing:** `loop-dispatcher` stayed **DISABLED**; MS-S1 not exercised by
> Wave-4 (the monitor is DB-only/offline); AI-assisted (Claude Code, session
> 101), no `Co-Authored-By` per §7.

> _Rotation note (session-101 Wave-4 reconcile, 2026-07-05): to hold STATUS
> under the **R1 64 KB hard ceiling** as the Session-101 Wave-4 CF block
> landed (R1 overrides the R2 4-session window — the s95–s100 precedents
> accepted a narrowed 1-block window), the **Session 100 Wave-3 (Cowork
> content-authoring track) COMPLETE — partner-intake-form v2→v3 (#572) +
> Wave-3 GTM ammo pack** Current Focus block was rotated verbatim to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md)
> (it is covered by the top Recent-Decisions row; the intake-form edit lives
> in `docs/conventions/` + the ammo pack in gitignored
> `docs/strategy/private/`). Resulting Current-Focus window = {Session 101
> `b4d312c`}; RD table = 10 rows (at the R2 cap; the 2026-07-04 PLAN-0048
> Q4 + PLAN-0049 v1 + ADR-0027 row rotated out to the same archive). Per the
> STATUS.md Rotation Policy (R1/R2/R4)._

### Recent-Decisions row — 2026-07-01 (HERO-DEMO v1 governed-run-baht path COMPLETE) [rotated 2026-07-06, session-102 S2-track reconcile]

| 2026-07-01 | **HERO-DEMO v1 "governed → run → ฿" path COMPLETE — offline + LIVE-verified (session 91)** — three PRs merged (#495/#496/#497) + a Cray-approved C-5 live MS-S1 smoke; MILESTONE (the demo path is done) NOT closure — **A1b is NOT complete** (PLAN-0044 Steps 2/4 + AC-9 remain). **#495 (`2ebe851`, A1b Step 5) `scored_rule` executor:** `GovernanceActionExecutor._scored_rule` (SD-1=(a), mirrors `_doa_tier`) scores an emergency-sourcing step's candidate quotes by the typed `ScoredRule`, selects the winner **DETERMINISTICALLY** (same inputs→same pick; LLM never selects) and — unlike `_doa_tier` — **REPLACES the output with the selected entity carrying `amount` (unit_price × qty) + currency**, closing the **§3 ฿-threading finding** (the shipped `ActionStepExecutor` dropped the entity's spend so `approve` `doa_tier` had no amount); scoring = criticality-as-event-weight amplifier (v1 weights provisional, ADR-0025 D2); **17 new tests.** **#496 (`52523df`) the live-run layer:** C-1 (`bfc4844`) Fastenal dataset (`operational_event.csv`+`quotation.csv`+adapter types); C-2 (`75e7e69`) the in-code Fastenal hero procedure (ladder-swap → **฿288k → CONTROLLER**); C-3 (`00b9a3c`) `hero_demo/run.py` `run_hero_governance_moment` drives the **REAL** loop (intake→judge→source→compliance→approve) through the orchestrator + AT-2 executors — the moment is **DERIVED by the run** (same audit contract, `source: "live-run"`); **3 new stub-client tests.** **#497 (`b4c03a9`) C-4 live toggle:** `GET /demo/hero/governance?live=true` returns the live-run audit; `view-hero.js` gains a "Run live"/"Offline fixture" toggle + source-aware badge; **HOST-STATE-FREE** (the `?live` path uses a deterministic advisory-LLM stub `advisory_stub_factory` — the governed decision is LLM-independent, no MS-S1 hit per request); preview-verified, **+1 endpoint test.** **C-5 live MS-S1 smoke (this session, Cray-approved via AskUserQuestion, HOST-STATE EVIDENCE):** warmed `gpt-oss:20b` on MS-S1 (192.168.1.133, verified present) + ran `run_hero_governance_moment` **ONCE** with the real `OllamaClient` — **result (fresh on-disk this session, a live run NOT re-derived): governed outcome IDENTICAL to the offline gate** (`SUP-RAPIDMRO → ฿288,000 → CONTROLLER (appr-controller)`, `sod.governed: true`, `scored_path: exception_policy`, `governed_decision: [doa_tier, sod]`) → **governed ≠ generated confirmed LIVE** (the real LLM = advisory prose only, does not change the governed decision). Live = **EVIDENCE** (the offline oracle stays the gate, §8); **no code shipped for C-5.** **NEXT (close-out):** A1b's remaining non-demo-critical work = Steps 2 (`OQ-6` N≥2) + 4 (`rule_gate`) + AC-9; verify PLAN-0045 AC then `git mv` → `done/`. **Owed at A1b CLOSE (not per-step):** PLAN-0044 Completion note + a STATUS full-body reconcile. `loop-dispatcher` stays DISABLED; MS-S1 cold (remaining A1b offline) | `b4c03a9` (#497) / `2ebe851` (#495) / `52523df`·`00b9a3c`·`75e7e69`·`bfc4844` (#496) / `services/engine/procedures/{scored_rule,governance_step}.py` (`select_scored_supplier` + the `_scored_rule` branch) + `verticals/procurement/hero_demo/run.py` (`run_hero_governance_moment`) + `verticals/procurement/data/hero/{operational_event,quotation}.csv` + `services/api/routers/demo.py` (`/demo/hero/governance?live=true`) + `services/api/static/assets/view-hero.js` |


<!-- rotated 2026-07-06 (session 104) from docs/STATUS.md during the ADR-016 S2 Phase B reconcile (Current Focus window + RD 10-row cap) -->

### Rotated Current-Focus blocks (2026-07-06, s104)

> **Closeout (2026-07-06, #590, head_commit `488ed25` → `4548ed8`):**
> PLAN-0054 archived to `docs/plans/done/` (Status → Complete + a COMPLETION
> note: PR map #584–#589, AC-1…AC-10 MET, v2 sequels listed). Control-leg v1
> arc fully closed; no active PLAN. Next = Cray-directed (candidates below).

> **Session 103, 2026-07-06 (head_commit `b68beee` → `488ed25`) —
> Control-leg v1 COMPLETE (PLAN-0054) + CSP follow-up.** The OCT Monitor
> (View H) flips watch-only → **watch + OPERATE**: a named, authenticated
> human approves/rejects a `waiting_human` procedure gate and cancels a
> parked run FROM the UI, with SoD + a tamper-evident audit actor enforced
> server-side (ADR-016 S2 RF-1 / PLAN-0053). **Code-built directly** (a
> Ready PLAN-0054 — the PLAN was `plan-drafter`-authored in s102),
> committed via PR (ADR-009 D2). **Five merged PRs (newest first):**
> **#587** (`036fffe`+`ba0a0ae`+`03588ea`+`7b41567`, merge `488ed25`) —
> **Steps 2–5 + 7: the operate UI.** NEW `assets/auth.js` (SD-A) = the
> single frontend credential seam (login/authHeader/logout; pilot API key
> in sessionStorage; Bearer on operate POSTs only; optimistic login — the
> display identity is cosmetic, the real approver is the key's
> server-resolved `person_id`). `view-monitor.js` = approve/reject per
> proposal (submit gated until all decided), auth bar, cancel
> (`waiting_human` only, SD-B), 403 (RF-1/SoD) + 409 (stale
> reload-and-retry) inline; + Monitor detail-pane scroll fix, audit-dump
> `[object Object]` fix (kvDump arrays-of-objects), green "approved by
> <person>" badge on resolved gates, `scripts/seed_operate_demo.py`
> (dev-only reseed). **2 spawned specialists (frontend + app-security):
> secure-for-pilot, no real vulns.** Preview-verified E2E (login → approve
> → submit → resume → issue_po gate → approve → completed; cancel; logout;
> 0 console errors). **#586** (`8a6e527`) — Step 6: procurement
> operate-demo provisioning + seed (`seed_operate_waiting_human_run` →
> `emergency_sourcing_round` at the approve gate, `req-planner` SoD
> requester, JSONB-safe Decimal→str; lifespan auto-seed gated on
> `OCT_DEMO_SEED_OPERATE`, idempotent + fail-soft; `.env.example` +
> runbook §3b; DB-backed test). **#585** (`16d218f`) — Step 6b:
> `register_procurement_procedure_executors` wired at startup
> (procurement-gated) — closes the live resolve endpoint 409ing "no
> procedure-executor factory"; reuses the hero `_executors` on the
> deterministic advisory stub (MS-S1-independent). AC-10. **#584**
> (`3a94012`) — Step 1: `POST /runs/{run_id}/cancel` (RF-1 403 guard,
> `waiting_human`-only → 409 SD-B, `run_cancelled` audit naming the human;
> first writer of `PipelineRunStatus.CANCELLED`). **#588** (`f98de81`) —
> CSP defense-in-depth (operate-UI security-review follow-up, parallel
> session): scoped `Content-Security-Policy` on static-file serving
> (`_StaticFilesWithCSP`), NOT the JSON API / /docs; operate UI runs under
> it with **0 CSP violations**. **Suite 2223 passed / 7 skipped** (frontend
> commits Python-neutral); ruff + mypy clean; MS-S1 not exercised.
> **Standing:** Control-leg v1 **COMPLETE** (no active PLAN);
> `loop-dispatcher` **DISABLED**; MS-S1 idle; AI-assisted (Claude Code,
> session 103), no `Co-Authored-By` per §7.

### Rotated Recent-Decisions row (2026-07-06, s104)

| 2026-07-01 | **ADR-016 Q3 READ-SIDE ONTOLOGY OBJECT-BINDING AMENDMENT ACCEPTED (Rock 3 / O-2, #505) (session 93)** — an in-place ADR-016 D2+D3 amendment closing the read-side governance gap that mirrors the shipped write-side. Two commits: `915c344` (Proposed) + `cb7eb05` (fold ratified decisions → Accepted). **Decision (contract-first):** a typed `StepInput.reads: list[str]` read entry point (OQ-5: list not `str` — procurement `intake` reads 3 object types + joins); `Agent.allowed.object_types` mirroring `action_handlers`; **LOAD-time enforcement** (`reads ∈ ontology ∩ allowlist`, else refuse load) — **zero runtime-data-flow change.** **Honest enforcement frame (Cowork caught, Code-verified):** v1 = a typed read contract + a load-time consistency/scoping gate, **NOT** runtime-enforced parity — even write-side `action_handlers` is only pre-flight-checked in `validate_runnable`; teeth = declared==dispatched, gained read-side only at **Q4**. **Deferred:** the generic run-consume query executor → a fast-follow build PLAN (touches runtime flow + enrich/join steps); the Box-4 economic-impact facet → a self-cancelling **N≥3** marker (typed facet only; economic dimension prose-captured at authoring). **OQ-1..6/A ratified:** OQ-1 `StepInput.reads` · OQ-2 load-gate+reframe · OQ-3 `object_types` bounds `fetch_objects` only (links/events out of v1) · OQ-4 `where`=post-fetch · OQ-5 `reads:list[str]` · OQ-A `reads`/`object_types` H-governed (`object_types` auto-covered; add `reads` to `STEP_GOVERNANCE_FIELDS` = build-PLAN task) · OQ-6 `object_types` empty=unconstrained (backward-compat). **Three-lens process:** `plan-drafter` AUTHORED the amendment + folded the ratified decisions; Cowork Tier-1b independent second-perspective review (caught the parity over-claim + surfaced OQ-5); Code R2-verified on disk + committed; Cray ratified OQ-1..6/A. **Context:** the parallel hero compliance-swap (#506, `0b7efe4`) landed last session (swapped the hero-demo compliance stub for the shipped `rule_gate` executor; governed outcome unchanged). **Impl note for the build PLAN:** the load-gate must thread the vertical `OntologyMeta` into pre-flight (`validate_runnable(procedure, agent)` doesn't carry it today). **NEXT = the fast-follow build PLAN** (`StepInput.reads` + `Agent.allowed.object_types` + load-gate + `reads`→`STEP_GOVERNANCE_FIELDS` + tests); the generic query executor (Q4) = a separate later PLAN. **Routing:** the ADR-016 amendment authored by the in-harness `plan-drafter` (prong-2 exempt) → Code R2 + committed via `docs/adr` PR. `loop-dispatcher` stays DISABLED; MS-S1 cold (offline) | `cb7eb05` (#505 fold→Accepted) / `915c344` (#505 Proposed) / `docs/adr/0016-*.md` (D2 `StepInput.reads` + `Agent.allowed.object_types` + D3 load-gate) |


## Rotated this reconcile (session-105, 2026-07-07 — ADR-0028 Accepted [schedule-trigger scheduler S1] + main greened #599/#600)

### Rotated Current-Focus block — Session 104 (ADR-016 S2 Phase B COMPLETE) [rotated 2026-07-07, session-105 reconcile; R1 64 KB ceiling]

> **Session 104, 2026-07-06 (head_commit `4548ed8` → `fe36e36`) —
> ADR-016 S2 Phase B COMPLETE (PLAN-0053): the typed service-principal
> actor model; "S2 before S1" now satisfied.** A scheduled/non-human run
> now has a typed, audit-legible actor and can NEVER approve its own gate.
> `plan-drafter`-authored, Code R2 + committed via PR (ADR-009 D1/D2).
> **Six merged PRs (newest first):** **#597** (`fe36e36`) — PLAN-0053
> `git mv` → `done/` (Phase A s102 + Phase B s104 COMPLETE). **#596**
> (`4f49e29`) — **Phase B audit:** `actor_service_principal_id` column
> (alembic 0010) + `compute_row_hash` **omit-when-None** (SD-2 RATIFIED —
> proven on-disk 7/7 that pre-migration rows recompute byte-identically,
> no epoch boundary) + `verify_chain` passthrough + `actor_kind:"service"`
> + on-behalf-of lineage. AC-9/10/11. **#595** (`4ab67ca`) — **Phase B
> runtime:** the **library-level RF-1 guard** at `resolve_gated_step`
> (AC-1 — a gated resolve with no principal RAISES `GateApproverError`
> independent of `api_auth_enabled`; closes the Phase-A HTTP-only gap so a
> scheduler / direct caller can't bypass) + `RunContext.service_principal`
> threaded through all 3 construction sites (AC-8). Blast radius: 8
> gate-resolve test files updated to name an approver + one incidental
> pre-existing test-isolation fix. **#594** (`bab3c3e`) — **Phase B
> spec:** `ServicePrincipal` type (distinct from Person — no approver
> field / SP-1, no scope primitive / SP-6) + vertical `service_principals`
> registry + `Agent.service_principal_ids` (SD-3) + draft-governance
> disjointness. AC-5/6/7/12. **#593** (`8077242`) — **Phase B
> activation:** Cray ratified SD-2 (omit-when-None, superseding the
> original epoch-boundary rec after a code read) + SD-3 (list on Agent).
> **#592** (`b1fb2e7`) — a `next-work-analyst` skill + a soft
> `UserPromptSubmit` handoff-nudge hook (rank next work + ELI-CRAY; grounds
> candidates vs code). **All ACs 1–13 met; 52 db + 489 procedures tests
> green; ruff + mypy clean; MS-S1 not exercised (deterministic).**
> **Standing:** ADR-016 S2 Phase B **COMPLETE** (no active PLAN);
> `loop-dispatcher` **DISABLED**; MS-S1 idle; AI-assisted (Claude Code,
> session 104), no `Co-Authored-By` per §7.

### Rotated Recent-Decisions rows [rotated 2026-07-07, session-105 reconcile]

| 2026-07-03 | **PLAN-0047 (pre-pilot hardening: authn + run/gate endpoints + write-ahead + audit + config-pin + CI) EXECUTED + COMPLETE + CLOSED (session 95; PRs #522–#531; PLAN → `done/`)** — all 7 steps + all 10 ACs; **+31 tests (suite 2066 → 2097 passed / 5 skipped)**; sales claims (authn / audit / exactly-once / config-pin) now code- and CI-backed. **Step→PR:** draft #522 `b6cb0d5` (plan-drafter authored) · SD-1..4 as-rec #523 `8198548` (SD-1=(a) API keys · SD-2 defer · SD-3 yes-minimal · SD-4 CI w/ DB) · Step 7 CI #524 `0401a0a` (FIRST CI gate on the repo: ruff + ruff-format + `mypy --strict` + full suite w/ postgres container + `alembic upgrade head` per PR) · Step 1 authn #525 `3b3db46` (fail-closed API-key gate on state-changing routes; `action_identity` sidecar, alembic 0005) · Step 2 endpoints #526 `5da9e1d` (POST `/procedures/{id}/run` + `/runs/{id}/gate/resolve` auto-resume; identity recorded server-side, AC-2 on the persisted row) · Step 3 gate state machine #527 `a0db450` (RESOLVED status; resume refuses undecided proposal gates + SoD tie re-assert; optimistic lock, alembic 0006) · Step 4 write-ahead #528 `bafdf92` (`run_procedure_persisted`; two-phase resolve — decision committed BEFORE effect, version bump AT decision commit = exactly-once under concurrency; `pending_execution` = the outbox seam) · Step 5 audit #529 `692f748` (append-only hash-chained `audit_log` + block trigger + INSERT-only `vero_audit_writer` role, alembic 0007; tamper-detect survives a superuser) · Step 6 pinning #530 `6cde2db` (`governance_pin.py`; fail-closed pin-mismatch at resume + gate; prose excluded; people deliberately NOT pinned; alembic 0008) · close-out #531 `28d919c` (completion fold: 10 ACs ticked, step→PR table, **5 disclosed deviations** incl. `/warm`+`/sleep`+`/intake/generate` gated + the AC-5 narrowing w/ empty-watch contract kept; `git mv` → `done/`). Local dev-box (disclosed): `.env` `API_AUTH_ENABLED=false` (code default now ON); dev DB migrated through alembic 0008. Offline throughout; MS-S1 cold | `353c04e` (#531 merge) / `28d919c` (#531 close) / `services/api/auth.py` + `services/engine/procedures/persistence.py` (write-ahead) + `services/engine/procedures/governance_pin.py` + `alembic/versions/{0005_action_identity,0006_pipeline_run_version,0007_audit_log,0008_governance_pin}.py` + `.github/workflows/ci.yml` + `docs/plans/done/0047-pre-pilot-hardening-authn-gate-audit.md` |

| 2026-07-02 | **PLAN-0046 (Q3 read-side ontology-binding build) EXECUTED + COMPLETE + CLOSED (session 93 cont., #511 feat + #512 close; PLAN → `done/`)** — renders the Accepted ADR-016 Q3 amendment into code; **all 11 ACs met.** `StepInput.reads: list[str]` + `AgentAllowed.object_types` (both `extra="forbid"`, backward-compat: absent/empty = loads as today) + the NEW pure `validate_read_bindings` load-gate (SD-1 Option A — `validate_runnable` + its ~12 call-sites untouched) wired at both production pre-flight sites (`run_procedure` + `persistence.resume_run`; skipped, no ontology I/O, for reads-absent procedures); `reads` → `STEP_GOVERNANCE_FIELDS` (OQ-A) + a disclosed `lift_to_step` strip-hardening (`StepDraft` reuses `StepInput` → generated drafts physically strip `reads` to ABSENT, OQ-C C1 pattern) + CI tripwire. 12 new tests; ruff + `mypy --strict` clean; **full offline suite 2066 passed / 5 skipped.** Zero runtime-data-flow change; honest frame (LOCKED-9): declared ✔ · load-gated ✔ · execution-bound ✖. SD-2 = Option A (verticals stay absent; gate inert until opt-in). The Q4 generic run-consume query executor = a SEPARATE later PLAN. Offline-only, no host-state | `eb63692` (#512 close) / `878b517` (#511 feat) / `services/engine/procedures/` (spec + orchestrator + draft-lift) + `docs/plans/done/0046-*.md` |

## Rotated this reconcile (session-106, 2026-07-07 — PLAN-0055 Ready + S1 Step 1 + branch-protection #602/#603/#604)

### Current-Focus block — Session 105 (head_commit `c9c0698`) [rotated 2026-07-07, session-106 reconcile]

> **Session 105, 2026-07-07 (head_commit `fe36e36` → `c9c0698`) —
> ADR-0028 Accepted (the procedure `schedule`-trigger scheduler = S1) +
> `main` greened.** Two merged PRs. `plan-drafter`-authored, Code R2 +
> committed via PR (ADR-009 D1/D2). **#599 — ADR-0028 (Status:
> Accepted).** Drafted Proposed (`5f3eec3`, plan-drafter) → **Cray
> ratified all 3 surfaced decisions 2026-07-07** (`c9c0698`,
> plan-drafter-authored, Code R2 + committed). The **ratified S1
> architecture:** SD-1 = a **separate long-lived worker/daemon**; SD-2 =
> **`croniter`** (thin, parse-only); SD-3 = **direct in-process
> `run_procedure_persisted`**. S1 is a **pure client** of the S2 actor
> plumbing shipped in s104 (PLAN-0053 Phase B) — so **"S2 before S1" is
> now satisfied**. The ADR decides **architecture only**; a **follow-on
> S1 build-PLAN** (not yet drafted) specs the build and will lift the
> `manual`-only trigger block at `orchestrator.py:146-150` + correct
> ADR-016 OQ-2 §1192-1195. Selection came from the `next-work-analyst`
> ranking (Cray picked S1, ADR-first). **#600 — `fix(tests)`: greened
> `main`.** `main` had been **CI-red since #595** (2 tests in
> `tests/api/test_runs_endpoints.py`), merged red through #596–#598. Root
> cause: the ADR-016 S2 RF-1 library guard (`resolve_gated_step`, added
> #595) fails closed when the resolved `principal` (`Person`) is `None` —
> and the **energy vertical authors no principals**, so an authenticated
> caller (`person_id="op-somchai"`, `person=None`, the documented Phase-A
> contract) hit `GateApproverError → 409` on gate-resolve. Fix (approach
> (a) — the guard is correct): the 2 happy-path tests now provision a
> **real `Person` approver** (monkeypatch `auth._principal_index`,
> mirroring `test_api_auth.py`); energy production `procedures.yaml`
> deliberately **not** given a principals block (would arm vertical-wide
> membership enforcement — the OQ-6 N≥2 boundary). Reproduced the 409 on a
> fresh DB, then verified **234 passed** (api+db+verticals). `4b7f472`.
> **Standing:** ADR-0028 **Accepted** + merged; no active PLAN (S1
> build-PLAN = the natural next); `main` **green**; 0 open PRs;
> `loop-dispatcher` **DISABLED**; MS-S1 idle; AI-assisted (Claude Code,
> session 105), no `Co-Authored-By` per §7.

### Recent-Decisions row — 2026-07-05 (PLAN-0051 reason-then-structure A/B — NULL result, COMPLETE session 99) [rotated 2026-07-07, session-106 reconcile]

| 2026-07-05 | **PLAN-0051 (reason-then-structure A/B — Wave-2(c)) DRAFTED → RATIFIED → BUILT (6 steps) → LIVE-RUN → COMPLETE + CLOSED (#565–#570) (session 99; PLAN → `done/`)** — operationalizes July-2026 research finding #2 (reason-then-structure lifts constrained-decoding accuracy 10-30%) as a **3-arm A/B** (`baseline` / `field_order_flip` / `two_pass`) on the two remaining single-pass structured-output call sites — **classify** (`classify_narrative`) + **nl_query** (`_translate`); the anomaly recommender was OUT of scope (already two-pass Pattern B). **Draft #565** `db8c889`→`8abdd33`/`bd8e2dc` (plan-drafter) → Cray ratified SD-1..SD-6 **as-rec** → Draft→Ready · **Step 1 classify plumbing #566** `1e6a121` (AC-1: keyword-only `arm` param, default `baseline` byte-identical; `field_order_flip` reasoning-first schema; `two_pass` free-form reasoning call omits `think`, CHECKPOINT-0; Arm-B moat guard byte-identical across arms) · **Step 2 classify driver #567** `426ebaa` (AC-2: `classify_ab_route` reusing PLAN-0041's 26-narrative corpus verbatim) · **Step 3 nl_query corpus #568** `b6619fd` (AC-3: 27 hand-authored gold questions over the energy ontology, all pass production `_validate_query`; `score_query` field-weighted match on RAW `_translate` output [SD-1]; pre-committed SD-4 thresholds) · **Step 4 nl_query plumbing #569** `74760bd` (AC-4: `arm` param on `_translate` default `baseline`; `field_order_flip` leading advisory `reasoning` field stripped before execute [Pydantic extra='ignore']; `two_pass`; `_validate_query` + Phase-B rewrite seam untouched) · **Step 5a harness + 5b results + Step 6 close #570** `b8ab793` (harness, skip-by-default) → `57a6593` (results + `git mv` → done/). **Live run (Step 5b — host-state §8, Cray go, full N=3 both sites, 2:17:02 on `gpt-oss:20b`): `2 passed`. RESULT: NO measurable lift on either site.** classify (AC-6): baseline at the **11/11 ceiling**; field_order_flip +0, two_pass −1; **Arm-B moat brake held 11/11 in EVERY arm/rep** (reasoning-order lever did not weaken the AT-2 abstain gate; no false-accepts). nl_query (AC-7): worst-rep mean baseline 0.978 vs variants 0.965–0.978; hard-class 0.844 all arms (Δ +0.000). **Recommendation (SD-6): REJECT both variants on both sites — keep the shipped `baseline`; NO production default changed; NO new ADR (SD-5).** The arm plumbing + 2 corpora + the A/B harness remain behind the `baseline`-default `arm` param as reusable scaffolding. The research "10-30% lift" **did not replicate** (both paths already strongly prompted; `gpt-oss:20b` extracts structured output well → the format tax is not biting) — a **valid null result**. **Offline gate AC-1..AC-5 (the binding bar) MET; AC-6/AC-7 (live) = confirming evidence.** Full record: `docs/logs/2026-07-05-plan0051-live-ab-results.md`. `loop-dispatcher` DISABLED; MS-S1 warmed once for the Cray-gated run then idle | `bb1921a` (#570 merge) / `57a6593` (Step 5b results + close) / `b8ab793` (Step 5a harness) / `74760bd` (#569 nl_query plumbing) / `b6619fd` (#568 nl_query corpus) / `426ebaa` (#567 classify driver) / `1e6a121` (#566 classify plumbing) / `services/engine/{classify,nl_query}` (`arm` plumbing) + the 2 A/B corpora + the skip-by-default A/B harness + `docs/plans/done/0051-*.md` |

### Recent-Decisions row — 2026-07-04 (PLAN-0050 ADR-0027 R2 semantic-enrichment ontology constructs, COMPLETE session 98) [rotated 2026-07-07, session-106 reconcile]

| 2026-07-04 | **PLAN-0050 (ADR-0027 R2 build — 4 OPTIONAL semantic-enrichment ontology constructs) DRAFTED → RATIFIED → BUILT COMPLETE (8 steps / 8 ACs) → CLOSED (#553–#563) (session 98)** — renders the Accepted ADR-0027 grammar into code: `synonyms` (th/en) · `sample_values` · `verified_queries` · metric `grain`/`join_path` now flow L1 grammar → Pydantic projection → L2 consistency → both v1 verticals → the LLM-facing context pack. **Draft #553** `db8c889` (SD-A..D surfaced) → **Ratify #554** `e9c4e07` (SD-A one-PR-per-vertical · SD-B verified_queries object-type-level · SD-C samples ⊆ enum · SD-D typed `Synonyms` model). **Step 1 L1 #555** `e430d5f` (AC-1: 4 constructs in `ontology_schema.json`, mirror `quantityBinding`) · **Step 2 projection #556** `3ee691a` (AC-2: typed `Synonyms`/`VerifiedQuery` + optional attrs on `PropertyMeta`/`ObjectTypeMeta`/`QuantityBinding`, `default_factory`) · **Step 3 L2 #557** `6b7cc74` (AC-3: `_check_enrichment` orchestrator — synonyms / sample_values [SD-C ⊆ enum] / verified_queries / quantity_binding_paths [SD-5 join_path]; no-op when absent, D2) · **Step 4 D2 GATE #558** `f0191b1` (AC-4: zero-backfill proof — `generate` byte-identical + git-clean) · **Step 5 energy-v1 backfill #559** `1254b2d` (AC-5: curated th/en synonyms + sample_values [enum-overlap + non-enum] + verified_queries + grain + join_path) · **Step 6 supply-chain-v1 backfill #560** `2e2150c` (AC-6: same, cold-chain; completes v1-batch backfill, ADR-0027 D5). **ADR-0027 erratum #561** `c23a7da` — Step-7 FINDING: the shipped R1 emitter did NOT read the enrichment fields (only a hardcoded degrade note); ADR-0027's "zero emitter change / for free" forward-reference was factually WRONG; corrected in-place, DESIGN (D1-D4, SD-1..7) unchanged, Status stayed Accepted. **Step 7 emitter fix #562** `33a2429` (AC-7: the 3 context-pack helpers RENDER the enrichment — synonyms `aka`, `sample values`, `Verified queries`, `@grain via join_path` — + the degrade note is now CONDITIONAL). **DISCLOSED DEVIATION:** AC-7 met via a **Cray-authorized emitter change** (erratum #561 → #562), NOT "for free" — the IN-1 escape hatch firing as designed (gap surfaced, not silently patched). **COMPLETE fold + `git mv` → done/ #563** `81cd3ff` (Status → Complete, 8 ACs ticked, deviation disclosure in the completion note). **Outcome:** R2's moat value (th/en synonyms + closed sample sets + verified queries + metric grain) now reaches the LLM context pack; both real vertical packs populate (Thai synonyms present; degrade note gone). **AC-8 / CI:** every step's PR green under the PLAN-0047 Step-7 CI gate (ruff + ruff-format + `mypy --strict` + full suite w/ postgres + `alembic upgrade head` + `alembic check`); **no Alembic migration the whole arc** (the 4 constructs are ontology-metadata, both verticals). **Tests ~+15 across the arc** (Step1 +5, Step2 +2, Step3 +4, Step4 +2, Step7 +2; baseline 2142 → ~2157, CI-green per PR — full suite NOT re-run locally, CI is the gate). `loop-dispatcher` DISABLED; MS-S1 cold (offline throughout) | `81090de` (#563 merge) / `81cd3ff` (COMPLETE fold) / `33a2429` (#562 emitter) / `c23a7da` (#561 erratum) / `services/engine/{code_generator.py,ontology_schema.json,ontology_meta.py,ontology_validator.py}` + `verticals/{energy,supply_chain}/ontology/*_v0.yaml` + `docs/plans/done/0050-ontology-semantic-enrichment-build.md` |

### Recent-Decisions row — 2026-07-04 (PLAN-0048 Q4 executor + PLAN-0049 v1 ontology bundle + ADR-0027 Accepted, sessions 96/97) [rotated 2026-07-07, session-106 reconcile]

| 2026-07-04 | **PLAN-0048 Q4 generic query executor COMPLETE + CLOSED (#533–#541) + PLAN-0049 v1 ontology bundle COMPLETE {1,2,4,5} (#542–#550, R2 carved out) + ADR-0027 semantic-enrichment fields ACCEPTED (sessions 96/97)** — suite 2097 → 2142 passed / 5 skipped (+45); every feature PR green under the PLAN-0047 Step-7 CI gate (ruff + ruff-format + `mypy --strict` + full suite w/ postgres + `alembic upgrade head`; #548 added an `alembic check` drift-guard step). **PLAN-0048** (read side gains **declared==dispatched** via `QueryStepExecutor`; Steps 1–3 reconciled in #540): Step 4 seams/docs #539 `f7d4972` (merge `ab394b0`) + COMPLETE fold + `git mv` → done/ #541 `73a6f9c` (merge `0215b3a`). **PLAN-0049** (executable set {1,2,4,5}; R2/Step-3 carved out to ADR-0027): draft #542 `6626d97` (SD-1..7 surfaced) · SD-1..7 as-rec + flip Draft→Ready + carve R2 #543 `c8b48be` · Step 1 energy-v1 #544 `69d7759` (asset_type feeder/cap_bank/gas_engine; NEW `rated_current_a` [SD-6]; measured_kind current/voltage; alembic 0009) · version=content-revision #545 `aec644d` (`ontology_schema.json` `version` const 0 → `{integer, minimum 0}` — the GRAMMAR-version field repurposed as content-revision, SD-2 Cray-confirmed; energy→1, supply_chain→1) · Step 2 supply-chain-v1 #546 `37387ed` (NEW Equipment entity + `shipment_uses_equipment` + `adjust_setpoint`; measured_kind temperature/battery; enum gaps; NO committed ORM — SD-3 gitignored fallback, SD-4 parity gap documented) · Step 4 R1 context-pack emitter #547 `b80dcff` (`emit_context_pack` 7th emitter; closed-set refuse-not-guess; R2 DEGRADE PATH reads ADR-0027 fields when present; 32K token-budget tripwire) · Step 5 alembic autogenerate #548 `1a689ef` (`compare_type=True`; CI `alembic check` drift-guard; migration<->ORM lockstep runbook) · COMPLETE fold + `git mv` → done/ #550 `579c5d1` (merge `d7041f4`). **ADR-0027** (ADR-008 D2/D3 grammar amendment, 4 OPTIONAL constructs: synonyms th+en · sample_values · verified_queries · metric grain/join-path; mirrors ADR-0021; backward-compat HARD INVARIANT; governed≠generated; decides grammar + defers build): Proposed #549 `a7bd595` (merge `e61c287`, 7 SDs) → **Accepted #551 `d8f9ec5`** (merge `9f95942`) — Cray ratified ALL SD-1..7 as-recommended (none overridden); **SD-6 follow-up build = PLAN-0050** (L1 `ontology_schema.json` + `ontology_meta.py` optional attrs mirroring QuantityBinding + L2 validators + energy-v1/supply-chain-v1 backfill; the shipped R1 emitter consumes it for free via the degrade path). #537 fixture-hermeticity fix (`2c627bb`) closed the #535/#536 concurrent-pytest disclosures. `loop-dispatcher` DISABLED; MS-S1 cold (offline throughout) | `9f95942` (#551 merge) / `d8f9ec5` (ADR-0027 Accepted) / `d7041f4` (#550 merge) / `0215b3a` (#541 merge) / `docs/adr/0027-ontology-semantic-enrichment-fields.md` + `docs/plans/done/{0048-q4-generic-query-executor,0049-v1-ontology-bundle}.md` + `services/engine/code_generator.py::emit_context_pack` + `services/engine/ontology_schema.json` + `alembic/versions/0009_*.py` |
