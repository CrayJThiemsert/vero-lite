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

### Current Focus block removed — sessions 149 + 150 (PLAN-0082 shared-ontology mechanism + Person promotion, #801–812) [rotated 2026-07-21, session-156 reconcile — 4-block window]

> **Sessions 149 + 150, 2026-07-19 (head_commit `0b67f76` → `043da3c`) —
> PLAN-0082 (the shared-ontology mechanism + `Person` promotion) BUILT
> end-to-end, then COMPLETE + archived, across both sessions (#801–812), with
> PLAN-0081 folded — and governance behaviour UNCHANGED throughout.** **The moat
> piece:** a shared `core` ontology home + an `imports:` grammar with cross-doc
> `core.<Type>` resolution + a `set`/`closed` type-system extension across all
> emitters + a shared `Person` (type + committed ORM + `person` table + Alembic
> migration) reconciled down to exactly ONE definition. **(s149 — build half,
> #801–808).** Filed PLAN-0082 `Status: Draft` (#801) + folded the SD-round
> (#802 — SD-F/G/H/I/K + OQ-1); **ADR-0033 Accepted (#803, `6dd6464`)** — the
> shared-ontology ADR + ADR-0008/0026 pointer notes, OQ-1=(a) JSONB. Steps 2–4:
> **#804** `ontology/core_v0.yaml` + the reserved `core` namespace + set/closed
> L1/L2; **#805** the Pydantic emitter (set→`frozenset` / closed→`extra=forbid`);
> **#806** the `imports:` grammar + qualified cross-doc `core.<Type>` resolution
> (no KeyError); **#807** set→JSONB across the SQL/ORM/JSON-Schema/TS emitters;
> **#808 (`5e45eb6`)** the committed shared Person ORM `services/db/person.py` +
> the `person` table + Alembic `0012` — RAN GREEN on dev Postgres. Additive
> throughout — zero shipped-behaviour change. **(s150 — reconciliation half,
> #809–812).** **Step 5 (#809)** reconciled the spec-layer `Person` onto the
> committed generated `core.Person` (SD-H=(a) = delete + re-export; Cray s150
> design = a1): the committed-dest mechanism was extended to the Pydantic emitter
> (`_PYDANTIC_COMMITTED_DEST["core"] → services/engine/procedures/person_model.py`),
> parallel to the committed ORM; the AC-4 one-`Person` grep guard was proven
> non-vacuous empirically. **A CI-scope miss caught + fixed:** the offline gate
> ran only the 3 changed files + engine/db tests, but CI runs `mypy services/`
> STRICT tree-wide — `--no-implicit-reexport` flagged 12 consumers of the plain
> re-export → fixed with the redundant-alias idiom (`import Person as Person`);
> lesson recorded (the offline gate must match CI scope). **Step 6 (#810)**
> migrated procurement + supply_chain onto the shared type (AC-5) + transformed
> the OQ-6 marker (AC-6). **Grounding collapsed the handoff's "LARGE dual-roster"
> work to SMALL:** AC-5's TYPE-unification was ALREADY satisfied by Step 5's
> re-export (every roster parses into the one shared `spec.Person`;
> `auth.py`/factory/`run.py` already read the shared seam — nothing to
> re-point). **AC-5 RE-SCOPE (Cray s150):** the "retire one of procurement's dual
> roster sources" clause was a MISREAD — `procedures.yaml` (the Thai SoD roster)
> and `person.csv` via `load_fastenal_principals` (the Fastenal LIVE-run demo
> roster) are DISTINCT demos, not redundant copies; retiring either deletes a
> demo (violates AC-5's own "verdicts may not change" bar). Neither retired,
> documented; classified **`superseded by new info`** (CLAUDE.md §6). The marker
> became a shared-type invariant (no re-arm at N=4), non-vacuity proven. **Step 7
> (#811, `e059303`)** — PLAN-0082 COMPLETE: all 7 ACs ticked against fresh
> on-disk evidence + a Closeout Verification block, `git mv` →
> `docs/plans/done/0082-*.md`. **PLAN-0081 fold (#812)** — SD-J=SPLIT resolved +
> executed: Step 9 shrunk to the `building_materials` residue, AC-7 re-pointed to
> PLAN-0082 AC-6, AC-12/13/14/15 → PLAN-0082 AC-1/2/3/4, OQ-1 → ADR-0033;
> **PLAN-0081 stays `Status: Draft`.** **Verification:** full offline suite
> **2888 passed / 7 skipped**, re-run on EACH merge commit; every existing
> SoD/tier/gate-resolve assertion UNMODIFIED. **OQ-2 (the `person`-table
> population story) stays OPEN + explicitly deferred** (the table ships empty,
> runtime roster-fed). **PLAN-0081 is UNBLOCKED** (Step 9 = land
> building_materials on the shared `Person`); the hero build stays uncommissioned
> beyond PLAN-0079's tracking stub. Post-merge: main=`043da3c`; 0 open PRs;
> loop-dispatcher DISABLED; MS-S1 idle/COLD (zero calls all session); dev
> Postgres UP (localhost:5442). Commits: `5e45eb6` (#808 merge, s149 tip) →
> `92f0019` (#809) → `c94d089` (#810) → `e059303` (#811) → `043da3c` (HEAD,
> #812 merge).

### Current Focus block removed — session 151 (PLAN-0081 building_materials governed-credit HERO, the 3rd AT-2 signature, #814) [rotated 2026-07-21, session-157 reconcile — 4-block window]

> **Session 151, 2026-07-19 (head_commit `043da3c` → `9422c40`) — PLAN-0081
> BUILT end to end: the `building_materials` governed-credit HERO — the **3rd
> AT-2 signature** (`building_materials.governed_credit_release`) — then
> PLAN-0079's tracking stub RETIRED (Step T3) + PLAN-0081 archived; governance
> behaviour UNCHANGED (#814).** Cray COMMISSIONED the hero this session
> (AskUserQuestion, after next-work-analyst ranked it #1); PLAN-0079 Step T1 was
> already fired (s146), so this session paid the BUILD. **The hero:** an
> exposure breach ABOVE the account's own `credit_limit_thb` routes the full
> governed AT-2 spine — per-entity band → `rule_gate` (KYC / overdue-AR /
> blacklist) → `doa_tier` human approval + SoD (sales requests, credit-control
> approves); steps intake → judge → reshape → credit_gate → approve → fulfill;
> the ฿550,000 shipped breach routes mid-ladder (`ผจก.ควบคุมเครดิต`), demoing
> tiering not just the top. **The 3rd signature REUSES, it does not re-invent:**
> the money `doa_tier` ladder is reused UNCHANGED (no new gate kind, no new
> authority quantity) — only the criterion vocabulary grows (`ComplianceCriterion
> += {kyc, overdue_ar, blacklist}`). **The ADR-0025 D7 re-evaluation was
> PERFORMED at N=3** (verdict Cray-ratified: the generator stays deferred,
> `test_at2_signature_retrigger.py` re-arms at N=4). **Engine diff bounded** to
> the additive `ComplianceCriterion` block (`spec.py`) — the `Person` promotion
> was PLAN-0082's dependency (already on main), so this PR carried NO engine
> `Person` edit; principals parse into the shared `core.Person` and the
> one-`Person` guard holds. **Coordination:** the endpoint pin bumped 9 → 10
> procedures + the spec-less guard re-pointed to a fixture vertical
> (building_materials is no longer spec-less); the archetype catalog + map gained
> the 3rd AT-2 signature; new AC tests
> `tests/verticals/building_materials/test_governed_credit_hero.py`
> (AC-1/2/4/5/9 — the in-memory run reaches the `doa_tier` gate, `waiting_human`).
> **Closeout (AC-10):** PLAN-0079 tracking stub RETIRED (Step T3) → `done/`, its
> guard test `test_governed_credit_hero_tracking_guard.py` DELETED, the STATUS
> Active-TODO pointer retired; **PLAN-0076 T1's gate-seam trigger recorded MET**
> (its own process owns the seam PLAN — not opened here); PLAN-0081 archived →
> `done/` at 15/15 ACs + a Closeout Verification block. **Honest flag:**
> `DoaLadder` REQUIRES an `emergency_waiver` (ADR-0025 D3) and
> `RelaxableConstraint` is a closed enum AC-3 forbids extending, so the
> procurement-shaped waiver is reused (GUESS-marked, not exercised on the happy
> path). **Verification:** full offline suite **2896 passed / 7 skipped** (re-run
> on the merge commit `9422c40`); `mypy --strict services/ verticals/` clean;
> ruff clean; CI `gate` PASS — deterministic-offline, MS-S1 never called, no
> host-state. Post-merge: main=`9422c40`; 0 open PRs; loop-dispatcher DISABLED.
> Commits: `a46bef8` (#814) → `9422c40` (HEAD, #814 merge).

> **Session 152, 2026-07-19 (head_commit `9422c40` → `a53c6ed`) — PLAN-0083
> (fix option c1) BUILT + verified + archived: the procurement ontology↔CSV
> column drift is CLOSED at the adapter seam (#818).** The `FastenalCsvAdapter`
> now translates raw Fastenal CSV columns → canonical ontology names via
> `_COLUMN_RENAMES` on the `fetch_objects` path — the type key
> `Asset`→`Equipment` (SD-1) plus columns `part_id`→`part_no`,
> `price_thb`→`price`, `asset_id`→`equipment_id`, `site`→`site_id`,
> `lead_time_days`→`lead_time`, and `PurchaseOrder.asset_id`→`equipment_id`
> (SD-4a); the ฿-columns (`total_thb`/`min_thb`/`max_thb`) are DEFERRED raw
> (SD-4b). So every consumer now sees ONE canonical vocabulary (the ontology's),
> closing the bring-your-own-data seam. **Rides under ADR-016's LOCKED boundary**
> ("the mapping layer absorbs source diversity; connectors-in-the-procedure OUT")
> — **no new ADR, no ontology YAML edit, no generated regen, no `services/`
> engine edit** (ADR-0023 zero-core-edit; diff = adapter + vertical + tests only).
> A new coverage tripwire (`test_fastenal_adapter_canonical_coverage.py`) pins
> per-type set-equality + required-props + rename-target ontology validity + the
> type-key + the SD-4b ฿-defer, proven non-vacuous EMPIRICALLY (dropped a rename
> → RED → reverted). Cray COMMISSIONED C3 this session via `next-work-analyst`
> (which ranked the drift item), then ratified (c1) + SD-1..SD-4 via
> AskUserQuestion. **R2 caught** that the PLAN under-scoped
> `governance_audit.py:177/179` (reads the renamed PO columns off the adapter) —
> added, within AC-5 scope. **Verification:** full offline suite **2915 passed /
> 7 skipped** (baseline 2896 + 19 tripwire); `mypy --strict services/ verticals/`
> clean (142 files); ruff clean; CI gate PASS on #818. Deterministic-offline;
> MS-S1 never called; dev Postgres UP (localhost:5442). Post-merge: main=`5140ee3`;
> 0 open PRs; loop-dispatcher DISABLED. Also **#816** pruned the stale ORM-emitter
> Active-TODO (resolved by PLAN-0082 Step 4). Commits: `a211651` (#818 build) →
> `a53c6ed` (#818 merge) → `8b76da2` (#819 closeout) → `5140ee3` (HEAD, #819
> merge).

> **Sessions 153 + 154 + 155, 2026-07-20 (head_commit `a53c6ed` → `25b31e2`) —
> the demo-beat runbook staged (#822), a strategy read that CUT the tempting
> part (s154, zero commits), the operator confidence badge REMOVED from
> both cards that carried it (#823), and the late-s155 PLAN-0084 arc: filed
> (#825) → all 5 SDs Cray-resolved (#826) → BUILT end-to-end (#827) —
> map↔monitor run linkage + opt-in seed rotation + the SD-F Fastenal-adapter
> swap.** **(s153) Two docs PRs, no code.** **#821
> (`0248ec1` → merge `b45f5c4`, `docs(status)`)** was a housekeeping prune:
> the "Standard partner-intake form" Active TODO CLOSED (the deliverable
> exists and is canonical at `docs/conventions/partner-intake-form.md:8`; its
> per-vertical generalization is deferred to Rule of Three **BY DESIGN, not
> incomplete**), plus the stale `ADR-011+` / `PLAN-002 (>=ADR-014)` pointers
> dropped from Next Steps 1 and 3 — Next Steps had been **contradicting Active
> TODOs two sections up** (both were already corrected at s141). It
> deliberately did NOT bump session/head_commit/recent_commits (pure prune, Q4
> semantics), which is why s152 stayed the last real reconcile. **#822
> (`90a2afb` → merge `d8057fb`, `docs(runbook)`)** is the SUBSTANTIVE one and
> had never been reflected in STATUS until now: `docs/runbooks/run-oct-demo.md`
> §3c stages the **config-pin fail-closed refusal as a deliberate demo beat
> (Beat 06)** per PLAN-0047 Step 6 — the refusal is the product, so it gets
> rehearsed, not hidden. Both PRs sat blocked mid-session on a GitHub-Actions
> outage and landed when CI recovered (~09:34 +07).
> **(s154) ZERO repo commits — strategic analysis only.** Cray brought the
> Cerebras enterprise-knowledge-base article and asked whether vero-lite should
> adopt that approach to grow beyond governance into org-wide monitoring +
> prediction + warning-with-alternatives. Code read **ADR-0032 first** (the §2
> mandated pre-strategic read), then ran 4 read-only specialists in parallel,
> all grounded `file:line` against code. Verdicts: (1) predict+warn+alternatives
> is **NOT a new direction** — it is OCT feature 3 / Shape-1, passing the D6 fit
> filter IF prediction stays **deterministic**; (2) a KB over vero-lite's OWN
> governed artifacts is **D3 Shape-2 fuel verbatim** → pilot-gated by OQ-1; (3)
> org-wide Slack/wiki ingestion is the only genuinely new part **and the part to
> CUT** (fails D6 ~0/4, hits the named refused archetype, DPO-veto surface); (4)
> the surviving reframe = **"governed retrieval over the decision record — an
> answer an auditor accepts"**. The live blog URL 500'd everywhere, so Cray
> saved the page manually and Code re-verified the digest-based analysis against
> the real article: **all 4 verdicts `confirmed — prior intact`**, deltas were
> refinements only. Highest-value delta: the blog gives its authn/authz/audit
> layer ONE bullet and zero design detail — **retrieval quality is the published
> commodity; governance OF retrieval is the uncovered lane.** Artifacts are
> gitignored under `docs/research/private/cerebras/`.
> **(s155, this session) `next-work-analyst` + the badge removal (#823,
> `fix(ui)`).** A full 4-agent Explore fan-out ranked post-rehearsal work; Cray
> commissioned item #1. **#823 (`f09cc99` + `ffb251b` → merge `4edfa3f`) removed
> the operator-facing confidence badge from BOTH cards that carried it**,
> executing the already-ratified demo-card trust shape
> (`docs/plans/done/0035-governed-action-verify-reshape-build.md:591-602`,
> Cray-approved s74, re-recorded s142, cited by ADR-0030: "No operator-facing
> confidence badge"). `f09cc99` removed the hardcoded "Confidence 86%" + meter
> from the story-mode scene-2 governed-action card and the same number from the
> proposal-card meta; **`ffb251b` removed the same badge from the View-B
> "Anomaly & Decision" card, where it was driven by a LIVE `rec.confidence` —
> the more load-bearing instance**, since that file is the operator
> recommendation card the decision actually names. **KEPT by design:** confidence
> inside the reasoning trace (trace-only is the point), the fault-mode `AI 0.41
> ↓ → rule fail-safe` badge (it narrates the reroute MECHANISM, not a self-graded
> score), and the DAG task-detail row (engine-view). `.dc-metarow` collapsed from
> a 2-column grid to 1 so the handler fills the row rather than stranding a dead
> half; orphaned `.gc-conf-top` / `.dc-conf-top` / `.dc-conf-val` rules removed;
> comments at every site cite the decision so the badge is not reintroduced.
> Files: `view-story.js`, `view-anomaly.js`, `story.css`, `views.css`,
> `index.html` (cache tokens bumped) — **static assets only**, no engine/API/
> contract change, ADR-007 D2 envelope untouched. **Verification:** full offline
> suite **2915 passed / 7 skipped** on each commit AND re-run on the merge commit
> `4edfa3f` (CI is PR-only, so the merge commit is otherwise never tested); mypy
> clean (97 files); ruff clean; CI `gate` PASS on #823. Live browser check on
> port 8101 with the connection strip reading **`LIVE`** (not `degraded`): the
> View-B card rendered through the real `decisionCard()` path with a fixture
> deliberately carrying `confidence: 0.86` — proving the badge is gone **even
> when the signal IS present**; `.dc-handler` measured 414/414 px against its row.
> **Four claim-vs-code corrections surfaced by the grounding pass (the session's
> durable finding):** **(a)** the s154 research note recommended running a
> naive-RAG comparison "before building anything", but **PLAN-0027 ALREADY ran
> it** (scored 2026-06-16, `benchmarks/procedure_baseline/REPORT.md:697-771`) and
> the answer is that arm (c) lean RAG **TIES** arm (a) governed on entity+action
> accuracy (97.5% vs 97.5–100%) at **3–15x lower latency** — the moat claim was
> already relocated OFF raw accuracy ONTO the governance layer; **(b)** "the
> actions router is fully governed" is an **overstatement** — `append_audit` is
> called once in a failure-alert helper, approve/execute never call it, and that
> router's own GET endpoints are as ungoverned as `/query`; **(c)** the
> "ADR-0031 tripwire" cited for a learned forecaster is the **wrong ADR** —
> ADR-0031's tripwires are eval/open-StepKind/untyped/enum-widening, while the
> real determinism line is **ADR-0019:50-57 + ADR-010 IN-3**, and a deterministic
> trend projection sits on the **PERMITTED** side so long as it stays advisory;
> **(d)** a 4th AT-2 signature is currently **unbuildable** — no vertical has the
> substrate (energy + aquaculture are AT-1/AT-1b with no principals, no SoD, zero
> money/authority ontology fields; vet_clinic is a parked README) — and ADR-0032
> D1/D6 argues against scoping one absent a named partner. **Also flagged for the
> demo:** the UI **silently serves MOCK data on any backend error**
> (`services/api/static/assets/api.js:37-39` routes any non-ok/non-JSON response
> to `fallback()`), so a rehearsal can pass entirely against fake data — **the
> only tell is the connection strip.** Post-merge: main=`4edfa3f`; 0 open PRs;
> loop-dispatcher DISABLED; MS-S1 idle/COLD (zero calls across all three
> sessions). Morning commits: `0248ec1` (#821) → `b45f5c4` (#821 merge) →
> `90a2afb` (#822) → `b1d7f5a` → `d8057fb` (#822 merge) → `f09cc99` →
> `ffb251b` (#823) → `4edfa3f` (#823 merge).
> **(s155 late) The PLAN-0084 arc — filed, SD-ratified, and BUILT end-to-end
> in one afternoon/evening (#825 → #826 → #827).** **#825 (`1b2c05c` → merge
> `628bfa1`, `docs(plans)`) filed PLAN-0084** (`Status: Draft`): map↔monitor
> run linkage + opt-in seed rotation — the demo-coherence ask Cray made
> mid-rehearsal; scope Cray-ratified via AskUserQuestion ("Flow + หมุน asset
> เดิม"; server-side object injection REJECTED) + PLAN-first routing. Authored
> by plan-drafter from Code's grounded dispatch; the drafter corrected Code's
> own fact-pack TWICE (RunSummaryView, not "RunListItem"; the event path's
> engine-side `trigger_context` stamp pinning CNC-Line-07, which matches no
> map pk). **#826 (`edf922d` + `f6bb12c` → merge `e5f3ede`, `docs(plans)`)
> resolved ALL FIVE SDs** (Cray, AskUserQuestion): SD-A typed subject on
> list+detail; **SD-B ALL FOUR non-hero assets rotatable (wider than rec** —
> CNC-009 cheap because `link_asset_uses_part` LNK-AUP-003 already binds it
> to the hero part); SD-C a distinct "governed run in flight" marker,
> waiting_human+running; **SD-D execute option (d) IN-PLAN (wider than rec)**
> — both demo entry points light the map, the `_EVENT_ASSET_ID` re-pin
> superseding PLAN-0057 OQ-1; SD-E newest-first cap 5. Step 0 SATISFIED. Two
> commits because the L1 same-file loop-detect interrupted the drafter's
> batch (3 restating edits landed in commit 2 after the counter reset — fully
> disclosed in the PR). **#827 (`45fcba1` + `64119b9` → merge `25b31e2`,
> `feat(demo)`) BUILT PLAN-0084 end-to-end + SD-F.** The build: seed stamps
> `trigger_context["subject"]` from the computed intake seed; `RunSubjectRef`
> + optional `subject` projected fail-soft on RunSummaryView AND
> RunDetailView; the map ingests `/runs` via a Monitor-style direct fetch
> (never the mock-fallback O.API path); assets with in-flight runs get the
> dashed amber ring; the node panel gains "Governed runs · in flight" with
> per-run "Open in Monitor →" buttons; `ViewMonitor.focusRun` + the
> `oct:goto {view:'H', run}` wire; Step 4b re-pin + the entity_ids→subject
> projection through a lazily-cached pk→object_type index (data-driven, no id
> map); rotation via `--asset`/`--rotate` with an ASSET-KEYED failure pick
> (row-order dependency killed); fixtures = one failure event per rotatable
> asset + 3 quotes each for three previously quote-less parts + the CNC-009
> PO (฿78,500 → the 50k–500k band); runbook §3d (rotation flags, the
> live-verified tier→approver table, the beat-1 cue now naming AST-CNC-014,
> the "strip must read LIVE" rule). **SD-F — the headline finding,
> Cray-ratified mid-build: the PLAN's grounding was WRONG (`was an error`,
> recorded in the PLAN)** — the map never rendered the hero CSV: the
> registered procurement adapter was the scaffold-era synthetic set
> (`equip-*`, 4 anonymous assets) while every hero surface narrates Fastenal
> (`AST-*`, 5 named assets) — the demo was already split-brain and the
> subject could light nothing. Cray: **"Fastenal เป็น adapter หลักของ
> procurement ทั้งหมด"** — `register_procurement_adapter` (discovery) now
> registers the `FastenalCsvAdapter`; the swap required the `plant.csv` geo
> anchor (without it the map has no mappable objects), `stock_qty`/
> `reorder_point` on `part.csv` (the calm-path chain runs over the registered
> adapter; synthetic semantics preserved EXACTLY incl. the PLAN-0066 AC-6
> >100 flip case as PRT-BLT-110 150/160), and four test repins (the
> PLAN-0083 canonical-coverage tripwire caught the new Part keys — working
> as designed; calm-path 3→5 rows; scheduled-demo verdicts; shadow-parity
> expected side JSON-sanitized for Decimal). Fastenal serves `[]` for
> unserved types + streams no events → GET /recommendations stays empty,
> matching the observed pre-swap demo; the synthetic adapter stays in-tree
> for direct-module harnesses. **Live verification (port 8101, strip LIVE,
> zero console errors):** AC-4 full click-through (map node → panel → button
> → View H with `run-row-run-s155-linkage` SELECTED); AC-9 (POST
> /demo/hero/event → the event run projects subject {Equipment, AST-CNC-014}
> and lights the map; the panel listed event + seeded runs newest-first);
> AC-5 (/runs forced 500 → map renders fully, zero markers, no mock
> fallback); AC-7 live (ROBOT-21 ฿99k→appr-pm; CONV-05 ฿7.2k→appr-buyer — a
> genuinely different tier; unknown asset lists the 5 rotatable); AC-2
> legacy fail-soft proven with the REAL morning run (subject: null). AC-1:
> full offline suite **2922 passed / 7 skipped**, re-run and CONFIRMED on the
> merge commit `25b31e2` itself (CI is PR-only, so the merge commit is otherwise
> never tested) — baseline 2915 + 7 new tests; mypy strict 142 files; ruff clean.
> **PLAN-0084 status: Draft, all 6 SDs resolved, ACs deliberately UNTICKED —
> closeout (tick + archive) is a named next step after Cray's rehearsal
> passes on the new build.** Post-merge: main=`25b31e2`; 0 open PRs;
> loop-dispatcher DISABLED; MS-S1 idle/COLD (zero calls all day). Late-s155
> commits: `1b2c05c` (#825) → `628bfa1` (#825 merge) → `edf922d` + `f6bb12c`
> (#826) → `e5f3ede` (#826 merge) → `45fcba1` + `64119b9` (#827) →
> `25b31e2` (HEAD, #827 merge).

> **Session 156, 2026-07-21 (head_commit `25b31e2` → `2f46fc9`) — a morning
> map-label UI fix, a long-carried demo rehearsal finally PERFORMED (the
> PLAN-0084 closeout gate), and the AI-Transition View-1 / Rung-1 arc built
> end-to-end in ONE day: PLAN-0085 "Advisory Gate Recommendation" filed (#831)
> → all 5 SDs Cray-ratified (#832) → BUILT (#833) → closed out (#834).**
> **(morning UI fix — #829, `19f5caa`, `fix(ui)`.)** On the Operational Map
> (View A) the site label plate overlapped the rightmost asset satellite node;
> the plate moved BELOW the node (the asset fan is always the upper hemisphere),
> `view-map.js ?v=c39` — live-verified on 8101 (0 overlaps, strip LIVE).
> **(the rehearsal — the closeout gate.)** Cray performed the demo rehearsal
> (Beats 1-5 on 8101, incl. the new PLAN-0084 map→monitor opening beat) —
> carried s153→154→155, finally run, ratified "ok" = PASS. No commit: it IS the
> AC-4/closeout evidence for **#830** (`ad39774`, `docs(plans)`) — PLAN-0084
> closed out, all 9 ACs ticked with dated evidence, archived to `done/` (the
> PLAN was Draft, so Code closed it directly). (The rehearsal-artifact PREP +
> Beat-06 wording was corrected + republished, but that is a gitignored
> claude.ai working note, not a repo commit.) **(the two-view AI-Transition
> frame — Cray-opened after the rehearsal.)** Two views: (1) an LLM at the
> approval gate, (2) a narrative→pipeline scaffolder. Cray ratified a SEQUENCE —
> capture a discussion note → build View-1 (Rung 1) → reshape View-2 against
> Rung-1's result → build View-2 — under the umbrella thesis **AI Transition =
> governance human in/on-the-loop → first-stage AI automation**. Captured in the
> gitignored note
> `.claude/handoffs/session-156/2026-07-21-0851-code-session156-discussion-ai-transition-two-views.md`
> (binds nothing). **(PLAN-0085 — the View-1 / Rung-1 arc, filed → SDs → built →
> closed, one day.)** **#831** (`8809776`, `docs(plans)`) filed PLAN-0085
> "Advisory Gate Recommendation (AI-Transition Rung 1)" `Status: Draft` by
> `plan-drafter` (grounded by 3 Explore fan-outs + Code's OQ-1 read; the drafter
> corrected the dispatch twice, both re-verified at R2). **#832** (`d679036`,
> `docs(plans)`) — Step 0: all 5 SDs Cray-ratified (AskUserQuestion), every pick
> = the draft recommendation — **SD-1(b)** emit INSIDE the `doa_tier` gate
> propose path (ZERO hash change), **SD-2(b)** stub-first deterministic arm +
> opt-in live MS-S1 seam, **SD-3** all three procedures, **SD-4** gate-panel
> advisory block, **SD-5** new trace kind `advisory_recommendation` (actor
> `llm`). **#833 (`2f46fc9`, `feat(engine)`) BUILT:** an advisory recommendation
> with grounded reasons at procurement's `doa_tier` approval gate — **SHOWN,
> never routes** (the ADR-0019:50-57 fence, now CI-pinned: byte-identical
> approve audit advisory-on / off / exploding-builder). New module
> `services/engine/procedures/gate_advisory.py` (never-raise, ADR-0030 D5
> pattern), wired via `GovernanceActionExecutor` + the procurement `_executors`
> default; a Monitor gate-panel block (reasons, spark glyph, arm sublabel, NO
> score — the L-C/#823 trust shape) + the new trace kind + a PLAN-0080 tripwire
> pin. Suite **2927/7**, mypy/ruff clean, live-verified on 8101 (strip LIVE, the
> run parks with the advisory persisted). **#834** (`63009c3`, `docs(plans)`) —
> PLAN-0085 closeout: all 8 ACs ticked, runbook §3e added, archived to `done/`.
> Cray confirmed the live advisory and surfaced an UNPLANNED value — it doubles
> as an **onboarding aid** (a first-time operator reads a plain-language "why
> this is on my desk", reducing panic), recorded as a signal for the View-2
> scaffolder reshape. **A model-economy policy** was ratified (a private memory,
> not a repo change): Fable reserved for complex planning/research, Opus 4.8 +
> Extra for execution/coding-to-plan. Post-merge: main=`63009c3` (head_commit
> pins `2f46fc9`, the #833 build — the last SUBSTANTIVE code commit, mirroring
> the s155 head-of-record convention; #834 is a `docs(plans)` closeout); 0 open
> PRs; loop-dispatcher DISABLED; MS-S1 idle/COLD (the advisory arm is stub-first
> deterministic — zero live calls). Commits (per-PR): `19f5caa` (#829) →
> `ad39774` (#830) → `8809776` (#831) → `d679036` (#832) → `2f46fc9` (#833
> BUILT — head_commit of record) → `63009c3` (#834 closeout, main HEAD);
> `recent_commits` interleaves the five merge commits.

> **Session 157, 2026-07-21 (head_commit `2f46fc9` → `79358c6`) — PLAN-0086
> COMPLETE: the AI-Transition **View-2** scaffolder run as a TIMED MANUAL
> baseline — a rambling, deliberately-dirtied customer monologue carried to a
> live, governed, human-gated pipeline on a 6th vertical (`fleet_maintenance`,
> #838), shipped with its measurement pack; and the ADR-0025 D7 AT-2-generator
> deferral CANCELLED at N=4.**
> **(the headline number — it MUST NOT be quoted without its caveat; AC-7 makes
> that binding.)** Narrative → governed pipeline in **27 minutes 39 seconds
> hands-on** (wall 43m17s minus 6m51s of customer-answer waits and 8m48s stopped
> on a governance escalation). **Caveat (AC-7, binding):** Code drafted the
> pre-dirtied narrative, so this is a **LOWER BOUND on true blind intake** —
> Cray's dirtying plus the four-question intake log partially restore validity,
> and it measures an operator with deep prior knowledge of this codebase.
> **(what shipped.)** `verticals/fleet_maintenance/` — an 8-file package
> HAND-WRITTEN from the `building_materials` template (`vero-lite new-vertical`
> was banned by the measurement protocol). Asset=Truck, Site=Depot; AT-2
> `governed_repair_approval`: intake → judge (per-truck repair ceiling) →
> reshape → quote_gate (`rule_gate`) → approve (money `doa_tier` + SoD) →
> fulfill. **First vertical shipping the PLAN-0085 gate advisory ON by default**
> (PLAN-0086 L-B — the parked gate explains itself on day one). Plus 14 tests,
> the 3 mandatory hand-wires, and an additive `ComplianceCriterion +=
> three_quote` engine change.
> **(ADR-0025 D7 — the AT-2-generator deferral is CANCELLED; Cray-ratified,
> typed.)** Shipping fleet fired `test_at2_signature_retrigger` at N=4. Code
> ESCALATED rather than patched — the marker says "re-argue it, do not just
> update this list", and the fix Code judged correct was also the fix that turned
> Code's own red green. Both readings went to Cray: by gate SHAPE fleet teaches
> nothing new (composition and authority quantity identical to
> `building_materials`'), but it is the FOURTH consecutive vertical to require an
> engine-level `ComplianceCriterion` extension — and repeated pressure on shared
> code is what Rule-of-Three actually watches. Cray's rationale: accept the cost
> now for future flexibility. The `len(signatures) < _RETRIGGER_N` guard is
> RETIRED and REPLACED (never deleted) by `test_at2_extraction_obligation_is_owned`
> (same module), which fails if PLAN-0076 — the standing owner via Step T1 — is
> archived or loses its record. **The extraction itself is NOT done — it needs
> its own PLAN, G2-gated, so `plan-drafter` must author it.** That is the most
> important open thread out of this session.
> **(the finding that outlives the number.)** Two of the four customer rules
> could NOT be fully encoded: the quote-comparison ฿ threshold has nowhere to
> live (a `rule_gate` criterion is pass/fail on a supplied signal and carries no
> threshold field, and ADR-0025 D4 forbids the amount in prose), and
> `EmergencyWaiver` has no fields for the emergency cap or the ratification
> window. Both are recorded in the question log and surfaced to readers in the
> vertical README as an explicit "stated but NOT enforced" table — a
> narrative→pipeline tool that silently dropped the un-modellable half would be
> worse than no tool.
> **Verification:** offline gate at execution HEAD **2943 passed / 7 skipped**,
> **re-run GREEN on the merge commit `79358c6` itself** (2943/7 — CI is PR-only,
> so the merge commit is otherwise never tested); baseline re-measured at
> `219a134` before the clock started (2927/7, matching the #833 figure —
> `confirmed — prior intact`); `mypy --strict services/` clean (98 files);
> `ruff check .` + `ruff format --check .` clean at CI scope; CI `gate` PASS on
> #838 (3m7s; 17 files, +1825/−40). **AC-4 by construction** — the diff touches ZERO files under the
> five existing verticals. Live: `run-b9c0804b52f0` parks `waiting_human` at
> `approve` with the advisory persisted (grounded fleet reasons, `model:
> deterministic`, no confidence key in the advisory), corroborated in the Monitor
> gate panel and confirmed by Cray. PLAN-0086 archives to `done/` in the
> follow-on closeout PR. Commits: `a2ef45e` (#838) → `79358c6` (HEAD, #838
> merge).

---

## Rotated this reconcile (session-163 second arc, 2026-07-22 — the PLAN-0090 pass)

### Current-Focus block — Sessions 158 + 159 (PLAN-0087, the ADR-0031 D3 gate seam's criterion-vocabulary half, #840/#841) [rotated 2026-07-22, session-163 second-arc reconcile — 4-session CF window]

Rotated because **R2 requires it**, not as a headroom judgement: with the Session-163 block added, the 4 most-recent sessions are 163 / 162 / 161 / 160, so this block fell outside the window.

> **Sessions 158 + 159, 2026-07-21 (head_commit `79358c6` → `e55f2b8`) —
> PLAN-0087 BUILT (#840) then CLOSED OUT + archived at 8/8 ACs (#841): the
> ADR-0031 D3 gate seam's **criterion-vocabulary half** is SHIPPED —
> `ComplianceCriterion` is RETIRED from engine code and a vertical now
> **declares** its own `rule_gate` vocabulary, so a new AT-2 vertical ships its
> gate with ZERO engine diff.**
> **(what shipped — s158, #840.)** `VerticalProcedures.compliance_criteria:
> list[CriterionId]` (`spec.py`) — pattern-constrained by the `CriterionId`
> type and membership-validated at load by `_validate_compliance_criteria`;
> only the four `rule_gate` verticals were migrated (`energy` + `aquaculture`
> YAMLs are absent from the diff entirely).
> **(the claim is PROVEN, not asserted.)** AC-1's proof pair: a fixture
> criterion `zzz_fixture_only_sourcing_check` that exists NOWHERE under
> `services/` loads through the real `load_procedures_file` and gates through
> the real `evaluate_compliance`, while its undeclared twin is REFUSED at load;
> a repo-grep static guard keeps the id confined to that one test module.
> **Behaviour-preserving:** no pinned governance hash moved — the declaration
> block sits outside the pin surface (the `principals` precedent).
> **(the scope split — Cray-ratified SD-1 = (a), typed.)** This discharges the
> criterion-vocabulary half of **PLAN-0076 Step T1 (F-FACTORY)** only; the
> procedure-aware `ExecutorFactory` half stays OPEN and still owned by
> PLAN-0076, so **PLAN-0076 does NOT archive** and its AC-6 presence guard
> stays ARMED — **no guard re-homing occurred, deliberately**. ADR-0031 D3
> row 3 was updated on landing per D4.4 — exactly one table row, which was
> AC-7's whole obligation.
> **(the closeout — s159, #841.)** `git mv docs/plans/0087-*.md
> docs/plans/done/`, Status `Draft` → **COMPLETE** (never flipped to
> `Accepted` — an `Accepted`-status PLAN is G1-gated for its own closeout), all
> 8 ACs ticked, plus a new **Closeout** section recording (a) the evidence read
> at closeout time and (b) what was deliberately left undone. Every AC was
> re-read against **fresh on-disk evidence** rather than carried over from the
> build session's notes — CLAUDE.md §6 ("Verification is hygiene, not a
> verdict") double-gates `confirmed — prior intact` on the pre-committed
> pass/fail read AND a fresh artifact.
> **(deliberately NOT done, and recorded as such in the PLAN.)** PLAN-0076 is
> **NOT** archived (T1's factory half open; §B item 1 — F-PIN's new-run
> re-routing threat — open by construction), so its guard stays armed.
> `scored_rule._KNOWN_CRITERIA` was NOT opened: zero extension pressure to
> date, and its shape is `derive`-grammar-like, not vocabulary-like. The stale
> `N=2`/`N=3` doc drift in ADR-0025 D7 + ADR-0032 was NOT folded in — s157
> expected it to ride along with PLAN-0087's G1-gated edits, but AC-7 obligated
> that one ADR-0031 row and nothing more; it now needs its own small
> `plan-drafter` dispatch.
> **Verification:** the suite walked **2943/7 → 2951/7 → 2954/7** across the
> build and re-ran GREEN on the merge commit `c6eec65`. Gate re-run at closeout
> on `main = c6eec65`: full suite **2954 passed / 7 skipped** (169.91s) and
> `mypy --strict services/` clean (98 source files) — **matching the build
> session exactly**; the four doc-reading guard tests re-ran green after the
> `git mv` (84 passed). Deterministic-offline: **MS-S1 idle/COLD, zero calls in
> both sessions**, no host-state change, no demo/dev server started; dev
> Postgres `vero-postgres` UP (localhost:5442 — evidenced by only 7 skips).
> `main` protected; **#841 is the only open PR**; loop-dispatcher DISABLED;
> working tree clean but for the 2 KEEP untracked paths
> (`.claude/benchmark-results/`, `.claude/launch.json`). Commits: `d9a0ad1` →
> `16c3622` → `bdd07ed` → `4f9cb7a` → `c6eec65` (HEAD of `main`, #840 merge) →
> `e55f2b8` (#841 closeout, head_commit of record).

<!-- rotated 2026-07-22, session-164 reconcile -->

> **Session 160, 2026-07-22 (head_commit `e55f2b8` → `0c9cdeb`) — a four-PR
> hook-hardening + doc-truth session: the Stop-hook classifier gained a
> **contentless-reason FLOOR** (#844) complementing the s159
> Cray-reserved-step rule (#843), the stale **AT-2 `N=4`** count was corrected
> everywhere it had drifted and the real `step_id` invariant pinned by a new
> guard (#845), and two Accepted-ADR bodies were corrected by `plan-drafter`
> (#846).**
> **(#843, `c8f7184` → merge `0090161`, `fix(hooks)` — recorded LATE.)** This
> landed in session 159, but the s159 reconcile never mentioned it (it was
> written before the PR existed; the s159 handoff flags the omission
> explicitly). The Stop-hook classifier prompt now treats **a step reserved for
> Cray as a natural stop, never a PROCEED next action**, pinned by a contract
> test proven non-vacuous by strip → RED → restore.
> **(#844, `532d3e4` → merge `c42abe4`, `fix(hooks)` — the CONTENTLESS-REASON
> FLOOR.)** The hook passes the classifier's `proceed` reason back to the agent
> **verbatim as its continuation instruction**, and the prompt requires that
> reason to NAME the next action — nothing enforced it. Session 160 observed the
> reason `"Continue to the next work step"` on a turn whose only real next step
> was Cray's decision among unratified candidates. **This is the COMPLEMENTARY
> shape to #843, not a regression of it:** #843 forbids *naming* a
> Cray-reserved step; a contentless reason names nothing, so #843's rule has
> nothing to bite on, and its contract test is four substring assertions on the
> prompt (behaviourally blind). New `_reason_is_contentless()` demotes such a
> verdict to pause. The design call that keeps it free of judgement: **a
> contentless reason is worthless even when `proceed` is CORRECT**, because the
> reason IS the instruction. It is a FLOOR, not a specificity judge —
> `_META_REASON_TOKENS` excludes every real action verb (guard-tested), and the
> OTHER s159 directive ("Continue running the test and mypy suite on the merged
> commit") still passes verbatim as the committed calibration pin. A **missing
> `reason` key** now demotes too (the old fallback was the literal
> `"continue"`). Also adds the gold case `pause-long-batch-then-question`:
> `gpt-oss:20b` already answers the existing short-question case correctly
> (19/20), so the live miss is a **fixture FIDELITY gap, not a model gap** —
> real payloads are a large work batch with the question only at the tail of the
> 8-turn / 3072-byte window. **+20 tests.**
> **(#845, `66b9707` + `b5272e2` → merge `d7bbb8b`, `chore` — the stale AT-2
> N-count, plus a new guard.)** AT-2 is **N=4** (`procurement` /
> `supply_chain` / `building_materials` / `fleet_maintenance` declare a
> `rule_gate` vocabulary; `energy` + `aquaculture` do not). Corrected in
> `spec.py` (×3 sites), `docs/conventions/procedure-archetypes.md`, and **the
> test module's own docstring** — the last two were NOT in the original scope:
> the drift was wider than recorded, and PLAN-0086 had shipped
> `fleet_maintenance` **without extending the archetype catalog** (its
> Quick-reference row and Instances list still enumerated three signatures —
> fixed in `b5272e2`, found during #846's R2). **Two corrections worth keeping
> as facts, not prose:** (a) `_RETRIGGER_N` is **retired and guards nothing**
> (its own docstring says so) — the live tripwire is the `_BASELINE_SIGNATURES`
> set-equality assertion, RED on a FIFTH signature; (b) PLAN-0087's "zero live
> `step_id` collisions today" is **wrong** — collisions already exist
> (`procurement` reuses `intake` / `approve` across three procedures); what is
> zero is the **over-mark**. New
> `tests/services/engine/procedures/test_sod_step_id_scope_guard.py` pins the
> real invariant (a step is in the vertical-flat `sod_steps` union **iff** its
> OWN procedure declares it), because `GovernanceStepExecutor.sod_steps` is a
> bare per-vertical `frozenset[str]` with no procedure key and nothing raises on
> an over-mark; it carries a second test so the guard cannot silently become
> vacuous. This hardens the premise **PLAN-0076 Step T1 (F-FACTORY)** defers on.
> **(#846, `25110c8` → merge `0c9cdeb`, `docs(adr)` — two Accepted-ADR body
> corrections, authored by the `plan-drafter` subagent (G1-gated), Code R2.)**
> **ADR-0032**'s "Where vero-lite stands" is a STATE snapshot and had drifted on
> more than N: it still said `building_materials` was a Tier-1 Mirror with **no
> `procedures.yaml`** and an unbuilt hero, counted four verticals, and did not
> know `fleet_maintenance` existed. It now reads six verticals, the
> governed-credit hero BUILT (PLAN-0081), fleet named, the full N=4 arc, and
> **symbolic anchors replacing the rotted line-number ones**. Its
> positive-consequences bullet — which claimed the ADR record makes exactly this
> stale-N-count error class harder to reintroduce, **while itself being stale**
> — was rewritten to say the durable guard is **the test, not the prose** ("the
> tripwire is CI; the ADR is the narrative"). **ADR-0025 D7's decision text was
> deliberately NOT rewritten** ("N ≥ 2" is the faithful 2026-06-28 record;
> editing a decision to match later events destroys the reasoning lineage) — a
> dated **outcome amendment** was appended instead, following the amendment
> precedent already in that ADR. **Attribution corrected by the drafter against
> Code's own dispatch:** **Cray** cancelled the D7 deferral, typed, 2026-07-21
> (s157), at the PLAN-0086 N=4 escalation; PLAN-0087 only **executed** the
> answer.
> **(deliberately NOT built.)** The second s159 tripwire — **tripwire B, the
> PLAN-0076 AC-6 F-PIN arm** — was NOT built: the grounding REFUTED its
> mechanism. The guard checks **file presence, not T1 text**, so it cannot
> self-release; it can only be deleted by hand, and a tripwire against a hand
> deletion buys nothing.
> **Verification:** both new tripwires proven non-vacuous **empirically** —
> backed up to `/tmp`, broken, **RED confirmed**, then restored **from the
> backup, never from git** (the s159 trap: a `git checkout` restore wipes the
> uncommitted edit under test and the run still prints a pass),
> `md5sum`-verified. Merge-commit gate against a pass/fail read fixed **BEFORE**
> the run — expected `2955 + 20 + 2 = 2977`; actual on `0c9cdeb` = **2977 passed
> / 7 skipped** (164.66s) + `mypy --strict services/` clean (98 files) ⇒
> `confirmed — prior intact`. Branch protection is **`strict: true`** —
> discovered while landing the stack (each remaining PR went `BEHIND` after a
> merge and needed a re-sync + a fresh `gate` run); it substantially closes the
> old "CI is PR-only, so the merge commit is never tested" gap. Grounding for
> the whole session came from a **5-agent Explore fan-out over 6 candidates**
> (the `next-work-analyst` skill), which is what surfaced the corrections above.
> Deterministic-offline: **MS-S1 idle/COLD, zero calls**, no host-state change;
> dev Postgres UP; loop-dispatcher DISABLED; **0 open PRs**; working tree clean
> but for the 2 KEEP untracked paths (`.claude/benchmark-results/`,
> `.claude/launch.json`). Commits: `c8f7184` → `0090161` (#843 merge) →
> `532d3e4` → `c42abe4` (#844 merge) → `66b9707` + `b5272e2` → `d7bbb8b` (#845
> merge) → `25110c8` → `0c9cdeb` (#846 merge, head_commit of record). The three
> `Merge remote-tracking branch 'origin/main'` sync commits (`d852ab1`,
> `329bfac`, `39a37d4`) are strict-mode re-sync noise and are excluded from
> `recent_commits`.

## Rotated this reconcile (session-166, 2026-07-23 — the dispatch-quality + Lesson #0032 closeout, #866)

### Current Focus block removed — Session 162, 2026-07-22 (PLAN-0089 fleet AT-3 calm path filed→built→archived + the #850 `PROCEDURE_ARCHETYPES` re-key, #850–#853) [rotated 2026-07-23, session-166 reconcile — 4-session CF window]

> **Session 162, 2026-07-22 (head_commit `e6bb8c8` → `1b942f5`) — a four-PR
> arc, two of it recorded LATE: #850 (the `PROCEDURE_ARCHETYPES` re-key) and
> #851 (PLAN-0089 filed) both merged during s161 and were never mentioned by
> the s161 reconcile; then PLAN-0089 was BUILT (#852) and CLOSED at 6/6 ACs +
> archived (#853, merged at the s163 open). The headline: `fleet_maintenance`
> gained the AT-3 calm path `pm_service_round` in **~14 min hands-on**, with
> **ZERO engine diff — PROVEN, not asserted** (`git diff df1982a..a8d679d --
> services/engine/` is EMPTY).**
> **(#850, `333f6f6` → merge `514dc1f`, `fix(api)` — recorded LATE, built by a
> spawned chip session, not the main one.)** `PROCEDURE_ARCHETYPES` was keyed
> on a bare `procedure_id`, but a `procedure_id` is unique only *within* a
> vertical (`services/engine/procedures/schedules.py:31-33`), so two verticals
> naming a procedure alike silently served each other's archetype —
> demonstrated repro: `energy` asking for `low_stock_reorder_round` received
> **procurement's AT-3**. A latent pre-existing bug, not a regression: the
> canonical catalog had always used `<vertical>.<procedure_id>`, so the mirror
> had drifted off its own canonical. Re-keyed to **`(vertical,
> procedure_id)`**, with a new `archetype_for()` as the single read point and a
> set-equality tripwire; +3 tests. The non-vacuity probe was done the right
> way — the old shape restored from a `/tmp` backup, never `git checkout`
> (which would have wiped the edit under test and produced a false PASS).
> **(#851, `f1cce45` + `fa43e6b` → merge `df1982a`, `docs(plans)` — also
> merged during s161, also recorded LATE.)** **PLAN-0089** filed: the fleet PM
> calm path as a *measured* "extend an existing vertical" experiment, with all
> **3 SDs Cray-ratified inline** — SD-1 manual trigger, SD-2 manual hand-port
> (no generator), SD-3 ride `Truck` with an **absolute**
> `next_service_due_km`, take the **third** truck, and name it
> `pm_service_round`, never `tire_*`.
> **(#852, `2904d77` + `610061b` → merge `a8d679d`, `feat(fleet_maintenance)`
> — PLAN-0089 BUILT.)** `fleet_maintenance.pm_service_round`, the **AT-3 calm
> path**: `read_odometer` → `judge_service_due` (`threshold_field:
> next_service_due_km`, `direction: above`) → gated `schedule_service`. Cray's
> **M-5 intake this session**: a 100,000 km service interval, all classes. +4
> tests; the counted-prose census moved **11 → 12**.
> **(#853, `b1d877f` → merge `1b942f5`, `docs(plans)` — merged at the s163
> open, head_commit of record.)** PLAN-0089 closed out `Draft` → **COMPLETE at
> 6/6 ACs** against fresh on-disk evidence, with a Closeout section, and
> archived to
> `docs/plans/done/0089-fleet-calm-path-extend-an-existing-vertical.md`.
> **(the measured number + its BINDING caveat.)** ~14 min hands-on to extend an
> existing vertical; the log lives at
> `docs/research/private/2026-07-22-fleet-extension-timing-log.md` —
> **gitignored, cite by path only**. **M-6 travels with the number and is
> BINDING: it is a lower bound under maximally favourable conditions, and it
> must NEVER be summed with PLAN-0086's 27m39s as one workflow.**
> **(what the instance taught the archetype.)** AT-3's catalog entry was too
> narrow and was **GENERALIZED** — "read stock, judge vs a reorder point" →
> "read a measure, judge vs a per-entity threshold". This instance **inverts
> the direction** (odometer *above* a ceiling vs stock *below* a floor), which
> is exactly what showed the archetype's signature is the **per-entity band +
> single gate**, not stock semantics. **N stays 4:** the AT-2 signature counter
> counts AT-2 signatures only, and `pm_service_round` is AT-3 — invisible to
> that counter by construction.
> **Verification.** Whole surface `df1982a..1b942f5` = 11 files / +496 / −37.
> AC-3's zero-engine-diff is proven by the EMPTY `git diff df1982a..a8d679d --
> services/engine/` (re-verified this session), not by prose. Offline gate on
> the merge commit `a8d679d`: `pytest tests/` = **2978 passed / 8 skipped / 5
> failed** — the 5 are the known **pre-existing worktree false-REDs** in
> `tests/handoffs/` (they pass in the main tree and in CI), not a regression;
> `mypy --strict services/` clean (98 files); ruff clean. **AC-5 live park
> (evidence, never a gate):** `run-0c69e3054102` read back from Postgres —
> `waiting_human` at `schedule_service`, verdicts `{truck-01: ok, truck-02:
> breach, truck-03: ok}`, handler `schedule_pm_service`, trace kinds
> `['action_proposed']` ONLY — **no** `advisory_recommendation` /
> `doa_tier_resolved` / `governed_kind`. That absence is **BY CONSTRUCTION,
> not by never-raising**: `GovernanceActionExecutor.execute` branches on
> `step.governance_content` and delegates straight to the base executor, and
> the advisory builder is invoked only inside `_doa_tier`
> (`services/engine/procedures/governance_step.py:183-191`, `:235-238`).
> **Process fact worth one clause (no commit).** A parallel session had already
> filed AND merged PLAN-0089 while s162 dispatched its own `plan-drafter`
> draft — caught only at `git fetch` before committing. Standing correction:
> `git fetch origin main` + `gh pr list --state open` **before** drafting any
> governance artifact. Commits: `333f6f6` → `514dc1f` (#850) → `f1cce45` →
> `fa43e6b` → `df1982a` (#851) → `2904d77` → `610061b` → `a8d679d` (#852) →
> `b1d877f` → `1b942f5` (HEAD of `main`, #853 merge, head_commit of record).


### Current Focus block removed — Session 161, 2026-07-22 (PLAN-0088 cross-run read substrate + run-insight readers filed Draft, #848) [rotated 2026-07-23, session-166 reconcile — 4-session CF window; includes the s163-era rotation-trail notes that sat inside the span]

> **Session 161, 2026-07-22 (head_commit `0c9cdeb` → `e6bb8c8`) — a one-PR
> strategy-to-PLAN session: PLAN-0088 filed Draft (#848, `docs(plans)`) — the
> cross-run read substrate + run-insight readers. Cray's opening question (once
> we have enough pipeline-run data, how do those data + the ontology feed an LLM
> to create customer value?) grounded out to ONE architectural shape, not a menu
> of features: the repo records everything PER-RUN and aggregates NOTHING across
> runs.**
> **(the grounded finding.)** `pipeline_runs` / `step_results` already carry
> `step_principals`, `governance_snapshot`/`_hash`, `duration_ms`, `artifact`,
> `reasoning_trace` and `audit` per run — but the only SQL aggregate anywhere in
> `services/` is the audit-chain length count
> (`services/api/routers/audit.py:54`), and `GET /runs`
> (`services/api/routers/runs.py:273-331`) materializes **every** run into
> Python and counts steps in dicts. That read path does not survive the "enough
> run data" premise, so the substrate — not a feature list — is the work.
> **(two forks Cray ratified by typed selection; they are the PLAN's LOCKED
> constraints.)** **L1 — "Group A" is NOT Shape 2** (NL query over runs, ฿ ROI
> narrative, bottleneck / cycle-time, audit-readiness): it emits no typed
> improvement proposal, so it extends Shape 1's `monitor` leg and does **not**
> trip the **ADR-0032 D2 pilot gate**. The separation test is **mechanical, not
> documentary** — AC-11 is a static guard over the substrate, the insights
> router and the run-query compiler asserting no write primitive, no import of a
> five-symbol proposal/write-path deny-list (each symbol verified on disk), and
> no `sqlalchemy` import engine-side. **L2 — build Group A and *prove* the
> substrate can express Group B's questions; do NOT build Group B.** Group B
> (band/DoA recalibration, refusal mining, procedure generation) **is** Shape 2
> and stays pilot-gated; the proof is four executable query-shape tests (AC-10),
> not prose.
> **(two hazards PINNED, not inherited.)** **Run ordering is unsound by the
> code's own admission** (`runs.py:291-294`: `started_at` "is a wall clock that
> is not monotonic on this box"), and the deferral doctrine pinned in
> `tests/services/db/test_load_run_ordering_guard.py:29-49` says the
> monotonic-sequence-column fix deserves its own PLAN — *"if a correctness path
> ever starts depending on either ordering, the sequence-column PLAN stops being
> optional."* PLAN-0088 therefore stays on the safe side: order-insensitive
> aggregates only, day-or-coarser buckets, no cross-row wall-clock arithmetic,
> plus an AST tripwire (AC-3) forbidding `ORDER BY` on raw wall-clock columns.
> **The sequence-column PLAN is explicitly still UNOPENED.** Second hazard:
> **cross-currency sums are made unrepresentable, not merely checked** — the ฿
> rollup's group key structurally includes `currency`
> (`EconomicImpact.currency`, `economic_impact.py:63`; THB-only in v1 per
> ADR-0030 OQ-4) and the report model carries **no cross-currency total field**.
> **(process note — the drafter corrected the reviewer three times and was right
> each time.)** The PLAN was authored by the in-harness `plan-drafter` (ADR-013
> D1) from a Code-authored, Cray-ratified dispatch; Code reviewed it against the
> code in **two rounds** and ordered three amendments (corpus vertical scoping,
> test-corpus size, a runnable predicate for AC-11). The drafter corrected two
> line ranges in Code's own dispatch and — substantively — the framing of the
> currency risk: Code's R2 tied it to vertical separation; the drafter separated
> cross-vertical **scope** (a business-honesty risk → stamp the report with the
> declared vertical) from cross-currency **summation** (a correctness risk → key
> on the facet's own `currency`). Vertical separation was never the right guard
> for currency, even accidentally.
> **(also this session, no commit — recorded because it is evidence for a
> standing candidate.)** The Stop hook emitted a directive `reason` **twice** on
> turns where nothing had been ordered: first *"Continue drafting ADR-0032
> content"* (work Code is G1-gate-forbidden to do), then *"Proceed with
> reconciling the status of s160 and rotating the s157 note"* (real pending work,
> but picking one branch of a two-option question Code had just put to Cray).
> Code declined both. **Neither shape is caught by #844's contentless-reason
> floor** — both name a concrete action, and the floor only demotes a reason that
> names none. Direct material for the still-missing
> `.claude/autonomy-triggers.md` approval/merge row.
> **Verification:** #848 is docs-only (1 file, +505 lines) — CI `gate` PASS in
> 3m12s, SHA-verified (run head == PR head ==
> `0dce906c48395ce9e11dee71e6503f030eda0066`) before merge; no suite re-run
> needed (docs-only). Artifact:
> `docs/plans/0088-cross-run-read-substrate-and-run-insight-readers.md`, **Status
> `Draft`** — deliberately not `Accepted`, which would G1-gate the PLAN's own
> closeout. Commits: `0dce906` (build) → `e6bb8c8` (HEAD of `main`, #848 merge,
> head_commit of record — `docs(plans):` counts as substantive; only
> `docs(status):` is excluded).

> _Rotation note (session-164 reconcile — the PLAN-0091 filing, 2026-07-22,
> `docs(status):`): added the **Session 164** CF block and rotated the OLDEST —
> the **Session 160** block (the four-PR hook-hardening + doc-truth session,
> #843 / #844 / #845 / #846) — to the Current-Focus rotation base
> `docs/status-archive/2026-h1-current-focus.md`. Rotating it is what **R2
> requires**, not a headroom judgement: the 4 most-recent sessions are now **164
> / 163 / 162 / 161**, so the s160 block fell **outside** the window. CF
> arithmetic: **4** real blocks → +1 = 5 → −1 = **4 blocks** (well under the
> 8-block cap). _(A naive `^> \*\*Session` grep over-counts: a WRAPPED line
> inside a rotation note also starts that way; the real headers carry a date and
> a `(head_commit …)`.)_ Recent Decisions gained ONE row — the s164 PLAN-0091
> filing, written at ≤600-char pointer length **from birth** — and rotated its
> ONE OLDEST, the **s153-155** row (#822's runbook demo beat / s154's
> zero-commit Cerebras-KB read / #823's confidence-badge removal), to the
> rotation base `docs/status-archive/2026-h1-status.md`; RD is back to **10
> rows**. The rotation-note trail was carrying **two**; this pass rotates the
> OLDER (the first session-163 reconcile note) to the same base and adds this
> one, so the trail stays at **two**. **Nothing was re-trimmed:** the R2
> pointer-rule pass landed in #854 (s163) and the RD rows plus Active TODOs are
> already at pointer length. **STATUS was 55,745 B before this reconcile**
> (caller-measured); the net of this pass is a SHRINK — one CF block and one
> rotation note out, one CF block and one note in — and the caller re-measures
> against the 64 KB R1 ceiling. Per the STATUS.md Rotation Policy (R1/R2/R4)._
>
> _Rotation note (session-163 reconcile #2 — the PLAN-0090 arc, 2026-07-22,
> `docs(status):`): added the **Session 163 (second arc)** CF block (PLAN-0090
> filed #855 → BUILT #856 → CLOSED at 7/7 #857, on top of #854's reconcile +
> pointer trim) and rotated the OLDEST CF block — **Sessions 158 + 159**
> (PLAN-0087, the ADR-0031 D3 gate seam's criterion-vocabulary half, #840/#841)
> — to the Current-Focus rotation base
> `docs/status-archive/2026-h1-current-focus.md`. Rotating it is what **R2
> requires**, not a headroom judgement: the 4 most-recent sessions are now **163
> / 162 / 161 / 160**, so the s158+159 block fell **outside** the window. CF
> arithmetic: **4** real blocks → +1 = 5 → −1 = **4 blocks** (well under the
> 8-block cap). _(A naive `^> \*\*Session` grep over-counts by one: a WRAPPED
> line inside the session-161 rotation note also starts that way; the real
> headers carry a date and a `(head_commit …)`.)_ Recent Decisions gained ONE row
> — the s163 PLAN-0090 arc, written at ≤600-char pointer length **from birth** —
> and rotated its ONE OLDEST, the **s152** row (PLAN-0083, the procurement
> ontology↔CSV column drift closed at the `FastenalCsvAdapter` seam, #818/#819),
> to the rotation base `docs/status-archive/2026-h1-status.md`; RD is back to
> **10 rows**. The rotation trail carried **two** notes: the older —
> **session-161 reconcile** — was rotated to the same base (R4 consolidation) and
> this note added, so the trail stays at **two**. **Nothing was re-trimmed:** the
> R2 pointer-rule pass landed in #854 earlier this same session, and the Active
> TODOs plus the remaining RD rows are already at pointer length. **STATUS:
> 55,745 B** (caller-measured, not estimated), against the 64 KB R1
> ceiling. Per the STATUS.md Rotation Policy (R1/R2/R4)._

## Rotated this reconcile (session-167, 2026-07-23 — the autonomy fork RESOLVED, A′ demotes the dispatch arm, #870/#871)

### Current Focus block removed — Session 163 (second arc), 2026-07-22 (PLAN-0090, the fleet AT-3 scheduled calm path) [rotated 2026-07-23, session-167 reconcile — 4-block CF window]

> **Session 163 (second arc), 2026-07-22 (head_commit `1b942f5` → `1ce3546`) —
> a four-PR arc that filed, BUILT and CLOSED **PLAN-0090** inside one session:
> the fleet AT-3 **scheduled** calm path. Headline —
> `scheduled_pm_service_round` fires at 06:00 Asia/Bangkok as the
> `svc-fleet-scheduler` service principal and PARKS at the gated
> `schedule_service` for a human (RF-3), and its steps are **BYTE-IDENTICAL** to
> the manual `pm_service_round` — PROVEN, not asserted, by
> `test_spine_is_byte_identical_to_the_manual_path`, which compares dumped
> models, so a changed projection / `threshold_field` / direction / handler /
> autonomy / facet on either path goes RED. **Cadence is a trigger property, not
> a governance one:** the only difference between the two procedures is HOW a
> run starts.**
> **(#854, `06a93f0` → merge `2d34d80`, `docs(status)`.)** The s162 reconcile,
> bundled with the **R2 pointer-rule trim**: 9 RD rows + 6 Active TODOs
> compressed to ≤600-char pointers, and one Active TODO **RETIRED as discharged
> because it was FALSE, not stale** — s160's #845/#846 had already corrected all
> three artifacts it named. 59,697 → 53,758 B; headroom 5,839 → 11,778.
> **(#855, `bd44842` + `5e88450` → merge `20f2585`, `docs(plans)`.)** PLAN-0090
> filed, with the Step-0 SD ratifications recorded inline. The path is a
> **DISTINCT `procedure_id`, never a trigger flip** — the procurement donor's own
> reasoning: `trigger` is a single enum and a schedule descriptor is present IFF
> `trigger == schedule`, so flipping the manual path would break its manual runs,
> and SD-P3 skip-if-in-flight keys on `procedure_id`. The manual path stays
> runnable. The spine was **extracted** from the manual path at authoring time
> rather than retyped, so the byte-identity above is by construction.
> **(#856, `db398bf` → merge `a3ef955`, `feat(fleet_maintenance)` — the build,
> plus the L3 generic CLI fix.)** **A CORRECTED claim, recorded as an error and
> not silently dropped:** Code's own dispatch said an unwired fleet daemon "ticks
> but 409s at resolve". It does not — `_run_scheduler` calls
> `registry.get_procedure_executors()` **unguarded** (`cli.py:151`) and the
> registry raises `RegistryError` (`registry.py:114-121`), so the daemon
> **CRASHED AT STARTUP** for five of six verticals and never ticked at all. The
> `plan-drafter` caught it at drafting; Code verified both files at R2. The fix
> **replaces a rotted docstring with an assertion**: `_register_executor_factory`
> now dispatches over a six-vertical map **mirroring** (never importing)
> `services/api/main.py:_PROCEDURE_EXECUTOR_REGISTRARS` — `services/engine/` must
> not depend on `services/api/`, and importing the app would drag FastAPI into
> daemon startup — with a **set-equality tripwire** pinning the two vertical sets
> equal, so a 7th vertical wired into one and not the other goes RED. Proven
> **non-vacuous**: a vertical was removed from the map → RED → restored from a
> `/tmp` backup byte-identically (`cmp -s` clean), never `git checkout`.
> **(#857, `5f49023` → merge `1ce3546`, `docs(plans)`.)** Closed out **COMPLETE
> at 7/7** and archived to `docs/plans/done/0090-fleet-scheduled-calm-path.md`.
> **THE MEASUREMENT: 16m13s hands-on**, no interruptions (YAML 2m19s /
> catalog+census 2m44s / CLI+tests 5m16s / gate 3m55s / smoke 1m59s). The MS-1…
> MS-6 protocol was written into the PLAN **before** Cray ratified SD-2, so it
> could not have been shaped around a result it had not seen; the artifact is
> gitignored — `docs/research/private/2026-07-22-fleet-scheduled-timing-log.md`,
> cited by path only. **THE MS-6 CAVEAT IS BINDING AND TRAVELS WITH THE NUMBER
> WHEREVER IT IS WRITTEN, INCLUDING HERE:** 16m13s is a **LOWER BOUND** under
> maximally favourable conditions — the same operator who built the manual path,
> a shipped donor to copy, all scheduler machinery already shipped, every
> decision pre-ratified. It does **NOT** measure machinery construction, blind
> intake, or a fresh operator, and it is **NEVER** to be presented summed with
> PLAN-0086's 27m39s or PLAN-0089's ~14 min — three claims under three
> conditions, companions not addends.
> **Two deviations, recorded as deviations rather than absorbed. D-1:** AC-5's
> "the PLAN-0089 suite stays green UNMODIFIED" could not hold literally — that
> suite pins the vertical's procedure-id set by SET-EQUALITY, so a third
> procedure turns it RED by construction (the guard working as designed; every
> behavioural assertion about the hero is byte-untouched, only the census line
> moved). **D-2:** part of AC-3 ("a human resolution completes it") was written
> **after the clock stopped** and is therefore NOT inside the 16m13s — disclosed
> because a number that silently excludes required work is worse than a slower
> honest one.
> **Live evidence (AC-6) — and it is evidence, never a gate.** The daemon
> registered the schedule, computed `next_fire` = 06:00 Asia/Bangkok **from the
> cron unaided**, fired on a **backdated slot** (never an edited cron), parked at
> `schedule_service` with verdicts `['breach','ok','ok']` — identical to the
> offline run AND to PLAN-0089's manual run — recording `actor_kind: "service"`
> on behalf of `req-mechanic-tom`, then re-armed to the next slot. **A local boot
> is NOT a host-state action** (CLAUDE.md §8 scopes that to MS-S1 and
> host/global config; s161 recorded over-applying it here as an error).
> **The merge-commit gate, against a pass/fail read fixed BEFORE the run:**
> `a3ef955` = **2994 passed / 7 skipped**, `mypy --strict` clean at 98 files,
> ruff clean at CI scope — expected 2984 baseline + 10 new tests = 2994, hit
> exactly ⇒ **`confirmed — prior intact`**; **2995/7** after the closeout's added
> test. The merge commit's tree is **byte-identical** to the tested commit's
> (both `d085400b9bc5a469a176df40e01806f121651ae6`), so the pre-merge live
> evidence IS merge-commit evidence — proven, not assumed.
> **Cray-ratified typed selections (AskUserQuestion), all BEFORE the work they
> govern:** L1 cron `0 6 * * *` Asia/Bangkok · L2 `owning_person_id:
> req-mechanic-tom` (accountability parity, PLAN-0065 SD-5(b); NOT an SoD
> requester) · L3 fix `cli.py` generically · SD-1 `svc-fleet-scheduler` · SD-2
> yes, timed. STATUS: 55,745 B.
> **(Stop-hook misfires — BACKFILLED session 165, 2026-07-23; this record was the
> doc gap s164 named and did not close.)** The Stop hook fired **3× on nothing
> ordered** during this session, the same count and the same shape as s71 and s164.
> Code declined each via the trigger's own override clause. Recorded late, so the
> tally is reconstructed from the s163/s164 handoffs rather than from a
> contemporaneous note — flagged as such rather than presented as fresh evidence.

> **Session 164, 2026-07-22 (head_commit `1ce3546` → `f758509`) — a one-PR
> session whose real product was a REFUTATION, not a build: a 4-agent Explore
> fan-out re-ranked the five session-163 candidates against code and killed two
> standing claims before Cray picked the winner by typed AskUserQuestion.
> PLAN-0091 — the narrative→vertical scaffolder tool v1, `vero-lite scaffold` —
> is FILED at `Status: Draft`, 10 ACs / 8 Steps, CREATE-SHAPE ONLY, and CANNOT
> be built until Cray adjudicates its Step 0 (SD-1…SD-4).**
> **(the open.)** Orientation + a full sync matched the handoff on all six
> checks: `main=caeda74`, 0 open PRs, **2995 passed / 7 skipped** — the
> pre-committed read, hit exactly ⇒ `confirmed — prior intact` — `mypy
> --strict` clean at 98 files, ruff clean at CI scope, STATUS 55,745 B.
> **(the fan-out — two REFUTATIONS, the session's intellectual headline.)**
> **(a) The scaffolder was NOT greenfield.** The correct label is
> **brownfield-with-a-ratified-half**: **ADR-0024 is Accepted** and already pins
> the generation contract, and **PLAN-0040 already shipped the
> narrative→procedure pipeline** (`services/engine/procedures/generator/
> pipeline.py` S0–S6, the archetype REGISTRY, restricted draft types,
> `prose_lint`); the AT-2 breadth block was CANCELLED at N=4 and PLAN-0087 made
> a new AT-2 vertical zero-engine-diff. So the genuine gaps are **narrower than
> "a scaffolder"** — narrative→**ontology YAML** (no ADR covers it) and the
> **money spine**. **(b) PLAN-0088 has 12 defects, not 6**, and **ADR-0032 D2's
> pilot gate does NOT block it** — shape 2 is defined by *output*, Group A emits
> no proposal, and AC-11 enforces exactly that **statically** on five
> on-disk-verified symbols, so **Cray's L1 classification is correct**. What
> blocks Step 1 is the PLAN blocking itself: **AC-3 ⊗ AC-12 is a trilemma** —
> violate AC-3, violate its own Out-of-Scope, or introduce an unwritten `run_id`
> sort key that breaks `view-map.js`'s newest-first dependency (a **second `GET
> /runs` consumer** AC-12 never counted). **8 of 14 ACs need rewriting before
> any code.** Also grounded: **PLAN-0076 T1 is counter-indicated, not merely
> unqueued** — the PLAN itself calls it an "inert audit display-flag over-mark
> with zero live collisions", so building it is abstraction ahead of pressure,
> which **ADR-0031 D4.1 forbids**. **Tire is EXTERNALLY blocked** on a per-tyre
> data source (the ontology carries zero tyre representation; the GPS stream is
> per-truck). The multi-SP refinement is unmotivated at **N=0** (only two agents
> declare an SP, one each). **Cray then picked the scaffolder PLAN by typed
> AskUserQuestion**, over PLAN-0088 and PLAN-0076 T1.
> **(#859, `74a49c2` → merge `f758509`, `docs(plans)` — fast-forward, docs-only,
> 1 file +508.)** The dispatch **carried its spec inline because both spec
> inputs are gitignored** — the 14-row seam ledger and the 4-question intake log
> (`docs/research/private/2026-07-21-fleet-scaffold-{seam-ledger,question-log}.md`,
> cited by path only). Code verified the fact pack **BEFORE** dispatch and found
> **four drift corrections**, two of which make ledger rows **actively wrong**:
> **row 12 is DEAD** (`ComplianceCriterion` retired, `spec.py:876-884`;
> vocabulary is declared per vertical at `:1688`) and **the hand-wire count is
> 4, not 3** (PLAN-0090's mirror map `services/engine/cli.py:130`, pinned equal
> by `tests/services/engine/test_cli_registrars.py`). Standing rule for this
> spec: **cite the ledger, never the PLAN-0086 closeout**, whose tally says 6
> then enumerates seven (6+5+2=13≠14; the correct split is 7/5/2=14).
> **R2 found ONE defect, and its source was Code's own dispatch, not the
> drafter.** The intake round-trip cost was stated as "6m51s of 27m39s ≈ 25%" —
> **wrong twice over**: none of the interruption time is *inside* the hands-on
> number (every PLAN-0086 phase row has `wall == hands-on` and the rows sum to
> 27m38s, so all 6m51s falls in the 15m39s of wall that hands-on excludes), and
> 1m34s of it was spent **asking while work continued**, not idling. Corrected
> in place to **6m51s of 43m17s wall (~16%)**, of which **5m17s was
> fully-blocked idle (~12% of wall)**, with the correction **and its
> attribution** recorded inline in the PLAN. Everything else verified on disk,
> including the AT-2 fleet signature AC-7 pins on. **The drafter re-grounded
> Code's fact pack and reported no fifth drift**, with one precision worth
> keeping: the AT-2 cancellation **removes the bar but does not pre-approve
> generation**, so the PLAN makes the **affirmative** case (ADR-0024 OQ-8's
> typed-content precondition verified MET on disk) rather than citing the
> cancellation as approval.
> **(a Stop-hook misfire, observed live — evidence for the still-open autonomy
> fork.)** The hook dispatched "spawn `plan-drafter`" **while the `plan-drafter`
> it was asking for was already running**; Code declined via the trigger's own
> override clause. This is the **3rd misfire this session** and it **cleared
> BOTH existing layers**: the reason had real content (so #844's
> contentless-reason floor did not demote it) and it used no approval/merge
> vocabulary (so #843's prompt paragraph did not catch it). _Doc gap CLOSED
> (session 165): s163's three are now recorded in the s163 block below._
> **Correction (session 165):** the "reason had real content so the floor did not
> demote it" diagnosis is **too generous to the floor**. Grounding found the
> contentless-reason floor is called only on the **proceed** arm; the s164 fire came
> down the **dispatch** arm, which never calls it **at any content level**. The floor
> was not out-argued — it was never reachable. This matters for the fix: a new
> deterministic layer added to the proceed arm would miss this shape too.
> **Verification / state:** `gate` PASS in 3m14s and **SHA-verified** (run
> `headSha` == PR head == `74a49c2`) before the merge, on Cray's typed
> instruction. **0 open PRs** at close; MS-S1 idle, no host-state change; dev
> Postgres UP; working tree clean but for the 2 KEEP untracked paths
> (`.claude/benchmark-results/`, `.claude/launch.json`). Commits: `74a49c2` →
> `f758509` (#859 merge, head_commit of record). Artifact:
> `docs/plans/0091-narrative-to-vertical-scaffolder-tool.md`, **Status `Draft`**.
> **Nothing is ordered next:** PLAN-0091 cannot start until Cray adjudicates
> SD-1…SD-4, and **SD-1's ruling may require an ADR merged first**; the other
> live candidates are PLAN-0088's 8-AC re-draft (ungated for Code) and the
> autonomy fork (a decision, not code).
