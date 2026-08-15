---
last_updated: 2026-08-15T13:20:58+07:00
session: 233
current_batch: "s232 fleet bring-up push — ELEVEN PRs MERGED (#1170–#1179), 0 open. Grounding REFUTED the inherited \"one artifact left\" framing: 14 gates walked, five closed by rulings, then PLAN-0106 built (D2.4 discharged), Cloudflare proven and host secrets staged. ONE gate left. [Reconciled s233 — s232 closed before updating STATUS for #1178/#1179.]"
current_actor: code
blocked_on: "NOTHING blocks repo work. Fleet's bring-up now gates on ONE artifact — PLAN-0103 AC-11's RoPA instance (Cray's, as controller). The typed §8 go was given verbally but cannot be validly RECORDED until the RoPA exists to cite by path."
next_action: "Cray's — author fleet's RoPA (last gate; inputs complete), and mark PLAN-0106 Complete so Code can tick its ACs and archive it."
head_commit: 5425822
recent_commits: [5425822, d09a77c, 6937573, 205ba4b, e4ebd51, efaa05a, 4653988, 8b2fc14, ec4ac0f, 334d797]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 232, 2026-08-15 (head_commit `b2fe45e` → `5425822`) — ELEVEN PRs
> MERGED (#1170–#1179), 0 open. A next-work ranking became a fleet bring-up
> push: grounding REFUTED the inherited "blocked on ONE artifact" framing and
> found three more gates. Cray ruled six times and five gates closed — then the
> session continued past its own close and shut three MORE, leaving fleet on
> exactly one.** _[Reconciled s233 — s232 closed before #1178/#1179.]_
>
> 🔴 **Prose has no consumer, proven twice** — PLAN-0105's archived text claimed
> a `delete_case` factoring **that did not exist** (EXTRACTED, not re-worded,
> #1171), and fleet's Operate seed shipped s221 while **two of the three
> artifacts describing it still said it was unbuilt**; ruff, mypy and 4093 tests
> stayed silent eleven sessions (#1170, #1173). _[Both in their TODO rows.]_
>
> ⚠️ **`GET /api/cases` is unauthenticated and unfiltered** and `^/api/cases$` is
> on fleet's allowlist — cloudflared matches PATH, not METHOD. **RULED INTENDED**
> (Cray, typed). 🔴 **Record the PREMISE, not the word:** legitimate **because the
> data is synthetic**. Recipients fact: `ropa-change-statement-fleet.md` §4(c).
> ⚠️ **This measurement also forced SD-1's visibility clause WIDER than its
> draft** — the exposure is not surface-bound.
>
> ⚠️ **An empty database is invisible until a visitor hits it.** `/health` never
> touches Postgres and `cloudflared` gates only on `service_healthy` — the tunnel
> OPENS on a system whose visitor case path fails on the first write. RULED
> **operator step + make the skip LEGIBLE** (#1176). ✅ **Also RULED (#1174,
> #1175):** ADR-0037 **D4/OQ-2 = (a)** · recorder free text = **(i)** · ⚠️ OQ-1
> had been ruled since s231 while the ADR still read OPEN. ✅ **`deploy.py` does
> NOT block the bring-up** — it is the REDEPLOY tool.
>
> 🔴 **ADR-0037 D2.4 was an obligation with NO OWNER for three sessions** — the
> ADR said mechanics belong to the owning PLAN and none took it; no STATUS row,
> no test, no checklist held it, and it surfaced only by walking D2's obligations
> one at a time. ✅ **Owned by PLAN-0106 (#1174), then RULED in full, BUILT and
> MERGED the same session (#1178, #1179) — D2.4 is DISCHARGED.** 11 tests;
> **4107 passed / 8 skipped**. **Read the PLAN's §Surfaced decisions, never a
> restatement.**
>
> 🔴 **A guard that scans COMMITTED files is blind to a NEW file, and the blind
> spot sits where confidence peaks** — #1179 went RED in CI but **not locally**.
> Its sibling: **the visual pass found what eleven green tests could not** (no
> CSS; legible but not recognisable *as* a notice). Both, plus the guard family
> and the practice, are recorded in
> [`docs/lessons/0044-*.md`](lessons/0044-a-committed-file-guard-is-blind-to-the-new-file.md)
> — **read it, never a restatement.**
>
> ✅ **Fleet's two Cloudflare artifacts and four host secrets are DONE and
> PROVEN** — ⚠️ the **differential PIN test** is the only check that proves the
> policy *discriminates*; a wide-open policy returns the same `302` and shows the
> same screen. **ADR-0036 D2's price is paid for fleet.** 🔴 **Read the evidence,
> never a restatement — and note it is RECONSTRUCTED, not captured live:**
> [`docs/logs/2026-08-15-fleet-cloudflare-artifacts-and-secrets-staging.md`](logs/2026-08-15-fleet-cloudflare-artifacts-and-secrets-staging.md)
> (written s233 — the bring-up log that will normally own AC-10's evidence cannot
> exist until the bring-up does, and until then it lived only in a **gitignored**
> handoff).
>
> ⚠️ **The gate list is now ONE item, not five. PLAN-0103 AC-11's RoPA is the
> only one left, and only Cray can write it.** Fleet's typed §8 go was given
> **verbally but cannot yet be validly RECORDED** — AC-11 requires the record to
> cite the RoPA **by path**. **Requester identification for the DSR path remains
> genuinely undesigned:** `repair_case.opened_by` has no foreign key and personas
> add no visitor identity, so a request matches rows **only by content**.

> **Session 231, 2026-08-14 (head_commit `9072760` → `b2fe45e`) — eight PRs
> MERGED (#1159–#1167), 0 open. vero-lite gained its FIRST row-retention
> control, and PLAN-0105 went from undrafted to COMPLETE 11/11 and ARCHIVED in
> one session.**
>
> ✅ **What ships:** fleet's visitor-opened repair cases, their six FK children
> and their upload directories are deleted **90 days after `opened_at`** by an
> in-app task — the sweep (`services/db/repair_case_retention.py`), the task
> (`services/api/case_retention_task.py`, wired into `lifespan` with **zero
> added branches**), the eighth-table completeness guard (AC-5), fleet's
> `CASE_RETENTION_ENABLED=true` profile flag with a both-directions deploy
> guard, and the scenario test (AC-10). **Read the archived PLAN, never a
> restatement:** `docs/plans/done/0105-fleet-case-retention-in-app-deletion.md`.
>
> 🔴 **The one finding a future reader must NOT re-derive — classified `was an
> error`.** `repair_case_accepted_quote` holds a **composite FK to
> `repair_case_quote`**, and Step 1's declared deletion order deleted the quote
> **FIRST** — so the sweep raised `ForeignKeyViolation` on every case that had
> ever accepted a quote, was caught by its own fail-soft, and **retried
> forever**. **Retention would silently never have completed on real data while
> every unit test stayed green.** ⚠️ **Neither existing guard could see it:**
> Step 1's unit test inserted a task event and no quote pack, and **AC-5 checks
> membership, not order**. Only the Step-6 scenario, on the first realistic
> case, failed. Fixed by one measured swap (**exactly one** child-to-child edge
> exists) and guarded by
> `test_the_declared_order_respects_every_child_to_child_dependency`.
>
> ✅ **Four SD slots RULED (Cray, typed, 2026-08-14) and folded in:** SD-1 **(b)**
> ordered app-level child deletes + the AC-5 guard (no migration; the loud
> fail-closed DELETE posture preserved) · SD-2 **(a)** files first, then rows ·
> SD-3 **no status exemption** — MEASURED: no code path closes a case, so an
> OPEN exemption would exempt **every** row — **and** the chain's dangling
> `case_id` pointer stated as intended design · SD-4 **(a)**
> `repair_case_run_link` rows deliberately RETAINED.
>
> ⚠️ **What `Complete` does NOT mean.** **PLAN-0103 AC-11's RoPA is still
> Cray's** (it now has a shipped control to describe), the **DSR-on-request path
> for case rows is still undefined**, and **fleet's bring-up still needs its own
> typed §8 go**.
>
> **Also landed:** #1159 corrected the RoPA's deployment-status line and two §7
> controls `owed` → `built` (`docs/compliance/ropa-published-demo.md`) —
> factual only, no controller judgment touched.

> **Session 229, 2026-08-14 (head_commit `9df016e` → `ee968e5`) — one PR
> MERGED (#1153). R8's PLAN-reference guard was structurally blind to a glob;
> the blindspot is closed, and the one live dead pointer it had been missing
> since s216 is repaired.**
>
> 🔴 **The guard could not see a glob.** Its slug class admitted no `*`, so a
> reference written as `NNNN-*.md` — **the form registries and closeout notes
> actually use** — matched nothing, and the guard stayed silent even after the
> PLAN had moved to `docs/plans/done/`. Present since R8 landed at s183.
>
> **Measured cost, one live instance:** the `stream-status` skill's stream-1 row
> went dead when PLAN-0100 was archived at **s216** and was **never reported
> once** — including by the very commit that updated the **stream-2** row beside
> it, for exactly this reason, one session later.
>
> **The fix — mechanics are in the runbook's R8 section, not restated here.** Two
> things a future reader must not re-derive: it resolves a glob through the **same
> MOVED-not-MISSING predicate**, so ⚠️ **the rejected "path does not resolve" rule
> (89 files flagged) is NOT reintroduced**; and it uses a flat `iterdir()` +
> `fnmatch`, **not `Path.glob`**, which would descend into `done/` and report every
> archived PLAN as still-live — **a fail-OPEN inversion**.
>
> ✅ **Non-vacuity: the six new tests were seen RED against the unfixed regex
> before the fix landed.** The widening then immediately flagged **two of the
> change's own source comments** — the narration trap the runbook records from
> s183, now on its **third occurrence**, fired by the very commit that widened the
> rule.
>
> 🔴 **A correction, classified `superseded by new info` — NOT `was an error`.**
> The session's brief named a second live dead pointer in
> `benchmarks/nl_query_feasibility/RESULTS.md`. Verified at the session's base: it
> was **not dead** — PLAN-0104 was still in `docs/plans/` and `done/0104*` had
> never existed. ⚠️ **Then the tree moved underneath the session:** #1151/#1152
> archived the PLAN and hand-repaired that citation **by hand precisely because
> this guard could not see the glob**. The file needed no edit.
>
> **Gates:** guard module **23 passed**; the real tree reports **0 violations
> across 1027 tracked files**; `mypy --strict services/` clean over 134 files;
> ruff + format clean on the archived HEAD tree.
>
> ⚠️ **The Windows-worktree environmental-RED floor is a DRIFTING count, not a
> remembered number** — the s229 run measured **7**, not the 6 previously carried.
> Attribute by cause and let the count fall out:
> [`docs/lessons/0042-a-remembered-baseline-is-not-evidence.md`](lessons/0042-a-remembered-baseline-is-not-evidence.md)
> holds the per-cause table and the named tests.

> **Session 228, 2026-08-13 (head_commit `75243b0` → `ad2804d`) — one PR
> merged (#1151), 0 open. PLAN-0104 Step 7 ran under Cray's typed §8 go, AC-7
> CLOSED, and the PLAN is COMPLETE 8/8 and ARCHIVED. The headline number is the
> least interesting thing in it.**
>
> ✅ **All four pre-committed reads PASS, on the FIRST pass** — nl-13 emitted
> `count` WITH `group_by: "asset_id"` (no retry) and scored `correct` under the
> tolerance-free `groups` scorer, groups relabelled to display names.
> **Read the evidence, never a restatement:**
> `benchmarks/nl_query_feasibility/RESULTS.md` §"Addendum — PLAN-0104 Step 7
> live evidence run".
>
> 🔴 **Citing 12/13 as an improvement over `11/12` is a DEFECT.** The prior
> figure is **RETIRED as non-comparable, not overwritten**, on two
> independently sufficient grounds: the shared system prompt changed in #1149,
> and the gold set grew 12 → 13. ⚠️ **The obvious citation is a TRAP** — the
> `11/12` in that file's arm-comparison table is **text-to-SQL**; the prior
> **engine-A** figure is AC-9's, in its own addendum. They coincidentally share
> a number.
>
> ✅ **The lone miss (nl-06) was re-run once per clause 3, failed again, and was
> investigated BEFORE merge — verdict: NOT a PLAN-0104 regression.** #1149's
> diff changes only the OPERATION sentence (FILTERS is **byte-identical**); the
> class is the catalogued simple-list filter-omission variance; and **the victim
> MOVED** — AC-9's miss was nl-01, `correct` here. Model-swap and prompt-tuning
> are both already PROVEN NEGATIVE on this axis. ⚠️ **The one alternative a
> single sweep cannot refute to zero is RECORDED:** that the lengthened
> OPERATION sentence dilutes attention to FILTERS. **Reopen condition, stated in
> place:** a sweep showing filter-omission **concentrating**, not **moving**.
>
> 🔴 **Bookkeeping, `was an error`:** STATUS asserted "AC-1..AC-6 and AC-8 are
> CLOSED" while **every AC checkbox was still `[ ]` on disk**; all eight are now
> ticked. ⚠️ **`c80df02` corrected the other direction — the Step 7 dumps are
> UNTRACKED, not gitignored**, so the raw per-case evidence survives **nowhere
> in history** and is **not protected from an accidental commit**.
>
> **Gates: 4045 passed / 8 skipped**, `mypy --strict services/` clean over 134
> files, ruff + format clean **on the HEAD tree**; `merge_tree_identical=YES`
> between tested `c80df02` and merge `ad2804d` (first parent `33dfc26`).

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
| 2026-08-15 | **s232 — ELEVEN PRs MERGED (#1170–#1179); the "fleet blocks on ONE artifact" framing was REFUTED — 14 gates walked, TWO owned by nobody.** Six typed rulings folded. ✅ **PLAN-0106 then RULED, BUILT and MERGED — D2.4 DISCHARGED** — and Cloudflare + host secrets closed. 🔴 **Fleet's gate list is now ONE item, AC-11's RoPA.** | `5425822` / [#1178](https://github.com/CrayJThiemsert/vero-lite/pull/1178) / [#1179](https://github.com/CrayJThiemsert/vero-lite/pull/1179) / `docs/plans/0106-*.md` / `docs/logs/2026-08-15-fleet-cloudflare-*.md` |
| 2026-08-14 | **s231 — PLAN-0105 drafted, its four SD slots RULED (Cray, typed), built and CLOSED 11/11 in one session: fleet's visitor cases, their six FK children and their upload dirs delete 90 days after `opened_at`.** 🔴 **The declared order deleted `repair_case_quote` BEFORE its composite-FK child** — `ForeignKeyViolation` on every case that had accepted a quote, swallowed by the fail-soft and **retried forever** with unit tests green; **AC-5 checks membership, not order**. Caught by the Step-6 scenario. | `b2fe45e` / [#1166](https://github.com/CrayJThiemsert/vero-lite/pull/1166) / [#1167](https://github.com/CrayJThiemsert/vero-lite/pull/1167) / `docs/plans/done/0105-*.md` |
| 2026-08-14 | **s229 — R8's PLAN-reference guard was blind to glob refs (`NNNN-*.md`, the form registries use) since s183; #1153 closes it.** The one live dead pointer had been dead since s216 and was **never reported once** — including by the commit that fixed the stream-2 row beside it. Resolves globs through the **same MOVED-not-MISSING predicate**; `Path.glob` would descend into `done/` and fail **OPEN**. | `ee968e5` (head_commit) / [#1153](https://github.com/CrayJThiemsert/vero-lite/pull/1153) / `docs/runbooks/memory-architecture.md` §R8 |
| 2026-08-13 | **s228 — PLAN-0104 Step 7 EXECUTED under a typed §8 go; AC-7 CLOSED, PLAN COMPLETE 8/8 and ARCHIVED.** 🔴 **The fresh 12/13 RETIRES the prior figure as non-comparable — it does NOT beat it** (prompt changed in #1149; gold grew 12 → 13), and the obvious citation is a trap: that file's arm-comparison `11/12` is **text-to-SQL**, not engine-A's. nl-06's miss was re-run, failed again, investigated — **not a regression; the victim moved**. | `ad2804d` (head_commit) / [#1151](https://github.com/CrayJThiemsert/vero-lite/pull/1151) / `benchmarks/nl_query_feasibility/RESULTS.md` §Addendum |
| 2026-08-13 | **s227 — PLAN-0104 Steps 2+3+4 as ONE PR (#1148) and Steps 5+6 (#1149); Steps 1–6 COMPLETE.** 🔴 **AC-5 is a hard merge dependency, not a preference:** no commit may exist where `count`+`group_by` validates while `_count` still collapses groups — that state answers with a **silently wrong** number, worse than the refusal it replaces. | `75243b0` / [#1148](https://github.com/CrayJThiemsert/vero-lite/pull/1148) / [#1149](https://github.com/CrayJThiemsert/vero-lite/pull/1149) / `docs/plans/done/0104-*.md` |
| 2026-08-13 | **s226 — PLAN-0104 DRAFTED, its three SD slots RULED (Cray, typed), Step 1 SHIPPED.** 🔴 The `count`+`group_by` refusal had **three independent enforcers**, so no single edit changed behaviour and the circulating *"≈ one PR + tests"* price was wrong. 🔴 The gold guard was **VACUOUS** — it restated the numbers instead of reading `SQL_EXPECT`, so two wrong tokens scored `wrong` every run, silently. | `fa8a61c` / [#1144](https://github.com/CrayJThiemsert/vero-lite/pull/1144) / [#1145](https://github.com/CrayJThiemsert/vero-lite/pull/1145) / `docs/plans/done/0104-*.md` |
| 2026-08-12 | **s225 — PLAN-0103 Step 6 SHIPPED and nine of eleven ACs CLOSED.** 🔴 **Verifying an inherited "closed in substance" claim rather than relaying it found two ACs FALSE** — AC-7's text described an approval the engine refuses; AC-6's named guard had never existed. **Both fixed, not ticked over.** ⚠️ AC-10 + AC-11 stay OPEN. | `b229fcd` / [#1139](https://github.com/CrayJThiemsert/vero-lite/pull/1139) / [#1140](https://github.com/CrayJThiemsert/vero-lite/pull/1140) / [#1141](https://github.com/CrayJThiemsert/vero-lite/pull/1141) / `docs/plans/0103-*.md` |
| 2026-08-12 | **s224 — RULED (Cray, typed): PLAN-0103 SD-8 = (iii)**, narrative copy in the Act card's place, Step 6 builds it; accepted cost: copy with no oracle. 🔴 **The slot's own premise was MEASURED FALSE** — the Act card renders on **no** published profile, suppressed by PLAN-0100 Step 3 *before* SD-8 was authored, so `was an error`, not `superseded by new info`. | `853d827` (head_commit) / [#1135](https://github.com/CrayJThiemsert/vero-lite/pull/1135) / `docs/plans/0103-portal-landing-and-per-system-published-profiles.md` §SD-8 |
| 2026-08-12 | **s223 — the MS-S1 secrets-ACL exposure is CLOSED and PROVEN, under two typed §8 gos.** RULED (Cray, typed): tighten as a **ladder A → C**, canary procurement only, recreate `oct-energy` for real, and **MOVE** the leftover backup into the tightened directory. 🔴 **A same-volume move keeps the OLD ACL — measured.** Each rung believed only on a force-recreate; verifier seen RED→GREEN. | `b4cb860` (head_commit) / [#1132](https://github.com/CrayJThiemsert/vero-lite/pull/1132) / [#1133](https://github.com/CrayJThiemsert/vero-lite/pull/1133) / `docs/logs/2026-08-12-ms-s1-secrets-acl-tightening.md` |
| 2026-08-12 | **s223 — RULED (Cray, typed): J4 ("run the full `tests/` before pushing") stays BINDING but is evaluated PER ACTION** — against the commit(s) being pushed at evaluation time; earlier uncovered pushes are residual gaps, not a standing FAIL. Rationale: **a criterion no future work can turn green is defective, not strict.** ✅ **R2 carve-out DISCHARGED s228** — rehomed to the lesson, so this row is now a pointer like any other. | `docs/lessons/0029-verify-full-suite-not-subset.md` §Addendum (rehomed s228) |

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

- [ ] **PLAN-0106 — fleet's OWN in-app case-persistence disclosure (ADR-0037 D2.4). Steps 1–4 SHIPPED s232 (#1178, #1179); **D2.4 is DISCHARGED** and it is no longer a fleet gate.** ⚠️ **`Status: Draft`, AC-1..AC-6 `[x]`, AC-7 `[ ]` — RULED (Cray, typed, s233).** AC-7's evidence is fleet's Step-10 **go record, which does not yet exist**; the PLAN closes 7/7 and archives **with fleet's bring-up, not before**. **Read the PLAN, never a restatement:** `docs/plans/0106-fleet-case-persistence-disclosure.md` (§Closure evidence · §Surfaced decisions). _[Trimmed s233 per R2 s141.]_
- [x] **PLAN-0105 — fleet's 90-day in-app case retention: COMPLETE 11/11, ARCHIVED s231.** **Read the archived PLAN, never a restatement:** `docs/plans/done/0105-fleet-case-retention-in-app-deletion.md` (§Surfaced decisions for SD-1..SD-4; the child-to-child FK ordering defect and its guard). ✅ s232 corrected its false "is factored" claim by EXTRACTING `delete_case()` (#1171); failure semantics RULED **(b)**. ⚠️ **What `Complete` does NOT mean:** AC-11's RoPA is still Cray's, and the **DSR-on-request path stays undefined — requester identification in particular is genuinely undesigned**; `delete_case()` is the mechanism half only. _[Trimmed s233 per R2 s141.]_
- [x] **PLAN-0104 — `count` WITH `group_by`: COMPLETE 8/8, ARCHIVED s228; discharges PLAN-0100 D-4.** **Read the archived PLAN and the evidence, never a restatement:** `docs/plans/done/0104-nl-query-count-with-group-by.md` · `benchmarks/nl_query_feasibility/RESULTS.md` §"Addendum — PLAN-0104 Step 7 live evidence run". 🔴 **Do not re-derive: the 12/13 does NOT beat the prior `11/12` — that figure is RETIRED as non-comparable** (prompt changed, gold grew 12→13), and the engine-A prior is in its own AC-9 addendum, not the arm-comparison table. ⚠️ **Live:** the Step 7 dumps under `.claude/benchmark-results/` are **untracked and NOT gitignored** — no copy in history, nothing stopping an accidental commit. _[Trimmed s233 per R2 s141.]_
- [x] **`_count`'s week silent-drop — CLOSED s228, RULED (a), SHIPPED [#1156](https://github.com/CrayJThiemsert/vero-lite/pull/1156).** The guard and its named set `_WEEK_ROLLUP_BLIND_TO` live in `services/engine/run_query.py` — **read the code, never a restatement.** 🔴 **Do not re-derive:** the guard keys on the **FILTER** as well as `group_by` (a bare `started_week` filter reaches the branch), and because the set is named, **(b) would SHRINK it, not delete the guard** — (a) is the honest floor, not a stopgap. ⚠️ **(b) is still the better ANSWER, unscheduled** — no gold case asks for it today. _[Trimmed s233 per R2 s141.]_
- [ ] **🆕 A THIRD silent drop, same family, STRICTLY LARGER — found s228, UNRULED.** The aggregate paths (`_aggregate_duration` via `_keep`, and `_aggregate_benefit`) filter on **procedure/status only — neither reads `started_week`** — so an aggregate carrying that filter silently answers across **EVERY week**. 🔴 Worse than the `count` case just closed: what vanishes is **the week filter itself**. Reachable — `started_week` is in `DIMENSIONS` and in the published descriptor, so the model emits it there. Found by following through on the `goal-evaluator`'s SD-1, **not by a test; no test covers it, which is why it survived**. Not repaired in #1156 (different site, outside the ruling). **Two dispositions, NEITHER ruled:** (a) refuse it, or (b) make the filter work.
- [ ] **🆕 A FOURTH silent drop in the NL engine — found s232, MEASURED at `5425822`, UNRULED, and recorded here because NO other artifact carries it** (grep across `docs/ services/ tests/` returned zero hits before this row). Same family as the third, **different axis: what vanishes is `group_by` itself, not a filter.** `_validate_query` **permits** `group_by` on aggregate ops — its guard is `query.group_by and query.operation not in _AGGREGATE_OPS and query.operation != "count"` (`services/engine/nl_query.py:571`) — and `_run_query_schema` binds the enum to `DIMENSIONS` (`run_query.py:420`), so the model **does** emit it. But **both** aggregate paths construct `AggregateResult(...)` with **no `groups` argument** (`run_query.py:330` duration, `:364` benefit) and `groups` defaults to `{}`. 🔴 **The count path at `:248` DOES pass `groups=groups`** — so the omission is a two-site gap in an otherwise-correct design, not a missing feature. **Effect:** *"average duration per procedure"* validates, executes, and silently returns **one ungrouped number**. ⚠️ **No test covers it**, which is why it survived PLAN-0104's whole build. Same two dispositions as the third drop, neither ruled: **(a) refuse it, or (b) make it group.**
- [ ] **🆕 `deploy.py` builds from a compose file that NO LONGER EXISTS — found s232, MEASURED, UNFIXED. NOT a fleet blocker; it breaks the next ENERGY redeploy.** `build_and_ship` sets `compose_file = repo_root / "deploy" / "published" / "docker-compose.yml"` (`deploy/published/deploy.py:242`), and that path was removed when PLAN-0103 Step 4 moved every compose into per-profile directories — `ls` confirms it is absent at `5425822`. ⚠️ **The same module's OTHER references were migrated correctly** (`_HOST_COMPOSE` and `_HOST_READ_PATHS` both name `oct-energy/docker-compose.yml`), so this is one straggler, not a systemic miss — which is exactly why reading the neighbours would not have caught it. 🔴 **No test guards it:** `tests/deploy/test_deploy.py` pins `_PROJECT`, the container names and `_HOST_READ_PATHS`, but **not** this path. Fix is a one-line repoint **plus** the guard that would have caught it; neither is scheduled.
- [ ] **`nl-03`'s `SQL_EXPECT` is UNDER-SPECIFIED — RULED (Cray, typed, s226): RECORD it, do NOT change the token now.** Its list omits `event-reading-08`, which `gold.yaml` lists among nl-03's three expected ids. 🔴 **This is a DIFFERENT defect class from the nl-02/nl-05 tokens Step 1 repaired, and keeping the distinction is the point of the row:** `score_sql` matches a **subset**, so nl-03's present tokens are **correct** and the case still scores `correct` — **the oracle is WEAKER than it should be, not WRONG**, where nl-02/nl-05 were factually wrong and therefore scored `wrong` on every run. ⚠️ **Adding the token would make the benchmark STRICTER:** a model whose SQL filters by unit would flip nl-03 from `correct` to `wrong`, which **changes what the measured numbers mean and breaks comparability with earlier runs**. That makes it a **measurement decision, not a typo fix** — which is why it is recorded rather than patched. On the same basis, noted and deliberately not acted on: **`score_sql` matches tokens as SUBSTRINGS**, so an expected `"1"` would match a result of `"21"`.
- [ ] **PLAN-0103 — vero-lite's side of the multi-vertical portal. `Status: Draft`; AC-1..AC-9 CLOSED, only AC-10 + AC-11 remain `[ ]`.** 🔴 **One live gate: AC-11's RoPA instance — Cray's as controller, and the LAST thing standing between fleet and its bring-up.** The typed §8 go is a *consequence* of it, not a separate gate: AC-11 requires the go record to cite the RoPA **by path**. ✅ The other four s232 gates are closed — PLAN-0106 (#1179), the two Cloudflare artifacts and four host secrets (evidence: `docs/logs/2026-08-15-fleet-cloudflare-artifacts-and-secrets-staging.md`, marked RECONSTRUCTED). ⚠️ **Requester identification for the DSR path is genuinely undesigned** — `repair_case.opened_by` has no FK, so a request matches rows only by content. **Read the PLAN, never a restatement:** `docs/plans/0103-portal-landing-and-per-system-published-profiles.md` (§The hard boundary · §Surfaced decisions · §Steps). _[Trimmed s233 per R2 s141 (pointer rule). The per-Step narrative, the no-portal-repo ruling and the SD slots are in the PLAN; `deploy.py` is NOT a blocker per `deploy/published/oct-fleet-maintenance/README.md:247-253`; the s225 G1/G2 correction is in `docs/status-archive/2026-h1-status.md:1250` and `2026-h1d-current-focus.md:140-142`. 🔴 That correction previously cited `CLAUDE.md` §6 as stating **G2 fires only when a numbered artifact does not yet exist** and **G1 is scoped to `Status: Accepted`** — §6 does NOT say either; it stops at the gates being scoped to `docs/adr/` + `docs/plans/`. Re-pointed to the archive, which does hold it.]_
- [x] **Fleet's Operate-tab seed flag — CLOSED s232 ([#1170](https://github.com/CrayJThiemsert/vero-lite/pull/1170)):** `OCT_DEMO_SEED_OPERATE` flipped `false`→`true`, so Tab H no longer opens empty on bring-up. The flag and its corrected comment live in `deploy/published/oct-fleet-maintenance/published.env`; the four README corrections in that profile's `README.md` (#1173). 🔴 **The durable shape — three artifacts described one fact and only `main.py`'s was right, because it was edited alongside the code; prose has no consumer, and ruff, mypy and 4093 tests stayed silent eleven sessions.** _[Trimmed s233 per R2 s141.]_
- [ ] **🆕 The apex domain leaks in ONE archived file — found s231 by repo-wide grep; UNRULED and not urgent.** The only carrier is `docs/plans/done/0100-exposure-published-demo-surface.md` (5 places), matching the s222 correction recorded in ADR-0036. ⚠️ **Outside the existing guard's reach:** `test_no_unknown_domain_appears_in_the_deploy_docs` scans `deploy/published/` and the published-demo runbooks, **not `docs/plans/`**. Three options, none ruled: scrub the file, widen the guard, or accept it knowingly. 🔴 **RE-PRICED s232 — "widen the guard" is NOT a one-file flip.** MEASURED: widening it to `docs/plans/` reddens **FOUR** files, not one — the archived PLAN-0100 **plus** three other archived plans carrying unrelated third-party domains (`docs/plans/done/0013-*`, `done/0014-*`, `done/0033-*`). So the option is **a flip PLUS three deliberate allowlist additions**, which that constant's own comment calls an act needing intent. **Reference BY PATH ONLY — the domain is not named here.**
- [ ] **The ฿ realized-vs-projected join — RECORDED ON ITS MEASURED BASIS, because the version circulating in session notes is PARTLY FALSE and it was ranked #1 next work on the strength of the false part.** ✅ **True:** the realized side already carries `total_thb` and `run_id` on the **same** `ExportRow` (`services/db/repair_spend_export.py`, linked via `RepairCaseRunLink`), so **no migration is needed**. 🔴 **False as circulated:** that `benefit_rollup` in `services/db/run_analytics.py` "already extracts `net_benefit_thb` by `run_id`". It does **not** — it aggregates by currency × procedure × facet-kind × day and touches `run_id` only inside a `count(distinct …)`, so it yields **no per-run figure at all**. **Therefore the join needs a NEW per-run aggregation, not a reuse of `benefit_rollup`'s output**; the `GROUP BY run_id` pattern to copy is the per-run SUM inner subquery in that same module. ✅ **RE-PRICED s226 — MEASURED, not estimated: ~150–250 lines across 6–7 files, ONE PR.** The circulating **"~40 lines by reusing `benefit_rollup`" framing was CHECKED and is WRONG**. 🔴 **Three constraints the old framing missed, all TEST-PINNED:** (a) `run_analytics.py`'s **SD-8(a) discipline FORBIDS O(runs) result shapes**, pinned by `tests/services/db/test_run_analytics.py` with statement capture — so **"per-run rows on screen" is a design decision, not a mechanical add**; (b) `tests/api/test_export_cover_ui_contract.py` asserts **set equality** against an **empty** `_UNREAD_COVER_FIELDS`, so a new `ExportCoverResponse` field **must ship with its `view-export.js` tile in the SAME PR** or CI reddens; (c) **`/insights/impact` is ABSENT from fleet's Cloudflare allowlist**, so the figure **must ride the existing cover response**. 🔴 **CORRECTED s232, `was an error`: this row called `/insights/impact` "the only existing consumer of the projected side" and it is NOT.** MEASURED — `_aggregate_benefit` (`services/engine/run_query.py:334`, consuming `run_analytics.benefit_rollup` at `:343`, dispatched at `:380`) is a **second** consumer, and it **IS reachable on fleet** via the allowlisted `^/query$`. Constraint (c)'s *conclusion* survives — the figure still rides the cover response — but the premise under it was false, and a reader pricing this work from the old sentence would mis-scope the blast radius. ⚠️ **Also corrected: "SD-8(a) is test-pinned by statement capture" holds only for the ELEVEN primitives hard-coded at `tests/services/db/test_run_analytics.py:253-268`, and only when Postgres is reachable** — a *new* O(runs) reader would **not** automatically redden CI. Pattern to copy: the per-run `GROUP BY` in `run_duration_totals` (`run_analytics.py:448`), **not** `benefit_rollup` (`:521`). Lands on **Tab J**, which fleet publishes.
- [ ] **Demo-key rotation cadence — CRAY'S, posture not code.** Fleet's README documents how to **generate** a persona key pair but says nothing about **when to rotate**. Measured s225: `git grep -i -e rotate -e rotation` under `deploy/published/oct-fleet-maintenance/` returns **zero** matches. The keys are served to the browser by ruling, so they are **public the moment fleet is reachable** — which makes the cadence a real posture question rather than a nicety. No code change is implied; the answer is Cray's.
- [ ] **Ungated items rehomed s219 out of the `next_action` frontmatter — they survived ONLY there, and R3 caps that field to one short line.** (1) ✅ **PLAN-0103 Step 9's MS-S1 headroom is MEASURED s221** (`docs/logs/2026-08-10-oct-energy-migration-phase2-and-step9-headroom.md`) — RAM and CPU do not constrain a second or third published system, and AC-10's first clause is discharged. ⚠️ **ADR-0036 OQ-2 does NOT follow from it and remains OPEN:** the aggregate in-flight LLM posture is a different question — the constraint on a second *assisted* system is the resident model and concurrent in-flight calls, not container footprint — and one term in the projection (Postgres idle) is declared unmeasured rather than folded silently into the total. (2) **The public one-pager v2 — now has its OWN row below** (design-ready; destination RULED s226). (3) ✅ **ADR-0037 D4 is RULED and CLOSED s232 (#1174, #1175): OQ-2 = (a) text-by-reference** — the chain holds the case id, the erasable row holds the text (its precondition was s222's D2.7 measurement, #1124: case text does not reach the chain on either path, and `case_id` stays recoverable). The recorder's own free text — `WaiverInvocation.justification` and the ratification `note`, a named internal principal's, not the visitor's — = **(i)**: its own RoPA line, stated plainly as **non-erasable**. ⚠️ **OQ-1 had been ruled since s231 while the ADR's text still read OPEN** — retroactive drift, closed in the same PR; check the artifact, not the ruling's date. ⚠️ **The one hole the oracles do not close stays ACCEPTED (Cray, typed, s222):** a middle-slice carrier is invisible to both; revisit if an audit payload gains a field legitimately holding a SLICE of operator-entered text. (This is the durable home; the Recent Decisions row rotates.) (4) **Edge cache-purge needs a Cloudflare API token = a new secret + host-state**, which is why the purge step in the PLAN-0100 row below is not simply "add a step". _(The remainder of that field — the `nl_query.py` seam count, versioned font URLs, the unpinned `OLLAMA_KEEP_ALIVE` — is homed in the PLAN-0104 and PLAN-0100 rows and is not duplicated here.)_
- [ ] **Public one-pager v2 — DESIGN-READY; a WRITE job, not a design job. ✅ RULED (Cray, typed, s226): if it is built, its output goes to `docs/strategy/private/` (GITIGNORED), NOT tracked `docs/`.** 🔴 **Recorded here because it had ZERO tracked home:** `git grep` across `docs/ services/ tests/ benchmarks/` returned **0 hits** — it lived only in a gitignored handoff, which is exactly how a ruling was lost in s223. **Grounded status, because it changes the item's cost:** a complete spec already exists at `docs/strategy/private/2026-08-10-onepager-v2-spec-and-q5-q12-triage.md`, carrying a **locked six-block structure**, the **bilingual roof line and CTA already written**, a **must-NOT-contain list**, and a **14-row claim→evidence ledger** pinning every claim to DEMO / PILOT / DESCRIPTION. Source material verified present: the wedge one-pager, the b3 talking points, the GTM ammo pack, and all three `deploy/published/*/card-copy.md`. ⚠️ **One honesty constraint the spec itself flags:** the DOA/SoD governed-approval claim is **`DESCRIPTION`, not `DEMO`** — the spec calls this **"the lead pillar's gap"**. 🔴 **CORRECTED s232, `was an error` — the STATED REASON was false, though the conclusion survives on a different basis.** This row (and the spec) said the gap exists *"because Tab G is not published"*. **Tab G IS published:** `deploy/published/oct-procurement/published.env:46` ships `UI_PUBLISHED_VIEWS=G,F` and procurement went live s222. The real basis: **the Act card renders on NO published profile** because event mode is suppressed — so the governance *moment* is viewable while the approval *action* is clickable nowhere public. ⚠️ **Consequence nobody has acted on: the spec's own stated unblock trigger has therefore ALREADY FIRED**, and its claim→evidence ledger row was never upgraded. **Reference that path BY PATH ONLY — pricing and spec body never get copied into STATUS.**
- [ ] **Landing-layer PLAN — CLOSED s226 as SUPERSEDED. NOT work to do; this row exists so nobody schedules it again.** PLAN-0103 Step 8 consumed the repo-side half (AC-9 ticked), and ADR-0036 D1/D2 place the landing surface, ingress map and Access policies **outside this repo** — a vero-lite file enumerating published systems is guard-rejected as a *shadow ingress map* (`tests/deploy/test_published_profiles.py`). Cray ruled s221 (typed): **no portal repo.** 🔴 **The remainder is CRAY'S DASHBOARD WORK — nothing for Code, no dispatch owed.** _[Trimmed s233 per R2 s141; measurement narrative in `docs/status-archive/`.]_
- [ ] **PLAN-0100's residuals outlive the PLAN** (COMPLETE 13/13 and ARCHIVED s216; the demo is LIVE, REDEPLOYABLE and DRIVEN). **Read the archived PLAN, never a restatement:** `docs/plans/done/0100-exposure-published-demo-surface.md` (§"Step 11 closure verdict"; §"Defects the live run found" for D-1..D-5, incl. the *transient* D-5 Safe-Browsing flag on the Access login callback, cause UNDETERMINED; §Instrument failures). _[s222: the completion narrative is dropped per R2's ratified Active-TODO rule — `[x]` items older than the session window go, git history + the archived PLAN hold them. Only the live residuals stay.]_ **Live, and recorded ONLY here:** (1) ✅ **D-4 is FULLY DISCHARGED — RULED s217 (Cray, typed): option (a), teach the engine; delivered as PLAN-0104, COMPLETE 8/8 and ARCHIVED s228 (#1145, #1148, #1149, #1151).** The engine executes `count` WITH `group_by` end-to-end, and AC-7's live evidence closed s228 — **nothing in D-4 is outstanding.** _[Corrected s226 IN PLACE, `superseded by new info`: this item read "nothing built, no PLAN drafted, still the largest ungated Code item" and carried the seam analysis inline. A PLAN now owns both, so the analysis is not kept in two divergent copies — it lives in the PLAN and, in summary, in the PLAN-0104 Active TODO above. The demand this item existed to make — **"re-price before scheduling; '≈ one PR + tests' rested on the four-seam count"** — is **DISCHARGED**: drafting re-priced it, and the answer is that the refusal has **three independent enforcers**, so no single edit changes behaviour. The s225 measurement it carried (`group_by` touched at **eight or more** sites, the decisive omitted one being the system prompt) is rotated to `docs/status-archive/2026-h1-status.md`.]_ **Read `docs/plans/done/0104-nl-query-count-with-group-by.md`, never a restatement.** (2) **No cache-purge step or versioned font URLs** in the redeploy runbook — nothing in the pipeline purges the edge and `?v=cNN` does not reach fonts; a purge needs a Cloudflare API token = a new secret + host-state. (3) **`published.env` pins no `OLLAMA_KEEP_ALIVE`**, so the published surface silently inherits the code default of 30m.
- [ ] **Assembly-cost axis — MEASURE it before an ADR argues it (Cray typed s197); nothing built, no PLAN drafted.** Build the tripwire that puts a number on assembly cost first, *then* draft the ADR on top of that number — the ordering is the ruling. **The series measured so far is banked HERE because it is banked NOWHERE ELSE in the repo — no test, no doc, no PLAN holds it:** churn per vertical went **1:1.8 → 1:6 → 1:1.1**, i.e. **spiky, not falling**, which is the shape any ADR on this axis has to argue against. Left unbanked it dies at the next context reset. 🔴 **BLOCKING GAP, measured s226 — the SERIES is banked here, but the METHOD is banked NOWHERE AT ALL:** no numerator, no denominator, no window is recorded anywhere in the repo. **A tripwire built today therefore emits a number that CANNOT be compared to those three.** One decision slot must be filled **before any build**: pin the metric definition (numerator / denominator / window), and rule whether the three banked figures are **reproducible under it** or must be **declared unrecoverable**.
- [ ] **Seam-scoped mutation-testing CI — a PLAN candidate, NOT built.** Surfaced s188 as the one CHECKABLE variant the scenario-test hook rejection does not cover; **rehomed here s191** when its parent `[x]` row was pruned, because STATUS was its only home. A CI job that requires the scenario suite to REDDEN under a seam mutation: ritual compliance cannot fake it, since an empty or stubbed scenario suite stays green under mutation — exactly what a file-existence hook would miss. Rationale: `CLAUDE.md` §8's scenario-test bullet. 🔴 **SCOPING BLOCKER, measured s226 and RE-MEASURED s232 — scenario tests cannot be machine-scoped today, by marker OR by filename:** `pyproject.toml` still defines exactly **two** pytest markers, `slow` and `host_state`, so there is **no `scenario` marker**; and `tests/api/test_fleet_pilot_scenarios.py` is **plural** where every sibling is singular `_scenario.py`. ⚠️ **The count in this row was STALE and is corrected — trust the measurement, not the remembered number:** s226 recorded "eight sibling files"; the tree at `5425822` holds **13 files / 63 test functions** (12 singular + the 1 plural), spanning `tests/api/`, `tests/services/db/` and `tests/services/engine/` — **not `tests/api/` alone**. 🔴 **CI runs bare `pytest -q` with no `-m`, so `CLAUDE.md` §8's binding scenario-test rule is enforced by NOTHING mechanical today** — it holds only because each PLAN's ACs restate it. ✅ **XS prerequisite, worth doing on its own and independent of the CI job: add a `scenario` marker and normalise that filename** — **rename blast radius is ZERO** (repo-wide grep finds one hit, this row's predecessor). The CI job itself stays effort **L**, with three unresolved design questions — what **marks** a scenario test, what **enumerates** a seam, which **mutation engine**.
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
- [ ] **PLAN-0102's two residues outlive the PLAN** (retire L1 loop-detect — COMPLETE 11/11 and ARCHIVED s217, #1096; L1 is gone from all four hooks, L2/L3/L4 intact and asserted so). **Read the archived PLAN, never a restatement:** `docs/plans/done/0102-retire-l1-loop-detect.md` (§Context for the measurement + the s180 "0 denies" correction to a **≥ 56** floor; §Governance; §"Corrections found by executing this PLAN"). _[s222: completion narrative dropped per R2's ratified Active-TODO rule; residues kept per its carve-out.]_ **Both non-gating and recorded ONLY here:** (1) **`observe()` is now callerless and was deliberately kept** — deleting it turns `_record`'s `bump` into a constant and pulls a refactor into the function every surviving L2/L3/L4 increment flows through; revisit only if that module is reworked anyway. (2) The **forwards-call-graph gap** behind all three PLAN defects is a *method* fix owed to the next excision PLAN, not a code fix — no artifact carries it yet.
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
