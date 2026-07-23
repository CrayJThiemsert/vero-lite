---
last_updated: 2026-07-23T22:40:00+07:00
session: 168
current_batch: "s168 CLOSED — PLAN-0091 COMPLETE 10/10 + ARCHIVED, and the two defects closing it exposed: the scaffolder's emitted package could not load, and `vero-lite scaffold` wrote nothing. Six PRs merged (#881-#886), 0 open."
current_actor: code
blocked_on: "Nothing. main=c2b92c5; suite FRESH 3109/7 on the merge commit; ruff + mypy --strict (106 files) clean; MS-S1 COLD (never contacted)."
next_action: "Cray's call — no work is ordered. Candidates, grounded s168: PLAN-0088's 8-AC re-draft (the RE-DRAFT is the ungated work, not the build; needs plan-drafter); scaffolder v2 extend-shapes (needs a seam spec first, Cray-ratified create-only); 14 stale remote branches + the 6 just merged (delete/keep call). PLAN-0076 T1 stays counter-indicated."
head_commit: c2b92c5
recent_commits: [c2b92c5, 5865d19, 4994801, 844eb6d, c47232f, b8f011d, 64c2190, e28c150, f28c8e3, de8dbbd]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

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

> **Session 166, 2026-07-23 (head_commit `6e351fc` → `9e19905`) — a two-arc,
> two-PR, docs-only session. Arc 1 ported the reported GPT 5.6 Pro
> conjecture-refutation episode into working discipline: the
> `code-operational-policy` skill gained § "Dispatch quality — hold the goal,
> arm the oracle" + Lesson #0032 filed (#866: `9200552` skill + `0a1cbe4`
> lesson; gate PASS 3m14s). Arc 2 (parallel, recorded below) re-grounded
> PLAN-0091 against the code before the build — #865 → `9e19905`: SD-5
> surfaced OPEN, s165's published build order REFUTED.**
> **(trigger + two-model analysis.)** Cray shared the reported episode — the
> general Dinitz–Garg–Goemans conjecture (open 30+ years) refuted via four
> short goal-holding prompts + one attached near-miss paper. Opus 4.8 first
> pass: a 4-prompt decomposition, 5 gaps (G1–G5), 2 already-strong
> confirmations (the goal-evaluator's refute mandate; `/goal amend`'s drift
> protection). Mid-session switch to Fable 5 for an adversarial R2: 4 new
> angles (copy the operator's CONTROL LOOP, not the prompts; the attachment
> is a near-miss to interrogate, not a template to imitate; dispatches were
> brake-rich / accelerator-poor; two work regimes) + 3 explicit disagreements
> with the first pass.
> **(shipped in #866.)** Skill: the 3 dispatch blocks — § Frontier with the
> verbatim anti-anchoring sentence ("You are permitted to propose that an
> item in this fact-pack should be ELIMINATED, not automated or preserved") ·
> the oracle-scoped accelerator clause · the REJECT-if list of named
> fake-done forms in the return contract — plus the M1–M4 follow-up
> vocabulary (goal constant, process pressure rising), the pre-close
> counterexample step (test the ORACLE, not the code), and description
> triggers extended so the skill fires on dispatch authoring / partial-return
> follow-up / AC close. Lesson #0032: ambition ∝ oracle strength; the two
> work regimes (plan-first execution, already codified §11/Lesson #0026, vs
> gate-at-checkpoints exploration, named here and mapped to the Fable-tier
> model-economy policy); what does NOT transfer (survivorship bias ×2,
> asymmetric error cost, the human judgment core).
> **(deliberate scope, recorded IN the lesson so it is not re-litigated.)**
> NO partial-ratchet detector and NO strategy-paragraph hook (both
> judgment-shaped — M3/M4 stay conversational; a hook can only check a
> paragraph EXISTS = ritual compliance); the REJECT-if list homed in dispatch
> return contracts, NOT the G2-gated plan template; promotion to
> template/convention is Rule-of-Three on recorded catches (every catch gets
> logged).
> **(process.)** One Stop-hook misfire declined via the override clause (the
> 13th fire — see the autonomy-fork ledger below); a separate bare "Continue
> generating" nudge also fired once — benign, not a dispatch, not counted.
> PR #865 (the PLAN-0091 arc's) was still OPEN at this arc's close, untouched
> by it — **now MERGED, in the parallel arc recorded below**. No suite ran in
> THIS arc (docs-only), and its "2995/7 is inherited from s164, not fresh"
> note is **now SUPERSEDED** — the parallel arc re-ran the suite FRESH at
> `355acb2` (see below). MS-S1 untouched/COLD, zero calls.
> **(parallel arc, same session — PLAN-0091 RE-GROUNDED before the build, not
> built. #865 `c11135f` → re-sync `fc29b3c` → merge `9e19905`, `docs(plans)` —
> docs-only, PLAN stays `Status: Draft`.)** The build did not start; the PLAN
> was re-read against the code first, and it moved: one NEW decision surfaced
> OPEN, two unnamed Step-4 hazards recorded, and s165's build-order claim
> refuted. `gate` PASS twice, **both SHA-verified against the head** — 3m14s on
> `c11135f`, 3m13s on the re-synced merge commit `fc29b3c` (`origin/main`
> `6e20a65` merged IN, never force-pushed). The suite was re-verified **FRESH**
> at `355acb2` *before* any edit — **2995 passed, 7 skipped in 177.87s**,
> matching the s164 prior exactly → logged **`confirmed — prior intact`**
> (CLAUDE.md §6); 7 skips = dev Postgres connected. **#865 is docs-only, so no
> suite re-run was owed on the merge commit and none was done.** MS-S1 COLD,
> zero calls all arc; loop-dispatcher DISABLED.
> **(the load-bearing correction — s165's forward dependency is REFUTED.)**
> s165 read "Step 1 carries a forward dependency on Step 4" and published the
> order **4-shape → 1 → 2 → 3 → 4-emit → 5 → 6 → 7**; both are wrong and are
> **corrected in the PLAN**. `derive_governance_todo` (`draft.py:293-322`)
> derives AT-2 obligations from `(gate_kind, kind)` alone and **never reads
> `REGISTRY`**, and the row-11 spine sequence is readable straight off the
> committed donor `verticals/fleet_maintenance/procedures.yaml:117-282`.
> Classified **`was an error`** — an over-strong inference, no code changed
> since. **CONSEQUENCE (the reason this reconcile exists): Steps 1–3 are
> executable NOW; Step 4 is the only one that waits on SD-5.**
> **(SD-5 — NEW and OPEN, awaiting Cray.)** Step 4's design note promised the
> S1 classify surface would not grow and the API abstain guard would stay
> as-is. That is structurally false if the AT-2 template registers in the
> shared `REGISTRY`: `generator/pipeline.py:225` builds the classify catalog
> from `REGISTRY.values()`, `:253`/`:258` route by label through the same dict,
> and the guard `_archetype_disagreement` (`:188-202`) rejects an AT-2 gate
> only when the model actually emits one in `step_gates` (`:190`) — its own
> contract at `:186-187` says an empty step list is not a disagreement, so it
> is a second layer, **not a guarantee**. Options: (a) tool-local registry ·
> (b) catalog-seam filter · (c) accept AT-2 into classify. **Recommendation
> (a)** — the only one keeping SD-1 = (c) "no ADR" intact; **(c) would re-open
> SD-1**. Recorded alongside it: **one unbudgeted RED test the PLAN never
> named** — `tests/services/engine/procedures/test_archetype_templates.py:37`
> asserts `set(REGISTRY) == set(AT1_FAMILY)` and goes RED the moment AT-2
> registers centrally (under (a) it never fires); adjacent drift noted — that
> file's `AT2_ONLY_KINDS` (`:32`) omits `GateKind.SEVERITY_TIER`, which
> `pipeline.py:82-84` and `draft.py:283-285` both include.
> **(smaller corrections + two build hazards, also into the PLAN.)** AC-10's
> scope — the module docstring tally runs `test_procedures_endpoint.py:5-9`,
> not `:5-6`. SD-4's line attribution — the stale token is "fleet_maintenance
> ships two" at `:8` (`_EXPECTED` ships three at `:63-77`), proved by the
> narrative summing to **12** against the executable `assert total == 13` at
> `:151`; "six" at `:5` is correct. Step 6's cited tripwire ranges re-checked
> **byte-exact**, with exactly one assertion (`:315`) going RED on a genuine
> 5th signature → `confirmed — prior intact`. Two hazards added: the extracted
> fingerprint helper must take an **explicit root** rather than inherit the
> CWD-relative `Path("verticals").glob(...)` scan at `:269` (else AC-8 goes
> vacuous), and four in-file call sites move with the helpers. Step 2 gains a
> chdir note (`validate`/`generate` are CWD-relative, `cli.py:25-30` → reuse
> the shipped `staged_repo` pattern, `test_cli_e2e.py:26-41`).
> **(process — continues the s165 pattern.)** Every finding was re-verified by
> the caller on disk before it entered the commit: a subagent over-claimed
> twice in this arc — it asserted the abstain guard "will no longer abstain"
> (too strong) and pinned a stale count to the wrong line — and both were
> caught by reading the code. **Subagent output is a draft, not a result.**

> **Session 165, 2026-07-23 (head_commit `3193acc` → `6e351fc`) — the session
> that UNBLOCKED PLAN-0091. Step 0 was its only bar ("no build before Step 0
> lands" gates every Step, not just Step 2), and Cray adjudicated all four
> surfaced decisions by typed AskUserQuestion, each as the drafter recommended:
> SD-1 = (c) PLAN-level, no ADR, promotion tripwire armed · SD-2 = create only ·
> SD-3 = the typed required-slot checklist as an interview loop · SD-4 = stop
> counted prose, load-bearing counts become executable assertions. Three PRs,
> all merged, all docs-only; 0 open at close.**
> **(the ranking that preceded it.)** A four-agent Explore fan-out re-ranked the
> candidate set against code. It found **zero claim-vs-code mismatches** in
> PLAN-0091 — every load-bearing citation, including the fleet AT-2 signature
> AC-7 pins on, verified byte-exact — and confirmed both genuine gaps: **no
> narrative→ontology code path exists** and **no ADR covers ontology
> generation**, which is exactly why SD-1 existed. It also corrected the
> orientation read twice: **Step 1 was blocked by SD-3, not SD-1** (SD-3's
> recommendation *is* Step 1's design, so "start Step 1 while SD-1 is pending"
> never existed), and — **believed here, REFUTED s166 by #865 (see the s166
> block above); this whole ordering claim is CORRECTED** — that **Step 1
> carries a forward dependency on Step 4** because its checklist derives from
> AT-2 obligations while no AT-2 `ArchetypeTemplate` exists and the first is
> authored in Step 4, which published the execution order **4-shape → 1 → 2 →
> 3 → 4-emit → 5 → 6 → 7** (not the printed 1→7) and classified it
> `superseded by new info` — an emergent ordering constraint, not a drafter
> error. **s166 re-classified it `was an error`:** `derive_governance_todo`
> never reads `REGISTRY`, so no such dependency exists and **Steps 1–3 are
> executable now**; do not build to the order quoted above.
> **(#861, `83854ad` → merge `54a2b73`, `docs(plans)` — fast-forward, docs-only,
> 1 file +47/−4.)** `gate` PASS in 3m15s and **SHA-verified** (run `headSha` == PR
> head) before the merge, on Cray's typed instruction. Each ruling recorded inline
> at its own SD; Step 2's "waits for that ADR" parenthetical struck through and
> resolved. **PLAN-0091 is now BUILD-READY and deterministic-offline** — AC-9
> requires the full AC suite to pass with MS-S1 unreachable.
> **(#862, `cea650e` → merge `dc38ca1`, `docs(plans)` — fast-forward, docs-only.)** The
> PLAN-0076 §T1 prose correction: the paragraph read "zero live collisions", which
> the s160 SoD-scope guard had **already refuted on disk** — collisions exist
> (procurement reuses `intake`/`approve` across three procedures); what is zero is
> the **over-mark**. Load-bearing here because T1's first named trigger was worded
> "a live `step_id` collision" — read literally, **it had already fired**. Restated
> as an *observable* over-mark. **One proposed correction was REFUTED and
> deliberately NOT applied:** the claim that the ADR-0031 D4.1 citation was wrong
> because "T1's trigger fired twice at N=3/N=4" — those firings are the
> AT-2-signature / criterion-vocabulary axis, **discharged by PLAN-0087**;
> F-FACTORY's own triggers remain unfired, so D4.1 is the applicable rule. The
> refutation is written into the PLAN so it is not re-proposed. Guards verified
> green before commit (9 passed), tripwires intact.
> **(#863, `4af05fb` → re-sync `b3dd3d1` → merge `6e351fc`, `docs(status)`.)** The
> s163 Stop-hook misfire **backfill** — the doc gap s164 named and left open — plus
> a correction to s164's own diagnosis: "the reason had real content so the floor
> did not demote it" is **too generous to the floor**, which is called only on the
> **proceed** arm while these misfires arrive on the **dispatch** arm and never
> reach it *at any content level*. The floor was unreachable, not out-argued — so a
> new deterministic layer bolted into the proceed arm would miss this shape too.
> Also opened the running **autonomy-fork ledger** under In-Flight Discussions. This
> PR was **re-synced by merging `main` INTO the branch** after #862 landed (strict
> protection; never force-pushed), and was **SHA-verified against the NEW head**
> `b3dd3d1`, not the pre-re-sync `4af05fb` — the easy mistake when landing a stack.
> **Verification / state:** all three gates SHA-verified before merge (3m14s /
> 3m7s / 3m19s). **No full suite ran this session** — every PR was docs-only, so
> 2995/7 is an INHERITED prior from s164, not fresh evidence, and the next session's
> first run is a real re-verification. R1 size guard PASSED (52,703 → 59,315 B,
> ceiling 65,536); R7 citation guard PASSED. **0 open PRs at close**; MS-S1
> idle/COLD with **zero calls all session**; dev Postgres UP; working tree clean but
> for the 2 KEEP untracked paths. Three feature branches deleted on merge, so the
> 14-stale-branch backlog is unchanged.
> **(process — three Stop-hook misfires, all declined via the trigger's own override
> clause.)** Two ordered work already done or already running. **The third was a NEW
> shape:** it proposed opening a *new PLAN* for a 4–8-line `CLAUDE.md` edit and
> routing it to `plan-drafter` — the one agent **hook-DENIED** from touching
> `CLAUDE.md`, and a new file under `docs/plans/` would itself trip G2. So the
> classifier misjudged the **artifact kind** and dispatched to a **closed route**,
> not merely re-dispatching in-flight work. Evidence that option (a) — another
> prompt rule — cannot keep up: each new shape would need its own rule.
> **(open at close, by design.)** The **model-economy rehome** is DISPATCHED but not
> drafted: `CLAUDE.md` §6 routes a constitutional edit through Cowork drafting, and
> Code cannot invoke Cowork — the validator-clean dispatch awaits Cray carrying it
> across. It separates the Cray-ratified core (Fable = planning/research; Opus 4.8 +
> Extra = execution) from four private-memory clauses still needing ratification.


> _Older content rotates out of this file per the **STATUS.md Rotation Policy (R1-R7)** in [`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md) (Lesson #23): Current Focus keeps the 4 newest sessions (<=8 blocks); Recent Decisions keeps the last 10 rows. Rotated blocks/rows live in [`docs/status-archive/`](status-archive/) and git history (Tier 3). Layout — **two separate chains, both with letters ascending with time and the base holding the recent window**: the rotation archive `2026-h1b` → `c` → `d` → `e` → `f` → `2026-h1-status.md`, and the Current-Focus-only `2026-h1b` → `c` → `2026-h1-current-focus.md`. Rotations append to the two bases. **Grep the directory, not a filename** — the chain is one corpus and which file holds a given block is an artifact of where the ~192 KB R4 bar happened to fall. _[Chain created 2026-07-17 (s144): the single `2026-h1-status.md` had reached 592,577 B, 2.3x R4's cap, and the new guard (#789) forced the split.]_

## Prior focus (archived)

PLAN-003 Phase 1 (ontology engine + 5 emitters), PLAN-0005 Phase 2
(OCT engine runtime layer), PLAN-0006 (LLM reasoning hook),
PLAN-0007 Phase 1 (harness autonomy layer — deterministic floor),
and **PLAN-0008 Phase 2 (harness autonomy layer — probabilistic /
classifier-mediated engine on top of Phase 1)** are all **merged and
moved to `docs/plans/done/`**. The Cowork-as-Tier-1 trial that ran as
the test-bed across the earlier batches **concluded** — ratified
permanently by **ADR-009** (Cowork = merged Tier 0 + Tier 1 workspace;
commits stay Code-exclusive). PLAN-004 Phase A (handoff frontmatter
schema + tooling) also landed; Phase B/C remain deferred (backlog).
Full detail lives in `docs/plans/done/`, the Recent Decisions table
below, and git history.

## Recent Decisions (last 10)

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-23 | **s168 — PLAN-0091 COMPLETE 10/10 + ARCHIVED (#883–#885), and the two defects that closing it exposed: the scaffolder's OUTPUT could not load and its COMMAND wrote nothing.** Cray ratified (typed) BUILD over re-scope for both partial ACs — AC-7(a) via **operator-typed intake slots**, never narrative mining (which would trip SD-1's promotion tripwire). `wire.py` registered a `procedures_factory` module the emitter never wrote, and the emitted adapter called `register_adapter` with two args against a one-arg signature (`TypeError` on import); `cli.py` still exited 3 with "Emission is not wired yet" while Steps 2–4 had shipped in #874–#876. **Both invisible to a green suite** — the package tests only `ast.parse` the emitted text, and the golden e2e calls the emitters directly, so **a suite addressed at the library could not see that the entry point was dead**. Honesty corrections recorded, not absorbed: s167's "8/10" was really **7/10** (AC-4 ticked while its text required a `procedures_factory.py` that did not exist — `was an error`, not `superseded`); AC-10's gap was wider AND a different SHAPE (a collection count, on which the shipped per-member pattern scores zero — adding `main.py` to the targets dict alone would have been a no-op); AC-7(c) ships as STRUCTURAL equality because literal bytes would make the tool emit a **false provenance claim about its own output**. One counted site is REPORTED not rewritten, on purpose and asserted as such. Suite 3083 → **3109** with per-PR deltas summing exactly; non-vacuity probed 6× (`/tmp` restore + `cmp -s`); MS-S1 never contacted. Full narrative: the Session-168 CF block above | `c2b92c5` (#886 merge, head_commit of record) / `5865d19` (#885 AC-10) / `4994801` (#884 CLI wiring) / `844eb6d` (#883 AC-7 a/b/c) / `c47232f` (#882) / `b8f011d` (#881) / `docs/plans/done/0091-narrative-to-vertical-scaffolder-tool.md` (COMPLETE, 10/10) + `services/engine/scaffolder/**` + `services/engine/cli.py` |
| 2026-07-23 | **s168 — PLAN-0092 closed 6/6 + archived (#881); the `AT2_ONLY_KINDS` drift fixed with an anti-drift tripwire (#882); SD-D settled — the classifier prompt no longer contradicts the arm it feeds (#886).** SD-D was parked as "stale-ish but harmless"; re-reading found two preamble sentences **factually false** post-A′ (DISPATCH described as something "the agent should NOT pause for", and conservatism justified by "they consume a subagent spawn"), while `.claude/autonomy-triggers.md` — read VERBATIM into the same prompt — described the no-directive behaviour correctly. The model was handed ordering framing and suggestion framing in one call. Reworded to a ROUTING SUGGESTION with the conservative bias intact on a true reason; two contract tests pin the framing AND that the decision value + reply schema are UNCHANGED (a rewording that renamed the verdict would silence the channel entirely). The `AT2_ONLY_KINDS` fix is pinned to `pipeline._AT2_ONLY_KINDS` but deliberately NOT to `draft._AT2_GATE_KINDS` — a distinct concept the design says so itself; the SD-5-guarded assertion is byte-unchanged | `c2b92c5` (#886 merge) / `c47232f` (#882 merge) / `b8f011d` (#881 merge) / `.claude/hooks/_sonnet_classifier.py` + `tests/handoffs/test_sonnet_classifier.py` + `tests/services/engine/procedures/test_archetype_templates.py` + `docs/plans/done/0092-stop-hook-dispatch-arm-demotion-to-suggestion.md` (COMPLETE, 6/6) |
| 2026-07-23 | **s167 — the autonomy fork (open since s71; 14 recorded misfires / 0 recorded valid dispatch-arm fires) RESOLVED + SHIPPED in one session: Cray typed-ratified option A′ — the Stop-hook `dispatch` verdict is DEMOTED from an ORDER to a SUGGESTION (PLAN-0092 filed #870, BUILT #871).** The hook now emits no directive on `dispatch`: pause semantics + stop-chain RESET, the routing sent to Cray as one `stop_dispatch_suggestion` Telegram ping; malformed metadata stays silent. Structural, not a fifth shape patch — it moots BOTH failure families (knowledge · judgment) at the arm. `_sonnet_classifier.py` byte-unchanged; the V1 goal-gate + PreToolUse arms untouched; D1/D2 rows annotated, never deleted. NO ADR amendment — the arm had zero ADR backing (grep-verified), so PLAN-0092 IS the governance record (stays `Draft`; ACs closed by the build, no closeout PR). Full narrative: the Session-167 CF block above | `7c86752` (#871 merge, head_commit of record) / `0870266` + re-sync `6afaf9c` (the build, gate SHA-verified on the re-synced head) / `2646456` → merge `822a7e8` (#870, the filing) / `.claude/hooks/stop_continuation.py` + `tests/handoffs/test_stop_continuation.py` + `docs/plans/0092-stop-hook-dispatch-arm-demotion-to-suggestion.md` (Draft) |
| 2026-07-23 | **s166 — PLAN-0091 SD-5 RATIFIED (a), Cray typed (#869): the AT-2 template is owned by `services/engine/scaffolder/` and NEVER enters the shared `REGISTRY`.** That makes Step 4's design promise true by construction — the classify path stays byte-unchanged and ADR-0024 D7's abstain routing stays literally true (the `_archetype_disagreement` guard is a second layer, not a guarantee). SD-1 = (c) "no ADR" therefore stands undisturbed, and **all five SDs are now closed — PLAN-0091 is fully unblocked, nothing in it awaits a decision.** Tripwire: `test_archetype_templates.py:37` (`set(REGISTRY) == set(AT1_FAMILY)`) must never need editing — if it does, STOP and re-open SD-5 rather than registering centrally | `097d180` (#869 merge) / `9eb7c90` (the ratification) + `1413383` (the STATUS record) / `docs/plans/0091-narrative-to-vertical-scaffolder-tool.md` §SD-5 + `tests/services/engine/procedures/test_archetype_templates.py:37` (the tripwire) |
| 2026-07-23 | **s166 — dispatch-quality discipline shipped (#866, docs-only): the `code-operational-policy` skill gains the 3 dispatch blocks (Frontier/anti-anchoring · oracle-scoped accelerator · REJECT-if) + the M1–M4 follow-up vocabulary + the pre-close counterexample step; Lesson #0032 files the why (ambition ∝ oracle strength; the two work regimes).** Deliberately NOT built: any hook/detector for M3/M4 (judgment-shaped); adoption is Rule-of-Three on recorded catches. Full narrative: the Session-166 CF block above | `b8566a6` (#866 merge, head_commit of record) / `0a1cbe4` + `9200552` (the two commits) / `.claude/skills/code-operational-policy/SKILL.md` + `docs/lessons/0032-ambition-scales-with-oracle-exploration-gated-not-planned.md` |
| 2026-07-22 | **s164 — PLAN-0091 filed Draft (#859, `docs(plans)`): the narrative→vertical scaffolder (`vero-lite scaffold`), 10 ACs / 8 Steps, create-shape only — BUILD-BLOCKED until Cray adjudicates Step 0 (SD-1…SD-4; SD-1 may require an ADR first).** A 4-agent Explore fan-out REFUTED two claims: the scaffolder is **brownfield-with-a-ratified-half** (ADR-0024 pins the generation contract; PLAN-0040 shipped narrative→procedure), and **PLAN-0088 has 12 defects, not 6** — the pilot gate does NOT block it, its own **AC-3 ⊗ AC-12 trilemma** does; 8 of 14 ACs need rewriting. Full narrative: the Session-164 CF block above | `f758509` (#859 merge, head_commit of record) / `74a49c2` (the filing commit) / `docs/plans/0091-narrative-to-vertical-scaffolder-tool.md` (Draft, Step 0 unadjudicated) |
| 2026-07-22 | **s163 — PLAN-0090 filed (#855) → BUILT (#856) → COMPLETE 7/7 + archived (#857): `fleet_maintenance.scheduled_pm_service_round`, the AT-3 SCHEDULED calm path — 16m13s hands-on, steps BYTE-IDENTICAL to the manual path (PROVEN by a dumped-model test).** MS-6 BINDING: a LOWER BOUND, never summed with PLAN-0086's 27m39s or PLAN-0089's ~14 min. A DISTINCT `procedure_id`, never a trigger flip. + the L3 CLI fix: the unwired daemon CRASHED at startup (not "409s at resolve"); a set-equality tripwire now mirrors `main.py`. Gate on `a3ef955`: 2994/7. Full narrative: the Session-163 CF block above | `1ce3546` (#857 merge, head_commit of record) / `a3ef955` (#856 build) / `20f2585` (#855) / `2d34d80` (#854 reconcile + trim) / `docs/plans/done/0090-fleet-scheduled-calm-path.md` (COMPLETE, 7/7) |
| 2026-07-22 | **s162 — PLAN-0089 filed (#851) → BUILT (#852) → COMPLETE 6/6 + archived (#853): `fleet_maintenance.pm_service_round`, the AT-3 calm path, as a measured "extend an existing vertical" experiment — ~14 min hands-on, ZERO engine diff PROVEN (`git diff df1982a..a8d679d -- services/engine/` EMPTY).** M-6 BINDING: a lower bound, never summed with PLAN-0086's 27m39s. + #850 `fix(api)` re-keyed `PROCEDURE_ARCHETYPES` on `(vertical, procedure_id)`. AT-3 GENERALIZED to "a measure vs a per-entity threshold"; N stays 4. Gate on `a8d679d`: 2978/8/5. Full narrative: the Session-162 CF block above | `1b942f5` (#853 merge, head_commit of record) / `a8d679d` (#852 build) / `df1982a` (#851) / `514dc1f` (#850) / `docs/plans/done/0089-fleet-calm-path-extend-an-existing-vertical.md` (COMPLETE, 6/6) |
| 2026-07-22 | **s161 — PLAN-0088 filed Draft (#848, `docs(plans)`): the cross-run read substrate + run-insight readers.** Two Cray-ratified TYPED forks are the PLAN's LOCKED constraints: L1 — "Group A" is NOT Shape 2 and does NOT trip the ADR-0032 D2 pilot gate, proven by a STATIC guard (AC-11), not prose; L2 — build Group A + PROVE the substrate expresses Group B (AC-10) but do NOT build Group B, which stays pilot-gated. Wall-clock ordering hazard PINNED not inherited (AC-3 AST tripwire); the sequence-column PLAN stays UNOPENED. Full narrative: the Session-161 CF block above | `e6bb8c8` (#848 merge, head_commit of record) / `0dce906` (build) / `docs/plans/0088-cross-run-read-substrate-and-run-insight-readers.md` (Draft) |
| 2026-07-22 | **s160 — four PRs hardening the Stop hook and the AT-2 doc record: #844 the CONTENTLESS-REASON FLOOR (complement to #843, landed s159 unrecorded); #845 AT-2 corrected to N=4 + a cross-procedure `step_id`-scope guard; #846 (`plan-drafter`, G1) ADR-0032 re-grounded + a dated ADR-0025 D7 OUTCOME amendment, its "N ≥ 2" decision text deliberately NOT rewritten.** Two premises are now pinned in code, not prose: `_RETRIGGER_N` is retired, and PLAN-0087's "zero live `step_id` collisions" is wrong — both carried by the guard docstrings cited right. Full narrative: the Session-160 CF block above | `0c9cdeb` (#846 merge, head_commit of record) / `d7bbb8b` (#845) / `c42abe4` (#844) / `0090161` (#843) / `tests/services/engine/procedures/test_sod_step_id_scope_guard.py` + `tests/services/engine/procedures/test_at2_signature_retrigger.py` + `docs/adr/0025-at2-managerial-layer.md` (D7 amendment) |

## In-Flight Discussions

- **PLAN-0091 — COMPLETE 10/10 and ARCHIVED (s168).** Built s167 (#873–#879), completed s168 (#883–#885). Full record: `docs/plans/done/0091-narrative-to-vertical-scaffolder-tool.md`. **Two follow-ons it named, neither scheduled:** the **extend shapes** (calm-path + scheduled-variant scaffolding) stay Cray-ratified CREATE-ONLY and need *a fresh seam spec, not just effort*; and the census-narrative comment in `tests/api/test_procedures_endpoint.py` is the one counted site the disposer REPORTS rather than rewrites (`residual_counted_prose`) — a human call, left visible on purpose.
- **PLAN-0088 — the RE-DRAFT is the ungated work, not the build (re-grounded s168).** 14 ACs + 6 Steps read as ready; they are not. S1–S7 are drafter-resolved and UNRATIFIED, 8/14 ACs need rewriting, and the **AC-3 ⊗ AC-12 trilemma** was independently re-verified against code — plus one defect the PLAN does not record: **AC-12 undercounts `/runs` consumers** (`services/api/static/assets/view-map.js` also depends on newest-first, not just `view-monitor.js`). A re-draft routes through `plan-drafter` (a G2-gated artifact for Code). Group A remains ungated by ADR-0032 D2; Group B stays pilot-gated. Precondition to respect: the `step_results` monotonic-`sequence` TODO re-opens FIRST if any reader becomes ordering-sensitive.
- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13; guarded trial (parallel to ADR-012) — verdict **continue-with-adjustments**. Run 1 (energy, s93) + Run 2 (supply-chain, s94) both COMPLETE, S-checks all PASS against pre-committed oracles, no R-PS trigger fired; C-1..C-3 CONFIRMED → **no open partner-sim debt**. ADR-011 audit stays gated on a REAL partner conversation (R3: SYNTHETIC provenance INFORMS but never TRIGGERS it). Full record: `docs/adr/0020-*.md` + the gitignored run packages `docs/research/private/2026-07-02-partnersim-run{1,2}-*.md`. _(Full prior narrative — the ~8 schema-mismatch findings, both run details, cross-run synthesis — archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **Procurement vertical — GO + SHIPPED (PLAN-0036 Fastenal, Stage 1):** 4th vertical greenlit (s75); PLAN-0036 drafted + merged Draft (#412, `7a7c036`; SD-1…SD-5 confirm-all). Demo target = Fastenal Thailand (auto-parts / EEC); **hero** = asset-failure → governed emergency sourcing, **calm-path** = low-stock reorder. Stage 1 = a PLAN-only pure-config plugin on the ADR-016 engine (zero `services/` core edit; CQ-1 / ADR-0023). **Pitch** = asset-ontology-triggered governed sourcing (native ontology ADR-008 + engine ADR-016), NOT the commoditized "governed"/"cross-vertical" claims. Full record: `docs/plans/0036-*.md` + the s72 de-risk dossier `docs/research/private/2026-06-22-procurement-*.md` (5 files: spec-expressiveness, GTM, asset-aware incumbent scan, AI-sourcing teardown, platform-incumbent deepdive). _(Full prior narrative archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).
- **The autonomy fork — Stop-hook misfires: CLOSED s167 (2026-07-23), no longer an open question.** RESOLVED by **option A′** (Cray, typed) and SHIPPED the same session — the `dispatch` verdict is a **suggestion, not an order** (#870 PLAN-0092 filed, #871 built). Final ledger, for the record: **14 recorded misfires across 5 sessions (3× s71 · 3× s163 · 3× s164 · 3× s165 · 2× s166) against 0 recorded valid dispatch-arm fires** in ~2 months live; four shapes in two families (knowledge · judgment), which is the empirical case against "one more prompt rule". **The whole argument — the shapes, the families, the rejected options (a)/(b)/(e), the scope locks, the honest caveat that an unrecorded valid fire cannot be fully ruled out — is settled history preserved in `docs/plans/0092-stop-hook-dispatch-arm-demotion-to-suggestion.md`; do not restate it here.** Live remainder only: **SD-D** (classifier-prompt wording still says "dispatch" in ordering voice) is **PARKED** as a follow-up note, and **option (e)** (flip the classifier backend from local Ollama `gpt-oss:20b` to Sonnet) is **deferred** with its API-key/org fail-closed probe unrun. Full narrative: the Session-167 CF block above.

## Active TODOs

- [ ] **The AT-2 extraction — only the F-FACTORY half remains, owned by PLAN-0076 T1.** The criterion-vocabulary half SHIPPED as PLAN-0087 — COMPLETE 8/8, ARCHIVED (s158 #840, s159 #841). ADR-0025 D7's generator deferral was CANCELLED at N=4 (Cray-ratified, typed). Cray-ratified SD-1 = (a): the procedure-aware `ExecutorFactory` half stays with PLAN-0076 T1, guard `test_at2_extraction_obligation_is_owned` ARMED. Full detail incl. the Closeout and the deliberately-unopened `scored_rule._KNOWN_CRITERIA`: `docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` + `docs/plans/0076-*.md` §A.
- [ ] **PLAN-0075 follow-ons — homed by PLAN-0076 (`Status: Tracking`, #752, s133).** T1 (ADR-0031 D3 gate-plugin seam, F-FACTORY) is PARTIALLY discharged: the criterion-vocabulary half shipped as PLAN-0087 (#840/#841); the procedure-aware-`ExecutorFactory` half stays OPEN and owned here. T2's F-PIN remainder CLOSED s143 (#784) — but **F-PIN itself stays OPEN**, so PLAN-0076 does NOT archive and its AC-6 presence guard (`test_at2_followon_tracking_guard.py`) stays ARMED. PLAN-0075 is COMPLETE (13/13) → `docs/plans/done/0075-*.md`. Full detail: `docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` §A.
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2) — open ONLY for the O-2 residue.** Every other leg is DONE + archived (PLAN-0046/0048/0061/0062/0066/0067/0068/0070/0071/0073 → `docs/plans/done/`). **The one OPEN residue:** procurement's `intake` is declared-expressible under shadow parity, but production execution stays the co-existing `_SeedQuery` for derived fields. Full detail: `docs/plans/done/0062-per-vertical-seed-migration.md` (SD-C — the co-exist decision + its STOP-and-surface tripwire) + the transform arc `done/0077-*.md`/`done/0078-*.md` (both COMPLETE), where the residue is homed and walled in **`done/0078-*.md` §L-3 + its Out-of-Scope**. _[Corrected s167, classified `was an error`: this entry previously said the fold-in "is named in `docs/plans/0076-*.md`". It is **not** — PLAN-0076 has **zero** hits for `_SeedQuery` / `candidate_quotes` / nest / reshape / shadow-parity / O-2 and tracks only F-FACTORY (SoD-scoping) + F-PIN (derivation-pin). Verified by scoped grep.]_
- [ ] **Bounded/incremental chain verification (PLAN-0063 SD-4 follow-up, s118).** `GET /audit/verify` walks the WHOLE chain O(n) on demand — accepted at pilot scale. Future work = a checkpointed head / verify-since-anchor design; anchor storage ≈ external anchoring — **do not build without re-reading the tripwire** in `docs/plans/done/0063-audit-chain-verification-surface.md` + the `services/api/routers/audit.py` module docstring (SD-4). _[Note: the docstring's "ADR-011 boundary" is an EARMARK — `docs/adr/` jumps 0010 → 0012.]_ *(#688/#690)*
- [ ] **DEFERRED: a monotonic `sequence` column on `step_results` — the ROOT fix for `load_run`'s wall-clock ordering.** Needs a DB migration → its own PLAN; none drafted, the deferral STANDS, and both surviving orderings are DISPLAY-ONLY. Full detail (ROOT-vs-guard, why it is tolerable, the AST guard, the un-defer trigger): the module docstring of `tests/services/db/test_load_run_ordering_guard.py`. _[s161: PLAN-0088 (#848) reads runs in aggregate but deliberately depends on neither ordering (AC-3 AST tripwire); any ordering-sensitive read on the substrate re-opens this FIRST.]_
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
