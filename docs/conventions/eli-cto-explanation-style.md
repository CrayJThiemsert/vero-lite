# ELI-CTO / ELI-Cray Explanation Style

> How Code explains work back to Cray. ELI-CTO is the default *tone*;
> ELI-Cray is the structured *deep-dive format* pulled on demand via `/eli-cray`.

---

## TL;DR — the distinction

These are not two competing styles. They sit at different levels:

- **ELI-CTO** = the **tone / altitude** of *every* conversational reply.
- **ELI-Cray** = a **fixed 4-part format** that operationalizes ELI-CTO when
  narrating a *specific work batch* that just finished. The `/eli-cray` command
  literally defines itself as "explain in ELI-CTO style", so ELI-Cray is just
  ELI-CTO in its full, structured form.

## ELI-CTO — the tone (default, always on)

A communication principle, not a fixed template. Every conversational reply
(status updates, recommendations, checkpoints, explanations) should be:

- **Decision / strategic altitude** — not line-by-line code detail unless asked.
- **Technically literate** — assume a reader who reads engineering fluently.
- **Lead with a recommendation** — give the call first, then the justification.
- **Terse by default** — short; let Cray pull more via `/eli-cray`.
- **Thai conversational language**, with code / paths / SHAs / ADR-PLAN numbers /
  tool names / PR# kept in English (per `user_prefers_thai`).

## ELI-Cray — the structured deep-dive format

The full expansion of ELI-CTO, used when narrating a batch of work. Four parts,
in order:

1. **Why** — why the task was needed; the problem or goal (decision-level, 1–3
   sentences — not code-level).
2. **Steps** — what was actually done, in real execution order; each step short.
3. **Expected per step** — what each step was expected to produce and whether it
   matched — **explicitly flag surprises, mid-course corrections, and anything
   not yet verified or still assumed.**
4. **Net result** — current status + what remains + who acts next.

### When it appears

- **Offered (Code's initiative):** after finishing a batch, *when cheap* — it is
  mostly reframing the summary you'd write anyway into why/steps/expected form.
  Keep it tight, not a wall of text.
- **Deferred to terse:** if the narration would bloat the primary task's context
  budget, reply in normal terse style and let Cray pull it on demand.
- **Pulled (Cray's initiative):** `/eli-cray` is the canonical trigger
  (user-level slash command at `~/.claude/commands/eli-cray.md`). Takes an
  optional focus arg, e.g. `/eli-cray PR #76`, to scope to one topic; empty =
  cover the whole last batch.

### Rules

- **Be direct** — if something was missed, skipped, not verified, or is still a
  hypothesis, say so plainly; never paper over it.
- **Cite real evidence** — if the batch produced numbers (live evidence, test
  results), quote the actual figures, not vague summaries.
- Output in Thai per the tone rules above.

## When to use which

| | ELI-CTO | ELI-Cray |
|---|---|---|
| **What it is** | tone / altitude | fixed 4-part format |
| **Scope** | every reply | narrating one finished batch |
| **Trigger** | always (default) | `/eli-cray`, or Code offers when cheap |
| **Length** | short | longer, structured |
| **Mnemonic** | how I talk | how I walk you through what I did |

Quick rule: want a recommendation or short update → ELI-CTO is already the
default. Want to follow a batch step-by-step or audit what diverged from
expectation → pull `/eli-cray`.

## Sources / related

- `~/.claude/commands/eli-cray.md` — the slash-command definition (4-part format,
  in Thai).
- Auto Memory (Tier 0, private): `eli-cray-explanation-style`, `user-prefers-thai`
  — the private-tier origin of this convention; this file is the shared canonical.
- `CLAUDE.md` §6 (Token Economy / Working Patterns) — broader communication norms.
