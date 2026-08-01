# PLAN-0099: Wall-Clock Root Fix — Store-at-Write + Monotonic Sequence

**Status:** Complete
**Owner:** Claude Code
**Completed:** 2026-08-01 (session 199) — all six steps shipped as one stack in
PR [#1008](https://github.com/CrayJThiemsert/vero-lite/pull/1008) (`6a3f2d7`).
All ten ACs closed. AC-9's gate ran at CI scope with its pass/fail read fixed
before the run: **3730 passed / 8 skipped / 0 failed**, the eight skips all
host-state or live opt-ins and none of them a node an AC names — proven
positively by re-running the named nodes alone (**38 passed, 0 skipped**)
rather than inferred from their absence among the skips. Seventeen
non-vacuity probes across Steps 2–4, 17/17 RED against their named tests.
**Created:** 2026-07-31 (session 196)
**Related ADRs:** None binding. Governance context: `docs/STATUS.md`
§'Active TODOs' (the deferral entry — "DEFERRED: a monotonic `sequence` column
on `step_results`"), CLAUDE.md §8 (scenario-test rule), CLAUDE.md §6
("Verification is hygiene, not a verdict" — the `superseded by new info`
classification used in §Governance).
**Drafted by:** in-harness `plan-drafter` subagent (ADR-013 D1 phased authority);
independent review + commit: Code + Cray at PR merge (ADR-012 D4.3).

---

## Goal

Retire wall-clock ordering and comparison from every **correctness path** in the
repair-case evidence subsystem, and discharge the long-deferred `step_results`
sequence-column root fix — in one migration wave. The mechanism is twofold:
**store at write time what is only cheaply true at write time** (the
at-acceptance lowest quote, which `services/api/routers/cases.py:637` already
computes correctly and then throws away), and **key "current row" on monotonic
insertion order** (a DB-assigned `seq`) instead of a clock that was measured
stepping backwards ≥ 400 ms roughly every 15 s on the dev box. The static guard
that held the line for the original deferral is widened so it can see the two
shapes it is currently structurally blind to: cross-row timestamp *comparisons*
and wall-clock *latest-wins picks*.

## Evidence (measured s196 — taken as given; forced reproductions are deterministic)

- **The clock.** `datetime.now(UTC)`, 300 s tight loop, 528M samples: 20
  backward steps, all ≥ 400 ms, worst −592 ms, ≈ 0.067/s. No step is "small" —
  any sub-second comparison window is swallowed whole.
- **The window.** Acceptance-write → next-quote-write gap over 30 real HTTP round
  trips: 90–166 ms (median 130). ⇒ P(flake) ≈ 0.067 × 0.13 ≈ **0.9 % per
  execution** — matching the observed 1-in-3 full-suite failure of
  `tests/api/test_accepted_quote_endpoint.py:275`
  (`test_a_cheaper_quote_arriving_later_does_not_rewrite_history`).
- **Ruled out by construction.** Postgres `now()` is not involved: no
  `server_default` on any timestamp column (migration
  `alembic/versions/0019_repair_case_accepted_quote.py:35` — "No
  ``server_default`` anywhere"; ORM `services/db/repair_case_evidence.py:188`;
  the only `server_default`s under `services/db/` are non-timestamp —
  `repair_case.py:87,90`). Both stamps are Python `datetime.now(UTC)` at
  `services/api/routers/cases.py:463` (quote) and `:654` (acceptance), separate
  requests, separate transactions.
- **Forced reproduction, three deterministic ways:** exact tie → pack returns
  the later-arriving cheaper figure with `accepted_the_cheapest=False`;
  −5 ms inversion → same; **frozen clock through the real HTTP path** →
  the exact flake signature *plus* a self-inconsistency: POST returns
  `45500.50` while GET returns `39000.00` for the same case.
- **The `<` experiment (both sites swapped, suite run, reverted byte-identical):**
  all 63 tests in the 6 touching files pass either way (a coverage gap, not a
  licence); `<` does **not** fix the inversion case (the one that happens);
  it fixes only the exact tie (impossible in production across a 130 ms gap);
  and it introduces a new failure — with equal stamps the accepted quote is
  excluded from its own comparison set, so a case that HAS an acceptance reads
  `lowest_amount_at_acceptance_thb = None`, `accepted_the_cheapest = None`.
  **The defect is not the operator. This PLAN does not change `<=` to `<`.**
- **`latest_accepted_quote` — the higher-severity site (Cray ruled it in scope):**
  exact-tie acceptances, 40 reps → the **superseded** acceptance won 20/40; the
  tiebreak `accepted_id.desc()` is a random UUID, so "current" is a coin flip.
  Under a −5 ms step between two acceptances,
  `services/db/case_events.py::governed_case_facts` — **the DOA gate's input** —
  reported the superseded row (`45500.50 / ส.เจริญยนต์ / reason=None`) instead of
  the operator's actual current decision (`51000.00 / อู่ริมทางปากช่อง /
  "เจ้าแรกปฏิเสธงาน"`). A dearer garage chosen *with* a stated reason reads as
  "accepted the cheapest, no reason needed" — the audit trail inverts its own
  meaning. Production likelihood is lower (needs two acceptances < ~600 ms
  apart) but severity is higher: gate path, not read model. In test,
  `tests/api/test_accepted_quote_endpoint.py:194` carries ~0.9 %/run exposure.
- **Blast radius, stated honestly.** `lowest_amount_at_acceptance_thb` /
  `accepted_the_cheapest` are an audit **claim**, not currently a decision
  **input** — grep-verified zero consumers beyond the HTTP response models. The
  422 write-time control uses the unfiltered `min` (`cases.py:637`, measured
  immune); `governed_case_facts` reads `accepted_amount_thb` through the join.
  The correctness-path exposure is `latest_accepted_quote` → the gate, and
  `latest_closeout` → the month-end ฿ export.

## Design

### D1 — ELIMINATE the re-derivation; store the figure at write time *(SD-1 — RATIFIED by Cray, s196)*

`services/db/evidence_pack.py:74-79` argues the at-acceptance lowest is derived
rather than stored because "a stored copy would be one more thing that can go
stale." The measurements refute that argument **on its own terms**: the derived
value is wrong ~0.9 % of executions, while the stored value **cannot go stale by
construction** — `repair_case_quote` and `repair_case_accepted_quote` are
append-only with no update path, so the set of quotes existing at the moment of
acceptance is immutable the instant the acceptance row is written. The write
path already computes the correct figure at the only instant it is trivially
correct (`cases.py:637`, no timestamp filter, measured immune) and then discards
it. This PLAN persists it: a `lowest_amount_at_acceptance_thb` column on
`repair_case_accepted_quote`, written by the POST handler, read by the pack, the
GET endpoint, and the POST response. **Both** wall-clock comparisons
(`evidence_pack.py:163` and its duplicate `cases.py:686`) are deleted, not
patched. The POST-vs-GET self-inconsistency disappears because both read the
same stored fact.

The ORM's join-not-copy rule (`repair_case_evidence.py:180-183`) is untouched:
it protects the accepted quote's *own* amount/vendor from drifting. The new
column is different in kind — an aggregate over the *other* rows at an instant,
knowable cheaply and correctly only at that instant.

**Provenance (the SD-2 ruling — Cray, s196).** Legacy rows are backfilled with
the derived figure AND positively marked as reconstructed. The governing
principle (Cray's, carried verbatim in intent): NULL says "not captured"; a
plain backfilled number says `45,500.50` *with false authority* — strictly
worse for an audit trail; and storing a reconstructed guess as though it had
been recorded would contradict this PLAN's own thesis that a recorded claim
must be true at the moment it was recorded. Mechanism (drafter-designed under
the ruling's explicit delegation; veto-open): a typed basis column,
`lowest_at_acceptance_basis` TEXT NOT NULL, vocabulary
`{'recorded', 'reconstructed'}` pinned by a CHECK constraint, and **no default
at any layer** — no ORM default, no `server_default` — so every insert site
must state provenance explicitly and no default can silently absorb a
reconstructed row (ruling req 2). A typed column over a boolean for
extensibility and house style (`three_quote_basis` on
`RepairCaseRunLink` is the naming precedent). The basis travels **wherever the
figure is read** (ruling req 1): the `EvidencePack` dataclass, the
`AcceptedQuoteResponse` model, and the month-end export row.
**`accepted_the_cheapest` inherits the caveat explicitly** (ruling req 3): the
boolean is computed from the stored figure, so the SAME basis field governs
both — it sits adjacent to the figure *and* the boolean in every read surface,
and its `Field(description=...)` states that it qualifies both. No second
marker is added, deliberately: there is exactly one underlying stored fact, and
two markers could disagree, which would be a new way to lie. End-to-end
distinguishability is AC-10's oracle (ruling req 4). The ruling also revises
SD-2's cost analysis: the ~0.9 %-per-legacy-pair inversion risk is no longer
baked in silently — it is disclosed at the point of reading.

### D2 — "current row" = monotonic insertion order, not a clock

Add a DB-assigned, strictly-increasing `seq` (BIGINT, server-side
identity/sequence — race-free without read-modify-write) to the latest-wins
tables, and make readers order by `seq.desc()` as the **leading** key.
`evidence_pack.py:181-186` is honest that a true same-instant tie is ambiguous —
but under a *backward clock step* the operator's intent **is** recoverable: it
is insertion order, and the clock simply lied. `seq` encodes exactly that.
Covered picks: `latest_accepted_quote` (`evidence_pack.py:188-202`),
`latest_closeout` (`services/db/repair_case_closeout.py:134-162` — identical
shape, feeds the month-end export ฿ figure; **SD-3(a) — ratified in, s196**),
the drafter-observed `justifications[-1]` pick (`evidence_pack.py:135`, ordered
only by `entered_at` at `:123` — narrative fields only; **SD-3(b) — ratified
in, s196**), and the export's Python-side last-write-wins on `linked_at`
(`repair_spend_export.py:587`; **SD-3(c) — ratified in, s196**).

### D3 — discharge the original deferral: `sequence` on `step_results`

`load_run` (`services/engine/procedures/persistence.py:204`) orders by
`(created_at, step_result_id)` — the deferral's subject. This PLAN adds the
monotonic per-insertion `seq` and re-keys the ordering `(seq, step_result_id)`.
`suspended_step_result` (`persistence.py:233`) semantics are unchanged. Note
carefully: the un-defer **trigger did not fire** — see §Governance for the
honest reading.

### D4 — widen the guards to the two shapes the tree cannot currently see *(revised per R2 amendment, s196)*

Two ordering guards exist, and the split decides who owns what:

- `tests/services/db/test_load_run_ordering_guard.py` scans for exactly one
  shape (subscripts of a name bound to `load_run(...)`; docstring lines 19-27
  state this honestly) — structurally blind to both disease shapes here.
- `tests/services/db/test_run_analytics_ordering_guard.py` (PLAN-0088 Step 1)
  **already implements wall-clock `order_by` detection as proven AST
  machinery**: `_unwrap` strips `.desc()/.asc()/.nullsfirst()/.nullslast()`,
  `_orders_by_wall_clock` matches attribute/name sort keys against a
  `_WALL_CLOCK` set, exempts `date_trunc`-bucketed keys (the wall clock as a
  function *argument* is fine), catches raw columns named inside `sa.text(...)`,
  and carries its own fires-on-what-it-forbids pinning test. Its only limits are
  scope (`_MODULE` = `services/db/run_analytics.py`, one file) and vocabulary
  (`_WALL_CLOCK = {started_at, created_at, updated_at}`).

**The pick-shape half of this PLAN is therefore a scope + vocabulary widening
of that existing proven guard, not new AST machinery**: point the scan at all
of `services/`, extend `_WALL_CLOCK` with `{entered_at, accepted_at, opened_at,
linked_at, occurred_at, fired_at}`, and keep `_orders_by_wall_clock`'s existing
exemptions rather than reinventing them. The run-analytics guard's machinery
**owns** the widened scan — it is the one that already knows how to unwrap sort
keys and exempt bucketing. The existing single-module zero-hit test stays as-is
(a stricter, allowlist-free local rule for the analytics substrate); the
widened `services/`-wide test lands alongside it, allowlist-backed. The
load_run guard is **not** the home of the `order_by` scan — it keeps the
positional-read rule (fate per SD-4).

**The comparison-shape half is unaffected by the amendment**: that machinery
genuinely exists nowhere, and it is new — a cross-row stored-timestamp
comparison (`q.entered_at <= accepted.accepted_at`) has no "position" and no
`order_by` call for either existing guard to find. General "wall-clock
comparison" detection is a much harder AST problem and is **not attempted** —
a guard that matches nothing is worse than none. The new check pins the
concrete comparison shape, homed alongside the widened `order_by` guard, with:

- pinning positives that are **frozen snippets of the exact pre-fix code
  shapes** from `evidence_pack.py:163` and `:188-202` (precedent:
  `test_the_guard_fires_on_the_pattern_it_forbids` — both existing guards carry
  one);
- negative fixtures for the fixed shapes (an order solely by `seq.desc()`; a
  stored-field read; a request-parameter `as_of` comparison in the
  `cases.py:384` shape, which is a legitimate view-as-of feature);
- an audited allowlist ledger for every surviving `order_by` hit, each entry
  named with a reason (the `_POST_SCAFFOLD_DONOR_FILES` golden-donor
  precedent). The measured ledger — the AC-7 baseline — is in §Coverage.

### D5 — every regression test FORCES a tie or an inversion

A happy-path test passes 99.1 % of the time today and proves nothing. Every
test this PLAN adds uses the proven frozen-clock shape — monkeypatch
`services.api.routers.cases.datetime` (and the persistence module's clock for
D3) with a `datetime` subclass whose `now()` is frozen or steps backwards —
**through the real HTTP path** (real producer → real consumer, CLAUDE.md §8).
Each test is run RED against pre-fix code and GREEN after; both runs are
captured as evidence. Restoration probes restore from a scratch copy, never
`git checkout` (which wipes the edit under test and manufactures a false PASS).

## Coverage — what this PLAN fixes vs knowingly leaves

| Site | Disposition |
|---|---|
| `services/db/evidence_pack.py:163` comparison | **ELIMINATED** (D1 — reads stored column) |
| `services/api/routers/cases.py:686` duplicate comparison | **ELIMINATED** (D1) |
| `services/db/evidence_pack.py:188-202` `latest_accepted_quote` | **FIXED** — `seq.desc()` leading key (D2) |
| `services/db/repair_case_closeout.py:134-162` `latest_closeout` | **FIXED** — SD-3(a) RATIFIED by Cray (s196) |
| `services/db/evidence_pack.py:135` `justifications[-1]` | **FIXED** — SD-3(b) RATIFIED by Cray (s196); narrative-only severity — the gate-relevant bool `has_sole_source_justification` is order-insensitive |
| `services/engine/procedures/persistence.py:204` `load_run` | **FIXED** — `(seq, step_result_id)` (D3; the original deferral) |
| `services/api/routers/runs.py:296` `/runs` `started_at.desc()` + `services/api/static/assets/view-map.js:364` `CAP = 5` | **KNOWINGLY LEFT** on the wall clock. STATUS names this PLAN as their owner; ownership is discharged by this recorded decision: both render newest-first rows a human reads; a backward step can transiently reorder adjacent rows in a display list; no correctness consumer exists. |
| Quote/justification list orderings feeding display tuples (`cases.py:525,534,573`; `evidence_pack.py:114`) | **KNOWINGLY LEFT** — display order of lists |
| `services/db/repair_spend_export.py:587` last-write-wins over ascending `linked_at` (dict overwrite at `:590-602`) | **FIXED** — SD-3(c) RATIFIED by Cray (s196): `repair_case_run_link` gains a `seq` in `0023` and the export re-keys on it. Recorded justification (the reasoning the ratification rests on): drafter-verified NOT display, confirmed by Code on disk — the in-code comment (`:593-595`) says "the last write wins … the case's current position"; same disease shape, implemented in Python. |
| The remaining wall-clock `order_by` sites under `services/` | **ENUMERATED — complete for the chosen vocabulary.** The R2 probe measured the full widened-scan hit list (ledger below). The limit is stated plainly: the extended `_WALL_CLOCK` set is nine hand-picked column names, so a timestamp column outside that vocabulary is invisible to the scan — the same species of limit that quietly falsified the old enumeration (§Governance). The completeness claim is scoped to the vocabulary, deliberately and visibly; the scan cannot back a broader one. |

### Measured widened-scan ledger (R2 probe, s196 — the AC-7 baseline)

The existing run-analytics guard machinery, pointed read-only at all of
`services/` with the extended `_WALL_CLOCK` vocabulary, flags **exactly 12
sites** (as-given measurement; in-memory patch, restored in a `finally`, no
files touched). The guard reports the line where the query-chain *expression
begins*, so its numbers sit ~2 above the argument lines cited elsewhere in this
PLAN — `evidence_pack.py:191` ≡ the `:188-202` pick, `repair_case_closeout.py:151`
≡ the `:134-162` pick, `persistence.py:202` ≡ the `:204` argument,
`repair_spend_export.py:569` ≡ the `:587` `order_by`. **Same sites, not new
ones.** With the guard's **current** vocabulary the same repo-wide scan yields
exactly 2 hits — see §Governance for why that matters.

| # | Guard-reported site | Disposition |
|---|---|---|
| 1 | `services/engine/procedures/persistence.py:202` (`load_run`) | **FIXED** (D3 — re-keyed `(seq, step_result_id)`; scan goes silent) |
| 2 | `services/db/evidence_pack.py:191` (`latest_accepted_quote`) | **FIXED** (D2 — orders solely by `seq.desc()`, a unique key needing no tiebreak; scan goes silent) |
| 3 | `services/db/repair_case_closeout.py:151` (`latest_closeout`) | **FIXED** — SD-3(a) RATIFIED (s196); scan goes silent |
| 4 | `services/db/evidence_pack.py:121` (justifications ordering feeding the `[-1]` pick at `:135`) | **FIXED** — SD-3(b) RATIFIED (s196); scan goes silent |
| 5 | `services/db/repair_spend_export.py:569` (`governed_by_case` last-write-wins on `linked_at`) | **FIXED** — SD-3(c) RATIFIED (s196); the export re-keys on `repair_case_run_link.seq`, scan goes silent |
| 6 | `services/api/routers/runs.py:296` (`/runs` newest-first) | **ALLOWLISTED** — display-only projection (decision recorded above) |
| 7 | `services/api/routers/cases.py:250` (`/cases` list, `opened_at.desc()` + truncating `limit`) | **ALLOWLISTED** — display list ordering (drafter-verified) |
| 8 | `services/api/routers/cases.py:523` (quotes list) | **ALLOWLISTED** — display list ordering (drafter-verified at the `:525` argument) |
| 9 | `services/api/routers/cases.py:532` (justifications list) | **ALLOWLISTED** — display list ordering (drafter-verified at the `:534` argument) |
| 10 | `services/api/routers/cases.py:571` (quotes list) | **ALLOWLISTED** — display list ordering (drafter-verified at the `:573` argument) |
| 11 | `services/db/case_events.py:80` (`governed_case_facts` case ordering) | **ALLOWLISTED** — ordering exists for projection-fingerprint stability, carries a deterministic `case_id` tiebreak, and does not change WHICH facts are reported (drafter-verified at `:82`) |
| 12 | `services/db/evidence_pack.py:112` (quotes ordering feeding the display tuple) | **ALLOWLISTED** — display order; the `min()` aggregates over it are order-insensitive (drafter-verified at `:114`) |

Post-fix expected state — single and unconditional, every SD-3 pick ratified
s196: **5 sites silent (#1–#5) + 7 allowlist entries (#6–#12)**. The executor
confirms every allowlist reason against the surrounding code at allowlist
time; finding a correctness consumer behind a "display" entry is
rejection-grade.

## Acceptance Criteria

Every AC names its proving artifact and how it is proven to have RUN. A skipped
DB test is never satisfaction — see AC-9. Each regression AC states the
counterexample check applied: the concrete restored-defect under which its
oracle goes RED.

- [x] **AC-1 — Stored figure; POST and GET agree under a lying clock.** New
  frozen-clock scenario test(s) in `tests/api/test_accepted_quote_endpoint.py`:
  real HTTP writes with the acceptance stamped at-or-before the quote (tie AND
  −5 ms inversion fixtures); assert the response figure is the write-time `min`
  (the `45500.50` shape, never `39000.00`), and POST == GET for the same case.
  *Counterexample applied:* restoring the `<=` derivation at either read site
  makes the fixture's derived answer differ from the stored one → RED. *Run
  evidence:* captured RED output against pre-fix code (this test reproduces the
  reported flake deterministically today) + GREEN after; pytest node shown
  `PASSED`, not `SKIPPED`.
- [x] **AC-2 — The accepted quote is never excluded from its own set.**
  Equal-stamp fixture, single quote accepted: `accepted_the_cheapest is True`
  and the stored figure equals the accepted amount — never `None`-with-an-
  acceptance. *Counterexample applied:* the rejected `<` variant reads
  `None`/`None` here → RED. This pins the boundary semantics the 63 existing
  tests left unpinned — as a semantics pin on the stored value, not on an
  operator choice.
- [x] **AC-3 — The gate input reports the operator's current decision.**
  Double-acceptance via real HTTP with the second stamped −5 ms *and* an
  exact-tie variant: `governed_case_facts` (`services/db/case_events.py:68-115`)
  reports the **last-inserted** acceptance's amount/vendor/reason (the
  `51000.00 / dearer garage / reason present` shape). With `seq` this is
  deterministic — a single assertion replaces the 20/40 coin flip.
  *Counterexample applied:* restoring `accepted_at.desc()` as the leading key
  makes the superseded row win the inversion fixture → RED.
- [x] **AC-4 — Month-end export under a lying clock** *(both halves locked —
  SD-3(a) and SD-3(c) ratified s196)*: (a) two closeout
  keyings, second stamped −5 ms; the export/endpoint
  total reads the newest keying — *counterexample:* `entered_at.desc()`
  restored → RED. (b) A provisional
  row → ratification pair with the ratification stamped −5 ms; the export's
  `governed_by_case` shows the ratification's outcome — *counterexample:*
  last-write-wins over ascending `linked_at` restored → RED. Artifacts: forcing
  tests alongside `tests/api/test_closeout_endpoint.py` /
  `tests/services/db/test_repair_spend_export.py`.
- [x] **AC-5 — `load_run` returns execution order under a backward-stepping
  clock.** Step results persisted through the real save path with a
  monkeypatched clock that steps backwards mid-run; `load_run` returns execution
  order; `suspended_step_result` behaviour unchanged. *Counterexample applied:*
  restoring `order_by(created_at, ...)` flips the order in this fixture → RED.
  This is the deferral's subject, discharged.
- [x] **AC-6 — Migration `0023` + backfill.** Alembic head is `0022`
  (`alembic/versions/0022_run_link_three_quote_basis.py`); the new migration is
  `0023`, **additive-only** (append-only tables may hold live dev/demo data — no
  rewrites of existing values, downgrade drops only the new columns). Upgrade on
  a DB holding pre-migration rows, including an adversarial inverted pair,
  yields: every acceptance row's stored figure populated via the derive-once
  ∪ {accepted quote itself} reconstruction AND stamped
  `lowest_at_acceptance_basis = 'reconstructed'` (the SD-2 ruling); the basis
  column is NOT NULL with **no ORM default and no `server_default`** (pinned by
  the migration test + `test_schema_parity.py` / `test_migration_orm_lockstep.py`
  — the schema half of ruling req 2); legacy `seq` order equals
  `(accepted_at, accepted_id)` (today's reader's answer — behavioural
  continuity for existing data); new inserts strictly increasing. Artifacts: `alembic/versions/0023_*.py` + a migration
  test following the `tests/services/db/test_repair_case_evidence_migration.py`
  convention; `test_migration_orm_lockstep.py` and `test_schema_parity.py`
  green. *Run evidence:* nodes `PASSED`, not `SKIPPED`.
- [x] **AC-7 — The guard sees the disease's next instance (widened existing
  machinery, pinned to the measured baseline).** (i) *Pick shape:* the
  run-analytics guard's machinery (`_unwrap` / `_orders_by_wall_clock`,
  existing exemptions kept) widened per D4 to scope `services/` + the extended
  `_WALL_CLOCK` vocabulary. **Against the pre-fix tree the scan yields exactly
  the 12 sites in the §Coverage ledger** — a run reporting fewer means the scan
  or vocabulary was narrowed to what already passes, which is the fake-done
  form and a rejection, not a pass. Against the post-fix tree every hit is
  either silent-because-fixed (the seq-keyed picks) or in the allowlist with
  its ledger reason (expected state per §Coverage, single and unconditional —
  every SD-3 pick ratified s196: **5 silent + 7 allowlisted**).
  (ii) *Comparison shape:* the new check fires on a frozen
  snippet of the exact pre-fix `evidence_pack.py:163` shape and stays silent on
  the stored-field read and the `as_of` request-param shape (`cases.py:384`).
  (iii) The existing single-module run-analytics test and the load_run
  positional-read rule (retained per SD-4's ratified outcome) remain green. **Widening only to the
  `step_results` pattern does not satisfy this AC.** *Anti-vacuity oracle:* the
  pinning positives + the pinned 12-hit pre-fix baseline (precedent: both
  guards' `test_the_guard_fires_on_the_pattern_it_forbids`).
- [x] **AC-8 — Governance reconciled, honestly worded.** `docs/STATUS.md` §'Active TODOs'
  and the guard docstring's deferral section rewritten per §Governance below;
  classification is `superseded by new info` (CLAUDE.md §6), **not** "was an
  error" — the evidence-pack sites postdate the enumeration (PLAN-0096 Step 8,
  migration `0019`, 2026-07-30). The PLAN does **not** claim the un-defer
  trigger "fired" — see §Governance for the literal-wording engagement. *Oracle,
  stated honestly:* wording has no mechanical oracle; the proof is the PR diff
  plus Cray's ratification of the exact text. (Per the accelerator clause, the
  bold-first licence does NOT extend to this AC.)
- [x] **AC-9 — Offline gate at CI scope; skips surfaced.** Full `pytest tests/`,
  `mypy --strict services/`, `ruff check` — green at CI scope, not the changed
  subset. Every DB-backed node named by AC-1…AC-6 shown `PASSED` against the
  real dev Postgres (Docker Desktop, host port 5442; a worktree has no `.env`,
  so DB env must be exported or the run made from a checkout that has one — a
  silent skip is a rejection condition). Evidence: pytest summary lines for the
  named nodes + a `-rs` skip report showing none of them among the skips.
- [x] **AC-10 — A reconstructed figure is distinguishable from a recorded one,
  end to end** *(the SD-2 ruling's req 1 + req 4)*. Migration applied over a
  legacy (pre-`0023`) acceptance fixture: `GET /accepted-quote` **and** the
  month-end export row for that case read `basis = 'reconstructed'`; a new
  acceptance written through POST after the migration reads
  `basis = 'recorded'` through POST, GET and the export. In every one of those
  read surfaces the basis field sits adjacent to both the figure and
  `accepted_the_cheapest`, and its `Field(description=...)` names **both** as
  covered (req 3 — the marked-number-feeding-an-unmarked-boolean failure mode).
  *Counterexample applied:* if the basis defaulted to `'recorded'` at any
  layer, the legacy fixture would read `'recorded'` → RED (the schema half of
  the no-default pin is AC-6's). *Run evidence:* real HTTP path; nodes
  `PASSED`, not `SKIPPED`.

## Out of Scope

- ❌ Changing `<=` to `<` anywhere — measured to fix nothing that occurs and to
  break the equal-stamp case (see Evidence).
- ❌ Code changes to the `/runs` display ordering (`runs.py:296`) or
  `view-map.js` `CAP = 5` — **in scope as a recorded decision** (Coverage
  table: knowingly left, display-only), out of scope as code.
- ❌ Display-list orderings (quotes/justifications/vendors tuples).
- ❌ General wall-clock-comparison AST detection — the guard pins two concrete
  shapes; an overreaching guard matches nothing or everything.
- ❌ Host clock remediation (NTP/chrony on the dev box) — host-state (§8 gate),
  and the fix must not depend on the clock behaving.
- ❌ UI changes — grep-verified zero UI/JS consumers of the affected fields.
- ❌ Any update/delete path on the append-only tables.
- ❌ Wall-clock `order_by` sites invisible to the widened scan because their
  column names fall outside the chosen nine-name `_WALL_CLOCK` vocabulary —
  the ledger's completeness is vocabulary-scoped (see §Coverage); a future
  timestamp column joins the vocabulary, or it joins the blind spot.

## Steps

### Step 1: Forcing tests first — see the RED
Write the frozen/stepping-clock tests for AC-1, AC-2, AC-3, AC-4 (both halves)
and AC-5, using the proven monkeypatch shape through the real HTTP path. **Pre-committed pass/fail:** each named test is RED against pre-fix
code *for the stated reason* (assertion mismatch on the forced fixture — not
ERROR/collection failure); output captured as the AC's RED evidence. Cheapest
gate first; this step touches no production code.

### Step 2: Migration `0023`
Add `lowest_amount_at_acceptance_thb` (`Numeric(14,2)`) + the typed
`lowest_at_acceptance_basis` provenance column (D1 §Provenance — NOT NULL, no
default at any layer, CHECK-pinned vocabulary) + `seq` (BIGINT, server-assigned
monotonic) on the locked-scope tables: `repair_case_accepted_quote`,
`repair_case_closeout`, `repair_case_justification`, `repair_case_run_link`,
`step_results` — all SD-3 picks ratified s196; nothing in `0023` is
contingent. Backfill legacy
rows: figure via derive-once ∪ {accepted quote itself}, stamped
`basis = 'reconstructed'` (the SD-2 ruling); `seq` in each table's current
reader's order (`(accepted_at, accepted_id)` / `(entered_at, closeout_id)` /
`(linked_at, primary key)` for the run-link table /
`(created_at, step_result_id)`; the justification table per its current
reader, deterministically tiebroken by primary key). Write the migration test
per AC-6. **Pass/fail:** AC-6's artifacts green, `PASSED` not `SKIPPED`.

### Step 3: Re-key the code
POST handler persists the write-time `min` (`cases.py:637` already computes it)
together with an explicit `basis = 'recorded'`; pack + GET + POST response read
the stored column and carry the basis adjacent to the figure and
`accepted_the_cheapest` (D1 §Provenance; the export row likewise); delete both
comparisons (`evidence_pack.py:163`, `cases.py:686`); re-key
`latest_accepted_quote`, `latest_closeout` and the justification pick on `seq`
leading, and the export's `governed_by_case` ordering on
`(case_id, RepairCaseRunLink.seq)` in place of `linked_at` — all SD-3 picks
ratified s196; re-key `load_run` on `(seq, step_result_id)`. **Pass/fail:** Step 1
tests flip GREEN; the 63 pre-existing tests in the 6 touching files stay green;
a grep of `services/` finds zero cross-row stored-timestamp comparisons of the
eliminated shape outside the `0023` backfill.

### Step 4: Widen the guards
Implement D4: widen the run-analytics guard's existing machinery (scope +
vocabulary, exemptions kept) and add the new comparison-shape check + pinning
tests + the allowlist ledger. The pre-fix 12-hit baseline (the AC-7 narrowing
tripwire) is captured at the **Step 1 boundary** — run the widened scan against
the pre-fix tree (or the branch-base ref) *before* Step 3 lands, and keep the
output with the RED evidence; at Step 4 time the live tree is already
post-fix, so a Step-4-only scan cannot substitute for it.
**Pass/fail:** AC-7 in full — positives fire, negatives stay silent, the
pre-fix scan matches the ledger exactly, the post-fix scan is
clean-or-allowlisted-with-reason.

### Step 5: Governance edits (Cray-gated)
Apply the §Governance wording to `docs/STATUS.md` §'Active TODOs' and the guard docstring
**only after Cray ratifies the exact text** at PLAN review or PR review.
**Pass/fail:** AC-8 — diff matches the ratified wording.

### Step 6: Full gate + PR
Run the offline gate at CI scope (AC-9), collect the RED/GREEN evidence pairs
and the skip report, open the PR (Code commits; branch + PR per CLAUDE.md §7).
**Pass/fail:** AC-9 in full.

## Verification

- Every regression oracle is a **forced** tie/inversion (D5): its RED-before /
  GREEN-after pair is the proof it can detect the defect it guards, captured at
  the Step 1 → Step 3 boundary. A restoration probe restores from a scratch
  copy, never `git checkout`.
- The guard's verification is its own pinning test (AC-7): frozen pre-fix
  snippets MUST be flagged, fixed shapes MUST NOT be.
- DB-backed proof means `PASSED` against the real Postgres — a `SKIPPED` node
  satisfies nothing (AC-9's `-rs` report is the check).
- AC-8 has no mechanical oracle and says so; its gate is Cray's ratification of
  exact wording.

## Governance — the deferral, engaged honestly

The deferral lives in two places: `docs/STATUS.md` §'Active TODOs' and the guard docstring
(`tests/services/db/test_load_run_ordering_guard.py:29-49`). Its trigger reads:
*"if a correctness path ever starts depending on either ordering, the
sequence-column PLAN stops being optional."*

**The trigger did not fire.** "Either ordering" is literally enumerated —
`load_run`'s `order_by(created_at, ...)` and the `/runs` list's
`started_at.desc()` — and both remain display-only today, exactly as s169's
first real-case reading found (SD-8 = ELIMINATE). The claim this PLAN makes is
different and weaker-but-sufficient: **the safety-margin *argument* no longer
holds, because its enumeration was subsystem-scoped and, read repo-wide, is now
false.** Wall-clock dependence was later built on correctness paths the
enumeration never anticipated — comparisons with no "position" to scan
(`evidence_pack.py:163`), and latest-wins picks feeding the DOA gate
(`evidence_pack.py:188-202` → `case_events.py:68-115`) — by PLAN-0096 Step 8 /
migration `0019` (2026-07-30), i.e. **after** the docstring was written. Per
CLAUDE.md §6 this is classified **`superseded by new info`**, not "was an
error": the enumeration was correct when written and the reasoning lineage is
kept.

The R2 probe (s196) sharpens the classification with a measurement: the
run-analytics guard machinery pointed repo-wide with its **current** vocabulary
(`{started_at, created_at, updated_at}`) flags **exactly 2 hits** —
`runs.py:296` and `persistence.py:202` — precisely the pair the docstring
enumerated. The old enumeration was not sloppy: it was correct *for its column
vocabulary* as well as for its subsystem. What changed is that later-built
tables stamp differently-named columns (`entered_at`, `accepted_at`,
`linked_at`, …) on correctness paths; the extended-vocabulary scan finds 12
(§Coverage ledger). That is the precise sense in which the enumeration is
`superseded by new info`.

**Proposed replacement for that Active TODO entry** (Cray ratifies exact text):

> - [x] ~~DEFERRED: a monotonic `sequence` column on `step_results`~~ →
>   **PLAN-0099 drafted (s196)** — the deferred sequence-column PLAN, widened:
>   store-at-write for the at-acceptance figure (+ reconstructed-vs-recorded
>   provenance per the SD-2 ruling), `seq`-keyed latest-wins picks
>   (`latest_accepted_quote` → DOA gate; closeout, justification + the export's
>   run-link pick all ratified in, SD-3 a/b/c), `load_run` re-keyed,
>   guard widened to comparison + pick shapes. The un-defer trigger did NOT
>   literally fire; its enumeration was superseded by new info (evidence-pack
>   sites, 2026-07-30). `/runs` + `view-map.js` CAP=5: knowingly left,
>   display-only (decision recorded in PLAN-0099 Coverage).

**Guard docstring:** the "deferral STANDS" paragraphs (lines 29-49) are
rewritten to record discharge-by-PLAN-0099 and the widened scope; the
positional-read rule itself is **retained with a rewritten rationale**
(SD-4 — RATIFIED by Cray, s196).

## Surfaced decisions (statuses recorded per Cray's s196 rulings)

- **SD-1 — Store-at-write vs monotonic-derivation — ✅ RATIFIED by Cray (s196):
  store-at-write.** The recommendation became the decision; D1 stands as
  drafted (the staleness-argument refutation is recorded there). *Original
  question, for the record:* persist the write-time figure, or keep a
  derivation keyed on monotonic ids — the alternative bought the same truth
  with strictly more machinery.
- **SD-2 — Backfill semantics for legacy acceptance rows — ✅ RULED by Cray
  (s196), as a THIRD option neither drafted alternative offered: backfill the
  derived value AND positively mark it reconstructed.** Governing principle
  (carried here because it is the principle, not a preference): NULL says "not
  captured"; a plain backfilled number speaks *with false authority* — strictly
  worse for an audit trail; and storing a reconstructed guess as though it had
  been recorded would contradict this PLAN's own thesis — a recorded claim must
  be true at the moment it was recorded. Four binding requirements, all
  AC-covered: (1) provenance readable **where the figure is read** — response
  models + export row, not only a table column (AC-10); (2) no default of
  `recorded` — reconstructed rows positively marked (AC-6 schema pin + AC-10
  counterexample); (3) anything derived from a reconstructed figure inherits
  the caveat — `accepted_the_cheapest` is governed by the same basis field,
  adjacent in every read surface, with the non-marking-of-a-second-field
  reasoning stated in D1 §Provenance (one stored fact; two markers could
  disagree); (4) end-to-end distinguishability proven through the real HTTP
  path + export (AC-10). Mechanism (typed `lowest_at_acceptance_basis` column)
  is drafter-designed under the ruling's explicit delegation — veto-open.
  Cost analysis revised by the ruling: the ~0.9 %-per-legacy-pair inversion
  risk is disclosed at the point of reading rather than baked in silently.
- **SD-3(a) `latest_closeout` + SD-3(b) `justifications[-1]` — ✅ RATIFIED by
  Cray (s196): include both.** Locked scope: Coverage ledger #3/#4 are now
  unconditionally FIXED, AC-4(a) is no longer contingent, and their `seq`
  columns are part of `0023` (Step 2). Original rationale preserved: one
  migration, one pattern, one forcing-test family; leaving the export's ฿
  figure on a coin-flip tiebreak while fixing its documented sibling
  (`repair_case_closeout.py:141-146` cross-references it) would be incoherent.
- **SD-3(c) `repair_spend_export.py:587` — ✅ RATIFIED by Cray (s196):
  include.** `repair_case_run_link` gains a `seq` in `0023`, and the export's
  `governed_by_case` stops last-write-winning on `linked_at`. Provenance,
  preserved honestly as history: the site was drafter-surfaced during the R2
  revision and Code-confirmed on disk as a latest-wins pick in Python clothing,
  NOT a display ordering (`governed_by_case` dict overwrite at `:590-602`; the
  in-code comment at `:593-595` states last-write-wins — under a backward step
  between a provisional gate row and its ratification, the month-end export
  shows the provisional outcome). Code recommended include on those grounds
  (a correctness path the partner's accounting reads; the same widened scan
  already flags it, ledger #5; one `seq` column, no new machinery, no second
  migration); **Cray ratified — it is now Cray's decision.** AC-4(b) is its
  forcing test; the ledger's post-fix arithmetic is the single unconditional
  5 + 7.
- **SD-4 — Fate of the positional-read guard rule — ✅ RATIFIED by Cray (s196):
  retain, with rewritten rationale** (select-by-STATUS expresses intent;
  insurance through the migration window). Folded into §Governance (the guard
  docstring edit) and AC-7(iii).
