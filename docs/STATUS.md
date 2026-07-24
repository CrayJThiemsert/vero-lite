---
last_updated: 2026-07-24T18:05:00+07:00
session: 170
current_batch: "s170 CLOSED — PLAN-0088 Step 4 BUILT (#895, AC-7); the owed s169 reconcile (#894, first NET SHRINK −596 B); then SD-9 surfaced (#897) + RULED (a2) by Cray (#898) — Step 4.5 created, Step 5 un-gated. 0 open."
current_actor: code
blocked_on: "Nothing. main=46f0ba1; suite FRESH 3159/7 re-run on 7150c07 (the last code-changing commit; #897/#898 are docs-only); ruff + mypy --strict (109 files) clean; MS-S1 COLD; 0 open PRs."
next_action: "PLAN-0088 Step 4.5 — the SD-9 (a2) substrate extension in `run_analytics.py`: a filterable run rollup (procedure x status), per-run `duration_ms_total` via grouped output only, a week bucket. Then Step 5 (AC-9b is host-state)."
head_commit: 46f0ba1
recent_commits: [46f0ba1, a46bec4, 776afee, 27f5af0, 7150c07, 501b169, a0d2939, 9e26195, 0d11da4, 8393af8]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 170, 2026-07-24 (head_commit `9e26195` → `7150c07`) — the session a
> MUTATION PROBE caught an oracle that could not fail. PLAN-0088 Step 4 shipped
> reader A4 at `GET /insights/audit-readiness` (#895), and deleting the approver
> `FILTER` from `gate_counts` reddened **only** the SQL-shape assertion — **both
> exact-value oracles stayed GREEN**. Two PRs (#894 the owed s169 reconcile, #895
> the build), both merged, 0 open at close.**
> **(the headline — the corpus, not the assertions, was the defect.)** The
> factory's `approve` branch set `status=RESOLVED` and appended the
> `gate_principal_recorded` trace **together**, so every resolved gate carried an
> approver, `gate_approvers` equalled `gates` identically, and extraction was
> indistinguishable from counting. The `sum(...) > 0` guard only ruled out
> all-zeros. **Without the SQL-shape test, AC-7 would have been untested while
> looking green.** Fixed in the second commit (`501b169`): `_gate_approver(i)`
> returns `None` for `i % 15 == 6`. Both properties of that residue are
> deliberate — it is a **proper subset** of the resolved set (`6 % 3 == 0`), so
> those runs really are resolved gates, and its `i mod 4` varies (6, 21, 36, 51 →
> 2, 1, 0, 3) so the gap lands on **every** procedure rather than pooling on one
> (procedure is assigned by `i % 4`). That is the Step-3 intersection lesson
> applied. Returning `None` also exercises the JSONB sharp edge the substrate
> documents: it lands as the JSON scalar `null`, so `->>'principal_id'` yields SQL
> `NULL` — exactly what the `IS NOT NULL` test must exclude — while the Python
> oracle reaches the same answer by a different route. The assertions now pin the
> **gap** (`gate_approvers != gates`; every procedure shows `approver_recorded <
> resolved_count`), and **re-probed, the same mutation now reddens THREE oracles
> instead of one**. Both probes restored from a `/tmp` copy verified
> byte-identical with `cmp -s`, never `git checkout`.
> **(#895 — Step 4: AC-7.)** `GET /insights/audit-readiness` — reader A4, zero
> LLM: run totals by status, resolved-gate counts **with the approver half**,
> refusal counts by kind, and the chain verdict via the shipped `verify_chain`
> seam. Three substrate reads plus that seam — the reader adds no SQL of its own
> (L3) and holds no write primitive (AC-11). Three design calls worth recording:
> (1) **the approver comes from the TRACE, not `step_principals`** — `gate_counts`
> gains `approver_recorded`, read from the `gate_principal_recorded` entry that
> `resolve_gated_step` writes into the step `reasoning_trace`; AC-2's wording
> remains a known error (flagged for Cray, not self-edited), and the field NAMES
> its source explicitly so the confusion cannot return quietly. (2) **`EXISTS`,
> not a join** — a joined lateral yields one row per trace entry, multiplying the
> step row and **inflating `resolved_count`** silently, since the inflated figure
> still looks plausible; `EXISTS` asks the same question without changing the row
> count, so the statement stays O(groups) and AC-1's statement-capture fixture
> keeps holding. (3) **split visibility is STRUCTURAL** — `verify_chain` returns
> verbatim break strings, they are reduced to a boolean in the handler and never
> leave it, and `AuditReadinessReport` has no field that could carry them (plus
> `extra="forbid"`): disclosure is *unrepresentable*, not merely absent — the
> technique `ImpactReport` uses for the cross-currency total (S7). Strictly
> narrower than `GET /audit/verify`, which already gives every caller `intact` and
> the detail only to a credentialed one (SD-2(d)), so A4 widens nothing and needs
> no auth dependency.
> **(#894 — the owed s169 reconcile, and the first prune that NETTED NEGATIVE.)**
> STATUS was one PR behind: the s169 reconcile (#892) landed BEFORE Step 3 merged
> (#893). `head_commit` was set to `9e26195`, Step 3 recorded, the stale
> `next_action` retired. The `status-scribe` draft came back at **58,005 B — an
> INCREASE of 148 B** over the pre-session 57,857 — and its own estimate (≈57,690)
> was wrong; **measuring caught it**. An R2 pass then found **all ten**
> Recent-Decisions rows over the ~600-char pointer budget, and four more were
> compressed, landing at **57,261 B (−596 net)** — the first net shrink in three
> sessions, against s168's standing "prune harder" ask. Also corrected **four
> stale path citations** (`superseded by new info`): three RD rows and the
> In-Flight autonomy-fork entry cited `docs/plans/0091-*.md` / `0092-*.md`, but
> both PLANs were archived to `docs/plans/done/` at s168.
> **(evidence.)** Suite **3150 → 3159 passed / 7 skipped**, re-run in full on the
> merge commit `7150c07` (CI is PR-only, so merge commits are otherwise never
> tested). ruff + ruff-format clean; `mypy --strict services/` clean (109 files).
> **MS-S1 never contacted.**
> **(process — L1 fired again, and the reset was blocked again.)** The guard
> denied the 6th edit to `tests/support/run_corpus_factory.py` mid-build, and
> `git commit` — the documented reset — was blocked because `ruff` was red
> (`C901`, `_expected` at complexity 11) on that very file: the same shape as
> s169. Extracting only the predicate did not help — the `if` stayed behind — so
> the whole tally had to move into a `_tally_gate` helper (the `_tally_dwell`
> pattern). **Cray adjudicated by typed selection and authorised the shell
> escape**, applied via a guarded patch script that aborts unless both anchors
> match exactly. The later corpus fix needed no escape — the first commit had
> reset the counter.
> **(after the close — SD-9 surfaced (#897), RULED (a2) (#898).)** Step 5 could
> not be built as specified: S5's declared A1 properties are unservable by the
> shipped substrate. Two findings resize it beyond a wording bug — **no primitive
> accepts a parameter at all** (an NL reader that cannot filter is the fixed
> reports with an LLM in front) and **AC-10's B1–B4 are equally unserved**, so
> Step 6 hits the same wall: the "substrate is complete, readers add no SQL"
> premise Steps 2–4 ran on **was never true**, just not load-bearing until now.
> S5 is ratified as SD-5, so this was a decision, not an edit — **S5's body
> stayed byte-unchanged** while `plan-drafter` surfaced SD-9 with costed options
> (and **refuted the dispatch's own fact-pack**: Code wrongly claimed Steps 1–3
> were already annotated BUILT). Cray ruled **(a2)** — extend the substrate in
> `run_analytics.py` only; eliminate `agent_id` + `trigger` from v1 as
> unmeasurable (constant in the AC-2 factory, and `trigger` undefined). **Step
> 4.5** created; Step 5 un-gated. **Precedent, so Step 6 does not re-litigate it:
> the invariant is S1 + AC-11 — SQL lives in `run_analytics.py`, readers and the
> compiler own none — not a frozen primitive inventory.** Full reasoning is
> §SD-9 in the PLAN; do not restate it here.

> **Session 169, 2026-07-24 (head_commit `c2b92c5` → `9e26195`) — the session that
> made PLAN-0088 ratified and then REAL. The re-draft SURFACED a four-item
> jointly-unsatisfiable knot (#888); Cray cut it in ONE typed pass — **SD-8 = (a)
> ELIMINATE** (#889); Steps 1–3 then shipped the cross-run read substrate, the
> ฿ ROI rollup, and the flow report (#890, #891, #893). Six PRs (incl. the #892
> reconcile), all merged, 0 open at close.**
> **(the open.)** `next-work-analyst` — 9 candidates, 3 Explore agents grounding
> each against code — picked the PLAN-0088 **RE-DRAFT**, not the build; every other
> candidate is DEFERRED-NO-PRESSURE or DO-NOT-BUILD (PLAN-0076 T1 unchanged), and
> scaffolder-v2's extend shapes are **greenfield**, not an extension (see In-Flight).
> **(#888 — the re-draft SURFACED; it deliberately did not resolve.)** PLAN-0088
> read execution-ready (14 ACs / 6 Steps), but its whole design layer was
> drafter-resolved and UNRATIFIED with no adjudication surface. `plan-drafter` added
> the PLAN-0091-pattern SD-1…SD-8 block + a Step 0 and named the load-bearing
> finding: four items were **jointly unsatisfiable** — AC-1 placing "paginated
> listing" in the substrate, AC-12's newest-first `list_runs_page`, AC-3's tripwire
> failing any `ORDER BY` on a raw wall-clock column inside `run_analytics.py`, and
> S4 refusing the monotonic-sequence fix. Newest-first paging needs that `ORDER BY`
> in the guarded module; dropping it makes offset pagination nondeterministic;
> ordering it correctly needs the key S4 defers. **Second defect:** AC-12 named
> `view-monitor.js` as the only `/runs` consumer — a census finds two, and the
> omitted one depends HARDER: `view-map.js` fetches `/runs` bare and **truncates**
> via a `CAP = 5` slice under a stated newest-first assumption, so an order change
> HIDES the newest runs rather than shuffling them; classified **`was an error`**
> (PLAN-0084 shipped that dependence one day before the draft). Third: the
> design-decisions header read "S1–S6" while seven exist.
> **(#889 — Cray ratified SD-1…SD-8 in ONE typed pass.)** SD-1…SD-7 as written;
> **SD-8 = (a) ELIMINATE** — `list_runs_page` and AC-12 STRUCK, the substrate ships
> aggregate primitives only, `GET /runs` untouched, listing pagination sequenced
> into the future monotonic-sequence-column PLAN. This is the first real-case
> reading of that deferral's un-defer trigger (in
> `tests/services/db/test_load_run_ordering_guard.py`) and it **declines to fire
> it** — the aggregate readers are order-insensitive. AC-12 is kept as a
> **tombstone** so AC-1…AC-13 numbering stays stable; live AC count is now 13.
> Step 0 DISCHARGED → PLAN build-ready (Status stays `Draft`).
> **(#890 — Step 1: AC-1 / AC-2 / AC-3 / AC-11.)** `services/db/run_analytics.py`:
> seven read-only async primitives, each **passed** an `AsyncSession` (the caller
> owns the transaction, mirroring `audit_log.py`). `tests/support/run_corpus_factory.py`:
> a deterministic seeded-RNG corpus — 250 runs × 6 spine steps = 1,500 step rows —
> whose expected aggregates are computed from the SAME seeded specs in plain Python,
> an oracle independent of the SQL under test. Two AST guards mirroring the
> ordering-guard doctrine, each carrying its own guard-fires-on-what-it-forbids test.
> **(#891 — Step 2: AC-4 / AC-5.)** `GET /insights/impact` + a deterministic no-LLM
> narrative. AC-4's grouping is finer than Step 1 shipped (currency × procedure ×
> facet kind × day) and L3 forbids readers writing SQL, so `benefit_rollup` was
> **extended**, not duplicated; the new `benefit_assumptions` returns the DISTINCT
> union of disclosed assumptions, because ADR-0030 D3 means an aggregate must
> disclose no less than its parts. `ImpactReport` carries **no cross-currency total
> field and must never gain one** — the wrong sum is unrepresentable, not merely
> discouraged (S7).
> **(two findings that generalise.)** (1) SQLAlchemy stores a Python `None` in a
> JSONB column as the JSON scalar `null`, **not** SQL `NULL`, so `IS NOT NULL` does
> not exclude it and `jsonb_array_elements` raises "cannot extract elements from a
> scalar" — and a LATERAL is evaluated per row BEFORE the `WHERE`, so no `WHERE`
> can protect a set-returning function; guard the input with `jsonb_typeof(...) =
> 'array'`. (2) A grep-style vocabulary guard whose target quotes the phrases it
> forbids **matches its own documentation** — the ADR-0032 D5 phrases now live only
> in the test, and the router cites the ADR by section.
> **(#893 — Step 3: AC-6.)** `GET /insights/flow` — reader A3, the flow report,
> zero LLM: `waiting_dwell_stats` in `services/db/run_analytics.py`, the report
> models in `services/api/models/insights.py`, the `/flow` handler in
> `services/api/routers/insights.py`. Per-procedure × per-step `duration_ms`
> stats (count/avg/max) via the shipped `duration_stats`; `waiting_human` dwell
> from SAME-ROW spans clamped via `GREATEST(span, 0)`, a surfaced
> `negative_clock_spans` counter, no cross-row wall-clock arithmetic (the AC-3
> AST guard's scope covers it). **Semantic caveat, flagged for Cray and
> deliberately NOT self-resolved:** AC-6 calls the same-row span "dwell", but for
> a run whose last write was its suspension it measures **start → suspension**,
> not elapsed-since-suspension — an AC-wording imprecision, not a code defect,
> stated plainly in BOTH `services/db/run_analytics.py:177-186` and
> `services/api/models/insights.py:93-102`; elapsed-since would need `now()`,
> neither test-reproducible nor trustworthy on this box's clock. Two findings
> that generalise: (1) a seeded subset must INTERSECT the scope under test —
> the backward-clock rows had to land on `waiting_human` (`i % 25 == 6` keeps
> the `i % 5 == 1` residue), else `negative_clock_spans` reads 0 and the test
> only LOOKS tested; (2) record WHICH oracle a mutation probe proved decisive —
> deleting the `GREATEST` clamp reddened the exact-value corpus comparison but
> left the purpose-written `>= 0` assertion GREEN; the test docstring now names
> which assertion is the guard and which the sanity floor.
> **(evidence.)** Suite **3109 → 3150**, per-PR deltas **+17 / +17 / +7** summing
> exactly, re-run on the final merge commit `9e26195` (CI is PR-only, so merge
> commits are otherwise never tested). Both build gates SHA-verified against the
> PR head before merge; `mypy --strict services/` clean (109 files); ruff +
> ruff-format clean.
> **Non-vacuity probed TWICE** (`/tmp` restore + `cmp -s` byte-identical): AC-1's
> statement-capture oracle and AC-5's narrative oracle each reddened ONLY their own
> test. The ฿ facet is additionally pinned through the REAL persistence path — a
> procedure emitting an `EconomicImpact` is run, `persist_run`-ed, and read back
> asserting the exact `Decimal` survives `Decimal → JSON string → JSONB → numeric
> cast → Decimal`. **MS-S1 never contacted.**
> **(process — a genuine L1 deadlock.)** L1 loop-detect fired on `run_analytics.py`
> at 6 edits, and all three documented exits were shut: a subagent inherits the
> exhausted counter, the turn boundary did not reset it (matching s168), and
> `git commit` — the documented reset — was itself blocked because `ruff` failed
> `F821` on the very file the guard gated, with `--no-verify` forbidden (§8). Cray
> adjudicated the resume twice by typed AskUserQuestion; the edit landed through the
> shell escape the Tier-0 memory names for this deadlock.

> **Session 168, 2026-07-23 (head_commit `7c86752` → `c2b92c5`) — the session that
> made the scaffolder REAL. PLAN-0091 closed at 10/10 and ARCHIVED; six PRs merged
> (#881–#886), 0 open. The headline is not "two partial ACs finished" — it is what
> finishing them exposed: the tool PLAN-0091 shipped in s167 emitted a package that
> could not load, and the command an operator would type wrote nothing at all. Every
> oracle was green throughout.**
> **(the open — a grounded re-rank, not a menu.)** The session began with
> `next-work-analyst`: 9 candidates from three sources, 4 Explore agents grounding
> each against code. It killed two readings before any build. **PLAN-0088 is not
> design-ready** despite 14 ACs + 6 Steps — S1–S7 are drafter-resolved and
> UNRATIFIED, 8/14 ACs need rewriting, and the AC-3 ⊗ AC-12 trilemma was
> re-verified independently (plus a defect the PLAN does not know: AC-12 undercounts
> `/runs` consumers — `view-map.js` also depends on newest-first). **The ungated work
> there is the RE-DRAFT, not the build.** **PLAN-0076 T1 stays counter-indicated**
> (trigger unfired; the PLAN itself calls building now "abstraction ahead of
> pressure", which ADR-0031 D4.1 forbids) and **T2 closed at s143**.
> **(the two defects that made this session worth more than its AC list.)** Both were
> invisible to a green suite, and both were found by RUNNING the thing rather than
> reading it. **(1) The emitted package could not load** — `wire.py` registered
> `verticals.<ns>.procedures_factory`, a module `emit_package` never wrote, and the
> emitted adapter called `registry.register_adapter` with TWO args against a
> one-arg signature, so a scaffolded vertical raised `TypeError` on import. The
> package tests only `ast.parse` the emitted text, and a syntactically perfect call to
> a wrong signature parses fine. **(2) `vero-lite scaffold` could not scaffold** —
> `cli.py` still exited 3 with "Emission is not wired yet (PLAN-0091 Steps 2-4)" while
> Steps 2–4 had shipped in #874–#876. The golden e2e calls the emitters DIRECTLY, and
> AC-1 only claims `--help` + `--plan-only`; no test pinned the exit-3 behaviour either
> way. **The generalisable lesson: a suite addressed at the library cannot see that the
> entry point is dead. The AC set was satisfiable without the tool being usable.**
> **(what Cray ratified, typed.)** BUILD all four remainders including AC-7(a) — via
> **operator-typed intake slots**, not narrative mining, which would put the model back
> on the value path and trip SD-1's promotion tripwire. Plus the three XS items
> (PLAN-0092 closeout, the `AT2_ONLY_KINDS` drift, SD-D) and — mid-session, on the
> evidence above — **wire the CLI now**.
> **(honesty corrections, recorded not absorbed.)** s167's "8/10" was really **7/10**:
> **AC-4 was ticked while its own text required a `procedures_factory.py` that did not
> exist** — classified `was an error`, not `superseded`, since the AC text never
> changed. **AC-10's gap was wider and different in kind** than recorded: adding
> `main.py` to the targets dict would have been a NO-OP, because the shipped pattern
> counts PER-MEMBER (`<vertical> ships <n>`) and scores zero on the COLLECTION count
> ("All six PROCEDURE-SHIPPING verticals"); the same blind spot hid a third site inside
> the file already being disposed. **AC-7(c) ships as STRUCTURAL equality, not literal
> bytes** — a correction, not a weakening: the donor's docstring records it was
> "Hand-written … NOT `vero-lite new-vertical`", so a tool emitting those bytes would
> emit a **false provenance claim about its own output**.
> **(one gap left open ON PURPOSE, and asserted as such.)** The census comment carries
> four interlocking counts in one free-form narrative, each encoding which PLAN
> contributed which procedure. `residual_counted_prose` REPORTS it rather than
> rewriting it — deleting a shipped file's provenance to satisfy a tally rule is a
> worse outcome than the stale tally, and it is the same stance the tool takes at a
> governance tripwire: detect, hand a human the specifics, never clear it yourself.
> **(evidence discipline.)** Suite **3083 → 3109**, and the per-PR deltas
> (+0/+1/+18/+2/+3/+2) summed to the merge-commit total EXACTLY — predicted before the
> run, matched after it. Non-vacuity probed **six times**, each restored from `/tmp` and
> verified `cmp -s` byte-identical (never `git checkout`, which wipes the edit under
> test). The two that mattered reproduced defects that had actually shipped. The final
> proof was not a test but an import: `registrar OK -> LiveFleetSyntheticAdapter`,
> `fetch_objects('Truck')` returning rows keyed with `plate` and WITHOUT `name`,
> `health_check` → ok. **MS-S1 never contacted.**
> **(process, recorded because it cost real time.)** `index.lock` contention hit
> repeatedly when `checkout && merge && push` ran as one compound command — the
> checkout failed while merge and push **continued and reported success**
> ("up-to-date", "Everything up-to-date") on work that never happened. One merge even
> printed "Automatic merge failed" and left a state with zero conflicted files and an
> empty staged diff. Diagnosed (no stray git process, no stale lock, no `core.worktree`
> hijack), aborted rather than committed, and redone one command at a time with
> `git branch --show-current` / `git merge-base --is-ancestor` as the verification.
> **`$?` inside `wsl bash -lc` reports 0 through a failed git op** — read a predicate,
> never the printed message. L1 loop-detect also fired once on `cli.py` (6 edits); the
> guard was respected, the counter reset via commit, not bypassed.

> **Session 167, 2026-07-23 (head_commit `9e19905` → `7c86752`) — the session
> that CLOSED the autonomy fork: open since s71, 14 recorded misfires across 5
> sessions, RESOLVED and SHIPPED in one session. Cray typed-ratified **option
> A′** — the Stop-hook classifier's `dispatch` verdict is DEMOTED from an
> ORDER to a SUGGESTION. Two PRs: #870 filed PLAN-0092, #871 built it.**
> **(the behavior now on `main`.)** On `decision == "dispatch"` the hook emits
> **no stdout directive**: the stop fires with pause semantics (the stop-chain
> **RESETS**, no longer increments) and the classifier's routing — subagent,
> artifact_kind, task_summary, matched D-rows, reason — goes to Cray as one
> Telegram ping (`stop_dispatch_suggestion`). Malformed dispatch metadata stays
> **silent**: no directive, no ping.
> **(the evidence that drove it.)** 14 recorded misfires against **0 recorded
> valid dispatch-arm fires** across ~2 months live — the caveat recorded
> honestly in the PLAN: an unrecorded valid fire cannot be fully ruled out. The
> four shapes span **two failure families** — **knowledge** (shapes 1/4 and part
> of 2: the classifier can see neither disk state nor in-flight work, so **no
> model upgrade fixes them**) and **judgment** (shape 3, mention-as-intent: a
> prompt-rule-per-shape race that PLAN-0034's rule already lost in four
> consecutive sessions). A′ moots **both families at the arm** — the first
> structural fix rather than a fifth shape-chasing patch.
> **(rejected alternatives, recorded IN the PLAN so they are not re-proposed.)**
> (a) another prompt rule — refuted empirically; (b) deterministic
> disconfirmers on a still-ordering arm — kills shapes 1/2/4 only, the judgment
> race survives; (e) the Sonnet backend flip — judgment family only, and it
> carries a known API-key/org fail-closed mode needing a probe, so the A′ pick
> **defers** it.
> **(scope locks honored in the build.)** `_sonnet_classifier.py` is
> **byte-unchanged** and still returns `dispatch` — only the hook's
> interpretation changed. The V1 goal-gate arm (`_goal_gate.py`, ADR-0018) and
> the PreToolUse arm (`pretooluse_classifier_dispatch.py`) are untouched. D1/D2
> registry rows are **annotated, never deleted** — they still document when a
> suggestion fires. **No ADR amendment**: the arm's order-emitting behavior had
> **zero ADR backing** (grep-verified), so **PLAN-0092 IS the governance
> record**. It stays `Status: Draft` — the ACs are closed by the build, but no
> closeout PR was filed this session.
> **(SD-A…SD-D — all Cray-ratified as-recommended, typed.)** SD-A a new compact
> `stop_dispatch_suggestion` Telegram shape via a formatter branch, not the
> cap-hit `depth=/cap=` shape · SD-B **DELETE** `_build_dispatch_instruction` +
> `_PLAN_DRAFTER_BUDGET_REMINDER` rather than repurpose them (order-shaped text
> must not survive into a suggestion channel) · SD-C **no** env-var escape hatch
> (`git revert` is the rollback; a flag is a silent path around a typed
> ratification) · SD-D classifier-prompt wording alignment **PARKED** as a
> follow-up note.
> **(route + R2.)** `plan-drafter` drafted the PLAN (ADR-009 D1, the PLAN-0034
> precedent) → Code R2 → Code commits (D2). R2 verified the drafter's
> per-function test inventory **line-exact** against
> `tests/handoffs/test_stop_continuation.py` (100% accurate) and added one
> catch: `_goal_gate.py`'s ADR-0018 D6 comment cited
> `_PLAN_DRAFTER_BUDGET_REMINDER` as its in-module-template precedent — a
> **textual reference, not a caller**, so the drafter's caller-grep was right —
> re-worded to cite it historically (docs-only; V1 behavior + tests untouched).
> **(the build ran test-first.)** The four rewritten dispatch tests were run
> **RED against the unmodified hook** before the Step 2 edit — AC-4 non-vacuity
> evidence, recorded in the #871 PR body. Honest caveat also recorded: the new
> malformed-no-ping guard passes both before and after (a forward regression
> guard on a negative property), so it is **NOT** counted as AC-4 evidence.
> **(process — two recorded events.)** **L1 loop-detect fired mid-build** (6
> code-path edits to one test file in a turn). Not thrash — six distinct
> planned edits, all successful; Code respected the guard, switched off the Edit
> tool for the final one-character lint fix, then committed (a documented L1
> reset). The same moment surfaced that the session was still on `main` after
> the sync — the build branch was created before any commit, so **nothing
> landed on `main` directly**. **The merges:** Cray twice stated both PRs were
> merged; Code verified on disk both times and found them still OPEN
> (`mergedAt: null`, `main` unmoved, no merge event in either timeline, nothing
> blocking — gate green, 0 required reviews). Code did **not** merge on the
> strength of the mistaken statement; it surfaced the discrepancy with evidence
> and asked, **Cray then typed an explicit authorization** (AskUserQuestion),
> executed in order #870 → #871.
> **(verification / state.)** `gate` PASS on both PRs, each SHA-verified —
> 2m59s on `2646456` (#870); 3m3s for #871 against **the re-synced head
> `6afaf9c`**, not the pre-sync `0870266` (`main` was merged INTO the branch
> after #870 landed; never force-pushed). Suite **2994 passed / 7 skipped** run
> twice — on the build branch and again **on the merge commit `7c86752`**
> (175.24s); against the 2995/7 prior the delta is exactly **−1** (two tests
> deleted, one added) ⇒ expected, not a regression. 7 skips = dev Postgres
> connected. Offline gate green at CI scope (`ruff check .` + `ruff format
> --check .` + `mypy --strict services/`); one clause of honesty — `ruff check
> .` also flags `.claude/benchmark-results/analyze_dump.py` (S108), an
> **untracked** file from another workstream that CI never sees and of which
> nothing is committed. **MS-S1 COLD, zero calls all session.** 0 open PRs at
> close; working tree clean but for the 2 standing KEEP untracked paths
> (`.claude/benchmark-results/`, `.claude/launch.json`).


> _Older content rotates out of this file per the **STATUS.md Rotation Policy (R1-R7)** in [`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md) (Lesson #23): Current Focus keeps the 4 newest sessions (<=8 blocks); Recent Decisions keeps the last 10 rows. Rotated blocks/rows live in [`docs/status-archive/`](status-archive/) and git history (Tier 3). Layout — **two separate chains, both with letters ascending with time and the base holding the recent window**: the rotation archive `2026-h1b` → `c` → `d` → `e` → `f` → `2026-h1-status.md`, and the Current-Focus-only `2026-h1b` → `c` → `2026-h1-current-focus.md`. Rotations append to the two bases. **Grep the directory, not a filename** — the chain is one corpus and which file holds a given block is an artifact of where the ~192 KB R4 bar happened to fall. _[Chain created 2026-07-17 (s144): the single `2026-h1-status.md` had reached 592,577 B, 2.3x R4's cap, and the new guard (#789) forced the split.]_

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
| 2026-07-24 | **s170 — PLAN-0088 Step 4 BUILT (#895): reader A4, audit-readiness at `GET /insights/audit-readiness` (AC-7) — status/gate/refusal counts + the public chain verdict via the shipped `verify_chain` seam; no SQL of its own (L3), zero LLM, split visibility STRUCTURAL (`extra="forbid"`, no field could carry a break string). Headline: a MUTATION PROBE caught an oracle that could not fail — deleting the approver `FILTER` reddened ONLY the SQL-shape assertion, both exact-value oracles stayed GREEN, because the CORPUS (every resolved gate carried an approver), not the assertions, was the defect. Corpus gap `i % 15 == 6` fixed it → the same mutation now reddens THREE oracles. Suite 3150 → **3159**. Then, after the close, **SD-9 surfaced (#897) and RULED (a2) by Cray (#898)**: S5's declared A1 properties are unservable by the shipped substrate, **no primitive accepts a parameter at all**, and AC-10's B1–B4 are equally unserved — so the "substrate is complete" premise Steps 2–4 ran on was never true. Ruling extends the substrate in `run_analytics.py` **only** and eliminates `agent_id` + `trigger` from v1; **Step 4.5** created, Step 5 un-gated. Precedent: the invariant is **S1 + AC-11**, not a frozen primitive inventory. Full narrative: the Session-170 CF block above | `46f0ba1` (#898 merge, head_commit of record) / `a46bec4` (the ruling) / `776afee` + `27f5af0` (#897, SD-9 surfaced) / `7150c07` (#895 merge) / `a0d2939` + `501b169` (Step-4 build) / `09b90bc` + `06b54cb` (#894, the owed s169 reconcile, −596 B net) / `docs/plans/0088-cross-run-read-substrate-and-run-insight-readers.md` §SD-9 + `services/db/run_analytics.py` |
| 2026-07-24 | **s169 — PLAN-0088's design layer ADJUDICATED: the re-draft (#888) surfaced a four-item JOINTLY-UNSATISFIABLE knot; Cray ratified SD-1…SD-8 in ONE typed pass (#889) — SD-8 = (a) ELIMINATE.** `list_runs_page` + AC-12 STRUCK: the substrate ships aggregate primitives only, `GET /runs` untouched, listing pagination sequenced into the future monotonic-`sequence`-column PLAN. First real-case reading of that deferral's un-defer trigger — and it **DECLINES to fire it** (the aggregate readers are order-insensitive). AC-12 kept as a **tombstone** so AC-1…AC-13 numbering stays stable (live count 13). Second correction, `was an error`: AC-12 undercounted `/runs` consumers — `view-map.js` fetches `/runs` bare and TRUNCATES via a `CAP = 5` slice under a newest-first assumption, so an order change HIDES the newest runs. Step 0 DISCHARGED → build-ready (Status stays `Draft`). Full narrative: the Session-169 CF block above | `dd16267` (#889 merge) / `4ef7b5d` (the rulings) / `8d1be34` (#888 merge) / `3a16238` (the re-draft) / `docs/plans/0088-cross-run-read-substrate-and-run-insight-readers.md` §Surfaced decisions |
| 2026-07-24 | **s169 — PLAN-0088 Steps 1–3 BUILT (#890, #891, #893): the cross-run read substrate (AC-1/2/3/11) + reader A2, the ฿ ROI rollup at `GET /insights/impact` (AC-4/5) + reader A3, the flow report at `GET /insights/flow` (AC-6).** Seven read-only async primitives (caller-owned `AsyncSession`, mirroring `audit_log.py`); a seeded 250-run × 6-step corpus with a plain-Python oracle independent of the SQL under test; two AST guards with guard-fires-on-what-it-forbids tests. Step 2 **EXTENDED** `benefit_rollup` (L3: readers write no SQL); `ImpactReport` has **no cross-currency total field and must never gain one** (S7). Step 3 added `waiting_dwell_stats`: SAME-ROW `waiting_human` dwell clamped via `GREATEST(span, 0)` + a surfaced `negative_clock_spans` counter, zero LLM — plus the AC-6 "dwell" caveat (start → suspension; flagged for Cray, see In-Flight). Suite 3109 → **3150** (+17/+17/+7), re-run on the merge commit; non-vacuity probed (`/tmp` restore + `cmp -s`); MS-S1 never contacted. Full narrative: the Session-169 CF block above | `9e26195` (#893 merge, head_commit of record) / `0d11da4` (#893 build) / `8393af8` (#891 merge) / `0be589e` (#891 build) / `b1e12d1` (#890 merge) / `c209bd9` + `2fba64b` (#890 builds) / `services/db/run_analytics.py` + `services/api/models/insights.py` + `services/api/routers/insights.py` + `tests/support/run_corpus_factory.py` |
| 2026-07-23 | **s168 — PLAN-0091 COMPLETE 10/10 + ARCHIVED (#883–#885): closing it exposed that the emitted package could not LOAD and `vero-lite scaffold` wrote NOTHING — both invisible to a green suite (a suite addressed at the library cannot see a dead entry point). Suite 3083 → 3109; honesty correction: s167's "8/10" was 7/10.** Full narrative: the archived PLAN | `c2b92c5` (#886 merge, head_commit of record) / `5865d19` (#885 AC-10) / `4994801` (#884 CLI wiring) / `844eb6d` (#883 AC-7 a/b/c) / `c47232f` (#882) / `b8f011d` (#881) / `docs/plans/done/0091-narrative-to-vertical-scaffolder-tool.md` (COMPLETE, 10/10) + `services/engine/scaffolder/**` + `services/engine/cli.py` |
| 2026-07-23 | **s168 — PLAN-0092 closed 6/6 + archived (#881); the `AT2_ONLY_KINDS` drift fixed with an anti-drift tripwire (#882); SD-D settled — the classifier prompt reworded to a ROUTING SUGGESTION, decision value + reply schema pinned UNCHANGED (#886).** Full narrative: the archived PLAN | `c2b92c5` (#886 merge) / `c47232f` (#882 merge) / `b8f011d` (#881 merge) / `.claude/hooks/_sonnet_classifier.py` + `tests/handoffs/test_sonnet_classifier.py` + `tests/services/engine/procedures/test_archetype_templates.py` + `docs/plans/done/0092-stop-hook-dispatch-arm-demotion-to-suggestion.md` (COMPLETE, 6/6) |
| 2026-07-23 | **s167 — the autonomy fork RESOLVED + SHIPPED in one session: option A′ (Cray, typed) DEMOTES the Stop-hook `dispatch` verdict from an ORDER to a SUGGESTION (#870 filed, #871 built).** No directive on `dispatch`: pause semantics + stop-chain RESET, routing sent as one `stop_dispatch_suggestion` ping. `_sonnet_classifier.py` byte-unchanged; V1 goal-gate + PreToolUse arms untouched. No ADR amendment — the arm had zero ADR backing, so the PLAN IS the governance record. Ledger: 14 misfires / 0 valid fires. **The argument is settled history in the archived PLAN — do not restate it here** | `7c86752` (#871 merge, head_commit of record) / `0870266` + re-sync `6afaf9c` (build) / `822a7e8` (#870) / `.claude/hooks/stop_continuation.py` + `tests/handoffs/test_stop_continuation.py` + `docs/plans/done/0092-stop-hook-dispatch-arm-demotion-to-suggestion.md` _[path fixed s170: archived to `done/` at s168]_ |
| 2026-07-23 | **s166 — PLAN-0091 SD-5 RATIFIED (a), Cray typed (#869): the AT-2 template is owned by `services/engine/scaffolder/` and NEVER enters the shared `REGISTRY`** — Step 4's design promise true by construction; the classify path stays byte-unchanged and ADR-0024 D7's abstain routing stays literally true. All five SDs closed. Tripwire: `test_archetype_templates.py:37` (`set(REGISTRY) == set(AT1_FAMILY)`) must never need editing — if it does, STOP and re-open SD-5 rather than registering centrally | `097d180` (#869 merge) / `9eb7c90` + `1413383` / `docs/plans/done/0091-narrative-to-vertical-scaffolder-tool.md` §SD-5 + `tests/services/engine/procedures/test_archetype_templates.py:37` _[path fixed s170]_ |
| 2026-07-23 | **s166 — dispatch-quality discipline shipped (#866, docs-only): the `code-operational-policy` skill gains the 3 dispatch blocks (Frontier/anti-anchoring · oracle-scoped accelerator · REJECT-if) + the M1–M4 follow-up vocabulary + the pre-close counterexample step; Lesson #0032 files the why.** Deliberately NOT built: any hook/detector for M3/M4 (judgment-shaped) — adoption is Rule-of-Three on recorded catches | `b8566a6` (#866 merge, head_commit of record) / `0a1cbe4` + `9200552` / `.claude/skills/code-operational-policy/SKILL.md` + `docs/lessons/0032-ambition-scales-with-oracle-exploration-gated-not-planned.md` |
| 2026-07-22 | **s164 — PLAN-0091 filed Draft (#859): the narrative→vertical scaffolder (`vero-lite scaffold`), 10 ACs / 8 Steps, create-shape only — BUILD-BLOCKED until Cray adjudicated Step 0.** A 4-agent Explore fan-out REFUTED two claims: the scaffolder is **brownfield-with-a-ratified-half** (ADR-0024 pins the generation contract; PLAN-0040 shipped narrative→procedure), and **PLAN-0088 had 12 defects, not 6** — its own **AC-3 ⊗ AC-12 trilemma** blocked it, not the pilot gate. Both since resolved (s168 / s169) | `f758509` (#859 merge, head_commit of record) / `74a49c2` / `docs/plans/done/0091-narrative-to-vertical-scaffolder-tool.md` _[path fixed s170]_ |
| 2026-07-22 | **s163 — PLAN-0090 filed (#855) → BUILT (#856) → COMPLETE 7/7 + archived (#857): `fleet_maintenance.scheduled_pm_service_round`, the AT-3 SCHEDULED calm path — 16m13s hands-on, steps BYTE-IDENTICAL to the manual path (PROVEN by a dumped-model test).** MS-6 BINDING: a LOWER BOUND, never summed with PLAN-0086's 27m39s or PLAN-0089's ~14 min. A DISTINCT `procedure_id`, never a trigger flip. + the L3 CLI fix: the unwired daemon CRASHED at startup (not "409s at resolve"); a set-equality tripwire now mirrors `main.py`. Gate on `a3ef955`: 2994/7. Full narrative: the Session-163 CF block above | `1ce3546` (#857 merge, head_commit of record) / `a3ef955` (#856 build) / `20f2585` (#855) / `2d34d80` (#854 reconcile + trim) / `docs/plans/done/0090-fleet-scheduled-calm-path.md` (COMPLETE, 7/7) |

## In-Flight Discussions

- **PLAN-0091 — COMPLETE 10/10 and ARCHIVED (s168).** Full record: `docs/plans/done/0091-narrative-to-vertical-scaffolder-tool.md`. **Two follow-ons it named, neither scheduled:** the **extend shapes** (calm-path + scheduled-variant scaffolding) are **greenfield, not an extension** — s169 re-confirmed the shipped emitters refuse an existing vertical *by construction* (`services/engine/cli.py` + the scaffolder's `wire.py`), and create-only is Cray-ratified SD-2, so this needs a fresh seam spec, not effort; and the census-narrative comment in `tests/api/test_procedures_endpoint.py` is the one counted site the disposer REPORTS rather than rewrites (`residual_counted_prose`) — a human call, left visible on purpose.
- **PLAN-0088 — RATIFIED and BUILDING: Steps 1–4 shipped (#890/#891/#893/#895); Steps 5–6 open.** SD-1…SD-8 are Cray-ratified (#889); **SD-8 = (a) ELIMINATE** struck `list_runs_page` + AC-12, so the substrate stays aggregate-only, `GET /runs` is untouched, and listing pagination moves to the future monotonic-`sequence`-column PLAN. Group A remains ungated by ADR-0032 D2 (proven by the AC-11 static guard, not prose); Group B stays pilot-gated (L2). **Step 4 SHIPPED (#895)** — reader A4 at `GET /insights/audit-readiness` (AC-7): `EXISTS`-shaped gate counts carrying the approver half, status + refusal counts, and the public chain verdict via the shipped `verify_chain` seam, read-only with split visibility structurally preserved. Remaining: **Step 5 (AC-8/9/9b — AC-9b is host-state: explicit Cray go required; and see (3) below, its scope is not yet settled)**, then Step 6 (AC-10/AC-13). **Four open questions, flagged for Cray and deliberately NOT self-edited.** (1) **AC-2's wording is wrong about where the gate approver lives.** AC-2 says the factory seeds "gate resolutions with `step_principals` approver halves", but every write to `run.step_principals` (`orchestrator.py`, `persistence.py`) writes the **REQUESTER** half; the approver is recorded by `resolve_gated_step` in three other places — the step `reasoning_trace` (`gate_principal_recorded.principal_id`), `StepResult.audit["governed_decision"].principal_id`, and the `audit_log` `gate_decision` row. The factory seeds it the way the engine actually records it, and Step 4's `approver_recorded` reads the TRACE and names that source explicitly so the confusion cannot return quietly. Steps 1–4 unaffected; it matters for **AC-10's B2**, which must join those three sources. Classified `was an error` in the AC wording. (2) **AC-6's "dwell"** is an AC-wording imprecision, not a code defect — the S4-sanctioned SAME-ROW span measures **start → suspension** for a run whose last write was its suspension, not elapsed-since-suspension; stated at `services/db/run_analytics.py:177-186` + `services/api/models/insights.py:93-102` (detail: the s169 CF block). (3) **NEW (s170) — S5 contradicts itself, so Step 5's scope is unsettled.** S5 says the A1 executor "adds no SQL of its own", but the numeric properties S5 itself declares — `duration_ms_total` (per **run**) and `started_week` — have **no shipped primitive**: `duration_stats` is per-**step** and `period_rollup` is per-**day**. Step 5 therefore needs 1–2 NEW substrate primitives, contrary to the "substrate is done, readers add no SQL" framing Steps 2–4 have been operating under. Cray's call: amend S5's wording · add a Step 1.5 · or narrow A1's declared properties. (4) **NEW (s170) — Step 6 needs the Step-1 corpus factory REOPENED.** B2 (per-tier approval outcome) cannot be written against what is seeded: the factory has **never seeded a reject**, hardcodes a single tier `"t1"`, and gives every run an identical `trigger_context` (so B4 has no trigger diversity to measure); refusals are keyed by kind only, not kind × procedure (B3). B2 also needs the hardest query in the PLAN — two-to-three correlated JSONB laterals on the same `StepResult` row, where the current hardest (`benefit_rollup`) joins one.
- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13; guarded trial (parallel to ADR-012) — verdict **continue-with-adjustments**. Run 1 (energy, s93) + Run 2 (supply-chain, s94) both COMPLETE, S-checks all PASS against pre-committed oracles, no R-PS trigger fired; C-1..C-3 CONFIRMED → **no open partner-sim debt**. ADR-011 audit stays gated on a REAL partner conversation (R3: SYNTHETIC provenance INFORMS but never TRIGGERS it). Full record: `docs/adr/0020-*.md` + the gitignored run packages `docs/research/private/2026-07-02-partnersim-run{1,2}-*.md`. _(Full prior narrative — the ~8 schema-mismatch findings, both run details, cross-run synthesis — archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **Procurement vertical — GO + SHIPPED (PLAN-0036 Fastenal, Stage 1):** 4th vertical greenlit (s75); PLAN-0036 drafted + merged Draft (#412, `7a7c036`; SD-1…SD-5 confirm-all). Demo target = Fastenal Thailand (auto-parts / EEC); **hero** = asset-failure → governed emergency sourcing, **calm-path** = low-stock reorder. Stage 1 = a PLAN-only pure-config plugin on the ADR-016 engine (zero `services/` core edit; CQ-1 / ADR-0023). **Pitch** = asset-ontology-triggered governed sourcing (native ontology ADR-008 + engine ADR-016), NOT the commoditized "governed"/"cross-vertical" claims. Full record: `docs/plans/0036-*.md` + the s72 de-risk dossier `docs/research/private/2026-06-22-procurement-*.md` (5 files: spec-expressiveness, GTM, asset-aware incumbent scan, AI-sourcing teardown, platform-incumbent deepdive). _(Full prior narrative archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).
- **The autonomy fork — Stop-hook misfires: CLOSED s167, no longer an open question.** RESOLVED by **option A′** (Cray, typed) and SHIPPED the same session — the `dispatch` verdict is a **suggestion, not an order** (#870 filed, #871 built). Final ledger: **14 recorded misfires across 5 sessions against 0 recorded valid dispatch-arm fires** in ~2 months live; four shapes in two families (knowledge · judgment). **The whole argument — the shapes, the families, the rejected options, the scope locks, the honest caveat that an unrecorded valid fire cannot be fully ruled out — is settled history preserved in `docs/plans/done/0092-stop-hook-dispatch-arm-demotion-to-suggestion.md`; do not restate it here.** _[path fixed s170: archived to `done/` at s168 — the entry still cited the active-plans path.]_ _[Corrected s169: this entry still listed **SD-D** as PARKED — it was **CLOSED s168 (#886)**, the classifier prompt reworded to a routing suggestion with two contract tests.]_ Live remainder: only **option (e)** (flip the classifier backend from local Ollama `gpt-oss:20b` to Sonnet), **deferred**, its API-key/org fail-closed probe unrun. Full narrative: the Session-167 CF block above.

## Active TODOs

- [ ] **The AT-2 extraction — only the F-FACTORY half remains, owned by PLAN-0076 T1.** The criterion-vocabulary half SHIPPED as PLAN-0087 — COMPLETE 8/8, ARCHIVED (s158 #840, s159 #841). ADR-0025 D7's generator deferral was CANCELLED at N=4 (Cray-ratified, typed). Cray-ratified SD-1 = (a): the procedure-aware `ExecutorFactory` half stays with PLAN-0076 T1, guard `test_at2_extraction_obligation_is_owned` ARMED. Full detail incl. the Closeout and the deliberately-unopened `scored_rule._KNOWN_CRITERIA`: `docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` + `docs/plans/0076-*.md` §A.
- [ ] **PLAN-0075 follow-ons — homed by PLAN-0076 (`Status: Tracking`, #752, s133).** T1 (ADR-0031 D3 gate-plugin seam, F-FACTORY) is PARTIALLY discharged: the criterion-vocabulary half shipped as PLAN-0087 (#840/#841); the procedure-aware-`ExecutorFactory` half stays OPEN and owned here. T2's F-PIN remainder CLOSED s143 (#784) — but **F-PIN itself stays OPEN**, so PLAN-0076 does NOT archive and its AC-6 presence guard (`test_at2_followon_tracking_guard.py`) stays ARMED. PLAN-0075 is COMPLETE (13/13) → `docs/plans/done/0075-*.md`. Full detail: `docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` §A.
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2) — open ONLY for the O-2 residue.** Every other leg is DONE + archived (PLAN-0046/0048/0061/0062/0066/0067/0068/0070/0071/0073 → `docs/plans/done/`). **The one OPEN residue:** procurement's `intake` is declared-expressible under shadow parity, but production execution stays the co-existing `_SeedQuery` for derived fields. Full detail: `docs/plans/done/0062-per-vertical-seed-migration.md` (SD-C — the co-exist decision + its STOP-and-surface tripwire) + the transform arc `done/0077-*.md`/`done/0078-*.md` (both COMPLETE), where the residue is homed and walled in **`done/0078-*.md` §L-3 + its Out-of-Scope**. _[Corrected s167, classified `was an error`: this entry previously said the fold-in "is named in `docs/plans/0076-*.md`". It is **not** — PLAN-0076 has **zero** hits for `_SeedQuery` / `candidate_quotes` / nest / reshape / shadow-parity / O-2 and tracks only F-FACTORY (SoD-scoping) + F-PIN (derivation-pin). Verified by scoped grep.]_
- [ ] **Bounded/incremental chain verification (PLAN-0063 SD-4 follow-up, s118).** `GET /audit/verify` walks the WHOLE chain O(n) on demand — accepted at pilot scale. Future work = a checkpointed head / verify-since-anchor design; anchor storage ≈ external anchoring — **do not build without re-reading the tripwire** in `docs/plans/done/0063-audit-chain-verification-surface.md` + the `services/api/routers/audit.py` module docstring (SD-4). _[Note: the docstring's "ADR-011 boundary" is an EARMARK — `docs/adr/` jumps 0010 → 0012.]_ *(#688/#690)*
- [ ] **DEFERRED: a monotonic `sequence` column on `step_results` — the ROOT fix for `load_run`'s wall-clock ordering.** Needs a DB migration → its own PLAN; none drafted, the deferral STANDS, and both surviving orderings are DISPLAY-ONLY. Full detail (ROOT-vs-guard, why it is tolerable, the AST guard, the un-defer trigger): the module docstring of `tests/services/db/test_load_run_ordering_guard.py`. _[s169: the un-defer trigger got its FIRST real-case reading and **did not fire** — Cray's SD-8 = (a) ELIMINATE removed PLAN-0088's paginated listing rather than un-defer the key, so the shipped substrate is aggregate-only and order-insensitive (AC-3 AST tripwire holds). **This PLAN now also owns newest-first `/runs` listing pagination**, and `view-map.js` (a `CAP = 5` truncating consumer) is a second dependant to respect when it opens.]_
- [ ] **Rock 4 — s84 deep research DELIVERED → O-sequence locked.** Cray locked **O-1 → O-3 → O-2 → O-4**. **O-1** (Box-4 ฿ pitch) **DONE** · **O-3 = ADR-0025 Accepted** · **O-4 = PARK** (agent-interop; `docs/adr/0032-*.md:169` D4 — option-only, un-park = a counterparty's *written* pull). **Remaining: O-2 only** (economic-impact facet + Q3 data-binding = Rock 3). Full detail: `docs/adr/0025-at2-managerial-layer.md:19` (O-sequence + Box-3 fit) + `:23-29` (the **evidence-asymmetry** finding — bullish ROI all vendor-authored, independent mostly skeptical — rehomed s142). *(s84 Cray ask)*
- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten. **Full table (all six rows + their triggers + where each lands): `docs/plans/done/0005-oct-engine-runtime-layer.md:390` §8.1** — which itself instructs this STATUS entry to be a pointer. *(per Cray note 2026-05-21)*
- [ ] **Demo card UX — "trust shape", NO operator confidence badge (s74 design, Cray-approved).** The operator card shows what / grounded-why / approve gate + a "show full reasoning trace" toggle; no confidence badge (`confidence_signal` is engine-internal QA, trace-only), and SD-3 settles at (a) — the first-class `verification` field is NOT needed. Full record + rationale + the reconsider-trigger: the §SD-3 post-archival amendment in `docs/plans/done/0035-governed-action-verify-reshape-build.md`; `ADR-0030` cites it. *(Trigger: the next demo / UI round.)*
- [ ] **PLAN-004 Phase C — OPTIONAL POLISH (forward-declared; "may never land"):** HTML/markdown handoff dashboard under `docs/` + references-graph (mermaid dispatch chains) + `render_transcript.py` unified session export (PLAN-0004 §"Phase C"). *(Phase A + B both COMPLETE — session 35; the prior TODO's validator **warning-swallow bug was FIXED #312**, s58. Minor never-formally-scoped sub-ideas — README/`_rename-map` walk-exclusion, Cat G `references_*` autofix, OQ-2 effective-vs-authored `status:` dashboard flag — fold in only if Phase C lands. Reconciled 2026-06-16 s65 audit.)*
- [ ] **Custom Postgres image with extensions (pgvector / AGE / pg_trgm) — needs a fresh ADR number + a PLAN; neither drafted.** *[Corrected s141: **PLAN-002 does not exist** ("NOT yet drafted", `docs/plans/done/0005-oct-engine-runtime-layer.md:14`), and the old "≥ ADR-014" floor is **moot** — ADRs now run to 0032 and `0014-WITHDRAWN.md` exists.]* Context: **`docs/adr/0013-autonomy-axis-relocation.md:285-289`** (the floor-bump note) + **`docs/plans/done/0005-*.md:403`** (trigger: semantic + graph features).
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (low priority)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)

## Next Steps

1. **PLAN-0005 §8.1 revisit register** — remaining deferred-foundational simplifications at their batch boundaries (audit framework, mapping layer, ORM emitter, base-Postgres → the custom-Postgres image, registry discovery). _[Corrected s153: dropped the stale "→ ADR-011+" and "→ PLAN-002 (≥ADR-014)" pointers — **ADR-011 does not exist** (earmark only, per the Active TODO above) and **PLAN-002 was never drafted** with its ADR floor moot; each item's corrected status lives in Active TODOs.]_
2. **Partner-trial readiness gaps** — `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` awaits a dedicated Cray discussion.
3. **Deferred (backlog)** — PLAN-004 Phase C only (optional polish: handoff dashboard / references-graph / unified export — Phase B complete s35, warning-swallow fixed #312); the custom Postgres image (needs a fresh ADR number + a PLAN — neither drafted; see the Active TODO for the corrected framing).
4. **Ongoing** — Continue exercising the file-based handoff mechanism (Chat ↔ Code ↔ Cowork) across batches.

## Update Workflow

This file is updated when:
- A commit changes project state significantly
- A new ADR/PLAN is minted or completed
- Active priorities shift
- A batch closes (sync `last_updated` + `current_batch` + `head_commit` + `recent_commits` frontmatter)
- A session closes (sync all frontmatter fields; archive batch history if needed)

**Update mechanism (locked per STATUS staleness batch 2026-05-18, Hybrid A+B short-term, C long-term):**

- **Per closeout (Option A + Q1(b) discipline):** Closeout drafter includes the line "STATUS.md updated: yes / no / N/A" in their closeout. If `yes`, the closeout's commit batch should include a dedicated `docs(status): …` housekeeping commit (Q3(b/c) pattern) bumping at minimum the `last_updated` and `head_commit` frontmatter fields.
- **Per batch boundary (Option B full body):** Full body refresh (Current Focus + Recent Decisions + Active TODOs + Next Steps) at batch close, alongside the frontmatter bump.
- **Per session boundary:** Full body + frontmatter sync; consider archive of prior session's batch history.
- **Future (Option C, PLAN-004 Phase A):** Validator will flag stale STATUS.md by comparing **frontmatter `last_updated` field** against newest closeout's `created` timestamp (NOT file mtime — mtime is defeated by side-effect commits, e.g. `c85a595` 2026-05-16 normalization sweep that touched STATUS.md body without bumping `last_updated`).

**Q4 `head_commit` semantics (codified 2026-05-18, locked Cray ratification of midflight `2026-05-18-1049` §4 + closeout `2026-05-18-1202` §6.2):**

- `head_commit` = short SHA of the newest **substantive** commit on
  `origin/main` that STATUS.md content reflects.
- **Excluded from `head_commit`:** `docs(status): …` housekeeping
  commits. These commits encode no new repo state — they ARE the
  STATUS.md freshness marker. Including them in `head_commit` creates
  a self-defeat where every housekeeping commit makes STATUS.md appear
  "fresh" to Q4 detection regardless of substantive backlog.
- **Substantive (included in `head_commit`):** everything else —
  `docs(lessons):`, `docs(adr):`, `docs(runbook):`, `feat:`, `fix:`,
  `chore:` (when changing meaningful state), `refactor:`, `test:`, etc.
  Any commit type that changes durable repo content updates
  `head_commit` at the next STATUS.md edit.
- **Reader recipe (returning after a pause):**

  ```bash
  # Newest substantive commit on origin/main (the value head_commit should hold)
  git log -1 --format=%h --invert-grep --grep='^docs(status):' origin/main

  # Compare to STATUS.md head_commit field
  grep -E '^head_commit:' docs/STATUS.md
  ```

  If the two differ → STATUS.md content is stale relative to substantive
  repo state. If they match → STATUS.md is fresh.

- **Writer rule (at each STATUS.md update):** Set `head_commit` to the
  output of `git log -1 --format=%h --invert-grep --grep='^docs(status):' origin/main`
  *after* the substantive commits of the current batch land but *before*
  any `docs(status):` housekeeping commit (or, if the STATUS.md edit
  itself is in a substantive commit like `docs(lessons):`, set
  `head_commit` to that substantive commit's own SHA — which becomes
  knowable only post-commit, so the writer typically updates
  `head_commit` to the *most-recent prior substantive commit* and lets
  the next batch's first edit catch up).
- **Two failure modes this rule closes:**
  1. **mtime trap** (closeout `2026-05-18-1202` §2): side-effect commits
     that touch STATUS.md body without bumping `last_updated` (e.g.
     `c85a595` 2026-05-16 normalization sweep) leave the file mtime-fresh
     but semantically stale. A SHA in `head_commit` cannot drift this way.
  2. **Housekeeping self-defeat** (closeout `2026-05-18-1202` §6.2 +
     midflight `2026-05-18-1049` §4): if `head_commit` = own SHA, every
     `docs(status):` commit makes Q4 say "fresh" regardless of
     substantive backlog. Excluding `^docs(status):` from the comparison
     baseline closes this loophole.

Manually edited until Option C lands.
