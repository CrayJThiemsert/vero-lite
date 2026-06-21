# PLAN-0035: Governed action verify+reshape build (ADR-0022 member (b))

**Status:** Draft
**Owner:** both (Cowork/Tier-1 authors this PLAN; Code commits + executes per ADR-009 D1/D2)
**Created:** 2026-06-22
**Related ADRs:** ADR-0022 (Accepted — D2 names **member (b)** verify+reshape; D3 = α one construct; **"(a) is a specific instance of (b)"**; **THIS PLAN builds member (b)**); ADR-0021 (the "classify, don't synthesize" lineage extended here); ADR-007 (D2 `RecommendedAction` envelope — generalised, not broken); ADR-010 (D5 LLM-backed `recommend()`; **IN-4 deterministic fail-safe — not regressed**); ADR-011 (earmarked audit framework — trace interplay **flagged, not designed**); ADR-016 (the governed procedure engine — the area member (b) lands in; it **carries no verify/reshape clause today**, the gap A1 fills); ADR-009 D1/D2 (Cowork drafts, Code commits); ADR-012 D4.3 (author≠reviewer disclosure); ADR-013 (Cowork = advisory governance drafter)
**Related Plans:** PLAN-0030 (member (a) entity-resolution build — **the pattern this mirrors**); PLAN-0027 / PLAN-0028 (the **D-6 contamination guard** — the binding boundary); PLAN-0019 (the procedure-baseline harness + arm (a)); PLAN-0006 (§6.6 the LLM path + the retained deterministic fail-safe)

> **Disclosure (ADR-012 D4.3).** The scope, the §B-3 target decomposition, and
> the code-surface fact-pack originate in **Code's** session-71/72 investigation
> (the A2 equal-rubric re-grade + the §B-3 residual decomposition + this session's
> Explore map) and were handed to Cowork in the session-72 dispatch
> (`.claude/handoffs/session-72/2026-06-22-0223-code-cowork-a1-verify-reshape-plan0035-dispatch.md`).
> This PLAN is **drafted (uncommitted) by Cowork** (Tier-1, ADR-009 D1). The
> construct, the gap evidence, and the build scope were **originated in Code's
> dispatch + ADR-0022 (Accepted)**, not in a Cowork free-form self-deliberation —
> so this is **not** an ADR-012 D4.3 self-deliberation case (no Cowork opinion is
> silently promoted; the independent-deliberation check is intact). The
> independent reviewers are **Code at PR review/commit** + **Cray at ratification
> of the SDs**. Cowork re-verified every cited code line / file / symbol against
> the live repo this session (fact-pack-first, ADR-009 D1 Tier-1 rule #4); see the
> **fact-pack note** in §"The gap + the anchors" on the post-PLAN-0030 line-number
> shift.

---

## Goal

Build the **verify+reshape slice (ADR-0022 D2 member (b))** as a coherent mirror
of member (a) (entity resolution, PLAN-0030). Today the governed LLM recommend
path trusts the model's **prose** to express the corrective action: in
`_compose_llm_record` (`services/engine/recommender.py:140-174`) the governed
`RecommendedAction` carries the model's `title` / `description` verbatim
(`:166`/judgment fields) alongside the structured `suggested_handler` (`:169`).
When the model **selects the correct action in the structured handler** but
**frames the prose as a "breach assessment" that omits the action verb**, the
governed envelope is **internally inconsistent** — its human- and
consumer-facing prose does not state the action its structured handler names.
This PLAN closes that gap on the **LLM recommend path only**: before the governed
record is trusted, **verify the proposal's prose expresses the corrective action
named by the resolved structured handler**, and on an inconsistency **reshape**
the governed envelope so it authoritatively carries that action (surfaced from the
resolved handler, never fabricated) **plus a resolution-outcome trace**, so a
downstream consumer trusts the **structured action**, not model prose. It is the
**same "classify, don't synthesize" move** member (a) made for entity *identity* —
the governed record is reshaped against a declared contract rather than trusting
the model's free text. Member (a) already verifies/reshapes *identity*; member (b)
verifies/reshapes the *action expression*. The procedure-engine step-to-step
"reshape to the **next step's** contract" seam stays **forward-declared, NOT built
here** (SD-2).

## Source of truth — ADR-0022 (Accepted 2026-06-18; stated, not re-opened)

The construct **and** its framing are ratified. This PLAN builds member (b); it
does **not** re-decide or re-ratify ADR-0022:

- **D2 member (b)** (`docs/adr/0022-governed-entity-resolution.md:124-128`):
  *"Verify an LLM step's output for semantic consistency against that step's
  requirement, and reshape it to the next step's contract — the governance
  capability arm (c) (naive RAG) structurally lacks."*
- **"(a) is a specific instance of (b)"** (`:130-134`): entity resolution
  **verifies** the emitted identity against a declared contract (the object
  universe) and **reshapes** an unresolved reference into a governed fall-back.
  Member (b) generalises that discipline to the emitted **action**.
- **D3 = α** (`:136-147`): one construct housing both members; member (b) is the
  second member of the same "govern emitted output against a declared contract"
  discipline — **no new ADR** (SD-4).
- **D-6 / Fork-3 = BINDING boundary** (`:190-198`): verify+reshape is a
  governed-product capability; it must **never** bleed into the arm-(c) naive-RAG
  baseline (Out of Scope; AC-6).

## The gap + the anchors (live code, re-verified session 72)

> **Fact-pack note (line-number shift).** The dispatch's `recommender.py`
> citations (`_compose_llm_record` at `:139-174` / hook at `:160`; `recommend()`
> at `:177-217`) predate **PLAN-0030 shipping member (a)** (#365). Member (a)
> added two parameters to `_compose_llm_record` and a resolution call inside
> `recommend()`, so the live line numbers have moved. All anchors below are
> **re-verified against the live repo this session** (`recommender.py` is the
> post-member-(a) form). The *substance* — the structured handler holds the
> action, the prose may omit it — is unchanged and dump-verified (§B-3).

### The §B-3 target evidence (the 5 prose-omission cases)

`benchmarks/procedure_baseline/REPORT.md:922-933` (the A2 equal-rubric residual
decomposition, handler-verified from each dump's `suggested_handler`):

- **5 of 7 chose the CORRECT action** — `start_emergency_aerator`,
  `probe_correct=True` — **aqua-007 / 014 / 028 / h03 / h06**. The action is
  present in the **structured `suggested_handler` field**, but the proposal prose
  was framed as a *"DO breach assessment"* that **never states the verb** in
  title / description / rationale, so the **prose-only `action_keywords` check**
  (`benchmarks/procedure_baseline/grader.py:260-267` — a substring search of
  `title\ndescription\nrationale`, reads **no** structured handler) missed it.
  **The action lives in the structured handler the prose check does not read.**
  ⇒ **the textbook member-(b) target.**
- **2 of 7 are genuine action-selection errors** — `increase_water_exchange`,
  `probe_correct=False` — **aqua-017 / h05** (true wrong-action **2/40**).
  Member (b) must **NOT** falsely rescue these: verify is against the *structured
  handler*, and for these two the handler **itself** is wrong, so the reshaped
  envelope faithfully reflects a wrong selection (a wrong handler stays wrong —
  AC-5, the anti-regression invariant).

### Where member (b) reads / verifies / reshapes (live anchors)

- `services/engine/recommender.py:140-174` — `_compose_llm_record`; **`:166`**
  `reasoning_trace=build_llm_reasoning_trace(...) + resolution_steps` (member (a)'s
  trace merge — the same seam member (b)'s trace joins), **`:168`**
  `affected_entities=affected_entities` (member (a)'s governed-resolved list),
  **`:169`** `suggested_handler=judgment.suggested_handler` (**the structured
  action — the declared contract member (b) verifies the prose against**),
  **`:162-167`** `title`/`description` from the model judgment (**the prose that
  may omit the action**).
- `services/engine/recommender.py:177-216` — `recommend()` (async); **`:199-201`**
  the member-(a) `resolve_affected_entities(...)` call, **`:202`** the
  `_compose_llm_record(...)` call (**where member (b) plugs in, exactly as member
  (a) did**), **`:203-216`** the IN-4 fail-safe `except` that falls back to
  `_rule_recommend` and **never raises into the runtime loop**.
- `services/engine/recommender.py:219-289` — `_rule_recommend`; **`:275-279`** its
  title/description **already state the action** and **`:284`**
  `suggested_handler="echo"` — the deterministic path is **already internally
  consistent**; member (b) hooks the **LLM path only** (do not regress — AC-7).
- `services/engine/structured.py:85-108` — `LlmJudgment` (what the model emits
  pre-governance): `title` `:85`, `description` `:86`, `rationale` `:87-91`,
  `suggested_handler` `:103-105`; **`:111-125`** `_judgment_schema` **enum-binds
  `suggested_handler` to the vertical's registered handler names** — so the
  structured handler is an **allow-listed, declared** value (the contract member
  (b) trusts), not free text.
- `services/engine/actions.py:42-63` — `RecommendedAction` (the ADR-007 D2
  envelope; `reasoning_trace` `:50`, `affected_entities` `:52`, `suggested_handler`
  `:53`, `handler_payload` `:54`); `:20-24` `ReasoningStep` (the trace step shape);
  `:33-39` `AuditMetadata` ("expanded in future audit-framework ADR" — **not**
  designed here, D-3 / ADR-011).

### Member (a) template — mirror this (live anchors)

- `services/engine/entity_resolution.py:164-209` — `resolve_affected_entities`
  (the verify/reshape-per-item loop: verify against the declared universe →
  keep-canonical or reshape-to-anchor → trace); **`:125-161`** `_resolution_step`
  → `ReasoningStep(kind="entity_resolution", …)` (the minimal machine-readable
  trace shape member (b)'s `action_verification` trace mirrors); **`:75-90`**
  `event_subject_ref` (the shared deterministic anchor); **`:62-72`**
  `normalize_entity_key` (recover-only, never-invent — the discipline member (b)'s
  reshape mirrors: surface only, never fabricate).
- Integration: `recommender.py:40-41` (import), `:199-202` (the call + compose
  seam). PLAN-0030 build + ACs: `docs/plans/done/0030-governed-entity-resolution-build.md`
  (the AC shape, the SD-1 deferred-field pattern `:112-122`, the offline-test
  contract).
- Test template: `tests/services/engine/test_entity_resolution.py:1-31` (offline
  fakes — `_FakeAdapter` `:39-60` + a fake `ChatClient`; no live Ollama, no
  host-state) — the harness member (b)'s tests reuse.

### Procedure-engine seam (SD-2 forward-pointer — NOT built here)

- `services/engine/procedures/orchestrator.py:59-72` (`StepOutcome.output` —
  threaded into the next step as its input set), `:90-95` (`StepExecutor.execute`
  Protocol — where a between-steps verify+reshape stage would hook), `:113-159`
  (`validate_runnable`; the `step.handler` allowlist check `:154-158`).
- `services/engine/procedures/action_step.py:113-144` (`_compose_action`; **`:140`**
  `suggested_handler=handler` = the procedure author's declared, allowlist-bounded
  `step.handler` — **not** the model's guess; **`:139`** `affected_entities=[_loop_entity_ref(event)]`)
  — the procedure-path analogue of `_compose_llm_record`. This is the literal
  "reshape to the **next step's** contract" surface (SD-2 (b)); the broader
  ADR-016 generalisation, named as a forward-pointer.

## Acceptance Criteria

- [ ] **AC-1 — Action-consistency verify on the LLM path (the construct).**
      Before the governed `RecommendedAction` is trusted (at the
      `_compose_llm_record` seam, `recommender.py:202`), the proposal is
      **verified** for semantic consistency between its **prose**
      (title/description/rationale) and the **corrective action named by the
      resolved structured handler** (`judgment.suggested_handler`, the
      enum-bound declared contract). The verify mechanism is **SD-1** (lean:
      deterministic, from the structured handler — no new model call). `[impl]`
- [ ] **AC-2 — A consistent proposal is kept unchanged.** When the prose already
      expresses the action the structured handler names, the governed envelope is
      **kept as-is** (outcome `consistent`); the verify is a no-op beyond emitting
      the trace (AC-4). `[impl]`
- [ ] **AC-3 — An inconsistent proposal is reshaped from the resolved handler +
      traced (never fabricated).** When the prose **omits / does not express** the
      action the structured handler names (the 5 §B-3 cases), the governed
      envelope is **reshaped** so it **authoritatively carries the corrective
      action surfaced from the resolved structured handler** (the reshape target +
      shape is **SD-3**; lean: a structured verified-action assertion + a
      normalized action statement, envelope-compatible), **and** a
      resolution-outcome trace step records the inconsistency and the reshape.
      The action is **surfaced from the already-selected, allow-listed
      `suggested_handler`** — **never invented** (the anti-hallucination invariant,
      CLAUDE.md §8; mirrors member (a)'s never-invent). `[impl]`
- [ ] **AC-4 — Minimal, structured verify-outcome trace.** Each proposal's
      outcome (`consistent` | `reshaped` | `skipped`) is recorded as a
      `ReasoningStep` (`kind="action_verification"`) appended to
      `RecommendedAction.reasoning_trace` (the same merge seam member (a) uses,
      `recommender.py:166`), with **machine-readable** `detail` (the structured
      handler, the verify outcome, and on reshape the surfaced action). The trace
      lands in `reasoning_trace` **only**; `AuditMetadata` is **not** designed here
      (D-3 / ADR-011). `[impl]`
- [ ] **AC-5 — No false rescue of a genuine wrong-action (anti-regression,
      BINDING).** When the structured handler is itself the **wrong** action
      (aqua-017 / h05, `increase_water_exchange`), member (b) **faithfully
      reflects the wrong selection** — verify is against the structured handler,
      so a wrong handler stays wrong; member (b) is **not** an action-*selection*
      improver. An offline test pins that a wrong-handler proposal is **not**
      silently corrected to a right action. `[impl]`
- [ ] **AC-6 — D-6 contamination boundary (BINDING non-goal).** The verify+reshape
      lives in the **governed-product recommend path only**. **No** verify /
      reshape / governance logic is added to the arm-(c) naive-RAG baseline
      (`benchmarks/procedure_comparison/`); **no** cross-import between
      `benchmarks/` and the new `services/` verifier in either direction
      (asserted by a test, as member (a) does for its normalizer). `[impl]`
- [ ] **AC-7 — The envelope + the deterministic fail-safe are not broken.** The
      ADR-007 D2 `RecommendedAction` shape stays backward-compatible (any field
      added under SD-3 is **optional with a default**); the `LlmJudgment`
      sub-schema the model emits is **not** forced to carry a verify-owned field;
      `_rule_recommend` (`recommender.py:219-289`) behaviour is **unchanged** (it
      is already internally consistent — `:275-279`/`:284`); a verify/reshape
      error **propagates** to the `recommend()` `except` → `_rule_recommend`
      (ADR-010 IN-4 / PLAN-0006 §6.6 intact, not swallowed). `[impl]`
- [ ] **AC-8 — Quality bar (CLAUDE.md §8), contract-covering, offline.** Type
      hints + tests + **ruff clean + `mypy --strict` clean**. Tests cover the
      **contract**, fully **offline** (fake `ChatClient` / fixed judgments; no live
      Ollama, no host-state): (i) a **consistent** proposal kept unchanged + a
      `consistent` trace; (ii) an **inconsistent** proposal (prose omits the verb,
      handler correct) → reshaped from the resolved handler + a `reshaped` trace —
      the 5-case shape; (iii) the **wrong-handler negative** (AC-5) — not rescued;
      (iv) a **null/unallowed handler** → fail-safe skip + a `skipped` trace, no
      fabrication; (v) a verify/reshape error → the deterministic fail-safe
      (IN-4 intact); (vi) the **D-6** no-cross-import assertion (AC-6); (vii) the
      full `uv run pytest -q` suite stays green (baseline stated at execution). `[impl]`

## Out of Scope

- ❌ **The procedure-engine step-to-step "reshape to the next step's contract"
  seam** — forward-declared only (SD-2 (b); `orchestrator.py:90-95` /
  `action_step.py:113-144`). PLAN-0035 = the **recommend-time** slice (the 5 A2
  cases), mirroring member (a)'s recommend-path-only scope.
- ❌ **Improving action *selection*** — member (b) verifies/reshapes the
  *expression* of the action the model already selected (in the structured
  handler); it does **not** change which handler the model picks. The 2 genuine
  wrong-action cases (aqua-017/h05) stay wrong (AC-5).
- ❌ **Touching / regressing the deterministic fail-safe** (`recommender.py:219-289`)
  — already internally consistent; behaviour unchanged (AC-7).
- ❌ **Leaking verify/reshape into the arm-(c) naive-RAG baseline** — the D-6
  contamination guard (BINDING; AC-6).
- ❌ **Fixing the benchmark grader's prose-only `action_keywords` check to read
  `suggested_handler`** — that is a **measurement-correctness** matter, **NOT** the
  moat capability (SD-5); scoped out here (or noted as a separate aside) so the
  engine work is not mistaken for teaching-to-the-test.
- ❌ **Designing the audit framework / expanding `AuditMetadata`** (ADR-011
  earmarked) — emit a **minimal** trace only; flag the interplay (D-3).
- ❌ **A new ADR or an edit to the Accepted ADR-0022** — PLAN-only (SD-4); ADR-0022
  D2 already frames member (b). (Only if SD-1 lands a fork ADR-0022 does not cover
  would a **one-line** ADR-0022 amendment be needed — a separate Cowork-drafted,
  G1-gated edit; flag, do not apply inline.)
- ❌ **Vertical #3/#4, UI work, NL-query** — PLAN-0035 is the **engine slice only**.

## Steps

Ordered, each small and reviewable (verify helper → reshape → trace → wire →
contract shape → tests → gate → handback). Mirrors PLAN-0030's step shape.

### Step 1 — The consistency-verify helper (in `services/`)

Add a small **deterministic** verifier in `services/engine/` (e.g. a new
`action_verification.py`, or a private helper beside the recommender — Code's call)
that, given the proposal prose (title/description/rationale) and the resolved
structured `suggested_handler`, decides whether the prose **expresses** the action
the handler names. Implements **SD-1** (lean: deterministic — derive the handler's
action lemma(s) from the registered handler name / its ontology `action_type` and
check prose expression; **no model call**). **Recover-only / never-invent**: it can
only detect omission, never invent an action. **Do NOT import** the benchmark
grader (`benchmarks/`) — that would breach D-6 (AC-6). Unit-test a positive (prose
states the action → consistent) + a negative (prose omits it → inconsistent).
(AC-1, AC-6, AC-8) `[impl]`

### Step 2 — Reshape from the resolved handler (SD-3)

On an inconsistency, **reshape** the governed envelope so it authoritatively
carries the corrective action **surfaced from the resolved `suggested_handler`**
(the reshape output contract is **SD-3**; lean: a structured verified-action
assertion + a normalized action statement, ADR-007 D2-compatible). **Never
fabricate** — surface only the already-selected, allow-listed handler's action.
On a **null / unallowed** handler, **skip** (no reshape) and trace the gap (fail
safe). (AC-3, AC-7) `[impl]`

### Step 3 — Verify-outcome trace step

Append a `ReasoningStep(kind="action_verification", …)` whose `detail` records the
structured handler, the outcome (`consistent` | `reshaped` | `skipped`), and on
reshape the surfaced action. Mirror `_resolution_step` (`entity_resolution.py:125-161`).
The trace lands in `reasoning_trace` only; `AuditMetadata` is **flagged, not
designed** (D-3). (AC-4) `[impl]`

### Step 4 — Wire into the LLM path (async-correct, IN-4-safe)

Hook the verify+reshape at the `_compose_llm_record` seam (`recommender.py:202`),
exactly where member (a)'s `resolve_affected_entities` plugged in (`:199-201`).
Pass the verified/reshaped fields + the verify trace step into the composed record
and **merge the trace** into the same `reasoning_trace` seam member (a) uses
(`:166`). **Keep the IN-4 fail-safe intact** — a verify/reshape exception must fall
through the `recommend()` `except` (`:203-216`) to `_rule_recommend`, never raise
into the loop. (AC-1, AC-4, AC-7, AC-8) `[impl]`

### Step 5 — Reshape output contract (implements SD-3)

Implement the contract decided in **SD-3**: the trace `ReasoningStep` + reuse of
existing structured fields is the default (no envelope change). **If** Cray/Code
approve an optional new envelope field (e.g. a `verified_action` marker), add it
**backward-compatibly** (`Optional`, default `None`) **without** forcing it into
the `LlmJudgment` model schema the LLM emits (mirrors member (a) SD-1 / the
deferred `EntityRef.resolution` field). (AC-3, AC-7) `[impl]`

### Step 6 — Offline tests (the contract)

Add offline tests (fake `ChatClient` / fixed `LlmJudgment`s — extend the patterns
in `tests/services/engine/`; no live Ollama, no host-state): the consistent
no-op; the inconsistent → reshape (the 5-case shape); the **wrong-handler
negative** (AC-5, not rescued); the **null/unallowed-handler skip**; a
verify/reshape error → deterministic fail-safe; the **D-6 no-cross-import**
assertion. Assert on the returned envelope + trace, never on incidental shape
(Lesson #7 §3). (AC-2, AC-3, AC-5, AC-6, AC-8) `[impl]`

### Step 7 — Gate + suite green

`ruff` + `mypy --strict` clean; full `uv run pytest -q` green against the current
baseline (state it at execution). (AC-8) `[impl]`

### Step 8 — Handback → Code commits + executes

Hand the uncommitted draft path back to Code. Code reviews, commits this PLAN via
a `docs(plans):` chore PR (ADR-009 D2; CLAUDE.md §7), executes member (b) on a
`feat/*` branch + PR (**gated on ADR-0022 Accepted — satisfied**), reconciles
`docs/STATUS.md`, then on completion `git mv docs/plans/0035-*.md docs/plans/done/`.

## Verification

- **Construct (AC-1/AC-2/AC-3):** offline tests show (i) a consistent proposal
  kept unchanged + a `consistent` trace; (ii) an inconsistent proposal (prose
  omits the verb, structured handler `start_emergency_aerator`) reshaped to
  authoritatively carry the action + a `reshaped` trace — the 5-case shape.
- **Anti-regression (AC-5):** a wrong-handler proposal (`increase_water_exchange`,
  the aqua-017/h05 shape) is **not** rescued — the governed envelope reflects the
  wrong selection; member (b) does not improve selection.
- **Never-fabricate / fail-safe (AC-3/AC-7):** a null/unallowed handler → a
  `skipped` trace, no invented action; a verify/reshape error routes to
  `_rule_recommend` (IN-4 intact).
- **D-6 (AC-6):** a grep/AST check shows **no** cross-import between `benchmarks/`
  and the new `services/` verifier; the arm-(c) baseline is unchanged.
- **Envelope (AC-7):** ADR-007 D2 shape backward-compatible; the `LlmJudgment`
  schema is not forced to carry a verify field; `_rule_recommend` untouched.
- **Gate (AC-8):** `ruff` + `mypy --strict` clean; `uv run pytest -q` green.
- **Reports-not-gates / no host-state run.** The build + tests are
  offline-deterministic; the offline oracle is the acceptance gate. The §B-3
  benchmark lift on the 5 cases is the **demonstration** (B-3/B-6
  reports-not-gates), **not** an acceptance condition; any live MS-S1 re-score is
  **host-state / Cray-gated / not a gate** (CLAUDE.md §8; Lesson #15).

## Surfaced decisions (SD-N) — for Cray to adjudicate

State each as an option set with a recommendation; **Cray adjudicates** (the
PLAN-0030 / PLAN-0034 SD pattern). LOCKED facts (§"Source of truth") are settled.

- **SD-1 — The VERIFY mechanism (the meaty one). [Cowork recommends: (a)
  deterministic, from the structured handler.]**
  *Question:* how does the engine check the proposal expresses the step's required
  corrective action?
  (a) **Deterministic, from the structured handler** — the correct action already
  lives in the enum-bound `suggested_handler` (`structured.py:103-105`/`:111-125`);
  verify = "does the prose express the action this allow-listed handler names",
  reshape = surface that structured handler's action into the governed contract so
  downstream trusts it (not the prose). No new model call.
  (b) **LLM-judge semantic-equivalence** — a model call asking "does this proposal
  semantically express `<required action>`?". ⚠ **No LLM-judge / semantic-equivalence
  helper exists in the repo today** (Code Explore-confirmed; Cowork did not find one
  either) — this introduces a new helper **and** a host-state / cost / latency
  surface, and would make the acceptance gate non-deterministic.
  (c) **Hybrid** — deterministic structured check primary, LLM-judge only on
  ambiguity.
  *Cowork recommendation:* **(a)** — the §B-3 evidence is that the structured
  handler **already holds the right answer**, so the gap is **prose-trust**, not a
  missing semantic capability; (a) keeps the offline-deterministic gate (AC-8) and
  dodges a host-state dependency, and it is the exact mirror of member (a)'s
  "classify/verify against a declared contract, don't synthesize." (b)/(c) are the
  honest "richer semantic verify" alternative if Cray wants future-proofing beyond
  the action-lemma check — but they trade away the deterministic gate.

- **SD-2 — The HOOK point / scope. [Cowork recommends: (a) recommend-time only,
  procedure-step seam as a forward-pointer.]**
  *Question:* where does member (b) hook?
  (a) **Recommend-time only** — the A2 cases are single-step action proposals; hook
  at `_compose_llm_record` (`recommender.py:202`), exactly where member (a) plugged
  in.
  (b) **Also the procedure-engine step-to-step seam** — `orchestrator.py`
  `StepExecutor` (`:90-95`) / `StepOutcome` (`:59-72`) / `action_step._compose_action`
  (`:113-144`), the literal "reshape to the **next step's** contract."
  *Cowork recommendation:* **(a)** — scope **recommend-time first** (it closes the
  5 §B-3 cases and mirrors member (a)'s recommend-path-only scope); **name the
  procedure-step seam as a forward-pointer** (the broader ADR-016 generalisation)
  rather than building it now. ADR-016 carries no verify/reshape clause today, so
  the step-to-step reshape is a clean future PLAN.

- **SD-3 — The RESHAPE output contract. [Cowork recommends: trace + reuse existing
  structured fields; defer any new envelope field.]**
  *Question:* what does the governed envelope carry post-reshape?
  (a) A structured **verified-action assertion** + a `ReasoningStep` trace
  (`kind="action_verification"`), **reusing** existing fields (the envelope already
  carries `suggested_handler`/`handler_payload`, `actions.py:53-54`) and a
  normalized action statement — no new field.
  (b) An **optional new field** on `RecommendedAction` (e.g. `verified_action`).
  *Cowork recommendation:* **(a)** — trace-only + reuse keeps the **ADR-007 D2
  envelope shape untouched** (the shared contract persistence + the future UI
  consume); member (a) **deferred** its analogous `EntityRef.resolution` field as
  *its* SD-1 for exactly this reason (`done/0030-*.md:112-122`), and the
  trace-only default is fully buildable without that decision.
  *Why this is a Cray/Code decision, not a Cowork judgment call:* adding a field to
  `RecommendedAction` changes the shared ADR-007 D2 envelope.

- **SD-4 — ADR need. [Cowork recommends: PLAN-only.]**
  *Question:* record the build in PLAN-0035 with **no ADR change**, **or** a
  one-line ADR-0022 amendment?
  *Cowork recommendation:* **PLAN-only** — ADR-0022 D2 already frames member (b)
  (`:124-128`) and D3-α houses it; no fork beyond the Accepted ADR is needed under
  SD-1 (a) (mirrors PLAN-0034 SD-3 = (a), PLAN-only). A one-line ADR-0022 amendment
  is needed **only if** SD-1 lands (b)/(c) (an LLM-judge surface the Accepted ADR
  does not contemplate) — and then it is a **separate Cowork-drafted, G1-gated
  edit** to the Accepted ADR, flagged not applied inline (Guardrails).

- **SD-5 — The moat-framing guard (call this out explicitly). [Cowork
  recommends: keep the distinction crisp; scope the grader fix OUT.]**
  *Statement, not a fork:* member (b) is an **engine governance capability**
  (verify+reshape so downstream consumers trust the **structured action**, not
  prose); the 5-case §B-3 benchmark lift is the **demonstration**
  (reports-not-gates), **NOT** the goal. A *separate, smaller* question — whether to
  also fix the grader's prose-only `action_keywords` check (`grader.py:260-267`) to
  read `suggested_handler` — is a **measurement-correctness** matter, **NOT** the
  moat capability.
  *Cowork recommendation:* the PLAN **distinguishes** them and **scopes the grader
  fix OUT** (Out of Scope), noting it only as a separate measurement aside, so the
  engine work is **not** mistaken for teaching-to-the-test. (If Cray wants the
  grader fix tracked, it is a one-line follow-up TODO, not part of this build.)

## References

- **ADR-0022 (Accepted)** `docs/adr/0022-governed-entity-resolution.md` — D1
  (`:108-115`), D2 (member (b) `:124-128`; "(a) is a specific instance of (b)"
  `:130-134`), D3-α (`:136-147`), Fork-3 / D-6 (`:190-198`), Constraints/guardrails
  (`:200-219`).
- **PLAN-0030 (member (a) build — the pattern)**
  `docs/plans/done/0030-governed-entity-resolution-build.md` (the AC shape, the SD-1
  deferred-field pattern `:112-122`, the offline-test contract).
- **The gap + anchors (live code, re-verified session 72):**
  `services/engine/recommender.py:140-174` (`_compose_llm_record`; `:166` trace
  merge, `:168` resolved entities, `:169` the structured handler), `:177-216`
  (`recommend` + the `:199-202` seam + the `:203-216` IN-4 fail-safe), `:219-289`
  (`_rule_recommend`; `:275-279`/`:284` already consistent);
  `services/engine/structured.py:85-108` (`LlmJudgment`), `:111-125`
  (`_judgment_schema` enum-binds `suggested_handler`);
  `services/engine/actions.py:20-24` (`ReasoningStep`), `:33-39` (`AuditMetadata`),
  `:42-63` (`RecommendedAction`); `services/engine/entity_resolution.py:164-209`
  (`resolve_affected_entities`), `:125-161` (`_resolution_step`), `:62-72`
  (`normalize_entity_key`); `tests/services/engine/test_entity_resolution.py:1-31`
  (offline fakes).
- **REPORT §B-3 (the target evidence):** `benchmarks/procedure_baseline/REPORT.md:697`
  (the three-arm baseline) + **`:922-933`** (the 5-correct-action / 2-wrong-action
  residual decomposition — the A1 target); §3.4 narrative `:747-771`; the
  verify+reshape forward-pointer `:773-780`. The grader gap:
  `benchmarks/procedure_baseline/grader.py:260-267` (`action_keywords` substring,
  reads no structured handler) + `benchmarks/procedure_baseline/schema.py:152-156`
  (`Expected.action_keywords`). The A2 re-grade harness:
  `benchmarks/procedure_comparison/regrade_arm_a.py`.
- **Procedure-engine seam (SD-2 forward-pointer):**
  `services/engine/procedures/orchestrator.py:59-72` (`StepOutcome`), `:90-95`
  (`StepExecutor`), `:113-159` (`validate_runnable`);
  `services/engine/procedures/action_step.py:113-144` (`_compose_action`; `:140`
  `step.handler` override).
- **Lineage + guardrails:** ADR-0021 (classify, don't synthesize); ADR-007 D2 (the
  envelope, generalised not broken); ADR-010 IN-4 / PLAN-0006 §6.6 (the
  deterministic fail-safe — do not regress); PLAN-0027 D-6 / PLAN-0028 (the
  contamination guard); ADR-016 (the governed procedure engine — no verify/reshape
  clause today); ADR-011 + `actions.py:33-39` (audit interplay, flagged only);
  CLAUDE.md §1 (semantic layer = the moat), §6 (Decision/Plan Flow), §8
  (PDPA-forward / anti-hallucination; ADR-Accepted-before-impl; host-state
  ASK-Cray); ADR-009 D1/D2; ADR-012 D4.3; ADR-013.
- **Dispatch + roadmap:**
  `.claude/handoffs/session-72/2026-06-22-0223-code-cowork-a1-verify-reshape-plan0035-dispatch.md`;
  `.claude/handoffs/session-72/2026-06-22-0211-code-session72-plan0034-closeout-a1-bridge.md`;
  STATUS Active TODO "A1 — verify+reshape governance demo (B-γ moat successor)".

---

*PLAN-0035, the verify+reshape build (ADR-0022 member (b) — the heaviest
moat-proof: the governed engine verifies an LLM step's emitted output for semantic
consistency against a declared contract and reshapes it so downstream trusts the
structured action, not prose — the capability arm (c) naive-RAG structurally
lacks). Drafted by Cowork (Tier-1, ADR-009 D1); Code reviews, commits (ADR-009
D2), and executes; Cray ratifies the SDs. Mirrors PLAN-0030 (member (a)). Synthetic
data only; engine slice only; the deterministic fail-safe (`recommender.py:219-289`)
is untouched; the D-6 boundary is BINDING; the §B-3 lift is a demonstration
(reports-not-gates), not the goal (SD-5); offline-only build (no host-state).
AI-assisted (Claude, Cowork session); no `Co-Authored-By` per CLAUDE.md §7.*
