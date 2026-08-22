---
last_updated: 2026-08-22T23:10:00+07:00
session: 246
current_batch: "s246 — THREE PRs merged (#1256–#1258), 0 open. PLAN-0112 Steps 6 AND 7 EXECUTED; PLAN-0112 AC-8 and AC-9 CLOSED — 8 of 9, AC-7 held open. The governable moment is LIVE on the published system."
current_actor: code
blocked_on: "Nothing. Main green, 0 open PRs. PLAN-0112 needs ONE Cray ruling to complete: AC-7(i)'s wording, measured false and left unticked. Owed: PLAN-0107 AC-9, PLAN-0109's three defects."
next_action: "Cray rules AC-7(i)'s narrowing, then PLAN-0112 is COMPLETE 9/9 and archives to done/. Then the Active-TODOs compliance trim — 27,473 B, 45% of STATUS, 24 of 35 items over cap."
head_commit: 38ef55e
recent_commits: [38ef55e, ee41b55, 73c968c, 9d0c3ff, 1d6fbd0, cc1b8e9, 12126a3, ed6a713, a8c42b7, 6fce826]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 246, 2026-08-22 (head_commit `9d0c3ff` → `38ef55e`) — THREE PRs
> MERGED ([#1256](https://github.com/CrayJThiemsert/vero-lite/pull/1256), [#1257](https://github.com/CrayJThiemsert/vero-lite/pull/1257),
> [#1258](https://github.com/CrayJThiemsert/vero-lite/pull/1258)), 0 open. PLAN-0112 Steps 6 and 7 EXECUTED;
> PLAN-0112 AC-8 and AC-9 CLOSED — eight of nine, with AC-7 deliberately held
> open on its own wording — and the visitor flow
> was driven end to end on the LIVE published system.**
>
> 🔴 **The host had never received Step 5.** Its checkout stood at `205ba4b`, a
> week behind, so the `accepted-quote` ingress row had never reached production and
> Step 5's whole promise was unreachable there. Nothing in the repo said so; only
> the pre-flight diff of the two files the host actually reads did. Cray's advance
> go for Step 7 predated that fact and the demo reading `CONSUMED`, so Phase D was
> re-asked with both on the table — `DEPLOY.md` §0 requires the go per occasion AND
> per phase.
>
> 🔴 **AC-7(i)'s own wording is MEASURED FALSE, and production agreed twice.** The
> criterion says a visitor-fired run's link rows survive a reset. Fleet's `intake`
> is a fleet-wide scan, so every visitor run's gate also decides the seeded demo
> case and `on_resolved` writes one link row **per decided case** — three, for a run
> fired from the visitor's own case. The reset reaches demo-scoped rows by
> `case_id`, so those cannot survive. Confirmed independently on the live system:
> the reset deleted **six** link rows for **two** demo runs, and the live gate
> reported *"3 candidates reached this gate"*. The build is complete and proven;
> the criterion is left UNTICKED pending Cray's narrowing.
>
> ✅ **AC-8 — `GET /runs` gained a bounded newest-N default** (200, env-overridable).
> A build choice SD-6(b) did not specify is recorded rather than left implicit:
> `waiting_human_count` is NOT bounded, because a "waiting on me" badge that shrank
> with the page would under-report decisions still pending.
>
> ✅ **The live walk.** Non-cheapest accept → 422 with the reason box scoped to that
> quote; reason submitted → a run fired with `trigger: event`; Tab H moved 2 → 3 and
> its badge 1 → 2; the gate reasoned on *"Spend 62000.0 THB"*, an amount that
> exists nowhere in the seed data, which is what makes it the visitor's OWN case;
> SoD refused the requester and the ladder resolved to `appr-owner`, who approved;
> the run parked again at `fulfill`; and the demo still read **`PRISTINE`** beside
> it. Rollback point recorded: `oct-fleet-maintenance-app:prev` = `sha256:63c5ec37…`.
>
> ⚠️ **Five instrument failures this session, and the artifact was right every
> time** — a block measurer that swallowed a paragraph, a positive control that
> moved an optimistic-lock `version`, a heredoc that ate 49 lines' worth of
> backticks into `done/0110`, a tripwire comparison blind to a line wrap, and a
> `docker exec … cat` against a distroless image that printed FAIL on an error
> string. Each was repaired rather than waived; a positive control caught all five.
>
> ✅ **Gate on `38ef55e`: 4267 passed / 8 skipped** (4259 + the 8 added) · bare
> `ruff check .` clean · `ruff format --check .` 654 files · `mypy --strict` clean
> over 201. Five non-vacuity probes, one per assertion, every mutation on a
> production file, each restored byte-identically and sha256-verified.

> **Session 245, 2026-08-22 (head_commit `a8c42b7` → `9d0c3ff`) — FOUR PRs
> MERGED ([#1252](https://github.com/CrayJThiemsert/vero-lite/pull/1252), [#1253](https://github.com/CrayJThiemsert/vero-lite/pull/1253),
> [#1254](https://github.com/CrayJThiemsert/vero-lite/pull/1254), [#1255](https://github.com/CrayJThiemsert/vero-lite/pull/1255)), 0 open.
> PLAN-0112 Step 5 SHIPPED — the governable moment now reaches the published
> visitor — and PLAN-0112 AC-2 through AC-6 are CLOSED. It stands at six ACs
> of nine, with Steps 6 and 7 blocked on nothing.**
>
> 🔴 **THREE guards written this session passed while protecting nothing, and
> every time the INSTRUMENT was wrong rather than the artifact.** A
> client-side-comparison ban that ENUMERATED `Math\.min\s*\(` reported 7
> passed with an ordinary `Math.min.apply(null, …)` planted in the shipped
> view. A control-wiring guard reported 16 passed with the button un-wired:
> `"acceptQuote(" in source` is satisfied by the function's own definition,
> and `"ตกลงใบนี้" in source` by the SUBSTRING inside `'ยืนยันตกลงใบนี้'`. A bare
> `grep -c` returned 0 for a retired clause that wraps across a line break —
> and that was precisely the site the audit had missed. **Enumerating syntax
> is not asserting a property, and a substring check over a file that also
> contains longer strings asserts almost nothing.** That is what promoted
> `CLAUDE.md` §8's witnessed-RED discipline from a PLAN stamp to a binding
> rule ([#1253](https://github.com/CrayJThiemsert/vero-lite/pull/1253)).
>
> 🔴 **G-13's prose-site set was FOUR, not the two it named** — the two extra
> sites are docstrings, invisible for exactly G-13's own stated reason: neither
> *calls* the endpoint, each *asserts it is unreachable*. All four corrected
> under G-13's own split, with the ฿-report half left TRUE and
> `seed_settled_history_case` still necessary.
>
> 🔴 **A leftover process fooled TWO sessions for four days, and the recipe
> that always worked is what hid it.** `git diff --stat`, pid 1843083, held
> `.git/index.lock` intermittently since 2026-08-18; the prescribed recovery
> (*verify HEAD → `pgrep -a git` → retry, never blind-delete*) succeeded every
> time, so nobody looked further. Measured under Cray's typed go: `STAT=T`,
> `WCHAN=do_signal_stop` — **SIGSTOP-suspended, never executing**, which
> explains the un-finishing diff, the ignored `SIGTERM` and the four-day lock
> together. **A workaround that always succeeds is how a root cause stays
> invisible.**
>
> ✅ **Live evidence on the published profile, not a gate:** no persona → 401 ·
> non-cheapest accept → 422 with the reason box scoped to that quote · reason
> submitted → +1 run, `trigger: event`, `waiting_human` · cheapest accept →
> no reason demanded. SD-2(b) observed live.
>
> ✅ **Gate on `9d0c3ff`: 4259 passed / 8 skipped** · bare `ruff check .` clean ·
> `ruff format --check .` 652 files · `mypy --strict` clean over 201. Five
> non-vacuity probes, every mutation on a production artifact, each restored
> byte-identically from the scratchpad and sha256-verified. A post-merge
> re-verification against 11 criteria fixed BEFORE the run returned
> `VERDICT=STEP5_REVERIFY_PASSES`, 18/18 — recorded `confirmed — prior intact`
> per §6, **not** a finding that anything was wrong.
>
> ⚠️ **Four UX chips were spawned BEFORE the commit existed and were stopped.**
> Their findings survive in the PLAN's §Steps Step 5 (WCAG contrast 3.29:1 on
> `.case-submit`; the accept button 4.59× smaller in area than the routine
> add-quote button; `--fg`/`--panel` used in `views.css` and defined nowhere).
> They must be re-spawned SEQUENTIALLY — `view-case.js` is in all four
> write-sets.

> **Session 244, 2026-08-21 (head_commit `f52dbdc` → `a8c42b7`) — THREE PRs
> MERGED ([#1248](https://github.com/CrayJThiemsert/vero-lite/pull/1248),
> [#1249](https://github.com/CrayJThiemsert/vero-lite/pull/1249),
> [#1250](https://github.com/CrayJThiemsert/vero-lite/pull/1250)), 0 open.
> PLAN-0112 Steps 3 and 4 BUILT: a visitor's accepted quote now fires the
> governed run, and the reads AC-2/AC-3/AC-4 specify are written. No AC ticked
> yet — see §Active TODOs.**
>
> 🔴 **A SECOND composition failure, and no key design could have routed around
> it.** G-14 recorded that SD-2(b) and SD-5(b) do not compose on the bridge's
> dedup KEY. They also do not compose on its SD-P4 in-flight guard, which selects
> on `procedure_id` and status alone. Measured: fleet's published profile pins
> `OCT_DEMO_SEED_OPERATE=true` and that seed RAISES unless its run parks at
> `waiting_human`, so a visitor's acceptance returned `SKIPPED_IN_FLIGHT` and
> wrote nothing — the whole promise failing with only an `event_skipped` audit
> row. With no seed at all, a visitor's SECOND acceptance was skipped by their
> own first parked run, so the blocker is inherent to SD-2(b) on a gated
> procedure. Cray ruled the opt-out; the default is unchanged and is pinned by a
> test that already existed.
>
> 🔴 **Ordering is the claim, not a detail — and it fails with no error.** The
> seam must fire AFTER `_refresh_case_events`. Fire before the projection catches
> up and the run still fires, still parks, still shows a healthy gate — about
> ANOTHER truck's case, with the visitor's own absent from every proposal.
> Measured: a run whose single proposal resolved to `case-demo-truck03-gearbox`.
> No count assertion can see that, so every new test asserts the visitor's
> `case_id` is among the proposals, and the probe that reverses the two lines
> reddens that assertion while the count stays green.
>
> 🔴 **Opting out of SD-P4 makes two runs able to approve ONE case — measured,
> and left in place on Cray's ruling.** Two `RepairCaseRunLink` rows result, from
> different runs, with `hook_failures` empty: designed behaviour, not a swallowed
> error. Both ฿ readers were measured NOT to double-count — the month-end export
> collapses them via a `case_id`-keyed latest-wins dict (฿62,000 once, not twice)
> and Tab J's rollup takes no input from this procedure at all. **Unmeasured and
> owed:** WHICH of the two runs the report names.
>
> ✅ **#1249, from the parallel strand: the Box-4 ฿ facet was UNREACHABLE, not
> missing.** Four of five ฿-producing verticals wrote `economic_impact` only into
> the action envelope while `benefit_rollup` reads `StepResult.reasoning_trace`,
> so Tab J read ฿0 for all of them. Emission moved down to `ActionStepExecutor`
> — the only seam `aquaculture`/`energy` share, since they bind it bare — with a
> run-scoped ledger, without which procurement reported ฿16,215,000 for a run
> worth ฿8,107,500. NOT a PLAN-0112 step.
>
> ✅ **Gate on `a8c42b7`: 4243 passed / 8 skipped** (+3 exactly over `6fce826`,
> the diff touching one file whose test count goes 4 → 7) · bare `ruff check .`
> clean · `ruff format --check .` 651 files · `mypy --strict` clean over 201.
> Ten non-vacuity probes across the two PRs, every mutation on production code,
> each source restored byte-identically from the scratchpad and sha256-verified.

> **Session 243 cont., 2026-08-21 (head_commit `0b5c333` → `f52dbdc`) — ONE PR
> MERGED ([#1246](https://github.com/CrayJThiemsert/vero-lite/pull/1246)), 0
> open. PLAN-0112's FIRST real code: Step 1 executed and AC-1 CLOSED —
> `run_procedure_endpoint` now fails closed without an authenticated human, 403
> before spec loading and before any DB write.**
>
> 🔴 **The asymmetry is closed, and the door that was open was the widest one.**
> `gate/resolve` and `cancel` both already 403 on a `None` principal; firing a
> governed run — the act that *creates* the thing those two guard — accepted an
> unauthenticated caller and recorded `triggered_by: null`. PLAN-0110's **G10(6)**
> found it and PLAN-0112 hard-ordered it FIRST. The guard now sits above the spec
> load, so a principal-less request can never leave a row behind.
>
> 🔴 **Non-vacuity needed TWO probes on DIFFERENT assertions, and the second is
> the one that mattered.** Deleting the guard reddens the 403 assertion —
> **presence**. Only *relocating* it past the write reddens the zero-rows
> assertion while the 403 still passes — **placement**, which is the half AC-1's
> own *"before spec loading or any DB write"* clause rests on. A delete-only
> battery would have reported success with that clause **unevidenced**.
>
> 🔴 **The new guard broke the tests that prove the SIBLING guards — by
> ARRANGEMENT, not assertion.** They deliberately run with authn off and minted
> their parked run through the very door this change closes, so their setup
> failed while their claim stood. ⚠️ **The trap that was avoided is now recorded
> in their own docstrings:** leaving authn ON and omitting the header yields a
> **401 from the dependency**, which never reaches the 403 — green, and silently
> no longer proving RF-1.
>
> ⚠️ **Blast radius was measured BEFORE the change (green baseline, 45 passed)
> and again after, so every red was attributable — and it arrived in TWO waves.**
> Arming authn in the scenario fixture reddened two *further* tests, because the
> fixture governs every request in that module, not only the run POST.
>
> ✅ **Gate on `f52dbdc`:** `pytest tests/` **4222 passed / 8 skipped** (4220 at
> session start — **+2 exactly**) · bare `ruff check .` clean · `ruff format
> --check .` **648 files already formatted**, so no file was touched after the
> probes were witnessed · `mypy --strict services/ verticals/` clean over 201.
> ✅ Cray ruled the missing **s242 Recent Decisions row** be backfilled at this
> reconcile — done below.


_[Current-Focus rotation ledger. The sessions-233–234 and 235/236 blocks rotated
to `docs/status-archive/2026-h1d-current-focus.md` at earlier reconciles; the
**sessions-237–238 and session-239** blocks rotated there this reconcile —
**one session below the four-session window, deliberately**, because the s241
Active-TODO corrections had to land without growing this file (SD-1 in the s241
reconcile report). Rotated with them: s237's video-rulings carried risk, since
DISCHARGED s239 to `docs/strategy/public/intro-video-production-rulings.md`, and
s239's headline — eight PRs, two host-state deploys, and *"a summary that is
ACCURATE about what it cites still shrinks"*; s239's two host records survive
tracked at `docs/logs/2026-08-18-s239-*` and `docs/logs/2026-08-19-s239-*`. The **session-240** block rotated there at the s242 reconcile — it measured ~5,800–5,900 B against R2's 4,096 B per-block cap, and rotating it is the runbook's own prescribed response to STATUS sitting over R1's soft target (fix the voice, do not raise the ceiling). Its live residue is not lost: the three s240 items that were open when it rotated (the font-size decision gating the beat-4 geometry re-measure, the unmeasured host-side run-list backlog badge, and the three unnamed Advisory-proposal candidates) are carried in §Active TODOs rather than left only in the archive. The **session-241** block rotated there at the s244 reconcile, holding the window at four; its retired-claim marker travelled with the quote it labels, so the guard stays satisfied on both surfaces. The **session-242** block rotated there at THIS (s245) reconcile — again one session below the four-session window and again deliberately: STATUS stood at 61,636 B, 12,484 B over R1's soft target, and a new block could not be written without either this rotation or a trim that would delete facts. Its live remainders were carried before the move, not after — PLAN-0110 SD-E's reversal and ADR-0035's L1 re-read each hold their own Active-TODO entry, and PLAN-0107 AC-10 is recorded in that PLAN. The **session-243** block rotated there at the s246 reconcile, holding the window at four sessions; its G-13/G-14/G-15 substance lives in `docs/plans/0112-*.md`, which the Active-TODO entry points at — the fact the s245 reconcile measured when it discharged the trim prerequisite.]_

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
| 2026-08-22 | **s246 — THREE PRs (#1256–#1258): PLAN-0112 Steps 6 and 7 EXECUTED; AC-8/AC-9 CLOSED (AC-7 held open) and the visitor flow proven LIVE.** 🔴 **The host had never received Step 5** — a week-stale checkout kept the accepted-quote ingress row out of production. 🔴 **AC-7(i)'s wording is MEASURED FALSE**: a fleet-wide `intake` makes every visitor run's gate decide the demo case too, so its demo-scoped link rows cannot survive a reset; production agreed twice. UNTICKED for Cray. | `38ef55e` / [#1257](https://github.com/CrayJThiemsert/vero-lite/pull/1257) / `docs/logs/2026-08-22-s246-*.md` |
| 2026-08-22 | **s245 — FOUR PRs (#1252–#1255): PLAN-0112 Step 5 SHIPPED, AC-2…AC-6 CLOSED — the governable moment reaches the published visitor.** 🔴 **THREE guards passed while protecting nothing:** enumerating `Math\.min\s*\(` missed `Math.min.apply`; `"acceptQuote(" in source` was satisfied by the function's own definition. **The instrument was wrong every time, not the artifact** — which promoted `CLAUDE.md` §8's witnessed-RED rule (#1253). 🔴 **G-13's prose set was FOUR, not two.** | `9d0c3ff` / [#1255](https://github.com/CrayJThiemsert/vero-lite/pull/1255) / `docs/plans/0112-*.md` |
| 2026-08-21 | **s244 — TWO PRs (#1248, #1250): PLAN-0112 Steps 3 and 4 BUILT — a visitor's accepted quote fires the governed run.** 🔴 **A SECOND composition failure beyond G-14:** SD-2(b) and SD-5(b) also fail to compose on the bridge's SD-P4 in-flight guard, which no key design can route around — the published profile's parked seed made every acceptance a silent `SKIPPED_IN_FLIGHT`. 🔴 **Ordering fails with no error:** fire before `_refresh_case_events` and the gate is about ANOTHER truck. **No AC ticked yet.** | `a8c42b7` / [#1248](https://github.com/CrayJThiemsert/vero-lite/pull/1248) / [#1250](https://github.com/CrayJThiemsert/vero-lite/pull/1250) / `docs/plans/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md` |
| 2026-08-21 | **s244 — ONE PR (#1249): the Box-4 ฿ facet was UNREACHABLE, not missing.** Four of five ฿-producing verticals wrote `economic_impact` only into the action envelope while `benefit_rollup` reads `StepResult.reasoning_trace`, so Tab J read ฿0 for all of them. Emission moved down to `ActionStepExecutor` — the only seam `aquaculture`/`energy` share, since they bind it bare — with a run-scoped `(action_id, kind)` ledger, without which procurement reported ฿16,215,000 for a run worth ฿8,107,500. **Standalone wiring fix; NOT a PLAN-0112 step.** | `6fce826` / [#1249](https://github.com/CrayJThiemsert/vero-lite/pull/1249) / `services/engine/procedures/action_step.py` |
| 2026-08-21 | **s243 cont. — ONE PR (#1246): PLAN-0112 Step 1 EXECUTED, AC-1 CLOSED — `run_procedure_endpoint` 403s without an authenticated human, before spec load and any DB write.** 🔴 **The only producer of a `PipelineRun` was the only one of three doors that did not fail closed**, recording `triggered_by: null` — PLAN-0110's G10(6) found it. 🔴 **Non-vacuity took TWO probes on DIFFERENT assertions:** deleting the guard proves *presence*; only RELOCATING it past the write reddens the zero-rows assertion while the 403 still passes — the *placement* half AC-1 rests on. ⚠️ Sibling-guard tests broke by ARRANGEMENT, not assertion. Gate **4222 passed** (+2). | `f52dbdc` / [#1246](https://github.com/CrayJThiemsert/vero-lite/pull/1246) / `services/api/routers/runs.py` / `docs/plans/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md` |
| 2026-08-21 | **s243 — TWO PRs (#1243, #1244): all SEVEN PLAN-0112 SDs RULED (SD-3, then SD-2/4/5/6/7) and the Step-2 gate DISCHARGED.** 🔴 **G-14 — two of Cray's own rulings did not compose:** SD-2(b)'s re-fire on a changed amount is swallowed by SD-5(b)'s bridge idempotency (`event_key` omits the amount) — **no error, no log**; key on `[case_id, quote_id]`. 🔴 **AC-2's pass read was FALSE in the shipped demo** — intake is a fleet-wide scan, so every visitor-fired run gates. 🔴 **G-13 — the exclusion is load-bearing PROSE at two sites that assert unreachability**, invisible to a call-graph review. ⚠️ Two corrections made a ruling CHEAPER; SD-2 was ruled AGAINST the PLAN's recommendation. | `0b5c333` / [#1243](https://github.com/CrayJThiemsert/vero-lite/pull/1243) / [#1244](https://github.com/CrayJThiemsert/vero-lite/pull/1244) / `docs/plans/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md` |
| 2026-08-21 | **s242 — FIVE PRs (#1237–#1241): PLAN-0107 AC-10 CLOSED and FOUR Cray rulings, two re-opening settled ground.** 🔴 **PLAN-0110 SD-E REVERSED** — quote-acceptance, not case creation, is the governable moment; a no-principal firing mints a run **nobody can ever approve**. 🔴 **ADR-0035's L1 re-read a SECOND time** — app code may READ the gate's verdict, never perform the gate; **OQ-7 (b)** stamps the absence rather than fabricating a principal. That pass read **126 insertions, 0 deletions**: a LOCKED ruling is not edited. ✅ AC-10 grades all eleven gold cases against the ENGINE; the register shipped EMPTY. _[Row backfilled s243 cont., Cray-ruled.]_ | `bf2771e` / [#1238](https://github.com/CrayJThiemsert/vero-lite/pull/1238) / [#1241](https://github.com/CrayJThiemsert/vero-lite/pull/1241) / `docs/adr/0035-hosting-and-exposure-model.md` |
| 2026-08-21 | **s241 — FIVE PRs (#1229, #1231–#1234): the backlog measured as RETRIEVAL debt, not technical debt, so the session shipped two pre-commit guards.** 🔴 **Both caught real defects before merge** — the retired-claim guard blocked its own first commit and flagged STATUS's own narrative; the AC-ledger guard found PLAN-0108's live duplicate label plus one in `done/0042`. 🔴 **The wrong fix was to narrow the retired text until the quote stopped matching** — editing the artifact to satisfy the instrument. ⚠️ **Findings were reported from a subagent that never returned; two unsourced rows RETRACTED.** | `6a2e34c` / [#1234](https://github.com/CrayJThiemsert/vero-lite/pull/1234) / `docs/conventions/retired-claims.md` |
| 2026-08-19 | **s240 — THREE PRs (#1225–#1227); PLAN-0107 AC-11 CLOSED and PLAN-0111 drafted with all six SDs ruled (Cray, typed).** 🔴 **A `git merge` reported success and silently reverted #1225** — `merge-base --is-ancestor` answered YES while the merged tree had dropped the change; **ancestry is not content**. 🔴 **A non-vacuity probe proved the wrong thing** — the `422` assert sat before the money read, so the claim the module exists to make never executed. 🔴 **Latest-wins means a credit note REPLACES the invoice** (`20,000.00` → `-15,000.00`), so admitting it is the silent option; the refusal closes the quote side's asymmetry and is INTERIM by docstring. **SD-E forces SD-A to a separate `repair_case_credit_note` table.** | `8fd3848` / [#1226](https://github.com/CrayJThiemsert/vero-lite/pull/1226) / [#1227](https://github.com/CrayJThiemsert/vero-lite/pull/1227) / `docs/plans/0111-*.md` |
| 2026-08-19 | **s239 — EIGHT PRs (#1216–#1223) and TWO host-state deploys under separately typed gos.** 🔴 **An ACCURATE summary still shrinks:** the video rulings were seven, not four — one typed two days earlier and recorded inline rather than in the table, carrying a live tripwire. Rehomed tracked, each row stamped with its source position. 🔴 **s238's correct forward-slash fix silently disarmed the path guard** for the ten commands it corrected, and the module's own `checked >= 5` floor stayed satisfied by the READMEs — a count floor cannot see a document category go dark. Now 26 paths checked, 0 broken. 🔴 **The shared `deploy.py` cannot deploy this system** and §3 handed it over without saying so; `DEPLOY.md` created, and its FIRST use found its own gap (`<last-deployed-sha>` comes from the HOST checkout, not the image's build sha). ✅ Tab F opens the origin narrative with six passages mapped to six steps, `reshape` deliberately unmapped. ✅ R8 ruled: drop the ฿15,000 contrast. ✅ Brand mark live — and **not legible at 28 px**, recorded rather than discovered later. | `dbb3e58` / [#1218](https://github.com/CrayJThiemsert/vero-lite/pull/1218) / [#1221](https://github.com/CrayJThiemsert/vero-lite/pull/1221) / `deploy/published/oct-fleet-maintenance/DEPLOY.md` / `docs/strategy/public/intro-video-production-rulings.md` |

_[The two oldest rows (**s234, s233**) rotated to `docs/status-archive/2026-h1-status.md` at the s243 cont. reconcile, holding the table at ten. Two rows were added: the **s242 backfill** — Cray ruled it in, discharging the gap the s243 reconcile flagged, and its four rulings are no longer carried by narrative alone — and a **second s243 row**, because Step 1 is a BUILD event of a different kind from that session's rulings and folding it into the existing row would have written a row far over R2's ~600-char pointer cap. The oldest row (**s237**) rotated to the same file at the s245 reconcile, holding the table at ten; the s238 row followed at the s246 reconcile for the same reason.]_

## In-Flight Discussions

- **OPEN QUESTION for Cray — does a skill's registry table *bind*? (raised by s210's closing notice, recorded here s209 cont.; Code's observation, NOT a ruling and NOT a defect.)** The notice asserted that the four-work-stream registry table in `.claude/skills/stream-status/SKILL.md` (#1062) is **canonical**, and that a carrier-artifact change must update it **in the same PR**. The registry as *reference* is unobjectionable; the **same-PR obligation** is the part that would have to live in `CLAUDE.md` or an ADR to bind — `CLAUDE.md` §1 places `.claude/skills/` at **Tier 2.6, derived, carrying no independent precedence (ADR-0017 D6)**, and §4 draws the bright line that *"a binding rule never moves into a skill (a skill that fails to trigger would silently drop it)"*. Cray's call: promote the obligation into a canonical, or keep the table advisory.
- **PLAN-0096 — COMPLETE 12/12 and ARCHIVED (s193); FOUR RESIDUAL RISKS OUTLIVE IT** (which is why this entry is a pointer and not a deletion): **RR-1** (per-baht approver→case attribution is INFERENCE, not data — silently wrong the day two approvers share a gate resolution), **RR-3** (concurrency-race coverage — both named gaps CLOSED s195 by #995), **ศูนย์ต้นทุน ships EMPTY** (partner granularity unanswered — also an open Active TODO below), and **`latest_per`** still collapsing two open cases on one truck (**Cray typed (ค) defer** — the older case reports as *ungoverned*, indistinguishable from a governance failure). Read the archived PLAN, not a restatement: `docs/plans/done/0096-fleet-flow-completion-phase1.md` (§Verification preamble + §Acceptance Criteria for RR-1 / RR-3 / ศูนย์ต้นทุน; §Step 8 for `latest_per`).
- **COMPLETE-and-ARCHIVED, no live remainder here — read the archived PLAN, never a restatement:** **PLAN-0095** (Docker image boot, s177 — its OQ-1 hosting model CLOSED by ADR-0035) · **PLAN-0094** (L1 loop-detect restructure, s183 — its OQ-4 is ANSWERED; see the PLAN-0102 row in Active TODOs) · **PLAN-0093** (LLM-arm degrade disclosure, s172 — **no follow-on owed**) · **PLAN-0091** (narrative→vertical scaffolder, s168 — two named follow-ons, **neither scheduled**, both greenfield/human-call) · **PLAN-0088** (cross-run read substrate + the four run-insight readers, s171 — **three AC-WORDING debts, none a code defect**) · **PLAN-0036 + PLAN-0037** (Fastenal procurement vertical Stage 1 + the Stage-2 facet retrofit, s76 — `Status: Done`; demo target = Fastenal Thailand, **pitch = asset-ontology-triggered governed sourcing**, NOT the commoditized "governed"/"cross-vertical" claims). Each record is in `docs/plans/done/`; the s168→s193 retrospectives these bullets used to carry are rotated to `docs/status-archive/`.
- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13; verdict **continue-with-adjustments**. Runs 1 (energy, s93) + 2 (supply-chain, s94) both COMPLETE, all S-checks PASS against pre-committed oracles, no R-PS trigger fired; C-1..C-3 CONFIRMED → **no open partner-sim debt**. ADR-011's audit stays gated on a REAL partner conversation (R3: SYNTHETIC provenance INFORMS but never TRIGGERS it). Full record: `docs/adr/0020-*.md` + the gitignored run packages under `docs/research/private/`.
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm — **not yet drafted**, and it needs a fresh ADR number. _[The old "≥ ADR-014" floor recorded here was **moot** — see the Active TODO below, corrected s141: ADRs now run past 0032 and `0014-WITHDRAWN.md` exists. Kept as one pointer rather than two divergent copies.]_
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **The autonomy fork — Stop-hook misfires: CLOSED s167.** Resolved by **option A′** (Cray, typed) and shipped the same session — the `dispatch` verdict is a **suggestion, not an order** (#870/#871). Final ledger: **14 misfires / 0 valid fires**. **The whole argument is settled history in `docs/plans/done/0092-stop-hook-dispatch-arm-demotion-to-suggestion.md` — do not restate it here.** Live remainder: only **option (e)** (flip the classifier backend from local Ollama `gpt-oss:20b` to Sonnet), **deferred**, its API-key/org fail-closed probe unrun.

## Active TODOs

- [ ] **🆕 PLAN-0112 — the visitor case that becomes a governed run (Tab I→Tab H): `Draft`; seven SDs RULED, Steps 1/3/4/5 EXECUTED, PLAN-0112 AC-1…AC-6 CLOSED (s243–s245).** Remaining: **Step 6** (AC-7, AC-8) and **Step 7** (AC-9 + live evidence — host-state; Cray typed an ADVANCE go). ⚠️ **Unmeasured:** WHICH of two runs the ฿ report names when both approve one case. _[Trimmed s245 from 2,403 chars, `was an error`: held at full length on the claim it carried G-13/14/15 in prose existing nowhere else — measured FALSE; the PLAN defines all three and holds G-13's four-site correction. Prerequisite DISCHARGED.]_ `docs/plans/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md`
- [ ] **🆕 ADR-0035 — L1 re-read a SECOND time, and OQ-7 ruled, both Cray-typed s242.** L1's intent moves from *"one gate, no app code"* to *"one gate at the edge; app code may READ the gate's verdict for provenance, never perform gating itself"*, which unblocks phase-2 identity **capture** on the published demo surface while leaving **validation** pilot-era. **OQ-7 RULED (b)**: when the edge identity is absent, the app proceeds and **stamps the absence** — never fabricates a principal, never claims provenance by omission. ⚠️ **Two costs Cray accepted, recorded so neither is rediscovered as a surprise:** the demo survives dashboard drift, **and runs stay unattributed until someone reads the stamps — nothing alerts on it**; and the concrete stamp shape is deliberately NOT fixed in the ADR — it is the PLAN-0112 identity-capture AC's to specify. **Read the ADR, never a restatement:** `docs/adr/0035-hosting-and-exposure-model.md` (§LOCKED L1 · §OQ-7 · the s242 amendment-pass note).
- [ ] **🆕 The three live items the rotated s240 block carried — carried here so the rotation ledger's claim is true, not merely stated.** Measured at s240, none resolved since: (i) the **font-size decision still gates re-measuring every geometry number in the beat-4 mockup**; (ii) the **run-list backlog badge on the host is still unmeasured** — a host-state read, so it needs its own typed §8 go; (iii) the **three Advisory-proposal candidates are still unnamed**, so the gate panel still reads as unfinished. The full s240 narrative is at `docs/status-archive/2026-h1d-current-focus.md`.
- [ ] **🆕 The Tier-0 auto-memory store is a git repo that DRIFTS — snapshotted s242, recorded here because nothing tracked carried it.** The private store at `~/.claude/projects/.../memory/` has its own git with **no remote**, and nothing auto-commits it: at s242 it tracked **91 files while 163 sat on disk** — 73 memories had never been committed at all, so a wrong deletion during a consolidation pass would have been **unrecoverable**. Now snapshotted (164 tracked, tree clean; the safety net was verified by the pair *witness resolves at HEAD* **and** *fails at HEAD~1*). ⚠️ **A snapshot guards against a wrong deletion, NOT against disk loss — there is still no remote.** The `MEMORY.md` consolidation pass this unblocks is owed and deliberately not done here.
- [ ] **🆕 PLAN-0110 SD-E is REVERSED (Cray, typed, s242) and its commissioned follow-on is PLAN-0112 — fully RULED s243. NARROWED s243 to what PLAN-0112 does not carry.** The original ruling stands as history and is **NOT** edited — `done/0110` ruled **(d) "accept and re-scope the promise; build nothing"** and named server-side firing as *"the NAMED follow-on build"*. ⚠️ **Two consequences fall out the moment the build lands, and no AC owns either:** `/runs` filtering is client-side only *because* the population is pinned at two, and the Monitor "all" filter has no cap — SD-6(b) rules a bounded default for Tab H, which is a **different surface**. ✅ **SEQUENCING (Cray, typed) was "execution follows PLAN-0107 AC-10" — AC-10 CLOSED s242, so that constraint is spent.** _[s243, `superseded by new info`: two things this row used to assert are dead — that a new PLAN was still owed through a drafter dispatch (PLAN-0112 exists, is merged, and is fully ruled), and that no PLAN carried the `run_procedure_endpoint` auth-asymmetry as a prerequisite (PLAN-0112 Step 1 carries it, hard-ordered first). The three-part break and option (b)'s three riders are trimmed per R2's pointer cap — they were restatements of `done/0110` §SD-E and of `operate_seed.py`'s module docstring, both still tracked and now also carried by PLAN-0112.]_ **Read the archived PLAN, never a restatement:** `docs/plans/done/0110-fleet-demo-run-markers-filter-and-deploy-reset.md` (§SD-E · §Out of Scope).
- [ ] **🆕 The four s235 audit findings ADR-0038 did NOT absorb — REHOMED s235 out of a gitignored handoff into `docs/logs/2026-08-17-s235-audit-findings-outside-adr-0038.md`.** The **retrieval-reliability ranking** · **"pruning never reclaims storage"** (so never argue a rotation on disk grounds) · **`docker build` in CI, rated YES and owned by no PLAN** · **the 11-class vacuity taxonomy**. 🔴 **One live obligation in there: ADR-0038's three-strike counter has NO OWNER** — three items sit at two firings and no artifact records a count. PLAN-0108 is the natural owner and does not claim it. _[s241, two labels. `was an error (naming only)`: **"ADR-0037 SD-1" does not exist** — the genuinely-unruled item is the **D2.1 authorship fork** (`0037:229-249`), still open. `superseded by new info`: the counter has DRIFTED — the s235 log names **three** items at two firings while **ADR-0038's own D4 names only TWO** (`0038:441-447` W-1/W-2); `#0042` was added by the s235 audit and D4 was never amended.]_
- [ ] **🆕 PLAN-0111 — the fleet close-out record that can hold a credit note (ใบลดหนี้): `Draft`, and all six SDs RULED in the same session** (Cray, typed 2026-08-19, [#1227](https://github.com/CrayJThiemsert/vero-lite/pull/1227)). **Cray ratified the SDs, not the PLAN; nothing gates execution.** 🔴 **SD-E (partial credits may coexist; over-credit refused 422) FORCES SD-A to (b), a separate `repair_case_credit_note` table** — a latest-per-kind row would re-arm the replacement trap one level down. ⚠️ **AV-1 is owed before Step 4, not before merge:** what Express/accounting reconciles a ใบลดหนี้ against is the one thing this repo cannot answer, and SD-C is provisional on it. The three code-verified obligations the rulings created (`_FK_CHILD_MODELS`, the `load_monthly_export` union, the AV-2 prohibition) are in the s240 Current Focus block above and in the PLAN. **Read the PLAN, never a restatement:** `docs/plans/0111-fleet-closeout-credit-note-record.md`.
- [ ] **PLAN-0107 — oracle-coverage hardening: `Draft`, 15 ACs. ✅ Phase A CLOSED 6/6 s236 ([#1204](https://github.com/CrayJThiemsert/vero-lite/pull/1204)); ✅ Phase B's AC-7 + AC-8 CLOSED s236 (#1206 `7a37c6d`, #1207 `5aedaf2`) ✅ AC-11 CLOSED s240 ([#1226](https://github.com/CrayJThiemsert/vero-lite/pull/1226)) and ✅ **AC-10 CLOSED s242** ([#1238](https://github.com/CrayJThiemsert/vero-lite/pull/1238)) — gold is now graded against the ENGINE for all eleven expressible cases; the inexpressibility register shipped **EMPTY** because all eleven were measured to round-trip BEFORE the test was written (`VERDICT=ALL_ELEVEN_REPRODUCE`), so **no gold value was edited** and no finding is owed. Tally **10/5**. Remaining: Phase B's AC-9 (BLOCKED on a Cray ruling), and Phase C — nothing else gates them.** CI now runs four oracles it lacked (**measured +74 s, no new dependency**). ⚠️ **Read each AC and its `Reviewer amendment` blocks as authoritative; the §Steps prose is narrative — three measured divergences in Phase A alone.** _[s241 — every defect this row named is now FIXED OR RECORDED IN THE PLAN ([#1232](https://github.com/CrayJThiemsert/vero-lite/pull/1232)): AC-11's checkbox ticked, AC-10's scope corrected to **nl-01…nl-11 (eleven)**, the expired 2-case-seed argument dropped in both places, three drifted citations re-anchored by symbol, and 🔴 **AC-9's Step-7 probe recorded UNRUNNABLE in a `Reviewer amendment` — three defects, three options laid out neutrally, BLOCKED pending a Cray ruling.** The PLAN carries the detail; do not restate it here.]_ **Read the PLAN, never a restatement:** `docs/plans/0107-oracle-coverage-hardening.md` (§Phase A closing evidence · §Acceptance Criteria · §AC-9's Reviewer amendment).
- [ ] **🆕 PLAN-0107's citation population is only PARTIALLY verified — recorded here because nothing else carries it.** The s241 sweep was exhaustive for **`verticals/fleet_maintenance/operate_seed.py` only** (three drifted cites re-anchored by symbol); asked directly, the drafter stated plainly it did **not** systematically check the rest, and named the at-risk set: AC-8's before-state cites into `tests/api/conftest.py`, the Phase A cites into `.github/workflows/ci.yml` (#1204 added ~5 steps to that file), and a tail into files no closed AC touched. 🔴 **The framing matters more than the count: most are BEFORE-STATE cites — historical by design, "wrong" only the way an archive is wrong** — so the likely treatment is **labelling them before-state, not re-anchoring them**, which makes this an **AC-authoring convention question (PLAN-0108's subject)**, not a repair job. **Recommendation on record; NOT ruled.**
- [ ] **🆕 PLAN-0108 — AC-authoring + pre-close convention hardening: `Draft`, UNRATIFIED.** The weak-oracle half of the same audit. 🔴 **Still gated, unchanged: SD-1 is NOT ruled — ROUTED to Cowork (`0108:209`; until it returns and is ratified, §8 as written governs); three of six ACs close only on Cray's PR-merge judge read; Step 1 is G2-gated for Code (`0108:240-242`).** _[s241: the two ACs both labelled `AC-5` are CORRECTED ([#1233](https://github.com/CrayJThiemsert/vero-lite/pull/1233)) — the `[evidence]` retro-classification AC is now **AC-6**; the `[check]` staleness-guard AC keeps **AC-5** because ADR-0038's OQ-5 attaches to it. ⚠️ **UNDECIDED, and live only here until ruled — the labels now read `[1, 5, 2, 3, 4, 6]`: unique but NOT ascending.** The AC-5 block is authored adjacent to AC-1's `measure` section and STATUS anchors it by line, so ordering them means physically moving the block — layout against a live citation, **Cray's call**; hook #19 checks collisions, not ordering, so nothing forces it.]_ Owns ADR-0038's **OQ-5** — the staleness-guard obligation attaches to the PLAN template, not to a build task. **Read the PLAN, never a restatement:** `docs/plans/0108-ac-authoring-and-preclose-convention-hardening.md`.
- [ ] **🆕 The two s241 pre-commit guards — BOTH ARE FLOORS, NOT CEILINGS; their limits are recorded here so neither is read as stronger than it is.** `tools/check_retired_claims.py` (hook #18; convention `docs/conventions/retired-claims.md`) — a claim declared retired must not survive anywhere live; it **cannot catch a reworded stale copy** (exact text only) and **cannot know a claim SHOULD have been retired**, so declaring stays a human act. `tools/check_ac_consistency.py` (hook #19) — no duplicate AC labels in an active PLAN, and a closure STATUS claims must be ticked in the PLAN; it **cannot read a phase-level claim** (*"Phase A CLOSED 6/6"* names no AC — three such claims exist), covers **active** PLANs only for duplicates, and cannot know whether an AC *should* be closed. ⚠️ Recorded so it is not rediscovered: `docs/plans/done/0042-at2-managerial-build.md` carries a duplicate `AC-13`, **deliberately out of scope** as frozen history.
- [ ] **🆕 PLAN-0109 (Ask over repair cases) carries THREE factual defects in its RULED content — measured s241, all zero-tracked-hits. Fix all three BEFORE Step 5; they are `docs/plans/` writes, so G2-gated for Code and owed to a drafter dispatch.** 🔴 **(i) AC-11 would write a FALSE sentence into the compliance record by deleting a TRUE one.** It orders the *"does not reach case text"* sentences deleted from `services/db/repair_case_retention.py:7-9` and `docs/compliance/ropa-change-statement-fleet.md:124-125` and replaced with a claim that case `description` / quote `vendor` / accepted-quote `reason` reach the `/query` translate + phrase prompts **and the D6 prompt log**. Measured: `services/engine/llm/prompt_log.py:26` `FIELDS` is a **CLOSED** 7-key set asserted at `:113`, and `services/api/routers/query.py:59` passes `text=request.question` only — so case text reaches the **phrase prompt only** (`nl_query.py:1220-1221`), **not** the translate prompt (schema-only, `:382-398`) and **not** the on-disk log. The deleted sentences stay TRUE after PLAN-0109 ships, and AC-11's grep pass read (*zero occurrences*) **cannot fail** — it is satisfied by deleting a truth. 🔴 **(ii) `tenant_id` is missing from the exclusion enumeration and reddens AC-3 on the first run** — a live column on all three ruled types via `TenantKeyMixin` (`services/db/tenant.py:71`), and it may **NOT** be moved into the YAML (`tests/services/engine/test_tenant_key_not_in_nl_query.py:70` reddens instead). **(iii)** minor: **AC-3(iii) contradicts AC-10 on `seq`** — neither `RepairCase` nor `RepairCaseQuote` has a `seq` column, so a flat exclusion entry is stale for two of three types. **Read the PLAN, never a restatement:** `docs/plans/0109-*.md`.
- [ ] **TWO unruled silent drops in the NL engine's aggregate paths — REHOMED s235 to the code.** (i) the **`started_week` filter is ignored entirely** (found s228) and (ii) **`group_by` never reaches `AggregateResult`**, so *"average duration per procedure"* validates, executes and silently returns **one ungrouped number** (found s232). Both live at `_aggregate_duration` / `_aggregate_benefit`; ⚠️ **the count path DOES pass `groups`**, so (ii) is a two-site gap in an otherwise-correct design, not a missing feature. **No test covers either.** **Read the docstring, never a restatement:** `services/engine/run_query.py::_aggregate_duration`. **Same two dispositions each, NEITHER ruled: (a) refuse, or (b) make it work.**
- [ ] **`nl-03`'s `SQL_EXPECT` is UNDER-SPECIFIED — RULED (Cray, typed, s226): RECORD it, do NOT change the token. REHOMED s235 to the module that defines it.** Its list holds two ids where `gold.yaml` lists three. 🔴 **A different defect class from the nl-02/nl-05 tokens Step 1 repaired:** `score_sql` matches a SUBSET, so the oracle is **WEAKER than it should be, not WRONG**. Adding the token would make the benchmark STRICTER and **break comparability with earlier runs** — a measurement decision, not a typo fix. **Read the note, never a restatement:** `benchmarks/nl_query_feasibility/text_to_sql.py` (above `SQL_EXPECT`).
- [ ] **The apex domain leaks in ONE archived file — UNRULED, not urgent; REHOMED s235 to the guard that would have to widen.** 🔴 **RE-PRICED s232 — "widen the guard" is NOT a one-file flip:** widening the scan to `docs/plans/` reddens **FOUR** files, so the option is a flip **plus three deliberate allowlist additions**. ⚠️ **The guard's path was recorded WRONG and is corrected s235** — it is `tests/deploy/test_published_compose.py::test_no_unknown_domain_appears_in_the_deploy_docs`, not `test_published_profiles.py`. **Read its docstring, never a restatement. Reference the carrier BY PATH only — the domain is not named.**
- [ ] **The ฿ realized-vs-projected join — REHOMED s235 to `services/db/run_analytics.py::benefit_rollup`,** which is the primitive the circulating framing wrongly claimed could be reused. 🔴 **It cannot** — it yields no per-run figure at all, so the join needs a NEW per-run aggregation; copy `run_duration_totals`. ✅ **No migration needed.** ⚠️ Re-priced **~150–250 lines across 6–7 files, ONE PR** — the *"~40 lines"* figure was checked and is WRONG. Three TEST-PINNED constraints live in that docstring. **Read it, never a restatement.** Lands on Tab J, which fleet publishes.
- [ ] **Demo-key rotation cadence — CRAY'S, posture not code.** Fleet's README documents how to **generate** a persona key pair but says nothing about **when to rotate**. Measured s225: `git grep -i -e rotate -e rotation` under `deploy/published/oct-fleet-maintenance/` returns **zero** matches. The keys are served to the browser by ruling, so they are **public the moment fleet is reachable** — which makes the cadence a real posture question rather than a nicety. No code change is implied; the answer is Cray's.
- [ ] **ADR-0036 OQ-2 — the aggregate in-flight LLM posture — remains OPEN.** ✅ PLAN-0103 Step 9's MS-S1 headroom is MEASURED s221 (`docs/logs/2026-08-10-oct-energy-migration-phase2-and-step9-headroom.md`): RAM and CPU do not constrain a second or third published system. ⚠️ **OQ-2 does NOT follow from it** — the constraint on a second *assisted* system is the resident model and concurrent in-flight calls, not container footprint, and one term (Postgres idle) is declared unmeasured rather than folded silently into the total. **Read the ADR's own OQ-2, never a restatement.** _[s235: this row's other three sub-items are DISCHARGED — the edge cache-purge cost is now in PLAN-0100's §Post-archival amendment, ADR-0037 D4/OQ-2 closed s232, and the one-pager has its own row.]_
- [ ] **Three measured, unscheduled items — REHOMED s235 to `docs/logs/2026-08-17-s235-unscheduled-measured-items.md`.** (1) **The public one-pager v2** — DESIGN-READY, a WRITE job; destination RULED (Cray, typed, s226) = gitignored `docs/strategy/private/`. (2) **The assembly-cost axis** — Cray's s197 ruling is an ORDERING (measure, then ADR); the banked series **1:1.8 → 1:6 → 1:1.1** is spiky, not falling, and 🔴 **its METHOD is recorded nowhere**, so a tripwire built today emits an incomparable number. (3) **Seam-scoped mutation-testing CI** — still unscopeable: **2 pytest markers, no `scenario` marker**, and CI runs bare `pytest -q`, so §8's binding scenario rule is **mechanically unenforced**. ✅ XS prerequisite (marker + filename normalise) has **ZERO** rename blast radius. **Read the log, never a restatement.**
- [ ] **Landing-layer PLAN — CLOSED s226 as SUPERSEDED. NOT work to do; this row exists so nobody schedules it again.** PLAN-0103 Step 8 consumed the repo-side half (AC-9 ticked), and ADR-0036 D1/D2 place the landing surface, ingress map and Access policies **outside this repo** — a vero-lite file enumerating published systems is guard-rejected as a *shadow ingress map* (`tests/deploy/test_published_profiles.py`). Cray ruled s221 (typed): **no portal repo.** 🔴 **The remainder is CRAY'S DASHBOARD WORK — nothing for Code, no dispatch owed.** _[Trimmed s233 per R2 s141; measurement narrative in `docs/status-archive/`.]_
- [ ] **PLAN-0100's residuals outlive the PLAN** (COMPLETE 13/13, ARCHIVED s216; the demo is LIVE, REDEPLOYABLE and DRIVEN). ✅ **REHOMED s235 under the R2 carve-out** — all three residuals (**D-4 fully discharged** by PLAN-0104 · **no cache-purge step and no versioned font URLs**, a purge needing a new secret + host-state · **no `OLLAMA_KEEP_ALIVE` pin**, so all three profiles inherit the 30m code default) now live in the PLAN's own **§Post-archival amendment**, each re-verified at source rather than copied. **Read it, never a restatement:** `docs/plans/done/0100-exposure-published-demo-surface.md` (§Post-archival amendment · §"Step 11 closure verdict" · §"Defects the live run found" for D-1..D-5).
- [ ] **CI has NO JS RUNTIME — s234 measured the cost; NARROWED s235, NOT closed.** Tab I clipped **305px** of itself on the **live** system while **4,113 tests were green**; a human found it. **No oracle here can see a clip.** ⚠️ **PLAN-0107 AC-1 adds `node --check`, a SYNTAX gate — a clip is a LAYOUT fact, so AC-1 narrows this row and does not close it.** 🔴 **The guard shipped with the fix does not close it either, and says so in its own docstring** — `test_case_wrap_declares_the_scroll_contract` reads the stylesheet, so it catches a deletion and **cannot catch a re-clip by other means**. An oracle gap, not a missing test. Closing it is a JS-runtime-in-CI project — nothing drafted. Evidence: `docs/logs/2026-08-16-plan0103-step10-fleet-bring-up.md` §Addendum.
- [ ] **PLAN-0096 partner round-2 — ANSWERED s189; nothing blocking remains.** **Open, NON-blocking: cost-center (ศูนย์ต้นทุน) granularity — per truck or per company?** Ship the column, fill the rule when it lands. (A5 stays **parked** — no real Wialon export exists yet.) _[s226: the per-answer ledger A1–A7 is ROTATED to `docs/status-archive/2026-h1-status.md`; `docs/plans/done/0096-fleet-flow-completion-phase1.md` holds the detail.]_
- [ ] **The AT-2 extraction — only the F-FACTORY half remains, owned by PLAN-0076 T1.** The criterion-vocabulary half SHIPPED as PLAN-0087 (ARCHIVED, #840/#841); SD-1 = (a) keeps the procedure-aware `ExecutorFactory` half with PLAN-0076 T1, guard `test_at2_extraction_obligation_is_owned` ARMED. Full detail: `docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` + `docs/plans/0076-*.md` §A.
- [ ] **PLAN-0075 follow-ons — homed by PLAN-0076 (`Status: Tracking`, #752).** T1's criterion-vocabulary half shipped as PLAN-0087; the procedure-aware-`ExecutorFactory` half (F-FACTORY) stays OPEN, and T2's F-PIN remainder closed s143 (#784) while **F-PIN itself stays OPEN** — so PLAN-0076 does **not** archive and its AC-6 presence guard stays ARMED. **Read the PLAN, never a restatement:** `docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` §A. ⚠️ Its six ACs and four Steps are **stub-level — none directs a build**, so nothing here is Code-executable. _[Trimmed s233 per R2 s141.]_
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2), open ONLY for the O-2 residue.** Every other leg is DONE and archived. The residue: procurement's `intake` migrated only PARTIALLY — the derived fields already moved to declared `transform` (PLAN-0078 PR-1 #762, AC-2 ticked), leaving **only the cardinality-changing `candidate_quotes` nest**, explicitly Out-of-Scope there. **Read the archived PLANs, never a restatement:** `docs/plans/done/0062-per-vertical-seed-migration.md` §SD-C (the co-exist decision + its STOP-and-surface tripwire) · `done/0078-*.md` §L-3. _[Trimmed s233 per R2 s141.]_
- [ ] **Bounded/incremental chain verification (PLAN-0063 SD-4 follow-up, s118).** `GET /audit/verify` walks the WHOLE chain O(n) on demand — accepted at pilot scale. Future work = a checkpointed head / verify-since-anchor design; anchor storage ≈ external anchoring — **do not build without re-reading the tripwire** in `docs/plans/done/0063-audit-chain-verification-surface.md` + the `services/api/routers/audit.py` module docstring (SD-4). *(#688/#690)*
- [ ] **Rock 4 — s84 deep research DELIVERED → O-sequence locked.** Cray locked **O-1 → O-3 → O-2 → O-4**. **O-1** (Box-4 ฿ pitch) **DONE** · **O-3 = ADR-0025 Accepted** · **O-4 = PARK** (agent-interop; `docs/adr/0032-*.md` D4 — option-only, un-park = a counterparty's *written* pull). **Remaining: O-2 only** (economic-impact facet + Q3 data-binding = Rock 3). Full detail: `docs/adr/0025-at2-managerial-layer.md` (O-sequence + Box-3 fit + the **evidence-asymmetry** finding rehomed s142). *(s84 Cray ask)*
- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten. **Full table (all six rows + their triggers + where each lands): `docs/plans/done/0005-oct-engine-runtime-layer.md` §8.1** — which itself instructs this STATUS entry to be a pointer. *(per Cray note 2026-05-21)*
- [ ] **PLAN-004 Phase C — OPTIONAL POLISH (forward-declared; "may never land"):** HTML/markdown handoff dashboard under `docs/` + references-graph (mermaid dispatch chains) + `render_transcript.py` unified session export (PLAN-0004 §"Phase C"). *(Phase A + B both COMPLETE — session 35; the prior TODO's validator **warning-swallow bug was FIXED #312**, s58.)* _[s226: the three never-formally-scoped sub-ideas are ROTATED to `docs/status-archive/2026-h1-status.md` — fold them in only if Phase C ever lands.]_
- [ ] **Custom Postgres image with extensions (pgvector / AGE / pg_trgm) — MEASURED DORMANT s226. Recommendation on record: NO ACTION.** Grepping `services/` for `pgvector|pg_trgm|trgm|Apache AGE|embedding|CREATE EXTENSION` returns **exactly one hit, and it is a false positive** — the English word "embedding" in a prose comment at `services/engine/llm/prompt.py:43`. **Nothing in the codebase needs these extensions**, and the documented trigger ("semantic query / graph features prioritised") points the **opposite** way from where the work actually went: NL query took the **relational-aggregation** route (PLAN-0104). ⚠️ **The price has RISEN since this row was written:** ADR-0037 grants fleet its **own** Postgres in the published deployment, so swapping the base image is **no longer a one-line compose edit** — it touches **three published profiles and their 68-test guard suite**. **Revisit only when a consumer feature defines which extensions are actually needed**; still needs a fresh ADR number + a PLAN, neither drafted. *[Corrected s141: **PLAN-002 does not exist** and the old "≥ ADR-014" floor is **moot** — ADRs now run past 0032 and `0014-WITHDRAWN.md` exists.]* Context: `docs/adr/0013-autonomy-axis-relocation.md` + `docs/plans/done/0005-*.md`.
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] **CLAUDE.md follow-up extraction pass (s181 option b): new Cowork dispatch; target < 20 KB. PARKED s183 by Cray — the dispatch stays UNSENT until two things are settled, and s183/s188 grounded both.** (1) **The unit of `< 20 KB` is load-bearing and unpinned** (KiB vs decimal); Cray was asked and declined to rule for now. (2) **The named candidates cannot reach either target:** at `CLAUDE.md`'s s188 size of **22,424 B** the cut needed is **1,944 B** (20 KiB) / **2,424 B** (decimal), where the five candidates measure **~930–1,000 B** combined and the genuinely large blocks are **not on the list**. Sending it as written would repeat the s181 failure of an arithmetically unreachable target. 🔴 **The real parked decision: the target and the constitution are pulling in opposite directions** — the growth is Cray-ratified binding-rule substance, not padding. Materials: `.claude/handoffs/session-181/` (gitignored). _[s226: the per-candidate enumeration and the full s183/s188 byte arithmetic are ROTATED to `docs/status-archive/2026-h1-status.md`.]_
- [ ] **PLAN-0102's two residues outlive the PLAN** (retire L1 loop-detect — COMPLETE 11/11, ARCHIVED s217, #1096; L1 gone from all four hooks, L2/L3/L4 intact and asserted so). ✅ **REHOMED s235 under the R2 carve-out** — the **callerless `observe()`** (kept deliberately; deleting it pulls a refactor into every surviving L2/L3/L4 increment) and the **forwards-call-graph method debt** (a linter cannot close it — `ruff` flags a dead import, never a dead private function) now live in the PLAN's own **§Post-archival amendment**, both re-verified at source. **Read it, never a restatement:** `docs/plans/done/0102-retire-l1-loop-detect.md`.
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
