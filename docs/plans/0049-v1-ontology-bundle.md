# PLAN-0049: v1 Ontology Bundle — energy-v1 + supply-chain-v1 content, meta-schema enrichment (R2), semantic-context-pack emitter (R1), alembic autogenerate

**Status:** Draft
**Owner:** Claude Code (executes) + Cray (ratifies SDs)
**Created:** 2026-07-04
**Related ADRs:** ADR-008 (YAML ontology grammar — authorizing), ADR-0021 (measured_kind / quantity_bindings grammar-amendment precedent), ADR-006 (vertical plugin architecture), PLAN-0031 (ORM emitter — B1-DP-1 deferral)

> Cray-picked 2026-07-04 as Wave-2 item (b) per the session-95 CLOSE handoff.
> **This PLAN is Draft.** Several load-bearing forks are surfaced as SDs (§ Surfaced Decisions) and MUST be ratified before the affected step executes. In particular **SD-1 (R2 ADR dependency) gates workstream C**, and **SD-3 (supply-chain runtime ORM) may block workstream B**.

## Goal

Deliver the "v1 ontology bundle": (A) energy-v1 and (B) supply-chain-v1 ontology **content** riding existing ADR-0021 grammar (enum + quantity_bindings, no meta-schema change); (C/R2) a one-time **meta-schema enrichment** adding the convergent semantic fields (`synonyms` th+en, `sample_values`, `verified_queries`, metric `grain`/join-path) — a genuine ADR-008 grammar amendment; (D/R1) a new **semantic-context-pack emitter** (7th emitter) compiling each vertical's YAML into a ~4KB markdown pack for NL-query + anomaly reasoning; and (E) wiring **alembic autogenerate** from the now-generated ORM. The bundle adds ENTITIES / KINDS / ENUMS and semantic metadata only — no band-expressiveness, no mapping-layer work (see Out of Scope). Every step lands with its own offline gate and handles the ontology-change ripple (regen → new hand-authored migration past head 0008 → parity re-pass) coherently.

## Acceptance Criteria

- [ ] **AC-1 (energy-v1 content).** `energy_v0.yaml` (path per SD-2): `Asset.asset_type` enum += `{feeder, cap_bank, gas_engine}`; `OperationalEvent.measured_kind` enum += `{current, voltage}`; `quantity_bindings` += `{current→A, voltage→kV}` (ADR-0021 one-unit-per-kind). Rating-property fork resolved per SD-6. `vero-lite validate energy` passes L1+L2.
- [ ] **AC-2 (energy regen ripple).** `vero-lite generate energy` regenerates `services/db/models.py` + `schema.sql`; a NEW hand-authored migration (`0009_*`) advances head past `0008_governance_pin.py`; `tests/services/db/test_schema_parity.py` re-passes green.
- [ ] **AC-3 (supply-chain-v1 content).** `supply_chain_v0.yaml` (path per SD-2): new `Equipment`/`Device` object type + `shipment_uses_equipment` link + `adjust_setpoint` action class (G1); `OperationalEvent` gains `measured_kind` enum `{temperature, battery}` + `quantity_bindings` `{temperature→celsius, battery→percent}` (G2 — supply_chain_v0 has NEITHER today); `Shipment.status` += `returned`, action enum += `{release, return, adjust_setpoint}` (G11). `vero-lite validate supply_chain` passes.
- [ ] **AC-4 (supply-chain regen + ORM/parity).** `vero-lite generate supply_chain` runs clean; runtime-ORM destination resolved per SD-3; parity coverage resolved per SD-4.
- [ ] **AC-5 (R2 meta-schema).** IFF SD-1 authorizes it in this PLAN: the meta-schema (ADR-008 grammar + `services/engine/ontology_meta.py` Pydantic models + L1/L2 validation) admits `synonyms`, `sample_values`, `verified_queries`, metric `grain`/join-path; the v1 verticals are backfilled; degrades gracefully when a field is absent. Machine-drafted, human-canonicalized (governed ≠ generated — every promotion PR-gated).
- [ ] **AC-6 (R1 emitter).** A 7th emitter compiles each vertical's YAML → a ~4KB markdown context pack (measures + conventions + disambiguation rules + th/en aliases); wired into `generate_all` (one added line, per fact-pack shape); consumes R2 fields when present, degrades when absent; holds a fixed per-vertical token budget (32K tripwire) with an explicit assertion/test.
- [ ] **AC-7 (alembic autogenerate).** `alembic revision --autogenerate` is wired from the generated ORM per SD-5 (new CLI command vs documented workflow); the v1 regen migration is the hand-verified test case (autogenerate output diffed against the hand-authored `0009_*`, discrepancies reconciled).
- [ ] **AC-8 (suite green at every boundary).** Each step keeps the offline suite green (baseline ~2131 passed / 5 skipped — confirm at execution). CI (PLAN-0047 Step 7): full suite + postgres + `alembic upgrade head` per PR.
- [ ] **AC-9 (governance intact).** No live-model run (any live run = host-state = Cray gate, CLAUDE.md §8). All LLM/machine-drafted semantic content (R1/R2) is human-canonicalized before commit.

## Out of Scope

- ❌ ALL band-expressiveness work (duration-qualified, two-sided/corridor, per-contract SLA-timer, context-scoped bands — run-1 §2.4, run-2 §2.3). Routes to the generalized-procedure-schema thread (backlog #3). This bundle adds ENTITIES / KINDS / ENUMS + semantic metadata only.
- ❌ Mapping-layer items: row→events explosion (WI-G2b [MAP]), calibration/bias registry (§2.4/G6), era-surrogate PK rules (§2.2), multi-latency fusion / retro-reaudit (§2.5/G5). All [MAP] = the mapping spec.
- ❌ 4-zone / multi-threshold band arithmetic (run-1 top-oil 78/87/92; the "report" zone) — band-expressiveness, backlog #3.
- ❌ R3 (schema-guided LLM bootstrap) + R4 (usage-mined synonym loop) — later, post-partner.
- ❌ PDPA / GTM / intake-form items (F10 instance-scoped authority, F11 degraded-mode UI, RoPA).

## Steps

> Sequencing rationale: A (energy content + ripple) first — it exercises the full regen→migration→parity loop end-to-end on the guarded vertical, de-risking the pattern before B. B (supply-chain) second (mirrors A, one regen) but may block on SD-3/SD-4. C (R2) is **gated by SD-1** — if carved out, it becomes a prerequisite ADR + follow-up PLAN and A/B/D/E ship unblocked. D (R1) after C (consumes R2 fields, degrades without them). E (alembic) last — the v1 regen migrations are its natural test case.

### Step 1: energy-v1 ontology content + regen ripple (workstream A)
Edit the energy ontology (path per SD-2): add the three `asset_type` enum members, the two `measured_kind` members, the two `quantity_bindings`, and resolve SD-6 (rating property). **Ripple:** `vero-lite generate energy` → regenerate `models.py` + `schema.sql`; hand-author migration `0009_*` past head `0008`; re-run parity.
**Offline gate:** `vero-lite validate energy` (L1+L2) green; `test_schema_parity.py` green; full offline suite green; `alembic upgrade head` clean in CI.

### Step 2: supply-chain-v1 ontology content (workstream B)
Edit the supply-chain ontology (path per SD-2): add `Equipment`/`Device` type + `shipment_uses_equipment` link + `adjust_setpoint` action (G1); add `measured_kind` + `quantity_bindings` to `OperationalEvent` (G2); `Shipment.status` += `returned` and action enum += `{release, return, adjust_setpoint}` (G11). **Blocked on SD-3** (runtime-ORM destination) and **SD-4** (parity scope) before regen commits.
**Offline gate:** `vero-lite validate supply_chain` green; regen clean; parity per SD-4; suite green.

### Step 3: R2 meta-schema enrichment (workstream C) — GATED BY SD-1
IFF SD-1 authorizes a bundled ADR-008 amendment here: extend the grammar + `ontology_meta.py` models (`ObjectTypeMeta`/`PropertyMeta` add `synonyms`/`sample_values`/`verified_queries`; metric `grain`/join-path) + L1/L2 checks; backfill v1 verticals (human-canonicalized). Else: this step exits to a prerequisite ADR + its own follow-up PLAN, and Steps 1/2/4/5 proceed unblocked.
**Offline gate:** meta-schema round-trips; `load_ontology_meta` parses new fields + tolerates their absence; validator tests; suite green.

### Step 4: R1 semantic-context-pack emitter (workstream D)
Add a 7th emitter (`(doc, path)->Path` shape) compiling YAML → ~4KB markdown pack; wire into `generate_all` (one added line after the ORM call). Consume R2 fields when present; degrade gracefully when absent; assert per-vertical token budget (32K tripwire).
**Offline gate:** emitter unit tests (both verticals); token-budget assertion; `generate_all` returns the new key; suite green.

### Step 5: alembic autogenerate wiring (workstream E)
Wire `alembic revision --autogenerate` from the generated ORM per SD-5 (new `vero-lite` CLI command vs documented workflow). `alembic/env.py:27` already sets `target_metadata`; add `compare_type` / `include_object` as needed. Test case = the v1 regen: diff autogenerate output against the hand-authored `0009_*`, reconcile.
**Offline gate:** autogenerate produces a migration matching (or reconciled to) the hand-authored one; `alembic upgrade head` clean; suite green.

## Surfaced Decisions

> These have multiple defensible answers and are NOT silently decided. Code recommends; Cray adjudicates.

- **SD-1 (R2 ADR dependency + sequencing) — TOP DECISION.** Does R2's meta-schema change ride this PLAN via a **bundled ADR-008 amendment**, or is it **carved to a prerequisite ADR + its own follow-up PLAN** so A/B/D/E ship now unblocked? *Code recommendation: CARVE OUT — R2's new fields (`synonyms`/`sample_values`/`verified_queries`/`grain`) are grammar amendments to ADR-008 D2/D3 exactly as `quantity_bindings` was (ADR-0021 `:148-164` did it via a dedicated ADR); baking a grammar amendment into a build PLAN would violate the ADR-first convention (CLAUDE.md §6). Recommend a prerequisite ADR authorizing the fields, then Step 3 becomes a thin follow-up.* Alternatives: bundle a lightweight ADR-008-amendment section into this PLAN's front-matter (faster, but mixes decision + build). **Cray call because:** it's an ADR-vs-PLAN boundary + grammar-authority question, not a Code judgment call.
- **SD-2 (v1 file strategy).** In-place edit of `{vertical}_v0.yaml` + bump `version: 0→1`, or new `{vertical}_v1.yaml` + change the hardcoded loader? *Code recommendation: EDIT `_v0.yaml` IN PLACE + bump version — the loader hardcodes `f"{vertical}_v0.yaml"` (`ontology_meta.py:77-79`) and the CLI mirrors it; a `_v1.yaml` filename forces a loader/CLI change with no content benefit ("v1" is the content generation, not the filename).* Alternatives: new file + loader indirection (cleaner if we ever need side-by-side v0/v1, but no such need surfaced). **Cray call because:** it sets the versioning convention for all future vertical revisions.
- **SD-3 (supply-chain runtime-ORM destination — the deferred B1-DP-1).** Does supply-chain-v1 need a **committed** runtime ORM at all in v1, and if so where (central per-vertical module vs a committed per-vertical generated file)? *Code recommendation: DECIDE PER RUNTIME NEED — if supply-chain-v1 has no runtime DB path in v1, leave it on the gitignored `orm.py` fallback (`code_generator.py:538`) and defer B1-DP-1; if it needs a runtime ORM, resolve B1-DP-1 as a committed `services/db/models_supply_chain.py` (mirrors energy).* Alternatives: force the central-module layout now (premature — Rule of Three not met). **Cray call because:** B1-DP-1 was explicitly deferred as a Rule-of-Three layout decision (PLAN-0031).
- **SD-4 (parity-test scope).** Extend `test_schema_parity.py` to supply_chain now, or document the gap? *Code recommendation: TIE TO SD-3 — if supply-chain gets a committed ORM (SD-3), extend parity to guard it now (unguarded generated DDL is a silent-drift hazard); if it stays on the gitignored fallback, document the gap in the PLAN + a test skip-reason.* Alternatives: always-extend (wasted if no committed ORM); always-defer (drift risk). **Cray call because:** it trades guard coverage vs scope, contingent on SD-3.
- **SD-5 (alembic autogenerate delivery).** A new `vero-lite migrate/revision` CLI command, or a documented `alembic revision --autogenerate` workflow + the v1 migration hand-verified against it? *Code recommendation: DOCUMENTED WORKFLOW + HAND-VERIFY for v1 — a CLI wrapper adds surface area before we know the ergonomics; PLAN-0031 SD-D scoped migration-generation OUT (`done/0031:105-111`), so this is greenfield. Ship the documented workflow, hand-verify against `0009_*`, promote to a CLI command later if friction warrants.* Alternatives: build the CLI command now (nicer ergonomics, more code + tests). **Cray call because:** it's an automation-surface scope decision reopening a prior OUT-of-scope boundary.
- **SD-6 (energy rating-property fork — F9).** `capacity_kw` misfits current-rated assets (feeders rated in A, 400 A). Add a distinct current-rating property, generalize to a `{rated_value, rated_unit}` pair, or keep `capacity_kw` + document the misfit? *Code recommendation: ADD A DISTINCT current-rating property (e.g. `rated_current_a`) for v1 — minimal, ships now, no grammar change; a generalized rated-value composite is a later Rule-of-Three call.* Alternatives: generalized composite (over-engineered for 2 verticals); keep-and-document (leaves a known modeling wart). **Cray call because:** it's a domain-modeling choice affecting the energy schema shape.
- **SD-7 (raw-counts quantity-kind fork — WI-3b, "Cray input wanted").** Batch-B raw-counts rows can't bind (counts ≠ a temperature unit; calibration curve lost). Add an own `unit: count` no-conversion quantity kind, or quarantine the counts rows? *Code recommendation: DEFER OUT of this PLAN — the research explicitly flags this "Cray input wanted" and routes it as a small ADR-0021 follow-up (run-1 §4 F3/WI-3b); it is a quantity-kind semantics decision, not v1 content. Record here, decide in the ADR-0021 thread.* Alternatives: add a `count` kind now (risks under-specifying the no-conversion semantics). **Cray call because:** it's an ADR-0021 semantics question the research itself reserved for Cray.

## Verification

Offline suite green at every step boundary (baseline ~2131 passed / 5 skipped, confirmed at execution). `vero-lite validate <vertical>` L1+L2 green post-edit; `vero-lite generate <vertical>` clean; `test_schema_parity.py` re-passes after each energy regen; new migrations advance head past `0008` and `alembic upgrade head` runs clean in CI (PLAN-0047 Step 7, postgres). R1 token-budget assertion enforces the 32K tripwire. No live-model run (host-state gate, CLAUDE.md §8). Governed ≠ generated: every R1/R2 machine-drafted artifact is human-canonicalized before its commit.
