# Lesson #0061 — an acceptance criterion is not a spec

**Session:** 282 (2026-09-06) · **PRs:** #1415 (built it wrong), #1416 (corrected it)
**Status:** advisory. Nothing enforces this — no guard can tell which paragraph an implementation was read from.

---

## The measurement

PLAN-0122 Step 4 required a decision log for the Stop-hook classifier. I read
**AC-8**, which is where the PLAN says how the log will be *checked*:

> *Pass read:* prints `case=<name> pre=N post=N+1 emitted=<block|demoted|none|suggestion> transport=<ok|timeout|…>`

I built to that. It shipped in #1415 and was **wrong in every name**:

| | §4.3 specifies | #1415 shipped |
|---|---|---|
| path | `.claude/state/stop-classifier-log.jsonl` | `stop-decisions.jsonl` |
| env override | `CLAUDE_STOP_CLASSIFIER_LOG` | `CLAUDE_STOP_DECISION_LOG` |
| field | `decision` | `verdict` |
| fields | `event`, `latency_s`, `prompt_sha8` | absent |
| field | — | an extra `depth` |
| enum | `transport ∈ {ok, timeout, malformed, retry}` | `{ok, fail_closed}` |

**The path alone would have been fatal.** AC-12 re-reads that file after 14 days
and would have found nothing there — discovered on the day the measurement was
due, with the window already spent.

## What makes this failure mode specific

An acceptance criterion is written to be **checkable**, so it names only what a
check can see: the observable behaviour, the values printed, the pass condition.
A design section is written to be **built**, so it names the things a check
cannot see: the path, the env var, the field names, the enum's full domain.

They overlap enough to feel like the same document. AC-8's pass read mentioned
`emitted` and `transport` — two of the nine fields — which is exactly enough
detail to convince a reader they have the spec in hand.

> **The AC tells you how you will be graded. The design section tells you what to
> build. Passing the grade is not the same as building the thing.**

## Why nothing caught it

This is the part worth internalising: **#1415 was not sloppy work.**

- `ruff` clean, `ruff format` clean, `mypy --strict` clean
- **4,939 tests passing**, including 9 new ones written for this feature
- **three probes**, each witnessing a distinct assertion RED, each with a control
  that stayed green — the full CLAUDE.md §8 discipline, honestly applied
- CI green
- an autouse socket guard added after measuring that the suite wrote 25 lines
  into production state

Every gate passed **because every gate checks the thing against itself.** The
tests assert the log does what the implementation intends; the probes prove those
assertions can fail. Nothing in that loop compares the artifact to the paragraph
that commissioned it, and no guard can — "did you read §4.3?" is not a property
of the tree.

## Reading §4.3 fixed a second, deeper error

The correction was not cosmetic renaming. §4.3's enum is
`transport ∈ {ok, timeout, malformed, retry}`, and **`retry` is a success
variant** — the model answered, on the second attempt.

So the boolean I shipped was not a coarse version of the spec. It was a
**different measurement**, one that could never answer the question AC-12 asks.
The spec's four values proved themselves on the first production line after the
fix, which read `transport=malformed` — a third MS-S1 failure shape (HTTP 200
with an empty body) that the boolean would have flattened together with 500s and
timeouts.

**The spec saw something I did not.** That is the ordinary case, not the
exception: it was written by someone thinking about the measurement, with more
context than the implementer has at the keyboard.

## The control that says this is about reading, not about drafters

Prompted to check whether the same miss had hit AC-9, I read **§4.4**. It
specifies the floor test as *"a test recording `demoted=N` on the ledger strings,
so a future edit that starts catching them earns a re-look instead of silent
credit"* — which is exactly what #1415 shipped. **AC-9 conformed.**

Same PLAN, same session, same implementer. The difference was not care or luck:
AC-9's pass read happens to restate its design section closely, so building from
the criterion produced the specified artifact by accident. AC-8's did not.

## How to apply

Before implementing any acceptance criterion:

1. **Find the design section that commissions it.** In a vero-lite PLAN that is
   §4.x; the AC usually names it, and if it does not, grep the PLAN for the
   artifact's path or filename.
2. **Read it in full, not for the fields you already expect.** The parts that
   matter are the ones the AC could not mention — names, paths, domains.
3. **Diff the two before writing code.** If the AC names three fields and §4.x
   names nine, the AC is the smaller document by design and you have just found
   six things you were about to invent.
4. **When they conflict, the design section wins** and the discrepancy is worth
   surfacing — one of them is stale.

When a spec cannot express something the implementation needs, **record the
deviation in the code rather than quietly diverging** (CLAUDE.md §8 — *a case the
system cannot express is registered in writing*). #1416 carries two: a fifth
`transport` value for failures that never left the box, and the note that an HTTP
error lands in `timeout` because the specified enum has no value for *"the server
refused"*.

Related: [`0056`](0056-suspect-the-instrument-before-the-artifact.md) — there the
check disagreed with the artifact and the artifact was right; here the artifact
disagreed with the *specification* and no check could see it at all.
