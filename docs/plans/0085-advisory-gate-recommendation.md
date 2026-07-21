# PLAN-0085: Advisory Gate Recommendation (AI-Transition Rung 1)

**Status:** Draft
**Owner:** Claude Code (executes + commits per ADR-009 D2)
**Created:** 2026-07-21 (session 156, post-rehearsal AI-Transition arc)
**Related ADRs:** ADR-0019 (shown-not-routing boundary — the load-bearing fence), ADR-010 IN-3 (confidence is advisory, never gates), ADR-0030 (advisory dimension = trace-carried precedent), ADR-007 D2 (envelope untouched), ADR-0032 (D1(3) offline-arm discipline, D5 positioning honesty), ADR-009 D1/D2 (authoring / commit boundary)
**Related PLANs:** PLAN-0035 (the s74 trust shape — L-C's source), PLAN-0080 (trace attribution channel + OQ-1, the parked cousin this PLAN must differentiate from), PLAN-0084 (map↔monitor linkage — the Monitor surface this renders into), PLAN-0075 (cumulative approver roles — the gate-resolution baseline AC-4 pins)

> Drafted by the in-harness `plan-drafter` subagent (ADR-013 D1); outline + fact-pack
> originated by Code (session 156), umbrella sequencing ratified by Cray (typed,
> 2026-07-21). Independent review: Code (R2) + Cray at PR merge. SD-1…SD-5 below
> await Cray's AskUserQuestion ratification (Step 0) — no implementation before it.

## Goal

Rung 1 of the AI-Transition arc: at procurement's tiered-DOA approval gate, generate
an **advisory recommendation with grounded reasons** — at run time, persisted into the
step's reasoning trace under the PLAN-0080 attribution channel — and show it to the
human approver, **who still decides exactly as today**. The signal is SHOWN, never
routes (L-B): same gate, same approver resolution, same audit. This is deliberately
the *substrate* for a future Rung 2 (AI as a principal in the DOA ladder — its own
PLAN, out of scope here). Arc context: the sequenced AI-Transition discussion is
captured in the gitignored note
`.claude/handoffs/session-156/2026-07-21-0851-code-session156-discussion-ai-transition-two-views.md`
(working note, binds nothing; this PLAN carries only the neutral framing that Rung 1
precedes Rung 2).

*Public-repo note:* this PLAN names no design partner — "the procurement
design-partner dataset" throughout (ADR-0032 public-repo boundary, :76-86).

## Locked decisions (Cray, typed, 2026-07-21 — do not reopen)

- **L-A Sequence:** Rung 1 first as the foundation, then Rung 2. PLAN-0085 = Rung 1
  ONLY. Rung 2 (AI principal in the ladder, band + sampling audit + kill switch) is a
  future PLAN that builds on this one.
- **L-B Advisory-only:** the LLM signal is SHOWN, never routes. ADR-0019:50-57
  explicitly permits "a model signal MAY be **shown** to the human at `waiting_human`,
  but it MUST NOT decide whether a set escalates"; anything routing-affecting is an
  **ADR-010 IN-3 reopen** and trips ADR-0019's scope fence (:77-79, :92-93). (The s155
  STATUS shorthand "reopens ADR-0019" was a near-miss — the ADR that would reopen is
  **ADR-010**; the s155 correction is recorded in `docs/STATUS.md`
  §"Current Focus" (s153–155 block).)
- **L-C Trust shape:** the operator surface shows *what / grounded-why / approve gate*
  plus a "show full reasoning trace" toggle; **NO operator-facing confidence
  badge/number** (ratified s74, re-recorded s142:
  `docs/plans/done/0035-governed-action-verify-reshape-build.md:591-602`; executed by
  PR #823). Advice renders as REASONS, never scores.

## Differentiation from PLAN-0080 OQ-1 (required boundary)

PLAN-0080 OQ-1 (`docs/plans/done/0080-trace-attribution-legibility-and-ui-convention.md:633-649`)
parked an **LLM-narrated ATTRIBUTION layer** — LLM prose *about* who/what produced
trace entries. This PLAN is different in kind: **LLM-AUTHORED ADVICE** — new content
(a recommendation + reasons), carried under an llm-actor trace kind on the *existing*
attribution channel; the labels themselves stay deterministic. OQ-1's three park
reasons are inherited here as **design constraints**, not obstacles:

- **(a) Offline arm ⇒ run-time generation.** The advice is generated AT RUN TIME and
  persisted in the trace — never rendered-time — so the demo's offline arm shows the
  real persisted artifact, not a fallback (ADR-0032 D1(3), :110-112).
- **(b) Attribution stays deterministic.** The advice is CONTENT carried under an
  llm-actor trace kind; it is not a label generator. The registry mapping stays
  static data (PLAN-0080 L-4).
- **(c) §8 host-state discipline + the s99 NULL-lift result.** No live-model
  dependency on the demo path; any live MS-S1 arm is opt-in and Cray-gated
  (CLAUDE.md §8).

OQ-1's surviving idea — a run-level "why did this need the CONTROLLER to sign?"
summary for a non-technical reader, sitting **above** the trace — is the recommended
UX direction for the advice content (SD-4).

## Verified ground (plan-drafter, 2026-07-21, re-verified on disk this draft — executor re-verifies before building)

**Trace substrate + the three shipped advisory precedents**
- `ReasoningStep` model: `services/engine/actions.py:20-24` (`step_id`, `kind`,
  `summary`, `detail`; no actor field — actor is registry-derived from `kind`).
- Advisory dimension = trace-carried is the ADR-0030 load-bearing precedent
  (`docs/adr/0030-box4-economic-impact-facet.md:88-103, :123-139`). The three shipped
  precedents: `economic_impact` (`services/engine/economic_impact.py:118-162` —
  **never-raise**, returns `[]` on any producer failure, "advisory must never harm the
  action, ADR-0030 D5"), `action_verification` ("adds confidence + a trace and NEVER
  overrides", quoted at ADR-0030:90-93), and confidence-as-advisory
  (`services/engine/llm/trace.py` — fact-pack cited, corroborated by the ADR-0030
  precedent chain).
- ADR-007 D2 envelope is NOT amended by an advisory dimension (PLAN-0035 SD-3=(a)
  trace-only: `docs/plans/done/0035-...:587-590`; `docs/STATUS.md` §"Current Focus"
  corroborates).
- Trace-kind registry: `services/api/static/assets/trace-kinds.js` — 23 kinds, strict
  JSON between `TRACE_KINDS_JSON_BEGIN/END` markers, actor closed set
  `human|llm|engine`; `llm_inference` EXISTS with actor `llm` (:40). A NEW kind
  requires a registry row or `tests/api/test_trace_kind_labels.py` goes RED
  (set-equality tripwire, PLAN-0080 AC-3). Unmapped kinds render dashed +
  `data-actor="unknown"` (:22-24). Trace-entry `kind` feeds NO hash (:26-28 — "Do not
  conflate" with definition-side `Step.kind`).

**Procedure seam (`emergency_sourcing_round`, `verticals/procurement/procedures.yaml:98`)**
- Step order (grep-confirmed): intake(:114) → enrich(:133) → judge(:160) →
  source(:178) → derive_spend(:222) → compliance(:252) → **approve(:283**, action /
  `autonomy: gated`, handler `request_approval`, `doa_tier` ladder :300-311, facet
  already declaring `llm_assist: "draft the justification + the approver exec-summary
  (advisory, editable)"` :320**)** → issue_po(:324) → audit(:339, echo). SoD binds
  intake↔approve (:364-368). Agent allowlist: `step_kinds` + `action_handlers`
  (:46-54).
- Siblings (⚠️ dispatch line-swap corrected on disk):
  `scheduled_emergency_sourcing_round` at **:480** and
  `event_emergency_sourcing_round` at **:842** — same intake→…→compliance→approve
  shape, but **neither carries an `issue_po` step** (approve :650/:1015 → audit
  :684/:1049). Each pins its own governance hash independently.
- Closed `StepKind` set: query / evaluate / action / human_task / transform
  (`services/engine/procedures/spec.py:55-62`). Executors are per-kind,
  factory-registered; procurement's factory:
  `verticals/procurement/hero_demo/run.py:702-715` (`_executors` at :262-305 — ACTION
  = `GovernanceActionExecutor(base=ActionStepExecutor(client_factory=...))`, one
  shared ACTION executor for source/approve/issue_po across ALL procedures in the
  vertical); wired at startup in `services/api/main.py`.
- **No shipped procedure hits a live LLM today** (negative claim, confirmed): every
  registered factory binds `advisory_stub_factory`
  (`services/engine/procedures/advisory_stub.py:67-89` — deterministic ChatClient, "No
  network, no MS-S1"; procurement `run.py:706-707`, docstring :657-661 "fires NO live
  MS-S1 call"). `ActionStepExecutor`'s LLM path exists behind the `client_factory`
  seam (`services/engine/procedures/action_step.py:151-162` builds the real
  OllamaClient as the DEFAULT factory), but every registered vertical factory
  overrides it with the stub.
- **Placement constraint:** an `autonomy: auto` action step placed AFTER the approve
  gate must have handler ∈ `{echo}` or the procedure is not run-loadable
  (`_check_no_auto_downstream_of_gate`, `orchestrator.py:669-703`;
  `_AUDIT_TERMINAL_HANDLERS` :647). BEFORE approve (e.g. between compliance and
  approve) carries no such restriction. A `gate_kind: none` action step owes only
  `handler` + `autonomy` (`derive_governance_todo`,
  `services/engine/procedures/draft.py:280-309` — no `governance_content`, no SoD
  entry).
- **Fail-soft pattern:** the orchestrator has NO advisory tolerance — any executor
  exception is fail-and-divert to FAILED or `on_failure: escalate_to_human` →
  `waiting_human` (`orchestrator.py:964-993`). The shipped advisory pattern is
  never-raise INSIDE the facet producer (`economic_impact.py:118-148`: catch all, log
  a warning, return `[]`). The advisory builder here MUST swallow its own failures and
  emit a degraded/absent advisory — never fail, park, or divert the run.
- **⚠️ Governance-hash blast radius (fires only under SD-1 option a):** adding ANY
  step changes the pinned snapshot — `step_id`/`kind`/`autonomy`/`handler` always
  enter the hash (`governance_pin.py:58-100, :103-123`) → every parked run refuses
  fail-closed at gate/resume with a 409-shaped `ProcedureError`
  (`assert_governance_pin`, `persistence.py:260-287`; the only sanctioned path is
  cancel + fresh run). The advisory's PROMPT/OUTPUT stay OUTSIDE the hash regardless
  of SD-1 (no facet/output/trace key enters the snapshot unless declared
  `governance_content`). If SD-1=(a) is ratified, this PLAN carries a **demo-reset
  note** (Step 6): drain/cancel parked runs before merging; the boot self-seed
  re-seeds.

**UI seams (Monitor)**
- `services/api/static/assets/view-monitor.js`: "Waiting on a human" banner
  (:288-296), gate panel + Submit (:297-313, `data-testid="gate-panel"`),
  `O.reasoningTrace` per-step (:344), Show-audit toggle (:345-357), approver chip
  from `gate_principal_recorded` (:316-326).
- ui.md conventions apply: no hardcoded ids in JS; `?v=` bump on every edited asset.

**Boundary ADRs / constraints**
- ADR-0019 (`docs/adr/0019-watch-gated-proposal-routing.md`): decision :28-35,
  no-new-kind :44-48, determinism invariant :50-61, scope fence :73-79, guarded
  reopen line :92-93.
- ADR-0032: D1(3) deterministic-offline demo discipline :110-112 ("no live-model or
  network dependency in the room"); D5 ownership/auditor line :188-196 + "never say
  AGI-ready / self-modifying" :198-199; D6 fit filter :202-212; public-repo boundary
  :76-86.
- CLAUDE.md §8: data residency (local MS-S1 default; Claude API only with consent +
  non-PII); "All AI outputs are assistive"; host-state gate — explicit Cray go before
  any MS-S1 warm/run; the offline oracle is the gate.
- s154/s155 STATUS grounding: predict+warn is OCT feature 3 / Shape-1 passing D6 IF
  deterministic, and the determinism-line correction (the real fence =
  ADR-0019:50-57 + ADR-010 IN-3) — both recorded in `docs/STATUS.md`
  §"Current Focus" (s153–155 block).

## Surfaced decisions (SD-N — Cray ratifies at Step 0; recommendations are contingent, not chosen)

### SD-1 — Insertion shape: where the advisory is generated

**Question:** where does the advisory recommendation get produced and attached?
**Options:**
- **(a) New advisory action step** (`autonomy: auto`, `gate_kind: none`, never-raise
  executor) between `compliance` and `approve`. Cleanest governance-draft visibility
  (its own step + facet), placement is legal (before the gate — no
  auto-downstream-of-gate conflict). COST: changes the governance hash of every edited
  procedure → parked-run 409 blast radius + demo reset (Verified ground ⚠️); also a
  new step per sibling procedure.
- **(b) Advisory generated inside the EXISTING approve/gate path** — the ACTION
  executor's doa_tier propose path appends ≤1 advisory `ReasoningStep` to the
  `approve` step's own trace before the run parks. No YAML change, **zero hash
  change**, no parked-run 409s; the advice lands exactly where the human looks (the
  gate panel's step). Single-responsibility concern mitigated by putting the builder
  in its own module with the `economic_impact` never-raise contract — the gate's
  control flow is untouched, it only gains a trace append.
- **(c) Computed at seed/run time by vertical wiring, no YAML step and no executor
  change** — least visible; splits the demo path from the engine path (HTTP-fired /
  scheduled / event runs would not carry it unless wired separately).

**Recommendation: (b).** It mirrors ALL THREE shipped advisory precedents (each is a
trace entry emitted within an existing flow — none is a pipeline step); it FULFILLS
the approve step's already-declared facet (`llm_assist: "draft the justification +
the approver exec-summary (advisory, editable)"`, procedures.yaml:320) rather than
adding a new declaration; and it keeps the governance hash byte-identical (provable
by test, AC-6), which honors "the advisory must never harm the run" at the fleet
level too — no parked-run casualties. Emission MUST happen in the propose path
(before suspension) so the parked run's persisted trace already carries the advice
(OQ-1 constraint (a)).
**Why Cray:** (a) vs (b) trades governance-draft visibility against hash blast
radius — how visible the advisory step should be in the authored procedure surface is
a product/demo-narrative call, and (a) forces a demo-reset event.
**RESOLVED/RATIFIED (Cray, 2026-07-21 s156, AskUserQuestion): (b)** — advisory
emitted inside the existing approve/gate propose path; zero YAML change, zero hash
change, AC-6 runs its hash-identical arm.

### SD-2 — LLM path for v1

**Question:** what produces the advice content?
**Options:**
- **(a) Deterministic-only:** advice built from the run's own data (quotes, resolved
  tier, breach context, waiver state) by templated reasons — zero live-model
  dependency; but "LLM advisory" is then nominal.
- **(b) Stub-first with an opt-in live arm:** the builder speaks through the existing
  `ChatClient`/`client_factory` seam; the DEFAULT arm builds deterministic grounded
  reasons from run data (demo-safe, honest, offline — effectively (a)'s content
  through (b)'s seam), while a live MS-S1 swap exists behind the seam for non-demo
  runs — **opt-in, host-state-gated per §8, never in the demo room** (ADR-0032
  D1(3)).
- **(c) Live-first:** violates ADR-0032 D1(3) + §8 for the demo path; not viable.

**Recommendation: (b).** The seam already exists (`action_step.py:151-162` /
`advisory_stub.py:86-89`); the marginal cost over (a) is an interface, not a
dependency; and it is the honest substrate claim for Rung 2 (the live capability
exists behind a gate, the demo arm is deterministic). The advisory's `detail` payload
MUST carry the producing arm (`model` from `ChatResult` — `"stub"` vs a real model
id) so the record never overstates which arm ran.
**Why Cray:** how much "real LLM" Rung 1 must contain to support the AI-Transition
pitch honestly is a positioning call (ADR-0032 D5 discipline).
**RESOLVED/RATIFIED (Cray, 2026-07-21 s156, AskUserQuestion): (b)** — stub-first
through the ChatClient seam; default arm deterministic grounded reasons; live MS-S1
opt-in, §8-gated, never in the demo room; mandatory `detail.model` arm disclosure.

### SD-3 — Scope across sibling procedures

**Question:** manual `emergency_sourcing_round` only, or all three
(`scheduled_` :480 / `event_` :842 too)?
**Recommendation: contingent on SD-1.** Under **(b)**: all three automatically and
at zero extra cost — the siblings share the vertical's single registered factory and
ACTION executor, so the advisory fires at ANY doa_tier gate in the vertical;
carving out manual-only would require procedure-id special-casing (an anti-pattern).
Guard the blast radius vertical-side: the builder is passed to the executor as an
optional constructor argument that ONLY procurement's factory supplies in v1 — other
verticals stay byte-identical. Under **(a)**: manual-only first (one hash re-pin,
not three).
**Why Cray:** whether the scheduled/event demo entry points should show the advisory
in v1 is a rehearsal-priority call (same class as PLAN-0084 SD-D).
**RESOLVED/RATIFIED (Cray, 2026-07-21 s156, AskUserQuestion — folded into the SD-1
pick): all three procedures** via SD-1(b)'s shared factory/executor; other verticals
stay byte-identical through the constructor-argument opt-in guard.

### SD-4 — UI surface

**Question:** trace-only, or ALSO a small "Advisory" block in the Monitor gate panel?
**Recommendation: gate-panel block + trace.** Render a compact advisory block inside
the gate panel (view-monitor.js:297-313 area, above Submit): what is recommended +
2-4 grounded reasons as short prose, carrying the actor=llm glyph attribution and an
arm sublabel when the producing arm is the stub (per SD-2's honesty payload) —
respecting L-C absolutely (REASONS, no score, no percentage, no meter). The full
entry stays in the step trace via the existing toggle. This is PLAN-0080 OQ-1's
surviving idea (a summary above the trace for a non-technical reader) landing on its
intended surface; trace-only would bury Rung 1's demo value behind a toggle.
Data source = the persisted trace entry (rendering reads what the run persisted —
never generates at render time).
**Alternative:** trace-only (cheaper, invisible in the demo beat).
**Why Cray:** the gate panel is the demo's decision moment — what the approver sees
there is presentation vocabulary Cray narrates live.
**RESOLVED/RATIFIED (Cray, 2026-07-21 s156, AskUserQuestion): gate-panel block +
trace** — compact advisory block above Submit (reasons prose, actor glyph, arm
sublabel, NO score) + full entry behind the existing trace toggle.

### SD-5 — Trace kind

**Question:** reuse `llm_inference`, or a NEW kind?
**Recommendation: NEW kind `advisory_recommendation`** — registry row
`{ "label": "Advisory recommendation (shown, never routes)", "cls": "s-info",
"actor": "llm" }` + the `test_trace_kind_labels` tripwire update (PLAN-0080 AC-3
mechanics). Reusing `llm_inference` would make SD-4's panel locate the advisory by
scanning a generic kind shared with unrelated inferences, and Rung 2's
reproducibility story will want to hang model/prompt-hash metadata on THIS kind
specifically. **Honesty wrinkle surfaced, not silently chosen:** the registry maps
kind→actor statically, so the stub arm's entries would also render the llm glyph.
Recommended mitigation: the mandatory `detail.model` arm disclosure (SD-2) + SD-4's
arm sublabel. The stricter PLAN-0080-conservative alternative — actor `"engine"`
until the live arm first ships — is defensible and is Cray's call.
**Why Cray:** the actor glyph is the attribution channel PLAN-0080 built to never
overstate; whether the stub arm may render under the llm glyph (with disclosure) is
exactly that judgment.
**RESOLVED/RATIFIED (Cray, 2026-07-21 s156, AskUserQuestion): NEW kind
`advisory_recommendation`, actor `llm`, with the disclosure mitigation** —
`detail.model` arm disclosure (SD-2) + the SD-4 arm sublabel; registry row + the
`test_trace_kind_labels` tripwire pin updated (PLAN-0080 AC-3 mechanics).

## Acceptance Criteria

- [ ] **AC-1 Offline gate:** full suite green + `mypy --strict services/` +
  `ruff check` / `ruff format --check` clean — CI scope (whole tree), re-baselined at
  execution HEAD (CLAUDE.md §8; offline oracle is the gate).
- [ ] **AC-2 Advisory persisted at run time:** a fresh seeded run
  (`python scripts/seed_operate_demo.py`) parks at `waiting_human` with the advisory
  `ReasoningStep` ALREADY in the persisted trace of the approve step (or the SD-1
  ratified location) — proven by reading the persisted run, not the renderer;
  `detail` carries the producing arm (`model`), grounded reason content from the
  run's own data, and NO numeric confidence field surfaced to the operator (L-C).
- [ ] **AC-3 Never-raise:** with the advisory builder forced to raise (test double),
  the run proceeds byte-identically to baseline — same statuses, same park, same
  audit; the advisory is absent or degraded, never an error step, never FAILED, never
  a divert (economic_impact.py:118-148 contract; orchestrator untouched).
- [ ] **AC-4 No routing delta:** advisory-on vs advisory-off runs are identical in
  everything but the advisory trace entry — same gate reached, same
  `doa_tier_resolved` tier + approver resolution (PLAN-0075 baseline), **byte-identical
  approve-step `audit` payload** vs baseline; the advice writes ONLY to
  `reasoning_trace`, never to `audit`/artifact. This is the L-B fence as a test.
- [ ] **AC-5 Trace-kind registry green:** `tests/api/test_trace_kind_labels.py` passes
  with the SD-5 outcome (new row + tripwire pin updated if a new kind; no change if
  reuse). No unmapped-kind rendering for the advisory entry.
- [ ] **AC-6 Hash discipline (arm depends on SD-1):** under SD-1(b) — a test asserts
  the governance snapshot/hash of ALL touched procedures is byte-identical pre/post
  (parked runs keep resuming). Under SD-1(a) — the demo-reset note is executed and
  verified: parked-run refusal (assert_governance_pin, persistence.py:260-287) is
  CALLED OUT in the PR + runbook, existing parked runs drained/cancelled before
  merge, boot self-seed confirmed re-seeding — never silently discovered.
- [ ] **AC-7 Live UI check (8101 demo, if SD-4 = gate-panel block):** seed → Monitor
  gate panel shows the advisory block (reasons, actor glyph, arm sublabel; NO
  score) above Submit; full trace entry visible via the toggle — **with the
  connection strip reading `LIVE`** (api.js silently serves mock on backend errors; a
  `degraded` strip invalidates the check). `?v=` bumped on every edited asset.
- [ ] **AC-8 L-C conformance:** grep-verified — no confidence number/percentage/meter
  rendered in any operator-facing advisory surface added by this PLAN (the #823
  discipline holds); comments at the render site cite the s74 decision.

## Out of Scope

- ❌ **Any routing effect.** The routing trigger stays the engine-computed
  deterministic verdict; a model signal "MUST NOT decide whether a set escalates"
  (ADR-0019:50-57). Any change letting the advisory route, escalate, pre-approve,
  default a decision, or alter which approver resolves is an **ADR-010 IN-3 reopen**
  and exceeds ADR-0019's scope fence (:77-79, :92-93) — it requires its own explicit
  Cray decision, never lands here.
- ❌ **Rung 2** — AI as a principal in the DOA ladder (band, sampling audit, kill
  switch, SoD binding on the agent). A future PLAN; this PLAN is its substrate only.
- ❌ **Operator-facing confidence numbers/badges/meters** (L-C; PLAN-0035:591-602,
  PR #823). Confidence may exist inside `detail` for audit purposes but is never
  rendered to the operator.
- ❌ **Model/prompt-hash pinning of the advisory** — the known follow-up for Rung 2's
  reproducibility story (a `governance_hash`-style pin extension); one line here, its
  own decision later.
- ❌ **Engine orchestrator changes** — advisory tolerance stays executor-local per the
  ADR-0030 D5 pattern (`orchestrator.py` untouched; the never-raise contract lives in
  the builder/executor seam).
- ❌ **ADR-007 D2 envelope / first-class fields** — trace-only, per the PLAN-0035
  SD-3=(a) standing answer.
- ❌ **Other verticals' factories opting in** (SD-3 guard: constructor-argument
  opt-in; only procurement supplies it in v1).
- ❌ **Live MS-S1 runs as part of this PLAN's gate** — the offline oracle is the gate;
  any live-arm smoke is a separate, Cray-gated host-state event (§8).

## Steps

### Step 0: SD ratification gate

Present SD-1…SD-5 to Cray (AskUserQuestion). No implementation before ratification —
SD-1 decides the wiring shape + whether AC-6 runs its hash-identical or demo-reset
arm; SD-4/SD-5 decide the UI + registry work. Record ratified picks in this PLAN
(per-SD stamps, PLAN-0084 pattern).

**SATISFIED — 2026-07-21 (s156, AskUserQuestion):** all five SDs ratified, every
pick = the draft recommendation (SD-3 folded into the SD-1 question by construction);
resolutions recorded in the per-SD stamps above. AC-6 runs the hash-identical arm;
no amendment content resulted (all steps were drafted contingent on these picks).

### Step 1: Advisory builder module (never-raise)

New module (e.g. `services/engine/procedures/gate_advisory.py`): builds the advisory
`ReasoningStep` from the run's own data at the gate — recommended content per OQ-1's
surviving idea: what is recommended + why THIS tier/approver (resolved ฿ amount vs
the ladder band, breach context, waiver state, quote basis), as short grounded
reasons. Speaks through the `ChatClient` seam per SD-2; the default arm is the
deterministic grounded-template path; `detail` carries `model`/arm disclosure.
**Contract (copied from economic_impact.py:118-148):** never raises — catch all, log
a warning, return `[]`/None; absence never harms the run.
**Verify:** unit tests — content grounded from inputs; raise-injection returns empty;
no numeric confidence in the operator-surfaced fields.

### Step 2: Emission wiring (per SD-1 as ratified)

Under SD-1(b): the ACTION executor's doa_tier gate path (the
`GovernanceActionExecutor` propose branch — locate the exact module at build;
constructed at `run.py:286-290`) gains an optional `advisory_builder` constructor
argument (default None = today's behavior, all other verticals byte-identical);
procurement's `_executors`/factory (`run.py:262-305, :702-715`) supplies it. Emission
happens in the propose path BEFORE the run parks, appending to the approve step's
trace only. Under SD-1(a): instead, add the YAML step between compliance and approve
(+ siblings per SD-3), a per-kind executor stub, and execute the demo-reset arm of
AC-6.
**Verify:** AC-2 (persisted-at-park), AC-3 (never-raise end-to-end), AC-6
(hash-identical test — or reset note), AC-4 baseline-diff test.

### Step 3: Trace-kind registry (per SD-5)

If a new kind: add the `advisory_recommendation` row between the JSON markers in
`trace-kinds.js` + update the `test_trace_kind_labels` set-equality pin (the tripwire
working as designed, PLAN-0080 AC-3). If reuse: assert the advisory entry renders
mapped (no dashed/unknown).
**Verify:** AC-5.

### Step 4: Monitor gate-panel advisory block (per SD-4)

In `view-monitor.js` gate panel (:297-313 area): render the advisory block from the
persisted trace entry (find by kind; data-driven, no hardcoded ids — ui.md) — reasons
prose + actor glyph + arm sublabel; NO score (L-C; cite the s74 decision in a comment
at the render site, the #823 convention). Bump `?v=` tokens.
**Verify:** AC-7 live click-through (strip `LIVE`), AC-8 grep.

### Step 5: Baseline-delta + fence tests

The AC-4 test pair (advisory-on vs off: identical statuses, tier, approver, audit
bytes; delta = the one trace entry) + the AC-3 raise-injection run + the AC-6 hash
test (SD-1(b) arm). These tests ARE the L-B fence in CI — a future change that makes
the advisory route anything turns one of them RED.

### Step 6: Gate, live verification, runbook note

- Full offline gate (AC-1) on the merge-ready branch.
- Live 8101 walkthrough (AC-7): local demo stack only — no MS-S1, no host-state
  change (§8).
- `docs/runbooks/run-oct-demo.md`: short §-note — the advisory block in the approve
  beat, the "strip must read LIVE" check, and (SD-1(a) arm only) the parked-run
  reset procedure. A note, not a rewrite.
- PR referencing PLAN-0085; after merge + Cray confirmation,
  `git mv docs/plans/0085-*.md docs/plans/done/`.

## Verification

How we know it worked, in one line each:
1. AC-2/AC-7: a seeded run parks with real, grounded advice visible at the gate — the
   Rung-1 "ให้เห็นของ" beat exists on the offline arm.
2. AC-4's baseline diff proves the L-B fence: nothing but a trace entry changed —
   same gate, same approver, same audit bytes.
3. AC-3 proves the ADR-0030 D5 posture: killing the advisory cannot touch the run.
4. AC-6 proves fleet safety: parked runs keep resuming (SD-1(b)) or the reset was an
   announced, executed event (SD-1(a)).
5. AC-5/AC-8 keep the attribution + trust-shape disciplines (PLAN-0080, L-C) intact
   under the first llm-actor CONTENT producer.
