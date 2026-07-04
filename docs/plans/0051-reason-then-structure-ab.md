# PLAN-0051: Reason-then-structure A/B — measure the reasoning-order lever on the two single-pass structured-output call sites

**Status:** Draft
**Owner:** Claude Code (executes; offline build is Code-solo); `plan-drafter` drafted (ADR-013 D1 phased authority); Cray ratifies
**Created:** 2026-07-04
**Related ADRs:** ADR-010 (IN-3 confidence-never-routes / determinism invariant; D1 local-backend), ADR-0021 (classify-don't-synthesize; `measured_kind`), ADR-0024 (procedure generator — D4 `gate_kind` cross-check / D7 AT-1-family-only + abstain, the moat guard this PLAN must NOT move; D12 tests-are-the-offline-oracle), ADR-001 (CHECKPOINT-0 / Ollama #15260 caller contract — never `think=False` with `response_format`)

> **No new ADR (recommended — SD-5).** This PLAN adds **experimental levers + labelled corpora + an offline+live A/B harness**. It changes **no grammar**, **no deterministic guard**, and **no shipped production default**. It mirrors PLAN-0041 (a prompt-lever A/B on the SAME classify path) which needed no ADR. If a *future adoption* of two-pass as a cross-site standard is decided, THAT is a separate, possibly ADR-gated decision — explicitly not this PLAN (SD-6). If execution surfaces a reason a deterministic guard or a shipped default *must* change to run the experiment, **STOP and surface it** (that flips to an ADR-gated decision); do not bake it in here.

> **Provenance / author≠reviewer (ADR-012 D4.3).** Originator of the outline = Cray (this session — the scope was Cray-ratified and LOCKED per the dispatch). Drafter = the in-harness `plan-drafter` subagent (ADR-013 D1 phased authority). The research grounding is the July-2026 brief `docs/research/private/2026-07-03-llm-db-reliability-techniques.md` (finding #2 + TOP-REC #1). Independent reviewer = Cray at PR merge, with Code R2-review at commit. Separation: INTACT (the drafter is not the reviewer; the outline originator is not the artifact author).

---

## Goal

Measure whether the industry-converged **"reason-then-structure"** pattern (a free-form reasoning pass before a constrained extraction pass) — and its cheaper within-schema variant, **ordering reasoning fields BEFORE decision fields** — improves accuracy on vero-lite's **two remaining single-pass structured-output call sites**, reusing the offline oracle as the scoring gate. The July-2026 research brief (finding #2 / TOP-REC #1) found that strict single-pass constrained decoding degrades reasoning 10-30%, worst when answer/decision fields precede reasoning fields. The two targets are the exact anti-pattern:

1. **classify** — `services/engine/procedures/generator/pipeline.py::classify_narrative`, schema `Classification` (field order: `archetype_id` [the DECISION, field 0] → `step_gates` → `rationale` [field 2] → `confidence`) — decision-before-reasoning.
2. **nl_query** — `services/engine/nl_query.py::_translate`, schema `StructuredQuery` — has NO reasoning field at all today.

(The anomaly **recommender**, `services/engine/llm/structured.py::generate_judgment`, ALREADY does reason-then-structure — a two-call Pattern B with a `ReasoningMode` lever — so it is OUT of scope: it is the reference pattern the two-pass arm mirrors, not a target.)

Each site runs a **3-arm A/B** — **baseline** (shipped single-pass), **field-order flip** (a reasoning field emitted first), and **two-pass reason-then-structure** (a free-form reasoning call before the constrained call, mirroring the recommender's Pattern B) — scored against a labelled offline corpus with a **pre-committed pass/fail read fixed BEFORE any run**. The deliverable is **the experiment + the DATA + an adopt/reject recommendation**; flipping any shipped default to a winning arm is a SEPARATE follow-up (SD-6).

## LOCKED (Cray-ratified this session — render faithfully, do NOT re-open)

1. **Both call sites, three arms each.** classify + nl_query; per site: `baseline` / `field_order_flip` / `two_pass`. baseline = the shipped single-pass call verbatim.
2. **HARD CONSTRAINT — CHECKPOINT-0 / Ollama #15260 (ADR-001).** In the two-pass arm the STRUCTURING call (call 2) must NOT pair `think=False` with `response_format` — **omit `think` on call 2**, exactly as the shipped recommender (`structured.py:212`) and the classify/prose schemas already do (`schemas.py` docstring lines 21-24). The free-form reasoning call (call 1) carries **no** `format`, so the hazard does not apply to it.
3. **The classify determinism invariants are LOCKED** (ADR-010 IN-3 / ADR-0019 / ADR-0021 / ADR-0024 D4/D7). `confidence` is advisory and NEVER routes; `archetype_id` is the closed `ARCHETYPE_CHOICES` enum (classify-don't-synthesize); the route is a deterministic function of the LABEL + the per-step cross-check. Any field-order / two-pass change must NOT touch `_archetype_disagreement`, `_AT2_ONLY_KINDS`, `_BAND_KINDS`, or the closed-label check — **the guard stays byte-identical across arms** (as PLAN-0041 already does, importing the production guard).
4. **The shipped default stays baseline** until a separate adoption decision (SD-3, SD-6). The arm selector is confined to the harness / an experimental lever; no arm becomes the production default in this PLAN.
5. **The offline oracle is the acceptance gate; live = confirming evidence, not the gate** (CLAUDE.md §8; Lesson #0026). Every pass/fail read is pre-committed in the committed harness BEFORE any live run and is **not adjusted after the run**. The whole offline build is Code-solo / offline; the live A/B on MS-S1 is host-state (explicit Cray go; live runs minimised).
6. **No grammar change, prefer no Alembic migration.** This is prompt/harness/corpus work — no ontology change, no schema DDL. If a migration appears necessary, STOP and surface it.

## Acceptance Criteria

**Offline gate (the verdict — zero host-state; each merges on green):**

- [ ] **AC-1 (classify — arm plumbing, offline).** An experimental arm selector (SD-3) drives `classify_narrative` through `baseline` / `field_order_flip` / `two_pass` WITHOUT changing the shipped default. Offline structural tests assert: (a) `field_order_flip` emits a schema whose FIRST property is the reasoning/`rationale` field, decision field(s) after it; (b) `two_pass` issues a free-form reasoning call (no `response_format`) BEFORE the constrained call, and the constrained call OMITS `think` (CHECKPOINT-0); (c) the deterministic guard (`_archetype_disagreement` + closed-label check) is **byte-identical** across all three arms; (d) `classification_schema()` still pins `archetype_id` to `list(ARCHETYPE_CHOICES)` in every arm. Runs on a `RecordedChatClient`-style seam; no MS-S1 call.
- [ ] **AC-2 (classify — corpus reuse, offline).** The A/B reuses PLAN-0041's labelled corpus verbatim — `tests/services/engine/procedures/classify_enrichment_fixtures.py` (26 narratives; Arm A lift {AT-1/AT-1b/AT-3}, Arm B {11 AT-2 that must abstain}) — and its structural validators (`test_classify_enrichment_fixtures.py`). No new classify corpus is authored; the arms are the only new variable.
- [ ] **AC-3 (nl_query — corpus, offline).** A NEW labelled nl_query A/B corpus exists (SD-1: size, authorship, scoring metric, the RESOLVED "aggregate-superlative" hard class NOT double-counting the Phase-B seam), as a pure-data module (no `test_` prefix) with structural validators. Gold `StructuredQuery` objects + the pre-committed accuracy metric + regression floor (SD-4) are recorded in the committed corpus/harness.
- [ ] **AC-4 (nl_query — arm plumbing, offline).** An experimental arm selector (SD-3) drives `_translate` through its arms (SD-2 decides whether `field_order_flip` applies to nl_query or only `baseline`+`two_pass` run there) WITHOUT changing the shipped default. Offline tests assert the two-pass constrained call OMITS `think` (CHECKPOINT-0), the semantic validator (`_validate_query`) and the Phase-B rewrite seam (`_infer_group_by`/`_coherence_rewrite`) are **unchanged**, and any added leading reasoning field (SD-2) is **dropped before execution** (advisory only).
- [ ] **AC-5 (both sites — full suite green).** Every step green under the PLAN-0047 Step-7 CI gate: `ruff` + `ruff-format` + `mypy --strict services/` clean; `pytest` green (existing baseline + new tests, with postgres); `alembic upgrade head` + `alembic check` clean (no migration expected — LOCKED-6).

**Live evidence (confirming, NOT the gate — behind an explicit Cray host-state go):**

- [ ] **AC-6 (classify — live twin metric, host-state).** Mirroring PLAN-0041 AC-7 / `test_classify_enrichment_live.py` exactly: on the 26-narrative set, per arm, N ≥ 3 reps, report the WORST rep. Pre-committed read: **Arm B 11/11 abstain HARD every rep**, AND **Arm A gated AT-1+AT-3 ≥ 9/11 AND strictly > the paired baseline arm on the same rep**. A single Arm-B false-accept (any rep, any arm) FAILS. Both arms route through the byte-identical imported guard. The `_route(client, messages)` helper pattern is copied from PLAN-0041.
- [ ] **AC-7 (nl_query — live A/B, host-state).** On the nl_query corpus (AC-3), per arm, N ≥ 3 reps, report the WORST rep, against the SD-4 pre-committed accuracy metric + regression floor. Recorded as "X/N → Y/N on this corpus", never a population rate (the corpus is small + hand-authored + the model is non-deterministic live — the PLAN-0041 honesty flag).

## Out of Scope

- ❌ **Flipping any shipped production default** to a winning arm — the deliverable is the experiment + DATA + a recommendation; adoption is a SEPARATE follow-up (SD-6).
- ❌ **A new ADR** — unless SD-5 is overturned by Cray. (A future cross-site adoption of two-pass may warrant one; that is deferred, not part of this PLAN.)
- ❌ **The recommender site** (`generate_judgment`) — it ALREADY does two-pass reason-then-structure with a `ReasoningMode` lever; it is the reference pattern, not a target.
- ❌ **Any change to the classify deterministic guard** (`_archetype_disagreement` / `_AT2_ONLY_KINDS` / `_BAND_KINDS` / the closed-label check) — LOCKED-3, byte-identical across arms.
- ❌ **Any change to the nl_query semantic validator or the Phase-B rewrite seam** (`_validate_query` / `_infer_group_by` / `_coherence_rewrite`) — the arms move only the translate LLM call, never the deterministic post-processing (LOCKED, and it is what already fixes the aggregate-superlative class — SD-1).
- ❌ **A confidence threshold in any route** (ADR-010 IN-3).
- ❌ **An Alembic migration / any ontology or grammar change** (LOCKED-6).
- ❌ **Widening the corpora beyond what the metric needs** — the classify corpus is reused as-is; the nl_query corpus is sized to the SD-1 recommendation.

## Surfaced Decisions (SD-1..SD-6 — recommendation each; Cray adjudicates, do NOT silently resolve)

### SD-1 — nl_query gold corpus: size, authorship, and the scoring metric

nl_query has **no** labelled A/B corpus today (only behavioural tests in `tests/services/engine/test_nl_query.py`). This PLAN must author one.

- **Recommendation — corpus size:** ~24-30 questions across the energy ontology (matching the classify corpus's ~26 scale so the two sites report comparably), spanning: simple `list` + conjunctive filter; `count`; each aggregate op (`max`/`min`/`avg`/`sum`); a cross-type `resolve` (name→id); and a **known-hard class** — the documented "aggregate-superlative drops filter+group_by" (memory `project_nl_query_aggregate_framing_drops_filter`).
- **Recommendation — authorship:** each gold `StructuredQuery` is hand-authored against the live energy ontology metadata (`load_ontology_meta("energy")`), validated by `_validate_query` at corpus-build time (a gold that fails the semantic validator is a corpus bug), stored as a pure-data module mirroring `classify_enrichment_fixtures.py`.
- **Recommendation — scoring metric: field-weighted partial structural match on the RAW `_translate` output**, NOT execution-equivalence and NOT strict all-or-nothing. Rationale: (a) execution-equivalence needs a fixed dataset + the full execute path and conflates translate accuracy with data-shape luck; (b) strict match over-penalizes a semantically-equivalent `limit` or field-ordering difference; (c) a field-weighted score (heavy weight on `object_type` + `operation` + the presence/correctness of the question-implied `filters`; lighter on `limit`) isolates the reasoning-order lever's actual effect. **Score the RAW `_translate` output, not the post-rewrite result** — the Phase-B deterministic seam (`_infer_group_by`, `_coherence_rewrite`) runs AFTER `_translate` and already FIXES the aggregate-superlative drop; scoring post-rewrite would let the seam mask (or credit) the lever. The known-hard class is therefore scored **only on what `_translate` emits** — the corpus must NOT double-count what the deterministic seam repairs (i.e. its gold is the raw translate the model *should* produce, and the seam's repair is a separate, already-tested property).
- **Alternatives considered:** execution-equivalence (rejected — conflates translate with execute + needs a frozen dataset); strict structural match (rejected — over-penalizes benign differences); scoring the post-rewrite result (rejected — the seam masks the lever).
- **Why a Cray decision:** the metric definition is load-bearing for the entire nl_query verdict and has multiple defensible forms; picking one silently would bake a measurement bias.

### SD-2 — the "field-order flip" realization for nl_query (StructuredQuery has no reasoning field)

classify's flip is mechanical (move `rationale` before `archetype_id`). `StructuredQuery` has **no** reasoning field, so "field-order" must be defined.

- **Recommendation — add an OPTIONAL leading `reasoning` (or `intent`) string field, emitted FIRST, advisory-only, dropped before execution.** Concretely: in the `field_order_flip` arm the harness builds a variant schema with a leading `reasoning: str` property; the model reasons into it first, then emits the decision fields (`object_type`, `operation`, ...); the harness **strips `reasoning` before `_validate_query`/execute** so the production execute path and the grounding receipt are untouched. This makes nl_query's flip the DIRECT analog of classify's `rationale`-first flip and keeps all three arms comparable across the two sites.
- **Alternative considered:** SKIP the field-order arm for nl_query and run only `baseline` + `two_pass` there (simpler; fewer moving parts; but then the two sites are not symmetric and the cheaper within-schema variant — the brief's second recommendation — goes unmeasured for nl_query, which is the more reasoning-starved site).
- **Why a Cray decision:** introducing even an advisory field into a moat schema (`StructuredQuery` is the grounding receipt returned to the caller) is a schema-surface choice; whether the symmetry is worth the added field is a judgment with a defensible either-way answer.

### SD-3 — lever-switching mechanism (select arms WITHOUT changing production defaults)

- **Recommendation — an experimental arm enum threaded as a keyword-only param with a baseline default**, mirroring the existing `ReasoningMode` precedent (`structured.py:42-57`). Concretely: a `ClassifyArm` / `TranslateArm` `Literal["baseline", "field_order_flip", "two_pass"]` defaulting to `"baseline"`, threaded through `classify_narrative` and `_translate` (which already takes a `ChatClient` and a `retry_budget`, so a keyword-only arm param is additive and back-compatible). The shipped call sites pass nothing → they get `"baseline"` → **byte-identical shipped behaviour**. The variant schema-builders and the free-form reasoning call live in the same module, gated on the arm. The harness/tests are the only callers that pass a non-baseline arm.
- **Alternatives considered:** a settings/env flag (rejected — global state, risks leaking into the shipped path + harder to isolate in pytest, cf. the goal-path leakage class in memory); a wholly separate harness-only copy of the translate/classify function (rejected — drifts from production, defeats "the guard/validator is byte-identical").
- **Why a Cray decision:** the mechanism determines how firmly the shipped default is protected; the `ReasoningMode`-style param is the safest analog but adding a public param to two production functions is an API-surface choice worth ratifying.

### SD-4 — metrics + pass/fail per site (pre-committed before any live run)

- **classify — recommendation:** reuse PLAN-0041's twin metric **verbatim** (it already fits the reused corpus): Arm B 11/11 abstain HARD every rep; Arm A gated AT-1+AT-3 ≥ 9/11 AND strictly > the paired baseline arm on the same rep; N ≥ 3, worst rep reported; AT-1b measured-only. The only change from PLAN-0041 is that "before/after" becomes "baseline vs {field_order_flip, two_pass}" — each variant arm is compared against the baseline arm measured in the SAME rep (paired, non-cherry-pickable).
- **nl_query — recommendation:** pre-commit **(a) a mean field-weighted score floor** (e.g. a variant arm must not fall below baseline mean minus a small tolerance — the **regression floor**) AND **(b) a strict-improvement read on the known-hard class** (a variant PASSES as a *win* only if it strictly beats baseline on the raw-translate aggregate-superlative subset without regressing the mean). Concrete numbers (the floor tolerance, the hard-class win threshold) are finalized when the corpus is authored (Step 3) and recorded in the committed harness **before** any live run — never adjusted after.
- **Alternatives considered:** a single global accuracy number (rejected — hides a hard-class win/loss); an unfloored "higher is better" (rejected — a variant could win the mean while regressing a critical class).
- **Why a Cray decision:** the nl_query metric is newly invented here (no PLAN-0041 precedent to inherit) and the floor/threshold values set the adopt/reject bar.

### SD-5 — does this experiment PLAN need an ADR?

- **Recommendation: NO.** This PLAN adds experimental levers + corpora + an offline+live harness; it changes no grammar, no deterministic guard, and no shipped default. PLAN-0041 (a prompt-lever A/B on the same classify path) needed no ADR under the identical rationale. **Deferred/possible ADR (noted, not part of this PLAN):** if the DATA later motivates adopting two-pass as a *cross-site standard* (changing shipped defaults on multiple call sites), that adoption is the ADR-worthy decision — this PLAN produces the evidence for it, nothing more.
- **Alternative considered:** author a small ADR now to record "reasoning-order is a first-class lever" (rejected as premature — there is no cross-cutting decision to record until the data exists; an ADR now would be a decision with no evidence).
- **Why a Cray decision:** whether an experiment that touches two production functions' signatures crosses the ADR bar is a governance judgment (CLAUDE.md §6 mechanical overlay routes new PLANs/ADRs through the drafter; the ADR-vs-no-ADR call is Cray's).

### SD-6 — adoption boundary (confirm the deliverable stops at the recommendation)

- **Recommendation — CONFIRM:** this PLAN's deliverable = **the experiment + the DATA + an adopt/reject recommendation per site×arm**. Flipping any production default to a winning arm is a **SEPARATE follow-up** — either a small PLAN or a small change gated on the live result (and, per SD-5, possibly ADR-gated if it becomes a cross-site standard). The shipped default stays `baseline` at the close of this PLAN regardless of the measured winner.
- **Alternative considered:** allow this PLAN to flip a default if a variant wins decisively offline+live (rejected — a production-default change on a moat path deserves its own reviewed boundary + its own §8 host-state confirmation of the *adoption*, not a rider on the experiment).
- **Why a Cray decision:** the scope boundary between "measure" and "adopt" is exactly the kind of load-bearing line Cray sets; confirming it prevents scope creep at execution time.

## Steps

> classify arms go first — the labelled corpus already exists (PLAN-0041), so classify reaches a live-ready state with the least new surface. The nl_query corpus is authored next, then its arms. Each step names its files + its offline gate. Executable by Code in feature-branch PRs (per-step, off `main`, Cray merges each — no self-merge).

### Step 1 — classify arm plumbing (SD-3) + variant schema-builders (AC-1)

Thread the experimental arm param (SD-3) through `classify_narrative` (`services/engine/procedures/generator/pipeline.py`), defaulting to `baseline`. Add the variant schema-builder for `field_order_flip` (a `Classification`-shaped schema with `rationale` emitted first, `archetype_id` after — still pinning `archetype_id` to `list(ARCHETYPE_CHOICES)`) and the `two_pass` path (a free-form reasoning call with no `response_format` before the constrained call; the constrained call OMITS `think` — CHECKPOINT-0). The deterministic guard is untouched and byte-identical across arms.
Files: `pipeline.py`, `schemas.py` (variant schema helper — leave the shipped `Classification` / `classification_schema()` untouched), `services/engine/procedures/generator/prompts.py` (a reasoning-pass message builder for the two-pass arm).
Offline gate: AC-1 structural tests (arm-selects-correct-schema, first-property assertion, two-pass omits `think` + issues a formatless reasoning call, guard byte-identity, enum pin).

### Step 2 — classify offline A/B harness reusing the PLAN-0041 corpus (AC-2)

Add the offline A/B driver that runs the 26-narrative `FIXTURES` through each arm on a `RecordedChatClient`-style seam and applies the imported production guard (`pipeline._archetype_disagreement` + closed-label check), asserting the structural properties per arm. Reuse `classify_enrichment_fixtures.py` + `test_classify_enrichment_fixtures.py` verbatim (no new classify corpus).
Files: `tests/services/engine/procedures/test_reason_then_structure_classify.py` (new offline harness).
Offline gate: AC-2 (corpus reused unchanged; the arm is the only new variable) + AC-5.

### Step 3 — author the nl_query gold corpus + pre-committed metric (SD-1, SD-4; AC-3)

Author the ~24-30-question labelled nl_query corpus as a pure-data module (no `test_` prefix), each with a hand-authored gold `StructuredQuery` validated by `_validate_query` at build time, including the known-hard aggregate-superlative class scored on the RAW `_translate` output (SD-1). Record the field-weighted scoring metric + the pre-committed regression floor + the hard-class win threshold (SD-4) in the committed harness/corpus **before any live run**. Add structural validators (gold well-formedness, every gold passes the semantic validator, hard-class present).
Files: `tests/services/engine/nl_query_ab_fixtures.py` (new, pure data), `tests/services/engine/test_nl_query_ab_fixtures.py` (new structural validators).
Offline gate: AC-3 + AC-5.

### Step 4 — nl_query arm plumbing (SD-2, SD-3) + offline A/B harness (AC-4)

Thread the arm param through `_translate` (`services/engine/nl_query.py`), defaulting to `baseline`. Realize the arms: `two_pass` (free-form reasoning call before the constrained translate call; the constrained call OMITS `think` — CHECKPOINT-0); `field_order_flip` per SD-2 (an optional leading advisory `reasoning` field on a variant schema, **stripped before `_validate_query`/execute** — OR, if Cray picks the SD-2 alternative, skip this arm for nl_query). The semantic validator + the Phase-B rewrite seam are untouched. Add the offline A/B driver that scores each arm's RAW `_translate` output against the corpus via the SD-1 metric on a `_StubQueryClient`-style seam.
Files: `nl_query.py`, `services/engine/llm/prompt.py` (a translate-reasoning message builder if needed), `tests/services/engine/test_reason_then_structure_nl_query.py` (new offline harness).
Offline gate: AC-4 (arm plumbing, `think`-omission, validator + seam unchanged, advisory field dropped before execute) + AC-5.

### Step 5 — Cray-gated live A/B on MS-S1 (AC-6, AC-7; HOST-STATE)

**ASK Cray** before warming (CLAUDE.md §8). Warm `gpt-oss:20b` via the `ms-s1-ollama` skill (reach by IP `192.168.1.133:11434`). Run both live twin-metric harnesses (classify AC-6 mirroring `test_classify_enrichment_live.py`; nl_query AC-7), each SKIPPED unless `OCT_LIVE_MS_S1=1` + reachable MS-S1, N ≥ 3 reps, WORST rep reported, pre-committed reads in the module docstrings/constants **fixed before the run**. Both classify arms route through the byte-identical imported guard. Live = confirming evidence; the offline gate (AC-1..AC-5) is the verdict.
Files: `tests/services/engine/procedures/test_reason_then_structure_classify_live.py`, `tests/services/engine/test_reason_then_structure_nl_query_live.py` (both new, skip-by-default, host-state).
Gate: AC-6 + AC-7 (evidence, not the merge gate).

### Step 6 — RESULTS write-up + adopt/reject recommendation (SD-6)

Record the offline + (Cray-gated) live numbers per site×arm and the adopt/reject recommendation per site. State explicitly that flipping any shipped default is a SEPARATE follow-up (SD-6). No production default is changed in this PLAN.
Files: a RESULTS doc under the PLAN's evidence location (NOT a new file under `docs/plans/` citing a plan# — that trips G2 per memory `project_g2_gate_on_non_plan_doc_in_docs_plans`; embed the results in the committed live-test module docstrings + a `docs/logs/` summary, mirroring how PLAN-0041 recorded evidence).
Gate: the recommendation is a report, not a CI gate.

## Verification

- **Offline (the verdict):** AC-1..AC-5 green — classify + nl_query arm plumbing correct, both two-pass arms OMIT `think` on the constrained call (CHECKPOINT-0), the classify guard byte-identical across arms, the nl_query semantic validator + Phase-B seam unchanged, the nl_query advisory reasoning field dropped before execute, schema enums pinned, full suite + ruff + ruff-format + mypy --strict + alembic check clean.
- **Red-team mitigations bound to assertions:**
  - **R1 (an arm silently changes the shipped default):** the shipped call sites pass no arm → `baseline` → byte-identical; an offline test asserts the shipped default is `baseline` for both functions.
  - **R2 (a two-pass arm pairs `think=False` with `format` — the Ollama #15260 hazard):** AC-1(b)/AC-4 assert the constrained call OMITS `think` and the reasoning call carries no `response_format`.
  - **R3 (the nl_query advisory reasoning field leaks into execute / the grounding receipt):** AC-4 asserts the field is stripped before `_validate_query`/execute; the returned `StructuredQuery` receipt is unchanged from baseline.
  - **R4 (the nl_query metric masks the lever via the Phase-B seam):** SD-1 scores the RAW `_translate` output, not the post-rewrite result; a corpus validator asserts the hard-class gold is the raw translate, not the seam-repaired query.
  - **R5 (a classify field-order/two-pass arm weakens the moat guard):** the guard is imported byte-identical (PLAN-0041 pattern); AC-1(c) asserts identity across arms; Arm B 11/11 HARD is the live measurement that the abstain brake still works.
- **Live (confirming evidence, Cray-gated):** AC-6 classify twin metric (Arm B 11/11 abstain HARD every rep AND Arm A gated ≥ 9/11 AND strictly > paired baseline, worst of N ≥ 3); AC-7 nl_query field-weighted score vs the pre-committed floor + hard-class win threshold, worst of N ≥ 3, reported as "X/N → Y/N on this corpus".

---

*Drafted by the in-harness `plan-drafter` subagent (session — ADR-013 D1 phased authority). Uncommitted; Code R2-reviews + commits via a `docs/*` PR after Cray ratifies (ADR-009 D2). Experimental levers + corpora + an offline+live A/B harness only — no grammar change, no deterministic-guard change, no shipped-default change; no new ADR (SD-5 recommends NO). The two-pass arm mirrors the shipped recommender's Pattern B (`structured.py`); the CHECKPOINT-0 / Ollama #15260 caller contract (never `think=False` with `response_format`) is a HARD constraint on the constrained call. Grounding: the July-2026 research brief `docs/research/private/2026-07-03-llm-db-reliability-techniques.md` (finding #2 + TOP-REC #1) + the PLAN-0041 offline+live harness. SD-1..SD-6 carry drafter recommendations; Cray adjudicates. AI-assisted; no `Co-Authored-By` per CLAUDE.md §7.*
