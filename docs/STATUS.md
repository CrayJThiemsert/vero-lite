---
last_updated: 2026-09-02T01:15:00+07:00
session: 268
current_batch: "s267 tail + s268 — EIGHT PRs (#1348-#1355): three of them are one lesson — a claim is only as good as the surface its consumer actually reads; #1352 cut the position #1349's rubric scored."
current_actor: code
blocked_on: "THREE Cray calls: the fl-21/fl-22 gold design; the Thai corpus (its hold EXPIRED — the existence test cut the position it was parked behind); the human half of the selection criterion."
next_action: "PLAN-0118 Step 3 (intake runner + grader), rehoming the three s268 orphans as it starts: AC-1(d)'s distractor definition, biomass_boiler's provenance, and §5a's call-site count."
head_commit: a0b743b
recent_commits: [a0b743b, f82bf94, 1e8780e, 6d7bd62, fa2da76, 269c15b, f06def0, fd0cb42, 466dc08, 377b3c0]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 267 tail + 268, 2026-09-01/02 (`8843000` → `a0b743b`) — EIGHT PRs
> merged ([#1348](https://github.com/CrayJThiemsert/vero-lite/pull/1348)–[#1355](https://github.com/CrayJThiemsert/vero-lite/pull/1355)),
> 0 open. Wider than one session: #1348–#1350 landed AFTER the s267 reconcile
> was written and were recorded nowhere. What it established: a claim is only
> as good as the surface its consumer actually reads.**
>
> 🔴 **#1349 ruled a rubric in the morning; #1352 cut the position that rubric
> scored, that same night.** Both read `gate_advisory.py`. #1349 narrowed the
> question honestly — brevity is already specified in code and restating
> figures already forbidden, so neither was ever open: score the **causal
> link** (amount → band → authority), not completeness. #1352 read one step
> further and asked what dissolves it — **does this output have a consumer?**
> The model's entire user input is `" ".join(reasons)` (`:171`), the same
> sentences already on the approver's screen (`:150`); the UI renders
> `reasons` and **never reads** `narrative` (`view-monitor.js:342`).
> `detail.narrative` has **one writer, zero readers**. Verdict
> **DO-NOT-WIRE** — the rubric was never wrong, it had no subject. Offline:
> **MS-S1 never contacted, the §8 go UNUSED**; questions SHA-256-**sealed
> before** the payload was read, against 17 real rendered sidecars.
>
> 🔴 **Two more claims sat beside their own refutations.** `grader.py`'s
> docstring claimed the headline scores fields the model "genuinely OWNS" —
> refuted **two paragraphs below itself** (#1350): the product overrides
> `affected_primary_key` (procedure path) and anchor-replaces it (reactive);
> `forbidden_primary_keys` is the *one* entity check that does measure product
> behaviour. Cray's typed s267 ledger ruling lived only in a commit message
> and a PR body — **surfaces no enforcer reads** — so it would have survived
> one reconcile (#1348); now in the runbook AND `status-scribe.md` with the
> **~900 B per-entry cap** and 🔴 **measure a block as its own contiguous `>`
> run, never header-to-header** (#1263 read 2,567 B as 4,936; s267 repeated
> it, 3,414 as 7,950).
>
> **PLAN-0118 drafted, ruled, started.** #1353 the Draft (466 lines,
> `plan-drafter`), #1354 all five SDs **RULED** by Cray (each took the drafted
> recommendation), #1355 Steps 1–2 — `gold.yaml`, **11 cases (8 scored + a
> 3-case injection band)**, three domains, the 2x2 enforced. #1351 gave the
> orphaned s267 findings tracked homes and **surfaced a fourth doing it**:
> §5.1's do-not-act instruction pointed at a test with **zero tracked hits**.
>
> **Evidence.** Every merge verified **by CONTENT, not ancestry** — 15 tokens,
> 0 hits pre-merge, ≥1 at merged `main`. Suite **4718 passed, 8 skipped, ×4**,
> matching s267; `ruff` clean (705 → 706 files); `mypy --strict
> benchmarks/intake_extraction/` **hand-run** — CI type-checks neither
> `benchmarks/` nor `tools/`. 🔴 **The Step-2 authoring check found a defect in
> ITSELF:** AC-1(d) read **8 of 8** by counting `recovery_value` — an expected
> answer — as a distractor, **vacuous by construction**; the tell was the
> number being too good. Fixed, criterion NOT relaxed; honest **4 of 8**.

> **Session 267, 2026-09-01 (`d420217` → `8843000`) — FOUR PRs merged
> ([#1343](https://github.com/CrayJThiemsert/vero-lite/pull/1343)–[#1346](https://github.com/CrayJThiemsert/vero-lite/pull/1346)),
> 0 open. What the session established: a comparison number measures the
> apparatus before it measures the thing — and two of this repo's own published
> numbers were the apparatus talking.**
>
> 🔴 **A p95 below 20 samples IS the sample maximum (#1344).** Nearest-rank
> picks `ceil(0.95n)`, which equals `n` for every `n < 20` — so the **n=14**
> procedure bar and the **10–13-case** NL lane published a **maximum** under a
> percentile's name in **every run ever made**. Fixed at the reporting layer,
> **four call sites**: the verdict survives in `tail_s`/`tail_label`, judged on
> the maximum and **labelled as one**. The NL half had **no test at all**
> before this. Battery **6/6 WITNESSED**.
>
> 🔴 **Turning the reasoning pass off costs rationale quality (#1346).** qwen q4
> on `fleet`, offline, no MS-S1: `full` **7/14** · `think_off` **4/14 (−3,
> material)** · `skip` **5/14 (−2, not established)**. The control gated it —
> the repeat reproduces the first run on **every** signal. 🔴 **The load-bearing
> negative recurs:** `names_amount` gives `skip` a perfect **14/14** while the
> ratified bar puts it **below** `full`, and `think_off` writes the **longest**
> rationales with the **fewest** roles. §13 saw that inversion **between two
> models**; this is the same one **inside a single model**.
>
> **#1345 — the server's own clock now reaches the dump.** Ollama's timings land
> in `CallMetrics` as raw nanoseconds plus derived **decode** and **prefill**
> rates, which extrapolate across prompt length where a wall-clock second
> cannot. `load_duration` separates a **cold load** from a slow model, and
> compounds with #1344: on a 14-item run a cold load into item 1 can be the
> whole reported "tail". Absent → `None` not `0`; zero → no rate, no crash;
> boolean → `None` not 1 ns. Battery **5/5 WITNESSED**.
>
> **#1343 — Lesson #0055**, six measured instances that had no home; the
> earliest survived **only in the archive**. A **LOW** score reads budget →
> flag → build → input *before* the model; a **HIGH** one suspects
> **non-engagement** (the invariant-score test needs a **mechanism count** to
> conclude); a **TIE or identical failure** proves the defect **shared**. Also
> recorded: every qwen figure on the NL benchmark is the **q4_K_M** build —
> **q8_0 has never run there**.
>
> **Evidence.** Probe batteries **11/11 WITNESSED**; the offline gate green at
> CI scope at **every** shipped sha, plus `mypy --strict benchmarks` by hand
> each time. Counts were measured by **stashing**, not carried: `a0a6559`
> **collects 4718** → **4722** (#1344) → **4726** (#1345); the final run
> **passes 4718 with 8 skipped**, which *is* that same 4726 collected — the two
> `4718`s are not a contradiction. Four Fable-5 specialists reviewed the
> measurement programme and **refuted the caller's central recommendation**.

> **Session 265-266, 2026-08-31 (`da06b17` to `668cb1d`) — TWELVE PRs merged
> ([#1329](https://github.com/CrayJThiemsert/vero-lite/pull/1329)-[#1340](https://github.com/CrayJThiemsert/vero-lite/pull/1340)),
> 0 open. Every merge gated on a CI conclusion measured **at a pinned sha** and
> verified on `main` **by content, not ancestry**. Tree clean. **PLAN-0117 is
> EXECUTED end to end, and the experiment it exists for is MEASURED.**
>
> **The unlock.** `Vendor` went 3 to 12 properties in two ruled bands: five
> synonym-carrying and four **dormant** — declared with a rich `description`,
> deliberately **no synonyms, no values**. All eight ACs closed; **14 of 14
> WITNESSED**. Measured on the built prompt: the five render with Thai synonyms,
> the four render name+type with **no aka clause**, and **no provenance prose
> reaches the prompt at all** — the dormant descriptions cost zero bytes, exactly
> as SD-3a bet.
>
> **The AFTER run (MS-S1, typed §8 go).** The unlock is **usable** — supplier band
> gpt-oss **1 of 3**, qwen **3 of 3**; both filtered on a property that did not
> exist before the PLAN. **Zero harm:** on the only like-for-like set both models
> scored **identically to BEFORE, case for case** (7 of 10 and 9 of 10, same cases
> wrong) despite a **+56% prompt** — PLAN-0117 F16's worry, measured and negative.
> Full read: `benchmarks/nl_query_feasibility/RESULTS.md`.
>
> 🔴 **A claim the s265 handoff made is RETIRED by measurement.** It named `fl-03`
> *the* discriminator. `fl-03` is a **Truck** question and `truck_class.synonyms`
> is still `None`; PLAN-0117 added synonyms to **Vendor** only, so a flip says
> nothing. Declared with a `retired:` marker beside the surviving copy (#1338).
>
> **The split metric earned its keep on first use.** `ceiling_rescue` measured zero
> instances of the step it was named after, so it became `ceiling_acc`,
> `ceiling_translated_n` and `phrase_rescue` with its own denominator. gpt-oss
> `fl-09` moved from *translate hard-failed* to *translated, and the query language
> cannot express it* — the old single number reads **0% to 0%**: no change at all.
>
> 🔴 **OPEN for Cray.** `fl-21` and `fl-22`: gpt-oss emits `group_by: null`, qwen
> `group_by: vendor_id`. gpt-oss's **prose answer is right** — the identity came
> from the phrase step reading records, not the aggregate. Whether gold should
> score **the answer** or **the query** is a design question; deciding it now, with
> the result visible, would relax a criterion after seeing the outcome.
>
> **The tree was lying, and two handoffs mis-diagnosed why** — a stray
> `core.worktree` in the shared git config, not the "UNC stat-cache artifact" both
> recorded. Fixed under Cray's go; the record and the `show-toplevel` pre-flight
> are lesson **#0053** and the `git-workflow` skill.
>
> **Evidence.** Suite **4681 to 4707 passed**, 0 failed, arithmetic checked at
> every step. Probe batteries **20 of 20 WITNESSED** across four runs.
>
>
> **And `main` went red on the clock alone** at the month boundary: the export
> windows its month in Asia/Bangkok while five test call sites named the month
> from the UTC clock, and those disagree for the last seven hours of every UTC
> month. Product unaffected — the route takes the month as a path parameter. One
> module already had the rule right, so it now has one home (#1340).

> **Session 264, 2026-08-31 (`4cfb267` → `3cd1609`) — FIVE PRs merged
> ([#1323](https://github.com/CrayJThiemsert/vero-lite/pull/1323),
> [#1324](https://github.com/CrayJThiemsert/vero-lite/pull/1324),
> [#1325](https://github.com/CrayJThiemsert/vero-lite/pull/1325),
> [#1326](https://github.com/CrayJThiemsert/vero-lite/pull/1326),
> [#1327](https://github.com/CrayJThiemsert/vero-lite/pull/1327)), 0 open, tree
> clean. **The `fleet` ceiling that blocked model comparison since s263 is broken
> — on a fourth axis, offline, with ZERO MS-S1 runs.**
>
> 🔴 **The blocker was never "harder items"; it was a missing axis.** β, α and
> consistency all grade *which* answer the model gave; none read the `rationale`.
> Scoring one question over the **six dumps already on disk** — does it name the
> human authority the spend routes to? — separates the tied models in **every
> cell, no overlap**: qwen **4–8/14**, gpt-oss **0–1/14**. No §8 go was needed or
> taken.
>
> ✅ **Fair by construction, not by assertion** (`b425bde`). The role vocabulary
> is the **intersection of a candidate set with the goal's own prose**, so a
> phrase is only demanded of a model that was handed it — here `head mechanic` /
> `fleet manager` / `owner`. The pre-fix goal (`0a1061f~1`) carries the identical
> clause, so the vocabulary is **unchanged across the goal fix** and the signal
> compares across all six cells; §11's β/α comparability line is untouched.
>
> 🔴 **The load-bearing result is NEGATIVE.** `names_amount` does **not** separate
> the models and **gpt-oss scores higher** (6/14 vs 5/14); mean length tracks
> verbosity. The intuitive *"state the amount"* rule ranks the models
> **backwards** — a new axis is a hypothesis, not a fix.
>
> ✅ **Bar RULED (Cray, typed): role-naming alone** (`e141338`) — the richer
> criteria rest on facts **the ontology does not carry**, and a rule may only
> demand what the run supplies. **Raising it is an ONTOLOGY move before a grader
> move.** Requiring the amount too: 0/14 vs ~3/14 — *unmeasurable*, not
> undesirable.
>
> ✅ **§13 records it and §12's blocking-prerequisite claim is RETIRED**
> (`b402cbf`) under `docs/conventions/retired-claims.md` — classified **superseded
> by new info, not an error**. ✅ **B2 lands the axis in the shipped grader**
> (`6743b4d`): a fourth lane with a consumer at every step, `goal` keyword-only
> and defaulting to `None` so **no goal ⇒ no check ⇒ β/α byte-identical**. The
> 268-test benchmark suite passing untouched IS that evidence.
>
> ✅ **STATUS reconciled out of its 84-byte corner** (`ec75c52`): 65,452 →
> 63,203 B, one asserted transaction — pre-flight **15/15**, post-write **13/13**,
> archives verified by byte **DELTA**, not presence. ✅ **Lessons `#0051`
> (a saturated benchmark may be missing an AXIS) + `#0052` (a criterion may only
> demand what the run supplies)** authored, plus scope fixes to `#0046`, `#0011`
> and `tools/probe_battery/README.md` (`3e067ab`).
>
> **Evidence.** Offline gate green at every sha — **4652 → 4656 → 4672 passed**,
> 8 skipped, each delta exactly the tests added; `mypy --strict services/
> verticals/` clean on 201 **and `benchmarks/` clean by hand** (CI checks neither);
> ruff + format clean; CI **pass** at all five shas. **Probe batteries 8/8 and 6/6
> `WITNESSED`**, `GAPS: 0`, lane isolation probed in **both** directions. Every
> merge verified by **content** with a negative control, never by badge.
> ⚠️ **Observation, not a finding:** qwen **q4** named roles *more* than q8 under
> the old goal (7 vs 4) — n=1 per side, gpt-oss reproducibility still unmeasured.

_[Current-Focus rotation ledger — **CURRENT window only** (R2, Cray s250; the ledger's OWN window plus a ~900 B per-entry cap, Cray s267); earlier entries travel with their blocks into [`2026-h1d-current-focus.md`](status-archive/2026-h1d-current-focus.md). Window = **264, 265-266, 267, 268**. ⚠️ **STATUS skipped s262** — the window is **259–260, 261, 263, 264** and no s262 block is backfilled. **THIS (s264) reconcile rotates the session-258 block** on the **window rule alone** — a fifth entered, the window is four — **not a cap overage**: measured **2,852 B** against the 4,096 cap. ✅ **Pinned, asserted, then measured by DELTA:** first AND last line pinned, neighbour-bleed checked, ledger checked OUT of the slice, checked ABSENT from the target *before* the write, then presence-in-archive and absence-from-STATUS verified **separately**. Also rotated: the s253 RD row and **7 completed `[x]` TODO rows** (s250/255/256/258, all older than the window) — archived per R4 rather than dropped, matching recent practice. Substance keeps tracked homes: `benchmarks/model_compare/RESULTS-1.6.md` §13 and `benchmarks/procedure_baseline/rationale_regrade.py` **THIS (s265-266) reconcile rotates the session-259-260 block** on the **window rule alone** — a fifth block entered and the window is four — **not a cap overage**: measured **3,038 B** against the 4,096 B cap. Pinned, asserted, then measured by DELTA: a 13-assertion battery fixed BEFORE any write pinned the slice by its first AND last line, checked neighbour-bleed in both directions, checked this ledger OUT of the slice, and checked the slice ABSENT from the target before the append; sed then extracted the slice and independently reproduced the same 3,038 B. Archive **+3,438 B** (slice plus its rotation header) and the s254 ADR-0038 RD row **+852 B**, both verified present-in-archive and absent-from-STATUS separately. Headroom is the real finding here: with zero completed `[x]` rows left to rotate (s264 took the last seven), the only lever was writing this block **under** the 4,096 cap. **Active TODOs is 27,062 B, 43% of STATUS across 45 open rows** — and it, not the Current-Focus window, is why R1 headroom keeps vanishing. The s264 next_action already named the rehome; it is still unaddressed and is now the binding constraint on the next reconcile. **THIS (s267) reconcile rotates the session-261 block** on the **window rule alone** — a fifth entered, the window is four — **not a cap overage**: the caller re-measured each block as its own contiguous `>` run (2,992 / 3,384 / **3,414** / 3,669 B), **all under** the 4,096 B cap; the earlier *7,950 B / 94% over* figure was a measuring bug that ran to the end of the SECTION and swallowed this ledger. 🔴 **The growth was the LEDGERS, not Active TODOs** (caller-measured: CF 6,793 + RD 8,143 B, ~22% of the file; the RD one **never pruned until now**). Per Cray's typed s267 ruling both ledgers now carry the **current window only** at **~900 B per entry**; out-of-window entries were returned **verbatim** for archiving (R4). ⚠️ **No byte delta measured here — no shell; the caller owes `wc -c` + append + verify-by-DELTA.** **THIS (s268) reconcile rotates the session-263 block** on the **window rule alone** — a fifth entered, the window is four — **not a cap overage**: caller-measured, each as its own contiguous `>` run, s267 **3,103** · s265-266 **3,385** · s264 **3,670** · s263 **2,993 B**, all under the 4,096 B cap. 🔴 **Its s263 entry here is NOT re-archived — the pre-write assertion caught it:** both ledgers were archived **whole and PRE-PRUNE** at s267 (R2 permits it), so R4's move duty is discharged; a second copy would duplicate a move-only archive. ⚠️ **STATUS was PARTIALLY updated during s268** (`377b3c0`/`fd0cb42` touched Active TODOs / Next Steps), so this completes the **frontmatter + CF + RD** half. ✅ **Caller-measured:** from **61,774 B**, still under R1; CF archive **+3,586 B**, byte-identical to `git show HEAD:`, present-once and absent-from-STATUS verified separately.]_


## Prior focus (archived)

PLAN-003, PLAN-0005, PLAN-0006, PLAN-0007 and PLAN-0008 are all merged
and archived to `docs/plans/done/`; the Cowork-as-Tier-1 trial concluded
and was ratified permanently by **ADR-009** (Cowork = merged Tier 0 +
Tier 1 workspace; commits stay Code-exclusive). Full detail lives in
`docs/plans/done/`, the Recent Decisions table below, and git history.
_[Corrected s169, `was an error`: this paragraph claimed PLAN-004's
"Phase B/C remain deferred", which both the Next Steps section and the
Active TODO refute — **Phase A + B are COMPLETE (s35)** and only the
optional Phase C polish is deferred. The stale sentence is dropped rather
than restated: the Active TODO owns that status.]_

## Recent Decisions (last 10)

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-09-01 | **s267 tail + s268 — EIGHT PRs (#1348–#1355): three are one lesson — a claim is only as good as the surface its consumer reads.** 🔴 **The `llm_assist` gate advisory is DO-NOT-WIRE** — the model's whole input is `" ".join(reasons)`, already on the approver's screen, and `detail.narrative` has **one writer, zero readers**; #1349's rubric, ruled that morning, scored a position #1352 cut that night. Offline, **§8 go UNUSED**. ✅ **PLAN-0118 drafted (#1353), five SDs RULED (#1354), Steps 1–2 shipped (#1355)** — 11 intake cases, 8 scored. 🔴 The Step-2 authoring check was **vacuous by construction** (8 of 8 → honest **4 of 8**). | `a0b743b` / [#1352](https://github.com/CrayJThiemsert/vero-lite/pull/1352) / [#1355](https://github.com/CrayJThiemsert/vero-lite/pull/1355) / `benchmarks/model_compare/DECISION.md` §5a-RESULT |
| 2026-09-01 | **s267 — FOUR PRs (#1343–#1346): two published numbers were measuring the apparatus.** 🔴 **A p95 below 20 samples IS the sample maximum** — nearest-rank `ceil(0.95n)` = `n` for `n < 20`, so the n=14 procedure bar and the NL lane published maxima under a percentile's name in **every run ever made**; fixed at the reporting layer (`tail_s`/`tail_label`), 4 call sites, NL half previously untested. 🔴 **`think_off` costs rationale quality** — qwen q4 `fleet`: `full` 7/14 · `think_off` 4/14 · `skip` 5/14, control-gated; `names_amount` still **inverts** the ratified bar, now inside one model. Batteries 11/11 WITNESSED. | `8843000` / [#1344](https://github.com/CrayJThiemsert/vero-lite/pull/1344) / [#1346](https://github.com/CrayJThiemsert/vero-lite/pull/1346) / `benchmarks/model_compare/RESULTS-1.6.md` |
| 2026-08-31 | **s265-266 — TWELVE PRs (#1329-#1340): PLAN-0117 EXECUTED and its experiment MEASURED.** `Vendor` 3 to 12 properties in two ruled bands; all 8 ACs closed, 14 of 14 WITNESSED. The AFTER run on MS-S1 (typed §8 go) shows the unlock **usable** (supplier band gpt-oss 1 of 3, qwen 3 of 3) and **zero harm** — `fl-01`..`fl-10` identical to BEFORE case-for-case on both models despite a +56% prompt. 🔴 The s265 handoff's `fl-03` discriminator claim is **RETIRED by measurement** (`truck_class` gained no synonyms). 🔴 **OPEN:** whether `fl-21` and `fl-22` should score the answer or the query shape. | `docs/plans/0117-fleet-ontology-supplier-evaluation-facts.md` · `benchmarks/nl_query_feasibility/RESULTS.md` · [#1335](https://github.com/CrayJThiemsert/vero-lite/pull/1335) · [#1337](https://github.com/CrayJThiemsert/vero-lite/pull/1337) |
| 2026-08-31 | **s264 — THREE more PRs (#1325, #1326, #1327): the axis becomes a shipped lane, and STATUS gets its headroom back.** ✅ **B2** puts the rationale check in `grader.py` as a **fourth lane with a consumer at every step**, `goal` keyword-only + `None`-default so **no goal ⇒ no check ⇒ β/α byte-identical** — the pre-existing 268-test suite passing untouched is that evidence; lane isolation probed in **both** directions. ✅ **STATUS 65,452 → 63,203 B** (headroom 84 → 2,333) via one asserted transaction, archives verified by byte **DELTA**. ✅ Lessons **#0051** (a saturated benchmark may be missing an AXIS, not needing harder data) + **#0052** (a criterion may only demand what the run supplies) authored. | `3cd1609` / [#1326](https://github.com/CrayJThiemsert/vero-lite/pull/1326) / [#1327](https://github.com/CrayJThiemsert/vero-lite/pull/1327) / `benchmarks/procedure_baseline/grader.py` |
| 2026-08-31 | **s264 — TWO PRs (#1323, #1324): the `fleet` ceiling is broken on a FOURTH axis, offline, with zero MS-S1 runs.** Scoring the `rationale` from the six dumps already on disk separates the tied models in **every cell, no overlap** — qwen **4–8/14**, gpt-oss **0–1/14**. 🔴 **The load-bearing result is NEGATIVE:** `names_amount` does not separate them and gpt-oss scores *higher*, so the intuitive "state the amount" rule would rank them backwards. ✅ **Bar RULED (Cray, typed): role-naming alone** — the richer criteria rest on facts the ontology lacks, making a higher bar an **ontology move before a grader move**. ✅ §12's *blocking-prerequisite* claim **RETIRED** (superseded, not an error). | `9cf5549` / [#1323](https://github.com/CrayJThiemsert/vero-lite/pull/1323) / [#1324](https://github.com/CrayJThiemsert/vero-lite/pull/1324) / `benchmarks/model_compare/RESULTS-1.6.md` §13 |
| 2026-08-30 | **s263 — ONE PR (#1321, five commits): stage 2c completed the five-cell matrix, and the matrix then found a defect in OUR OWN procedure.** 🔴 **The `fleet` procedure GOAL told the LLM to check a gate that is evaluated deterministically downstream with no LLM**, withholding its threshold — live on **11 of 14** items, the rule fires on **one**. Rewritten (`0a1061f`, runtime spine), verified on two models: qwen q8 β/α **85.7 → 100%**, consistency **12/14 → 14/14**; gpt-oss identical, its 100% being **compliance-by-omission** (gate named in **1 of 17** items vs **17 of 17**). 🔴 **~60% of the q4 handler gap was COMPRESSION.** 🔴 `fleet` is at **ceiling for both models**. | `43f707a` / [#1321](https://github.com/CrayJThiemsert/vero-lite/pull/1321) / `benchmarks/model_compare/RESULTS-1.6.md` |
| 2026-08-29 | **s261 — FOUR PRs (#1310–#1313): two of three phase-1.6 audit findings CLOSED; the third's model is on the box, unrun.** 🔴 **`think=False` does NOT turn gpt-oss thinking off — MEASURED** (a **3,105-char** trace on a live 1-item run), so 1.6's `gptoss/full` and `gptoss/think_off` were **one request**: the §4 *"p95 anomaly"* is two runs of one config, and the next matrix has **FIVE cells, not six**. 🔴 `num_predict` was unset, so a deadline **discarded every token produced** — bounded now. 🔴 The shell-hygiene advisory fired on **the idiom it prescribes** (30.8% of 950 commands); FP 3→0. | `41c0d4c` / [#1313](https://github.com/CrayJThiemsert/vero-lite/pull/1313) / `benchmarks/model_compare/RESULTS-1.6.md` |
| 2026-08-28 | **s259–260 — ONE PR (#1309, five commits): a 7-phase FDE readiness programme is RATIFIED (Cray) and phases 0/1/1.5/1.6 shipped.** 🔴 **Phase 1.5's *keep `gpt-oss:20b`* verdict is SUPERSEDED** — every challenger "error" was a **deadline cut** (counts matching 3/3, 2/2, 0/0), so that count measured the **harness, not the model**. 🔴 **Turning the reasoning pass off improved BOTH models** (gpt-oss β 10→30%, qwen 30→80%), making it a **pipeline** property, not a model one. ⚠️ **No model is bound** — one repeat per cell against a measured **45% flip rate**. | `7306f17` / [#1309](https://github.com/CrayJThiemsert/vero-lite/pull/1309) / `benchmarks/model_compare/RESULTS-1.6.md` |
| 2026-08-27 | **s258 — ONE PR (#1307): PLAN-0107 COMPLETE 15/15 and ARCHIVED; AC-9 closed on Cray's ruled option (b).** 🔴 The golden corpus was **not an oracle** — invariants 1–4 compare each file to itself, so `tools/golden_trace/` plus a new **invariant 5** now score the system's LIVE composition against the recorded envelope (`created_at` the sole exclusion, measured 1 of 16 keys). 🔴 **AC-12/13/14 had landed unticked while STATUS claimed them closed, and `check_ac_consistency.py` reported clean** — it searches `AC-N` backwards from `CLOSED`. **That guard gap is NOT fixed.** | `d78eebe` / [#1307](https://github.com/CrayJThiemsert/vero-lite/pull/1307) / `docs/plans/done/0107-*.md` |
| 2026-08-27 | **s257 — THREE PRs (#1303–#1305): PLAN-0107 Phase C closes AC-12/13/14/15 — the PLAN goes 10/15 → 14/15; only AC-9 remains, BLOCKED on a Cray ruling.** 🔴 **Three "gates" that read as protection enforced nothing:** a `pyproject.toml` coverage threshold nothing measured (DELETED per Cray's typed ruling; the same claim struck from `PULL_REQUEST_TEMPLATE.md`), and a cache-bust test freezing per-file minima over **9 of 21 JS / 0 of 4 CSS files** — replaced by a relational diff check. 🔴 **AC-12's dead-port probe exits 1 while pytest reports `4005 passed, 484 skipped`** — 484 skips against a normal 8. | `1993bda` / [#1305](https://github.com/CrayJThiemsert/vero-lite/pull/1305) / `docs/plans/done/0107-oracle-coverage-hardening.md` |

_[Recent-Decisions rotation ledger — **CURRENT window only** (R2; the ledger's own window plus a ~900 B per-entry cap, Cray s267); earlier entries travel with their rows into [`2026-h1-status.md`](status-archive/2026-h1-status.md). Window = **264, 265-266, 267, 268**. The oldest row (**s254**) rotated to the same file at THIS (s267) reconcile — one s267 row entered, so one left to hold the table at ten, on the **count rule alone**. Its substance keeps the homes the row itself names — `docs/plans/done/0115-*.md` for PLAN-0115's four SDs, ADR-0018 VX-1 for the struck clause — **read off the row, not re-grepped here**, so `asserted-not-verified`. 🔴 **This is the FIRST reconcile ever to prune THIS ledger:** under Cray's typed s267 ruling it now holds the current window only at ~900 B per entry, and every out-of-window entry — back to the s243 cont. one — was returned **verbatim** for archiving (R4, move-never-drop), never deleted. ⚠️ No byte delta measured — no shell; the caller owes `wc -c` + append + verify-by-DELTA. The oldest row (**s255**) rotated to the same file at THIS (s268) reconcile — one s268 row entered, so one left to hold the table at ten, on the **count rule alone**; caller-measured **651 B**. Its substance keeps the homes the row itself names — `docs/plans/done/0115-*.md` for PLAN-0115, ADR-0018 VX-1 for the Stop-hook `systemMessage` — **read off the row, not re-grepped here**, so `asserted-not-verified`. Also rotated: the **one completed `[x]` TODO row** (the s268 gate-existence verdict, **949 B**), substance homed at `DECISION.md` §5a-RESULT. 🔴 This ledger's **s263 entry is NOT re-archived** — archived whole and PRE-PRUNE at s267, so re-appending would duplicate. ✅ **Caller-measured:** archive **+2,195 B**, both rows byte-identical to `git show HEAD:`, present-once and absent-from-STATUS verified separately.]_

## In-Flight Discussions

- **OPEN QUESTION for Cray — does a skill's registry table *bind*?** (Code's observation, not a ruling.) s210's closing notice asserted the four-work-stream registry table in `.claude/skills/stream-status/SKILL.md` (#1062) is **canonical**, and that a carrier-artifact change must update it **in the same PR**. The table as *reference* is fine; the **same-PR obligation** is the part that would have to live in `CLAUDE.md` or an ADR to bind — §1 places `.claude/skills/` at **Tier 2.6, derived, no independent precedence** (ADR-0017 D6). **Cray's call: promote it, or keep the table advisory.**
- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm — **not yet drafted**, and it needs a fresh ADR number. _[The old "≥ ADR-014" floor recorded here was **moot** — see the Active TODO below, corrected s141: ADRs now run past 0032 and `0014-WITHDRAWN.md` exists. Kept as one pointer rather than two divergent copies.]_
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).

## Active TODOs

- [ ] **🆕 NOW THE LIVE NEXT ACTION — the machine half of the selection criterion.** Unblocked s268 by the verdict above. Of the two positions whose next consumer is **code**, the NL lane already runs its real consumer (`answer_question`); **intake extraction has no benchmark of any kind** (measured s268 — five suites under `benchmarks/`, zero grep hits for `intake`, against a shipped seam at `services/engine/llm/intake.py`). 🔴 **Cray's ruled order for what follows:** the **human half** only after the existence test — which has now run, so it is unblocked but should be scoped **down** by specialists posing questions for Cray to rule on; and the **Thai corpus** was deliberately not started because the existence test might cut the position it would serve — **it did**, so that reason is now spent and the corpus needs its own decision rather than inheriting a hold. **Read:** `benchmarks/model_compare/DECISION.md` §5a-RESULT.
- [ ] **🆕 THREE s268 findings live ONLY in a gitignored handoff — ZERO tracked hits in `docs/`, `benchmarks/`, `tests/` (caller-grepped at close).** **(i)** AC-1(d)'s real test must count **same-reading-same-unit** distractors, not magnitude-proximate numbers — the `thr/3..thr*3` window **excludes `rm-02`'s 0.6 kPa clean-bag reading**, the very distractor the control wants; **rehome into PLAN-0118 AC-1(d) at Step 3**. **(ii)** `biomass_boiler` is **Code's stated assumption, not Cray's pick** (Cray picked telecom base-station power + rice mill; Step 2 needs ≥3) and `gold.yaml` records the domain, **not its provenance**; if vetoed, `bo-01`/`bo-02` re-author and the 2x2 + discordant count need re-checking (`bo-01` is discordant). **(iii)** `DECISION.md` §5a says *"all four call sites"*; the caller counted **three** production sites plus the test file — harmless to DO-NOT-WIRE; fix in passing. **Read:** `docs/plans/0118-intake-extraction-benchmark.md`.
- [ ] **🆕 Cray's s267 ledger ruling is not yet on its ENFORCERS' input surface.** Typed s267: **both** rotation ledgers carry the **current window only**, each entry capped at **~900 B**. Applied in this file at the s267 reconcile, but written nowhere the enforcers read — `docs/runbooks/memory-architecture.md` §R2 and `.claude/agents/status-scribe.md` still window the Current-Focus **blocks** only, with no ledger window and no per-entry cap. Per §4's routing rule, a rule absent from its consumer's input surface is for that consumer **not written**, and both ledgers will regrow. **Read:** `docs/runbooks/memory-architecture.md` §R2.
- [ ] **🆕 CRAY'S CALL — the *45% flip rate* in Current Focus is CONTRADICTED, not re-measured.** s262 ran `fleet` × `qwen/full` twice under a 16,384 cap: **20 of 20 items byte-identical** (drafts, rationales, `eval_count`), while latency differed on 17 — two genuine runs. The 45% was measured on `energy` **before `num_predict` existed**, when generation ran to a client timeout and was CUT; a wall-clock cut is not reproducible by construction. **Hypothesis: it measured the harness.** One repeat per cell settles it. **Do not budget repeats on the 45% until then.**
- [ ] **🆕 CRAY'S CALL — the PORTABLE CORE of Lesson #0049 has no cross-project home, and no such surface exists yet.** Measured s262: `~/.claude/skills/` and `~/.claude/CLAUDE.md` **do not exist**, and Tier-0 auto-memory is path-scoped to this repo — so every reusable practice built here is vero-lite-only. Cray's intent (s262): **prepare, do not build** — no second project exists, and §1's Rule of Three says the abstraction waits for something to extract *toward*. **Trigger: the first new project.** **Read:** `docs/lessons/0049-measure-generation-demand-not-the-cap-that-happens-to-work.md` §PORTABLE CORE.
- [ ] **🆕 CRAY'S CALL — the fleet benchmark awards 100% to *"answer `escalate` on every item without reading anything"*.** `canonical_handler` is `escalate` for **all 14** breach items, so β cannot separate comprehension from a constant. ✅ **The CEILING half is solved (s264)** — the rationale axis separates the models (qwen **4–8/14**, gpt-oss **0–1/14**) — but that restores *discrimination*, **not validity**: a model can name a role and still always-`escalate`. Harder items remain the only fix for the exploit itself. **Read:** `benchmarks/model_compare/RESULTS-1.6.md` §13.
- [ ] **🆕 CRAY'S CALL — the phase-2 MODEL DECISION is still unbound, and `fleet` can no longer discriminate.** ✅ **Audit finding 3 (quantisation) is CLOSED s263** — q8 fixed **exactly the five items** q4 missed; ~60% of the handler gap was compression, not the model. 🔴 Both models now score **100/100/14-of-14**, and every cell but 4-bit qwen `full` is **n=1**. 🔴 **A comparability line exists at `0a1061f`:** §8–§10 was measured against the defective goal directive and does **not** compare with anything after it. 🔴 **Every live run needs a NEW typed §8 go.** **Read:** `benchmarks/model_compare/RESULTS-1.6.md` §9–§12.
- [ ] **🆕 Nothing measures Thai prose QUALITY — and that is what phase 2's LLM tasks actually are.** Everything scored so far grades structure, handler picks and pinned strings; nothing reads the prose a Thai operator would be handed. `DECISION.md` reserves the question for a **blind read that has never been run**, so no model choice can be defended on prose quality today. **Cray's call: schedule the blind read, or accept the gap explicitly.** 🆕 **s267 adds a second, narrower call that gates it:** the **Thai-brief rubric** — brevity vs completeness — which gates the ratified Thai-corpus option; until it is ruled, no Thai brief can be scored either way. **Read:** `benchmarks/model_compare/DECISION.md`.
- [ ] **🆕 CRAY'S CALL — PLAN-0116's THREE SDs are unruled and had no row here until s257.** `docs/plans/0116-deterministic-claim-rollup-tool.md`, `Status: Draft`, 0/8 ACs, 3 Steps, one PR, deterministic-offline. **SD-1 is the heavy one** — the mixed case (∃ vs ∀ reading); it hard-codes forever an interpretation of Cray's own typed four-line rule, and `_rollup.py` cannot be written until it is ruled. SD-2 (measure labelling stability here?) and SD-3 (exit-code contract) are light. ⚠️ **Measured s257, and it is the reason to rule deliberately rather than by default:** the tool ships with **zero wired producers and zero wired consumers** — both are cut by name in its Out of Scope — so on day one its only caller is its own test suite. Until s257 the SDs were carried only by a `blocked_on` line naming #1301 as *open*, and #1301 merged — the drift this row exists to stop.
- [ ] **🆕 CRAY'S CALL — the s256 walk's residue is TWO RUNS, not two cases; leaving them parked is the current lean.** Measured s257 LIVE, read-only, under three typed gos: both cases **ABSENT** (control-backed); `governed_repair_approval@41bb78353e7c4138` is still `waiting_human` at a resolvable `approve` gate, `@d8f5a677b8f73b3b` `completed`. 🔴 `DEMO-RESET.md` is **not** the tool for a visitor-created id; the per-case seam is `delete_case`. ✅ Resolving that gate is **harmless** — proven offline, not by clicking live ([#1304](https://github.com/CrayJThiemsert/vero-lite/pull/1304)). ⚠️ `audit_log` unchanged at 64 rows, so **how the cases went away is measured but unexplained**. **Read:** `docs/logs/2026-08-27-s257-fleet-walk-residue-readonly-probe.md`.
- [ ] **🆕 CRAY'S CALL — `.claude/worktrees/` is 1.8 GB and `git worktree prune` cannot reach most of it.** Measured s256 by set difference, jointly with the parallel session: **19 directories on disk · 7 registered · 6 prunable · 12 UNREGISTERED**. Prune touches **6 of 19**; the other 12 git no longer knows about and only a manual delete removes. Largest: `eloquent-chatelet` 257 MB · `recursing-chatterjee` 163 · `wizardly-hopper` 161 · `youthful-driscoll` 150. **Nothing deleted — 1.8 GB is irreversible and out of scope for Code.** Related: Cray ruled parallel sessions onto separate worktrees this session, so the set will keep growing.
- [ ] **🆕 CRAY'S CALL — a battery skip is indistinguishable from "no active goal" in the trail.** `_goal_gate.py`'s early return fires before any `record_evaluation` for BOTH the battery-lock stand-down and the no-goal case, so `goal.json` stays **byte-identical** — nothing can later establish that the gate ever stood down for a battery. This is the **price PLAN-0115 SD-2's zero-residue ruling pays**, not a defect, but the price was never measured when it was ruled. Changing it needs a new SD, not a trim. **Read:** `docs/logs/2026-08-26-sd-premortem-replay-experiment.md`.
- [ ] **🆕 ADR-016 SB-3 enumerates THREE load-gate refusals; the SHIPPED Step 1 has FOUR.** The fourth — `when_absent` supplied with **no `scope_by`** — was Cray-ratified at the #1275 merge (typed, s251), but SB-3's body still names only the three `scope_by`-present cases; re-checked in the ADR at the s251 reconcile. **Cray's call: amend the ADR, or leave the fourth recorded in the PLAN.** ⚠️ Whoever opens ADR-016 for this should also repair its **two dead pre-archive PLAN pointers** (`0052-*` and, since s252, `0113-*` — both now under `docs/plans/done/`). R8 exempts `docs/adr/` **temporarily and by design**, because G1 blocks Code from editing an Accepted ADR; the exemption's own comment says to remove it in the same change that lands those fixes. **Read:** `docs/adr/0016-governed-procedure-engine.md` §SB-3 · `docs/plans/done/0113-scope-event-fired-run-to-its-firing-case.md`.
- [ ] **🆕 CRAY'S CALL — should R2 cap the Active TODOs *COUNT*, and govern the Recent Decisions trailing ledger? Still unruled, and the pressure is now structural.** 🔴 STATUS entered s263 at **64,584 B against R1's 65,536-byte HARD ceiling — 952 B of headroom**, and is **~15 KB over the 49,152-byte soft target**; the s263 block only fit because s257 rotated. ⚠️ Active TODOs (~31 KB, ~48 entries) and the RD trailing ledger (~5.5 KB) are ungoverned **by count**, so rotation inside the windows **cannot** reach the soft target — capping either **authors a rule (R6)**. ⚠️ ~20 **open** rows are still over R2's ~600-char pointer cap (s261 shortened the ticked ones only). ✅ **The trailing-ledger half is RULED (Cray, typed s267):** both ledgers hold the current window only, ~900 B per entry — applied at the s267 reconcile, which pruned the RD ledger for the first time ever. The **Active-TODOs COUNT** half is still unruled. **Read:** `docs/runbooks/memory-architecture.md` §R2.
- [ ] **🆕 ADR-0035 — L1 re-read a SECOND time, and OQ-7 ruled, both Cray-typed s242.** L1 becomes *"one gate at the edge; app code may READ the verdict, never gate itself"*, unblocking phase-2 identity **capture** while **validation** stays pilot-era. **OQ-7 = (b)**: absent edge identity → proceed and **stamp the absence**. ⚠️ Two costs Cray accepted: runs stay unattributed until someone reads the stamps and **nothing alerts on it**; the stamp shape is PLAN-0112's to specify, not the ADR's. **Read the ADR:** `docs/adr/0035-hosting-and-exposure-model.md`.
- [ ] **🆕 The three live items the rotated s240 block carried — carried here so the rotation ledger's claim is true, not merely stated.** Measured at s240, none resolved since: (i) the **font-size decision still gates re-measuring every geometry number in the beat-4 mockup**; (ii) the **run-list backlog badge on the host is still unmeasured** — a host-state read, so it needs its own typed §8 go; (iii) the **three Advisory-proposal candidates are still unnamed**, so the gate panel still reads as unfinished. The full s240 narrative is at `docs/status-archive/2026-h1d-current-focus.md`.
- [ ] **The Tier-0 auto-memory store is a git repo that DRIFTS — REHOMED s247 to the runbook's Tier-0 section, which is where a reader about to run a consolidation actually looks.** Snapshotted s242 (164 tracked, tree clean). ⚠️ **A snapshot guards against a wrong deletion, NOT against disk loss — there is still no remote.** 🔴 **The `MEMORY.md` consolidation is PARKED (Cray, s257):** all **116** memories citing no repo home were audited and **ZERO** were unconditionally safe to delete, and **no hook anywhere enforces the < 140 target** (`.claude/hooks/**/*.py`, both `settings.json`, `~/.claude/hooks/` all checked). **Do not re-run the audit.** **Read the runbook, never a restatement:** `docs/runbooks/memory-architecture.md` §Tier 0.
- [ ] **🆕 PLAN-0110 SD-E is REVERSED (Cray, typed, s242); its commissioned follow-on PLAN-0112 is COMPLETE and ARCHIVED s246.** The original ruling stands as history and is **NOT** edited. ⚠️ **Two consequences no AC owns:** `/runs` filtering is client-side only *because* the population was pinned at two, and the Monitor "all" filter has no cap — SD-6(b)'s bounded default covers Tab H, a **different surface**. **Read the archived PLAN:** `docs/plans/done/0110-fleet-demo-run-markers-filter-and-deploy-reset.md` (§SD-E · §Out of Scope).
- [ ] **🆕 The four s235 audit findings ADR-0038 did NOT absorb — REHOMED s235 to `docs/logs/2026-08-17-s235-audit-findings-outside-adr-0038.md`.** 🔴 **One live obligation: ADR-0038's three-strike counter has NO OWNER** — and the count has DRIFTED, the s235 log naming **three** items at two firings while ADR-0038's own D4 names **two**. PLAN-0108 is the natural owner and does not claim it. ⚠️ The genuinely-unruled item is the **D2.1 authorship fork**, not "ADR-0037 SD-1", which does not exist. **Read the log.**
- [ ] **🆕 PLAN-0111 — the fleet close-out record that can hold a credit note (ใบลดหนี้): `Draft`, all six SDs RULED** (Cray, typed 2026-08-19, [#1227](https://github.com/CrayJThiemsert/vero-lite/pull/1227)). **Cray ratified the SDs, not the PLAN; nothing gates execution.** 🔴 **SD-E forces SD-A to (b), a separate `repair_case_credit_note` table.** ⚠️ **AV-1 is owed before Step 4, not before merge** — SD-C is provisional on it. **Read the PLAN:** `docs/plans/0111-fleet-closeout-credit-note-record.md`.
- [ ] **🆕 `tools/check_ac_consistency.py` has a measured blind spot — the AC-ledger guard did not see PLAN-0107's own drift.** Four of that PLAN's criteria sat unticked while this file asserted its Phase C had shipped, and the guard still exited **0**. Reading its source: it scans for criterion references **backwards** from each closure keyword, with the lookback stopping at the previous one — so a row that writes the keyword *first* and its criterion references *after* falls outside the window entirely, while a sibling phrasing on the same line that puts them *before* is detected normally. 🔴 **NOT fixed, and the mechanism is read from source, NOT probed.** ⚠️ Widening the matcher needs a prototype pass first, for two measured reasons: the guard's own docstring records deliberate non-claims a wider matcher would begin catching, **and this very row had to be rephrased to stop the guard reading its description of the bug as a closure claim** — the s257 `fail_under` lesson exactly (prose containing the token breaks the read; rewrite the prose, never the criterion).
- [ ] **🆕 PLAN-0107's citation population is only PARTIALLY verified — recorded here because nothing else carries it.** The s241 sweep was exhaustive for `verticals/fleet_maintenance/operate_seed.py` **only**; the drafter said it had not checked the rest, and named the at-risk set: AC-8's cites into `tests/api/conftest.py`, the Phase A cites into `.github/workflows/ci.yml`, and a tail into files no closed AC touched. 🔴 **Most are BEFORE-STATE cites — historical by design** — so the treatment is likely **labelling, not re-anchoring**, making it PLAN-0108's question. **NOT ruled.**
- [ ] **🆕 PLAN-0108 — AC-authoring + pre-close convention hardening: `Draft`, UNRATIFIED.** The weak-oracle half of the s235 audit. 🔴 **Still gated: SD-1 is NOT ruled — ROUTED to Cowork** (until ratified, §8 as written governs); three of six ACs close only on Cray's PR-merge read; Step 1 is G2-gated for Code. ⚠️ **UNDECIDED, live only here: the AC labels read `[1, 5, 2, 3, 4, 6]` — unique but NOT ascending.** Ordering them means moving a block against a live citation — **Cray's call**. Owns ADR-0038's **OQ-5**. **Read:** `docs/plans/0108-ac-authoring-and-preclose-convention-hardening.md`.
- [ ] **🆕 The two s241 pre-commit guards are FLOORS, NOT CEILINGS.** `tools/check_retired_claims.py` (hook #18; convention `docs/conventions/retired-claims.md`) cannot catch a **reworded** stale copy and cannot know a claim *should* have been retired — declaring stays a human act. `tools/check_ac_consistency.py` (hook #19) cannot read a **phase-level** claim (*"Phase A CLOSED 6/6"* names no AC — three exist), and covers **active** PLANs only. ⚠️ `docs/plans/done/0042-at2-managerial-build.md` carries a duplicate `AC-13`, **deliberately out of scope** as frozen history.
- [ ] **🆕 PLAN-0109 (Ask over repair cases) carries FOUR factual defects in its RULED content — (i)–(iii) measured s241, (iv) measured s260; zero tracked hits before this reconcile. Fix all four BEFORE Step 5; `docs/plans/` writes, so G2-gated, owed to a drafter dispatch.** 🔴 **(i) AC-11 would write a FALSE sentence by deleting a TRUE one** — case text reaches the **phrase prompt only**, so its grep pass read **cannot fail**: it is satisfied by deleting a truth. 🔴 **(ii) `tenant_id` is missing from the exclusion enumeration and reddens AC-3 on the first run.** **(iii)** AC-3(iii) contradicts AC-10 on `seq`. 🔴 **(iv) MEASURED s260 — AC-11's pass read is HALF-VACUOUS, and the PLAN's own non-vacuity note is wrong about it.** Running the AC's verbatim command at baseline returns **one** hit, not the *"occurrences in **both** artifacts"* the PLAN asserts: the ROPA contributes one, and `services/db/repair_case_retention.py` contributes **zero** — its docstring **line-wraps** the phrase (`does not reach case` / `text`), so an exact-phrase grep cannot see it. A wrap-tolerant control finds the sentence in **both** files, so it really is there; the AC simply cannot observe the module's copy, and that half of the pass read is satisfied by changing nothing. ⚠️ **The 45-degree fix is the wrong one** — widening the grep would make the AC pass on the ROPA edit alone; the phrase in the module has to become greppable, or the AC needs a per-artifact read. **Read:** `docs/plans/0109-*.md`.
- [ ] **TWO unruled silent drops in the NL engine's aggregate paths — REHOMED s235 to the code.** (i) the **`started_week` filter is ignored entirely**; (ii) **`group_by` never reaches `AggregateResult`**, so *"average duration per procedure"* validates, executes and silently returns **one ungrouped number**. ⚠️ **The count path DOES pass `groups`** — a two-site gap, not a missing feature. **No test covers either.** **Read the docstring:** `services/engine/run_query.py::_aggregate_duration`. **Two dispositions each, NEITHER ruled: (a) refuse, or (b) make it work.**
- [ ] **`nl-03`'s `SQL_EXPECT` is UNDER-SPECIFIED — RULED (Cray, typed, s226): RECORD it, do NOT change the token. REHOMED s235 to the module that defines it.** 🔴 **A different defect class from the nl-02/nl-05 tokens Step 1 repaired:** `score_sql` matches a SUBSET, so the oracle is **WEAKER than it should be, not WRONG** — adding the token would make the benchmark stricter and **break comparability with earlier runs**. A measurement decision, not a typo fix. **Read the note:** `benchmarks/nl_query_feasibility/text_to_sql.py`.
- [ ] **The apex domain leaks in ONE archived file — UNRULED, not urgent; REHOMED s235 to the guard that would have to widen.** 🔴 **RE-PRICED s232 — "widen the guard" is NOT a one-file flip:** widening the scan to `docs/plans/` reddens **FOUR** files, so the option is a flip **plus three deliberate allowlist additions**. The guard is `tests/deploy/test_published_compose.py::test_no_unknown_domain_appears_in_the_deploy_docs`. **Read its docstring. Reference the carrier BY PATH only — the domain is not named.**
- [ ] **The ฿ realized-vs-projected join — REHOMED s235 to `services/db/run_analytics.py::benefit_rollup`,** which is the primitive the circulating framing wrongly claimed could be reused. 🔴 **It cannot** — it yields no per-run figure at all, so the join needs a NEW per-run aggregation; copy `run_duration_totals`. ✅ **No migration needed.** ⚠️ Re-priced **~150–250 lines across 6–7 files, ONE PR** — the *"~40 lines"* figure was checked and is WRONG. Three TEST-PINNED constraints live in that docstring. **Read it, never a restatement.** Lands on Tab J, which fleet publishes.
- [ ] **Demo-key rotation cadence — CRAY'S, posture not code.** Fleet's README documents how to **generate** a persona key pair but says nothing about **when to rotate**. Measured s225: `git grep -i -e rotate -e rotation` under `deploy/published/oct-fleet-maintenance/` returns **zero** matches. The keys are served to the browser by ruling, so they are **public the moment fleet is reachable** — which makes the cadence a real posture question rather than a nicety. No code change is implied; the answer is Cray's.
- [ ] **ADR-0036 OQ-2 — the aggregate in-flight LLM posture — remains OPEN.** ✅ PLAN-0103 Step 9's MS-S1 headroom is MEASURED s221 (`docs/logs/2026-08-10-oct-energy-migration-phase2-and-step9-headroom.md`): RAM and CPU do not constrain a second or third published system. ⚠️ **OQ-2 does NOT follow from it** — the constraint on a second *assisted* system is the resident model and concurrent in-flight calls, not container footprint, and one term (Postgres idle) is declared unmeasured rather than folded silently into the total. **Read the ADR's own OQ-2.**
- [ ] **Three measured, unscheduled items — REHOMED s235 to `docs/logs/2026-08-17-s235-unscheduled-measured-items.md`.** (1) **The public one-pager v2** — DESIGN-READY, a WRITE job; destination RULED (Cray, typed, s226) = gitignored `docs/strategy/private/`. (2) **The assembly-cost axis** — 🔴 the banked series is spiky, not falling, and **its METHOD is recorded nowhere**, so a tripwire built today emits an incomparable number. (3) **Seam-scoped mutation-testing CI** — no `scenario` marker and CI runs bare `pytest -q`, so §8's scenario rule is **mechanically unenforced**. **Read the log.**
- [ ] **Landing-layer PLAN — CLOSED s226 as SUPERSEDED. NOT work to do; this row exists so nobody schedules it again.** PLAN-0103 Step 8 consumed the repo-side half (AC-9 ticked), and ADR-0036 D1/D2 place the landing surface, ingress map and Access policies **outside this repo** — a vero-lite file enumerating published systems is guard-rejected as a *shadow ingress map* (`tests/deploy/test_published_profiles.py`). Cray ruled s221 (typed): **no portal repo.** 🔴 **The remainder is CRAY'S DASHBOARD WORK — nothing for Code, no dispatch owed.**
- [ ] **PLAN-0100's residuals outlive the PLAN** (COMPLETE 13/13, ARCHIVED s216; the demo is LIVE, REDEPLOYABLE and DRIVEN). ✅ **REHOMED s235 under the R2 carve-out** — all three residuals (D-4 discharged by PLAN-0104 · no cache-purge step and no versioned font URLs · no `OLLAMA_KEEP_ALIVE` pin, so all three profiles inherit the 30m code default) now live in the PLAN's own **§Post-archival amendment**, each re-verified at source. **Read it:** `docs/plans/done/0100-exposure-published-demo-surface.md`.
- [ ] **CI has NO JS RUNTIME — s234 measured the cost; NARROWED s235, NOT closed.** Tab I clipped **305px** of itself on the **live** system while **4,113 tests were green**; a human found it. **No oracle here can see a clip.** ⚠️ **PLAN-0107 AC-1 adds `node --check`, a SYNTAX gate — a clip is a LAYOUT fact**, so it narrows this row and does not close it. 🔴 **The guard shipped with the fix says so in its own docstring:** it reads the stylesheet, so it catches a deletion and **cannot catch a re-clip by other means**. Closing it is a JS-runtime-in-CI project; nothing drafted.
- [ ] **PLAN-0096 residuals — ANSWERED s189; nothing blocking remains.** **Open, NON-blocking:** cost-center (ศูนย์ต้นทุน) granularity — per truck or per company? Ship the column, fill the rule when it lands. **RR-1** per-฿ approver→case attribution is INFERENCE, not data (wrong the day two approvers share a gate resolution). **`latest_per`** still collapses two open cases on one truck (**Cray typed (ค) defer** — the older reports as *ungoverned*). (A5 **parked**.) _[RR-1 + `latest_per` carried here s250 from In-Flight; detail in `docs/plans/done/0096-fleet-flow-completion-phase1.md`.]_
- [ ] **The AT-2 extraction — only the F-FACTORY half remains, owned by PLAN-0076 T1.** The criterion-vocabulary half SHIPPED as PLAN-0087 (ARCHIVED, #840/#841); SD-1 = (a) keeps the procedure-aware `ExecutorFactory` half with PLAN-0076 T1, guard `test_at2_extraction_obligation_is_owned` ARMED. Full detail: `docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` + `docs/plans/0076-*.md` §A.
- [ ] **PLAN-0075 follow-ons — homed by PLAN-0076 (`Status: Tracking`, #752).** T1's criterion-vocabulary half shipped as PLAN-0087; the procedure-aware-`ExecutorFactory` half (F-FACTORY) stays OPEN, and **F-PIN stays OPEN** — so PLAN-0076 does **not** archive and its AC-6 presence guard stays ARMED. ⚠️ Its six ACs and four Steps are **stub-level — none directs a build**, so nothing here is Code-executable. **Read the PLAN:** `docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` §A.
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2), open ONLY for the O-2 residue.** Every other leg is DONE and archived. The residue: procurement's `intake` migrated only PARTIALLY — the derived fields already moved to declared `transform`, leaving **only the cardinality-changing `candidate_quotes` nest**, explicitly Out-of-Scope there. **Read the archived PLANs:** `docs/plans/done/0062-per-vertical-seed-migration.md` §SD-C (the co-exist decision + its STOP-and-surface tripwire) · `done/0078-*.md` §L-3.
- [ ] **Bounded/incremental chain verification (PLAN-0063 SD-4 follow-up, s118).** `GET /audit/verify` walks the WHOLE chain O(n) on demand — accepted at pilot scale. Future work = a checkpointed head / verify-since-anchor design; anchor storage ≈ external anchoring — **do not build without re-reading the tripwire** in `docs/plans/done/0063-audit-chain-verification-surface.md` + the `services/api/routers/audit.py` module docstring (SD-4). *(#688/#690)*
- [ ] **Rock 4 — s84 deep research DELIVERED → O-sequence locked.** Cray locked **O-1 → O-3 → O-2 → O-4**. **O-1** (Box-4 ฿ pitch) **DONE** · **O-3 = ADR-0025 Accepted** · **O-4 = PARK** (agent-interop; `docs/adr/0032-*.md` D4 — option-only, un-park = a counterparty's *written* pull). **Remaining: O-2 only** (economic-impact facet + Q3 data-binding = Rock 3). Full detail: `docs/adr/0025-at2-managerial-layer.md` (O-sequence + Box-3 fit + the **evidence-asymmetry** finding rehomed s142). *(s84 Cray ask)*
- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten. **Full table (all six rows + their triggers + where each lands): `docs/plans/done/0005-oct-engine-runtime-layer.md` §8.1** — which itself instructs this STATUS entry to be a pointer. *(per Cray note 2026-05-21)*
- [ ] **PLAN-004 Phase C — OPTIONAL POLISH (forward-declared; "may never land"):** HTML/markdown handoff dashboard under `docs/` + references-graph (mermaid dispatch chains) + `render_transcript.py` unified session export (PLAN-0004 §"Phase C"). *(Phase A + B both COMPLETE — session 35; the prior TODO's validator **warning-swallow bug was FIXED #312**, s58.)* _[s226: the three never-formally-scoped sub-ideas are ROTATED to `docs/status-archive/2026-h1-status.md` — fold them in only if Phase C ever lands.]_
- [ ] **Custom Postgres image with extensions (pgvector / AGE / pg_trgm) — MEASURED DORMANT s226. Recommendation: NO ACTION.** Grepping `services/` returns **one hit, a false positive** — the word "embedding" in a comment. **Nothing needs these extensions**, and the documented trigger points **opposite** to where the work went: NL query took the **relational-aggregation** route. ⚠️ **The price has RISEN:** ADR-0037 grants fleet its **own** Postgres, so swapping the base image now touches **three published profiles and their 68-test guard suite**. Needs a fresh ADR + PLAN, neither drafted.
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] **CLAUDE.md follow-up extraction pass (s181 option b): Cowork dispatch, target < 20 KB. PARKED s183 by Cray — the dispatch stays UNSENT until two things settle.** (1) **The unit of `< 20 KB` is load-bearing and unpinned** (KiB vs decimal); Cray declined to rule. (2) **The named candidates cannot reach either target** — the cut needed was ~1,944–2,424 B where the five candidates measure ~930–1,000 B combined, and the large blocks are **not on the list**. 🔴 **The real parked decision: target and constitution pull opposite ways** — the growth is ratified binding-rule substance, not padding.
- [ ] **PLAN-0102's two residues outlive the PLAN** (retire L1 loop-detect — COMPLETE 11/11, ARCHIVED s217; L1 gone from all four hooks, L2/L3/L4 intact and asserted so). ✅ **REHOMED s235 under the R2 carve-out** — the **callerless `observe()`** (kept deliberately; deleting it pulls a refactor into every surviving increment) and the **forwards-call-graph method debt** (`ruff` flags a dead import, never a dead private function) now live in the PLAN's own **§Post-archival amendment**. **Read it:** `docs/plans/done/0102-retire-l1-loop-detect.md`.
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)

## Next Steps

> **Immediate next action is the MACHINE HALF of the selection criterion — now PLAN-0118 Step 3** (the gate existence test ran s268, verdict DO-NOT-WIRE; that completed row rotated to the archive at the s268 reconcile, its substance homed at `benchmarks/model_compare/DECISION.md` §5a-RESULT) — see the **first two Active TODOs** above: the live next action, and the three s268 findings that must be rehomed as Step 3 starts. The items below are the long-horizon register and none of them gates it.

1. **PLAN-0005 §8.1 revisit register** — remaining deferred-foundational simplifications at their batch boundaries (audit framework, mapping layer, ORM emitter, base-Postgres → the custom-Postgres image, registry discovery). _[Corrected s153: dropped the stale "→ ADR-011+" and "→ PLAN-002 (≥ADR-014)" pointers — **ADR-011 does not exist** (earmark only, per the Active TODO above) and **PLAN-002 was never drafted** with its ADR floor moot; each item's corrected status lives in Active TODOs.]_
2. **Partner-trial readiness gaps** — `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` awaits a dedicated Cray discussion.
3. **Deferred (backlog)** — PLAN-004 Phase C only (optional polish: handoff dashboard / references-graph / unified export — Phase B complete s35, warning-swallow fixed #312); the custom Postgres image (needs a fresh ADR number + a PLAN — neither drafted; see the Active TODO for the corrected framing).
4. **Ongoing** — Continue exercising the file-based handoff mechanism (Chat ↔ Code ↔ Cowork) across batches.

## Update Workflow

**Rehomed 2026-07-24 (session-171).** The update mechanism and the Q4
`head_commit` semantics are *procedure*, not *state*, so they now live in
[`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md)
section "STATUS.md Update Workflow" (ADR-0017 D5 knowledge placement). Moved
verbatim; nothing was rewritten.
