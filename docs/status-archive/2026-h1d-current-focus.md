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

- [ ] **PLAN-0107 — oracle-coverage hardening: `Draft`, 15 ACs. ✅ Phase A CLOSED 6/6 s236 ([#1204](https://github.com/CrayJThiemsert/vero-lite/pull/1204)); ✅ Phase B's AC-7 + AC-8 CLOSED s236 (#1206 `7a37c6d`, #1207 `5aedaf2`) and ✅ AC-11 CLOSED s240 ([#1226](https://github.com/CrayJThiemsert/vero-lite/pull/1226)). Remaining: Phase B's AC-9 (design-blocked) + AC-10, and Phase C — NOTHING gates them.** _[Corrected s240, `was an error`: this row read "Phases B and C remain", which had been false since s236.]_ CI now runs four oracles it lacked — `node --check`, the asset↔reference bijection, a **per-vertical** lifespan boot smoke, `mypy --strict verticals/` and the two adopted pre-commit hooks (**measured +74 s, no new dependency**). ⚠️ **Executing the remainder: read each AC and its `Reviewer amendment` blocks as authoritative and treat the §Steps prose as narrative — three measured divergences in Phase A alone** (a retired `≥ 20` floor, a superseded asset count, `uvx` vs `uv run --no-sync`). _[Also corrected s240: this row's *"with today's 2-case live seed nothing overflows"* — the stated reason for holding a browser stage back — has **expired on that ground**; AC-7 grew the seed and the tree now holds **21** cases. ⚠️ **The same stale sentence is still in the PLAN itself.**]_ _[Corrected s241: (a) **AC-11 closed s240 but its checkbox in the PLAN still reads `[ ]`** (`0107:295`) — STATUS and the PLAN disagree and the PLAN is the stale one. (b) 🔴 **AC-9 is not merely "design-blocked" — its Step 7 probe is UNRUNNABLE AS WRITTEN, SURFACED to Cray:** it names `services/engine/demo_events.py:62` as the `below` comparison to invert, but that line **delegates** — the comparison lives at `services/engine/recommender.py:77-79`; and `tests/services/engine/eval/test_eval_harness.py` loads traces as static JSON with **zero** references to `demo_events` or `crosses_threshold`, so the mutation is unobservable there **by construction**. Executing it as written would manufacture an ADR-0038 **class-C1** guard inside the PLAN that exists to eliminate class-C1 guards. (c) **AC-10's scope is off by one** — it says *"nl-01…nl-12"*, but nl-12 is the set's only `ceiling: true` case, so the real remainder is **nl-01…nl-11 (eleven)**.]_ **Read the PLAN, never a restatement:** `docs/plans/0107-oracle-coverage-hardening.md` (§Phase A closing evidence · §Acceptance Criteria).

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
