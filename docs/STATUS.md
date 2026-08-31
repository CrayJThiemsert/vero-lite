---
last_updated: 2026-08-31T23:30:00+07:00
session: 266
current_batch: "s265-266 — TEN PRs (#1329-#1338): PLAN-0117 executed end to end and its experiment MEASURED on MS-S1; the fleet gold set became an oracle of the system rather than of itself; and a shared-config core.worktree hijack that two handoffs mis-diagnosed was found and fixed."
current_actor: code
blocked_on: "Nothing on work. TWO calls sit with Cray: whether fl-21 and fl-22 should score the answer or the query shape, and the Active-TODO rehome that R1 headroom now depends on."
next_action: "Rehome the Active TODOs — 27,062 B, 43 percent of STATUS across 45 open rows. It is now the BINDING constraint, not a tidy-up: this reconcile landed with 664 B of R1 headroom and there are zero completed rows left to rotate."
head_commit: c16aaae
recent_commits: [c16aaae, 3b0fcf4, fdee563, 01f2881, 11093e8, 0d4b4ff, efe08f7, ef6d908, e3108bb, 46cab29]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 265-266, 2026-08-31 (`da06b17` to `c16aaae`) — TEN PRs merged
> ([#1329](https://github.com/CrayJThiemsert/vero-lite/pull/1329)-[#1338](https://github.com/CrayJThiemsert/vero-lite/pull/1338)),
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
> `gold_fleet.yaml` is now an oracle of the **system**, not of itself: fleet had no
> engine-grading test at all before #1336.

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

> **Session 263, 2026-08-30 (`59019f3` → `43f707a`) — ONE PR merged
> ([#1321](https://github.com/CrayJThiemsert/vero-lite/pull/1321), five
> commits), 0 open, tree clean. Stage 2c completed the five-cell matrix — and
> the matrix then found a defect in OUR OWN procedure, not in a model.**
>
> ✅ **`gpt-oss:20b` scores 100% β / 100% α (canonical 14/0/0/0) / 14-of-14
> consistency**, at **4.84×** (full) and **3.77×** (skip) qwen q4's speed in
> the same mode. ⚠️ The §9 *"4–6×"* claim shipped with it was **wrong, and
> self-corrected in-PR** (`6f862a6`).
>
> 🔴 **~60% of the handler gap was COMPRESSION, not the model** (`7bc4155`,
> §10). `qwen3.8:27b-mtp-q8_0` fixed **exactly the five items** the 4-bit build
> got wrong — α and consistency each **+3 items**, β unchanged.
>
> 🔴 **The real defect was in the procedure GOAL — a runtime-spine change**
> (`0a1061f`, `verticals/fleet_maintenance/procedures.yaml` + §11). The goal
> told the LLM to CHECK the sourcing-hygiene gate and that the gate **blocks
> the spend on failure**, while withholding the threshold (*"authored in the
> typed rule, never in this prose"*) — but that gate is evaluated
> **deterministically downstream, with no LLM**. **11 of 14** breach items
> carry fewer than three quotes, so the invitation was live on nearly every
> graded item; the rule actually fires on **one** (`fleet-006`). ✅ **The gold
> set was audited and CLEARED as the cause BEFORE anything was edited** — it
> varies honestly on `drivable`/`load_aboard`, flat on `quotes_obtained`.
>
> ✅ **Fix verified on two models, one variable each** (`d366be1`, §12). qwen
> q8: β/α **85.7 → 100%**, consistency **12/14 → 14/14**, and the *mechanism*
> moved with it — gate overriding the routing **2 → 0**, naming it downstream
> **0 → 15**. gpt-oss: **every score identical** — under the OLD goal it named
> the gate in **1 of 17** items where qwen named it in **17 of 17**. 🔴 **Its
> 100% was compliance-by-omission, not comprehension.**
>
> 🔴 **`fleet` is a BLOCKER now, not a limit.** Both models sit at
> 100/100/14-of-14, and it obstructed work **twice in one session**: q8's real
> 3-item gain was invisible to β, and gpt-oss could not be the test cell for
> our own fix — no room to improve. Worse, the benchmark awards **100% to
> *"answer `escalate` on every item without reading anything"***:
> `canonical_handler` is `escalate` for all 14 breach items. 🔴 **A
> comparability line exists at `0a1061f`** — §8–§10 was measured against the
> defective directive and does **not** compare with anything after it; only the
> 4-bit qwen `full` cell has ever been repeated.
>
> **Evidence.** Offline gate green **before** the spine change shipped: bare
> `ruff check .` · `mypy --strict services/ verticals/` clean on 201 files ·
> **pytest 4636 passed, 8 skipped** · **no golden test reddened** (fleet is the
> scaffolder golden donor). CI PASS at all five pinned shas.

> **Session 261, 2026-08-28→29 (`7306f17` → `41c0d4c`) — FOUR PRs merged
> ([#1310](https://github.com/CrayJThiemsert/vero-lite/pull/1310)–[#1313](https://github.com/CrayJThiemsert/vero-lite/pull/1313)),
> 0 open, tree clean. Two of three phase-1.6 audit findings CLOSED; the third's
> model is on the box, unrun. One asserted claim became measured, and it
> retroactively rewrites a 1.6 result.**
>
> 🔴 **`think=False` did NOT turn thinking off — MEASURED, not asserted.** A live
> 1-item run returned a **3,105-char reasoning trace** (`aqua-001`, guard fired
> at `harness.py:258`, model verified `gpt-oss:20b` MXFP4 resident). So 1.6's
> `gptoss/full` and `gptoss/think_off` were the **SAME request** — the *"p95
> anomaly"* in `RESULTS-1.6.md` §4 is **two runs of one configuration**, not an
> anomaly. ⚠️ **The next matrix has FIVE cells, not six:** `gptoss/think_off` is
> **inexpressible** (§8) and the guard stops any run attempting it. That is the
> answer, not a failure.
>
> **#1312 — a deadline that discarded everything now leaves something
> gradeable.** `num_predict` was unset, so generation was bounded ONLY by the
> client-side timeout, which **aborts and discards every token produced**. New
> `llm_max_output_tokens` (default 1024) is sent as `num_predict`, so a breach
> leaves a short answer instead of nothing. `think` was `bool | None` while
> reasoning-effort models take `"low"/"medium"/"high"` and **discard a
> boolean** — widened to `bool | str | None` in **5 lines** (`ChatClient` is a
> Protocol, so ~45 duck-typed stubs were untouched). The guard keys on **what the
> model returned**, never a roster of model names.
>
> **#1313 — the instrument fired on the idiom it prescribes.** The shell-hygiene
> advisory searched the whole command for `$`, so a `$?` **outside** the quoted
> arg — which is exact, measured `exit 7`→7, `exit 8`→8 — tripped it: **30.8% of
> 950 sampled commands**, 37.8% of that rule's firings being this false
> positive. Now quote-span aware, exempts `wsl -e`, fails open; **FALSE_POSITIVES
> 3→0, MISSED 4→1** on a fixed corpus. Also `tools/ci/wait_for_ci.py`, a CI wait
> that **cannot report green from silence** (`[]` = NO-RUN 5 · `cancelled` =
> SUPERSEDED 4 · deadline = TIMEOUT 6 · exit 0 only for a conclusion measured at
> the named sha), and `pretooluse_ci_wait_deny.py` denying loop∧sleep∧CI-poll
> (0.74% of commands) on **`Bash` AND `Monitor`**. ⚠️ **The gate only binds a NEW
> session** — hook registrations are snapshotted at session start; verified here
> empirically, a matching command ran **un-denied**.
>
> **Host-state under Cray's go: the quantisation-matched model is on the box and
> NOTHING has been run with it.** `qwen3.8:27b-mtp-q4_K_M` **16 GB** Q4_K_M,
> params **27.3B** — identical params to 1.6's challenger
> `qwen3.8:27b-mtp-q8_0` **27 GB** Q8_0, so **only quantisation differs**;
> incumbent `gpt-oss:20b` is **12 GB** MXFP4. 🔴 **Audit finding 3 is NOT
> closed.** ⚠️ Two handoff-asserted sizes were **wrong when measured** (12 not
> ~14 GB, 27 not ~30); conclusions unaffected. ⚠️ **Nothing measures Thai prose
> quality** — which is what phase 2's LLM tasks are; `DECISION.md` reserves it
> for a blind read **never run**.
>
> **Evidence.** Suite **4607 passed, 8 skipped** (4,561 + 46 = 4,607); probe
> batteries **16/16 WITNESSED** across four runs.

_[Current-Focus rotation ledger — **CURRENT window only** (R2, Cray s250); earlier entries travel with their blocks into [`2026-h1d-current-focus.md`](status-archive/2026-h1d-current-focus.md). Window = **259–260, 261, 263, 264**. **THIS (s260) reconcile rotates the session-255 block** on the **window rule alone, not a cap overage** — measured **1,984 B** against the 4,096 B cap. ✅ **Both directions were checked, never inferred:** the slice was pinned by its first AND last line, checked for neighbour-bleed, checked absent from the target *before* the write, then verified present-in-archive and absent-from-STATUS **separately**, by byte **delta** rather than presence — a presence test passes on a pre-existing copy. Slice **1,984 B** · archive **+3,300 B** · STATUS **−2,644 B** across both rotations at this reconcile (this block and the s249 RD row). Substance keeps tracked homes, re-checked with `git grep`: `docs/plans/done/0115-*.md`, `docs/adr/0038-*.md`, and the stale-`.pyc` hazard in `tools/probe_battery/README.md` plus `_battery.py` / `_snapshot.py`. **THIS (s261) reconcile rotates the session-256 block** on the **window rule alone** — a fifth block entered, the window is four — **not a cap overage**: s260 measured it at **4,055 B**, inside the 4,096 cap. ⚠️ **No byte delta was measured here** — `status-scribe` has no shell; the slice was pinned by its first and last line and returned verbatim, so the **caller owes `wc -c` + append + verify-by-DELTA** (presence passes on a pre-existing copy). Substance is carried by live Active-TODO rows naming `docs/plans/done/0114-*.md` and the three `docs/logs/2026-08-26-*` files — **read off those rows, NOT re-grepped here.** 🔴 **One residue is carried by nothing else and travels into the archive only:** *nowhere records that the battery-lock case was considered for the classifier arm*. **THIS (s263) reconcile rotates the session-257 block** on the **window rule alone** — a fifth entered, the window is four. ✅ **Measured by the caller, not asserted:** slice **3,754 B** (one heading, no neighbour bleed), extracted with `git show` rather than retyped, checked ABSENT from the target *before* the write, then verified by byte **delta** — archive **+3,755 B**, and **+731 B** for the s251 RD row. Substance keeps live rows: PLAN-0107 15/15 (`docs/plans/done/0107-*.md`), the `check_ac_consistency.py` blind spot, the two s241 guards, and the s256-walk residue log. ⚠️ **STATUS skipped s262** — the window is **259–260, 261, 263, 264** and no s262 block is backfilled. **THIS (s264) reconcile rotates the session-258 block** on the **window rule alone** — a fifth entered, the window is four — **not a cap overage**: measured **2,852 B** against the 4,096 cap. ✅ **Pinned, asserted, then measured by DELTA:** first AND last line pinned, neighbour-bleed checked, ledger checked OUT of the slice, checked ABSENT from the target *before* the write, then presence-in-archive and absence-from-STATUS verified **separately**. Also rotated: the s253 RD row and **7 completed `[x]` TODO rows** (s250/255/256/258, all older than the window) — archived per R4 rather than dropped, matching recent practice. Substance keeps tracked homes: `benchmarks/model_compare/RESULTS-1.6.md` §13 and `benchmarks/procedure_baseline/rationale_regrade.py` **THIS (s265-266) reconcile rotates the session-259-260 block** on the **window rule alone** — a fifth block entered and the window is four — **not a cap overage**: measured **3,038 B** against the 4,096 B cap. Pinned, asserted, then measured by DELTA: a 13-assertion battery fixed BEFORE any write pinned the slice by its first AND last line, checked neighbour-bleed in both directions, checked this ledger OUT of the slice, and checked the slice ABSENT from the target before the append; sed then extracted the slice and independently reproduced the same 3,038 B. Archive **+3,438 B** (slice plus its rotation header) and the s254 ADR-0038 RD row **+852 B**, both verified present-in-archive and absent-from-STATUS separately. Headroom is the real finding here: with zero completed `[x]` rows left to rotate (s264 took the last seven), the only lever was writing this block **under** the 4,096 cap. **Active TODOs is 27,062 B, 43% of STATUS across 45 open rows** — and it, not the Current-Focus window, is why R1 headroom keeps vanishing. The s264 next_action already named the rehome; it is still unaddressed and is now the binding constraint on the next reconcile.]_


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
| 2026-08-31 | **s265-266 — TEN PRs (#1329-#1338): PLAN-0117 EXECUTED and its experiment MEASURED.** `Vendor` 3 to 12 properties in two ruled bands; all 8 ACs closed, 14 of 14 WITNESSED. The AFTER run on MS-S1 (typed §8 go) shows the unlock **usable** (supplier band gpt-oss 1 of 3, qwen 3 of 3) and **zero harm** — `fl-01`..`fl-10` identical to BEFORE case-for-case on both models despite a +56% prompt. 🔴 The s265 handoff's `fl-03` discriminator claim is **RETIRED by measurement** (`truck_class` gained no synonyms). 🔴 **OPEN:** whether `fl-21` and `fl-22` should score the answer or the query shape. | `docs/plans/0117-fleet-ontology-supplier-evaluation-facts.md` · `benchmarks/nl_query_feasibility/RESULTS.md` · [#1335](https://github.com/CrayJThiemsert/vero-lite/pull/1335) · [#1337](https://github.com/CrayJThiemsert/vero-lite/pull/1337) |
| 2026-08-31 | **s264 — THREE more PRs (#1325, #1326, #1327): the axis becomes a shipped lane, and STATUS gets its headroom back.** ✅ **B2** puts the rationale check in `grader.py` as a **fourth lane with a consumer at every step**, `goal` keyword-only + `None`-default so **no goal ⇒ no check ⇒ β/α byte-identical** — the pre-existing 268-test suite passing untouched is that evidence; lane isolation probed in **both** directions. ✅ **STATUS 65,452 → 63,203 B** (headroom 84 → 2,333) via one asserted transaction, archives verified by byte **DELTA**. ✅ Lessons **#0051** (a saturated benchmark may be missing an AXIS, not needing harder data) + **#0052** (a criterion may only demand what the run supplies) authored. | `3cd1609` / [#1326](https://github.com/CrayJThiemsert/vero-lite/pull/1326) / [#1327](https://github.com/CrayJThiemsert/vero-lite/pull/1327) / `benchmarks/procedure_baseline/grader.py` |
| 2026-08-31 | **s264 — TWO PRs (#1323, #1324): the `fleet` ceiling is broken on a FOURTH axis, offline, with zero MS-S1 runs.** Scoring the `rationale` from the six dumps already on disk separates the tied models in **every cell, no overlap** — qwen **4–8/14**, gpt-oss **0–1/14**. 🔴 **The load-bearing result is NEGATIVE:** `names_amount` does not separate them and gpt-oss scores *higher*, so the intuitive "state the amount" rule would rank them backwards. ✅ **Bar RULED (Cray, typed): role-naming alone** — the richer criteria rest on facts the ontology lacks, making a higher bar an **ontology move before a grader move**. ✅ §12's *blocking-prerequisite* claim **RETIRED** (superseded, not an error). | `9cf5549` / [#1323](https://github.com/CrayJThiemsert/vero-lite/pull/1323) / [#1324](https://github.com/CrayJThiemsert/vero-lite/pull/1324) / `benchmarks/model_compare/RESULTS-1.6.md` §13 |
| 2026-08-30 | **s263 — ONE PR (#1321, five commits): stage 2c completed the five-cell matrix, and the matrix then found a defect in OUR OWN procedure.** 🔴 **The `fleet` procedure GOAL told the LLM to check a gate that is evaluated deterministically downstream with no LLM**, withholding its threshold — live on **11 of 14** items, the rule fires on **one**. Rewritten (`0a1061f`, runtime spine), verified on two models: qwen q8 β/α **85.7 → 100%**, consistency **12/14 → 14/14**; gpt-oss identical, its 100% being **compliance-by-omission** (gate named in **1 of 17** items vs **17 of 17**). 🔴 **~60% of the q4 handler gap was COMPRESSION.** 🔴 `fleet` is at **ceiling for both models**. | `43f707a` / [#1321](https://github.com/CrayJThiemsert/vero-lite/pull/1321) / `benchmarks/model_compare/RESULTS-1.6.md` |
| 2026-08-29 | **s261 — FOUR PRs (#1310–#1313): two of three phase-1.6 audit findings CLOSED; the third's model is on the box, unrun.** 🔴 **`think=False` does NOT turn gpt-oss thinking off — MEASURED** (a **3,105-char** trace on a live 1-item run), so 1.6's `gptoss/full` and `gptoss/think_off` were **one request**: the §4 *"p95 anomaly"* is two runs of one config, and the next matrix has **FIVE cells, not six**. 🔴 `num_predict` was unset, so a deadline **discarded every token produced** — bounded now. 🔴 The shell-hygiene advisory fired on **the idiom it prescribes** (30.8% of 950 commands); FP 3→0. | `41c0d4c` / [#1313](https://github.com/CrayJThiemsert/vero-lite/pull/1313) / `benchmarks/model_compare/RESULTS-1.6.md` |
| 2026-08-28 | **s259–260 — ONE PR (#1309, five commits): a 7-phase FDE readiness programme is RATIFIED (Cray) and phases 0/1/1.5/1.6 shipped.** 🔴 **Phase 1.5's *keep `gpt-oss:20b`* verdict is SUPERSEDED** — every challenger "error" was a **deadline cut** (counts matching 3/3, 2/2, 0/0), so that count measured the **harness, not the model**. 🔴 **Turning the reasoning pass off improved BOTH models** (gpt-oss β 10→30%, qwen 30→80%), making it a **pipeline** property, not a model one. ⚠️ **No model is bound** — one repeat per cell against a measured **45% flip rate**. | `7306f17` / [#1309](https://github.com/CrayJThiemsert/vero-lite/pull/1309) / `benchmarks/model_compare/RESULTS-1.6.md` |
| 2026-08-27 | **s258 — ONE PR (#1307): PLAN-0107 COMPLETE 15/15 and ARCHIVED; AC-9 closed on Cray's ruled option (b).** 🔴 The golden corpus was **not an oracle** — invariants 1–4 compare each file to itself, so `tools/golden_trace/` plus a new **invariant 5** now score the system's LIVE composition against the recorded envelope (`created_at` the sole exclusion, measured 1 of 16 keys). 🔴 **AC-12/13/14 had landed unticked while STATUS claimed them closed, and `check_ac_consistency.py` reported clean** — it searches `AC-N` backwards from `CLOSED`. **That guard gap is NOT fixed.** | `d78eebe` / [#1307](https://github.com/CrayJThiemsert/vero-lite/pull/1307) / `docs/plans/done/0107-*.md` |
| 2026-08-27 | **s257 — THREE PRs (#1303–#1305): PLAN-0107 Phase C closes AC-12/13/14/15 — the PLAN goes 10/15 → 14/15; only AC-9 remains, BLOCKED on a Cray ruling.** 🔴 **Three "gates" that read as protection enforced nothing:** a `pyproject.toml` coverage threshold nothing measured (DELETED per Cray's typed ruling; the same claim struck from `PULL_REQUEST_TEMPLATE.md`), and a cache-bust test freezing per-file minima over **9 of 21 JS / 0 of 4 CSS files** — replaced by a relational diff check. 🔴 **AC-12's dead-port probe exits 1 while pytest reports `4005 passed, 484 skipped`** — 484 skips against a normal 8. | `1993bda` / [#1305](https://github.com/CrayJThiemsert/vero-lite/pull/1305) / `docs/plans/done/0107-oracle-coverage-hardening.md` |
| 2026-08-26 | **s255 — FOUR PRs (#1293–#1296): PLAN-0115 COMPLETE 10/10 and ARCHIVED — `tools/probe_battery/` ships as ADR-0038 C6's named D2 form-(c) enforcer.** 🔴 **VX-1 DISCHARGED** (owed since PLAN-0021, never answered): a non-blocking Stop-hook `systemMessage` **does** surface as `Stop says: …` to the **user's UI only**, but adopting it breaks **PLAN-0069 AC-3** parity — available, unadopted. 🔴 The instrument found **two defects in itself**; the stale-`.pyc` one passed the full local suite and **only CI reddened**. | `2448f90` / [#1296](https://github.com/CrayJThiemsert/vero-lite/pull/1296) / `docs/plans/done/0115-*.md` |
| 2026-08-25 | **s254 — FOUR PRs (#1288–#1291): PLAN-0115's four SDs RULED (Cray, typed).** 🔴 **SD-2's two drafted options BOTH failed on measurement** — (a) a hook exiting 0 sends its stderr note to a debug log holding **0 files and a dangling symlink**; (b) trail annotation corrupts **four control-flow reads** in `_goal_gate.py`. Ruled: zero-residue upheld, visibility to **Telegram keyed to the lock**; the *"no Telegram"* clause **struck — no author, no reviewer** (ADR-0018 VX-1). SD-1 effort **~36 → 53 sites / 50 files**, measured. SD-3 **defer**. | `db98126` / [#1288](https://github.com/CrayJThiemsert/vero-lite/pull/1288) / `docs/plans/done/0115-*.md` |

_[The two oldest rows (**s234, s233**) rotated to `docs/status-archive/2026-h1-status.md` at the s243 cont. reconcile, holding the table at ten. Two rows were added: the **s242 backfill** — Cray ruled it in, discharging the gap the s243 reconcile flagged, and its four rulings are no longer carried by narrative alone — and a **second s243 row**, because Step 1 is a BUILD event of a different kind from that session's rulings and folding it into the existing row would have written a row far over R2's ~600-char pointer cap. The oldest row (**s237**) rotated to the same file at the s245 reconcile, holding the table at ten; the s238 row followed at the s246 reconcile for the same reason. The **s239** row followed at THIS (s247) reconcile, again holding the table at ten. **Session 248 discharged the pointer-cap overage this table still carried: 8 of the 10 rows were over R2's ~600-char cap, and are now zero.** Each row's substance — not merely the path it named — was resolved against `git ls-files` before that row was shortened; the one fact tracked nowhere else, s240's *ancestry is not content*, was **rehomed first** into `.claude/skills/git-workflow/SKILL.md`, then re-pointed, then trimmed. All eight full originals are preserved verbatim in `docs/status-archive/2026-h1-status.md` (R4, move-never-drop). The **s240** row rotated to the same file at THIS (s248) reconcile, holding the table at ten. ⚠️ It is the one row whose fact was rehomed the session *before* it rotated — *ancestry is not content* now lives in `.claude/skills/git-workflow/SKILL.md`, and that skill's widened `description` surfaces it automatically — so its rotation drops nothing that STATUS was the sole carrier of. The **s241** row rotated to the same file at THIS (s249) reconcile, holding the table at ten. Its substance keeps two tracked homes — `docs/conventions/retired-claims.md` for the guard it shipped, and the *"the two s241 pre-commit guards are FLOORS, NOT CEILINGS"* entry in §Active TODOs for the live remainder — so it, too, rotates on the count rule alone. The two oldest rows (**s243**, **s242**) rotated to the same file at the **s251** reconcile — a two-session reconcile added two rows (s250, s251), so two left to hold the table at ten. Both rotate on the count rule alone: s243's G-13/G-14 substance lives in `docs/plans/done/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md`, and s242's SD-E reversal, second L1 re-reading and OQ-7(b) each keep a live Active TODO plus `docs/adr/0035-hosting-and-exposure-model.md`, whose own amendment pass records that a LOCKED ruling is amended in place, never edited. The two oldest rows (**s244**'s #1249 ฿-facet row and **s243 cont.**'s #1246 row) rotated to the same file at THIS (s253) reconcile — two s253 rows entered, one build and one governance, so two left to hold the table at ten. Both rotate on the count rule alone, **checked against the artifact before trimming, not assumed**: the #1249 emission fix and its run-scoped `(action_id, facet kind)` ledger are documented in `services/engine/procedures/action_step.py`'s own docstring, and the #1246 `triggered_by: null` / two-probes-on-different-assertions substance lives in `docs/plans/done/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md`. The two oldest rows (**s245**, **s244**) rotated to the same file at THIS (s254) reconcile — two s254 rows entered, one rulings and one governance, so two left to hold the table at ten. Both rotate on the **count rule alone**: s245's *three guards passed while protecting nothing* finding is the one that promoted `CLAUDE.md` §8's witnessed-RED rule, and lives there as binding text; both rows' PLAN-0112 build substance is in `docs/plans/done/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md`. The oldest row (**s246**) rotated to the same file at THIS (s255) reconcile — one s255 row entered, so one left to hold the table at ten. It rotates on the **count rule alone**, checked at the artifact rather than assumed: PLAN-0112 is COMPLETE 9/9 and its AC-7(i) finding lives in `docs/plans/done/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md`, and the week-stale-checkout incident is recorded in `docs/logs/2026-08-22-s246-*.md`, which the row itself names. The oldest row (**s247**) rotated to the same file at THIS (s257) reconcile — one s257 row entered, so one left to hold the table at ten. It rotates on the **count rule alone**: the Active-TODOs pointer cap it records is binding text in `docs/runbooks/memory-architecture.md` §R2 and in its enforcer `.claude/agents/status-scribe.md`. ⚠️ **Its *"R9 is now tracked NOWHERE"* finding was NOT re-checked at this reconcile** — surfaced to Cray rather than asserted resolved; the full row travels verbatim into the archive, so nothing is dropped. The oldest row (**s249**) rotated to the same file at THIS (s260) reconcile — one s259–260 row entered, so one left to hold the table at ten, on the **count rule alone**: PLAN-0112's SD-4 reversal lives in `docs/plans/done/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md` and the ADR-016 amendment it required is Accepted. ⚠️ **Its OQ-1 ruling — Code may append a `## Post-archival amendment` and one inline pointer in `done/`, supersession pointers ONLY — still governs, but the BROADER "may Code edit `done/` at all" question it left open is carried by no Active TODO row** (grepped at this reconcile: the other STATUS hits *use* the mechanism, they do not hold the question). It travels into the archive with the row. The oldest row (**s250**) rotated to the same file at THIS (s261) reconcile — one s261 row entered, so one left to hold the table at ten, on the **count rule alone**. ✅ **Its substance was re-grepped at the artifact, not read off the row's own claim:** the R2 caps are live in `docs/runbooks/memory-architecture.md` (4 hits) **and** in their enforcer `.claude/agents/status-scribe.md` (3 hits for `4,096`/`s141`/`s194`, so both backfills survive), and the `index.lock` root cause is live in `.claude/skills/git-workflow/SKILL.md` (5 hits). ⚠️ Its `53,048 → 48,645 B` figure is a **historical measurement** that now exists only in the archived row. **s261 also discharged a pointer-cap overage in §Active TODOs that s260 had asserted was zero:** eight rows — seven **ticked** ones plus the R2-cap row itself — ran 700–1,850 chars against R2's ~600 cap and were shortened to pointers, each naming the archived PLAN or `docs/logs/` file that holds its full story; **all eight originals travel verbatim to `docs/status-archive/2026-h1-status.md`** (R4, move-never-drop). 🔴 **The PLAN-0109 four-defect row was deliberately NOT shortened** — it is the sole tracked carrier of those defects (the PLAN itself does not yet hold them), so trimming it would drop a live defect list to an archive. The oldest row (**s251**) rotated to the same file at THIS (s263) reconcile — one s263 row entered, so one left to hold the table at ten, on the **count rule alone**: PLAN-0113 is COMPLETE and archived at `docs/plans/done/0113-scope-event-fired-run-to-its-firing-case.md`, and the **fourth load-gate refusal SB-3 does not enumerate** keeps its own live Active TODO row.]_

## In-Flight Discussions

- **OPEN QUESTION for Cray — does a skill's registry table *bind*?** (Code's observation, not a ruling.) s210's closing notice asserted the four-work-stream registry table in `.claude/skills/stream-status/SKILL.md` (#1062) is **canonical**, and that a carrier-artifact change must update it **in the same PR**. The table as *reference* is fine; the **same-PR obligation** is the part that would have to live in `CLAUDE.md` or an ADR to bind — §1 places `.claude/skills/` at **Tier 2.6, derived, no independent precedence** (ADR-0017 D6). **Cray's call: promote it, or keep the table advisory.**
- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm — **not yet drafted**, and it needs a fresh ADR number. _[The old "≥ ADR-014" floor recorded here was **moot** — see the Active TODO below, corrected s141: ADRs now run past 0032 and `0014-WITHDRAWN.md` exists. Kept as one pointer rather than two divergent copies.]_
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).

## Active TODOs

- [ ] **🆕 CRAY'S CALL — the *45% flip rate* in Current Focus is CONTRADICTED, not re-measured.** s262 ran `fleet` × `qwen/full` twice under a 16,384 cap: **20 of 20 items byte-identical** (drafts, rationales, `eval_count`), while latency differed on 17 — two genuine runs. The 45% was measured on `energy` **before `num_predict` existed**, when generation ran to a client timeout and was CUT; a wall-clock cut is not reproducible by construction. **Hypothesis: it measured the harness.** One repeat per cell settles it. **Do not budget repeats on the 45% until then.**
- [ ] **🆕 CRAY'S CALL — the PORTABLE CORE of Lesson #0049 has no cross-project home, and no such surface exists yet.** Measured s262: `~/.claude/skills/` and `~/.claude/CLAUDE.md` **do not exist**, and Tier-0 auto-memory is path-scoped to this repo — so every reusable practice built here is vero-lite-only. Cray's intent (s262): **prepare, do not build** — no second project exists, and §1's Rule of Three says the abstraction waits for something to extract *toward*. **Trigger: the first new project.** **Read:** `docs/lessons/0049-measure-generation-demand-not-the-cap-that-happens-to-work.md` §PORTABLE CORE.
- [ ] **🆕 CRAY'S CALL — the fleet benchmark awards 100% to *"answer `escalate` on every item without reading anything"*.** `canonical_handler` is `escalate` for **all 14** breach items, so β cannot separate comprehension from a constant. ✅ **The CEILING half is solved (s264)** — the rationale axis separates the models (qwen **4–8/14**, gpt-oss **0–1/14**) — but that restores *discrimination*, **not validity**: a model can name a role and still always-`escalate`. Harder items remain the only fix for the exploit itself. **Read:** `benchmarks/model_compare/RESULTS-1.6.md` §13.
- [ ] **🆕 CRAY'S CALL — the phase-2 MODEL DECISION is still unbound, and `fleet` can no longer discriminate.** ✅ **Audit finding 3 (quantisation) is CLOSED s263** — q8 fixed **exactly the five items** q4 missed; ~60% of the handler gap was compression, not the model. 🔴 Both models now score **100/100/14-of-14**, and every cell but 4-bit qwen `full` is **n=1**. 🔴 **A comparability line exists at `0a1061f`:** §8–§10 was measured against the defective goal directive and does **not** compare with anything after it. 🔴 **Every live run needs a NEW typed §8 go.** **Read:** `benchmarks/model_compare/RESULTS-1.6.md` §9–§12.
- [ ] **🆕 Nothing measures Thai prose QUALITY — and that is what phase 2's LLM tasks actually are.** Everything scored so far grades structure, handler picks and pinned strings; nothing reads the prose a Thai operator would be handed. `DECISION.md` reserves the question for a **blind read that has never been run**, so no model choice can be defended on prose quality today. **Cray's call: schedule the blind read, or accept the gap explicitly.** **Read:** `benchmarks/model_compare/DECISION.md`.
- [ ] **🆕 CRAY'S CALL — PLAN-0116's THREE SDs are unruled and had no row here until s257.** `docs/plans/0116-deterministic-claim-rollup-tool.md`, `Status: Draft`, 0/8 ACs, 3 Steps, one PR, deterministic-offline. **SD-1 is the heavy one** — the mixed case (∃ vs ∀ reading); it hard-codes forever an interpretation of Cray's own typed four-line rule, and `_rollup.py` cannot be written until it is ruled. SD-2 (measure labelling stability here?) and SD-3 (exit-code contract) are light. ⚠️ **Measured s257, and it is the reason to rule deliberately rather than by default:** the tool ships with **zero wired producers and zero wired consumers** — both are cut by name in its Out of Scope — so on day one its only caller is its own test suite. Until s257 the SDs were carried only by a `blocked_on` line naming #1301 as *open*, and #1301 merged — the drift this row exists to stop.
- [ ] **🆕 CRAY'S CALL — the s256 walk's residue is TWO RUNS, not two cases; leaving them parked is the current lean.** Measured s257 LIVE, read-only, under three typed gos: both cases **ABSENT** (control-backed); `governed_repair_approval@41bb78353e7c4138` is still `waiting_human` at a resolvable `approve` gate, `@d8f5a677b8f73b3b` `completed`. 🔴 `DEMO-RESET.md` is **not** the tool for a visitor-created id; the per-case seam is `delete_case`. ✅ Resolving that gate is **harmless** — proven offline, not by clicking live ([#1304](https://github.com/CrayJThiemsert/vero-lite/pull/1304)). ⚠️ `audit_log` unchanged at 64 rows, so **how the cases went away is measured but unexplained**. **Read:** `docs/logs/2026-08-27-s257-fleet-walk-residue-readonly-probe.md`.
- [ ] **🆕 CRAY'S CALL — `.claude/worktrees/` is 1.8 GB and `git worktree prune` cannot reach most of it.** Measured s256 by set difference, jointly with the parallel session: **19 directories on disk · 7 registered · 6 prunable · 12 UNREGISTERED**. Prune touches **6 of 19**; the other 12 git no longer knows about and only a manual delete removes. Largest: `eloquent-chatelet` 257 MB · `recursing-chatterjee` 163 · `wizardly-hopper` 161 · `youthful-driscoll` 150. **Nothing deleted — 1.8 GB is irreversible and out of scope for Code.** Related: Cray ruled parallel sessions onto separate worktrees this session, so the set will keep growing.
- [ ] **🆕 CRAY'S CALL — a battery skip is indistinguishable from "no active goal" in the trail.** `_goal_gate.py`'s early return fires before any `record_evaluation` for BOTH the battery-lock stand-down and the no-goal case, so `goal.json` stays **byte-identical** — nothing can later establish that the gate ever stood down for a battery. This is the **price PLAN-0115 SD-2's zero-residue ruling pays**, not a defect, but the price was never measured when it was ruled. Changing it needs a new SD, not a trim. **Read:** `docs/logs/2026-08-26-sd-premortem-replay-experiment.md`.
- [ ] **🆕 ADR-016 SB-3 enumerates THREE load-gate refusals; the SHIPPED Step 1 has FOUR.** The fourth — `when_absent` supplied with **no `scope_by`** — was Cray-ratified at the #1275 merge (typed, s251), but SB-3's body still names only the three `scope_by`-present cases; re-checked in the ADR at the s251 reconcile. **Cray's call: amend the ADR, or leave the fourth recorded in the PLAN.** ⚠️ Whoever opens ADR-016 for this should also repair its **two dead pre-archive PLAN pointers** (`0052-*` and, since s252, `0113-*` — both now under `docs/plans/done/`). R8 exempts `docs/adr/` **temporarily and by design**, because G1 blocks Code from editing an Accepted ADR; the exemption's own comment says to remove it in the same change that lands those fixes. **Read:** `docs/adr/0016-governed-procedure-engine.md` §SB-3 · `docs/plans/done/0113-scope-event-fired-run-to-its-firing-case.md`.
- [ ] **🆕 CRAY'S CALL — should R2 cap the Active TODOs *COUNT*, and govern the Recent Decisions trailing ledger? Still unruled, and the pressure is now structural.** 🔴 STATUS entered s263 at **64,584 B against R1's 65,536-byte HARD ceiling — 952 B of headroom**, and is **~15 KB over the 49,152-byte soft target**; the s263 block only fit because s257 rotated. ⚠️ Active TODOs (~31 KB, ~48 entries) and the RD trailing ledger (~5.5 KB) are ungoverned **by count**, so rotation inside the windows **cannot** reach the soft target — capping either **authors a rule (R6)**. ⚠️ ~20 **open** rows are still over R2's ~600-char pointer cap (s261 shortened the ticked ones only). **Read:** `docs/runbooks/memory-architecture.md` §R2.
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
