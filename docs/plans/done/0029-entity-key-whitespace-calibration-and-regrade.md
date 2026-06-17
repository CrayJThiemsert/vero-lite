---
plan: PLAN-0029
title: Entity-key whitespace calibration + offline re-grade of the B-γ dumps (small; measurement-correctness; unblocks PLAN-0028 Step 6 REPORT)
status: Accepted
owner: Claude Code
created: 2026-06-17
related_plans:
  - PLAN-0028 (B-γ extension — THIS plan re-grades its scored-run dumps to canonical numbers and unblocks its Step 6 REPORT; numbers reported there are PRE-calibration until this lands)
  - PLAN-0027 (B-γ methodology — the arm-(c) grader adapter `answer_to_judgment` this calibrates; D-1..D-6 + SD-1..SD-4 + the joint fairness binding are INHERITED, not re-opened)
  - PLAN-0019 (Core Procedure baseline — `normalize_primary_key` + the B-6 grader-calibration family this extends)
  - PLAN-0020 (the hardened breach datasets where aqua-h06 lives)
related_adrs:
  - ADR-001 (gpt-oss:20b pin — the scored-run model that emitted the U+202F glyph)
  - ADR-009 (D1 interim authoring; D2 only-Code-commits)
  - ADR-012 (D4.3 author≠reviewer disclosure)
  - ADR-013 (autonomy-axis relocation — phased; plan-drafter interim authoring)
  - "future ADR (number TBD) — governed entity resolution against the declared universe (the product-side universality investment routed OUT of this plan; see Findings)"
authored_by: "plan-drafter subagent (in-harness; independent drafting + fact-verification pass, session-66) — body materialized by Cowork (Desktop) from this handoff under Cray's explicit per-diff approval with SD-1/SD-2 Cray-ratified; Cray reviews at ratification, Code commits per ADR-009 D2"
---

# PLAN-0029 — entity-key whitespace calibration + offline re-grade

> **Drafting provenance / author≠reviewer disclosure (ADR-012 D4.3).**
> The outline originator was **Code** (session-66 dispatch §3) on a scope **Cray
> ratified** (universality criterion + "small PLAN before the REPORT"). The
> independent drafting + fact-verification pass was performed by the in-harness
> `plan-drafter` subagent under ADR-009 D1 interim authoring (ADR-013 phased
> relocation); its `Write` — and Code's — to `docs/plans/` was **G2-denied** (the
> always-pause boundary fires on materializing ANY new PLAN, regardless of agent,
> and does NOT release on in-context approval). **Cowork materialized** the verified
> body (Desktop) under **Cray's explicit approval** with **SD-1/SD-2 ratified**
> (2026-06-17). Reviewer at ratification = **Cray**; Code commits via PR per ADR-009
> D2. Separation: originator (Code) ≠ independent drafter (plan-drafter) ≠
> materializer (Cowork) ≠ reviewer (Cray) — **INTACT**.

## Status

**Accepted.** Cray ratified this PLAN 2026-06-17 (session 67); **SD-1 + SD-2 were
already Cray-ratified at materialization** (see the drafting-provenance note above).
All work is complete — this is a formal flip of already-executed,
already-Cray-approved work, not a new decision.

**Completion — AC-1..AC-5 met.** `normalize_primary_key` now folds the
whitespace-separator family ({U+0020, U+00A0, U+2007, U+202F, U+2060} → `-`,
recover-only) for KEY comparison; the offline re-grade flipped **exactly aqua-h06**
→ aquaculture arm-(c) **39/40 → 40/40** (VERIFIED via the Read tool); supply_chain
unchanged (40/40); arm-(b) unchanged. ruff + `mypy --strict` clean; `tests/benchmark`
151 passed (+4). Shipped #353 (`e5f9774` / `1ada20d`). The product entity-trust
finding is routed OUT to a future ADR + PLAN-0030 (AC-5).

## Goal

Extend the B-6 grader calibration in `normalize_primary_key`
(`benchmarks/procedure_baseline/grader.py`) — which today maps only the Unicode
**hyphen** family to ASCII `-` — to **also map the Unicode whitespace-as-separator
family to ASCII `-`**, for primary-KEY comparison only (free-text keyword matching
stays un-normalized). Then **offline re-grade** the stored PLAN-0028 B-γ
`--dump-json` files under the patched normalizer, producing the **canonical**
per-vertical numbers that unblock the PLAN-0028 Step 6 REPORT. Fully **offline** —
no host-state run. The calibration is **recover-only / never-invent**, the same
measurement-correctness family as the Cray-ratified U+2011 hyphen calibration
(2026-06-12): it can only recover a correctly-named entity, never invent one, so it
tightens **nothing** in the baseline's favour.

### Root cause (the one thing this plan fixes)

The single aquaculture arm-(c) miss in the scored run is **aqua-h06**. The dataset
expects `pond-A116` (`benchmarks/procedure_baseline/dataset/aquaculture.yaml:175-176`).
The model **named the right pond** but used a **U+202F NARROW NO-BREAK SPACE** as the
separator (`"Pond A116"`). The arm-(c) adapter `answer_to_judgment`
(`benchmarks/procedure_comparison/rag_arm.py:180-184`) substring-matches known
candidate keys after `normalize_primary_key`, which maps only the hyphen family →
`"pond-a116"` is not a substring of `"pond a116"` → no match → placeholder `∅` →
graded a miss. The 39 passing aqua items used a U+2011 hyphen (already covered). This
is a benchmark **measurement-calibration** gap, **not** a product entity-resolution
defect.

## Acceptance Criteria

- [ ] **AC-1** — `normalize_primary_key` also maps the enumerated Unicode whitespace
      family **{U+202F NARROW NO-BREAK SPACE, U+00A0 NO-BREAK SPACE, U+2007 FIGURE
      SPACE, U+2060 WORD JOINER, U+0020 SPACE} → ASCII `-`** (mirroring the existing
      `_UNICODE_HYPHENS` dict-translate), for KEY comparison **only**; free-text
      keyword matching (`action_keywords`/`forbidden_keywords`) stays un-normalized
      (no evidence of need; consistent with the docstring). The docstring records the
      calibration standard (recover-only / never-invent) + names the dump-verified
      glyph (aqua-h06, U+202F). [SD-1 Cray-ratified: map→`-`, enumerated set — NOT
      strip-separators.]
- [ ] **AC-2** — a small **offline** re-grade harness reads each PLAN-0028 B-γ dump
      record's raw `arm_c.answer` + the dataset item's candidate keys (scenario
      `primary_key` + distractors) + `_reduced_expected`, re-runs `answer_to_judgment`
      + `grade_proposal` under the patched normalizer, and emits a per-item
      **before→after** table + per-vertical summary. **No live model call; no
      `services` import beyond what `rag_arm` already uses;** runs from the stored
      dumps + datasets only.
- [ ] **AC-3** — the re-grade output is **VERIFIED via the Read tool**
      (confirm-not-assume, session-46). The flipped-item set is reported honestly and
      each flip is shown to be a legitimate recovery (a correctly-named entity
      previously blocked by a whitespace separator). [SD-2 Cray-ratified: "only
      aqua-h06 flips" is an **expectation to verify**, NOT an assumption baked into the
      logic — if any other item flips, investigate + report before declaring numbers
      canonical.] Expectation: aqua arm-c **39/40 → 40/40**; supply_chain unchanged
      (40/40); arm-(b) unchanged (no prose grading).
- [ ] **AC-4** — offline gate green: ruff + `mypy --strict` clean; `tests/benchmark/`
      passes; a **regression test** asserts a whitespace-separated correct entity
      (U+202F between label and key) resolves (the calibration guard, mirroring the
      hyphen guard), **and** a negative guard asserts a genuinely-wrong entity still
      fails (never-invent).
- [ ] **AC-5** — this PLAN documents the product entity-trust finding (Findings) and
      routes it **OUT OF SCOPE** to a future ADR + PLAN-0030.

## Out of Scope

- ❌ the product LLM-path entity-resolution change (`recommender._compose_llm_record`,
  `services/engine/recommender.py:160`) → **future ADR + PLAN-0030** (design-first)
- ❌ embeddings / hybrid retriever (the lexical retriever near-oracle caveat stays)
- ❌ vertical #3 (Rule-of-Three) — a separate research dispatch (Cowork)
- ❌ any host-state / live re-run — the re-grade is offline from the stored dumps
- ❌ the already-shipped U+2011 hyphen calibration (this only ADDS the whitespace family)
- ❌ re-opening PLAN-0027's D-1..D-6 / SD-1..SD-4 / the joint fairness binding

## Steps

### Step 1: extend `normalize_primary_key` + regression tests
Add the enumerated whitespace family to the translate map (or a sibling map applied
alongside `_UNICODE_HYPHENS`); extend the docstring with the calibration standard +
the aqua-h06 evidence. Add the positive (whitespace-separated correct entity resolves)
+ negative (wrong entity still fails) regression tests. (AC-1, AC-4)

### Step 2: offline re-grade harness + run
Write a small offline re-grade module/script (under `benchmarks/procedure_comparison/`
or a `tools/` sibling — keep the `services` import surface = what `rag_arm` already
uses) that joins each dump record to its dataset item and re-runs the adapter + grader.
Run it against both PLAN-0028 dumps. (AC-2)

### Step 3: VERIFY before→after via Read
Read the re-grade output; report the flipped set honestly (confirm-not-assume). Confirm
each flip is a legitimate recovery. (AC-3)

### Step 4: STATUS reconcile (Code lane)
Reconcile `docs/STATUS.md` to the **canonical** post-calibration numbers; supersede the
PRE-calibration marker so no before/after ambiguity survives into a new session.

### Step 5: hand canonical numbers to PLAN-0028 Step 6 REPORT
The canonical per-vertical numbers (aqua arm-c expected 40/40) flow into the PLAN-0028
`REPORT.md ## B-3` extension. (PLAN-0028 Step 6 — not executed here.)

## Findings → follow-up (OUT OF SCOPE — the universality investment)

**Evidence of the gap.** `services/engine/recommender.py:160` (`_compose_llm_record`)
builds the governed `RecommendedAction` with `affected_entities=judgment.affected_entities`
— the LLM-emitted entity refs are **trusted verbatim**, with **no** resolution/validation
against the declared object universe. (The deterministic fail-safe path, `recommender.py:265`,
grounds the entity in the actual event via `EntityRef(primary_key=subject_id)` — already
universal-correct.) `EntityRef` (`services/engine/actions.py:27-30`) is a plain model with
no validation.

**Why this is THE universality lever.** A new vertical declares its object instances in the
ontology; the governed layer should **resolve a model-named entity against that declared
universe** (normalize → match a known instance; reject/flag/fall-back on a non-match) rather
than trusting model prose/format. Same "classify-don't-synthesize" discipline as ADR-0021
(measured_kind), applied to entity identity. This generalises across verticals and is the
thing that makes the governed stack robust where raw text-to-SQL (arm b) is brittle. The
grader calibration in this plan is **measurement hygiene only** — it does NOT advance product
universality; this finding is where the universality investment actually lives.

**Open design fork (for the future ADR — do NOT pre-decide):**
1. Where does the "known universe" come from at recommend-time? (a) the triggering event's
   candidate entities; (b) a DB/ontology-object lookup against the canonical object table;
   (c) the deterministic trigger's already-identified subject as anchor.
2. What happens on a non-resolving model PK? drop / flag low-confidence / fall back to the
   deterministic subject / reject pending human review (audit implications).
3. Boundary: governed-product path only — must NOT leak into the arm-(c) naive-RAG baseline
   (the D-6 contamination guard).

→ Route to a **new ADR (number TBD) + PLAN-0030**, design-first (mirror the ADR-0021 (b)
ratification flow); Cowork drafts the ADR framing + this fork, Cray ratifies the construct
before implementation. A separate Cowork research dispatch scopes vertical #3 (Rule-of-Three).

## Verification

The re-grade **before→after** table, read via the Read tool, shows the canonical numbers;
the offline gate is green; the positive + negative regression guards pass; the flipped set is
**{aqua-h06}** (or, if not, investigated + reported before any number is called canonical).
The canonical numbers (aqua arm-c expected 40/40; supply_chain 40/40; arm-(b) unchanged) flow
into the PLAN-0028 Step 6 REPORT. No host-state run occurs at any point.
