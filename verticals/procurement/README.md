# `procurement/` — Procurement vertical (PLAN-0036 Stage 1)

**Status:** Hand-authored, the **4th vero-lite vertical** (PLAN-0036 Stage 1).
A **pure-config plugin** on the shipped ADR-016 procedure engine + ADR-0023
auto-discovery — **zero `services/` engine edit** (CQ-1). Synthetic Tier-1 demo
(ADR-0015 D1); no live DB (SD-2).
**Asset-role:** `Equipment` · **Site-role:** `Plant` (geo). The pitch target is
**Fastenal Thailand** — automotive / auto-parts manufacturing in the EEC
(Chonburi–Rayong); all identifiers in `data_adapter/synthetic.py` are **abstract**
(no partner brand).

## Problem

A **critical production asset fails** (a CNC machining center); its spare is out
of stock and the line is down. The spare must be **sourced under governed
emergency procurement** — fast, but without dropping the controls (compliance,
authority limits, separation of duties, audit) that emergencies tempt teams to
skip.

## Decision / workflow

Two procedures on **one governed engine + agent** (`procedures.yaml`):

- **Hero — `emergency_sourcing_round`** (7 steps): criticality band → source
  (on-contract default; RFQ→AVL exception) → per-criterion compliance → tiered
  DOA approval + emergency waiver → issue PO → audit.
- **Calm-path — `low_stock_reorder_round`** (3 steps): the routine MRO reorder,
  the single-tier contrast on the same engine.

**Governed ≠ generated (L-3):** the LLM only **drafts/summarises** (PR enrich,
quote summary, justification + exec-summary, audit summary). It **never** selects
the supplier (a scored rule), **never** sets a threshold (authored band), and
**never** approves (the human gate). The demo's AI-assist throughput panel makes
this visible: *"AI drafted N · 0 supplier-selections · 0 approvals."*

## The 5-facet map (SD-4 — the schema substrate)

Each hero step is annotated in `procedures.yaml` with a structured **5-facet**
field — the first-class typed `facet:` field (ADR-016 D2 Amendment 2026-06-25 /
PLAN-0038). It was **comment-only** through Stage-1 (because
`services/engine/procedures/spec.py` declared `Step` with `extra="forbid"`, so a
real `facet:` key would be rejected); the **Stage-2** amendment promoted it to a
typed, validated, optional field (the net-new `decision_condition` + `llm_assist`
typed; `input`/`output`/`governance` as non-authoritative notes, D2-A2). This map
is the **template substrate**: **Stage 3** extracts the generalized procedure
generator from it (and it cross-checks aquaculture's procedure).

| Hero step | kind / autonomy | input | decision-condition | llm-assist | output | governance |
|---|---|---|---|---|---|---|
| `intake` | query / — | PR / CMMS work-order | — | enrich / auto-fill PR | enriched PR set | — |
| `judge` | evaluate / — | intake set | **deterministic criticality band** (`0.8`/above) | — | criticality verdict | determinism invariant (ADR-0019) |
| `source` | action / **auto** | judge (critical) | **on-contract default; RFQ→AVL exception** | summarise quotes | candidate quote(s) | **selection = scored rule, not the LLM** |
| `compliance` | evaluate / — | source set | **per-criterion** AVL · tax · cert · sanctions · single-source | — | per-criterion pass/fail | **blocks the PO on any fail** |
| `approve` | action / **gated** | compliance pass | **DOA tier band (฿)** | draft justification + exec-summary | approval decision | **tiered DOA + emergency waiver + SoD; human approves** |
| `issue_po` | action / **gated** | approved | — | — | PurchaseOrder | human-gated write |
| `audit` | action / **auto** | full run | — | decision-summary | audit record | ties each row to the control that governed it |

The five facets — **input · decision-condition · llm-assist · output ·
governance** — are the common attributes the future generalized schema
([[project-vero-ultimate-target-generative-procedures]]) is extracted from.

## Credibility musts (L-6) encoded in the synthetic hero

- **DOA tiered in ฿:** หน.จัดซื้อ ≤฿50k · ผจก.จัดซื้อ ≤฿500k · ผจก.โรงงาน ≤฿2M ·
  ผอ. >฿2M. The hero PO (**฿2.15M**) escalates to **ผอ.**; the calm PO (฿45k) sits
  in tier-1.
- **Emergency waiver** relaxes 3-bid/sole-source **but escalates the approver +
  forces a logged justification** — it never skips a gate.
- **On-contract default / RFQ exception** (never RFQ a stocked contracted item).
- **Per-criterion compliance** blocks the PO — the synthetic alt supplier's
  expired certificate blocks its quote (the gate biting, not theater).
- **Separation of Duties** — the PO's `approver_chain` keeps requester ≠ approver.

## Run this vertical

The vertical auto-registers (no `services/api/main.py` edit). Env block (paste
into your local `.env`) and boot `uvicorn`:

```dotenv
OCT_VERTICAL=procurement
OCT_RECOMMEND_THRESHOLD=0.8
OCT_RECOMMEND_DIRECTION=above
OCT_RECOMMEND_ENTITY_TYPE=Equipment
OCT_RECOMMEND_ENTITY_ID_FIELD=equipment_id
OCT_RECOMMEND_LABEL="equipment criticality"
OCT_RECOVERY_VALUE=0.1
OCT_RECOVERY_DESCRIPTION="spare installed; equipment restored to service"
```

The **demo UI** (the 5 operator surfaces — worklist · process timeline · approval
money-screen · graduation moment · monitoring dashboard) is the procurement scene
group in the PLAN-0033 story overlay (`services/api/static/assets/view-story.js`);
open the story mode (the **S** key) and page to the procurement scenes. See the
`run-oct-demo` runbook for the walkthrough. A live MS-S1 LLM run is **host-state /
Cray-gated** and is **not** an acceptance gate — the offline test suite is the
gate (CLAUDE.md §8).

## Files

| File | Purpose |
|------|---------|
| `ontology/procurement_v0.yaml` | 6 base OCT object_types + 6 procurement extensions + link_types (ADR-008) |
| `procedures.yaml` | the agent + hero (7-step) + calm-path procedures, with the typed 5-facet `facet:` fields |
| `handlers.py` | the action-type vocabulary as no-op receipt stubs (real ERP/email I/O ships with the partner) |
| `data_adapter/` | the deterministic synthetic Tier-1 hero + calm-path dataset |
| `generated/` | codegen artifacts (gitignored; `vero-lite generate procurement`) |

Tests: `tests/services/engine/test_procurement_vertical.py` (offline governance +
run invariants).
