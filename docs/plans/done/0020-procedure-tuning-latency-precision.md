---
plan: PLAN-0020
title: Procedure-path tuning — latency levers + precision findings (the PLAN-0019 B-6 ring-fence follow-up)
status: Accepted
owner: Claude Code
created: 2026-06-09
related_adrs:
  - ADR-016 (governed procedure engine — THE binding primitive shape; this PLAN is RING-FENCED from it)
  - ADR-001 (LLM model baseline — gpt-oss:20b pin; the G-3 sweep CONFIRMED it holds)
  - ADR-007 (OCT engine contracts — D2 RecommendedAction envelope; fix #2 sets one field, envelope class UNCHANGED)
  - ADR-010 (LLM reasoning-hook surface — the two-call Pattern B path tuned for latency)
  - ADR-013 (autonomy-axis relocation — safe / human-gated posture; gates unchanged)
related_plans:
  - PLAN-0019 (Core Procedure baseline — Part B's B-6 ring-fence EXPLICITLY anticipated this tuning PLAN)
  - PLAN-0006 (shipped reactive loop — reactive path that DOES consume the handler/entity guess; fix #2 + prompt nudge touch shared judgment surfaces)
  - PLAN-0010 (scheduled-task autonomy loop — schedule trigger reuse; not built here)
grounding_evidence:
  - benchmarks/procedure_baseline/REPORT.md ("Results — HARDENED run (2026-06-09)") — the measured findings this PLAN acts on
authored_by: plan-drafter subagent (in-harness; ADR-009 D1 interim authoring under ADR-013 phased relocation — uncommitted draft; Code commits per ADR-009 D2)
---

# PLAN-0020 — Procedure-path tuning: latency levers + precision findings

> **Drafting provenance / author≠reviewer disclosure (ADR-012 D4.3).**
> Drafted (uncommitted) by the in-harness `plan-drafter` subagent under
> ADR-009 D1 interim authoring per ADR-013's phased relocation. The outline
> originator was **Cray** (founder, this session): the four-item scope (latency
> levers; the deterministic `affected_entities` override = fix #2; the
> aquaculture prompt nudge; the gated supply_chain α `valid_handlers`
> evaluation), the B-6 ring-fence framing, and the "REPORTS-not-gates"
> discipline were all Cray-originated in the dispatch and **G2-approved by Cray
> on 2026-06-09** (number 0020 + this scope). This draft renders them against
> PLAN-0019's B-6 ring-fence + the hardened 2026-06-09 REPORT.md numbers + the
> shipped code sites, and surfaces residual choices as **Surfaced decisions**
> (§8) rather than silently resolving them. The independent reviewer will be
> **Cray at ratification** (Draft → Proposed → Accepted); **Code commits via PR**
> (ADR-009 D2 / CLAUDE.md §7; the drafter holds no commit authority). Separation
> between drafter (`plan-drafter`) and reviewer (Cray) is **INTACT**.
>
> This PLAN is the **follow-up tuning PLAN** that PLAN-0019 Part B's **B-6
> ring-fence** explicitly anticipated: *"any measured number below threshold is a
> logged finding that opens a follow-up tuning PLAN (which model / which prompt)
> and MUST NOT reopen ADR-016's primitive shape."* It is a **tuning** PLAN, not a
> re-architecture. It does **NOT** reopen ADR-016's primitive shape and does
> **NOT** move any pre-registered bar (the SD-B1 8 s p95 / β ≥ 85% numbers).

## 1. Status

**Accepted → CLOSED (2026-06-11).** Ratified by Cray on 2026-06-11 (Draft →
Accepted); all §4 acceptance criteria landed and the PLAN is moved to `done/`
(Step 10). **AC-X1 ring-fence CONFIRMED:** the only bar moved (latency) had Cray's
explicit SD-2 re-ratification; ADR-016's primitive shape is untouched; no silent
grader / dataset / methodology change (SD-1 was SKIPPED). Authored 2026-06-09 by
the `plan-drafter` subagent; number **0020** + scope G2-approved 2026-06-09. At
ratification Cray resolved **both** surfaced decisions (§8):

- **SD-1 = WIDEN (ratification) → SKIP (Step 9 final).** Cray authorized widening
  the supply_chain α expected-set `[hold]` → `[hold, inspect]` at ratification, but
  the host-state runs (R1/R2) showed the Phase-1 nudge **eliminated** the `inspect`
  divergence (0 `inspect`; supply α = 100%), so the motivation went moot. **Cray's
  Step-9 final call: SKIP — no grader/dataset edit;** the analysis stands as a
  logged finding (REPORT). The richer fix (tiered handler grading) → follow-up PLAN.
- **SD-2 = MOVE the latency acceptance bar** from SD-B1's **8 s p95 per-call** to
  **≤ 30 s p95 per-judgment** (end-to-end two-call wall-clock), **reports-not-gates**,
  superseding SD-B1's latency bar (β ≥ 85% unchanged).

Both resolutions are recorded verbatim in §8. The bar move (SD-2) is the
explicit Cray re-ratification that AC-X1 / §5 require — the ring-fence is
honored, not breached.

## 2. Context — the evidence this PLAN acts on

The PLAN-0019 Part B **hardened run (2026-06-09)** is complete and the numbers
are in [`benchmarks/procedure_baseline/REPORT.md`](../../benchmarks/procedure_baseline/REPORT.md)
(`gpt-oss:20b` on MS-S1 `192.168.1.133:11434`, Cray-approved host-state run,
warm-first, every per-item judgment `--dump-json`-VERIFIED). Three findings drive
this tuning PLAN, all under the B-6 ring-fence (logged findings → this PLAN, never
a bar move, never an ADR-016 reopen):

1. **Latency is ~2.8× over the SD-B1 bar.** p95 **22.64 s** / mean **15.02 s**
   per LLM call (240 calls), vs the SD-B1 **≤ 8 s p95** bar. The dominant
   per-call cost is the `think=True` call-1 reasoning pass in
   `generate_judgment` (`services/engine/llm/structured.py`), which generates a
   large reasoning trace. The G-3 model-selection sweep already **closed the
   "swap the model" lever**: across 12 B–35 B structured-output-capable local
   models, `gpt-oss:20b` is best on **both** accuracy and latency — ~3.5× faster
   than every alternative; *smaller did NOT mean faster* (`gemma4:12b` is
   reliable + accurate but ~3.5× slower). **The pin HOLDS.** Any new-model lever
   must therefore be a genuinely *faster-architecture* candidate, not just fewer
   parameters.

2. **The β headline now discriminates, and surfaced a real aquaculture precision
   weakness.** Overall β = **85.8%** (companion warm run 89.2% → honest read
   ~86–89%), clearing the bar but no longer a ceiling-less 100%. Driven almost
   entirely by **aquaculture (60.0%)**, with two VERIFIED failure modes:
   - **11 × `forbidden_primary_keys`** — under multi-entity input the model
     frames a *"DO Monitoring Summary"* and lists **all** ponds in
     `affected_entities`, including SAFE decoy siblings (e.g. `aqua-h01`: named
     breached `pond-A101` **and** safe `pond-A102` / `pond-A103`). A genuine
     entity-precision weakness under distractors.
   - **7 × `action_keywords`** — the same "summary/assessment" framing describes
     the situation but never states the *aerate / oxygenate* action verb.
   - energy & supply_chain show **no** over-naming; energy's lone β fail is the
     same verb-omission "Event" framing.

3. **The supply_chain α handler-probe surfaced a BENIGN divergence (32.5%).** The
   model picks **`inspect`** (a defensible cold-chain first action) where the
   dataset pins the single handler `hold` — and crucially never the dangerous
   near-misses `expedite` / `reroute`. β stays 100% because `action_keywords`
   admits `inspect`/`hold`/`quarantine`/`divert` as the same action class. The
   REPORT itself flags this as a **tuning-PLAN question** (widen the α
   expected-set to `[hold, inspect]`?) — explicitly **not** a grader change made
   inline (methodology is ratified / fixed).

### 2.1 The product-side leak fix #2 closes (why this is the only real one)

The hardened run's over-naming finding (#2 above) reaches the product **envelope**
through exactly one site. In `services/engine/procedures/action_step.py`,
`_compose_action` (line ~114) copies the model's guess verbatim:

```python
affected_entities=judgment.affected_entities,
```

The `ActionStepExecutor.execute` loop already runs **once per deterministic
breach entity** (line ~156) and already **overrides** the model's handler guess
with the author's `step.handler` (a deterministic, allowlist-bounded blast-radius
bound — ADR-016 D3). The entity that the proposal/audit envelope NAMES should be
overridden the **same way**: from the loop's deterministically-scoped breach
entity, not the model's free guess. Today, when the model over-includes safe
decoy siblings, that over-naming copies into the `RecommendedAction` envelope the
human sees at the gate — a **metadata / UX leak**. It does **NOT** change which
handler fires (firing is per-deterministic-entity, fixed by `step.handler`), so
the leak is cosmetic-but-real: the gate UI and the audit trail name SAFE entities
as "affected." Fix #2 closes this with the **same override pattern** the handler
already uses — **ADR-016-consistent**, and the ADR-007 `RecommendedAction`
envelope *class* stays UNCHANGED (one field is now sourced deterministically).

## 3. Goal

Reduce the procedure-path **per-LLM-call latency** toward the SD-B1 bar
(**≤ 8 s p95**; the hardened 2026-06-09 run measured **p95 22.64 s / mean
15.02 s**, ~2.8× over), AND act on the **precision findings** the hardened run
surfaced — all **WITHOUT** reopening ADR-016's primitive shape and **WITHOUT**
moving any pre-registered bar (the PLAN-0019 B-6 ring-fence). Concretely: (1)
**measure and report** each candidate latency lever on the procedure path (trim
the `think=True` pass; batch a step's entities; evaluate a genuinely
faster-architecture model; and a *reported* review of whether 8 s is the right
bar for a two-call reasoning exchange on MS-S1) and emerge with a clear
recommendation; (2) ship **fix #2** — the deterministic `affected_entities`
override in `_compose_action` — with an offline unit test; (3) land the
**aquaculture prompt nudge** (name only the breached entity; always state the
action verb in the title) and re-run to record the aqua β delta; (4) **propose +
analyze** widening the supply_chain α `valid_handlers` to `[hold, inspect]`,
gated behind an explicit Cray re-ratification **before** any dataset/grader edit.
Every below-bar result stays a **logged finding**; the benchmark **reports**, it
does not gate.

## 4. Acceptance Criteria

### Item #1 — Latency levers (REPORTED, never gated)

- [ ] **AC-1a — `think=True` trim measured.** Trim / make optional the call-1
  reasoning pass in `generate_judgment` (the dominant per-call cost); the latency
  delta **AND** the β-accuracy delta (does trimming the reasoning trace cost
  correctness?) are measured on the procedure path and **RECORDED in REPORT.md**.
- [ ] **AC-1b — Request batching measured.** Evaluate batching the judgment calls
  across a step's affected entities (today the `execute` loop is sequential, 2N
  calls for N entities); the latency delta is measured + RECORDED. If batching is
  infeasible without touching the ADR-016 set-valued semantics, record **why**
  (a negative finding is a valid result).
- [ ] **AC-1c — Faster-architecture model candidate evaluated (host-state — ASK
  Cray).** Any new candidate must be a genuinely faster *architecture*, not just
  fewer params (the G-3 finding: among 12 B–35 B local models the pin is best on
  BOTH axes, ~3.5× faster — "smaller ≠ faster"). The pin HOLDS unless a candidate
  beats it on **both** accuracy and latency; result RECORDED, the pin only moves
  with explicit Cray re-ratification of ADR-001.
- [ ] **AC-1d — 8 s-bar review (REPORTED analysis only).** A written analysis of
  whether **8 s p95** is the right bar for a **two-call** reasoning exchange on
  MS-S1 hardware (it is a *per-call* bar; a two-call judgment = 2× wall-clock the
  human waits). A bar-**review** is allowed as a reported analysis; **actually
  CHANGING the bar requires Cray re-ratification** (surfaced as SD-2). **SD-2
  RESOLVED at ratification (2026-06-11): the bar IS moved to ≤ 30 s p95
  per-judgment** — this AC-1d analysis now documents that move's rationale
  (per-call vs per-judgment wall-clock; why 30 s/judgment is the right unit).
- [ ] **AC-1e — Recommendation emerges.** REPORT.md states a clear
  recommendation: which lever(s) to adopt, or "8 s bar revisited" with the
  re-ratification ask, grounded in the measured deltas above.

### Item #2 — Deterministic `affected_entities` override (offline; product code)

- [ ] **AC-2a — Override implemented.** `_compose_action` in
  `services/engine/procedures/action_step.py` sets
  `RecommendedAction.affected_entities` from the **loop entity the action step is
  processing** (the deterministically-scoped breach entity), NOT a verbatim copy
  of `judgment.affected_entities` — mirroring the existing `step.handler`
  override. The ADR-007 `RecommendedAction` envelope **class is UNCHANGED**; the
  ADR-016 primitive shape is **untouched**.
- [ ] **AC-2b — Offline unit test.** A unit test (fake `ChatClient`, no live LLM)
  drives a model that **over-names** (returns the breach entity + safe decoy
  siblings in `affected_entities`) and asserts the composed
  `RecommendedAction.affected_entities` is the **single loop entity**. (Lesson #7
  §3 behavioral assertion on the return value — no `$?`.)
- [ ] **AC-2c — Invariants green.** `ruff check services/` clean;
  `mypy --strict services/` clean; `pytest` suite green (read pytest's own
  `N passed` summary line).

### Item #3 — aquaculture prompt nudge (reactive / raw-judgment path)

- [ ] **AC-3a — Prompt adjusted.** The reasoning / structuring prompt
  (`services/engine/llm/prompt.py`) is nudged so the model (a) names **ONLY** the
  breached entity, not a "monitoring summary" of all readings, and (b) **always**
  states the action verb (aerate / oxygenate) in the proposal **TITLE**. This
  targets BOTH verified aqua β failure modes (11× `forbidden_primary_keys`
  over-naming + 7× `action_keywords` verb-omission).
- [ ] **AC-3b — Delta re-run + RECORDED (host-state — ASK Cray).** A Cray-approved
  host-state re-run records the aqua β delta in REPORT.md. Below-bar **stays a
  finding** — no bar move, no ADR-016 reopen. (Note: the prompt change touches the
  shared judgment path, so the re-run should confirm energy / supply_chain β did
  not regress.)

### Item #4 — supply_chain α `valid_handlers` evaluation (METHODOLOGY — GATED)

- [ ] **AC-4a — Written analysis.** A written analysis in REPORT.md of whether the
  α expected-set for supply_chain should widen from `[hold]` to `[hold, inspect]`,
  grounded in the VERIFIED benign-divergence finding (the model picks the
  defensible `inspect`, never the dangerous `expedite` / `reroute`).
- [ ] **AC-4b — Explicit Cray re-ratification recorded BEFORE any edit.** Because
  this is a **benchmark-methodology change** (dataset/grader), it MUST be
  explicitly **Cray-RE-RATIFIED** (anti-moving-target) **before** any
  dataset/grader edit. The re-ratification decision (approve / reject) is recorded
  in the PLAN + REPORT.md *before* the edit. **This PLAN only proposes + analyzes
  it (SD-1); it does NOT pre-authorize the change.** If Cray rejects, the analysis
  stands as a logged finding and no edit is made.

### Cross-cutting

- [ ] **AC-X1 — Ring-fence honored.** Every below-bar result remains a **logged
  finding**; **no bar is moved** (β ≥ 85% unchanged; the latency bar was
  re-ratified by Cray via SD-2 on 2026-06-11 from 8 s p95 per-call to ≤ 30 s p95
  per-judgment — an explicit re-ratification, not a silent move) without explicit
  Cray re-ratification; **ADR-016's primitive shape is untouched**; no silent
  grader / dataset / methodology change.

## 5. Out of Scope / ring-fence (state explicitly)

- ❌ **NO change to ADR-016's primitive shape** — `Procedure` / `Step` /
  `PipelineRun` / `Agent`; the `kind` set; the autonomy model. This PLAN tunes
  *around* the primitive, never *into* it.
- ❌ **NO moving the pre-registered bars** (SD-B1 **8 s p95**, **β ≥ 85%**)
  without explicit Cray re-ratification. The benchmark **REPORTS**, it does not
  gate. A bar *review* (AC-1d) is allowed as reported analysis; a bar *change* is
  SD-2 (Cray). **SD-2 RESOLVED 2026-06-11: the latency bar is re-ratified by Cray
  to ≤ 30 s p95 per-judgment (β ≥ 85% unchanged)** — the explicit re-ratification
  this line requires; the ring-fence is honored, not breached.
- ❌ **NO silent grader / dataset / methodology change.** Item #4 is **gated**
  behind explicit Cray re-ratification (SD-1); it is proposed + analyzed here, not
  pre-authorized.
- ❌ **NOT a Tier-2 real-data / PDPA-gated effort.** All work is **offline** + on
  the **existing synthetic dataset** + the **existing MS-S1 pin**. Any new-model
  eval or re-run is a **host-state run → ASK Cray** (marked per step below).
- ❌ **NO change to the ADR-007 `RecommendedAction` envelope class.** Fix #2 sets
  one existing field deterministically; the class shape is UNCHANGED.
- ❌ **NO reopening the ADR-001 model pin** as a build action — the G-3 sweep
  CONFIRMED the pin; a model change needs Cray re-ratification of ADR-001
  (AC-1c).

## 6. Steps

Ordered: **offline code/doc work first** (fix #2 + its test; the prompt nudge),
**then** the Cray-gated host-state re-run to measure the latency levers + the
aqua/supply deltas, **then** the REPORT.md fill + the item-#4 re-ratification
decision. Host-state steps are marked **ASK Cray (host-state)**.

### Phase 1 — Offline (no live LLM; lands via `feat/*` product PRs)

- **Step 1 — Fix #2: deterministic `affected_entities` override.** In
  `services/engine/procedures/action_step.py`, change `_compose_action` so
  `affected_entities` is sourced from the loop's deterministically-scoped breach
  entity (mirror the `step.handler` override pattern; thread the loop entity into
  `_compose_action`). The ADR-007 envelope class is untouched. *(AC-2a.)* Lands
  via `feat/*`.
- **Step 2 — Fix #2 offline unit test.** Add a unit test with a fake `ChatClient`
  returning an over-naming judgment (breach entity + safe decoys); assert the
  composed `RecommendedAction.affected_entities` is the single loop entity.
  `ruff` / `mypy --strict` / `pytest` clean. *(AC-2b, AC-2c.)* Same `feat/*` PR.
- **Step 3 — aquaculture prompt nudge.** Adjust the reasoning / structuring prompt
  in `services/engine/llm/prompt.py`: name ONLY the breached entity; always put
  the action verb in the proposal TITLE. Keep the change scoped so it does not
  regress energy / supply_chain framing. *(AC-3a.)* Lands via `feat/*` (product
  prompt code).

### Phase 2 — Host-state measurement (ASK Cray; lands via `test/*` PR)

> Each step here is a **host-state run on MS-S1** → **ASK Cray (host-state)**
> before running (per the project's host-state-run discipline + the existing pin).

- **Step 4 — Latency lever: `think=True` trim measurement.** **ASK Cray
  (host-state).** Run the procedure path with the call-1 reasoning pass trimmed /
  made optional; record the latency delta AND the β-accuracy delta. *(AC-1a.)*
- **Step 5 — Latency lever: request-batching measurement.** **ASK Cray
  (host-state).** Measure batching the per-step entity judgment calls; record the
  delta, or record why batching is infeasible without touching set-valued
  semantics. *(AC-1b.)*
- **Step 6 — Latency lever: faster-architecture model eval.** **ASK Cray
  (host-state)** — a new model on MS-S1 is a host-state change. Evaluate one
  genuinely faster-architecture candidate (not just fewer params); record
  accuracy + latency; the pin HOLDS unless it wins on both. *(AC-1c.)*
- **Step 7 — Prompt-nudge delta re-run.** **ASK Cray (host-state).** Re-run the
  aquaculture β (and a regression check on energy / supply_chain β) with the
  Step-3 prompt nudge; record the aqua β delta. *(AC-3b.)*

### Phase 3 — Report fill + the gated decision (lands via `docs/*` + `test/*`)

- **Step 8 — REPORT.md fill + recommendation.** Record all measured deltas
  (Steps 4–7) in REPORT.md under a new tuning-results section; state the clear
  latency recommendation (which lever(s), or "8 s bar revisited"). Author the
  AC-1d 8 s-bar review analysis. *(AC-1d, AC-1e, AC-3b.)*
- **Step 9 — Item-#4 analysis + the GATED re-ratification.** Write the
  supply_chain α `[hold, inspect]` analysis (AC-4a). Surface the methodology
  change to Cray (SD-1); **record Cray's explicit approve/reject BEFORE any
  dataset/grader edit**. If approved, make the dataset/grader edit + re-run and
  record the α delta; if rejected, the analysis stands as a logged finding and no
  edit is made. *(AC-4a, AC-4b.)*
- **Step 10 — Close.** Confirm AC-X1 (ring-fence honored: no bar moved, ADR-016
  untouched, no silent methodology change); `git mv` the PLAN to
  `docs/plans/done/` when all items land (Code, separate `docs/*` PR).

## 7. Verification

"Done" = all §4 criteria green via Lesson #7 §3 reliable methods:

- **Item #2** — `_compose_action` override implemented + the offline unit test
  passes (proving the deterministic single-entity override against an over-naming
  model); `ruff` / `mypy --strict` / `pytest` clean from their own summary lines.
- **Item #1** — each lever's latency (and accuracy, where relevant) delta is
  RECORDED in REPORT.md from a Cray-approved host-state run; a clear
  recommendation is stated.
- **Item #3** — the prompt nudge is landed and a Cray-approved host-state re-run
  records the aqua β delta (with no energy / supply_chain regression).
- **Item #4** — the written analysis exists AND an explicit Cray re-ratification
  decision is recorded **before** any dataset/grader edit.
- **Ring-fence** — every below-bar result is a logged finding; no bar moved;
  ADR-016 primitive untouched.

Per ADR-009 D2, **Code** runs verification and commits; the drafter holds no
execution or commit authority. Host-state runs are **Cray-gated** (ASK Cray).

## 8. Surfaced decisions (for Cray — do NOT silently resolve)

- **SD-1 (item #4 — widen supply_chain α `valid_handlers` to `[hold, inspect]`?)
  — GATED, needs explicit Cray re-ratification BEFORE any edit.**
  *Question:* should the α expected-set for supply_chain widen from `[hold]` to
  `[hold, inspect]`, given the VERIFIED finding that the model picks the
  defensible cold-chain `inspect` (never the dangerous `expedite` / `reroute`)?
  *Code recommendation:* **widen to `[hold, inspect]`** — one-line reason: the
  α=32.5% is a benign divergence (`inspect` is a defensible first cold-chain
  action), not a model error, and a too-narrow expected-set understates real
  handler quality. *Alternatives considered:* (a) keep `[hold]` (preserves the
  strict single-answer key, but mis-reports a benign answer as wrong); (b) drop
  the supply_chain α probe entirely (loses a forward-looking reactive-path
  signal — rejected). *Why a Cray decision (not a Code judgment call):* this is a
  **benchmark-methodology change** (dataset/grader) — changing what counts as
  "correct" after seeing the results is exactly the moving-target risk the B-6
  ring-fence + the PLAN-0019 "ratify methodology BEFORE the scored run" discipline
  guard against. It MUST be Cray-re-ratified **before** any edit; this PLAN only
  proposes + analyzes it.
  **→ RESOLVED — Cray (2026-06-11): WIDEN authorized at ratification, then SKIPPED
  at Step 9.** Cray approved widening to `[hold, inspect]` at ratification (recorded
  before any edit, AC-4b). But the host-state runs (R1/R2) VERIFIED the Phase-1
  nudge **eliminated** the divergence — the model now picks `hold` (0 `inspect`
  across all 40 supply items every run; α supply = 100%), so widening's motivation
  went moot. **Cray's Step-9 final call: SKIP — make NO grader/dataset edit.** The
  analysis stands as a logged finding (REPORT § "SD-1 implication"); anti-moving-
  target honored (no change made). The richer fix Cray's production-fidelity review
  surfaced — **tiered handler grading** (canonical / acceptable / forbidden, so the
  α metric self-distinguishes a benign alternative from a dangerous pick) — is
  deferred to a **follow-up PLAN**.

- **SD-2 (item #1d — is the 8 s p95 the right bar for a TWO-CALL exchange?) —
  REVIEW allowed here; a bar CHANGE needs Cray re-ratification.**
  *Question:* the SD-B1 bar is **8 s p95 per LLM call**, but the procedure
  judgment is a **two-call** Pattern-B exchange, so the human waits ~2× that
  wall-clock per affected entity. Is the per-call 8 s bar the right unit / value
  for this hardware (MS-S1) and this two-call shape? *Code recommendation:*
  produce the AC-1d **reported analysis** (current per-call vs per-judgment
  wall-clock; what 8 s implies end-to-end), and **recommend whatever the measured
  levers support** — but **do not move the bar** in this PLAN. *Alternatives
  considered:* (a) silently treat 8 s as per-judgment (rejected — re-scopes a
  ratified definition); (b) move the number now (rejected — anti-moving-target).
  *Why a Cray decision:* SD-B1 is a Cray-ratified pre-registered bar; reviewing it
  is fine, **changing** it (the number OR its operational definition) is a Cray
  re-ratification, never a Code judgment call.
  **→ RESOLVED — Cray (2026-06-11): bar MOVED to ≤ 30 s p95 per-judgment.** The
  acceptance bar changes from SD-B1's **8 s p95 per-call** to **≤ 30 s p95
  per-judgment** (end-to-end two-call wall-clock — the unit the human waits on).
  **Reports-not-gates:** < 30 s = gain; > 30 s = a logged finding with a
  task-complexity rationale. The per-call number is retained as a lever
  diagnostic. This **supersedes SD-B1's latency bar**; **β ≥ 85% is unchanged**.
  Operationally requires a small offline harness add (a per-judgment latency
  timer; today the recorder times per-call). Unit chosen per-judgment (not
  per-call) specifically to avoid a moving target: at 30 s per-call the current
  22.6 s would pass purely by the bar move, whereas 30 s per-judgment keeps the
  levers load-bearing.

## 9. References

### Binding design / ring-fence
- `docs/adr/0016-governed-procedure-engine.md` — D2 primitive (the RING-FENCE: not reopened), D3 autonomy / handler allowlist (the override pattern fix #2 mirrors), D5 goal.
- `docs/plans/0019-core-procedure-baseline.md` — Part B **B-6 ring-fence** (this PLAN's mandate), **SD-B1** (the 8 s p95 / β ≥ 85% bars — not moved), the β/α handler-determinism finding.

### Evidence acted on
- `benchmarks/procedure_baseline/REPORT.md` — "Results — HARDENED run (2026-06-09)": β 85.8% / ~86–89%, aquaculture 60.0% (11× over-naming + 7× verb-omission), α supply_chain 32.5% benign divergence, latency p95 22.64 s / mean 15.02 s, the G-3 sweep ("pin holds; smaller ≠ faster").

### Code sites touched
- `services/engine/procedures/action_step.py` — `_compose_action` (line ~114, `affected_entities=judgment.affected_entities` → deterministic loop-entity override = fix #2) + the per-entity loop in `ActionStepExecutor.execute` (line ~156, where `step.handler` already overrides the guess — the pattern to mirror).
- `services/engine/llm/structured.py` — `generate_judgment` (the two-call path; call-1 `think=True` at line ~165 = the dominant per-call latency cost = item #1a).
- `services/engine/llm/prompt.py` — `build_reasoning_messages` / `build_structuring_messages` (the aquaculture prompt nudge = item #3).
- `services/engine/actions.py` — ADR-007 D2 `RecommendedAction` envelope class (UNCHANGED; fix #2 only sets one existing field deterministically).

### Governance
- `CLAUDE.md` §6 (Decision / Plan Flow), §7 (all commits via PR; product code → `feat/*`, benchmark/report → `test/*` / `docs/*`), §8 (AI assistive).
- ADR-009 D1 (interim authoring), D2 (only Code commits); ADR-013 (autonomy-axis relocation); ADR-012 D4.3 (author≠reviewer disclosure).

---

*PLAN-0020 — Draft authored by the `plan-drafter` subagent 2026-06-09. The
follow-up tuning PLAN anticipated by PLAN-0019 Part B's B-6 ring-fence. G2-approved
by Cray (number 0020 + scope) 2026-06-09. RING-FENCED from ADR-016's primitive
shape; moves no pre-registered bar. Moves to Proposed → Accepted on Cray
ratification. Code commits per ADR-009 D2.*

*AI-assisted per project convention.*
