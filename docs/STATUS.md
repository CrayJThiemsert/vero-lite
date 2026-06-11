---
last_updated: 2026-06-11T15:51:02+07:00
session: 53
current_batch: 'Session 53 — PLAN-0020 (Procedure-path tuning) COMPLETE + archived to done/ (#251-#256): nudge worked (β/α →100%), skip lever cuts p95 31.80→21.62s under the 30s bar at zero β cost; SD-1 skipped, ring-fence honored.'
current_actor: code
blocked_on: 'Nothing gates shipped work. No open PRs.'
next_action: 'Future PLAN for tiered handler grading (canonical/acceptable/forbidden — α too coarse); wiring skip into product procedure path is an open audit trade-off design call. Both deferred for discussion. Also HELD: an R3-adjacent MS-S1 warm-cycle (pin vs 3 nemotron-3-nano variants, ideally paired with the U-1 MXFP4-vs-Q4_K_M check) when a maintenance window opens — no eval yet, no ADR-0001 change.'
head_commit: a6125c1
recent_commits: [a6125c1, 4968f51, ac56653, bef462f, a3a6f54, 19706eb, 60e88fe, fa368e2]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 53 (current) — PLAN-0020 (Procedure-path tuning) is COMPLETE
> + archived to `docs/plans/done/` (#251–#256, branch-tip `a6125c1` =
> head_commit, the `docs(plans):` close-mv riding #256; merge `02d3e46`;
> the PLAN-0019 B-6 ring-fence follow-up).** Headline results (all
> `--dump-json`-VERIFIED, `gpt-oss:20b` on MS-S1): the Phase-1 aquaculture
> prompt nudge (PR #232, previously UNMEASURED) worked **dramatically** —
> overall β `85.8%→100%`, aquaculture β `60%→100%`, overall α `70%→100%`
> (supply_chain α `32.5%→100%`: the model now picks `hold`, not `inspect`).
> **The latency lever:** a new `reasoning_mode` lever showed `skip` (drop the
> call-1 reasoning pass) cuts per-judgment p95 `31.80s→21.62s` — UNDER the
> re-ratified SD-2 bar — at **ZERO β cost** (the reasoning pass is redundant
> given the nudged prompt); `think_off` is a **dead lever** (slower).
> **SD-2 re-ratified** the latency bar from 8 s/per-call to **≤30 s p95
> per-judgment** (reports-not-gates). **SD-1** (widen supply-α `valid_handlers`)
> was authorized at ratification but **SKIPPED at Step 9** — the nudge made the
> divergence moot (0 `inspect`); anti-moving-target honored, **no grader
> change**. Also shipped: a per-judgment latency timer (#252), the think-trim
> lever (`feat(engine)`, #253, PLAN-0020 AC-1a), and the **`ms-s1-ollama`
> skill** (#254, `warm.sh` live-tested). PR lineage: #251 ratify Draft→Accepted
> (`19706eb`, SD-1 widen-α + SD-2 →30 s/judgment) → #252 latency timer
> (`a3a6f54`) → #253 think-trim lever (`bef462f`) → #254 skill (`ac56653`) →
> #255 tuning report (`4968f51`, `docs(report):`) → #256 close-mv to done/
> (`a6125c1`, `docs(plans):` = head_commit, the newest substantive per
> `lint_status` — only `docs(status):` is excluded).
> **Session 52 was non-committing** (an Axis-B verification-loop LIVE demo +
> a backlog-prioritization pass that ranked PLAN-0020 priority #1) — no repo
> state changed, so the jump is session 51 → 53.
> **Next.** A follow-up PLAN for **tiered handler grading**
> (canonical / acceptable / forbidden) is surfaced by Cray's production-fidelity
> review — the α metric is too coarse to self-distinguish a benign alternative
> (`inspect`) from a dangerous pick (`expedite`/`reroute`); deferred to a future
> session for discussion. Separately, **wiring `skip` into the product
> procedure path** is an open design call (audit trade-off: `skip` drops the
> ADR-010 reasoning narrative; the model-asserted `rationale` survives). The
> gitignored Cowork research (why `gpt-oss:20b` wins) is now **DONE** —
> delivering a 6-criterion model-selection **screening rubric (R1–R6)** + a
> warm-cycle gate (`docs/research/private/2026-06-11-gpt-oss-20b-winning-properties.md`),
> the paper pre-filter for the deferred R3 faster-arch eval. **Held for a future
> R3-adjacent warm-cycle:** Cray pulled **3 `nemotron-3-nano` variants** to
> MS-S1 (`30b-a3b-q4_K_M`, `30b-a3b-q8_0`, `4b`) — **no eval run yet, no
> ADR-0001 change**; intent is pin vs these in one maintenance-window warm-cycle,
> ideally paired with the U-1 `MXFP4`-vs-`Q4_K_M` tok/s check + U-2 `eval_count`
> logging. **Caveat:** they ship `q4_K_M`/`q8_0`/`fp16` (not `MXFP4`), so they
> exercise rubric R1/R5 now but a fair **R2 bandwidth** comparison needs an
> `MXFP4` build.
> AI-assisted (Claude Code, session 53); no `Co-Authored-By` per CLAUDE.md §7.
>
> **Session 51 — PLAN-0021 EXECUTED + MERGED (#249, branch tip
> `3dc586a`; merge `83f179d`; head_commit `7d6d713` = the `docs(plans):`
> archive-mv riding this closeout PR, the newest substantive per
> `lint_status` — only `docs(status):` is excluded): the Axis-B
> verification loop is LIVE.** 2,125 insertions: 6 new files
> (`_goal_state.py`; `_goal_gate.py` at the D4 seam inside
> `stop_continuation.py`; the `/goal` project command — the repo's first,
> discovered mid-session; `goal-evaluator` as 4th subagent sibling; the
> SD-1 narrowed-Write deny hook; +64 tests across 3 new test modules + M2
> rows), exactly 3 modified files, `settings.json` untouched (F-1). All 10
> ACs closed; the 10-row case-coverage matrix fully implemented as named
> tests AND 7 rows proven LIVE in the session's own Stop hooks: real
> dispatch ×2 (D6 pointers-only template; Windows-side check subprocess +
> UNC git fingerprint worked), live evaluator spawn (J1=PASS
> file:line-cited; appended its verdict through the SD-1 hook; caught a
> real registry-footer gap on its first run), happy flip
> (`_goal_gate:passed` + Telegram info), and the fail-open probe
> (deliberately unanswered dispatch → `released-unevaluated` + LOUD
> Telegram + stop fired, NO wedge — D4's asymmetry held in production;
> both Telegrams Cray-screenshot-confirmed, timestamps matching the
> trail). Full suite 1398 passed / 22 skipped, zero regression. Key
> finding **F-L1**: verdict→flip lands at the next non-chained Stop (the
> re-entry guard short-circuits block-continuation Stops — a PLAN-0008
> invariant, 3 consistent observations; OQ-8 blocking-mode promotion must
> account for it). PLAN-0021 archived to done/ (`7d6d713`, same PR as
> this reconcile). Closeout handoff:
> `.claude/handoffs/session-51/2026-06-10-1450-code-plan0021-build-closeout.md`.
> AI-assisted (Claude Code, session 51); no `Co-Authored-By` per CLAUDE.md §7.
>
> **Session 51 (earlier) — PLAN-0021 "Axis-B verification loop — build"
> landed as Draft (#247, head_commit `78b8659`, `docs(plans):`).** Cowork
> drafted it per ADR-009 D1 off the session-51 T2 dispatch; Code R2-reviewed
> + committed per D2/D3. The PLAN renders Accepted ADR-0018 into a build
> plan: 6 new files (`_goal_state.py`, `_goal_gate.py`,
> `.claude/commands/goal.md` — the repo's FIRST project command, net-new
> dir; `goal-evaluator.md` as 4th subagent sibling;
> `pretooluse_goal_evaluator_write_deny.py` SD-1 narrowed-Write hook; 3
> test modules) + exactly 3 modified files (M1 `stop_continuation.py` one
> insertion at the D4 seam, M2 its tests, M3 `autonomy-triggers.md` V-row).
> 10 ACs incl. AC-2 goal-less byte-for-byte non-interference; a 10-row
> case-coverage matrix, each row mapped to a named test; VX-1..3 resolved;
> OQ-8 pinned Out of Scope. Key R2 item **F-1**: Cowork caught the
> dispatch's wrong premise — status-scribe's deny hook wires via agent
> frontmatter ONLY, not `settings.json` — so the PLAN keeps `settings.json`
> untouched and ADR-0018 §spec 4 stays literally true. **NEXT:** Cray
> ratifies PLAN-0021 (incl. SD-1: SubagentStop notify for goal-evaluator —
> Cowork recommends NO for v1) → Code executes Steps 1-6 in a feature
> branch.
> AI-assisted (Claude Code, session 51); no `Co-Authored-By` per CLAUDE.md §7.
>
> **Session 51 (earlier) — STATUS rotation arc COMPLETE: Lesson #23 +
> rotation policy R1-R6 (#244), status-scribe hardened (#245), FIRST
> ROTATION under the policy + 64 KB pre-commit guard (this PR).** Root
> cause of the 393 KB bloat was the scribe's own retention rule ("never
> delete history" with no size counterweight — Lesson #23 §2); the policy
> pairs retention with a budget: hard 64 KB / soft 48 KB (R1), window =
> 4 newest sessions / <=8 CF blocks + 10 RD rows (R2), terse single-line
> frontmatter (R3), archive-don't-drop to `docs/status-archive/` (R4),
> surgical reads only for the scribe (R5), prune every reconcile (R6).
> **This rotation:** session-47 CF block + 39 RD rows -> archive
> (`2026-h1-status.md` — new file; the ratified h1 current-focus file is
> 242 KB, past the ~192 KB R4 split bar, so appending would breach the
> 256 KB Read cap — flagged, not silent); F-6 prune dropped all [x]
> Active TODOs older than the window + Next Steps items 1-9 (superseded
> MERGED history; recorded in RD/git). head_commit `25af97b` (#245
> `chore(agents):` = newest substantive; #244's `e22ab18`/`311761c`
> precede it). R2 review note: Code-harness tokenizer measures ~2.2 B/tok
> on this file (38.6k tok at 83 KB) vs Cowork's ~3.3 — 64 KB may still
> exceed a whole-file Read in some harnesses; R5 surgical reads are the
> structural protection, the byte ceiling is the enforcement proxy.
> **NEXT = Axis-B T2** (dispatch ready, awaiting Cray relay to Cowork).
> AI-assisted (Claude Code, session 51); no `Co-Authored-By` per CLAUDE.md §7.
>
> **Session 51 (earlier) — ADR-0018 "Axis-B Verification Loop" is RATIFIED
> Accepted (#242, head_commit `1be60f7`, `docs(adr):`); the deferred Axis-B
> verification-loop track is no longer deferred — it is now Accepted and
> entering its build phase.** ADR-0018 opens harness-review **track 2** (the
> evaluator loop) on top of the already-at-frontier Axis-A governance layer:
> a `/goal` Stop-hook gate + a `goal-evaluator` subagent that judges whether a
> run actually achieved its declared goal. **Decisions:** D1 hybrid
> deterministic-check + LLM-judge; D2 a `.claude/state/goal.json` run-goal
> artifact; D3 a **4th subagent sibling that REFUTES rather than blesses**
> (the structural guard against reasoning-blindness); D4 a `_goal_gate.py`
> living inside `stop_continuation.py`, **FAIL-OPEN** (a broken/absent
> evaluator never blocks Stop); D5 a session-Stop **warn-only v1**; D6 the
> structural reasoning-blindness rationale; D7 formalize + augment the manual
> AC ritual. **SD-1 resolved = narrowed Write** — the evaluator's `Write` is
> hook-narrowed to `goal.json` only (the same author-bounded pattern that
> governs `plan-drafter` and `status-scribe`). **Lineage:** PR #241 added the
> ADR `Proposed` (`5f8073c`) → **#242 ratified it Proposed→Accepted (Cray,
> session 51)** and carries this **T4** STATUS reconcile (the ADR §"Required
> follow-on" T4 task: record ADR-0018 in Recent Decisions + clear the
> Current-Focus Axis-B "deferred" earmark). head_commit = `1be60f7` (the
> ratification `docs(adr):` commit = the newest *substantive* commit per
> `lint_status`; this `docs(status):` reconcile does NOT count). **NEXT = T2:**
> Code dispatches the Axis-B **build PLAN** to Cowork (ADR-009 D1) — covering
> `_goal_gate.py` + the `stop_continuation.py` insertion, the `goal.json`
> schema + tests, the `/goal` command, the `goal-evaluator` agent + the SD-1
> write-deny hook, Telegram wiring, and a verification-rigor case-coverage
> matrix; after draft + Cray ratify → T3 (autonomy-triggers **V-row**) →
> build. **OQ-8** (plugin packaging, MS-S1 local evaluator, blocking-mode
> promotion, PR-merge gating, auto-declared goals) and **VX-1..3** stay
> non-binding / verify-at-execution — none blocks T2. This session also
> earlier resolved ADR-0017 OQ-B (#239/#240), already recorded below.
> AI-assisted (Claude Code, session 51); no `Co-Authored-By` per CLAUDE.md §7.
>
> **Session 51 (earlier) — ADR-0017 OQ-B is RESOLVED; the skills-as-memory-tier
> arc's last open thread is CLOSED (#239, head_commit `c512cf9`,
> `docs(adr):`).** OQ-B (skill-loader tie-break on a same-bare-name collision)
> was the one "delegated to Code" empirical item left after the arc body landed
> in session 49 (#234/#236/#237/#238). Empirical finding, restart-confirmed at a
> clean session-51 startup (~99% confidence): on a same-name collision the
> **GLOBAL/user skill (`C:\Users\crayj\.claude\skills\`) WINS over the project
> skill** (`<repo>/.claude/skills/`) — the OPPOSITE of ADR-0017 D7's
> "project-local context wins" premise; the WSL `~/.claude/skills/` path is not
> scanned, and plugin skills are namespaced (so they don't collide). Recorded
> three ways: (1) ADR-0017 gains a **"D7 Errata (2026-06-10)"** subsection +
> OQ-B flipped Open→RESOLVED (errata applied with Cray's explicit per-diff
> approval through the G1 Accepted-ADR gate); (2) new
> `docs/lessons/0022-skill-loader-precedence.md`; (3) a fill of the
> `docs/runbooks/memory-architecture.md` §"Skill Conventions" OQ-B placeholder.
> The D7 **authority rule** (global/plugin skills must not encode
> project-binding rules) is UNCHANGED and *reinforced* — only the loader
> tie-break mechanics and an incidental `eli-cray` example (it's a command, not
> a global skill) were corrected. The throwaway probe artifacts (host state on
> three skill roots) were cleaned up after merge — working tree restored to
> clean. AI-assisted (Claude Code, session 51); probe ran with Cray's approval;
> no `Co-Authored-By` per CLAUDE.md §7. Two ADR-0017 OQs remain, both
> non-blocking: **OQ-A** (migration backlog — non-binding future-PR candidates)
> and **OQ-C** (revisit the tier definition only if harness-as-plugin packaging
> is pursued). No governance thread is currently blocked or in-flight.
>
> **Session 49 — ADR-0017 "Skills as a memory tier" is ACCEPTED; the
> skills-as-memory-tier governance arc is COMPLETE (#236 + #237, head_commit
> `8b18b3a`, `docs(constitution):`).** Two PRs landed since the #235 reconcile,
> so this single reconcile advances head_commit past BOTH (it was stale at
> `471bcb5`). #236 (`docs(adr):`, `7bf9d38`) added ADR-0017 `Proposed` —
> Cowork-drafted, Code-reviewed via the ADR-009 D3 receive sequence; #237
> (`docs(constitution):`, `8b18b3a`) ratified it (status flipped
> Proposed→Accepted) and applied the alignment. head_commit = `8b18b3a` (the
> newest *substantive* commit per `lint_status`; `8b18b3a` is
> `docs(constitution):` = substantive → it sets head_commit; the #236/#237
> merge commits `c04787b`/`7bf9d38`'s merge and the `docs(status):` reconciles
> are lint-excluded). This block is **T6** (STATUS reconcile) of the ADR-0017
> follow-on plan.
>
> **The arc, end to end.** PR #234 added the `.claude/skills/` **mechanism**
> (two on-demand skills + CLAUDE.md slimming) → #236 added the **ADR** (the
> governance rationale + decisions) → #237 applied the **alignment** (T1–T5).
> The skills-as-memory-tier arc is now governance-complete.
>
> **What #237 aligned (T1–T5).**
> - `.claude/skills/` is now **Tier 2.6** in the memory model (`CLAUDE.md` §4 +
>   the memory-architecture runbook) — git-tracked, auto-loaded by description
>   match.
> - The **D5 knowledge-placement decision rule** — binding rule→`CLAUDE.md`;
>   durable learning→`docs/lessons/`; canonical reference→`conventions`/
>   `runbooks`; task-triggered how-to→a **Skill** — and the **D7
>   skill-authoring conventions** are codified in the runbook (compact form +
>   a pointer from §4).
> - `CLAUDE.md` §1 gained the **D6** line (derived artifacts 2.5 + 2.6 carry no
>   independent precedence; canonical wins on conflict); the §10 skills row now
>   cites ADR-0017.
>
> **T6 housekeeping (this reconcile).** ADR-0017 (Accepted) recorded in Recent
> Decisions; the §50/§57 "next: draft ADR-017" earmark is **cleared** (the ADR
> now exists and is Accepted); the PR #234 skills follow-up is marked
> **governance-complete**.
>
> **Next.** The arc is closed. Open threads: (1) **OQ-B** — skill loader
> tie-break (same-named project vs global vs plugin skill) is delegated to Code
> but needs Cray approval for a probe touching global `~/.claude/skills/` (host
> state); (2) the deferred **Axis-B verification-loop** track (evaluator
> subagent + `/goal` Stop-hook gate) from the harness-engineering review. A
> **restart-bridge handoff is due this session** because #237 edited
> constitutional `CLAUDE.md` (Lesson #5 §1).
>
> **Session 49 (#234 — predecessor in this same arc) — CLAUDE.md slimmed: git +
> Code-ops procedures extracted to on-demand project skills (#234, `471bcb5`,
> `docs(constitution):`).** One
> `docs(constitution)` PR landed this turn (`docs(constitution): slim CLAUDE.md —
> extract git + Code-ops procedures to on-demand skills`), Cray-reviewed + merged
> via merge commit `d556421` (#234). This block = the session-49 #234 reconcile
> (head_commit `471bcb5` — the newest substantive commit per `lint_status`;
> `docs(constitution):` IS substantive, so it sets head_commit; the #234 merge
> commit `d556421` is lint-excluded).
>
> **What shipped.** The always-loaded constitution shrank `206→193 lines /
> 2050→1908 words` by extracting git mechanics + the Tier-2 Code-ops procedure
> into TWO new on-demand project skills under `.claude/skills/` —
> **`git-workflow`** and **`code-operational-policy`** — with **all binding rules
> retained in `CLAUDE.md`** (only the step-by-step procedure moved). This
> establishes `.claude/skills/` as the project's on-demand procedure layer,
> adopting Anthropic's Agent-Skills pattern: a bloated always-on `CLAUDE.md`
> causes rules to be ignored, so procedure belongs in on-demand skills that load
> only when relevant.
>
> **Genesis (the two-axis harness-engineering review, 2026-06-09).** A review of
> vero-lite against Anthropic's public harness guidance reached a two-axis
> verdict: **Axis A (governance / safety)** = vero-lite is at the frontier — its
> deterministic-hooks + Sonnet-classifier hybrid independently mirrors Anthropic
> *auto mode*, and `chain-cap=8` matches Claude Code's own default; **Axis B
> (task-completion / verification — the evaluator loop)** = thin, deferred as a
> separate, higher-leverage track. PR #234 is the **low-risk FIRST move** Cray
> chose off that review (Skills adoption + CLAUDE.md slimming).
>
> **Follow-up already DISPATCHED to Cowork.** Cowork is to draft an ADR (next free
> number, likely **ADR-017**) titled **"Skills as a memory tier"** — handoff
> (gitignored) at `.claude/handoffs/session-49/2026-06-09-2140-code-skills-memory-tier-adr-dispatch.md`.
> Code commits the resulting `Proposed` ADR per ADR-009 D2. The dispatch carries
> 8 OQs to resolve: tier placement, `for_llm/` overlap, the canonical-vs-derived
> rule, authoring ownership, the knowledge-placement decision rule, the precedence
> ladder, conventions, and the migration backlog.
>
> **Next.** Cowork drafts ADR-017 "Skills as a memory tier" → Code commits
> `Proposed` → Cray ratifies. Separately/optionally: begin the Axis-B
> verification-loop prototype (an evaluator subagent + a `/goal` Stop-hook gate).
>
> _Older content rotates out of this file per the **STATUS.md Rotation Policy (R1-R6)** in [`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md) (Lesson #23): Current Focus keeps the 4 newest sessions (<=8 blocks); Recent Decisions keeps the last 10 rows. Rotated blocks/rows live in [`docs/status-archive/`](status-archive/) (sessions <=46: `2026-h1-current-focus.md`; 2026-06-10 onward: `2026-h1-status.md`) and git history (Tier 3)._

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
| 2026-06-11 | **PLAN-0020 (Procedure-path tuning) COMPLETE + archived to done/ (#251–#256, `a6125c1`, session 53)** — the PLAN-0019 B-6 ring-fence follow-up. All `--dump-json`-VERIFIED on `gpt-oss:20b`/MS-S1: the Phase-1 aqua prompt nudge (PR #232, prev. UNMEASURED) worked dramatically — overall β `85.8%→100%`, aqua β `60%→100%`, overall α `70%→100%` (supply α `32.5%→100%`: model now picks `hold` not `inspect`). Latency lever: new `reasoning_mode=skip` (drop call-1 reasoning) cuts p95 `31.80s→21.62s` UNDER the 30s bar at **zero β cost** (`think_off` = dead lever). **SD-1** (widen supply-α) authorized at ratify but **SKIPPED at Step 9** — nudge made the divergence moot (0 `inspect`); anti-moving-target honored, no grader change. Also: per-judgment latency timer (#252), think-trim lever (#253), `ms-s1-ollama` skill (#254, `warm.sh` live-tested), tuning report (#255). Next: future PLAN for tiered handler grading (canonical/acceptable/forbidden — α too coarse); wiring `skip` into product path is an open audit trade-off | `a6125c1` (#251–#256) / `docs/plans/done/0020-procedure-tuning-latency-precision.md` + `benchmarks/procedure_baseline/REPORT.md` |
| 2026-06-11 | **PLAN-0020 ratified Draft→Accepted (#251, `19706eb`, session 53)** — SD-1 = widen supply-α `valid_handlers` `[hold]`→`[hold, inspect]` (later skipped at Step 9, see close row); SD-2 = re-ratify the latency bar from **8 s/per-call → ≤30 s p95 per-judgment** (reports-not-gates). Unblocked the gated MS-S1 tuning campaign | `19706eb` (#251) / `docs/plans/done/0020-procedure-path-tuning.md` |
| 2026-06-10 | **PLAN-0021 SHIPPED (#249, `3dc586a`, session 51) — the Axis-B verification loop is LIVE; both harness-review tracks complete** — goal gate (`_goal_gate.py` at the D4 seam inside `stop_continuation.py`, fail-open per ADR-0018 D4) + `goal-evaluator` 4th subagent + `/goal` (the repo's first project command) + the SD-1 narrowed-Write deny hook; +64 tests (suite 1398 passed / 22 skipped, zero regression); 7/10 case-matrix rows proven LIVE incl. the fail-open probe (`released-unevaluated` + LOUD Telegram, no wedge). F-L1: verdict→flip lands at the next non-chained Stop (OQ-8 blocking-mode promotion must account). Archived to done/ (`7d6d713`, same PR) | `3dc586a` (#249) / `docs/plans/done/0021-axis-b-verification-loop-build.md` |
| 2026-06-10 | **PLAN-0021 "Axis-B verification loop — build" landed as Draft (#247, `78b8659`, session 51)** — Cowork-drafted per ADR-009 D1, Code R2-reviewed + committed per D2/D3; renders Accepted ADR-0018 into a build plan: 6 new files (incl. the repo's first project command `.claude/commands/goal.md`, the `goal-evaluator` 4th subagent, the SD-1 narrowed-Write deny hook), exactly 3 modified files at the D4 seam, 10 ACs incl. AC-2 byte-for-byte non-interference, 10-row case matrix, VX-1..3 resolved, OQ-8 Out of Scope. R2 **F-1**: the deny hook wires via agent frontmatter, not `settings.json`. Gates on Cray ratification (SD-1: Cowork recommends NO for v1) | `78b8659` (#247) / `docs/plans/0021-axis-b-verification-loop-build.md` |
| 2026-06-10 | **ADR-0018 "Axis-B Verification Loop" ACCEPTED (Cray-ratified, session 51) — opens harness-review track 2 (the evaluator loop) on top of the at-frontier Axis-A governance layer.** A `/goal` Stop-hook gate + a `goal-evaluator` subagent that judges whether a run achieved its declared goal. **Decisions:** D1 hybrid deterministic-check + LLM-judge; D2 a `.claude/state/goal.json` run-goal artifact; D3 a 4th subagent sibling that **REFUTES not blesses** (structural guard against reasoning-blindness); D4 `_goal_gate.py` inside `stop_continuation.py`, **FAIL-OPEN** (broken/absent evaluator never blocks Stop); D5 session-Stop **warn-only v1**; D6 structural reasoning-blindness rationale; D7 formalize + augment the manual AC ritual. **SD-1 resolved = narrowed Write** (the evaluator's Write is hook-narrowed to `goal.json` only — same author-bounded pattern as `plan-drafter`/`status-scribe`). **Lineage:** #241 (`5f8073c`, `docs(adr):`) added ADR-0018 `Proposed` → **#242 (`1be60f7`, `docs(adr):`, head_commit) ratified it Proposed→Accepted** + carries the T4 STATUS reconcile (record ADR-0018 here + clear the Current-Focus Axis-B "deferred" earmark). **NEXT = T2:** Code dispatches the Axis-B build PLAN to Cowork (ADR-009 D1) → T3 (autonomy-triggers V-row) → build. OQ-8 (plugin packaging, MS-S1 local evaluator, blocking-mode promotion, PR-merge gating, auto-declared goals) + VX-1..3 stay non-binding / verify-at-execution | `1be60f7` (#241 + #242) / `docs/adr/0018-axis-b-verification-loop.md` |
| 2026-06-09 | **ADR-0017 "Skills as a memory tier" ACCEPTED — the skills-as-memory-tier governance arc is COMPLETE** — #236 (`docs(adr):`, `7bf9d38`) added ADR-0017 `Proposed` (Cowork-drafted, Code-reviewed via the ADR-009 D3 receive sequence); #237 (`docs(constitution):`, `8b18b3a`, head_commit) ratified it (Proposed→Accepted) + applied the alignment (T1–T5). `.claude/skills/` is now **Tier 2.6** in the memory model (`CLAUDE.md` §4 + the memory-architecture runbook), git-tracked + auto-loaded by description match; the **D5 knowledge-placement decision rule** (binding→CLAUDE.md; durable learning→lessons; canonical reference→conventions/runbooks; task-triggered how-to→a Skill) + **D7 skill-authoring conventions** codified in the runbook; §1 gained the **D6** derived-precedence line (2.5+2.6 carry no independent precedence; canonical wins); §10 skills row cites ADR-0017. **Arc lineage:** PR #234 (`471bcb5`) added the `.claude/skills/` *mechanism* → #236 the *ADR* → #237 the *alignment*. This (T6) reconcile records the Accepted ADR, clears the §50/§57 "draft ADR-017" earmark, and marks the PR #234 skills follow-up governance-complete. Open threads: **OQ-B** skill-loader tie-break (delegated to Code; Cray-gated probe of global `~/.claude/skills/` host state) + the deferred **Axis-B verification-loop** track. Restart-bridge handoff due (#237 edited constitutional `CLAUDE.md`, Lesson #5 §1) | `8b18b3a` (#236 + #237) / `docs/adr/0017-skills-as-a-memory-tier.md` + `CLAUDE.md` §1/§4/§10 + `docs/runbooks/memory-architecture.md` |
| 2026-05-25 | **PLAN-0009 (Phase 3 — subagent topology) RATIFIED + Ready for execution + COMMITTED** — Cowork drafted under interim ADR-009 D1 phasing; Cray adjudicated all 4 OQs (OQ-1…OQ-4) 2026-05-25 (WebFetch for Explore; no new ADR — execute ADR-013 D1; subagent identity folds with ADR-013 OQ-3 in Step 1; PLAN status vocabulary). Cowork → Code dispatch handoff at `.claude/handoffs/session-10/2026-05-25-1240-cowork-plan0009-review-dispatch.md` `validate_handoff.py` clean (K-1 / ADR-009 D3 substitute — 9 required fields, actor=cowork / phase=dispatch / status=READY / suffix=dispatch, ISO-8601 +07:00, filename matches `_FILENAME_RE`). Code fact-pack / R2 review clean across 9 citations (0009 next free; ADR-013 D1/OQ-1/OQ-3 quoted verbatim; PLAN-0008 4 carry-overs accurate; PLAN template structure intact; Cray verification-rigor directive present in Step 6 + Verification). Status flipped Draft → Ready for execution in commit `d10073e` on `feat/plan0009-subagent-topology` (single-doc, worktree-OFF per CLAUDE.md §11). **2 reconciliation findings folded** into Current Focus: (1) `.claude/` readability — K-2 is write-block NOT read-block (research-note §6); OQ-D load-bearing forcing fact remains K-1 (Cowork can't run `validate_handoff.py`), substantive deferral stands. (2) Working-tree divergence — git worktree sees neither uncommitted new files nor gitignored paths (research-note §6.1, reproduced live this session); not K-1/K-2 but checkout-resolution mismatch; design implication for Phase 3.5 if approved. **CLAUDE_TIER / session-identity unification** confirmed correctly folded in PLAN-0009 Step 1 (one mechanism, 3 identity cases: main Code may commit, Plan/Explore subagent must NOT, scheduled Local Code session may [Phase 3.5 HELD]). **Phase 3 execution gated on PR merge. HOLD Phase 3.5** (research-note §7.5 local scheduled-task poller option SURFACED, not decided) | `d10073e` / `docs/plans/0009-subagent-topology.md` + `.claude/handoffs/session-10/2026-05-25-1240-cowork-plan0009-review-dispatch.md` |
| 2026-05-25 | **PLAN-0008 AC-1 CORROBORATED via Auto mode bonus run + layer orthogonality CONFIRMED in production** — A second AC-1 live verification run (2026-05-25 00:30–00:32) using **Mode = Auto** in a fresh worktree session: task `"สร้าง docs/CHANGELOG.md สรุป Phase 2 PRs #9-#17, commit บน branch ใหม่, ไม่ต้อง push"`, single Cray paste, no further input. Result: **≥ 4 auto-continues, 0 permission prompts (Auto mode skipped them all), 0 Telegram pings, terminal pause at commit done** (followed explicit "ไม่ต้อง push" instruction — no over-step). Commit `6dc808c` on branch `chore/phase2-changelog` (unpushed per instruction). **Layer orthogonality confirmed**: Mode (PreToolUse harness layer) ↔ PLAN-0008 (Stop classifier layer) operate independently — Auto mode eliminates per-tool prompts without changing Stop-continuation decisions. **Minor finding for PLAN-0009 carry-over**: `_loop_counter._normalize_file_path()` strips main-repo prefix but does not collapse worktree path suffix (L1 counter key showed `.claude/worktrees/busy-bose-eedc8f/docs/CHANGELOG.md` instead of `docs/CHANGELOG.md`). Non-blocking; per-session isolation works correctly. Both AC-1 evidence runs documented in Current Focus comparison table. Cost: ~$0.004 (4 classifier calls × ~$0.001) | PR #20 amendment / `docs/STATUS.md` |
| 2026-05-25 | **PLAN-0008 AC-1 VERIFIED — Phase 2 fully audited** — Cray ran the live AC-1 task in a fresh Code session (task: *"ตรวจ ruff + mypy ทั้ง project, แก้ warning ถ้ามี, commit"*, single Cray paste, no further input). Agent self-continued **≥ 5 consecutive turns** without Cray paste (initial scan → file inspection → plan → branch creation → 5 file fixes → re-verify → tests → commit), then paused at the `git push` boundary asking permission — classifier correctly identified push as state change outside worktree per `feedback_state_change_outside_worktree.md` memory pattern. **0 Telegram pings** (no `cap_reached`, no L1–L4 false-positives). `stop-chain.json` `depth: 0` at end (consistent with terminal pause resetting chain). Side effect: the session surfaced 21 project-wide mypy errors in `tools/` + `tests/` (outside the pre-commit gate scope) and shipped a cleanup commit `8fef3a5` — PR #18 follows separately. Confirms classifier conservatism bias (spurious pauses > spurious proceeds, per OQ-B) works in production. Phase 2 all 4 ACs now VERIFIED; entry conditions for PLAN-0009 (Phase 3 — subagent topology) met | PR #19 amendment / `docs/STATUS.md` + closeout handoff §1 |
| 2026-05-25 | **PLAN-0008 Phase 2 COMPLETE — Step 8 closeout MERGED** — PR #17 → `main` (`79fe373`), single `feat(claude)` commit `b3657d5` + merge. AC matrix at merge time: AC-2/AC-3/AC-4 VERIFIED; AC-1 deferred to live Cray-supervised observation (subsequent AC-1 row above closes this). Step 8 deliverables: +2 E2E tests (test_l3_traceback_inline_fires_on_threshold + test_l2_resets_on_pass_for_same_nodeid; 387 → 389 pass / 6 skip); closeout handoff at `.claude/handoffs/session-10/2026-05-25-0130-code-plan0008-phase2-closeout.md` (gitignored local working note per CLAUDE.md §11); `git mv docs/plans/0008-...md docs/plans/done/`; STATUS final bump. Phase 3 (subagent topology, ADR-013 D1 phased) entry conditions met. **Reflexive H1 hook fire on the closeout handoff frontmatter** (`phase: completion` initially invalid; corrected to `phase: closeout` per enum) — N=3 production-validation events through this session (L1 in PR #15, L1-attempt in PR #16, H1 in this PR) prove the deterministic + classifier-mediated layer is reachable from real agent activity | `79fe373` (PR #17) / `docs/plans/done/0008-harness-autonomy-layer-phase-2.md` |
| 2026-05-25 | **PLAN-0008 Step 7 (Phase 2 integration tests + mypy hook coverage extension) MERGED** — PR #16 → `main` (`9100e65`), single `test(claude)` commit `d870d76` + merge. New `tests/handoffs/test_phase2_integration.py` with 15 E2E scenarios driving real subprocess invocations of all 3 wired Phase 2 hooks against a local mock HTTP Sonnet server (ephemeral 127.0.0.1 port via `socketserver.TCPServer` + threading daemon; `$CLAUDE_SONNET_API_URL` override; no live network). Coverage: Stop↔classifier wiring (proceed→block, pause→no-block, fail-closed, re-entry guard — mock receives 0 requests = negative proof); chain-cap fail-safe + cap_reached Telegram; observer→state→PreToolUse deny on L1+L4 + Cray-E.4 payload assertion; L4 reset on success; L2 inline Telegram on pytest-fail threshold; L1 turn-boundary survive vs reset; chain depth progression. Pre-commit `mypy` glob extended `^(services\|verticals)/` → `^(services\|verticals\|\.claude/hooks)/` (closes Step 1 follow-on; all 9 hooks pass `--strict`). 372 → 387 pass / 6 skip (+15). Per-test isolation via `tmp_path` for state + classifier fallback path + telegram capture + chain file. AC-3 demonstrated E2E for the first time | `9100e65` (PR #16) / `tests/handoffs/test_phase2_integration.py` |

## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten (full table: PLAN-0005 §8.1): rule-based recommender → **ADR-010 ACCEPTED (2026-05-22) → PLAN-0006 next** (LLM reasoning hook); minimal approval gate → **ADR-011+** (audit framework — trigger: first design-partner data / PDPA review); no mapping layer → **dbt/SQLMesh** (trigger: first non-synthetic source); hand-authored ORM → **"ORM emitter"** Rule-of-Three candidate (trigger: 3rd vertical / DDL↔ORM parity-test drift); base Postgres only → **PLAN-002** (pgvector/AGE — trigger: semantic + graph features); explicit registry → **ADR-006 D3 L2** (trigger: vertical #2/#3 or `new-vertical` generator). *(per Cray note 2026-05-21)*
- [ ] **Phase-enum amendment** — add `consultation` (or equivalent Q&A-round value) to canonical Phase enum (Q15 of `2026-05-20-0245-code-plan003-pre-draft-consultation-reply.md`); requires touching `tools/handoffs/_schema.py` + `docs/conventions/handoff-frontmatter-schema.md` + validator tests; PLAN-004 Phase B adjacent. *(Deferred per R-9, 2026-05-20)*
- [ ] **Cleanup stale `ontology/README.md`** — 2026-05-05 PLAN-001 artifact; ontology directory canon now lives at `verticals/<name>/ontology/<name>_v0.yaml` per ADR-006 D1 / ADR-008 D5; superseded by PLAN-003. *(Deferred per R-9 cohort, 2026-05-20)*
- [ ] **PLAN-004 Phase B/C — DEFERRED (backlog, post-PLAN-003):** validator-scope exclusion (`README.md` / `_rename-map.md`, manifest §4.2/§6.1) + Cat G `references_*` autofix + Phase C handoff dashboard + OQ-2 systemic candidate (effective-vs-authored `status:` / archival flag so dead handoffs don't surface as actionable in the dashboard) + **validator warning-swallow bug** — `tools/handoffs/_schema.py` `_build()` (lines ~302–306) returns `Frontmatter` and discards its local `errors` list when no hard error exists, so `_check_unknown()` WARNING-severity findings (e.g. unknown field `brief-number`) are unreachable on otherwise-valid files; fix to surface warnings + add a regression test *(found 2026-05-22 dog-fooding the 4 Cowork LLM-hook handoffs; Cray routed → Phase B)*
- [ ] **ADR-NN (TBD, ≥ ADR-014) + PLAN-002** — Custom Postgres image with extensions (ADR-011 earmarked for the audit framework, ADR-012 taken, ADR-013 taken by autonomy axis relocation; floor bumped from ≥0013 to ≥0014 on 2026-05-23 per ADR-013 T6)
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (low priority)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)

## Next Steps

1. **PLAN-0005 §8.1 revisit register** — remaining deferred-foundational simplifications at their batch boundaries (audit framework → ADR-011+, mapping layer, ORM emitter, base-Postgres → PLAN-002 (≥ADR-014), registry discovery).
2. **Partner-trial readiness gaps** — `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` awaits a dedicated Cray discussion.
3. **Deferred (backlog)** — PLAN-004 Phase B (validator-scope exclusion; Cat G `references_*` autofix; validator warning-swallow bug) + Phase C (handoff dashboard); PLAN-002 custom Postgres image (≥ADR-014).
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
