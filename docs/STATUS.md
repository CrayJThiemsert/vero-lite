---
last_updated: 2026-08-23T21:40:00+07:00
session: 249
current_batch: "s249 — two PRs (#1268, #1269): PLAN-0113 drafted and the ADR-016 amendment Accepted, reversing PLAN-0112 SD-4 so an event-fired run is scoped to its firing case."
current_actor: code
blocked_on: "Nothing. Main green, 0 open PRs. Owed: PLAN-0107 AC-9 re-scope, PLAN-0109's three ruled-content defects, PLAN-0108 label ordering, the `MEMORY.md` (Tier-0) consolidation."
next_action: "PLAN-0113 Step 1 — the `scope_by` grammar in `spec.py`; unblocked because Step 0b (the ADR-016 amendment) is merged and Accepted, which CLAUDE.md §8 required first."
head_commit: 33a4887
recent_commits: [33a4887, 857767c, 98463e7, e05cfa3, 674a985, 2073e95, e126ebd, c169b46, 1b26fdc, 2095e6e]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

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

> **Session 247, 2026-08-23 (head_commit `2095e6e` → `e126ebd`) — THREE PRs
> MERGED ([#1261](https://github.com/CrayJThiemsert/vero-lite/pull/1261), [#1262](https://github.com/CrayJThiemsert/vero-lite/pull/1262),
> [#1263](https://github.com/CrayJThiemsert/vero-lite/pull/1263)), 0 open, CI
> green on each. The Active-TODOs compliance trim SHIPPED: R2's ~600-char
> pointer cap — ratified 2026-07-17 (s141), never enforced since — went from
> **24 of 35 rows over to zero**; Active TODOs 27,450 → **18,167 B**, STATUS
> 60,553 → **51,270 B**.**
>
> 🔴 **A home is what `git ls-files` says it is, not what the filesystem says.**
> The carve-out was applied per item against the index, and 23 items had a
> tracked home. The **one that did not** — the Tier-0 auto-memory store, whose
> only path pointed outside the repo — was **REHOMED first** into
> `docs/runbooks/memory-architecture.md` §Tier 0, then re-pointed, then trimmed:
> rehome → re-point → verify → trim, never trim first. R4 checked against
> `git show HEAD:` — **11 unchanged + 24 archived verbatim = 35, LOST = 0.**
>
> 🔴 **A pre-committed criterion FAILED and was repaired by SCOPE, not by
> threshold.** It demanded STATUS reach R1's 48 KB soft target and failed at
> 51,270 B. Rather than relax a number after seeing the result (`CLAUDE.md` §8
> forbids exactly that), the criterion was examined and found wrong **about
> itself**: it attached a whole-file **R1** target to a section-scoped **R2**
> task. R1's own guard agrees out loud — *"Passing, but prune harder next
> reconcile (R2/R6)"*. Only the 64 KB hard ceiling gates a commit boundary.
>
> ⚠️ **The remaining overage is located:** Recent Decisions is **9,193 B, 9 of
> 10 rows over that same cap** — another section, another clause, out of scope at
> #1263 by decision and spawned as a task.
>
> 🔴 **A companion #1263 claim is MEASURED FALSE and retired here:** *"one CF
> block (s243 cont.) is over R2's 4,096 B cap at 4,936 B"*. Real size **2,567 B,
> under cap** — it was merely LAST, and the measurer bounded blocks
> header-to-header, swallowing the ledger that belongs to no block: **s246's
> instrument failure #1, verbatim.** Repaired: **zero** CF blocks over cap either
> side of this reconcile. The ledger below carries the positive controls.
>
> ✅ **The split ran FIRST, by Cray's ruling** (#1262): sections s173→s225
> spilled to `docs/status-archive/2026-h1h-status.md`, base 189,574 →
> **46,113 B**. A prerequisite, not a tidy-up — the trim's 21,958 B of full
> originals would have carried the base to 211,532 B, **14,924 B past R4's
> 196,608 B split trigger** yet still inside the hard cap, so the guard would
> have **passed it with a warning**: the wrong outcome for a compliance PR.
>
> 🔴 **R9 is now tracked NOWHERE — recorded rather than hidden** (#1261, on
> Cray's typed rulings, closing the two files carried in the tree since s241).
> The brand mark is gitignored (`docs/design/Cray_J_*`, a family pattern,
> positive-controlled so the tracked `.md` siblings stay visible); the edit to
> `docs/strategy/public/intro-video-production-rulings.md` was reverted after
> confirming R9 survives at ten sites in the **gitignored** storyboard — the
> exact failure mode that rulings file exists to prevent. Its own reverted text
> *claimed* the gap had closed while `git show HEAD: | grep -c R9` returned
> **0**, and had for six sessions. Cray ruled it acceptable.
>
> ⚠️ **Two probe instruments failed SILENTLY and were repaired before their
> results counted** — a `sed` mutation that never matched inside a `wsl bash
> -lc` string (the probe ran unmutated code and printed green; `diff` proved the
> file byte-identical), and a same-byte-length mutation defeated by a stale
> `__pycache__/*.pyc`. §8's *"suspect the probe first"* held both times. The
> strongest evidence was unstaged: the cap assertion reddened against the
> author's own drafts **twice** (12 over cap, then 5).

> **Session 246, 2026-08-22 (head_commit `9d0c3ff` → `38ef55e`) — THREE PRs
> MERGED ([#1256](https://github.com/CrayJThiemsert/vero-lite/pull/1256), [#1257](https://github.com/CrayJThiemsert/vero-lite/pull/1257),
> [#1258](https://github.com/CrayJThiemsert/vero-lite/pull/1258)), 0 open. PLAN-0112 Steps 6 and 7 EXECUTED;
> PLAN-0112 AC-7, AC-8 and AC-9 CLOSED — **the PLAN is COMPLETE 9/9 and archived**
> to `docs/plans/done/`, AC-7 after Cray ratified the narrowing its own
> measurement forced — and the visitor flow
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


_[Current-Focus rotation ledger. The sessions-233–234 and 235/236 blocks rotated
to `docs/status-archive/2026-h1d-current-focus.md` at earlier reconciles; the
**sessions-237–238 and session-239** blocks rotated there this reconcile —
**one session below the four-session window, deliberately**, because the s241
Active-TODO corrections had to land without growing this file (SD-1 in the s241
reconcile report). Rotated with them: s237's video-rulings carried risk, since
DISCHARGED s239 to `docs/strategy/public/intro-video-production-rulings.md`, and
s239's headline — eight PRs, two host-state deploys, and *"a summary that is
ACCURATE about what it cites still shrinks"*; s239's two host records survive
tracked at `docs/logs/2026-08-18-s239-*` and `docs/logs/2026-08-19-s239-*`. The **session-240** block rotated there at the s242 reconcile — it measured ~5,800–5,900 B against R2's 4,096 B per-block cap, and rotating it is the runbook's own prescribed response to STATUS sitting over R1's soft target (fix the voice, do not raise the ceiling). Its live residue is not lost: the three s240 items that were open when it rotated (the font-size decision gating the beat-4 geometry re-measure, the unmeasured host-side run-list backlog badge, and the three unnamed Advisory-proposal candidates) are carried in §Active TODOs rather than left only in the archive. The **session-241** block rotated there at the s244 reconcile, holding the window at four; its retired-claim marker travelled with the quote it labels, so the guard stays satisfied on both surfaces. The **session-242** block rotated there at THIS (s245) reconcile — again one session below the four-session window and again deliberately: STATUS stood at 61,636 B, 12,484 B over R1's soft target, and a new block could not be written without either this rotation or a trim that would delete facts. Its live remainders were carried before the move, not after — PLAN-0110 SD-E's reversal and ADR-0035's L1 re-read each hold their own Active-TODO entry, and PLAN-0107 AC-10 is recorded in that PLAN. The **session-243** block rotated there at the s246 reconcile, holding the window at four sessions; its G-13/G-14/G-15 substance lives in `docs/plans/done/0112-*.md`, which the Active-TODO entry points at — the fact the s245 reconcile measured when it discharged the trim prerequisite. The **session-243 cont.** block rotated there at THIS (s247) reconcile, holding the window at four sessions; its AC-1 substance lives in `docs/plans/done/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md`. ⚠️ **It rotated on the window rule alone — NOT on a cap overage.** #1263 recorded it at **4,936 B** against R2's 4,096 B per-block cap; that figure is **retired as an error** at this reconcile. Its real size is **2,567 B, under cap**: it was the LAST block, and the measurer bounded blocks header-to-header, so it swallowed this very ledger (2,368 B), which belongs to no block. The repaired measure finds **zero** CF blocks over cap on either side of this reconcile. The older figures in this ledger are **not** affected — the archived s240 block re-measures at 5,819 B against the *"~5,800–5,900 B"* recorded above. The **session-244** block rotated there at THIS (s248) reconcile, holding the window at four sessions; its PLAN-0112 Steps 3–4 substance lives in `docs/plans/done/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md`, and the #1249 ฿-facet fix it also carried holds its own Recent Decisions row. Like the s243-cont. block before it, **it rotated on the window rule alone — NOT on a cap overage**: the repaired measure (#1264) — bounding each block by its own contiguous blockquote run rather than header-to-header — found zero CF blocks over R2's 4,096 B cap. The **session-245** block rotated there at THIS (s249) reconcile, holding the window at four sessions and again on the **window rule alone, not a cap overage**; its witnessed-RED finding is now binding in `CLAUDE.md` §8 (#1253) and its G-13 / Step-5 substance sits in `docs/plans/done/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md`. ⚠️ **One fact of it has NO tracked repo home** and now travels only in the archive — the four-day `.git/index.lock` root cause (`STAT=T` / `do_signal_stop`: SIGSTOP-suspended, so the always-succeeding retry hid it); `.claude/skills/git-workflow/SKILL.md` holds the recovery, not that cause. Rehoming it is a separate PR.]_

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
| 2026-08-23 | **s249 — TWO PRs (#1268, #1269): PLAN-0112 SD-4 REVERSED (Cray, typed) — an event-fired run is scoped to its FIRING CASE**, drafted as PLAN-0113 with the ADR-016 amendment it requires Accepted the same session; `superseded by new info`, not an error. 🔴 Ten rulings, all as-recommended. 🔴 **OQ-1 closed a 3-session-old question** — Code may append `## Post-archival amendment` + one inline pointer in `done/`, **supersession pointers ONLY**. ⚠️ ADR-016's amendments index read 5 against 7 body sections; backfilled, now 8 = 8. | `33a4887` / [#1269](https://github.com/CrayJThiemsert/vero-lite/pull/1269) / `docs/adr/0016-*.md` |
| 2026-08-23 | **s248 — ONE PR (#1265): the Recent Decisions pointer cap went 8-of-10 rows over to ZERO** (7,408 → 5,743 B), the one fact tracked nowhere else REHOMED first into the git-workflow skill, then trimmed; R4: 2 + 8 = 10, LOST = 0. 🔴 **The inherited "next place to cut" was WRONG** — R2 does not govern In-Flight Discussions, capping it is a Cray ruling, not a trim. ⚠️ `674a985` lacks its `(#1265)` suffix — `gh pr merge --subject` writes verbatim. | `674a985` / [#1265](https://github.com/CrayJThiemsert/vero-lite/pull/1265) / `docs/runbooks/memory-architecture.md` |
| 2026-08-23 | **s247 — THREE PRs (#1261–#1263): the Active-TODOs pointer cap went 24-of-35 rows over to ZERO** (27,450 → 18,167 B), the archive split running first by Cray's ruling. 🔴 A home is what `git ls-files` says — the lone item without one was REHOMED, re-pointed, then trimmed; R4: 11 + 24 = 35, LOST = 0. 🔴 A failed pre-committed criterion was repaired by SCOPE, not threshold. 🔴 R9 is now tracked NOWHERE. | `e126ebd` / [#1263](https://github.com/CrayJThiemsert/vero-lite/pull/1263) / `docs/runbooks/memory-architecture.md` |
| 2026-08-22 | **s246 — THREE PRs (#1256–#1258): PLAN-0112 Steps 6 and 7 EXECUTED; COMPLETE 9/9, ARCHIVED, and the visitor flow proven LIVE.** 🔴 **The host had never received Step 5** — a week-stale checkout kept the accepted-quote ingress row out of production. 🔴 **AC-7(i)'s wording is MEASURED FALSE** — a fleet-wide `intake` makes every visitor run's gate decide the demo case too; production agreed twice. UNTICKED for Cray. | `38ef55e` / [#1257](https://github.com/CrayJThiemsert/vero-lite/pull/1257) / `docs/logs/2026-08-22-s246-*.md` |
| 2026-08-22 | **s245 — FOUR PRs (#1252–#1255): PLAN-0112 Step 5 SHIPPED, AC-2…AC-6 CLOSED — the governable moment reaches the published visitor.** 🔴 **THREE guards passed while protecting nothing:** enumerating `Math\.min\s*\(` missed `Math.min.apply`; `"acceptQuote(" in source` was satisfied by the function's own definition. **The instrument was wrong every time, not the artifact** — which promoted `CLAUDE.md` §8's witnessed-RED rule (#1253). 🔴 **G-13's prose set was FOUR, not two.** | `9d0c3ff` / [#1255](https://github.com/CrayJThiemsert/vero-lite/pull/1255) / `docs/plans/done/0112-*.md` |
| 2026-08-21 | **s244 — TWO PRs (#1248, #1250): PLAN-0112 Steps 3 and 4 BUILT — a visitor's accepted quote fires the governed run.** 🔴 **A SECOND composition failure beyond G-14** — SD-2(b) and SD-5(b) do not compose on the bridge's SD-P4 in-flight guard, which no key design routes around: every acceptance became a silent `SKIPPED_IN_FLIGHT`. 🔴 **Ordering fails with no error** — fire before `_refresh_case_events` and the gate is about ANOTHER truck. **No AC ticked yet.** | `a8c42b7` / [#1248](https://github.com/CrayJThiemsert/vero-lite/pull/1248) / `docs/plans/done/0112-*.md` |
| 2026-08-21 | **s244 — ONE PR (#1249): the Box-4 ฿ facet was UNREACHABLE, not missing.** Four of five ฿-producing verticals wrote `economic_impact` only into the action envelope while `benefit_rollup` reads `StepResult.reasoning_trace` — Tab J read ฿0 for all of them. Emission moved down to `ActionStepExecutor`, plus a run-scoped `(action_id, kind)` ledger without which procurement DOUBLE-COUNTED a run. **Standalone wiring fix; NOT a PLAN-0112 step.** | `6fce826` / [#1249](https://github.com/CrayJThiemsert/vero-lite/pull/1249) / `services/engine/procedures/action_step.py` |
| 2026-08-21 | **s243 cont. — ONE PR (#1246): PLAN-0112 Step 1 EXECUTED, AC-1 CLOSED — `run_procedure_endpoint` 403s without an authenticated human, before spec load and any DB write.** 🔴 **The only producer of a `PipelineRun` was the one door of three that did not fail closed** — `triggered_by: null`; PLAN-0110's G10(6) found it. 🔴 **Non-vacuity took TWO probes on DIFFERENT assertions** — deletion proves presence, RELOCATION proves placement. | `f52dbdc` / [#1246](https://github.com/CrayJThiemsert/vero-lite/pull/1246) / `docs/plans/done/0112-*.md` |
| 2026-08-21 | **s243 — TWO PRs (#1243, #1244): all SEVEN PLAN-0112 SDs RULED and the Step-2 gate DISCHARGED.** 🔴 **G-14 — two of Cray's own rulings did not compose:** SD-2(b)'s re-fire is swallowed by SD-5(b)'s bridge idempotency (`event_key` omits the amount) — **no error, no log**. 🔴 **AC-2's pass read was FALSE in the shipped demo.** 🔴 **G-13 — the exclusion is load-bearing PROSE at two sites.** ⚠️ SD-2 was ruled AGAINST the PLAN's recommendation. | `0b5c333` / [#1243](https://github.com/CrayJThiemsert/vero-lite/pull/1243) / `docs/plans/done/0112-*.md` |
| 2026-08-21 | **s242 — FIVE PRs (#1237–#1241): PLAN-0107 AC-10 CLOSED; FOUR Cray rulings, two re-opening settled ground.** 🔴 **PLAN-0110 SD-E REVERSED** — quote-acceptance, not case creation, is the governable moment; a no-principal firing mints a run **nobody can approve**. 🔴 **ADR-0035's L1 re-read a SECOND time** — app code may READ the gate's verdict, never gate; **OQ-7 (b)** stamps its absence. A LOCKED ruling is amended, never edited. _[Backfilled s243 cont.]_ | `bf2771e` / [#1238](https://github.com/CrayJThiemsert/vero-lite/pull/1238) / `docs/adr/0035-hosting-and-exposure-model.md` |

_[The two oldest rows (**s234, s233**) rotated to `docs/status-archive/2026-h1-status.md` at the s243 cont. reconcile, holding the table at ten. Two rows were added: the **s242 backfill** — Cray ruled it in, discharging the gap the s243 reconcile flagged, and its four rulings are no longer carried by narrative alone — and a **second s243 row**, because Step 1 is a BUILD event of a different kind from that session's rulings and folding it into the existing row would have written a row far over R2's ~600-char pointer cap. The oldest row (**s237**) rotated to the same file at the s245 reconcile, holding the table at ten; the s238 row followed at the s246 reconcile for the same reason. The **s239** row followed at THIS (s247) reconcile, again holding the table at ten. **Session 248 discharged the pointer-cap overage this table still carried: 8 of the 10 rows were over R2's ~600-char cap, and are now zero.** Each row's substance — not merely the path it named — was resolved against `git ls-files` before that row was shortened; the one fact tracked nowhere else, s240's *ancestry is not content*, was **rehomed first** into `.claude/skills/git-workflow/SKILL.md`, then re-pointed, then trimmed. All eight full originals are preserved verbatim in `docs/status-archive/2026-h1-status.md` (R4, move-never-drop). The **s240** row rotated to the same file at THIS (s248) reconcile, holding the table at ten. ⚠️ It is the one row whose fact was rehomed the session *before* it rotated — *ancestry is not content* now lives in `.claude/skills/git-workflow/SKILL.md`, and that skill's widened `description` surfaces it automatically — so its rotation drops nothing that STATUS was the sole carrier of. The **s241** row rotated to the same file at THIS (s249) reconcile, holding the table at ten. Its substance keeps two tracked homes — `docs/conventions/retired-claims.md` for the guard it shipped, and the *"the two s241 pre-commit guards are FLOORS, NOT CEILINGS"* entry in §Active TODOs for the live remainder — so it, too, rotates on the count rule alone.]_

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

- [ ] **🆕 CRAY'S CALL — should R2 cap `In-Flight Discussions` at all?** All three R2-governed sections are compliant, and stayed so at s249. STATUS measured **52,834 B entering s249 — 3,682 B over R1's 48 KB soft target**, not the *2,591 B* this row carried (that was s248's pre-commit read, retired as stale). In-Flight Discussions is the largest remaining section at **5,152 B / 9 entries** — but 🔴 **R2 does not govern it: "In-Flight" appears nowhere in `docs/runbooks/memory-architecture.md`.** Capping it **authors a new rule rather than enforcing one** — not Code's to do. Recorded here; `next_action` is overwritten each reconcile.
- [x] **🆕 PLAN-0112 — the visitor case that becomes a governed run (Tab I→Tab H): COMPLETE 9/9, ARCHIVED s246.** All seven SDs ruled, Steps 1–7 executed, and the flow is LIVE on the published system. AC-7(i)'s wording was **measured false** and **NARROWED (Cray, typed, s246)** — no code changed with the ruling. **Read the archived PLAN, never a restatement:** `docs/plans/done/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md`; the deploy and live walk are at `docs/logs/2026-08-22-s246-*`.
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
- [ ] **PLAN-0096 partner round-2 — ANSWERED s189; nothing blocking remains.** **Open, NON-blocking: cost-center (ศูนย์ต้นทุน) granularity — per truck or per company?** Ship the column, fill the rule when it lands. (A5 stays **parked** — no real Wialon export exists yet.) _[s226: the per-answer ledger A1–A7 is ROTATED to `docs/status-archive/2026-h1-status.md`; `docs/plans/done/0096-fleet-flow-completion-phase1.md` holds the detail.]_
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
