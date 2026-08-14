# PLAN-0105: Fleet repair-case retention — in-app periodic deletion of visitor-opened case data at 90 days

**Status:** Draft
**Owner:** Claude Code
**Created:** 2026-08-14
**Related ADRs:** ADR-0035 (published-demo posture; D6 prompt-log regime — explicitly NOT inherited, see LOCKED-1), ADR-0037 (fleet compliance direction; D2.1/D4)
**Related PLANs:** PLAN-0096 (case capture), PLAN-0100 (published demo), PLAN-0103 (AC-11 — this PLAN is a *precondition* of its closure, see §Ordering)

## Context — what exists and what does not

The furthest solved point of retention in this repo is **file** retention:
`services/engine/llm/prompt_log.py` deletes prompt-log day-files older than
`RETENTION_DAYS = 90` (`prompt_log.py:32`) on the write path, with its rationale
stated in its own comment (`:28-31`): *"there is no cron on the published box, and
a retention policy whose enforcement depends on a scheduler nobody installed is a
promise, not a control."* Its `rotate()` (`:59-78`) never raises, returns what it
deleted, and retries next time what it could not remove. Its `_file_date`
(`:42-56`) reads age from the file **name, never mtime** — a copy, restore, or
volume remount rewrites mtimes and would silently resurrect expired data.

**Row** retention does not exist. Every purge path in the repo operates on
prompt-log files only (`docs/runbooks/published-demo-operations.md` §1.2/§1.3 —
`find … -name 'prompt-*.jsonl' -delete`). Fleet's published system is the first
with a visitor-writable surface whose free text persists to Postgres
(`docs/compliance/ropa-change-statement-fleet.md` §1, §3), and §3's retention cell
reads *"no number exists yet."* This PLAN builds the row half.

### LOCKED rulings (Cray, typed, 2026-08-14) — restated, not re-litigated

1. **Retention = 90 days — an independent decision.** ⚠️ It *coincides* with the
   prompt log's number but does **not** inherit from it:
   `docs/compliance/ropa-change-statement-fleet.md` §4(a) records that ADR-0035
   D6's regime is defined per request to a published LLM route and **does not
   reach case text**. A future D6 change changes nothing here; a future change
   here changes nothing in D6. AC-9 makes this independence structural.
2. **Enforcement is code, not a documented manual command.**
3. **The mechanism is a periodic task INSIDE the application** — no Windows Task
   Scheduler, no cron on MS-S1. A host scheduler is a host-state change (CLAUDE.md
   §8), lives outside the repo, and does not follow a redeploy; an in-app task
   ships with the image.
4. **Build the mechanism BEFORE the RoPA text is written.** This PLAN's
   completion is a precondition of PLAN-0103 AC-11, not a follow-up to it.
5. **This PLAN authors no RoPA text.** The RoPA is Cray's artifact in the
   controller's voice (PLAN-0103 AC-11's authorship boundary, `0103:549-551`).
   This PLAN supplies the mechanism the RoPA will describe.

### The data to be deleted — verified on disk 2026-08-14

**The row.** `RepairCase` (`services/db/repair_case.py:57`,
`__tablename__ = "repair_case"` `:73`): `case_id` PK Text (`:79`), `opened_at`
tz-aware DateTime (`:82`), nullable `description` Text (`:85`) — the visitor's
free text — and `photos` JSONB (`:90-92`) whose **bytes live on disk**
(class docstring `:60-64`): the JSONB carries only metadata including a
**relative `stored_path`**.

**The disk footprint.** `_store_upload` (`services/api/routers/cases.py:137-180`)
is *"shared by the case-photo and quote-attachment routes"* (`:142`) and writes
every upload under `photo_root() / <case_id> / <upload_id><suffix>` (`:149-150`;
`photo_root()` `:111-114` resolves `settings.repair_case_photo_dir`, default
`var/repair-case-photos`, `services/api/config.py:432-439`). So the per-case
directory `photo_root()/<case_id>/` is the complete disk footprint of a case —
photos **and** quote attachments (`RepairCaseQuote.attachment` is *"the same
shape a case photo"* uses, `services/db/repair_case_evidence.py:76`, `:120`).

**🔴 The reference graph is TWO-SHAPED — the central design fact.**

*Shape 1 — six children hold a real ForeignKey to `repair_case.case_id`, and not
one declares `ondelete`* (grep for `ondelete` across `services/db/`: **zero**
matches):

| Table | FK site |
|---|---|
| `repair_case_order_number` (FK **at the primary key**) | `services/db/repair_case_closeout.py:86-88` |
| `repair_case_closeout` | `services/db/repair_case_closeout.py:114-115` |
| `repair_case_task_event` | `services/db/repair_case_task.py:70` |
| `repair_case_quote` (`__tablename__` `:85`) | `services/db/repair_case_evidence.py:104` |
| `repair_case_justification` (`__tablename__` `:139`) | `services/db/repair_case_evidence.py:150` |
| `repair_case_accepted_quote` (`__tablename__` `:202`) | `services/db/repair_case_evidence.py:250` |

→ a bare `DELETE FROM repair_case` **raises ForeignKeyViolation**; nothing
cascades. This failure is **loud**.

*Shape 2 — a seventh table references `case_id` with NO ForeignKey, deliberately:*
`RepairCaseRunLink` (`services/db/repair_case_run_link.py:60`,
`__tablename__` `:84`) holds `case_id` as plain `sa.Text` (`:109`) with an index
(`:86`). Its docstring records the measurement (s191, `:75-78`): with a `case_id`
FK in place, existing ratification tests drove the post-gate hook into
`ForeignKeyViolation` — the FK was dropped **on purpose**, and *"a missing
referent degrades the export rather than the gate"* (`:80-81`).

→ deleting a case leaves run-link rows behind **silently** — no error, no
cascade, nothing reddens. The two shapes fail in **opposite directions**, and a
review that walks backwards from FK declarations finds the six and misses the
seventh. The deletion design below classifies **every** `case_id`-bearing table
explicitly, and AC-5's guard makes an unclassified eighth table a test failure,
not a silent orphan (forward enumeration; `tools/excision_scope.py` exists for
exactly this class of walk, and the `excision-scope` skill records why a linter
cannot close it).

**The age anchor — the row analogue of name-not-mtime.** The sweep computes
expiry against `opened_at` (`repair_case.py:82`): written once by the
application at case creation, carried *inside* the row, never updated by any code
path, and preserved byte-for-byte by a dump/restore. It is the row-side analogue
of `_file_date` reading the file name: a DB restore, a volume remount, or a
re-import cannot silently resurrect an expired case's clock the way an
mtime-anchored rule would. (A backwards wall-clock step — a measured hazard on
this hardware — only *delays* deletion until the clock recovers; it can never
over-delete, because the cutoff moves earlier, not later.)

**Where the task hangs.** `lifespan` (`services/api/main.py:393`, wired `:523`)
sits **exactly at the C901 complexity ceiling (10)** — stated at `:259-262` and
`:454-455`. Adding an `if` inside it reddens ruff. The established escape is an
extracted helper that gates itself internally: `_seed_fleet_operate_demo`
(`:245`), called **unconditionally** at `:457`, branching inside on
`vertical == "fleet_maintenance"` plus a settings flag (`:269`) — and its
docstring says the next per-vertical boot hook *"has to take the same shape or it
will redden the same rule"* (`:262`). This PLAN takes that shape.

**Which system.** Fleet is the only DB-granted published profile
(`_DB_GRANTED = {"oct-fleet-maintenance"}`,
`tests/deploy/test_published_profiles.py:406`, asserted both directions by
`test_only_a_granted_profile_declares_a_database` `:410`, `:420`, `:471`).
Energy and procurement are DB-less; the task must be **inert there by
construction** — the same double gate (vertical + default-OFF env flag) that
makes the fleet seed a no-op everywhere else, not an accident of an unreachable
database.

**One RAM consequence the fact-pack implies.** `case_projection` is an in-memory
view refreshed from the DB (`services/api/routers/cases.py:105-108`;
boot load `main.py:487-505`). A sweep that deletes rows but never refreshes the
projection leaves the deleted case's text **serving from memory** until the next
case write — a retention leak in RAM. The sweep therefore triggers a projection
refresh after any deletion, under the same fail-soft contract the router uses.

## Goal

Ship a periodic, in-application retention task for fleet's published system that
deletes visitor-opened repair-case data — the `repair_case` row, its six
FK-child rows, and the per-case upload directory on disk — 90 days after
`opened_at`, with the seventh (no-FK) table and every future `case_id`-bearing
table explicitly classified rather than silently orphaned; enabled only on the
fleet published profile (default OFF everywhere), fail-soft (retention failing
never takes the demo down), and evidenced by a scenario test that drives a real
case through the real route, really ages it, really sweeps it, and inspects the
real seven-table + disk aftermath — so that PLAN-0103 AC-11's RoPA can state a
retention number that names a shipped control, not a promise.

## Acceptance Criteria

Every AC names the evidence that closes it. None is satisfiable by mocking the
seam under test. ⚠️ The DB-backed modules in this suite **skip when Postgres is
unreachable** — a **skip is never satisfaction**; each DB-backed AC below closes
only on a run where the test *executed* (CI provisions Postgres; locally, dev
Postgres on port 5442).

- [ ] **AC-1 — the sweep exists and is age-correct.**
  `services/db/repair_case_retention.py` deletes cases with
  `opened_at < now − CASE_RETENTION_DAYS`, anchored to `opened_at` (write-once,
  restore-proof — see Context). Evidence: a DB-backed boundary test in the shape
  of the prompt log's (`docs/runbooks/published-demo-operations.md:60` cites the
  89/91-day boundary in `tests/api/test_prompt_log.py`): an 89-day case
  survives, a 91-day case is deleted, asserted against real Postgres rows.
- [ ] **AC-2 — the six FK children are handled per the SD-1 ruling.** After a
  sweep, zero rows reference the expired case in each of
  `repair_case_order_number`, `repair_case_closeout`, `repair_case_task_event`,
  `repair_case_quote`, `repair_case_justification`, and
  `repair_case_accepted_quote` — asserted **per table by name** against the real
  DB, not via a rowcount aggregate that could pass with one table forgotten.
  Evidence: the Step-6 aftermath assertions, RED-proven by the Step-6 probe.
- [ ] **AC-3 — the seventh table's fate is explicit, per the SD-4 ruling.** The
  scenario aftermath asserts `repair_case_run_link` rows for the deleted case
  are in the SD-4-ruled state (retained-by-design or deleted), **by name**, with
  the ruling cited in the assertion's comment. Absence of any assertion about
  `repair_case_run_link` is a review-rejectable defect — its silent-orphan
  behaviour is the reason this PLAN's deletion design exists.
- [ ] **AC-4 — photo bytes are deleted per the SD-2 ruling, and partial failure
  is safe.** After a sweep, `photo_root()/<case_id>/` is gone (photos AND quote
  attachments). Under an injected disk-removal failure, the SD-2-ruled ordering
  guarantees the case **row survives the sweep pass** and is retried next pass —
  the "unreachable AND undeleted" state (row gone, file stranded) is
  unconstructible. Evidence: the scenario's disk assertion plus a
  fault-injection test that makes directory removal raise and asserts the row
  remains and a subsequent sweep completes the deletion.
- [ ] **AC-5 — the eighth table cannot be silent.** A completeness guard test
  walks the live SQLAlchemy metadata and asserts: (i) the set of tables holding
  an FK to `repair_case.case_id` **equals** the sweep's declared FK-child list;
  (ii) every mapped table with a column named `case_id` is classified in exactly
  one of the sweep's three declared sets — FK-children, no-FK-referencers (with
  an explicit per-table policy), or `repair_case` itself. A new `case_id`-bearing
  table reddens this test until a human classifies it. Evidence: the guard test
  green on `main`, and its Step-4 non-vacuity probe seen RED.
- [ ] **AC-6 — the task is periodic, in-app, and boot-anchored.** A task started
  from `lifespan` runs one sweep at startup and then on a fixed interval (24 h),
  so retention follows every redeploy with no host scheduler (LOCKED-3) and a
  box that restarts more often than the interval still enforces. The sweep
  **never raises** into the app (the `rotate()` contract,
  `prompt_log.py:59-78`): per-case failures are logged and retried next pass.
  Evidence: a lifecycle test asserting start/stop and the boot sweep; the
  fail-soft test of AC-4.
- [ ] **AC-7 — C901 is respected, not fought.** `lifespan` gains **no branch**:
  the task is started/stopped via helper(s) called unconditionally, with both
  gates (vertical + flag) inside the helper — the `_seed_fleet_operate_demo`
  shape (`main.py:245`, `:269`, `:457`). Evidence: `ruff check .` clean (C901
  included) over the touched files, plus the call-site diff in review.
- [ ] **AC-8 — inert by construction off fleet.** With the flag unset (the
  default) or the vertical ≠ `fleet_maintenance`, the helper returns before
  creating any task — dev, CI, energy, procurement, and pilot deployments are
  untouched unless a profile opts in. The fleet published profile sets the flag;
  a both-directions deploy guard (the `_DB_GRANTED` pattern,
  `test_published_profiles.py:406-420`) asserts fleet's compose sets it and the
  DB-less profiles do not. Evidence: the gating unit tests (both directions) +
  the deploy guard, RED-proven per Step 5's probe.
- [ ] **AC-9 — the 90 is structurally independent of ADR-0035 D6 (LOCKED-1).**
  `repair_case_retention.py` defines its **own** `CASE_RETENTION_DAYS = 90` with
  a comment citing LOCKED-1 (independent decision, coincidental number), and a
  guard test asserts the module does **not** import from
  `services.engine.llm.prompt_log` — so a future D6 change cannot silently
  change case retention, and vice versa. Evidence: the guard test + the comment
  in review.
- [ ] **AC-10 — the scenario test (CLAUDE.md §8 — binding).** A DB-backed
  scenario drives the **real producer into the real consumer on realistic
  simulated data**: a case opened through the real `POST /api/cases` route with
  typed Thai/English free text, a real photo upload and a real quote attachment
  through their routes, the case driven into a governed run so real
  `repair_case_run_link` rows exist (donor:
  `tests/api/test_visitor_case_to_monitor_scenario.py`), then **really aged**
  past the cutoff (an `UPDATE` of `opened_at` — aging the *data's timeline*, not
  stubbing the seam), then swept **via the same callable the periodic task
  invokes** — and the aftermath inspected, not assumed: row gone, six child
  tables empty for that case (per-table), run-link in its SD-4 state, per-case
  disk directory gone, the in-memory `case_projection` no longer serving the
  case, and a fresh control case + its files fully intact. No mock on either
  side of the sweep→DB or sweep→disk seam. Evidence: the test green **executed**
  (not skipped) in CI, RED-proven per Step 6's probe.
- [ ] **AC-11 — full gates.** Full `tests/` green (dispatch-recorded baseline on
  `main` = `1d7903c`: 4067 passed / 8 skipped — re-verify at execution),
  `mypy --strict services/` clean, `ruff check .` + format clean. Evidence: the
  PR's CI run + the pre-PR offline gate at CI scope.

## Out of Scope

- ❌ **Any RoPA text.** LOCKED-5: the RoPA (retention cell included) is Cray's
  artifact under PLAN-0103 AC-11's authorship boundary. This PLAN's closeout
  hands Cray the mechanism description as *input*, nothing more.
- ❌ **The DSR-on-request path** (`ropa-change-statement-fleet.md` §3's second
  gap, *"undefined for case rows"*). Deliberately separate: it needs its own
  ruling on identification/verification of the requester. The sweep's per-case
  deletion unit is factored so a future DSR path can call it for one named case,
  but building that path is not this PLAN.
- ❌ **Fleet's live bring-up or any redeploy.** PLAN-0103 Step 10's gated go.
  Nothing here touches the host (see §Host-state).
- ❌ **Any change to the prompt-log regime** (ADR-0035 D6) or to energy's /
  procurement's DB-less posture.
- ❌ **Editing PLAN-0103.** The ordering relationship is stated here (§Ordering);
  0103 is not reopened.
- ❌ **Retention for operator/pilot deployments' business data.** The flag is
  default-OFF precisely so a pilot's cases are never deleted by an engine
  default; a pilot retention regime is that engagement's decision.

## Surfaced decisions — Cray's slots. Recommendations only; no Step assumes an answer.

### SD-1 — cascade or ordered delete?

**(a) `ondelete="CASCADE"` on the six FKs.** Real costs, priced honestly: an
alembic migration — feasible here, the family already has hand-written ones
(`alembic/versions/0013_repair_case.py`, `0016_repair_case_task_chain.py`,
`0025_task_event_seq.py`, registered via `alembic/env.py:23-34`), and it must be
hand-written (autogenerate is unreliable on this repo's constructs — measured:
`alembic check` sees `Identity` but not `server_default`). Subtler cost:
CASCADE changes semantics for **every** deleter forever — today a stray
`DELETE FROM repair_case` from any future code path fails **loudly** on
ForeignKeyViolation, and that fail-closed shape is itself a safety property;
CASCADE trades it away globally so that one function can be terser. And CASCADE
buys less than it appears to: it cannot touch the run-link (no FK), the disk
directory, or the projection refresh — the application-side sweep exists under
(a) anyway, just with fewer statements in it.

**(b) explicit child deletes in dependency order in application code.** No
migration; the current loud-by-default DB shape is preserved. Its honest cost is
rot: the day someone adds an eighth `case_id`-bearing table, an unmaintained
hand-list orphans it silently. **That rot is exactly what AC-5's metadata-walk
guard closes**: the FK-child list is asserted *equal* to the FKs the live
metadata declares, and any `case_id` column anywhere must be classified — the
eighth table reddens CI the day it is mapped, under (a) as much as under (b)
(a no-FK eighth table orphans under CASCADE too, so the guard is needed in both
worlds).

**Recommendation: (b).** With AC-5 in place, (b)'s only structural weakness is
guarded by construction, while (a) still needs most of the same application code
*plus* a migration *plus* a permanent global weakening of the accidental-delete
posture. (Not decided here; Step 1 carries both variants.)

### SD-2 — the photo bytes: deletion order and partial-failure semantics

The hazard, stated plainly: if the **row** goes first and the file unlink then
fails, the bytes are **unreachable AND undeleted** — no DSR search can find
them (nothing points at `stored_path` any more), and no retry can either,
because the sweep finds expired cases *by row*. That is strictly worse than
either failure alone.

**(a) Files first, then rows — recommended.** Per expired case, one unit of
work: remove `photo_root()/<case_id>/` (the complete disk footprint — photos
and quote attachments, `cases.py:142`, `:149-150`); only if the directory is
verifiably gone, delete the child rows and the case row in one transaction. A
partial failure leaves: **row intact, some files gone** — still discoverable
(the row still names every `stored_path`), logged, retried next pass (the
`rotate()` retry contract). The bad state is unconstructible.
**(b) Rows first, then files.** Rejected above — constructs the worst state.
**(c) ELIMINATE the input: disable photo/attachment upload on the published
profile.** Then row deletion alone suffices on the published box. Priced: it is
the strongest *data-minimization* answer and this dispatch explicitly permits
elimination — but it removes the roadside photo-first flow that is Tab I's
demonstrated product story (`repair_case.py:84` — the truck pick is the only
required input *because* a photo may be everything), and quote attachments are
the evidence pack's substance. It trades the demo's point for a smaller cleanup.
**Recommendation: (a)**, with (c) noted as the fallback if Cray ever wants the
published surface text-only.

### SD-3 — is a still-OPEN case deleted at 90 days? And the audit chain's pointer?

Two sub-questions, one recommendation each — **neither ruled here**:

**Status exemption: recommend NO exemption — age governs, status does not.**
This is measured, not assumed: `CASE_STATUS_CLOSED` is defined
(`services/db/repair_case.py:43-44`) and has **zero referencers anywhere in
`services/`** (grep, 2026-08-14) — no route or code path sets a case to
`closed` today, and `status` defaults to `open` (`:86`). Every case, visitor or
operator, currently stays `open` forever; an OPEN-case exemption therefore
exempts **every** row the retention regime exists for — the promise goes
vacuous on exactly its motivating surface. Alternatives priced: exempt-OPEN
(vacuous, above); auto-close-then-delete after a grace period (invents workflow
state no partner asked for, and the auto-close event would be a synthetic fact
in an evidence-bearing system).

**The audit chain's dangling pointer: recommend stating it as the intended
design, because it is measured, not hoped.** The chain holds `case_id` while
the erasable text lives in the row — s222, PR #1124,
`tests/api/test_visitor_case_to_monitor_scenario.py`: visitor text absent from
**every** `audit_log` row on both the ordinary and waiver→ratify paths, with a
positively-controlled sentinel and a structural key allowlist; `case_id` stays
recoverable. Deleting the row makes the chain point at nothing **by design** —
this is the separation the new RoPA's erasure promise will rest on
(`ropa-change-statement-fleet.md` §5.2: shape 1 is *"the measured actual
behaviour"*). The PLAN's job is to make that deliberate and stated; Cray's job
is to ratify that reading or exempt chain-referenced cases (which would tie
retention to run participation — priced as: it re-couples the two things the
s222 measurement deliberately separated).

### SD-4 — the seventh table's fate (drafter-added slot; same discipline)

The run-link is outside both SD-1 options by construction — no FK, so neither
CASCADE nor FK-ordered deletion touches it. Its fate needs its own ruling:

**(a) Deliberately RETAIN run-link rows — recommended.** Verified against every
column (`repair_case_run_link.py:108-142`): `link_id`, `case_id`, `run_id`,
`step_id`, `outcome`, `three_quote_basis` (gate-derived, one of four bases or
NULL — `:128-131`), `linked_at`, `seq`. **No visitor free text rides this
table.** It is a decision record — the same class as the audit chain: `case_id`
as pointer, erasable text elsewhere. And the system already *measured* this
exact state as acceptable: the module docstring records that demo-fixture cases
were never inserted at all, yet their link rows are real decisions the export
must show (`:71-78`), and *"a missing referent degrades the export rather than
the gate"* (`:80-81`). Retention deleting a case simply moves it into the
already-designed degrade mode. Deleting the links instead would silently shrink
month-end KPI/export history — the double-count constraint (`:88-101`) exists
because those counts matter.
**(b) Delete run-link rows for hygiene.** Priced: buys a cleaner table at the
cost of erasing governance-decision history that carries no personal visitor
data — the one category the erasure argument does *not* require deleting.

Whichever way Cray rules, AC-3 and AC-5(ii) force the choice to be **written
down** in the sweep's no-FK policy set and asserted in the scenario aftermath.

## Steps

> Execution notes binding all steps: feature branch + PR (CLAUDE.md §7); every
> guard's non-vacuity probe is **run from a `/tmp` copy of the mutated file, the
> RED is seen and recorded in the PR evidence, and the original restored** —
> a probe whose RED was not witnessed proves nothing. No step assumes an SD
> answer: Step 0 collects the rulings first.

### Step 0: Collect the four SD rulings

Present SD-1..SD-4 to Cray; record the typed rulings in this file (a one-line
`RULED (Cray, typed, date):` under each SD). Steps 1–6 name which ruling they
consume. **Stop condition:** no ruling, no Step 1.

### Step 1: The sweep module — `services/db/repair_case_retention.py`

- `CASE_RETENTION_DAYS = 90`, own constant, LOCKED-1 comment (AC-9); no import
  from `prompt_log`.
- Three **declared, module-level** classification sets (AC-5 reads these):
  `FK_CHILD_TABLES` (the six), `NO_FK_REFERENCERS` (`repair_case_run_link` →
  the SD-4-ruled policy), and the root table.
- `sweep(session, *, now, photo_root) -> RetentionReport`: select expired
  `case_id`s by `opened_at`; per case, one unit of work in the SD-2-ruled
  order; children handled per the SD-1 ruling — **variant (b):** explicit
  deletes in dependency order (children before parent; `repair_case_order_number`
  and `repair_case_closeout` before `repair_case`, etc.); **variant (a):** an
  alembic migration `00XX` adds `ondelete="CASCADE"` to the six FKs (hand-written
  — autogenerate untrusted here) and the sweep deletes the parent row only —
  disk + run-link policy + projection refresh remain in code under both.
- Never raises out of a case: per-case failures land in the report and the log,
  retried next pass (`rotate()` contract). Tenant-agnostic by design (age
  governs; the published box is single-tenant `TENANT_ID=demo`).
- After any pass that deleted ≥1 case: `case_projection.refresh` under the
  router's fail-soft contract (`cases.py:105-108`) so deleted text stops being
  served from memory.
- Unit tests (DB-backed): the AC-1 89/91 boundary; the AC-4 fault injection
  (monkeypatch the directory-removal call at the OS boundary **below** the seam
  under test — the seam being the sweep's ordering + error handling — assert
  row survives, next sweep completes).
- The AC-9 independence guard (module imports nothing from
  `services.engine.llm.prompt_log`), reading the module's real import table, not
  a string constant of its own. **Non-vacuity probe:** from a `/tmp` copy, add
  `from services.engine.llm.prompt_log import RETENTION_DAYS` to the retention
  module → guard RED; restore.

### Step 2: The task runner — `services/api/case_retention_task.py`

- `start_case_retention(vertical) -> handle | None` / `stop_case_retention(handle)`:
  both gates **inside** (`vertical == "fleet_maintenance"` and
  `settings.case_retention_enabled`, a new default-`False` field beside
  `oct_demo_seed_operate`, `config.py:402`); returns `None` when inert.
- The loop: one sweep immediately at start (boot-anchored — retention follows
  every redeploy, LOCKED-3's rationale), then every `CASE_RETENTION_SWEEP_HOURS
  = 24`; each iteration fail-soft-logged, DB-unreachable included (the DB-less
  boot contract, `main.py:460-463`).
- Unit tests: inert when flag off; inert when vertical ≠ fleet; started when
  both true; stop cancels cleanly; boot sweep observed via the report.

### Step 3: Wire into `lifespan` — zero added branches

Two unconditional statements in `lifespan` (`main.py:393`): start before
`yield`, stop after — the `_seed_fleet_operate_demo` call shape (`:457`).
**Evidence for AC-7:** ruff clean (C901 unchanged at ≤10) + the call-site diff.
If ruff reddens anyway, the fix is in the helper, never a branch in `lifespan`.

### Step 4: The completeness guard (AC-5)

`tests/db/test_case_retention_completeness.py`: metadata walk per AC-5(i)+(ii)
against the live `Base.metadata` (the guard reads the **artifact** — the
declared sets in the sweep module — against the metadata, not its own copy of
either). **Non-vacuity probe:** from a `/tmp` copy, drop one table from
`FK_CHILD_TABLES` → guard RED; separately, simulate the eighth table (a scratch
mapped class with a `case_id` column in the test's own module — the measured
G2-style trick of embedding the fixture in the test module) → guard RED until
classified; restore.

### Step 5: Arm the fleet published profile (repo files only)

Set the env flag in `deploy/published/oct-fleet-maintenance/`'s compose; extend
`tests/deploy/test_published_profiles.py` with the both-directions assertion
(fleet sets it; energy + procurement do not — the `_DB_GRANTED` pattern `:406-420`).
**Non-vacuity probe:** from a `/tmp` copy, unset the flag in fleet's compose →
RED; set it in energy's → RED; restore.

### Step 6: The scenario test (AC-10 — CLAUDE.md §8)

`tests/api/test_case_retention_scenario.py`, donor
`tests/api/test_visitor_case_to_monitor_scenario.py` for the case→run drive:
real route in (case + photo + quote attachment), real run (so run-link rows
exist), real `UPDATE` aging, sweep via the **task's own callable**, then the
full aftermath per AC-10 — per-table child checks, run-link per SD-4, disk gone,
projection refreshed, control case intact. DB-backed; skips honestly when
Postgres is unreachable and **counts only when executed**.
**Non-vacuity probe:** from a `/tmp` copy of the sweep module, sever the disk-
removal call → the disk-aftermath assertion RED (and only it — the probe's
mutation names the exact output it changes); restore. Second probe: sever one
child-table delete → that table's AC-2 assertion RED; restore.

### Step 7: Gates + closeout

Full offline gate at CI scope (full `tests/`, `mypy --strict services/`, bare
`ruff check .`, format), PR, merge. Closeout note to Cray: the mechanism PLAN-0103
AC-11's retention cell will describe now exists — naming module paths, the
constant, the schedule, and the SD rulings as ratified — **as input for the RoPA,
not as RoPA text** (LOCKED-4/-5). Then `git mv` to `docs/plans/done/`.

## Host-state statement (CLAUDE.md §8)

**No step is a host-state action.** Steps 1–6 are worktree code + tests; Step 5
edits *repo* compose files only — it changes what the next bring-up ships, and
the bring-up itself stays PLAN-0103 Step 10's separately-gated go. No cron, no
Task Scheduler, no MS-S1 touch, no live redeploy. That is LOCKED-3 rendered: the
control ships with the image.

## Ordering — PLAN-0103 AC-11

This PLAN **precedes** AC-11's closure (LOCKED-4: build first). The chain:
PLAN-0105 merges → the RoPA's retention cell can name a shipped control
(`docs/compliance/ropa-change-statement-fleet.md` §3's *"no number exists yet"*
closes) → Cray authors the RoPA (AC-11, authorship boundary intact) → fleet's
Step-10 go cites it. PLAN-0103 is not edited by this PLAN.

## Verification

- All 11 ACs checked, each against its named evidence; DB-backed tests
  **executed**, not skipped (CI provisions Postgres).
- Every probe's RED witnessed and recorded in the PR evidence file
  (per-commit evidence discipline).
- Offline gate at CI scope before the PR; baseline drift from
  4067 passed / 8 skipped re-verified at execution time, not assumed.

---

*Drafted by the in-harness `plan-drafter` subagent (ADR-013 D1 phased authority)
from a Cray-ratified dispatch, 2026-08-14. Author≠reviewer (ADR-012 D4.3):
drafter = plan-drafter; independent review = Code + Cray at PR merge; separation
intact. Every `file:line` claim re-verified on disk at drafting time against
`main` = `1d7903c`. AI-assisted; no `Co-Authored-By` per CLAUDE.md §7.*
