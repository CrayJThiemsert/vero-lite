# PLAN-0026: NL-query aggregate metric-semantics (two-layer fix — Phase B deterministic rewrite, ships first; Phase A ontology `measured_kind`, gated)

**Status:** Proposed
**Owner:** both (Cowork/plan-drafter authors this PLAN; Code commits + executes per ADR-009 D2)
**Created:** 2026-06-15
**Related ADRs:** ADR-008 (YAML ontology specification — the `measured_kind` home; SD-2); ADR-001 + Amendment 1 (`gpt-oss:20b` recommender-path pin — **stays**); ADR-010 (LLM reasoning-hook surface — D1 local backend, D4 untrusted-block containment); ADR-005 (OCT pivot — energy first); ADR-006 (vertical plugin architecture / template-first, Rule of Three); ADR-009 D1/D2 (Cowork drafts, Code commits); ADR-012 D4.3 (author≠reviewer disclosure)
**Related Plans:** PLAN-0013 (OCT stakeholder demo — shipped the engine-A NL-query path, done); PLAN-0024 (NL-query T2 engine enrichment — deterministic aggregates + `resolve` join, done; **this PLAN closes its two residual misses**); **PLAN-0025 (the UI shell — number reserved, deferred, future)**

> **Disclosure (ADR-012 D4.3).** Drafted by Cowork (Tier-1 plan-drafter, ADR-009 D1)
> from Cray's 2026-06-15 dispatch on the in-repo evidence base (the RESULTS.md
> 4-model-sweep + 3-prompt-escalation addenda, the metric-semantics pattern
> article, and the two-LLM external consult). **One source artifact —
> `docs/research/private/2026-06-15-ontology-metric-semantics-pattern.md` — is a
> Cowork (Tier-0) research output**, so the research-author and this plan-author
> sit in the same tier; the independent-deliberation check is therefore **not**
> exercised at authoring time. **Code's review at PR merge is the remaining
> independent check** (and Cray ratifies the gated Phase-A ADR). Separation noted,
> not asserted.

---

## Goal

Close the **one residual NL-query failure class** that PLAN-0024 left open — the
**filter-omission on aggregate superlatives** (the spike's nl-08 / nl-11) — with
the **two-layer, phased fix** the evidence points to, while preserving without
exception the deterministic grounded-execute path and the **12/12
anti-hallucination** guarantee. The fix is structural, not another model or prompt
attempt: both obvious levers are **empirically falsified** (a 4-model family sweep
and a 3-variant prompt escalation, both NEGATIVE — see Evidence base). The
corrected diagnosis is a **data-model problem** — a *typed query over an untyped,
unit-heterogeneous metric* — so the fix lives in the engine and the ontology, not
the model.

- **Phase B (engine, deterministic, offline-validatable) — ships FIRST, no
  governance gate.** A deterministic post-translate **rewrite seam** between
  translate and execute that (1) **infers `group_by`** for "which / on-which
  `<entity>`" superlatives, (2) applies a **heterogeneous-aggregate coherence
  rewrite** that *composes* the implied kind filter in the engine (the model
  never re-supplies it), and (3) adds a **clarification-not-silent-no-data
  guard**. Phase B makes nl-08 / nl-11 pass the **structured-result lens** on
  today's untyped ontology.
- **Phase A (ontology `measured_kind`, governed) — GATED on the T2-vs-T3 roadmap
  call and on its ADR being Accepted before its impl PR (CLAUDE.md §8).** Declare
  metric-kind as a first-class ontology concept (`measured_kind` enum bound to a
  canonical unit, derived from `unit`), so "temperature" becomes a **first-class
  enum filter** the translate stage only has to *classify* (a bounded enum pick),
  and the engine's coherence rewrite consumes a *principled* kind→unit binding
  instead of Phase B's best-effort determination.

The two phases compose: Phase B builds the seam and ships the interim fix
immediately; Phase A upgrades the same seam from best-effort to typed once the
roadmap call and governance land.

## The load-bearing diagnosis (Cray-directed — stated, not re-opened)

The residual on nl-08 / nl-11 is **not** a model-quality or prompt-tuning gap.
This is the binding read of the evidence and it is **not open in this PLAN**:

- **Model swap is falsified.** A 4-family sweep (`gpt-oss:20b` pin, `nemotron-3-nano:30b`,
  `qwen3.6:35b`, `gemma4:26b`) **all dropped the implied filter** on the
  superlatives (`filters:[]` → all 11 events instead of the 7 celsius readings);
  `group_by` was flaky across all four; the larger models were **2.5–6× slower**
  (a non-starter for an interactive operator tool); the dense 26B was the worst
  (invented a `resolve` to an un-named entity, failed a coherent named-entity
  aggregate after 3 retries). The omission is **model-class-general**.
- **Prompt tuning is falsified.** A 3-variant escalation on the pin: a general
  "an aggregate still needs its implied filter" rule had **no effect**; a
  units-coherence rule **regressed** (the model emitted a filter but *invented a
  bogus `resolve` placeholder* → empty → honest-but-wrong no-data); only a
  near-answer few-shot moved it, flakily (1/2), and that is **teaching to the
  test**, not a generalizable fix.
- **Corrected diagnosis (raw-dump verified).** On the un-named-entity
  superlatives the model drops **two** things: the implied `unit='celsius'` filter
  (→ `result_count 11 ≠ gold 7`) **and** `group_by:asset_id` (emitted
  inconsistently). The headline `value = 96.5` is correct **only by luck** (the
  two `hz` readings at 50.0 sit below it); the `top = "Battery Bank A"` seen in
  the answer is the **phrase step's prose, not the structured aggregate**.
- **Root cause = a typed query over an untyped metric.** `measured_value` is a
  **unit-heterogeneous** float column (celsius and hz in the same column);
  aggregating across it is physically meaningless, and the schema gives the model
  **no metric-kind discriminator** to bind the word "temperature" to. The model
  is being faithful to an underspecified schema. (Two strong external LLMs,
  given a self-contained brief, independently converged on this same data-model
  framing.)

**Therefore:** the fix is *(B)* a deterministic engine rewrite that **composes**
the coherence filter (because the model is unreliable at *synthesizing* it — the
v2 regression evidence) plus deterministic `group_by` inference, and *(A)* moving
metric-kind into the ontology so the model only **classifies** while code
**composes** ("classify, don't synthesize"). Raw text-to-SQL and engine-B remain
**rejected** (PLAN-0024 — text-to-SQL traded away the anti-hallucination guard);
do not re-surface them.

## Evidence base

This PLAN is built on, and must be read against, four in-repo artifacts (the
brief said the context is in-repo — this PLAN does not re-derive it):

- **`benchmarks/nl_query_feasibility/RESULTS.md`** — the spike verdict + the
  PLAN-0024 AC-8 live re-verify (8 → 10/12 structured, anti-hallucination 12/12
  HELD) + **the 2026-06-15 addendum** (the 4-model sweep + 3-prompt escalation,
  both NEGATIVE; the corrected "drops filter AND group_by" diagnosis; the
  PENDING-Cray proposed resolution this PLAN supersedes with the two-layer fix).
- **`docs/research/private/2026-06-15-ontology-metric-semantics-pattern.md`** —
  the pattern article (Cowork Tier-0 output): the root-cause argument, the
  two-layer fix fully argued ("make metric-kind first-class; LLM classifies,
  deterministic code synthesizes; `group_by` inference + clarification guard"),
  and the strategic framing (the typed semantic layer is the moat).
- **`.claude/benchmark-results/2026-06-15-nl-filter-omission-external-consult.md`**
  — the self-contained consult brief; two strong external LLMs independently
  converged on the data-model root cause (the system design, the exact failing
  StructuredQuery, and the constraints are all captured here).
- **`services/engine/nl_query.py`** — the SHIPPED engine-A path (PLAN-0013 +
  PLAN-0024). Current shape this PLAN extends: `StructuredQuery` already carries
  `operation` (`list|count|max|min|avg|sum`), conjunctive `filters`,
  `aggregate_property`, `group_by`, a cross-type `resolve`, and `limit`; the
  execute stage computes aggregates deterministically (`_compute_aggregate`,
  `_relabel_groups`); `_validate_query` / `_validate_extras` already reject an
  incoherent `operation:list` + `aggregate_property`; the empty → `_no_data_answer`
  short-circuit (`_no_data_nlanswer`) is the anti-hallucination guard. **There is
  no rewrite seam between translate and execute today — Phase B adds it.**

The 12-question gold set (`benchmarks/nl_query_feasibility/gold.yaml`) + the
offline scoring test (`tests/benchmark/test_nl_query_feasibility_gold.py`) + the
`_StubQueryClient` offline pattern (`tests/services/engine/test_nl_query.py`) are
reused as the acceptance / regression oracle; the live harness
(`run_benchmark.py`) is the optional, host-state-only verification.

## Acceptance Criteria

- [ ] **AC-1 — nl-08 / nl-11 pass the structured-result lens (the headline gate).**
  Both temperature superlatives execute to **`result_count == 7`** (the celsius
  readings, not the over-broad 11), a structured aggregate **`value ≈ 96.5`**, and
  a structured **`top == "Battery Bank A"`** — produced by the **deterministic
  execute stage over the rewritten query**, present in the grounding receipt
  (`NlAnswer.aggregate`), **not** rescued by the phrase prose. (`≈` allows the
  engine's existing `_fmt_num` rounding; assert on the receipt's structured value
  and group `top`, not on phrased text.)
- [ ] **AC-2 — `group_by` inference (Phase B, deterministic, SAFE).** For a
  "which / on-which `<entity>`" superlative, the rewrite seam **infers
  `group_by`** (the referenced entity dimension, e.g. `asset_id`) from the
  ontology ref relationships when the translate stage left it null. This operation
  **only reshapes the aggregate — it never reduces the matched set, so it can
  never cause a false no-data** (invariant).
- [ ] **AC-3 — Heterogeneous-aggregate coherence rewrite (Phase B, engine
  composes).** When the aggregate target (`measured_value`) is **unit-heterogeneous**
  over the matched set, the rewrite seam **composes the implied kind filter**
  (the coherent `unit`) **in the engine** so the aggregate is computed over a
  single coherent unit. **The model never re-supplies this filter** — the
  translate prompt is **not** escalated to emit it (the v2 prompt-escalation
  *regressed* when asked to: it invented a bogus `resolve` placeholder → empty
  set). Composition is deterministic and engine-internal.
- [ ] **AC-4 — Clarification-not-silent-no-data guard (Phase B, anti-hallucination
  adjacent).** If a rewrite-composed filter **would turn an otherwise-non-empty
  result empty** (or the coherent kind cannot be determined unambiguously), the
  engine **asks the operator to clarify** rather than (a) silently dropping data
  to a false no-data, or (b) fabricating a match. Never confabulate, never
  silently over-filter. (Observability of this third outcome is **SD-1**.) For
  nl-08 / nl-11 the celsius subset is non-empty (7 records), so the guard does
  **not** trigger — it answers.
- [ ] **AC-5 — Anti-hallucination preserved (THE hard gate — non-negotiable).**
  The spike's **12/12 holds.** Every fact still comes from deterministic execute;
  every no-data path (the existing empty short-circuit, an empty aggregate, an
  unresolved name, and the new clarify path) returns an honest answer with **zero
  invented facts**. nl-12 ("list all open alerts", no Alert data) still returns
  the deterministic "No Alert records" answer. **If a capability cannot hold this,
  it is not shipped.**
- [ ] **AC-6 — No regression on the other 10.** The 10 non-target questions keep
  their PLAN-0024 results (the structured lens does not drop below its post-0024
  baseline on any of them); no existing `nl_query` test regresses.
- [ ] **AC-7 — Offline suite green + quality bar (CLAUDE.md §8).** The Phase-B
  rewrite is fully covered by **offline** tests (monkeypatched chat client, **no
  live Ollama**) — including the **decisive offline oracle**: mock the translate
  stage to emit the known-bad output `{filters:[], operation:"max",
  aggregate_property:"measured_value", group_by:null}` → assert the rewrite seam
  produces **`result_count == 7`, `value ≈ 96.5`, `top == "Battery Bank A"`**. The
  deterministic seam (group_by inference, coherence composition, clarify guard) is
  unit-tested with **no LLM at all**. `uv run pytest -q` stays green; **ruff
  clean + mypy clean**; all new code carries type hints + tests.
- [ ] **AC-8 — Phase A: `measured_kind` first-class (GATED — does not ship with
  Phase B).** The ontology declares a `measured_kind` enum (derived from / bound
  to `unit`) on `OperationalEvent`; the translate stage **classifies** the kind
  (bounded enum pick) and the engine synthesizes the precise unit filter from the
  declared kind. **Gate:** built only on the T2-vs-T3 roadmap go AND its governing
  ADR Accepted **before** the impl PR (SD-2; CLAUDE.md §8). This AC is **carried,
  not satisfied, by the Phase-B ship.**
- [ ] **AC-9 — (Optional, MANUAL) live re-verify — host-state, Cray's go.** A
  **live** 12-question harness run against `gpt-oss:20b` @ MS-S1
  (`192.168.1.133:11434`, by IP, warm first) confirms nl-08 / nl-11 move onto the
  structured lens while anti-hallucination stays 12/12. **Minimize live runs**
  (host-state; Cray authorizes). This is a verification step, **not a CI gate**
  (Lesson #15 live-vs-mock).

## Out of Scope

- ❌ **Model swap + prompt tuning to close nl-08 / nl-11 — PROVEN NEGATIVE.** The
  4-model sweep and 3-prompt escalation both failed (see the load-bearing
  diagnosis). Not re-attempted. The translate prompt is **not** escalated to
  supply the coherence filter (it regressed when asked to).
- ❌ **The UI shell (PLAN-0025).** This PLAN ships engine (Phase B) + the gated
  Phase-A ontology change + tests only — no screen. (PLAN-0025 number is reserved
  for the deferred A1 operational-map + A2 approval/review UI.)
- ❌ **A full classify-only translate redesign** (re-architecting translate so it
  *only* classifies and emits no filters at all) — **deferred to a Phase-3 idea**;
  Phase A introduces classification for `measured_kind` specifically, not a
  wholesale translate redesign.
- ❌ **Switching to raw text-to-SQL / engine-B** — rejected by PLAN-0024 (trades
  away the 12/12 anti-hallucination guard); not re-opened.
- ❌ **Multi-operator / write / mutating queries; a new vertical or
  meta-framework** — the engine stays single-operator, read-only over the existing
  energy ontology (Rule of Three, CLAUDE.md §1).
- ❌ **Delegating the new rewrite compute to the phrase LLM** — the rewrite is
  deterministic and engine-internal by construction; phrase-rescue is not the
  mechanism (it is exactly the brittle path the spike flagged).

## Steps

Ordered, each step small and reviewable. **Steps 1–5 are Phase B (unblocked,
ships first). Steps 6–7 are Phase A (gated — do not start until SD-2's ADR is
Accepted and the T2-vs-T3 roadmap go is given). Step 8 is handback.**

### Step 1 — Add the post-translate rewrite seam (Phase B scaffolding)

Introduce a deterministic seam in `answer_question` (`services/engine/nl_query.py`)
**between** `_translate(...)` returning the `StructuredQuery` and the execute
block — the pattern article's `[REWRITE (deterministic, no LLM)]` stage. It
consumes the question + the translated query + the ontology meta
(`OntologyMeta` / `ObjectTypeMeta`), and returns a (possibly) rewritten query
plus a rewrite-decision record for the receipt. It **never calls a model.** Keep
it a pure, separately-unit-testable function so the offline oracle (AC-7) can
drive it directly with the known-bad query.

### Step 2 — `group_by` inference for entity superlatives (AC-2)

In the seam: when `operation ∈ {max,min,avg,sum}`, `group_by is None`, and the
**question** matches a "which / on-which `<entity>`" superlative whose entity maps
(via the ontology ref relationships in `ObjectTypeMeta`) to a ref property on the
queried type, **set `group_by` to that ref property** (e.g. `asset_id`). Reuse
the existing `_relabel_groups` so the receipt's group keys surface the entity
**title** ("Battery Bank A"), not the raw id. **Invariant (assert in tests):**
inferring `group_by` changes only the aggregate's bucketing — the matched set and
`result_count` are unchanged, so this can never produce a false no-data (AC-2).

### Step 3 — Heterogeneous-aggregate coherence rewrite (AC-3) + clarify guard (AC-4)

In the seam, for an aggregate over a **unit-heterogeneous** target property:
- **Detect heterogeneity deterministically** — the matched set spans more than
  one `unit` value for `measured_value`; aggregating across them is incoherent.
- **Compose the coherent kind filter in the engine** (the model never re-supplies
  it — AC-3). The Phase-B determination of *which* coherent unit is the key
  engine-design judgment (see Implementation note IN-1) — it must be deterministic
  and must obey the guard below.
- **Clarify guard (AC-4):** if composing the filter would empty an otherwise-non-empty
  result, **or** the coherent kind is not determinable unambiguously, return the
  **clarify** outcome (SD-1) — never a silent over-filtered no-data, never a
  fabricated match. For nl-08 / nl-11 the celsius subset is non-empty → it
  answers (7 records); the guard does not trigger.
- **Preserve the empty short-circuit:** a genuinely empty matched set (pre-rewrite)
  still routes to `_no_data_nlanswer` unchanged (AC-5).

### Step 4 — Surface the rewrite in the grounding receipt (ties to SD-1)

Carry what the seam did into the returned `NlAnswer` so the rewrite is **auditable**
(which filter the engine composed, which `group_by` it inferred, and whether the
outcome was answered / no_data / clarify). The exact receipt-contract change —
adding `outcome: Literal["answered","no_data","clarify"]` — is **SD-1** (Cray
adjudicates, because it changes the public receipt PLAN-0025's UI will consume).
Do not silently overload `grounded=false` to mean both no_data and clarify.

### Step 5 — Offline tests + suite green (AC-5, AC-6, AC-7)

Extend `tests/services/engine/test_nl_query.py` (the `_StubQueryClient` offline
pattern) and the gold-scoring test:
- **The decisive oracle (AC-7):** mock translate → known-bad output
  `{filters:[], operation:"max", aggregate_property:"measured_value", group_by:null}`
  → assert the seam rewrites to `result_count == 7`, `aggregate.value ≈ 96.5`,
  group `top == "Battery Bank A"`. Add the symmetric nl-11 ("which battery is
  hottest") shape.
- **Seam unit tests (no LLM):** group_by-inference reshape-not-empty invariant
  (AC-2); coherence composition picks the coherent unit (AC-3); the clarify guard
  fires on a would-empty rewrite and returns the clarify outcome, **not** a
  fabricated row and **not** a silent no-data (AC-4).
- **Anti-hallucination (AC-5):** every no-data / clarify path returns zero
  invented facts, asserted at unit + end-to-end level; nl-12 unchanged.
- **Regression (AC-6):** update `benchmarks/nl_query_feasibility/gold.yaml` so
  nl-08 / nl-11 score on the structured lens (per SD-3's disposition); the other
  10 stay green. Run `uv run pytest -q`, `ruff`, `mypy` — all clean (AC-7).

### Step 6 — Phase A: declare `measured_kind` in the ontology (GATED; AC-8)

**Do not start until SD-2's ADR is Accepted and the T2-vs-T3 roadmap go is given.**
Add a `measured_kind` enum to `OperationalEvent` in
`verticals/energy/ontology/energy_v0.yaml`, bound to / derived from `unit`
(e.g. `temperature → celsius`, `frequency → hz`). `enum` already fits ADR-008 D3
(generates `Literal[...]` Pydantic + `TEXT CHECK` SQL), so the existing generator
emits it across all five artifacts — **but the kind→unit binding representation**
(a new ontology construct vs a derived convention) is part of SD-2's ADR scope and
may touch ADR-008 D3 grammar. Update `verticals/energy/data_adapter/synthetic.py`
so the 7 celsius readings carry `measured_kind: temperature` and the 2 hz readings
`measured_kind: frequency`.

### Step 7 — Phase A: translate classifies, engine synthesizes (GATED; AC-8)

Once `measured_kind` exists: extend `_describe_ontology` / `_translate_messages`
so the model **classifies** `measured_kind` (a bounded enum pick — the reliable
operation) instead of synthesizing a unit filter; the Step-3 coherence seam then
consumes the **declared kind** for a *principled* `unit` synthesis (replacing
Phase B's best-effort determination). The clarify guard remains the safety net.
Re-point the offline oracle so the kind is classified, not inferred. Anti-hallucination
12/12 must still hold.

### Step 8 — Handback → Code commits + reconciles

Hand the uncommitted draft path(s) back to Code. **Cowork does not commit**
(ADR-009 D2). Code reviews, commits Phase B on a `feat/*` branch + PR (CLAUDE.md
§7), merges after Cray review, and executes. **Phase A's impl PR is gated on its
ADR (SD-2) being Accepted first** (CLAUDE.md §8: "All ADRs: must be merged before
related implementation PR"). On completion `git mv docs/plans/0026-*.md
docs/plans/done/`.

## Verification

- **AC-1 / AC-7 (the headline):** the offline oracle — mock translate → known-bad
  query → the rewrite seam yields `result_count == 7`, `aggregate.value ≈ 96.5`,
  group `top == "Battery Bank A"` in the receipt (deterministic, not phrase prose),
  for both nl-08 and nl-11 shapes.
- **AC-2:** a unit test asserts `group_by` inference leaves `result_count`
  unchanged (reshape-not-empty invariant).
- **AC-3 / AC-4:** unit tests show the engine composes the coherent unit filter
  with **no** translate-prompt change, and the clarify guard fires (returns the
  clarify outcome, not a fabricated/silent answer) on a would-empty rewrite.
- **AC-5 (the gate):** every no-data + clarify path returns `grounded=false` (or
  the clarify outcome per SD-1) with zero invented facts; nl-12 unchanged —
  asserted at unit + end-to-end level.
- **AC-6 / AC-7:** `uv run pytest -q` green; `ruff` clean; `mypy` clean; all
  NL-query tests offline (no live Ollama).
- **AC-8 (Phase A, gated):** the generated artifacts carry `measured_kind`; the
  translate stage classifies it; the oracle passes via classification — verified
  only after the SD-2 ADR is Accepted.
- **AC-9 (optional, manual):** the live harness shows nl-08 / nl-11 on the
  structured lens with anti-hallucination 12/12, recorded as host-state evidence
  (not a CI gate; Cray authorizes the run).

## Implementation notes

- **IN-1 — the Phase-B coherent-unit determination is the key engine judgment.**
  Phase B must pick the coherent unit deterministically **without** the brittle
  free-form keyword→value map the research explicitly rejected (and without
  re-prompting the model — the v2 regression). A defensible Phase-B rule is to
  derive the coherent unit from the matched set itself (e.g. the unit of the
  records carrying the aggregate extremum / the single coherent unit subset that
  contains the answer), with the **clarify guard (AC-4) as the safety net**
  whenever the determination is ambiguous. Phase A then **supersedes** this
  best-effort rule with the *classified* `measured_kind`. The precise Phase-B rule
  is an implementation choice for Code — flagged here, not silently fixed, because
  it is load-bearing for AC-3.

## Open Questions

- **OQ-1 — Phase-A trigger coupling.** Phase A is gated on the **T2-vs-T3 roadmap
  fork** (Cray's partner-psychology call, still open per RESULTS.md) AND on the
  SD-2 ADR. If T2 is not chosen, Phase A may never ship while **Phase B still
  stands on its own** (it closes nl-08 / nl-11 on today's ontology). Recorded so
  the coupling is explicit and Phase B is not blocked on the fork.

## Surfaced decisions (SD-N) — Cray adjudicates (Tier 1 rule #8: surface, don't silently choose)

### SD-1 — Add `outcome: Literal["answered","no_data","clarify"]` to `NlAnswer`?

- **Question:** the clarification guard (AC-4) introduces a **third** terminal
  state that is neither "answered" nor the existing `grounded=false` no-data.
  Make it observable by adding an explicit `outcome` enum to the `NlAnswer`
  grounding receipt, or overload the existing `grounded: bool` + answer string?
- **Cowork recommendation:** **add the `outcome` enum.** The whole point of the
  guard is to *not* conflate "I asked you to clarify" with "I have no data" — the
  exact silent-no-data failure Phase B removes. An explicit `outcome` makes the
  receipt self-describing for PLAN-0025's UI and keeps the anti-hallucination
  story legible. Cost: it **changes the public grounding-receipt contract**
  (every consumer + the offline assertions update).
- **Alternative:** keep `grounded=false` and distinguish clarify via the answer
  text only — cheaper, no contract change, but re-introduces exactly the
  no_data/clarify conflation and pushes parsing onto the UI.
- **Why this is Cray's call, not Code's:** it changes the **public
  `StructuredQuery` / `NlAnswer` contract** that PLAN-0025 and any future engine-B
  consume — a contract decision, not an implementation detail (same class as
  PLAN-0024 SD-1).

### SD-2 — `measured_kind`: amend ADR-008, or a new ADR?

- **Question:** Phase A declares metric-kind as a first-class ontology concept.
  Home it as an **amendment to ADR-008** (the YAML ontology specification — the
  grammar owner), or a **new ADR** (the next free number is **ADR-0021**)?
- **Cowork recommendation:** **lean new ADR-0021**, because metric-kind-as-typed-semantics
  + "classify, don't synthesize" is a **distinct architectural decision** with
  substantial independent rationale (the falsified model/prompt fixes, the EAV /
  unit-heterogeneity root cause, the QUDT quantity-kind-vs-unit separation, the
  Foundry value-type precedent — all argued in the pattern article) and a clean
  citation anchor; it **extends** the modeling approach rather than correcting
  ADR-008. **Caveat:** if the kind→unit binding needs a **grammar extension to
  ADR-008 D3** (a new property construct, not just an enum), the new ADR should
  explicitly amend ADR-008 D3, or an in-place amendment may be cleaner.
- **Alternative:** **amend ADR-008 in place** (precedent: ADR-001 Amendment 1,
  Cray-adjudicated amend-vs-new on 2026-05-22) — keeps all ontology-spec knowledge
  in one document; lighter ceremony.
- **Number-collision note:** ADR-0021 is the next free slot (highest accepted is
  ADR-0020; ADR-0014 is WITHDRAWN). Surfacing the collision risk per
  boundary-discipline; Code confirms the number at commit.
- **Governance gate either way:** the chosen ADR must be **Accepted before**
  Phase A's impl PR (CLAUDE.md §8).

### SD-3 — Scoring nl-08 / nl-11 during the transition

- **Question:** while Phase B is in flight, score nl-08 / nl-11 as **2 known
  misses** ("10/12 + 2 known"), or **temporarily reclassify** them to
  `ceiling: true` (the phrase-rescue lens)?
- **Cowork recommendation:** **score as 2 known misses** (the brief's recommended
  default). Phase B is explicitly building them toward passing the **structured
  lens**, so reclassifying to `ceiling:true` and then un-reclassifying is churn
  that *masks* the very gap the structured lens exists to catch, and adds
  integrity noise to the gold set. Keep them as honest known misses until Phase B
  lands, then they pass the structured lens directly.
- **Alternative:** reclassify to `ceiling:true` now (RESULTS.md's earlier
  PENDING-Cray proposal) — defensible per the file's own taxonomy and zero engine
  risk, but it concedes the precision gap Phase B is about to close.
- **Why this is Cray's call:** benchmark-integrity / gold-set classification is
  **Tier 3** (RESULTS.md: "benchmark-integrity is Tier 3").

## Dependencies & governance

- **Phase B is unblocked** — engine, deterministic, offline-validatable, no
  governance gate; it ships first.
- **Phase A is gated** — needs (a) the T2-vs-T3 roadmap go (OQ-1) and (b) its ADR
  (SD-2) **Accepted before** its impl PR (CLAUDE.md §8).
- **`gpt-oss:20b` pin stays** (ADR-001 Amendment 1; digest `17052f91a42e`, Ollama
  0.24.0) — this PLAN changes no model.
- **Minimize live MS-S1 runs** — host-state; AC-9 is optional and runs only on
  Cray's go (by IP `192.168.1.133:11434`, warm first; Lesson #15).
- **Cowork drafts, Code commits** (ADR-009 D1/D2) — no git operation by Cowork.
- **AI-assisted; no `Co-Authored-By`** (CLAUDE.md §7).

## References

- **Evidence:** `benchmarks/nl_query_feasibility/RESULTS.md` (spike + AC-8
  re-verify + the 2026-06-15 4-model-sweep / 3-prompt-escalation addendum);
  `docs/research/private/2026-06-15-ontology-metric-semantics-pattern.md` (the
  two-layer pattern, fully argued — Cowork Tier-0 output);
  `.claude/benchmark-results/2026-06-15-nl-filter-omission-external-consult.md`
  (the two-LLM consult, converged on the data-model root cause);
  `benchmarks/nl_query_feasibility/gold.yaml` + `harness.py` + `run_benchmark.py`
  (gold set, scoring oracle, live harness).
- **Code touched:** `services/engine/nl_query.py` (the new post-translate rewrite
  seam in `answer_question`; `group_by` inference + coherence composition + the
  clarify guard; `NlAnswer` receipt per SD-1; reuse of `_compute_aggregate`,
  `_relabel_groups`, `_no_data_nlanswer`). Phase A:
  `verticals/energy/ontology/energy_v0.yaml`,
  `verticals/energy/data_adapter/synthetic.py`, `_describe_ontology` /
  `_translate_messages`.
- **Tests:** `tests/services/engine/test_nl_query.py` (`_StubQueryClient` offline
  pattern), `tests/benchmark/test_nl_query_feasibility_gold.py`.
- **ADRs:** ADR-008 (D3 enum grammar — the `measured_kind` home / SD-2); ADR-001
  + Amendment 1 (pin stays); ADR-010 (D1 local backend, D4 untrusted containment);
  ADR-005, ADR-006 (OCT / plugin / Rule of Three); ADR-009 D1/D2; ADR-012 D4.3.
  CLAUDE.md §1 (semantic layer = the moat; Rule of Three), §8 (quality bar; ADR
  merged before impl PR). Lessons: #15 (live-vs-mock), the MS-S1 reachability /
  pinned-model note (`gpt-oss:20b` by IP).

---

*PLAN-0026 closes the last NL-query residual (filter-omission on aggregate
superlatives) with a phased two-layer fix: a deterministic engine rewrite seam
(Phase B, ships first) and an ontology `measured_kind` declaration (Phase A,
gated). The fix is structural — both model-swap and prompt-tuning are empirically
falsified. Anti-hallucination 12/12 is a hard gate; synthetic data only; engine
stays single-operator, read-only. SD-1/SD-2/SD-3 are Cray's to adjudicate.*

*Drafted by Cowork (Tier-1 plan-drafter, ADR-009 D1) on Cray's 2026-06-15
dispatch; Code reviews, commits (ADR-009 D2), and executes. AI-assisted; no
`Co-Authored-By` per CLAUDE.md §7.*
