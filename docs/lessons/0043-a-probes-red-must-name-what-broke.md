# Lesson #0043 — A probe has a second job: the RED it produces must name what broke

**Date:** 2026-08-14 (session 231)
**Class:** advisory (oracle design / guard legibility)
**Trigger:** PLAN-0105 Steps 2–3 and Step 4
([#1163](https://github.com/CrayJThiemsert/vero-lite/pull/1163) /
[#1164](https://github.com/CrayJThiemsert/vero-lite/pull/1164)). Two probes in
consecutive PRs reddened **correctly** and **illegibly**. Neither guard was
vacuous; both would have been useless the day they fired.

## The lesson

A non-vacuity probe answers *"can this assertion fail?"* It does **not** answer
*"will the failure tell anyone what broke?"* — and the second question decides
whether the guard survives contact with a future session.

**A guard whose RED is unreadable gets deleted or muted by the next person who
trips it**, because they cannot tell a real defect from a broken test. The
protection ends there, silently, and the deletion looks like tidying up.

So the probe has two outputs, not one: the RED itself (the guard is live) and
the RED's *text* (the guard is usable). Only the first is usually checked.

## 1. Case one — the test crashed before it could assert

`test_ac8_inert_on_a_db_less_vertical_even_with_the_flag_on` asserts that
`start_case_retention("energy")` returns `None`. The probe removed the vertical
gate. Measured RED:

```
E       RuntimeError: no running event loop
```

The test was **sync**, so with the gate gone the function reached
`asyncio.create_task` and blew up *before* reaching the assertion. It failed —
so the guard was not vacuous — but the message says nothing about retention,
nothing about a gate, and nothing a reader could act on.

Fix: make the test `async`. Same mutation, new RED:

```
E       AssertionError: assert <Task pending name='Task-2' coro=<_retention_loop() ...>> is None
```

Now the failure names the thing that broke.

**Smell:** the RED is an *exception type* rather than an *assertion*. The test
died on the way to its own oracle.

## 2. Case two — the container comparison pytest truncated

`test_ac5i_the_declared_fk_children_equal_the_fks_the_metadata_declares` compared
two sets of six near-identical `repair_case_*` table names with a bare `==`. The
probe dropped one child from the declared list. Measured RED:

```
E       AssertionError: assert {'repair_case...e_task_event'} == {'repair_case...e_task_event'}
```

Both sides truncate to the same string. The assertion is correct, the probe is
correct, and the output is unusable.

Fix: spell out both directions in the assertion message. Re-running the same
probe printed:

```
E  AssertionError: the sweep's declared FK children have drifted from the metadata.
   Declares an FK to repair_case but the sweep never clears it:
   ['repair_case_accepted_quote']. Declared by the sweep but no longer an FK child: [].
```

**Smell:** a comparison of two containers whose elements share a long common
prefix. pytest's truncation is doing its job; the assertion is not doing its
own.

## 3. Why the usual remedies do not reach this

* **"Run the non-vacuity probe"** is satisfied. Both probes were RED on the first
  attempt, and both were recorded as passing evidence.
* **Test-count arithmetic** proves the test was collected, never that its failure
  is readable.
* **Reviewing the assertion** does not help — both assertions were *correct*. The
  defect lives in the failure OUTPUT, which nobody reads until the day it fires,
  by which time the reader is not the author.
* **[[0040-a-probe-proves-one-direction-only]]** covers whether the right
  assertions were probed at all. This is the step *after* each of those probes:
  the mutation broke the right thing — now read what it said.

## 4. Operational form

After a probe goes RED — before recording it as evidence:

1. **Read the message and ask: does it name the thing that broke?** If a
   competent stranger could not act on it, the guard is not finished.
2. **Two smells worth naming.** An exception type instead of an assertion (the
   test crashed before its oracle). A container comparison the runner truncates.
3. **Fix the GUARD, not the probe.** The probe is doing its job by exposing this;
   weakening it to get a prettier failure inverts the point.
4. **Commit the reason in the test's docstring, marked measured.** Both fixes
   above look like fussiness without their reason attached, and the next reader
   "simplifies" them back — an `async` on a test that awaits nothing, and a long
   assertion message where `==` would do, are exactly the shapes a tidy-up
   removes.

## 5. Scope

This is about **legibility**, not about doubting the assertion — CLAUDE.md §6
("Verification is hygiene, not a verdict") still governs how a passed check is
narrated, and nothing here licenses re-opening settled work.

It also is **not** "write long assertion messages everywhere". It fires on
exactly one trigger: **a probe you just watched go RED**. At that moment the
failure output is in front of you for free, which is the only moment it is cheap
to judge — every other time, reading it means reproducing the failure first.

Related: [[0040-a-probe-proves-one-direction-only]] (probe by assertion KIND, not
by module — this lesson is its successor step);
[[0035-negative-measurement-needs-a-positive-control]] (an absence needs a
control that can find a presence); CLAUDE.md §8 (the scenario-test rule — a
mock-fed suite agrees with itself by construction). Worked examples with their
measured output: the docstrings of
`tests/api/test_case_retention_task.py::test_ac8_inert_on_a_db_less_vertical_even_with_the_flag_on`
and
`tests/services/db/test_case_retention_completeness.py::test_ac5i_the_declared_fk_children_equal_the_fks_the_metadata_declares`.

*AI-assisted (Claude Code, session 231); no `Co-Authored-By` per CLAUDE.md §7.*
