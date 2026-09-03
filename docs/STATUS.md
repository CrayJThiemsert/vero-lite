---
last_updated: 2026-09-04T00:05:00+07:00
session: 275
current_batch: "s274–s275 — NINE PRs (#1371–#1379): PLAN-0117 CLOSED 16/16 after eight AC repairs; the goal gate fabricated nine failures a THIRD time; ADR-0018 D8 + four harness defects fixed; PLAN-0119/0120 drafted."
current_actor: code
blocked_on: "NOTHING. PLAN-0120's six SDs are all RULED (a) and ADR-0018 D8 is merged, so the §8 ADR-before-implementation gate is clear."
next_action: "PLAN-0120 Step 0 — the MEASUREMENT pass (junit shape of a fixture-level pytest.exit; does wsl.exe propagate exit 75; +3 unknowns). Several AC pass reads depend on it — do NOT start Step 1 first."
head_commit: dfe7fca
recent_commits: [dfe7fca, 0e58be9, 3ce2006, 20024d6, 15d3a34, c373227, 549b363, 7d308ef, 4446e4b, a674f95]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 274–275, 2026-09-03 (`8ac17f5` → `dfe7fca`) — NINE PRs merged
> ([#1371](https://github.com/CrayJThiemsert/vero-lite/pull/1371)–[#1379](https://github.com/CrayJThiemsert/vero-lite/pull/1379)),
> 0 open, tree clean, MS-S1 never contacted. What it established: every rule
> that would have prevented Code's five errors already existed — so the fix is
> not more prose, it is a separate reader.**
>
> ✅ **PLAN-0117 is CLOSED — but eight AC definitions (C1–C8) had to be
> repaired FIRST.** s274 audited the *proposed* closeout with four specialists
> and found its premise wrong: the work shipped at s265-266 and only the
> checkboxes were unticked, while several ACs were **structurally incapable of
> failing**. Cray ruled a full re-witness; s275 then **observed** all three
> predictions — AC-3(a) read `GREEN` *because* no synonym-carrying property has
> a sole carrier, AC-4's dormant probe `MISFIRE`d (pytest stops at the first
> failed assert), AC-7's positive control was itself vacuous. Final
> `PROBE-BATTERY: PASS` — `claims: 86 · witnessed RED: 15 · exempted: 71 ·
> GAPS: 0`, plus AC-1(a) by hand (a pre-commit hook, so no `Claim` in the 86) =
> **16 of 16**, Cray having widened his own typed count 15→16 via SD-8.
>
> 🔴 **The goal gate fabricated nine test failures — for the THIRD time (s228,
> s253, s275).** Its `check` criteria run at every Stop; a `pytest` criterion
> bound the same per-checkout test DB as a running suite, `DROP SCHEMA public
> CASCADE` deadlocked, and the run reported **4 failed / 5 errors**
> indistinguishable from real defects. A serialized re-run of the
> byte-identical command: **4801 passed, 0 failed**.
>
> 🔴 **Four latent defects fell out of that analysis, none of them what it was
> sent to find** (#1376): `DEFAULT_CHECK_BUDGET_S` was **600 s inside a 180 s
> Stop hook**, unreachable for months and starving the classifier if ever
> spent; **8 of 8** pre-commit hooks used a bare `uv run`, which uninstalls
> pytest/ruff/mypy from the shared `.venv` mid-commit (CI and one skill defend
> against this **by name**; pre-commit, which fires most often, did not); three
> write guards documented a route measured dead at s272; and the goal schema's
> own canonical example was `{"cmd": "pytest -q", "timeout_s": 300}` — the
> authoring surface modelling the exact hazard. Two new guard tests, both
> witnessed RED (`claims: 7 · witnessed RED: 5 · exempted: 2 · GAPS: 0`).
>
> ✅ **ADR-0018 gains D8, the resource-binding contract** (#1377). D1's
> *"Cheap, fast, **un-arguable**"* is corrected `was an error`: an exit code is
> un-arguable only about the process that returned it, **not** about whether
> that process held the resource alone. D8 explicitly **rejects** *"a check
> must be side-effect-free"* as self-banning. Root cause: a **CLAUDE.md §4
> violation** — Cray ruled this constraint, typed, 2026-07-29, homed in a
> **test docstring** (`test_migration_orm_lockstep.py:17-23`), binding nobody.
>
> ✅ **PLAN-0119** (five-class local-model serving policy) drafted, all nine
> SDs RULED + three factual defects corrected; **PLAN-0120** (goal-gate test-DB
> isolation, 11 ACs) drafted, all six SDs RULED **(a)**. Its bar is the
> **opposite** of PLAN-0117's: an advisory lock dies with its holder, so a lost
> guard reports exactly what a working guard reports on a clean run.
>
> **The finding that produced the rest:** *why did Code self-catch none of its
> five errors?* **Every preventing rule already existed** — #3 and #4 violated
> `CLAUDE.md:189` **in the same sentence**, #2 recurred PLAN-0117's own C5, the
> DB hazard sat in a Tier-0 memory the gate cannot read. Review layer caught
> Code **9× (6 `plan-drafter`, 2 `goal-evaluator`, 1 specialist); Code 0.**

> **Session 269–273, 2026-09-02/03 (`a0b743b` → `8ac17f5`) — TWELVE PRs merged
> ([#1357](https://github.com/CrayJThiemsert/vero-lite/pull/1357)–[#1370](https://github.com/CrayJThiemsert/vero-lite/pull/1370)),
> 0 open, MS-S1 never contacted. What it established: a guard that is never
> invoked reports nothing, and a benchmark's own criterion can be the false
> negative.**
>
> 🔴 **The three subagent write guards had been inert since birth.** #1362:
> their frontmatter `hooks:` had been FLAT since s269 — 2.1.247 discarded the
> block at DEBUG and loaded the agents **UNGUARDED**, 2.1.255 refuses them
> fail-closed. The nested rewrite restored **registration** (3/3 spawn, offline
> oracle on the real binary with a flat control refused in the same run) but
> **not the guard** — the §8 scenario went RED. #1363 found why: frontmatter
> hooks **never run in this harness** (instrumented guard, **0 invocations**,
> while `goal-evaluator`'s legitimate `goal.json` write succeeded), so they
> moved to `settings.json` behind `pretooluse_subagent_write_dispatch.py`,
> routing by `agent_type` to the three **unchanged** scripts, fail-closed where
> identity is known. ✅ **s273 witnessed it LIVE:** a fresh `/goal` write passed
> un-denied; a Fable `goal-evaluator` asked for a forbidden Write got ONE call,
> denied with the guard's own `SD-1 narrowed Write` reason verbatim, the file
> absent after. **Live from #1363**; `agent_type` is the frontmatter `name`.
> Lesson **#0057** carries the arc; #1366 marks it `was an error` on ADR-0018
> SD-1 / PLAN-0009 H2 / PLAN-0034 prong 2 (plan-drafter drafted = the third
> routed agent witnessed; Cray ruled SD-1 covered by the s249 `done/` form,
> SD-2 no marker on ADR-013 D2 — G5 is settings-level and always held).
>
> ✅ **PLAN-0118 Steps 1–6 done, AC-1–AC-5 CLOSED; only AC-6 is open**, and it
> needs a NEW typed §8 go. #1357 shipped the scorer + gold controls (37 tests)
> with 🔴 **AC-1(d) CORRECTED** from same-*magnitude* (`thr/3..thr*3`, a measured
> FALSE NEGATIVE excluding `rm-02`'s 0.6 kPa reading) to **same-unit**, each case
> declaring `same_unit_distractors` checked against its description. #1360
> shipped the runner (recording pass-through over the real `OllamaClient`,
> transport error distinct from validation exhaustion, SD-5) plus the binding §8
> scenario driving the SHIPPED `extract_package` through its designed seam into
> the real scorer. #1359 settled the four s269 items — fl-21/fl-22 from the
> standing principle, Thai corpus = gap ACCEPTED, `biomass_boiler` RATIFIED as
> **SD-6** with per-domain PROVENANCE, §5a's call-site count corrected in place
> (`was an error`). ⚠️ #1364 ticked AC-1/2/5 only after re-verifying on `main` —
> they shipped in #1357 and sat unticked through **three** handoffs.
>
> **Evidence.** Suite **4761 → 4795 passed**, 8 skipped; `mypy services/
> verticals/` clean (201) and `--strict benchmarks/intake_extraction/` by hand;
> bare `ruff check .` clean. Batteries **23 → 31** (22 WITNESSED + 9 GREEN;
> denominator widened 81 → 121, **reported, not gamed**) + s272's **13/13**.
> #1358 widened CLAUDE.md §8's suspect-the-instrument clause past batteries —
> it fired **seven times** in s269 and the artifact was right every time.

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

_[Current-Focus rotation ledger — **CURRENT window only** (R2, Cray s250; the ledger's OWN window plus a ~900 B per-entry cap, Cray s267); earlier entries travel with their blocks into [`2026-h1d-current-focus.md`](status-archive/2026-h1d-current-focus.md). Window = **267, 268, 269-273, 274-275**. **THIS (s267) reconcile rotates the session-261 block** on the **window rule alone** — a fifth entered, the window is four — **not a cap overage**: the caller re-measured each block as its own contiguous `>` run (2,992 / 3,384 / **3,414** / 3,669 B), **all under** the 4,096 B cap; the earlier *7,950 B / 94% over* figure was a measuring bug that ran to the end of the SECTION and swallowed this ledger. 🔴 **The growth was the LEDGERS, not Active TODOs** (caller-measured: CF 6,793 + RD 8,143 B, ~22% of the file; the RD one **never pruned until now**). Per Cray's typed s267 ruling both ledgers now carry the **current window only** at **~900 B per entry**; out-of-window entries were returned **verbatim** for archiving (R4). ⚠️ **No byte delta measured here — no shell; the caller owes `wc -c` + append + verify-by-DELTA.** **THIS (s268) reconcile rotates the session-263 block** on the **window rule alone** — a fifth entered, the window is four — **not a cap overage**: caller-measured, each as its own contiguous `>` run, s267 **3,103** · s265-266 **3,385** · s264 **3,670** · s263 **2,993 B**, all under the 4,096 B cap. 🔴 **Its s263 entry here is NOT re-archived — the pre-write assertion caught it:** both ledgers were archived **whole and PRE-PRUNE** at s267 (R2 permits it), so R4's move duty is discharged; a second copy would duplicate a move-only archive. ⚠️ **STATUS was PARTIALLY updated during s268** (`377b3c0`/`fd0cb42` touched Active TODOs / Next Steps), so this completes the **frontmatter + CF + RD** half. ✅ **Caller-measured:** from **61,774 B**, still under R1; CF archive **+3,586 B**, byte-identical to `git show HEAD:`, present-once and absent-from-STATUS verified separately. **THIS (s269-273) reconcile rotates the session-264 block** on the **window rule alone** — a fifth entered, the window is four — **not a cap overage**: caller-measured, each as its own contiguous `>` run, 3,274 · 3,101 · 3,573 · 3,668 B, all under the 4,096 B cap. 🔴 **Its s264 entry here is NOT re-archived** — both ledgers were archived **whole and PRE-PRUNE** at the s267 reconcile, so R4's move duty for it is discharged and a second copy would duplicate a move-only archive. ✅ **First reconcile ever to NET-SHRINK STATUS:** it opened with **327 B** of headroom under R1, so the new block was written to a **≤ 3,300 B** budget and two completed `[x]` TODO rows rotated alongside it. ✅ **Caller-measured:** **65,209 → 62,092 B**; CF archive **+4,267 B**, byte-identical to `git show HEAD:`, present-once / absent-from-STATUS verified separately. **THIS (s274-275) reconcile rotates the session-265-266 block** on **BOTH** rules — a first: a fifth block entered a four-wide window **and** that block measured **7,775 B, 90% over** the 4,096 B per-block cap (caller-measured; survivors 3,293 · 3,275 · 3,102 B, all under). 🔴 **Its LEDGER entry is NOT re-archived** — both ledgers were archived whole and PRE-PRUNE at s267, so R4's move duty for it is discharged; only the **block** travels, to `2026-h1d-current-focus.md`. ✅ **Second net-shrink reconcile ever:** STATUS opened at **63,480 B** with just **2,056 B** of R1 headroom, so the new block was written to a **≤ 4,096 B** budget against **7,775 B** recovered. ⚠️ **No byte delta measured — the caller owes `wc -c` + append + verify-by-DELTA.**]_


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
| 2026-09-03 | **s275 — FIVE PRs (#1375–#1379): PLAN-0117 CLOSED, but only after eight AC definitions (C1–C8) were repaired — several could not fail by construction. 16 of 16 WITNESSED** (`claims: 86 · RED: 15 · exempted: 71 · GAPS: 0`, + AC-1(a) by hand). 🔴 **The goal gate fabricated nine test failures — the THIRD time (s228/s253/s275):** a `check` `pytest` criterion bound the same per-checkout test DB as a running suite; the serialized re-run of the byte-identical command gave **4801 passed, 0 failed**. ✅ **ADR-0018 D8** (resource-binding contract) + four latent harness defects fixed (#1376). ✅ **PLAN-0120** drafted, six SDs RULED (a). | `dfe7fca` / [#1375](https://github.com/CrayJThiemsert/vero-lite/pull/1375) / [#1377](https://github.com/CrayJThiemsert/vero-lite/pull/1377) / `docs/plans/done/0117-*.md` · `docs/adr/0018-*.md` §D8 |
| 2026-09-03 | **s274 — FOUR PRs (#1371–#1374): PLAN-0119 drafted and all NINE SDs RULED (Cray, typed), with three factual defects corrected.** 🔴 **The *proposed* PLAN-0117 closeout was audited by four specialists and its premise found WRONG** — the work had shipped at s265-266 and only the checkboxes were unticked, while several ACs were structurally incapable of failing. Cray ruled a **full re-witness** rather than a tick. ✅ STATUS hygiene (#1374) homed the `Counterparty` deferral and corrected two Active-TODO rows that were measurably false. | `51591d2` / [#1373](https://github.com/CrayJThiemsert/vero-lite/pull/1373) / [#1374](https://github.com/CrayJThiemsert/vero-lite/pull/1374) / `docs/plans/0119-*.md` |
| 2026-09-03 | **s269–273 — TWELVE PRs (#1357–#1370): PLAN-0118 COMPLETE 6/6 and archived; the empty-body failure is MEASURED as the `num_predict` cap, and it is the CALL PATH, not the model.** 45 of 45 empty attempts carry `done_reason=length` with `eval_count` 1024 across three arms, and both Qwen arms are **worse** than `gpt-oss` (74% / 75% vs 53%). 🔴 **Three of Code's own claims were withdrawn on re-measurement** (#1370) — `eval_count` was never broken, the arithmetic was Code's; the reasoning-ate-the-budget mechanism is unsupported; a second-segment budget is CONTESTED and open. ✅ The three subagent write guards are live and witnessed (#1362/#1363), marked `was an error` (#1366). | `8ac17f5` / [#1369](https://github.com/CrayJThiemsert/vero-lite/pull/1369) / `docs/plans/done/0118-intake-extraction-benchmark.md` · `benchmarks/intake_extraction/RESULTS.md` · Lesson #0057 · ADR-0018 §Amendment |
| 2026-09-01 | **s267 tail + s268 — EIGHT PRs (#1348–#1355): three are one lesson — a claim is only as good as the surface its consumer reads.** 🔴 **The `llm_assist` gate advisory is DO-NOT-WIRE** — the model's whole input is `" ".join(reasons)`, already on the approver's screen, and `detail.narrative` has **one writer, zero readers**; #1349's rubric, ruled that morning, scored a position #1352 cut that night. Offline, **§8 go UNUSED**. ✅ **PLAN-0118 drafted (#1353), five SDs RULED (#1354), Steps 1–2 shipped (#1355)** — 11 intake cases, 8 scored. 🔴 The Step-2 authoring check was **vacuous by construction** (8 of 8 → honest **4 of 8**). | `a0b743b` / [#1352](https://github.com/CrayJThiemsert/vero-lite/pull/1352) / [#1355](https://github.com/CrayJThiemsert/vero-lite/pull/1355) / `benchmarks/model_compare/DECISION.md` §5a-RESULT |
| 2026-09-01 | **s267 — FOUR PRs (#1343–#1346): two published numbers were measuring the apparatus.** 🔴 **A p95 below 20 samples IS the sample maximum** — nearest-rank `ceil(0.95n)` = `n` for `n < 20`, so the n=14 procedure bar and the NL lane published maxima under a percentile's name in **every run ever made**; fixed at the reporting layer (`tail_s`/`tail_label`), 4 call sites, NL half previously untested. 🔴 **`think_off` costs rationale quality** — qwen q4 `fleet`: `full` 7/14 · `think_off` 4/14 · `skip` 5/14, control-gated; `names_amount` still **inverts** the ratified bar, now inside one model. Batteries 11/11 WITNESSED. | `8843000` / [#1344](https://github.com/CrayJThiemsert/vero-lite/pull/1344) / [#1346](https://github.com/CrayJThiemsert/vero-lite/pull/1346) / `benchmarks/model_compare/RESULTS-1.6.md` |
| 2026-08-31 | **s265-266 — TWELVE PRs (#1329-#1340): PLAN-0117 EXECUTED and its experiment MEASURED.** `Vendor` 3 to 12 properties in two ruled bands; all 9 ACs closed, 16 of 16 WITNESSED. The AFTER run on MS-S1 (typed §8 go) shows the unlock **usable** (supplier band gpt-oss 1 of 3, qwen 3 of 3) and **zero harm** — `fl-01`..`fl-10` identical to BEFORE case-for-case on both models despite a +56% prompt. 🔴 The s265 handoff's `fl-03` discriminator claim is **RETIRED by measurement** (`truck_class` gained no synonyms). 🔴 **OPEN:** whether `fl-21` and `fl-22` should score the answer or the query shape. | `docs/plans/done/0117-fleet-ontology-supplier-evaluation-facts.md` · `benchmarks/nl_query_feasibility/RESULTS.md` · [#1335](https://github.com/CrayJThiemsert/vero-lite/pull/1335) · [#1337](https://github.com/CrayJThiemsert/vero-lite/pull/1337) |
| 2026-08-31 | **s264 — THREE more PRs (#1325, #1326, #1327): the axis becomes a shipped lane, and STATUS gets its headroom back.** ✅ **B2** puts the rationale check in `grader.py` as a **fourth lane with a consumer at every step**, `goal` keyword-only + `None`-default so **no goal ⇒ no check ⇒ β/α byte-identical** — the pre-existing 268-test suite passing untouched is that evidence; lane isolation probed in **both** directions. ✅ **STATUS 65,452 → 63,203 B** (headroom 84 → 2,333) via one asserted transaction, archives verified by byte **DELTA**. ✅ Lessons **#0051** (a saturated benchmark may be missing an AXIS, not needing harder data) + **#0052** (a criterion may only demand what the run supplies) authored. | `3cd1609` / [#1326](https://github.com/CrayJThiemsert/vero-lite/pull/1326) / [#1327](https://github.com/CrayJThiemsert/vero-lite/pull/1327) / `benchmarks/procedure_baseline/grader.py` |
| 2026-08-31 | **s264 — TWO PRs (#1323, #1324): the `fleet` ceiling is broken on a FOURTH axis, offline, with zero MS-S1 runs.** Scoring the `rationale` from the six dumps already on disk separates the tied models in **every cell, no overlap** — qwen **4–8/14**, gpt-oss **0–1/14**. 🔴 **The load-bearing result is NEGATIVE:** `names_amount` does not separate them and gpt-oss scores *higher*, so the intuitive "state the amount" rule would rank them backwards. ✅ **Bar RULED (Cray, typed): role-naming alone** — the richer criteria rest on facts the ontology lacks, making a higher bar an **ontology move before a grader move**. ✅ §12's *blocking-prerequisite* claim **RETIRED** (superseded, not an error). | `9cf5549` / [#1323](https://github.com/CrayJThiemsert/vero-lite/pull/1323) / [#1324](https://github.com/CrayJThiemsert/vero-lite/pull/1324) / `benchmarks/model_compare/RESULTS-1.6.md` §13 |
| 2026-08-30 | **s263 — ONE PR (#1321, five commits): stage 2c completed the five-cell matrix, and the matrix then found a defect in OUR OWN procedure.** 🔴 **The `fleet` procedure GOAL told the LLM to check a gate that is evaluated deterministically downstream with no LLM**, withholding its threshold — live on **11 of 14** items, the rule fires on **one**. Rewritten (`0a1061f`, runtime spine), verified on two models: qwen q8 β/α **85.7 → 100%**, consistency **12/14 → 14/14**; gpt-oss identical, its 100% being **compliance-by-omission** (gate named in **1 of 17** items vs **17 of 17**). 🔴 **~60% of the q4 handler gap was COMPRESSION.** 🔴 `fleet` is at **ceiling for both models**. | `43f707a` / [#1321](https://github.com/CrayJThiemsert/vero-lite/pull/1321) / `benchmarks/model_compare/RESULTS-1.6.md` |
| 2026-08-29 | **s261 — FOUR PRs (#1310–#1313): two of three phase-1.6 audit findings CLOSED; the third's model is on the box, unrun.** 🔴 **`think=False` does NOT turn gpt-oss thinking off — MEASURED** (a **3,105-char** trace on a live 1-item run), so 1.6's `gptoss/full` and `gptoss/think_off` were **one request**: the §4 *"p95 anomaly"* is two runs of one config, and the next matrix has **FIVE cells, not six**. 🔴 `num_predict` was unset, so a deadline **discarded every token produced** — bounded now. 🔴 The shell-hygiene advisory fired on **the idiom it prescribes** (30.8% of 950 commands); FP 3→0. | `41c0d4c` / [#1313](https://github.com/CrayJThiemsert/vero-lite/pull/1313) / `benchmarks/model_compare/RESULTS-1.6.md` |

_[Recent-Decisions rotation ledger — **CURRENT window only** (R2; the ledger's own window plus a ~900 B per-entry cap, Cray s267); earlier entries travel with their rows into [`2026-h1-status.md`](status-archive/2026-h1-status.md). Window = **267, 268, 269-273, 274-275**. The oldest row (**s254**) rotated to the same file at THIS (s267) reconcile — one s267 row entered, so one left to hold the table at ten, on the **count rule alone**. Its substance keeps the homes the row itself names — `docs/plans/done/0115-*.md` for PLAN-0115's four SDs, ADR-0018 VX-1 for the struck clause — **read off the row, not re-grepped here**, so `asserted-not-verified`. 🔴 **This is the FIRST reconcile ever to prune THIS ledger:** under Cray's typed s267 ruling it now holds the current window only at ~900 B per entry, and every out-of-window entry — back to the s243 cont. one — was returned **verbatim** for archiving (R4, move-never-drop), never deleted. ⚠️ No byte delta measured — no shell; the caller owes `wc -c` + append + verify-by-DELTA. The oldest row (**s255**) rotated to the same file at THIS (s268) reconcile — one s268 row entered, so one left to hold the table at ten, on the **count rule alone**; caller-measured **651 B**. Its substance keeps the homes the row itself names — `docs/plans/done/0115-*.md` for PLAN-0115, ADR-0018 VX-1 for the Stop-hook `systemMessage` — **read off the row, not re-grepped here**, so `asserted-not-verified`. Also rotated: the **one completed `[x]` TODO row** (the s268 gate-existence verdict, **949 B**), substance homed at `DECISION.md` §5a-RESULT. 🔴 This ledger's **s263 entry is NOT re-archived** — archived whole and PRE-PRUNE at s267, so re-appending would duplicate. ✅ **Caller-measured:** archive **+2,195 B**, both rows byte-identical to `git show HEAD:`, present-once and absent-from-STATUS verified separately. The oldest row (**s257**) rotated to the same file at THIS (s269-273) reconcile — one row entered, so one left to hold the table at ten, on the **count rule alone**; caller-measured **767 B**. Its substance keeps the home the row itself names — `docs/plans/done/0107-*.md` — **read off the row, not re-grepped here**, so `asserted-not-verified`. Also rotated under the R2 completed-row carve-out: **two `[x]` TODO rows** — the three s268 findings (all closed; homed at PLAN-0118 AC-1(d)/SD-6 and `DECISION.md` §5a) and the s270 Thai-prose ruling (homed at `DECISION.md` §5-RULED). ✅ **Caller-measured:** archive **+3,671 B** (767 + 1,190 + 990 B + header), all three byte-identical to `git show HEAD:`, present-once / absent-from-STATUS verified separately. **Follow-up (#1366):** the completed guards TODO row rotated to the base under the carve-out — **637 B**, archive **+1,172 B**, byte-identical, present-once / absent-from-STATUS. **TWO rows rotated to the same file at THIS (s274-275) reconcile** — **s258** and **s259–260** — because **two** entered (one per session) and the table holds ten, on the **count rule alone**; neither is a cap overage. Their substance keeps the homes the rows themselves name — `docs/plans/done/0107-*.md` for PLAN-0107 and `benchmarks/model_compare/RESULTS-1.6.md` for the phase-1.5/1.6 verdicts — **read off the rows, not re-grepped here**, so `asserted-not-verified`. **No `[x]` TODO row rotated: the section holds ZERO completed rows**, so the R2 carve-out had nothing to take. ⚠️ No byte delta measured — no shell; the caller owes `wc -c` + append + verify-by-DELTA.]_

## In-Flight Discussions

- **OPEN QUESTION for Cray — does a skill's registry table *bind*?** (Code's observation, not a ruling.) s210's closing notice asserted the four-work-stream registry table in `.claude/skills/stream-status/SKILL.md` (#1062) is **canonical**, and that a carrier-artifact change must update it **in the same PR**. The table as *reference* is fine; the **same-PR obligation** is the part that would have to live in `CLAUDE.md` or an ADR to bind — §1 places `.claude/skills/` at **Tier 2.6, derived, no independent precedence** (ADR-0017 D6). **Cray's call: promote it, or keep the table advisory.**
- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm — **not yet drafted**, and it needs a fresh ADR number. _[The old "≥ ADR-014" floor recorded here was **moot** — see the Active TODO below, corrected s141: ADRs now run past 0032 and `0014-WITHDRAWN.md` exists. Kept as one pointer rather than two divergent copies.]_
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).

## Active TODOs

- [ ] **🆕 PLAN-0120 (goal-gate test-database isolation) — `Draft`, all six SDs RULED (a) (Cray, typed, s275), 11 ACs, 0 ticked. The next action is Step 0, the MEASUREMENT pass — NOT Step 1.** Several ACs' pass reads are pre-committed only *after* Step 0 measures five unknowns: the junit shape of a fixture-level `pytest.exit`, whether `wsl.exe` propagates exit code 75, and three others. 🔴 **Its acceptance bar is the OPPOSITE of PLAN-0117's** — an advisory lock is released the instant its holder dies, so a **lost guard reports exactly what a working guard reports** on a clean run; the fail-OPEN direction is what must be witnessed. **Read:** `docs/plans/0120-*.md`.
- [ ] **🆕 PLAN-0119 (five-class local-model serving policy: Gate / Structure / Judge / Narrate / Author) — `Draft`, all NINE SDs RULED (Cray, typed, s274) + three factual defects corrected; nothing scheduled.** Its FIRST work is the **offline instrument repair**, before any further live run: the benchmark recorder drops `load_duration` and `prompt_eval_duration` that `CallMetrics` already computes, and there is no flag to set a cap at all. ⚠️ Ruled-but-unscheduled is exactly the drift the PLAN-0116 row below exists to stop. **Read:** `docs/plans/0119-*.md`.
- [ ] **🆕 CRAY'S CALL — core `Counterparty` promotion: DEFERRED by the SD-2 SPLIT (s265); needs its own ADR (formally reopening ADR-0033 D6) + PLAN.** Not rejected — split off PLAN-0117 so a generator-mechanism change never rides a 5-property YAML edit. 🔴 Structural blocker: `_ORM_COMMITTED_DEST` routes namespace→ONE file and `emit_orm` takes one output path (`code_generator.py:900-914,936-938`) — a second core object type needs per-object-type routing first. Bill: 2 committed files + an alembic migration (CI `alembic check` reddens without it) + 3 tooling gaps (pre-commit glob skips `ontology/`; no `vero-lite generate core`; stale runbook `ontology-migration-autogenerate.md:11-13`). ⚠️ The future work must NOT delete fleet's `Vendor` (`test_golden_e2e.py:344`). Shape lean: `core.Counterparty` = `counterparty_id`+`name` only, HAS-A via `ref` — the DSL has NO inheritance. **Read:** PLAN-0117 § Out of Scope (deferred-core record).
- [ ] **PLAN-0118 is COMPLETE 6/6 and ARCHIVED (s273) — this row survives ONLY for the human half.** ⚠️ `was an error` (s274): it previously read *"Only AC-6 remains … needs a NEW typed §8 go"* — AC-6 closed s273 and the PLAN is in `docs/plans/done/`; the s273 reconcile updated the frontmatter and Current Focus but missed this row. 🔴 **Still open:** the human-half 20-pair re-run needs a typed §8 go **and** a timeout fix (qwen p95 sits on the 120 s client timeout); the Thai corpus is an ACCEPTED gap. **Read:** `benchmarks/model_compare/DECISION.md` **§5-RULED** / **§5a-RESULT**.
- [ ] **The s267 ledger ruling IS homed on both prose surfaces; what remains is that NOTHING enforces it mechanically.** ⚠️ `was an error` (s274): this row claimed the ruling was *"written nowhere the enforcers read"* — measured false. Both carry it: `docs/runbooks/memory-architecture.md` §R2 (the ~900 B per-ENTRY cap) and `.claude/agents/status-scribe.md` (both ledgers, current window only, plus a required per-ledger report line). 🔴 **The real, unclosed gap:** **zero deterministic enforcement** — no hook, tool or test parses STATUS *sections*; the six STATUS-adjacent guards measure whole-file bytes or citations only. The runbook records the reason (ledger entries are prose with no uniform delimiter, so a fragile per-entry parse is the worse risk), so compliance rests on the scribe's own reading. **Read:** `docs/runbooks/memory-architecture.md` §R2.
- [ ] **🆕 CRAY'S CALL — the *45% flip rate* in Current Focus is CONTRADICTED, not re-measured.** s262 ran `fleet` × `qwen/full` twice under a 16,384 cap: **20 of 20 items byte-identical** (drafts, rationales, `eval_count`), while latency differed on 17 — two genuine runs. The 45% was measured on `energy` **before `num_predict` existed**, when generation ran to a client timeout and was CUT; a wall-clock cut is not reproducible by construction. **Hypothesis: it measured the harness.** One repeat per cell settles it. **Do not budget repeats on the 45% until then.**
- [ ] **🆕 CRAY'S CALL — the PORTABLE CORE of Lesson #0049 has no cross-project home, and no such surface exists yet.** Measured s262: `~/.claude/skills/` and `~/.claude/CLAUDE.md` **do not exist**, and Tier-0 auto-memory is path-scoped to this repo — so every reusable practice built here is vero-lite-only. Cray's intent (s262): **prepare, do not build** — no second project exists, and §1's Rule of Three says the abstraction waits for something to extract *toward*. **Trigger: the first new project.** **Read:** `docs/lessons/0049-measure-generation-demand-not-the-cap-that-happens-to-work.md` §PORTABLE CORE.
- [ ] **🆕 CRAY'S CALL — the fleet benchmark awards 100% to *"answer `escalate` on every item without reading anything"*.** `canonical_handler` is `escalate` for **all 14** breach items, so β cannot separate comprehension from a constant. ✅ **The CEILING half is solved (s264)** — the rationale axis separates the models (qwen **4–8/14**, gpt-oss **0–1/14**) — but that restores *discrimination*, **not validity**: a model can name a role and still always-`escalate`. Harder items remain the only fix for the exploit itself. **Read:** `benchmarks/model_compare/RESULTS-1.6.md` §13.
- [ ] **🆕 CRAY'S CALL — the phase-2 MODEL DECISION is still unbound, and `fleet` can no longer discriminate.** ✅ **Audit finding 3 (quantisation) is CLOSED s263** — q8 fixed **exactly the five items** q4 missed; ~60% of the handler gap was compression, not the model. 🔴 Both models now score **100/100/14-of-14**, and every cell but 4-bit qwen `full` is **n=1**. 🔴 **A comparability line exists at `0a1061f`:** §8–§10 was measured against the defective goal directive and does **not** compare with anything after it. 🔴 **Every live run needs a NEW typed §8 go.** **Read:** `benchmarks/model_compare/RESULTS-1.6.md` §9–§12.
- [ ] **🆕 CRAY'S CALL — PLAN-0116's THREE SDs are unruled and had no row here until s257.** `docs/plans/0116-deterministic-claim-rollup-tool.md`, `Status: Draft`, 0/8 ACs, 3 Steps, one PR, deterministic-offline. **SD-1 is the heavy one** — the mixed case (∃ vs ∀ reading); it hard-codes forever an interpretation of Cray's own typed four-line rule, and `_rollup.py` cannot be written until it is ruled. SD-2 (measure labelling stability here?) and SD-3 (exit-code contract) are light. ⚠️ **Measured s257, and it is the reason to rule deliberately rather than by default:** the tool ships with **zero wired producers and zero wired consumers** — both are cut by name in its Out of Scope — so on day one its only caller is its own test suite. Until s257 the SDs were carried only by a `blocked_on` line naming #1301 as *open*, and #1301 merged — the drift this row exists to stop.
- [ ] **🆕 CRAY'S CALL — the s256 walk's residue is TWO RUNS, not two cases; leaving them parked is the current lean.** Measured s257 LIVE, read-only, under three typed gos: both cases **ABSENT** (control-backed); `governed_repair_approval@41bb78353e7c4138` is still `waiting_human` at a resolvable `approve` gate, `@d8f5a677b8f73b3b` `completed`. 🔴 `DEMO-RESET.md` is **not** the tool for a visitor-created id; the per-case seam is `delete_case`. ✅ Resolving that gate is **harmless** — proven offline, not by clicking live ([#1304](https://github.com/CrayJThiemsert/vero-lite/pull/1304)). ⚠️ `audit_log` unchanged at 64 rows, so **how the cases went away is measured but unexplained**. **Read:** `docs/logs/2026-08-27-s257-fleet-walk-residue-readonly-probe.md`.
- [ ] **🆕 CRAY'S CALL — `.claude/worktrees/` is 1.8 GB and `git worktree prune` cannot reach most of it.** Measured s256 by set difference, jointly with the parallel session: **19 directories on disk · 7 registered · 6 prunable · 12 UNREGISTERED**. Prune touches **6 of 19**; the other 12 git no longer knows about and only a manual delete removes. Largest: `eloquent-chatelet` 257 MB · `recursing-chatterjee` 163 · `wizardly-hopper` 161 · `youthful-driscoll` 150. **Nothing deleted — 1.8 GB is irreversible and out of scope for Code.** Related: Cray ruled parallel sessions onto separate worktrees this session, so the set will keep growing.
- [ ] **🆕 CRAY'S CALL — a battery skip is indistinguishable from "no active goal" in the trail.** `_goal_gate.py`'s early return fires before any `record_evaluation` for BOTH the battery-lock stand-down and the no-goal case, so `goal.json` stays **byte-identical** — nothing can later establish that the gate ever stood down for a battery. This is the **price PLAN-0115 SD-2's zero-residue ruling pays**, not a defect, but the price was never measured when it was ruled. Changing it needs a new SD, not a trim. **Read:** `docs/logs/2026-08-26-sd-premortem-replay-experiment.md`.
- [ ] **🆕 ADR-016 SB-3 enumerates THREE load-gate refusals; the SHIPPED Step 1 has FOUR.** The fourth — `when_absent` supplied with **no `scope_by`** — was Cray-ratified at the #1275 merge (typed, s251), but SB-3's body still names only the three `scope_by`-present cases; re-checked in the ADR at the s251 reconcile. **Cray's call: amend the ADR, or leave the fourth recorded in the PLAN.** ⚠️ Whoever opens ADR-016 for this should also repair its **two dead pre-archive PLAN pointers** (`0052-*` and, since s252, `0113-*` — both now under `docs/plans/done/`). R8 exempts `docs/adr/` **temporarily and by design**, because G1 blocks Code from editing an Accepted ADR; the exemption's own comment says to remove it in the same change that lands those fixes. **Read:** `docs/adr/0016-governed-procedure-engine.md` §SB-3 · `docs/plans/done/0113-scope-event-fired-run-to-its-firing-case.md`.
- [ ] **🆕 CRAY'S CALL — should R2 cap the Active TODOs *COUNT*, and govern the Recent Decisions trailing ledger? Still unruled, and the pressure is now structural.** 🔴 STATUS entered s263 at **64,584 B against R1's 65,536-byte HARD ceiling — 952 B of headroom**, and is **~15 KB over the 49,152-byte soft target**; the s263 block only fit because s257 rotated. ⚠️ Active TODOs (~31 KB, ~48 entries) and the RD trailing ledger (~5.5 KB) are ungoverned **by count**, so rotation inside the windows **cannot** reach the soft target — capping either **authors a rule (R6)**. ⚠️ ~20 **open** rows are still over R2's ~600-char pointer cap (s261 shortened the ticked ones only). ✅ **The trailing-ledger half is RULED (Cray, typed s267):** both ledgers hold the current window only, ~900 B per entry — applied at the s267 reconcile, which pruned the RD ledger for the first time ever. The **Active-TODOs COUNT** half is still unruled. **Read:** `docs/runbooks/memory-architecture.md` §R2.
- [ ] **🆕 The three live items the rotated s240 block carried — carried here so the rotation ledger's claim is true, not merely stated.** Measured at s240, none resolved since: (i) the **font-size decision still gates re-measuring every geometry number in the beat-4 mockup**; (ii) the **run-list backlog badge on the host is still unmeasured** — a host-state read, so it needs its own typed §8 go; (iii) the **three Advisory-proposal candidates are still unnamed**, so the gate panel still reads as unfinished. The full s240 narrative is at `docs/status-archive/2026-h1d-current-focus.md`.
- [ ] **The Tier-0 auto-memory store is a git repo that DRIFTS — REHOMED s247 to the runbook's Tier-0 section, which is where a reader about to run a consolidation actually looks.** Snapshotted s242 (164 tracked, tree clean). ⚠️ **A snapshot guards against a wrong deletion, NOT against disk loss — there is still no remote.** 🔴 **The `MEMORY.md` consolidation is PARKED (Cray, s257):** all **116** memories citing no repo home were audited and **ZERO** were unconditionally safe to delete, and **no hook anywhere enforces the < 140 target** (`.claude/hooks/**/*.py`, both `settings.json`, `~/.claude/hooks/` all checked). **Do not re-run the audit.** **Read the runbook, never a restatement:** `docs/runbooks/memory-architecture.md` §Tier 0.
- [ ] **🆕 The four s235 audit findings ADR-0038 did NOT absorb — REHOMED s235 to `docs/logs/2026-08-17-s235-audit-findings-outside-adr-0038.md`.** 🔴 **One live obligation: ADR-0038's three-strike counter has NO OWNER** — and the count has DRIFTED, the s235 log naming **three** items at two firings while ADR-0038's own D4 names **two**. PLAN-0108 is the natural owner and does not claim it. ⚠️ The genuinely-unruled item is the **D2.1 authorship fork**, not "ADR-0037 SD-1", which does not exist. **Read the log.**
- [ ] **🆕 PLAN-0111 — the fleet close-out record that can hold a credit note (ใบลดหนี้): `Draft`, all six SDs RULED** (Cray, typed 2026-08-19, [#1227](https://github.com/CrayJThiemsert/vero-lite/pull/1227)). **Cray ratified the SDs, not the PLAN; nothing gates execution.** 🔴 **SD-E forces SD-A to (b), a separate `repair_case_credit_note` table.** ⚠️ **AV-1 is owed before Step 4, not before merge** — SD-C is provisional on it. **Read the PLAN:** `docs/plans/0111-fleet-closeout-credit-note-record.md`.
- [ ] **🆕 `tools/check_ac_consistency.py` has a measured blind spot — the AC-ledger guard did not see PLAN-0107's own drift.** Four of that PLAN's criteria sat unticked while this file asserted its Phase C had shipped, and the guard still exited **0**. Reading its source: it scans for criterion references **backwards** from each closure keyword, with the lookback stopping at the previous one — so a row that writes the keyword *first* and its criterion references *after* falls outside the window entirely, while a sibling phrasing on the same line that puts them *before* is detected normally. 🔴 **NOT fixed, and the mechanism is read from source, NOT probed.** ⚠️ Widening the matcher needs a prototype pass first, for two measured reasons: the guard's own docstring records deliberate non-claims a wider matcher would begin catching, **and this very row had to be rephrased to stop the guard reading its description of the bug as a closure claim** — the s257 `fail_under` lesson exactly (prose containing the token breaks the read; rewrite the prose, never the criterion).
- [ ] **🆕 PLAN-0107's citation population is only PARTIALLY verified — recorded here because nothing else carries it.** The s241 sweep was exhaustive for `verticals/fleet_maintenance/operate_seed.py` **only**; the drafter said it had not checked the rest, and named the at-risk set: AC-8's cites into `tests/api/conftest.py`, the Phase A cites into `.github/workflows/ci.yml`, and a tail into files no closed AC touched. 🔴 **Most are BEFORE-STATE cites — historical by design** — so the treatment is likely **labelling, not re-anchoring**, making it PLAN-0108's question. **NOT ruled.**
- [ ] **🆕 PLAN-0108 — AC-authoring + pre-close convention hardening: `Draft`, UNRATIFIED.** The weak-oracle half of the s235 audit. 🔴 **Still gated: SD-1 is NOT ruled — ROUTED to Cowork** (until ratified, §8 as written governs); three of six ACs close only on Cray's PR-merge read; Step 1 is G2-gated for Code. ⚠️ **UNDECIDED, live only here: the AC labels read `[1, 5, 2, 3, 4, 6]` — unique but NOT ascending.** Ordering them means moving a block against a live citation — **Cray's call**. Owns ADR-0038's **OQ-5**. **Read:** `docs/plans/0108-ac-authoring-and-preclose-convention-hardening.md`.
- [ ] **🆕 PLAN-0109 (Ask over repair cases) carries FOUR factual defects in its RULED content — (i)–(iii) measured s241, (iv) measured s260; zero tracked hits before this reconcile. Fix all four BEFORE Step 5; `docs/plans/` writes, so G2-gated, owed to a drafter dispatch.** 🔴 **(i) AC-11 would write a FALSE sentence by deleting a TRUE one** — case text reaches the **phrase prompt only**, so its grep pass read **cannot fail**: it is satisfied by deleting a truth. 🔴 **(ii) `tenant_id` is missing from the exclusion enumeration and reddens AC-3 on the first run.** **(iii)** AC-3(iii) contradicts AC-10 on `seq`. 🔴 **(iv) MEASURED s260 — AC-11's pass read is HALF-VACUOUS, and the PLAN's own non-vacuity note is wrong about it.** Running the AC's verbatim command at baseline returns **one** hit, not the *"occurrences in **both** artifacts"* the PLAN asserts: the ROPA contributes one, and `services/db/repair_case_retention.py` contributes **zero** — its docstring **line-wraps** the phrase (`does not reach case` / `text`), so an exact-phrase grep cannot see it. A wrap-tolerant control finds the sentence in **both** files, so it really is there; the AC simply cannot observe the module's copy, and that half of the pass read is satisfied by changing nothing. ⚠️ **The 45-degree fix is the wrong one** — widening the grep would make the AC pass on the ROPA edit alone; the phrase in the module has to become greppable, or the AC needs a per-artifact read. **Read:** `docs/plans/0109-*.md`.
- [ ] **TWO unruled silent drops in the NL engine's aggregate paths — REHOMED s235 to the code.** (i) the **`started_week` filter is ignored entirely**; (ii) **`group_by` never reaches `AggregateResult`**, so *"average duration per procedure"* validates, executes and silently returns **one ungrouped number**. ⚠️ **The count path DOES pass `groups`** — a two-site gap, not a missing feature. **No test covers either.** **Read the docstring:** `services/engine/run_query.py::_aggregate_duration`. **Two dispositions each, NEITHER ruled: (a) refuse, or (b) make it work.**
- [ ] **`nl-03`'s `SQL_EXPECT` is UNDER-SPECIFIED — RULED (Cray, typed, s226): RECORD it, do NOT change the token. REHOMED s235 to the module that defines it.** 🔴 **A different defect class from the nl-02/nl-05 tokens Step 1 repaired:** `score_sql` matches a SUBSET, so the oracle is **WEAKER than it should be, not WRONG** — adding the token would make the benchmark stricter and **break comparability with earlier runs**. A measurement decision, not a typo fix. **Read the note:** `benchmarks/nl_query_feasibility/text_to_sql.py`.
- [ ] **The apex domain leaks in ONE archived file — UNRULED, not urgent; REHOMED s235 to the guard that would have to widen.** 🔴 **RE-PRICED s232 — "widen the guard" is NOT a one-file flip:** widening the scan to `docs/plans/` reddens **FOUR** files, so the option is a flip **plus three deliberate allowlist additions**. The guard is `tests/deploy/test_published_compose.py::test_no_unknown_domain_appears_in_the_deploy_docs`. **Read its docstring. Reference the carrier BY PATH only — the domain is not named.**
- [ ] **Demo-key rotation cadence — CRAY'S, posture not code.** Fleet's README documents how to **generate** a persona key pair but says nothing about **when to rotate**. Measured s225: `git grep -i -e rotate -e rotation` under `deploy/published/oct-fleet-maintenance/` returns **zero** matches. The keys are served to the browser by ruling, so they are **public the moment fleet is reachable** — which makes the cadence a real posture question rather than a nicety. No code change is implied; the answer is Cray's.
- [ ] **Three measured, unscheduled items — REHOMED s235 to `docs/logs/2026-08-17-s235-unscheduled-measured-items.md`.** (1) **The public one-pager v2** — DESIGN-READY, a WRITE job; destination RULED (Cray, typed, s226) = gitignored `docs/strategy/private/`. (2) **The assembly-cost axis** — 🔴 the banked series is spiky, not falling, and **its METHOD is recorded nowhere**, so a tripwire built today emits an incomparable number. (3) **Seam-scoped mutation-testing CI** — no `scenario` marker and CI runs bare `pytest -q`, so §8's scenario rule is **mechanically unenforced**. **Read the log.**
- [ ] **Landing-layer PLAN — CLOSED s226 as SUPERSEDED. NOT work to do; this row exists so nobody schedules it again.** PLAN-0103 Step 8 consumed the repo-side half (AC-9 ticked), and ADR-0036 D1/D2 place the landing surface, ingress map and Access policies **outside this repo** — a vero-lite file enumerating published systems is guard-rejected as a *shadow ingress map* (`tests/deploy/test_published_profiles.py`). Cray ruled s221 (typed): **no portal repo.** 🔴 **The remainder is CRAY'S DASHBOARD WORK — nothing for Code, no dispatch owed.**
- [ ] **CI has NO JS RUNTIME — s234 measured the cost; NARROWED s235, NOT closed.** Tab I clipped **305px** of itself on the **live** system while **4,113 tests were green**; a human found it. **No oracle here can see a clip.** ⚠️ **PLAN-0107 AC-1 adds `node --check`, a SYNTAX gate — a clip is a LAYOUT fact**, so it narrows this row and does not close it. 🔴 **The guard shipped with the fix says so in its own docstring:** it reads the stylesheet, so it catches a deletion and **cannot catch a re-clip by other means**. Closing it is a JS-runtime-in-CI project; nothing drafted.
- [ ] **The AT-2 extraction — only the F-FACTORY half remains, owned by PLAN-0076 T1.** The criterion-vocabulary half SHIPPED as PLAN-0087 (ARCHIVED, #840/#841); SD-1 = (a) keeps the procedure-aware `ExecutorFactory` half with PLAN-0076 T1, guard `test_at2_extraction_obligation_is_owned` ARMED. Full detail: `docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` + `docs/plans/0076-*.md` §A.
- [ ] **PLAN-0075 follow-ons — homed by PLAN-0076 (`Status: Tracking`, #752).** T1's criterion-vocabulary half shipped as PLAN-0087; the procedure-aware-`ExecutorFactory` half (F-FACTORY) stays OPEN, and **F-PIN stays OPEN** — so PLAN-0076 does **not** archive and its AC-6 presence guard stays ARMED. ⚠️ Its six ACs and four Steps are **stub-level — none directs a build**, so nothing here is Code-executable. **Read the PLAN:** `docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` §A.
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2), open ONLY for the O-2 residue.** Every other leg is DONE and archived. The residue: procurement's `intake` migrated only PARTIALLY — the derived fields already moved to declared `transform`, leaving **only the cardinality-changing `candidate_quotes` nest**, explicitly Out-of-Scope there. **Read the archived PLANs:** `docs/plans/done/0062-per-vertical-seed-migration.md` §SD-C (the co-exist decision + its STOP-and-surface tripwire) · `done/0078-*.md` §L-3.
- [ ] **Bounded/incremental chain verification (PLAN-0063 SD-4 follow-up, s118).** `GET /audit/verify` walks the WHOLE chain O(n) on demand — accepted at pilot scale. Future work = a checkpointed head / verify-since-anchor design; anchor storage ≈ external anchoring — **do not build without re-reading the tripwire** in `docs/plans/done/0063-audit-chain-verification-surface.md` + the `services/api/routers/audit.py` module docstring (SD-4). *(#688/#690)*
- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten. **Full table (all six rows + their triggers + where each lands): `docs/plans/done/0005-oct-engine-runtime-layer.md` §8.1** — which itself instructs this STATUS entry to be a pointer. *(per Cray note 2026-05-21)*
- [ ] **Custom Postgres image with extensions (pgvector / AGE / pg_trgm) — MEASURED DORMANT s226. Recommendation: NO ACTION.** Grepping `services/` returns **one hit, a false positive** — the word "embedding" in a comment. **Nothing needs these extensions**, and the documented trigger points **opposite** to where the work went: NL query took the **relational-aggregation** route. ⚠️ **The price has RISEN:** ADR-0037 grants fleet its **own** Postgres, so swapping the base image now touches **three published profiles and their 68-test guard suite**. Needs a fresh ADR + PLAN, neither drafted.
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] **CLAUDE.md follow-up extraction pass (s181 option b): Cowork dispatch, target < 20 KB. PARKED s183 by Cray — the dispatch stays UNSENT until two things settle.** (1) **The unit of `< 20 KB` is load-bearing and unpinned** (KiB vs decimal); Cray declined to rule. (2) **The named candidates cannot reach either target** — the cut needed was ~1,944–2,424 B where the five candidates measure ~930–1,000 B combined, and the large blocks are **not on the list**. 🔴 **The real parked decision: target and constitution pull opposite ways** — the growth is ratified binding-rule substance, not padding.
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)

## Next Steps

> **Immediate next action is PLAN-0120 Step 0** — the measurement pass for goal-gate test-database isolation, and **not** Step 1: several of its 11 ACs' pass reads are pre-committed only after Step 0 measures the junit shape of a fixture-level `pytest.exit`, whether `wsl.exe` propagates exit code 75, and three other unknowns. All six SDs are RULED (a) and ADR-0018 D8 is merged, so §8's ADR-before-implementation gate is clear and **nothing blocks it**. PLAN-0119's offline instrument repair is the queued follow-on. Nothing else from s274–s275 is owed. The items below are the long-horizon register and none of them gates it.

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
