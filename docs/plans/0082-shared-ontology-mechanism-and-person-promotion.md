# PLAN-0082: The shared-ontology mechanism + `Person` promotion (the PLAN-0081 dependency)

**Status:** Draft — **SD round CLOSED (Cray, s148, typed AskUserQuestion):
SD-F=(a) · SD-G=(b)+(c) · SD-H=(a) · SD-I=(b — override, see record) ·
SD-K(i)=(a) · SD-K(ii)=(a) · OQ-1=ONE new shared-ontology ADR.** All seven
are ratified inputs — recorded, not re-litigated. Ready to execute once the
Step-1 ADR (next free number — likely ADR-0033) + its two pointer-note
edits merge (AC-1). One NEW open question (OQ-2 — the `person`-table
population story SD-I=(b) creates) is surfaced for build-time resolution;
it does not block the ADR dispatch.
**Owner:** Claude Code (execution) · Cray (SD adjudication + ratification)
**Created:** 2026-07-18
**Related ADRs:** **the NEW shared-ontology ADR (PRIMARY — OQ-1 RESOLVED,
Cray s148: ONE new ADR codifies the construct; next free number — highest
on disk is ADR-0032, 0014 is WITHDRAWN, so likely ADR-0033 — authored by a
SEPARATE plan-drafter dispatch; it must merge BEFORE any grammar/codegen/
ORM change ships — CLAUDE.md §8, AC-1)**, ADR-0008 (its per-vertical
grammar is EXTENDED by the new ADR, NOT amended in place; ADR-0008 gets a
pointer note — a G1 Accepted-body edit authored WITH the new ADR, ratified
one-pass — recording that the shared-ontology construct is codified there;
its `:79-80` `shared property` Rule-of-Three deferral is consciously
re-argued in the new ADR), ADR-0026 (gets the matching pointer/supersession
note: its `:89` "no new generation surface / codegen path untouched"
consequence is SUPERSEDED by SD-E=(b-ii) and its OQ-6 per-vertical deferral
`:116` is CLOSED by this extraction — both recorded in the note pointing to
the new ADR; its `:95` ontology-layer framing + `:157` "ontology object
(ADR-0008 grammar)" Implementation Note are what SD-E=(b-ii) honors),
ADR-006 (D4 Rule of Three — satisfied for the
`Person` PATTERN at N=3; consciously in TENSION for the mechanism at N=1,
see Out of Scope), ADR-0024 (D3 governed ≠ generated — the H-partition
nuance in Step 1), ADR-0031 (D4.2 own-PLAN rule — the SPLIT's cited
precedent), ADR-0032 (D6 honest-cost discipline). Related PLANs:
**PLAN-0081 (the parent — it DEPENDS on this PLAN; its Step 9 shrinks to
the `building_materials` migration once this PLAN ships)**, PLAN-0074/0075
(the shipped SoD + tier-authority machinery whose behavior this PLAN must
preserve), PLAN-0031 B1 (the committed-ORM Option-B precedent AC-3/AC-7
reuse; SD-I=(b) forces its deferred B1-DP-1 second-ORM-layout follow-up —
Step 4).

> **Mandate.** This PLAN exists by **Cray's SD-J = SPLIT ratification
> (s147, typed AskUserQuestion)** on PLAN-0081's highest-order structural
> fork: the SD-E=(b-ii) shared-ontology work is SPLIT out of the hero build
> into this dedicated dependency PLAN (`0081:760-782` — "a dedicated
> shared-ontology PLAN … that PLAN-0081 depends on; [PLAN-0081's] Step 9
> shrinks to the migration"). **Two parent decisions are RESOLVED INPUTS
> here, not re-litigated:** **SD-E = (b-ii)** — promote `Person` to an
> ADR-0008 ontology `object_type` at a NEW shared/core ontology home,
> inventing the shared-ontology mechanism (Cray, s147; full record incl.
> rejected alternatives (a)/(b-i)/(c): `0081:643-683`) — and **SD-J =
> SPLIT** itself. *Fold note (flagged, not fixed here): on-disk PLAN-0081
> still lists SD-J as open (`0081:15-18,760-782`) — the ratification
> postdates its last fold. Classified `superseded by new info`, not `was an
> error`; PLAN-0081 needs its own fold (a separate drafter pass) to record
> SD-J=SPLIT, shrink Step 9, and re-point its AC-7 — outside this PLAN's
> write scope.*
>
> *Fold (s148): Cray's SD-round rulings recorded — SD-F/G/H/I, SD-K(i)/(ii),
> and OQ-1 are now RESOLVED inputs (typed AskUserQuestion picks = ratified;
> see Surfaced Decisions for the full record). SD-I=(b) is an OVERRIDE of
> this drafter's (a) recommendation — classified `superseded by new info`
> (the PLAN-0081 SD-D precedent), NOT `was an error` — and its scope
> consequence (committed ORM + `person` DB table + Alembic migration) is
> threaded through Goal, Out of Scope, AC-3/AC-7, Step 4, Verification, and
> the NEW OQ-2 below.*

## Goal

Build the **shared/core ontology mechanism** — a shared ontology home +
reserved namespace (SD-F) and cross-vertical discovery/resolution in the
generator + CLI (SD-G) — and use it to **promote `Person` from a spec-layer
convenience to an ADR-0008 ontology `object_type` generated at that shared
home**, reconciling the shipped spec-layer `Person`
(`services/engine/procedures/spec.py:1359`) down to **exactly one
authoritative type** (SD-H=(a): delete + re-export), placing the generated
module at a COMMITTED home per precedent AND — per **Cray's SD-I=(b)
override** — shipping a committed shared-`Person` ORM plus a `person` DB
table with its Alembic migration (the repo's SECOND committed generated
ORM and its first ontology-object migration outside the energy schema —
the honest scope cost, stated plainly), and **migrating the two
EXISTING principal-bearing verticals (`procurement`, `supply_chain`) onto
the shared `Person`** with governance behavior preserved (SD-K(i)=(a)) —
all behind **ONE preceding NEW shared-ontology ADR** (OQ-1 resolved, Cray
s148; authored by a SEPARATE dispatch — no ADR is authored in
this PLAN). End state: PLAN-0081's hero build only has to land
`building_materials` on an already-shipped, already-proven shared `Person`
(its Step 9 residue). Honest cost, stated plainly (ADR-0032 D6): this is a
**new generation surface** — the change PLAN-0081 called "bigger than the
hero build itself" — consciously chosen by Cray with exactly that framing
in view (SD-E record, `0081:655-660`).

## Current state (verified on `main` fa4f6c6, 2026-07-18, by this drafter)

**The grounded crux (every anchor re-read from disk this session):** the
shipped codegen model is **strictly per-vertical**, and **no shared/
cross-vertical ontology home exists** — SD-E=(b-ii) INVENTS the mechanism;
this PLAN builds that invention.

*Fold re-verification (s148, `main` db4d866, this drafter): the SD-I=(b)
and OQ-1 load-bearing anchors were re-read from disk this fold —
`_ORM_COMMITTED_DEST = {"energy": Path("services/db/models.py")}` is still
energy-only (`code_generator.py:736-742`, including the B1-DP-1 comment
`:740-741`: "How a 2nd vertical's ORM is laid out … is a deferred
Rule-of-Three decision" — SD-I=(b) now forces that call, Step 4); the
Alembic chain is 11 revisions (`alembic.ini:6` → `alembic/versions/`) and
ontology-OBJECT tables exist ONLY in `0001_initial_energy_schema.py`
(site/alert/asset/operational_event/recommended_action/alert_event_link) —
revisions 0002–0011 create engine-runtime tables (pipeline_runs/
step_results, action_identity, audit_log, schedule_states) or alter energy
columns; NO `person` table exists anywhere (DB identity today = `person_id`
STRINGS on `action_identity`, `services/db/identity.py:20-34` — a
hand-authored engine-governance table, not a roster); and the highest ADR
on disk is ADR-0032 (0014 WITHDRAWN), so the new shared-ontology ADR takes
the next free number — likely ADR-0033. All other anchors in this section
are carried from the s147 draft pass (verified then on `main` fa4f6c6)
unless marked otherwise.*

- `generate_all(yaml_path, output_dir)` loads exactly ONE ontology YAML per
  run (`services/engine/code_generator.py:745-763`) over a single-doc
  `load_doc` (`:71-76`) — no import/include/merge logic exists.
- A `ref`-typed property resolves ONLY within that same doc
  (`object_types[target]` — `:163` SQL emitter, `:435` ORM emitter); a
  cross-vertical `ref` today raises `KeyError`.
- The CLI hard-wires `verticals/{vertical}/ontology/{vertical}_v0.yaml`
  (`services/engine/cli.py:22-23`; `generate` `:37-52` validates then
  emits; console script `vero-lite`, `pyproject.toml:44-45`).
- Seven emitters land under `verticals/<v>/generated/`, which is gitignored
  (`.gitignore:41-42`; ADR-0008 `:101`) — EXCEPT the runtime-imported ORM,
  which generates to a COMMITTED path when registered
  (`_ORM_COMMITTED_DEST = {"energy": Path("services/db/models.py")}`,
  `code_generator.py:736-742` — the PLAN-0031 B1 Option-B precedent AC-3
  reuses).
- The ADR-0008 grammar is per-vertical BY CONSTRUCTION:
  `namespace: <vertical_name>` (D2, `0008:37-63`, the literal at `:41`); D5
  puts every artifact under `verticals/<name>/generated/` (`:89-101`); and
  ADR-0008's own deferral list puts `shared property`-class constructs
  behind a Rule-of-Three trigger (`:79-80` — "Add when 3+ verticals request
  them"; the amendment must consciously re-argue this).
- `Person` is **spec-layer-only**: `class Person`
  (`spec.py:1359-1378` — docstring: "Lives in the procedures spec layer"),
  consumed by `VerticalProcedures.principals` (`:1660-1664`; class at
  `:1649`), the identity validators (`:1677-1694`), the parse (`:1789`),
  `check_principal_sod` (`services/engine/procedures/principal_sod.py:118`),
  and `_principal_index(vertical) -> dict[str, Person]`
  (`services/api/auth.py:49`). **Zero** `Person`/`principal` hits in any
  `verticals/*/ontology/*_v0.yaml` (grep-verified this session, empty
  result) and `code_generator.py` has no `Person` awareness.
- **NEW grounded finding #1 — the emitter-capability gap is CONCRETE, not
  hypothetical:** the ADR-0008 D3 type table (`0008:65-77`) has **no
  collection/array type** (only `string/int/float/bool/timestamp/date/
  enum/json/ref`), but the shipped `Person` carries `roles:
  frozenset[RoleId]` with `min_length=1` (`spec.py:1374-1378`) plus
  `extra="forbid"` (`:1367`) — load-bearing constraints (a roles-less
  Person breaks the OQ-1=(a) role→principal resolution). The ADR-0008
  amendment must therefore extend the TYPE SYSTEM (or codify an equivalent
  constraint construct) before the promotion is expressible at all; a
  `json`-typed `roles` would silently drop the typing. This sharpens
  PLAN-0081 SD-H's emitter-capability note (`0081:736-740`) into a named
  amendment obligation (Step 1).
- **NEW grounded finding #2 — the namespace reservation is semantic, not
  syntactic:** L1 validation constrains `namespace` only to
  `^[a-z][a-z0-9_]*$` (`services/engine/ontology_schema.json:15-18`), so a
  shared token (e.g. `core`) already PASSES L1 syntactically; nothing
  hard-binds namespace == vertical directory except the CLI path
  convention (`cli.py:22-23`) + ADR-0008 D2 prose. The SD-F reservation is
  therefore a D2-prose + validator/CLI matter the amendment codifies — not
  a JSON-Schema rewrite.
- The identity type aliases are spec-layer strings: `RoleId = str`
  (`spec.py:833`), `PersonId = str` (`:839`), `ServicePrincipalId = str`
  (`:845`). `PrincipalAlias` (`:1340-1356`, `members: frozenset[PersonId]`
  min 2) and `ServicePrincipal` (`:1381-1397`, deliberately NO `roles`)
  sit beside `Person` and are NOT promoted (Out of Scope).
- The OQ-6 marker (`tests/services/engine/procedures/
  test_principal_identity_retrigger.py`) is green at N=2: `_RETRIGGER_N =
  3` (`:43`), baseline `["procurement", "supply_chain"]` (`:49`), the
  baseline-equality assert (`:71`) and the N<3 re-trigger assert (`:80`).
  Its counter reads per-vertical `procedures.yaml` `principals:` blocks
  (roster DATA — which stays per-vertical demo data under this PLAN), so
  **this PLAN alone keeps both asserts green**; the marker question is
  about its MEANING, not CI (SD-K(ii)).
- The migration touch-points (verified): procurement's roster
  (`verticals/procurement/procedures.yaml:64` `principals:`, `:93`
  `service_principals:`) **plus its second roster source** — `person.csv`
  via `load_fastenal_principals`
  (`verticals/procurement/hero_demo/procedure.py:70-76`, constructing
  spec-layer `Person`s); supply_chain's roster
  (`verticals/supply_chain/procedures.yaml:63-84`) + factory wiring
  (`verticals/supply_chain/procedures_factory.py:272` reads
  `spec.principals`, `:295` passes `principals=` into
  `GovernanceActionExecutor`). *Carried from PLAN-0081, NOT independently
  re-verified here: the `hero_demo/run.py` wiring lines
  (`:347-358,:380-382,:542-550,:666,:738-749` — `0081:840-841`); Code
  spot-checks at build time.*
- Newest-ADR sweep (precedence, CLAUDE.md §1): highest Accepted ADR is
  ADR-0032 (strategic frame) — no later ADR touches the shared-ontology
  question; ADR-0008 + ADR-0026 remain the operative decisions this PLAN's
  ADR dependency amends.

## Dependency & scope boundary vs PLAN-0081

- **PLAN-0081 DEPENDS ON this PLAN.** The hero build's Step 9 shrinks to
  migrating **only `building_materials`** onto the shared `Person` this
  PLAN ships (plus its 9d ADR-flag residue). PLAN-0081 must not merge its
  principal-bearing YAML before this PLAN's end state lands — otherwise
  the OQ-6 marker fires (N=3) against a per-vertical shape this PLAN
  exists to retire.
- **This PLAN migrates the two EXISTING principal-bearing verticals**
  (`procurement`, `supply_chain` — PLAN-0081 AC-11's targets,
  `0081:273-285`), proving the mechanism end-to-end on shipped,
  test-covered consumers BEFORE the hero build stacks on top. That
  boundary is SD-K(i) — **RESOLVED (a) by Cray (s148)**: procurement +
  supply_chain migrate HERE; `building_materials` stays PLAN-0081 Step 9.
- Rosters remain **per-vertical, per-org demo DATA** (PLAN-0081 Out of
  Scope, `0081:363-368`): what unifies is the `Person` TYPE (one generated
  definition), procurement's dual roster SOURCE (one canonical remains),
  and the loading/index seam — never a cross-vertical roster merge and
  never cross-vertical identity semantics (ADR-0026 OQ-3=(c) untouched).
  The SD-I=(b) `person` TABLE does not change this: it is a typed STORE,
  not a cross-vertical identity merge — whether/how per-vertical roster
  DATA seeds it is OQ-2, and no seeding shape may introduce cross-vertical
  identity semantics.

## Acceptance Criteria

Renumbered into this PLAN's own scheme; AC-1..AC-6 each map from a
PLAN-0081 AC almost verbatim (SD-J's own words, `0081:770`); AC-7 is NEW —
created by Cray's SD-I=(b) override (s148). Test artifacts are landed
by Code at build time (this drafter cannot write `tests/` — the PLAN-0079
AC-2 precedent).

| This PLAN | Maps from | Substance |
|---|---|---|
| AC-1 | 0081 AC-12 | ADR-first ordering gate (now: ONE new ADR + two pointer notes) |
| AC-2 | 0081 AC-13 | mechanism works end-to-end |
| AC-3 | 0081 AC-14 | reproducibility + committed home (extended by SD-I=(b)) |
| AC-4 | 0081 AC-15 | exactly one authoritative `Person` |
| AC-5 | 0081 AC-11 | existing-vertical migration, behavior preserved |
| AC-6 | 0081 AC-7/9c | OQ-6 marker transformation (owned HERE — SD-K(ii)=(a)) |
| AC-7 | NEW — SD-I=(b) | `person` DB table + Alembic migration (committed-ORM DB surface) |

- [ ] **AC-1 — the NEW shared-ontology ADR lands FIRST (CLAUDE.md §8:
  the ADR is merged before the related implementation PR).** Pass/fail
  read: **ONE new shared-ontology ADR** (OQ-1 resolved, Cray s148; next
  free number — likely ADR-0033) codifying the SD-F=(a) home/namespace
  reservation + the SD-G=(b)+(c) `imports:`/pre-pass mechanism + the
  Step-1 type-system extension for constrained collection properties +
  the SD-I=(b) committed-ORM contract for the shared home is **Accepted**
  and MERGED, **together with its two pointer-note edits** (ADR-0008 +
  ADR-0026 — both G1 Accepted-body edits authored WITH the new ADR,
  ratified in ONE pass, never flip Status then edit body), before any
  Step 2–7 grammar/codegen/ORM/migration change ships. G1-gated:
  plan-drafter authors in a SEPARATE dispatch, Code commits.
  Verified at R2 by PR ordering, not by a pytest artifact. Fails if any
  grammar/codegen/ORM/migration change ships ahead of its ADR, or if the
  pointer notes are dropped (leaving ADR-0008/0026 silently stale).
- [ ] **AC-2 — the shared-ontology mechanism WORKS end-to-end.** Pass/fail
  read: the shared ontology YAML at `ontology/core_v0.yaml` with the
  reserved `core` namespace (SD-F=(a)), defining
  `Person` as an ADR-0008 `object_type`, generates a shared `Person` type
  via the extended generator/CLI, and a
  cross-vertical reference to the shared type resolves via the ratified
  `imports:` + pre-pass mechanism (SD-G=(b)+(c))
  WITHOUT the `KeyError` the shipped within-doc
  resolution would raise (`code_generator.py:163,435`). Code lands a
  generate-then-import test: the generated shared `Person` is importable
  and its fields match the YAML definition **including the load-bearing
  constraints** (`roles` non-empty, unknown-field rejection — the
  `spec.py:1367,1374-1378` behavior, expressed by the EMITTER per the
  amended grammar, never by a hand-written shim). Fails if the shared type
  is hand-written rather than generated, or if "resolution" duplicates the
  object_type into each vertical's own doc.
- [ ] **AC-3 — reproducibility + the generated module's home are handled,
  not left ambient.** Pass/fail read: the shared generated artifacts
  follow the committed-vs-gitignored discipline — reference artifacts
  gitignored-reproducible (`.gitignore:41-42` / ADR-0008 `:101`);
  runtime-imported code at a COMMITTED path (the `_ORM_COMMITTED_DEST` /
  B1 Option-B precedent, `code_generator.py:736-742`) — which under
  **SD-I=(b)** now INCLUDES the shared `Person` ORM:
  `_ORM_COMMITTED_DEST` is EXTENDED with the shared-doc entry (the layout
  pick is the forced B1-DP-1 call — Step 4); and a codegen re-run is
  idempotent (regenerating
  from an unchanged YAML produces no diff — Code lands the check). The DB
  table + Alembic migration themselves are AC-7 — split out so this AC
  stays the reproducibility/committed-home gate. Fails
  if runtime-imported code lands under a gitignored path, or if
  regeneration is not reproducible.
- [ ] **AC-4 — the spec-layer `Person` is RECONCILED: exactly ONE
  authoritative `Person` type remains.** Pass/fail read: after Step 5, the
  SD-H=(a) end state (delete + re-export) holds — there are NOT two
  competing `Person`
  types; every consumer (`VerticalProcedures.principals` `spec.py:1660` +
  parse `:1789`, `check_principal_sod` `principal_sod.py:118`, `auth.py:49`
  `_principal_index`) resolves to the generated shared type (directly or
  via the SD-H re-export), and Code lands a grep-level guard that FAILS if
  a second independent `class Person(BaseModel)` definition reappears
  outside the generated home. Fails on any two-`Person` collision.
- [ ] **AC-5 — the two existing verticals migrate onto the shared `Person`
  with behavior preserved (scope per SD-K(i)=(a)).** Pass/fail read:
  procurement + supply_chain resolve their principals as instances of the
  generated shared type; procurement's **dual roster source is unified**
  (the `procedures.yaml:64` block vs `person.csv` via
  `load_fastenal_principals`, `hero_demo/procedure.py:70-76` — one
  canonical source remains, the other becomes a pointer or is retired);
  `verticals/supply_chain/procedures_factory.py:272,295` and
  `services/api/auth.py:49` read the shared seam. Every existing SoD /
  tier-authority / gate-resolve test passes **unmodified in its
  assertions** (roster-source plumbing may change; verdicts may not), and
  the SoD fail-closed SEMANTICS are untouched (`check_principal_sod`'s
  verdict behavior preserved; no change to `_spend()`, `resolve_doa_tier`,
  `check_tier_authority`). Fails if any existing governance verdict
  changes, or if a per-vertical `Person` TYPE survives alongside the
  shared one.
- [ ] **AC-6 — the OQ-6 marker is transformed honestly (owned HERE —
  SD-K(ii)=(a), Cray s148; PLAN-0081's pending fold re-points its AC-7 to
  its Step-9 residue).** Pass/fail read:
  `test_principal_identity_retrigger.py` changes FROM the N-count
  re-trigger (`:43,:80`) INTO an assertion that the shared generated
  `Person` **is the one type every principal-bearing vertical's roster
  parses into** (no re-arm at N=4; a future vertical adding principals
  onto the shared home is the INTENDED state; a regression REINTRODUCING a
  per-vertical `Person` definition fails). The module docstring preserves
  the honest lineage: N=2 fired and was answered (per-vertical
  re-confirmed + follow-on filed, PLAN-0074 AC-12); at N=3 the extraction
  was **PERFORMED — by THIS PLAN, with PLAN-0081 landing the 3rd vertical
  on the shared home**. Fails if the baseline is merely extended/re-armed,
  or if the lineage record is dropped.
- [ ] **AC-7 (NEW — created by Cray's SD-I=(b) override, s148) — the
  shared `Person` ships a DB surface: committed ORM + `person` table +
  Alembic migration.** Pass/fail read: the generated shared-`Person` ORM
  lives at its committed destination (registered in
  `_ORM_COMMITTED_DEST`, per AC-3); a new Alembic revision — the 12th in
  the chain, and the FIRST creating an ontology-object table outside the
  energy schema (verified this fold: `0001_initial_energy_schema.py` is
  the only ontology-object revision today) — creates the `person` table
  matching the generated ORM, and applies cleanly under the repo's
  disposable test-DB pattern (Code lands the check per the existing
  DB-test discipline; DB-backed checks skip when Postgres is down, so
  this check must be RUN green on the PR head, not skip-passed). Runtime
  principal resolution (`auth.py:49` et al.) stays roster-fed under this
  PLAN: the table ships without a decided population path — OQ-2 owns
  those mechanics — and no runtime consumer may start REQUIRING table
  population before OQ-2 resolves. Honest scope cost, stated plainly
  (ADR-0032 D6): this is the repo's SECOND committed generated ORM (only
  `energy` registers one today) and its first non-energy ontology-object
  migration — the DB/migration blast radius Cray consciously accepted in
  the SD-I=(b) override. Fails if the ORM lands gitignored, if the
  migration hand-drifts from the generated ORM, or if the table silently
  becomes load-bearing at runtime.
  *(Structural note, flagged for R2: this drafter split the DB surface
  into its own AC rather than overloading AC-3 — AC-3 keeps the
  reproducibility/committed-home discipline, AC-7 owns the table +
  migration + empty-safe bar. Collapse into AC-3 at R2 if Code prefers.)*

## Out of Scope

- ❌ **The `building_materials` migration** — PLAN-0081 Step 9's residue;
  this PLAN ships the home the hero lands on, it does not touch the hero's
  vertical.
- ❌ **The hero build itself** (PLAN-0081 Steps 1–8: spine, reshape seam,
  factory wiring, endpoint re-points, the D7 re-evaluation).
- ❌ **Authoring any ADR.** OQ-1 = (Cray, s148) ONE NEW shared-ontology ADR
  (likely ADR-0033) that both ADR-0008 + ADR-0026 point to, plus its two G1
  pointer-note edits (ADR-0008 grammar reference; ADR-0026 `:89` supersession
  + OQ-6 closure) — authored by a SEPARATE plan-drafter dispatch, merged
  before impl (AC-1). This PLAN only pins the ordering.
- ⏩ **A `Person` DB/ORM table is now IN SCOPE (SD-I=(b), Cray s148).** The
  original draft deferred this "unless Cray picks (b), via a conscious
  follow-on amendment" — this fold IS that conscious amendment: the committed
  ORM + `person` table + Alembic migration are AC-7 (+ the AC-3 extension +
  Step 4). Still OUT: POPULATING the table (OQ-2 — runtime stays roster-fed)
  and any cross-vertical identity semantics (ADR-0026 OQ-3=(c) untouched).
- ❌ **Genericizing beyond `Person`.** The shared mechanism ships with
  `Person` as its N=1 consumer — a Rule-of-Three tension **consciously
  accepted** by SD-E=(b-ii) (ADR-0008 `:79-80` deferred `shared property`
  constructs to a 3-verticals trigger; the AC-1 amendment must re-argue
  that deferral on Cray's ratified strategic ground, `0081:660-666`). No
  second shared object_type is authored here.
- ❌ **Promoting `PrincipalAlias` / `ServicePrincipal`.** Both stay
  spec-layer (`spec.py:1340-1356,1381-1397`); only `Person` promotes.
  A future shared-type need re-opens this under the amended grammar.
- ❌ **Cross-vertical identity SEMANTICS** — no cross-vertical SoD
  comparison, no cross-vertical role semantics, no alias-collapse change
  (ADR-0026 OQ-3=(c) stands); rosters remain per-org demo DATA.
- ❌ **Roster merging** — the shared home unifies the TYPE, not the DATA.
- ❌ **Writing test files by this drafter** — Code lands every AC test.

## Steps

### Step 1: The ADR dependency — pinned first gate (AC-1; NOT authored here)
Block all grammar/codegen/ORM work behind the Accepted ADR. OQ-1 is
RESOLVED (Cray, s148): **ONE NEW shared-ontology ADR** (likely ADR-0033)
that both ADR-0008 + ADR-0026 point to, plus its two G1 pointer-note edits
(ratified one-pass) — NOT two in-place amendments. The new ADR's content
obligations, as grounded by this PLAN (handed to the authoring dispatch as
its fact-pack): **(i)** the SD-F shared home + reserved namespace token —
noting the reservation is semantic (D2 prose + validator/CLI), since L1
already admits the token syntactically (`ontology_schema.json:15-18`);
**(ii)** the SD-G discovery/resolution grammar (the `imports:` key +
pre-pass semantics); **(iii)** the TYPE-SYSTEM extension for constrained
collection-valued properties — `roles: frozenset[RoleId]` min≥1 is
unexpressible in the D3 table today (`0008:65-77` vs `spec.py:1374-1378`) —
or an equivalent constraint construct; **(iv)** the SD-I=(b) committed-ORM
contract for the shared home — the shared ontology's runtime ORM generates
to a COMMITTED path and backs a DB table, extending ADR-0008 D5's
generation contract beyond the per-vertical gitignored default; **(v)** the
conscious re-argument of the `:79-80` `shared property` Rule-of-Three
deferral (mechanism at N=1 consumer); **(vi)** the ADR-0026 `:89`
supersession record + OQ-6 closure-by-extraction (`:116`); **(vii)** the
ADR-0024 D3 H-partition clarification — the `Person` TYPE becomes
codegen-emitted while roster DATA stays human-authored ("never
model-emitted" in the shipped docstrings means LLM-emission; the two axes
must not be conflated, and the H markers survive the move); **(viii)**
optionally reconcile D5's 5-artifact table with the shipped 7 emitters
(`code_generator.py:756-762`) — a known drift, Cray/dispatch's call.

### Step 2: The shared ontology home + reserved namespace (SD-F)
Create the shared/core ontology YAML at `ontology/core_v0.yaml` (SD-F=(a),
Cray s148) with the reserved `core` namespace, defining `Person` as an
ADR-0008 `object_type`:
`person_id` (primary key), `name`, `roles` (via the Step-1(iii) construct,
min≥1), carrying the spec-layer semantics (`spec.py:1369-1378`) including
description text and the H-partition provenance comments. L1 + L2
validation extended to cover the shared doc (the `vero-lite validate`
surface follows the SD-G invocation shape).

### Step 3: Extend the generator + CLI for shared-doc discovery + cross-vertical resolution (SD-G)
Per SD-G=(b)+(c) (Cray, s148) — the explicit `imports:` grammar key as the
declared, greppable surface + a shared-doc pre-pass that emits ONE shared
module which vertical generation imports (never a per-vertical re-embed):
extend `load_doc`/`generate_all`
(`code_generator.py:71-76,745-763`) and the CLI path wiring
(`cli.py:22-23,37-52`) so the shared doc is discoverable, validatable, and
generable; cross-vertical `ref` resolution routes through the mechanism
instead of raising `KeyError` (`:163,:435`). The 7-emitter surface is
extended only as far as the shared doc needs (the Pydantic emitter is the
load-bearing one; which other emitters run for the shared doc is a build
detail Code records at R2).

### Step 4: Generate the shared `Person` + ship the DB surface (SD-I=(b), AC-3 + AC-7)
Run the extended codegen → the generated shared `Person` module at a
COMMITTED path (extend `_ORM_COMMITTED_DEST`, `code_generator.py:736-742`;
reference artifacts stay gitignored-reproducible), and land the
idempotent-regen check (unchanged YAML → zero diff, AC-3). Extending
`_ORM_COMMITTED_DEST` with the shared-doc entry forces the deferred B1-DP-1
2nd-ORM-layout call (`code_generator.py:740-741`) — drafter-recommended: a
separate committed module (e.g. `services/db/person.py`) preserving per-doc
YAML→ORM parity (`services/db/identity.py:1-8`), Code finalizes at R2.
Author the Alembic revision (the 12th; the first ontology-object table
outside the energy schema) creating the `person` table (AC-7). Population
is NOT built here — OQ-2 owns it; the table ships empty and runtime stays
roster-fed.

### Step 5: Reconcile the spec-layer `Person` (SD-H=(a), AC-4)
Per SD-H=(a) (Cray, s148): DELETE the class at `spec.py:1359-1378` and
RE-EXPORT the generated type from the spec-layer import path so every
consumer keeps its import — exactly one authoritative
definition remains. Handle the satellites explicitly: `PersonId`/`RoleId`
aliases (`spec.py:833,839`) stay or move with the re-export coherently;
`PrincipalAlias` + `ServicePrincipal` stay spec-layer and continue to
reference the (now generated) `Person`'s id-space; the H-partition
docstrings are preserved. Code lands the AC-4 grep guard.

### Step 6: Migrate procurement + supply_chain onto the shared `Person` (SD-K(i)=(a), AC-5) + transform the marker (SD-K(ii)=(a), AC-6)
Type-source unification for both verticals (with SD-H=(a) the imports may
be near-no-ops — the LOAD-BEARING work is procurement's dual-roster
unification: `procedures.yaml:64` vs `person.csv` via
`load_fastenal_principals`, one canonical source remains) + re-point
`hero_demo/run.py` wiring (lines carried from `0081:840-841` — Code
verifies on disk at build), `supply_chain/procedures_factory.py:272,295`,
and `auth.py:49` if the seam moves. Behavior bar: AC-5 — existing test
assertions unmodified, verdicts unchanged. Transform
`test_principal_identity_retrigger.py` per AC-6 with the lineage record
(owned here — SD-K(ii)=(a), Cray s148).

### Step 7: Coordination + verification pass
Full offline suite green; the AC-2 generate-then-import test, AC-3
idempotence check, AC-4 grep guard, AC-5 migration bar, AC-6 marker, and
the AC-7 DB surface (migration applied green on the PR head) all present;
diff inspection at R2 confirms the engine touch is bounded to the named
mechanism + reconciliation + migration scopes with governance semantics
untouched. Closeout records: OQ-2 resolved-or-explicitly-deferred;
PLAN-0081 is UNBLOCKED (its Step 9 residue = `building_materials` only) and
PLAN-0081's own fold (recording SD-J=SPLIT + the shrink + re-pointing its
AC-7 per SD-K(ii)=(a)) is flagged as the parent's next drafting action.
This PLAN archives to `done/` per Plan Flow.

## Verification

The offline oracle is the gate: `pytest` fully green on the PR head with
every Code-landed AC assertion present — the generate-then-import test
(AC-2: the shared `Person` generated at the SD-F home via the SD-G
mechanism; cross-vertical resolution without the shipped `KeyError`;
constraints emitter-expressed), the idempotent-regen check + committed-home
discipline (AC-3), the one-`Person` grep guard (AC-4), the migration
behavior bar (AC-5: existing SoD/tier/gate-resolve assertions unmodified),
the transformed marker with preserved lineage (AC-6 — owned here,
SD-K(ii)=(a)), plus the AC-7 DB surface (the Alembic migration RUN green on
the PR head under the disposable test-DB pattern, `tests.db_support` — NOT
skip-passed when Postgres is down). **AC-1 is R2/process-verified, not a
pytest artifact:** the new ADR + its two pointer-note edits merged BEFORE
the implementation PR, checked by PR ordering. The codegen/mechanism suite
stays deterministic-offline (no MS-S1, no live host-state); only AC-7's
migration check touches the DB. CI RED states, if any, are intra-branch
only; the merged PR is green.

## Surfaced Decisions

**Resolved parent inputs (Cray, s147, AskUserQuestion) — recorded, NOT
re-opened here:**

- **SD-E — RESOLVED = (b-ii):** promote `Person` to an ADR-0008 ontology
  `object_type` at a NEW shared/core ontology home. Full record — the
  grounded cost, why Cray chose it over the lighter spec-layer (a), and
  the rejected alternatives (a)/(b-i)/(c) with classifications:
  `0081:643-683`.
- **SD-J — RESOLVED = (b) SPLIT:** this PLAN is that verdict executed.
  Record + the absorb-vs-split option set: `0081:760-782`.

**Resolved this PLAN's SD round (Cray, s148, typed AskUserQuestion):
SD-F=(a), SD-G=(b)+(c), SD-H=(a), SD-I=(b) [OVERRIDE of the drafter's (a)],
SD-K(i)=(a), SD-K(ii)=(a).** The option sets + drafter recommendations +
rejected-alternatives lineage below are KEPT verbatim as the REASONING
RECORD — each "Drafter recommendation: (x)" is now Cray's ratified pick,
EXCEPT SD-I where Cray overrode (a)→(b). SD-I's override is classified
`superseded by new info` (the PLAN-0081 SD-D precedent): the drafter's (a)
remains internally sound, declined on scope-appetite grounds — Cray chose
the more foundational/complete option with the DB/migration blast-radius
cost in view. SD-K was new — this PLAN's own boundary; both parts resolved
=(a). The parent's fuller prose at the cited `0081:` lines governs on any
wording doubt.

- **SD-F — WHERE the shared/core ontology file lives + its namespace**
  (`0081:689-705`). ADR-0008 D2 fixes `namespace: <vertical_name>`
  (`0008:37-63`); the pick is PART of what the amendment codifies — a
  grammar reservation, not a file-layout detail (and per grounded finding
  #2, a semantic reservation: L1 already admits the token). Options:
  **(a)** a repo-level `ontology/core_v0.yaml` — a new top-level home,
  visibly NOT a vertical; the amendment reserves a `core`/`shared`
  namespace token. **(b)** `verticals/_shared/ontology/…` — under the tree
  the tooling knows, but a pseudo-vertical (a lie-shaped path discovery +
  CLI must special-case). **(c)** `services/engine/ontology/…` —
  engine-owned, but inverts the "engine artifacts are generated FROM the
  ontology" direction. **Drafter recommendation: (a)** — honest topology
  (shared ≠ a vertical), one reserved namespace, the cleanest grammar
  story. **Why Cray:** repo topology + a namespace-grammar reservation
  that outlives this PLAN — every future shared type inherits it.
- **SD-G — HOW the generator/CLI discovers + loads the shared ontology,
  and how a cross-vertical `ref` resolves** (`0081:706-725`). Shipped
  baseline: single-doc `load_doc` (`code_generator.py:71-76`), per-vertical
  CLI hard-wire (`cli.py:22-23`), within-doc-only `ref` (`:163,:435`).
  Options: **(a)** a two-doc merge at generate time — simplest, but each
  vertical's generated module re-EMBEDS its own `Person` copy, recreating
  the N-copies problem at the artifact layer and colliding with AC-4.
  **(b)** a shared-ontology pre-pass — the shared doc emits ONE shared
  module; vertical generation resolves shared refs against it and emits
  IMPORTS. **(c)** an explicit `imports:` (or `extends:`) grammar key in a
  vertical's `_v0.yaml` naming the shared doc — the dependency declared in
  YAML, never inferred. **Drafter recommendation: (b) + (c) combined** —
  the `imports:` key is the grammar surface (declared, greppable,
  amendment-codifiable); the pre-pass + emitted-import is the mechanism
  (exactly ONE generated `Person`, satisfying AC-2 + AC-4). **Why Cray:**
  this IS the shared-ontology mechanism the amendment codifies — the
  resolution semantics every future shared type uses.
- **SD-H — WHAT happens to the existing spec-layer `Person`**
  (`spec.py:1359-1378`; `0081:726-744`). The two-`Person`-collision risk
  lives here (AC-4 pins the end state). Options: **(a)** DELETE the class
  and RE-EXPORT the generated type from the spec-layer path — consumers
  keep their import path; exactly one authoritative definition. **(b)**
  keep a thin alias/subclass — risk: "thin" accretes logic and becomes a
  second definition. **(c)** generate INTO the spec-layer path — a
  committed, hand-edited engine module becoming partially generated is a
  standing hazard. **Emitter-capability note, now grounded (finding #1):**
  the D3 grammar cannot express `roles` today — any gap is an EMITTER +
  GRAMMAR extension (Step 1(iii)), never a hand-written shim quietly
  carrying the constraints. **Drafter recommendation: (a)** —
  delete-and-re-export, guarded by AC-4's grep check. **Why Cray:** it
  pins the single-source-of-truth end state — the wrong pick silently
  recreates the collision AC-4 exists to prevent.
- **SD-I — does the shared `Person` get a committed ORM/DB home?**
  (`0081:745-759`). The Pydantic module's committed-vs-gitignored half is
  SETTLED by AC-3 (runtime-imported code cannot live gitignored — the B1
  Option-B precedent, `code_generator.py:736-742`). The open fork is the
  DB side. Options: **(a)** NO ORM/DB home — `Person` is a Pydantic-only
  shared type; rosters remain per-vertical YAML demo data; no table, no
  migration (matches the mirror discipline — only energy has a committed
  ORM today). **(b)** a committed ORM + DB table à la energy. **Drafter
  recommendation: (a)** — no consumer needs a `Person` table today; (b)
  drags migrations + the DB surface into an already-heavy identity
  refactor. **Why Cray:** it decides whether the identity model enters the
  DB/migration blast radius — a scope call, not a mechanics call.
  **→ RESOLVED = (b) (Cray, s148) — OVERRIDE of this recommendation;
  `superseded by new info` (PLAN-0081 SD-D precedent). Consequences
  threaded: Out-of-Scope flip, AC-3 + AC-7, Step 4, Step 1(iv), OQ-2.**
- **SD-K (NEW — this PLAN's scope boundary vs PLAN-0081; two sub-parts):**
  **(i) WHICH verticals migrate HERE.** Options: **(a)** this PLAN
  migrates the two EXISTING principal-bearing verticals (procurement +
  supply_chain — PLAN-0081 AC-11's targets), leaving `building_materials`
  to PLAN-0081 Step 9; **(b)** this PLAN ships mechanism + reconciliation
  only, and PLAN-0081 migrates all three. **Drafter recommendation: (a)**
  — the mechanism is proven end-to-end on shipped, fully-test-covered
  consumers BEFORE the hero stacks on it; option (b) re-couples the
  migration blast radius to the hero build, which is the exact coupling
  SD-J=SPLIT was ratified to avoid. **(ii) WHICH PLAN owns the OQ-6
  marker transformation** (PLAN-0081 AC-7/9c as parent-written). Options:
  **(a)** transform HERE (AC-6): after Step 5 the per-vertical `Person`
  TYPE no longer exists, so the marker's N-count premise is dead — leaving
  it untransformed leaves a tripwire asserting a retired architecture, and
  it would then fire mid-PLAN-0081 as a surprise; **(b)** leave it to
  PLAN-0081 (as its AC-7 currently states) — both sequencings keep CI
  green here (the counter reads roster DATA, still N=2 after this PLAN).
  **Drafter recommendation: (a)** transform here, and PLAN-0081's pending
  fold re-points its AC-7 to its Step-9 residue ("`building_materials`
  lands on the shared home"). **Why Cray (both sub-parts):** this is
  cross-PLAN scope + sequencing — the same routing authority that ratified
  SD-J; the drafter cannot re-partition Cray's split.

## Open questions (surfaced, not decided)

- **OQ-1 — RESOLVED (Cray, s148): ONE NEW shared-ontology ADR that both
  ADR-0008 + ADR-0026 point to (NOT two in-place amendments).** The ADR
  work is substantial + load-bearing: the new ADR (likely ADR-0033)
  codifies the SD-F home/namespace, the SD-G `imports:`+pre-pass mechanism,
  the Step-1(iii) type-system extension, the SD-I=(b) committed-ORM
  contract, and the `:79-80` deferral re-argument; plus two G1 pointer-note
  edits — ADR-0008 (grammar reference) + ADR-0026 (`:89` supersession +
  OQ-6 closure-by-extraction `:116`, honoring `:95`/`:157`). All three (new
  ADR + two notes) are ratified one-pass (never flip Status then edit body)
  and merge BEFORE the implementation PR (CLAUDE.md §8; AC-1). A separate
  plan-drafter dispatch authors them; nothing ADR-shaped is authored here.
- **OQ-2 (NEW — opened by SD-I=(b)) — the `person` table's population
  story.** The committed ORM + table ship EMPTY (AC-7 is empty-safe;
  runtime principal resolution stays roster-fed). HOW the table gets
  populated is undecided. Recommended shape: an explicit, idempotent,
  per-vertical seed script (never load-on-startup); rows carry
  source-vertical/org provenance; uniqueness scoped so same-named
  principals from different orgs never merge; the rosters
  (`procedures.yaml` `principals:` + procurement's `person.csv`) stay the
  canonical demo DATA + the runtime source until this resolves. HARD
  constraint: the table is a typed STORE, not a cross-vertical merge —
  ADR-0026 OQ-3=(c) stays untouched. Code proposes the shape at Step-4
  build; Cray ratifies. AC-7 passes with the table empty, so OQ-2 never
  blocks the mechanism.

## References

- **PLAN-0081** (`docs/plans/0081-building-materials-governed-credit-hero.md`)
  — the parent: SD-E record `:643-683`; SD-F..SD-I `:689-759`; SD-J
  `:760-782`; OQ-1 `:786-810`; AC-11..AC-15 `:273-330`; Step 9/9a
  `:508-575`; the codegen-crux current state `:139-163`; verified-anchor
  lists `:827-881`.
- **ADR-0008** (`docs/adr/0008-yaml-ontology-specification.md`) — D2
  namespace grammar `:37-63`; D3 type table `:65-77` (no collection type —
  the Step-1(iii) gap); the `shared property` Rule-of-Three deferral
  `:79-80`; D5 generation contract `:89-101` (gitignore line `:101`).
- **ADR-0026** (`docs/adr/0026-principal-identity-run-enforcement.md`) —
  the superseded `:89` consequence; the `:95` ontology-layer tension; the
  OQ-6 `:116` resolution this PLAN's extraction closes; the `:157`
  "ontology object (ADR-0008 grammar)" Implementation Note; the `:164`
  out-of-scope gate this extraction now passes through.
- Codegen anchors (verified this session):
  `services/engine/code_generator.py:71-76,163,435,736-742,745-763,756-762`;
  `services/engine/cli.py:22-23,37-52`; `pyproject.toml:44-45`;
  `.gitignore:41-42`; `services/engine/ontology_schema.json:7,15-18`.
- Identity anchors (verified this session):
  `services/engine/procedures/spec.py:833,839,845` (id aliases),
  `:1340-1356` (`PrincipalAlias`), `:1359-1378` (`class Person`),
  `:1381-1397` (`ServicePrincipal`), `:1649` (`VerticalProcedures`),
  `:1660-1675` (principal fields), `:1677-1694` (validators), `:1789`
  (parse); `services/engine/procedures/principal_sod.py:118`
  (`check_principal_sod`); `services/api/auth.py:49` (`_principal_index`).
- Migration anchors (verified this session unless noted):
  `verticals/procurement/procedures.yaml:64,93`;
  `verticals/procurement/hero_demo/procedure.py:70-76`;
  `verticals/supply_chain/procedures.yaml:63-84`;
  `verticals/supply_chain/procedures_factory.py:272,295`;
  `tests/services/engine/procedures/test_principal_identity_retrigger.py:43,49,71,80`.
  *Carried from PLAN-0081, not re-verified:* `hero_demo/run.py`
  `:347-358,:380-382,:542-550,:666,:738-749`.
- DB-surface anchors (verified this fold, s148 — `main` db4d866):
  `alembic.ini:6`; `alembic/versions/` (11 revisions; the only
  ontology-object table is `0001_initial_energy_schema.py`; runtime tables
  in 0002/0005/0007/0011); `services/db/identity.py:1-8,20-34` (stores
  `person_id` strings, not a roster); `_ORM_COMMITTED_DEST` energy-only at
  `code_generator.py:736-742` (the deferred B1-DP-1 2nd-ORM-layout call
  `:740-741`); next free ADR number = 0033 (highest Accepted = 0032; 0014
  WITHDRAWN).

---

> **Drafting provenance (ADR-012 D4.3 / ADR-013 OQ-1).** Authored by the
> in-harness `plan-drafter` subagent under ADR-013 D1 phased authority, on
> Code's session-147 dispatch executing **Cray's SD-J=SPLIT ratification
> (typed AskUserQuestion, s147)** — the split-out dependency PLAN that
> PLAN-0081's SD-J verdict commissions. SD-E=(b-ii) and SD-J=SPLIT are
> treated as resolved inputs (not re-litigated); SD-F..SD-I + OQ-1 are
> carried forward OPEN with their PLAN-0081 option sets and lineage;
> SD-K is newly surfaced. Every `file:line` above was read from disk by
> this drafter on `main` fa4f6c6, 2026-07-18, EXCEPT the
> `hero_demo/run.py` wiring lines (carried from PLAN-0081 `:840-841`,
> marked; Code spot-checks at build). Two NEW grounded findings beyond the
> PLAN-0081 fact-pack: the ADR-0008 D3 no-collection-type gap vs
> `Person.roles` (Step 1(iii)) and the L1 namespace pattern's syntactic
> admission of a shared token (`ontology_schema.json:15-18`). One
> parent-state discrepancy flagged, classified `superseded by new info`:
> on-disk PLAN-0081 still lists SD-J as open — its fold postdates this
> draft and is a separate drafting action. No ADR authored; no `tests/`
> file written; no shell run; no commit. Independent review: Code (R2) at
> PR; ratification: Cray (SD-F..SD-K + OQ-1). Author≠reviewer separation:
> **INTACT**. Uncommitted draft — Code commits per ADR-009 D2.
>
> **Fold (s148): Cray's SD-round rulings recorded** — SD-F=(a), SD-G=(b)+(c),
> SD-H=(a), **SD-I=(b) OVERRIDE**, SD-K(i)=(a), SD-K(ii)=(a), OQ-1 = one new
> shared-ontology ADR; OQ-2 newly surfaced (the `person` table's population
> story). Verified this fold on `main` db4d866: next free ADR = 0033,
> `_ORM_COMMITTED_DEST` energy-only, the alembic chain's only ontology-object
> table (`0001_initial_energy_schema.py`). Authored across two `plan-drafter`
> passes — the first L1-halted at 15/28 edits having authored the full
> remaining punch list; **Code applied the drafter-authored punch list after
> a git-commit L1-reset, then R2'd the whole file** + re-verified the new
> anchors. Author (plan-drafter) ≠ applicator/reviewer (Code) — separation
> INTACT.
