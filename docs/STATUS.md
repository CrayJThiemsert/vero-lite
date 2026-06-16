---
last_updated: 2026-06-16T08:12:26+07:00
session: 62
current_batch: 'session-62 (second batch) — HARNESS IMPROVEMENT: the AC-9 "plan-first then execute" pattern distilled into durable discipline. code-operational-policy skill gains a plan-first section + /goal-for-verification habit; Lesson #0026 (interpret-before-run); CLAUDE.md §8 "Host-State Actions" + §11 pointer codified Cray-direct (Lesson #5 §2); restart-bridge filed (#334 ba66561, #335 cf958d3). First batch = PLAN-0026 AC-9 live re-verify PASS (#332).'
current_actor: code
blocked_on: 'Nothing blocks Code (PLAN-0026 complete + AC-9 PASS; session-62 harness-improvement batch closed). Held: B-γ baselines, PLAN-002 ≥ADR-014, auditprep SD-4/SD-5/OQ-A + ADR-011 (real-partner gated), partner-sim guarded trial.'
next_action: 'Session-62 harness-improvement batch closed (plan-first discipline skill + Lesson #0026 + host-state rule codified in CLAUDE.md §8). Held (Cray-gated): B-γ baselines, PLAN-002 ≥ADR-014, auditprep SD-4/SD-5/OQ-A + ADR-011 (real-partner gated), partner-sim guarded trial. ADR-0021 (c) = future triggered successor.'
head_commit: cf958d3
recent_commits: [cf958d3, ff687f6, ba66561, fd49c42, affdfb4, cf63ebb, c16778d, dc65425, 8de6be0, 703b1ce]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 62 (second batch, current; head_commit `cf958d3`) — HARNESS
> IMPROVEMENT: the AC-9 "plan-first then execute" pattern distilled into durable
> harness discipline (Cray-directed retrospective).** Cray observed the AC-9
> session went well largely because the prompt said *"plan carefully, then if
> ready, begin"* — but that quality depended on Cray re-typing it, not on the
> harness. Cray selected all four proposed improvements (cost ~0, advisory-first,
> reusing existing machinery — **no new always-on hook**, per the classifier-billing
> / L1-friction lessons). **(1+2+4 — #334 `ba66561`, `docs:`):** the
> `code-operational-policy` skill gains a *"Plan-first for costly / host-state /
> irreversible / multi-step work"* section (read the result-producing code first →
> staged plan + pre-committed pass/fail read → cheapest gate first → run once →
> verify via the Read tool) + a *"use the Axis-B `/goal` loop for verification
> tasks"* sub-section (reuses ADR-0018, no new hook); **Lesson #0026
> (interpret-before-run)** — pre-commit what each outcome MEANS (pass /
> known-acceptable-miss / real failure) before running, generalising the
> green-against-the-wrong-thing failure class (the AC-9 nl-01 false-alarm +
> nl-08/11 false-confidence near-misses it avoided). **(3 + §11 pointer — #335
> `cf958d3`, `docs(constitution):`):** Cray-direct constitutional codification
> (Lesson #5 §2): CLAUDE.md §8 gains a **"Host-State Actions"** subsection homing
> the host-state ASK-Cray binding rule that previously lived only in transient
> PLANs/handoffs (orphaned once PLAN-0026 archived), and §11 gains a plan-first
> pointer to the skill. **Restart-bridge filed** (Lesson #5 §1, gitignored,
> validated OK). The meta-move: turn a good *per-prompt instruction* into a harness
> default so future sessions keep the quality sustainably. **Frontier:**
> harness-improvement batch closed; held items remain (B-γ, PLAN-002 ≥ADR-014,
> auditprep + ADR-011 real-partner-gated, partner-sim). Nothing blocks Code.
> AI-assisted (Claude Code, session 62); no `Co-Authored-By` per CLAUDE.md §7.

> **Session 62 (first batch; head_commit `c16778d`) — PLAN-0026 AC-9 OPTIONAL LIVE
> MS-S1 RE-VERIFY RAN AND PASSED: nl-08/nl-11 CONFIRMED CORRECT ON THE
> DETERMINISTIC STRUCTURED LENS, LIVE.** Cray-authorized host-state run closing
> the one remaining PLAN-0026 open item (the optional live re-verify; the
> offline oracle stays the CI **gate**, AC-9 is **verification, not a gate** —
> Lesson #15 live-vs-mock). The 12-question NL-query harness ran live against
> `gpt-oss:20b` @ MS-S1 (`run_benchmark.py --warm`); the offline oracle
> (`tests/services/engine/test_nl_query.py` + `tests/benchmark/test_nl_query_feasibility_gold.py`)
> was **65 passed** immediately before the run. **Result: 11/12 correct (was
> 10/12 in AC-8) · anti-hallucination 12/12 HELD · latency p50 15.5s / p95 39.0s.**
> **Headline (AC-1 confirmed live):** nl-08 + nl-11 both flipped to **correct on
> the deterministic structured lens** — `result_count 7`, max `96.5 °C`, top
> `Battery Bank A` read from the execute-stage `AggregateResult` (not phrase
> prose). Both AC-8 failure modes are gone live: the model emits `operation:max`
> (not `list`) and does **not** invent a `resolve` placeholder. **Two honest
> notes (kept, not dropped):** (1) the lone miss is **nl-01** — *not* an AC-9
> target — a known filter-omission nondeterminism on a *simple list*; the phrase
> named the 2 real batteries (zero fabrication), it is **out of PLAN-0026 scope**,
> and its offline gold test is green → **not a Phase-A regression**. (2) This run
> reached the right result via the model's own `unit=celsius` filter
> (`measured_kind:null`), so the coherence seam had nothing to rewrite — the
> deterministic seam is the **safety net proven by the offline oracle (AC-7)**,
> not exercised this particular run; both routes yield the identical grounded
> result. **Verdict: AC-9 PASS.** Recorded as an addendum in
> `benchmarks/nl_query_feasibility/RESULTS.md` (#332, `dc65425`; merge `c16778d`);
> the `--dump-json` evidence is gitignored at
> `.claude/benchmark-results/2026-06-16-nl-query-ac9.jsonl`. **Frontier:** AC-9
> done → PLAN-0026 fully closed incl. the optional live re-verify; no gated
> NL-query work remains; ADR-0021 (c) remains a future triggered successor
> (ADR-016 procedure engine + ≥3 verticals); held items (B-γ, PLAN-002,
> auditprep, ADR-011) unchanged. AI-assisted (Claude Code, session 62); no
> `Co-Authored-By` per CLAUDE.md §7.
> _Rotation note: this reconcile rotated both Session-58 Current Focus blocks
> (third batch — NL-query feasibility spike / fork-resolution, head_commit
> `987c2be`; second batch — two backlog quick-wins, head_commit `9595d3e`;
> session 58 falls outside the 4-newest-sessions window {62,61,60,59}) plus the
> oldest Recent Decisions row (2026-06-12 watch-lane ground truth PINNED,
> `1bd6328`) to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md)
> per the STATUS.md Rotation Policy (R2/R4)._
>
> **Session 61 (head_commit `b53e631`) — PLAN-0026 COMPLETE: ADR-0021
> (METRIC-KIND TYPED ONTOLOGY SEMANTICS) AUTHORED→ACCEPTED, THEN PHASE A
> (`measured_kind` enum + `quantity_bindings` + "classify, don't synthesize")
> SHIPPED; PLAN-0026 ARCHIVED to `done/`.** The session opened with #323 MERGED
> (`e93320f`, PLAN-0026 eval tooling + 2026-06-15 RESULTS.md addendum → the
> RESULTS.md citation no longer dangles on main) and a latent handoff-validator
> commit-blocker FIXED (#325, `ea08d88`: `session_md_files` now exempts raw
> `-transcript.md` renders, which carry a `# Transcript —` preamble and **never**
> frontmatter by design — they had falsely blocked every commit; 29 handoff tests,
> 2 new; the good frontmatter format stays enforced). Both were preamble; the
> headline is **PLAN-0026 closed end-to-end** — the principled fix for
> aggregate-superlative kind-word disambiguation Phase B could only approximate.
> **Decision chain (Cray):** Gate-1 (T2-vs-T3 roadmap fork) = **T2** (NL-query is
> the moat wedge to invest in deep); Gate-2 (PLAN-0026 SD-2) = **Path B**
> (kind↔unit binding declared in the ontology → a new ADR). Cross-check confirmed
> **(b) over (c)**: (c) typed-measurement-composite is over-scope now (Rule of
> Three; ADR-008 D3 defers composites to v1; JSONB-vs-deterministic-execute tension
> risks the 12/12 anti-hallucination) and (b) reuses entirely into (c).
> **ADR-0021 ("classify, don't synthesize"):** Cowork-authored the draft (ADR-009
> D1) → Code committed **Proposed** (#327, `a102b9d`) → Cray ratified **Accepted**
> (#328, `4423a22`); construct **(b)** (QUDT-style quantity-kind ⟂ unit typed pair,
> `quantity_bindings`) confirmed over (a) per-enum-value map and (c) composite —
> (c) recorded as a **triggered successor** (revisit when the ADR-016
> procedure/trigger engine needs first-class measurements AND ≥3 verticals exercise
> the path). Amends ADR-008 D3. **Phase A (PLAN-0026 steps 6–7, #329 `37f62a7`;
> commits `bcbb62d` step 6 + `7f72181` step 7):** *Step 6* — `measured_kind` enum
> (temperature|frequency) + object-level `quantity_bindings` (temperature→celsius,
> frequency→hz) on OperationalEvent in the energy ontology; `quantity_bindings`
> admitted by `ontology_schema.json` (amends ADR-008 D3) + parsed into
> `ontology_meta` (QuantityBinding); synthetic data tagged (7 temperature /
> 2 frequency / 2 none); `vero-lite generate` emits `measured_kind` across all 5
> artifacts; a D6 L2 validator check (kinds ∈ enum, bound once); ORM
> (`services/db/models.py`) + Alembic `0003` add the column (DB↔generated-DDL
> parity, caught by `test_schema_parity`). *Step 7* — `StructuredQuery.measured_kind`:
> the translate LLM **classifies** the bounded kind; the coherence seam
> **synthesizes** the precise `unit` filter from the binding, **superseding
> Phase B's best-effort dominant-unit** (PLAN-0026 IN-1). Backward-compat: no
> classified kind → dominant-unit fallback; a classified kind whose bound unit is
> absent → clarify (never fabricate). The win: distinguishes "highest **frequency**"
> from "highest temperature" that Phase B's dominant heuristic could not. **Verified:
> full suite 1535 passed / 22 skipped; ruff + ruff-format + mypy clean; 12/12
> anti-hallucination preserved; the offline oracle re-pointed to feed a classified
> `measured_kind` (not inferred); 6 new tests (4 engine + 2 validator).**
> **PLAN-0026 → `done/`** (#330, `0a1427e`/`b53e631`) — both phases shipped,
> archived per Plan Flow. **Frontier:** no gated NL-query work remains; ADR-0021 (c)
> is a future triggered successor; held items (B-γ, PLAN-002, auditprep, ADR-011)
> unchanged. AI-assisted (Claude Code, session 61); no `Co-Authored-By` per
> CLAUDE.md §7.
> _Rotation note: this reconcile replaced the prior session-61 CF block (#323/#325)
> with the comprehensive PLAN-0026-COMPLETE narrative, and rotated all four
> Session-57 CF blocks (fifth/fourth/third/second batches — head_commits `e09af9b`
> / `2331ffb` / `f1cf3b4` / `4c46a92`; session 57 falls outside the 4-newest-sessions
> window {61,60,59,58}) plus the oldest Recent Decisions row (2026-06-12 Lessons
> #24 + #25, `4b0e306`) to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md) per
> the STATUS.md Rotation Policy (R2/R4)._
>
> **Session 60 (head_commit `19eeb21`) — PLAN-0026 (NL-QUERY AGGREGATE
> METRIC-SEMANTICS) AUTHORED + RATIFIED + MERGED (#321), THEN PHASE B
> (DETERMINISTIC REWRITE SEAM) MERGED (#322).** Closes the one residual NL-query
> failure PLAN-0024 left open: **filter-omission on aggregate superlatives** (the
> spike's nl-08 / nl-11). **Diagnosis (Cray-directed):** two MS-S1 host-state
> experiments both came back NEGATIVE — a **4-model sweep** (gpt-oss:20b /
> nemotron-3-nano:30b / qwen3.6:35b / gemma4:26b all dropped the implied filter;
> larger models 2.5–6× slower, gemma4 worst) and a **3-variant prompt escalation**
> (general rule no-op; units rule regressed; near-answer few-shot = teaching-to-test).
> Corrected diagnosis: the model drops the implied `unit=celsius` filter AND
> `group_by`; `value 96.5` was right only by luck (hz readings < 96.5); "top" was
> phrase prose, not the structured aggregate. Two external LLMs (Cray-consulted)
> independently converged: this is a **typed-query-on-untyped-metric / data-model
> problem**, not a model/prompt problem. **PLAN-0026 (two-layer, phased).**
> Governance chain (clean): Cray chose "governed-first" → the in-harness
> `plan-drafter` Write was G2-denied → **Cowork (Tier-1, ungated) authored the
> PLAN** → Code committed it (#321, ADR-009 D2) → Cray ratified Proposed→Accepted
> (SD-1 resolved = add the outcome enum). **Phase B (engine, deterministic,
> offline-validatable) ships first; Phase A (ontology `measured_kind` enum) is
> GATED** on the T2-vs-T3 roadmap call + its ADR (SD-2). **Phase B (#322,
> `19eeb21`):** a post-translate **rewrite seam** in `services/engine/nl_query.py`
> — `group_by` inference for "which/on-which <entity>" superlatives (AC-2,
> reshape-only → never a false no-data) + a **heterogeneous-aggregate coherence
> rewrite** that composes the dominant-unit filter in the engine (AC-3; the model
> never re-supplies it = the v2 regression) + a **clarify-not-silent-no-data
> guard** (AC-4) + **`NlAnswer.outcome: Literal["answered","no_data","clarify"]`**
> (SD-1, Cray-approved). The decisive **offline oracle** feeds the model's
> known-bad `{filters:[], operation:max, group_by:null}` and asserts the seam
> rewrites to `result_count==7`, aggregate `value 96.5`, `top "Battery Bank A"`
> (nl-08 + nl-11) in the structured receipt, NOT phrase-rescued. **Full suite 1527
> passed / 22 skipped; ruff + mypy clean; anti-hallucination 12/12 preserved
> (AC-5).** An L1 loop-detect was hit twice during the multi-edit implementation;
> resolved via a WIP-scaffolding commit (counter reset, not a Bash circumvention)
> + a justified `# noqa: C901` on `answer_question` (orchestrator; each stage is a
> named helper) when the edit-cap left no room to extract further. **Honest
> limitation (Phase B):** the coherent-unit pick is the **dominant unit in the
> matched data**, not the question's kind word — passes nl-08/nl-11 (temperature =
> dominant) but wouldn't distinguish "highest frequency"; **Phase A
> (`measured_kind`) is the principled fix** (gated). PLAN-0026 stays ACTIVE (not
> `git mv`'d to `done/`) — Phase A is still pending. **Open threads:** PR #323
> MERGED (`e93320f`; eval tooling + the 2026-06-15 RESULTS.md addendum — the
> evidence base PLAN-0026 cites; the dangling-on-main reference is now resolved);
> SD-2 ADR (amend
> ADR-008 vs new ADR-0021 — Cowork leaned new; route Cowork to author) gates Phase
> A impl; SD-3 (benchmark scoring) closed = no gold reclassification needed (gold
> already carried the structured expectations Phase B now lands); AC-9 optional
> live MS-S1 re-verify available on Cray's go; a Cowork pattern article
> (gitignored `docs/research/private/2026-06-15-ontology-metric-semantics-pattern.md`,
> "the typed semantic layer is the moat") exists untracked (Cray may decide).
> AI-assisted (Claude Code, session 60); no `Co-Authored-By` per CLAUDE.md §7.
> _Rotation note: this reconcile rotated the oldest Current Focus block (Session 57
> "watch-lane GROUND TRUTH PINNED on all 39 watch items", head_commit `1bd6328`)
> and the oldest Recent Decisions row (2026-06-12 Stop classifier switched to local
> `gpt-oss:20b`, `3375778`) to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md) per
> the STATUS.md Rotation Policy (R2/R4)._
>
> **Session 59 (head_commit `f4aa7fe`) — PLAN-0024 (NL-QUERY T2 ENGINE
> ENRICHMENT) DRAFTED + COMMITTED + EXECUTED (#316 plan / #317 engine).** The
> engine half of the Cray-ratified T2 (NL-query) wedge: the session-58 spike
> resolved the partner-trial fork to T2 and named the build; session 59 built
> it. Engine-only — UI deferred to PLAN-0025. Two pieces:
> **(1) `StructuredQuery` enrichment** (`services/engine/nl_query.py`): `operation`
> gains `max/min/avg/sum` (+ optional `group_by`), computed in the
> **deterministic execute stage** (like `count`) and carried in a new
> `NlAnswer.aggregate` grounding receipt — **never** delegated to the phrase LLM
> (the spike showed phrase-rescue is brittle). nl-08 (max 96.5) / nl-10 (avg 41.3)
> now pass via deterministic compute. A `NameResolve` descriptor adds cross-type
> name→id resolution (resolve-then-filter; `object_type` stays single +
> enum-constrained) so "events for Battery Bank A" works (nl-09 = 5; nl-11 hottest
> = Battery Bank A); group keys are relabelled id→title so the answer names the
> entity. **(2) Translate prompt fix**: require the implied filter (kills the
> whole-table fetch — the #1 spike error) + exact enum/value grounding ("celsius"
> not "C"). **Anti-hallucination (AC-5, the hard gate) preserved:** empty match,
> aggregate-over-no-numeric, and unresolved-name all short-circuit to the
> deterministic no-records answer (phrase LLM never called). The gold set's 4
> ceiling cases (nl-08/09/10/11) moved off phrase-rescue onto the deterministic
> **structured-result lens** (executed result + `expected_aggregate`); harness
> `score_case` gained `_aggregate_ok`. **11 new offline tests; full suite 1511
> passed / 22 skipped (was 1481/22, +30); ruff + mypy clean.**
> **Governance chain (clean):** Cray scoped the build (engine-only; SD-1 deferred;
> UI→PLAN-0025) via AskUserQuestion → the in-harness `plan-drafter` authored
> PLAN-0024 (ADR-013 D1) → the **ungated Cowork tier placed the PLAN file** after
> the G2 PreToolUse gate denied every in-harness Code write (subagent ×2 + main
> agent ×1, even with explicit approval — the "Cowork authors, Code commits" path)
> → Code committed it (#316, ADR-009 D2) → Cray reviewed + merged → Code executed
> Steps 1-6 (#317). **SD-1** (name→id mechanism) implemented as the recommended
> **pre-step** (Cray deferred the decision to execution). Execution hit an L1
> loop-detect (6 edits to one file = the code threshold) — resolved by collapsing
> the remainder into one full-file Write after a Cray-approved counter reset; no
> Bash circumvention.
> AI-assisted (Claude Code, session 59); no `Co-Authored-By` per CLAUDE.md §7.
> _Rotation note: this reconcile rotated the oldest Current Focus block (Session 56
> sixth batch — Lessons #24 + #25, head_commit `4b0e306`) and the oldest Recent
> Decisions row (2026-06-12 Stop-classifier calibration arc, `246ee0a`) to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md) per
> the STATUS.md Rotation Policy (R2/R4)._
>
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
| 2026-06-16 | **PLAN-0026 AC-9 optional live MS-S1 re-verify RAN + PASSED (#332, `dc65425`/`c16778d`, session 62)** — Cray-authorized host-state run closing the last PLAN-0026 open item; offline oracle stays the CI gate, AC-9 is verification-not-gate (Lesson #15). 12-Q NL-query harness vs `gpt-oss:20b` @ MS-S1 (`run_benchmark.py --warm`), offline oracle 65 passed immediately prior. **Result: 11/12 correct (was 10/12 in AC-8) · anti-hallucination 12/12 HELD · p50 15.5s / p95 39.0s.** Headline (AC-1 live): nl-08 + nl-11 both flipped correct on the deterministic structured lens (`result_count 7`, max `96.5 °C`, top `Battery Bank A` from the execute-stage `AggregateResult`, not phrase prose) — model emits `operation:max` not `list` and invents no `resolve` placeholder. Two honest notes: (1) lone miss = nl-01 (not an AC-9 target) — known simple-list filter-omission nondeterminism, zero fabrication, out of PLAN-0026 scope, offline gold green → not a Phase-A regression; (2) this run hit the right result via the model's own `unit=celsius` filter (`measured_kind:null`) so the coherence seam had nothing to rewrite — the seam is the safety net proven by the offline oracle (AC-7), both routes yield the identical grounded result. **Verdict: AC-9 PASS.** Recorded as a RESULTS.md addendum; `--dump-json` evidence gitignored at `.claude/benchmark-results/2026-06-16-nl-query-ac9.jsonl`. PLAN-0026 now fully closed incl. the optional live re-verify | `c16778d` (#332, content `dc65425`) / `benchmarks/nl_query_feasibility/RESULTS.md` |
| 2026-06-15 | **PLAN-0026 COMPLETE — ADR-0021 (metric-kind typed ontology semantics) AUTHORED→ACCEPTED then Phase A (`measured_kind`) SHIPPED; PLAN archived to `done/` (#327–#330, `b53e631`, session 61)** — closes PLAN-0026 end-to-end (the principled fix Phase B could only approximate). Cray decisions: Gate-1 = **T2** (NL-query is the moat wedge), Gate-2/SD-2 = **Path B** (kind↔unit binding in the ontology → a new ADR); cross-check confirmed **(b) over (c)** ((c) over-scope now per Rule of Three + ADR-008 D3, and (b) reuses entirely into (c)). **ADR-0021 ("classify, don't synthesize"):** Cowork-authored (ADR-009 D1) → Code committed Proposed (#327, `a102b9d`) → Cray ratified Accepted (#328, `4423a22`); construct **(b)** QUDT-style quantity-kind ⟂ unit typed pair (`quantity_bindings`) over (a) per-enum-value map and (c) composite; (c) is a **triggered successor** (ADR-016 procedure engine + ≥3 verticals); amends ADR-008 D3. **Phase A (steps 6–7, #329 `37f62a7`; `bcbb62d`+`7f72181`):** step 6 — `measured_kind` enum (temperature|frequency) + object-level `quantity_bindings` on OperationalEvent, admitted by `ontology_schema.json` + parsed into `ontology_meta`, synthetic data tagged (7/2/2), emitted across all 5 artifacts, D6 L2 validator check, ORM + Alembic `0003` column (DB↔DDL parity via `test_schema_parity`); step 7 — `StructuredQuery.measured_kind` (translate LLM **classifies** the kind, the coherence seam **synthesizes** the precise `unit` from the binding, **superseding** Phase B dominant-unit per IN-1; no kind → dominant fallback, classified-but-absent → clarify, never fabricate). Distinguishes "highest frequency" from "highest temperature". Suite 1535/22; ruff+ruff-format+mypy clean; 12/12 anti-hallucination preserved; offline oracle re-pointed to a classified `measured_kind`; 6 new tests (4 engine + 2 validator). PLAN-0026 → `done/` (#330, `0a1427e`/`b53e631`). No gated NL-query work remains | `b53e631` (#327/#328/#329/#330) / `docs/adr/0021-metric-kind-typed-ontology-semantics.md` + `services/engine/nl_query.py` + `docs/plans/done/0026-nl-query-aggregate-metric-semantics.md` |
| 2026-06-15 | **PLAN-0026 (NL-query aggregate metric-semantics) AUTHORED+RATIFIED+MERGED (#321) then Phase B (deterministic rewrite seam) MERGED (#322, `19eeb21`, session 60)** — closes the filter-omission-on-aggregate-superlative gap PLAN-0024 left open (nl-08/nl-11). Diagnosis (Cray-directed): a 4-model MS-S1 sweep + a 3-variant prompt escalation both NEGATIVE → it's a typed-query-on-untyped-metric data-model problem, not model/prompt (two external LLMs concurred). Phase B = a post-translate rewrite seam in `nl_query.py`: `group_by` inference for "which <entity>" superlatives (AC-2, reshape-only) + a heterogeneous-aggregate coherence rewrite composing the dominant-unit filter in the engine (AC-3, model never re-supplies it = v2-regression-proof) + a clarify-not-silent-no-data guard (AC-4) + `NlAnswer.outcome: Literal["answered","no_data","clarify"]` (SD-1, Cray-approved). Offline oracle feeds the model's known-bad `{filters:[], operation:max, group_by:null}` and asserts the seam → `result_count==7`, value 96.5, top "Battery Bank A" structurally (not phrase-rescued). Suite 1527/22; ruff+mypy clean; anti-hallucination 12/12 preserved (AC-5); one `# noqa: C901` justified on the orchestrator. Governance: Cray "governed-first" → `plan-drafter` G2-denied → Cowork (ungated) authored → Code committed #321 → Cray ratified Proposed→Accepted → Phase B #322. Phase A (`measured_kind` ontology enum, the principled kind-word fix) GATED on the T2-vs-T3 roadmap call + SD-2's ADR; PLAN stays ACTIVE (not `done/`) | `19eeb21` (#321/#322) / `services/engine/nl_query.py` + `docs/plans/0026-nl-query-aggregate-metric-semantics.md` |
| 2026-06-15 | **PLAN-0024 (NL-query T2 engine enrichment) SHIPPED — engine half of the T2 wedge (#316 plan / #317 engine, `f4aa7fe`, session 59)** — `StructuredQuery` gains `max/min/avg/sum` (+ optional `group_by`) computed in the deterministic execute stage + a new `NlAnswer.aggregate` grounding receipt (never the phrase LLM), plus a `NameResolve` cross-type name→id descriptor (resolve-then-filter; `object_type` stays single/enum-constrained, group keys relabelled id→title); translate prompt now requires the implied filter + exact enum grounding. Gold ceiling cases nl-08/09/10/11 moved onto the deterministic structured-result lens (`_aggregate_ok`). Anti-hallucination AC-5 preserved (empty/no-numeric/unresolved short-circuit to no-records). 11 new offline tests; suite 1511/22 (+30); ruff+mypy clean. Governance: Cray scoped engine-only (UI→PLAN-0025, SD-1 deferred) → `plan-drafter` authored PLAN-0024 → ungated Cowork placed the file (G2 denied all in-harness Code writes) → Code committed #316 → merged → Code executed #317; SD-1 done as the recommended pre-step; one L1 loop-detect resolved by a Cray-approved counter reset, no Bash | `f4aa7fe` (#316/#317) / `services/engine/nl_query.py` + `docs/plans/done/0024-nl-query-t2-engine-enrichment.md` |
| 2026-06-14 | **Two backlog quick-wins SHIPPED (Code-solo, #311 + #312, `9595d3e`, session 58)** — cleared after the audit-framework arc closed; a separate small harness-tooling batch. **#311** (`f2ee579`, `test(stop-classifier):`): 3 "dispatch discriminator" gold cases added to `benchmarks/stop_classifier/gold.yaml` (20→23) pinning the surfaced-vs-ratified distinction the local classifier got wrong in s57 (over-fired `plan-drafter` on ADR/PLAN mentions while formality was a PENDING Cray decision — 2 cases) and right in s58 (post-ratification dispatch correct); 2 `pause` negatives + 1 `dispatch` positive, safety-weighted (spurious dispatch = HARD FAIL); offline test green (4 passed); live re-score pending Cray go; RESULTS.md addendum (recorded 2026-06-12 run predates the cases). **#312** (`9595d3e`, `fix(handoffs):`, PLAN-004 Phase B): handoff-validator warning-swallow bug fixed — `_schema.py::_build()` discarded its `errors` list on the otherwise-valid path so `_check_unknown()` WARNINGs were unreachable; `Frontmatter` gains `warnings`, `validate_file()` surfaces it, CLI prints it (precommit unchanged); regression tests strengthened; `tests/handoffs/` 573 passed / 2 skipped; ruff + mypy clean | `9595d3e` (#311/#312) / `benchmarks/stop_classifier/gold.yaml` + `tools/handoffs/_schema.py` |
| 2026-06-14 | **PLAN-0023 (PDPA RoPA-lite, step-2 of audit-framework-prep) SHIPPED (#308 PLAN + #309 deliverables, `afea6b3`, session 58)** — two tracked deliverables: reusable RoPA-lite template (`docs/conventions/partner-ropa-lite.md`, canonical) + NPD synthetic example (`docs/strategy/public/partner-sim-run1-ropa-example.md`, SYNTHETIC), each RoPA slot annotated with a data-quality/lineage hook; example's DSR/lineage→ADR-011 section maps 4 gaps→implications (PII-in-free-text→log-by-reference; scattered actor identity→actor unification; PK reuse + NTP drift→lineage/valid-from + ordering; under-recording→completeness-not-assumed). Governance: Cray ratified PLAN formality (3 decisions) → `plan-drafter` subagent authored PLAN-0023 (ADR-013 D1) → Code committed (#308, ADR-009 D2) → Code executed deliverables Code-direct (#309); PLAN archived to `done/`. SD-1 kept (AC-6 in-PLAN). ADR-011 still gated on a real partner — synthetic run INFORMS but never triggers PLAN-0005 §8.1 (ADR-0020 R3). Carried open: SD-4/SD-5/OQ-A | `afea6b3` (#308/#309) / `docs/conventions/partner-ropa-lite.md` + `docs/strategy/public/partner-sim-run1-ropa-example.md` |
| 2026-06-13 | **ADR-0020 (partner-sim venue) RATIFIED Proposed→Accepted (#302, `4d1347b`, session 57)** — Cray ratified in-session ("เอาตาม Cowork ทุกข้อ"); all four venue SDs + dispatch-SD-1 accepted per Cowork rec (Cowork-authored fold per ADR-009 D1, Code R2-reviewed + committed). SD-1 N=3 (→D2/R2); SD-2 one-project-per-business-type (→D4; R-PS4 reframed as a guard); SD-3 size/region/maturity enums + run-1 default energy·mid·th-regional·mixed-legacy (→D3 input); SD-4 "what we refused to share" ratified-required (→D3 output). R1/R2/R3 substance unchanged (#300 errata settled those). Instruction file reconciled same PR (6 ratification-pending markers → ratified; Code-amends-conventions, ADR-009 D2). dispatch-SD-1 (gitignored): one-pager sector-callout forbidden-action note trimmed, R1-clean seed untouched. Venue now ACCEPTED guarded-trial (R-PS1..R-PS4) — live action is Cray's (launch energy run-1) | `4d1347b` (#302) / `docs/adr/0020-partner-sim-venue.md` + `docs/conventions/partnersim_project_instructions.md` |
| 2026-06-13 | **ADR-0020 (synthetic design-partner simulation venue, partner-sim) committed Proposed (#297, `e25281d`, session 57) + project system instruction landed (#298, `e387a63`)** — a specialist Cowork project that role-plays a Thai operator + emits a "partner profile package" so the intake+PDPA pipeline is rehearsed before a real partner. D1 venue OUTSIDE governance tiers (no commits / no repo mount / enters via Code receive); D2 three BINDING anti-circularity rules (R1 feed-questions-not-schema, R2 forced messiness, R3 SYNTHETIC provenance — never trips PLAN-0005 §8.1 / ADR-011 first-real-data trigger); D3 reuses completion-handoff schema (no enum change); D4 guarded-trial (mirrors ADR-012 D5) + R-PS1..R-PS4. SD-1..SD-4 recommendations only. **Awaits Cray ratification (Proposed→Accepted + SD-1..SD-4) before the project goes live (ADR-0020 T3).** Author≠reviewer (ADR-012 D4.3): Cowork authored, Code R2-reviewed + committed both | `e25281d` (#297) + `e387a63` (#298) / `docs/adr/0020-partner-sim-venue.md` + `docs/conventions/partnersim_project_instructions.md` |
| 2026-06-12 | **B-6 hyphen-normalization grader change RATIFIED + SHIPPED (#295, `2331ffb`, session 57)** — Cray ratified in-session; `grader.py` `normalize_primary_key()` folds the Unicode hyphen/dash family (U+2010–U+2014, U+2212) → ASCII `-` on both sides of the two primary-KEY comparisons only; free-text untouched. Offline dump replay vs the 2026-06-12 scored run: β 118/120 → 119/120, EXACTLY one flip (energy-007, zero collateral); aqua-028 still fails. Same measurement-correctness class as the 2026-06-08 items; no bar moves; REPORT.md dated addendum | `2331ffb` (#295) / `benchmarks/procedure_baseline/grader.py` |
| 2026-06-12 | **First SCORED watch-lane run RECORDED — watch 97.4% (38/39); M-2=b arc COMPLETE (#288, `4c46a92`, session 57)** — `gpt-oss:20b`/MS-S1, 198 items, 318 calls, 0 errors, dump-VERIFIED (39/39 `watch_graded:true`); first production `run_detached.sh` run (sentinel as designed; watcher Monitor died silently + one false alarm — truth via content-based test). Aqua + energy 13/13; supply 12/13 — sole FAIL supply-040 (reroute @1.0 on an in-spec 7.8 °C) = `forbidden_keywords` discriminating as designed. β 98.3% (same two known misses; energy-007 U+2011 now ×3 → strengthens B-6). SD-2 p95 30.18s = +0.18s nominal, within the ±10s straddle band + classifier-contaminated; no bar moves (B-6) | `4c46a92` (#288) / `benchmarks/procedure_baseline/REPORT.md` |

## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13 (ratified `4d1347b`, #302; committed Proposed `e25281d`, #297 + instruction `e387a63`, #298 + R1 errata `655344d`, #300) — guarded trial under observation (parallel to ADR-012). A specialist Cowork project role-plays a Thai operator and emits a "partner profile package" to rehearse the intake+PDPA pipeline before a real partner; venue OUTSIDE the governance tiers (no commits / no repo mount / enters via Code receive). Three BINDING anti-circularity rules R1/R2/R3 (R3 SYNTHETIC provenance → never trips PLAN-0005 §8.1 / ADR-011 first-real-data trigger). All four venue SDs + dispatch-SD-1 ratified per Cowork rec (SD-1 N=3; SD-2 one-project-per-business-type; SD-3 size/region/maturity enums w/ energy·mid·th-regional·mixed-legacy default; SD-4 "what we refused to share" now required). D4 guarded-trial mirrors ADR-012 D5; regression triggers R-PS1..R-PS4 are the exit criteria; run 1 = energy operator (ADR-005 primary). **Now live-able: Cray launches run-1 (paste the R1-clean seed NOT the one-pager); ADR-011 audit framework stays gated on a partner conversation — the synthetic run INFORMS but never TRIGGERS it.**
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten (full table: PLAN-0005 §8.1): rule-based recommender → **ADR-010 ACCEPTED (2026-05-22) → PLAN-0006 next** (LLM reasoning hook); minimal approval gate → **ADR-011+** (audit framework — trigger: first design-partner data / PDPA review); no mapping layer → **dbt/SQLMesh** (trigger: first non-synthetic source); hand-authored ORM → **"ORM emitter"** Rule-of-Three candidate (trigger: 3rd vertical / DDL↔ORM parity-test drift); base Postgres only → **PLAN-002** (pgvector/AGE — trigger: semantic + graph features); explicit registry → **ADR-006 D3 L2** (trigger: vertical #2/#3 or `new-vertical` generator). *(per Cray note 2026-05-21)*
- [ ] **Phase-enum amendment** — add `consultation` (or equivalent Q&A-round value) to canonical Phase enum (Q15 of `2026-05-20-0245-code-plan003-pre-draft-consultation-reply.md`); requires touching `tools/handoffs/_schema.py` + `docs/conventions/handoff-frontmatter-schema.md` + validator tests; PLAN-004 Phase B adjacent. *(Deferred per R-9, 2026-05-20)*
- [ ] **Cleanup stale `ontology/README.md`** — 2026-05-05 PLAN-001 artifact; ontology directory canon now lives at `verticals/<name>/ontology/<name>_v0.yaml` per ADR-006 D1 / ADR-008 D5; superseded by PLAN-003. *(Deferred per R-9 cohort, 2026-05-20)*
- [ ] **PLAN-004 Phase B/C — DEFERRED (backlog, post-PLAN-003):** validator-scope exclusion (`README.md` / `_rename-map.md`, manifest §4.2/§6.1) + Cat G `references_*` autofix + Phase C handoff dashboard + OQ-2 systemic candidate (effective-vs-authored `status:` / archival flag so dead handoffs don't surface as actionable in the dashboard) + **validator warning-swallow bug** — `tools/handoffs/_schema.py` `_build()` (lines ~302–306) returns `Frontmatter` and discards its local `errors` list when no hard error exists, so `_check_unknown()` WARNING-severity findings (e.g. unknown field `brief-number`) are unreachable on otherwise-valid files; fix to surface warnings + add a regression test *(found 2026-05-22 dog-fooding the 4 Cowork LLM-hook handoffs; Cray routed → Phase B)*
- [ ] **ADR-NN (TBD, ≥ ADR-014) + PLAN-002** — Custom Postgres image with extensions (ADR-011 earmarked for the audit framework, ADR-012 taken, ADR-013 taken by autonomy axis relocation; floor bumped from ≥0013 to ≥0014 on 2026-05-23 per ADR-013 T6)
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (low priority)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)

## Next Steps

1. **PLAN-0005 §8.1 revisit register** — remaining deferred-foundational simplifications at their batch boundaries (audit framework → ADR-011+, mapping layer, ORM emitter, base-Postgres → PLAN-002 (≥ADR-014), registry discovery).
2. **Partner-trial readiness gaps** — `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` awaits a dedicated Cray discussion.
3. **Deferred (backlog)** — PLAN-004 Phase B (validator-scope exclusion; Cat G `references_*` autofix; validator warning-swallow bug) + Phase C (handoff dashboard); PLAN-002 custom Postgres image (≥ADR-014).
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
