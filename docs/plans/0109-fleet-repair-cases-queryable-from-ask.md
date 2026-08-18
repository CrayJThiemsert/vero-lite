# PLAN-0109: Fleet repair-case data queryable from Tab C (Ask) — declare, serve, and guard the lockstep

**Status:** Draft
**Owner:** both — Claude Code executes; SD-A / SD-B / SD-D are RULED (Cray, typed 2026-08-18, session 237); SD-C is Code-adopted, open to countermand; SD-E needs no ruling. **Execution is unblocked — no step waits on a ruling.**
**Created:** 2026-08-18
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

- [ ] **AC-1 — the YAML declares the ratified types.**
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
- [ ] **AC-2 — `/meta` advertises them.**
  Artifact: a test in `tests/api/` (new file `tests/api/test_meta_fleet_governance_types.py`
  or the existing meta-test module — executor's call) asserting GET `/meta` under the
  fleet vertical contains each ratified type with its declared `primary_key` and that
  `RepairCase.truck_id` carries `target: Truck`.
  Command: `uv run pytest tests/api/test_meta_fleet_governance_types.py -x 2>&1`.
  Pass read: green. **Witnessed RED (mandatory, CLAUDE.md §8):** the same test run at
  baseline (before the YAML edit) fails on the missing type name — captured in the step
  log before the edit lands.
- [ ] **AC-3 — the lockstep guard exists, reads both artifacts, and reddens in both directions.**
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
  (i) an ORM column absent from the YAML and not in the exclusion list;
  (ii) a YAML property with no ORM column;
  (iii) a **stale exclusion** — an exclusion entry naming a column the ORM no longer has;
  (iv) a declared YAML property whose type is incompatible with the column's SQL type
  (per the small SQLA→ontology type map: `Text→string`, `Numeric→float`,
  `DateTime→timestamp`, `JSONB→json`, `BigInteger→int`);
  and exits 0 on the lockstep fixture.
- [ ] **AC-4 — the guard is non-vacuous on the LIVE tree (witnessed RED, both directions).**
  Development-time probes, evidence captured in the PR body: (a) add a scratch column to
  `services/db/repair_case.py` (backup to the scratchpad first, restore from that copy —
  never from git), run `uv run python tools/check_ontology_orm_lockstep.py 2>&1` → exit 1
  naming the scratch column; (b) add a scratch property to the fleet YAML, same command
  → exit 1 naming the scratch property. Pass read: both outputs show exit 1 + the
  offender's name; the restored tree then exits 0.
- [ ] **AC-5 — the scaffolder golden oracle stays green via a written exemption, not a weakened assertion.**
  Artifact: `tests/services/engine/scaffolder/test_golden_e2e.py` —
  `_DONOR_EXTENSION_OBJECTS` extended per Step 1 (recommended: derive the exemption for
  DB-backed types from the guard's mapping module so one source of truth feeds both,
  with the existing "exemption naming a missing object fails" tripwire retained).
  Command: `uv run pytest tests/services/engine/scaffolder/ -x 2>&1`.
  Pass read: green. **Witnessed RED:** the golden set-equality test run after the YAML
  edit and before the exemption fails naming the new types — captured in the step log.

### Phase 2 — Serve the data through the adapter seam (SD-A RULED (b) — the session-owning fleet adapter)

- [ ] **AC-6 — the fleet adapter serves DB-backed types with the SD-D-RULED projection.**
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
  excluded as internal). **Presence controls (ruled IN):** the seeded `description`,
  `vendor` and `reason` values round-trip **verbatim** into the projected dicts.
  **Absence controls (ruled OUT):** `note`, `photos`, `attachment` appear in **no**
  returned dict — and the seed's non-null values are the positive control making that
  absence a real exclusion, not a vacuous one (CLAUDE.md §8: an absence needs a positive
  control); datetimes are ISO-8601 strings; `amount_thb` is a float.
- [ ] **AC-7 — the seven synthetic types are untouched.**
  Command: `uv run pytest tests/verticals/fleet_maintenance/ 2>&1` (full directory).
  Pass read: every pre-existing test green with zero modifications to their assertions;
  `health_check()` still reports the seven synthetic object counts (it may *add* a DB
  status field; it may not change existing keys).
- [ ] **AC-8 — the scenario test (CLAUDE.md §8, binding): real producer into real consumer.**
  Artifact: `tests/verticals/fleet_maintenance/test_ask_repair_case_scenario.py`.
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
  `source ids == the two case_ids the POSTs returned` (proving the rows flowed, not a
  fixture); a second scenario case filters by `truck_id` and matches only that truck's
  case. **Non-vacuity probe with a named changing output:** opening a third case changes
  the asserted count read from 2 → 3 (asserted in-test by a second act+ask round);
  severing the adapter's DB branch (dev-time scratch mutation, restored from the
  scratchpad) flips `grounded` to False — witnessed once during Step 4.
  ⚠️ Like the PLAN-0104 scenario, this makes **no claim the live model emits the
  translation** — that claim belongs to the (Cray-gated) live smoke in AC-14 only.
- [ ] **AC-9 — honest degrade without a database.**
  Artifact: an offline test in the same module: adapter constructed with a session
  factory pointing at an unreachable URL → `answer_question` returns the ungrounded
  "couldn't retrieve" answer (`nl_query.py:1363-1367` path), never an invented count.
  Command: same pytest file, no DB required for this case.
  Pass read: `grounded is False` and the canned honest-degrade phrase, not a number.
- [ ] **AC-10 — the projection is an ALLOWLIST, single-sourced and leak-resistant.**
  Artifact: one shared module (recommended:
  `verticals/fleet_maintenance/data_adapter/db_projection.py`) holding the
  type↔table mapping and the exclusion entries `{column: reason}` — reasons carry
  provenance (`ruled-out (Cray)` for `note`; `payload-not-text (Code, reversible)` for
  `photos`/`attachment`; `internal` for `seq`); **both** the adapter's projection and
  `tools/check_ontology_orm_lockstep.py` import it.
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

- [ ] **AC-11 — the compliance record is corrected in the same PR (SD-D consequence 1 — mandatory, its own AC, not a Step footnote).**
  Artifacts: `docs/compliance/ropa-change-statement-fleet.md` **and** the module
  docstring of `services/db/repair_case_retention.py`.
  Shipping `description` into Ask makes recorded sentences **false at the moment of
  merge**, so this AC lands in the same PR as the Phase 2 serving change. The passages
  that go stale, named: (a) the retention docstring's claim that ADR-0035 D6's regime
  "does not reach case text (`docs/compliance/ropa-change-statement-fleet.md` §4(a))"
  (`repair_case_retention.py:7-13`); (b) the ROPA's §4(a)-anchored scope claim
  ("defined per LLM request and does not reach case text"); (c) the ROPA's own two
  tripwire sentences — "goes **stale as stated** the day fleet…" (§4 scope facts) and
  "The day any real case text enters this surface the ruling is stale" — §239's day
  **is this PR**. Each must be **corrected to state the new truth** (case
  `description`, quote `vendor`, accepted-quote `reason` now reach the `/query`
  translate + phrase prompts and the D6 prompt log), never merely appended to.
  Command: `grep -n "does not reach case text" services/db/repair_case_retention.py docs/compliance/ropa-change-statement-fleet.md 2>&1`
  (output to a file). Pass read (fixed): **zero** remaining occurrences of the
  now-false sentence in either artifact, and the amended ROPA names PLAN-0109, the
  ruled IN-set, the new surface, and its bounds (the 90-day case sweep; D6 prompt-log
  rotation; the `case-persist-notice`).
  **Why no existing guard closes this:** the retention module's own import-absence
  guard — `test_ac9_the_module_does_not_inherit_the_prompt_log_regime`
  (`tests/services/db/test_case_retention.py:327,:343`) — asserts only that the
  retention module **imports** nothing from `prompt_log`. This change adds no import,
  so that guard **cannot redden** on it: the coupling is data-flow (case text flowing
  *into* prompt-log content), and the instrument is aimed one field to the left. Hence
  a mandatory AC with its own grep read instead of trust in an existing green.

### Phase 3 — Evidence + closure

- [ ] **AC-12 — SD-E confirmed on disk: the YAML edit changes zero committed files via codegen.**
  Command: run the engine's generate CLI for fleet (`uv run vero-lite ...` — the
  console-script form, never `python -m`), then `git status --porcelain 2>&1` written to
  a file. Pass read (fixed): empty output — every regenerated artifact lands under
  gitignored `verticals/fleet_maintenance/generated/` (F8). The changed gitignored set
  (models/schema/mcp/types/orm/context-pack) is listed in the step log for the record.
- [ ] **AC-13 — full offline gate at CI scope.**
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
Property sets = ORM columns minus the ruled exclusions (`photos`, `note`, `attachment`,
plus internal `seq`) — authored by reading the model classes (F7), not from memory. The
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
property set, the ruled-OUT columns (`photos`, `note`, `attachment`, `seq`) never
emitted, datetimes to ISO strings, `Decimal` to float — the procurement-datetime
lesson.
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

### Step 5 — Correct the compliance record (AC-11; lands in the Phase 2 PR)

Amend `docs/compliance/ropa-change-statement-fleet.md`: correct the §4(a)-anchored
scope claim and resolve the ROPA's two self-declared tripwires ("goes **stale as
stated** the day fleet…"; "The day any real case text enters this surface the ruling is
stale") by recording the day — this PR, PLAN-0109 — the ruled IN-set
(`description` / `vendor` / `reason`), the new surface (the `/query` translate + phrase
prompts and the ADR-0035 D6 prompt log), and its bounds (90-day case sweep on
`opened_at`; D6's prompt-log rotation; the public `case-persist-notice`). Rewrite the
retention-module docstring sentence (`repair_case_retention.py:7-13`) so it states the
new truth instead of the now-false one. State plainly in the diff that the existing
import-absence guard (`test_ac9_the_module_does_not_inherit_the_prompt_log_regime`,
`tests/services/db/test_case_retention.py:327`) cannot see this coupling — it guards
imports, and this change adds none (AC-11's rationale).
**Non-vacuity probe / changing output:** the AC-11 grep's match set changes from
occurrences in **both** artifacts (baseline, witnessed) to **zero** — the corrected
files are the output that changes.

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
values enter the **LLM prompt** (translate/phrase) and the ADR-0035 D6 **prompt log**.
F13: the visitor-typed set is `description`, `photos`, `note`, `attachment`, `reason`,
plus the short string `vendor`. The drafter recommended excluding all free text; **Cray
ruled more free text IN.**

**RULED IN** (projected, queryable, reaching the LLM prompt and the D6 prompt log):
`RepairCase.description`, `RepairCaseQuote.vendor`, `RepairCaseAcceptedQuote.reason`.
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
1. **The compliance record goes false at merge — AC-11, mandatory, same PR.**
   `services/db/repair_case_retention.py:7-13` states in its own docstring that the D6
   regime "does not reach case text (`docs/compliance/ropa-change-statement-fleet.md`
   §4(a))" — shipping `description` into Ask makes that sentence FALSE the moment the
   Phase 2 PR merges. The ROPA's own tripwires already call this out: "goes **stale as
   stated** the day fleet…" and "The day any real case text enters this surface the
   ruling is stale" — that day is this PR. AC-11 names each stale passage and requires
   correction, not appendage.
2. **No existing guard sees this coupling.** The retention module deliberately imports
   nothing from `prompt_log`, and PLAN-0105's AC-9 guard
   (`test_ac9_the_module_does_not_inherit_the_prompt_log_regime`,
   `tests/services/db/test_case_retention.py:327,:343`) enforces exactly that
   **import** absence — verified on disk: it scans imported module names for
   `prompt_log`. This change adds no import, so the guard **cannot redden**; the
   coupling is data-flow (case text flowing *into* prompt-log content), one field to
   the left of where the instrument is aimed. Priced accordingly: AC-11 is a manual
   correction with its own grep-based pass read, not a trusted green.
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
translate/phrase prompts and can be echoed inside a grounded answer. What bounds it
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
5. **Compliance true at merge:** zero remaining occurrences of "does not reach case
   text" across the retention docstring and the ROPA statement, the ROPA's own
   tripwire sentences resolved with this PR named, landed in the same PR as the
   serving change (AC-11).
6. **Priced and clean:** zero committed-file drift from codegen (AC-12), full CI-scope
   offline gate green (AC-13), and — only with Cray's typed go — one live smoke as
   evidence, never as the gate (AC-14).
