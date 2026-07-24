# PLAN-0088: Cross-run read substrate and run-insight readers

**Status:** Draft
**Owner:** Claude Code
**Created:** 2026-07-22
**Related ADRs:** ADR-0032 (strategic frame — governs scope), ADR-0030 (฿ facet — advisory discipline inherited), ADR-016 (run records), ADR-0026 (step principals / SoD map)

> Provenance: session-161 dispatch. Cray (Tier 3) asked how accumulated
> pipeline-run data + the ontology can be fed to an LLM to create customer
> value; Code ground the question against the code and ADR-0032; Cray ratified
> the two forks recorded under **Locked constraints** below by typed selection.

## Goal

Build **one** cross-run read/aggregate substrate over the persisted
`pipeline_runs` / `step_results` records, and ship the four **Group-A**
run-insight readers as thin consumers of it: **A1** natural-language query over
run history, **A2** ฿ ROI rollup + narrative, **A3** bottleneck / cycle-time
reporting, **A4** audit-readiness reporting. Additionally, **prove — with
offline tests, not prose — that the same substrate can express Group B's
questions** (threshold/band recalibration, DoA/approval-chain calibration,
refusal mining, procedure-generation fuel) **without building any of Group B**.
Today nothing aggregates across runs: the only SQL aggregate anywhere in
`services/` is the audit-chain length count (`services/api/routers/audit.py:54`),
and the sole run-list read path materializes **every** run into Python and
counts steps in dicts (`services/api/routers/runs.py:273-331`) — a read surface
that does not survive this PLAN's own "enough run data" premise. (The
*aggregation* half of that gap is this PLAN's substrate under every outcome;
the *listing* half — whether `GET /runs` gains pagination — is a surfaced
fork, **SD-8**, not an assumed deliverable.)

## Locked constraints (Cray-ratified by typed selection — do not reopen here)

- **L1 — Group A is NOT Shape 2 and does not trip the ADR-0032 D2 pilot gate.**
  Rationale, stated so a future reader can apply the same test: ADR-0032 D3
  (`docs/adr/0032-…:170-193`) defines Shape 2 by its output — a loop that
  **surfaces typed improvement proposals** which a **human approves** through
  the `monitor→decide→approve→act` spine. Group A emits **no** typed proposal:
  it queries and summarises persisted records. It is therefore an extension of
  Shape 1's `monitor` leg, not Shape 2's loop, and the D2 gate
  (`:150-168`) — a live pilot, or Cray's explicit in-session override recorded
  in the proposing PLAN — does not apply. **The separation test, applied per
  reader:** *does it emit a typed improvement proposal for human approval, or
  feed anything back into governance config?* If yes → Group B → gated. If it
  only reads and reports → Group A. This PLAN makes the test **mechanical**,
  not just documentary: AC-11's read-only guard fails the build if the
  substrate or any reader acquires a write primitive.
- **L2 — Scope = build Group A + prove the substrate carries Group B. Do not
  build Group B.** The Group-B half is not a paper design: AC-10 poses Group B's
  four question shapes as executable queries against a seeded corpus and asserts
  exact answers. Group B's *build* stays out of scope (see Out of Scope) and
  stays gated by ADR-0032 D2.
- **L3 — The architectural core is a single cross-run read/aggregate layer.**
  The four readers are thin consumers of one substrate; Group B will consume
  the same substrate later. The substrate is this PLAN's centre of gravity
  (Step 1), and every reader step depends on it.
- **L4 — Do not amend ADR-0032.** L1's rationale lives in this PLAN only;
  ADR-0032 is cited by D-number + line range, never restated (ADR-0017 D6).

## Grounding — what exists today (all claims verified this session)

- **Run records** (`services/engine/procedures/runs.py`): `pipeline_runs`
  (`:59-94`) — `run_id` Text PK, `procedure_id`, `agent_id`, `trigger_context`
  JSONB, `step_principals` JSONB (requester half from typed
  `RunContext.principal`; approver half added at gate resolution), `status`,
  `started_at`/`updated_at` (timezone-aware), `governance_snapshot`/`_hash`,
  `version`. **No secondary index — PK only** (no `__table_args__`).
  `step_results` (`:97-111`) — per-step `status`, `duration_ms` BIGINT,
  `artifact`/`reasoning_trace`/`audit` JSONB, `created_at`; single index
  `idx_step_results_run_id` (`:101`).
- **The read gap**: `GET /runs` (`services/api/routers/runs.py:273-331`)
  selects ALL runs, then all their step rows, and counts in Python — no
  pagination, no filters, no SQL aggregation. Display-only by its docstring.
  **Pre-existing discrepancy, documented so a reader is not misled:** that
  docstring claims runs "are scoped by the single active vertical
  (`settings.oct_vertical`)", but the `select(PipelineRun)` is **unfiltered**
  — `settings.oct_vertical` only builds the declared step-count map
  (`:283-287`). The claim is true only incidentally (one deployment = one
  vertical against one DB; `pipeline_runs` has no vertical column). This PLAN
  documents the discrepancy and states its own scoping stance in S7; it does
  **not** fix the docstring/endpoint.
- **The ordering hazard**: the router's own comment (`runs.py:291-294`) admits
  `started_at` "is a wall clock that is not monotonic on this box — so this
  order is approximate", tolerated *because* the projection is display-only.
  The pinned deferral doctrine
  (`tests/services/db/test_load_run_ordering_guard.py:29-49`) is explicit: the
  root fix is a monotonic sequence column in its own PLAN, and **"if a
  correctness path ever starts depending on either ordering, the
  sequence-column PLAN stops being optional"** (`:47-49`). S4 below is this
  PLAN's answer.
- **NL query** (`services/engine/nl_query.py`, via `POST /query`):
  translate (LLM, schema-constrained) → execute (deterministic, no LLM,
  against the vertical `DataAdapter`) → phrase (LLM, retrieved records only);
  empty result short-circuits to a fixed answer. The corpus is the **ontology**
  — `object_type` is enum-constrained and properties are semantically validated
  (`_validate_query` aggregate/group coherence at `:458-504`, read directly).
  The aggregate vocabulary (`operation` list/count/max/min/avg/sum,
  `aggregate_property`, `group_by`; per-group computation `:705-760`;
  `_infer_group_by` rewrite seam `:828-847`) **already exists** — what is
  missing is a run-corpus schema to point it at (S5).
- **฿ facet** (`services/engine/economic_impact.py:50-79`): the typed
  `EconomicImpact` payload (`provisional`, `currency`, `kind`,
  baseline/governed `EconomicExposure`, validated `net_benefit_thb` Decimal,
  `assumptions`, `basis_refs`) rides a `ReasoningStep(kind="economic_impact")`
  **`detail` dict inside the `reasoning_trace` JSONB** — not a column, not part
  of the ADR-007 envelope (`:12-17`). **No cross-run rollup exists anywhere**:
  `services/engine/discovery.py:76-92` only *registers* a vertical's optional
  producer; the hero "฿-impact ledger" (`services/api/routers/demo.py:68-78`)
  is scenario-computed by `verticals/procurement/hero_demo/ledger.py`, which
  contains **zero** run-record reads (grep: no `PipelineRun`/`load_run`/
  `select(`/`session` hits).
- **Chain-of-command verdicts** are structured + stable-keyed and minable by a
  read-only surface: `doa_tier.py` (band-resolved tier), `tier_authority.py`
  (exact role check; `native_approver` routing distinct from cumulative-role
  enforcement), `principal_sod.py` (fail-closed identity collapse) — all pure,
  no LLM/DB, typed violation kinds. Refusals become first-class hash-chained
  audit facts at the persistence seam
  (`services/engine/procedures/persistence.py:56-80`).
- **Audit read surface**: `GET /verify` exposes `verify_chain` as a typed
  `ChainVerificationReport`, split visibility (public verdict, credentialed
  break strings), SELECTs only (`services/api/routers/audit.py`).
- **UI state** (resolves a dispatch open item): `view-monitor.js` renders a
  per-run list + polled detail with an operate seam (`:1-16`) — **no
  aggregate/insight view exists**; `view-hero.js` renders the per-run
  governance moment + the demo-scoped ฿ ledger (`:1-15`). No Group-A reader is
  half-built in the UI.
- **`GET /runs` consumer census (grep-derived 2026-07-24 — exactly two list
  consumers; grep `services/api/static/` for `'/runs'`):**
  (1) `view-monitor.js:168` reads the list and renders rows in payload order —
  no re-sort, **no cap** (`:216` `d.runs.forEach(...)`); pure display, so an
  order change degrades cosmetically only. (2) `view-map.js:84` fetches
  `/runs` bare (no params), builds per-asset in-flight flags in payload order
  with no re-sort (`:90-98`), and — the **stronger** dependence —
  **truncates**: the node panel takes `nodeRuns.slice(0, CAP)` with
  `CAP = 5`, under a comment stating the assumption outright: "Newest-first
  (the /runs list order), capped per SD-E" (`view-map.js:359-365`). If
  `/runs` stops being newest-first, the map does not merely look shuffled —
  it silently shows 5 arbitrary in-flight runs and *hides the newest*,
  defeating its own "jump to the EXACT run" purpose. The 2026-07-22 draft
  enumerated only `view-monitor.js` + `view-hero.js` in the bullet above and
  named `view-map.js` nowhere — see the re-draft note.
- **Test seeding** (resolves a dispatch open item): direct-ORM seeding of run
  rows is an established pattern (`tests/api/test_monitor_runs.py:53-70`
  `_seed_rows()`), but **no volume-scale fixture exists** — Step 1 ships one.

## Design decisions (S1–S7 — drafter-resolved reasoning; **none ratified yet**. Each is surfaced for one-pass typed ratification as SD-1…SD-7 in the Surfaced-decisions block below; the 2026-07-22 draft's header here read "S1–S6", an off-by-one that undercounted the unratified surface — see the re-draft note)

### S1 — The substrate lives in `services/db/run_analytics.py`

A read-only repository/query module under `services/db/`, sibling to
`audit_log.py` (the existing precedent for cross-record read logic living in
the DB layer). Not API-layer: Group B's eventual consumer is engine-side and
must not import a router. Not `services/engine/`, per the **layering rule this
PLAN follows — stated once here, obeyed by every module it adds: SQL lives in
`services/db`; engine-side logic stays session-free and reaches records only
through a delegate** (the shipped pattern: `nl_query.py` is engine-side and
touches data only via the vertical `DataAdapter`). The substrate is SQL-first
by definition, so it lives in `services/db`; S5's `run_query.py` sits
engine-side precisely *because* it owns no SQL and opens no session (AC-11
holds that statically). Typed result models (Pydantic, `Field(description=…)`)
live with it; a new thin router `services/api/routers/insights.py` is the only
API-side addition.

### S2 — ฿ aggregability: extract-on-read from JSONB; projection named as the upgrade path, not taken

Options weighed: (a) **extract-on-read** — SQL lateral over
`step_results.reasoning_trace`, filter `kind = 'economic_impact'`, cast
`detail->>'net_benefit_thb'` to numeric; (b) a write-time projection table /
derived column (+migration +backfill). Decision: **(a)**. Rationale: ADR-0030
makes the facet *advisory, trace-carried, never-raise* — a write-path
projection table starts treating an advisory facet as first-class state, the
exact drift ADR-0030 D1/SD-1 avoided; (a) needs no migration, no write-path
change, and is fully reversible. Inherited discipline: extraction is
**never-raise** (a malformed/absent facet row is skipped and *counted*, never
an error), every rollup output carries `provisional: true` and surfaces the
union of disclosed assumptions, and money stays Decimal end-to-end (AC-4 pins
the JSONB round-trip so serialization drift cannot silently corrupt figures).
The projection table is the named upgrade path **only on measured query-cost
evidence** at real volume — out of scope here.

### S3 — Reader order: A2 → A3 → A4 → A1

**A2 (฿ ROI rollup + narrative) ships first.** It is the instrument that
converts a pilot into a contract under ADR-0032 D1's 1-KPI 6-week charter, and
it forces the substrate's hardest design point (JSONB facet extraction, S2)
immediately — de-risking the core early. A3 (bottleneck/cycle-time) second:
same substrate, zero LLM, high operator value. A4 (audit-readiness) third: it
partially composes existing surface (`GET /verify`), so marginal build is
lowest. A1 (NL over runs) last **despite being the flashiest demo**: it has
the largest integration surface (corpus schema + deterministic executor +
grounding-parity tests) and its payoff grows with the run volume the earlier
readers already prove. The dispatch's non-binding lean (A2 first) was examined,
not deferred to — the deciding argument is D1-leverage plus
hardest-risk-first, and it would hold even if A1 were cheaper.

### S4 — Ordering soundness: constrain the readers; do NOT take the sequence-column fix into this PLAN

The pinned deferral stands because both wall-clock orderings are display-only
(`test_load_run_ordering_guard.py:37-49`). This PLAN keeps the substrate on
the safe side of that line instead of crossing it:

- Substrate v1 exposes **order-insensitive** operations only: counts, sums,
  averages, min/max, and `GROUP BY` bucket rollups.
- Time-series readers bucket by `date_trunc` at **day or coarser**. The
  observed clock skew (worst backward step −555 ms per the guard's doctrine)
  is immaterial at that granularity; the tolerance is documented in the module
  docstring.
- Cycle-time never subtracts wall-clock values **across rows**: step latency
  comes from `duration_ms` (per-step telemetry), and per-run wall span is the
  same-row `updated_at − started_at`, clamped at ≥ 0 with a
  `negative_clock_spans` counter surfaced in the report (never silently
  swallowed).
- **Tripwire (owned by AC-3):** a static AST guard — same doctrine as
  `test_load_run_ordering_guard.py` — fails if the substrate ever emits
  `ORDER BY` on raw `started_at`/`created_at`/`updated_at` (ordering bucket
  labels is allowed). Any future reader needing strict adjacent-row ordering
  (e.g., "previous-run delta") triggers the sequence-column PLAN **first**, per
  the guard's own `:47-49` rule.

*Re-draft note (2026-07-24): the 2026-07-22 draft's own AC-12 — newest-first
offset pagination inside the substrate — was exactly the consumer this
tripwire exists to stop, and the draft did not notice; the first bullet above
("order-insensitive operations only") already excluded it in the same
document. That fork was surfaced at SD-8 and is now RULED (a) ELIMINATE (Cray,
2026-07-24) — so this tripwire's consumer is struck, not merely excluded. S4
itself stood unmodified under every SD-8 option; the per-option consequences
are stated there.*

### S5 — A1 binds NL to the runs via a code-owned run-corpus schema + a deterministic SQL executor; separate endpoint

Run records are not ontology objects, so A1 does **not** widen the ontology
corpus. Instead: a static, code-owned **run-corpus descriptor**
(`services/engine/run_query.py`) declares pseudo-object-type(s) — v1:
`pipeline_run` with typed properties (`procedure_id`, `agent_id`, `status`,
`trigger`, `started_week` bucket; numeric: `duration_ms_total`,
`net_benefit_thb`) — presented in the same properties+types meta shape
`nl_query`'s validator checks against. All three provable-grounding properties
are preserved *by construction* and re-proven by tests (AC-8): (1) the
object type stays enum-constrained (to the run-corpus types); (2) every filter
/ aggregate / group property is semantically validated with the same
validate-and-retry contract; (3) the execute stage is **deterministic and
LLM-free** — it compiles the validated `StructuredQuery` to
`run_analytics` substrate calls, reusing the existing aggregate
vocabulary rather than inventing one (layering per S1's rule: the compiler
owns no SQL, opens no session, and imports no `sqlalchemy` symbol — AC-11
enforces this statically — exactly as `nl_query` reaches data only through
the `DataAdapter`); (4) the empty-result short-circuit to a
fixed "no matching records" answer is kept verbatim. Surface: a **separate**
`POST /insights/query` endpoint — cross-corpus routing ("is this question
about pumps or about runs?") is a real disambiguation problem that deserves
its own decision later; v1 does not fake it (see Out of Scope).

### S6 — Group-B "proof" ACs: executable query shapes + a mechanical no-proposal guard

The proof that the substrate *carries* Group B is a test suite (AC-10) that
poses each Group-B question **as a query** over a factory-seeded corpus and
asserts exact expected values through the substrate's public surface only:

- **B1 (band recalibration fuel):** distribution of a measured value vs its
  band verdict — outcome counts + summary stats grouped by band verdict,
  extracted from step artifacts/traces.
- **B2 (DoA/approval-chain calibration fuel):** approval outcomes + gate dwell
  grouped by resolved DoA tier, joining trace verdicts with the
  `step_principals` approver half.
- **B3 (refusal-mining fuel):** refusal counts grouped by refusal kind ×
  procedure, from the typed `read_refused` audit facts
  (`persistence.py:56-80`). *Counting/reporting refusals is Group A by the L1
  test; deriving improvement proposals from them is Group B and is not built.*
- **B4 (procedure-generation fuel):** run frequency grouped by
  (procedure_id × trigger kind × terminal status).

Paired with **AC-11**, the mechanical converse: the substrate + insights
router are statically proven read-only (no insert/update/delete primitive, no
proposal construction), so the suite demonstrates the *questions* are
expressible while the *loop* remains unbuilt.

### S7 — Corpus scoping: single-vertical by declared assumption; ฿ currency safety structural, never emergent

The corpus has no vertical dimension: `pipeline_runs` carries no vertical
column (`services/engine/procedures/runs.py:59-94`), and the one existing read
path's vertical-scoping docstring is true only incidentally (see the
Grounding read-gap bullet). Two distinct risks hide here and get **different**
treatments, because only one of them is enforceable against the data on disk:

- **Cross-vertical scope (a business-honesty risk):** the substrate v1 treats
  the DB as a **single-vertical corpus**, matching deployment reality (one
  `settings.oct_vertical` per deployment against one DB). The assumption is
  *named* in the substrate module docstring, and every insights report is
  **stamped** with the deployment's declared vertical
  (`settings.oct_vertical`, applied at the router layer — the DB layer stays
  settings-free per S1) so no report can be mistaken for a cross-vertical
  claim. Rejected alternative: deriving a vertical dimension by resolving
  `procedure_id` → vertical through the loaded specs — rejected because it
  couples the DB substrate to the vertical spec loader, breaks for runs whose
  procedure no longer ships (the router already tolerates `FileNotFoundError`
  for exactly that case), and still would not be the actual correctness gate.
- **Cross-currency summation (a correctness risk):** the ฿ facet carries its
  own `currency` field (`EconomicImpact.currency`, ISO code — THB-only in v1
  per ADR-0030 OQ-4), so the ฿ rollup's group key **structurally includes
  `currency`**: sums exist only per-currency, and the report model carries
  **no cross-currency total field** — the wrong sum is *unrepresentable*, not
  merely checked. This is the reader-side analog of `doa_tier.py`'s
  fail-closed currency-mismatch discipline, and it holds even in a
  hypothetical multi-vertical DB: currency safety no longer rides on the
  accidental fact that `procedure_id`s differ per vertical. AC-4 owns the
  test (two seeded currencies → separate buckets, no combined figure).

If a real multi-vertical-one-DB deployment ever appears, adding a vertical
column (a migration) is that deployment's PLAN — not this one.

## Surfaced decisions (SD-1…SD-8 — ✅ ALL RATIFIED by Cray 2026-07-24, session 169, typed AskUserQuestion — adjudicated at Step 0)

**LOCKED vs SURFACED, stated once:** the four **Locked constraints L1–L4** are
already Cray-ratified by typed selection (see their own section). They are
**not** re-listed here and this block may not reopen, weaken, or re-argue
them. Everything below is the *unratified* surface: the seven drafter-resolved
design decisions S1–S7 (per the disclosure section, the R2-round F1–F3
amendments were Cray-*ordered* but drafter-*answered* — the answers were never
ratified), plus one newly surfaced fork (SD-8) that the 2026-07-22 draft
resolved silently and self-contradictorily. The pattern is PLAN-0091's SD
block (`docs/plans/done/0091-narrative-to-vertical-scaffolder-tool.md:407-614`):
per decision — the question, the options, a recommendation with reasoning —
ratifiable in a single typed pass. Where a decision is well-argued and
uncontroversial, the recommendation says "ratify as written" plainly; no
controversy is manufactured to fill the template.

> **✅ RULINGS (Cray, 2026-07-24, session 169, typed AskUserQuestion — one
> pass, per Step 0). This banner is the authoritative inline ruling record for
> the block.**
> - **SD-1 … SD-7 — RATIFIED as written**, each as recommended (S1 substrate
>   location/layering · S2 ฿ extract-on-read · S3 reader order A2→A3→A4→A1 ·
>   S4 order-insensitive substrate, sequence fix stays deferred · S5 A1
>   run-corpus descriptor + separate endpoint · S6 Group-B proof standard ·
>   S7 single-vertical corpus + structural currency safety). No option pulled
>   for separate discussion.
> - **SD-8 — RULED (a): ELIMINATE.** `list_runs_page` and AC-12 are struck from
>   this PLAN; the substrate ships **aggregate primitives only** and `GET /runs`
>   is **untouched** by this PLAN. Listing pagination is not abandoned — it is
>   sequenced into the future monotonic-sequence-column PLAN, where newest-first
>   paging is correct by the monotonic key (per the deferral doctrine,
>   `tests/services/db/test_load_run_ordering_guard.py:47-49`). AC-3 passes, S4
>   holds, both `/runs` consumers unchanged, nothing new on the critical path.
> - **Consequence: Step 0 is DISCHARGED and PLAN-0088 is BUILD-READY.** Status
>   stays `Draft` (flips to `Complete` only at closeout, per the Accepted-status
>   G1 gate). No AC may still read as "contingent on SD-8".

### SD-1 — Ratify S1 as written? (substrate location + layering rule)

**Question:** does the substrate live in `services/db/run_analytics.py` under
the SQL-in-`services/db` / session-free-engine layering rule, with
`insights.py` the only API-side addition?
**Options:** as argued in S1 — `services/db` (chosen) vs API-layer vs
`services/engine/` (both rejected there, with reasons).
**Recommendation: ratify as written.** It follows the shipped `audit_log.py`
precedent and the layering rule S1 states once and every module obeys; AC-11
holds the rule statically. What makes this Cray's call: it fixes the layering
boundary every future insight consumer — including Group B's eventual
engine-side consumer — inherits.

### SD-2 — Ratify S2 as written? (฿ extract-on-read from JSONB)

**Question:** extract-on-read over `step_results.reasoning_trace` (chosen) vs
a write-time projection table (rejected; named as the upgrade path only on
measured query-cost evidence)?
**Recommendation: ratify as written.** It is the ADR-0030-conforming option —
the facet stays advisory and trace-carried, never first-class write-path
state — and it is fully reversible. What makes this Cray's call: it sets the
evidence bar (measured query cost, not speculation) for ever taking the
projection-table upgrade.

### SD-3 — Ratify S3 as written? (reader order A2 → A3 → A4 → A1)

**Question:** which reader ships first?
**Options:** A2-first (chosen: D1-leverage — the pilot→contract instrument —
plus hardest-risk-first on the S2 JSONB extraction) vs A1-first (the flashiest
demo; largest integration surface, payoff grows with run volume the earlier
readers prove).
**Recommendation: ratify as written.** The reasoning in S3 is explicit and
would survive a cost re-estimate. What makes this Cray's call: it is a bet on
which conversation happens next — a pilot-conversion conversation (A2) vs a
demo conversation (A1) — which is business judgment, not engineering.

### SD-4 — Ratify S4 as written? (order-insensitive substrate; sequence fix stays deferred)

**Question:** does the substrate constrain itself to order-insensitive
operations, day-or-coarser buckets, same-row spans, with the AC-3 tripwire —
rather than taking the monotonic-sequence fix into this PLAN?
**Recommendation: ratify as written — noting the entanglement with SD-8.**
The 2026-07-22 draft's AC-12 violated S4's own first bullet and AC-3's guard
(see SD-8's bind paragraph); S4 itself stands under every SD-8 option: under
(a) trivially, under (b) because the page key is not a wall clock, under (c)
because the fix lands in its own prerequisite PLAN, not this one. What makes
this Cray's call: it re-affirms the pinned deferral doctrine
(`tests/services/db/test_load_run_ordering_guard.py:29-49`) against a new
consumer class — cross-run readers.

### SD-5 — Ratify S5 as written? (A1 = code-owned run-corpus descriptor + deterministic executor; separate endpoint)

**Question:** does A1 bind NL to runs via a static run-corpus descriptor and a
deterministic LLM-free compiler to substrate calls, on a **separate**
`POST /insights/query` endpoint — leaving cross-corpus routing out of scope?
**Recommendation: ratify as written.** It preserves `nl_query`'s three
grounding properties by construction and refuses to fake cross-corpus
disambiguation. What makes this Cray's call: separate-endpoint vs
one-NL-surface is product shape, and the deferral of routing is a scope bet.

### SD-6 — Ratify S6 as written? (Group-B proof = executable query shapes + the mechanical no-proposal guard)

**Question:** is AC-10's four-query suite + AC-11's static read-only converse
the standard of proof for L2's "the substrate carries Group B"?
**Recommendation: ratify as written.** It is what makes L1/L2 mechanical
rather than documentary. What makes this Cray's call: it defines the standard
a future Group-B PLAN will point back at when it claims the substrate was
proven ready.

### SD-7 — Ratify S7 as written? (single-vertical corpus by declared assumption; currency safety structural)

**Question:** single-vertical corpus assumption (named + report-stamped, not
enforced by a vertical column) and per-currency-only ฿ sums with no
representable cross-currency total?
**Recommendation: ratify as written — and note this one is substantive, not
pro-forma:** S7 is one of the R2-round F-amendment answers the drafter wrote
to Cray's amendment *orders* (disclosure item 7) — Cray fixed the questions,
never these answers. What makes this Cray's call: the single-vertical stance
is a business-honesty commitment about what an insights report may claim, and
the structural currency rule is its correctness twin.

### SD-8 — The pagination fork (✅ RULED (a) ELIMINATE, Cray 2026-07-24; the 2026-07-22 draft had resolved it silently and self-contradictorily)

**Question:** does this PLAN ship a run-listing pagination primitive at all —
and if so, ordered how?

**The bind, on the record (why this is a fork and not an AC):** the
2026-07-22 draft contained all four of: (1) AC-1 placing "paginated listing"
among the substrate's primitives; (2) AC-12 — `list_runs_page(limit, offset)`
plus an optional `limit` on `GET /runs` preserving newest-first; (3) AC-3's
tripwire failing the build if `run_analytics.py` emits `ORDER BY` on a raw
wall-clock column; (4) S4 refusing to take the monotonic-sequence fix into
this PLAN (its first bullet: "order-insensitive operations only"). These are
**jointly unsatisfiable**. A paged listing that preserves newest-first must
`ORDER BY started_at DESC` *inside the guarded module* — exactly what AC-3
fails on (`GET /runs` does it today at `services/api/routers/runs.py:296`,
legally, because it sits outside the guard's scope and is display-only per
its own comment at `:291-294`). Drop the ORDER BY instead and offset
pagination over Postgres is nondeterministic — without a total order, rows
can repeat or vanish across pages (standard SQL semantics: unordered SELECT
has no stable row order). Order it correctly and you need the monotonic key
S4 defers. You cannot have all of {pagination lives in the guarded substrate;
pagination is newest-first + deterministic; AC-3 passes; S4 holds}. The
default path was and is safe — an absent `limit` keeps `runs.py`'s own query
(`:295-299`), outside the guard — so this is a **latent contradiction on the
paged path, not a live breakage**. And it lands on real consumers the draft
never censused: both `/runs` list consumers assume newest-first, and
`view-map.js` **truncates** on that assumption (`nodeRuns.slice(0, CAP)`,
`CAP = 5`, `view-map.js:359-365`) — see the consumer-census grounding bullet.

**Options, with consequences for AC-3, S4, and both consumers:**

- **(a) ELIMINATE.** Strike `list_runs_page` and AC-12 from this PLAN; the
  substrate ships **aggregate primitives only**; `GET /runs` stays exactly as
  it is (unbounded, its own display-only wall-clock sort, tolerated by the
  pinned doctrine, `test_load_run_ordering_guard.py:37-49`). Listing
  pagination becomes a **stated concern of the future sequence-column PLAN**,
  where newest-first paging is trivially correct (order by the monotonic
  key). AC-3: passes, nothing to except. S4: intact. `view-monitor.js` /
  `view-map.js`: contracts byte-unchanged. Cost: the O(all-runs) listing read
  stays unbounded for now — as it already is today, on a display-only path.
- **(b) Paginate on a stable non-wall-clock key** — the only one that exists
  today is `run_id`, the Text PK (`services/engine/procedures/runs.py:64`;
  the sole wall clocks are `started_at`/`updated_at`, `:77-78`).
  Deterministic and AC-3-clean, but **not newest-first** — `run_id` order is
  semantically arbitrary. AC-3: passes. S4: intact. Consumers: **neither may
  ever be switched onto the paged path without regression** — `view-monitor.js`
  would render an arbitrary order (cosmetic), and `view-map.js`'s
  `slice(0, 5)` would hide the newest runs (functional regression of its
  "jump to the EXACT run" purpose). (b) therefore ships a primitive **no
  known consumer can safely adopt**: dead weight plus a standing trap.
- **(c) Keep newest-first pagination** — which, per the guard doctrine's own
  trigger ("if a correctness path ever starts depending on either ordering,
  the sequence-column PLAN stops being optional",
  `test_load_run_ordering_guard.py:47-49`), means **the monotonic-ordering-key
  PLAN must be drafted and land FIRST**; the substrate then paginates by that
  key (not a wall clock). AC-3: passes. S4: intact in the letter — the fix
  lands in its own prerequisite PLAN, not this one — but this PLAN's Step 1
  becomes **blocked on a migration PLAN that does not exist today** (the
  doctrine notes "none is drafted", `:33`). Consumers: correct newest-first
  pages, adoptable by both.

**Recommendation: (a) — eliminate.** Reasoning: (1) the primitive is not
load-bearing for this PLAN's goal — L3's centre of gravity is an *aggregate*
substrate, and all four readers consume rollups, not row listings; AC-12 was
a drafter beyond-dispatch addition (disclosure item 1), never
dispatch-mandated, never ratified. (2) It is the only option with zero
casualties: guard passes, S4 intact, both consumer contracts untouched,
nothing new on the critical path. (3) It does not abandon pagination — it
sequences it after its own prerequisite, inside the sequence-column PLAN the
doctrine already demands for any ordering-dependent path. (4) Reversal cost
is minimal now (one AC struck, zero code built) and high later (a mid-Step-1
redesign). What makes this Cray's typed call and not a drafter's: it deletes
a previously drafted deliverable, decides whether a consumer-visible endpoint
changes in this PLAN, and sets the first real-case interpretation of the
guard doctrine's un-defer trigger.

**→ RULED (a) ELIMINATE (Cray, 2026-07-24, session 169, typed AskUserQuestion).**
`list_runs_page` and AC-12 are struck; the substrate ships aggregate primitives
only; `GET /runs` is untouched by this PLAN; listing pagination is sequenced
into the future monotonic-sequence-column PLAN. This is the first real-case
reading of the deferral doctrine's un-defer trigger, and it declines to fire it
here — the aggregate readers are order-insensitive, so the trigger stays unfired
and the sequence-column PLAN stays optional until a genuinely ordering-dependent
consumer appears.

## Acceptance Criteria

All ACs are **offline-testable** (CLAUDE.md §8: offline tests are the gate;
DB-backed tests use the disposable per-checkout test DB). The single
live-model item is explicitly non-CI (AC-9b).

- [ ] **AC-1 — Substrate, SQL-side.** `services/db/run_analytics.py` exposes
  typed read primitives (status/procedure/period rollups, duration stats, ฿
  rollup, refusal/gate counts — **no listing primitive** (SD-8 ruled (a)
  ELIMINATE, 2026-07-24; `list_runs_page`/AC-12 struck)). A seeded-corpus DB test
  (**≥ 250 runs / ≥ 1,250 step rows** via the AC-2 factory) asserts exact
  aggregate values. **The load-bearing proof of the SQL-side property is the
  statement-capture fixture, not the corpus size**: it asserts the rows
  fetched are O(groups), never O(runs) — an assertion that holds at 250
  exactly as it would at 1,000. 250 is the smallest corpus that dominates the
  group count by > 10×, so an accidental O(runs) materialization is
  unmistakable in the capture. (The 2026-07-22 draft's second sizing leg —
  "limit=100 → three pages, exercising AC-12's bounds" — presumed the paged
  path SD-8 (a) struck; the 250 figure now stands on the group-domination leg
  alone.) A larger corpus proves nothing
  the fixture cannot, and its cost would land on every CI run forever;
  performance-at-volume is a measured-evidence concern (S2's upgrade-path
  stance), not a CI micro-benchmark.
- [ ] **AC-2 — Volume factory.** A deterministic (seeded-RNG) corpus factory
  under `tests/support/` generalizing the `test_monitor_runs.py` direct-ORM
  pattern: ≥ 3 procedures, all run statuses, gate resolutions with
  `step_principals` approver halves, ฿ facets on a known subset (including a
  non-THB-currency sub-subset for AC-4's currency-separation test),
  `read_refused` audit facts on a known subset, band-verdict artifacts on a
  known subset.
  Reproducible expected values are computable in-test from the seed.
- [ ] **AC-3 — Ordering tripwire (owns the S4 guard).** A static AST guard
  test fails if `run_analytics.py` emits `ORDER BY` on a raw wall-clock column
  (`started_at`/`created_at`/`updated_at`); bucket-label ordering allowed. The
  ±1 s skew tolerance and the day-or-coarser bucketing rule are documented in
  the module docstring and asserted present by the same test.
- [ ] **AC-4 — A2 rollup.** `GET /insights/impact` returns a typed ฿ rollup
  grouped by **`currency` × procedure × facet `kind` × period**: run counts,
  summed/averaged `net_benefit_thb` (Decimal end-to-end), `figures_missing`
  count, `provisional: true` at report level, union-of-assumptions
  disclosure, and the S7 deployment-vertical stamp. **Currency safety is
  structural per S7:** sums exist only per-currency and the report model
  carries no cross-currency total field (the wrong sum is unrepresentable);
  a test seeding facets in two currencies (AC-2) asserts they land in
  separate buckets with no combined figure — the reader-side analog of
  `doa_tier`'s fail-closed currency discipline. A round-trip test persists a
  run **through the real persistence path** with a known `EconomicImpact`
  facet and asserts extraction equals the emitted Decimal (pins the JSONB
  serialization shape). A malformed facet row is skipped + counted — asserted
  never to raise (ADR-0030 never-raise inherited).
- [ ] **AC-5 — A2 narrative.** A deterministic (no-LLM) template narrative
  renders the rollup; a test asserts every figure in the narrative equals the
  rollup value it cites, and that the provisional labeling is present. No
  ADR-0032 D5 forbidden vocabulary anywhere in reader-facing strings
  (asserted by grep-style test over the insights modules).
- [ ] **AC-6 — A3 flow report.** `GET /insights/flow` returns per-procedure ×
  per-step `duration_ms` stats (count/avg/max), `waiting_human` dwell from
  same-row spans clamped ≥ 0, and a surfaced `negative_clock_spans` counter.
  Seeded test asserts exact values; no cross-row wall-clock arithmetic exists
  (covered by AC-3's guard scope).
- [ ] **AC-7 — A4 audit-readiness.** `GET /insights/audit-readiness` composes:
  run totals by status, gate-resolution counts (approver half present),
  refusal counts by kind, and the existing public chain verdict via the
  shipped `verify_chain` seam — read-only, split visibility preserved (no
  verbatim break strings). Seeded test asserts exact composition.
- [ ] **AC-8 — A1 grounding parity.** The run-corpus descriptor + executor
  preserve `nl_query`'s three grounding properties, each with its own test:
  (i) unknown object type / property / non-numeric aggregate rejected with
  validate-and-retry-shaped errors; (ii) execute is deterministic and LLM-free
  — the LLM client is monkeypatched to raise, a stubbed translate feeds a
  fixed `StructuredQuery`, and exact seeded values come back; (iii) an
  empty result short-circuits to the fixed no-matching-records answer with
  the phrase stage never invoked.
- [ ] **AC-9 — A1 endpoint.** `POST /insights/query` wires
  translate→validate→execute→phrase with the translate/phrase stages
  pluggable; CI exercises the pipeline end-to-end with a schema-shaped stub
  translator + stub phraser (offline).
- [ ] **AC-9b — A1 live smoke (host-state, NOT CI).** One live translate+phrase
  run against local MS-S1 Ollama only. **Requires explicit Cray go before the
  run** (CLAUDE.md §8); never a CI gate; run records carry `person_id` (PII —
  PDPA), so the remote Anthropic API is **never** used on run data.
- [ ] **AC-10 — Group-B carrier proof (owns the L2 proof).** Four tests — B1
  band-verdict distribution, B2 per-tier approval outcome + dwell, B3 refusal
  counts by kind × procedure, B4 trigger × outcome frequency — each expressed
  through the substrate's public surface only, asserting exact seeded values.
- [ ] **AC-11 — Read-only guard (owns the L1 mechanical test).** A static AST
  guard over `run_analytics.py`, `insights.py`, **and `run_query.py`**
  asserting three concrete predicates — nothing in this guard is prose-only:
  (i) no write primitive (`session.add` / `insert(` / `update(` / `delete(`);
  (ii) no import of the proposal/write-path **deny-list, each symbol verified
  on disk**: `RecommendedAction` from `services/engine/actions.py:85` (the
  ADR-007 envelope) and its ORM twin `RecommendedAction` in
  `services/db/models.py:68`, `resolve_gated_step`
  (`services/engine/procedures/action_step.py:546`), `persist_run`
  (`services/engine/procedures/persistence.py:48`), and `resume_run`
  (`services/engine/procedures/persistence.py:311`);
  (iii) `run_query.py` imports no `sqlalchemy` symbol at all (S1's layering
  rule, held statically). The insights router registers only read semantics
  (GETs + the query POST whose handler calls substrate reads only).
- ~~**AC-12 — `/runs` pagination.**~~ **ELIMINATED per SD-8 (a)** (Cray,
  2026-07-24, session 169, typed). The slot is kept as a tombstone so AC-1…AC-13
  numbering and every cross-reference stay stable; **there is no AC-12 to build,
  tick, or verify.** The 2026-07-22 text (substrate exposes
  `list_runs_page(limit, offset)`; `GET /runs` gains an optional `limit`) was
  jointly unsatisfiable with AC-3 + S4 (SD-8's bind) and undercounted the
  consumers — `view-map.js:84` fetches `/runs` bare and **truncates** to the
  first 5 in-flight runs per node on a stated newest-first assumption
  (`nodeRuns.slice(0, CAP)`, `CAP = 5`, `view-map.js:359-365`). SD-8 struck it:
  the substrate ships **no** listing primitive and `GET /runs` is untouched by
  this PLAN. Listing pagination lives in the future monotonic-sequence-column
  PLAN. **Live AC count: 13** (AC-1…AC-11, AC-9b, AC-13; AC-12 is a tombstone).
- [ ] **AC-13 — Quality gate.** New code: type hints, `mypy --strict` clean on
  the whole `services/` tree, ruff clean, all request/response models Pydantic
  with `Field(description=…)`.

## Out of Scope

- ❌ **Building any of Group B** — typed improvement-proposal emission,
  threshold/band recalibration, DoA/approval-chain calibration, refusal-mining
  actioning, procedure generation. Group B **is Shape 2** and is bound by the
  ADR-0032 D2 pilot gate (`docs/adr/0032-…:150-168`): a future Group-B PLAN
  must cite a live pilot or record Cray's explicit in-session override **in
  that PLAN itself**. This PLAN records no such override and — per L1 — needs
  none. L2's "prove the substrate carries B" is **not** permission to build B.
- ❌ **Amending ADR-0032** (L4; ADR-0017 D6 — restating an ADR is a drift
  surface).
- ❌ **The monotonic sequence-column migration** (the root ordering fix) — it
  deserves its own PLAN per the pinned deferral
  (`tests/services/db/test_load_run_ordering_guard.py:29-49`); this PLAN
  constrains itself to order-insensitive reads instead (S4).
- ❌ **Any remote-API LLM processing of run records** — they carry `person_id`
  (PII / PDPA); local MS-S1 only, and any live run is host-state Cray-gated
  (CLAUDE.md §8).
- ❌ **Cross-corpus NL routing** (one endpoint answering over ontology + runs)
  — deferred until the disambiguation problem is designed on its own merits
  (S5).
- ❌ **A ฿ projection table / derived column** — the named upgrade path of S2,
  taken only on measured query-cost evidence.
- ❌ **UI panels for the readers** (`view-*.js`) — this PLAN delivers substrate
  + typed API surface; UI adoption is follow-on work.
- ❌ **New indexes beyond what the substrate's own measured test-DB plans
  justify** — Step 1 may add obvious ones (e.g., `pipeline_runs.started_at`,
  `procedure_id`) but speculative index tuning for hypothetical volume is out.

## Steps

### Step 0: Cray adjudicates SD-1…SD-8 (gates every later step) — ✅ DISCHARGED 2026-07-24

One typed pass over the Surfaced-decisions block — the PLAN-0091 Step-0
pattern (`docs/plans/done/0091-…:605-614`). **Discharged 2026-07-24 (session
169, typed AskUserQuestion):** SD-1…SD-7 ratified as written, SD-8 ruled (a)
ELIMINATE — the authoritative record is the RULINGS banner atop the
Surfaced-decisions block. AC-12 is struck (tombstone); AC-1's listing clause and
paged sizing leg stay gone (they returned only under (b)/(c), which were not
ruled). **Step 1 is now unblocked.**

### Step 1: The substrate (`services/db/run_analytics.py`) — AC-1, AC-2, AC-3, AC-11

Typed read-only query layer: rollup primitives (status/procedure/period,
duration stats, ฿ extraction per S2, refusal/gate counts) + Pydantic
row/report models. Ships **with** its discipline in the same PR: the
volume corpus factory, the statement-capture fixture, the AC-3 ordering guard,
and the AC-11 read-only guard. Per SD-8 (a), ruled 2026-07-24, this step ships
**no** listing primitive and leaves `GET /runs` untouched. This step is the L3
centre of gravity — every later step consumes it and adds no new SQL of its
own.

### Step 2: Reader A2 — ฿ ROI rollup + narrative (`GET /insights/impact`) — AC-4, AC-5

New `services/api/routers/insights.py` (thin; substrate calls only). Rollup
model + deterministic narrative renderer. Pins the JSONB facet round-trip
through the real persistence path. First reader by S3's ordering rationale.

### Step 3: Reader A3 — bottleneck / cycle-time (`GET /insights/flow`) — AC-6

`duration_ms`-based step latency stats + same-row dwell spans with the
clamped-negative counter. Zero LLM.

### Step 4: Reader A4 — audit-readiness (`GET /insights/audit-readiness`) — AC-7

Compose substrate counts with the existing `verify_chain` public verdict.
Read-only; split visibility preserved.

### Step 5: Reader A1 — NL query over runs (`POST /insights/query`) — AC-8, AC-9, AC-9b

Run-corpus descriptor + deterministic `StructuredQuery`→substrate executor in
`services/engine/run_query.py`; endpoint wiring with pluggable translate/
phrase; grounding-parity tests offline. The single live smoke (AC-9b) is
host-state: **explicit Cray go required before any live run**, MS-S1 local
model only.

### Step 6: Group-B carrier proof + close — AC-10, AC-13

The four B-shape query tests over the seeded corpus; final quality gate sweep;
STATUS update. (Archival `git mv` to `done/` happens per standard plan flow
after completion.)

## Verification

- **Offline gate (the gate):** full `pytest` + `mypy --strict` over the whole
  `services/` tree + ruff, per CLAUDE.md §8 and the offline-gate-matches-CI
  discipline. DB-backed tests run against the disposable per-checkout test DB
  (Docker Postgres up).
- **The guards prove the constraints, not just the features:** AC-3 (ordering
  discipline holds statically), AC-11 (Group-A read-only boundary holds
  statically, on named symbols), AC-4's round-trip + two-currency separation
  (฿ figures cannot silently drift through JSONB, and no cross-currency sum
  is representable — S7), AC-1's statement capture (aggregation cannot
  silently regress to in-Python counting).
- **Live evidence, not CI:** AC-9b's one MS-S1 smoke, only after explicit Cray
  approval, results recorded in the session handoff — evidence, never a gate.
- **Done means:** SD-1…SD-8 carry Cray's typed ruling (recorded in the RULINGS
  banner atop the Surfaced-decisions block; Step 0 DISCHARGED 2026-07-24); all
  **13 live** ACs ticked — AC-12 is *struck* per SD-8 (a), a tombstone that is
  never built or ticked; guards green in CI; no ADR edited; and the Group-B
  proof suite green while AC-11 simultaneously proves no proposal machinery
  exists.

## Re-draft note (2026-07-24) — what was wrong, how it was found, classification

The 2026-07-22 draft was complete, detailed, internally cited — and
self-contradictory. Three defects, all classified **`was an error`** per
CLAUDE.md §6 (nothing on disk changed between draft and discovery; every fact
below was on disk at draft time and the draft missed it — none of this is
`superseded by new info`):

1. **AC-3 ⊗ AC-12 ⊗ S4 were jointly unsatisfiable** (the SD-8 bind: a
   newest-first page needs the wall-clock `ORDER BY` the guard forbids, or
   the monotonic key S4 defers). Two later sessions re-read this PLAN
   linearly and did not surface it; session 168 found it only by reading the
   *consumers* (`runs.py`, `view-map.js`) rather than the plan. Each AC
   individually checked out against disk — the contradiction lives only in
   their composition.
2. **The consumer census was short.** AC-12 named `view-monitor.js` only;
   `view-map.js` — the stronger, *truncating* dependence
   (`nodeRuns.slice(0, CAP)`, `CAP = 5`, `view-map.js:359-365`), shipped by
   PLAN-0084 which closed out 2026-07-21, one day *before* this PLAN was
   drafted (`docs/plans/done/0084-map-monitor-run-linkage-and-seed-rotation.md:3`)
   — appeared nowhere in the document.
3. **The design-decisions header read "S1–S6"** while seven S-sections exist
   — the off-by-one that let a reader undercount the unratified surface.

Structural lessons, recorded here so they cannot be re-lost: **(i) an AC set
can be complete, individually verified, and still jointly unsatisfiable —
cross-AC consistency is a *composition* check that no linear read performs**
(concretely: check every guard-AC's scope against every obligation the other
ACs place *inside* that scope); **(ii) a consumer census is grep-derived,
never recalled** (the census bullet in Grounding states its grep); **(iii) a
drafter-resolved design layer needs an explicit adjudication surface** — this
PLAN sat in Draft not for lack of quality but because seven unratified
decisions had no one-pass surface for Cray to ratify; PLAN-0091's SD block is
that surface, and that PLAN went Draft→build-ready the day it was adjudicated
(s165). This re-draft adds the same surface (SD-1…SD-8, Step 0).

## Author≠reviewer disclosure (ADR-012 D4.3)

This PLAN was drafted by the in-harness `plan-drafter` subagent under ADR-013
D1 phased authority, from a session-161 Code-authored, Cray-ratified dispatch.
Independent review: Claude Code (R2) + Cray at PR merge. Separation: INTACT —
the drafter did not originate the L1/L2 forks (Cray did, by typed selection)
and does not commit.

**Beyond-dispatch additions (SD disclosure — for explicit Code/Cray review):**

1. **AC-12** — the dispatch flagged the `GET /runs` O(all-runs) gap but did not
   mandate touching the endpoint; this draft adds an optional, non-breaking
   `limit` param + substrate pagination primitive. *(Re-draft 2026-07-24: this
   addition was the SD-8 contradiction — see the re-draft note. Surfaced as
   SD-8 and RULED (a) ELIMINATE by Cray 2026-07-24 — the addition is struck.)*
2. **AC-5's deterministic-narrative-first choice** — the dispatch did not
   specify LLM vs template for the A2 narrative; this draft chooses template
   (no-LLM) for v1, keeping every reader except A1 fully LLM-free.
3. **AC-9b** as a separate host-state, non-CI item — an interpretation of the
   dispatch's §8 constraint, made explicit so it cannot be mistaken for a gate.
4. **The `negative_clock_spans` clamp+counter** (S4/AC-6) — drafter-added
   handling for the pathological backwards-clock case inside a single row.
5. **UI panels declared out of scope** — the dispatch listed readers without
   specifying UI; this draft scopes them as API + models only.
6. **The last Out-of-Scope bullet (index restraint)** — drafter-added scope
   hygiene, since `pipeline_runs` was verified to carry no secondary index.
7. **R2-round amendments (Cray-ordered F1–F3, drafter-resolved):** S7's
   single-vertical + structural-currency resolution, AC-1's 250-run number,
   and AC-11's five-symbol deny-list are the drafter's answers to Cray's
   amendment orders — the orders fixed the questions, not these answers.
   Reviewable independently of the rest of the draft.

**Re-draft round (2026-07-24, this edit):** re-drafted **in place** by the
in-harness `plan-drafter` subagent from a Code-authored dispatch carrying the
session-168 diagnosis. This drafting round **resolved no decision** (Cray ruled
separately the same day — see the RULINGS banner + Step 0): it converted the
drafter-resolved S1–S7 into the surfaced SD-1…SD-7, surfaced the pagination
contradiction as SD-8 (recommendation: eliminate — since RULED (a) by Cray),
completed the `GET /runs` consumer census (added
`view-map.js`, the truncating dependence), corrected the S1–S6→S1–S7 header,
made AC-1/AC-12/Step 1 state their SD-8 dependence explicitly, and recorded
the diagnosis in the re-draft note. L1–L4 were not reopened; `Status: Draft`
unchanged; no AC ticked. Separation: INTACT — the drafter neither originated
the s168 diagnosis nor ratifies any SD, and does not commit. Independent
review: Claude Code (R2 — every added `file:line` spot-checked against disk)
+ Cray at PR merge.
