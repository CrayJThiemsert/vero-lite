# Lesson #0056 — suspect the instrument before the artifact

**Session:** 269 (2026-09-02) · **PRs:** #1356 (STATUS reconcile), #1357 (PLAN-0118 Step 3)
**Status:** advisory. The binding half is the widened clause in `CLAUDE.md` §8 Code Quality.

---

## The measurement

In one session a check disagreed with the artifact **seven times**. The artifact was
right **seven times**. Not once was the code or the data the defect.

That ratio is the lesson. It is not an argument for checking less — three of the seven
were caught *only because* a check ran, and two of those would have shipped a real
defect. It is an argument about **where to look first when a check goes red**.

## The seven, and what each would have cost

| # | The check said | The artifact said | Cost if unnoticed |
|---|---|---|---|
| 1 | the s263 ledger entry is absent from the archive, so append it | it was already archived **whole and PRE-PRUNE** at s267 | 🔴 a duplicate written into a move-only archive |
| 2 | archive delta must equal `len(appended)` | delta was `len(appended) − 1` | a false FAIL that **invites relaxing the criterion** |
| 3 | `"No byte delta measured"` should be gone | the **retained s267 entry** carries the same phrase, and the runbook forbids rewriting a retained entry | a false FAIL |
| 4 | `rm-02`'s description holds one number | it holds three — the regex's trailing lookahead rejected any number ending a sentence | 🔴 **AC-1(d) authored from a wrong figure → a control dead on arrival** |
| 5 | `injected_value` is a float | the band has three shapes: `9999.0`, `"hacked_namespace"`, `"below"` | 🔴 **two of three injection cases silently mis-scored** |
| 6 | `"Clean bags sit around 0.6"` is new | it is the case's **own description text** — the source the new declaration points *at* | a false FAIL |
| 7 | `same_unit_distractors` is absent from STATUS (a "positive control") | the STATUS row **names the field on purpose** to explain the rehome | a control that proved nothing |

## Four classes, and only two are dangerous

**A — the instrument was never tested itself** (#4, #7).
A regex with no control, and a "positive control" whose needle was legitimately
present. Both report a confident wrong answer and make **no noise**. #4 is the
expensive one: the figure would have gone straight into an acceptance criterion.

**D — a single instance generalised to a set** (#1, #5).
One ledger rotation read as the pattern for all of them; one injection case read as
the shape of the band. Code written this way works **perfectly on the instance you
read** and fails silently on the rest.

**B — the expectation came from intent, not from the artifact** (#3, #6).
Both are token-selection errors: a token chosen from what the change *means* rather
than from what the diff *adds*.

**C — the oracle did not model the writer, and I wrote both** (#2).
The writer did `before.rstrip("\n") + add`; the criterion was `delta == len(add)`.
Two things I authored, disagreeing by exactly one byte.

> **A and D are dangerous because they are silent. B and C announce themselves as a
> FAIL — their cost is time, not a shipped defect.** Spend prevention on A and D;
> spend *diagnosis* speed on B and C.

## What to do about each

**Against A — an instrument passes a control before its first reading is trusted.**
Feed it a fixture whose answer you already know, assert the exact expected output,
and refuse to report a figure if the control fails. The repaired regex opened with:

```python
FIXTURE = "Clean bags sit around 0.6. By 2.4 the fan stalls; back at 1.0. 240 sites, 12 years."
EXPECT  = ["0.6", "2.4", "1.0", "240", "12"]
if NUM.findall(FIXTURE) != EXPECT:
    raise SystemExit("instrument failed its own control - no figure below is trustworthy")
```

Once repaired it reproduced the handoff's independently-derived `4 of 8` **exactly** —
which is what established the *earlier* session's instrument had been right all along.
A control does double duty: it catches your bug, and it lets an agreement mean something.

**Against D — count the variety before coding against one instance.**
`grep -c` the field, list the distinct values, *then* write the branch. #5 was caught
only because a test read the **real** gold file rather than a fixture; a mock-fed unit
test would have agreed with the author's imagined shape (CLAUDE.md §8, scenario rule).

**Against B — pick the token out of `git diff`, not out of your intent.**
Full treatment in the Tier-0 memory
`feedback_merge_verification_token_must_be_new_not_mentioned`. Short form: when a
change *adds a copy* of existing text, assert the **delta** (`pre=1 post=2`) plus a
narrower needle unique to the new form — indentation included.

**Against C — prefer an oracle you did not author.**
`git show HEAD:<path>` byte-identity beat every arithmetic criterion derived from my
own writer. When the actor and the oracle share an author, they share his blind spot.

## The habit that made all seven cheap

**Every check printed the values it measured, never a bare verdict.**

```
[A5] the ledger IOU is gone (both ledgers): pre=2 post=2 -> FAIL
```

`pre=2` is the entire diagnosis. A bare `FAIL` would have started a hunt; every one of
these was resolved in a single follow-up probe because the number was already on the
screen. **A verification report that prints only PASS/FAIL is withholding the evidence
it just collected.**

## What already worked, and should not be changed

- 🔴 **Assert-absent-from-the-target BEFORE the write.** This is what caught #1 — the
  only one of the seven that would have corrupted a Tier-3 archive. A
  verify-by-presence-*after*-writing would have passed happily on the duplicate.
  Runbook R6 already binds this; s269 is its worked justification.
- **Sibling-green controls.** 8 of 23 probes were the same mutation aimed at a
  neighbouring test that had to stay **green**. All 8 held. `P7c`/`P8c` are the sharp
  pair: the two scorer guards share one loop, so a green sibling proves the mutation
  disabled one *half* rather than the loop.
- **Repair by derivation, never by relaxation.** #2's fix was deriving
  `delta == len(appended) − 1` from the writer's own `rstrip` and re-testing it — not
  widening a tolerance after seeing the miss. CLAUDE.md §8 already forbids the latter;
  the point here is that the *derivation* is usually easy once you stop defending the
  criterion.

## The one-line version

> A red check is a claim about **two** things — the artifact and the instrument. Session
> 269 measured which one is usually wrong, and it was the instrument, every time. Go
> read the artifact first; and give every instrument a control, because the ones that
> do not have one do not fail loudly, they fail *confidently*.

---

*Related: [`0007`](0007-harness-exit-code-artifact.md) (command output is evidence),
[`0026`](0026-interpret-before-run-pre-commit-outcome-meaning.md) (pre-commit the
pass/fail read), [`0027`](0027-verify-not-indictment-refute-claim-not-decision.md) (verification is
hygiene, not a verdict), [`0055`](0055-a-comparison-number-measures-the-apparatus-first.md)
(the apparatus talks first). Binding half: `CLAUDE.md` §8 Code Quality.*
