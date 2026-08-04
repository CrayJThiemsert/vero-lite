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
PLAN builds **no** per-request tenancy, RLS, or tenant authn (D7(vii)).

**All three surfaced decisions were ruled by Cray on 2026-08-04 (session 203), so every
step is unblocked** — SD-1 = a column-level Python default with **no** `server_default`;
SD-2 = a generator special-case that keeps the ontology clean, **plus** the tenant exposed
as deployment metadata on `/meta` (new **AC-10**); SD-3 = `tenant_id` joins **all twelve**
unique constraints, against the Code recommendation and with three riders Step 4 must
carry. Step 1 shipped in session 203 (#1022).

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
- [x] **AC-9 (adjudication record):** the three `**Ruling:**` slots in §Surfaced
  decisions are filled with Cray's typed rulings (value + date) **before** the
  steps marked BLOCKED-ON-SD begin. This PLAN stays `Status: Draft` until Complete
  (an Accepted-status PLAN becomes G1-gated and Code cannot edit its own closeout).
  **CLOSED 2026-08-04 (session 203)** — all three ruled; Steps 2–6 are unblocked.
- [ ] **AC-10 (deployment metadata — added by SD-2's ruling):** `OntologyMeta`
  (`services/engine/ontology_meta.py`) carries `tenant_id`, served by the existing
  `GET /meta` route (`services/api/routers/actions.py`), so a reader can tell which
  customer a deployment serves **without** the key entering any generated semantic
  surface. Guarded by a test asserting the field is present and reflects
  `settings.tenant_id`, plus a **negative** assertion that no generated artifact
  under `ontology/generated/` or `verticals/*/generated/` mentions `tenant_id` —
  the leak this AC exists to prevent is the one option (a) would have caused, so
  the guard has to watch for it rather than trust the choice.

## Surfaced decisions — ALL THREE RULED by Cray, 2026-08-04 (session 203)

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

**Ruling: (b) — a column-level Python `default=lambda: settings.tenant_id`, centralized
through SD-2's mechanism, and NO retained `server_default`.** Cray, typed 2026-08-04
(session 203). Rationale as recommended: column defaults apply to both ORM and Core
inserts, so the option-(a) bypass (a Core `session.execute(insert(...))` skipping the
flush event) does not exist; the lambda keeps the read late-bound and therefore
testable; and dropping `server_default` means a hypothetical unstamped raw-SQL write
fails NOT NULL **loudly** rather than landing silently as `'default'` — which the Step-1.4
measurement shows no tooling would catch, since neither `alembic check` nor
`--autogenerate` sees `server_default` drift. The folded question is thereby answered:
**no `server_default` after the backfill.**

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

**Ruling: (b) — special-case `tenant_id` inside `emit_orm` (+ `emit_sql`, which moves in
the same step), the ontology staying clean — PLUS surface the tenant as DEPLOYMENT
METADATA on `/meta`.** Cray, typed 2026-08-04 (session 203).

Cray asked whether the ontology should carry `tenant_id` too, so that many verticals and
many customers do not become confusing. **The answer is no, and the reasoning runs the
opposite way to the intuition:** `tenant_id` is not a property of a domain object — an
`Asset` has the same shape for every customer, which is the entire reason one ontology
serves them all. The tenant is a property of the *deployment*. Putting it in the ontology
would leak an infrastructure field into all five generated semantic surfaces, and two of
those are read by a model: the **MCP tool definitions** and the **NL-query context pack**,
where `tenant_id` would become domain vocabulary the LLM can reason and filter on. ADR-0035
has effectively already ruled this — it states the key must never enter the
resolved-procedures hash, i.e. it is *not* part of the semantic/governance surface.

**But the underlying concern is legitimate, and it is answered at the right layer.** This
PLAN therefore also adds `tenant_id` to `OntologyMeta` (`services/engine/ontology_meta.py`),
served by the existing `GET /meta` route (`services/api/routers/actions.py`) that the UI
already re-skins from — so "which customer is this deployment serving?" is answerable
without touching object shape. This is a read of a process-wide setting, **not** per-request
tenant resolution, so it does not breach D7(vii). Scope addition tracked as **AC-10**.

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

**Ruling: `tenant_id` joins ALL TWELVE.** Cray, typed 2026-08-04 (session 203) —
**against** the Code recommendation above, which is retained verbatim so the reasoning
that was weighed and set aside stays legible. Cray's basis: make the schema
forward-compatible with a second concurrently-hosted customer now, rather than pay a
migration later on tables that will by then hold production rows.

**Three consequences Step 4 must handle, not discover** — each grounded on disk at ruling
time, not inferred:

1. **#12 needs a shape change, not a list edit.** `services/db/pm_import.py`'s `seq` is a
   column-level `unique=True`, so joining `tenant_id` means replacing it with a *named*
   composite `UniqueConstraint` in `__table_args__`. Pick the name explicitly — an
   unnamed composite is what made this site invisible to the census in the first place.
2. **The Identity-`seq` family gains a promise the sequence generator does not keep.**
   `GENERATED ... AS IDENTITY` counters are per-*table*, so under any future shared DB each
   tenant's `seq` view is gap-ful (tenants interleave one counter). `(tenant_id, seq)`
   uniqueness is still *correct*; what it must not do is invite a reader to assume
   gap-free per-tenant monotonicity. State that where the constraint is defined.
3. **`uq_audit_log_prev_hash` is load-bearing beyond uniqueness, and two call sites are
   global.** `services/db/audit_log.py` documents the UNIQUE index as what makes the chain
   "linear by construction", and its append path says the concurrency race with "nothing to
   lock" is *closed by that constraint*. Widening it to `(tenant_id, prev_hash)` keeps that
   property **per tenant**, which is equivalent today under one DB per deployment — but the
   head lookup in `services/api/routers/audit.py` and `verify_chain`'s walk are **not**
   tenant-scoped. They stay correct while one tenant occupies a database and would read a
   second tenant's rows as a chain break. Step 4 records this as a known, bounded
   consequence; scoping those reads is **out of scope here** (it is per-tenant query
   behaviour, adjacent to D7(vii)'s non-goals) and belongs to the multi-tenant ADR whose
   trigger is a second concurrently-hosted customer. The `audit_log.py` module docstring's
   "linear by construction" wording must be amended in the same step, or it becomes a stale
   claim the moment the constraint widens.

Step 4 still records a per-row verdict for all twelve, per D7(vi)'s decide-not-discover
requirement — the verdict is now "re-scoped: `tenant_id` joined" for each, with the three
riders above attached to their rows.

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

### Step 0 — Adjudication record — **DONE (session 203, 2026-08-04)**

All three `**Ruling:**` slots filled with Cray's typed rulings. **Steps 2–6 are
unblocked.** Summary, with the full reasoning in §Surfaced decisions:

| SD | Ruling | Note |
|---|---|---|
| SD-1 | **(b)** column `default=lambda: settings.tenant_id`, **no** `server_default` | as recommended; the Step-1.4 measurement is its evidence |
| SD-2 | **(b)** generator special-case (`emit_orm` + `emit_sql`), ontology stays clean, **plus** `tenant_id` on `/meta` | the `/meta` half is new scope → **AC-10** |
| SD-3 | **join ALL TWELVE** | **against** the Code recommendation; three riders attached, see SD-3 |

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

### Step 2 — Teach the generator (UNBLOCKED by SD-2; discharges AC-1 + AC-10)

Special-case `tenant_id` in `services/engine/code_generator.py` per SD-2's ruling —
`emit_orm` **and** `emit_sql` move in the same change (G-b makes that non-optional the
moment the ORM gains a column the DDL lacks). Regenerate `services/db/models.py` +
`services/db/person.py`; update G-a (byte-equality re-baselines via regeneration, never
hand edits), G-b's expected column set, and confirm G-c green. One commit — the
`0035:667-669` coordination cost is sequenced here, not discovered.

Also in this step, per SD-2's ruling: add `tenant_id` to `OntologyMeta` and ship AC-10's
guard, **including its negative half** — no generated artifact under
`ontology/generated/` or `verticals/*/generated/` may mention `tenant_id`. That guard is
what keeps the ontology clean by construction rather than by intention.

### Step 3 — Hand-written models (UNBLOCKED; discharges AC-2)

Add `tenant_id` (Text, NOT NULL) to the 14 hand-written tables listed in AC-2, carrying
SD-1's `default=lambda: settings.tenant_id`. SD-1(b) + SD-2(b) compose into a single
`TenantKeyMixin` holding both the column and its Python-side default, so this is one
import per module rather than 14 `mapped_column` additions — and a future table that
forgets the mixin is caught by AC-5's set-equality guard, not by review.

### Step 4 — The unique-constraint verdicts (UNBLOCKED by SD-3; discharges AC-6)

**SD-3 ruled: `tenant_id` joins all twelve.** Record a per-row verdict for each of the 12
census rows in the code review and this PLAN's closeout — "re-scoped: `tenant_id` joined"
plus the migration change — so D7(vi) is discharged by decision, not omission.

Handle SD-3's three riders here rather than discovering them:

1. **#12 (`services/db/pm_import.py`)** — replace the column-level `unique=True` with a
   **named** composite `UniqueConstraint` in `__table_args__`. Name it explicitly; the
   unnamed column-level form is exactly what hid this site from the original census.
2. **The Identity-`seq` family** — note at each constraint that the counter is
   per-*table*, so `(tenant_id, seq)` uniqueness must not be read as a promise of
   gap-free per-tenant monotonicity.
3. **`uq_audit_log_prev_hash`** — widening it preserves the "closed by the UNIQUE
   constraint" concurrency property **per tenant**, equivalent today under one DB per
   deployment. Record that the head lookup in `services/api/routers/audit.py` and
   `verify_chain`'s walk remain **global** and are correct only while one tenant occupies
   a database — scoping them is out of scope here and belongs to the multi-tenant ADR.
   **Amend `services/db/audit_log.py`'s "linear by construction" docstring in this same
   step**, or the widening silently makes it a false claim.

### Step 5 — Alembic revision `0024` (UNBLOCKED; discharges AC-3)

One revision, `down_revision "0023"`, all 21 tables, measured-safe shape per the
`0023_*.py:140-168` template: `add_column(nullable=True)` → backfill `'default'`
→ `alter_column(nullable=False)`; symmetric downgrade. **Per SD-1's ruling, NO
`server_default` is retained** — an unstamped write must fail NOT NULL loudly, and the
Step-1.4 measurement is why: neither `alembic check` nor `--autogenerate` would ever
report a `server_default` that drifted back in.

This revision also carries SD-3's twelve constraint re-scopes, including #12's
column-level → named-composite shape change. Run
`tools/check_alembic_model_registration.py` and `alembic check` against the disposable
test DB. **Note the blind spot both tools share:** they will confirm the columns and the
`Identity` columns, and say nothing about `server_default` either way — so "no
`server_default`" is a claim the tooling cannot check for you. Assert it directly.

### Step 6 — The set-equality guard + scenario test (UNBLOCKED; discharges AC-5, AC-8)

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
