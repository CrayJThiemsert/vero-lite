# STATUS.md rotation archive — 2026 H1 (from 2026-06-10)

Rotated out of `docs/STATUS.md` per the **STATUS.md Rotation Policy (R1-R6)**
(`docs/runbooks/memory-architecture.md`, Lesson #23). Two sections per R4:
rotated Current Focus blocks and rotated Recent Decisions rows, newest at top,
each tagged with its rotation date. This file opens the `YYYY-hN-status.md`
naming scheme early: the prior archive (`2026-h1-current-focus.md`, sessions
<=46, ratified as-is) is 242 KB — past the ~192 KB R4 split bar — so new
rotations start here rather than appending. Tier-3: grep + windowed reads only.

---

## Rotated Current Focus blocks (rotated 2026-06-10)

_Addendum — rotated 2026-06-21 (session-71 reconcile): the **Session-66 `e5f9774`** CF block (PLAN-0028 Step 5 RAN + VERIFIED; PLAN-0029 whitespace calibration minted + implemented; canonical B-γ numbers locked) fell outside the 4-newest-sessions window when the session-71 PLAN-0034 ratify+implement block landed (Current Focus 8-block cap, R2)._

> **Session 66 (head_commit `e5f9774`) — PLAN-0028 Step 5 RAN + VERIFIED;
> PLAN-0029 (entity-key whitespace calibration) minted + implemented; canonical B-γ
> numbers locked.** Building on session 65's offline Step 2/3 (#350 — the data-driven
> harness + the aquaculture/supply_chain corpora), this session got the Cray
> host-state go and ran **PLAN-0028 Step 5** — the ONE combined scored sweep
> (`gpt-oss:20b` @ MS-S1, warm-first, 80 breach items = 40 aquaculture + 40
> supply_chain, serialized in one warm window via a `systemd-run --user` unit, ~18
> min, **0 errors / 0 invalid SQL**). Every score traced to a real model verdict via
> the Read tool (session-46 confirm-don't-infer). **Cross-vertical finding
> (Cray-ratified framing):** arm (c) **lean RAG ties arm (a) governed on BOTH new
> verticals** (canonical **100% / 100%** post-calibration), while arm (b) **raw
> text-to-SQL swings 0% (aquaculture) ↔ 100% (supply_chain)** — the swing is
> **evidence FOR the moat, not a bug**: the explanatory variable is **semantic
> distance** between the NL question and the physical schema (supply_chain breach = a
> clean numeric threshold raw SQL nails; aquaculture breach hides meaning in a
> free-text `description` + a named pond subtype raw SQL must guess → 0 rows). arm (c)
> is robust because the corpus carries the mapping ("ontology in prose"); the governed
> stack declares it once. **OQ-2 answered: the arm-c≈arm-a tie REPLICATES.** **The
> single aquaculture arm-c miss (aqua-h06) was a grader MEASUREMENT artifact** — the
> model named the right pond `pond-A116` with a **U+202F NARROW NO-BREAK SPACE**
> separator the hyphen-only `normalize_primary_key` didn't recover. Under Cray's
> **universality** criterion the fix split two ways: **(1) PLAN-0029** (small, offline)
> — extend the B-6 calibration to fold the whitespace-separator family
> ({U+0020,U+00A0,U+2007,U+202F,U+2060} → ASCII `-`, recover-only / never-invent) + an
> **offline re-grade** of the stored dumps (no host-state); **(2) the product
> entity-trust gap** (`recommender._compose_llm_record` trusts model-emitted entity
> PKs verbatim, no resolution against the declared object universe) = the **real
> universality investment**, routed OUT → a future **ADR + PLAN-0030** (design-first).
> PLAN-0029 was **minted #352** — the **G2 boundary blocked both the in-harness
> plan-drafter AND Code** from writing a new PLAN (G2 ≠ G1, no in-context-approval
> release; **Cowork authored on Desktop, Code committed** via a `docs/*` chore PR) —
> then **implemented #353** (`feat(benchmarks)`): the whitespace fold + 4 regression
> tests + the offline re-grade harness (`benchmarks/procedure_comparison/regrade.py`).
> **Re-grade VERIFIED via Read:** **exactly one** flip (aqua-h06) → aquaculture arm-c
> **39/40 → 40/40**; supply_chain unchanged 40/40; arm (b) whitespace-invariant by
> construction (not re-gradable from the dump → carried forward). Gate green: ruff +
> mypy clean, `tests/benchmark` **151 passed** (+4). **Step 6 B-3 REPORT cross-vertical
> extension SHIPPED (#355)** — canonical tables + OQ-1/OQ-3 disclosures +
> threats-to-validity → **PLAN-0028 COMPLETE end-to-end**. **Frontier (next session,
> Cowork-routed; see the session-66 closeout handoff `…1405…`):** the
> PLAN-0028/0029 status-flips + done-moves (Cowork, G1) and the ADR/PLAN-0030 +
> vertical-#3 research (Cowork-routed). Nothing blocks Code. AI-assisted (Claude Code,
> session 66); no `Co-Authored-By` per CLAUDE.md §7.

_Addendum — rotated 2026-06-20 (session-71 reconcile): the **Session-64 `0aee4eb`** CF block (B-γ executed end-to-end — PLAN-0027 Steps 2–5 SHIPPED; PLAN-0019 Step B-γ / AC B-3 DONE) fell outside the 4-newest-sessions window {71, 69, 67, 66} when the session-71 PLAN-0033 Phase C closeout block landed._

> **Session 64 (head_commit `0aee4eb`) — B-γ EXECUTED END-TO-END:
> PLAN-0027 Steps 2–5 SHIPPED; PLAN-0019 Step B-γ / AC B-3 = DONE.** This session
> read the session-63 handoff and ran PLAN-0019's last open step (the three-arm
> comparison on the energy breach subset) to completion. **Offline arms (#339
> `e41806a`/`a394342`, Steps 2–3):** arm (b) **raw text-to-SQL** + arm (c)
> **lean RAG** + the comparison harness, all built behind a **mock-ChatClient
> offline gate** (D-6 contamination guard intact — arm c stays a clean naive RAG
> baseline). **ONE Cray-approved scored host-state run** (`gpt-oss:20b` on MS-S1,
> 40 energy breach items, warm-first; **every score VERIFIED from `--dump-json`
> via the Read tool**, reports-not-gates per B-3/B-6), then the **B-3 REPORT**
> landed (#342 `0aee4eb`/`01370e5`, Step 5). **Scored results:** arm (a)
> governed-procedure stack **97.5–100%** entity+action (REUSED from REPORT, D-2 —
> NOT re-run; p95 ~30s/judgment); arm (b) raw text-to-SQL **100% entity-ID** (40/40,
> correct `WHERE measured_value >= 90` threshold join) but **structurally cannot
> propose an action** (D-3; p95 10.2s); arm (c) lean RAG **97.5% entity+action**
> (39/40; action 100%; p95 3.2s). **0 errors / 0 invalid SQL.** The one arm-c miss
> (`energy-h05`) is a real naive-RAG output-fidelity miss (emitted non-canonical
> `E113`, not the ontology key `asset-E113`), VERIFIED — not a grading artifact.
> **The load-bearing finding:** raw entity+action accuracy does **NOT** separate
> the governed stack from lean RAG (arm c ties arm a at 97.5%) → this **relocates
> the moat claim** off "raw NL→action accuracy" and onto the **governance layer**
> (the §3.4 verify+reshape / deterministic disposition / handler allowlist / audit
> narrative arm c structurally lacks). The **verify+reshape enhancement** is
> captured as a forward-pointer (future ADR-016 area), OUT OF SCOPE for B-γ per the
> D-6 contamination guard. **Two supporting PRs:** **#340** (`099d55b`/`17863ef`,
> `test(handoffs):`) — the spun-off chip-session fix isolating `CLAUDE_GOAL_PATH`
> in the `stub_env` fixture so a developer's live `.claude/state/goal.json` can't
> leak into the Phase-2 Stop-hook integration tests (test-only +6 lines; handoffs
> suite 575 passed / 2 skipped; before/after repro: PR head + active goal PASSES,
> main FAILS with goal-gate dispatch); **#341** (`cf645f7`/`7d8a716`,
> `fix(benchmarks):`) — the pre-run measurement-correctness calibration
> (case+hyphen-normalize the arm-c free-text entity match, **ratified BEFORE the
> scored run** per B-6; only recovers a correctly-named entity, never invents one).
> **Concurrent-session recovery handled:** the chip session ran in the SHARED WSL
> checkout; after #339 merged, local-main vs origin diverged + a transient
> `.git/index.lock` appeared — diagnosed read-only (nothing lost: origin/main
> correct, chip work pushed) then synced cleanly (the shared-worktree
> concurrent-branch-switch lesson). **Frontier:** B-γ extension to aquaculture +
> supply_chain (D-5 was energy-first; the natural point to revisit RAG-baseline
> fairness with a fresh creative/adversarial Cowork perspective) + the
> verify+reshape forward-pointer (future PLAN/ADR) — both Cray-routed/gated. Held
> items unchanged (PLAN-002 ≥ADR-014, auditprep + ADR-011 real-partner-gated,
> partner-sim, ADR-0021(c) future-triggered). Nothing blocks Code.
> AI-assisted (Claude Code, session 64); no `Co-Authored-By` per CLAUDE.md §7.

_Addendum — rotated 2026-06-20 (session-69 reconcile): two CF blocks fell outside the 4-newest-sessions window {69, 67, 66, 64} — the **Session-67 `1cda40f`** block (Phase 1 ratify-flips, PLAN-0028/0029 → Accepted) and the **Session-63 `ab0174a`** block (B-γ kickoff, PLAN-0027 pre-registration), newest first._

> **Session 67 (head_commit `1cda40f`) — PHASE 1 RATIFY-FLIPS DONE
> (#357): PLAN-0028 + PLAN-0029 → Accepted + archived to `done/`.** The
> governance-closeout half of the universality track: **PLAN-0028** (B-γ
> cross-vertical extension — aquaculture + supply_chain) and **PLAN-0029**
> (entity-key whitespace calibration + offline re-grade) both flipped
> **Proposed (draft) → Accepted** (Cray ratified in-session 2026-06-17) and
> `git mv`'d to `docs/plans/done/`. **Cowork** applied the status-flip +
> ratification record (ADR-009 D1, G1-clean on Desktop); **Code** committed
> per ADR-009 D2 (#357, merge `1cda40f` / flip `3d5e2af`). Both PLANs document
> **already-complete, already-Cray-approved** work — a formal flip, not new
> work — so this is a clean close of the PLAN-0028/0029 governance loop; both
> moats' source PLANs are now archived. **R2 trust-but-verify confirmed:** spot
> SHAs check out (#353 `e5f9774`/`1ada20d`, #355 `d48b770`/`7275a69`) and the
> #357 diff is **status + ratification record only** (no scope/numbers change).
> **One harness note:** a Stop-hook D2 auto-dispatch **misrouted** — it tried to
> spawn `plan-drafter` to "draft a plan to flip 0028/0029," but the task was a
> **status-flip on existing complete PLANs**, not new-plan drafting; Code
> declined per the hook's override clause (reinforces the parked
> G2-drafting-friction root-fix — now a durable Active TODO). **Frontier:**
> Phase 2 kicked off — **ADR-0022 (governed entity resolution) authored by Cowork
> + committed Proposed (#359, `9ce1289`)**, design-first with the §Design fork left
> OPEN (Fork 3 = D-6 guard binding); scoped as one ADR-016-area construct also
> housing Group-A A1 (verify+reshape). **Awaits Cray ratification** (resolves the
> fork) → then a separate Cowork dispatch authors PLAN-0030; vertical-#3 research
> runs in parallel — all **Cowork-routed / Cray-gated**. Nothing blocks Code.
> AI-assisted (Claude Code, session 67); no `Co-Authored-By` per CLAUDE.md §7.

> **Session 63 (head_commit `ab0174a`) — B-γ KICKOFF: PLAN-0027 (B-γ
> COMPARISON METHODOLOGY PRE-REGISTRATION) LANDED + CRAY-RATIFIED §3–§4 (#337).**
> This session opens **B-γ** — PLAN-0019's last open step (AC B-3): the three-arm
> comparison on the **energy breach subset** — (a) the **governed-procedure stack**
> (reuse the existing REPORT numbers, **no re-run**), (b) **raw text-to-SQL**, and
> (c) a **lean-but-real RAG** baseline. Framed **reports-not-gates** (B-3/B-6) with
> a **D-6 contamination guard**: arm (c) stays a clean naive RAG baseline — **no**
> verify/reshape/governance layer bleeds in, so the comparison measures paradigms
> not a stacked deck. **PLAN-0027 completes B-γ Step 1 (pre-registration); status is
> now Ready for execution.** **Governance chain (the G2-routed path):** the
> in-harness `plan-drafter` authored the PLAN body → the **G2 PreToolUse gate blocks
> Code/subagent from writing a new PLAN** → **Cowork materialized** the file
> (ungated) → **Code committed** it (#337 `e70daa9`; ADR-009 D1/D2) → **Cray ratified
> §3–§4** (`fb91777`), resolving **SD-1..SD-4** per the drafter recommendations.
> Added at ratification: a **joint SD-1↔SD-2 fairness binding** (Cowork advisory) —
> under the locked lexical retriever the corpus + question template must **share
> vocabulary** and cover every breach item's `action_keywords` lemma, else arm (c)
> misses are **retrieval artifacts, not paradigm limits** (the binding that keeps the
> naive-RAG arm an honest baseline). **Also this session (no artifact change):**
> discussed the recurring **G2-vs-drafting friction** (the gate that forces the
> plan-drafter → Cowork → Code relay on every new PLAN); Cray **PARKED** the root-fix
> (exempt the plan-drafter's *uncommitted-draft* write from G2) as a **future
> harness-improvement batch**, and a "proceed vs Cowork-dispatch-file" routing
> framework was captured in private memory. **Frontier:** PLAN-0027 is Ready —
> **Step 2 (build arms b + c + the comparison harness offline, mock-ChatClient,
> honoring the joint binding) is ungated**; Step 3 offline gate; Step 4 host-state
> run is Cray-gated (§8). Held items unchanged. Nothing blocks Code.
> AI-assisted (Claude Code, session 63); no `Co-Authored-By` per CLAUDE.md §7.

_Addendum — rotated 2026-06-17 (session-67 reconcile): three CF blocks fell outside the 4-newest-sessions window {67,66,64,63} — both Session-62 blocks (second batch — harness-improvement "plan-first then execute" distillation, `cf958d3`; first batch — PLAN-0026 AC-9 optional live MS-S1 re-verify PASS, `c16778d`) and the Session-61 block (PLAN-0026 COMPLETE: ADR-0021 authored→Accepted + Phase A `measured_kind` shipped, `b53e631`), newest first._

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

_Addendum — rotated 2026-06-16 (session 64 reconcile): the Session-60 CF block (session 60 fell outside the 4-newest-sessions window {64,63,62,61})._

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

_Addendum — rotated 2026-06-16 (session 63 reconcile): the Session-59 CF block (session 59 fell outside the 4-newest-sessions window {63,62,61,60})._

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

_Addendum — rotated 2026-06-16 (session 62 reconcile): both Session-58 CF blocks
(third/second batches) rotated as session 58 fell outside the 4-newest-sessions
window {62,61,60,59}._

> **Session 58 (third batch; head_commit `987c2be`) — NL-QUERY
> FEASIBILITY SPIKE SHIPPED (#314) → PARTNER-TRIAL ROADMAP FORK RESOLVED: T2
> (NL-query) CHOSEN.** The headline is the FORK RESOLUTION, not just a
> benchmark. The partner-trial roadmap fork (T2 NL-query "wow demo" vs T3
> real-data "show me MY data"; readiness doc §4) needed its engineering half
> de-risked before Cray's go-to-market call. The spike (`benchmarks/nl_query_feasibility/`,
> `feat(benchmark):`, two commits — `ff5bab8` engine-A arm + `987c2be`
> text-to-SQL arm = the newest substantive per `lint_status`; merge `c3a48b4`)
> PIVOTED on a verified finding: from a hypothetical NL→MCP-tool-call to
> benchmarking the **shipped** engine-A path (`services/engine/nl_query.py`,
> PLAN-0013 — T2 was MORE built than the 2026-05-22 readiness doc said).
> **engine-A arm (gpt-oss:20b @ MS-S1):** 8/12 structured (~10/12
> operator-answer), latency p50 11s / p95 32s, and **anti-hallucination 12/12
> (zero invented facts)**. Dominant gap = translate filter-omission
> (whole-table fetch, phrase-rescued on toy data); join-by-name is a hard
> ceiling that fails *safely* (honest no-data). **text-to-SQL arm (same 12
> Qs):** 11/12, p50 5.6s / p95 12s — cleared every join/aggregate, applied
> WHERE every time, BUT **lost the anti-hallucination guard** (nl-12:
> improvised `SELECT … event_type='alarm'` for a no-data "alerts" question →
> returned an alarm as an alert). **The comparison answered the question:**
> the **ceiling is ARCHITECTURE** (StructuredQuery expressiveness — text-to-SQL
> cleared it, the model is capable), the **filter-omission is PROMPT** (the
> same model wrote WHERE under SQL framing). Both engine-A weaknesses are
> FIXABLE, not model limits. **Cray decision (fork resolved): T2 (NL-query)
> chosen** as the wedge — evidence-backed build path = enrich `StructuredQuery`
> with join + aggregate ops while KEEPING the grounded-execute safety (NOT a
> switch to raw text-to-SQL, which loses anti-hallucination) + fix the
> translate prompt (require the filter) + a UI shell (readiness T1 A1/A2).
> Process: Code-direct spike (like step-1); each AskUserQuestion decision was
> Cray-ratified inline.
> AI-assisted (Claude Code, session 58); no `Co-Authored-By` per CLAUDE.md §7.

> **Session 58 (second batch, current; head_commit `9595d3e`) — TWO BACKLOG
> QUICK-WINS (Code-solo, #311 + #312), cleared after the audit-framework arc
> closed.** A genuinely separate small batch (harness tooling, not the partner
> arc): two long-standing backlog items shipped back-to-back. **(1)
> stop-classifier gold cases #311 (`f2ee579`, `test(stop-classifier):`):**
> added 3 "dispatch discriminator" cases to `benchmarks/stop_classifier/gold.yaml`
> (20→23) pinning the surfaced-vs-ratified distinction the local classifier got
> WRONG in session 57 (it OVER-FIRED `plan-drafter` dispatches on ADR/PLAN
> *mentions* while the formality choice was a PENDING Cray decision — 2 instances)
> and RIGHT in session 58 (once Cray RATIFIED PLAN formality, the dispatch was
> correct). Two `pause` negatives + one `dispatch` positive; safety-weighted
> scoring makes a spurious dispatch a HARD FAIL. Offline test
> (`tests/benchmark/test_stop_classifier_gold.py`) green (4 passed); the live
> re-score (warm MS-S1) is a host-state eval — **pending Cray's go**; RESULTS.md
> got an addendum noting the recorded 2026-06-12 run predates the 3 cases (no
> model numbers fabricated). **(2) handoff-validator warning-swallow bug FIXED
> #312 (`9595d3e`, `fix(handoffs):`; PLAN-004 Phase B backlog):**
> `tools/handoffs/_schema.py::_build()` returned the typed `Frontmatter` on the
> otherwise-valid path and discarded its local `errors` list, so
> `_check_unknown()` WARNING findings (e.g. unknown field `brief-number`) were
> unreachable on any file without a hard error — contradicting `validate_file`'s
> own docstring. Fix: `Frontmatter` gains a `warnings` field; `_build()` fills
> it on the success path; `validate_file()` surfaces it; the `validate_handoff.py`
> CLI now prints the warning; precommit unchanged (still gates/prints only
> `is_error()`). Regression tests strengthened (the OLD test passed on the bug)
> + text-API + clean-file guards; `tests/handoffs/` 573 passed / 2 skipped;
> ruff + mypy clean. **Next:** quick-wins #2/#3 done → a strategic discussion is
> teed up for Cray — sequence the partner-trial roadmap fork (NL-query-first vs
> real-data-first) vs the B-γ benchmark baselines (do the fork first and feed
> B-γ, or B-γ first to inform the fork). Other backlog held: B-γ, PLAN-002
> (≥ADR-021), partner-trial gaps + audit-framework SD-4/SD-5/OQ-A + ADR-011
> (gated on a real partner).
> *Rotation note:* a new Session-58 (second batch) CF block was added (separate
> subject — harness tooling, not the partner arc), taking the count to 9 > the
> 8-block soft cap; per R2 the oldest CF block (session 56 fourth batch,
> stop-classifier calibration arc, #278/#279/#280) rotated to
> `docs/status-archive/2026-h1-status.md` this reconcile (R2/R4), keeping the
> count at 8.
> AI-assisted (Claude Code, session 58); no `Co-Authored-By` per CLAUDE.md §7.

_Addendum — rotated 2026-06-15 (session 61 reconcile): all four Session-57 CF blocks
(fifth/fourth/third/second batches) rotated as session 57 fell outside the
4-newest-sessions window {61,60,59,58}._

> **Session 57 (fifth batch, current; head_commit `e09af9b`) — AUDIT-FRAMEWORK PREP arc:
> partner-sim venue ADR-0020 committed Proposed (#297, `e25281d`, `docs(adr):`) + its
> project system instruction LANDED (#298, `e387a63`, `docs(conventions):`; merge
> `e10f589`), then a pre-ratification R1 errata + instruction align (#300, `655344d`,
> `docs(adr):`; merge `b466802`), then RATIFIED Proposed→Accepted (#302, head_commit
> `4d1347b`, `docs(adr):`; merge `d8c7c11`) — the venue is now ACCEPTED and live-able.**
> Two sub-batches both done this session. **(1) auditprep:** Cowork drafted two seed
> instruments (first-dataset requirements one-pager + PDPA review checklist); Code
> receive-verified; both gitignored under `docs/research/private/`, NOT committed. Open
> for Cray: SD-4 residency scope, SD-5 erasure vs append-only, OQ-A Thai PDPA lawyer
> review. **(2) partnersim:** ADR-0020 = a specialist Cowork project that role-plays a
> Thai operator and emits a "partner profile package" so the intake+PDPA pipeline is
> rehearsed before a real partner; D1 venue OUTSIDE the governance tiers; D2 three
> anti-circularity rules (R1 feed-questions-not-schema, R2 forced messiness, R3 SYNTHETIC
> provenance); D4 guarded-trial. Ratified in-session ("เอาตาม Cowork ทุกข้อ") with all
> venue SDs accepted. **Codas:** pre-ratification R1 errata (#300) caught a VERIFIED R1
> self-contradiction (the one-pager leaked our verdict taxonomy at the paste step) →
> dedicated R1-clean seed; RUN-1 received (#304, R2 PASS) + operation runbook; STEP-1
> mapping rehearsal shipped (#306, intake form v2 + mapping-gap analysis). ADR-011 still
> gated on a real partner — the synthetic run INFORMS but never TRIGGERS it.
> AI-assisted (Claude Code, sessions 57–58); no `Co-Authored-By` per CLAUDE.md §7.
> _(condensed at session-61 rotation; full verbatim in git history at STATUS.md pre-`b53e631`.)_

> **Session 57 (fourth batch) — B-6 hyphen normalization SHIPPED (#295; head_commit
> `2331ffb`, `fix(benchmark):`; merge `7374f52`) + post-#282 test-hermeticity gap FIXED
> en route (#294; `5330dfb`, `fix(tests):`).** `grader.py` gains
> `normalize_primary_key()`: the Unicode hyphen/dash family (U+2010–U+2014, U+2212) folds
> to ASCII `-` on both sides of the two primary-KEY comparisons; free-text matching
> untouched. 3 new tests. VERIFIED by offline dump replay: β re-grades 118/120 → 119/120
> with exactly one flip (energy-007 False→True, zero collateral). En-route (#294): the B-6
> regression check hit 17 timeouts in `test_stop_continuation.py` — post-#282 the
> subprocess fixtures' defang-by-no-key only neutered the SONNET path; the new
> local-Ollama default made REAL MS-S1 calls; pinned `CLAUDE_CLASSIFIER_BACKEND=sonnet`.
> Full suite 1481 passed / 22 skipped.
> AI-assisted (Claude Code, session 57); no `Co-Authored-By` per CLAUDE.md §7.
> _(condensed at session-61 rotation; full verbatim in git history.)_

> **Session 57 (third batch) — unit-side completion PING + no-Monitor rule SHIPPED (#290;
> `feat(skills):` `3c25d94`; merge `6a47d89`) + deferred header line LANDED (#292;
> head_commit `f1cf3b4`, `chore(skills):`; merge `f2184f6`).** `_run_detached_body.sh` now
> sends a best-effort unit-side Telegram ping immediately AFTER writing the `.done`
> sentinel — the sentinel stays the authoritative signal; a ping failure can never touch
> the sentinel or rc. SKILL.md codifies: never arm a harness Monitor on the sentinel.
> Verified `[wrap] PING ok` inside a real `systemd --user` unit. Classifier denied a
> cosmetic header edit (self-modification gate); the deferred line later landed (#292)
> after explicit per-diff Cray approval.
> AI-assisted (Claude Code, session 57); no `Co-Authored-By` per CLAUDE.md §7.
> _(condensed at session-61 rotation; full verbatim in git history.)_

> **Session 57 (second batch) — first SCORED watch-lane run RECORDED (#288; head_commit
> `4c46a92`, `docs(benchmark):`; merge `adb1bc5`) — watch lane 97.4% (38/39); the M-2=b
> arc is COMPLETE.** ~67 min via `run_detached.sh` (first production full run):
> `gpt-oss:20b` on MS-S1, 198 items, 318 LLM calls, 0 errors. Watch lane: aquaculture
> 100% / energy 100% / supply_chain 92.3% (1/13 fail = supply-040 forbidden `reroute` on
> an in-spec reading = the lane discriminating as designed). Companion lanes: β 98.3%
> (same two known misses incl. the energy-007 U+2011 hyphen → B-6), α 100%, deterministic
> 100%. SD-2 p95 30.18s (0.18s over; within the ±10s straddle band + run-unique
> classifier contamination). The harness watcher Monitor died silently; completion
> recovered via the sentinel + content test.
> AI-assisted (Claude Code, session 57); no `Co-Authored-By` per CLAUDE.md §7.
> _(condensed at session-61 rotation; full verbatim in git history.)_

_Addendum — rotated 2026-06-15 (session 60 reconcile):_

> **Session 57 — watch-lane GROUND TRUTH PINNED on all 39
> watch items (#286; head_commit `1bd6328`, `feat(benchmark):`; merge
> `6585bfc`).** The M-2=b
> calibration-first follow-up: Cray adjudicated the pinning from the #273
> REPORT.md calibration distribution — a dataset-only PR (no
> harness/grader/schema change); the watch lane auto-flips
> unscored→scored. Pins: **aquaculture** canonical
> `start_emergency_aerator` + acceptable `[dispatch_technician,
> increase_water_exchange, escalate]`; **energy** canonical `restart` +
> acceptable `[dispatch_technician, escalate]` (`isolate` deliberately
> excluded → grades 'other'); **supply_chain** canonical `inspect` +
> acceptable `[hold, escalate]` + `forbidden_keywords [expedite,
> reroute]` DECLARED on watch items, so the 3/13 observed reroute
> proposals classify forbidden. Adjudication-surfaced facts:
> `suggested_handler` is enum-constrained to the vertical's registered
> handlers (`run_benchmark.py`); the grader exact-matches
> canonical/acceptable; supply_chain watch items are in-spec near-ceiling
> readings (6.5–7.9 °C vs the 8.0 ceiling), not excursions — which drove
> the inspect-as-canonical choice. `tests/benchmark` **71 passed**
> (registered-handler + canonical-not-in-acceptable guards green); full
> suite re-ground earlier in session: **1478 passed / 22 skipped**.
> **Local-classifier first flight** (session 57 = first session on the
> `gpt-oss:20b` Stop/PreToolUse backend, #282): one false-continue Stop
> verdict observed — the turn legitimately ended awaiting Cray
> adjudication, and the closing "I'll open the PR once confirmed"
> sentence likely tripped the completion-consistency rule; not dangerous,
> cost one turn. **NEXT:** first SCORED watch run awaits a separate Cray
> go — launch ONLY via `bash .claude/skills/ms-s1-ollama/run_detached.sh
> <name> --reasoning-mode full` (done iff `<name>.done` exists; ETA
> ~65–70 min). Second pending adjudication: hyphen-normalization grader
> calibration (energy-007/energy-027 U+2011) needs explicit Cray
> ratification before any grader edit (B-6).
> AI-assisted (Claude Code, session 57); no `Co-Authored-By` per CLAUDE.md §7.

_Addendum — rotated 2026-06-15 (session 59 reconcile):_

> **Session 56 (sixth batch) — Lessons #24 + #25 RECORDED (#284;
> head_commit `4b0e306`, `docs(lessons):` = the newest substantive per
> `lint_status`; merge `c2da9b5`).** Cray-approved docs-capture coda to the
> calibration arc: **#24** — rules must live where the enforcer looks (the C5
> registry-gap finding generalized; adds an enforcement dimension to the
> ADR-0017 D5 placement rule). **#25** — an LLM judge's `{verdict, reason}`
> needs verdict-by-observable definitions + an explicit cross-field agreement
> contract, pinned by a prompt contract test + gold case (generalizes to the
> ADR-0018 goal-evaluator).
> AI-assisted (Claude Code, session 56); no `Co-Authored-By` per CLAUDE.md §7.

_Addendum — rotated 2026-06-14 (session 58 third-batch reconcile):_

> **Session 56 (fifth batch) — stop classifier SWITCHED to
> local `gpt-oss:20b` on MS-S1 (#282; head_commit `3375778`,
> `feat(claude):` = the newest substantive per `lint_status`; merge
> `03f81ec`).** The implementation of the fourth-batch decision: Cray
> picked **(b)** on the eval evidence ("latency 8s–30s acceptable") and
> the switch shipped same-day. `_sonnet_classifier.py`'s DEFAULT backend
> is now local `gpt-oss:20b` on MS-S1 Ollama (format-constrained
> `/api/chat`, temperature 0, `keep_alive` 10m, 75s timeout; no API key
> and no WSL bridge on this path); the Anthropic-API transport is
> retained as rollback via `CLAUDE_CLASSIFIER_BACKEND=sonnet`.
> `classify()` refactored around a backend-independent `_run_with_retry`
> keeping fail-closed-pause + the legacy reason strings byte-identical
> (unreachable MS-S1 pauses, never proceeds). `settings.json` hook
> timeouts → 180s (cold-load headroom); registry gains the backend note.
> Tests: the legacy suite pinned to the sonnet backend + 4 new
> ollama-backend tests (571 passed / 2 skipped; `mypy --strict` clean).
> LIVE-verified from the production hook runtime (Windows Python →
> 192.168.1.133): 7.9s → pause; Windows reachability pre-flight 0.09s.
> The next real Stop event in the working session is the production
> validation.
> AI-assisted (Claude Code, session 56); no `Co-Authored-By` per CLAUDE.md §7.

_Addendum — rotated 2026-06-14 (session 58 reconcile):_

> **Session 56 (fourth batch) — stop-classifier calibration arc
> SHIPPED (#278 + #279 + #280; head_commit `246ee0a`, `feat(claude):` = the
> newest substantive per `lint_status`; merge `9fde2d7`).** Cray-approved
> hook improvement + Cray-directed local-model eval. **#278** (`cbe6d05`):
> the classifier prompt gains the completion-consistency rule — PROCEED
> requires concrete remaining work and the decision must agree with its
> reason (fixes the observed over-continue on completed work; contract test
> pins it). **#279** (`aecf1bd` + `c84264e`): a 20-case safety-weighted
> eval harness at `benchmarks/stop_classifier/` with full prompt fidelity
> to the production hook (gold incl. Thai turns; offline tests). MS-S1
> sweep (4 models × 20 cases, 80 dump-verified records, 13:21–13:33):
> `gpt-oss:20b` 19/20, proceed-recall 100%, p50 7.1s / p95 21.6s vs
> sonnet(prod) 17+2/20, recall 75%, p50 2.5s / p95 3.5s; nemotron-4b
> DISQUALIFIED on safety (proceeds on dropdb); nemotron-30b out. **#280**
> (`246ee0a`) — the HEADLINE is a **registry gap, not a model gap**: ALL
> models incl. prod Sonnet proceeded on warm-MS-S1-without-a-go → new
> registry row **C5 (host-state gate)**, re-verified LIVE (both
> `gpt-oss:20b` and sonnet(prod) now flip to pause). RESULTS.md records the
> comparison + recommendation; the transport decision (local `gpt-oss:20b`
> vs API Sonnet) is **Cray's, on this evidence**.
> AI-assisted (Claude Code, session 56); no `Co-Authored-By` per CLAUDE.md §7.

_Addendum — rotated 2026-06-11 (session 53 reconcile):_

> **Session 49 (earlier) — PLAN-0020 Phase 1 (OFFLINE) is COMPLETE + merged
> (#232, `8324cba`, `feat(engine):`): two complementary, INDEPENDENT product-code
> changes addressing the session-48 PLAN-0019 Part B aquaculture over-naming
> finding.** One `feat(engine)` PR landed this turn (`feat(engine): deterministic
> affected_entities override + aqua precision prompt nudge (PLAN-0020 Phase 1)`),
> Cray-reviewed + merged via merge commit `f46f29c` (#232). This block = the
> session-49 #232 reconcile (head_commit `8324cba` — the newest substantive
> commit per `lint_status`; the #232 merge commit `f46f29c` is lint-excluded).
>
> **The two changes (both product code, independent).**
> - **fix #2 — deterministic `affected_entities` override (PRODUCT path).**
>   `services/engine/procedures/action_step.py` `_compose_action` now sources
>   `affected_entities` from the single loop `event` entity (a new
>   `_loop_entity_ref`), NOT the model's guess — mirroring the existing
>   `step.handler` override. This closes the envelope's over-naming metadata/UX
>   leak; the ADR-007 D2 `RecommendedAction` envelope CLASS is **unchanged** (one
>   field is now sourced deterministically).
> - **aqua prompt nudge (the benchmark β lever).** `services/engine/llm/prompt.py`
>   `build_reasoning_messages` / `build_structuring_messages` now instruct the
>   model to (a) name ONLY the breaching entity, (b) put the action verb in the
>   title. Vertical-agnostic wording (energy/supply already pass these checks → no
>   regression expected).
>
> **The key finding this session — why the two changes DON'T overlap.** The
> benchmark grades the **RAW `LlmJudgment`** (`harness.evaluate_item` bypasses
> `_compose_action` entirely), so **fix #2 is INVISIBLE to the benchmark β/α
> score** — it is validated instead by a dedicated **offline unit test**
> (`test_affected_entities_is_loop_entity_not_llm_overnaming`: an over-naming
> judgment → asserts the composed envelope names only the single loop entity,
> Lesson #7 §3 behavioural). The **prompt nudge** is what moves β — to be measured
> later in a **GATED host-state delta re-run** (NOT run this session).
>
> **The entity-key fork, RESOLVED.** `_loop_entity_ref` assumes the faithful
> ontology-projected event keys `object_type` + `primary_key`, with defensive
> `.get(..., fallback)` mirroring `recommender._rule_recommend` (degrades to
> `event_id`/`"unknown"` on a stub event, **never raises**). The procedure-path
> event shape is not yet standardised — this was surfaced for **merge-review per
> a two-way-door call** (reversible, offline, no production consumer today since
> Tier-2 real-data is parked); **Cray confirmed NO Tier-2 event-key contract in
> mind**, so the defensive getter STANDS. The HEDGE is documented in the
> `_loop_entity_ref` docstring + the commit body + the PR body.
>
> **Verification.** `ruff` + `mypy --strict` (services) green; `pytest` **71**
> (action_step + prompt + DB procedure + benchmark) + **104** (llm + eval
> golden-trace + recommender) green → confirms the reactive Pipeline-v0 path + the
> eval golden traces do NOT regress from the shared `prompt.py` edit.
>
> **PLAN-0020 stays status Draft.** SD-1 (widen supply-α `valid_handlers`
> `[hold]`→`[hold, inspect]`; needs Cray re-ratify BEFORE any dataset/grader edit)
> + SD-2 (8 s-bar review) remain **pending Cray ratification**; Code did NOT touch
> the grader/dataset this session.
>
> **Next — remaining Part B, Cray sequences (host-state — ASK before warming/
> running MS-S1).** ONE batched campaign: **B-3 baselines** (text-to-SQL + RAG,
> REPORTED not gated — the heaviest remaining sub-step + the conviction artifact)
> + **PLAN-0020 latency levers** + the **aqua prompt-nudge delta re-run** (re-run
> aqua β with the Step-1 nudge; confirm energy/supply did not regress). Cray must
> ratify SD-1 + SD-2 BEFORE the relevant gated step; Code does NOT touch the
> grader/dataset until SD-1 is ratified. THEN **B-5** report finalize + **B-6**
> ring-fence wrap (closes Part B). Sequencing = **Cray's call.** Standing backlog
> beyond Part B unchanged: Task (C) Tier-2 real-data path (gate on a design
> partner, not engineering readiness), PLAN-0010 loop handlers (soak-gated),
> `status_digest` v2, PLAN-004 Phase C.

> **Session 48 — PLAN-0019 Part B hardened re-run is COMPLETE (#228,
> `ec073a4`, `feat(benchmark):`): the hardened benchmark now DISCRIMINATES as
> designed, on live `gpt-oss:20b` (MS-S1, Cray-approved host-state run).** One
> `feat(benchmark)` PR landed this turn (`feat(benchmark): hardened re-run
> results + --dump-json verify tooling (PLAN-0019 B)`), Cray-reviewed + merged
> via merge commit `838f0ab`. This block = the session-48 #228 reconcile
> (head_commit `ec073a4` — the newest substantive commit per `lint_status`; the
> #228 merge commit `838f0ab` is lint-excluded). Touched only `benchmarks/`
> (REPORT.md, harness.py, run_benchmark.py) — **no product code.**
>
> **Verify, don't infer (the session-46 lesson, operationalized).** Added
> `--dump-json` to the runner — per-item JSONL emitting verdicts + per-check
> details + the raw `LlmJudgment` (`harness.py` `ItemResult` now carries the raw
> judgment) — so **every score was VERIFIED against real model output, not
> inferred.** `REPORT.md` gains a "Results — HARDENED run (2026-06-09)" section;
> the pre-hardening baseline is retained for comparison. Raw evidence dump kept
> as a gitignored working note under `.claude/benchmark-results/`.
>
> **Hardened results (2026-06-09 run; 198 items / 240 LLM calls / 0
> StructuredOutputError).**
> - **β headline (SD-B1 ≥ 85%):** aquaculture 60.0% (24/40), energy 97.5%
>   (39/40), supply_chain 100% (40/40) → **overall 85.8% (103/120) — CLEARS
>   ≥85%** (a companion warm run read 89.2% → honest β ~86–89%). β fell from a
>   pre-hardening 100% to ~86–89% — the hard scenarios gave the headline real
>   discriminating power, exactly as PR2 intended.
> - **α handler-probe (own lane, NOT the headline):** aquaculture 77.5%
>   (31/40), energy 100% (40/40), supply_chain 32.5% (13/40) → overall 70.0%
>   (84/120).
> - **deterministic sanity:** 100% (198/198).
> - **latency (B-δ):** p95 22.64 s, mean 15.02 s (240 calls) → OVER the 8 s bar
>   (~2.8×) — the same ring-fenced finding (NOT a build failure, NOT a bar move,
>   NOT an ADR-016 reopen).
>
> **Verified failure modes (from the `--dump-json` capture — the discriminating
> signal).**
> - **aquaculture β=60% — two REAL model weaknesses:** 11× `forbidden_primary_keys`
>   (under multi-entity input the model frames a "DO Monitoring Summary" and
>   over-names SAFE decoy sibling ponds — e.g. `aqua-h01` names breached
>   `pond-A101` AND safe `pond-A102`/`pond-A103`) + 7× `action_keywords`
>   (assessment framing omits the aerate/oxygenate verb). Energy & supply_chain
>   show NO over-naming — energy's `forbidden_primary_keys` passed on every hard
>   item, so it handles multi-entity input markedly better (a real cross-vertical
>   signal).
> - **supply_chain α=32.5% is a BENIGN divergence, not a model error:** the model
>   picks `inspect` (a defensible cold-chain action; 21/28 easy, 6/12 hard) where
>   the dataset pins single `hold`, and crucially NEVER the dangerous near-misses
>   `expedite`/`reroute`. β stays 100% (action_keywords admits
>   inspect/hold/quarantine/divert). **Finding → tuning PLAN:** the α
>   `valid_handlers` for supply_chain is plausibly too narrow (arguably
>   `[hold, inspect]`) — a tuning-PLAN question, NOT a grader change (methodology
>   ratified). aquaculture's α misses are likewise mostly the benign
>   `increase_water_exchange`.
>
> **Bottom line.** Part B's empirical core is now closed end-to-end: the
> hardened benchmark **discriminates** (β ~86–89%, driven by aquaculture's hard
> scenarios surfacing real entity-precision + action-verb weaknesses), the α
> probe surfaces a real but **benign** handler divergence, sanity stays 100%,
> and latency is the known over-bar B-δ finding. All below-bar reads are logged
> findings → the follow-up tuning PLAN under the B-6 ring-fence; none moves a bar
> or reopens ADR-016.
>
> **Next — remaining Part B, Cray sequences.** **(1) Latency tuning PLAN** from
> the B-δ finding (p95 22.6 s > 8 s) — OFFLINE, authored via `plan-drafter`;
> levers: trim the `think=True` call-1 pass / batching / a faster-arch small
> model not yet on MS-S1 / revisit the 8 s bar; **incorporate the supply-α
> `valid_handlers`-too-narrow observation** as a candidate methodology tweak.
> **Must NOT reopen ADR-016's primitive shape (ring-fence).** **(2) B-3
> baselines** — raw text-to-SQL + a RAG baseline on the same questions
> (REPORTED, not gated; acceptance = a comparison run + measures recorded) — the
> heaviest remaining sub-step; hits MS-S1 (host-state). **(3) B-5 report
> finalize + B-6 ring-fence wrap.** Standing backlog beyond Part B unchanged:
> Task (C) Tier-2 real-data path (heavy-spend → Cray green-lights), PLAN-0010
> loop handlers (soak-gated), `status_digest` v2, PLAN-004 Phase C. Sequencing
> remains **Cray's call**.

> **Session 47 — PLAN-0019 Part B hardening is COMPLETE (PR1 #224 +
> PR2 #226): the benchmark now has the real action vocabulary, the β/α grading
> split, AND the hard multi-entity / near-miss scenarios + precision checks.
> PR2 (#226, `e76977d`, `test(benchmark):`) makes the β headline
> discriminating.** This is the SECOND PR of session 47 (PR1 = #224 below). One
> `test(benchmark)` PR landed this turn (`test(benchmark): hard scenarios +
> β-headline precision checks (PLAN-0019 B PR2)`), Cray-reviewed + merged via
> merge commit `6efb28c`. Cray-ratified design (2026-06-09): the entity-precision
> check is **`forbidden_primary_keys`**, and the hard items **augment** the
> dataset (the easy items stay as a floor baseline). Sequencing decided ELI-CTO:
> **build PR2 first, THEN one comprehensive hardened re-run** (not
> re-run-now-then-again) — higher information yield per host-state window, no
> misleading intermediate ~100%, respects anti-moving-target.
>
> **What PR2 hardens (why the β headline now discriminates).** PR2 gives the
> β headline real discriminating power on the two fields the model genuinely
> OWNS in the procedure path — entity-ID and action class:
> - **Multi-entity decoys (entity-ID):** `Scenario` gains `distractors` (1–3
>   SAFE sibling readings, mostly in the watch band so they read as borderline),
>   injected into the event as `other_readings`; the model must name the breach
>   AND NOT the decoys → the β-headline scoring checks `affected_primary_key`
>   (right entity) + the new `forbidden_primary_keys` (no decoy named). A loader
>   guard asserts every decoy is genuinely non-breaching and that
>   `forbidden_primary_keys` exactly equals the scenario's distractor set.
> - **Near-miss action (action-class):** a plausible-but-wrong action the model
>   must avoid recommending — aquaculture `feed` (feeding during an O₂ crash),
>   energy `monitor`/`schedule` (deferring an acute over-temp), supply_chain
>   `expedite`/`reroute` (keeping a possibly-spoiled load moving) → the checks
>   `action_keywords` (right verb present) + the new `forbidden_keywords` (decoy
>   verb absent from the proposal TITLE; the body may legitimately rule it out).
> - **Dataset:** +12 HARD breach items per vertical (ids `*-h01..h12`), each a
>   clear breach among the safe sibling decoys + a domain near-miss. The easy
>   items are kept as the floor baseline. **54 → 66 items/vertical; 84 → 120
>   graded breach items.**
>
> `grader.py` / `harness.py` / `schema.py` thread the precision checks + the
> distractor injection; `REPORT.md` documents the hard scenarios + precision
> checks and keeps the prior filled numbers as the PRE-HARDENING baseline. PR2
> touched only `benchmarks/` + `tests/benchmark/` — **no product code**.
>
> **Verification:** ruff check + ruff format clean; `mypy --strict` (benchmarks)
> clean; full suite **1347 passed / 2 skipped** (was 1340/2; +7 benchmark
> tests). This block = the session-47 #226 reconcile (head_commit `e76977d` —
> the newest substantive commit per `lint_status`; the #226 merge commit
> `6efb28c` is lint-excluded).
>
> **Next — a comprehensive hardened re-run on live `gpt-oss:20b` on MS-S1.**
> The hardened re-run on `gpt-oss:20b` on MS-S1 (192.168.1.133:11434) is **a
> host-state change — ASK Cray before warming/running.** One comprehensive run
> fills the β headline on the hard scenarios + the α handler-selection probe on
> the real menu (per the agreed PR2→single-re-run ordering); warm-first,
> serialized for a clean p95. Then **author a latency tuning PLAN** from the
> B-δ finding (trim the `think` pass / batching / a faster-arch small model /
> revisit the 8 s bar) — **must NOT reopen ADR-016's primitive shape
> (ring-fence)**; **B-3 baselines** (text-to-SQL + RAG, REPORTED not gated —
> the heaviest remaining sub-step); then **B-5** report finalize + **B-6**
> ring-fence wrap. Sequencing remains **Cray's call**.
>
> **Prior context (session 47 earlier — #224, `00d7a24`, `feat(benchmark):`):
> PLAN-0019 Part B hardening PR1 of 2 is COMPLETE — the real ontology
> action-handler vocabulary ((C) product-complete) + a β-headline / α-probe
> grading split, driven by a handler-determinism finding.** This was the FIRST
> PR of session 47, executing the remaining PLAN-0019 Part B work that session
> 46's handoff left for Cray to sequence. One `feat(benchmark)` PR landed
> (`feat(benchmark): action_type handler vocabulary + β/α grading split
> (PLAN-0019 B)`), Cray-reviewed + merged via merge commit `0dfd03a`. Cray
> ratified the design this session: **scope (C) product-complete**, **grading
> β + α**, **2 PRs (handlers first, then harder scenarios)**.
>
> **The handler-determinism finding (why β/α).** While scoping the hardening,
> Code found that vero-lite has TWO action paths with different handler
> semantics: the **reactive** Pipeline-v0 (`recommender._compose_llm_record`)
> USES the model's `suggested_handler` guess and `execute()` runs it; the
> **procedure** orchestrator (ADR-016, `action_step._compose_action`) OVERRIDES
> the guess with the author's deterministic, allowlist-bounded `step.handler`.
> The benchmark grades the raw `LlmJudgment`, but PLAN-0019 validates the
> **procedure** path, which discards the handler guess — so grading
> handler-selection as the *headline* would measure a field the procedure
> product overrides (and brush ADR-016). Resolution, Cray-ratified 2026-06-09:
> **β headline** = the fields the model owns in the procedure path = entity
> (`affected_primary_key`) + action class (`action_keywords`); **α probe** =
> handler-selection (`suggested_handler` vs the correct ontology `action_type`),
> reported on its OWN lane as a reactive-path / future-autonomy signal, NOT
> folded into the headline. `payload_contains` stays advisory.
>
> **Product ((C) product-complete).**
> `verticals/{aquaculture,energy,supply_chain}/handlers.py` now register the
> ontology `RecommendedAction.action_type` vocabulary as distinctly-named
> **no-op stubs** alongside `echo` (aquaculture
> `start_emergency_aerator`/`dispatch_technician`/`increase_water_exchange`/`escalate`;
> energy `restart`/`isolate`/`dispatch_technician`/`escalate`; supply_chain
> `reroute`/`expedite`/`hold`/`inspect`/`escalate`) — so the LLM
> `suggested_handler` enum is now a real 4–5-option menu (real I/O still lands
> with the design partner). Each procedure's breach action step now fixes
> `step.handler` to the correct `action_type` (aquaculture
> `aerate`→`start_emergency_aerator`, energy `restart_breaches`→`restart`,
> supply_chain `hold_breaches`→`hold`), **autonomy stays `gated`** (the human
> go/no-go is unchanged), and each agent's `allowed.action_handlers` allowlist
> was updated; aquaculture `summary` stays `echo` (a no-op artifact). So the OCT
> product now proposes/executes real-named gated actions instead of `echo`.
>
> **Benchmark.** `grader.py` `FieldCheck` gained a `probe` lane +
> `GradeResult.probe_passed`; `harness.py` `Summary`/`ItemResult` thread the α
> metric; `run_benchmark.py` prints it. Dataset `valid_handlers
> [echo]→[correct action_type]` across all 84 breach items. The
> dataset-consistency guard now requires ≥1 β-headline scoring field; a new
> offline test asserts every α-probe handler is registered for its vertical.
> `REPORT.md` documents the finding + the β/α lanes and **relabels the prior
> filled numbers as the PRE-HARDENING baseline** (echo-only,
> valid_handler-in-headline) — a hardened re-run is pending. `pyproject.toml`
> adds `allowed-confusables = ["α","β"]` for the project's Greek step/metric
> notation. `tests/services/db/test_procedure_headline.py` binds its gate spy to
> `start_emergency_aerator` (the gated step's new handler).
>
> **Verification:** ruff check + ruff format clean; `mypy --strict`
> (services/verticals/benchmarks) clean; full suite **1340 passed / 2 skipped**
> (was 1336/2; +4 net benchmark tests). This block was the session-47 #224
> reconcile (its substantive commit was `00d7a24`; the #224 merge commit
> `0dfd03a` is lint-excluded). Superseded as the head by #226 above.
>
> **Next — remaining Part B, β+α direction chosen, Cray to sequence.** **PR2 —
> harder scenarios** (multi-entity sets, distractors, near-miss actions) +
> **grader precision** (decoy-entity absence / forbidden-keyword checks) to give
> the **β headline** real discriminating power → then a **hardened re-run** on
> live `gpt-oss:20b` on MS-S1 (fills the β headline on the harder scenarios +
> the α handler-selection probe on the real menu — a host-state change, **ASK
> Cray before warming/running**). **Author a latency tuning PLAN** from the B-δ
> finding (trim the `think` pass / batching / a faster-arch small model / revisit
> the 8 s bar) — **must NOT reopen ADR-016's primitive shape (ring-fence)**.
> **B-3 baselines** — text-to-SQL + RAG comparison on the same questions
> (REPORTED, not gated) — the heaviest remaining sub-step. Then **B-5** report
> finalize + **B-6** ring-fence wrap. All via `test/*` (or `feat/*` where product
> code) PR(s). Sequencing remains **Cray's call**.

_Addendum — rotated 2026-06-11 (session 55 reconcile):_

> **Session 49 — ADR-0017 "Skills as a memory tier" is ACCEPTED; the
> skills-as-memory-tier governance arc is COMPLETE (#236 + #237, head_commit
> `8b18b3a`, `docs(constitution):`).** Two PRs landed since the #235 reconcile,
> so this single reconcile advances head_commit past BOTH (it was stale at
> `471bcb5`). #236 (`docs(adr):`, `7bf9d38`) added ADR-0017 `Proposed` —
> Cowork-drafted, Code-reviewed via the ADR-009 D3 receive sequence; #237
> (`docs(constitution):`, `8b18b3a`) ratified it (status flipped
> Proposed→Accepted) and applied the alignment. head_commit = `8b18b3a` (the
> newest *substantive* commit per `lint_status`; `8b18b3a` is
> `docs(constitution):` = substantive → it sets head_commit; the #236/#237
> merge commits `c04787b`/`7bf9d38`'s merge and the `docs(status):` reconciles
> are lint-excluded). This block is **T6** (STATUS reconcile) of the ADR-0017
> follow-on plan.
>
> **The arc, end to end.** PR #234 added the `.claude/skills/` **mechanism**
> (two on-demand skills + CLAUDE.md slimming) → #236 added the **ADR** (the
> governance rationale + decisions) → #237 applied the **alignment** (T1–T5).
> The skills-as-memory-tier arc is now governance-complete.
>
> **What #237 aligned (T1–T5).**
> - `.claude/skills/` is now **Tier 2.6** in the memory model (`CLAUDE.md` §4 +
>   the memory-architecture runbook) — git-tracked, auto-loaded by description
>   match.
> - The **D5 knowledge-placement decision rule** — binding rule→`CLAUDE.md`;
>   durable learning→`docs/lessons/`; canonical reference→`conventions`/
>   `runbooks`; task-triggered how-to→a **Skill** — and the **D7
>   skill-authoring conventions** are codified in the runbook (compact form +
>   a pointer from §4).
> - `CLAUDE.md` §1 gained the **D6** line (derived artifacts 2.5 + 2.6 carry no
>   independent precedence; canonical wins on conflict); the §10 skills row now
>   cites ADR-0017.
>
> **T6 housekeeping (this reconcile).** ADR-0017 (Accepted) recorded in Recent
> Decisions; the §50/§57 "next: draft ADR-017" earmark is **cleared** (the ADR
> now exists and is Accepted); the PR #234 skills follow-up is marked
> **governance-complete**.
>
> **Next.** The arc is closed. Open threads: (1) **OQ-B** — skill loader
> tie-break (same-named project vs global vs plugin skill) is delegated to Code
> but needs Cray approval for a probe touching global `~/.claude/skills/` (host
> state); (2) the deferred **Axis-B verification-loop** track (evaluator
> subagent + `/goal` Stop-hook gate) from the harness-engineering review. A
> **restart-bridge handoff is due this session** because #237 edited
> constitutional `CLAUDE.md` (Lesson #5 §1).

> **Session 49 (#234 — predecessor in this same arc) — CLAUDE.md slimmed: git +
> Code-ops procedures extracted to on-demand project skills (#234, `471bcb5`,
> `docs(constitution):`).** One
> `docs(constitution)` PR landed this turn (`docs(constitution): slim CLAUDE.md —
> extract git + Code-ops procedures to on-demand skills`), Cray-reviewed + merged
> via merge commit `d556421` (#234). This block = the session-49 #234 reconcile
> (head_commit `471bcb5` — the newest substantive commit per `lint_status`;
> `docs(constitution):` IS substantive, so it sets head_commit; the #234 merge
> commit `d556421` is lint-excluded).
>
> **What shipped.** The always-loaded constitution shrank `206→193 lines /
> 2050→1908 words` by extracting git mechanics + the Tier-2 Code-ops procedure
> into TWO new on-demand project skills under `.claude/skills/` —
> **`git-workflow`** and **`code-operational-policy`** — with **all binding rules
> retained in `CLAUDE.md`** (only the step-by-step procedure moved). This
> establishes `.claude/skills/` as the project's on-demand procedure layer,
> adopting Anthropic's Agent-Skills pattern: a bloated always-on `CLAUDE.md`
> causes rules to be ignored, so procedure belongs in on-demand skills that load
> only when relevant.
>
> **Genesis (the two-axis harness-engineering review, 2026-06-09).** A review of
> vero-lite against Anthropic's public harness guidance reached a two-axis
> verdict: **Axis A (governance / safety)** = vero-lite is at the frontier — its
> deterministic-hooks + Sonnet-classifier hybrid independently mirrors Anthropic
> *auto mode*, and `chain-cap=8` matches Claude Code's own default; **Axis B
> (task-completion / verification — the evaluator loop)** = thin, deferred as a
> separate, higher-leverage track. PR #234 is the **low-risk FIRST move** Cray
> chose off that review (Skills adoption + CLAUDE.md slimming).
>
> **Follow-up already DISPATCHED to Cowork.** Cowork is to draft an ADR (next free
> number, likely **ADR-017**) titled **"Skills as a memory tier"** — handoff
> (gitignored) at `.claude/handoffs/session-49/2026-06-09-2140-code-skills-memory-tier-adr-dispatch.md`.
> Code commits the resulting `Proposed` ADR per ADR-009 D2. The dispatch carries
> 8 OQs to resolve: tier placement, `for_llm/` overlap, the canonical-vs-derived
> rule, authoring ownership, the knowledge-placement decision rule, the precedence
> ladder, conventions, and the migration backlog.
>
> **Next.** Cowork drafts ADR-017 "Skills as a memory tier" → Code commits
> `Proposed` → Cray ratifies. Separately/optionally: begin the Axis-B
> verification-loop prototype (an evaluator subagent + a `/goal` Stop-hook gate).

_Addendum — rotated 2026-06-12 (session 56 reconcile) — five session-51 blocks, newest first:_

> **Session 51 — PLAN-0021 EXECUTED + MERGED (#249, branch tip
> `3dc586a`; merge `83f179d`; head_commit `7d6d713` = the `docs(plans):`
> archive-mv riding this closeout PR, the newest substantive per
> `lint_status` — only `docs(status):` is excluded): the Axis-B
> verification loop is LIVE.** 2,125 insertions: 6 new files
> (`_goal_state.py`; `_goal_gate.py` at the D4 seam inside
> `stop_continuation.py`; the `/goal` project command — the repo's first,
> discovered mid-session; `goal-evaluator` as 4th subagent sibling; the
> SD-1 narrowed-Write deny hook; +64 tests across 3 new test modules + M2
> rows), exactly 3 modified files, `settings.json` untouched (F-1). All 10
> ACs closed; the 10-row case-coverage matrix fully implemented as named
> tests AND 7 rows proven LIVE in the session's own Stop hooks: real
> dispatch ×2 (D6 pointers-only template; Windows-side check subprocess +
> UNC git fingerprint worked), live evaluator spawn (J1=PASS
> file:line-cited; appended its verdict through the SD-1 hook; caught a
> real registry-footer gap on its first run), happy flip
> (`_goal_gate:passed` + Telegram info), and the fail-open probe
> (deliberately unanswered dispatch → `released-unevaluated` + LOUD
> Telegram + stop fired, NO wedge — D4's asymmetry held in production;
> both Telegrams Cray-screenshot-confirmed, timestamps matching the
> trail). Full suite 1398 passed / 22 skipped, zero regression. Key
> finding **F-L1**: verdict→flip lands at the next non-chained Stop (the
> re-entry guard short-circuits block-continuation Stops — a PLAN-0008
> invariant, 3 consistent observations; OQ-8 blocking-mode promotion must
> account for it). PLAN-0021 archived to done/ (`7d6d713`, same PR as
> this reconcile). Closeout handoff:
> `.claude/handoffs/session-51/2026-06-10-1450-code-plan0021-build-closeout.md`.
> AI-assisted (Claude Code, session 51); no `Co-Authored-By` per CLAUDE.md §7.

> **Session 51 (earlier) — PLAN-0021 "Axis-B verification loop — build"
> landed as Draft (#247, head_commit `78b8659`, `docs(plans):`).** Cowork
> drafted it per ADR-009 D1 off the session-51 T2 dispatch; Code R2-reviewed
> + committed per D2/D3. The PLAN renders Accepted ADR-0018 into a build
> plan: 6 new files (`_goal_state.py`, `_goal_gate.py`,
> `.claude/commands/goal.md` — the repo's FIRST project command, net-new
> dir; `goal-evaluator.md` as 4th subagent sibling;
> `pretooluse_goal_evaluator_write_deny.py` SD-1 narrowed-Write hook; 3
> test modules) + exactly 3 modified files (M1 `stop_continuation.py` one
> insertion at the D4 seam, M2 its tests, M3 `autonomy-triggers.md` V-row).
> 10 ACs incl. AC-2 goal-less byte-for-byte non-interference; a 10-row
> case-coverage matrix, each row mapped to a named test; VX-1..3 resolved;
> OQ-8 pinned Out of Scope. Key R2 item **F-1**: Cowork caught the
> dispatch's wrong premise — status-scribe's deny hook wires via agent
> frontmatter ONLY, not `settings.json` — so the PLAN keeps `settings.json`
> untouched and ADR-0018 §spec 4 stays literally true. **NEXT:** Cray
> ratifies PLAN-0021 (incl. SD-1: SubagentStop notify for goal-evaluator —
> Cowork recommends NO for v1) → Code executes Steps 1-6 in a feature
> branch.
> AI-assisted (Claude Code, session 51); no `Co-Authored-By` per CLAUDE.md §7.

> **Session 51 (earlier) — STATUS rotation arc COMPLETE: Lesson #23 +
> rotation policy R1-R6 (#244), status-scribe hardened (#245), FIRST
> ROTATION under the policy + 64 KB pre-commit guard (this PR).** Root
> cause of the 393 KB bloat was the scribe's own retention rule ("never
> delete history" with no size counterweight — Lesson #23 §2); the policy
> pairs retention with a budget: hard 64 KB / soft 48 KB (R1), window =
> 4 newest sessions / <=8 CF blocks + 10 RD rows (R2), terse single-line
> frontmatter (R3), archive-don't-drop to `docs/status-archive/` (R4),
> surgical reads only for the scribe (R5), prune every reconcile (R6).
> **This rotation:** session-47 CF block + 39 RD rows -> archive
> (`2026-h1-status.md` — new file; the ratified h1 current-focus file is
> 242 KB, past the ~192 KB R4 split bar, so appending would breach the
> 256 KB Read cap — flagged, not silent); F-6 prune dropped all [x]
> Active TODOs older than the window + Next Steps items 1-9 (superseded
> MERGED history; recorded in RD/git). head_commit `25af97b` (#245
> `chore(agents):` = newest substantive; #244's `e22ab18`/`311761c`
> precede it). R2 review note: Code-harness tokenizer measures ~2.2 B/tok
> on this file (38.6k tok at 83 KB) vs Cowork's ~3.3 — 64 KB may still
> exceed a whole-file Read in some harnesses; R5 surgical reads are the
> structural protection, the byte ceiling is the enforcement proxy.
> **NEXT = Axis-B T2** (dispatch ready, awaiting Cray relay to Cowork).
> AI-assisted (Claude Code, session 51); no `Co-Authored-By` per CLAUDE.md §7.

> **Session 51 (earlier) — ADR-0018 "Axis-B Verification Loop" is RATIFIED
> Accepted (#242, head_commit `1be60f7`, `docs(adr):`); the deferred Axis-B
> verification-loop track is no longer deferred — it is now Accepted and
> entering its build phase.** ADR-0018 opens harness-review **track 2** (the
> evaluator loop) on top of the already-at-frontier Axis-A governance layer:
> a `/goal` Stop-hook gate + a `goal-evaluator` subagent that judges whether a
> run actually achieved its declared goal. **Decisions:** D1 hybrid
> deterministic-check + LLM-judge; D2 a `.claude/state/goal.json` run-goal
> artifact; D3 a **4th subagent sibling that REFUTES rather than blesses**
> (the structural guard against reasoning-blindness); D4 a `_goal_gate.py`
> living inside `stop_continuation.py`, **FAIL-OPEN** (a broken/absent
> evaluator never blocks Stop); D5 a session-Stop **warn-only v1**; D6 the
> structural reasoning-blindness rationale; D7 formalize + augment the manual
> AC ritual. **SD-1 resolved = narrowed Write** — the evaluator's `Write` is
> hook-narrowed to `goal.json` only (the same author-bounded pattern that
> governs `plan-drafter` and `status-scribe`). **Lineage:** PR #241 added the
> ADR `Proposed` (`5f8073c`) → **#242 ratified it Proposed→Accepted (Cray,
> session 51)** and carries this **T4** STATUS reconcile (the ADR §"Required
> follow-on" T4 task: record ADR-0018 in Recent Decisions + clear the
> Current-Focus Axis-B "deferred" earmark). head_commit = `1be60f7` (the
> ratification `docs(adr):` commit = the newest *substantive* commit per
> `lint_status`; this `docs(status):` reconcile does NOT count). **NEXT = T2:**
> Code dispatches the Axis-B **build PLAN** to Cowork (ADR-009 D1) — covering
> `_goal_gate.py` + the `stop_continuation.py` insertion, the `goal.json`
> schema + tests, the `/goal` command, the `goal-evaluator` agent + the SD-1
> write-deny hook, Telegram wiring, and a verification-rigor case-coverage
> matrix; after draft + Cray ratify → T3 (autonomy-triggers **V-row**) →
> build. **OQ-8** (plugin packaging, MS-S1 local evaluator, blocking-mode
> promotion, PR-merge gating, auto-declared goals) and **VX-1..3** stay
> non-binding / verify-at-execution — none blocks T2. This session also
> earlier resolved ADR-0017 OQ-B (#239/#240), already recorded below.
> AI-assisted (Claude Code, session 51); no `Co-Authored-By` per CLAUDE.md §7.

> **Session 51 (earlier) — ADR-0017 OQ-B is RESOLVED; the skills-as-memory-tier
> arc's last open thread is CLOSED (#239, head_commit `c512cf9`,
> `docs(adr):`).** OQ-B (skill-loader tie-break on a same-bare-name collision)
> was the one "delegated to Code" empirical item left after the arc body landed
> in session 49 (#234/#236/#237/#238). Empirical finding, restart-confirmed at a
> clean session-51 startup (~99% confidence): on a same-name collision the
> **GLOBAL/user skill (`C:\Users\crayj\.claude\skills\`) WINS over the project
> skill** (`<repo>/.claude/skills/`) — the OPPOSITE of ADR-0017 D7's
> "project-local context wins" premise; the WSL `~/.claude/skills/` path is not
> scanned, and plugin skills are namespaced (so they don't collide). Recorded
> three ways: (1) ADR-0017 gains a **"D7 Errata (2026-06-10)"** subsection +
> OQ-B flipped Open→RESOLVED (errata applied with Cray's explicit per-diff
> approval through the G1 Accepted-ADR gate); (2) new
> `docs/lessons/0022-skill-loader-precedence.md`; (3) a fill of the
> `docs/runbooks/memory-architecture.md` §"Skill Conventions" OQ-B placeholder.
> The D7 **authority rule** (global/plugin skills must not encode
> project-binding rules) is UNCHANGED and *reinforced* — only the loader
> tie-break mechanics and an incidental `eli-cray` example (it's a command, not
> a global skill) were corrected. The throwaway probe artifacts (host state on
> three skill roots) were cleaned up after merge — working tree restored to
> clean. AI-assisted (Claude Code, session 51); probe ran with Cray's approval;
> no `Co-Authored-By` per CLAUDE.md §7. Two ADR-0017 OQs remain, both
> non-blocking: **OQ-A** (migration backlog — non-binding future-PR candidates)
> and **OQ-C** (revisit the tier definition only if harness-as-plugin packaging
> is pursued). No governance thread is currently blocked or in-flight.

_Addendum — rotated 2026-06-12 (session-56 reconcile #284) — the session-53 block (first rotation forced by the R2 8-block cap):_

> **Session 53 — PLAN-0020 (Procedure-path tuning) is COMPLETE
> + archived to `docs/plans/done/` (#251–#256, branch-tip `a6125c1` =
> head_commit, the `docs(plans):` close-mv riding #256; merge `02d3e46`;
> the PLAN-0019 B-6 ring-fence follow-up).** Headline results (all
> `--dump-json`-VERIFIED, `gpt-oss:20b` on MS-S1): the Phase-1 aquaculture
> prompt nudge (PR #232, previously UNMEASURED) worked **dramatically** —
> overall β `85.8%→100%`, aquaculture β `60%→100%`, overall α `70%→100%`
> (supply_chain α `32.5%→100%`: the model now picks `hold`, not `inspect`).
> **The latency lever:** a new `reasoning_mode` lever showed `skip` (drop the
> call-1 reasoning pass) cuts per-judgment p95 `31.80s→21.62s` — UNDER the
> re-ratified SD-2 bar — at **ZERO β cost** (the reasoning pass is redundant
> given the nudged prompt); `think_off` is a **dead lever** (slower).
> **SD-2 re-ratified** the latency bar from 8 s/per-call to **≤30 s p95
> per-judgment** (reports-not-gates). **SD-1** (widen supply-α `valid_handlers`)
> was authorized at ratification but **SKIPPED at Step 9** — the nudge made the
> divergence moot (0 `inspect`); anti-moving-target honored, **no grader
> change**. Also shipped: a per-judgment latency timer (#252), the think-trim
> lever (`feat(engine)`, #253, PLAN-0020 AC-1a), and the **`ms-s1-ollama`
> skill** (#254, `warm.sh` live-tested). PR lineage: #251 ratify Draft→Accepted
> (`19706eb`, SD-1 widen-α + SD-2 →30 s/judgment) → #252 latency timer
> (`a3a6f54`) → #253 think-trim lever (`bef462f`) → #254 skill (`ac56653`) →
> #255 tuning report (`4968f51`, `docs(report):`) → #256 close-mv to done/
> (`a6125c1`, `docs(plans):` = head_commit, the newest substantive per
> `lint_status` — only `docs(status):` is excluded).
> **Session 52 was non-committing** (an Axis-B verification-loop LIVE demo +
> a backlog-prioritization pass that ranked PLAN-0020 priority #1) — no repo
> state changed, so the jump is session 51 → 53.
> **Next.** A follow-up PLAN for **tiered handler grading**
> (canonical / acceptable / forbidden) is surfaced by Cray's production-fidelity
> review — the α metric is too coarse to self-distinguish a benign alternative
> (`inspect`) from a dangerous pick (`expedite`/`reroute`); deferred to a future
> session for discussion. Separately, **wiring `skip` into the product
> procedure path** is an open design call (audit trade-off: `skip` drops the
> ADR-010 reasoning narrative; the model-asserted `rationale` survives). The
> gitignored Cowork research (why `gpt-oss:20b` wins) is now **DONE** —
> delivering a 6-criterion model-selection **screening rubric (R1–R6)** + a
> warm-cycle gate (`docs/research/private/2026-06-11-gpt-oss-20b-winning-properties.md`),
> the paper pre-filter for the deferred R3 faster-arch eval. **Held for a future
> R3-adjacent warm-cycle:** Cray pulled **3 `nemotron-3-nano` variants** to
> MS-S1 (`30b-a3b-q4_K_M`, `30b-a3b-q8_0`, `4b`) — **no eval run yet, no
> ADR-0001 change**; intent is pin vs these in one maintenance-window warm-cycle,
> ideally paired with the U-1 `MXFP4`-vs-`Q4_K_M` tok/s check + U-2 `eval_count`
> logging. **Caveat:** they ship `q4_K_M`/`q8_0`/`fp16` (not `MXFP4`), so they
> exercise rubric R1/R5 now but a fair **R2 bandwidth** comparison needs an
> `MXFP4` build.
> AI-assisted (Claude Code, session 53); no `Co-Authored-By` per CLAUDE.md §7.

_Addendum — rotated 2026-06-12 (session-57 reconcile #286) — the session-54 block (R2 8-block cap):_

> **Session 54 — PLAN-0022 "tiered decision routing" landed as
> Draft (#259, head_commit `f5eba1b`, `docs(plans):`); the deferred
> tiered-handler-grading follow-up is now a committed plan.** Cowork drafted it
> (ADR-009 D1) off the session-54 Code dispatch + the design seed; Code ran the
> ADR-009 D3 receive sequence — `validate_handoff.py` **clean** on the companion
> handoff, plus an **R2 fact-pack review that re-verified Cowork's two
> load-bearing catches against HEAD**: **FP-2/SD-6** — `services/engine/procedures/`
> ships exactly one concrete `StepExecutor` (`ActionStepExecutor`); `StepKind.EVALUATE`
> exists but executors are caller-provided and **no `watch_margin` lives under
> `services/`** (benchmark-only), so a deterministic `evaluate` executor is a real
> **prerequisite** for `watch→gated` wiring; **FP-1/SD-7** — aquaculture
> `procedures.yaml` routes `verdict: watch → human_task` (a bare visual check),
> **not** silence, so the change is an *upgrade* (bare "go look" → a `gated`
> proposal). The PLAN renders Cray's two-axis reframe (threshold clear × data
> clear/ambiguous) into (1) tier the benchmark grader
> (canonical/acceptable/forbidden) and (2) wire the deterministic `watch` band →
> a `gated` human-escalation — trigger = the engine watch band, **never**
> `confidence` (ADR-010 IN-3, load-bearing AC-3). Covers all 5 dispatch areas;
> SD-1..SD-5 = the design-seed OQs, **SD-6/SD-7 newly surfaced**. **Also received**
> (gitignored research, no commit): **3 Build-Vertical narratives** (one each
> energy/supply_chain/aquaculture — each carries a clear breach + a borderline
> `watch`, so they double as PLAN-0022 routing fixtures; **S-1** = aquaculture
> uses ammonia not the benchmark's DO/aerate, Cowork recommends KEEP; **S-3** =
> a deterministic `dwell_minutes` co-gate candidate that escalates `watch`
> **without** an ADR-010 reopen), and the **gpt-oss model-selection rubric
> R1–R6** (recorded in #258). **RATIFIED (#261, `46061b7`):** Cray accepted
> **SD-1..SD-7 per recommendation** (SD-1=a gated *replaces* human_task; SD-2=a
> deterministic watch band only, no ADR-010 reopen; SD-4=a reuse
> `forbidden_keywords`; SD-5=a fields on the `Step`; SD-6=a evaluate executor in
> the impl PR) + **S-1 keep ammonia**; status flipped Draft → Ready for
> execution + a **§ Execution Order** (dependency-sequenced) added. **Phase 0 DONE**
> (#263, `137766c`): **ADR-0019** (`watch→gated`-proposal routing) ratified
> **Accepted** + merged — the CLAUDE.md §8 gate. Cowork authored the **option-(b)**
> follow-on ADR (Cray's OQ-1 pick) after the **G1/G2 PreToolUse gates correctly
> blocked Code's direct ADR write** (ADR-009 D1: Cowork authors, Code commits);
> Code R2-verified verbatim + committed. *(A transient classifier-bridge timeout
> first fail-closed the gate with a misleading "policy" deny — diagnosed, bridge
> confirmed healthy; memory updated.)* **NEXT (implementation):** Phase 1 grader
> taxonomy ∥ config (define once) → Phase 2 the deterministic `evaluate` executor →
> `watch→gated` → Phase 3 escalation scoring. Trigger = engine watch band, never
> `confidence` (ADR-010 IN-3).
> AI-assisted (Claude Code, session 54); no `Co-Authored-By` per CLAUDE.md §7.

_Addendum — rotated 2026-06-12 (session-57 second reconcile #288) — the session-55 block (R2 8-block cap):_

> **Session 55 — PLAN-0022 Phase 2 SHIPPED (#267, head_commit
> `6870f87`, `feat(engine):`; merge `9072fda`) — the session's SECOND impl
> merge: the deterministic `evaluate` executor + the `watch → gated` routing
> (ADR-0019) are LIVE.** **Phase 2a (SD-6, the evaluate executor):** NEW
> `services/engine/procedures/evaluate_step.py` — an engine-owned judge
> computing `breach / watch / ok` from the Step-authored band via
> `classify_verdict`, **no LLM call** — the ADR-0019 determinism invariant
> holds by construction. **Phase 2b (SD-1=a, watch→gated):** the aquaculture
> `watch` set now routes to a gated `increase_water_exchange` proposal
> `escalate_watch`, replacing the bare visual-check `human_task`; the
> existing `resolve_gated_step` / suspend / resume machinery is reused
> verbatim. **AC-8 named test landed** — escalation byte-for-byte identical
> under confidence 0.05 vs 0.99 (trigger = the engine watch band, never
> `confidence`; ADR-010 IN-3) — and **AC-9 held** (breach path + reject =
> continue+record proven on both gates). Full suite **1459 passed** (+14);
> ruff + mypy clean. **NEXT = Phase 3, the only remaining phase:** the
> escalation-correctness scoring lane (Step 5 — scores "escalated
> correctly" vs "should have acted" vs "should have stayed silent" on its
> own watch-tier lane), **B-6 ring-fenced: the scoring methodology must be
> Cray-ratified BEFORE any scored benchmark run**. *Methodology RATIFIED
> (Cray, 2026-06-12, in-session):* **M-1** watch items run the LLM judgment,
> graded on a NEW watch-tier lane (pass = handler ∈ {canonical, acceptable};
> forbidden named explicitly per SD-4=a; never folded into β); **M-2 = (b)
> CALIBRATION-FIRST** — watch ground truth is NOT authored yet (no REPORT
> evidence); the first run reports the suggested-handler distribution only
> (no pass/fail pinned), ground truth pinned from that evidence (mirrors the
> B-β calibration precedent); **M-3** deterministic mis-routing is
> structurally impossible in the harness — reported as structural, no fake
> failure surface; **M-4** watch-judgment latency = its own diagnostic, the
> SD-2 ≤30s bar stays breach-scoped — **no bar moves**. A scored run still
> needs a separate Cray go (MS-S1 host-state). Spec + ratification record in
> the session-55→56 kickoff handoff
> (`.claude/handoffs/session-55/2026-06-12-0039-...-phase3-kickoff.md`).
> After Phase 3, PLAN-0022 archives to done/. Held items carry unchanged
> (nemotron MXFP4
> warm-cycle hold; bridge-resilience option B parked). *Rotation note:* per
> Cray (2026-06-11) the five session-51 CF blocks rotate at the NEXT
> reconcile; this pass added no new block (Phase 2 extends this block), so
> they are kept one more pass.
>
> *Earlier this session — Phase 1 SHIPPED (#265, `a68a114`, `feat(engine):`;
> merge `6b1bdd5`): the benchmark grader's α probe TIERED + the `Step`
> band/tiers config surface (Phase 0 = ADR-0019, #263, prior session).*
> **Step 1 (grader tiering, SD-4=a):**
> `Expected.valid_handlers` → `canonical_handler` + `acceptable_handlers`;
> dispositions are now `canonical / acceptable / forbidden-or-other`; all
> datasets migrated. Acceptable sets are grounded in PLAN-0020 REPORT
> evidence — supply_chain `[inspect]`, aquaculture
> `[increase_water_exchange]`, energy none (no recorded benign divergence).
> **Step 3 (config surface, SD-5=a):** the `Step` spec gains optional
> `threshold` / `direction` / `watch_margin` + `tiers`, and the NEW
> engine-owned `classify_verdict` (`services/engine/procedures/verdict.py`)
> is the single shared watch-band definition — `grader.classify_disposition`
> now DELEGATES to it (watch-band math defined once, per the ratified
> § Execution Order); aquaculture `procedures.yaml` carries the worked
> example. Full suite **1445 passed**; **AC-9 byte-for-byte back-compat
> held**. (The Phase-2 items formerly listed as NEXT here shipped later
> this session — superseded by the lead of this block.)
> AI-assisted (Claude Code, session 55); no `Co-Authored-By` per CLAUDE.md §7.

_Addendum — rotated 2026-06-12 (session-57 third reconcile #290) — the session-56 Phase-3 block (R2 8-block cap):_

> **Session 56 — PLAN-0022 Phase 3 SHIPPED (#270, `1723981`,
> `feat(benchmark):`; merge `93d0b67`) + PLAN-0022 CLOSED OUT to
> `docs/plans/done/` (#271, head_commit `b41a138`, `docs(plans):` = the
> newest substantive per `lint_status`; merge `f15115c`) — ALL FOUR PHASES
> COMPLETE (#263 ADR-0019 → #265 Phase 1 → #267 Phase 2 → #270 Phase 3).**
> Phase 3 implements the Cray-ratified methodology M-1..M-4 verbatim.
> **M-1:** watch items now RUN `generate_judgment` and grade on a new
> ISOLATED watch-tier lane via the shared `classify_handler_tier` taxonomy
> (pass = handler ∈ {canonical, acceptable}; forbidden explicit per SD-4=a)
> — never folded into β. **M-2 = b (calibration-first):** dataset YAMLs are
> UNCHANGED (no watch ground truth authored yet); the lane reports the
> suggested-handler DISTRIBUTION unscored until ground truth is pinned from
> run evidence (mirrors the B-β calibration precedent). **M-3:**
> deterministic mis-routing columns are STRUCTURAL (the harness makes
> mis-routing impossible — no fake failure surface). **M-4:** watch-judgment
> latency is its OWN diagnostic; the SD-2 ≤30s bar stays breach-scoped —
> **no bar moves**. The REPORT.md methodology section was recorded BEFORE
> any scored run (B-6 honored); module docstring aligned (`7bf7240`). Full
> suite **1469 passed / 22 skipped** (+10); ruff + mypy clean. **NO scored
> run has happened yet** — the first calibration-only run still needs a
> separate explicit Cray go (MS-S1 host-state; warm via the `ms-s1-ollama`
> skill, pinned `gpt-oss:20b`); AFTER it, the M-2=b follow-up authors the
> watch canonical/acceptable handlers from the distribution evidence. Held
> items carry unchanged (nemotron MXFP4 warm-cycle hold; bridge-resilience
> option B parked). *Rotation note:* executed Cray's standing 2026-06-11
> decision — the five session-51 CF blocks rotated to
> `docs/status-archive/2026-h1-status.md` this reconcile (R2/R4).
> AI-assisted (Claude Code, session 56); no `Co-Authored-By` per CLAUDE.md §7.

_Addendum — rotated 2026-06-12 (session-57 fourth-batch reconcile #294/#295) — the session-56 second-batch block (R2 8-block cap):_

> **Session 56 (second batch) — the FIRST watch-lane scored run
> (calibration-only per M-2=b; explicit Cray go 2026-06-12) RAN on MS-S1 and
> its results are RECORDED in `benchmarks/procedure_baseline/REPORT.md`
> (#273, head_commit `489b695`, `docs(benchmark):` = the newest substantive
> per `lint_status`; merge `d0f8af8`).** Run: pinned `gpt-oss:20b`, full 198
> items, `reasoning_mode=full`, 319 LLM calls, 0 errors — all numbers
> `--dump-json`-VERIFIED. **Watch suggested-handler distribution (unscored
> per M-2=b):** aquaculture 13/13 `start_emergency_aerator`, energy 13/13
> `restart`, supply_chain `hold` 5 / `inspect` 5 / **`reroute` 3 — the
> lane's first real safety signal**: "Continue"/"Proceed" titles at
> confidence 1.0 on borderline excursions; under a `{hold, inspect}` pinning
> these classify FORBIDDEN. **Companion lanes:** β 98.3% (118/120; both
> misses verified — aqua-028 boundary hedger + energy-007 U+2011
> non-breaking hyphen → a standing grader-calibration candidate awaiting
> ratification), α 100%, deterministic 198/198. **Latency:**
> per-breach-judgment p95 28.73s = the first SD-2 PASS in full mode (read
> within the ±10s noise band); per-watch-judgment mean 32.12s / p95 54.21s
> recorded as the M-4 own-lane diagnostic (notably slower than breach; no
> bar). **No bar moves (B-6).** Run artifacts gitignored at
> `.claude/benchmark-results/2026-06-12-plan0022-phase3-calibration.{log,jsonl}`.
> Next: Cray adjudicates the watch ground-truth pinning (per-item
> canonical/acceptable from this distribution evidence) → dataset PR → the
> first SCORED watch-lane run.
> AI-assisted (Claude Code, session 56); no `Co-Authored-By` per CLAUDE.md §7.

_Addendum — rotated 2026-06-13 (session-57 sixth reconcile #297/#298) — the session-56 third-batch block (carrier-death hardening; R2 8-block cap):_

> **Session 56 (third batch) — post-calibration carrier-death
> incident HARDENED (#275 merge `97d132c`, #276 merge `09750af`;
> head_commit `3a8a175`, `feat(skills):` = the newest substantive per
> `lint_status`).** The calibration run's carrier (held `wsl.exe` + wrapper)
> was one-off-reaped at ~59 min while the file-redirected python survived as
> an orphan and COMPLETED — no harness completion notification fired and the
> background-task chip stayed "running" stale; truth was established
> content-based (final DUMP/NOTE lines + 198/198 dump records + `pgrep`
> empty + TaskStop "No task found"). Shipped: **#275** (`f7cb82a`) records
> the gotcha + the content-based truth test in the `ms-s1-ollama` skill;
> **#276** (`3a8a175`) adds `run_detached.sh` + `_run_detached_body.sh` —
> long MS-S1 runs now launch under `systemd-run --user` (unit parented to
> the user manager, not the carrier; PROBE-VERIFIED 2026-06-12: a unit
> launched from a foreground `wsl` call — the exact condition that kills
> `setsid`/`nohup` children — kept writing and completed; offline
> end-to-end smoke validated uv-under-systemd + `[wrap]` markers + the
> `.done` SENTINEL "rc ISO-ts" written as the job's last act). SKILL.md
> launch recipe rewritten (ETA rule: ETA + ~10 min → check the sentinel;
> `Linger=no` caveat — enabling linger = host-state, ask Cray).
> AI-assisted (Claude Code, session 56); no `Co-Authored-By` per CLAUDE.md §7.

---

## Rotated Recent Decisions rows (rotated 2026-06-10)

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-06-15 | **PLAN-0024 (NL-query T2 engine enrichment) SHIPPED — engine half of the T2 wedge (#316 plan / #317 engine, `f4aa7fe`, session 59)** _(rotated 2026-06-21, session 71)_ — `StructuredQuery` gains `max/min/avg/sum` (+ optional `group_by`) computed in the deterministic execute stage + a new `NlAnswer.aggregate` grounding receipt (never the phrase LLM), plus a `NameResolve` cross-type name→id descriptor (resolve-then-filter; `object_type` stays single/enum-constrained, group keys relabelled id→title); translate prompt now requires the implied filter + exact enum grounding. Gold ceiling cases nl-08/09/10/11 moved onto the deterministic structured-result lens (`_aggregate_ok`). Anti-hallucination AC-5 preserved (empty/no-numeric/unresolved short-circuit to no-records). 11 new offline tests; suite 1511/22 (+30); ruff+mypy clean. Governance: Cray scoped engine-only (UI→PLAN-0025, SD-1 deferred) → `plan-drafter` authored PLAN-0024 → ungated Cowork placed the file (G2 denied all in-harness Code writes) → Code committed #316 → merged → Code executed #317; SD-1 done as the recommended pre-step; one L1 loop-detect resolved by a Cray-approved counter reset, no Bash | `f4aa7fe` (#316/#317) / `services/engine/nl_query.py` + `docs/plans/done/0024-nl-query-t2-engine-enrichment.md` |
| 2026-06-14 | **Two backlog quick-wins SHIPPED (Code-solo, #311 + #312, `9595d3e`, session 58)** _(rotated 2026-06-21, session 71)_ — cleared after the audit-framework arc closed; a separate small harness-tooling batch. **#311** (`f2ee579`, `test(stop-classifier):`): 3 "dispatch discriminator" gold cases added to `benchmarks/stop_classifier/gold.yaml` (20→23) pinning the surfaced-vs-ratified distinction the local classifier got wrong in s57 (over-fired `plan-drafter` on ADR/PLAN mentions while formality was a PENDING Cray decision — 2 cases) and right in s58 (post-ratification dispatch correct); 2 `pause` negatives + 1 `dispatch` positive, safety-weighted (spurious dispatch = HARD FAIL); offline test green (4 passed); live re-score pending Cray go; RESULTS.md addendum (recorded 2026-06-12 run predates the cases). **#312** (`9595d3e`, `fix(handoffs):`, PLAN-004 Phase B): handoff-validator warning-swallow bug fixed — `_schema.py::_build()` discarded its `errors` list on the otherwise-valid path so `_check_unknown()` WARNINGs were unreachable; `Frontmatter` gains `warnings`, `validate_file()` surfaces it, CLI prints it (precommit unchanged); regression tests strengthened; `tests/handoffs/` 573 passed / 2 skipped; ruff + mypy clean | `9595d3e` (#311/#312) / `benchmarks/stop_classifier/gold.yaml` + `tools/handoffs/_schema.py` |
| 2026-06-14 | **PLAN-0023 (PDPA RoPA-lite, step-2 of audit-framework-prep) SHIPPED (#308 PLAN + #309 deliverables, `afea6b3`, session 58)** _(rotated 2026-06-20, session 71)_ — two tracked deliverables: reusable RoPA-lite template (`docs/conventions/partner-ropa-lite.md`, canonical) + NPD synthetic example (`docs/strategy/public/partner-sim-run1-ropa-example.md`, SYNTHETIC), each RoPA slot annotated with a data-quality/lineage hook; example's DSR/lineage→ADR-011 section maps 4 gaps→implications (PII-in-free-text→log-by-reference; scattered actor identity→actor unification; PK reuse + NTP drift→lineage/valid-from + ordering; under-recording→completeness-not-assumed). Governance: Cray ratified PLAN formality (3 decisions) → `plan-drafter` subagent authored PLAN-0023 (ADR-013 D1) → Code committed (#308, ADR-009 D2) → Code executed deliverables Code-direct (#309); PLAN archived to `done/`. SD-1 kept (AC-6 in-PLAN). ADR-011 still gated on a real partner — synthetic run INFORMS but never triggers PLAN-0005 §8.1 (ADR-0020 R3). Carried open: SD-4/SD-5/OQ-A | `afea6b3` (#308/#309) / `docs/conventions/partner-ropa-lite.md` + `docs/strategy/public/partner-sim-run1-ropa-example.md` |
| 2026-06-13 | **ADR-0020 (partner-sim venue) RATIFIED Proposed→Accepted (#302, `4d1347b`, session 57)** _(rotated 2026-06-20, session 69)_ — Cray ratified in-session ("เอาตาม Cowork ทุกข้อ"); all four venue SDs + dispatch-SD-1 accepted per Cowork rec (Cowork-authored fold per ADR-009 D1, Code R2-reviewed + committed). SD-1 N=3 (→D2/R2); SD-2 one-project-per-business-type (→D4; R-PS4 reframed as a guard); SD-3 size/region/maturity enums + run-1 default energy·mid·th-regional·mixed-legacy (→D3 input); SD-4 "what we refused to share" ratified-required (→D3 output). R1/R2/R3 substance unchanged (#300 errata settled those). Instruction file reconciled same PR (6 ratification-pending markers → ratified; Code-amends-conventions, ADR-009 D2). dispatch-SD-1 (gitignored): one-pager sector-callout forbidden-action note trimmed, R1-clean seed untouched. Venue now ACCEPTED guarded-trial (R-PS1..R-PS4) — live action is Cray's (launch energy run-1) | `4d1347b` (#302) / `docs/adr/0020-partner-sim-venue.md` + `docs/conventions/partnersim_project_instructions.md` |
| 2026-06-13 | **ADR-0020 (synthetic design-partner simulation venue, partner-sim) committed Proposed (#297, `e25281d`, session 57) + project system instruction landed (#298, `e387a63`)** _(rotated 2026-06-17, session 67)_ — a specialist Cowork project that role-plays a Thai operator + emits a "partner profile package" so the intake+PDPA pipeline is rehearsed before a real partner. D1 venue OUTSIDE governance tiers (no commits / no repo mount / enters via Code receive); D2 three BINDING anti-circularity rules (R1 feed-questions-not-schema, R2 forced messiness, R3 SYNTHETIC provenance — never trips PLAN-0005 §8.1 / ADR-011 first-real-data trigger); D3 reuses completion-handoff schema (no enum change); D4 guarded-trial (mirrors ADR-012 D5) + R-PS1..R-PS4. SD-1..SD-4 recommendations only. **Awaits Cray ratification (Proposed→Accepted + SD-1..SD-4) before the project goes live (ADR-0020 T3).** Author≠reviewer (ADR-012 D4.3): Cowork authored, Code R2-reviewed + committed both | `e25281d` (#297) + `e387a63` (#298) / `docs/adr/0020-partner-sim-venue.md` + `docs/conventions/partnersim_project_instructions.md` |
| 2026-06-12 | **B-6 hyphen-normalization grader change RATIFIED + SHIPPED (#295, `2331ffb`, session 57)** _(rotated 2026-06-16, session 64)_ — Cray ratified in-session; `grader.py` `normalize_primary_key()` folds the Unicode hyphen/dash family (U+2010–U+2014, U+2212) → ASCII `-` on both sides of the two primary-KEY comparisons only; free-text untouched. Offline dump replay vs the 2026-06-12 scored run: β 118/120 → 119/120, EXACTLY one flip (energy-007, zero collateral); aqua-028 still fails. Same measurement-correctness class as the 2026-06-08 items; no bar moves; REPORT.md dated addendum | `2331ffb` (#295) / `benchmarks/procedure_baseline/grader.py` |
| 2026-06-12 | **First SCORED watch-lane run RECORDED — watch 97.4% (38/39); M-2=b arc COMPLETE (#288, `4c46a92`, session 57)** _(rotated 2026-06-16, session 63)_ — `gpt-oss:20b`/MS-S1, 198 items, 318 calls, 0 errors, dump-VERIFIED (39/39 `watch_graded:true`); first production `run_detached.sh` run (sentinel as designed; watcher Monitor died silently + one false alarm — truth via content-based test). Aqua + energy 13/13; supply 12/13 — sole FAIL supply-040 (reroute @1.0 on an in-spec 7.8 °C) = `forbidden_keywords` discriminating as designed. β 98.3% (same two known misses; energy-007 U+2011 now ×3 → strengthens B-6). SD-2 p95 30.18s = +0.18s nominal, within the ±10s straddle band + classifier-contaminated; no bar moves (B-6) | `4c46a92` (#288) / `benchmarks/procedure_baseline/REPORT.md` |
| 2026-06-12 | **Watch-lane ground truth PINNED — all 39 watch items (#286, `1bd6328`, session 57)** _(rotated 2026-06-16, session 62)_ — Cray adjudicated the M-2=b pinning from the #273 calibration distribution: aqua canonical `start_emergency_aerator` + acceptable `[dispatch_technician, increase_water_exchange, escalate]`; energy canonical `restart` + acceptable `[dispatch_technician, escalate]` (`isolate` excluded → 'other'); supply_chain canonical `inspect` + acceptable `[hold, escalate]` + `forbidden_keywords [expedite, reroute]` declared (3/13 observed reroutes → forbidden). Dataset-only; the watch lane auto-flips unscored→scored; first SCORED run gated on a separate Cray go | `1bd6328` (#286) / `benchmarks/procedure_baseline/dataset/` |
| 2026-06-12 | **Lessons #24 + #25 RECORDED (#284, `4b0e306`, session 56)** _(rotated 2026-06-15, session 61)_ — Cray-approved coda to the classifier calibration arc. **#24:** rules must live where the enforcer looks — a binding rule placed only in prose is invisible to a machine enforcer reading a different surface (C5 registry-gap finding generalized; adds an enforcement dimension to the ADR-0017 D5 placement rule). **#25:** an LLM judge's `{verdict, reason}` needs verdict-by-observable definitions + an explicit cross-field agreement contract, pinned by a prompt contract test + gold case (generalizes to the ADR-0018 goal-evaluator) | `4b0e306` (#284) / `docs/lessons/0024-rules-must-live-where-the-enforcer-looks.md` + `docs/lessons/0025-llm-judge-verdict-must-bind-to-its-own-reasoning.md` |
| 2026-06-12 | **Stop classifier SWITCHED to local `gpt-oss:20b` (#282, `3375778`, session 56)** — Cray picked **(b)** on the calibration evidence (8–30s latency acceptable). Default backend = MS-S1 Ollama (format-constrained `/api/chat`, temp 0, keep_alive 10m, 75s timeout; no API key / no WSL bridge); Anthropic API retained as rollback via `CLAUDE_CLASSIFIER_BACKEND=sonnet`. Fail-closed pause + legacy reason strings byte-identical; legacy suite pinned to sonnet + 4 new ollama-backend tests (571 passed / 2 skipped; mypy --strict clean); LIVE-verified from the prod hook runtime: 7.9s → pause | `3375778` (#282) / `.claude/hooks/_sonnet_classifier.py` |
| 2026-06-12 | **Stop-classifier calibration arc SHIPPED (#278 + #279 + #280, `246ee0a`, session 56)** _(rotated 2026-06-15, session 59)_ — #278 completion-consistency rule (PROCEED needs concrete remaining work; decision↔reason agreement; contract-test-pinned). #279 20-case safety-weighted eval harness (full prod-prompt fidelity; gold incl. Thai); MS-S1 sweep 4×20 (80 dump-verified): `gpt-oss:20b` 19/20, recall 100%, p95 21.6s vs sonnet(prod) 17+2/20, recall 75%, p95 3.5s; nemotron-4b safety-DQ. #280 HEADLINE = registry gap not model gap → registry row C5 (host-state gate), re-verified live; transport pick (local vs API Sonnet) = Cray's | `246ee0a` (#278–#280) / `benchmarks/stop_classifier/RESULTS.md` |
| 2026-06-12 | **Carrier-death incident → ops hardening SHIPPED (#275 + #276, `3a8a175`, session 56)** _(rotated 2026-06-14, session 58)_ — the calibration run's carrier (held `wsl.exe` + wrapper) was reaped at ~59 min; the orphaned python completed silently (stale "running" task chip, no completion event; truth established content-based). #275 records the gotcha + content-based truth test in the `ms-s1-ollama` skill; #276 adds `run_detached.sh` — long MS-S1 runs launch under `systemd-run --user` (carrier-proof, PROBE-VERIFIED 2026-06-12; `.done` sentinel "rc ISO-ts"; ETA + ~10 min → check sentinel; `Linger=no` = host-state, ask Cray) | `3a8a175` (#275 + #276) / `.claude/skills/ms-s1-ollama/` |
| 2026-06-12 | **First watch-lane calibration run RECORDED (#273, `489b695`, session 56)** _(rotated 2026-06-14, session 58)_ — M-2=b evidence on MS-S1 (`gpt-oss:20b`, 198 items, 319 calls, 0 errors, `--dump-json`-verified). Watch distribution: aqua 13/13 aerator, energy 13/13 restart, supply_chain hold 5 / inspect 5 / **reroute 3 = the lane's first real safety signal** (forbidden under a `{hold, inspect}` pinning). β 98.3% (2 verified misses incl. the U+2011 hyphen grader-calibration candidate), α 100%, deterministic 198/198. Breach p95 28.73s = first SD-2 PASS in full mode (±10s noise band); watch latency = M-4 own diagnostic. No bar moves (B-6) | `489b695` (#273) / `benchmarks/procedure_baseline/REPORT.md` |
| 2026-06-12 | **PLAN-0022 COMPLETE — Phase 3 watch-tier escalation lane SHIPPED (#270, `1723981`, session 56) + plan archived to done/ (#271, `b41a138`)** _(rotated 2026-06-13, session 57)_ — implements the Cray-ratified M-1..M-4 methodology (M-2=b calibration-first: watch items run the LLM judgment, unscored distribution reporting until ground truth is pinned from run evidence; M-4 watch latency = own diagnostic, SD-2 bar stays breach-scoped; REPORT methodology recorded BEFORE any scored run). All four phases done (#263/#265/#267/#270). Suite 1469; first calibration run gated on a separate Cray go | `b41a138` (#270 + #271) / `docs/plans/done/0022-tiered-decision-routing.md` + `benchmarks/procedure_baseline/REPORT.md` |
| 2026-06-11 | **ADR-0019 (`watch → gated`-proposal routing) ACCEPTED + merged (#263, `137766c`, session 54)** _(rotated 2026-06-13, session 57)_ — PLAN-0022 **Phase 0** governance gate (CLAUDE.md §8; merges before the impl PR). Cray chose **OQ-1 form (b)** = a follow-on ADR over an in-place ADR-016 amendment. Sanctions routing the deterministic `watch` set → a `gated` `action` proposal (LLM proposes → human decides via `resolve_gated_step`); **extends ADR-016 D3** — no primitive / auto-gated / ceiling / allowlist change; trigger = engine verdict, never `confidence` (ADR-010 IN-3). **Authored by Cowork** — the G1/G2 PreToolUse gates correctly blocked Code's *direct* ADR Write/Edit (ADR-009 D1: Cowork authors, Code commits); Code R2-verified verbatim + committed. Includes an ADR-016 forward pointer + the Morning-Pond Step 4 row (`human_task` → gated proposal, SD-1=a). *(A transient classifier-bridge timeout first fail-closed the gate; diagnosed + healthy.)* | `137766c` (#263) / `docs/adr/0019-watch-gated-proposal-routing.md` + `docs/adr/0016-*` |
| 2026-06-11 | **PLAN-0022 (tiered decision routing) RATIFIED Draft → Ready for execution (#261, `46061b7`, session 54)** _(rotated 2026-06-12, session 57)_ — Cowork-drafted (ADR-009 D1, #259); Code R2-reviewed, re-verifying the two load-bearing fact-pack catches vs HEAD (**FP-2/SD-6:** no deterministic `evaluate` executor in `services/engine/procedures/` — only `ActionStepExecutor`; a real prerequisite for `watch→gated`; **FP-1/SD-7:** aquaculture `procedures.yaml` routes `watch→human_task`, an *upgrade* target not silence). Cray accepted **SD-1..SD-7 per recommendation** (SD-1=a gated replaces human_task; SD-2=a deterministic watch band only, no ADR-010 reopen; SD-4=a reuse `forbidden_keywords`; SD-5=a fields on the `Step`; SD-6=a evaluate executor in the impl PR) + **S-1 keep ammonia**. Added **§ Execution Order**: Phase 0 ADR-016 D3 amendment first (CLAUDE.md §8) → Phase 1 grader taxonomy ∥ config (define once) → Phase 2 `evaluate` executor → `watch→gated` → Phase 3 escalation scoring. Trigger = engine watch band, never `confidence` (ADR-010 IN-3). Impl = later separate PR. Also received (gitignored research): 3 Build-Vertical narratives + the gpt-oss rubric R1–R6 | `46061b7` (#261) / `docs/plans/0022-tiered-decision-routing.md` |
| 2026-06-11 | **PLAN-0020 (Procedure-path tuning) COMPLETE + archived to done/ (#251–#256, `a6125c1`, session 53)** _(rotated 2026-06-12, session 57)_ — the PLAN-0019 B-6 ring-fence follow-up. All `--dump-json`-VERIFIED on `gpt-oss:20b`/MS-S1: the Phase-1 aqua prompt nudge (PR #232, prev. UNMEASURED) worked dramatically — overall β `85.8%→100%`, aqua β `60%→100%`, overall α `70%→100%` (supply α `32.5%→100%`: model now picks `hold` not `inspect`). Latency lever: new `reasoning_mode=skip` (drop call-1 reasoning) cuts p95 `31.80s→21.62s` UNDER the 30s bar at **zero β cost** (`think_off` = dead lever). **SD-1** (widen supply-α) authorized at ratify but **SKIPPED at Step 9** — nudge made the divergence moot (0 `inspect`); anti-moving-target honored, no grader change. Also: per-judgment latency timer (#252), think-trim lever (#253), `ms-s1-ollama` skill (#254, `warm.sh` live-tested), tuning report (#255). Next: future PLAN for tiered handler grading (canonical/acceptable/forbidden — α too coarse); wiring `skip` into product path is an open audit trade-off | `a6125c1` (#251–#256) / `docs/plans/done/0020-procedure-tuning-latency-precision.md` + `benchmarks/procedure_baseline/REPORT.md` |
| 2026-06-11 | **PLAN-0020 ratified Draft→Accepted (#251, `19706eb`, session 53)** _(rotated 2026-06-12, session 57)_ — SD-1 = widen supply-α `valid_handlers` `[hold]`→`[hold, inspect]` (later skipped at Step 9, see close row); SD-2 = re-ratify the latency bar from **8 s/per-call → ≤30 s p95 per-judgment** (reports-not-gates). Unblocked the gated MS-S1 tuning campaign | `19706eb` (#251) / `docs/plans/done/0020-procedure-path-tuning.md` |
| 2026-06-10 | **PLAN-0021 SHIPPED (#249, `3dc586a`, session 51) — the Axis-B verification loop is LIVE; both harness-review tracks complete** _(rotated 2026-06-12, session 56)_ — goal gate (`_goal_gate.py` at the D4 seam inside `stop_continuation.py`, fail-open per ADR-0018 D4) + `goal-evaluator` 4th subagent + `/goal` (the repo's first project command) + the SD-1 narrowed-Write deny hook; +64 tests (suite 1398 passed / 22 skipped, zero regression); 7/10 case-matrix rows proven LIVE incl. the fail-open probe (`released-unevaluated` + LOUD Telegram, no wedge). F-L1: verdict→flip lands at the next non-chained Stop (OQ-8 blocking-mode promotion must account). Archived to done/ (`7d6d713`, same PR) | `3dc586a` (#249) / `docs/plans/done/0021-axis-b-verification-loop-build.md` |
| 2026-06-10 | **PLAN-0021 "Axis-B verification loop — build" landed as Draft (#247, `78b8659`, session 51)** _(rotated 2026-06-12, session 56)_ — Cowork-drafted per ADR-009 D1, Code R2-reviewed + committed per D2/D3; renders Accepted ADR-0018 into a build plan: 6 new files (incl. the repo's first project command `.claude/commands/goal.md`, the `goal-evaluator` 4th subagent, the SD-1 narrowed-Write deny hook), exactly 3 modified files at the D4 seam, 10 ACs incl. AC-2 byte-for-byte non-interference, 10-row case matrix, VX-1..3 resolved, OQ-8 Out of Scope. R2 **F-1**: the deny hook wires via agent frontmatter, not `settings.json`. Gates on Cray ratification (SD-1: Cowork recommends NO for v1) | `78b8659` (#247) / `docs/plans/0021-axis-b-verification-loop-build.md` |
| 2026-06-10 | **ADR-0018 "Axis-B Verification Loop" ACCEPTED (Cray-ratified, session 51) — opens harness-review track 2 (the evaluator loop) on top of the at-frontier Axis-A governance layer.** _(rotated 2026-06-12, session 56)_ A `/goal` Stop-hook gate + a `goal-evaluator` subagent that judges whether a run achieved its declared goal. **Decisions:** D1 hybrid deterministic-check + LLM-judge; D2 a `.claude/state/goal.json` run-goal artifact; D3 a 4th subagent sibling that **REFUTES not blesses** (structural guard against reasoning-blindness); D4 `_goal_gate.py` inside `stop_continuation.py`, **FAIL-OPEN** (broken/absent evaluator never blocks Stop); D5 session-Stop **warn-only v1**; D6 structural reasoning-blindness rationale; D7 formalize + augment the manual AC ritual. **SD-1 resolved = narrowed Write** (the evaluator's Write is hook-narrowed to `goal.json` only — same author-bounded pattern as `plan-drafter`/`status-scribe`). **Lineage:** #241 (`5f8073c`, `docs(adr):`) added ADR-0018 `Proposed` → **#242 (`1be60f7`, `docs(adr):`, head_commit) ratified it Proposed→Accepted** + carries the T4 STATUS reconcile (record ADR-0018 here + clear the Current-Focus Axis-B "deferred" earmark). **NEXT = T2:** Code dispatches the Axis-B build PLAN to Cowork (ADR-009 D1) → T3 (autonomy-triggers V-row) → build. OQ-8 (plugin packaging, MS-S1 local evaluator, blocking-mode promotion, PR-merge gating, auto-declared goals) + VX-1..3 stay non-binding / verify-at-execution | `1be60f7` (#241 + #242) / `docs/adr/0018-axis-b-verification-loop.md` |
| 2026-06-09 | **ADR-0017 "Skills as a memory tier" ACCEPTED — the skills-as-memory-tier governance arc is COMPLETE** _(rotated 2026-06-12, session 56)_ — #236 (`docs(adr):`, `7bf9d38`) added ADR-0017 `Proposed` (Cowork-drafted, Code-reviewed via the ADR-009 D3 receive sequence); #237 (`docs(constitution):`, `8b18b3a`, head_commit) ratified it (Proposed→Accepted) + applied the alignment (T1–T5). `.claude/skills/` is now **Tier 2.6** in the memory model (`CLAUDE.md` §4 + the memory-architecture runbook), git-tracked + auto-loaded by description match; the **D5 knowledge-placement decision rule** (binding→CLAUDE.md; durable learning→lessons; canonical reference→conventions/runbooks; task-triggered how-to→a Skill) + **D7 skill-authoring conventions** codified in the runbook; §1 gained the **D6** derived-precedence line (2.5+2.6 carry no independent precedence; canonical wins); §10 skills row cites ADR-0017. **Arc lineage:** PR #234 (`471bcb5`) added the `.claude/skills/` *mechanism* → #236 the *ADR* → #237 the *alignment*. This (T6) reconcile records the Accepted ADR, clears the §50/§57 "draft ADR-017" earmark, and marks the PR #234 skills follow-up governance-complete. Open threads: **OQ-B** skill-loader tie-break (delegated to Code; Cray-gated probe of global `~/.claude/skills/` host state) + the deferred **Axis-B verification-loop** track. Restart-bridge handoff due (#237 edited constitutional `CLAUDE.md`, Lesson #5 §1) | `8b18b3a` (#236 + #237) / `docs/adr/0017-skills-as-a-memory-tier.md` + `CLAUDE.md` §1/§4/§10 + `docs/runbooks/memory-architecture.md` |
| 2026-05-25 | **PLAN-0009 (Phase 3 — subagent topology) RATIFIED + Ready for execution + COMMITTED** _(rotated 2026-06-12, session 56)_ — Cowork drafted under interim ADR-009 D1 phasing; Cray adjudicated all 4 OQs (OQ-1…OQ-4) 2026-05-25 (WebFetch for Explore; no new ADR — execute ADR-013 D1; subagent identity folds with ADR-013 OQ-3 in Step 1; PLAN status vocabulary). Cowork → Code dispatch handoff at `.claude/handoffs/session-10/2026-05-25-1240-cowork-plan0009-review-dispatch.md` `validate_handoff.py` clean (K-1 / ADR-009 D3 substitute — 9 required fields, actor=cowork / phase=dispatch / status=READY / suffix=dispatch, ISO-8601 +07:00, filename matches `_FILENAME_RE`). Code fact-pack / R2 review clean across 9 citations (0009 next free; ADR-013 D1/OQ-1/OQ-3 quoted verbatim; PLAN-0008 4 carry-overs accurate; PLAN template structure intact; Cray verification-rigor directive present in Step 6 + Verification). Status flipped Draft → Ready for execution in commit `d10073e` on `feat/plan0009-subagent-topology` (single-doc, worktree-OFF per CLAUDE.md §11). **2 reconciliation findings folded** into Current Focus: (1) `.claude/` readability — K-2 is write-block NOT read-block (research-note §6); OQ-D load-bearing forcing fact remains K-1 (Cowork can't run `validate_handoff.py`), substantive deferral stands. (2) Working-tree divergence — git worktree sees neither uncommitted new files nor gitignored paths (research-note §6.1, reproduced live this session); not K-1/K-2 but checkout-resolution mismatch; design implication for Phase 3.5 if approved. **CLAUDE_TIER / session-identity unification** confirmed correctly folded in PLAN-0009 Step 1 (one mechanism, 3 identity cases: main Code may commit, Plan/Explore subagent must NOT, scheduled Local Code session may [Phase 3.5 HELD]). **Phase 3 execution gated on PR merge. HOLD Phase 3.5** (research-note §7.5 local scheduled-task poller option SURFACED, not decided) | `d10073e` / `docs/plans/0009-subagent-topology.md` + `.claude/handoffs/session-10/2026-05-25-1240-cowork-plan0009-review-dispatch.md` |
| 2026-05-25 | **PLAN-0008 AC-1 CORROBORATED via Auto mode bonus run + layer orthogonality CONFIRMED in production** _(rotated 2026-06-12, session 56)_ — A second AC-1 live verification run (2026-05-25 00:30–00:32) using **Mode = Auto** in a fresh worktree session: task `"สร้าง docs/CHANGELOG.md สรุป Phase 2 PRs #9-#17, commit บน branch ใหม่, ไม่ต้อง push"`, single Cray paste, no further input. Result: **≥ 4 auto-continues, 0 permission prompts (Auto mode skipped them all), 0 Telegram pings, terminal pause at commit done** (followed explicit "ไม่ต้อง push" instruction — no over-step). Commit `6dc808c` on branch `chore/phase2-changelog` (unpushed per instruction). **Layer orthogonality confirmed**: Mode (PreToolUse harness layer) ↔ PLAN-0008 (Stop classifier layer) operate independently — Auto mode eliminates per-tool prompts without changing Stop-continuation decisions. **Minor finding for PLAN-0009 carry-over**: `_loop_counter._normalize_file_path()` strips main-repo prefix but does not collapse worktree path suffix (L1 counter key showed `.claude/worktrees/busy-bose-eedc8f/docs/CHANGELOG.md` instead of `docs/CHANGELOG.md`). Non-blocking; per-session isolation works correctly. Both AC-1 evidence runs documented in Current Focus comparison table. Cost: ~$0.004 (4 classifier calls × ~$0.001) | PR #20 amendment / `docs/STATUS.md` |
| 2026-05-25 | **PLAN-0008 AC-1 VERIFIED — Phase 2 fully audited** _(rotated 2026-06-11, session 55)_ — Cray ran the live AC-1 task in a fresh Code session (task: *"ตรวจ ruff + mypy ทั้ง project, แก้ warning ถ้ามี, commit"*, single Cray paste, no further input). Agent self-continued **≥ 5 consecutive turns** without Cray paste (initial scan → file inspection → plan → branch creation → 5 file fixes → re-verify → tests → commit), then paused at the `git push` boundary asking permission — classifier correctly identified push as state change outside worktree per `feedback_state_change_outside_worktree.md` memory pattern. **0 Telegram pings** (no `cap_reached`, no L1–L4 false-positives). `stop-chain.json` `depth: 0` at end (consistent with terminal pause resetting chain). Side effect: the session surfaced 21 project-wide mypy errors in `tools/` + `tests/` (outside the pre-commit gate scope) and shipped a cleanup commit `8fef3a5` — PR #18 follows separately. Confirms classifier conservatism bias (spurious pauses > spurious proceeds, per OQ-B) works in production. Phase 2 all 4 ACs now VERIFIED; entry conditions for PLAN-0009 (Phase 3 — subagent topology) met | PR #19 amendment / `docs/STATUS.md` + closeout handoff §1 |
| 2026-05-25 | **PLAN-0008 Phase 2 COMPLETE — Step 8 closeout MERGED** _(rotated 2026-06-11, session 55)_ — PR #17 → `main` (`79fe373`), single `feat(claude)` commit `b3657d5` + merge. AC matrix at merge time: AC-2/AC-3/AC-4 VERIFIED; AC-1 deferred to live Cray-supervised observation (subsequent AC-1 row above closes this). Step 8 deliverables: +2 E2E tests (test_l3_traceback_inline_fires_on_threshold + test_l2_resets_on_pass_for_same_nodeid; 387 → 389 pass / 6 skip); closeout handoff at `.claude/handoffs/session-10/2026-05-25-0130-code-plan0008-phase2-closeout.md` (gitignored local working note per CLAUDE.md §11); `git mv docs/plans/0008-...md docs/plans/done/`; STATUS final bump. Phase 3 (subagent topology, ADR-013 D1 phased) entry conditions met. **Reflexive H1 hook fire on the closeout handoff frontmatter** (`phase: completion` initially invalid; corrected to `phase: closeout` per enum) — N=3 production-validation events through this session (L1 in PR #15, L1-attempt in PR #16, H1 in this PR) prove the deterministic + classifier-mediated layer is reachable from real agent activity | `79fe373` (PR #17) / `docs/plans/done/0008-harness-autonomy-layer-phase-2.md` |
| 2026-05-25 | **PLAN-0008 Step 7 (Phase 2 integration tests + mypy hook coverage extension) MERGED** _(rotated 2026-06-11, session 55)_ — PR #16 → `main` (`9100e65`), single `test(claude)` commit `d870d76` + merge. New `tests/handoffs/test_phase2_integration.py` with 15 E2E scenarios driving real subprocess invocations of all 3 wired Phase 2 hooks against a local mock HTTP Sonnet server (ephemeral 127.0.0.1 port via `socketserver.TCPServer` + threading daemon; `$CLAUDE_SONNET_API_URL` override; no live network). Coverage: Stop↔classifier wiring (proceed→block, pause→no-block, fail-closed, re-entry guard — mock receives 0 requests = negative proof); chain-cap fail-safe + cap_reached Telegram; observer→state→PreToolUse deny on L1+L4 + Cray-E.4 payload assertion; L4 reset on success; L2 inline Telegram on pytest-fail threshold; L1 turn-boundary survive vs reset; chain depth progression. Pre-commit `mypy` glob extended `^(services\|verticals)/` → `^(services\|verticals\|\.claude/hooks)/` (closes Step 1 follow-on; all 9 hooks pass `--strict`). 372 → 387 pass / 6 skip (+15). Per-test isolation via `tmp_path` for state + classifier fallback path + telegram capture + chain file. AC-3 demonstrated E2E for the first time | `9100e65` (PR #16) / `tests/handoffs/test_phase2_integration.py` |
| 2026-05-25 | **Cross-env Anthropic key file setup completed (Step 5b follow-up)** _(rotated 2026-06-11, session 53)_ — Code copied WSL `~/.claude/.anthropic_api_key` to Windows `C:\Users\crayj\.claude\.anthropic_api_key` with NTFS ACL tightened to `crayj` user only (SYSTEM + Administrators removed — strictly tighter than chmod 600). Both `Path.home() / ".claude" / ".anthropic_api_key"` resolution paths verified: WSL Python finds at `/home/crayj/.claude/...`, Windows Python finds at `C:\Users\crayj\.claude\...`. Hook firing path (Windows-spawned hooks) and pytest path (WSL-spawned via Bash tool) both unblocked for live Sonnet operations | `C:\Users\crayj\.claude\.anthropic_api_key` (NTFS user-only) |
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
