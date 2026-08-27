---
last_updated: 2026-08-27T12:06:36+07:00
session: 258
current_batch: "s258 — ONE PR merged (#1307): PLAN-0107 COMPLETE 15/15 and ARCHIVED. AC-9 closed on Cray's ruled option (b) — a golden-trace producer plus the scoring path that makes the corpus an oracle."
current_actor: code
blocked_on: "Nothing blocking. Main green at `d78eebe`; 0 open PRs. Owed: the `check_ac_consistency.py` backwards-lookback gap · PLAN-0116's three SDs · the 1.8 GB worktree sweep · PLAN-0109 · PLAN-0108."
next_action: "Cray's call: fix the AC-ledger guard's backwards-lookback blind spot, or start PLAN-0109 (highest demo value, no migration needed) — its drafter round must repair FOUR ruled defects, not the three STATUS names."
head_commit: 1904caa
recent_commits: [d78eebe, 1904caa, 1993bda, b5fd234, 61c8a80, 6bddc82, dd4228f, 6882b8b, 13d11b7, a5da51d]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 258, 2026-08-27 (`1904caa` → `d78eebe`) — ONE PR merged
> ([#1307](https://github.com/CrayJThiemsert/vero-lite/pull/1307)), 0 open, tree
> clean. **PLAN-0107 is COMPLETE 15/15 and ARCHIVED** — AC-9 unblocked by
> Cray's typed ruling for **option (b)**, and AC-12/13/14/15 ticked only after
> each AC's own pass read was re-run.**
>
> 🔴 **AC-9's literal text could not be executed without manufacturing the
> defect the PLAN exists to remove.** Its three s241 defects were re-verified
> first: the named seam (`demo_events.py:62`) is a **delegation**; the named
> oracle reads static JSON and cannot observe the mutation; and the producer the
> AC presumes **never existed** — `golden_trace` across every `.py` matched one
> file, the consuming test. Dropping two JSON fixtures in would have added ~8
> assertions pinning none of it: an ADR-0038 **class-C1** guard inside the PLAN
> that exists to eliminate class-C1 guards.
>
> ✅ **Option (b) shipped as producer PLUS scoring path — the second half is the
> load-bearing one.** `tools/golden_trace/` recomputes each trace's
> `expected_envelope` through the real `_compose_llm_record`; **invariant 5**
> then scores the system's LIVE composition against the recorded value.
> Invariants 1–4 compare each file to itself — they redden on a malformed
> fixture and never on a composition regression (CLAUDE.md §8). `created_at` is
> the **sole** exclusion, and that is measured: composing twice differs in
> **1 of 16** keys.
>
> ⚠️ **What the two new traces do NOT claim, recorded so nobody over-reads
> them.** Trace 04 does not pin the `below` comparison — that is
> `crosses_threshold`, already covered by `test_recommender_config.py` and
> `test_demo_events.py` **with a control**, both predating this PLAN. Trace 05
> does not pin the anchor filter's `event_type` clause: **no non-`reading` event
> anywhere carries a `measured_value`**, so the clause is redundant with the
> `isinstance` beside it and no test can redden on its removal. Making it matter
> needs an event that does not exist.
>
> 🔴 **The AC ledger had drifted and its own guard could not see it.**
> AC-12/13/14 landed in #1305 but were never ticked, while this file claimed
> *Phase C CLOSED s257* — and `tools/check_ac_consistency.py` reported
> **clean**. It searches `AC-N` **backwards** from `CLOSED`, and the row wrote
> `CLOSED s257 — AC-12, …` with the refs **after**, outside the lookback.
> **The guard gap is NOT fixed** — mechanism read from source, not yet probed.
>
> 🔴 **AC-12's shape is the finding, not its verdict:** its own command returns
> `4023 passed, 486 skipped` and **exit 1** — pytest reports nothing failed and
> the process fails anyway. That is exactly why the pre-#1305 state was
> invisible: a collapsed DB layer looked identical to a green run.

> **Session 257, 2026-08-27 (`6bddc82` → `1993bda`) — THREE PRs merged
> ([#1303](https://github.com/CrayJThiemsert/vero-lite/pull/1303),
> [#1304](https://github.com/CrayJThiemsert/vero-lite/pull/1304),
> [#1305](https://github.com/CrayJThiemsert/vero-lite/pull/1305)), 0 open, tree
> clean. **PLAN-0107 Phase C closes AC-12/13/14/15 — the PLAN goes 10/15 →
> 14/15**; only AC-9 remains, BLOCKED on a Cray ruling (3 options written).**
>
> 🔴 **Three gates that READ as protection started providing it.** **AC-13**
> deleted a coverage threshold from `pyproject.toml` that measured nothing — no
> `addopts` adds `--cov`, CI is a bare `pytest -q`; deleted, not armed (Cray's
> typed ruling), and the same "coverage ≥ 70%" certification was struck from
> `.github/PULL_REQUEST_TEMPLATE.md`, surfaced by Step 11's required grep
> rather than silently edited. **AC-14** retired
> `test_every_edited_asset_got_a_cache_bust` — it froze per-file minima over **9
> of 21 JS and 0 of 4 CSS files**, so it passed while `views.css` was unguarded
> — for `tools/ci/cache_bust_diff_check.py` + `fetch-depth: 2`: **relational,
> not absolute** — if the bytes changed, the token must have changed, driven
> RED/GREEN/ERROR through **real git**. **AC-15**: the step costs **under 1s of
> a 606s job**; recorded, not a gate.
>
> 🔴 **AC-12's probe is the headline.** A session-finish, CI-only floor of
> **400** under the executed DB-test count — baseline **475** (`CI=1`, real
> Postgres, 4477 collected), ~16% margin because it catches a COLLAPSE, not
> drift. Under the dead-port mutation the check **exits 1 while pytest's own
> summary reports `4005 passed, 484 skipped`** — 484 skips against a normal 8.
> It also settled what everything hung on: that `session.exitstatus = 1` in
> `pytest_sessionfinish` reaches the process exit code — **none of the seven
> unit tests could establish it**.
>
> 🔴 **The s256 walk residue is TWO RUNS, not two cases** (#1303) — re-measured
> LIVE by three READ-ONLY probes, each under its own typed Cray go recorded
> before it ran. Both cases **ABSENT** (control-backed); run
> `@41bb78353e7c4138` is still `waiting_human` at a resolvable `approve` gate.
> STATUS's own row was wrong **twice** (corrected below); `audit_log` unchanged
> at **64 rows**, so **how the cases went away is measured but unexplained**.
>
> ✅ **And if a visitor clicks that orphaned gate, nothing breaks** (#1304).
> Answered offline first: a controlled grep sweep found **ZERO** `repair_case`
> refs on the whole resolve path — `runs.py`, `action_step.py`, all 74 modules
> of `services/engine/` — against a control where the same grep finds 5 modules
> under `services/db/` and 4 under `services/api/`; and those six files are
> **byte-identical** between `dd4228f`, what the deployed image was built from,
> and `6bddc82`. `tests/api/test_orphan_case_gate_resolve_scenario.py` then
> drives the real producer (HTTP `/api/cases` + quotes + accepted-quote) into
> the real `resolve_gated_step`, erasing the case in between through the real
> `delete_case` seam, with a positive control. Cray chose to **simulate rather
> than click live**, so nothing touched the live audit chain. **3/3 probes
> WITNESSED**, `PROBE-COVERAGE: COMPLETE`, 0 gaps, tree byte-identical after.
>
> **Evidence.** Offline gate green at CI scope — **4481 passed, 8 skipped, 0
> failed**; `mypy --strict services/ verticals/` clean on 201 files; bare `ruff
> check .` + `ruff format --check .` clean; 20 pre-commit hooks; CI green at
> every pinned sha. **Not in a PR:** all **116** Tier-0 memories with no repo
> home were audited — **ZERO safe deletions**, and **no hook enforces the
> `MEMORY.md` < 140 target**. Cray **PARKED** it.

> **Session 256, 2026-08-26 (`f8aeba0` → `6882b8b`) — PLAN-0114 Steps 2–5.
> `POST /runs/{run_id}/continue` ships; the dead-end tripwire becomes its own
> closure. **PLAN-0114 is COMPLETE 6/6 and archived to `done/`** —
> [#1298](https://github.com/CrayJThiemsert/vero-lite/pull/1298) merged `13d11b7`.**
>
> 🔴 **AC-1's premise was measured FALSE, so the ruling was re-put.** `fulfill` is
> `autonomy: gated` too, so acknowledging `approve` parks the run again — it takes
> **TWO**, not one. That changed what Step 3's UI rested on: **SD-4 RULED (B)** —
> one button walks the empty gates, halting at the first gate holding a real
> proposal. API, chokepoint and audit trail untouched; only the click count.
>
> 🔴 **A live-only gap the offline suite could not see.** The published ingress
> allowlist is **default-deny**, so the button would have **404'd at the Cloudflare
> edge** while every local test passed — caught by
> `test_ac6b_every_route_the_ui_references_is_classified`. ⚠️ The fix **admits a
> new write route to a published surface** (less privileged than the published
> `gate/resolve` — the chokepoint 409s any gate holding a proposal, so it can never
> approve) — flagged for Cray at the PR, not treated as mechanical.
>
> 🔴 **PLAN-0113 is merged but NOT live, and it must not ship alone** — its Step 3
> is what *creates* this dead end, so **deploy unit = 0113 + 0114 together**. The
> host is safe today by accident, not plan (0113 was never deployed, which is also
> why its AC-9 is archived CARRIED-OPEN). Read-only MS-S1 census under a typed go,
> plus the phased plan:
> [`docs/logs/2026-08-26-s256-…`](logs/2026-08-26-s256-ms-s1-readonly-deploy-census.md);
> the decision itself is a live Active TODO below.
>
> **Evidence.** Suite 4460 → **4466**, 0 failed; `mypy --strict` clean, 201 files;
> ruff + format clean. Two batteries through `tools/probe_battery/` (AC-2: 4
> WITNESSED + a declared-GREEN control; AC-4: both parity tests RED under a
> `_suspends` mutation, tree restored byte-identical). AC-5 verified in the
> preview; the acknowledgment proven on the **live** audit chain, one
> `run_continued_no_decision` row per gate, `GET /audit/verify` `intact: true`.
> Two of my own probes were defective; the driver caught both.
>
> **A parallel session (`vero-lite-d6`) — `sd-premortem`, three blind replays on
> `git archive ce7c003`, pass/fail pre-committed. v1 3/4 · v2 3/5 ·
> v3 3/5: the hypothesis FELL.** 🔴 A repeat of the **identical** dispatch then
> settled the open question: **variance dominates — 5 of 7 options flipped verdict
> on unchanged evidence.** One arithmetic result surfaced in both rounds and was
> called `REFUTED` (⇒ DEAD) once, "measured consequence" (⇒ ALIVE) the next.
> **Three layers, not two: citations stable · counts NOT stable · rollup
> unstable** — and neither count was wrong; they answered different unstated
> patterns. ⇒ **LLM emits claim + evidence,
> deterministic code rolls up the verdict.** **No PLAN opened; the proposal is not
> to open one on the original design.** Log
> [#1299](https://github.com/CrayJThiemsert/vero-lite/pull/1299), OPEN. Cray then
> split the sessions onto **separate worktrees** — nothing collided today, but
> because that session chose to wait, **not because anything prevented it**.
>
> **Checked, NOT a defect** — recorded so it is not re-derived as one. The battery
> lock's **stand-down scopes to the gate, not the Stop hook**: a `None` gate return
> falls through to `_classify` (`stop_continuation.py:531` → `:540`), which still
> runs. Not a defect **because `_classify` never reads the tree** (`:569`: *"can see
> neither disk state nor in-flight work"*) — that citation, not the verdict, is what
> stops the next reader. The lock protects **`goal.json` specifically**, not
> `.claude/state/` wholesale (`stop-chain.json` is there; `proceed` writes it).
> Remaining: a **documentation gap** — nowhere records that the battery-lock case
> was considered for the classifier arm.

> **Session 255, 2026-08-26 (head_commit `f0f60fd` → `2448f90`) — FOUR PRs
> MERGED ([#1293](https://github.com/CrayJThiemsert/vero-lite/pull/1293)–[#1296](https://github.com/CrayJThiemsert/vero-lite/pull/1296)),
> 0 open, CI green per-sha on every merge, tree clean. **PLAN-0115 is COMPLETE
> 10/10 and ARCHIVED — `tools/probe_battery/` ships, so the witnessed-RED
> discipline finally has an instrument instead of a `/tmp` script rebuilt wrong
> every session.** ADR-0038 C6's named D2 form-(c) enforcer now exists.**
>
> 🔴 **VX-1 is DISCHARGED — owed since PLAN-0021, never answered.** Measured
> live, twice: a non-blocking Stop-hook `systemMessage` **does** surface as
> `Stop says: …`, to the **user's UI only** — never into Claude's context. **Not
> a drop-in, though:** adopting it on the gate's warn arm breaks **PLAN-0069
> AC-3** parity, so it stays available and unadopted; Telegram remains D5's
> channel of record.
>
> 🔴 **The instrument found TWO defects in itself, both fixed in flight.** A
> **same-size mutation was masked by stale bytecode** (CPython validates a `.pyc`
> by *mtime-seconds + size*) and reported a false `GREEN` — the full local suite
> passed and **only CI reddened.** ⚠️ That hazard was measured at s247, fix
> included, and was **re-made inside the very tool meant to stop that.** And a
> probe mutating its own claim's file **shifted that claim's line**, so a real RED
> was rejected as MISFIRE — the right refusal on the wrong grounds.
>
> ✅ **21 assertions witnessed RED through the driver itself**, each with a
> control left GREEN under the same mutation; **four probes reported GREEN first
> and were REPAIRED, never recorded as witnessed** (§8: suspect the probe first).
> **Step 3 migrated 54 `drop_all` sites / 51 files** onto a bounded helper — the
> 67-minute hang class — with a **rule-not-roster** guard that walks the tree **on
> disk** and matches by **AST**. Full record: the PLAN's §Closeout.

_[Current-Focus rotation ledger — **CURRENT window only** (R2, Cray s250); earlier entries travel with their blocks into [`2026-h1d-current-focus.md`](status-archive/2026-h1d-current-focus.md), the full pre-trim ledger into [`2026-h1-status.md`](status-archive/2026-h1-status.md). Window = **255–258**. The **s255** reconcile rotated the **session-251** block; the **s256** reconcile rotated the **session-252** block; the **s257** reconcile rotated the **session-253** block. **THIS (s258) reconcile rotates the session-254 block**, holding the window at four (255–258) — on the **window rule alone, not a cap overage**. Its substance keeps tracked homes: PLAN-0115's four ruled SDs are in `docs/plans/done/0115-probe-battery-driver-and-verification-instrument-hardening.md`, and C6's promotion plus its legibility conjunct in `docs/adr/0038-advisory-lesson-promotion-three-strike-rule.md`. ✅ **The R6 both-directions byte check was PERFORMED at this reconcile, not deferred**: the slice was pinned by its first AND last line, checked for neighbour-bleed, checked absent from the target *before* the write, then verified **present-in-target and absent-from-source separately**, with a byte **delta** rather than a presence test (a presence-only check passes on a pre-existing copy). Measured: slice **2,671 B**, archive delta **+3,062 B**, STATUS **−3,268 B**. 🔴 **A correction the check produced:** the s257 handoff recorded this block as *"4,303 B — over"* the 4,096 B cap. Measuring it gives **2,671 B — inside**. That number was never in a tracked file; it travels into the archive with the block rather than being dropped silently. All four blocks in the current window are now measured under cap. The earlier ledger travel notes (s246/s247, s251) went into the archive with their blocks.]_


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
| 2026-08-27 | **s258 — ONE PR (#1307): PLAN-0107 COMPLETE 15/15 and ARCHIVED; AC-9 closed on Cray's ruled option (b).** 🔴 The golden corpus was **not an oracle** — invariants 1–4 compare each file to itself, so `tools/golden_trace/` plus a new **invariant 5** now score the system's LIVE composition against the recorded envelope (`created_at` the sole exclusion, measured 1 of 16 keys). 🔴 **AC-12/13/14 had landed unticked while STATUS claimed them closed, and `check_ac_consistency.py` reported clean** — it searches `AC-N` backwards from `CLOSED`. **That guard gap is NOT fixed.** | `d78eebe` / [#1307](https://github.com/CrayJThiemsert/vero-lite/pull/1307) / `docs/plans/done/0107-*.md` |
| 2026-08-27 | **s257 — THREE PRs (#1303–#1305): PLAN-0107 Phase C closes AC-12/13/14/15 — the PLAN goes 10/15 → 14/15; only AC-9 remains, BLOCKED on a Cray ruling.** 🔴 **Three "gates" that read as protection enforced nothing:** a `pyproject.toml` coverage threshold nothing measured (DELETED per Cray's typed ruling; the same claim struck from `PULL_REQUEST_TEMPLATE.md`), and a cache-bust test freezing per-file minima over **9 of 21 JS / 0 of 4 CSS files** — replaced by a relational diff check. 🔴 **AC-12's dead-port probe exits 1 while pytest reports `4005 passed, 484 skipped`** — 484 skips against a normal 8. | `1993bda` / [#1305](https://github.com/CrayJThiemsert/vero-lite/pull/1305) / `docs/plans/done/0107-oracle-coverage-hardening.md` |
| 2026-08-26 | **s255 — FOUR PRs (#1293–#1296): PLAN-0115 COMPLETE 10/10 and ARCHIVED — `tools/probe_battery/` ships as ADR-0038 C6's named D2 form-(c) enforcer.** 🔴 **VX-1 DISCHARGED** (owed since PLAN-0021, never answered): a non-blocking Stop-hook `systemMessage` **does** surface as `Stop says: …` to the **user's UI only**, but adopting it breaks **PLAN-0069 AC-3** parity — available, unadopted. 🔴 The instrument found **two defects in itself**; the stale-`.pyc` one passed the full local suite and **only CI reddened**. | `2448f90` / [#1296](https://github.com/CrayJThiemsert/vero-lite/pull/1296) / `docs/plans/done/0115-*.md` |
| 2026-08-25 | **s254 — FOUR PRs (#1288–#1291): PLAN-0115's four SDs RULED (Cray, typed).** 🔴 **SD-2's two drafted options BOTH failed on measurement** — (a) a hook exiting 0 sends its stderr note to a debug log holding **0 files and a dangling symlink**; (b) trail annotation corrupts **four control-flow reads** in `_goal_gate.py`. Ruled: zero-residue upheld, visibility to **Telegram keyed to the lock**; the *"no Telegram"* clause **struck — no author, no reviewer** (ADR-0018 VX-1). SD-1 effort **~36 → 53 sites / 50 files**, measured. SD-3 **defer**. | `db98126` / [#1288](https://github.com/CrayJThiemsert/vero-lite/pull/1288) / `docs/plans/done/0115-*.md` |
| 2026-08-25 | **s254 — ADR-0038's W-1 entry is PROMOTED to C6 on its third firing** (#0043, *"a probe's RED must name what broke"*) — the D1.6 promotion obligation discharged, merged by Cray the same session. 🔴 **C6's predicate needed a legibility conjunct:** firing 2's assertion fired correctly at its own site, so crediting it was right — the defect was **unreadable output**; a crediting-only predicate counts two and never triggers. ⚠️ C6 names **PLAN-0115 Step 1 AC-2/AC-4** its D2 form-(c) enforcer, so PR-A now owes enforcement work. | `28f5cc3` / [#1290](https://github.com/CrayJThiemsert/vero-lite/pull/1290) / `docs/adr/0038-*.md` |
| 2026-08-25 | **s253 — TWO PRs (#1286, #1287): PLAN-0114 Step 1 SHIPPED — the `continue_no_decision_run` chokepoint, purely additive; 14 tests, 17 claims, 14/14 probes witnessed, `orchestrator.py` + `action_step.py` at 0 diff lines.** 🔴 **Two of thirteen probes had been credited for reddening on a CRASH** (`AttributeError`, `KeyError`) rather than on the assertion each claimed — a published `13/13` was overstated and was corrected in-PR with measured evidence. 🔴 The `goal-evaluator` found **five** residual gaps in work already called done; all five real. | `082a6f1` / [#1287](https://github.com/CrayJThiemsert/vero-lite/pull/1287) / `docs/plans/done/0114-empty-gate-continuation-acknowledge-and-complete.md` |
| 2026-08-25 | **s253 — ADR-0038 D4's W-1 watch-list entry took its THIRD firing** (*"a probe's RED must name what broke"*, #0043, previously at exactly two): D1.6 makes promotion **an obligation, not an option**, and leaving a counted class advisory needs an explicit typed Cray waiver at the same site. **UNRESOLVED — it is SD-4 on #1288.** ✅ **Three Cray-typed rulings for PLAN-0115, all LOCKED:** scope as recommended · amend `CLAUDE.md` §8 to name the tool · include the flake-attribution lesson. | `b5c76bd` / [#1288](https://github.com/CrayJThiemsert/vero-lite/pull/1288) / `docs/adr/0038-advisory-lesson-promotion-three-strike-rule.md` |
| 2026-08-24 | **s251 — ONE PR (#1275): PLAN-0113 Step 1 SHIPPED, AC-1 CLOSED — the `scope_by`/`when_absent` read grammar lands on `StepInput`, consuming nothing yet.** Governance-pinned **only-when-supplied** (ADR-0034 D6, the `transform` precedent): an always-present key would have moved all six verticals' config hashes and made every in-flight run refuse at resume. 🔴 The nine-probe battery **failed its own criterion twice** — instrument repaired, criterion never relaxed. ⚠️ Two Cray-typed ratifications at merge: `from:` required-explicit, and a **fourth load-gate refusal SB-3 does not enumerate**. | `968b34e` / [#1275](https://github.com/CrayJThiemsert/vero-lite/pull/1275) / `docs/plans/done/0113-*.md` |
| 2026-08-24 | **s250 — FOUR PRs (#1271–#1274): In-Flight Discussions and the Current-Focus rotation ledger are CAPPED (Cray, typed)** — pointer ≤ ~600 chars · OPEN-only · ≤ 6 entries; the ledger keeps the current window. 🔴 **The enforcer had never received two rules Cray ratified long ago** — the s194 per-block cap and the s141 Active-TODO rule were absent from `.claude/agents/status-scribe.md` entirely; both backfilled. STATUS 53,048 → **48,645 B**. ⚠️ The four-day `index.lock` root cause (a SIGSTOP'd git process, `STAT=T`) rehomed into the git-workflow skill. | `98b3cda` / [#1271](https://github.com/CrayJThiemsert/vero-lite/pull/1271) / `docs/runbooks/memory-architecture.md` |
| 2026-08-23 | **s249 — TWO PRs (#1268, #1269): PLAN-0112 SD-4 REVERSED (Cray, typed) — an event-fired run is scoped to its FIRING CASE**, drafted as PLAN-0113 with the ADR-016 amendment it requires Accepted the same session; `superseded by new info`, not an error. 🔴 Ten rulings, all as-recommended. 🔴 **OQ-1 closed a 3-session-old question** — Code may append `## Post-archival amendment` + one inline pointer in `done/`, **supersession pointers ONLY**. ⚠️ ADR-016's amendments index read 5 against 7 body sections; backfilled, now 8 = 8. | `33a4887` / [#1269](https://github.com/CrayJThiemsert/vero-lite/pull/1269) / `docs/adr/0016-*.md` |

_[The two oldest rows (**s234, s233**) rotated to `docs/status-archive/2026-h1-status.md` at the s243 cont. reconcile, holding the table at ten. Two rows were added: the **s242 backfill** — Cray ruled it in, discharging the gap the s243 reconcile flagged, and its four rulings are no longer carried by narrative alone — and a **second s243 row**, because Step 1 is a BUILD event of a different kind from that session's rulings and folding it into the existing row would have written a row far over R2's ~600-char pointer cap. The oldest row (**s237**) rotated to the same file at the s245 reconcile, holding the table at ten; the s238 row followed at the s246 reconcile for the same reason. The **s239** row followed at THIS (s247) reconcile, again holding the table at ten. **Session 248 discharged the pointer-cap overage this table still carried: 8 of the 10 rows were over R2's ~600-char cap, and are now zero.** Each row's substance — not merely the path it named — was resolved against `git ls-files` before that row was shortened; the one fact tracked nowhere else, s240's *ancestry is not content*, was **rehomed first** into `.claude/skills/git-workflow/SKILL.md`, then re-pointed, then trimmed. All eight full originals are preserved verbatim in `docs/status-archive/2026-h1-status.md` (R4, move-never-drop). The **s240** row rotated to the same file at THIS (s248) reconcile, holding the table at ten. ⚠️ It is the one row whose fact was rehomed the session *before* it rotated — *ancestry is not content* now lives in `.claude/skills/git-workflow/SKILL.md`, and that skill's widened `description` surfaces it automatically — so its rotation drops nothing that STATUS was the sole carrier of. The **s241** row rotated to the same file at THIS (s249) reconcile, holding the table at ten. Its substance keeps two tracked homes — `docs/conventions/retired-claims.md` for the guard it shipped, and the *"the two s241 pre-commit guards are FLOORS, NOT CEILINGS"* entry in §Active TODOs for the live remainder — so it, too, rotates on the count rule alone. The two oldest rows (**s243**, **s242**) rotated to the same file at the **s251** reconcile — a two-session reconcile added two rows (s250, s251), so two left to hold the table at ten. Both rotate on the count rule alone: s243's G-13/G-14 substance lives in `docs/plans/done/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md`, and s242's SD-E reversal, second L1 re-reading and OQ-7(b) each keep a live Active TODO plus `docs/adr/0035-hosting-and-exposure-model.md`, whose own amendment pass records that a LOCKED ruling is amended in place, never edited. The two oldest rows (**s244**'s #1249 ฿-facet row and **s243 cont.**'s #1246 row) rotated to the same file at THIS (s253) reconcile — two s253 rows entered, one build and one governance, so two left to hold the table at ten. Both rotate on the count rule alone, **checked against the artifact before trimming, not assumed**: the #1249 emission fix and its run-scoped `(action_id, facet kind)` ledger are documented in `services/engine/procedures/action_step.py`'s own docstring, and the #1246 `triggered_by: null` / two-probes-on-different-assertions substance lives in `docs/plans/done/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md`. The two oldest rows (**s245**, **s244**) rotated to the same file at THIS (s254) reconcile — two s254 rows entered, one rulings and one governance, so two left to hold the table at ten. Both rotate on the **count rule alone**: s245's *three guards passed while protecting nothing* finding is the one that promoted `CLAUDE.md` §8's witnessed-RED rule, and lives there as binding text; both rows' PLAN-0112 build substance is in `docs/plans/done/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md`. The oldest row (**s246**) rotated to the same file at THIS (s255) reconcile — one s255 row entered, so one left to hold the table at ten. It rotates on the **count rule alone**, checked at the artifact rather than assumed: PLAN-0112 is COMPLETE 9/9 and its AC-7(i) finding lives in `docs/plans/done/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md`, and the week-stale-checkout incident is recorded in `docs/logs/2026-08-22-s246-*.md`, which the row itself names. The oldest row (**s247**) rotated to the same file at THIS (s257) reconcile — one s257 row entered, so one left to hold the table at ten. It rotates on the **count rule alone**: the Active-TODOs pointer cap it records is binding text in `docs/runbooks/memory-architecture.md` §R2 and in its enforcer `.claude/agents/status-scribe.md`. ⚠️ **Its *"R9 is now tracked NOWHERE"* finding was NOT re-checked at this reconcile** — surfaced to Cray rather than asserted resolved; the full row travels verbatim into the archive, so nothing is dropped.]_

## In-Flight Discussions

- **OPEN QUESTION for Cray — does a skill's registry table *bind*?** (Code's observation, not a ruling.) s210's closing notice asserted the four-work-stream registry table in `.claude/skills/stream-status/SKILL.md` (#1062) is **canonical**, and that a carrier-artifact change must update it **in the same PR**. The table as *reference* is fine; the **same-PR obligation** is the part that would have to live in `CLAUDE.md` or an ADR to bind — §1 places `.claude/skills/` at **Tier 2.6, derived, no independent precedence** (ADR-0017 D6). **Cray's call: promote it, or keep the table advisory.**
- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm — **not yet drafted**, and it needs a fresh ADR number. _[The old "≥ ADR-014" floor recorded here was **moot** — see the Active TODO below, corrected s141: ADRs now run past 0032 and `0014-WITHDRAWN.md` exists. Kept as one pointer rather than two divergent copies.]_
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).

## Active TODOs

- [x] **PLAN-0114 — COMPLETE 6/6 (s256) and archived.** Shipped in [#1287](https://github.com/CrayJThiemsert/vero-lite/pull/1287) (Step 1) and [#1298](https://github.com/CrayJThiemsert/vero-lite/pull/1298) (Steps 2–5, merged `13d11b7`). ⚠️ **Two PLAN texts were measured WRONG in flight** and corrected in place: AC-1's one-POST arity (it takes two — `fulfill` is gated too), and §Mechanism item 3's Tab G/H mislabel, which turned `view-hero.js` from "in scope" into a **scope cut**. The first is why SD-4 exists — it invalidated the premise Step 3 rested on, so the question went back to Cray. 🔴 **AC-5's LIVE half is CARRIED, not closed** — see the deploy TODO below. **Read:** `docs/plans/done/0114-empty-gate-continuation-acknowledge-and-complete.md` §Closeout.
- [x] **CRAY'S CALL — deploy PLAN-0113 + PLAN-0114 to the live fleet demo, as ONE unit. DONE s256; ticked s257** (the row's own sub-line recorded the deploy while the box stayed unticked). 🔴 **0113 must not ship alone:** its Step 3 is what *creates* the empty-gate dead end, and 0114 is what closes it — deploying 0113 by itself puts a visitor-reachable dead end on the published demo whose only exit records *abandonment*. Measured read-only on MS-S1 under a typed go: host at `ee41b55`, fleet image `0fc679cf` (2026-08-22), the `vero-published` STOP condition **clear**. Needs a typed go **per phase**. Closing this also closes PLAN-0113's CARRIED-OPEN **AC-9** and PLAN-0114 AC-5's live half in one occasion. **Read:** `docs/logs/2026-08-26-s256-ms-s1-readonly-deploy-census.md` §5.
  <br>✅ **DONE s256 (Cray's typed go, recorded before the first host command).** Host `ee41b55` → `dd4228f`; image `0fc679cf` → `880307365d7f`, **id-identical across machines**; only `app` recreated, then `cloudflared` force-recreated because `config.yml` carried the new ingress row; `DEMO-STATE: PRISTINE` before and after; rollback tagged `:prev`. **Record:** `docs/logs/2026-08-26-s256-fleet-deploy-plan0113-plus-0114.md`.
- [ ] **🆕 CRAY'S CALL — PLAN-0116's THREE SDs are unruled and had no row here until s257.** `docs/plans/0116-deterministic-claim-rollup-tool.md`, `Status: Draft`, 0/8 ACs, 3 Steps, one PR, deterministic-offline. **SD-1 is the heavy one** — the mixed case (∃ vs ∀ reading); it hard-codes forever an interpretation of Cray's own typed four-line rule, and `_rollup.py` cannot be written until it is ruled. SD-2 (measure labelling stability here?) and SD-3 (exit-code contract) are light. ⚠️ **Measured s257, and it is the reason to rule deliberately rather than by default:** the tool ships with **zero wired producers and zero wired consumers** — both are cut by name in its Out of Scope — so on day one its only caller is its own test suite. Until s257 the SDs were carried only by a `blocked_on` line naming #1301 as *open*, and #1301 merged — the drift this row exists to stop.
- [x] **`tools/probe_battery/` restored CONTENT but not file MODE — FIXED s256.** Found mid-deploy: the three files this session's batteries mutated came back **`0600`**, because `NamedTemporaryFile` creates its temp file `0600` and `os.replace` carries that onto the target — so every atomic write silently narrowed the file, on the mutation and again on the restore. **Every existing check was blind, each for a different reason:** `git status` (`core.fileMode=false`), the suite (reads as the owner), CI (fresh clone gets git's `100644`), and the driver's own restore check (compares sha256 — and the bytes were perfect). `docker build` copies the mode faithfully, so **the image could not import its own engine** (`PermissionError`, container runs as `uid=999`). Only DEPLOY.md §2a's in-image hash check found it. **Fix:** `original_mode` on the snapshot, handed back on both writes, and `_restore_entry` now RAISES on a mode mismatch. 3 tests, 2 witnessed RED + a declared-GREEN control through the driver itself; the battery mutated `_snapshot.py` and the fixed driver restored its own mode correctly. **Read:** `tools/probe_battery/README.md` §"Restore returns the MODE".
- [x] **The visitor WALK is DONE (s256) — PLAN-0114 AC-5's live half is CLOSED, and the scoping PLAN's carried live-evidence line is discharged and ticked in its archived file.** Driven in a real browser on the published surface, Cray doing the Access PIN. **Scoping:** the mid-band run's gate holds **exactly one** proposal and it is the visitor's own case — against the pre-scoping seeded run still showing three. **AC-5:** the empty-gate run renders **Acknowledge** and no Submit, the one-proposal run renders **Submit** and no Acknowledge, and **one click** took the empty run to `completed` reporting **"(2 empty gates)"** — the arity measured offline, confirmed live. Audit carries an acknowledgment on **both** gates naming วิรัช; `/audit/verify` `intact: true`, 64 rows, 0 breaks; `DEMO-STATE: PRISTINE` unchanged. The live page also serves `api.js?v=c49` / `view-monitor.js?v=c42` — the bumps reached the browser, not just the container. **Read:** `docs/logs/2026-08-26-s256-fleet-deploy-plan0113-plus-0114.md` §5.
- [ ] **🆕 CRAY'S CALL — the s256 walk's residue is TWO RUNS, not two cases; leaving them parked is the current lean.** Measured s257 LIVE, read-only, under three typed gos: both cases **ABSENT** (control-backed); `governed_repair_approval@41bb78353e7c4138` is still `waiting_human` at a resolvable `approve` gate, `@d8f5a677b8f73b3b` `completed`. 🔴 `DEMO-RESET.md` is **not** the tool for a visitor-created id; the per-case seam is `delete_case`. ✅ Resolving that gate is **harmless** — proven offline, not by clicking live ([#1304](https://github.com/CrayJThiemsert/vero-lite/pull/1304)). ⚠️ `audit_log` unchanged at 64 rows, so **how the cases went away is measured but unexplained**. **Read:** `docs/logs/2026-08-27-s257-fleet-walk-residue-readonly-probe.md`.
- [ ] **🆕 CRAY'S CALL — `.claude/worktrees/` is 1.8 GB and `git worktree prune` cannot reach most of it.** Measured s256 by set difference, jointly with the parallel session: **19 directories on disk · 7 registered · 6 prunable · 12 UNREGISTERED**. Prune touches **6 of 19**; the other 12 git no longer knows about and only a manual delete removes. Largest: `eloquent-chatelet` 257 MB · `recursing-chatterjee` 163 · `wizardly-hopper` 161 · `youthful-driscoll` 150. **Nothing deleted — 1.8 GB is irreversible and out of scope for Code.** Related: Cray ruled parallel sessions onto separate worktrees this session, so the set will keep growing.
- [ ] **🆕 CRAY'S CALL — a battery skip is indistinguishable from "no active goal" in the trail.** `_goal_gate.py`'s early return fires before any `record_evaluation` for BOTH the battery-lock stand-down and the no-goal case, so `goal.json` stays **byte-identical** — nothing can later establish that the gate ever stood down for a battery. This is the **price PLAN-0115 SD-2's zero-residue ruling pays**, not a defect, but the price was never measured when it was ruled. Changing it needs a new SD, not a trim. **Read:** `docs/logs/2026-08-26-sd-premortem-replay-experiment.md`.
- [x] **PLAN-0115 — COMPLETE (s255) and archived.** All ten ACs closed across three PRs: [#1293](https://github.com/CrayJThiemsert/vero-lite/pull/1293) (Step 1 + 4a — the driver, and ADR-0038 C6's named D2 form-(c) enforcer), [#1294](https://github.com/CrayJThiemsert/vero-lite/pull/1294) (Step 4b — lesson 0048 + W-1's tally in a tracked file), [#1295](https://github.com/CrayJThiemsert/vero-lite/pull/1295) (Steps 2+3 — the battery lock and the bounded teardown). 🔴 **Step 2's VX-1 `systemMessage` probe is DISCHARGED** — owed since PLAN-0021 and never answered: it **does** surface, rendered `Stop says: …`, to the **user's UI only** (never Claude's context). But adopting it on the warn path would break PLAN-0069 **AC-3**'s enforce-parity guarantee, so it stays available-and-unadopted. **Read:** `docs/plans/done/0115-probe-battery-driver-and-verification-instrument-hardening.md` §Closeout.
- [ ] **🆕 ADR-016 SB-3 enumerates THREE load-gate refusals; the SHIPPED Step 1 has FOUR.** The fourth — `when_absent` supplied with **no `scope_by`** — was Cray-ratified at the #1275 merge (typed, s251), but SB-3's body still names only the three `scope_by`-present cases; re-checked in the ADR at the s251 reconcile. **Cray's call: amend the ADR, or leave the fourth recorded in the PLAN.** ⚠️ Whoever opens ADR-016 for this should also repair its **two dead pre-archive PLAN pointers** (`0052-*` and, since s252, `0113-*` — both now under `docs/plans/done/`). R8 exempts `docs/adr/` **temporarily and by design**, because G1 blocks Code from editing an Accepted ADR; the exemption's own comment says to remove it in the same change that lands those fixes. **Read:** `docs/adr/0016-governed-procedure-engine.md` §SB-3 · `docs/plans/done/0113-scope-event-fired-run-to-its-firing-case.md`.
- [ ] **🆕 CRAY'S CALL — should R2 cap the Active TODOs *COUNT*, and govern the Recent Decisions trailing ledger?** 🔴 **Measured s255, and this is now what holds STATUS over R1's soft target:** Active TODOs is **21,311 B — 43% of the file** across 38 entries (each ≤ ~600 chars, fully compliant; nothing bounds how many), and the RD trailing ledger is **4,261 B, ungoverned** — the s250 cap reached the *Current-Focus* ledger only. By contrast all four Current-Focus blocks are **1,985–3,301 B**, well under R2's 4,096 cap. Capping either **authors a rule**, so Code surfaced it rather than trimming (R6). **Read:** `docs/runbooks/memory-architecture.md` §R2.
- [x] **CRAY'S CALL — should R2 cap `In-Flight Discussions`? RULED s250 (Cray, typed): YES.** Capped at pointer ≤ ~600 chars · OPEN-only · ≤ 6 entries; the Current-Focus **rotation ledger** is capped to the current window by the same ruling. Both live in R2 (`docs/runbooks/memory-architecture.md`) **and** in their enforcer, `.claude/agents/status-scribe.md` — which s250 measured had never received the s194 per-block cap or the s141 Active TODOs rule either; both backfilled. STATUS **53,048 → 48,645 B**, under the R1 soft target ([#1271](https://github.com/CrayJThiemsert/vero-lite/pull/1271)).
- [ ] **🆕 ADR-0035 — L1 re-read a SECOND time, and OQ-7 ruled, both Cray-typed s242.** L1 becomes *"one gate at the edge; app code may READ the verdict, never gate itself"*, unblocking phase-2 identity **capture** while **validation** stays pilot-era. **OQ-7 = (b)**: absent edge identity → proceed and **stamp the absence**. ⚠️ Two costs Cray accepted: runs stay unattributed until someone reads the stamps and **nothing alerts on it**; the stamp shape is PLAN-0112's to specify, not the ADR's. **Read the ADR:** `docs/adr/0035-hosting-and-exposure-model.md`.
- [ ] **🆕 The three live items the rotated s240 block carried — carried here so the rotation ledger's claim is true, not merely stated.** Measured at s240, none resolved since: (i) the **font-size decision still gates re-measuring every geometry number in the beat-4 mockup**; (ii) the **run-list backlog badge on the host is still unmeasured** — a host-state read, so it needs its own typed §8 go; (iii) the **three Advisory-proposal candidates are still unnamed**, so the gate panel still reads as unfinished. The full s240 narrative is at `docs/status-archive/2026-h1d-current-focus.md`.
- [ ] **The Tier-0 auto-memory store is a git repo that DRIFTS — REHOMED s247 to the runbook's Tier-0 section, which is where a reader about to run a consolidation actually looks.** Snapshotted s242 (164 tracked, tree clean). ⚠️ **A snapshot guards against a wrong deletion, NOT against disk loss — there is still no remote.** 🔴 **The `MEMORY.md` consolidation is PARKED (Cray, s257):** all **116** memories citing no repo home were audited and **ZERO** were unconditionally safe to delete, and **no hook anywhere enforces the < 140 target** (`.claude/hooks/**/*.py`, both `settings.json`, `~/.claude/hooks/` all checked). **Do not re-run the audit.** **Read the runbook, never a restatement:** `docs/runbooks/memory-architecture.md` §Tier 0.
- [ ] **🆕 PLAN-0110 SD-E is REVERSED (Cray, typed, s242); its commissioned follow-on PLAN-0112 is COMPLETE and ARCHIVED s246.** The original ruling stands as history and is **NOT** edited. ⚠️ **Two consequences no AC owns:** `/runs` filtering is client-side only *because* the population was pinned at two, and the Monitor "all" filter has no cap — SD-6(b)'s bounded default covers Tab H, a **different surface**. **Read the archived PLAN:** `docs/plans/done/0110-fleet-demo-run-markers-filter-and-deploy-reset.md` (§SD-E · §Out of Scope).
- [ ] **🆕 The four s235 audit findings ADR-0038 did NOT absorb — REHOMED s235 to `docs/logs/2026-08-17-s235-audit-findings-outside-adr-0038.md`.** 🔴 **One live obligation: ADR-0038's three-strike counter has NO OWNER** — and the count has DRIFTED, the s235 log naming **three** items at two firings while ADR-0038's own D4 names **two**. PLAN-0108 is the natural owner and does not claim it. ⚠️ The genuinely-unruled item is the **D2.1 authorship fork**, not "ADR-0037 SD-1", which does not exist. **Read the log.**
- [ ] **🆕 PLAN-0111 — the fleet close-out record that can hold a credit note (ใบลดหนี้): `Draft`, all six SDs RULED** (Cray, typed 2026-08-19, [#1227](https://github.com/CrayJThiemsert/vero-lite/pull/1227)). **Cray ratified the SDs, not the PLAN; nothing gates execution.** 🔴 **SD-E forces SD-A to (b), a separate `repair_case_credit_note` table.** ⚠️ **AV-1 is owed before Step 4, not before merge** — SD-C is provisional on it. **Read the PLAN:** `docs/plans/0111-fleet-closeout-credit-note-record.md`.
- [x] **PLAN-0107 — oracle-coverage hardening: COMPLETE 15/15, ARCHIVED s258** to `docs/plans/done/0107-*.md` ([#1307](https://github.com/CrayJThiemsert/vero-lite/pull/1307), `d78eebe`). AC-9 closed on Cray's ruled **option (b)**; AC-12/13/14/15 ticked only after each AC's **own pass read was re-run**, never from #1305's prose. ⚠️ **Read each AC and its `Reviewer amendment` blocks as authoritative; the §Steps prose is narrative** — Step 7 was rewritten at closure because its probe was unrunnable as written.
- [ ] **🆕 `tools/check_ac_consistency.py` has a measured blind spot — the AC-ledger guard did not see PLAN-0107's own drift.** Four of that PLAN's criteria sat unticked while this file asserted its Phase C had shipped, and the guard still exited **0**. Reading its source: it scans for criterion references **backwards** from each closure keyword, with the lookback stopping at the previous one — so a row that writes the keyword *first* and its criterion references *after* falls outside the window entirely, while a sibling phrasing on the same line that puts them *before* is detected normally. 🔴 **NOT fixed, and the mechanism is read from source, NOT probed.** ⚠️ Widening the matcher needs a prototype pass first, for two measured reasons: the guard's own docstring records deliberate non-claims a wider matcher would begin catching, **and this very row had to be rephrased to stop the guard reading its description of the bug as a closure claim** — the s257 `fail_under` lesson exactly (prose containing the token breaks the read; rewrite the prose, never the criterion).
- [ ] **🆕 PLAN-0107's citation population is only PARTIALLY verified — recorded here because nothing else carries it.** The s241 sweep was exhaustive for `verticals/fleet_maintenance/operate_seed.py` **only**; the drafter said it had not checked the rest, and named the at-risk set: AC-8's cites into `tests/api/conftest.py`, the Phase A cites into `.github/workflows/ci.yml`, and a tail into files no closed AC touched. 🔴 **Most are BEFORE-STATE cites — historical by design** — so the treatment is likely **labelling, not re-anchoring**, making it PLAN-0108's question. **NOT ruled.**
- [ ] **🆕 PLAN-0108 — AC-authoring + pre-close convention hardening: `Draft`, UNRATIFIED.** The weak-oracle half of the s235 audit. 🔴 **Still gated: SD-1 is NOT ruled — ROUTED to Cowork** (until ratified, §8 as written governs); three of six ACs close only on Cray's PR-merge read; Step 1 is G2-gated for Code. ⚠️ **UNDECIDED, live only here: the AC labels read `[1, 5, 2, 3, 4, 6]` — unique but NOT ascending.** Ordering them means moving a block against a live citation — **Cray's call**. Owns ADR-0038's **OQ-5**. **Read:** `docs/plans/0108-ac-authoring-and-preclose-convention-hardening.md`.
- [ ] **🆕 The two s241 pre-commit guards are FLOORS, NOT CEILINGS.** `tools/check_retired_claims.py` (hook #18; convention `docs/conventions/retired-claims.md`) cannot catch a **reworded** stale copy and cannot know a claim *should* have been retired — declaring stays a human act. `tools/check_ac_consistency.py` (hook #19) cannot read a **phase-level** claim (*"Phase A CLOSED 6/6"* names no AC — three exist), and covers **active** PLANs only. ⚠️ `docs/plans/done/0042-at2-managerial-build.md` carries a duplicate `AC-13`, **deliberately out of scope** as frozen history.
- [ ] **🆕 PLAN-0109 (Ask over repair cases) carries THREE factual defects in its RULED content — measured s241, zero tracked hits. Fix all three BEFORE Step 5; `docs/plans/` writes, so G2-gated, owed to a drafter dispatch.** 🔴 **(i) AC-11 would write a FALSE sentence by deleting a TRUE one** — case text reaches the **phrase prompt only**, so its grep pass read **cannot fail**: it is satisfied by deleting a truth. 🔴 **(ii) `tenant_id` is missing from the exclusion enumeration and reddens AC-3 on the first run.** **(iii)** AC-3(iii) contradicts AC-10 on `seq`. **Read:** `docs/plans/0109-*.md`.
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
