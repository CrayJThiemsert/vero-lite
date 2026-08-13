# PLAN-0104: Teach the NL query engine `count` WITH `group_by` (PLAN-0100 D-4, option (a))

**Status:** Complete (8/8 ACs closed, session 228)
**Owner:** Claude Code (execution) · Cray (SD rulings; the one §8 go)
**Created:** 2026-08-13
**Related ADRs:** none new proposed — ADR-0032 D1 (the demo→pilot wedge this
feature serves), ADR-0021 (measured-kind context: a count is kind-less and
unit-less by construction, which SD-3 leans on). The governing ruling is not an
ADR: **PLAN-0100 D-4, RULED s217 (Cray, typed): option (a), teach the engine**
(`docs/STATUS.md`, PLAN-0100 residuals row; `docs/plans/done/0100-*.md`).

> **Drafting provenance (ADR-012 D4.3 / ADR-013 D1).** Drafted by the in-harness
> `plan-drafter` subagent from a Code-authored dispatch (2026-08-13, session
> 226). Every `file:line` cited below was **opened and read by the drafter this
> session** unless explicitly marked *[claim — confirm at execution]*; the
> dispatch's Tier-2 (agent-reported) figures were independently re-verified
> where cited, or carried as marked claims where not. Independent review: Code
> at PR; ratification: Cray. Author≠reviewer separation: **INTACT**.
> Uncommitted draft — Code commits per ADR-009 D2.

---

## The problem, precisely (read before the steps)

The engine executes `max`/`min`/`avg`/`sum` **with** `group_by` end-to-end.
The cardinality case — *"how many events per battery?"* — is unrepresentable,
and the refusal is **enforced at three independent layers**, so no single edit
changes observable behaviour:

1. **The system prompt instructs the model never to emit the pair.**
   `services/engine/nl_query.py:393` — verbatim: *"If you set
   aggregate_property or group_by, operation must be max/min/avg/sum (never
   list/count)."* Relaxing the validator alone changes nothing observable.
2. **The shared validator rejects the pair** (`nl_query.py:536-549`), and its
   own comment (`:529-535`) says why: the deterministic aggregate is computed
   ONLY for `max/min/avg/sum`, so a `count` op would **silently drop** the
   grouping — the refusal guards a real execution gap. Relaxing it without
   building the execution half ships a silently-dropped grouping, worse than
   today's honest refusal.
3. **The result carrier cannot hold a grouped count.** `AggregateResult`
   (`nl_query.py:195-208`) requires `property: str` (no default) and its
   `groups: dict[str, float]` values are measures — a grouped count has **no
   property** and its group values are **cardinalities**. This is the core
   design problem (SD-1), not a plumbing detail.

Plus one blast-radius site outside the module: `run_query.py:_count`
(`services/engine/run_query.py:164-178`) contains a `query.group_by ==
"started_week"` branch that is **dead today for validated queries** (the shared
validator — reused at `run_query.py:123` — rejects the pair first) and, if
un-deadened, **answers "runs per week" with a single total** (`week_total =
sum(...)` → `RunQueryResult(matched=week_total, count=week_total)`). Worse
(verified this session): after relaxation, `count` + `group_by` over **any**
run-corpus dimension (`procedure_id`, `status`, `started_week` —
`run_query.py:68`) validates, and `_count`'s fall-through path collapses all of
them to a total — while `_run_query_schema` (`run_query.py:296-300`) **already
advertises** `operation ∈ {count,max,min,avg,sum}` × `group_by ∈ DIMENSIONS` to
the model. SD-2 owns this.

## Goal

Make *"how many X per Y?"* a first-class, deterministically-executed,
provably-grounded query: the translate stage may emit `operation: "count"` with
`group_by` (never with `aggregate_property`), the execute stage computes the
per-group cardinalities deterministically over the full matched set, the
grounding receipt carries them in the ruled result shape (SD-1), group keys are
relabelled to entity titles exactly as numeric aggregates are, and the phrased
answer names every group with its count. The run-corpus surface
(`/insights/query`) either gains the same capability or keeps refusing the pair
explicitly — it must never silently collapse a grouped count to a total (SD-2).
Everything except the live-model emission question is closed offline; the one
genuine unknown — whether the live model actually emits the pair once the
prompt rule is inverted — is settled by a single gated live run on MS-S1.

## Acceptance Criteria

None of these is satisfiable by mocking the seam it tests; guards get a
non-vacuity probe (plant the violation from a `/tmp` copy, see the RED,
restore — never restore from git).

- [x] **AC-1 — the validator admits exactly the new pair, nothing else.**
  `_validate_query` accepts `count` + `group_by` (with `aggregate_property`
  unset) and still rejects: `list` + `group_by`, `list` + `aggregate_property`,
  and `count` + `aggregate_property` — each with a corrective message that
  still nudges the retry loop. The existing
  `test_group_by_with_count_operation_is_rejected`
  (`tests/services/engine/test_nl_query.py:664-671`) is **rewritten into the
  acceptance test, not deleted**; the three remaining rejections each keep a
  named test. Offline.
- [x] **AC-2 — the scenario test drives the real producer into the real
  consumer on realistic simulated data (CLAUDE.md §8, binding).** A scenario
  test runs `answer_question` end-to-end against the **real energy synthetic
  adapter** (`verticals/energy/data_adapter/synthetic.py`) with the translate
  stage driven by a canned constrained-JSON response (the established offline
  pattern for this module — the stub is the *model transport*, never the
  execute/phrase seam under test): question "How many operational events are
  recorded for each asset?" → `count` + `group_by: asset_id` → the engine
  computes the per-asset cardinalities over all 13 events, relabels ids to
  titles via the real `_relabel_groups` path, sets `result_count` to the full
  matched count, and the phrased answer names **every** group with its exact
  cardinality. Expected groups (derived by the drafter from `synthetic.py`
  this session; **re-verify by hand at execution**, per `gold.yaml`'s own
  convention): Battery Bank A = 5, Inverter Unit A = 3, Battery Bank B = 3,
  Feeder Meter A = 2 (sums to 13). ⚠️ This AC deliberately does **not** claim
  the live model emits the pair — that is AC-7's, and only AC-7's, claim.
- [x] **AC-3 — ungrouped `count` is regression-frozen.** Every existing
  `count`-without-`group_by` test passes **unmodified**, and the flat count
  branch of `_fallback_answer` (`nl_query.py:1080-1081`) still serves the
  ungrouped case (a grouped count rides the aggregate branch instead —
  asserted by a test that an ungrouped count answer carries no group listing).
- [x] **AC-4 — the benchmark's own gold is repaired and the repair is
  guarded.** `SQL_EXPECT` (`benchmarks/nl_query_feasibility/text_to_sql.py:
  67-80`) reads `nl-02: ["13"]` and `nl-05: ["2"]` (today: `["11"]` / `["1"]`
  — stale by PLAN-0070's two added readings), **and** the cross-check test
  (`tests/benchmark/test_nl_query_text_to_sql.py:58-84`) is extended to score
  the real SQL results **against `SQL_EXPECT` itself** (today it asserts raw
  SQL numbers and never reads `SQL_EXPECT` — verified this session: the
  docstring claims validation the body does not perform, so the stale tokens
  pass silently; the fix makes the precondition read the SUT's output).
  Non-vacuity probe: replant `"11"`, see the RED. Offline.
- [x] **AC-5 — the run-corpus surface never silently collapses a grouped
  count.** Whichever way SD-2 is ruled, a test proves it: either (a) a grouped
  count over the run corpus returns per-group figures (per-week from
  `week_rollup`, per-procedure/status from `run_status_rollup`), or (b)
  `validate_run_query` refuses `count` + `group_by` with an explicit
  corrective message. **In both worlds** the test asserts that a
  `count`+`group_by="started_week"` query does **not** return a single-total
  `RunQueryResult` shaped like today's `_count` collapse — this AC is written
  to fail while `run_query.py:164-178` still folds groups into `week_total`.
  🔴 **Merge dependency (both SD-2 branches):** the shared-validator
  relaxation and this AC's change land in the **same PR** — there is no
  intermediate commit where the pair validates and `_count` collapses.
- [x] **AC-6 — the gold set gains the grouped-count case, offline.**
  `benchmarks/nl_query_feasibility/gold.yaml` gains a case (nl-13, category
  `group-count`) for the AC-2 question with `expected_operation: count`,
  `expected_count: 13`, and per-group expectations; the harness scorer
  (`benchmarks/nl_query_feasibility/harness.py:89-108`, today supporting only
  `{value}`/`{top}`) is extended to score a `groups` expectation, unit-tested
  in `tests/benchmark/test_nl_query_feasibility_gold.py` (which already
  constructs `AggregateResult`s). Gold values hand-verified against
  `synthetic.py` at execution. No synthetic event is added or changed (the
  energy events couple the existing gold — freezing them keeps nl-01..nl-12's
  values valid).
- [x] **AC-7 — the live model emits the pair, measured on MS-S1 (HOST-STATE —
  the one claim no fixture can settle).** Under a typed Cray §8 go (Step 7):
  (i) the raw translate output for the nl-13 question, recorded from the live
  run artifact, sets `operation: "count"` + `group_by` — a canned translate
  JSON explicitly does **not** satisfy this; (ii) the **full gold set (now 13
  cases) is re-measured** and the fresh accuracy recorded — the shared system
  prompt changed, so every previously recorded accuracy is non-comparable and
  is not cited as if current. Pass/fail is pre-committed in Step 7 before the
  run.
- [x] **AC-8 — gates and the frozen corpus.** Full `tests/` green, `mypy
  --strict services/` clean, ruff clean; `git diff` for
  `tests/services/engine/nl_query_ab_fixtures.py` is **empty** across every
  PR of this PLAN (see Out of Scope), and its `len(FIXTURES) == 27` assertion
  (`tests/services/engine/test_nl_query_ab_fixtures.py:36`) is untouched.

## Out of Scope

- ❌ **`tests/services/engine/nl_query_ab_fixtures.py` — untouched, byte for
  byte.** That corpus was pre-committed before PLAN-0051's completed live A/B,
  whose verdict is recorded (`docs/plans/done/0051-reason-then-structure-ab.md:7`
  — "NO LIFT either site; REJECT both variants"). Adding or editing a fixture
  would retroactively alter the corpus a finished pre-committed experiment was
  measured on. **No live A/B re-run is required by this item.**
- ❌ **Re-recording fixtures on MS-S1.** Refuted as circulated: neither fixture
  set is a recording — `gold.yaml:6-7` says every gold answer is "verified by
  hand", and the A/B corpus is hand-authored. Gold gains cases offline; what
  needs the live model is **evidence** (AC-7), not fixtures.
- ❌ **Any API/UI model change.** Verified this session: `NlQueryResponse`
  (`services/api/models/query.py:27-74`) exposes no aggregate field and the
  router mapping (`services/api/routers/query.py:30-46`) passes none — grouped
  numbers reach the user via the phrased `answer` plus the `structured_query`
  receipt, exactly as grouped numeric aggregates do today. This PLAN keeps it
  that way; exposing the aggregate over the API is a separate decision nobody
  has asked for.
- ❌ **The two-pass reasoning prompt** (`_translate_reasoning_messages`,
  `nl_query.py:443-469`). It belongs to the PLAN-0051 rejected experimental
  arm; its *structuring* call reuses `_translate_messages` wholesale
  (`nl_query.py:485` — verified), so it inherits the Step-6 prompt edit by
  construction, and its free-prose wording is left alone.
- ❌ **Extending `_infer_group_by` to count questions.** The Phase-B inference
  seam (`nl_query.py:896-915`) stays gated to `max`/`min` entity
  superlatives; whether "which asset has the most events?" should infer a
  grouped count is a different feature with its own evidence bar.
- ❌ **`list` + `group_by` / `list` + `aggregate_property` /
  `count` + `aggregate_property`** — all stay rejected (AC-1).
- ❌ **Any change to energy synthetic events** — the gold set is coupled to
  them; nl-13 is added against the data as it stands.

## Surfaced decisions — Cray's slots (recommendation ≠ ruling; nothing below is assumed by the steps)

> ✅ **ALL THREE SLOTS RULED s226 (Cray, typed)** — SD-1 = **(a)**, SD-2 = **(a)**,
> SD-3 = **NO (keep the bypass)**, each stamped in place below. Every ruling
> matched the drafted recommendation, so no Step re-shapes. **Nothing gates
> execution of Steps 1–6 any more.** Step 7 remains gated on its own typed §8
> go, which is a separate ask made at that step, never inherited from these.
> The rejected alternatives are kept as the reasoning lineage — do not
> re-litigate them.

- **SD-1 — What carries a grouped count?**
  ✅ **RULED (Cray, typed, s226): (a)** — `AggregateResult.property` becomes
  `str | None = None` with the construction-enforced invariant *"property is
  None iff operation == 'count'"*. Step 2 executes against this; (b), (c) and
  (d) below are recorded as the rejected alternatives, not re-litigated.

  `AggregateResult.property` is a
  required `str` with no meaning for a count, and `groups: dict[str, float]`
  values are measures, not cardinalities (`nl_query.py:195-208`). The §Frontier
  clause of the dispatch explicitly permits eliminating the wrong carrier
  rather than contorting it. Options, stated neutrally:
  - **(a) Make `property` optional (`str | None = None`) with the invariant
    "property is None iff operation == 'count'".** Blast radius (each site
    read this session): every existing constructor stays valid —
    `nl_query.py:810,846`, `run_query.py:210,244`, plus the test constructors
    in `tests/benchmark/test_nl_query_feasibility_gold.py` and
    `tests/services/engine/test_run_query_llm_stages.py`, all pass `property=`
    explicitly; `_phrase_aggregate` (`:1053-1067`) gains a count branch (it
    reads `aggregate.property` unconditionally today and `_AGG_LABEL` at
    `:1050` has no `count` entry); `_relabel_groups` (`:813-851`) works
    unchanged (its body is op-agnostic); `_fallback_answer` (`:1070-1085`)
    needs no change (the aggregate branch fires first); the API receipt is
    untouched (no aggregate field — see Out of Scope). Cardinalities ride as
    floats, but render exactly: `_fmt_num` (`:1042-1047`) prints `5.0` as
    `"5"`. One carrier feeds phrasing, relabelling, the benchmark scorer, and
    the run-corpus fallback (`run_query.py:384-386` calls `_phrase_aggregate`)
    with zero new seams.
  - **(b) A sentinel property value** (e.g. `""`) — rejected by both drafter
    and dispatch framing: it lies in the grounding receipt.
  - **(c) A separate result shape** (e.g. `GroupCountResult` with
    `groups: dict[str, int]`) carried on a new `NlAnswer` field. Type-honest
    (ints are ints; no invariant to police), but it duplicates every seam the
    moment it exists: a second relabel path, a second phrasing function, a
    second benchmark-scorer branch (`harness.py:84` reads `ans.aggregate`), a
    second `RunQueryResult` field, and a second thing the receipt consumer
    must know about.
  - **(d) A count-specific field on `AggregateResult` itself** (keep `property`
    required, add `count_groups`) — splits one result's data across two fields
    and still needs every phrasing/scoring branch of (c).

  **Recommendation: (a)**, with the invariant enforced at construction (the
  dataclass is frozen; a `__post_init__` check turns a miss into a loud
  error). *Why Cray:* the `AggregateResult` docstring is the system's public
  definition of what an aggregate *is* ("a number computed over a property");
  loosening that identity — versus keeping it strict and adding a sibling
  shape — is a design-identity call on the grounding receipt, not a
  judgment call the drafter should bury in a diff.
- **SD-2 — `run_query.py:_count`: fix in this PLAN, or scope out behind a
  guard?**
  ✅ **RULED (Cray, typed, s226): (a) — fix it here.** Step 4 executes the
  grouped-count path from the existing rollups. ⚠️ The hard merge dependency in
  AC-5 stands **unchanged and is not softened by this ruling**: the
  shared-validator relaxation and this fix land in the SAME PR — no
  intermediate commit may exist where the pair validates and `_count` still
  collapses groups to a total. The one marked claim survives the ruling: if the
  `/insights/query` response shape cannot carry grouped figures without an API
  change, **surface to Cray — this PLAN does not authorize widening scope.**

  Options:
  - **(a) Fix it here.** The substrate already computes grouped counts —
    `week_rollup` returns per-ISO-week `run_count` (`run_query.py:167-170`)
    and `run_status_rollup` per procedure×status (`:172-176`) — so `_count`
    can return per-group figures in the SD-1 carrier with **no new SQL**, and
    the deterministic fallback phrasing comes free via `_phrase_aggregate`
    (`:384-386`). Also removes a standing incoherence: `_run_query_schema`
    already advertises the pair to the model (`:296-300`), so today's design
    *invites* an emission the validator then refuses. One open detail, marked
    as a claim: the `/insights/query` response model's shape for grouped
    figures (`services/api/routers/insights.py:339,351` is the call site;
    the response model was not read this session — *[claim — confirm at
    execution]*).
  - **(b) Scope out, guard the surface.** `validate_run_query`
    (`run_query.py:116-144`) gains an explicit run-corpus rejection of
    `count` + `group_by` (exactly like its existing `list` rejection at
    `:126-131`), with a corrective message, plus the schema enum for
    `group_by` narrowed when the op is `count` if feasible.

  **Recommendation: (a)** — the fix is bounded, the data is already grouped,
  and (b) leaves the engine's two query surfaces giving contradictory answers
  to the same English question. **Either way the dependency is hard (AC-5):
  the shared-validator relaxation must not merge without (a) or (b) in the
  same PR** — otherwise "runs per week" becomes a wrong single-total answer
  the moment the validator relaxes, a strictly worse state than today's
  refusal. *Why Cray:* it is a scope call with a cost/risk trade (option (a)
  touches a PDPA-sensitive surface's response shape), and the dispatch names
  it as Cray's.
- **SD-3 — Does unit-coherence apply to a grouped count?**
  ✅ **RULED (Cray, typed, s226): NO — keep the existing structural bypass.** A
  grouped count counts *records*, not measures. Step 3's expected groups
  therefore stand as drafted (per-asset counts **include** transitions and
  alarms, not only readings), and no unit filter is synthesized for a count.

  Verified basis: the
  coherence seam is *already structurally bypassed* for count —
  `_apply_coherence` returns immediately unless
  `query.operation in _AGGREGATE_OPS and query.aggregate_property`
  (`nl_query.py:1023`), and count has neither. **Recommendation: keep that
  bypass — a count has no unit and no measured kind (ADR-0021: kind⟂unit
  attach to measures); it counts *records*, and synthesizing a unit filter
  would silently shrink the counted set** (e.g. "how many readings per
  battery" would silently drop the hz and ampere readings, returning a number
  that contradicts the same question asked ungrouped). The alternative —
  applying coherence when the counted type carries a `unit` property — is
  inventing a filter the question did not ask. *Why Cray:* this fixes what
  number the demo's flagship query returns (per-asset counts include
  transitions and alarms, not just readings); that is a product-semantics
  call, and if Cray rules the other way, Step 3's expected groups change.

## Steps

Sequenced so **every offline step precedes the host-state one**. Steps 2–4
land as **one PR** (the merge-dependency in AC-5; no intermediate commit may
relax the validator without the execution half and the run-corpus disposition).

### Step 1: Repair the benchmark's own gold before it is used as evidence (offline)

The live evidence run (Step 7) is untrustworthy until this lands: `SQL_EXPECT`
is stale by PLAN-0070's two added readings and would score two cases wrong on
the very run this PLAN needs.

- `benchmarks/nl_query_feasibility/text_to_sql.py:69` — `"nl-02": ["11"]` →
  `["13"]`; `:72` — `"nl-05": ["1"]` → `["2"]` (gold.yaml's hand-verified
  values at `:64` and `:103`; the DB's real counts asserted at
  `tests/benchmark/test_nl_query_text_to_sql.py:62-63`).
- Make the cross-check non-vacuous: extend
  `test_gold_values_cross_check_against_real_sql` to run the real SQL results
  through the same normalization `score_sql` uses (`text_to_sql.py:194-196`)
  and assert every `SQL_EXPECT` token appears — the guard must **read**
  `SQL_EXPECT`, not restate the numbers beside it.

Pass/fail (pre-committed): the extended test is RED against the stale tokens
(non-vacuity probe: plant `"11"` back from a `/tmp` copy, see the RED,
restore), green after; AC-4.

### Step 2: The carrier + deterministic grouped-count execution (offline)

**SD-1 is RULED (a), s226** — the carrier is the loosened `AggregateResult`,
so this Step executes exactly as drafted; the "re-shapes mechanically if Cray
rules (c)/(d)" conditional this paragraph carried is now moot and resolved:

- `AggregateResult.property` becomes `str | None = None` with the
  construction-time invariant (SD-1); docstring updated to define the count
  case explicitly.
- New `_compute_group_count(query, matched) -> AggregateResult`: overall
  `value = float(len(matched))`, `groups` = per-`group_by`-key cardinalities.
  A record whose group key is `None` counts in the total but joins no group —
  the exact convention `_collect_numeric` already uses (`nl_query.py:781-784`),
  stated here so it is a decision, not an accident.
- Orchestrator (`nl_query.py:1298-1303`): alongside the existing
  `_AGGREGATE_OPS` branch, a `count`-with-`group_by` branch computes the
  grouped count and passes it through the **same** `_relabel_groups` call, so
  ref-keyed groups (e.g. `asset_id`) surface as entity titles. `result_count`
  and `source_objects` semantics unchanged — a count's receipt is the full
  matched set (`:1305-1311`).
- Phrasing: `_phrase_aggregate` (`:1053-1067`) gains the count branch (no
  `property` to name; every group listed with its cardinality plus the
  total); `_AGG_LABEL` (`:1050`) is either extended or bypassed by that
  branch — execution's call, asserted by tests either way. The LLM phrase
  path needs no prompt change: it already receives the computed aggregate
  with the report-exactly instruction (`:1112-1118`).
- Unit tests for: grouped count over a ref key (relabelled), over an enum key
  (e.g. `severity` — no relabel), None-key handling, deterministic phrasing,
  and the AC-3 ungrouped-count freeze.

Pass/fail: new unit tests green; AC-3's regression clause holds.

### Step 3: The narrow validator relaxation + test rewrite (offline, same PR as Steps 2/4)

- `_validate_extras` (`nl_query.py:526-549`): admit exactly
  `operation == "count" and group_by and not aggregate_property`; keep the
  rejection (with corrective messages that still nudge the retry loop) for
  the three combinations AC-1 names. Update the comment at `:529-535` — its
  stated reason (the execution gap) is discharged by Step 2, and a comment
  guarding a gap that no longer exists is exactly the drift this repo's
  verify-hygiene rules exist to catch.
- Rewrite `test_group_by_with_count_operation_is_rejected`
  (`tests/services/engine/test_nl_query.py:664-671`) into the acceptance
  test; add the three named rejection tests.
- The AC-2 scenario test lands here, driving the full
  translate(stubbed transport)→execute(real)→relabel(real)→phrase(real
  fallback) chain on the real synthetic adapter.

Pass/fail: AC-1 + AC-2 evidence.

### Step 4: The run-corpus disposition (offline, same PR as Steps 2/3 — SD-2)

**SD-2 is RULED (a), s226** — so this Step builds grouped-count execution from
the existing rollups; the (b) refusal branch is not taken. _[The two-branch
wording this paragraph carried while the slot was open is resolved, not
deleted: (b) stays recorded in §Surfaced decisions as the rejected
alternative.]_ Either way the following holds and is unchanged by the ruling:
delete or subsume the now-un-deadened
`group_by == "started_week"` half of `_count` (`run_query.py:166-171`) so no
path folds groups into a single total, and add AC-5's test asserting the
collapse is impossible. If (a): confirm the `/insights/query` response shape
carries grouped figures (*the one unread surface — claim to confirm at
execution*); if it cannot without an API change, surface that to Cray before
widening scope — an API change is not authorized by this PLAN.

Pass/fail: AC-5 evidence, both directions of the branch taken recorded in the
PR body.

### Step 5: The gold case + harness `groups` scoring (offline)

- `harness.py:_aggregate_ok` (`:89-108`) gains a `groups` expectation:
  exact-match on relabelled keys and cardinalities (tolerance-free — counts
  are integers), unit-tested in `tests/benchmark/test_nl_query_feasibility_gold.py`
  alongside the existing `{value}`/`{top}` cases.
- `gold.yaml` gains nl-13 (category `group-count`, `ceiling: false`):
  "How many operational events are recorded for each asset?" —
  `expected_operation: count`, `expected_count: 13`,
  `expected_aggregate: {groups: {Battery Bank A: 5, Inverter Unit A: 3,
  Battery Bank B: 3, Feeder Meter A: 2}}`. Values hand-verified against
  `synthetic.py` at execution (drafter-derived this session; the hand-check
  is the gold set's own stated bar, `gold.yaml:6-7`).

Pass/fail: harness unit tests green; the new case scores `correct` against a
canned correct answer and `wrong` against a groups-collapsed one.

### Step 6: The prompt edit (offline-lintable, oracle-less — conservative by design)

**The accelerator clause does not cover this step: no test anywhere pins the
prompt string (verified this session — greps for the rule's substrings and for
test references to `_translate_messages` return nothing), so ambition here
buys confident wrongness.** The edit is minimal and single-site:

- `nl_query.py:389-393`: replace the blanket rule with one admitting the new
  pair — direction (final wording at execution, kept close to this): *"use
  'count' with group_by for how-many-per-\<thing\> questions; if you set
  aggregate_property, operation must be max/min/avg/sum; never combine 'list'
  with aggregate_property or group_by."* The OPERATION sentence's existing
  `group_by` guidance (`:390-392`) is adjusted to stop tying `group_by`
  exclusively to aggregate ops.
- The two-pass structuring call inherits this edit by construction
  (`:485` — it reuses `_translate_messages`); the reasoning-arm prose is out
  of scope.
- Verification here is honest about its limit: compiles, lints, and the
  existing offline suite green — **the prompt's only real oracle is Step 7's
  live run.** No offline claim is made that the wording works.

Pass/fail: gates green; the diff touches exactly the one prompt constant.

### Step 7: The live evidence run on MS-S1 (HOST-STATE — gated, last)

🔴 **Runs only after a typed Cray §8 go, requested for this step by name**
(CLAUDE.md §8: warming/running a model on MS-S1 is a host-state change; the
live run is *evidence*, the offline oracle is the gate; minimize live runs —
one warm + one benchmark sweep). Everything before this step is closed
offline first.

Pre-committed pass/fail, fixed here before the run:

1. **Emission (AC-7-i):** the recorded raw translate output for nl-13 sets
   `operation: "count"` + `group_by` (any valid `group_by`; `asset_id`
   expected). A retry-loop recovery to the pair still passes; a final
   emission without the pair fails.
2. **Scoring (AC-7-ii):** nl-13 scores `correct` under the Step-5 scorer.
3. **Re-measurement (AC-7-ii):** all 13 gold cases run; fresh per-case
   outcomes + accuracy recorded (a committed results artifact or `docs/logs/`
   thin summary naming numbers, method, model, date). The prior recorded
   accuracy is **retired as non-comparable** (shared prompt changed), not
   silently overwritten: the record states both the old figure and why it no
   longer applies. A previously-correct case going wrong is re-run once
   (the local backend is non-deterministic even at temp 0); a repeat failure
   is a defect investigated before merge, not noise.
4. No fixture is re-recorded; no A/B re-run (Out of Scope).

Pass/fail: the three numbered reads, against the run artifact.

✅ **EXECUTED s228 under Cray's typed §8 go, requested for this step by name.**
All four reads PASS; the record is
`benchmarks/nl_query_feasibility/RESULTS.md` §"Addendum — PLAN-0104 Step 7 live
evidence run" — **read it, not this summary**. Headline: nl-13 emitted
`operation:"count"` + `group_by:"asset_id"` on the first pass and scored
`correct`; **12/13** over the full gold set; the prior **11/12** (AC-9,
2026-06-16) is **RETIRED as non-comparable** for two independent reasons
(the shared prompt changed in #1149; the gold set grew 12 → 13). The lone miss
(nl-06) was re-run once per clause 3, failed again, and was **investigated
before merge**: it is the pre-existing, catalogued simple-list filter-omission
variance — #1149's diff leaves the FILTERS sentence byte-identical, and the
victim moved (AC-9's miss was nl-01, correct in this run) — **not a PLAN-0104
regression**. The addendum records the one alternative this single sweep cannot
refute to zero.

## Verification

- **Offline gates (the gate):** full `tests/` green (including the rewritten
  validator tests, the AC-2 scenario, AC-5's collapse-impossible test, and
  the benchmark unit tests), `mypy --strict services/` clean, ruff clean —
  scope per the standing rule that the offline gate matches CI scope.
- **Non-vacuity probes:** AC-4's replanted stale token; AC-5's probe = a
  `/tmp`-copy revert of the `_count` disposition must redden the collapse
  test; AC-2's scenario must redden if the grouped branch is severed (e.g.
  the probe mutation drops the `groups` population — a behaviour-changing
  mutation, named output: the per-group listing disappears from the answer).
- **Frozen-corpus check:** `git diff --stat` for `nl_query_ab_fixtures.py`
  empty in every PR (AC-8).
- **Host-state evidence (evidence, not the gate):** Step 7's recorded run
  under its typed go — the only place the "model actually emits it" claim is
  ever made.

## References

| Site | What it holds |
|---|---|
| `services/engine/nl_query.py:70,75` | `QueryOperation` includes `count`; `_AGGREGATE_OPS` excludes it |
| `services/engine/nl_query.py:385-393` | The system prompt; `:393` = the decisive "never list/count" rule |
| `services/engine/nl_query.py:526-549` | The validator rejection; `:529-535` its execution-gap rationale |
| `services/engine/nl_query.py:195-208` | `AggregateResult` — the SD-1 carrier problem |
| `services/engine/nl_query.py:1050,1053-1067,1070-1085` | `_AGG_LABEL` / `_phrase_aggregate` / `_fallback_answer` |
| `services/engine/nl_query.py:1298-1311` | Orchestrator aggregate gate + full-matched-set receipt rule |
| `services/engine/nl_query.py:770-785,788-810,813-851,896-915,1011-1031` | `_collect_numeric` / `_compute_aggregate` / `_relabel_groups` / `_infer_group_by` / `_apply_coherence` (all read this session) |
| `services/engine/run_query.py:123,164-178,296-300` | Shared validator reuse; `_count`'s collapse; the schema already advertising the pair |
| `services/api/models/query.py:27-74` + `services/api/routers/query.py:30-46` | No aggregate field over the API — verified, no forced change |
| `tests/services/engine/test_nl_query.py:664-671` | The test to rewrite, not delete |
| `benchmarks/nl_query_feasibility/text_to_sql.py:67-80` + `tests/benchmark/test_nl_query_text_to_sql.py:58-84` | The stale `SQL_EXPECT` + the vacuous cross-check |
| `benchmarks/nl_query_feasibility/gold.yaml:6-7,43-65,93-104` | Hand-verified convention; nl-02/nl-05 true values |
| `benchmarks/nl_query_feasibility/harness.py:57-108` | The scorer to extend with `groups` |
| `docs/plans/done/0051-reason-then-structure-ab.md:7` | The A/B verdict freezing the fixture corpus |
| `docs/STATUS.md` (PLAN-0100 residuals row) | D-4 RULED s217 (Cray, typed): option (a) — the ruling this PLAN executes |

**Claims carried, not measured (marked per the dispatch's provenance
discipline):** the "~15 logical `group_by` sites / ~10–12 edit sites" figure
is an estimate (the drafter verified **30 raw occurrences** in `nl_query.py`;
the logical-site grouping was not independently re-counted); the
`/insights/query` response-model shape for grouped figures (SD-2(a)) and the
exact home of the run-corpus guard test are execution-time confirmations; the
prior benchmark accuracy record's path (`RESULTS.md`, referenced from
`nl_query.py:859`) is cited by reference, not re-opened.
