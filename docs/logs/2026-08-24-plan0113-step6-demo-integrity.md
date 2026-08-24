# PLAN-0113 Step 6 — the demo survives the scope clause, offline

**Date:** 2026-08-24 (session 252)
**Branch:** `feat/plan0113-step6-demo-integrity`, cut from `main` = `a06ea2d`
**Event type:** measurement + a scratch probe (restored byte-identical). No host touched.

## Verdict

**AC-6 PASS.** The positive half was already carried by shipped green tests; what this step
adds is the half nothing witnessed — the **RED**.

## 1. The positive half — already green, and not re-derived

`tests/api/test_fleet_demo_reset_scenario.py` boots the REAL seed block
(`services.api.main._seed_fleet_operate_demo`) and asserts a fresh boot reads
`DEMO-STATE: PRISTINE`, that exactly two demo runs stand, and — the part a status check
would miss — the **suspended STEP**, not merely the status. All green on this tree with
the `scope_by` clause authored (whole suite: 4354 passed / 8 skipped at `ca6133e`).

That is AC-6's *"the operate seed boots, the seeded run parks at `approve` with a non-empty
`output_set`, and `read_demo_state` reads PRISTINE"*, already asserted by a shipped test.

## 2. The RED — AC-6's named witness

Probe **R1**: flip fleet's `when_absent: sweep` → `refuse` in a scratch copy.

| | |
|---|---|
| mutation reached the file | `procedures.yaml` `b68f47cf7317` → `8842541ca854` |
| **named witness** (pre-committed) | `read_demo_state(db_session) == STATE_PRISTINE` |
| result | **RED**, exactly as predicted |
| restore | **byte-identical**, post-restore baseline green |
| coverage | **53 claims — 3 witnessed RED, 50 exempted with a named mechanism, 0 gaps, 0 stale** |

**The mechanism, stated:** `_seed_fleet_operate_demo` is **fail-soft** by contract — *"a
seed error logs and never blocks the demo boot"* (`services/api/main.py:253-261`). So under
`refuse` the seed's `intake` refuses, the boot swallows it, **no run parks**, and the state
reads `CONSUMED`. This is precisely the failure mode PLAN-0113 D1 chose `sweep` to avoid:
the seeded demo run fires with **no** `entity_ids` by design, because its breaching truck is
chosen by the declared query *during* the run.

## 3. Denominator scoping, stated where a reviewer meets it

The instrument is a **one-key flip** of fleet's absent-scope policy. It can reach any claim
whose premise is the parked demo pair; it cannot reach the reset's own delete/re-seed
machinery, the tamper-evident audit chain, or the static source guard. All 53 claims of the
module are enumerated and every unreddened one is named with the mechanism that puts it out
of reach — five groups, each a real mechanism rather than a blanket.

## 4. Instrument repairs — three, none on the criterion

1. **The battery REFUSED TO RUN** on the first attempt: five helper owners had no exemption
   mechanism named. That is the discipline working — an unnamed claim is a gap, never a
   default pass. Reasons added.
2. **A helper-owned red read as "unpredicted".** `_proposals_at|loaded is not None` reddened
   because, with no demo run seeded, `load_run` returns `None` inside the helper — the same
   premise-loss mechanism, surfacing one frame down. The check was comparing a HELPER's name
   against a set of TEST names. Repaired to attribute a helper-owned red to the test that
   actually failed.
3. **One collateral prediction was wrong, and is withdrawn with its reason.**
   `test_the_reset_cannot_reach_a_non_demo_run_or_a_visitor_case` was predicted to lose its
   premise and did **not** fail: its claims are **negative** — what the reset does *not*
   touch — and a missing demo pair does not falsify a "does not reach" assertion. The
   prediction was wrong about the SHAPE of the claim, not about the mutation's effect.
   *(Worth a future reader's eye: without the seeded pair that test would go partly vacuous,
   which is why it carries its own controls and why the baseline runs WITH the pair.)*

None of the three was repaired by relaxing what the check demanded.

## Next

Step 7 (AC-7 — the four governance record sites, plus the `docs/STATUS.md` fleet-wide
narrative that Step 4's re-grep confirmed is still live). Then AC-8, measured last so the
counts describe the tree that ships. Step 8 stays gated on a typed Cray go per occasion and
per phase.
