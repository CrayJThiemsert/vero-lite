---
last_updated: 2026-07-28T13:09:08+07:00
session: 183
current_batch: "s183 — PLAN-0094 ARCHIVED to done/ (Cray released the live-loop soak: no anomalies) with OQ-4 re-homed here per Step 6; goal-gate `evaluations: 0` DIAGNOSED — the warn path under enforce:false records nothing, by design."
current_actor: code
blocked_on: "Nothing blocking."
next_action: "Cray's ruling on the CLAUDE.md `< 20 KB` unit (decimal vs KiB) — PARKED s183 by Cray, so the extraction dispatch stays unsent. Otherwise: decide whether the goal-gate warn-path observability finding becomes a PLAN (see Active TODO)."
head_commit: 5d64a7d
recent_commits: [5d64a7d, 0f07dfd, fd3469e, b5d2ccd, 1d0649f, 6726b69, 1281b5c, 7c4e488, 85efe52, 8ffd290]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 183, 2026-07-28 (head_commit `1d0649f` → `5d64a7d`) — the session
> the gate that records nothing turned out not to be broken. **PLAN-0094 is
> ARCHIVED** — Cray released the live-loop soak — and the `evaluations: 0`
> finding carried out of s182 is **diagnosed, not guessed**: the goal gate's
> most-travelled outcome is its least observable one.**
>
> **(the soak — released, and recorded as what it is.)** The `git mv` to
> `done/` was gated on one thing no session can self-serve: the L1 guards run
> on **Cray's own working loop**, so only Cray can report whether the new
> non-progress unit misbehaved. Asked directly, Cray reported **no anomalies**
> across the sessions run since Step 4 landed (s180). That is the whole of the
> evidence — a negative report on a live loop, **not a test run** — and it is
> written into the archived PLAN in those terms rather than dressed up as a
> gate artifact. **OQ-4 was re-homed to an Active TODO in the same change**,
> exactly as §Step 6 demanded; it is not buried in `done/`.
>
> **(the goal-gate finding — the mechanism is FINE; the observability is not.)**
> s182 closed with `.claude/state/goal.json` sitting `status: active` and
> `evaluations: 0` across many Stops, cause unestablished. Four measurements,
> each fresh on disk:
> **(1)** `save_goal()` serializes with `sort_keys=True`
> (`_goal_state.py:406`) but the on-disk key order is `schema_version, goal,
> source, …` — **not alphabetical**, so that function had **never once written
> the file**. **(2)** An offline probe replayed `run_goal_gate({})` against a
> **copy** (via `CLAUDE_GOAL_PATH`, so the evidence artifact was never
> touched): it imported, parsed all 8 criteria, ran all 4 checks green,
> dispatched, and **wrote** — `evaluations 0 → 1`. **The gate works today.**
> **(3)** C1–C4 complete in **32 s** against the harness's **180 s** kill on
> `stop_continuation.py` (`settings.json:80`), so the timeout theory is
> **refuted**, not merely doubted. **(4)** Reading the code closes it:
> `_failing_consequence` under `enforce: false` pings Telegram and
> `return None` — **no `record_evaluation`, no `save_goal`**
> (`_goal_gate.py:440-446`) — and *any* failing check routes there
> (`:491-494`). s182 spent its session running an 18-mutation sweep, in which
> C1 (`pytest tests/handoffs -q`) goes **red by construction** on every
> mutated Stop. Every one of those Stops took the silent path.
>
> **(why this is a finding and not a shrug.)** `enforce: false` is the default
> posture and a red check is the *ordinary* mid-work state, so **the most
> frequently travelled branch of the gate is the only one that leaves no
> in-repo trail**. `_goal_gate.py` has no logging at all; its sole signal is a
> Telegram ping that leaves the machine, cannot be audited from the repo, and
> **no-ops silently if `tools/notify/telegram.sh` is absent**. That is
> structurally the same defect class PLAN-0094 AC-1 exists to kill — a
> mechanism that looks live and records nothing. The author knew: the wrapper
> comment at `stop_continuation.py:600` says "warn-only outcome -> classifier
> flow unchanged", and `_goal_gate.py:437-439` calls it "v1 — the stop fires".
> **So the behaviour is ratified, and changing it is an ADR-0018 question, not
> a patch** — logged as an Active TODO with the recommendation, not fixed
> here.
>
> **(five stale STATUS sites corrected, all `was an error`.)** The grounding
> sweep found this file asserting the PLAN-0094 §Verification **live-check (ii)
> is "still unrun"** in **five** places — including `next_action`, which was
> actively directing the next session to **re-run work that had already
> passed** at s182 (#945). Also corrected: the PLAN-0036 pointer still named
> the pre-archive path and called it "merged Draft" when it is `done/` with
> `Status: Done`.
>
> **(the check that was mis-specified caught more than the check that was
> aimed.)** The pre-committed verification asserted "zero `docs/plans/0094`
> references" and came back **4** — the Recent-Decisions `Reference` columns,
> pointing at a path this very change had just deleted. Two *other* assertions
> in the same run also failed and were **false alarms**: the counts included
> this session's own narrative *quoting* the defect it was fixing. Rather than
> patch the thresholds, the check was **generalised** — resolve *every*
> `docs/plans/…` path in the file against disk — and it immediately found a
> **fifth** dead pointer nobody was looking for — the **PLAN-0095** reference,
> stale since that PLAN archived at **s177**, six sessions ago. **A `Reference`
> column is a navigation aid, not a historical claim**, so the paths were fixed
> while the decision text was left untouched. Generalising a failed check beat
> re-tuning it. _(One recursion worth recording: the first draft of this very
> paragraph quoted the dead path **literally**, which re-broke the sweep it was
> describing. Prose about a stale pointer must not contain one — the check
> cannot tell narration from assertion.)_
>
> **State at close:** `main` `5d64a7d` → this PR. `pytest tests/handoffs -q`
> green (31 s), `mypy services/` clean, `ruff` clean at CI scope, thresholds
> byte-unchanged. **R2 rotation applied** — the s179 Current-Focus block and
> the s174 Recent-Decisions row moved to `docs/status-archive/`, boundary-
> asserted before the write so a mismatch would abort rather than half-apply.

> **Session 182, 2026-07-28 (head_commit `1281b5c` → `1d0649f`) — the sweep
> that re-ran everything instead of citing itself. One PR merged (#943), 0
> open. **PLAN-0094 Step 6 executed and AC-10 CLOSED** — all 11 ACs are now
> closed or withdrawn — proved by a **full fresh 18/18 non-vacuity mutation
> sweep**, plus two stale-doc defects fixed. Gate at close: **3327 passed /
> 8 skipped**, `mypy services/` clean over **110 source files**, `ruff` clean
> at CI scope, CI `gate` PASS.**
>
> **(the framing that matters — Cray typed the expensive reading.)** Two
> readings of AC-10's sweep were offered *before* the run: re-confirm
> AC-1…AC-5 and cite the recorded s177/s180 build-time runs for the rest, or
> re-run everything fresh. Cray typed the **full re-sweep**. So every
> mutation below is fresh on-disk evidence, not a citation, and the
> pre-committed pass/fail read was fixed before the baseline ran.
>
> **(18 mutations, 18 clean.)** 11 named by the PLAN (M-A…M-D, N-A…N-D, and
> AC-9's three) plus **7 derived** for the ACs that name none — AC-1(i),
> AC-1(iii), AC-2, AC-3, AC-5, and AC-9(d), the goal-gate-directive row that
> had a negative test but no named mutation. **`missing_red` was EMPTY for
> all 18**: no predicted-red row stayed green, so no oracle in this surface
> is vacuous. Sibling invariance held — no L2/L3/L4 row reddened under any
> mutation. Applied by a **harness script, not the Edit tool**: the files
> under mutation are the session's own live hooks (python re-reads them per
> invocation), so an Edit-tool apply would feed the mutated L1 logic the very
> edit that installed it, and M-A ("always increment") would count the
> sweep's own edits toward a deny. Restores were `/tmp` copies, never
> `git checkout`.
>
> **(finding 1 — M-A's blast radius is 8 L1 rows, not the 3 first
> predicted.)** A whole-feature revert must redden every row asserting a
> specific L1 count or a recorded-but-not-counted edit. This is **neither a
> code defect nor a PLAN defect**: the session's own prediction was too
> narrow, and the PLAN's load-bearing claim — L2 and L4 stay green — is
> **`confirmed — prior intact`**, more strongly than it was stated. Widening
> was legitimate only because `missing_red` was empty (nothing predicted-red
> went green) and because the correction runs toward **more** breakage, never
> less.
>
> **(finding 2 — AC-4 additionally reddens AC-11(i), and that is a FEATURE.)**
> AC-11(i) asserts the deny body names *the threshold actually applied*, so
> moving the gate onto the warn bar renders `N/6` and the row moves with it —
> positive evidence that the row reads the applied bar instead of hard-coding
> a literal.
>
> **(finding 3 — the harness's own site-count guard aborted a naive apply.)**
> The first AC-1(iii) attempt stopped on a site count:
> `pretooluse_loop_detect.py` is registered at **TWO** PreToolUse sites, not
> one. A naive apply would have half-installed and reported a result proving
> nothing — the vacuous-apply form the sweep exists to detect, caught on the
> sweep's own tooling. `git status` after the abort showed the file fully
> restored.
>
> **(two defects fixed, neither found by the sweep — both by grounding the
> closeout.)** (a) The scope note in `tests/handoffs/test_settings_hook_wiring.py`
> had been stale on **four** counts since the s179 D4(a) withdrawal: it still
> claimed part (ii) is "delivered by Step 4", that Step 4 registers the event
> after a live schema probe, that its `settings.json` diff carries its own
> Cray per-diff approval, and that "AC-1 closes when Step 4 adds it" — AC-1
> was already closed with (ii) withdrawn. Its header also read "Step 1 of 4"
> for a 6-step PLAN. Rewritten to withdrawn-on-evidence while **keeping the
> module's anti-vacuity argument intact**. (b) The `L1_DOC_THRESHOLD`
> citation **drifted a second time** (the `LOOP_TRIGGER_THRESHOLD` pointer has
> been right since s179). The **values 6 and 15 stay byte-identical at every
> re-measure** — the invariant has held each time; only the pointer moves.
>
> **(what is still OWED, and was deliberately not forced.)** The `git mv` to
> `docs/plans/done/` stays gated on a **Cray-confirmed live-loop soak** — it
> cannot be self-served, because the guards run on Cray's own working loop;
> the PLAN §Verification **live-check (ii)** (one deliberate warn-crossing on
> a scratch file) is **still unrun**; and **OQ-4 is OPEN with a dated
> commitment** (re-measure after ~20 sessions; a Cowork-drafted ADR-013
> amendment retiring L1 if true positives stay 0 with ≥1 false positive).
> Step 6 now records that OQ-4 must be **re-homed in whatever change finally
> archives this PLAN**, never buried in `done/`. Both live checks are
> *evidence*, not gates on AC-10 — which is why the PLAN closes out while
> staying in `docs/plans/`. _[s183, **`superseded by new info`** — not an
> error: this paragraph was true when written for #944, and **#945 ran
> live-check (ii) later the same session** (PASSED). The soak was then
> released by Cray at s183 and the PLAN is now **archived to `done/`**. The
> paragraph is annotated rather than rewritten because it correctly records
> what s182 knew at its reconcile.]_ Merge-commit re-run performed;
> `git diff 6726b69 HEAD` = **0 bytes**.

> **Session 181, 2026-07-28 (head_commit `767d520` → `85efe52`) — the session
> the constitution got a third lighter and no rule changed. One PR merged
> (#941), 0 open. CLAUDE.md full slim: the **11.1 KB footer changelog — ONE
> physical line, 33.6% of the file — retired to git history** under a NEW
> convention; §6 compressed; **277 → 261 lines / 33,014 → 21,524 B
> (−35.2%)** — ~2.8k tokens returned to every session.**
>
> **(the trigger was behavioral; the diagnosis was measured.)** Cray observed
> inconsistent instruction-following. A 2026-07-28 research pass against the
> official guidance (target < 200 lines; "bloated CLAUDE.md files cause
> Claude to ignore your actual instructions"; ❌-exclude "information that
> changes frequently") identified the footer as the anomaly — one physical
> line of 11,104 B, exactly the frequently-changing class the guidance
> excludes.
>
> **(the safety condition ran BEFORE the cut.)** Cray attached a coverage
> verification as a precondition: every footer entry diffed against its
> edit's full commit message (20 commits to scaffold) — every commit body ≥
> the footer entry, and every companion artifact (Lessons
> #0007/#0010/#0011/#0026/#0027, ADR-009/012/013/0017/0018/0032, the ms-s1
> runbook + skills) exists on disk. The footer was a strict summary layer
> over git history; retiring it loses nothing. The NEW convention: a
> constitutional edit bumps the footer date ONLY — the edit's commit message
> is the full record, and `git log --follow -- CLAUDE.md` is the amendment
> history.
>
> **(routing + R2 — five flags, five rulings.)** Cowork drafted (ADR-009 D1,
> cloud session, K-2 delivery); Code R2'd with a one-for-one E2
> six-commitment checklist, a binding-rule substance diff, and arithmetic
> verification, then ruled the returned flags: **α ACCEPT** (Decision + Plan
> Flows merged into one "Governance Artifact Flow"; 8/8 facts verified),
> **β ACCEPT** (the ADR-013 T4 sentence dropped — canonical in ADR-013),
> **γ ACCEPT** (the D2 hook-fact stated once), **δ APPLIED** (Lesson #0027
> linkified), **ε KEEP** (the tier table is the single in-file ADR-009 D1/D2
> statement). Cray ratified the wording + the rulings via AskUserQuestion.
> **No binding rule's substance changed** — verified hunk-by-hunk: 9 hunks,
> all inside the §6 span + the footer.
>
> **(the LOCKED target was unreachable — and the drafter said so.)** Cowork
> flagged per stop-and-flag, and Code verified the arithmetic: the
> < 200-line LOCKED target cannot be met in LOCKED scope — outside-§6 alone
> is 194 lines. Cray ruled option **(b)**: the target restates as **< 20 KB**
> (now 21.5 KB) and a follow-up extraction pass is queued (new Active TODO).
>
> **State at close:** `main` `85efe52`, 0 open PRs. Gate: pytest **3327
> passed / 8 skipped**, mypy clean (110 files), ruff clean on the tracked
> tree, CI `gate` PASS. Restart-bridge filed:
> `.claude/handoffs/session-181/2026-07-28-1027-code-session181-restart-bridge.md`
> — running sessions hold the pre-edit CLAUDE.md until Claude Desktop
> restarts. The two standing CLAUDE.md defect TODOs both SURVIVED the slim
> (re-verified on disk this reconcile): the dead `docs/conventions/git.md`
> link shifted `:176` → `:160`, the stale plan-drafter gate claim now sits
> at `CLAUDE.md:112` — line refs updated in their Active TODO rows.

> **Session 180, 2026-07-28 (head_commit `bc7be51` → `767d520`) — the session
> L1 stopped counting touches and started counting non-progress, and the
> question of whether L1 should exist at all got a measured baseline. Three PRs
> merged (#937, #938, #939), **0 open**. **PLAN-0094 Step 4 COMPLETE** (AC-7,
> AC-8(i)/(iii), AC-11); **OQ-4 opened** with a pre-committed retirement
> criterion; suite 3318 → **3327**. Only Step 6 (closeout, AC-10) remains.**
>
> **(#937 — the unit changed.)** `_handle_write_or_edit` used to increment on
> every Write/Edit, so six distinct forward edits of one file were
> indistinguishable from six retries of one broken change. It now increments
> only on **(b)** a re-applied `old_string` (`repeat xN`) or **(c)** the file
> returning to content it already held this turn (`osc xN`); a distinct forward
> edit is recorded via `observe()` with `result == ""`. `clear_turn_scoped()` is
> wired into the turn boundary. The measurement that makes this real: **all
> three L1 warns ever recorded would not fire under the new unit.**
>
> **(The s179 BLOCKING item was settled WITHOUT the probe it had staged.)**
> s179 closed planning to register a payload-dump hook and **restart the
> session** to learn whether `Edit`'s `tool_response` could supply a hermetic
> digest for (c). Answered instead from **84 recorded `Edit` results** in
> existing transcripts: an `Edit` result carries **no `content` key at all**,
> `originalFile` was null in **78 of 84**, and `structuredPatch` holds 1–2
> hunks — a diff, not a state. Nothing reconstructs the post-edit file, so the
> PLAN's on-disk hash stood unchanged. **The probe was never run; no restart was
> spent.** Corroboration for reading transcripts as a proxy for live payloads:
> the `Write` keyset measured this way matches the `Write` hook payload measured
> live in s179, key for key.
>
> **(#938 — two PLAN corrections, both measured, not inferred.)** The recorded
> result is ASCII `repeat xN`, not `repeat×N` — **seven sites** carried the
> multiplication sign **including AC-8's assertion text**, which is a
> pre-committed pass/fail read, so a test written to the PLAN as it stood could
> not have linted clean (ruff `RUF001`, measured directly). And (c)'s on-disk
> digest is now **grounded rather than defaulted**.
>
> **(OQ-4 — Cray asked whether L1 should exist at all.)** Baseline measured
> across **all 113 session transcripts, 2026-06-27 → 2026-07-27: 0 denies, 3
> warns, 0 true positives.** Two readings recorded: all three warns landed on
> exactly the *old* deny bar, so without P2's grace budget they would have been
> three hard walls during the month's most concentrated build work — the
> false-positive rate is **not flat, it climbs with how much work concentrates
> on single files**; and the guard **cannot catch the s169 incident that
> motivated it**. Not retired on the spot because the *marginal* cost of
> finishing was below the cost of retiring (an ADR-013 amendment plus deleting
> the test surface, against AC-7 on top of a state layer already merged), and a
> deleted detector cannot be measured. **Pre-committed criterion: re-measure
> after ~20 sessions; if true positives are still 0 and there is ≥1 false
> positive, dispatch Cowork to draft the ADR-013 amendment retiring L1** —
> L2/L3/L4 already carry E.4 more faithfully, since E.4 says "the same
> *problem*" while L1 keys only on "the same *file*".
>
> **(#939 — AC-11, and a spec that contradicted itself.)** (i) asked the deny
> body for "the threshold actually applied" (T+G) while (ii) asked the warn body
> for "the same line" (fires at T). **Cray ruled for the deny bar in both**: the
> warn body reads `count: 6/9`, "six of the nine that wall". The observer reads
> its denominator through `l1_deny_threshold_for` — the same function the gate
> applies — which exists precisely so the two bars cannot drift across two hook
> processes.
>
> **Non-vacuity swept twice, 9 named mutations**, each restored from a `/tmp`
> copy, never `git checkout`. The two carrying the most weight: **M-A**
> (whole-feature revert) reddens all three Step-4 rows while **L2 and L4 stay
> green**, proving the blast radius is L1; and **N-D** rewords a shared line
> *unrelated to the count* and reddens **only** the mirror row, proving the
> mirror-invariance assertion stands on its own rather than re-testing the count
> line from a third angle. **Every merge commit was checked, not assumed** —
> `git diff <CI-verified-head> HEAD` was **0 bytes** all three times, closing the
> PR-only-CI hazard by evidence.
>
> **State at close:** `main` `767d520`, suite **3327 passed / 8 skipped** (+9),
> `tests/handoffs/` **710 passed** re-run on the merge commit. 0 open PRs.
> `.claude/state/goal.json` **CLEARED this session** — it had been armed with
> the COMPLETED PLAN-0095 goal since s177, five sessions, and was carried
> unactioned in three prior blocks. Owed and unrun: the PLAN §Verification
> live-check (ii) — one deliberate warn-crossing on a scratch file, to confirm
> the advisory reaches the agent's context — and a Cray-confirmed live-loop
> soak, both gating Step 6.

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
| 2026-07-28 | **s183 — PLAN-0094 ARCHIVED (Cray released the soak), and the goal-gate `evaluations: 0` finding DIAGNOSED: the gate is not broken, its warn path is unobservable.** Cray reported **no anomalies** on the live loop since Step 4 (s180) — the one thing no session can self-serve — discharging the §Step 6 gate on the `git mv`; **OQ-4 re-homed to an Active TODO in the same change**, never buried in `done/`. The `evaluations: 0` diagnosis rests on four fresh measurements: `save_goal()` writes with `sort_keys=True` while the on-disk key order is **not** alphabetical ⇒ **it never wrote the file**; an offline replay of `run_goal_gate({})` against a `CLAUDE_GOAL_PATH` **copy** dispatched and wrote (`evaluations 0 → 1`) ⇒ **the mechanism works today**; C1–C4 run in **32 s** against the harness's **180 s** kill ⇒ **timeout refuted**; and `_goal_gate.py:440-446` shows `_failing_consequence` under `enforce: false` pinging Telegram and returning `None` with **no `record_evaluation` / `save_goal`**, which *any* failing check reaches (`:491-494`) — and s182's 18-mutation sweep made C1 red by construction on every mutated Stop. **The behaviour is ratified ("v1 — the stop fires"), so changing it is an ADR-0018 question, not a patch** — recommendation logged, not applied. Plus **five stale STATUS sites** corrected (`live-check (ii)` "still unrun" — including a `next_action` that directed a re-run of already-passed work) and the PLAN-0036 pre-archive pointer | `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md` §Step 6 + §OQ-4 / `.claude/hooks/_goal_gate.py:440-446,491-494` / `.claude/hooks/stop_continuation.py:600` |
| 2026-07-28 | **s182 — PLAN-0094 Step 6 executed, AC-10 CLOSED (#943): all 11 ACs closed or withdrawn, on a FULL FRESH 18/18 non-vacuity sweep** — Cray typed the full re-sweep rather than citing the recorded s177/s180 runs. 11 PLAN-named mutations + **7 derived** for the ACs that name none; **`missing_red` EMPTY for all 18**; sibling L2/L3/L4 invariance held. Applied by a harness script, not the Edit tool (the mutated files are the session's own live hooks). **M-A's blast radius is 8 L1 rows, not the 3 first predicted** — the session's prediction was too narrow; the PLAN's L2/L4-stay-green claim is `confirmed — prior intact`. AC-4 also reddens AC-11(i) — a FEATURE. Two stale-doc defects fixed. **The `git mv` to `done/` stays Cray-gated** (live-loop soak + live-check (ii)); OQ-4 OPEN | `1d0649f` (#943 merge, head_commit) / `6726b69` / `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md` §Step 6 |
| 2026-07-28 | **s181 — CLAUDE.md full slim (#941): the 11.1 KB footer changelog RETIRED to git history; 277 → 261 lines / 33,014 → 21,524 B (−35.2%).** NEW convention: a constitutional edit bumps the footer date only — the edit's commit message is the full record; `git log --follow -- CLAUDE.md` = amendment history. Coverage verified BEFORE the cut (20 commit bodies ≥ their footer entries; companion artifacts on disk). No binding rule's substance changed (9 hunks, all §6 + footer). The <200-line LOCKED target unreachable (outside-§6 = 194 lines) → Cray ruled (b): target <20 KB + follow-up extraction pass queued | `85efe52` (#941 merge, head_commit) / `8ffd290` / `CLAUDE.md` + `.claude/handoffs/session-181/` |
| 2026-07-28 | **s180 — PLAN-0094 Step 4 COMPLETE (#937/#938/#939): L1 counts NON-PROGRESS, not touches. AC-7, AC-8(i)/(iii), AC-11 closed.** L1 increments only on a re-applied `old_string` (`repeat xN`) or a return to content already held this turn (`osc xN`); forward edits record `result == ""`; `clear_turn_scoped()` wired into the turn boundary. **All three L1 warns ever recorded would not fire under the new unit.** s179's BLOCKING `tool_response` probe was **answered without being run** (84 recorded `Edit` results: no `content` key, `originalFile` null in 78/84, `structuredPatch` = a diff not a state) — the PLAN's on-disk hash stands, no restart spent. **AC-11: `T` = the DENY bar in BOTH Telegram bodies** (Cray's ruling on a self-contradicting spec). **OQ-4 OPENED — should L1 exist at all?** Baseline over all 113 transcripts: **0 denies, 3 warns, 0 true positives**. **Pre-committed: re-measure after ~20 sessions; TPs still 0 with ≥1 FP → dispatch Cowork to draft the ADR-013 amendment retiring L1.** Suite 3318 → **3327** | `767d520` (#939 merge, head_commit) / `2b9cb6f` / `053410a` (#938) / `0a85b21` (#937) / `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md` §D4 + §OQ-4 |
| 2026-07-27 | **s179 — PLAN-0094 Step 4 RE-SCOPED on its own probe's refutation (#933); OQ-3 opened + RESOLVED same session.** Measured twice, one session apart: **a failed `Edit` invokes NO hook** — not `PostToolUseFailure`, not `PostToolUse`. **D4(a) withdrawn**, taking **AC-1(ii) / AC-6 / AC-8(ii)** with it (AC-6 withdrawn, not weakened) and with them Step 4's only Cray-gated `settings.json` surface; the s169-class thrash stays **uncountable**. OQ-3 → (b), four rulings: **R1** a self-contained COUNT, not a sha1 pointer (evidence ring 6 vs doc trip bar 15); **R2** `dict[str,int]`; **R3** `result == ""` on forward edits; **R4** → new **AC-11** (Telegram `count: N/T` + formatter mirror-invariance) | `b3c20dd` / `bde43d6` (#933) / `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md` §D4 + §OQ-3 |
| 2026-07-27 | **s179 — `main` was RED for three hours and PR-only CI structurally could not see it (#934): the tests EXPIRED, they did not regress.** `_seed_ack` hardcoded a `last_updated`; `load_counter`'s `prune_stale_entries` drops entries past `COUNTER_MAX_AGE_HOURS` (6 h) — green at merge, red hours later. `git diff 25239f3 490f09e` was **EMPTY**: same tree, opposite verdict. Proved with zero code edits (`CLAUDE_LOOP_COUNTER_MAX_AGE_HOURS=100000`). Fix stamps from `_now_iso()` + adds `test_seed_ack_is_stamped_live`, a guard that **tests the FIXTURE** so a future re-hardcode fails at the cause. Suite 3317 → **3318** | `35851f2` (#934) / `bc7be51` (head_commit) / `a5dacb0` (#935, OPEN — Step 4 state layer) |
| 2026-07-27 | **s177 — PLAN-0094 Step 5 BUILT (#930): `awaiting_ack`, the L1 exit an agent cannot fake. AC-9 closed.** When L1 denies, all three documented exits can be shut at once — sticky turn boundary, a commit needing a tree the gated file itself blocks, a subagent reset scoped to the subagent's own edits — which is why **2 of 5 recorded incidents ended in a Cray-authorised shell escape**. The deny branch now arms the marker (that gate becomes a **narrow state writer**) and the Stop hook clears it **only where the stop actually fires** (cap / contentless demotion / dispatch suggestion / pause), never on `proceed`, a goal-gate directive, or re-entry. Also **overrides the sticky rule** for armed targets → two-turn recovery becomes one. **Landed ahead of Step 4 deliberately** (Step 4 is gated on a Cray per-diff `settings.json` approval; no step depends on a later one) — surfaced, not assumed. Key finding the RED-first run forced: a negative row went RED because the turn-boundary reset rewrites the whole document, so **additive-and-tolerant was necessary but not sufficient — additive-and-SERIALIZED is the requirement**. 11 rows, **8 RED-first**; the 3 negative rows proven by named mutations (scratchpad restore, never `git checkout`). Thresholds byte-unchanged. **Live demo, unplanned:** the L1 warn fired on `stop_continuation.py` *while it was being fixed* — 6 distinct forward edits, zero retries = exactly the false-positive class Step 4 exists to kill. Plus **#931**: Cray enabled Docker Desktop's WSL integration (Code declined to flip it itself and said why — `RestartPolicy=no` meant an unasked-for downtime; the prediction held exactly), runbook §1a converts to bash with the build **re-verified from WSL**. Suite 3306 → **3317** | `da0b50b` (#931 merge, head_commit) / `387bef0` / `2736acf` (#930 merge) / `c076f7a` / `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md` §D5 |
| 2026-07-27 | **s177 — PLAN-0095 COMPLETE 7/7, archived to `done/`: the image builds and boots for the first time since the 2026-05-07 scaffold commit.** #927 lands Steps 1–5 as ONE PR (the oracle is born-RED, so splitting lands a red suite): builder defects **eliminated not repaired** (`--no-install-project`), `python -m uvicorn` for a guaranteed import path, `alembic/` shipped per SD-2, a thin compose `app` consumer per SD-1. The oracle **derives** its COPY set by transitive closure from the app root — born-RED with **5 assertion families**, **12/12 mutations bit** (M-C goes RED with *no Dockerfile edit*), derived set measured exactly `['services','verticals']`. AC-3 ships as a **sibling test**, not the PLAN's reviewer-grep (Cray's call). #928 adds runbook §1a. **Step 6 live, on Cray's go:** build exit 0, `/health` 200 in ~2 s, all six verticals in the boot log, `uid=999(vero)`, HEALTHCHECK `healthy`, `alembic current` → **`0012 (head)` from inside the image**. **OQ-2 residual + OQ-3 RESOLVED; OQ-1 (hosting model) open by design.** Two PLAN departures, both evidence-backed: no `docker compose down` and `--no-deps`, because `vero-postgres`/`vero-redis` were **up 7 days** and §1 depends on them — `StartedAt` byte-identical before/after. Two self-caught errors: the oracle's URL extraction (found by reading, one step before a false RED) and a mis-aimed M-D that hit a **comment** not the `RUN` line — oracle logged `confirmed — prior intact`. Finding, reported not fixed: **Docker Desktop's WSL integration is OFF** for `ubuntu-24.04`, so runbook §1's own `docker ps` precondition fails from WSL today. Suite 3296 → **3306** | `8618081` (#928 merge, head_commit) / `54f0189` / `6ab2c28` (#927 merge) / `fb0e1f8` / `docs/plans/done/0095-docker-image-boot.md` + `tests/docker/test_dockerfile_oracle.py` |
| 2026-07-27 | **s176 — PLAN-0095 merged as Draft (#925): make the Docker image build + boot the DB-less OCT demo. Nothing built; Steps 1–5 unexecuted.** The grounding sweep (4 Explore agents, 15 items) killed **5 wrong s175-handoff premises** — the first-order boot failure is a plain import (`discovery.py:45`, uncaught at `main.py:166`), **not** the CWD-relative `Path("verticals")`; plus an uncounted **9th** defect (`pyproject.toml:7` `readme` never COPY'd). Cray ruled **SD-1 = both**, **SD-2 = include `alembic/` + document**, **SD-3 = all four** — reframing the PLAN as *ready for development toward production*; SD-1/SD-2 overturned the drafter and are logged `superseded by new info`. Oracle derives the COPY set by **transitive closure from the app root** (not a `verticals` glob — that would break AC-3); **AC-6: no AC needs a Docker daemon**. Finding: **CLAUDE.md §6's plan-drafter gate claim is STALE** — the subagent is exempt by design (`pretooluse_classifier_dispatch.py:301-311`), G2 preserved for Code | `77fa734` (#925 merge, head_commit) / `2fb8709` / `docs/plans/done/0095-docker-image-boot.md` |
| 2026-07-26 | **s175 — the harness stopped letting a failed command look like a success.** #923: Lesson #0007's mechanism CORRECTED and reclassified `was an error` (a bare `$` expands one shell layer early; `$?` is not unreadable) + a binding CLAUDE.md §8 rule + a `_shell_hygiene_warning` PostToolUse advisory. #922: PLAN-0094 **Step 3** — warn at T, deny at T+G (9 code / 18 doc), L4 flat 6; AC-3/4/5 closed. #920 pins all six verticals' ACTION factory offline at REGISTRATION; #921 fixes four stale cross-refs. **Cray: demo target = the LIVE-API shape** → Candidate C is the long pole. ADR-009 D1 one-off Code-authors-§8 exception — **not precedent**. Suite 3252 → **3296** | `04c94e4` (#923 merge, head_commit) / `3b3b666` (#922) / `59c81a6` (#921) / `65c6953` (#920) / `docs/lessons/0007-harness-exit-code-artifact.md` |

## In-Flight Discussions

- **PLAN-0095 — COMPLETE 7/7 and ARCHIVED (s177, #927/#928).** The scaffold-era `Dockerfile` builds and boots the DB-less synthetic OCT demo: `/health` 200 in ~2 s, all six verticals discovered, `uid=999(vero)`, `HEALTHCHECK` healthy, and `alembic current` → `0012 (head)` from inside the image. The only thing still open from it is **OQ-1, the hosting model** — already homed in the next bullet, not restated here. Full record: `docs/plans/done/0095-docker-image-boot.md`. _[Corrected s182, `was an error`: this entry still described the PLAN as Draft with "Steps 1–5 UNEXECUTED … the image does not boot today" and cited the pre-archive path — refuted by the s177 row in Recent Decisions above and by the archived PLAN's own `Status: Complete`.]_
- **Hosting model → ADR-002's LAN trust boundary: a LIVE candidate needing its own ADR (surfaced s176, still not drafted; this is where PLAN-0095's OQ-1 lives).** *"Customer uses our server"* touches ADR-002's LAN trust model — `docs/adr/0002-network-topology.md` defers its own successor **twice** as an unnumbered `ADR-NN`: in **§Consequences → Neutral** (the LAN trust assumption is to be re-evaluated when a first design partner deploys to a real site) and in **§Alternatives Considered → Alternative 3** (Tailscale / WireGuard, to be reconsidered when remote development or design-partner site connectivity becomes a need). Nothing in the image or the compose service selects *where* the image runs, so the question only bites when a hosting model is actually chosen. Route: a new ADR via the Cowork/plan-drafter path (G1/G2 — Code may not author it). _[s182: the two line-number citations here were **dropped, not corrected** — one of them had already rotted onto a PDPA bullet, which is the failure mode the rotation policy's R7 rule names. Cite the ADR's section headings; they survive an edit, line numbers do not.]_
- **PLAN-0094 — COMPLETE (all 11 ACs closed or withdrawn) and ARCHIVED (s183).** The L1 loop-detect restructure: count non-progress instead of touches (P1), warn at `T` and deny at `T+G` (P2, `G=3` → 9 code / 18 doc), add an acknowledged-pause exit the agent cannot fake (P3), and wire the `SubagentStop` reset that had **never been live**, scoped per-`agent_id` so a zero-edit spawn cannot launder the main agent's budget (F3c). Built across s174 #917, s175 #922, s177 #930, s180 #937/#939, closed out s182 #943 on a **full fresh 18/18 non-vacuity sweep**. Archived at s183 once **Cray released the live-loop soak** (no anomalies) — the one gate no session could self-serve. **The one thing that did NOT archive with it: `OQ-4` (should L1 exist at all?) is OPEN and dated — re-homed to an Active TODO below**, per the PLAN's own §Step 6 instruction never to bury it in `done/`. Full record: `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md`; the anti-pattern behind it: `docs/lessons/0033-raising-the-threshold-is-not-fixing-the-unit.md`.
- **PLAN-0093 — COMPLETE 8/8 and ARCHIVED (s172, #913).** The LLM-arm degrade disclosure — no silent arm swap: which arm phrased an NL answer is disclosed, the rule fail-safe says it is a fail-safe, the authoring arm is projected over HTTP (including the insights run-corpus path), and `LLM_RETRY_BUDGET` no longer sits inert on the governed path. No follow-on owed. Full record: `docs/plans/done/0093-llm-arm-degrade-disclosure.md`.
- **PLAN-0091 — COMPLETE 10/10 and ARCHIVED (s168).** Two follow-ons it named, **neither scheduled**: the **extend shapes** (calm-path + scheduled-variant scaffolding) are **greenfield, not an extension** — the shipped emitters refuse an existing vertical *by construction* and create-only is Cray-ratified SD-2, so this needs a fresh seam spec, not effort; and the census-narrative comment in `tests/api/test_procedures_endpoint.py` is the one counted site the disposer REPORTS rather than rewrites — a human call, left visible on purpose. Full record: `docs/plans/done/0091-narrative-to-vertical-scaffolder-tool.md`.
- **PLAN-0088 — COMPLETE (13/13 live ACs) and ARCHIVED (s171, #908).** The cross-run read substrate + the four run-insight readers (A2 ฿ ROI, A3 flow, A4 audit-readiness, A1 NL-over-runs) + the Group-B carrier proof. SD-1…SD-9 all Cray-ratified; the substrate stays aggregate-only (SD-8 a) and grows only in `run_analytics.py` (SD-9 a2); Group A ungated, Group B pilot-gated (AC-10 proves the questions expressible, AC-11 that no proposal machinery exists). AC-9b's live MS-S1 smoke PASSED. **Three AC-WORDING debts carried into the archived PLAN, none a code defect** (Cray's to reword if ever): (1) AC-2 names the wrong approver source — the approver is in the trace / `governed_decision` / audit-log, not `step_principals` (the requester half); (2) AC-6's "dwell" is a same-row start→suspension span, stated plainly in the code; (3) SD-9's aside miscalls `trigger` "undefined". Full record: `docs/plans/done/0088-cross-run-read-substrate-and-run-insight-readers.md`.
- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13; verdict **continue-with-adjustments**. Runs 1 (energy, s93) + 2 (supply-chain, s94) both COMPLETE, all S-checks PASS against pre-committed oracles, no R-PS trigger fired; C-1..C-3 CONFIRMED → **no open partner-sim debt**. ADR-011's audit stays gated on a REAL partner conversation (R3: SYNTHETIC provenance INFORMS but never TRIGGERS it). Full record: `docs/adr/0020-*.md` + the gitignored run packages under `docs/research/private/`.
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **Procurement vertical — GO + SHIPPED (PLAN-0036 Fastenal, Stage 1):** 4th vertical greenlit (s75); **PLAN-0036 is `Status: Done` — Stage 1 complete 2026-06-25 (s76), all 8 Steps executed, AC-1…AC-15 satisfied offline — and Stage 2 (the facet retrofit it forward-declared) shipped as PLAN-0037.** Demo target = Fastenal Thailand; **hero** = asset-failure → governed emergency sourcing, **calm-path** = low-stock reorder. Stage 1 = a PLAN-only pure-config plugin on the ADR-016 engine (zero `services/` core edit; CQ-1 / ADR-0023). **Pitch** = asset-ontology-triggered governed sourcing (ADR-008 + ADR-016), NOT the commoditized "governed"/"cross-vertical" claims. Full record: `docs/plans/done/0036-fastenal-procurement-vertical.md` + `done/0037-stage2-facet-retrofit-archetype-catalog.md` + the s72 de-risk dossier under `docs/research/private/`. _[Corrected s183, `was an error`: this entry pointed at the pre-archive path `docs/plans/0036-*.md` and described the PLAN as "merged Draft" long after it reached `done/` with `Status: Done` — the same stale-pointer class the s182 corrections were chasing.]_
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm — **not yet drafted**, and it needs a fresh ADR number. _[The old "≥ ADR-014" floor recorded here was **moot** — see the Active TODO below, corrected s141: ADRs now run past 0032 and `0014-WITHDRAWN.md` exists. Kept as one pointer rather than two divergent copies.]_
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **The autonomy fork — Stop-hook misfires: CLOSED s167.** Resolved by **option A′** (Cray, typed) and shipped the same session — the `dispatch` verdict is a **suggestion, not an order** (#870/#871). Final ledger: **14 misfires / 0 valid fires**. **The whole argument is settled history in `docs/plans/done/0092-stop-hook-dispatch-arm-demotion-to-suggestion.md` — do not restate it here.** Live remainder: only **option (e)** (flip the classifier backend from local Ollama `gpt-oss:20b` to Sonnet), **deferred**, its API-key/org fail-closed probe unrun.

## Active TODOs

- [ ] **The AT-2 extraction — only the F-FACTORY half remains, owned by PLAN-0076 T1.** The criterion-vocabulary half SHIPPED as PLAN-0087 (COMPLETE 8/8, ARCHIVED — #840/#841); ADR-0025 D7's generator deferral was CANCELLED at N=4 (Cray-ratified, typed); SD-1 = (a) keeps the procedure-aware `ExecutorFactory` half with PLAN-0076 T1, guard `test_at2_extraction_obligation_is_owned` ARMED. Full detail: `docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` + `docs/plans/0076-*.md` §A.
- [ ] **PLAN-0075 follow-ons — homed by PLAN-0076 (`Status: Tracking`, #752, s133).** T1 (ADR-0031 D3 gate-plugin seam, F-FACTORY) is PARTIALLY discharged — the criterion-vocabulary half shipped as PLAN-0087; the procedure-aware-`ExecutorFactory` half stays OPEN here. T2's F-PIN remainder CLOSED s143 (#784), but **F-PIN itself stays OPEN**, so PLAN-0076 does NOT archive and its AC-6 presence guard stays ARMED. Full detail: `docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` §A.
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2) — open ONLY for the O-2 residue.** Every other leg is DONE + archived (PLAN-0046/0048/0061/0062/0066–0068/0070/0071/0073 → `done/`). **The one OPEN residue:** procurement's `intake` migrated only **PARTIALLY** — the derived fields ALREADY moved to declared `transform` ✔ (PLAN-0078 PR-1 #762, AC-2 ticked), so what is left is **only the cardinality-changing `candidate_quotes` nest**, which is explicitly Out-of-Scope there. *[Corrected s175 by the #921 grounding sweep, `was an error`: this entry said production execution stays `_SeedQuery` "for derived fields" — it does not; the derived fields are migrated and the reshape is the sole residue.]* Full detail: `docs/plans/done/0062-per-vertical-seed-migration.md` §SD-C (the co-exist decision + its STOP-and-surface tripwire) + `done/0078-*.md` §L-3 and its Out-of-Scope, where the residue is walled in.
- [ ] **Bounded/incremental chain verification (PLAN-0063 SD-4 follow-up, s118).** `GET /audit/verify` walks the WHOLE chain O(n) on demand — accepted at pilot scale. Future work = a checkpointed head / verify-since-anchor design; anchor storage ≈ external anchoring — **do not build without re-reading the tripwire** in `docs/plans/done/0063-audit-chain-verification-surface.md` + the `services/api/routers/audit.py` module docstring (SD-4). _[Note: the docstring's "ADR-011 boundary" is an EARMARK — `docs/adr/` jumps 0010 → 0012.]_ *(#688/#690)*
- [ ] **DEFERRED: a monotonic `sequence` column on `step_results` — the ROOT fix for `load_run`'s wall-clock ordering.** Needs a DB migration → its own PLAN; none drafted, the deferral STANDS, both surviving orderings DISPLAY-ONLY. Full detail (ROOT-vs-guard, the AST guard, the un-defer trigger): the docstring of `tests/services/db/test_load_run_ordering_guard.py`. _[s169: the un-defer trigger got its FIRST real-case reading and did NOT fire — SD-8 = (a) ELIMINATE. This PLAN now also owns newest-first `/runs` pagination; `view-map.js` (a `CAP = 5` truncating consumer) is a second dependant.]_
- [ ] **Rock 4 — s84 deep research DELIVERED → O-sequence locked.** Cray locked **O-1 → O-3 → O-2 → O-4**. **O-1** (Box-4 ฿ pitch) **DONE** · **O-3 = ADR-0025 Accepted** · **O-4 = PARK** (agent-interop; `docs/adr/0032-*.md` D4 — option-only, un-park = a counterparty's *written* pull). **Remaining: O-2 only** (economic-impact facet + Q3 data-binding = Rock 3). Full detail: `docs/adr/0025-at2-managerial-layer.md` (O-sequence + Box-3 fit + the **evidence-asymmetry** finding rehomed s142). *(s84 Cray ask)*
- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten. **Full table (all six rows + their triggers + where each lands): `docs/plans/done/0005-oct-engine-runtime-layer.md` §8.1** — which itself instructs this STATUS entry to be a pointer. *(per Cray note 2026-05-21)*
- [x] **Demo card UX — "trust shape" — BUILT; closed s175 with at most one residue.** *[Closed by the #921 grounding sweep: this sat open as a design-to-build TODO long after it shipped.]* The s74 design (Cray-approved) is live on **both** operator surfaces — what / grounded-why / approve gate + a "show full reasoning trace" toggle (`story.css` `.gc-card.trace-open .gc-trace`), and **no confidence badge**: `confidence_signal` stays engine-internal QA/trace-only, pinned by anti-regression comments citing the PLAN-0035 §SD-3 amendment in `story.css`, `view-story.js` and `view-monitor.js` (the latter at `advisoryBlock`: "grounded REASONS, never a score … no confidence number renders on any operator surface"). SD-3 settled at (a) — the first-class `verification` field is NOT needed. **Residue:** at most one toggle on the monitor step card. Full record + rationale + the reconsider-trigger: the §SD-3 post-archival amendment in `docs/plans/done/0035-governed-action-verify-reshape-build.md`; `ADR-0030` cites it. *(Trigger for the residue: the next demo / UI round.)*
- [ ] **PLAN-004 Phase C — OPTIONAL POLISH (forward-declared; "may never land"):** HTML/markdown handoff dashboard under `docs/` + references-graph (mermaid dispatch chains) + `render_transcript.py` unified session export (PLAN-0004 §"Phase C"). *(Phase A + B both COMPLETE — session 35; the prior TODO's validator **warning-swallow bug was FIXED #312**, s58. Minor never-formally-scoped sub-ideas — README/`_rename-map` walk-exclusion, Cat G `references_*` autofix, OQ-2 effective-vs-authored `status:` dashboard flag — fold in only if Phase C lands. Reconciled 2026-06-16 s65 audit.)*
- [ ] **Custom Postgres image with extensions (pgvector / AGE / pg_trgm) — needs a fresh ADR number + a PLAN; neither drafted.** *[Corrected s141: **PLAN-002 does not exist** ("NOT yet drafted", `docs/plans/done/0005-oct-engine-runtime-layer.md`), and the old "≥ ADR-014" floor is **moot** — ADRs now run to 0032 and `0014-WITHDRAWN.md` exists.]* Context: **`docs/adr/0013-autonomy-axis-relocation.md`** (the floor-bump note) + **`docs/plans/done/0005-*.md`** (trigger: semantic + graph features).
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] **`docs/conventions/git.md` — substance DISCHARGED, one DEAD LINK left, and it needs Cowork.** *[De-duplicated s175: this TODO existed twice — here and as an In-Flight "Convention extraction" bullet; the In-Flight copy is dropped, this row is the single home.]* The extraction's substance is effectively discharged by the **`git-workflow` skill** (`.claude/skills/git-workflow/`, Tier 2.6), so the file may never need to exist. What DOES need fixing: **`CLAUDE.md:160` holds a dead relative link** *(shifted from `:176` by the s181 slim; re-verified on disk s181)* to the non-existent `docs/conventions/git.md` ("Future canonical: …"). Either extract the file or drop the link — and **either way it is a Cowork round-trip**, since Code may not author `CLAUDE.md` (ADR-009 D1; the s175 #923 exception was scoped to §8 only). *(low priority)*
- [ ] **`CLAUDE.md` §6's gate-route claim is STALE — needs a Cowork round-trip (found s176; SURVIVED the s181 slim verbatim, now `CLAUDE.md:112`; NOT fixed).** §6 "Mechanical overlay" says a new PLAN/ADR is PreToolUse-gated for Code **and the in-harness `plan-drafter`**. Measured: `.claude/hooks/pretooluse_classifier_dispatch.py:301-311` **exempts the `plan-drafter` subagent from the G2 classifier gate by design** (PLAN-0034 prong 2, SD-1(a)) — it short-circuits *before* the classifier, so it does not even depend on MS-S1 being warm. The main Code agent carries no `agent_id` and **is** still gated, so **G2's substance is preserved**; only the sentence is wrong. _[Sharpened s183 — the correction is **"gated by a different hook"**, NOT "ungated": `pretooluse_plan_subagent_write_deny.py` is an **allowlist** that affirmatively **permits** `docs/adr/*.md` + `docs/plans/*.md` for this subagent and denies everything else fail-closed. So `plan-drafter` is precisely the one actor for whom writing a new PLAN/ADR is *allowed by design*. Whoever drafts the CLAUDE.md fix should say that, not merely delete the clause.]_. Same round-trip class as the `CLAUDE.md:160` dead-link row above — Code may not author `CLAUDE.md` (ADR-009 D1; the s175 #923 exception was scoped to §8 only), so batch the two if convenient. *(low priority — a documentation defect, not a guard defect)*
- [ ] **CLAUDE.md follow-up extraction pass (s181 option b): new Cowork dispatch; target < 20 KB (~18 KB / ~225–235 line floor).** Candidates (Cowork fresh-eyes, s181 completion §6): §11 ¶3 restates the §6 E2 rule → one-line pointer; §10 skills-row annotation duplicates §4's Tier-2.6 row (in-file ADR-0017 D6 drift); §10 docs/logs row's PLAN-004 parenthetical; §9 halves; §3 folds into §1. Materials: `.claude/handoffs/session-181/` (gitignored). **PARKED s183 by Cray — the dispatch stays UNSENT until two things are settled, and s183 grounded both.** (1) **The unit of `< 20 KB` is load-bearing and unpinned:** `CLAUDE.md` measures **21,524 B / 261 lines**, so the target needs **1,044 B** cut against 20 KiB but **1,524 B** against decimal 20,000 — Cray was asked and declined to rule for now. (2) **The five named candidates cannot reach either target:** measured at **~930–1,000 B** combined, and the row's own "~225–235 line floor" needs **26–36 lines** removed where the five move **~7** (candidates 1–3 are in-line trims that shorten bytes without deleting lines). The genuinely large blocks — `CLAUDE.md:112` (~1,100 B), `:153` (~700 B), `:73` (~800 B) — are **not on the list**. Sending this dispatch as written would repeat the s181 failure of a target that is arithmetically unreachable in scope. **Batch the two standing CLAUDE.md defects into whatever dispatch eventually goes out** (the dead `docs/conventions/git.md` link and the stale plan-drafter gate claim — the two rows below).
- [ ] **OQ-4 — should L1 loop-detect exist at all? OPEN with a DATED, pre-committed criterion. RE-HOMED here s183 from PLAN-0094, which archived.** This row exists because the PLAN's own §Step 6 forbade carrying a live dated commitment into `done/`. **The criterion, unchanged:** re-measure after **~20 sessions** of the post-AC-7 guard (AC-7 closed s180) → **due ≈ s200**; if **true positives are still 0 and there is ≥ 1 false positive**, dispatch Cowork to draft an **ADR-013 amendment retiring L1**, noting that L2/L3/L4 already carry row E.4 more faithfully — they key on "the same *problem*" while L1 keys only on "the same *file*". **Baseline already banked (s180, all 113 transcripts 2026-06-27 → 07-27): 0 denies, 3 warns, 0 true positives**, and the guard cannot catch the s169 incident that motivated it. **Measurement method matters:** grep transcripts for `L1 warn on` **and both** deny wordings — searching only the current wording under-counts. Full reasoning: `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md` §OQ-4. *(Not due yet — premature re-measure burns the pre-commitment on an under-powered sample.)*
- [ ] **The goal gate's warn path records NOTHING — diagnosed s183, NOT fixed. Cray's call whether this becomes a PLAN.** Under `enforce: false` (the default posture) a failing `check` routes to `_failing_consequence`, which pings Telegram and returns `None` with **no `record_evaluation` and no `save_goal`** (`.claude/hooks/_goal_gate.py:440-446`); *any* failing check reaches it (`:491-494`), and `_goal_gate.py` carries **no logging at all**. So the gate's most frequently travelled branch — a red check mid-work — is its **only** branch that leaves no in-repo trail, and its sole signal leaves the machine and no-ops silently if `tools/notify/telegram.sh` is absent. **The mechanism is NOT broken** (offline replay of `run_goal_gate({})` against a `CLAUDE_GOAL_PATH` copy dispatched and wrote, `evaluations 0 → 1`), and **the behaviour is ratified** — `:437-439` calls it "v1 — the stop fires" and `stop_continuation.py:600` documents the fall-through — so **changing it is an ADR-0018 question routed through Cowork, not a Code patch**. **Recommendation:** worth a small PLAN *if* the Axis-B loop is meant to be auditable after the fact; the cheapest shape is a trail entry on the warn path (no consequence change), which is still a recorded-state change and therefore still gated. **Evidence, if this is picked up:** the s182 `goal.json` sat `status: active` / `evaluations: 0` all session, and the decisive forensic is that `save_goal()` serializes with `sort_keys=True` while the on-disk key order was never alphabetical — it had never written the file. *(Related: `.claude/state/goal.json` still holds the COMPLETED s182 PLAN-0094 goal; it was kept as this finding's evidence and can be cleared once the finding is ruled on.)*
- [ ] **STATUS rotation-window slack (runbook R2) — OPEN, Cray's call; untouched s180.** The 4-session / 8-block Current Focus window and the file's byte ceiling now bind at the same time: this reconcile rotated the s175 block out to make room and wrote the s180 block to a byte budget rather than to what the session warranted. Widen the window, tighten the per-block cap, or accept the trade — a Cray decision. Policy home: the R1–R7 rotation policy in `docs/runbooks/memory-architecture.md` (Lesson #23).
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
