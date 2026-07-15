# PLAN-0078: transform seed-migration — flip the two shipped verticals' derived intake halves from execution-bound ✖ to declared `transform` ✔, under zero-tolerance parity

**Status:** Proposed — SD-1..SD-5 await Cray ratification via AskUserQuestion at PR
(the 0058/0059/0060/0061/0077 pattern); ACs/Steps are written to the
recommendations and re-scope mechanically if Cray picks otherwise.
**Owner:** Claude Code (executes); Cray ratifies the surfaced decisions
**Created:** 2026-07-15
**Related ADRs:** **ADR-0031** D3 row-1 (the transform grammar this PLAN puts to
work — now shipped by PLAN-0077); **ADR-016 Q4** OQ-3 resolution
(`docs/adr/0016-governed-procedure-engine.md:1302-1315` — "a downstream transform
step" is the designated home; its own text contemplates procurement migrating
**PARTIALLY**, `0016:1306-1308`). **No new ADR** (L-1). Also: ADR-0024 D3/D6
(governed ≠ generated — no LLM in the derivation path), ADR-0025 D3
(bypass-unrepresentable), ADR-009 D1/D2 + ADR-012 D4.3 + ADR-013 D1
(authoring/commit boundaries + disclosure).
**Related PLANs:** **PLAN-0077**
(`docs/plans/done/0077-transform-grammar-build.md` — the build PLAN whose SD-4
(`0077:491-505`) split THIS migration out; its SD-8 row-local wall
(`0077:558-577`) and SD-1 stamp deferral (`0077:376-379`) bound this scope);
**PLAN-0062** (the parity-harness precedent,
`tests/services/engine/procedures/test_seed_migration_parity.py:1-15`);
**PLAN-0075** (the freshly-hardened authority path SD-1 weighs; AC-13
`derivation_hash`); **PLAN-0076**
(`docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` — Step
T2 `:293-302` tracks the F-PIN fold-in, Step T3 `:304-314` governs the marker);
PLAN-0061 (the build→migrate split template); PLAN-0074 (the fail-closed gate
readers L-6 protects).

> **Drafting provenance (ADR-012 D4.3 / ADR-013 OQ-1).** Authored by the
> in-harness `plan-drafter` subagent under ADR-013 D1 phased authority. Dispatch
> originated by Code; direction by Cray (picked the SD-4 migration as the #1
> next-work item via next-work-analyst, then typed "(ก)"). Independent review:
> Code (R2) at PR — every `file:line` citation re-verified on disk; ratification:
> Cray (SD-1..SD-5 via AskUserQuestion at PR merge). Author≠reviewer separation:
> **INTACT**. Uncommitted draft — Code commits per ADR-009 D2; the drafter does
> not git. The dispatch fact-pack was independently re-verified by the drafter
> against the working tree 2026-07-15; drift found and corrected in-draft: the
> per-step transform pin sits at `governance_pin.py:96-98` (not `:81-85` — that
> range is the PLAN-0061 join pin; the fact-pack citation predates the PLAN-0077
> transform key), the snapshot fold-in at `:122-125` (not `:111-115`), the
> supply_chain executor dict spans `procedures_factory.py:285-303` (not
> `:286-295`), and the fixtures' self-declaration sits in the module docstring at
> `test_transform_fixtures_e2e.py:4-6`. A sixth key-set assertion
> (`tests/services/engine/procedures/test_example_procedures.py:59`) uses a
> SUBSET check (`<=`) and tolerates TRANSFORM — it needs **no** change; only the
> five exact-equality tests move in lockstep.

> **Tripwire (inherited from PLAN-0077, absolute).** If execution finds a real
> derivation the shipped whitelisted op-set cannot honestly express — STOP and
> surface for an ADR-0031 amendment. Do **NOT** invent an eval escape hatch
> (ADR-0031 D2 tripwire 1); an inexpressible derivation stays code-side, honestly
> labelled, until Cray amends the row. Never bake a deviation in.

## Goal

Put the PLAN-0077 grammar to work in production: migrate the two shipped
verticals' derived-field **intake halves** from execution-bound-in-seed-code (✖)
to **declared `transform` steps** (✔) in their `procedures.yaml`, guarded by a
**zero-tolerance output-set parity harness** (the PLAN-0062 precedent) proving
the observable run semantics are unchanged — the declared-transform run produces
byte-equal rows and verdicts to the seed run on the same inputs. Then resolve the
F-PIN remainder tracking (retire the PLAN-0075 AC-13 `derivation_hash` code-hash
throwaway + rewrite its self-cancelling marker) **to whatever extent the ratified
SD-1 scope permits** — under the recommended SD-1 (A) it does NOT resolve here
(the ladder stays code-side, so the provider stays; PLAN-0076 Step T2 stays
honestly open), under (B) it resolves in-PLAN. This renders PLAN-0077 SD-4's
"SEPARATE parity-guarded follow-on PLAN migrates the two verticals' seeds"
(`0077:491-505`) and partially satisfies ADR-016 Q4 OQ-3's full-migration
conditional — **partially by design** (L-3): the `candidate_quotes` nest stays
seed-side per the SD-8 row-local wall, exactly the partial outcome the OQ-3
resolution itself contemplated (`0016:1306-1308`).

## LOCKED (ratified upstream — rendered faithfully; do NOT re-litigate)

- **L-1 (no new ADR).** This PLAN renders PLAN-0077 SD-4 (`0077:491-505`) + the
  ADR-016 Q4 OQ-3 "downstream transform home" whose full-migration conditional it
  partially satisfies (`0016:1302-1315`). It rides Accepted ADR-016 Q4 +
  ADR-0031 D3 row-1 (now shipped). If a real derivation cannot be honestly
  expressed by the shipped op-set → STOP and surface for an ADR-0031 amendment
  (the tripwire above — never an eval escape).
- **L-2 (parity is the bar).** Every migration is guarded by a zero-tolerance
  output-set parity test (the PLAN-0062 shape:
  `test_seed_migration_parity.py:1-15` — order-insensitive, key-complete,
  independent hand-coded reference) proving the declared-transform run is
  byte-equal to the seed run on the same inputs. **A migration that cannot be
  proven parity-equal does not land.**
- **L-3 (procurement migrates PARTIALLY).** The `candidate_quotes` N-rows→
  one-nested-list reshape (`_normalize_quotes`, `run.py:186-199`, threaded
  `:229`) stays seed-side — cardinality-changing, walled off by PLAN-0077 SD-8
  (`0077:558-577`); v1 transforms are row-local. Stated without overclaiming
  OQ-3's "full migration" (`0016:1306-1308` contemplated exactly this).
- **L-4 (F-PIN stays open).** The new-run re-routing threat (a fresh run on
  already-changed code pins the changed derivation without complaint) is an
  architectural property of per-run pinning, orthogonal to declaring derivations
  (`0077:338-341`; `cold_chain_assess.py:98-100`). **Nothing in this PLAN records
  F-PIN closed** — under any SD-1 outcome.
- **L-5 (offline binding bar only).** Deterministic, MS-S1-independent, no
  host-state — the derivation path has no LLM (ADR-0024 D3/D6). The offline suite
  + parity harness under CI `gate` is the ENTIRE bar. No live run.
- **L-6 (do not weaken the hardened authority path).** Whatever the SD-1 stamp
  scope, the PLAN-0074/0075 authority invariants — fail-closed gate readers
  (`governance_step.py` `_spend`/`_severity`), exact-Decimal arithmetic,
  unrepresentable bypass — remain intact and their suites green.

## Substrate facts (all re-verified on disk 2026-07-15)

**The grammar (shipped, PLAN-0077).**
`services/engine/procedures/transform_step.py` — `plan_transform` (compile;
shares `validate_transform_spec` with the load gate, L-6 no-drift, `:7-14`) +
`TransformStepExecutor` (`:197`, `@dataclass(frozen=True)`, fieldless,
ENGINE-GENERIC: "no adapter, no I/O, no LLM, no registry" `:16-17`, `:201-203` —
every composing factory can register ONE shared instance uniformly). Row-local
(SD-8), fail-closed (SD-7), exact-Decimal, JSONB-safe via `_json_safe` (the
derived Decimals coerce to their exact string form, exactly as the supply_chain
seed's coercions do, `:207-216`).

**The authoring examples (shipped, PLAN-0077 Phase C).**
`tests/services/engine/procedures/test_transform_fixtures_e2e.py` self-declares
"these procedures double as the authoring examples for the SD-4 migration PLAN"
(`:4-6`). Fixture A (procurement-shaped: criticality copy + unit default +
compliance map, `:139-179`) and fixture B (supply_chain-shaped: magnitude
arithmetic + defaults + compliance map + Decimal→str coercion, `:185-231`)
mirror the two seeds field-for-field. The marquee parity block (`:237-339`)
proves the grammar reproduces `derive_excursion_severity`'s exact
severity + ratio (bands built FROM the shipped `_DOSE_LADDER` constants,
`:52-56`) and `scored_rule`'s `amount` value-identically.

**OQ-3 registration gap.** `StepKind.TRANSFORM` is registered in NONE of the 4
production factories (grep: only test fixtures). The dicts:
procurement `verticals/procurement/hero_demo/run.py:286-290` (keys `:287-289`),
supply_chain `verticals/supply_chain/procedures_factory.py:285-303`,
energy `verticals/energy/procedures_factory.py:66-70`,
aquaculture `verticals/aquaculture/procedures_factory.py:72-76`.
**FIVE tests assert the exact key set** `{QUERY, EVALUATE, ACTION}` and BREAK the
instant a factory gains TRANSFORM — lockstep updates:
`tests/verticals/aquaculture/test_aquaculture_procedure_factory.py:119`,
`tests/verticals/energy/test_energy_procedure_factory.py:71`,
`tests/verticals/supply_chain/test_supply_chain_procedure_factory.py:78`,
`tests/verticals/procurement/test_operate_executor_factory.py:52`,
`tests/verticals/procurement/test_intake_shadow_parity.py:302`.
(A sixth, `test_example_procedures.py:59`, is a subset assertion — unaffected.)

**procurement seed** (`verticals/procurement/hero_demo/run.py:202-248`,
`_intake_seed`). MOVES to a declared transform: the `criticality =
measured_value` copy (`:227`), the `unit` default — production default value is
the string `"criticality"` (`:225`), and the `compliance` literal map
(`:237-243`). STAYS seed-side: the adapter reads + `event_type` carry (`:207-218`),
the requisition metadata (`:245-247`), and the `candidate_quotes` reshape
(`:186-199`, `:229` — L-3, including its element-wise `price_thb→unit_price`
rename inside the nested list, which is not row-local-top-level). Procedure step
topology (`verticals/procurement/procedures.yaml`): `intake` (`:112`) → `judge`
(`:124`) → `source` (`:142`, scored_rule) → `compliance` (`:186`, rule_gate) →
`approve` (`:217`, doa_tier) → `issue_po` → `audit`. The migration is
deliberately SMALL (3 ops) — its value is proving the declared pattern in
production + rendering the OQ-3 partial conditional honestly.

**supply_chain seed** (`verticals/supply_chain/procedures_factory.py:145-244`,
`_intake_seed`). MOVES: `excursion_magnitude_c = reading_c − temp_ceiling`
(`:189`, emitted `:204`), the `excursion_duration_h`/`stability_budget_ch`
authored defaults (`:205-206`), the GDP `compliance` map (`:237-242`), the
Decimal→str coercions (`:200-204`, `:208`). STAYS seed-side: the adapter reads +
`_latest_breach_reading` argmax selection (`:163-171`), the `magnitude_c <= 0`
eligibility early-return guard (`:190-191` — a filter, not a derivation; the
seed may keep computing the subtraction for the GUARD while no longer emitting
the field), and the `candidate_quotes` authored-literal lane list (`:212-234` —
nothing to derive). The seed is captured ONCE at registration (`:279`,
JSONB-coerced) and served as the `intake` query fallback
(`_DispositionSeed`, `:290`). Step topology
(`verticals/supply_chain/procedures.yaml`): `intake` (`:193`) → `assess`
(`:206`, scored_rule + severity stamp) → `gdp_gate` (`:247`) → `approve`
(`:278`, severity_tier) → `fulfill` (`:323`).

**The marquee stamps (the SD-1 fork's substance).** Kept code-side, byte-
untouched, by PLAN-0077 SD-1 — with the re-sequencing decision explicitly
deferred to THIS PLAN, "with PLAN-0075's reversal cost weighed" (`0077:376-379`):

- `amount = winner.unit_price × qty` at
  `services/engine/procedures/scored_rule.py:230` — computed on the **selection
  winner** inside `select_scored_supplier`, i.e. it is entangled with the scored
  choice mid-action-step. **Expressibility ≠ schedulability**: the PLAN-0077
  fixture proved the grammar computes the product value-identically
  (`test_transform_fixtures_e2e.py:305-339`), but no pre-gate row carries the
  winner's `unit_price` for a standalone transform step to consume — declaring
  it requires re-sequencing the `source` action itself.
- the `_DOSE_LADDER` severity (`verticals/supply_chain/cold_chain_assess.py:73-78`)
  stamped by `ColdChainAssessExecutor.execute` (`:225-260`) — which stamps NOT
  just the severity: also the `criticality` amplifier
  (`str(min(Decimal(1), d.ratio))`, `:239`), the `severity_derivation` audit
  payload (`:234`, `:256-259`), and per-derivation reasoning-trace entries
  (`:244-255`). Migrating the map_value alone does not retire the executor, and
  reproducing the audit/trace surface declaratively changes the observable run
  record.

These are the **freshly PLAN-0075-hardened authority path** (`scored_rule`,
`ColdChainAssessExecutor`, the `doa_tier`/`severity_tier` gate readers) — L-6.

**derivation_hash + F-PIN coupling.** Provider
`cold_chain_assess.py:82-106` (hashes `_DOSE_LADDER` + `_TOP_SEVERITY`;
PROVENANCE-ONLY, F-PIN open `:98-100`); registered
`procedures_factory.py:311`; registry hook `services/engine/registry.py:39`
(type) + `:136-163` (register/pull, recomputed-never-cached); snapshot fold-in
**only-when-supplied** `governance_pin.py:122-125` (None = byte-identical);
pass-through threading across **8 files** (grep-verified: `governance_pin.py`,
`orchestrator.py`, `action_step.py`, `event_bridge.py`, `persistence.py`,
`scheduler.py`, `registry.py`, `services/api/routers/runs.py`). Once a
derivation is a declared transform, the existing per-step pin covers it for free
— `_step_governance_snapshot` pins `step.transform` canonically, by_alias,
fail-closed at resume (`governance_pin.py:96-98`, shipped by PLAN-0077).
**The F-PIN marker**
(`tests/services/engine/procedures/test_derivation_pin.py:205-224`) asserts
BOTH `registry.derivation_hash("supply_chain") is not None` (`:215-217`) AND
`registry.derivation_hash("procurement") is None` (`:218-224`). Retiring
supply_chain's provider BREAKS the first assertion → the marker must be
**REWRITTEN**, not merely "fired" (PLAN-0076 Step T3 `:304-314`; Step T2
`:293-302` tracks the fold-in — and T3 additionally blocks PLAN-0076's archive
until its deferrals close or Cray re-adjudicates).

**Pin consequence of migrating (intended, stated plainly).** Adding a declared
transform step to a shipped `procedures.yaml` CHANGES that procedure's
governance snapshot and config hash (new step + `transform` key + re-pointed
threading) — by design: a declared derivation IS governance. A persisted
mid-flight run of a migrated procedure fails CLOSED at resume on the hash
mismatch (the pin working as intended, same class as a mid-flight ladder edit).
Procedures with no transform pin **byte-identically** to before
(`governance_pin.py:59-63` — the only-when-supplied key precedent).

## Surfaced Decisions

Each SD carries a recommendation; **Cray ratifies via AskUserQuestion at PR**;
none is silently decided. ACs/Steps are written to the recommendations and
re-scope mechanically if Cray picks otherwise.

- **SD-1 — THE central scope fork: marquee stamps in or out.**
  *Recommendation:* **(A) intake-only migration.** Migrate the intake enrichment
  derivations (magnitude / defaults / compliance maps / coercions /
  criticality-copy) to declared transforms; KEEP the marquee `amount` /
  `_DOSE_LADDER`-severity stamps code-side, byte-untouched. Consequences, stated
  honestly: `derivation_hash` STAYS (it cannot be retired without migrating the
  ladder), the F-PIN marker is left as-is (SD-5), PLAN-0076 Step T2 stays
  **open** (this PLAN does not fold F-PIN's remainder in — a future
  stamp-migration PLAN owns that), and the PLAN-0075-hardened authority path
  sees ZERO change (L-6 satisfied by construction).
  *Why (A) — the drafter's independent read, agreeing with Code's disclosed
  lean:* (i) **`amount` is not schedulable as a pre-gate transform at all** — it
  is computed on the scored-selection winner mid-action (`scored_rule.py:230`);
  declaring it means re-sequencing the `source` action, not inserting a step.
  (ii) **The severity stamp is not just a map_value** —
  `ColdChainAssessExecutor.execute` also stamps the `criticality` amplifier,
  the `severity_derivation` audit payload, and trace entries (`:239`,
  `:244-259`); a declarative replacement changes the observable run record,
  which is exactly what L-2's parity bar exists to forbid — option (B) would
  have to either violate its own parity bar or replicate an audit surface the
  grammar was never designed to emit. (iii) **Reversal cost**: PLAN-0075 just
  hardened these executors and gate readers; re-opening them weeks later to
  retire a cheap, working provenance hash is a poor trade — the throwaway costs
  ~nothing to keep (one provider + an only-when-supplied key). (A) proves the
  declared pattern in production first; (B) becomes its own follow-on PLAN with
  its own parity design once (A) is green.
  *Alternatives:* **(B) full migration incl. stamps** — re-sequence the
  `_DOSE_LADDER` severity (and `amount`) into declared transform steps so the
  per-step pin covers them; RETIRE `derivation_hash` (8 pass-through files) +
  REWRITE the F-PIN marker (PLAN-0076 T3) + close T2. Payoff: the code-hash
  throwaway dies now and the severity derivation becomes governed data
  end-to-end. Cost: touches the freshly-hardened path (L-6 risk), changes the
  run-record audit/trace shape (parity bar cannot be met as byte-equality —
  it would need a ratified relaxation), and the `amount` half needs an action
  re-sequencing design that does not exist yet. **(B-lite)** — migrate ONLY the
  `_DOSE_LADDER` (retirement needs only supply_chain's provider), keep `amount`
  code-side: smaller than (B) but inherits the same audit-surface + hardened-
  path problems; noted for completeness, not recommended.
  *Why Cray:* this sets how much of the just-hardened authority path this PLAN
  may approach, whether the run-record shape may move, and when PLAN-0076 T2
  closes — a risk-appetite + sequencing call, not a drafter call.

- **SD-2 — phasing.**
  *Recommendation:* **one PLAN, one vertical per PR** — PR-1 procurement, PR-2
  supply_chain — each PR carrying its own parity harness, landed **oracle-first**
  (harness passing against the CURRENT seed semantics in one commit, the flip in
  the next — the PLAN-0077 SD-5 two-commit discipline). Procurement first: the
  smaller diff (3 row-local ops, no arithmetic, no coercion) debugs the
  migration *mechanics* (yaml step insertion, threading, pin change, factory
  slimming) at minimum blast radius; supply_chain then reuses the proven
  mechanics for the richer transform. Suite green at every PR boundary.
  *Alternatives:* both verticals in one PR (one review boundary for two
  behavior flips of shipped demo verticals — needlessly wide); supply_chain
  first (the richer case earlier, but it debugs mechanics + arithmetic at once).
  *Why Cray:* PR boundaries = review boundaries on two demo-visible verticals.

- **SD-3 — OQ-3 registration scope: 2 factories or all 4.**
  *Recommendation:* **uniform — register `TransformStepExecutor()` in all 4
  factories**, updating all five exact-key tests in lockstep, as its own small
  Step-1 prep commit (pure-additive, zero behavior change: no shipped procedure
  declares a transform until the flips). Grounds: the executor is fieldless,
  frozen, adapter-free — the shipped design's own words are "every composing
  factory can register ONE shared instance uniformly"
  (`transform_step.py:16-18`, `:201-203`); uniform registration makes the
  engine posture consistent (any vertical may author a transform tomorrow
  without a confusing missing-executor failure) and the five tests are touched
  ONCE, never again.
  *Alternative:* narrow — only the 2 migrating factories (+ their 2 tests):
  smaller diff, but it leaves energy/aquaculture as delayed traps and touches
  the same test file set again the day either vertical declares a transform.
  *Why Cray:* it fixes the production registration posture across all verticals,
  not just this migration's.

- **SD-4 — parity-harness shape.**
  *Recommendation:* a **fresh module**
  (`tests/verticals/.../test_transform_migration_parity.py` per vertical, or one
  shared module under `tests/services/engine/procedures/` — executor's choice at
  R2) that **copies the PLAN-0062 comparator discipline** — zero-tolerance,
  order-insensitive, key-complete, and an **independent hand-coded reference**:
  the CURRENT seed's enriched intake rows frozen as hand-written expected
  fixtures (from the seed *contract*, not by calling the old code — so after the
  seed is slimmed the reference cannot silently drift, the
  `test_seed_migration_parity.py:6-13` property). The harness asserts (i) the
  enriched row set at the transform's output boundary is byte-equal to the
  frozen reference, and (ii) the downstream run record — verdicts, statuses,
  gate outcomes — is unchanged on the same inputs.
  *Alternative:* extend `test_seed_migration_parity.py` itself — rejected: that
  file is the PLAN-0062 query-migration guard with its own frozen reference
  semantics (argmax read migration); bolting a different migration's reference
  into it muddies both guards.
  *Why Cray:* the harness IS the L-2 bar; its independence property is what
  makes "provably unchanged" true rather than asserted.

- **SD-5 — F-PIN marker disposition (mechanically dependent on SD-1).**
  *Recommendation:* under the recommended **SD-1 (A): leave
  `test_fpin_residual_procurement_unpinned_marker`
  (`test_derivation_pin.py:205-224`) byte-untouched** — both of its assertions
  remain true (supply_chain's provider stays registered `:215-217`; procurement
  still registers no code-hash `:218-224`; declaring procurement's intake
  fields as transform data adds a per-step `transform` pin, NOT a
  `derivation_hash`, so the None assertion holds). PLAN-0076 T2/T3 stay open,
  honestly. Under **SD-1 (B) or (B-lite)**: the marker MUST be rewritten in the
  same PR that retires the provider (the first assertion breaks by
  construction) — rewrite it to assert both verticals' `derivation_hash` is
  None AND the migrated supply_chain procedure's pin carries the declared
  ladder as step-transform content; close PLAN-0076 T2 tracking in that same
  PR per T3 (`0076:304-314` — never delete/skip/weaken a marker without
  closing the tracking it guards, route to Cray).
  *Why Cray:* the marker is a Cray-governed tripwire (PLAN-0076 T3's own rule);
  its disposition follows from the SD-1 pick and must be ratified with it, not
  silently inherited.

## Steps

Build order = cheapest gate first; parity harness lands BEFORE each flip; suite
green at every boundary. Written to the SD recommendations (A / per-vertical PRs
/ uniform registration / fresh harness / marker untouched); re-scope
mechanically on a different ratification.

### Step 1 — Registration prep (SD-3; AC-1): uniform `TransformStepExecutor` + lockstep tests
Add `StepKind.TRANSFORM: TransformStepExecutor()` to all 4 production factories
(`run.py:286-290`, `procedures_factory.py:285-303` (supply_chain), `:66-70`
(energy), `:72-76` (aquaculture)); update the five exact-key assertions to
`{QUERY, EVALUATE, ACTION, TRANSFORM}` (`test_aquaculture_procedure_factory.py:119`,
`test_energy_procedure_factory.py:71`,
`test_supply_chain_procedure_factory.py:78`,
`test_operate_executor_factory.py:52`, `test_intake_shadow_parity.py:302`);
confirm the subset assertion (`test_example_procedures.py:59`) is untouched.
Pure-additive — no shipped procedure declares a transform yet; zero behavior
change; full suite green. Lands as the first commit(s) of PR-1 (or its own tiny
prep PR — executor's call at R2, OQ-2).

### Step 2 — PR-1 procurement (SD-2; AC-2, AC-4, AC-5): oracle first, then the flip
1. **Oracle commit:** the SD-4 parity harness for procurement — hand-coded
   frozen reference of the CURRENT enriched intake row (criticality copy, unit
   default `"criticality"`, compliance map, plus every seed-side field that
   STAYS: event_type, qty, candidate_quotes, requisition metadata), asserted
   byte-equal against the CURRENT production factory's run; downstream verdicts
   (judge band, scored_rule selection + amount, rule_gate, doa_tier) pinned.
   Passing = the reference is proven correct against the pre-flip world.
2. **Flip commit:** add the declared `enrich` transform step to
   `verticals/procurement/procedures.yaml` between `intake` (`:112`) and
   `judge` (`:124`) — ops per fixture A / the PLAN-0077 SD-2 sketch: the
   `criticality` typed copy, `default: {target: unit, value: criticality}`,
   the `compliance` literal map; thread per the shipped `input.from`
   convention (fixtures, `test_transform_fixtures_e2e.py:139-179`) with the
   downstream re-point; give the step its governance facet
   (`decision_condition: {gate_kind: none}`, mirroring the query steps).
   Slim `_intake_seed` (`run.py:202-248`): remove `criticality` (`:227`),
   `unit` (`:225`), `compliance` (`:237-243`) from the emitted dict; keep
   everything that STAYS (L-3). Re-run the harness — byte-equal or the flip
   does not land (L-2).
3. Update the seed/module docstrings honestly (✖→✔ for the migrated fields;
   the nest + reads labelled as the remaining seed residue, L-3); PR per §7.

### Step 3 — PR-2 supply_chain (SD-2; AC-3, AC-4, AC-5): oracle first, then the flip
1. **Oracle commit:** the parity harness for supply_chain — frozen reference of
   the CURRENT enriched disposition row (`:193-244`: magnitude `"4"`-form
   string, duration/budget defaults, GDP compliance map, coercion forms, plus
   the STAYS fields: identity, reading_c/temp_ceiling strings, qty, currency,
   candidate_quotes, quarantine_status), asserted against the current factory
   run; downstream verdicts (assess selection, severity stamp, gdp_gate,
   severity_tier approve) pinned.
2. **Flip commit:** add the declared `enrich` transform step to
   `verticals/supply_chain/procedures.yaml` between `intake` (`:193`) and
   `assess` (`:206`) — ops per fixture B (`test_transform_fixtures_e2e.py:185-206`):
   `excursion_magnitude_c` sub-derive from `reading_c`/`temp_ceiling`,
   duration/budget defaults, compliance map, Decimal→str coercion(s). Slim
   `_intake_seed` (`procedures_factory.py:145-244`): stop emitting the derived
   fields; KEEP the adapter reads, `_latest_breach_reading`, and the
   `magnitude_c <= 0` guard (`:190-191` — the seed may keep the subtraction for
   the guard while no longer emitting it; the exact guard form is OQ-1). Verify
   the registration-time JSONB capture (`:279`) still round-trips the slimmed
   row. Re-run the harness — byte-equal or no landing (L-2).
3. Docstring honesty pass (the `_DispositionSeed`/`_intake_seed` AUTHORED-half
   labels move to the yaml transform; the eligibility-predicate follow-on note
   `:158-162` stays); PR per §7.

### Step 4 — Pin + marker + closeout (AC-5, AC-6, AC-7, AC-8)
- Pin tests: the two migrated procedures' snapshots carry the canonical
  `transform` key (`governance_pin.py:96-98`) and a mid-flight transform edit
  fails closed at resume (the existing pin-test pattern); every NO-transform
  procedure (energy, aquaculture, and the untouched procedures inside the two
  migrated yamls) pins **byte-identically** to before (AC-6).
- SD-5 per ratification: under (A) assert the F-PIN marker still passes
  untouched; under (B)/(B-lite) execute the rewrite + PLAN-0076 T2 closure in
  the retiring PR.
- Authority-path regression: the PLAN-0074/0075 suites green, stamps
  byte-untouched under (A) (L-6, AC-7).
- STATUS update in the merged PRs (or immediate `docs(status):` reconcile);
  `git mv docs/plans/0078-*.md docs/plans/done/` on completion. If ADR-0031's
  D3 row-1 warrants a "migrated" annotation (D4.4), that is an Accepted-body
  edit → drafter-authored, ratified in one pass (OQ-3 below) — never edited
  in-PLAN.

## Acceptance Criteria

Written to the SD recommendations; re-scope mechanically if Cray picks otherwise.

- [ ] **AC-1 (registration).** `TransformStepExecutor` registered per the
  ratified SD-3 scope (recommended: all 4 factories); the five exact-key tests
  updated in lockstep; the subset assertion untouched; full suite green with
  zero behavior change before any flip.
- [ ] **AC-2 (procurement parity flip).** The declared `enrich` transform
  (criticality copy + unit default + compliance map) replaces the seed's
  emission of those fields; the SD-4 zero-tolerance harness proves the enriched
  row set AND the downstream run record (judge/source/compliance/approve
  verdicts, run status) byte-equal to the frozen pre-flip reference on the same
  inputs. The `candidate_quotes` nest + reads + metadata stay seed-side,
  honestly labelled (L-3).
- [ ] **AC-3 (supply_chain parity flip).** The declared `enrich` transform
  (magnitude derive + defaults + compliance map + coercions) replaces the
  seed's emission of those fields; the harness proves row-set + run-record
  byte-equality including the exact string forms (`"4"`-style magnitude). The
  reads, breach-selection, eligibility guard, and lane list stay seed-side.
- [ ] **AC-4 (fail-closed intact).** A missing/non-coercible source field on a
  migrated transform refuses the whole step typed (SD-7 posture inherited from
  the shipped executor) — demonstrated per vertical with a mutated fixture row.
- [ ] **AC-5 (pin coverage).** Each migrated procedure's governance snapshot
  carries the transform canonically (`governance_pin.py:96-98`); a mid-flight
  transform edit fails closed at resume. The config-hash change on the two
  migrated procedures is asserted INTENDED (a fresh pin), not silently absorbed.
- [ ] **AC-6 (byte-identical non-participants).** Every procedure declaring no
  transform — energy, aquaculture, and the untouched procedures in both
  migrated yamls — produces a governance snapshot and config hash byte-identical
  to pre-migration (the only-when-supplied property, `governance_pin.py:59-63`,
  `:122-125`).
- [ ] **AC-7 (authority path untouched — L-6).** Under SD-1 (A): `scored_rule.py`,
  `cold_chain_assess.py`, and the `governance_step.py` gate readers are
  byte-untouched (diff-verified at R2); the PLAN-0074/0075 suites green.
- [ ] **AC-8 (F-PIN honesty — L-4 + SD-5).** Under (A): the F-PIN marker passes
  untouched; PLAN-0076 T2 recorded still-open in this PLAN's closeout. Under
  (B)/(B-lite): the marker rewritten + T2 closed in the retiring PR per T3.
  In ALL cases: no artifact of this PLAN records F-PIN closed.

## Out of Scope

- ❌ **Closing F-PIN's new-run re-routing threat** — architectural, stays open
  (L-4; `cold_chain_assess.py:98-100`).
- ❌ **The marquee stamp migration under the recommended SD-1 (A)** — `amount` /
  `_DOSE_LADDER` re-sequencing is its own follow-on PLAN if/when ratified
  (becomes IN scope only if Cray picks (B)/(B-lite)).
- ❌ **The deferred transform ops** — `unit_convert`, `extract`, `normalize`,
  `derive(concat)`, discrete `map_value` (zero instances; PLAN-0077 L-7).
- ❌ **The `candidate_quotes` nest / any cardinality-changing reshape** (SD-8
  wall; procurement partial, L-3) — if execution finds the nest indispensable,
  that is the tripwire path (surface for an ADR-0031 amendment), never an
  in-PLAN invention.
- ❌ **Eligibility predicates** (the `magnitude_c <= 0` guard,
  `procedures_factory.py:158-162` note) — a declarative filter is a different
  construct from a derivation; it waits for its own trigger.
- ❌ **Any new ADR, ontology change, regen, or Alembic migration** — yaml +
  seed + factory + tests only (and per project memory: only energy has a
  committed ORM table; nothing here touches it).
- ❌ **Any LLM / live / host-state run** (L-5) — this PLAN never touches MS-S1.
- ❌ **Editing ADR-0031 in this PLAN** — a D4.4 row annotation, if warranted, is
  a drafter-authored Accepted-body edit ratified in one pass (OQ-3).

## Verification

Offline under CI `gate` — the ENTIRE bar (L-5); no live run, no `docs/logs/`
evidence note. The AC matrix above, concretely: per-vertical zero-tolerance
output-set parity (declared-transform run == frozen seed reference, rows AND
run record); the exact-key factory tests green post-registration; the
PLAN-0074/0075 authority suites green with stamps diff-verified untouched
(SD-1 A); the F-PIN marker green per SD-5; migrated procedures pin the
transform + fail closed on mid-flight edit; every no-transform procedure pins
byte-identically. Pass/fail reads are fixed in the harness BEFORE each flip
commit (oracle-first — Lesson #0026 discipline).

## Open Questions

- **OQ-1 (guard form).** After the magnitude field moves to the declared
  transform, does the supply_chain seed keep computing `reading_c − ceiling`
  solely for the `<= 0` eligibility guard (`:190-191`), or switch the guard to
  the equivalent direct compare `reading_c <= ceiling`? Recommendation: keep
  the subtraction (smallest diff, same semantics); executor decides at R2 —
  parity harness is indifferent (the guard's emit path is unchanged either way).
- **OQ-2 (prep landing).** Step 1's uniform registration: first commits of PR-1,
  or its own tiny prep PR? Recommendation: fold into PR-1 (it is pure-additive
  and reviewed against the flip that motivates it); executor's call.
- **OQ-3 (ADR-0031 D4.4 row annotation).** On completion, does D3 row-1's
  status text warrant a "seeds migrated (partial per SD-8)" annotation? If yes:
  Accepted-body edit → route to plan-drafter, ratified in one pass (G1;
  project memory: never flip-then-edit). Not blocking this PLAN's archive.
- **OQ-4 (in-flight runs at deploy).** The migrated procedures' config hash
  changes; any persisted mid-flight run fails closed at resume (intended pin
  behavior). Demo runs are ephemeral so no migration shim is planned — confirm
  no durable environment holds in-flight runs of these two procedures at
  merge time (a Cray confirm at PR, not a code change).

## Size estimate

- **PR-1 (procurement + prep):** ~8-10 files — 4 factory files + 5 test files
  (Step 1), `procedures.yaml`, `hero_demo/run.py` (seed slim), 1 new parity
  module, pin-test additions. Small-medium.
- **PR-2 (supply_chain):** ~4-6 files — `procedures.yaml`,
  `procedures_factory.py`, 1 new parity module, pin-test additions, docstring
  honesty pass. Small-medium.
- Under SD-1 (B) instead: + the 8-file `derivation_hash` pass-through
  retirement + marker rewrite + executor re-sequencing — a materially larger,
  riskier PLAN (part of why (A) is recommended).
