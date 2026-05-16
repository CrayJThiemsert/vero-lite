# Lesson #5 — Tier-System Audit Baseline (2026-05-15)

> **Status:** Captured (post-audit baseline)
> **Captured:** 2026-05-15 (Session 10 governance mini-batch closeout)
> **Captured by:** Chat tab (Tier 1) drafted; Code tab (Tier 2) applied
> **Predecessor:** Lesson #4 (WSL bash -c variable expansion)
> **Successor:** TBD (next durable learning)
> **Related ADRs:** None (audit findings below ADR threshold per CLAUDE.md §1 precedence)
> **Related lessons:** #3 (worktree lifecycle traps — referenced from new CLAUDE.md §11)

---

## Context

After 10 sessions of multi-tier collaboration (Tier 0 Cowork, Tier 1 Chat,
Tier 2 Code, Tier 3 Cray), Chat tab conducted a governance audit of the
three primary collaboration files: `CLAUDE.md`, `chat_tab_instructions.md`,
and `cowork_tab_instructions.md`. The audit used a multi-lens framework
(Confucian roles/rituals, Daoist flow, Mohist utility, systems thinking,
right speech, multi-agent cooperation, middle-way balance) to identify
governance debt before it compounded into session-over-session friction.

Audit produced 10 findings. A governance mini-batch addressed 6 findings
in a single atomic commit (`ac3baf3`). The remaining 4 findings are
either deferred to PLAN-004 Phase A (which inherits them naturally) or
parked as low-priority.

This lesson captures:
1. **Canonical 10-finding numbering** so future references resolve
   unambiguously (commit subject `ac3baf3` listed an incorrect subset
   — see §3.1 below for the corrected numbering)
2. **Constitutional-file edit + session-restart pattern** (originally
   conceptualized as "Lesson #15 candidate" during the audit cycle;
   folded into §1 below per audit recommendation rather than minted
   as a separate lesson)
3. **Outstanding follow-up items** that should not be silently dropped

**Note on lesson numbering convention:** This file is `0005-...md`,
the fifth lesson file in `docs/lessons/`. During the audit cycle the
working name "Lesson #15 candidate" was used informally in handoffs
(extrapolated from Lessons #13 and #14 references in CLAUDE.md). On
2026-05-15 a normalization pass aligned conversational references with
file numbering: lesson body titles and inline references match the
file number (`0001` = Lesson #1, `0005` = Lesson #5, etc.). The
"Lesson #15 candidate" terminology is preserved here as historical
record only.

---

## Canonical finding numbering

The 10 findings produced by the audit, with canonical numbering and
resolution status:

| # | Finding | Status |
|---|---|---|
| 1 | CLAUDE.md §6 describes a 2-tier world (Chat + Code only); Tier 0 (Cowork) and Tier 3 (Cray) absent | **RESOLVED** (mini-batch — new 4-tier table) |
| 2 | Phase/batch hardcoded in tier instruction files (Chat says "Batch 3", Cowork says "Batch 4" — already drifted) | **RESOLVED** (mini-batch — pointer to STATUS.md) |
| 3 | No precedence rule when sources conflict (CLAUDE.md vs ADR vs lesson vs tier instructions) | **RESOLVED** (mini-batch — §1 Precedence subsection) |
| 4 | Tier 1 file-write asymmetry (Cowork has `cowork-` prefix discipline; Chat does not) | **DEFERRED — partially resolved** (mini-batch added forward-declared `chat-` prefix convention; actual write capability awaits interface change) |
| 5 | Three "source of truth" lists drift independently across the three files | **RESOLVED** (mini-batch — tier files point to CLAUDE.md §10) |
| 6 | "Type X" / "Type Y" terminology referenced as if defined but undefined | **DEFERRED** (low priority; current usage works; address on next file-touch) |
| 7 | Tier 1 instructions ~3x shorter than Tier 0; no precedent log or self-check parity | **RESOLVED** (mini-batch — added Tier 1 self-check (6-item) + empty precedent log) |
| 8 | Worktree policy lives in CLAUDE.md §6 (constitutional creep) — should be Tier 2 tactical policy | **RESOLVED** (mini-batch — relocated to new §11 Tier 2 Operational Policy) |
| 9 | No archival/rotation rule for tier-instruction precedent logs (will grow over time) | **DEFERRED — partial via PLAN-004** (Phase A validator naturally surfaces archive pressure; explicit policy still needed) |
| 10 | Multi-instance ambiguity — no protocol for parallel Chat conversations or parallel Cowork dispatches | **DEFERRED** (low priority; current solo-developer cadence keeps work sequential) |

**Errata note:** Commit `ac3baf3` subject line reads
`findings 1, 2, 3, 5, 8` — this was a drafting error in the coordination
handoff. The correct resolved set is **{1, 2, 3, 5, 7, 8}** (six
findings, not five — #7 added Tier 1 self-check and precedent log).
Commit subject is not amended; the canonical numbering is authoritative
going forward.

---

## Lesson body

### 1. Constitutional-file edits require Code-tab session restart

**Pattern observed:**

`CLAUDE.md` is injected into a Code tab session's context at session
start, not on every tool call. When the same Code tab session edits
`CLAUDE.md` (or any tier instruction file), the file content changes
on disk but the **system reminder** that binds Tier 2 behavior remains
the pre-edit version until the session restarts.

This creates an asymmetry: a Code tab session that just committed an
update to CLAUDE.md §6 (4-tier model) would not see the 4-tier model
as authoritative for its own subsequent reasoning in that same session —
it would still be operating under the old 2-tier table.

**Implication:**

Sequence for constitutional-file edits must be:

1. Code tab executes the constitutional edit + commit
2. Code tab produces a **restart bridge handoff** describing:
   - Commit SHA of the constitutional change
   - Locked decisions from the prior session
   - Standby posture for the new session
3. Close the Code tab session
4. Cray restarts Claude Desktop
5. New Code tab session reads bridge handoff first → reads updated
   CLAUDE.md as authoritative system reminder → proceeds with downstream
   work

**Test for "constitutional":**

If the file being edited appears in the Tier-2 read-priority list at
session start (CLAUDE.md §9), the constitutional pattern applies.
Specifically: `CLAUDE.md`, `docs/STATUS.md`, files under `docs/adr/`,
files under `docs/conventions/` matching tier instructions.

State files (e.g., `docs/STATUS.md` daily updates) can proceed in-session
because they encode state, not rules. Rule files cannot.

**First instance:** Session 10 governance mini-batch (this audit) →
PLAN-004 Phase A bridge (`2026-05-15-2218-code-session10-restart-bridge.md`)

### 2. "Chat designs / Code executes" boundary works at scale

**Pattern observed:**

The governance mini-batch was the first time Tier 2 (Code) modified
constitutional files (`CLAUDE.md` + tier instructions) based on Tier 1
(Chat) content design rather than its own initiative or direct Cray
instruction. The boundary held cleanly:

- Code tab surfaced ambiguity in coordination handoff (`§6.1` of
  closeout) rather than silently fixing
- Code tab flagged scope expansion (`§6.3` — Chat draft touched §4 and
  §10 of CLAUDE.md beyond what coordination notice §3.1 specified)
  rather than silently narrowing execution
- Code tab surfaced fuzzy cross-reference (`§6.4` — archived path) for
  follow-up rather than treating as broken
- Code tab caught Chat's drafting error in commit subject numbering
  (`§6.1` — `{1,2,3,5,8}` vs canonical `{1,2,3,5,7,8}`) and surfaced
  for fix-forward

**Implication:**

The boundary discipline established for Cowork (Tier 0) flag-and-pause
pattern translates cleanly to Tier 2. Both tiers benefit from the same
rule: "If the design has ambiguity or contradicts something authoritative,
surface and pause — do not silently fix."

**Counterfactual:** If Code tab had silently fixed the commit subject
to `{1,2,3,5,7,8}`, the audit trail would have been clean but Chat
tab's drafting weakness would have gone uncaught, and similar errors
would recur.

### Sub-rule: Cray-direct constitutional codification path

**Pattern observed (Session 11, 2026-05-16, commit `dd65d9b`):**

Code tab authored CLAUDE.md §11 "Transcript Handoff" subsection under
direct Cray (Tier 3) wording approval, codifying an existing runbook
(`docs/runbooks/transcript-handoff.md`) into constitutional form.
Normally constitutional content originates from Chat (Tier 1) design
per §2 above.

**When the path is valid:**

The Cray-direct codification path is acceptable when ALL apply:

1. **Source exists** — the content being codified is already authoritative
   in a non-constitutional artifact (runbook, lesson, ADR, established
   convention)
2. **Codification is thin** — the constitutional text adds invariant
   wording + pointer, not new design decisions
3. **Cray initiates explicitly** — direct instruction to Code, not
   inferred from context
4. **Post-hoc ratification follows** — Chat reviews the resulting
   constitutional text + source artifact for fit; ratification is logged
   (this sub-rule + cross-reference in the relevant lesson body)

**When Chat-first design is still required:**

- Net-new constitutional content (no existing source artifact)
- Multi-tier policy (affects Tier 0 / Tier 1 boundaries)
- Conflict with existing precedence rules (§1)
- Wording that encodes design decisions not yet settled

**Asymmetry with §2 main rule:**

The main rule says "Chat designs / Code executes." This sub-rule does not
weaken that — design is still Chat's; codification of *already-designed*
content can be Code's when Cray initiates. The Tier 3 (Cray) authority
chain remains: Cray sees runbook → Cray instructs Code → Code codifies →
Chat ratifies. Chat is not bypassed; the cycle is post-hoc instead of
pre-hoc.

**First instance:** §11 Transcript Handoff promotion (Session 11,
commit `dd65d9b`, ratified Session 10-continuation via Chat tab on
2026-05-17).

### 3. Coordination handoff format needs scope-precision discipline

**Pattern observed:**

Chat's coordination handoff (`2026-05-15-1700-chat-governance-mini-batch-
coordination.md`) listed CLAUDE.md changes as "§1, §6, §11" but the
actual drafts also modified §4 (Memory table) and §10 (docs/conventions
row) — necessary changes for self-consistency, but not explicit in the
coordination scope.

Code tab caught this in closeout §6.3 as scope expansion. Semantically
aligned; mechanically a coordination-document inaccuracy.

**Implication:**

Coordination handoffs that scope Code tab work should list **every**
section touched, not just the headline ones. If a draft requires
secondary edits for consistency (e.g., index update, table row update),
list them in the coordination notice or note them as "expected secondary
changes" with rationale.

**Proof-of-life observation:** Within hours of this lesson landing on
disk, Cray applied the same scope-precision check across peer files —
asking "should `cowork_tab_instructions.md` also be updated?" when
Chat proposed a CLAUDE.md normalization that touched a pattern shared
by tier instruction files. The check correctly revealed the Cowork
file had no specific Lesson-number references (only `docs/lessons/*.md`
glob), so no edit was needed. Cray's instinct mirrored §3's rule:
"When a governance pattern is touched in one file, regression-check
every peer file." Pattern works as intended.

**Template fix for future Chat coordination handoffs:**

When listing scope in coordination handoffs, use this format:

```
**Primary changes** (the work itself):
- File X §N — describe change
- File Y §N — describe change

**Secondary changes** (for self-consistency, not the work itself):
- File X §M — index/cross-ref update because of primary §N
- File Z §M — pointer update because of primary
```

### 4. Handoff files are gitignored by design — surface clearly

**Pattern observed:**

Code tab discovered that `.claude/handoffs/.gitignore` uses `*` pattern
to ignore all handoff files by default. The closeout and restart bridge
handoffs Code tab created appeared as "untracked" but were actually
intentionally excluded from version control.

This is correct per project policy (handoff files are working notes,
session-scoped, not part of canonical repo history). But for a new
session reading `git status`, the absence of these files from version
control could appear to be a missing-commit issue.

**Implication:**

This is not a bug. The pattern is correct. But the implicit nature of
the policy creates a confusion risk for new sessions. Recommend a
one-liner in `CLAUDE.md` §10 or `.claude/handoffs/README.md` noting:
*"Handoff files are gitignored by design (session-scoped working notes
between tiers). Canonical artifacts live in docs/."*

**Not addressed in mini-batch.** Captured here for future minor
revision.

---

## Outstanding follow-up items

### 5.1 "Lesson #15 candidate" terminology — resolved by normalization

During the audit cycle, Code tab and Chat tab used the informal label
"Lesson #15 candidate" in handoffs (governance mini-batch closeout §7,
restart bridge §7) to refer to the constitutional-edit pattern captured
in §1 above. The "#15" number was an extrapolation from CLAUDE.md
references to "Lesson #13" and "Lesson #14".

On 2026-05-15 Cray identified that file numbering (`0001-0005`) and
conversational references (`#13`, `#14`) had drifted apart by an
offset of 10, creating future confusion risk. The apply batch that
landed this lesson also normalized references in CLAUDE.md §7 and §11
to use file-aligned numbers (`Lesson #4` for `0004-...md`, `Lesson #3`
for `0003-...md`).

**Status:** The "Lesson #15 candidate" terminology is preserved in
this file as historical record only. All future references use
file-aligned numbering.

### 5.2 Fuzzy cross-reference fix in `chat_tab_instructions.md`

Closeout §6.4 identified that `chat_tab_instructions.md` references
`2026-05-12-1050-...batch2-mid.md` twice (as template example), but the
file is at `.claude/handoffs/archive/chat-export-2026-05-13/project-
knowledge/2026-05-12-1050-chat-conversation-handoff-batch2-mid.md`,
not in `.claude/handoffs/session-10/`.

**Fix applied in this apply batch:** Edit
`docs/conventions/chat_tab_instructions.md` to mark the reference as
`(archived template, see .claude/handoffs/archive/...)` per Lesson #5
recommendation option (b). Preserves historical pointer while making
archived status explicit.

### 5.3 Coordination handoff template (next Chat work)

Per §3 above, future Chat coordination handoffs should adopt the
"primary changes" / "secondary changes" split. This is a Chat-side
discipline (not enforced via repo change), but noted here for traceability.

### 5.4 PLAN-004 Phase A inherits findings #9 surface

The handoff frontmatter validator that PLAN-004 Phase A will build
naturally surfaces archive pressure for precedent logs (finding #9
deferred above). Phase A spec should explicitly address: when a tier
instruction file's precedent log grows beyond N entries, rotation to
`docs/lessons/cowork-precedents.md` (or equivalent) is recommended.

Carried to PLAN-004 Phase A spec, not addressed here.

---

## Resolution

**Mini-batch landed via commit `ac3baf343de67e7d7a558bd6c862e96faa83fe14`**
on branch `main` (2026-05-15 22:17 +07).

Files modified:
- `CLAUDE.md` (§1, §4, §6, §10, §11 — see commit message)
- `docs/conventions/chat_tab_instructions.md` (NEW canonical file)
- `docs/conventions/cowork_tab_instructions.md` (NEW canonical file)

Handoffs produced (session-scoped, gitignored):
- `2026-05-15-1700-chat-governance-mini-batch-coordination.md` (Chat dispatch)
- `2026-05-15-2217-code-governance-mini-batch-closeout.md` (Code execution closeout)
- `2026-05-15-2218-code-session10-restart-bridge.md` (Code session restart bridge)

Outstanding work captured here (§5.2 fuzzy ref fix + §5.1 normalization)
is being addressed in the apply batch that lands this lesson. Findings
#4, #6, #9, #10 remain deferred per their individual rationale in the
canonical numbering table above.

---

## Test for regression

In future sessions, if any of these patterns recur, treat as regression
and re-open the relevant finding:

- A new tier instruction file appears that duplicates source-of-truth
  lists rather than pointing to CLAUDE.md §10 → finding #5 regression
- A new section in CLAUDE.md encodes tier-specific tactical policy
  (e.g., Tier 0 worktree analog) at the top level rather than under a
  tier-specific subsection (§11, §12, etc.) → finding #8 regression
- A coordination handoff lists only primary changes and Code tab
  discovers secondary scope expansion → finding from §3 above (this
  lesson) regression
- A constitutional-file edit lands without a restart bridge → §1 above
  (this lesson) regression
- A new lesson file is created where file number does not match
  conversational reference number → §5.1 above (this lesson) regression

---

*Lesson #5 ends. Lesson #6 will capture the next durable learning.*
