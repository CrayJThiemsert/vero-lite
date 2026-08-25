# `tools/probe_battery/` — the probe-battery driver

The shipped instrument for CLAUDE.md §8's witnessed-RED discipline: break a line on
purpose, run one test, and decide whether **the assertion you predicted** is what failed.

Before this package every session rebuilt that driver from scratch in `/tmp`. Session 253
measured what a fresh one does by default — it re-made four defect classes an earlier
session had already fixed, and published `13/13` while doing it. PLAN-0115 Step 1 ships the
machinery so the mistakes stop being re-derived; ADR-0038 **C6** names this driver's AC-2
and AC-4 as its form-(c) enforcer.

> ### Two similar names, unrelated tools
>
> | Path | What it is |
> |---|---|
> | `tools/probe_battery/` | **this** — the *mutation* battery driver |
> | `tools/probes/` | live *liveness* probes (e.g. the vero-bridge reachability check) |
> | `tools/probe_coverage.py` | the *coverage* half — "what did I never probe?" (lesson #0047) |

---

## What it refuses to do

Each refusal traces to a measured s253 defect.

| # | The defect | The refusal |
|---|---|---|
| 1 | Keyed on `returncode == 0`, output discarded — a crash counted as a witnessed RED | Outcome comes from pytest's junit **failure record**, never an exit code |
| 2 | One reddened test marked **all** its claims witnessed | A `WITNESSED` probe credits **exactly one** claim — the one it pre-declared |
| 3 | Hand-rolled `owner::source` keys while `Claim.stable_key` sat unused on the imported object | Claims are addressed **only** by `stable_key`; there is no alternate keying path |
| 4 | A self-check that intersected exemptions with an already-exemption-filtered set — empty by construction | The overlap check reads the **pre-filter declared** set, so it can actually be non-empty |

It is an **instrument, not a gate** (ADR-0038 D2-C1 refused a mechanical gate). It automates
the mechanics of witnessing; the verdict's authority stays with the review that reads the
report. Deliberately **not** wired into CI or pre-commit — batteries mutate real source
files, so they stay agent/human-invoked. Crossing that line would need an ADR-0038
amendment, not a workflow tweak.

---

## Workflow

**1 — list the claims you intend to witness.** A probe declares a `stable_key`, so get one
from the tool rather than deriving it by hand:

```bash
python -m tools.probe_battery keys tests/services/test_thing.py
```

**2 — write the battery file.** Probe definitions are data:

```json
{
  "claim_sources": ["tests/services/test_thing.py"],
  "probes": [
    {
      "name": "P1",
      "subject": "services/engine/thing.py",
      "old": "if value is None:",
      "new": "if False:",
      "node_id": "tests/services/test_thing.py::test_rejects_none",
      "expect_claim": "test_rejects_none|result.error == \"missing\"|#0",
      "note": "disables the None guard; the error-message assert must redden"
    }
  ],
  "exemptions": {
    "test_helper|sys.platform == \"linux\"|#0": "platform assumption, not a claim about us"
  }
}
```

| Field | Meaning |
|---|---|
| `claim_sources` | modules whose claims form the coverage **denominator** |
| `old` / `new` | the edit, applied to `subject`. `old` must occur **exactly once** |
| `node_id` | the pytest node the probe runs |
| `expect_claim` | the one `stable_key` predicted to redden — a **pre-committed read** |
| `expect` | optional; defaults to `WITNESSED`. Set another outcome for a negative control |
| `exemptions` | `stable_key` → the written reason no probe can reach it |

**3 — run it.**

```bash
python -m tools.probe_battery run --battery battery.json
```

Exit `0` = `PROBE-BATTERY: PASS`, `1` = `FAIL`, `2` = bad battery definition, `3` = refused
because an earlier run is unrestored, `130` = signalled (tree already restored).

---

## Outcomes

Only `WITNESSED` credits a claim.

| Outcome | Meaning |
|---|---|
| `WITNESSED` | the **declared** assertion failed **at its own site** — the one crediting outcome |
| `MISFIRE` | an assertion failed, but not the declared one (or more than one test failed) |
| `CRASHED` | a non-assertion exception — the mutation broke something else |
| `UNREADABLE` | the failure record names no site, so it cannot show *what* broke (C6's legibility conjunct) |
| `GREEN` | the mutation reached disk and nothing reddened — **the guard may be vacuous** |
| `SETUP/COLLECT-ERROR` | collection/fixture/teardown error, or no usable report (pytest failed to start, or timed out) |
| `SKIPPED` | every selected test was skipped |
| `NO-TESTS` | the node id selected nothing |
| `MUTATION-ERROR` | `old` was absent, matched more than once, or the write changed no bytes |

### The witness rule is a conjunction

A RED is a witness only when **the site matches** *and* **the failure is assertion-family**
(`AssertionError` or `Failed`). Both halves are load-bearing:

- `assert obj.thing == 1` with `obj is None` raises `AttributeError` at the declared
  assertion's *own line*. Site matches, kind does not → `CRASHED`. A site-only rule credits
  this.
- A `KeyError` raised one line above a tracked assert *about* a `KeyError` has the right
  type and the wrong site → rejected on the site. Identity is **never** decided by exception
  type alone (ADR-0038 C6).

### Measured pytest facts the classifier rests on

Probed 2026-08-25 across 15 outcome shapes, against the project's pinned pytest:

- 🔴 **`<failure type="...">` is empty** — pytest does not populate it. A classifier reading
  that attribute cannot tell an assertion from a crash. `tests/tools/test_probe_battery.py`
  pins this, so a future pytest that starts populating it reddens and gets a re-look.
- The failure body's **last non-empty line is `<file>:<line>: <ExcType>`**, and that held for
  every shape probed: plain asserts, an assert inside a helper (the line is the *helper's* —
  which is also where `enumerate_claims` attributes the claim), parametrized cases,
  multi-line exception messages, multi-line assertion reprs, and setup/teardown errors.
- `DID NOT RAISE` reports as `Failed` at the `with` line — where a `raises` claim lives.

---

## Crash safety

Batteries edit real tracked source, so restore is defended twice.

- **SIGTERM / SIGINT / any exception** — the signal is turned into an exception so
  `try/finally` runs. (Python's *default* SIGTERM disposition kills the interpreter without
  running a single `finally`; that is the case this exists for.) The running pytest is
  killed on the way out rather than orphaned.
- **SIGKILL runs no Python**, so nothing in-process can help. The guarantee there is the
  **persisted manifest**: every snapshot is on disk with its sha256 *before* the matching
  mutation is written. A later `restore` recovers byte-identically — and `run` **refuses to
  start** while an unrestored manifest exists, because starting anyway would snapshot a
  *mutated* file as pristine and make the damage permanent.

```bash
python -m tools.probe_battery status     # what is outstanding
python -m tools.probe_battery restore    # recover, and reap the orphaned pytest
```

`restore` also **reaps the orphaned pytest child** the kill left behind (pid + exact
cmdline recorded in the manifest; the cmdline match is the pid-reuse guard). That orphan is
still executing the code `restore` is about to put back — and this repo has already paid 67
minutes for a leaked test session at the head of a lock chain.

Run state lives under `.claude/state/probe_battery/` (gitignored), overridable with
`CLAUDE_PROBE_BATTERY_STATE` — the `CLAUDE_*` testability family `_goal_state.py` already
uses.

⚠️ Freshness is a **counter**, not a clock: WSL2's wall clock steps backwards, so the
manifest carries a monotonic `heartbeat` and nothing here orders runs by time.

---

## Related

- `tools/probe_coverage.py` — the coverage half (lesson #0047 §6's fourth clause)
- `docs/lessons/0043-a-probes-red-must-name-what-broke.md` — the source lesson behind C6
- `docs/adr/0038-advisory-lesson-promotion-three-strike-rule.md` §D2-C6 — the binding rule
- `docs/plans/0115-probe-battery-driver-and-verification-instrument-hardening.md` — this
  package's PLAN, including the two safety holes Steps 2–3 still owe
