# Lesson #0065 — the tracked-surface rule stops at gates; the losses did not

**Session:** 312 (2026-09-19), measured · **PRs:** [#1528](https://github.com/CrayJThiemsert/vero-lite/pull/1528)
(story plan rehomed), [#1530](https://github.com/CrayJThiemsert/vero-lite/pull/1530) (R9 rehomed)
· **Status:** advisory (§1 precedence — promote to ADR if it must bind).
**Class:** this is ADR-0038 **C4** territory — *"a rule recorded outside the surface its consumer
scans"* — but the three firings below are **outside the clause C4 actually promoted**. That gap
is the lesson.

---

## The measurement

Three artifacts were lost or nearly lost in one session, by one mechanism, at three very
different ages.

| Artifact | Lived only in | How long unreachable | How it was found |
|---|---|---|---|
| **R9** — Cray's typed ruling that the intro video has no runtime bound | the gitignored storyboard (11 sites) | **71 sessions** (s241 → s312) | only because a *different* task (G7) sent someone to look |
| **Appendix A** — the reviewed story plan: 5 content decisions, 4 gates, a sole-source case, the "forbidden claims" list | one gitignored handoff | 5 sessions, re-copied **by name only** (s306 → s311) | a standing 🔴 on STATUS said so, and nobody acted on it |
| **`.tag-synth`'s open position** | two gitignored handoffs | had **already fallen out of `docs/STATUS.md` entirely** — 0 occurrences — while still being carried as an open item | measured while rehoming Appendix A |

### What the loss cost, where it is measurable

R9 is the one with a price tag. It relaxed R2's ~140-second runtime bound on **2026-08-20**.
Because it was tracked nowhere, `docs/strategy/public/intro-video-production-rulings.md` — a
tracked file, actively maintained — went on reasoning from the voided bound in **three** places.
The sharpest: §5 item 5 recorded that the explainer-vs-runtime conflict *"have to be reconciled
by a later ruling"* — **and that ruling already existed, predating the entry by twenty-six days.**

The file was not careless. It reasoned correctly from everything it could read. **R9 was not in
anything it could read.**

## Why the existing rule did not catch it

`CLAUDE.md` §4 already carries C4's promoted clause (ii):

> *A gate or tripwire — its definition **and** its do-not-act instruction — must live on a
> tracked, scanned surface; a gitignored handoff or an archived PLAN holds the rationale, never
> the gate.*

That rule is right, and it is already binding. **It just does not reach any of the three.**

- R9 is a **ruling** — it permits, it does not gate.
- Appendix A is a **reviewed plan with open decisions**.
- `.tag-synth` is **one open decision**.

None is a gate or a tripwire. The clause was written from the firings that produced it (a gate
definition in an archived PLAN; a rule outside an enforcer's input), and its scope is honest
about that. The three firings here say the *failure mode* is wider than the *artifact kind* the
clause names.

## The rule this suggests

**A decision that has been made, and that something tracked will later reason from, needs a
tracked home — whether or not it gates anything.**

The test is not "is this a gate?" but the one §4 already teaches, applied one step further:
**name the consumer, then check the home is in that consumer's input.** R9's consumer was a
tracked rulings file. Appendix A's consumer was the next session. `.tag-synth`'s consumer was
whoever would next touch the filmed frame. In all three the consumer could not read the home.

**Handoffs are the failure surface, not the fix.** Five sessions carried Appendix A's *names*
forward faithfully and its *content* never travelled. A handoff that names an item proves the
baton was passed; it does not prove anything is still holding it.

### What actually worked

Not a better handoff, and not a better ordering of work — **a tracked file**. The story plan and
R9 both survived this session for one reason: someone wrote them into `docs/logs/` and
`docs/strategy/public/`, where `git grep` reaches them. That is also why this lesson exists as a
file rather than as a paragraph in a closing note.

## Tripwires

- **"It is in the handoff" is not a home.** `.claude/handoffs/` is gitignored working notes. One
  `rm`, one cleared worktree, one session that carries the name without the content.
- **A negative grep is not a finding without a positive control.** The claim "R9 is tracked
  nowhere" was checked with a grep that was *also* shown to find something (`git grep` for a
  string known to exist returned hits, the invented strings returned zero). An uncontrolled grep
  returning nothing proves the grep ran, not that the thing is absent.
- **Age is not the signal.** R9 sat for 71 sessions and cost real reasoning; `.tag-synth` was
  days old and had already fallen out of STATUS. The mechanism does not need time to work.

## Open — not decided here

Whether §4's clause should be widened from *gate/tripwire* to *any made decision a tracked
surface will reason from* is **constitutional**, so it is Cowork-drafted and Cray's to ratify
(ADR-009 D1). ADR-0038 D1 governs whether these firings promote the class further; this lesson
records them and takes no promotion action.

## Reference

- `docs/logs/2026-09-19-s312-story-page-open-decisions.md` — Appendix A, rehomed
- `docs/strategy/public/intro-video-production-rulings.md` §2.2 (R9) and §7 (its provenance and the 71-session gap)
- `docs/adr/0038-...md` §C4 — the class and its promoted clause
- `CLAUDE.md` §4 — the knowledge-placement rule and the consumer test
