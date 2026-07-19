# PLAN-0083: Procurement adapter canonical source mapping (ontology↔CSV drift fix, option c1)

**Status:** Accepted — ready to execute (fix-option c1 + SD-1..SD-4 Cray-ratified 2026-07-19)
**Owner:** Claude Code (executor) — drafted by `plan-drafter` (see Authorship disclosure below)
**Created:** 2026-07-19
**Related ADRs:** ADR-016 (mapping layer absorbs source diversity — the design anchor), ADR-007 (DataAdapter contract), ADR-0023 (zero-`services/`-core-edit discipline)

---

## Context — the drift, verified

The procurement ontology **deliberately canonicalized** raw Fastenal source names to
OCT vocabulary: `verticals/procurement/ontology/procurement_v0.yaml:25` — "Base (OCT)
object_types — mirror aquaculture, Asset→Equipment, Site→Plant" (also the header
comment `:7-11`). So the ontology declares CANONICAL names: `Equipment` pk
`equipment_id` (`:27-28`), `Plant` pk `plant_id` (`:52-53`),
`OperationalEvent.equipment_id`/`site_id` (`:93-98`), `Part` pk `part_no`
(`:171-172`), `Quotation.part_no`/`price`/`lead_time` (`:234-249`),
`PurchaseOrder.part_no`/`amount` (`:263-276`), `ApprovalTier.max_amount` (`:322-324`).

But the hero CSVs + the `FastenalCsvAdapter` serve **raw Fastenal names verbatim**:

- `verticals/procurement/data_adapter/fastenal_csv.py:19-23` — "keyed by the CSV
  column names verbatim — zero field translation"; `_OBJECT_FILES` (`:77-98`) maps
  `object_type → (filename, {column: coercion})` where coercions change TYPE only,
  never NAME, and the object_type keys are the RAW names (`"Asset"` → `asset.csv`,
  not `"Equipment"`); `_read_rows` (`:121-133`) copies raw column names through.
- The engine's load gates validate **declared** ontology property names
  (`services/engine/procedures/orchestrator.py:372-414` threshold_field gate,
  `:490-516` `_validate_join_collisions`) while the generic query executor merges
  **runtime** CSV keys (`services/engine/procedures/query_step.py:583-603` `_merge`) —
  so a declared foreign key like `part_no` is absent from rows carrying `part_id`.

The drift is **real but latent** — no run breaks today because the hero production
path hand-reads raw keys and sidesteps the generic join:

- `verticals/procurement/hero_demo/run.py:188-201` `_normalize_quotes` does an ad-hoc
  `price_thb → unit_price` rename; `:204-248` `_intake_seed` reads
  `q["part_id"]`/`req["part_id"]` (`:220`, `:231`) and `req["asset_id"]` (`:230`).
  The production `intake` executor `_SeedQuery` (`:134-169`) is a hand-seed, not a
  grammar join.
- `tests/verticals/procurement/test_intake_shadow_parity.py:86-101` proves the join
  half grammar-expressible only via explicit `on: {left: part_id, right: part_id}`
  (`:91`) plus a declared `"part_no": "quote_part_no"` rename that is a **no-op at
  runtime** (`:83-85` — "`part_no` never appears at runtime (ontology drift)"); the
  test's own header documents the drift (`:27-31`).
- The synthetic adapter already emits canonical names — `part_no`
  (`verticals/procurement/data_adapter/synthetic.py:186` ff.), `equipment_id`/`site_id`
  (`:87-176`), `fits_equipment_id` (`:193-216`), type key `"Equipment"` (`:430`) — and
  the calm path rides it (`tests/verticals/procurement/test_calm_path_production_runnability.py:67`,
  `:98` key on `part_no`). **The synthetic path needs no change** (verified).
- PLAN-0062 pinned this drift and left it as an explicit follow-up:
  `docs/plans/done/0062-per-vertical-seed-migration.md:520-526` and `:540-542`.

**Motivating contract gap:** the `DataAdapter` protocol advertises "the engine maps
the returned raw dicts to typed entities via the generated ontology models"
(`services/engine/data_adapter.py:28-30`, `:42`) — but the hero path reads raw keys
directly, so the advertised contract is not applied. (c1) makes reality match the
advertised contract.

## Locked decision — fix option (c1) 🔒

**LOCKED (Cray-ratified via AskUserQuestion, session of 2026-07-19):** the
`FastenalCsvAdapter` — the per-vertical source-diversity-absorbing layer — translates
raw CSV column names → canonical ontology property names (and raw type names →
canonical, per SD-1), so **all downstream consumers see one canonical vocabulary: the
ontology's**.

- **Design anchor:** ADR-016 locks this placement —
  `docs/adr/0016-governed-procedure-engine.md:492-495` "bind query steps to ontology
  objects (the mapping layer absorbs source diversity); this is **not**
  connectors-in-the-procedure", and `:647-648` "**OUT:** connectors-in-the-procedure
  (LOCKED — the mapping layer absorbs source diversity, Cray s84)". The adapter IS
  that absorbing layer, so the translation belongs there.
- The ontology stays CANONICAL: **no `procurement_v0.yaml` edit, no generated-artifact
  regen.**

### Considered & rejected

- **(a) Rename the ontology to match the CSVs** — undoes the deliberate
  mirror-aquaculture canonicalization (`procurement_v0.yaml:7-11`, `:25`) AND
  relocates the drift onto the synthetic path (the calm-path test keys on `part_no`
  today — `test_calm_path_production_runnability.py:67`, `:98` — it would break).
- **(b) Grammar alias via `project.fields`** — scatters CSV-column knowledge into
  procedure YAML, i.e. the "connectors-in-the-procedure" form ADR-016 marks OUT
  (`0016:647-648`), and only helps the grammar path (the hero hand-reads stay raw).
- **(c2) A real dbt/SQLMesh mapping layer** — the Phase-2 funded deliverable; too big
  for now (recorded in Out of Scope).

## Drift inventory (enumerated from the CSV headers vs the ontology declaration)

Every hero CSV header was read and diffed against `procurement_v0.yaml`. Columns fall
into three classes: **RENAME** (a declared canonical property exists for the same
datum), **KEEP** (demo-extra — no declared counterpart; stays raw), and
**ABSENT** (declared property the CSV does not carry — all such are
ontology-optional; no required property is missing after rename).

| Adapter type (raw) | CSV (`verticals/procurement/data/hero/`) | RENAME raw → canonical | KEEP (demo-extra) | ABSENT (declared, optional) |
|---|---|---|---|---|
| `Asset` → SD-1 | `asset.csv:1` | `asset_id→equipment_id`, `asset_type→equipment_type`, `site→site_id` | `line_code`, `downtime_cost_per_hour_thb` | — |
| `Part` | `part.csv:1` | `part_id→part_no` | `category`, `unit`, `on_contract_unit_price_thb`, `emergency_expedite_unit_price_thb`, `criticality` | `on_contract`, `preferred_supplier`, `stock_qty`, `reorder_point`, `lead_time`, `fits_equipment_id` |
| `Supplier` | `supplier.csv:1` | *(none — no name drift)* | `region`, `on_contract` | `tax_id`, `cert_status`, `sanctions_flag`, `single_source_flag` |
| `PurchaseOrder` | `purchase_order.csv:1` | `part_id→part_no`; `asset_id→equipment_id` (SD-4a) | `qty`, `unit_price_thb`, `total_thb` (SD-4b), `order_type`, `is_off_avl_override`, `required_tier_id`, `requester_role`, `approver_role` | `quote_id`, `currency`, `approver_chain`, `waiver_applied`, `justification` |
| `ApprovalTier` | `approval_tier.csv:1` | *(SD-4b: `max_thb→max_amount` deferred)* | `tier_name`, `min_thb`, `max_thb`, `sod_required` | `tier` (int ordinal — `tier_name` is a different datum, NOT a rename) |
| `Person` | `person.csv:1` | *(none — `person_id`/`name`/`roles` already match the cross-vertical principal vocabulary; not declared in `procurement_v0.yaml` — shared/promoted, PLAN-0082)* | — | — |
| `OperationalEvent` | `operational_event.csv:1` | `asset_id→equipment_id`, `site→site_id` | — | — (all 7 other columns match declared exactly) |
| `Quotation` | `quotation.csv:1` | `part_id→part_no`, `price_thb→price`, `lead_time_days→lead_time` | — | — (all 5 other columns match declared exactly) |

**Core rename set (unambiguous — a declared property is evidently the same datum):**
`asset_id→equipment_id`, `asset_type→equipment_type`, `site→site_id` (Asset rows);
`part_id→part_no` (Part, PurchaseOrder, Quotation rows); `price_thb→price`,
`lead_time_days→lead_time` (Quotation rows); `asset_id→equipment_id`,
`site→site_id` (OperationalEvent rows). Edge rows are SD-4.

**Adjacent drift axes observed (recorded, deferred — see Out of Scope):**
(i) **link-type-name drift** — the adapter serves `asset_uses_part`,
`part_suppliable_by_supplier`, `po_references_part`, `po_sourced_from_supplier`,
`po_for_asset`, `po_requires_tier` (`fastenal_csv.py:101-118`); NONE matches a
declared `link_types` name (`quotation_for_part`, `po_for_part`, … —
`procurement_v0.yaml:329-414`). (ii) **enum value-domain drift** — e.g. `CNC_MILL`
vs `cnc_machine`, `DOWN` vs `failed` (`asset.csv:2` vs `procurement_v0.yaml:38-46`),
`ON_AVL` vs `approved` (`supplier.csv:2` vs `:213-214`). (iii) **link prop names**
(`quoted_unit_price_thb`, `lead_time_days` — link_types declare no properties, no
canonical counterpart exists). All three are out of this PLAN's scope; column names
only (the locked c1 scope).

## Goal

Make the `FastenalCsvAdapter` emit **canonical ontology property names** for every
drifted column (per the ratified rename map above), flip the downstream hand-reads to
the canonical names, and land a **coverage tripwire** so a future column cannot
silently re-drift — with zero ontology YAML edit, zero generated-artifact change,
zero `services/` engine code edit, and all existing behavior (verdicts, gate
outcomes, ฿ figures) preserved. After this PLAN, the advertised `DataAdapter`
contract ("raw dicts → ontology vocabulary at the adapter seam") is true for
procurement, and the declared-vs-runtime seam (`orchestrator.py:372-414`/`:490-516`
vs `query_step.py:583-603`) closes for this vertical.

## Acceptance Criteria

- [ ] **AC-1 Canonical emission:** `fetch_objects` returns rows keyed by canonical
  ontology property names for every core-set drifted column — a test asserts, per
  served type, the exact emitted key set (set-equality pin) and that no raw
  denylisted name (`part_id`, `price_thb`, `asset_id`, `site`, `asset_type`,
  `lead_time_days`) appears in emitted object rows.
- [ ] **AC-2 Tripwire, non-vacuous:** the full drift set is covered by a coverage
  tripwire test that asserts (i) per-type emitted-key set-equality against pinned
  canonical sets, (ii) every declared **required** property of each served
  procurement type is present in its emitted rows (`Equipment`: `equipment_id`,
  `name`, `site_id`; `Part`: `part_no`, `name`; `Quotation`: `quote_id`, `part_no`,
  `supplier_id`; `PurchaseOrder`: `po_id`, `part_no`, `supplier_id`;
  `OperationalEvent`: `event_id`, `occurred_at`; `Supplier`: `supplier_id`, `name`;
  `ApprovalTier`: `tier_id`), and (iii) every rename target is a declared property of
  its canonical type (ontology-anchored — a typo'd target fails). Non-vacuity is
  proven by a probe: a permanent test case feeding a doctored raw-keyed row set
  through the check and asserting it goes RED, plus a one-shot build-time probe
  (temporarily drop one rename map entry → tripwire RED → revert).
- [ ] **AC-3 Behavior preserved:** the procurement hero run still reaches its
  `doa_tier`/SoD approval gate (`waiting_human`; `verticals/procurement/procedures.yaml:301`,
  `:318`); `test_hero_run.py`, `test_calm_path_production_runnability.py`,
  `test_hero_ledger.py`, `test_transform_migration_parity.py`,
  `test_hero_governance_audit.py`, and the box-4 economic-impact suites
  (`tests/services/engine/test_economic_impact*.py`, `tests/api/test_demo_hero_routes.py`)
  pass **byte-unchanged** with verdicts/฿ figures unchanged. Only the two
  adapter-facing tests (`test_fastenal_csv_adapter.py`,
  `test_intake_shadow_parity.py`) receive **mechanical** key-name updates with all
  expected values unchanged.
- [ ] **AC-4 Full gates:** full offline suite green, re-run on the merge commit
  (CI is PR-only — the merge commit is never tested otherwise); `mypy` clean under
  the repo's strict config (`pyproject.toml:82-84`); `ruff` clean.
- [ ] **AC-5 Invariant:** NO `verticals/procurement/ontology/` edit, NO
  generated-artifact change, NO `services/` code edit — the diff is adapter +
  vertical (`verticals/procurement/`) + tests only (rides under ADR-016,
  adapter-scoped).
- [ ] **AC-6 SD resolutions recorded:** SD-1…SD-4 resolutions are recorded in the
  Surfaced Decisions section above (Cray-ratified 2026-07-19, stamped per SD); this
  box ticks at closeout once execution confirms the build matches the stamped
  resolutions.

## Out of Scope

- ❌ **(c2)** the real dbt/SQLMesh mapping layer — the Phase-2 funded deliverable.
- ❌ **(a)** any ontology YAML rename; **(b)** grammar-level aliasing via
  `project.fields`.
- ❌ Enum **value-domain** canonicalization (`DOWN`→`failed`, `ON_AVL`→`approved`, …)
  — observed above, recorded as a deferred follow-up; renaming values is a behavior
  change this PLAN's AC-3 forbids.
- ❌ **Link-type-name** reconciliation (`po_references_part` vs declared
  `po_for_part`, …) and link **prop** names — recorded follow-up (same seam, separate
  change; no declared-link consumer exists today).
- ❌ The O-2 nest residue / generic-query-router migration of the hero `intake`
  (blocked at N=1, separate track — `run.py:147-161`).
- ❌ Other verticals' adapters (procurement only — Rule of Three: generalize the
  adapter-translation pattern only after a 2nd vertical needs it).
- ❌ Renaming the **seed dict** output keys (`_intake_seed`'s emitted `"part_id"`/
  `"asset_id"`, `run.py:230-231`) or the **ledger** output keys (`ledger.py:72-73`)
  — those are those artifacts' own downstream contracts (audit/parity/render), not
  adapter rows; keeping them is what makes AC-3's byte-unchanged test set possible.

## Steps

### Step 1: Pin the rename map in the adapter (SD-2 shape)

Add a per-object-type column-rename structure to
`verticals/procurement/data_adapter/fastenal_csv.py` carrying the ratified core set
(+ SD-4a if ratified), applied at the `fetch_objects` seam only. Recommended shape
(SD-2): a parallel module-level `_COLUMN_RENAMES: dict[str, dict[str, str]]` keyed
like `_OBJECT_FILES`, applied after coercion (coercion keys stay raw — they key the
CSV) inside `fetch_objects`/`_read_rows` via an optional parameter. **Link reads stay
raw internally**: `_explicit_links` (`:184-198`) and `_po_inline_links` (`:200-205`)
address CSV columns positionally (`from_col`/`to_col`, `row["part_id"]` etc.) and
emit only `from_id`/`to_id`/props — untouched. `health_check` semantics unchanged.
If SD-1(i) is ratified, rename the `_OBJECT_FILES`/`_COLUMN_RENAMES` keys
`"Asset"`→`"Equipment"` in the same step.

### Step 2: Flip the downstream hand-reads to canonical names

- `verticals/procurement/hero_demo/run.py` — `_normalize_quotes` `:195`
  (`q["price_thb"]`→`q["price"]`), `:197` (`q["lead_time_days"]`→`q["lead_time"]`;
  the emitted `"lead_time_days"` **key** of the normalized quote shape stays — it is
  the `scored_rule` candidate shape, not an adapter row); `_intake_seed` `:220`
  (`part_id`→`part_no`, both sides of the filter), `:230-231` (read
  `req["equipment_id"]`/`req["part_no"]`; the seed's emitted keys stay per Out of
  Scope). `:408`/`:410`/`:574`/`:576` read the seed dict, not adapter rows — no change.
- `verticals/procurement/hero_demo/ledger.py` — `:48` (`hero_po["part_no"]`), `:53`
  (`hero_po["equipment_id"]`; plus `fetch_objects("Equipment")` + the row key
  `"equipment_id"` if SD-1(i)). `:51` `total_thb`, `:56-62` link props, and the output
  keys `:72-73` stay (SD-4b defer + Out of Scope).
- `verticals/procurement/hero_demo/governance_audit.py:79-80` (`min_thb`) and
  `verticals/procurement/economic_impact.py:40-43` (provenance label strings) —
  **untouched** under the SD-4b defer recommendation; if SD-1(i) is ratified the
  provenance labels still stay (they cite the raw *source dataset* column — that is
  what provenance is for; record this choice in the code comment).

### Step 3: Mechanical updates to the two adapter-facing tests (SD-3)

- `tests/verticals/procurement/test_fastenal_csv_adapter.py` — canonical key asserts
  (`:98` `part_id`→`part_no`; `:70`/`:93` type key if SD-1(i); `:104-105`/`:137-138`
  `min_thb`/`max_thb` asserts stay under SD-4b defer). Values unchanged.
- `tests/verticals/procurement/test_intake_shadow_parity.py` — the join spec `:91`
  **must** become `on: {left: part_no, right: part_no}` (the raw key no longer exists
  at runtime — this is required, not optional); `_BASE_FIELD_MAP` `:106-116` updates
  its grammar-row keys (`part_no`, `equipment_id`) while the seed-side keys stay. The
  four declared `project.fields` renames (`:94-99`) are kept: the previously no-op
  `"part_no": "quote_part_no"` rename becomes genuinely load-bearing (the join-key
  pair is gate-exempt per `orchestrator.py:506-507` and value-neutral at merge per
  `query_step.py:591-592`, but the projection preserves each quote's own `part_no`
  labeling exactly as before). Update the header comment `:27-31`/`:83-85` — the
  documented drift is now fixed; the parity semantics are unchanged.

### Step 4: The coverage tripwire (new test module)

New `tests/verticals/procurement/test_fastenal_adapter_canonical_coverage.py`
implementing AC-2's three assertions against the live adapter + the procurement
`OntologyMeta`, plus the permanent doctored-fixture probe proving the check RED on a
raw-keyed row. The check helper lives in the test module (a new doc under
`docs/plans/` would trip G2; a test module is the right home — cf. the
tracking-guard convention). `Person` is excluded from the ontology-anchored
assertions (not declared in `procurement_v0.yaml`; shared per PLAN-0082) but included
in the set-equality pins.

### Step 5: Verification sweep + invariant check

Run the pre-committed verification below; confirm the diff-scope invariant (AC-5)
with `git diff --stat` before the PR; re-run the full suite on the merge commit.

## Surfaced Decisions (Cray-ratified 2026-07-19 — see the RATIFIED stamp on each SD)

- **SD-1 — TYPE-name reconciliation (`Asset`→`Equipment`; `Site`→`Plant`).**
  **RATIFIED (Cray, 2026-07-19): (i)** rename the adapter type key
  `Asset`→`Equipment` now.
  Evidence: `fetch_objects("Asset")` has exactly **three** procurement call sites —
  `hero_demo/ledger.py:53`, `test_fastenal_csv_adapter.py:70`, `:93` (repo-wide grep;
  the energy hits are that vertical's own synthetic adapter). There is **no
  `Site`/`Plant` half to reconcile**: the adapter serves no site/plant file at all
  (`_OBJECT_FILES:77-98`), and `operational_event.csv`/`asset.csv` carry `site` only
  as a column (→ `site_id` in the core set). **Recommendation: (i) rename the
  adapter's type keys `Asset`→`Equipment` now** — three verified call sites + the
  `health_check` counts key; it completes the canonical vocabulary in one move, and
  deferring it would leave the tripwire asserting canonical *columns* under a raw
  *type* key (an odd half-state). The `economic_impact.py:40-43` provenance strings
  stay raw either way (source-citation semantics — see Step 2), keeping the box-4
  suites byte-unchanged. Why Cray: type-key rename is demo-visible vocabulary
  (`health_check` object_counts, any operator-facing surface that echoes type names)
  — a positioning-adjacent call, not a pure code judgment.
- **SD-2 — translation-map shape.**
  **RATIFIED (Cray, 2026-07-19): (b)** parallel `_COLUMN_RENAMES` dict applied on
  the `fetch_objects` path only.
  Options: (a) extend each `_OBJECT_FILES` tuple to
  a 3-tuple, (b) a parallel `_COLUMN_RENAMES` dict, (c) rename inside `_read_rows`
  unconditionally. **Recommendation: (b)** — lowest blast radius: `_OBJECT_FILES`
  tuple shape and every existing site stay untouched; coercion keys stay raw
  (they address the CSV); the link paths (which call `_read_rows` with raw
  `from_col`/`to_col`) are structurally unaffected because the rename applies only on
  the `fetch_objects` path. (c) would silently break `_explicit_links`/`_po_inline_links`
  column addressing; (a) churns every `_OBJECT_FILES` consumer including
  `health_check`. Why Cray: pure implementation shape — flagged only because the
  dispatch asked; a one-word ratification suffices.
- **SD-3 — shadow-parity overrides.**
  **RATIFIED (Cray, 2026-07-19):** keep the shadow-parity shape, mechanical rename
  only (`on:{left:part_no}`).
  The `on: {left: part_id}` update is **forced**
  (Step 3 — the raw key ceases to exist), so the real question is whether to also
  restructure (e.g. drop the now-load-bearing `part_no` projection rename or switch
  to a declared `link:` join). **Recommendation: keep the shape, mechanically rename
  only.** A `link:` join is unavailable anyway (the PO↔Quotation declared link
  `po_from_quotation` rides `quote_id`, which the PO CSV does not carry —
  PLAN-0062's "fact 5", `test_intake_shadow_parity.py:82`), and dropping the
  projection rename would change the merged-row shape (behavior). Why Cray: the
  parity test is the recorded evidence for the O-2 migration track — its shape is a
  governance artifact, not just a test.
- **SD-4 — edge rows of the rename map.** (a) `PurchaseOrder.asset_id→equipment_id`:
  **RATIFIED (Cray, 2026-07-19):** rename `PurchaseOrder.asset_id`→`equipment_id`.
  Rationale: the ontology declares **no** PO→Equipment property at all, but `equipment_id` is
  the canonical Equipment-ref vocabulary everywhere else
  (`procurement_v0.yaml:93-95`, `:146-148`, `:197-199`). **Recommend: rename** —
  consumers are `run.py:230` + `ledger.py:53` only (verified); one vocabulary is the
  point of c1. (b) `total_thb→amount` (declared, `:274-276`) and
  `max_thb→max_amount` (declared, `:322-324`) + the symmetric ontology-undeclared
  `min_thb→min_amount`: **RATIFIED (Cray, 2026-07-19): DEFER** the ฿-columns
  (`total_thb`/`max_thb`/`min_thb`) — keep raw, pinned deliberately in the tripwire
  with a comment citing this SD. Rationale (**recommend: DEFER (keep raw)**) — the governed amount is
  **re-derived** by the run, never read from the PO (`run.py:205-208`), so these
  columns feed only the ฿-ledger/box-4/DoaTier-construction surfaces
  (`ledger.py:51`, `economic_impact.py:40-43`, `governance_audit.py:79-80`,
  `test_fastenal_csv_adapter.py:104-138`); renaming buys no generic-join value and
  churns the box-4 provenance surface, breaking AC-3's byte-unchanged set. Record
  the defer in the tripwire pins (raw names pinned deliberately, with a comment
  citing this SD). Why Cray: (a) writes an ontology-undeclared canonical name into
  emitted rows (a small vocabulary-extension call); (b) trades canonical purity
  against demo-surface churn — a value judgment.

## Verification (pre-committed pass/fail — fixed before the run)

Deterministic-offline; **MS-S1 not involved** (CLAUDE.md §8 — the offline oracle is
the gate). One pytest per checkout; DB tests use the per-checkout disposable test DB
(`tests/db_support`; dev Postgres = Docker Desktop, compose default host port 5432 —
`docker-compose.yml:10`; local `.env` may override).

| # | Check | PASS iff |
|---|---|---|
| V1 | `pytest tests/verticals/procurement/` | all green; `test_hero_run.py` / calm-path / ledger / transform-parity / governance-audit **byte-unchanged** |
| V2 | Hero gate | the hero run result still parks `waiting_human` at the `doa_tier`/SoD gate (existing `test_hero_run.py` assertions, unmodified) |
| V3 | Tripwire | new coverage test green; permanent doctored-fixture probe case green (i.e. it asserts RED-on-raw); one-shot probe: drop one rename entry → tripwire FAILS → revert |
| V4 | Box-4 / API | `pytest tests/services/engine/test_economic_impact*.py tests/api/test_demo_hero_routes.py` green, byte-unchanged |
| V5 | Diff scope | `git diff --stat` touches only `verticals/procurement/**` (excluding `ontology/`) + `tests/verticals/procurement/**`; zero `services/` code, zero YAML, zero generated artifacts |
| V6 | Full gates | full offline suite green **re-run on the merge commit**; `mypy` strict clean (`pyproject.toml:82-84` scope); `ruff` clean |

Any V-row failing = the PLAN step is not done; no narrowing of a check to make it
pass (a failed check is refuted, not reworded).

---

## Authorship disclosure (ADR-012 D4.3)

Drafted by the in-harness `plan-drafter` subagent (ADR-013 D1 phased authority) from
a Code-tab dispatch; every `file:line` fact above was independently re-verified
against the working tree on 2026-07-19 (drift set enumerated from the CSV headers,
not inherited). Independent reviewer: Code (R2) + Cray at PR merge.
Author≠reviewer separation: **INTACT**. Fix option (c1) is LOCKED and SD-1…SD-4
are Cray-ratified (2026-07-19), stamped per SD above.
