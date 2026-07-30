# PLAN-0096: Fleet flow completion — Phase 1, Lean KPI-first

**Status:** COMPLETE — 12/12 ACs, archived 2026-07-30 (session 193)
**Owner:** Claude Code (execution); Cowork drafted (ADR-009 D1, s184 dispatch)
**Created:** 2026-07-28
**Related ADRs:** ADR-0034 (governed exception family — Proposed; precondition for Step 5), ADR-0025 (typed AT-2 content + prose-lint), ADR-0026 (live run-checks), ADR-0032 (D1 pilot wedge + 1-KPI charter), ADR-016/ADR-007 (run + write-gate substrate)

> **Drafting provenance.** Cowork-drafted (uncommitted) per the session-184 dispatch — mechanical G2
> routing (CLAUDE.md §6), not a quality judgment. Code R2s + commits via PR (ADR-009 D2).
> **Author≠reviewer disclosure (ADR-012 D4.3):** originators = the design partner (18 answers),
> Cray (typed Phase-1 = Lean-KPI-first + ADR-first picks, 2026-07-28), Code (dispatch fact-pack);
> drafter = Cowork. Engine citations verified at `main`=`7b84fa2`; PLAN number 0096 from the
> dispatch fact-pack — Code re-verifies next-free at commit. Keep Status **Draft** until Complete.
>
> **Amendment round 2026-07-29.** The partner's round-2 reply (A1–A7 + 4 dev suggestions,
> `docs/research/private/2026-07-29-fleet-partner-intake-round2_reply.md`, gitignored) and Cray's
> FOUR typed decisions (2026-07-29) are recorded in dated blocks below by the in-harness
> `plan-drafter` (s188 dispatch; Code fact-pack verified at `main`=`98744bd`). Recording edit,
> not a design pass: original text is preserved or explicitly superseded in marked blocks. Code
> R2s + commits via PR (ADR-009 D2). Status stays **Draft**.
>
> **CLOSEOUT 2026-07-30 (session 193) — 12/12, archived.** Step 8's build-order item 5
> shipped as #982–#986 and Step 10's AC-12 sign-off was written the same session. The
> AC checkboxes below were ticked in ONE pass at closeout, and that is worth stating
> plainly: **the tick column was never maintained during the build.** Every AC read
> `- [ ]` at closeout, including ones shipped seven sessions earlier, while the real
> record lived in the prose ("**Shipped — PR #975, merged as `d781683`**") and in
> `docs/STATUS.md`. So a later reader must not reconstruct the delivery order from
> these ticks — they are all dated 2026-07-30. Each is annotated below with what
> actually discharged it.
>
> **The sign-off itself is NOT in this file.** AC-12's four coverage matrices, seven
> named residual risks and confidence statement are in
> `.claude/handoffs/session-193/2026-07-30-2140-code-session193-CLOSE-plan0096-step8-COMPLETE-step10-AC12-signoff.md`
> — a gitignored working note, per the handoff convention. The residual risks that
> outlive this PLAN are carried forward into `docs/STATUS.md` rather than left only
> there; **RR-1** (per-baht approver→case attribution is inference, not data, because
> `GovernedDecision` carries no timestamp or entity key under `extra="forbid"`) is the
> ceiling on what AC-9's KPI can honestly claim and is the one to re-read first.

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

**What actually discharged each AC (closeout 2026-07-30, session 193).** The ticks below
all carry today's date because the column was never maintained during the build; this
table is the real delivery record, and the caveats are not decoration — they are the
part a reader skimming twelve ticks would otherwise miss.

| AC | Discharged by | Caveat |
|---|---|---|
| AC-1 | s186 — real partner ladder + boundary tests (#951–#961) | — |
| AC-2 | s186 — cross-vertical config-hash tripwire | — |
| AC-3 | s186 — `repair_case` capture, alembic `0013` | — |
| AC-4 | s186 — quote evidence pack, alembic `0014`; the fail-open `three_quote: true` default KILLED | **RR-3**: the concurrency-race row is a same-instant-tie test, not a concurrent-writer race |
| AC-5 | s186 — E-2 ratification, incl. the optimistic-lock test | strongest matrix of the four; adversarial-bypass four deep |
| AC-6 | s186 — only-when-supplied schema discipline | — |
| AC-7 | s189 — thin task-chain, alembic `0016` (#965) | — |
| AC-8 | s186 + s189 — LINE notify seam, six events; **outbound-only and DISARMED** | never armed against the live channel |
| AC-9 | **s193** — export + KPI + cover, #982–#986; bar demonstrated on the real path (`เจ๊หงส์` 100 → 0) | ศูนย์ต้นทุน ships EMPTY (partner granularity unanswered — the PLAN pre-authorises it); **RR-3** no concurrency test |
| AC-10 | s186 — PM import measured-then-confirmed, alembic `0015` + ontology overlay | **RR-3**: last-write-ordering, not a concurrent race |
| AC-11 | the suite's existing no-live-model offline guard; `host_state` is the explicit opt-OUT marker | — |
| AC-12 | **s193** — four matrices, seven residual risks, confidence statement (session-193 handoff) | the sign-off records RR-1 as the ceiling on AC-9's KPI claim |

- [x] **AC-1 — Real ladder + boundary semantics.** Fleet `doa_tier` floors encode the partner's
  inclusive-ceiling phrasing (Q9: ≤5,000 ต้อม / 5,001–30,000 วิรัช / >30,000 owner) with the
  engine's inclusive floors: `"0"` / `"5001"` / `"30001"` THB; per-truck `minor_repair_ceiling_thb`
  default 5001 (breach ⇔ quote > ฿5,000). Boundary oracle: 5,000 → no governed run; 5,001 → วิรัช
  tier; 30,000 → วิรัช tier; 30,001 → owner tier. `GUESS — รอแก้` stamps for ladder + ceilings
  removed; provenance comments cite the REAL partner answers. Counterexample: floors `"5000"`/`"30000"`
  would route 5,000/30,000 one tier too high — the boundary tests fail.
- [x] **AC-2 — No cross-vertical drift.** Resolved governance config hashes of procurement,
  supply_chain, building_materials, energy, aquaculture are BYTE-IDENTICAL across the whole
  Phase-1 diff (fixture hash-equality test). Counterexample: an always-serialized new `None` field
  (ADR-0034 D6) flips every hash — this test is the tripwire.
- [x] **AC-3 — Case capture from minute 1.** A mobile-first, human-opened case (truck pick +
  photo attach, zero further required typing) exists; the governed run's intake row carries the
  `case_id` so evidence links end-to-end. No auto-detection path exists anywhere (Q1).
- [x] **AC-4 — Quote evidence pack + computed signal (E-1 + E-3).** Quotes attach as
  PDF / LINE-exported photo / photographed paper with vendor + typed amount; the pack computes the
  `compliance.three_quote` signal and stamps `three_quote_basis`. Decision matrix oracle (real
  `evaluate_compliance`, no mocks): (48,000; 1 quote; no justification) → **blocked**; (48,000; 3
  quotes) → pass, basis `three_quotes`; (48,000; 1 quote; sole-source justification) → pass, basis
  `sole_source_justified`; (25,000; 1 quote) → pass, basis `under_threshold`; boundary 30,000 →
  under_threshold vs 30,001 → quotes-required; **breach row with NO signal map → `RuleGateError`
  (fail closed)**. Counterexample: today's reshape `default three_quote: true` would pass the
  no-evidence case — that default is removed and the fail-closed test proves it.
- [x] **AC-5 — E-2 ratification state machine (ADR-0034 D3), full case-coverage matrix.** All of:
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
- [x] **AC-6 — Only-when-supplied schema discipline.** A waiver WITHOUT `ratification_window_days`
  serializes byte-identically to the pre-change model (serialization + hash test), per ADR-0034
  D6. This is AC-2's schema-level twin; both must exist (one catches YAML drift, one catches
  model-serialization drift).
- [x] **AC-7 — Thin task-chain.** Post-approval checklist statuses on the case
  (แจ้งอู่ / รออะไหล่ / รถยก / รถถ่ายของ — set confirmed with partner, intake Q below) with
  actor + timestamp per flip; humans decide everything; a stale item triggers a LINE nudge
  (fake clock + stub transport oracle). No handler automation is added to `fulfill` (its receipt
  stub stays).
  **Amended 2026-07-29 (partner A1 + Cray, typed — Decision 1).** The guessed 4-item set above is
  SUPERSEDED — the intake question is answered. The checklist is the partner's REAL 8 steps,
  A1's table transcribed exactly:

  | ขั้นตอน                      | ใช้จริง              | Optional | ถ้าค้างเกิน                           |
  | ---------------------------- | -------------------- | -------- | ------------------------------------- |
  | แจ้งอู่ / ยืนยันอู่ที่จะซ่อม | ✔ ทุกเคส             | ✘        | 30 นาที (รถเสียกลางทาง), 1 วัน (PM)   |
  | จัดหารถยก                    | เฉพาะรถวิ่งต่อไม่ได้ | ✔        | 1 ชั่วโมง                             |
  | จัดหารถถ่ายของ               | เฉพาะรถมีสินค้าค้าง  | ✔        | 1 ชั่วโมง                             |
  | สั่งอะไหล่                   | เฉพาะไม่มีของในสต๊อก | ✔        | 1 วัน                                 |
  | รออะไหล่                     | เฉพาะสั่งของ         | ✔        | 2 วัน (ของทั่วไป), 5 วัน (อะไหล่ใหญ่) |
  | เริ่มซ่อม                    | ✔                    | ✘        | 1 วันหลังของครบ                       |
  | ทดลองวิ่ง / ตรวจรับ          | ✔                    | ✘        | 1 วัน                                 |
  | ปิดงาน / เก็บเอกสาร          | ✔                    | ✘        | 7 วัน                                 |

  4 mandatory (แจ้งอู่/ยืนยันอู่ · เริ่มซ่อม · ทดลองวิ่ง/ตรวจรับ · ปิดงาน/เก็บเอกสาร) + 4
  conditional (จัดหารถยก · จัดหารถถ่ายของ · สั่งอะไหล่ · รออะไหล่). The set and its PER-ITEM
  staleness SLAs (the ถ้าค้างเกิน column, including the two context variants — แจ้งอู่ 30 นาที
  breakdown / 1 วัน PM; รออะไหล่ 2 วัน general / 5 วัน major part — and เริ่มซ่อม anchored
  relative to parts-complete per A1, "1 วันหลังของครบ", not to case open) live in a fleet-side
  AUTHORED CONFIG: editable config, NO template UI — the partner's dev-suggestion #1 template
  system is declined for Phase 1 per ADR-006 Rule of Three; dev-suggestion #2 (per-step SLA) is
  absorbed here. Context variants read `repair_case.work_type` (Decision 2, Step 6). The oracle
  refines accordingly: staleness fires per-item against ITS OWN SLA (fake clock), with both
  context variants each exercised.
- [x] **AC-8 — LINE notify surface (the ONE new outbound channel).** A single notify seam emits:
  approval-needed (gate suspended), ratification-due reminder, ratification-overdue,
  task-chain stale nudge, month-end-export ready. Transport is injected; the offline suite makes
  zero network calls (AC-11). Outbound only — no LINE inbound/bot.
  **Amended 2026-07-29 (partner A3 + Cray, typed — Decision 4).** Five events → **SIX**: `pm_due`
  fires when a truck's PM falls due; recipient = a NEW mechanics-group role (กลุ่มช่าง per A3);
  producer rides the existing 06:00 scheduled sweep (PLAN-0090 precedent); built in Phase 1. The
  shipped `LineEvent` enum is a closed StrEnum of exactly the five events above
  (`services/notify/line.py:65-74`) whose docstring requires precisely this decision — a named
  producer and a named recipient rule — before a sixth member may exist; that decision is now
  made. The original five events and their role-based routing stand unchanged.
- [x] **AC-9 — Month-end export + KPI (the payoff moment).** An Express-entry-shaped monthly
  file: one row per governed repair spend with case, truck, date, vendor, amount, approver (from
  `governed_decision`), `three_quote_basis`, exception labels (emergency
  provisional/ratified/overdue/refused; sole-source), justification ref, run id. KPI = % of rows
  fully traceable, computed from the export. Non-vacuity fixture: one deliberately incomplete row
  must drop the KPI below 100% — if it doesn't, the metric is vacuous. Exact column mapping to
  Express entry = named intake question.
  **Amended 2026-07-29 (partner A2 + Cray, typed — Decision 3).** The exact-column intake
  question is RESOLVED. Accounting uses Express, keying into หมวด "ค่าใช้จ่ายซ่อมรถ"; one row
  per vehicle (รถแต่ละคันลงแยกเป็นรายการ — never multiple trucks in one line). The 15 required
  columns, transcribed exactly from A2: วันที่เอกสาร · วันที่อนุมัติ · เลขที่ใบแจ้งซ่อม ·
  เลขที่ใบกำกับภาษี · ผู้ขาย / อู่ · รหัสผู้ขาย (ถ้ามี) · ทะเบียนรถ · รหัสรถ ·
  ประเภทงาน (PM / Breakdown / Accident) · รายการซ่อม · จำนวนเงินก่อน VAT · VAT · จำนวนเงินรวม ·
  ผู้อนุมัติ · ศูนย์ต้นทุน. The shipped evidence schema cannot fill the invoice trio —
  `RepairCaseQuote.amount_thb` is a single `Numeric(14, 2)`
  (`services/db/repair_case_evidence.py:67`) with no VAT split and no tax-invoice field in the
  file (grep-verified 2026-07-29; Code fact-pack confirms none exists anywhere in the schema) —
  so, Cray's typed **Decision 3**: a NEW append-only close-out invoice record —
  เลขที่ใบกำกับภาษี, pre-VAT amount, VAT (**nullable** — small garages may not be
  VAT-registered), total — keyed by เมย์ at the ปิดงาน / เก็บเอกสาร task-chain step; its own
  alembic migration rides Step 8. Back-computing VAT at 7% in the export was explicitly
  **rejected** (typed). ประเภทงาน comes from the new `repair_case.work_type` (Decision 2). The
  original row-content list above is otherwise preserved — case, truck, date, vendor, amount,
  approver, `three_quote_basis`, exception labels, justification ref, run id all map into the 15
  columns + the cover summary.
  **Amended 2026-07-29 (s190):** เลขที่ใบแจ้งซ่อม = human-readable `RC-<year>-<NNNN>` per Cray's
  typed **Decision A** — see Step 8's session-190 amendment block (migration `0017`).
  **Amended 2026-07-30 (s191):** two facts a reader of this AC alone would miss. (1) The approval
  pair — วันที่อนุมัติ (column 2) + ผู้อนุมัติ (column 14) — currently has NO source for any REAL
  row: a real repair case never reaches a governed run, so `governed_decision` never fires for
  real spend. (2) The governed ฿ amount + vendor provenance now exist — the accepted quote
  (ใบที่ตกลง, alembic `0019`) — but the gate does not read it yet. Both facts, Cray's typed
  decisions, and the corrected build order: Step 8's session-191 amendment block.
- [x] **AC-10 — PM real data (measured + confirmed).** Wialon **CSV export** import proposes
  odometer values; a human confirm gates any `Truck` update (unconfirmed rows never touch the
  ontology — Q4's imprecision); mangled CSV fails closed. Last-service odometers load manually
  from the paper PM folder as a documented **onboarding task** (runbook step, not code beyond the
  import); `next_service_due_km` computed absolute at load (last_service + 100,000) by the import
  service — the YAML's no-arithmetic constraint is why it must be stored absolute. Kills the
  last-service `GUESS — รอแก้` stamps.
- [x] **AC-11 — No live API anywhere.** The full suite passes with no network access: Wialon =
  CSV fixtures; LINE = injected transport; Express = file output; LLM = recorded stubs
  (CLAUDE.md §8). A test asserting no outbound socket during the suite run (or the harness's
  existing offline guard) is the oracle.
- [x] **AC-12 — Verification sign-off.** Per-component case-coverage matrices (AC-4, AC-5, AC-10
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
- ❌ **Added 2026-07-29 (partner A5; s188 dispatch disposition):** Admin-mapped, remembered
  Wialon column mapping. NO real export file exists yet (A5); the partner asks that columns be
  admin-mapped once and remembered ("ควรให้ Admin จับคู่ Field ครั้งแรก แล้วจำ Mapping ไว้")
  rather than fixed by name, because a Wialon version or template change can rename them.
  **PARKED until a real file exists** — the Step 9 importer stays fixed-column for now. A5's
  guessed header set (Vehicle Name · Plate Number · Odometer · Last GPS Time · Driver · Status)
  is recorded here for when this unparks.

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

> **Amended 2026-07-29 (partner A4 + A7).** Two intake items above are resolved:
> — **A4 (per-truck ceiling stretch values): none initially.** Flat ฿5,000 for every truck at
> start ("ขอใช้ 5,000 บาท ทุกคันก่อน … เดี๋ยวถ้าใช้จริงแล้วค่อยเพิ่มรายคัน — ดีกว่าเริ่มต้น
> ซับซ้อน"); the authored default 5001 stands UNCHANGED; per-truck increases arrive later in
> real use as authored config edits. Drafter proposal (veto-open): the "stretch values loaded at
> onboarding" sub-task above is thereby **eliminated**, not kept pending — A4 says the values do
> not exist yet, so there is nothing to load and no onboarding step to preserve.
> — **A7 (satang / de-minimis): confirmed, nothing changes.** 99% of garage quotes are whole
> baht (เศษสตางค์ ถ้ามี มาจาก VAT หรือค่าขนส่งอะไหล่, not the quote); the partner states the
> rule directly — ฿30,000 พอดี = ไม่ต้องเทียบสามเจ้า, ฿30,001 ขึ้นไป = ต้องเทียบ — which
> CONFIRMS the shipped `"30001"` inclusive floors and closes the de-minimis intake note.

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

> **Amended 2026-07-29 (partner A1 + Cray, typed — Decisions 1 + 2).** The default item set above
> is SUPERSEDED by the partner's real 8 steps — 4 mandatory + 4 conditional, with per-item SLAs —
> transcribed in AC-7's amended table. Shape, per Cray's typed **Decision 1**: the items live in
> a fleet-side AUTHORED CONFIG — editable config, NO template UI (dev-suggestion #1's template
> system is declined for Phase 1 per ADR-006 Rule of Three; the rename/reorder/toggle need it
> describes is met by editing the config). Staleness is a PER-ITEM SLA (dev-suggestion #2
> absorbed — this retires any single-timeout reading of "staleness clock" above), including the
> context variants แจ้งอู่ 30 นาที (breakdown) / 1 วัน (PM) and รออะไหล่ 2 วัน (ของทั่วไป) /
> 5 วัน (อะไหล่ใหญ่), and เริ่มซ่อม's SLA anchored to parts-complete ("1 วันหลังของครบ"), not
> to case open. The context variants need the work class, so Cray's typed **Decision 2**:
> `repair_case.work_type` (pm / breakdown / accident) — the shipped table has no such column
> (`services/db/repair_case.py:68-78`) *[superseded by new info, s190: shipped by Step 6's build —
> now `services/db/repair_case.py:86-88`; see Step 8's session-190 amendment]* — alembic migration
> **0016** approved 2026-07-29 (dev DB
> at 0015 per the Code fact-pack); one field serves both these SLAs and Step 8's ประเภทงาน
> column. It rides THIS step as the first consumer in the 6→8 build order (placement is
> ordering-derived, not a separate typed decision). A1's notes bind the conditional semantics:
> PM cases mostly skip รถยก/รถถ่ายของ entirely, some jobs (แบต/ยาง) finish on site, some repairs
> happen at the garage with no tow — a case whose 4 conditional items are all skipped is a
> NORMAL complete case, not an incomplete one. Build note (Code-verified 2026-07-29):
> `task_chain` matches only `services/notify/line.py` — the checklist itself is greenfield on
> the case + notify seam.

### Step 7: LINE notification channel

One outbound notify seam (module + `tools/notify/line.sh`-style CLI analog beside the existing
`tools/notify/telegram.sh`), injected transport, the five AC-8 events. **Design note (verified
2026-07-28): LINE Notify was discontinued 2025-03-31 — the channel is a LINE Official Account via
the Messaging API push; the partner's delivery target (existing LINE group vs new OA) is a named
intake question.** Recipients per event: approval-needed → the resolved tier's approver;
ratification reminders → owner + เมย์; task-chain → เมย์; export-ready → owner + accounting
contact. Oracle: AC-8 with stub transport; the daily reminder ride-along on the existing 06:00
scheduled sweep precedent (PLAN-0090) rather than a new scheduler.

> **Amended 2026-07-29 (partner A3 + Cray, typed — Decision 4).** A3's mixed routing —
> เรื่องอนุมัติ → ส่งเฉพาะคนที่ต้องอนุมัติ · เอกสารค้าง → น้องเมย์ · ใกล้ครบ 7 วัน → น้องเมย์ +
> ผู้อนุมัติ · ไฟล์สิ้นเดือน → กลุ่ม "บัญชี + Fleet" · PM ถึงกำหนด → กลุ่มช่าง — maps onto the
> EXISTING role-based `Recipient` / `EVENT_RECIPIENTS` design (`services/notify/line.py:77-101`)
> with deployment CONFIG only, no code reshape, EXCEPT `pm_due`: the sixth event per Cray's typed
> **Decision 4** (AC-8 amendment) — new mechanics-group role (กลุ่มช่าง), producer riding the
> existing 06:00 scheduled sweep (PLAN-0090 precedent), built in Phase 1. The named intake
> question "existing LINE group vs new OA" is RESOLVED to the extent A3 names recipients — the
> partner explicitly refuses one-group-for-everything ("ผมไม่อยากให้ทุกอย่างเด้งเข้ากลุ่มเดียว
> เดี๋ยวคนปิดแจ้งเตือนหมด") — while the OA channel-access token remains an ONBOARDING item; LINE
> stays disarmed until it exists. Dev-suggestion #4 (event ↔ recipient separation) is already
> structurally satisfied by the role-based `EVENT_RECIPIENTS` design — recorded, no new scope.

### Step 8: Month-end export — the KPI's payoff moment

The Express-entry-shaped monthly file (CSV first; exact columns = intake question) per AC-9,
reading completed + in-flight governed runs, `governed_decision` ties, `three_quote_basis`,
`ratification_state` (computed at report time), and the evidence pack refs. Emits the KPI number
(% spend fully traceable) + the proxy (per-case audit-answer completeness) on a cover summary.
Oracle: AC-9 fixtures incl. the non-vacuity incomplete row.

> **Amended 2026-07-29 (partner A2 + Cray, typed — Decisions 2 + 3).** The exact-column question
> is RESOLVED — the 15 Express columns are transcribed in AC-9's amendment (one row per vehicle,
> keyed into หมวด "ค่าใช้จ่ายซ่อมรถ"). Consequences for this step:
> — **Close-out invoice record (Cray, typed — Decision 3):** the NEW append-only record
> (เลขที่ใบกำกับภาษี, pre-VAT amount, VAT nullable, total; keyed by เมย์ at ปิดงาน / เก็บเอกสาร)
> defined in AC-9's amendment — its own alembic migration rides THIS step. Back-computing VAT at
> 7% in the export: explicitly rejected (typed).
> — **Vendor codes (A2):** the ~20–30 main vendors already have Express codes; a NEW vendor is
> opened by accounting in Express FIRST. The export therefore needs a vendor → Express-code
> AUTHORED mapping (authored config, not name matching).
> — **รหัสรถ (A2):** no vehicle-code property exists on `Truck`
> (`verticals/fleet_maintenance/ontology/fleet_maintenance_v0.yaml:33-84`; whole-file grep clean
> 2026-07-29) — it arrives as an authored per-truck value via YAML + regen (fleet is in-memory
> synthetic; no migration).
> — **ศูนย์ต้นทุน (A2):** no cost-center exists anywhere in the fleet ontology (same grep);
> its granularity (per truck vs per company) is a NEW named intake follow-up (see Verification)
> — the column ships; its fill rule awaits the answer.
> — **ประเภทงาน:** read from `repair_case.work_type` (Decision 2; migration 0016 rides Step 6).
> — Dev-suggestion #3 (central mapping tables) — disposition assembled from the pieces above,
> drafter synthesis, veto-open: vendor-code + vehicle-code mappings arrive as authored config in
> this step; the Wialon ↔ truck mapping is parked with A5 (Out of Scope). No standalone mapping
> subsystem is built.

> **Amended 2026-07-29 (session 190 — Cray typed, Decision A; findings grounded by Code).** Two
> typed decisions and five on-disk findings recorded BEFORE migration `0017` is written, because
> together they change that migration's shape. Citations verified this session at `main`=`7b05f1e`;
> alembic head today is 0016 (`alembic/versions/0016_repair_case_task_chain.py`), so the close-out
> record takes **0017** — Code re-verifies next-free at commit.
> — **The missed column (grounding for Decision A):** AC-9's earlier amendment flagged only the
> invoice trio as unfillable and MISSED เลขที่ใบแจ้งซ่อม (column 3). `repair_case.case_id` is
> generated as `case-{uuid.uuid4().hex[:12]}` (`services/api/routers/cases.py:168`) — a UUID no
> accounting department can key against an Express document. This gap is why Decision A exists,
> and it had to be settled before `0017` was written rather than after.
> — **Repair-case number (Cray, typed — Decision A, s190):** Express column 3, เลขที่ใบแจ้งซ่อม,
> gets a human-readable repair-case number carried on the close-out record in migration `0017`.
> Format **`RC-<year>-<NNNN>`** (e.g. `RC-2026-0001`), the running sequence **reset per year**.
> The allocation mechanism — how the running number is issued and how it stays unique under
> concurrency — is **Code's implementation choice, NOT a PLAN-level pin**: no later reader should
> treat any particular mechanism as ratified by this PLAN.
> — **Close-out invoice record (Decision B — typed s189; RESTATED for this step, not re-decided):**
> the record carries เลขที่ใบกำกับภาษี / pre-VAT amount / VAT (**nullable**) / total, keyed by
> เมย์ at the ปิดงาน / เก็บเอกสาร (`close_case`) task-chain step; back-computing VAT at 7% was
> explicitly **rejected** (typed). Same decision AC-9's amendment records as "Decision 3" —
> restated here so `0017`'s author reads the complete close-out field set (the invoice quartet +
> Decision A's case number) in one place.
> — **รหัสรถ mechanism correction (supersedes "via YAML + regen" in the bullet above):**
> `verticals/fleet_maintenance/generated/` is imported by NOTHING anywhere in the repo, and
> `next_service_due_km` — present in `verticals/fleet_maintenance/ontology/fleet_maintenance_v0.yaml`
> — appears in no file under `generated/`: the generated artifacts are stale. The per-truck values
> the runtime and tests actually consume are hand-written in
> `verticals/fleet_maintenance/data_adapter/synthetic.py` (`truck_records()`, `:118`). Following
> the regen line literally would produce a value that never reaches the export. The working edit
> is **YAML (schema/doc) + `synthetic.py` (the value)**, and no migration — the fleet vertical
> has no alembic-registered ORM of its own.
> — **Step 6-amendment citation superseded by new info (not an error):** Step 6's amendment states
> the shipped table "has no such column (`services/db/repair_case.py:68-78`)" about `work_type`.
> True when written; Step 6's build then shipped it — `work_type` is at
> `services/db/repair_case.py:86-88`. Classified **superseded by new info** per CLAUDE.md §6
> (verify-loop hygiene), and marked in place at the claim so it cannot mislead a `0017` author.
> — **Greenfield export surface (effort/scope fact):** repo-wide across `services/` +
> `verticals/`: ZERO occurrences of `csv.writer` / `csv.DictWriter` / `writerow` / `to_csv` /
> `StreamingResponse`, and no `text/csv` response anywhere; `csv` appears only as a READER
> (`csv.DictReader` — `verticals/fleet_maintenance/pm_import.py:151`,
> `verticals/procurement/data_adapter/fastenal_csv.py:157`). There is no export router. This step
> builds the repo's first export surface — plan it as construction, not wiring.
> — **A new table costs THREE registrations, not one:** `0017` must be registered in
> `alembic/env.py`, in `tests/db_support.py`, AND in `_HEAD_TABLES` in
> `tests/services/db/test_db_hermeticity.py`. The offline guard
> `tools/check_alembic_model_registration.py` catches the first two; the third fails in the
> suite. This is the exact defect class that reddened CI at 54 s during s189 (#965 → #966/#967).
> — *[s191 in-place note: after this block was recorded, session 190 also typed **Decision 9** —
> case↔run link = a scalar `run_id` column on `repair_case`, migration `0019` — which never
> entered this PLAN. It is REFUTED and SUPERSEDED unbuilt: `0019` shipped as the accepted-quote
> table instead, and the case↔run link is now a JOIN TABLE gated behind the case → event path.
> Do not resurrect the scalar-column shape — see the 2026-07-30 amendment block below.]*

> **Amended 2026-07-30 (session 191 — Cray typed; findings grounded + the s190 case↔run-link
> decision REFUTED by Code; recorded by the in-harness `plan-drafter`, s191 dispatch).** Session
> 190 closed this step's foundations — the close-out record + Decision A's `RC-<year>-<NNNN>`
> number (migration `0017`), the close-out `vendor` column (`0018`, AC-9 column 5 ผู้ขาย / อู่),
> and Express accounting codes as ontology data (`Truck.accounting_code` + a `Vendor` object,
> AC-9 columns 6 + 8) — then closed by typing one further decision, **Decision 9**, as the next
> session's build task: case↔run link = a scalar `run_id` column on `repair_case`, migration
> `0019`. Grounding that task in s191 REFUTED it before a line was written (three measured
> reasons below). Decision 9 was typed in-session and never entered this PLAN (the s190 block
> above records Decision A only); it is recorded AND retired here in one motion so no later
> reader resurrects the scalar-column shape. The corrected build order at the end of this block
> supersedes the old Step 8 → Step 10 sequencing. Citations re-verified this session at
> `main`=`d781683`. Recording edit, not a design pass; Status stays **Draft**.
> — **The frontier fact every remaining Step-8 item sits behind: a REAL repair case never
> reaches a governed run.** `POST /api/cases` (`services/api/routers/cases.py:156`; prefix
> `:73`) writes the row and returns; the router references `OperationalEvent` NOWHERE (grep
> re-verified s191, zero hits). The only `case_id` that reaches a run is the demo fixture
> `case-demo-truck01-axle` (`verticals/fleet_maintenance/data_adapter/synthetic.py:267`).
> Consequence: AC-9's approval columns (วันที่อนุมัติ · ผู้อนุมัติ) have NO source for any real
> row regardless of join shape, and a case↔run link built today would be NULL in 100% of real
> rows. **Cray's typed order (s191): build the event path BEFORE the link table.**
> — **Claim-vs-code, classified `was an error` (CLAUDE.md §6 verify-loop hygiene):**
> `synthetic.py:56-57` states "Step 3 wires the real case → quote → event path". Step 3 as
> executed shipped the quote evidence pack and did NOT wire the event path — a forward reference
> that never landed. That is **`was an error`**, NOT `superseded by new info`: no later fact
> changed it; it was never true. The comment itself is code, so its correction rides the
> event-path PR (Code); the classification is recorded here so no reader trusts it meanwhile.
> — **Why Decision 9's scalar `run_id` cannot be correct — three measured reasons (Code, s191):**
> (1) a manual run is re-fireable without limit — `services/api/routers/runs.py:370`
> (`POST /procedures/{procedure_id}/run`) has no idempotency key and no in-flight guard (the
> router's only "in-flight" mention is the CANCEL docstring, `:547`); fire the hero procedure
> twice and one still-open case appears in run A and run B, and a scalar column is
> last-write-wins — silently overwriting the run that actually approved the spend. (2) "the run
> that APPROVED" is per-PROPOSAL, not per-run —
> `services/engine/procedures/action_step.py:953-956` builds the final artifact by pairing each
> proposal with its own APPROVE / reject disposition; one run can approve one case and reject
> another, and a run pointer cannot tell them apart. (3) the provisional branch splits the
> moment in two — `action_step.py:971` lands `RESOLVED_PROVISIONAL` and `ratify_gated_step`
> (`action_step.py:1028`) completes it days later; one value written at first resolve cannot
> express ADR-0034's E-2 mechanism.
> — **Revised typed decision (Cray, s191): case↔run link = a JOIN TABLE `repair_case_run_link`
> (`case_id`, `run_id`, `step_id`, `outcome`, `linked_at`) — DECIDED, NOT BUILT.** There is also
> no seam to write it today: `on_step_complete`
> (`services/engine/procedures/orchestrator.py:930`) is engine-internal, and `_FIRED_HOOKS`
> (`services/engine/cli.py:359`) is scheduler-daemon-only — the API process never reaches
> either. Smallest seam identified (Code implementation surface, not a PLAN-level pin beyond the
> stated requirement): an optional `on_resolved` callback on `resolve_gated_step`
> (`action_step.py:669`), fired after the commit at `action_step.py:1006`, wired by a
> per-vertical map — and it MUST hook `ratify_gated_step` (`:1028`) too, or the E-2 path
> silently drops its link rows.
> — **The root cause behind both `0018` and the missing gate amount — RESOLVED (s191).** The
> s190 finding: nothing recorded WHICH quote was accepted, so the ฿ figure the DoA ladder routes
> on had no source before the work was done — `RepairCaseCloseout.total_thb` exists only AFTER
> the repair the gate was meant to authorise; `EvidencePack.lowest_amount_thb` is explicitly
> disclaimed for this use (`services/db/evidence_pack.py:52` — "the gate does not") while
> `verticals/fleet_maintenance/procedures.yaml:278` routes tiers on "the FULL quote". This is
> the SAME hole `0018` patched with `RepairCaseCloseout.vendor`: the accepted quote carries both
> the amount and the vendor — had the primitive existed, `0018` would not have been needed.
> Cray's typed decisions (s191): **(1)** the accepted quote — ใบที่ตกลง — joins the quote pack;
> typed at the close of s190 as the next session's FIRST task, ahead of the event path. **(2)**
> the reference is a REQUIRED foreign key — an acceptance must name a quote already recorded
> against that same case; a free-typed vendor + amount was offered and DECLINED (the accepted
> amount is what an authority threshold routes on, so it must trace to evidence somebody
> recorded; when the chosen garage's quote was never keyed, it is keyed first through the
> existing quote route). **(3)** a reason is required ONLY when the accepted quote is not the
> cheapest on file at that moment — always-required and never-required were both offered and
> declined; rationale as typed: the audit question is never "why did you accept a quote", it is
> "why did you not take the cheapest one", and demanding it always trains the operator to type
> "ถูกสุด" into the box — compliance text instead of information.
> **Shipped — PR #975, merged as `d781683`, alembic `0019`:** `RepairCaseAcceptedQuote`
> (`services/db/repair_case_evidence.py:131`) — append-only, latest row wins; a THIRD table
> rather than a flag on the quote row, because a flag would have to be UPDATEd (breaking the
> append-only rule these tables exist to hold) and would permit two rows flagged at once.
> `0019` also adds `UNIQUE (case_id, quote_id)` on `repair_case_quote`
> (`alembic/versions/0019_repair_case_accepted_quote.py:53-54`) existing solely as a
> composite-FK target, so "case A accepted case B's quote" is refused by Postgres rather than
> by application care (measured s191: with the router's case filter removed, the insert fails
> with `ForeignKeyViolationError` on `fk_repair_case_accepted_quote_quote`, `0019_…py:67`).
> `POST`/`GET /api/cases/{case_id}/accepted-quote` (`cases.py:572` / `:637`). `EvidencePack`
> gains `accepted_quote_id` / `accepted_amount_thb` / `accepted_vendor` / `accepted_reason` /
> `accepted_by` / `accepted_at`, a DERIVED `lowest_amount_at_acceptance_thb`, and a three-valued
> `accepted_the_cheapest` (`evidence_pack.py:61-97`). Evidence (Code, s191): 3588 passed / 8
> skipped (baseline 3572, +16); `ruff` + `ruff format --check` clean over 556 files;
> `mypy --strict services/` clean over 124; registration guard, R7, R8 exit 0; CI `gate` pass;
> merge-commit equality 0 bytes; three non-vacuity probes each shown RED and restored
> byte-identical. **Still not wired:** the gate does not yet READ `accepted_amount_thb` (zero
> occurrences under `services/engine/`, grep s191) — and cannot until the event path exists.
> — **The event-path design — SETTLED, Option A: mirror the ratified `pm_projection` seam**
> (the repo's sanctioned DB → object-source overlay; public surface `refresh` / `apply` /
> `status` / `reset` / `record_unavailable` / `overrides`,
> `verticals/fleet_maintenance/pm_projection.py:49-89`; boot refresh with fail-soft
> `services/api/main.py:220-235`). Files (all three new modules verified ABSENT s191 —
> construction, not wiring): new `services/db/case_events.py` (read open cases + their evidence
> packs); new PURE `verticals/fleet_maintenance/case_events.py`
> (`build_event(case, pack, *, now) -> dict`); new `verticals/fleet_maintenance/case_projection.py`
> (refresh / apply / status + `demo_events.reset()`); a ~3-line overlay edit in `synthetic.py`'s
> `operational_events()`; boot refresh in `main.py` beside the PM block; a refresh call in
> `services/api/routers/cases.py` after `add_quote` / `add_justification` — and now also after
> the accept route. **Zero `services/engine/` diff. Zero `data_adapter/__init__.py` diff — the
> latter MANDATORY:** `tests/services/engine/scaffolder/test_golden_e2e.py:206-210` holds that
> module structurally equal to the regenerated donor (PLAN-0086 AC-7 row 4 — even one extra
> entry breaks it), and `synthetic.py:292-300` already litigated and REJECTED exactly that move.
> The event contract a real row must satisfy: `event_id`, `event_type: "reading"`, `severity`,
> `measured_value`, `unit: "THB"`, `case_id`, `description`, `occurred_at` (tz-aware),
> `truck_id`, `site_id`, plus `{"compliance": {"three_quote": bool}, "three_quote_basis": …}`
> from `compute_three_quote` (`verticals/fleet_maintenance/sourcing.py:71`) via
> `compliance_signal_map` (`:97`) — Step 4 deleted the fail-open `compliance` default, so
> `rule_gate` fails CLOSED if the block is absent. Read model: `load_evidence_pack`
> (`evidence_pack.py:100`). The "which quote is the governed amount" decision inside this item
> is now ANSWERED — the accepted quote (above). Two decisions remain inside it: `demo_events`
> cache-invalidation semantics; and a real case event on truck-01 will outrank the ฿48,000
> fixture breach by `occurred_at`, so the AT-2 hero narrative and its tests MOVE.
> — **`latest_per: event_for_truck` collapses two open cases on one truck**
> (`procedures.yaml:159`): `_latest_per_group`
> (`services/engine/procedures/query_step.py:607-648`) keeps exactly one row per group and drops
> rows whose group key is `None` (`:623`) — two open cases on one truck means the older never
> reaches the gate, and its link row stays absent forever, indistinguishable from "no run yet".
> The fix is a VERTICAL-side ontology edit, not an engine change: a `RepairCase` object type +
> `case_id: {type: string}` on `OperationalEvent` + an `event_for_case` link, then flip
> `latest_per`. Two tripwires: declare `case_id` as `string`, NEVER `ref` —
> `services/engine/scaffold.py:163-171` raises `ScaffoldError` when `OperationalEvent` carries
> more than one non-Site ref — and rows without a `case_id` vanish from intake (`:623` above),
> so the demo's `ok` contrast set changes visibly. Own PR, gated on the event path landing.
> — **The corrected build order (supersedes the old Step 8 → Step 10 sequencing):** (1) ~~the
> accepted-quote primitive~~ — **DONE, PR #975, alembic `0019`**; (2) the case → event path
> (Option A above); (3) `repair_case_run_link` + the `on_resolved` seam on BOTH
> `resolve_gated_step` and `ratify_gated_step`; (4) optionally re-key `latest_per` onto the case;
> (5) then the export, the KPI and the scenario test; then Step 10. Scope honesty, recorded
> explicitly: this is SEVERAL PRs, not one — "add `run_id`" became a join table, then an event
> path, then a missing primitive, each caught BEFORE shipping.
> — **Residual risk, named for Step 10 (NOT resolved here):** `governed_decision` carries no
> per-entity key and no timestamp — only `{control_ref, principal_id}`
> (`services/engine/actions.py:52-67`, `extra="forbid"`). If one gate resolution routes two
> cases into the same tier, the ties are byte-identical. Survivable today (one human resolves
> the whole gate), but per-baht attribution of approver → case is INFERENCE, not data — and
> AC-9's KPI claims to measure exactly that. Step 10's sign-off must name it as residual risk.

### Step 9: PM real data — Wialon CSV + confirmed load

Importer for the partner's Wialon CSV export (odometer per truck) with the measured+confirmed
pattern (AC-10); the onboarding runbook step for เมย์'s manual last-service load from the paper PM
folder; absolute `next_service_due_km` computed at load. PM is the near-daily adoption surface
(Q3) — this step is what makes the calm path real. Oracle: AC-10.

> **Amended 2026-07-29 (partner A5 + A6).**
> — **A5:** NO real Wialon export file exists yet; the partner requests admin-mapped,
> REMEMBERED column mapping rather than fixed column names. PARKED until a real file exists
> (new Out of Scope item, where his guessed header set is recorded); THIS importer stays
> fixed-column for now.
> — **A6 (onboarding-runbook grounding):** last-service odometers are scattered across แฟ้ม PM /
> ใบงานซ่อม / สมุดของช่าง and ~10–15% are unrecoverable. เมย์ backfills ~30–35 trucks, estimated
> half a day to one day. A truck with NO recoverable history starts counting from its CURRENT
> odometer — `next_service_due_km = current + 100,000` — per the partner
> ("ให้เริ่มนับจากเลขไมล์ปัจจุบันได้เลย ดีกว่าปล่อยไม่มีข้อมูล"). These numbers go into the
> runbook step verbatim so the onboarding effort estimate is the partner's own, not a guess.

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

**Amended 2026-07-29 (partner round-2 + Cray, typed).** All five named intake questions above are
dispositioned by the round-2 reply
(`docs/research/private/2026-07-29-fleet-partner-intake-round2_reply.md`) and Cray's four typed
decisions:

- Exact Express entry columns → **RESOLVED** (A2): 15 columns, one row per vehicle — transcribed
  in AC-9's amendment; consequences in Step 8's amendment.
- LINE delivery target → **RESOLVED to the extent A3 names recipients** (mixed routing, five
  targets — Step 7's amendment); the OA channel-access token remains an ONBOARDING item, and
  LINE stays disarmed until it exists.
- Task-chain item set → **RESOLVED** (A1 + Cray Decision 1): the real 8 steps, 4 mandatory + 4
  conditional, per-item SLAs — AC-7's amended table.
- Per-truck ceiling stretch values → **RESOLVED: none initially** (A4): flat ฿5,000 all trucks;
  the authored default 5001 stands; per-truck increases arrive later in real use.
- Satang / de-minimis 30,000/30,001 → **CONFIRMED** (A7): 99% whole-baht; ฿30,000 exactly = no
  comparison, ฿30,001+ = required. The shipped `"30001"` floors stand; nothing changes.

**New named intake follow-up (one):** ศูนย์ต้นทุน (cost-center) granularity — per truck or per
company? (A2 consequence; Step 8's amendment.)
