# PLAN-0078: transform seed-migration — migrate the two shipped verticals' derived fields (the intake halves AND the marquee severity/amount stamps) from execution-bound ✖ to declared `transform` ✔, parity-guarded in two phases

**Status:** Proposed — **SD-1..SD-8 ALL RATIFIED by Cray 2026-07-15** via AskUserQuestion
(SD-1 = **(B) full migration incl. the marquee stamps** — an informed risk-appetite
call against the draft's (A) recommendation, made with the two on-disk findings in
view; SD-6 = **two-tier parity bar**, SD-7 = **slim `ColdChainAssessExecutor` to a
fail-closed scalar guard**, SD-8 = **one derivation home** — all as recommended).
Every SD carries its ratified pick below; the build (5 PRs, two phases) is the next
session's execution work.
**Owner:** Claude Code (executes); Cray ratifies the surfaced decisions
**Created:** 2026-07-15 (revised same day: (A)→(B) re-scope on Cray's ratification)
**Related ADRs:** **ADR-0031** D3 row-1 (the transform grammar this PLAN puts to
work — shipped by PLAN-0077); **ADR-016 Q4** OQ-3 resolution
(`docs/adr/0016-governed-procedure-engine.md:1302-1315` — "a downstream transform
step" is the designated home; its own text contemplates procurement migrating
**PARTIALLY**, `0016:1306-1308`). **No new ADR** (L-1). Also: ADR-0024 D3/D6
(governed ≠ generated — no LLM in the derivation path), ADR-0025 D3
(bypass-unrepresentable), ADR-009 D1/D2 + ADR-012 D4.3 + ADR-013 D1
(authoring/commit boundaries + disclosure).
**Related PLANs:** **PLAN-0077**
(`docs/plans/done/0077-transform-grammar-build.md` — the build PLAN whose SD-4
(`0077:491-505`) split THIS migration out; its SD-8 row-local wall
(`0077:558-577`) bounds the intake scope; its SD-1 stamp deferral (`0077:376-379`)
is the deferral Phase 2 now renders); **PLAN-0062** (the parity-harness precedent,
`tests/services/engine/procedures/test_seed_migration_parity.py:1-15`);
**PLAN-0075** (the freshly-hardened authority path L-6 protects; AC-13
`derivation_hash` — **retired by Phase 2**); **PLAN-0076**
(`docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` — Step
T2 `:293-302` tracks the F-PIN fold-in **which this PLAN now closes**, Step T3
`:304-314` governs the marker rewrite; T1 stays open, so PLAN-0076 does NOT
archive here); PLAN-0061 (the build→migrate split template); PLAN-0074 (the
fail-closed gate readers).

> **Drafting provenance (ADR-012 D4.3 / ADR-013 OQ-1).** Authored by the
> in-harness `plan-drafter` subagent under ADR-013 D1 phased authority. Dispatch
> originated by Code; direction by Cray (picked the SD-4 migration as the #1
> next-work item via next-work-analyst, then typed "(ก)"). Independent review:
> Code (R2) at PR — every `file:line` citation re-verified on disk; ratification:
> Cray. Author≠reviewer separation: **INTACT**. Uncommitted draft — Code commits
> per ADR-009 D2; the drafter does not git.
> **Ratification record (2026-07-15):** Cray ratified **SD-1 = (B)** (full
> migration incl. the marquee stamps — against the draft's (A) recommendation;
> Cray saw the two on-disk findings — `amount` is not schedulable without
> re-sequencing the action, and the severity stamp is more than a map_value —
> and made an informed risk-appetite call to take the fuller, riskier scope) and
> the **SD-2..SD-5 recommendations** (procurement-first one-vertical-per-PR
> oracle-first; uniform registration; fresh parity-harness module; marker
> rewrite + T2 closure — the (B) branch) via AskUserQuestion. The (A)→(B)
> re-scope of this document was performed by the drafter on Cray's ratification;
> **SD-6** (parity-bar semantics), **SD-7** (executor disposition), and **SD-8**
> (amount re-sequencing shape) are newly surfaced as the consequence of (B).
> The original dispatch fact-pack was independently re-verified by the drafter
> against the working tree 2026-07-15; drift found and corrected in-draft: the
> per-step transform pin sits at `governance_pin.py:96-98` (not `:81-85` — that
> range is the PLAN-0061 join pin; the fact-pack citation predates the PLAN-0077
> transform key), the snapshot fold-in at `:122-125` (not `:111-115`), the
> supply_chain executor dict spans `procedures_factory.py:285-303` (not
> `:286-295`), and the fixtures' self-declaration sits in the module docstring at
> `test_transform_fixtures_e2e.py:4-6`. A sixth key-set assertion
> (`tests/services/engine/procedures/test_example_procedures.py:59`) uses a
> SUBSET check (`<=`) and tolerates TRANSFORM — it needs **no** change; only the
> five exact-equality tests move in lockstep. **Phase-2 re-verification (at the
> (B) revision):** `min`/`max` ARE shipped derive operators
> (`transform_step.py:412-415`) so the criticality clamp is expressible;
> `map_value.source` is a full `Expr` (`:296-299`) so severity can band a nested
> `div(mul(...),...)` without materializing intermediates; the transform's
> `_to_decimal` accepts NEGATIVE scalars (`:360-388` — only non-numeric /
> non-finite refuse) while the executor's `_positive_decimal` fails closed on
> non-positive (`cold_chain_assess.py:119-145`) — the guard-loss hazard SD-7
> exists to adjudicate; and the `amount` stamp lives in the ENGINE-GENERIC
> `_scored_rule` branch shared by **four** scored_rule steps across THREE
> procurement procedures + supply_chain's `assess` (grep-verified, anchors
> re-verified 2026-07-16 post-Phase-1: `verticals/procurement/procedures.yaml`
> `kind: scored_rule` at `:196,543,878`; `verticals/supply_chain/procedures.yaml`
> `kind:` at `:264` + `gate_kind:` at `:281`) — the SD-8 blast radius.

> **Tripwire (inherited from PLAN-0077, absolute).** If execution finds a real
> derivation the shipped whitelisted op-set cannot honestly express — STOP and
> surface for an ADR-0031 amendment. Do **NOT** invent an eval escape hatch
> (ADR-0031 D2 tripwire 1); an inexpressible derivation stays code-side, honestly
> labelled, until Cray amends the row. Never bake a deviation in. (Phase-2 note:
> the severity band, the criticality clamp, and the amount product were
> re-verified expressible against the shipped op-set at revision time; the
> POSITIVITY guard is verified NOT expressible — that is SD-7's subject, handled
> by keeping it code-side, not by inventing an op.)

## Goal

Put the PLAN-0077 grammar to work in production, in **two phases inside one
PLAN** — the low-risk intake migration first, so the declared pattern is proven
before the hardened path is touched:

- **Phase 1 — intake migration.** Migrate the two shipped verticals'
  derived-field **intake halves** from execution-bound-in-seed-code (✖) to
  **declared `transform` steps** (✔) in their `procedures.yaml` — procurement
  (criticality copy + unit default + compliance map; the `candidate_quotes`
  nest stays seed-side, L-3 partial) and supply_chain (magnitude derive +
  defaults + GDP compliance + Decimal→str coercions) — each guarded by a
  **zero-tolerance full-byte parity harness** (the PLAN-0062 precedent).
- **Phase 2 — stamp re-sequencing (the ratified SD-1 (B) work).** Move the two
  marquee derivations off the freshly-hardened executors into declared
  transforms: the `_DOSE_LADDER` **severity** (+ the `criticality` amplifier)
  out of `ColdChainAssessExecutor`, and the **`amount = unit_price × qty`**
  spend out of the `scored_rule` action path — the gate READERS (`_spend`,
  `_severity`) stay byte-untouched; only WHO stamps the fields they read moves.
  Then **retire `derivation_hash`** (the PLAN-0075 AC-13 code-hash throwaway —
  the per-step transform pin covers the ladder for free once it is declared
  data), **rewrite the F-PIN marker**, and **close PLAN-0076 Step T2** in the
  retiring PR per T3. Parity for this phase is the **SD-6 two-tier bar**
  (output-row byte parity + semantic run-record equivalence — the provenance
  surface changes FORM by design).

This renders PLAN-0077 SD-4's "SEPARATE parity-guarded follow-on PLAN migrates
the two verticals' seeds" (`0077:491-505`) AND its SD-1 stamp-re-sequencing
deferral (`0077:376-379`, "with PLAN-0075's reversal cost weighed" — Cray
weighed it and picked (B)), and satisfies ADR-016 Q4 OQ-3's full-migration
conditional — **still partially** (L-3): the `candidate_quotes` nest stays
seed-side per the PLAN-0077 SD-8 row-local wall, exactly the partial outcome
the OQ-3 resolution itself contemplated (`0016:1306-1308`). **F-PIN's new-run
re-routing threat stays OPEN** (L-4) — only the T2 remainder fold-in closes.

## LOCKED (ratified — rendered faithfully; do NOT re-litigate)

- **L-1 (no new ADR).** This PLAN renders PLAN-0077 SD-4 (`0077:491-505`) + SD-1
  (`0077:376-379`) + the ADR-016 Q4 OQ-3 "downstream transform home"
  (`0016:1302-1315`). It rides Accepted ADR-016 Q4 + ADR-0031 D3 row-1 (shipped).
  If a real derivation cannot be honestly expressed by the shipped op-set →
  STOP and surface for an ADR-0031 amendment (the tripwire above — never an
  eval escape).
- **L-2 (parity is the bar — TWO-TIER, per SD-1 (B) + SD-6).**
  - **Phase 1 (intake): full byte parity.** Zero-tolerance output-set parity
    (the PLAN-0062 shape: `test_seed_migration_parity.py:1-15` —
    order-insensitive, key-complete, independent hand-coded reference) proving
    the declared-transform run is byte-equal to the seed run — **rows AND run
    record** — on the same inputs.
  - **Phase 2 (stamps): output-row byte parity + semantic run-record
    equivalence** — the **SD-6 ratified two-tier bar** (Cray 2026-07-15): every
    governance-relevant entity field
    the gates read (`excursion_severity`, `criticality`, `amount`, and all
    Phase-1 intake fields) byte-equal to the pre-migration stamp output, PLUS
    identical verdicts / statuses / gate outcomes / final run status, PLUS a
    provenance surface that — though changed in form (executor audit+trace →
    transform provenance) — remains **complete** (every derivation that was
    traced is still traced). Byte-equality of the whole run record is
    impossible for Phase 2 **by design** (the derivation's provenance home
    moves); that impossibility is why SD-6 exists rather than a silent
    relaxation.
  - In BOTH phases: **a migration that cannot be proven parity-equal at its
    tier does not land.**
- **L-3 (procurement intake migrates PARTIALLY).** The `candidate_quotes`
  N-rows→one-nested-list reshape (`_normalize_quotes`, `run.py:186-199`,
  threaded `:229`) stays seed-side — cardinality-changing, walled off by
  PLAN-0077 SD-8 (`0077:558-577`); v1 transforms are row-local. Stated without
  overclaiming OQ-3's "full migration" (`0016:1306-1308` contemplated exactly
  this).
- **L-4 (F-PIN stays open).** The new-run re-routing threat (a fresh run on
  already-changed code — or now, already-changed declared data — pins the
  changed derivation without complaint) is an architectural property of per-run
  pinning, orthogonal to declaring derivations (`0077:338-341`;
  `cold_chain_assess.py:98-100`). **Nothing in this PLAN records F-PIN
  closed** — Phase 2 closes only the PLAN-0076 T2 remainder fold-in (retire the
  code-hash + rewrite the marker); the threat itself remains open and tracked.
- **L-5 (offline binding bar only).** Deterministic, MS-S1-independent, no
  host-state — the derivation path has no LLM (ADR-0024 D3/D6). The offline
  suite + parity harnesses under CI `gate` are the ENTIRE bar. No live run.
- **L-6 (the authority INVARIANTS hold — the crux of the (B) risk, stated
  precisely).** Phase 2 deliberately re-sequences the PLAN-0074/0075-hardened
  STAMPING executors — so "byte-untouched authority path" is no longer the
  contract. The contract is: the authority **invariants** remain intact and
  their PLAN-0074/0075 suites green at every PR boundary — (i) the fail-closed
  gate READERS are **byte-untouched**: `_spend` (`governance_step.py:47`) and
  `_severity` (`governance_step.py:81`) read the SAME fields off the entity and
  fail closed on absence/unrecognized exactly as before — what moves is **who
  stamps the fields they read**, never how they are read; (ii) exact-`Decimal`
  arithmetic end-to-end (the transform executor shares the discipline,
  `transform_step.py:207-216`); (iii) bypass stays unrepresentable (ADR-0025
  D3 — the transform grammar has no call/attribute/code node,
  `transform_step.py:332-340`); (iv) the fail-closed posture on the severity
  scalars is **preserved**, not silently dropped (the SD-7 subject — the
  grammar cannot express the positivity guard, so it stays code-side per the
  ratified SD-7 shape).

## Substrate facts (all re-verified on disk 2026-07-15, incl. at the (B) revision)

**The grammar (shipped, PLAN-0077).**
`services/engine/procedures/transform_step.py` — `plan_transform` (compile;
shares `validate_transform_spec` with the load gate, no-drift, `:7-14`) +
`TransformStepExecutor` (`:197`, `@dataclass(frozen=True)`, fieldless,
ENGINE-GENERIC: "no adapter, no I/O, no LLM, no registry" `:16-17`, `:201-203` —
every composing factory can register ONE shared instance uniformly). Row-local
(PLAN-0077 SD-8), fail-closed (PLAN-0077 SD-7), exact-Decimal, JSONB-safe via
`_json_safe` (derived Decimals coerce to their exact string form, `:207-216`).
**Phase-2-relevant op inventory (verified):** `derive` expression ops include
`add`/`mul`/`sub`/`div`/**`min`**/**`max`** (`:403-423`) — the criticality
clamp `min(1, ratio)` IS expressible; `map_value` bands a **full nested
`Expr` source** (`:296-299` + `_band` `:319-330`, inclusive-ceiling
ascending + mandatory unbounded `above` top — reproducing
`derive_excursion_severity` semantics exactly) — so severity can band
`div(mul(magnitude, duration), budget)` directly, without materializing
intermediate fields; every op emits a `transform_provenance` trace entry
(op/target/rows-written, `:241-254`) and a deterministic audit block
(`:255-262`). **Verified NOT expressible:** a strictly-positive guard — the
executor's `_to_decimal` refuses only non-numeric/non-finite (`:360-388`); a
NEGATIVE scalar flows through arithmetic legally (a negative ratio would band
to the LOWEST severity — fail-dangerous), whereas the current
`_positive_decimal` fails CLOSED on non-positive (`cold_chain_assess.py:119-145`).
This asymmetry is SD-7's subject.

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
`_intake_seed`). MOVES (Phase 1) to a declared transform: the `criticality =
measured_value` copy (`:227`), the `unit` default — production default value is
the string `"criticality"` (`:225`), and the `compliance` literal map
(`:237-243`). STAYS seed-side: the adapter reads + `event_type` carry (`:207-218`),
the requisition metadata (`:245-247`), and the `candidate_quotes` reshape
(`:186-199`, `:229` — L-3, including its element-wise `price_thb→unit_price`
rename inside the nested list, which is not row-local-top-level). Hero procedure
step topology (`verticals/procurement/procedures.yaml`): `intake` (`:112`) →
`judge` (`:124`) → `source` (`:142`, scored_rule) → `compliance` (`:186`,
rule_gate) → `approve` (`:217`, doa_tier) → `issue_po` → `audit`. The Phase-1
migration is deliberately SMALL (3 ops) — its value is proving the declared
pattern in production at minimum blast radius.

**supply_chain seed** (`verticals/supply_chain/procedures_factory.py:145-244`,
`_intake_seed`). MOVES (Phase 1): `excursion_magnitude_c = reading_c −
temp_ceiling` (`:189`, emitted `:204`), the
`excursion_duration_h`/`stability_budget_ch` authored defaults (`:205-206`), the
GDP `compliance` map (`:237-242`), the Decimal→str coercions (`:200-204`,
`:208`). STAYS seed-side: the adapter reads + `_latest_breach_reading` argmax
selection (`:163-171`), the `magnitude_c <= 0` eligibility early-return guard
(`:190-191` — a filter, not a derivation), and the `candidate_quotes`
authored-literal lane list (`:212-234` — nothing to derive). The seed is
captured ONCE at registration (`:279`, JSONB-coerced) and served as the `intake`
query fallback (`_DispositionSeed`, `:290`). Step topology
(`verticals/supply_chain/procedures.yaml`): `intake` (`:193`) → `assess`
(`:206`, scored_rule + severity stamp) → `gdp_gate` (`:247`) → `approve`
(`:278`, severity_tier) → `fulfill` (`:323`).

**The marquee stamps (the Phase-2 work).** Kept code-side by PLAN-0077 SD-1 with
the re-sequencing decision explicitly deferred to THIS PLAN, "with PLAN-0075's
reversal cost weighed" (`0077:376-379`) — Cray weighed it and ratified (B):

- **severity + criticality.** `ColdChainAssessExecutor.execute`
  (`verticals/supply_chain/cold_chain_assess.py:225-260`) derives each entity's
  severity via `derive_excursion_severity` (`:174-202` — dose = magnitude ×
  duration `:189`; ratio = dose / budget `:190`; severity = first
  `_DOSE_LADDER` band covering the ratio, else `_TOP_SEVERITY` `:191-194`;
  ladder constants `:73-78`) and STAMPS onto the entity: `excursion_severity`
  (`:233`), the `severity_derivation` audit payload (`:234`, values via
  `SeverityDerivation.to_audit` `:161-171`), and the `criticality` amplifier
  `str(min(Decimal(1), d.ratio))` (`:239`); it then appends `severity_derived`
  reasoning-trace entries (`:244-255`) and a step-audit `severity_derivation`
  list (`:256-259`). Its scalars are guarded strictly-positive + finite by
  `_positive_decimal` (`:119-145`, fail-closed). The downstream `severity_tier`
  gate READER (`governance_step._severity`, `:81`) reads `excursion_severity`
  off the entity and fails closed — it is untouched by the re-sequencing.
- **amount.** `amount = winner.unit_price × qty` is computed on the
  **scored-selection winner** inside `select_scored_supplier`
  (`services/engine/procedures/scored_rule.py:230`, on the
  `ScoredRuleVerdict`) and stamped onto the threaded entity by the
  ENGINE-GENERIC `_scored_rule` branch (`governance_step.py:285` method;
  the enriched stamp `"amount": str(v.amount)` at `:321-329`) for the
  `doa_tier` READER (`_spend`, `:47`) to resolve. `amount` depends on the
  selected winner, so a transform can only derive it AFTER the action threads
  the winner's `unit_price` onto the entity — the SD-8 re-sequencing.
  **Blast radius (verified):** `_scored_rule` serves FOUR scored_rule steps —
  procurement's three scored_rule-bearing procedures
  (`verticals/procurement/procedures.yaml:196,543,878` — the hero
  `emergency_sourcing_round` + its two scheduled/auto variants) and
  supply_chain's `assess` (`verticals/supply_chain/procedures.yaml:264`, whose
  `gate_kind` sits at `:281`). Anchors re-verified 2026-07-16 post-Phase-1.
  Changing the stamp touches all four; each affected procedure needs its own
  declared `derive_spend` transform (or the SD-8 alternative).

These executors + readers are the **freshly PLAN-0075-hardened authority path**
— L-6 states exactly which parts move (stamping) and which are inviolable
(reading, Decimal exactness, bypass-unrepresentable, fail-closed scalars).

**derivation_hash + F-PIN coupling (retired by Phase 2).** Provider
`cold_chain_assess.py:82-106` (hashes `_DOSE_LADDER` + `_TOP_SEVERITY`;
PROVENANCE-ONLY, F-PIN open `:98-100`); registered
`procedures_factory.py:311`; registry hook `services/engine/registry.py:39`
(type) + `:136-163` (register/pull, recomputed-never-cached); snapshot fold-in
**only-when-supplied** `governance_pin.py:122-125` (None = byte-identical);
pass-through threading across **8 files** (grep-verified at revision:
`governance_pin.py`, `orchestrator.py`, `action_step.py`, `event_bridge.py`,
`persistence.py`, `scheduler.py`, `registry.py`,
`services/api/routers/runs.py`). Once the ladder is a declared transform, the
existing per-step pin covers it for free — `_step_governance_snapshot` pins
`step.transform` canonically, by_alias, fail-closed at resume
(`governance_pin.py:96-98`, shipped by PLAN-0077) — so the code-hash throwaway
retires. **The F-PIN marker**
(`tests/services/engine/procedures/test_derivation_pin.py:205-224`) asserts
BOTH `registry.derivation_hash("supply_chain") is not None` (`:215-217`) AND
`registry.derivation_hash("procurement") is None` (`:218-224`). Retiring
supply_chain's provider BREAKS the first assertion → the marker is
**REWRITTEN** (never deleted/skipped/weakened) in the retiring PR, and
PLAN-0076 Step T2 (`:293-302`) is closed in that same PR per Step T3
(`:304-314`). T3 also blocks PLAN-0076's archive until BOTH its deferrals
close — its T1 (gate-plugin seam) stays open, so **PLAN-0076 does NOT archive
here** and its AC-6 guard-test stays.

**Pin consequence of migrating (intended, stated plainly).** Adding a declared
transform step to a shipped `procedures.yaml` CHANGES that procedure's
governance snapshot and config hash (new step + `transform` key + re-pointed
threading) — by design: a declared derivation IS governance. Under the full (B)
scope, up to FIVE shipped procedures' pins change across the PRs (the two
Phase-1 intake migrations; supply_chain again at the severity PR; the three
procurement scored_rule procedures + supply_chain at the amount PR). A
persisted mid-flight run of a migrated procedure fails CLOSED at resume on the
hash mismatch (the pin working as intended). Procedures with no transform pin
**byte-identically** to before (`governance_pin.py:59-63` — the
only-when-supplied key precedent) — until Phase 2 removes `derivation_hash`,
after which supply_chain's snapshot loses that key too (an intended,
asserted pin change in the retiring PR, not a silent one).

## Surfaced Decisions

SD-1..SD-8: **ALL RATIFIED by Cray 2026-07-15** via AskUserQuestion (each
recorded below — none open). Phase-2 Steps/ACs execute on the ratified
SD-6/SD-7/SD-8. **OQ-5 (`dose_ch`/`ratio` materialization) — RATIFIED by Cray
2026-07-16: (a) materialize** (see Open Questions); it calibrates SD-6(ii)'s
"provenance remains complete" clause at the VALUE level and is a Step-4
precondition.

- **SD-1 — scope fork: marquee stamps in or out. RATIFIED: (B) full migration
  incl. the stamps.** The draft recommended (A) intake-only on three grounds
  (amount not schedulable without action re-sequencing; the severity stamp is
  more than a map_value — audit/trace surface changes; PLAN-0075 reversal
  cost). Cray reviewed those findings and made an informed risk-appetite call
  for (B): the code-hash throwaway dies now, the severity + spend derivations
  become governed data end-to-end, and the price — a form-change in the
  run-record provenance surface + touching the freshly-hardened path — is
  accepted and managed via SD-6 (a ratified two-tier parity bar, never a
  silent relaxation), L-6 (the invariants contract), and phasing (Phase 1
  proves the pattern first; the riskiest PR lands last).
- **SD-2 — phasing. RATIFIED (recommendation): one PLAN, one vertical/concern
  per PR, oracle-first.** Phase 1: PR-1 procurement, PR-2 supply_chain — each
  PR carrying its own parity harness, landed **oracle-first** (harness passing
  against the CURRENT semantics in one commit, the flip in the next — the
  PLAN-0077 SD-5 two-commit discipline); procurement first (smaller diff,
  debugs the migration mechanics at minimum blast radius). Phase 2 extends the
  same discipline by CONCERN, cheapest/lowest-risk first: PR-3 severity
  (one vertical, one executor), PR-4 amount (the shared `_scored_rule` +
  4 steps), PR-5 the `derivation_hash` retirement + marker rewrite + T2
  closure. Suite green at every PR boundary.
- **SD-3 — OQ-3 registration scope. RATIFIED (recommendation): uniform —
  register `TransformStepExecutor()` in all 4 factories**, updating all five
  exact-key tests in lockstep, as a pure-additive prep commit (zero behavior
  change: no shipped procedure declares a transform until the flips). Grounds:
  the executor is fieldless, frozen, adapter-free — "every composing factory
  can register ONE shared instance uniformly" (`transform_step.py:16-18`,
  `:201-203`); the five tests are touched ONCE, never again.
- **SD-4 — parity-harness shape. RATIFIED (recommendation): fresh module(s)**
  (`tests/verticals/.../test_transform_migration_parity.py` per vertical, or
  one shared module under `tests/services/engine/procedures/` — executor's
  choice at R2) **copying the PLAN-0062 comparator discipline** —
  zero-tolerance, order-insensitive, key-complete, and an **independent
  hand-coded reference**: the CURRENT enriched/stamped rows frozen as
  hand-written expected fixtures (from the contract, not by calling the old
  code — so after the old code is slimmed the reference cannot silently drift,
  the `test_seed_migration_parity.py:6-13` property). NOT bolted onto
  `test_seed_migration_parity.py` (that file is the PLAN-0062 query-migration
  guard with its own frozen reference semantics). Phase-2 harnesses assert the
  SD-6 two-tier bar.
- **SD-5 — F-PIN marker disposition. RATIFIED: the (B) branch.** The marker
  `test_fpin_residual_procurement_unpinned_marker`
  (`test_derivation_pin.py:205-224`) is **REWRITTEN in the same PR that
  retires the provider** (its first assertion breaks by construction):
  the new marker asserts BOTH verticals' `derivation_hash` is None AND the
  migrated supply_chain procedure's pin carries the `_DOSE_LADDER` as declared
  step-transform content (the bands + `above: critical`, hand-written
  expectation — no import of the retired constants). PLAN-0076 Step T2 is
  closed in that same PR per T3 (`0076:304-314` — never delete/skip/weaken a
  marker without closing the tracking it guards). **F-PIN's new-run threat
  stays OPEN (L-4)** — the rewrite + T2 closure is the REMAINDER fold-in,
  never a closure of the threat.

- **SD-6 — the parity-bar semantics under (B). RATIFIED (Cray 2026-07-15):
  the two-tier bar (recommendation).**
  Because Phase 2 deliberately MOVES the severity/amount derivations out of
  the executors and into declared transforms, the run RECORD's provenance
  surface changes FORM (the executor's `severity_derivation` audit +
  `severity_derived` trace becomes the transform's `transform_provenance`;
  the scored_rule audit's amount home moves per SD-8) — a byte-equal parity
  of the whole run record is impossible BY DESIGN.
  *Recommendation:* re-scope L-2 for Phase 2 to **(i) output-ROW parity** —
  every governance-relevant entity field the gates read
  (`excursion_severity`, `criticality`, `amount`, and all Phase-1 intake
  fields) is byte-equal to the pre-migration seed/stamp output — **PLUS
  (ii) semantic run-record equivalence** — the verdicts, statuses, gate
  outcomes, and final run status are identical, and the provenance surface,
  though changed in form, remains complete (every derivation that was traced
  is still traced, by the transform). L-2 above is already written two-tier
  to this recommendation (Phase 1 = full byte parity incl. run record;
  Phase 2 = output-row byte parity + semantic run-record equivalence).
  *Alternative:* insist on byte-equal run records for Phase 2 — rejected:
  impossible once the derivation moves; it would forbid (B) entirely, which
  Cray has already ratified.
  *Why Cray:* this redefines the PLAN's binding bar (L-2) for the stamp
  phase — it is the price of (B) and must be ratified, not silently adopted.
- **SD-7 — `ColdChainAssessExecutor` disposition. RATIFIED (Cray 2026-07-15):
  SLIM to a fail-closed scalar-validation guard (recommendation) — do NOT full-retire.**
  *Recommendation:* **SLIM to a fail-closed scalar-validation guard** — the
  executor stops deriving and stamping (severity, criticality,
  `severity_derivation` audit, trace all come from the declared transform) but
  KEEPS validating the three excursion scalars strictly-positive + finite
  before delegating (`_positive_decimal`'s posture, `:119-145`). Grounds
  (verified at revision): the transform grammar **cannot express the
  positivity guard** — its `_to_decimal` accepts negative scalars
  (`transform_step.py:360-388`), and a negative ratio would band to the
  LOWEST severity: fail-DANGEROUS, the exact shape PLAN-0074 fixed. Slimming
  preserves the two-independent-closed-doors posture (guard + gate reader)
  without an ADR amendment. Today's data path produces only positive scalars
  (the seed's `magnitude_c <= 0` eligibility guard + authored positive
  defaults), so the guard is defense-in-depth — but silently dropping a
  hardened fail-closed door is not the drafter's call.
  *Alternatives:* **full retire** — accept the one-door posture (the
  `_severity` reader still fails closed on absent/unrecognized, but a
  wrongly-LOW severity from a hypothetical negative scalar would pass);
  smallest end-state, weakens defense-in-depth. **ADR-0031 amendment** adding
  a declarative positivity-guard op — the tripwire path; heavier, reopens an
  Accepted ADR for one guard; available later if a second vertical needs it.
  *Why Cray:* the fail-closed posture on the authority path is a governance
  property (L-6(iv)); how much of a hardened door may be removed is a
  risk-appetite call, not a drafter judgment.
- **SD-8 — the amount re-sequencing shape. RATIFIED (Cray 2026-07-15): (a) one
  derivation home (recommendation).** More than one shape is
  viable, and the blast radius is 4 scored_rule steps across 4 procedures in
  both shipped yamls (verified above).
  *Recommendation:* **(a) one derivation home.** `_scored_rule` stamps the
  winner's **`selected_unit_price`** (JSONB-safe string, mirroring the
  `selected_quote_id`/`selected_supplier_id` naming; `qty` already rides the
  entity — `_quantity` reads it today) and **stops stamping `amount`**;
  `ScoredRuleVerdict` drops its `amount` field (`scored_rule.py:230`) so the
  derivation exists ONCE — as data; a declared `derive_spend` transform
  (`derive: amount = mul(selected_unit_price, qty)` + `coerce: amount →
  string`) is inserted downstream of EVERY scored_rule step — procurement ×3
  (between each `source` and its `compliance`) and supply_chain ×1 (between
  `assess` and `gdp_gate`) — so every row that carried `amount` still carries
  it byte-equal (output-row parity) and the `doa_tier` reader `_spend` is
  untouched. The scored_rule audit surface changes form (unit_price + qty in
  place of the precomputed amount) — covered by SD-6(ii).
  *Alternatives:* **(b) duplicated derivation** — the verdict keeps computing
  `amount` for its audit, the entity stamp switches to `selected_unit_price`,
  the transform derives the gate-read `amount`: byte-preserves the scored_rule
  audit but leaves the derivation living in BOTH code and data — a dishonest
  rendering of (B) (the code-side derivation would still exist un-declared).
  **(c) hero-procedure-only re-sequencing** via a step-conditional stamp —
  requires the procedure-aware executor-factory seam that does not exist
  (PLAN-0076 T1, open) — out of scope.
  *Why Cray:* the shape decides how many shipped procedures' pins change
  (all four vs fewer) and whether the (B) principle — the derivation has ONE
  home, as declared data — is rendered honestly or half-way.

## Steps

Build order = cheapest/lowest-risk gate first; the parity harness lands BEFORE
each flip (oracle-first); suite green at every PR boundary. Phase 1 executes on
the ratified SD-2/SD-3/SD-4; **Phase 2 executes on the ratified SD-6/SD-7/SD-8**
(and, for Step 4, the ratified OQ-5 = (a) materialize).

### Phase 1 — intake migration (prove the pattern at low risk)

#### Step 1 — Registration prep (SD-3 ratified; AC-1): uniform `TransformStepExecutor` + lockstep tests
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

#### Step 2 — PR-1 procurement intake (SD-2 ratified; AC-2, AC-4, AC-5): oracle first, then the flip
1. **Oracle commit:** the SD-4 parity harness for procurement — hand-coded
   frozen reference of the CURRENT enriched intake row (criticality copy, unit
   default `"criticality"`, compliance map, plus every seed-side field that
   STAYS: event_type, qty, candidate_quotes, requisition metadata), asserted
   byte-equal against the CURRENT production factory's run; downstream verdicts
   (judge band, scored_rule selection + amount, rule_gate, doa_tier) pinned —
   Phase-1 tier: **full byte parity incl. the run record** (L-2).
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

#### Step 3 — PR-2 supply_chain intake (SD-2 ratified; AC-3, AC-4, AC-5): oracle first, then the flip
1. **Oracle commit:** the parity harness for supply_chain — frozen reference of
   the CURRENT enriched disposition row (`:193-244`: magnitude `"4"`-form
   string, duration/budget defaults, GDP compliance map, coercion forms, plus
   the STAYS fields: identity, reading_c/temp_ceiling strings, qty, currency,
   candidate_quotes, quarantine_status), asserted against the current factory
   run; downstream verdicts (assess selection, severity stamp, gdp_gate,
   severity_tier approve) pinned — Phase-1 tier: full byte parity.
2. **Flip commit:** add the declared `enrich` transform step to
   `verticals/supply_chain/procedures.yaml` between `intake` (`:193`) and
   `assess` (`:206`) — ops per fixture B (`test_transform_fixtures_e2e.py:185-206`):
   `excursion_magnitude_c` sub-derive from `reading_c`/`temp_ceiling`,
   duration/budget defaults, compliance map, Decimal→str coercion(s). Slim
   `_intake_seed` (`procedures_factory.py:145-244`): stop emitting the derived
   fields; KEEP the adapter reads, `_latest_breach_reading`, and the
   `magnitude_c <= 0` guard (`:190-191` — the seed may keep the subtraction for
   the guard while no longer emitting the field; exact guard form is OQ-1).
   Verify the registration-time JSONB capture (`:279`) still round-trips the
   slimmed row. Re-run the harness — byte-equal or no landing (L-2).
3. Docstring honesty pass (the `_DispositionSeed`/`_intake_seed` AUTHORED-half
   labels move to the yaml transform; the eligibility-predicate follow-on note
   `:158-162` stays); PR per §7.

### Phase 2 — stamp re-sequencing (SD-1 (B); SD-6/SD-7/SD-8 + OQ-5 ratified)

#### Step 4 — PR-3 severity re-sequencing (SD-6, SD-7; AC-7, AC-9, AC-12): oracle first, then the flip
1. **Oracle commit:** the Phase-2 parity harness for supply_chain per SD-6 —
   (i) frozen output-row reference for the gate-read + amplifier fields:
   `excursion_severity` (exact enum-string value) and `criticality` (the exact
   `str(min(Decimal(1), ratio))` string form), alongside the Phase-1 fields;
   (ii) semantic run-record pins: assess scored-selection verdict, gdp_gate
   outcome, severity_tier resolution (tier id, required role, approver), final
   run status; (iii) provenance-completeness assertion — every derivation the
   executor traced is still traced (the transform's `transform_provenance`
   entries + the materialized derivation fields per OQ-5). Proven against the
   CURRENT (executor-stamped) world first.
2. **Flip commit:** declare the severity derivation in
   `verticals/supply_chain/procedures.yaml` (extend the Phase-1 `enrich`
   step's ops or add a `derive_severity` transform step between it and
   `assess` — OQ-6): `map_value` target `excursion_severity`, source =
   `div(mul(excursion_magnitude_c, excursion_duration_h),
   stability_budget_ch)` (a nested Expr — no intermediate fields required,
   `transform_step.py:296-299`), bands = the `_DOSE_LADDER` values
   (0.25→negligible, 0.50→minor, 1.00→major) + `above: critical`; `derive`
   target `criticality` = `min(const 1, <the same ratio expr>)` + `coerce`
   to string; optionally materialize `dose_ch`/`ratio` per OQ-5. Re-shape
   `ColdChainAssessExecutor` per the ratified SD-7 (recommended: slim to the
   fail-closed scalar-validation guard; stop stamping severity /
   criticality / audit / trace — the transform now owns them upstream of
   `assess`, so `assess`'s scored_rule sees the same `criticality` amplifier
   values). **Interim redundancy, stated honestly:** the `_DOSE_LADDER`
   constants + `derivation_hash` provider stay in code until PR-5 (the pin
   carries BOTH the declared transform content and the code-hash in the
   interim; the F-PIN marker still passes — its rewrite belongs to the
   retiring PR per SD-5/T3). Re-run the harness — the SD-6 two-tier bar or no
   landing.
3. **L-6 check:** `_severity` (`governance_step.py:81`) byte-untouched
   (diff-verified); PLAN-0074/0075 suites green; the fail-closed scalar
   posture demonstrated per SD-7 (AC-12). PR per §7.

#### Step 5 — PR-4 amount re-sequencing (SD-6, SD-8; AC-8, AC-9): oracle first, then the flip
1. **Oracle commit:** the Phase-2 parity harness for the amount path,
   covering ALL FOUR scored_rule steps (the three procurement procedures +
   supply_chain `assess`): frozen `amount` string forms per procedure on the
   same inputs; semantic run-record pins incl. the doa_tier resolution on
   procurement's `approve` (`_spend` reads the same amount+currency) and the
   unchanged non-amount stamps (`selected_quote_id`, `selected_supplier_id`,
   `source_path`, `override_required`, `currency`).
2. **Flip commit (per the ratified SD-8; recommended shape (a)):**
   `_scored_rule` stamps `selected_unit_price`, stops stamping `amount`;
   `ScoredRuleVerdict` drops `amount` (`scored_rule.py:230`) — the derivation's
   ONE home becomes declared data; insert the `derive_spend` transform
   (`amount = mul(selected_unit_price, qty)` + coerce-to-string) after each of
   the four scored_rule steps in both yamls; thread + re-point per the shipped
   convention. Re-run the harness — output-row `amount` byte-equal everywhere
   + semantic equivalence, or no landing.
3. **L-6 check:** `_spend` (`governance_step.py:47`) byte-untouched
   (diff-verified); the PLAN-0074/0075 doa_tier/SoD suites green. PR per §7.

#### Step 6 — PR-5 `derivation_hash` retirement + F-PIN marker rewrite + PLAN-0076 T2 closure (SD-5 ratified; AC-10, AC-11)
1. Retire the code-hash end-to-end (grep-clean, AC-10): the provider
   `cold_chain_assess.py:82-106` (+ the now-dead `derive_excursion_severity` /
   `SeverityDerivation` / `_DOSE_LADDER` / `_TOP_SEVERITY` code, to whatever
   extent the ratified SD-7 shape leaves them unused); the registration
   `procedures_factory.py:311`; the registry hook (`registry.py:39` type,
   `:136-163` register/pull, the `_VerticalEntry` field); the snapshot fold-in
   + parameters (`governance_pin.py:122-125` and the `derivation_hash`
   kwargs); the pass-through threading in `orchestrator.py`, `action_step.py`,
   `event_bridge.py`, `persistence.py`, `scheduler.py`,
   `services/api/routers/runs.py`. Assert supply_chain's snapshot losing the
   `derivation_hash` key is an INTENDED pin change (the transform content
   already covers the ladder — `governance_pin.py:96-98`).
2. **Rewrite the F-PIN marker** per the ratified SD-5:
   `test_derivation_pin.py:205-224` → assert BOTH verticals'
   `derivation_hash` is None AND the migrated supply_chain procedure's pin
   carries the `_DOSE_LADDER` as declared step-transform content (hand-written
   band expectations — no import of retired constants). Prune/repoint the
   sibling derivation-pin tests that exercised the retired hook.
3. **Close PLAN-0076 Step T2** (`0076:293-302`) in this same PR per T3
   (`0076:304-314`): record the fold-in closed (the ladder promoted to
   declared data; the code-hash retired; the marker rewritten). **PLAN-0076
   itself does NOT archive** — T1 (gate-plugin seam) stays open and its AC-6
   guard-test stays. **No artifact records F-PIN closed** (L-4). PR per §7.

#### Step 7 — Closeout (AC-5, AC-6)
- Pin tests: the migrated/re-sequenced procedures' snapshots carry the
  canonical `transform` key(s) (`governance_pin.py:96-98`) and a mid-flight
  transform edit fails closed at resume (the existing pin-test pattern); every
  NO-transform procedure (energy, aquaculture, and the untouched procedures
  inside the two migrated yamls) pins **byte-identically** to before (AC-6).
- STATUS update in the merged PRs (or immediate `docs(status):` reconcile);
  `git mv docs/plans/0078-*.md docs/plans/done/` on completion. If ADR-0031's
  D3 row-1 warrants a "migrated" annotation (D4.4), that is an Accepted-body
  edit → drafter-authored, ratified in one pass (OQ-3 below) — never edited
  in-PLAN.

## Acceptance Criteria

Phase 1 executes on the ratified SDs; Phase-2 ACs execute on the ratified
SD-6..SD-8 (AC-7 additionally on the ratified OQ-5 = (a) materialize).

- [x] **AC-1 (registration).** *(Phase 1 — `d8707ca`.)* `TransformStepExecutor` registered in all 4
  factories (SD-3 ratified); the five exact-key tests updated in lockstep; the
  subset assertion untouched; full suite green with zero behavior change
  before any flip.
- [x] **AC-2 (procurement intake parity flip).** *(Phase 1 — PR-1 #762 `173d869`;
  `tests/verticals/procurement/test_transform_migration_parity.py:139`.)* The declared `enrich`
  transform (criticality copy + unit default + compliance map) replaces the
  seed's emission of those fields; the SD-4 zero-tolerance harness proves the
  enriched row set AND the downstream run record (judge/source/compliance/
  approve verdicts, run status) **byte-equal** (Phase-1 tier) to the frozen
  pre-flip reference on the same inputs. The `candidate_quotes` nest + reads +
  metadata stay seed-side, honestly labelled (L-3).
- [x] **AC-3 (supply_chain intake parity flip).** *(Phase 1 — PR-2 #763 `45d6b82`;
  `tests/verticals/supply_chain/test_transform_migration_parity.py:113`.)* The declared `enrich`
  transform (magnitude derive + defaults + compliance map + coercions)
  replaces the seed's emission of those fields; the harness proves row-set +
  run-record **byte-equality** (Phase-1 tier) including the exact string forms
  (`"4"`-style magnitude). The reads, breach-selection, eligibility guard, and
  lane list stay seed-side.
- [x] **AC-4 (fail-closed intact).** *(Phase 1 — the per-vertical bar is MET:
  `test_intake_transform_fails_closed_on_missing_source_field` (procurement,
  `:188`) + `test_enrich_transform_fails_closed_on_missing_source_field`
  (supply_chain, `:173`). Phase 2's scalar-posture leg is AC-12's, per SD-7.)*
  A missing/non-coercible source field on a
  migrated transform refuses the whole step typed (the shipped executor's
  fail-closed posture, PLAN-0077 SD-7) — demonstrated per vertical with a
  mutated fixture row.
- [ ] **AC-5 (pin coverage).** *(Phase-1 leg GREEN — both migrated procedures'
  snapshots assert the `enrich` transform canonically. Stays UNTICKED: the
  "re-sequenced" leg is Phase 2.)* Each migrated/re-sequenced procedure's
  governance snapshot carries its transform(s) canonically
  (`governance_pin.py:96-98`); a mid-flight transform edit fails closed at
  resume. Every config-hash change (the two intake flips; the severity PR;
  the amount PR's four procedures; the `derivation_hash` key removal) is
  asserted INTENDED, never silently absorbed.
- [ ] **AC-6 (byte-identical non-participants).** *(Phase-1 leg GREEN — the
  reorder siblings + the sweep assert no `transform` key. Stays UNTICKED: Phase
  2 adds transforms, so the non-participant set shrinks and must be re-swept.)*
  Every procedure declaring no
  transform — energy, aquaculture, and the untouched procedures in both
  migrated yamls — produces a governance snapshot and config hash
  byte-identical to pre-migration (the only-when-supplied property,
  `governance_pin.py:59-63`, `:122-125`).
- [ ] **AC-7 (severity re-sequencing parity — SD-6 tier).** The declared
  severity transform replaces the executor's stamping; the Phase-2 harness
  proves (i) output-row byte parity on `excursion_severity` + `criticality`
  (exact string forms) and every Phase-1 field, and (ii) semantic run-record
  equivalence — identical assess/gdp_gate/severity_tier outcomes + final run
  status — and (iii) provenance completeness (every derivation traced, in the
  transform's form).
- [ ] **AC-8 (amount re-sequencing parity — SD-6 tier).** Per the ratified
  SD-8 shape: `amount` is derived by declared transforms downstream of ALL
  FOUR scored_rule steps; the harness proves output-row byte parity on
  `amount` (exact string form) in every affected procedure + semantic
  run-record equivalence incl. the doa_tier resolution; the non-amount
  scored_rule stamps are unchanged.
- [ ] **AC-9 (authority invariants — L-6).** `_spend`
  (`governance_step.py:47`) and `_severity` (`:81`) are **byte-untouched**
  (diff-verified at R2 on every Phase-2 PR); exact-Decimal end-to-end; bypass
  stays unrepresentable; the PLAN-0074/0075 suites green at every PR boundary.
- [ ] **AC-10 (`derivation_hash` fully retired).** After PR-5: zero residual
  `derivation_hash` references in code + tests (grep-clean across the 8
  pass-through files, the provider, the registration, and
  `test_derivation_pin.py`; docs/ archaeology exempt); supply_chain's snapshot
  no longer carries the key (an asserted, intended pin change).
- [ ] **AC-11 (marker rewritten + T2 closed — F-PIN honesty, L-4 + SD-5).**
  The F-PIN marker is rewritten in the retiring PR (both verticals None + the
  supply_chain pin carries the ladder as declared step-transform content);
  PLAN-0076 Step T2 closed in that same PR per T3; PLAN-0076 NOT archived
  (T1 open, AC-6 guard-test stays). **No artifact of this PLAN records F-PIN
  closed.**
- [ ] **AC-12 (fail-closed scalar posture preserved — SD-7).** Per the
  ratified SD-7 shape: a non-positive / non-finite excursion scalar still
  refuses the run BEFORE the severity gate (demonstrated with a mutated
  fixture row); the door is re-homed or consciously removed by Cray's pick —
  never silently dropped.

## Out of Scope

- ❌ **Closing F-PIN's new-run re-routing threat** — architectural, stays open
  (L-4; `cold_chain_assess.py:98-100`). Phase 2 closes only the T2 remainder
  fold-in.
- ❌ **Archiving PLAN-0076** — its T1 (gate-plugin seam) deferral stays open;
  T3 blocks the archive until both deferrals close (`0076:310-314`).
- ❌ **The deferred transform ops** — `unit_convert`, `extract`, `normalize`,
  `derive(concat)`, discrete `map_value` (zero instances; PLAN-0077 L-7) — and
  any NEW op (incl. a declarative positivity guard: SD-7's alternative routes
  through an ADR-0031 amendment, never an in-PLAN invention).
- ❌ **The `candidate_quotes` nest / any cardinality-changing reshape**
  (PLAN-0077 SD-8 wall; procurement partial, L-3) — if execution finds the
  nest indispensable, that is the tripwire path (surface for an ADR-0031
  amendment).
- ❌ **Eligibility predicates** (the `magnitude_c <= 0` guard,
  `procedures_factory.py:158-162` note) — a declarative filter is a different
  construct from a derivation; it waits for its own trigger.
- ❌ **A step-conditional / procedure-aware stamp seam** (SD-8 alternative (c))
  — that is PLAN-0076 T1's gate-plugin-seam PLAN, not this one.
- ❌ **Any new ADR, ontology change, regen, or Alembic migration** — yaml +
  seed + engine-stamp + factory + tests only (and per project memory: only
  energy has a committed ORM table; nothing here touches it).
- ❌ **Any LLM / live / host-state run** (L-5) — this PLAN never touches MS-S1.
- ❌ **Editing ADR-0031 in this PLAN** — a D4.4 row annotation, if warranted, is
  a drafter-authored Accepted-body edit ratified in one pass (OQ-3).

## Verification

Offline under CI `gate` — the ENTIRE bar (L-5); no live run, no `docs/logs/`
evidence note. The AC matrix above, concretely, at the L-2 two-tier bar:

- **Phase 1:** per-vertical zero-tolerance output-set parity — the
  declared-transform run == the frozen seed reference, **rows AND run record**,
  byte-equal.
- **Phase 2:** per-PR output-ROW byte parity on every gate-read field
  (`excursion_severity`, `criticality`, `amount`, + the Phase-1 fields) +
  semantic run-record equivalence (verdicts / statuses / gate outcomes / final
  status identical; provenance complete in its new form) — per the ratified
  SD-6.
- The exact-key factory tests green post-registration; the PLAN-0074/0075
  authority suites green at EVERY PR boundary with the gate readers
  diff-verified byte-untouched (AC-9); the fail-closed scalar posture
  demonstrated per SD-7 (AC-12); migrated procedures pin their transforms +
  fail closed on mid-flight edit; every no-transform procedure pins
  byte-identically; post-PR-5 `derivation_hash` grep-clean (AC-10) and the
  rewritten marker green (AC-11).

Pass/fail reads are fixed in each harness BEFORE its flip commit (oracle-first
— Lesson #0026 discipline).

## Open Questions

- **OQ-1 (guard form).** After the magnitude field moves to the declared
  transform, does the supply_chain seed keep computing `reading_c − ceiling`
  solely for the `<= 0` eligibility guard (`:190-191`), or switch the guard to
  the equivalent direct compare `reading_c <= ceiling`? Recommendation: keep
  the subtraction (smallest diff, same semantics); executor decides at R2 —
  the parity harness is indifferent (the guard's emit path is unchanged either
  way). Interplay with SD-7: this seed-side guard is the reason today's data
  path never produces a non-positive magnitude; it stays regardless.
- **OQ-2 (prep landing).** Step 1's uniform registration: first commits of PR-1,
  or its own tiny prep PR? Recommendation: fold into PR-1 (pure-additive,
  reviewed against the flip that motivates it); executor's call.
- **OQ-3 (ADR-0031 D4.4 row annotation).** On completion, does D3 row-1's
  status text warrant a "seeds + marquee stamps migrated (partial per SD-8
  wall)" annotation? If yes: Accepted-body edit → route to plan-drafter,
  ratified in one pass (G1; project memory: never flip-then-edit). Not
  blocking this PLAN's archive.
- **OQ-4 (in-flight runs at deploy).** Up to five shipped procedures' config
  hashes change across the PRs; any persisted mid-flight run fails closed at
  resume (intended pin behavior). Demo runs are ephemeral so no migration shim
  is planned — confirm no durable environment holds in-flight runs of the
  affected procedures at each merge (a Cray confirm at PR, not a code change).
- **OQ-5 (materialize `dose_ch`/`ratio`?).** The severity transform can band a
  nested expression WITHOUT materializing dose/ratio as row fields — but the
  retired `severity_derivation` audit carried those values (the "show WHY a
  batch is CRITICAL without re-deriving" contract,
  `cold_chain_assess.py:149-171`). Recommendation: **materialize them** as
  declared `derive` targets (`dose_ch`, `ratio`) + string coercions — additive
  row fields, included in the frozen Phase-2 reference — keeping SD-6(ii)'s
  "provenance remains complete" clause true at the VALUE level, not just the
  op level. Alternative: nested-expr only (leaner rows; the WHY values vanish
  from the record). **RATIFIED by Cray 2026-07-16 (AskUserQuestion): (a)
  materialize** — SD-6(ii)'s "provenance remains complete" binds at the VALUE
  level. Grounds recorded at ratification (verified at revision):
  `transform_provenance` carries the op name, target and row count ONLY, never
  values (`transform_step.py:244-253`; `_op_summary` is "a display concern
  only", `:184`), and `_eval_expr` returns just the tree's final value
  (`:332`, written at `:273`) — so under the alternative `dose_ch`/`ratio` are
  computed and DISCARDED, and answering "why CRITICAL?" would require
  re-running the pinned spec against the input row. That re-derivation depends
  on the very guarantee F-PIN leaves open (L-4 / AC-11), and `dose_ch` +
  `ratio` are traced TODAY by `to_audit()` (`cold_chain_assess.py:161-171`), so
  dropping them would regress a shipped audit surface — not defer a new one.
  NOTE: this makes the severity transform THREE ops (`dose_ch`, `ratio`,
  `excursion_severity`), which is an input to OQ-6 below (executor's call).
- **OQ-6 (one transform step or two, supply_chain).** Extend the Phase-1
  `enrich` step's op list with the severity ops (ops apply sequentially over
  the working row — `transform_step.py:234-238` — so later ops see the
  Phase-1 derivations), or add a separate `derive_severity` step?
  Recommendation: extend `enrich` (fewer steps, one threading seam; either way
  the pin changes once per PR); alternative: a separate step gives the
  severity its own provenance boundary. Executor's call at R2 — the parity
  harness is indifferent.

## Size estimate

**Materially larger than the (A) draft — five PRs across two phases, and
Phase 2 deliberately touches the freshly-PLAN-0075-hardened path** (the honest
price of the ratified (B); managed by L-6 + SD-6 + landing the riskiest PR
last):

- **PR-1 (procurement intake + prep):** ~8-10 files — 4 factory files + 5 test
  files (Step 1), `procedures.yaml`, `hero_demo/run.py` (seed slim), 1 new
  parity module, pin-test additions. Small-medium.
- **PR-2 (supply_chain intake):** ~4-6 files — `procedures.yaml`,
  `procedures_factory.py`, 1 new parity module, pin-test additions, docstring
  honesty pass. Small-medium.
- **PR-3 (severity re-sequencing):** ~5-8 files — supply_chain
  `procedures.yaml`, `cold_chain_assess.py` (slim/retire per SD-7), the
  Phase-2 parity module, pin-test + PLAN-0074/0075 suite touches where they
  asserted the executor's stamping form. Medium; hardened-path.
- **PR-4 (amount re-sequencing):** ~8-12 files — `governance_step.py`
  (`_scored_rule` stamp), `scored_rule.py` (verdict), BOTH `procedures.yaml`s
  (4 transform insertions), parity module(s), doa_tier/SoD suite touches.
  Medium-large; the widest blast radius (4 procedures, both verticals) —
  lands only after PR-3 proves the re-sequencing pattern.
- **PR-5 (`derivation_hash` retirement + marker + T2):** ~11-13 files — the 8
  pass-through files, the provider + registration, `test_derivation_pin.py`
  rewrite, the PLAN-0076 T2 closure edit. Wide but mechanical (deletion +
  one rewritten marker), grep-clean verifiable.
