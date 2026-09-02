# Lesson #0057 — a perfect correlation is not a cause; ask when it changed

**Session:** 270 (2026-09-02) · **Subject:** three subagents vanished from the harness
registry (`goal-evaluator`, `plan-drafter`, `status-scribe`)
**Status:** advisory. Carries one **do-not-act** instruction (§4), homed here because a
gitignored handoff is not a surface anyone greps.

---

## The situation

Since session 269, three of the four project subagents defined in `.claude/agents/` stop
being offered by the harness. `explore-research` — same directory, same last-touching
commit — keeps loading fine. The s269 handoff recorded it honestly as *"the cause is
unknown"* and told the next session to re-check rather than assume.

Session 270 re-checked, found **four** hypotheses that each fit the evidence **perfectly**,
and every one of them was wrong.

## The four dead hypotheses, and why each looked so good

The four files split 1-registered / 3-missing. With n=4, a great many properties split the
same way. Each of these was a clean 4/4:

| # | Hypothesis | Why it looked right | What killed it |
|---|---|---|---|
| 1 | **exec bit stripped** — the known WSL-UNC hazard in this repo | the session opened with `tools/notify/*.sh` showing pure `100755 → 100644` mode drift, so the hazard was demonstrably live; all three declared hook scripts are `100644` | `stop_continuation.py` is **also** `100644` and was firing the goal gate all session. A control on a known-working instance |
| 2 | **`hooks:` in the frontmatter** — present on exactly the 3 missing, absent from the 1 present | a genuinely clean 4/4 split, and the only frontmatter key that splits that way (`effort` covers just 1 of 3) | `git log -S` dates the blocks to **2026-05-26 / 06-03 / 06-10**. They worked for three months |
| 3 | **`command:` lacks the `python` prefix** that `settings.json` uses on every hook | a real inconsistency, and a plausible load-time validation failure | same dates. It has always been written that way |
| 4 | **`Write`/`Edit` in `tools:`** — declared by all 3 missing, by neither the 1 present | fits 4/4, and a plausible policy tightening | `statusline-setup` (Tools: Read, **Edit**) and `general-purpose` (Tools: `*`) **are registered** in the same session |

A fifth, file size, also splits 4/4 (5,245 B present; 9,319 / 9,525 / 14,661 B missing) and
is equally irrelevant — see below.

## What actually settled it

Not a better correlation. **A question about time:**

> *When did this property last change?*

- `.claude/agents/` last changed at **`8114e5e`, 2026-09-01 14:42** (session 267).
- `.claude/settings.json` last changed **2026-08-29**.
- Commit **`9cffe2c`** (session 269, **2026-09-02**) says in its own body:
  *"Authored by the in-harness status-scribe subagent (ADR-013 D1)"*.

That last line is **tracked evidence in git**, not a handoff claim: `status-scribe` ran
successfully on 2026-09-02, *after* the last modification to its own definition file.

**Therefore the files are byte-identical to when they last worked.** No property of any
file — hooks block, tool list, command spelling, size — can explain a change, because
none of them changed. The variable that moved is in the **client/harness runtime**,
outside the repository.

## The generalisable lesson

**A hypothesis has to explain the CHANGE, not just fit the split.** A static property
cannot cause a transition. Before ranking correlations, ask the cheap question — *when did
each candidate last change?* — and discard everything that predates the last known-good
observation. Here that one question killed four hypotheses that no amount of further
correlation-hunting would have separated.

The corollary is about **n**: with four items, dozens of properties split 1/3. Correlation
strength is nearly worthless at that scale; **timeline evidence is not**, because it is a
different kind of evidence rather than more of the same. (Lesson
[#0053](0053-two-sessions-agreeing-through-one-instrument-is-one-measurement.md) is the
same shape from the other side — more agreement through one instrument is still one
measurement.)

## 🔴 Do not "fix" the agent definition files

**Binding for whoever meets this next:** do **not** edit `.claude/agents/*.md` to restore
the three subagents — not the `hooks:` block, not the `command:` spelling, not the tool
lists. Those files are proven not to be the cause. Editing them would change something
already exonerated, discard this diagnosis, and risk breaking the one agent that still
works. Nothing is deleted; all four files are present and tracked.

## The test procedure, in cost order

1. **Restart the Claude Code session.** The agent registry is built at session start, so a
   restart is both the cheapest diagnostic and the most likely fix. If the three return, it
   was session-scoped and the case closes.
2. If they are still missing after a restart, the cause is a **client change**, not a
   glitch — check whether the client updated around 2026-09-01/02.
3. Only if a client change is *confirmed* to have dropped support for something these three
   declare does editing the files become correct — and that edit then needs its own
   evidence, recorded here.

## While they are missing — what still works

- **`plan-drafter` absent** → a *new* PLAN or ADR cannot be drafted in-harness. Editing an
  **existing Draft** PLAN is not G2-gated and needs no drafter.
- **`status-scribe` absent** → Code writes the STATUS reconcile directly. Do not recreate
  the agent file.
- **`goal-evaluator` absent** → a `/goal` with `judge` criteria can never close; the Stop
  gate re-dispatches every turn into a hole. Declare goals with **`check` criteria only**
  until the evaluator is back, or expect the dispatch loop. Never self-judge a `judge`
  criterion: ADR-0018 D6 exists precisely so the evaluator disregards the author's own
  prose success-claims, and writing your own verdict makes the mechanism decorative.

## References

- `CLAUDE.md` §4 (a do-not-act instruction must live on a tracked, scanned surface),
  §6 (an inherited premise a decision rests on is a claim, not context).
- `docs/adr/0018-axis-b-verification-loop.md` D6 — why the evaluator's independence is the
  whole mechanism.
- Session-269 handoff §7 recorded the disappearance and the "check before assuming"
  instruction that made this diagnosis happen at all.
