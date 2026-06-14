# PLAN-0023: PDPA RoPA-lite — template + NPD example (audit-framework-prep, step-2)

**Status:** Draft
**Owner:** both (Cowork/plan-drafter authors this PLAN; Code commits + executes)
**Created:** 2026-06-14
**Related ADRs:** ADR-011 (earmarked audit framework — *fed*, not authored, by this PLAN); ADR-0020 R3 (synthetic-informs, does-not-trigger); ADR-009 D1/D2 (Cowork drafts, Code commits); PLAN-0005 §8.1 (first-real-data trigger boundary)

> **Disclosure (ADR-012 D4.3).** Outline originated by Code (session-58 drafting
> brief); drafted by the in-harness `plan-drafter` subagent under ADR-013 D1
> phased authority; independent reviewer = Cray at PR merge. Separation INTACT.

---

## Goal

Produce a reusable **PDPA RoPA-lite template** (`docs/conventions/partner-ropa-lite.md`,
tracked/canonical) plus an **NPD-populated example**
(`docs/strategy/public/partner-sim-run1-ropa-example.md`, tracked, SYNTHETIC),
framed so the **DSR / lineage pain** surfaced in partner-sim run-1 (PII embedded
in free-text `note`, actor identity scattered across 4 unlinked places,
back-filled + NTP-drifted timestamps, PK reuse, systematic under-recording) lands
as **direct design input to the ADR-011 audit framework** — not as a standalone
compliance checklist. This is **step-2** of the session-57 audit-framework-prep
arc, parallel in shape to step-1 (intake form v2 + mapping-gap analysis, merged
#306). Scope is **lite** — proportional to a dev/test design-partner trial, not a
full legal RoPA.

RoPA = **Record of Processing Activities**, a Thailand PDPA processor obligation
(Section 40(3); the controller's parallel duty is Section 39). Under the trial
posture the **design partner = controller**, **vero-lite = processor**.

## Acceptance Criteria

- [ ] **AC-1 — Template (tracked, canonical):** `docs/conventions/partner-ropa-lite.md`
  exists, using the same `[generic]` / `[energy]` applicability-tag convention as
  the intake form. It carries one slot per PDPA processor-RoPA element:
  controller / processor / contact (+ DPO if any); purpose(s) of processing;
  categories of **data subjects** + categories of **personal data**; categories
  of **recipients**; **cross-border / residency** posture; **retention / erasure**
  schedule; **technical + organizational security measures**; **data-subject-rights
  (DSR) mechanism**. **Each slot is annotated with the concrete data-quality /
  lineage hook** it connects to (so the template doubles as an ADR-011 input, not
  just a form).
- [ ] **AC-2 — NPD example (tracked, SYNTHETIC):** `docs/strategy/public/partner-sim-run1-ropa-example.md`
  is the template populated from run-1 (§5 classification, §7 standing
  constraints, §8.6 + §9 delivery/refusals, §10 inconvenient facts). The synthetic
  **mess is preserved, never normalized** (refusals + inconvenient facts are
  load-bearing evidence per ADR-0020 D2/R1).
- [ ] **AC-3 — Dedicated "DSR / lineage → ADR-011" section** in the example mapping
  each gap to its design implication: PII-in-free-text `note` → **log-by-reference**
  (can't satisfy erasure when PII is smeared through free-text); scattered actor
  identity (4 unlinked places) → **actor unification**; PK reuse (`TX-07`
  pre/post-2018) + NTP drift (~7 min, 2024) → **lineage / valid-from + reliable
  ordering**; systematic under-recording → **completeness cannot be assumed**.
- [ ] **AC-4 — SYNTHETIC provenance stamp** on both artifacts, mirroring the run-1
  package / intake form wording: ADR-0020 R3 — *informs* the audit framework,
  **does NOT** trip ADR-011 / the first-real-data trigger (PLAN-0005 §8.1).
- [ ] **AC-5 — Cross-references** present and correct: intake form v2 §H (H14–H17);
  mapping-analysis headline #5; ADR-011 §Context earmark; PDPA checklist seed
  (carrying SD-4 residency, SD-5 erasure-vs-append-only, OQ-A lawyer-review as
  **open** risks — not resolved here).
- [ ] **AC-6 — STATUS reconcile** (Code, post-merge): fifth-batch CF block; note the
  9-block soft-cap rotation flag from the session-58 kickoff §2.

## Out of Scope

- ❌ **Authoring ADR-011 itself** — gated on a *real* partner conversation; the
  synthetic run informs but never triggers it (ADR-0020 R3 / PLAN-0005 §8.1). This
  PLAN only *feeds* ADR-011 §Context.
- ❌ **A full legal RoPA** — this is "lite". A Thai PDPA lawyer review is held as
  **OQ-A**, not performed here. This is an engineering-readiness aid, not legal advice.
- ❌ **Resolving SD-4** (residency-guarantee scope) or **SD-5** (erasure vs
  append-only) — the RoPA-lite *surfaces* both; Cray / Legal resolve them later.
- ❌ Re-running partner-sim or re-doing step-1 (intake form v2 / mapping analysis).
- ❌ Building any engine code (auth/RBAC, audit-log immutability, `correlation_id`
  propagation) — those are ADR-011 build items, named here only as design inputs.

## Steps

### Step 1: Draft the template skeleton — `docs/conventions/partner-ropa-lite.md`

Author the canonical template with `[generic]` / `[energy]` tags. One section per
RoPA element (AC-1 list). Under each section add a short **"data-quality / lineage
hook"** line stating which run-1-class challenge that slot exposes — e.g. under
*categories of personal data*, flag free-text fields that may carry embedded PII;
under *retention / erasure*, flag the append-only-vs-erasure tension (= SD-5,
carried open); under *DSR mechanism*, flag that erasure requires raw→canonical
lineage to *find* a subject's records. Open the file with the SYNTHETIC-neutral
"what this is / design principle / applicability tags" header pattern used by the
intake form (the template itself is not synthetic; only the example is).

### Step 2: Populate the NPD example — `docs/strategy/public/partner-sim-run1-ropa-example.md`

Fill every template slot from run-1, **preserving the messiness**:
- **Controller / processor / contact:** controller = NPD (synthetic
  "นครพิงค์ พาวเวอร์"); processor = vero-lite; contact = COO ("ปวีณา"); no DPO (a
  finding — name it). Authority/egress gating: HN.IT/OT + Legal + COO for any
  PII/customer egress, Board for the customer list (§7).
- **Purpose:** dev/test design-partner trial only (§8.6 DPA-in-principle:
  purpose-limited, no re-share, delete at trial end, Legal review first, first cut
  pseudonymized).
- **Data subjects:** operators (`by`), shift-roster staff, field technicians/
  contractors, embedded customer contacts inside `note`.
- **Personal data categories:** `by` = PII; shift log/roster = PII (labor-welfare
  committee gated, §7); `note` free-text = **PII + business-confidential**
  (names embedded, pseudonymize-resistant). Tag plain numerics (`load_mva`,
  `v_kv`, `oil_c`) and business-confidential (customer list, anchor lines,
  protection settings) per §5.
- **Recipients:** vero-lite (processor) under DPA; no onward re-share (§8.6).
- **Cross-border / residency:** on-box default (local LLM, MS-S1); reference SD-4
  as the open scope question; do not resolve.
- **Retention / erasure:** delete at trial end (§8.6); flag the append-only-vs-
  erasure tension as SD-5 (open).
- **Security measures:** OT semi-isolated, single jump-host egress, paper +
  email approval logs (§7) — note these are *partner* controls; vero-lite-side
  auth/RBAC + audit-log immutability are ADR-011 build items (not built — a gap).
- **DSR mechanism:** the hard case — see Step 3.
- **Refusals (§9):** record what NPD **would not release** (customer list + anchor
  map, full `note`, protection settings/single-line, individual roster, OMS
  "system B" historical export = technically impossible). These are the RoPA-lite's
  load-bearing "what can't be cleanly handled" evidence — do not omit or soften.

Stamp the file SYNTHETIC (AC-4).

### Step 3: Write the "DSR / lineage → ADR-011" section (AC-3)

In the example, a dedicated section that, for each run-1 gap, names the design
implication for ADR-011:
- PII-in-free-text `note` → **log-by-reference** (erasure is unsatisfiable when
  PII is smeared through free-text; ties to checklist §5 erasure question).
- Actor identity in 4 unlinked places (paper switching order / shift log / LINE /
  email) → **actor unification** (`AuditMetadata.actor`).
- PK reuse (`TX-07` pre/post-2018) + NTP drift (~7 min, 2024, never corrected) →
  **lineage / valid-from disambiguation + reliable event ordering**.
- Systematic under-recording (quiet off-system anchor-SLA fixes) → **completeness
  cannot be assumed** (the audit log is not a complete record by construction).
Frame each as an *input to* ADR-011, explicitly **not** a decision taken here.

### Step 4: Provenance stamps + cross-references (AC-4 / AC-5)

Add the SYNTHETIC stamp to both artifacts (AC-4). Add cross-refs (AC-5): intake
form v2 §H (H14–H17); mapping-analysis headline #5; ADR-011 §Context earmark;
PDPA checklist seed (carrying SD-4 / SD-5 / OQ-A as open). On the template, add the
intake-form-style sync note (canonical repo copy wins on conflict, CLAUDE.md §4).

### Step 5: Handback → Code commits + reconciles

Hand the two uncommitted draft paths back to Code. Code verifies, commits on a
`docs/*` branch + PR per CLAUDE.md §7 (Cowork/plan-drafter does **not** commit,
ADR-009 D2), merges after Cray review, then reconciles STATUS (AC-6).

## Verification

- **AC-1:** `docs/conventions/partner-ropa-lite.md` exists, carries all 8 RoPA
  slots, each with a data-quality/lineage hook, and uses `[generic]`/`[energy]` tags.
- **AC-2/AC-3:** `docs/strategy/public/partner-sim-run1-ropa-example.md` exists,
  every slot populated from run-1 with the mess preserved (refusals + inconvenient
  facts present, not normalized), and contains the "DSR / lineage → ADR-011" section
  with all four gap→implication mappings.
- **AC-4:** both files carry a SYNTHETIC stamp citing ADR-0020 R3 + the
  "does-not-trigger" PLAN-0005 §8.1 language.
- **AC-5:** grep confirms cross-refs to the intake form, mapping analysis, ADR-011,
  and the PDPA checklist seed; SD-4 / SD-5 / OQ-A appear as **open** (unresolved).
- **AC-6:** STATUS shows the step-2 closeout (fifth-batch CF block) with the
  9-block soft-cap rotation flag noted.

## Open risks (carried, not resolved — per checklist seed §"Surfaced for Cray")

- **SD-4** — scope of the provable-residency guarantee (minimal model+on-box/API
  flag vs rich per-field PII-class). *Recommendation:* start minimal, design
  extensible. **Cray decides.**
- **SD-5** — erasure vs append-only integrity (tombstone-in-log vs crypto-erasure
  vs out-of-log PII store). *Recommendation:* crypto-erasure best preserves
  append-only; it is an ADR-011 D-item. **Cray decides.**
- **OQ-A** — a Thai PDPA lawyer should review before any partner signature. The
  RoPA-lite is an engineering-readiness aid, **not** legal advice. **Held.**

---

_PLAN-0023, step-2 of audit-framework-prep. Drafted by in-harness `plan-drafter`
(ADR-013 D1); Code commits + executes (ADR-009 D2). The two output artifacts are
SYNTHETIC-informed (ADR-0020 R3) and do not trip the first-real-data trigger._
