# PLAN-0117: Fleet ontology carries supplier-evaluation facts — the Ask-surface unlock; a prerequisite for the rationale bar, not its unlock

**Status:** Draft
**Owner:** Claude Code — **execution-unblocked, no open SDs.** Cray ruled every SD (typed, 2026-08-31, session 265): SD-1=(c), SD-2=SPLIT (fleet side here; core promotion deferred to its own ADR+PLAN), SD-3 IN-set ruled, SD-4=(a), SD-5=(a), and — later the same session — **SD-3a RULED: declare all four remaining donor properties now, bare + rich `description`, NO synonyms** (see the SD-3a ruling block; it overturns this draft's earlier OUT disposition for those four, lineage preserved). In the s265 correction pass, **SD-6 RULED (a): the ontology's effect on the two MS-S1 models is measured on the NL / Ask surface (`benchmarks/nl_query_feasibility/`), not on `procedure_baseline`** (see SD-6 + the Correction record).
**Created:** 2026-08-31 · **Revised:** 2026-08-31 ×3 (same session family, s265 — first pass: rulings + two specialist investigations; second pass: SD-3a ruling closed + propagated; third pass: **correction** — Code's offline measurement F17 showed the ontology never reaches the procedure agent's prompt, so the theory of change is corrected from "rationale-bar unlock" to "Ask-surface unlock + rationale-bar prerequisite"; SD-6 ruled)
**Related ADRs:** ADR-006 (Rule of Three — bore on SD-2's *original* reasoning; superseded as the operative ground by the SPLIT ruling), ADR-008 (ontology schema + D1 "may extend" license; D4 many_to_many deferral), ADR-0032 (D1 demo→pilot correction-surface discipline — bears on SD-1), ADR-0033 (**D6 boundary — the deferred core promotion must formally reopen it**; see the Out-of-Scope deferred-core record), ADR-0034 (D4 evidence-alternative — the per-case sole-source record that makes a vendor-level `single_source_flag` a double-statement risk; originally the OUT reason in SD-3, now the **noted residual concern** under the SD-3a ruling)
**Related PLANs:** PLAN-0109 (Draft, unexecuted — **edits the same YAML file**; see the Coordination section), PLAN-0111 (verified **zero overlap** — Coordination §5 / F14), `done/0036` (the procurement donor), the later grader PLAN this one feeds (unnumbered; named in Out of Scope — this PLAN is a prerequisite for its rationale lane, **not** its unlock: that lane also needs the goal edit (SD-4, that PLAN) and the still-unscoped event/goal carrier, F17), the deferred core-promotion ADR+PLAN (unnumbered; the Out-of-Scope block below is its durable record until they exist)

> **Drafting provenance (ADR-012 D4.3).** Authored by the in-harness `plan-drafter`
> subagent from a Code-tab dispatch (session-264 follow-on fact-pack, verified by the
> dispatcher and re-verified on disk by this draft, 2026-08-31). **Revised the same day
> (s265) by the same subagent** to record Cray's typed rulings on SD-1..SD-5 and fold in
> two specialist investigations (DSL expressibility; the core-promotion bill) — every
> specialist claim re-verified on disk by this revision except the two explicitly marked
> "measured by Code, s265" (a DB row count and prompt byte sizes, F12/F13). **Revised a
> second time the same day (s265, same subagent)** to close SD-3a per Cray's typed
> ruling and propagate it; the ruling's structural grounds (description dropped at load
> by design, schema legality of a property `description`, the honest-no-records path)
> re-verified on disk by this second revision — only the byte figures remain "measured
> by Code, s265". **Revised a third time (s265, same subagent) — a correction pass:**
> Code's offline measurement (F17: the ontology does not reach the procedure agent's
> prompt; positive-controlled) narrows the theory of change, and Cray's typed SD-6
> ruling fixes the measurement surface. Every F17 grep count, the positive control, the
> prompt-builder signatures, the orchestrator near-miss, and the six-vertical `reads:`
> staleness evidence were re-verified on disk by this revision before citing.
> Independent review: Cray at PR merge. Code commits via PR
> (CLAUDE.md §7); the drafter does not commit.

---

## Goal

Extend the `fleet_maintenance` ontology — and the synthetic seed that makes its
declarations answerable — to carry **supplier-evaluation facts**: the vendor-standing
and service-history facts the ratified rationale bar named as missing. The bar is
role-naming alone **because** "is this the right supplier, does their delivery history
support accepting this quote, how does it compare with the alternatives — rest on facts
the ontology does not yet carry" (`benchmarks/procedure_baseline/grader.py:83-91`;
`benchmarks/model_compare/RESULTS-1.6.md:706-718` §13;
`docs/lessons/0052-a-criterion-may-only-demand-what-the-run-supplies.md:69-74`). That
framing is right that the facts have no home — and this PLAN builds the home. What it
does **not** do is put those facts in front of the procedure model, because the
ontology is not on that model's prompt path at all (**F17, measured s265 with a
positive control**). Stated plainly, in three parts:

- **What this PLAN DOES unlock, and it is real: the NL / Ask surface (Tab C).**
  `_describe_ontology` genuinely feeds the translate prompt there (F13), and the seed
  serves the values — a visitor asking "which garage has the most comebacks?" becomes
  answerable, on a live, visitor-facing surface of the published demo. This is where
  the ontology's effect on the MS-S1 models will be measured (**SD-6, RULED**:
  `benchmarks/nl_query_feasibility/`).
- **What it does NOT unlock on its own: the `procedure_baseline` rationale lane.**
  The procedure agent's prompt is built from exactly four inputs — a static role
  string, the `procedures.yaml` goal, the handler catalog, and the event (F17) — and
  a declared ontology property routes into none of them. Adding properties alone
  moves **nothing** in that lane.
- **The missing second half, named as unscoped work:** for supplier facts to reach
  the procedure model, something must carry them into the **event** (the adapter's
  event builders, `verticals/fleet_maintenance/data_adapter/synthetic.py:175,198`) or
  into the **goal** text (`procedures.yaml` — SD-4 deliberately parked goal edits
  with the later grader PLAN). **Nobody has scoped that carrier.** It is not this
  PLAN's job; its absence is recorded in Out of Scope so it is visible here, not
  discovered later.

The rationale-lane statement per RESULTS §13 ("each supplier-evaluation fact that
enters the ontology **and the goal** makes a stricter rule answerable") therefore
needs all its halves read literally: the goal/dataset/grader half rides together in
the later PLAN (SD-4, **RULED (a)**), the value-carrier is unscoped, and this PLAN
supplies the declaration + Ask-surface half. This PLAN is still worth executing
exactly as ruled: `Vendor` property declaration is a **prerequisite for anything
supplier-shaped on either surface** — no carrier, goal edit, or grader move can
reference a fact that has no declared home. It demands nothing of any model.

Shape, per the s265 rulings: **SD-1=(c)** — the values ship as DEMO-SEED,
provenance-marked **AUTHORED**, with the measured-projection route recorded in YAML
comments as the promotion path (the house rule: a backfilled/authored value carries its
provenance). **SD-2=SPLIT** — this PLAN is the **fleet-side extension only**; the core
promotion is **deferred, not rejected**, to its own ADR+PLAN, with its durable record in
the Out-of-Scope deferred-core block below. **SD-3+SD-3a — the declaration is
two-banded:** the 5 narrative-grounded facts carry Thai synonyms and seed values (the
"answerable" band above); the donor's 4 remaining compliance properties (`tax_id`,
`cert_status`, `sanctions_flag`, `single_source_flag`) are declared **bare + rich
`description`, NO synonyms, NO seed values** — prompt-visible by name so the
Ask/translate LLM can use them the moment a value exists (Cray's requirement (c);
the procedure model sees no ontology property either way, F17), while an unpopulated
one routes honestly to the no-records answer (F15) rather than a fabrication.

## Correction record (s265, third pass) — believed, measured, stands

⚠️ **Corrected 2026-08-31 (s265).** Recorded in the house idiom for a corrected
claim: what was believed, what was measured, what now stands.

- **Believed (this PLAN's own earlier title + Goal):** that this PLAN was "the
  rationale-bar unlock, supply side" — i.e. that declaring the supplier facts in the
  ontology was **the** unlock for raising the `procedure_baseline` rationale bar,
  inheriting `grader.py:83-91`'s "an **ontology** move before it is a grader move"
  and Lesson 0052's "the ontology work is now the **named unlock**" at face value.
- **Measured (Code, s265, offline, positive-controlled — F17):** the ontology never
  reaches the procedure agent's prompt. `build_reasoning_messages` →
  `build_system_instruction(vertical: str, goal, catalog)` builds it from a static
  role string, the goal, the handler catalog, and the event — the vertical parameter
  is a `str` name, never `OntologyMeta`. `grep -c ontology` = 0 on both prompt-path
  modules while the **same grep returns 18 on `nl_query.py`** (the control that makes
  the zeros evidence rather than a broken grep). Declaring a property routes it into
  neither the event nor the goal — the only two channels that reach that model.
- **Stands:** (i) the sources' literal claims are still true — the facts had no home,
  and RESULTS §13's own wording already named "the ontology **and the goal**"; (ii)
  what died is the *reading* that declaration alone puts facts in front of the
  procedure model; (iii) this PLAN's unlock is the **NL / Ask surface**, where the
  ontology genuinely feeds the prompt, and that is where the effect is measured
  (SD-6); (iv) the rationale lane additionally needs the goal edit (SD-4, later PLAN)
  **and** an unscoped value-carrier into the event or goal (Out of Scope); (v) every
  AC of this PLAN stands unweakened — **this correction narrows a claim, not a
  criterion** — and the work is still worth executing: no surface can use a fact
  that has no declared home. A post-F17 reading note on SD-3a: "the LLM must be able
  to use them" in Cray's requirement (c) is satisfied on the **Ask/translate model**
  — the mechanism the ruling itself cites is `_describe_ontology` — not on the
  procedure model, which sees no ontology property until the carrier exists.

**Retired-claim handling (`docs/conventions/retired-claims.md`, checked — judged NOT
to emit a marker from this PLAN; stated explicitly, not silently picked):** (1) the
verbatim source wordings are **not dead claims** — `grader.py:83-91` truly states the
facts "rest on facts the ontology does not yet carry", and RESULTS §13 names both
halves — so retiring their text would kill true sentences; what died is a *reading*,
whose only verbatim home was this PLAN's own pre-amendment title/Goal, rewritten in
place on the unmerged PR branch — no live stale copy survives for a marker to guard;
(2) a marker matching `grader.py`'s or Lesson 0052's live wording would fail the
guard against those files and force cross-file edits this correction pass must not
make (the grader is this PLAN's own first Out-of-Scope bullet). One candidate stale
copy IS named for later propagation per the convention's backfill rule: Lesson
0052:71-72 ("the ontology work is now the named unlock") is now half-true — true for
the Ask surface, incomplete for the rationale lane — and should gain its
qualification (with a retire marker if reworded) whenever that lesson or the later
grader PLAN next touches it. Likewise `orchestrator.py:569`'s stale "every shipped
procedure is reads-absent" docstring (F17) — noted, not fixed here.

## Baseline facts (verified on disk 2026-08-31 by this draft — cite, don't re-derive; re-confirm line numbers on the execution branch, the base moves)

- **F1.** The unlock framing is recorded in three places and is not re-argued here:
  `grader.py:73-96` (`role_vocabulary` — "a model is only ever measured against
  vocabulary its **own prompt handed it**"; the cap on strictness), RESULTS-1.6 §13
  (`:706-718` — "an **ontology** move before it is a grader move"; requiring the amount
  scored 0/14 vs ~3/14, "unmeasurable, not undesirable"), and
  `benchmarks/procedure_baseline/rationale_regrade.py:123-131` ("As supplier-evaluation
  facts enter the ontology and the goal, each …"). ⚠️ **Scope corrected s265 (F17 +
  the Correction record):** these three correctly record the demand-side cap; the
  supply they call for is two-channel (declared home + a carrier into the goal/event),
  and this PLAN builds only the first channel.
- **F2.** Fleet's object types today (`verticals/fleet_maintenance/ontology/fleet_maintenance_v0.yaml:32-282`):
  Truck, Vendor, Depot, OperationalEvent, Alert, RecommendedAction, AlertEventLink —
  **no supplier-evaluation facts anywhere**. `Vendor` (`:105-151`) carries exactly
  `vendor_id`, `name`, `accounting_code`, and its own description (`:120-127`) settles
  the free-text seam: `RepairCaseQuote.vendor` et al. "stay free text on purpose"; the
  registry resolves typed names by exact trimmed case-insensitive match, never fuzzily.
- **F3.** The donor: `verticals/procurement/ontology/procurement_v0.yaml:201-327`
  ships `Supplier` (`avl_status`, `tax_id`, `cert_status`, `sanctions_flag`,
  `single_source_flag`), `Quotation` (`price`, `currency`, `lead_time`, `warranty`,
  `on_contract`), `PurchaseOrder`, `ComplianceRule`, `ApprovalTier` (built by
  `done/0036`). **This is a port with a filter, not an invention** — SD-3 + SD-3a are
  the filter (two-banded since the SD-3a ruling: synonym-carrying vs bare-dormant).
  Donor types for the dormant four, verified at `:216-225` by this revision: `tax_id`
  string; `cert_status` enum `[valid, expired, none]`; `sanctions_flag` bool;
  `single_source_flag` bool.
- **F4.** The run's prompt supply chain (`services/engine/llm/prompt.py:133-156`):
  system = vertical + **goal** + catalog; the event reaches only the untrusted block.
  The ontology is among **none** of these inputs — measured, with a positive control,
  as F17.
  Fleet's goal (`verticals/fleet_maintenance/procedures.yaml:133-143`) currently
  instructs: the sourcing gate "is applied DOWNSTREAM by the engine and not by you …
  never withhold a routing decision on quote counts." Any future goal wording that asks
  the model to weigh vendor history must be written **against** that sentence, not past
  it — SD-4.
- **F5.** The sourcing gate (`verticals/fleet_maintenance/sourcing.py:1-60`) is pure,
  deterministic, count-based, and downstream — the caller supplies counts; nothing
  surfaces vendor facts to the LLM as named facts. Its fraud provenance (`:33-36`,
  "adopted after being defrauded on parts") is the narrative ground for a vendor
  `standing` fact (SD-3).
- **F6.** The evidence-table seam: real quote rows live in a **hand-written** ORM
  outside the ontology layer — `services/db/repair_case_evidence.py:73-122`
  (`RepairCaseQuote`: `vendor` free text `:106`, `amount_thb` Numeric `:108`). Fleet
  has **no committed generated code**: `_ORM_COMMITTED_DEST` = {energy, core},
  `_PYDANTIC_COMMITTED_DEST` = {core} (`services/engine/code_generator.py:900-914`);
  `generate_all` (`:917-939`) falls back to gitignored
  `verticals/fleet_maintenance/generated/` for fleet. **A YAML edit needs no
  migration** — confirmed under the SD-1 ruling (c): option (b)'s projection half
  enters this PLAN only as comments, never as code.
- **F7.** The golden guard (dispatch constraint: named here):
  `tests/services/engine/scaffolder/test_golden_e2e.py:341-349` asserts the donor's
  **object-type set** and **link-type set** against the scaffolder's emission, with a
  hand-maintained exemption `_DONOR_EXTENSION_OBJECTS = {"Vendor"}` (`:318-324`) whose
  comment warns: past "a couple of entries", build an extension slot instead.
  Consequences, verified in the assertion text: (i) **property** extension of the
  already-exempt `Vendor` is invisible to this oracle by construction (`Vendor` is
  subtracted before comparison, `:343`); (ii) a **new object type** reddens it and
  grows the exemption; (iii) a **new link type** reddens it with **no exemption slot at
  all** (`:349` is bare set equality). This prices SD-3's shape options.
- **F8.** The contract guard: `tests/verticals/fleet_maintenance/test_ontology_data_contract.py`
  is generic and two-directional — every `required` property present in every row
  (`:44-55`), no row carries an undeclared property (`:58-67`) — and its own docstring
  (`:8-11`) names the gap this PLAN must close for **non-required** properties:
  "declare a property … forget the value in `synthetic.py`, and NOTHING goes red" while
  `/meta` advertises it. `:120-134` proves Thai synonyms reach `_describe_ontology` —
  "the line between 'in the ontology in principle' and 'answerable'".
- **F9.** The seed: `verticals/fleet_maintenance/data_adapter/synthetic.py:328-364`
  (`vendor_records` — three garages, one deliberately uncoded so the AC-9 KPI stays
  non-vacuous; `OBJECT_SOURCES` `:367-371`). The uncoded-row honesty pattern is the
  template for the new facts' "no history yet" row (Step 3).
- **F10. 🔴 Grounded negative (dispatch constraint 3, answered):**
  `tools/check_ontology_orm_lockstep.py` does **not exist on disk** (verified by direct
  read, 2026-08-31). It is **PLAN-0109's deliverable** (its AC-3 / Step 2; its F9
  records the same grounded negative). Either way it cannot bite here: the guard
  compares YAML↔ORM per a declared type↔table mapping, and `Vendor` is a synthetic
  type with no ORM table — outside the mapping under both PLANs.
- **F11.** The benchmark's fleet ground truth
  (`benchmarks/procedure_baseline/dataset/fleet_maintenance.yaml:1-56`) authors its
  scenarios to stay faithful to real ontology-projected events (B-β calibration,
  `harness.py:61`). It carries no vendor facts today; mirroring new facts into it is
  the later PLAN's move (Out of Scope).
- **F12.** (measured by Code, s265 — a DB measurement this draft cannot re-derive
  offline; re-confirmable at execution) The month-end export currently contains
  **exactly one row** (`case-fleet-demo-history`). SD-1 option (b)'s "a history of
  n=1 cases is noise wearing a number" is therefore **measured, not asserted** — the
  evidentiary ground for ruling (c) over (b)-now.
- **F13.** Prompt-cost facts (fed SD-3a; now the ruling's evidentiary ground).
  Structural halves, verified on disk by this revision (and re-verified by the second
  s265 revision — the base moves): `_describe_ontology`
  (`services/engine/nl_query.py:382-398`) renders **every declared property with no
  value check**, and `PropertyMeta` (`services/engine/ontology_meta.py:268-285`)
  carries no visibility/queryable flag — so "auto-skip when unpopulated" **does not
  exist today**; `services/engine/ontology_schema.json` sets
  `additionalProperties: false` at every level, so a documentation-only YAML parking
  key is inexpressible. **The description half (decisive for SD-3a):** a property-level
  `description` IS schema-legal (`ontology_schema.json:79`), but `_property_meta`
  (`ontology_meta.py:268-285`) drops it at load — `PropertyMeta` carries only
  `name, type, required, enum, target, synonyms, sample_values` — and
  `_property_aliases`'s docstring (`nl_query.py:363-371`) records this as
  **deliberate design**: "``description`` is deliberately NOT rendered … content aimed
  at a human reader of the YAML, not at the model." A rich `description` therefore
  costs **ZERO prompt bytes**, by design. **Synonyms are the expensive part, not
  declaration**: the existing `name` property's synonym list alone is ~90 B against
  ~17-26 B for a bare name+type line (measured by Code, s265). Sizes (measured by
  Code, s265; re-derivable at execution from `len(_describe_ontology(meta).encode())`):
  the fleet schema block is **1,945 B** across 7 object types; the `Vendor` line is
  339 B; the 5 ruled-IN properties add **+145 B (7.5%)**; the 4 dormant ones add
  **+107 B (5.5%)** — roughly 30 tokens per translate call (whether that figure
  already includes `cert_status`'s rendered enum values is re-derivable at execution;
  no AC pins a byte number).
- **F14.** PLAN-0111 (`docs/plans/0111-fleet-closeout-credit-note-record.md`) touches
  **neither** `fleet_maintenance_v0.yaml` **nor** `ontology/` — grep for both terms
  returned zero matches (verified by this revision, 2026-08-31). The earlier
  "asserted-not-verified" residual note about 0111 is **CLOSED** (see Coordination §5).
- **F15.** The honest-no-records path (verified on disk by the second s265 revision —
  the mechanism the SD-3a ruling's requirement (b) rides on): an empty match
  short-circuits to `_no_data_nlanswer` (`services/engine/nl_query.py:1369-1371` →
  `:1280-1283`, "no record matched, so no fact is invented"); a resolve miss takes the
  same path (`:1354-1358`). A declared-but-unpopulated property filtered on therefore
  yields a grounded-but-empty answer through **existing** machinery — partial
  population needs **no new mechanism**.
- **F16. ⚠️ Asserted-not-verified — UNMEASURED.** The answer-quality effect of the
  wider translate vocabulary (9 new property names in every translate call, 4 of them
  valueless): a model may attempt queries that return empty more often. This is
  **unmeasured**; measuring it needs a live MS-S1 run under a typed CLAUDE.md §8 go.
  Recommendation (Code, s265, adopted by this draft): fold that measurement into the
  later grader PLAN's MS-S1 run — which re-baselines the lane anyway (SD-4 ruling) —
  rather than paying for a separate host-state round. Until then, every claim that
  the dormant band is behaviourally free rests on the offline F15 mechanism only.
  ⚠️ **Recommendation superseded by the SD-6 ruling (s265, kept as lineage):** the
  ruled surface for measuring the ontology's effect on the MS-S1 models is route (a),
  `benchmarks/nl_query_feasibility/` — F16's vocabulary-width question rides THAT run
  (it is a translate-surface effect, so route (a) is also where it is observable),
  still under its own typed CLAUDE.md §8 go.
- **F17. 🔴 Measured (Code, s265, offline, positive-controlled; every count and
  anchor re-verified on disk by this revision — re-verify again before citing, the
  base moves): the ontology does NOT reach the procedure agent's LLM prompt.** The
  prompt on that path is built by `build_reasoning_messages` →
  `build_system_instruction(vertical: str, goal, catalog)`
  (`services/engine/llm/prompt.py:72-138`) from exactly four inputs: (1) a static
  `role` string keyed on the vertical **name** — a `str`, never `OntologyMeta`; (2)
  `goal` — the procedure's directive from `procedures.yaml`; (3) `catalog` —
  `registry.handler_catalog` (handler names + descriptions); (4) the `event` dict,
  rendered by `format_event` (`:122`) into the untrusted block. Evidence:
  `grep -c ontology` → `services/engine/llm/prompt.py` = **0** (0 even
  case-insensitive), `services/engine/llm/structured.py` = **0** (the single
  case-insensitive hit is the capitalized English word inside a static
  `Field(description=...)` at `structured.py:101` — schema prose, not a meta feed),
  `services/engine/procedures/action_step.py` = **1**, and that hit is a docstring
  phrase ("ontology-projected keys", `:234`), not a prompt feed. **Positive control
  (what makes the zeros evidence rather than a broken grep):** the same
  `grep -c ontology` on `services/engine/nl_query.py` returns **18** — the NL path
  genuinely consumes the ontology via `load_ontology_meta` → `_describe_ontology`.
  Near-miss, classified: `services/engine/procedures/orchestrator.py`'s
  `validate_read_bindings_for_vertical` (`:562-577`) DOES call `load_ontology_meta`
  (`:574`) — a **validation gate**, not a prompt feed; loading is not prompting.
  ⚠️ That function's docstring claim "every shipped procedure is reads-absent"
  (`:569`) is **STALE** — all six verticals declare `reads:` in their
  `procedures.yaml` (10 occurrences across 6 files; fleet: 3) — noted here because
  it could mislead a reader re-tracing this measurement; fixing that file is out of
  scope. **Consequence:** the only channels into the procedure model are the
  **event** (built by `operational_events` / `_fixture_events`,
  `verticals/fleet_maintenance/data_adapter/synthetic.py:175,198`) and the **goal**
  text — declaring an ontology property routes it into neither.

## Coordination with PLAN-0109 (required — the two PLANs edit the same file)

`docs/plans/0109-fleet-repair-cases-queryable-from-ask.md` Step 1 (`:338-355`) edits
`fleet_maintenance_v0.yaml` — it **adds three new object types** (SD-B **RULED**:
`RepairCase`, `RepairCaseQuote`, `RepairCaseAcceptedQuote`, `/meta` 7 → 10), grows
`_DONOR_EXTENSION_OBJECTS`, and builds the lockstep guard (F10). PLAN-0109 is Draft,
unexecuted, and execution-unblocked (all its blocking SDs ruled).

**Partition (this PLAN's contract, under the ruled SD-3 shape — property-only
extension of the existing `Vendor` block):**

1. **Disjoint file regions.** 0109 appends new type blocks; 0117 edits **inside the
   existing `Vendor` block only** (`:105-151`). A textual merge is clean in either
   landing order.
2. **Disjoint guard surfaces.** 0117 does not touch `_DONOR_EXTENSION_OBJECTS`
   (AC-5 asserts a zero diff); `Vendor` is outside the lockstep guard's mapping (F10);
   0109's AC-1(b) asserts the exact **type-name** list, which property edits cannot
   move; 0117's AC-1(b) asserts the exact **Vendor property** list, which 0109 does
   not touch.
3. **Scope fence.** SD-3 + SD-3a as ruled include **no quote-level facts** — both
   bands are vendor-level; the SD-3a ruling named only the four vendor-level
   properties, and quote-level `warranty` / `on_contract` were **not** in Cray's
   ruling (they stay OUT as a partition boundary, not a cost call — see Out of
   Scope). Standing fence, kept: if any later amendment ever adds a quote-level fact
   (e.g. a per-quote `warranty`), it lands as an amendment to PLAN-0109's
   RepairCaseQuote declaration (whose PII/lockstep/ROPA machinery already governs
   that block), **never** in this PLAN. 0117 stays off the `RepairCase*` blocks
   entirely.
4. **Sequencing (SD-5 — RULED (a), Cray, typed, 2026-08-31, s265): no forced order.**
   Whichever PLAN lands second rebases and re-runs
   `tests/verticals/fleet_maintenance/` + the scaffolder suite before its PR. 0117's
   counts are asserted **relative to the branch baseline** (AC-6), never pinned to
   7-vs-10, precisely so either order stays green. In practice 0109 likely lands
   first (it is fully ruled); nothing here waits for it.
5. **PLAN-0111 is not a party.** Verified by this revision (F14): it names neither
   `fleet_maintenance_v0.yaml` nor `ontology/` — zero grep matches — so no
   coordination contract with 0111 is needed, and the earlier residual gap about it
   is closed.

## Acceptance Criteria

Commands run from the repo root via WSL under CLAUDE.md §8 evidence rules (`2>&1`,
no `head`/`tail` pipes, verdicts read from files). Two ruled bands (both typed, Cray,
2026-08-31, s265): **the synonym-carrying set** (SD-3) = `standing`, `is_contracted`,
`repairs_completed_count`, `comeback_count`, `avg_turnaround_days` — Thai synonyms +
seed values + AUTHORED stamps; **the dormant set** (SD-3a) = `tax_id`, `cert_status`,
`sanctions_flag`, `single_source_flag` — bare declaration + rich `description`,
**no `synonyms` block, no seed values**. Where an AC says "the ruled IN-set" it means
the synonym-carrying five; the dormant four have their own contract (AC-3a). Every
witnessed-RED probe below runs through the shipped driver `tools/probe_battery/`
(CLAUDE.md §8 — never a from-scratch script), one mutation per assertion, restore
from the scratchpad copy.

- [ ] **AC-1 — the YAML declares BOTH ruled bands on `Vendor`, schema-valid.**
  Artifact: `verticals/fleet_maintenance/ontology/fleet_maintenance_v0.yaml`.
  Command (a): `uv run --no-sync pre-commit run check-jsonschema --all-files 2>&1`
  → exit 0 (this also witnesses that a property-level `description` is schema-legal,
  `ontology_schema.json:79` — the SD-3a mechanism). Command (b):
  `uv run python -c "from services.engine.ontology_meta import load_ontology_meta; m=load_ontology_meta('fleet_maintenance'); print(sorted(p.name for o in m.object_types if o.name=='Vendor' for p in o.properties))"`
  → pass read fixed pre-run: exactly the 3 baseline names (F2) plus the
  synonym-carrying five plus the dormant four:
  `['accounting_code', 'avg_turnaround_days', 'cert_status', 'comeback_count', 'is_contracted', 'name', 'repairs_completed_count', 'sanctions_flag', 'single_source_flag', 'standing', 'tax_id', 'vendor_id']`.
  Command (c) — **the SD-1(c) comment contract** (two assertions):
  `grep -c "AUTHORED / DEMO SEED" verticals/fleet_maintenance/ontology/fleet_maintenance_v0.yaml 2>&1`
  → ≥ 5 (one stamp per synonym-carrying property; the dormant four carry **no**
  AUTHORED stamp — nothing is authored for them, their `description` is their
  contract, AC-3a(c)), and
  `grep -n "PROMOTION PATH" verticals/fleet_maintenance/ontology/fleet_maintenance_v0.yaml 2>&1`
  → exactly one block, naming the SD-1(b) measured-projection route.
  **Witnessed RED (one probe per assertion):** (a) a scratch undeclared key inside a
  Vendor property block → the hook exits non-zero naming the file
  (`additionalProperties: false`, per 0109 F12); (b) remove exactly **one** declared
  property from the YAML — **pick a dormant one** (e.g. `tax_id`), so the five's
  synonyms are genuinely untouched and AC-2 stays green under this mutation (the
  cross-green that isolates the probe; the second s265 revision repaired this probe —
  removing a synonym-carrying property would have reddened AC-2 as well, voiding the
  isolation the original text claimed); (c1) strip one property's AUTHORED stamp → the count drops below 5
  while the PROMOTION PATH grep stays green; (c2) delete the PROMOTION PATH comment
  line → that grep exits non-zero while the stamp count stays ≥ 5 — two mutations,
  two assertions, each with the other's green as isolation.
- [ ] **AC-2 — the facts are Thai-addressable in the translate prompt.**
  Artifact: a new test in `tests/verticals/fleet_maintenance/test_ontology_data_contract.py`
  (the `:120-134` pattern) asserting `_describe_ontology(meta)` contains one designated
  Thai synonym **per synonym-carrying property** (the five — e.g. `ประวัติงานซ่อม`,
  `อู่คู่สัญญา`; the dormant four are synonym-free **by ruling**, guarded by AC-3a's
  cost guard) and still excludes provenance prose.
  Command: `uv run pytest tests/verticals/fleet_maintenance/test_ontology_data_contract.py -x 2>&1`.
  **Witnessed RED:** delete only the `synonyms` block of one ruled property → this test
  reddens on that synonym while AC-1(b) stays green (the property remains declared) —
  one mutation, one assertion, other-assertion-green.
- [ ] **AC-3 — the seed carries values for the synonym-carrying five (closing F8's named gap for non-required properties).**
  Artifact: `verticals/fleet_maintenance/data_adapter/synthetic.py` (`vendor_records`)
  + a new presence test in `test_ontology_data_contract.py`: for **each**
  synonym-carrying property, at least one vendor row carries a non-null value (the
  positive control — the dormant four are **excluded by ruling**: unpopulated is
  their contracted state, asserted by AC-3a(b)),
  **and** at least one vendor omits the history facts (the F9 honesty pattern — a
  garage genuinely can have no history yet; keeps any future completeness KPI
  non-vacuous). The existing generic direction-2 guard (`:58-67`) covers undeclared
  keys.
  Command: same module, same pytest command as AC-2.
  **Witnessed RED (two assertions, two probes):** (a) blank the sole carrying row's
  value for one ruled property → the presence test reddens naming that property
  (YAML untouched → AC-1/AC-2 stay green); (b) add a scratch key `x_scratch` to one
  vendor row → the **existing** `test_no_row_carries_a_property_the_ontology_never_declared`
  reddens — witnessing that the pre-existing guard, not a new copy of it, patrols
  direction 2.
- [ ] **AC-3a — the dormant band contract (SD-3a): declared, prompt-visible,
  synonym-free, unpopulated, description-carrying.** Artifact: a new dormant-band
  test in `test_ontology_data_contract.py` (it may read the raw YAML — descriptions
  are dropped at load, F13, so loaded meta cannot check assertion (c)). Command:
  `uv run pytest tests/verticals/fleet_maintenance/test_ontology_data_contract.py -x 2>&1`.
  Five assertions, each with its own probe:
  (a) **prompt-visible** — `_describe_ontology(meta)` contains each of the four names
  (Cray's requirement (c): the LLM can use a dormant property the moment a value
  exists, with zero code change). Probe: remove one dormant property from the YAML →
  this assertion reddens naming it while (d) on the remaining three stays green.
  (b) **unpopulated** — no `vendor_records()` row carries any of the four keys
  (dormant = no authored value; also what makes the SD-3a residual concern inert in
  this PLAN — an unpopulated flag cannot disagree with the per-case record). Probe:
  add `sanctions_flag: false` to one seed row → this assertion reddens naming the
  row, YAML untouched so (a)/(c)/(d) stay green — and the existing
  undeclared-key guard also stays green (the key IS declared now), witnessing that
  THIS guard, not that one, patrols dormancy.
  (c1) **description present** — every one of the four carries a non-empty raw-YAML
  `description` explaining declared-but-unpopulated and why. Probe: blank `tax_id`'s
  description → reddens while (c2) stays green.
  (c2) **the residual-concern mitigation** — `single_source_flag`'s description
  names `RepairCaseJustification` as the authoritative record. Probe: strip that
  token from the description → reddens while (c1) stays green (the description is
  still non-empty).
  (d) **the cost guard (dispatch-mandated)** — each of the four has
  `synonyms is None` in loaded `PropertyMeta` (equivalently: its rendered line
  carries no `; aka`), so nobody silently adds the ~90 B-per-list synonym cost
  (F13); synonyms for these four arrive only via a deliberate later YAML edit when
  the narrative brings the Thai term. Probe: add a `synonyms: {th: [...]}` block to
  one of the four → this assertion reddens while (a) stays green (the property
  still renders) — the isolation that proves the redden is about synonyms, not
  declaration.
- [ ] **AC-4 — scenario test (CLAUDE.md §8, binding): a supplier-evaluation question is
  answerable end-to-end offline.** Artifact:
  `tests/verticals/fleet_maintenance/test_vendor_facts_scenario.py`. Real producer →
  real consumer: the registered fleet synthetic adapter through
  `answer_question(question, "fleet_maintenance", client=<transport stub>)` — translate
  → execute → phrase all real, only the LLM *transport* canned (`TranslateOnlyStub`,
  the PLAN-0104 precedent) — asking a question over a ruled property (e.g. count of
  vendors with `standing == approved`, and a lookup of the contracted garage).
  Pass read fixed pre-run: `grounded is True`; the count equals the seed's authored
  figure; the lookup's source ids are the seed's `vendor_id`s (rows flowed, not a
  fixture constant). **Plus the dormant case (SD-3a requirement (b), riding F15's
  existing machinery):** a question filtering on a dormant property (e.g. vendors
  with `sanctions_flag == true`) terminates in the honest no-records answer
  (`_no_data_nlanswer`, `nl_query.py:1369-1371`) — grounded-but-empty, never a
  fabricated fact. Makes **no claim** any live model emits the translation — that is
  MS-S1 territory and out of scope (the vocabulary-width effect on live translate
  quality is explicitly UNMEASURED, F16).
  Command: `uv run pytest tests/verticals/fleet_maintenance/test_vendor_facts_scenario.py -x 2>&1`.
  **Witnessed RED / named changing output:** flip one seed row's `standing` → the
  asserted count changes by exactly 1 — the probe's mutation reaches the code and
  names the output it changes. **Dormant-case probe (its own mutation):** author
  `sanctions_flag: true` onto one seed row → the no-records assertion reddens (the
  answer now carries a record) — proving the case exercises the live no-data path,
  not a constant; AC-3a(b) reddens on the same mutation in ITS run, which is exactly
  the two-guard agreement expected, not a confound.
- [ ] **AC-5 — the golden oracle stays green with ZERO exemption growth.**
  Artifacts: `tests/services/engine/scaffolder/test_golden_e2e.py` — **unmodified**.
  Command (a): `uv run pytest tests/services/engine/scaffolder/ -x 2>&1` → green.
  Command (b): `git diff --stat tests/services/engine/scaffolder/ 2>&1` → empty (the
  F7 tripwire: this PLAN adds no object types and no link types, so the exemption must
  not move).
  **Witnessed RED (proving the oracle is alive, not merely un-tripped):** add a scratch
  object type `ScratchObject` to the fleet YAML → the set-equality assertion (`:348`)
  reddens naming it; restore from scratchpad. This is the probe for the surface this
  PLAN promises not to touch.
- [ ] **AC-6 — the rest of the vertical is untouched, relative to the branch baseline.**
  Command: `uv run pytest tests/verticals/fleet_maintenance/ 2>&1` → green with zero
  modified assertions in pre-existing tests; object-type count and link-type count
  equal the branch baseline captured in Step 1 (7/7 links pre-0109, 10/7 post-0109 —
  asserted relative, per Coordination §4).
  **Witnessed RED:** covered by AC-5's scratch-object probe (the count read moves on
  the same mutation); no second mutation needed for the same surface.
- [ ] **AC-7 — codegen produces zero committed drift, with a positive control.**
  Command: run fleet codegen via the console script (`uv run vero-lite …` — never
  `python -m`), then `git status --porcelain 2>&1` written to a file → **empty** (F6:
  fleet's outputs are gitignored). **Positive control (an absence claim needs one —
  CLAUDE.md §8):** `grep -n "standing" verticals/fleet_maintenance/generated/schema.json 2>&1`
  (or the ruled set's first property) → present, proving the regen actually ran and
  expressed the new facts; an empty porcelain from a codegen that did nothing would
  otherwise pass vacuously.
- [ ] **AC-8 — full offline gate at CI scope.**
  Commands: bare `uv run ruff check . 2>&1`; full `uv run mypy services/ verticals/ 2>&1`;
  full `uv run pytest tests/ 2>&1` on the checkout that owns the test DB. Pass read:
  all green — partial-scope greens do not close this AC.

## Out of Scope

- ❌ **The grader move.** `benchmarks/procedure_baseline/grader.py`, the rationale
  lane, `rationale_regrade.py`, and any change to `carries_content` or the ratified
  role-naming bar (Cray, typed 2026-08-31). Raising the demand side is a **later,
  separate PLAN** — this PLAN gives the facts a declared home and makes them
  answerable on the Ask surface; rationale-lane expressibility additionally needs the
  goal edit (SD-4, that PLAN) **and** the unscoped carrier (next bullet, F17).
- ❌ **The procedure-side carrier — unscoped by ANYONE; named so its absence is
  visible here, not discovered later (F17).** For supplier facts to reach the
  procedure model at all, something must carry values into the **event** (the
  adapter's event builders, `synthetic.py:175,198`) or into the **goal** text
  (`procedures.yaml` — goal edits parked with the grader PLAN by SD-4's ruling).
  No PLAN owns that carrier today. It is not this PLAN's job to build or scope it —
  but whoever scopes the later grader PLAN must scope the carrier with it, or the
  rationale lane stays unmovable regardless of grader edits.
- ❌ **`procedures.yaml` goal text** (SD-4 — **RULED (a)**, Cray, typed, 2026-08-31,
  s265) — the goal is the vocabulary source `role_vocabulary` caps the lane by
  (F1/F4); it moves **with** the grader PLAN so supply and demand land in one
  reviewable diff, its "never withhold a routing decision on quote counts" sentence
  gets rewritten against, not past (F4), and **the re-baseline happens once, there**.
- ❌ **The benchmark dataset** (`dataset/fleet_maintenance.yaml`, F11) — mirroring the
  new facts into scenarios is the demand-side lockstep, same later PLAN.
- ❌ **MS-S1 / any live model run** — host-state, typed Cray go required (CLAUDE.md
  §8). This PLAN is deterministic-offline end to end. Where the eventual live
  measurements go, per the s265 rulings: **the ontology's effect on the two MS-S1
  models is measured on route (a), the NL / Ask surface
  (`benchmarks/nl_query_feasibility/`) — SD-6, RULED** — and F16's UNMEASURED
  vocabulary-width effect (does the wider translate vocabulary, 4 valueless names
  included, raise the empty-result rate?) rides that same route-(a) run.
  Re-measuring the 0/14 vs ~3/14 rationale-lane figures stays with the grader PLAN
  under its own go — and is **deferred until the procedure-side carrier is scoped**
  (previous bullet): before the carrier exists, a procedure-side run would measure a
  channel that does not exist (F17).
- ❌ **NOT swept in by the SD-3a ruling** (stated so nothing rides in silently —
  Cray's ruling named exactly four properties, all vendor-level): quote-level
  `warranty` / `on_contract` stay OUT — they are PLAN-0109's block, a **partition
  boundary** (Coordination §3), not a cost call; and `last_engaged_at` stays OUT —
  derivable, hold until a consumer asks (SD-3's original reason, untouched by the
  ruling). Reopening either takes a fresh typed ruling, not this PLAN.
- ❌ **Synonyms for the dormant four** — deliberately absent under the SD-3a ruling
  (the ~90 B-per-list cost, F13, is the expensive half); they arrive as a later
  cheap YAML edit if and when the narrative actually uses the Thai term, and
  AC-3a(d)'s cost guard makes any earlier addition redden a test.
- ❌ **New object types or link types** — settled by the SD-3 ruling (property-only
  extension; the `VendorServiceRecord` alternative is dead): a new object grows
  `_DONOR_EXTENSION_OBJECTS` against its own tripwire, and a new link reddens the
  golden oracle with **no** exemption slot (F7). Only a fresh typed ruling reopens
  this line.
- ❌ **DB backing, migrations, or projecting `repair_case_*` rows into Vendor facts**
  — SD-1's ruling (c) takes only the **comment** half of option (b): the projection is
  *named* as the promotion path, never built here. No alembic touch; fleet has no
  committed ORM (F6); the free-text `vendor`→registry join and its honesty rules stay
  exactly as `Vendor`'s description states them (F2).
- ❌ **Anything in PLAN-0109's scope** — the `RepairCase*` declarations, the lockstep
  guard, the session-owning adapter, the ROPA/retention corrections (Coordination §3's
  fence).
- ❌ **Promotion of a shared counterparty shape into `ontology/` core — DEFERRED,
  NOT REJECTED** (SD-2 ruling: **SPLIT** — Cray, typed, 2026-08-31, s265). The core
  promotion goes to its **own ADR + PLAN** (both unnumbered today); until they exist,
  **this block is the deferral's durable, tracked home** — a deferred item whose only
  record is a closed conversation rots, and that is the failure mode this block
  exists to prevent. The companion STATUS row is proposed below. Findings from the
  two s265 specialist investigations, **each re-verified on disk by this revision
  (2026-08-31) except where marked**:
  1. **The ontology DSL has no inheritance/subtype/mixin construct at all.**
     `services/engine/ontology_schema.json`: the `property.type` enum is closed
     (`string,int,float,bool,timestamp,date,enum,json,ref,set`, `:76`), every `$def`
     sets `additionalProperties: false`, and no `extends`/`parent`/`abstract` keyword
     exists at any level (whole-file read). The only cross-object levers are `ref`
     (qualifiable `<namespace>.<Type>` per ADR-0033 D2, `:87-91`) and `link_types`
     (no `many_to_many` — deferred per ADR-008 D4, `:158-159`). **A
     superclass/subtype design is not expressible; composition-by-reference is the
     only option.**
  2. **`Person` is NOT a subtyping precedent.** Its promotion was ratified as
     **delete + re-export** (ADR-0033 Alt-4, `docs/adr/0033-shared-ontology-mechanism.md:421-422`
     — "delete + re-export pins the single-source-of-truth end state") — possible
     precisely because the per-vertical Persons had **zero vertical-specific
     fields**. `Supplier`/`Vendor` diverge on real fields — the opposite case.
  3. **ADR-0033 D6 explicitly forecloses a silent second shared type**
     (`0033-shared-ontology-mechanism.md:294-300`): "No second shared object_type is
     authored; … the decision to use it is not pre-granted." The same boundary names
     the reopening route ("re-opens under this grammar with its own concrete
     pressure") — **the deferred work must formally reopen D6, which is why it needs
     an ADR, not just a PLAN.**
  4. **External prior art converges on composition, not inheritance** (s265
     specialist finding; not derivable from this repo): schema.org's `Organization`
     deliberately has **no** `Supplier` subtype — supplier-ness is relational, via
     `seller`/`provider`; Fowler's Party/Role pattern splits stable identity from
     contextual role.
  5. **Recommended future shape (contingent on the future ADR):** `core.Counterparty`
     holding ONLY `counterparty_id` + `name` — the two fields verified identical in
     both live shapes — with each vertical keeping its own fields plus a `ref` to it:
     **HAS-A, never IS-A**. Both vertical docs would then need `imports: [core]`,
     which **no real vertical declares today** (grep across
     `verticals/*/ontology/*.yaml`: zero matches; only a synthetic in-memory test
     fixture exercises the construct).
  6. **The bill, measured:** `_ORM_COMMITTED_DEST` = `{energy, core}` and
     `_PYDANTIC_COMMITTED_DEST` = `{core}` (`services/engine/code_generator.py:900-914`),
     so a core edit changes **two committed, git-tracked files**
     (`services/db/person.py`, `services/engine/procedures/person_model.py`) **plus a
     new alembic migration** (precedent: `alembic/versions/0012_person_table.py`).
     `alembic check` runs in CI (`.github/workflows/ci.yml:118-131`) and locally via
     `tests/services/db/test_migration_orm_lockstep.py`, and reddens without one.
  7. 🔴 **The structural blocker — the single biggest reason the split is correct:**
     `_ORM_COMMITTED_DEST` routes by **namespace → one file**, and `emit_orm` takes a
     whole doc + one output path (`code_generator.py:936-938`). Core's SECOND object
     type therefore either lands inside the Person-named files, or
     `code_generator.py` must gain per-object-type routing — **a generator-mechanism
     change, not a data change** — and bundling that with this PLAN's 5-property YAML
     edit would confound two variables.
  8. **Three tooling gaps the deferred PLAN must also close:** (i) the
     `check-jsonschema` pre-commit glob is `^verticals/.*/ontology/.*\.yaml$`
     (`.pre-commit-config.yaml:55`) and **does not match `ontology/core_v0.yaml`**;
     (ii) there is **no `vero-lite generate core`** — `services/engine/cli.py:29`
     hardcodes `verticals/{vertical}/ontology/{vertical}_v0.yaml`; (iii)
     `docs/runbooks/ontology-migration-autogenerate.md:11-13` is **STALE** — it names
     energy as "the only entry in `_ORM_COMMITTED_DEST`", which
     `code_generator.py:900-903` now contradicts (core is the second entry).
  9. **Guard note:** adding a new CORE object type does **not** redden
     `test_golden_e2e.py` (it reads fleet's own donor YAML) — but **removing `Vendor`
     from fleet's YAML WOULD**: the dead-weight-exemption assert
     `_DONOR_EXTENSION_OBJECTS <= set(donor["object_types"])`
     (`tests/services/engine/scaffolder/test_golden_e2e.py:344-347`). **The future
     core work must not delete `Vendor`.**

  **Proposed `docs/STATUS.md` Active-TODO row** (Code lands this separately, verbatim
  or trimmed to the block cap — it is proposed here so the deferral has a scanned,
  tracked tripwire, not just this PLAN):

  > - [ ] **🆕 CRAY'S CALL — core `Counterparty` promotion: DEFERRED by the SD-2
  >   SPLIT (s265); needs its own ADR (formally reopening ADR-0033 D6) + PLAN.** Not
  >   rejected — split off PLAN-0117 so a generator-mechanism change never rides a
  >   5-property YAML edit. 🔴 Structural blocker: `_ORM_COMMITTED_DEST` routes
  >   namespace→ONE file and `emit_orm` takes one output path
  >   (`code_generator.py:900-914,936-938`) — a second core object type needs
  >   per-object-type routing first. Bill: 2 committed files + an alembic migration
  >   (CI `alembic check` reddens without it) + 3 tooling gaps (pre-commit glob skips
  >   `ontology/`; no `vero-lite generate core`; stale runbook
  >   `ontology-migration-autogenerate.md:11-13`). ⚠️ The future work must NOT delete
  >   fleet's `Vendor` (`test_golden_e2e.py:344`). Shape lean: `core.Counterparty` =
  >   `counterparty_id`+`name` only, HAS-A via `ref` — the DSL has NO inheritance.
  >   **Read:** PLAN-0117 § Out of Scope (deferred-core record).
- ❌ **`services/db/evidence_pack.py` / month-end export changes** — exact-match
  vendor resolution and the AC-9 KPI are untouched.

## Steps

**All SD gates are lifted — no open SDs** (Cray's typed rulings, 2026-08-31, s265;
SD-3a ruled later the same session; SD-6 ruled in the correction pass — it changes
**no step** in this PLAN, only where the later live measurement runs). Step 2
declares **both bands**: the
synonym-carrying five (SD-3) and the dormant four (SD-3a — bare + `description`, no
synonyms, no seed values). The earlier preamble text ("under every option the four
stay undeclared in this PLAN") described the pre-ruling option space and is
superseded by the ruling, which chose an outcome none of the three recorded options
named — see the SD-3a block for the lineage. All work on one `feat/*` branch; one
PR.

### Step 1 — Baseline capture + coordination check

Record on the branch: the current Vendor property list (AC-1(b)'s command at baseline
— this run is AC-1(b)'s witnessed baseline RED for the new names), the object/link
type counts (AC-6's relative baseline), and whether PLAN-0109 has landed (Coordination
§4 — if it has, re-verify F2/F7 line anchors before editing). Confirm `git status` in
the first tool batch per standing hygiene.

### Step 2 — Author the `Vendor` extension in the YAML (AC-1, AC-2)

Inside the existing `Vendor` block only (Coordination §1): declare the ruled IN-set
under ADR-008 D1's "may extend" license, mirroring the house provenance style —
every value-bearing comment states **AUTHORED / DEMO SEED, not a partner answer**,
names the future intake question that promotes it (the `minor_repair_ceiling_thb`
precedent, F2's guess-and-react discipline: a promoted fact retires its stamp, an
unanswered one keeps it), and Thai-first synonyms per property (`_property_aliases`
rationale). Per **SD-1=(c)**, one comment block inside `Vendor` records the
**PROMOTION PATH**: the measured projection (SD-1 option (b)) — aggregate
`repair_case_quote` / `repair_case_accepted_quote` / closeout rows joined on the
exact-match free-text `vendor` name (F2's rule) — as the route that retires the
AUTHORED stamps once real volume exists (today the export holds one row, F12).
Ruled declarations, band 1 (SD-3, s265): `standing` (enum
`[approved, probation, suspended]`), `is_contracted` (bool — the narrative's
อู่คู่สัญญา, F9), `repairs_completed_count` (int), `comeback_count` (int),
`avg_turnaround_days` (float). All **non-required** — a garage with no history is a
real state (F9's honesty pattern), which is also why AC-3 must exist (F8's gap).

Ruled declarations, band 2 — **the dormant four** (SD-3a, s265): `tax_id` (string),
`cert_status` (enum `[valid, expired, none]` — the donor's values, F3),
`sanctions_flag` (bool), `single_source_flag` (bool). Shape per the ruling: bare
`name` + `type` (+ enum `values` where enum), **no `synonyms` block** (AC-3a(d)'s
cost guard), no seed values, and a **rich `description`** per property — schema-legal
(`ontology_schema.json:79`), dropped at load so it costs zero prompt bytes (F13) —
explaining that the property is declared-but-unpopulated and why (the narrative may
bring some, not necessarily all, of these facts later; declaring now means the
Ask/translate LLM can use a value the day it exists — Cray's requirements (a)-(c),
read per the Correction record's SD-3a note: the procedure model sees no ontology
property either way, F17).
`single_source_flag`'s description additionally carries the residual-concern
mitigation verbatim in substance: the per-case `RepairCaseJustification` (ADR-0034
D4) is the **authoritative** sole-source record; this vendor-level flag is
**advisory, never the basis for a gate decision**, and if it is ever populated its
value must be **derived from the per-case records, never independently authored**
(AC-3a(c2)).

### Step 3 — Extend the seed (AC-3)

`vendor_records()`: DEMO SEED values labelled as such — the contracted garage carries
`is_contracted: true`, `standing: approved`, and a plausible small history; one vendor
carries `standing` but **no history facts** (the "used once, no record yet" row —
mirrors the uncoded-`accounting_code` row's stated purpose). No real vendor data is
invented (F9's public-repo rule for codes applies to history figures identically).
**The dormant four get NO seed values** — unpopulated is their contracted state
(SD-3a; AC-3a(b) asserts it), and an unpopulated question routes to the honest
no-records answer through existing machinery (F15, witnessed by AC-4's dormant case).

### Step 4 — Tests (AC-2, AC-3, AC-3a, AC-4)

Extend `test_ontology_data_contract.py` with the synonym-rendering and per-property
presence tests (generic over the ruled set where practical — F8's "guard for the NEXT
property" spirit) **plus the dormant-band test** (AC-3a: prompt-visible, unpopulated,
description contract, cost guard — the description assertions read the raw YAML, F13).
New `test_vendor_facts_scenario.py` per AC-4's fixed reads, including the dormant
no-records case (`TranslateOnlyStub` precedent:
`tests/services/engine/test_grouped_count_scenario.py`).

### Step 5 — Probe battery (every witnessed RED above)

Run the AC-1(a)/(b), AC-2, AC-3(a)/(b), AC-3a(a)/(b)/(c1)/(c2)/(d), AC-4 (both
mutations), AC-5 probes through
`tools/probe_battery/` — one claim per probe, `Claim.stable_key` addressing,
scratchpad-backed restore, coverage report captured for the PR body (CLAUDE.md §8;
module README, PLAN-0115). If a probe fails its pre-fixed criterion, repair the
instrument — never relax the criterion after seeing the result.

### Step 6 — Regenerate, gate, close (AC-5, AC-6, AC-7, AC-8)

Run fleet codegen + the AC-7 porcelain/positive-control pair; run the scaffolder suite
and the zero-diff read (AC-5); full vertical suite with the relative counts (AC-6);
the CI-scope offline gate (AC-8). Update `docs/STATUS.md` per session hygiene. PR via
branch per CLAUDE.md §7 (Code commits; Cray merges by default). After merge + Cray
closeout, `git mv` to `docs/plans/done/`.

## Surfaced decisions — RULED (Cray, typed, 2026-08-31, session 265), original recommendation texts preserved for reasoning lineage

Every SD below carries its ruling inline — **including SD-3a, ruled later in the
same session, and SD-6, ruled in the s265 correction pass; nothing remains open.**
Where a ruling's *reasoning* differs from the
original recommendation (SD-2), or the ruling *overturns* recommendations outright
(SD-3a overturns both this draft's OUT disposition for the four and Code's own
"YAML comments only" recommendation), all versions are recorded — this repo keeps
lineage; nothing is deleted.

### SD-1 — RULED (c) — the ontology↔evidence-table seam: what backs the new facts?

The hardest question in this PLAN (dispatch's own framing), not papered over. The real
transactional truth lives in hand-written evidence tables (F6); the new facts describe
vendors *across* cases. Options:

- **(a) Ontology + synthetic seed only — RECOMMENDED.** Declare the properties; values
  are DEMO SEED in `vendor_records()`; no DB, no migration (F6 makes this the
  zero-migration path). Cost, stated: the facts are **authored, not measured** — every
  comment says so (backfilled/authored values are marked, house rule), and the demo
  shows authored history until a partner answer or a projection promotes it.
- **(b) Measured projection.** Compute history from `repair_case_quote` /
  `repair_case_accepted_quote` / closeout rows at serve time, joining on the exact-match
  free-text `vendor` name (F2's rule). Cost: an aggregation seam in an adapter that is
  only now gaining DB access (0109 SD-A), honest handling of unmatched names, **and**
  near-zero real volume today — a "history" of n=1 cases is noise wearing a number.
- **(c) Declare now, name the projection as the promotion path.** (a) today, with the
  (b) design recorded in comments as the intake/measurement route.

Recommendation: **(a) with (c)'s pointer recorded**. Why Cray, not Code: this decides
whether the demo surface shows authored or measured facts — a truthfulness-of-the-demo
call under ADR-0032 D1's correction-surface discipline, and it fixes the evidence story
the later grader PLAN inherits.

**RULING (Cray, typed, 2026-08-31, s265): (c).** Declare the properties with
DEMO-SEED values now, **and** record the measured-projection route (option (b)) in
comments as the promotion path; every authored value carries its **AUTHORED**
provenance stamp (the house backfilled-value rule; enforced by AC-1(c)). This matches
the draft's "(a) with (c)'s pointer" recommendation in substance — the ruling names
(c) as the frame. **New evidence since drafting:** option (b)'s cost is now
**measured, not asserted** — the month-end export holds exactly one row
(`case-fleet-demo-history`; F12, measured by Code s265), so "a history of n=1 is
noise wearing a number" is a fact, not a forecast.

### SD-2 — RULED: SPLIT — duplicate into fleet vs promote to `ontology/` core

Procurement's `Supplier` and fleet's `Vendor` are the same *idea* at N=2 with different
shapes (a bolt supplier carries AVL/sanctions machinery; a garage carries comebacks and
turnaround). Recommendation: **fleet-side extension, no promotion** — Rule of Three
(ADR-006) says extract after 3 working verticals, and the one prior core promotion
(Person, ADR-0033) was forced by a runtime engine consumer that has no analogue here.
Alternative: promote a minimal shared `supplier-evaluation` fragment now. Why Cray:
promotion changes what every 7th vertical inherits — architecture direction, not a
drafting call.

**RULING (Cray, typed, 2026-08-31, s265): SPLIT — and the reasoning CHANGED; both
are recorded.** Sequence, kept for lineage: Cray initially ruled "promote to core";
after two specialist investigations returned (DSL expressibility; the promotion
bill), the ruling became a split:

- **This PLAN executes the fleet-side extension** — the same *action* the original
  recommendation named, **but for a different reason, and the new reason is the
  ruling's substance**. The original ground was "Rule of Three (ADR-006) says wait at
  N=2." That is **no longer the operative reason**. The operative reason: **the core
  promotion is real architecture work with its own bill** — a generator-mechanism
  change (the namespace→one-file routing blocker, Out-of-Scope finding 7), two
  committed files + an alembic migration (finding 6), three tooling gaps (finding 8),
  and a formal reopening of ADR-0033 D6 (finding 3) — **and bundling that with a
  5-property YAML edit would confound two variables** (the
  one-variable-per-change discipline).
- **The core promotion is DEFERRED, NOT REJECTED** — to its own ADR (reopening
  ADR-0033 D6 is an architecture decision, not a PLAN step) plus its own PLAN. Its
  durable, tracked record is the Out-of-Scope deferred-core block + the proposed
  STATUS Active-TODO row there — never only a closed conversation.
- The original recommendation's `Person` point survives **strengthened**: ADR-0033's
  promotion was delete+re-export of a zero-divergence type (Alt-4, `:421-422`) — not
  a subtyping precedent for the field-divergent `Supplier`/`Vendor` pair (Out-of-Scope
  finding 2).

### SD-3 — RULED (the IN-set) — the property IN/OUT set (the port filter)

Each property widens the translate vocabulary and costs prompt tokens in every call
(PLAN-0109 SD-B's pricing) — the set should be the smallest that makes the three
approver questions expressible. Menu, priced:

- **Recommended IN (5):** `standing` (the fraud narrative F5 gives it teeth — the
  small-operator register of `avl_status`); `is_contracted` (narrative-grounded:
  อู่คู่สัญญา is literally the seed's first garage, F9 — "is this the right supplier"
  is partly "is this our contracted garage"); `repairs_completed_count`,
  `comeback_count`, `avg_turnaround_days` (the delivery-history facts an approver
  actually asks).
- **Recommended OUT, with reasons recorded per Lesson 0052's rule (unmeasurable ≠
  forgotten):** `tax_id` / `cert_status` / `sanctions_flag` — corporate-compliance
  machinery the narrative's garages don't carry; dead vocabulary tokens.
  `single_source_flag` — fleet models sole-source **per case** via
  `RepairCaseJustification` (ADR-0034 D4's evidence-alternative); a vendor-level flag
  would double-state it. `on_contract`/`warranty` at quote level — 0109's block,
  Coordination §3's fence. `last_engaged_at` — derivable, hold until a consumer asks.
- **Alternative shape:** a new `VendorServiceRecord` object (one row per engagement) —
  richer, but grows `_DONOR_EXTENSION_OBJECTS` against its own tripwire and needs
  either synthetic engagement rows or SD-1(b)'s projection; priced OUT by F7 unless
  Cray wants the row-level story now.

Why Cray: this set **is** the future bar's vocabulary — it bounds what the later
grader PLAN may ever demand, and the OUT-list is a partner-facing modelling claim
about what a Thai garage is.

**RULING (Cray, typed, 2026-08-31, s265): the 5 recommended IN properties are IN** —
`standing`, `is_contracted`, `repairs_completed_count`, `comeback_count`,
`avg_turnaround_days`. ⚠️ At first ruling, **the disposition of the 4 OUT properties
was NOT ruled** — Cray asked a follow-up question about them, Code measured the
answer, and the question became sub-decision **SD-3a** below. The alternative
`VendorServiceRecord` shape is dead under the ruling (no new object types).

**Resolved later the same session — SD-3a RULED (see its block): all four are
DECLARED, bare + rich `description`, NO synonyms.** The consistent post-ruling
framing of this SD's set is therefore **two bands, one declared set**: the five
above are the **synonym-carrying, narrative-grounded band** (Thai synonyms + seed
values + AUTHORED stamps); the four are **declared-but-dormant, NOT OUT**
(prompt-visible by name, synonym-free, unpopulated). The OUT bullet above stays as
lineage: its cost reasons ("dead vocabulary tokens") were answered by the F13
measurements and overturned; its `single_source_flag` reason was a **correctness**
objection and survives as the **noted residual concern** under the SD-3a ruling.
Still genuinely OUT, untouched by SD-3a: quote-level `on_contract`/`warranty`
(0109's block) and `last_engaged_at` — see the SD-3a not-covered list.

### SD-3a — RULED (declare all four: bare + rich `description`, NO synonyms) — the 4 OUT properties: can they be kept "optional, skipped when there is no data, without costing prompt tokens"?

Cray's question, verbatim in substance. The measured answer (Code, s265; the
structural halves re-verified on disk by this revision — F13): **no such free slot
exists today.** *(The bullets below are the pre-ruling record, kept as lineage —
the RULING block after them supersedes their option framing.)*

- **Sizes (F13):** the whole fleet prompt-schema block is 1,945 B across 7 object
  types; the `Vendor` line is 339 B; the 5 IN properties add **+145 B (7.5%)**; the 4
  OUT ones would add **+107 B (5.5%)**.
- **Structure (F13, verified):** `_describe_ontology`
  (`services/engine/nl_query.py:382-398`) renders **every declared property with no
  value check**, and `PropertyMeta` (`services/engine/ontology_meta.py:268-285`)
  carries no visibility/queryable flag — **"auto-skip when unpopulated" does not
  exist today**. `ontology_schema.json`'s `additionalProperties: false` also
  forecloses parking them in a documentation-only YAML key.
- **Expressible options — all three recorded (pre-ruling; none was chosen as
  written):**
  1. **YAML comments only** — free, zero code, zero tokens, not machine-readable.
     **Code recommended (1)** *(overturned by the ruling — recorded for lineage)*.
  2. **Build a `prompt: false` property flag** — ~4 files + a guard; yields
     "declared but dormant"; saves the 107 B. Hazard, named: a property hidden from
     the prompt is one the LLM **can never query** until the flag is flipped —
     dormant means *invisible*, not *optional*.
  3. **Do not declare them** — the reasons live in this PLAN (this SD-3/SD-3a record
     is the durable home).
- **Considered and advised AGAINST (recorded so it is not re-invented):** a
  data-driven "render only if some row has a value" variant — it puts a DB read on
  every translate call (the hot path) and makes the prompt **data-dependent**, which
  breaks benchmark comparability — the very surface SD-4's ruling protects.
- **Gating (pre-ruling note, superseded):** the original text here said "under every
  option the four stay undeclared in this PLAN" — true of the three options as
  written, but the ruling chose a fourth shape none of them named, and the four now
  **do** enter this PLAN. Why Cray (unchanged): the OUT-list is a partner-facing
  modelling claim (SD-3's original ground), and mechanism-vs-comment was a spend
  call against a measured 107 B saving.

**RULING (Cray, typed, 2026-08-31, s265): DECLARE all four now — `tax_id`,
`cert_status`, `sanctions_flag`, `single_source_flag` — bare `name` + `type` (+ enum
`values` where the type is enum: `cert_status`), a rich `description` per property,
and NO `synonyms` block yet.** This **overturns two recommendations, both preserved
above for lineage**: this draft's SD-3 OUT disposition for these four, and Code's
own option-(1) "YAML comments only" recommendation.

- **What decided it — Cray's requirement, three parts that must hold at once:**
  (a) the narrative may mention these properties in future; (b) it may bring only
  SOME of them, not all four; (c) **the LLM must be able to use them effectively in
  its reasoning once a value exists.** Requirement (c) eliminates every option that
  hides the property from the prompt — both option (1) and option (2)'s
  `prompt: false` flag leave a property that HAS data but cannot be used until a
  human intervenes.
- **What makes declaring cheap (measured, F13; structural halves re-verified on disk
  by this revision):** `description` is absent from `PropertyMeta` entirely —
  dropped at load, by documented design (`nl_query.py:363-371`) — so a rich
  description costs **ZERO prompt bytes**; **`synonyms` is the expensive part**
  (~90 B for the existing `name` property's list alone, vs ~17-26 B for a bare
  name+type line); the four bare cost **+107 B on the 1,945 B block (5.5%)** —
  roughly 30 tokens per translate call.
- **Partial population needs no new mechanism (requirement (b) satisfied):** a
  declared property with no values yields an empty result, which routes to the
  existing honest-no-records path (`_no_data_nlanswer`, F15 — the "never invent"
  discipline), not a fabricated answer. Witnessed offline by AC-4's dormant case.
- **Enforcement in this PLAN:** AC-1(b) (the 12-name list), AC-3a (prompt-visible,
  unpopulated, description contract, and the **cost guard** — a `synonyms` block
  added to any of the four reddens a test), Step 2's band-2 declaration spec.

**🔴 Noted residual concern under the ruling (flagged, NOT re-ruled):** the original
OUT reason for `single_source_flag` was **not** a token argument — it is a
**correctness objection of a different kind from the cost question Cray was
answering**. Fleet models sole-source **per case** via `RepairCaseJustification`
(ADR-0034 D4's evidence-alternative), so a vendor-level flag **double-states** the
same fact at two levels, and the two copies can DISAGREE. Cray ruled all four in,
so all four go in — but this risk is recorded visibly rather than silently
absorbed. **Cheapest mitigation, adopted (free — descriptions cost zero prompt
bytes):** the flag's `description` states that the per-case
`RepairCaseJustification` is the **authoritative** record, that the vendor-level
flag is **advisory — never the basis for a gate decision** — and that if it is ever
populated, its value must be **derived from the per-case records, never
independently authored** (removing the second author removes the disagreement
channel by construction). Enforced textually by AC-3a(c2). **Honest adequacy
judgment:** *sufficient while dormant* — AC-3a(b) keeps the flag unpopulated in
this PLAN, and an unpopulated flag cannot disagree with anything; **not sufficient
on its own once populated** — the description is invisible to the LLM at translate
time (dropped at load, F13) and no guard executes a prose authoring rule, so the
change that first populates this flag MUST bring a machine check (flag ⇔ per-case
justification consistency) or the disagreement channel reopens. That future check
is flagged here for whichever PLAN first authors a value; it is not built now.

**What this ruling does NOT cover (nothing silently swept in — Cray named exactly
four properties, all vendor-level):** quote-level `warranty` / `on_contract` stay
OUT — they are PLAN-0109's block, a **partition boundary** (Coordination §3), not a
cost call; `last_engaged_at` stays OUT — derivable, hold until a consumer asks
(the original reason, untouched). See the Out-of-Scope not-swept-in bullet.

**⚠️ Asserted-not-verified, UNMEASURED (F16):** the answer-quality effect of the
wider translate vocabulary — a model may attempt queries that return empty more
often. Measuring it needs a live MS-S1 run under a typed CLAUDE.md §8 go. The
original recommendation here (fold it into the later grader PLAN's MS-S1 round) is
**superseded by the SD-6 ruling**, kept as lineage: it now rides the ruled route-(a)
run on `benchmarks/nl_query_feasibility/` — the surface where a translate-vocabulary
effect is actually observable.

### SD-4 — RULED (a) — `procedures.yaml` goal text: pre-thread now, or move with the grader?

RESULTS §13 is explicit that answerability needs the ontology **and the goal** (F1);
`role_vocabulary` reads only the goal (F1). Options: **(a) leave the goal untouched in
this PLAN — RECOMMENDED** — the goal edit and the grader edit are one supply-and-demand
pair and should land in one reviewable diff (the same pair-landing spirit as 0109's
declare+guard REJECT-IF), and the current "applied DOWNSTREAM … never withhold on quote
counts" sentence (F4) must be *rewritten against*, which deserves its own PLAN's
attention; **(b)** pre-thread supplier vocabulary now so the later PLAN is grader-only.
Why Cray: the goal is a ratified prompt surface (its trigger ruling was typed, s243)
and the benchmark's measurement surface — editing it re-baselines every banked number.

**RULING (Cray, typed, 2026-08-31, s265): (a).** The goal text stays untouched in
this PLAN; the goal edit pairs with the grader edit in the later PLAN, and **the
re-baseline happens once, there.** As recommended.

### SD-5 — RULED (a) — sequencing vs PLAN-0109

**(a) No forced order — RECOMMENDED** (Coordination §1-§4: disjoint regions, disjoint
guard surfaces, second-lander rebases); **(b)** strict 0109-first (simplest mental
model; 0109 is fully ruled and unblocked anyway). Why Cray: two Draft PLANs claiming
one file is a routing/priority call between sessions, exactly the class Tier-3 owns.

**RULING (Cray, typed, 2026-08-31, s265): (a).** No forced order; disjoint regions;
the second-lander rebases (Coordination §4). As recommended. Additionally, verified
on disk by this revision: **PLAN-0111 touches neither the fleet YAML nor
`ontology/`** (F14, zero grep matches) — the earlier "asserted-not-verified" residual
note about 0111 is **CLOSED**, and 0111 needs no coordination contract
(Coordination §5).

### SD-6 — RULED (a) — where is the ontology's effect on the two MS-S1 models measured?

Arose in the s265 correction pass, not in the original draft: the pre-correction
framing implied the ontology's effect could be read off `procedure_baseline`'s
rationale lane, and F17's measurement showed the ontology is not on that prompt path
— a run there would measure a channel that does not exist. Options:

- **(a) The NL / Ask surface — `benchmarks/nl_query_feasibility/`** (harness,
  `gold.yaml`, `run_benchmark.py` verified on disk by this revision). On this route
  the declared facts genuinely reach the model: `_describe_ontology` feeds the
  translate prompt (F13) and the seed serves the values (AC-3/AC-4).
- **(b) `procedure_baseline`.** Only meaningful after the unscoped event/goal
  carrier exists (Out of Scope, F17) and the SD-4 goal edit lands — before that, any
  delta measured there is noise attributed to a channel that is not connected.

Why Cray: this fixes which banked benchmark lane the ontology work is accountable
to — a measurement-surface ruling of exactly the kind SD-4 protected.

**RULING (Cray, typed, 2026-08-31, s265): (a).** The ontology's effect on the two
MS-S1 models is measured on the NL / Ask surface, route (a) — **because there the
facts genuinely reach the model, so the experiment measures the ontology rather
than measuring a channel that does not exist.** The procedure-side question is
**deferred until the carrier is scoped** — deferred, not ruled. Consequences
recorded: F16's vocabulary-width measurement rides this route-(a) run (the earlier
fold-into-grader-PLAN recommendation is superseded, kept as lineage in F16 and the
SD-3a block); any live run still requires its own typed CLAUDE.md §8 go; nothing in
this PLAN's offline ACs moves.

## Verification

1. **Declared and addressable:** AC-1's exact 12-name property list (both bands)
   after its witnessed baseline RED; schema hook green with its own red probe; Thai
   synonyms rendered for the five (AC-2) with the synonyms-only mutation; the
   SD-1(c) comment contract — ≥ 5 AUTHORED stamps + exactly one PROMOTION PATH
   block — present with its two removal probes (AC-1(c1)/(c2)).
2. **Answerable, not just advertised:** every synonym-carrying property has a valued
   seed row (AC-3, closing F8's named gap), and a supplier-evaluation question
   round-trips grounded through the real translate→execute→phrase chain offline
   (AC-4), count moving with the seed.
3. **The dormant band held to its contract (SD-3a):** the four prompt-visible,
   synonym-free (the cost-guard probe: an added `synonyms` block reddens),
   unpopulated in the seed, each carrying its `description` — with the
   `RepairCaseJustification`-authoritative sentence on `single_source_flag`
   (AC-3a's five probes); a dormant-property question terminates in the honest
   no-records answer, reddening when a value is authored (AC-4's dormant case).
4. **The promised non-events, witnessed:** golden oracle green with a zero exemption
   diff and a live scratch-object red probe (AC-5); vertical counts unchanged relative
   to baseline (AC-6); zero committed codegen drift with the positive control proving
   the regen ran (AC-7).
5. **Gate:** CI-scope ruff/mypy/pytest green (AC-8); all probes through
   `tools/probe_battery/` with the coverage report in the PR body.
