# Lesson #6: Code surface → Chat re-dispatch → Code execute (pattern)

> **Status:** Codified 2026-05-18 (this lesson cleanup batch v3).
> **Source:** Closeout `2026-05-16-1204-code-lesson5-apply-batch-closeout.md` §6 finding 5; sync `2026-05-16-2210-code-chat-sync-transcript-tooling.md` §2.2 finding 5; midflights `2026-05-18-1450-...` + `2026-05-18-1528-...` for the anchor-mismatch family.
> **Cross-references:** Lesson #5 §2 (Chat designs / Code executes — this lesson is a clean execution of the rule), Lesson #5 §2 Code-judgment-on-contradiction sub-rule (this is the *non-contradiction* sibling pattern); Lesson #5 §3 schema-fidelity sub-rule (failure modes #4 + #5 are this pattern's prevention layer).

## 1. The pattern

When Code tab discovers a **scope expansion**, **anchor mismatch**, or
other **gap** during execution that materially changes the batch shape
(more files, more lines, a different scope of work, unexecutable
anchors), the safe execution path is:

1. **Code surfaces** the discovery via stop-and-ask in the same reply
   (closeout, midflight, or in-progress flag) — NOT silently expanding
   scope, NOT silently dropping scope, NOT silently relocating anchors.
2. **Chat re-dispatches** with corrected scope, references the surface,
   and provides updated acceptance criteria.
3. **Code executes** the re-dispatched scope.

This produces a clean audit trail: every scope decision is in a Chat-
authored dispatch; every execution result is in a Code-authored closeout;
no scope changes happen inside Code execution silently.

## 2. First validated uses

### 2.1 Scope expansion (Session 11, `8274a66` → `c85a595`)

**Context:** Lesson #5 apply batch (`8274a66`) was scoped to normalize
references for `Lesson #13` and `Lesson #14`. During execution, Code
discovered (via pre-flight grep) that `Lesson #12` also had stale
references throughout the repo — same family of off-by-N numbering
inherited from the pre-audit era.

**Code surface (closeout `2026-05-16-1204` §scope-expansion):** Reported
the additional `Lesson #12` matches, paused, did NOT include them in
the apply batch.

**Chat (this thread, mid-session):** Reviewed scope expansion, Cray
chose Option 1 (sweep all three — `#12/#13/#14`), Chat drafted offset
sweep dispatch.

**Code re-dispatched execution (`c85a595` offset sweep):** Applied the
full `#12/#13/#14` → `#2/#3/#4` normalization.

**Result:** Clean two-commit history (`8274a66` original scope +
`c85a595` expanded scope) with audit trail across closeout + dispatch
files in `.claude/handoffs/session-10/`. No silent scope expansion. No
backed-out commits. No restart.

### 2.2 Anchor mismatch family — two sub-instances (Session 12 v1 → v2 → v3)

**Context:** Lesson cleanup batch went through **two pause-and-redispatch
cycles** for the anchor-mismatch family of issues:

#### 2.2.1 v1: Annotation-as-content confusion

Dispatch v1 (`2026-05-18-1440-...`) §6 instructed edits to
`docs/STATUS.md` Update Workflow referencing three "current text" blocks
that did not exist in the file. Chat had confused predecessor execute-
dispatch annotation text (`2026-05-18-1143` §3) with content actually
written into STATUS.md by execute commit `ec38e2b`.

**Code surface (midflight `2026-05-18-1450-...` §2):** Anchor
verification caught the hard failure before any edit. Code paused the
whole batch per this lesson's anti-pattern "silent scope contraction".

**Chat (this thread):** Ratified Option 6-A (additive rather than
replace), disambiguated §3.1/§3.2/§3.3 per Code midflight
recommendations, drafted v2 re-dispatch.

#### 2.2.2 v2: Inferred-text-as-content fabrication

Dispatch v2 (`2026-05-18-1519-...`) §3.2 Part A quoted a "current
bullet at L315" of `docs/lessons/0003-...` that did not exist. Chat
had inferred what an understated `uv run` anti-pattern bullet would
look like, attributed the fabricated text as "verbatim per Code
midflight" (which it was not), and would have replaced a valid unrelated
anti-pattern (`uv run pre-commit install` hook-regen).

**Code surface (midflight `2026-05-18-1528-...` §2):** Cross-checked
v2 dispatch's "current text" quotes against the live file (the very
protocol §4.2 codifies), caught the fabrication, paused again.

**Chat (this thread):** Ratified Option A (additive bullet, no replace);
codified Chat-side prevention discipline in `chat_tab_instructions.md`
(operational layer) per Cray decision (recurrence justified
two-layer enforcement); drafted v3 re-dispatch (this dispatch).

**Result of family 2.2:** Clean three-dispatch chain (v1 paused → v2
paused → v3 to execute) with audit trail through both midflights +
both re-dispatches. Validates the pattern on *both* anchor-mismatch
sub-modes (annotation-confusion + inferred-fabrication). Repeat
offenses informed the dual-layer prevention design (Lesson #5 §3
durable + chat_tab_instructions.md operational).

## 3. When the pattern applies vs alternatives

### Applies when:

- Code discovers scope expansion **mid-execution** or anchor mismatch
  **pre-execution** (both qualify; the key is "Code finds gap that
  affects batch shape")
- The discovery is **off-the-critical-path** of the current batch's
  primary purpose (i.e., resolvable by re-dispatch; not blocking
  external dependencies)
- The expansion or anchor correction is **well-bounded** (Code can
  describe it precisely: N more matches, M missing anchors, specific
  patterns)
- A second dispatch + second commit (or re-dispatch + one commit) is
  acceptable in the audit history

### Does NOT apply when:

- The discovery is a **dispatch-internal contradiction** (two parts of
  the same dispatch contradicting each other), not a
  scope/anchor/external-mismatch — that's Code-judgment-on-contradiction
  path (Lesson #5 §2 sub-rule), not this pattern
- The discovery **invalidates** the current batch (e.g., the entire
  approach is wrong) — that's a stop-and-revert situation, not
  re-dispatch
- The expansion would **bloat** the current commit beyond safe review
  (>~50 lines + non-trivial logic) — that's also a re-dispatch
  candidate, just with stronger gating

## 4. Relationship to other tiers

- **Tier 0 (Cowork):** Cowork brief disputes happen on a different
  cadence (briefs are one-shot research deliverables, not in-flight
  execution). The pattern does not directly apply to Cowork; the
  closest analog is Cowork closeout flagging "out-of-scope-but-noted"
  items for Chat triage.
- **Tier 1 (Chat):** Receives the surface; decides whether to expand
  the current batch (rare) or queue a follow-up batch (common); for
  anchor mismatches, the resolution typically goes into a v2+ re-dispatch
  with corrected anchors.
- **Tier 2 (Code):** Surfaces the discovery; standby until re-dispatch;
  executes the re-dispatched scope.
- **Tier 3 (Cray):** Optional adjudicator if Chat is uncertain about
  scope expansion direction (Session 11 Option-1 choice was Cray-made)
  or anchor-resolution path (Session 12 Option-6-A, Option-A, and
  dual-layer prevention choices were Cray-made).

## 5. Anti-pattern (do NOT do this)

- **Silent scope expansion:** Code execs additional matches not in
  dispatch scope. Audit trail broken; future Chat reviews can't
  distinguish "Chat approved scope" from "Code added scope".
- **Silent scope contraction:** Code skips matches in dispatch scope
  because "they looked unrelated" or because part of the dispatch is
  unexecutable. Same audit-trail break in reverse.
- **Silent anchor relocation:** Code finds the anchor isn't where the
  dispatch says, picks an alternate location, and applies the edit
  there without surfacing. Breaks schema-fidelity (Lesson #5 §3
  sub-rule).
- **Inline re-design:** Code attempts to re-author the dispatch in the
  closeout body, prescribing new scope without going through Chat.
  Bypasses Tier 1 authority.

The safe path is always: **surface → Chat decides → re-dispatch → execute**.

## 6. References

- Closeout (scope expansion source): `.claude/handoffs/session-10/2026-05-16-1204-code-lesson5-apply-batch-closeout.md` §scope-expansion
- Sync (5 findings source): `.claude/handoffs/session-10/2026-05-16-2210-code-chat-sync-transcript-tooling.md` §2.2 finding 5
- Midflight v1 (annotation-as-content source): `.claude/handoffs/session-10/2026-05-18-1450-code-lesson-cleanup-midflight.md` §2
- Midflight v2 (inferred-text-as-content source): `.claude/handoffs/session-10/2026-05-18-1528-code-lesson-cleanup-v2-midflight.md` §2
- Commits: `8274a66` (original scope), `c85a595` (re-dispatched scope), `ec38e2b` (predecessor execute)
- Lesson #5 §2 main rule (Chat designs / Code executes)
- Lesson #5 §2 sub-rule: Code-judgment-on-contradiction path (sibling pattern; 3rd instance covers both v1+v2 midflights)
- Lesson #5 §3 sub-rule: Schema-fidelity discipline (prevention layer; failure modes #4 + #5)
- `docs/conventions/chat_tab_instructions.md` "Chat-side anchor verification protocol" section (operational-layer prevention, codified same batch)
