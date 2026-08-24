---
last_updated: 2026-08-24T10:08:36+07:00
session: 251
current_batch: "s251 — one PR (#1275): PLAN-0113 Step 1 lands the `scope_by`/`when_absent` read grammar on `StepInput`, consuming nothing yet; AC-1 CLOSED."
current_actor: code
blocked_on: "Nothing. Main green, 0 open PRs, tree clean. Owed: PLAN-0107 AC-9 re-scope, PLAN-0109's three ruled-content defects, PLAN-0108 label ordering, the `MEMORY.md` (Tier-0) consolidation."
next_action: "PLAN-0113 Step 2 — the `trigger_context` wire; Step 1 is merged with AC-1 CLOSED, and the PLAN stays `Draft` on purpose."
head_commit: 968b34e
recent_commits: [968b34e, 98b3cda, 17defa0, 9b16ebf, 31e5e55, 0d9b808, 33a4887, 857767c, 98463e7, e05cfa3]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 251, 2026-08-24 (head_commit `98b3cda` → `968b34e`) — ONE PR
> MERGED ([#1275](https://github.com/CrayJThiemsert/vero-lite/pull/1275)), 0
> open, CI green, tree clean. **PLAN-0113 Step 1 SHIPPED and AC-1 is CLOSED:
> the `scope_by` / `when_absent` read grammar now lives on `StepInput` and
> consumes NOTHING yet** — it renders SB-1..SB-6 of the ADR-016 amendment
> (2026-08-23) as schema, and the run path is untouched until Step 2.**
>
> 🔴 **The pin choice is the load-bearing decision, and it went AGAINST the
> nearest-looking precedent.** `scope_by` is governance-pinned
> **only-when-supplied** (ADR-0034 D6), following `transform` rather than the
> always-present `reads` / `join` / `project` shape it sits beside. An
> always-present key would have moved **all six verticals' config hashes** and
> made **every in-flight run refuse at resume** — a migration nobody asked for,
> bought back by one serialization decision.
>
> ✅ **The no-op claim was MEASURED, not asserted:** all **13 procedures across
> all 6 verticals** are byte-identical HEAD-vs-tree — **fleet included, because
> the named oracle guards only five**, so the sixth was checked rather than
> assumed covered.
>
> 🔴 **The nine-probe non-vacuity battery FAILED ITS OWN CRITERION TWICE, and
> the instrument was repaired both times** — never the criterion, per
> `CLAUDE.md` §8's *"suspect the probe and control selection first"*. Judged
> independently by the `goal-evaluator`: **J1 / J2 / J3 all PASS.**
>
> ⚠️ **Two Code-decided points were Cray-ratified at merge (typed, s251):**
> `from:` is **required-explicit**, and there is a **fourth load-gate refusal
> that SB-3 does not enumerate** — `when_absent` supplied with no `scope_by`.
> Re-checked at this reconcile: SB-3's body still names three refusals, all of
> them `scope_by`-present cases, so the fourth is carried by the PR and this
> record only. Tracked as an Active TODO below.
>
> **Not started: PLAN-0113 Steps 2–8.** Step 2 is the `trigger_context` wire;
> PLAN-0113 stays `Status: Draft` **on purpose**.

> **Session 250, 2026-08-24 (head_commit `0d9b808` → `98b3cda`) — FOUR PRs
> MERGED ([#1271](https://github.com/CrayJThiemsert/vero-lite/pull/1271), [#1272](https://github.com/CrayJThiemsert/vero-lite/pull/1272),
> [#1273](https://github.com/CrayJThiemsert/vero-lite/pull/1273), [#1274](https://github.com/CrayJThiemsert/vero-lite/pull/1274)), 0 open, CI
> green, tree clean. A governance-plumbing session — no engine code moved, and
> what shipped is the machinery s251's build was then measured against.
> **In-Flight Discussions and the Current-Focus rotation ledger are CAPPED
> (Cray, typed, s250)** — the two sections R2 had never governed.**
>
> ✅ **The cap, in three clauses** (#1271): an In-Flight entry is a **pointer ≤
> ~600 chars**; the section holds **only discussions still OPEN** — one
> announcing its own closure has stopped being in flight; and it is **capped at
> 6 entries**. The rotation ledger keeps **only the current 4-session window**,
> each entry travelling into the archive with the block it explains. STATUS
> **53,048 → 48,645 B**, back under R1's 48 KB soft target.
>
> 🔴 **The backfill is the real finding: two Cray-ratified rules had never
> reached their enforcer at all.** The **s194 per-block 4,096 B cap** and the
> **s141 Active-TODO pointer rule** were absent from
> `.claude/agents/status-scribe.md` — zero hits, with a positive control
> proving the grep finds a rule that *is* there. Both sections happened to be
> compliant, **but not because the enforcer was enforcing them**. R2 now says
> it out loud: *a rule absent from its enforcer's input is, for that enforcer,
> not written* — `CLAUDE.md` §4's consumer test, measured.
>
> ✅ **The TODO that asked for the ruling is CLOSED** (#1272) — and at **638
> chars it was the last Active TODO over the s141 cap**, so that section is now
> 100% per-entry compliant.
>
> ✅ **The s245 block's one unhomed fact is REHOMED** (#1273): the four-day
> `.git/index.lock` root cause — a **SIGSTOP-suspended git process (`STAT=T`)
> holding the lock while not running** — now sits in
> `.claude/skills/git-workflow/SKILL.md` beside the recovery it explains.
> ✅ **PLAN-0113 Step 0's baseline is recorded** (#1274) at
> `docs/logs/2026-08-24-plan0113-step0-baseline.md` — the pre-change
> measurement Step 1's byte-identical claim is checked against.

> **Session 249, 2026-08-23 (head_commit `674a985` → `33a4887`) — TWO PRs
> MERGED ([#1268](https://github.com/CrayJThiemsert/vero-lite/pull/1268),
> [#1269](https://github.com/CrayJThiemsert/vero-lite/pull/1269)), 0 open, CI
> green verified on each exact head sha, tree clean. A Tab-H usability question
> became a ratified architecture reversal: **PLAN-0113 — scope an event-fired
> run to its firing case** — plus the ADR-016 amendment that reversal requires,
> Accepted the same session. This session was mostly DECISIONS; weigh them over
> the diffs.**
>
> 🔴 **PLAN-0112 SD-4 is REVERSED (Cray, typed, s249)** — from its s243 ruling
> **(a) accept the multi-case gate** to that ruling's rejected option **(b)
> scope the run to the firing case**. Classified **`superseded by new info`,
> NOT `was an error`**: (a) was correct in its context. Trigger: a Tab-H run
> stayed `WAITING_HUMAN` after an approval, and one accepted quote produced
> three approvals. Root cause measured — fleet's `intake` is a **fleet-wide
> scan**, so the event *triggers* the run but does not *scope* it, and a
> visitor's gate also decides both seeded demo cases.
>
> ✅ **Ten Cray-typed rulings landed, all as-recommended.** PLAN-0113: the SD-4
> reversal · D1 `when_absent` declared per-step in YAML · D2 the YAML names the
> field, so the engine never learns `case_id` · SD-1 `when_absent`
> required-explicit · SD-2 mirror the `join`/`project` governance
> classification · OQ-2 yes, an ADR-016 amendment · OQ-1 how Code records a
> supersession inside `docs/plans/done/`. ADR-016 amendment: OQ-1 closed
> two-member `when_absent` · OQ-2 join-path scoping base-read-only in v1 · OQ-3
> counted scope provenance is contractual — plus the amendment's own
> **Proposed → Accepted** ratification.
>
> 🔴 **OQ-1 closed a question that had been open for three sessions** — *"may
> Code edit `docs/plans/done/`?"*, the worked NOT-DECIDED example in the
> `decision-lookup` skill. Measurement narrowed it: the additive
> `## Post-archival amendment` form already had **6 merged precedents**, while
> an inline marker added to an *already-archived* PLAN had **zero**. Cray ruled
> **(b)** — appended amendment section **plus** a fixed one-line inline
> pointer, history never rewritten. **Scoped to supersession pointers only; the
> broad question stays open.**
>
> ⚠️ **Byproduct finding: ADR-016's running amendments index listed FIVE
> entries while the body carried SEVEN** — `Amendment (2026-07-11)` and
> `(2026-07-12)`, both Accepted and Cray-ratified, were never appended. ~6
> weeks of drift, now backfilled with a provenance note; the index reads
> **8 = 8**.
>
> **Not started: PLAN-0113 Steps 1–8.** Step 0b (the ADR) is the only one done
> — and it is precisely what unblocks Step 1, since `CLAUDE.md` §8 requires the
> ADR merged before any implementation PR.

> **Session 248, 2026-08-23 (head_commit `e126ebd` → `674a985`) — ONE PR
> MERGED ([#1265](https://github.com/CrayJThiemsert/vero-lite/pull/1265)), 0
> open, CI green, tree clean. The Recent Decisions R2 trim SHIPPED, the sibling
> of s247's Active-TODOs trim: **8 of 10 rows over the ~600-char pointer cap,
> now zero**; the table 7,408 → **5,743 B**, STATUS 53,133 → **51,743 B**, row
> count unchanged at 10.**
>
> 🔴 **The inherited "next place to cut" was measured WRONG, and correcting it
> changes what the next session should do.** The hand-off into this session
> named **In-Flight Discussions** as the remaining target. Measured: **R2 does
> not govern that section at all** — R2 names Current Focus, Recent Decisions,
> Active TODOs and Next Steps, and *"In-Flight"* appears **nowhere** in
> `docs/runbooks/memory-architecture.md`. Capping it would be **authoring a new
> rule, not enforcing one** — a Cray ruling, not a trim Code may perform. That
> section is 5,152 B across 9 entries.
>
> ✅ **The carve-out produced one rehome, and it ran FIRST.** Each row's
> *content* — not merely the paths it cited — was resolved against
> `git ls-files`; seven of eight already had a tracked home. The eighth, s240's
> **"ancestry is not content"** — a `git merge` reported success while the tree
> dropped every change from #1225, and `merge-base --is-ancestor` still
> answered YES — was rehomed into `.claude/skills/git-workflow/SKILL.md`, whose
> `description` was widened to trigger *"whenever about to trust that a
> `git merge` landed its content"*: surfaced at the moment of need, not merely
> filed. Re-pointed and verified before anything was trimmed.
>
> ⚠️ **A first sweep for orphaned facts produced THREE false positives**, each
> caught by going to the artifact: it searched STATUS's wording, not the
> artifact's — *"production agreed twice"* vs the log's *"second production
> confirmation"*; *"subagent never returned"*, which lives in
> `.claude/skills/fan-out-dispatch/SKILL.md`; `฿8,107,500`, which a test spells
> `8107500`. Trusting it would have rehomed three rows that had homes.
>
> ⚠️ **`674a985`'s subject lacks its `(#1265)` suffix** — `--subject` was
> passed to `gh pr merge --squash`, so `gh` wrote it verbatim instead of
> letting GitHub append the number. Not fixable without a force-push over
> protected `main`. **For that commit the PR number is recoverable only via
> `gh pr view 1265`, never from `git log --oneline`.**
>
> ✅ **All three R2-governed sections are compliant for the first time** —
> Active TODOs (#1263), Recent Decisions (#1265), Current Focus (zero over cap
> under the repaired blockquote bounding, #1264). R4 verified independently
> against `git show 2073e95:docs/STATUS.md`: **2 unchanged + 8 archived
> verbatim = 10, LOST = 0, in BOTH = 0.** STATUS is still **2,591 B over R1's
> 48 KB soft target**, far under the 64 KB hard ceiling that gates a commit —
> and no rule now covers the remainder.


_[Current-Focus rotation ledger — **CURRENT window only** (R2, Cray s250); earlier entries travel with their blocks into [`2026-h1d-current-focus.md`](status-archive/2026-h1d-current-focus.md), the full pre-trim ledger into [`2026-h1-status.md`](status-archive/2026-h1-status.md). The **session-244** block rotated there at the s248 reconcile, holding the window at four sessions; its PLAN-0112 Steps 3–4 substance lives in `docs/plans/done/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md`, and the #1249 ฿-facet fix it also carried holds its own Recent Decisions row. **It rotated on the window rule alone — NOT on a cap overage**: the repaired measure (#1264) — bounding each block by its own contiguous blockquote run rather than header-to-header — found zero CF blocks over R2's 4,096 B cap. The **session-245** block rotated there at the s249 reconcile, holding the window at four sessions and again on the **window rule alone, not a cap overage**; its witnessed-RED finding is now binding in `CLAUDE.md` §8 (#1253) and its G-13 / Step-5 substance sits in `docs/plans/done/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md`. ⚠️ **That block's one unhomed fact is REHOMED (s250)** — the four-day `.git/index.lock` root cause now sits in `.claude/skills/git-workflow/SKILL.md` beside the recovery it explains, where the reader staring at a stuck lock will actually meet it. The **session-246 AND session-247** blocks BOTH rotated there at THIS (s251) reconcile: this is a **two-session reconcile** (s250 + s251), so two blocks enter and two leave, holding the window at four. Both rotated on the **window rule alone, not a cap overage** — s246's PLAN-0112-COMPLETE and live-walk substance lives in `docs/plans/done/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md` + `docs/logs/2026-08-22-s246-*.md`, s247's trim-and-split substance in `docs/runbooks/memory-architecture.md` §R2 and the `2026-h1h-status.md` header, and each keeps its own Recent Decisions row. **The s250 reconcile rotated no CF block** (its four PRs were governance plumbing), so the ledger entries for the s246 and s247 reconciles — the ones this reconcile drops — travel into the archive with the blocks they explain.]_


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
| 2026-08-24 | **s251 — ONE PR (#1275): PLAN-0113 Step 1 SHIPPED, AC-1 CLOSED — the `scope_by`/`when_absent` read grammar lands on `StepInput`, consuming nothing yet.** Governance-pinned **only-when-supplied** (ADR-0034 D6, the `transform` precedent): an always-present key would have moved all six verticals' config hashes and made every in-flight run refuse at resume. 🔴 The nine-probe battery **failed its own criterion twice** — instrument repaired, criterion never relaxed. ⚠️ Two Cray-typed ratifications at merge: `from:` required-explicit, and a **fourth load-gate refusal SB-3 does not enumerate**. | `968b34e` / [#1275](https://github.com/CrayJThiemsert/vero-lite/pull/1275) / `docs/plans/0113-*.md` |
| 2026-08-24 | **s250 — FOUR PRs (#1271–#1274): In-Flight Discussions and the Current-Focus rotation ledger are CAPPED (Cray, typed)** — pointer ≤ ~600 chars · OPEN-only · ≤ 6 entries; the ledger keeps the current window. 🔴 **The enforcer had never received two rules Cray ratified long ago** — the s194 per-block cap and the s141 Active-TODO rule were absent from `.claude/agents/status-scribe.md` entirely; both backfilled. STATUS 53,048 → **48,645 B**. ⚠️ The four-day `index.lock` root cause (a SIGSTOP'd git process, `STAT=T`) rehomed into the git-workflow skill. | `98b3cda` / [#1271](https://github.com/CrayJThiemsert/vero-lite/pull/1271) / `docs/runbooks/memory-architecture.md` |
| 2026-08-23 | **s249 — TWO PRs (#1268, #1269): PLAN-0112 SD-4 REVERSED (Cray, typed) — an event-fired run is scoped to its FIRING CASE**, drafted as PLAN-0113 with the ADR-016 amendment it requires Accepted the same session; `superseded by new info`, not an error. 🔴 Ten rulings, all as-recommended. 🔴 **OQ-1 closed a 3-session-old question** — Code may append `## Post-archival amendment` + one inline pointer in `done/`, **supersession pointers ONLY**. ⚠️ ADR-016's amendments index read 5 against 7 body sections; backfilled, now 8 = 8. | `33a4887` / [#1269](https://github.com/CrayJThiemsert/vero-lite/pull/1269) / `docs/adr/0016-*.md` |
| 2026-08-23 | **s248 — ONE PR (#1265): the Recent Decisions pointer cap went 8-of-10 rows over to ZERO** (7,408 → 5,743 B), the one fact tracked nowhere else REHOMED first into the git-workflow skill, then trimmed; R4: 2 + 8 = 10, LOST = 0. 🔴 **The inherited "next place to cut" was WRONG** — R2 does not govern In-Flight Discussions, capping it is a Cray ruling, not a trim. ⚠️ `674a985` lacks its `(#1265)` suffix — `gh pr merge --subject` writes verbatim. | `674a985` / [#1265](https://github.com/CrayJThiemsert/vero-lite/pull/1265) / `docs/runbooks/memory-architecture.md` |
| 2026-08-23 | **s247 — THREE PRs (#1261–#1263): the Active-TODOs pointer cap went 24-of-35 rows over to ZERO** (27,450 → 18,167 B), the archive split running first by Cray's ruling. 🔴 A home is what `git ls-files` says — the lone item without one was REHOMED, re-pointed, then trimmed; R4: 11 + 24 = 35, LOST = 0. 🔴 A failed pre-committed criterion was repaired by SCOPE, not threshold. 🔴 R9 is now tracked NOWHERE. | `e126ebd` / [#1263](https://github.com/CrayJThiemsert/vero-lite/pull/1263) / `docs/runbooks/memory-architecture.md` |
| 2026-08-22 | **s246 — THREE PRs (#1256–#1258): PLAN-0112 Steps 6 and 7 EXECUTED; COMPLETE 9/9, ARCHIVED, and the visitor flow proven LIVE.** 🔴 **The host had never received Step 5** — a week-stale checkout kept the accepted-quote ingress row out of production. 🔴 **AC-7(i)'s wording is MEASURED FALSE** — a fleet-wide `intake` makes every visitor run's gate decide the demo case too; production agreed twice. UNTICKED for Cray. | `38ef55e` / [#1257](https://github.com/CrayJThiemsert/vero-lite/pull/1257) / `docs/logs/2026-08-22-s246-*.md` |
| 2026-08-22 | **s245 — FOUR PRs (#1252–#1255): PLAN-0112 Step 5 SHIPPED, AC-2…AC-6 CLOSED — the governable moment reaches the published visitor.** 🔴 **THREE guards passed while protecting nothing:** enumerating `Math\.min\s*\(` missed `Math.min.apply`; `"acceptQuote(" in source` was satisfied by the function's own definition. **The instrument was wrong every time, not the artifact** — which promoted `CLAUDE.md` §8's witnessed-RED rule (#1253). 🔴 **G-13's prose set was FOUR, not two.** | `9d0c3ff` / [#1255](https://github.com/CrayJThiemsert/vero-lite/pull/1255) / `docs/plans/done/0112-*.md` |
| 2026-08-21 | **s244 — TWO PRs (#1248, #1250): PLAN-0112 Steps 3 and 4 BUILT — a visitor's accepted quote fires the governed run.** 🔴 **A SECOND composition failure beyond G-14** — SD-2(b) and SD-5(b) do not compose on the bridge's SD-P4 in-flight guard, which no key design routes around: every acceptance became a silent `SKIPPED_IN_FLIGHT`. 🔴 **Ordering fails with no error** — fire before `_refresh_case_events` and the gate is about ANOTHER truck. **No AC ticked yet.** | `a8c42b7` / [#1248](https://github.com/CrayJThiemsert/vero-lite/pull/1248) / `docs/plans/done/0112-*.md` |
| 2026-08-21 | **s244 — ONE PR (#1249): the Box-4 ฿ facet was UNREACHABLE, not missing.** Four of five ฿-producing verticals wrote `economic_impact` only into the action envelope while `benefit_rollup` reads `StepResult.reasoning_trace` — Tab J read ฿0 for all of them. Emission moved down to `ActionStepExecutor`, plus a run-scoped `(action_id, kind)` ledger without which procurement DOUBLE-COUNTED a run. **Standalone wiring fix; NOT a PLAN-0112 step.** | `6fce826` / [#1249](https://github.com/CrayJThiemsert/vero-lite/pull/1249) / `services/engine/procedures/action_step.py` |
| 2026-08-21 | **s243 cont. — ONE PR (#1246): PLAN-0112 Step 1 EXECUTED, AC-1 CLOSED — `run_procedure_endpoint` 403s without an authenticated human, before spec load and any DB write.** 🔴 **The only producer of a `PipelineRun` was the one door of three that did not fail closed** — `triggered_by: null`; PLAN-0110's G10(6) found it. 🔴 **Non-vacuity took TWO probes on DIFFERENT assertions** — deletion proves presence, RELOCATION proves placement. | `f52dbdc` / [#1246](https://github.com/CrayJThiemsert/vero-lite/pull/1246) / `docs/plans/done/0112-*.md` |

_[The two oldest rows (**s234, s233**) rotated to `docs/status-archive/2026-h1-status.md` at the s243 cont. reconcile, holding the table at ten. Two rows were added: the **s242 backfill** — Cray ruled it in, discharging the gap the s243 reconcile flagged, and its four rulings are no longer carried by narrative alone — and a **second s243 row**, because Step 1 is a BUILD event of a different kind from that session's rulings and folding it into the existing row would have written a row far over R2's ~600-char pointer cap. The oldest row (**s237**) rotated to the same file at the s245 reconcile, holding the table at ten; the s238 row followed at the s246 reconcile for the same reason. The **s239** row followed at THIS (s247) reconcile, again holding the table at ten. **Session 248 discharged the pointer-cap overage this table still carried: 8 of the 10 rows were over R2's ~600-char cap, and are now zero.** Each row's substance — not merely the path it named — was resolved against `git ls-files` before that row was shortened; the one fact tracked nowhere else, s240's *ancestry is not content*, was **rehomed first** into `.claude/skills/git-workflow/SKILL.md`, then re-pointed, then trimmed. All eight full originals are preserved verbatim in `docs/status-archive/2026-h1-status.md` (R4, move-never-drop). The **s240** row rotated to the same file at THIS (s248) reconcile, holding the table at ten. ⚠️ It is the one row whose fact was rehomed the session *before* it rotated — *ancestry is not content* now lives in `.claude/skills/git-workflow/SKILL.md`, and that skill's widened `description` surfaces it automatically — so its rotation drops nothing that STATUS was the sole carrier of. The **s241** row rotated to the same file at THIS (s249) reconcile, holding the table at ten. Its substance keeps two tracked homes — `docs/conventions/retired-claims.md` for the guard it shipped, and the *"the two s241 pre-commit guards are FLOORS, NOT CEILINGS"* entry in §Active TODOs for the live remainder — so it, too, rotates on the count rule alone. The two oldest rows (**s243**, **s242**) rotated to the same file at THIS (s251) reconcile — a two-session reconcile added two rows (s250, s251), so two left to hold the table at ten. Both rotate on the count rule alone: s243's G-13/G-14 substance lives in `docs/plans/done/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md`, and s242's SD-E reversal, second L1 re-reading and OQ-7(b) each keep a live Active TODO plus `docs/adr/0035-hosting-and-exposure-model.md`, whose own amendment pass records that a LOCKED ruling is amended in place, never edited.]_

## In-Flight Discussions

- **OPEN QUESTION for Cray — does a skill's registry table *bind*?** (Code's observation, not a ruling.) s210's closing notice asserted the four-work-stream registry table in `.claude/skills/stream-status/SKILL.md` (#1062) is **canonical**, and that a carrier-artifact change must update it **in the same PR**. The table as *reference* is fine; the **same-PR obligation** is the part that would have to live in `CLAUDE.md` or an ADR to bind — §1 places `.claude/skills/` at **Tier 2.6, derived, no independent precedence** (ADR-0017 D6). **Cray's call: promote it, or keep the table advisory.**
- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13; verdict **continue-with-adjustments**. Runs 1 (energy, s93) + 2 (supply-chain, s94) both COMPLETE, all S-checks PASS against pre-committed oracles, no R-PS trigger fired; C-1..C-3 CONFIRMED → **no open partner-sim debt**. ADR-011's audit stays gated on a REAL partner conversation (R3: SYNTHETIC provenance INFORMS but never TRIGGERS it). Full record: `docs/adr/0020-*.md` + the gitignored run packages under `docs/research/private/`.
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm — **not yet drafted**, and it needs a fresh ADR number. _[The old "≥ ADR-014" floor recorded here was **moot** — see the Active TODO below, corrected s141: ADRs now run past 0032 and `0014-WITHDRAWN.md` exists. Kept as one pointer rather than two divergent copies.]_
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).

## Active TODOs

- [ ] **🆕 ADR-016 SB-3 enumerates THREE load-gate refusals; the SHIPPED Step 1 has FOUR.** The fourth — `when_absent` supplied with **no `scope_by`** — was Cray-ratified at the #1275 merge (typed, s251), but SB-3's body still names only the three `scope_by`-present cases; re-checked in the ADR at the s251 reconcile. **Cray's call: amend the ADR, or leave the fourth recorded in the PLAN.** **Read:** `docs/adr/0016-governed-procedure-engine.md` §SB-3 · `docs/plans/0113-scope-event-fired-run-to-its-firing-case.md`.
- [ ] **🆕 CRAY'S CALL — should R2 cap the Active TODOs *COUNT*?** The s141 rule caps each entry (≤ ~600 chars — 100% compliant since #1272) and the s250 ruling caps In-Flight at 6 entries, but **nothing bounds how many TODOs this section holds** — **38 today**, and it only grows. Recorded, not acted on: adding a count cap would **author a new rule, not enforce one**. **Read:** `docs/runbooks/memory-architecture.md` §R2.
- [x] **CRAY'S CALL — should R2 cap `In-Flight Discussions`? RULED s250 (Cray, typed): YES.** Capped at pointer ≤ ~600 chars · OPEN-only · ≤ 6 entries; the Current-Focus **rotation ledger** is capped to the current window by the same ruling. Both live in R2 (`docs/runbooks/memory-architecture.md`) **and** in their enforcer, `.claude/agents/status-scribe.md` — which s250 measured had never received the s194 per-block cap or the s141 Active TODOs rule either; both backfilled. STATUS **53,048 → 48,645 B**, under the R1 soft target ([#1271](https://github.com/CrayJThiemsert/vero-lite/pull/1271)).
- [ ] **🆕 ADR-0035 — L1 re-read a SECOND time, and OQ-7 ruled, both Cray-typed s242.** L1 becomes *"one gate at the edge; app code may READ the verdict, never gate itself"*, unblocking phase-2 identity **capture** while **validation** stays pilot-era. **OQ-7 = (b)**: absent edge identity → proceed and **stamp the absence**. ⚠️ Two costs Cray accepted: runs stay unattributed until someone reads the stamps and **nothing alerts on it**; the stamp shape is PLAN-0112's to specify, not the ADR's. **Read the ADR:** `docs/adr/0035-hosting-and-exposure-model.md`.
- [ ] **🆕 The three live items the rotated s240 block carried — carried here so the rotation ledger's claim is true, not merely stated.** Measured at s240, none resolved since: (i) the **font-size decision still gates re-measuring every geometry number in the beat-4 mockup**; (ii) the **run-list backlog badge on the host is still unmeasured** — a host-state read, so it needs its own typed §8 go; (iii) the **three Advisory-proposal candidates are still unnamed**, so the gate panel still reads as unfinished. The full s240 narrative is at `docs/status-archive/2026-h1d-current-focus.md`.
- [ ] **The Tier-0 auto-memory store is a git repo that DRIFTS — REHOMED s247 to the runbook's Tier-0 section, which is where a reader about to run a consolidation actually looks.** Snapshotted s242 (164 tracked, tree clean). ⚠️ **A snapshot guards against a wrong deletion, NOT against disk loss — there is still no remote.** The `MEMORY.md` consolidation pass this unblocks is owed and deliberately not done here. **Read the runbook, never a restatement:** `docs/runbooks/memory-architecture.md` §Tier 0.
- [ ] **🆕 PLAN-0110 SD-E is REVERSED (Cray, typed, s242); its commissioned follow-on PLAN-0112 is COMPLETE and ARCHIVED s246.** The original ruling stands as history and is **NOT** edited. ⚠️ **Two consequences no AC owns:** `/runs` filtering is client-side only *because* the population was pinned at two, and the Monitor "all" filter has no cap — SD-6(b)'s bounded default covers Tab H, a **different surface**. **Read the archived PLAN:** `docs/plans/done/0110-fleet-demo-run-markers-filter-and-deploy-reset.md` (§SD-E · §Out of Scope).
- [ ] **🆕 The four s235 audit findings ADR-0038 did NOT absorb — REHOMED s235 to `docs/logs/2026-08-17-s235-audit-findings-outside-adr-0038.md`.** 🔴 **One live obligation: ADR-0038's three-strike counter has NO OWNER** — and the count has DRIFTED, the s235 log naming **three** items at two firings while ADR-0038's own D4 names **two**. PLAN-0108 is the natural owner and does not claim it. ⚠️ The genuinely-unruled item is the **D2.1 authorship fork**, not "ADR-0037 SD-1", which does not exist. **Read the log.**
- [ ] **🆕 PLAN-0111 — the fleet close-out record that can hold a credit note (ใบลดหนี้): `Draft`, all six SDs RULED** (Cray, typed 2026-08-19, [#1227](https://github.com/CrayJThiemsert/vero-lite/pull/1227)). **Cray ratified the SDs, not the PLAN; nothing gates execution.** 🔴 **SD-E forces SD-A to (b), a separate `repair_case_credit_note` table.** ⚠️ **AV-1 is owed before Step 4, not before merge** — SD-C is provisional on it. **Read the PLAN:** `docs/plans/0111-fleet-closeout-credit-note-record.md`.
- [ ] **PLAN-0107 — oracle-coverage hardening: `Draft`, 15 ACs, tally 10/5.** ✅ Phase A CLOSED 6/6 · AC-7, AC-8, AC-10, AC-11 CLOSED. Remaining: **AC-9 (BLOCKED on a Cray ruling — three defects, three options laid out neutrally in its `Reviewer amendment`)** and Phase C; nothing else gates them. ⚠️ **Read each AC and its `Reviewer amendment` blocks as authoritative; the §Steps prose is narrative** — three measured divergences in Phase A alone. **Read the PLAN:** `docs/plans/0107-oracle-coverage-hardening.md`.
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
