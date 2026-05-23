# ADR-009: Cowork as Tier-1 Dispatch Author (Tier Topology Change)

**Status:** Accepted
**Date:** 2026-05-21
**Deciders:** Jirachai Thiemsert (founder)
**Related:** ADR-006 (vertical plugin architecture), ADR-007 (OCT engine contracts), ADR-008 (YAML ontology specification), CLAUDE.md §1 (precedence) + §6 (4-tier table) + §11 (Tier 2 operational policy), Lesson #5 (tier-system audit), Lesson #6 (surface→re-dispatch pattern); trial protocol `.claude/handoffs/session-10/2026-05-20-1345-code-cowork-tier1-trial-protocol.md`; parent discussion `.claude/handoffs/session-10/2026-05-20-1235-code-tier-collaboration-asymmetry-discussion.md`

## Context

The project runs four collaboration tiers (CLAUDE.md §6): Tier 0 Cowork
(research), Tier 1 Chat (strategy + dispatch authoring), Tier 2 Code
(repo writes + git), Tier 3 Cray (final authority). Across ten sessions
a recurring friction surfaced in the Tier 1 → Tier 2 handoff: Chat-tab
dispatches asserted repo facts as verified when they were not, and Code
caught the gaps downstream. The parent discussion
(`2026-05-20-1235-code-tier-collaboration-asymmetry-discussion.md` §1)
calibrated three incident baselines:

- **Incident #1** — Step 2b.1 rename + ref-graph dispatch: **5 Code-side
  surfaces**, resolved via a 5-cycle Lesson #6 chain (high cost).
- **Incident #2** — Step 2b.2 dispatch authored from a Code fact pack:
  **0 surfaces**, single-pass (low cost).
- **Incident #3** — PLAN-003 consultation dispatch: **3 pre-execution
  catches**, including a `phase: consultation` value not in the canonical
  schema enum (`tools/handoffs/_schema.py:61-69`).

The parent discussion §0 diagnosed the asymmetry as **structural, not a
Chat discipline defect** (F-1): Code reads disk and runs tools; Chat
reasons over Project Knowledge that can drift from repo HEAD. The three
incident-#3 catches all partition into "read-disk / run-tool" classes
that Chat structurally cannot perform in-thread (parent §2.2 table). The
hypothesis under test (trial protocol §1): the chronic
"assert-then-Code-catches" pattern is caused by **capability mismatch**
— Chat lacks direct repo read/write and runs from separate Project
Instructions that drift from CLAUDE.md — not by Chat-tier discipline
failure.

Cowork (Tier 0) does not share that limitation: it has direct repo
read/write and shares the same `CLAUDE.md` system reminder as Code. The
trial protocol (§2, §5) therefore tested whether moving Tier-1 dispatch
authorship from Chat to Cowork reduces the surface count without
introducing new failure modes, measured against four pre-locked criteria
C1–C4.

**Round 1** (PLAN-003 Phase 1 kickoff dispatch,
`2026-05-20-1530-cowork-plan003-phase1-kickoff-dispatch.md`) was a
concrete dispatch-authoring test (specifications, file paths, commit
plan). It passed under the amended criteria: pre-execution surfaces
**C1 = 0**, mid-execution Lesson #6 cycles **C4 = 0**, and Cray-attention
copy/paste rounds **C2 = 0** (engine closeout
`2026-05-20-1840-code-plan003-phase1-engine-closeout.md` §7.5). The
dispatch made the exact cross-file structural catch the hypothesis
predicted: Cowork read ADR-008 D2 (`docs/adr/0008-yaml-ontology-specification.md:39-63`,
map grammar) and plan §8.6
(`docs/plans/0003-ontology-engine.md:271-280`, list-of-dicts grammar)
directly and resolved the divergence per CLAUDE.md §1 precedence
(pre-exec status `2026-05-20-1510-code-cowork-tier1-trial-preexec-status.md`
§3.1). Cray ratified the PASS verdict 2026-05-21.

Two architectural constraints in Claude Desktop's Cowork feature surfaced
during the trial and were investigated in
`2026-05-20-1545-code-cowork-blocker-investigation.md` (§0, §1). Both are
documented Anthropic-side gaps with no shipped fix:

- **K-1 — bash UNC refusal.** Cowork's sandbox bash returns
  `UNC paths are not supported: \\wsl.localhost\...` on every invocation
  when the project Context folder is a WSL UNC path. The sandbox is a
  remote/cloud Linux VM that receives the UNC string as `cwd` and rejects
  it; Read/Glob/Grep/Write work only because they are proxied through the
  Windows desktop client. Tracked at anthropics/claude-code issues #45297
  (open), #49933, #56145. Consequence: Cowork cannot run
  `validate_handoff.py` to dog-food its own draft.
- **K-2 — `.claude/` write block.** Cowork's Write tool refuses any path
  under `.claude/`; the documented exempt-subdir allowlist
  (`commands`/`agents`/`skills`/`worktrees`) is not honored in the Cowork
  sandbox (blocker investigation §3 confirmed `.claude/agents/handoffs/`
  also fails). Consequence: Cowork cannot write directly to the canonical
  `.claude/handoffs/session-NN/` handoff path.

Cray chose **Path D** (accept the gaps + refine criteria) from the
blocker investigation §2, and amended trial criteria C2 and C3 (trial
protocol §5, §16) so that documented Anthropic-side tool gaps are
recorded as **known constraints**, not trial-failure modes. **Round 2**
(this dispatch — the post-trial mini-ADR per trial protocol §7.1.1 +
Q-Trial-4 ratification §13) tests a different capability class than round
1: ADR drafting is abstract synthesis (rationale, alternatives,
trade-offs), where round 1 was concrete dispatch authoring. This ADR is
both the artifact ratifying the topology change and the round-2 test
specimen.

## Decision

### D1: Cowork becomes the Tier-1 dispatch and ADR author

> **Amended by ADR-013 (2026-05-23, Accepted).** ADR-013 D1 relocates the
> harness *execution-automation* axis (hooks, subagents, MCP transport,
> defer/headless resume) to Code + subagents (Tier 2). Cowork's
> governance-authoring role here is **retained as advisory** (ADR-013 OQ-1
> resolved — not deprecated) and continues under this D1 process during
> the phased transition until the Plan-subagent topology lands
> (PLAN-0008+, Phase 3). ADR-013 takes precedence per CLAUDE.md §1
> (most-recent accepted ADR wins).

Cowork replaces Chat as the Tier-1 author of **dispatches** (kickoff,
consultation, execute dispatches to Code) and **governance drafts**
(ADR drafts, PLAN drafts) for strategy/architecture work. The scope of
the role transfer is the artifact-authoring responsibility CLAUDE.md §6
currently assigns to Tier 1 Chat: producing the paste-ready Markdown
contracts that Code executes.

Rationale: the capability-mismatch hypothesis (trial protocol §1) is
**supported by two independent trials of two different capability
classes**. Round 1 (concrete dispatch authoring) produced C1 = 0 / C4 = 0
versus the Chat best case of 0 and worst case of 5 (parent §1). Round 2
(this abstract-synthesis ADR) is the second specimen. Cowork's direct
repo read removes the Project-Knowledge-staleness class of error
(incident #3 C-2/C-3) by construction, and lets it perform the cross-file
structural comparisons Chat cannot (round-1 R-K1 catch).

This decision transfers **authorship only**. It does not transfer
commit authority (see D2), and it does not retire Cowork's Tier-0
research responsibility, which continues unchanged (trial protocol §9).

### D2: Permission boundary — commit authority stays Code-exclusive

> **Reinforced by ADR-013 D2 (2026-05-23, Accepted).** The "only Code
> commits" boundary is preserved unchanged and **enforced deterministically**
> by a `PreToolUse deny` hook (bypass-immune even to `bypassPermissions`)
> shipped in PLAN-0007 Step 4. The boundary is no longer prose-only.

The trial-scoped permission boundary (trial protocol §3) is ratified as
the standing boundary for Cowork-as-Tier-1:

| Capability | Cowork (Tier 0 + Tier 1) | Code (Tier 2) |
|---|---|---|
| Read entire repo incl. `docs/strategy/private/`, `docs/research/private/` | yes | yes |
| Write own handoff drafts to outputs scratchpad (K-2 workaround) | yes | n/a |
| Write `docs/adr/NNNN-*.md`, `docs/plans/NNNN-*.md` drafts (uncommitted) | yes | yes |
| `git add` / `commit` / `push` / branch / worktree ops | **no** | yes |
| Edit tracked non-draft files (CLAUDE.md, conventions, code, tests) | **no** | yes |

"Only Code commits" is retained as the last-line fail-safe (trial
protocol §3 rationale): the trial changed one variable (who authors),
not two (who authors + who commits). Permission expansion to commit /
worktree / branch ops is **explicitly a separate future trial (Phase 2
of rollout)**, not granted by this ADR (trial protocol §7.1.4).

### D3: K-1 / K-2 operating workflow contract

Until K-1 and K-2 are fixed upstream, each Cowork-authored Tier-1 round
follows this contract (trial protocol §16.3), which substitutes Code's
post-receive verification for Cowork's blocked self-validation:

1. Cray dispatches the task to Cowork (autonomous task prompt).
2. Cowork reads the repo via proxied Read/Glob/Grep, authors the
   artifact, and writes it to its **outputs scratchpad** (Write to
   `.claude/` is blocked by K-2). Where a draft target is a tracked path
   it can write (`docs/adr/`, `docs/plans/`), it writes there directly.
3. Cowork performs **manual in-source mental validation** against
   `tools/handoffs/_schema.py` (bash dog-food blocked by K-1) and
   **explicitly flags the validator-gap** in its completion report.
4. Cowork reports the artifact path(s) to Cray (filename forward, not
   file content).
5. Cray forwards the path to Code (one chat message).
6. Code copies any scratchpad artifact to its canonical path, runs the
   `validate_handoff.py` in-process `main()` dog-food (Lesson #7 §3.2),
   and applies the R2 required-veto checks (parent §3.3: validator pass;
   lesson numbers resolve; file paths resolve at HEAD; deps present;
   enum values valid). If all pass, Code executes/commits; if any fail,
   Code surfaces a midflight (Lesson #6 firing).

This workflow is the **steady-state operating contract**, not a
temporary scaffold — it stands until Anthropic ships a fix or an
engineering path (Alternative B/C) is pursued.

### D4: C2 / C3 criterion refinement codified as durable

The trial protocol §5 amendments (made under Path D) are ratified as the
durable interpretation of the two cost criteria for any future
Cowork-as-Tier-1 evaluation:

- **C2 (Cray-attention copy/paste).** A Code-automated `cp` from the
  Cowork outputs scratchpad to a canonical path — where Cray forwards
  only a filename — does **not** count as Cray cognitive load. C2 counts
  only rounds where Cray must manually copy artifact *content* between UI
  surfaces. (Original C2 conflated "Cowork writes directly" with "Cray
  attention spent"; the refinement separates them.)
- **C3 (new failure modes).** Documented Anthropic-side Cowork-mode tool
  gaps (K-1, K-2, and any successor architectural constraint Anthropic
  owns) are recorded as **known constraints**, not new failure modes.
  C3 counts only new *Cowork-discipline* failure classes — e.g. silent
  scope extension, fabricated citations, conflating Tier-0 research style
  with Tier-1 dispatch style, ignoring non-quoting discipline.

### D5: Chat-tab disposition — RATIFIED option (b)

> **Amended by ADR-012 (2026-05-22):** D5 is extended — Chat is
> **retained** as a free-form venue (option (b) stands), and Cowork
> gains a **second** free-form role (Tier-1b, repo-grounded) alongside
> it. The two are complementary venues; route by ADR-012 D2. ADR-012
> amends D5 only — ADR-009 D1–D4 and D6 are unchanged. Per CLAUDE.md §1,
> the more-recent accepted ADR (ADR-012) governs on conflict.

**Ratified 2026-05-21 by Cray:** option **(b)** — Chat retained for
free-form exploration / strategy discussion only, with **no
dispatch- or governance-artifact-authoring role**.

Considered options:

- **(a)** Deprecate Chat fully — Cowork takes all Tier-1 work.
  *Rejected:* discards Chat's interactive cadence entirely; that
  cadence was never the thing shown to fail.
- **(b)** Retain Chat for free-form exploration / strategy discussion
  only, with **no dispatch- or governance-artifact-authoring role**.
  *Chosen.*
- **(c)** Migrate gradually — reframe Chat as a "research / exploration
  assistant" with no governance role. *Rejected:* overlaps Cowork's
  retained Tier-0 research role and risks role confusion.

Reasoning for (b): the two trials demonstrated that Chat underperforms
specifically at *dispatch authoring that cites repo contracts* (parent
§2.2) — not at open-ended synthesis or thinking-partner work, which the
trials did not test. (b) removes Chat from the governance /
artifact-ownership path (where Cowork now provably does better) while
preserving its no-stakes value as an interactive strategy sounding
board. T4 (Required follow-on commits) amends
`docs/conventions/chat_tab_instructions.md` to reflect this scope
narrowing.

### D6: Reversibility and regression triggers

This ADR is reversible by a future superseding ADR (see Consequences →
Reversibility). The following observations are pre-declared regression
triggers that should re-open the topology question: a Cowork-authored
dispatch produces ≥2 Code-side pre-execution surfaces (C1 regression); a
new Cowork-*discipline* failure class appears (C3 regression); or the
single-workspace merge of Tier-0 + Tier-1 (trial protocol §13 Q-Trial-1)
measurably degrades research-vs-governance discipline.

## Consequences

### Positive

- **Removes the Project-Knowledge-staleness error class** (incident #3
  C-2/C-3) by construction: Cowork reads repo HEAD directly and shares
  CLAUDE.md, so the tier authoring dispatches operates from the same
  ground truth as the tier executing them.
- **Enables cross-file structural catches** Chat cannot make in-thread —
  validated by round 1's ADR-008-vs-plan grammar-divergence catch
  (pre-exec status §3.1), caught pre-execution rather than as a Lesson #6
  cycle.
- **Preserves the audit trail and the commit fail-safe** (D2): every
  scope decision still lands in an authored dispatch; only Code commits.
- **Single source of truth strengthened** (CLAUDE.md §4): one fewer
  drifting Project-Instructions surface to keep synced.

### Negative

- **K-1 removes Cowork self-validation** and **K-2 forces a scratchpad
  hop** (Context K-1/K-2). Mitigated by the D3 workflow (Code
  post-receive validation substitutes), but it is a real dependency on
  Code's verification step and a standing 1-`cp`-per-dispatch cost.
- **Risk of normalizing the workaround.** Accepting Path D could let a
  fixable-later constraint ossify; D6 + the follow-on TODO to revisit
  Alternative B keep the door open.
- **Capability tested narrowly.** Only two capability classes (concrete
  dispatch authoring, abstract ADR synthesis) are evidenced. Generalizing
  to *all* Tier-1 work is unproven (see Risks).

### Neutral

- **Lesson #6 retained as the durable layer** (parent §2.3 F-3); this ADR
  amends the operational/topology layer, not Lesson #6 itself. Fewer
  firings are expected, not zero (parent §4 enumerates the legitimate
  residual firings: mid-execution discoveries, Cray-decision forks,
  genuine ambiguity).
- **Tier 0 research role unchanged** (trial protocol §9): Cowork keeps
  `docs/research/private/` authorship; the merged single workspace
  (Q-Trial-1) now carries both Tier-0 and Tier-1 responsibilities.
- **ADR-number earmark collision.** ADR-007 References informally
  earmarked "ADR-009+" for the LLM reasoning-hook surface and "ADR-010+"
  for the action-approval/audit framework. This ADR consumes 0009 for
  tier topology; those future ADRs shift to 0010+ / 0011+ accordingly.
  Surfaced for Cray (no action required in this ADR).

### Required follow-on commits (TODOs for Code — separate commits)

This ADR is a draft; Code commits it and the following amendments. None
of these edits are made in this draft — they are listed for Code because
Cowork has no write access to CLAUDE.md or `docs/conventions/`:

1. **T1 — Commit this ADR** to `docs/adr/0009-cowork-tier1-tier-topology.md`
   with status Accepted.
2. **T2 — Amend CLAUDE.md §6 4-tier table:** Tier 1 row updates from
   "Chat" to "Cowork (dispatch + ADR/PLAN authoring)"; Chat's row updated
   per Cray's D5 ruling. Also reflect that Tier 0 + Tier 1 are merged in
   one Cowork workspace.
3. **T3 — Amend `docs/conventions/cowork_tab_instructions.md`:** expand
   write scope from Tier-0-only (research outputs + `cowork-` handoffs)
   to include Tier-1 dispatch + `docs/adr/` / `docs/plans/` draft
   authoring; document the D3 K-1/K-2 workflow; retain the non-quoting
   discipline for `docs/strategy/private/**`.
4. **T4 — Resolve `docs/conventions/chat_tab_instructions.md` disposition**
   per Cray's D5 choice (deprecate / repurpose to no-governance / narrow).
5. **T5 — Update `docs/STATUS.md`** Recent Decisions with the topology
   change and the round-2 trial outcome.
6. **T6 (ratified 2026-05-21)** — promote the K-1/K-2 workflow and the
   C2/C3 refinement to **Lesson #8** (`docs/lessons/0008-cowork-tier1-k1-k2-workflow.md`).
   Cray ratified inclusion (Q4) on the rationale that vero-lite may
   become a template for future Claude-Desktop-on-WSL projects; the
   Lesson preserves the operational layer beyond this project's
   session-scoped handoffs.
7. **T7 — Leave a pointer note in ADR-007 References** (`docs/adr/0007-oct-engine-contracts.md`)
   recording that ADR-009 consumed the "0009+" slot earmarked for the
   LLM reasoning-hook surface; downstream earmarks shift to ADR-010+
   (LLM reasoning) and ADR-011+ (action-approval/audit). Ratified by
   Cray (Q2 option α).

Per CLAUDE.md §1 precedence, an accepted ADR outranks CLAUDE.md and tier
instructions; T2–T4 bring the lower-precedence files into alignment.
Per Lesson #5 §1, CLAUDE.md edits are constitutional and need the
session-restart-bridge sequence.

### Risks

- **K-1 / K-2 may be permanent Anthropic-side gaps** (blocker
  investigation §0: no ETA). If so, the D3 workflow is the permanent
  operating mode, not a stopgap. Alternative B (move handoffs out of
  `.claude/`) remains a viable future fix for K-2 only (it does not fix
  K-1).
- **Cowork may fail at untested Tier-1 work.** The two trials covered
  dispatch authoring and ADR synthesis. Other Tier-1 activities —
  multi-turn interactive strategy refinement, live design negotiation,
  rapid-iteration brainstorming — were not tested and may favor Chat's
  interactive cadence. Recommend trial-by-trial scope expansion rather
  than blanket generalization, to avoid scope creep past the evidence.
- **Merged-workspace discipline blur.** Holding Tier-0 research and
  Tier-1 governance in one Cowork workspace (Q-Trial-1) risks bleeding
  research-style output into governance artifacts or vice versa; D6 makes
  this a regression trigger.

### Reversibility

This ADR can be retracted or superseded by a future ADR if observed
Cowork-as-Tier-1 performance regresses against the D6 triggers. Because
D2 keeps commit authority with Code and Tier-0 research unchanged,
reverting to Chat-as-Tier-1 (the status-quo alternative) costs only the
T2–T4 amendment reversals plus adopting the parent-discussion R1+R3+R4
operational fixes — no architectural unwind.

## Alternatives Considered

### Alternative A: Move repo to a Windows-native path (`C:\...`)

- **Pros:** Likely fixes K-1 (Cowork bash receives a non-UNC `cwd`),
  restoring Cowork self-validation.
- **Cons:** Does not fix K-2; 10–100× slower `.git/` ops over NTFS;
  requires rewriting every WSL-native path reference (CLAUDE.md §5,
  Lesson #2, conventions) and risks new NTFS/case-sensitivity traps
  (blocker investigation §2 Path A).
- **Why rejected:** High cost, partial fix; the WSL-native checkout is
  Code's known-good config and the moat work depends on it.

### Alternative B: Move the handoff convention out of `.claude/`

- **Pros:** Fully fixes K-2 (Cowork could write handoffs directly); the
  validator is filename-only so likely needs no change (blocker
  investigation §2 Path B).
- **Cons:** Does not fix K-1 (bash still blocked, no self-validation);
  ~30 path references to sweep + an ADR; the cheap variant
  (`.claude/agents/handoffs/`) was tested and **failed** (blocker
  investigation §3).
- **Why rejected for now:** Medium cost, partial fix; standalone it does
  not unblock self-validation. Retained as a viable future follow-up if
  long-term Cowork-as-Tier-1 justifies eliminating the scratchpad hop.

### Alternative C: Move both (repo to `C:\` + handoffs out of `.claude/`)

- **Pros:** Fixes K-1 and K-2 together.
- **Cons:** Sum of A + B cost (3–4 h engineering + unknown NTFS/WSL
  traps); only sensible after validating A alone first (blocker
  investigation §2 Path C).
- **Why rejected:** Highest cost; not justified by current evidence when
  Path D already unblocks at the process layer.

### Alternative D: Accept the gaps + refine criteria (RATIFIED)

- **Pros:** Lowest cost (process-layer fix only); preserves the
  content-quality benefit; reversible; the D3 workflow is documented and
  reproducible and was demonstrated to work in round 1 (engine closeout
  §7).
- **Cons:** Retains the 1-`cp`-per-dispatch cost and the loss of Cowork
  self-validation; risks normalizing a fixable-later constraint.
- **Why chosen:** It is the only path that unblocks Cowork-as-Tier-1
  without engineering work, keeps the commit fail-safe intact, and does
  not foreclose A/B/C later. Cray ratified Path D (blocker investigation
  §5 Q1).

### Status quo: Chat remains Tier-1 with R1+R3+R4 operational fixes

- **Pros:** No topology change; the parent-discussion operational fixes
  (R1 generalize pre-verification scope; R3 schema self-check on send;
  R4 fact-pack-first default) catch most of what Cowork catches (parent
  §5 cost-benefit), at ~0 token cost.
- **Cons:** Does not remove the structural Project-Knowledge-staleness
  class; keeps the latency between Chat asserting and Code verifying
  (parent §2.2); walks past the round-1 evidence that Cowork's direct
  repo read produces materially higher dispatch quality.
- **Why rejected:** Two trials of two capability classes support the
  capability-mismatch hypothesis; the operational fixes mitigate but do
  not eliminate the structural cause. R2 (Code required-veto criteria)
  is adopted regardless of topology — it is tier-orthogonal (parent
  §7.2.4) and is the substitute-verification backbone of the D3 workflow.

## References

- **Trial protocol (the contract):**
  `.claude/handoffs/session-10/2026-05-20-1345-code-cowork-tier1-trial-protocol.md`
  (§3 permission boundary, §5 amended C1–C4 criteria, §7.1/§7.3 decision
  tree, §13 Cray ratifications, §16 K-1/K-2 documented constraints +
  workflow)
- **Parent discussion (the hypothesis + R1–R4):**
  `.claude/handoffs/session-10/2026-05-20-1235-code-tier-collaboration-asymmetry-discussion.md`
  (§0 F-1/F-2/F-3, §1 three-incident baseline, §2.2 capability partition,
  §3.3 R2 required-veto criteria, §4 residual Lesson #6 firings, §5
  cost-benefit)
- **Blocker investigation (4 paths weighed; Path D ratified):**
  `.claude/handoffs/session-10/2026-05-20-1545-code-cowork-blocker-investigation.md`
  (§0 both gaps Anthropic-side, §2 Paths A–D, §3 `.claude/agents/handoffs/`
  test failed, §5 Cray decision)
- **Round 1 pre-execution status (R2 PASS, C1 = 0):**
  `.claude/handoffs/session-10/2026-05-20-1510-code-cowork-tier1-trial-preexec-status.md`
  (§2 R2 checks, §3.1 R-K1 cross-file catch)
- **Round 1 closeout (trial scorecard, content-quality evidence):**
  `.claude/handoffs/session-10/2026-05-20-1840-code-plan003-phase1-engine-closeout.md`
  (§7 trial addendum: C1 = 0, C2 = 0, C3 = 2 sandbox, C4 = 0)
- **Round 1 dispatch (proof of concrete-authoring capability):**
  `.claude/handoffs/session-10/2026-05-20-1530-cowork-plan003-phase1-kickoff-dispatch.md`
  (§0 R-K1–R-K5 pre-emptions, §11 Cowork R3 self-check under K-1)
- **ADR-006** (`docs/adr/0006-vertical-plugin-architecture.md`) — 4-tier
  context and Rule of Three precedent
- **ADR-007** (`docs/adr/0007-oct-engine-contracts.md`) — References
  earmark for ADR-009+/010+ (numbering note, Consequences → Neutral)
- **ADR-008** (`docs/adr/0008-yaml-ontology-specification.md`) — D2 grammar
  (the round-1 R-K1 catch anchor)
- **Lesson #5** (`docs/lessons/0005-tier-system-audit-2026-05-15.md`) —
  §1 constitutional-edit restart sequence; §2 Cray-direct codification
  path; §3 schema-fidelity discipline
- **Lesson #6** (`docs/lessons/0006-code-surface-chat-redispatch-pattern.md`)
  — the durable surface→re-dispatch layer this ADR's operational layer
  amends (not the lesson itself)
- **CLAUDE.md** §1 (precedence), §6 (4-tier table — amended by T2), §11
  (Tier 2 operational policy)
- **Handoff schema:** `tools/handoffs/_schema.py` (REQUIRED_FIELDS,
  Phase/Actor/Status enums — the mental-validation anchor under K-1);
  `tools/handoffs/validate_handoff.py`

## Implementation Notes

This ADR was drafted by Cowork as the round-2 trial dispatch (trial
protocol §7.1.1, Q-Trial-4 §13). Cowork has no commit authority (D2);
Code reviews and commits this file plus the T1–T6 follow-on amendments.
Per K-1, Cowork could not run `validate_handoff.py`; the companion
completion handoff records the mental-validation substitute and flags
the gap. AI-assisted per project convention.
