# Lesson #0040 — A probe proves one direction only: an absence oracle and a presence oracle need opposite mutations, and a count is not an identity

**Date:** 2026-08-11 (session 222)
**Class:** advisory (oracle design / non-vacuity discipline)
**Trigger:** Building the AC-8 clause-2 + ADR-0037 D2.7 scenario module
(`tests/api/test_visitor_case_to_monitor_scenario.py`, PRs
[#1124](https://github.com/CrayJThiemsert/vero-lite/pull/1124) /
[#1125](https://github.com/CrayJThiemsert/vero-lite/pull/1125)). Five behavioural
probes were run against it. Two of them found that assertions which looked
covered were not.

## The lesson

**A non-vacuity probe licenses exactly the assertions its mutation can break —
no others.** The habit ("mutate behaviour, see RED, restore") is usually stated
as one step per *module*, which is where it goes wrong: a module holding both an
**absence** assertion (*this text must not appear*) and a **presence** assertion
(*this field must appear*) needs **two probes running in opposite directions**,
because the mutation that reddens one cannot touch the other.

**And a count is not an identity.** For an acceptance criterion of the shape
*"X now appears in the UI"*, the obvious oracle is a delta — the count went up.
A delta is **necessary and not sufficient**: it can be satisfied by something
that is not X. What closes the criterion is the **identity tie** — that the thing
which appeared is provably *this* X, read through the same function production
uses.

Both halves share one root: **an assertion is only as strong as the mutation you
have shown can break it.** Everything else is inference about a test you did not
run.

## 1. Case one — the probe that covered half the module

The module asserts, over every `audit_log` row a run produces:

* **absence** — the visitor's typed case text appears in **no** payload (D2.7);
* **presence** — the emergency path's `WaiverInvocation.justification` and the
  ratification `note` **do** appear (they are human free text in the chain **by
  design**, and pinning that is what the RoPA needs).

**Probe 1** folded the whole proposal list into `gate_decision`'s payload at the
real write site. The absence scan reddened, with the visitor's Thai text visible
in the failure output. Convincing — and it says **nothing** about the presence
assertion, because inserting text cannot make a "must be present" claim fail.

**Probe 3** removed `"justification"` from the provisional decision payload. The
presence assertion reddened. Without it, that assertion could have been
permanently green — asserting a compliance fact that no probe had shown could
fail.

The mutations run in opposite directions: **probe 1 adds, probe 3 removes.** One
probe set does not cover both, and no amount of care about *"did I probe this
module?"* surfaces the gap — the question has to be *"did I probe this
assertion?"*

## 2. Case two — the delta passed while the thing under test was severed

AC-8 clause 2 reads: *a case opened via Tab I's backend appears in Tab H's list.*
PLAN-0103 Step 7 had just seeded one waiting run at boot, so the module was
already shaped around the obvious trap — *"open a case, then assert H has a
run"* passes with the case removed entirely. The assertion was therefore written
as a **delta**: the waiting-run count strictly increased.

**Probe 2** severed `case_projection.apply()`'s overlay, so the visitor's case
never reached the run at all. Measured result:

| assertion | under the severed overlay |
|---|---|
| `waiting_human_count` increased 1 → 2 | **still PASSED** |
| the parked run carries the visitor's `case_id` | **FAILED** |

The delta survived because a run still parks — on the fixture rows — regardless
of whether any visitor case exists. The count was real; it was about something
else.

What caught it was reading the case id off the parked proposal's grounding trace
with `run_link.case_id_of`, **the same function the production hook uses** to
decide which case a decision belongs to. Not a re-implementation: a
re-implementation would have been a second chance to be wrong in the same
direction.

## 3. Why the usual remedies do not reach this

* **"Run the non-vacuity probe"** is satisfied by one probe. Both gaps above sit
  *inside* a module whose probe was already green.
* **Test count arithmetic** (4004 → 4007) proves the tests were collected, not
  that any of them can fail.
* **Reviewing the assertions** does not help: both looked correct, and both
  *were* correct. The defect was never in the assertion — it was in the evidence
  that the assertion was live.
* **A stronger delta** (`+= 1` instead of `>= 1`) would not have caught case two.
  The severed run still produced exactly one new waiting run. The problem is not
  the delta's tightness; it is that a count carries no identity.

## 4. Operational form

When a module's green is about to be trusted:

1. **Enumerate the assertion KINDS, not the modules.** Absence, presence,
   identity, ordering, count. Each kind needs a mutation that can break *it*.
2. **Name the mutation's direction.** If every probe you ran *added* something,
   you have not tested any "must be present" claim, and vice versa.
3. **For an "X appears" criterion, assert the tie, not only the delta** — and
   read the identity through the production reader, not a copy of it.
4. **Positively control the absence.** Assert the sentinel IS present upstream
   first; otherwise "absent downstream" also passes in the world where the value
   never arrived. (That is [[0035-negative-measurement-needs-a-positive-control]]
   applied inside a test rather than to a measurement.)
5. **Restore from a snapshot outside git**, and verify `git diff` is empty after
   — a probe left in place is a behaviour change nobody decided.

## 5. Scope

This is about **oracle design**, not about doubting settled work — CLAUDE.md §6
("Verification is hygiene, not a verdict") still governs how a passed check is
narrated. The rule here fires *before* the green is trusted, and it fires
hardest on modules that pin **compliance facts**, where a permanently-green
assertion is worse than a missing one: it reads as evidence in an audit and is
not.

It also does **not** mean "probe everything." It means the probe budget should
be spent by assertion kind rather than by file, and that an unprobed assertion
should be *known* to be unprobed rather than assumed covered.

Related: CLAUDE.md §8 (the scenario-test rule — a mock-fed suite agrees with
itself by construction) + §6 (verification is hygiene);
[[0035-negative-measurement-needs-a-positive-control]] (a zero needs a control
that can find a one — the same idea one layer out);
[[0027-verify-not-indictment-refute-claim-not-decision]] (claim-refutation stays
adversarial); [[0019-adversarial-spoof-tests-belong-at-unit-layer]] (where an
adversarial assertion belongs). Worked example, with all five probes and their
measured RED output: `docs/logs/` is not the home — read the module's own
docstrings, which record each trap inline.

*AI-assisted (Claude Code, session 222); no `Co-Authored-By` per CLAUDE.md §7.*
