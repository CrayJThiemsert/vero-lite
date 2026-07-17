# STATUS.md — archived Current Focus blocks (2026 H1, recent window, base file)

> **Period covered:** sessions 116 → 128 (the RECENT window; appends land here)
> **Sibling chain (letters ascend with time; the base holds the RECENT window):** [`2026-h1b-current-focus.md`](2026-h1b-current-focus.md) (session 25) → [`2026-h1c-current-focus.md`](2026-h1c-current-focus.md) (sessions 26–46) → [`2026-h1-current-focus.md`](2026-h1-current-focus.md) (sessions 116–128, base). This chain is **Current-Focus-only** and is SEPARATE from the rotation archive's `2026-h1b/c/d/e/f-status.md` chain — same letter scheme, different corpus.


Archived `## Current Focus` session blocks, rotated out of `docs/STATUS.md` on 2026-06-10
(session 51) so the always-read Tier-1 STATUS stays small — it had grown to 393 KB / >25k
tokens and could no longer be read in full (a single frontmatter line was 48 KB). Full
record also in git history (Tier 3). **Tier-3: grep + windowed reads only.**

**Split lineage (session 144).** The combined file stood at 258,346 B — 1.31x R4's ~192 KB
split trigger and ~3,798 B under its 256 KB cap, still receiving appends and therefore on
track to breach with nobody watching. R4 had no mechanism until #789; this chain is what
that guard forced. **No content lost:** every session block is preserved verbatim and
exactly once, verified by exact list equality at split time, not by a byte-sum estimate.

**Two honest notes, recorded rather than quietly fixed.**
1. The pre-split header claimed the file held "Session 46 and earlier". It did not:
   sessions 116/117/127/128 had been appended at the bottom by later deep-rotates, so the
   file carried two orderings at once. This chain gives each file one coherent window; the
   original claim is preserved here as the record of what it used to assert.
2. The `session 25` block is 162,823 B on its own — 83% of R4's trigger in a single
   indivisible block. `2026-h1b-current-focus.md` is therefore large by necessity, not by
   packing choice. It is frozen; nothing appends to it.

---

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
> `read_stock` is **deferred, labelled, reason corrected** (ERRATUM 2 — the true
> blocker was per-`StepKind` executor routing, not "no substrate"; discharged by
> PLAN-0064's per-step QUERY router #696). Full PR2/PR3/PR4 detail in git history
> (#675/#676/#682) + the PLAN-0062 done/ close-out; MS-S1 untouched across s116+s117.

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


---

### Current Focus block removed — session 127 (PLAN-0071 Box-4 economic-impact ฿ facet, all 4 verticals)

> **Session 127, 2026-07-14 (head_commit `a9dbb6f` → `b11ea40`) — PLAN-0071
> (the Box-4 economic-impact ฿ facet) shipped END-TO-END across all 4 OCT
> verticals in TWO PRs + CLOSED → `done/`; the reactive AND governed
> recommenders now append an ADVISORY, trace-carried `economic_impact`
> `ReasoningStep` (baseline vs governed exposure → net ฿ benefit) — DISCHARGING
> the ADR-016 self-cancelling Box-4 N≥3 deferral with an OWNED marker (AC-5
> GREEN at N=4); the ADR-007 D2 "verbatim" envelope stays byte-untouched
> (zero-collateral).** (STATUS jumped straight here from the ADR-0030-only s126
> reconcile — the whole ADR-0030 → PLAN-0071 arc was designed to reconcile
> ONCE, now, at PLAN-0071 close.) **#731 PR1 (`81c7070`, `feat`) — engine
> core:** a new `services/engine/economic_impact.py`
> (`EconomicExposure`/`EconomicImpact` models + a NEVER-RAISE
> `build_economic_steps` emission helper) wired at BOTH `RecommendedAction`
> composition sites — `recommender._compose_llm_record` (reactive) +
> `action_step._compose_action` (governed) — appended LAST, never on
> `_rule_recommend`; the AC-5 ≥3-vertical marker landed RED
> (`xfail(strict=True)`); a conftest autouse fixture clears the
> economic-producer registry. Envelope (`services/engine/actions.py`)
> byte-untouched. **#732 PR2 (`b11ea40`, `feat`) — THE close:** four
> per-vertical ฿ producers (`verticals/<ns>/economic_impact.py`) — energy
> `avoided_outage` ฿405,000 / supply_chain `spoilage_avoided` ฿2,120,000 /
> aquaculture `mortality_avoided` ฿247,000 (all assumptions-first per SD-B/SD-G,
> every ฿ input a named `assumptions[]` entry, NO ontology/regen/migration);
> procurement `expedite_tradeoff` derived from the committed-CSV demo ledger
> (`hero_demo/ledger.py` byte-untouched), `basis_refs` cite the CSV columns,
> gated on the emergency-failure trigger (OQ-C: a calm-path event → `None`; the
> hero-PO exemplar stands in for per-event PO anchor resolution, deferred to
> v2). `discovery._register_vertical` gained a GUARDED optional producer import
> (`ModuleNotFoundError.name` checked — an absent module is skipped, a broken
> transitive import surfaces). AC-5 flipped GREEN at N=4; AC-9 GREEN (the real
> energy producer → one `economic_impact` step, net ฿405,000); the coupled-test
> audit classified every pin PINNED-UNMODIFIED. **Net (PLAN-0071 COMPLETE):**
> the Box-4 economic facet is now advisory + trace-carried across all 4
> verticals — mirroring the vero-lite advisory-trace default (confidence_signal
> / s74 no-badge / ADR-0030), ZERO ADR-007 D2 envelope change. **draft≠review≠verify:**
> `plan-drafter` PLAN → Code R2 → Cray SD-A..SD-G → Code build. **Evidence
> bar:** full suite **2591 passed / 7 skipped / 0 xfailed** WITH Postgres —
> verified on BOTH the PR head AND the merge commit `b11ea40` (CI is PR-only, so
> the re-run on the merge commit is the real gate); ruff check + `ruff format
> --check` + `mypy --strict services/` clean; deterministic-offline — no MS-S1 /
> host-state. 0 open PRs after this; tree clean (2 pre-existing untracked KEEP);
> loop-dispatcher DISABLED. PLAN-0071 `git mv`→`done/` this session;
> `docs/plans/` empty again. Commits: `81c7070` (#731 PR1 engine core) →
> `b11ea40` (#732 PR2 four ฿ producers + AC-5/AC-9 GREEN + close).

> _Rotation note (session-130 reconcile, 2026-07-14, `docs(status):`):
> frontmatter bumped to `head_commit 192dc52` (session 130); a new s130
> Current-Focus block was PREPENDED for the FOUNDATION/GOVERNANCE work
> (plan-drafter rigor hardening #740 + ADR-0031 "core lifecycle architecture"
> Accepted #741). **NORMAL reconcile** (no size pressure — comfortably under the
> R1 ceiling): with s130 prepended, Current Focus held 5 sessions (s130 + s129 +
> s128 + s127 + s126), so the OLDEST — the whole **session-126** block (ADR-0030
> Accepted #728: the Box-4 economic-impact ฿ facet — typed, ADVISORY,
> trace-carried — DISCHARGING the ADR-016 self-cancelling Box-4 N≥3 deferral at
> N=4; a doc-only, contract-only governance batch, NO code/tests) — was rotated
> OUT to keep the 4-session window (now s130 + s129 + s128 + s127). Recent
> Decisions rotated its OLDEST row (2026-07-12 **s120** — `threshold_field`
> per-entity band shipped END-TO-END, ADR-016 amendment → PLAN-0066 Ready →
> build #703/#704/#705; procurement `judge_stock` bands each `Part` vs its OWN
> `reorder_point`) to keep the 10-row window. Both were emitted verbatim in the
> reconcile reply for the caller to append to
> `docs/status-archive/2026-h1-status.md` (Bash-side). **Backlog update:** the
> Box-4 economic-impact ฿ arc stays COMPLETE across engine + UI (through s129);
> s130 shipped NO feature — it hardened the drafter (#740) and ratified the
> core-lifecycle architecture (ADR-0031, #741) that pre-designs each core's ONE
> typed policy-carrying seam for its N≥2 trigger. Prior rotation notes (through
> the session-129 reconcile) are consolidated into this one (R4). Per the
> STATUS.md Rotation Policy (R1/R2/R4)._

> _Older content rotates out of this file per the **STATUS.md Rotation Policy (R1-R6)** in [`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md) (Lesson #23): Current Focus keeps the 4 newest sessions (<=8 blocks); Recent Decisions keeps the last 10 rows. Rotated blocks/rows live in [`docs/status-archive/`](status-archive/) (sessions <=46: `2026-h1-current-focus.md`; 2026-06-10 onward: `2026-h1-status.md`) and git history (Tier 3)._

*Rotated 2026-07-15 (session 131 reconcile — s131 PLAN-0074 entry prepended; CF window kept at 4 sessions [128–131] under the 64 KB R1 ceiling).*

*Rotated 2026-07-15 (session-132 reconcile) — Current Focus block, session 128:*

> **Session 128, 2026-07-14 (head_commit `b11ea40` → `88e6984`) — PLAN-0072
> (the Palantir-lite hero demo's beat-3 "run it" step) shipped END-TO-END +
> CLOSED → `done/` in ONE session-128 day (#734 Ready → #735 build): the hero
> demo's "run it" beat now GENUINELY resolves the parked DOA gate through the
> REAL production `POST /runs/{id}/gate/resolve` route, rendering the PERSISTED
> truth — replacing the prior FAKE front-end badge.** `next-work-analyst` ranked
> the options → Cray picked **D3** (make beat-3 genuinely resolve); `plan-drafter`
> authored + re-scoped PLAN-0072, Code R2, Cray ratified
> **SD-A(b)/SD-B(b)/SD-C(a)/SD-D(a)** via AskUserQuestion, then built + closed the
> same session. **#734 (`85f90ed`, `docs(plans)`) — PLAN-0072 Ready.** **#735
> (`88e6984`, `feat`) — THE build** (demo wiring, NO engine change). **Backend:**
> the event opener additively exposes the parked `run_id` on its `hero` dict;
> **generation-aware replay (SD-C)** — a DECIDED (approved OR rejected → both
> COMPLETED) fixed-key run bumps `detected_at` by one hour to cross the 3600 s
> event-dedup bucket and fire a FRESH parked run, clock-free (a COUNT of decided
> runs). **SD-A(b):** the demo drives the PRODUCTION resolve route with
> `api_auth_enabled` + a real authenticated `appr-pm` Person (RF-1 end-to-end) —
> NO new endpoint. **Frontend:** `renderActPanel` reworked — **SD-D(a)** inline
> login (authenticate THEN sign), **SD-B(b)** Approve AND Reject, renders the
> persisted `GateResolveResponse` (approve → COMPLETED + SoD tie; reject → the
> honest shipped semantics "no PO, decision recorded, run completed" — reject =
> continue+record, NOT a rejected terminal); `api.js` gains `Hero.runDetail` +
> `Hero.resolve`; `?v=` cache tokens bumped. **Build-discovered production bug
> (disclosed correction to AC-6):** the resolve endpoint's SoD-403 path did
> `asdict(exc.verdict)` whose `SoDViolation.constraint_steps` is a frozenset —
> un-serializable → Starlette 500 MASKED the 403 (procurement is the FIRST
> frozenset-bearing SoD verdict to reach this HTTP path). Fixed in
> `services/api/routers/runs.py` (JSON-sanitize the verdict, frozenset → sorted
> list); **security posture INTACT** — the SoD check fails CLOSED before
> serialization (run stays parked, `gate_refused` audit written), only the
> response CODE was wrong, never a bypassed gate. **OQ-4 resolved:** the AC-4
> reject test proves `event_emergency_sourcing_round`'s downstream steps tolerate
> an empty executed-effect set (a rejected run resumes to COMPLETED).
> **draft≠review≠verify:** `plan-drafter` PLAN → Code R2 → Cray SD-A..SD-D → Code
> build. **Evidence bar:** 5 new AC tests GREEN (approve→COMPLETED / SoD tie
> persisted / wrong-approver 403 + unauth 401 + still-parked + `gate_refused`
> audit / reject→COMPLETED no-effect / generation-aware replay); full suite **2596
> passed / 7 skipped** WITH Postgres — verified on BOTH the PR head AND the merge
> commit `88e6984` (CI PR-only, so the merge-commit re-run is the real gate); ruff
> check + `ruff format --check` + `mypy --strict services/` clean; preview
> (oct-demo-procurement) confirms the new Act panel renders the inline-login UI
> with no console errors (supporting evidence — the deterministic backend test is
> the gate). Deterministic-offline (no MS-S1 / host-state); Postgres for the
> DB-backed AC tests only. 0 open PRs after this; tree clean (2 pre-existing
> untracked KEEP); loop-dispatcher DISABLED. PLAN-0072 `git mv`→`done/` this
> session; `docs/plans/` empty again. Commits: `85f90ed` (#734 PLAN-0072 Ready) →
> `88e6984` (#735 feat build + close).
