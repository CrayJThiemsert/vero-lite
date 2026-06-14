# Partner RoPA-lite — NPD worked example (partner-sim run-1, energy)

```
⚠️  SYNTHETIC — NOT REAL PARTNER DATA  ⚠️
"NPD" is a FABRICATED design-partner persona from the partner-sim rehearsal
(ADR-0020 R3). No org, name, threshold, or data sample below originates from any
real partner. This artifact INFORMS the audit framework and satisfies NO
"first real partner data" trigger (PLAN-0005 §8.1; the ADR-011 gate). It must
NEVER enter a benchmark, REPORT, or governance context as if it were real.
```

> **What this is.** The `docs/conventions/partner-ropa-lite.md` template
> **populated** from partner-sim run-1 — the synthetic energy operator "NPD"
> (`docs/research/private/2026-06-13-partnersim-energy-session58-package.md`,
> gitignored SYNTHETIC). Step-2 of the audit-framework-prep arc (PLAN-0023),
> parallel to step-1's mapping-gap analysis. The mess is **preserved, not
> normalized** — the refusals (§9) and inconvenient facts (§10) are the
> load-bearing evidence (ADR-0020 D2/R1).

---

## RoPA-lite (NPD as controller, vero-lite as processor)

### 1. Controller / processor / contact

- **Controller:** NPD — สมมุติ "บริษัท นครพิงค์ พาวเวอร์ ดิสทริบิวชั่น จำกัด" (a regional
  electricity distributor; **not** กฟภ.).
- **Processor:** vero-lite.
- **Contact:** ปวีณา (รองกรรมการผู้จัดการ สายปฏิบัติการ / COO). **No DPO, no single data
  owner** — a finding (run-1 §8.2: nearest is the system engineer + the maintenance
  secretary *together*; neither can answer alone).
- **Egress gating (run-1 §1 / §7):** หน.IT/OT approves any export; **PII/customer →
  Legal + COO**; customer list → **Board**.

> **Hook.** Release authority is itself split four ways (COO / IT-OT / Legal /
> Board) → the DPA must name one accountable party; today it's a committee.

### 2. Purpose

- **Dev/test design-partner trial only.** Run-1 §8.6 (DPA-in-principle):
  purpose-limited, dev/test only, **no re-share, delete at trial end, Legal review
  first, first cut pseudonymized**.

> **Hook.** NPD already insists on a written purpose + Legal review → record it as
> the binding purpose limitation.

### 3. Data subjects + personal data

- **Data subjects:** operators, shift-roster staff, field technicians/contractors,
  **and customers/persons named inside `note`**.

| field (NPD's name) | class | the mess to know (run-1 §3/§5) |
|---|---|---|
| `by` (operator name/nickname) | **PII** | nicknames collide (2 people share one); some rows blank |
| shift log / roster | **PII** | labor-welfare-committee gated (§7); individual hours are sensitive |
| `note` (free-text Thai) | **PII + business-confidential** | **customer/person names embedded in the text** — pseudonymize-resistant |
| customer list / anchor feeders | business-confidential | trade secret + SLA |
| protection settings / single-line diagram | business-confidential | grid security |
| `load_mva`, `v_kv`, `oil_c` (unbound numerics) | **plain** | technical values only |
| `feeder` / `tx` id | plain* | *but IDs are reused — inconvenient #1 |

> **Hook.** The PII is not confined to a column — it lives inside Thai free-text →
> a column filter can neither find nor erase it.

### 4. Recipients

- vero-lite (processor) under DPA; **no onward re-share** (§8.6). No sub-processors
  in the on-box trial. The OMS "system B" vendor is defunct (inconvenient #3) — no
  live third party there.

> **Hook.** A single recipient keeps erasure-propagation simple — record it so it
> stays that way.

### 5. Cross-border / residency

- **On-box default** (local LLM on MS-S1); **no cross-border transfer** in the trial.
- **SD-4 (open):** the scope of the provable-residency guarantee — not resolved.

> **Hook.** Residency is provable only if each processing path logs where it ran.

### 6. Retention / erasure

- **Retention:** delete at trial end (§8.6).
- **Erasure:** mechanism undefined. **SD-5 (open):** append-only audit integrity vs
  erasure — the `note` free-text PII makes a clean delete especially hard.

> **Hook.** "Delete at trial end" is unsatisfiable for PII smeared through
> free-text unless we adopt log-by-reference or crypto-erasure.

### 7. Security measures

- **Partner-side (run-1 §7):** OT semi-isolated; **single jump-host** egress;
  permit-to-work + lockout/tagout; approval evidence on **paper + email + LINE**
  (not one system).
- **vero-lite-side (gaps → ADR-011):** auth/RBAC, audit-log immutability, access
  logging — **not built**; named here as design inputs only (PLAN-0023 out-of-scope).

> **Hook.** Approval evidence on paper / LINE / email is not queryable → we can't
> evidence "who authorized this processing" without actor unification.

### 8. DSR mechanism — the hard case

- Can we locate **all** of a subject's records on an access/erasure request?
  **Not today:** identity lives in `by` (collides / blank), is **embedded in `note`
  free-text**, and "who did what" sits in **4 unlinked stores** (paper switching
  order / shift log / LINE / email, §1). PK reuse + NTP drift further break
  record-level traceability. → see the ADR-011 section next.

---

## DSR / lineage → ADR-011 (the design-driver section)

Each run-1 gap, and the audit-framework requirement it generates. These are
**inputs to ADR-011 — not decisions taken here** (ADR-011 is gated on a *real*
partner conversation, ADR-0020 R3; the synthetic only feeds its §Context).

| run-1 gap | evidence | ADR-011 design implication |
|---|---|---|
| **PII embedded in free-text `note`** | §5 (customer/person names inside Thai text); §8.6/§9 ("pseudonymize ไม่ทันชุดแรก" → the field is **dropped from the first cut**) | **log-by-reference** — store canonical references, not raw PII inline; erasure is otherwise unsatisfiable |
| **actor identity in 4 unlinked places** | §1 ("กระจายอยู่ 4 ที่ ไม่ได้ link กัน": paper order / shift log / LINE / email) | **actor unification** (`AuditMetadata.actor`) — one resolvable identity per action |
| **PK reuse + clock drift** | inconvenient #1 (`TX-07` pre/post-2018 rebuild = different assets) + #4 (NTP drift ~7 min in 2024, never corrected) | **lineage / valid-from disambiguation + reliable ordering** — `Asset.install_date` as a temporal key; blind ordering can't be trusted |
| **systematic under-recording** | inconvenient #5 (anchor near-misses fixed off-system to dodge an SLA-penalty record) | **completeness cannot be assumed** — the audit log is not a complete record by construction; surface coverage gaps |

---

## What NPD would not release (refusals — §9, load-bearing)

Preserved verbatim-in-spirit (data-room friction is the point, not noise):

- customer list + anchor-feeder map (Board sign-off; trade secret/SLA)
- the **full `note`** free-text (embedded PII, can't pseudonymize in time)
- protection settings / single-line diagram (grid security — IT/OT refuses)
- individual shift roster + hours (labor law / welfare committee)
- OMS "system B" historical export (**technically impossible** — no export
  function, vendor defunct)
- full-fidelity dataset (deferred to on-site deploy, per the processor posture)

> These refusals are exactly the RoPA-lite's "what can't be cleanly handled"
> evidence — they shape the DPA scope and the ADR-011 requirements, and must not be
> softened.

---

## Cross-references

- Template: `docs/conventions/partner-ropa-lite.md`
- Run-1 package (SYNTHETIC, gitignored): `docs/research/private/2026-06-13-partnersim-energy-session58-package.md`
- Intake form v2 §H (H14–H17): `docs/conventions/partner-intake-form.md`
- Mapping-gap analysis, headline #5 (identity & lineage gaps): `docs/strategy/public/partner-sim-run1-mapping-analysis.md`
- PDPA checklist seed (carries SD-4 / SD-5 / OQ-A as open): `docs/research/private/2026-06-13-pdpa-review-checklist.md`
- Downstream: **ADR-011** (§Context earmark); **PLAN-0005 §8.1** (first-real-data trigger)

## Provenance & status

**SYNTHETIC** (ADR-0020 R3) — *informs* the audit framework, does **not** trip the
first-real-data trigger. Evidence base = one synthetic run; a real partner will
surface gaps this one didn't (do not over-fit — Rule of Three waits for a 2nd/3rd
real vertical). PLAN-0023, step-2 of audit-framework-prep.
