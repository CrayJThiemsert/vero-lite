---
last_updated: 2026-07-26T21:25:48+07:00
session: 175
current_batch: "s175 — 4 PRs, 0 open: #920 pins every vertical's ACTION factory offline; #921 fixes 4 stale cross-refs; #922 PLAN-0094 Step 3 warn-then-deny; #923 makes a masked shell failure unbelievable."
current_actor: code
blocked_on: "Nothing. main=04c94e4; suite 3296 passed / 8 skipped; mypy 110 files + ruff 501 files clean, run in the main tree; 0 open PRs. Tree clean but for the 2 standing KEEP untracked paths."
next_action: "PLAN-0094 Step 3 DONE; Steps 4-6 remain — Step 4 needs a settings.json diff, so Cray per-diff approval. Candidate C unblocked by Cray's live-API decision but needs a new PLAN via plan-drafter (G2)."
head_commit: 04c94e4
recent_commits: [04c94e4, 6118d24, 3b3b666, 8f868c6, 59c81a6, 924c8d6, 65c6953, ff14137, 3612d33, 1e8e49a]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 175, 2026-07-26 (head_commit `a3a9c66` → `04c94e4`) — the session
> the harness stopped letting a failed command look like a success. Four PRs
> merged (#920–#923), 0 open. Two of them are the same defect class at two
> layers: a guard that fires but says nothing legible (#920), and a shell that
> reports `0` for a command that failed (#923).**
>
> **(#923 — a masked command failure is now impossible to believe silently.)**
> Cray caught that a `| tail -6` hid a traceback, swallowed an exit code, and a
> FAILED script was reported successful. Probing found **three** hazards, and
> the reported one was the smallest. (1) A bare `$` inside `wsl bash -lc`
> expands **one shell layer early** — `$?` reads `0` for a failed command and
> `$(pwd)` resolves *before* a preceding `cd`; escaped `\$?` returns the true
> `1`, but only with a single-quoted outer arg. (2) Unmerged **stderr
> OVERWRITES stdout** byte-for-byte — one stderr line erased all 8 stdout
> lines, 3/3 runs — previously unrecorded anywhere in the repo. (3) A pipe into
> `head`/`tail` reports the **truncator's** status, and the inverse `| head`
> under `pipefail` yields 141 SIGPIPE. Three changes per the §4 routing rule:
> Lesson #0007's mechanism **CORRECTED and reclassified `was an error`** (the
> harness does not "fail to propagate exit codes"; a two-character escape
> recovers `$?`, and the over-generalization cost two months of stderr-parsing
> workarounds), a binding **CLAUDE.md §8** rule, and a `_shell_hygiene_warning`
> **PostToolUse advisory** — deliberately not a PreToolUse deny, because the
> harm is not running the command but *believing* its output, which is knowable
> only after it runs. It attaches to a hook already registered for Bash, so
> `.claude/settings.json` stays untouched. Hazard 2 is deliberately NOT
> enforced: whether a command emits stderr is not knowable from its text, so a
> check would either miss most cases or warn on every call. The advisory caught
> a real bug in the author's own command on its first live use.
>
> **(#922 — PLAN-0094 Step 3: L1 warns first, denies on the second trip.
> Closes AC-3 (final surface), AC-4, AC-5.)** L1's path-class threshold becomes
> the **WARN** bar (observer ping + agent-visible advisory, edit ALLOWED); the
> gate denies only at threshold + `L1_GRACE_BUDGET` (3, Cray-ratified OQ-1) =
> **9 code / 18 doc**. **L4 is untouched** at a flat 6. An additive
> `CounterEntry.warned_at` dedupes the warn. `.claude/settings.json` NOT
> touched. **One deliberate deviation from the Step 3 spec, pinned by a test:**
> the deny message does NOT name the P3 stop-ack, because P3 ships at Step 5
> and advertising an unbuilt exit would recreate the exact defect AC-3 closes.
> Non-vacuity by 3 mutations, each RED count predicted before the run and
> matched. The AC-3 grep oracle caught the author quoting the banned anchor
> phrase in a docstring; the warn then fired live on the author's own 6th edit
> mid-implementation.
>
> **(#920 — every vertical's ACTION client factory pinned offline.)**
> `ActionStepExecutor.client_factory` defaults to a **LIVE** `OllamaClient`
> against MS-S1, so dropping one kwarg from any vertical factory is a silent
> CLAUDE.md §8 host-state change. A parametrized guard now asserts at
> **REGISTRATION**, across all six procedure-shipping verticals, that the
> factory is not the live default and does not produce an `OllamaClient`.
> **The measurement corrected the draft's own premise:** it claimed five
> verticals were unguarded, but mutation-testing each showed the existing suite
> DOES catch it (aquaculture 3 / building_materials 1 / energy 2 /
> fleet_maintenance 6 / supply_chain 7 failures). The real defect is therefore
> not absence but **shape** — the signal is opaque (`BaseExceptionGroup:
> unhandled errors in a TaskGroup`), incidental (only where a vertical happens
> to own an e2e ACTION test), and pytest-only (the production registrations in
> `main.py` / `cli.py` run under neither). The assertion is "not the live
> default", never "is <a specific stub>": procurement injects its own
> same-named PO-shaped stub.
>
> **(#921 — four stale cross-references, found by a five-agent grounding
> sweep.)** Repo claims verified against code, not against each other.
> `query_step.py` still asserted the PLAN-0048 SD-3 "deprecate-in-place, never
> migrated" stance that **PLAN-0062 SD-C overturned**, leaving two engine
> docstrings in live contradiction; `supply_chain/procedures_factory.py` cited
> `hero_demo/run.py:278` (actual `:298`); PLAN-0076's Code-anchors block named
> four symbols PLAN-0078 PR-5 retired (now grep-clean); PLAN-0094 gained a
> line-citation drift table + AC state. All four classified **`superseded by
> new info`**, not `was an error`.
>
> **Governance, recorded so it does not read as precedent.** ADR-009 D1
> reserves `CLAUDE.md` authorship to Cowork; Cray granted Code a **one-off,
> explicitly scoped** exception for the #923 §8 edit — reason given: the
> problem is important, the context was already warm, and the evidence was in
> Code's hands. Cray ratified; it is recorded in the CLAUDE.md footer and the
> PR. **Normal routing is unchanged.** Separately, **Cray settled the
> demo-target fork: the LIVE-API shape ("แบบ B"), not static-only** — which was
> gating both Candidate C (the Docker image) and the future MS-S1 hosting ADR,
> and makes **Candidate C the long pole** rather than an optional alternative.
> And **PLAN-0094 Step 1's soak reported no anomalies** on Cray's live loop,
> which released Step 3.
>
> **Three deferred corrections applied to this file** (found by the #921 sweep,
> held back for this reconcile): the **Demo-card UX TODO is
> closed-with-residue** — the s74 trust shape ships on both the story and
> monitor surfaces with anti-regression comments citing the PLAN-0035 §SD-3
> amendment (`story.css`, `view-story.js`, `view-monitor.js`), residue at most
> one toggle on the monitor step card; **Rock-3 / O-2's wording is corrected**
> — the derived fields ALREADY migrated to declared `transform` ✔ (PLAN-0078
> PR-1 #762, AC-2 ticked), so the residue is ONLY the cardinality-changing
> `candidate_quotes` nest; and the **duplicated `git.md` extraction TODO** is
> de-duplicated to one row, noting its substance is effectively discharged by
> the `git-workflow` skill and that **`CLAUDE.md:176` holds a DEAD link** to a
> non-existent `docs/conventions/git.md` — a **Cowork** round-trip, since the
> #923 exception was scoped to §8 only.
>
> **State at close:** `main` `04c94e4`, suite **3296 passed / 8 skipped**,
> `mypy services/` clean (110 files), ruff + ruff-format clean (501 files) —
> all run in the main tree. 0 open PRs; tree clean but for the two standing
> KEEP untracked paths (`.claude/benchmark-results/`, `.claude/launch.json`).

> **Session 174, 2026-07-25 (head_commit `6fb89b8` → `a3a9c66`) — the session
> MS-S1 stopped being an inference appliance and became an administrable host,
> and the constitution's gated surface was widened to match. Three PRs merged
> (#916, #917, #918), 0 open. The headline is not "three PRs landed" — it is that
> a second channel onto the LLM box changed what §8's host-state gate has to
> cover, and §8's one concrete illustration was pointing at a port.**
>
> **(#916 — the channel, and the §4 three-layer split.)** ADR-002 opened TCP
> 11434 and nothing else, so box-level state on MS-S1 was undiagnosable without
> walking to the machine. Cray opened a second **LAN-only** channel — OpenSSH on
> TCP 22, firewall scoped `Domain, Private`, the same scoping as the Ollama rule
> (it had been `Private`-only, so the box was never publicly exposed). Verified
> with `ssh -o BatchMode=yes` → `REMOTE_OK` / `CRAY-MS-S1-MAX`; **BatchMode
> forbids interactive fallback, so that proves publickey auth rather than a
> silent password prompt** — a distinction a plain `ssh` smoke cannot make. The
> knowledge then split three ways per the CLAUDE.md §4 placement rule, and **that
> split is the reusable part**: the **binding rule** stays in `CLAUDE.md` §8, the
> **setup + four traps + recovery** in `docs/runbooks/ms-s1-ssh-access.md`
> (Tier 2), and the **task-triggered operating procedure** in a new
> `.claude/skills/ms-s1-admin/` (Tier 2.6). Neither derived artifact carries the
> rule — the §4 bright line, since a skill that fails to trigger would silently
> drop it.
> **(the trap worth carrying.)** A `$` inside `wsl bash -lc "ssh ms-s1 '...'"`
> passes through **two** bash layers and is expanded away **with no error** —
> `Write-Output "got:[$PSVersionTable]"` returned `got:[]`, a silent empty rather
> than a failure. Escaping survives exactly one layer. The documented answer —
> write a `.ps1` and pipe it via `powershell -NoProfile -Command -` on stdin, so
> no shell ever parses the payload — was verified end-to-end. That same probe
> measured `Elevated=True`: an OpenSSH session for an administrator carries a
> **full, un-UAC-filtered admin token**. Also a drift fix: `ms-s1-ollama` pointed
> the binding rule at "the active PLAN / handoff (e.g. PLAN-0020)", which session
> 62 had already moved into `CLAUDE.md` §8 and which is now archived. Classified
> per §6 as **`superseded by new info`, not `was an error`**.
>
> **(#918 — §8 rescoped, net +1 line.)** The rule's **substance did not change**:
> "any change to global / host configuration outside the worktree" already gated
> SSH-borne changes. What failed was the **illustration** — MS-S1 was exemplified
> as `192.168.1.133:11434`, a *port*, which post-SSH reads as a scope boundary
> rather than an example, leaving the one concrete anchor a hurried reader takes
> away as the narrower half of the truth. Three drafting calls: (1) the literal
> address is **dropped entirely**, not merely the port — §5 Hardware already
> carries it, and a second copy is the ADR-0017 D6 drift class this edit exists to
> undo; (2) the verb is **"altering"**, not "any action over SSH" — gating
> *access* rather than *change* would over-gate read-only diagnostics, a
> substantive tightening outside the dispatch's remit; (3) an **elevation warning
> was considered and declined** — it changes no behaviour (§8 already forbids the
> action without a go, unconditionally) and §8 states no other rule's rationale;
> the hazard rides on the adjective **"administrative"**. **Honest caveat,
> ratified knowingly:** this is a hair wider than pure re-illustration — "host
> *configuration*" arguably did not cover writing an arbitrary file on MS-S1;
> "the gated surface is the whole host" does. Routing: **Cowork drafted the text**
> (ADR-009 D1 — Code may not author `CLAUDE.md`, and `plan-drafter` is
> hook-denied) and corrected Code's reasoning on the elevation fork; **Code R2'd,
> ruled on two returned flags (both rejected), surfaced the widening, applied and
> committed** (D2); Cray ratified the exact wording.
>
> **(#917 — PLAN-0094 Steps 1+2: the reset that was never wired.)** AC-1 + AC-2,
> plus AC-3 in part. The subagent-completion L1 reset shipped 2026-06-08 with a
> handler, green tests and **no event registration that could ever invoke it** —
> dead for seven weeks while three documents advertised it live; s172 followed
> that advice and lost most of a session. **Two independent defects, both fixed.**
> *Route:* a new `SubagentStop` entry, matcher `*`, invoking the observer;
> `main()` now branches on `hook_event_name` **before** `tool_name`; the dead
> `("Task","Agent")` branch deleted. *Scope:* the reset clears the completing
> agent's **own** recorded edits (new additive `subagent_touched:
> {agent_id: [targets]}` state), not `turn_touched` — restoring the documented
> turn-scoped form would have created a **self-unlock path**, letting the main
> agent launder its budget through any zero-edit spawn. Cray ratified that
> divergence from Lesson #0021 §3 **as a decision**. Class-killer: a new
> `tests/handoffs/test_settings_hook_wiring.py` parses `settings.json` **as data**
> and fails on a registration removal alone — it pins the defect class, not the
> instance.
> **(evidence.)** RED-first on every new assertion except one, which was **proved
> non-vacuous by mutation** (reverting to turn-scoped semantics reddens it plus
> three siblings; the file was restored from a `/tmp` copy, byte-identical, never
> `git checkout`). Suite **3244 → 3252 passed / 8 skipped** — the exact +8
> predicted before the run. `mypy` clean (110 files), `ruff` clean (501 files),
> both run in the **main tree**. Thresholds `6` / `15` **byte-unchanged**. Two ACs
> deliberately close later, Cray-approved: **AC-1 (ii)** (`PostToolUseFailure`
> registration) at Step 4, and **AC-3's third surface** (the deny-message anchor in
> `pretooluse_loop_detect.py`) at Step 3, per D2's do-not-edit-twice instruction.
> **Steps 3–6 remain unbuilt and are gated on Step 1 soaking on Cray's live loop.**

> **Session 173, 2026-07-25 (head_commit `ca39841` → `6fb89b8`) — the session that
> found the loop-detect guard was measuring the wrong quantity. Two PRs merged
> (#912, #914), 0 open. The headline is not "a guard was tuned" — it is that L1
> counted only SUCCESSFUL edits, so it was blind to the exact thrash it exists to
> catch, and one of its three documented escapes had never been wired at all.**
>
> **(what shipped.)** **#912** bounds the lifetime of `.claude/state/loop-counter.json`,
> which was effectively immortal: `load_counter` minted fresh state only on a missing
> or corrupt file, and the `session_id` it records was written but never compared. Two
> independent guards now bound it — **age-out** (entries whose `last_updated` is older
> than `COUNTER_MAX_AGE_HOURS` = 6 h are dropped on load) and a **session boundary**
> (re-mint when the recorded id differs from the hook payload's). **#914** lands
> **PLAN-0094** (Draft) + **Lesson #0033**.
>
> **(the finding that reframed the work.)** The brief arrived with five findings from
> s172; all five held, but **three were worse than reported** and two changed the fix.
> (1) `PostToolUse` fires **only on success**, so a failed Edit never reaches the
> counter — probed live: a successful Write took it to 1, a mismatched-`old_string`
> Edit left it at **1**. Six good edits score 6; six retries of one broken anchor score
> **0**. No threshold value separates those, which is why PLAN-0094 changes none.
> (2) `session_id` is not unreliable, merely **unread** — it is a required field on every
> hook payload and three other hooks in this repo already read it. (3) The
> subagent-completion reset is not "denied", it is **unwired**: `settings.json`
> registers `PostToolUse` for `Write|Edit` and `Bash` only, so the handler is dead code
> that has never run — while the registry row L1, Lesson #0021 §3, **and the deny
> message itself** all still advertise it as live. That last one plausibly explains
> STATUS's repeated "a subagent inherits the exhausted counter": the agent was
> following the deny's own advice.
>
> **(evidence.)** Suite **3043 passed / 204 skipped**, 5 failed — the documented
> worktree false-RED set by exact name and count. The 5th touches `stop_continuation.py`,
> which this change edits, so it was **isolated rather than assumed**: it fails
> identically with the change removed. `ruff check` + `ruff format --check` clean (497
> files); `mypy services/` clean (110 files). **Non-vacuity probe:** with the logic
> neutered and the API kept, **10 of the 27 new tests go red** (8 age-out, 2 session
> boundary) — they bite on behaviour, not symbol presence. **MS-S1 never contacted.**
>
> **(governance — the R2 catch that improved the argument.)** `plan-drafter` authored
> PLAN-0094; Code R2 returned three corrections, all applied. The material one: the
> draft's §Why-no-ADR **missed ADR-0013 row E.4** (`0013:90`), which specifies the L1
> consequence as **"pause + Telegram alert"** — not deny. So the hard deny went
> **beyond its own Accepted-ADR mandate**, and P2's warn-first moves L1 *toward* E.4
> rather than away; since E.4 also names the number ("loops > 6 rounds"), keeping 6
> while fixing the proxy is fidelity, not drift. The second correction killed a
> **vacuous grep oracle** (AC-3's anchor string does not exist contiguously in source —
> it is split across an f-string boundary — so the check would have passed forever).
> Cray ratified OQ-1 `G=3`, OQ-2 full fresh budget, and **SD-2 as a decision, not a
> diff approval** — it changes what Lesson #0021 §3 recorded as the fix. The
> ratification was recorded in the PLAN **before** merge so main never carried a
> document reading "awaiting Cray" on settled points.
>
> **(process — two mistakes, both caught and reported.)** A 216-line test block was
> written into the **main tree** by using the wrong path root, onto the concurrent
> s172 session's branch; caught because `pytest -k` selected 4 tests instead of ~27.
> Recovered /tmp-copy-first, then `git checkout --` scoped to that one pathspec after
> verifying the diff was 100% mine; s172's work was unaffected (its 5 files landed as
> `82e518c`, without the stray file). Second: the first commit attempt ran pre-commit
> with a PATH that omitted `uv`, so two hooks failed and **no commit was created** —
> verified by HEAD, not by the message. #912 then hit `strict` branch protection when
> s172's PLAN-0093 PRs landed ahead of it, costing a main-merge + full re-gate.
>
> **(Tier-0 correction.)** The private memory prescribing "spawn a subagent to reset
> L1" was describing a mechanism that cannot fire; corrected and classified
> **`was an error`**, not `superseded`. s172 then independently corroborated it from
> the other side — it had run that recipe verbatim, synchronously, with the target in
> `turn_touched`, and the counter did not clear. Static read and live observation
> converged.

> **Session 172, 2026-07-25 (head_commit `ca39841` → `9786c63`) — PLAN-0093 COMPLETE
> 8/8, archived to `done/`. Three PRs merged (#910 plan, #911 build, #913 closeout).**
> _[Block reconstructed in s173 from git + the s172→s173 handoff, not authored by that
> session — the narrative is thin on purpose; the archived PLAN is the record.]_
>
> **(what shipped.)** The LLM-arm degrade disclosure — no silent arm swap. Step 1
> disclosed which arm phrased an NL answer (`7a852e3`); Step 2 made the rule fail-safe
> say it is a fail-safe (`b73b19c`); Step 3 + 3b projected the authoring arm over HTTP,
> including the insights run-corpus path (`e0ed8d1`, `82e518c`); Step 4 fixed
> `LLM_RETRY_BUDGET` being **inert on the governed path** (`27ef271`). Full record:
> `docs/plans/done/0093-llm-arm-degrade-disclosure.md`.
>
> **(what it produced for s173.)** While building Step 1 on
> `services/engine/nl_query.py` this session hit an L1 deadlock and ran the documented
> subagent-reset escape verbatim — foreground, target in `turn_touched`. The counter
> did **not** clear and the next Edit was denied again. It escaped via a
> match-exactly-once-or-abort Python replacement (Cray-approved after the pause the
> deny message asks for) plus a normal commit. That observation became the s173 brief
> and is the empirical half of the F3c finding above.

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
| 2026-07-26 | **s175 — the harness stopped letting a failed command look like a success.** #923: Lesson #0007's mechanism CORRECTED and reclassified `was an error` (a bare `$` expands one shell layer early; `$?` is not unreadable) + a binding CLAUDE.md §8 rule + a `_shell_hygiene_warning` PostToolUse advisory. #922: PLAN-0094 **Step 3** — warn at T, deny at T+G (9 code / 18 doc), L4 flat 6; AC-3/4/5 closed. #920 pins all six verticals' ACTION factory offline at REGISTRATION; #921 fixes four stale cross-refs. **Cray: demo target = the LIVE-API shape** → Candidate C is the long pole. ADR-009 D1 one-off Code-authors-§8 exception — **not precedent**. Suite 3252 → **3296** | `04c94e4` (#923 merge, head_commit) / `3b3b666` (#922) / `59c81a6` (#921) / `65c6953` (#920) / `docs/lessons/0007-harness-exit-code-artifact.md` |
| 2026-07-25 | **s174 — MS-S1 stopped being an inference appliance, and CLAUDE.md §8's gated surface was widened to match.** #916 opens OpenSSH on TCP 22, LAN-only (`Domain, Private`), verified with `BatchMode=yes` — which proves publickey auth, not a silent password prompt; the knowledge splits per §4 — rule in §8, how-to in the runbook, procedure in a new `ms-s1-admin` skill. #918 rescopes §8, net +1 line: substance unchanged, its `…:11434` *illustration* was reading as a scope boundary (Cowork drafted → Code R2'd + committed → Cray ratified). #917 lands PLAN-0094 Steps 1+2 — the `SubagentStop` L1 reset, scoped to the completing agent's OWN edits (turn-scoped would be a self-unlock path; Cray ratified the divergence from Lesson #0021 §3); suite 3244 → **3252** | `a3a9c66` (#918 merge, head_commit) / `2cda070` (#917) / `c9050b9` (#916) / `docs/runbooks/ms-s1-ssh-access.md` + `docs/plans/0094-loop-detect-non-progress-and-reset-paths.md` |
| 2026-07-25 | **s173 — the L1 loop-detect guard: its unit of measurement was wrong and one documented escape was never wired.** #912 bounds the loop-counter state lifetime (age-out 6 h + a session boundary read from the hook payload, which `resolve_session_id` never consulted). #914 lands **PLAN-0094** (Draft) + **Lesson #0033**. Probed live: `PostToolUse` fires only on success, so L1 could not see a failed edit at all — 6 good edits score 6, 6 retries of one broken anchor score 0, so **no threshold separates them** and PLAN-0094 changes none. `_handle_agent_completion` is **dead code** (no `PostToolUse` Task/Agent matcher); the registry row L1, Lesson #0021 §3 and the deny message all still call it live. Cray ratified **OQ-1 `G=3`, OQ-2 full fresh budget, SD-2 subagent-scoped reset** (a decision, not a diff approval — it changes a recorded lesson) | `6fb89b8` (#914 merge, head_commit) / `3383697` + `2d09002` (#912) / `docs/plans/0094-loop-detect-non-progress-and-reset-paths.md` + `docs/lessons/0033-raising-the-threshold-is-not-fixing-the-unit.md` |
| 2026-07-25 | **s172 — PLAN-0093 COMPLETE 8/8, archived to `done/` (#913): the LLM-arm degrade disclosure, no silent arm swap.** Four steps — disclose which arm phrased an NL answer, make the rule fail-safe say it is a fail-safe, project the authoring arm over HTTP (incl. the insights run-corpus path), and fix `LLM_RETRY_BUDGET` being **inert on the governed path**. Its L1 deadlock on `services/engine/nl_query.py` — where the documented subagent-reset escape was run verbatim and did **not** clear the counter — became the s173 brief and the empirical half of that finding | `9786c63` (#913 merge) / `55d2007` (#911) / `30285bc` (#910) / `docs/plans/done/0093-llm-arm-degrade-disclosure.md` |
| 2026-07-25 | **s171 — PLAN-0088 COMPLETE, 13 live ACs, archived to `done/` (#908).** AC-9b BUILT + PASSED (#907): live translate/phrase stages wired (reusing `nl_query`); one MS-S1 `gpt-oss:20b` smoke → grounded count 120 = the seeded corpus. A test premised on an unwired seam RAN the model twice unasked → a socket-level `_no_outbound_network` guard now makes an off-box call impossible. Suite 3189 → **3203/8** | `ca39841` (#908 merge, head_commit) / `c21c0aa` + `e443696` (#907) / `docs/plans/done/0088-*.md` |
| 2026-07-24 | **s171 — PLAN-0088 Step 6 BUILT (#905): the four Group-B primitives + the AC-10 carrier proof, under SD-9 (a2)'s precedent so no new SD was needed.** Reopening the corpus found FOUR shapes it wrote that the engine never does (the AC-2 class), and B3's refusal kind was a BIJECTION of procedure — its oracle could not have failed. Mutation probe 4/4 as predicted. Suite 3178 -> **3189**. Plus **#904**, the STATUS rotate A+C: 61,748 -> 48,920 B, window untouched | `08304a0` (#905 merge, head_commit of record) / `023f24a` / `a3716db` / `d863078` + `96fbdcc` (#904) |
| 2026-07-24 | **s170 — PLAN-0088 Steps 4 / 4.5 / 5 BUILT (#895/#900/#902); SD-9 RULED (a2) by Cray (#898, surfaced #897).** Readers A4 (audit-readiness, AC-7) + A1 (NL query over runs, AC-8/AC-9), three new primitives; SD-9 settles that the substrate grows in `run_analytics.py` **only** and strikes `agent_id` + `trigger` from v1. Suite 3150 → **3178**. **AC-9b (live MS-S1) OPEN — host-state.** | `5d02538` (#902 merge, head_commit of record) / `46f0ba1` (#898) / `7150c07` (#895) / `docs/plans/done/0088-cross-run-read-substrate-and-run-insight-readers.md` §SD-9 |
| 2026-07-24 | **s169 — PLAN-0088's design layer ADJUDICATED: SD-1…SD-8 ratified in ONE typed pass (#889); SD-8 = (a) ELIMINATE struck `list_runs_page` + AC-12**, so the substrate ships aggregate-only, `GET /runs` is untouched, and listing pagination moves to the future monotonic-`sequence`-column PLAN. AC-12 kept as a tombstone so AC numbering stays stable (live count 13). Step 0 DISCHARGED → build-ready. Detail: the s169 CF block above | `dd16267` (#889) / `8d1be34` (#888) / `docs/plans/done/0088-cross-run-read-substrate-and-run-insight-readers.md` §Surfaced decisions |
| 2026-07-24 | **s169 — PLAN-0088 Steps 1–3 BUILT (#890/#891/#893): the cross-run read substrate (AC-1/2/3/11) + reader A2 (`GET /insights/impact`, AC-4/5) + reader A3 (`GET /insights/flow`, AC-6).** Seven read-only async primitives, a seeded 250-run corpus with a plain-Python oracle independent of the SQL under test, two AST guards. `ImpactReport` carries **no** cross-currency total and must never gain one (S7). Suite 3109 → **3150**. Detail: the s169 CF block above | `9e26195` (#893) / `8393af8` (#891) / `b1e12d1` (#890) / `services/db/run_analytics.py` |
| 2026-07-23 | **s168 — PLAN-0091 COMPLETE 10/10 + ARCHIVED (#883–#885): closing it exposed that the emitted package could not LOAD and `vero-lite scaffold` wrote NOTHING — both invisible to a green suite (a suite aimed at the library cannot see a dead entry point).** Suite 3083 → 3109; honesty correction: s167's "8/10" was 7/10 | `c2b92c5` (#886 merge, head_commit of record) / `docs/plans/done/0091-narrative-to-vertical-scaffolder-tool.md` (COMPLETE 10/10) + `services/engine/scaffolder/**` |

## In-Flight Discussions

- **PLAN-0094 — Draft; Steps 1–3 BUILT (s174 #917, s175 #922), Steps 4–6 UNBUILT.** The L1 loop-detect restructure: count non-progress instead of touches (P1), warn on the first trip and deny on the second (P2), add an acknowledged-pause exit the agent cannot fake (P3), and wire the subagent-completion reset that had **never been live** (F3c). **Step 1 (F3c) landed:** a `SubagentStop` registration (matcher `*`) plus additive per-`agent_id` `subagent_touched` state, so a completing subagent clears its **own** recorded edits and cannot launder the main agent's budget through a zero-edit spawn. **The soak released Step 3** — Cray reported no anomalies on the live loop. **Step 3 landed (#922, AC-3 final surface / AC-4 / AC-5):** the path-class threshold is now the WARN bar and the deny sits at `T+G` (`G=3`) = **9 code / 18 doc**, L4 untouched at flat 6, `CounterEntry.warned_at` dedupes the warn; the deny message deliberately does **not** name the P3 stop-ack, since P3 ships at Step 5 (test-pinned). **AC-1 (ii)** (`PostToolUseFailure` registration) closes at Step 4. **Ratified inputs are LOCKED:** OQ-1 `G=3`, OQ-2 full fresh budget, and SD-2 — subagent-scoped, per-`agent_id`-keyed reset — ratified as a **decision, not a diff approval**, because it changes what Lesson #0021 §3 recorded as the 2026-06-08 fix. **Every `settings.json` diff needs Cray per-diff approval** (guard self-modification, Lesson #0021 §4). Governance footing: **no ADR amendment** — ADR-0013 row E.4 (`docs/adr/0013-autonomy-axis-relocation.md:90`) specifies the consequence as "pause + Telegram alert", so the hard deny exceeded its own mandate and P2 moves L1 *toward* the ADR. Of the three surfaces that asserted the dead reset path was live, **two were corrected in Step 2** (registry row L1, Lesson #0021 §3) and the third — the deny message in `pretooluse_loop_detect.py` — was rewritten in Step 3, per D2's do-not-edit-twice instruction. All three are now closed. Substrate already shipped in #912; do not re-plan it. Full record: `docs/plans/0094-loop-detect-non-progress-and-reset-paths.md`; the anti-pattern behind it: `docs/lessons/0033-raising-the-threshold-is-not-fixing-the-unit.md`.
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
- [ ] **`docs/conventions/git.md` — substance DISCHARGED, one DEAD LINK left, and it needs Cowork.** *[De-duplicated s175: this TODO existed twice — here and as an In-Flight "Convention extraction" bullet; the In-Flight copy is dropped, this row is the single home.]* The extraction's substance is effectively discharged by the **`git-workflow` skill** (`.claude/skills/git-workflow/`, Tier 2.6), so the file may never need to exist. What DOES need fixing: **`CLAUDE.md:176` holds a dead relative link** to the non-existent `docs/conventions/git.md` ("Future canonical: …"). Either extract the file or drop the link — and **either way it is a Cowork round-trip**, since Code may not author `CLAUDE.md` (ADR-009 D1; the s175 #923 exception was scoped to §8 only). *(low priority)*
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
