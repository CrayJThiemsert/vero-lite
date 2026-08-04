# PLAN-0101: The tenant-key column — `tenant_id` on every committed persistence table

**Status:** Draft
**Owner:** Claude Code (implementation) + Cray (SD rulings)
**Created:** 2026-08-04
**Related ADRs:** ADR-0035 (D7 — the tenant key, L4), ADR-0032 (demo→pilot wedge context)

> Drafted by the in-harness `plan-drafter` subagent (ADR-013 D1 phased authority)
> from the session-203 Code dispatch
> (`.claude/handoffs/session-203/2026-08-04-0746-code-plan-drafter-tenant-key-plan-dispatch.md`).
> Reviewer: Cray at PR merge (author≠reviewer per ADR-012 D4.3). Every `file:line`
> anchor below was opened on disk at draft time against `main` = `ffb8860`, except
> where explicitly marked *lead-to-verify*.

## Goal

Add the customer-organisation tenant key — `tenant_id` (Text, NOT NULL, stable slug,
default `"default"`) — to **all 21 committed persistence tables across 12 modules**,
stamped process-wide from `settings.tenant_id` (env `TENANT_ID`) exactly like
`oct_vertical` (`services/api/config.py:179-185`), discharging ADR-0035 D7
sub-items (i)–(vii) one-for-one so none is silently dropped. The key never enters
the governance pin (it must never reach the resolved-procedures hash), and this
PLAN builds **no** per-request tenancy, RLS, or tenant authn (D7(vii)). Three
architecture/governance decisions are surfaced for Cray in §Surfaced decisions —
implementation steps that depend on them are marked **BLOCKED-ON-SD** and do not
start until the ruling slots are filled.

## Context (what is settled, what this PLAN decides)

**Settled by ADR-0035 D7 (`docs/adr/0035-hosting-and-exposure-model.md:544-587`) —
restated, not re-derived:**

- `tenant_id` identifies a **customer organisation** — not a deployment, not a
  vertical instance (the vertical is already `settings.oct_vertical`).
- Value source: `settings.tenant_id` (env `TENANT_ID`), default `"default"` so every
  existing dev/test flow is untouched; the public demo deployment sets
  `TENANT_ID=demo`. Process-wide like `oct_vertical` — per-request tenancy would
  collide with the process-scoped vertical (`services/api/auth.py:82`) and the
  hand-wired executor factories (`services/api/main.py:103-156`).
- **Never part of the governance pin** — a plain settings field, excluded from the
  resolved-procedures hash.
- Scope: **every committed persistence table — 21 tables / 12 modules** (census
  re-verified at draft time: 22 `__tablename__` hits under `services/` minus the
  generator's own f-string at `services/engine/code_generator.py:638`). The two
  generated ORM modules (`services/db/models.py` — asset, site, operational_event,
  alert, recommended_action, alert_event_link; `services/db/person.py` — person)
  plus the hand-written spine: `pipeline_runs` + `step_results`
  (`services/engine/procedures/runs.py:84,122`), `schedule_states`
  (`services/engine/procedures/schedules.py:35`), `audit_log`
  (`services/db/audit_log.py:63`), `action_identity` (`services/db/identity.py:29`),
  `pm_import_row` (`services/db/pm_import.py:71`), and the eight `repair_case*`
  tables. No elimination is proposed: each of the 21 is a rows-in-one-DB table, and
  a table that omitted the key would be exactly the query-written-wrongly trap L4
  exists to prevent. (The draft explicitly considered proposing eliminations and
  found no candidate.)

**What D7 left open — the reason this PLAN exists (and why three SDs are surfaced):**

1. **D7(iv) names a seam that does not exist.** `services/db/session.py` is the
   whole persistence seam — 24 lines: `create_async_engine`, `async_sessionmaker`,
   and a FastAPI `get_session()` dependency. There is **no repository layer**, and
   `settings.tenant_id` does not exist yet (a case-insensitive grep for `tenant`
   across `services/` returns 0 matches at draft time). "Stamp at the seam" is an
   instruction to *build* a seam → **SD-1**.
2. **D7(i) collides with the generator's contract.** `emit_orm`
   (`services/engine/code_generator.py:631-646`) builds each class body as a pure
   function of the ontology YAML: the loop is
   `for obj_name, obj_def in object_types.items()` and the only column source is
   `props = obj_def.get("properties")`. A non-ontology column has no legal home in
   the current design, and three committed guards enforce the purity (§Guards
   below) → **SD-2**.
3. **D7(vi) names 2 constraints; the true census is 12** (§SD-3 table), including
   one that is invisible to a `UniqueConstraint(` grep → **SD-3**.

**Guards that break if the generator or ORMs change** (D7(i) says "update the
reproducibility guard", singular — there are three):

| # | Guard | Site | Trip condition |
|---|-------|------|----------------|
| G-a | `test_committed_person_orm_is_reproducible` | `tests/services/engine/test_shared_ontology_mechanism.py:134-141` | **byte equality** `fresh.read_text() == committed` — any emitted-column change reddens it |
| G-b | `test_core_orm_columns_match_generated_ddl` | `tests/services/engine/test_shared_ontology_mechanism.py:144-157` | line `:153` hardcodes Person's column set `{"person_id", "name", "roles"}` and ties the ORM to `emit_sql`'s DDL — **`emit_orm` cannot move without `emit_sql` moving in the same step** |
| G-c | energy DDL↔ORM parity | `tests/services/db/test_schema_parity.py` (mapper enumeration at `:34-38`) | any ORM column the emitted energy DDL lacks |

ADR-0035's own consequence note says exactly this: "the generator and its
reproducibility guard move together (D7 (i)) — a coordination cost the tenant-key
PLAN must sequence, not discover" (`0035:667-669`).

**Ordering vs PLAN-0100 (exposure):** independent — PLAN-0100 "takes no dependency
either way" and ships only a commented `# TENANT_ID=demo` line in the published env
file (`docs/plans/0100-exposure-published-demo-surface.md:220-227`). Note the
correct citation is **PLAN-0100:220-227, not the ADR**: PLAN-0100:221's phrase
"ADR-0035 mandates no ordering" is not backed by ADR text (the strings
`order`/`ordering` do not appear in a between-PLANs sense there; the ADR's only
ordering sentence, `0035:667-669`, is *intra*-PLAN). Cray typed the call at s203 to
start this PLAN without waiting on PLAN-0100's SD-1 ruling.

## Acceptance Criteria

Each AC quotes the D7 sub-item it discharges (source: `0035:570-584`), so no
sub-item can be silently dropped — the stated reason D7 enumerated them.

- [ ] **AC-1 (D7(i)):** *"teach the generator to emit the column for the committed
  ORMs and update the reproducibility guard"* — implemented per the **SD-2 ruling**.
  The regenerated `services/db/models.py` and `services/db/person.py` carry
  `tenant_id`; **all three guards** (G-a, G-b, G-c) are green in the same commit,
  and `emit_sql` moves in the same step as `emit_orm` whenever the ORM gains a
  column (G-b makes that non-optional). G-b's expected set at
  `test_shared_ontology_mechanism.py:153` is updated to include `tenant_id`.
- [ ] **AC-2 (D7(ii)):** *"add the column to the hand-written models"* — all 14
  hand-written tables (21 minus the 7 generated) across the 10 hand-written
  modules carry `tenant_id` (Text, NOT NULL): `runs.py` (2), `schedules.py` (1),
  `audit_log.py` (1), `identity.py` (1), `pm_import.py` (1), `repair_case.py` (1),
  `repair_case_closeout.py` (2), `repair_case_evidence.py` (3),
  `repair_case_run_link.py` (1), `repair_case_task.py` (1).
- [ ] **AC-3 (D7(iii)):** *"ship one Alembic revision in the measured-safe shape —
  add nullable → backfill `'default'` → NOT NULL"* — **one** revision, id `0024`
  (`down_revision "0023"`; head verified at
  `alembic/versions/0023_stored_lowest_and_monotonic_seq.py:64-65`), covering all
  21 tables, following the working template of the exact required shape at
  `0023_stored_lowest_and_monotonic_seq.py:140-168` (add nullable → backfill →
  `alter_column(..., nullable=False)`). Whether a `server_default` is retained
  after the backfill follows the SD-1 ruling (see the folded question in SD-1).
  Downgrade is symmetric.
- [ ] **AC-4 (D7(iv)):** *"stamp writes from `settings.tenant_id` at the
  session/repository seam"* — implemented per the **SD-1 ruling**. A
  `tenant_id: str` settings field (env `TENANT_ID`, default `"default"`,
  `Field(description=...)`) exists in `services/api/config.py` beside
  `oct_vertical`, is read **late-bound** at write time (so a test can exercise a
  non-default value without process restart), and **never enters the
  resolved-procedures hash** — guarded by a test asserting the governance pin /
  config hash is byte-identical with `TENANT_ID` set and unset (the
  only-when-supplied discipline: a new settings field must not change every
  existing config hash).
- [ ] **AC-5 (D7(v)):** *"add a set-equality guard test asserting every
  `__tablename__` model carries `tenant_id` (a new table cannot silently opt
  out)"* — the guard is **structurally non-vacuous**, i.e. it fails when a new
  table ships without `tenant_id` through *either* hole:
  1. **AST-walk** all of `services/` recursively for real `__tablename__` class
     attributes (the `tools/check_alembic_model_registration.py:86-110` idiom —
     `_defines_a_table` ignores text inside string templates, so the generator's
     f-string at `code_generator.py:638` does not count) → set **A** of tables on
     disk;
  2. enumerate `Base.registry.mappers` (the
     `tests/services/db/test_schema_parity.py:34-38` idiom) → set **B** of
     imported tables;
  3. assert **A == B** (an unimported model module cannot hide), then assert every
     mapper's `Table` contains a `tenant_id` column of type Text / NOT NULL.

  *Counterexample check (recorded):* a hardcoded 21-table list passes today and
  still passes when a 22nd table ships without the column — vacuous, rejected. A
  registry-only walk misses a model module no test imports — vacuous, rejected.
  The A==B pairing closes both holes: a new un-imported file grows A and breaks
  A==B; a new imported table without the column breaks step 3.
- [ ] **AC-6 (D7(vi)):** *"rule on every natural-key unique constraint that a
  tenant column re-scopes — concretely `uq_schedule_states_vertical_procedure` on
  `(vertical, procedure_id)` (`schedules.py:36-38`): under one-DB-per-deployment it
  is unaffected, but the PLAN must decide (not discover) whether `tenant_id` joins
  such keys, and `uq_step_results_seq` (`runs.py:125`) gets the same review"* —
  discharged over the **full 12-constraint census** in SD-3 (not D7's 2), with an
  explicit per-family ruling recorded in SD-3's ruling slot before Step 4 runs.
  The PLAN's census must never carry fewer than 12 entries and must include the
  column-level `unique=True` at `services/db/pm_import.py:82`, which a
  `UniqueConstraint(` grep cannot see.
- [ ] **AC-7 (D7(vii)):** *"build **no** per-request tenant resolution, no
  row-level security, no tenant-scoped authn — those are T2-full and are
  explicitly not this decision"* — verified by absence: no request-scoped tenant
  parameter, no `POLICY`/RLS DDL, no authn change lands in this PLAN's diff.
- [ ] **AC-8 (scenario test — CLAUDE.md §8, binding):** a scenario test drives the
  **real producer into the real consumer on realistic simulated data**: with
  `TENANT_ID` set to a non-default value (e.g. `"scenario-acme"`), it drives an
  existing end-to-end flow (a synthetic-event → procedure-run path that writes at
  minimum `pipeline_runs`, `step_results`, and `audit_log` through the **real**
  `async_session` factory in `services/db/session.py`) against the disposable test
  DB, then reads the rows back and asserts every written row landed with
  `tenant_id == "scenario-acme"`. **Anti-mock clause:** a test that patches or
  substitutes the session factory, the stamping seam, or the models under test
  does **not** satisfy this AC; nor does asserting only that the column exists.
- [ ] **AC-9 (adjudication record):** the three `**Ruling:**` slots in §Surfaced
  decisions are filled with Cray's typed rulings (value + date) **before** the
  steps marked BLOCKED-ON-SD begin. This PLAN stays `Status: Draft` until Complete
  (an Accepted-status PLAN becomes G1-gated and Code cannot edit its own closeout).

## Surfaced decisions (for Cray — unruled; recommendations are Code-side input only)

### SD-1 (load-bearing) — where does the write-stamp happen?

D7(iv)'s "session/repository seam" does not exist: `services/db/session.py` is 24
lines of engine + `async_sessionmaker` + `get_session()`, and there is no
repository layer. The options, with blast radius:

| Option | Mechanism | Blast radius | Bypass risk |
|---|---|---|---|
| (a) | SQLAlchemy `before_flush` (Session-level event) on the session factory: iterate `session.new`, set `tenant_id` when unset | one seam (`session.py`) | Core-level `session.execute(insert(...))` statements bypass ORM flush events — a write path not using the unit-of-work is silently unstamped |
| (b) | column-level Python `default=lambda: settings.tenant_id` on every model (centralized via the SD-2 mechanism, e.g. a shared mixin) | one definition site if SD-2 lands a mixin; otherwise 21 models | none for omitted-column inserts — SQLAlchemy column defaults apply to both ORM and Core inserts; an insert that *explicitly* passes a wrong value is not caught (same as (a)) |
| (c) | DB `server_default 'default'`, app overrides when it writes | one migration | rows written by any path that omits the column silently get `'default'` even on a `TENANT_ID=demo` deployment — the failure D7 exists to prevent, made invisible |
| (d) | explicit edits at every write site (routers + engine + adapters) | largest — every current write site, plus every future one by convention only | a future write path can silently omit the stamp; nothing structural catches it |

This is load-bearing because it decides whether the change is one seam or ~21
models, and whether a future write path can silently bypass the stamp.

**Code recommendation (not a ruling):** (b), centralized through SD-2's mechanism —
column defaults cover both ORM and Core inserts, the lambda keeps the read
late-bound (testable, per AC-4), and pairing it with **no** DB-side
`server_default` after the backfill means a hypothetical unstamped raw-SQL write
fails NOT NULL loudly instead of silently landing as `'default'`.

**Folded question (not a fourth SD — resolves with this ruling):** does the NOT
NULL column keep a `server_default='default'` after the AC-3 backfill? D7(iii) is
silent. It matters only if the chosen stamping can be bypassed: a retained
`server_default` converts "unstamped write" from a loud NOT NULL failure into a
silent `'default'` row.

**MEASURED (Step 1.4, 2026-08-04, session 203) — the lead is CONFIRMED.** On a
throwaway `vero_lite_probe` DB at head, with a positive control proving the tool
works:

| Probe | Result |
|---|---|
| baseline | `No new upgrade operations detected` (exit 0) — uncontaminated |
| **positive control** — a new column on a model, absent in DB | `FAILED: New upgrade operations detected: [('add_column', None, 'action_identity', …)]` (exit **255**) |
| **`server_default="probe-default"`** on an existing model column, absent in DB | `No new upgrade operations detected` (exit **0**) — **NOT detected** |
| corroboration — `alembic revision --autogenerate` on the same state | emitted a revision whose `upgrade()` and `downgrade()` are both `pass` — **empty** |

The positive control is what makes the negative meaningful: `alembic check` was
demonstrably able to detect drift on the same DB in the same session, and still
reported none for `server_default`. So a retained `server_default` is invisible to
**both** `alembic check` and `--autogenerate`, on top of silently absorbing an
unstamped write. All three of the recommendation's stated reasons hold.

**Ruling:** _(unruled)_

### SD-2 — how does the generator emit a non-ontology column?

D7(i) says "teach the generator" without choosing a mechanism, and `emit_orm`'s
class body is a pure function of the ontology YAML's `properties`
(`code_generator.py:631-646`). Options, costed against guards G-a/G-b/G-c:

| Option | Mechanism | Cost |
|---|---|---|
| (a) | add `tenant_id` to every ontology YAML document's `properties` | the ontology stays the single source of truth and the generator stays pure — but a process-wide infra column leaks into the **semantic layer's object shape**: Pydantic models, JSON Schema, MCP tools, TS types, and the NL-query context pack all grow a field that is not part of the domain object |
| (b) | special-case `tenant_id` inside `emit_orm` (+ `emit_sql`) as an infra column appended to every class | breaks the "pure function of `properties`" contract explicitly but keeps the ontology clean; G-a/G-b/G-c all move in the same step; the special case is one documented site in the generator |
| (c) | declare it once on the shared `services.db.base.Base` (currently a 7-line bare `DeclarativeBase`) as a mixin/mapped column all 21 models inherit | smallest diff and automatically covers future tables — but deviates from D7(i)'s **letter** ("teach the generator to *emit* the column") while honoring its intent; and the ORM gains a column the emitted DDL lacks, so G-b (`:144-157`) and G-c **still force `emit_sql` (or the guards) to move in the same step** |

**Whichever option is chosen, the ruling must state explicitly whether `emit_sql`
moves in the same step** — G-b makes that non-optional if the answer is "the ORM
gains a column the DDL lacks". Note the interplay with SD-1: option (c) here plus
option (b) there compose into a single `TenantKeyMixin` carrying both the column
and its Python-side default.

**Code recommendation (not a ruling):** (b) — it keeps `tenant_id` out of the
semantic layer's generated surfaces (option (a)'s leak is permanent and
customer-visible in MCP/TS/context-pack outputs), keeps the coordination cost
inside the generator module where `0035:667-669` says to sequence it, and unlike
(c) it satisfies D7(i)'s letter. If Cray prefers (c), the deviation from D7(i)'s
wording should be recorded in the ruling slot as an accepted re-interpretation.

**Ruling:** _(unruled)_

### SD-3 — which of the 12 unique constraints does `tenant_id` join?

D7(vi) says the PLAN must **decide, not discover** — and names 2. The full census
(all 12 sites opened on disk at draft time; #12 is column-level `unique=True`, so a
`UniqueConstraint(` grep silently returns 11):

| # | Constraint | Site | Shape |
|---|---|---|---|
| 1 | `uq_schedule_states_vertical_procedure` | `services/engine/procedures/schedules.py:37` | composite natural key `(vertical, procedure_id)` |
| 2 | `uq_step_results_seq` | `services/engine/procedures/runs.py:125` | single-col, Identity-backed `seq` |
| 3 | `uq_repair_case_closeout_seq` | `services/db/repair_case_closeout.py:99` | single-col, Identity-backed `seq` |
| 4 | `uq_repair_case_justification_seq` | `services/db/repair_case_evidence.py:138` | single-col, Identity-backed `seq` |
| 5 | `uq_repair_case_accepted_quote_seq` | `services/db/repair_case_evidence.py:218` | single-col, Identity-backed `seq` |
| 6 | `uq_repair_case_run_link_seq` | `services/db/repair_case_run_link.py:95` | single-col, Identity-backed `seq` |
| 7 | `uq_repair_case_order_number_year_seq` | `services/db/repair_case_closeout.py:75` | composite business key `(year, seq)` |
| 8 | `uq_repair_case_order_number_no` | `services/db/repair_case_closeout.py:74` | single-col business key |
| 9 | `uq_repair_case_quote_case_quote` | `services/db/repair_case_evidence.py:95` | composite `(case_id, quote_id)` — exists as a composite-FK target |
| 10 | `uq_repair_case_run_link_decision` | `services/db/repair_case_run_link.py:92-94` | composite `(case_id, run_id, step_id, outcome)` — **named** (a circulating claim that it is unnamed is wrong) |
| 11 | `uq_audit_log_prev_hash` | `services/db/audit_log.py:67` | single-col **hash-chain** key — keeps the audit chain linear by construction |
| 12 | *(unnamed, column-level)* | `services/db/pm_import.py:82` | `sa.Identity(always=True), unique=True` on `seq` — invisible to a `UniqueConstraint(` grep |

Ten are mechanical under one-DB-per-deployment (one tenant per DB → adding
`tenant_id` to any key is behaviorally a no-op today, and *widening* a unique key
only ever weakens it). Two families need their own ruling:

- **The six Identity-`seq` sites (#2–#6, #12).** The sequence generator is
  per-*table* (`GENERATED ... AS IDENTITY`), not per-tenant. Joining `tenant_id`
  to these keys would advertise per-tenant sequences that the generator does not
  provide: under any future two-tenant DB, each tenant's `seq` view would have
  gaps (the tenants interleave one shared counter), so gap-free per-tenant
  monotonicity would be a false promise. #12 additionally is `always=True` —
  re-scoping it means converting a column-level `unique=True` into a named
  composite constraint, a shape change beyond adding a column to a list.
- **`uq_audit_log_prev_hash` (#11).** Tenant-scoping an audit **hash chain** is a
  governance decision, not a schema tidy-up: `(tenant_id, prev_hash)` uniqueness
  would permit per-tenant chains, i.e. it changes what "the chain is linear by
  construction" (`audit_log.py:65-67`) means. Under one-DB-per-deployment the
  chain is single-tenant either way.

**Code recommendation (not a ruling):** `tenant_id` joins **none** of the 12 under
this PLAN. One-DB-per-deployment (D7's L4 frame, and the `0035:585-587` non-goal:
"one process never serves two tenants under this ADR") makes every re-scope a
behavioral no-op that only weakens guarantees; the Identity family cannot honor a
per-tenant reading; and the audit-chain question properly belongs to the future
multi-tenant ADR whose trigger is a second concurrently-hosted customer. Record
the "reviewed, deliberately unchanged" verdict per constraint in Step 4 so D7(vi)
is discharged by decision, not by omission.

**Ruling:** _(unruled)_

## Out of Scope

- ❌ **Per-request tenant resolution, row-level security, tenant-scoped authn** —
  D7(vii) verbatim: "those are T2-full and are explicitly not this decision".
- ❌ **Multi-tenant serving** — `0035:585-587`: one process never serves two
  tenants under this ADR; multi-tenant is a future ADR with its own trigger (a
  second concurrently-hosted customer).
- ❌ **Anything in PLAN-0100's exposure surface** — the published demo deployment,
  its env file (which ships only a commented `# TENANT_ID=demo` line,
  PLAN-0100:220-227), tunnel, gate, and notice.
- ❌ **A deployment-id label** — D7 allows one later as a separate column; not
  this PLAN.
- ❌ **Backfilling any value other than `'default'`** — no existing deployment
  carries a non-default tenant.

## Steps

### Step 0 — Adjudication record (BLOCKS Steps 2–6)

Present §Surfaced decisions to Cray; fill the three `**Ruling:**` slots with the
typed rulings (value + date). No implementation for the blocked steps until this
lands (AC-9). Step 1 is not blocked and can run in parallel.

### Step 1 — Settings field + the `alembic check` probe (no SD dependency)

1. Add `tenant_id: str` to `Settings` (`services/api/config.py`, beside
   `oct_vertical` at `:179-185`): env `TENANT_ID`, default `"default"`,
   `Field(description=...)` per the endpoint-model convention.
2. Add a commented `# TENANT_ID=default` line + one-line explanation to
   `.env.example` (vendor-default discipline, CLAUDE.md §6).
3. Guard test: the governance pin / resolved-procedures config hash is
   byte-identical with and without `TENANT_ID` set (AC-4's never-enters-the-pin
   clause, and the only-when-supplied hash discipline).
4. **Empirical probe for SD-1's folded question — DONE (session 203).** Measured on
   a throwaway `vero_lite_probe` DB at head, with a positive control: `alembic check`
   does **not** detect `server_default` drift, and `--autogenerate` emits an empty
   revision for it. Full result table in SD-1's folded question above. The dev DB
   (`vero_lite`, at `0022`) and every per-checkout test DB were left untouched; the
   probe DB was dropped.

### Step 2 — Teach the generator (BLOCKED-ON-SD-2; discharges AC-1)

Implement the SD-2 ruling in `services/engine/code_generator.py`; move `emit_sql`
in the same change whenever the ORM gains a column the DDL lacks (G-b);
regenerate `services/db/models.py` + `services/db/person.py`; update G-a
(byte-equality re-baselines via regeneration, never hand edits), G-b (`:153`
expected set), and confirm G-c green. One commit — the `0035:667-669` coordination
cost is sequenced here, not discovered.

### Step 3 — Hand-written models (BLOCKED-ON-SD-1/SD-2 shape only; discharges AC-2)

Add `tenant_id` (Text, NOT NULL, stamped per the SD-1 ruling's mechanism) to the
14 hand-written tables listed in AC-2. If SD-1/SD-2 compose into a shared mixin,
this is one import per module; otherwise 14 `mapped_column` additions.

### Step 4 — The unique-constraint verdicts (BLOCKED-ON-SD-3; discharges AC-6)

Apply the SD-3 ruling. For every one of the 12 census rows, record in the code
review (and in this PLAN's closeout) either "re-scoped: `tenant_id` joined" with
the migration change, or "reviewed, deliberately unchanged" with the one-line
reason — decide, not discover.

### Step 5 — Alembic revision `0024` (BLOCKED-ON-SD-1 for the server_default clause; discharges AC-3)

One revision, `down_revision "0023"`, all 21 tables, measured-safe shape per the
`0023_*.py:140-168` template: `add_column(nullable=True)` → backfill `'default'`
→ `alter_column(nullable=False)`; retain or drop `server_default` per the SD-1
ruling + the Step 1.4 probe result; symmetric downgrade. Run
`tools/check_alembic_model_registration.py` and `alembic check` against the
disposable test DB.

### Step 6 — The set-equality guard + scenario test (BLOCKED-ON-SD-1; discharges AC-5, AC-8)

1. Implement the AC-5 guard exactly as specified (AST-walk set A == mapper set B,
   then per-table `tenant_id` presence).
2. **Non-vacuity probe (required):** temporarily remove `tenant_id` from one
   model *and* temporarily add a table-defining file the tests do not import;
   observe the guard go RED both times; restore from a saved scratch copy (never
   `git checkout`, which can wipe the probe edit and fake a PASS). Record the RED
   observations in the PR body.
3. Implement the AC-8 scenario test through the real seam with the anti-mock
   clause honored.

### Step 7 — Closeout

Full offline gate at CI scope (`mypy services/`, full `tests/`, ruff), PR per
CLAUDE.md §7, then `git mv` to `docs/plans/done/` after merge. Status flips
Draft → Complete at closeout only.

## Verification

- All nine ACs check off; each D7 sub-item (i)–(vii) is traceable to its AC by the
  quoted text.
- The AC-5 guard's two RED probes are recorded (Step 6.2) — the guard is proven
  non-vacuous, not assumed.
- The AC-8 scenario run shows real rows in at least `pipeline_runs`,
  `step_results`, `audit_log` carrying the non-default tenant value, via the real
  session factory.
- G-a/G-b/G-c green; `alembic upgrade head` + `alembic check` clean on the
  disposable test DB; `tools/check_alembic_model_registration.py` clean.
- The governance-pin hash test (Step 1.3) proves `TENANT_ID` never reaches the
  resolved-procedures hash.
- SD ruling slots are filled with typed rulings; the 12-row constraint table
  carries a per-row verdict.
