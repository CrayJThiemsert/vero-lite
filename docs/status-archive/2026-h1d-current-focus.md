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
