# PLAN-0105: Fleet repair-case retention — in-app periodic deletion of visitor-opened case data at 90 days

**Status:** Complete (2026-08-14)
**Owner:** Claude Code
**Created:** 2026-08-14
**Related ADRs:** ADR-0035 (published-demo posture; D6 prompt-log regime — explicitly NOT inherited, see LOCKED-1), ADR-0037 (fleet compliance direction; D2.1/D4)
**Related PLANs:** PLAN-0096 (case capture), PLAN-0100 (published demo), PLAN-0103 (AC-11 — this PLAN is a *precondition* of its closure, see §Ordering)

> **Rulings round (2026-08-14, post-merge `0ea641b` / PR #1160, same drafter):**
> Cray ruled all four SD slots (typed, 2026-08-14), adopting each
> recommendation: SD-1 → (b) ordered app-level child deletes + the AC-5 guard;
> SD-2 → (a) files first, then rows; SD-3 → no status exemption AND the
> dangling `case_id` pointer stated as intended design; SD-4 → (a) run-link
> rows deliberately retained. This round stamps the verdicts into the SD slots,
> collapses Step 1's dual variant to the ruled (b) shape, fixes AC-2/AC-3/AC-4
> and every conditional phrasing to the ruled outcomes, and records Step 0 as
> satisfied. Every recommendation's reasoning is preserved verbatim as the
> auditable record of *why*. The eleven ACs stand — none added, removed, or
> renumbered; `Status:` stays Draft until Complete. Author≠reviewer separation:
> **INTACT** (drafter = `plan-drafter`; review = Code — PR #1160's review
> verified four load-bearing claims on disk, all held; ratification = Cray).

> **Closeout round (2026-08-14, post-merge `6f7c547` / PR #1166, same drafter —
> the PLAN-0103 precedent):** All six build steps shipped and merged
> (PRs #1162–#1166, per-step record under Step 7). Every AC is ticked below
> against its named evidence, each item verified by Code on `main` = `6f7c547`;
> the closure stamps under the ACs cite the tests and probes by name. This round
> also records the one defect the build surfaced — Step 6's deletion-order
> ForeignKeyViolation, stamped under AC-2 and classified **`was an error`**
> (§6 verify-loop hygiene: wrong on disk from the moment Step 1 shipped, not
> overtaken by events) — plus Step 5's executed-as-corrected deviation
> (`published.env`, not compose) and the honest scope of probe P14. Step 7
> carries the closeout note to Cray: **input for the RoPA, never RoPA text**
> (LOCKED-4/-5). `Status:` → Complete. Author≠reviewer separation: **INTACT**
> (drafter = `plan-drafter`, the same subagent as both earlier rounds;
> independent review of this closeout diff = Code at the PR; ratification =
> Cray).

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
`opened_at`, with the seventh (no-FK) table deliberately retained as a decision
record (SD-4 ruling) and every future `case_id`-bearing table explicitly
classified rather than silently orphaned; enabled only on the
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

- [x] **AC-1 — the sweep exists and is age-correct.**
  `services/db/repair_case_retention.py` deletes cases with
  `opened_at < now − CASE_RETENTION_DAYS`, anchored to `opened_at` (write-once,
  restore-proof — see Context). Evidence: a DB-backed boundary test in the shape
  of the prompt log's (`docs/runbooks/published-demo-operations.md:60` cites the
  89/91-day boundary in `tests/api/test_prompt_log.py`): an 89-day case
  survives, a 91-day case is deleted, asserted against real Postgres rows.
  _✅ Closed (2026-08-14, verified by Code on `main` = `6f7c547`):
  `tests/services/db/test_case_retention.py::test_ac1_the_boundary_is_the_cutoff_not_a_neighbourhood`
  — 89-day case survives, 91-day case deleted, against real Postgres. Probe P2
  (drop the `opened_at < cutoff` filter) seen RED with `assert 2 == 1`._
- [x] **AC-2 — the six FK children are deleted by ordered application-level
  deletes (SD-1 ruling: (b) — no CASCADE, no migration).** After a sweep, zero
  rows reference the expired case in each of
  `repair_case_order_number`, `repair_case_closeout`, `repair_case_task_event`,
  `repair_case_quote`, `repair_case_justification`, and
  `repair_case_accepted_quote` — asserted **per table by name** against the real
  DB, not via a rowcount aggregate that could pass with one table forgotten.
  Evidence: the Step-6 aftermath assertions, RED-proven by the Step-6 probe.
  _✅ Closed (2026-08-14): the six children asserted per table BY NAME by
  `tests/api/test_case_retention_scenario.py`'s `_CHILD_TABLES` loop, plus
  `tests/services/db/test_case_retention.py::test_the_fk_children_go_and_the_run_link_is_deliberately_left_standing`.
  Closed **with the correction below** — this AC's evidence is the part of the
  record that changed most between Step 1 and merge._
  _🔴 **Correction (found by Step 6; classified `was an error` — §6 verify-loop
  hygiene: it was wrong on disk from the moment Step 1 shipped, not overtaken by
  events).** `repair_case_accepted_quote` holds a **composite FK to
  `repair_case_quote`** (`tenant_id, case_id, quote_id`) in addition to its FK
  to the root. Step 1's declared order deleted the quote FIRST, so the sweep
  raised `ForeignKeyViolation` on any case that had ever accepted a quote —
  every case that reached a gate. The fail-soft caught it, so the case was
  reported failed and retried forever: **retention would silently never complete
  on real data while every unit test stayed green.** Neither existing guard
  could see it: Step 1's unit test inserted a task event and no quote pack, and
  AC-5 as written checks MEMBERSHIP, not ORDER. The Step-6 scenario failed on
  the first realistic case. Fixed by reordering `_FK_CHILD_MODELS` — measured,
  not guessed: a walk over every FK edge in the family found exactly ONE
  child-to-child dependency. Guarded by
  `test_the_declared_order_respects_every_child_to_child_dependency`, which
  walks the child-to-child edges off the live metadata;
  `FK_CHILD_DELETION_ORDER` is exported as an ordered tuple beside the frozenset
  because a set cannot carry the property being checked. Probe P12 reddens BOTH
  the order guard and the scenario from one mutation. The order guard is an
  **addition beyond AC-5's wording**, not something that AC always demanded —
  see AC-5's stamp and Step 7's record (probe P14's honest scope)._
- [x] **AC-3 — the seventh table is deliberately RETAINED (SD-4 ruling), and
  the retention is asserted positively.** The scenario aftermath asserts
  `repair_case_run_link` rows for the deleted case are **still present and
  unchanged** — retained-by-design — **by name**, with SD-4's ruling cited in
  the assertion's comment. "Retained" must be a positive presence assertion,
  never the mere absence of a delete: an absent assertion is indistinguishable
  from a forgotten table. Absence of any assertion about
  `repair_case_run_link` is a review-rejectable defect — its silent-orphan
  behaviour is the reason this PLAN's deletion design exists.
  _✅ Closed (2026-08-14): the run-link asserted as POSITIVE PRESENCE by name in
  both modules — the scenario's aftermath section ("asserted as PRESENCE (SD-4
  ruled (a))") and the Step-1 unit test — with SD-4 cited at the assertion.
  Probe P3 (add `RepairCaseRunLink` to the delete loop) seen RED with
  `assert [] == ['link-1']`._
- [x] **AC-4 — photo bytes are deleted files-FIRST, then rows (SD-2 ruling:
  (a)), and partial failure is safe.** After a sweep, `photo_root()/<case_id>/`
  is gone (photos AND quote attachments). Under an injected disk-removal
  failure, the files-first ordering guarantees the case **row survives the
  sweep pass** and is retried next pass —
  the "unreachable AND undeleted" state (row gone, file stranded) is
  unconstructible. Evidence: the scenario's disk assertion plus a
  fault-injection test that makes directory removal raise and asserts the row
  remains and a subsequent sweep completes the deletion.
  _✅ Closed (2026-08-14): the scenario's disk assertion plus
  `tests/services/db/test_case_retention.py::test_ac4_a_failed_unlink_leaves_the_row_and_the_next_pass_finishes_the_job`
  (fault injected at the OS boundary below the seam). Probe P13 (sever the disk
  removal) seen RED at "the case's upload directory must be gone"._
- [x] **AC-5 — the eighth table cannot be silent.** A completeness guard test
  walks the live SQLAlchemy metadata and asserts: (i) the set of tables holding
  an FK to `repair_case.case_id` **equals** the sweep's declared FK-child list;
  (ii) every mapped table with a column named `case_id` is classified in exactly
  one of the sweep's three declared sets — FK-children, no-FK-referencers (with
  an explicit per-table policy), or `repair_case` itself. A new `case_id`-bearing
  table reddens this test until a human classifies it. Evidence: the guard test
  green on `main`, and its Step-4 non-vacuity probe seen RED.
  _✅ Closed (2026-08-14): `tests/services/db/test_case_retention_completeness.py`
  (landed under the suite's mirror of `services/db/`, not the `tests/db/` path
  Step 4 wrote — see Step 4's note), six tests: the not-vacuous floor, AC-5(i)
  equality, AC-5(ii) exactly-once with the three sets pairwise disjoint, the
  non-empty-policy check, the both-shapes eighth-table detector demonstration,
  and the Step-6 order guard (an ADDITION beyond this AC's wording — see AC-2's
  correction). Probes P7 (drop a declared FK child) and P8 (drop the run link
  from `NO_FK_REFERENCERS`) both seen RED. Measured before writing: of 21 mapped
  tables exactly 8 carry a `case_id` column, and no exemption was needed._
- [x] **AC-6 — the task is periodic, in-app, and boot-anchored.** A task started
  from `lifespan` runs one sweep at startup and then on a fixed interval (24 h),
  so retention follows every redeploy with no host scheduler (LOCKED-3) and a
  box that restarts more often than the interval still enforces. The sweep
  **never raises** into the app (the `rotate()` contract,
  `prompt_log.py:59-78`): per-case failures are logged and retried next pass.
  Evidence: a lifecycle test asserting start/stop and the boot sweep; the
  fail-soft test of AC-4.
  _✅ Closed (2026-08-14): `tests/api/test_case_retention_task.py` — the boot
  sweep observed via an Event (not a sleep), and the loop surviving a raising
  sweep; stop cancels cleanly, and stop on a disarmed start is a no-op. Probe P5
  (narrow `except Exception` to `except ValueError`) seen RED._
- [x] **AC-7 — C901 is respected, not fought.** `lifespan` gains **no branch**:
  the task is started/stopped via helper(s) called unconditionally, with both
  gates (vertical + flag) inside the helper — the `_seed_fleet_operate_demo`
  shape (`main.py:245`, `:269`, `:457`). Evidence: `ruff check .` clean (C901
  included) over the touched files, plus the call-site diff in review.
  _✅ Closed (2026-08-14):
  `tests/api/test_case_retention_task.py::test_ac7_lifespan_gained_no_branch_for_retention`
  parses `lifespan`'s own source and requires both calls at statement level;
  `lifespan` gained exactly two unconditional statements (start before `yield`,
  stop after). Probe P6 (wrap the start call in an `if`) seen RED. `ruff check .`
  clean per AC-11._
- [x] **AC-8 — inert by construction off fleet.** With the flag unset (the
  default) or the vertical ≠ `fleet_maintenance`, the helper returns before
  creating any task — dev, CI, energy, procurement, and pilot deployments are
  untouched unless a profile opts in. The fleet published profile sets the flag;
  a both-directions deploy guard (the `_DB_GRANTED` pattern,
  `test_published_profiles.py:406-420`) asserts fleet's compose sets it and the
  DB-less profiles do not. Evidence: the gating unit tests (both directions) +
  the deploy guard, RED-proven per Step 5's probe.
  _✅ Closed (2026-08-14): inert by construction — both gates inside the helper,
  asserted for energy AND procurement (`test_ac8_*` in
  `tests/api/test_case_retention_task.py`), plus the deploy guard
  `test_published_profiles.py::test_only_the_armed_profile_enables_case_retention`.
  The flag landed in fleet's **`published.env`**, not compose — the AC's
  substance (the fleet published profile sets it, both directions guarded) is
  satisfied; "compose" was the PLAN's guess at the profile's mechanism — see
  Step 5's executed-as-corrected note. Probes P4 (remove the vertical gate),
  P9 (flip fleet to false), P10 (arm energy), P11 (arm energy with `=1`) all
  seen RED._
- [x] **AC-9 — the 90 is structurally independent of ADR-0035 D6 (LOCKED-1).**
  `repair_case_retention.py` defines its **own** `CASE_RETENTION_DAYS = 90` with
  a comment citing LOCKED-1 (independent decision, coincidental number), and a
  guard test asserts the module does **not** import from
  `services.engine.llm.prompt_log` — so a future D6 change cannot silently
  change case retention, and vice versa. Evidence: the guard test + the comment
  in review.
  _✅ Closed (2026-08-14):
  `tests/services/db/test_case_retention.py::test_ac9_the_module_does_not_inherit_the_prompt_log_regime`
  walks the module's REAL import table out of its source. Probe P1 seen RED with
  `assert not ['services.engine.llm.prompt_log']`._
- [x] **AC-10 — the scenario test (CLAUDE.md §8 — binding).** A DB-backed
  scenario drives the **real producer into the real consumer on realistic
  simulated data**: a case opened through the real `POST /api/cases` route with
  typed Thai/English free text, a real photo upload and a real quote attachment
  through their routes, the case driven into a governed run so real
  `repair_case_run_link` rows exist (donor:
  `tests/api/test_visitor_case_to_monitor_scenario.py`), then **really aged**
  past the cutoff (an `UPDATE` of `opened_at` — aging the *data's timeline*, not
  stubbing the seam), then swept **via the same callable the periodic task
  invokes** — and the aftermath inspected, not assumed: row gone, six child
  tables empty for that case (per-table), run-link rows still present (SD-4: retained), per-case
  disk directory gone, the in-memory `case_projection` no longer serving the
  case, and a fresh control case + its files fully intact. No mock on either
  side of the sweep→DB or sweep→disk seam. Evidence: the test green **executed**
  (not skipped) in CI, RED-proven per Step 6's probe.
  _✅ Closed (2026-08-14): `tests/api/test_case_retention_scenario.py`, three
  tests. 🔴 **Executed, not skipped — measured, not assumed**: a `-v` run of the
  scenario module plus Step 1's module reports **7 PASSED / 0 SKIPPED**. Real
  routes in (case + photo + three quotes with attachments + accepted quote +
  justification + task flip), a real run driven to a RESOLVED gate so run-link
  rows exist, real `UPDATE` aging, swept through `_sweep_once` — the task's own
  callable — and the aftermath inspected per table, on disk, and in the
  projection, with a control case intact. RED-proven per probes P12/P13; probe
  P14's honest scope recorded under Step 7._
- [x] **AC-11 — full gates.** Full `tests/` green (dispatch-recorded baseline on
  `main` = `1d7903c`: 4067 passed / 8 skipped — re-verify at execution),
  `mypy --strict services/` clean, `ruff check .` + format clean. Evidence: the
  PR's CI run + the pre-PR offline gate at CI scope.
  _✅ Closed (2026-08-14, verified by Code on `main` = `6f7c547`): full `tests/`
  **4091 passed / 8 skipped** (drift from the 4067 baseline re-verified, not
  assumed — the growth is this PLAN's own added tests); `mypy --strict
  services/` clean over **136** source files; `ruff check .` + `ruff format
  --check` clean on the **extracted HEAD tree** (`git archive HEAD`, 628 files)
  rather than the local checkout._

## Out of Scope

- ❌ **Any RoPA text.** LOCKED-5: the RoPA (retention cell included) is Cray's
  artifact under PLAN-0103 AC-11's authorship boundary. This PLAN's closeout
  hands Cray the mechanism description as *input*, nothing more.
- ❌ **The DSR-on-request path** (`ropa-change-statement-fleet.md` §3's second
  gap, *"undefined for case rows"*). Deliberately separate: it needs its own
  ruling on identification/verification of the requester. The sweep's per-case
  deletion unit is factored so a future DSR path can call it for one named case,
  but building that path is not this PLAN.
  _[Corrected s232, **`was an error`** — false on disk from the moment Step 1
  shipped, not overtaken by events. There was no callable per-case unit: the
  work was **inline in `sweep`'s loop body** and reachable from nowhere else,
  and `sweep` accepts no case identifier at all — it selects its work set by
  age. The claim was written as though the extraction had happened. **It has
  now:** `delete_case(session, case_id, *, photo_root)` exists in
  `services/db/repair_case_retention.py`, and this sentence is true of the tree
  as of s232 rather than being quietly deleted. ⚠️ **The unit rolls back its own
  partial work and re-raises** (Cray, typed, s232) so a DSR caller never
  inherits a session in a failed transaction — but it deliberately does **not**
  refresh the projection, which stays the caller's job. What is still genuinely
  undecided is unchanged and is the harder half: **requester identification has
  no in-repo answer**, because personas add no visitor identity (§4(b) of the
  change statement) — so "prove you own case X" is not merely unbuilt.]_
- ❌ **Fleet's live bring-up or any redeploy.** PLAN-0103 Step 10's gated go.
  Nothing here touches the host (see §Host-state).
- ❌ **Any change to the prompt-log regime** (ADR-0035 D6) or to energy's /
  procurement's DB-less posture.
- ❌ **Editing PLAN-0103.** The ordering relationship is stated here (§Ordering);
  0103 is not reopened.
- ❌ **Retention for operator/pilot deployments' business data.** The flag is
  default-OFF precisely so a pilot's cases are never deleted by an engine
  default; a pilot retention regime is that engagement's decision.

## Surfaced decisions — RULED (Cray, typed, 2026-08-14). The recommendations below are preserved verbatim as the auditable record of *why*; the stamps carry the verdicts.

### SD-1 — cascade or ordered delete?

🔴 **RULED (Cray, typed, 2026-08-14): (b) — ordered application-level child
deletes in dependency order, plus the AC-5 completeness guard. No migration;
the loud fail-closed DELETE posture is preserved.**

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
posture. (Recommendation adopted by the ruling above; Step 1 now carries the
ruled (b) shape, with (a) kept as a recorded alternative.)

### SD-2 — the photo bytes: deletion order and partial-failure semantics

🔴 **RULED (Cray, typed, 2026-08-14): (a) — files first, then rows, one unit
of work per expired case.**

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

🔴 **RULED (Cray, typed, 2026-08-14): no status exemption — age governs,
status does not — AND the audit chain's dangling `case_id` pointer is stated
as the intended design.**

Two sub-questions, one recommendation each — both ruled above; the reasoning
stands as the record:

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

_Review-round corroboration (Code's PR #1160 review; re-verified on disk at
fold-in, 2026-08-14): stronger than stated above — the literal `"closed"` is
never assigned to any status anywhere in `services/` (its only other
occurrences are the unrelated ontology closed-model flag), `CASE_STATUSES`
(`repair_case.py:44`) is itself unreferenced (nothing even validates against
it), and the API layer's only `.status =` write is PM import-row status
(`services/api/routers/pm.py:255`), not case status._

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

🔴 **RULED (Cray, typed, 2026-08-14): (a) — `repair_case_run_link` rows are
deliberately RETAINED.**

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

The ruling is **written down** in the sweep's no-FK policy set (Step 1:
`repair_case_run_link` → RETAIN) and **positively asserted** in the scenario
aftermath (AC-3, AC-5(ii)): retained is asserted as presence, never left
unasserted — an absent assertion is indistinguishable from a forgotten table,
the exact failure this slot exists to prevent.

## Steps

> Execution notes binding all steps: feature branch + PR (CLAUDE.md §7); every
> guard's non-vacuity probe is **run from a `/tmp` copy of the mutated file, the
> RED is seen and recorded in the PR evidence, and the original restored** —
> a probe whose RED was not witnessed proves nothing. All four SD rulings were
> collected before any build step (Step 0 — satisfied 2026-08-14); each step
> below names the ruling it consumes.

### Step 0: Collect the four SD rulings — ✅ SATISFIED 2026-08-14

Present SD-1..SD-4 to Cray; record the typed rulings in this file (a one-line
`RULED (Cray, typed, date):` under each SD). Steps 1–6 name which ruling they
consume. **Stop condition:** no ruling, no Step 1.

_Satisfied: all four rulings collected and stamped (Cray, typed, 2026-08-14 —
see the Surfaced-decisions section; rulings round, post-PR #1160). The stop
condition was honoured — no build step preceded the rulings. The step is kept,
not deleted: its record is the evidence the gate was._

### Step 1: The sweep module — `services/db/repair_case_retention.py`

- `CASE_RETENTION_DAYS = 90`, own constant, LOCKED-1 comment (AC-9); no import
  from `prompt_log`.
- Three **declared, module-level** classification sets (AC-5 reads these):
  `FK_CHILD_TABLES` (the six), `NO_FK_REFERENCERS` (`repair_case_run_link` →
  **RETAIN**, per SD-4's ruling), and the root table.
- `sweep(session, *, now, photo_root) -> RetentionReport`: select expired
  `case_id`s by `opened_at`; per case, one unit of work in SD-2's ruled order —
  **files first, then rows**; children handled per SD-1's ruled shape (b):
  **explicit deletes in dependency order** (children before parent; all six
  FK-child tables before `repair_case`; the row deletes in one transaction).
  _Recorded alternative, no longer executable: SD-1 (a) — `ondelete="CASCADE"`
  via a hand-written alembic migration (autogenerate untrusted here) — was
  rejected by the ruling; its honest pricing stands in SD-1's record. Disk +
  run-link policy + projection refresh would have remained in code under
  either option._
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

_As landed (PR #1164): the guard lives at
`tests/services/db/test_case_retention_completeness.py` — the suite's mirror of
`services/db/`, not the `tests/db/` path written above. Same guard, same probes;
plus the Step-6 order guard added beside it (see AC-2's correction)._

### Step 5: Arm the fleet published profile (repo files only)

Set the env flag in `deploy/published/oct-fleet-maintenance/`'s compose; extend
`tests/deploy/test_published_profiles.py` with the both-directions assertion
(fleet sets it; energy + procurement do not — the `_DB_GRANTED` pattern `:406-420`).
**Non-vacuity probe:** from a `/tmp` copy, unset the flag in fleet's compose →
RED; set it in energy's → RED; restore.

_**Executed as corrected** (PR #1165): the flag landed in fleet's
**`published.env`** (`CASE_RETENTION_ENABLED=true`), not the compose file —
`published.env` is where every non-secret setting lives as `KEY=value`
(the sibling `OCT_DEMO_SEED_OPERATE` included), while the compose
`environment:` block carries only bare pass-throughs for secrets. "Compose" was
this step's guess at the profile's mechanism, written before the profile was
read; the deviation discharges the drafter's own residual gap 2 ("fleet's
compose was not read"). The both-directions guard landed as
`test_only_the_armed_profile_enables_case_retention`; probes P9–P11 seen RED
per AC-8's stamp._

### Step 6: The scenario test (AC-10 — CLAUDE.md §8)

`tests/api/test_case_retention_scenario.py`, donor
`tests/api/test_visitor_case_to_monitor_scenario.py` for the case→run drive:
real route in (case + photo + quote attachment), real run (so run-link rows
exist), real `UPDATE` aging, sweep via the **task's own callable**, then the
full aftermath per AC-10 — per-table child checks, run-link rows asserted
present (SD-4: retained), disk gone, projection refreshed, control case intact. DB-backed; skips honestly when
Postgres is unreachable and **counts only when executed**.
**Non-vacuity probe:** from a `/tmp` copy of the sweep module, sever the disk-
removal call → the disk-aftermath assertion RED (and only it — the probe's
mutation names the exact output it changes); restore. Second probe: sever one
child-table delete → that table's AC-2 assertion RED; restore.

### Step 7: Gates + closeout — ✅ SATISFIED 2026-08-14

Full offline gate at CI scope (full `tests/`, `mypy --strict services/`, bare
`ruff check .`, format), PR, merge. Closeout note to Cray: the mechanism PLAN-0103
AC-11's retention cell will describe now exists — naming module paths, the
constant, the schedule, and the four SD rulings (Cray, typed, 2026-08-14) — **as
input for the RoPA, not as RoPA text** (LOCKED-4/-5). Then `git mv` to `docs/plans/done/`.

_Satisfied (2026-08-14): all six build steps shipped and merged; every AC ticked
above against its named evidence, verified by Code on `main` = `6f7c547`; gate
numbers per AC-11's stamp. The `git mv` to `docs/plans/done/` is Code's move
after this closeout round merges (`git add` before the move — a `git mv` of a
modified file drops the edit)._

#### What shipped, by step (all merged; final `main` = `6f7c547`)

| Step | PR | Landed |
|---|---|---|
| 1 | #1162 (`11a031c`) | `services/db/repair_case_retention.py` + `tests/services/db/test_case_retention.py` |
| 2+3 | #1163 (`7ebd7d7`) | `services/api/case_retention_task.py`, `settings.case_retention_enabled`, two unconditional statements in `lifespan`, `tests/api/test_case_retention_task.py` |
| 4 | #1164 (merge `311cd44`) | `tests/services/db/test_case_retention_completeness.py` |
| 5 | #1165 (merge `61e18ef`) | `CASE_RETENTION_ENABLED=true` in fleet's `published.env` + the both-directions deploy guard |
| 6 | #1166 (merge `6f7c547`) | `tests/api/test_case_retention_scenario.py`, the deletion-order fix (AC-2's correction), and the order guard |

#### What the record carries beyond the ticks

- **The defect Step 6 found** — the deletion-order `ForeignKeyViolation` on
  `repair_case_accepted_quote`'s composite FK, classified **`was an error`**:
  full record under AC-2's correction note. The build's one defect, caught
  exactly where the design said it would be — by the scenario on the first
  realistic case, after every unit test stayed green.
- **Step 5's deviation** — flag in `published.env`, not compose; executed as
  corrected: record under Step 5.
- **Probe P14, recorded honestly (no overclaim).** Skipping one child-table
  delete reddens the scenario at the REPORT assertion, not at that table's
  per-table assertion: with FKs and no CASCADE, a skipped child makes the
  PARENT delete fail, so silent partial deletion is impossible. The per-table
  assertions are therefore documentation plus the check that would become
  primary if SD-1 were ever re-ruled to (a) — P14 proved the report-level
  failure, not per-table reddening.

#### Closeout note to Cray — input for the RoPA, never RoPA text (LOCKED-4/-5)

The mechanism PLAN-0103 AC-11's retention cell will describe now exists. What
follows names it so Cray can describe the control without reading code; the
authorship boundary is the point — the RoPA's words are Cray's.

- **Where the control lives:** `services/db/repair_case_retention.py` (the
  sweep — selection, ordered deletion, disk removal, report) and
  `services/api/case_retention_task.py` (the periodic task that runs it).
- **The number:** `CASE_RETENTION_DAYS = 90` — the module's own constant,
  **independent of ADR-0035 D6** (LOCKED-1: coincidental number, separate
  decision). The independence is structural, not narrative: AC-9's guard
  reddens if the retention module ever imports from the prompt-log module.
- **The schedule:** one sweep at application boot, then every
  `CASE_RETENTION_SWEEP_HOURS = 24` hours, inside the application process — no
  cron, no Task Scheduler, nothing installed on the host. The control ships
  with the image and follows every redeploy (LOCKED-3).
- **What a sweep deletes**, for every case older than 90 days from `opened_at`:
  the `repair_case` row; its six FK-child rows (`repair_case_order_number`,
  `repair_case_closeout`, `repair_case_task_event`, `repair_case_quote`,
  `repair_case_justification`, `repair_case_accepted_quote`); and the per-case
  upload directory on disk — photos AND quote attachments. Files first, rows
  after (SD-2): a partial failure leaves a discoverable row retried next pass,
  never a stranded unreachable file.
- **What is deliberately RETAINED:** `repair_case_run_link` (SD-4) —
  governance-decision records carrying no visitor free text (`case_id` as
  pointer; the erasable text lived in the row now deleted). Deleting them would
  erase KPI/export history the erasure argument does not require; a deleted
  case's link degrades the export exactly the already-measured way (s191:
  "a missing referent degrades the export rather than the gate").
- **The arming:** `CASE_RETENTION_ENABLED`, default `False` everywhere — dev,
  CI, energy, procurement, and pilot deployments untouched; `true` only in
  fleet's published profile (`deploy/published/oct-fleet-maintenance/published.env`),
  guarded both directions by a deploy test.
- **The four SD rulings, as ratified (Cray, typed, 2026-08-14):** SD-1 → (b)
  ordered application-level child deletes plus the completeness guard; SD-2 →
  (a) files first, then rows; SD-3 → no status exemption (age governs, status
  does not) and the audit chain's dangling `case_id` pointer stated as intended
  design; SD-4 → (a) run-link rows deliberately retained.

**What this closeout does NOT close:**

- **PLAN-0103 AC-11 remains Cray's.** The RoPA (retention cell included) is
  Cray's artifact in the controller's voice; this note is its input, nothing
  more (LOCKED-4/-5).
- **The DSR-on-request path is still undefined for case rows** (this PLAN's
  Out of Scope). The per-case deletion unit is factored so a future DSR path
  can call it for one named case; building that path needs its own ruling on
  requester identification.
  _[Corrected s232, **`was an error`** — see the fuller note in §Out of Scope.
  The factoring was asserted twice and existed in neither place; `delete_case`
  was extracted in s232 to make both sentences true rather than to delete them.
  🔴 **The lesson is not the missing function, it is that a closeout restated a
  build claim nobody read the code to check** — the same shape as this PLAN's
  own AC-2 correction, caught by the same means (reading the module) one session
  later.]_
- **Fleet's live bring-up still needs its own typed §8 go** (PLAN-0103
  Step 10). Nothing in this PLAN touched the host; the armed flag changes what
  the next bring-up ships, not what runs today.

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

_Satisfied (2026-08-14): all three lines held — every AC closed on executed
evidence (AC-10's stamp records 7 PASSED / 0 SKIPPED for the DB-backed
modules), probes P1–P13 RED-witnessed with P14's scope recorded honestly
(Step 7), and the gate re-verified at 4091 passed / 8 skipped on
`main` = `6f7c547` (AC-11's stamp)._

---

*Drafted by the in-harness `plan-drafter` subagent (ADR-013 D1 phased authority)
from a Cray-ratified dispatch, 2026-08-14. Rulings round folded in place the
same day by the same subagent (see the provenance note at top): four SD verdicts
stamped, Step 1 collapsed to the ruled shape, AC-2/AC-3/AC-4 fixed to the ruled
outcomes, Step 0 recorded satisfied — every recommendation's reasoning preserved
as the record. Author≠reviewer (ADR-012 D4.3):
drafter = plan-drafter; independent review = Code + Cray at PR merge; separation
intact. Every `file:line` claim re-verified on disk at drafting time against
`main` = `1d7903c`. AI-assisted; no `Co-Authored-By` per CLAUDE.md §7.*

*Closeout round written 2026-08-14 by the same subagent (the PLAN-0103
same-drafter precedent), from a Code-verified evidence dispatch on
`main` = `6f7c547`: all eleven ACs ticked with named evidence, the AC-2
correction recorded (`was an error`), Step 4's landed path and Step 5's
executed-as-corrected deviation stamped, Step 7 recorded with the closeout note
(input for the RoPA, never RoPA text — LOCKED-4/-5), `Status:` set Complete.
Test names, constants, the armed flag, the lifespan wiring, and the sweep
callable re-verified on disk at this round's drafting time. Author≠reviewer
(ADR-012 D4.3): drafter = plan-drafter; independent review of this diff = Code
at the PR; ratification = Cray; separation intact.*
