# PLAN-0050: ADR-0027 R2 grammar amendment — build the four optional semantic-enrichment ontology constructs (synonyms, sample_values, verified_queries, metric grain)

**Status:** Ready for execution (SD-A…SD-D ratified as-recommended 2026-07-04)
**Owner:** both (in-harness `plan-drafter` authors this PLAN; Code commits + executes per ADR-009 D2)
**Created:** 2026-07-04
**Related ADRs:** ADR-0027 (the AUTHORITATIVE spec — Accepted 2026-07-04; D1–D5 + SD-1…SD-7 all ratified as-recommended; **this PLAN renders D1–D5 into code**, SD-6's named follow-up build); ADR-0021 (the DIRECT `quantity_bindings` grammar-amendment precedent this mirrors — L1 sub-schema + Pydantic `default_factory` projection + `_check_*` L2 pass); ADR-008 (YAML ontology specification — **D2/D3 amended** by ADR-0027 to admit the four constructs; D5 generator, D6 L1+L2); ADR-0024 (governed ≠ generated — machine drafts, human canonicalizes; the D3 standing rule); ADR-006 (vertical plugin architecture / Rule of Three); ADR-005 (OCT pivot — energy first); ADR-009 D1/D2 (drafter drafts, Code commits); ADR-012 D4.3 (author≠reviewer disclosure); ADR-013 D1 (plan-drafter phased authority)
**Related Plans:** PLAN-0049 (the R1 semantic-context-pack emitter — steps {1,2,4,5} shipped; this PLAN is the remaining R2 follow-up carved out by PLAN-0049 SD-1); PLAN-0026 (the ADR-0021→PLAN pattern this mirrors — `measured_kind` + `quantity_bindings` build); PLAN-0047 Step 7 (the live CI gate every step's PR runs)

> **Disclosure (ADR-012 D4.3).** Drafted by the in-harness `plan-drafter`
> subagent (ADR-013 D1 phased authority) from Code's session-96 dispatch, over
> the Accepted ADR-0027 (the authoritative spec) + the ADR-0021→PLAN-0026
> precedent + the on-disk code surfaces (`ontology_meta.py`,
> `ontology_schema.json`, `ontology_validator.py`, `code_generator.py`). The
> ADR-author (ADR-0027) and this PLAN-author are the same in-harness subagent
> across two fresh dispatches; **Code's R2 review at PR merge + Cray's
> ratification are the independent checks.** Separation noted, not asserted.

---

## Goal

Build the **ADR-0027 R2 grammar amendment**: implement the four OPTIONAL
semantic-enrichment ontology constructs that ADR-0027 (Accepted 2026-07-04, all
SD-1…SD-7 ratified as-recommended) decided but deferred to this named follow-up
PLAN (SD-6). The four constructs — **`synonyms`** (lang-keyed th/en map, at
object-type AND property level), **`sample_values`** (property-level, closed
filtering set when populated), **`verified_queries`** (`{question, answer}` NL
pairs), and metric **`grain`/join-path** (optional attrs on the existing
ADR-0021 `quantity_bindings`) — are rendered into code by mirroring the
`quantity_bindings` shape exactly: an L1 optional sub-schema per construct
(`ontology_schema.json`), a Pydantic projection with `default_factory` for
backward-compat (`ontology_meta.py`), an L2 `_check_*` consistency pass per
construct (`ontology_validator.py`), then a backfill of the two v1 verticals
(energy-v1 + supply-chain-v1). The R1 emitter (`emit_context_pack`) consumes the
constructs **for free** on its shipped degrade path — this PLAN changes no
emitter code but proves the degrade path fills in once a backfilled value exists.

The **hard invariant** (ADR-0027 D2): every field is OPTIONAL, so an ontology
declaring none loads byte-identically to today, generates the same artifacts,
and validates unchanged. This PLAN's grammar + validators land and stay green
**with zero backfill first**; the backfill is separate.

## The load-bearing frame (from ADR-0027 — stated, NOT re-opened)

The DESIGN is fully ratified in ADR-0027 (SD-1…SD-7 as-recommended). This PLAN
does **not** re-open any of it; the construct shapes below are FIXED inputs:

- **`synonyms`** — lang-keyed map `{th: [...], en: [...]}` (SD-2); attachable at
  BOTH object-type AND property level (SD-1). The th/en separation is the moat
  (F9 — Thai is in no benchmark found).
- **`sample_values`** — property-level (SD-1); semantics = **closed filtering
  set when populated** (SD-3); DISTINCT from an enum property's `values` (a prop
  may have neither, either, or both by intent).
- **`verified_queries`** — object-type-level (SD-B ratified: object-type-level)
  (SD-1 / SD-4); shape = `{question, answer}` NL pair (least-coupling v1; **NO
  IR/QueryFilter binding**).
- **metric `grain` / join-path** — OPTIONAL attrs on the existing ADR-0021
  `quantity_bindings` construct (SD-5): each binding gains an OPTIONAL `grain` +
  OPTIONAL join-path; **NOT** a parallel metrics block.
- **Enforcement (SD-7):** L1 shape (optional sub-schema per construct) + L2
  consistency (`_check_*` per construct, mirroring `_check_quantity_bindings`).

The only NEW decisions this PLAN surfaced were BUILD-level (step batching,
one-PR-per-vertical vs both, fixture strategy, and the SD-4-latitude
object-type-vs-top-level placement for `verified_queries`) — all ratified
as-recommended 2026-07-04; see *Surfaced decisions*.

## Acceptance Criteria

- [ ] **AC-1 — L1 shape for all four constructs (`ontology_schema.json`).** The
  L1 JSON Schema gains, mirroring the existing `quantityBinding` `$def`:
  (a) a `synonyms` optional sub-schema (lang-keyed map `{th: [str], en: [str]}`,
  `additionalProperties: false` on the lang keys) referenced from BOTH the
  `objectType` and the `property` `$def`; (b) a `sample_values` optional array on
  the `property` `$def`; (c) a `verified_queries` optional array of
  `{question, answer}` objects at object-type level (SD-B ratified:
  object-type-level); (d) an OPTIONAL `grain` +
  OPTIONAL join-path on the `quantityBinding` `$def`. Each is OPTIONAL (absent =
  valid). **Oracle:** a schema-validation test asserts a YAML declaring each
  construct passes L1, and a malformed one (e.g. `synonyms` as a flat list, an
  extra lang key, a `verified_query` missing `question`) is REJECTED.
- [ ] **AC-2 — Pydantic projection (`ontology_meta.py`).** `PropertyMeta` gains
  optional `synonyms` + `sample_values` attrs; `ObjectTypeMeta` gains optional
  `synonyms` + `verified_queries` attrs; `QuantityBinding` gains optional
  `grain` + join-path attrs — each with `default_factory` (or `None` default) so
  an absent field projects to the empty/None default, exactly the
  `quantity_bindings: list[...] = Field(default_factory=list)` pattern. A new
  `VerifiedQuery` model and a typed `Synonyms` model (SD-D ratified: typed model)
  mirror `QuantityBinding`.
  `load_ontology_meta` populates them from the raw YAML (mirroring the existing
  `bindings = [...]` comprehension). **Oracle:** a unit test loads a backfilled
  vertical and asserts the projected values; a second loads an un-enriched fixture
  and asserts every new attr is the empty/None default.
- [ ] **AC-3 — L2 consistency (`ontology_validator.py`).** A `_check_*` pass per
  construct, mirroring `_check_quantity_bindings` (:291): (a) `_check_synonyms` —
  well-formedness + (property-level) the synonym'd property exists on the type;
  (b) `_check_sample_values` — the sample-valued property exists, and (SD-C
  ratified) when the property is also an enum the samples must be ⊆ `values`
  (orthogonal only for non-enum props); (c) `_check_verified_queries` — non-empty
  `question` + `answer` (v1 = least coupling, so NO referent check into the NL-IR;
  optional: if the query names an object_type/property, it must resolve);
  (d) the `grain`/join-path check folds into `_check_quantity_bindings` (grain
  well-formed; a named join-path resolves to a real ref/link). Each **no-ops when
  its key is absent** (the D2 invariant). **Oracle:** per-construct unit tests
  with a well-formed pass + a deliberately-broken fail (e.g. `verified_queries`
  referencing a non-existent property; a `sample_values` on a missing property).
- [ ] **AC-4 — D2 BACKWARD-COMPAT HARD INVARIANT (explicit, tested).** An
  ontology YAML that declares NONE of the four constructs loads
  **byte-identically** to today, generates the same five artifacts
  byte-for-byte, and validates unchanged. **Oracle (decisive):** run
  `uv run vero-lite generate energy` **before** any energy backfill (Step 4) and
  capture the generated artifacts; assert the grammar+validator+projection
  changes (Steps 1–3) leave every generated artifact byte-identical and every L1
  +L2 check green with zero backfill. This is the gate that lets R2 land without
  touching any vertical. A test asserts an un-enriched ontology's L2 findings
  list is unchanged (the new `_check_*` passes all no-op).
- [ ] **AC-5 — Backfill energy-v1 (`energy_v0.yaml`).** The energy ontology
  gains curated, human-canonicalized values for the four constructs on a
  representative slice (e.g. `Asset.asset_type` th/en synonyms + `sample_values`;
  `OperationalEvent` `verified_queries`; a `grain` on the `temperature`/`current`
  `quantity_bindings`). All values pass L1+L2. `uv run vero-lite generate energy`
  reports **"OK:"**, regenerates the committed `services/db/models.py` (energy)
  + gitignored artifacts, artifact mtime advances. **No Alembic migration** — the
  four constructs are ontology-meta, not asset DB columns (verified s96: enum-
  value adds + metadata constructs need no migration; `alembic check` drift-guard
  stays green).
- [ ] **AC-6 — Backfill supply-chain-v1 (`supply_chain_v0.yaml`).** Same curated
  backfill on the supply-chain vertical (the natural batch partner per ADR-0027
  D5 / research R2). Passes L1+L2; `uv run vero-lite generate supply_chain`
  reports "OK:"; no migration. (SD-A ratified: one PR per vertical — AC-5 (energy)
  and AC-6 (supply-chain) land in separate PRs.)
- [ ] **AC-7 — Emitter POPULATES for free (the forward-reference proof).** With
  the constructs + a backfilled value in place (AC-5), `emit_context_pack` — **with
  ZERO emitter code change** — now populates the previously-degraded sections
  (synonyms / sample values / verified queries / metric grain) in the generated
  context pack, and the "not yet populated — pending the R2 meta-schema follow-up"
  degrade note (`code_generator.py` :646–653) no longer fires for the enriched
  vertical. **Oracle:** a test emits the pack for a backfilled fixture and asserts
  the enrichment sections are present + populated; a second emits for an
  un-enriched fixture and asserts the degrade note still fires (both paths held).
  If the emitter's degrade-path READ does not actually surface a section that a
  backfilled value should populate, that is a genuine emitter gap → surface it
  (do not silently patch the emitter — ADR-0027 says zero emitter change; a real
  gap is a finding for Code + Cray, see Residual note IN-1).
- [ ] **AC-8 — Offline suite green + quality bar (CLAUDE.md §8 / PLAN-0047 Step
  7 CI gate).** Every step's PR is green under the live CI gate: `ruff` +
  `ruff-format` + `mypy --strict` + full suite w/ postgres + `alembic upgrade
  head` + `alembic check` drift-guard. All new code carries type hints + tests;
  the ontology tests are **offline** (no live Ollama — pure schema/projection/
  validator/emitter unit tests). `uv run vero-lite generate <vertical>` verified
  via "OK:" + artifact mtime (NOT `python -m` — that is a silent no-op).

## Out of Scope

- ❌ **R3 (schema-guided LLM bootstrap) and R4 (usage-mined loop)** — ADR-0027 D3
  keeps these OUT. These are curated, human-canonicalized fields (governed ≠
  generated, ADR-0024 D3/D6); no auto-write, no machine promotion into the
  governed YAML in this PLAN. Later, post-partner.
- ❌ **Any IR / `QueryFilter` binding for `verified_queries`** — ADR-0027 SD-4
  ratified the **least-coupling v1** (`{question, answer}` NL pair only). NO
  coupling to `services/engine/nl_query.py`'s internal `StructuredQuery` /
  `QueryFilter` shape; the answer side stays natural-language / short grounded
  fact. Deferred until a consumer needs it.
- ❌ **Any emitter (`emit_context_pack`) code change** — ADR-0027's forward-
  reference is that the R1 degrade path reads these fields FOR FREE. This PLAN
  proves it (AC-7); it does not modify the emitter. (A genuine emitter gap is a
  surfaced finding, not an in-scope patch — IN-1.)
- ❌ **N:M / DB-column / asset-schema changes → no Alembic migration.** The four
  constructs are ontology-META (synonyms/samples/verified-queries/grain), not new
  asset columns. If a construct is ever discovered to require a real column, that
  is a separate PLAN with its own migration (out of scope here).
- ❌ **A parallel `metrics` block** — SD-5 ratified attaching `grain`/join-path to
  the existing `quantity_bindings`, NOT inventing a first-class metrics construct.
- ❌ **Backfilling the non-v1 verticals** (aquaculture, procurement) — ADR-0027
  D5 names the v1 pair (energy + supply-chain) as the batch boundary; other
  verticals are a later curation pass. (Their ontologies still load unchanged by
  the D2 invariant — AC-4.)
- ❌ **Amending ADR-0027's ratified DESIGN SDs** — SD-1…SD-7 are FIXED. Only new
  BUILD-level choices are surfaced here (SD-A…SD-D).

## Steps

Ordered, each step small and reviewable, each with its offline oracle. The
grammar + validators land and go green **with ZERO backfill first** (AC-4 gate)
before any vertical is touched — so the D2 backward-compat invariant is proven
independently of the curated content.

### Step 1 — L1 shape: add the four optional sub-schemas (`ontology_schema.json`) → AC-1

Add, mirroring the existing `quantityBinding` `$def` + its optional array on
`objectType`: (a) a `synonyms` `$def` (lang-keyed `{th, en}` map, both optional,
`additionalProperties: false`) referenced from BOTH `objectType` and `property`;
(b) `sample_values` (optional array of strings) on `property`; (c) a
`verifiedQuery` `$def` (`{question, answer}`, both required, non-empty) + a
`verified_queries` optional array at object-type level (SD-B ratified:
object-type-level); (d) OPTIONAL `grain` +
join-path on the `quantityBinding` `$def`. All OPTIONAL. **Oracle:** L1-validation
test — a fully-enriched YAML passes; malformed ones (flat-list `synonyms`, extra
lang key, `verified_query` missing `question`) are REJECTED; a bare YAML still
passes. `additionalProperties: false` must still hold everywhere it does today.

### Step 2 — Pydantic projection (`ontology_meta.py`) → AC-2

Add a `VerifiedQuery` model and a typed `Synonyms` model (SD-D ratified: typed
model). Extend `PropertyMeta` (+`synonyms`,
+`sample_values`), `ObjectTypeMeta` (+`synonyms`, +`verified_queries`), and
`QuantityBinding` (+`grain`, +join-path) with `default_factory`/`None` defaults.
Extend `_property_meta` + the `load_ontology_meta` comprehensions to populate
them (mirror the `bindings = [...]` block). **Oracle:** load-projection unit
tests — a backfilled fixture projects the values; an un-enriched fixture projects
every new attr to its empty/None default (the D2 half of AC-4 at the projection
layer).

### Step 3 — L2 consistency: one `_check_*` per construct (`ontology_validator.py`) → AC-3

Add `_check_synonyms`, `_check_sample_values`, `_check_verified_queries`, and
fold `grain`/join-path into `_check_quantity_bindings`, each mirroring the
existing pass (:291): a defined referent (property exists; enum-sample subset when
the property is also an enum — SD-C ratified; join-path resolves to a real
ref/link), well-formedness, and a
**no-op-when-absent** guard. Wire each into `_validate_l2`. **Oracle:** per-check
unit tests — a well-formed pass + a deliberately-broken fail (non-existent
referent), and an absent-key no-op assertion.

### Step 4 — Prove the D2 backward-compat HARD INVARIANT (zero backfill) → AC-4 (GATE)

**Before touching any vertical:** capture `uv run vero-lite generate energy` +
`generate supply_chain` artifacts on the un-enriched ontologies; assert Steps 1–3
leave every generated artifact byte-identical, L1+L2 green, `alembic check` clean.
This is the decisive gate — the grammar can land on `main` with the two verticals
still bare and nothing changes. **Oracle:** a byte-identity / L2-findings-unchanged
test on an un-enriched ontology (the new `_check_*` all no-op). Steps 1–4 are one
reviewable unit ("grammar + validators, zero backfill"); the backfill is separate.

### Step 5 — Backfill energy-v1 (`energy_v0.yaml`) → AC-5

Add curated th/en `synonyms` (object-type + property level), `sample_values`
(closed filtering set on a representative property), `verified_queries` (a small
known-good `{question, answer}` set on `OperationalEvent`/`Asset`), and a `grain`
on selected `quantity_bindings`. Human-canonicalized values (D3 governed ≠
generated). Run `uv run vero-lite generate energy` → "OK:", regenerated
committed `models.py` + gitignored artifacts, mtime advances, **no migration**.
**Oracle:** L1+L2 green on the enriched YAML; generate "OK:"; `alembic check`
still clean (metadata-only change, verified s96).

### Step 6 — Backfill supply-chain-v1 (`supply_chain_v0.yaml`) → AC-6

Same curated backfill on the supply-chain vertical (the ADR-0027 D5 batch
partner). **Oracle:** L1+L2 green; `generate supply_chain` "OK:"; no migration.
SD-A ratified: **one PR per vertical** — Step 5 (energy) and Step 6
(supply-chain) are separate PRs.

### Step 7 — Prove the emitter POPULATES for free (zero emitter change) → AC-7

With a backfilled value present (Step 5), assert `emit_context_pack` now
populates the enrichment sections in the generated context pack and the degrade
note no longer fires for the enriched vertical — **with no emitter edit**.
**Oracle:** emit for a backfilled fixture → enrichment sections present +
populated; emit for an un-enriched fixture → degrade note still fires (both held).
If a backfilled value does NOT surface (the degrade-path read is incomplete for
that construct), that is a genuine emitter gap → surface as a finding for Code +
Cray (IN-1), do NOT silently patch the emitter (ADR-0027 = zero emitter change).

### Step 8 — Handback → Code commits + reconciles

Hand the uncommitted PLAN + draft diffs back to Code. **plan-drafter does not
commit** (ADR-009 D2). Code R2-reviews, commits each step on a `feat/*` (or
`docs/*` for the PLAN itself) branch + PR (CLAUDE.md §7), the live CI gate
(PLAN-0047 Step 7) runs on every PR, merges after Cray review, executes. On
completion `git mv docs/plans/0050-*.md docs/plans/done/`.

## Verification

- **AC-1 / AC-3 (L1+L2):** schema + validator unit tests — enriched passes,
  malformed/broken-referent rejected, bare/absent no-ops.
- **AC-2:** projection unit tests — backfilled projects values; un-enriched
  projects empty/None defaults.
- **AC-4 (the D2 gate):** byte-identity of generated artifacts + unchanged L2
  findings on an un-enriched ontology after Steps 1–3, with zero backfill; the
  decisive proof R2 lands without touching any vertical.
- **AC-5 / AC-6 (backfill):** `uv run vero-lite generate <vertical>` reports
  "OK:", artifact mtime advances, `alembic check` drift-guard stays green (no
  migration — metadata-only, verified s96); NOT `python -m` (silent no-op).
- **AC-7 (emitter for free):** the context pack populates the enrichment sections
  for a backfilled vertical with zero emitter change; the degrade note still
  fires for an un-enriched one.
- **AC-8 (CI gate):** every PR green under `ruff` + `ruff-format` + `mypy
  --strict` + full suite w/ postgres + `alembic upgrade head` + `alembic check`
  (PLAN-0047 Step 7); ontology tests offline (no live Ollama).

## Implementation notes

- **IN-1 — the emitter degrade path is READ-ONLY for this PLAN.** ADR-0027's
  forward-reference (`code_generator.py` :539–544, :646–653) is that the emitter
  already reads the four fields on its degrade path and will populate them once
  they exist. Step 7 PROVES this. If a backfilled value does not surface, do NOT
  edit the emitter to fix it — surface the gap as a finding (a real emitter miss
  is a Code + Cray decision, since ADR-0027 asserted zero emitter change). This
  boundary is load-bearing: it protects the "R1 gains enrichment with no emitter
  change" consequence ADR-0027 recorded.
- **IN-2 — mirror `quantity_bindings` literally.** The whole PLAN is a
  four-fold repeat of one proven pattern (L1 `$def` + optional array/attr →
  Pydantic `default_factory` projection → `_check_*` no-op-when-absent). Do not
  invent a new shape; the `QuantityBinding` triple (schema :90–98, meta :35–39
  + :110–114, validator :291–336) is the template for each construct.
- **IN-3 — no migration expected.** All four constructs are ontology-META (they
  live in the YAML + its projection + the generated reference artifacts + the
  committed ORM's non-column surfaces), not asset DB columns. Verified s96: enum-
  value adds + metadata constructs need no Alembic migration. If a backfill
  unexpectedly changes a real column in `services/db/models.py`, STOP — that is
  out of scope and a separate migration PLAN.

## Surfaced decisions (SD-N) — Cray adjudicates (BUILD-level only; the DESIGN SDs are ratified in ADR-0027)

> The DESIGN (field placement SD-1, `synonyms` shape SD-2, `sample_values`
> semantics SD-3, `verified_queries` shape SD-4, `grain` placement SD-5, build
> sequencing SD-6, enforcement depth SD-7) is **fully ratified in ADR-0027 —
> not re-opened here.** Only genuinely-new BUILD-level choices follow.

**Ratified 2026-07-04: SD-A…SD-D all confirmed as-recommended (none overridden).**

### SD-A — One PR for both vertical backfills, or one PR per vertical?

- **Question:** land energy-v1 + supply-chain-v1 backfills (Steps 5–6) in ONE PR,
  or TWO (one per vertical)?
- **Code recommendation:** **one PR per vertical** — each is an independent
  curated-content change with its own generate + no-migration verification, and a
  per-vertical diff is easier for Cray to review the hand-authored Thai synonyms
  against. Reason: curation is the manual-labor / correctness-sensitive part
  (ADR-0027 D3), and smaller diffs = tighter review of the moat content.
- **Alternatives:** one PR for both (fewer round-trips, but a larger curated diff
  to review); or grammar+validators+energy in one PR and supply-chain follow-on.
- **Why this is Cray's call:** it is a review-granularity + curation-batching
  judgment on hand-authored moat content, not a code-mechanics detail.
- **Ratified 2026-07-04 — as-recommended.**

### SD-B — `verified_queries` at object-type level vs top-level (within the SD-4 latitude)?

- **Question:** ADR-0027 SD-4 ratified the `{question, answer}` shape but left
  "object-type-level (or top-level)" as latitude. Attach `verified_queries` under
  each `objectType`, or as a top-level ontology array?
- **Code recommendation:** **object-type-level** — it keeps each known-good query
  next to the type it exercises (locality, easier L2 referent checks, mirrors how
  `quantity_bindings` lives under its type), and a query spanning types can still
  name its primary type. Reason: co-location with the type simplifies the
  `_check_verified_queries` referent pass and matches the existing per-type home.
- **Alternatives:** top-level array (better for cross-type / whole-ontology
  queries; looser coupling to any one type).
- **Why this is Cray's call:** it sets the grammar placement the L1 schema + L2
  check + backfill all implement — a shape decision within ADR-0027's explicit
  SD-4 latitude, with two defensible cuts.
- **Ratified 2026-07-04 — as-recommended.**

### SD-C — `sample_values` on an enum property: enforce samples ⊆ `values` in L2, or leave orthogonal?

- **Question:** ADR-0027 SD-3 ratified `sample_values` as DISTINCT from an enum's
  `values` (a prop may have neither/either/both by intent). When a property has
  BOTH, should `_check_sample_values` (L2) require the samples to be a subset of
  `values`, or treat them as fully orthogonal?
- **Code recommendation:** **enforce samples ⊆ `values` when the property is also
  an enum** — SD-3's "closed filtering set when populated" reading means a sample
  outside the closed enum set is almost certainly an authoring error, and the
  emitter's "CLOSED — refuse, do not guess" framing argues against silent
  divergence. Reason: catches a real curation mistake cheaply; the "distinct"
  ratification is about non-enum props, where no `values` exists to check against.
- **Alternatives:** fully orthogonal (SD-3 said "distinct" — a strict reading
  admits an enum prop whose samples intentionally differ; but no motivating case
  is known).
- **Why this is Cray's call:** it is an L2-strictness interpretation of the SD-3
  "distinct-but-compatible" ratification — a validator-semantics choice that
  could reject a (rare) intentional divergence.
- **Ratified 2026-07-04 — as-recommended.**

### SD-D — Typed `Synonyms` Pydantic model, or a raw `dict[str, list[str]]` projection?

- **Question:** in `ontology_meta.py`, project `synonyms` as a typed `Synonyms`
  model (`th: list[str]`, `en: list[str]`) mirroring `QuantityBinding`, or as a
  raw `dict[str, list[str]]`?
- **Code recommendation:** **a typed `Synonyms` model** — it mirrors the
  `QuantityBinding` precedent (IN-2), gives mypy `--strict` a concrete shape, and
  makes the th/en moat first-class in the projection. Reason: parity with the
  existing typed projection + strict-mypy legibility; the lang keys are a fixed,
  known set.
- **Alternatives:** raw dict (fewer new symbols; but loses the typed shape the
  rest of the meta projection has).
- **Why this is Cray's call:** it sets the public shape of the `OntologyMeta`
  projection the `/meta` endpoint + emitter read — a contract-surface choice, same
  class as adding `QuantityBinding` was.

## References

- **ADR-0027** (`docs/adr/0027-ontology-semantic-enrichment-fields.md`) — the
  AUTHORITATIVE spec; D1 (four constructs), D2 (backward-compat HARD INVARIANT),
  D3 (governed ≠ generated), D4 (L1+L2 enforcement), D5 (grammar, not impl —
  build = this PLAN); SD-1…SD-7 all ratified as-recommended 2026-07-04.
- **Surfaces the follow-up PLAN will touch** (mirrored from ADR-0027 References):
  `services/engine/ontology_schema.json` (L1),
  `services/engine/ontology_meta.py` (`PropertyMeta` / `ObjectTypeMeta` /
  `QuantityBinding` optional attrs, mirroring `QuantityBinding`),
  `services/engine/ontology_validator.py` (`_check_*` mirroring
  `_check_quantity_bindings` :291), and the v1 vertical backfill
  (`verticals/energy/ontology/energy_v0.yaml`,
  `verticals/supply_chain/ontology/supply_chain_v0.yaml`).
  `services/engine/code_generator.py::emit_context_pack` (:539–544 degrade-path
  note, :646–653 the "not yet populated" note) consumes them **for free**.
- **ADR-0021** + **PLAN-0026** (`docs/plans/done/0026-*.md`) — the DIRECT
  precedent: `quantity_bindings` / `QuantityBinding` / `measured_kind` added via
  L1 sub-schema + `default_factory` Pydantic projection + `_check_quantity_bindings`
  L2 pass. PLAN-0050 follows the SAME shape four-fold.
- **ADR-008** (D2/D3 grammar — amended by ADR-0027; D5 generator; D6 L1+L2),
  **ADR-0024** (governed ≠ generated — the D3 standing rule; R3/R4 out of scope),
  **ADR-006** (Rule of Three), **ADR-005** (energy first).
- **PLAN-0049** (the R1 emitter + the SD-1 carve-out originating ADR-0027; steps
  {1,2,4,5} shipped, R2 = this PLAN). **PLAN-0047 Step 7** (the live CI gate).
- **CLAUDE.md** §1 (semantic layer = the moat; Rule of Three), §8 (ADR Accepted
  before impl PR — ADR-0027 Accepted 2026-07-04, satisfied). ADR-009 D1/D2
  (drafter drafts, Code commits), ADR-012 D4.3 (author≠reviewer disclosure),
  ADR-013 D1 (plan-drafter phased authority).
- **Toolchain notes:** `uv run vero-lite generate <vertical>` (console script,
  NOT `python -m` — silent no-op); verify "OK:" + artifact mtime; no Alembic
  migration for metadata constructs (verified s96); enrichment tests are offline
  (no live Ollama).

---

*PLAN-0050 builds the ADR-0027 R2 grammar amendment — the four optional
semantic-enrichment constructs (synonyms th/en, sample_values, verified_queries,
metric grain/join-path) — by mirroring the ADR-0021 `quantity_bindings` shape
four-fold: L1 sub-schema → Pydantic `default_factory` projection → `_check_*` L2
pass → backfill energy-v1 + supply-chain-v1. The D2 backward-compat HARD
INVARIANT (absent = byte-identical) is proven with zero backfill first (AC-4
gate); the R1 emitter populates the enrichment FOR FREE with no emitter change
(AC-7). R3/R4, any IR/QueryFilter binding, and DB-column/migration changes are
OUT. The design is ratified in ADR-0027 — only build-level SD-A…SD-D are Cray's
to adjudicate.*

*Drafted by the in-harness `plan-drafter` (ADR-013 D1) on Code's 2026-07-04
dispatch; Code R2-reviews, commits (ADR-009 D2), and executes. AI-assisted; no
`Co-Authored-By` per CLAUDE.md §7.*
