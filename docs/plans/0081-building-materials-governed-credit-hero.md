# PLAN-0081: The building_materials governed-credit HERO (build)

**Status:** Draft — SD-A/SD-B/SD-C/SD-D **RESOLVED (Cray, s146)**: SD-A/SD-B
proceed-with-GUESS as proposed; SD-C = stays-deferred (re-arm AT-2 marker at
N=4); **SD-D = (a) — Cray OVERRODE the drafter's (b) recommendation: the
shared/core `Person` extraction lands IN THIS PLAN** (a conscious
scope-expanding override, chosen with the blast-radius framing in view).
**SD-E RESOLVED (Cray, s147, AskUserQuestion) = (b-ii):** promote `Person`
to an ADR-0008 ontology `object_type` at a **NEW shared/core ontology
home** — which requires INVENTING the shared-ontology mechanism (no such
home exists today; the shipped codegen model is strictly per-vertical),
EXTENDING `code_generator.py` + `cli.py`, and (per CLAUDE.md §8) landing a
preceding **ADR-0008 grammar amendment**. A second conscious scope
expansion, chosen with the full grounded cost in view.
Still open: **SD-F…SD-J** (b-ii's own sub-forks, incl. **SD-J
absorb-vs-split — the highest-order structural fork**) + **OQ-1** (now
EXPANDED: substantial ADR work — an ADR-0026 amendment AND the ADR-0008
amendment) — below.
**Owner:** Claude Code (execution) · Cray (SD-F…SD-J adjudication +
ratification)
**Created:** 2026-07-18
**Related ADRs:** **ADR-0008 (PRIMARY — its per-vertical YAML-ontology
grammar is AMENDED by the SD-E=(b-ii) shared-ontology construct; the
amendment must precede the implementation PR, CLAUDE.md §8 / AC-12)**,
ADR-0032 (D1 wedge / D6 AT-2 cost class), ADR-0025 (D2/D3
typed AT-2 content; D7 re-trigger — the obligation this PLAN pays), ADR-0026
(SoD run-check + principals; OQ-6 Person deferral; its `:89` "codegen
untouched" consequence is SUPERSEDED by SD-E=(b-ii)), ADR-0031 (D3 seam map;
D4.2 own-PLAN rule), ADR-016 (per-entity `threshold_field` FKP band), ADR-0015
(D2 Tier-1 Mirror — the shipped starting state), ADR-006 (D4 Rule of Three),
ADR-0007 (approve→execute gate). Related PLANs: **PLAN-0079** (the tracking
mandate this PLAN executes — read it first), PLAN-0076 (gate-seam tracker; its
T1 trigger is MET by this build, see Step 8), PLAN-0074/0075 (the 2nd AT-2
signature + tier-authority enforcement, reused), PLAN-0077 (SD-8 row-local
wall, honored), PLAN-0078 (declared-transform precedent, mirrored), PLAN-0062
(executor-factory wiring pattern), PLAN-0068 (per-entity band exemplar).

> **Mandate.** PLAN-0079 Step T1 fired this session: Cray commissioned the
> hero (AskUserQuestion, s146) and resolved SD-1 (**trip N=3 in-PLAN — do not
> wait for PLAN-0076 T1**) and SD-2 (**ride the existing `measured_value`
> exposure field — no aggregation, no new field**). Those two adjudications
> are LOCKED inputs here, not re-litigated. PLAN-0079's 3-part spine
> (`0079:115-127`), coordination points (`0079:128-141`) and honest-cost
> framing govern this PLAN's shape. **Also LOCKED (Cray, s146, this PLAN's
> own SD round):** SD-A/SD-B GUESS values proceed as proposed; SD-C = the D7
> deferral stays (AT-2 marker re-arms at N=4); SD-D = (a), the shared/core
> `Person` extraction is IN scope here and CLOSES the ADR-0026 OQ-6 deferral
> (the Person marker TRANSFORMS — it does not re-arm). **Also LOCKED (Cray,
> s147, AskUserQuestion, this PLAN's second SD round):** SD-E = (b-ii) —
> the ontology-layer promotion at a NEW shared/core ontology home (see the
> resolved SD-E record below; not re-litigated).

## Goal

Build the `building_materials` **governed-credit HERO**: a runnable, offline-
deterministic AT-2 procedure over the shipped Tier-1 Mirror (#765) in which a
trade customer's outstanding credit exposure (the event stream's
`measured_value`, THB) breaches ABOVE the account's own `credit_limit_thb`,
and the release decision runs the full governed spine — **(a)** a
deterministic per-entity exposure band, **(b)** a hard credit-compliance
`rule_gate` (KYC / overdue-AR / blacklist), **(c)** a `doa_tier` human
approval with SoD (sales REQUESTS, credit-control APPROVES) and the engine
audit — using the shipped machinery unchanged (`DoaLadder` `spec.py:958`,
`resolve_doa_tier` `doa_tier.py:95`, `check_tier_authority`
`tier_authority.py:125`). The build consciously pays the hero's true cost
(ADR-0032 D6: never a config-cost item): it is **AT-2 signature #3**, so it
trips the ADR-0025 D7 re-trigger marker and performs the D7 re-evaluation
**in this PLAN** (Step 8 — verdict Cray-ratified: stays deferred, re-arm at
N=4), and — found on verification this session — it is also the **3rd
principal-bearing vertical**, tripping the ADR-0026 OQ-6 Person-extraction
marker. Per Cray's SD-D=(a) override, this PLAN therefore **also promotes `Person`
to an ADR-0008 ontology `object_type` at a NEW shared/core ontology home
(SD-E=(b-ii), Cray s147) — inventing the shared-ontology mechanism +
extending the generator/CLI, behind a preceding ADR-0008 grammar
amendment — and migrates all three principal-bearing verticals
(procurement, supply_chain, building_materials) onto the GENERATED shared
`Person`** (Step 9), closing the OQ-6 deferral under ADR-006 D4 Rule of
Three. Honest cost, now at its heaviest reading (ADR-0032 D6: never a
config-cost item): Step 9 opens a **new generation surface** — a change
bigger than the hero build itself — consciously chosen by Cray with
exactly that framing in view. All authored numbers are demo GUESSES
marked "GUESS — รอแก้" (ADR-0032 D1 guess-then-react discipline).

## Current state (verified on `main` 7e34913, 2026-07-17/18)

- `verticals/building_materials/` is a Tier-1 Mirror: ontology
  (`ontology/building_materials_v0.yaml`) + synthetic adapter + a no-op
  `echo` handler stub (`handlers.py:16`) + `generated/` — **no
  `procedures.yaml`, no `procedures_factory.py`** (`services/api/main.py:131-134`
  docstring confirms the mirror registers no executor factory).
- The exposure field ALREADY exists: `OperationalEvent.measured_value`
  (`building_materials_v0.yaml:88-90` — "Current outstanding credit exposure
  (open AR + this order), THB"). The per-account ceiling ALREADY exists:
  `credit_limit_thb` (`:36-41`, a per-entity `threshold_field` band, marked
  "GUESS — รอแก้"). The synthetic timeline already carries the demo beat:
  baseline 250,000 THB then a breach reading of **550,000 THB vs a 500,000
  limit** (`data_adapter/synthetic.py:34-44,61-71`). The adapter wires
  `OperationalEvent` through the real-time anchor
  (`data_adapter/__init__.py:36-42`).
- The `doa_tier` gate reads a FLAT `amount`/`currency` off its input entity
  and **fails closed** otherwise (`governance_step.py:47-57`, `_spend()`).
  Exposure arrives as `measured_value` — hence the reshape seam (Step 4).
- AT-2 is N=2 (`spec.py:822-831`, post-#767); the re-trigger marker re-arms at
  N=3 (`tests/services/engine/procedures/test_at2_signature_retrigger.py:81`
  `_RETRIGGER_N = 3`; the count assertion `:213` **and** the baseline-equality
  assertion `:208` — both fire on a new signature).
- Principal identity is N=2 (`test_principal_identity_retrigger.py:49`
  baseline `["procurement", "supply_chain"]`; re-armed at N=3, `:43,:80`).
- **The principal-identity anatomy the Step-9 extraction operates on
  (verified this session — what is ALREADY shared vs what is per-vertical):**
  the `Person` TYPE, its validators, the YAML parse, the SoD run-check, and
  the API-side principal index are already engine-core —
  `services/engine/procedures/spec.py:1359` (`class Person`), `:1660`
  (`VerticalProcedures.principals` — class at `:1649`; misnamed
  "ProceduresSpec" in this PLAN's first draft, corrected at the s147
  fold: `was an error`, a citation typo), `:1678-1695` (validators),
  `:1789` (parse);
  `services/engine/procedures/principal_sod.py` (`check_principal_sod`);
  `services/api/auth.py:49` (`_principal_index(vertical)`). What is
  PER-VERTICAL (the hand-copied pattern the OQ-6 marker counts) is the
  roster homes + wiring: `verticals/procurement/procedures.yaml:64`
  (`principals:`) **plus a SECOND procurement roster source** —
  `person.csv` via `load_fastenal_principals`
  (`verticals/procurement/hero_demo/procedure.py:70-74`) — and the
  `hero_demo/run.py` wiring (`:347-358,:380-382,:542-550,:666,:738-749`);
  `verticals/supply_chain/procedures.yaml:63-84` (`principals:`) + its
  factory wiring (`procedures_factory.py:272,295`).
- DB state: only energy has a committed ORM (`code_generator.py:742`
  `_ORM_COMMITTED_DEST = {"energy": …}`); this mirror is in-memory
  synthetic. **The first draft's "No ontology change → no regen, no
  migration (unless SD-E resolves to the ontology-layer placement)" line
  now RESOLVES to the ontology-layer placement — FLIPPED for the Person
  scope:** Step 9 REQUIRES ontology edits (the new shared/core YAML), a
  codegen extension + re-run, and — per the SD-I verdict — possibly a
  committed home for the shared `Person` artifacts. The exposure/L-2
  scope is untouched by this flip: it still rides existing fields and
  stays ontology-frozen (see Out of Scope).
- **The per-vertical codegen reality b-ii must invent around (verified on
  `main` e03e56f, s147 — Code + an Explore agent, two independent passes;
  every anchor re-read from disk by this drafter at the fold):** the
  generator loads exactly ONE ontology YAML per run —
  `generate_all(yaml_path, output_dir)` (`code_generator.py:745-763`)
  over a single-doc `load_doc` (`:71-76`), with no import/include/merge
  logic; a `ref`-typed property resolves ONLY within that same doc
  (`object_types[target]`, `:163` SQL / `:435` ORM — a cross-vertical
  `ref` would raise `KeyError`); the CLI hard-wires
  `verticals/{vertical}/ontology/{vertical}_v0.yaml` (`cli.py:22-23`;
  `generate` at `:37-52`; console script `vero-lite`,
  `pyproject.toml:44-45`); the shipped generator emits **7** artifacts
  (ADR-0008 D5 names 5; plus a SQLAlchemy `orm.py` + an R1
  `context_pack.md`, `code_generator.py:756-762`);
  `verticals/*/generated/` is gitignored (`.gitignore:42`; ADR-0008
  `:101`); the ADR-0008 grammar is per-vertical BY CONSTRUCTION
  (`namespace: <vertical_name>`, D2 `:37-63`; 5 base object types per
  vertical, D1 `:22-36`; every artifact under
  `verticals/<name>/generated/`, D5 `:89-101`) with NO construct for a
  shared object_type defined once and used across verticals; and
  `Person` today is spec-layer-only, NOT in codegen (`spec.py:1359-1378`
  — "Lives in the procedures spec layer"; zero `Person`/`principal` hits
  in any `verticals/*/ontology/*_v0.yaml` or `verticals/*/generated/*`;
  `code_generator.py` has no `Person` awareness and never reads
  `procedures.yaml`). **b-ii therefore has NO existing home — Step 9a
  must build one.**

## Acceptance Criteria

Each AC carries a pre-committed pass/fail read. Test artifacts are **landed
by Code at build time** (this drafter cannot write `tests/`), per the
PLAN-0079 AC-2 precedent.

- [ ] **AC-1 — the 3-part spine ships, all three, or the PR does not merge.**
  Pass/fail read: `load_procedures("building_materials")` returns the hero
  procedure whose steps carry (a) an `evaluate` band with
  `threshold_field: credit_limit_thb`, `direction: above`; (b) a
  `governance_content: {kind: rule_gate}` compliance step upstream of the
  authority gate; (c) a `governance_content: {kind: doa_tier}` gated action
  plus a `separation_of_duties` constraint binding requester ≠ approver.
  Code lands a guard test asserting exactly this composition (gate-kind
  tuple `("rule_gate", "doa_tier")` read off typed `governance_content`).
  Fails if any leg is missing — a ladder-only form is the hollow-governance
  shape PLAN-0079 forbids (`0079:115-123`).
- [ ] **AC-2 — the reshape seam resolves the DOA tier (the L-2 seam,
  first-class).** Pass/fail read: an in-memory `run_procedure` over the
  synthetic data reaches the `doa_tier` gate with `amount` equal to the
  breach event's `measured_value` (550,000, Decimal-exact via the
  string-coerce) and `currency: "THB"`, and the run suspends
  `waiting_human` at the approve step — no `DoaTierError`. Code lands the
  test. Fails if the gate fail-closes on the shipped happy path or if the
  amount is not byte-derived from `measured_value`.
- [ ] **AC-3 — fail-closed is untouched; the engine diff is bounded to the
  two NAMED scopes.** Pass/fail read: the PR's diff under
  `services/engine/` (and `services/api/auth.py`, if the principal-index
  seam moves) touches **only** (i) the additive `ComplianceCriterion` enum
  block in `spec.py` (Step 2) and (ii) the SD-E=(b-ii) shared-`Person`
  promotion scope (Step 9), which NOW SPANS: the new shared/core ontology
  YAML (SD-F home), the `code_generator.py` + `cli.py` extension that
  discovers/loads it, emits the shared module, and resolves
  cross-vertical refs (SD-G mechanism), the generated shared `Person`
  module itself (its home per SD-I), the spec-layer reconciliation
  (`spec.py:1359` area, per SD-H), and the roster homes + loading/index
  seam migration. (The ADR-0008 grammar amendment is a SEPARATE,
  PRECEDING PR — AC-12 — not part of this diff.) **No change** to
  `_spend()`, `resolve_doa_tier`, `check_tier_authority`,
  `evaluate_compliance`, or `ComplianceRule.blocks_po`, and no change to
  the SoD fail-closed SEMANTICS (`check_principal_sod`'s verdict
  behavior is preserved even as the roster/type source moves onto the
  generated `Person`). A non-breach / non-reshaped entity still raises
  `DoaTierError`. *Honest flag (compounded — SD-D=(a), then
  SD-E=(b-ii)): this is now a MUCH larger diff than SD-D=(a) alone
  implied — scope (ii) grew from "roster home + loading/index seam" to
  "a new generation surface". The bound remains these two named scopes,
  verified at R2 by diff inspection; the WIDTH of scope (ii) is the
  consciously accepted b-ii cost, never a config-cost item.*
- [ ] **AC-4 — the executor factory is wired (coordination point i).**
  Pass/fail read: `verticals/building_materials/procedures_factory.py`
  exists; `services/api/main.py` gains a lazy
  `_register_building_materials_executors` registrar + a
  `_PROCEDURE_EXECUTOR_REGISTRARS["building_materials"]` entry, and the
  `:131-134` docstring drops building_materials from the mirrors list. Code
  lands a test (PLAN-0062 AC-5 pattern) asserting
  `registry.get_procedure_executors("building_materials")` succeeds after
  the registrar runs — the 409-at-resolve failure mode is covered.
- [ ] **AC-5 — SoD + tier authority are demonstrably enforced.** Pass/fail
  read: Code lands tests asserting (i) gate-resolve by the requesting
  sales principal fails closed (SoD, ADR-0026 D4); (ii) the tier's own
  approver resolves; (iii) a SENIOR principal approves a lower-tier
  exposure via cumulative roles (PLAN-0075 Policy B — roles authored
  cumulatively in the YAML, mirroring `supply_chain/procedures.yaml:63-84`).
- [ ] **AC-6 — the D7 re-evaluation is performed and recorded (Step 8), and
  the marker is honestly re-pointed.** Pass/fail read:
  `test_at2_signature_retrigger.py` is updated in the same PR — the new
  signature added to `_BASELINE_SIGNATURES`, `_RETRIGGER_N` re-armed at
  **4** (the SD-C verdict, Cray-ratified s146: stays-deferred), and the
  module docstring carries the N=3 re-evaluation record mirroring the N=2
  record's form (argument + verdict + what generalised). Fails if the
  marker is silently bumped without the recorded argument, or if CI merges
  RED.
- [ ] **AC-7 — the OQ-6 Person marker TRANSFORMS (Step 9, SD-D=(a)): the
  deferral is CLOSED, not re-deferred.** Pass/fail read: Code lands the
  marker transformation — `test_principal_identity_retrigger.py` changes
  FROM a "FAIL when an Nth vertical ships a per-vertical `Person`"
  re-trigger INTO an assertion that the shared/core `Person` home **is the
  one used across all principal-bearing verticals** (no re-arm at N=4; a
  future vertical adding principals onto the shared home is the INTENDED
  state, and a regression REINTRODUCING a per-vertical roster home fails).
  The module docstring preserves the honest lineage: the N=2 firing was
  answered (per-vertical re-confirmed + follow-on filed, PLAN-0074 AC-12),
  and at N=3 the extraction was **PERFORMED** (this PLAN; ADR-006 D4
  satisfied). Fails if the baseline is merely extended/re-armed, or if the
  lineage record is dropped.
- [ ] **AC-8 — the endpoint coordination points are consciously re-pointed
  (ii + iii).** Pass/fail read: in the same PR,
  `tests/api/test_procedures_endpoint.py` `_EXPECTED` gains
  `building_materials: {<hero_id>: "AT-2"}`; the count pin `:113` bumps
  `9 → 10`; the spec-less guard `:116-140` is **re-pointed, not deleted**
  — via the fixture route its own comment names (`:131`), because after
  this build **zero discovered spec-less verticals remain** (`vet_clinic/`
  is a README-only parked directory that `discover_and_register` cannot
  import — `services/engine/discovery.py:67-68` requires `data_adapter` +
  `handlers`). CI green at merge.
- [ ] **AC-9 — demo discipline (ADR-0032 D1).** Pass/fail read: every
  authored number (ladder tiers, compliance thresholds, principal roster)
  carries a "GUESS — รอแก้" marking in the YAML comments; the whole build
  is deterministic-offline (no MS-S1, no host-state, no DB); the LLM
  appears only as `llm_assist` advisory prose.
- [ ] **AC-10 — PLAN-0079 retires on its own T3 terms.** Pass/fail read: in
  the PR that completes this build, PLAN-0079 moves to `docs/plans/done/`,
  its guard test
  (`tests/services/engine/procedures/test_governed_credit_hero_tracking_guard.py`
  — exists on `main`, verified) is deleted **in that same PR**, and the
  STATUS PLAN-0079 pointer retires in the same motion (`0079:228-233`).
  This PLAN itself archives to `done/` per the normal Plan Flow.
- [ ] **AC-11 — the two existing verticals migrate onto the shared `Person`
  home with behavior preserved (the SD-D=(a) blast radius, pinned).**
  Pass/fail read: procurement + supply_chain resolve their principals from
  the shared home (the GENERATED shared `Person`, SD-E=(b-ii));
  procurement's **dual roster source is unified** (the
  `procedures.yaml:64` block vs `person.csv` via `load_fastenal_principals`,
  `hero_demo/procedure.py:70-74` — one canonical source remains, the other
  becomes a pointer or is retired); `verticals/supply_chain/procedures_factory.py:272,295`
  and `services/api/auth.py:49` read the shared seam. Every existing
  SoD / tier-authority / gate-resolve test passes **unmodified in its
  assertions** (roster-source plumbing may change; verdicts may not). Fails
  if any existing governance verdict changes, or if a per-vertical roster
  home survives alongside the shared one.
- [ ] **AC-12 — the ADR-0008 grammar amendment lands FIRST (CLAUDE.md §8:
  the ADR is merged before the related implementation PR).** Pass/fail
  read: the shared-ontology grammar construct (the SD-F namespace/home
  answer + the SD-G discovery/resolution mechanism) is **Accepted** in an
  ADR-0008 amendment (or a new ADR — the OQ-1 path, Cray sequences) and
  MERGED before any Step-9 codegen/grammar change ships. G1-gated:
  plan-drafter authors, Code commits, ratified in ONE pass (never flip
  Status then edit body). This AC is verified at R2 by PR ordering, not
  by a pytest artifact. Fails if any grammar/codegen change ships ahead
  of its ADR.
- [ ] **AC-13 — the shared-ontology mechanism WORKS end-to-end.**
  Pass/fail read: a shared/core ontology YAML (at the SD-F-ratified
  home) defining `Person` as an ADR-0008 `object_type` generates a
  shared `Person` type via the extended generator/CLI (`uv run
  vero-lite generate …`, exact invocation per SD-G), and a
  cross-vertical reference to the shared type resolves via the
  SD-G-ratified mechanism WITHOUT the `KeyError` the shipped within-doc
  resolution would raise (`code_generator.py:163,435`). Code lands a
  test exercising generate-then-import: the generated shared `Person`
  is importable and its fields match the YAML definition (incl. the
  load-bearing constraints — see SD-H's emitter-capability note). Fails
  if the shared type is hand-written rather than generated, or if
  "resolution" is achieved by duplicating the object_type into each
  vertical's own doc.
- [ ] **AC-14 — reproducibility + the generated module's home are
  handled, not left ambient.** Pass/fail read: the shared generated
  artifacts follow the committed-vs-gitignored discipline —
  reference artifacts gitignored-reproducible (`.gitignore:42` /
  ADR-0008 `:101`), runtime-imported code at a COMMITTED home (the
  energy `_ORM_COMMITTED_DEST` / B1 Option-B precedent,
  `code_generator.py:736-742`: runtime code cannot live gitignored) —
  per the SD-I-ratified verdict; and a codegen re-run is idempotent
  (regenerating from an unchanged YAML produces no diff). Fails if
  runtime-imported code lands under a gitignored path, or if
  regeneration is not reproducible.
- [ ] **AC-15 — the spec-layer `Person` is RECONCILED: exactly ONE
  authoritative `Person` type remains.** Pass/fail read: after Step
  9a(v), the SD-H-ratified end state holds — there are NOT two
  competing `Person` types; every consumer
  (`VerticalProcedures.principals` `spec.py:1660` + parse `:1789`,
  `check_principal_sod`, `auth.py:49` `_principal_index`) resolves to
  the generated shared type (directly or via the SD-H re-export/alias),
  and Code lands a grep-level guard that FAILS if a second independent
  `class Person(BaseModel)` definition reappears outside the generated
  home. Fails on any two-`Person` collision.

## Out of Scope

- ❌ **The transform-grammar aggregation extension** (PLAN-0079 SD-2 option
  (c)) — the PLAN-0077 SD-8 row-local wall is RATIFIED
  (`done/0077-transform-grammar-build.md:558-577`); exposure rides the
  existing `measured_value` field, period (Cray, s146). If build reality
  contradicts this, that is the SD-8 Tripwire path (surface for an ADR-0031
  row amendment) — never an in-PLAN invention.
- ❌ **Any change to `ComplianceRule.blocks_po`** or any other
  bypass-unrepresentable invariant (`spec.py:813-816`). The
  `ComplianceCriterion` enum grows ADDITIVELY only (its own docstring's
  contract, `spec.py:852-860`).
- ❌ **Writing test files by this drafter** — Code lands every test named in
  the ACs at commit time (PLAN-0079 AC-2 precedent).
- ❌ **A new `current_exposure_thb` field — the EXPOSURE/L-2 scope touches
  no ontology and no codegen.** Exposure rides the existing
  `measured_value` field; the mirror stays in-memory synthetic; the L-2
  seam is the Step-4 reshape only. *(Split at the s147 SD-E=(b-ii) fold:
  the first draft's blanket "no ontology edits, codegen re-runs, or DB
  migrations" prohibition is REMOVED for the PERSON scope — Step 9 now
  REQUIRES ontology edits + a codegen extension/re-run + a new shared
  generated module, and possibly a committed DB/ORM home per SD-I. The
  two scopes are distinct by design and must not be conflated: the
  exposure path is ontology-FROZEN; the Person path is
  ontology-EXPANDING.)*
- ❌ **Schedule- / event-triggered variants** — `trigger: manual` only
  (the PLAN-0019 L-1 precedent all four exemplar verticals follow). No
  `Schedule.owning_person_id` / headless-SoD surface is entered.
- ❌ **Building the AT-2 generator or the ADR-0031 D3 gate-plugin seam** —
  Step 8 *records* the D7 verdict; the extraction itself is PLAN-0076 T1
  territory and PLAN-0076's scope is not reassigned (`0079:137-141`).
- ❌ **Cross-vertical identity SEMANTICS beyond what the extraction needs**
  — the shared `Person` extraction (Step 9, IN scope per SD-D=(a)) unifies
  the roster HOME and its loading/index seam; it does NOT introduce
  cross-vertical SoD comparison, cross-vertical role semantics, or any
  alias-collapse rule change (ADR-0026 OQ-3=(c) stands untouched). The
  three rosters remain per-org demo DATA — different humans per vertical.
- ❌ **UI changes** — the generic `GET /procedures` viewer + OCT monitor
  surfaces the new procedure with zero UI work; none is scoped.
- ❌ **Re-litigating PLAN-0079's L-1/L-2 (SD-1/SD-2)** — Cray-ratified s146.

## Steps

### Step 1: Preflight — verify the anchors, branch, confirm both markers green
On a feature branch off current `main`: confirm `spec.py:822-831` still
records N=2; both re-trigger markers green pre-change
(`test_at2_signature_retrigger.py`, `test_principal_identity_retrigger.py`);
the count pin still `total == 9`; the spec-less guard still passing on
building_materials. Any drift → correct this PLAN's citations in the same PR
(symbols are the stable reference; PLAN-0079 T2 discipline).

### Step 2: Extend `ComplianceCriterion` with the credit block (the only SPINE engine edit — the OTHER engine scope is Step 9's b-ii codegen extension, AC-3(ii))
Add the credit-compliance criteria as a third instance-scoped block in
`spec.py` (`:852-872`), mirroring how PLAN-0074 added the GDP block —
additive, commented as building_materials' block. Proposed members (SD-A —
GUESS content, Cray sanity-checks): `kyc` (KYC/identity verification on file
and current), `overdue_ar` (no invoice past due beyond terms + grace), and
`blacklist` (account not suspended / not on the credit blacklist). Rationale
recorded in the enum comment: the N=2 finding — the GATE generalises, the
criterion vocabulary never does (`spec.py:856-860`) — predicts exactly this
kind of growth.

### Step 3: Author the spine part (a) — intake + the per-entity exposure band
Create `verticals/building_materials/procedures.yaml` (namespace, agent,
procedure skeleton; principals arrive in Step 5). The intake `query` step
reads the latest `OperationalEvent` reading per `CustomerAccount` via the
`event_for_account` link with an FK-parent join bringing `credit_limit_thb`
onto the reading (the aquaculture pattern, `aquaculture/procedures.yaml:64-90`
incl. the `site_id` projection-rename for the declared collision — both
objects carry `site_id`). The `judge` `evaluate` step bands each account
against ITS OWN limit: `threshold_field: credit_limit_thb`,
`direction: above` (`aquaculture/procedures.yaml:102` analog; the shipped
`supply_chain` `temp_ceiling` band is the `above`-direction exemplar,
`supply_chain/procedures.yaml:128-129`). Facets per ADR-016 D2 (typed
`decision_condition`; prose non-authoritative). Agent:
`autonomy_ceiling: gated`, `step_kinds: [query, evaluate, action, transform]`
(`transform` in the allowlist per the PLAN-0078 PR-2 precedent,
`supply_chain/procedures.yaml:45-47`).

### Step 4: The `measured_value` → `amount`/`currency` reshape (the L-2 seam, first-class)
A declared `transform` step over the breach subset (`from: judge, where:
{verdict: breach}`) — the enrich/derive path, NOT a bespoke executor —
supplying exactly what the downstream gates read and nothing more:

- `derive: {target: amount, expr: {field: measured_value}}` — the identity
  derive is shipped grammar (`procurement/procedures.yaml:144` precedent);
- `default: {target: currency, value: THB}` (the ontology's `unit` is
  already THB, but the gate contract wants the flat `currency` key —
  `governance_step.py:53-57`);
- `default: {target: compliance, value: {kyc: true, overdue_ar: true,
  blacklist: true}}` — the per-criterion signal map the `rule_gate` executor
  reads (the `supply_chain/procedures.yaml:236-241` precedent), GUESS-marked;
- `coerce: {target: amount, to: string}` so `Decimal(str(...))` is exact on
  the authority threshold (the PLAN-0078 byte-form discipline).

Why this shape is load-bearing: `_spend()` fails CLOSED without flat
`amount`/`currency` (`governance_step.py:47-57`) — this step is the entire
bridge between "exposure as a monitored reading" and "exposure as a governed
spend". Row-local throughout; the SD-8 wall is never approached.

### Step 5: Spine parts (b) + (c) — `rule_gate`, `doa_tier`, SoD, principals
- **(b)** `credit_gate` (`evaluate`, `governance_content: {kind: rule_gate}`)
  with the Step-2 criteria — band-less by design; any failed criterion
  blocks (`blocks_po` is `Literal[True]`, `spec.py:815` — bypass
  unrepresentable). Mirrors `supply_chain/procedures.yaml:359-389`.
- **(c)** `approve` (gated `action`, `governance_content: {kind: doa_tier}`)
  fed `from: credit_gate, where: {compliant: true}`. Proposed ladder (SD-B —
  GUESS, Cray-ratifiable; procurement's 4-tier THB form,
  `procurement/procedures.yaml:300-307`, re-priced for credit):
  `0 → จนท.เครดิต`, `250000 → ผจก.ควบคุมเครดิต`, `1000000 → ผอ.ฝ่ายการเงิน`
  (the shipped 550,000-THB breach lands mid-ladder — the demo shows tiering,
  not always-the-top). Routes on the FULL exposure, not the overage (SD-B
  names this sub-choice).
- **SoD + principals:** `separation_of_duties: distinct_steps [intake,
  approve]` with `required_roles` intake→`requester`, approve→`approver`
  (`supply_chain/procedures.yaml:460-465` form). Principals roster (SD-A/B
  — GUESS): one sales requester + three credit approvers with CUMULATIVE
  roles so a senior approves downward (PLAN-0075 Policy B,
  `supply_chain/procedures.yaml:63-84` form).
- A terminal gated `fulfill` step writes the approved decision via a no-op
  receipt handler (ADR-0007 approve→execute stays the only write path).

### Step 6: Handlers + executor factory + `main.py` wiring (coordination point i)
Extend `handlers.py` with no-op receipt stubs for the ontology
`RecommendedAction.action_type` vocabulary used by the procedure (e.g.
`escalate`, `approve_credit_override` — `building_materials_v0.yaml:137-139`),
registered alongside `echo`. Author
`verticals/building_materials/procedures_factory.py` on the supply_chain
template (`procedures_factory.py:255-303`): `QueryStepRouter` +
`GovernanceEvaluateExecutor(base=…)` + `GovernanceActionExecutor(base=…)` +
`TransformStepExecutor`, with the SoD principal index. Add the lazy registrar
+ dict entry in `services/api/main.py:125-134` and update its docstring
(building_materials leaves the mirrors list). Without this a fired run 409s
at gate-resolve (PLAN-0062; the `run-firing-entrypoint` lesson).

### Step 7: Re-point the endpoint coordination points (ii + iii)
In the SAME PR (these are RED-by-design transitions — CI is RED between the
YAML landing and this step, so they land together): `_EXPECTED` gains the
hero (`test_procedures_endpoint.py:28-46`); `returned == set(_EXPECTED)`
(`:96`) follows automatically; the count pin `total == 9 → 10` (`:113`,
bump the stale "eight/nine" prose comments consciously); the #765 spec-less
guard (`:116-140`) re-points via a FIXTURE (its `:131` alternative) — e.g. a
tmp-path scaffolded spec-less vertical registered for the test — because no
discovered spec-less vertical remains (see AC-8; `vet_clinic/` is
README-only and non-discoverable, `discovery.py:67-68`). Do NOT delete the
guard: the skip path it protects stays live code.

### Step 8: The ADR-0025 D7 re-evaluation at N=3 (first-class — the cost of the hero)
The new signature `("building_materials", ("rule_gate", "doa_tier"),
<enum surface>)` breaks BOTH marker assertions
(`test_at2_signature_retrigger.py:208` baseline-equality, `:213` count).
Perform the D7 re-evaluation as a conscious re-decision, recorded in the
marker's module docstring in the N=2 record's form, and in this PLAN's
closeout:

- **The argument FOR extraction:** N=3 is Rule-of-Three's own trigger
  (ADR-006 D4); three hand-authored governance shapes now ship; the marker's
  own failure text says "extract … or re-argue the deferral in a follow-on
  ADR" (`:213-223`).
- **The argument FOR stays-deferred (Code's recommendation — SD-C, Cray's
  verdict):** D7's recorded N=2 answer — "N>=2 PERMITS genericization, it
  does not mandate it" (`spec.py:826-829`) — and this 3rd signature is the
  WEAKEST possible extraction datum: it introduces no new gate kind, no new
  authority quantity (the money `DoaLadder` is REUSED unchanged, THB and
  all), and grows only the criterion vocabulary — the exact axis the N=2
  finding already established as per-instance forever. What it DOES do is
  fire PLAN-0076 T1's own named trigger ("a third AT-2 signature fires the
  N=3 re-trigger marker", `0076:299-304`) — so the extraction question has a
  live owner and does not need this PLAN to answer it.
- **Mechanics either way:** extend `_BASELINE_SIGNATURES` with the recorded
  argument; re-arm `_RETRIGGER_N` (→ 4 if stays-deferred); never a silent
  bump (`:208-212`: "Re-argue it (do not just update this list)").
- **Record in the closeout** that PLAN-0076 T1's trigger condition is now
  MET; PLAN-0076's own process owns the seam-PLAN opening (scope not
  reassigned, `0079:137-141`).

### Step 9: Extract the shared/core `Person` home + migrate all three verticals (SD-D=(a), Cray s146 — the scope-expanding override)
Shipping `principals:` (unavoidable — SoD + `doa_tier` gate-resolve require
resolvable `Person`s, ADR-0026 D4 / the RF-1 finding) makes
building_materials the THIRD principal-bearing vertical, firing
`test_principal_identity_retrigger.py` (`:71` baseline, `:80` N=3 — whose
failure text says the shared-`Person` extraction "is due, not deferrable").
**Cray chose to pay that debt HERE** — after seeing the blast-radius
framing (this couples an identity refactor to the hero build; the shape
PLAN-0074 SD-4 avoided at N=2) — so ADR-006 D4 Rule of Three is satisfied
by EXTRACTION, not by another recorded deferral. This marker was NOT in
the dispatch's four coordination points — it is coordination point (v).
*(SD-J note: this step as written renders the ABSORB structure — all of
b-ii inside this PLAN. If Cray's SD-J verdict is SPLIT, 9a moves to a
dependency PLAN and this step shrinks to the migration — see SD-J below;
the sub-step content is the same work either way.)* Sub-steps:

- **9a — Build the ontology-layer shared home (SD-E=(b-ii)).**
  *(Historical lineage: the first draft gated this on "Cray adjudicates
  SD-E before this step executes" — SD-E is now adjudicated, Cray s147
  AskUserQuestion.)* In order:
  **(i)** land the **ADR-0008 grammar amendment** in its own PRECEDING
  PR (AC-12; CLAUDE.md §8) — it codifies the SD-F namespace/home
  construct + the SD-G discovery/resolution grammar;
  **(ii)** create the **shared/core ontology YAML** defining `Person` as
  an ADR-0008 `object_type` at the SD-F-ratified path, carrying the
  shipped spec-layer anatomy (`person_id` PK, `name`,
  `roles` — `spec.py:1369-1378`, incl. the load-bearing constraints);
  **(iii)** extend **`code_generator.py` + `cli.py`** to discover/load
  the shared ontology, emit a shared generated module, and resolve
  cross-vertical refs per the SD-G-ratified mechanism (the shipped
  baseline being single-doc `load_doc`, a hard-wired per-vertical CLI
  path, and within-doc-only `ref` — Current state);
  **(iv)** run codegen → the **generated shared `Person`** (its
  committed-vs-gitignored home per SD-I; reproducibility per AC-14);
  **(v)** **reconcile the spec-layer `Person`** (`spec.py:1359-1378`)
  per SD-H so exactly one authoritative type remains (AC-15).
  What the SD-D=(a) anatomy finding established still holds underneath:
  the validators + parse + SoD check + API index are ALREADY
  engine-core; the per-vertical copies being unified are the roster
  HOMES and their loading/index wiring. b-ii ADDITIONALLY moves the
  `Person` TYPE's source of truth into the ontology (semantic) layer —
  that is the new part, and the new generation surface.
- **9b — Migrate the two existing verticals onto the GENERATED shared
  `Person`** (the AC-11 touch-points, all
  verified on disk): procurement — the `procedures.yaml:64` `principals:`
  block AND the second roster source (`person.csv` via
  `load_fastenal_principals`, `hero_demo/procedure.py:70-74`) unify into
  the canonical home; re-point the `hero_demo/run.py` wiring
  (`:347-358,:380-382,:542-550,:666,:738-749`). supply_chain — the
  `procedures.yaml:63-84` block + the factory wiring
  (`procedures_factory.py:272,295`). Plus `services/api/auth.py:49`
  (`_principal_index`) if the seam moves. Behavior bar: AC-11 — verdicts
  unchanged, existing test assertions unmodified. building_materials'
  roster (Step 5) lands directly on the shared home (Code may sequence 9a
  before Step 5 to avoid authoring-then-migrating; the end-state is what
  the ACs pin, not the intra-branch order).
- **9c — Transform the marker** (AC-7): from the N-count re-trigger into
  the shared-home assertion; preserve the honest lineage in the docstring
  (N=2 answered per PLAN-0074 AC-12; N=3 extraction PERFORMED by this
  PLAN). The OQ-6 deferral is **CLOSED** — no re-arm.
- **9d — Surface, do not decide (OQ-1 below, EXPANDED):** the ADR work
  is now substantial and load-bearing — an **ADR-0026 amendment** (OQ-6
  closure by extraction, `0026:116`, PLUS the `:89` "codegen untouched"
  supersession) **and** the **ADR-0008 grammar amendment** (9a(i),
  AC-12 — this one is not optional under CLAUDE.md §8). The exact ADR
  path + sequencing (in-place amendments vs a new shared-ontology ADR;
  ordering vs the SD-J verdict) is Cray's call at R2/ratification; the
  PLAN only flags it, and neither amendment is authored in this fold.

### Step 10: Offline verification + closeout
Full offline suite green (all Code-landed AC tests + the re-pointed
coordination tests + the re-armed AT-2 marker + the TRANSFORMED Person
marker + the AC-11 migration bar + the b-ii mechanism / reproducibility /
reconciliation tests — AC-13/AC-14/AC-15). In-memory `run_procedure`
evidence for AC-2/AC-5 paths. No live/host-state run is required or scoped
(CLAUDE.md §8) — any live OCT demo smoke is separate Cray-gated evidence,
not this PLAN's gate. Then AC-10 bookkeeping: PLAN-0079 → `done/` + its
guard test deleted + STATUS pointer retired, all in the completing PR; this
PLAN archives per Plan Flow.

## Verification

The offline oracle is the gate: `pytest` fully green on the PR head with
every AC's named assertion present — the spine-composition guard (AC-1), the
reshape run-path test (AC-2), the
factory-registration test (AC-4), the SoD/tier-authority triple (AC-5), the
re-armed AT-2 marker with its recorded re-evaluation (AC-6), the TRANSFORMED
Person marker with its preserved lineage (AC-7), the re-pointed endpoint
pins (AC-8), grep-level GUESS-marking (AC-9), the migration
behavior-preservation bar (AC-11 — existing governance test assertions
unmodified), the shared-ontology mechanism test (AC-13 —
generate-then-import at the SD-F home via the SD-G mechanism;
cross-vertical resolution WITHOUT the shipped within-doc `KeyError`), the
reproducibility + committed-home checks (AC-14 — idempotent regen;
runtime-imported code at a COMMITTED path, reference artifacts
gitignored-reproducible), and the one-`Person` reconciliation guard
(AC-15 — grep-level; fails if a second independent definition
reappears). Two ACs are R2/process-verified, NOT pytest artifacts:
**AC-12** (the ADR-0008 grammar amendment merged BEFORE the
implementation PR — verified by PR ordering) and **AC-3** (the
engine-diff two-named-scopes bound — verified by diff inspection at R2).
CI RED states are expected only INTRA-branch (between Steps
3–9); the merged PR is green.

## Surfaced Decisions

**Resolved (Cray, s146) — recorded verdicts, no longer open:**

- **SD-A — RESOLVED = proceed-with-GUESS as proposed** (ADR-0032 D1
  guess-then-react): criteria `{kyc, overdue_ar, blacklist}` (Step 2
  definitions); compliance signals default-true GUESSES in the reshape step
  (the supply_chain precedent); the existing 500,000-limit /
  550,000-breach data kept; the second-account-fails-a-criterion demo
  option approved as pure adapter data. Everything stays clearly marked
  "GUESS — รอแก้", Cray-correctable at the demo.
- **SD-B — RESOLVED = proceed-with-GUESS as proposed:**
  `0 → จนท.เครดิต / 250,000 → ผจก.ควบคุมเครดิต / 1,000,000 → ผอ.ฝ่ายการเงิน`,
  THB, cumulative senior roles, routing on the **FULL exposure** (not the
  over-limit increment).
- **SD-C — RESOLVED = as-recommended: the D7 deferral STAYS; re-arm the
  AT-2 marker at N=4** (Step 8). Recorded argument: the 3rd signature adds
  no new gate kind / authority quantity (doa_tier/THB reused unchanged),
  grows only the criterion vocabulary (the axis the N=2 finding already
  established as per-instance); PLAN-0076 T1's trigger is now met and owns
  the extraction question.
- **SD-D — RESOLVED = (a), OVERRIDING the drafter's (b) recommendation:
  extract the shared/core `Person` IN THIS PLAN** (Step 9). Cray chose (a)
  with the blast-radius framing in view ("heaviest — couples an identity
  refactor to the hero; PLAN-0074 SD-4 avoided exactly this") — a
  conscious scope expansion, honestly rendered: AC-3's engine-diff bound
  widened, AC-11 added to pin the migration behavior bar, and the OQ-6
  marker transforms (deferral CLOSED) instead of re-arming.

**Resolved (Cray, s147, AskUserQuestion) — the second SD round:**

- **SD-E — RESOLVED = (b-ii): promote `Person` to an ADR-0008 ontology
  `object_type` at a NEW shared/core ontology home.** A typed
  AskUserQuestion pick, made AFTER Code grounded the full cost (the
  Current-state per-vertical-codegen fact-pack). The grounded consequence
  — the crux: **no shared/core ontology home exists in the shipped model**
  (single-doc `load_doc`, per-vertical CLI hard-wire, within-doc-only
  `ref`, per-vertical-by-construction ADR-0008 grammar) — so (b-ii) is not
  a placement, it **INVENTS the mechanism** (Step 9a). Why Cray chose it
  over the lighter (a): Cray wants the ontology-layer identity model FOR
  REAL — `Person` as a first-class semantic-layer object, honoring the
  ADR-0026 `:95` "at the ontology layer" / `:157` "ontology object
  (ADR-0008 grammar)" reading — not a spec-layer convenience the ontology
  never sees. The honest cost, consciously accepted with exactly this
  framing in view: a **new generation surface** (a change bigger than the
  hero build itself); **contradicts ADR-0026 `:89`** ("introduces no new
  generation surface … leaves … the ADR-0008 ontology codegen path
  untouched" — now SUPERSEDED: a stated non-goal deliberately taken on);
  requires a **preceding ADR-0008 grammar amendment** (AC-12, CLAUDE.md
  §8); and a **Rule-of-Three tension consciously accepted** — the pattern
  being unified is at N=3 (three principal-bearing verticals), but the
  shared-ontology MECHANISM ships with N=1 real consumer (`Person` is its
  only object_type), and ADR-0008 itself deferred `shared property`-class
  constructs to a 3-verticals trigger (`0008:79-80`) — the amendment must
  re-argue that deferral. *Alternatives considered (recorded lineage —
  why-not):* **(a) engine-core spec-layer module** — the lightest path: a
  canonical shared roster home + one core loading/index function (e.g.
  beside `principal_sod.py`), honoring the verified anatomy
  (type/validators/check already engine-core), zero codegen touch. This
  was the drafter's s146 recommendation; it is classified **`superseded
  by new info`** (Cray's informed choice of the heavier ontology-layer
  identity model, made with the full grounded cost in view) — NOT `was an
  error`: (a) remains internally sound and was declined on strategic
  grounds, not correctness. **(b-i) ontology-layer WITHOUT a shared
  home** — each vertical's `_v0.yaml` defines `Person` under the EXISTING
  per-vertical grammar (no mechanism invention): re-copies the pattern ×3
  (the exact shape the marker counts), unifies nothing, and collides with
  the spec-layer `Person` — not coherent; rejected. **(c) a shared
  top-level rosters file** (one YAML for all verticals' principals) —
  maximal unification, but merges genuinely per-org demo DATA and
  inflates every vertical's identity blast radius; rejected.

**Still open (Cray adjudication — recommended, not decided): the b-ii
sub-forks.** (b-ii) is an invention, so it opens genuine architecture
sub-decisions. **SD-J is the highest-order structural fork — its verdict
SEQUENCES SD-F…SD-I and the OQ-1 ADR path.**

- **SD-F — WHERE the shared/core ontology file lives + its namespace.**
  ADR-0008 D2 fixes `namespace: <vertical_name>` (`0008:37-63`); a shared
  ontology breaks that convention, so the pick here is PART of what the
  ADR-0008 amendment must codify — a grammar reservation, not a
  file-layout detail. Options: **(a)** a repo-level `ontology/core_v0.yaml`
  — a new top-level home, visibly NOT a vertical; the amendment reserves a
  `core`/`shared` namespace token. **(b)** `verticals/_shared/ontology/…`
  — stays under the tree the tooling knows, but `_shared` is a
  pseudo-vertical (a lie-shaped path that discovery and the CLI must
  consciously special-case). **(c)** `services/engine/ontology/…` —
  engine-owned, but moving the semantic layer's source of truth INTO the
  engine tree inverts the "engine artifacts are generated FROM the
  ontology" direction. **Drafter recommendation: (a)** — honest topology
  (shared ≠ a vertical), one reserved namespace, the cleanest grammar
  story for the amendment to codify. Why Cray: repo topology + a
  namespace-grammar reservation that outlives this PLAN — every future
  shared type inherits it.
- **SD-G — how the generator/CLI discovers + loads the shared ontology,
  and how a cross-vertical `ref` resolves.** Shipped baseline: single-doc
  `load_doc` (`code_generator.py:71-76`), the per-vertical CLI hard-wire
  (`cli.py:22-23`), and `ref` resolving via `object_types[target]` within
  ONE doc only (`:163,:435` — cross-doc today = `KeyError`). Options:
  **(a)** a two-doc merge at generate time (shared + vertical YAML merged
  before emit) — simplest, but each vertical's generated module re-EMBEDS
  its own `Person` copy, recreating the N-copies problem at the artifact
  layer and colliding with AC-15's one-type end state. **(b)** a
  shared-ontology pre-pass — generating the shared doc emits ONE shared
  module; vertical generation resolves shared refs against the shared doc
  and emits IMPORTS of that module. **(c)** an explicit `imports:` (or
  `extends:`) grammar key in a vertical's `_v0.yaml` naming the shared
  doc — the dependency declared in YAML, never inferred. **Drafter
  recommendation: (b) + (c) combined** — the explicit `imports:` key is
  the grammar surface (declared, greppable, amendment-codifiable); the
  pre-pass + emitted-import is the mechanism (exactly ONE generated
  `Person`, satisfying AC-13 + AC-15). Why Cray: this IS the
  shared-ontology mechanism the ADR-0008 amendment codifies — the
  resolution semantics every future shared type uses.
- **SD-H — what happens to the existing spec-layer `Person`
  (`spec.py:1359-1378`).** The two-`Person`-collision risk lives here
  (AC-15 pins the end state). Options: **(a)** DELETE the class and
  RE-EXPORT the generated type from the spec-layer path — consumers
  (`VerticalProcedures.principals` `spec.py:1660`, parse `:1789`,
  `check_principal_sod`, `auth.py:49`) keep their import path; exactly
  one authoritative definition. **(b)** keep it as a thin alias/subclass
  — risk: the "thin" alias accretes logic and becomes a second
  definition. **(c)** generate INTO the spec-layer path — a committed,
  hand-edited engine module becoming partially generated is a standing
  hazard. **Emitter-capability note (load-bearing for AC-13):** the
  shipped class carries load-bearing constraints; the Pydantic emitter
  must be ABLE to express whatever the YAML definition claims to own —
  any gap is an EMITTER extension, never a hand-written shim quietly
  carrying the logic. **Drafter recommendation: (a)** —
  delete-and-re-export, guarded by the AC-15 grep-level check against a
  second independent `class Person(BaseModel)`. Why Cray: it pins the
  single-source-of-truth end state — the wrong pick silently recreates
  the collision AC-15 exists to prevent.
- **SD-I — does the shared `Person` get a committed ORM/DB home?** The
  generated Pydantic module is RUNTIME-IMPORTED (per SD-H), so it cannot
  live gitignored — the energy `_ORM_COMMITTED_DEST` / B1 Option-B
  precedent (`code_generator.py:736-742`: runtime code generates to a
  COMMITTED path; reference artifacts stay gitignored-reproducible,
  `.gitignore:42` / ADR-0008 `:101`) — that half is settled by AC-14.
  The open fork is the DB side. Options: **(a)** NO ORM/DB home —
  `Person` is a Pydantic-only shared type; rosters remain per-vertical
  YAML demo data; no table, no migration (matches the mirror discipline —
  only energy has a committed ORM today). **(b)** a committed ORM + DB
  table à la energy. **Drafter recommendation: (a)** — no consumer needs
  a `Person` table today; (b) drags migrations + the DB surface into an
  identity refactor that is already this PLAN's heaviest scope. Why Cray:
  it decides whether the identity model enters the DB/migration blast
  radius — a scope call, not a mechanics call.
- **SD-J (STRUCTURAL — flag prominently: the highest-order sub-fork; its
  verdict SEQUENCES SD-F…SD-I and the OQ-1 ADR path) — ABSORB b-ii into
  PLAN-0081 Step 9, or SPLIT it into its own ADR-0008-amendment +
  shared-ontology PLAN that PLAN-0081 DEPENDS on?** b-ii is arguably a
  foundational capability — a new ontology subsystem — currently coupled
  to the hero build. Options: **(a) ABSORB** — Step 9 as written; one
  PLAN, no cross-PLAN sequencing, but it couples the new subsystem to the
  hero (the coupling shape PLAN-0074 SD-4 avoided at N=2, now
  compounded), makes the completing PR much harder to review, and holds
  the hero hostage to the mechanism (and vice versa). **(b) SPLIT** — a
  dedicated shared-ontology PLAN (own Goal/ACs/Steps — AC-12/13/14/15 map
  onto it almost verbatim) that PLAN-0081 depends on; this PLAN's Step 9
  shrinks to the migration (9b–9d) onto the by-then-shipped shared home
  (cf. the ADR-0031 D4.2 own-PLAN rule already cited in this PLAN's
  header). The sub-step content is the same work either way — SD-J
  decides its PLAN topology, not its substance (Step 9's own SD-J note
  says the same). **Drafter recommendation: (b) SPLIT** — b-ii has its
  own ADR, its own acceptance surface, and its own failure modes; the
  ADR-first ordering (AC-12) already forces a sequence point, and a split
  keeps both PRs reviewable. Honest cost of (b): one more PLAN, a
  dependency edge, and the hero waits on the mechanism landing. Why Cray:
  PLAN topology + sequencing is Cray's routing authority — this fork
  decides what "this PLAN" even means and orders every other sub-fork.

## Open questions (surfaced, not decided)

- **OQ-1 — the ADR path for the b-ii decision (EXPANDED at the s147
  fold: the ADR work is now substantial and load-bearing, not a
  bookkeeping note).** SD-E=(b-ii) does two things to the ADR record.
  **(i)** It **SUPERSEDES ADR-0026 `:89`** — the Accepted ADR's recorded
  positive consequence ("introduces no new generation surface, and
  leaves … the ADR-0008 ontology codegen path untouched") no longer
  holds — and touches `:95` (the OQ-6 ontology-layer risk framing this
  pick honors) + `:116` (the OQ-6 "(b) per-vertical + enforceable
  re-trigger" resolution whose deferral this PLAN's extraction closes).
  **(ii)** It **REQUIRES an ADR-0008 grammar amendment** — the
  shared-ontology construct (the SD-F home/namespace + the SD-G
  discovery/resolution mechanism); ADR-0008's own `:79-80` deferred
  `shared property`-class constructs to a Rule-of-Three trigger, so the
  amendment must consciously re-argue that deferral too. Both are
  G1-gated (an Accepted-ADR body edit: plan-drafter authors, Code
  commits, ratified in ONE pass — never flip Status then edit body) and
  both must PRECEDE the implementation PR (CLAUDE.md §8; AC-12 pins the
  ordering). What Cray decides — not this PLAN: the exact ADR path +
  sequencing — **two in-place amendments** (the ADR-0022 / ADR-016
  precedent) vs **one NEW shared-ontology ADR** both existing ADRs point
  to vs **an ADR-0008 amendment + an ADR-0026 note** — and its ordering
  relative to the SD-J verdict (a SPLIT PLAN would carry the ADR work as
  its own first step). Neither amendment is authored in this fold
  (dispatch §5 constraint); a separate dispatch authors the ADR work
  after Cray sequences SD-J. Cray decides at R2/ratification.

## References

- **PLAN-0079** (`docs/plans/0079-building-materials-governed-credit-hero-tracking.md`)
  — the mandate: spine `:115-127`, coordination points `:128-141`,
  SD-1/SD-2/SD-3 `:246-263`, T3 retirement `:228-233`.
- **PLAN-0076** (`docs/plans/0076-…md:299-304`) — T1 trigger list naming the
  3rd-signature firing condition.
- **ADR-0026** (`docs/adr/0026-principal-identity-run-enforcement.md`) —
  OQ-6 resolution "(b) per-vertical + enforceable re-trigger" `:116`; the
  "ontology layer" tension `:95` vs Implementation Notes `:157` (the SD-E
  fork, resolved (b-ii) s147); the s132 tier-authority amendment
  `:170-174`. **Its `:89` consequence — "introduces no new generation
  surface, and leaves … the ADR-0008 ontology codegen path untouched" —
  is SUPERSEDED by SD-E=(b-ii)** (a stated non-goal deliberately taken
  on; the OQ-1 ADR work records the supersession).
- Step-9 / SD-E anchors (all verified on disk this session):
  `services/engine/procedures/spec.py:1340-1356` (`PrincipalAlias`),
  `:1359-1378` (`class Person` — "Lives in the procedures spec layer"),
  `:1660-1668` (`VerticalProcedures.principals` — class at `:1649`;
  misnamed "ProceduresSpec" in this PLAN's first draft, fixed at the
  s147 fold: `was an error`, a citation typo), `:1678-1695` (validators),
  `:1789` (parse); `services/engine/procedures/principal_sod.py`
  (`check_principal_sod`); `services/api/auth.py:49`
  (`_principal_index(vertical) -> dict[str, Person]`);
  `verticals/procurement/procedures.yaml:64` (`principals:`), `:93`
  (`service_principals:`);
  `verticals/procurement/hero_demo/procedure.py:70-74`
  (`load_fastenal_principals` — the second procurement roster source);
  `verticals/procurement/hero_demo/run.py:347-358,380-382,542-550,666,738-749`
  (principal wiring); `verticals/supply_chain/procedures_factory.py:272,295`.
- SD-E=(b-ii) / Step-9a codegen anchors (all verified on disk this
  session — the per-vertical baseline the mechanism must extend):
  `services/engine/code_generator.py:71-76` (single-doc `load_doc`),
  `:163,:435` (within-doc-only `ref` resolution — SQL / ORM emitters),
  `:736-742` (the B1 Option-B committed-ORM precedent,
  `_ORM_COMMITTED_DEST` — runtime code generates to a COMMITTED path),
  `:745-763` (`generate_all` — exactly one ontology YAML per run),
  `:756-762` (the 7 shipped emitters); `services/engine/cli.py:22-23`
  (the per-vertical path hard-wire), `:37-52` (`generate`);
  `pyproject.toml:44-45` (the `vero-lite` console script);
  `.gitignore:42` (`verticals/*/generated/` gitignored); ADR-0008
  `:22-36` (D1 per-vertical base types), `:37-63` (D2
  `namespace: <vertical_name>` grammar), `:79-80` (the grammar's OWN
  Rule-of-Three deferral of `shared property` — "Add when 3+ verticals
  request them" — the deferral the amendment must re-argue), `:89-101`
  (D5 generation contract + the gitignore line); ADR-0026 `:89` (the
  superseded no-new-generation-surface consequence), `:95` (the OQ-6
  ontology-layer risk framing), `:157` (the "ontology object (ADR-0008
  grammar)" Implementation Note), `:164` (the out-of-scope line —
  "genericizing `Person` to a shared/core object … gated on the …
  re-trigger" — whose gate this PLAN's N=3 firing now opens).
- Code anchors (all verified on disk this session):
  `verticals/building_materials/ontology/building_materials_v0.yaml:36-41,88-90`;
  `verticals/building_materials/data_adapter/synthetic.py:34-44,61-71`;
  `verticals/building_materials/data_adapter/__init__.py:36-42`;
  `verticals/building_materials/handlers.py:16`;
  `services/engine/procedures/governance_step.py:47-57`;
  `services/engine/procedures/spec.py:813-816,822-831,852-872,958`;
  `services/engine/procedures/doa_tier.py:95`;
  `services/engine/procedures/tier_authority.py:125`;
  `services/engine/procedures/orchestrator.py:659-666` (`_is_at2_procedure`);
  `services/engine/discovery.py:62-71`; `services/api/main.py:125-134`;
  `verticals/procurement/procedures.yaml:144,300-307`;
  `verticals/supply_chain/procedures.yaml:45-47,63-84,216-280,337-358,359-389,460-465`;
  `verticals/aquaculture/procedures.yaml:64-90,102`;
  `tests/api/test_procedures_endpoint.py:28-46,96,113,116-140`;
  `tests/services/engine/procedures/test_at2_signature_retrigger.py:81,86-115,208,213`;
  `tests/services/engine/procedures/test_principal_identity_retrigger.py:14-15,43,49,71,80`;
  `tests/services/engine/procedures/test_governed_credit_hero_tracking_guard.py`
  (exists on `main` — the AC-10 deletion target).

---

> **Drafting provenance (ADR-012 D4.3 / ADR-013 OQ-1).** Authored by the
> in-harness `plan-drafter` subagent under ADR-013 D1 phased authority
> (dispatch originated by Code, session 146, executing PLAN-0079 Step T1 on
> Cray's commissioning decision). Amended same session by the same drafter
> to fold in Cray's SD ratifications (SD-A/B proceed-with-GUESS; SD-C
> stays-deferred; **SD-D = (a) — Cray's override of the drafter's (b)
> recommendation**, expanding scope to the shared-`Person` extraction) and
> to surface SD-E + OQ-1. Independent review: Code (R2) at PR;
> ratification: Cray (SD-E has since RESOLVED — Cray, s147,
> AskUserQuestion; see the resolved SD-E record above. SD-F…SD-J + the
> EXPANDED OQ-1 remain open above). Author≠reviewer
> separation: **INTACT**. Uncommitted draft — Code commits per ADR-009 D2.
> Code fact-pack verified against `main` 7e34913 by Code; every line cited
> above re-read from disk by this drafter, 2026-07-17/18 — except the
> ADR-0026 s132 amendment range `:170-174`, read in partial context (start
> of the amendment section verified; its full extent unverified — Code
> spot-checks at R2).
>
> **Amendment (s147 fold — SD-E=(b-ii)).** Amended by the in-harness
> `plan-drafter` on Code's session-147 dispatch (a fresh drafter pass
> completed the fold after a prior pass was stopped at 14/18 edits by an
> L1 loop-detect lockout), folding **Cray's SD-E=(b-ii) AskUserQuestion
> ratification** — made after Code grounded the per-vertical codegen
> model + the no-shared-home finding on `main` e03e56f (Code + an
> Explore agent, two independent passes; the b-ii codegen + ADR anchors
> re-read from disk by this drafter at the fold). The fold renders: the
> conscious SCOPE EXPANSION (a new generation surface — Step 9a builds a
> shared-ontology mechanism that does not exist in the shipped model);
> the **preceding ADR-0008 grammar-amendment requirement** (AC-12,
> CLAUDE.md §8); the **ADR-0026 `:89` supersession** + the EXPANDED OQ-1
> (the ADR work is now substantial and load-bearing — neither amendment
> is authored in this fold, per dispatch §5); the new AC-12/13/14/15 +
> the widened AC-3 diff bound; the Out-of-Scope split (exposure path
> ontology-FROZEN vs Person path ontology-EXPANDING); and the SURFACED
> b-ii sub-forks **SD-F…SD-J** (SD-J absorb-vs-split = the highest-order
> structural fork — Cray sequences). The drafter's prior SD-E
> recommendation (a) is classified **`superseded by new info`** (Cray's
> informed choice), NOT `was an error`; one genuine `was an error` is
> fixed at this fold — the first draft's `ProceduresSpec.principals`
> citation (the class is `VerticalProcedures`, `spec.py:1649`; a
> citation typo). No `tests/` file written; no shell run; no commit.
> Author≠reviewer separation: **INTACT** (this drafter authors; Code R2s
> every claim against disk; Cray ratifies SD-F…SD-J + OQ-1).
> Uncommitted — Code commits per ADR-009 D2.
