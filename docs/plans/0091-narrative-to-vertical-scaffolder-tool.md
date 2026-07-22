# PLAN-0091: Narrative→Vertical Scaffolder Tool v1 — `vero-lite scaffold` (the create shape)

**Status:** Draft
**Owner:** both (Claude Code executes; Cray adjudicates SD-1…SD-4 at Step 0)
**Created:** 2026-07-22
**Related ADRs:** ADR-0024 (binding generation constraints — the ratified half), ADR-0025 (D4 no-currency-in-free-text; D7 marker lineage), ADR-0015 (D2 Tier-1 Mirror seam), ADR-0021 (classify-don't-synthesize), ADR-0031 (gate-plugin-seam frame; tripwire-4), ADR-0032 (D1 wedge / D2 pilot gate / D5 honesty), ADR-006 (D4 Rule of Three)

> **Drafting provenance / author≠reviewer disclosure (ADR-012 D4.3, ADR-013 OQ-1).**
> Drafted (uncommitted) by the in-harness `plan-drafter` subagent under ADR-013 D1
> phased authority, from the session-164 Code dispatch
> (`.claude/handoffs/session-164/2026-07-22-2200-code-plan-drafter-scaffolder-tool-dispatch.md`),
> whose fact pack the drafter re-grounded against `main=caeda74` file-by-file.
> Outline originator = Code (s164) + Cray (typed pick of this PLAN over PLAN-0088 /
> PLAN-0076 T1). Independent reviewers = Code R2 at commit + Cray at ratification.
> Separation: **INTACT**. Code commits via a `docs/*` PR (ADR-009 D2); the drafter
> does not commit.

## Goal

Build the tool PLAN-0086 forward-declared as "the scaffolder TOOL itself — the next
PLAN (L-A)" (`docs/plans/done/0086-fleet-vertical-timed-manual-scaffold.md:411-413`):
a `vero-lite scaffold` CLI command that turns a customer's spoken operational
narrative into a **running governed vertical package** — intake → ontology YAML →
the shipped codegen floor → the vertical package → the AT-2 money spine → the four
external wires — with **every governance value entering through a human-confirmed,
typed intake record, never through the LLM**, and with a hard, designed-in ceiling:
the tool **detects, STOPS, and hands a pre-built argument to a human** at every
governance tripwire; it never clears one.

Spec inputs: the 14-row manual-seam ledger and the 4-question customer-intake log
from PLAN-0086 (gitignored:
`docs/research/private/2026-07-21-fleet-scaffold-seam-ledger.md`,
`docs/research/private/2026-07-21-fleet-scaffold-question-log.md`). PLAN-0086 `:157`
declares the ledger "**IS the scaffolder tool's spec**"; this PLAN reads the ledger
**as corrected** by the four verified drift corrections in § Drift corrections —
two ledger rows are now wrong on disk.

**Strategic classification (stated once):** this is **shape-1 wedge work** under
ADR-0032 D1 element 2 ("Guess in their shape, on the shipped machinery… Every
guessed value is marked 'guess — correct me'", `docs/adr/0032-…md:127-131`). It is
not shape-2/shape-3 work, so ADR-0032 D2's binding pilot gate (`0032:161-167`) does
not apply. The tool's purpose is to make the wedge motion — pre-build a *guessed*
governed hero in the partner's own shape — fast, repeatable, and performable by
someone who is not the founder.

## Why build a tool against a 16–28-minute manual baseline (the honest counter-argument)

The manual path is already fast: PLAN-0086 built a whole new vertical in **27m39s
hands-on** (`0086:535`), PLAN-0089 added a calm path in **~14 min hands-on**
(`0089:435`), PLAN-0090 added a scheduled variant in **16m13s hands-on**
(`0090:506`). A reviewer should ask why an L-effort tool beats that.

The answer, with its caveat intact — **binding, per ADR-0032 D5 and PLAN-0086's own
AC-7 honesty clause**: every one of those numbers is a **lower bound measured under
maximally favourable conditions** — the same operator who built the donor path, a
shipped donor to copy, all machinery already shipped, and every governance decision
pre-ratified by Cray *before* the clock started. None of them measures blind intake
from a real narrative, a fresh operator, or machinery construction. **The three
numbers are companions, never addends — never present them summed.**

What the tool actually buys, grounded in the measurements rather than asserted:

1. **The intake round-trips add ~16% on top of the run, and they are additive —
   not a slice of the hands-on number.** *(Corrected at Code R2; the session-164
   dispatch stated this as "6m51s of 27m39s ≈ 25%", which was wrong twice over.
   The error was the dispatch's, not the drafter's.)* The question log's
   interruption ledger totals **6m51s**, of which **5m17s was fully-blocked idle**
   (3m07s awaiting Q1 + 2m10s awaiting Q2–Q4); the remaining 1m34s was spent asking
   Q1–Q4 while work **continued** on the ฿-independent files ("resumed on the
   ฿-independent files rather than idling"). Critically, **none of it is inside the
   27m39s**: every phase row in PLAN-0086's table has `wall == hands-on`
   (`0086:523-535`) and the rows sum to 27m38s, so all interruption time sits in the
   43m17s − 27m39s = **15m39s of wall that hands-on excludes**. The honest read:
   intake round-trips cost **6m51s of 43m17s wall (~16%)**, blocking work for
   **5m17s (~12% of wall)**. A tool cannot delete customer-answer latency, but it can
   (a) derive the *complete* question set up front instead of discovering gaps
   mid-file, (b) enforce the re-ask discipline the human demonstrably fumbled (Q2's
   accountability half was silently dropped), and (c) batch the asks into one
   customer-shaped pass — which attacks the 5m17s blocked half directly.
2. **The money spine's three parse round-trips go to zero.** `procedures.yaml` cost
   4m41s — more than the other seven files combined — and failed to load 3× on
   ADR-0025 D4 (currency in free text). The lint that rejects that is already
   shipped (`services/engine/procedures/prose_lint.py:133` currency scan, `:217`
   the ADR-0025 D4 canonical-text scan); the tool runs it **pre-emit** instead of
   eating load-time failures one field at a time.
3. **The operator stops being the founder.** The 27m39s belongs to the person who
   built the machinery. The tool encodes the checklist, the wire points (all
   **four** — one of which did not exist when the ledger was written, see
   correction 2), and the tripwire map, so a non-founder operator inherits them
   instead of rediscovering them. This is the wedge's repeatability requirement,
   not a speed requirement.
4. **Five of six verticals shipped with a latent daemon-crash wire bug** until
   PLAN-0090 fixed it (the second registrar map). A generator that writes both
   maps by construction converts a recurring human omission class into a
   structural impossibility.

## Grounding — what is already shipped (verified on `main=caeda74`; invoke, never re-implement)

| Shipped thing | Where (file:line) | This PLAN's relation to it |
|---|---|---|
| Narrative→procedure pipeline S0–S6 (classify LLM → abstain → instantiate → stub-stamp → prose LLM → assemble) | `services/engine/procedures/generator/pipeline.py` (PLAN-0040, under Accepted ADR-0024) | **Reuse.** No second pipeline. |
| Archetype template artifact + registry — **AT-1 family only today** | `services/engine/procedures/archetypes/template.py:108` (`ArchetypeTemplate`), `:254` (`REGISTRY = {AT-1, AT-1b, AT-3}`) | **Extend** with one AT-2 template (Step 4; lineage in § Drift corrections). |
| Restricted draft types + governance-field disjointness | `services/engine/procedures/draft.py:123` (`StepDraft`), `:171` (`ProcedureDraft`), `:186` (`GovernanceStub`), `:109-115` (`GOVERNANCE_FIELDS` union incl. `:98` `VERTICAL_GOVERNANCE_FIELDS = {compliance_criteria}`) | **Reuse.** The LLM emission surface stays exactly this. |
| Deterministic prose-lint (numerics / currency / handler names / approval verbs) | `services/engine/procedures/prose_lint.py:133`, `:217` | **Reuse pre-emit** (Step 4). |
| API exposure of the generator | `services/api/routers/procedure_draft.py:62-70` | **Untouched.** The CLI path does not alter the router or its abstain behaviour. |
| AT-2 abstain guard in the API pipeline | `services/engine/procedures/generator/pipeline.py:82` (`_AT2_ONLY_KINDS`), `:190` | **Untouched** (see Step 4 design note). |
| Codegen floor: ontology YAML → 7 artifacts, EXIT 0, 2m02s measured | `uv run vero-lite validate` / `generate` (console script `pyproject.toml:44-45`) | **Invoke** (ledger row 10: `[one-time-only]` — the floor, never re-implemented). |
| Tier-1 Mirror scaffolder | `services/engine/scaffold.py:876` (`scaffold_vertical`), CLI seam "Requires the ontology … to exist first" (`services/engine/cli.py:84-85`) | **Untouched as a command** (ADR-0015 D2 stays); internals reused where they fit. The new tool starts *before* the ontology exists — exactly the seam `new-vertical` starts after. |
| Per-vertical declared criterion vocabulary (no engine enum) | `services/engine/procedures/spec.py:876-884` (RETIRED note), `:1688` (`compliance_criteria`), `:1717` (`_validate_compliance_criteria`) | **Rely on.** A new AT-2 vertical ships with **zero engine diff** (correction 1). |
| The two executor-registrar maps, pinned EQUAL | `services/api/main.py:141`, `services/engine/cli.py:130` (mirror rationale `:123-129`), equality pin `tests/services/engine/test_cli_registrars.py` | **Write BOTH** (Step 5; correction 2). |
| Archetype label map + procedure census | `services/api/routers/procedures.py:50` (`PROCEDURE_ARCHETYPES`), `tests/api/test_procedures_endpoint.py:40` (`_EXPECTED`), `:151` (`total == 13`) | **Write** the mechanical entries (ledger rows 8–9). |
| AT-2 signature census — **armed for a 5th signature** | `tests/services/engine/procedures/test_at2_signature_retrigger.py:167-205` (`_BASELINE_SIGNATURES`), `:307-319` (set-equality), `:322-342` (obligation-owned guard) | **Never edit the baseline.** Predict + STOP + hand over (Step 6). |
| Committed golden donor: the hand-built fleet vertical | `verticals/fleet_maintenance/` (8-file package + 4 wires) | **The diff-oracle.** PLAN-0086 SD-1(a) committed it *precisely so this PLAN could diff generated output against it* (`0086:186-188`). |

## Drift corrections absorbed (dispatch §3, re-verified by the drafter on disk)

The seam ledger was written 2026-07-21; the tree moved. This PLAN is drafted against
the corrected facts, so it cannot be read against the stale rows:

1. **Ledger row 12 is dead.** The `ComplianceCriterion` engine enum is retired
   (`spec.py:876-884`); the vocabulary is declared per vertical
   (`spec.py:1688`, validated at `:1717`). Consequence built into Step 4: the
   scaffolded vertical **declares its own criterion vocabulary in its
   `procedures.yaml` and touches zero engine code.** No design element of this PLAN
   may assume an "engine edit per vertical" seam.
2. **The hand-wire count is 4, not 3.** PLAN-0090 added the mirror registrar map
   `services/engine/cli.py:130`, deliberately **mirroring, never importing**
   `services/api/main.py:141` (`cli.py:123-129`), with the two sets pinned equal by
   `tests/services/engine/test_cli_registrars.py`. Step 5 writes **both maps**;
   AC-6 makes the equality pin the oracle. (The bug class is real: five of six
   verticals had the daemon-crash omission until PLAN-0090.)
3. **Cite the ledger, never the PLAN-0086 closeout summary.** The closeout
   (`0086:539-545`) says "`[scaffolder-can-generate]`: 6" then enumerates seven
   items (6+5+2 = 13 ≠ 14). The correct tally from the ledger rows:
   **7** `[scaffolder-can-generate]` (rows 1, 3, 4, 5, 7, 8, 9) ·
   **5** `[needs-human-judgment]` (rows 2, 6, 11, 13, 14) ·
   **2** `[one-time-only]` (rows 10, 12) = **14**.
4. **Row 13's example is spent; its lesson is armed.** The N=4 census firing
   self-cancelled the deferral (below) — but the set-equality assertion
   (`test_at2_signature_retrigger.py:307-319`) **remains armed and goes RED on any
   fifth distinct signature**, with "Re-argue it (do not just update this list)"
   written into the assertion. Step 6 is designed to that lesson: detect → STOP →
   hand the human a pre-built comparison table.

**Deferral lineage (why emitting an AT-2 spine is in bounds).** ADR-0024 D7 /
PLAN-0040 LOCKED-7 (`0040:38`) deferred AT-2 generation on Rule-of-Three at N=1.
That deferral (operationalized as the ADR-0025 D7 marker) **was CANCELLED at N=4 —
Cray, typed, 2026-07-21** — recorded durably in the committed marker module
(`test_at2_signature_retrigger.py:76-108`) and in `spec.py:876-884`. Under CLAUDE.md
§1 precedence the newest ratified decision wins: AT-2 emission is no longer barred
on the old ground. Two additional facts make it *safe* now, not merely permitted:
(a) ADR-0024 OQ-8's stated **precondition** for any future AT-2 generation — "a
typed, human-only sub-model for scored-rule / compliance-criteria / DOA-tier
content" — is **MET on disk**: `DoaLadder` / `ScoredRule` / `ComplianceGate` are
typed `governance_content` models, H-class-guarded ("never model-emitted",
`spec.py:872-873`; `draft.py:109-115`); (b) the cancellation resolution steered the
paid extraction at "stop requiring an engine edit per vertical" (landed, PLAN-0087)
— and this PLAN's AT-2 emission is exactly the **structure-only** kind ledger row 11
calls mechanical, with all values human-supplied. The remaining extraction half (the
procedure-aware `ExecutorFactory`) stays owned by **PLAN-0076 Step T1** — this PLAN
does not touch it (see Out of Scope).

## Deliverable shape

A new **Typer subcommand `vero-lite scaffold`** on the existing console script
(`vero-lite = "services.engine.cli:app"`, `pyproject.toml:44-45`; existing commands
`validate` / `generate` / `new-vertical` / `scheduler`), implemented in a new
engine-generic package **`services/engine/scaffolder/`** (placement mirrors the
ADR-0024 OQ-2 reasoning that put `archetypes/` under `services/engine/procedures/`:
the tool is vertical-agnostic engine machinery, not per-vertical config).

- **CLI, not a router, in v1.** The operator is the FDE-style human running intake,
  not the customer; the review surface for generated *procedures* remains the
  PLAN-0039/0040 component (ADR-0024 D8) and the intake UI face (D9) is a
  follow-on, not v1 (see Out of Scope).
- `vero-lite new-vertical` is **not** overloaded: it stays the ADR-0015 D2 Tier-1
  Mirror vehicle (PLAN-0086 `:413` explicitly banned it for this motion). The new
  command covers the seam `new-vertical` declares out of scope — it starts from a
  narrative, *before* the ontology exists (`cli.py:84-85`).
- Inputs: `--narrative <file>` (free text) and/or `--intake <file>` (a typed,
  partially- or fully-answered intake record); output: a new `verticals/<ns>/`
  package + proposed wire edits, **uncommitted**, refusing to overwrite an existing
  namespace. No git operations, ever.

**The ADR-0024 compliance story, stated once and designed to (binding):** the LLM's
emission surface in this tool is *unchanged* from the shipped pipeline — draft-typed
structure + closed-enum classification + advisory prose behind `prose_lint`. Every
governance **value** (฿ tiers, roles, waiver content, criterion ids, thresholds,
synthetic-fixture numbers) enters through the **typed `IntakeRecord`, whose value
slots are operator-input-only by construction** — the LLM has no write path to
them. The deterministic emitters move human-typed values from the intake record
into H-class fields; an unanswered H-slot is emitted as the stub sentinel +
`governance_todo` entry, leaving the spine **draft-loadable but not run-loadable**
(ADR-0024 D6). "Governed ≠ generated" therefore stays a type-level property
(`0024:74-78`), not a prompt hope, on this new surface.

## Acceptance Criteria

All ACs are **offline-verifiable** (CLAUDE.md §8: the offline oracle is the gate).
Every LLM-touching stage runs behind recorded fixtures in tests; MS-S1 is never
required for any AC. A single live smoke is *evidence only*, Cray-gated — see
§ Verification for what it would catch that fixtures cannot.

- [ ] **AC-1 — the command exists and is inert-safe.** `vero-lite scaffold` is
  registered on the existing app (`pyproject.toml:44-45`); `--help` and a dry-run
  (`--plan-only`: print the derived question queue + file manifest, write nothing)
  work offline with deterministic exit codes; the command **refuses to run** if
  `verticals/<ns>/` already exists (no overwrite path in v1). Verified via the CLI
  test runner.
- [ ] **AC-2 — intake derives the complete question set up front, with mechanical
  re-ask discipline.** A typed `IntakeRecord` + a deterministic **required-slot
  checklist** derived from (the AT-2 template's obligation set × the ontology's
  three judgment slots × the synthetic-fixture value slots). On a committed
  fleet-*shaped* narrative fixture (same four gap classes as PLAN-0086's run:
  feel-only authority tiers, an unbounded emergency bypass, an ambiguous requester,
  a threshold-less comparison rule — deliberately **not** the verbatim private
  narrative, which stays gitignored for future-run freshness), the derived open
  queue covers all four gap classes. **The Q2 test, named:** answering only
  "cap = ฿10,000" to the emergency-waiver question fills exactly the cap sub-slot;
  the ratifier and window sub-slots remain **individually open** and re-surface.
  One number is never treated as a full answer.
- [ ] **AC-3 — ontology emission is mechanical where the ledger says it is, and
  refuses to guess where it says judgment lives.** The emitter produces the 6-object
  OCT skeleton + all 7 link_types from the grammar alone; the three judgment slots
  (Asset noun · per-entity band property · `RecommendedAction.action_type`
  vocabulary) and narrative-mined property enums are emitted **only from confirmed
  intake entries** — unconfirmed ⇒ the run stops at the ontology stage with the
  open queue printed, it does not default. The emitted YAML passes the invoked
  floor: `vero-lite validate` + `generate` EXIT 0 into a scratch tree (row 10:
  invoked, never re-implemented).
- [ ] **AC-4 — package emission with no fabricated numbers.** Rows 1/3/4/5 files are
  emitted from the ontology (`__init__.py`, `handlers.py` with
  `ACTION_TYPES` == the ontology enum + registrar-name convention,
  `data_adapter/__init__.py`, `procedures_factory.py` incl.
  `advisory_builder=GateAdvisoryBuilder()` and StepKind slots computed from the
  spine), plus the `synthetic.py` skeleton (row 6) where **every numeric literal
  either traces to an intake answer or carries a `# GUESS — รอแก้` marker** —
  asserted by a scanner test, so "must not fabricate; ask" is falsifiable, not
  aspirational. Event emission honours latest-per-asset ordering semantics (row 6).
  The README (row 14) is emitted with the mechanical parts (env block, step
  walk-through) generated and the human parts (problem statement, the
  **"stated but NOT enforced" register** — fed by the intake queue's unanswered
  non-schema sub-slots, e.g. Q2's ratifier/window) clearly stubbed.
- [ ] **AC-5 — the money spine, structure generated, values human, lint pre-paid.**
  An AT-2 `ArchetypeTemplate` exists (Step 4) modelling row 11's fixed spine
  (intake → judge → reshape → rule_gate → approve → fulfill + SoD + terminal); the
  emitted `procedures.yaml` round-trips `load_procedures`; its gate signature
  matches the template (ADR-0024 D4 agreement — a contradicting `gate_kind` is a
  hard failure); the vertical **declares its own `compliance_criteria`**
  (`spec.py:1688`) with **zero engine diff** (correction 1); every governance value
  traces to a confirmed intake answer, else the stub sentinel + `governance_todo`
  (draft-loadable, refused by `validate_runnable` — D6); and the emitter runs the
  shipped free-text lint (`prose_lint.py:133/:217`) **before** writing, so the
  golden fixture emits with **zero** ADR-0025 D4 parse round-trips (the manual run
  ate three).
- [ ] **AC-6 — all four wires, by construction.** The wire-writer produces the
  registrar wrapper + entry in `services/api/main.py:141` **and** the mirror entry
  in `services/engine/cli.py:130` (lazy-import convention preserved — row 7), the
  `PROCEDURE_ARCHETYPES` entry (`procedures.py:50`, classified from gate content,
  row 8), and the census updates (`test_procedures_endpoint.py:40` `_EXPECTED` +
  the `total ==` pin, row 9). Oracle: with the scaffolded vertical present, the
  existing equality pin `tests/services/engine/test_cli_registrars.py` and the
  procedures-endpoint census both go GREEN — the same tests that hard-fail on a
  missed wire today.
- [ ] **AC-7 — the golden diff-oracle: regenerate fleet.** From a committed, typed
  intake fixture carrying the Q1–Q4 answers + the three ontology judgments (the
  answers are in-tree facts already: the ladder `[0,5k)/[5k,50k)/[50k,∞)`, waiver
  cap ฿10k relaxing `three_bid`, requester=ช่างใหญ่ with approve-down (PLAN-0075
  Policy B), `three_quote` ≥ ฿20k × 3 vendors), the tool regenerates the fleet
  package into a scratch tree and it **structurally matches** committed
  `verticals/fleet_maintenance/`: same file set; same ontology object/link/
  property-enum sets incl. the band property on the Asset; `ACTION_TYPES` set
  equal; spine gate signature equal to the shipped one
  (`("rule_gate", ("three_quote",)), ("doa_tier", ("THB",))` — the
  `_BASELINE_SIGNATURES` fleet row); governance values equal to the Q1–Q4 answers;
  wire entries equal to the in-tree ones. Byte-equality is asserted **only** where
  the ledger claims it (row 4: `data_adapter/__init__.py` modulo namespace) —
  prose may differ, structure may not.
- [ ] **AC-8 — the governance ceiling, exercised not asserted.** The tool computes
  the would-be AT-2 signature of the spine it is about to emit using **the same
  fingerprint key** as the census (Step 6 extracts the key helpers so the two
  cannot drift), compares against the shipped baseline, and — since any new
  AT-2-bearing vertical **is** a candidate 5th signature — **STOPS before writing
  any wire edit**, emitting a pre-built comparison table (new signature vs each
  `_BASELINE_SIGNATURES` row, per-axis deltas: gate composition / authority
  quantity / enum surface) that names the exact test that will go RED and quotes
  its own instruction ("Re-argue it — do not just update this list"). The tool
  **never modifies `_BASELINE_SIGNATURES`** and has no flag that does. Offline
  test: a synthetic would-be-5th-signature intake ⇒ stop + table + zero writes to
  `tests/`; the fleet golden fixture (a baseline member) passes through without
  firing.
- [ ] **AC-9 — hard non-capabilities hold.** Test-asserted where mechanically
  possible, review-asserted otherwise: zero git operations; zero procedure-run
  firing; zero writes to any **existing** `verticals/*/procedures.yaml`
  (ADR-0024 `:147`); the full AC suite passes with MS-S1 unreachable.
- [ ] **AC-10 — counted prose is disposed per SD-4's ratified option** in the files
  this tool's wire-writer touches (the three count-carrying comments:
  `tests/api/test_procedures_endpoint.py:5-6`, `:116`, `:144` + the `main.py`
  registrar-module docstring count, ledger rows 7/9) — no fourth stale count is
  possible along the tool's write path.

## Out of Scope

- ❌ **Auto-commit / any git operation.** Output is uncommitted working-tree files;
  Code commits via PR (ADR-009 D2). Also no write-back into any **existing**
  `verticals/*/procedures.yaml` (ADR-0024 `:147`).
- ❌ **Firing a run of the scaffolded procedure.** No run (ADR-0024 D10). The live
  boot→fire→park walk stays a human demo step; one live smoke is evidence only,
  Cray-gated (CLAUDE.md §8).
- ❌ **The extend shapes** — calm-path (PLAN-0089) and scheduled-variant (PLAN-0090)
  scaffolding — per SD-2's recommendation. Their seams have no ledger; they are
  this tool's v2 once their own seam evidence exists.
- ❌ **The intake UI face / edit-mode review surface** (ADR-0024 D8/D9, PLAN-0017
  face). v1 is CLI-first; the API generator path (`procedure_draft.py:62-70`) and
  its AT-2 abstain guard (`pipeline.py:82`) are untouched.
- ❌ **The procedure-aware `ExecutorFactory` extraction** — owned by PLAN-0076
  Step T1 (`test_at2_signature_retrigger.py:322-342` guards that ownership). The
  tool writes today's two registrar maps as they exist; if T1 lands, Step 5's
  wire-writer simplifies in T1's PLAN, not here.
- ❌ **Anything shape-2** (self-improvement loop) — ADR-0032 D2's pilot gate stands;
  this PLAN neither needs nor claims the named escape.
- ❌ **dbt/SQLMesh auto-canonicalization** — a funded Phase-2 deliverable per
  ADR-0032, never a pilot precondition. Scaffolded verticals are synthetic
  in-memory (building_materials/fleet pattern): **no ORM, no Alembic**.
- ❌ **Clearing any governance tripwire** — editing `_BASELINE_SIGNATURES`, the
  census totals beyond the mechanical row-9 entries, or any G1/G2-adjacent
  artifact. Detect → STOP → hand over is the ceiling (ledger row 13), and it is a
  feature of the design, not a gap.
- ❌ **Replacing `vero-lite new-vertical`** (ADR-0015 D2 stays as-is) and any
  multi-narrative / multi-procedure batch mode (mirrors ADR-0024 OQ-6:
  one-vertical-per-run).

## Surfaced decisions (SD-1…SD-4 — Cray ratifies at Step 0; recommendations are contingent, not chosen)

### SD-1 — Does the narrative→ontology-YAML stage need its own ADR?

**Question:** ADR-0024 deliberately scoped itself to procedures and left the
ADR-008 ontology codegen path untouched (`0024:6`). The tool's ontology stage is
new authoring surface: mechanical skeleton (6 objects, 7 link_types) + exactly
three concentrated human judgments (ledger row 2) + LLM-*proposed*,
human-ratified enum values (action vocabulary, property enums).
**Options:** (a) a new ADR; (b) an ADR-0024 amendment; (c) a PLAN-level design
decision, no ADR.
**Recommendation: (c), with a named promotion tripwire.** Reasoning: an ADR is
warranted when a new *invariant class* or cross-cutting contract is created. This
stage creates none — it binds itself to already-Accepted invariants: closed-grammar
skeleton emission is deterministic code; the three judgment slots are
human-confirmed inputs (the ADR-0021 classify/propose-then-human-ratify pattern,
already Accepted); values are H-class (ADR-0024 D3, extended by analogy but
enforced by the same shipped machinery). (b) is the worst option — ADR-0024's clean
self-scoping (`:6`) is load-bearing and amending it to cover ontology muddies a
ratified boundary. **The tripwire that flips this to (a):** if the build finds the
ontology stage needs the LLM to emit *structure* beyond the fixed 6-object grammar
(new object types, new link shapes) or any unratified vocabulary to land without a
human confirm, STOP — that is a new authoring invariant and gets its own ADR before
the stage ships. What makes this Cray's call: it sets where the governance-artifact
boundary sits for all future authoring surfaces, not just this one.

### SD-2 — v1 breadth: which of the three worked shapes?

**Question:** create-a-vertical (PLAN-0086) vs add-a-calm-path (PLAN-0089) vs
add-a-scheduled-variant (PLAN-0090).
**Recommendation: create only.** Reasoning: (1) the evidence asymmetry is total —
the seam ledger and question log exist *only* for create; the extend runs produced
timing numbers but no seam spec; (2) the golden oracle exists only for create —
PLAN-0086 SD-1(a) committed the fleet vertical expressly as this PLAN's diff target
(`0086:186-188`); (3) the wedge motion itself is create-shaped (ADR-0032 D1:
pre-build a guessed governed hero in the partner's shape); (4) Rule-of-Three
discipline (ADR-006 D4): create is N=1 *with a spec*; the extend shapes are N=2
*without one* — scaffolding them now would be abstraction ahead of evidence.
Alternatives: all-three (rejected: triples surface on the thinnest evidence);
create+scheduled (rejected: the scheduled seam's hard part — `Schedule`
governance pins — was measured but never ledgered). What makes this Cray's call:
it is a bet on where the next pilot conversation actually lands.

### SD-3 — The intake form's shape and re-ask discipline

**Question:** the ledger's own closing finding is that "the tool's hard part is the
**intake form**, not the emission", and the question log is the only empirical data
about it.
**Recommendation: a typed required-slot checklist operated as an interview loop,
with guess-prefill only where guessing is licensed.** Concretely, three slot
classes with different disciplines:

1. **Schema-bearing authority/numeric slots** (the DOA ladder, waiver cap,
   rule-gate threshold + vendor count, requester role/SoD): **ask, never guess,
   never fabricate** (row 6; row 11). Asked in the customer's shape — Q1's finding:
   the ladder is **one open question**, not three ("ต้อมเคาะเองได้ถึงกี่บาท…" got the
   whole ladder in one sentence).
2. **Non-schema-bearing accountability slots** (Q2's waiver ratifier + window):
   ask; if unanswered, **do not block** — route to the README's "stated but NOT
   enforced" register (row 14) *and* keep the sub-slot on the open queue.
3. **Demo-design slots** (synthetic values inside customer-stated ranges, enum
   glosses, prose): **guess-prefill, marked** — `# GUESS — รอแก้` per value, exactly
   ADR-0032 D1's "guess — correct me" discipline.

**Re-ask discipline (the Q2 finding, made mechanical):** every question is a typed
bundle of sub-slots; an answer fills only the sub-slots it actually covers;
unfilled sub-slots stay **individually** open and re-surface on the next pass. One
number is never accepted as a full answer. The LLM's role in intake is bounded to
narrative pre-fill *proposals* (gap detection and the checklist are deterministic;
candidate enum values are proposals the operator confirms) — testable behind
recorded fixtures. Alternatives: a fixed questionnaire (rejected: Q1 shows
customer-shaped open questions outperform form fields); a fully LLM-driven
interview (rejected: un-testable offline, and the checklist — the part that failed
in the manual run — is exactly the part that must be deterministic). What makes
this Cray's call: the intake form *is* the customer-facing motion; its feel in a
real conversation is founder judgment, not derivable from four data points.

### SD-4 — Counted prose

**Question:** three comments along the tool's write path carry hard-coded counts;
one was stale before PLAN-0086's run even started (ledger row 9).
**Recommendation: stop writing counts into comments; where a count is load-bearing,
it must be an executable assertion.** The repo's own pattern already embodies this —
`assert total == 13` (`test_procedures_endpoint.py:151`) is a count that cannot go
silently stale; "across the six procedure-bearing verticals" (`:5-6`) is one that
already has. Scope discipline: this PLAN converts/removes only the three counts in
files the wire-writer touches (+ the `main.py` docstring count, row 7) — not a
repo-wide sweep. Alternative — the tool owns counted prose (rejected): it
perpetuates a drift surface with a 100% observed staleness-per-run rate, and prose
rewriting is the highest-fragility generation class the tool could take on for the
lowest value. What makes this Cray's call: it is a repo-wide authoring convention
(the same class as the Tier-0 "N=1-comment drift" lesson), not a local
implementation choice.

## Steps

### Step 0 — Cray adjudicates SD-1…SD-4

Record the four rulings in this PLAN (edit under its Draft status). No build
before Step 0 lands; SD-1's ruling gates whether Step 2 needs an ADR first
(CLAUDE.md §8: ADR merged before related implementation).

### Step 1 — Intake engine (`services/engine/scaffolder/intake.py`)

The typed `IntakeRecord` (operator-input-only value slots), the deterministic
required-slot checklist derived from (AT-2 obligations × ontology judgment slots ×
fixture value slots), the question queue with sub-slot decomposition + re-ask
discipline (SD-3), guess-marking, and the "stated but NOT enforced" register feed.
Committed fixtures: the fleet-shaped narrative (AC-2) and the fleet golden intake
record (AC-7). Oracle: AC-1, AC-2.

### Step 2 — Ontology emitter + the invoked floor

Skeleton from the 6-object grammar + 7 link_types; the three judgment slots +
mined enums filled only from confirmed intake; then invoke `vero-lite validate` +
`generate` into the scratch tree and require EXIT 0. (If SD-1 = (a)/(b), this step
waits for that ADR.) Oracle: AC-3.

### Step 3 — Package emitter

Rows 1/3/4/5 + the `synthetic.py` skeleton with traceable-or-marked values and
latest-per-asset ordering + the README with the gap register. Oracle: AC-4.

### Step 4 — The AT-2 template + spine emitter

Add one `ArchetypeTemplate` for the row-11 spine to
`services/engine/procedures/archetypes/` (registered; D4 signature-agreement
machinery reused). **Design note, R2-reviewable:** the API pipeline's abstain guard
(`pipeline.py:82,190`) stays as-is — the scaffolder instantiates the AT-2 template
**directly, operator-confirmed** (trivially satisfying ADR-0024 D5's
human-confirmed-match requirement) rather than growing the S1 classify surface;
growing classify to AT-2 is deliberately deferred until the API path wants it. The
emitter injects intake values into H-class fields, stubs the unanswered, declares
`compliance_criteria` per PLAN-0087, and runs `prose_lint` pre-emit. Oracle: AC-5.

### Step 5 — Wire-writer

The four wire points (both registrar maps with the lazy-import convention;
`PROCEDURE_ARCHETYPES` classified from gate content; census `_EXPECTED` + total),
plus the SD-4 disposition of the counted comments. Oracle: AC-6, AC-10.

### Step 6 — Governance-ceiling detector

Extract the census fingerprint helpers (`_at2_gate_kinds`, `_content_enum_surface`,
`test_at2_signature_retrigger.py:219-257`) into an engine module consumed by both
the census test and the tool — **the baseline list and both assertions stay in the
test, byte-identical**; this refactor may not weaken the tripwire (the test's
set-equality against `_BASELINE_SIGNATURES` must still fire on a genuine 5th
signature — R2 verifies the assertion is untouched). The tool predicts the would-be
signature, and on baseline extension STOPS pre-wire-write with the comparison
table. Oracle: AC-8.

### Step 7 — Golden end-to-end + gate

The fleet regeneration diff-oracle (AC-7), the non-capability asserts (AC-9), full
offline gate (`mypy services/` + full `tests/`, per the CI-scope rule), closeout
evidence. Then — separately, Cray-gated, evidence-not-gate — at most one live smoke
(§ Verification).

## Verification

- **The offline oracle is the gate** (CLAUDE.md §8). AC-1…AC-10 run with MS-S1
  unreachable; LLM stages are exercised via recorded fixtures (the PLAN-0040 D12
  pattern, already proven for this pipeline).
- **What one live run would catch that fixtures cannot** (named per the
  fixture-masking hazard): whether the real `gpt-oss:20b` (a) proposes action-type
  / enum candidates that collide with the grammar's reserved names or drift from
  the closed vocabularies the fixtures encode, (b) handles a **Thai-language**
  narrative's numerals and role nouns as well as the fixture assumes (the real
  customer answers are Thai — Q1–Q4), and (c) abstains where the fixture says it
  abstains. One live smoke, explicit Cray go before it, result recorded as
  evidence in the closeout — never as an AC.
- **The tool's own success claim is falsifiable by construction:** AC-7 is a diff
  against a committed, hand-built donor the tool's spec was measured on. If the
  regenerated fleet does not structurally match the real one, the tool is wrong —
  not the oracle.
