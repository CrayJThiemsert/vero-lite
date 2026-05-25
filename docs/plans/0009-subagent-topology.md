# PLAN-0009: Subagent Topology — Harness Autonomy Phase 3

**Status:** Ready for execution
**Owner:** Claude Code (Tier 2 — subagent primitives are Code-exclusive per ADR-013 D1)
**Created:** 2026-05-25
**Related ADRs:** ADR-013 (autonomy axis relocation — **gates this plan**; Phase 3 executes the ADR-013 D1 phased end-state: relocate the execution-automation axis into Code + subagents), ADR-009 (D2 "only Code commits" preserved + extended to subagents; D1 interim authoring + D3 K-1/K-2 workflow context), ADR-012 (D4.3 author≠reviewer disclosure — load-bearing for the Plan subagent), ADR-006 (core vs vertical infrastructure — subagent topology = core harness tooling)
**Related PLANs:** PLAN-0007 (Phase 1, MERGED `b2ea9b8` 2026-05-23 — deterministic hooks G5/H1/C4 + Notification bridge), PLAN-0008 (Phase 2, FULLY CLOSED in `docs/plans/done/` — Stop continuation loop + Sonnet classifier + L1–L4 loop-detect; this plan resolves four PLAN-0008 carry-overs, see §Carry-overs)

> **Ratification status.** Cray adjudicated all four open questions
> (OQ-1…OQ-4) on 2026-05-25, agreeing with each recommendation: `WebFetch`
> for the Explore subagent; no new ADR (execute ADR-013 D1); subagent
> identity folds into Step 1 with ADR-013 OQ-3; PLAN status vocabulary
> (not ADR). This satisfies the §Sequencing-gate ratification condition;
> **Status flipped Draft → Ready for execution by Code in this commit**
> (Cowork drafted, Code applied the ratification edit + committed per
> ADR-009 D2).

> **Sequencing gate.** Code executes this plan only after:
>
> 1. PLAN-0008 Phase 2 is fully closed on `main` (✓ — archived to
>    `docs/plans/done/0008-harness-autonomy-layer-phase-2.md`; all four
>    ACs VERIFIED, AC-1 corroborated by 2 independent live runs per
>    `docs/STATUS.md`).
> 2. ADR-013 is Accepted (✓ — `docs/adr/0013-autonomy-axis-relocation.md`,
>    D1 phased relocation is the architectural authority for this plan).
> 3. This PLAN's `Status` flips Draft → Ready for execution after Cray
>    ratifies the §Resolved-decisions section (✓ — Cray adjudicated
>    OQ-1…OQ-4 on 2026-05-25; Code flipped at commit time).

## Goal

Stand up the **subagent topology** that completes the ADR-013 D1 phased
relocation of the execution-automation axis into Code (Tier 2). Phase 3
introduces two co-located subagents inside the Code harness — a
**read-only Explore subagent** (research + codebase archaeology) and a
**Plan subagent** (ADR/PLAN drafting) — plus the **main-agent dispatch
protocol** that spawns them, enforces their tool/cwd boundaries, and
reduces their results back into the main agent's context. The main agent
retains edits and commits; the deterministic `pretooluse_git_deny.py`
(G5) fail-safe is preserved and **extended to bind subagents** so that
neither subagent can commit (ADR-009 D2 / ADR-013 D2). Phase 3 also
resolves the in-harness arm of the auto-handoff bottleneck (PLAN-0008
OQ-D): the Plan subagent is the natural author for an auto-drafted
governance artifact, removing the Cray paste for the *co-located* case
while leaving the cross-tab Cowork/Chat relay unchanged (K-1/K-2 still
blocks the desktop sandboxes — see §Boundary notes).

End-state per ADR-013 OQ-1 (Cray-resolved 2026-05-23): even after the
Plan subagent lands, **Cowork is retained as the advisory drafter of
governance artifacts** so an author≠reviewer separation is preserved that
a single-harness subagent cannot self-supply. Phase 3 therefore builds
the in-harness drafting *capability* without retiring the external
advisory drafter.

## Acceptance Criteria

> Six criteria. AC-1…AC-5 cover the new Phase 3 surface; AC-6 guards
> against Phase 1 + Phase 2 regression (mirrors the PLAN-0008 AC-4
> pattern).

- [ ] **AC-1 — Subagent contract is defined and enforced.** A
  machine-checkable contract exists for each subagent type specifying:
  input schema (task prompt + scoped context), output schema (reduced
  result the main agent ingests), tool allowlist, and cwd boundary. The
  main agent can spawn a subagent, pass scoped context, and receive a
  reduced result without leaking the subagent's full transcript into the
  main context. Verified by a contract-validation test + one end-to-end
  spawn→reduce round-trip per subagent type.

- [ ] **AC-2 — Explore subagent is provably read-only.** The Explore
  subagent's tool allowlist is `Read`, `Grep`, `Glob`, and `WebFetch`
  (external prior-art research, Cray-approved 2026-05-25 / OQ-2 —
  `WebFetch` only, no `Bash`-based fetching); it has **no** `Write`,
  `Edit`, or `Bash`. A negative test confirms a Write/Edit/Bash attempt
  from inside the Explore subagent is denied at the allowlist layer (not
  merely by prompt instruction). It returns reduced research findings the
  main agent or Plan subagent can consume.

- [ ] **AC-3 — Plan subagent drafts only under `docs/{adr,plans}/` and
  cannot commit.** The Plan subagent may `Write`/`Edit` only files
  matching `docs/adr/NNNN-*.md` or `docs/plans/NNNN-*.md`; a negative
  test confirms an edit outside those paths is denied, and that a `git
  commit`/`push`/`merge` attempt is hard-blocked by the extended
  `pretooluse_git_deny.py` (AC-6 cross-check). Its output is a PR-ready
  draft the main agent commits.

- [ ] **AC-4 — Main-agent dispatch protocol routes correctly.** A
  documented + tested decision procedure governs spawn-vs-inline (when to
  delegate to a subagent vs. handle inline), transcript/context
  propagation into the subagent, result reduction back to the main agent,
  and cwd + tool-boundary enforcement at spawn time. ≥ 4 routing cases
  green (2 spawn, 2 inline) plus boundary-enforcement assertions.

- [ ] **AC-5 — In-harness auto-handoff (OQ-D arm) works without a Cray
  paste.** For the *co-located* case, the main Code agent can dispatch a
  governance-drafting task to the Plan subagent and receive a PR-ready
  draft back without a human relay step. The cross-tab Cowork/Chat relay
  is explicitly **out of this AC** (K-1/K-2 unchanged — see §Boundary
  notes). Verified by an end-to-end "classifier pauses on a
  governance-relevant Stop → main agent spawns Plan subagent → draft
  produced → main agent commits" flow.

- [ ] **AC-6 — Phase 1 + Phase 2 guarantees regression-free.** Re-run all
  prior acceptance checks after Phase 3 lands:
  - Phase 1 — G5 `pretooluse_git_deny.py` 16-case bypass-immune matrix
    (now including subagent-identity cases per Step 1/OQ-1); H1
    `posttooluse_validate_handoff.py`; C4 `pretooluse_research_path_deny.py`.
  - Phase 2 — `Stop` continuation loop, Sonnet classifier conservatism
    (G1/G2/C2 pause + routine proceed), L1–L4 loop-detect + reset.

  **All must remain green.** A Phase 3 change that disturbs a Phase 1/2
  guarantee is a hard fail regardless of new-feature progress.

## Out of Scope

> Deferred beyond Phase 3. Listed so the boundary is explicit.

- ❌ **Phase 4 — MCP `vero-bridge` cross-surface transport.** The
  machine-to-machine bus that would let surfaces signal each other
  directly. Build only after subagents prove out. Carry to PLAN-0010.

- ❌ **Phase 4 — plugin bundle.** Packaging the autonomy layer as an
  installable plugin/marketplace bundle. Carry to PLAN-0010.

- ❌ **Cross-tab auto-handoff Code → Cowork/Chat without a Cray paste.**
  Structurally blocked by K-1/K-2 (the desktop sandboxes cannot read
  `.claude/handoffs/`); only the *in-harness* subagent arm (AC-5) reduces
  the relay. The cross-tab arm is not solved by Phase 3 and is not a
  Phase 3 deliverable (it depends on Phase 4 transport or an upstream
  Anthropic fix).

- ❌ **Cross-session loop-counter persistence.** `.claude/state/` remains
  per-session (PLAN-0008 Out-of-Scope, unchanged). Phase 3 may *touch*
  the state schema for subagent contracts (Step 1) but does not add
  cross-session retention.

- ❌ **Replacing Phase 1 deterministic hooks with subagent/classifier
  judgment.** G5 git-deny + H1 handoff-validator + C4 research-path-deny
  stay deterministic per ADR-013 D2 ("the most safety-critical rules must
  be deterministic"). Phase 3 *extends* G5 to bind subagents; it does not
  substitute classifier judgment for any deterministic floor.

- ❌ **Retiring Cowork as governance drafter.** ADR-013 OQ-1 keeps Cowork
  as the advisory drafter for author≠reviewer separation. Phase 3 builds
  the Plan-subagent capability but does **not** remove the external
  drafter; the follow-on instruction-file annotation (ADR-013 T4) is
  deferred to the Phase-3 boundary, not executed by this plan.

## Steps

### Step 1a — Subagent primitive survey (research spike)

> **Sub-step split rationale (Code, 2026-05-25 post-cross-check).** Before
> locking the contract design, verify the Anthropic Claude Code subagent
> primitive surface area. The plan-as-written assumes the primitive
> exposes everything required (tool-allowlist enforcement at harness
> layer, cwd boundary, identity signal, write-path allowlist, result
> reduction). Today's research-note cross-check (see STATUS Current Focus
> 2026-05-25 PLAN-0009 ratification entry) found that 3 of 4 vendor docs
> had at least one Cowork-research diff vs current docs — including
> undocumented APIs and stale cap numbers. Verifying live before design
> is the cheapest insurance and matches the PLAN-0008 fact-pack-first
> discipline.

Time-box: 1–2 hours. If the primitive surface is materially different
from the plan's assumption, raise via Cray ratification before Step 1b
proceeds.

- **Verification matrix:**
  - **Tool-allowlist enforcement layer:** harness-native deny (load-bearing for AC-2/AC-3 negative tests) vs prompt-only model discipline (insufficient).
  - **cwd boundary:** does the primitive accept a per-subagent working-directory restriction at spawn?
  - **Identity signal:** how does a hook (G5 git-deny) distinguish a subagent invocation from a main-agent invocation? Candidates: `CLAUDE_TIER` env-var inheritance / non-inheritance, settings-scope marker, subagent metadata in `tool_input`, harness-provided subagent name in the hook environment.
  - **Result reduction model:** what is returned to the main agent vs what stays in the subagent transcript? Is the reduction bounded (e.g., explicit max tokens) or free-form?
  - **Write-path allowlist for Plan subagent:** does the primitive accept per-subagent write-path restrictions, or does a `PreToolUse` hook need to enforce (extending the C4 pattern)?
- **Output:** `docs/research/private/YYYY-MM-DD-subagent-primitive-survey.md` (Tier-0 research note, gitignored per CLAUDE.md §10 + `.gitignore` line for `docs/research/private/`). Feeds Step 1b design choices.
- **Sequencing:** Step 1a can run in parallel with the Phase 3.5 smoke test observation period (1–2 day window) — both unblock Step 1b independently.

### Step 1b — Subagent contract design (+ state-schema touch)

Design the contract before any subagent lands, **based on Step 1a survey
findings**. Output is a spec doc section + a schema the dispatch protocol
validates against.

- **Per-type contract fields:** `name`, `tool_allowlist` (explicit, not
  wildcard), `cwd_boundary` (project-relative root the subagent may
  operate under), `write_path_allowlist` (Plan subagent only — the
  `docs/{adr,plans}/NNNN-*.md` patterns), `input_schema` (task prompt +
  scoped context payload), `output_schema` (the reduced result; what the
  main agent ingests vs. what stays in the subagent transcript).
- **Result-reduction contract:** define what the subagent returns to the
  main agent (a bounded summary + artifact path(s)), so the subagent's
  full read/transcript does not bloat the main context — the same
  context-economy rationale CLAUDE.md §6 Token Economy states.
- **State-schema touch (resolves PLAN-0008 carry-over).** If subagent
  bookkeeping needs `.claude/state/`, fold in two PLAN-0008 carry-overs
  while the schema is open:
  - **L3 automatic reset** — "error signature absent from next N tool
    outputs" multi-tool observation (deferred by PLAN-0008 §Step 4
    closeout; needs state evolution). Add the counter/observation field
    if and only if the schema is being touched anyway.
  - **Worktree path normalization** — `_loop_counter._normalize_file_path()`
    leaves worktree-prefixed keys (e.g.
    `.claude/worktrees/<id>/docs/CHANGELOG.md` instead of
    `docs/CHANGELOG.md`; STATUS 2026-05-25 finding). Collapse the
    worktree suffix so keys are stable across worktrees. Refinement only
    — per-session isolation already works.
- **Boundary-enforcement mechanism (OQ-1 RESOLVED — Cray 2026-05-25:
  fold here with ADR-013 OQ-3).** Specify *how* the tool allowlist +
  write-path allowlist + the subagent's exclusion from commit authority
  are enforced (harness-native subagent config vs. a `PreToolUse` deny
  extension). Resolve **together with ADR-013 OQ-3** (the `session != Code`
  signal for the git-deny hook) — the subagent case is the same class of
  problem: the hook must distinguish *main Code agent* (may commit) from
  *Plan/Explore subagent* (must not). One mechanism serves both.

### Step 2 — Explore subagent (read-only)

`.claude/agents/explore.*` (final path/format per Step 1 contract).

- **Tool allowlist:** `Read`, `Grep`, `Glob`, `WebFetch` (external
  prior-art research, Cray-approved 2026-05-25 / OQ-2 — `WebFetch` only,
  no `Bash`-based fetching). **No `Write`/`Edit`/`Bash`** — enforced at
  the allowlist layer, not by prompt alone (AC-2 negative test).
- **Use cases:** research before Plan-subagent drafting (the natural
  upstream of an ADR/PLAN draft); codebase archaeology ("where is X
  defined / what references Y"); fact-pack gathering for a dispatch.
- **Output:** a reduced findings payload (summary + file/line citations +
  any external URLs) the main agent or Plan subagent consumes. Mirrors
  the fact-pack-first discipline that ADR-009 made Cowork's Tier-1 norm,
  now available in-harness.

### Step 3 — Plan subagent (ADR/PLAN drafting)

`.claude/agents/plan.*` (final path/format per Step 1 contract).

- **Write scope:** `Write`/`Edit` restricted to `docs/adr/NNNN-*.md` and
  `docs/plans/NNNN-*.md` only (AC-3 negative test: edit outside is
  denied). No commits, no edits to code/tests/config — same boundary
  ADR-009 D2 set for Cowork, now applied to the in-harness drafter.
- **Output:** a PR-ready uncommitted draft. The **main agent commits**
  (Plan subagent cannot — G5 binds it per Step 1/OQ-1).
- **Author≠reviewer (ADR-012 D4.3 + ADR-013 OQ-1).** The Plan subagent
  shares the main harness's framing/context, so a Plan-subagent draft has
  **no** independent-deliberation check from within Code. Phase 3 must
  preserve the external advisory drafter (Cowork) for governance per
  ADR-013 OQ-1, and the Plan subagent's drafts must carry the same
  author≠reviewer disclosure ADR-012 D4.3 mandates. Specify the
  disclosure-stamp requirement in the Plan subagent's output contract.

### Step 4 — Main-agent dispatch protocol

The protocol the main Code agent uses to spawn and manage subagents.

- **Spawn-vs-inline decision:** when delegation is worth the spawn cost
  (large read-only research sweep; an isolated drafting task) vs. when
  the main agent handles it inline (small lookups, edits the main agent
  must own). Document as a short decision procedure (AC-4 routing cases).
- **Context propagation:** what scoped context the main agent passes into
  a subagent (the subagent starts fresh — the prompt must be
  self-contained), and how much transcript (if any) is forwarded.
- **Result reduction:** how the subagent's output is reduced back into
  the main agent (bounded summary + artifact paths, per Step 1 contract)
  to protect main-context headroom.
- **Boundary enforcement at spawn:** cwd boundary + tool allowlist are
  applied when the subagent is spawned, not left to runtime prompt
  discipline.

### Step 5 — Auto-handoff Code → Plan subagent (resolves PLAN-0008 OQ-D, in-harness arm)

Wire the Phase-2 `Stop`/classifier `pause` arm to spawn the Plan subagent
for governance-drafting tasks.

- **Trigger:** when the Phase-2 Sonnet classifier (PLAN-0008 Step 5)
  classifies a `Stop`/`PreToolUse` event as a governance-drafting need
  (e.g., a decision reached that warrants an ADR/PLAN draft), the main
  agent dispatches to the Plan subagent rather than pausing for a Cray
  paste — for the co-located case only.
- **Why this resolves OQ-D's load-bearing reasons (PLAN-0008 Notes):**
  - PLAN-0008 OQ-D reason 1 (K-1/K-2 still blocks the cross-tab relay)
    is **acknowledged, not solved** — Phase 3 only removes the relay for
    the in-harness subagent destination, which is exactly the case OQ-D
    said "is reduced only when the destination is a subagent in the same
    Code harness — that is PLAN-0009 scope by construction."
  - PLAN-0008 OQ-D reason 2 (author = Plan subagent is the right role):
    realized here — the main agent dispatches, the Plan subagent drafts.
  - PLAN-0008 OQ-D reason 3 (surface bloat — needs a template +
    context-window policy + trigger→handoff-type mapping + an H1
    validator round-trip): specified by Step 1's output contract + Step
    5's trigger→artifact-type mapping; H1 validation still runs
    deterministically on any `.claude/handoffs/` write.
- **`PreToolUse` classifier dispatch (resolves a second PLAN-0008
  carry-over).** PLAN-0008 shipped the `Stop`-side classifier dispatch
  only; the `PreToolUse` arm for non-G5 rows that can be classified
  pre-tool (e.g., **G1** ADR mutation via `Edit`, **G2** number
  consumption via filename creation) was deferred to PLAN-0009
  (`.claude/autonomy-triggers.md` "How the classifier reads this file"
  §). Add the `PreToolUse` classifier dispatch here, preserving all
  current registry rows (G1–G5, C1–C4, H1, L1–L4) unchanged; the
  classifier-dispatch protocol may extend `autonomy-triggers.md` per its
  Change protocol (Cowork drafts the row, Code commits).

### Step 6 — Tests + live AC + closeout

Mirror the PLAN-0008 Step 7 + Step 8 pattern.

> **Verification-rigor directive (Cray, 2026-05-25 — binding for ALL
> autonomy work, including any Phase-3.5 scheduled-task loop).** These
> components run **unattended** — no human is in the loop to catch a fault
> as it happens — so a green test suite is *not sufficient evidence* of
> correctness. Each component must ship an explicit **case-coverage matrix**
> enumerating, per behavior: happy path, boundary/threshold, fail-closed /
> error, adversarial / bypass-attempt, and concurrency / race cases — with
> a test mapped to **every** row and any uncovered case named as residual
> risk. Match the PLAN-0007 G5 precedent (16-case bypass-immune matrix).
> Unit coverage alone does not close an AC; the live-verification matrix is
> mandatory; and sign-off states residual-risk/confidence explicitly. The
> bar is **"we are confident it does what we intend,"** not "tests pass."

- **Unit + integration tests:** contract validation; per-subagent tool
  allowlist negatives (AC-2/AC-3); dispatch routing (AC-4); the OQ-D
  in-harness auto-handoff flow (AC-5); G5 subagent-identity extension
  (AC-6). Maintain Phase 2's density and gate parity (`ruff` + `mypy
  --strict` + `detect-secrets` clean; pre-commit `mypy` glob already
  covers `.claude/hooks/**`).
- **Live verification matrix:** drive each subagent type end-to-end;
  observe the auto-handoff arm produce a draft with no Cray paste;
  re-run the Phase 1 bypass-immunity matrix (now incl. subagent-identity
  commit-deny) + Phase 2 classifier/loop-detect checks (AC-6).
- **Closeout:** `.claude/handoffs/session-NN/YYYY-MM-DD-NNNN-code-plan0009-phase3-closeout.md`
  with the AC matrix, carry-overs surfaced, and the `git mv
  docs/plans/0009-*.md docs/plans/done/` archive step.

## Verification

Maps 1:1 to AC-1…AC-6. Repo-health gate:

- Subagent config is valid + the tool allowlists are enforced at the
  harness layer (negative tests prove non-allowlisted tools are denied,
  not merely discouraged by prompt).
- `pretooluse_git_deny.py` (G5) blocks commits from **both** subagents
  (extended matrix) while still allowing the main Code agent — the
  ADR-009 D2 / ADR-013 D2 boundary survives the new spawn paths.
- Phase 1 (G5/H1/C4) + Phase 2 (`Stop` loop, Sonnet classifier, L1–L4)
  guarantees verified post-merge (AC-6).
- No secret in tracked files (`detect-secrets`); subagent config carries
  no credentials.
- `.claude/state/` (if touched) remains gitignored
  (`git check-ignore` returns a hit).
- A per-component **case-coverage matrix** is attached to the closeout
  (happy / boundary / fail-closed / adversarial / concurrency rows), every
  row has a mapped test, and any uncovered case is named as residual risk
  (Cray verification-rigor directive 2026-05-25). Live verification is
  required in addition to unit coverage; sign-off states confidence
  explicitly.

## Carry-overs resolved from PLAN-0008

| PLAN-0008 deferred item | Resolved in PLAN-0009 |
|---|---|
| **OQ-D** — auto-handoff Code → Cowork/Chat (Cray-deferred 2026-05-24) | Step 5 — in-harness arm only (Plan subagent destination); cross-tab arm remains blocked by K-1/K-2 and stays Out of Scope |
| **L3 automatic reset** — multi-tool "signature absent from next N outputs" | Step 1 — folded *iff* the state schema is touched for subagent contracts |
| **`PreToolUse` classifier dispatch** — non-G5 rows classifiable pre-tool (G1/G2) | Step 5 — added alongside the Stop-side dispatch; registry rows preserved unchanged |
| **Worktree path normalization** in `_loop_counter._normalize_file_path()` | Step 1 — collapse worktree suffix for stable keys (refinement only) |

## Resolved decisions (Cray-adjudicated 2026-05-25)

> Surfaced per cowork rule #8 (options + recommendation, Cray adjudicates)
> and rules #12/#13 (flag conflicts + scope). All four resolved by Cray on
> 2026-05-25 — each agreeing with the recommendation. Recorded inline for
> the audit trail.

- **OQ-1 — Subagent boundary-enforcement + commit-deny mechanism.
  RESOLVED:** fold into Step 1 **together with ADR-013 OQ-3** (the
  `session != Code` signal), since the subagent-identity signal and the
  session-identity signal share one mechanism. The G5
  `pretooluse_git_deny.py` extension that distinguishes *main Code agent*
  (may commit) from *Plan/Explore subagent* (must not) is the load-bearing
  deliverable (AC-3 / AC-6).

- **OQ-2 — Explore subagent gets `WebFetch`. RESOLVED: yes,** bounded to
  `WebFetch` only (no `Bash`-based fetching), so external prior-art
  research — the Explore subagent's natural job, mirroring Cowork's Tier-0
  web-research role — is in scope while the read-only surface stays
  narrow. Baked into AC-2 + Step 2.

- **OQ-3 — New ADR vs. execute ADR-013 D1. RESOLVED: no new ADR** —
  Phase 3 executes the already-Accepted ADR-013 D1 (PLAN-0008 precedent:
  Phase 2 executed ADR-013 D4 with no new ADR). Mint an ADR only if Step 1
  surfaces a genuinely architecture-level choice; the next free ADR is
  `0014` (`0011` stays reserved for the action-approval/audit framework).

- **OQ-4 — Status vocabulary + authoring path. RESOLVED:** use the PLAN
  template vocabulary (`Draft` → `Ready for execution`), not ADR
  vocabulary (`Proposed`/`Accepted`). The draft was written **directly**
  to `docs/plans/0009-subagent-topology.md` (write-direct per cowork
  pattern 4 + ADR-009 D3 step 2 — K-2 does not apply outside `.claude/`);
  Code commits from the main working tree (single-doc draft = worktree-OFF
  per CLAUDE.md §11; `feat/plan0009-subagent-topology` branch optional).

## Non-commit reminder (ADR-009 D2 / ADR-013 D2 — load-bearing)

This is a Cowork draft. **Cowork does not commit** — only Code commits,
and the boundary is enforced deterministically by `pretooluse_git_deny.py`
(bypass-immune even to `bypassPermissions`, ADR-013 D2). Code applies the
file write + commit on the appropriate branch after review; Cowork could
not run `git` even if instructed.

## Implementation Notes

Drafted by Cowork in Tier-1 (governance authoring) mode under the interim
ADR-009 D1 process (the Phase-3 relocation this plan specifies has not yet
executed — the Plan subagent it designs does not exist yet, so Cowork is
still the governance drafter per ADR-013 D1 phasing). Cowork has no commit
authority (ADR-009 D2); Code reviews and commits this file.

**Author≠reviewer disclosure (ADR-012 D4.3).** The substance of this PLAN
was **not** self-deliberated in a Cowork Tier-1b free-form session. It was
authored from a Code-authored dispatch whose outline derives from the
PLAN-0008 closeout §6 (Code-authored) and the ADR-013 D1 end-state
(Cray-ratified). The independent-deliberation separation is therefore
**intact** for this artifact: the drafter (Cowork) is distinct from the
outline's originator (Code/Cray), and Code's review (ADR-009 D3 step 6)
remains the independent check. (Noted explicitly because Phase 3 itself is
the topology under which this separation will be re-examined per ADR-013
OQ-1.)

**Schema / fact-pack self-check (K-1 validator gap flagged).** Per K-1,
Cowork cannot run repo tooling (`mcp__workspace__bash` refuses the WSL-UNC
cwd). This PLAN is not a `.claude/handoffs/` artifact, so the
`validate_handoff.py` frontmatter schema does not apply; the relevant
canonical shape is the PLAN template (`docs/plans/0000-template.md`),
matched field-by-field (Status / Owner / Created / Related ADRs / Goal /
Acceptance Criteria / Out of Scope / Steps / Verification). All repo
citations in this draft were verified against HEAD via Read/Glob this
session:
- `0009` is the next free PLAN number (`docs/plans/` glob: `0004` active +
  `done/{0003,0005,0006,0007,0008}` + templates; no `0009*`).
- ADR-013 D1 subagent triad (Explore read-only / Plan drafter / main
  edits+commits), OQ-1 (Cowork retained as advisory drafter), OQ-3
  (`session != Code` signal delegated to Code) — verified in
  `docs/adr/0013-autonomy-axis-relocation.md`.
- PLAN-0008 OQ-D + L3-reset + `PreToolUse`-dispatch + worktree-key
  carry-overs — verified in `docs/plans/done/0008-...md` Notes/Steps and
  `docs/STATUS.md`.
- Registry rows G1–G5 / C1–C4 / H1 / L1–L4 and the deferred `PreToolUse`
  dispatch — verified in `.claude/autonomy-triggers.md`.

AI-assisted per project convention (noted in commit body, never as
Co-Authored-By, per CLAUDE.md §7).
