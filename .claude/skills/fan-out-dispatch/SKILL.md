---
name: fan-out-dispatch
description: Split work across parallel sessions/agents safely, and close the loop when they return — run the write-set disjointness check BEFORE spawning, keep shared writes with the dispatcher, avoid the append-to-tail / shared-enumerating-list conflict shapes, and COUNT the returns against the dispatches before synthesising anything from them. Use whenever about to call spawn_task more than once for related work, fan work out to several sessions or subagents, split a backlog into parallel chips, decide whether work is parallel-safe at all, OR write a ranking / summary / recommendation that aggregates results from more than one agent. Encodes Lesson #0031 (3 wasted merge commits + a policy clause authored twice, s141-142) and Lesson #0046 (a synthesis cited five agents when four had returned, s241).
---

# Fan-out dispatch — split on the write-set, not on the idea

Task-triggered procedure for the **dispatcher** (the session that hands work out). Full
rationale + the measured incident: [`docs/lessons/0031-fan-out-on-the-write-set-not-the-idea.md`](../../../docs/lessons/0031-fan-out-on-the-write-set-not-the-idea.md).

## The one rule

> **Shared writes never enter the fan-out. The dispatcher owns them.**

Parallelism pays only when tasks are disjoint in **what they WRITE**. Disjoint *ideas* mean
nothing — three tasks can reason about three unrelated things and still all append to the
same file.

## 🔴 Tripwire — check this first

If you are writing, or about to write, any of these into a dispatch summary:

- *"the merges must be serial"* / *"ห้ามขนาน"*
- *"expect conflicts"* / *"conflict แทบแน่นอน"*
- *"whoever lands first wins; the rest need `update-branch`"*
- *"I'll resolve the conflicts after"*

**STOP. That is not a caveat for the user — it is a bug report about your own split.**
This exact text was written in s141, the tasks were spawned anyway, and it cost 3 merge
commits. Go back to step 3 below and move the shared write out.

## The check (before the FIRST `spawn_task`, not after the last)

1. **Write down each task's write-set** — actual files and sections, not topics.
   *Topic-disjoint is not write-disjoint.* Example that fooled a prior session:

   | task | thinks about | writes |
   |---|---|---|
   | A | ADR-0025 | STATUS + archive tail + carve-out clause |
   | B | PLAN-0035 | STATUS + archive tail + carve-out clause |
   | C | guard docstring | STATUS + archive tail + carve-out clause |

   Maximally independent ideas. Identical write-sets. Guaranteed collision.

2. **Intersect the sets.** Any file in ≥2 sets is a **defect in the split**, not a
   coordination problem to manage with warnings.

3. **Cut at the seam.** Fan out only the disjoint remainder; the intersection becomes ONE
   follow-up step the dispatcher does after the chips land:

   ```
   FAN OUT   chip A → file-set A only
             chip B → file-set B only
             chip C → file-set C only        ← merge in any order, no conflicts

   CENTRAL   dispatcher, once, after they land:
             all the shared bookkeeping      → 1 PR
   ```

   Usually the same PR count, zero conflict tax. If the disjoint remainder is **empty**,
   the work was never parallel — do it in one session.

4. **Put the write-set IN each prompt.** State the allowed files explicitly and tell the
   session to **stop and report** if it finds it must write outside them. A spawned session
   cannot see its siblings; it learns about them from a merge conflict unless you tell it.

5. **`log`/report what you centralized**, so the user sees the shape — not just N chips.

## Conflict shapes to hunt for (all four are dispatcher-authored, not accidents)

- **Append-to-tail** — archives, changelogs, `status-archive/`, logs. N branches appending
  at EOF all edit the same position. The worst shape there is.
- **A sentence/list that enumerates the fan-out** — e.g. a policy clause naming all three
  items, where each task's last act is deleting its own name. *An enumerating list is a
  shared mutable variable.* If you wrote that list for a single session, it becomes a
  contention point the moment you split.
- **One status/index file every task must tick** — `docs/STATUS.md`, a README table, a
  tracking PLAN's AC checkboxes.
- **A shared counter/total** — a `total == N` pin, a count comment, a "N of M done" line.

## The economics (why "just resolve the conflicts" is the wrong answer)

`main` is protected with `{"contexts":["gate"],"strict":true}` — a branch that is BEHIND
**cannot merge**. So N parallel branches on a shared file merge **serially anyway**:

- 1st PR: free.
- Each later PR: `gh api --method PUT repos/CrayJThiemsert/vero-lite/pulls/<N>/update-branch`
  (`gh pr update-branch` does not exist in this `gh` version) → wait ~3 min for the gate →
  merge. If the shared region truly conflicts, `update-branch` **fails** and needs a manual
  merge.

You pay N sessions of tokens and get serial wall-clock. Never `--admin`.

## Two fixes the s142 siblings added (they lived the collision; adopt both)

**1. `gh pr list --state open` — at session start AND again immediately before merging.**
The cheapest habit there is, and it would have caught this batch. The Rock-4 session
reported: *"I skipped it, merged first, and broke two green PRs. Finding a sibling PR
early is trivial; finding it after your merge is three merge commits of rework."* Sessions
started ~7 hours apart worked the same program unaware of each other. A spawned session
cannot see its siblings — but it CAN see their PRs.

**2. Fix the SURFACE, not the schedule.** Serialising a batch treats the symptom once;
removing the shared surface removes it for every future batch. The archive-tail collision
here is a property of R4's *one flat archive file* design — *"N branches tail-appending to
ONE flat file conflict 100% of the time … not fixable by better session behaviour."* When
you spot a structurally collision-prone surface, prefer fixing it (split the file, give
each task its own section/file, make the append idempotent) over scheduling around it
forever.

**And the shape a merge tool cannot save you from:** two sessions independently wrote
**near-duplicate paragraphs stating the same rule** with different examples. Git will
happily take either side — or both — leaving the doc stating one rule twice. **A textual
merge cannot detect a semantic duplicate.** If two chips could both plausibly author the
same policy/prose, that is not a merge risk; it is the same "shared write" defect wearing
a disguise. Only one task writes the rule.

## When fanning out IS right

Real disjointness, verified — not assumed:

- **Read-only fan-out** is always safe: `Explore` agents grounding claims, research sweeps,
  independent verification. No write-set at all. (This is what `next-work-analyst` does.)
- **Per-file / per-vertical work** where each task owns its own files end-to-end.
- **Worktree isolation** (`isolation: "worktree"`) prevents *tree* collisions — it does
  **not** prevent *merge* collisions. Two worktrees editing one file still conflict at the
  PR. Isolation is not coordination.

## Before you spawn, say this out loud

> *"Task A writes ___. Task B writes ___. The intersection is ___, and I am doing that part
> myself, after they land."*

If you cannot fill in the last clause, do not spawn yet.

## 🔴 After they return — COUNT before you synthesise

**Measured s241: five grounding agents were dispatched, four returned, and the synthesis
was written as if it had five.** The fifth failed silently; its completion notice arrived
long after. Two rows of a ranked recommendation to Cray were written **with no source** and
had to be retracted once measured.

The rule *"verify a subagent delivered"* already existed in memory and did **not** fire —
because it had no **moment of application**. This is that moment:

> **Before writing anything that aggregates subagent results — a ranking, a summary, a
> table, a recommendation — list the agents you dispatched and tick off each one's return.**

- **Four-of-five is not five.** A missing return does not announce itself; you notice the
  notifications you got, never the one you did not.
- **Do not fill a gap from expectation.** If an agent's scope is uncited, the honest output
  is *"not grounded — agent did not return"*, not a plausible sentence.
- **Read the tick-list out loud in the reply** when the fan-out is load-bearing, so a wrong
  count is visible to Cray and not only to you.
- A background agent that dies leaves the harness silent, not red. Silence is not a pass —
  the same shape as [`docs/lessons/0007`](../../../docs/lessons/0007-harness-exit-code-artifact.md)'s
  fabricated exit code, one layer up.

Full incident + the four siblings it travelled with:
[`docs/lessons/0046-when-a-check-and-a-claim-disagree-go-to-the-artifact.md`](../../../docs/lessons/0046-when-a-check-and-a-claim-disagree-go-to-the-artifact.md).
