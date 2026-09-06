# Lesson #0060 — an archive move is three acts, not one; the third is to leave a pointer alone

**Session:** 282 (2026-09-06) · **PRs:** #1412 (the closeout that surfaced it), and the follow-up that shipped the tripwire below
**Status:** advisory. The enforced half is the corpus-registration check in `tools/check_plan_archive_refs.py` and its four tests — a lesson that only lives here would not fire on the next archive.

---

## The measurement

Closing PLAN-0121 needed one command. `git mv` it into `docs/plans/done/`, ledger already
8/8, nothing else outstanding. The offline gate then went **RED** on
`test_the_real_repo_is_clean` with **three** pre-archive references the move had just
killed.

Two were ordinary. The third would have destroyed a number that cannot be re-measured.

## The three acts

**Act 1 — move the file.** The part everyone plans for.

**Act 2 — repair the navigation pointers.** Two of the three: a Recent-Decisions row and a
rotation-ledger glob, both pointing a reader at where the PLAN lives. Re-point them at
`done/`. Mechanical, correct, uninteresting.

**Act 3 — identify the pointers that are DATA, and leave them exactly as written.** The
third hit was inside `benchmarks/stop_classifier/gold_s280.yaml`, in a gold case named
`proceed-closeout-git-mv-after-go`: a **simulated assistant turn** announcing it is about
to `git mv` the PLAN-0121 reference into `done/`.

Re-pointing that one does two things, and the second is the expensive one:

1. It makes the simulated sentence self-contradictory — the turn describes a state
   *before* the move, so the pre-archive path is **correct** in that context.
2. It changes the corpus that the classifier arms were scored on. FULL's held-out 29/30
   was measured against that file as it stands, and PLAN-0122's `J4` was judged on *"no
   arm was re-run after its score was seen"*. So the number cannot be re-established by
   re-running. **The edit is not merely wrong; it is unrecoverable.**

The failure mode is not "I didn't notice the third one". The guard pointed straight at it.
The failure mode is **treating a guard's file list as a to-do list** — running `sed` down
it because the first two were mechanical.

> A guard reports *where* a string is. It cannot report *what the string is doing there.*
> That judgement is never delegable to the tool that found it.

## What made the third one invisible in advance

`EXEMPT_PREFIXES` already carried `benchmarks/stop_classifier/gold.yaml`, exempted for
**exactly this reason**, with a comment naming the twin case (an assistant narrating a
`git mv` of a PLAN-0028 reference). The principle was written down, correctly, and had
been applied once.

`gold_s280.yaml` was split out of that same gold set at s280 — **after** the exemption was
written. It was never refused. It was simply **not thought of**, and the allowlist is
file-scoped, so the guard stayed quiet on it for two sessions until an unrelated `git mv`
tripped over it.

That is the standing cost of a named-file allowlist, and it is worth stating plainly
because the file scope is **still right**: the `RESULTS.md` beside the corpus is genuine
navigation, and a benchmark `RESULTS.md` is precisely where this rot was originally found.
The scope was never the bug. The **absence of a trigger** was.

## The second finding: archiving drops a file out of its guards' scope

Measured across the same move:

```
before:  86 AC(s) across 10 active PLAN(s)   — clean, exit 0
after:   78 AC(s) across  9 active PLAN(s)   — clean, exit 0
```

`tools/check_ac_consistency.py` walks `docs/plans/*.md` and **not** `docs/plans/done/`.
The move is handled gracefully — an archived PLAN drops out rather than erroring on its
`**Batteries:**` glob — but the consequence is that **nothing re-checks that file again,
ever.**

This mattered immediately. The same closeout found the archived PLAN's battery header had
shipped `26 claims … 12 exemptions` where the committed JSON declares `probes: 14` +
`exemptions: 14` = 28. Off by exactly `-2` in both fields, wrong **as committed** — the
JSON and the prose landed in one commit, so the figures were most likely copied from a run
taken before the last two exemptions were added.

Had it been archived without that repair, the wrong numbers would have been permanent.

> **Archiving is not filing. It is removing a file from the set of things anything checks.**
> The moment to read a PLAN most carefully is the moment you are about to archive it —
> which is exactly the moment everyone is most inclined to hurry.

## What shipped, so this fires without anyone remembering it

`corpus_files()` in `tools/check_plan_archive_refs.py` enumerates tracked `*.yaml` carrying
the corpus marker `transcript_turns` and splits them `(registered, unregistered)` against
`EXEMPT_PREFIXES`. The pre-commit hook fails on any unregistered corpus, naming it, at the
commit that **adds** it — not in the unrelated PR that trips over it later.

Three design points worth keeping:

- **Detection is by CONTENT, not filename.** The notes beside that gold set document a
  corpus called `s280-GOLD-fable.yaml`, so a `gold*.yaml` rule would already have a known
  miss.
- **It prints what it measured** — `corpus registered=2 unregistered=0` — never a bare
  verdict, so a disagreement is one step to diagnose (`CLAUDE.md` §8).
- **It fails closed at zero.** An empty `unregistered` list proves nothing if the detector
  matched nothing at all; if the marker key is ever renamed, a content probe silently
  reports a clean tree forever. Both halves are witnessed RED by separate probes, because
  one mutation witnesses one assertion.

## How to apply

When a PLAN is about to be archived:

1. Read it **before** the move, not after — this is its last inspection by anything.
2. `git mv`, then run the R8 guard and treat its output as a **classification task**, not a
   fix list. For each hit ask: *is this string telling a reader where to go, or is it
   content that something consumes?*
3. Navigation → re-point at `done/`. Content → exempt it, file-scoped, **with the reason
   written down**, and register it in the same change that created it.
4. If a hit is inside anything a benchmark, gold set, fixture, or scored corpus reads:
   **stop.** Establish what measurement depends on those bytes before touching them.

Related: [`0056`](0056-suspect-the-instrument-before-the-artifact.md) (the check and the
artifact disagreeing — here the check was right and the *response* to it was the hazard),
and [`0058`](0058-an-assertion-that-moves-with-the-mutation-has-no-witness.md).
