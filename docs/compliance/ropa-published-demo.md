# RoPA-lite instance — the published OCT demo

> **What this is.** A populated instance of
> [`docs/conventions/partner-ropa-lite.md`](../conventions/partner-ropa-lite.md) for
> **one dataset**: what visitors type into the publicly reachable OCT demo. Required by
> ADR-0035 D6; filled under PLAN-0100 Step 10 (AC-10).
>
> Not legal advice and not a full legal RoPA — an engineering-readiness record, the same
> standing the template claims for itself. A Thai PDPA lawyer reviews before any real
> partner signature (template OQ-A); this instance covers a **synthetic** demo and no
> partner data.
>
> ⚠️ **Roles are INVERTED relative to the template.** The template's trial posture is
> partner = controller / vero-lite = processor (`partner-ropa-lite.md:22-23`). For the
> public demo there is no partner: **vero-lite is the controller** and **Cloudflare is a
> named recipient/processor** (ADR-0035 D6). Read every slot below with that swap in mind
> — it changes who owes the duty, not just who is named.

**Status:** populated, offline. The deployment it describes does not exist until
PLAN-0100 Phase 3/5 land; this record is written **before** exposure, not after, which is
the point of writing it at all.

---

## 1. Controller / processor / contact

- **Controller:** vero-lite — Jirachai Thiemsert, sole operator. No DPO exists, and per
  the template that absence is **recorded as a finding**, not left blank: a one-person
  controller is also the person who fields every data-subject request, so the DSR path in
  §8 has no escalation tier and must be workable by one person on an ordinary day.
- **Recipient / processor:** **Cloudflare** — the access gate processes **visitor email
  addresses**, and all traffic transits the vendor edge (ADR-0035 D3/D6).
- **Sub-processors:** none beyond the above.
- **Authority / egress gating:** Cray alone. Deploying the published surface, warming a
  model, or any command touching MS-S1 is a **host-state action requiring explicit Cray
  go** (CLAUDE.md §8) — the same gate that governs the data here governs the box.

> **Lineage hook.** One accountable party is unambiguous; the risk is the opposite of the
> template's — not "who may release data", but no second pair of eyes. §8 compensates by
> keeping the DSR path to commands a single operator can run.

## 2. Purpose(s) of processing

- **The single purpose:** operating a public demonstration of the OCT wedge, and
  understanding what visitors ask it so the demo can be improved.
- Purpose-limited. **No** secondary use: no marketing profiling, no model training, no
  enrichment, no sale, no onward re-share.

> **Lineage hook.** "Improve the demo" is narrow enough to audit against the stored field
> set in §3 — every field there earns its place under this purpose or does not exist.

## 3. Categories of data subjects + personal data

- **Data subjects:** demo visitors, and **any third party a visitor names inside typed
  free text**. The second class is the hard one and cannot be enumerated in advance.
- **Personal data categories:**

| Field | Class | Where |
|---|---|---|
| Visitor-typed free text (`text`) | **PII-capable** — free text may carry embedded PII regardless of what the notice asks | our prompt log |
| Visitor email address | **PII** | **Cloudflare only** — the access gate. Never copied into our log |
| UTC timestamp, route, vertical, model, outcome, arm | plain — operational metadata | our prompt log |

- **Explicitly NOT stored by us:** IP address, request headers, any gate identity
  (ADR-0035 D6, ratified OQ-2). The vendor edge keeps its own access-log metadata under
  its own retention; that is Cloudflare's record, not a copy of ours.
- The stored set is **closed, not minimal** — enforced in code by
  `services/engine/llm/prompt_log.py` and asserted by set-equality in
  `tests/api/test_prompt_log.py`, so a field added later reddens a test rather than
  quietly widening this record.

> **Lineage hook.** PII smeared through free text cannot be located by a column filter.
> That is why §8's erasure path is line- and file-scoped rather than identity-scoped —
> there is no stable subject identity in this dataset to filter on, **by design**.

## 4. Categories of recipients

- **Cloudflare** — gate emails + edge transit. The only recipient.
- **No onward re-share.** The log never leaves the serving host except for Cray's local
  analysis.

> **Lineage hook.** Cloudflare is therefore an **erasure-propagation target**: §8's DSR
> path is incomplete unless it files the vendor-side request too.

## 5. Cross-border / residency posture

- **Inference:** on-box. The local model runs on MS-S1 (Thailand); the demo's LLM routes
  never call an external model API.
- **Transit + gate:** Cloudflare's global edge — a **cross-border transit and processing
  path**, named here rather than assumed away.
- **At rest:** the prompt log is LAN-only on the serving host, in a named volume; never
  committed to the repository.

> **Lineage hook.** The residency claim is provable for inference (one configured host)
> and only *stated* for the vendor edge, which is the vendor's to evidence. Recorded as
> the weaker of the two.

## 6. Retention / erasure schedule

- **Retention: 90 days rolling.** Files older than **90 days** are deleted.
- **Erasure mechanism — three paths, per ADR-0035 D6:**
  1. **Automatic rotation at 90 days**, executed on the write path (there is no scheduler
     on the serving host, so retention enforced by cron would be a promise rather than a
     control). Implemented in `prompt_log.rotate`; tested, including the boundary and the
     name-vs-mtime rule.
  2. **A manual purge command**, documented in
     [`docs/runbooks/published-demo-operations.md`](../runbooks/published-demo-operations.md).
  3. **A data-subject deletion request honored within 30 days** — §8.
- **Who may read: Cray (Jirachai Thiemsert) only** — sole operator and controller of this
  dataset.

> **Lineage hook.** The template's §6 open question (append-only audit integrity vs
> erasure) **does not bite here**: the prompt log is not the tamper-evident audit chain,
> carries no hash links, and nothing downstream reads it. Deleting a line breaks nothing —
> which is exactly why this dataset can promise erasure when the audit chain cannot.

## 7. Technical + organizational security measures

| Control | State |
|---|---|
| Deny-by-default route allowlist at the edge proxy | **owed** — PLAN-0100 Step 8 |
| No published `ports:` on any service | **owed** — Step 8 |
| `API_AUTH_ENABLED=true`; state-changing routes keyed | **built** |
| Per-IP rate cap on LLM routes (10/min, burst 20) | **owed** — Step 8, proxy config |
| Global in-flight LLM cap (1, fast-fail) | **built** — PLAN-0100 Step 6 |
| Prompt log closed field set + rotation | **built** — Step 7 |
| Persistent in-app D6 notice | **built** — PLAN-0100 Step 5 (published profile only; not dismissable) |
| Access logging over the prompt log itself | **gap** — nobody logs Cray reading it |

> **Lineage hook.** The last row is an honest gap, not an oversight: with a single reader
> who is also the controller, a read-access log would have no independent auditor. Named
> so it is a decision rather than a silence.

## 8. Data-subject-rights (DSR) mechanism

**Honored within 30 days.** Full procedure:
[`docs/runbooks/published-demo-operations.md`](../runbooks/published-demo-operations.md)
§DSR.

- **Can we locate all of a subject's records? Partly — and the limit is the core
  finding.** This dataset stores **no subject identifier at all** (§3), by ratified
  design. So a request cannot be served by looking someone up. It is served by:
  - **Gate email** — the one identified surface. Removed from the vendor allowlist, and a
    vendor-side deletion request filed with Cloudflare (§4).
  - **Typed free text** — located by **content search** over the prompt log, using
    whatever the requester can tell us they typed, then deleting the matching lines or the
    day's file.
- **The honest statement:** if a visitor typed something identifying and cannot recall it,
  we cannot find it, because we deliberately kept nothing that would let us. Erasure of
  the whole dataset within 90 days is automatic regardless, and a full manual purge is one
  command.
- **Every DSR action is noted in this instance** (§9) — the record is the evidence.

> **Lineage hook.** DSR feasibility here is bounded by an intentional absence of identity,
> not by a missing capability. That trade is the right one for a demo and would be the
> **wrong** one for partner operational data, where ADR-011's log-by-reference work
> applies instead.

## 9. DSR + purge action log

Append one row per action. Empty is the correct state before exposure.

| Date | Action | Scope | Requester (if DSR) | Vendor request filed | By |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

---

*PLAN-0100 Step 10 (AC-10). Roles per ADR-0035 D6; template
`docs/conventions/partner-ropa-lite.md` §6/§8. Retention and DSR figures — 90 days, 30
days — are ADR-0035 D6's, restated verbatim, not re-decided here.*
