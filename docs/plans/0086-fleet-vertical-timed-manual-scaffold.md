# PLAN-0086: Fleet-Maintenance Vertical — Timed Manual Scaffold (AI-Transition View-2 Grounding)

**Status:** Draft (SD-1…SD-3 await Cray ratification at Step 0; the timed window opens at Step 1)
**Owner:** Claude Code (executes + commits per ADR-009 D2) + Cray (simulated customer: delivers the dirtied narrative, answers the question log)
**Created:** 2026-07-21 (session 156, ratified View-2 sequence)
**Related ADRs:** ADR-0032 (D6 fit filter, D5 positioning honesty, D1(3) offline-arm discipline, public-repo boundary), ADR-0025 (DoaLadder REQUIRES an emergency_waiver), ADR-0023 (import-scan discovery), ADR-0015 D2 (the Tier-1 `new-vertical` scaffold — deliberately NOT used here), ADR-0030 (advisory never-raise precedent), ADR-009 D1/D2 (authoring / commit boundary)
**Related PLANs:** PLAN-0085 (gate advisory builder + fence-test mechanics — the L-B wire), PLAN-0081 (building_materials — the lean money/doa_tier template this scaffold hand-copies), PLAN-0075 (cumulative approver roles policy), PLAN-0084 (map↔monitor surfaces the live check renders into)

> Drafted by the in-harness `plan-drafter` subagent (ADR-013 D1); outline + fact-pack
> originated by Code (session 156), View-2 sequence ratified by Cray (typed,
> 2026-07-21). Independent review: Code (R2) + Cray at PR merge. SD-1…SD-3 below
> await Cray's AskUserQuestion ratification (Step 0) — no implementation before it.

## Goal

Run ONE **timed, manual** scaffold of a 6th vertical — `fleet_maintenance` (Thai
trucking) — from a **customer-style narrative**, producing a **dual deliverable**:

1. **A working 6th vertical**: emergency roadside breakdown → parts sourcing → tiered
   THB approval, booting live with the PLAN-0085 gate advisory wired from day one
   (L-B: "pipeline ที่ทีมคุณอ่านออกตั้งแต่วันแรก" is the headline; the time number is
   secondary evidence).
2. **The measurement pack** that specs the future narrative→pipeline scaffolder TOOL
   from practice, not from reading code: a per-phase timing log (the pitch number —
   "customer narrative → running governed pipeline in X hours"), a manual-seam ledger
   (the tool's generation spec), and a customer-question log (the tool's intake-form
   spec).

This is the View-2 grounding experiment of the ratified AI-Transition sequence (Cray,
typed, 2026-07-21 s156; arc context in the gitignored working note
`.claude/handoffs/session-156/2026-07-21-0851-code-session156-discussion-ai-transition-two-views.md`
— binds nothing; this PLAN carries the framing). Rule-of-Three is over-satisfied
(5 verticals exist); this run grounds the automation. The scaffolder TOOL is a LATER
PLAN that consumes this PLAN's measurements (L-A).

*Public-repo note:* the customer is **fictional** — no real partner/company names
anywhere in the committed tree (ADR-0032 public-repo boundary). The narrative
(pre-dirtied draft: gitignored
`docs/research/private/2026-07-21-fleet-maintenance-narrative-draft.md`; Cray's
dirtied version: same private dir) stays gitignored.

## Locked decisions (Cray, typed/AskUserQuestion, 2026-07-21 s156 — do not reopen)

- **L-A Sequence:** timed manual scaffold FIRST; the scaffolder tool is a LATER PLAN
  consuming this PLAN's measurements. This PLAN delivers the manual run + the numbers.
- **L-B Pitch axis = onboarding-first:** every scaffolded vertical ships READABLE on
  day one — the PLAN-0085 gate advisory MUST be wired in the new vertical's factory
  (one constructor arg; Verified ground below). This deliberately extends the
  PLAN-0085 opt-in set (procurement-only in v1) to fleet_maintenance — a Cray-locked
  extension, not scope creep; all EXISTING verticals stay byte-identical (AC-4).
- **L-C Vertical #6 = fleet maintenance (Thai trucking):** truck fleet, emergency
  roadside breakdown → parts sourcing → tiered THB approval. ADR-0032 D6 fit filter
  4/4: assets = trucks; numeric stream = GPS/odometer; band anomaly =
  breakdown/maintenance-due; governed approval = repair-spend DOA + SoD.
- **L-D Narrative protocol:** Code drafted the customer-style narrative; **Cray is
  dirtying it** (cutting data, shuffling order, adding tangents). The DIRTIED version
  is the experiment's input; the scaffold works from it ONLY, and gaps are resolved by
  ASKING Cray (simulated customer intake) — every question logged as measurement.
  **Timing starts only when the dirtied narrative is delivered** (Step 1 = input gate).

## Verified ground (plan-drafter, 2026-07-21 — file:line re-verified on disk this draft unless marked *census*; executor re-verifies before building)

**Minimal viable file set (8 files; template = building_materials, the leanest
money/doa_tier vertical):**
`verticals/fleet_maintenance/{__init__.py, README.md, ontology/fleet_maintenance_v0.yaml, data_adapter/__init__.py (register_fleet_maintenance_adapter), data_adapter/synthetic.py (OBJECT_SOURCES + operational_events), handlers.py (ACTION_TYPES + ACTION_DESCRIPTIONS + register_fleet_maintenance_handlers), procedures.yaml, procedures_factory.py (register_fleet_maintenance_procedure_executors)}`.
`economic_impact.py` is optional — discovery registers it only when present
(`discovery.py:62-73`). `verticals/_template/` is discovery-SKIPPED
(`discovery.py:34`) and a README-only placeholder — NOT a copy source; hand-copy from
building_materials. NO committed ORM: `verticals/*/generated/` is gitignored
(`.gitignore:42`); committed codegen destinations exist only for energy + core via
`_ORM_COMMITTED_DEST` (`services/engine/code_generator.py:871-874`). No Alembic
migration.

**Mandatory hand-wire points OUTSIDE the package (exactly 3):**
1. `services/api/main.py:133-139` — `_PROCEDURE_EXECUTOR_REGISTRARS` dict entry + a
   lazy-import wrapper coroutine (model: `:125-130`, building_materials).
2. `services/api/routers/procedures.py:38-55` — `PROCEDURE_ARCHETYPES` entry
   (procedure_id → `"AT-2"`); cosmetically optional but test-coupled.
3. `tests/api/test_procedures_endpoint.py` — the deliberate census tripwire:
   `_EXPECTED` (`:29-52`) gains the fleet entry, `assert total == 10` (`:120`) bumps
   to 11, exact-set assert at `:103` follows `_EXPECTED`. Census finding: the only
   repo-wide test that hard-fails on a 6th procedure-bearing vertical
   (discovery/registry tests use subset semantics); AC-1's full-suite run is the
   real oracle if a second tripwire exists.

**Automatic via convention (NO hand-wire):** adapter/handlers/economic-impact
registration via `discover_and_register` import-scan (`discovery.py:37-73`;
conventional names `register_<ns>_adapter` / `register_<ns>_handlers`); ontology path
`verticals/<v>/ontology/<v>_v0.yaml` (*census:* `ontology_meta.py:152-154`);
procedures path (*census:* `spec.py:1755-1757`); principals/auth generic from the
active vertical's procedures.yaml (*census:* `auth.py:49-57`); `OCT_VERTICAL` is a
flat config field, no registry (*census:* `config.py:179`).

**CLI (allowed tooling):** `uv run vero-lite validate fleet_maintenance` then
`uv run vero-lite generate fleet_maintenance` — validates YAML first, refuses to emit
on failure (`services/engine/cli.py:37-52`), then emits **7 gitignored artifacts**
(pydantic/sql/jsonschema/mcp/typescript/orm/context-pack —
`code_generator.py:888-911`; fleet has no committed dest, so all land under
`generated/`). It does NOT generate procedures.yaml / factory / handlers / adapter /
fixtures / tests — those are the hand-written (and hand-TIMED) part.
**Protocol rule (not an SD):** `vero-lite new-vertical` (`cli.py:55-117`) scaffolds
only a Tier-1 recommend/breach mirror (ADR-0015 D2), NOT the AT-2 money spine — and
using ANY generator for the parts the future scaffolder will replace contaminates
the manual measurement. Allowed tools = the ontology codegen CLI only.

**procedures.yaml minimum for the doa_tier gate (template =
`verticals/building_materials/procedures.yaml`, PLAN-0081):** agent block with
`autonomy_ceiling: gated` (`:36`) + step_kinds/action_handlers allowlists; principals
roster with cumulative senior roles (PLAN-0075 Policy B); ONE procedure:
intake(query, declared reads) → judge(evaluate, threshold_field band) →
reshape(transform → flat amount/currency + compliance signal map — doa_tier's
`_spend()` fails closed without `amount`) → rule_gate(evaluate) → approve(action,
gated, `governance_content.kind: doa_tier` (`:214`), currency THB, ascending tiers,
MANDATORY `emergency_waiver` block (`:221-227` — ADR-0025 D3, reuse the
procurement-shaped waiver per PLAN-0081)) → terminal gated action;
`separation_of_duties` binding intake↔approve (`:267`). Every `handler:` named must
be in handlers.py ACTION_TYPES (discovery-registered; procurement's
`_ensure_handlers()` is procurement-specific — *census*, not needed here).
Procurement's `emergency_sourcing_round` (*census:*
`verticals/procurement/procedures.yaml:98`) is the closest DOMAIN match (scored_rule
sourcing + doa_tier) if the dirtied narrative demands quote comparison.

**Advisory wire (L-B, PLAN-0085):** ONE constructor arg — in the new
`procedures_factory.py`, at the `GovernanceActionExecutor(...)` construction
(pattern: `verticals/building_materials/procedures_factory.py:106-110`, which today
passes NO builder), add `advisory_builder=GateAdvisoryBuilder()` (import from
`services.engine.procedures.gate_advisory` — class at `:107`). The executor already
conditionally invokes it (`governance_step.py:235-238`, trace-only, never-raise);
default `None` elsewhere keeps every other vertical byte-identical.

**Pitfall checklist (each burned before — encode as build-time checks):**
- synthetic events carrying `datetime` → JSONB fails on persist: sanitize
  `json.loads(json.dumps(raw, default=str))` before any DB run.
- doa_tier REQUIRES the `emergency_waiver` block — fails closed without it.
- any run-firing entrypoint needs `discover_and_register()` called first.
- trace kinds: fleet emits only EXISTING kinds (`doa_tier_resolved` etc. +
  `advisory_recommendation`) → NO new registry row expected; if the build finds
  otherwise, STOP and flag (registry row + tripwire update = PLAN-0080 AC-3
  mechanics, and a deviation from this census).

## The measurement protocol (pre-committed BEFORE the run — CLAUDE.md §6/§11: the pass/fail read is fixed before the clock starts)

The experiment half — this PLAN's reason to exist. All three artifacts live
**gitignored** during the run (suggest `docs/research/private/2026-07-NN-fleet-scaffold-*`);
their summaries land in this PLAN's closeout evidence.

1. **Timing artifact** — checkpoint rows at the SD-2 granularity; each row carries
   **wall-clock** and **hands-on** time separately; interruptions logged with reason
   and subtracted explicitly. Clock starts at Step-1 delivery; stops when AC-2 first
   passes. The summary TABLE lands in the closeout (the number is the pitch
   deliverable).
2. **Manual-seam ledger** — EVERY file hand-written + every hand-wire touched, each
   tagged exactly one of `[scaffolder-can-generate]` / `[needs-human-judgment]` /
   `[one-time-only]`. **This ledger IS the scaffolder tool's spec** — the next PLAN's
   primary input.
3. **Customer-question log** — every question asked back to Cray, with what triggered
   it (which narrative gap, at which phase) and the answer received. Measures where
   the narrative/template under-specifies — the tool's intake-form spec.

**Honesty caveat (binding — ADR-0032 D5):** Code drafted the pre-dirtied narrative,
so the measured time is a **lower bound on true blind intake**; the dirtying +
question log partially restore validity. The headline number is NEVER presented
without this caveat (AC-7).

## Surfaced decisions (SD-N — Cray ratifies at Step 0; recommendations are contingent, not chosen)

### SD-1 — Commit the vertical, or scratch it?

**Question:** does `fleet_maintenance` land in the tree via normal PR flow, or is it
built in a scratch/worktree with only the measurements kept?
**Options:**
- **(a) Commit via normal PR flow.** A 6th demo asset + permanent, reproducible
  evidence for AC-2; the census-test/archetype updates land properly (they are REAL
  scaffold work the tool must generate — the seam ledger needs them measured either
  way). COSTS: maintenance surface grows (roughly building_materials-sized: a
  synthetic in-memory vertical, no ORM/Alembic, suite grows by the fleet test set);
  the census pins now say 6/11, so vertical #7 bumps them again (known, small).
- **(b) Scratch/worktree, keep only the measurements.** Zero maintenance surface;
  but the working vertical evaporates, AC-2's evidence is non-reproducible, the demo
  loses a 6th asset, and a future scaffolder PLAN has no live reference scaffold to
  diff its generated output against.

**Recommendation: (a).** The dual deliverable is L-A's point — the vertical is not a
byproduct, it is half the deliverable; and the scaffolder PLAN's acceptance story
("generate what this PLAN hand-wrote") wants the hand-written original in-tree to
diff against. The maintenance cost is the smallest of any vertical class we ship
(in-memory synthetic, no migrations).
**Why Cray:** repo maintenance surface vs demo-portfolio value is a portfolio call,
not an engineering derivation.
**RESOLVED/RATIFIED (Cray, 2026-07-21 s156, AskUserQuestion): (a)** — commit via
normal PR flow; the vertical lands in-tree as the 6th demo asset and the scaffolder
PLAN's diff-reference.

### SD-2 — Timing granularity

**Question:** how fine are the timing checkpoints?
**Options:**
- **(a) Per template-section checkpoints** (~9 rows: the 6 narrative-template phases
  + wiring + tests + live-verify).
- **(b) Coarse 3-phase** (author / wire / verify).
- **(c) Fine per-file.**

**Recommendation: (a).** (b) cannot tell the scaffolder PLAN *which parts* the tool
saves — it specs nothing. (c) over-instruments: logging inflates the very hands-on
time being measured (the observer effect is a validity threat to the pitch number —
said plainly here so the closeout can repeat it). (a) matches the seam ledger's
natural grain: one checkpoint per generatable part.
**Why Cray:** the number is Cray's pitch artifact — granularity determines what claim
it can honestly support ("narrative → pipeline in X hours, of which the tool
eliminates Y").
**RESOLVED/RATIFIED (Cray, 2026-07-21 s156, AskUserQuestion): (a)** — per
template-section checkpoints (~9 rows: 6 narrative-template phases + wiring + tests +
live-verify).

### SD-3 — Procedure scope

**Question:** ONE hero procedure, or also a calm-path second procedure (the
narrative's tire/PM-interval thread)?
**Options:**
- **(a) ONE hero procedure:** emergency breakdown → parts sourcing → tiered THB
  approval (building_materials-lean spine).
- **(b) Hero + calm-path** (tire/PM-interval reorder thread) in this run.

**Recommendation: (a).** The experiment measures the MECHANISM (narrative → first
governed pipeline), and one AT-2 spine exercises every seam the scaffolder must
generate. The tire/PM thread is a natural SECOND-session extension that would measure
a *different, also valuable* number — "extend an existing vertical" — and folding it
in now would blur both measurements into neither. Defer it as a named candidate
follow-on (not scheduled here).
**Why Cray:** experiment-portfolio design — which number the pitch needs first is
Cray's call.
**RESOLVED/RATIFIED (Cray, 2026-07-21 s156, AskUserQuestion): (a)** — ONE hero
procedure; the tire/PM calm-path stays a named, unscheduled follow-on measuring the
"extend an existing vertical" number.

## Acceptance Criteria

- [ ] **AC-1 Offline gate:** full suite green including the census-tripwire update
  (`_EXPECTED` fleet entry, `total == 11`, archetype map entry) + `mypy --strict
  services/` + `ruff check` / `ruff format --check` at CI scope, re-baselined at
  execution HEAD (the offline oracle is the gate).
- [ ] **AC-2 Live boot + park + advisory:** `OCT_VERTICAL=fleet_maintenance` boots; a
  seeded run parks `waiting_human` at the doa_tier gate with the advisory
  `ReasoningStep` ALREADY in the persisted approve-step trace — grounded FLEET
  reasons from the run's own data, `detail.model` arm disclosure
  (`deterministic`/stub), and NO confidence key in any operator-surfaced field
  (PLAN-0085 AC-2/AC-8 discipline). Proven by reading the persisted run, then
  corroborated in the Monitor gate panel (connection strip `LIVE`).
- [ ] **AC-3 Narrative fidelity:** every ฿ threshold, role, and rule in
  `procedures.yaml` is traceable to a sentence in the DIRTIED narrative or to a
  logged customer answer (question-log entry) — recorded as a spot-auditable mapping
  table in the closeout. Nothing invented silently.
- [ ] **AC-4 Existing verticals byte-identical:** no file of the five existing
  verticals or the engine changes semantics; the pinned governance hashes of all
  previously-shipped procedures are unchanged (reuse the PLAN-0085 pinned-hash test
  pattern — parked runs keep resuming).
- [ ] **AC-5 Advisory fence, flipped for fleet (L-B):** the adapted PLAN-0085 fence
  set passes with advisory-on as the DEFAULT arm: advisory PRESENT in the parked
  approve trace, approve-step `audit` payload byte-identical vs a `builder=None`
  baseline arm, raise-injection cannot fail/park/divert the run (never-raise,
  ADR-0030 D5).
- [ ] **AC-6 Measurement pack complete + internally consistent:** phase times sum ≈
  wall total (interruptions accounted); every hand-written file and hand-wire appears
  in the seam ledger with exactly one tag; every question has trigger + answer;
  summary table, ledger summary, and question-log summary land in the closeout.
- [ ] **AC-7 Honesty caveat:** the lower-bound caveat appears co-located with the
  headline number EVERYWHERE it is recorded (closeout, STATUS, any pitch note).

## Out of Scope

- ❌ **The scaffolder TOOL itself** — the next PLAN (L-A); it consumes this PLAN's
  seam ledger + question log as its spec.
- ❌ **`vero-lite new-vertical`** — banned by protocol (Tier-1 mirror only, ADR-0015
  D2; and any generator use for scaffolder-replaceable parts contaminates the manual
  measurement).
- ❌ **Scheduler-daemon wiring** — `_register_executor_factory` is procurement-only
  today (`cli.py:120-131`); fleet's need is UNCONFIRMED — defer.
- ❌ **`economic_impact.py` facet** — optional; building_materials precedent.
- ❌ **Committed ORM / Alembic** — `generated/` stays gitignored; no
  `_ORM_COMMITTED_DEST` entry.
- ❌ **New UI surfaces** — existing views only. View A (map) lights only if the
  ontology carries geo — an authoring choice inside the scaffold, not a PLAN
  commitment.
- ❌ **New trace kinds** — none expected (Verified ground pitfall #4); a discovered
  need is flagged, not silently added.
- ❌ **Rung-2 anything** (AI as principal — its own future PLAN).

## Steps

### Step 0: SD ratification gate (untimed)

Present SD-1…SD-3 to Cray (AskUserQuestion). No implementation before ratification —
SD-1 decides the landing (PR vs scratch), SD-2 the checkpoint template, SD-3 the
procedure count. Record ratified picks as per-SD stamps (PLAN-0084/0085 pattern).
Pre-create the three measurement artifacts (empty, with the SD-2 checkpoint template)
so the clock never waits on scaffolding the instruments.

**SATISFIED — 2026-07-21 (s156, AskUserQuestion):** all three SDs ratified, every
pick = the draft recommendation ((a)/(a)/(a): commit via PR / ~9-row template-section
checkpoints / one hero procedure). The dirtied narrative was delivered
2026-07-21T14:20:45+07:00 (before this ratification — logged as the delivery stamp;
the hands-on clock starts at Step-1 pre-flight completion, not at file arrival,
since Step 0 is untimed by construction). Measurement artifacts pre-created at the
SD-2 granularity in `docs/research/private/` (gitignored).

### Step 1: INPUT GATE — the dirtied narrative (timing starts at delivery)

Cray delivers the dirtied narrative (gitignored, `docs/research/private/`). Pre-flight
before the clock: working tree clean (stash unrelated drafts — pre-smoke hygiene),
baseline suite state known. **The wall clock starts when the dirtied file is
delivered.** From here to the end of Step 6, every question about the narrative goes
to Cray and into the question log — no silent invention (AC-3).

### Step 2: Author the package (timed)

Hand-write the 8-file set from the building_materials template (Verified ground):
ontology YAML from the narrative; the money-spine `procedures.yaml` (agent block,
cumulative principals, the SD-3-scoped procedure(s), THB doa_tier ladder +
emergency_waiver, SoD intake↔approve); handlers; synthetic adapter (datetime-sanitize
pitfall); `procedures_factory.py` with the L-B advisory arg
(`advisory_builder=GateAdvisoryBuilder()`). Maintain all three measurement artifacts
continuously.

### Step 3: CLI validate + generate (timed)

`uv run vero-lite validate fleet_maintenance` → fix to green →
`uv run vero-lite generate fleet_maintenance` (7 gitignored artifacts; verify "OK:" +
mtime). Ledger-tag the CLI-covered parts `[scaffolder-can-generate]`-adjacent
(already automated — record as the tool's existing floor).

### Step 4: The 3 mandatory hand-wires (timed)

`main.py` registrar (lazy-import wrapper + dict entry), `PROCEDURE_ARCHETYPES` entry,
census-test update (`_EXPECTED` + `total == 11`). Each is a ledger row.

### Step 5: Tests + offline gate (timed)

Fleet test set per the building_materials pattern + the AC-5 adapted fence set +
the AC-4 pinned-hash sibling check. Run the full AC-1 gate (suite / mypy strict /
ruff at CI scope).

### Step 6: Live verification (timed — clock stops at AC-2 pass)

Boot `OCT_VERTICAL=fleet_maintenance`, seed, confirm the park at the doa_tier gate
with the advisory persisted + visible in the Monitor gate panel (strip `LIVE`).
**Timing stops at first AC-2 pass.** Local demo stack only — no MS-S1, no host-state
change (§8).

### Step 7: Measurement-pack closeout (untimed)

Summary table + seam-ledger summary + question-log summary + the AC-3 fidelity
mapping into this PLAN's closeout evidence, each stamped with the AC-7 caveat.
Full artifacts stay gitignored as the scaffolder-PLAN's input (pointer recorded).
Under SD-1(a): PR referencing PLAN-0086; after merge + Cray confirmation,
`git mv docs/plans/0086-*.md docs/plans/done/`.

## Verification

1. AC-2 is the experiment's finish line: a governed fleet run parks at a THB gate
   with day-one-readable advice — L-B made concrete on vertical #6.
2. AC-3's mapping table proves the pipeline came from the narrative + logged intake,
   not from the drafter's imagination.
3. AC-4 + AC-5 prove the scaffold is additive: five verticals byte-identical, the
   advisory shown-never-routes fence holds on the new one.
4. AC-6 + AC-7 make the number usable: internally consistent, honestly caveated —
   the scaffolder PLAN can be written from the ledger alone.
