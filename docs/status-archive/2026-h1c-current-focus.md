# STATUS.md — archived Current Focus blocks (2026 H1, continuation)

> **Period covered:** sessions 26 → 46 (newest-at-top within this file)
> **Sibling chain (letters ascend with time; the base holds the RECENT window):** [`2026-h1b-current-focus.md`](2026-h1b-current-focus.md) (session 25) → [`2026-h1c-current-focus.md`](2026-h1c-current-focus.md) (sessions 26–46) → [`2026-h1-current-focus.md`](2026-h1-current-focus.md) (sessions 116–128, base). This chain is **Current-Focus-only** and is SEPARATE from the rotation archive's `2026-h1b/c/d/e/f-status.md` chain — same letter scheme, different corpus.


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
