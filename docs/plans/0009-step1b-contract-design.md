# PLAN-0009 Step 1b — Subagent Contract Design

**Status:** Ready for execution (this is the design artifact; Phase 3 Step 2/3/4/5/6 consume contracts defined here)
**Owner:** Claude Code (Tier 2 — subagent primitives are Code-exclusive per ADR-013 D1)
**Created:** 2026-05-26
**Parent plan:** [PLAN-0009 §Step 1b](0009-subagent-topology.md) (`docs/plans/0009-subagent-topology.md`)
**Related ADRs:** ADR-013 (autonomy axis relocation — D1 phased relocation), ADR-009 (D2 only-Code-commits boundary extended to subagents), ADR-012 (D4.3 author≠reviewer disclosure — `plan-drafter` stamp), ADR-006 (core vs vertical infrastructure)
**Related research:** `docs/research/private/2026-05-25-subagent-primitive-survey.md` (Step 1a survey, 8/8 high-confidence; gitignored, local-durable)
**Related lessons:** Lesson #8 (Cowork K-1/K-2 — sibling), Lesson #9 (Auto-mode Sonnet+ floor — `plan-drafter` model floor), Lesson #10 (classifier blocks direct push — informs PR-flow for `plan-drafter` drafts)

> **Ratification status.** Cray ratified 5 small contract decisions (SD1b-1 … SD1b-5) on 2026-05-26 alongside the outline. All 5 = agreed with Code recommendations. This document is the durable design output of Step 1b.

> **Sequencing.** Step 1b unblocks PLAN-0009 Step 2/3/4/5/6 (execution arc). Steps 2–6 may proceed against contracts defined here subject to internal dependencies. Step 6 (Tests + live AC + closeout) consumes all prior steps.

## Goal

Define the **machine-checkable contracts** for the two custom subagents introduced by PLAN-0009 (the read-only `explore-research` and the writer `plan-drafter`) + the **hook architecture** (G5 extension + new H2 write-path deny + `SubagentStart`/`SubagentStop` wiring) that enforces them. Step 1b is **design-only**: actual subagent files (Step 2/3), hook patches (Step 5), and dispatch routing (Step 4) are downstream deliverables that consume this design.

The load-bearing safety property — *only the main Code agent can commit; both subagents are denied at the hook layer (not by prompt)* — is preserved across all 4 identity cases via the **composed G5 check** (§1) shared with PLAN-0010 AC-4.

## §1 — Identity gate (composed G5 check)

The single load-bearing primitive shared across Phase 3 (subagents) + Phase 3.5 (scheduled tasks). **Same check, four cases.**

### Logic

```python
# Pseudocode for pretooluse_git_deny.py extension (Step 5 implements)
def is_commit_allowed(hook_stdin: dict, env: dict) -> bool:
    agent_id = hook_stdin.get("agent_id")  # Step 1a Q3 — absent for main agent
    tier = env.get("CLAUDE_TIER", "")
    return (agent_id is None) and (tier == "code")
```

### Four-case identity matrix (binding for AC-3 / AC-4 / AC-6)

| # | Identity case | `agent_id` in hook stdin | `CLAUDE_TIER` env | Verdict | Justification |
|---|---|---|---|---|---|
| 1 | Main Code interactive | absent | `code` | ✅ allow commit | Verified live PLAN-0008 AC-1 Run 1+2 + session 10 |
| 2 | Main Code scheduled (Phase 3.5) | absent | `code` (verified live) | ✅ allow commit | Verified live Phase 3.5 smoke F5 |
| 3 | `plan-drafter` / `explore-research` subagent (Phase 3) | **PRESENT** (with `agent_type` = subagent name) | (inherited from main) | ❌ deny commit | Step 1a Q3 documentation + ADR-013 D2 enforcement |
| 4 | Cowork (impossible reach) | absent | empty/other | ❌ deny commit | Cowork sandbox has no `Bash` per K-1; this row defends against future cross-tab transport |

### Why composed (not two separate checks)

One function with two conditions ANDed together covers all 4 cases. Separate checks (a subagent gate + a tier gate) would:

- Duplicate the deny-side logic across hook implementations
- Risk drift if one is updated without the other
- Hide the "all 4 cases by design" intent from readers

The composed check makes the safety property an invariant readable in 3 lines of code.

### Bypass-immunity (ADR-013 D2)

The G5 hook fires regardless of `permissionMode`, including `bypassPermissions`. Step 5 must preserve this; AC-6 includes a `bypassPermissions` × subagent negative test.

## §2 — Custom subagent names (shadow-avoidance)

Anthropic ships **two built-in subagents whose names are reserved**: `Plan` (read-only, used inside plan mode) and `Explore` (read-only, Haiku, denied Write/Edit). Per Step 1a survey §6 + Surprising findings: defining a custom subagent named `Plan` or `Explore` collides with the built-in registry — precedence rules may shadow ours, and hook `agent_type` matchers become ambiguous.

**Custom subagent names (binding for Steps 2/3):**

| Phase 3 role | Custom name | Filename | Avoids collision with |
|---|---|---|---|
| Read-only research subagent | **`explore-research`** | `.claude/agents/explore-research.md` | Built-in `Explore` (Haiku, read-only, denied Write/Edit) |
| Writer (ADR/PLAN drafting) | **`plan-drafter`** | `.claude/agents/plan-drafter.md` | Built-in `Plan` (read-only, used in plan mode) |

Hook `agent_type` matchers (G5 deny + H2 write-path deny + `SubagentStart`/`SubagentStop`) reference these custom names **exactly**. Renaming after Step 5 wiring is a coordinated change across hook configs + subagent files + handoff schema if it leaks into handoffs.

## §3 — Per-subagent contract: `explore-research` (read-only)

The harness-native read-only research subagent. Mirrors built-in `Explore`'s purpose (codebase research + fact-pack gathering) but adds `WebFetch` per OQ-2 (Cray-ratified 2026-05-25).

### Frontmatter fields

```yaml
---
name: explore-research
description: |
  Read-only codebase + web-research subagent. Use for fact-pack gathering,
  codebase archaeology ("where is X / what references Y"), and external
  prior-art research before a plan-drafter draft. Returns bounded summary
  + file/line citations + URL list.
tools:
  - Read
  - Grep
  - Glob
  - WebFetch
disallowedTools:
  - Write
  - Edit
  - Bash
  - Agent           # cannot spawn nested subagents per Step 1a Q6
model: inherit       # Opus 4.7 — SD1b-3 ratified
maxTurns: 50         # SD1b-2 ratified — research sweeps need more turns
# isolation: <omitted> — SD1b-5; worktree-OFF default per §11
# background: <omitted> — caller decides at spawn time
---
```

### Input schema (caller-provided at spawn)

- `task_prompt` — self-contained instruction (subagent has no parent transcript per Step 1a Q4)
- `scoped_context` — minimal facts the subagent needs to start (file paths, key terms, prior findings to extend)
- (No `cwd` override — Step 1a Q2 confirms subagent inherits parent cwd; cannot narrow below)

### Output schema (encoded in subagent system prompt — markdown body)

The subagent's **final message** (the only thing returned to the parent per Step 1a Q4) must follow this template:

```markdown
# Research findings: <one-line summary>

## Bounded summary (≤ 2k tokens guideline; primitive does NOT enforce — see §6)
<key findings as prose, ≤ 6 paragraphs>

## File/line citations
- `path/to/file.py:42` — <quote or paraphrase>
- ...

## External URLs (if WebFetch used)
- <url> — <one-line excerpt>

## Residual gaps / open questions
- <any question the survey could not answer with high confidence>
```

### Hook bindings

- **Project-level G5** (extended composed check per §1) — denies any git op when `agent_id` present (defense-in-depth; `explore-research` has no `Bash` so cannot reach git directly, but the gate fires for the impossible-reach case)
- **No subagent-scoped frontmatter hooks** — `explore-research` has no `Write`/`Edit` so H2 (§5) does not bind

### Verification cases (feeds §8 matrix)

- **Happy:** main spawns `explore-research` with task → receives bounded summary
- **Boundary:** `maxTurns: 50` reached → subagent returns partial findings with explicit residual-gaps section
- **Fail-closed:** `Write`/`Edit`/`Bash` attempt → harness-layer deny (Step 1a Q1)
- **Adversarial:** prompt-injection trying to talk the subagent into `Write` — denied at allowlist (not prompt discipline)
- **Concurrency:** multiple `explore-research` spawned in parallel (Step 1a Q8) — each independent; result-reduction does not race

## §4 — Per-subagent contract: `plan-drafter` (writer, ADR/PLAN drafting)

The harness-native governance-drafting subagent. Replaces (for the *co-located* case only — AC-5) the Cowork-tab paste loop with an in-harness dispatch. Cowork retained as **external advisory drafter** for author≠reviewer separation per ADR-013 OQ-1.

### Frontmatter fields

```yaml
---
name: plan-drafter
description: |
  Writer subagent for ADR/PLAN drafting. Receives a self-contained
  drafting task + scoped context; produces a PR-ready uncommitted draft
  under docs/{adr,plans}/NNNN-*.md. Returns the draft path + a bounded
  summary. The main agent commits (subagent cannot — G5 binds).
tools:
  - Read
  - Grep
  - Glob
  - Write
  - Edit
disallowedTools:
  - Bash            # no shell; no git access from subagent
  - WebFetch        # plan-drafter consumes explore-research's findings;
                    # does not fetch directly (separation of concerns)
  - Agent           # cannot spawn nested subagents
model: inherit       # Opus 4.7 — SD1b-3 ratified; Lesson #9 Auto-mode Sonnet+ floor honored
maxTurns: 30         # SD1b-2 ratified — drafting is bounded scope
# isolation: <omitted> — SD1b-5; draft lands in parent cwd → main agent commits
hooks:
  PreToolUse:
    - matcher: "Write|Edit"
      command: ".claude/hooks/pretooluse_plan_subagent_write_deny.py"
      # H2 — see §5; subagent-scoped per Step 1a Q5 (frontmatter hooks
      # are cleaner than project-level matchers gated on agent_type)
---
```

### Input schema (caller-provided at spawn)

- `task_prompt` — self-contained drafting instruction (artifact type, fact-pack, structure cues)
- `scoped_context` — `explore-research` findings (when chained), prior ADRs/PLANs referenced, citation requirements
- `artifact_kind` ∈ {`adr`, `plan`} — used by output schema to pick template
- `target_number` — the assigned `NNNN` (caller enumerates the directory pre-spawn; subagent does not pick)

### Output schema (encoded in subagent system prompt)

```markdown
# Drafting complete: <artifact path>

## Author≠reviewer disclosure (ADR-012 D4.3 mandatory)
This draft was authored by the in-harness `plan-drafter` subagent under
ADR-013 D1 phased authority. The outline originator was <Code | Cray |
Cowork>, and the independent reviewer will be <designated reviewer>.
Separation: <INTACT | NOT INTACT — flag for Cray>.

## Bounded summary (≤ 1k tokens guideline)
<≤ 4 paragraphs covering: goal of artifact; key decisions surfaced;
non-obvious dependencies; surfaced decisions for Cray>

## Artifact path
docs/{adr,plans}/<NNNN-name>.md

## Surfaced decisions (per Cowork rule #8 — NOT silently chosen)
- SD-N: <question> | Code rec: <X> | Cray adjudicates
```

### Hook bindings

- **Project-level G5** (extended composed check per §1) — denies any git op when `agent_id` present; this is the load-bearing AC-3 + AC-4 + AC-6 deliverable
- **Subagent-scoped H2** (new — `pretooluse_plan_subagent_write_deny.py`) — see §5; denies `Write`/`Edit` outside `docs/{adr,plans}/NNNN-*.md`
- **Project-level H1** (existing handoff validator, PLAN-0007) — still runs deterministically on any `.claude/handoffs/` write, unchanged

### Verification cases (feeds §8 matrix)

- **Happy:** main spawns `plan-drafter` with task → draft appears at `docs/plans/NNNN-*.md` (uncommitted) → main commits via PR-flow per CLAUDE.md §7
- **Boundary:** draft hits `maxTurns: 30` → subagent emits residual-gaps section + flags incomplete
- **Fail-closed (write-path):** `plan-drafter` `Write` attempt to `services/api/main.py` → H2 denies (Step 1a Q5 PreToolUse hook)
- **Fail-closed (commit):** `plan-drafter` `Bash` attempt (would fail at `disallowedTools` first) → also denied at G5 if it reached the hook; AC-3 negative test asserts G5 fires
- **Adversarial:** prompt-injection trying "skip the disclosure stamp" → mitigated by system-prompt rigor; **residual risk** if the subagent ignores its prompt (named in §8)
- **Concurrency:** two `plan-drafter`s spawned in parallel for different artifacts (`adr/0014` + `plan/0011`) — independent `target_number`s; no `NNNN` collision (caller enumerates pre-spawn)

## §5 — Hook architecture (Phase 3 additions)

Three hook changes land in Step 5 (execution phase). Step 1b specs them; Step 5 implements.

### G5 extension (composed check)

- **File:** `.claude/hooks/pretooluse_git_deny.py` (existing — extend, do not replace)
- **Change:** add `agent_id` stdin check; combine with existing `CLAUDE_TIER` env check via AND (§1 pseudocode)
- **Identity matrix:** all 4 cases tested (§1 table); 16-case bypass-immune matrix from PLAN-0007 extended to include rows 2 (scheduled) and 3 (subagent) → **18-case new matrix**; AC-6 binding
- **Stdin handling:** robust to missing `agent_id` key (treated as `None`, matches main-agent case); robust to malformed JSON (fail-closed deny)

### H2 — new subagent-scoped write-path deny (`pretooluse_plan_subagent_write_deny.py`)

- **File (new):** `.claude/hooks/pretooluse_plan_subagent_write_deny.py`
- **Wiring:** referenced in `plan-drafter` frontmatter `hooks.PreToolUse` (subagent-scoped per Step 1a Q5 — cleaner than project-level matcher gated on `agent_type == "plan-drafter"`)
- **Matcher:** `Write|Edit`
- **Logic:**
  ```python
  ALLOWED_PREFIXES = ("docs/adr/", "docs/plans/")
  def is_allowed(tool_input: dict) -> bool:
      path = tool_input.get("file_path", "")
      return any(path.startswith(p) for p in ALLOWED_PREFIXES) and path.endswith(".md")
  ```
- **Pattern source:** extends C4 `pretooluse_research_path_deny.py` (PLAN-0007) — same exit-2-on-deny convention; same fail-closed-on-malformed-input discipline
- **Bypass-immunity:** fires regardless of `permissionMode` (ADR-013 D2 — Step 5 includes a `bypassPermissions` × `plan-drafter` `Write` outside allowlist negative test)

### `SubagentStart` / `SubagentStop` event wiring (AC-5 notification)

- **Events:** Anthropic primitive emits both (Step 1a Q3 surprising findings); matcher on `agent_type`
- **Use case (AC-5):** when `plan-drafter` completes, fire Telegram via `tools/notify/telegram.sh` (PLAN-0007) so Cray is notified without polling the chat
- **File (new — Step 5 execution):** `.claude/hooks/subagentstop_notify.py`
- **Matcher:** `agent_type ∈ {plan-drafter}` initially; `explore-research` notifications deferred (research sweeps are not Cray-actionable on completion)
- **Degradation:** if Telegram env vars unset → graceful no-op (PLAN-0007 pattern)
- **`SubagentStart`:** optional log-only wiring; not in AC-5 scope but specced here for future observability without re-opening the contract

## §6 — Result reduction contract

The primitive's reduction is **"final assistant message verbatim"** with **no hard byte/token bound** (Step 1a Q4). The bounded-summary contract from PLAN-0009 §Step 1b is **not enforced by the primitive** — it must be encoded in the subagent's system prompt (markdown body).

### Three mitigations (all three must ship)

1. **Output schema in markdown body** (§3 + §4 above) — the subagent's system prompt instructs the exact final-message template + the ≤ 2k tokens (`explore-research`) / ≤ 1k tokens (`plan-drafter`) guideline.
2. **Artifact-path-only pattern** — when a draft file exists (`plan-drafter` case), the final message references the **path**, not the file contents. The main agent reads the artifact from disk if needed.
3. **Budget guideline assertion in dispatch** (Step 4 deliverable) — the main agent's spawn payload includes the budget reminder as part of `task_prompt` (defense-in-depth against subagent system-prompt drift).

### Residual risk (named in §8 + sign-off binding)

A misbehaving subagent (prompt injection, hallucinated verbosity, runaway final message) could still emit a final message exceeding the guideline. The primitive has no hard cap. Mitigation = `maxTurns` (cheap loop bound) + AC-1 verification (assert final message ≤ 4k tokens for the happy path) + post-merge observability (main agent measures returned size and alerts on > 4k tokens).

## §7 — State-schema touch decision

**Decision: omit.** `.claude/state/` is **not** touched by Phase 3. (SD1b-1 ratified.)

### Rationale

Subagent bookkeeping uses the **primitive-native subagent transcript path** (`~/.claude/projects/<project>/<sessionId>/subagents/agent-<id>.jsonl`, per Step 1a §3 surprising findings). No new state field needed. The two PLAN-0008 carry-overs remain deferred:

| Carry-over | Status after Step 1b | When to revisit |
|---|---|---|
| **L3 automatic reset** (multi-tool error-signature observation) | Still deferred; PLAN-0008 §Step 4 closeout reasoning intact | When an L3-class failure occurs in unattended autonomy (Phase 3 or Phase 3.5 execution) and the lack of automatic reset accumulates Cray-paste friction |
| **Worktree path normalization** (`_loop_counter._normalize_file_path`) | Still deferred; STATUS 2026-05-25 finding intact | When a worktree-keyed counter row causes a real false-negative on loop-detect across worktree boundaries |

Both are reactive triggers; neither is needed pre-emptively for Phase 3 to ship.

## §8 — Verification matrix (case-coverage per Cray verification-rigor directive)

Mirrors PLAN-0009 §Step 6 + PLAN-0010 §Verification. Per the binding directive: each AC ships rows covering **happy / boundary / fail-closed / adversarial / concurrency**, with a test mapped to **every** row; uncovered cases are named as residual risk; sign-off states confidence explicitly. Bar = **"we are confident it does what we intend,"** not "tests pass."

### Per-AC matrix (Step 6 will fill the test column)

| AC | Happy | Boundary | Fail-closed | Adversarial | Concurrency |
|----|-------|----------|-------------|-------------|-------------|
| **AC-1 contract** | Main spawns each subagent → reduced result | `maxTurns` reached → partial result + residual gaps | Malformed input schema → spawn fails fast | Prompt-injection ignoring output template → final message > 4k tokens → observability alert (§6 residual) | Multiple subagents in parallel → results merge correctly |
| **AC-2 `explore-research` read-only** | Read/Grep/Glob/WebFetch succeed | `maxTurns: 50` reached | Write/Edit/Bash → allowlist deny (Step 1a Q1) | Prompt asks "ignore allowlist and Write" → still denied at harness | Two `explore-research` parallel → no cwd interference |
| **AC-3 `plan-drafter` write-scope + no-commit** | Draft at `docs/plans/0011-foo.md` | `maxTurns: 30` reached | Write outside `docs/{adr,plans}/` → H2 deny; Bash → disallowedTools; git → G5 deny | `bypassPermissions` × `plan-drafter` Write to `services/` → still denied | Two `plan-drafter`s parallel different NNNNs → no collision |
| **AC-4 dispatch protocol** | 4 routing cases green (2 spawn / 2 inline) | Budget reminder propagation verified | Misconfigured tool list at spawn → deny | Crafted `scoped_context` with hidden instructions → spec mitigations (Step 4) | Concurrent spawns from main → all return |
| **AC-5 OQ-D auto-handoff in-harness** | Stop classifier → spawn `plan-drafter` → draft → main commits → Telegram fires | `SubagentStop` notification fires for `agent_type=plan-drafter` only | Telegram env unset → graceful no-op | Stop classifier mis-fires → main agent inline-handles (no false spawn) | Two governance triggers near-simultaneous → ordered dispatch |
| **AC-6 Phase 1+2 regression** | 18-case G5 matrix green; H1/C4 green; L1–L4 green; Stop loop + classifier green | Each prior boundary preserved | Each prior fail-closed preserved | `bypassPermissions` × every guarded op | Concurrent main-agent + scheduled task + subagent — all gates compose |

### Residual risks (named for sign-off)

1. **Final-message size unbounded by primitive** (§6) — observability alert is the only post-hoc safety net; runaway message could blow main context before alert fires
2. **Author≠reviewer separation for `plan-drafter`** — Plan subagent shares main harness's framing/context (Step 1a Q4) → no in-harness independent-deliberation check; ADR-013 OQ-1 mitigation (Cowork retained as external advisory drafter) is preserved by *policy*, not enforced by *primitive*
3. **`maxTurns` + L1–L4 loop-detect overlap** — both are loop-bounds; cheap insurance but could mask which one fired in postmortem; logging must record both signals
4. **Subagent transcript persistence** (`~/.claude/projects/.../subagents/`) is **outside repo + outside `.claude/state/`** — audit trail lives on the local machine only; cross-machine forensics impossible without manual copy

## §9 — Deferred to Step 2–6 execution

Out of scope for Step 1b. Step-by-step execution plan (Phase 3 §Step 2–6 in `docs/plans/0009-subagent-topology.md`):

| PLAN-0009 Step | Step 1b deliverable consumed | New work |
|---|---|---|
| **Step 2** — `explore-research` subagent file | §3 contract | Write `.claude/agents/explore-research.md` with frontmatter + system prompt encoding output schema |
| **Step 3** — `plan-drafter` subagent file + H2 hook | §4 contract + §5 H2 spec | Write `.claude/agents/plan-drafter.md` + `.claude/hooks/pretooluse_plan_subagent_write_deny.py` |
| **Step 4** — Dispatch protocol | §1 composed check + §6 budget guideline + AC-4 routing | Document spawn-vs-inline decision + context-propagation discipline + budget reminder injection |
| **Step 5** — Auto-handoff (OQ-D in-harness arm) + G5 extension + `SubagentStop` wiring | §1 composed check + §5 `SubagentStop` notification | Extend `pretooluse_git_deny.py` for the composed check + wire `subagentstop_notify.py` |
| **Step 6** — Tests + live AC + closeout | §8 matrix template | Fill the test column for every row; live-verify the matrix; sign off residual risks |

## Implementation Notes

Drafted by Code (Tier 2, Claude Code Opus 4.7) in session 11 (2026-05-26). Per ADR-013 D1 phased authority, the `plan-drafter` subagent — the in-harness drafter that *would* author such a design doc — does not yet exist (it is the very thing this doc designs). So Step 1b is necessarily **Code-drafted, not Cowork-drafted**; the author≠reviewer separation for *this* artifact is held by **Cray's review at PR merge**, not by drafter/reviewer tier distinction.

Cray ratified the 5 contract decisions (SD1b-1 … SD1b-5) on 2026-05-26 in the session-11 thread. All 5 ratifications = agreement with Code recommendations:

- **SD1b-1** = omit `.claude/state/` touch (§7)
- **SD1b-2** = `maxTurns: 50` for `explore-research`, `30` for `plan-drafter` (§3 + §4)
- **SD1b-3** = `model: inherit` (Opus 4.7) for both (§3 + §4)
- **SD1b-4** = `SubagentStop` notification *designed* in Step 1b, *implemented* in Step 5 (§5)
- **SD1b-5** = omit `isolation: worktree` for `plan-drafter` (§4)

AI assistance: drafted by Code (Claude Code, Opus 4.7). AI-assistance noted in commit body per CLAUDE.md §7; never `Co-Authored-By`.
