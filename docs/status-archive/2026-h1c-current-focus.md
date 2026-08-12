# STATUS.md — archived Current Focus blocks (2026 H1, continuation)

> ✅ **THIS FILE IS THE LIVE APPEND TARGET for Current-Focus rotations** (Cray-ratified 2026-08-06, session 212; runbook R4's scoped exception). New blocks go at the **BOTTOM**, in rotation order.
> **Period covered:** an original sessions 26 → 46 body (newest-at-top *within that body*), then **s192 onward appended at the bottom in rotation order** — s192–s196, s202–s206 as of s212. _[The old header claimed "sessions 26 → 46" alone; that was already false by s196 and is corrected here rather than restated.]_
> **Sibling chain — for THIS chain the NEWEST LETTER holds the NEWEST content** (the opposite of the `-status.md` chain): [`2026-h1b-current-focus.md`](2026-h1b-current-focus.md) (session 25) → [`2026-h1-current-focus.md`](2026-h1-current-focus.md) (**legacy base, closed to appends** — it stalled at 190,527 B against R4's ~192 KB bar) → [`2026-h1c-current-focus.md`](2026-h1c-current-focus.md) (this file, live). This chain is **Current-Focus-only** and is SEPARATE from the rotation archive's `2026-h1b/c/d/e/f/g-status.md` chain — same letter scheme, different corpus, **and now different append rules**.


Archived `## Current Focus` session blocks, rotated out of `docs/STATUS.md` on 2026-06-10
(session 51) so the always-read Tier-1 STATUS stays small — it had grown to 393 KB / >25k
tokens and could no longer be read in full (a single frontmatter line was 48 KB). Full
record also in git history (Tier 3). **Tier-3: grep + windowed reads only.**

**Split lineage (session 144).** The combined file stood at 258,346 B — 1.31x R4's ~192 KB
split trigger and ~3,798 B under its 256 KB cap, still receiving appends and therefore on
track to breach with nobody watching. R4 had no mechanism until #789; this chain is what
that guard forced. **No content lost:** every session block is preserved verbatim and
exactly once, verified by exact list equality at split time, not by a byte-sum estimate.

**Two honest notes, recorded rather than quietly fixed.**
1. The pre-split header claimed the file held "Session 46 and earlier". It did not:
   sessions 116/117/127/128 had been appended at the bottom by later deep-rotates, so the
   file carried two orderings at once. This chain gives each file one coherent window; the
   original claim is preserved here as the record of what it used to assert.
2. The `session 25` block is 162,823 B on its own — 83% of R4's trigger in a single
   indivisible block. `2026-h1b-current-focus.md` is therefore large by necessity, not by
   packing choice. It is frozen; nothing appends to it.

---

> **Session 46 — PLAN-0019 Step B-δ is COMPLETE (#222, `957a657`,
> `test(benchmark):`): per-call latency instrumentation + the SD-B1 p95
> measurement for the pin, plus the B-4/G-3 four-model selection sweep and a
> runner-robustness fix.** One `test(benchmark)` PR landed this turn
> (`test(benchmark): B-δ latency + G-3 model sweep (PLAN-0019)`), Cray-reviewed
> + merged via merge commit `19b816c`. **The headline outcome: the SD-B1
> latency bar is MISSED — and that is a *logged finding* → a follow-up tuning
> PLAN, NOT a build failure and NOT a reason to move the bar (B-6 ring-fence).
> The ADR-0001 pin `gpt-oss:20b` HOLDS.**
>
> **B-δ Part 1 — latency instrumentation (`a6d3f62`).** Added a
> `TimingChatClient` decorator (times each `chat()` call into a shared
> `LatencyRecorder`) + `percentile` (nearest-rank) + `summarize_latency` to
> `benchmarks/procedure_baseline/harness.py`; `run_benchmark` wraps its client
> and reports p95 vs a new `--latency-threshold` (default 8.0). Live
> `gpt-oss:20b` warm-first run (full 162 items / 168 calls): accuracy **97.6%
> (82/84)** this run — **run-to-run non-deterministic** (the #220 run was 100%;
> honest read **~98–100%**), the two misses **both inclusive-boundary breaches**
> (DO 4.0, 90.0 °C) → boundary cases are the failure mode; **latency mean
> 13.0 s / p50 12.1 s / p95 19.2 s / max 22.5 s → OVER the SD-B1 ≤ 8 s bar
> (~2.4×)** (the `think=True` call-1 reasoning dominates per-call time).
>
> **B-δ Part 2 — G-3 sweep (4 models) + runner robustness (`2476ff7`,
> `957a657`).** A robustness gap surfaced: a slow model exceeding the 120 s
> per-call timeout raised `OllamaError` and crashed the run → `evaluate_item`
> now records a transport error as an error-tagged failed proposal and
> continues (+1 test). Sweep (serialized so MS-S1 stayed quiesced; MS-S1 Ollama
> updated to **0.30.6**; pin ran 84 breach items, candidates a 9-item breach
> subset, each re-warmed):
> - `gpt-oss:20b` (20 B, pin): ~98–100% acc, **13.0 s mean / 19.2 s p95** —
>   best on both axes.
> - `gemma4:12b` (12 B): **100% (9/9)**, reliable JSON, **45.9 s mean / 81.1 s
>   p95** (clean, un-clipped).
> - `qwen3.6:35b` (35 B): ~87.5% (7/8; 1 timeout), 46.9 s mean / 120 s p95
>   (timeout-clipped). NB this **corrects the prior "qwen3.x = NOT_JSON" note**
>   — qwen3.6 DOES emit valid structured JSON on this build.
> - `gemma4:26b` (26 B): not measurable (8/9 errored — 7 timeouts + 1 malformed
>   JSON), 51.7 s mean / 120 s p95.
>
> **Key finding — smaller ≠ faster:** `gemma4:12b` (smaller than the pin) is
> ~3.5× SLOWER; per-call latency is dominated by generated-token count +
> architecture/quant, not param count. **G-3 conclusion (closes the evidence
> gap):** across 12 B–35 B the pin `gpt-oss:20b` is best on BOTH axes and ~3.5×
> faster than every alternative; going smaller did not help, so the latency miss
> is **not** a param-count problem and is **not** solved by any available model.
> **The pin holds.** Levers (trim the `think` pass / batching / a faster-arch
> small model not yet on MS-S1 / revisit the 8 s bar) belong to the follow-up
> tuning PLAN.
>
> All of B-δ **REPORTS — it does not gate** (B-6 ring-fence); the latency miss
> is a logged finding, not a build failure, and is not a reason to move the bar.
> Results live in `benchmarks/procedure_baseline/REPORT.md` (headline + sanity +
> latency + the 4-model G-3 table, all caveated). Verification: ruff clean;
> `mypy --strict` clean; offline benchmark suite **35 passed**; full suite
> **1336 passed / 2 skipped**. This block = the session-46 B-δ reconcile
> (head_commit `957a657` — the newest substantive commit per `lint_status`; the
> #222 merge commit `19b816c` is lint-excluded).
>
> **Next — remaining Part B, Cray to sequence.** **(ข) harden the benchmark**
> to give the headline discriminating power: ship **real, distinct action
> handlers** (so `suggested_handler` becomes a meaningful graded choice instead
> of trivial `echo`) + add **harder scenarios** (multi-entity sets, distractors,
> near-miss actions), then **re-run**. **Author a latency tuning PLAN** from the
> B-δ finding (trim the `think` pass / batching / a faster-arch small model /
> revisit the 8 s bar) — **must NOT reopen ADR-016's primitive shape
> (ring-fence)**. **B-3 baselines** — text-to-SQL + RAG comparison on the same
> questions (REPORTED, not gated) — the heaviest remaining sub-step. Then
> **B-5** report finalize + **B-6** ring-fence wrap. All via `test/*` PR(s). The
> benchmark RUN hits live `gpt-oss:20b` on MS-S1 (192.168.1.133:11434) — a
> host-state change, so **ASK Cray before warming/running.** Sequencing remains
> **Cray's call**.
>
> **Session 46 (earlier) — PLAN-0019 Step B-β is COMPLETE: the dataset was
> filled to SD-B2 size (#219, `73170d7`, `test(benchmark):`), then the harness
> was calibrated and the LIVE HEADLINE run was executed (#220, `ae7221a`,
> `test(benchmark):`).** Two `test(benchmark)` PRs landed this turn, each
> Cray-reviewed + merged. **The headline: LLM action-proposal correctness =
> 100.0% (84/84)** on the live `gpt-oss:20b`-on-MS-S1 run — clearing the SD-B1
> ≥85% bar, *with a load-bearing caveat* (it is a FLOOR, not a ceiling — see
> below).
>
> **#219 — fill the dataset to SD-B2 size (`73170d7`).** Grew the three seed
> datasets from ~7 to **54 items/vertical (162 total)** = the Cray-ratified
> SD-B2 size (~50–60/vertical). Breach-weighted: **28 breach / 13 watch / 13 ok
> per vertical (84 graded breach items total)**, with dense inclusive-boundary
> clusters (aquaculture DO 3.9 / 3.95 / 3.99 / 4.0; energy 90.0 / 90.1 / 90.3 /
> 90.5; supply_chain 8.0 / 8.1 / 8.2 / 8.3). The `tests/benchmark`
> self-consistency test asserts every item's declared disposition matches
> `classify_disposition`. Data + REPORT denominators only — offline.
>
> **#220 — calibrate the harness + run the live headline (`ae7221a`).** A
> pre-run smoke against live `gpt-oss:20b` on MS-S1 surfaced that the
> **harness, not the model, was mis-measuring**. Four **measurement-correctness**
> fixes were **Cray-ratified BEFORE the scored run** — anti moving-target: none
> moves the ≥85% bar or tunes-to-pass:
> 1. `scenario_to_event` now injects the domain `parameter`
>    (`dissolved_oxygen` / `temperature`) so the model knows *what* is measured
>    (faithful to a real ontology event); a required `reading_parameter` field
>    was added to the `Dataset` schema + the three dataset files.
> 2. `payload_contains` → **advisory** (recorded, not a headline gate) — the
>    live model's `handler_payload` keys are free-form (`event_id` / `action` /
>    `recommendation`, never the guessed `pond_id`); `FieldCheck` gained an
>    `advisory` flag.
> 3. `action_keywords` broadened to per-vertical action lemmas (aquaculture
>    `[aerat, oxygenat]`, energy `[restart, reset, reboot]`, supply_chain
>    `[hold, inspect, quarantine, divert]`).
> 4. `action_keywords` now searches `rationale` too (title / description /
>    rationale) — the model often places its proposed action in `rationale`
>    (the diagnostic showed every aquaculture "fail" already said "Aeration"
>    there).
>
> Smoke trajectory: **44% → 61% → 100%**.
>
> **Live run (all 162 items; 84 breach → 168 LLM calls; `gpt-oss:20b` on MS-S1,
> Cray-warmed + Cray-approved).** **Headline (LLM action-proposal correctness):
> 100.0% (84/84)** — aquaculture 28/28, energy 28/28, supply_chain 28/28 —
> clears SD-B1 ≥85%. **Deterministic disposition sanity: 100.0% (162/162).**
> **0 `StructuredOutputError`**; the inclusive-boundary breaches (DO 4.0 /
> 90.0 °C / 8.0 °C) all pass. `benchmarks/procedure_baseline/REPORT.md` records
> the result **with a load-bearing caveat**: the 100% is easy-by-construction
> (`echo`-only handler ⇒ `valid_handler` trivially satisfied; well-posed
> single-entity breaches), so it is a **FLOOR** — "the well-posed path works
> end-to-end," *not* "the model is infallible." Per the B-6 ring-fence this
> REPORTS, it does not gate. **Latency (SD-B1 ≤8 s p95/call) was NOT measured**
> — the runner isn't instrumented for per-call timing; that's B-δ. Verified
> across both PRs: ruff clean; `mypy --strict benchmarks tests/benchmark` clean;
> offline benchmark suite **30 passed**; full suite **1331 passed / 2 skipped**.
> This block = the session-46 B-β-complete reconcile (head_commit `ae7221a` —
> the newest substantive calibration+run commit per `lint_status`; the merge
> commits `c433fd6` (#220) / `42a6e52` (#219) are lint-excluded).
>
> **Next — Cray's chosen (ก)→(ข) sequence (to make the result more
> meaningful).** **(ก) B-δ next:** instrument the runner for **per-LLM-call
> latency** (p95 vs the SD-B1 ≤8 s bar) + run the **per-procedure
> model-selection sweep** (closes evidence-gap G-3); needs the available
> structured-output-capable local models on MS-S1 (gpt-oss:20b is the ADR-0001
> pin; qwen3.x = NOT_JSON). **(ข) then harden the benchmark** to give the
> headline discriminating power — ship **real, distinct action handlers** (so
> `suggested_handler` becomes a meaningful graded choice instead of trivial
> `echo`) + add **harder scenarios** (multi-entity sets, distractors, near-miss
> actions), then **re-run**. Then **B-γ** (text-to-SQL + RAG comparison
> baselines, REPORTED not gated) + **B-5** report finalize + **B-6** ring-fence,
> all via `test/*` PR(s). Live runs hit `gpt-oss:20b` on MS-S1
> (192.168.1.133:11434) — a host-state change, so **ASK Cray before
> warming/running.** Sequencing remains **Cray's call**.
>
> **Session 46 (earlier) — PLAN-0019 Step B-β SCAFFOLD landed (#217,
> `367503c`, `test(benchmark):`) — the FIRST Part B build PR.** A
> scaffold-first, OFFLINE thin slice of the procedure-baseline benchmark proves
> the Cray-ratified **SD-B1 graded-unit-A** design end-to-end *before* mass
> dataset authoring — design-risk retired before authoring-cost is spent.
>
> **What landed.** A new top-level **`benchmarks/procedure_baseline/`** package
> (kept OUT of `services/` per PLAN-0019 §2.1 review-separation) + offline tests
> under `tests/benchmark/`, on a `test/*` branch per the Part B PR-boundary
> rule. Modules: **`schema.py`** — `Scenario` / `Expected` / `BenchmarkItem` /
> `Dataset` Pydantic models (`extra="forbid"`); **`loader.py`** — pure
> `ruamel.yaml` → validated models (matches
> `services/engine/procedures/spec.py`); **`grader.py`** —
> `classify_disposition` **reuses the engine's own `crosses_threshold`**
> (`services/engine/recommender.py`) as the single source of truth for the
> breach decision, then layers the watch band, and `grade_proposal` does
> objective field checks (affected-entity PK / valid_handlers / `handler_payload`
> subset / action-class keywords); **`harness.py`** — `evaluate_item`
> (deterministic disposition → if breach, run the live two-call
> `generate_judgment` → grade the `LlmJudgment`) + `summarize` (keeps the
> **headline** vs the **deterministic sanity** number SEPARATE per SD-B1);
> **`run_benchmark.py`** — a live runner **SKELETON** (manual; hits
> `gpt-oss:20b` on MS-S1; **NOT collected by CI** since `testpaths = ["tests"]`);
> **`dataset/{aquaculture,energy,supply_chain}.yaml`** — ~7 human-authored seed
> items/vertical spanning breach/watch/ok including the inclusive boundary
> (aquaculture DO 4.0; energy/supply_chain thresholds **provisional**, pinned vs
> the ontologies during the FILL PR); **`REPORT.md`** — a B-5 placeholder
> carrying the B-6 ring-fence header up front.
>
> **Graded unit (SD-B1).** The headline = **LLM action-proposal correctness**
> (target **≥ 85%**) on the breach subset (right entity / valid handler / action
> class / payload); the deterministic `evaluate` routing is reported
> **separately** as a **~100% sanity** check (NOT folded into the headline);
> watch/ok items are the false-positive guard (no LLM call). This is exactly the
> separation Code pinned at SD-B1 ratification — accuracy is graded on the LLM
> reasoning path, never on the ~100%-by-construction threshold rule.
>
> **Tests.** 28 offline tests under `tests/benchmark/` (mock `ChatClient`,
> Lesson #7 §3) — grader bands + objective checks, loader + **dataset
> self-consistency** (every seed item's declared disposition matches the
> classifier; all three dispositions covered per vertical), and the harness
> end-to-end (breach → graded; watch/ok → deterministic guard with no LLM call;
> `StructuredOutputError` → incorrect proposal; `summarize` splits the two
> metrics). **Additive only** — no existing files touched. Verified: ruff clean;
> `mypy --strict benchmarks tests/benchmark` clean; full suite **1329 passed /
> 2 skipped** (+28). This block = the session-46 reconcile (head_commit
> `367503c` — the newest substantive per `lint_status`; the merge commit
> `efb412e` is lint-excluded).
>
> **Next (the FILL).** The design is proven offline, so the next step is to
> **fill the dataset**, not re-architect it. **Step B-β FILL:** grow the seed
> set (~7/vertical) to **~50–60/vertical (~150–180 total)**, weighted to breach
> + boundary; verify each vertical's exact `scenario` fields + `crosses_threshold`
> thresholds against the real ontologies (aquaculture DO 4.0 below-boundary
> confirmed; energy/supply_chain provisional → pin vs `*_v0.yaml`); calibrate the
> live `handler_payload` key shape — **OFFLINE (mock `ChatClient`), via `test/*`
> PR(s)**. Then **B-γ** (text-to-SQL + RAG comparison, REPORTED not gated) +
> **B-δ** (per-procedure model-selection sweep, closes G-3) + **B-5** report +
> the **B-6** ring-fence. The live benchmark **RUN** (B-γ / B-δ) hits live
> `gpt-oss:20b` on MS-S1 (192.168.1.133:11434) — a host-state change, so **ASK
> Cray before warming/running.** Sequencing remains **Cray's call**.
>
> **Session 45 — PLAN-0019 Part B pre-registration RATIFIED *in the
> binding plan* + the L1 loop-detect guard fixed → the HARD GATE is CLEARED;
> Part B is GO.** Two PRs landed this session.
>
> **Step 0 — ratify Part B into PLAN-0019 §8 (#214, `9d98f03`,
> `docs(plans):`).** The Cray-ratified Part B surfaced decisions were ratified
> in conversation but not yet written into the binding plan — this PR closes
> that anti-moving-target gap before any dataset authoring. **SD-B1 → ✅
> RATIFIED** (numbers unchanged: procedure-recommendation accuracy ≥ 85%, p95
> per-LLM-call latency ≤ 8 s on `gpt-oss:20b`; #211 had added the operational
> definitions but left the §8 header in "Recommendation" framing — now flipped).
> **SD-B2 → ✅ RATIFIED: ~50–60 questions/vertical (~150–180 total)** — Cray
> chose the larger set over the draft's ~30/vertical for external-grade
> statistical defensibility (~30's ±~13pp CI was too wide). **SD-B3 → ✅
> RATIFIED: DEFER** — the G-2 build-cost-via-`new-vertical`-generator measure
> stays out of Part B (the generator isn't built, and it's tangential to engine
> quality). The PR also flipped §1's "B-side SDs stay open" → all ratified,
> fixed a stale `SD-B3`→`SD-B2` cross-ref in AC B-1 / Step B-β / the §8 header
> note, and set frontmatter `status: Draft` → `In execution`. Authored by the
> `plan-drafter` subagent (6 of 8 edits) + Code (the 2 remaining SD-B2/SD-B3
> flips, after an L1 loop-detect turn-boundary reset).
>
> **The L1 fix — path-class threshold + subagent-completion reset (#215,
> `d96e69f`, `fix(hooks):`).** The L1 loop-detect guard was false-firing on
> legitimate documentation authoring — it bit this very session: the
> `plan-drafter` subagent's 6 edits to PLAN-0019 exhausted the flat-6 turn
> budget, so the main agent couldn't add even one more edit. Fix:
> `_loop_counter.l1_threshold_for` now returns **6 for code paths (unchanged),
> 15 for prose/doc paths** (`*.md` / `docs/` — finite, so a stuck doc loop
> still trips), and `posttooluse_progress_observer._handle_agent_completion`
> resets L1 for files touched this turn when an `Agent` / `Task` tool completes
> (so a subagent's edits no longer pre-spend the main agent's budget). The deny
> message + `.claude/autonomy-triggers.md` row L1 were updated, and **Lesson
> #0021** records it (sequel to Lesson #0012). This was Cray-approved per-diff
> self-modification — the auto-mode classifier correctly denied the first
> attempt as self-modification under a mere direction pick; Cray chose "A now,
> B later", deferring distinctness-based counting (option B) as a follow-up.
> Verified: ruff + mypy --strict (`.claude/hooks`) clean; full suite **1301
> passed / 2 skipped** (+25 tests). The fix is now LIVE in the working tree, so
> this very reconcile authors under the 15-threshold. This block = the
> session-45 reconcile (head_commit `d96e69f` — the newest substantive per
> `lint_status`; the two merge commits `3f505a9` / `bacdf8d` are lint-excluded).
>
> **Next (the HARD GATE is now cleared).** Part A is COMPLETE and the full
> Part B pre-registration is RATIFIED in the binding plan, so **Part B is GO.**
> **Next = Step B-β:** author the synthetic ground-truth dataset (~50–60
> questions/vertical ≈ 150–180 total) over the three example procedures, graded
> as procedure-recommendation correctness on the LLM `action`-reasoning path vs
> a controlled key (the SD-B1 definition) — **OFFLINE, no live LLM (mock
> `ChatClient`)**. Then B-γ (text-to-SQL + RAG comparison, REPORTED not gated) +
> B-δ (per-procedure model-selection sweep, closes G-3) + B-5 report + the B-6
> ring-fence, landing via `test/*` PR(s). The benchmark RUN (B-γ / B-δ) hits
> live `gpt-oss:20b` on MS-S1 (192.168.1.133:11434) — a host-state change, so
> **ASK Cray before warming/running.** Sequencing remains **Cray's call**.
>
> **Session 44 — PLAN-0019 Part A COMPLETE → the HARD GATE.**
> The two final Part-A steps landed via **#208 (`5b2c189`, `feat(engine):`)**.
> **A-ζ** authored the three example `procedures.yaml` (config only, no new
> executors): the aquaculture **"Morning Pond Health Round"** headline
> (`read_do` query → `judge` evaluate → `aerate` **gated** action over the
> breach subset via the named-input fan-out `input: {from: judge, where:
> {verdict: breach}}` → `visual` **human_task** over the watch subset →
> `summary` **auto** action over the whole verdict set), plus energy
> **"Substation Health Sweep"** and supply_chain **"Cold-Chain Excursion
> Sweep"** (each a `query → evaluate → gated action` path). Every action routes
> through the `echo` handler (the only one registered; the intended
> `start_emergency_aerator` / `restart` / `hold` `action_type`s are noted in the
> specs but deferred to demo polish, per the session-43 fork). A new pure-Python
> load test (`test_example_procedures.py`, 10 cases) asserts all three load +
> validate (cross-refs resolve, named-input references are linear/backward,
> handlers are allowlisted). **A-η** added the headline end-to-end integration
> test (`tests/services/db/test_procedure_headline.py`, DB-gated): it drives the
> **real shipped** aquaculture headline manually with FAKE `query` / `evaluate`
> / `human_task` executors + the **REAL** `ActionStepExecutor` (mock
> `ChatClient`, no live LLM) and asserts behaviourally (Lesson #7 §3) — the
> breach/watch fan-out, the durable suspend → `resolve_gated_step(approve)` →
> resume lifecycle (`echo` fires once per breach pond; the run reaches
> `completed`), the auto summary over the whole set, the telemetry seam on every
> `StepResult`, and **reject = continue + record** (a rejected breach never
> fires its handler, yet the run still completes). Purely additive — no engine
> code touched. Verified (**AC A-12**): ruff + ruff-format + mypy --strict clean
> (47 files); full suite **1276 passed / 2 skipped** (+12; DB tests run live).
> **Part A (A-1…A-12) is DONE and the engine is demo-able → the HARD GATE is
> reached.** Cray reviewed + merged #208; Code landed the frontmatter STATUS
> reconcile (#209). This block = the session-44 reconcile (head `5b2c189`;
> merges `5af7271` / `2548479`).
>
> **Next (gated by the HARD GATE).** Part B (the benchmark) does **not** start
> until **SD-B1** thresholds (candidate `evaluate`-accuracy ≥ 85%, p95 step
> latency ≤ 8 s on `gpt-oss:20b`) are **Cray-ratified** first (anti
> moving-target). The text-to-SQL + RAG comparison is **REPORTED, not gated**;
> below-threshold = a logged finding → a follow-up tuning PLAN that must not
> reopen ADR-0016's shape (ring-fence; closes G-3). **SD-B2** (synthetic dataset
> ~30/vertical) + **SD-B3** (G-2 build-cost, lean DEFER) also stay open. Part B
> lands via a `test/*` PR. Sequencing remains **Cray's call**. See the handoff
> `.claude/handoffs/session-44/2026-06-08-1434-code-session44-procedure-engine-a-zeta-eta.md`.
>
> **Session 43 — PLAN-0019 Part A engine FEATURE-COMPLETE: A-ε (A-7 + A-8) +
> the named-input fan-out.** Three `feat(engine)` PRs, each Cray-reviewed +
> merged with a STATUS reconcile. **A-8 goal injection (#202, `e857c14`)** —
> `Procedure.goal` (a trusted authored directive, ADR-016 D5) is threaded into
> the LLM system prompt for `evaluate` + action reasoning (both Pattern-B calls)
> and onto `RunContext.goal`; the `goal=None` default keeps the reactive path
> byte-identical. **A-7 action-step adapter (#204, `56ab5f3`)** — the real
> `action` `StepExecutor` (`services/engine/procedures/action_step.py`): per
> entity it builds an ADR-007 `RecommendedAction` (envelope UNCHANGED;
> `suggested_handler = step.handler`, allowlist-bounded) with reasoning via the
> mockable `generate_judgment`, and routes through the shipped
> `approve()` → `execute()` gate **verbatim**. **Option 2 (external gate):**
> `gated` actions only PROPOSE → suspend; `resolve_gated_step` applies the
> human's approve/reject, rewrites the step `output_set`, persists; a plain
> `resume_run` continues. **Reject = continue + record** (the handler never
> fires, the rejection is recorded in the trace, the run reaches `completed` not
> `failed`); `auto` actions approve + execute inline. **A-ζ-prep named-input
> (#206, `42739b8`)** — the orchestrator keeps a NAMED-OUTPUT BAG (each step's
> output keyed by `step_id`); `Step.input` became structured `StepInput {from,
> where}` (`from` = a named prior step, default = the immediately prior one;
> `where` = a field-equality filter), enabling the breach/watch/ok fan-out, and
> `resume_run` rebuilds the bag from the DB across a restart. Three genuine
> design forks were each decided **with Cray** (AskUserQuestion) before
> building: the Option-2 external gate, reject = continue + record (grounded in
> a Palantir staged-Action research pass), and named-input over pass-through.
>
> **Session 42 — PLAN-0019 Part A build STARTED: the first build PR
> landed (#195, `6ef3a57`, `feat(engine):`) — the Procedure spec layer
> (Step A-α) + run-record persistence (Step A-β).** ADR-0016 Phase 1 is now in
> execution. This PR delivered the `Procedure / Step / Agent` Pydantic **SPEC**
> models + a `ruamel.yaml` loader (`services/engine/procedures/spec.py`), and
> the durable **`pipeline_runs` / `step_results`** ORM + Alembic migration
> **`0002`** (`services/engine/procedures/runs.py`). It is **additive only — NO
> orchestrator yet**; the ADR-007 `RecommendedAction` envelope + the ADR-008
> ontology are untouched. The **D3 autonomy invariant** is enforced in the spec
> (autonomy on `action` only, default `gated`; a non-action step that sets
> autonomy is rejected); the **per-step telemetry seam** (`duration_ms` BIGINT +
> `reasoning_trace` + `audit` JSONB) that Part B consumes is in place (**AC
> A-9**); `trigger ∈ {manual, schedule}` both load but only **`manual`** is
> runnable in Phase 1 (L-1). **Acceptance landed: A-1** (spec loaders), **A-2**
> (run records + migration), **A-9** (telemetry columns), **A-12** (ruff +
> mypy --strict + full suite green: **1221 passed / 2 skipped**; DB tests run
> live — migration applies + ORM round-trips). The energy DDL↔ORM parity guard
> (`tests/services/db/test_schema_parity.py`) was scoped to the energy ontology
> module since the new tables share `Base.metadata` but are cross-vertical
> engine infra. **Drafted + verified + committed by Code.** This PR = the
> session-42 Part-A reconcile (head `6ef3a57`; merge `f9d613d`).
>
> **Earlier this session — PLAN-0019 (Core Procedure baseline, Phase 1)
> earmarked, drafted, reviewed, and committed via #193 (`69c1ddf`,
> `docs(plans):`).** ADR-0016's Phase 1 got its executable plan: PLAN-0019 was
> G2-approved by Cray, drafted by the `plan-drafter` subagent, reviewed by Code
> (reuse symbols verified against the live
> `services/engine/{actions,recommender,registry}.py`), and committed via #193.
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
> **Next (gated).** PLAN-0019 **Part A is well underway** — spec (A-α),
> run-record persistence (A-β), and the orchestrator control plane (A-γ, #197)
> have landed. Next build step = **A-δ durable suspend/resume** (persist the
> in-memory `PipelineRun` / `StepResult` records; resume a `waiting_human` run
> from its suspended step across a process restart), then **A-ε** action-step
> adapter + goal injection → **A-ζ** three example procedures → **A-η** headline
> integration test, each via a `feat/*` PR. The **HARD GATE** precedes Part B;
> **SD-B1 thresholds must be Cray-ratified before any Part B run**. Sequencing
> remains **Cray's call**. Reference the still-active handoff
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

## Rotated this reconcile (session-196, 2026-07-31 — the wall-clock root-fix reconcile; PLAN-0099 drafted + merged, #1003)

Session 192's Current Focus block, rotated out when session 196's block entered the 4-session window.

> **Session 192, 2026-07-30 (head_commit `99b752f` → `5dd8ce6`) — the session the
> case → run link got a real oracle, and the oracle found two defects in code that
> already looked merge-ready.** One PR merged (#979), 0 open. **PLAN-0096 Step 8
> build-order item 3 is COMPLETE:** `repair_case_run_link` plus the `on_resolved`
> gate seam, proven on **both** `resolve_gated_step` and `ratify_gated_step`.
>
> **The hold was the point.** s191 built item 3 and deliberately did NOT merge it —
> clean code, `mypy --strict` clean, and **zero tests on the `ratify_gated_step`
> call site**, which is the entire reason the seam has two call sites. Four scenario
> tests then came up red with `no principal resolved for constrained step 'intake'`,
> and that was **not a bug**: `POST /procedures/{id}/run` records `step_principals`
> from `auth.person`, authn was off, so the round carried no requester and
> `_enforce_principal_sod` correctly refused the later approval. Fixed **at the
> cause** — the round now fires as an authenticated ต้อม (`req-mechanic-tom`, a
> declared fleet principal), so SoD passes on its **merits**, two distinct humans,
> instead of being skipped. The s191 handoff had proposed dropping to a direct
> `run_procedure` call; declined, because it would contradict the module's own
> docstring claim to drive the real run endpoint.
>
> **Defect 1 — the hook read the wrong half of the artifact.** `resolve_gated_step`
> writes `{"output_set": executed_effects, "decisions": decided}` and says why:
> *"executed effects thread forward; rejects are recorded, not threaded"*. Both
> `gate_hooks.vertical_of` and `link_resolved_cases` read `output_set`, so a case
> the approver **turned down** was absent entirely — `LINK_OUTCOME_REJECTED` was
> unreachable code — and an all-reject round left `output_set` empty, so the hook
> never dispatched at all. New `gate_hooks.decided_entries()` reads `decisions` (the
> complete per-action record, carrying the FINAL status), falling back to
> `output_set` for `auto` steps that never passed a human gate.
>
> **Defect 2 was visible ONLY after defect 1 was fixed.** `_outcome` let the
> run-level ratification state outrank the per-proposal status, stamping a REJECTED
> case `provisional` — the month-end export would have chased เฮีย for a signature
> on spend that never happened. **Cray typed the rule: a refusal is checked FIRST** —
> a declined repair has nothing to ratify and is already a complete, traceable
> decision; the ratification obligation belongs to the **run**, so it rides along on
> every case that gate touched, including the ones turned down.
>
> **Five non-vacuity probes**, each restored from a backup **copy** and
> `diff`-verified byte-identical (never `git checkout`): M1 delete the ratify
> `fire_on_resolved` → exactly the 2 ratification tests; M2 read `output_set` again
> → exactly the 2 rejection tests; M3 revert the `_outcome` ordering → exactly the
> waiver-reject test; M4 never arm the hook → all 7; M5 drop the idempotency guard →
> the double-fire test **and** both ratify tests, via `failures()` catching the
> swallowed `IntegrityError` — s191's assert-the-component-is-healthy design proving
> itself non-vacuous. Suite **3597 → 3604** (7 new tests). ruff + ruff format clean,
> `mypy --strict services/` clean over 127 files, registration guard + R7 + R8 exit
> 0, CI `gate` pass, merge-commit tree equality `git diff e443cb7 HEAD` = **0
> bytes**, and the full suite re-run **on the merge commit** (CI is PR-only).

---

## Current-Focus block — Session 193

Rotated out when session 196's SECOND workstream block entered the 4-block window (PRs #999–#1002).

> **Session 193, 2026-07-30 (head_commit `5dd8ce6` → `367c15b`) — the session the
> month-end export went from zero lines to a downloadable file with a KPI that can
> fail.** Six PRs merged (#982–#987), 0 open. PLAN-0096 **Step 8 item 5 COMPLETE**;
> **Step 10's AC-12 evidence written** — four coverage matrices, seven named residual
> risks, a confidence statement, in `.claude/handoffs/session-193/` (gitignored).
>
> **The build, in five PRs.** #982 the reader, whose row set is a UNION: cases with a
> `gate_decision` in the month, filed on the APPROVAL date, **∪** close-outs in the
> month with no governed run at all, filed on `entered_at`. That second source is the
> whole point — a naive export reports 100% traceability *by construction*, because the
> rows it cannot explain are the rows it never selected. #983 the KPI + cover: **Cray
> typed rule (ค)** — a row counts only if it was governed AND fully documented;
> governance-only would score a perfectly-approved repair with no invoice at 100%,
> paperwork-only would score escaped money as traceable the moment a tidy invoice was
> keyed. `vat_thb` and `cost_center` are deliberately NOT required — a garage that is
> not VAT-registered; and requiring the unfilled `cost_center` would pin the KPI at 0%
> forever. #984 **Cray typed (ก)**: persist `three_quote_basis` (alembic `0022`) rather
> than recompute it — recomputing would answer last month's audit question with this
> month's threshold *while looking completely filled in*. #985 the CSV + router, the
> repo's **first** export surface, UTF-8 **with BOM** because Excel on Windows mojibakes
> Thai without one. #986 the E-2 exception report on the cover.
>
> **Two defects were found by ORACLES, not by review — the useful half.** A probe
> mutating `is_fully_traceable` so its governed/outcome guard never fires left the suite
> **GREEN**: the guard was unreachable through `load_monthly_export`, which already
> nulls the approver when there is no decision, so nothing tested it on its own terms;
> four direct predicate tests now do. And the **end-to-end scenario found a real bug** —
> the hero round decides the demo fixture cases alongside the real one, and rejecting
> them produced link rows with no approver, invoice or amounts, landing in the export as
> **฿0 Express entries** an accountant would have to key to record that nothing
> happened. No unit test could have shown it; every fixture built exactly the rows its
> author had in mind. `is_reportable` now states the rule: money exists → always a row
> (a REJECTED case *with* a close-out is the worst case in the report);
> authorised-but-unpaid → a row; neither → not spend.
>
> **28 non-vacuity probes**, each restored from a backup copy and diff-verified. Two did
> not redden and were treated as findings rather than passes: one exposed the untested
> guard above, the other that **a probe whose mutation is a semantic no-op measures
> nothing while reading as a pass**. AC-9's bar is demonstrated on the real path, not
> asserted (archived PLAN, §Acceptance Criteria).
>
> **Also:** #987 corrected a **public-repo** overclaim — README and
> `docs/conventions/tech-stack.md` described pgvector + Apache AGE + pg_trgm as the
> database when `docker-compose.yml` runs stock `postgres:16-alpine`. STATUS had carried
> the corrected framing since s141 and never propagated it to the two files a *reader*
> hits first; two dead pointers fell out of the same pass. Suite **3607 → 3646**; `mypy
> --strict services/` 127 → **130**; dev DB `0021` → **`0022`** on Cray's go against five
> criteria fixed before the run. MS-S1 never touched; LINE still disarmed. **R2/R4
> rotation applied** — s186→187 block + s179 RD row out; the archive base spilled
> sessions-142→171 into the new `2026-h1g-status.md` (numbers in the chain note below).

> _Older content rotates out of this file per the **STATUS.md Rotation Policy (R1-R8)** in [`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md) (Lesson #23): Current Focus keeps the 4 newest sessions (<=8 blocks); Recent Decisions keeps the last 10 rows. Rotated blocks/rows live in [`docs/status-archive/`](status-archive/) and git history (Tier 3). Layout — **two separate chains, both with letters ascending with time and the base holding the recent window**: the rotation archive `2026-h1b` → `c` → `d` → `e` → `f` → `g` → `2026-h1-status.md`, and the Current-Focus-only `2026-h1b` → `c` → `2026-h1-current-focus.md`. Rotations append to the two bases. **Grep the directory, not a filename** — the chain is one corpus and which file holds a given block is an artifact of where the ~192 KB R4 bar happened to fall. _[Chain created 2026-07-17 (s144): the single `2026-h1-status.md` had reached 592,577 B, 2.3x R4's cap, and the new guard (#789) forced the split. `g` added 2026-07-30 (s193): the base had returned to 194,232 B with a ~10.7 KB block due to rotate in, so sessions-142→171 spilled and the base dropped to 46,215 B.]_


<!-- rotated 2026-07-31, session 197 (STATUS reconcile, PR after 687705d) -->
> **Session 194, 2026-07-30 (head_commit `367c15b` → `b25cc98`) — two rotted-pointer
> repairs landed, and Cray ruled the standing STATUS-size TODO.** Two PRs merged
> (#990, #991), 0 open.
>
> **#990 — ADR-0025's archive pointer was wrong by whole FILE, not by offset.** It cited
> a line range in `docs/status-archive/2026-h1-status.md`; that base was **re-chartered**
> at the s144 split as the rolling recent window, so the target had long since migrated
> to a lettered sibling. Repaired by citing `2026-h1c-status.md` **by section heading,
> with no line numbers** — § "Current-Focus block — Session 84 (cont.; head_commit
> `f56a6e8`)" — per the house rule that headings survive an edit and line numbers do not.
> **Pre-existing rot from s144**, whose repair sweep fixed three pointers of this shape
> and missed one; **not** caused by the s193 R4 split, which preserved every heading.
> N=1 — no sibling rot in `docs/adr/`. Drafted by `plan-drafter` (ADR-0025 is Accepted →
> G1-denied to Code), Code R2'd.
>
> **#991 — PLAN-0097 drafted (`Status: Draft`), and the finding is that the standing
> TODO's PREMISE was wrong.** That TODO read the goal gate's silent warn path as
> *ratified behaviour*, which made any fix an ADR-0018 amendment question. It is not:
> **D5** says verbatim *"v1 is warn + annotate … records the verdict trail in the goal
> file"*, and **V2-D1** (ratified 2026-07-13, with the warn path already built)
> re-describes the default tier as *"warn + annotate + Telegram"*. The spec's step 5
> omits the record and the implementation followed the sketch — so the silence is an
> **implementation gap against a ratified Decision, not a ratified design**. **Third
> instance of this class** (ADR-0034 D3(3) vs D3(6) at s186; D3(3)/D3(4) at s188): a
> Decision's prose and its own procedural sketch disagreeing, code following the sketch.
>
> **Cray typed three calls.** (1) **PLAN-0097 SD-1 = (a): D5 controls** — the trail entry
> is licensed by ADR-0018 as it stands, no amendment needed; recorded at the PLAN's SD-1
> and as a discharged gate at Step 0, with Appendix A's contingency amendment retained
> but marked NOT applied / superseded, and `docs/adr/0018-*.md` untouched. **SD-2 and
> SD-3 were NOT ruled and stay OPEN.** (2) **STATUS size = tighten the per-block cap +
> cut duplicated content**, declining both "widen the rotation window" and "accept the
> trade". (3) **Next build ordering #3 → #1** — the fleet demo showability work
> (surfacing the month-end KPI + export in the console UI) goes first.
>
> **Ruling (2) is applied in this same reconcile.** STATUS measured **59,820 B** against
> R1's 49,152 B soft target. Runbook §R2 gained a **per-Current-Focus-block cap of
> ≤ 4,096 B** — the count caps bounded how *many* blocks, never how *large* one may be —
> and its existing "RD rows are pointers, ≤ ~600 chars" rule was measured **unenforced**,
> 8 of 10 rows over, worst 2,660 B. This pass rewrites every RD row to that cap, brings
> each retained block under the new cap, and cuts the PLAN-0096 In-Flight entry to a
> pointer. **The R2 carve-out bound the work**: nothing was trimmed until its substance
> was verified present in a tracked file.

> _Older content rotates out of this file per the **STATUS.md Rotation Policy (R1-R8)** in [`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md) (Lesson #23): Current Focus keeps the 4 newest sessions (<=8 blocks); Recent Decisions keeps the last 10 rows. Rotated blocks/rows live in [`docs/status-archive/`](status-archive/) and git history (Tier 3). Layout — **two separate chains, both with letters ascending with time and the base holding the recent window**: the rotation archive `2026-h1b` → `c` → `d` → `e` → `f` → `g` → `2026-h1-status.md`, and the Current-Focus-only `2026-h1b` → `c` → `2026-h1-current-focus.md`. Rotations append to the two bases. **Grep the directory, not a filename** — the chain is one corpus and which file holds a given block is an artifact of where the ~192 KB R4 bar happened to fall. _[Chain created 2026-07-17 (s144): the single `2026-h1-status.md` had reached 592,577 B, 2.3x R4's cap, and the new guard (#789) forced the split. `g` added 2026-07-30 (s193): the base had returned to 194,232 B with a ~10.7 KB block due to rotate in, so sessions-142→171 spilled and the base dropped to 46,215 B.]_

> **Session 195, 2026-07-31 (head_commit `b25cc98` → `a8912e0`) — four PRs merged
> (#994–#997), 0 open. The theme: a documented claim that measurement refuted, four
> times in four places.**
>
> **#994 — fleet's Box-4 ฿ facet, the last config-shaped half of ADR-0032 D1.** Fifth
> economic producer, first **event-anchored** one: procurement's OQ-C fell back to a hero
> PO (its events carry a criticality score, not a ฿ anchor), but a fleet repair-quote
> event *is* the money (`measured_value`, `unit == "THB"`) — baseline = an uncompared
> price, governed = the same repair after the three-vendor comparison the partner adopted
> after being defrauded on parts. **Cray typed the basis** (event-anchored + the
> partner's own ฿30,000 threshold, over an assumptions-first exemplar and a DB read empty
> at `row_count: 0`) **and the 15% recovery fraction** over a fraud-sized 25%. The
> threshold is **imported from `sourcing.py`**, so producer and gate cannot drift; no ADR
> amendment needed (ADR-0030 D3 leaves `kind` a free `str`). `test_golden_e2e`'s donor
> oracle fired as designed; the exclusion is **surgical**.
>
> **#995 — a REAL production defect, not a hardening.** `decide_pm_import` read a row's
> status then wrote it on an **unlocked** read, so two deciders could both observe
> `proposed`, both pass the 409 guard, and the later commit would overwrite the earlier
> decision — stamping the loser's `decided_by` on a row someone else had ruled on,
> **while both callers got a 200**. The guard's own "idempotent BY STATE" comment was
> true for a *replay*, false for a *race*. Fixed with `FOR UPDATE` on the decide path's
> read only (the review GET must not lock), no migration — Code's call over a version
> column, veto open.
>
> **#996 / #997 — PLAN-0097 built and CLOSED (7/7 ACs, archived).** The warn arm was the
> only terminal outcome in `_goal_gate.py` that wrote nothing; it now records before it
> pings. Load-bearing is what the entry is **invisible to**: `_last_decision_evaluation`
> excludes warn entries from every decision read, or two untested corners change
> behaviour (flake would skip a dispatch; enforce-flip would double-block). **Cray typed
> SD-2 = yes** (first-class `Evaluation.detail`) **and SD-3 = dedup** (marker + same
> non-empty fingerprint; empty always records).
>
> **The theme, four times.** The allocator docstring named the wrong constraint; AC-6
> predicted M6 would redden the ladder tests and it does not, so the enforce fence was an
> **untested** property M6 would have passed silently; the s194 RR-3 estimate was
> over-scoped; and **two of eight mutation probes were themselves defective** — one
> mutated the wrong site (its anchor recurs earlier), the other was a deletion wearing
> another probe's label. Both showed **GREEN as vacuous oracles**. Also measured: a
> two-session DB race test fails by **hanging**, not reddening, unless the parked task is
> unwound in a `finally` and bounded with Postgres `lock_timeout`.
>
> Suite **3656 → 3676** / 8 skipped, re-run per merge commit, `git diff <ci-head> HEAD` =
> 0 bytes ×4. ruff + format clean over 576 files, `mypy --strict services/` clean over
> 130; guard + R1/R4/R7/R8 exit 0; `alembic check` clean, dev DB at `0022`; CI `gate` ×4.
> **21 non-vacuity probes**, each RED against its named test, restored from `/tmp`.


> **Session 202, 2026-08-03 (head_commit `6a3f2d7` → `40d65d9`) — seven PRs merged
> (#1013–#1018, #1020); this reconcile is the one still open. The theme: a
> governance gate stops asking a non-deterministic oracle, and ADR-0035's
> follow-on work opens.**
>
> **#1013 / #1016 — G1/G2 are now DETERMINISTIC.**
> `.claude/hooks/pretooluse_governance_gate_deny.py` reads the target's own
> `**Status:**` line instead of asking the local-LLM classifier, which was
> **measured** non-deterministic: the same input at `temperature 0` returned both
> `proceed` and `pause`, self-consistency **0/4**, blank output **3/12**. #1016 then
> unwired the classifier's now-redundant G1/G2 PreToolUse arm
> (`pretooluse_classifier_dispatch.py`) from `settings.json` — it was also **broader
> than its own spec**, pausing Accepted PLANs, which neither the registry's G1 row
> nor `CLAUDE.md` §6 ever claimed (both say ADR). `plan-drafter` stays exempt; the
> main agent gets no override. Three tests pin the new topology.
>
> **#1014 — ADR-0035 D2's four pointer amendments now all EXIST** (ADR-002 ×3,
> ADR-0003 ×1), plus **nine currency notes** re-dating ADR-0035's own present-tense
> claims about the MS-S1 Cloudflare Tunnel — which Cray confirms is **not running**.
> 117 insertions, **0 deletions**: pure appends, no prior text rewritten.
>
> **#1015 — ADR-0032's Context snapshot RE-GROUND (third pass), discharging the s197
> debt.** "six synthetic verticals" → six verticals of which five are synthetic and
> `fleet_maintenance` is the design partner's real Phase-1 pilot.
>
> **#1017 — PLAN-0100 drafted** (`Status: Draft`, 12 ACs, 6 phases): the ADR-0035
> exposure PLAN. Per **Cray's s202 ruling** it absorbs the UI work D5(2) implies,
> because ADR-0035's "Env only — no code" is contradicted by its own D5(2).
> **SD-1..SD-5 are unruled and execution does not start without them** — SD-1
> (published DB posture: DB-less vs synthetic Postgres) is load-bearing: it decides
> which tabs the public sees, and every allowlist row hangs off it.
>
> **#1018 — the OCT nav-bar overflow is FIXED for the dev profile.** `theme.css`'s
> responsive ladder was written for a **five**-tab header while `app.js` registers
> **ten**; measured natural width **2253 px**, so the inactive-label collapse moves
> `max-width:1360px` → `2299px`. Verified **0 overflow** at
> 1280/1366/1440/1680/1920/2400. Two tripwires, both probe-proven RED. The
> published-profile half stays open as PLAN-0100 AC-3.
>
> **#1020 — `CLAUDE.md` §3 rewritten: the runtime procedure spine is named as the
> primitive.** §3 called the ontology + code generator "the moat" and never
> mentioned `procedures.yaml` being interpreted at load; it now leads with
> ADR-0032 D6's `monitor→decide→approve→act` identity. Codegen is **rescoped, not
> denied** — only `energy`/`core` emit committed code. Cowork drafted (§6
> convention) and returned **four corrections to Code's fact-pack**, all confirmed
> before applying. `docs/conventions/glossary.md` carried the same stale framing
> and was corrected with it. **The "SME wording in §1" half is struck** — see the
> Active TODO; it has no referent.
>
> CI `gate` pass ×6. Offline at the last PR: `ruff` clean over `services/` +
> `tests/`, `mypy --strict` clean over 130 files, suite **3411 passed / 370
> skipped**; `tests/handoffs/` **762 / 2** at #1016. **Honest gap:** the 370 skips
> are the Postgres-down shape (dev DB not up on **5442**), so the offline gate did
> **not** match CI scope — CI is the check that did. Four of the six PRs are
> docs-only. Three dispatch fact-packs were refuted by the drafter and corrected
> before use (unmerged-branch reads, a stale date, a wrong route attribution) —
> each was Code's error, not the drafter's.

> _Older content rotates out of this file per the **STATUS.md Rotation Policy (R1-R8)** in [`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md) (Lesson #23): Current Focus keeps the 4 newest sessions (<=8 blocks); Recent Decisions keeps the last 10 rows. Rotated blocks/rows live in [`docs/status-archive/`](status-archive/) and git history (Tier 3). Layout — **two separate chains, both with letters ascending with time and the base holding the recent window**: the rotation archive `2026-h1b` → `c` → `d` → `e` → `f` → `g` → `2026-h1-status.md`, and the Current-Focus-only `2026-h1b` → `c` → `2026-h1-current-focus.md`. Rotations append to the two bases. **Grep the directory, not a filename** — the chain is one corpus and which file holds a given block is an artifact of where the ~192 KB R4 bar happened to fall. _[Chain created 2026-07-17 (s144): the single `2026-h1-status.md` had reached 592,577 B, 2.3x R4's cap, and the new guard (#789) forced the split. `g` added 2026-07-30 (s193): the base had returned to 194,232 B with a ~10.7 KB block due to rotate in, so sessions-142→171 spilled and the base dropped to 46,215 B.]_

> **Session 203, 2026-08-04 (head_commit `40d65d9` → `592124b`) — three PRs merged
> (#1021–#1023), 0 open. Theme: the ADR-0035 D7 tenant-key PLAN opens, and all three
> of its SDs are the ADR describing something that does not exist.**
>
> **#1021 — PLAN-0101 drafted** (`Status: Draft`, 9 ACs): AC-1..AC-7 each quote their
> D7 sub-item **verbatim** so none can be silently dropped, plus a binding scenario
> test and an adjudication record. `plan-drafter` authored (G2), Code R2'd. It carries
> a `**Ruling:** _(unruled)_` slot under every SD **from the start** — the thing
> PLAN-0100 omitted, which is why PLAN-0100's Phase 0 must now *author* its record.
>
> **Three SDs surfaced UNRULED; Steps 2–6 are BLOCKED-ON-SD.** **SD-1 (load-bearing) —
> the write-stamp site:** D7(iv) names a "session/repository seam" that **does not
> exist**: `services/db/session.py` is 24 lines of engine + `async_sessionmaker` +
> `get_session()`, and a case-insensitive `tenant` grep across `services/` returned
> **0 matches**, so `settings.tenant_id` did not exist either — D7 states both in the
> present tense. **SD-2, emitting a non-ontology column:** `emit_orm` builds each class
> body as a pure function of the ontology's `properties`, and **three** committed
> guards enforce that purity where D7(i) says "the reproducibility guard", singular.
> **SD-3, which uniques `tenant_id` joins:** D7(vi) names **2**; the census is **12**,
> and the 12th is a column-level `unique=True` in `services/db/pm_import.py` that a
> `UniqueConstraint(` grep cannot see — so that census returns 11 and looks complete.
> Two families are non-mechanical: the six Identity-`seq` sites, and an audit chain.
>
> **#1022 — Step 1, the only SD-free step:** the `tenant_id` setting, a `.env.example`
> entry, a 3-leg guard test over a **discovered** (globbed, not hardcoded) vertical
> census, and the Step-1.4 probe. **The probe CONFIRMED a lead by measurement** on a
> throwaway `vero_lite_probe` DB: baseline clean → a new model column IS detected
> (`add_column`, exit **255**) → a `server_default` on the model but absent in the DB
> is **NOT** (exit **0**). **The `add_column` leg is the positive control** — without
> it, exit 0 cannot be told from a broken invocation. Unblocks SD-1's folded
> `server_default` question; dev + all four test DBs untouched, the probe DB dropped.
>
> **Two non-vacuity probes, restored from `/tmp`:** a `settings` read folded into the
> step snapshot → **12 RED**; a constant `"tenant_scoped": True` → **6 RED on the name
> leg, both value legs GREEN** — which is what shows leg 3 closes a real hole rather
> than restating legs 1–2. **Measured, not asserted:** `test_derivation_pin.py` stayed
> green (15 passed) under *both*, because its tripwire watches only the **top** level.
>
> **#1023 — four stale-claim chores.** `code_generator.py`'s "other five" at **three**
> sites (the s202 handoff listed two): one → "six" (the emitter count is fixed at 7),
> the two artifact sites **de-numbered** rather than renumbered — how many outputs are
> gitignored is **namespace-dependent**, so any fixed number re-stales. Plus
> `glossary.md`'s two parked-vertical rows, a stale `[ ]` TODO flipped, and **OQ-4's
> "(Not due yet)" removed — it is NOW DUE**. **Also corrected:** "ADR-0035 mandates no
> ordering" is **not in the ADR** — it originates in PLAN-0100.
>
> **Cray typed:** start the tenant-key PLAN now, not after PLAN-0100's SD-1 (they are
> independent); guard scope = tenant-shaped **names**, not step-level set-equality;
> started `vero-postgres` (5442) / stopped `smb-dev-postgres`; #1021 merges first.
>
> CI `gate` ×3. Offline at CI scope with Dev Postgres up: **3792 passed / 8 skipped /
> 0 failed**, ruff clean, 448 formatted, `mypy --strict` over 130 files. Collected
> totals reconcile against the DB-down run — **3781 both ways** — so the **370 → 8**
> skip collapse is the database coming up, not a coverage change.

> _Older content rotates out of this file per the **STATUS.md Rotation Policy (R1-R8)** in [`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md) (Lesson #23): Current Focus keeps the 4 newest sessions (<=8 blocks); Recent Decisions keeps the last 10 rows. Rotated blocks/rows live in [`docs/status-archive/`](status-archive/) and git history (Tier 3). Layout — **two separate chains, both with letters ascending with time and the base holding the recent window**: the rotation archive `2026-h1b` → `c` → `d` → `e` → `f` → `g` → `2026-h1-status.md`, and the Current-Focus-only `2026-h1b` → `c` → `2026-h1-current-focus.md`. Rotations append to the two bases. **Grep the directory, not a filename** — the chain is one corpus and which file holds a given block is an artifact of where the ~192 KB R4 bar happened to fall. _[Chain created 2026-07-17 (s144): the single `2026-h1-status.md` had reached 592,577 B, 2.3x R4's cap, and the new guard (#789) forced the split. `g` added 2026-07-30 (s193): the base had returned to 194,232 B with a ~10.7 KB block due to rotate in, so sessions-142→171 spilled and the base dropped to 46,215 B.]_


> **Session 204, 2026-08-04 (head_commit `592124b` → `22202f2`) — three PRs merged
> (#1026–#1028), one open (#1029, CI green, awaiting merge). Theme: the ADR-0035 D7
> tenant key lands end to end, and a remedy stated in halves fabricated a green run.**
>
> **PLAN-0101 Steps 2–6 COMPLETE, 12/12 ACs, ARCHIVED (#1028/#1029).** 21 tables carry
> `tenant_id`; all **12** uniques re-scoped (unscoped **0**, anonymous **0**, read from
> the **built SQLAlchemy metadata**, not source text); revision `0024` = 21 tables ×
> three phases + 12 drop/recreates, downgrade proven by *running* it. **Two consequences
> SD-3's riders never named, both found by the work, not by review:** a composite FK
> **must move with its widened target** (Postgres demands an exact match — **335 suite
> errors from one root**), and audit-chain scoping is **four** sites, not the two Cray's
> call named, because `append_audit`'s head lookup is a **correctness requirement** of
> the widened constraint. Closeout: `docs/plans/done/0101-tenant-key-column.md`.
>
> **Four Cray calls reshaped it mid-flight** (attributed in the PLAN): unbind SD-2's
> letter once AC-10's negative guard proved undischargeable; name the real worry — a
> future LLM over ontology data sweeping tenants; a **synthetic second-tenant fixture**
> not a real second customer; **SD-3 rider 3 reversed** to scope the audit reads here.
>
> **That worry got a measured answer that INVERTS the intuition.** The NL-query path never
> writes SQL (**0** raw-SQL execution sites in `services/`) and `_validate_query` checks
> every filter property against the ontology's property list — **the ontology is the
> allowlist of what a model may name**: `tenant_id` **in** makes cross-tenant selection
> *expressible*, **out** keeps it inexpressible (AC-11 asserts it). Nor is the fixture
> convenience — under one tenant the twelve re-scopes are a **100% behavioural no-op**, so
> the second tenant is the positive control for Cray's own ruling.
>
> **Banked:** a planted `server_default`, read against both oracles in one run, turned
> `test_tenant_key_migration.py` **RED** while `alembic check` stayed **GREEN at exit 0**
> — SD-1(b)'s "no `server_default`" is **provably invisible** to the tool that looks like
> it should catch it. **Read-site census: 50** raw `select(` hits over **16** files in
> `services/`, UNCLASSIFIED — not a bug today (one deployment = one DB = one tenant); four
> are now tenant-scoped, the rest owed to a future multi-tenant ADR, AC-12(iii) records them.
>
> **An unplanned harness-hygiene detour (#1026/#1027).** A pytest run reported `EXIT=0`
> with two tests RED. The remedy has **two required halves** — a SINGLE-quoted outer
> argument **and** `\$` for every `$` — compressed to **one half in three places at once**:
> the memory index, the hook advisory, `CLAUDE.md` §8. Code followed it literally, kept
> double quotes, read a **fabricated zero**, and came within one step of an unnecessary
> constitutional amendment; only the pytest summary three lines below contradicted it.
> **§8 and lesson 0007 §1.1 were correct throughout — only the enforcement was half-built.**
> Recorded: *a two-half remedy stated as one half is worse than stating neither* —
> `docs/lessons/0007-harness-exit-code-artifact.md` §6.1.
>
> Final gate: `tests/` **3817 passed / 0 failed / 8 skipped**, `mypy --strict` clean over
> **131** files, `ruff` + `alembic check` clean, CI `gate` 5m41s. **7 non-vacuity probes,
> every RED observed**, restored from `/tmp`, never `git checkout`.

> **Session 205, 2026-08-04 (head_commit `22202f2` → `bcab1f4`) — three PRs merged
> (#1031–#1033), all s205's own work. Theme:
> answering an overdue question corrected two errors in the record it was built on.**
>
> _[Three PARALLEL-session PRs — **#1034, #1035, #1036 — also landed in this window and
> are NOT s205's work**: #1034 from the chip session s205 spawned, #1035 and #1036 from
> one other session. They carry head to `bcab1f4` and alembic head to **`0025`**; their
> authors wrote the record, and **Recent Decisions** below carries all three.]_
>
> **OQ-4 CLOSED — Cray typed RETIRE L1 (2026-08-04); PLAN-0102 is the vehicle (#1031).**
> Re-measured over **130** transcripts keyed on **structural hook-emission paths**, not
> substring, with a **positive control that passed 3/3** — a zero was pre-committed as
> unreportable unless the method first re-found three known-present warns. **True
> positives = 0 in both eras.** Post-AC-7: **0 denies, 0 organic warns** (the lone warn
> was an induced self-test), so the "≥ 1 false positive" arm could not fire: the literal
> criterion is **unfireable by construction** — AC-7 left the guard inert, and a detector
> that never fires cannot produce the false positive its own retirement trigger requires.
>
> **Running it corrected two errors in the record it was built on.** (1) The s180
> baseline's **"0 denies" was wrong — ≥ 56 measured** over 19 days / 4,201 Write-Edit ops
> (**~1.33 %** of all edits hard-walled), and that is a **floor** — 30-day retention had
> already deleted 06-27 → 07-04 of the baseline's own span. Root cause: **three** deny
> wordings existed, not two — lesson 0012 quotes `in this **session**` while every live
> emission says `in this **turn**`, so s180 searched for a string no transcript contains;
> its warn count (3) was right because that string came from the hook source. Classified
> **was an error**, not superseded (§6). (2) The criterion's **prescribed remedy was
> mis-premised**: it called for an ADR-013 amendment, but `0013:90` states trigger E.4 as
> "the same *problem*" and never names L1, and `0013:333-336` delegates stateful
> loop-detection to PLAN-0008+. **L1 has zero ADR backing ⇒ no amendment**; PLAN-0102 is
> the governance record, on the PLAN-0092 precedent. Method + the four traps that nearly
> skewed it: `docs/lessons/0035-negative-measurement-needs-a-positive-control.md`.
>
> **PLAN-0100's fold-in (#1032) makes SD-1..SD-5 askable.** Five empty `Ruling:` slots +
> **AC-13** (the adjudication record) + BLOCKED-ON-SD markers; the H/I/J inconsistency
> reconciled by **dropping Tab H from SD-1's promise** — its backend is **mixed**, not
> DB-posture-contingent; `54dfc7d`'s measurement table folded in **verbatim** (dev half
> discharged, published half open); SD-4 restated **published-profile-only**.
>
> **The archive relocation (#1033) found its own recorded blocker false.** Three misfiled
> s196/s197 Recent-Decisions rows moved `h1g` → base. The Current-Focus chain split the
> move was said to depend on is a **separate corpus**, and the rotation base had ~109 KB
> of headroom throughout — the dependency never existed.

> **Session 206, 2026-08-05 (head_commit `bcab1f4` → `296cc34`) — six PRs merged
> (#1040–#1045), one open for Cray (#1046). Theme: every defect found this session
> was one that leaves the system LOOKING correct.**
>
> **PLAN-0102 was one ratification away from bricking the harness (#1040).** An R2
> pass found three scope gaps. The sharp one: the acknowledged-pause (`awaiting_ack`)
> subsystem was **entirely unscoped** while Step 5 removed one of its two
> dependencies — `stop_continuation.py:73` would still import a deleted function at
> module load, an `ImportError` **no `try/except` catches**, taking the chain-cap
> fail-safe, the classifier and auto-handoff down with it. Steps 3 and 5 also
> contradicted each other over `_apply_commit_reset`, whose `AttributeError` is
> **swallowed** by the observer's blanket handler — L2/L3/L4 would stop persisting
> while the hook still exits 0. **One root cause for all three: none of the missed
> identifiers carries an `L1` or `loop` token in its name**, so the name-keyed census
> could not see them. New **AC-11** carries two prongs that go RED on exactly these,
> because ACs 1–10 would all have passed over a bricked harness.
>
> **PLAN-0100's "blocked" slice was half unblocked — and all of it shipped.** STATUS
> read *execution gated on SD-1..SD-5*; the PLAN's own text gates only steps marked
> BLOCKED-ON-SD. **Six SD-free items shipped**: the Step-1 census (#1043), `ui_profile`
> + its two delivery seams (#1042), the in-flight cap + prompt log (#1044), the D6
> banner (#1045). **Cray chose server-injection for the boot seam; the carrier had to
> change from `<script>` to `<meta>`** — `_OCT_CSP` pins `script-src 'self'`, so an
> inline script is silently blocked and the profile would fall back to the FULL
> console. Every property the decision was made for survives.
>
> **The census found the published demo unloginable (#1043).** `/whoami` was in
> **neither** allowlist table, so it fell to default-deny — but `auth.js:39` probes it
> to provision the operator key, so approve/execute and gate-resolve would have been
> undrivable *while sitting on the allow table as keyed routes*. The PLAN's own
> keyed-routes paragraph rested on a route the same section denied. Generalises: **an
> allowlist complete for the routes a feature CALLS can be incomplete for the routes
> that make it REACHABLE.**
>
> **The unowned wall-clock intermittent is closed (#1041)** — and the reported framing
> was wrong in a useful way: not two clocks, but **one clock sampled twice** on a
> non-monotonic host. Bracket → equality against a frozen `Clock`; a planted
> **1-second** defect reddens both tests, which the old bracket could not catch at all.
>
> **Two silent failures the gates caught, not review:** `uvicorn.Config` applies a
> **global** logging `dictConfig` (`propagate=False` on `uvicorn.error`), so a test
> stub broke a `caplog` assertion three files away while the line it wanted still
> reached stderr — only the full-suite run saw it. And a CSS custom property that does
> not exist **fails silently**, so the D6 banner's first draft would have rendered in
> an inherited colour with nothing to redden.
>
> Gate at CI scope on every merge, including each merge commit (CI is PR-only and
> never tests those): suite **3826 → 3847**, ruff + `mypy --strict` clean throughout.

<!-- rotated 2026-08-07, session 213 (STATUS reconcile — the published OCT demo went LIVE behind Cloudflare Access; #1069–#1072) -->
> **Session 207, 2026-08-05 (head_commit `296cc34` → `5621266`) — one PR merged
> (#1049), 0 open. Theme: a ratified plan's own recommendation and its own allow
> table had never been checked against each other, and an unreviewed fold-in got
> two of its own claims wrong.**
>
> _[The s206 tail also merged **#1046** (Step 10 — RoPA + the published-demo
> runbook), **#1047** (`0c9348a` — the s206 STATUS reconcile itself, which is why
> the s206 block below stops where it does) and **#1048** (lessons
> **0036**/**0037**); the s206 block below predates all three.]_
>
> **Step 4 COMPLETE, AC-3 CLOSED:** the published profile measured green at all
> five pinned widths — **0 overflow, 0 clipped** — under SD-4's option (a),
> *before* Step 3's removals, i.e. at maximum header width demand. A 600 px
> **non-vacuity probe** drove the instrument red first. ⚠️ The initial probe's
> `querySelector('header')` returned **null** (the element is `class="header"`),
> scanning **zero** nodes and reporting a clean "0 clipped" — the table now carries
> a **nodes-scanned column** so a void row cannot pass as a clean one.
>
> **Cray ruled all five SDs (typed 2026-08-05); AC-13 is CLOSED and every
> BLOCKED-ON-SD marker is RELEASED.** SD-1 = (a) DB-less · SD-2 = exclude all
> three draft routes · SD-4 = (a) measure-to-confirm · SD-5 = keep both. **SD-3
> was restated before it was ruled: ADR-0035 never names nginx** — it says only
> "at vero-lite's edge" and that "rate limiting lives at the edge", which forbids
> rate limiting *inside* `services/` rather than mandating a proxy. Cray ruled
> **(ii): stay with `cloudflared`** (ingress allowlist + catch-all 404, config
> committed) plus the zone's Cloudflare rate-limiting rule — **no nginx service**.
>
> **Finding C-3 — four allow-table rows the ruled DB-less posture cannot serve.**
> Tracing every allow-table handler for a DB session dependency found
> `/recommendations/{id}/execute`, `/runs/{id}`, `/runs/{id}/gate/resolve` and
> `/insights/query`, and there is **no global exception handler anywhere in
> `services/api/`** — so each returns an unhandled **500, not a degrade**.
> Sharpest: the allow table called `execute` the "operator-driven demo beat", so
> **Approve would succeed and Execute would 500** — the Tab B loop dying at its
> last step. The runs pair also fails a second, DB-independent way: justified as
> "Tab G beat 3", but that panel mounts only in event mode (`view-hero.js:641`)
> and event mode is excluded — **zero callers**. This is **C-1 mirrored**: C-1
> was a route *missing* that made a feature undrivable; C-3 is routes *present*
> whose reachability path is excluded. Method note: the drafting census walked
> *UI call sites → routes*; C-3 needed *routes → handler DB dependency*, and
> **neither walk finds the other's defect**.
>
> **An R2 pass with three independent adversarial reviewers discharged the
> author≠reviewer separation the fold-in owed — and it paid for itself.** C-3
> survived **5/5**. But SD-3's ruling drew **six findings**, three of which the
> spec cannot remove: a **blocking D4/L5 ADR debt** (the ADR assigns the connector
> + ingress map to the portal repo, so `0035:421-424`'s drift trigger fires), a
> vendor-branded 429 on Free, and NAT-shared-IP with no burst. And **Step 9's
> pass/fail read scored 4/5 against a completely dead app** — its "non-404" bar
> let a crashed container pass four cases at once — so it was rewritten as **v2**.
>
> **Two of the PLAN's own claims were retracted.** `GET /recommendations` was
> pinned `deterministic` but is **LLM-backed** (`recommender.py:194-195`), so the
> recorded consequence "`/query` is the only published LLM route" was **false**;
> it is tracked now as **OI-1** — the route is neither rate-capped nor
> prompt-logged, and each failure pages Cray via `notify_llm_unreachable`. And
> ~14 `api.js` citations were stale by exactly **+7**: the fold-in corrected three
> instances without recognising the shift was **systematic**.

<!-- rotated 2026-08-08, session 214 (STATUS reconcile — the repeatable deploy procedure, and the first live redeploy; #1073-#1078) -->
> **Session 208, 2026-08-06 (head_commit `5621266` → `c0f08b8`) — three PRs merged
> (#1056–#1058), 0 open. Theme: a fail-soft handler was holding the DB-less boot
> guarantee for the wrong reason, and an AC table read 4 of 13 while its own handoff
> claimed 10.**
>
> **#1056 — every non-procurement boot was raising `UnboundLocalError`, and the test
> suite passed anyway.** `async_session` was imported inside a nested branch of
> `lifespan` but used by the separate `if "fleet_maintenance" in known:` block below,
> so Python bound the name **function-local**: any boot not taking the
> procurement-seed branch — **including the plain `energy` default** — raised at
> **both** call sites. `tests/test_startup_log.py` had been exercising the broken
> path all along and **passing**, because the fail-soft handler absorbed it. So the
> DB-less boot guarantee **was holding for the wrong reason**: a handler swallowing
> a *code bug* rather than an *environment absence*. The fix leaves a deliberate
> open seam — `_is_environment_absent(exc)` is a documented `return True` stub that
> **Cray chose to author personally**; it is behaviour-neutral today and nothing
> else in the repo tracks it.
>
> **#1057 — ADR-0035 D4/L5 amended; PLAN-0100 Step 8's ADR blocker is CLEARED.**
> **Cray's typed ruling, 2026-08-06: reading (a)** — vero-lite's `cloudflared` **is**
> this system's connector in its own compose project; the portal repo owns the
> ingress map *across systems*; each system owns its *own* route allowlist. Reading
> (b) was **rejected** (it voids AC-6(a) and re-opens SD-3). The amendment is framed
> as the ADR **reconciled with itself**: Implementation Note 1 gave connector + map
> to the portal while Note 2 already gave the route allowlist to vero-lite. Two
> drafter-surfaced decisions were **also typed by Cray**: **SD-1** restate D4's
> acceptance shape to count *each system's own* connector (otherwise the ADR's own
> drift trigger fires on the arrangement just ruled), **SD-2** keep the binding
> corollary that **no other system's connector may join this system's network**. The
> same PR renumbered **81 line numbers across 45 PLAN-0100 citations** with a
> self-verifying script (old line content must be byte-identical to new, or abort) —
> **no guard test validates ADR line citations**, so that drift would have rotted
> silently.
>
> **#1058 — PLAN-0100 AC-7/8/9/10 CLOSED: 4 of 13 → 8 of 13, and two of the four came
> back NOT-CLOSEABLE.** The work had shipped in s206 (Steps 5/6/7/10) and the AC
> table was simply never ticked — the s207 handoff claimed "10 of 13 closed" while
> the checkboxes read **4**. Every AC was verified clause-by-clause by independent
> **refuting** reviewers. **AC-7:** two clauses were **unassertable as written** and
> were amended on Cray's typed ruling ("< 5 s" on one coroutine whose completion
> order the event loop does not promise; "the first" is not identifiable), and a
> third was **genuinely unmet and built** — no prompt-log assertion existed anywhere
> under the cap; non-vacuity was shown by mutating the router to log a hardcoded
> `arm="llm"`, which reddened **only** the new assertion. **AC-8** closed **with
> Postgres up on purpose** — its `/insights/query` half is the sole coverage and
> silently **skips** otherwise. **AC-9's** required ADR-0032 D5 wording review **had
> never been performed**: done, **PASS**, and its tripwire hardened (pinning
> `"Cloudflare"` survived a reword that deletes the actual D6 duty). **AC-10** fixed
> a purge command reading `prompts-*.jsonl` against a writer emitting `prompt-` — it
> matched **zero** files and **exited 0**.
>
> **OI-1 got worse, not clearer.** The LLM fan-out fires on **Tab A, the default
> landing view** — not first on Tab B as previously recorded — so the exposure sits
> on the page every visitor lands on; and option **(a)** collides with a **closed**
> prompt-log row schema whose `text` is defined as *the visitor's typed input*,
> which `/recommendations` has none of. Cray owes two calls: **OI-1** (three options
> in the PLAN's §Open items; **(c) conflicts with D6**) and the **per-IP rate cap
> 2 → 10 req/10s** nod. Step 8 also still owes an **unpinned `OCT_VERTICAL`**;
> Step 9 follows Step 8.

> **Session 209 cont., 2026-08-06 (head_commit `0c067de` → `8bd331d`) — two PRs
> merged (#1063, #1065), 0 open. This block: #1063, PLAN-0100 Step 8 — the
> published surface got its deploy target and its vertical pin, and the pin turned
> on an empty iterator, not on the DB posture everyone assumed.**
>
> **#1063 — PLAN-0100 Step 8 SHIPPED `deploy/published/`.** Greenfield: neither
> `deploy/` nor `tests/deploy/` existed, and the repo held zero cloudflared YAML.
> Ships `{docker-compose.yml, published.env, README.md, cloudflared/config.yml}` +
> `tests/deploy/test_published_compose.py` (**69 tests**); `app.js` drops **Tab G**
> on the published profile (`?v=c48`; `test_ui_profile.py` follows); `.env.example`
> gains three `LLM_*` names. `/demo/hero/*` is excluded for a reason unlike every
> other exclusion — its backend is offline, DB-free and would serve fine, but the
> governed hero is bespoke per design partner (ADR-0032 D1.2) and energy owns no
> hero builder, so `_builders()` would serve a **Fastenal hero under an energy
> banner**. **AC-4 · AC-5 · AC-6(a)+(b) CLOSED — PLAN-0100 moves 8 → 10 of 13**;
> AC-6 itself stays **unticked deliberately** ((c) is Step 9's live compose smoke).
>
> **`OCT_VERTICAL` is pinned `energy` (Cray typed) — and the DB posture was NOT the
> discriminator.** Pinning `procurement` would *not* have cost the DB-less boot
> guarantee: measured, its adapter and executor registrar open no session at all.
> What decided it — `FastenalCsvAdapter.stream_events` is an **empty async iterator
> by design** (`fastenal_csv.py:243-251`, "ships no OperationalEvent stream (v1)")
> and `_populate_store` streams `"reading"` **before** any arm choice
> (`actions.py:186`), so under procurement `GET /recommendations` returns `[]` on
> **both** profiles, tunable by no setting, leaving **Tab A — the default landing
> view — blank**. Energy streams real events and exactly one breaches (`96.5` ≥ the
> pinned `90.0`), which is that dataset's stated design.
>
> **A non-vacuity probe caught a vacuous test inside the very change it probed.**
> Stripping the anchors off `^/query$` reddened **one** test where three were
> expected — the anchoring and deny assertions were parametrized over the test
> module's own constant (anchored by construction, unable to fail) and never read
> the committed file. Post-fix the same mutation reddens **four**, including the
> `/insights/query` leak SD-1 excludes; a positive control now ships in-suite.

> **Session 209 cont., 2026-08-06 (same window, head_commit `8bd331d`) — this
> block: #1065 (ADR-0036 `Proposed`), the two PARALLEL-session PRs that are
> NOT s209's work, and Cray's three outstanding reads.**
>
> **#1065 — ADR-0036 `Proposed`: a deployed vertical instance IS a "system".**
> ADR-0035 defines "system" operationally, by what one owns (`0035:478-493`), and a
> vertical instance satisfies every clause with **zero engine change** — so the
> multi-vertical demo is N systems (`oct-energy.`, `oct-procurement.`, …) picked
> from the `portal.` landing surface, and D4's reopening trigger does **not** fire.
> In-process multi-vertical serving is a recorded **non-goal** (`auth.py:82`'s
> vertical-scoped principal roster is the ADR-level blocker). ⚠️ **A live obligation
> rides in the renamed guard test's docstring**
> (`test_the_non_accepted_adrs_are_exactly_the_expected_set`): ratifying 0036
> `Proposed → Accepted` must REMOVE its entry from that set **in the same edit**.
>
> **Two PARALLEL-session PRs — #1062 and #1064 — also landed in this window and are
> NOT s209's work**: they are **session 210's** (a parallel session, now closed
> without reconciling) — the new `.claude/skills/stream-status/` skill and a
> 4-stream lens for `next-work-analyst/SKILL.md`. s210 also produced a **gitignored**
> strategy doc (`docs/strategy/private/2026-08-06-marketing-fde-plan-synthesis.md` —
> marketing / FDE + pricing, four frame decisions Cray typed). The governance
> question its closing notice raised is recorded under In-Flight Discussions.
>
> **Cray owes three reads, all genuinely open:** **ADR-0036 ratification** + its
> three OQs (OQ-1 retire vs alias the bare `oct.` label — the ADR recommends
> **retire**; OQ-2 the aggregate in-flight LLM posture across N systems; OQ-3 the
> trigger for `fleet_maintenance` as system #3) · the **per-IP cap 2 → 10 req/10s**
> nod (unchanged since s207; §Pinned values still reads "needs Cray's nod") ·
> **AC-12**, still failed by #1057.

> **Session 209, 2026-08-06 (head_commit `c0f08b8` → `0c067de`) — one PR merged
> (#1060), 0 open. Theme: an LLM call the visitor never asked for was being made on
> the default landing view, and the ruling that stopped it was written as a
> principle rather than as a one-route patch.**
>
> **OI-1 RULED — Cray typed option (b), and #1060 built it.** On the `published` UI
> profile, an LLM call the visitor did not initiate is **no longer made**. The rule
> lives in a new `services/engine/llm/arm_policy.py` — the principle in its
> docstring, one predicate that decides it — and `recommender.recommend(...)` now
> takes `visitor_initiated=False` **keyword-only and fail-closed by default**, so a
> future caller that forgets the flag gets the deterministic arm rather than a
> silent fan-out. Cray's second typed call: **keep the ฿ facet under the pin** —
> `build_economic_steps` is deterministic and never raises, so pinning the *LLM arm*
> need not cost the Box-4 facet anything.
>
> **A third disclosure state, on purpose.** `_disclose_rule_by_design` is new rather
> than a reuse of `_disclose_llm_degrade`: the degrade wording would have made the
> demo announce it is **degraded** while it is in fact working exactly **as
> designed**. The new trace step `arm-pin-disclosure` deliberately reuses the
> CI-pinned `rule_check` kind, so **no UI label and no `?v=` asset cache-bust are
> owed**.
>
> **Verification.** Non-vacuity **DEMONSTRATED** — neutralising the predicate to
> `return False` drove **3 of the 5** new tests RED while both dev controls stayed
> correctly green. Gate at CI scope: `ruff check .` clean on the tracked tree,
> ruff-format clean (609 files), `mypy services/` clean (**133** files, up from
> 132), full `tests/` **3869 passed / 8 skipped / 0 failed** (baseline 3864 / 8 —
> the **+5** is exactly `tests/api/test_published_arm_pin.py`, skip count unchanged).
>
> **No AC was ticked — PLAN-0100 stays 8 of 13.** The ruling *unblocks*; it does not
> close AC-4/5/6. Same PR reconciled the PLAN (OI-1 RULED, the allow-table posture,
> Step 8's now-stale BLOCK released, an AC-12 note, Step 9 Case 4). **Step 8 is now
> fully unblocked** — both blockers discharged (D4/L5 ratified in #1057 on
> 2026-08-05; OI-1 ruled today). **Cray owes one call, not two:** the **per-IP rate
> cap 2 → 10 req/10s** nod (the PLAN's §Pinned values row still reads "needs Cray's
> nod"), plus a read on **AC-12**, whose "this PLAN's diff touches no file under
> `docs/adr/`" clause is still failed by #1057 (#1060 touches no `docs/adr/` file,
> so it does not worsen it). Cray's third typed call was **"merge only, then
> stop"** — Step 8 is deliberately deferred to s210.

> **Session 212, 2026-08-06 (head_commit `8bd331d` → `a22ff8e`) — one PR merged
> (#1067), 0 open. Theme: the run that could not run still told the truth — and all
> three defects it found were in the instructions for running it.**
>
> **PLAN-0100 Step 9 ran as its OWN sanctioned offline fallback, not as the smoke.**
> Probed first: the box has `docker` and `curl` but **no `cloudflared` binary**, no
> `CLOUDFLARED_CREDENTIALS_FILE`, no `~/.cloudflared`; the compose declares that
> variable required-with-no-default, so `up` cannot start the project and **case 0 —
> which gates every other case — is unreachable**. A real tunnel needs a Cloudflare
> account action plus a domain ADR-0035 D1(3) places in the portal repo, which does
> not exist. Against the pass/fail read fixed **before** the run: **case 2 PASS**
> (24/24 excluded routes → `http_status:404`; 11/11 allowed → `http://app:8000`) and
> **case 7 PASS** (`cloudflared 2025.8.1`, committed config validates `OK`) — both
> install-free through the image the compose project already pins. **Cases 0, 1, 3,
> 4, 5, 6, 8 are NOT COVERED**, recorded and inherited by **Step 11**.
>
> **Non-vacuity DEMONSTRATED, not asserted.** Re-run against a **copy** of
> `config.yml` in `/tmp` with the `^…$` anchors stripped, the excluded
> `/insights/query` **flipped** from `http_status:404` to `http://app:8000` — so the
> 35 PASS rows prove the probe discriminates, not merely that it ran; the committed
> file was never mutated and both states are in the transcript.
>
> **AC-6 stays unticked; PLAN-0100 stays 10 of 13.** (c) has two clauses and only one
> is met — "excluded → 404 at the edge" is proven against the real `cloudflared`
> matcher, "allowed → served" is not, because **nothing was ever served**. Case 2
> likewise closes in its **rule-resolution form only**: its positive control (an
> allowed request must appear in `docker compose logs app`) has no app log to read,
> so that half rides to Step 11 with case 1.
>
> **Three COMMITTED defects found and fixed in the same PR; each would have scored a
> false verdict.** (1) The case list still called three `/demo/hero/*` GETs **served
> (200)** — Step 8 excluded that surface the day after v2 was written, so an operator
> reading it literally would have logged **three FAILs against an edge behaving
> exactly as intended**. (2) The sanctioned fallback was written `tunnel ingress
> validate --config F` in the PLAN and twice in `deploy/published/README.md`; the
> flag belongs on `tunnel`, and the wrong form prints `Incorrect Usage`, validates
> **nothing**, and **still exits 0** — a silent false pass for anyone scoring on
> `$?`. (3) It assumed a host `cloudflared`; the README now documents the
> install-free image invocation, installing one being a host-state change under
> `CLAUDE.md` §8.
>
> Gate at CI scope: ruff-format clean (610 files), `mypy services/` clean (133
> files), `tests/` **3938 passed / 8 skipped / 0 failed**, matching the count
> pre-committed before the run. _[Numbering: 209 → 212 is not a slip — parallel
> sessions consumed 210 and the 211 handoff directory, and the merged Step 9 run
> record says "session 212", so STATUS agrees with it.]_

> **Session 213, 2026-08-07 (head_commit `a22ff8e` → `07e9603`) — four PRs merged
> (#1069, #1070, #1071, #1072), 0 open. Theme: the session that stood the published
> demo up for real — and NOT ONE of the four defects came from a failing test.**
>
> **The demo is LIVE** at the `oct-energy` subdomain behind Cloudflare Access
> (one-time-PIN email allowlist), verified end-to-end in a browser by Cray. Every
> defect was found by touching a layer of reality nobody had touched before —
> docs → config → image → deploy host → edge.
>
> 🔴 **#1071 — `python-multipart` is a RUNTIME dependency, and the shipped image
> could not boot; it had not been able to since 2026-07-28.** It reached the dev
> venv only via `mcp` (a **dev** extra); the image installs `--no-dev`. FastAPI
> resolves multipart routes at *import* time, so `import services.api.main` raised.
> **3943 tests were green over a container that could not start.** The fix ships
> **a CI step that reproduces the image's dependency set and imports the entry
> module** — it guards the *class*, not the instance.
>
> **#1069 — `API_KEYS` had no way into the container.** `env_file` loads
> `published.env` and nothing else, and compose does not forward the host
> environment, so the secret the README told operators to provision was silently
> dropped: the demo was unloginable no matter what the host exported. Bare
> pass-through added, deliberately optional. **#1070** adds the bring-up runbook +
> `verify_tunnel_credentials.py` and fixes **7** `docker compose -p vero-oct`
> invocations in the operations runbook — the project is `vero-published`, so **all
> three PDPA deletion paths were unexecutable**. **#1072** folds in 7 corrections
> from executing the runbook for real, plus **13 tests for the verifier** (it
> shipped with none).
>
> **Step 11 is BLOCKED on a governance ruling nobody knew was needed — SURFACED,
> NOT RULED.** PLAN-0100 Step 11's case list asserts exact statuses (`/health` →
> 200, keyless `/whoami` → *exactly* 401 — which the PLAN calls the only thing that
> catches `API_AUTH_ENABLED=false` in the running container); through the ratified
> Access gate **every path returns 302** (measured on seven paths; the redirect
> metadata carries `"service_token_status": false`). The remedy is a service token,
> which Cloudflare requires be a **second Access policy** — and ADR-0035's
> acceptance shape names "a second Access policy" as a drift trigger. **ADR-0035 D3
> and the case list are each correct and were written at different times — a
> composition problem, not a defect in either.** **PLAN-0100 stays 10 of 13; AC-6
> unticked** ((c)'s "allowed → served" clause is still unproven).
>
> Verification: the full offline gate at CI scope **four times**, once per PR; final
> `ruff format --check` clean (612 files) · `mypy services/` clean (133) ·
> **3956 passed / 8 skipped / 0 failed**, the count pre-committed before every run.
> Non-vacuity demonstrated for all **9** guards added (mutations restored from
> `/tmp` copies, never `git checkout`). The shipped image proven identical across
> machines via `docker image inspect` after `save`/`scp`/`load`.

> **Session 214, 2026-08-07→08 (head_commit `07e9603` → `1384278`) — six PRs merged
> (#1073–#1078), 0 open. Theme: the published demo got a repeatable deploy
> procedure, and the procedure found three defects in itself before it was allowed
> to touch the host.**
>
> **#1074 — the redeploy pipeline.** `deploy/published/deploy.py` + a runbook +
> **18 guard/scenario tests**. Bring-up was a one-time procedure; nothing covered
> "main moved, make the demo be that". It asserts an **effect** — the running
> container's `.Image` equals the id just loaded — not a step count, because
> `compose up` decides for itself whether a container is stale and that decision
> appears in no command's output. Also: `:prev` tagged before the load overwrites
> `:latest` (rollback), and force-recreate of the connector **only** when the
> bind-mounted ingress config changed.
>
> 🔴 **#1076 — every remote `--format={{…}}` was unrunnable.** The deploy host's ssh
> shell is **PowerShell** (`echo %COMSPEC%` comes back unexpanded), which reads
> `{…}` as a script block: docker gets `unknown shorthand flag: 'e' in
> -encodedCommand`. Fixed by asking for plain JSON and parsing locally; `scp` and
> the `C:\vero-staging` path dropped for `docker load` on stdin. **The guard written
> one PR earlier to catch exactly this went GREEN over it** — its hazard set listed
> quotes, `$` and separators but not braces, because it came from what was
> imagined, not measured. **#1075:** a plan reported `PASS` for checks it never ran
> and closed "2 checks, 0 FAIL" at exit 0, found by running it and reading the
> output. **#1077:** the build could not interpolate its own compose file (`compose
> config` exits 1 without `CLOUDFLARED_CREDENTIALS_FILE`) while the code's own
> comment said so and passed nothing — the **third** instance in one session of
> *comment states the rule, adjacent code breaks it*. **#1073** reconciled s213's
> STATUS (never done) and discharged a stale 🔴 "Step 8 must not start" marker in
> PLAN-0100, cleared by #1057 on 2026-08-05; **#1078** folds in the corrections from
> the real run.
>
> **THE DEPLOY RAN, under Cray's typed §8 go (2026-08-08).** The demo now serves the
> image built from `d0a2808`; it had been on s213's image for 10 hours. `8 checks,
> 0 FAIL` — and every pre-committed read was verified **independently of the
> script's own ledger** by reading the host: container `11b0fb7201be…` →
> `45f6440a2d48…` (genuinely new — `Up 45 seconds` vs `Up 10 hours`), `.Image`
> `4c88145c8653…` → `153324a2995c…`, `:prev` now holds `4c88145c8653…` so rollback
> is live, host checkout `9601f068` → `d0a28080`, `/health` and `/` both **302** at
> the edge. The connector was correctly **not** recreated (none of the 14 changed
> files was `cloudflared/config.yml`).
>
> **The finding worth carrying:** none of the three pipeline defects was catchable
> by the offline suite — **3977 tests green over a script whose first command failed
> on contact with the host**. Same shape as s213's #1071 (3943 green over a
> container that could not boot), one layer up. What caught them was a read-only
> recon phase with a pass/fail read fixed **before** the run, and a rule that a
> failed phase means no deploy. Gate at CI scope on every merge: `ruff format
> --check` clean (614 files) · `mypy services/` clean (133) · **3977 passed /
> 8 skipped / 0 failed**.

> **Session 215, 2026-08-08 (head_commit `a5ae3cd` → `94fac66`) — four PRs merged
> (#1084–#1087), 0 open. Theme: PLAN-0100 Step 11 — the Cray-gated live run against
> the published demo — was executed end to end; it found four defects, three of which
> were fixed, redeployed and re-verified live in the same session.**
>
> **The run.** Driven through the ratified Cloudflare Access gate with a cookie from a
> real one-time-PIN login (the s214 route), under Cray's typed §8 go, with the
> unauthenticated control re-run alongside (302/302/302). **Cases 0, 2, 3, 4, 6, 8
> CLOSE.** **Case 1 closes 19/21 on its own read** — the two misses were the font
> content-types, and two further failures were probes the runner added, not rows the
> case asks for. **Case 5 FAILED, was fixed, and re-verified PASS.** **P5 PASS**;
> **P4(ii) PASS** twice independently; **P4(i)'s exact `T_edge` is UNMEASURED** —
> recorded as INSUFFICIENT-EVIDENCE with a measured lower bound (`T_edge ≥ 54 s`)
> that excludes the clause's own FAIL condition of `< 40 s`.
>
> 🔴 **Four defects, none catchable offline.** **D-1 — 90+ published `POST /query`
> wrote ZERO prompt-log rows.** The image never created the volume mount point, so
> Docker made it root-owned while the runtime is uid 999; `prompt_log.record` swallows
> `OSError` **by design**, so it failed silently and ADR-0035 D6's whole regime (RoPA,
> 90-day retention, the purge command, the DSR path) described a file that did not
> exist. **D-2** — the prompt log named a model that never ran
> (`ollama_default_model` / `gemma4:26b` recorded while the engine ran
> `recommender_model` / `gpt-oss:20b`). **D-3** — bundled `.woff2` fonts served as
> `text/plain`: the slim image ships no `/etc/mime.types` and Python's built-in table
> has no `.woff2`. **D-4**, narrowed after a second measurement: **only** the
> `group_by` verified_query fails — `count` aggregation works, and the second query's
> empty result is the **correct** answer (the dataset holds no `feeder` asset). Left
> open, direction undecided. **Also:** the demo pinned no `keep_alive`, so the first
> visitor after an idle spell waited the full 25 s timeout and got a degraded,
> ungrounded answer; fixed by sending the existing `ollama_keep_alive` on every chat
> call.
>
> **The finding worth carrying forward:** `deploy.py`'s seven green checks prove the
> **container** runs the new image; they do **not** prove a **visitor** receives it.
> D-3 read as still-broken after redeploy because Cloudflare was serving a
> `text/plain` copy cached while the defect was live (`cf-cache-status: HIT`,
> `max-age=14400`), closed by a manual **Purge Everything** (Cray). Nothing in the
> pipeline purges the edge, and the repo's `?v=cNN` convention does not reach fonts
> (referenced from inside CSS with no version parameter). A purge step or versioned
> font URLs belongs in the redeploy runbook — **not done**.
>
> **Twelve instrument faults** were caught and are listed in the PLAN record. The two
> most consequential: the probe matrix first scored **0/43 against a completely
> healthy demo**, because Cloudflare's Browser Integrity Check rejects a
> `Python-urllib` User-Agent *before* Access is consulted; and a `/query` oracle
> passed on the string *"I couldn't translate that question into a query over the
> operational data."* Common root: **checking a proxy for the thing rather than the
> thing.** **No AC was ticked — PLAN-0100 stays `Draft` at 10 of 13.** _[STATUS's
> frontmatter had stalled at `1384278`; s214 in fact closed at `a5ae3cd`, so the
> commits between them are s214's later merges, reconciled here rather than
> restated.]_

> **Session 216, 2026-08-08 (head_commit `94fac66` → `f987888`) — four PRs merged
> (#1090–#1093), 0 open. Theme: PLAN-0100 is COMPLETE 13/13 and ARCHIVED — the
> exposure PLAN closed after its last three ACs fell in one session, each to a
> DIFFERENT kind of move.**
>
> **Three ACs, three kinds of move — the distinction is the transferable part, and
> flattening it to "three ACs closed" loses the whole lesson.** **AC-6(c) closed by
> arithmetic over evidence already in hand** (#1090): case 1 was re-scored against the
> D-3 fix — **no new run** — its only two misses having been the `.woff2`
> content-types, fixed and live-verified in s215 on a `cf-cache-status: MISS`. The same
> PR corrected AC-6's stale "case 4" citation for the rate cap (under v2 numbering the
> rate cap is **case 6**; case 4 is arm posture) and recorded the carve-out as
> discharged through the Step-11 deferral branch. **AC-11 closed by a fresh live
> measurement** (#1091). **AC-12 closed by VERIFYING rather than drafting** (#1093),
> after which PLAN-0100 went `Draft` → `Complete` and was `git mv`-ed to
> `docs/plans/done/`.
>
> **`T_edge` = 125 s, and why s215 could not get it.** s215 failed five times. Four
> were ordinary instrument faults, already logged. The fifth was subtler: the
> instrument *worked*, but it stalled the upstream with `qwen3.6:35b` — a model big
> enough to cold-load — and it cold-loaded **and answered** in 54 s. **A slow upstream
> is not a stalled one**; vero-lite replied before the edge could cut in. s216 replaced
> *slow* with *never answers*: a socket that `bind`s and `listen`s but **never calls
> `accept()`**, verified from **inside the app container** (connect in 0.013 s, then
> `TimeoutError`, zero bytes). Two runs positive-control each other — a 120 s window
> yielded only `T_edge > 120 s`, recorded **INSUFFICIENT-EVIDENCE, not a pass**, and it
> missed by **five seconds**; a 600 s window returned **HTTP 524 at 125.19 s**.
> ⚠️ **Cloudflare documents 100 s; the measured value is 125 s** — the path is a
> `cloudflared` Tunnel, not a proxied origin, so a run that had trusted the published
> number would have concluded the cut-off was unreachable.
>
> **Cray's ruling is what produced that number.** Offered the `≥ 54 s` bound as
> discharging P4(i), Cray typed that **a bound is not the number the clause asks
> for**. Had Code accepted the bound on its own judgement it would have been rewriting
> an AC to fit the evidence available, and neither the 125 s nor the Tunnel-vs-docs
> finding would exist.
>
> **AC-12 is the reusable one.** The next move *looked* like a `plan-drafter` dispatch
> — Code cannot author ADRs. Verifying the fact-pack first showed all three
> "unrouted" ADR-0035 amendments had **already landed on 2026-08-06 in `06e2b84`**;
> only the tick was missing. Same shape as #1089's unmet "Record which was used".
> **A doc saying "not done" is a claim to grep, not evidence.**
>
> 🟡 **D-5 — a TRANSIENT Safe Browsing phishing flag** on the Access login callback,
> found while fetching a fresh cookie and lifted within ~30 min. **No security posture
> was involved:** the unauthenticated control stayed **302** on five paths across two
> runs, including under a browser UA. Four candidate causes were ruled out **by
> measurement** — a host-wide block (`/health` clean in the same Chrome), a path-prefix
> block (bare callback clean, the omnibox `Dangerous` chip gone, no bypass clicked), a
> flag inherited from a previous domain owner (RDAP: `registration` == `last changed`
> == 2025-12-15), and a neighbour on the zone (only one system resolves). **The cause
> is UNDETERMINED and is recorded as such** — Google Search Console is the only source
> that would report why, and only if it recurs.
>
> **Also:** the `ms-s1-admin` skill gained the **stripped-`"` trap** (#1092) —
> PowerShell strips double quotes when handing argv to a native exe — plus a comparison
> table of all three traps in that family. **Five residual items outlive PLAN-0100**;
> they are carried as a pointer in Active TODOs and none of them gates anything.

## Rotated this reconcile (session-221, 2026-08-10 — energy's live migration COMPLETE + PLAN-0103 Step 9 headroom MEASURED; #1119/#1118 reconciled)

### Current-Focus block — Session 217

> **Session 217, 2026-08-08 (head_commit `f987888` → `36e5735`) — two PRs merged
> (#1095, #1096), 0 open. Theme: PLAN-0102 is COMPLETE 11/11 and ARCHIVED — the
> L1 loop-detect guard is RETIRED, and executing the PLAN found three defects in
> the PLAN itself that share one root cause.**
>
> **Why L1 went.** It keyed on the same **file**; ADR-013 E.4 ratified "the same
> **problem**", which is what L2/L3/L4 key on — so the retirement narrows the
> implementation *toward* the Accepted ADR. Across L1's entire live history:
> **zero true positives**, against **≥ 56 denies over 4,201 Write/Edit ops**
> pre-AC-7 (~1.33 % of every edit hard-walled) and 0 denies / 0 organic warns
> over 1,369 ops after. **No ADR amendment** — E.4 never named L1 and
> `0013:333-336` delegated stateful loop-detection to PLANs, so L1 had zero ADR
> backing and an amendment would have *created* the ratification it never had.
> Also eliminated: the three harness registrations that existed only for L1 —
> the PreToolUse `Write|Edit` one spawned a Python process on **every single
> edit** to compute what is now a guaranteed no-op.
>
> **The evidence discipline is the transferable part.** L1 had not fired
> organically since AC-7, so a test that merely observes silence passes
> *identically* before and after the excision. Every absence is therefore paired
> with a live control in the same run: L1 deny **YES→NO** beside L4 deny
> **YES→YES**; L1 warn **YES→NO** beside the shell-hygiene advisory
> **YES→YES**. Both AC-11 probes reintroduced their exact defect and went RED.
>
> 🔴 **Three PLAN defects, one root cause — worth carrying to the next excision
> PLAN.** s206's R2 walked the call graph **backwards** from `LoopType.FILE_EDIT`
> and found the name-less sites; **nobody walked it forwards** from the functions
> being deleted, so every callee reachable only from an L1 entry point stayed
> invisible. Step 4 said to KEEP two imports whose only callers it deletes (and
> never mentioned a third); Step 3 named `_apply_commit_reset` but not the four
> symbols it exclusively owned; Step 5 omitted three constants. ⚠️ **AC-9 would
> not have caught the worst of them** — ruff flags a dead *import* but not a dead
> *private function*, so `_state_path()` would have shipped dead past a green
> gate. **Also a live-behaviour fix:** the deny message named three reset paths,
> all of them L1 paths deleted by this PLAN, on a message only L4 now reaches.
>
> **Also (#1095): D-4's direction RULED (a) by Cray — on a corrected premise.**
> Every prior record framed the fork as "teach the translator `group_by`", which
> is not the problem: `group_by` already works for `max`/`min`/`avg`/`sum`. What
> is unrepresentable is `count` **with** `group_by` — `_AGGREGATE_OPS` excludes
> `count` — so option (a) is four seams in one file, not the scope-uncertain
> prompt work the fork was priced against. ⚠️ **ADR-0036 is newly load-bearing:**
> it designs a "pick which vertical" portal, which *is* a landing surface, so it
> is an ordering prerequisite of the landing/framing layer. Nothing recorded that.

## Rotated this reconcile (session-222, 2026-08-11 — PLAN-0103 AC-8 clause 2 CLOSED in substance + ADR-0037 D2.7 MEASURED; #1121–#1125 reconciled)

### Current-Focus block — Session 218

> **Session 218, 2026-08-09→10 (head_commit `36e5735` → `faf48b6`) — ten PRs
> merged (#1099–#1108), 0 open. Theme: ADR-0036 ratified, its follow-on PLAN
> drafted, amended and fully ruled, and a second ADR spawned — the whole
> ratify→plan→rule cycle inside one session.** _[Corrected s219, `was an error`:
> this header read six PRs (#1099–#1104) closing `9160f4f` — it undercounted its
> own session as written.]_
>
> **What Cray ratified (typed, in-context).** ADR-0036 as drafted: **D1** scope
> ruling (a) — this enters vero-lite as an ADR extending ADR-0035 L9/D4, portal-repo
> files stay out; **D2** *a deployed vertical instance IS a system*, with the
> `oct-<vertical-id>` subdomain-label convention (`_`→`-`), labels only, no apex
> domain anywhere in this repo; **D5** vero-lite owns every vertical-system's
> {allowlist + env} profile, N near-identical allowlists accepted at N ≤ 3 under the
> Rule of Three with per-instance guards as the mitigation; **OQ-1** adopted —
> retire the bare `oct.` label rather than keep it as an alias. LOCKED-1/2/3 were
> already typed 2026-08-06 and were not re-asked. ADR-0035 D1–D4 untouched
> (LOCKED-4): D2's drift check shows system N+1 still costs the portal exactly the
> two artifacts the restated acceptance shape allows, so the **D4 reopening trigger
> does not fire**.
>
> **The two edits are one commit by construction.** ADR-0036 sat in
> `test_the_non_accepted_adrs_are_exactly_the_expected_set` because it was IN
> FLIGHT, not because it was exempt. Flipping without removing the entry reddens
> that assertion; removing without flipping reddens it from the other side. Edit
> **order** also matters and was observed — the test edit landed **first**, because
> flipping `Status` puts the ADR behind the G1 gate and blocks every later edit to
> it (sessions 67 / 110 / 126). The docstring is rewritten to state that as a
> general rule with this ratification as its worked precedent.
>
> **Verified behaviourally, not just green:** `gate.evaluate(ADR-0036)` → **DENY**
> (was allow), beside two live controls — `0014-WITHDRAWN` → allow, `0035` → DENY.
> Without them the DENY is equally consistent with "the gate denies everything".
>
> **Then the whole cycle ran to the end in one session.** PLAN-0103 drafted,
> amended, and **all eight slots RULED by Cray** (#1101/#1103/#1104). 🔴 **SD-1
> overruled both the drafter and Code's R2 concurrence** — both read ADR-0036 D5's
> "PLAN's to finalize" grant as sufficient; Cray ruled a new ADR is required, and
> was right: a DB on a public system changes what personal data it holds and what
> erasure can be promised — legal consequence, outliving the PLAN, needing
> attribution. **Two reviewers agreeing was not independent evidence**; both had
> priced the cost of *having* an ADR and neither the cost of *not*. **ADR-0037**
> (`Proposed`) is the result and the home for two previously-unrecorded findings
> (D6's scope, the audit-chain erasure boundary). All of it — the rulings, the
> eleven-consumer census, the second-assisted-system premise change, the gate map
> — is in the artifacts; read those, not a restatement:
> `docs/adr/0037-*.md` and `docs/plans/0103-*.md` §Surfaced decisions.
>
> **The suite caught the new ADR the same day the rule was written.** Adding
> ADR-0037 `Proposed` reddened `test_the_non_accepted_adrs_are_exactly_the_expected_set`
> — the same test edited that morning, whose rewritten docstring already
> prescribed the fix ("the entry and its Status line move together, in both
> directions"). Morning exercised removal; evening, addition. It caught it only
> because it enumerates `docs/adr/` on disk rather than a hardcoded census.

## Rotated this reconcile (session-223, 2026-08-12 — STATUS reconciled EIGHT PRs behind, #1126–#1133; the MS-S1 secrets-ACL exposure CLOSED)

Three blocks land here for two different reasons, stated so a later reader does not
have to infer which is which:

- **Session 219 — ROTATED OUT** of the R2 4-session window (223, 222, 221, 220).
- **Sessions 221 and 220 — TRIMMED IN PLACE**, still live in `docs/STATUS.md` in
  shortened form. R2's per-block cap (≤ 4,096 B, Cray-ratified s194) had never been
  enforced on them: s221 stood at 5,528 B and s220 at 7,613 B. **R4 requires the full
  original be archived before a trim lands — move, never drop** — so the pre-trim text
  is preserved below verbatim. STATUS now carries s221 at 3,813 B and s220 at 4,152 B.
  _(s220 finishes 56 B over the cap. Trimming further would have cut measured evidence
  to hit a number, which is gaming the criterion rather than meeting it; the overage is
  recorded instead of hidden.)_

---

### Session 219 — rotated out of the window

> **Session 219, 2026-08-10 (head_commit `faf48b6` → `ac93b64`) — two code PRs
> merged (#1109, #1111) plus the #1110 reconcile, 0 open. Theme: PLAN-0103 Steps
> 2 + 3 — published-ness stops being guessed and becomes **declared per system**,
> and the last guess left in the surface now refuses instead.**
>
> **Step 2 (#1109) — the declaration.** `PUBLISHED_EXCLUDED_VIEWS` is gone.
> `config.ALL_VIEW_KEYS` + `ui_published_views` refuse the process **at boot** on
> an unknown key, an empty set or a repeat; `main.py` emits `<meta name="ui-views">`
> from the **same substitution** as the profile tag, so the pair cannot
> half-arrive; `/meta` carries the same set (a test asserts the two carriers agree
> on a **non-default** value); `app.js` maps the keys **in order**, first = landing tab.
>
> **What Cray ruled (typed).** A page that declares no views **refuses to render
> and says so** — never guesses: a calm panel with no internals for the visitor
> plus a short statement of what vero-lite is (the failure page doubles as the one
> honest place to say it), and the precise diagnostic on the operator's console.
> The **empty-set boot refusal** is Code's extension of that reasoning
> (deploy-time terminal, never a visitor's browser) — flagged as inference, not
> ruling, and accepted. Cray also **took** Step 3's *optional* hero hardening.
>
> **Step 3 (#1111) — the last guess closed.** `_FALLBACK_VERTICAL = "procurement"`
> served procurement's hero to any vertical lacking one: correct while exactly one
> system was published, inverted by multi-system, since a hero is **bespoke per
> design partner** (ADR-0032 D1.2) — the failure mode is a Fastenal hero under an
> energy banner, which is why PLAN-0100 had to *edge-exclude* Tab G. Refusal moves
> from the **edge** (an allowlist that must remember to exclude G for every future
> heroless vertical) to the **route**, which knows: a heroless vertical now 404s,
> and the docstring asserting the fallback as current behaviour was fixed.
>
> 🔴 **Closing it exposed a test-integrity defect, not a code one.**
> `tests/api/test_demo_hero_routes.py` asserts **procurement's** hero throughout
> (Fastenal's ledger, `AST-CNC-014`, `SUP-RAPIDMRO`) while booting the default
> `energy` — it reached those numbers *through the fallback*, so it read as "the
> hero routes work on a default boot" while proving "the fallback works". The
> fixture now pins `OCT_VERTICAL=procurement`; **no assertion changed.**
>
> 🔴 **Step 3's own text named the wrong targets — the THIRD doc-vs-code mismatch
> in this PLAN.** `view-flow.js` is Tab **D**, published by energy all along and
> never unreachable; `view-monitor.js` has **no `isPublished()` at all**. Corrected
> scope: `view-hero.js` (G — dead branch today) and `view-monitor/case/export.js`
> (H/I/J — **no branch, which is correct**: fleet has a Postgres and Step 5 puts
> those on fleet's own allowlist). Property: publishing them adds no *unguarded*
> excluded-backend call — measured zero, now tripwired.
>
> **AC-2 is FULLY CLOSED** (first clause #1109, second #1111) and **AC-1 closed in
> #1109** with two documented literal-wording gaps; AC-2's census was wrong in both
> prior records (`was an error`) — **9** call sites, not 11. Record: PLAN-0103 row.
>
> **Evidence, both steps:** ruff + `ruff format` clean · `mypy --strict services/`
> Success (133 files) · `tests/` **3915** then **3926 passed / 8 skipped / 0
> failed** (3906 +10 −1, then +11 — exact arithmetic is the check that nothing
> vanished) · **nine non-vacuity probes RED**, notably Step 3's probe 1, which
> **restored the real fallback** rather than breaking the function, so the 404 test
> discriminates closed-vs-open and not working-vs-crashing · Step 2 also driven
> **live in a browser**. **#1109 / #1111 bodies** carry the tables and the probes.


---

### Session 221 — full pre-trim original (5,528 B; STATUS now carries 3,813 B)

> **Session 221, 2026-08-10 (head_commit `f78068e` → `e938cf6`) — two code PRs
> merged (#1119, #1118), 0 open, plus a host-state run that carries no PR of its
> own.** _[s222: session 221 did not end here — #1121, #1122 and #1123 merged
> after this block was written; they are recorded in the s222 block above and
> not restated.]_ **Theme: PLAN-0103 Step 8a landed together with the repair of a build
> context that could not build, and energy's LIVE system finally caught up with
> the rename the repo made two sessions ago.**
>
> ✅ **Step 8a SHIPPED (#1119) — every profile now carries its card copy, so
> AC-3 CLOSES.** `card-copy.md` exists in all three profile directories
> (`oct-energy`, `oct-procurement`, `oct-fleet-maintenance`), bilingual TH/EN,
> asserted **structurally** — section presence, not copy quality, which has no
> oracle — by `test_ac9_the_card_copy_is_bilingual_and_structurally_complete`.
> 🔴 **AC-9 is NOT closed by this:** its second clause is the portal-side
> assembly request (Step 8b), still owed, and itself a Step 10 input.
>
> 🔴 **The same PR repaired a compose build context that could not build — and
> "all three composes validate" had been reported while none of them could.**
> `context: ../..` from `deploy/published/<system>/` reaches `deploy/`, one
> directory short of the repo root; Step 4a moved the file deeper without
> following the relative path, and all three profiles inherited the error.
> `docker compose config --quiet` returned 0 over all three because it validates
> the **schema**, not whether the context resolves — so the check that was
> trusted in the s220 record could not have caught this. Now `../../..` in all
> three, guarded by `test_the_build_context_resolves_to_a_real_dockerfile`.
>
> ✅ **#1118 discharged the PLAN-0103 self-citation TODO** — the four stale
> citations are corrected in the PLAN itself. The fourth item that TODO carried,
> **whether Tab G's "Act — the human DOA gate" card should render at all on a
> personaless system**, is now homed in the PLAN as **SD-8, explicitly NOT
> RULED**, with three neutral options and no step assuming an answer. It stops
> being a STATUS-only item; it is Step 6's question and **Cray's call**.
>
> ✅ **energy's LIVE system migration is COMPLETE and Step 9's headroom is
> MEASURED — both under one typed Cray §8 go.** The demo now runs as compose
> project **`oct-energy`** on network `oct-energy_vero_oct`; project
> `vero-published` no longer exists on the host in any form — containers,
> network or volume. The prompt-log rows were migrated volume→volume and
> verified **byte-identical on both sides** (per-file checksums, not merely
> sizes), and the running app was proven able to **write** to the log as its
> non-root user — **refuting** the s215 silent-`OSError` failure mode rather
> than assuming it absent. The old volume was removed **last**, and the off-host
> backup — which held personal data outside the retention system — was deleted
> only after the edge check passed. **Read the record, never a restatement:
> `docs/logs/2026-08-10-oct-energy-migration-phase2-and-step9-headroom.md`**
> carries every number, the method, the pre-committed pass/fail reads, and the
> two things the run could not prove.
>
> ⚠️ **What the headroom measurement does NOT settle, so it is not read as
> broader than it is.** RAM and CPU do not constrain a second or third published
> system — but the binding constraint on a second *assisted* system was never
> container footprint; it is the resident LLM and the number of concurrent
> in-flight model calls. That is **ADR-0036 OQ-2, and it stays OPEN.** One term
> in the projection — Postgres idle footprint — is **declared unmeasured**
> rather than folded silently into the total. **Step 9 is MEASURED; AC-10 is NOT
> closed** — its first clause is discharged, its second (every bring-up carries
> its own explicit §8 go) stands.
>
> ⚠️ **A hardware correction worth one clause.** MS-S1's 128 GB unified memory
> is deliberately split roughly in half with the GPU, so only about half of it
> is visible to Windows at all. `CLAUDE.md` §5 / ADR-002 record the hardware
> figure, which is **true of the machine and false of what any process can
> allocate** — any projection starting from 128 GB overstates available RAM.
>
> ⚠️ **Honest miss:** downtime overran its planned window, and the overrun was
> an **instrument failure, not migration work** — a display-only
> `docker network ls` wedged inside a remote PowerShell script whose output was
> block-buffered, so the log sat at zero bytes while containers had already been
> removed. Zero bytes was not evidence that nothing had happened. The log file
> carries the diagnosis and what actually finished the run.
>
> **What remains on PLAN-0103:** Steps **6** (persona picker), **7** (fleet's
> Tab-H seed), **8b** (the portal-side assembly request — AC-9's open clause),
> **10** (bring-up — procurement first per SD-2's ruling, fleet gated on AC-11's
> RoPA, which is Cray's to author). ⚠️ **A hazard Step 7 must not walk into:**
> the operate-demo seed gate in `services/api/main.py` sits inside a
> `vertical == "procurement"` branch, so flipping `OCT_DEMO_SEED_OPERATE` alone
> for fleet is a **no-op that reads like a fix**. ⚠️ **AC bookkeeping:** the
> PLAN's checkboxes read `[ ]` for all eleven ACs on disk because Code cannot
> edit `docs/plans/` (G2 gate) — trust this record, not the checkbox tally.


---

### Session 220 — full pre-trim original (7,613 B; STATUS now carries 4,152 B)

> **Session 220, 2026-08-10 (head_commit `ac93b64` → `f78068e`) — two code PRs
> merged (#1114, #1116), 0 open. Theme: PLAN-0103 Steps 4b + 5 — every
> published system now has a profile of its own, and per-system isolation stops
> being a convention and becomes a guarded property.**
>
> ✅ **Steps 4b and 5 are COMPLETE.** Step 4 authors three profiles and Step 5
> authors two allowlists; procurement's half landed first (#1114) and fleet's
> closed both Steps (#1116). 🔴 **AC-3 is still NOT closed, and not for the
> reason the half-way record gave:** it requires **five** committed artifacts
> per profile — `{docker-compose.yml, published.env, cloudflared/config.yml,
> README, card copy}` — and **the card copy has been written for NO system**.
> That is Step 8a. **AC-4 and AC-5 remain closed** as guarded properties, and
> the third profile now exercises them rather than merely inheriting them.
>
> **Step 4b — procurement's profile.** `deploy/published/oct-procurement/` is
> authored, all four artifacts, **DB-less**. Published set `G,F`, default `G`,
> **no personas** — SD-3 and SD-4 ruled jointly, so the profile answers "which
> views" and "who can act" in one shape rather than two.
>
> **AC-4 resolved the standing instruction energy's compose addressed to this
> PLAN.** The compose project `name:` is now the profile **directory** name —
> asserted equal by a guard, not left to convention — and the fixed network
> `name:` key is **dropped** so compose scopes the network per project instead
> of pinning every system onto one. Energy was renamed `vero-published` →
> `oct-energy` across the project, both containers, the prompt-log volume and
> the derived image tag, with the ripple carried through `deploy.py`,
> `test_deploy.py` and ~19 runbook commands.
>
> **AC-5 closed as a property, not a checklist.** New
> `tests/deploy/test_published_profiles.py` (**45 tests**): no committed file
> outside a profile names two or more `oct-*` labels, and each profile names
> only its own. That is the form that survives a third system being added by
> someone who never read this PLAN.
>
> 🔴 **Step 4a left six broken operator paths behind, and executing 4b is what
> found them** — two in `published-demo-redeploy.md` written as Windows host
> paths, four in `oct-energy/README.md`. All six fixed, plus **a guard that
> reads the runbooks as instructions** rather than as prose, so the next move
> cannot silently orphan a command again. Two comments in
> `oct-energy/cloudflared/config.yml` that **Steps 2 and 3 of this same PLAN
> had falsified** were also corrected — the allowlist **row** was and is
> correct; only the stated reasons were stale. Doc-vs-code drift inside this
> PLAN is now a pattern, not an incident (see the PLAN-0103 self-citation TODO).
>
> 🔴 **The rename does not follow the LIVE system, and that is now an owed
> migration.** Measured on MS-S1 read-only under Cray's typed §8 go:
> `vero-published` is **`running(2)`** — app up 43 h healthy, cloudflared up 2
> days — the `vero-published-prompt-log` volume **holds real data**, and the
> host checkout sits at `00ddca0`, far behind main. Docker does not follow a
> rename, so a plain `up -d` under the new name would raise a **second parallel
> stack** and leave the prompt log stranded. A **§0b STOP CONDITION** was added
> to `published-demo-redeploy.md` and the migration is carried as its own
> Active TODO — offline tests cannot see any of this.
>
> **Evidence:** `tests/` **3926 → 3971 passed** (+45), 8 skipped, 0 failed —
> the arithmetic closes exactly · **eleven non-vacuity probes**, each RED then
> restored green · `ruff` + `ruff format` + `mypy --strict services/` all
> clean. **AC-4 and AC-5 are both CLOSED**; **#1114's body** carries the tables,
> the probes and the open Tab G question.
>
> **Steps 4b + 5 CLOSED — fleet's profile and allowlist (#1116).**
> `deploy/published/oct-fleet-maintenance/` is authored, all four artifacts.
> Published set `A,C,F,H,I,J`, default **A** (SD-3). It is the only published
> system carrying **both personas** (LOCKED-5) **and** a database (LOCKED-1 /
> ADR-0037), so it is the first profile forced to answer questions the other
> two never raised.
>
> **The database is a grant, not a default.** Three services instead of two:
> `postgres:16-alpine` on this system's own network, its own named volume, and
> **no `ports:` key at all** — worth stating because the repo-root dev compose
> *does* publish 5432, so "not published" here is a deliberate departure rather
> than something inherited. Both credentials are **required host-env
> pass-throughs with no default**, in the postgres service *and* inside the
> `DATABASE_URL` the app composes at runtime.
>
> ⚠️ **Energy's recommender defaults would have opened fleet's own landing tab
> on five anomalies.** Fleet lands on Tab A and the five `OCT_RECOMMEND_*`
> values are energy's; fleet's `measured_value` is a repair quote in THB
> (readings 1,800 / 2,400 / 3,200 / 15,000 / 48,000), so energy's threshold of
> 90.0 breaches **all five**. The real boundary is the **฿5,000 DOA ceiling** —
> pinned at 5000.0, exactly two breach and they route to **two different
> tiers**, which is the fixture's stated design intent: the demo shows the
> ladder ROUTING, which a single-breach fixture cannot.
>
> **The allowlist is 21 rows and every re-admission carries its own written
> basis**, because the original exclusions never shared one. Tabs I/J were
> excluded on SD-1(a) **DB-less** grounds — a basis that simply **dissolves**
> for a system ADR-0037 grants a database. Tab H's five routes were excluded by
> default-deny plus SD-1's C-3, which is **not** a storage fact, so `/runs`,
> `/runs/{id}`, `/runs/{id}/gate/resolve`, `/runs/{id}/cancel` and
> `/audit/verify` are each admitted on their own merits. Only routes the UI
> actually drives are admitted, and the export admits the **cover only**,
> keeping the typed s192 ruling in force.
>
> **Two new guards — and the second was widened by a probe that was itself
> mis-aimed.** (i) Only an ADR-0037-granted profile may declare a database,
> asserted in **both** directions. (ii) Every credential-bearing env value must
> be a required pass-through. The non-vacuity probe for (ii) switched the
> credential inside the app's `DATABASE_URL` connection string to a `:-`
> default and the guard stayed **green**: it was reading only
> `postgres.POSTGRES_PASSWORD`. The probe was mis-targeted, and **in failing it
> exposed a real hole in the assertion** — so the guard was widened to cover
> the connection string too.
>
> **Evidence (#1116):** `tests/` **3971 → 3994 passed** (+23), 8 skipped; the
> profile module collects **68** (was 45) — 45+23=68 *and* 3971+23=3994, so the
> arithmetic closes both ways · **nine non-vacuity probes**, each RED then
> restored green · **all three composes validated with `docker compose config
> --quiet` (exit 0)** — schema-valid, not merely YAML-parseable, and that check
> caught a real defect (the app service mixed sequence and mapping form in one
> `environment:` block, which is invalid YAML) · `ruff` + `ruff format` +
> `mypy --strict services/` clean.
>
> **What remains on PLAN-0103:** Steps 6 (persona picker), 7 (fleet's Tab H
> seed), 8 (card copy + portal request), 9 (MS-S1 headroom measurement), 10
> (bring-up). Two are live candidates and the choice between them is Cray's,
> not this record's: **Step 8a card copy closes AC-3 for all three systems at
> once**, while **Step 6's only consumer is fleet**, which now exists.
