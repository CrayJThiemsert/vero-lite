# PLAN-0024: NL-query T2 engine enrichment (engine-A grounded + richer StructuredQuery — pieces 1+2, engine-only)

**Status:** Proposed
**Owner:** both (Cowork/plan-drafter authors this PLAN; Code commits + executes)
**Created:** 2026-06-14
**Related ADRs:** ADR-005 (OCT pivot — energy first); ADR-006 (vertical plugin architecture / template-first); ADR-010 (LLM brain-swap — local Ollama + deterministic fail-safe); ADR-009 D1/D2 (Cowork/plan-drafter drafts, Code commits); ADR-012 D4.3 (author≠reviewer disclosure)
**Related Plans:** PLAN-0013 (OCT stakeholder demo — shipped the engine-A NL-query path this PLAN enriches, done); **PLAN-0025 (the UI shell — A1 operational-map + A2 approval/review screen — deferred, future)**

> **Disclosure (ADR-012 D4.3).** Outline originated by Code (session-59 drafting
> brief, on the session-58 feasibility-spike evidence); drafted by the in-harness
> `plan-drafter` subagent under ADR-013 D1 phased authority; independent reviewer
> = Cray at PR merge. Separation INTACT.

---

## Goal

Build the **engineering half of the T2 (NL-query) roadmap direction** that Cray
ratified in session 58 on the feasibility-spike evidence (the partner-trial fork
T2-NL-query vs T3-real-data was resolved to **T2**). This PLAN delivers the
**engine-only** build — **two pieces, no UI**: (1) **enrich the
`StructuredQuery`** in `services/engine/nl_query.py` with deterministic
**aggregates (MAX / MIN / AVG / SUM, with group-by)** and **cross-type
name→id resolution** (the "join" gap), closing the architecture ceiling the
spike found; and (2) **fix the translate prompt** so it emits the filter the
question implies (killing the whole-table fetch) and grounds question terms to
the actual enum values. Both pieces preserve, without exception, the
deterministic grounded-execute path and the **empty → fixed no-data answer →
no invention** short-circuit. The non-negotiable hard gate is that the spike's
**12/12 anti-hallucination result holds**. The UI shell is deliberately
**deferred to PLAN-0025** — this PLAN ships an enriched, well-tested engine and
an offline regression oracle, not a screen.

## The load-bearing architecture decision (Cray-ratified — stated, not re-opened)

The target T2 is **engine-A's grounded-execute safety + a richer
`StructuredQuery`** (joins + aggregates) — **NOT** a switch to raw text-to-SQL.
The session-58 text-to-SQL comparison arm proved the trade is not worth it:
text-to-SQL scored 11/12 but **lost the anti-hallucination guard** (on nl-12 it
improvised an alarm event for a no-data alerts question — a quiet
hallucination-by-substitution). The spike's own read is binding here: *"the
ceiling is ARCHITECTURE, not the model"* (enriching `StructuredQuery` clears the
join/aggregate ceiling the local model is already capable of) and *"the
filter-omission is PROMPT, not the model"* (under SQL framing the same model
wrote a `WHERE` every time). Therefore:

- The new capabilities (aggregates, joins) **MUST** be computed in the
  **deterministic execute stage** (exactly as `count` is today via
  `_matches` / `_filter_matches`), **NOT** delegated to the phrase LLM. The
  spike showed phrase-rescue of max/avg (nl-08 / nl-10) is real but **brittle**:
  it breaks the moment translate over-specifies into an empty set (nl-11,
  `unit="C"` ≠ `"celsius"` → empty → unrescuable).
- The "empty → fixed no-data answer → no invention" guarantee is preserved
  throughout. This is the credibility asset, not a caveat.

This decision is **not open** in this PLAN. Do not re-surface text-to-SQL or
engine-B.

## Evidence base

This PLAN is built on, and must be read against, two artifacts:

- **`benchmarks/nl_query_feasibility/RESULTS.md`** — the session-58 spike verdict
  + the text-to-SQL comparison arm. Headline (verified against the `--dump-json`
  records): engine-A **8/12 structured** (~10/12 operator-answer),
  **anti-hallucination 12/12 (zero invented facts)**; text-to-SQL 11/12 but
  **lost** the anti-hallucination guard (nl-12). Findings 1–4 are the direct
  driver of the two build pieces (filter-omission = the #1 translate error;
  join-by-name = a hard ceiling that fails *safely*; phrase-rescue of
  aggregates is real but brittle; anti-hallucination held perfectly).
- **`services/engine/nl_query.py`** — the SHIPPED engine-A path (PLAN-0013).
  Current shape this PLAN enriches: `StructuredQuery` = single `object_type`
  (enum-constrained to the live ontology), `operation: Literal["list","count"]`,
  `filters: list[QueryFilter]` (conjunctive AND), `limit: int`. **Single
  object-type, no join, the only aggregate is `count`.** Three-stage flow:
  **translate** (LLM, schema-constrained via Ollama `format` + validate-and-retry)
  → **execute** (DETERMINISTIC, no LLM — `_matches` / `_filter_matches`; an empty
  result short-circuits to `_no_data_answer`) → **phrase** (LLM, uses ONLY
  retrieved records as untrusted DATA, deterministic fallback on LLM failure).

The 12-question gold set (`benchmarks/nl_query_feasibility/gold.yaml`) + the
scoring harness (`benchmarks/nl_query_feasibility/harness.py`) are reused as the
acceptance / regression oracle.

## Acceptance Criteria

- [ ] **AC-1 — Aggregates computed deterministically (execute stage).**
  `StructuredQuery.operation` gains **MAX / MIN / AVG / SUM** (alongside the
  existing `list` / `count`), each computed in the **deterministic execute
  stage** — no LLM — and carried in the grounding receipt (the returned
  `NlAnswer`), exactly as `count` is today. **Group-by** is supported (an
  aggregate over a grouping property returns a per-group result). The spike's
  **nl-08** (max temp, expects `96.5` on `Battery Bank A`) and **nl-10** (avg
  temp across Battery Bank B's readings, expects `41.3`) pass via **deterministic
  compute, not phrase-rescue** — the aggregate value appears in the grounding
  receipt, not only in the phrased prose.
- [ ] **AC-2 — Cross-type name→id resolution (the join gap).** An entity *name*
  (e.g. `"Battery Bank A"`) resolves to its *id* so cross-type questions
  ("events for Battery Bank A") execute against the correct foreign-key value —
  via a **name→id resolve pre-step** *or* a name filter that resolves across
  types (SD-1 below picks the mechanism). The spike's **nl-09** (join-count,
  true answer **5** events for Battery Bank A) and **nl-11** (entity-superlative,
  true answer **Battery Bank A** running hottest) — which today fail **safely to
  empty** — return the **correct non-empty result**.
- [ ] **AC-3 — Filter-omission eliminated (translate prompt).** The translate
  prompt requires the filter the question implies. The whole-table-fetch /
  filter-omission error (the #1 engine-A failure mode — nl-01, nl-07, and the
  no-filter half of nl-08) is gone: nl-01 emits `asset_type=battery` (→ the 2
  batteries) and nl-07 emits `site_type=microgrid` (→ the 1 microgrid site)
  rather than a no-filter whole-table read.
- [ ] **AC-4 — Enum / value grounding (translate prompt).** A question term is
  mapped to the actual enum / property value during translate, so single-token
  mismatches resolve: a question phrased with `"C"` (or "celsius") resolves to
  the data's actual value `"celsius"`, and "Celsius" / unit phrasings no longer
  emit `unit="C"` → empty (the nl-11 failure cause).
- [ ] **AC-5 — Anti-hallucination preserved (THE hard gate — non-negotiable).**
  The spike's **12/12 holds**. Every no-data question still returns the honest
  deterministic no-records answer (`grounded=false`); **zero invented facts**
  across every failure mode, including the new aggregate / join paths (an
  aggregate over an empty set short-circuits to the no-data answer — it never
  invents a number; a name→id resolve that finds no entity yields the honest
  no-records answer, never a fabricated row). nl-12 ("list all open alerts",
  no Alert data) still returns the deterministic "No Alert records" answer.
  **This is a gate, not a nice-to-have** — if it cannot be held, the offending
  capability is not shipped.
- [ ] **AC-6 — Quality bar (CLAUDE.md §8).** All new code carries type hints +
  tests + **ruff clean + mypy clean**. Tests are **offline** — they monkeypatch
  the chat client exactly as the existing `tests/services/engine/test_nl_query.py`
  does (the `_StubQueryClient` pattern: a `response_format` call = translate, a
  bare call = phrase), so there is **no live-LLM dependency in the suite**. The
  deterministic execute-stage logic (aggregate compute, group-by, name→id
  resolution) is fully unit-tested with no LLM at all.
- [ ] **AC-7 — Regression green.** The full `uv run pytest -q` suite stays green
  (last broad green baseline: **1481 passed / 22 skipped**). No existing
  `nl_query` test regresses; the offline gold-scoring test
  (`tests/benchmark/test_nl_query_feasibility_gold.py`) is updated for the new
  aggregate / resolved-join expectations and stays green.
- [ ] **AC-8 — (Optional, MANUAL verification step — not an offline unit test).**
  A **live** re-run of the 12-question harness against `gpt-oss:20b` @ MS-S1
  (`192.168.1.133:11434`) confirms the **structured-result lens improves from
  8/12** while **anti-hallucination stays 12/12**. This is host-state / manual
  (Lesson #15 live-vs-mock; the live harness is driven by `run_benchmark.py`,
  never the offline suite) and is a **verification step, not a CI gate**.

## Out of Scope

- ❌ **The UI shell** — A1 operational-map + A2 approval/review screen are
  **deferred to PLAN-0025**. This PLAN ships engine + tests + oracle only. **See
  Open Question OQ-1** (the UI-approach choice is left open for that future PLAN —
  do not resolve it here).
- ❌ **Switching to raw text-to-SQL** — explicitly **rejected** (see "the
  load-bearing architecture decision"); the spike proved it trades away the
  12/12 anti-hallucination guard. Not built, not re-opened.
- ❌ **Agentic NL→tool-call (engine B / "option B")** over `mcp_tools.json` —
  remains **deferred** (OQ-3, carried from PLAN-0013). Engine A only.
- ❌ **Multi-operator or write / mutating queries** — the engine stays
  **single-operator, read-only** (the PLAN-0013 / `nl_query.py` boundary is
  preserved).
- ❌ **Delegating the new aggregate / join compute to the phrase LLM** — the new
  capabilities are computed in the deterministic execute stage by construction
  (the architecture decision). Phrase-rescue is not the mechanism.
- ❌ **A new ontology / new vertical / a meta-framework** — this enriches the
  existing `StructuredQuery` over the existing ontology (Rule-of-Three guard,
  CLAUDE.md §1); no new abstraction layer.

## Steps

Ordered, each step small and reviewable (schema/model → execute-stage compute →
translate-prompt → tests → suite green → optional live re-verify).

### Step 1 — Extend the query model (schema + validation)

Extend `StructuredQuery` in `services/engine/nl_query.py`:
- Add the aggregate operations to `QueryOperation`:
  `Literal["list", "count", "max", "min", "avg", "sum"]`. An aggregate operation
  carries the **target property** it aggregates (e.g. `measured_value`) and an
  **optional group-by property**. Keep the field additions backward-compatible
  (defaults that reduce to today's `list` / `count` behavior).
- Add the structural slots for cross-type resolution per the SD-1 mechanism
  Cray picks (a name→id resolve pre-step descriptor, or a name-filter that the
  executor resolves across types). Keep `object_type` single and
  enum-constrained — the join is a **resolve-then-filter**, not a multi-type
  query language.
- Extend `_query_schema` / `_validate_query` so the new operation + aggregate
  target + group-by + resolve descriptor are **semantically checked against the
  live ontology** (aggregate target must be a numeric property of the type;
  group-by must be a real property; a resolve target must be a real cross-type
  ref). Constrained generation still cannot target a non-existent type/property.
  Surface any violation through the existing validate-and-retry feedback loop.

### Step 2 — Deterministic aggregate compute in the execute stage (AC-1)

In the execute stage (the `answer_question` retrieval block + helpers — *no LLM*):
- After `matched = [obj for obj in objects if _matches(...)]`, branch on
  `operation`: for `max` / `min` / `avg` / `sum`, compute the aggregate over the
  matched objects' target property using the existing numeric coercion
  (`_to_number`), with **group-by** producing a per-group mapping. Reuse the
  `_to_number` tolerance already proven by `count`/numeric filters.
- Carry the computed aggregate (and per-group breakdown) in the returned
  `NlAnswer` grounding receipt — add the field(s) needed so the aggregate is a
  **first-class grounded fact**, not prose. The phrase step then phrases the
  *already-computed* value (it never computes it).
- **Preserve the empty short-circuit:** an aggregate over an empty matched set
  goes to `_no_data_answer` — it must never emit `0` / `NaN` / an invented
  number (AC-5). Extend `_fallback_answer` so the deterministic phrasing path
  also reports the aggregate when the LLM is down.
- Add the nl-08 / nl-10 targets to the deterministic path: nl-08 `max` over
  celsius readings → `96.5`; nl-10 `avg` over Battery Bank B's readings →
  `41.3`, **both produced by execute-stage compute**, verifiable in the receipt.

### Step 3 — Cross-type name→id resolution (AC-2)

Implement the SD-1 mechanism (after Cray ratifies it):
- Resolve an entity **name** to its **id** against the target type (e.g.
  `"Battery Bank A"` → `asset-battery-01`) using the ontology's `title_key` /
  `primary_key` metadata already in `ObjectTypeMeta`, then apply the resolved id
  as the foreign-key filter on the queried type (e.g. `asset_id=asset-battery-01`
  on `OperationalEvent`). Keep the resolve **deterministic** (a name lookup over
  fetched objects, not an LLM call).
- **Fail safe, not silent-wrong:** a name that resolves to nothing yields the
  honest no-records answer (`grounded=false`) — never a fabricated match (AC-5).
- Targets: nl-09 (count events for Battery Bank A → **5**) and nl-11
  (which battery is hottest → **Battery Bank A**, via resolve + the Step-2
  per-entity `max`/group-by) both return the correct non-empty result.

### Step 4 — Translate-prompt fix: require-the-filter + enum grounding (AC-3, AC-4)

In `_translate_messages` (the system prompt is the lever — the spike proved this
is a **prompt** fix, not a model limit):
- **Require the filter the question implies.** Strengthen the instruction so the
  model does not emit a bare object_type / whole-table read when the question
  names a property condition. Keep the existing "if it asks about everything of
  a type, use no filters" escape so genuine all-of-type questions still work.
  Target the spike's nl-01 / nl-07 / nl-08 filter-omission.
- **Enum / value grounding.** The ontology description handed to the model
  (`_describe_ontology`) already lists enum values (`enum: a|b|c`); extend the
  prompt to instruct the model to **map question terms to those exact enum /
  property values** ("celsius" / "C" → the data's `"celsius"`), and lean on the
  validate-and-retry loop to correct a near-miss. Do **not** weaken the
  case-insensitive equality the executor already does — this is belt-and-braces
  at the translate boundary.
- Keep the IN-2 / ADR-010 D4 untrusted-block containment intact (the operator
  question stays labelled untrusted DATA; no instruction-following from it).

### Step 5 — Offline tests (AC-6)

Extend `tests/services/engine/test_nl_query.py` (and the gold-scoring test) using
the **existing offline pattern** — monkeypatch the chat client via the
`_StubQueryClient` (a `response_format` call returns the translate JSON; a bare
call returns the phrase), **no live Ollama**:
- **Execute-stage unit tests (no LLM at all):** aggregate compute (max / min /
  avg / sum), group-by, name→id resolution, and the empty-set short-circuit for
  each new operation (the AC-5 guard at the unit level).
- **Translate tests:** a stub that emits a no-filter query for a
  filter-implying question is corrected (or the prompt-driven expectation is
  asserted via the stub's recorded messages); enum-grounding near-miss
  (`unit="C"`) resolves to the matched set.
- **End-to-end `answer_question` tests:** nl-08, nl-09, nl-10, nl-11, nl-12
  shapes — assert on the returned `NlAnswer` (grounding receipt + answer
  substrings + `grounded` flag), never on incidental shape.

### Step 6 — Update the gold-scoring oracle + full suite green (AC-7)

- Update `benchmarks/nl_query_feasibility/gold.yaml` / the offline gold test
  (`tests/benchmark/test_nl_query_feasibility_gold.py`) so the four
  now-expressible cases (nl-08, nl-09, nl-10, nl-11) are scored on the
  **deterministic executed result** (they move off `ceiling: true` phrase-rescue
  onto the structured-result lens where appropriate), while nl-12 stays the
  honesty probe (`expected_grounded: false`).
- Run `uv run pytest -q`; confirm the full suite stays green against the
  **1481 passed / 22 skipped** baseline (AC-7). Run `ruff` + `mypy` clean (AC-6).

### Step 7 — (Optional, MANUAL) live harness re-verify (AC-8)

Host-state / manual, **not** part of the offline suite (Lesson #15): re-run the
12-question harness live against `gpt-oss:20b` @ MS-S1 via `run_benchmark.py`
(warm the model first; reach by IP `192.168.1.133:11434`, not hostname). Confirm
the **structured-result lens improves from 8/12** and **anti-hallucination stays
12/12**. Record the verdict as evidence; this step gates nothing in CI.

### Step 8 — Handback → Code commits + reconciles

Hand the uncommitted draft path(s) back to Code. Code reviews, commits on a
`feat/*` branch + PR per CLAUDE.md §7 (plan-drafter does **not** commit —
ADR-009 D2), merges after Cray review, executes the steps, then reconciles
STATUS. On completion `git mv docs/plans/0024-*.md docs/plans/done/`.

## Verification

- **AC-1 / AC-2:** offline `answer_question` tests show nl-08 (`96.5`,
  Battery Bank A) and nl-10 (`41.3`) carry the aggregate **in the grounding
  receipt** (deterministic, not phrase-only); nl-09 (`5`) and nl-11
  (Battery Bank A) return the correct **non-empty** result via name→id resolve.
- **AC-3 / AC-4:** translate tests show nl-01 → `asset_type=battery`, nl-07 →
  `site_type=microgrid` (no whole-table fetch); a `"C"`/"celsius" term resolves
  to the matched set rather than empty.
- **AC-5 (the gate):** every no-data path — nl-12, an empty aggregate, an
  unresolved name — returns `grounded=false` + the deterministic no-records
  answer with **no invented fact**, asserted at both unit and end-to-end level.
- **AC-6 / AC-7:** `uv run pytest -q` green at the 1481/22 baseline; `ruff`
  clean; `mypy` clean; all NL-query tests offline (no live Ollama).
- **AC-8 (optional, manual):** the live 12-question harness shows the
  structured-result lens > 8/12 with anti-hallucination 12/12, recorded as
  host-state evidence (not a CI gate).

## Open Questions

- **OQ-1 — UI approach (deferred to PLAN-0025; left OPEN here by Cray).**
  Whether the T2 demo UI is an **in-house shell** (build the A1 operational-map +
  A2 approval/review screen) or **driven through an existing tool** (RESULTS
  readiness §4 secondary) is **undecided**. Cray left this open for the future
  UI PLAN. **This PLAN does not resolve it** — it ships the engine only. Recorded
  here so the deferral is explicit and the question is not silently dropped.

## Surfaced decisions (SD-N) — for Cray to adjudicate

- **SD-1 — name→id resolution mechanism (AC-2 / Step 3). [Cray decision: DEFER —
  resolve at execution time; Code's recommendation below stands as the default.]**
  *Question:* implement cross-type resolution as a **name→id resolve pre-step**
  (a distinct descriptor on `StructuredQuery` that resolves a named entity to its
  id before the main filter runs) **or** as a **cross-type name filter** (a
  filter the executor transparently resolves across types)?
  *Code recommendation:* the **name→id resolve pre-step** — it keeps
  `object_type` single + enum-constrained (the bounded-attack-surface property
  the spike praised), makes the resolved id explicit in the grounding receipt
  (provable join), and is the smaller, more auditable change.
  *Alternatives considered:* the cross-type name filter (more ergonomic for the
  model to emit, but blurs the single-type invariant and hides the resolution
  inside the executor — harder to audit in the receipt).
  *Why this is a Cray decision, not a Code judgment call:* it changes the
  **public `StructuredQuery` shape / grounding-receipt contract** that PLAN-0025's
  UI and any future engine-B work will consume — a schema-contract decision, not
  an implementation detail.
  *Status:* Cray chose at the session-59 dispatch to **defer** this to execution
  time rather than pre-commit; the Code-recommended pre-step is the working
  default unless Step-3 implementation surfaces a reason to switch.

## References

- **Evidence:** `benchmarks/nl_query_feasibility/RESULTS.md` (spike verdict +
  text-to-SQL comparison arm), `benchmarks/nl_query_feasibility/gold.yaml` +
  `benchmarks/nl_query_feasibility/harness.py` (gold set + scoring oracle).
- **Code enriched:** `services/engine/nl_query.py` (`StructuredQuery`,
  `QueryOperation`, `_query_schema`, `_validate_query`, `_translate_messages`,
  `_describe_ontology`, the execute block in `answer_question`, `_no_data_answer`,
  `_fallback_answer`).
- **Tests:** `tests/services/engine/test_nl_query.py` (the `_StubQueryClient`
  offline pattern), `tests/benchmark/test_nl_query_feasibility_gold.py`.
- **Ontology + data:** `verticals/energy/ontology/energy_v0.yaml`,
  `verticals/energy/data_adapter/synthetic.py`.
- **ADRs:** ADR-005, ADR-006, ADR-010 (D1 local backend / D4 untrusted
  containment), ADR-009 D1/D2, ADR-012 D4.3. CLAUDE.md §1 (Rule-of-Three),
  §8 (quality bar). Lessons: #15 (live-vs-mock), the MS-S1 reachability /
  pinned-model note (gpt-oss:20b by IP).

---

*PLAN-0024, the engine-only build (pieces 1+2) of the T2 NL-query roadmap
direction (Cray-ratified, session 58). Drafted by in-harness `plan-drafter`
(ADR-013 D1); Code reviews, commits (ADR-009 D2), and executes. The UI shell is
deferred to PLAN-0025 (OQ-1 open). Synthetic data only; engine stays
single-operator, read-only; anti-hallucination 12/12 is a hard gate.*

*AI-assisted (Claude Code, plan-drafter, session 59); no Co-Authored-By per CLAUDE.md §7.*
