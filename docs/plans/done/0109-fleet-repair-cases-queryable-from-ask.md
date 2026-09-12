# PLAN-0109: Fleet repair-case data queryable from Tab C (Ask) — declare, serve, and guard the lockstep

**Status:** Complete (2026-09-12, session 296 — see §Closeout). **13 of 14 ACs ticked.** AC-14 is deliberately UNTICKED: it is a host-state live smoke and no typed Cray go for it exists (CLAUDE.md §8). Every ticked AC was re-measured against `main` `c519466` in s296 — the ticks rest on that run, not on the s294 PR bodies.
**Owner:** both — Claude Code executes; SD-A / SD-B / SD-D are RULED (Cray, typed 2026-08-18, session 237); SD-C is Code-adopted, open to countermand; SD-E needs no ruling. **Execution is unblocked — no step waits on a ruling.**
**Created:** 2026-08-18
**Batteries:** `tests/batteries/plan-0109-*.json` — the three committed probe-battery definitions whose reports this PLAN's acceptance criteria cite. Figures are the s296 re-run, not the authoring run. `plan-0109-phase1-declare-and-guard.json` (**34 claims, 34 witnessed, 0 exemptions**, `GAPS: 0`) carries AC-3/AC-4's live-tree witnesses; `plan-0109-phase2-serve.json` (**42 claims, 38 witnessed, 4 exemptions**, `GAPS: 0`) carries AC-6…AC-10's; `plan-0109-ac5-golden-exemption.json` (**38 claims, 2 witnessed, 36 exemptions**, `GAPS: 0`, added s296) carries AC-5's two — the set-equality at `tests/services/engine/scaffolder/test_golden_e2e.py:398` and the missing-object tripwire at `:394`. ⚠️ That last ratio is stated here rather than left behind the word COMPLETE: the 36 exemptions are the scaffolder's own pre-existing grammar claims, which this PLAN neither authored nor modified, and an exemption is not a witness. A coverage report is not reviewable without its definition.
**Related ADRs:** ADR-007 (DataAdapter contract — deliberately untouched, see SD-A), ADR-008 (ontology schema + D1 "may extend" license), ADR-0032 (D1 demo→pilot wedge — the customer rationale), ADR-0035 (D6 prompt-log retention — bears on SD-D)

> **Drafting provenance (ADR-012 D4.3).** Authored by the in-harness `plan-drafter`
> subagent from a Code-tab dispatch (session 237 fact-pack, ratified direction typed by
> Cray 2026-08-18). Independent review: Cray at PR merge. Code commits via PR
> (CLAUDE.md §7); the drafter does not commit.
> **Rulings folded in same day (2026-08-18, relayed via Code):** SD-A = (b), SD-B = the
> demo-play spine, SD-D = a ruled IN/OUT set that **differs from the drafter's
> recommendation** (more free text IN; the ROPA amendment is now a mandatory AC — see
> the SD-D block). SD-C carries no typed ruling — Code adopted the recommended
> mechanism, open to countermand. Code re-verified F11/F12/F13, the SD-E anchors and
> the retention-docstring anchor on disk before the fold: all held.

> **Errata — session 294 (Cray, typed: fix the four defects before Step 1).** Four defects
> in RULED content, each `was an error` in the draft as written and each re-measured on disk
> at `main` `816a478` before the edit (STATUS Active TODOs, the PLAN-0109 row; (i)–(iii)
> first measured s241, (iv) s260). **The rulings are untouched** — SD-A (b), the SD-B type
> set and the SD-D IN/OUT set stand; what changed is the drafter's factual scaffolding.
> **(i)** AC-11 prescribed deleting a TRUE sentence and writing a FALSE one. Measured: projected
> row values reach the **phrase** request only (`services/engine/nl_query.py:1208-1235`,
> `facts_json`, capped at `_PHRASE_FACT_CAP`, and only when the LLM arm phrases); the
> translate request carries the ontology description + the question (`_describe_ontology`
> `:395`, `_translate_messages` `:414`) — never row values; and the ADR-0035 D6 prompt log
> stores the closed field set `{ts_utc, route, vertical, text=the QUESTION, model, outcome,
> arm}` (`services/engine/llm/prompt_log.py:81-113`) — never a prompt body or a row. So
> *"D6's regime … does not reach case text"* stays TRUE after Phase 2, and the ROPA's two
> tripwires fire on other days (§4(a): the day Tab I published, s234; §4(c): the day REAL
> case text replaces synthetic). AC-11, Step 5, SD-D consequence 1, SD-F and Verification
> §5 are rewritten to the measured truth.
> **(ii)** all three tables carry `tenant_id` through `TenantKeyMixin` (`services/db/repair_case.py:57`,
> `repair_case_evidence.py:73,:167`; the mixin at `services/db/tenant.py:62-71`) and the
> exclusion enumeration omitted it — AC-3 (i) would redden on the first run. Added, ×3.
> **(iii)** AC-10 keyed exclusions by column alone while AC-3 (iii) fails any exclusion
> *"naming a column the ORM no longer has"*: `seq` exists on `repair_case_accepted_quote`
> only (`repair_case_evidence.py:307`), `photos` on `repair_case` only, `note` / `attachment`
> on `repair_case_quote` only — a flat dict is stale for two tables on every non-universal
> entry. Exclusions are now keyed `(type, column)` and AC-3 (iii) is defined per pair.
> **(iv)** AC-11's `grep` read was half-vacuous: at baseline the verbatim needle reads
> ROPA=**1**, module=**0**, because the docstring line-wraps the phrase (`does not reach case`
> / `text`, `repair_case_retention.py:8-9`); a whitespace-normalised instrument with a
> control reads module=1, ROPA=1 (s294, control PASS). With (i) the absence read is
> withdrawn entirely; the presence reads AC-11 now carries are per-artifact `grep -c` on
> sentences written on ONE physical line (ruff `line-length = 100` permits it), so the
> instrument can see what it is asked about.

---

## Goal

Make fleet's governance/transaction data — the repair cases demo play creates, and the
quotes/accepted-quotes that carry the governed spend decision — queryable from **Tab C
(Ask)** exactly the way the operational ontology already is, via ratified option **(A)**:
the ontology YAML **declares** the ruled types (SD-B, RULED: `RepairCase`,
`RepairCaseQuote`, `RepairCaseAcceptedQuote` — `/meta` 7 → 10; so `/meta` advertises
them and the NL-query translator gains them as vocabulary), the **adapter seam serves**
the rows from the existing tables through a session-owning fleet adapter (SD-A, RULED
(b)), **plus a fail-closed guard that keeps the YAML and the hand-written ORM in
lockstep** in both directions. The customer-visible point (Cray, typed 2026-08-18):
a visitor who opened a repair case on Tab B and then asks Tab C "มีเคสซ่อมของ truck-01
กี่เคส" must get a grounded answer sourced from the same rows — proof that the data
across screens is genuinely related through one ontology, and that this ontology is what
makes future LLM leverage possible.

## Baseline facts (verified 2026-08-18, session 237, `main` @ `06170b4` — re-verified on disk by this draft)

Cited here so Steps/ACs can anchor to them; do not re-derive.

- **F1.** Tab C already answers fleet *ontology* questions live ("How many trucks are
  there?" → `{object_type:"Truck", operation:"count"}` → "There are 3 trucks…",
  `phrased_by: gpt-oss:20b`). The engine is vertical-generic; nothing energy-specific.
- **F2.** Fleet `/meta` (`services/api/routers/actions.py:210`, reading
  `load_ontology_meta(settings.oct_vertical)`) exposes exactly **7** object types:
  Truck, OperationalEvent, Alert, RecommendedAction, Depot, AlertEventLink, Vendor.
- **F3.** `^/query$` is already on fleet's Cloudflare allowlist
  (`deploy/published/oct-fleet-maintenance/cloudflared/config.yml`). No deploy change.
- **F4.** The chain: `services/api/routers/query.py:49-52` → `answer_question` →
  `load_ontology_meta(vertical)` (`services/engine/nl_query.py:1315`) →
  `services/engine/ontology_meta.py:288-298` reads **only** `ontology_path(vertical)`
  (`verticals/fleet_maintenance/ontology/fleet_maintenance_v0.yaml`) — **no adapter
  contribution** to the type vocabulary. The translator's vocabulary is
  `_describe_ontology(meta)` (`nl_query.py:382`) consumed by `_translate_messages`
  (`:401`). Declaring in the YAML is therefore unavoidable — this is why option (A).
- **F5.** Data retrieval: `registry.get_adapter(vertical)` then
  `adapter.fetch_objects(query.object_type)` (`nl_query.py:1352,:1362`) — called with
  the protocol's **default `limit=1000`**; filters are applied in-engine (`_matches`,
  `:1369`) after fetch. Retrieval failure degrades to an honest ungrounded answer
  (`:1363-1367`) — never an invented one.
- **F6. 🔴 Hard constraint.** `services/engine/data_adapter.py:36-43` — the
  `DataAdapter.fetch_objects(object_type, filter_expr, limit)` protocol carries **no
  session**. **Grounded negative:** no adapter in any of the six verticals reads a
  database today (`grep "AsyncSession|async_session|select(" verticals/*/data_adapter/*.py`
  → zero). `FleetMaintenanceSyntheticAdapter.fetch_objects`
  (`verticals/fleet_maintenance/data_adapter/__init__.py:52-62`) is a pure dict lookup,
  `[]` on unknown type. Resolved by SD-A.
- **F7.** The data surface: **8 tables across 6 modules**, migrations 0013–0021 — all
  already applied. `repair_case` (`services/db/repair_case.py:73`),
  `repair_case_order_number` + `repair_case_closeout`
  (`services/db/repair_case_closeout.py:73,:104`), `repair_case_quote` +
  `repair_case_justification` + `repair_case_accepted_quote`
  (`services/db/repair_case_evidence.py:85,:139,:202`), `repair_case_run_link`
  (`services/db/repair_case_run_link.py:84`), `repair_case_task_event`
  (`services/db/repair_case_task.py:54`). **No new migrations in this PLAN.**
- **F8.** Fleet has **no committed generated ORM**: `_ORM_COMMITTED_DEST` = energy +
  core only, `_PYDANTIC_COMMITTED_DEST` = core only
  (`services/engine/code_generator.py:900-914`); every fleet codegen output is a
  gitignored reference artifact under `verticals/fleet_maintenance/generated/`
  (`:921-938`). The real table definitions stay hand-written in `services/db/`.
- **F9. 🔴 Grounded negative:** the lockstep guard does not exist. The only
  ontology-related hook is `check-jsonschema` (`.pre-commit-config.yaml:50-56`) —
  YAML *shape* vs `services/engine/ontology_schema.json`, never YAML vs ORM. The
  closest precedent to copy is `tools/check_alembic_model_registration.py`
  (hook `alembic-model-registration`, `.pre-commit-config.yaml:134-139`).
- **F10.** Adjacent, not this PLAN: `run_query` is wired from
  `services/api/routers/insights.py:245,:339,:351` and `/insights/*` is **not** on
  fleet's allowlist. The run corpus is not Ask; do not conflate (Out of Scope).
- **F11.** *(Found by this draft, not in the dispatch fact-pack.)* The scaffolder's
  golden diff-oracle uses fleet as donor and asserts the donor's object SET
  (`tests/services/engine/scaffolder/test_golden_e2e.py:328-349`), with a
  hand-maintained exemption set `_DONOR_EXTENSION_OBJECTS` (`:306-325`, currently
  `{"Vendor"}`) whose own comment warns: past "a couple of entries", build the
  scaffolder an extension slot instead. Adding governance types **will redden this
  test** until exempted — Step 1 handles it; the slot itself is Out of Scope.
- **F12.** *(Found by this draft.)* `ontology_schema.json` sets
  `additionalProperties: false` on object types — the YAML **cannot** carry a custom
  DB-mapping key (e.g. `x_orm_model`). The type↔table mapping must live outside the
  YAML (Step 2 puts it in the guard's shared mapping module).
- **F13.** *(Found by this draft.)* Visitor-typed free text is wider than
  `repair_case.description` + `photos`: `repair_case_quote.note` (`repair_case_evidence.py:111`),
  `repair_case_quote.attachment` (`:120`), `repair_case_accepted_quote.reason` (`:258`)
  are all visitor-typed, and `vendor` (`:106`) is a visitor-typed short string. SD-D
  covers all of them, not just `description`.

## Acceptance Criteria

Every AC names its artifact by path, its command, and a pass/fail read fixed **before**
the run. Commands run from the repo root via WSL (CLAUDE.md §8 evidence rules apply:
`2>&1`, no `head`/`tail` pipes, verdict read from a file). The type set is **RULED**
(SD-B, Cray typed 2026-08-18): **RepairCase, RepairCaseQuote, RepairCaseAcceptedQuote**.
The projected-column set is **RULED** (SD-D, same day): free text `description`,
`vendor`, `reason` IN; `note`, `photos`, `attachment` OUT (see the SD-D block for
provenance — the last two are Code's exclusion, reversible by Cray).

### Phase 1 — Declare + guard (one unit: REJECT-IF-2 — the declaration never lands on `main` without the guard)

- [x] **AC-1 — the YAML declares the ratified types.**
  Artifact: `verticals/fleet_maintenance/ontology/fleet_maintenance_v0.yaml`.
  Command (a): `uv run --no-sync pre-commit run check-jsonschema --all-files` → exit 0.
  Command (b): `uv run python -c "from services.engine.ontology_meta import load_ontology_meta; print(sorted(t.name for t in load_ontology_meta('fleet_maintenance').object_types))"`.
  Pass read (fixed pre-run): the printed list is exactly the 7 baseline names (F2) plus
  the ruled set, alphabetically:
  `['Alert', 'AlertEventLink', 'Depot', 'OperationalEvent', 'RecommendedAction', 'RepairCase', 'RepairCaseAcceptedQuote', 'RepairCaseQuote', 'Truck', 'Vendor']`.
  Each new type declares `primary_key`, `title_key`, Thai + English `synonyms`, and the
  relational refs — `RepairCase.truck_id` as `ref → Truck`, `*.case_id` as
  `ref → RepairCase` — because the refs are the machine-readable form of "the screens
  are related" (Goal) and what `_describe_ontology` renders as `(ref->Target)`.
- [x] **AC-2 — `/meta` advertises them.**
  Artifact: a test in `tests/api/` (new file `tests/api/test_meta_fleet_governance_types.py`
  or the existing meta-test module — executor's call) asserting GET `/meta` under the
  fleet vertical contains each ratified type with its declared `primary_key` and that
  `RepairCase.truck_id` carries `target: Truck`.
  Command: `uv run pytest tests/api/test_meta_fleet_governance_types.py -x 2>&1`.
  Pass read: green. **Witnessed RED (mandatory, CLAUDE.md §8):** the same test run at
  baseline (before the YAML edit) fails on the missing type name — captured in the step
  log before the edit lands.
- [x] **AC-3 — the lockstep guard exists, reads both artifacts, and reddens in both directions.**
  Artifacts: `tools/check_ontology_orm_lockstep.py`; hook id **`ontology-orm-lockstep`**
  in `.pre-commit-config.yaml` (local repo, `uv run python tools/check_ontology_orm_lockstep.py`,
  `always_run: true` — the violation is authored by editing a *different* file than the
  one that trips, same rationale as `alembic-model-registration`); CI step
  `Ontology↔ORM lockstep (pre-commit ontology-orm-lockstep)` in
  `.github/workflows/ci.yml` running
  `uv run --no-sync pre-commit run ontology-orm-lockstep --all-files` (the PLAN-0107
  AC-6 precedent at `ci.yml:98-102`); tool tests
  `tests/tools/test_check_ontology_orm_lockstep.py` using a repo-root override env var
  (`ONTOLOGY_GUARD_ROOT`, mirroring `ALEMBIC_GUARD_ROOT`) over fixture trees.
  The guard **reads both real artifacts** — it parses the ontology YAML from disk and
  reads the ORM column set from the imported model's `__table__.columns` — and compares
  them per the declared type↔table mapping; it never compares a hardcoded expected list
  to itself (the mapping + exclusion entries say *which* pairs to compare and *which*
  columns are deliberately undeclared, never what the compared sets contain).
  Command: `uv run pytest tests/tools/test_check_ontology_orm_lockstep.py -x 2>&1`.
  Pass read, fixed pre-run — the tool exits 1 and names the offender for each of:
  (i) an ORM column absent from the YAML and not in **that type's** exclusion entries
  (✎ s294: `tenant_id`, stamped on every table by `TenantKeyMixin`, is the first column
  this fires on if the entries omit it — Errata (ii));
  (ii) a YAML property with no ORM column;
  (iii) a **stale exclusion** — an exclusion entry `(type, column)` whose column that
  type's table no longer has (✎ s294, Errata (iii): defined per pair, because `seq`,
  `photos`, `note` and `attachment` each exist on ONE of the three tables — a column-only
  entry would be stale for the other two by this very rule);
  (iv) a declared YAML property whose type is incompatible with the column's SQL type
  (per the small SQLA→ontology type map: `Text→string | enum | ref`, `Numeric→float`,
  `DateTime→timestamp`, `JSONB→json`, `BigInteger→int`; a column type outside the map
  is refused as `unmapped-sql-type`, never guessed);
  and exits 0 on the lockstep fixture.
  ✎ **s294 Step 2, `was an error`:** the map read `Text→string`, while AC-1 requires
  `truck_id` / `case_id` — both `Text` columns — to be `ref` properties, so a guard built
  to that letter reddens on AC-1's own declaration. Built as `Text→string | enum | ref`.
  Also built and fixture-tested beyond (i)–(iv): `excluded-and-declared` (an exclusion the
  YAML contradicts — the projection follows the YAML, so the exclusion would read as
  protection while the column reached the model), `undeclared-type` (a mapped type the
  YAML does not declare, which would otherwise be compared against nothing), and a
  REFUSAL, exit 2, when either input is missing. The mapping module is loaded by path, so
  `ONTOLOGY_GUARD_ROOT` fixture trees supply their own tables.
- [x] **AC-4 — the guard is non-vacuous on the LIVE tree (witnessed RED, both directions).**
  Development-time probes, evidence captured in the PR body: (a) add a scratch column to
  `services/db/repair_case.py` (backup to the scratchpad first, restore from that copy —
  never from git), run `uv run python tools/check_ontology_orm_lockstep.py 2>&1` → exit 1
  naming the scratch column; (b) add a scratch property to the fleet YAML, same command
  → exit 1 naming the scratch property. Pass read: both outputs show exit 1 + the
  offender's name; the restored tree then exits 0.
  ✎ **s294 Step 2 — run through the shipped driver, not a hand-rolled backup** (CLAUDE.md §8:
  probe batteries run through `tools/probe_battery/`). Probes `AC4-a` / `AC4-b` in
  `tests/batteries/plan-0109-phase1-declare-and-guard.json` apply exactly these two
  mutations and run `test_this_repository_passes_its_own_guard`, whose
  `result.returncode == 0` must redden — both `WITNESSED`. The driver snapshots each
  subject before writing and restores it byte- and mode-identically; the run's own
  pre/post sha256 and `git status --porcelain` agreed. The driver keeps each run's outcome,
  not the stderr that named the offender, so the NAME half is asserted separately: on the
  REAL inputs by `test_ac4_a_a_scratch_column_on_the_real_model_is_named` and
  `test_ac4_b_a_scratch_property_on_the_real_yaml_is_named` (the real YAML and real models,
  the scratch column or property added to an in-memory copy — no tracked file touched), each
  witnessed by its own probe; and on the fixture trees, one probe per named assertion.
- [x] **AC-5 — the scaffolder golden oracle stays green via a written exemption, not a weakened assertion.**
  Artifact: `tests/services/engine/scaffolder/test_golden_e2e.py` —
  `_DONOR_EXTENSION_OBJECTS` extended per Step 1 (recommended: derive the exemption for
  DB-backed types from the guard's mapping module so one source of truth feeds both,
  with the existing "exemption naming a missing object fails" tripwire retained).
  Command: `uv run pytest tests/services/engine/scaffolder/ -x 2>&1`.
  Pass read: green. **Witnessed RED:** the golden set-equality test run after the YAML
  edit and before the exemption fails naming the new types — captured in the step log.

### Phase 2 — Serve the data through the adapter seam (SD-A RULED (b) — the session-owning fleet adapter)

- [x] **AC-6 — the fleet adapter serves DB-backed types with the SD-D-RULED projection.**
  Artifact: `verticals/fleet_maintenance/data_adapter/__init__.py` (+ a projection
  module if the executor splits it). DB-backed test (existing disposable-test-DB
  convention, `tests/db_support.py`) seeding one repair case **with a non-null
  `description` and one photo**, one quote **with a non-null `note` and a non-null
  `attachment`**, and one accepted quote **with a non-null `reason`**, then calling
  `await adapter.fetch_objects(...)` for each of the three types.
  Command: `uv run pytest tests/verticals/fleet_maintenance/test_adapter_db_objects.py -x 2>&1`.
  Pass read, fixed pre-run: the returned dict's key set is **exactly** the declared YAML
  property set per type — RepairCase:
  `{case_id, truck_id, opened_by, opened_at, description, status, work_type}`;
  RepairCaseQuote: `{quote_id, case_id, vendor, amount_thb, entered_by, entered_at}`;
  RepairCaseAcceptedQuote: `{accepted_id, case_id, quote_id, reason, accepted_by,
  accepted_at, lowest_amount_at_acceptance_thb, lowest_at_acceptance_basis}` (`seq`
  excluded as internal; `tenant_id` excluded on all three types — AC-10, ✎ s294). **Presence controls (ruled IN):** the seeded `description`,
  `vendor` and `reason` values round-trip **verbatim** into the projected dicts.
  **Absence controls (ruled OUT):** `note`, `photos`, `attachment` appear in **no**
  returned dict — and the seed's non-null values are the positive control making that
  absence a real exclusion, not a vacuous one (CLAUDE.md §8: an absence needs a positive
  control); datetimes are ISO-8601 strings; `amount_thb` is a float.
- [x] **AC-7 — the seven synthetic types are untouched.**
  Command: `uv run pytest tests/verticals/fleet_maintenance/ 2>&1` (full directory).
  Pass read: every pre-existing test green with zero modifications to their assertions;
  `health_check()` still reports the seven synthetic object counts (it may *add* a DB
  status field; it may not change existing keys).
  ✎ **s294, `was an error`:** measured, the base adapter's `object_counts` holds **four**
  types — `Depot`, `OperationalEvent`, `Truck`, `Vendor` — not seven (`Alert`,
  `RecommendedAction` and `AlertEventLink` are declared but not served by it). Built as:
  every existing key keeps its value and exactly one key is added, `db_backed_types`
  (listed, not pinged); the synthetic types are compared against the unchanged base
  adapter in `tests/verticals/fleet_maintenance/test_adapter_db_objects.py`.
- [x] **AC-8 — the scenario test (CLAUDE.md §8, binding): real producer into real consumer.**
  Artifact: `tests/verticals/fleet_maintenance/test_ask_repair_case_scenario.py`.
  ✎ *s294:* built at `tests/api/test_ask_repair_case_scenario.py` — `client_with_db` and
  `api_db_maker` live in `tests/api/conftest.py`, and a copy would be a second definition
  of how a test binds to the disposable database.
  The **real producer**: two repair cases opened through `POST /api/cases`
  (`services/api/routers/cases.py:183`) on the real app against the test DB — the same
  route demo play uses; one quote added via `POST /api/cases/{id}/quotes`. The **real
  consumer**: `answer_question(question, "fleet_maintenance", client=<transport stub>)`
  with the fleet adapter registered — translate → execute → phrase all real, only the
  LLM *transport* canned (`tests/support/nl_query_transport_stub.py` /
  `TranslateOnlyStub`, the PLAN-0104 precedent in
  `tests/services/engine/test_grouped_count_scenario.py`).
  Command: `uv run pytest tests/verticals/fleet_maintenance/test_ask_repair_case_scenario.py -x 2>&1`.
  Pass read, fixed pre-run: `answer.grounded is True`; the count aggregate equals **2**;
  (✎ *s294, `was an error` in the wording, not the intent:* an UNGROUPED count carries no
  `aggregate` object — `nl_query.answer_question` builds one only for numeric aggregates
  and grouped counts — so the count is asserted as the engine's own deterministic
  sentence `2 RepairCase record(s) match that query.` together with the two source ids);
  `source ids == the two case_ids the POSTs returned` (proving the rows flowed, not a
  fixture); a second scenario case filters by `truck_id` and matches only that truck's
  case. **Non-vacuity probe with a named changing output:** opening a third case changes
  the asserted count read from 2 → 3 (asserted in-test by a second act+ask round);
  severing the adapter's DB branch (dev-time scratch mutation, restored from the
  scratchpad) flips `grounded` to False — witnessed once during Step 4.
  ⚠️ Like the PLAN-0104 scenario, this makes **no claim the live model emits the
  translation** — that claim belongs to the (Cray-gated) live smoke in AC-14 only.
- [x] **AC-9 — honest degrade without a database.**
  Artifact: an offline test in the same module: adapter constructed with a session
  factory pointing at an unreachable URL → `answer_question` returns the ungrounded
  "couldn't retrieve" answer (`nl_query.py:1363-1367` path), never an invented count.
  Command: same pytest file, no DB required for this case.
  Pass read: `grounded is False` and the canned honest-degrade phrase, not a number.
- [x] **AC-10 — the projection is an ALLOWLIST, single-sourced and leak-resistant.**
  Artifact: one shared module (recommended:
  `verticals/fleet_maintenance/data_adapter/db_projection.py`) holding the
  type↔table mapping and the exclusion entries keyed **`(type, column) → reason`** —
  ✎ s294, per pair, never by column alone (Errata (iii)). The seven entries, authored from
  the model classes: `(RepairCase, photos)` and `(RepairCaseQuote, attachment)` —
  `payload-not-text (Code, reversible)`; `(RepairCaseQuote, note)` — `ruled-out (Cray)`;
  `(RepairCaseAcceptedQuote, seq)` — `internal`; `(RepairCase, tenant_id)`,
  `(RepairCaseQuote, tenant_id)` and `(RepairCaseAcceptedQuote, tenant_id)` —
  `tenancy-key (TenantKeyMixin, ADR-0035 D7; never queryable)`. **Both** the adapter's
  projection and `tools/check_ontology_orm_lockstep.py` import it.
  **The projection emits exactly the declared YAML property set** (read from the real
  ontology artifact) — an allowlist naming what is included, never "all columns minus a
  denylist". Consequence, asserted in the tool tests: an ORM column added later is
  **excluded by default** and simultaneously **reddens the guard** (AC-3 direction (i))
  until it is either declared in the YAML (a visible, reviewable diff) or given a
  reasoned exclusion entry — a future free-text column has no silent leak path.
  Command: `uv run pytest tests/tools/test_check_ontology_orm_lockstep.py -x 2>&1`
  (fixture cases) — pass read: (a) the new-column fixture shows default-excluded +
  guard exit 1; (b) deleting an exclusion entry while the YAML stays silent makes the
  guard exit 1 (a quiet leak attempt forces a visible diff or a red guard).

- [x] **AC-11 — the compliance record is EXTENDED in the same PR, and its true sentences are KEPT (SD-D consequence 1 — mandatory, its own AC, not a Step footnote). ✎ Rewritten s294 — Errata (i) + (iv).**
  Artifacts: `docs/compliance/ropa-change-statement-fleet.md` **and** the module
  docstring of `services/db/repair_case_retention.py`.
  **What Phase 2 changes, measured:** once the fleet adapter serves the three types, a
  `/query` question that returns rows sends the projected values — including the
  ruled-IN free text `description` / `vendor` / `reason` — to the on-prem model as part
  of the **phrase** request (`services/engine/nl_query.py:1208-1235`: up to
  `_PHRASE_FACT_CAP` records as `facts_json`, only when the LLM arm phrases; the
  deterministic fallback sends nothing). **What it does NOT change:** the translate
  request still carries the ontology description + the question and never a row
  (`_describe_ontology` `:395`, `_translate_messages` `:414`); the ADR-0035 D6 prompt log
  still stores its closed field set, whose `text` is the visitor's **question** — never
  the prompt body or a record (`services/engine/llm/prompt_log.py:81-113`); so D6's
  **retention regime still does not reach case text**. The sentences the draft called
  stale are therefore TRUE and stay: (a) `repair_case_retention.py:7-13` ("does not
  reach case text"); (b) the ROPA's §3.1 item 2 / §4(a) scope claim. The ROPA's two
  tripwires are not this PR's either — §4(a)'s fired when Tab I published (s234) and
  §4(c)'s fires when REAL case text replaces synthetic; neither is re-attributed.
  **What must be written — an addition that corrects the record's completeness, never
  an appendage to a false sentence:** (1) a new dated subsection in the ROPA change
  statement, in the §3.3 shape ("🆕 … added sNNN"), naming PLAN-0109, the ruled IN-set,
  the new **reader** (Tab C / `/query`), the new **processing step** (case text leaves
  the row in a phrase request to the on-prem model host, `_PHRASE_FACT_CAP` records per
  question), what is stored (the question only — the D6 field set), and its bounds (the
  90-day case sweep; D6 prompt-log rotation applies to the question, not to rows; the
  `case-persist-notice`; the SD-F injection-shaped surface); (2) in the retention
  docstring, one added sentence beside the kept one, so *"does not reach case text"*
  cannot be misread as *"the model never sees case text"*. **The same one-line sentence
  appears verbatim in both artifacts** (the ROPA subsection opens with it), written on
  ONE physical line (ruff `line-length = 100`), and the docstring's kept sentence is
  re-flowed so its needle sits on one line too — a needle that spans a wrap reads 0
  while the content is present (Errata (iv): verbatim module=0, normalised module=1).
  Commands (each to a file; `grep -c` over two files prints one count PER file):
  `grep -c "does not reach case text" services/db/repair_case_retention.py docs/compliance/ropa-change-statement-fleet.md 2>&1`
  and `grep -c "<the added sentence, bytes fixed in the PR body BEFORE the edit>" services/db/repair_case_retention.py docs/compliance/ropa-change-statement-fleet.md 2>&1`.
  Pass read (fixed): the kept sentence reads **≥ 1 in EACH artifact** (retention, and the
  positive control that the instrument sees both files); the added sentence reads **≥ 1
  in EACH artifact**; the ROPA subsection names PLAN-0109 and the IN-set. **Witnessed RED
  at baseline (s294):** added sentence `0` / `0`; kept sentence module `0` (wrapped) /
  ROPA `1` — so a green on the kept-sentence read is itself evidence the re-flow landed.
  **Why no existing guard closes this:** the retention module's own import-absence
  guard — `test_ac9_the_module_does_not_inherit_the_prompt_log_regime`
  (`tests/services/db/test_case_retention.py:327,:343`) — asserts only that the
  retention module **imports** nothing from `prompt_log`. This change adds no import,
  so that guard **cannot redden** on it: the coupling is data-flow (case text flowing
  *into* a model request), and the instrument is aimed one field to the left. Hence a
  mandatory AC with its own per-artifact reads instead of trust in an existing green.

### Phase 3 — Evidence + closure

- [x] **AC-12 — SD-E confirmed on disk: the YAML edit changes zero committed files via codegen.**
  Command: run the engine's generate CLI for fleet (`uv run vero-lite ...` — the
  console-script form, never `python -m`), then `git status --porcelain 2>&1` written to
  a file. Pass read (fixed): empty output — every regenerated artifact lands under
  gitignored `verticals/fleet_maintenance/generated/` (F8). The changed gitignored set
  (models/schema/mcp/types/orm/context-pack) is listed in the step log for the record.
- [x] **AC-13 — full offline gate at CI scope.**
  Commands: bare `uv run ruff check . 2>&1`; full `uv run mypy services/ verticals/ 2>&1`
  (CI scope per PLAN-0107 AC-5); full `uv run pytest tests/ 2>&1` on the checkout that
  owns the test DB. Pass read: all green — partial-scope greens do not close this AC.
- [ ] **AC-14 (optional — requires explicit typed Cray go; host-state, CLAUDE.md §8).**
  One live smoke on the published fleet demo: a repair-case question through Tab C
  answers grounded from a case demo play created. Evidence, not a gate — the offline
  oracle (AC-8) is the gate. Skipping this AC does not block closeout; running it
  without Cray's typed go is a violation.

## Out of Scope

- ❌ **New alembic migrations.** All 8 tables exist (F7, migrations 0013–0021). A step
  that "needs" one is mis-scoped — stop and re-read F7.
- ❌ **Changing the `DataAdapter` protocol or ADR-007.** SD-A is RULED (b): the
  protocol signature, ADR-007, the engine and the other five verticals stay untouched.
  Reopening (a) would be a new Cray ruling and a re-scope, not a drift within this PLAN.
- ❌ **The other five verticals' adapters.** Zero diffs outside `verticals/fleet_maintenance/`
  at the adapter layer.
- ❌ **The run corpus on Ask.** `run_query` / `/insights` (F10) stays off Tab C;
  `repair_case_run_link` is not declared (SD-B) partly for this reason.
- ❌ **Tab C UI changes.** The UI renders whatever `/query` returns; nothing here changes it.
- ❌ **`link_types` declarations** for case↔truck — the `ref` properties give the
  translator the relationship; a link-object is weight without a consumer today.
- ❌ **A scaffolder extension slot** (F11's tripwire). If `_DONOR_EXTENSION_OBJECTS`
  keeps growing after this PLAN, that slot is its own PLAN — noted, not built here.
- ❌ **Committed codegen for fleet** (F8) — no `_ORM_COMMITTED_DEST` entry is added.
- ❌ **Declaring the remaining five tables** — ruled out with the spine (SD-B, RULED):
  `RepairCaseCloseout` + `RepairCaseOrderNumber` (after-the-fact bookkeeping — noise
  for Ask); `RepairCaseJustification` (mostly visitor free text, little structured
  value — and its `reason` is the same class as the quote `note` Cray ruled out);
  `RepairCaseRunLink` (dangles without the run corpus, F10); `RepairCaseTaskEvent`
  (operational chatter). Widen only on demonstrated demo pull, via a new ruling.
- ❌ **`note`, `photos`, `attachment` reaching the LLM prompt** (SD-D, RULED — with
  split provenance): `note` is **Cray's typed ruling**; `photos` + `attachment` are
  **Code's exclusion, not Cray's** — a path list and a JSON blob are payload, not text
  an LLM answers from — and **Cray can reverse it**. Any reversal is a YAML
  declaration + exclusion-entry diff + an AC-11-class compliance correction in the same
  PR, never a silent projection edit (AC-10's allowlist makes the silent path
  structurally red).

## Steps

SD-A, SD-B and SD-D are **RULED** (Cray, typed 2026-08-18, session 237 — recorded in
the SD blocks below, per the record-the-amendment-when-Cray-rules lesson); SD-C is
Code-adopted (open to countermand); SD-E needs no ruling (AC-12 is its stop-condition).
**No step waits on a ruling.** All work on a feature branch; Phase 1 and Phase 2 may be
separate PRs, but **AC-1's YAML edit and AC-3's guard land in the same PR**
(REJECT-IF-2), **the Phase 2 PR that makes `description` reachable from Ask carries the
AC-11 compliance corrections in that same PR** (SD-D consequence 1), and if Phase 2
merges separately, the intermediate state on `main` is the honest "no records" answer
(unknown type → `[]`, F6) — never a wrong answer, and never longer than one PR cycle.

### Step 1 — Declare the ratified types + settle the golden-oracle coupling (AC-1, AC-2, AC-5)

Add the SD-B-ratified object types to `fleet_maintenance_v0.yaml` under ADR-008 D1's
"may extend" license, mirroring the Vendor precedent (property comments carry
provenance; Thai-first synonyms per the `_property_aliases` rationale, e.g. RepairCase:
`th: [เคสซ่อม, ใบแจ้งซ่อม]`). Types use the schema's enum vocabulary (F12 check ran:
`timestamp` for datetimes, `float` for `Numeric`, never a made-up `datetime`).
Property sets = ORM columns minus the exclusions (`photos`, `note`, `attachment`, internal
`seq`, and `tenant_id` on every table — `TenantKeyMixin`, ✎ s294 Errata (ii)) — authored
by reading the model classes (F7), not from memory. The
ruled-IN free text (`description`, `vendor`, `reason`) is declared as `string`
properties like any other.

Run the AC-2 meta test **first** at baseline to witness its RED, then edit, then run the
scaffolder suite to witness AC-5's RED, then extend `_DONOR_EXTENSION_OBJECTS` with the
written reason (recommended: import the DB-backed type set from Step 2's mapping module
so exemption and guard share one source; keep the dead-exemption tripwire assertion).
**Non-vacuity probe / changing output:** the AC-1(b) printed type list changes from the
7-name baseline to the ratified list; the meta test flips RED→GREEN on exactly the edit.

### Step 2 — Build the lockstep guard (AC-3, AC-4, AC-10)

New `tools/check_ontology_orm_lockstep.py`, copying the shape of
`tools/check_alembic_model_registration.py` (F9): stdlib + repo imports, root-override
env var `ONTOLOGY_GUARD_ROOT` for fixture trees, exit 0/1, offender-naming stderr with a
"why it matters" consequence line. The type↔table mapping + exclusions live in the
shared module (AC-10; F12 forbids an in-YAML mapping key). The guard reads the YAML via
ruamel from disk and the column set via the imported model's `__table__.columns` —
both real artifacts, both directions, plus the stale-exclusion and type-compat checks
(AC-3 i–iv). Wire the pre-commit hook (`always_run: true`) and the CI step (PLAN-0107
AC-6 pattern). Tool tests build lockstep + four broken fixture trees.
✎ *s294:* built as lockstep + six broken trees + the refusal + AC-10 (a)/(b) + the real
tree with its counts pinned (`types=3 declared=21 columns=28 excluded=7 offenders=0`) +
AC-4's two name tests on the real inputs. All 34 assertions — these 26 and AC-2's 8 — are
witnessed by `tests/batteries/plan-0109-phase1-declare-and-guard.json` (35 probes,
`GAPS: 0`, 0 exemptions).
**Non-vacuity probe / changing output:** the AC-4 live-tree probes — the guard's exit
code and stderr change from `0`/silent to `1`/offender-named on the scratch column and
scratch property; both witnessed and captured before restore (restore from the
scratchpad copy, never `git checkout` — the probe discipline from the lessons file).

### Step 3 — The adapter's DB branch (AC-6, AC-7, AC-9 — SD-A RULED (b))

Extend `FleetMaintenanceSyntheticAdapter`: `fetch_objects` consults the DB-backed
mapping first — for a governance type it opens a short-lived session from an injectable
`session_factory` (constructor param, default `services.db.session.async_session` —
engine creation is lazy, `services/db/session.py:14`, so import cost is nil), runs a
deterministic `select(...).order_by(opened_at/entered_at DESC).limit(limit)`, and
projects rows through the declared-property **allowlist** (AC-10): exactly the YAML
property set, the excluded columns (`photos`, `note`, `attachment`, `seq`, `tenant_id` —
per `(type, column)`, AC-10 ✎ s294) never emitted, datetimes to ISO strings, `Decimal`
to float — the procurement-datetime
lesson.
✎ **s294 — a coupling this draft did not see, and how it was built.** The scaffolder's
golden oracle holds `data_adapter/__init__.py` STRUCTURALLY EQUAL to what the scaffolder
emits (`test_row_4_adapter_is_structurally_equal_to_the_donor` — the one row that
ledger claims equality for), so a DB branch written into that file reddens it. Witnessed
RED before any oracle edit: exactly two failures, row 4 and the file-set test. Built as a
subclass, `FleetMaintenanceAdapter`, in the post-scaffold module
`verticals/fleet_maintenance/data_adapter/db_objects.py`; the registrar instantiates it,
and row 4 names that two-line substitution exactly (each entry must match once, so a
stale one reddens) while the class, every method and the rest of the registrar stay
under structural equality. The subclass overrides only `__init__`, `fetch_objects` and
`health_check` — pinned by a test — so `fetch_links` / `stream_events` remain the base's.
Synthetic types fall through to the existing dict path unchanged. Update the module
docstring (its "No external I/O" claim becomes false) and `health_check` (additive
DB-status key only, AC-7). Injecting the *test-DB-bound factory* in tests is
configuration, not stubbing — the real query path runs against a real database.
**Non-vacuity probe / changing output:** AC-6's key-set assertion — inserting a row with
non-null `description` and asserting its projected absence is the positive control; and
the seeded-row count in the DB changes the length of the returned list.

### Step 4 — The scenario test (AC-8, AC-9)

Per AC-8, drive `POST /api/cases` (+ one quote) through the real app on the test DB
(fixture pattern: `tests/verticals/fleet_maintenance/test_governed_repair_hero.py`),
register the real fleet adapter with the test-DB factory, then `answer_question` with
`TranslateOnlyStub` — the one canned element is the model *transport*, the established
offline pattern (F4-chain stays real end to end). Assert grounded/count/source-ids per
AC-8's fixed read; act again (third case) and assert the count read **changes** 2→3 —
the probe's named changing output. Witness the severed-branch RED once (scratch
mutation, restore from scratchpad). Add the AC-9 unreachable-DB degrade case.
✎ *s294:* the severed-branch RED ran through the shipped driver, not a hand-rolled scratch
copy (CLAUDE.md §8): probe `S-severed` in `tests/batteries/plan-0109-phase2-serve.json`.
That battery witnesses every assertion in the adapter and scenario modules — 38 probes,
42 claims, 4 exemptions (each a positive control over the test's own seed, with its reason
written), `GAPS: 0` — with restore checked by sha256 and `git status --porcelain`.

### Step 5 — Extend the compliance record (AC-11; lands in the Phase 2 PR) — ✎ rewritten s294, Errata (i)/(iv)

Fix the added sentence's exact bytes in the PR body first. ✎ *s294 — fixed as:*
`PLAN-0109: Tab C phrase requests carry case description, vendor and reason to the on-prem model.`
(96 characters, one line in both artifacts). Then amend
`docs/compliance/ropa-change-statement-fleet.md` with a dated `🆕` subsection in the §3.3
shape: PLAN-0109, the ruled IN-set (`description` / `vendor` / `reason`), the new reader
(Tab C / `/query`), the new processing step (a phrase request to the on-prem model
carrying up to `_PHRASE_FACT_CAP` projected records — `nl_query.py:1208-1235`), what is
stored (the D6 log's `text` is the question — `prompt_log.py:81-113`), and the bounds
(90-day case sweep on `opened_at`; D6 rotation applies to the question, not to rows; the
public `case-persist-notice`; SD-F). **Keep** §3.1 item 2 and §4(a) — they stay true —
and do **not** re-attribute either tripwire to this PR. In `repair_case_retention.py:7-13`
**keep** the "does not reach case text" sentence, re-flow it onto one line, and add the
same one-line sentence the ROPA subsection opens with. State plainly in the diff that the
existing import-absence guard (`test_ac9_the_module_does_not_inherit_the_prompt_log_regime`,
`tests/services/db/test_case_retention.py:327`) cannot see this coupling — it guards
imports, and this change adds none (AC-11's rationale).
**Non-vacuity probe / changing output:** the added-sentence `grep -c` changes from `0` /
`0` (baseline, witnessed s294) to `≥ 1` / `≥ 1`, and the kept-sentence read changes from
module `0` (wrapped) / ROPA `1` to `≥ 1` / `≥ 1` — per artifact, so a green on one file
cannot vouch for the other (Errata (iv)).

### Step 6 — Regenerate reference artifacts + evidence + closeout prep (AC-12, AC-13)

Run the fleet codegen, capture `git status --porcelain` to a file, read it back (AC-12
pass = empty), list the changed gitignored artifacts in the step log. Run the full AC-13
offline gate at CI scope. Update `docs/STATUS.md` per normal session hygiene. If Cray
gives the typed go, run AC-14's single live smoke and file its evidence; otherwise mark
AC-14 skipped-by-rule. Then PR(s) per the Step-preamble landing constraint; after merge
and Cray's closeout, `git mv` to `docs/plans/done/` per convention.

## Surfaced decisions (SD-A / SD-B / SD-D RULED — Cray, typed 2026-08-18, session 237; SD-C Code-adopted; SD-E no ruling needed)

### SD-A — RULED (b): the session-owning fleet adapter (Cray, typed 2026-08-18)

The protocol (F6) carries no session, and no adapter reads a DB today. The candidate
menu, kept for the record (the drafter's blast-radius pricing stands as surfaced):

- **(a) Widen the protocol** — add a session/context param to `fetch_objects`.
  Blast radius: `services/engine/data_adapter.py` + **all six** verticals' adapters +
  every engine call site + conformance tests, **and** the ADR-007 D1 contract itself (an
  ADR edit → G1-gated, heavier governance). Forces DB-awareness on five adapters that
  have none. Priced honestly: the most invasive option for zero gain to any other
  vertical today.
- **(b) Session-owning adapter (RULED)** — fleet's adapter internally opens a
  short-lived session from an injectable factory defaulting to
  `services.db.session.async_session`, only for DB-backed types. Blast radius:
  `verticals/fleet_maintenance/` only; protocol, ADR-007, engine, and the other five
  verticals untouched. Every consumer routed through the adapter seam sees the same
  data — which is exactly Cray's cross-screen-relatedness rationale. Cost, stated: the
  adapter loses its "no external I/O" purity (docstring + health_check updated); DB
  lifecycle is the adapter's to own (mitigated: per-call `async with`, the same shape as
  the FastAPI dependency at `services/db/session.py:21-24`); DB-down degrades through
  the engine's existing honest-ungrounded path (F5, AC-9).
- **(c) Registry-level provider** — a second registered seam (`register_data_provider`)
  merged by `nl_query`. Blast radius: `registry.py` + engine merge logic + a new
  concept; but only *Ask* would see the data unless every other adapter consumer is also
  taught the seam — it structurally undercuts the "same data on every screen" goal.
- **(d) Engine-side special-case read path** — vertical-specific branching inside the
  vertical-generic engine. Rejected outright: it breaks the property that made F1 true.

**RULED: (b)** (Cray, typed 2026-08-18). Protocol, ADR-007, the engine and the other
five verticals stay untouched. The stated costs stand and are accepted with the ruling:
the adapter loses its "no external I/O" purity (docstring + `health_check` updated);
session lifecycle is per-call `async with`; DB-down degrades through AC-9's
honest-ungrounded path. Step 3 and AC-6 execute this without contingency.

### SD-B — RULED: the demo-play spine (Cray, typed 2026-08-18)

Each added type widens the translator vocabulary (prompt tokens per translate call), the
queryable surface, and the guard's drift surface. Menu, with what each buys:
`RepairCase` (the spine — case counts, per-truck relatedness; without it nothing else
means anything); `RepairCaseQuote` (the ฿ that drives the governed decision — "which
vendor quoted the most?"); `RepairCaseAcceptedQuote` (the governed *outcome* — who
approved, at what amount vs the lowest at acceptance); `RepairCaseCloseout` /
`OrderNumber` (after-the-fact bookkeeping — noise for Ask); `Justification` (mostly
visitor free text — SD-D-hostile, little structured value); `RunLink` (dangles without
the run corpus, F10); `TaskEvent` (operational chatter).
**RULED: the demo-play spine — RepairCase + RepairCaseQuote + RepairCaseAcceptedQuote
(3 types, `/meta` 7 → 10)** (Cray, typed 2026-08-18). The five rejected types are
recorded in Out of Scope with their one-line reasons; widening the set later is a new
ruling, not a drift. Alternatives that were on the table for the record: RepairCase
alone (demonstrates a lookup, not relatedness) or all eight (maximum drift surface for
no demo pull).

### SD-C — Guard mechanism: recommendation ADOPTED BY CODE — not typed by Cray; open to countermand

Locked by the dispatch in outline; the surfaced residue is the *mechanism*. **No typed
ruling was taken from Cray on this SD.** Code adopted the drafter's recommended
mechanism as-is; Cray may countermand at PR review, and a countermand reopens only this
SD — the ruled ones (SD-A/SD-B/SD-D) are unaffected.
**Adopted mechanism:** tool `tools/check_ontology_orm_lockstep.py`; hook id
`ontology-orm-lockstep` (pre-commit, `always_run`); CI step via
`pre-commit run ontology-orm-lockstep --all-files` (PLAN-0107 AC-6 pattern); assertions
AC-3 (i)–(iv) — two-way name lockstep, stale-exclusion detection, type compatibility —
reading the YAML and the imported `__table__.columns`, with the type↔table mapping +
reasoned exclusions in the AC-10 shared module (F12 rules out an in-YAML mapping key).
Alternatives considered: AST-parsing the ORM instead of importing (the alembic guard's
choice — needed there because it scans *all* files and must dodge template text; not
needed here where the mapping names exact modules); a pytest-only guard with no hook
(rejected: the violation is authored while editing a different file, so it must gate
commits, not just CI). Placement remains a governance surface (CLAUDE.md §4: the gate
must live on the enforcer's input surface) — which is exactly why this block records
that the placement was **Code's adoption, not Cray's ruling**, rather than silently
relabeling it (attribution-honesty rule: "เคาะ" = typed picks only).

### SD-D — 🔴 PII / retention — RULED (Cray, typed 2026-08-18) — NOT the drafter's recommendation

Context, unchanged: repair cases carry visitor-typed free text under the 90-day sweep
(`services/db/repair_case_retention.py`), and Ask adds a **new** surface — projected
values enter the **phrase request** to the model (✎ s294, Errata (i): the translate
request carries no row, and the ADR-0035 D6 prompt log stores the question only).
F13: the visitor-typed set is `description`, `photos`, `note`, `attachment`, `reason`,
plus the short string `vendor`. The drafter recommended excluding all free text; **Cray
ruled more free text IN.**

**RULED IN** (projected, queryable, reaching the phrase request — ✎ s294: the ruling is
the SET; the reach is the measured fact, Errata (i)): `RepairCase.description`,
`RepairCaseQuote.vendor`, `RepairCaseAcceptedQuote.reason`.
`opened_by` / `entered_by` / `accepted_by` are demo-persona principal ids from the
procedures roster, not visitor identities — included.

**RULED / EXCLUDED OUT** (guard-enforced, AC-10 — with split provenance):
- `RepairCaseQuote.note` — **ruled out by Cray** (typed).
- `RepairCase.photos` + `RepairCaseQuote.attachment` — **excluded by Code before the
  question reached Cray**, on the stated ground that a path list and a JSON blob are
  not text an LLM answers from — they would carry raw payload into a prompt for no
  answering value. **This exclusion is Code's, not Cray's, and Cray can reverse it**
  (reversal path in Out of Scope).

**Consequences of the ruling — written, not softened:**
1. **The compliance record goes INCOMPLETE at merge — AC-11, mandatory, same PR.**
   ✎ Corrected s294 (Errata (i), `was an error`): this item read that
   `repair_case_retention.py:7-13`'s *"does not reach case text"* becomes FALSE and that
   the ROPA's two tripwires fire on this PR. Measured otherwise — the D6 log stores the
   question (`prompt_log.py:81-113`) and its retention regime still does not reach case
   rows; the tripwires belong to Tab I's publish day (§4(a)) and to real-data day
   (§4(c)). What merge makes true and unrecorded is a new **reader** and a new
   **processing step**: case text leaves the row in a phrase request to the on-prem
   model. AC-11 requires that to be written as an addition, with the true sentences kept.
2. **No existing guard sees this coupling.** The retention module deliberately imports
   nothing from `prompt_log`, and PLAN-0105's AC-9 guard
   (`test_ac9_the_module_does_not_inherit_the_prompt_log_regime`,
   `tests/services/db/test_case_retention.py:327,:343`) enforces exactly that
   **import** absence — verified on disk: it scans imported module names for
   `prompt_log`. This change adds no import, so the guard **cannot redden**; the
   coupling is data-flow (case text flowing *into* a model request — ✎ s294, not into
   prompt-log content), one field to the left of where the instrument is aimed. Priced
   accordingly: AC-11 is a manual correction with its own per-artifact reads, not a
   trusted green.
3. **The operational consequence is recorded for Cray** — SD-F below.

### SD-E — Generated-artifact impact (confirm, then record)

Confirmed on disk by this draft: `_ORM_COMMITTED_DEST = {energy, core}` and
`_PYDANTIC_COMMITTED_DEST = {core}` (`services/engine/code_generator.py:900-914`);
`generate_all` falls back to `output_dir` for fleet (`:921-938`), i.e. gitignored
`verticals/fleet_maintenance/generated/{models.py, schema.sql, schema.json,
mcp_tools.json, types.ts, orm.py, context_pack.md}`. **No committed file changes from
the YAML edit via codegen.** One consequence worth stating: the *generated* fleet
`orm.py`/`schema.sql` for RepairCase will NOT textually match the hand-written
`services/db/` tables (different emitter conventions) — those artifacts are
reference-only and gitignored, and the AC-3 guard, not codegen, is what ties YAML to the
real ORM. AC-12 turns this confirmation into on-disk evidence (`git status --porcelain`
empty after regen). Surfaced as an SD only so Cray sees the residue: **nothing here
needs a ruling unless AC-12's read comes back non-empty**, in which case execution stops
and this SD reopens. *(Ruling status: none needed — confirmed unchanged 2026-08-18.)*

### SD-F — recorded operational consequence of SD-D (no ruling requested now; for Cray to see)

With `description` queryable, a visitor on the **public** demo can type arbitrary free
text that a *later* visitor's Ask question surfaces through the model: it enters the
phrase request (✎ s294 — not the translate request, Errata (i)) and can be echoed inside
a grounded answer. What bounds it
today, stated exactly: the **90-day sweep** deletes the rows, their FK children and the
upload directory (`services/db/repair_case_retention.py` — age-anchored on
`opened_at`); the **D6 prompt-log rotation** bounds the prompt-side copies of the same
text; and the **`case-persist-notice`** already discloses that any visitor can read
case text — Ask is a new *reader* of an already-public surface, not a new audience
class, though whether the notice's wording should also name the LLM path is Cray's to
judge later. What does **not** bound it: nothing moderates the content, and
visitor-typed text inside a phrase prompt is a prompt-injection-shaped surface — the
model may follow instructions embedded in a `description`. Recorded so a later ruling
(moderation, notice wording, or narrowing the IN-set) starts from a stated baseline
rather than a rediscovery.

## Verification

How we know it worked, end to end — each already fixed in its AC:

1. **Declared:** AC-1(b)'s printed type list equals the ratified list;
   `check-jsonschema` green; `/meta` test green after a witnessed baseline RED (AC-2).
2. **Guarded:** the guard's four RED shapes red on fixtures (AC-3), both live-tree
   probes witnessed RED then restored-green (AC-4), hook + CI step present, golden
   oracle green with the written exemption after its witnessed RED (AC-5).
3. **Served, per the ruling:** projected key sets exact — ruled-IN free text
   (`description`/`vendor`/`reason`) round-trips verbatim as the presence control,
   ruled-OUT columns absent against seeded non-null values as the absence control
   (AC-6); the allowlist default-excludes any future column (AC-10); the seven
   synthetic types untouched (AC-7); honest degrade with no DB (AC-9).
4. **Related, provably:** the scenario (AC-8) — rows demo play's own route created are
   the source ids of a grounded Tab C answer, count changing 2→3 when a third case is
   opened, transport-stub-only per the binding §8 scenario rule.
5. **Compliance true at merge:** the kept sentence "does not reach case text" reads
   ≥ 1 in EACH of the retention docstring and the ROPA statement, the added one-line
   sentence reads ≥ 1 in EACH, and the ROPA's new dated subsection names PLAN-0109 and
   the IN-set — landed in the same PR as the serving change (AC-11, ✎ s294).
6. **Priced and clean:** zero committed-file drift from codegen (AC-12), full CI-scope
   offline gate green (AC-13), and — only with Cray's typed go — one live smoke as
   evidence, never as the gate (AC-14).

## Closeout (session 296, 2026-09-12)

Every AC below was **re-measured against `main` `c519466`** in this session. Nothing here is
carried over from the s294 PR bodies; where a figure differs from what was written then, the
fresh reading is the one recorded.

| AC | Command re-run | Read |
|---|---|---|
| AC-1 | `load_ontology_meta('fleet_maintenance')` + `check-jsonschema` | printed list **equals** the ratified 10 names, exit 0 |
| AC-2 | `pytest tests/api/test_meta_fleet_governance_types.py` | 3 passed |
| AC-3 | `pytest tests/tools/test_check_ontology_orm_lockstep.py` | 13 passed; guard on the real tree `VERDICT: PASS exit=0` |
| AC-4 | `probe_battery run --battery plan-0109-phase1-…` | 34 claims, **34 witnessed**, `GAPS: 0`, PASS |
| AC-5 | `probe_battery run --battery plan-0109-ac5-golden-exemption.json` | 2 witnessed at `:398` and `:394`, `GAPS: 0`, PASS |
| AC-6 / AC-7 | `pytest tests/verticals/fleet_maintenance/` | 129 passed |
| AC-8 / AC-9 | `pytest tests/api/test_ask_repair_case_scenario.py` + phase-2 battery | 4 passed; 42 claims, 38 witnessed, `GAPS: 0`, PASS |
| AC-10 | the lockstep tool tests above | included in the 13 |
| AC-11 | the two per-file greps | kept sentence **1 in each** artifact; added sentence present in **both** (`repair_case_retention.py:16`, `ropa-change-statement-fleet.md:250`) |
| AC-12 | `vero-lite generate fleet_maintenance` then `git status --porcelain` | porcelain **byte-identical** pre vs post; positive control (a scratch file) proved the instrument sees a change |
| AC-13 | `ruff check .`, `ruff format --check .`, `mypy --strict services/ verticals/`, full `pytest` | all rc=0; **5238 passed, 8 skipped**; `db_tests=499` (above the 400 floor, so the DB layer really ran) |

**AC-13's basis.** The full gate ran on the tree at `f506292`; `git diff f506292 c519466` is
**empty**, so the result transfers to `main` rather than being re-asserted from memory.

### Two corrections to the closeout premises

1. 🔴 **`check_ac_consistency.py` Check 3 is INERT for this PLAN** — measured, not assumed. Check 3
   scans a *single line* beginning `- [x] **AC-N ` for an italicised `*Artifacts:*` clause;
   PLAN-0109 writes `Artifact:` on the **continuation** line, unitalicised, so `_ARTIFACT_SEG`
   returns `None` and every AC is skipped as "a command-run AC". This PLAN also carries neither
   the binding sentence (`no AC box is ticked before its probe`) nor — until this commit — a
   `**Batteries:**` header, so none of Check 3's three branches could fire. The s294/s295 handoffs
   recorded AC-5's missing battery as a *Check 3* blocker; the substantive concern was right, the
   mechanical one was not. The battery was built because §8 requires the witness, not because a
   guard demanded it. The header added above arms the glob branch for any future tick.
2. **AC-5's battery is deliberately narrow.** 36 of its 38 claims are exempted (see the
   `**Batteries:**` line). AC-5's obligation is that the golden oracle stays green *through a
   written exemption rather than a weakened assertion* — that rests on the two assertions the
   exemption mechanism itself carries, and both are witnessed. Witnessing the scaffolder's own
   grammar claims belongs to the PLAN that owns that tool.

### What stays open

- **AC-14** — unticked. A live smoke on the published demo is host-state (CLAUDE.md §8) and
  needs Cray's typed go. The offline oracle (AC-8) is the gate; AC-14 would be evidence only,
  and skipping it does not block this closeout.
- The **object-synonym** options (i)/(ii)/(iii) and the other merged-but-never-typed-ruled items
  remain Cray's, and are tracked in `docs/STATUS.md`, not here.
