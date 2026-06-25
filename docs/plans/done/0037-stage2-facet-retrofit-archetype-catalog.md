# PLAN-0037: Stage 2 PREP — 5-facet retrofit to N=4 + procedure archetype catalog

**Status:** Complete — Step A + Step B shipped 2026-06-25 (session 77); archived to `done/`.
**Owner:** both (Code executed; Cray adjudicated SD-1/2/3 + merged each PR)
**Created:** 2026-06-25
**Completed:** 2026-06-25 (session 77). Step A — 5-facet retrofit to N=4 (#425). Step B — procedure archetype catalog at `docs/conventions/procedure-archetypes.md` (#426). Cray resolved the surfaced decisions: SD-1 = one PR for the 3 verticals; SD-2 = Step B as a follow-on PR; SD-3 = catalog home `docs/conventions/`. Step C (the ADR-016 `facet:` first-class field) stays out of scope — a separate Cowork-drafted ADR; Stage 3 (the generator) remains Rule-of-Three-deferred.
**Related ADRs:** ADR-016 (procedure engine), ADR-0023 (auto-discovery), ADR-006 (vertical plugin + Rule-of-Three), ADR-0019 (tiered routing / determinism invariant), ADR-0015 (Tier-1 synthetic)
**Related PLANs:** PLAN-0036 (done — the procurement vertical that produced the 5-facet template)

> **Author≠reviewer disclosure (ADR-012 D4.3 / ADR-013 OQ-1).** This PLAN was
> drafted by the in-harness `plan-drafter` subagent under ADR-013 D1 phased
> authority. Outline originator: **Cray** (2026-06-25 dispatch). Independent
> reviewer: **Cray at PR merge** (Code R2-reviews + commits per ADR-009 D2).
> Separation: **INTACT** — the drafter is not the ratifier; the originating
> request and the merge-time review are distinct acts by distinct actors
> (subagent drafts → Code commits → Cray ratifies).

## Goal

Bring all **four** vero-lite verticals (`energy`, `supply_chain`, `aquaculture`,
and the already-instrumented `procurement`) to **consistent 5-facet
instrumentation** as the Rule-of-Three substrate for the "generative procedures"
target (memory `project-vero-ultimate-target-generative-procedures`; the 3-phase
generate / run / monitor arc). This PLAN does **two PREP deliverables only**:

- **Step A — 5-facet retrofit.** Add the structured **5-facet** annotation
  (`input · decision-condition · llm-assist · output · governance`) as **YAML
  comment blocks**, one per procedure step, to the `procedures.yaml` of `energy`,
  `supply_chain`, and `aquaculture`, mirroring the exact comment format already
  shipped in `verticals/procurement/procedures.yaml` (PLAN-0036 Stage 1, SD-4).
- **Step B — procedure archetype catalog.** A new reference doc naming the
  reusable **workflow shapes** observed across the now-N=4 instrumented
  verticals (AT-1, AT-1b, AT-2, AT-3 below).

The framing is deliberately self-explanatory to a future cold reader: these PLAN
files are retained as a historical archive substrate for later cross-project
work-pattern analysis (Cray's stated ทาง-1 rationale, 2026-06-25).

## Acceptance Criteria

Pre-committed pass/fail (bake into review). **PASS** requires all four:

- [ ] **(1) Format parity.** All 3 retrofit files (`energy`, `supply_chain`,
  `aquaculture`) carry a 5-facet comment block **per step**, matching the
  procurement template's `# facet[<step_id>]` / `#   input:` / `#   decision:` /
  `#   llm-assist:` / `#   output:` / `#   governance:` layout.
- [ ] **(2) Parse-clean.** `load_procedures()` parses **all four** verticals with
  zero error (the loader uses `YAML(typ="safe")` → comments are discarded at
  parse, so Step objects are **byte-identical** to pre-retrofit; this non-impact
  is the acceptance anchor).
- [ ] **(3) No regression.** The **full offline test suite** is green against the
  pre-retrofit baseline (**1651 passed**) — the acceptance gate per CLAUDE.md §8.
  **No live MS-S1 LLM run.**
- [ ] **(4) Comment-only diff.** `git diff` shows **only `#` comment-line
  additions** — zero data-line change, zero `services/` engine edit, zero
  demo/JS edit.
- [ ] **(5) Catalog (Step B).** The archetype catalog doc exists, names AT-1 /
  AT-1b / AT-2 / AT-3, lists which verticals/procedures instantiate each, and
  records each shape's governance signature.

**FAIL** = any YAML parse error, any test regression, or any non-comment diff
line.

### Why the diff is provably inert (acceptance anchor detail)

`services/engine/procedures/spec.py:341 load_procedures_file` loads via
`YAML(typ="safe")`, which **discards comments at parse time**. The `Step` model
declares `extra="forbid"`, so a first-class `facet:` *field* would be **rejected**
— hence the annotation is **comment-only by constraint**. The story-mode demos
(`services/api/static/assets/view-story.js`) are hand-authored static JS that
**never read `procedures.yaml` at runtime**, so demos are unaffected. Therefore a
green suite + comment-only diff is a *complete* proof of non-impact.

## Out of Scope

- ❌ **Step C — the ADR-016 amendment** that promotes `facet:` to a first-class
  schema field. That is a **separate Cowork-drafted ADR** (it edits the engine's
  `Step` model to relax `extra="forbid"` for a typed `facet` block). The honest
  env-vs-in-file `decision-condition` nuance captured below is the **input** to
  that ADR, not resolved here.
- ❌ **Stage 3 — the procedure generator.** **Rule-of-Three-forbidden** (ADR-006)
  until the generalized schema is extracted from the N=4 substrate. Authoring the
  generator before the third+fourth instrumented vertical exists is exactly the
  premature-abstraction this PLAN's PREP work guards against.
- ❌ Any `services/` engine edit, any demo/JS edit, any data-line edit to the
  retrofit YAMLs, any ontology (`*_v0.yaml`) edit.
- ❌ Live MS-S1 LLM verification (host-state, CLAUDE.md §8 — not an acceptance
  gate).

## Steps

### Step A1: Retrofit `energy/procedures.yaml`

Annotate `substation_health_sweep` (3 steps), mirroring the procurement comment
format. Per-step facets:

- **`read_readings`** (query): input = latest temperature reading per active
  Asset; decision = —; llm-assist = —; output = reading per asset; governance = —.
- **`judge`** (evaluate): input = read_readings set; decision = **DETERMINISTIC
  over-temperature band authored via ENV** (`OCT_RECOMMEND_THRESHOLD`,
  `direction=above`) — **NO in-file `threshold` field** (encode this honestly,
  cite env); llm-assist = —; output = per-asset verdict {breach, ok}; governance
  = determinism invariant (ADR-0019).
- **`restart_breaches`** (action / gated): input = judge (breach subset);
  decision = —; llm-assist = —; output = restart proposal; governance = human
  go/no-go on an irreversible write (handler `restart`, no-op stub).

### Step A2: Retrofit `supply_chain/procedures.yaml`

Annotate `cold_chain_excursion_sweep` (3 steps) — structurally identical to
energy (handler `hold`). Same env-authored band caveat on `judge`
(`OCT_RECOMMEND_THRESHOLD`, `direction=above`, **no in-file threshold**):

- **`read_temps`** (query): latest temperature per in-transit Shipment.
- **`judge`** (evaluate): **ENV-authored** cold-chain ceiling band; verdict
  {breach, ok}; determinism invariant.
- **`hold_breaches`** (action / gated): hold proposal on the breach subset; human
  go/no-go (handler `hold`).

### Step A3: Retrofit `aquaculture/procedures.yaml`

Annotate `morning_pond_health_round` (5 steps). Unlike energy/supply_chain,
aquaculture authors its band **IN-FILE** (`threshold: 4.0`, `direction: below`,
`watch_margin: 1.0`) — encode `decision-condition` as **in-file band** (cite the
fields):

- **`read_do`** (query): latest DO reading per active Pond.
- **`judge`** (evaluate): **IN-FILE** deterministic band (`threshold:4.0` /
  `below` / `watch_margin:1.0`); verdict {breach < 4, watch 4–5, ok > 5}; the
  watch zone is the ADR-0019 escalate-to-human band.
- **`aerate`** (action / gated): breach subset; handler
  `start_emergency_aerator` + `tiers` taxonomy; human go/no-go.
- **`escalate_watch`** (action / gated): watch subset → precautionary
  water-exchange proposal (ADR-0019 watch→gated; routing trigger = the
  deterministic verdict, **never confidence**, ADR-010 IN-3); handler
  `increase_water_exchange`.
- **`summary`** (action / auto): whole verdict set; handler `echo`; auto terminal
  receipt artifact.

### Step A-load-bearing: capture the env-vs-in-file split honestly

The instrumentation **reveals** that `judge` bands are authored two ways across
the N=4 substrate:

| Vertical | `judge` band source | Fields |
|---|---|---|
| `energy` | **ENV** | `OCT_RECOMMEND_THRESHOLD`, `direction=above` — no in-file field |
| `supply_chain` | **ENV** | `OCT_RECOMMEND_THRESHOLD`, `direction=above` — no in-file field |
| `aquaculture` | **IN-FILE** | `threshold:4.0` / `direction:below` / `watch_margin:1.0` |
| `procurement` | **IN-FILE** | `threshold:0.8` / `direction:above` / `watch_margin:0.2` (+ calm-path `100.0`/`below`) |

Encode each vertical's `decision-condition` facet to state its **actual** source
(env vs in-file). This split is **load-bearing for Step C**: the generalized
schema must model **both** band-authoring styles. Do not paper over it by writing
a fictional in-file threshold into energy/supply_chain (that would violate the
comment-only constraint **and** misrepresent the source).

### Step B: Author the procedure archetype catalog

A new reference doc naming the reusable workflow shapes already visible across the
now-N=4 instrumented verticals. For each archetype: name the shape, list the
verticals/procedures that instantiate it, and note the **governance signature**.

- **AT-1 `anomaly→action`** — sense → judge(deterministic band) → gated action on
  breach. Instances: `energy.substation_health_sweep`,
  `supply_chain.cold_chain_excursion_sweep`, `procurement.low_stock_reorder_round`
  core, `aquaculture.morning_pond_health_round` core. Governance signature: single
  deterministic band + one human gate on the irreversible write.
- **AT-1b** (variant of AT-1) — AT-1 **+** a watch→gated proposal branch **+** an
  auto summary terminal. Instance: `aquaculture.morning_pond_health_round`.
  Governance signature: AT-1 + the ADR-0019 watch→gated escalation + an auto
  (un-gated) terminal receipt.
- **AT-2 `request→approve→fulfill`** — intake → judge → source(scored rule) →
  compliance(rule gate) → tiered DOA(human) → fulfill(write) → audit. Instance:
  `procurement.emergency_sourcing_round` (the governance-heaviest shape).
  Governance signature: per-criterion rule gate + tiered DOA + emergency waiver
  (escalate-never-skip) + SoD + traceable audit.
- **AT-3 `monitor→reorder`** — read_stock → judge(reorder point) → gated reorder.
  Instance: `procurement.low_stock_reorder_round` (calm-path). Governance
  signature: deterministic reorder-point band + single-tier human approval.

(Step B's **home** is OPEN — see SD-3 below.)

## Verification

Run the offline suite via the WSL toolchain; confirm:

1. `load_procedures()` for all four verticals returns without error (the
   discard-comments-at-parse non-impact proof).
2. Full offline suite **1651 passed** (no regression vs baseline).
3. `git diff` on the three retrofit files shows **only `#`-prefixed line
   additions** (machine-checkable: every added hunk line starts with `+#` or is
   whitespace).
4. Step objects byte-identical pre/post (implied by #1+#3; the `YAML(typ="safe")`
   comment-discard guarantees it).

No live MS-S1 run. The offline oracle is the gate (CLAUDE.md §8).

## Surfaced decisions (LOCKED vs OPEN)

### LOCKED (constraints — do not relitigate at execution)

- **L-1 Comment-only annotation.** `spec.py` `Step` declares `extra="forbid"`; a
  first-class `facet:` field is rejected. Annotation is comment-only **by
  constraint**. Promotion = the downstream Step C ADR.
- **L-2 Zero runtime/parse effect.** `YAML(typ="safe")` discards comments; Step
  objects byte-identical; demos (hand-authored static JS) unaffected.
- **L-3 Offline gate only.** Acceptance = the offline suite (baseline 1651). No
  live MS-S1 LLM run (host-state, CLAUDE.md §8).
- **L-4 Zero non-comment diff.** No `services/` edit, no demo/JS edit, no
  data-line change — only `#` comment additions.
- **L-5 Encode the env-vs-in-file band split honestly** (energy/supply_chain =
  ENV; aquaculture/procurement = in-file). Load-bearing input to Step C.

### OPEN (Cray/Code to adjudicate — flagged, not resolved here)

- **SD-1 PR granularity for Step A.** ONE PR for all 3 verticals
  (`plan-drafter`'s lean — the three diffs are tiny, homogeneous comment-only
  additions reviewable in one pass) **vs** 3 PRs (one per vertical, finer
  revert granularity). *Why Cray's call:* review-load vs revert-granularity is a
  workflow-ergonomics judgment, not derivable from the dispatch.
- **SD-2 Step B sequencing.** Ship the archetype catalog (Step B) in the **same**
  PLAN execution / PR cycle as Step A **vs** as a **follow-on** PR. *Why Cray's
  call:* depends on whether the catalog should wait for a second reviewer pass on
  the instrumented N=4 before it's named.
- **SD-3 Home for the archetype catalog doc.** `docs/conventions/` (a canonical
  reference looked up deliberately) **vs** `docs/for_llm/` (a derived cold-start
  snippet) **vs** a `verticals/`-level README (co-located with the substrate).
  *`plan-drafter` recommendation:* **`docs/conventions/`** — the catalog is a
  canonical standard the future Step C ADR + Stage-3 generator design will cite,
  not a derived snippet (Tier 2.5) and not vertical-specific. *Final call OPEN.*
