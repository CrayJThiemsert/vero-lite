# Mapping-gap analysis — partner-sim run-1 (energy / NPD) → canonical model

> **What this is.** Step-1 of the partner-sim follow-up: a **mapping rehearsal**.
> We take the run-1 synthetic package (energy operator "NPD" —
> `docs/research/private/2026-06-13-partnersim-energy-session58-package.md`,
> gitignored SYNTHETIC) and rehearse mapping it into our **canonical energy
> model**, to find where the mapping *breaks*. Every break = something we should
> have asked. Those breaks drive the real-partner intake form v2
> (`docs/conventions/partner-intake-form.md`). Tracked (the *analysis* is repo
> knowledge); the NPD package itself stays SYNTHETIC + gitignored (ADR-0020 R3 —
> informs the form, does **not** trigger ADR-011).
>
> **Method:** energy-first, lightweight (no PLAN). The mapping work is Code's —
> reading our own schema is correct (R1 insulates the *sim*, not the receiver).

## The canonical target (what we map INTO)

- **Ontology** (`verticals/energy/ontology/energy_v0.yaml`): `Asset`
  {`asset_id`, `name`, `asset_type ∈ {battery, inverter, meter, transformer}`,
  `capacity_kw`, `status`, `install_date`, `site_id`}; `Site`
  {`site_type ∈ {substation, microgrid, depot}`}; `OperationalEvent`
  {`measured_value`, `unit`, `severity ∈ {info, warn, error, critical}`,
  `occurred_at`, `asset_id`}; `Alert`; `RecommendedAction`
  {`action_type ∈ {restart, isolate, dispatch_technician, escalate}`}.
- **Procedure** (`verticals/energy/procedures.yaml` — `substation_health_sweep`):
  read **temperature** per active Asset → `judge` vs a **single** over-temp
  threshold (breach/watch/ok, direction=above) → **gated restart**. One
  parameter, one threshold, one action.
- **Verdict** (`services/engine/procedures/verdict.py`): `classify_verdict` =
  breach/watch/ok from `(value, threshold, direction, watch_margin)`.
- **Judgment** (`services/engine/llm/structured.py` — `LlmJudgment`):
  `affected_entities`, `suggested_handler` (enum = registered handlers),
  `handler_payload`.

## The mapping table (NPD as-given → our model)

Classification key: **clean** (direct) · **transform** (deterministic convert) ·
**disambiguate** (needs extra info to be correct) · **MISSING** (our model has
no slot) · **PII** (privacy/lineage concern).

| NPD as-given | our model slot | class | what breaks → form implication |
|---|---|---|---|
| `feeder` F-xx (22 kV), recloser, RMU, switching station | `Asset.asset_type` enum {battery/inverter/meter/transformer} | **MISSING** | their asset taxonomy ≠ ours → *enumerate their asset types, don't force-fit our enum* |
| `tx` TX-xx | `Asset.asset_type=transformer` | disambiguate | clean type, but **ID reuse** (below) |
| 2× 115/22 kV station + switching station | `Site.site_type` {substation/microgrid/depot} | **MISSING** | "switching station" absent → *list their site types* |
| `load_mva` (sometimes **Amps**) | `OperationalEvent.measured_value`+`unit` | transform | mixed unit per-row → *unit explicit per reading; flag legacy mixed-unit columns* |
| `v_kv` (sometimes **V** sec.) | `measured_value`+`unit` | transform | same unit-drift class |
| `oil_c` (sometimes **raw ADC**) | `measured_value`+`unit=°C` | transform | needs a calibration map → *which values are calibrated vs raw* |
| **3 parameters** (load + voltage + oil-temp), each own bands | procedure judges **1** (temperature) | **MISSING (structural — headline #1)** | *per-parameter spec: unit + watch/act threshold + action + approver, FOR EACH reading* |
| their thresholds (load 6.4/7.6, oil 96/104, undervolt 20.6) | one over-temp threshold | **MISSING** | bands are per-parameter + two-tier (watch/act) → *capture both tiers per parameter* |
| `status_note` (Thai: ปกติ/เฝ้าระวัง/เกินพิกัด) | verdict breach/watch/ok | disambiguate | their words, not standardized → *give your status vocabulary + the numeric rule behind each* |
| actions: reset-reclose / isolate-restore / dispatch / **loadshed** / permit-to-work | `action_type` {restart/isolate/dispatch_technician/escalate} | **MISSING + disambiguate** | **loadshed** has no slot; "restart"=recloser-reset ≠ asset-restart → *list actions + meaning + approval limit* |
| (no severity field) | `OperationalEvent.severity` {info/warn/error/critical} | **MISSING** | they don't tag severity → *do you have a severity field, or is it inferred/free-text?* |
| `occurred_at` back-filled + **NTP drift 7 min (2024)** | `occurred_at` (required) | transform + disambiguate | timestamps unreliable → *how recorded; known drift/back-fill periods* (audit lineage) |
| `TX-07` reused pre/post 2018 rebuild | `Asset.asset_id` (stable PK assumed) | **disambiguate** | PK not stable over time → *are IDs reused? since when? valid-from date?* (our `install_date` could disambiguate) |
| `note` free-text (Thai) + `by` (operator) | `description` (string) / — | **PII** | names embedded in free-text → *which fields are free-text + may carry PII* (PDPA, log-by-reference) |
| actor identity in 4 unlinked places (paper / shift log / LINE / email) | `AuditMetadata.actor` (ADR-011) | **MISSING** | "who did what" not unified → *where is actor identity recorded; one system or several* |
| events systematically under-counted (SLA "quiet fixes") | — (assumes complete log) | **MISSING** | completeness can't be assumed → *event types under-recorded? incentive not to log?* |

## Headline structural gaps (what actually shapes the form)

1. **Single-parameter vs multi-parameter (the big one).** Our procedure judges
   ONE reading (temperature → restart). NPD runs on **load (MVA) + voltage (kV)
   + oil-temp (°C)**, each with its own two-tier band (watch/act) and its own
   action. The form must elicit a **per-parameter spec** — for *each* reading a
   partner monitors: the unit, the watch threshold, the act threshold, the
   action taken, and who approves it. (This is also a *product* signal: a single
   over-temp procedure under-models a real distribution operator.)
2. **Action vocabulary is incomplete + semantically loose.** `loadshed` has no
   slot; NPD's "restart" is a recloser reset, not an asset restart. Ask for
   their action list + a one-line meaning + the approval limit each — so we
   extend the vocabulary deliberately (not force-fit) and bind semantics.
3. **Severity/verdict lives in free-text, not a field.** Their Thai
   `status_note` carries the judgment. Ask for the status vocabulary AND the
   numeric rule behind each word — that is what `classify_verdict` needs.
4. **Asset/site taxonomy mismatch.** Feeder / recloser / RMU / switching-station
   aren't in our enums. Ask them to enumerate their asset + site types (we
   extend the enum per the Rule-of-Three, not guess).
5. **Identity & lineage gaps (feed ADR-011).** PK reuse, scattered+unlinked
   actor identity, back-filled/NTP-drifted timestamps, PII-in-free-text,
   systematic under-reporting — each is an audit-framework design input, and
   each becomes a data-quality question on the form.

## What the run-1 one-pager/seed got right (keep)

The six original asks (people+authority, data dictionary + named owner, a time
window with edge cases, volumes+cadence, partner-labeled classification,
DPA+pseudonymization) are all still valid — NPD answered them usefully. The gap
is **structure**, not topic: the asks need to become **per-parameter /
per-asset-type / per-action** and add explicit **data-quality** questions, so
the input arrives mapping-ready instead of as prose we reverse-engineer.

## Scope / provenance

Energy-first; `[generic]` vs `[energy]` field applicability is marked in the
form. Evidence base = **one synthetic run** (NPD) — a real partner will surface
gaps this one didn't (do not over-fit; the Rule-of-Three abstraction waits for a
2nd/3rd real vertical). SYNTHETIC provenance per ADR-0020 R3: this analysis
*informs* the form and the eventual ADR-011 audit framework, and **does not**
trip any first-real-data trigger.

## References

- Run-1 package (SYNTHETIC, gitignored): `docs/research/private/2026-06-13-partnersim-energy-session58-package.md`
- Canonical model: `verticals/energy/ontology/energy_v0.yaml`, `verticals/energy/procedures.yaml`, `services/engine/procedures/verdict.py`, `services/engine/llm/structured.py`
- Derived instrument: `docs/conventions/partner-intake-form.md`
- Venue + provenance: ADR-0020 (R3); runbook `docs/runbooks/partner-sim-operation.md`
- Downstream: ADR-011 (earmarked audit framework — the identity/lineage gaps feed its §Context); PLAN-0005 §8.1 (mapping layer / dbt trigger = first real source)
