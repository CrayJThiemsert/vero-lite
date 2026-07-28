# PLAN-0096: Fleet flow completion — Phase 1, Lean KPI-first

**Status:** Draft
**Owner:** Claude Code (execution); Cowork drafted (ADR-009 D1, s184 dispatch)
**Created:** 2026-07-28
**Related ADRs:** ADR-0034 (governed exception family — Proposed; precondition for Step 5), ADR-0025 (typed AT-2 content + prose-lint), ADR-0026 (live run-checks), ADR-0032 (D1 pilot wedge + 1-KPI charter), ADR-016/ADR-007 (run + write-gate substrate)

> **Drafting provenance.** Cowork-drafted (uncommitted) per the session-184 dispatch — mechanical G2
> routing (CLAUDE.md §6), not a quality judgment. Code R2s + commits via PR (ADR-009 D2).
> **Author≠reviewer disclosure (ADR-012 D4.3):** originators = the design partner (18 answers),
> Cray (typed Phase-1 = Lean-KPI-first + ADR-first picks, 2026-07-28), Code (dispatch fact-pack);
> drafter = Cowork. Engine citations verified at `main`=`7b84fa2`; PLAN number 0096 from the
> dispatch fact-pack — Code re-verifies next-free at commit. Keep Status **Draft** until Complete.

## Goal

Complete the fleet_maintenance flow to real-use evaluation shape for the design partner —
**Lean KPI-first** (Cray's LOCKED pick): no live API integration anywhere; every input arrives by
human-initiated capture, CSV export + human confirm, or authored config; the ONE new outbound
surface is LINE notify. The pilot's **1-KPI charter** (partner's own words, Q16):

> *"ถ้าผมตอบได้ทุกบาทว่า เงินซ่อมก้อนนี้ ใครอนุมัติ ซื้อจากใคร ทำไมซื้อ ผมว่าคุ้มแล้ว
> ประหยัดได้เท่าไรเป็นโบนัส"*
> → **KPI = % of repair spend fully traceable (who approved · bought from whom · why).**
> Savings are explicitly a bonus, not the KPI. Proxy metric (Q17): time to answer an audit
> question (today: LINE archaeology up to 2 months back).

Phase 1 delivers: case capture from minute 1, the quote evidence pack, real governance numbers,
E-1 (three-quote threshold in the signal feed), E-2 (the ADR-0034 ratification window), E-3 (the
sole-source evidence-alternative — additive-trivial per ADR-0034 D4, so it lands here), the thin
post-approval task-chain, LINE notify, the month-end Express-shaped export, and PM real data.
Personas bind the design: **น้องเมย์** is operator №1 (photo-first, minimal typing, aggregates every
document); the owner sees summaries + LINE nudges only; the trail is framed as **protecting**
ต้อม/วิรัช (evidence of good decisions), never surveillance.

## Acceptance Criteria

Binding oracle rule for every AC (dispatch return contract): no AC may be satisfiable by mocking
the gate/waiver under test (the LLM stub per CLAUDE.md §8 is the only permitted fake besides
transport/clock injection); for each AC, construct the counterexample — if the test still passes
with the behavior silently broken, fix the test first. TODO/`pass` stubs count as vacuous.

- [ ] **AC-1 — Real ladder + boundary semantics.** Fleet `doa_tier` floors encode the partner's
  inclusive-ceiling phrasing (Q9: ≤5,000 ต้อม / 5,001–30,000 วิรัช / >30,000 owner) with the
  engine's inclusive floors: `"0"` / `"5001"` / `"30001"` THB; per-truck `minor_repair_ceiling_thb`
  default 5001 (breach ⇔ quote > ฿5,000). Boundary oracle: 5,000 → no governed run; 5,001 → วิรัช
  tier; 30,000 → วิรัช tier; 30,001 → owner tier. `GUESS — รอแก้` stamps for ladder + ceilings
  removed; provenance comments cite the REAL partner answers. Counterexample: floors `"5000"`/`"30000"`
  would route 5,000/30,000 one tier too high — the boundary tests fail.
- [ ] **AC-2 — No cross-vertical drift.** Resolved governance config hashes of procurement,
  supply_chain, building_materials, energy, aquaculture are BYTE-IDENTICAL across the whole
  Phase-1 diff (fixture hash-equality test). Counterexample: an always-serialized new `None` field
  (ADR-0034 D6) flips every hash — this test is the tripwire.
- [ ] **AC-3 — Case capture from minute 1.** A mobile-first, human-opened case (truck pick +
  photo attach, zero further required typing) exists; the governed run's intake row carries the
  `case_id` so evidence links end-to-end. No auto-detection path exists anywhere (Q1).
- [ ] **AC-4 — Quote evidence pack + computed signal (E-1 + E-3).** Quotes attach as
  PDF / LINE-exported photo / photographed paper with vendor + typed amount; the pack computes the
  `compliance.three_quote` signal and stamps `three_quote_basis`. Decision matrix oracle (real
  `evaluate_compliance`, no mocks): (48,000; 1 quote; no justification) → **blocked**; (48,000; 3
  quotes) → pass, basis `three_quotes`; (48,000; 1 quote; sole-source justification) → pass, basis
  `sole_source_justified`; (25,000; 1 quote) → pass, basis `under_threshold`; boundary 30,000 →
  under_threshold vs 30,001 → quotes-required; **breach row with NO signal map → `RuleGateError`
  (fail closed)**. Counterexample: today's reshape `default three_quote: true` would pass the
  no-evidence case — that default is removed and the fail-closed test proves it.
- [ ] **AC-5 — E-2 ratification state machine (ADR-0034 D3), full case-coverage matrix.** All of:
  happy (waiver-invoked provisional resolve → effects execute → `RESOLVED_PROVISIONAL` + audit
  ratification block, NO `governed_decision` tie → ratify by owner within window → `RESOLVED` +
  tie naming the ratifier); boundary (`due_at` edge, `window_days=1` minimum); fail-closed (no
  authored window ⇒ provisional branch unreachable; unresolvable attested approver ⇒ refused;
  RF-1 on recorder); adversarial (requester attempts ratify ⇒ SoD block; lower-tier attempts
  ratify ⇒ tier-authority block; double-ratify ⇒ idempotent-by-state; provisional attempt on a
  non-waiver gate ⇒ refused); refusal (recorded disposition, nothing un-executes); concurrency
  (ratify vs concurrent resolve/resume ⇒ optimistic-lock loser gets `StaleDataError`).
  `resume_run` advances from `RESOLVED_PROVISIONAL`; `ratification_state(step, now)` returns
  pending/ratified/overdue/refused purely (injected `now`). Counterexample per the dispatch: if
  ratification were silently skipped, the tie-timing test and the overdue-computation test fail.
- [ ] **AC-6 — Only-when-supplied schema discipline.** A waiver WITHOUT `ratification_window_days`
  serializes byte-identically to the pre-change model (serialization + hash test), per ADR-0034
  D6. This is AC-2's schema-level twin; both must exist (one catches YAML drift, one catches
  model-serialization drift).
- [ ] **AC-7 — Thin task-chain.** Post-approval checklist statuses on the case
  (แจ้งอู่ / รออะไหล่ / รถยก / รถถ่ายของ — set confirmed with partner, intake Q below) with
  actor + timestamp per flip; humans decide everything; a stale item triggers a LINE nudge
  (fake clock + stub transport oracle). No handler automation is added to `fulfill` (its receipt
  stub stays).
- [ ] **AC-8 — LINE notify surface (the ONE new outbound channel).** A single notify seam emits:
  approval-needed (gate suspended), ratification-due reminder, ratification-overdue,
  task-chain stale nudge, month-end-export ready. Transport is injected; the offline suite makes
  zero network calls (AC-11). Outbound only — no LINE inbound/bot.
- [ ] **AC-9 — Month-end export + KPI (the payoff moment).** An Express-entry-shaped monthly
  file: one row per governed repair spend with case, truck, date, vendor, amount, approver (from
  `governed_decision`), `three_quote_basis`, exception labels (emergency
  provisional/ratified/overdue/refused; sole-source), justification ref, run id. KPI = % of rows
  fully traceable, computed from the export. Non-vacuity fixture: one deliberately incomplete row
  must drop the KPI below 100% — if it doesn't, the metric is vacuous. Exact column mapping to
  Express entry = named intake question.
- [ ] **AC-10 — PM real data (measured + confirmed).** Wialon **CSV export** import proposes
  odometer values; a human confirm gates any `Truck` update (unconfirmed rows never touch the
  ontology — Q4's imprecision); mangled CSV fails closed. Last-service odometers load manually
  from the paper PM folder as a documented **onboarding task** (runbook step, not code beyond the
  import); `next_service_due_km` computed absolute at load (last_service + 100,000) by the import
  service — the YAML's no-arithmetic constraint is why it must be stored absolute. Kills the
  last-service `GUESS — รอแก้` stamps.
- [ ] **AC-11 — No live API anywhere.** The full suite passes with no network access: Wialon =
  CSV fixtures; LINE = injected transport; Express = file output; LLM = recorded stubs
  (CLAUDE.md §8). A test asserting no outbound socket during the suite run (or the harness's
  existing offline guard) is the oracle.
- [ ] **AC-12 — Verification sign-off.** Per-component case-coverage matrices (AC-4, AC-5, AC-10
  minimally: happy / boundary / fail-closed / adversarial-bypass / concurrency-race) reviewed;
  uncovered cases named as residual risk; an explicit confidence statement recorded in the
  closeout — the standard is "we are confident it does what we intend," not "tests pass"
  (partner-facing pilot infrastructure; the PLAN-0007 G5 16-case matrix is the rigor model).

## Out of Scope

Evidence-backed (LOCKED by the dispatch unless marked ⊕ = drafter addition):

- ❌ Live Wialon API (Q4/LOCKED — CSV export + human confirm only)
- ❌ Express / ERP API integration (Q6 — "export file suffices"; full re-key is the pain, the file
  is the cure)
- ❌ Automatic breakdown detection / event-trigger variant (Q1 — humans open cases; stays parked)
- ❌ Fully-automatic OCR of quotes (Q15 — เมย์ types the amount; OCR at most assistive, later)
- ❌ A ฿ cap on emergency spend (Q11 refuted it — ADR-0034 eliminates, not defers)
- ❌ `Tire` object + tyre capture workflow (Q7 — no data source exists; a tacit-knowledge capture
  workflow designed with ต้อม; Phase 2. Naming discipline per PLAN-0089: nothing is called
  `tire_*` until a `Tire` object exists)
- ❌ Deep post-approval orchestration (auto garage dispatch / parts ordering / tow booking — the
  task-chain is statuses + nudges; humans decide everything, Q2)
- ❌ E-4 tier-deferral BUILD (mechanism defined in ADR-0034 D2/D5; calendar-gated — next holiday
  crunch is New Year; its own PLAN)
- ❌ Seasonal / preferred-vendor / SLA policies (unconfirmed analyst-voice hypotheses — verify
  next partner visit)
- ❌ ⊕ `ExceptionPolicy` enum growth for E-3 (no consumer in the fleet flow — `ScoredRule`-only,
  `spec.py:1028`; ADR-0034 D4)
- ❌ ⊕ LINE inbound (bot receiving messages / LINE-photo auto-ingest) — notify is outbound-only;
  quote photos arrive via เมย์'s upload in the case UI
- ❌ ⊕ Any new `PipelineRunStatus` member (ADR-0034 D3/Alt-6 — Text status + JSONB audit suffice).
  **Amended 2026-07-28 (Cray, typed):** this item originally also read "or DB migration". It was a
  ⊕ drafter addition (not dispatch-LOCKED) whose parenthetical cites ADR-0034 D3/Alt-6 — which is
  about the **E-2 ratification status**, i.e. Step 5. Read as a blanket Phase-1 ban it would have
  forced repair cases into a file store or memory, and a case that does not survive a restart
  cannot support "capture from minute 1" (AC-3) or a KPI that must answer for every baht. Cray was
  shown both readings and ratified the narrow one: **Step 2 adds the `repair_case` table +
  `alembic 0013`.** The ban still binds where it was aimed — Step 5 adds NO `PipelineRunStatus`
  member and NO migration. Naming discipline (ADR-006 Rule of Three, PLAN-0089): the table is
  `repair_case`, not `case`, because exactly one vertical needs it today.

## Steps

Ordering: 1–4 need no ADR; Step 5 requires ADR-0034 **Accepted** (CLAUDE.md §8: ADR merged before
related implementation PR). 2→3→4 is a dependency chain (case → evidence → signal); 6–8 consume
2–5; 9 is independent and can parallelize.

### Step 1: Real governance numbers — kill the guesses

Update `verticals/fleet_maintenance/procedures.yaml` + `data_adapter/synthetic.py` + README:
ladder floors `"0"`/`"5001"`/`"30001"` (AC-1 boundary encoding — the partner's ≤/– /> phrasing
mapped onto inclusive half-open bands; garage quotes are whole-baht, and a satang-bearing quote in
(30,000, 30,001) routing วิรัช is accepted de-minimis, noted as intake); per-truck ceilings default
5001 with the "some tractor heads stretch" values loaded at onboarding (Q8 — real numbers = intake);
provenance comments rewritten to cite the real answers (Q9/Q10) replacing the synthetic-narrative
citations; `OCT_RECOMMEND_THRESHOLD` README block aligned. Keep one synthetic mid-ladder breach
row (~฿15k) beside the ฿48k one so the demo still shows tiering, not always-the-top. Oracle: AC-1
boundary tests + AC-2 hash equality + golden load.

### Step 2: Case capture from minute 1

A minimal mobile-first case surface (the existing FastAPI + static-assets stack — no new
framework): open case (truck pick, optional description, photo attach), case record
(`case_id`, `truck_id`, `opened_by`, `opened_at`, photos, status), and the bridge that makes the
governed run's intake row carry `case_id`. Design for เมย์ + roadside ต้อม (photo-first, zero
required typing beyond the truck pick). Human-opened only. Oracle: AC-3 API tests; a
create-with-photo-only flow test.

### Step 3: Quote evidence pack

Per-case quote entries: vendor, typed amount (เมย์ keys it — Q15), attachment
(PDF / LINE-exported photo / photographed paper), timestamp, entered-by; plus the E-3 sole-source
justification entry (free text + vendor, entered by เมย์/วิรัช). The pack exposes `quote_count`
and the justification presence to Step 4. This is the artifact that replaces "3-quote compare =
scrolling LINE, sometimes lost" (Q5). Oracle: pack unit tests; attachment round-trip; AC-4
matrix's data half.

### Step 4: E-1 threshold + computed compliance signal (retires the fail-open default)

The evidence feed computes `compliance.three_quote` per ADR-0034 D4: pass ⇔ amount ≤ ฿30,000
(typed fleet-side config with Q10 provenance — NOT an engine field, NOT in rule prose) OR
**`distinct_vendor_count ≥ 3`** OR sole-source justification logged; stamps `three_quote_basis`.

> **Amended 2026-07-28 (Cray, typed).** This step originally read `quote_count ≥ 3`. Step 3's
> evidence pack surfaced that three quotes from the SAME garage — a revision, a re-quote, a second
> phone call — would satisfy that, and the partner's Q10 rule is "สามเจ้า": three *places*. Counting
> raw quotes would let a repair that was never price-compared satisfy a rule he adopted after being
> defrauded on parts, which is the hollow-compliance shape the gate exists to prevent. The pack
> reports both numbers; the gate reads `distinct_vendor_count`, and the audit records both so the
> partner can see "3 ใบ 2 ร้าน" when a case is blocked. **Remove** the
reshape `default: {compliance: {three_quote: true}}` — a case-fed breach row always carries the
computed map, and a missing map now fails CLOSED at the gate (`RuleGateError`), which is correct
(wiring error, not a pass). Rewrite the rule's authored `spec` prose to name both evidence paths,
฿-token-free (ADR-0025 D4 prose-lint). Oracle: the full AC-4 matrix on the real gate.

### Step 5: E-2 — the ratification window (ADR-0034 D2 Door 1 + D3) — *gated on ADR-0034 Accepted*

Exactly the ADR's named path: `EmergencyWaiverPolicy.ratification_window_days: int | None`
(only-when-supplied; AC-6); `StepResultStatus.RESOLVED_PROVISIONAL`; the waiver-invoked
provisional branch in `resolve_gated_step` (attestation record, SoD + tier-authority on the
attested approver, effects execute, NO `governed_decision` tie); `ratify_gated_step` (RF-1,
tier-authority on the ratifier via `check_tier_authority`, SoD, tie at ratify, refusal audited);
`resume_run` advance; pure `ratification_state`; fleet waiver authored `ratification_window_days: 7`
(Q11 provenance). Oracle: the AC-5 matrix, in full — this is the component the AC-12 rigor
standard binds hardest.

### Step 6: Thin task-chain

Post-approval checklist on the case (default items แจ้งอู่ / รออะไหล่ / รถยก / รถถ่ายของ —
confirm the set with the partner), actor+timestamp per flip, staleness clock → LINE nudge. Case
layer, not engine steps; `fulfill`'s receipt stub is untouched. This is the honest reading of Q2's
"อยากให้มันวิ่งต่อเอง": nudges and visible state, humans deciding. Oracle: AC-7.

### Step 7: LINE notification channel

One outbound notify seam (module + `tools/notify/line.sh`-style CLI analog beside the existing
`tools/notify/telegram.sh`), injected transport, the five AC-8 events. **Design note (verified
2026-07-28): LINE Notify was discontinued 2025-03-31 — the channel is a LINE Official Account via
the Messaging API push; the partner's delivery target (existing LINE group vs new OA) is a named
intake question.** Recipients per event: approval-needed → the resolved tier's approver;
ratification reminders → owner + เมย์; task-chain → เมย์; export-ready → owner + accounting
contact. Oracle: AC-8 with stub transport; the daily reminder ride-along on the existing 06:00
scheduled sweep precedent (PLAN-0090) rather than a new scheduler.

### Step 8: Month-end export — the KPI's payoff moment

The Express-entry-shaped monthly file (CSV first; exact columns = intake question) per AC-9,
reading completed + in-flight governed runs, `governed_decision` ties, `three_quote_basis`,
`ratification_state` (computed at report time), and the evidence pack refs. Emits the KPI number
(% spend fully traceable) + the proxy (per-case audit-answer completeness) on a cover summary.
Oracle: AC-9 fixtures incl. the non-vacuity incomplete row.

### Step 9: PM real data — Wialon CSV + confirmed load

Importer for the partner's Wialon CSV export (odometer per truck) with the measured+confirmed
pattern (AC-10); the onboarding runbook step for เมย์'s manual last-service load from the paper PM
folder; absolute `next_service_due_km` computed at load. PM is the near-daily adoption surface
(Q3) — this step is what makes the calm path real. Oracle: AC-10.

### Step 10: Verification + confidence sign-off

Full suite + mypy clean across the diff; the AC-12 matrices reviewed with residual risks named;
one offline end-to-end walkthrough of BOTH paths (normal: case → quotes → breach → gate → approve
→ export; exception: waiver-provisional → ratify → export showing the labeled exception); the
confidence statement in the closeout handoff. Partner-facing intake questions collected below
handed to Cray in one list.

## Verification

How we know it worked: every AC's oracle is offline and deterministic (CLAUDE.md §8 — the offline
oracle is the gate; the LLM is stubbed with fixtures; clock and transports injected); the AC-4 and
AC-5 matrices run against the REAL `evaluate_compliance` / `resolve_gated_step` / new
`ratify_gated_step` code paths — mocking the gate or waiver under test is a rejection condition,
per the dispatch's return contract. AC-2 + AC-6 are the schema-drift tripwires. The M-vocabulary
applies: a partial return that drops any LOCKED scope item above is a conditional result.

**Named intake questions for the partner (collected, not blocking):** exact Express entry columns
for the export (Q6/Q17 follow-up) · LINE delivery target (existing group vs new OA) · task-chain
item set confirmation · per-truck ceiling stretch values (Q8) · satang-precision note on the
30,000/30,001 boundary (de-minimis; confirm whole-baht quoting).
