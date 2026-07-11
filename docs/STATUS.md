---
last_updated: 2026-07-11T16:36:41+07:00
session: 118
current_batch: "s118 cont.2: PLAN-0010 closed shipped+disabled #695; PLAN-0064 built #696 + closed #697 — read_stock execution-bound via the per-step router, 0062 AC-7 discharged; suite 2512/7"
current_actor: code
blocked_on: "Nothing blocking. main=869a56d gate-green; 0 open PRs; tree clean (2 pre-existing untracked); loop-dispatcher DISABLED — PLAN-0010 CLOSED shipped-then-disabled; MS-S1 idle, untouched all s118; dev Postgres UP"
next_action: "No PLAN active. Next ranking candidates: procurement ontology↔CSV drift (s118 grounding rank #2, CSV-aligned direction recommended); calm-path runnability (PLAN-0064 fact-9 follow-up); monotonic sequence column; hero-demo dossier (needs ADR); PLAN-0063 SD-4 bounded verification"
head_commit: 869a56d
recent_commits: [869a56d, 9a0eb7d, fdd6a9b, 75ed717, 0b784f7, 3bdef0d, 6146a06, 79978ec, 2694253, e8cba64]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 118, 2026-07-11 (head_commit `22242e4` → `2694253`) — PLAN-0063
> audit-chain verification surface (trust dossier object ③, first product
> surface) COMPLETE in one window: drafted + ratified (#687, SD-1..6 as-rec)
> → PR1 `GET /audit/verify` (#688) → PR2 monitor "Verify chain" panel (#689)
> → closed, all 8 ACs → `done/` (#690).** `verify_chain()` (PLAN-0047 Step 5)
> gains its FIRST production caller: **#688** exposes a typed
> `ChainVerificationReport` with SD-2(d) SPLIT VISIBILITY — the verdict is
> open, verbatim break detail is credentialed via the new
> `get_optional_principal` seam in `services/api/auth.py` (OQ-1 =
> `/audit/verify`); **#689** renders it as an ON-DEMAND monitor panel
> (`view-monitor.js?v=c34`, off the poll timers). `services/db/audit_log.py`
> + `alembic/` byte-unchanged (AC-8 pins verified). **Evidence bar:** #690's
> required CI `gate` = **2506 passed / 8 skipped in 93.5 s** (FULL suite
> incl. DB-backed tests via the CI postgres:16-alpine service) on code
> identical to `main=360007a` plus the docs close-out; local on the merge
> commit ruff + ruff-format + mypy --strict clean (the LOCAL pytest degraded
> to 2391/123-skipped — dev Postgres DOWN, dockerd off — recorded as NOT the
> bar). **TWO DISCLOSED DEFERRALS** (in the close-out, not silent): (1) the
> merge-commit LOCAL full-suite re-run and (2) the Step-5 render check —
> both blocked on the dev Postgres; starting dockerd = §8 host-state
> awaiting explicit Cray go; erratum-if-fail when the render check runs.
> SD-4 follow-up (bounded/incremental verification) → Active TODO.
> **CONTINUATION (same session, afternoon batch — `next-work-analyst`
> ranking delivered; Cray picked "Router + hygiene"; every pick/ratification
> below = Cray via AskUserQuestion):** (1) **Both disclosed deferrals
> DISCHARGED — `confirmed — prior intact`, no erratum.** Cray gave the §8
> go; Docker Desktop restarted, `vero-postgres` (volume
> `vero-lite_postgres_data`) up. The Step-5 render check PASSED its
> pre-committed strings: the monitor "Verify chain" panel rendered "chain
> intact · 36 rows verified" over the REAL dev-DB audit chain (36 rows,
> breaks []), DOM-asserted + screenshot; the withheld leg is not reachable
> on this deployment (dev box opts out of authn via `.env`) and stays
> pinned by the AC-6 pytest matrix. Local full suite on main WITH Postgres
> = **2507 passed / 7 skipped** (supersedes the 2391/123 degraded run). (2)
> Orphan test DB `vero_lite_test_69fa7362` DROPPED (Cray-approved §8) after
> fresh re-verification: sha256-hashed ALL 16 existing checkout-path forms
> (main + 7 worktrees × POSIX/UNC) — none maps to `69fa7362`; only the live
> `vero_lite_test_bb36873b` remains → the s117 housekeeping TODO fully
> discharged. (3) **PLAN-0064 "per-step QUERY router for procurement"
> READY (#692)** — `plan-drafter`-authored, Code R2 re-verified every
> load-bearing citation on disk (accept); **SD-0..SD-5 ratified as-rec**:
> SD-0 no ADR-016 amendment (executor supply is "not an engine contract",
> 0016:511-513; the STOP tripwire stands) / SD-1 declaration-presence
> dispatch / SD-2 engine-module home (`query_router.py`) / SD-3
> `read_stock` only / SD-4 tripwire test rewritten in place / SD-5 declared
> reads served by the registry-registered `ProcurementSyntheticAdapter`.
> Reopens PLAN-0062 AC-7 per ERRATUM 2 by its own ACs. (4) **Hygiene
> (#693):** PLAN-0004 (Phases A+B shipped; Phase C optional → backlog) +
> PLAN-0012 (vero-bridge Phase 1 shipped + live; AC-1/AC-2 ticked as
> bookkeeping; Phase 2 stays unminted) filed to `done/`; **PLAN-0010
> deliberately NOT closed** — Cray asked for an ELI-CRAY brief before the
> close-vs-park decision (delivered in-session; decision pending). NEXT:
> build PLAN-0064 (un-gated Code build, one PR).
> **CONTINUATION 2 (same session — PLAN-0064 went draft [`plan-drafter`] →
> Code R2 → Cray SD ratification → build → close in ONE session-118 day):**
> (1) **PLAN-0010 CLOSED "shipped + intentionally disabled" → `done/`
> (#695)** — Cray-ratified after the ELI-CRAY brief (AskUserQuestion);
> AC-1/AC-3/AC-5 ticked against `tests/loop/` + the 427-message production
> run (2026-05-26→06-25); AC-2/AC-4/AC-6 left unticked HONESTLY (closed by
> operational decision over the s76 drift hazard, NOT full AC discharge —
> they become requirements of any revival PLAN); companion chore fixed the
> stale `tools/loop/__init__.py` "(future) dispatcher" docstring. (2)
> **PLAN-0064 BUILT (#696) + CLOSED, all 8 ACs → `done/` (#697)** —
> `QueryStepRouter` (declaration-presence, SD-1) in
> `services/engine/procedures/query_router.py` + 5 unit pins; the
> production procurement factory routes per step: declared `read_stock`
> (`reads: [Part]`, PLAN-0048 single-read) → the SHIPPED
> `QueryStepExecutor` over the REGISTRY-registered
> `ProcurementSyntheticAdapter` (SD-5); undeclared `intake` → the
> co-existing `_SeedQuery` byte-identically (PLAN-0062 SD-C carried).
> ERRATUM-2 tripwire test rewritten IN PLACE per its own contract (SD-4);
> SD-0 honored — zero orchestrator/registry/spec change, the STOP tripwire
> never fired; the L-4 governance-pin consequence disclosed in the PR body.
> Suite **2512/7 local WITH Postgres**. **Honest frame (LOCKED-9 style —
> nothing claims more):** procurement `read_stock` = declared ✔ ·
> load-gated ✔ · **execution-bound ✔ on the production factory path**;
> `intake` unchanged (declared-expressible ✔ per 0062 AC-6, production
> execution = the co-existing seed, derived fields ✖);
> `low_stock_reorder_round` END-TO-END = **still not production-runnable**
> — `judge_stock` reads `measured_value`, raw Part rows don't carry it
> (PLAN-0064 fact 9 → Active TODO); **PLAN-0062 AC-7's deferral is
> DISCHARGED by reference** (no 0062 line edited).

> **Session 117, 2026-07-10 (head_commit `fe9e98d` → `22242e4`) — residual
> flaky-suite fix: the TESTS half of #678's wall-clock invariant (#684
> `fix(test)`).** A ~1-in-3 full-suite flake on `main` — two procurement DB
> tests (`test_event_run_resolves_through_to_completed`,
> `test_scheduled_procurement_run_parks_at_doa_gate`) — with NO code cause
> (#683 was docs-only), green in isolation and under `tests/services/db` alone.
> Root cause = the SAME non-monotonic WSL2 `datetime.now(UTC)` #678 found, on
> the OTHER side of the seam: `load_run` still `ORDER BY created_at` (a
> wall-clock column), and #678 migrated only the PRODUCTION consumers
> (`resume_run`, `GET /runs/{id}`) to `suspended_step_result()` — leaving SIX
> TEST sites reading `loaded.step_results[-1]`. Under a backward step the
> `approve` gate sorts before the completed `compliance` step, so `[-1]` names
> the wrong step → both observed messages. Fixed BY INTENT: 4 demo sites →
> `suspended_step_result()`; 2 latent sites → select by `step_id` (status would
> make their own status-assert circular); + 2 order-asserting sites (a
> different shape, found while reading) now compare `sorted(...)` — a round-trip
> preserves a step SET, not an order. Cover: a non-vacuous AST guard
> (`test_load_run_ordering_guard.py` — reports EXACTLY the six pre-fix sites,
> provenance-tracked so legit in-memory `RunResult[-1]` reads pass) + a
> deterministic clock-inversion pin. NO production code changed. Verified:
> `pytest -q` 5x pre-merge + 3x on the merge commit `22242e4` (CI is PR-only) =
> eight consecutive full-suite greens, 2499/7 (was 2496 + 3 new); ruff clean;
> offline, MS-S1 untouched.

> **Session 117, 2026-07-10 (head_commit `a711927` → `9a12087`) — flaky-DB-test
> isolation track (a CONCURRENT Code track, separate from the PLAN-0062 work
> below). One intermittent `test_procedure_headline` failure unpacked into TWO
> unrelated bugs, one of them PRODUCTION. #678 + #679 + #680.**
> **The load-bearing finding (#678 `fix(engine)`):** `datetime.now(UTC)` on the
> WSL2 dev box is **NON-MONOTONIC** — measured 2 backward steps in a 20 s sample,
> worst jump **−555 ms**. `load_run` orders step results by that wall-clock
> `created_at`, and `resume_run` / `GET /runs/{id}` read `step_results[-1]` as the
> suspended step. A run straddling the jump therefore resumed from an
> already-COMPLETED step: re-running a decided gate (duplicate side effects; run
> stuck at `waiting_human`), or failing on "undecided proposals". ~1 process in 20.
> Fixed by selecting the suspended step by **STATUS** — the shared
> `suspended_step_result()` in `services/engine/procedures/persistence.py`.
> gate/resolve was never affected (it looks steps up by caller-supplied `step_id`).
> **The test bug (#678 `test(db)`, deterministic):** `Base.metadata` is populated
> by import side effect, so a process collecting only `tests/services/db` never
> registered `action_identity` — `create_all` skipped it, `drop_all` could not
> reach it, and the `alembic upgrade head` tests left it standing
> (`DuplicateTableError`). The full suite hid it. Fixed with `alembic/env.py`-
> mirroring registration imports + a `DROP SCHEMA public CASCADE` per test.
> **#679 `test(db)`:** that reset made concurrent `pytest` in sibling worktrees
> wipe each other, so the derived test DB is now scoped per checkout
> (`vero_lite_test_<8-hex of repo root>`); an explicit `TEST_DATABASE_URL` still
> wins verbatim, so CI is unaffected. Proven by a control experiment (shared DB:
> both checkouts fail; scoped: both pass).
> **#680 `fix(engine)`:** the "exactly one unresumed step" invariant was
> documented but unenforced — two such rows now raise rather than resume from the
> wrong step, and `get_run` answers **409** instead of an unhandled 500. Plus the
> HTTP-surface regression test #678 left owing.
> **Suite 2473/7 → 2488 passed / 7 skipped**, verified on the merge commit itself
> (CI here is PR-only and never tests a merge commit); ruff + format + mypy clean;
> offline, **MS-S1 untouched, dev DB unchanged**.
> **PLAN-0062 unchanged by this track — still 4-of-5 built, PR4 outstanding.**
> *(True when written; **superseded** — PR4 #682 landed after this track closed and
> PLAN-0062 is now COMPLETE. See the PLAN-0062 block below.)*
> Carry-overs → Active TODOs.

> **Session 117, 2026-07-10 (head_commit `4da573d` → `359555b`) — PLAN-0062
> per-vertical seed migration COMPLETE: PR1b + PR2 + PR3 + PR4 shipped this
> session (four un-gated Code PRs; STATUS last written at the PR1b reconcile).
> PLAN-0062 = 5-of-5 built, all 9 ACs ticked → `docs/plans/done/`** — PR1 parity
> core (#672, s116) + PR1b env-band executor/energy factory (#673) + PR2 (#675)
> + PR3 (#676) + **PR4 (#682)** procurement shadow-parity + `read_stock` deferral
> + close-out. **Final honest enforcement frame (LOCKED-9 — nothing claims
> more):** the three OCT query steps — energy `read_readings`, supply_chain
> `read_temps`, aquaculture `read_do` — are declared ✔ · load-gated ✔ ·
> **execution-bound ✔ on the production HTTP path**; procurement `intake` is
> **declared-expressible ✔ (proven under shadow parity)**, production execution
> stays the co-existing `_SeedQuery`, execution-bound ✖ for the derived fields;
> `read_stock` is **deferred, labelled, reason corrected**.
> **PR2 (#675, `b9c5ebd` → merge `624b731`):** supply_chain `read_temps` migrated
> to the declared latest-per-group grammar over `event_concerns_shipment` +
> `verticals/supply_chain/procedures_factory.py`; the shared parity harness became
> **vertical-parameterised** (SD-3). It reused PR1b's `EnvBandEvaluateExecutor` +
> `advisory_stub_factory` **UNCHANGED — zero new engine surface** (supply_chain's
> judge is the SAME `env_band`; only the threshold differs — an 8 °C cold-chain
> ceiling vs energy's 90 °C). **OQ-2 settled against the data:**
> `where: {event_type: reading}` is load-bearing — the synthetic door-open alarm
> is NEWER than `shipment-frozen-01`'s last reading and carries no
> `measured_value`. Suite 2473/7.
> **PR3 (#676, `c17500a` → merge `a711927`):** aquaculture `read_do` migrated over
> `event_emitted_by_pond` + `verticals/aquaculture/procedures_factory.py` — the
> `main.py` registrar table's **fourth and final** entry. This one binds the
> **shipped `EvaluateStepExecutor` UNWRAPPED**, because aquaculture's judge is an
> `in_file_band` (typed `threshold 4.0 / direction below / watch_margin 1.0`) and
> a test **asserts `EnvBandEvaluateExecutor` is ABSENT** — the wrapper is the
> `env` half of the ADR-016 D2-A3 split, not a funnel. **Latent-bug catch:**
> latest-per-group is what *decides* pond-07 — its 4.6 mg/L reading sits inside
> the 4–5 watch band, its later 3.2 mg/L crash is a breach; a projection bug would
> have silently downgraded a crash to a watch (pinned by fixture + real-data
> parity + the e2e). **Scope-honesty note:** `_suspends` is a function of the
> STEP, not its input set, so the gated `aerate` suspends on every pass;
> `escalate_watch` (ADR-0019 watch→gated) + the auto `summary` terminal are
> reachable only AFTER a human resolves that gate via the DB-backed
> `resolve_gated_step` resume path — so PLAN-0062 Step 3's "watch-escalation path
> downstream" over-reaches what one pass can show; the PR asserts the watch band
> only where observable (judge verdict tags + absence from `aerate`'s breach-only
> fan-out). Suite **2479 passed / 7 skipped**, green on TWO consecutive full runs;
> ruff + ruff-format + mypy clean.
> **Pre-existing flake (surfaced, not fixed):**
> `tests/services/db/test_procedure_headline.py` is order-/state-dependent — it
> fails on a CLEAN `main` tree when `tests/services/db` runs as a subset; NOT a
> PLAN-0062 regression → spun off as its own task. **AC-5 erratum (ERRATUM 1) DISCHARGED** — PR4 #682's close-out records it (AC-5's
> "the *shipped* evaluate/action executors" wording vs PR1b's new
> `EnvBandEvaluateExecutor`), so the standing Active TODO is retired.
> **PR1b recap (#673):** `EnvBandEvaluateExecutor`
> (`services/engine/procedures/env_band_step.py`, binds
> `OCT_RECOMMEND_THRESHOLD`/`_DIRECTION` onto a band-less step, delegates to the
> SHIPPED `EvaluateStepExecutor`) + deterministic `advisory_stub.py` +
> `register_energy_procedure_executors` + the `main.py` per-vertical registrar
> table. ADR-016 D2-A4 honored (no `facet.decision_condition` dispatch; env band
> selected by the FACTORY). Everything offline/deterministic (SD-6); **MS-S1 never
> touched** in s116 or s117 (no host-state action, no live run). `main` green +
> PROTECTED; 0 open PRs; tree clean; loop-dispatcher DISABLED; MS-S1 idle; dev DB
> unchanged.
> **PR4 (#682, `bd8e586` → merge `359555b`) — the last of PLAN-0062's five PRs.**
> **AC-6 — intake join half proven under SHADOW parity:** a new
> `tests/verticals/procurement/test_intake_shadow_parity.py` runs the declared
> join half (`reads: [OperationalEvent, PurchaseOrder, Quotation]`, `where:
> {event_type: failure}`, fuse the hero PO, quotes `on: {left: part_id, right:
> part_id}`) through the production `run_procedure` path over the REAL
> `FastenalCsvAdapter` — information-identical to `_intake_seed`'s join-half
> fields (`price_thb`→`unit_price`, compared as `Decimal`) — emitting three flat
> rows with NONE of the seed's derived fields (`compliance`, the `criticality`
> amplification, the nested `candidate_quotes` reshape): the OQ-3 boundary made
> executable. `_SeedQuery`'s "nothing migrates" docstring superseded with the
> SD-C co-exist rationale. **A drift the test pins:** the ontology declares
> `PurchaseOrder.part_no` / `Quotation.price` / `OperationalEvent.equipment_id`
> while the real CSVs emit `part_id` / `price_thb` / `asset_id` (the load gate
> checks DECLARED props, the executor merges RUNTIME keys) → four declared
> `PurchaseOrder`∩`Quotation` collisions renamed, which is what keeps each
> quote's own supplier.
> **AC-7 — the deferral stands but the PLAN's stated reason was WRONG (ERRATUM
> 2):** PLAN-0062 said `read_stock` is deferred for "no substrate" — FALSE (the
> ontology declares `Part.stock_qty`/`reorder_point` and the registry-registered
> `ProcurementSyntheticAdapter` emits both; the missing columns live in the HERO
> demo's `part.csv`, not the vertical's). The true blocker is **per-`StepKind`
> executor routing** — procurement's QUERY executor is the fixed `_SeedQuery`, so
> a declared `read_stock` would pass the gate and still receive the intake
> requisition. This was SUMMARY DRIFT (fact 7's body already named the per-kind
> factory; the routing reason fell out of its heading → SD-1/AC-7/the header each
> carried the heading forward). Cray ratified (s117): keep the deferral, correct
> the reason; pinned as an executable invariant
> (`test_read_stock_is_blocked_by_per_kind_executor_routing_not_by_data`) — when
> a per-step router ships, that test fails and the deferral falls due.
> **Close-out:** PLAN-0062 → **Complete**, all 9 ACs ticked with **no ratified
> line reworded**; a Close-out section records **both errata** (ERRATUM 1 = AC-5's
> "shipped executors" vs PR1b's new `EnvBandEvaluateExecutor`; ERRATUM 2 above),
> each with its Cray ratification, + three in-body "see ERRATUM 2" pointers on the
> stale citations; `git mv docs/plans/0062-*.md docs/plans/done/`. **The session's
> real lesson:** two errata, both DISCLOSED rather than silently reinterpreted — a
> PLAN/ADR claim about shipped code is a claim to VERIFY, not a fact to repeat. All
> four shipped verticals now register a production procedure-executor factory
> (`main.py`'s per-vertical registrar table is complete). Green through the
> required CI `gate`; **full suite re-run ON THE MERGE COMMIT: 2496 passed / 7
> skipped** (CI here is PR-only, never tests a merge commit); ruff + ruff-format +
> mypy clean; offline/deterministic (SD-6), **MS-S1 untouched across s116 + s117**.
> **NEXT: PLAN-0062 is COMPLETE — no successor PLAN selected yet.** Candidate
> next-work (unranked): (a) a per-step QUERY router for procurement (would make
> `read_stock` migratable + reopen AC-7; pinned by the invariant test above); (b)
> the procurement ontology↔CSV column drift; the hero-demo dossier backlog; the
> plan-status decisions on PLAN-0004 / PLAN-0010 / PLAN-0012; the Rock-3 Box-4
> economics residue. The `next-work-analyst` skill ranks them against the code.

> **Session 116, 2026-07-09 — hygiene sweep (this batch, docs-only).** Filed
> two shipped-but-misfiled plans to `docs/plans/done/` — **PLAN-0019**
> (core-procedure baseline) + **PLAN-0027** (B-γ comparison baselines); their
> artifacts have been on disk + in use for sessions, only the status flip +
> closeout `git mv` were outstanding. Reconciled this file: corrected the stale
> Active-TODO **Rock-3** line (it still called the Q4 join-grammar ADR + grammar
> PLAN "both UNDRAFTED" — the ADR is **Accepted #659** and **PLAN-0061 is
> built+closed #664–#668**) and trimmed the s115 focus block. NO code change;
> full offline suite unchanged (2452 / 7). NEXT: the **Phase-3 per-vertical
> seed-migration PLAN** (PLAN-0062, via `plan-drafter`). Origin: s116
> `next-work-analyst` re-rank → Cray picked hygiene-first, then Phase-3.

> _Rotation note (session-118 CONTINUATION-2 reconcile, 2026-07-11,
> `docs(status):`): frontmatter bumped to `head_commit 869a56d`; the s118
> Current-Focus block was EXTENDED IN PLACE a second time (same session —
> no new block); the oldest Recent-Decisions row (2026-07-08 PLAN-0058)
> ROTATED OUT under R1 size pressure so the table holds at 10 after the
> new s118-continuation-2 row; two Active TODOs REMOVED (the s117 per-step
> QUERY-router TODO — DISCHARGED by PLAN-0064 #696; the PLAN-0010
> close-vs-park TODO — decided + executed #695) and one ADDED (calm-path
> end-to-end runnability, PLAN-0064 fact 9). The rotated row + both removed
> TODOs were emitted verbatim in the reconcile reply for the caller to
> append to `docs/status-archive/2026-h1-status.md` (Bash-side). The prior
> s118-continuation rotation note was consolidated into this one (R4:
> self-referential meta-note). Per the STATUS.md Rotation Policy
> (R1/R2/R4)._

> _Older content rotates out of this file per the **STATUS.md Rotation Policy (R1-R6)** in [`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md) (Lesson #23): Current Focus keeps the 4 newest sessions (<=8 blocks); Recent Decisions keeps the last 10 rows. Rotated blocks/rows live in [`docs/status-archive/`](status-archive/) (sessions <=46: `2026-h1-current-focus.md`; 2026-06-10 onward: `2026-h1-status.md`) and git history (Tier 3)._

## Prior focus (archived)

PLAN-003 Phase 1 (ontology engine + 5 emitters), PLAN-0005 Phase 2
(OCT engine runtime layer), PLAN-0006 (LLM reasoning hook),
PLAN-0007 Phase 1 (harness autonomy layer — deterministic floor),
and **PLAN-0008 Phase 2 (harness autonomy layer — probabilistic /
classifier-mediated engine on top of Phase 1)** are all **merged and
moved to `docs/plans/done/`**. The Cowork-as-Tier-1 trial that ran as
the test-bed across the earlier batches **concluded** — ratified
permanently by **ADR-009** (Cowork = merged Tier 0 + Tier 1 workspace;
commits stay Code-exclusive). PLAN-004 Phase A (handoff frontmatter
schema + tooling) also landed; Phase B/C remain deferred (backlog).
Full detail lives in `docs/plans/done/`, the Recent Decisions table
below, and git history.

## Recent Decisions (last 10)

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-11 | **s118 CONTINUATION 2 — PLAN-0010 CLOSED "shipped + intentionally disabled" (#695) / PLAN-0064 per-step query router BUILT (#696) + CLOSED all 8 ACs → `done/` (#697); draft→R2→SD-ratify→build→close in ONE session-118 day** — #695: Cray-ratified (AskUserQuestion) after the ELI-CRAY brief; AC-1/AC-3/AC-5 ticked (tests/loop/ + the 427-message production run), AC-2/AC-4/AC-6 HONESTLY unticked (operational close over the s76 drift hazard — they become revival-PLAN requirements). #696: `QueryStepRouter` (declaration-presence, SD-1) routes the production procurement factory per step — declared `read_stock` → the SHIPPED `QueryStepExecutor` over the registry-registered `ProcurementSyntheticAdapter` (SD-5); undeclared `intake` → `_SeedQuery` byte-identically; ERRATUM-2 tripwire rewritten in place (SD-4); SD-0 zero engine change; **PLAN-0062 AC-7's deferral DISCHARGED by reference**; `low_stock_reorder_round` end-to-end still NOT production-runnable (fact 9 → Active TODO). Suite **2512/7** local WITH Postgres. Full narrative: the Session-118 CF block above | `869a56d` (#697 merge) / `9a0eb7d` / `fdd6a9b` (#696 merge) / `75ed717` / `0b784f7` (#695 merge) / `3bdef0d` / `services/engine/procedures/query_router.py` + `verticals/procurement/hero_demo/run.py` + `verticals/procurement/procedures.yaml` + `tests/verticals/procurement/test_intake_shadow_parity.py` + `docs/plans/done/0064-per-step-query-router-procurement.md` + `docs/plans/done/0010-phase3-5-scheduled-task-autonomy-loop.md` |
| 2026-07-11 | **s118 CONTINUATION — PLAN-0063 deferrals DISCHARGED (`confirmed — prior intact`, no erratum) / #692 PLAN-0064 Ready / #693 hygiene / orphan DB dropped (session 118 cont.)** — Step-5 render check PASSED its pre-committed strings over the REAL dev-DB audit chain (36 rows, breaks []; DOM-asserted + screenshot) + local full suite WITH Postgres **2507/7** (supersedes the 2391/123 degraded run); `vero_lite_test_69fa7362` DROPPED (Cray §8; all 16 checkout-path hash forms re-verified, only the live `bb36873b` remains); **PLAN-0064** (per-step QUERY router for procurement) `plan-drafter`-authored, Code R2 accept, **SD-0..SD-5 Cray-ratified as-rec**, reopens PLAN-0062 AC-7 per ERRATUM 2; PLAN-0004 + PLAN-0012 → `done/` (PLAN-0010 deliberately NOT closed — close-vs-park = Cray decision pending after the s118 ELI-CRAY brief). Full narrative: the Session-118 CF block above | `2694253` (#693 merge) / `e8cba64` (#693 docs) / `f494013` (#692 merge) / `b7e6e40` (#692 Ready) / `docs/plans/0064-per-step-query-router-procurement.md` + `docs/plans/done/{0004,0012}-*.md` |
| 2026-07-11 | **PLAN-0063 audit-chain verification surface COMPLETE (all 8 ACs) → `done/` — trust dossier object ③'s first product surface (session 118; #687/#688/#689/#690)** — #687 Ready (`plan-drafter`-authored, SD-1..6 Cray-ratified as-rec); #688 PR1 `GET /audit/verify` → typed `ChainVerificationReport`, `verify_chain()`'s (PLAN-0047 Step 5) FIRST production caller, SD-2(d) split visibility (verdict open / verbatim break detail credentialed via the new `get_optional_principal`; OQ-1 = `/audit/verify`); #689 PR2 on-demand monitor "Verify chain" panel (off the poll timers); #690 close-out with TWO DISCLOSED DEFERRALS (local merge-commit full-suite + Step-5 render check — dev Postgres down, §8 Cray go pending, erratum-if-fail). `services/db/audit_log.py` + `alembic/` byte-unchanged (AC-8 pins). Suite **2506/8** via the required CI `gate`. Full narrative: the Session-118 CF block above | `7e87d76` (#690 merge) / `576a201` (#690 close) / `360007a` (#689 merge) / `ceee552` (#689 feat) / `9d02686` (#688 merge) / `b41e3f5` (#688 feat) / `ec2250e` (#687 merge) / `e2c65f0` (#687 Ready) / `services/api/routers/audit.py` + `services/api/models/audit.py` + `services/api/auth.py` (`get_optional_principal`) + `tests/api/test_audit_verify.py` + `services/api/static/assets/view-monitor.js` + `docs/plans/done/0063-audit-chain-verification-surface.md` |
| 2026-07-10 | **Residual flaky-suite fix — the TESTS half of #678's wall-clock invariant (session 117; #684, `fix(test)`)** — a ~1-in-3 full-suite flake on `main` (two procurement DB tests), NO code cause (#683 docs-only), green in isolation. SAME non-monotonic WSL2 `datetime.now(UTC)` as #678 on the OTHER side of the seam: `load_run` still `ORDER BY created_at`; #678 migrated only the PRODUCTION consumers to `suspended_step_result()`, leaving SIX TEST sites on `step_results[-1]` → under a backward step `[-1]` names the wrong (completed) step. Fixed by intent: 4 demo sites → `suspended_step_result()`, 2 latent → select by `step_id` (a status-assert would be circular), + 2 order-asserting sites now compare `sorted(...)` (a round-trip preserves a step SET, not an order). Cover: a non-vacuous AST guard (`test_load_run_ordering_guard.py`, reports EXACTLY the six pre-fix sites) + a deterministic clock-inversion pin. NO production code changed; `pytest -q` 5x pre-merge + 3x on the merge commit (CI PR-only) = eight consecutive greens, 2499/7 (was 2496 + 3 new); ruff clean, offline, MS-S1 untouched. | `22242e4` (#684 merge) / `0a9542a` (#684 fix) / `tests/services/db/test_load_run_ordering_guard.py` + `tests/services/db/{test_event_procurement_demo.py,test_scheduled_procurement_demo.py}` + `tests/services/engine/procedures/{test_procedure_persistence.py,test_write_ahead.py}` |
| 2026-07-10 | **Flaky-DB-test isolation track — one intermittent `test_procedure_headline` failure = TWO unrelated bugs, one PRODUCTION (session 117, a CONCURRENT Code track; #678/#679/#680)** — **#678 (a) production correctness:** WSL2 `datetime.now(UTC)` is NON-MONOTONIC (2 backward steps / 20 s, −555 ms worst); `load_run` orders step results by that wall-clock `created_at` and `resume_run`/`GET /runs/{id}` read `step_results[-1]` as the suspended step → a run straddling the jump resumed from an already-COMPLETED step (re-ran a decided gate, dup side effects, stuck `waiting_human`; or "undecided proposals"); ~1 process in 20. Fixed by selecting the suspended step by **STATUS** (`suspended_step_result()`); gate/resolve never affected (looks up by caller `step_id`). **(b) test isolation (deterministic):** `Base.metadata` is import-populated → a `tests/services/db`-only process never registered `action_identity`, so `drop_all` left it for the next `alembic upgrade head` (`DuplicateTableError`); the full suite hid it. Fixed with `alembic/env.py`-mirroring registration imports + `DROP SCHEMA public CASCADE` per test. **#679:** that reset made concurrent sibling-worktree `pytest` wipe each other → test DB scoped per checkout (`vero_lite_test_<8-hex repo root>`), explicit `TEST_DATABASE_URL` still wins so CI is unaffected; control experiment (shared DB → both fail; scoped → both pass). **#680:** the "exactly one unresumed step" invariant was documented but unenforced → two such rows now raise; `get_run` answers **409** not an unhandled 500; + the HTTP-surface regression test #678 left owing. Suite 2473/7 → **2488/7**, verified on the merge commit (CI here is PR-only); ruff+format+mypy clean; offline, MS-S1 untouched, dev DB unchanged. Carry-overs → Active TODOs. | `9a12087` (#680 merge) / `7afff6a` / `8b617b0` (#679 merge) / `4f018bf` / `47a58ed` (#678 merge) / `a4593c8` / `b4b042c` / `services/engine/procedures/persistence.py` + `services/api/routers/runs.py` + `tests/db_support.py` |
| 2026-07-10 | **PLAN-0062 (Q4 Phase-3 per-vertical seed migration, parity-guarded, SD-C) — COMPLETE, all 9 ACs → `done/` (sessions 116–117; #671/#672/#673/#675/#676/#682)** — **#671 Ready** (`docs/plans/0062-*.md`): plan-drafter-authored, Code R2-verified facts 3/5/7, **SD-1..SD-6 Cray-ratified as-rec** (AskUserQuestion). **#672 PR1 (parity core, s116):** energy `read_readings` → the DECLARED latest-per-group grammar (`reads:[OperationalEvent]` + `where:{event_type:reading}` + `project:{latest_per:event_emitted_by_asset, order_by:occurred_at}`) + the shared `assert_read_step_parity` harness (grammar == an INDEPENDENT hand-coded SD-5 reference, ZERO tolerance) + SD-5-edge fixtures + a 4-vertical load-gate pin; suite 2458/7. **#673 PR1b (s117):** `EnvBandEvaluateExecutor` (binds `OCT_RECOMMEND_THRESHOLD`/`_DIRECTION` onto a band-less step, delegates to the SHIPPED `EvaluateStepExecutor`) + deterministic `advisory_stub.py` + `register_energy_procedure_executors` + `main.py` per-vertical registrar table → energy `read_readings` now **execution-bound ✔ on the production HTTP path**. **#675 PR2 (s117):** supply_chain `read_temps` over `event_concerns_shipment` + `verticals/supply_chain/procedures_factory.py`; parity harness went vertical-parameterised (SD-3); reused PR1b's `EnvBandEvaluateExecutor` + `advisory_stub_factory` UNCHANGED (same `env_band` judge, only the threshold differs — 8 °C cold-chain vs energy's 90 °C); OQ-2 settled against the data (`where:{event_type:reading}` load-bearing); suite 2473/7. **#676 PR3 (s117):** aquaculture `read_do` over `event_emitted_by_pond` + `verticals/aquaculture/procedures_factory.py` (the `main.py` registrar table's 4th/final entry); binds the shipped `EvaluateStepExecutor` UNWRAPPED (judge is `in_file_band` typed `threshold 4.0/below/watch_margin 1.0`; a test asserts `EnvBandEvaluateExecutor` is ABSENT — the `env` half of the ADR-016 D2-A3 split). All THREE OCT query steps now execution-bound ✔; procurement `intake` is declared-expressible ✔ (shadow parity, PR4) but production execution stays the co-existing `_SeedQuery` (✖ for the derived fields); `read_stock` deferred/labelled/reason-corrected. ADR-016 D2-A4 honored (env band selected by the FACTORY). **PR4 (#682, `bd8e586` → merge `359555b`):** AC-6 intake shadow-parity over the REAL `FastenalCsvAdapter` (declared join half == `_intake_seed`'s fields, derived fields ABSENT; four `PurchaseOrder`∩`Quotation` column collisions renamed to keep each quote's supplier); AC-7 `read_stock` deferral KEPT, its "no substrate" reason CORRECTED to per-`StepKind` executor routing (ERRATUM 2, Cray-ratified, pinned by an executable invariant test) → PLAN-0062 **COMPLETE (all 9 ACs)**, both errata (ERRATUM 1 = AC-5 "shipped executors" vs PR1b's `EnvBandEvaluateExecutor`; ERRATUM 2) recorded in the Close-out, `git mv`→`done/`; suite **2496/7 on the merge commit**. Both errata DISCLOSED, not silently reinterpreted. Un-gated Code build (PLAN-0062 §6); offline (SD-6), MS-S1 untouched. Full narrative: the Session-117 CF block above | `359555b` (#682 PR4 merge) / `bd8e586` (#682 feat) / `a711927` (#676 PR3 merge) / `c17500a` (#676 feat) / `624b731` (#675 PR2 merge) / `b9c5ebd` (#675 feat) / `ea08e54` (#673 merge) / `f41da9c` (#673 feat) / `8641cb3` (#672 merge) / `d9e4bd2` (#672 feat) / `66beb17` (#671 merge) / `833676e` (#671 Ready) / `services/engine/procedures/{env_band_step.py,advisory_stub.py}` + `verticals/{energy,supply_chain,aquaculture}/procedures_factory.py` + `services/api/main.py` + `tests/services/engine/procedures/test_seed_migration_parity.py` + `tests/verticals/procurement/test_intake_shadow_parity.py` + `docs/plans/done/0062-per-vertical-seed-migration.md` |
| 2026-07-09 | **PLAN-0061 join/projection-grammar build COMPLETE (all 8 ACs) → moved to `docs/plans/done/` — the ADR-016 Q4 amendment RENDERED: a query step now DECLARES multi-read equi-join enrichment + latest-per-group projection as typed authored spec — declared ✔ load-gated ✔ execution-bound ✔ for the 2 v1 shapes (session 115; #664/#665/#666/#667/#668)** — the un-gated Code build of the Ready PLAN (§6 "Steps execute directly"); ALL offline/deterministic, NO live run (SD-6 — MS-S1 never touched); every PR green through the required CI `gate`; **full suite 2452 passed / 7 skipped, ruff + mypy clean.** Chain: **#664** the SD-D substrate (`JoinKeyMeta` + ONE shared parser; `foreign_key` no longer dropped at load; `join_path` → typed) → **#665** the SD-1 lean `JoinSpec`/`ProjectSpec` schema + H-governance pin (a mid-flight edit fails CLOSED at resume) + the structural load gate (`validate_read_bindings` `meta=`; WARN-first on/fuse overrides, OQ-4) → **#666** compile + execute (`JOIN_SHAPE_VIOLATION`, OQ-1; `plan_read` `meta=` = ONE decision surface; `QueryStepExecutor` SD-1 pinned pipeline, D-N2 extended; single-read path byte-identical) → **#667** both shapes e2e over the REAL energy + procurement ontologies (SD-3 fixtures, zero vertical-file change; DB-backed JSONB-safety + governance-hash round-trip) → **#668** Ready → Complete → `done/`. The 4 shipped verticals' hand-written seeds stay execution-bound ✖ until the Phase-3 parity-guarded migration PLAN (SD-C). Full narrative: the Session-115 CF block above | `5a264d6` (#668 PLAN-COMPLETE move-to-done) / `66896e8` (#668 merge) / `e04a00b` (#667 Step 4 feat) / `0d738e1` (#666 Step 3 feat) / `93e01d1`+`7fb7497` (#665 Step 2) / `978caca` (#664 Step 1 feat) / `services/engine/ontology_meta.py` (`JoinKeyMeta` + shared parser) + `services/engine/procedures/{spec.py,orchestrator.py,query_step.py}` + `docs/plans/done/0061-join-projection-grammar-build.md` |
| 2026-07-09 | **DESIGN: ADR-016 join/projection-grammar amendment ACCEPTED (Q4 multi-read) — Phase 1 of the moat join-grammar sequence (session 115; #659)** — renders ADR-016's deferred Q4 (the 2026-07-01 OQ-5 "the multi-read join lands with Q4"; PLAN-0048 walled the grammar off as "an ADR-016 amendment"): query steps will DECLARE multi-read joins + projections as typed, authored, deterministic spec surface (today `StepInput.reads` is names-only + `QueryStepExecutor` refuses `len(reads)>1` typed). **SD-A grammar surface = HYBRID** — ontology `link_types.foreign_key` = the default join (governed, single source of truth) + a typed per-step explicit override for shapes the ontology cannot declare (the procurement `intake`'s positional singleton fusion + custom projections). **SD-B v1 scope = the 2 shipped shapes** (equi-join enrichment + latest-per-group projection; general group-by/aggregation math DEFERRED — stays the walled-off `nl_query` surface). **SD-C = co-exist + parity-guarded seed migration (Phase 3, no force-retire).** **SD-D (entailed by SD-A)** = promote `LinkTypeMeta.foreign_key` into typed form + parse ADR-0027 `join_path` into the same execution-consumable shape (projection layer only; ADR-008 grammar untouched). **OQ-1..4 ratified as-rec** (Cray, AskUserQuestion): extend `StepInput` `join`/`project`; NO repair loop in v1 (D-N2); grammar = join+projection ONLY (arbitrary computation stays downstream/seed → `intake` migrates PARTIALLY under the SD-C parity guard); warn-first override validation. **NO LLM in the read path** (LOCKED-6 / ADR-0024 D3/D6); every joined type still routes through the single `read_bound_violation` bound at BOTH load gate + run dispatch (PLAN-0048 AC-3, extended not forked). `plan-drafter`-authored (in-place amendment per the D2-Amendment precedent), Code R2-verified every cited file:line on disk (corrected a dispatch over-claim — the procurement join is declared as `quote_id→Quotation.quote_id` + transitive `part_no` via `Part`, not a literal `part_id` link). **Sequence:** this amendment → build PLAN (grammar schema + compile/execute extension + SD-D promotion) → Phase-3 per-vertical factory + seed migration. Origin: s115 Cray picked the Q4 join-grammar ADR after PLAN-0060 closed; the Phase-2 build **PLAN-0061 is Ready** (#661, `ad0f543`; SD-1..6 ratified as-rec — lean 2-construct schema, 4 phases, offline-only) | `ad0f543` (#661 PLAN-0061 Ready) / `a38acde` (#659 amendment feat) / `dbf25e2` (#659 merge) / `docs/adr/0016-governed-procedure-engine.md` (§ "Amendment (2026-07-09): join/projection grammar for multi-read query steps (Q4)") |
| 2026-07-09 | **PLAN-0060 reactive judgment handler catalog COMPLETE (all 7 ACs) → moved to `docs/plans/done/` — surface per-handler descriptions into the REACTIVE recommender judgment prompt so the model picks by MEANING, the fix for the session-114 event-bridge live-smoke FINDING (session 115; #655/#656/#657)** — the reactive judgment prompt now renders an **"Available actions" catalog** (per-handler `description`s) inside the **TRUSTED system instruction** (same trust class as the ADR-016 D5 goal), so the model distinguishes `emergency_source` vs `reorder` instead of bare handler NAMES. Registry gains a keyword-only `description` + `handler_catalog(vertical)`; the 4 handler-registering verticals (procurement / energy / supply_chain / aquaculture; vet_clinic registers none) declare `ACTION_DESCRIPTIONS`; the block reaches **both** Pattern-B calls **and** the PLAN-0020 skip path via `build_structuring_messages`→`build_reasoning_messages`; `generate_judgment` gains `include_handler_catalog` (all 3 reasoning modes); a default-off `handler_catalog_enabled` Settings flag is threaded at the reactive `recommend()` call site. `suggested_handler` enum unchanged; flag-off byte-identical; **GOVERNED path untouched (governed ≠ generated).** **#655 (Steps 1-6, offline binding bar):** full offline suite **2389 passed / 7 skipped**, ruff + mypy clean. **AC-7 live re-validate (host-state MS-S1 `gpt-oss:20b`, Cray-gated §8, evidence-only NOT a gate):** ONE controlled A/B on the s114 CNC line-down event — catalog OFF → `reorder` (reproduces the finding), catalog ON → `emergency_source` (confidence 1.0); same event, the flag the only moved variable, pass/fail pre-committed, each arm fired once. **#656 (SD-4 default flip):** `handler_catalog_enabled` default False→True after the AC-7 PASS (only `recommend()` reads it; `generate_judgment`'s param default stays False → governed path + benchmark harness unaffected; flag-off stays available). **#657:** Ready → Complete → `done/`. Origin: s115 `next-work-analyst` re-rank → Cray picked PLAN-0060 | `f6a2217` (#657 PLAN-COMPLETE move-to-done) / `0c68d58` (#657 merge) / `a81f05a` (#656 default-flip feat) / `468c3c9` (#656 merge) / `4d54683` (#655 Steps 1-6 feat) / `7c8f2e0` (#655 merge) / `services/engine/registry.py` (`description` + `handler_catalog`) + `services/engine/llm/prompt.py` ("Available actions" block in `build_structuring_messages`/`build_reasoning_messages`) + `services/engine/llm/structured.py` (`generate_judgment` `include_handler_catalog`) + `services/engine/recommender.py` (`recommend()` flag threading) + `services/api/config.py` (`handler_catalog_enabled`) + `verticals/{procurement,energy,supply_chain,aquaculture}/handlers.py` (`ACTION_DESCRIPTIONS`) + `docs/logs/2026-07-09-reactive-handler-catalog-live-revalidate.md` + `docs/plans/done/0060-reactive-judgment-handler-catalog.md` |
| 2026-07-08 | **PLAN-0059 KPI stat-tile panel COMPLETE (all 5 ACs) → moved to `docs/plans/done/` + the deferred event-bridge live-smoke FINDING recorded (session 114; B→A per Cray's directive; #649/#650/#651/#652)** — **(A, #650/#651/#652):** the hero demo's three headline ฿-impact figures — expedite premium `฿52,500` / avoided downtime `฿8.16M` / net benefit `฿8.11M` — now render as **KPI stat-tiles** over the already-shipped `GET /demo/hero/impact` ledger, with baseline→governed (`฿9.76M → ฿1.65M`) as a net-benefit-tile context sublabel; the old `kv()` rows are replaced (no duplication); no trend/target affordances. **Pure frontend composition — NO new ADR / backend / engine / payload change** (the PLAN-0057 "compose over shipped plumbing" pattern, render-only). `plan-drafter`-authored PLAN; Code R2-verified every citation + confirmed the `thb`/`thbM` formatters produce the pre-committed strings; **SD-1..SD-5 ratified as-rec** (Cray, session 114, AskUserQuestion). #651 diff confined to `services/api/static/**`, full offline suite green under the required CI `gate`, preview-verified on the hero view; #652 Ready → Complete → `done/`. **(B, #649, evidence-only §8 host-state):** the deferred event-bridge live smoke asked whether the REAL MS-S1 recommender (`gpt-oss:20b`) picks `emergency_source` for a procurement critical-asset-failure event — it chose **`reorder`** (`actor_kind=llm`, the real model engaged not the rule fallback, confidence 1.0). Root cause (offline trace): the reactive judgment prompt shows the model **bare handler NAMES only** (no per-handler descriptions / no when-to-pick guidance / `goal=None`); the distinguishing prose lives only in `procedures.yaml` step descriptions + the procedure goal, which thread into the GOVERNED path, not the reactive prompt. **Governed path + shipped hero demo (deterministic advisory stub) UNAFFECTED**; offline gates (`test_action_event_bridge.py`, `test_event_procurement_demo.py`) stay the binding bar + green. Fix (surface per-handler descriptions in the reactive prompt) = a DEFERRED next-work candidate (own PLAN, cross-vertical blast radius, then one controlled live re-validate). Origin: session-114 `next-work-analyst` re-rank → Cray picked **B → A** | `1de4d14` (#652 PLAN-COMPLETE move-to-done) / `ab02dfd` (#652 merge) / `e8a7d93` (#651 feat KPI panel) / `cffa9d1` (#650 PLAN Ready) / `f528f03` (#649 docs(logs) finding) / `services/api/static/**` (hero KPI stat-tiles) + `docs/logs/2026-07-08-event-bridge-recommender-live-smoke.md` + `docs/plans/done/0059-*.md` |
## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13; guarded trial (parallel to ADR-012) — verdict **continue-with-adjustments**. Run 1 (energy, s93) + Run 2 (supply-chain, s94) both COMPLETE, S-checks all PASS against pre-committed oracles, no R-PS trigger fired; C-1..C-3 CONFIRMED → **no open partner-sim debt**. ADR-011 audit stays gated on a REAL partner conversation (R3: SYNTHETIC provenance INFORMS but never TRIGGERS it). Full record: `docs/adr/0020-*.md` + the gitignored run packages `docs/research/private/2026-07-02-partnersim-run{1,2}-*.md`. _(Full prior narrative — the ~8 schema-mismatch findings, both run details, cross-run synthesis — archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **Procurement vertical — GO + SHIPPED (PLAN-0036 Fastenal, Stage 1):** 4th vertical greenlit (s75); PLAN-0036 drafted + merged Draft (#412, `7a7c036`; SD-1…SD-5 confirm-all). Demo target = Fastenal Thailand (auto-parts / EEC); **hero** = asset-failure → governed emergency sourcing, **calm-path** = low-stock reorder. Stage 1 = a PLAN-only pure-config plugin on the ADR-016 engine (zero `services/` core edit; CQ-1 / ADR-0023). **Pitch** = asset-ontology-triggered governed sourcing (native ontology ADR-008 + engine ADR-016), NOT the commoditized "governed"/"cross-vertical" claims. Full record: `docs/plans/0036-*.md` + the s72 de-risk dossier `docs/research/private/2026-06-22-procurement-*.md` (5 files: spec-expressiveness, GTM, asset-aware incumbent scan, AI-sourcing teardown, platform-incumbent deepdive). _(Full prior narrative archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2; Q3 ADR Accepted + BUILD COMPLETE s93 — open only for the residues).** (1) **Q3 ontology data-binding — DONE end-to-end:** the ADR-016 D2+D3 amendment (Accepted s93, #505) is now **BUILT + CLOSED** (PLAN-0046 → `done/`; #511 feat `878b517` / #512 close `eb63692`, s93 cont. 2026-07-02): `StepInput.reads: list[str]` + `Agent.allowed.object_types` + the `validate_read_bindings` **LOAD-time consistency/scoping gate** (`reads ∈ ontology ∩ allowlist`, SD-1 Option A) wired at both production pre-flight sites; `reads` H-governed via `STEP_GOVERNANCE_FIELDS` + the `lift_to_step` draft-strip hardening; 12 new tests, offline suite 2066 passed / 5 skipped. v1 = a typed read contract + load-gate, **NOT** runtime-enforced parity — the declared==dispatched teeth for the read side then **SHIPPED as PLAN-0048** (the "Q4 generic run-consume query executor", `docs/plans/done/0048-q4-generic-query-executor.md`, s96, #533–#539; all 15 ACs, Complete 2026-07-04): an engine-owned deterministic `QueryStepExecutor` (`services/engine/procedures/query_step.py`) giving *plain declared reads* the **declared ✔ · load-gated ✔ · execution-bound ✔** frame + a typed auditable refusal (no silent `[]`). **The remaining Q4 residue** (the ADR + grammar build now DONE — only the migration PLAN remains): the four shipped verticals are NOT yet on the generic executor — their query steps encode projections/joins the spec could not yet declare (PLAN-0048 fact-pack 8 / LOCKED-9: hand-written seeds stay **execution-bound ✖** until migrated). The join/projection-grammar ADR is now **Accepted** (ADR-016 Q4 amendment, #659) + the grammar is **BUILT + CLOSED** (PLAN-0061, #664–#668) — a declaring step is execution-bound ✔ for the 2 v1 shapes; only **(b) the per-vertical production-factory + seed-migration PLAN** (Phase 3 = **PLAN-0062, COMPLETE — all 5 PRs, all 9 ACs → `done/`** — PR1 #672 parity core + PR1b #673 env-band executor/energy factory + PR2 #675 supply_chain + PR3 #676 aquaculture + PR4 #682 procurement shadow-parity/close-out) is DONE, having migrated the four verticals' hand-written seeds onto the grammar (all THREE OCT query steps — energy `read_readings`, supply_chain `read_temps`, aquaculture `read_do` — now execution-bound ✔ on the production HTTP path; procurement `intake` is declared-expressible ✔ under shadow parity but production execution stays the co-existing `_SeedQuery` ✖ for derived fields; `read_stock` deferred/labelled/reason-corrected — ERRATUM 2). (2) **Box 4 (Profit Formula) — STILL DEFERRED (N≥3, unchanged).** The reasoning trace is operational, not economic — tie each action to ฿ impact (avoided outage / margin / ROI). Prepare by capturing the economic dimension as prose when hand-authoring verticals + proving the ฿ framing in the demo; type an economic-impact facet only after **N≥3** verticals triangulate it (the ADR-016 Q3 amendment left it a self-cancelling N≥3 marker). *(s84 strategy discussion + the 3-layer / ontology-binding diagram; Q3 ADR Accepted s93 #505; Q3 build complete + PLAN-0046 closed s93 cont. #511/#512; **Q4 executor SHIPPED = PLAN-0048 closed s96 #533–#539** [reconciled 2026-07-08]; **Q4 join-grammar ADR Accepted #659 + grammar built PLAN-0061 #664–#668** [reconciled 2026-07-09 s116] — **Phase-3 PLAN-0062 COMPLETE** [PR1 #672 + PR1b #673 + PR2 #675 + PR3 #676 + PR4 #682 → `done/`, reconciled 2026-07-10 s117]; TODO stays open ONLY for the Box-4 facet)*
- [ ] **Bounded/incremental chain verification (PLAN-0063 SD-4 follow-up, s118).** `GET /audit/verify` walks the WHOLE chain O(n) on demand — accepted at pilot scale and documented in the endpoint docstring. Future work = a checkpointed head / verify-since-anchor design; anchor storage ≈ external anchoring = **ADR-011 tripwire territory — do not build without re-reading the tripwire**. *(s118; #688/#690)*
- [ ] **Calm-path end-to-end runnability (PLAN-0064 fact-9 follow-up).** `judge_stock` reads `measured_value`; raw Part rows carry `stock_qty` — so `low_stock_reorder_round` still cannot run end-to-end on the production path. Options when ranked: a `project.fields` rename (PLAN-0064 SD-3's declined option (i)) vs a judge-contract decision; pairs with the ontology↔CSV drift candidate. *(s118; #696)*
- [ ] **procurement ontology ↔ CSV column drift (PLAN-0062 close-out follow-up, s117).** The procurement ontology declares `PurchaseOrder.part_no` / `Quotation.price` / `OperationalEvent.equipment_id` while the real CSVs emit `part_id` / `price_thb` / `asset_id`; the load gate checks DECLARED properties while the executor merges RUNTIME keys (the AC-6 shadow-parity test renames four `PurchaseOrder`∩`Quotation` collisions to keep each quote's own supplier). Data/ontology evolution — explicitly **out of PLAN-0062's scope**. *(s117; PLAN-0062 PR4 #682)*
- [ ] **DEFERRED: a monotonic `sequence` column on `step_results` (s117 flaky-DB track carry-over; needs a migration → own PLAN).** #678 fixed the resume/GET-run path to read the suspended step by STATUS, but two wall-clock orderings remain — `load_run` (`services/engine/procedures/persistence.py`) + the run-list `order_by(PipelineRun.started_at)` in `services/api/routers/runs.py:200` — both **DISPLAY-ONLY** now, so not urgent. **#684 closed the TESTS half of the same invariant** — six positional `step_results[-1]` reads that misread `load_run`'s wall-clock order — and a static AST guard (`tests/services/db/test_load_run_ordering_guard.py`) now prevents that class of regression; but `load_run`'s wall-clock `ORDER BY created_at` is **unchanged by design**, so **the deferral STANDS**: a monotonic per-run sequence column would remove the hazard at its ROOT rather than guard against it. It needs a DB migration, so it deserves its own PLAN (PLAN-0062-independent). *(s117; #678/#680/#684)*
- [ ] **Standard partner-intake form (template candidate — Cray observation, s93 partner-sim run-1).** Generalize the 6-ask structure (+ the TWP package's §1–§10 answer shape as a SYNTHETIC-bannered worked example) into a stakeholder-facing standard intake form per vertical, so partners can prepare narrative context for vero-lite to generate workflow pipelines more accurately. Template lineage = the partner-facing ONE-PAGER (full taxonomy allowed for real partners), NOT the R1-clean variant (partner-sim-only screen). Pairs with the partner-trial-readiness discussion + ADR-016 Phase 2 intake. *(s93; ADR-0020 run-1)*
- [ ] **Rock 4 — Cowork deep research DELIVERED → O-sequence locked, O-1 done, O-3 Accepted (s84).** The 4-box + Palantir + agentic research landed (`docs/research/private/2026-06-28-rock4-4box-palantir-agentic-research.md`; ~48 sources, vendor-vs-independent tagged, adversarially balanced; central finding = the evidence asymmetry [bullish ROI all vendor, independent mostly skeptical]) → Cray **locked O-1 → O-3 → O-2 → O-4**. **O-1 (Box-4 ฿ pitch artifact) DONE** (conservative ฿ + impact-ledger mock; `docs/strategy/private/2026-06-28-box4-roi-spine-impact-ledger-pitch.md`). **O-3 = ADR-0025 Accepted** (see Rock 2). **Remaining:** **O-2** (economic-impact facet + Q3 ontology data-binding = Rock 3, after N≥3) · **O-4** (agent-interop North-Star, vision only). [[reference_rock4_4box_palantir_demo_research]]. *(s84 Cray ask)*
- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten (full table: PLAN-0005 §8.1): rule-based recommender → **ADR-010 ACCEPTED (2026-05-22) → PLAN-0006 next** (LLM reasoning hook); minimal approval gate → **ADR-011+** (audit framework — trigger: first design-partner data / PDPA review); no mapping layer → **dbt/SQLMesh** (trigger: first non-synthetic source); hand-authored ORM → **"ORM emitter"** Rule-of-Three candidate (trigger: 3rd vertical / DDL↔ORM parity-test drift); base Postgres only → **PLAN-002** (pgvector/AGE — trigger: semantic + graph features); explicit registry → **ADR-006 D3 L2** (trigger: vertical #2/#3 or `new-vertical` generator). *(per Cray note 2026-05-21)*
- [ ] **Demo card UX — "trust shape", NO operator confidence badge (s74 design, Cray-approved).** For the next demo round's operator recommendation card: show **what / grounded-why / approve gate** + a **"show full reasoning trace" toggle** that reveals the engine-view (where the floor-vs-judge agreement lives, labelled *audit/QA — not the operator*; reuses the scene-6 why-toggle pattern). **No operator-facing confidence badge** — the floor-vs-judge `confidence_signal` (PLAN-0035 Phase 2) is an **engine-internal QA/audit signal kept trace-only (SD-3 option A)**; surfacing it as a badge mis-reads as "the action might be wrong" (it is **not** — member (b) is advisory, never changes the action). The **(B) first-class `verification` envelope field is NOT needed for the operator UI** — reconsider **only** if a future internal audit/QA dashboard wants confidence as a first-class field (trace stays sufficient otherwise). Settled via a show_widget design review (s74; Cray: "ตรงใจ ตอบโจทย์"). The reframe: users want *what was decided · is it right · why* — answered by the action + grounding (real entity, allow-listed handler, deterministic detection, human approve) + the reasoning trace, **not** a self-reported confidence number. *(Trigger: the next demo / UI round; pairs with any (B) reconsideration.)*
- [ ] **PLAN-004 Phase C — OPTIONAL POLISH (forward-declared; "may never land"):** HTML/markdown handoff dashboard under `docs/` + references-graph (mermaid dispatch chains) + `render_transcript.py` unified session export (PLAN-0004 §"Phase C"). *(Phase A + B both COMPLETE — session 35; the prior TODO's validator **warning-swallow bug was FIXED #312**, s58. Minor never-formally-scoped sub-ideas — README/`_rename-map` walk-exclusion, Cat G `references_*` autofix, OQ-2 effective-vs-authored `status:` dashboard flag — fold in only if Phase C lands. Reconciled 2026-06-16 s65 audit.)*
- [ ] **ORM-emitter per-vertical layout (B1-DP-1 follow-up; Cray-deferred s67).** B1 (PLAN-0031, #370) ships the ORM emitter writing energy's ORM to the **committed** `services/db/models.py` (via `code_generator._ORM_COMMITTED_DEST`) — the gitignored `verticals/<ns>/generated/` cannot host a runtime dependency. When a **2nd vertical needs its own ORM** (the Rule-of-Three trigger), decide the per-vertical layout: extend `_ORM_COMMITTED_DEST` to per-vertical committed modules **vs** un-ignore a per-vertical `generated/orm.py` (gitignore negation) + re-export. Premature to design now (one ORM today). *(Cray-deferred 2026-06-18)*
- [ ] **ADR-NN (TBD, ≥ ADR-014) + PLAN-002** — Custom Postgres image with extensions (ADR-011 earmarked for the audit framework, ADR-012 taken, ADR-013 taken by autonomy axis relocation; floor bumped from ≥0013 to ≥0014 on 2026-05-23 per ADR-013 T6)
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (low priority)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)

## Next Steps

1. **PLAN-0005 §8.1 revisit register** — remaining deferred-foundational simplifications at their batch boundaries (audit framework → ADR-011+, mapping layer, ORM emitter, base-Postgres → PLAN-002 (≥ADR-014), registry discovery).
2. **Partner-trial readiness gaps** — `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` awaits a dedicated Cray discussion.
3. **Deferred (backlog)** — PLAN-004 Phase C only (optional polish: handoff dashboard / references-graph / unified export — Phase B complete s35, warning-swallow fixed #312); PLAN-002 custom Postgres image (≥ADR-014).
4. **Ongoing** — Continue exercising the file-based handoff mechanism (Chat ↔ Code ↔ Cowork) across batches.

## Update Workflow

This file is updated when:
- A commit changes project state significantly
- A new ADR/PLAN is minted or completed
- Active priorities shift
- A batch closes (sync `last_updated` + `current_batch` + `head_commit` + `recent_commits` frontmatter)
- A session closes (sync all frontmatter fields; archive batch history if needed)

**Update mechanism (locked per STATUS staleness batch 2026-05-18, Hybrid A+B short-term, C long-term):**

- **Per closeout (Option A + Q1(b) discipline):** Closeout drafter includes the line "STATUS.md updated: yes / no / N/A" in their closeout. If `yes`, the closeout's commit batch should include a dedicated `docs(status): …` housekeeping commit (Q3(b/c) pattern) bumping at minimum the `last_updated` and `head_commit` frontmatter fields.
- **Per batch boundary (Option B full body):** Full body refresh (Current Focus + Recent Decisions + Active TODOs + Next Steps) at batch close, alongside the frontmatter bump.
- **Per session boundary:** Full body + frontmatter sync; consider archive of prior session's batch history.
- **Future (Option C, PLAN-004 Phase A):** Validator will flag stale STATUS.md by comparing **frontmatter `last_updated` field** against newest closeout's `created` timestamp (NOT file mtime — mtime is defeated by side-effect commits, e.g. `c85a595` 2026-05-16 normalization sweep that touched STATUS.md body without bumping `last_updated`).

**Q4 `head_commit` semantics (codified 2026-05-18, locked Cray ratification of midflight `2026-05-18-1049` §4 + closeout `2026-05-18-1202` §6.2):**

- `head_commit` = short SHA of the newest **substantive** commit on
  `origin/main` that STATUS.md content reflects.
- **Excluded from `head_commit`:** `docs(status): …` housekeeping
  commits. These commits encode no new repo state — they ARE the
  STATUS.md freshness marker. Including them in `head_commit` creates
  a self-defeat where every housekeeping commit makes STATUS.md appear
  "fresh" to Q4 detection regardless of substantive backlog.
- **Substantive (included in `head_commit`):** everything else —
  `docs(lessons):`, `docs(adr):`, `docs(runbook):`, `feat:`, `fix:`,
  `chore:` (when changing meaningful state), `refactor:`, `test:`, etc.
  Any commit type that changes durable repo content updates
  `head_commit` at the next STATUS.md edit.
- **Reader recipe (returning after a pause):**

  ```bash
  # Newest substantive commit on origin/main (the value head_commit should hold)
  git log -1 --format=%h --invert-grep --grep='^docs(status):' origin/main

  # Compare to STATUS.md head_commit field
  grep -E '^head_commit:' docs/STATUS.md
  ```

  If the two differ → STATUS.md content is stale relative to substantive
  repo state. If they match → STATUS.md is fresh.

- **Writer rule (at each STATUS.md update):** Set `head_commit` to the
  output of `git log -1 --format=%h --invert-grep --grep='^docs(status):' origin/main`
  *after* the substantive commits of the current batch land but *before*
  any `docs(status):` housekeeping commit (or, if the STATUS.md edit
  itself is in a substantive commit like `docs(lessons):`, set
  `head_commit` to that substantive commit's own SHA — which becomes
  knowable only post-commit, so the writer typically updates
  `head_commit` to the *most-recent prior substantive commit* and lets
  the next batch's first edit catch up).
- **Two failure modes this rule closes:**
  1. **mtime trap** (closeout `2026-05-18-1202` §2): side-effect commits
     that touch STATUS.md body without bumping `last_updated` (e.g.
     `c85a595` 2026-05-16 normalization sweep) leave the file mtime-fresh
     but semantically stale. A SHA in `head_commit` cannot drift this way.
  2. **Housekeeping self-defeat** (closeout `2026-05-18-1202` §6.2 +
     midflight `2026-05-18-1049` §4): if `head_commit` = own SHA, every
     `docs(status):` commit makes Q4 say "fresh" regardless of
     substantive backlog. Excluding `^docs(status):` from the comparison
     baseline closes this loophole.

Manually edited until Option C lands.
