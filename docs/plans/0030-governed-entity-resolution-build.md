# PLAN-0030: Governed entity-resolution build (ADR-0022 member (a))

**Status:** Draft
**Owner:** both (Cowork/Tier-1 authors this PLAN; Code commits + executes per ADR-009 D1/D2)
**Created:** 2026-06-18
**Related ADRs:** ADR-0022 (the ratified construct — F1 = 1-b + 1-c · F2 = 2-c + trace · D3 = α — **THIS PLAN builds member (a)**); ADR-0021 (the "classify, don't synthesize" lineage extended here); ADR-007 (D2 `RecommendedAction` / `EntityRef` envelope — generalised, not broken); ADR-010 (D5 LLM-backed `recommend()`; **IN-4 deterministic fail-safe — not regressed**); ADR-011 (earmarked audit framework — trace interplay **flagged, not designed**); ADR-016 (the governed-engine area this extends); ADR-009 D1/D2 (Cowork drafts, Code commits); ADR-012 D4.3 (author≠reviewer disclosure)
**Related Plans:** PLAN-0029 (entity-key whitespace calibration — its `## Findings` routed this universality investment OUT to "a future ADR + PLAN-0030"); PLAN-0027 / PLAN-0028 (the **D-6 contamination guard** — the binding boundary); PLAN-0006 (§6.6 the LLM path + the retained deterministic fail-safe)

> **Disclosure (ADR-012 D4.3).** Outline originated by **Code** (session-67
> dispatch `.claude/handoffs/session-67/2026-06-18-1210-code-dispatch-plan0030-entity-resolution-build.md`)
> on the **ADR-0022 construct + fork Cray ratified** (2026-06-18). Drafted
> (uncommitted) by **Cowork** (Tier-1, ADR-009 D1). The construct, the gap
> evidence, the resolved fork, and the build scope were **originated in Code's
> dispatch + ADR-0022**, not in a Cowork free-form self-deliberation — so this is
> **not** an ADR-012 D4.3 self-deliberation case (no Cowork opinion is silently
> promoted; the independent-deliberation check is intact). Reviewers: **Cray** at
> ratification + **Code** at PR review. Separation originator (Code) ≠ drafter
> (Cowork) ≠ reviewer (Cray/Code) — **INTACT**. Cowork re-verified every cited
> code line / file / symbol against the live repo this session (fact-pack-first,
> ADR-009 D1 Tier-1 rule #4).

---

## Goal

Build the **entity-resolution slice (ADR-0022 D2 member (a))** per the ratified
fork. Today the LLM path certifies model-named identity verbatim: in
`_compose_llm_record` (`services/engine/recommender.py:160`) the governed
`RecommendedAction` is built with `affected_entities=judgment.affected_entities`
— the model-emitted `EntityRef`s are trusted with **no resolution** against the
vertical's declared object universe (`EntityRef` is a plain Pydantic model with
no validation, `actions.py:27-30`). This PLAN closes that gap on the **LLM path
only**: for each emitted `EntityRef`, **resolve its `primary_key` against the
declared object universe via a 1-b lookup** (the registered vertical
`DataAdapter`'s `fetch_objects`); on a **resolving** PK keep the entity, on a
**non-resolving** PK **fall back to the deterministic `subject_id` anchor**
(the `:265` ground truth — 1-c/2-c) **and write a resolution-outcome trace** so a
model-invented identity is never silently certified (the PDPA-forward invariant,
ADR-0022 F2 / CLAUDE.md §8). It is the **same "classify, don't synthesize" move
ADR-0021 made for measurement kind, now applied to entity identity** — the model
selects against a declared set; code composes the governed identity. Member (b)
verify+reshape stays **forward-declared, NOT built here**.

## Source of truth — ADR-0022 (Accepted 2026-06-18; stated, not re-opened)

The construct **and** the design fork are ratified. This PLAN builds the selected
branches; it does **not** re-decide them:

- **F1 = 1-b** (DB / ontology-object lookup against the declared object universe)
  **primary + 1-c** (the deterministic `subject_id`, `recommender.py:265`) as the
  **fall-back anchor**.
- **F2 = 2-c** (fall back to the deterministic subject on a non-resolving model PK)
  **+ a resolution-outcome trace** (never silently fabricate identity).
- **D3 = α** (one construct; member (a) entity resolution is the buildable slice,
  member (b) verify+reshape forward-declared).
- **Fork 3 = BINDING boundary** — the D-6 contamination guard (see Out of Scope).

## The gap + the anchors (live code, re-verified session 67)

- `services/engine/recommender.py:139-166` — `_compose_llm_record`; **`:160`** sets
  `affected_entities=judgment.affected_entities` (the LLM judgment **verbatim** —
  **THE GAP**, the one line member (a) fixes).
- `services/engine/recommender.py:169-202` — `recommend()` (async); the LLM path,
  with the IN-4 fail-safe `except` that falls back to `_rule_recommend` and
  **never raises into the runtime loop**.
- `services/engine/recommender.py:205-271` — `_rule_recommend`; **`:227`**
  `entity_type = settings.oct_recommend_entity_type`, **`:229`**
  `subject_id = str(event.get(settings.oct_recommend_entity_id_field, "unknown"))`,
  **`:265`** builds `EntityRef(object_type=entity_type, primary_key=subject_id)` —
  grounded in the triggering event; **already universal-correct, the 1-c/2-c
  anchor — do NOT regress or re-open it** (ADR-010 IN-4 / PLAN-0006 §6.6).
- `services/engine/actions.py:27-30` — `EntityRef(object_type, primary_key,
  title?)`, **no validation**; `:42-63` `RecommendedAction` (`affected_entities`
  at `:52`, `reasoning_trace` at `:50`); `:33` `AuditMetadata` ("expanded in
  future audit-framework ADR").
- `services/engine/llm/structured.py:98-102` — `LlmJudgment.affected_entities:
  list[EntityRef]` (what the model emits); `:250-269` `_semantic_errors` already
  iterates `affected_entities` and rejects an **empty** `primary_key`
  (`:266-267`) — the existing per-entity seam, which this PLAN extends from
  "non-empty" to "resolves against the declared universe".

### Where the declared universe is reachable at recommend-time (decided — see Design points D-1)

- `services/engine/registry.py:62-67` — `registry.get_adapter(vertical)` returns
  the vertical's registered `DataAdapter`.
- `services/engine/data_adapter.py:36-43` — `DataAdapter.fetch_objects(object_type,
  filter_expr=None, limit=1000) -> list[dict[str, Any]]` — the per-vertical data
  ingress (ADR-007 D1); the engine maps the raw dicts to typed entities via the
  ontology.
- `services/engine/ontology_meta.py:46` — `ObjectTypeMeta.primary_key: str | None`
  — the PK field name per object type (used to extract each instance's key from
  the raw dict for matching).
- `services/db/persistence.py:9-10` — Phase-2 note: **"assets are served from the
  synthetic adapter, not the database"** — so the universe source is the adapter,
  not a `services/db/` read (D-1).

## Decided design points (ADR-0022's three flagged open details — now specified)

ADR-0022 flagged three details for PLAN-0030 to specify (dispatch §5). Resolved:

- **D-1 — The exact 1-b lookup source: the registered `DataAdapter.fetch_objects`,
  not a direct `services/db/` read.** Rationale: it is the engine's existing
  per-vertical declared-universe ingress (ADR-007 D1), keyed uniformly through the
  registry so it generalises across verticals (Rule of Three); it avoids coupling
  the recommender to `services/db/` (which Phase 2 does not even populate with
  assets — `persistence.py:9-10`); freshness/staleness is the adapter's own live
  read (no recommender-side cache to invalidate). **Latency** (the cost ADR-0022
  Fork-1 flagged): one `fetch_objects(object_type)` per **distinct** object type in
  the judgment, **deduped + memoised within a single `recommend()` call** (Step 2).
  A DB-backed object store is deferred until a vertical's adapter is DB-backed
  (not this PLAN).
- **D-2 — Resolution-outcome marker shape: a structured `ReasoningStep` in
  `reasoning_trace` by default; an optional `EntityRef.resolution` field is
  SD-1 (Cray/Code).** The trace step alone satisfies the PDPA-forward requirement
  and keeps the ADR-007 D2 `EntityRef` envelope untouched and the `LlmJudgment`
  model schema clean. Adding a field to `EntityRef` touches the shared contract
  that persistence + the future UI consume, so it is surfaced (SD-1), not silently
  chosen — the trace-only default is fully buildable without that decision.
- **D-3 — Where the trace lands: `RecommendedAction.reasoning_trace` only, NOT
  `AuditMetadata`.** `AuditMetadata` (`actions.py:33`) is ADR-011's earmarked
  surface; this PLAN emits a **minimal** trace and **flags** (does not design) the
  audit-framework interplay.

## Acceptance Criteria

- [ ] **AC-1 — Resolution on the LLM path (the construct).** Before the governed
      `RecommendedAction` trusts `judgment.affected_entities`
      (`recommender.py:160`), each emitted `EntityRef`'s `primary_key` is
      **resolved against the vertical's declared object universe**: fetch the
      declared instances for the `EntityRef.object_type` via the registered
      `DataAdapter.fetch_objects` (D-1), extract each instance's key via the
      object type's `ObjectTypeMeta.primary_key`, **normalize-then-match**
      (recover-only / never-invent).
- [ ] **AC-2 — A resolving PK is kept.** A model-emitted `EntityRef` whose
      normalized `primary_key` matches a declared instance is **kept**, carrying
      the **canonical** declared key (the governed record certifies a real,
      declared identity). The outcome `resolved` is recorded (AC-4).
- [ ] **AC-3 — A non-resolving PK falls back + traces (PDPA-forward invariant).**
      A model-emitted `EntityRef` whose `primary_key` does **not** resolve is
      replaced by the **deterministic subject anchor** —
      `EntityRef(object_type=settings.oct_recommend_entity_type,
      primary_key=str(event.get(settings.oct_recommend_entity_id_field,
      "unknown")))`, the **same** event-grounded source the `:265` fail-safe uses
      — **and** a resolution-outcome trace step records that the model PK did not
      resolve and the fall-back was applied. The model-invented PK is **never**
      certified as a real entity.
- [ ] **AC-4 — Minimal, structured resolution-outcome trace.** Each entity's
      outcome (`resolved` | `fallback`) is recorded as a `ReasoningStep`
      (`kind="entity_resolution"`) appended to `RecommendedAction.reasoning_trace`,
      with **machine-readable** `detail` (the emitted PK, the outcome, and on
      fall-back the substituted subject). The trace lands in `reasoning_trace`
      **only**; `AuditMetadata` is **not** designed here (D-3).
- [ ] **AC-5 — The deterministic fail-safe is untouched + converged.**
      `_rule_recommend` (`:265`) behaviour is **unchanged**; the LLM-path
      fall-back converges on the **same** event-grounded subject anchor — reuse,
      not duplicate (ADR-0022 / dispatch §3.4). [Shared-helper extraction vs.
      duplicate = SD-2.]
- [ ] **AC-6 — D-6 contamination boundary (BINDING non-goal).** The resolution
      lives in the governed-product recommender path **only**. **No** resolution /
      ontology / governance logic is added to the arm-(c) naive-RAG baseline
      (`benchmarks/procedure_comparison/`); the benchmark `normalize_primary_key`
      is **not** imported into `services/`, and the new product normalizer is
      **not** imported into the benchmark (PLAN-0027 D-6 / PLAN-0028).
- [ ] **AC-7 — The envelope is not broken.** The ADR-007 D2 `RecommendedAction` /
      `EntityRef` shapes stay backward-compatible; any marker added under SD-1 is
      **optional with a default**; the `LlmJudgment` sub-schema the model emits is
      **not** forced to carry a resolution-owned field.
- [ ] **AC-8 — Quality bar (CLAUDE.md §8), contract-covering, offline.** Type
      hints + tests + **ruff clean + `mypy --strict` clean**. Tests cover the
      **contract**, fully **offline** (monkeypatch the registered adapter + the
      chat client; no live Ollama, no host-state): (i) a resolving PK is kept with
      the canonical key; (ii) a non-resolving PK → fall-back to `subject_id` + an
      `entity_resolution` trace step; (iii) the **never-invent negative** — a
      well-formed but non-existent PK is **not** certified; (iv) a mixed
      multi-entity judgment (some resolve, some fall back); (v) a resolution-path
      error falls through to the deterministic fail-safe (IN-4 intact); (vi) the
      full `uv run pytest -q` suite stays green (baseline stated at execution).

## Out of Scope

- ❌ **Member (b) verify+reshape** — forward-declared only (ADR-0022 D2(b)); the
  §3.4 / §B-3 pointer. PLAN-0030 = **member (a) only**.
- ❌ **Touching / regressing the deterministic fail-safe** (`recommender.py:265`)
  — behaviour unchanged; at most a **behavior-preserving** shared-anchor extract
  if SD-2 is approved.
- ❌ **Leaking resolution into the arm-(c) naive-RAG baseline** — the D-6
  contamination guard (BINDING; AC-6).
- ❌ **Designing the audit framework / expanding `AuditMetadata`** (ADR-011
  earmarked) — emit a **minimal** trace only; flag the interplay (D-3).
- ❌ **`EntityRef` shape/format validation as the mechanism** (ADR-0022
  Alternative 3) — resolution against the declared **set** is the construct, not a
  regex/format constraint on the key (a shape constraint is at most an optional
  belt-and-suspenders, not built here).
- ❌ **A `services/db/` object-store read path** for the universe (Phase 2 serves
  assets from the adapter, not the DB) — the lookup goes through the registered
  `DataAdapter`; a DB-backed universe is deferred until a vertical's adapter is
  DB-backed.
- ❌ **Vertical #3/#4, UI work, NL-query** — PLAN-0030 is the **engine slice
  only**.

## Steps

Ordered, each small and reviewable (normalizer → lookup → fall-back/trace → wire
→ marker → tests → gate → handback).

### Step 1 — Product-side key normalizer (in `services/`)

Add a small **recover-only** normalizer in `services/engine/` (e.g. a new
`entity_resolution.py`, or a private helper beside the recommender) that
normalizes a `primary_key` for **comparison only** — case-fold + map the Unicode
hyphen and whitespace-as-separator families to ASCII, mirroring the Cray-ratified
calibration standard (recover-only / **never-invent**: it can only recover a
correctly-named key, never invent one). **Do NOT import** the benchmark grader's
`normalize_primary_key` (`benchmarks/procedure_baseline/grader.py`) — that would
breach D-6 (AC-6). Unit-test a positive (a case/whitespace variant resolves) + a
negative (a genuinely wrong key still fails). (AC-1, AC-6, AC-8)

### Step 2 — The 1-b lookup against the declared universe

Add an async resolver (e.g. `async def _resolve_affected_entities(event, vertical,
judgment) -> tuple[list[EntityRef], list[ReasoningStep]]`). For each emitted
`EntityRef`: get `adapter = registry.get_adapter(vertical)`; fetch the declared
instances `await adapter.fetch_objects(entity.object_type)`; read each instance's
key via the object type's `ObjectTypeMeta.primary_key` (`ontology_meta.py:46`);
normalize both sides (Step 1) and match. **Dedup + memoise `fetch_objects` per
object type within a single `recommend()` call** to bound the recommend-time read
cost (the ADR-0022 Fork-1 latency flag). On a match → keep the `EntityRef` with
the **canonical** declared key. (AC-1, AC-2, D-1)

> *Implementation note (Code to confirm):* the exact dict key under which
> `fetch_objects` returns each instance's PK (the synthetic adapter's convention
> for the ontology `primary_key` property) — confirm against
> `verticals/<name>/data_adapter/` at build time; the resolver reads it via
> `ObjectTypeMeta.primary_key`, not a hard-coded field name.

### Step 3 — Non-resolving fall-back to the deterministic subject + trace

On no match, substitute the deterministic subject anchor —
`EntityRef(object_type=settings.oct_recommend_entity_type,
primary_key=str(event.get(settings.oct_recommend_entity_id_field, "unknown")))`,
the **same** source `_rule_recommend` uses at `:227`/`:229`/`:265` (reuse via a
shared helper per SD-2; do **not** duplicate the grounding — dispatch §3.4).
Append a `ReasoningStep(kind="entity_resolution", ...)` whose `detail` records the
emitted PK, the outcome (`fallback`), and the substituted subject. **Never**
certify the unresolved model PK. (AC-3, AC-4, AC-5)

### Step 4 — Wire into the LLM path (async-correct)

Resolution does async I/O (`fetch_objects`), so run it inside the already-async
`recommend()` (`:181-188`): resolve `judgment.affected_entities` → pass the
resolved list **and** the resolution trace steps into `_compose_llm_record` (or
make `_compose_llm_record` async and await the resolver there — Code's call, an
internal refactor, not a contract change). Replace the `:160`
`affected_entities=judgment.affected_entities` verbatim assignment with the
**resolved** list, and merge the resolution `ReasoningStep`s into the record's
`reasoning_trace`. **Keep the IN-4 fail-safe intact** — a resolution exception must
fall through the `recommend()` `except` to `_rule_recommend`, never raise into the
loop (ADR-010 IN-4 / PLAN-0006 §6.6). (AC-1, AC-4, AC-8)

### Step 5 — Resolution-outcome marker shape (implements SD-1)

Implement the marker decided in **SD-1**: the trace `ReasoningStep` is the default
(no envelope change). **If** Cray/Code approve the optional `EntityRef.resolution`
field, add it **backward-compatibly** (`Optional`, default `None`) **without**
forcing it into the `LlmJudgment` model schema the LLM emits. (AC-4, AC-7)

### Step 6 — Offline tests (the contract)

Add offline tests (monkeypatch the registered adapter + the chat client — extend
the existing stub patterns in `tests/services/engine/`; no live Ollama, no
host-state): a resolving PK kept (canonical key); a non-resolving PK →
fall-back to `subject_id` + an `entity_resolution` trace step; the **never-invent
negative**; a mixed multi-entity judgment (resolve + fall-back); a resolution
error → deterministic fail-safe. Assert on the returned envelope + trace, never on
incidental shape. (AC-2, AC-3, AC-5, AC-8)

### Step 7 — Gate + suite green

`ruff` + `mypy --strict` clean; full `uv run pytest -q` green against the current
baseline (state it at execution). (AC-8)

### Step 8 — Handback → Code commits + executes

Hand the uncommitted draft path back to Code. Code reviews, commits this PLAN via
a `docs(plans):` chore PR (ADR-009 D2; CLAUDE.md §7), executes member (a) on a
`feat/*` branch + PR (**gated on ADR-0022 Accepted — satisfied, #361**),
reconciles `docs/STATUS.md`, then on completion
`git mv docs/plans/0030-*.md docs/plans/done/`.

## Verification

- **Contract (AC-2/AC-3/AC-5):** offline tests show (i) a resolving PK kept with
  the canonical declared key; (ii) a non-resolving PK falls back to the event
  `subject_id` (byte-identical to the `:265` anchor) with an `entity_resolution`
  trace step; (iii) a well-formed non-existent PK is never certified; (iv) the
  deterministic fail-safe still grounds at `subject_id`; (v) a resolution error
  routes to `_rule_recommend` (IN-4 intact).
- **D-6 (AC-6):** a grep shows **no** cross-import between
  `benchmarks/procedure_comparison/` (and `…/procedure_baseline/`) and the new
  `services/` resolver; the arm-(c) baseline is unchanged.
- **Envelope (AC-7):** ADR-007 D2 shapes backward-compatible; the `LlmJudgment`
  schema is not forced to carry a resolution field.
- **Gate (AC-8):** `ruff` + `mypy --strict` clean; `uv run pytest -q` green.
- **No host-state run at any point.** The build + tests are offline-only. An
  optional live MS-S1 re-verify, if ever wanted, is a **separate Cray-gated
  verification-not-gate** step (CLAUDE.md §8 host-state ASK-Cray; Lesson #15) —
  **not** required by this PLAN.

## Surfaced decisions (SD-N) — for Cray to adjudicate

- **SD-1 — Resolution-outcome marker shape (D-2 / AC-4 / Step 5). [Cowork
  recommends: trace `ReasoningStep` only.]**
  *Question:* record the outcome (a) **only** as a
  `ReasoningStep(kind="entity_resolution")` in `reasoning_trace` (envelope
  untouched), or (b) **also** add an optional `EntityRef.resolution` marker field
  (`resolved` | `fallback`)?
  *Cowork recommendation:* **(a)** — it satisfies the PDPA-forward "never silently
  fabricate" requirement, keeps the ADR-007 D2 `EntityRef` contract untouched, and
  keeps the `LlmJudgment` model schema clean (the model never emits a resolution
  field).
  *Why this is a Cray/Code decision, not a Cowork judgment call:* adding a field to
  `EntityRef` changes the **shared ADR-007 D2 envelope** that persistence
  (`services/db/`) and the future UI consume — a contract decision (mirrors
  PLAN-0024 SD-1). The trace-only default is fully buildable now without it.

- **SD-2 — Shared subject-anchor helper vs. duplicate (AC-5 / Step 3). [Cowork
  recommends: shared helper.]**
  *Question:* to converge the LLM-path fall-back on the deterministic `:265`
  subject anchor, (a) extract a shared helper (e.g. `_event_subject_ref(event)`)
  called by **both** `_rule_recommend` (`:265`) and the new resolver, or (b)
  duplicate the two-line expression in the LLM path and pin convergence with a
  test?
  *Cowork recommendation:* **(a)** — it guarantees the two paths cannot drift
  (dispatch §3.4 "reuse, do not duplicate") and the extract is behavior-preserving
  (covered by the existing `_rule_recommend` tests).
  *Flag (surface, do not silently choose):* **(a) edits the `:265` line** (a
  refactor-only, behavior-identical change). The dispatch + ADR-0022 say **do NOT
  regress or re-open** the fail-safe — a behavior-preserving extract is not a
  regression, but because the instruction is emphatic, **Cray/Code adjudicate**
  whether even a refactor-only touch of `:265` is acceptable; else fall to (b).

## References

- **ADR-0022 (Accepted)** `docs/adr/0022-governed-entity-resolution.md` — D1/D2/D3,
  the resolved Design fork (F1 = 1-b + 1-c · F2 = 2-c + trace · D3 = α),
  Constraints/guardrails, Alternatives 3 (shape-only) + 4 (always-collapse).
- **The gap + anchors (live code, re-verified this session):**
  `services/engine/recommender.py:139-166` (`_compose_llm_record`; `:160` the
  trusted line), `:169-202` (`recommend` + the IN-4 fail-safe), `:205-271`
  (`_rule_recommend`; `:227`/`:229` the subject source, `:265` the grounded
  anchor); `services/engine/actions.py:27-30` (`EntityRef`, no validation), `:33`
  (`AuditMetadata`), `:42-63` (`RecommendedAction`; `affected_entities` `:52`,
  `reasoning_trace` `:50`); `services/engine/llm/structured.py:98-102`
  (`LlmJudgment.affected_entities`), `:250-269` (`_semantic_errors`, the per-entity
  seam).
- **The declared-universe surface:** `services/engine/registry.py:62-67`
  (`get_adapter`); `services/engine/data_adapter.py:36-43`
  (`DataAdapter.fetch_objects`); `services/engine/ontology_meta.py:46`
  (`ObjectTypeMeta.primary_key`); `services/db/persistence.py:9-10`
  (assets are adapter-served in Phase 2).
- **Lineage + guardrails:** ADR-0021 (classify, don't synthesize); ADR-007 D2
  (the envelope, generalised not broken); ADR-010 IN-4 / PLAN-0006 §6.6 (the
  deterministic fail-safe — do not regress); PLAN-0027 D-6 / PLAN-0028 (the
  contamination guard); ADR-011 + `actions.py:33` (audit interplay, flagged only);
  CLAUDE.md §1 (semantic layer = the moat), §6 (Decision/Plan Flow), §8
  (PDPA-forward; ADR-Accepted-before-impl; host-state ASK-Cray); ADR-009 D1/D2;
  ADR-012 D4.3.
- **Dispatch + roadmap:** `.claude/handoffs/session-67/2026-06-18-1210-code-dispatch-plan0030-entity-resolution-build.md`;
  `.claude/handoffs/session-67/2026-06-18-0938-code-session67-roadmap-sequencing-handoff.md`;
  PLAN-0029 `## Findings → follow-up`
  (`docs/plans/done/0029-entity-key-whitespace-calibration-and-regrade.md`).

---

*PLAN-0030, the entity-resolution build (ADR-0022 member (a) — the universality
lever). Drafted by Cowork (Tier-1, ADR-009 D1); Code reviews, commits (ADR-009
D2), and executes; Cray ratifies. Synthetic data only; engine slice only; the
deterministic fail-safe (`:265`) is untouched; the D-6 boundary is BINDING;
offline-only build (no host-state). AI-assisted (Claude, Cowork session); no
`Co-Authored-By` per CLAUDE.md §7.*
