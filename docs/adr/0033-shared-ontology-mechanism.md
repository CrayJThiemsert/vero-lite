# ADR-0033: Shared-ontology mechanism — the repo-level `core` home + reserved namespace, the `imports:` pre-pass, the constrained-collection type extension, and the shared `Person` with a committed ORM + DB surface

**Status:** Accepted
**Ratified:** 2026-07-18 (Jirachai Thiemsert / Cray, session 149, typed AskUserQuestion) — the construct ratified ONE-PASS together with both pointer notes (ADR-0008, ADR-0026); OQ-1 adjudicated = (a) JSONB (see § Open Questions).
**Date:** 2026-07-18
**Deciders:** Jirachai Thiemsert (founder) — ratifies the construct AND adjudicates OQ-1 (§ Open Questions)
**Related:** ADR-0008 (the YAML ontology grammar — **EXTENDED by this ADR, never amended in place**: D2/D3/D5 stand as written for per-vertical docs; its `:79-80` `shared property` Rule-of-Three deferral is consciously re-argued in D6 below; ADR-0008 carries the matching pointer note), ADR-0026 (principal identity + run enforcement — **superseded in part**: its `:89` "no new generation surface / codegen path untouched" consequence no longer holds, and its OQ-6 per-vertical-`Person` deferral `:116` is **CLOSED by this extraction**; its `:95` ontology-layer framing and `:157` "ontology object (ADR-0008 grammar)" Implementation Note are what this ADR honors; ADR-0026 carries the matching pointer note), ADR-006 (D4 Rule of Three — "concrete-first or nothing"; the D6 re-argument's governing discipline), ADR-0024 (D3 "governed ≠ generated" / the G-H-D partition — the D4 two-axes clarification), ADR-016 (the procedure engine whose spec layer re-exports the generated type), ADR-0031 (D4 fractal Rule-of-Three discipline; the closed-governed vocabulary), ADR-0032 (D6 honest-cost discipline — § Consequences states the blast radius plainly), ADR-009 D1/D2 · ADR-012 D4.3 / ADR-013 (drafting + commit boundary). **Implementing PLAN: PLAN-0082** (`docs/plans/0082-shared-ontology-mechanism-and-person-promotion.md` — Steps 2–7 build what this ADR decides; its parent PLAN-0081 lands the 3rd vertical on the shared home).

> **Drafting provenance (ADR-012 D4.3 / ADR-013 OQ-1).** Drafted (uncommitted)
> by the in-harness `plan-drafter` subagent under ADR-013 D1 phased authority,
> on Code's session-149 dispatch executing **Cray's OQ-1 ratification (typed
> AskUserQuestion, s148): ONE new shared-ontology ADR** plus two pointer-note
> edits. Code R2-reviews + commits via a `docs/*` PR after Cray ratifies
> (ADR-009 D2). This is a **new ADR** — Code is G2-gated from authoring it;
> the independent design lens is the point. Outline originator = Cray (the
> s147/s148 SD rulings this ADR codifies). Independent reviewer = Code (R2)
> at PR + Cray at ratification. Author≠reviewer separation: **INTACT**.

---

## Context

### The ratified mandate (codified here, never re-opened)

Cray ratified, via typed AskUserQuestion across sessions 147–148 (full
records: PLAN-0082 § Surfaced Decisions; PLAN-0081 `:643-683,689-782`):

- **SD-E = (b-ii)** — promote `Person` from a spec-layer convenience to an
  ADR-0008 ontology `object_type` at a NEW shared/core ontology home,
  inventing the shared-ontology mechanism.
- **SD-J = SPLIT** — the mechanism is its own dependency PLAN (PLAN-0082);
  PLAN-0081 (the building-materials governed-credit hero) depends on it.
- **SD-F = (a)** — the shared home is a repo-level `ontology/core_v0.yaml`
  with a reserved `core` namespace token (NOT a pseudo-vertical, NOT
  engine-owned).
- **SD-G = (b)+(c)** — discovery/resolution = an explicit `imports:` grammar
  key (declared, greppable) + a shared-doc PRE-PASS emitting ONE shared
  module that vertical generation IMPORTS (never a per-vertical re-embed).
- **SD-H = (a)** — the shipped spec-layer `Person` is DELETED and RE-EXPORTED
  from the generated type — exactly one authoritative definition.
- **SD-I = (b)** — the shared `Person` ships a COMMITTED generated ORM + a
  `person` DB table + an Alembic migration (an OVERRIDE of the drafter's (a)
  recommendation, classified `superseded by new info` — Cray consciously
  chose the DB/migration blast radius; PLAN-0082 § Surfaced Decisions).
- **SD-K(i)/(ii) = (a)/(a)** — PLAN-0082 migrates procurement + supply_chain
  and owns the OQ-6-marker transform (scope facts this ADR references, not
  decides).
- **OQ-1 (PLAN-0082) = ONE new ADR** — this document; it must merge, with its
  two pointer notes, BEFORE any grammar/codegen/ORM/migration change ships
  (CLAUDE.md §8; PLAN-0082 AC-1).

### The grounded gap (every anchor verified on disk, `main` b93c1e1, 2026-07-18)

The shipped codegen model is **strictly per-vertical by construction**, and
`Person` is unexpressible in the grammar:

- `generate_all` loads exactly ONE ontology YAML over the single-doc
  `load_doc` (`services/engine/code_generator.py:71-76,745-763`) — no
  import/include/merge logic exists. The CLI hard-wires
  `verticals/{vertical}/ontology/{vertical}_v0.yaml`
  (`services/engine/cli.py:22-23`).
- A `ref`-typed property resolves ONLY within the same doc
  (`object_types[target]` — SQL emitter `code_generator.py:161-165`, ORM
  emitter `:433-435`); a cross-vertical `ref` today raises `KeyError`.
- ADR-0008 D2 fixes `namespace: <vertical_name>` (`0008:41`); D5 puts every
  artifact under `verticals/<name>/generated/` (`:89-101`), gitignored
  (`:101`) — except the runtime-imported ORM, which generates to a COMMITTED
  path when registered (`_ORM_COMMITTED_DEST = {"energy":
  Path("services/db/models.py")}`, `code_generator.py:742`; the PLAN-0031 B1
  Option-B precedent, deferral comment `:736-741`).
- **The type-system gap is concrete, not hypothetical:** the ADR-0008 D3
  type table (`0008:65-77`) has NO collection/array type (only
  `string/int/float/bool/timestamp/date/enum/json/ref`), but the shipped
  `Person` carries `roles: frozenset[RoleId]` with `min_length=1`
  (`services/engine/procedures/spec.py:1374-1378`) and
  `model_config = ConfigDict(extra="forbid")` (`:1367`) — load-bearing
  governance constraints (a roles-less or open `Person` breaks the ADR-0026
  role→principal resolution). A `json`-typed `roles` would silently drop
  both the element typing and the min≥1 constraint.
- **The namespace reservation is semantic, not syntactic:** L1 constrains
  `namespace` only to `^[a-z][a-z0-9_]*$`
  (`services/engine/ontology_schema.json:15-18`; its description merely says
  "Matches verticals/<name>/ directory name") — a `core` token already
  passes L1. Nothing hard-binds namespace == vertical directory except the
  CLI path convention + ADR-0008 D2 prose. Two small L1 ADDITIONS are
  nonetheless required by the ratified mechanism itself: the optional
  `imports:` key (top-level `additionalProperties: false`,
  `ontology_schema.json:8`) and a widened `ref` `target` pattern (currently
  `^[A-Z][A-Za-z0-9]*$`, `:82` — a qualified `core.Person` target does not
  pass today).
- `Person` is spec-layer-only (`spec.py:1359-1378` — docstring: "Lives in
  the procedures spec layer … Human-author-only (H, ADR-0024 D3) — a
  principal is never model-emitted"). `ServicePrincipal` (`:1381-1397`,
  deliberately NO `roles`) and `PrincipalAlias` sit beside it and are NOT
  promoted. The id aliases are spec-layer strings (`RoleId`/`PersonId`/
  `ServicePrincipalId = str`, `spec.py:833,839,845`).
- ADR-0008's own deferral list (`:79-80`) puts `shared property`-class
  constructs behind a Rule-of-Three trigger ("Add when 3+ verticals request
  them") — re-argued consciously in D6, never silently overridden.

## Decision

Codify the **shared-ontology mechanism** — the home, the namespace
reservation, the `imports:` discovery/resolution grammar, the
constrained-collection type extension, and the committed runtime + DB
contract — scoped to exactly what the shared `Person` needs. ADR-0008 stays
authoritative for per-vertical grammar; this ADR EXTENDS it.

### D1 — The shared home: repo-level `ontology/core_v0.yaml` + the reserved `core` namespace (SD-F=(a))

The shared/core ontology lives at **`ontology/core_v0.yaml`** — a new
repo-level home, visibly NOT a vertical (not under `verticals/`, honoring
"shared ≠ a vertical") and NOT engine-owned (the engine is generated FROM
the ontology, never the ontology's owner).

The **`core` namespace token is RESERVED**. The reservation is **semantic**
(per the grounded finding above): L1's namespace pattern is NOT rewritten.
It is enforced as:

1. **Grammar prose (this ADR):** `namespace: core` is legal ONLY in the
   shared doc; no vertical may claim it (no `verticals/core/` directory, no
   vertical doc declaring `namespace: core`).
2. **Validator/CLI convention (PLAN-0082 Steps 2–3):** the L2 validator /
   CLI wiring refuses a vertical claiming the reserved token, and the shared
   doc itself MUST declare `namespace: core`. Fail closed.

v0 boundary: exactly ONE shared doc and ONE reserved token. No second token
(`shared`, `common`, …), no versioned/pinned imports — deferred until a
concrete need presses (D6 boundary; ADR-006 D4).

### D2 — Discovery/resolution: the explicit `imports:` key + the shared-doc pre-pass (SD-G=(b)+(c))

**The grammar surface** — a vertical `_v0.yaml` declares its dependency on
the shared doc explicitly, at top level:

```yaml
version: 0
namespace: procurement
imports: [core]          # OPTIONAL; declared, greppable — never inferred.
                         # v0: the only legal member is the reserved `core` token.
```

- L1 gains the OPTIONAL `imports` key (array of namespace tokens, unique
  items; v0 effectively `["core"]`). A doc declaring no `imports:` loads
  **byte-identically to today** — the backward-compat hard invariant
  (mirroring the ADR-0027 R2 precedent, `ontology_schema.json:5`).
- **Qualified `ref` targets:** an importing doc's `ref` property may name
  `target: core.<ObjectTypeName>` (qualified = cross-doc, resolved against
  the imported shared doc; unqualified = within-doc, unchanged). L1's
  `target` pattern widens to admit the qualified form. A qualified target
  whose namespace is NOT declared in `imports:`, or an `imports:` token that
  is not the reserved shared namespace, is an **L2 validation error — fail
  closed** (never a raw `KeyError`, `code_generator.py:161-165,433-435`).

**The resolution mechanism** — generation is two-phase:

1. **Pre-pass:** the shared doc generates ONCE, emitting ONE shared module
   set (deterministic + idempotent — the PLAN-0082 AC-3 regen bar).
2. **Vertical pass:** a vertical doc declaring `imports: [core]` resolves
   `core.*` references against the shared doc and **emits an IMPORT /
   reference** — Pydantic: an import from the shared committed module;
   SQL/ORM: a reference to the shared table — **never a re-embedded copy**
   of the shared type (the N-copies failure SD-G option (a) was rejected
   for; PLAN-0082 AC-2/AC-4).

The import graph is **depth-1 and acyclic by construction**: the shared doc
may NOT itself declare `imports:` (v0). The shared doc is validatable +
generable through the same `vero-lite` CLI surface; the exact invocation
shape (a dedicated subcommand vs a special-cased argument) is a build detail
Code records at R2 (PLAN-0082 Step 3), as is which of the seven emitters run
for the shared doc (the Pydantic + ORM emitters are the load-bearing ones).

### D3 — The type-system extension: a constrained `set` collection + the `closed:` strict-object knob (minimal — exactly what `Person` needs)

ADR-0008 D3 gains ONE collection type and ONE object-strictness knob,
scoped to the shipped `Person`'s load-bearing constraints
(`spec.py:1367,1374-1378`):

```yaml
object_types:
  Person:
    primary_key: person_id
    closed: true            # NEW (object_type-level): unknown-field rejection
    properties:
      roles:
        type: set           # NEW collection type literal
        items: string       # element type — v0: scalar literals only
        required: true
        constraints:        # REUSES the existing D2 `constraints:` sub-key
          min_length: 1
```

| Surface | Mapping |
|---------|---------|
| Pydantic | `frozenset[<item>]` + `Field(min_length=N)`; `closed: true` → `model_config = ConfigDict(extra="forbid")` |
| JSON Schema | `array` + `uniqueItems: true` + `minItems: N` |
| SQL | `JSONB` (+ `NOT NULL` when required; + `CHECK (jsonb_array_length(<col>) >= N)`) — **OQ-1 RESOLVED = (a) JSONB (Cray, s149)** |
| ORM | `Mapped[list[<item>]] = mapped_column(JSONB, …)`; set semantics + regen determinism via canonical serialization (sorted, de-duplicated array) |
| TypeScript | readonly array of the element type (build detail) |

v0 boundary of the extension (all deliberate — extend only under pressure):

- `set` only (no `list` until a concrete consumer needs order/duplicates);
  **scalar `items` only** (`string`/`int`/`float`/`bool`); no nested
  collections; no `ref` items.
- `constraints:` admits `min_length` / `max_length` for collections. L1's
  free-form `constraints` object (`ontology_schema.json:73`) already passes
  them; L2 + the emitters give them meaning.
- **The generated Pydantic layer is the LOAD-BEARING enforcement** (the
  roster parse rejects an empty or malformed role set); the DB `CHECK` is
  defense-in-depth on a table that ships empty (D5).
- The `closed:` key spelling may be renamed at R2 (e.g. `extra: forbid`);
  the SEMANTICS — emitter-expressed unknown-field rejection, never a
  hand-written shim (PLAN-0082 AC-2) — are the decision.
- The set-of-scalars SQL/ORM representation is **OQ-1 — RESOLVED = (a)
  JSONB (Cray, s149)**; the option set + tradeoff stay recorded in § Open
  Questions as the reasoning record.

### D4 — The shared `Person`: ONE authoritative, codegen-emitted TYPE; human-authored DATA (SD-E=(b-ii) + SD-H=(a) + the ADR-0024 D3 clarification)

- `Person` is defined in `ontology/core_v0.yaml` as an ADR-0008
  `object_type`: `person_id` (primary key), `name`, `roles` (the D3
  construct, min≥1), `closed: true` — carrying the spec-layer semantics
  (`spec.py:1369-1378`) including the description text and the H-partition
  provenance.
- **SD-H=(a):** the spec-layer class (`spec.py:1359-1378`) is **DELETED and
  RE-EXPORTED** from the spec-layer import path — every consumer keeps its
  import; **exactly one authoritative definition** remains (guarded by
  PLAN-0082 AC-4's grep check). The id aliases (`PersonId`/`RoleId`) stay or
  move coherently with the re-export (PLAN-0082 Step 5).
- **NOT promoted:** `ServicePrincipal` (`spec.py:1381-1397` — deliberately
  roles-less and distinct, so the approver seam cannot be reused) and
  `PrincipalAlias` stay spec-layer.
- **The ADR-0024 D3 two-axes clarification (binding reading):** the shipped
  docstrings' "never model-emitted" (`spec.py:1365`) means **LLM-emission**
  — the H partition forbids a language model synthesizing a principal or a
  binding. **Codegen-emission of the TYPE is a different axis**: a
  deterministic transform of a HUMAN-AUTHORED YAML source. Promoting the
  `Person` TYPE to codegen does NOT violate ADR-0024 D3 — the shared YAML is
  human-authored governance data, the generated type preserves the H
  provenance docstring, and roster DATA (`principals:` blocks, per-vertical)
  stays human-authored. The two axes must never be conflated: conflation
  would either wrongly forbid deterministic codegen or wrongly license LLM
  emission — both stay exactly as ADR-0024 D3 fixed them.

### D5 — The committed runtime + DB contract for the shared home (SD-I=(b))

This ADR states the CONTRACT; file paths/layout are Code's R2 call.

1. **Every RUNTIME-IMPORTED generated artifact of the shared doc lands at a
   COMMITTED destination**: (a) the shared `Person` Pydantic module (the
   SD-H re-export imports it — runtime code cannot live gitignored) and
   (b) the shared ORM module, registered by extending `_ORM_COMMITTED_DEST`
   (`code_generator.py:742`) or its successor mapping. Reference artifacts
   stay gitignored-reproducible (the ADR-0008 D5 `:101` discipline), with
   idempotent regeneration (unchanged YAML → zero diff).
2. **The DB surface:** the shared `Person` backs a **`person` table + an
   Alembic migration** (the 12th revision; the FIRST ontology-object table
   outside the energy schema). The table ships **EMPTY / empty-safe**;
   runtime principal resolution stays roster-fed; POPULATING it is
   **PLAN-0082 OQ-2** (out of scope here — Code proposes the shape at
   build, Cray ratifies), and no runtime consumer may start REQUIRING table
   population before OQ-2 resolves.
3. This **extends ADR-0008 D5's generation contract** beyond the
   per-vertical gitignored default, and **forces the deferred B1-DP-1
   second-ORM-layout decision** (`code_generator.py:736-741` — "How a 2nd
   vertical's ORM is laid out … is a deferred Rule-of-Three decision").
   PLAN-0082 recommends a separate committed module (e.g.
   `services/db/person.py`); the final layout is Code's R2 call at PLAN-0082
   Step 4.

### D6 — The Rule-of-Three re-argument: the `Person` deferral is ANSWERED; the mechanism ships at N=1 consumer, consciously

ADR-0008 `:79-80` deferred `shared property`-class constructs to a
3-verticals trigger. This ADR re-argues that deferral **openly, on the
ratified strategic ground** — it does not silently override it:

1. **The re-trigger for exactly this extraction already fired.** ADR-0026
   OQ-6 (`:116`) resolved per-vertical-`Person` WITH "an enforceable N≥2
   re-evaluation flag for the shared/core extraction" — a self-cancelling
   deferral, not a silent comment. TWO principal-bearing verticals exist
   (procurement, supply_chain), so the N≥2 condition is met; the ADR-0026
   `:164` out-of-scope gate ("genericizing `Person` … gated on the N≥2
   re-trigger") is passed **through**, not around.
2. **The `Person` PATTERN reaches N=3.** PLAN-0081 lands the 3rd
   principal-bearing vertical (`building_materials`) on the shared home —
   the Rule-of-Three count for the pattern is satisfied by the very program
   this ADR unblocks.
3. **The MECHANISM ships at N=1 consumer** (`Person` is the only shared
   object_type) — a Rule-of-Three tension **consciously accepted by Cray's
   SD-E=(b-ii) ratification**, taken with the "bigger than the hero build
   itself" framing in view (PLAN-0082 § Goal; PLAN-0081 SD-E record).

**Boundary (binding):** the deferral is answered **for `Person` only** — it
is NOT genericized. No second shared object_type is authored; no shared
`link_types`; no speculative shared-framework surface (ADR-006 D4
"concrete-first or nothing"; ADR-0031 D4 fractal discipline). A future
shared-type candidate re-opens under this grammar with its own concrete
pressure — the mechanism it inherits is ratified; the decision to use it is
not pre-granted.

### D7 — Record-keeping: the ADR-0026 supersession/closure + the ADR-0008 D5 5-vs-7 reconciliation

1. **ADR-0026 supersession + OQ-6 closure.** ADR-0026's `:89` consequence
   ("introduces no new generation surface … leaves the ADR-0008 ontology
   codegen path untouched") is **SUPERSEDED** — this ADR IS a new
   generation surface. ADR-0026 **OQ-6 is CLOSED by extraction** (`:116`).
   Both are recorded in ADR-0026's pointer note (ratified one-pass with this
   ADR). Every other ADR-0026 decision — D1–D6, the 2026-07-15 amendment,
   the run-enforcement semantics — stands unchanged.
2. **The D5 5-vs-7 drift, reconciled (recorded, not rewritten).** ADR-0008
   D5's table (`:89-101`) enumerates 5 artifacts; the shipped generator
   emits **SEVEN** (`code_generator.py:756-762` — pydantic, sql, jsonschema,
   mcp, typescript, **orm**, **context_pack**), the ORM via the
   committed-destination exception (`:736-742`), and the CLI docstring still
   says "five" (`cli.py:39`). This ADR records the **7-emitter reality as
   the operative generation-contract baseline** its shared-doc extension
   builds on — the D5 discipline itself (reference artifacts gitignored,
   runtime artifacts committed) is unchanged and is exactly what D5 above
   extends. ADR-0008's table is NOT rewritten in place (the pointer note
   flags the drift); the `cli.py:39` docstring correction is a build-time
   cleanup PLAN-0082 may fold in or Code lands as a separate chore.

## Consequences

### Positive

- **PLAN-0082 becomes buildable** (its AC-1 gate is this ADR), and PLAN-0081
  Step 9 shrinks to landing `building_materials` on an already-proven
  shared `Person`.
- **Exactly one authoritative `Person`** — the two-definition collision risk
  is structurally closed (SD-H=(a) + the AC-4 guard), and the load-bearing
  governance constraints (`roles` min≥1, unknown-field rejection) become
  **emitter-expressed grammar**, not conventions carried by a hand-written
  class.
- **Identity gets a durable, typed home + DB surface** — the `person` table
  gives the principal model a real store the moment a population story
  (OQ-2) is ratified, without re-opening the mechanism.
- **Every future shared type inherits a ratified mechanism** (home, reserved
  namespace, `imports:`, pre-pass, committed-runtime contract) instead of
  re-inventing one ad hoc — while D6's boundary keeps each future use a
  conscious decision.
- **The ADR-0026 OQ-6 deferral closes as designed** — the enforceable
  re-trigger did its job; the deferral was self-cancelling, not silently
  bypassed.

### Negative / risks (honest cost, ADR-0032 D6)

- **This is a NEW generation surface** — the change PLAN-0081 called
  "bigger than the hero build itself": a grammar key + L1 additions, a
  two-phase generator, qualified-ref resolution, a type-system extension,
  and CLI wiring. Blast radius consciously chosen by Cray (SD-E record).
- **The SD-I=(b) DB/migration blast radius, stated plainly:** the repo's
  SECOND committed generated ORM (only `energy` registers one today), its
  FIRST ontology-object table outside the energy schema, and a 12th Alembic
  revision — for a table that ships EMPTY. An empty committed table with an
  unresolved population story (OQ-2) must be actively managed or it rots
  into a confusing artifact; PLAN-0082 AC-7 pins the empty-safe bar and
  OQ-2 ownership.
- **JSONB `roles` (if OQ-1 resolves as recommended)** trades away DB-level
  element integrity and makes SQL-side role predicates containment
  operators — acceptable while the type layer is the enforcement and the
  table is a store, but a future DB-side role-query consumer re-opens the
  representation (OQ-1 records the re-trigger).
- **A mechanism shipped at N=1 consumer can be mis-shaped** — the classic
  premature-abstraction risk. Mitigated by scoping every construct to
  exactly `Person`'s needs (D1 v0 boundary, D2 depth-1, D3's `set`-only
  minimalism) and by D6's no-genericization boundary.
- **Grammar-surface growth**: more L1/L2 to maintain, and the `core`
  reservation is convention-enforced (validator/CLI), not schema-enforced —
  a validator regression could silently admit a `core`-claiming vertical;
  PLAN-0082's tests are the guard.

### Neutral

- **Governance semantics are untouched.** No change to SoD, tier-authority,
  or gate-resolve verdicts (PLAN-0082 AC-5 pins behavior preservation);
  ADR-0026's run-enforcement stands in full.
- **Rosters remain per-vertical, per-org demo DATA.** The shared home
  unifies the TYPE, never the data; no cross-vertical identity semantics
  (ADR-0026 OQ-3=(c) untouched); the `person` table is a typed STORE, not a
  cross-vertical merge.
- **ADR-0008 remains authoritative** for the per-vertical grammar; this ADR
  extends it and both carry cross-pointers.

## Alternatives Considered

### Alternative 1: A pseudo-vertical (`verticals/_shared/`) or engine-owned (`services/engine/ontology/`) home — SD-F options (b)/(c)
- **Pros:** (b) lives under the tree the tooling already walks; (c) puts the
  shared doc next to its consumer.
- **Cons:** (b) is a lie-shaped path — shared is NOT a vertical, and every
  discovery/CLI surface must special-case it forever; (c) inverts the
  "engine artifacts are generated FROM the ontology" direction.
- **Why rejected:** Cray ratified SD-F=(a) — honest topology, one reserved
  namespace, the cleanest grammar story (s148).

### Alternative 2: A two-doc merge at generate time (no pre-pass) — SD-G option (a)
- **Pros:** simplest implementation; no new module.
- **Cons:** each vertical's generated artifacts re-EMBED their own `Person`
  copy — recreating the N-copies problem at the artifact layer and
  colliding head-on with the one-authoritative-type end state (PLAN-0082
  AC-4).
- **Why rejected:** Cray ratified SD-G=(b)+(c) — the `imports:` key is the
  declared grammar surface; the pre-pass + emitted-import yields exactly ONE
  generated `Person` (s148).

### Alternative 3: Express `roles` as the existing `json` type (no type-system extension)
- **Pros:** zero grammar change; JSONB column for free.
- **Cons:** silently drops the element typing AND the min≥1 constraint —
  the exact "constraints held only by convention" failure the promotion
  exists to end; `extra="forbid"` similarly inexpressible.
- **Why rejected:** the constraints are load-bearing governance behavior
  (ADR-0026 D2 role→principal resolution); they must be emitter-expressed
  grammar (D3; PLAN-0082 AC-2), never a hand-written shim.

### Alternative 4: Keep a spec-layer `Person` (thin alias/subclass) or generate INTO `spec.py` — SD-H options (b)/(c)
- **Pros:** (b) minimal diff; (c) no re-export seam.
- **Cons:** (b) "thin" accretes logic and becomes a second definition —
  the collision AC-4 exists to prevent; (c) a committed, hand-edited engine
  module becoming partially generated is a standing hazard.
- **Why rejected:** Cray ratified SD-H=(a) — delete + re-export pins the
  single-source-of-truth end state (s148).

### Alternative 5: Pydantic-only shared `Person` — no ORM, no table, no migration — SD-I option (a)
- **Pros:** smaller blast radius; no consumer needs a `person` table today;
  matches the only-energy-has-an-ORM mirror discipline.
- **Cons:** defers the DB surface an identity model will eventually need;
  re-opens the layout question later under more pressure.
- **Why rejected:** **Cray OVERRODE the drafter's (a) recommendation to (b)
  (s148)** — classified `superseded by new info`, a conscious scope choice
  made with the DB/migration blast radius in view (PLAN-0082 § Surfaced
  Decisions). This ADR codifies (b) as the ratified contract (D5).

### Alternative 6: Genericize now — multi-doc imports, shared `link_types`, versioned import pins, a second shared object_type
- **Pros:** one coordinated construction pass; no later re-opening.
- **Cons:** every element is at N=0/1 concrete pressure; premature
  abstraction is wrong abstraction (the exact reason ADR-0024 D7 deferred
  the AT-2 generator and ADR-0031 D4 makes the discipline fractal).
- **Why rejected:** ADR-006 D4 is non-negotiable ("concrete-first or
  nothing"); D6's boundary keeps the mechanism scoped to `Person`.

## Open Questions

Surfaced for Cray to adjudicate at ratification (option set + a
recommendation; not silently resolved — the ADR-0026 house pattern).

- **OQ-1 — the set-of-SCALARS SQL/ORM representation for `roles`: JSONB
  column vs normalized join table.** Options: **(a) JSONB** — one column
  (`roles JSONB NOT NULL CHECK (jsonb_array_length(roles) >= 1)`), ORM
  `Mapped[list[str]]` over `JSONB`, canonical sorted/de-duplicated
  serialization for regen determinism; **(b) a normalized `person_role`
  join table** (`person_id`, `role`, row-unique). **Recommendation: (a)
  JSONB.** Reasons: `RoleId` is a ratified FREE STRING with no referent
  table (the ADR-0026 2026-07-15 amendment's rank-as-authored-data stance —
  no engine rank primitive), so a join table adds relational ceremony with
  **no referential-integrity target to gain**; (b) re-opens the
  ADR-0008 D4 deferred join-table-shaped construct (`many_to_many` —
  "defer until 3+ verticals need it") for a table that ships EMPTY; and the
  `person` table is a typed STORE, not a query surface (PLAN-0082 OQ-2 /
  AC-7), with the generated Pydantic layer as the load-bearing enforcement.
  **Tradeoff, honestly:** (a) loses DB-level element typing + row-level
  uniqueness and makes SQL role predicates containment operators
  (`roles ? 'dept_head'`); (b) buys clean relational queries + per-row
  integrity at the cost of a second table, a wider migration surface, and
  the construct-deferral re-open. **Re-trigger:** a real DB-side role-query
  consumer (e.g. an audit dashboard filtering approvers by role in SQL)
  re-opens this as its own decision. *Cray decision (not a Code judgment):
  it fixes the first non-energy ontology-object schema shape — hard to
  unwind after the migration ships, and it touches the D4 deferral.*
  **→ RESOLVED (Cray, s149, typed AskUserQuestion) = (a) JSONB.** The
  recommendation stands as ratified: `RoleId` is a free string with no
  referent table, so a join table gains no referential-integrity target and
  would re-open the ADR-0008 D4 join-table deferral for a table that ships
  empty; a real DB-side role-query consumer re-opens the representation as
  its own decision. The option set + tradeoff above are KEPT as the
  reasoning record.

## References

- **PLAN-0082** (`docs/plans/0082-shared-ontology-mechanism-and-person-promotion.md`)
  — the implementing PLAN: the ratified SD record (§ Surfaced Decisions),
  AC-1..AC-7, Steps 2–7, OQ-2 (the population story). Parent: **PLAN-0081**
  (`docs/plans/0081-building-materials-governed-credit-hero.md` — the SD-E
  record `:643-683`; its Step 9 shrinks to the `building_materials`
  migration).
- **ADR-0008** — D2 namespace grammar `:37-63` (literal `:41`); D3 type
  table `:65-77`; the `shared property` deferral `:79-80`; D5 generation
  contract `:89-101` (gitignore line `:101`). Extended by this ADR; carries
  the pointer note.
- **ADR-0026** — the superseded `:89` consequence; the `:95` ontology-layer
  tension; OQ-6 `:116` (closed by D6/D7); Implementation Note 1 `:157`; the
  `:164` out-of-scope gate. Carries the pointer note.
- ADR-006 (D4 Rule of Three) · ADR-0024 (D3 G-H-D partition — the D4
  two-axes reading) · ADR-016 (the spec layer re-exporting the generated
  type) · ADR-0031 (D4 fractal discipline; closed-governed vocabulary) ·
  ADR-0032 (D6 honest-cost) · ADR-009 D1/D2 · ADR-012 D4.3 / ADR-013.
- Code anchors (verified on `main` b93c1e1, 2026-07-18, by this drafter):
  `services/engine/code_generator.py:71-76` (`load_doc`), `:161-165` (SQL
  `ref`), `:433-435` (ORM `ref`), `:736-741` (B1-DP-1 deferral comment),
  `:742` (`_ORM_COMMITTED_DEST`), `:745-763` (`generate_all`), `:756-762`
  (the 7 emitters); `services/engine/cli.py:22-23,37-52` (path hard-wire +
  `generate`, docstring "five" at `:39`);
  `services/engine/ontology_schema.json:8,15-18,73,82` (top-level
  `additionalProperties`, namespace pattern, free-form `constraints`,
  `target` pattern); `services/engine/procedures/spec.py:833,839,845` (id
  aliases), `:1359-1378` (`class Person` — `extra="forbid"` `:1367`, PK
  `:1369`, `roles` `:1374-1378`), `:1381-1397` (`ServicePrincipal`, NOT
  promoted).
- CLAUDE.md §7 (no `Co-Authored-By`) · §8 (ADR merged before related
  implementation PR — the PLAN-0082 AC-1 gate).

## Implementation Notes

**PLAN-0082 owns the build** (Steps 2–7): D1 + D2 → Steps 2–3 (home, L1/L2
additions, validator/CLI reservation enforcement, pre-pass + qualified-ref
resolution); D3 + D4 → Steps 2 + 5 (the `set`/`closed:` emitters; the
delete-and-re-export reconciliation with the AC-4 guard); D5 → Step 4 + AC-7
(committed destinations, the forced B1-DP-1 layout call at R2, the `person`
table + 12th Alembic revision, empty-safe; population = OQ-2); the
procurement + supply_chain migrations + the OQ-6-marker transform → Step 6
(SD-K(i)/(ii)); the verification pass → Step 7. PLAN-0081 lands the 3rd
vertical on the shared home (its Step 9 residue).

**Ordering (binding):** this ADR + BOTH pointer notes (ADR-0008, ADR-0026)
merge — ratified in ONE pass, never flip-Status-then-edit-body — **before**
any grammar/codegen/ORM/migration change ships (CLAUDE.md §8; PLAN-0082
AC-1).

Status flipped Proposed → Accepted at Cray's ONE-PASS ratification (s149,
together with both pointer notes — the top **Status**/**Ratified** lines are
the source of truth); Code applies + commits via a `docs/*` PR (ADR-009 D2).
AI-assisted (`plan-drafter` subagent); no `Co-Authored-By` per CLAUDE.md §7.

---

> **Drafting provenance (ADR-012 D4.3 / ADR-013 OQ-1).** Authored by the
> in-harness `plan-drafter` subagent under ADR-013 D1 phased authority, on
> Code's dispatch executing **Cray's OQ-1 ratification (s148, typed
> AskUserQuestion): ONE new shared-ontology ADR** + two pointer-note edits.
> The eight content obligations and the ratified SD inputs
> (SD-E/F/G/H/I/K, s147–s148) are codified, not re-litigated; ONE new open
> question is surfaced (OQ-1, the set-of-scalars representation — flagged
> per the dispatch, recommendation (a) JSONB). Every `file:line` above was
> read from disk by this drafter on `main` b93c1e1, 2026-07-18. One
> refinement beyond the dispatch fact-pack, grounded on disk: the L1 `ref`
> `target` pattern (`ontology_schema.json:82`) does not admit a qualified
> `core.Person` target — the namespace RESERVATION stays semantic as
> ratified, but the `imports:` key + the qualified-target form are honest
> L1 additions (D2). No `tests/` file written; no PLAN authored; no shell
> run; no commit. Author = `plan-drafter`; independent review = Code (R2)
> at PR; ratification = Cray. Author≠reviewer separation: **INTACT**.
> Uncommitted draft — Code commits per ADR-009 D2.
