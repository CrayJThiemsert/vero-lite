---
plan: PLAN-0027
title: B-γ comparison methodology pre-registration + offline build plan — governed-procedure stack vs raw text-to-SQL vs lean RAG (PLAN-0019 Step B-γ / AC B-3)
status: Ready for execution — §3–§4 ratified (Cray, 2026-06-16)
owner: Claude Code
created: 2026-06-16
related_plans:
  - PLAN-0019 (Core Procedure baseline — THIS is its last open step, B-γ / AC B-3; "In execution")
  - PLAN-0020 (latency tuning — SD-2 ≤ 30 s p95 per-judgment unit reused for latency)
  - PLAN-0022 (watch-tier lane — the same grader/harness this plan reuses)
related_adrs:
  - ADR-016 (governed procedure engine — the stack arm (a) measures; the future verify+reshape layer is an ADR-016-area enhancement, OUT OF SCOPE here)
  - ADR-001 (LLM model baseline — gpt-oss:20b pin = the scored-run model for all three arms)
  - ADR-009 (D1 interim authoring; D2 only-Code-commits)
  - ADR-012 (D4.3 author≠reviewer disclosure)
  - ADR-013 (autonomy-axis relocation — phased; plan-drafter interim authoring)
authored_by: plan-drafter subagent (in-harness; ADR-009 D1 interim authoring under ADR-013 phased relocation — Cowork materializes per the G2 gate; Code commits per ADR-009 D2)
---

# PLAN-0027 — B-γ comparison methodology pre-registration + offline build plan

> **Drafting provenance / author≠reviewer disclosure (ADR-012 D4.3).**
> Drafted by the in-harness `plan-drafter` subagent under ADR-009 D1 interim
> authoring per ADR-013's phased relocation. The outline originator was **Cray**
> (founder, this session): the three-arm comparison structure, the
> RATIFIED/LOCKED design decisions (the common graded sub-task on the breach
> subset; arm (a) = reuse REPORT numbers, arm (b) = raw text-to-SQL, arm (c) =
> lean-but-real RAG; the energy-first / breach-subset / lean-RAG scope; the SD-5
> contamination guard; and the report-narrative hook framing the arm(a)–arm(c)
> gap as evidence of a future governed inter-step contract layer) were
> Cray-originated in the dispatch. This draft renders and cross-checks them
> against PLAN-0019 (§2.1, §4 Part B, §6 Step B-γ, §8 SD-B1/B2/B3), the live
> `benchmarks/procedure_baseline/` harness + grader + schema, the
> `benchmarks/nl_query_feasibility/text_to_sql.py` reusable pattern, the energy
> synthetic adapter, and ADR-016, and surfaces residual choices as **Surfaced
> decisions** (§8) rather than silently resolving them. The independent reviewer
> will be **Cray at ratification** (the Step-1 pre-registration go, per B-6 —
> the methodology is fixed BEFORE the scored host-state run); **Cowork
> materializes the file (G2 gate) and Code commits via PR** (ADR-009 D2; the
> drafter holds no commit authority). Separation between drafter
> (`plan-drafter`) and reviewer (Cray) is **INTACT**.
>
> This PLAN **completes PLAN-0019 Step B-γ / AC B-3** — PLAN-0019's last open
> step. It does NOT re-open any ratified PLAN-0019 decision (SD-B1 thresholds +
> their operational definitions, SD-B2 dataset size, SD-B3 G-2 defer) or
> ADR-016's primitive shape (Accepted/fixed). It inherits PLAN-0019's HARD-GATE
> / ring-fence discipline verbatim.

## 1. Status

**Ready for execution — §3–§4 ratified by Cray (2026-06-16); SD-1…SD-4 resolved (§8).** Per PLAN-0019 B-6
(anti moving-target), the methodology in §3–§4 below must be **Cray-ratified
BEFORE the scored host-state run** (Step 4). The build (Step 2) and the offline
mock gate (Step 3) may proceed once the pre-registration is ratified; the live
scored run (Step 4) needs a **separate** explicit Cray go per CLAUDE.md §8
(host-state). Moves to **Ready for execution** on Code landing this doc on
`origin/main` after Cray ratifies §3–§4.

### 1.1 LOCKED design decisions (Cray-ratified this session — recorded, do NOT re-open)

| ID | Decision | Note |
|---|---|---|
| **D-1 (common graded sub-task)** | On the **breach subset**, every arm produces and is graded on the SAME sub-task: **"name the affected entity + name the correct action class,"** reusing `Expected.{affected_primary_key, action_keywords}` (`schema.py`) and the existing grader checks (`grade_proposal`, `grader.py`). | Makes all three arms apples-to-apples with arm (a)'s **β headline**. |
| **D-2 (arm a)** | **Arm (a) = the existing governed-procedure stack.** Reuse the REPORT numbers (β 98.3–100% / α probe / watch-lane / latency from `benchmarks/procedure_baseline/REPORT.md`). **Do NOT re-run arm (a).** | Already measured; re-running wastes an MS-S1 warm cycle. |
| **D-3 (arm b)** | **Arm (b) = raw text-to-SQL.** Render the scenario as an NL question; the model writes a read-only SQL `SELECT` over an in-memory SQLite built from `verticals/energy/data_adapter/synthetic.py`; execute; grade **entity-ID**. Raw SQL **cannot propose an action class** → that inability **IS a structural finding**, recorded as such (not a harness bug). | Reuse the `text_to_sql.py` pattern: SELECT-only guard, in-memory SQLite, value-token scoring. |
| **D-4 (arm c)** | **Arm (c) = lean-but-real RAG** (SD-5 RESOLVED/RATIFIED): a small energy corpus (ontology threshold rules + action-playbook snippets) + a **deterministic top-k retriever** (lexical/keyword top-k — **NO vector store**) → retrieved context into the prompt → LLM freeform answer → grade **entity-ID + action-class** with the same grader checks. It is **NOT** a bare no-retrieval prompt. | Fairness via corpus richness (SD-1) + prompt (SD-2) ONLY. |
| **D-5 (scope)** | **Energy-first, breach subset, lean RAG corpus.** Extend to aquaculture / supply_chain only after the energy shape works. | The energy synthetic adapter is the proven one. |
| **D-6 (contamination guard — BINDING)** | Arm (c) stays a **CLEAN naive RAG baseline.** Do **NOT** add any LLM-verify / semantic-consistency / output-reshape / governance layer to arm (c). Such a layer requires procedure/ontology awareness and would import vero-lite's structure into the baseline, **destroying the comparison's ability to isolate "what governance adds over RAG."** | Fairness of the RAG arm = corpus richness (SD-1) + prompt (SD-2) ONLY. |

## 2. Context

PLAN-0019 Part B (the benchmark) is otherwise complete: arm (a) — the governed
procedure stack — is measured across multiple Cray-approved host-state runs
(`benchmarks/procedure_baseline/REPORT.md`: β headline 98.3–100%, α handler
probe, watch-tier lane, SD-2 latency). The **one open step** is **B-γ / AC B-3**
— the three-arm comparison — which the REPORT explicitly marks **"TODO — own
step (B-γ)"** in its `## B-3 comparison` section. This PLAN is that step's
pre-registration + offline build/run plan.

**The design gap this PLAN resolves.** AC B-3 says the harness runs "the **same
synthetic questions**" through three arms. But the procedure-baseline dataset
(`benchmarks/procedure_baseline/schema.py` + `dataset/*.yaml`) is **scenarios**
— a reading event (`Scenario.{event_id, primary_key, measured_value, threshold,
direction, watch_margin, distractors}`) carrying an `Expected` action-proposal
key — **NOT** NL "questions." A scenario is what the procedure path consumes; a
"question" is what a text-to-SQL / RAG path consumes. So the comparison needs an
explicit pin of (i) **what each arm produces** and (ii) the **common graded
sub-task** that makes the three arms commensurable. That pin is the **D-1
common graded sub-task** above, ratified this session.

**What already exists (reuse — do not re-build).**

- **The grader (the apples-to-apples anchor).**
  `benchmarks/procedure_baseline/grader.py` — `grade_proposal(judgment,
  expected)` scores `affected_primary_key` (entity) + `action_keywords` (action
  class) over an `LlmJudgment`; `classify_handler_tier` tiers the handler probe;
  `normalize_primary_key` handles the Unicode-hyphen artifact. The β-headline
  scoring fields (`affected_primary_key`, `action_keywords`) ARE the D-1 common
  sub-task — arm (b) and arm (c) grade against the **same** `Expected` fields.
- **The dataset.** `benchmarks/procedure_baseline/dataset/energy.yaml` — 66
  items (40 breach incl. 12 hard `energy-h01..h12`, 13 watch, 13 ok). The
  **breach subset** (D-5) is the graded mass. Each item's `Scenario` is
  self-contained (carries threshold/direction), so a per-arm NL rendering (SD-2)
  draws its fields verbatim.
- **The text-to-SQL pattern (arm b).**
  `benchmarks/nl_query_feasibility/text_to_sql.py` — `build_db()` (in-memory
  SQLite from `verticals/energy/data_adapter/synthetic.py`), `is_select_only()`
  / `execute_sql()` (read-only SELECT guard, statement-chaining + DDL/DML
  rejection), `generate_sql()` (the model writes ONE `{"sql": "SELECT ..."}`),
  `score_sql()` (value-token scoring). This is a **different, closed** benchmark
  (nl_query_feasibility, session 58) — arm (b) **reuses the pattern**, it does
  not import that benchmark's questions.
- **The synthetic energy DB.** `verticals/energy/data_adapter/synthetic.py` —
  deterministic `sites()` / `assets()` / `operational_events()`; the proven
  adapter (energy's `synthetic.py` is the one `text_to_sql.py` already binds).
- **The live runner conventions.** `benchmarks/procedure_baseline/run_benchmark.py`
  — `--warm`, `--limit`, `--dump-json`, `--model gpt-oss:20b`,
  per-call/per-judgment latency recorders, the `_register_all_handlers()` +
  `_resolve_goal_and_model()` pattern. RAG/text-to-SQL are explicitly noted there
  as "deliberately TODO ... land in their own steps."
- **The LLM seam.** `services/engine/llm/structured.py` — `generate_judgment`
  (the arm-(a)/arm-(c) judgment path, `ChatClient`-injectable for offline mock),
  `StructuredOutputError`; `services/engine/llm/client.py` — `OllamaClient` /
  `OllamaError`.
- **The host-state launcher.** `.claude/skills/ms-s1-ollama/run_detached.sh` —
  the carrier-proof detached runner used for the prior scored runs (sentinel +
  `DUMP: wrote N` completion truth).

**RAG exists nowhere** — arm (c)'s corpus + deterministic retriever is the only
genuinely greenfield component; arm (b) is a thin re-wire of an existing pattern.

## 3. Methodology pre-registration (Cray ratifies §3–§4 BEFORE the scored run — B-6)

### 3.1 What each arm produces, and the common graded sub-task (D-1)

All three arms run over the **energy breach subset** (D-5). For each breach
scenario:

| Arm | Input it consumes | Output it produces | Graded on (D-1 common sub-task) |
|---|---|---|---|
| **(a) governed-procedure stack** | the `Scenario` as an event (existing path) | `LlmJudgment` (affected entity + action class + handler) | **entity-ID + action-class** — `grade_proposal` β fields. **Reused from REPORT — not re-run.** |
| **(b) raw text-to-SQL** | the scenario rendered as an NL question (SD-2) | one read-only `SELECT` → executed rows | **entity-ID** only (value-token match on the affected `primary_key`). Action-class is **structurally unavailable** (a finding — D-3). |
| **(c) lean RAG** | the NL question (SD-2) + top-k retrieved corpus context (SD-1) | LLM freeform answer | **entity-ID + action-class** — the SAME `Expected.{affected_primary_key, action_keywords}` checks. |

**Apples-to-apples anchor.** Entity-ID is graded for all three arms against the
same `Expected.affected_primary_key`. Action-class is graded for arm (a) and arm
(c) against the same `Expected.action_keywords` (the per-vertical action lemmas,
e.g. energy `[restart, reset, reboot]`); arm (b)'s **absence** of an action
output is reported as the structural finding, not scored as a wrong answer.

> **Grader reuse is mandatory (D-1).** Arm (b)'s entity check and arm (c)'s
> entity + action-class checks reuse `grade_proposal` / `normalize_primary_key`
> / the `action_keywords` haystack search **as-is**. Where an arm's output is
> not an `LlmJudgment` (arm (b) emits SQL rows; arm (c) emits free text), the
> harness adapts that output into the minimal shape the existing checks consume
> (e.g. an entity-key set for the entity check; a free-text blob for the
> action-keyword search) — it does **not** fork the grading logic. This keeps
> the comparison faithful to arm (a)'s β headline.

### 3.2 Arm (b) — raw text-to-SQL (D-3)

- **DB.** Build an in-memory SQLite from `verticals/energy/data_adapter/synthetic.py`
  via the `text_to_sql.py` `build_db()` pattern (the `site` / `asset` /
  `operational_event` tables + the enum-hint DDL shown to the model). The
  scenario readings are synthetic; the question is "which asset breached" — so
  the breach event/value must be present in the DB for a correct SELECT to find
  it (see SD-2 / SD-3 for how the breach scenario maps onto rows).
- **Generate.** Reuse `generate_sql(client, question)` — ONE
  `{"sql": "SELECT ..."}`, read-only guarded by `is_select_only()` (rejects
  DDL/DML + statement chaining).
- **Execute + grade.** `execute_sql()` → rows; grade **entity-ID** by the
  value-token method (`score_sql`-style: the affected `primary_key` token must
  appear in the stringified result). **No action-class grade** — raw SQL returns
  data, not an action proposal. Record "action-class: structurally N/A" as the
  D-3 finding.
- **Latency.** Per-arm wall-clock + per-call (SD-4).

### 3.3 Arm (c) — lean-but-real RAG (D-4; SD-5 RESOLVED — clean-baseline guard D-6)

- **Corpus (SD-1).** A small energy corpus: the `energy_v0.yaml` threshold rule
  + action-playbook snippets for `restart` / `isolate` / `dispatch_technician` /
  `escalate` (≈8–15 short snippets — SD-1 pins exact content/size). Authored as a
  static fixture (deterministic; no network).
- **Retriever.** A **deterministic top-k lexical retriever** (keyword/term
  overlap top-k — **NO vector store, no embeddings**). Deterministic so the
  offline mock smoke is reproducible and the comparison isolates the LLM
  variable, not retriever nondeterminism.
- **Prompt + answer.** Retrieved snippets → into the prompt as context → LLM
  freeform answer (the same `ChatClient` seam; a freeform — not
  schema-constrained — answer is the honest naive-RAG shape). Grade **entity-ID
  + action-class** with the same grader checks (entity-key search + the
  `action_keywords` haystack search).
- **D-6 CONTAMINATION GUARD (BINDING).** Arm (c) is a **CLEAN naive RAG
  baseline**: NO LLM-verify, NO semantic-consistency check, NO output-reshape, NO
  governance/disposition/handler-allowlist/audit layer. Any such layer needs
  procedure/ontology awareness and would import vero-lite's structure into the
  baseline — destroying the comparison's ability to isolate what governance adds
  over RAG. Arm (c) fairness is achieved via **corpus richness (SD-1) + prompt
  (SD-2) ONLY**. This guard is asserted in code review of Step 2 (a reviewer
  checks arm (c) imports no `services/engine/procedures/` symbol and runs no
  second "verify" LLM call).

### 3.4 What the comparison is designed to show (report-narrative hook — Cray-directed)

This narrative is prescribed here and MUST head the eventual REPORT `## B-3`
section. **It is a framing/interpretation note for the report — NOT a B-γ build
step (B-γ is measurement-only).**

The qualitative differentiator between arm (a) and arm (c) is a **governed
inter-step contract layer**: vero-lite's procedure engine can (i) **verify** an
LLM step's output for *semantic* consistency against that step's requirement and
(ii) **reshape** the output to fit the **next** procedure step's input contract,
improving downstream-step processing. A naive RAG baseline structurally lacks
this — no deterministic disposition, no handler allowlist, no audit trail, no
inter-step contract glue. The arm(a)–arm(c) gap is therefore evidence of THIS
layer's value (over and above raw retrieval-augmented generation).

> **Forward-pointer / future-work note (OUT OF SCOPE for B-γ).** The
> **verify + reshape** layer described above is a **separate, future
> procedure-engine enhancement** (ADR-016 area) — it is **NOT** built or
> measured in B-γ, which is measurement-only. The engine **today** already has
> structured-output **schema** validation (`StructuredOutputError`,
> `services/engine/llm/structured.py`); the enhancement would **extend** that
> from schema-validation to **semantic-verify + inter-step reshape**. Record it
> as a forward-pointer for a future PLAN/ADR; do **not** turn it into a B-γ build
> step, and do **not** add any of it to arm (c) (D-6).

### 3.5 Inherited guardrails (PLAN-0019 — recorded, not re-opened)

- **Reports-not-gates (B-3 / B-6).** "Our stack wins" is the **thesis under
  test**, NOT an acceptance condition. Acceptance = "comparison run + the three
  measures (accuracy / failure-mode / latency) recorded + report committed." A
  result where a baseline matches or beats arm (a) is a **finding**, not a build
  failure, and never moves a bar or reopens ADR-016's primitive shape.
- **Anti moving-target (B-6).** §3–§4 are ratified **before** the scored run.
  No methodology / rendering / corpus / grading change after the scored run —
  a below-expectation number is a logged finding feeding a follow-up, never a
  retroactive methodology edit. As-run numbers are never rewritten.
- **Host-state discipline (CLAUDE.md §8).** The scored run on MS-S1 needs an
  **explicit Cray go**; warm-first; minimize live runs; the offline mock smoke
  is the gate, the live run is evidence.

## 4. Acceptance Criteria

- [ ] **AC-1 Methodology pre-registered + Cray-ratified.** §3 (what each arm
  produces, the D-1 common graded sub-task, the SD-1..SD-4 resolutions, the
  D-6 contamination guard, the §3.4 report-narrative hook + its OUT-OF-SCOPE
  forward-pointer) is ratified by Cray **before** any scored run (B-6).
- [ ] **AC-2 Arm (b) built offline.** A text-to-SQL arm over the energy breach
  subset, reusing the `text_to_sql.py` pattern (in-memory SQLite from
  `synthetic.py`, read-only SELECT guard, value-token entity-ID scoring), with a
  **mock-`ChatClient` unit test** (no network) asserting: a correct SELECT scores
  entity-ID PASS; a non-SELECT is refused; the "action-class structurally N/A"
  finding is recorded.
- [ ] **AC-3 Arm (c) built offline.** A lean-RAG arm: a static energy corpus
  (SD-1), a deterministic top-k lexical retriever, the retrieve→prompt→freeform
  path, graded entity-ID + action-class via the **existing** grader checks, with
  a **mock-`ChatClient` unit test** asserting the retriever is deterministic and
  the grade reuses `grade_proposal`'s fields. **The D-6 guard holds** (no
  procedure/ontology/verify/reshape layer — asserted by review + a test that arm
  (c) imports no `services/engine/procedures/` symbol).
- [ ] **AC-4 Comparison harness + reporting shape.** A harness that runs arms
  (b) + (c) on the same breach items, joins arm (a)'s REPORT numbers, and emits
  per-arm **accuracy / failure-mode / latency**. `--dump-json` captures every
  per-item judgment for offline VERIFY (the session-46 "confirm, don't infer"
  discipline).
- [ ] **AC-5 Offline gate green (the cheapest gate — BEFORE any live run).** The
  full **mock** smoke (arms b + c on the breach subset with a deterministic mock
  `ChatClient`) runs end-to-end green; `ruff check` clean; `mypy --strict` clean
  on new code; `pytest` unit suite green (read the `N passed` summary line, not
  `$?`).
- [ ] **AC-6 ONE scored host-state run.** After Cray go (CLAUDE.md §8): ONE run
  on MS-S1 (`gpt-oss:20b`, ADR-001 pin), **warm-first**, via `run_detached.sh`,
  capturing `--dump-json`. Arm (a) is **NOT re-run** (REPORT numbers reused).
- [ ] **AC-7 Verify + REPORT B-3 committed.** Scores VERIFIED from `--dump-json`
  with the **Read tool** (not piped `wc`/`cat` — Auto-Memory false-negative
  caveat); the REPORT `## B-3 comparison` section written (per-arm
  accuracy/failure-mode/latency table + the §3.4 narrative header + the
  forward-pointer note + the reports-not-gates ring-fence restatement); landed
  via a dedicated **`test/*` PR** (PLAN-0019 review-separation — keeps the
  research review off the engineering review).

## 5. Out of Scope (defer)

- ❌ **Re-running arm (a)** — REPORT numbers are reused (D-2); a re-run wastes an
  MS-S1 warm cycle.
- ❌ **A vector store / embeddings for arm (c)** — D-4: a deterministic lexical
  top-k retriever is the lean baseline.
- ❌ **Any verify / semantic-consistency / output-reshape / governance layer on
  arm (c)** — D-6 contamination guard (BINDING).
- ❌ **Building the future verify+reshape procedure-engine enhancement** — §3.4
  forward-pointer; a separate future PLAN/ADR (ADR-016 area). B-γ is
  measurement-only.
- ❌ **aquaculture / supply_chain arms** — D-5 energy-first; extend only after the
  energy shape works.
- ❌ **watch / ok subsets** — SD-3 recommends breach-only (matches arm (a)'s β
  headline); pending Cray.
- ❌ **Moving any pre-registered bar / reopening ADR-016** — B-6 ring-fence.

## 6. Steps

1. **Step 1 — Pre-registration (this doc) → Cray ratify.** Land §3–§4 on
   `origin/main`; Cray ratifies the methodology BEFORE any scored run (B-6).
   *(AC-1.)*
2. **Step 2 — Build arms (b) + (c) offline.** Arm (b): re-wire the
   `text_to_sql.py` pattern over the energy breach subset (in-memory SQLite from
   `synthetic.py`, read-only SELECT guard, value-token entity scoring). Arm (c):
   author the static energy corpus (SD-1), the deterministic top-k lexical
   retriever, the retrieve→prompt→freeform path, grading via the **existing**
   grader checks; enforce the D-6 guard. Both with **mock-`ChatClient` unit
   tests**. *(AC-2, AC-3, AC-4.)* Lands via `feat/*` or `test/*` PR(s).
3. **Step 3 — Offline gate (cheapest gate, MUST be green first).** Full mock
   smoke (arms b + c, breach subset, deterministic mock client) green; ruff /
   mypy --strict / pytest clean from their own summary lines. **No live run
   before this is green.** *(AC-5.)*
4. **Step 4 — ONE scored host-state run.** Cray go per CLAUDE.md §8; MS-S1
   `gpt-oss:20b`, warm-first, `run_detached.sh`, `--dump-json`. Arm (a) not
   re-run. *(AC-6.)*
5. **Step 5 — Verify + REPORT + land.** VERIFY scores from `--dump-json` with the
   **Read tool**; write the REPORT `## B-3 comparison` section (per-arm
   table + §3.4 narrative header + forward-pointer + ring-fence); land via a
   dedicated `test/*` PR (review-separation). *(AC-7.)*

> **HARD GATE (inherited from PLAN-0019).** No scored host-state run (Step 4)
> before the offline mock gate (Step 3) is green AND the pre-registration (Step
> 1) is Cray-ratified. The ring-fence (reports-not-gates) holds throughout.

## 7. Verification

"Done" = all §4 ACs green via Lesson #7 §3 reliable methods: the offline mock
smoke + ruff/mypy/pytest green from their own summary lines (Step 3); ONE
Cray-approved scored run (Step 4); every reported number VERIFIED from
`--dump-json` via the Read tool (Step 5); the REPORT `## B-3` section committed
via a `test/*` PR. Per ADR-009 D2, **Code** runs verification + commits; the
drafter holds no execution or commit authority.

## 8. Surfaced decisions (for Cray — do NOT silently resolve)

> **ALL SDs RESOLVED/RATIFIED (Cray, 2026-06-16 — §3–§4 ratification, Step 1).**
> SD-1…SD-4 are ratified **per the recommendations as written below** (SD-5 was
> already resolved). **Joint binding (SD-1 ↔ SD-2 — Cowork advisory, Cray-ratified):**
> under the locked lexical retriever (D-4, no embeddings) arm (c) is bounded by the
> lexical overlap between the SD-2 question template and the SD-1 corpus snippet, so
> SD-1 and SD-2 are ratified as **ONE joint item** — the corpus snippets MUST share
> surface vocabulary (entity-type words + action verbs) with the question template,
> AND every breach item's expected `action_keywords` lemma MUST be covered by ≥1
> corpus snippet. Otherwise an arm (c) miss is a *retrieval artifact* (externally
> rebuttable), not a naive-RAG-paradigm limit. This is arm (c)'s fairness guarantee
> for the comparison's external defensibility; it stays within the corpus + prompt
> levers (D-6 intact). **Step 2 build MUST honor it.** Recorded — not re-opened (B-6).

- **SD-1 — RAG corpus content + size (arm c).** *Recommendation:* **~8–15 short
  snippets** — the energy `energy_v0.yaml` threshold rule + playbook entries for
  `restart` / `isolate` / `dispatch_technician` / `escalate`. *Alternatives:*
  rules-only (leaner, but the model can't retrieve an action verb → unfairly
  weak arm (c)); include event rows (richer, but blurs "retrieval" with "data
  lookup"). *Why a Cray decision:* corpus richness is the ONLY fairness lever for
  arm (c) under D-6 — too thin and the comparison unfairly handicaps RAG; too
  rich and it stops being a *naive* baseline. Multiple defensible answers; Cray
  sets the fairness bar Cray is willing to defend externally.

- **SD-2 — scenario→NL rendering (arms b + c).** *Recommendation:* a
  **deterministic per-arm template** drawing `Scenario` fields verbatim (entity
  type/PK, measured value, unit, threshold, direction) into a plain operator
  question, e.g. *"Which asset has a temperature breach above 90 °C, and what
  should we do?"* *Alternatives:* terser entity-only ("which asset breached?" —
  drops the action half, handicaps arm (c)'s action grade); include the
  distractor `other_readings` (harder, multi-entity — but arm (b)'s SQL would
  need the decoys in the DB rows too). *Why a Cray decision:* the rendering
  fixes what "the same question" means across arms — a load-bearing
  pre-registration choice (B-6); silently picking it would let the rendering be
  tuned post-hoc.

- **SD-3 — breach-only vs include watch/ok.** *Recommendation:* **breach-only**
  — matches PLAN-0019 L-2 (the breach subset) and arm (a)'s β headline, so the
  three arms are commensurable with the reused arm (a) numbers. *Alternatives:*
  add an `ok` no-fire sanity (does a baseline hallucinate an action on a
  non-breach? a real finding, but doubles authoring); full-198 parity (most
  faithful, most costly — and watch/ok have no arm-(a) β number to compare
  against). *Why a Cray decision:* it sets the comparison's denominator and what
  "accuracy" ranges over — pinned with the methodology (B-6).

- **SD-4 — latency unit.** *Recommendation:* **reuse the PLAN-0020 SD-2
  per-judgment unit** (reported-not-gated here) **PLUS per-arm wall-clock**,
  since the arms differ in call shape (arm (b) = 1 SQL-gen call + a local
  execute; arm (c) = 1 retrieve + 1 freeform call; arm (a) = the 2-call Pattern-B
  exchange). *Alternatives:* per-call only (hides that arm (a) is a 2-call
  exchange); per-arm only (hides per-call cost). *Why a Cray decision:* a fair
  latency comparison across structurally-different arms needs the unit pinned up
  front; reported-not-gated (no bar moves — B-3/B-6).

- **SD-5 — RAG vs bare-LLM — ✅ RESOLVED/RATIFIED: lean-but-real RAG (Cray, this
  session).** *Decision:* arm (c) is a **lean-but-real RAG** baseline (small
  corpus + deterministic top-k lexical retriever + retrieved context → freeform
  answer), **NOT** a bare no-retrieval prompt. *Binding guard (D-6):* it stays a
  **CLEAN naive RAG baseline** — NO LLM-verify / semantic-consistency /
  output-reshape / governance layer (those need procedure/ontology awareness and
  would import vero-lite's structure into the baseline, destroying the
  comparison's ability to isolate what governance adds over RAG). Fairness =
  corpus richness (SD-1) + prompt (SD-2) ONLY. *Recorded as resolved — not an
  open question.*

## 9. References

### Completes
- `docs/plans/0019-core-procedure-baseline.md` — §2.1 (MERGE-with-guardrails,
  HARD GATE, review-separation), §4 Part B (B-1..B-6: reports-not-gates,
  ring-fence, the same-questions comparison), §6 Step B-γ ("Harness + baselines
  ... raw text-to-SQL + RAG comparison ... on the SAME questions"), §8
  SD-B1/B2/B3 (ratified — not re-opened).

### Reused surfaces (verbatim / pattern)
- `benchmarks/procedure_baseline/grader.py` — `grade_proposal`,
  `classify_handler_tier`, `normalize_primary_key` (the D-1 apples-to-apples
  anchor).
- `benchmarks/procedure_baseline/schema.py` — `Scenario`, `Expected`
  (`affected_primary_key`, `action_keywords`), `BenchmarkItem`, `Dataset`.
- `benchmarks/procedure_baseline/harness.py` — `scenario_to_event`,
  `evaluate_item`, the latency recorders, `percentile`.
- `benchmarks/procedure_baseline/dataset/energy.yaml` — the energy breach
  subset (40 breach incl. `energy-h01..h12`).
- `benchmarks/procedure_baseline/run_benchmark.py` — `--warm` / `--limit` /
  `--dump-json` / `--model` runner conventions (B-γ noted there as TODO).
- `benchmarks/nl_query_feasibility/text_to_sql.py` — the arm-(b) pattern:
  `build_db`, `is_select_only`, `execute_sql`, `generate_sql`, `score_sql`
  (read-only SELECT guard, in-memory SQLite, value-token scoring).
- `verticals/energy/data_adapter/synthetic.py` — the deterministic energy DB
  (`sites` / `assets` / `operational_events`).
- `services/engine/llm/structured.py` — `generate_judgment` (arm a / arm c
  path), `StructuredOutputError` (today's schema validation — the §3.4
  forward-pointer's starting point); `services/engine/llm/client.py` —
  `OllamaClient` / `OllamaError`.
- `.claude/skills/ms-s1-ollama/run_detached.sh` — the carrier-proof host-state
  launcher (sentinel + `DUMP: wrote N` completion truth).

### Governance
- `CLAUDE.md` §8 (host-state ASK-Cray; ADRs merged before implementation; AI
  assistive), §6 (Plan Flow), §7 (PR-only to main).
- ADR-009 D1 (interim authoring), D2 (only Code commits); ADR-013 (autonomy-axis
  relocation, phased); ADR-012 D4.3 (author≠reviewer disclosure); ADR-016
  (procedure engine — the future verify+reshape enhancement is an ADR-016-area
  forward-pointer, OUT OF SCOPE here); ADR-001 (`gpt-oss:20b` pin).

---

*PLAN-0027 — Draft authored by the `plan-drafter` subagent 2026-06-16. Completes
PLAN-0019 Step B-γ / AC B-3 (the comparison: governed-procedure stack vs raw
text-to-SQL vs lean RAG). Pre-registration (§3–§4) awaits Cray ratification
BEFORE any scored host-state run (B-6 anti moving-target). Cowork materializes +
Code commits per ADR-009 D2. Reports-not-gates ring-fence inherited from PLAN-0019.*

*AI-assisted per project convention.*
