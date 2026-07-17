# Lesson #23: STATUS.md bloat — an always-read Tier-1 file needs a size budget + a rotation rule, or it silently becomes an unreadable archive

> **Status:** Codified 2026-06-10 (Session 51, Cray-ratified). Cowork-authored per the session-51 Code dispatch (`2026-06-10-0946-code-status-rotation-policy-dispatch.md`); Code reviews + commits per ADR-009 D2/D3. Canonical rule: `docs/runbooks/memory-architecture.md` §"STATUS.md Rotation Policy" (drafted alongside this lesson).
> **Severity:** High (silent-until-total — the file degraded gradually with zero errors, then crossed the Read-tool limits and the `status-scribe` subagent looped on failed Reads; by the time anything failed, the Tier-1 file was already unreadable in full).
> **Cross-references:** `CLAUDE.md` §4 (Tier 1 = hot context, "volatile state"; Tier 3 = archeology); `docs/runbooks/memory-architecture.md` (Tier model + the rotation policy this lesson motivates); `.claude/agents/status-scribe.md` (the agent whose retention rule encoded the failure); `docs/runbooks/claude-code-chat-handoff.md` §6 (sibling precedent: the handoff rotation policy, same bounded-active-scope rationale); [[lesson-0021-l1-loop-detect-subagent-and-doc-threshold]] + [[lesson-0012-loop-detect-l1-vs-governance-doc-fillup-passes]] (sibling loop-detect lessons — the scribe's failed-Read loop is exactly the repeated-action class the L-rows watch); PR [#243](https://github.com/CrayJThiemsert/vero-lite/pull/243) (`2dac21e`, the acute de-bloat).

## 1. The incident (measured)

`docs/STATUS.md` — the Tier-1 *"read every session"* volatile-state file — grew to
**393 KB / 3,526 lines / >25k tokens**, exceeding the Read tool's **256 KB byte**
AND **25k token** whole-file limits. Worse, the `current_batch:` frontmatter field
was a **single 48,133-character line** (~12k tokens), with `next_action:` at
12.7 KB and `blocked_on:` at 6.1 KB. The `status-scribe` subagent, whose contract
says "Read `docs/STATUS.md` first", **looped on failed Reads** — the session-51 T4
reconcile burned ~72.8k tokens / ~11 minutes before the loop was caught.

A file whose constitutional role is *current state* had become a 393 KB archive —
the exact opposite of its Tier-1 design (CLAUDE.md §4: volatile state in STATUS;
archeology in `docs/plans/done/` + git history, Tier 3).

## 2. Root cause — a retention rule with no counterweight

The bloat was not accidental sloppiness; it was **written into the agent**:

1. **Append-only frontmatter.** `status-scribe` *prepended* each session's summary
   into `current_batch` / `next_action` / `blocked_on` and kept all prior text
   behind `Prior:` chains — three fields that should each be one line became
   nested narrative archives (48 KB in one YAML scalar).
2. **"Never delete history."** The agent's narrative discipline (rule 5) said
   *"Retain prior session blocks for archeology — never delete history"*, and its
   adversarial-hardening list treated *deleting prior session blocks* as an
   injection signature. Every reconcile prepended a block; **31** Current Focus
   blocks accumulated. Nothing ever pruned.
3. **Unbounded tables.** The Recent Decisions table grew to ~287 rows under a
   header that literally said *"(last 5)"* — the cap existed in prose, with no
   enforcement and no owner.

Each rule was individually reasonable ("don't lose history", "record every
decision"). The failure is structural: **a retention rule without a paired size
budget + rotation rule makes growth monotonic.** "Retain for archeology" is a
Tier-3 job; encoding it into a Tier-1 file's writer guarantees the Tier-1 file
eventually stops being readable — which is the one property a Tier-1 file must
keep.

## 3. Failure mechanics — why it failed the way it did

- **Two independent Read ceilings.** The Read tool enforces ~256 KB bytes AND
  ~25k tokens **whole-file**; STATUS crossed both. Windowed reads (offset/limit)
  also degrade on a bloated file: large windows fail outright (see §4).
- **The single-long-line trap (the acute killer).** A 48 KB one-line YAML scalar
  cannot be windowed around: any Read window that includes the line includes all
  48 KB of it; shrinking `limit` never helps because `limit` counts *lines*. One
  pathological line defeats the offset/limit mechanism entirely.
- **The loop.** `status-scribe` is contract-bound to read STATUS before editing,
  has no Bash (cannot `stat`/`head` its way around the tool), and had no
  instruction for the read-fails case → repeated failed whole-file Reads. A
  subagent + a degraded input + no fallback path = the classic L1-class loop
  ([[lesson-0021-l1-loop-detect-subagent-and-doc-threshold]]).

## 4. The ceiling is tokens, not bytes — and 100 KB is already too high

Empirical follow-up while drafting this lesson (Cowork, 2026-06-10, **after** the
acute de-bloat): at **83 KB** the slimmed STATUS **still fails whole-file Read** —
the tool reports **25,447 tokens > 25,000**. A 170-line window Read also failed;
a 45-line window succeeded. Measured density: **~3.3 bytes/token** for this
file's link- and identifier-dense prose.

Consequences for any cap:

- The **binding limit is the 25k-token cap**, hit at ~83 KB — far below the
  256 KB byte limit. A "≤ ~100 KB" budget (the dispatch's initial suggestion)
  would still be **~30k tokens — unreadable in full**.
- A safe hard ceiling must leave headroom under 25k tokens: **64 KB ≈ ~19.6k
  tokens** at measured density (~78% of the cap). That is the figure the
  rotation policy adopts (R1), with a 48 KB soft target.
- Bytes are the right *enforcement* unit (deterministic, `stat`-checkable,
  pre-commit-friendly) even though tokens are the binding *limit* — the byte
  figure simply encodes the token budget via measured density with margin.

## 5. The general principle

**Every always-read file needs an explicit size budget and a rotation rule with
an owner.** Without both, growth is monotonic and the failure is silent until
total. The repo already practices this discipline elsewhere — it just had never
been applied to STATUS:

- `.claude/handoffs/` rotates per session (handoff rotation policy, runbook §6:
  bounded active scope / archive preserves history).
- `CLAUDE.md` (the other Tier-1 member) was deliberately slimmed by extracting
  how-to into on-demand skills (PR #234 / ADR-0017) — same principle from the
  other direction: keep the always-loaded artifact small, move detail to
  on-demand homes.
- STATUS now gets the same treatment: a hard byte ceiling, a rolling window,
  terse frontmatter, move-don't-delete archiving (`docs/status-archive/`), and
  per-reconcile pruning. Canonical spec: the runbook's "STATUS.md Rotation
  Policy" section (R1–R6).

Corollary for agent authors: when a writer agent's contract contains a retention
rule ("never delete X"), pair it **in the same contract** with the budget that
bounds it ("…within the rolling window; older X rotates to the archive").
Otherwise the agent will faithfully execute its way into this incident.

## 6. Detecting recurrence early (don't wait for the loop)

- **Pre-commit size guard** on `docs/STATUS.md` (fail at >64 KB) — deterministic,
  catches the creep at the commit boundary, immune to agent drift (Code scopes;
  policy R1).
- **`status-scribe` structural self-check** — block/row counts are Grep-countable
  even without Bash; the scribe reports counts + prunes every reconcile (R2/R6).
- **Surgical-read discipline** — the scribe never whole-file Reads STATUS again
  (R5); a future degradation therefore cannot re-trigger the failed-Read loop
  even if the guards are bypassed.

## 7. Related artifacts

- `docs/runbooks/memory-architecture.md` §"STATUS.md Rotation Policy" — the
  canonical rule (R1–R6) this lesson motivates; placement per the ADR-0017 D5
  knowledge-placement rule (durable learning → this lesson; canonical
  operational rule → the runbook that owns the Tier model).
- `docs/status-archive/2026-h1-current-focus.md` — the first rotation artifact,
  created by the acute fix (#243), path ratified by policy R4. _[Two corrections,
  2026-07-17: it is now the base of a **chain** (`-b`/`-c` continuations) after
  the session-144 R4 split, so grep the archive directory rather than this
  filename; and "sessions ≤46" was never quite true — later deep-rotates appended
  sessions 116–128 to it.]_
- `.claude/agents/status-scribe.md` — carries the superseded rule 5 wording this
  lesson corrects; Code hardens per the dispatch follow-on (terse frontmatter,
  prune-to-window, surgical reads).
- PR [#243](https://github.com/CrayJThiemsert/vero-lite/pull/243) (`2dac21e`) —
  acute de-bloat mechanics (393 KB → 83 KB).

---

*Drafted by Cowork (session 51) under ADR-009 D1 / ADR-013 OQ-1 advisory
authority, from the session-51 Code dispatch. Author≠reviewer disclosure
(ADR-012 D4.3): the policy decisions summarized here were deliberated and
authored in the same Cowork session; Code's R2 review + Cray's ratification are
the independent checks. AI-assisted; no `Co-Authored-By` per CLAUDE.md §7.*
