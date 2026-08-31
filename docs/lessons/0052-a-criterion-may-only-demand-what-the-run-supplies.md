# Lesson 0052: A criterion may only demand what the run supplies — so raising a bar is an ontology move before it is a grader move

**Status:** Advisory (names a feasibility constraint on grading criteria and
records the ruling it produced; the constraint is enforced in code by
`benchmarks/procedure_baseline/grader.role_vocabulary`)
**Source:** Session 264 — Cray's typed ruling on the rationale bar, 2026-08-31

## The claim

A grading criterion can only ask about facts the run actually put in front of the
model. Demand more and the criterion stops measuring the model and starts
measuring the **system's silence** — every candidate fails, identically, for a
reason that has nothing to do with any of them.

The consequence is the useful half:

> **When a bar is too weak, the fix is usually upstream of the grader.** Each fact
> that enters the ontology and the directive makes a stricter criterion
> *answerable*. Until then, writing the stricter criterion produces a uniformly
> red column, not a better measurement.

## What was ruled, and why it is the weakest option on purpose

Session 264 added a rationale axis to the `fleet` benchmark and had to fix its
pass rule. Three candidates, all scored on real runs before the choice:

| rule | gpt-oss | qwen q8 | why it was or was not taken |
|---|---|---|---|
| names a goal-supplied human role | 0/14 | **8/14** | **RATIFIED** (Cray, typed, 2026-08-31) |
| names a role **and** the quoted amount | 0/14 | ~3/14 | rejected — **unmeasurable, not undesirable** |
| graded 0–3, no pass/fail | — | — | no verdict for the lane to report |

The richer questions a human approver would actually want answered — *is this the
right supplier? does their delivery history support accepting this quote? how does
it compare with the alternatives?* — are the ones worth asking. They were not
asked, because **the ontology carries none of those facts.** A rationale cannot
name a supplier's delivery record that the run never showed it, so a criterion
demanding one grades the ontology, not the model.

That is why the ratified bar is the weakest of the three. It is not a judgment
that role-naming is sufficient; it is the strictest rule that is currently
*answerable*.

## The mechanism that makes this structural, not a promise

The same principle governs the vocabulary the check matches against.
`role_vocabulary(goal)` is the intersection of a candidate phrase set with **the
procedure goal's own prose**, so a phrase can only ever be demanded of a model
that was handed it in its prompt.

Two properties follow for free, and both were verified rather than assumed:

- **Fairness is checkable.** `gpt-oss`'s 0/14 is a failure to use words it was
  given — the goal says *"the head mechanic REQUESTS, the fleet manager or the
  owner APPROVES (SoD)"* verbatim — not a vocabulary mismatch the grader invented.
- **Comparability is structural.** The pre-fix goal (`0a1061f~1`) carries that
  clause unchanged, so the demanded vocabulary is identical on both sides of the
  goal fix and the signal compares across all six cells. Edit the goal and the
  check follows it; supply no goal and no check is emitted at all.

## Where this fires

- Writing or tightening any acceptance criterion, benchmark lane, or LLM-judge
  rubric — before asking *"is this strict enough?"*, ask *"is this answerable
  from what the run supplies?"*
- A criterion whose column is **uniformly red across every candidate**. That is
  the signature of this failure, and it reads exactly like "all the models are
  bad" until someone checks what they were given.
- Planning work to "make the eval stricter." The first question is which ontology
  or directive facts are missing, not which rule to write. In session 264 that
  reframed a grader task into an ontology task, and the ontology work is now the
  named unlock rather than a nice-to-have.
- A vertical's seventh instantiation: "how will we know the agent is doing well?"
  starts at what the ontology can say, not at the grader.

## What this does NOT say

- Not "keep every bar weak." The bar should be the strictest **answerable** rule —
  and it should rise as soon as the facts land.
- Not that unmeasurable criteria should be forgotten. Record them with the reason
  they are unmeasurable, so the ontology work has a named payoff; §13 and
  `role_vocabulary`'s docstring both do.
- Not an argument against hard bars generally. `CLAUDE.md` §8's evidence rules are
  hard by design — they demand things the repo genuinely supplies.

## References

- `benchmarks/procedure_baseline/grader.py` — `role_vocabulary`'s docstring is the
  binding copy of this reasoning, at the site that enforces it.
- `benchmarks/model_compare/RESULTS-1.6.md` §13 — the measured comparison of the
  three candidate rules.
- Lesson #0051 — the sibling: an axis may be missing entirely; this one bounds how
  strict the axis may be once added.
- Lesson #0024 (rules must live where the enforcer looks) — same placement logic,
  applied to rules rather than to criteria.
- Lesson #0035 (a negative measurement needs a positive control) — a uniformly red
  column and a correctly-empty result are told apart the same way.
