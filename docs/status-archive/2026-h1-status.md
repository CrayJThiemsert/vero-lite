# STATUS.md rotation archive — 2026 H1 (recent window, base file)

> **Period covered:** 2026-07-25 (session-173) → onward (the RECENT window)
> **Sibling chain (letters ascend with time; the base file holds the RECENT window):** [`2026-h1b-status.md`](2026-h1b-status.md) (2026-05-10 → 2026-06-09) → [`2026-h1c-status.md`](2026-h1c-status.md) → [`2026-h1d-status.md`](2026-h1d-status.md) → [`2026-h1e-status.md`](2026-h1e-status.md) → [`2026-h1f-status.md`](2026-h1f-status.md) → [`2026-h1g-status.md`](2026-h1g-status.md) (2026-07-17 session-142 → 2026-07-24 session-171) → [`2026-h1-status.md`](2026-h1-status.md) (base, newest — rotations append HERE). The separate `2026-h1-current-focus.md` (sessions ≤46, ratified as-is) is a Current-Focus-only artifact predating this chain.


Rotated out of `docs/STATUS.md` per the **STATUS.md Rotation Policy**
(`docs/runbooks/memory-architecture.md`, Lesson #23). Tier-3: **grep + windowed reads
only, never a whole-file Read.**

**Split lineage.** At session 80 the combined `2026-h1-status.md` first crossed R4's
~192 KB bar and was split into a recent-window file and its `-b` sibling. The recent
window then grew back to **592,577 B — 3.01x the split trigger and 2.26x the 256 KB
cap** — because R4 had no mechanism: its responsibility-matrix guard column read `—`
where R1 and R7 read `fail`. Session 144 added that mechanism
(`tools/check_archive_size.py`, #789) and this file is one of the four it forced.
**No content lost:** every section is preserved verbatim and exactly once across the
chain, verified by exact list equality at split time, not by a byte-sum estimate.

**Second split — session 193.** This file reached **194,232 B**, 2,376 B under the
trigger, with a ~10,661 B Current-Focus block due to rotate in; the sessions-142→171
sections spilled to [`2026-h1g-status.md`](2026-h1g-status.md) and this file kept its
recent window, dropping to **46,215 B**. Arithmetic: 194,232 = 2,129 header + 148,017
spilled + 44,086 retained. **Verified the same way as the first split** — the 65
section headings were listed before and after and compared for exact equality, not
estimated from byte sums.

**Structural note (honest).** R4 describes an archive as TWO sections — rotated
Current Focus blocks and rotated Recent Decisions rows, *newest at top*. That is not
the shape on disk: the file drifted into **one section per reconcile, appended at the
bottom** (27 of them by session 144), and the old preamble's own "Period covered" had
gone stale years of sessions ago. This split preserves the drifted shape rather than
silently rewriting history to match the spec — reconciling R4's text with the real
convention is separate work, deliberately not done here.

---

## Rotated this reconcile (session-173, 2026-07-25 — the loop-detect guard pass, #912/#914)

Recent Decisions rows rotated because **R2 caps the table at the last 10**: the session-172 (PLAN-0093 COMPLETE) and session-173 (loop-detect guard) rows were prepended, so these two session-166 rows fell outside the window.

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-23 | **s166 — PLAN-0091 SD-5 RATIFIED (a), Cray typed (#869): the AT-2 template is owned by `services/engine/scaffolder/` and NEVER enters the shared `REGISTRY`** — the classify path stays byte-unchanged and ADR-0024 D7's abstain routing stays literally true. All five SDs closed. Tripwire: the `set(REGISTRY) == set(AT1_FAMILY)` assertion must never need editing — if it does, STOP and re-open SD-5 | `097d180` (#869) / `docs/plans/done/0091-narrative-to-vertical-scaffolder-tool.md` §SD-5 + `tests/services/engine/procedures/test_archetype_templates.py` |
| 2026-07-23 | **s166 — dispatch-quality discipline shipped (#866, docs-only): the `code-operational-policy` skill gains the 3 dispatch blocks (Frontier/anti-anchoring · oracle-scoped accelerator · REJECT-if) + the M1–M4 follow-up vocabulary + the pre-close counterexample step.** Deliberately NOT built: any hook/detector for M3/M4 — adoption is Rule-of-Three on recorded catches | `b8566a6` (#866) / `docs/lessons/0032-ambition-scales-with-oracle-exploration-gated-not-planned.md` |
| 2026-07-23 | **s167 — the autonomy fork RESOLVED + SHIPPED in one session: option A′ (Cray, typed) DEMOTES the Stop-hook `dispatch` verdict from an ORDER to a SUGGESTION (#870 filed, #871 built).** Ledger: 14 misfires / 0 valid fires. No ADR amendment — the arm had zero ADR backing, so the PLAN **is** the governance record. **The argument is settled history in the archived PLAN — do not restate it** | `7c86752` (#871 merge, head_commit of record) / `822a7e8` (#870) / `docs/plans/done/0092-stop-hook-dispatch-arm-demotion-to-suggestion.md` |
| 2026-07-23 | **s168 — PLAN-0092 closed 6/6 + archived (#881); the `AT2_ONLY_KINDS` drift fixed with an anti-drift tripwire (#882); SD-D settled — the classifier prompt reworded to a ROUTING SUGGESTION, decision value + reply schema pinned UNCHANGED (#886)** | `c2b92c5` (#886) / `c47232f` (#882) / `b8f011d` (#881) / `docs/plans/done/0092-stop-hook-dispatch-arm-demotion-to-suggestion.md` (COMPLETE 6/6) |
| 2026-07-24 | **s169 — PLAN-0088 Steps 1–3 BUILT (#890/#891/#893): the cross-run read substrate (AC-1/2/3/11) + reader A2 (`GET /insights/impact`, AC-4/5) + reader A3 (`GET /insights/flow`, AC-6).** Seven read-only async primitives, a seeded 250-run corpus with a plain-Python oracle independent of the SQL under test, two AST guards. `ImpactReport` carries **no** cross-currency total and must never gain one (S7). Suite 3109 → **3150**. Detail: the s169 CF block above | `9e26195` (#893) / `8393af8` (#891) / `b1e12d1` (#890) / `services/db/run_analytics.py` |
| 2026-07-24 | **s169 — PLAN-0088's design layer ADJUDICATED: SD-1…SD-8 ratified in ONE typed pass (#889); SD-8 = (a) ELIMINATE struck `list_runs_page` + AC-12**, so the substrate ships aggregate-only, `GET /runs` is untouched, and listing pagination moves to the future monotonic-`sequence`-column PLAN. AC-12 kept as a tombstone so AC numbering stays stable (live count 13). Step 0 DISCHARGED → build-ready. Detail: the s169 CF block above | `dd16267` (#889) / `8d1be34` (#888) / `docs/plans/done/0088-cross-run-read-substrate-and-run-insight-readers.md` §Surfaced decisions |

---

## Rotated this reconcile (session-179, 2026-07-27 — PLAN-0094 Step 4 re-scoped on its own probe (#933) + the expired-test fix that unblocked main (#934))

The session-174 Current Focus block rotated out under the R2 four-session window, and two session-171/170 Recent Decisions rows fell outside the 10-row cap. **Archival note:** the s174 block's closing sentence — "**AC-1 (ii)** (`PostToolUseFailure` registration) at Step 4" — was **falsified in session 179**; AC-1(ii) is now WITHDRAWN because the event does not fire in this harness build. The block is preserved verbatim as the historical record; the correction lives in the s179 Current Focus block and the In-Flight PLAN-0094 bullet.

### Current Focus block — session 174

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

### Recent Decisions rows — rotated under the 10-row cap

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-24 | **s171 — PLAN-0088 Step 6 BUILT (#905): the four Group-B primitives + the AC-10 carrier proof, under SD-9 (a2)'s precedent so no new SD was needed.** Reopening the corpus found FOUR shapes it wrote that the engine never does (the AC-2 class), and B3's refusal kind was a BIJECTION of procedure — its oracle could not have failed. Mutation probe 4/4 as predicted. Suite 3178 -> **3189**. Plus **#904**, the STATUS rotate A+C: 61,748 -> 48,920 B, window untouched | `08304a0` (#905 merge, head_commit of record) / `023f24a` / `a3716db` / `d863078` + `96fbdcc` (#904) |
| 2026-07-24 | **s170 — PLAN-0088 Steps 4 / 4.5 / 5 BUILT (#895/#900/#902); SD-9 RULED (a2) by Cray (#898, surfaced #897).** Readers A4 (audit-readiness, AC-7) + A1 (NL query over runs, AC-8/AC-9), three new primitives; SD-9 settles that the substrate grows in `run_analytics.py` **only** and strikes `agent_id` + `trigger` from v1. Suite 3150 → **3178**. **AC-9b (live MS-S1) OPEN — host-state.** | `5d02538` (#902 merge, head_commit of record) / `46f0ba1` (#898) / `7150c07` (#895) / `docs/plans/done/0088-cross-run-read-substrate-and-run-insight-readers.md` §SD-9 |

## Rotated this reconcile (session-180, 2026-07-28 — PLAN-0094 Step 4 COMPLETE: the unit changed from touches to non-progress (#937), two measured PLAN corrections + OQ-4 opened (#938), AC-11's count line + mirror-invariance (#939))

### Current Focus block — session 175

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

> _Older content rotates out of this file per the **STATUS.md Rotation Policy (R1-R7)** in [`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md) (Lesson #23): Current Focus keeps the 4 newest sessions (<=8 blocks); Recent Decisions keeps the last 10 rows. Rotated blocks/rows live in [`docs/status-archive/`](status-archive/) and git history (Tier 3). Layout — **two separate chains, both with letters ascending with time and the base holding the recent window**: the rotation archive `2026-h1b` → `c` → `d` → `e` → `f` → `2026-h1-status.md`, and the Current-Focus-only `2026-h1b` → `c` → `2026-h1-current-focus.md`. Rotations append to the two bases. **Grep the directory, not a filename** — the chain is one corpus and which file holds a given block is an artifact of where the ~192 KB R4 bar happened to fall. _[Chain created 2026-07-17 (s144): the single `2026-h1-status.md` had reached 592,577 B, 2.3x R4's cap, and the new guard (#789) forced the split.]_

### Recent Decisions rows — rotated under the 10-row cap

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-25 | **s171 — PLAN-0088 COMPLETE, 13 live ACs, archived to `done/` (#908).** AC-9b BUILT + PASSED (#907): live translate/phrase stages wired (reusing `nl_query`); one MS-S1 `gpt-oss:20b` smoke → grounded count 120 = the seeded corpus. A test premised on an unwired seam RAN the model twice unasked → a socket-level `_no_outbound_network` guard now makes an off-box call impossible. Suite 3189 → **3203/8** | `ca39841` (#908 merge, head_commit) / `c21c0aa` + `e443696` (#907) / `docs/plans/done/0088-*.md` |

## Rotated this reconcile (session-181, 2026-07-28 — CLAUDE.md full slim landed (#941): footer changelog retired to git history, §6 compressed)

### Current Focus block — rotated under the R2 four-session window

> **Session 176, 2026-07-27 (head_commit `04c94e4` → `77fa734`) — the session
> that went looking for a routing answer and found the fact-pack was wrong.
> One PR merged (#925, docs-only), 0 open. PLAN-0095 lands as **Draft** — a
> plan to make the scaffold-era `Dockerfile` build and boot the synthetic OCT
> demo with **no database**. Nothing was built: no Dockerfile change, no test,
> no compose edit, Steps 1–5 unexecuted. The image does **not** boot today.**
>
> **(the grounding sweep is the durable half.)** The session opened as a
> routing question — which of 15 candidate work-items to dispatch. Four Explore
> agents verified all 15 against code and **five premises carried in from the
> s175 handoff were wrong**. The load-bearing one: the first-order Docker boot
> failure is a plain Python import — `importlib.import_module(_VERTICALS_PACKAGE)`
> at `services/engine/discovery.py:45`, uncaught as the **first line** of
> `lifespan()` (`services/api/main.py:166`) — **not** the CWD-relative
> `Path("verticals")` read at `ontology_meta.py:154`, which is real but
> second-order. Dispatching the drafter on the original fact-pack would have
> fixed the second-order problem and left the image still unbootable. Also
> corrected: "8 distinct defects" overstated independence (it is **two** broken
> `COPY` statements, each with two symptoms, plus hygiene gaps), and a **ninth**
> defect nobody had counted — `pyproject.toml:7` declares `readme = "README.md"`,
> never COPY'd, so `uv sync` fails a **second** time even after the
> package-tree fix.
>
> **(a stale gate-route claim in the constitution.)** `CLAUDE.md` §6 says a new
> PLAN/ADR is PreToolUse-gated for Code **and the in-harness `plan-drafter`**.
> Measured: `pretooluse_classifier_dispatch.py:301-311` **exempts the
> `plan-drafter` subagent from the G2 classifier gate by design** (PLAN-0034
> prong 2, SD-1(a)), short-circuiting *before* the classifier — so it does not
> depend on MS-S1 being warm. The main Code agent carries no `agent_id` and is
> still gated, so **G2 is preserved**; only the sentence is wrong. Recorded as a
> **finding needing a Cowork round-trip** (Code may not author `CLAUDE.md`),
> alongside the already-tracked `CLAUDE.md:176` dead-link TODO — **not fixed**.
>
> **(Cray's ruling reframed the PLAN, it did not just pick options.)** The frame
> Cray set: the artifact must be shaped so it grows into production **without a
> rewrite**, under two hosting models (the customer uses an instance we host; we
> stand up a server at the customer's site) — *"ready for development toward
> production," not "build production now."* **SD-1 = both** — the standalone
> image is the artifact, compose is a thin consumer proving it composes with a
> real Postgres (the "no current consumer" premise died under the production
> frame). **SD-2 = include `alembic/` + document** — the over-promise concern is
> answered by documentation, not omission; "one image, different commands"; a
> separate migration image is the *riskier* shape (version skew). **SD-3 = all
> four hygiene items IN.** SD-1 and SD-2 **overturned the drafter's own
> recommendations** and are recorded in-PLAN as **`superseded by new info`**,
> not `was an error`, with the original analysis preserved as the decision
> record.
>
> **(two R2 rounds — and the drafter caught an error in the reviewer's
> correction.)** R2 round 1 widened the oracle's AST scan to the verticals tree;
> the drafter showed a literal `verticals` glob would **break AC-3** — the
> anti-tautology invariant the same review insisted on (the oracle module must
> not contain the string at all) — so the correction could not be implemented
> naively, and it proposed a derived scan set instead. R2 round 2 corrected
> *that* rule: "top-level packages excluding the test tree" is **three**
> directories, not the two claimed — `benchmarks/`, `services/`, `tests/`,
> `verticals/` all carry `__init__.py` — so the behaviour-identity held **by
> luck, not by construction**, and `benchmarks/` is never COPY'd into the image,
> making it a latent **false-RED** surface. Replaced with a **transitive closure
> seeded from the app root**: code that never enters the image cannot fail
> inside it, so it must not constrain the image.
>
> **(the oracle design is the PLAN's real content.)** A test that hardcodes the
> expected COPY list re-encodes the Dockerfile and passes tautologically
> forever. Instead **O-1 derives** the required root set from an AST scan and
> asserts the Dockerfile covers it, with a greppable anti-tautology invariant
> (AC-3) and a mutation (M-C) that adds a runtime-resolved root with no
> Dockerfile edit and **must go RED**. O-4/O-5/O-6 carry **binding
> derivation-status labels** — a presence check presented as derived is an R2
> reject; `USER` is honestly labelled a presence check because no code source of
> truth exists. **AC-6 is invariant: no acceptance criterion needs a Docker
> daemon** (O-6 parses YAML with `ruamel.yaml`, verified a main dependency at
> `pyproject.toml:23`); every daemon action sits in the optional Cray-gated
> evidence step.
>
> **(the hosting question is surfaced, not drafted.)** *"Customer uses our
> server"* touches **ADR-002's LAN trust model** —
> `docs/adr/0002-network-topology.md:76` and `:86` — which defers its own
> successor **twice** as an unnumbered `ADR-NN`. PLAN-0095 states it can land
> with that open, because nothing in the image or the compose service selects
> *where* the image runs. This is now a **live candidate needing its own ADR**.
>
> **(one execution trap recorded for whoever builds this.)** The compose
> sketch's `vero:vero` in-network URL trips the `detect-secrets` pre-commit hook
> as Basic Auth Credentials and needs an inline `# pragma: allowlist secret` —
> in the **real `docker-compose.yml` at Step 3**, not only in the PLAN sketch.
> It is a pattern match, not a leak (`vero:vero` is the already-tracked dev
> placeholder at `docker-compose.yml:6-7` and `services/api/config.py:39`).
> Never `--no-verify` (CLAUDE.md §8).
>
> **State at close:** `main` `77fa734`, 0 open PRs; tree clean but for the two
> standing KEEP untracked paths (`.claude/benchmark-results/`,
> `.claude/launch.json`). CI `gate` PASSED on `2fb8709` in 3m38s and was
> **SHA-verified** against the PR head before merge. **No suite re-run was owed
> or performed** — the merge is docs-only (one file, 702 insertions, zero code).
> **MS-S1 was not contacted; no model warmed or run.** PLAN-0094 Steps 4–6 are
> untouched and still carry their prior blockers.

### Recent Decisions rows — rotated under the 10-row cap

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-25 | **s172 — PLAN-0093 COMPLETE 8/8, archived to `done/` (#913): the LLM-arm degrade disclosure, no silent arm swap.** Four steps — disclose which arm phrased an NL answer, make the rule fail-safe say it is a fail-safe, project the authoring arm over HTTP (incl. the insights run-corpus path), and fix `LLM_RETRY_BUDGET` being **inert on the governed path**. Its L1 deadlock on `services/engine/nl_query.py` — where the documented subagent-reset escape was run verbatim and did **not** clear the counter — became the s173 brief and the empirical half of that finding | `9786c63` (#913 merge) / `55d2007` (#911) / `30285bc` (#910) / `docs/plans/done/0093-llm-arm-degrade-disclosure.md` |


---

_Rotated out of `docs/STATUS.md` on 2026-07-28 (session 182), per the R1–R7 rotation policy._

| 2026-07-25 | **s173 — the L1 loop-detect guard: its unit of measurement was wrong and one documented escape was never wired.** #912 bounds the loop-counter state lifetime (age-out 6 h + a session boundary read from the hook payload, which `resolve_session_id` never consulted). #914 lands **PLAN-0094** (Draft) + **Lesson #0033**. Probed live: `PostToolUse` fires only on success, so L1 could not see a failed edit at all — 6 good edits score 6, 6 retries of one broken anchor score 0, so **no threshold separates them** and PLAN-0094 changes none. `_handle_agent_completion` is **dead code** (no `PostToolUse` Task/Agent matcher); the registry row L1, Lesson #0021 §3 and the deny message all still call it live. Cray ratified **OQ-1 `G=3`, OQ-2 full fresh budget, SD-2 subagent-scoped reset** (a decision, not a diff approval — it changes a recorded lesson) | `6fb89b8` (#914 merge, head_commit) / `3383697` + `2d09002` (#912) / `docs/plans/0094-loop-detect-non-progress-and-reset-paths.md` + `docs/lessons/0033-raising-the-threshold-is-not-fixing-the-unit.md` |

<!-- Recent-Decisions row rotated out of docs/STATUS.md by the s183 reconcile (R2) -->
| 2026-07-25 | **s174 — MS-S1 stopped being an inference appliance, and CLAUDE.md §8's gated surface was widened to match.** #916 opens OpenSSH on TCP 22, LAN-only (`Domain, Private`), verified with `BatchMode=yes` — which proves publickey auth, not a silent password prompt; the knowledge splits per §4 — rule in §8, how-to in the runbook, procedure in a new `ms-s1-admin` skill. #918 rescopes §8, net +1 line: substance unchanged, its `…:11434` *illustration* was reading as a scope boundary (Cowork drafted → Code R2'd + committed → Cray ratified). #917 lands PLAN-0094 Steps 1+2 — the `SubagentStop` L1 reset, scoped to the completing agent's OWN edits (turn-scoped would be a self-unlock path; Cray ratified the divergence from Lesson #0021 §3); suite 3244 → **3252** | `a3a9c66` (#918 merge, head_commit) / `2cda070` (#917) / `c9050b9` (#916) / `docs/runbooks/ms-s1-ssh-access.md` + `docs/plans/0094-loop-detect-non-progress-and-reset-paths.md` |

<!-- Current Focus blocks rotated out of docs/STATUS.md by the s185 reconcile (R2) -->
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

<!-- Recent-Decisions row rotated out of docs/STATUS.md by the s185 reconcile (R2) -->
| 2026-07-26 | **s175 — the harness stopped letting a failed command look like a success.** #923: Lesson #0007's mechanism CORRECTED and reclassified `was an error` (a bare `$` expands one shell layer early; `$?` is not unreadable) + a binding CLAUDE.md §8 rule + a `_shell_hygiene_warning` PostToolUse advisory. #922: PLAN-0094 **Step 3** — warn at T, deny at T+G (9 code / 18 doc), L4 flat 6; AC-3/4/5 closed. #920 pins all six verticals' ACTION factory offline at REGISTRATION; #921 fixes four stale cross-refs. **Cray: demo target = the LIVE-API shape** → Candidate C is the long pole. ADR-009 D1 one-off Code-authors-§8 exception — **not precedent**. Suite 3252 → **3296** | `04c94e4` (#923 merge, head_commit) / `3b3b666` (#922) / `59c81a6` (#921) / `65c6953` (#920) / `docs/lessons/0007-harness-exit-code-artifact.md` |

<!-- Recent-Decisions row rotated out of docs/STATUS.md by the s187 reconcile (R2: newest 10 rows) -->
| 2026-07-27 | **s176 — PLAN-0095 merged as Draft (#925): make the Docker image build + boot the DB-less OCT demo. Nothing built; Steps 1–5 unexecuted.** The grounding sweep (4 Explore agents, 15 items) killed **5 wrong s175-handoff premises** — the first-order boot failure is a plain import (`discovery.py:45`, uncaught at `main.py:166`), **not** the CWD-relative `Path("verticals")`; plus an uncounted **9th** defect (`pyproject.toml:7` `readme` never COPY'd). Cray ruled **SD-1 = both**, **SD-2 = include `alembic/` + document**, **SD-3 = all four** — reframing the PLAN as *ready for development toward production*; SD-1/SD-2 overturned the drafter and are logged `superseded by new info`. Oracle derives the COPY set by **transitive closure from the app root** (not a `verticals` glob — that would break AC-3); **AC-6: no AC needs a Docker daemon**. Finding: **CLAUDE.md §6's plan-drafter gate claim is STALE** — the subagent is exempt by design (`pretooluse_classifier_dispatch.py:301-311`), G2 preserved for Code | `77fa734` (#925 merge, head_commit) / `2fb8709` / `docs/plans/done/0095-docker-image-boot.md` |

<!-- Recent-Decisions row rotated out of docs/STATUS.md by the s189 reconcile (R2: newest 10 rows) -->
| 2026-07-27 | **s177 — PLAN-0095 COMPLETE 7/7, archived to `done/`: the image builds and boots for the first time since the 2026-05-07 scaffold commit.** #927 lands Steps 1–5 as ONE PR (the oracle is born-RED, so splitting lands a red suite): builder defects **eliminated not repaired** (`--no-install-project`), `python -m uvicorn` for a guaranteed import path, `alembic/` shipped per SD-2, a thin compose `app` consumer per SD-1. The oracle **derives** its COPY set by transitive closure from the app root — born-RED with **5 assertion families**, **12/12 mutations bit** (M-C goes RED with *no Dockerfile edit*), derived set measured exactly `['services','verticals']`. AC-3 ships as a **sibling test**, not the PLAN's reviewer-grep (Cray's call). #928 adds runbook §1a. **Step 6 live, on Cray's go:** build exit 0, `/health` 200 in ~2 s, all six verticals in the boot log, `uid=999(vero)`, HEALTHCHECK `healthy`, `alembic current` → **`0012 (head)` from inside the image**. **OQ-2 residual + OQ-3 RESOLVED; OQ-1 (hosting model) open by design.** Two PLAN departures, both evidence-backed: no `docker compose down` and `--no-deps`, because `vero-postgres`/`vero-redis` were **up 7 days** and §1 depends on them — `StartedAt` byte-identical before/after. Two self-caught errors: the oracle's URL extraction (found by reading, one step before a false RED) and a mis-aimed M-D that hit a **comment** not the `RUN` line — oracle logged `confirmed — prior intact`. Finding, reported not fixed: **Docker Desktop's WSL integration is OFF** for `ubuntu-24.04`, so runbook §1's own `docker ps` precondition fails from WSL today. Suite 3296 → **3306** | `8618081` (#928 merge, head_commit) / `54f0189` / `6ab2c28` (#927 merge) / `fb0e1f8` / `docs/plans/done/0095-docker-image-boot.md` + `tests/docker/test_dockerfile_oracle.py` |

<!-- Recent-Decisions row rotated out of docs/STATUS.md by the s192 reconcile (R2: newest 10 rows) -->
| 2026-07-27 | **s179 — `main` was RED for three hours and PR-only CI structurally could not see it (#934): the tests EXPIRED, they did not regress.** `_seed_ack` hardcoded a `last_updated`; `load_counter`'s `prune_stale_entries` drops entries past `COUNTER_MAX_AGE_HOURS` (6 h) — green at merge, red hours later. `git diff 25239f3 490f09e` was **EMPTY**: same tree, opposite verdict. Proved with zero code edits (`CLAUDE_LOOP_COUNTER_MAX_AGE_HOURS=100000`). Fix stamps from `_now_iso()` + adds `test_seed_ack_is_stamped_live`, a guard that **tests the FIXTURE** so a future re-hardcode fails at the cause. Suite 3317 → **3318** | `35851f2` (#934) / `bc7be51` (head_commit) / `a5dacb0` (#935, OPEN — Step 4 state layer) |

## Rotated this reconcile (session-193, 2026-07-30 — PLAN-0096 Step 8 item 5 COMPLETE: the month-end export shipped end to end, #982-#986; plus the docs overclaim fix #987 and the h1g archive split)

### Current Focus block — Sessions 186→187 (PLAN-0096 Steps 1-5, 7 and 9 COMPLETE, #951-#961) [rotated 2026-07-30, session-193 reconcile — 4-newest-sessions CF window; the OLDEST of exactly four, evicted because a new block forces a rotation]

> **Session 186→187, 2026-07-28/29 (head_commit `760ceed` → `728da00`) — the
> arc where PLAN-0096 stopped being a document. Ten PRs merged (#951–#961),
> 0 open: **Steps 1–5, 7 and 9 COMPLETE (6 of 10)**. The fleet vertical now
> carries the design partner's real governance numbers, captures cases from
> minute 1 into Postgres, holds a quote evidence pack, **enforces its sourcing
> rule instead of decorating it**, can record a roadside decision provisionally
> and chase the signature afterwards, imports the partner's PM history as
> measured-then-confirmed data, and owns one outbound notify surface — built
> DISARMED. But the session's most important output is not a feature: **a
> plausible one-line bug left all 24 LINE unit tests GREEN and reddened only
> the scenario suite** — and on that measurement Cray set a new standing work
> standard.**
>
> **(s186 — Steps 1–4, and Step 5 split in half on purpose.)** Step 1 replaced
> the PLAN-0086 simulated customer's ladder with the partner's own (floors
> `"0"`/`"5001"`/`"30001"`, per-truck ceiling 5001) and built the AC-2
> cross-vertical hash tripwire. Step 2 added `repair_case` + alembic 0013 + a
> mobile-first View I. Step 3 added the quote evidence pack — two tables and a
> facts-only read model that states no verdict. **Step 4 is the load-bearing
> one:** it KILLED the fail-open `default: {compliance: {three_quote: true}}`
> reshape, which had been passing every repair whether or not anyone compared
> a price. Cray ratified three things mid-session (the `repair_case` table over
> a ⊕ PLAN line; `distinct_vendor_count` over the PLAN's `quote_count` —
> because three quotes from one garage is not "สามเจ้า"; and a dev-DB
> migration). Step 5 was then split deliberately: part 1 landed the schema, the
> `RESOLVED_PROVISIONAL` status and the pure `ratification_state`, because
> **authoring the fleet window before a driver existed would itself have been
> the PLAN-0094 AC-1 defect class** ADR-0034 D3 exists to prevent.
>
> **(s187 — Step 5 part 2, and one ADR that contradicted itself.)** The
> provisional branch, `ratify_gated_step`, the resume advance, and the fleet's
> `ratification_window_days: 7`. The design's load-bearing choice is an
> **absence**: no `governed_decision` tie is emitted at provisional time,
> because the attested authority answered a phone rather than acting in-system,
> and a tie naming them would be a lie the audit model cannot catch (PLAN-0075
> SD-6(a)). The tie appears at ratification, naming whoever actually signs; a
> refusal emits none at all. **The contradiction found by building it:**
> ADR-0034 **D3(3)** writes the ratify precondition as `status ==
> RESOLVED_PROVISIONAL`, while **D3(6)** requires ratification to stay possible
> on an advanced run — and `resume_run` marks every advanced step `complete`.
> In the fleet hero the step after the gate is *itself* gated, so the run
> always moves past `approve` within minutes while the window is seven days;
> read literally, D3(3) makes the owner's signature **impossible in exactly the
> flow the window exists for**. Cray was shown all four options and typed the
> **state-based precondition** — the obligation (`pending`|`overdue`), not the
> step status — which is a strict superset of D3(3) and preserves its stated
> intent (idempotency BY STATE) verbatim. **The ADR text was amended to match in
> s188 (#962, `eae0f82`) — and it was not the "one word" s187 predicted.** Code
> R2 on that amendment found a SECOND divergence of the same class: D3(3) *and*
> D3(4) both stated the `RESOLVED_PROVISIONAL → RESOLVED` transition
> **unconditionally**, while the shipped flip is conditional on the step still
> being parked there — a step the run has advanced past stays `complete`,
> because walking it back would re-enter `_UNRESUMED_STATUSES` and make a
> finished step look like the one the run is suspended at
> (`action_step.py:1165-1172`). Both halves are the same defect: **the shipped
> mechanism is obligation/audit-based where the ADR text described a
> status-based model.**
>
> **(s187 tail — Steps 9 and 7.)** Step 9 (#959) landed PM data import on the
> shape **Cray typed**: a `pm_import_row` table (**alembic 0015**) *plus* a
> confirmed-PM **ontology overlay**, chosen over a per-process cache and over a
> table with no overlay — the rejected third option would have made **AC-10
> vacuous**, since unconfirmed rows would not touch the ontology and neither
> would confirmed ones. The parser is pure and fail-closed whole-file /
> reject-per-row; four API routes and an onboarding runbook ride with it; the
> fleet's last-service `GUESS` stamps are retired. Cray gave an **explicit go**
> to migrate the dev DB to 0015, and it was verified **against the live schema,
> not `alembic current`** — a probe read `information_schema` and confirmed 15
> columns, `seq` as `bigint … IDENTITY(ALWAYS)`, both indexes + the PK + the
> unique constraint, 0 rows. *(`alembic current` reports which migration RAN,
> never what it produced.)* Step 7 (#960) built the **LINE Official Account
> notify seam**: five AC-8 events, recipients addressed as **ROLES not ids**,
> per-(event, recipient) cooldowns, `tools/notify/line.sh`, an `.env.example`
> block — **outbound only, and DISARMED by design**
> (`LINE_NOTIFY_ENABLED=false`, no token, no recipients), so no test and no dev
> session can reach a real recipient.
>
> **(s187 — the measurement that changed the work standard.)** A non-vacuity
> probe measured that a plausible one-line bug — normalising the LINE recipient
> role key (`role.replace(".", "")`) — leaves **all 24 mock-fed LINE unit tests
> GREEN** while silently ensuring the `ผจก.เดินรถ` role never receives an
> approval request for its entire ฿5,001–30,000 DOA rung. **Only the scenario
> suite reddened.** Root cause: every LINE unit case feeds a `_DETAIL` dict the
> test author wrote, so **the suite agrees with itself by construction** — it
> proves the contract the author IMAGINED, not the one the system produces. On
> that measurement **Cray set a new standing work standard (typed, not
> inferred): a passing unit test proves the SEAM works, never that the system
> does its job — every build also needs a scenario test driving the REAL
> producer into the REAL consumer on realistic simulated data, and skipping it
> is not allowed.** #961 is that correction landing: **8 scenario cases** on
> realistic data, producers wired to consumers. The standard is ADVISORY until
> it reaches `CLAUDE.md` §8 — a Cowork round-trip, logged below.
>
> **Two anti-patterns, each worth a sentence because each cost real time.**
> **"Assert absence by making the test double EXPLODE" does not survive a
> blanket `except`:** the AC-11 case ("a disarmed channel makes no outbound
> call") used a raising transport, and removing the arm gate entirely left it
> GREEN — `_push`'s `except Exception`, correct on its own terms, swallowed the
> `AssertionError`. Rewritten to **RECORD each call and assert the record is
> empty**; nothing can swallow that. And **editing a vertical's
> `data_adapter/__init__.py` retracts a MEASUREMENT** —
> `test_row_4_adapter_is_structurally_equal_to_the_donor` carries PLAN-0086
> AC-7's claim that the hand-written adapter equals scaffolder output, so the
> PM overlay was hung on the object SOURCE
> (`synthetic.OBJECT_SOURCES["Truck"]`) rather than weakening that test.
> Future vertical-specific seams go there too.
>
> **State at close:** `main` `728da00`, 0 open PRs. Full offline gate re-run on
> **every merge commit** (CI here is PR-only, so a merge commit is otherwise
> never tested): **3502 passed / 8 skipped** (s185 baseline 3343 → 3438 at
> #958 → **3470** Step 9 → **3494** Step 7 → **3502** scenarios), `mypy
> services/ verticals/` clean over **175** files, ruff + format clean, R7/R8
> exit 0, and `git diff <branch> <merge>` **0 bytes** on all three tail merges
> (`f7f85ef`↔`1de7b80`, `00b40b2`↔`bc7c8a9`, `a042ce1`↔`728da00`). **AC-2 and
> AC-6 stayed green through every schema touch** — only the fleet's own
> governance hash moved, which is the intended and only effect.
> Non-vacuity discipline held throughout: **eleven probes in session 187
> alone** (the s187 close report's own count — the figure this block carried
> before the tail reconcile counted only through #958), each shown RED before
> its oracle was believed, restored from `/tmp` copies (never `git checkout`)
> and `diff`-verified clean afterwards — including the one that proves Cray's
> precondition ruling is guarded by a single discriminating test, the one
> that flipped `quote_gate` from `failed` back to `complete` when the fail-open
> default was restored, demonstrating the hole Step 4 closed, and the role-key
> probe above. Three real
> defects were found **by running the work**: a JSONB-null-vs-SQL-NULL trap
> that would have silently broken Step 8's export, a response model dropping
> fields the router stored, and an un-gitignored photo-upload directory on a
> PUBLIC repo. `.claude/state/goal.json` **CLEARED this session** — the file
> does not exist, so no stale goal is armed. **MS-S1 was never touched;
> everything was deterministic-offline.** **R2 rotation applied at the
> mid-session reconcile** — the s183 + s182 Current-Focus blocks and the s176
> Recent-Decisions row rotate to `docs/status-archive/`; both archive files
> remain under R4's ~192 KB bar. *(This tail reconcile extends the s186→s187
> block and row in place rather than appending new ones, so it rotates
> nothing.)*

### Recent-Decisions row — s179 (PLAN-0094 Step 4 RE-SCOPED on its own probe's refutation, #933) [rotated 2026-07-30, session-193 reconcile — 10-row window]

| 2026-07-27 | **s179 — PLAN-0094 Step 4 RE-SCOPED on its own probe's refutation (#933); OQ-3 opened + RESOLVED same session.** Measured twice, one session apart: **a failed `Edit` invokes NO hook** — not `PostToolUseFailure`, not `PostToolUse`. **D4(a) withdrawn**, taking **AC-1(ii) / AC-6 / AC-8(ii)** with it (AC-6 withdrawn, not weakened) and with them Step 4's only Cray-gated `settings.json` surface; the s169-class thrash stays **uncountable**. OQ-3 → (b), four rulings: **R1** a self-contained COUNT, not a sha1 pointer (evidence ring 6 vs doc trip bar 15); **R2** `dict[str,int]`; **R3** `result == ""` on forward edits; **R4** → new **AC-11** (Telegram `count: N/T` + formatter mirror-invariance) | `b3c20dd` / `bde43d6` (#933) / `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md` §D4 + §OQ-3 |

### Current Focus block — Session 189 (PLAN-0096 Steps 1–7 and 9 COMPLETE, #965–#968) [rotated 2026-07-30, session-194 reconcile — 4-newest-sessions CF window; the OLDEST of exactly four, evicted because a new block forces a rotation]

> **Session 189, 2026-07-29 (head_commit `be7d386` → `13aa2f0`) — the session
> the fleet partner's round-2 answers landed and PLAN-0096 stopped being
> blocked. Four PRs merged (#965–#968), 0 open: **Steps 1–7 and 9 COMPLETE (8
> of 10)**. **Five of the seven questions are closed:** A1 built Step 6, A3
> built `pm_due`, and **A4 + A7 confirmed values that had already shipped** — a
> flat ฿5,000 ceiling for every truck initially, so the authored `5001` default
> stands and the per-truck "stretch values" sub-task is **eliminated, not
> deferred** (those values do not exist yet); and 99% whole-baht quoting,
> ฿30,000 exactly = no comparison / ฿30,001+ = comparison required, confirming
> the shipped `"30001"` inclusive floors and closing the satang de-minimis
> intake note. **A2 is answered, so Step 8 is unblocked rather than blocked** —
> the only question with build left. A5 is **parked** (no real Wialon export
> exists yet, and the partner wants an admin-mapped remembered column mapping,
> so the Step 9 importer stays fixed-column); A6 is a Step 9 *runbook* item,
> not code. **Nothing blocks the build.**
>
> **Step 6 (#965) — the partner's chain, not ours.** A1 superseded the PLAN's
> guessed four-item checklist: the real chain is **8 steps, 4 mandatory + 4
> conditional**, each carrying its **own** "ถ้าค้างเกิน" threshold rather than
> one shared timeout — two of them context-dependent (แจ้งอู่ 30 min on a
> breakdown / 1 day on PM; รออะไหล่ 2 days general / 5 days major part), and
> เริ่มซ่อม anchored to parts-complete ("1 วันหลังของครบ"). Shipped as a
> fleet-side **authored config** (`verticals/fleet_maintenance/task_chain.py`);
> the partner's suggested partner-editable template system was **declined for
> Phase 1** per ADR-006's Rule of Three. Storage is an **append-only**
> `repair_case_task_event` trail plus `repair_case.work_type` (alembic
> **0016**), so AC-7's "actor + timestamp per flip" is the storage model rather
> than logging bolted onto mutable state; that one `work_type` field serves
> both these context SLAs and Step 8's ประเภทงาน export column. Plus the
> staleness sweep into the existing `task_chain_stale` LINE event and
> `POST|GET /api/cases/{case_id}/tasks`, whose GET takes an optional `as_of`
> that Step 8's period-close export needs.
>
> **The anchor rule — Cray typed it, of three options weighed.** A step with
> prerequisites starts its clock when the prerequisites **this case actually
> has** are settled; counting from the item's own activation would have nudged
> เมย์ about starting a repair from day two of an *authorised* five-day
> major-part wait — against a partner whose own stated failure mode is
> *"ผมไม่อยากให้ทุกอย่างเด้งเข้ากลุ่มเดียว เดี๋ยวคนปิดแจ้งเตือนหมด"*, with exactly
> one outbound channel to spend.
>
> **`pm_due` (#968) — a sixth LINE event, admitted on evidence.** A3 supplied
> the two things `LineEvent`'s closed-set docstring demanded before a sixth
> member could exist — a named producer and a named recipient rule — so Cray
> amended AC-8 from five events to six. The recipient is a **group** (กลุ่มช่าง),
> not a person, by the partner's choice, and it is **one message per round**
> listing the due plates, not one push per truck. The producer reads the due
> set off the **persisted `judge_service_due` verdicts of the run that just
> fired** — never re-deriving "due" from odometers, because a second
> implementation of that comparison could disagree with the one the governed
> run acted on and the message would name a different set than the screen the
> human approves. Keyed to a run id, so a truck is announced once per round.
> The scheduler daemon holds no vertical knowledge by design, so it gained an
> **injected `on_fired` hook**, and `services/engine/cli.py` resolves the fleet
> producer as that hook — the same hand-wired shape as the executor factories.
>
> **The unplanned thread (#966 + #967) — the session's most transferable
> finding.** #965's CI failed at 54 s on the `alembic check` lockstep guard:
> `alembic/env.py` never imported the new ORM module, so `Base.metadata` did
> not know the table existed and autogenerate wanted to **DROP** it. **3528
> passing tests could not see it** — `create_all` knows only what the
> *importing test module* pulled in, and nothing offline traverses `env.py`.
> #966 built an offline AST-based guard for that class. Then Cray asked whether
> `alembic check` really needs a live DB, or whether we could run it and see
> what was hiding. **Probing instead of reasoning did three things:** it
> **refuted the premise** of Code's earlier answer (no *dev* DB needed — the
> disposable per-checkout test DB works, measured at **1.75 s** total); it
> found a **live drift**, since #965's own fix had patched `env.py` only and
> left `tests/db_support.py` — the second registration site, whose comment says
> "keep in lockstep with alembic/env.py" — missing the same module; and closing
> that revealed the **pre-existing guard had been defeated by co-drift**,
> because `test_db_hermeticity.py`'s hand-maintained `_HEAD_TABLES` was missing
> the same table, so two wrong lists agreed and the test stayed green. **The
> rule that came out of it: a comparison means something only when at most ONE
> side is hand-maintained.** The widened guard derives the model set from
> source via AST; `_HEAD_TABLES` stays hand-written **on purpose** (deriving it
> would compare metadata to itself). The `alembic check` half
> shipped as a **test, not a hook** (Cray typed it) — a hook's `upgrade head`
> would collide with a concurrent pytest's `DROP SCHEMA public CASCADE`, and
> running the suite in the background while editing is normal here.
>
> **State at close:** `main` `13aa2f0`, 0 open PRs. Suite **3502 → 3552**; ruff
> check + format clean over **552** files; `mypy --strict services/` clean over
> **123**; `alembic check` + the registration guard clean; CI `gate` PASS and
> merge-commit equality **0 bytes** on all four PRs. **Six non-vacuity
> mutations**, each restored from `/tmp` and diff-verified byte-identical; two
> load-bearing — a router writing `"PENDING"` for `"pending"`, a pure seam bug,
> left **all 17 rule-suite cases GREEN** and reddened 5 of 8 scenario cases;
> emptying the CLI's `_FIRED_HOOKS`, an unwired seam, left the **scenario suite
> fully green** and reddened only the hook suite. One proves the producer is
> right, the other proves anything calls it — which is why §8 wants both. **Dev
> DB migrated 0015 → 0016 on Cray's explicit go.** MS-S1 never touched; LINE
> still disarmed. **R2 rotation applied** — the s184→s185 Current-Focus block
> and the s177 PLAN-0095 Recent-Decisions row rotate to `docs/status-archive/`.

### Recent-Decisions row — s180 (PLAN-0094 Step 4 COMPLETE; L1 counts NON-PROGRESS, #937/#938/#939) [rotated 2026-07-30, session-194 reconcile — 10-row window]

| 2026-07-28 | **s180 — PLAN-0094 Step 4 COMPLETE (#937/#938/#939): L1 counts NON-PROGRESS, not touches. AC-7, AC-8(i)/(iii), AC-11 closed.** L1 increments only on a re-applied `old_string` (`repeat xN`) or a return to content already held this turn (`osc xN`); forward edits record `result == ""`; `clear_turn_scoped()` wired into the turn boundary. **All three L1 warns ever recorded would not fire under the new unit.** s179's BLOCKING `tool_response` probe was **answered without being run** (84 recorded `Edit` results: no `content` key, `originalFile` null in 78/84, `structuredPatch` = a diff not a state) — the PLAN's on-disk hash stands, no restart spent. **AC-11: `T` = the DENY bar in BOTH Telegram bodies** (Cray's ruling on a self-contradicting spec). **OQ-4 OPENED — should L1 exist at all?** Baseline over all 113 transcripts: **0 denies, 3 warns, 0 true positives**. **Pre-committed: re-measure after ~20 sessions; TPs still 0 with ≥1 FP → dispatch Cowork to draft the ADR-013 amendment retiring L1.** Suite 3318 → **3327** | `767d520` (#939 merge, head_commit) / `2b9cb6f` / `053410a` (#938) / `0a85b21` (#937) / `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md` §D4 + §OQ-4 |


---

### Rotated 2026-07-31 (session 195 reconcile)

#### Current-Focus block — Session 191 (head_commit `99b752f`)

> **Session 191, 2026-07-30 (head_commit `143fe6b` → `99b752f`) — the session a REAL
> repair case first reached the governed gate.** Three PRs merged (#975–#977), 0 open.
> Until then the claim "the gate governs real repairs" was **true of the demo and false
> of the product** — `cases.py` referenced `OperationalEvent` nowhere, and the only
> `case_id` ever reaching a run was the fixture `case-demo-truck01-axle`.
>
> **#975 — ใบที่ตกลง, the accepted quote (alembic `0019`).** The DoA ladder routes on the
> ฿ figure of a repair, and nothing recorded that figure at the moment it became true:
> `RepairCaseCloseout.total_thb` is written *after* the work the gate was meant to
> authorise, and `EvidencePack.lowest_amount_thb` is the *cheapest* quote, which is not
> what was agreed whenever an approved higher quote wins on lead time. The same absence
> forced `0018` — nothing recorded WHICH garage was used. **Cray typed two decisions:**
> the reference is a **REQUIRED** foreign key (a free-typed vendor + amount was offered
> and declined — the figure an authority threshold routes on must trace to evidence
> somebody recorded), and a **reason is required only when the accepted quote is not the
> cheapest on file** (the audit question is never "why did you accept a quote", it is
> "why did you not take the cheapest one"; demanding it always trains the operator to
> type "ถูกสุด" into the box). A third TABLE, not a flag: a flag would need `UPDATE`,
> breaking the append-only rule these tables exist to hold. The cross-case invariant is
> a composite FK — measured: with the router's case filter removed, **Postgres itself**
> refuses the insert.
>
> **#977 — the case → event path**, Option A, mirroring the ratified `pm_projection`
> seam, with **zero `services/engine/` diff and zero `data_adapter/__init__.py` diff**,
> both verified — the latter mandatory, since `test_golden_e2e` holds that module
> structurally equal to the scaffolder's output (PLAN-0086 AC-7 row 4). Only cases with
> an **accepted** quote are emitted — a case with quotes and no acceptance has no agreed
> number, and emitting one would mean inventing it. **A real case OUTRANKS the fixture on
> its own truck and the AT-2 hero narrative moves with it** — Cray typed that over
> parking real cases on unused trucks, which would have hidden the collision. Cache
> invalidation is **fingerprinted, not blanket** (Code's call, veto open): `demo_events`
> caches its live list per process, and that list also holds the recovery reading Execute
> appends (PLAN-0015 D2), so a blanket reset would silently delete it.
>
> **The session's own defect, found by probing rather than by failing.** The scenario
> suite passed first run; the sweep then returned **GREEN on one probe — a vacuous
> oracle**: the mutation raised inside the projection's digest, the router's fail-soft
> refresh swallowed it, and the stream stayed unchanged — exactly what the test asserted.
> **A test that cannot distinguish "correctly skipped" from "crashed and was swallowed"
> proves nothing**, the same class as the `assert-absence-by-recording` lesson. Fixed by
> asserting the view is *healthy* (`loaded`, no `last_error`); both probes are recorded
> in the test's docstring.
>
> **#976 — the PLAN caught up with reality.** s190 typed "case↔run link = a scalar
> `run_id`, migration `0019`" and it **never entered the PLAN**; s191 grounding refuted
> it on three measured reasons (re-fireable runs, per-PROPOSAL approval, the
> provisional/ratify split) and `0019` shipped as the accepted quote instead. **The
> dispatch was wrong and the drafter caught it** — told to mark the decision superseded
> "where it sits", it found no such text and said so; Code confirmed by grep. Dev DB
> `0017` → `0019` on Cray's go, pre-flighted — `repair_case_closeout` verified EMPTY,
> which made `0018`'s NOT NULL `vendor` column safe rather than assumed. Suite **3572 →
> 3597**.

#### Recent Decisions row — session 181

| 2026-07-28 | **s181 — CLAUDE.md full slim (#941): the 11.1 KB footer changelog RETIRED to git history; 33,014 → 21,524 B (−35.2%).** NEW convention: a constitutional edit bumps the footer date only — `git log --follow -- CLAUDE.md` is the amendment history. Coverage verified BEFORE the cut; no binding rule's substance changed. The <200-line LOCKED target was unreachable → Cray ruled (b): target <20 KB + a follow-up extraction pass | `85efe52` (#941 merge, head_commit) / `CLAUDE.md` |

<!-- Recent-Decisions row rotated out of docs/STATUS.md by the s202 reconcile (R2: newest 10 rows) -->
| 2026-07-29 | **s189 — PLAN-0096 Steps 1–7 and 9 COMPLETE (8 of 10), #965–#968.** Partner round-2 answers closed 5 of 7 questions. Step 6 = the partner's real 8-step task chain (alembic `0016`); `pm_due` = a sixth LINE event, group recipient, read off persisted `judge_service_due` verdicts. Cray typed the prerequisite-anchored clock + the AC-8 bump. Unplanned (#966/#967): an ORM↔alembic registration guard — **a comparison means something only when at most ONE side is hand-maintained**. Suite → **3552** | `13aa2f0` (#968 merge, head_commit) / `26e61b3` (#965) / `docs/plans/done/0096-fleet-flow-completion-phase1.md` |

### Rotated 2026-08-04 (session 203 reconcile — PLAN-0101 drafted with three unruled SDs + its Step 1 shipped + four stale claims retired, #1021–#1023)

_Both session-196 Current Focus blocks, rotated out together: adding the s203 block made the window span five sessions, and R2 keeps the four newest. The block-byte cap was not the binding constraint here (each was under 4,096 B) — the session window was._

> **Session 196, 2026-07-31 (head_commit `5382052` → `4846d5e`) — one PR merged
> (#1003), 0 open. The theme: an intermittent flake root-caused by MEASUREMENT —
> which refuted the leading hypothesis and found two sites worse than the reported
> one.**
>
> **The failure.** `test_accepted_quote_endpoint.py::test_a_cheaper_quote_arriving_later_does_not_rewrite_history`
> failed once in three full-suite runs. **The leading hypothesis was refuted by
> construction:** Postgres `now()` / transaction-start is not involved — there is no
> `server_default` on any timestamp column; both stamps are Python
> `datetime.now(UTC)`, in separate requests and separate transactions. **Measured
> instead:** the dev box's clock steps **backwards 20x per 300 s, every step
> ≥ 400 ms** (worst −592 ms) against a vulnerable window of **90–166 ms** ⇒ **~0.9%
> flake per execution**, matching the observed 1-in-3. Reproduced deterministically
> three ways, incl. a frozen clock through the real HTTP path — which also exposed
> **POST and GET disagreeing about the same case** (`45500.50` vs `39000.00`).
>
> **`<=` → `<` was tried and REJECTED on evidence:** all 63 tests in the 6 touching
> files pass either way (a coverage gap in itself), and the swap fixes only the tie
> that cannot occur in production, does nothing for the inversion that does, and
> breaks the equal-stamp case. **Two further sites, both worse than the reported
> one:** `latest_accepted_quote` feeds the DOA gate via `governed_case_facts`, so a
> backward step reports the **superseded** acceptance (wrong ฿, wrong vendor, the
> operator's stated reason dropped); and `repair_spend_export.py:587`
> sorts-then-overwrites, so the month-end export can show a provisional gate outcome
> instead of its ratification.
>
> **The un-defer trigger did NOT literally fire** — both orderings it enumerates
> remain display-only, as s169 found. What failed is the safety-margin *argument*,
> whose enumeration was scoped by subsystem **and** by column vocabulary: the
> PLAN-0088 guard machinery flags **2** sites repo-wide on its current 3-name
> vocabulary (exactly the pair the docstring named) and **12** once the repair-case
> column names are added. Classified **`superseded by new info`** per `CLAUDE.md`
> §6, not "was an error".
>
> **PLAN-0099 merged (#1003), five SDs all Cray-ratified:** SD-1 store-at-write
> (eliminate the re-derivation); SD-2 backfill marks the value **reconstructed**,
> not recorded (a third option neither drafted alternative offered); SD-3 (a)
> `latest_closeout` (b) `justifications[-1]` (c) `repair_spend_export.py:587` all
> ride migration `0023`; SD-4 retain the positional-read rule, rewritten rationale.
> **No production code changed** — execution starts at Step 1 (forcing tests, RED
> first). Numbered 0099 because a concurrent session claimed 0098 (#1001)
> mid-flight. Full detail: `docs/plans/done/0099-wall-clock-root-fix-store-at-write-and-sequence.md`.

> **Session 196, 2026-07-31 — SECOND workstream, same session (head_commit `a8912e0` →
> `5382052`): four PRs merged (#999–#1002). s196 ran TWO concurrent workstreams; this
> block and the one above are deliberately separate — one merged block would breach the
> 4,096 B per-block cap. Theme: two vocabulary guards pinned by measurement, then
> PLAN-0098 ratified and its backend built.**
>
> **#999 (`399fbe0`) — the CSS-class guard widened from 1 asset to all 15** (found by
> glob): 883 defined / 873 applied / **33 undefined** → a two-category allowlist under
> set equality in both directions — 4 JS lookup hooks (permanent, correct); 29 no-rule,
> of which 3 sit on inline-styled elements (semantic markers, NOT debt) and 3 are state
> toggles on a view root nothing reacts to (the likeliest real defects). Four scanner
> defects each got a permanent test — worst two: `classList.toggle(token, force)`'s
> boolean second arg read as a class name, and `api.js`'s whole `s-*` vocabulary
> invisible because it only RETURNS status names, applying no class.
>
> **#1000 (`f931b8b`) — `EconomicImpact.kind`'s documented vocabulary pinned to what
> producers emit** (five kinds now, set equality both directions vs producers found by
> glob). #994 (s195) had added `overpay_avoided` while the Field description — the one
> place a reader learns the vocabulary, shipped in the OpenAPI schema — still listed
> four. Deliberately kept OUT of PLAN-0098 so AC-6 ("zero engine build") stays absolute.
>
> **#1001 (`4bb9494`) — PLAN-0098 ratified** (fleet View G, `Status: Draft`): a mirror
> of `verticals/procurement/hero_demo/` by FUNCTION, not by shape. Cray typed SD-1 (a)
> unregistered verticals fall back to the procurement hero; SD-2 the assumptions strip
> is always-visible; **SD-3 = (c), differing from the draft's (a)** — lead with the
> measured ฿48,000, the partner's fraud origin story rides as narrative copy only,
> never a rendered figure; AC-9 added as that ruling's oracle. The drafter's AC-6
> carve-out was withdrawn at Code's R2.
>
> **#1002 (`5382052`) — PLAN-0098 Steps 1–4: fleet's View G backend + its vertical
> seam.** New `FleetHeroImpact` (measured `quoted_repair_thb` vs modelled `impact` —
> REQUIRED, validator-rejects empty `assumptions`);
> `verticals/fleet_maintenance/hero_demo/` (3 files) runs the real engine over the
> spec-loaded ladder — ฿48,000 → เจ้าของกิจการ, ฿15,000 → ผจก.เดินรถ, plus the
> fleet-only `three_quote` rule-gate card; a lazy `_HERO_BUILDERS` seam in `demo.py`
> on `settings.oct_vertical` (**ADR-0031 D4 corollary 1 FIRED at N=2**).
> `HeroImpactLedger` untouched (ADR-0030 D2) — `/impact` unions at the decorator.
> AC-1/2/3/4/5/6/8 closed — **AC-6 + AC-4 verified by empty `git diff`, not
> asserted**; Steps 5 (frontend) + AC-7/AC-9 remain. Two deviations recorded, not
> absorbed: Step 2's "run the real `compute_three_quote`" is impossible (events carry
> no vendor counts) — the stamped basis is READ per `sourcing.py:79-82`, still
> satisfying AC-2; and AC-2's set-equality parity cannot hold (2 bands vs 3 rungs) —
> implemented as the stronger per-side derivation from the loaded spec.
>
> **Suite 3676 → 3700 / 8 skipped throughout** — same skip count, nothing silently
> disabled; ruff + format + `mypy --strict services/` + `alembic check` clean; guards
> exit 0; CI `gate` pass, merge-commit `git diff` = 0 bytes, and the full suite re-run
> on every merge commit. **16 non-vacuity probes**, each RED against its NAMED test,
> restored from `/tmp` and diff-verified; **two probes were themselves defective and
> read GREEN** before correction — caught only because each is bound to the one test
> it must redden. The 3 new `hero_demo/` files are named in
> `_POST_SCAFFOLD_DONOR_FILES` with a prose reason (fleet is the scaffolder's golden
> donor; a governed hero is bespoke per partner, ADR-0032 D1.2); the exclusion proven
> surgical — a stray `.py` in the donor still reddens the test.

<!-- Recent-Decisions row rotated out of docs/STATUS.md by the s203 reconcile (R2: newest 10 rows) -->
| 2026-07-30 | **s191 — a REAL repair case now reaches the governed gate (#975–#977).** The accepted quote (ใบที่ตกลง, alembic `0019`) gives the DoA ladder a ฿ figure existing BEFORE the work and tracing to recorded evidence; Cray typed the required FK + reason-only-when-not-cheapest. The case → event path wires it in with **zero engine and zero adapter-`__init__` diff**. One probe came back GREEN — a vacuous oracle a fail-soft handler was hiding. Suite → **3597** | `99b752f` (#977, head_commit) / `d3f2919` (#976) / `d781683` (#975) / `docs/plans/done/0096-fleet-flow-completion-phase1.md` §Step 8 |

<!-- RELOCATED 2026-08-04 (session 205): the two sections below were rotated by the s196 and s197 reconciles but appended to 2026-h1g-status.md, whose declared period ends 2026-07-24 (session-171). Moved here per the runbook rule that rotations append to the base (memory-architecture.md R6). Content is byte-identical to what h1g held; placed before the s204 section so the base stays chronological. The matching s196/s197 Current-Focus blocks were already in this file. -->

## Rotated this reconcile (session-196, 2026-07-31 — the wall-clock root-fix reconcile; PLAN-0099 drafted + merged, #1003)

### Recent Decisions row

Rotated out when session 196's row entered the last-10 window.

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-28 | **s182 — PLAN-0094 Step 6 executed, AC-10 CLOSED (#943): all 11 ACs closed or withdrawn, on a FULL FRESH 18/18 non-vacuity sweep** — Cray typed the full re-sweep rather than citing the recorded s177/s180 runs. **`missing_red` EMPTY for all 18**; sibling L2/L3/L4 invariance held. **M-A's blast radius is 8 L1 rows, not the 3 first predicted** — the session's prediction was too narrow. Applied by a harness script, not the Edit tool (the mutated files are the session's own live hooks) | `1d0649f` (#943 merge, head_commit) / `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md` §Step 6 |

---

## Recent-Decisions row — s183

Rotated out when session 196's SECOND-workstream row entered the last-10 window.

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-28 | **s183 — PLAN-0094 ARCHIVED (Cray released the live-loop soak), and the goal-gate `evaluations: 0` finding DIAGNOSED: the gate is not broken, its warn path is unobservable.** OQ-4 re-homed to an Active TODO rather than buried in `done/`. _[s194: this row's "the behaviour is ratified" reading was REFUTED — see PLAN-0097.]_ | `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md` §Step 6 + §OQ-4 / `docs/plans/done/0097-goal-gate-warn-path-trail.md` §"The ADR-0018 determination" |


<!-- rotated 2026-07-31, session 197 (STATUS reconcile, PR after 687705d) -->
| 2026-07-28 | **s184→s185 — ADR-0034 "governed exception family" ACCEPTED (#948) + PLAN-0096 "fleet flow completion Phase 1, Lean KPI-first" merged as Draft (#949).** Partner-driven: 18/18 discovery answers → three mechanisms (escalate-never-skip waiver / evidence-alternative E-3 / deferred-ratification E-2+E-4); SoD + compliance stay NON-waivable. Cray resolved OQ-1/OQ-2/OQ-3 per the in-file recommendations. All 8 dispatch rejection criteria run adversarially, none fired | `760ceed` (#949 merge, head_commit) / `24c3b45` (#948) / `docs/adr/0034-governed-exception-family.md` |

## Rotated this reconcile (session-204, 2026-08-04 — PLAN-0101's tenant key end to end (#1026-#1029), and the half-stated escaping remedy)

> **Session 197, 2026-07-31 (head_commit `1dbd972` → `687705d`) — one PR merged
> (#1006), 0 open. PLAN-0098 COMPLETE and ARCHIVED in the same PR: View G's fleet
> branch shipped, all nine ACs closed. Theme, again: the donor's reuse contract was
> MEASURED, not re-read.**
>
> **PLAN-0098's own §D-D was wrong about the donor.** It asserted the joiner
> `governanceMoment` binds only `doa_tier` / `sod` / `governed_decision`, "all of which
> fleet produces". It also binds `po_id`, `declared_tier_id`, `is_off_avl_override`
> (`view-hero.js:42,46,49`), none of which fleet's audit emits — verbatim reuse would
> have rendered `undefined — display only` in the DOA card in front of an audience. A
> fleet joiner was written instead; SoD + join cards ARE reused verbatim, and
> `test_the_fleet_branch_reads_no_procurement_only_field` pins the correction.
>
> **Zero new CSS classes** — `EconomicImpact.baseline/governed` map onto the existing
> `hero-ledger` idiom, so `hero.css` is untouched, #999's class contract needed no
> allowlist edit, and the `?v=` bump covered exactly one asset (`c36` → `c47`).
> **AC-4 / AC-6 closed by EMPTY `git diff`** (`services/engine/`,
> `services/api/models/demo.py`, the donor's own suite) — evidence, not prose. **Five
> non-vacuity probes**, each an observable behaviour change, each RED against its
> NAMED test, each restored from a `/tmp` copy and byte-diff verified: a smuggled
> money literal, a dispatch that stops matching, a reverted cache token, a
> procurement-only field creeping back, a hidden assumptions strip.
>
> **Preview review is evidence, never a gate — and it found a real defect.** Runtime
> DOM probe on `OCT_VERTICAL=fleet_maintenance`: `undefined`=0, `NaN`=0, `hero-*`
> overflow=0, assumptions strip `hidden:false` / 144px / 6 lines, `hero-toggle`
> count=0 (**SD-2 confirmed in the DOM**, stronger than the lexical test). It also
> caught the authored `three_quote` rule rendering 143 chars of prose right-aligned
> in a 54px kv cell against a 19px row — moved to its own full-width line (`bfd789c`).
> **Found but NOT fixed (not this PLAN's):** the page overflows horizontally,
> `scrollWidth 1825` vs `clientWidth 1382`; all 24 overflowing elements are in the
> global nav bar, zero `hero-*`. Pre-existing header behaviour, tracked separately.
>
> **Cray typed four calls** in a "platform vs dev shop" discussion held BEFORE the work
> was picked; all four are carried as Active TODOs / `next_action`: (1) **measure the
> assembly-cost axis BEFORE an ADR argues it** — tripwire first, ADR on the number; (2)
> **no buyer-model mismatch** — the partners are mid-size regulated operators already,
> so `CLAUDE.md` §1's "SME" wording is loose phrasing to correct, not a strategy change;
> (3) **ADR-0032 D2's pilot gate = SATISFIED** (the fleet Phase-1 flow is a real pilot),
> so its Context snapshot must be **re-grounded**, unlocking shape-2 work — OWED, not
> done, G1-gated → `plan-drafter`; (4) **finish the fleet block** (PLAN-0098 ✅, then
> PLAN-0099 Steps 1–6) before the primitives block — insights found along the way may
> strengthen it.
>
> Suite **3700 → 3709** / 8 skipped — skip count unmoved, all 8 host-state/live
> opt-ins. `ruff` clean over 583; `mypy --strict` clean over 130; R1/R4/R7/R8 +
> registration guard exit 0. CI `gate` pass 5m56s on `bfd789c`; `git diff bfd789c
> HEAD` = 0 bytes; full suite re-run on the merge commit = **3709 / 8**.


<!-- Recent-Decisions rows rotated out of docs/STATUS.md by the s204 reconcile (R2: newest 10 rows) -->
| 2026-07-30 | **s193 — PLAN-0096 Step 8 item 5 COMPLETE (#982–#986): the month-end export end to end, with a KPI that can fail.** Row set = governed ∪ escaped money (a naive export reports 100% by construction). **Cray typed (ค)** traceable = governed AND documented; **(ก)** persist `three_quote_basis` (alembic `0022`). Two defects found by ORACLES, not review. Suite 3607 → **3646** | `367c15b` (#987 merge, head_commit) / `367a08e` (#986) / `ed09502` (#982) / `docs/plans/done/0096-fleet-flow-completion-phase1.md` |
| 2026-07-30 | **s192 — PLAN-0096 Step 8 item 3 COMPLETE (#979): the case → run link, proven on BOTH gate drivers.** The hook read `output_set`, so a rejected case was invisible (fix: `decided_entries()` reads `decisions`); `_outcome` let the run state outrank a refusal. **Cray typed: a refusal is checked FIRST.** Five non-vacuity probes, all RED as predicted. Suite → **3604** | `5dd8ce6` (#979, head_commit) / `docs/plans/done/0096-fleet-flow-completion-phase1.md` §Step 8 |


## Rotated this reconcile (session-205, 2026-08-04 — OQ-4 CLOSED and the s180 deny baseline corrected (#1031), PLAN-0100's fold-in (#1032), the s196/s197 archive relocation (#1033))

### Current Focus block — session 199

Rotated out when session 205's block entered the 4-session R2 window.

> **Session 199, 2026-08-01 (head_commit `2ed45b9` → `6a3f2d7`) — one PR merged
> (#1008), 0 open. PLAN-0099 COMPLETE and ARCHIVED: the wall-clock root fix, all
> six steps landing as a single six-commit stack.** The at-acceptance lowest quote
> is now stored at write time with a `recorded`/`reconstructed` provenance marker,
> both cross-row wall-clock comparisons are **deleted** rather than patched, and
> five latest-wins picks are re-keyed on a DB-assigned `seq`. All ten ACs closed.
>
> **AC-9's gate ran with its pass/fail read fixed before the run:** 3730 passed /
> 8 skipped / 0 failed; the eight skips are all host-state or live opt-ins and none
> is a node an AC names. That last clause was proven **positively** — the named
> nodes were re-run alone (38 passed, 0 skipped) rather than inferred from their
> absence among the skips, because a correct total can hide a wrong skip: one node
> starting to skip while another stops leaves the count at 8 either way. `ruff`
> clean over 586, `mypy --strict services/` clean over 130, five offline guards
> exit 0, CI `gate` pass, merge-commit `git diff` = **0 bytes**, and the full suite
> re-run on the merge commit (3730/8/0) since CI here is PR-only.
>
> **Cray ratified all four veto-open calls as-is** (typed): the stored figure stays
> NOT NULL, `seq` keeps UNIQUE on all five tables, the export row keeps figure +
> boolean + basis together, and `compute_accepted_the_cheapest` stays shared. Only
> the last carried an action — a docstring that claimed three callers where two
> reach it directly. Grounding the other three surfaced a coupling the veto list
> did not show: `cases.py` narrows `bool | None` to `bool` on the stated grounds
> that both operands are NOT NULL **columns**, so relaxing the DB constraint would
> silently change what the endpoint reports, not merely loosen a schema rule.
>
> **Separately — the MS-S1 hosting ADR's trigger FIRED.** Cray named two of
> PLAN-0095 OQ-1's four conditions directly (expose the demo beyond the LAN; test
> MS-S1 call performance over the internet, to inform scaling). The row had been
> sitting in In-Flight Discussions, not Active TODOs — it was **4 of 5** of the
> items s183 grouped as trigger-gated that were Active TODOs, and the odd one out.
> Its wording ("a LIVE candidate … still not drafted") also read as actionable
> while the handoff record said do-not-touch, and the reconciling fact — the
> trigger, and that it had not fired — lived only in a gitignored handoff and an
> archived PLAN's OQ block. Moved to an Active TODO with the trigger stated inline,
> following the OQ-4 row's precedent. Cray's initial lean is **B1** (app public,
> MS-S1 stays on LAN), veto open pending the ADR's own analysis. **The generalised
> rule is `docs/lessons/0034-deliberate-gate-outside-the-scanned-surface.md`** — a
> decision NOT to act needs the same recording discipline as an action, and its
> home is the list where someone would look for it if they thought it was missing.

---

### Recent-Decisions rows — s195, s194

Rotated out when session 205's two rows entered the last-10 window.

| 2026-07-31 | **s195 — fleet's Box-4 ฿ facet, a REAL PM-confirm race, PLAN-0097 COMPLETE (#994–#997).** **Cray typed** fleet's **event-anchored** ฿30,000 basis + the conservative **15%** recovery fraction. #995 fixed an **unlocked** read-then-write that let two deciders both get a 200 while one overwrote the other (`FOR UPDATE`, no migration). #996/#997 shipped the warn-path trail and archived the PLAN — **SD-2 = yes**, **SD-3 = dedup**. Suite → **3676** | `a8912e0` (#997, head_commit) / `8381c92` (#994) / `fa53911` (#995) / `docs/plans/done/0097-goal-gate-warn-path-trail.md` |
| 2026-07-30 | **s194 — two rotted-pointer repairs + Cray's STATUS-size ruling (#990, #991).** #990 fixed ADR-0025's archive pointer (wrong by whole FILE since the s144 re-charter; now cited by section heading, no line numbers). #991 drafted PLAN-0097 — the goal gate's silent warn path is an **implementation gap against ADR-0018 D5/V2-D1**, not ratified design. **Cray typed: SD-1 = (a), D5 controls (SD-2/SD-3 stay OPEN)**; **STATUS size = tighten the per-block cap + cut duplicates** | `b25cc98` (head_commit) / `c2584c8` (#990) / `docs/plans/done/0097-goal-gate-warn-path-trail.md` / runbook §R2 |


## Rotated this reconcile (session-205 addendum, 2026-08-04 — three parallel-session PRs recorded: #1034 cases-list tiebreak, #1035 seq-keyed chain state + alembic 0025, #1036 the 0024 audit_log backfill)

### Recent-Decisions rows — s197, s196 (two rows)

Rotated out when the #1034 / #1035 / #1036 rows entered the last-10 window.

| 2026-07-31 | **s197 — PLAN-0098 COMPLETE + ARCHIVED (#1006): View G's fleet branch, all nine ACs.** The donor joiner also binds `po_id`/`declared_tier_id`/`is_off_avl_override`, which fleet never emits (§D-D claimed otherwise) — a fleet joiner was written; SoD + join cards reused. Zero new CSS; AC-4/AC-6 by empty `git diff`; 5 probes RED. **Cray typed 4 calls**: measure assembly-cost first; no buyer-model mismatch; **ADR-0032 D2 pilot gate = SATISFIED** (Context re-ground OWED); fleet before primitives. Suite → **3709** | `687705d` (head_commit) / `docs/plans/done/0098-fleet-view-g-hero-demo-mirror.md` |
| 2026-07-31 | **s196, 2nd workstream (#999–#1002) — PLAN-0098 ratified + Steps 1–4 built; CSS-class guard → all 15 assets; `EconomicImpact.kind` → 5 kinds.** **Cray typed SD-1 (a), SD-2 always-visible, SD-3 = (c), differing from the draft's (a)**: lead with the measured ฿48,000 — the fraud origin story is narrative copy only, never a rendered figure (AC-9 = its oracle). Backend runs the real engine over the spec-loaded ladder via `_HERO_BUILDERS` (ADR-0031 D4 corollary 1 FIRED at N=2). Suite → **3700** | `5382052` / `4bb9494` / `docs/plans/done/0098-fleet-view-g-hero-demo-mirror.md` |
| 2026-07-31 | **s196 — PLAN-0099 drafted + merged (#1003): the wall-clock root fix.** An intermittent quote-history flake was **measured**, not inferred — the dev clock steps back 20x/300 s (every step ≥400 ms) against a 90–166 ms window ⇒ ~0.9%/run; the Postgres-`now()` hypothesis was **refuted by construction**. **`<=` → `<` rejected on evidence.** Two worse sites found (the DOA gate via `latest_accepted_quote`; the month-end export). **All 5 SDs Cray-ratified** — store-at-write, backfill marked **reconstructed**, three riders on migration `0023`. No production code changed | `4846d5e` (head_commit) / `docs/plans/done/0099-wall-clock-root-fix-store-at-write-and-sequence.md` |

| 2026-08-03 | **s202 — G1/G2 made DETERMINISTIC (#1013/#1016); ADR-0035 D2's amendments COMPLETE (#1014); ADR-0032 Context re-ground (#1015); PLAN-0100 drafted (#1017); nav-bar overflow fixed (#1018).** The classifier was *measured* non-deterministic at `temperature 0` (self-consistency 0/4, 3/12 blank), so the gate now reads the target's `**Status:**` line and the classifier's G1/G2 arm is unwired. **Cray typed: PLAN-0100 absorbs the UI work D5(2) implies.** SD-1..SD-5 unruled → execution gated | `ef2c898` (head_commit) / [#1018](https://github.com/CrayJThiemsert/vero-lite/pull/1018) / `docs/adr/0035-hosting-and-exposure-model.md` / `docs/plans/0100-exposure-published-demo-surface.md` |
| 2026-08-01 | **s199 — PLAN-0099 COMPLETE (10/10 ACs) and ARCHIVED; the MS-S1 hosting ADR's trigger FIRED.** Six-commit stack merged as one PR: stored at-acceptance figure + provenance, both wall-clock comparisons deleted, five picks re-keyed on `seq`, the ordering guard widened to `services/`. AC-9 proven positively (named nodes re-run alone, 38/0) rather than inferred from the skip total. **Cray ratified all four veto-open calls as-is.** Separately, Cray's stated intent to show the demo over the internet fired two of OQ-1's four conditions; row moved In-Flight → Active TODO, initial lean **B1** | `6a3f2d7` (head_commit) / [#1008](https://github.com/CrayJThiemsert/vero-lite/pull/1008) / `docs/plans/done/0099-wall-clock-root-fix-store-at-write-and-sequence.md` |
| 2026-08-04 | **s204 — the `bash -c` escaping remedy was stated in HALVES in three places at once (#1026/#1027).** A pytest run read `EXIT=0` with two tests RED: the advisory named `\$`-escaping but not the SINGLE-quoted outer argument, so following it literally kept double quotes and fabricated a zero. The hook advisory gains a **4th predicate** (any `$` inside a double-quoted `bash -c` argument, escaped or not) and `CLAUDE.md` §8 now states **both** halves. **§8 and lesson 0007 §1.1 were correct throughout — only the enforcement was half-built.** | `e549e98` (#1027) / `017cf94` (#1026) / `docs/lessons/0007-harness-exit-code-artifact.md` §6.1 |
| 2026-08-04 | **s203 — PLAN-0101 drafted (#1021), its Step 1 SHIPPED (#1022), four stale claims retired (#1023).** All three SDs are ADR-0035 D7 describing what does not exist: the D7(iv) "session/repository seam" (grep `tenant` in `services/` = **0**), "the reproducibility guard" (there are **three**), D7(vi)'s **2** uniques (census = **12**). Steps 2–6 BLOCKED-ON-SD. A probe CONFIRMED `alembic check` sees a new column but **not** a `server_default`. Suite **3792 / 8** | `592124b` (head_commit) / [#1022](https://github.com/CrayJThiemsert/vero-lite/pull/1022) / `docs/plans/done/0101-tenant-key-column.md` |
