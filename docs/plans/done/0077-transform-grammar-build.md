# PLAN-0077: transform-grammar build — the typed declarative `transform` StepKind (renders ADR-0031 D3 row-1 + the ADR-016 Q4 OQ-3 transform home)

**Status:** Proposed — SD-1..SD-8 await Cray ratification via AskUserQuestion at PR
(the 0058/0059/0060/0061 pattern); ACs/Steps are written to the recommendations and
re-scope mechanically if Cray picks otherwise.
**Owner:** Claude Code (executes); Cray ratifies the surfaced decisions
**Created:** 2026-07-15
**Related ADRs:** **ADR-0031** (`docs/adr/0031-core-lifecycle-architecture.md`) is the
authorizing decision — **D3 row-1** (`0031:134`) pre-designs this exact seam ("a
typed declarative transform grammar: a bounded op-set … plus a `derive` op restricted
to a whitelisted expression grammar — never arbitrary eval"), its D2 moat tripwires
(`0031:119-125`) bind every choice below, its D4 fractal Rule-of-Three
(`0031:140-159`) bounds the op-set, and row-1 itself delegates the exact op-set +
grammar surface to "the transform PLAN (OQ-1)" — this PLAN. **ADR-016 Q4 amendment**
(Accepted 2026-07-09): the (c) derived/computed-field decomposition (`0016:1094-1097`)
and the **OQ-3 resolution** (Cray-ratified s115, `0016:1302-1315`) name "a downstream
transform step" as the designated home for the fields the join/projection grammar
deliberately refuses — this PLAN builds that home. Also: ADR-0024 D3/D6 (governed ≠
generated — no LLM in the derivation path), ADR-006 D4 (Rule of Three), ADR-0025 D3
(the bypass-unrepresentable discipline the SD-3 expression tree mirrors), ADR-009
D1/D2 + ADR-012 D4.3 + ADR-013 D1 (authoring/commit boundaries + disclosure).
**Related PLANs:** PLAN-0061 (`docs/plans/done/0061-join-projection-grammar-build.md`
— the direct template: an Accepted-decision-rendering build PLAN, the
compile/execute/inspect factoring, the one-shared-surface load-gate property, the
build-vs-migrate split); PLAN-0048 (the compile-or-refuse-typed seam + the AC-3
no-drift property this extends); PLAN-0062 (the parity-guarded migration follow-on
precedent SD-4 mirrors); PLAN-0075 (AC-13 `derivation_hash` — the temporary
throwaway a declared transform makes redundant; and the freshly-hardened authority
path SD-1 deliberately does not touch); **PLAN-0076**
(`docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` — its Step
T2 is where F-PIN's fold-in is tracked; the fold-in itself belongs to the SD-4
migration PLAN, **not** here).

> **Drafting provenance (ADR-012 D4.3 / ADR-013 OQ-1).** Authored by the in-harness
> `plan-drafter` subagent under ADR-013 D1 phased authority. Dispatch originated by
> Code; direction by Cray (Cray picked the transform-grammar build as the #1
> next-work item). Independent review: Code (R2) at PR — every `file:line` citation
> re-verified on disk; ratification: Cray (SD-1..SD-8 via AskUserQuestion at PR
> merge). Author≠reviewer separation: **INTACT**. Uncommitted draft — Code commits
> per ADR-009 D2; the drafter does not git. Fact-pack anchors were Code-verified
> against `origin/main` @ `b8df516` and independently re-verified by the drafter
> against the working tree 2026-07-15; drift found and corrected in-draft:
> `STEP_GOVERNANCE_FIELDS` now spans `draft.py:42-60` (the fact-pack's `:42-54`
> predates the PLAN-0061 join/project entries), and the lift/strip/todo helpers sit
> at `draft.py:182/:199/:274`.

> **This is a build PLAN — no new ADR.** Both authorizing decisions are Accepted and
> the D3 row-1 trigger **has fired**: case 1 = procurement's `_SeedQuery`
> derived-field residue, self-documented as staying execution-bound "without
> inventing a transform StepKind (out of scope)"
> (`verticals/procurement/hero_demo/run.py:147-152`); case 2 = supply_chain's
> `_DispositionSeed`, self-documented as needing "a transform StepKind — ADR-0031 D3
> row-1, deliberately deferred" (`verticals/supply_chain/procedures_factory.py:99-103`).
> **Tripwire — STOP and surface for an ADR-0031 amendment if execution finds any
> of:** (i) a real derivation the whitelisted expression grammar cannot honestly
> express without arbitrary evaluation — do **NOT** invent an eval escape hatch
> (tripwire 1 is absolute; an inexpressible derivation stays code-side, honestly
> labelled, until Cray amends the row); (ii) the two concrete cases press an op
> *shape* materially different from row-1's pre-design (D4's own caveat: the map is
> a default, not a cage — deviation = amend the row, `0031:178-180`, never a silent
> bake-in); (iii) any LOCK below must bend. Never bake a deviation in.

## Goal

Render the two Accepted decisions into working code: a **`transform` StepKind** —
"declare the derivation as data" — so a procedure step can declare, as typed
authored spec surface, the deterministic field derivations that today live only in
per-vertical seed/executor code, and a generic engine executor compiles + runs them.
This is the "downstream transform home" ADR-016 Q4 OQ-3 conditions procurement's
full intake migration on (`0016:1302-1315`), and the D3 row-1 seam ADR-0031
pre-designed (`0031:134`). The concrete substrate is **exactly two shipped cases**:

- **Case 1 — procurement intake enrichment** (`run.py:202-248`): the `criticality`
  copy of the failure reading (`:227`), the `unit` default (`:225`), the
  `compliance` literal signal map (`:237-243`), the `candidate_quotes` reshape
  (`_normalize_quotes` `:186-199`, `price_thb→unit_price` at `:193`); marquee
  downstream derivation `amount = unit_price × qty` at the scored_rule action stamp
  (`services/engine/procedures/scored_rule.py:230`, emitted onto the threaded entity
  by `_scored_rule`, `governance_step.py:285-297`, consumed by the `doa_tier` gate's
  `_spend` reader, `governance_step.py:47-65`).
- **Case 2 — supply_chain disposition intake** (`procedures_factory.py:145-244`):
  the `excursion_magnitude_c` arithmetic derive (`reading_c − temp_ceiling`,
  `:189`), the `excursion_duration_h`/`stability_budget_ch` defaults (`:205-206`),
  the GDP `compliance` map (`:237-242`), the Decimal→str JSONB-safety coercions
  (`:200-204`, `:208`); marquee downstream derivation = the **`_DOSE_LADDER`**
  threshold banding (`verticals/supply_chain/cold_chain_assess.py:73-78`;
  `dose = magnitude × duration; ratio = dose / budget; severity = first band where
  ratio ≤ ceiling else _TOP_SEVERITY`, `derive_excursion_severity` `:174-202`),
  stamped at the assess action (`ColdChainAssessExecutor.execute` `:225-260`),
  consumed by the `severity_tier` gate's `_severity` reader
  (`governance_step.py:81-102`). The code names its own destiny: `_DOSE_LADDER` "IS
  THE DATUM A TRANSFORM GRAMMAR WOULD DECLARE (ADR-0031 D3 row-1)"
  (`cold_chain_assess.py:70-72`).

This PLAN builds **grammar + load gate + compile + executor + offline fixtures**. It
replaces nothing in production: it does **NOT** migrate either vertical's seed or
`procedures.yaml` — that is the separate parity-guarded migration PLAN (SD-4, the
PLAN-0061→PLAN-0062 split), which also owns retiring the PLAN-0075 AC-13
`derivation_hash` code-hash provider and firing the F-PIN self-cancelling marker
(PLAN-0076 Step T2). **F-PIN is not closed here** — once a derivation is declared
as transform data the existing pin covers it for free (`build_governance_snapshot`
already serializes each step's typed content, `governance_pin.py:81-85`), but the
new-run re-routing threat is an architectural property of per-run pinning,
orthogonal to this grammar, and **stays open** (`governance_pin.py:43-44`).
Everything here is offline, deterministic, and MS-S1-independent: **no LLM anywhere
in the derivation path** (governed ≠ generated, ADR-0024 D3/D6).

## LOCKED (ratified in the ADRs — render faithfully; do NOT re-litigate)

- **L-1 (no new ADR).** This PLAN renders ADR-0031 D3 row-1 (`0031:134`) + ADR-016
  Q4 OQ-3 (`0016:1302-1315`), both Accepted; the row-1 N≥2 trigger has fired (case
  1 + case 2 above, both self-documented on disk). Per D4.1 a PLAN may not cite the
  seam map alone — the fired trigger is cited above.
- **L-2 (declaration-as-data; the anti-eval wall).** The `derive` op uses a
  **whitelisted expression grammar** (arithmetic / concat / compare per row-1;
  concat defers under L-7's Rule-of-Three) — **NEVER** `eval` / `exec` /
  arbitrary-expression (ADR-0031 D2 tripwire 1). The SD-3 representation must make
  arbitrary evaluation *unrepresentable by construction* (the ADR-0025 D3
  discipline), not merely rejected.
- **L-3 (closed-spine discipline).** `transform` is an **additive closed-enum
  member** of `StepKind` (`spec.py:54-60`; the ADR-016 OQ-A1 additive-growth path)
  — NOT an open worker kind (tripwire 2); no untyped/free-form content registers
  onto the governed spine (tripwire 3); no closed enum flips to free strings
  (tripwire 4).
- **L-4 (deterministic throughout).** No LLM anywhere in the derivation path —
  same inputs → same derived fields; no clock, no randomness (governed ≠
  generated; the `derive_excursion_severity` determinism contract,
  `cold_chain_assess.py:174-180`, generalized).
- **L-5 (offline binding bar ONLY).** No MS-S1, no host-state action, no live run
  anywhere in this PLAN (CLAUDE.md §8 minimize-live-runs; the PLAN-0061 SD-6
  precedent — restated here as SD-5).
- **L-6 (one decision surface).** The load gate and the run-time compile share ONE
  structural-validation predicate — they cannot drift (the PLAN-0048 AC-3 property;
  the shipped precedent: `_validate_join_project` invoked by BOTH the load gate,
  `orchestrator.py:412`, AND the compile, `query_step.py:189`).
- **L-7 (Rule-of-Three bounds the op-set).** Ship only ops the two concrete cases
  exercise; defer the speculative remainder honestly labelled (ADR-0031 D4,
  `0031:140-159`; the ADR's own Negative consequence warns a pre-designed list can
  anchor prematurely, `0031:178-180`). Row-1 explicitly delegates the exact op-set
  to this PLAN, so subsetting is in-authority; the shipped set is recorded into the
  D3 row at landing (L-8).
- **L-8 (the D4.4 landing obligation).** When this seam LANDS (built + merged),
  ADR-0031's D3 row-1 is updated to "shipped — see PLAN-0077" with the shipped
  op-set recorded (`0031:157-159`). G1 nuance, recorded not performed: an
  Accepted-ADR body edit routes through the drafter (plan-drafter authors, Code R2
  + commits) — this is a **landing obligation of the final Step**, never an edit
  made in this draft.

## Substrate facts (verified on disk, 2026-07-15 — the extension points)

1. **The code template — compile / execute / inspect.**
   `services/engine/procedures/query_step.py` is the module the transform seam
   mirrors 1:1: `plan_read` (`:263-346`) is pure/total — plan-or-refuse, no I/O;
   `ReadRefusal` (`:81-107`) is a typed structured refusal, deliberately **NOT** an
   `*Error` (refusal ≠ no-data; here: refusal ≠ no-op); `ReadRefusalKind`
   (`:63-78`) grew additively (`JOIN_SHAPE_VIOLATION` `:78`, one member for the
   whole grammar); `QueryStepExecutor` (`:379-456`) is a `@dataclass(frozen=True)`
   constructor-injected executor emitting provenance trace entries; `_json_safe`
   (`:363-376`) is the adapter/JSONB boundary guard derived rows also need. The
   transform analog is **simpler**: it consumes `from`-threaded rows and performs
   **no adapter I/O at all**.
2. **The construct-home precedents.** `JoinSpec` (`spec.py:231`) / `ProjectSpec`
   (`spec.py:284`) live as `extra="forbid"` models with `Field(description=...)`
   on `StepInput` (`spec.py:326-377`); `governance_content` lives **top-level on
   `Step`** and is serialized per step into the governance snapshot
   (`governance_pin.py:81-85`). SD-6 picks the transform declaration's home
   between these two precedents.
3. **The closed kind registry.** `StepKind` (`spec.py:54-60`) = {query, evaluate,
   action, human_task}. Executor wiring is the StepKind-keyed `ExecutorFactory =
   Callable[[], Mapping[StepKind, StepExecutor]]` (`services/engine/registry.py:30`)
   — a new kind is registered by the composing factories (project memory: new
   verticals hand-wire factories in `main.py`; fixtures compose their own).
4. **The H-governance machinery.** `STEP_GOVERNANCE_FIELDS`
   (`services/engine/procedures/draft.py:42-60`) already carries `reads` / `join` /
   `project` with the comment "H-authored spec surface — a generated skeleton may
   never self-declare it" (`:54-58`); the lift strips at `_strip_read_binding`
   (`:182`) applied in `lift_to_step` (`:199`); `derive_governance_todo` (`:274`)
   is the unfilled-stub read a new authored surface must join (project memory: a
   new governed Step field skipped there fails runs with "unfilled stub").
   `build_governance_snapshot` (`governance_pin.py:56-115`) pins `join`/`project`
   canonically (`:97-106`) and folds the optional `derivation_hash` only-when-
   supplied so absent = byte-identical snapshot (`:111-115`).
5. **Case 1 on disk (procurement).** `_SeedQuery` (`run.py:133-167`): the join half
   is PROVEN grammar-expressible (`tests/verticals/procurement/test_intake_shadow_parity.py`,
   cited in the docstring `:140-144`); what keeps the seed in production is
   exactly the derived-field half (`:147-152`). The derivations: `criticality` =
   copy of `failure["measured_value"]` (`:227`; the source field is ALSO kept at
   `:224` — a copy, not a strict rename), `unit` = `.get` default (`:225`),
   `compliance` = literal map (`:237-243`), `candidate_quotes` = per-element
   reshape of a JOINED row-set into a nested list (`:186-199`, `:229`) — note:
   PLAN-0061 explicitly walled this off as "a transform, not a join/projection"
   (its Out of Scope), and it is **cardinality-changing** (N joined rows → one
   list field) — see SD-8. Marquee: `amount = unit_price × qty`
   (`scored_rule.py:230` → stamped `governance_step.py:285-297` → read by `_spend`
   `:47-65`, exact-`Decimal`, fail-closed).
6. **Case 2 on disk (supply_chain).** `_DispositionSeed` (`procedures_factory.py:92-113`)
   + `_intake_seed` (`:145-244`): `excursion_magnitude_c = reading_c − ceiling` as
   exact `Decimal` (`:189`), authored defaults (`:205-206`), `compliance` map
   (`:237-242`), `Decimal→str` coercions for JSONB safety (`:200-204`, `:208`).
   Marquee: `_DOSE_LADDER` (`cold_chain_assess.py:73-78`) + `_TOP_SEVERITY` (`:78`)
   consumed by `derive_excursion_severity` (`:174-202`): `dose = magnitude ×
   duration`, `ratio = dose / budget`, first band `ratio ≤ ceiling` else the
   unbounded top — inclusive ceilings, **total cover** (`:64-72`); NaN/±Inf fail
   CLOSED (`:129-139` — a non-finite scalar must never band); the criticality
   amplifier clamp `min(Decimal(1), ratio)` at the stamp (`:239`) is the on-disk
   `derive(compare)` instance. Stamped by `ColdChainAssessExecutor` (`:225-260`),
   read fail-closed by `_severity` (`governance_step.py:81-102`).
7. **The F-PIN linkage (state precisely; never overclaim).** Declared transform
   content is pinned **for free** by the existing snapshot (`governance_pin.py:81-85`
   for top-level typed content; `:97-106` shows the per-field pattern if SD-6 picks
   `StepInput`). The PLAN-0075 AC-13 `derivation_hash` provider (`registry.py:39`;
   `cold_chain_assess.py:82`; threaded `governance_pin.py:56-58`, folded
   `:111-115`) is the **temporary throwaway** a declared derivation obsoletes — but
   retiring it + firing the self-cancelling marker
   (`tests/services/engine/procedures/test_derivation_pin.py::test_fpin_residual_procurement_unpinned_marker`)
   belongs to the SD-4 **migration** PLAN (PLAN-0076 Step T2), not here. And the
   transform grammar does **NOT** close F-PIN's new-run re-routing threat — a
   deploy-time change before run-start pins clean by design (`governance_pin.py:43-44`);
   that stays open regardless. Nothing in this PLAN records F-PIN closed.

### Op-set triangulation (Rule-of-Three against the two cases — L-7)

| Op | Concrete instances on disk | Verdict |
|----|---------------------------|---------|
| `derive` (arithmetic) | magnitude `sub` (`procedures_factory.py:189`); amount `mul` (`scored_rule.py:230`); dose `mul` + ratio `div` (`cold_chain_assess.py:189-190`); clamp `min` (`:239`) | **SHIP** (N≥2, both verticals) |
| `derive` (field-copy leaf) | `criticality` copy (`run.py:227`) | SHIP (falls out of the SD-3 tree for free — a bare field leaf) |
| `default` | `unit` (`run.py:225`); both compliance maps (`run.py:237-243`, `procedures_factory.py:237-242`); duration/budget (`:205-206`); qty fallback (`:208-210`) | **SHIP** (N≥2) |
| `coerce` | Decimal→str JSONB safety (`procedures_factory.py:200-204,208`); `Decimal(str(...))` exact reads (house-wide, e.g. `governance_step.py:59`, `cold_chain_assess.py:130`) | **SHIP** (N≥2; v1 targets `string` + `decimal`) |
| `rename` | `batch_id ← reference` / `qty ← payload_kg` shape (`procedures_factory.py:197,208`); `price_thb→unit_price` (`run.py:193` — but element-wise, see SD-8) | **SHIP** (thin; overlaps the query grammar's `project.fields` — disclosed in SD-2) |
| `map_value` (threshold-ladder/banding form) | `_DOSE_LADDER` (`cold_chain_assess.py:73-78`, `:191-194`) — **the** case-2 marquee datum + the F-PIN fold-in target | **SHIP with disclosure** — the transform-side count is honestly **N=1**; the banding *shape* is triangulated by the house gate ladders (`SeverityLadder` / DOA tiers — which stay gate content, not transforms). See SD-2. |
| `derive` (compare) | the clamp (`:239`) rides `min`; the ladder predicate rides `map_value` | **PROVISIONAL** — armed-but-thin; ships only as tree operators, no standalone op |
| `unit_convert`, `extract`, `normalize`, `derive(concat)`, discrete (key→value) `map_value` | **zero** concrete instances | **DEFER** — speculative; designing them now is exactly ADR-0031's own Negative consequence (`0031:178-180`) |
| nest / aggregate (rows → list field: `candidate_quotes`) | one instance (`run.py:186-199,229`); supply_chain's list is authored literal, not derived | **DEFER** (cardinality-changing — a different semantic class; SD-8) |

## Acceptance Criteria

Everything below is **offline and deterministic**, each provable under the required
CI `gate` on a fresh PR (prove main-green via the PR's CI, not a named subset).

- [ ] **AC-1 — the typed `extra="forbid"` spec surface.** `StepKind` gains
      `TRANSFORM = "transform"` (`spec.py:54-60`) — additive closed-enum growth;
      the four existing members and every existing executor path are untouched
      (L-3). The transform declaration (`TransformSpec`, the per-op models, and the
      SD-3 `derive` expression tree) are typed Pydantic models, all
      `extra="forbid"`, every field `Field(description=...)`, homed per the
      ratified SD-6. The operator vocabulary is a **closed enum**; field access,
      attribute access, calls, and free-form expressions are **unrepresentable by
      construction** (L-2 — the anti-eval property is structural, and a test
      asserts the spec surface rejects every escape-hatch shape tried). An empty
      `ops` list is a schema-level rejection (the `ProjectSpec` "declares nothing"
      precedent, `spec.py:321-322`).
- [ ] **AC-2 — H-governed and pinned; the draft machinery cannot skip it.** The
      transform declaration joins `STEP_GOVERNANCE_FIELDS` (`draft.py:42-60`); the
      lift strips it to an absent stub (extending the `:182`/`:199` strip — a
      generated skeleton never self-declares a derivation); `derive_governance_todo`
      (`draft.py:274`) yields a filled/unfilled read for a transform step so a
      lifted draft cannot silently skip authoring it (the new-governed-field
      gotcha). `build_governance_snapshot` pins the declaration's canonical JSON
      per step (the `join`/`project` pattern `governance_pin.py:97-106`, or via
      `governance_content`-style top-level serialization `:81-85` per SD-6); a
      **mid-flight transform edit fails CLOSED at resume** (tested — the ladder-edit
      precedent). A procedure with **no** transform step pins **byte-identically**
      to today (the AC-13 only-when-supplied precedent, `governance_pin.py:111-115`);
      any pin-format consequence for declaring steps is disclosed in the PR body.
- [ ] **AC-3 — the load gate governs the declaration; ONE decision surface with the
      compile.** A structural validator (op well-formedness; closed operator
      enums; the SD-3 tree's depth bound; ladder bands strictly ascending +
      inclusive-ceiling + **mandatory unbounded top band** so cover is total,
      `cold_chain_assess.py:64-72`; coerce target types; targets non-colliding
      within the declared op sequence; `transform` kind ⇔ declaration-present
      coherence) runs at the PLAN-0046-lineage load gate AND inside
      `plan_transform` — **one shared predicate**, mirroring
      `_validate_join_project` at both `orchestrator.py:412` and
      `query_step.py:189` (L-6). A shared-matrix test drives the same declaration
      set through both surfaces and asserts identical accept/refuse decisions (the
      PLAN-0048 AC-3 / PLAN-0061 AC-3 tripwire pattern).
- [ ] **AC-4 — compile is pure and total.** `plan_transform` (no I/O, no adapter,
      no registry) turns a transform step into a typed **frozen plan** or raises a
      typed structured **`TransformRefusal`** (kind enum + step_id + detail — the
      `ReadRefusal` grain, `query_step.py:81-107`; deliberately NOT an `*Error`,
      and **refusal ≠ no-op**: a transform step never silently passes rows through
      while claiming to derive). Every step shape either compiles or refuses —
      there is no silently-empty path.
- [ ] **AC-5 — each shipped op executes deterministically.** `TransformStepExecutor`
      (`@dataclass(frozen=True)`, constructor-injected, **no adapter, no I/O, no
      LLM**) executes a compiled plan over the `from`-threaded input set with a
      per-op test matrix: arithmetic on **exact `Decimal`** (never binary float on
      an authority quantity — the `_spend`/`_positive_decimal` house discipline,
      `governance_step.py:52`, `cold_chain_assess.py:119-145`);
      division-by-zero and non-finite results refuse typed (fail closed — NaN/±Inf
      must never band, the `:131-139` lesson); `map_value` reproduces
      inclusive-ceiling + unbounded-top banding exactly; `default` fills only
      absent fields; `coerce` string/decimal round-trips; missing/non-coercible
      source fields follow the ratified SD-7 posture; output rows are JSONB-safe
      (the `_json_safe` boundary, `query_step.py:363-376`); every op execution
      emits a provenance trace entry (targets written, per-op row counts — the
      `read_provenance` grain).
- [ ] **AC-6 — end-to-end on the production paths + the two concrete-case parity
      fixtures.** Test-module-embedded procedures (the PLAN-0061 SD-3 pattern —
      zero shipped vertical file changes; house gotcha honored: no fixture files
      under `docs/plans/`, G2 fires there): **fixture A** (procurement-shaped)
      derives `criticality`-copy + `unit` default + `compliance` map and **fixture
      B** (supply_chain-shaped) derives magnitude arithmetic + defaults +
      `compliance` + coercions, each running through `run_procedure` and threading
      into a downstream consumer step; fixture B additionally runs through
      `run_procedure_persisted` proving JSONB-safe output + the pinned transform
      declaration round-trips. **Marquee expressibility parity (the shadow-parity
      precedent):** a declared transform reproduces `derive_excursion_severity`'s
      exact severity + ratio on the same inputs (`cold_chain_assess.py:174-202`,
      including the band edges and the top band) and `amount = unit_price × qty`
      (`scored_rule.py:230`) **value-identically** — proving the grammar can
      express the F-PIN derivations **without** touching the shipped stamp path
      (SD-1). These fixtures double as the authoring examples for the SD-4
      migration PLAN.
- [ ] **AC-7 — existing behavior unchanged.** The four existing `StepKind` members,
      all shipped executors, both verticals' seeds and hero paths are
      byte-untouched; a no-transform procedure's governance snapshot + config hash
      are byte-identical (AC-2); the PLAN-0074/0075 authority-path suites pass
      untouched (SD-1 = the freshly-hardened `doa_tier`/`severity_tier`/stamp
      executors are not modified); the F-PIN self-cancelling marker
      (`test_derivation_pin.py::test_fpin_residual_procurement_unpinned_marker`)
      stays **GREEN** — no procurement derivation hash and no `derivation_hash`
      retirement lands here (that firing belongs to the migration PLAN, PLAN-0076
      Step T2).
- [ ] **AC-8 — offline gate green.** Full suite + ruff + ruff-format +
      `mypy --strict services/` green under the required CI `gate` on a fresh PR;
      new API-facing fields carry `Field(description=...)`; **no MS-S1 / live-LLM
      call anywhere in any gate** (L-5 / SD-5 — see Verification).

## Out of Scope

- ❌ **Seed migration** — no shipped `procedures.yaml`, seed, or factory changes;
  flipping either vertical's derived half from execution-bound ✖ to ✔ is the
  separate parity-guarded migration PLAN (SD-4; the PLAN-0061→0062 split).
- ❌ **Retiring `derivation_hash` / firing the F-PIN marker** — the migration
  PLAN's job (PLAN-0076 Step T2). This PLAN leaves the provider, the pin fold-in,
  and the marker exactly as shipped.
- ❌ **Closing F-PIN's new-run re-routing threat** — an architectural property of
  per-run pinning (`governance_pin.py:43-44`), orthogonal to declaring derivations;
  it stays open and is recorded open (PLAN-0076 §B). **F-PIN is not recorded closed
  anywhere in this PLAN.**
- ❌ **The deferred ops** — `unit_convert`, `extract`, `normalize`,
  `derive(concat)`, discrete key→value `map_value` (zero concrete instances; L-7).
- ❌ **Cardinality-changing nest/aggregation** (the `candidate_quotes` rows→list
  reshape) per SD-8 — v1 transforms are row-local; the aggregation wall (PLAN-0048
  `0048:98`, PLAN-0061 L-2) is not re-litigated here.
- ❌ **Touching the hardened authority path** — `doa_tier` / `severity_tier` /
  `scored_rule` / `ColdChainAssessExecutor` and their gate readers are
  byte-untouched (SD-1; PLAN-0075 just hardened them).
- ❌ **Eligibility predicates** (the supply_chain lane-eligibility follow-on noted
  at `procedures_factory.py:158-162`) — a declarative *filter* is a different
  construct from a derivation; it waits for its own trigger.
- ❌ **LLM anywhere in the derivation path** (L-4) — no proposal, selection,
  reshaping, or retry by a model; this PLAN never touches MS-S1.
- ❌ **Editing ADR-0031 in this draft** — the D4.4 row update is a landing
  obligation (L-8), authored by the drafter at merge time, not here.

## Surfaced Decisions

Build-level forks only — the direction is LOCKED above. Each SD carries a
recommendation; **Cray ratifies via AskUserQuestion at PR (the 0058/0059/0060/0061
pattern)**; none is silently decided. ACs/Steps are written to the recommendations
and re-scope mechanically if Cray picks otherwise.

- **SD-1 — the central scope fork: seam placement (what v1 `transform` handles).**
  *Recommendation:* **(A) pre-gate placement, capability-complete grammar.** The
  v1 `transform` StepKind targets the **intake/enrichment derivations** — the
  fields the join grammar refused (magnitude, compliance, defaults, coercions,
  copies) — as a standalone step between a query and its consumers. The marquee
  action-stamp derivations (`amount = unit_price × qty`; the `_DOSE_LADDER`
  severity) **stay in code**: the freshly-hardened PLAN-0074/0075 authority path
  (`scored_rule` stamp, `ColdChainAssessExecutor`, the fail-closed gate readers)
  is byte-untouched. BUT the grammar itself ships **capability-complete** for
  both cases — `derive(arithmetic)` + ladder `map_value` are in the v1 op-set and
  AC-6 proves, by expressibility-parity fixtures, that the declared grammar
  reproduces both marquee derivations value-identically. Whether the migration
  PLAN then actually moves the stamps into declared transform steps (re-sequencing
  the stamp path under parity guards) is decided THERE, with PLAN-0075's reversal
  cost weighed.
  *Alternatives:* **(A-strict)** intake-only op-set (no ladder `map_value`, no
  amount-shaped arithmetic proof) — smallest, but it hobbles the follow-on: the
  migration PLAN could not fold in F-PIN's derivations without ANOTHER grammar
  PLAN first, recreating the deferral-rot shape PLAN-0076 exists to prevent;
  **(B)** subsume the action-stamp derivations now — declares the severity/spend
  derivations as data in THIS PLAN so the pin covers them immediately, but it
  entangles a new grammar with the authority executors PLAN-0075 just hardened
  (the exact "bundling a framework refactor with a security fix" anti-pattern
  Cray's SD-3 keep-narrow ratification named), and the migration is a separate
  PLAN anyway, so B's payoff still would not land until then.
  *Why Cray:* this sets how much of the just-hardened authority path a new seam is
  allowed to approach, and when F-PIN's fold-in becomes possible — a risk-appetite
  + sequencing call, not a drafter call. (Dispatch disclosure: Code's stated lean
  was A; the drafter's independent read agrees and adds the
  capability-completeness refinement so A does not silently become A-strict.)

- **SD-2 — the exact v1 op-set surface.**
  *Recommendation:* ship **{`derive` (expression tree: arithmetic + compare
  operators + field/const leaves — a bare field leaf is the typed copy),
  `map_value` (threshold-ladder/banding form only), `default`, `rename`,
  `coerce` (string | decimal)}**; defer **{`unit_convert`, `extract`, `normalize`,
  `derive(concat)`, discrete `map_value`}** (zero instances — the triangulation
  table above). Honest disclosures Cray ratifies with this: (i) `map_value`'s
  transform-side instance count is **N=1** (the `_DOSE_LADDER`); it ships because
  it is THE self-identified case-2 datum (`cold_chain_assess.py:70-72`) and the
  F-PIN fold-in target, with the banding *shape* triangulated by the house gate
  ladders (which remain gate content); a strict-letter Rule-of-Three reading would
  defer it — that reading is rejected here, explicitly. (ii) `rename` overlaps
  the query grammar's `project.fields`; it ships for post-query/derived-field
  renames but is the thinnest member. Authoring sketches (fix the public
  `extra="forbid"` grammar; final literal schema per SD-3/SD-6):

  ```yaml
  # Case 2 — supply_chain disposition enrichment (row-local; SD-8):
  - id: enrich
    kind: transform
    input: {from: intake}
    transform:
      ops:
        - derive:
            target: excursion_magnitude_c
            expr: {op: sub, args: [{field: reading_c}, {field: temp_ceiling}]}
        - default: {target: excursion_duration_h, value: 9}
        - default: {target: stability_budget_ch, value: 24}
        - default:
            target: compliance
            value: {stability_budget: true, batch_quarantine: true,
                    licensed_disposal_vendor: true, coa_customs: true}
        - coerce: {target: excursion_magnitude_c, to: string}

  # Case 1 — procurement intake enrichment + the marquee expressibility fixtures
  # (the amount/severity forms are AC-6 parity fixtures, not shipped wiring — SD-1):
  - id: enrich
    kind: transform
    input: {from: intake_read}          # the PLAN-0061-proven join half feeds this
    transform:
      ops:
        - derive: {target: criticality, expr: {field: measured_value}}   # typed copy
        - default: {target: unit, value: criticality}
        - default:
            target: compliance
            value: {avl: true, tax: true, cert: true, sanctions: true, single_source: true}
  # amount = unit_price × qty (fixture):
  - derive: {target: amount, expr: {op: mul, args: [{field: unit_price}, {field: qty}]}}
  # the _DOSE_LADDER as declared data (fixture):
  - derive:
      target: dose_ratio
      expr: {op: div,
             args: [{op: mul, args: [{field: excursion_magnitude_c},
                                     {field: excursion_duration_h}]},
                    {field: stability_budget_ch}]}
  - map_value:
      target: excursion_severity
      source: {field: dose_ratio}
      bands: [{ceiling: "0.25", value: negligible},
              {ceiling: "0.50", value: minor},
              {ceiling: "1.00", value: major}]
      above: critical     # mandatory unbounded top band — total cover, never optional
  ```

  *Alternatives:* ship row-1's full pre-designed list (speculative — the ADR's own
  Negative consequence, `0031:178-180`); defer `map_value` on the strict N=1
  reading (hobbles the F-PIN fold-in and contradicts the datum's own comment).
  *Why Cray:* this fixes the public authored grammar every future vertical writes,
  AND ratifies the two Rule-of-Three judgment calls disclosed above.

- **SD-3 — the `derive` whitelisted-expression representation (the load-bearing
  anti-eval design).**
  *Recommendation:* a **small typed operation tree** of tagged `extra="forbid"`
  Pydantic nodes: leaves = `{field: <name>}` (read a source field) or
  `{const: <JSON-safe literal>}`; interior nodes = `{op: <member of a CLOSED
  operator enum>, args: [<nodes>]}` with v1 operators `{add, sub, mul, div, min,
  max}` (arithmetic) + `{le, lt, ge, gt, eq}` (compare, for the provisional
  predicate uses); a static **depth bound** (e.g. 8) enforced at schema; arity
  validated per operator. Evaluation: operands coerce via `Decimal(str(...))`
  (exact — never binary float on an authority quantity); division-by-zero and
  non-finite results are typed refusals (fail closed). The anti-eval property is
  **structural**: no node type can express a name lookup beyond `field`, an
  attribute access, a call, or a string of code — there is nothing to sanitize
  because the unsafe shapes are unrepresentable (ADR-0025 D3 discipline; tripwire
  1 honored by construction, statically checkable, canonically pinnable as JSON).
  *Alternatives:* (i) a string mini-DSL (`"unit_price * qty"`) with a hand-rolled
  parser — rejected: a string surface is exactly the seam that grows toward eval,
  is harder to validate at load and to pin canonically, and reads as tripwire-1
  bait to every future author; (ii) a flat prefix/RPN op list — equal power,
  rejected: less readable as authored YAML, and the nesting bound stops being a
  schema property.
  *Why Cray:* this IS the rendering of ADR-0031 D2 tripwire 1 — the shape of the
  wall between "declared derivation" and "arbitrary code" — and it fixes the
  grammar every future author writes.

- **SD-4 — build-only vs build+migrate.**
  *Recommendation:* **build-only** (the PLAN-0061 → PLAN-0062 split, and ADR-016
  Q4's own SD-C sequencing). This PLAN ships grammar + load gate + compile +
  executor + offline fixtures; a SEPARATE parity-guarded follow-on PLAN migrates
  the two verticals' seeds (flipping their derived halves execution-bound ✖→✔,
  partially for procurement while SD-8 defers the nest), retires the AC-13
  `derivation_hash` provider, and fires/retires the F-PIN self-cancelling marker
  (PLAN-0076 Step T2 routes there). Until that PLAN lands, both seeds stay
  production and honestly labelled — nothing here claims otherwise.
  *Alternative:* migrate in-PLAN — rejected: changes demo-visible run semantics of
  BOTH shipped verticals inside the same PR series that introduces the grammar,
  needs the parity harness this PLAN deliberately does not build, and couples the
  F-PIN marker firing to grammar review.
  *Why Cray:* it decides whether any shipped vertical's observable behavior can
  move in this PLAN (recommendation: none can).

- **SD-5 — phasing + verification posture.**
  *Recommendation:* **three phases, one PR each** (Steps 1–3): **A** schema +
  H-governance + load gate (NO execution) → **B** compile + execute → **C**
  fixtures end-to-end + full oracle; suite green at every phase boundary,
  oracle-first two-commit history inside each PR where practical. Verification =
  **offline binding bar ONLY** (the PLAN-0061 SD-6 twin): every deliverable is
  deterministic and MS-S1-independent — no LLM exists in the derivation path
  (L-4) — so the offline suite under CI `gate` is not just the binding bar, it is
  the ENTIRE bar; no host-state action, no §8 gate, no `docs/logs/` live-evidence
  note.
  *Alternatives:* one monolithic PR (loses per-boundary green + review
  boundaries); a confirming live run (pure host-state cost, zero evidence value —
  nothing non-deterministic exists to confirm).
  *Why Cray:* phase boundaries = review boundaries, and §8 makes live-run posture
  explicitly Cray's call — this records the deliberate decision NOT to ask for
  one.

- **SD-6 — the construct home: where the transform declaration lives on `Step`.**
  *Recommendation:* a **top-level `Step.transform: TransformSpec | None`** —
  mirroring `governance_content` (typed content keyed to a step's nature,
  serialized per step into the pin, `governance_pin.py:81-85`), with a model
  validator enforcing presence **iff** `kind == transform` (the kind⇔content
  coherence precedent). `StepInput` stays data-*sourcing* scoped (`from` / `where`
  / `reads` / `join` / `project`); a transform consumes the `from` thread and
  declares *derivation*, which is a different concern.
  *Alternatives:* (i) fields on `StepInput` (the `join`/`project` precedent) —
  rejected: conflates sourcing with derivation and lets a query step carry a
  half-meaningful transform surface; (ii) a new arm of the AT-2
  `governance_content` union — rejected: that union is managerial gate content
  (ADR-0025 D2) with its own consumers; derivation logic in it would muddy both.
  *Why Cray:* it fixes the public spec surface and the pin shape (an operational
  compatibility call, not a drafter call).

- **SD-7 — the missing-input posture (what a transform does when a source field is
  absent or non-coercible on a row).**
  *Recommendation:* **fail CLOSED — a typed refusal for the step** (the whole
  step, not a per-row skip), with the `default` op as the *authored* escape hatch:
  if absence is legal, the author declares the default; the engine never invents
  one. This mirrors the house authority-input discipline (`_spend`
  `governance_step.py:47-65`; `_positive_decimal` `cold_chain_assess.py:119-145`):
  transform outputs feed governance gates, and a silently dropped or
  silently-nulled row upstream of a gate fails DANGEROUS, not closed.
  *Alternatives:* (i) exclude-and-count (the join-grammar posture for read rows,
  `query_step.py:605-646`) — right for reads, wrong for governance inputs (a
  vanished row is an unreviewed disposition); (ii) SQL-style null propagation —
  rejected: feeds gates values they must then re-refuse, moving the failure away
  from its cause.
  *Why Cray:* it sets the failure posture of every derivation upstream of an
  authority gate — the same class of call as OQ-4's warn-vs-reject in the Q4
  amendment.

- **SD-8 — the row-local boundary (nest/aggregation stays out).**
  *Recommendation:* v1 transforms are **row-local**: one input row → the same row
  enriched (fields added / renamed / coerced); ops may read only that row's
  fields. **Cardinality-changing** shapes — nesting N joined rows into a
  list-valued field (the `candidate_quotes` reshape, `run.py:186-199`, which
  PLAN-0061 walled off to "a transform" in its Out of Scope) and any
  aggregation — are OUT, honestly re-deferred (N=1; and aggregation is the
  standing PLAN-0048 wall, `0048:98`). Consequence, stated plainly so OQ-3's
  conditional is not overclaimed: even after the SD-4 migration, procurement's
  intake migrates **partially** (join half + row-local derived fields; the
  `candidate_quotes` nest stays seed-side) — the OQ-3 resolution itself
  contemplated exactly this partial outcome (`0016:1306-1308`). If the migration
  PLAN finds the nest indispensable, that is the Tripwire path (surface for the
  ADR-0031 row amendment), never an in-PLAN invention.
  *Alternatives:* (i) ship a `nest`/collect op now — N=1 + speculative aggregation
  semantics; (ii) an element-wise `over: <list_field>` scope on rename/select —
  N=1 and it still cannot *produce* the list from joined rows.
  *Why Cray:* it decides whether procurement's "full migration" conditional can
  ever be satisfied without a future amendment — an honesty-of-scope call with
  demo-visible consequences.

## Steps

Build order = cheapest gate first; the suite stays green at every phase boundary.

### Step 1 — Phase A: schema + H-governance + load gate (AC-1, AC-2, AC-3 — no execution)
`spec.py`: `StepKind.TRANSFORM`; `TransformSpec` + op models + the SD-3 expression
tree per the ratified SD-2/SD-3/SD-6 schemas, all `extra="forbid"`, every field
`Field(description=...)`; kind⇔declaration coherence validator; empty-ops
rejection. H-governance: the declaration enters `STEP_GOVERNANCE_FIELDS`
(`draft.py:42-60`), the lift strips it (extend `:182`/`:199`; disjointness test
extends), `derive_governance_todo` (`:274`) learns the transform stub,
`build_governance_snapshot` pins it (per SD-6; fail-closed resume-mismatch test;
no-transform procedures byte-identical). Load gate: the shared structural
validator wired into the PLAN-0046-lineage load path (the `orchestrator.py:412`
precedent) — the AC-3 shared-matrix test lands here with the compile half stubbed
to the same predicate. No executor exists yet; no shipped procedure declares a
transform, so run-time behavior is unchanged.

### Step 2 — Phase B: compile + execute (AC-4, AC-5)
A new `services/engine/procedures/transform_step.py` mirroring `query_step.py`'s
factoring: `plan_transform` (pure/total → frozen `TransformPlan` |
`TransformRefusal`, re-running the SAME shared structural predicate — L-6);
`TransformStepExecutor` (`@dataclass(frozen=True)`, no adapter, no I/O, no LLM;
exact-`Decimal` evaluation; fail-closed division/non-finite/missing-input per
SD-7; ladder banding; JSONB-safe outputs; per-op provenance trace). The per-op
determinism matrix + the AC-3 matrix's compile half go live. Existing suites
byte-untouched (AC-7 sweep starts here).

### Step 3 — Phase C: fixtures end-to-end + the offline oracle (AC-6, AC-7, AC-8)
Test-module-embedded procedures + fake adapters (PLAN-0061 SD-3 pattern): fixture
A (procurement-shaped) + fixture B (supply_chain-shaped) through `run_procedure`;
fixture B through `run_procedure_persisted` (JSONB-safe + pin round-trip). The
marquee expressibility-parity fixtures (severity ladder value-identical to
`derive_excursion_severity`; amount value-identical to `scored_rule.py:230`).
Full AC-7 no-regression sweep (authority-path suites untouched; F-PIN marker
GREEN). Full oracle: suite + ruff + ruff-format + `mypy --strict services/` under
CI `gate` on a fresh PR. Conventional commits `feat(engine): ...` referencing
PLAN-0077; Code commits via PR per CLAUDE.md §7 (ADR-009 D2). **Landing
obligation (L-8):** at merge, route the ADR-0031 D3 row-1 update ("shipped — see
PLAN-0077", shipped op-set recorded) through the drafter (G1: Accepted-body edit)
in the same landing series.

## Verification

How do we know it worked? **Binding — and complete (SD-5):** the AC matrix,
entirely offline under the required CI `gate` on a fresh PR. The deterministic
properties are tested as properties: one shared structural surface deciding
identically at load and compile (AC-3 matrix), exact-Decimal arithmetic +
fail-closed division/non-finite/missing-input (SD-7), ladder totality (bands
ascending, inclusive ceilings, mandatory top), marquee expressibility parity
(severity + amount value-identical to the shipped code paths), fail-closed pin at
resume, and the byte-identical no-regression sweeps (no-transform snapshot, the
four existing kinds, the authority-path suites, the F-PIN marker GREEN). **There
is NO live run** — this PLAN is deterministic and MS-S1-independent end to end
(L-4/L-5); the offline oracle is not just the gate, it is the entire bar. **Honest
enforcement frame:** after this PLAN, a step that DECLARES a transform and runs
under the new executor is declared ✔ · load-gated ✔ · execution-bound ✔ for the
shipped op-set; the two shipped verticals' seeds remain **execution-bound ✖** for
their derived halves, the marquee `amount`/`severity` stamps remain code-side by
ratified choice (SD-1), `derivation_hash` remains in service, and **F-PIN remains
open** — until the SD-4 migration PLAN lands, nothing here may claim otherwise.

## Open Questions

- **OQ-1 — refusal-type grain.** One `TransformRefusal` with a kind enum (the
  `ReadRefusal` shape) vs one member added to a shared refusal taxonomy. Additive
  either way; settle at Step 2 review against the `query_step.py:63-78` grain.
- **OQ-2 — op + trace naming.** `map_value` vs `band` (the shipped semantics ARE
  banding; row-1's name is `map_value`); the provenance trace kind
  (`transform_provenance` recommended, mirroring `read_provenance`). Settle at
  Step 1 review; greppable alignment with ADR-0031 row-1 vocabulary preferred, and
  the landing row-update (L-8) records whatever is chosen.
- **OQ-3 — executor registration shape.** Engine-generic: `TransformStepExecutor`
  needs no adapter, so composing factories can register it uniformly (and the
  fixtures compose their own) — vs per-vertical opt-in. Leaning engine-generic at
  each composing factory; settle at Step 2 (note the house gotcha: NEW verticals
  hand-wire factories in `main.py`, so whichever shape is chosen must be
  documented in the factory convention).
- **OQ-4 — `from`-thread validation coverage.** Confirm at Step 1 that the
  existing pre-flight `from` linearity validation (`validate_runnable` lineage,
  `spec.py:333-335` docstring) applies kind-agnostically to a transform step, or
  extend it; a transform with a forward/unknown `from` must fail at load, not at
  run.

## Size estimate

**M.** Three phased PRs: a contained spec + governance + gate extension (Step 1),
the genuinely new logic — the expression-tree evaluator + ladder semantics + the
transform executor (Step 2), and a fixture/oracle pass (Step 3). No migration, no
UI, no live runs, no adapter I/O; the blast radius is bounded by AC-7's
byte-identical guarantees and SD-1's do-not-touch wall around the authority path.

---

*PLAN-0077 drafted by the in-harness `plan-drafter` subagent (2026-07-15), ADR-013
D1 phased governance authoring (ADR-009 D1). It renders two Accepted decisions —
ADR-0031 D3 row-1 (`0031:134`, trigger fired: both cases on disk) and ADR-016 Q4
OQ-3 (`0016:1302-1315`) — and needs NO new ADR; L-1..L-8 are LOCKED and none is
reopened; eight build-level forks are surfaced (SD-1..SD-8) with recommendations,
none silently decided — including two disclosed Rule-of-Three judgment calls
(SD-2) and the drafter's independent SD-1 refinement of Code's stated lean.
Author≠reviewer (ADR-012 D4.3): drafter = plan-drafter; reviewers = Code R2 (every
citation re-verified on disk) + Cray at SD ratification (AskUserQuestion) and PR
merge — separation INTACT. Drafted uncommitted; Code commits via a `docs/*` PR
(ADR-009 D2); the drafter does not git. AI-assisted (plan-drafter); no
`Co-Authored-By` per CLAUDE.md §7.*
