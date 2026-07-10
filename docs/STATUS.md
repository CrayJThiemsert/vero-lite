---
last_updated: 2026-07-10T17:44:21+07:00
session: 117
current_batch: "s117 PLAN-0062 close-out (un-gated Code): PR4 #682 — intake shadow-parity (AC-6) + read_stock deferral reason corrected (ERRATUM 2) + close-out; PLAN-0062 COMPLETE (5 PRs)→done/; suite 2496/7."
current_actor: code
blocked_on: "Nothing blocking. main = 359555b, green on the merge commit (2496/7) + PROTECTED (required gate + strict); 0 open PRs; tree clean; loop-dispatcher DISABLED; MS-S1 idle; dev DB unchanged."
next_action: "PLAN-0062 COMPLETE (all 5 PRs); no successor PLAN selected. Candidate next-work items (unranked) enumerated in the s117 Current Focus block; run next-work-analyst to rank them vs the code."
head_commit: 359555b
recent_commits: [359555b, bd8e586, 1600395, 569ab58, 9a12087, 7afff6a, 895c548, b812f78, 8b617b0, 4f018bf]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

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

> **Session 115, 2026-07-09 (head_commit `1de4d14` → `5a264d6`; merge tip
> `66896e8`) — BUILD + LIVE-VALIDATE + CLOSE, the full join-grammar arc: (1)
> PLAN-0060 "reactive judgment handler catalog" shipped end-to-end (all 7
> ACs) → `docs/plans/done/` — the fix for the session-114 event-bridge
> live-smoke FINDING; (2) the Q4 join/projection-grammar ADR-016 amendment
> ACCEPTED (#659); (3) PLAN-0061 (join-grammar build) Ready (#661); (4)
> PLAN-0061 BUILT + CLOSED (all 8 ACs, #664–#668) — Phases 1-2 of the
> join-grammar sequence DONE.**
> Per-PR / per-SD detail for all three sub-batches (#655-#668) lives in the
> Recent-Decisions rows below + the `done/` plans (`0060`, `0061`) + the
> ADR-016 Q4 amendment. Headlines: **PLAN-0060** made the reactive prompt show
> per-handler descriptions (an "Available actions" catalog) so the model picks
> by MEANING; default flipped **ON** after a Cray-gated live A/B PASS (§8;
> OFF to `reorder` / ON to `emergency_source`); GOVERNED path untouched
> (governed ≠ generated). **Q4 amendment (#659):** SD-A HYBRID surface / SD-B
> 2 v1 shapes (equi-join + latest-per-group) / SD-C co-exist + parity migration
> (Phase 3) / SD-D FK + `join_path` → typed; OQ-1..4 ratified. **PLAN-0061
> (#664-#668):** grammar schema (`JoinSpec`/`ProjectSpec`) + H-governance pin +
> load gate + compile/execute (`QueryStepExecutor`, `JOIN_SHAPE_VIOLATION`),
> all offline (SD-6, NO live run), full suite **2452 / 7**. **Honest frame:**
> a DECLARING query step is declared ✔ · load-gated ✔ · execution-bound ✔ for
> the 2 v1 shapes; the 4 shipped verticals keep hand-written seeds
> (execution-bound ✖) until the Phase-3 parity-guarded migration PLAN (SD-C)
> lands — that is NEXT. `main` green + PROTECTED; 0 open PRs; loop-dispatcher
> DISABLED; MS-S1 idle; dev DB unchanged. Also on `main` this window (not this
> work): #663 `render-handoff` skill (`bb459f4`) — a parallel-session PR.

> _Rotation note (session-117 PLAN-0062 PR4 close-out reconcile, 2026-07-10,
> `docs(status):`): frontmatter bumped to `head_commit 359555b`; the s117
> PLAN-0062 Current-Focus block EXTENDED in place for PR4 #682 + close-out (no
> new session block); the s117 PLAN-0062 Recent-Decisions row EXTENDED in place
> to COMPLETE (no new row → RD holds at 10). No Current Focus block rotated (s117
> ×2 tracks + s116 + s115 = 3 sessions ≤ the 4-session window, 4 blocks ≤ 8). Two
> Active TODOs REMOVED — the discharged PLAN-0062 AC-5-erratum debt + the
> Cray-declined "one session = one git worktree" convention — and two ADDED
> (per-step QUERY router; procurement ontology↔CSV drift); the removed pair was
> emitted verbatim in the reconcile reply for the caller to append to
> `docs/status-archive/` (Bash-side). The two prior s117 rotation notes were
> consolidated into this one (R4: self-referential meta-note). Per the STATUS.md
> Rotation Policy (R1/R2/R4)._

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
| 2026-07-10 | **Flaky-DB-test isolation track — one intermittent `test_procedure_headline` failure = TWO unrelated bugs, one PRODUCTION (session 117, a CONCURRENT Code track; #678/#679/#680)** — **#678 (a) production correctness:** WSL2 `datetime.now(UTC)` is NON-MONOTONIC (2 backward steps / 20 s, −555 ms worst); `load_run` orders step results by that wall-clock `created_at` and `resume_run`/`GET /runs/{id}` read `step_results[-1]` as the suspended step → a run straddling the jump resumed from an already-COMPLETED step (re-ran a decided gate, dup side effects, stuck `waiting_human`; or "undecided proposals"); ~1 process in 20. Fixed by selecting the suspended step by **STATUS** (`suspended_step_result()`); gate/resolve never affected (looks up by caller `step_id`). **(b) test isolation (deterministic):** `Base.metadata` is import-populated → a `tests/services/db`-only process never registered `action_identity`, so `drop_all` left it for the next `alembic upgrade head` (`DuplicateTableError`); the full suite hid it. Fixed with `alembic/env.py`-mirroring registration imports + `DROP SCHEMA public CASCADE` per test. **#679:** that reset made concurrent sibling-worktree `pytest` wipe each other → test DB scoped per checkout (`vero_lite_test_<8-hex repo root>`), explicit `TEST_DATABASE_URL` still wins so CI is unaffected; control experiment (shared DB → both fail; scoped → both pass). **#680:** the "exactly one unresumed step" invariant was documented but unenforced → two such rows now raise; `get_run` answers **409** not an unhandled 500; + the HTTP-surface regression test #678 left owing. Suite 2473/7 → **2488/7**, verified on the merge commit (CI here is PR-only); ruff+format+mypy clean; offline, MS-S1 untouched, dev DB unchanged. Carry-overs → Active TODOs. | `9a12087` (#680 merge) / `7afff6a` / `8b617b0` (#679 merge) / `4f018bf` / `47a58ed` (#678 merge) / `a4593c8` / `b4b042c` / `services/engine/procedures/persistence.py` + `services/api/routers/runs.py` + `tests/db_support.py` |
| 2026-07-10 | **PLAN-0062 (Q4 Phase-3 per-vertical seed migration, parity-guarded, SD-C) — COMPLETE, all 9 ACs → `done/` (sessions 116–117; #671/#672/#673/#675/#676/#682)** — **#671 Ready** (`docs/plans/0062-*.md`): plan-drafter-authored, Code R2-verified facts 3/5/7, **SD-1..SD-6 Cray-ratified as-rec** (AskUserQuestion). **#672 PR1 (parity core, s116):** energy `read_readings` → the DECLARED latest-per-group grammar (`reads:[OperationalEvent]` + `where:{event_type:reading}` + `project:{latest_per:event_emitted_by_asset, order_by:occurred_at}`) + the shared `assert_read_step_parity` harness (grammar == an INDEPENDENT hand-coded SD-5 reference, ZERO tolerance) + SD-5-edge fixtures + a 4-vertical load-gate pin; suite 2458/7. **#673 PR1b (s117):** `EnvBandEvaluateExecutor` (binds `OCT_RECOMMEND_THRESHOLD`/`_DIRECTION` onto a band-less step, delegates to the SHIPPED `EvaluateStepExecutor`) + deterministic `advisory_stub.py` + `register_energy_procedure_executors` + `main.py` per-vertical registrar table → energy `read_readings` now **execution-bound ✔ on the production HTTP path**. **#675 PR2 (s117):** supply_chain `read_temps` over `event_concerns_shipment` + `verticals/supply_chain/procedures_factory.py`; parity harness went vertical-parameterised (SD-3); reused PR1b's `EnvBandEvaluateExecutor` + `advisory_stub_factory` UNCHANGED (same `env_band` judge, only the threshold differs — 8 °C cold-chain vs energy's 90 °C); OQ-2 settled against the data (`where:{event_type:reading}` load-bearing); suite 2473/7. **#676 PR3 (s117):** aquaculture `read_do` over `event_emitted_by_pond` + `verticals/aquaculture/procedures_factory.py` (the `main.py` registrar table's 4th/final entry); binds the shipped `EvaluateStepExecutor` UNWRAPPED (judge is `in_file_band` typed `threshold 4.0/below/watch_margin 1.0`; a test asserts `EnvBandEvaluateExecutor` is ABSENT — the `env` half of the ADR-016 D2-A3 split). All THREE OCT query steps now execution-bound ✔; procurement `intake` is declared-expressible ✔ (shadow parity, PR4) but production execution stays the co-existing `_SeedQuery` (✖ for the derived fields); `read_stock` deferred/labelled/reason-corrected. ADR-016 D2-A4 honored (env band selected by the FACTORY). **PR4 (#682, `bd8e586` → merge `359555b`):** AC-6 intake shadow-parity over the REAL `FastenalCsvAdapter` (declared join half == `_intake_seed`'s fields, derived fields ABSENT; four `PurchaseOrder`∩`Quotation` column collisions renamed to keep each quote's supplier); AC-7 `read_stock` deferral KEPT, its "no substrate" reason CORRECTED to per-`StepKind` executor routing (ERRATUM 2, Cray-ratified, pinned by an executable invariant test) → PLAN-0062 **COMPLETE (all 9 ACs)**, both errata (ERRATUM 1 = AC-5 "shipped executors" vs PR1b's `EnvBandEvaluateExecutor`; ERRATUM 2) recorded in the Close-out, `git mv`→`done/`; suite **2496/7 on the merge commit**. Both errata DISCLOSED, not silently reinterpreted. Un-gated Code build (PLAN-0062 §6); offline (SD-6), MS-S1 untouched. Full narrative: the Session-117 CF block above | `359555b` (#682 PR4 merge) / `bd8e586` (#682 feat) / `a711927` (#676 PR3 merge) / `c17500a` (#676 feat) / `624b731` (#675 PR2 merge) / `b9c5ebd` (#675 feat) / `ea08e54` (#673 merge) / `f41da9c` (#673 feat) / `8641cb3` (#672 merge) / `d9e4bd2` (#672 feat) / `66beb17` (#671 merge) / `833676e` (#671 Ready) / `services/engine/procedures/{env_band_step.py,advisory_stub.py}` + `verticals/{energy,supply_chain,aquaculture}/procedures_factory.py` + `services/api/main.py` + `tests/services/engine/procedures/test_seed_migration_parity.py` + `tests/verticals/procurement/test_intake_shadow_parity.py` + `docs/plans/done/0062-per-vertical-seed-migration.md` |
| 2026-07-09 | **PLAN-0061 join/projection-grammar build COMPLETE (all 8 ACs) → moved to `docs/plans/done/` — the ADR-016 Q4 amendment RENDERED: a query step now DECLARES multi-read equi-join enrichment + latest-per-group projection as typed authored spec — declared ✔ load-gated ✔ execution-bound ✔ for the 2 v1 shapes (session 115; #664/#665/#666/#667/#668)** — the un-gated Code build of the Ready PLAN (§6 "Steps execute directly"); ALL offline/deterministic, NO live run (SD-6 — MS-S1 never touched); every PR green through the required CI `gate`; **full suite 2452 passed / 7 skipped, ruff + mypy clean.** Chain: **#664** the SD-D substrate (`JoinKeyMeta` + ONE shared parser; `foreign_key` no longer dropped at load; `join_path` → typed) → **#665** the SD-1 lean `JoinSpec`/`ProjectSpec` schema + H-governance pin (a mid-flight edit fails CLOSED at resume) + the structural load gate (`validate_read_bindings` `meta=`; WARN-first on/fuse overrides, OQ-4) → **#666** compile + execute (`JOIN_SHAPE_VIOLATION`, OQ-1; `plan_read` `meta=` = ONE decision surface; `QueryStepExecutor` SD-1 pinned pipeline, D-N2 extended; single-read path byte-identical) → **#667** both shapes e2e over the REAL energy + procurement ontologies (SD-3 fixtures, zero vertical-file change; DB-backed JSONB-safety + governance-hash round-trip) → **#668** Ready → Complete → `done/`. The 4 shipped verticals' hand-written seeds stay execution-bound ✖ until the Phase-3 parity-guarded migration PLAN (SD-C). Full narrative: the Session-115 CF block above | `5a264d6` (#668 PLAN-COMPLETE move-to-done) / `66896e8` (#668 merge) / `e04a00b` (#667 Step 4 feat) / `0d738e1` (#666 Step 3 feat) / `93e01d1`+`7fb7497` (#665 Step 2) / `978caca` (#664 Step 1 feat) / `services/engine/ontology_meta.py` (`JoinKeyMeta` + shared parser) + `services/engine/procedures/{spec.py,orchestrator.py,query_step.py}` + `docs/plans/done/0061-join-projection-grammar-build.md` |
| 2026-07-09 | **DESIGN: ADR-016 join/projection-grammar amendment ACCEPTED (Q4 multi-read) — Phase 1 of the moat join-grammar sequence (session 115; #659)** — renders ADR-016's deferred Q4 (the 2026-07-01 OQ-5 "the multi-read join lands with Q4"; PLAN-0048 walled the grammar off as "an ADR-016 amendment"): query steps will DECLARE multi-read joins + projections as typed, authored, deterministic spec surface (today `StepInput.reads` is names-only + `QueryStepExecutor` refuses `len(reads)>1` typed). **SD-A grammar surface = HYBRID** — ontology `link_types.foreign_key` = the default join (governed, single source of truth) + a typed per-step explicit override for shapes the ontology cannot declare (the procurement `intake`'s positional singleton fusion + custom projections). **SD-B v1 scope = the 2 shipped shapes** (equi-join enrichment + latest-per-group projection; general group-by/aggregation math DEFERRED — stays the walled-off `nl_query` surface). **SD-C = co-exist + parity-guarded seed migration (Phase 3, no force-retire).** **SD-D (entailed by SD-A)** = promote `LinkTypeMeta.foreign_key` into typed form + parse ADR-0027 `join_path` into the same execution-consumable shape (projection layer only; ADR-008 grammar untouched). **OQ-1..4 ratified as-rec** (Cray, AskUserQuestion): extend `StepInput` `join`/`project`; NO repair loop in v1 (D-N2); grammar = join+projection ONLY (arbitrary computation stays downstream/seed → `intake` migrates PARTIALLY under the SD-C parity guard); warn-first override validation. **NO LLM in the read path** (LOCKED-6 / ADR-0024 D3/D6); every joined type still routes through the single `read_bound_violation` bound at BOTH load gate + run dispatch (PLAN-0048 AC-3, extended not forked). `plan-drafter`-authored (in-place amendment per the D2-Amendment precedent), Code R2-verified every cited file:line on disk (corrected a dispatch over-claim — the procurement join is declared as `quote_id→Quotation.quote_id` + transitive `part_no` via `Part`, not a literal `part_id` link). **Sequence:** this amendment → build PLAN (grammar schema + compile/execute extension + SD-D promotion) → Phase-3 per-vertical factory + seed migration. Origin: s115 Cray picked the Q4 join-grammar ADR after PLAN-0060 closed; the Phase-2 build **PLAN-0061 is Ready** (#661, `ad0f543`; SD-1..6 ratified as-rec — lean 2-construct schema, 4 phases, offline-only) | `ad0f543` (#661 PLAN-0061 Ready) / `a38acde` (#659 amendment feat) / `dbf25e2` (#659 merge) / `docs/adr/0016-governed-procedure-engine.md` (§ "Amendment (2026-07-09): join/projection grammar for multi-read query steps (Q4)") |
| 2026-07-09 | **PLAN-0060 reactive judgment handler catalog COMPLETE (all 7 ACs) → moved to `docs/plans/done/` — surface per-handler descriptions into the REACTIVE recommender judgment prompt so the model picks by MEANING, the fix for the session-114 event-bridge live-smoke FINDING (session 115; #655/#656/#657)** — the reactive judgment prompt now renders an **"Available actions" catalog** (per-handler `description`s) inside the **TRUSTED system instruction** (same trust class as the ADR-016 D5 goal), so the model distinguishes `emergency_source` vs `reorder` instead of bare handler NAMES. Registry gains a keyword-only `description` + `handler_catalog(vertical)`; the 4 handler-registering verticals (procurement / energy / supply_chain / aquaculture; vet_clinic registers none) declare `ACTION_DESCRIPTIONS`; the block reaches **both** Pattern-B calls **and** the PLAN-0020 skip path via `build_structuring_messages`→`build_reasoning_messages`; `generate_judgment` gains `include_handler_catalog` (all 3 reasoning modes); a default-off `handler_catalog_enabled` Settings flag is threaded at the reactive `recommend()` call site. `suggested_handler` enum unchanged; flag-off byte-identical; **GOVERNED path untouched (governed ≠ generated).** **#655 (Steps 1-6, offline binding bar):** full offline suite **2389 passed / 7 skipped**, ruff + mypy clean. **AC-7 live re-validate (host-state MS-S1 `gpt-oss:20b`, Cray-gated §8, evidence-only NOT a gate):** ONE controlled A/B on the s114 CNC line-down event — catalog OFF → `reorder` (reproduces the finding), catalog ON → `emergency_source` (confidence 1.0); same event, the flag the only moved variable, pass/fail pre-committed, each arm fired once. **#656 (SD-4 default flip):** `handler_catalog_enabled` default False→True after the AC-7 PASS (only `recommend()` reads it; `generate_judgment`'s param default stays False → governed path + benchmark harness unaffected; flag-off stays available). **#657:** Ready → Complete → `done/`. Origin: s115 `next-work-analyst` re-rank → Cray picked PLAN-0060 | `f6a2217` (#657 PLAN-COMPLETE move-to-done) / `0c68d58` (#657 merge) / `a81f05a` (#656 default-flip feat) / `468c3c9` (#656 merge) / `4d54683` (#655 Steps 1-6 feat) / `7c8f2e0` (#655 merge) / `services/engine/registry.py` (`description` + `handler_catalog`) + `services/engine/llm/prompt.py` ("Available actions" block in `build_structuring_messages`/`build_reasoning_messages`) + `services/engine/llm/structured.py` (`generate_judgment` `include_handler_catalog`) + `services/engine/recommender.py` (`recommend()` flag threading) + `services/api/config.py` (`handler_catalog_enabled`) + `verticals/{procurement,energy,supply_chain,aquaculture}/handlers.py` (`ACTION_DESCRIPTIONS`) + `docs/logs/2026-07-09-reactive-handler-catalog-live-revalidate.md` + `docs/plans/done/0060-reactive-judgment-handler-catalog.md` |
| 2026-07-08 | **PLAN-0059 KPI stat-tile panel COMPLETE (all 5 ACs) → moved to `docs/plans/done/` + the deferred event-bridge live-smoke FINDING recorded (session 114; B→A per Cray's directive; #649/#650/#651/#652)** — **(A, #650/#651/#652):** the hero demo's three headline ฿-impact figures — expedite premium `฿52,500` / avoided downtime `฿8.16M` / net benefit `฿8.11M` — now render as **KPI stat-tiles** over the already-shipped `GET /demo/hero/impact` ledger, with baseline→governed (`฿9.76M → ฿1.65M`) as a net-benefit-tile context sublabel; the old `kv()` rows are replaced (no duplication); no trend/target affordances. **Pure frontend composition — NO new ADR / backend / engine / payload change** (the PLAN-0057 "compose over shipped plumbing" pattern, render-only). `plan-drafter`-authored PLAN; Code R2-verified every citation + confirmed the `thb`/`thbM` formatters produce the pre-committed strings; **SD-1..SD-5 ratified as-rec** (Cray, session 114, AskUserQuestion). #651 diff confined to `services/api/static/**`, full offline suite green under the required CI `gate`, preview-verified on the hero view; #652 Ready → Complete → `done/`. **(B, #649, evidence-only §8 host-state):** the deferred event-bridge live smoke asked whether the REAL MS-S1 recommender (`gpt-oss:20b`) picks `emergency_source` for a procurement critical-asset-failure event — it chose **`reorder`** (`actor_kind=llm`, the real model engaged not the rule fallback, confidence 1.0). Root cause (offline trace): the reactive judgment prompt shows the model **bare handler NAMES only** (no per-handler descriptions / no when-to-pick guidance / `goal=None`); the distinguishing prose lives only in `procedures.yaml` step descriptions + the procedure goal, which thread into the GOVERNED path, not the reactive prompt. **Governed path + shipped hero demo (deterministic advisory stub) UNAFFECTED**; offline gates (`test_action_event_bridge.py`, `test_event_procurement_demo.py`) stay the binding bar + green. Fix (surface per-handler descriptions in the reactive prompt) = a DEFERRED next-work candidate (own PLAN, cross-vertical blast radius, then one controlled live re-validate). Origin: session-114 `next-work-analyst` re-rank → Cray picked **B → A** | `1de4d14` (#652 PLAN-COMPLETE move-to-done) / `ab02dfd` (#652 merge) / `e8a7d93` (#651 feat KPI panel) / `cffa9d1` (#650 PLAN Ready) / `f528f03` (#649 docs(logs) finding) / `services/api/static/**` (hero KPI stat-tiles) + `docs/logs/2026-07-08-event-bridge-recommender-live-smoke.md` + `docs/plans/done/0059-*.md` |
| 2026-07-08 | **PLAN-0058 COMPLETE (all 5 ACs) → moved to `docs/plans/done/` — a thin `GET /whoami` echo over the shipped fail-closed auth seam + a frontend reject-at-login probe (session 113; #645/#646/#647)** — executes the ratified **PLAN-0054 SD-A tail** (the "who am I" read named as a designed-into-seams sequel); **NO new ADR / NO new auth backend / NO change to the seam's validation logic.** Fully offline / deterministic / MS-S1-independent. **#645 (`docs(plans):`, PLAN Ready):** `plan-drafter`-authored, Code R2-verified every code citation; **SD-1..SD-4 ratified as-rec** (Cray, AskUserQuestion) — SD-1 shape `{person_id, display_name, auth_enabled}`, SD-2 fail-closed reuse `Depends(get_current_principal)`, SD-3 include the frontend wiring, SD-4 deterministic API tests. **#646 (`feat(api):`, Steps 1-3):** `services/api/models/whoami.py` (`WhoamiResponse`) + `services/api/routers/whoami.py` (`GET /whoami` injects the shared `Depends(get_current_principal)`) + `main.py` register; `tests/api/test_whoami.py` 6 deterministic cases (200 valid + display_name / 200 no-principals null / 401 no-header / 401 unknown key / 403 unmapped person / dev-escape → auth_enabled false); async `login()` probes `/whoami` (`auth.js`) → reject-at-login, `doLogin` promise-aware (`view-monitor.js`), `?v=` bump. **#647:** Ready → Complete → `done/`. **Full offline suite 2359 passed / 7 skipped**; ruff + mypy clean. **Preview-verified** on `oct-demo-procurement` (`API_AUTH_ENABLED=true`): a bad key → inline "unknown API key", NO session stored (reject-at-login e2e); good key → session stored. Origin: s113 `next-work-analyst` re-rank → Cray picked **C1 (whoami)**, now SHIPPED | `a3b7113` (#647 merge) / `cd32b02` (#647 PLAN-COMPLETE) / `fa0a187` (#646 merge) / `8eaacd1` (#646 feat) / `1734187` (#645 merge) / `847a0bb` (#645 PLAN) / `services/api/routers/whoami.py` + `services/api/models/whoami.py` + `services/api/main.py` + `tests/api/test_whoami.py` + `services/api/static/assets/{auth.js,view-monitor.js}` + `services/api/static/index.html` + `docs/plans/done/0058-*.md` |
| 2026-07-08 | **PLAN-0057 COMPLETE (all 8 ACs, live-verified) → moved to `docs/plans/done/` — the event-triggered hero-demo opener made VISIBLE over shipped ADR-0029 / PLAN-0056 plumbing (session 112; #638/#639/#640/#641)** — demo composition; NO new engine capability / NO new ADR / NO contract reshape. **#638 (Step 1+5):** `run_hero_event_governance_moment` + `build_event_hero_governance_audit` (`verticals/procurement/hero_demo/run.py`) + a service-layer test. **#639 (Step 2+4):** new `POST /demo/hero/event` (SD-2 = a new POST, NOT a param on the read-only GET) + `view-hero.js` manual↔event toggle + sense cue + `api.js` `Hero.event()`. **#640 (Step 3, AC-2):** approve→COMPLETED reveal (`renderActPanel`, client + Replay). **Live smoke Cray-approved (§8):** detected `CNC-Line-07` failure → `fire_event` → `doa_tier` gate → `appr-pm` (SoD vs `req-planner`) → COMPLETED + ฿ ledger. SD-1..SD-5 + OQ-1/OQ-2 ratified as-rec. **#641:** Ready → Complete → `done/`. Dev DB migrated `0009→0011` (Cray-approved §8) — "behind on migrations" caveat RESOLVED | `5abb1d9` (#641 PLAN-COMPLETE) / `d33fff7` (#641 merge) / `4524a29` (#640) / `8aa71c1` (#639) / `0020097` (#638) / `verticals/procurement/hero_demo/run.py` + `services/api/routers/demo.py` + `view-hero.js`/`api.js` + `tests/services/db/test_event_hero_opener.py` + `docs/plans/done/0057-*.md` |
| 2026-07-08 | **PLAN-0056 Phase B COMPLETE (Steps 6–8) → whole PLAN COMPLETE (all 12 ACs), moved to `docs/plans/done/` — the `event`/Alert-triggered governed run wired end-to-end behind a default-off ship-dark flag + LOUD-on-failure + a procurement event demo (session 111; #631 + #632 + #633 + #634)** — three un-gated Code `feat` PRs + one `docs` close, each green through the required `gate`; MS-S1-independent. **Step 6 (#631, AC-11):** `_populate_store` FEEDS an actionable recommendation INTO the governed engine in-process (ADR-0029 SD-1/SD-4) behind a **default-off `event_bridge_enabled`** flag (mirrors `verification_judge_enabled`, SD-P3); flag-off = ZERO behavior change; `event_kind = RecommendedAction.suggested_handler` (the envelope has NO `action_type`). **Step 7 (#632, AC-10, ADR-0028 D4 mirror):** a dropped/failed fire is LOUD — `event_fire_missed`/`event_fire_failed` audit + best-effort Telegram (`notify_event_fire_failed`, SEPARATE cooldown, no `llm_backend` gate), then `None` so the read path never breaks; distinct from a healthy `event_skipped`. **Step 8 (#633, AC-12):** a DISTINCT `event_emergency_sourcing_round` (trigger:event, `event_kind:emergency_source`, `owning_person_id:req-planner` SP-5 SoD) in procurement — the 7th shipped procedure (AT-2); DB-backed MS-S1-free test fires a detected asset-failure event → `build_event_resolver` → `fire_event` through the SHIPPED executor factory → parks at the DOA gate (actor_kind:service, on_behalf_of req-planner) → `appr-pm` distinct approver → COMPLETED (live smoke deferred, §8). **#634:** PLAN-0056 Ready → Complete → `done/`. **Full offline suite 2350 passed / 7 skipped**; ruff + mypy clean | `9fbc703` (#634 PLAN-COMPLETE move-to-done) / `65d9039` (#634 merge) / `f5b5c21` (#633 Step 8 feat) / `1af7928` (#632 Step 7 feat) / `02f2af9` (#631 Step 6 feat) / `services/api/routers/actions.py` (`_load_event_bridge` + `_fire_event_for_record`) + `services/api/config.py` (`event_bridge_enabled`) + `services/notify/telegram.py` (`notify_event_fire_failed`) + `verticals/procurement/procedures.yaml` (`event_emergency_sourcing_round`) + `tests/services/db/test_event_procurement_demo.py` + `docs/plans/done/0056-*.md` |
| 2026-07-07 | **PLAN-0056 Phase A COMPLETE (Steps 1–5) — the `event` trigger lifted + a typed `EventTrigger` descriptor + event-keyed idempotency + the event resolver + the governed `fire_event` bridge (session 110; #623 + #625 + #626 + #628 + #629)** — five un-gated Code `feat` PRs executed directly (PLAN-0056 Ready; §6 "Steps execute directly"), each green through the required `gate` (full CI). **Step 1 (#623, AC-1/2/3):** `Trigger.EVENT` admitted to `_RUNNABLE_TRIGGERS` — the `event` block lifted, every OTHER governance check intact. **Step 2 (#625, AC-4):** a typed `EventTrigger` mapping descriptor on `Procedure` (present iff `trigger==event`, `extra="forbid"`; carries `event_kind` + SP-5 `owning_person_id`, mirrors `Schedule`) + `_validate_event_trigger_descriptor` (symmetric iff-invariant) + `VerticalProcedures` cross-refs (`_check_event_cross_refs`, C901-extracted: owning-person → a declared Person + each `event_kind` maps to exactly one procedure — duplicate = ambiguous, caught at load). Fact-vs-code: the recommender's `RecommendedAction` has NO `action_type` → `event_kind` stays a free authored string, the match field pinned by Step 4. 783 passed. **Step 3 (#626, AC-5):** new `services/engine/procedures/event_bridge.py` — pure/offline `event_key(...)` (deterministic dedup hash → same window = same key = idempotent no-op re-fire; later window = fresh key; naive dt = UTC; `\x1f` sep) + `event_run_id → <procedure_id>@<event_key>` (the `pipeline_runs` write-ahead PK, mirrors PLAN-0055 S6). 11 tests. **Step 4 (#628, AC-6):** `build_event_resolver` (mirrors `scheduler_wiring.build_resolver`) turns a detected actionable event into an `EventRunRequest` — procedure by `event_kind` + run-by agent + SP-4 ServicePrincipal + SP-5 `owning_person` + the event-keyed `run_id` + a `trigger_context` stamp; an unmapped `event_kind` raises `EventBridgeError` loudly. Plus `EventTrigger.dedup_window_seconds` (per-mapping detection-window granularity, SD-P1, default 1h). 12 tests. **Step 5 (#629, AC-7/8/9):** `fire_event(session, request, *, now)` FEEDS the recommender's actionable detection INTO the governed engine (SD-1) — a REAL persisted `PipelineRun` via `run_procedure_persisted`, NOT the lightweight `ActionRecord` path; two skips mirror the scheduler (SD-2 idempotency → `ALREADY_FIRED` no-op via the write-ahead PK + SD-P4 skip-if-in-flight → `SKIPPED_IN_FLIGHT`, both landing an `event_skipped` audit); the service-actor audit (AC-7: actor_kind:service + SP-5 on-behalf-of), gated-park (AC-8: RF-3) + write-ahead durability inherited verbatim from `run_procedure_persisted`. New DB-backed `tests/services/db/test_event_bridge_fire.py` (5 tests). **807 passed** (procedures/db/verticals/api). **→ Phase A COMPLETE (the offline foundation); next = Phase B (Steps 6–8).** MS-S1-independent | `117e2d4` (#629 Step 5 feat) / `7da5622` (#628 Step 4 feat) / `f63f121` (#626 Step 3 feat) / `3a7bc16` (#625 Step 2 feat) / `ef7bd15` (#623 Step 1 feat) / merge tip `be190d8` / `services/engine/procedures/event_bridge.py` (`event_key` + `event_run_id` + `build_event_resolver` + `fire_event`) + `services/engine/procedures/spec.py` (`EventTrigger` + `dedup_window_seconds` + `_validate_event_trigger_descriptor` + `_check_event_cross_refs`) + `services/engine/procedures/orchestrator.py` (`Trigger.EVENT`) + `tests/services/engine/procedures/{test_spec.py,test_event_bridge.py}` + `tests/services/db/test_event_bridge_fire.py` |
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
- [ ] **A per-step QUERY router for procurement (PLAN-0062 close-out follow-up, s117).** procurement's QUERY executor is the fixed `_SeedQuery`, so a declared `read_stock` would pass the load gate and still receive the intake requisition — the true blocker behind PLAN-0062 AC-7's `read_stock` deferral (ERRATUM 2: the PLAN's "no substrate" reason was wrong — the ontology declares `Part.stock_qty`/`reorder_point` + the registry adapter emits both). A per-`StepKind` executor router would make `read_stock` migratable and **reopen PLAN-0062 AC-7**; pinned by the executable invariant `test_read_stock_is_blocked_by_per_kind_executor_routing_not_by_data` (fails when the router ships → the deferral falls due). *(s117; PLAN-0062 PR4 #682)*
- [ ] **procurement ontology ↔ CSV column drift (PLAN-0062 close-out follow-up, s117).** The procurement ontology declares `PurchaseOrder.part_no` / `Quotation.price` / `OperationalEvent.equipment_id` while the real CSVs emit `part_id` / `price_thb` / `asset_id`; the load gate checks DECLARED properties while the executor merges RUNTIME keys (the AC-6 shadow-parity test renames four `PurchaseOrder`∩`Quotation` collisions to keep each quote's own supplier). Data/ontology evolution — explicitly **out of PLAN-0062's scope**. *(s117; PLAN-0062 PR4 #682)*
- [ ] **DEFERRED: a monotonic `sequence` column on `step_results` (s117 flaky-DB track carry-over; needs a migration → own PLAN).** #678 fixed the resume/GET-run path to read the suspended step by STATUS, but two wall-clock orderings remain — `load_run` (`services/engine/procedures/persistence.py`) + the run-list `order_by(PipelineRun.started_at)` in `services/api/routers/runs.py:200` — both **DISPLAY-ONLY** now, so not urgent. The durable fix is a monotonic per-run sequence column; it needs a DB migration, so it deserves its own PLAN (PLAN-0062-independent). *(s117; #678/#680)*
- [ ] **Housekeeping (s117 flaky-DB track): 3 merged branches un-deleted + 3 stale test DBs on the dev Postgres.** Branches `fix/hermetic-db-tests`, `chore/isolate-test-db-per-worktree`, `fix/suspended-step-fail-closed` merged but not deleted; stale test DBs `vero_lite_test`, `vero_lite_test_shared`, `vero_lite_test_2cee3da7` left on the dev Postgres. Low-priority cleanup. *(s117; #678/#679/#680)*
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
