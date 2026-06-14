# Partner RoPA-lite — PDPA record-of-processing template (design-partner trial)

> **What this is.** A **lite** Record of Processing Activities (RoPA) we fill in
> for each design-partner dataset, so a PDPA processor obligation (Thailand PDPA
> **§40(3)**; the controller's parallel duty is **§39**) is satisfiable from day 1
> of a dev/test trial. It is **not** a full legal RoPA and **not** legal advice —
> an engineering-readiness aid; a Thai PDPA lawyer reviews before any partner
> signature (**OQ-A**). **Canonical, tracked.** Derived from the partner-sim run-1
> rehearsal; the populated example (SYNTHETIC) is
> `docs/strategy/public/partner-sim-run1-ropa-example.md`.
>
> **Design principle.** Each RoPA slot doubles as an **audit-framework design
> input**: under every slot we record the **data-quality / lineage hook** it
> exposes — because the hard part of PDPA for an operational dataset is not the
> form, it is whether we can actually *find, trace, and erase* a data subject's
> records later. Those hooks feed **ADR-011** (the audit framework).
>
> **Applicability tags.** `[generic]` = vertical-agnostic · `[energy]` =
> energy-specific phrasing/example. Energy-first (Rule of Three — do not
> over-abstract before a 2nd/3rd real vertical).
>
> **Roles (trial posture).** design partner = **controller**; vero-lite =
> **processor**. This template is the processor-side record.

---

## 1. Controller / processor / contact `[generic]`

- **Controller:** the partner org (legal name).
- **Processor:** vero-lite.
- **Contact(s):** the named person who can answer data questions; a **DPO** if one
  exists — *if none, record that as a finding* (it shapes who signs the DPA and who
  fields a data-subject request).
- **Authority / egress gating:** who must approve data leaving the operational
  network (e.g. `[energy]` IT/OT + Legal + COO for any PII/customer egress; Board
  for a customer list).

> **Lineage hook.** If "who may release data" is itself scattered/unclear, the DPA
> can't bind a single accountable party — capture the approval chain now.

## 2. Purpose(s) of processing `[generic]`

- The **single** purpose: a dev/test design-partner trial (model the partner's
  operation; build + validate the ontology/engine). Purpose-limited, **no**
  secondary use.

> **Lineage hook.** A narrow, written purpose is what makes later
> purpose-limitation auditable; a vague purpose → unprovable compliance.

## 3. Categories of data subjects + personal data `[generic]`

- **Data subjects:** e.g. `[energy]` operators, shift-roster staff, field
  technicians/contractors, **and any third parties named inside free-text**.
- **Personal data categories:** tag each field **PII** / **business-confidential**
  / **plain**. Flag **free-text fields that may carry embedded PII** separately —
  they are the hard case (see §8).

> **Lineage hook.** PII smeared through free-text can't be located by a column
> filter → drives **log-by-reference** + an explicit free-text PII strategy.

## 4. Categories of recipients `[generic]`

- Who receives the data: here, vero-lite (processor) under DPA; **no onward
  re-share**. Record any **sub-processors**.

> **Lineage hook.** Each recipient is an erasure-propagation target — an
> unrecorded recipient is an un-erasable copy.

## 5. Cross-border / residency posture `[generic]`

- Where processing happens: **on-box default** (local LLM, e.g. `[energy]` MS-S1);
  external API (e.g. Claude) only with consent + non-PII (CLAUDE.md §8). Record any
  transfer.
- **Open — SD-4:** the *scope* of the provable-residency guarantee (minimal
  on-box/API flag vs rich per-field PII-class). Carried, not resolved here.

> **Lineage hook.** Residency is provable only if every processing path logs where
> it ran — ties straight to the audit framework.

## 6. Retention / erasure schedule `[generic]`

- **Retention:** delete at trial end (the DPA term).
- **Erasure mechanism:** how a delete is actually executed.
- **Open — SD-5:** the tension between append-only audit integrity and erasure
  (tombstone-in-log vs crypto-erasure vs an out-of-log PII store). Carried.

> **Lineage hook.** Append-only logs and "delete on request" conflict; resolving
> it is an ADR-011 decision.

## 7. Technical + organizational security measures `[generic]`

- **Partner-side controls** as they exist today (e.g. `[energy]` OT semi-isolated,
  single jump-host egress, paper/email approval logs).
- **vero-lite-side controls** the trial requires (auth/RBAC, audit-log
  immutability, access logging) — mark each **built vs gap** (the gaps are ADR-011
  build items, not built under this PLAN).

> **Lineage hook.** A security measure you can't evidence (no access log) is a
> security measure you can't audit.

## 8. Data-subject-rights (DSR) mechanism `[generic]`

- How an access / rectification / erasure request is served: can we **locate all of
  a subject's records** — across systems, free-text, and any unlinked actor stores?
  If not, **say so — it's the core finding.**

> **Lineage hook.** DSR feasibility is the integral of everything above: stable
> identity (§3), recipient tracking (§4), residency logging (§5), an erasure
> mechanism (§6), and access logging (§7). This is where RoPA-lite meets ADR-011.

---

## How this maps onward (for us, not the partner)

- **§3 / §8** (free-text PII, scattered identity) → **log-by-reference** + **actor
  unification** (ADR-011 §Context).
- **§6** (erasure vs append-only) → **SD-5**, an ADR-011 D-item.
- **§5** (residency scope) → **SD-4**.
- Every slot's **lineage hook** → the audit framework's requirements list.

## Provenance & status

Derived from one **synthetic** run (partner-sim run-1, **ADR-0020 R3** — *informs*,
does **not** trip the first-real-data trigger, PLAN-0005 §8.1). Lite by design;
superseded by a real RoPA after the first real partner + lawyer review (OQ-A).
Populated example (SYNTHETIC): `docs/strategy/public/partner-sim-run1-ropa-example.md`.

_Sync note: this is a canonical repo instrument; if it is ever pasted into a
partner-facing doc or a Claude project, the repo copy wins (CLAUDE.md §4)._
