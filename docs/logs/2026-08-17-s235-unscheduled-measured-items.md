# s235 — three measured, unscheduled items rehomed out of STATUS

**Date:** 2026-08-17 · **Session:** 235 · **Base:** `main` at `0449de0`

**Why this file exists.** Three `docs/STATUS.md` Active-TODO rows carried facts that
**no other tracked artifact held** — `git grep` confirmed each before the cut. R2's
carve-out therefore forbade trimming them, and its exit is
`rehome → re-point → verify → trim`. None of the three has a natural code, PLAN or
lesson home: one is a **write job whose output is deliberately gitignored**, one is a
**banked measurement series with no method**, and one is a **CI project with three
unresolved design questions**. A dated `docs/logs/` record is the right shelf for all
three — tracked, never rotated, and carrying no obligation of its own.

> **Every figure below was re-measured against `0449de0` while writing this file.**
> Where the STATUS row's number was stale, the fresh number is written and the stale
> one is named as superseded. Two of the three had a stale figure.

---

## 1. The public one-pager v2 — DESIGN-READY, a WRITE job, not a design job

✅ **RULED (Cray, typed, s226): if it is built, its output goes to
`docs/strategy/private/` (GITIGNORED), NOT tracked `docs/`.**

**Why it needed a tracked home at all:** `git grep` across `docs/ services/ tests/
benchmarks/` returned **zero** hits — it lived only in a gitignored handoff, which is
exactly how a ruling was lost at s223.

**Grounded status, because it changes the item's cost.** A complete spec already
exists at `docs/strategy/private/2026-08-10-onepager-v2-spec-and-q5-q12-triage.md`
(verified present, 18,733 B, gitignored — **referenced BY PATH only**; pricing and
spec body never get copied into tracked docs). It carries a locked six-block
structure, the bilingual roof line and CTA already written, a must-NOT-contain list,
and a 14-row claim→evidence ledger pinning every claim to DEMO / PILOT / DESCRIPTION.
Source material verified present: the wedge one-pager, the b3 talking points, the GTM
ammo pack, and all three `deploy/published/*/card-copy.md`.

⚠️ **One honesty constraint the spec itself flags:** the DOA/SoD governed-approval
claim is **`DESCRIPTION`, not `DEMO`** — the spec calls this *"the lead pillar's
gap"*.

🔴 **CORRECTED s232, `was an error` — the stated reason was false, though the
conclusion survives on a different basis.** The row and the spec said the gap exists
*"because Tab G is not published"*. **Tab G IS published** — re-verified 2026-08-17:
`deploy/published/oct-procurement/published.env:46` ships `UI_PUBLISHED_VIEWS=G,F`,
and procurement went live at s222. The real basis: **the Act card renders on NO
published profile** because event mode is suppressed, so the governance *moment* is
viewable while the approval *action* is clickable nowhere public.

⚠️ **Consequence nobody has acted on:** the spec's own stated unblock trigger has
therefore **ALREADY FIRED**, and its claim→evidence ledger row was never upgraded.

---

## 2. The assembly-cost axis — MEASURE it before an ADR argues it

**Cray's ruling (typed, s197) is an ORDERING:** build the tripwire that puts a number
on assembly cost **first**, *then* draft the ADR on top of that number. Nothing is
built and no PLAN is drafted.

**The banked series, preserved because it is banked nowhere else.** Verified
2026-08-17: `git grep -i "assembly cost|assembly-cost"` over `docs/ services/ tests/
benchmarks/` hits **only `docs/STATUS.md` and `docs/status-archive/`** — no test, no
PLAN, no ADR holds it. Churn per vertical went:

> **1:1.8 → 1:6 → 1:1.1**

i.e. **spiky, not falling** — which is the shape any ADR on this axis has to argue
against. Left unbanked it dies at the next context reset.

🔴 **BLOCKING GAP, measured s226 — the SERIES is banked, but the METHOD is banked
NOWHERE AT ALL.** No numerator, no denominator, no window is recorded anywhere in the
repository. **A tripwire built today would therefore emit a number that CANNOT be
compared to those three.**

**One decision slot must be filled BEFORE any build:** pin the metric definition
(numerator / denominator / window), and rule whether the three banked figures are
**reproducible under it** or must be **declared unrecoverable**.

---

## 3. Seam-scoped mutation-testing CI — a PLAN candidate, NOT built

Surfaced s188 as the one CHECKABLE variant the scenario-test hook rejection does not
cover. A CI job that requires the scenario suite to **REDDEN under a seam mutation**:
ritual compliance cannot fake it, since an empty or stubbed scenario suite stays green
under mutation — exactly what a file-existence hook would miss. Rationale:
`CLAUDE.md` §8's scenario-test bullet.

🔴 **SCOPING BLOCKER — scenario tests cannot be machine-scoped today, by marker OR by
filename.** Re-measured 2026-08-17 at `0449de0`:

| | measured | STATUS row said |
|---|---|---|
| pytest markers in `pyproject.toml` | **2** — `slow`, `host_state`; **no `scenario` marker** | same |
| scenario/e2e files | **14** (13 singular `_scenario.py` + 1 plural) | 13 — **superseded** |
| test functions in them | **69** | 63 — **superseded** |
| directories spanned | `tests/api`, `tests/services/db`, `tests/services/engine` | same |
| the odd filename | `tests/api/test_fleet_pilot_scenarios.py` (**plural**, every sibling singular) | same |

⚠️ **The count drifted again, which is the point of lesson #0042** — a remembered
baseline is not evidence. s226 recorded "eight sibling files"; s232 corrected it to
13/63; the tree at `0449de0` holds **14/69**. **Trust the measurement, not the
remembered number**, and expect this table to be stale the next time it is read.

🔴 **CI runs bare `pytest -q` with no `-m`, so `CLAUDE.md` §8's binding scenario-test
rule is enforced by NOTHING mechanical today** — it holds only because each PLAN's
ACs restate it. That is a ③-arming failure in the session's own three-condition law:
the instrument exists and the data reaches it, but nobody armed it as a gate.

✅ **XS prerequisite, worth doing on its own and independent of the CI job: add a
`scenario` marker and normalise that filename.** **Rename blast radius re-measured
2026-08-17: ZERO** — `git grep test_fleet_pilot_scenarios` returns exactly one
tracked hit, the STATUS row that this file replaces.

**The CI job itself stays effort L**, with three unresolved design questions: what
**marks** a scenario test, what **enumerates** a seam, which **mutation engine**.

---

*Written session 235 (2026-08-17) as the tracked home for three carve-out items whose
substance `git grep` confirmed lived only in `docs/STATUS.md`. Two stale figures were
re-measured and corrected in place rather than copied forward. AI-assisted (Claude
Code).*
