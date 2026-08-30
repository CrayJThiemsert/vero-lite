# STATUS.md — archived Current Focus blocks (2026 H1, continuation d)

> ✅ **THIS FILE IS THE LIVE APPEND TARGET for Current-Focus rotations** (started session 227, 2026-08-13). New blocks go at the **BOTTOM**, in rotation order.
> **Why this file exists:** [`2026-h1c-current-focus.md`](2026-h1c-current-focus.md) reached **192,607 B** with only **4,001 B** of headroom under R4's **196,608-byte split trigger**. Session 227's rotation is **14,468 B**, so appending it there would have crossed the trigger. Per R4 (`tools/check_archive_size.py`; `docs/runbooks/memory-architecture.md` §"R4 — Archive, don't drop") the continuation file is started **before** the bar is crossed, not after — h1c stays under the trigger and is now **closed to appends**.
> **Sibling chain — for THIS chain the NEWEST LETTER holds the NEWEST content** (the opposite of the `-status.md` chain): [`2026-h1b-current-focus.md`](2026-h1b-current-focus.md) (session 25) → [`2026-h1-current-focus.md`](2026-h1-current-focus.md) (legacy base, closed) → [`2026-h1c-current-focus.md`](2026-h1c-current-focus.md) (closed session 227) → **this file (live)**. Current-Focus-only; SEPARATE from the `2026-h1b..g-status.md` rotation chain — same letter scheme, different corpus, different append rules.
> **Tier-3: grep + windowed reads only, never a whole-file Read.**

**No content is lost by this rotation.** Every block below is the byte-exact text
that stood in `docs/STATUS.md` at `75243b0`, extracted with `git show` rather than
retyped, and verified by reading it back out of this file after the append.


## Rotated this reconcile — session 227 (2026-08-13)

Rotated out of `docs/STATUS.md` while reconciling **PLAN-0104 Steps 2-6 SHIPPED**
(#1148, #1149). These are the session-223 → session-226 Current Focus blocks, in
the order they stood in STATUS (newest first). Their live remainders were carried
into the session-227 block and the Active TODOs before rotation — nothing here is
still the only home for a live obligation.

⚠️ **One carve-out checked before rotating, not assumed:** the s223 block carried
the **J4 per-action ruling** under an explicit R2 "do not trim without rehoming"
marker. It survives outside this rotation in STATUS's own **Recent Decisions**
table, which this reconcile deliberately did NOT trim. Verified by grep before
the cut, not by memory.

> **Session 226, 2026-08-13 (head_commit `b229fcd` → `fa8a61c`) — three PRs
> merged (#1143–#1145), 0 open; the block below stops at `b229fcd` and could
> not know about **#1142**, its own reconcile merge. Theme: PLAN-0104 exists
> because the refusal it removes is enforced at THREE independent layers — and
> drafting it surfaced a benchmark guard that could not fail.**
>
> ✅ **PLAN-0104 DRAFTED (#1143)** —
> `docs/plans/0104-nl-query-count-with-group-by.md`, 480 lines, `Status:
> Draft`. It executes **PLAN-0100 D-4, RULED s217 (Cray, typed): option (a),
> teach the engine** — `count` **WITH** `group_by`. Authored by `plan-drafter`
> from a Code dispatch; **reviewed by Code against a rubric fixed BEFORE the
> draft was seen**.
>
> 🔴 **Why a PLAN and not a patch: the refusal has THREE independent
> enforcers**, so no single edit changes observable behaviour — the **system
> prompt** (`services/engine/nl_query.py:393`, verbatim *"never list/count"*),
> the **validator** (`:536-549`), and the result carrier **`AggregateResult`**
> (`:195-208` — `property: str` required, group values are measures). That is
> why the long-circulating *"≈ one PR + tests"* estimate was wrong.
>
> ✅ **All three SD slots RULED s226 (Cray, typed) (#1144).** **SD-1 = (a)**
> `AggregateResult.property` becomes `str | None` under a
> construction-enforced invariant — *property is None iff operation ==
> `count`*. **SD-2 = (a)** fix `run_query.py`'s `_count` inside this PLAN.
> **SD-3 = NO** — keep the existing structural unit-coherence bypass. Every
> ruling matched the drafted recommendation, so **no Step re-shaped**; two
> Steps' live conditionals were **RESOLVED in place, not deleted**, with the
> rejected alternatives kept as lineage.
>
> ✅ **PLAN-0104 Step 1 SHIPPED (#1145)** — two factually-wrong gold tokens
> repaired and the guard that should have caught them rebuilt. 🔴 **That guard
> was VACUOUS.** `tests/benchmark/test_nl_query_text_to_sql.py`'s
> `test_gold_values_cross_check_against_real_sql` has claimed in its docstring
> **since session 58** that it "validates the gold set"; its body **never
> referenced `SQL_EXPECT`**, restating the numbers as literals beside the
> constant. That is the mechanism by which `SQL_EXPECT["nl-02"] = ["11"]` and
> `["nl-05"] = ["1"]` survived **PLAN-0070 adding two readings** (true values
> **13** and **2**): `score_sql` requires every expected token to appear in the
> result, so both cases scored **`wrong` on every run of that arm, silently**.
> **A guard that reads its own copy of the answer cannot fail.**
>
> 🔴 **The `run_query.py` hazard is BROADER than the known dead `started_week
> ==` branch.** `DIMENSIONS` has **three** members (`run_query.py:68`) and
> `_count`'s fall-through collapses all of them to a single total, while
> `_run_query_schema` (`:296-300`) **already advertises the pair to the
> model**. **AC-5 therefore makes it a hard merge dependency** — no
> intermediate commit may exist where the pair validates and `_count` still
> collapses.
>
> ✅ **Step 1's fix keeps TWO layers rather than swapping one for the other.**
> The literal assertions stay (they redden if `synthetic.py` moves), and a new
> loop feeds **real result rows through the PRODUCTION `score_sql`** for
> **every** scored qid, asserting coverage explicitly. **Non-vacuity probe run,
> RED SEEN:** replanting `["11"]` from a `/tmp` copy failed at the new layer —
> `nl-02: SQL_EXPECT=['11'] does not match the real result [(13,)]` /
> `assert 'wrong' == 'correct'` — while **layer 1 stayed green through the
> mutation**, which is the evidence that the old guard could not have caught
> it.
>
> **Gates on the tip (`0b0de18`, captured after committing / before pushing,
> `git diff --stat HEAD` empty):** **4028 passed / 8 skipped**, `mypy --strict
> services/` clean over **134** files, `ruff check .` + `ruff format --check`
> clean — ruff run against `git archive HEAD` extracted to a temp dir, i.e.
> **CI's actual view**, because a bare `ruff check .` in the working dir also
> lints untracked local scratch.
>
> 🆕 **One Active TODO added on a Cray ruling — `nl-03`'s `SQL_EXPECT` is
> UNDER-SPECIFIED, recorded and deliberately NOT changed.** It is a
> **different defect class** from nl-02/nl-05: that oracle is **weaker than it
> should be, not wrong**. The row below carries why tightening it is a
> **measurement decision**, not a typo fix.
>
> ⚠️ **Where PLAN-0104 stands: Step 1 DONE, nothing else built.** Steps 2–6 are
> unblocked and **entirely offline**; **Steps 2/3/4 must land as ONE PR**
> (AC-5). **Step 7 is the only host-state step and needs its OWN typed §8 go,
> asked for at that step by name and never inherited from the SD rulings — no
> §8 go has been given.** `Status:` stays `Draft`. Unchanged by this session:
> **PLAN-0103's AC-11 (the RoPA) is Cray's and still gates fleet's bring-up.**

> **Session 225, 2026-08-12 (head_commit `853d827` → `b229fcd`) — six PRs
> merged (#1136–#1141), 0 open. #1136–#1138 are session 224's tail and are
> recorded here, because the block below was written by #1135 and stops
> there. Theme: an inherited "these ACs are closed in substance" claim was
> VERIFIED rather than relayed, and two of them were false.**
>
> ✅ **PLAN-0103 Step 6 SHIPPED (#1138)** — fleet's three-persona picker plus
> SD-8(iii)'s narrative copy where Tab G's Act card would be. 15 files,
> **+1062**, tests **4007 → 4025**. **#1139** then closed six ACs in the PLAN
> (**AC-1..AC-5, AC-7**), recorded Step 6's execution, and carried three
> corrections.
>
> 🔴 **Verifying the inherited claim is what found the two falsehoods.**
> **AC-7's own text described an approval the engine refuses** — wrong from
> the moment it was written, not drifted into. **AC-6 was not closed at all:
> the guard its text names had never existed.** Both were **fixed rather than
> ticked over** — **#1140** shipped AC-6's missing guard (tests **4025 →
> 4028**; `.gitignore` also gained `.claude/launch.json`) and **#1141** ticked
> AC-6, closed **as code**.
>
> ✅ **Nine of eleven ACs are now closed.** Open: **AC-10** (the per-bring-up
> obligation — fleet's bring-up has not happened and needs its own typed §8
> go) and **AC-11** (the RoPA, Cray's artifact as data controller). AC-11
> gates fleet's bring-up, which gates AC-10, and `Status:` is still `Draft`.
> ⚠️ **Nothing remaining in this PLAN is Code-executable.**
>
> ✅ **The session-224 tail.** **#1136** reconciled s224 and corrected
> procurement's `cloudflared/config.yml` header, which still repeated SD-8's
> false premise. **#1137** tracked the RoPA change statement at
> `docs/compliance/ropa-change-statement-fleet.md` — so **AC-11 now names its
> path** — and added **Lesson #0041**.
>
> 🔴 **Three of STATUS's OWN standing claims were measured false and are
> corrected IN PLACE, not annotated beside the wrong sentence.** (1) *"Code
> cannot edit `docs/plans/` (G2)"* — **false**: G2 fires only on a numbered
> artifact that does **not yet exist** (creating one consumes a number), and
> G1 is scoped to `docs/adr/` with `Status: Accepted`, never `docs/plans/`.
> What actually routes an existing PLAN to the drafter is the **ADR-009 D1
> convention** plus the advisory Stop classifier — practice unchanged, stated
> reason wrong. (2) PLAN-0100 D-4's *"four seams in one file"* — an
> **undercount**: eight or more, and the decisive omitted seam is the **system
> prompt**, which forbids the very combination the work exists to enable.
> (3) The stream-3 (primitives) *"ZERO ratified ACs/Steps"* — false as worded:
> PLAN-0076 has six ACs and four Steps; the true claim is *zero that direct a
> build*.
>
> 🆕 **Two Active TODOs added, each on its MEASURED basis** — the ฿
> realized-vs-projected join (⚠️ the circulating *"~40 lines by reusing
> `benefit_rollup`"* framing was **checked and is wrong**) and the demo-key
> rotation cadence (Cray's, posture not code). Read the rows below.

> **Session 224, 2026-08-12 (head_commit `b4cb860` → `853d827`) — one PR
> merged (#1135), 0 open. Theme: a governance slot's own factual premise had
> been wrong for three sessions, and RUNNING THE SURFACE is what found it.**
>
> ✅ **RULED (Cray, typed, s224): PLAN-0103 SD-8 = option (iii)** — Tab G's Act
> card is replaced with **narrative copy** on a personaless published system,
> and **Step 6 builds it**. The cost is accepted unsoftened: **copy with no
> oracle — no test reddens if the copy is wrong.**
>
> 🔴 **The slot's premise was FALSE, and measurement is what found it.** SD-8
> asked whether Tab G's Act card "should render at all" on a personaless
> system. Measured against a **local reproduction** of procurement's own
> committed `published.env` (`UI_PROFILE=published`, `UI_PUBLISHED_VIEWS=G,F`,
> no `API_KEYS`): the card **does not render on any published profile** — zero
> `input` elements of any type on Tab G and Tab F, "Act — the human DOA gate"
> absent from the DOM, rendered tabs `G`,`F` only. ⚠️ **A reproduction, never a
> live-system reading** — the domain is deliberately absent from this repo
> (ADR-0035 D1(3)) and the live surface sits behind Access.
>
> **The mechanism is upstream of personas.** The card renders only in event
> mode (`view-hero.js:655`) and `mount()` defaults to manual (`:662`), while
> the one control that reaches event mode is suppressed on every published
> profile (`:604-614`, `if (!published)`) because event mode fires
> `POST /demo/hero/event` — the unauthenticated DB write D5(2) excludes.
> **PLAN-0100 Step 3 did that BEFORE SD-8 was authored**, which is why the
> classification is **`was an error`, not `superseded by new info`**. It stood
> through s222 and s223 because nobody ran the surface and looked.
>
> **Four statements corrected INLINE, each marked**, on this PLAN's own
> #1128→#1129 precedent: the "visitor sees a login form" claim; the slot's
> premise; option (i)'s rationale (it describes a dead end that cannot occur —
> its *outcome* was coherent, its *reasoning* was not); and option (ii)'s
> quoted price of "a new published-profile UI branch", already paid by
> PLAN-0100 for an unrelated reason. The s222 Live-input paragraph was
> **corrected rather than struck** — it carries a separate typed ruling (keep
> `API_KEYS` provisioned) plus true edge facts; only its "option (i)"
> characterisation was wrong.
>
> 🆕 **One implementation note added under Step 6 — rides SD-4 RULED (b), no
> new slot.** `view-monitor.js` contains **zero** `isPublished()` references,
> so its `authBar()` login form — free-text identity + password-type key input
> (`view-monitor.js:425-463`) — renders **unconditionally** whenever Tab H
> mounts. **Fleet is the only system publishing H**, so this is invisible today
> and **becomes visible at fleet's bring-up**. SD-4(b) already rules that
> surface is the published-profile-only persona picker; the published branch
> that would make "published-profile-only" true **does not exist yet**.
>
> **Gates on the tip:** 4007 passed / 8 skipped, ruff + `ruff format` +
> `mypy --strict services/` clean, CI green on the same SHA. ⚠️ Riding in the
> reconcile PR and **not** in `853d827`: `oct-procurement/cloudflared/config.yml`'s
> header, which still described SD-8 as open and repeated the same false
> login-form claim, is corrected there.

> **Session 223, 2026-08-12 (head_commit `bd43d67` → `b4cb860`) — two PRs
> merged (#1132, #1133), 0 open. STATUS had fallen EIGHT PRs behind
> (#1126–#1133); #1127–#1131 are session 222's tail and are recorded in the
> next block, not here. Theme: the MS-S1 secrets exposure session 222 left
> open is CLOSED and PROVEN.**
>
> ✅ **The exposure is CLOSED (#1132).** Run as a ladder under **two typed §8
> gos**: rung A dropped `Authenticated Users`; rung C also dropped
> `BUILTIN\Users` and granted the signed-in account's SID `(OI)(CI)(RX)`.
> Final ACL on the directory and all **8** paths under it: that account
> `(RX)` + `BUILTIN\Administrators (F)` + `NT AUTHORITY\SYSTEM (F)`. The
> bring-up §8 remedy that s222 **measured** to break Docker Desktop's bind
> mount is replaced with the working form, together with the **filtered-token**
> mechanism that explains why the old Administrators-only tightening failed.
> Record, never a restatement:
> `docs/logs/2026-08-12-ms-s1-secrets-acl-tightening.md`.
>
> 🔴 **The canary discipline is the transferable part — and it is why s222's
> breakage stayed invisible.** Each rung was verified by a **force-recreate,
> never a restart**: a running container already holds the file handle, so a
> restart cannot see a broken ACL. A rung was believed only on a **changed
> container id** plus `Registered tunnel connection` in the connector log.
> Canaries were **procurement-only**; `oct-energy`'s connector was recreated
> **exactly once**, deliberately, as the terminal end-to-end proof, and
> **`oct-energy-app` was never recreated** (Up 40 h throughout). The verifier
> was seen **RED before GREEN** (`authenticated_users_aces` 4 → 0) with a
> positive anchor, so an ssh failure fails **closed**. Gates: **4007 passed /
> 8 skipped**.
>
> ✅ **#1133 — the leftover `icacls /save` backup relocated** into the
> tightened directory rather than deleted (Cray, typed). 🔴 **A same-volume
> move keeps the OLD ACL** — measured, and now in the runbook; an unmeasured
> "a copy inherits" claim was **scoped back to what was actually measured**.
>
> 🔴 **The one Cray ruling this record exists to carry — J4's per-action
> reading.** "Run the full `tests/` before pushing" stays **BINDING**, but is
> evaluated against **the commit(s) being pushed at evaluation time**; earlier
> uncovered pushes are **residual gaps, not a standing FAIL** — a criterion no
> future work can turn green is defective, not strict. ⚠️ **This ruling lived
> in a gitignored `goal.json` that has since been DELETED. STATUS and the s223
> handoff are now its only homes — do NOT trim it on a later reconcile without
> rehoming it first (R2 carve-out).**
>
> ⚠️ **Unchanged by this session.** **SD-8 is still NOT RULED** and gates Step
> 6. **AC-11's RoPA** (Cray's, as data controller) gates **fleet's** bring-up,
> the last Step 10. **AC-10 stays deliberately NOT ticked** — three typed §8
> gos are on record, fleet's is outstanding.

---

### Session 227 Current-Focus block (rotated 2026-08-14, session 231)

> **Session 227, 2026-08-13 (head_commit `fa8a61c` → `75243b0`) — two PRs
> merged (#1148, #1149), 0 open, and PLAN-0104 went from ONE shipped Step to
> SIX. What is left in it is the one claim no fixture can settle.**
>
> ✅ **Steps 2+3+4 SHIPPED as ONE PR (#1148)** — the carrier, the validator
> relaxation and the run-corpus execution, deliberately inseparable. **AC-5 is a
> hard merge dependency, not a preference:** no commit may exist where
> `count`+`group_by` validates while `run_query.py`'s `_count` still collapses
> groups to a total — that intermediate state answers *"how many runs per week?"*
> with a single **silently wrong** number, which is strictly worse than the
> honest refusal it replaces. `AggregateResult.property` is now `str | None`
> under a **construction-enforced** invariant (*None iff `count`*), so a
> grounding receipt can never name a property the figure was not computed over.
>
> ✅ **Steps 5+6 SHIPPED (#1149)** — gold case **nl-13** (`group-count`;
> per-asset **5/3/3/2 = 13**, hand-verified against `synthetic.py`), a
> **tolerance-free exact** `groups` scorer, and the prompt's blanket *"never
> list/count"* rule inverted. Gates: **4045 passed / 8 skipped** (4028 at s226
> close), `mypy --strict services/` clean over 134 files, ruff + format clean
> **judged on the HEAD tree**, not the working dir.
>
> 🔴 **The strongest thing added this session is a test that grades the gold
> against the ENGINE.** nl-13's numbers are not restated in a test beside them:
> the real engine runs the real adapter and the **real scorer** grades the
> **real gold case**, so a drift on *either* side reddens. That is exactly the
> s226 defect — a gold token nothing ever compared against a real result stayed
> wrong for 168 sessions while scoring green — and this **closes** it for this
> case rather than merely avoiding a repeat.
>
> ✅ **SD-2 (a)'s one marked claim is RESOLVED, and the answer was "no API
> change".** `RunQueryAnswer` carries `aggregate_value` under `extra="forbid"`
> and has **no groups field** — and needs none: the per-group figures reach the
> user through the phrased answer plus the `structured_query` receipt, exactly
> as the ontology path's grouped numbers already do. **Scope was NOT widened.**
>
> 🔴 **Found while executing, deliberately NOT fixed — RULED (Cray, typed,
> s227): record it as a TODO.** `_count`'s week branch applies only the
> `started_week` filter, so a `procedure_id`/`status` filter alongside it is
> **silently dropped** (`week_rollup` carries no such dimension). Reachable
> **today** via a filter, so PLAN-0104 neither introduced nor repaired it; a
> comment now names it at the site. Its own Active TODO row below.
>
> ⚠️ **Step 7 is ALL that remains, and it needs its OWN typed §8 go, asked for
> at that step BY NAME — not inherited from the SD rulings and not implied by
> merging #1149. None has been given, and MS-S1 was untouched all session.**
>
> **Carried forward from the s226 block (rotated this reconcile to
> `docs/status-archive/2026-h1d-current-focus.md`) because both outlive it:**
> the refusal had **three independent enforcers**, which is why the *"≈ one PR +
> tests"* price was wrong twice; and **a guard that reads its own copy of the
> answer cannot fail**.

<!-- Rotated 2026-08-16 (session 234) from docs/STATUS.md Current Focus to keep
     the window at four blocks. Target is the NEWEST 2026-h1*-current-focus.md
     chain file; Recent-Decisions rows archive to the unlettered base instead. -->

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


## Rotated this reconcile — session 235 (2026-08-17)

Rotated out of `docs/STATUS.md` while reconciling **ADR-0038 RATIFIED + `CLAUDE.md`
BOUND** (#1193–#1200, `027986e` → `218a521`). This is the session-229 Current Focus
block — the oldest in the window, displaced by the session-235 block.

⚠️ **Carve-out checked before rotating, not assumed.** The block's two load-bearing
facts survive outside it: R8's glob-blindness fix and its six-tests-seen-RED
non-vacuity record live in `docs/runbooks/memory-architecture.md` §R8 and in
[#1153](https://github.com/CrayJThiemsert/vero-lite/pull/1153); the
Windows-worktree environmental-RED **drifting count** lives in
`docs/lessons/0042-a-remembered-baseline-is-not-evidence.md`, which the block
itself cites. The session-229 **Recent Decisions row is deliberately NOT trimmed**
and stays in STATUS. Verified by grep before the cut, not by memory.

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


## Rotated this reconcile — session 236 (2026-08-18)

Rotated out of `docs/STATUS.md` while reconciling **PR-B COMPLETE + PLAN-0107
Phase A CLOSED 6/6** (#1201–#1204, `218a521` → `de3295a`). This is the session-231
Current Focus block — the oldest in the window, displaced by the session-236 block.

⚠️ **Carve-out checked before rotating, not assumed.** Every load-bearing fact in the
block survives outside it, grep-verified: PLAN-0105 is archived at
`docs/plans/done/0105-fleet-case-retention-in-app-deletion.md` (its four SD rulings
appear 30 times there); the child-to-child FK ordering defect keeps its guard at
`tests/services/db/test_case_retention_completeness.py`
(`test_the_declared_order_respects_every_child_to_child_dependency`); and #1159's
RoPA corrections live in `docs/compliance/ropa-published-demo.md`. The PLAN-0105
**Active TODO row is deliberately NOT trimmed** and still carries the live
DSR-on-request remainder.

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

<!-- rotated from docs/STATUS.md by the session-238 reconcile -->

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


### Rotated 2026-08-19, session-239 reconcile — Current Focus s233-234

> **Sessions 233–234, 2026-08-15→16 (head_commit `5425822` → `027986e`) — TWELVE
> PRs merged (#1180–#1191), 0 open. Fleet's last gate closed, fleet WENT LIVE, a
> human drove it, and it broke in a way CI structurally cannot see.
> `oct-fleet-maintenance` is published system #3 and is now serving the FIXED
> build; PLAN-0103 is COMPLETE 11/11 and PLAN-0106 COMPLETE 7/7, both ARCHIVED.**
>
> ✅ **AC-11's RoPA was written and ADOPTED** (`docs/compliance/ropa-fleet-cases.md`,
> #1184) — the artifact the whole chain waited on. 🔴 **Its authorship DEPARTS
> from ADR-0037 D2.1, disclosed ON the artifact:** Code drafted at Cray's request,
> Cray ruled every promise slot and adopted. **SD-1 stays unruled; until it is,
> D2.1 as written governs.**
>
> 🔴 **s233's load-bearing work was VERIFICATION, not construction — seven
> inherited claims were checked and REFUTED**, including ADR-0037's OQ-3, which
> had been *ruled* 2026-08-14 while its recorded Recommendation was still the
> **OVERRULED** option. Three downstream artifacts inherited it and it nearly
> sent the RoPA into the wrong file. _[Closed #1185. The general rule — a ruled
> OQ closes in the same change that records the ruling — is proposed as SD-2 and
> is UNRULED.]_
>
> ✅ **Tab J shows real money — ฿33,705, not a structural ฿0** (#1187), with an
> honest empty state. ⚠️ Seeding onto the demo's flagship truck **displaced** its
> ฿48,000 axle breach (the query projects the latest event **per truck**) —
> silent demo damage caught only by the full suite.
>
> ✅ **s234 executed Step 10 under Cray's typed §8 go**, and the pre-flight found
> **two steps every prose summary of that sequence had omitted** — the image was
> not on the host (`build:` with no `image:`, so `up -d` would build on the deploy
> host and fail there), and the host checkout was deliberately **not** pulled
> (the `deploy/` diff across those eight commits is empty).
>
> 🔴 **The keyed `/whoami` control was recorded as a DIFFERENTIAL** — keyless
> 401, correct key 200, **wrong key 401**. The third reading is what makes the
> second mean anything: a `200` alone is equally explained by "auth is off".
>
> 🔴 **Two documentation claims were MEASURED FALSE and corrected in the same
> PR** — the backslashed Windows path stripped through `ssh`→PowerShell, and
> *"302 proves a **working** origin"*. **Both now live in the runbooks they
> misled.** ⚠️ **Step 9's headroom projection is exceeded (≈1.33 GiB vs ≈0.95)
> because it models containers at boot** — the PLAN-0103 Active TODO owns that
> residual.
>
> Do-no-harm held on both host actions, against baselines captured **before** the
> first one: `oct-energy-app` and `oct-procurement-app` never restarted.
>
> 🔴 **Then Cray drove the live surface through Access, and that is the session's
> lesson.** It closed the scope limit Code had recorded (all six tabs render;
> Tab J shows **฿33,705** live) **and found a defect 4,113 green tests could
> not** — Tab I's root stood **919px inside a 614px `overflow: hidden` view**, so
> **305px was unreachable** with no scrollbar and no error. Fixed by copying
> Tab J's contract (#1190), guarded by a stylesheet-reading test, shipped live
> under a second typed §8 go. **CI has no JS runtime — that is the gap, not a
> missing test; own Active TODO.**
>
> ✅ **Redeploy, measured:** the new image id **differs**, **only `app` was
> recreated** so the tunnel never re-registered, both seeds' idempotency proven on
> real data, and the audit chain's `head_hash` came back **byte-identical** —
> which proves nothing was written, a claim `intact: true` alone cannot make.
> ⚠️ `index.html` is served `cache-control: no-store`, which **narrows**
> PLAN-0100's "nothing purges the edge" residual without closing it (fonts stand).
>
> **Gates: 4114 passed / 8 skipped**, `mypy --strict services/` clean over 136
> files, ruff + format clean over 631. Full record — bring-up **and** redeploy
> addendum: `docs/logs/2026-08-16-plan0103-step10-fleet-bring-up.md`.

## Rotated this reconcile — session 240 (2026-08-19)

> **Session 236, 2026-08-17→18 (head_commit `218a521` → `de3295a`) — FOUR PRs
> MERGED (#1201–#1204), 0 open. The session that paid s235's STATUS debt in full
> and then built the first four oracles PLAN-0107 asks for.**
>
> ✅ **STATUS is reconciled and PR-B is COMPLETE — 61,736 → 48,852 B, under R1's
> 49,152 B soft target for the first time in this chain**, headroom 3,800 →
> **16,684 B**. The rehome, not the trim, is what paid: every carve-out fact moved
> to **the artifact whose reader needs it**, then the row collapsed to a pointer
> (PLAN-0100's residuals → its own §Post-archival amendment, 2,202 → 480 B). Six
> facts came out of a **gitignored** handoff into
> `docs/logs/2026-08-17-s235-audit-findings-outside-adr-0038.md`; nine rows out of
> STATUS into code, tests, a benchmark module and `docs/logs/`. **Read those, never
> a restatement.**
>
> ✅ **PLAN-0107 Phase A CLOSED 6/6** (#1204) — CI gained four oracles it did not
> have: `node --check` over every shipped JS asset · an asset↔reference
> **bijection** (chosen over a floor constant: a `≥ 20` floor over 21 files has one
> file of headroom and its misfire remedy is editing the number) · a **per-vertical
> lifespan boot smoke** · `mypy --strict verticals/` plus the two pre-commit hooks
> that had only ever run on a developer's laptop. **Measured bill: `gate` 7m53s →
> 9m7s ≈ +74 s, no new dependency.** Verified at **step level**, not job level — a
> green job cannot distinguish a step that passed from one that was skipped.
>
> 🔴 **AC-3's own central claim was MEASURED FALSE in the configuration CI runs.**
> The AC said the smoke makes §3's fail-loud contract CI-visible; corrupting each
> spec in turn, it is **CAUGHT** for fleet_maintenance, building_materials,
> supply_chain and procurement and **MISSED for `energy`** — the **default**
> vertical, and the one spec-shipping factory that never calls `load_procedures`.
> Booting only the default would have been green and blind to exactly what CI runs.
> Fixed by booting once per spec-shipping vertical; **the `energy` residual stays
> OPEN** in `tools/ci/boot_smoke.py`'s docstring.
>
> 🔴 **CI caught what no local probe structurally could.** Phase A's first run died
> on `ModuleNotFoundError: No module named 'services'` — the runtime venv is
> `--no-install-project` by design, and `python <file>` puts the *script's*
> directory on `sys.path` where `python -c` put the CWD. **Every local run used the
> dev venv, which has the project installed, so the failing state was unreachable
> there.** A ② *reach* failure inside the PLAN that exists to close ② failures.
> Fixed by **building** that condition locally and reproducing the error, not by
> reasoning about it.
>
> 🔴 **ELEVEN inherited claims were checked and EIGHT were wrong** — including two
> live falsehoods in STATUS itself (`deploy.py`'s "broken" compose path, fixed a day
> earlier; *"AC-11's RoPA is still Cray's"*, adopted at s233), a guard cited at the
> wrong file, and a scenario census stale in both figures (13/63 → **14/69**, the
> third drift of that number). **The base rate is high enough that checking an
> inherited claim is not optional.**
>
> **Gates, every PR: `pytest tests/` 4115 → 4123 passed / 8 skipped**, `mypy
> --strict services/ verticals/` clean over **200** files, ruff + format clean over
> 634, CI `gate` pass.

> **Session 235, 2026-08-17 (head_commit `027986e` → `218a521`) — EIGHT PRs
> MERGED (#1193–#1200), 0 open. s234's Tab I clip was asked to generalise beyond
> UI, and it did: a five-specialist audit turned one 305px defect into a measured
> failure-class census, ADR-0038 made five classes BINDING, and `CLAUDE.md`
> gained FOUR new rules — in one session.**
>
> 🔴 **The organising law the whole session turns on:** an oracle sees a defect
> only when three independent conditions hold — **① an INSTRUMENT can read the
> artifact · ② the test DATA can reach the failing state · ③ someone ARMED it as
> a gate rather than as evidence.** The weakness is **not** UI-specific and is
> **not** a missing test; it was failing silently across two of the three
> Phase-1 OCT features.
>
> ✅ **ADR-0038 RATIFIED** (#1195, #1197) — the three-strike promotion rule for
> advisory lessons, the census, D2's per-class enforcement forms, D5's demotion
> path. **All four surfaced decisions RULED** (Cray, typed); its OQ-5 resolved to
> the PLAN template rather than a build task (#1198). **Read the ADR, never a
> restatement:** `docs/adr/0038-advisory-lesson-promotion-three-strike-rule.md`.
>
> ✅ **`CLAUDE.md` BOUND — four new rules, +314 words / +1,852 B, zero new
> sections** (#1200): a load-bearing green is not evidence until its assertion is
> **witnessed RED** in the direction it claims · an **expected-value set is not
> an oracle of the system** until the system's own output is scored against it ·
> an **inherited premise a decision rests on is a claim, not context** · **name
> the rule's consumer, then check the home is in that consumer's input.** Per the
> file's own convention the amendment record is the commit message
> (`git log --follow -- CLAUDE.md`) and is not restated here.
>
> 🔴 **A live defect on `main` was fixed** (#1193) — `deploy.py` built against
> `deploy/published/docker-compose.yml`, deleted three commits earlier; Phase 1
> would have died on the next `--execute`. Path promoted to a module constant
> plus a guard that walks the module's own path constants. ⚠️ **That guard's
> first draft masked its own oracle** — the probe reddened on a pinned literal
> and the filesystem stat never ran. **Seeing RED is not enough; read the RED.**
>
> ✅ **The control group that shaped the whole response:** `CLAUDE.md` §8's
> scenario-test rule is **GENUINELY OBEYED — all 17 scenario/e2e files, zero
> violations**, recorded per §6 as `confirmed — prior intact`, not a defect. This
> repo obeys a binding *mechanical* rule almost perfectly and fails on *advisory*
> ones — the asymmetry ADR-0038 rests on.
>
> ✅ **Branch protection verified LIVE, not from memory:** `strict: true`,
> `contexts: ["gate"]`, `enforce_admins: true`. With `strict` plus a bare
> `actions/checkout@v4` on `pull_request`, **the graded tree IS the tree that
> lands** — so `on: push: main` is NOT worth adding, and a specialist proposal to
> add it was retired on this evidence.
>
> **PLAN-0107 + PLAN-0108 drafted and split by ORACLE STRENGTH** (#1194, #1199)
> on Cray's typed S1 ruling; both `Draft`, unratified. **Gates, eight times:**
> `pytest tests/` **4115 passed / 8 skipped**, `mypy --strict services/` clean
> over 136, ruff + format clean over 631, CI `gate` **pass** every time.

### Rotated 2026-08-20, session-241 reconcile — Current Focus s237-238

> **Sessions 237–238, 2026-08-18 (head_commit `de3295a` → `32854ab`) — SEVEN PRs
> MERGED (#1208–#1214), 0 open. PLAN-0110 drafted, ruled, built and DEPLOYED in
> one arc; s237 was never separately reconciled, so this block carries both.**
>
> 🔴 **s237's method, and it is the transferable part: measuring the LIVE demo
> refuted the intro video's central beat.** Beat 4's three shots film **Tab G**,
> which the published profile does not serve — excluded **by ruling** (SD-3 s218 +
> ADR-0032 D1.2), while the storyboard was verified on a local dev profile where
> all ten tabs render. Cray ruled (A): shoot on the published profile. Measuring
> the replacement found **Tab H carries the whole beat in ONE frame, no scrolling**
> (`docH == viewport == 737`), against Tab G's two halves 797 px apart.
>
> 🔴 **A real fleet defect, found on the LIVE system, with a NON-obvious second
> layer** (#1209). Tab H showed a **settled** repair — invoice keyed, case CLOSED —
> sitting in the visitor's approval queue. Root cause: `seed_settled_history_case`
> resolved the gate without resuming; **and one resume is not enough**, because
> `governed_repair_approval`'s TERMINAL step is itself `autonomy: gated`, so
> resuming once parks the run again at `fulfill`, still `waiting_human`. **The
> money was never wrong**, which is why no offline oracle noticed — the defect
> lived in a run's status field, on a screen counting RUNS while every assertion
> counted CASES. An instrument existed and was aimed one field to the left.
>
> ✅ **PLAN-0110 COMPLETE 7/7 and ARCHIVED** — Tab A run markers, a three-mode run
> filter, and a deploy-time demo reset ([#1213](https://github.com/CrayJThiemsert/vero-lite/pull/1213) code,
> [#1214](https://github.com/CrayJThiemsert/vero-lite/pull/1214) evidence).
> 🔴 **The measurement that reversed the obvious design:** the parked gate carries
> **three** proposals and **all three name a `case_id`** — two exist only in the
> fixture and resolve to no row. Reading `truck_id` off the ingested event (the
> shorter path) yields three trucks, trips the ambiguity guard, and stamps
> **nothing, forever**, with every test green. The `repair_case` lookup is the
> discriminator, not a formality.
>
> ⚠️ **TWO divergences from PLAN-0110's own wording, named in its Status block
> rather than left in a diff:** Step 3's *"one transaction"* is incompatible with
> reusing `delete_case` (which owns its commit + rollback by PLAN-0105 contract);
> and Step 4's runbook location **reddened the ADR-0036 D2 label guard**, so the
> operator procedure ships in the profile directory instead.
>
> ✅ **Step 7 DEPLOYED to MS-S1 under a typed §8 go.** `DEMO-STATE: CONSUMED` →
> `PRISTINE`; both demo runs gained a `subject` (`NULL` before, so Tab A could key
> no marker); `run-fleet-demo-history` went `waiting_human` → **`completed`**, so
> #1209's fix is finally live. Audit rows **9 → 17, never decreased**. Only `app`
> recreated; postgres + cloudflared kept their container ids.
> 🔴 **The deploy found a gap in a file merged hours earlier:** `DEMO-RESET.md`
> prescribes reset-then-`up -d`, but **the tool ships inside the image it must run
> before** — impossible on a bootstrap deploy. It fails safely (no token = failed
> check, by that file's own rule); §2a now documents the four-step form.
> Full record: `docs/logs/2026-08-18-plan0110-fleet-demo-reset-deploy.md`.
>
> 🔴 **CARRIED RISK — s237's video rulings exist ONLY in a gitignored handoff**
> (`.claude/handoffs/session-237/…-CLOSE-…`): Cray's option-(A) ruling, the CTA
> decision (*no demo URL on screen*, or viewers hit the Access wall), and the
> beat-4 Tab G→H remap. `git grep` finds none of it. Needs a tracked home before
> the clip is shot.

### Rotated 2026-08-20, session-241 reconcile — Current Focus s239

_[Rotated ONE session below R2's four-session window, deliberately. Keeping
this block would have left `docs/STATUS.md` at ~54 KB, over R1's 49,152 B soft
target, because the s241 reconcile added five citation-dense Active-TODO
corrections. Current Focus therefore holds s240 + s241 only. The trade is R2's
window against R1's soft target — neither dominant — and the content is
preserved verbatim here rather than trimmed.]_

> **Session 239, 2026-08-18→19 (head_commit `32854ab` → `dbb3e58`) — EIGHT PRs
> MERGED (#1216–#1223), 0 open, and TWO host-state deploys to MS-S1 under two
> separately typed §8 gos.**
>
> 🔴 **The organising finding, and it is not about any one artifact: a summary
> that is ACCURATE about what it cites still shrinks.** s237's handoff cited the
> storyboard's ruling table (four rulings) and was correct; s238 inherited that
> and was correct; the actual count was **seven**, because one was typed two days
> earlier and recorded INLINE in the beat it governs rather than in the table —
> and it is the one with a live tripwire (*"a number enters beat 2.5 or 4"*).
> Going to the ORIGINATING artifact rather than the latest summary is what
> recovered it. Everything now lives in `docs/strategy/public/intro-video-production-rulings.md`,
> tracked, each row carrying its **date and source position** for exactly this
> reason. Before #1216, `git grep` over the repo returned **ZERO** hits for the
> CTA ruling, `barely say`, `verify-chain` and `founder on camera`.
>
> 🔴 **A correct fix silently disarmed the guard that was watching it — measured,
> and the more transferable half of the session.** s238 rightly corrected every
> documented host path to forward slashes, because a backslash is stripped by the
> ssh→PowerShell chain and fails as a missing file. `test_every_documented_operator_path_resolves`
> accepted a drive letter only before a **backslash**, so that correction moved
> ten `docker compose -f C:/…` commands OUT of its reach and the guard matched
> **zero** of them. ⚠️ **The module's own anti-vacuity floor (`checked >= 5`)
> stayed satisfied by the READMEs the whole time** — a count floor cannot see a
> category of document going dark. Widened to every profile `*.md` and the regex
> fixed: **26 paths checked, 0 broken**, eight of them previously unreachable and
> three (`DEMO-RESET.md`) unchecked since the day they were written.
>
> 🔴 **The shared deploy script cannot deploy this system, and the runbook handed
> it over without saying so.** Plan mode — which touches nothing, verified in the
> code rather than taken from the docstring — printed `oct-energy` in every
> literal. `--execute` would have built and shipped the wrong profile's image and
> recreated a container on a system nobody meant to touch. The fact was already
> recorded in three places, none of them where §3 sends a reader: a **routing**
> gap, not a knowledge gap. Fixed at the point of handover (#1220), and the
> missing procedure now exists — `deploy/published/oct-fleet-maintenance/DEPLOY.md`
> (#1221), the procedure tier this system never had. Its **first real use found
> its own gap**: §2 said to diff `<last-deployed-sha>..HEAD` without saying the
> sha comes from the HOST's checkout, which is not the image's build sha — here
> `205ba4b3` vs `907a842`. Corrected in the same PR as the deploy record (#1223).
>
> ✅ **Tab F now opens the raw customer story its procedure was formalised from**
> (#1218), with six passages numbered against `governed_repair_approval`'s six
> steps and the legend built from the procedure's **live** steps. `reshape` is
> deliberately left unmapped and the legend says so — it is platform machinery,
> not a rule the business stated, and forcing a sentence onto it would make the
> panel's claim false in the one place a careful viewer checks. Needs no
> infrastructure: `^/assets/.+$` is already allowlisted, `connect-src 'self'`
> already admits the fetch, Tab F is already published under SD-3. It had to live
> under `services/` because the Dockerfile COPYs that and **pointedly not `docs/`**.
>
> ✅ **R8 RULED (Cray, typed): drop the ฿15,000 contrast from beat 4** (#1217).
> Measured this session and recorded by no prior artifact: the remap trades a
> **demonstration** for a **declaration** — no published tab renders the second,
> cheaper repair routing to the fleet manager. Option (b), asserting it over Tab
> A's rings, was rejected as dishonest and the measurement made it worse than it
> looked — Tab A shows **three** anomalies, not the two `published.env` documents,
> and two of the three exceed the band floor.
>
> ✅ **The header brand mark is the Cray.J logo** (#1222), deployed and confirmed
> by Cray on the live surface. Recorded rather than discovered later: it is **not
> legible at 28 px** — the artwork paints at 7% of source scale, so the wordmark
> inside it renders about 16×4.6 px. Cray chose that form knowingly from three
> options; the fix is cropping the artwork to the bunny and needs no code change.
>
> **Both deploys were do-no-harm verified against a baseline captured BEFORE the
> first action**: this system's `cloudflared` and `postgres` kept their container
> ids and uptimes both times — the tunnel never re-registered, `pgdata` was never
> at risk — and both sibling systems' four containers were untouched. The demo
> read `DEMO-STATE: PRISTINE` before and after each, so **`--execute` appears
> nowhere in what was executed** and no row was deleted. Image id **IDENTICAL on
> both machines** each time, which is the guarantee — "a rebuild produced the same
> id" is not, since buildkit's provenance attestation makes an id identify a build
> rather than its content.
>
> ⚠️ **The half neither deploy could close: the render through Cloudflare Access.**
> It needs an interactive PIN no automated step can satisfy. Cray closed it both
> times by opening the live system, and both records say so — recorded as **Cray's
> observation, not this process's measurement**, because blurring that would make
> the next deploy's "verified" weaker than it reads.
>
> **Gates: 4170 passed / 8 skipped**, `mypy --strict services/ verticals/` clean
> over 201 files, bare `ruff check .` + `ruff format --check .` clean over 642.
> Twenty-two non-vacuity probes across the session, each restored from a `/tmp`
> copy and each seen RED with a message naming what broke. Host records:
> `docs/logs/2026-08-18-s239-fleet-origin-narrative-deploy.md` and
> `docs/logs/2026-08-19-s239-brand-mark-deploy.md`.

### Rotated 2026-08-21, session-241 second reconcile — Current Focus s241 (first version)

_[The s241 block was REWRITTEN in place rather than rotated out: the session ran
two days and five PRs, and one session keeps one block. This is its first
version, covering PR #1229 only, preserved for the detail the rewrite compressed
away — the measured cost of the stale DNS claim, and the "no RED witnessed"
record.]_

> **Session 241, 2026-08-20 (head_commit `8fd3848` → `5cdbf68`) — ONE PR MERGED
> ([#1229](https://github.com/CrayJThiemsert/vero-lite/pull/1229)), 0 open: the
> `ms-s1-ollama` skill's seven-model snapshot REMOVED (not refreshed) and two
> stale claims corrected.**
>
> 🔴 **The organising finding: two of the three were corrections the file had
> ALREADY made in its own body, then contradicted in its own footer and helper
> script.** `SKILL.md` fixed the DNS claim at s171 and the §8 gate pointer at
> s174; `warm.sh:11`'s *"`ms-s1-max` has no WSL DNS entry"* and the footer routing
> the gate to *"the active PLAN/handoff"* were never propagated. **A correction
> that lands at the top of a file and is not propagated reads as settled — while
> the stale copy stays the one an operator follows.** Measured cost:
> `services/api/config.py` defaults `ollama_host` to `http://ms-s1-max:11434`, so
> *"does not resolve"* made a live default read as inert. It is not — a test that
> reached it ran `gpt-oss:20b` twice with no §8 go.
> <!-- retired: "`ms-s1-max` has no WSL DNS entry" -->
> <!-- The line above QUOTES a dead claim to narrate its correction. The marker
>      is what makes that legible to the guard and to a skimming reader: a live
>      surface repeating a retired claim labels it dead where it appears. -->

>
> 🔴 **The snapshot was REMOVED, not refreshed** (dated 2026-06-11, seven models;
> the box holds eleven): a refresh rots at the next `ollama pull`, re-measuring to
> rewrite it is **itself a host-state call needing its own go**, and it held
> nothing durable — the `gpt-oss:20b` pin and `qwen3.x` = NOT_JSON already live
> under *"The pinned model"*. All three claims had **zero tracked hits** before
> this PR: they lived only in a gitignored handoff and would have died with it.
>
> ⚠️ **No RED was witnessed, and that is recorded rather than papered over** — no
> test or guard reads either file, so there is no oracle to mutate; a
> comment-and-prose change, not dressed up with a vacuous guard. Gate **pass**
> (8m30s), `sha=MATCH` across local HEAD / PR head / the run's own `head_sha`;
> merged content re-verified on `main` via `git show HEAD:<path>` (3 new strings
> present, 3 old gone). **No host-state action; MS-S1 was not contacted.**
>
> 🔴 **A five-agent grounded fan-out re-ranked next work and returned
> claim-vs-code corrections with ZERO tracked hits — folded into the Active TODO
> rows below, which own the detail:** PLAN-0108's *"nothing gates it"* is false
> (SD-1 routed, not ruled; Step 1 G2-gated) and it wears **two AC-5 labels**;
> PLAN-0107's AC-9 Step-7 probe is **unrunnable as written**; PLAN-0109's AC-11
> would **delete a true sentence and write a false one**.

### Rotated 2026-08-21, session-241 second reconcile — Active TODO rows, pre-round-2

_[The PLAN-0107 and PLAN-0108 rows below are their versions BEFORE the round-2
reconcile shrank their now-discharged annotations. What is unique here is the
FULL s240/s241 correction text — the AC-11 checkbox drift, the AC-9 probe
diagnosis, the AC-10 off-by-one and the two-AC-5 finding — which the live rows
now compress to a pointer, because the PLANs themselves carry them.
_[Corrected at write time: an earlier draft of this note said the +74 s CI
measurement and the three Phase-A prose divergences no longer appear live. They
do — the reconcile kept both. The report this note was written from listed them
as removed; the tree says otherwise, and the tree wins. Checked after the
append, not assumed.]_
The deploy.py row is fully discharged and rotated for good — its
durable homes are deploy/published/deploy.py, tests/deploy/test_deploy.py and
lesson 0043.]_

**PLAN-0107 row (pre-round-2):**

- [ ] **PLAN-0107 — oracle-coverage hardening: `Draft`, 15 ACs. ✅ Phase A CLOSED 6/6 s236 ([#1204](https://github.com/CrayJThiemsert/vero-lite/pull/1204)); ✅ Phase B's AC-7 + AC-8 CLOSED s236 (#1206 `7a37c6d`, #1207 `5aedaf2`) and ✅ AC-11 CLOSED s240 ([#1226](https://github.com/CrayJThiemsert/vero-lite/pull/1226)). Remaining: Phase B's AC-9 (design-blocked) + AC-10, and Phase C — NOTHING gates them.** _[Corrected s240, `was an error`: this row read "Phases B and C remain", which had been false since s236.]_ CI now runs four oracles it lacked — `node --check`, the asset↔reference bijection, a **per-vertical** lifespan boot smoke, `mypy --strict verticals/` and the two adopted pre-commit hooks (**measured +74 s, no new dependency**). ⚠️ **Executing the remainder: read each AC and its `Reviewer amendment` blocks as authoritative and treat the §Steps prose as narrative — three measured divergences in Phase A alone** (a retired `≥ 20` floor, a superseded asset count, `uvx` vs `uv run --no-sync`). _[Also corrected s240: this row's *"with today's 2-case live seed nothing overflows"* — the stated reason for holding a browser stage back — has **expired on that ground**; AC-7 grew the seed and the tree now holds **21** cases. ⚠️ **The same stale sentence is still in the PLAN itself.**]_ _[Corrected s241: (a) **AC-11 closed s240 but its checkbox in the PLAN still reads `[ ]`** (`0107:295`) — STATUS and the PLAN disagree and the PLAN is the stale one. (b) 🔴 **AC-9 is not merely "design-blocked" — its Step 7 probe is UNRUNNABLE AS WRITTEN, SURFACED to Cray:** it names `services/engine/demo_events.py:62` as the `below` comparison to invert, but that line **delegates** — the comparison lives at `services/engine/recommender.py:77-79`; and `tests/services/engine/eval/test_eval_harness.py` loads traces as static JSON with **zero** references to `demo_events` or `crosses_threshold`, so the mutation is unobservable there **by construction**. Executing it as written would manufacture an ADR-0038 **class-C1** guard inside the PLAN that exists to eliminate class-C1 guards. (c) **AC-10's scope is off by one** — it says *"nl-01…nl-12"*, but nl-12 is the set's only `ceiling: true` case, so the real remainder is **nl-01…nl-11 (eleven)**.]_ **Read the PLAN, never a restatement:** `docs/plans/done/0107-oracle-coverage-hardening.md` (§Phase A closing evidence · §Acceptance Criteria).

**PLAN-0108 row (pre-round-2):**

- [ ] **🆕 PLAN-0108 — AC-authoring + pre-close convention hardening: `Draft`, UNRATIFIED.** The weak-oracle half of the same audit. _[Corrected s241, `was an error`: this row read *"its only blocker was ADR-0038, which has landed, so nothing gates it either"* — measured s241, **SD-1 is NOT ruled, it was ROUTED to Cowork** (`0108:209`: *"Not ruled here… Until it returns and is ratified, §8 as written governs"*), **three of six ACs close only on Cray's PR-merge judge read**, and **Step 1 is G2-gated for Code** (`0108:240-242`). 🔴 **The PLAN also wears TWO ACs both labelled AC-5** — `:93` `[check]` staleness-guard and `:156` `[evidence]` retro-classification, six items under five labels, in a PLAN whose subject is AC-authoring hygiene.]_ Owns ADR-0038's **OQ-5** — the staleness-guard obligation attaches to the PLAN template, not to a build task. **Read the PLAN, never a restatement:** `docs/plans/0108-ac-authoring-and-preclose-convention-hardening.md`.

**deploy.py dead-compose-path row (discharged, rotated for good):**

- [x] **`deploy.py`'s dead compose path — FIXED s235 ([#1193](https://github.com/CrayJThiemsert/vero-lite/pull/1193)).** Found s232 and live on `main` for three commits; Phase 1 would have died on the next `--execute`. The path is now the module constant `_LOCAL_COMPOSE`, guarded by a test that walks the module's own path constants, so a future straggler reddens by construction. **Read the code and the guard, never a restatement:** `deploy/published/deploy.py` · `tests/deploy/test_deploy.py`. ⚠️ **That guard's first draft masked its own oracle** — homed in [`docs/lessons/0043-*.md`](lessons/0043-a-probes-red-must-name-what-broke.md), now binding via `CLAUDE.md` §8's witnessed-RED rule.

> **Session 240, 2026-08-19 (head_commit `dbb3e58` → `8fd3848`) — THREE PRs
> MERGED (#1225–#1227), 0 open. PLAN-0107 AC-11 CLOSED, `DEPLOY.md` gained a
> pre-ship check, and PLAN-0111 was drafted with all six of its SDs ruled in the
> same session.**
>
> 🔴 **The organising finding: three losses of correct work, two of them mine
> this session — each caught by a discipline, none by re-reading a summary.**
>
> 🔴 **(1) A `git merge` reported success and silently reverted a merged PR.** It
> first died with `Unable to write index` although the two sides touched disjoint
> files; `git status` then read *"All conflicts fixed but you are still merging"*
> with **no `index.lock` on disk**. Concluding it produced a merge commit whose
> tree **dropped #1225's entire `DEPLOY.md` change** — while `git merge-base
> --is-ancestor origin/main HEAD` answered **YES**. **Ancestry is not content.**
> Caught by grepping the merged tree for a string only the incoming side
> introduces; recovered by `git reset --hard` to my own commit and re-merging,
> which reported the expected `53 insertions(+)`.
>
> 🔴 **(2) The first non-vacuity probe proved the wrong thing.** The scenario's
> `assert status_code == 422` sat *before* the month-end read, so disarming the
> guard reddened **that** line and returned — the money assertion, the claim the
> module exists to make, never executed. Reordered so the ฿ assertions fire
> first; the RED now reads `assert Decimal('-15000.00') == Decimal('20000.00')`,
> the export holding one row carrying the credit note's document date.
>
> ⚠️ **(3) Two ACs in the first-pushed PLAN-0111 draft named test files that do
> not exist** — corrected to grep-verified paths. Separately, swapping a stale
> line citation for a symbol produced a *wrong symbol* (`get_case` for
> `get_closeout`) until the enclosing function was grepped rather than assumed.
>
> ✅ **PLAN-0107 AC-11 CLOSED — negative money refused at the close-out producer**
> (#1226), plus a four-test scenario module. 🔴 **Why a refusal and not `sum()`:**
> `repair_case_closeout` is append-only with **latest-wins** — `latest_closeout`
> returns one row per case and both consumers read it, so a credit note keyed
> there does not join the invoice, it **REPLACES** it. Measured: month-end moves
> `20,000.00` → `-15,000.00` with every row still looking perfectly filled in.
> Admitting the negative is the **silent** option, not the lenient one. 🔴 **It
> closes an asymmetry rather than adding a rule** — the quote side already refused
> negative money on the same reasoning
> (`tests/api/test_cases_endpoint.py::test_a_negative_quote_is_refused`, *"Not a
> discount — a typo or a credit note"*); the close-out was the outlier, and it is
> the end that feeds the month-end figure. A credit note is internally
> **coherent** (`-14,018.69 + -981.31 = -15,000.00`), so it passes the existing
> totals check — the sign check is its own door, and the scenario pins that
> discriminator. The refusal is **INTERIM**, says so in the handler docstring, and
> names its lift condition: only with a schema holding invoice and credit as two
> coexisting facts.
>
> ✅ **`DEPLOY.md` §2a Pre-ship** (#1225) — build locally, then compare a
> `sha256sum` taken **inside the freshly built image** against the working tree,
> before the host is touched at all.
>
> ✅ **PLAN-0111 drafted and all six SDs RULED** (Cray, typed 2026-08-19, #1227);
> `Status: Draft` — the SDs were ratified, not the PLAN. **SD-E: multiple partial
> credits may coexist** (ทยอยลด; over-credit refused 422), **which forces SD-A to
> (b), a separate `repair_case_credit_note` table** — latest-per-kind would re-arm
> the replacement trap one level down. SD-B (b) one composite reader · SD-C (b)
> two lines matching real documents · SD-D (a) credit inherits the case's `RC-`
> number · SD-F (a) KPI counts repairs, not documents. Newly load-bearing from
> those rulings, each verified against code: the new table must join retention's
> `_FK_CHILD_MODELS`; 🔴 **`load_monthly_export`'s ungoverned branch enumerates
> cases only from `RepairCaseCloseout.entered_at`, so a credit-only month would
> emit no row at all** and must union a second source; and 🔴 **AV-2 stopped being
> hypothetical** — a table FK'd to the close-out with no `case_id` column is
> invisible to both retention walks, prohibited without a guard extension
> witnessed RED first. ⚠️ **AV-1 is the one thing this repo cannot answer** — what
> Express/accounting reconciles a ใบลดหนี้ against; SD-C is provisional on it, and
> the PLAN requires confirming it before Step 4, not before merge.
>
> **Gates: 4174 passed / 8 skipped** (4170 baseline + 4), `mypy --strict services/
> verticals/` clean over **201** files, bare `ruff check .` + `ruff format
> --check .` clean over **643**. Three non-vacuity probes witnessed RED: the
> `DEPLOY.md` operator-path guard naming `DEPLOY.md:111` · the guard-disarm
> reddening the ฿ assertion · the `< 0` → `<= 0` tightening reddening **only** the
> zero-VAT positive control — disjoint sets, which is what makes the control a
> control. **No host-state action this session; MS-S1 was not touched.**
>
> ⚠️ **CARRIED FORWARD from s239's `next_action` — recorded here because the
> frontmatter cap cannot hold them and nothing else in this file does; none was
> touched this session, none is resolved:** (i) the **font-size decision still
> gates re-measuring every geometry number in the beat-4 mockup**; (ii) the
> **run-list backlog badge on the host is still unmeasured** (a host-state read,
> so it needs its own typed §8 go); (iii) the **three Advisory-proposal
> candidates are still unnamed**, so the gate panel still reads as unfinished.

> **Session 241, 2026-08-20→21 (head_commit `8fd3848` → `6a2e34c`) — FIVE PRs
> MERGED ([#1229](https://github.com/CrayJThiemsert/vero-lite/pull/1229),
> [#1231](https://github.com/CrayJThiemsert/vero-lite/pull/1231)–#1234), 0 open:
> it opened as *"rank the next work"* and became a MECHANISM change.**
>
> 🔴 **The grounded fan-out found the backlog was RETRIEVAL debt, not technical
> debt** — eight measured facts `git grep` could not find, because they lived
> only in a gitignored handoff and would have died with it. So the work became
> two guards that make such debt findable: `tools/check_retired_claims.py`
> (hook #18) and `tools/check_ac_consistency.py` (#19); the row below states
> the limits each one declares about itself.
>
> 🔴 **Both caught real defects before they could merge — neither was built from
> a hypothetical.** The retired-claim guard **blocked its own first commit**,
> exposing a real design flaw: a file exempted from *declaring* could not exempt
> *its own examples* either (fixed with `Marker.local_only`). It then flagged
> **this file** — STATUS's own narrative quoted a dead claim. The AC-ledger
> guard's first run named PLAN-0108's live duplicate label, and a second nobody
> knew about in `docs/plans/done/0042-at2-managerial-build.md`.
>
> 🔴 **The tempting wrong fix, recorded because it will recur:** narrowing the
> retired text until STATUS's quote stopped matching would have silenced the
> guard — **that is editing the artifact to satisfy the instrument.** A marker
> went beside the quote instead, so on a surface an agent reads every session a
> dead claim carries a label saying so — *"`ms-s1-max` has no WSL DNS entry"*.
> <!-- retired: "`ms-s1-max` has no WSL DNS entry" -->
>
> ⚠️ **One honest failure, recorded not dropped: findings were reported from a
> subagent that never returned.** Four of five grounding agents came back; the
> fifth failed silently and its notice arrived much later. **Two rows of the
> ranking's claim-vs-code table were written with no source** and were RETRACTED
> on measurement (a `/runs` docstring citation, a scenario-marker census) —
> items ranked #8 and below only, not the #1/#2 picks. The memory rule *"verify
> a subagent delivered"* existed and was not applied.
>
> ✅ **The documentation debts then landed** — #1232 PLAN-0107's five, #1233
> PLAN-0108's duplicate label; the rows below own them. Gate on `6a2e34c`: **4206 passed / 8 skipped**, `ruff` + format clean
> over 647, `mypy --strict` clean over 201 files; every PR `sha=MATCH` across
> local HEAD, PR head and the run's own `head_sha`.


## Rotated this reconcile — session 245 (2026-08-22)

Rotated out of `docs/STATUS.md` while reconciling **PLAN-0112 Step 5 SHIPPED,
AC-5/AC-6 CLOSED** (#1252–#1255). This is the **session-242** block, moved
byte-exact by slice rather than retyped, and verified present here and absent
from STATUS after the move. It rotates one session below R2's four-session
window — **deliberately**, the same call the s244 reconcile recorded: STATUS
stood at 61,636 B, 12,484 B over R1's 48 KB soft target, and a new block cannot
be written without either this rotation or a trim that would delete facts. Its
live remainders were already carried elsewhere before the move: PLAN-0110 SD-E's
reversal and ADR-0035's L1 re-read each hold an Active-TODO entry, and
PLAN-0107 AC-10 is recorded in that PLAN.

> **Session 242, 2026-08-21 (head_commit `30b9488` → `bf2771e`) — FIVE PRs
> MERGED ([#1237](https://github.com/CrayJThiemsert/vero-lite/pull/1237)–[#1241](https://github.com/CrayJThiemsert/vero-lite/pull/1241)),
> 0 open. PLAN-0107 AC-10 CLOSED, and FOUR Cray rulings landed — two of them
> re-opened settled ground.**
>
> ✅ **AC-10 closed the last gold-versus-gold oracle.** `nl-01…nl-11` were checked
> only against themselves — a shape that reddens on a malformed file and **cannot
> redden on a wrong value**. All eleven now grade against the real engine; a probe
> run BEFORE the test returned `VERDICT=ALL_ELEVEN_REPRODUCE`, so **no gold value
> was edited** and the register shipped EMPTY, measured.
>
> 🔴 **Cray REVERSED PLAN-0110 SD-E — and grounding it corrected the commission
> itself, three times:** quote-acceptance rather than case creation is the
> governable moment; a SECOND door is excluded from the published allowlist by
> design; and a no-principal firing does not leave a run *ungoverned* — it mints
> one **nobody can ever approve**.
>
> 🔴 **Cray re-read L1 a SECOND time** — *"one gate, no app code"* becomes *"app
> code may READ the gate's verdict for provenance, never perform gating itself."*
> That pass read **126 insertions, 0 deletions**: a LOCKED ruling is not edited.
> Its trigger was Cray's own reasoning failing a measurement — SD-1(b) rested
> partly on *"use the email they logged in with"*, **measured FALSE at the app
> layer**; the ruling stands and the amendment is what makes that half true later.
>
> ⚠️ **Five times a report disagreed with the tree, and the tree won every time** —
> two drafter claims, hook #19 firing on this session's own STATUS edit, guard R7,
> and **three greps of mine that returned 0 on text that was present but
> line-wrapped**. Nothing but opening the file separated instrument from subject.


## Rotated this reconcile — session 246 (2026-08-22)

Rotated out of `docs/STATUS.md` while reconciling **PLAN-0112 Steps 6 and 7 —
AC-7(ii), AC-8 and AC-9 closed, and the visitor flow proven on the live published
system** (#1256–#1258). This is the **session-243** block, moved byte-exact by
slice rather than retyped, and verified present here and absent from STATUS after
the move. Its live remainder is not lost: G-13/G-14/G-15 are defined in
`docs/plans/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md`, which the
Active-TODO entry points at — the very fact the s245 reconcile measured when it
discharged the trim prerequisite.

> **Session 243, 2026-08-21 (head_commit `bf2771e` → `0b5c333`) — TWO PRs
> MERGED ([#1243](https://github.com/CrayJThiemsert/vero-lite/pull/1243),
> [#1244](https://github.com/CrayJThiemsert/vero-lite/pull/1244)), 0 open. All
> SEVEN of PLAN-0112's Surfaced Decisions are RULED and its Step-2 gate is
> DISCHARGED — and measuring before each ruling corrected EIGHT things the PLAN
> asserted, two of which would have contradicted each other silently at build
> time. Both PRs are rulings + measurements; the build is still owed.**
>
> 🔴 **G-14 — two of Cray's own rulings did not compose, and the failure would
> have been SILENT.** SD-2(b) says a changed accepted amount fires a new run;
> SD-5(b) fires through the event bridge, whose `event_key` hashes vertical,
> event kind, sorted entity ids and a time bucket — **the amount is not in the
> key** — and `fire_event_run` returns `ALREADY_FIRED` without starting
> anything when the derived run id already exists. The ruled re-fire would have
> been swallowed by the ruled mechanism's own idempotency: **no error, no log,
> nothing to see.** Constraint recorded for the build: key `entity_ids` on
> `[case_id, quote_id]`. Two traps measured with it — `accept_quote` mints a
> fresh `accepted_id` on **every** call, so keying on it would let a
> double-click mint two runs; and the dedup window's time bucket would
> spuriously re-fire a same-quote accept once it elapses, so the window must be
> authored wide for a **human-driven, not polled** event.
>
> 🔴 **AC-2 carried a pass read that is FALSE in the shipped demo** — *"a
> sub-ceiling acceptance fires and completes with no gate"*. `reshape` consumes
> only the breach subset while intake is a **fleet-wide population scan**, and
> the seeded demo pair stays OPEN with breaching accepted quotes, so **every**
> visitor-fired run gates, sub-ceiling or not. Re-fixed to: the run exists, and
> the visitor's case appears in **none** of the gate's proposals.
>
> 🔴 **G-13 — the accepted-quote exclusion is load-bearing PROSE at two tracked
> sites SD-3 never counted** (`seed_settled_history_case`'s docstring in
> `verticals/fleet_maintenance/operate_seed.py`, and the same claim inside
> `tests/api/test_operate_seed_spend_scenario.py`) — invisible to a call-graph
> review because **neither calls the endpoint; each asserts it is
> unreachable**. Under SD-3(a) the gate-reachability clause goes FALSE **and
> must be corrected in the same PR that adds the ingress row** (still owed —
> both sites read as written today); the ฿-report clause stays TRUE
> (`/closeout` is still excluded) and `seed_settled_history_case` **remains
> necessary** — only its reason sentence splits.
>
> ⚠️ **Two corrections made a ruling CHEAPER, not more expensive** — recorded
> because the reflex is the opposite. The accepted-quote route is absent from
> the published config's admitted rows but is on **no** cross-system deny list,
> so SD-3(a) reverses a per-system omission, not a floor. And flipping SD-5's
> *declared* trigger does not break manual firing (the runnable-trigger
> allowlist admits all three; the run endpoint never reads the declared
> trigger) — while the *"only manual runs in Phase 1"* comment **already
> misdescribes its own file**, which ships a `schedule` trigger. (b) corrects a
> stale comment, not a live lock.
>
> ⚠️ **SD-2's ruling is NOT the option the PLAN recommended** (it recommended
> once-per-case); the stamp says so plainly. SD-2(b) + SD-6(b) + SD-7(a)+(c)
> compose as a deliberate posture: audit completeness, a bounded *display*, and
> manual operator cleanup.
>
> **Method, worth one clause:** the G-13 corrections came from reading code —
> **G-14 came from laying two rulings on top of each other and asking what the
> code would do if both were true.** Per-decision review cannot see that class.

### Current Focus block — Session 243 cont. (PLAN-0112 Step 1 executed, AC-1 CLOSED, #1246) [rotated 2026-08-23, session-247 reconcile — 4-newest-sessions CF window; the OLDEST of exactly four, evicted because a new block forces a rotation]

⚠️ It rotated on the **window rule alone**. The session-247 reconcile recorded at #1263 that this block was *"the single Current Focus block over R2's 4,096 B per-block cap (4,936 B)"*; that figure is **retired as an error**. Measured with a parser bounded by the block's own contiguous blockquote run it is **2,567 B — under cap**. The 4,936 B reading came from bounding blocks header-to-header, so the LAST block swallowed the `_[Current-Focus rotation ledger]_` paragraph that belongs to no block — session 246's instrument failure #1, repeating verbatim.

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

### Current Focus block — Session 244 (PLAN-0112 Steps 3 and 4 BUILT; #1248/#1249/#1250) [rotated 2026-08-23, session-248 reconcile — 4-newest-sessions CF window; the OLDEST of exactly four, evicted because a new block forces a rotation]

⚠️ **Window eviction, NOT a cap overage** — the block measures 3,405 B against R2's 4,096 B per-block cap. Recorded explicitly because #1263 once misread a rotating block as over-cap (a header-to-header measurer swallowing the rotation ledger), and #1264 retired that claim; every rotation note here now states which of the two rules did the evicting.

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

_[Rotated 2026-08-23 (s249 reconcile) out of `docs/STATUS.md` §Current Focus — window rule (4 most-recent sessions), not a cap overage.]_

## Rotated this reconcile — sessions 250 + 251 (2026-08-24), Current Focus 4-session window

_A TWO-SESSION reconcile (s250's four PRs #1271–#1274 and s251's #1275 landed against a
STATUS still stamped `session: 249`), so two blocks entered and two left, holding the
window at four. **Both rotated on the window rule alone — NOT on a cap overage.** Measured
at this reconcile with each block bounded by its OWN contiguous blockquote run (the #1264
repair, never header-to-header): every block on both sides of the rotation is under R2's
4,096 B per-block cap. The s250 reconcile rotated no CF block of its own — its four PRs
were governance plumbing — so the ledger entries for the s246 and s247 reconciles travel
into this file with the blocks they explain._

_R2 carve-out, checked per block BEFORE the move: s246's PLAN-0112-COMPLETE and live-walk
substance lives in `docs/plans/done/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md`
plus `docs/logs/2026-08-22-s246-*.md`; s247's trim-and-split substance in
`docs/runbooks/memory-architecture.md` §R2 and the `2026-h1h-status.md` header; each keeps
its own Recent Decisions row in STATUS. ⚠️ **Two facts had NO tracked home outside these
blocks and were carried out FIRST, not after** — the `sed`-never-matched-inside-`wsl bash
-lc` hazard and the stale-`__pycache__` same-length-mutation hazard now live in
`docs/lessons/0007-harness-exit-code-artifact.md` §4.1, where a reader running a probe
will meet them at the moment of need._

### Current Focus block — Session 247 (the Active-TODOs pointer-cap trim, the R4 continuation split, and a retired 4,936 B measurement) [rotated 2026-08-24, sessions-250+251 reconcile — 4-newest-sessions CF window]

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

### Current Focus block — Session 246 (PLAN-0112 COMPLETE 9/9 and archived; the visitor flow proven LIVE) [rotated 2026-08-24, sessions-250+251 reconcile — 4-newest-sessions CF window]

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


<!-- rotated from docs/STATUS.md at the s253 reconcile (sessions 248 + 249) -->

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

## Rotated this reconcile — session 254 (2026-08-25), Current Focus 4-session window

### Current Focus block — Session 250 (the In-Flight + rotation-ledger caps)

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


## Rotated this reconcile — session 251 (s255 reconcile, 2026-08-26)

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

## Rotated this reconcile — session 252 (s256 reconcile, 2026-08-26)

### Current Focus block — Session 252 (PLAN-0113 Steps 3–7, SD-3 RULED (b), and the empty-gate dead end first recorded) [rotated 2026-08-26, s256 reconcile — 4-newest-sessions CF window; the OLDEST of exactly five, evicted because the s256 block forces a rotation. Its substance keeps tracked homes: PLAN-0113 is archived at `docs/plans/done/0113-scope-event-fired-run-to-its-firing-case.md` (which now carries a pointer to PLAN-0114 for the SD-3 execution), and the dead end it recorded is CLOSED by PLAN-0114 Steps 2–3.]

> **Session 252, 2026-08-25 (head_commit `968b34e` → `c8f685e`) — SIX PRs
> MERGED ([#1279](https://github.com/CrayJThiemsert/vero-lite/pull/1279)–[#1284](https://github.com/CrayJThiemsert/vero-lite/pull/1284)),
> 0 open, CI green per-sha on every merge, tree clean. **PLAN-0113 EXECUTED end
> to end and ARCHIVED at `COMPLETE 8/9 — offline`; PLAN-0113 AC-3 through AC-8
> CLOSED, AC-9 (live) CARRIED not dropped.** Fleet's `intake` now carries
> `scope_by: {field: case_id, from: trigger.entity_ids}` + `when_absent: sweep`,
> so a visitor who accepts a quote sees a gate proposing **exactly one case —
> their own**.**
>
> 🔴 **The `intake` fleet-wide scan is GONE — every narrative above that rests
> on it is superseded.** The s249 root-cause paragraph (*"fleet's `intake` is a
> fleet-wide scan, so the event triggers the run but does not scope it"*) was
> true when written and is now history. The four `done/` record sites carry the
> ruled two-part supersession (PLAN-0113 Step 7): `done/0112` SD-4, its AC-7(i)
> NARROWED clause and its AC-2 sub-ceiling re-fix, plus `done/0110`'s s245
> population bound.
>
> 🔴 **Scoping made a dead-end run reachable for the first time, and it is
> RULED.** A **sub-ceiling** acceptance now parks at `approve` with an EMPTY
> proposal list; `/gate/resolve` answers 409 and only `/cancel` exits — which
> records *abandonment* for a case that was checked and cleared. **PLAN-0113
> SD-3 RULED (b)** (Cray, typed): such a run must reach `completed`.
> **PLAN-0114** carries the build, with **SD-2 (dual audit)** and **SD-3 (the
> RF-1 floor — any authenticated human)** both ruled as recommended. Grounding
> found the engine ALREADY sanctions the completion (`resume_run`'s no-decision
> branch); the gap is **reachability** from the product surface, so no ADR-016
> amendment is needed.
>
> ✅ **Two PLAN predictions were MEASURED WRONG and corrected in place, not
> absorbed:** the sub-ceiling run "completes with no gate" (it parks with an
> empty one), and the witnessed-RED cardinality "3 proposals" (measured: **2**).
> Neither changed an AC's conclusion.
>
> ✅ **AC-4 registered an INEXPRESSIBLE case rather than upgrading it to a
> pass** (CLAUDE.md §8): `scope_by` requires a declared `reads` list and **no
> step of procurement's `emergency_sourcing_round` declares one**, so its event
> path structurally cannot carry the clause; the control was re-aimed at the
> calm path's `read_stock`.
>
> ✅ **`tools/probe_coverage.py` shipped** — lesson #0047 §6's fourth clause,
> computed from the AST. Three batteries used it (47/47, 43/43, 53/53 claims, 0
> gaps); it caught a **vacuous assertion written the same session** and refused
> to run until every claim owner had a named exemption mechanism.

<!-- rotated from docs/STATUS.md at the session-257 reconcile (2026-08-27) -->

> **Session 253, 2026-08-25 (head_commit `c8f685e` → `082a6f1`) — TWO PRs
> MERGED ([#1286](https://github.com/CrayJThiemsert/vero-lite/pull/1286),
> [#1287](https://github.com/CrayJThiemsert/vero-lite/pull/1287)), ONE OPEN
> ([#1288](https://github.com/CrayJThiemsert/vero-lite/pull/1288)), CI green
> per-sha on both merges, tree clean. **PLAN-0114 Step 1 SHIPPED — the
> `continue_no_decision_run` chokepoint**
> (`services/engine/procedures/persistence.py::continue_no_decision_run`),
> purely additive: five fail-closed refusals, SD-2's dual audit written at both
> levels, and an acknowledgment block that REFERENCES the governance pin rather
> than copying the procedure shape.**
>
> 🔴 **The session's real subject was the verification instrument, not the
> engine.** An adversarial review found **two of thirteen probes had been
> credited for reddening on a CRASH** (`AttributeError`, `KeyError`) rather than
> on the assertion each claimed — a published `13/13` was overstated, and was
> corrected in-PR with measured evidence. Root cause: the driver returned only
> `returncode == 0` and discarded captured output. The `goal-evaluator` had
> already found **five** residual gaps in work called done; all five were real.
>
> 🔴 **ADR-0038 D4's W-1 watch-list entry took its THIRD firing** — *"a probe's
> RED must name what broke"* (#0043), previously at exactly two. D4 names W-1 so
> the next distinct incident promotes without any census, and D1.6 makes
> promotion at three **an obligation, not an option**: leaving a counted class
> advisory requires an explicit typed Cray waiver recorded at the same site.
> **UNRESOLVED — it is SD-4 on #1288.**
>
> ✅ **Three PLAN-0114 corrections landed BEFORE Step 1 was written** (#1286),
> each grounded in a measurement of the live tree: AC-2(a)'s RED-witness recipe
> (`resume_run` carries a second, pre-existing guard refusing the same case with
> the same exception type, so the drafted probe could not have witnessed what it
> claimed); SD-3's *"the ONLY thing"* wording (measurably too strong — the seam
> is defense-in-depth); and guard 3's key — **`actor_person_id`, not a resolved
> `Person`**, because only **4 of 6** verticals ship a `principals:` block (not
> `aquaculture`, not `energy`), so a `Person`-keyed guard would permanently
> refuse **3 of the 18** gated steps and contradict the LOCKED SD-3.
>
> ✅ **Step 1's close-out is a measured battery, not a claim:** **14 tests, 17
> claims, 14/14 probes witnessed** with a per-probe evidence line (17 =
> witnessed 14 + exempted 3), GAPS 0, stale ids 0. `orchestrator.py` and
> `action_step.py` are **0 diff lines** — AC-4's byte-identical half — and both
> shipped parity tests stayed green, so the STOP tripwire never fired.
>
> **PLAN-0115 is DRAFTED and OPEN (#1288):** ship `tools/probe_battery/`, close
> two safety holes (a SIGTERM-surviving restore; a lock so the Stop-hook gate
> never evaluates a mutated tree), amend `CLAUDE.md` §8 to name the tool, and
> promote PLAN-0099's flake-attribution method to a lesson. **Four SDs await
> Cray.** Next build step: **PLAN-0114 Step 2**, where AC-1 and AC-2 close.
> ⚠️ **PLAN-0113 AC-9 (live on MS-S1) is still CARRIED, not dropped** — it needs
> a typed Cray go per occasion AND per phase.

_[Current-Focus rotation ledger — **CURRENT window only** (R2, Cray s250); earlier entries travel with their blocks into [`2026-h1d-current-focus.md`](status-archive/2026-h1d-current-focus.md), the full pre-trim ledger into [`2026-h1-status.md`](status-archive/2026-h1-status.md). Window = **253–256**. The **s254** reconcile rotated the **session-250** block; the **s255** reconcile rotated the **session-251** block. **THIS (s256) reconcile rotates the session-252 block**, holding the window at four (253–256) — on the **window rule alone, not a cap overage**. Its substance keeps tracked homes: PLAN-0113 is archived at `docs/plans/done/0113-scope-event-fired-run-to-its-firing-case.md`, which now carries an **additive pointer to PLAN-0114** for the SD-3 execution, and the empty-gate dead end that block first recorded is **CLOSED** by PLAN-0114 Steps 2–3. ⚠️ **Verified in BOTH directions (R6), and by content rather than presence:** the archived block is **byte-identical (2,778 B) to the same block at `git show HEAD:docs/STATUS.md`** and is absent from this file — a presence-only check would have passed on a pre-existing copy. The earlier ledger travel notes (s246/s247, s251) went into the archive with their blocks.]_

> **Session 254, 2026-08-25 (head_commit `082a6f1` → `f0f60fd`) — FOUR PRs
> MERGED ([#1288](https://github.com/CrayJThiemsert/vero-lite/pull/1288)–[#1291](https://github.com/CrayJThiemsert/vero-lite/pull/1291)),
> 0 open, CI green per-sha on every merge, tree clean. **PLAN-0115's four SDs
> are RULED (Cray, typed "เอาตามนี้") and ADR-0038's W-1 watch-list entry is
> PROMOTED to C6 on its third firing** — the D1.6 pass, dispatched, amended and
> merged the same session ([#1290](https://github.com/CrayJThiemsert/vero-lite/pull/1290),
> merged by Cray himself). #1289 was s253's own reconcile plus the owed R2/R6
> rotation, merged early so `main` stopped reading `session: 252`.**
>
> 🔴 **SD-2's two drafted options BOTH died on measurement — the ruling is a
> third thing neither draft proposed.** (a) *"silent + stderr note"* writes its
> note **nowhere**: a hook exiting 0 has stderr routed to the debug log only,
> and that log on this box holds **0 files and a dangling symlink**. (b)
> *"trail annotation"* corrupts **four control-flow reads** in `_goal_gate.py`,
> not merely dedup. Ruled: zero-residue in `goal.json` **upheld**; visibility
> moves to **Telegram keyed to the lock** — one ping on acquire, one on release
> if it deferred. The drafted *"no Telegram"* clause was **struck — it had no
> author and no reviewer**, and ADR-0018 VX-1 already names Telegram the warn
> channel of record.
>
> ✅ **The other three ruled with their measurements attached** (#1288):
> **SD-1** — helper + guard ship as **one indivisible deliverable**, effort
> corrected from ~36 to **53 sites / 50 files**, measured not estimated.
> **SD-3** — **defer**, and the Residual now records that the one
> fully-instrumented incident points **away from** the orphan-pytest theory.
> **SD-4** — (a), with the firing tally required in the **lesson file**, not
> carried by narrative.
>
> 🔴 **C6's predicate needed a legibility conjunct.** Firing 2's assertion
> fired correctly **at its own site**, so crediting it was right — the defect
> was **unreadable output**. A crediting-only predicate counts two and never
> triggers, which would have made the promotion unreachable by its own rule.
>
> ✅ **Step 4b can now satisfy Cray's own L-3 condition** (#1291) — it had
> shipped carrying **no W-1 tally at all**; its sequencing note records why
> PR-B waits on C6 (which now exists, so that gate is satisfied). ⚠️ **PR-A is
> now owed enforcement work under an Accepted ADR:** C6 names **PLAN-0115 Step
> 1 AC-2/AC-4** as its D2 form-(c) enforcer, so §8's pointer (Step 4a) must
> ride **in** PR-A rather than trailing it.

_[Rotated from `docs/STATUS.md` at the **s258** reconcile — the window holds at four (255–258) as the s258 block enters. Rotates on the **window rule alone**, not a cap overage: **measured 2,671 B**, inside the 4,096 B per-block cap. The block is archived byte-identical, untrimmed. ⚠️ **A correction travelling with it:** the session-257 handoff recorded this block as *"`s254` is 4,303 B — over"* the cap, and that number is **wrong** — pinning the block by its own first and last lines and measuring gives 2,671 B. The claim was never written to a tracked file, so nothing else needs repair; it is recorded here because the rotation is the last moment anyone would have checked it, and the next reader would otherwise inherit it.]_

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

_[Rotated from `docs/STATUS.md` at the **s260** reconcile — the window holds at four (256, 257, 258, 259–260) as the session-259–260 block enters. Rotates on the **window rule alone**, not a cap overage: **measured 1,984 B**, the smallest block in the outgoing window and well inside the 4,096 B per-block cap. The block is archived byte-identical, untrimmed. Its substance keeps tracked homes, each checked with `git grep` at this reconcile rather than assumed: PLAN-0115's closeout and its ten ACs are in `docs/plans/done/0115-probe-battery-driver-and-verification-instrument-hardening.md`; ADR-0038 C6's promotion (and the legibility conjunct its predicate needed) in `docs/adr/0038-advisory-lesson-promotion-three-strike-rule.md`; and the **stale-`.pyc` hazard** — a same-size mutation masked by CPython's *mtime-seconds + size* validation, which passed the full local suite and reddened **only in CI** — is documented in `tools/probe_battery/README.md` (3 references) and in `_battery.py` / `_snapshot.py`, which is where a reader about to trust a battery's GREEN actually looks. The **VX-1 `systemMessage` discharge** (it surfaces as `Stop says: …` to the user's UI only, and adopting it would break PLAN-0069 AC-3 parity) travels with the block and is also recorded in that PLAN's §Closeout.]_

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

_[Current-Focus rotation ledger — **CURRENT window only** (R2, Cray s250); earlier entries travel with their blocks into [`2026-h1d-current-focus.md`](status-archive/2026-h1d-current-focus.md). Window = **256, 257, 258, 259–260**. **THIS (s260) reconcile rotates the session-255 block** on the **window rule alone, not a cap overage** — measured **1,984 B** against the 4,096 B cap. ✅ **Both directions were checked, never inferred:** the slice was pinned by its first AND last line, checked for neighbour-bleed, checked absent from the target *before* the write, then verified present-in-archive and absent-from-STATUS **separately**, by byte **delta** rather than presence — a presence test passes on a pre-existing copy. Slice **1,984 B** · archive **+3,300 B** · STATUS **−2,644 B** across both rotations at this reconcile (this block and the s249 RD row). Substance keeps tracked homes, re-checked with `git grep`: `docs/plans/done/0115-*.md`, `docs/adr/0038-*.md`, and the stale-`.pyc` hazard in `tools/probe_battery/README.md` plus `_battery.py` / `_snapshot.py`.]_

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
