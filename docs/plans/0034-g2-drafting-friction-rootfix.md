# PLAN-0034: G2 drafting-friction root-fix — stop the classifier over-firing + exempt the `plan-drafter`'s uncommitted draft-write from the G2 PreToolUse gate

**Status:** Draft
**Owner:** Claude Code (execution) — drafted by Cowork (Tier-1, ADR-009 D1); Code commits (ADR-009 D2)
**Created:** 2026-06-21
**Related ADRs:** ADR-009 (Cowork Tier-1 authoring D1 / "only Code commits" D2 — **preserved, not amended**), ADR-013 (autonomy-axis relocation; D2 deterministic deny reinforcing ADR-009 D2 — **the mechanism this PLAN refines, possibly a one-line amendment — see SD-3**), ADR-012 (Cowork free-form; D4.3 disclosure at foot)

> **Drafting provenance.** Drafted (uncommitted) by Cowork in Tier-1 governance-authoring mode under ADR-009 D1, off the Code-authored session-71 dispatch (`.claude/handoffs/session-71/2026-06-21-0506-code-cowork-g2-drafting-friction-rootfix-dispatch.md`, anchors code-verified by Code against `main` `0073e32`). Code reviews + commits via a `docs/*` PR (ADR-009 D2); Cray ratifies. This PLAN **drafts** the design; it implements nothing (see Out of Scope). **Author≠reviewer disclosure (ADR-012 D4.3):** at the foot of this file.

---

## Goal

The G1/G2 governance gate has one **legitimate** job and two **illegitimate** side-effects, and this PLAN removes only the latter two while keeping the first intact. The legitimate job: a *new* PLAN/ADR (or an edit to an Accepted ADR) cannot be authored inline by the main Code agent — it routes through Cowork (ADR-009 D1) or the in-harness `plan-drafter` subagent, and Code commits (ADR-009 D2). That routing is working as designed (this very PLAN exists because of it). The two illegitimate side-effects: **(A)** the pause/proceed/dispatch classifier **over-fires** — it emits `dispatch`/`pause` on edits that are *not* new-artifact authoring (a CLAUDE.md constitutional edit mis-typed as a "new ADR"; a status/lifecycle flip of an already-existing artifact; a task that has *already* been routed to Cowork), each a manual catch every time it happens (≥3 incidents, s67/s68, and once more live while the dispatch was being written); and **(B)** the project-level classifier gate **denies the `plan-drafter` subagent's own draft-write** — the dispatch says "spawn `plan-drafter` to draft this," then the same gate fires on the drafter's `Write` of `docs/(adr|plans)/NNNN-*.md` (G2 = Write + new file) and denies it, a mutual deadlock. This PLAN drafts a two-pronged fix — **prong 1** tightens the classifier (its registry + system-prompt guidance + the offline gold set) so it stops the spurious `dispatch`/`pause`; **prong 2** exempts the sanctioned `plan-drafter` subagent's uncommitted draft-write from the project-level classifier gate (the subagent's writes stay governed by the H2 allowlist + G5 commit-block + PR review, which are the real oversight). The invariant — **Code never authors *committed* governance unilaterally** (G5 / ADR-009 D2) — is untouched. The implementation is a later, separate PR that references this PLAN.

| failure mode | where | what fires | why it's wrong | prong |
|---|---|---|---|---|
| **A — classifier over-fires** | Stop-side arm (`stop_continuation.py` → `_sonnet_classifier`) | `dispatch` / `pause` on a non-new-artifact edit | no *new* `NNNN` is being consumed (CLAUDE.md / lifecycle-flip / already-dispatched) — there is nothing to draft | 1 |
| **B — gate denies the drafter** | PreToolUse arm (`pretooluse_classifier_dispatch.py`, project-level) | `deny` (spawn-redirect) on the `plan-drafter`'s own `Write` | the drafter's write *is* the sanctioned output of the dispatch; redirecting it to "spawn `plan-drafter`" when you *are* `plan-drafter` deadlocks | 2 |

---

## Fact-pack — verified repo state this PLAN reasons about (read 2026-06-21)

Every claim below was checked against the live repo before assertion (Tier-1 fact-pack rule). Three of them **sharpen the dispatch's framing** and are flagged ⚠ — surfacing cross-file structural divergence is the catch class the dispatch asked for.

1. **The gate is two arms over one classifier brain.** `.claude/hooks/pretooluse_classifier_dispatch.py` is the **PreToolUse arm**: a cheap deterministic pre-filter (`_detect_signature`) detects a G1/G2 *signature*, then `_sonnet_classifier.classify()` returns `proceed` (→ allow, exit 0) / `pause` (→ `deny` + surface) / `dispatch` (→ `deny` + spawn-redirect via `_build_dispatch_deny_reason`). `.claude/hooks/stop_continuation.py` is the **Stop-side arm**: at turn-end it calls the *same* `_sonnet_classifier.classify()`, and on `dispatch` emits a `block` directive instructing the main agent to spawn `plan-drafter`. Same brain, two trigger points.

2. ⚠ **The PreToolUse pre-filter is already immune to the CLAUDE.md and PLAN-lifecycle over-fires — so prong-1 acts on the *Stop-side* arm + the brain, not the pre-filter.** `_detect_signature` only returns non-`None` when `_is_governance_path(file_path)` matches `^docs/(?:adr|plans)/\d{4}-[\w\-]+\.md$` (regex `_GOVERNANCE_PATH_RE`). So a **CLAUDE.md** `Write`/`Edit` never reaches the classifier through the PreToolUse arm (path miss → exit 0). Likewise G1 there requires the on-disk file to currently match `Status: Accepted` (`_STATUS_ACCEPTED_RE`, scanned over the first 20 lines) — and the PLAN **template** vocabulary is `Status: Draft|Ready for execution|In progress|Complete` (`docs/plans/0000-template.md`), while a ratify-flip reads the *pre-edit* status — so a flip-edit does *not* trip the PreToolUse G1 pre-filter. (**R2 correction at commit (Code):** a few PLANs nonetheless adopted the ADR-style `Status: Accepted` — e.g. `docs/plans/done/0026` — so *editing an already-`Accepted` PLAN* would legitimately trip G1; that is a real G1, not the over-fire. The s67 ratify-flip over-fire was confirmed **Stop-side** per the STATUS s67 record, so prong-1's Stop-side targeting is unchanged.) **Consequence:** the s68 CLAUDE.md mis-type and the s67 PLAN ratify-flip over-fires came from the **Stop-side arm** (which has *no* path/status pre-filter — it runs the LLM on the transcript every turn), not the PreToolUse pre-filter. Prong 1 must therefore target the **classifier brain's guidance** (`_sonnet_classifier._build_system_prompt`) + the **registry it reads verbatim** (`.claude/autonomy-triggers.md`) + the **gold set** — *not* loosen the (already-correct) PreToolUse pre-filter.

3. **The classifier brain has no CLAUDE.md / already-dispatched / existing-vs-new guard today.** `_sonnet_classifier._build_system_prompt` instructs "default to PAUSE; DISPATCH only on a D-row governance-drafting need; spurious dispatches are worse than spurious pauses," and the registry's **D1/D2** rows (`.claude/autonomy-triggers.md` §"Auto-handoff triggers") describe "Cray ratifies a decision that warrants a new ADR" (D1) / "a multi-step plan needs to be drafted" (D2). Neither the prompt nor the D-rows carry an explicit negative guard for: (a) a non-`docs/(adr|plans)/NNNN` target (e.g. CLAUDE.md), (b) a task already routed to Cowork / `plan-drafter` (a dispatch handoff already exists), or (c) a *status/lifecycle edit of an existing* artifact (vs authoring a new one). These three guards are prong 1.

4. **The gold set is the offline test bed + the gate; it is safety-weighted.** `benchmarks/stop_classifier/gold.yaml` holds **23 cases** today — 10 `pause`, 8 `proceed`, 2 `dispatch`, plus 3 "dispatch discriminator: surfaced vs ratified" cases (`pause-pending-formality-decision`, `pause-handoff-describes-future-plan-thread`, `dispatch-plan-after-ratified-formality`). Scoring (per the file header + `run_eval.py`): `expected=pause` answered `proceed`/`dispatch` = **HARD FAIL**; `expected=dispatch` answered `proceed` = **HARD FAIL**, answered `pause` = acceptable soft miss. There is **no** CLAUDE.md negative, no already-dispatched negative, and no PLAN-lifecycle-flip negative in the set today — prong 1 adds them.

5. ⚠ **The gold *re-score* is host-state (Cray-gated, MANUAL-only) — it is NOT the offline gate.** `benchmarks/stop_classifier/run_eval.py` is documented "⚠️ MANUAL ONLY — hits the live MS-S1 Ollama server … warming/running MS-S1 models is a host-state change — run only with Cray's go" and is excluded from CI (`pytest testpaths = ["tests"]`). So "the offline gold is the gate" resolves to: **editing `gold.yaml` (add cases) is offline and part of the gate; *running* the candidate model against it is the optional live evidence after Cray's go.** The hard offline gate for this PLAN is therefore the **deterministic hook unit tests** (`tests/`) + ruff + mypy --strict + a well-formed/parseable `gold.yaml`. (This matters: most of prong 1's effect is mediated by the LLM, whose true measurement is the gated re-score; the *deterministic* slices of both prongs are what CI can actually pin — see Step 4 / SD-2.)

6. **Prong 2 — the project-level classifier arm fires on the subagent and overrides the H2 allow.** `pretooluse_classifier_dispatch.py` is wired project-level (settings-level), so it fires on the **`plan-drafter` subagent's** `Write` too. For a fresh `docs/(adr|plans)/NNNN-*.md` the subagent write is exactly the G2 signature (`Write` + path match + file does-not-exist → `_detect_signature` returns `"G2"`), the classifier runs, and a conservative `dispatch`/`pause` verdict → `deny`. Meanwhile `.claude/hooks/pretooluse_plan_subagent_write_deny.py` (the **H2** hook, wired via `.claude/agents/plan-drafter.md` frontmatter) *allows* the same write (it is under the `docs/adr/` | `docs/plans/` allowlist) — but a project-level `deny` overrides a subagent-scoped allow. Hence the deadlock: the dispatch says "spawn `plan-drafter`," and the same gate denies the drafter's legitimate draft-write.

7. ⚠ **The H2 hook deliberately does NOT inspect `agent_id`/`agent_type` — and its header warns a future project-level move must "fail loudly so the boundary inversion is caught."** `pretooluse_plan_subagent_write_deny.py`'s module docstring: *"This hook intentionally does not inspect agent_id/agent_type. Subagent scoping comes from the frontmatter wiring; if a future change moves the hook to project-level the test suite must fail loudly so the boundary inversion is caught at review time."* **Nuance (load-bearing for SD-1):** that caveat warns against making a *subagent-scoping policy* govern the *main agent* (the H2 inversion). Prong 2 is the **opposite direction** — exempting the *subagent* from a *main-agent policy* (the G1/G2 gate). It does not create the H2 inversion, but it does raise the same root question the caveat is about: *how does a project-level hook reliably tell "this is the `plan-drafter` subagent" without brittle runtime inspection?* That detection signal is the open mechanism (SD-1).

8. **G5 (the commit-block) is the real oversight and is untouched by either prong.** `git commit`/`push`/`merge` from a non-Code identity is **deterministically denied** by `.claude/hooks/pretooluse_git_deny.py` (G5 row in `.claude/autonomy-triggers.md`; ADR-009 D2 / ADR-013 D2 — and per `stop_continuation._build_dispatch_instruction`, the composed identity gate denies any git op from a subagent regardless of `CLAUDE_TIER`). The `plan-drafter` subagent therefore **cannot commit** even with prong 2's draft-write exemption; Code commits via PR, Cray reviews. This is precisely what makes prong 2 safe (SD-4).

---

## Acceptance Criteria

This is a **drafting** PLAN; the ACs gate the *plan's completeness and correctness*, and (for the implementation PR that later references it) the *design contract* the implementation must satisfy. Implementation-time ACs are tagged **[impl]**.

- [ ] **AC-1 — Prong-1 rules specified.** The PLAN specifies the three classifier guards (non-`docs/(adr|plans)/NNNN` target incl. CLAUDE.md; already-dispatched; existing-edit/lifecycle-flip vs new-artifact), names the exact surfaces each is authored on (`_sonnet_classifier._build_system_prompt` and/or `.claude/autonomy-triggers.md` D-rows), and resolves SD-2 (rule wording + deterministic-vs-LLM split).
- [ ] **AC-2 — Prong-1 gold cases enumerated.** The PLAN enumerates the gold negatives to add — **at minimum** the s67 PLAN ratify-flip, the s68 CLAUDE.md mis-type, and the live "already-Cowork-dispatched re-dispatch" incident — each as `expected: pause` (no-dispatch) per the safety-weighted convention (a spurious `dispatch` = HARD FAIL), and states that the existing true-`dispatch` positives must **not** regress.
- [ ] **AC-3 — Prong-2 mechanism specified.** The PLAN specifies how the project-level classifier arm stops denying the `plan-drafter`'s `docs/(adr|plans)/NNNN-*.md` draft-write, weighing the SD-1 options against the fact-7 boundary-inversion caveat, and names the **fact-finding prerequisite** (what subagent signal the PreToolUse payload reliably carries in this Claude Code version).
- [ ] **AC-4 — Invariant stated and load-bearing (SD-4).** The PLAN states explicitly that **G5 (commit-block) + the PR-review boundary + ADR-009 D2 "only Code commits" are untouched**, and that prong 2 unblocks only the *uncommitted draft-write*; that the `plan-drafter` remains bounded by the H2 allowlist to `docs/(adr|plans)/*.md`.
- [ ] **AC-5 — ADR-need resolved (SD-3).** The PLAN decides PLAN-only vs an ADR-013 (and/or ADR-009) amendment, with reasoning, and — if PLAN-only — specifies the `.claude/autonomy-triggers.md` annotation that records the prong-2 scope refinement (G2 governs the main agent; the subagent draft-write is H2-governed) per the registry's own Change protocol.
- [ ] **AC-6 — Guardrails encoded.** The PLAN encodes the Out-of-Scope guardrails (no G5 change; no G1 Accepted-ADR-edit loosening; no L1 loop-detect change; live re-score is Cray-gated, the offline gate is CI).
- [ ] **AC-7 [impl] — Prong-2 deterministic tests.** The implementation PR proves (named tests, offline): (a) a `plan-drafter` subagent `Write` to `docs/(adr|plans)/NNNN-*.md` is **no longer denied** by `pretooluse_classifier_dispatch.py`; (b) a **main-agent** new-PLAN/ADR `Write` to the same path is **still gated** (G2 preserved for the main agent); (c) the exemption short-circuits **before** the LLM call (no network dependency in the test); (d) G5 still denies a git op from the subagent (negative test).
- [ ] **AC-8 [impl] — Prong-1 offline integrity.** `gold.yaml` parses and the new negatives are well-formed; the deterministic classifier unit suite (`tests/`) is green; ruff + mypy --strict clean. The live gold re-score (host-state) is run **only after Cray's go** and reported as evidence, not as a CI gate (fact 5).
- [ ] **AC-9 [impl] — No collateral regression.** The existing PreToolUse pre-filter behaviour (G1 on a truly-Accepted ADR edit still gates; G2 on a main-agent new write still gates) and the Stop-side true-`dispatch` D1/D2 positives remain behaviourally intact except where this PLAN deliberately changes them.

---

## Out of Scope

- ❌ **Any implementation.** No hook code, no `_sonnet_classifier.py` edits, no `gold.yaml` edits, no registry edit, **no benchmark run**. This PLAN is a plan; the implementation is a later, separate PR that references PLAN-0034 (CLAUDE.md §6 Plan Flow).
- ❌ **Touching G5 / the commit-block.** `pretooluse_git_deny.py`, the G5 row, and ADR-009 D2 "only Code commits" are the oversight that *makes prong 2 safe* — preserve both byte-for-byte (SD-4 / fact 8).
- ❌ **Loosening G1 (Accepted-ADR-edit gate).** Prong 1 removes *spurious* fires (CLAUDE.md / already-dispatched / existing-lifecycle-edit); it does **not** stop the gate from pausing a genuine mutation of an `Status: Accepted` ADR. A real G1 still pauses.
- ❌ **L1 loop-detect changes.** Separate concern (`pretooluse_loop_detect.py` / the L-rows); not touched.
- ❌ **A live classifier re-score as a gate.** Running gpt-oss:20b (or any candidate) on MS-S1 against the gold is **host-state, Cray-gated** (fact 5) — it is optional evidence *after* Cray's go, never a CI acceptance condition. The offline gate is the deterministic tests + the parseable gold edits.
- ❌ **Redesigning the dispatch contract or the `plan-drafter` agent.** The D1/D2 auto-handoff mechanism, the budget-reminder template, and the H2 allowlist shape are fixed; this PLAN refines *when* the gate fires and *who* it exempts, not the drafting protocol itself.

---

## Steps

### Step 1 — Prong 1a: guard the classifier against non-`docs/(adr|plans)/NNNN` targets (CLAUDE.md)

**Surfaces (impl PR):** `.claude/hooks/_sonnet_classifier.py` (`_build_system_prompt`), `.claude/autonomy-triggers.md` (the D1/D2 rows / a new negative-guard note), `benchmarks/stop_classifier/gold.yaml`.

The s68 incident: a **CLAUDE.md** constitutional edit Cray had *already routed to Cowork* was classified `dispatch` with `artifact_kind: adr` ("pick the next NNNN"). Per fact 2 this is a **Stop-side** over-fire (the PreToolUse pre-filter never sees CLAUDE.md). The fix lives in the classifier's *guidance*, read verbatim from the registry + the system prompt:

- Add an explicit negative guard: **D1/D2 dispatch applies only to authoring a *new* `docs/(adr|plans)/NNNN-*.md`.** A constitutional edit (CLAUDE.md), a convention/lesson/runbook/STATUS edit, or any non-`docs/(adr|plans)/NNNN` target has **no `NNNN` to consume** → it is never a D1/D2 dispatch. The classifier may still `pause` if such an edit independently crosses an always-pause row, but it must not emit `dispatch` with an `adr`/`plan` `artifact_kind` for it.
- Note the routing fact (so the model has the right mental model): CLAUDE.md is **Cowork-drafted by convention, not gate-routed** (CLAUDE.md §6 "Routing"); the gate's job is `docs/(adr|plans)/NNNN`, not the constitution.

**Deliverable:** the registry/prompt wording for guard (a) + the gold case `pause-claudemd-already-routed` (Step 4). (Resolves part of AC-1/AC-2; ties to SD-2.)

### Step 2 — Prong 1b/1c: guard against already-dispatched tasks and existing-artifact lifecycle edits

**Surfaces (impl PR):** same as Step 1.

- **1b — already-dispatched guard.** When the recent activity shows the task has **already been routed** — a Cowork dispatch handoff exists for it, or a `plan-drafter` spawn is already in-flight / just completed — the classifier must **not** re-emit `dispatch`. The correct outcome is `pause` (wait for the Cowork/subagent draft to return), never a second dispatch of the same work. This is the exact class of the **live incident** the dispatch flagged: while Code authored *this* dispatch, the Stop-hook auto-dispatched again, re-routing an already-Cowork-dispatched task to `plan-drafter` (and would have hit the prong-2 deadlock on the drafter's write).
- **1c — existing-edit / lifecycle-flip guard.** A **status/lifecycle edit of an existing artifact** (e.g. flipping a PLAN `Status: Ready for execution → Complete`, or a `git mv … done/`) is **not** authoring a *new* artifact and must not `dispatch`. ⚠ **Interplay with G1 (do not loosen):** a genuine mutation of an `Status: Accepted` **ADR** is still an always-pause G1 — this guard does **not** exempt that. The guard distinguishes *new-artifact authoring* (D-row dispatch) from *lifecycle bookkeeping on an existing file* (not a dispatch; routine), while G1's "mutating an Accepted ADR pauses" stays fully in force.

**Deliverable:** the registry/prompt wording for guards (b) + (c), with the explicit G1 non-loosening note + the gold cases `pause-already-dispatched-cowork` and `pause-plan-status-flip` (Step 4). (Resolves the rest of AC-1/AC-2; ties to SD-2.)

### Step 3 — Prong 2: exempt the `plan-drafter` subagent's draft-write from the project-level classifier gate

**Surfaces (impl PR):** `.claude/hooks/pretooluse_classifier_dispatch.py`; `tests/` (new deterministic tests).

The load-bearing change. The project-level arm must stop denying the sanctioned subagent's `docs/(adr|plans)/NNNN-*.md` draft-write, while still gating the **main agent's** inline new-PLAN/ADR write (G2 preserved for the main agent). The exemption should be **deterministic and short-circuit before the LLM call** (so the test needs no network and the subagent never eats a ~7s classify on its own legitimate write).

**Prerequisite — fact-finding spike (must precede the mechanism choice).** Determine what signal the PreToolUse payload reliably carries that identifies a subagent (and specifically the `plan-drafter`) tool call in this Claude Code version — e.g. an `agent_type`/`agent_id`/`subagent` field, an env marker, or none. The SD-1 mechanism choice **depends on** this finding; do not pick a mechanism before the signal is confirmed against the live harness. If no reliable signal exists, fall back to the H2-side option (see SD-1 option b) or surface the gap to Cray.

Mechanism options are surfaced in **SD-1** (recommend → Cray adjudicates). Whichever is chosen, the implementation must satisfy AC-7: subagent write allowed, main-agent write still gated, short-circuit before the API call, G5 still denies the subagent's git ops.

**Deliverable:** the spike finding + the exemption code-path spec + the four deterministic tests (AC-7). (Resolves AC-3; ties to SD-1/SD-4.)

### Step 4 — Gold negatives + offline integrity

**Surfaces (impl PR):** `benchmarks/stop_classifier/gold.yaml`, `tests/` (deterministic classifier unit tests), `benchmarks/stop_classifier/RESULTS.md` (only if a Cray-gated re-score is later run).

Add (at minimum) these `expected: pause` gold negatives — pause is the safe expected, and it makes any `dispatch` a HARD FAIL, which is exactly the over-fire being killed (fact 4):

| id (proposed) | models | why pause / no-dispatch |
|---|---|---|
| `pause-claudemd-already-routed` | a CLAUDE.md constitutional edit Cray has already routed to Cowork | not a `docs/(adr|plans)/NNNN` target → no `NNNN` to consume; already routed (1a + 1b) |
| `pause-plan-status-flip` | flipping a PLAN `Status: Ready for execution → Complete` / `git mv … done/` | lifecycle edit of an *existing* artifact, not new-artifact authoring (1c) |
| `pause-already-dispatched-cowork` | a task with an existing Cowork dispatch handoff; turn ends awaiting the returned draft | already dispatched — re-dispatch is the spurious fire (1b; the live incident) |

State explicitly that the existing true-`dispatch` positives (`dispatch-plan-draft`, `dispatch-adr-draft`, `dispatch-plan-after-ratified-formality`) must **not** regress to `pause`/`proceed`. The **offline** gate is: `gold.yaml` parses, the deterministic unit suite is green, ruff + mypy --strict clean (AC-8). The **live re-score** (gpt-oss:20b on MS-S1) is Cray-gated host-state — run only on Cray's go, reported as evidence (fact 5).

**Deliverable:** the enumerated gold negatives + the offline-gate definition + the explicit no-regression statement. (Resolves AC-2/AC-8/AC-9.)

### Step 5 — ADR-need + registry annotation

**Surfaces (impl PR):** `.claude/autonomy-triggers.md` (annotation per its Change protocol); conditionally `docs/adr/0013-autonomy-axis-relocation.md` (a one-line amendment — only if SD-3 lands "amend").

Resolve SD-3. If **PLAN-only** (the recommended lean): annotate the G2 row + the Auto-handoff section of `.claude/autonomy-triggers.md` to record the prong-2 scope refinement — *G2 governs the main agent's inline new-artifact write; the `plan-drafter` subagent's draft-write is governed by the H2 allowlist, not the classifier arm* — following the registry's own Change protocol (Cowork drafts the row, Code commits, cross-link from this PLAN). If **amend**: draft the one-line ADR-013 D2 clarification (G2's deny scope = main agent; the sanctioned subagent draft-write is an explicit carve-out, G5/commit-block unchanged) and gate the implementation PR on it (CLAUDE.md §8 "ADRs merged before related implementation").

**Deliverable:** the resolved ADR-need + the registry annotation text (and the conditional ADR-013 amendment scope). (Resolves AC-5.)

---

## Surfaced Decisions

Each carries a recommendation; **Cray adjudicates** all of them (Tier-1 rule #8 — surface, do not silently choose).

| # | Decision | Options | Recommendation (Cray adjudicates) |
|---|---|---|---|
| **SD-1** | **Prong-2 mechanism** — how does the project-level classifier arm exempt the `plan-drafter`'s draft-write? | **(a)** inspect `agent_type`/`agent_id` in `pretooluse_classifier_dispatch.py` and skip when writer = `plan-drafter`; **(b)** make the classifier arm **defer to the H2 subagent allowlist** for subagent writes (single source of truth for subagent write-governance = H2); **(c)** narrow the G1/G2 pre-filter to **main-agent** writes only (exempt the subagent context) | **Run the Step-3 spike first**, then **(c)** if a reliable non-`plan-drafter`-specific "is-subagent" signal exists (cleanest: exempts the subagent context generically, no brittle name-coupling, and — per fact 7 — this is the *opposite* direction from the H2 inversion the caveat warns about, so it is defensible); fall back to **(b)** if only a per-agent signal exists (keeps governance in H2). Avoid **(a)**'s name-coupling unless it's the only signal. **Whichever lands, add the loud test (AC-7b) that the main-agent path is still gated** — the same "fail loudly on boundary inversion" discipline fact 7 asks for. |
| **SD-2** | **Prong-1 rules + the deterministic-vs-LLM split** — exact wording of guards (a)/(b)/(c) and which (if any) can be made deterministic vs left to the LLM brain | Author all three as **LLM guidance** (registry + system prompt) only; **or** add deterministic pre-checks where a signal is available | **Hybrid:** keep guards (a)/(b)/(c) primarily as **registry + system-prompt guidance** (the Stop-side arm is LLM-only — fact 2), and add a **deterministic** belt-and-suspenders only where the PreToolUse arm already has the signal (it already excludes non-`docs/(adr|plans)/NNNN` paths and already-existing files — confirm no extra code needed there). Gold negatives all `expected: pause` (safety-weighted; a spurious `dispatch` = HARD FAIL). |
| **SD-3** | **ADR-need** — PLAN-only refinement, or an ADR-013 (and/or ADR-009) amendment? | **(a)** PLAN-only + a `.claude/autonomy-triggers.md` annotation; **(b)** a one-line ADR-013 D2 amendment carving out the sanctioned subagent draft-write; **(c)** both | **(a) PLAN-only** (agrees with Code's lean): the draft-write exemption does **not** touch "only Code commits" — G5 + PR review preserve ADR-009 D2 (fact 8). The registry annotation (Step 5) is the durable record per its Change protocol. **Escalate to (b)** *only if* Cray/Code regard "G2 denies *every* new-NNNN write regardless of writer" as a ratified ADR-013 D2 invariant — then a one-line clarifying amendment is the clean record and the impl PR gates on it (CLAUDE.md §8). |
| **SD-4** | **Invariant to assert** — what must the fix *not* weaken? | n/a — an assertion to pin | **Assert and keep intact:** Code never authors *committed* governance unilaterally. **G5 (commit-block)** + **the PR-review boundary** + **ADR-009 D2** are untouched; prong 2 unblocks only the *uncommitted draft-write*, and the `plan-drafter` stays bounded by the H2 allowlist to `docs/(adr|plans)/*.md`. AC-7d (G5 still denies the subagent's git op) is the negative-test proof. |

---

## Verification

How we know the PLAN (and later the implementation) is right:

1. **PLAN-level (this artifact, pre-commit):** both prongs specified with named surfaces; the three prong-1 guards + the three gold negatives enumerated; the prong-2 mechanism surfaced with the spike prerequisite; the invariant (SD-4) stated and load-bearing; all guardrails (no G5 / no G1 loosen / no L1 / live-re-score-is-Cray-gated) in Out of Scope. Fact-pack: every hook/path/row/gold-count citation verified against the live repo this session (see Fact-pack); three ⚠ corrections sharpen the dispatch's framing (the over-fires are Stop-side, not PreToolUse-pre-filter; the gold re-score is host-state not the offline gate; the boundary-inversion caveat is direction-specific).
2. **Impl-level (the later PR, for reference):** AC-7 (prong-2 deterministic tests — subagent allowed, main-agent still gated, short-circuit before API, G5 negative) + AC-8 (gold parses, deterministic unit suite green, ruff + mypy --strict clean) + AC-9 (no collateral regression of the PreToolUse pre-filter or the Stop-side true-`dispatch` positives). The live gold re-score, if run, is Cray-gated evidence appended to `RESULTS.md`, not a CI gate.
3. **Governance:** Cray ratifies (Draft → Ready for execution); Code R2-reviews the fact-pack and commits via a `docs/*` PR (ADR-009 D2). If SD-3 lands "amend," the ADR-013 amendment merges before the implementation PR (CLAUDE.md §8).

---

## References

- **Dispatch:** `.claude/handoffs/session-71/2026-06-21-0506-code-cowork-g2-drafting-friction-rootfix-dispatch.md` (Code-authored, session 71; anchors code-verified against `main` `0073e32`).
- **Anchors (code-verified this session):** `.claude/hooks/pretooluse_classifier_dispatch.py` (PreToolUse G1/G2 arm — `_detect_signature`, `_is_governance_path`/`_GOVERNANCE_PATH_RE`, `_has_status_accepted`/`_STATUS_ACCEPTED_RE`, `_build_dispatch_deny_reason`); `.claude/hooks/stop_continuation.py` (Stop-side arm — `_classify`, `_build_dispatch_instruction`, the D-row dispatch path); `.claude/hooks/_sonnet_classifier.py` (the shared brain — `classify`, `_build_system_prompt`, `_validate_dispatch_metadata`, `DISPATCH_ALLOWED_SUBAGENTS`/`ARTIFACT_KINDS`); `.claude/hooks/pretooluse_plan_subagent_write_deny.py` (H2 allowlist + the no-`agent_type`-inspection / boundary-inversion caveat); `.claude/hooks/pretooluse_git_deny.py` (G5, referenced); `.claude/autonomy-triggers.md` (G1/G2/G5 rows + the D1/D2 Auto-handoff section + the Change protocol); `benchmarks/stop_classifier/gold.yaml` (23 cases, safety-weighted); `benchmarks/stop_classifier/run_eval.py` (MANUAL-only, host-state, not in CI); `.claude/agents/plan-drafter.md` (H2 frontmatter wiring).
- **ADRs:** `docs/adr/0009-cowork-tier1-tier-topology.md` (D1 Cowork authoring / D2 "only Code commits" — preserved); `docs/adr/0013-autonomy-axis-relocation.md` (D2 deterministic deny reinforcing ADR-009 D2 — the mechanism refined here; possible one-line amendment per SD-3); `docs/adr/0012-cowork-second-freeform-tier.md` (D4.3 disclosure).
- **Governance:** `CLAUDE.md` §6 (Routing: proceed vs Cowork-dispatch; the G1/G2 mechanical overlay) / §7 (PR-flow) / §8 (ADRs merged before related implementation); `docs/lessons/0008-cowork-tier1-k1-k2-workflow.md` (the K-1/K-2 workflow under which this draft was authored).
- **Template:** `docs/plans/0000-template.md`; **shape precedent:** `docs/plans/done/0022-tiered-decision-routing.md` (a recent Cowork-drafted PLAN with the same fact-pack / Surfaced-Decisions / disclosure structure).

---

## Implementation Notes

For Code / the implementation PR. Cowork has no commit authority (ADR-009 D2); Code reviews + commits this draft (and, if SD-3 lands "amend," the ADR-013 amendment). Per K-1, Cowork could not run `validate_handoff.py` on the companion completion handoff; that handoff records the mental-validation substitute and flags the gap. AI-assisted per CLAUDE.md §8 (noted in the commit body, never as `Co-Authored-By`, per §7).

- **The spike (Step 3 prerequisite) is the one hard unknown.** The whole prong-2 mechanism (SD-1) turns on what subagent signal the PreToolUse payload carries in this Claude Code version — Code should confirm this against the live harness before picking (a)/(b)/(c). If no reliable signal exists, surface to Cray rather than guess.
- **The over-fires are Stop-side (fact 2)** — do not "fix" them by loosening the PreToolUse pre-filter, which is already correctly narrow. The fix is the classifier's guidance (registry + system prompt) + the gold set.
- **The offline gate is CI; the live gold re-score is Cray-gated host-state (fact 5)** — do not let an un-run live score block the PLAN, and do not run the live score without Cray's go.
- **G5 / "only Code commits" is the invariant (SD-4)** — if any change to prong 2 would let the subagent commit, that is out of scope and a hard stop.

### Author≠reviewer disclosure (ADR-012 D4.3)

This PLAN was **authored** by Cowork (Tier-1) directly from the Code-authored session-71 dispatch; it was **not** separately deliberated in a Cowork free-form (Tier-1b) session, so the specific self-deliberation risk D4.3 targets is low here. Per the spirit of D4.3: the three fact-pack ⚠ corrections (fact 2 — the over-fires are Stop-side, not PreToolUse-pre-filter; fact 5 — the gold re-score is host-state, not the offline gate; fact 7 — the boundary-inversion caveat is direction-specific) are Cowork's own findings against the dispatch's framing and have **not** been independently reviewed by another tier. **Code's R2 review + Cray's ratification are the remaining independent checks.** Cowork recommends Code specifically re-verify fact 2 (that a CLAUDE.md edit and a PLAN status-flip cannot trip the PreToolUse G1/G2 pre-filter, so prong 1 must act Stop-side) and the Step-3 spike finding before committing, since prong-1's targeting and prong-2's mechanism turn on them.
