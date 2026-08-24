# Lesson #0047 — A probe battery reports on the probes you wrote and is silent about the assertions you did not probe; make it compute its own coverage, and give every test one claim so that coverage is assert-level

**Date:** 2026-08-24 (session 251)
**Class:** advisory (verification-instrument design / non-vacuity discipline)
**Trigger:** PLAN-0113 Step 2. A nine-probe non-vacuity battery printed
`PROBE-VERDICT: PASS` — every probe reached the code, reddened its named target,
and left the others green. The `goal-evaluator` then hand-traced all nine
mutations against the module and found that **12 of the 33 test items were never
red under any probe**, two of those groups load-bearing rather than controls. The
battery had been telling the truth and answering the wrong question.
**Cross-references:**
[[0039-a-self-authored-guard-inherits-the-authors-blind-spot]] (the same failure
one level down: a self-supplied *predicate* reproduces its author's model — this
is the self-supplied *probe set* doing the same thing);
[[0040-a-probe-proves-one-direction-only]] (a probe licenses only the assertions
its mutation can break — that is about one assertion's direction, this is about
the assertions with no probe at all);
[[0043-a-probes-red-must-name-what-broke]];
[[0045-a-probe-that-shares-fate-with-its-subject-cannot-fail]].
PRs [#1275](https://github.com/CrayJThiemsert/vero-lite/pull/1275),
[#1277](https://github.com/CrayJThiemsert/vero-lite/pull/1277).

## The lesson

**A probe battery is a self-authored enumeration, and its green means exactly one
thing: "the probes I thought of behaved as I predicted." It says nothing whatever
about the assertions I did not think to probe — and it cannot, because those
assertions appear nowhere in it.** The gap is invisible from inside: no probe
fails, no count looks wrong, and the artifact reads as thorough precisely in
proportion to how carefully the probes that *do* exist were built.

Two moves close it, and they are different in kind:

1. **Make the battery compute its own coverage.** Enumerate the test items,
   subtract every item any probe reddened, and **fail on the remainder** unless
   each is a named control with a written reason. This converts "what did I not
   probe?" from a question needing an outside asker into a line of output.
2. **Give every test exactly one claim, so item-level coverage IS assert-level
   coverage.** A run stops at the first failing assert, so a test with three
   asserts can be "witnessed RED" while the second and third have never executed
   under any mutation. Splitting is a *structural* fix: it makes the instrument
   you already have exact, instead of adding a second instrument to maintain.

## 1. What the battery reported, and what was true

The Step-2 battery's pass rule was strict and unchanged throughout: each probe had
to (a) prove its mutation reached the code — anchor found plus a post-write sha256
difference, (b) redden a set of tests named **in advance**, and (c) produce no
extra red. Nine probes satisfied all three.

The evaluator's finding was not that any of that was false. It was that the union
of all nine red sets covered 21 of 33 items. Among the 12 never touched:

- `test_the_new_refusal_kind_is_additive` — the additivity claim another criterion
  explicitly rested on — **had no probe at all**.
- `test_scope_ids_absent_shapes` — the enumeration of the three "absent" shapes the
  whole `when_absent` policy is defined against — survived every probe, because the
  one probe near it mutated only the function's final `return` line and never its
  three guard branches.

Neither is exotic. Both are the kind of assertion you write early, feel good about,
and never think about again — which is exactly why nothing pointed a mutation at
them.

## 2. The count of gaps is itself a self-supplied enumeration

The evaluator named **three** unreached asserts. Treating that as the work list
would have been the same error one turn later: an inherited defect list is not an
enumeration. An AST scan of the module found **seven** tests carrying more than one
claim.

Counting mechanically also surfaced a category the prose list had missed:
**`pytest.raises` is itself an assertion.** A test with a raises-context *and* an
assert carries two claims, not one. Four of the seven were that shape. The fix was
a small helper that performs the call and returns the caught exception, so the
claim *that it raises* belongs to exactly one test and the context is plumbing
everywhere else.

## 3. The coverage check's first output was wrong, and the error was instructive

Switched on, the check reported **30** unexplained items. It was asking the Step-2
battery to redden Step-1's assertions — which a different battery had already
witnessed, by mutating different files, in an already-merged PR.

Narrowing the denominator to the module under test is the obvious repair and also
the obvious way to cheat, so it was surfaced for review rather than done quietly.
The evaluator's answer was worth having: the denominator had **not** moved — its own
earlier finding had already been scoped to that module ("12 of 33"). A worry about
one's own honesty is still a claim, and it can be wrong in the reassuring direction.

**The general form:** a coverage denominator must be the surface the instrument can
actually reach. Including what it structurally cannot reach forces junk exemptions,
and a junk-filled exemption list destroys the check faster than not having one.

## 4. What the numbers did

| stage | probes | coverage |
|---|---|---|
| battery reports PASS, no coverage check | 9 | unknown — later measured 21/33 |
| after the evaluator's FAIL, gaps probed | 13 | still uncounted |
| coverage check added, denominator fixed | 17 | 33/34 items |
| every test split to one claim | 17 | **40/42 assertions** |

The last row is the only one that means "every load-bearing assertion has been
witnessed RED", and reaching it required no new probes — only that the tests stop
hiding assertions behind each other.

## 5. The side-effect nobody predicted

After the split, the seventeen `expect_red` sets had to be re-derived. Doing that by
reasoning each mutation against the fixture *before* running produced **17
predictions with zero mismatches on the first attempt** — against three earlier
rounds that each needed an instrument repair.

That is not luck. One-claim tests make the question "what does this mutation break?"
answerable by reading, because each answer is a single behaviour rather than a
bundle. **A test structure that makes probe outcomes predictable is a test structure
that makes probe outcomes checkable** — and the predictions being written down first
is what makes a mismatch a finding rather than a thing to be explained away.

## 6. Do this

- A battery's pass rule needs a fourth clause beside reach / named-red / no-extra:
  **every item not reddened by some probe is named, with a reason.**
- Prefer **one claim per test**. Count `pytest.raises` as a claim. Count a
  conjunction (`assert a and b`) and a tuple comparison as the claims they are —
  the run stops at the first failing one either way.
- Compute the gap list **mechanically** (AST, not regex — a regex over `assert `
  matches prose in docstrings). A hand list will be short by the number of cases
  you cannot see.
- Scope the denominator to what the instrument can reach, and **state the scoping**
  where a reviewer will meet it. If narrowing it feels convenient, that is the
  moment to have someone else check.
- Write every `expect_red` set **before** the run. If one is wrong afterwards, the
  repair is to name the causal mechanism that made it wrong — not to widen the set
  until the output fits.

## 7. The residual, stated

Splitting tests is not free: 20 tests became 28, and a reader now has to hold more
names. That is the price of the instrument being exact, and it is worth paying for
a module whose whole job is to be evidence. It would not be worth paying everywhere.

The battery also still runs most probes against one target module, so its
no-extra-red guarantee covers a narrower surface than its baseline count suggests.
That is recorded rather than fixed — latent, not an active false green.
