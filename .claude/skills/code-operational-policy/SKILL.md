---
name: code-operational-policy
description: Tier 2 (Code) tactical operating policy for vero-lite — when to turn git worktree mode ON vs OFF, how to render a transcript handoff to Chat/Cowork, and the plan-first discipline for costly / host-state / irreversible / multi-step execution (read the result-producing code first, stage a plan, pre-commit the pass/fail read, run once, verify; + the Axis-B /goal habit for verification tasks). Use when deciding worktree isolation, handing off a transcript, OR planning a host-state run / live benchmark / multi-step verification. Other tiers do not need this.
---

# Tier 2 (Code) operational policy

Tactical policy specific to Tier 2 (Code) execution. This is procedure, not a
constitutional rule — it loads on demand. The constitutional pointer lives in
`CLAUDE.md` §11.

## Worktree mode

Default policy per Lesson #3:

| Scenario | Worktree | Rationale |
|----------|----------|-----------|
| Single-task work (ADR draft, doc edit, single commit) | **OFF** | Avoid Family B traps (sandbox ownership cascade); zero isolation benefit |
| Parallel work (multiple branches in flight, risky refactor) | **ON** | Isolation worth the lifecycle cost; apply Lesson #3 prevention checklist |
| Buildable code that should fail-isolated in CI | **ON** | PR boundary clarity; explicit pre-flight required |

Apply the [Lesson #3 prevention checklist](../../../docs/lessons/0003-code-tab-worktree-lifecycle-traps.md#prevention-checklist)
before any worktree-on session.

## Transcript handoff

When the Code tab judges that a reply or span of work should be handed to Chat
or Cowork for follow-up, render the full raw transcript via
`tools/handoffs/render_transcript.py` into `.claude/handoffs/session-NN/`
(gitignored working note) and **always state the export file path in the reply**.

Procedure + options: [`docs/runbooks/transcript-handoff.md`](../../../docs/runbooks/transcript-handoff.md).

## Plan-first for costly / host-state / irreversible / multi-step work

For a task that is **host-state** (warm/run a model on MS-S1, touch global
config — ASK Cray first, CLAUDE.md §8), **irreversible / outward-facing** (a
live run that burns a one-shot authorization, a push/merge), **costly** (a long
benchmark, a paid API run), or **multi-step** (≥ ~3 dependent stages), do NOT
execute blind. Trivial, reversible, single-step work — just do it; this does not
apply. The discipline keeps the run trustworthy *and* cheap (it avoids wasted
host-state runs and false reads):

1. **Read the code that PRODUCES the result before you run it.** For an
   eval/benchmark/verification, read the harness + the scoring + the engine path
   the run exercises. You must be able to say, *before* the run, what each
   outcome will MEAN — pass / known-acceptable-miss (out of scope) / real failure
   — or you cannot tell a regression from noise afterward. This is the
   single highest-leverage step (interpret-before-run, Lesson #0026): it prevents
   both false alarms (an out-of-scope miss read as a regression) and false
   confidence (a lucky or off-route pass read as a validation).
2. **State a staged plan + pre-commit the pass/fail read.** A short stage table
   (cheapest checks first, host-state/irreversible last) + the explicit
   acceptance criteria you will judge against. Checkpoint here if the work is
   governance- or host-state-gated; otherwise proceed.
3. **Run the cheapest gate first.** Offline / mocked gate before any host-state
   or paid run — if the offline gate is red, never spend the live run.
4. **Run once.** Minimize host-state / paid runs (the ASK-Cray host-state gate).
   No iterating on the live target.
5. **Verify with the right tool, against the pre-committed criteria.** Read the
   evidence artifact with the **Read tool** (never piped `cat`/`wc` — it silently
   misreports; verify-relayed / verify-pin lessons). Judge against step 2's
   criteria and report misses honestly: out-of-scope/known vs regression.

### Use the Axis-B `/goal` loop for verification tasks

When the task has explicit acceptance criteria (a verification, a multi-criteria
eval, an AC-N re-verify), declare them up front with **`/goal`** (writes
`.claude/state/goal.json`; ADR-0018 / PLAN-0021). The Stop-hook goal gate then
checks every turn and can dispatch the `goal-evaluator` to adversarially
**REFUTE** — not bless — each `judge` criterion from on-disk evidence. This moves
step 2's pass/fail read from post-hoc prose into machinery and adds a skeptical
second perspective for free. Warn-only v1 (never blocks) → pure upside.

## References

- `CLAUDE.md` §11 (constitutional pointer), §8 (host-state ASK-Cray gate)
- Lesson #3 (worktree lifecycle traps + prevention checklist)
- Lesson #0026 (interpret-before-run: pre-commit what each outcome means)
- ADR-0018 / PLAN-0021 (Axis-B `/goal` verification loop); the `goal` skill
- `docs/runbooks/transcript-handoff.md`; the `ms-s1-ollama` skill (host-state mechanics)
