# PLAN-0111: Credit notes (ใบลดหนี้) in the fleet close-out record

**Status:** Draft
**Owner:** both — SD-A…SD-F **ruled** (Cray, typed 2026-08-19); Claude Code executes
**Created:** 2026-08-19
**Related ADRs:** ADR-0037 (fleet Postgres + RoPA D2.1), ADR-0028 (SD-P1 accounting timezone)
**Related PLANs:** PLAN-0096 (close-out record, AC-9 export), PLAN-0099 (seq latest-wins),
PLAN-0101 (tenant key), PLAN-0105 (retention), PLAN-0107 AC-11 (the probe that shipped the
interim refusal, PR #1226)

> **Drafting disclosure (ADR-012 D4.3):** authored by the in-harness `plan-drafter`
> subagent from a Code-originated dispatch (2026-08-19); independent review = Cray at
> PR merge. SD slots below were surfaced 2026-08-19 and **ruled by Cray (typed) the
> same day**; the rulings were recorded by the same subagent from a second dispatch
> (2026-08-19), which also collapsed the two-branch conditionality to the ruled
> SD-A(b) branch and re-fixed every pass read against the ruled options. The rejected
> alternatives are retained deliberately per SD. Status stays **Draft** — Cray
> ratifies the PLAN itself at PR merge.

## Goal

Give the fleet close-out record a way to hold a credit note (ใบลดหนี้) **alongside** the
invoice it credits — two coexisting facts, not one replacing the other — so that the
month-end figure reads `20,000.00 − 15,000.00 = 5,000.00` instead of either
`20,000.00` (credit refused, knowably incomplete — today's interim state) or
`-15,000.00` (credit replaces invoice, invisibly wrong — the measured failure). เมย์
**does** receive real ใบลดหนี้ (Cray, typed 2026-08-19 — LOCKED; this PLAN does not
re-open it). The interim 422 refusal shipped in PR #1226 is lifted **only together
with** this schema, per its own docstring's stated condition
(`services/api/routers/cases.py:794-800`).

## Context — why a credit note cannot be keyed today (verified)

`RepairCaseCloseout` is **append-only, latest-wins**: a correction is a new row and
`latest_closeout` returns the newest row by `seq`
(`services/db/repair_case_closeout.py:156-182`). **Both** production consumers read
exactly that one row — the month-end export (`services/db/repair_spend_export.py:683`)
and `GET /{case_id}/closeout` (`services/api/routers/cases.py:884`; the PR #1226
dispatch and the scenario-test docstring cite `:843` — line drift from the guard block
added in the same PR, same site). **This is the whole problem:** a credit-note row does
not JOIN the invoice it credits, it REPLACES it. Measured with the guard removed
(`tests/api/test_closeout_negative_money_scenario.py`): the case's month-end figure
goes `20,000.00 → -15,000.00` and the export holds ONE row carrying the credit note's
document date.

### Verified fact census (cite these; do not re-derive)

| # | Fact | Where |
|---|------|-------|
| F1 | Columns today: `closeout_id, case_id, vendor, tax_invoice_no, tax_invoice_date, amount_pre_vat_thb, vat_thb, total_thb, entered_by, entered_at, seq` + `tenant_id` via `TenantKeyMixin`. **No document-type column.** | `services/db/repair_case_closeout.py:113-153` |
| F2 | `__table_args__` = Index + `UniqueConstraint(tenant_id, seq)` — **no sign CheckConstraint**. CheckConstraint precedent (vocabulary stated as schema, not docstring): `ck_repair_case_accepted_quote_basis` | `repair_case_closeout.py:105-111`; `services/db/repair_case_evidence.py:230-233` |
| F3 | `vat_thb` NULL = "vendor not VAT-registered", a **different fact** from `0.00`. Any new nullable column must state its NULL meaning the same way. | `repair_case_closeout.py:98-101,141-142`; positive control `test_the_guard_does_not_refuse_an_ordinary_zero_vat_invoice` |
| F4 | `RepairCaseOrderNumber`: **exactly one per case** — `case_id` is the primary key; allocator idempotent by case; series gap-free within a year by construction. | `repair_case_closeout.py:55-92,206-258` |
| F5 | Interim refusal: any negative `amount_pre_vat_thb`/`vat_thb`/`total_thb` → 422, checked BEFORE the totals comparison because a credit note is internally coherent. Docstring states the lift condition: *"Lift this only together with that schema — a silent lift re-arms the replacement failure."* | `services/api/routers/cases.py:786-828` |
| F6 | Quote-side precedent — negatives refused for the same stated reason (*"Not a discount — a typo or a credit note."*). **Stays; out of scope.** | `tests/api/test_cases_endpoint.py:285` |
| F7 | Export: 15 fixed Express columns (`EXPORT_COLUMNS`), **one row per case** (`load_monthly_export` loops case ids → one `_build_row` each). No document-type column in the CSV. Extra CSV columns are documented as breaking Express keyability (the exception-labels precedent). | `services/db/repair_spend_export.py:83-99,646-657,666-751,212-225` |
| F8 | `MonthlyExport.total_thb` is a plain `sum()` over rows; `ungoverned_thb` likewise. Governed rows file by **approval date** (audit `occurred_at` in month); ungoverned close-outs file by **`entered_at`**, not `tax_invoice_date`. | `repair_spend_export.py:227-239,586-640` |
| F9 | KPI: `is_fully_traceable` requires governed + paperwork complete; `traceability_pct = traceable / len(rows)`; `audit_answers` asks "who approved it" of **every** row. | `repair_spend_export.py:363-406,186-199,302-322` |
| F10 | An ordering-guard test pins `latest_closeout`'s `seq.desc()` pick — any reader change must keep or consciously amend it. | `tests/services/db/test_run_analytics_ordering_guard.py:290` |
| F11 | Retention enumerates FK children of `repair_case` in **deletion order**, with a completeness guard asserting the declared list EQUAL to live-metadata FKs at the root, and an order guard over child-to-child FKs. `RepairCaseCloseout` is in the list; a new table must join it. | `services/db/repair_case_retention.py:64-100` |
| F12 | `operate_seed.py` constructs `RepairCaseCloseout` rows **directly** (bypasses the endpoint) — a new NOT NULL column breaks the seed unless defaulted there. | `verticals/fleet_maintenance/operate_seed.py:665-680` |
| F13 | Migrations `0013`–`0025` exist; head = `alembic/versions/0025_task_event_seq.py`; this table already has migrations (`0017`, `0018`, `0021`) — **a migration is the normal path; the next slot is `0026`**. | `alembic/versions/` |
| F14 | Fleet has its own Postgres (ADR-0037). Tab J is on fleet's ingress allowlist **cover-endpoint only**; `/api/cases/{id}/closeout` is not on the published allowlist. | `tests/deploy/test_published_profiles.py:141-143`; `operate_seed.py:480-483` |
| F15 | RoPA texts are the **controller's** (Cray's) to author — ADR-0037 D2.1: *"no PLAN or drafter authors its text."* This PLAN may only **flag** an amendment. | `docs/compliance/ropa-fleet-cases.md:8-16` |

### Asserted-not-verified (mark stays until resolved)

- **AV-1 — What Express/accounting actually reconciles a ใบลดหนี้ against** (own line in
  its own document month vs netted into the invoice line; whether a negative-amount row
  keyed with a credit-note number in `เลขที่ใบกำกับภาษี` imports cleanly). Not derivable
  from the repo. Same class as the ศูนย์ต้นทุน granularity question AC-9 pre-authorised
  shipping unfilled — a partner-intake question. **NOT closed by the 2026-08-19
  rulings:** SD-C's ruling is (b) *provisional on AV-1* — confirm before Step 4 lands.
- **AV-2 — retention-guard coverage of the new credit table — now LIVE (SD-A(b)
  ruled), resolved empirically at Step 6 / AC-7 with a witnessed RED, never asserted.
  NOT closed by the rulings.** Code-read at recording time (2026-08-19) sharpens what
  the guards actually assert (`tests/services/db/test_case_retention_completeness.py`):
  `test_ac5i_the_declared_fk_children_equal_the_fks_the_metadata_declares` asserts set
  **equality** between `FK_CHILD_TABLES` and the tables holding an FK to
  `repair_case.case_id` (`:42-55,70-91`), and
  `test_ac5ii_every_case_id_bearing_table_is_classified_exactly_once` reddens on ANY
  `case_id`-bearing table left unclassified (`:94-117`) — so the **ruled shape**
  (root FK + `case_id` column) is covered by both walks *on code-read*. Two residuals
  keep AV-2 open: (i) **no witnessed RED yet** — coverage stays a code-read claim
  until AC-7's probe reddens `test_ac5i` naming `repair_case_credit_note`;
  (ii) the true child-of-child shape — a table referencing `repair_case_closeout`
  while carrying **no** `case_id` column — is invisible to BOTH walks
  (`_tables_with_an_fk_to_repair_case` filters on the root target only, `:42-55`;
  `_tables_with_a_case_id_column` needs the column, `:45-46`), and the order guard
  inspects only edges whose source is already declared in the family (`:171-185`).
  The ruled build does not construct that shape (document-number linkage, no FK to
  `repair_case_closeout`), so Step 6 also forbids drifting into it: any later FK
  targeting `repair_case_closeout` requires a guard extension witnessed RED **before**
  the FK lands.
- **AV-3 — No third production reader of the close-out row.** Grep over `services/` finds
  only F7's two consumers plus retention (deletion) and `operate_seed` (writer). Claimed
  exhaustive **for `services/` at draft time**; the executor re-greps at execution time
  (the base moves).

## Surfaced decisions — ALL SIX RULED (Cray, typed 2026-08-19)

> These had multiple defensible answers with different schema/consumer consequences;
> ADR-009 D1 made them Cray's, not Code's. SD-A and SD-E were ruled **together** —
> the cardinality couples them, and SD-A's branch was *selected by* SD-E's ruling.
> The options and reasoning below are **retained deliberately**: a future reader must
> see what was rejected and why. Only SD-C's ruling remains provisional (on AV-1).

### SD-A — Shape of the record

**RULED (Cray, typed 2026-08-19): (b) — the separate `repair_case_credit_note`
table.** Selected **by SD-E's cardinality ruling**, not chosen independently: per the
contingent recommendation below, once N partial credits coexist, latest-per-kind
cannot hold them without re-arming the replacement trap one level down.

**Question.** Where does a credit note live?

- **(a) `document_type` discriminator on `repair_case_closeout`** (`'invoice' |
  'credit_note'`, CheckConstraint per F2 precedent) + a nullable
  `credits_tax_invoice_no` naming the credited invoice. One migration; reuses the
  existing append-only/seq/tenant machinery; the correction path (เมย์ can mistype a
  credit note too) comes for free — but "latest-wins" must become **latest per
  document kind**, and if SD-E admits *multiple coexisting* credit notes per case,
  latest-per-kind silently replaces the first partial credit with the second — **the
  same replacement trap, one level down**.
- **(b) Separate `repair_case_credit_note` table** keyed to the case (FK to
  `repair_case.case_id`; names the credited invoice by document number). Clean
  coexistence of N credits; duplicates the append-only/seq/correction machinery; must
  join retention's deletion list (F11) and the export must union a second source.
- **(c) Explicit invoice↔credit link row** (credit stored per (a) or (b), plus a link
  table pinning which close-out row it credits). Strongest audit join; most schema; the
  link must survive the invoice being *corrected* (a new invoice row lands — the link
  points at a superseded `closeout_id`).

**Recommendation (contingent):** **(a) if SD-E rules "at most one current credit note
per case"** — it is the existing machinery applied twice, and the CheckConstraint can
state sign-by-kind at the schema level (invoice rows ≥ 0, credit rows ≤ 0). **(b) if
multiple concurrent partial credits must coexist** — forcing them through
latest-per-kind re-arms the trap this PLAN exists to close. (c) is not recommended
alone: linking to a correctable `closeout_id` couples the credit to a superseded row;
linking by document number gets (c)'s benefit inside (a)/(b) for one column.

**Why Cray:** this fixes what the DB can and cannot refuse, and how many real-world
paperwork shapes (multiple partial credits) the pilot promises to hold.

### SD-B — What `latest_closeout` returns once two document kinds exist

**RULED (Cray, typed 2026-08-19): (b) — the one composite reader; the raw-latest
read becomes uncallable from outside the module.**

**Constraint (already documented, F10 + the function's own docstring):** *"every
consumer — the case endpoint, the month-end export — must agree on which row is
current. One query in one place is how they stay agreed."* The two consumers must not
be allowed to disagree, whatever is chosen.

- **(a) Keep the signature** — `latest_closeout` returns the latest **invoice** row
  only; add a sibling reader (`current_credit_notes(session, case_id)`); each consumer
  calls both. Two readers = two chances to call only one.
- **(b) One composite reader** — `current_closeout_documents(session, case_id) →
  CurrentCloseoutDocuments(invoice: RepairCaseCloseout | None, credits:
  tuple[RepairCaseCloseout, ...])` (or the two-table equivalent under SD-A(b));
  `latest_closeout` becomes internal or is deleted so no caller can accidentally read
  the raw latest row again. Both consumers are **forced** through the one richer read.
- **(c) Leave it returning the raw newest row** — named only to reject: that is the
  measured replacement failure verbatim.

**Recommendation:** **(b)**. It is the docstring's own one-query-one-place rule,
generalised; both consumers need both facts anyway (the endpoint must return credits;
the export must aggregate them). The F10 ordering guard is amended in the same commit,
consciously, never silently.

**Why Cray:** it deletes/renames a documented seam two consumers and a guard test pin.

### SD-C — Month-end presentation

**RULED (Cray, typed 2026-08-19): (b) — two lines matching real documents, the
credit filed in its own month. ⚠️ Provisional on AV-1 (the ruling did not close it):
confirm what Express/accounting reconciles a ใบลดหนี้ against before Step 4 lands; if
the intake answer contradicts two-line filing, SD-C returns to Cray with the answer
attached — the executor does not re-decide it.**

**Question.** Does the export show a credited repair as **one netted line**
(`5,000.00`) or **two lines that sum to the net** (invoice `20,000.00` + credit
`-15,000.00`, credit-note number in `เลขที่ใบกำกับภาษี`)?

- **(a) Net one line.** Keeps one-row-per-case (F7), the KPI denominator, and Express
  keyability untouched. But it prints a figure that matches **no piece of paper** —
  the export's stated purpose is reconciling against documents — and it silently
  rewrites an already-issued month: governed rows file by approval date (F8), so a
  September credit netted into an August-approved case changes August's figure on
  re-run.
- **(b) Two lines.** Each line matches one real document; the credit line files in its
  **own** month (`entered_at` for month selection, per F8's ungoverned precedent, with
  the credit's own document date in `วันที่เอกสาร`), so a closed month's figure never
  moves retroactively. Costs: `load_monthly_export`'s one-row-per-case loop is
  restructured, and SD-F must decide what the extra row does to the KPI.

**Which one Express/accounting actually reconciles against: AV-1 —
asserted-not-verified.** Domain practice for Thai VAT paperwork *suggests* a ใบลดหนี้ is
its own document reported in its own tax month, which favours (b) — but that is
outside-repo knowledge; treat as an intake question, not a fact.

**Recommendation:** **(b)** — the net-one-line option quietly mutates reconciled
months, which is this table's original sin wearing a new hat. Confirm against AV-1
before Step 4 lands.

**Why Cray:** this is the number the partner's accountant keys; it is a product
promise, not an implementation detail.

### SD-D — Does a credit note get its own repair-order number?

**RULED (Cray, typed 2026-08-19): (a) — the credit inherits the case's `RC-`
number.** F4's one-number-per-case invariant stands untouched.

- **(a) Inherit the case's `RC-` number.** F4's invariant (one number per case,
  `case_id` = PK, gap-free series) stands untouched; the credit is paperwork about the
  same repair, and the series counts **repairs**, not documents.
- **(b) Allocate its own number.** Requires dismantling the PK-enforced one-per-case
  invariant and re-stating what the gap-free series means — for no consumer identified
  in this draft that needs it.

**Recommendation:** **(a)**, firmly. (b) exists as a slot only because a partner's
Express conventions could conceivably demand a distinct reference per keyed line
(AV-1).

### SD-E — Partial vs full credit; over-credit; how many credits per case

**RULED (Cray, typed 2026-08-19): MULTIPLE partial credit notes may coexist on one
case** (ทยอยลด — the vendor credits in instalments). Partial **and** full credits
allowed; over-credit refused 422, as recommended. **This cardinality is what selects
SD-A(b)** — see SD-A's RULED line.

- Partial credits: the measured fixture is itself partial (−15,000 against 20,000) —
  refusing partials contradicts the paperwork that motivated the LOCKED ruling.
  **Recommend: allow partial and full.**
- Over-credit (cumulative credits exceeding the invoice's current total): **recommend
  refuse 422**, same spirit as the totals-must-agree check (`cases.py:781-785` — เมย์
  still has the paper in her hand; month-end is a filing cabinet away). The refusal
  message names the invoice total and the cumulative credit, like the F5 message names
  its fields.
- **The crux that couples SD-A: how many credit notes may coexist on one case?** If
  "at most one current credit" → SD-A(a) is the whole machinery. If "N partial
  credits coexist" → latest-per-kind cannot hold them, and the correction path needs a
  per-credit identity (which document is เมย์ correcting?) — a mistyped credit-note
  *number* cannot itself be the identity key. **Recommend: rule the cardinality
  explicitly**; this draft's Steps were originally written for both branches
  (collapsed to the ruled SD-A(b) branch when the rulings were recorded, 2026-08-19 —
  the per-credit-identity consequence is directed at Step 1).

**Why Cray:** cardinality + over-credit policy define what the system refuses a real
operator mid-paperwork.

### SD-F — KPI / `is_fully_traceable` consequence

**RULED (Cray, typed 2026-08-19): (a) — the KPI counts repairs, not documents.**
The SD-C(b) × SD-F(a) interaction is now first-class: see AC-6, which fixes the
denominator-exclusion, approval-question-exclusion, and case-level credit-completeness
consequences as probeable assertions.

Verified consequences (F9): the denominator is `len(rows)`; `audit_answers` asks "who
approved it" of every row; a second line per case (SD-C(b)) would (i) double-weight
credited cases in the KPI, (ii) score the credit line as unanswerable on the approval
questions — no gate ever decided the credit — dragging `audit_answer_pct` down for
having *more complete* paperwork.

- **(a) The KPI counts repairs, not documents.** Denominator stays per case; credit
  lines are excluded from `rows`' KPI arithmetic (or carried as a non-KPI row kind);
  the case's own `is_fully_traceable` additionally requires each credit's paperwork
  complete (number + document date + amounts) — an incomplete credit makes the *case*
  untraceable.
- **(b) Every line is a row.** Simple, but the KPI moves for document-count reasons
  unrelated to governance — the number AC-9 puts in front of a partner starts
  measuring paperwork volume.

**Recommendation:** **(a)**. The KPI's definition is deliberately "one function in the
open where it can be argued with" (F9) — this is the argument, and it should be settled
by ruling, not drift.

## Acceptance Criteria

> Every command runs via WSL from the repo root with `2>&1` merged (CLAUDE.md §8).
> Pass reads are fixed **here, before any run**. Each test-closing AC names its
> non-vacuity probe: the mutation, the assertion it must redden, and the direction.
> **All six SDs are RULED (Cray, typed 2026-08-19)** — SD-E multiple partial credits
> coexist → SD-A(b) `repair_case_credit_note` table, SD-B(b) composite reader,
> SD-C(b) two lines (provisional on AV-1), SD-D(a) inherited `RC-` number, SD-F(a)
> KPI counts repairs. Every pass read below is fixed against the **ruled** options;
> the draft's two-branch conditionality is collapsed. The only remaining contingency
> is SD-C(b)'s AV-1 caveat (AC-5, Step 0/Step 4).

- [ ] **AC-1 — Schema + migration `0026` round-trips.**
  Command: `uv run alembic upgrade head && uv run alembic check && uv run alembic downgrade 0025 && uv run alembic upgrade head`.
  Pass read: both `upgrade` runs exit 0; `alembic check` reports no drift; downgrade
  leaves migrations `0013`–`0025` intact. (Caveat: `alembic check` cannot see
  server-default-only drift — MEMORY s203; the round-trip is the load-bearing half.)
  Non-vacuity probe: with the DB at `0025`, run the AC-3 scenario test — it must go
  RED with `UndefinedTable` on `repair_case_credit_note` (direction: the ruled
  SD-A(b) table is what admits the credit), then green again at head.

- [ ] **AC-2 — Both consumers agree on the coexisting facts** *(SD-B(b) as ruled)*.
  A test drives `POST` invoice then `POST` credit, then reads **both** consumers:
  `GET /api/cases/{id}/closeout` and the case's export row(s).
  Command: `uv run pytest tests/api/test_closeout_credit_note_scenario.py -q -k consumers_agree 2>&1`.
  Pass read fixed now (ruled options): endpoint reports invoice
  `total_thb == 20000.00` AND the credit `-15000.00` as distinct documents; the export
  holds a `20000.00` line and a `-15000.00` line for the case; **no reader anywhere
  reports `-15000.00` as the case's whole cost**.
  Non-vacuity probe: point one consumer back at a raw newest-row read (re-inline the
  old `latest_closeout` call) → the invoice-side assertion
  (`total_thb == 20000.00`) must redden reading `-15000.00` — the measured replacement
  failure, resurrected on purpose and witnessed RED. Restore from a `/tmp` copy, not
  git.

- [ ] **AC-3 — Scenario test: real producer → real consumer (CLAUDE.md §8, binding).**
  New module `tests/api/test_closeout_credit_note_scenario.py`, modelled on the
  PLAN-0107 AC-11 module: producer = the real authn-on `POST /api/cases/{id}/closeout`
  + the real credit route (SD-A(b) as ruled — Step 3's new endpoint, nothing seeded
  directly into the table), consumer = the real `load_monthly_export` and
  its real `total_thb` sum (F8). Realistic data: invoice `18,691.59 + 1,308.41 =
  20,000.00`; credit `-14,018.69 + -981.31 = -15,000.00`. Nothing stubbed on either
  side; DB-backed, SKIP ≠ satisfaction; month bounds derived in `Asia/Bangkok`, and
  month selection keyed on `entered_at` (F8 — a `tax_invoice_date`-keyed month
  silently selects an empty one).
  Command: `uv run pytest tests/api/test_closeout_credit_note_scenario.py -q 2>&1`.
  Pass read fixed now (ruled options): the month-end `total_thb == 5000.00`
  when both documents key in the same month; the ฿ assertion is ordered **before**
  any status-code assertion (the PLAN-0107 module's own lesson, stated in its
  docstring at lines 219-224).
  Non-vacuity probe: filter credit rows out of the consumer's aggregation (one-line
  mutation in `repair_spend_export.py`) → `total_thb == 5000.00` must redden reading
  `20000.00` (direction: the credit stopped reaching the figure).

- [ ] **AC-4 — The interim guard is lifted only as re-scoping, never as removal.**
  The plain **invoice** path still refuses negative money with the F5-style message;
  the credit path is the only door that admits a negative, per the SD-E rules
  (over-credit refused). The `key_closeout` docstring's 🔴 interim block
  (`cases.py:794-800`) is rewritten to record that the lift condition was met and by
  which PLAN.
  Command: `uv run pytest tests/api/test_closeout_negative_money_scenario.py tests/api/test_closeout_credit_note_scenario.py -q 2>&1`.
  Pass read fixed now: a negative keyed as an ordinary invoice close-out → 422 naming
  the field; an over-credit → 422 naming invoice total + cumulative credit; the
  in-range credit → 201. Each of the four existing PLAN-0107 tests is explicitly
  dispositioned in the diff (kept / reworked / superseded-with-reason) — none silently
  deleted.
  Non-vacuity probe: remove the invoice-path sign check → the invoice-path 422
  assertion must redden with a 201 (direction: the door that must stay shut, opened).

- [ ] **AC-5 — Express CSV shape holds** *(SD-C(b) as ruled — ⚠️ provisional on
  AV-1; confirmed at Step 0 before Step 4 lands)*.
  Command: `uv run pytest tests/services/db/test_repair_spend_export.py tests/api/test_repair_spend_export_scenario.py tests/api/test_export_cover_ui_contract.py -q 2>&1`
  (paths verified by repo grep at recording time, 2026-08-19 — the draft's
  `test_export_endpoint*.py` pattern matched nothing; executor re-confirms at Step 0,
  the base moves).
  Pass read fixed now (SD-C(b)): `to_csv` still emits **exactly the 15
  `EXPORT_COLUMNS`** (F7 — Express keyability is a documented constraint, not a
  preference); the credit line carries the credit note's own number and document date;
  a re-run of the **invoice's** month after the credit lands in a later month is
  byte-identical to before the credit (no retroactive mutation).
  Non-vacuity probe: append a 16th column to the writer → the column-count assertion
  must redden 16 ≠ 15.

- [ ] **AC-6 — The SD-C(b) × SD-F(a) interaction, first-class: two lines per
  credited case, ONE KPI unit.**
  The ruled pair interacts: SD-C(b) puts a second line in `rows` for a credited case,
  SD-F(a) says the KPI counts repairs — so the credit line must be **excluded from
  the KPI denominator and from the approval questions**, while the case's own
  judgment **absorbs** credit paperwork completeness.
  Command: `uv run pytest tests/services/db/test_repair_spend_export.py -q -k "traceab or credit" 2>&1`.
  Pass read fixed now, against the verified KPI surfaces (`repair_spend_export.py`:
  denominator `len(self.rows)` at `:190-199`; `cover_summary`'s
  `askable = len(self.rows) * len(AUDIT_QUESTIONS)` at `:241-244`; `audit_answers`
  at `:302-322`; `is_fully_traceable` at `:363-406`):
  (i) a governed, fully-papered case with a fully-papered credit is traceable and
  counts **once** — `traceability_pct` and the cover's audit-answer figures are
  **identical** before and after the credit is added to the already-counted case;
  (ii) the same case with a credit missing its document number is **not** traceable —
  each credit's paperwork completeness (number + document date + amounts) folds into
  the case's `is_fully_traceable`;
  (iii) the approval questions are **never asked of a credit line** — no gate ever
  decided the credit, and its structural unanswerability must not drag
  `audit_answer_pct` down for *more complete* paperwork;
  (iv) a credit on a **governed** case leaves `ungoverned_thb` (`:231-239`)
  unchanged — the credit line inherits its case's governed status for the money
  buckets, else a governed case's credit prints as negative escaped money — while
  `MonthlyExport.total_thb` (`:227-229`) **does** include the credit line (that
  netting is the Goal figure).
  Non-vacuity probes (mutation → the assertion it must redden, direction):
  **P1** — re-admit credit lines into the KPI arithmetic (drop the row-kind exclusion
  in `traceability_pct` / `cover_summary`) → assertion (i) reddens: the denominator
  grows by one per credit and the pct moves (direction: a credit line re-entered the
  denominator — this probe is the tripwire the ruling asked for);
  **P2** — mutate `is_fully_traceable` to ignore credit completeness → assertion (ii)
  reddens traceable-when-it-must-not-be;
  **P3** — ask the approval questions of the credit line → assertion (iii) reddens:
  `audit_answer_pct` drops on a case whose paperwork got *more* complete.

- [ ] **AC-7 — Retention still deletes everything, in order** *(SD-A(b) as ruled —
  fires unconditionally; the conditional framing is collapsed)*.
  `RepairCaseCreditNote` joins `_FK_CHILD_MODELS`
  (`services/db/repair_case_retention.py:82-89`). The order guard imposes **no**
  position constraint on it — the ruled shape holds no inter-child FK
  (document-number linkage, no FK to `repair_case_closeout`) — place it adjacent to
  `RepairCaseCloseout` for the reader; the order guard's own edge-emptiness assertion
  (`test_case_retention_completeness.py:209-213`) stays satisfied by the standing
  accepted-quote→quote edge.
  Command: `uv run pytest tests/services/db/test_case_retention.py tests/services/db/test_case_retention_completeness.py tests/api/test_case_retention_scenario.py -q 2>&1`
  (paths verified by repo grep at recording time, 2026-08-19 — the draft's
  `test_repair_case_retention*.py` pattern matched nothing; executor re-confirms at
  Step 0).
  Pass read fixed now: `test_ac5i_the_declared_fk_children_equal_the_fks_the_metadata_declares`,
  `test_ac5ii_every_case_id_bearing_table_is_classified_exactly_once`, and
  `test_the_declared_order_respects_every_child_to_child_dependency` all green with
  the new table declared; the retention scenario deletes a seeded case carrying an
  invoice + **N ≥ 2** coexisting partial credits (SD-E's ruled cardinality, not the
  single-credit shape) cleanly past the window.
  Non-vacuity probe — **this probe IS AV-2's empirical resolution; witnessed, never
  asserted**: with the table created, remove `RepairCaseCreditNote` from
  `_FK_CHILD_MODELS` → `test_ac5i` must redden in its *"declares an FK to repair_case
  but the sweep never clears it"* direction, naming `repair_case_credit_note` (the
  assertion message spells both directions — `test_case_retention_completeness.py:86-91`).
  If it does NOT redden, the guard has the hole AV-2 predicted: extend the guard in
  the same step and witness the extension RED first. Standing prohibition either way
  (AV-2(ii)): any later FK targeting `repair_case_closeout` — the shape invisible to
  both walks — requires a guard extension witnessed RED **before** that FK lands.

- [ ] **AC-8 — Sign stated as schema, not convention** *(SD-A(b) as ruled — the
  constraint splits across two tables)*.
  CheckConstraints per the F2 precedent: `repair_case_closeout` money columns
  **non-negative** (the invoice table can no longer hold the negative the measured
  failure rode in on), `repair_case_credit_note` amounts **non-positive** (matching
  the measured fixture and the export line). `vat_thb` NULL-vs-zero semantics (F3)
  restated verbatim on the credit table's column comment — NULL = vendor not
  VAT-registered, a different fact from `0.00`.
  Command: `uv run pytest tests/services/db/ -q -k "closeout or credit" 2>&1` including a direct-INSERT test that bypasses the API.
  Pass read fixed now: a raw INSERT of a negative invoice row or a positive credit row
  raises `IntegrityError` naming the constraint.
  Non-vacuity probe: this AC **is** the probe for the API-layer checks — the DB
  refuses what a future endpoint forgets to; witnessed RED by the direct INSERT before
  the constraint exists (run once against `0025`).

- [ ] **AC-9 — Compliance flag raised, not authored.**
  A dated note is added to `docs/STATUS.md` Active TODOs surfacing to Cray: does the
  fleet RoPA dataset description (`docs/compliance/ropa-fleet-cases.md`, and
  `ropa-change-statement-fleet.md`) cover credit-note documents, and does D2.1 require
  an amendment? **This PLAN does not edit RoPA text** — ADR-0037 D2.1 reserves it to
  Cray (F15).
  Command: `grep -n "0111" docs/STATUS.md`.
  Pass read: the TODO line exists, names both files and D2.1, and carries no drafted
  RoPA wording.

- [ ] **AC-10 — Full gates.** `uv run pytest tests/ -q 2>&1`, `uv run mypy services/ 2>&1`,
  `uv run ruff check . 2>&1` (bare `.`, matching CI — MEMORY: explicit paths bypass
  exclude). Pass read: all exit 0; the F10 ordering guard is green **as amended**, with
  its amendment in the same commit as the reader change, never a follow-up.

## Out of Scope

- ❌ **Lifting the PR #1226 interim guard on its own.** The guard's docstring states the
  lift condition; a lift lands only in the same PR as the schema + both consumers
  (AC-4). A standalone lift re-arms the measured replacement failure.
- ❌ **Any host-state deploy to MS-S1** (CLAUDE.md §8 — explicit Cray go required;
  nothing here needs one).
- ❌ **Redesigning the quote-side negative refusal** (F6). It is correct and stays: a
  negative *quote* is still a typo or a credit note in the wrong doorway.
- ❌ **UI for keying credit notes.** `/api/cases/{id}/closeout` is not on the published
  allowlist (F14); the internal keying surface follows in its own PLAN once the record
  exists.
- ❌ **RoPA text authoring** (F15 — D2.1; AC-9 only flags).
- ❌ **Back-computing VAT on credit notes.** Rejected twice, typed, for invoices
  (`repair_case_closeout.py:24-29`); the same ruling binds credits — all three figures
  supplied, none derived.

## Steps

### Step 0: Ruling round — **DONE** (Cray, typed 2026-08-19) + residual confirmations

The rulings are recorded inline per SD and every pass read in this file is re-fixed
against them (same edit, 2026-08-19; test paths in AC-5/AC-7 corrected to
grep-verified ones in that edit). **Remaining Step-0 work for the executor, before
Step 1:** re-grep AV-3 (readers of the close-out row) and re-confirm the AC-5/AC-6/
AC-7 test paths against the then-current tree (the base moves), and pursue **AV-1 by
partner intake — SD-C(b) is provisional on it; confirm before Step 4 lands.** If the
intake answer contradicts two-line filing, SD-C returns to Cray with the answer
attached — the executor does not re-decide it.

### Step 1: Schema — new module `services/db/repair_case_credit_note.py` + `alembic/versions/0026_*.py`

Per SD-A(b) **as ruled** (the (a)/(c) shapes remain recorded in SD-A as the rejected
alternatives; no `document_type` discriminator is added to `repair_case_closeout`):
- New table `repair_case_credit_note`: TenantKeyMixin; own `seq` Identity +
  `UniqueConstraint(tenant_id, seq)` per F1's pattern (append-only — a correction is
  a new row, never an UPDATE); FK to `repair_case.case_id`; the credited invoice
  named by **document number**, never by `closeout_id` — a corrected invoice must not
  orphan the credit — and **no FK may target `repair_case_closeout`** (AV-2(ii): that
  shape is invisible to the retention walks).
- **Per-credit identity for corrections** (the consequence SD-E's ruled cardinality
  makes mandatory — the crux itself noted a mistyped credit-note *number* cannot be
  the identity key): each row carries its own `credit_note_id` PK; a correction row
  names its predecessor via `supersedes_credit_note_id` (plain column, no FK — same
  no-FK reasoning as the invoice linkage); *current* credits = unsuperseded rows, and
  the over-credit arithmetic (Step 3) reads current credits only. Executor-directed
  mechanism within the ruled shape, reviewable at PR — not a re-opened SD.
- Migration `0026` creates the table and adds AC-8's CheckConstraints on **both**
  tables; round-trip per AC-1. Money stays `Numeric`, never float (module docstring
  rule); all three figures supplied, none derived (Out of Scope).
- **Seed verified unaffected — F12's hazard is closed for the ruled branch:** SD-A(b)
  leaves `RepairCaseCloseout`'s columns untouched, so the direct constructor at
  `operate_seed.py:672-685` compiles and runs unchanged; no edit, no defaulting
  (the NOT-NULL-column hazard was an (a)-branch consequence — moot as ruled).
  Seeding a *demonstration* credit note is not a step of this PLAN; it rides the
  keying-surface PLAN (see Out of Scope: UI).

### Step 2: Reader — SD-B's single seam

Per SD-B(b) **as ruled**: introduce the composite reader —
`current_closeout_documents(session, case_id) → CurrentCloseoutDocuments(invoice:
RepairCaseCloseout | None, credits: tuple[RepairCaseCreditNote, ...])`, the
two-table equivalent SD-B(b) named — in `services/db/repair_case_closeout.py`,
route **both** consumers (`repair_spend_export.py:683`, `cases.py:884`) through it,
and make the raw-latest read uncallable from outside the module. Amend the F10
ordering guard (`tests/services/db/test_run_analytics_ordering_guard.py:290`) in the
same commit, stating why the pick changed. The reader's docstring carries forward the
one-query-one-place rationale verbatim — it is the constraint that made this PLAN
necessary and the one that prevents its recurrence.

### Step 3: Producer — `services/api/routers/cases.py` + `services/api/models/cases.py`

Per SD-A(b) **as ruled**: a credit-note request model + its own route —
`CloseOutRequest` (`models/cases.py:422`) is **not** extended; the invoice path's
request shape is untouched. Mechanisms:
- The invoice path's sign check **stays**, message intact (AC-4).
- The credit path enforces SD-E as ruled: internally coherent totals (reuse the
  existing comparison), non-positive sign, **over-credit refused 422 against the
  invoice's current total + the cumulative *current* credits** (SD-E's ruled
  cardinality — N coexisting partials, ทยอยลด, must sum), credit-before-invoice
  refused (there is nothing to credit), document number + date coherence rule
  carried over (`cases.py:841-856`).
- `key_closeout`'s 🔴 interim docstring block is rewritten to record the lift
  (AC-4); `get_closeout` / its response model return the composite (SD-B(b)) —
  the invoice plus **all** current credits as distinct documents.

### Step 4: Consumer — `services/db/repair_spend_export.py`

Per SD-C(b) + SD-F(a) **as ruled**. ⚠️ Gated on the AV-1 confirmation (Step 0) —
SD-C(b) is provisional until the intake answer lands.
- **`load_monthly_export` unions a second source — a verified gap, not a style
  choice:** today the ungoverned branch enumerates cases **only** from
  `RepairCaseCloseout.entered_at` (`repair_spend_export.py:631-640`) and the month's
  case set is `governed_by_case | ungoverned_case_ids` (`:646`) — a case whose only
  in-month activity is a credit would produce **no row at all**. Add the equivalent
  select over `RepairCaseCreditNote.entered_at` to the enumeration, and file each
  credit line by the credit's own `entered_at` month (F8's ungoverned precedent —
  never the nullable document date), with the credit's document date in
  `วันที่เอกสาร`.
- `_build_row` splits into per-document assembly; its `latest_closeout` call
  (`:683`) becomes the Step-2 composite reader.
- `to_csv` unchanged in column count (AC-5).
- KPI per SD-F(a): credit rows carried outside the KPI arithmetic — **AC-6's four
  assertions are the spec** (denominator invariance; approval questions never asked
  of a credit line; credit completeness folded into the case's `is_fully_traceable`;
  the credit line inherits its case's governed status so `ungoverned_thb` never
  shows negative escaped money on a governed case).
- The governed-month/approval-date filing for the *invoice* row is untouched.

### Step 5: Tests

- New scenario module per AC-3 (real producer → real consumer; nothing stubbed).
- AC-2 consumers-agree test; AC-6 KPI tests; AC-8 direct-INSERT constraint tests.
- Disposition each existing PLAN-0107 AC-11 test per AC-4 — kept / reworked /
  superseded, stated in the diff, none silently dropped.
- Every load-bearing green witnessed RED per its named probe (CLAUDE.md §8;
  restore mutations from `/tmp`, not git).

### Step 6: Retention + census closeout

SD-A(b) created the table, so this step fires unconditionally: `_FK_CHILD_MODELS`
(`repair_case_retention.py:82-89`) gains `RepairCaseCreditNote` (F11; placement per
AC-7 — no inter-child FK constrains it). **AC-7's probe IS AV-2's empirical
resolution**: witness `test_ac5i` RED naming `repair_case_credit_note` before
trusting the guard, and honor the standing prohibition — no FK targeting
`repair_case_closeout` without first extending the guard family and witnessing the
extension RED (AV-2(ii)). Then re-grep `RepairCaseCloseout` + `RepairCaseCreditNote`
over `services/` + `verticals/` and reconcile against AV-3's census before the PR is
opened.

### Step 7: Compliance flag + PLAN closeout

AC-9's STATUS TODO; PLAN moves to `docs/plans/done/` only after all ACs are checked
(the rulings themselves are recorded — 2026-08-19, this file; keep `Status: Draft`
until closeout — an "Accepted" PLAN G1-gates its own closeout, and Cray ratifies the
PLAN at PR merge).

## Verification

- Each AC's own command + fixed pass read, in AC order; AC-10's full gates last.
- The one figure that summarises the whole PLAN, from AC-3's scenario: a case carrying
  a real invoice (`20,000.00`) and a real ใบลดหนี้ (`-15,000.00`) month-ends at
  **`5,000.00`** (SD-C(b) as ruled: two lines summing to it, each matching a real
  document), with both documents readable from both consumers — against today's
  measured `20,000.00 → -15,000.00` replacement.
- Non-vacuity: every probe above names its mutation, its reddened assertion, and the
  direction; a probe whose RED was never witnessed does not close its AC.
