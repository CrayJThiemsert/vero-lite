---
last_updated: 2026-06-29T14:54:24+07:00
session: 86
current_batch: "session-86: PLAN-0042 v1 offline tail COMPLETE (#470/#471/#472, Cray-merged) → PLAN-0042 v1 (Steps 1–3+5) COMPLETE, PLAN git mv → done/. AT-2 layer typed + run-gated + rendered authoritative (advisory band) + red-teamed offline."
current_actor: code
blocked_on: "Nothing blocking — PLAN-0042 v1 complete (offline oracle is the gate; pytest 1877/24). Non-blocking carries: AC-13-ALT (A2 run path) needs a principal-identity capability; OQ-B placeholder values provisional pending Cray sign-off (B1, verticals/ PR); PLAN-0041 ready (live Step 5 = Cray go); loop-dispatcher DISABLED."
next_action: "Mint a follow-on PLAN for AC-13-ALT / the A2 run path once a principal-identity-resolution capability exists; OQ-B real Fastenal numbers fold-in (B1, small verticals/ PR); PLAN-0041 live Step 5 (Cray host-state go). loop-dispatcher stays DISABLED."
head_commit: 973ba69
recent_commits: [973ba69, fb46095, 5464831, 5fac5d2, c70012a, 4ff1180, 9d1015c, b91a16e, e92e2f5, 059c6ea]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

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

> _Rotation note (session-85 reconcile, 2026-06-29): the **Session-83** Current Focus
> block (PLAN-0040 AC-B5 — the live MS-S1 single-shot INTAKE FACE — shipped +
> LIVE-VERIFIED → PLAN-0040 [A+B+C + live intake] DONE 100% via #457/#458/#459;
> head_commit `ef46ea0`; the oldest in-window block) was rotated to hold STATUS under the
> **R1 64 KB hard ceiling** (the file had reached ~63 KB and adding the s85 PLAN-0042
> block would cross it; R1 overrides the R2 4-session window) — moved verbatim to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md), per the
> STATUS.md Rotation Policy (R1/R2/R4). Resulting Current-Focus window = {85, 84 (×2
> blocks)}._

> _Rotation note (session-84 cont. reconcile, 2026-06-29): the **Session-82** Current
> Focus block (PLAN-0040 Phase C — the edit-mode authoring GATE UI — COMPLETE end-to-end
> #453/#454/#455, head_commit `d3c2279`; the oldest in-window block) was rotated to hold
> STATUS under the **R1 64 KB hard ceiling** (the file had crossed it at ~65.6 KB when the
> session-84-cont O-3 / ADR-0025 block landed; R1 overrides the R2 4-session window) —
> moved verbatim to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md), per the
> STATUS.md Rotation Policy (R1/R2/R4). Resulting Current-Focus window = {84 (×2 blocks), 83}._

> _Rotation note (session-83 reconcile, 2026-06-27): the **Session-81** Current
> Focus block (PLAN-0040 Phase B offline pipeline [the S0–S6 two-call generator]
> BUILT + merged #449 + post-audit hardened #450, head_commit `8e11f82`) and the
> **Session-80** block (PLAN-0040 Phase A offline guardrail spine, zero-LLM, BUILT
> end-to-end #444/#446/#447, head_commit `42a0aa0` — the oldest in-window block)
> were rotated to hold STATUS under the **R1 64 KB hard ceiling** (the file was at
> ~63 KB, near the ceiling) and back toward the soft ceiling when the session-83
> PLAN-0040 AC-B5-LIVE block landed, both moved verbatim to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md), per
> the STATUS.md Rotation Policy (R1/R2/R4). Resulting window = {83, 82}._

> _Rotation note (session-82 reconcile, 2026-06-27): the **Session-79** Current
> Focus block (PLAN-0039 — the read-only 5-facet procedure viewer — BUILT
> end-to-end [#437/#440], plus the harness/memory sharpening pass — CLAUDE.md §6
> "Verification is hygiene, not a verdict" #438 + Lesson #0027 #439; head_commit
> `3eaf881` — the oldest in-window block) was rotated to hold STATUS comfortably
> under the **R1 64 KB hard ceiling** (the file was at ~62 KB, near the ceiling)
> when the session-82 PLAN-0040 Phase-C-COMPLETE block landed, moved verbatim to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md),
> per the STATUS.md Rotation Policy (R1/R2/R4). Resulting window = {82, 81, 80}._

> _Rotation note (session-81 reconcile, 2026-06-26): the **Session-78** Current
> Focus block (Stage 3 of the generative-procedures arc KICKED OFF — ADR-0024
> archetype-first generator ACCEPTED #434 + PLAN-0039 read-only 5-facet viewer
> Ready #435 + the ADR-0024 OQ-disposition errata, head_commit `4e56d4b` — the
> oldest in-window block) was rotated to hold the Current Focus window at the
> **R2 4-session cap** (resulting window = {81, 80, 79}) and STATUS under the **R1
> 64 KB hard ceiling** when the session-81 PLAN-0040 Phase-B block landed, moved
> verbatim to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md), per
> the STATUS.md Rotation Policy (R1/R2/R4)._

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
| 2026-06-29 | **PLAN-0042 v1 (O-3 AT-2/managerial layer) OFFLINE TAIL COMPLETE → v1 (Steps 1–3 + 5) COMPLETE (session 86, #470/#471/#472, all Cray-merged)** — the offline A1 tail of the AT-2/managerial build; PLAN `git mv` → `done/`. The AT-2 layer is now typed + run-gated + rendered authoritative (with the advisory band) + red-teamed offline. **Step 3a (#470, feat `4ff1180`):** the scoped value-only prose-lint over AT-2 free-text (`governance_prose_lint` = value classes + an approver-role-token check; OMITS the decision-verb + broad-identifier classes, finding 6) + a LOAD gate (`Procedure._validate_at2_free_text` blocks load on a ฿-amount/weight/role token smuggled into AT-2 free-text) + the 3 ADR-0025-D4 advisory NON-AUTHORITATIVE free-text fields (`EmergencyWaiverPolicy.justification`, `DoaTier.note`, `ScoredCriterion.note`); one reword (`"3-bid"`→`"three-bid"`). **Step 3b (#471, feat `5fac5d2`):** the PLAN-0039 read-only viewer renders the typed AT-2 content (DOA ladder/scored rule/compliance gate/SoD) as AUTHORITATIVE (the Box-3 "the gate is no longer blind" artifact, AC-13) + bands the AT-2 free-text "ADVISORY — NOT A CONTROL" (OQ-D); no API change (`model_dump` serializes it), verified live on the preview. **Step 4 (AC-13) = author + render only (A1)** — delivered by Step 3's render, no separate build. **Step 5 (#472, test `5464831`):** the D8 offline oracle `tests/services/engine/procedures/test_red_team_at2.py` consolidates the 3 red-team fixtures (hollow-but-complete → refused; leak-in-free-text → blocks load; identity-collapse role-level = single-step SoD rejected at construction + a missing-SoD `doa_tier` proc refused at the gate) + a positive control; PRINCIPAL-level collapse / literal `approver_role==requester_role` / un-gated-audit are A2-deferred (AC-13-ALT), documented + intentionally NOT asserted (no false coverage). Gate (every step, offline): ruff + ruff-format + `mypy --strict services/` (64 files) clean, **pytest 1877 passed / 24 skipped**, no live MS-S1. **AC-13-ALT (the A2 run path)** deferred to a follow-on PLAN, gated on a principal-identity-resolution capability the engine lacks today. OQ-B placeholder control values stay provisional (real Fastenal figures fold in via a small `verticals/`-only PR, B1; blocks nothing). `loop-dispatcher` stays DISABLED | `973ba69` (#470/#471/#472) / `services/engine/procedures/{spec,draft,orchestrator}.py` + `tests/services/engine/procedures/test_red_team_at2.py` + `services/api/static/assets/view-procedures.js` + `docs/plans/done/0042-at2-managerial-build.md` |
| 2026-06-29 | **PLAN-0042 (O-3 AT-2/managerial layer) Steps 1-2 SHIPPED + MERGED (session 85 cont., #467/#468)** — typed AT-2 content (D2) + the AT-2-aware run-gate (D5) closing the live blindness defect; the procurement AT-2 migrated prose→typed behind a green golden test; OQ-B=B2 values mirror the data adapter (provisional, pending Cray sign-off). **Step 1 (#467, `6176b18`):** discriminated `Step.governance_content` (`DoaLadder`\|`ScoredRule`\|`ComplianceGate`, keyed on `kind`) + `Procedure.separation_of_duties`; D3 bypass unrepresentable (`Decimal` money; closed `RelaxableConstraint` enum can't name compliance/SoD; `blocks_po`/`requires_justification` `Literal[True]`; total strictly-monotonic DOA ladder); D4 H-field invariants (new fields in `GOVERNANCE_FIELDS`, never on a draft type; draft-disjointness + `StepFacet`-unreachability CI). Finding 1 honored (DOA tiers nest in `DoaLadder`, no 2nd `Step.tiers`). **Step 2 (#468, `059c6ea`):** the AT-2-aware run-gate + the prose→typed migration in ONE PR behind the golden test — `validate_governance_complete` now owes typed `governance_content` on the AT-2 kinds + a `doa_tier` proc owes `separation_of_duties`; an empty-DOA/no-criteria/no-SoD AT-2 is no longer run-loadable (the negative hollow-but-complete regression = the D5 ratification gate). **Build interps:** principal-level SoD + resolved-tier strict-escalation deferred to **A2 (AC-13-ALT)** — no engine principal/role-rank layer; the author-time gate enforces the STRUCTURAL form (≥2 distinct steps; ladder totality). Gate: mypy --strict + ruff clean, **pytest 1843/24**; no live MS-S1. Remaining: Steps 3 (prose-lint + "ADVISORY — NOT A CONTROL" banding) + 5 (offline oracle), A1 | `059c6ea` (#467/#468) / `services/engine/procedures/{spec,draft,orchestrator}.py` + `verticals/procurement/procedures.yaml` |
| 2026-06-29 | **PLAN-0042 (the O-3 follow-on AT-2 / managerial-layer BUILD PLAN) DRAFTED + RATIFIED + MERGED (session 85, #465)** — the build PLAN ADR-0025 OQ-5 named; renders ADR-0025 (Accepted #463) D1–D8 + owns migration sequencing. **Build PLAN — no new ADR.** **Primary deliverable = closing a LIVE shipped defect:** `validate_governance_complete` is blind to AT-2 *content* (`rule_gate` evaluate → `[]`; `scored_rule`/`doa_tier` action → `[handler,autonomy]`, both filled → no AT-2-content obligation) → the build **types the AT-2 content** (D2 discriminated `Step.governance_content` union + `Procedure.separation_of_duties`), makes the **run-gate AT-2-aware** (D5), and **migrates the procurement AT-2 prose→typed in ONE PR behind a green golden test** (the migration trap). **Cray-ratified:** **OQ-A = A1** (author + render only — no principal-identity layer for run-time SoD, so D6 author+render fallback; the A2 run path deferred to a follow-on PLAN); **OQ-B = B2** (labelled-provisional placeholder control values + Cray sign-off — typing D2 is authoring not transcription); **OQ-C/D/E confirmed** (golden test + D5 migration in ONE PR; scoped value-only prose-lint + "ADVISORY — NOT A CONTROL" band; no per-spec `schema_version`). **Process:** Cowork-drafted (ADR-009 D1) → **Code R2** re-verified the fact-pack on HEAD `1305b32` + surfaced two substrate items: **finding 1** (a `Step.tiers` collision — `StepTiers` = PLAN-0022 handler taxonomy at `spec.py:264`, in `STEP_GOVERNANCE_FIELDS` → DOA tiers must nest in `DoaLadder`, never a 2nd top-level `Step.tiers`) and the **SoD principal-vs-role scoping finding** (A1 = author-time structural+role-level SoD; principal-identity SoD is run-time → relocated to the deferred **AC-13-ALT**, lineage = superseded-by-A1, not an ADR amendment) → Code revision dispatch → Cowork applied 3 surgical deltas → Cray-ratified → Code R2 + committed (#465). **v1 build surface = Steps 1–3 + 5** (A2 / AC-13-ALT deferred). `loop-dispatcher` stays DISABLED; MS-S1 cold, no live run (offline oracle is the gate). NEXT = execute Step 1 (D2 union + SoD + D3/D4) then Step 2 (D5 gate + migration in ONE PR; author the B2 placeholders) | `21d7669` (#465) / `docs/plans/0042-at2-managerial-build.md` |
| 2026-06-29 | **ADR-0025 (AT-2 / managerial-process layer) RATIFIED + ACCEPTED (session 84, #463)** — makes DOA/SoD/scored-rule/compliance governance first-class (the Box-3 "Action = contract" story the Rock-4 research found is vero-lite's strongest sellable box; Palantir's Apr-2026 "each Action is a contract" ≈ our `Agent.allowed` + gate + audit); **revisits ADR-0024 D7** (AT-2 deferral) + **decides ADR-0024 OQ-8** (typed content sub-model). **Re-framed around a SHIPPED DEFECT Code R2 verified live on HEAD:** `derive_governance_todo` owes no obligation for `scored_rule`/`rule_gate`/`doa_tier` → `validate_governance_complete` is blind to AT-2 content (an empty-DOA AT-2 is run-loadable today). **D2** authoritative discriminated `Step.governance_content` keyed to `gate_kind` (not the non-authoritative facet; D2-A4 held); **D3** bypass structurally unrepresentable (`Decimal` money; total-cover DOA ladder; strict-escalate waiver; compliance+SoD non-waivable); **D5** run-gate becomes AT-2-aware (closes the defect, + a negative regression test); **D7** the AT-2 generator stays deferred under a CI-enforced N≥2 re-trigger (AT-2 = N=1). **Cowork-drafted + a Cowork-run panel (disclosed self-review, NOT independent of the drafter) → Code R2 = the independent check (substrate fact-pack independently verified) → Cray-ratified per the recs** (OQ-1=(c) build-layer/defer-generator [the N=1 "(b)-minus-codegen" trade accepted because the defect forces typing the obligation regardless]; OQ-2=(b)-in-(a); OQ-3=D6 boundary [concrete run-vs-author → the follow-on PLAN]; OQ-4/5 per rec). A harness Stop-hook said "commit as Accepted" pre-ratification — Code **declined** (false attribution on the permanent record), held, committed on Cray's actual ratify. NEXT = the follow-on build PLAN (OQ-5, separate dispatch). Also s84: O-1 (Box-4 ฿ pitch artifact) done; the Rock-4 research delivered + the O-sequence locked | `f56a6e8` (#463) / `docs/adr/0025-at2-managerial-layer.md` |
| 2026-06-28 | **PLAN-0041 (classify-prompt enrichment lever) RATIFIED + COMMITTED (session 84, #461)** — the fix for the PLAN-0040 AC-B5 live finding (~1-in-3 false-abstain on a textbook AT-1/AT-3). A **prompt-only** lever: enrich `build_classify_messages` with per-archetype descriptions (derived from the canonical catalog) + a positive band-vs-out-of-scope-gate explainer that teaches the band case, so the live model stops mis-tagging the judge step with an AT-2-only `gate_kind`. **Moat-safe:** the AT-2 cross-check (`_archetype_disagreement`/`_AT2_ONLY_KINDS`, ADR-0024 D4/D7) stays **byte-identical**; no schema change; **no new ADR**. **OQ-C twin-metric:** Arm B **11/11 AT-2-abstain HARD gate** + a pre-committed pass/fail read; offline tests = the gate, the live hit-rate lift = confirming evidence behind a Cray host-state go (§8). **Cowork-drafted (ADR-009 D1) → Code R2-reviewed (fact-pack byte-verified; LOCKED-7↔D4/D7 mapping confirmed) → Cray-ratified (OQ-A..E recs as-is) → committed → Cray merged (no self-merge).** Also session 84: a **strategy consultation** mapping vero-lite onto the **Four-Box Business Model** → a 4-rock roadmap (Rock 1 = PLAN-0041; Rock 2 = AT-2/managerial; Rock 3 = Box-4 economics + ontology data-binding; **Rock 4 = a Cowork 4-box+Palantir deep-research dispatch**, awaiting relay). NEXT = execute PLAN-0041 (offline Steps 1-4; live Step 5 = Cray go) + relay Rock 4. `loop-dispatcher` stays DISABLED | `7601174` (#461) / `docs/plans/0041-classify-prompt-enrichment.md` |
| 2026-06-27 | **PLAN-0040 AC-B5 (the live MS-S1 single-shot intake face) SHIPPED + LIVE-VERIFIED → PLAN-0040 (A+B+C + live intake) DONE 100% (session 83, #457/#458/#459)** — the last PLAN-0040 item (LOCKED-9 / D9): narrative → classify → human-confirm → governed skeleton on live MS-S1 `gpt-oss:20b` (local-only, §8). Three **Code-direct per-step PRs off `main`, Cray merged each (no self-merge)**. **#457 server (`0fd0489` merge):** `services/api/routers/procedure_draft.py` — `POST /procedures/draft/{classify,build,instantiate}` (classify = narrative→archetype, no skeleton, LOCKED-5; build = CONFIRMED archetype→governed skeleton, refuses unconfirmed/unknown 422; instantiate = ZERO-LLM manual-pick fallback, D9); model-pinned + local-only; `_governance_todo`→public `build_governance_todo`; **security fold `5c00a76`** = classify rationale now `prose_lint`-gated (was leak-class-1) + degraded detail no longer echoes MS-S1 host/port; offline route tests (recorded-fixture, zero host-state). **#458 front-end (`0dd7693` merge):** `intake-procedures.js` capture (classify→confirm→build + graceful degradation to manual-pick/sample); `view-procedures.js` `mount(opts.draft)` renders via the **existing gate path** (no second renderer, LOCKED-8); `api.js` `O.Draft.*`; `?v=` c19→c20. **#459 prose fix from the live run (`ef46ea0` merge, `751c1e2`):** `_build_procedure_draft` falls back to **POSITIONAL** step pairing when the count matches — the live model does NOT echo template `step_id`s so descriptions dropped to `""`; advisory-prose only, governance untouched, +1 test. **Gate:** ruff+ruff-format+`mypy --strict services/` (64 files) clean; **pytest 1801 passed/24 skipped.** **LIVE (Cray-pre-approved host-state + hands-on UI verify):** **moat HOLDS** — poisoned narrative → build → forced values NOWHERE (leaked `[]`), all governance ABSENT, fails `validate_governance_complete` (D6); classify matches live for clear AT-1/AT-3 (conf 0.9–0.95), happy path = value-free advisory prose + unfilled stubs + empty `goal` (OQ-B B2). **Live findings (honest):** classify is non-deterministic + the strict per-step AT-2 cross-check → ~1-in-3 false-abstain (mis-tag of the judge step with AT-2-only `scored_rule`/`rule_gate` → correct abstain, never down-classify, LOCKED-7; SAFETY signal only, never builds, never leaks); the offline fixture masked the prose step-id-rename gap (live = cheapest catch). NEXT lever = classify-prompt enrichment (G2-gated → Cowork), NO guard relax without data + ADR. `loop-dispatcher` stays DISABLED | `0fd0489` (#457) / `0dd7693` (#458) / `ef46ea0` (#459) / `services/api/routers/procedure_draft.py` + `services/api/static/assets/{intake-procedures,view-procedures,api}.js` |
| 2026-06-25 | **Stage 3 KICKED OFF — ADR-0024 (archetype-first procedure generator) ACCEPTED #434 + PLAN-0039 (read-only 5-facet viewer) Ready #435 + the ADR-0024 OQ-disposition errata (session 78)** — opens Stage 3 of the generative-procedures arc (ADR-016 Phase 2). Both artifacts **Cowork-drafted (ADR-009 D1) → Code R2-reviewed → Cray-ratified → committed (D2)**. **ADR-0024 (#434, add `c90b2d2`):** archetype-first generation **backed by a Code-run 5-specialist design panel** (LLM-pipeline · governance · schema · product-UX · red-team). **D1–D12 locked:** classify narrative → 1 of N archetypes → deterministic-code instantiates → LLM drafts advisory prose only (**exactly 2 narrow LLM calls**, classify-don't-synthesize ADR-0021); **"governed ≠ generated" re-fenced at the AUTHORING surface + made MECHANICAL** = a **restricted draft type** with NO governance fields (leak = type error) + a deterministic prose-lint; generator emits `gate_kind` (closed-enum) but **never a value/handler/threshold/tier/autonomy/env_var** (D4); **abstain never force-fit** (D5); determinism invariant holds at the authoring layer; skeleton **draft-loadable but NOT run-loadable** until a human authors gates (D6); **v1 = AT-1 family (AT-1/AT-1b/AT-3), AT-2 DEFERRED** (only AT-2 = `procurement.emergency_sourcing`, N=1; catalog really N≈2; D7); **one review surface**, read-only viewer ships first (D8); the catalog promotes prose→machine-readable `ArchetypeTemplate` (D2). **9 OQs Cray-ratified ACCEPTED** as standing guidance. **PLAN-0039 (#435, `edd28a6`):** a **zero-LLM** oct-demo view rendering **every shipped procedure (5 across 4 verticals — Cowork corrected the dispatch's "4"→5, procurement ships two)** by its 5 facets per step, authoritative band visually distinct from prose, served by read-only `GET /procedures`; built as the **read-mode of the ONE component PLAN-0040 extends to edit-mode** (`mode:read|edit` + pure `facetModel(step)`, AC-7); **AT-2 RENDERED here though AT-2 generation is deferred (D7)**; **7 UI/endpoint OQs Cray-ratified ACCEPTED**. **ADR-0024 OQ errata (commit `4e56d4b`, bundled into #435):** records the ratified OQ disposition in the Accepted ADR's OQ section — Code could NOT inline it (editing an Accepted ADR is **G1-gated**; **in-context approval does NOT override the local-Ollama classifier**, fail-closed deny → routed via Cowork, the s77 chore-PR precedent); **NO decision changed (D1–D12 byte-identical, diff-verified)**. **Notes:** PLAN-0039 + errata bundled one PR / two commits (#435, Code-judgment, separable in history); **`loop-dispatcher` stays DISABLED**; **no live MS-S1** (docs only, §8); pre-commit detect-secrets + handoff-validation green. NEXT = build PLAN-0039 (the viewer) then dispatch PLAN-0040 (the generator, AT-1 family, G2-gated) | `c90b2d2` (#434) / `edd28a6` + `4e56d4b` (#435) / `docs/adr/0024-procedure-generator.md` + `docs/plans/0039-readonly-facet-viewer.md` |
| 2026-06-25 | **PLAN-0038 (ADR-016 D2 Amendment implementation) EXECUTED end-to-end → Complete + archived; Stage 2 (generalized-schema extraction) now COMPLETE on real data (session 77, batch 3, #431/#432)** — completes Stage 2 of the generative-procedures arc, now proven on real data not just the model. **Step A (PR-1, #431, feat `bf7e858`):** the `services/engine/procedures/spec.py` engine edit — the typed `facet` sub-model per the amendment delta (`BandSource`/`GateKind` (6 kinds)/`DecisionCondition` w/ `band_source⇔gate_kind` + `env_var`-only-with-`env` validator/`StepFacet`/`Step.facet`), keeping `extra="forbid"` (facet now a KNOWN key) — the **first deliberate `spec.py` edit since procurement's zero-engine-edit (CQ-1)**, ADR-sanctioned; schema-level facet tests landed here (suite 1669 passed). **Step B (PR-2, #432, feat `777393c`, merge `42a8327`):** migrate the **4 verticals'** comment-facets → the real typed `facet:` field — **config + tests only, no `services/` edit**; +19 end-to-end migration round-trip tests. **SDs (Cray-resolved):** SD-1=(a) populate all 5 facets (`decision_condition`+`llm_assist` typed; `input`/`output`/`governance` str notes from the comment prose); SD-2=(a) remove the comment blocks (single carrier, grep confirms 0 leftover `# facet[`); SD-3=(b) split A/B PRs. **D2-A3 `gate_kind` mapping:** energy/supply_chain `judge`→`env_band` (`OCT_RECOMMEND_THRESHOLD`); aquaculture/procurement `judge`+`judge_stock`→`in_file_band` (points at the typed `threshold`/`direction`/`watch_margin`, no re-store — AC-6); procurement `compliance`→`rule_gate`, `source`→`scored_rule`, `approve`→`doa_tier`; reads/mechanical writes/audit terminals/simple gated actions→`none` (incl. `escalate_watch`=`none`+`decision_condition.note`, Cray-endorsed). Updated the stale "facets are comment-only" framing in `verticals/procurement/README.md` + the procurement `procedures.yaml` header. **`facet` stays non-authoritative** — engine reads but does NOT consume it at run time (D2-A4; grep = 0 `.facet` reads in `services/`). Gates: full offline suite **1688 passed/22 skipped** (1669 baseline + 19 new), ruff + ruff-format clean, mypy --strict `services/` clean, no live MS-S1 (§8 — pure schema/config). `loop-dispatcher` still DISABLED all session (Stop-hook root-fix deferred = precondition for re-enable). PLAN-0038 `git mv` → `done/`. NEXT = Stage 3 (the procedure generator, ADR-016 Phase 2, Rule-of-Three-deferred) + a schema-driven 5-facet review UI | `bf7e858` (#431) / `777393c` (#432) / `services/engine/procedures/spec.py` + `verticals/{energy,supply_chain,aquaculture,procurement}/procedures.yaml` + `docs/plans/done/0038-*.md` |
| 2026-06-25 | **Stage 2 COMPLETE — ADR-016 D2 Amendment (first-class typed `facet:` Step field) ACCEPTED + merged (#428) + PLAN-0038 impl PLAN minted (#429) (session 77, batch 2)** — Step C promotes the 5-facet annotation from a YAML comment to a **first-class, typed, validated, optional `facet:` field** on `Step`, completing Stage 2 (generalized-schema extraction). **Cowork-drafted** (ADR-009 D1) → Code R2-reviewed (gate_kind↔N=4 split, `spec.py extra="forbid"`+typed fields, `procedures.yaml` engine-read, validator dog-food 0 errors) → **Cray-ratified both forks** → committed (D2). **Fork 1 = Hybrid** (`facet` carries net-new `decision_condition`+`llm_assist` typed; `input`/`output`/`governance` optional non-authoritative notes — one source of truth, `spec.py` already types 4/5 via PLAN-0022). **Fork 2 = discriminated `gate_kind`** (enum over the 6 N=4 kinds `env_band`/`in_file_band`/`rule_gate`/`scored_rule`/`doa_tier`/`none` + `band_source`/`env_var`; `in_file_band` points at the existing typed band, no re-store). **Process note:** the ratify status-flip (Proposed→Accepted) was **G1-blocked for Code** — editing an already-Accepted ADR is denied **even with Cray per-diff approval + a warmed `gpt-oss:20b` classifier** (genuine policy, not a fail-closed infra deny; distinct from the ratify-transition case s40/67) → resolution = chore-PR path: **Cowork applied the flip** (ungated), Code committed, Cray merged (= the G1 review); [[project_g1_adr_gate_override_via_incontext_approval]] updated. **PLAN-0038 MINTED Draft** (#429, `b2f19bc`) — **`plan-drafter`-authored** (ADR-013 D1) → Code R2-reviewed → committed. Scope: the `services/engine/procedures/spec.py` engine edit (typed `facet` per the delta) + migrate the 4 verticals' comment-facets → the real field + load/validation tests — the **first deliberate `spec.py` edit since procurement's zero-engine-edit (CQ-1)**, ADR-sanctioned. **Schema only** (engine still ignores `facet` at run time); **implements nothing on commit**; **3 OPEN SDs** (note-migration / comment-removal / PR-granularity). Gate = offline suite (1651 baseline + new tests) + `mypy --strict`; no live MS-S1. NEXT = Cray merges #429 + adjudicates SD-1/2/3 → execute PLAN-0038 → Stage 3 generator + review UI | `0b56954` (#428) / `b2f19bc` (#429) / `docs/adr/0016-governed-procedure-engine.md` + `docs/plans/0038-*.md` |
| 2026-06-25 | **PLAN-0037 / Stage 2 PREP COMPLETE — 5-facet retrofit (→N=4) + procedure-archetype catalog SHIPPED + PLAN archived (session 77, #424/#425/#426)** — Stage 2 PREP for the generative-procedures target. PLAN-0037 was **`plan-drafter`-authored** (the in-harness subagent, ADR-013 D1 phased authority) → Code R2-reviewed + committed (#424, ADR-009 D2; separation intact); Cray chose the formal-PLAN route (ทาง 1). **Step A (#425, content `31ded05`):** retrofit the SD-4 5-facet annotation (`input · decision-condition · llm-assist · output · governance`) as **YAML comment blocks** onto `energy`/`supply_chain`/`aquaculture` `procedures.yaml` → consistent **N=4** instrumentation (Rule-of-Three substrate). **Provably inert:** `services/engine/procedures/spec.py` `Step` declares `extra="forbid"` (so `facet:` can only be a comment) + the loader uses `YAML(typ="safe")` (discards comments) → Step objects byte-identical, static-JS demos untouched; gate parse-clean all 4 verticals (steps unchanged 3/3/5/10), **66 insertions all-comment / 0 deletion**, **full offline suite 1651 passed/22 skipped** (baseline), no live MS-S1 (§8). Captured the env-vs-in-file judge-band split (energy/supply_chain via `OCT_RECOMMEND_THRESHOLD`; aquaculture/procurement in-file) as the Step-C input. **Step B (#426, content `c3b477a`):** the procedure-archetype catalog at `docs/conventions/procedure-archetypes.md` (AT-1 `anomaly→action`, AT-1b `watch+summary`, AT-2 `request→approve→fulfill`, AT-3 `monitor→reorder`) — the canonical reference the Step-C ADR + Stage-3 generator cite. SD-1=one PR for the 3 verticals / SD-2=Step B follow-on PR / SD-3=catalog home `docs/conventions/` (all Cray-resolved). **`loop-dispatcher` (Cray s77) = keep-disabled + guard** (over fix-hook / delete); the Stop-hook root-fix (scheduled-task auto-continue exemption) is deferred + is the precondition for any re-enable. **Out of scope (forward):** Step C (ADR-016 first-class `facet:` field = a separate **Cowork-drafted ADR**, G2-gated) + Stage 3 (the procedure generator, Rule-of-Three-deferred). PLAN-0037 `git mv` → `done/` | `f029913` (#424/#425/#426) / `verticals/{energy,supply_chain,aquaculture}/procedures.yaml` + `docs/conventions/procedure-archetypes.md` + `docs/plans/done/0037-*.md` |

## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13 (ratified `4d1347b`, #302; committed Proposed `e25281d`, #297 + instruction `e387a63`, #298 + R1 errata `655344d`, #300) — guarded trial under observation (parallel to ADR-012). A specialist Cowork project role-plays a Thai operator and emits a "partner profile package" to rehearse the intake+PDPA pipeline before a real partner; venue OUTSIDE the governance tiers (no commits / no repo mount / enters via Code receive). Three BINDING anti-circularity rules R1/R2/R3 (R3 SYNTHETIC provenance → never trips PLAN-0005 §8.1 / ADR-011 first-real-data trigger). All four venue SDs + dispatch-SD-1 ratified per Cowork rec (SD-1 N=3; SD-2 one-project-per-business-type; SD-3 size/region/maturity enums w/ energy·mid·th-regional·mixed-legacy default; SD-4 "what we refused to share" now required). D4 guarded-trial mirrors ADR-012 D5; regression triggers R-PS1..R-PS4 are the exit criteria; run 1 = energy operator (ADR-005 primary). **Now live-able: Cray launches run-1 (paste the R1-clean seed NOT the one-pager); ADR-011 audit framework stays gated on a partner conversation — the synthetic run INFORMS but never TRIGGERS it.**
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **Procurement vertical — GO + IN MOTION: PLAN-0036 (Fastenal, Stage 1) drafted + merged Draft (#412, `7a7c036`):** **GO** — Cray greenlit the 4th vertical (Procurement) and **PLAN-0036 (Fastenal procurement vertical, Stage 1) is drafted + merged Draft** (#412, head_commit `7a7c036`; Cowork-D1 + Code-R2 + committed D2, session 75). **Cray adjudicated SD-1…SD-5 = confirm-all** (2026-06-24, as-recommended). **Demo target = Fastenal Thailand** — automotive/auto-parts in the EEC; **hero** = asset-failure → governed emergency sourcing, **calm-path** = low-stock reorder. Stage 1 = a **PLAN-only, no-ADR pure-config plugin** on the shipped ADR-016 engine, **zero `services/` core edit** (CQ-1 confirmed, ADR-0023); the **SD-4 catch** = `services/engine/procedures/spec.py` `Step = ConfigDict(extra="forbid")` → Stage-1 facet annotations are **comment-only** (a first-class `facet` field = a Stage-2 ADR-016 amendment). It is the **proving ground** for the ultimate **3-phase generative-procedure platform** (generate / run / monitor); per Rule-of-Three it builds **no generic generator** (hand-author → extract schema Stage 2 → generator Stage 3). **NEXT = a new session flips PLAN-0036 Draft → Ready for execution (SDs confirm-all) then executes Stage 1.** *Supporting de-risk dossier (Cowork, session 72, 2026-06-22, `docs/research/private/`)* — **(1)** `2026-06-22-procurement-spec-expressiveness-probe.md` (procurement is **config-layer**, **0 new core amendments**; only engine pulls are the already-deferred ADR-016 Phase 2 / Phase 4+ items); **(2)** `2026-06-22-procurement-gtm-commercial-validation.md` (wedge = ops-triggered asset-aware procurement; econ buyer = CFO/Controller, champion = ops/procurement mgr; metric = **cycle-time**; ~$40K–150K/yr; 6-wk paid pilot); **(3)** `2026-06-22-procurement-asset-aware-incumbent-scan.md` (de-risk #1 — EAM/CMMS = nearest incumbent on the *trigger* only; white space = the **triple intersection** asset-trigger × governed sourcing × cross-vertical); **(4)** `2026-06-22-ai-sourcing-competitor-teardown.md` (de-risk #2 — Verusen/Keelvar/Fairmarkit/Arkestro/… triple intersection unoccupied; defensibility on **axis (a) asset-event trigger**; watchlist: **Verusen #1**, Fairmarkit, Coupa); **(5)** `2026-06-22-platform-incumbent-deepdive.md` (de-risk #3 — Palantir/Maximo/GE Vernova/SAP = capability-yes / product-no; moat = **packaging × ICP × price** = the **"Palantir-lite"** thesis, ADR-005, **governed ≠ generated**). **Pitch:** lead with asset-ontology-triggered governed sourcing + the native ontology (ADR-008) + engine (ADR-016) combination — **NOT** "governed"/"cross-vertical" (now commoditized claims).
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [ ] **PLAN-0041 (classify-prompt enrichment lever — Rock 1) — RATIFIED + COMMITTED (#461, s84); ready for execution.** The fix for the s83 AC-B5 live finding (~1-in-3 false-abstain on a textbook AT-1/AT-3). Prompt-only: enrich `build_classify_messages` with **per-archetype descriptions** (derived from the canonical catalog) + a **positive band-vs-out-of-scope-gate explainer**, **WITHOUT relaxing the AT-2 cross-check** (`_archetype_disagreement`/`_AT2_ONLY_KINDS`, ADR-0024 D4/D7 — byte-identical; no schema change; no new ADR). **OQ-C twin-metric:** Arm B 11/11 AT-2-abstain HARD gate + a pre-committed pass/fail read; offline Steps 1-4 = the gate, **Step 5 live before/after on MS-S1 = Cray host-state go** (§8). **NEXT = a session executes Steps 1-4 (offline) then the Cray-gated live run.** *(Cowork-D1 → Code-R2 → Cray-ratified → committed #461; PLAN-0040 AC-B5 live finding)*
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
