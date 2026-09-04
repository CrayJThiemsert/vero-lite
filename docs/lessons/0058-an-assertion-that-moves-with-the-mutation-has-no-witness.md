# Lesson #0058 — an assertion that moves with the mutation, or sits behind a failing sibling, has no witness

**Session:** 277 (2026-09-04) · **Measured on:** PLAN-0120 Steps 1–4, four probe
batteries, 32 witnessed REDs · **Status:** advisory (§1 precedence — promote to ADR if
it must bind)

## The claim

CLAUDE.md §8 says a load-bearing green is not evidence until its assertion has been
**witnessed RED**. Two shapes make an assertion *un-witnessable*, and both pass every
other check — the test is green, the suite is green, `ruff` and `mypy` are clean, and
the probe battery reports `PROBE-COVERAGE: COMPLETE` if the claim is exempted:

1. **Shared fate** — the expected value is derived from the code the mutation changes,
   so both sides move together and the comparison can never fail.
2. **Never reached** — an earlier assertion in the same test fails first, so pytest
   stops and the claim's state is *unknown*, not green.

Each occurred in session 277. Neither was caught by review. Both were caught by the
same question: **"which single mutation reddens this line?"** — being unable to answer
it *is* the finding.

---

## Shape 1 — the expectation moves with the mutation

### Instance A: an expected value computed by the function under test

```python
# tests/services/db/test_db_guard_second_arriver.py — the FIRST draft
expected_db = make_url(db_guard.role_suffixed(settings.test_database_url, child_role)).database
assert f"db={expected_db}" in proc.stdout
```

The test asserts the child resolved the right database name — the load-bearing claim of
D8-VX-1, that the role marker crossed into the child process. But `expected_db` is
computed with **`role_suffixed`, the function under test**. Mutate the suffixing and
both the child's name and the expectation change together. The assertion is green
before the mutation and green after it.

**The fix is not a better assertion — it is a different anchor.** The name is now
checked against the **parent's** database name, a value no mutation to the suffixing
can follow:

```python
parent_db = make_url(settings.test_database_url).database
child_db = reported[0].split("db=", 1)[1].split(" ", 1)[0]
assert child_db != parent_db          # ← probe P6 reddens here
```

### Instance B: a constant both sides import

The obvious mutation for "a contended child exits with the reserved code" is to change
the constant:

```python
CONTENDED_EXIT = 75   →   CONTENDED_EXIT = 74
```

It does nothing. The parent process and the child pytest **import the same module**, so
the child exits 74 and the parent expects 74. The probe reports `GREEN` and the claim
looks vacuous when it is the *mutation* that is inert.

The mutation has to hit the **call site**, where only one side moves:

```python
pytest.exit(reason, returncode=db_guard.CONTENDED_EXIT)   →   returncode=0
```

⚠️ **This is why `_goal_gate.py` and `tests/db_guard.py` each carry `CONTENDED_EXIT = 75`
as a literal with a cross-file pin test** rather than sharing an import: the gate runs
Windows-side and cannot import `tests/`. The pin
(`tests/handoffs/test_goal_gate_contended_exit_pins_the_guard.py`) is the assertion that
*can* redden, because its two sides genuinely come from different files.

### The tell

You cannot name a mutation that reddens the line. Not "I would have to think about it"
— there is no such mutation, because the expectation is downstream of the thing you
would change. **Ask the question while writing the assertion, not while writing the
probe**; by then the test is already committed and reads as covered.

---

## Shape 2 — the claim behind a failing sibling

pytest stops at the first failing assert. Every assertion after it is **NOT REACHED** —
its state is unknown. It is not green, and a probe cannot credit it.

So the *order* of assertions inside one test decides which claims are witnessable:

```python
# tests/services/db/test_db_guard_second_arriver.py — AC-6
assert skipped == 0                                    # ← 6c reddens HERE
assert proc.returncode == db_guard.CONTENDED_EXIT      # ← 6a reddens here
assert fields["outcome"] == db_guard.CONTENDED
assert holder_named
```

`skipped == 0` is the claim that matters most — a contended session that *skips* reads
as a pass on the summary line, which is the failure PLAN-0120 §2 exists to remove. With
`rc == 75` first, the mutation `pytest.exit → pytest.skip` reddens `rc` and leaves
`skipped == 0` permanently NOT-REACHED: **no probe anywhere could witness it.**

Reordering gives each claim its own reddening mutation, and leaves the *other* green —
which is what makes each probe attributable rather than a blast radius:

| mutation | `skipped == 0` | `rc == 75` |
|---|---|---|
| `pytest.exit → pytest.skip` (6c) | 🔴 reddens | green (not reached) |
| `returncode=CONTENDED_EXIT → 0` (6a) | 🟢 stays green | 🔴 reddens |

The same reordering was needed for AC-8's zero-residue claim in
`tests/handoffs/test_goal_gate_db_role.py`.

🔴 **Write a comment saying the order is deliberate.** Otherwise the next reader tidies
it for readability and silently deletes a witness, with every check still green.

---

## The practice

1. **While writing an assertion, name the mutation that reddens it.** No answer ⇒ the
   assertion is decorative; find a different anchor before committing it.
2. **Anchor expectations on something the mutation cannot follow** — a value from the
   other side of the boundary, a literal in a different file with a pin test, a
   constant the test owns. Never on the function under test.
3. **Order asserts so each claim has a mutation that reddens it while its siblings stay
   green**, and say in a comment that the order is load-bearing.
4. **In a probe battery, `NOT-REACHED` is an honest exemption ground** — write it as
   such (*"NOT-REACHED under probe X; state unknown, never green"*) rather than
   letting the claim look covered. Both files above carry exemptions in exactly that
   wording.

## Related

- [#0045](0045-a-probe-that-shares-fate-with-its-subject-cannot-fail.md) — the same
  family one layer down: a *liveness* probe running inside its subject. Shape 1 is that
  lesson at the assertion level, and the tell is identical (the check cannot return
  failure, so its green carries no information).
- [#0047](0047-a-probe-battery-is-silent-about-what-it-never-probed.md) — coverage says
  nothing about claims no probe reached; Shape 2 is the case where the *battery* thinks
  a claim was reachable and it never was.
- [#0043](0043-a-probes-red-must-name-what-broke.md) — the legibility half of the same
  discipline.
- [#0040](0040-a-probe-proves-one-direction-only.md) — why each probe needs its sibling
  green, not merely its own red.
- `tools/probe_battery/README.md` — the driver's four refusals, all traceable to s253.
