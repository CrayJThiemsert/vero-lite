# PLAN-0022: Tiered Decision Routing — tier the grader + wire the deterministic `watch` band to a `gated` human-escalation

**Status:** Draft *(uncommitted; awaiting Cray ratification → Ready for execution. The session-54 dispatch framed the gate as `Proposed → Accepted`; this PLAN uses the template's `Draft → Ready for execution` vocabulary — see Governance note. Number `0022` + scope "Full decision-routing" are Cray G2-approved, 2026-06-11.)*
**Owner:** Claude Code (execution) — drafted by Cowork (Tier-1, ADR-009 D1); Code commits (ADR-009 D2)
**Created:** 2026-06-11
**Related ADRs:** ADR-016 (governed procedure engine — D3 autonomy `auto`/`gated`; `resolve_gated_step`; `step.handler` allowlist — **amended by Step 4**), ADR-010 (LLM reasoning-hook surface — IN-3 confidence advisory; D4 the human-approval gate — **flagged as a POSSIBLE reopen only, Step 4 / SD-2**), ADR-005 (OCT feature-3 / design-partner verticals), ADR-009 (Cowork Tier-1 authoring + commit boundary), ADR-012 (Cowork free-form — D4.3 disclosure at foot)

> **Drafting provenance.** Drafted (uncommitted) by Cowork in Tier-1 governance-authoring mode under ADR-009 D1, off the Code-authored session-54 dispatch (`docs/research/private/2026-06-11-plan0022-tiered-decision-routing-cowork-dispatch.md`) and its grounding design seed (`docs/research/private/2026-06-11-tiered-decision-routing-design-seed.md`). Code reviews + commits via a `docs/*` PR (ADR-009 D2); Cray ratifies. This PLAN **drafts** the design; it implements nothing (see Out of Scope). **Author≠reviewer disclosure (ADR-012 D4.3):** at the foot of this file.

---

## Goal

Make vero-lite's decision surface **tiered** instead of binary. Today the engine fires a deterministic action only on a clear `breach`; everything else is either a bare human task (procedure path) or a no-op (reactive/benchmark path), and the benchmark's single `α` handler probe lumps a *benign* alternative (`inspect`) together with a *dangerous* one (`expedite`/`reroute`). This PLAN turns Cray's two-axis reframe — **(design-time) is the threshold clearly measurable × (runtime) is the data clear or ambiguous** — into an executable design across two surfaces: (1) **tier the benchmark grader** so the handler metric self-distinguishes *canonical* / *acceptable* / *forbidden* picks, and (2) **wire the deterministic `watch` band to a `gated` proposal** — the LLM recommends, a human approves/rejects via the already-shipped `resolve_gated_step` flow — instead of leaving `watch` silent or routing it to a bare "go look" human task. The ambiguity trigger is the **engine-computed `watch` band**, never the LLM's `confidence` field (ADR-010 IN-3). The implementation itself is a later, separate PR that references this PLAN.

### The tiering, in one table

| tier | design-time / runtime regime | who decides | engine behaviour (target) | grader measures |
|---|---|---|---|---|
| **canonical** | threshold clear + data clear (`breach`) | deterministic (`auto`-eligible) | propose/execute the author's `step.handler` | picked the right (canonical) handler |
| **acceptable / escalate** | threshold clear, **data ambiguous** (`watch`) | **LLM proposes → human decides** | a **`gated` proposal**, run suspends at `waiting_human` | did it route to human review **correctly**? + was the proposed handler an *acceptable* alternative? |
| **forbidden** | — (any regime) | never | the dangerous action is never the recommended one | rejected the dangerous action (β `forbidden_keywords` / `forbidden_primary_keys`) |

---

## Fact-pack — verified repo state this PLAN reasons about (read 2026-06-11, HEAD `a6125c1`)

Every claim below was checked against the live repo before assertion (Tier-1 fact-pack rule). Two of them **correct the design seed's framing** and are flagged ⚠ — surfacing cross-file structural divergence is the catch class the dispatch asked for.

1. **The deterministic three-way disposition lives only in the benchmark, not the product engine.** `benchmarks/procedure_baseline/grader.py::classify_disposition` computes `breach`/`watch`/`ok` from `crosses_threshold` + `Scenario.watch_margin` (`benchmarks/procedure_baseline/schema.py`). In `services/engine`, `recommender.crosses_threshold(measured, threshold, direction)` decides **breach only**; there is **no `watch_margin` and no watch band anywhere under `services/engine`** (grep-confirmed). So "the engine computes the watch band" is true **only inside the benchmark grader today**.
2. ⚠ **No shipped deterministic `evaluate` (`judge`) executor.** `services/engine/procedures/` ships exactly one concrete `StepExecutor` — `ActionStepExecutor` (`action_step.py`). The orchestrator (`orchestrator.py`) states executors are "provided by the caller," and the `judge`/`evaluate` step that produces the per-entity `verdict: breach/watch/ok` fan-out key is **not yet implemented as engine code**. The aquaculture `procedures.yaml` `judge` step describes the band only in NL goal text ("watch (4–5)"). **Consequence:** wiring `watch → gated` in the *product* requires a deterministic evaluate executor as a prerequisite (Step 2) — it is not merely "flip a switch."
3. ⚠ **In the product procedure path, `watch` is NOT silent today — it routes to a bare `human_task`.** `verticals/aquaculture/procedures.yaml` routes `where: {verdict: watch}` to a `human_task` (technician visual check) — a human is told to go look, with **no machine recommendation attached**. The design-seed's "today `watch` = silent / no action" is precise for the **reactive recommender + the benchmark** (where `watch` fires no `RecommendedAction`), but **not** for the procedure path. The real change this PLAN proposes is therefore an **upgrade**: from a bare "go look" task to a `gated` **action proposal** the human approves/rejects against a concrete LLM recommendation.
4. **The "ambiguous → human decides" primitives already exist and are wired for `breach`, not `watch`.** A `gated` `action` step only *proposes* (each `ActionRecord` stays `proposed`); `orchestrator._suspends` suspends the run at `waiting_human`; `action_step.resolve_gated_step` applies the human's per-proposal approve/reject (`approve()→execute()` / `reject()`), rewrites the step `output_set`, and persists; a plain `resume_run` then threads it forward. Today the aquaculture `aerate` step uses exactly this — on the **breach** subset.
5. **`step.handler` is deterministic and allowlist-bounded.** `action_step._compose_action` overrides the model's `suggested_handler` guess with the procedure author's `step.handler` (ADR-016 D3), checked against `Agent.allowed.action_handlers` by `orchestrator.validate_runnable`. So the executed handler is **not** a model decision on the procedure path — which is exactly why the benchmark grades the handler as a separate **α probe**, not a β-headline gate (`grader.py` docstring; REPORT § "Handler-determinism finding").
6. **`forbidden` (danger-rejection) is already encoded by the β precision checks, for the action class.** `Expected.forbidden_keywords` asserts the near-miss/dangerous verb (e.g. `expedite`/`reroute`) is **not** in the proposal title; `forbidden_primary_keys` asserts no decoy entity is named. PLAN-0020 REPORT confirms the model avoids the dangerous near-misses (it picked `inspect`/`hold`, never `expedite`/`reroute`). **Consequence (SD-4):** `forbidden` likely does **not** need a brand-new grader tier — it needs to be made *first-class / explicit in reporting*, not invented.
7. **`confidence` is advisory and must not gate.** `LlmJudgment.confidence` (`services/engine/llm/structured.py`) is documented "advisory only (ADR-010 IN-3)". The escalation trigger in this PLAN is the deterministic watch band (fact 1), **not** `confidence`. (PLAN-0020's `reasoning_mode="skip"` lever is out of scope here — see Out of Scope.)

---

## Acceptance Criteria

This is a **drafting** PLAN; the ACs gate the *plan's completeness and correctness*, and (for the implementation PR that later references it) the *design contract* the implementation must satisfy. Implementation-time ACs are tagged **[impl]**.

- [ ] **AC-1 — Tiered grader design.** The PLAN specifies how `grader.classify_disposition` / the α probe distinguish **canonical** vs **acceptable** vs **forbidden** handler picks (replacing the single coarse α), including the concrete `Expected`-schema change, and resolves SD-4 (whether `forbidden` is a new tier or the existing `forbidden_keywords`).
- [ ] **AC-2 — `watch → gated` routing design.** The PLAN specifies the engine change in `services/engine/procedures/` (the prerequisite deterministic `evaluate` executor + routing the `watch` subset to a `gated` proposal) and the **escalation product/UX** (what the human sees and decides at `waiting_human`).
- [ ] **AC-3 — Determinism invariant stated and load-bearing.** The PLAN states explicitly that the escalation trigger is the engine's `watch` band, never `confidence` (ADR-010 IN-3), and that any model-derived ambiguity signal would be an ADR-010 reopen surfaced as an explicit decision (SD-2), never silent.
- [ ] **AC-4 — ADR touch-points identified.** The PLAN names the **ADR-016 amendment** (add the `watch → gated`-proposal path to D3) the implementation PR will reference, and **flags ADR-010 as a *possible* reopen only** under the SD-2 condition (otherwise untouched).
- [ ] **AC-5 — Config-surface decision.** The PLAN decides whether the procedure/ontology YAML needs **new structured fields** (a per-procedure/per-threshold `watch_margin` + the canonical/acceptable/forbidden tier mapping) and specifies them, given that the watch band is NL-only / benchmark-only today (fact 1–2).
- [ ] **AC-6 — Benchmark-scoring design.** The PLAN specifies how the grader scores **"correctly escalated an ambiguous case"** vs **"should have acted deterministically"** vs **"should have stayed silent,"** i.e. how `watch` items move from a deterministic false-positive guard to an LLM-proposes→human-routes path scored for correct escalation — **honoring the B-6 ring-fence** (methodology ratified before any scored run; no bar moves).
- [ ] **AC-7 — Surfaced Decisions complete.** All five design-seed open questions appear as Surfaced Decisions, each either **resolved (with a recommendation + "Cray adjudicates")** or **explicitly deferred**; newly-discovered items (evaluate-executor prerequisite; `human_task` vs `gated`) are surfaced too.
- [ ] **AC-8 [impl] — Determinism test.** The implementation PR proves (a named test) that the `watch → gated` escalation fires from the engine's watch-band math and is **independent of** `confidence` (e.g. identical disposition under varied `confidence`).
- [ ] **AC-9 [impl] — Non-regression of the breach path.** The shipped `breach → gated/auto` aerate flow, the `resolve_gated_step` semantics (reject = continue + record), and the existing β headline / α probe lanes remain byte-for-byte behaviourally intact except where this PLAN deliberately changes them.

---

## Out of Scope

- ❌ **Any implementation.** No engine code, no grader code, no `procedures.yaml`/ontology edits, **no benchmark run**. This PLAN is a plan; the implementation is a later, separate PR that references PLAN-0022 (CLAUDE.md §6 Plan Flow).
- ❌ **Wiring `reasoning_mode="skip"` into the product procedure path.** The PLAN-0020 latency lever and its ADR-010 audit-narrative trade-off are a **separate deferred follow-up** (PLAN-0020 REPORT AC-1e); not touched here.
- ❌ **Wiring `skip` step semantics into the product procedure path** (the open ADR-010 audit trade-off named in STATUS `next_action`) — explicitly excluded per the dispatch.
- ❌ **Reopening ADR-016's primitive shape.** The `Procedure/Step/PipelineRun/Agent` contract is Accepted/fixed; this PLAN *amends D3's routing* (adds a path), it does not redesign the primitive. (B-6 ring-fence: a benchmark finding never reopens ADR-016.)
- ❌ **Moving any benchmark threshold/bar.** The B-3/B-6 ring-fence holds: the benchmark reports, it does not gate; "our stack wins" is the thesis under test, not an acceptance condition.
- ❌ **Vertical-specific procedure authoring** (e.g. choosing energy's watch_margin). The PLAN defines the *config surface*; authoring per-vertical values is downstream.
- ❌ **A model-derived ambiguity signal** (using `confidence` or a model "I'm unsure" to route). Out of scope unless Cray opens the SD-2 ADR-010 reopen; the v1 trigger is the deterministic watch band only.

---

## Steps

### Step 1 — Tier the benchmark grader (canonical / acceptable / forbidden)

**Files (impl PR):** `benchmarks/procedure_baseline/grader.py`, `benchmarks/procedure_baseline/schema.py`, the three `dataset/*.yaml`.

The single α probe (`valid_handlers` membership) is too coarse: it scores `inspect` (benign) and `expedite`/`reroute` (dangerous) identically as "not the canonical handler." Tier it:

- **Schema change (`Expected`).** Replace the flat `valid_handlers: list[str] | None` with a tiered handler key — recommended shape:
  - `canonical_handler: str | None` — the single correct ontology `action_type` (e.g. `start_emergency_aerator`, `restart`, `hold`).
  - `acceptable_handlers: list[str] | None` — benign defensible alternatives (e.g. `inspect`, `increase_water_exchange`) that are *not* wrong, just not canonical.
  - `forbidden` stays expressed by the existing `forbidden_keywords` (title-level) — **not** a new field (see SD-4).
  - Back-compat: keep `valid_handlers` as a deprecated alias for one migration, or migrate the datasets in the same PR (decide in impl; recommend migrate-in-PR — the dataset is small and authored).
- **Grader change (`grade_proposal` / a new tiering helper).** The α probe returns a **three-way classification** instead of a boolean: `canonical` (handler == `canonical_handler`), `acceptable` (handler ∈ `acceptable_handlers`), or `forbidden`/`other` (handler triggers a `forbidden_keywords` hit, or is neither canonical nor acceptable). Report all three counts on the α lane; the β headline is unchanged (entity + action-class + the `forbidden_*` precision checks).
- **Why this is the right cut:** it makes the metric self-explain the PLAN-0020 SD-1 finding (the supply_chain `inspect` divergence was *benign* — `acceptable`, not a miss) **without a human reading the `--dump-json`**, which is exactly the production-fidelity gap Cray named.

**Deliverable:** the tiered `Expected` schema + the three-way α classification spec. (Resolves AC-1; depends on SD-4.)

### Step 2 — Decision-routing: wire the deterministic `watch` band → a `gated` proposal

**Files (impl PR):** `services/engine/procedures/` (new deterministic `evaluate` executor; `action_step.py`; `orchestrator.py` only if the routing key needs it), `verticals/*/procedures.yaml`.

This is the load-bearing engine change. It has a **prerequisite** the design seed did not name (fact 2):

1. **Prerequisite — a deterministic `evaluate` executor.** Add an engine `evaluate` `StepExecutor` that computes the per-entity `verdict` ∈ {`breach`, `watch`, `ok`} from authored `threshold` + `watch_margin` (Step 3 config), reusing `recommender.crosses_threshold` for the breach edge and the benchmark's watch-band math (`floor < value ≤ floor + margin` on the safe side) as the single shared definition. This is what makes the `where: {verdict: watch}` fan-out **deterministic and engine-owned**, satisfying the ADR-010 IN-3 invariant. (Today the verdict key is NL-described and has no shipped engine producer.)
2. **Route the `watch` subset to a `gated` action proposal.** Where the procedure today sends `where: {verdict: watch}` to a bare `human_task`, route it (or add a parallel step) to a **`gated` `action`** whose `step.handler` is the author-declared *escalation* handler. The existing machinery does the rest unchanged: the `ActionStepExecutor` only *proposes* (`gated`), `orchestrator._suspends` parks the run at `waiting_human`, and `resolve_gated_step` applies the human's approve/reject. **No new lifecycle primitive is needed** — only the routing of the watch subset into the existing `gated` path.
3. **Escalation product/UX (`waiting_human`).** At suspension the human reviewer sees, per watch entity: the LLM's proposed `RecommendedAction` (title/description), its `reasoning_trace` (the ADR-010 D3 hybrid trace) and the **advisory** `confidence` (surfaced, not gating — ADR-010 IN-3/D4), and a per-proposal **approve → execute** / **reject → record-and-continue** control (the shipped `resolve_gated_step` contract; reject is not a run failure). The distinction from today's `human_task`: the human decides on a **concrete machine recommendation**, not a bare "go look."

**Surfaced sub-decision (folded into SD-1):** does the `watch` set get a `gated` action **replacing** the `human_task`, or **in addition to** it (propose an action *and* still queue a visual check)? Recommend **replace for v1** (the gated proposal already encodes "human decides"); keep "augment" as a per-procedure authoring option. **Cray adjudicates.**

**Deliverable:** the engine-change spec (evaluate executor + watch→gated routing) + the escalation UX spec. (Resolves AC-2.)

### Step 3 — Config surface: do the tiers + `watch_margin` need new YAML fields?

**Files (impl PR):** `services/engine/procedures/spec.py` (the `Step`/`Procedure` models), `verticals/*/procedures.yaml`; **ontology untouched** (ADR-008 / ADR-016 D2 keep `procedures.yaml` a separate spec layer).

Given fact 1–2 (the watch band is NL-only in `procedures.yaml` and structured only in the *benchmark* dataset), the engine cannot compute the watch band from current config. **Recommendation: YES — add structured fields**, authored per procedure / per threshold:

| field | on | purpose |
|---|---|---|
| `threshold` + `direction` | the `evaluate`/`judge` step (or a per-procedure threshold block) | the breach floor + crash/over semantics (today only `settings.oct_recommend_*` for the reactive path) |
| `watch_margin` | same | the width of the ambiguity band just inside the safe side (the escalate-to-human zone). Absent ⇒ band collapses ⇒ no escalation (preserves today's behaviour) |
| `tiers` (optional) | the `action` step, or the agent | maps canonical / acceptable / forbidden handlers per procedure, mirroring the Step-1 grader tiers so product and benchmark share one source of truth |

Keep the fields **optional** so existing procedures (no `watch_margin`) keep today's behaviour byte-for-byte (AC-9). Surface whether the tier mapping belongs on the `Step`, the `Agent.allowed`, or a new `procedures.yaml` block (recommend the `action` step, beside `handler`). **Cray adjudicates the exact placement** (SD-5).

**Deliverable:** the `spec.py` field additions + a worked `procedures.yaml` example (aquaculture). (Resolves AC-5; ties to SD-5.)

### Step 4 — ADR touch-points

- **ADR-016 (amendment, required).** D3 today: autonomy is an axis of `action` steps; `watch` routes to `human_task`; `gated` = the breach go/no-go. This PLAN adds a **`watch → gated`-proposal routing path** (LLM proposes on the ambiguous band → human decides). That is an **extension of D3**, not a primitive change — surface it as an ADR-016 amendment (or a short follow-on ADR) that the implementation PR references. The `auto`/`gated` model, ceiling, and allowlist are unchanged.
- **ADR-010 (POSSIBLE reopen — flagged, not taken).** As long as the escalation trigger is the deterministic `watch` band, **ADR-010 is untouched** (IN-3 honored; D4 human gate reused verbatim). ADR-010 is reopened **only if** Cray decides a *model-derived* ambiguity signal may influence routing (SD-2) — an explicit decision, never silent. Default recommendation: **do not reopen**; keep the trigger deterministic.

**Deliverable:** the ADR-016 amendment scope + the conditional ADR-010-reopen flag. (Resolves AC-4; ties to SD-2.)

### Step 5 — Benchmark scoring: escalation correctness

**Files (impl PR):** `benchmarks/procedure_baseline/grader.py`, `benchmarks/procedure_baseline/REPORT.md` (methodology section), `dataset/*.yaml`.

Today `watch`/`ok` items are a deterministic false-positive guard: the grader asserts the engine does **not** fire, with **no LLM call** (REPORT § "Deterministic disposition"). Under this model, `watch` items exercise an **LLM-proposes → human-routes** path that the grader scores for **correct escalation**. Three outcomes per item:

| dataset disposition | correct behaviour | grader scores |
|---|---|---|
| `breach` (canonical) | propose/execute the canonical handler deterministically | **acted deterministically** ✓ — the existing β headline + tiered α (Step 1) |
| `watch` (acceptable/escalate) | route to a `gated` proposal (LLM recommends → human decides); proposed handler should be canonical or `acceptable`, never `forbidden` | **escalated correctly** ✓ — a NEW watch-tier check: (a) the item routed to the gated/escalation path, and (b) the proposed handler ∈ {canonical, acceptable} |
| `ok` | no fire | **stayed silent** ✓ — the existing false-positive guard, unchanged |

The new failure modes the grader must name: a `watch` item that **acted deterministically** (over-eager — should have escalated), a `breach` item that **escalated** (under-eager — should have acted), and either firing a **`forbidden`** handler. **Ring-fence (B-6):** this is a **methodology** change, ratified by Cray *before* any scored run (anti-moving-target); this PLAN drafts the methodology only — **no run** (Out of Scope). The watch-tier check is **reported on its own lane**, never folded into the β headline (the same lane-isolation discipline as α).

**Deliverable:** the three-way scoring spec + the new watch-tier lane + the ring-fence note. (Resolves AC-6; ties to SD-3.)

---

## Surfaced Decisions

The five design-seed open questions (seed §5) are the backbone. Each carries a recommendation; **Cray adjudicates** all of them (Tier-1 rule #8 — surface, do not silently choose). Two newly-discovered items follow.

| # | Decision | Options | Recommendation (Cray adjudicates) |
|---|---|---|---|
| **SD-1** | Should `watch` fire a `gated` proposal instead of staying silent / a bare `human_task`? What is the UX? | (a) `gated` proposal replaces the `human_task`; (b) `gated` proposal **+** keep the visual-check `human_task`; (c) leave `watch` as today | **(a)** for v1 — the gated proposal already encodes "human decides" and shows a concrete recommendation; keep (b) as a per-procedure authoring option. UX = `waiting_human` + per-proposal approve/reject (Step 2.3). |
| **SD-2** | Is the trigger purely the deterministic `watch` band, or is there a role for a (deterministic) data-quality / missingness signal too? | (a) watch band only; (b) watch band **+** a deterministic data-quality/missingness signal; (c) allow a model-derived signal (⇒ **ADR-010 reopen**) | **(a)** for v1. (b) is a clean future extension and **stays deterministic ⇒ no ADR-010 reopen**. (c) is explicitly an ADR-010 reopen — **do not take silently**; default no. |
| **SD-3** | Grader: how to score "correctly escalated" vs "should have acted deterministically" vs "should have stayed silent"? | The three-way scheme in Step 5 vs a coarser pass/fail | **Adopt the three-way scheme** (Step 5 table) on its own watch-tier lane; ring-fenced methodology, ratified before any run. |
| **SD-4** | Does `forbidden` need a first-class grader tier, or does β `forbidden_keywords` already cover danger-rejection? | (a) no new tier — reuse `forbidden_keywords`/`forbidden_primary_keys`; (b) add a dedicated `forbidden_handlers` field | **(a)** — fact 6 + PLAN-0020 REPORT show the action class is already covered; make it *explicit in reporting*, do not invent a tier. (b) only if a future vertical needs handler-level (not verb-level) danger lists. |
| **SD-5** | Per-procedure config: do the tiers + `watch_margin` need new YAML fields, and where? | (a) add optional `threshold`/`watch_margin`/`tiers` to the `Step` (beside `handler`); (b) put them on `Agent.allowed`; (c) a new `procedures.yaml` block | **(a)** — co-locate with the `evaluate`/`action` step; keep optional for byte-for-byte back-compat (AC-9). Ontology stays untouched (ADR-016 D2). |
| **SD-6** *(newly surfaced)* | The deterministic `evaluate`/`judge` executor does not exist in the engine yet (fact 2) — it is a **prerequisite** for any `watch → gated` wiring. Build it in this work or as a pre-step? | (a) include the evaluate executor in the same implementation PR; (b) split it into a predecessor PR | **(a)** — it is small and tightly coupled to the watch-band config (Step 3); splitting adds a handoff with little benefit. Flag the dependency clearly in the impl PR. |
| **SD-7** *(newly surfaced — fact-pack correction)* | The design seed says "today `watch` = silent / no action," but the procedure path routes `watch → human_task` (fact 3). Confirm the framing so the impl PR targets the right baseline. | n/a — a clarification | Treat "silent / no action" as accurate for the **reactive + benchmark** path only; the **procedure** baseline is a bare `human_task`, and the change is an **upgrade** to a `gated` proposal. Recorded so Code doesn't implement against the wrong baseline. |

---

## Verification

How we know the PLAN (and later the implementation) is right:

1. **PLAN-level (this artifact, pre-commit):** all five dispatch coverage areas present (grader tiering / decision-routing / ADR touch-points / config surface / benchmark scoring); the five seed OQs all appear as SDs; the determinism invariant (trigger = watch band, not `confidence`) is stated and load-bearing; the B-6 ring-fence and "drafting-only" boundaries are explicit. Fact-pack: every code/ADR/path citation verified against HEAD `a6125c1` (see Fact-pack section).
2. **Impl-level (the later PR, for reference):** AC-8 (determinism test — escalation independent of `confidence`); AC-9 (breach-path + `resolve_gated_step` non-regression; full suite green); the new watch-tier grader lane runs on its own and never contaminates the β headline; a `watch_margin`-absent procedure behaves byte-for-byte as today.
3. **Governance:** Cray ratifies (Draft → Ready for execution / `Proposed → Accepted`); Code R2-reviews the fact-pack and commits via a `docs/*` PR (ADR-009 D2). The ADR-016 amendment (Step 4) merges before the implementation PR (CLAUDE.md §8 "ADRs merged before related implementation").

---

## References

- **Dispatch + grounding:** `docs/research/private/2026-06-11-plan0022-tiered-decision-routing-cowork-dispatch.md` (Code-authored brief, session 54); `docs/research/private/2026-06-11-tiered-decision-routing-design-seed.md` (Cray's two-regime observation + the 5 OQs).
- **ADRs:** `docs/adr/0016-governed-procedure-engine.md` (D2 primitive, D3 autonomy `auto`/`gated` + `step.handler` allowlist + the "Morning Pond Health Round" worked example where `watch → human_task`); `docs/adr/0010-llm-reasoning-hook-surface.md` (D4 human-approval gate; D5 + **IN-3 confidence advisory, never gates**); `docs/adr/0009-cowork-tier1-tier-topology.md` (D1 authoring / D2 commit boundary); `docs/adr/0012-cowork-second-freeform-tier.md` (D4.3 disclosure).
- **Code sites:** `benchmarks/procedure_baseline/grader.py` (`classify_disposition`, `grade_proposal`, the β headline + α probe + `forbidden_*` checks); `benchmarks/procedure_baseline/schema.py` (`Disposition`, `Expected`, `Scenario.watch_margin`, `valid_handlers`); `services/engine/procedures/action_step.py` (`ActionStepExecutor`, `resolve_gated_step`, `_compose_action`); `services/engine/procedures/orchestrator.py` (`_suspends`, `_resolve_input` verdict fan-out, `execute_steps`); `services/engine/procedures/spec.py` (`Step`/`Procedure`/`Agent`, `Autonomy`); `services/engine/recommender.py` (`crosses_threshold`, `approve`/`reject`/`execute`, `settings.oct_recommend_threshold` — no `watch_margin`); `services/engine/llm/structured.py` (`LlmJudgment.confidence` advisory; `reasoning_mode`); `verticals/aquaculture/procedures.yaml` (the live `judge → verdict` fan-out; `watch → human_task`; `breach → gated`).
- **Prior PLAN:** `docs/plans/done/0020-procedure-tuning-latency-precision.md` + `benchmarks/procedure_baseline/REPORT.md` (§ "SD-1 implication" — the deferred tiered-handler-grading follow-up this PLAN renders; the α-coarseness finding; the B-6 ring-fence).

---

## Implementation Notes

For Code / the implementation PR. Cowork has no commit authority (ADR-009 D2); Code reviews + commits this draft and the ADR-016 amendment. Per K-1, Cowork could not run `validate_handoff.py` on the companion completion handoff; that handoff records the mental-validation substitute and flags the gap. AI-assisted per CLAUDE.md §8 (noted in the commit body, never as `Co-Authored-By`, per §7).

- The **determinism invariant** (AC-3) is the single most important constraint: if any future change lets `confidence` or a model "I'm unsure" influence routing, that is an **ADR-010 reopen** (SD-2 option c) and must be raised explicitly.
- **SD-6** (the missing deterministic evaluate executor) is a real prerequisite the design seed did not surface — do not schedule the `watch → gated` wiring without it.
- **SD-7** corrects the baseline framing — the procedure-path baseline is a bare `human_task`, not silence.

### Author≠reviewer disclosure (ADR-012 D4.3)

This PLAN was **authored** by Cowork (Tier-1) directly from the Code-authored dispatch + design seed; it was **not** separately deliberated in a Cowork free-form (Tier-1b) session, so the specific self-deliberation risk D4.3 targets is low here. However, per the spirit of D4.3: the two fact-pack corrections (SD-7 / fact 3) and the newly-surfaced prerequisite (SD-6 / fact 2) are Cowork's own findings against the dispatch's framing — they have **not** been independently reviewed by another tier. **Code's R2 review + Cray's ratification are the remaining independent checks.** Cowork recommends Code specifically re-verify facts 2 and 3 (the no-shipped-`evaluate`-executor claim and the `watch → human_task` procedure-path baseline) against HEAD before committing, since the PLAN's scope (notably SD-6) turns on them.
