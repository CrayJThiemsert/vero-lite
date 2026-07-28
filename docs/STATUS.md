---
last_updated: 2026-07-28T10:27:38+07:00
session: 181
current_batch: "s181 — 1 PR merged (#941), 0 open: CLAUDE.md full slim — 11.1 KB footer changelog retired to git history, §6 compressed; 277 -> 261 lines / 33,014 -> 21,524 B (-35.2%)."
current_actor: code
blocked_on: "Nothing blocking. PLAN-0094 Step 6 (closeout, AC-10) is all that remains; it needs a Cray-confirmed live-loop soak + the PLAN §Verification live-check (ii), both unrun."
next_action: "Restart Claude Desktop so sessions load the slimmed CLAUDE.md (restart-bridge in .claude/handoffs/session-181/), then the CLAUDE.md follow-up extraction dispatch (<20 KB) or PLAN-0094 Step 6."
head_commit: 85efe52
recent_commits: [85efe52, 8ffd290, 767d520, 2b9cb6f, 053410a, 02db847, 0a85b21, 309168e, bc7be51, fd31ba9]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

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

> **Session 179, 2026-07-27 (head_commit `da0b50b` → `bc7be51`) — the session
> probe-first paid for itself twice: Step 4's own gate refuted the premise Step
> 4 was designed on, and a suite that was green at merge turned `main` RED three
> hours later with nobody watching. Two PRs merged (#933, #934), **#935 open**.
> **D4(a) withdrawn**; **OQ-3 opened and RESOLVED same-session**; suite 3317 →
> **3318**. (No session 178 entry — s178 committed nothing.)**
>
> **(#933 — the refutation, and what it cost.)** Step 4's probe-before-build
> gate came back negative: **a failed `Edit` invokes NO hook in this harness
> build** — not `PostToolUseFailure` (the s173 bundle-extracted claim), and not
> `PostToolUse` either. Two independent measurements one session apart: s173's
> live `PostToolUse` observer, and an s179 payload-dump probe registered on
> **both** events at once, so one run covered both. **The control is what made
> it readable** — the successful `Write` dumped with `tool_response` present and
> no `error` key, while the failing `Edit` dumped nothing at all; without a
> known-good event in the same run, "no dump" is indistinguishable from "the
> config never reloaded". Registrations are snapshotted at session start
> (measured s178), so the probe had to be staged uncommitted and armed by a
> restart. Consequence: **D4(a) withdrawn**, and **AC-1(ii), AC-6, AC-8(ii)**
> with it — AC-6 **withdrawn rather than weakened**, since greening it would
> mean feeding a synthetic payload straight into `main()`, the exact "green
> tests over dead wiring" class AC-1 exists to kill. Step 4 thereby **LOST its
> Cray per-diff `settings.json` gate** (removing (a) removed the only gated
> surface), and the s169-class thrash — retrying one broken `old_string` —
> **stays uncountable**; §Goal is corrected to say P1 now delivers only the
> stop-miscounting-forward-progress half. Per §6: the s173 *schema claim* was
> **`was an error`** (a bundle-extracted schema reported as if it established
> runtime behaviour, single-source, self-labelled "not live-observed"); the
> *decision* to design D4(a) on it was **`superseded by new info`** — which is
> exactly why Step 4 was written probe-first.
> **(OQ-3 — opened and ruled the same session.)** D4(a) was the only planned
> writer of `ActionRecord.result`. Cray took option (b) and ratified: **R1** a
> self-contained COUNT (`repeat xN` / `osc xN`), NOT the drafted
> `repeat:<sha1[:8]>` — grounding disqualified the pointer, since the evidence
> ring is **6** deep (`_loop_counter.py:89`) while the doc trip bar is **15**
> (`:100`), so the partner row a sha1 names has almost always aged out; **R2**
> `attempted_edits`/`content_hashes` become `dict[str,int]` (a set cannot carry
> N); **R3** forward edits keep `result == ""`, since both formatters bracket
> `result` only when non-empty — **the bracket's presence IS the signal**;
> **R4** a `count: N/T` line in both Telegram bodies, raised as out-of-scope and
> **pulled in by Cray as new AC-11**, which also pins mirror-invariance between
> the two formatters (the observer docstring claimed it; nothing enforced it).
> Ruled out and recorded: the literal `old_string` text in `result` — it reaches
> `telegram.sh` and leaves the machine, and the formatters truncate
> `target[:60]` but not `result`. Plus 4 drifted line citations corrected, one
> in a row the PLAN's own drift table had marked "exact"
> (`_loop_counter.py:84,96` → `:88,100`; threshold VALUES `6`/`15` identical).
>
> **(#934 — `main` had been RED since 06:00Z and nobody knew.)** Two rows of the
> Step 5 block failed — **not a regression; the tests expired.** `_seed_ack`
> hardcoded `last_updated: "2026-07-27T00:00:00+0000"`, but `load_counter` runs
> `prune_stale_entries`, which drops entries older than `COUNTER_MAX_AGE_HOURS`
> (6 h) — so the seed survived only inside a six-hour window of the day it was
> written. **The diagnosis chain is the reusable part:** the same two rows
> failed on `main` at `490f09e` (2 failed / 62 passed), and `git diff 25239f3
> 490f09e` was **EMPTY** — the tree CI passed at ~05:16Z is byte-identical to
> the tree failing at 09:13Z, and every prior PR run was green at its own head,
> so **nobody merged a red PR: the tests aged out AFTER merge**, which PR-only
> CI structurally cannot see. The `main`-is-never-tested hazard, firing for
> real. Proof with **zero code edits**:
> `CLAUDE_LOOP_COUNTER_MAX_AGE_HOURS=100000` turned the file green. Fix: stamp
> from `_now_iso()` (the helper the production writer already uses) +
> `test_seed_ack_is_stamped_live`, a guard asserting the seeded entry survives a
> real `load_counter` — **deliberately testing the FIXTURE** so a future
> hardcode fails where the cause is. Non-vacuity: M-1 (re-hardcode) reddens the
> guard + both original rows; M-2 (early `return` in `_ack_clear_guarded`)
> reddens 4 rows; both restored from `/tmp`, never `git checkout`. Noted while
> the bomb was live: the fired-pause row's `assert not entry_present` was being
> satisfied by the **age-out**, not the clear (`prune_stale_entries` never
> touches `awaiting_ack`) — but its `marker == []` half kept testing real
> behaviour, so the row was **never fully vacuous**. Suite 3317 → **3318**.
>
> **(#935 — OPEN, the state layer alone.)** `feat(hooks)` `a5dacb0` lands Step
> 4's **state layer** by itself so the behaviour change reviews separately —
> **no hook behaviour changes yet**; thresholds and `pyproject.toml`
> byte-identical to `main`. Two decisions worth carrying: `_digest_tally`
> **drops** malformed members rather than coercing (a corrupt tally must not
> manufacture an increment), and the new record-only `observe()` shares one
> `_record()` body with `increment()` so evidence cannot drift between the
> counting and non-counting paths. One **reversal**: the first draft spelled
> `result` with `×`, ruff RUF001 rejected it, and the fix briefly widened
> `allowed-confusables` — reverted, since R1 ratified a **count, not a glyph**.
>
> **(what the next session picks up.)** **Step 4 is HALF BUILT.** Remaining: the
> observer rewrite (AC-7 — increment only on (b)/(c), observe otherwise), the
> existing L1 touch-counting test block (it asserts the OLD unit by design),
> both `_format_message`s + AC-11, wiring `clear_turn_scoped()` into
> `_apply_turn_boundary_reset` (`stop_continuation.py:224-239`, called at
> `:576`), then Step 6 closeout. **A design question blocks (c) and needs a
> probe:** the PLAN says hash the on-disk file, but this session's dump shows a
> successful `Write`'s `tool_response` already carries
> `content`/`originalFile`/`structuredPatch` — a hermetic payload-based digest
> may be available, keeping observer tests off real repo files. **Unmeasured for
> `Edit`**; measuring needs a hook registration, hence a restart, free at next
> session's start. Two traps are recorded in the PLAN: the `_edit()` helper's
> constant `old_string: "a"`, and existing targets pointing at real repo files.
>
> **State at close:** `main` `bc7be51`, suite **3318**, **1 open PR (#935)**.
> Carried, unactioned: `.claude/state/goal.json` still armed with the COMPLETED
> PLAN-0095 goal (raised three sessions running — Cray's artifact); the
> `CLAUDE.md` §6 stale plan-drafter gate claim + the `CLAUDE.md:176` dead
> `docs/conventions/git.md` link (one Cowork trip clears both; the `SKILL.md:62`
> copy is Code-fixable). AC-0088 wording debts **grounded this session as 2
> real, not 3** — debt #2 (AC-6 "dwell") does not reproduce; the AC text already
> says "same-row spans".

> **Session 177, 2026-07-27 (head_commit `c0f5935` → `da0b50b`) — the image
> builds and boots, and the L1 guard gets an exit that cannot be faked. Five
> PRs merged (#927, #928, #929, #930, #931), 0 open. **PLAN-0095 COMPLETE 7/7**,
> archived to `done/`; **PLAN-0094 Step 5 BUILT**, AC-9 closed. The `Dockerfile`
> had not built since the 2026-05-07 scaffold commit; `docker run` now answers
> `/health` in about two seconds with **no database reachable at all**.
> Suite 3296 → **3317**.**
>
> **(what shipped.)** **#927** — Steps 1–5 as ONE PR, because Step 1's oracle
> is deliberately born-RED and splitting would land a red suite on `main`.
> The builder defects are **eliminated, not repaired**: `--no-install-project`
> removes the hatchling build from the image entirely (the image needs neither
> the wheel nor the console script), which also keeps the dependency layer
> cacheable. `python -m uvicorn` replaces the bare console script so imports
> resolve by interpreter contract rather than by uvicorn's internal
> `sys.path.insert`. Per SD-2 the image also ships `alembic/` + `alembic.ini`;
> per SD-1 a thin compose `app` service consumes the same image and declares
> **no `command:`**. **#928** — runbook §1a, the hand-it-to-someone path.
>
> **(the oracle derives, it does not mirror.)** `tests/docker/` — 10 tests,
> stdlib + pytest + `ruamel.yaml`, **no daemon**. O-1 walks a **transitive
> closure seeded from the app package**, resolving module-level string
> constants (mandatory — the real defect's call site passes one, so a
> literal-only scan would miss the very bug that motivates the oracle) and
> filtering to real top-level directories. Seeding from the app root rather
> than "every top-level package" is deliberate: `benchmarks/` also carries
> `__init__.py` but never enters the image. **Born-RED with five distinct
> assertion families**; **12/12 mutations bit**, each turning exactly one
> predicted test red. `M-C` is the one that matters — a new runtime-resolved
> root goes RED **with no Dockerfile edit at all**. The derived set measured
> exactly `['services', 'verticals']`, no spurious roots. AC-3 ships as a
> **sibling test module** rather than the PLAN's literal reviewer-grep
> (Cray's call): a grep is a habit, a test is a gate.
>
> **(Step 6 — live evidence, on Cray's explicit go; evidence, never the gate.)**
> `docker build` exit 0 — the first successful build. `/health` 200 in ~2 s;
> boot log shows **all six verticals discovered**, which is precisely the
> `ModuleNotFoundError` that used to abort `lifespan()`; `/meta` serves the
> energy ontology; the container runs as **`uid=999(vero)`** with its
> `HEALTHCHECK` reporting **healthy**; `DATABASE_URL` is unset inside, so the
> DB-less claim is structural, not incidental. `alembic current` printed
> **`0012 (head)`** from inside the image against the live Postgres, exercising
> the whole SD-2 chain. **OQ-2's residual and OQ-3 are resolved by that run**
> (the *containerized* uv:0.11.9 does accept the flag — the dev-box measurement
> could not establish it); **OQ-1, the hosting model, stays open by design.**
>
> **(two deliberate departures from the PLAN's Step 6 sketch.)** A read-only
> probe first found `vero-postgres` + `vero-redis` **up 7 days** — and §1 of
> this repo's own runbook depends on them. So `docker compose down` was
> **not** run (it would stop them); cleanup was `docker compose rm -sf app`,
> removing only what this session created. `--no-deps` was added because the
> running containers carry a compose config-hash from a **Linux** path while
> the invocation came from a **Windows** path, which could have read as
> "out of date" and recreated them. Verified both directions: postgres's
> `StartedAt` was **byte-identical** before and after, and no image was left
> behind.
>
> **(two of this session's own errors, caught before they cost anything.)**
> The oracle's healthcheck URL extraction was wrong — it tokenized on
> whitespace and `strip()`ped, which cannot cut a leading `urlopen('` — found
> by **reading before running**, one step before it would have produced a
> false RED against a correct Dockerfile. And mutation `M-D` did not bite on
> the first pass: a whole-file substitution hit the **explanatory comment**
> naming the same flag instead of the `RUN` directive. The oracle was sound
> throughout (`_logical_lines` drops comments) — logged **`confirmed — prior
> intact`**; the probe script was the defect.
>
> **(a finding that was reported, then closed by Cray in the same session.)**
> Docker Desktop's **WSL integration was off for `ubuntu-24.04`**, so `docker`
> was not on `PATH` there and Step 6 ran from Windows PowerShell against a UNC
> build context. The consequence worth naming was that **§1 of
> `run-oct-demo.md` runs `docker ps` from bash** and would have failed for
> anyone following it from WSL. Code declined to flip the setting itself even
> after Cray said go, and said why: the toggle needs a Docker Desktop restart,
> and `vero-postgres` / `vero-redis` carry **`RestartPolicy=no`**, so they would
> not come back on their own — a downtime Cray had not asked for. Cray flipped
> it; the prediction held exactly (both `Exited (0)`, while other projects'
> `restart: always` containers returned by themselves). Restored with
> `docker start`, then verified: healthy on 5442 / 6379, `alembic current` still
> `0012 (head)`, `tests/api` 189 passed / 1 skipped. **#931** converts §1a's
> three blocks to bash — the bash `docker build` was **re-run and verified from
> WSL** (exit 0, image removed) rather than inferred — and records the trap the
> toggle itself demonstrated, including its tell: **a full suite reporting ~141
> skips instead of 8 is an unreachable DB, not a regression.**
>
> **(second half of the session — PLAN-0094 Step 5, the L1 exit an agent cannot
> fake.)** **#930** builds P3 / **AC-9**. When L1 denies, all three documented
> exits can be shut at once — the turn boundary is sticky, a commit needs a
> committable tree the gated file can itself block, and the subagent reset
> clears only a subagent's own edits — which is why **two of five recorded
> incidents ended in a Cray-authorised shell escape**. The deny branch now arms
> `awaiting_ack` (making that gate a **narrow state writer** for the first time)
> and the Stop hook clears it **only where the stop actually fires** (cap /
> contentless-proceed demotion / dispatch suggestion / pause), never where the
> agent is handed back to its own loop (substantive `proceed`, goal-gate
> directive, re-entry). Unforgeable because a fired stop by construction returns
> the prompt to Cray. The clear also **overrides the sticky rule** for exactly
> the armed targets, turning two-turn recovery into one. Step 5 landed **ahead
> of Step 4** deliberately: Step 4 is gated on a Cray per-diff `settings.json`
> approval and no step depends on a later one — surfaced, not assumed, and the
> PLAN's Status line (still reading "Steps 3–6 unbuilt" after Step 3 landed in
> s175) is corrected in the same PR. Suite 3306 → **3317**.
>
> **(what the RED-first run found that the design had not.)** The negative row
> `test_proceed_does_not_clear_the_marker` went **RED** — which a *missing*
> feature should not cause. Reason: the always-on turn-boundary reset rewrites
> the whole state document every Stop, so the marker is **dropped on every path**
> unless `awaiting_ack` round-trips through `to_json`. Stated as a rule because
> it generalizes past this field: **additive-and-tolerant was necessary but not
> sufficient; additive-and-serialized is the requirement.** A field the writer
> forgets is a field the reader silently loses, and the tolerance contract is
> exactly what hides it. Evidence discipline: 11 rows, **8 RED-first**; the three
> negative rows pass trivially against featureless code, so each was proven by a
> **named mutation** (drop the L1 scope guard / clear inside the re-entry guard /
> clear on substantive proceed), restored from a scratchpad copy, never
> `git checkout`. Thresholds **byte-unchanged**, verified by diff.
>
> **(an unplanned live demonstration.)** The L1 **warn** fired on
> `stop_continuation.py` mid-implementation — the guard warning about the file
> implementing its own fix. Assessed as the warning asks: six edits = helper,
> import, an import-order self-correction, three call sites — distinct forward
> progress, no retries of a failing change. That is precisely the false-positive
> class **Step 4 (P1)** exists to kill, observed in the wild rather than argued
> from the incident table; under the pre-Step-3 first-strike deny it would have
> been a wall, not a ping.

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
| 2026-07-28 | **s181 — CLAUDE.md full slim (#941): the 11.1 KB footer changelog RETIRED to git history; 277 → 261 lines / 33,014 → 21,524 B (−35.2%).** NEW convention: a constitutional edit bumps the footer date only — the edit's commit message is the full record; `git log --follow -- CLAUDE.md` = amendment history. Coverage verified BEFORE the cut (20 commit bodies ≥ their footer entries; companion artifacts on disk). No binding rule's substance changed (9 hunks, all §6 + footer). The <200-line LOCKED target unreachable (outside-§6 = 194 lines) → Cray ruled (b): target <20 KB + follow-up extraction pass queued | `85efe52` (#941 merge, head_commit) / `8ffd290` / `CLAUDE.md` + `.claude/handoffs/session-181/` |
| 2026-07-28 | **s180 — PLAN-0094 Step 4 COMPLETE (#937/#938/#939): L1 counts NON-PROGRESS, not touches. AC-7, AC-8(i)/(iii), AC-11 closed.** L1 increments only on a re-applied `old_string` (`repeat xN`) or a return to content already held this turn (`osc xN`); forward edits record `result == ""`; `clear_turn_scoped()` wired into the turn boundary. **All three L1 warns ever recorded would not fire under the new unit.** s179's BLOCKING `tool_response` probe was **answered without being run** (84 recorded `Edit` results: no `content` key, `originalFile` null in 78/84, `structuredPatch` = a diff not a state) — the PLAN's on-disk hash stands, no restart spent. **AC-11: `T` = the DENY bar in BOTH Telegram bodies** (Cray's ruling on a self-contradicting spec). **OQ-4 OPENED — should L1 exist at all?** Baseline over all 113 transcripts: **0 denies, 3 warns, 0 true positives**. **Pre-committed: re-measure after ~20 sessions; TPs still 0 with ≥1 FP → dispatch Cowork to draft the ADR-013 amendment retiring L1.** Suite 3318 → **3327** | `767d520` (#939 merge, head_commit) / `2b9cb6f` / `053410a` (#938) / `0a85b21` (#937) / `docs/plans/0094-loop-detect-non-progress-and-reset-paths.md` §D4 + §OQ-4 |
| 2026-07-27 | **s179 — PLAN-0094 Step 4 RE-SCOPED on its own probe's refutation (#933); OQ-3 opened + RESOLVED same session.** Measured twice, one session apart: **a failed `Edit` invokes NO hook** — not `PostToolUseFailure`, not `PostToolUse`. **D4(a) withdrawn**, taking **AC-1(ii) / AC-6 / AC-8(ii)** with it (AC-6 withdrawn, not weakened) and with them Step 4's only Cray-gated `settings.json` surface; the s169-class thrash stays **uncountable**. OQ-3 → (b), four rulings: **R1** a self-contained COUNT, not a sha1 pointer (evidence ring 6 vs doc trip bar 15); **R2** `dict[str,int]`; **R3** `result == ""` on forward edits; **R4** → new **AC-11** (Telegram `count: N/T` + formatter mirror-invariance) | `b3c20dd` / `bde43d6` (#933) / `docs/plans/0094-loop-detect-non-progress-and-reset-paths.md` §D4 + §OQ-3 |
| 2026-07-27 | **s179 — `main` was RED for three hours and PR-only CI structurally could not see it (#934): the tests EXPIRED, they did not regress.** `_seed_ack` hardcoded a `last_updated`; `load_counter`'s `prune_stale_entries` drops entries past `COUNTER_MAX_AGE_HOURS` (6 h) — green at merge, red hours later. `git diff 25239f3 490f09e` was **EMPTY**: same tree, opposite verdict. Proved with zero code edits (`CLAUDE_LOOP_COUNTER_MAX_AGE_HOURS=100000`). Fix stamps from `_now_iso()` + adds `test_seed_ack_is_stamped_live`, a guard that **tests the FIXTURE** so a future re-hardcode fails at the cause. Suite 3317 → **3318** | `35851f2` (#934) / `bc7be51` (head_commit) / `a5dacb0` (#935, OPEN — Step 4 state layer) |
| 2026-07-27 | **s177 — PLAN-0094 Step 5 BUILT (#930): `awaiting_ack`, the L1 exit an agent cannot fake. AC-9 closed.** When L1 denies, all three documented exits can be shut at once — sticky turn boundary, a commit needing a tree the gated file itself blocks, a subagent reset scoped to the subagent's own edits — which is why **2 of 5 recorded incidents ended in a Cray-authorised shell escape**. The deny branch now arms the marker (that gate becomes a **narrow state writer**) and the Stop hook clears it **only where the stop actually fires** (cap / contentless demotion / dispatch suggestion / pause), never on `proceed`, a goal-gate directive, or re-entry. Also **overrides the sticky rule** for armed targets → two-turn recovery becomes one. **Landed ahead of Step 4 deliberately** (Step 4 is gated on a Cray per-diff `settings.json` approval; no step depends on a later one) — surfaced, not assumed. Key finding the RED-first run forced: a negative row went RED because the turn-boundary reset rewrites the whole document, so **additive-and-tolerant was necessary but not sufficient — additive-and-SERIALIZED is the requirement**. 11 rows, **8 RED-first**; the 3 negative rows proven by named mutations (scratchpad restore, never `git checkout`). Thresholds byte-unchanged. **Live demo, unplanned:** the L1 warn fired on `stop_continuation.py` *while it was being fixed* — 6 distinct forward edits, zero retries = exactly the false-positive class Step 4 exists to kill. Plus **#931**: Cray enabled Docker Desktop's WSL integration (Code declined to flip it itself and said why — `RestartPolicy=no` meant an unasked-for downtime; the prediction held exactly), runbook §1a converts to bash with the build **re-verified from WSL**. Suite 3306 → **3317** | `da0b50b` (#931 merge, head_commit) / `387bef0` / `2736acf` (#930 merge) / `c076f7a` / `docs/plans/0094-loop-detect-non-progress-and-reset-paths.md` §D5 |
| 2026-07-27 | **s177 — PLAN-0095 COMPLETE 7/7, archived to `done/`: the image builds and boots for the first time since the 2026-05-07 scaffold commit.** #927 lands Steps 1–5 as ONE PR (the oracle is born-RED, so splitting lands a red suite): builder defects **eliminated not repaired** (`--no-install-project`), `python -m uvicorn` for a guaranteed import path, `alembic/` shipped per SD-2, a thin compose `app` consumer per SD-1. The oracle **derives** its COPY set by transitive closure from the app root — born-RED with **5 assertion families**, **12/12 mutations bit** (M-C goes RED with *no Dockerfile edit*), derived set measured exactly `['services','verticals']`. AC-3 ships as a **sibling test**, not the PLAN's reviewer-grep (Cray's call). #928 adds runbook §1a. **Step 6 live, on Cray's go:** build exit 0, `/health` 200 in ~2 s, all six verticals in the boot log, `uid=999(vero)`, HEALTHCHECK `healthy`, `alembic current` → **`0012 (head)` from inside the image**. **OQ-2 residual + OQ-3 RESOLVED; OQ-1 (hosting model) open by design.** Two PLAN departures, both evidence-backed: no `docker compose down` and `--no-deps`, because `vero-postgres`/`vero-redis` were **up 7 days** and §1 depends on them — `StartedAt` byte-identical before/after. Two self-caught errors: the oracle's URL extraction (found by reading, one step before a false RED) and a mis-aimed M-D that hit a **comment** not the `RUN` line — oracle logged `confirmed — prior intact`. Finding, reported not fixed: **Docker Desktop's WSL integration is OFF** for `ubuntu-24.04`, so runbook §1's own `docker ps` precondition fails from WSL today. Suite 3296 → **3306** | `8618081` (#928 merge, head_commit) / `54f0189` / `6ab2c28` (#927 merge) / `fb0e1f8` / `docs/plans/done/0095-docker-image-boot.md` + `tests/docker/test_dockerfile_oracle.py` |
| 2026-07-27 | **s176 — PLAN-0095 merged as Draft (#925): make the Docker image build + boot the DB-less OCT demo. Nothing built; Steps 1–5 unexecuted.** The grounding sweep (4 Explore agents, 15 items) killed **5 wrong s175-handoff premises** — the first-order boot failure is a plain import (`discovery.py:45`, uncaught at `main.py:166`), **not** the CWD-relative `Path("verticals")`; plus an uncounted **9th** defect (`pyproject.toml:7` `readme` never COPY'd). Cray ruled **SD-1 = both**, **SD-2 = include `alembic/` + document**, **SD-3 = all four** — reframing the PLAN as *ready for development toward production*; SD-1/SD-2 overturned the drafter and are logged `superseded by new info`. Oracle derives the COPY set by **transitive closure from the app root** (not a `verticals` glob — that would break AC-3); **AC-6: no AC needs a Docker daemon**. Finding: **CLAUDE.md §6's plan-drafter gate claim is STALE** — the subagent is exempt by design (`pretooluse_classifier_dispatch.py:301-311`), G2 preserved for Code | `77fa734` (#925 merge, head_commit) / `2fb8709` / `docs/plans/0095-docker-image-boot.md` |
| 2026-07-26 | **s175 — the harness stopped letting a failed command look like a success.** #923: Lesson #0007's mechanism CORRECTED and reclassified `was an error` (a bare `$` expands one shell layer early; `$?` is not unreadable) + a binding CLAUDE.md §8 rule + a `_shell_hygiene_warning` PostToolUse advisory. #922: PLAN-0094 **Step 3** — warn at T, deny at T+G (9 code / 18 doc), L4 flat 6; AC-3/4/5 closed. #920 pins all six verticals' ACTION factory offline at REGISTRATION; #921 fixes four stale cross-refs. **Cray: demo target = the LIVE-API shape** → Candidate C is the long pole. ADR-009 D1 one-off Code-authors-§8 exception — **not precedent**. Suite 3252 → **3296** | `04c94e4` (#923 merge, head_commit) / `3b3b666` (#922) / `59c81a6` (#921) / `65c6953` (#920) / `docs/lessons/0007-harness-exit-code-artifact.md` |
| 2026-07-25 | **s174 — MS-S1 stopped being an inference appliance, and CLAUDE.md §8's gated surface was widened to match.** #916 opens OpenSSH on TCP 22, LAN-only (`Domain, Private`), verified with `BatchMode=yes` — which proves publickey auth, not a silent password prompt; the knowledge splits per §4 — rule in §8, how-to in the runbook, procedure in a new `ms-s1-admin` skill. #918 rescopes §8, net +1 line: substance unchanged, its `…:11434` *illustration* was reading as a scope boundary (Cowork drafted → Code R2'd + committed → Cray ratified). #917 lands PLAN-0094 Steps 1+2 — the `SubagentStop` L1 reset, scoped to the completing agent's OWN edits (turn-scoped would be a self-unlock path; Cray ratified the divergence from Lesson #0021 §3); suite 3244 → **3252** | `a3a9c66` (#918 merge, head_commit) / `2cda070` (#917) / `c9050b9` (#916) / `docs/runbooks/ms-s1-ssh-access.md` + `docs/plans/0094-loop-detect-non-progress-and-reset-paths.md` |
| 2026-07-25 | **s173 — the L1 loop-detect guard: its unit of measurement was wrong and one documented escape was never wired.** #912 bounds the loop-counter state lifetime (age-out 6 h + a session boundary read from the hook payload, which `resolve_session_id` never consulted). #914 lands **PLAN-0094** (Draft) + **Lesson #0033**. Probed live: `PostToolUse` fires only on success, so L1 could not see a failed edit at all — 6 good edits score 6, 6 retries of one broken anchor score 0, so **no threshold separates them** and PLAN-0094 changes none. `_handle_agent_completion` is **dead code** (no `PostToolUse` Task/Agent matcher); the registry row L1, Lesson #0021 §3 and the deny message all still call it live. Cray ratified **OQ-1 `G=3`, OQ-2 full fresh budget, SD-2 subagent-scoped reset** (a decision, not a diff approval — it changes a recorded lesson) | `6fb89b8` (#914 merge, head_commit) / `3383697` + `2d09002` (#912) / `docs/plans/0094-loop-detect-non-progress-and-reset-paths.md` + `docs/lessons/0033-raising-the-threshold-is-not-fixing-the-unit.md` |

## In-Flight Discussions

- **PLAN-0095 — Draft, merged s176 (#925); Steps 1–5 UNEXECUTED, Step 6 host-state.** Make the scaffold-era `Dockerfile` build and boot the synthetic OCT demo with **no database**. **Nothing is built** — no Dockerfile change, no test, no compose edit; the image does **not** boot today. Root cause is measured, not guessed: the first-order failure is a plain Python import (`importlib.import_module(_VERTICALS_PACKAGE)`, `services/engine/discovery.py:45`, uncaught as the first line of `lifespan()` at `services/api/main.py:166`); the CWD-relative `Path("verticals")` at `ontology_meta.py:154` is real but **second-order**. The defect count is **two broken `COPY` statements** (each with two symptoms) + hygiene gaps + a **ninth** defect found in-session: `pyproject.toml:7` declares `readme = "README.md"`, never COPY'd, so `uv sync` fails a second time even after the package-tree fix. **All three SDs RULED by Cray under a production frame** — *"ready for development toward production," not "build production now,"* across two hosting models (customer uses an instance we host / we stand up a server on-site): **SD-1 = both** (standalone image is the artifact; compose is a thin consumer proving it composes with a real Postgres), **SD-2 = include `alembic/` + document** (one image, different commands; a separate migration image is the riskier shape — version skew), **SD-3 = all four hygiene items IN**. SD-1 + SD-2 overturned the drafter's own recommendations and are in-PLAN as **`superseded by new info`**, not `was an error`, with the original analysis preserved. **The oracle is the PLAN's real content:** O-1 **derives** the required COPY root set by AST **transitive closure seeded from the app root** (a literal `verticals` glob was rejected in R2 — it breaks AC-3, and `benchmarks/` never enters the image, a latent false-RED), with anti-tautology invariant **AC-3** and mutation **M-C** that must go RED; O-4/O-5/O-6 carry binding derivation-status labels (`USER` is honestly a presence check). **AC-6 is invariant: no acceptance criterion needs a Docker daemon** (O-6 parses YAML via `ruamel.yaml`, a main dep at `pyproject.toml:23`); every daemon action sits in the optional Cray-gated evidence step. **Execution trap:** the compose `vero:vero` in-network URL trips `detect-secrets` as Basic Auth Credentials and needs an inline `# pragma: allowlist secret` **in the real `docker-compose.yml` at Step 3** — a pattern match, not a leak (dev placeholder already tracked at `docker-compose.yml:6-7` + `services/api/config.py:39`); never `--no-verify` (CLAUDE.md §8). **Steps 1–5 are ONE PR-sized unit that cannot be split** — Step 1's oracle is deliberately born-RED against the current Dockerfile, so committing it alone lands a red suite. Full record: `docs/plans/0095-docker-image-boot.md`.
- **Hosting model → ADR-002's LAN trust boundary: a LIVE candidate needing its own ADR (surfaced s176, not drafted).** *"Customer uses our server"* touches ADR-002's LAN trust model — `docs/adr/0002-network-topology.md:76` and `:86` — which defers its own successor **twice** as an unnumbered `ADR-NN`. PLAN-0095 can land with this open, because nothing in the image or the compose service selects *where* the image runs; the question bites when a hosting model is actually chosen. Route: a new ADR via the Cowork/plan-drafter path (G1/G2 — Code may not author it).
- **PLAN-0094 — Draft; Steps 1–5 ALL BUILT (s174 #917, s175 #922, s177 #930, s180 #935/#937/#939 — Step 4 COMPLETE, AC-7 / AC-8(i)(iii) / AC-11); Step 6 (closeout, AC-10) is all that remains.** The L1 loop-detect restructure: count non-progress instead of touches (P1), warn on the first trip and deny on the second (P2), add an acknowledged-pause exit the agent cannot fake (P3), and wire the subagent-completion reset that had **never been live** (F3c). **Step 1 (F3c) landed:** a `SubagentStop` registration (matcher `*`) plus additive per-`agent_id` `subagent_touched` state, so a completing subagent clears its **own** recorded edits and cannot launder the main agent's budget through a zero-edit spawn. **The soak released Step 3** — Cray reported no anomalies on the live loop. **Step 3 landed (#922, AC-3 final surface / AC-4 / AC-5):** the path-class threshold is now the WARN bar and the deny sits at `T+G` (`G=3`) = **9 code / 18 doc**, L4 untouched at flat 6, `CounterEntry.warned_at` dedupes the warn; the deny message deliberately does **not** name the P3 stop-ack, since P3 ships at Step 5 (test-pinned). **AC-1 (ii) is WITHDRAWN** (s179 #933) — a failed `Edit` invokes no hook at all, so there is nothing to register; **AC-6 + AC-8(ii) fell with it**, and Step 4 no longer carries a gated `settings.json` surface. **Ratified inputs are LOCKED:** OQ-1 `G=3`, OQ-2 full fresh budget, and SD-2 — subagent-scoped, per-`agent_id`-keyed reset — ratified as a **decision, not a diff approval**, because it changes what Lesson #0021 §3 recorded as the 2026-06-08 fix. **Every `settings.json` diff needs Cray per-diff approval** (guard self-modification, Lesson #0021 §4). Governance footing: **no ADR amendment** — ADR-0013 row E.4 (`docs/adr/0013-autonomy-axis-relocation.md:90`) specifies the consequence as "pause + Telegram alert", so the hard deny exceeded its own mandate and P2 moves L1 *toward* the ADR. Of the three surfaces that asserted the dead reset path was live, **two were corrected in Step 2** (registry row L1, Lesson #0021 §3) and the third — the deny message in `pretooluse_loop_detect.py` — was rewritten in Step 3, per D2's do-not-edit-twice instruction. All three are now closed. Substrate already shipped in #912; do not re-plan it. **OQ-4 is OPEN (s180): should L1 exist at all?** Baseline over all 113 session transcripts — **0 denies, 3 warns, 0 true positives**, and the guard cannot catch the s169 incident that motivated it — with a **pre-committed re-measure after ~20 sessions** and a Cowork-drafted ADR-013 amendment retiring L1 if TPs stay 0 with ≥1 FP. Full record: `docs/plans/0094-loop-detect-non-progress-and-reset-paths.md`; the anti-pattern behind it: `docs/lessons/0033-raising-the-threshold-is-not-fixing-the-unit.md`.
- **PLAN-0093 — COMPLETE 8/8 and ARCHIVED (s172, #913).** The LLM-arm degrade disclosure — no silent arm swap: which arm phrased an NL answer is disclosed, the rule fail-safe says it is a fail-safe, the authoring arm is projected over HTTP (including the insights run-corpus path), and `LLM_RETRY_BUDGET` no longer sits inert on the governed path. No follow-on owed. Full record: `docs/plans/done/0093-llm-arm-degrade-disclosure.md`.
- **PLAN-0091 — COMPLETE 10/10 and ARCHIVED (s168).** Two follow-ons it named, **neither scheduled**: the **extend shapes** (calm-path + scheduled-variant scaffolding) are **greenfield, not an extension** — the shipped emitters refuse an existing vertical *by construction* and create-only is Cray-ratified SD-2, so this needs a fresh seam spec, not effort; and the census-narrative comment in `tests/api/test_procedures_endpoint.py` is the one counted site the disposer REPORTS rather than rewrites — a human call, left visible on purpose. Full record: `docs/plans/done/0091-narrative-to-vertical-scaffolder-tool.md`.
- **PLAN-0088 — COMPLETE (13/13 live ACs) and ARCHIVED (s171, #908).** The cross-run read substrate + the four run-insight readers (A2 ฿ ROI, A3 flow, A4 audit-readiness, A1 NL-over-runs) + the Group-B carrier proof. SD-1…SD-9 all Cray-ratified; the substrate stays aggregate-only (SD-8 a) and grows only in `run_analytics.py` (SD-9 a2); Group A ungated, Group B pilot-gated (AC-10 proves the questions expressible, AC-11 that no proposal machinery exists). AC-9b's live MS-S1 smoke PASSED. **Three AC-WORDING debts carried into the archived PLAN, none a code defect** (Cray's to reword if ever): (1) AC-2 names the wrong approver source — the approver is in the trace / `governed_decision` / audit-log, not `step_principals` (the requester half); (2) AC-6's "dwell" is a same-row start→suspension span, stated plainly in the code; (3) SD-9's aside miscalls `trigger` "undefined". Full record: `docs/plans/done/0088-cross-run-read-substrate-and-run-insight-readers.md`.
- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13; verdict **continue-with-adjustments**. Runs 1 (energy, s93) + 2 (supply-chain, s94) both COMPLETE, all S-checks PASS against pre-committed oracles, no R-PS trigger fired; C-1..C-3 CONFIRMED → **no open partner-sim debt**. ADR-011's audit stays gated on a REAL partner conversation (R3: SYNTHETIC provenance INFORMS but never TRIGGERS it). Full record: `docs/adr/0020-*.md` + the gitignored run packages under `docs/research/private/`.
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **Procurement vertical — GO + SHIPPED (PLAN-0036 Fastenal, Stage 1):** 4th vertical greenlit (s75), PLAN-0036 merged Draft (#412, SD-1…SD-5 confirm-all). Demo target = Fastenal Thailand; **hero** = asset-failure → governed emergency sourcing, **calm-path** = low-stock reorder. Stage 1 = a PLAN-only pure-config plugin on the ADR-016 engine (zero `services/` core edit; CQ-1 / ADR-0023). **Pitch** = asset-ontology-triggered governed sourcing (ADR-008 + ADR-016), NOT the commoditized "governed"/"cross-vertical" claims. Full record: `docs/plans/0036-*.md` + the s72 de-risk dossier under `docs/research/private/`.
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
- [ ] **`CLAUDE.md` §6's gate-route claim is STALE — needs a Cowork round-trip (found s176; SURVIVED the s181 slim verbatim, now `CLAUDE.md:112`; NOT fixed).** §6 "Mechanical overlay" says a new PLAN/ADR is PreToolUse-gated for Code **and the in-harness `plan-drafter`**. Measured: `.claude/hooks/pretooluse_classifier_dispatch.py:301-311` **exempts the `plan-drafter` subagent from the G2 classifier gate by design** (PLAN-0034 prong 2, SD-1(a)) — it short-circuits *before* the classifier, so it does not even depend on MS-S1 being warm. The main Code agent carries no `agent_id` and **is** still gated, so **G2's substance is preserved**; only the sentence is wrong. Same round-trip class as the `CLAUDE.md:160` dead-link row above — Code may not author `CLAUDE.md` (ADR-009 D1; the s175 #923 exception was scoped to §8 only), so batch the two if convenient. *(low priority — a documentation defect, not a guard defect)*
- [ ] **CLAUDE.md follow-up extraction pass (s181 option b): new Cowork dispatch; target < 20 KB (~18 KB / ~225–235 line floor).** Candidates (Cowork fresh-eyes, s181 completion §6): §11 ¶3 restates the §6 E2 rule → one-line pointer; §10 skills-row annotation duplicates §4's Tier-2.6 row (in-file ADR-0017 D6 drift); §10 docs/logs row's PLAN-004 parenthetical; §9 halves; §3 folds into §1. Materials: `.claude/handoffs/session-181/` (gitignored).
- [ ] **PLAN-0094 Step 6 (closeout, AC-10) — the only step left, and it is gated on two unrun live checks.** Step 4 completed s180 (#937/#938/#939), so Steps 1–5 are all BUILT. Before AC-10 can close: (i) the **PLAN §Verification live-check (ii)** — one deliberate warn-crossing on a scratch file, to confirm the advisory actually reaches the agent's context — is **still unrun**; and (ii) Cray must confirm a **live-loop soak** on the new non-progress unit. Full detail: `docs/plans/0094-loop-detect-non-progress-and-reset-paths.md` §Step 6 + §Verification.
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
