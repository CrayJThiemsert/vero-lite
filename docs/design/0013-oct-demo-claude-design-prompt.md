# PLAN-0013 Step 3 — Claude Design prompt (OCT stakeholder demo UI)

**Status:** Draft (Code-authored working note — not governance)
**Owner:** Claude Code (drafter) · Cowork (UX/operator-tone refinement, ADR-009 D1 / ADR-013 advisory) · Cray (runs Claude Design + attaches theme images, Step 4)
**Created:** 2026-05-30
**For:** PLAN-0013 Step 3 → feeds Step 4 (Cray runs Claude Design) → Step 5 (Code wires HTML → live API, serves static from FastAPI)

> **Provenance.** Code drafted this from the verified API contracts it holds
> (PLAN-0013 fact-pack + Steps 1–2 as-built, confirmed live against the running
> app on 2026-05-30). The Step-3 artifact is a **Code-drafted working note**, not a
> governance doc (per session-27 kickoff §6 / the tier model). **Cowork may refine
> UX/operator tone**; Cray attaches theme images and runs Claude Design.
>
> **Make-or-break principle (PLAN-0013 AC-template, CLAUDE.md §1).** The UI must be
> **ontology-driven, not hard-coded to energy** — entity types, field labels, and
> enums are rendered from `GET /meta`, never from energy-specific strings. Then
> *swapping the vertical = swapping the ontology + adapter*, with **zero UI-code
> change**. Energy is only the *data that happens to come back* in v1.

## How to use

1. **Cray:** open Claude Design (https://support.claude.com/en/articles/14604416-get-started-with-claude-design),
   paste **everything between the two `═══ PROMPT ═══` rulers** below as the text
   prompt, attach the theme/reference images, and (optionally) link this repo.
2. Export the **standalone HTML**.
3. **Code (Step 5):** wire the exported HTML to the live endpoints and serve it
   static from FastAPI (one process, one URL, no CORS — OQ-4). See *Step 5 wiring
   notes* at the bottom.

---

═══════════════════════════════ PROMPT ═══════════════════════════════

Build a single-page **Operational Control Tower (OCT)** web UI for a distributed
asset-operations platform. This is a **stakeholder demo**: within the first ten
seconds, an operator — energy or supply-chain — should see their *own* operational
data turn into decisions they can trust and act on. Tone: a professional
**control-tower** product the way a working operator expects one to feel — dense,
glanceable, calm under load, trustworthy. Not playful, not a toy dashboard.

**Deliverable:** one self-contained, standalone HTML page (vanilla HTML/CSS/JS, or
a single CDN-loaded framework — no build step, no bundler). It will be served
**same-origin** by the backend, so all data is fetched from **relative URL paths**
(`/meta`, `/objects/...`, `/recommendations`, `/query`). No API keys, no external
data services. Handle loading and error states gracefully (the backend may be
mid-call or a model may be offline).

### Hard principle: the UI is ONTOLOGY-DRIVEN (do not hard-code the domain)

On load, fetch `GET /meta` **first**. Build the UI's entire vocabulary from it:
- object **type names** come from `meta.object_types[].name` — never hard-code
  "Asset"/"Site".
- the **display label** of any record is the value of its `title_key` property
  (fall back to `primary_key`).
- **detail views** are built by iterating that type's `properties[]` — render each
  property's `name` + value; show `enum` properties as colored **status badges**
  using the allowed `enum` values; show `ref` properties (`type == "ref"`) as links
  to the `target` type.
- **relationships** come from `meta.link_types[]` (`from_type` → `to_type`).

The same UI must render correctly for *any* ontology returned by `/meta`. Energy is
just the current data. Treat every domain word as data.

### Navigation

A persistent top bar showing the active vertical (`meta.vertical`), `namespace`,
and `version`, plus a small live/degraded connection indicator. Four primary views
selectable from the top bar (or a left rail):

- **A — Operational Map**
- **B — Anomaly & Decision** (the headline view)
- **C — Ask (natural-language query)**
- **D — Data → Decision Flow**

### View A — Operational Map

*The "where, and in what state" view — every site and asset on one canvas, each
reading its status at a glance.*

Source: `GET /meta` + `GET /objects/{object_type}` for each object type.

- Plot every object that has geographic coordinates (properties whose values
  provide lat/lng) on a **schematic geographic canvas** (an SVG/positioned plot of
  lat/lng — self-contained, no map tiles/keys). In the seed data these are the
  `Site` objects.
- Show the other objects (e.g. `Asset`) grouped under the site they reference
  (via their `ref` property), each with a **status badge** from its enum property.
- Selecting any node opens a **detail panel** built by iterating that type's
  `/meta` properties (label + value rows). One node carries an anomaly — surface a
  warning affordance on it (see View B's over-temp asset) and let the user jump to
  View B.
- A legend of object types + status enums, generated from `/meta`.

### View B — Anomaly & Decision  ← the headline "show me WHY" moment

*This is where the platform earns trust. It doesn't just flag a problem — it shows
its work, then waits for a human to sign off before anything happens.*

Source: `GET /recommendations`, then `POST /recommendations/{action_id}/approve`
and `POST /recommendations/{action_id}/execute`.

For each recommendation render a **decision card**:
- `title`, `description`.
- `confidence` as a labeled bar (0.0–1.0 → %).
- a **status badge** for `status` (`proposed` → `approved` → `executed`; also
  `rejected`).
- the **affected entity** chip(s) from `affected_entities[]`
  (`object_type` · `title` || `primary_key`).
- **THE REASONING TRACE** — render `reasoning_trace[]` as an ordered, vertical
  stepper. Each step: a `kind` badge (e.g. `rule_check`, `llm_inference`,
  `ontology_query`), the `summary` line, and an expandable `detail` (key/value
  dump of the `detail` object). This is the credibility centerpiece: an operator
  should be able to read it top to bottom and follow the system's reasoning the way
  a colleague would walk them through it. Make it prominent and readable, never a
  footnote.
- **Actions:** an **Approve** button (calls approve; on success the card moves to
  `approved` and reveals **Execute**) and an **Execute** button (calls execute; on
  success show `status: executed` and the returned `handler_receipt`). A **Reject**
  control may be shown as a visual dismiss (note: there is no reject endpoint in
  v1 — Approve→Execute is the live round-trip).

The seed scenario has exactly one recommendation: an over-temperature action on a
battery asset (96.5 °C ≥ 90 °C threshold). It should land as the demo's punchline —
the whole story in one card: *anomaly detected → here is the reasoning → a human
approves → it executes.*

### View C — Ask (natural-language operational query)

*Ask the system a question in plain language — and see exactly which records
produced the answer.*

Source: `POST /query` with body `{"question": "<text>"}`.

A **chat-style panel**: a text input + send, a running transcript of Q/A. For each
answer also render a **grounding receipt** (collapsible, shown by default) — this
is the trust feature, do not hide it:
- the **structured query** the engine ran: `structured_query.object_type` /
  `.operation` (`list`|`count`) / `.filters[]` (`property` `op` `value`).
- `result_count` and the **source object ids** (`source_object_ids[]`) as chips —
  "answered from these records."
- a clear **grounded vs. not-found** state: when `grounded` is `false` (and the
  answer is a no-data message), show an explicit *"No matching records — not
  invented"* badge. **This is the anti-hallucination guarantee made visible: the
  system returns 'no data' instead of making something up.**

Offer 4–5 **example-question chips** to seed the conversation, phrased the way an
operator on shift would actually ask: e.g. "How many assets are we running?",
"Which sites do we operate?", "Any readings above 90 °C?", "Which assets are active
right now?", "What's currently in maintenance?". (Phrase chips generically; they are
example content, not hard-coded logic.)

### View D — Data → Decision Flow

*The whole journey on one screen — raw data on the left, a decision someone can
stand behind on the right — so a stakeholder sees how one becomes the other.*

Source: reuse `GET /objects/...` + the `GET /recommendations` payload — **no new
endpoint**. A horizontal 4-stage pipeline with connecting arrows, each stage a
card showing the *real artifact* at that stage:

1. **Ingest** — live counts from `/objects` ("2 Sites · 4 Assets · N events" —
   driven by `/meta` type names + `/objects` counts).
2. **Condition** — the trigger: the over-temperature reading (its
   `measured_value` + unit on the affected asset) **and/or** a user's View-C
   question as an interactive condition.
3. **Process** — the recommendation's `reasoning_trace[]` steps (the engine's
   "why").
4. **Result** — the `RecommendedAction` (title + status) with the approve/execute
   control.

It draws the automatic anomaly path (View B) and the interactive query path
(View C) together into a single "your data → a governed decision" story a
stakeholder can follow end to end. The four stage names are generic — content is
ontology-driven.

### Visual / theme direction

Defer the exact palette, typography, and any branding to the **attached theme
images**. Guardrails for the control-tower feel: high information density without
clutter, and a clear visual hierarchy that tells the operator where to look first.
Use semantic status colors consistently — a calm/ok state, a warning state, an
error/critical state — and reuse the same set for both event severities and entity
statuses. Legible monospace for ids and values; cards and subtle dividers that
organize rather than decorate. Built for a single operator at a desk; responsive to
a laptop screen.

### Data contracts (exact response shapes — bind to these field names)

`GET /meta` →
```
{ "vertical": str, "namespace": str|null, "version": int|null,
  "object_types": [ { "name": str, "primary_key": str|null, "title_key": str|null,
      "description": str|null,
      "properties": [ { "name": str, "type": str, "required": bool,
                        "enum": [str]|null, "target": str|null } ] } ],
  "link_types": [ { "name": str, "from_type": str, "to_type": str,
                    "cardinality": str|null } ] }
```
`GET /objects/{object_type}` →
```
{ "object_type": str, "count": int, "objects": [ { ...raw fields per /meta... } ] }
```
`GET /recommendations` →
```
{ "count": int, "recommendations": [ {
    "action_id": str, "title": str, "description": str, "vertical": str,
    "status": "proposed"|"approved"|"rejected"|"executed",
    "confidence": float, "requires_approval": bool, "suggested_handler": str,
    "reasoning_trace": [ { "step_id": str, "kind": str, "summary": str,
                           "detail": object|null } ],
    "affected_entities": [ { "object_type": str, "primary_key": str,
                             "title": str|null } ] } ] }
```
`POST /recommendations/{action_id}/approve` → one recommendation object (as above).
`POST /recommendations/{action_id}/execute` →
```
{ "action_id": str, "status": str, "handler_receipt": object }
```
`POST /query`  (body `{ "question": str }`) →
```
{ "question": str, "answer": str, "grounded": bool,
  "structured_query": { "object_type": str, "operation": "list"|"count",
      "filters": [ { "property": str, "op": str, "value": str } ], "limit": int } | null,
  "source_object_type": str|null, "source_object_ids": [str],
  "source_objects": [ { ...raw object... } ], "result_count": int }
```

### Seed data (energy vertical — use as the realistic example the mockup renders)

`/meta` returns object types **Site** (primary_key `site_id`, title `name`;
properties incl. `site_type` enum `[substation, microgrid, depot]`, `lat`, `lng`),
**Asset** (pk `asset_id`, title `name`; `asset_type` enum
`[battery, inverter, meter, transformer]`, `capacity_kw`, `status` enum
`[active, maintenance, retired]`, `install_date`, `site_id` ref→Site),
**OperationalEvent** (pk `event_id`; `event_type` enum `[reading, transition,
alarm]`, `severity` enum `[info, warn, error, critical]`, `measured_value`, `unit`,
`occurred_at`, `asset_id` ref→Asset), plus Alert / RecommendedAction / AlertEventLink.

`/objects/Site` → 2: **North Substation** (`site-substation-01`, substation,
13.75, 100.50) · **Riverside Microgrid** (`site-microgrid-01`, microgrid, 13.81,
100.56).
`/objects/Asset` → 4: **Battery Bank A** (`asset-battery-01`, battery, 250 kW,
active, @ North Substation) · **Inverter Unit A** (`asset-inverter-01`, inverter,
500 kW, active, @ North Substation) · **Battery Bank B** (`asset-battery-02`,
battery, 250 kW, active, @ Riverside Microgrid) · **Feeder Meter A**
(`asset-meter-01`, meter, active, @ Riverside Microgrid).

`/recommendations` → 1: title "Investigate over-temperature on asset-battery-01",
`status: proposed`, `confidence: 0.8`, affected `Asset / asset-battery-01 / Battery
Bank A`, reasoning_trace = a threshold-check step ("measured_value 96.5 celsius ≥
threshold 90.0") + an alert-derivation step.

`/query` examples: "how many assets?" → grounded, query `Asset/count`, 4 source ids,
answer "There are 4 assets…". "which assets are in maintenance?" → `grounded:false`,
query `Asset` filter `status=maintenance`, 0 ids, answer "No Asset records match
that query." (render the not-found/not-invented state).

### Acceptance checklist (the design should satisfy)

- [ ] Nothing domain-specific is hard-coded — type names, labels, enums, and
      relationships all come from `/meta`. Swapping `/meta` alone would re-skin the UI.
- [ ] View B makes the reasoning trace the centerpiece and supports the live
      Approve → Execute round-trip.
- [ ] View C surfaces the structured query + source ids, with a clearly visible
      grounded-vs-not-found state.
- [ ] View D walks the 4-stage Ingest→Condition→Process→Result flow over live data.
- [ ] Loading and error states are handled gracefully; works on a laptop screen;
      standalone (no build step); fetches only relative URLs.

═════════════════════════════ END PROMPT ═════════════════════════════

---

## Step 5 wiring notes (Code — after Cray exports the HTML)

- Serve the exported HTML as **static from FastAPI** (mount `StaticFiles` or a
  catch-all route returning the file) so it is **same-origin** with the API — one
  process, one URL, no CORS (OQ-4). Place the export under e.g. `services/api/static/`.
- The prompt instructs the design to fetch **relative URLs**, so wiring should be
  mostly "serve it + verify each fetch hits the real endpoint." Reconcile any field
  names the designer renamed back to the contracts above.
- Expect the recommender to use the **rule fail-safe** when MS-S1/Ollama is down
  (AC-safety) — View B must still render the over-temp action. `/query` (View C)
  needs the LLM; when it is unavailable the endpoint returns `grounded:false` with
  an "unavailable" answer — the UI's not-found/error state covers this.
- MS-S1 reachability for the live `/query` path: the dev box reaches Ollama via the
  `.env` `OLLAMA_HOST` IP override (and now a `ms-s1-max` hosts entry) — see the
  `project_ms_s1_ollama_reachability` note.
- AC-template smoke (Step 6): point `/meta` + `/objects` at a second ontology stub
  and confirm the *same* HTML re-skins with **zero UI-code change**.

## Cowork refinement (optional, ADR-009 D1 / ADR-013 advisory)

Code holds the contracts, so the contract/data-binding sections are authoritative.
Cowork may refine: operator-facing copy/tone, the example-question wording, View-B
decision-card microcopy ("show me why"), and the visual hierarchy guidance — without
changing the field-name bindings. If refined, land it as a follow-up `docs/*` PR.
