# Lesson #0031 — Fan out on the WRITE-SET, not on the idea; the dispatcher owns every shared write

**Date:** 2026-07-17 (sessions 141 → 142)
**Class:** advisory (parallel-work dispatch hygiene / spawn_task design)
**Trigger:** Code (s141) finished a STATUS terseness pass and surfaced three genuinely
independent follow-ups — rehome the s74 demo-card decision, rehome Rock-4's
evidence-asymmetry finding, rehome the `sequence`-column deferral. Each targeted a
*different* artifact (`PLAN-0035` / `ADR-0025` / a guard-test docstring), so Code judged
them parallel-safe and spawned all three as `spawn_task` chips. Cray started all three.
They collided.

## What it cost (measured on `main`, not asserted)

Three extra merge commits, each one pure collision tax:

- `157c650` — *"Merge main into docs/status-sequence-deferral-rehome — **resolve the
  archive-tail collision** with #780"*
- `255ba06` — *"Merge main into docs/s74-demo-card-rehome-plan0035 — **consolidate the
  duplicate carve-out clause** with #780"*
- `59a4937` — a second `origin/main` sync into the same branch

Plus: the runbook carve-out clause was **authored twice by two sessions** and one copy
thrown away; and because branch protection is `strict: true`, PRs #778 and #779 each had
to re-sync and re-run the ~3-minute gate before they could merge. The first PR to land
(#780) paid nothing; every later one paid.

**No work was lost and nothing shipped broken** (suite 2822/7, all three rehomes landed,
one of them better than specified). The cost was entirely *avoidable rework and tokens* —
which is exactly the class of cost that is invisible unless someone measures it.

## The lesson

**Parallelism pays only when the tasks are disjoint in what they WRITE. Being disjoint in
what they THINK about is irrelevant.**

The three tasks were maximally independent as *ideas* — three different findings, three
different destinations, no shared reasoning. Code looked at that axis, saw no overlap, and
concluded "parallel-safe". But the write-sets were **identical**:

| task | thinks about | writes |
|------|--------------|--------|
| A | ADR-0025 | `STATUS` + archive tail + the carve-out clause |
| B | PLAN-0035 + ADR-0030 | `STATUS` + archive tail + the carve-out clause |
| C | a guard docstring | `STATUS` + archive tail + the carve-out clause |

The interesting axis (the idea) is the one that grabs attention. The boring axis (the
write-set) is the one that decides whether fanning out is cheaper or more expensive. Look
at the boring one.

### Two shared-write shapes that guarantee a conflict

Both were **designed in by the dispatcher**, not discovered:

1. **Append-to-tail.** Every prompt ended with the same sentence: *"archiving the original
   to `docs/status-archive/2026-h1-status.md`"*. N branches appending at the end of one
   file all add lines at the same position — the single most conflict-prone edit shape
   there is.
2. **A sentence that enumerates the fan-out.** The R2 carve-out clause (written in s141)
   *named all three items in one sentence*, so each task's natural last act was to delete
   its own name from that sentence — three sessions editing one line. The clause was good
   design for a single session and became a contention point the instant the work was
   split. **An enumerating list is a shared mutable variable.**

### The seam

The rehomes themselves parallelize perfectly — `ADR-0025`, `PLAN-0035`+`ADR-0030`, and the
guard docstring are three disjoint files. The bookkeeping (trim the TODO, archive the
original, release the carve-out) is inherently shared. **Split there:**

```
FAN OUT   — disjoint write-sets, merge in any order, no conflicts:
  chip A → ADR-0025 only
  chip B → PLAN-0035 + ADR-0030 only
  chip C → guard docstring + runs.py + persistence.py only

CENTRAL   — the dispatcher does this ONCE, after they land:
  trim the 3 TODOs + archive the 3 originals + release the carve-out   → 1 PR
```

Same four PRs. Zero conflict merges. The clause authored once. **The correct split was not
more expensive — it was strictly cheaper, and it was available from the start.**

> **The rule:** *shared writes never enter the fan-out. The dispatcher owns them.*

## The sharpest part: the collision was predicted and shipped anyway

Before Cray started the tasks, Code wrote — unprompted:

> *"archive — ทั้ง 3 append ท้ายไฟล์เดียวกัน → conflict แทบแน่นอน … **merge ต้องเรียงทีละอัน
> ห้ามขนาน**"*

The analysis was complete and correct. Code then treated it as a **cost to warn about**
rather than **evidence of a bad split**, because the prompts were already written. The
failure was not ignorance. It was accepting a self-diagnosed design flaw as a fact of life.

> **Tripwire (greppable):** if you are drafting a warning that says *"the merges must be
> serial"* / *"expect conflicts"* / *"whoever lands first wins"* — **stop**. That is not a
> caveat to pass to the user; it is a bug report about your own split. Go back and move the
> shared write out of the fan-out.

## Why `strict: true` makes this worse than it looks

`main` requires branches to be up to date (`{"contexts":["gate"],"strict":true}`). So N
parallel branches touching one file do not merge in parallel *at all*: each later PR must
sync and re-run the full gate. You pay N sessions' worth of tokens and get serial
wall-clock — the worst of both. (The upside of `strict` is real and unrelated: it closes
the "CI is PR-only, the merge commit is never tested" hazard.)

## How to apply

Before calling `spawn_task` more than once for related work:

1. **List each task's write-set** — the actual files/sections, not the topic.
2. **Intersect them.** Any file in ≥2 sets is a defect in the split, not a coordination
   problem to manage.
3. **Move the intersection to the dispatcher** as a single follow-up step. If what remains
   per task is empty, the work was never parallel — do it in one session.
4. **Look specifically for:** append-to-tail (archives, changelogs, logs), a shared list
   that enumerates the tasks, one status/index file every task must tick, a shared counter
   or total.
5. **State the write-set in each dispatch prompt** so the spawned session can refuse if it
   discovers it needs to write outside it.

The dispatcher's job is not just to describe N tasks. It is to **own the seam between
them** — nobody else can see it. A spawned session sees only its own prompt; it learns
about its siblings from a merge conflict.

Related: `.claude/skills/fan-out-dispatch/` (the at-the-moment-of-need procedure this
lesson backs), Lesson #0030 (verify the fact-pack before dispatching — the drafter/chip
trusts what you hand it), `docs/runbooks/memory-architecture.md` R2/R4 (the carve-out
clause and the archive tail that collided here).
