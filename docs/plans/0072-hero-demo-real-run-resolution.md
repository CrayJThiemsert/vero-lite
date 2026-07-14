# PLAN-0072: Hero-demo real run resolution — beat 3 genuinely resolves the parked DOA gate

**Status:** Ready for execution
**Owner:** Claude Code (build + commit); drafted by `plan-drafter` (in-harness, G1/G2-exempt author)
**Created:** 2026-07-14 (re-scoped same day after Cray ratified SD-A=(b), SD-B=(b), SD-C=(a); SD-D pending — does not block Steps 1–4)
**Related ADRs:** ADR-016 (S2 RF-1 — untouched, see contract check), ADR-0026 (principal SoD), ADR-0029 (event bridge), ADR-007 (reasoning envelope — untouched)
**Related PLANs:** PLAN-0045 (hero demo), PLAN-0047 (API-key auth + governance pin), PLAN-0053 (RF-1 library guard), PLAN-0054 (operate seam: auth.js, login bar, gate-resolve/cancel), PLAN-0056 (event bridge build), PLAN-0057 (event-triggered opener), PLAN-0058 (reject-at-login /whoami probe)

> **Author≠reviewer disclosure (ADR-012 D4.3).** Drafted and re-scoped by the
> in-harness `plan-drafter` subagent (ADR-013 D1 phased authority). Outline
> originator: Cray (D3 selection + SD-A/B/C ratification, 2026-07-14, relayed
> via Code dispatch). Independent reviewer: Code (R2) + Cray (SD-D
> ratification) at PR merge. Separation: INTACT.

## Goal

The Palantir-lite hero demo (View G "Governance Moment") tells 4 beats:
narrative → governed → run → ฿. Beat 3 ("run it") already FIRES a real
persisted procedure via the shipped event bridge and parks it at the DOA
`approve` gate (`waiting_human`) — but the on-screen "Approve → ✓ COMPLETED"
step is a **fake front-end badge**: `renderActPanel`
(`services/api/static/assets/view-hero.js:220-241`) paints
`'✓ COMPLETED · ' + apprId` client-side on click (`view-hero.js:230-237`),
and the code comment admits it — *"the parked run itself never auto-resolves
… the approve→COMPLETED beat is the demo's front-end reveal"*
(`view-hero.js:220-222`; backend echo at
`verticals/procurement/hero_demo/run.py:464-467`).

This PLAN makes beat 3 **genuinely decide the parked run on screen — both
directions**. Per the ratified SDs, the Act panel authenticates the approver
(`appr-pm`) through the shipped credential seam and calls the **production**
`POST /runs/{run_id}/gate/resolve` route **verbatim**
(`services/api/routers/runs.py:324-424`), which drives the REAL
`resolve_gated_step` (`services/engine/procedures/action_step.py:433-443` —
2-phase decide/execute, RF-1 approver guard `:508-519`, governance pin
`:525-526`, fail-closed principal-SoD per ADR-0026 D4) and `resume_run`
(`runs.py:400-409`). The panel then renders the **genuinely-persisted**
outcome: the real run status, the resolved-by principal, the SoD
audit-to-control tie emitted **at resolution** (`action_step.py:400-403`),
and — on the reject path — the honest shipped semantics (see SD-B).

The capability is shipped and test-proven:
`tests/services/db/test_event_procurement_demo.py:193-244` proves
`fire_event → resolve_gated_step (principal=appr-pm) → resume_run →
COMPLETED`; `tests/services/db/test_procedure_action_gate.py:192-236` proves
the reject semantics; the auth-armed HTTP surface is proven at
`tests/api/test_runs_endpoints.py:49-50` (auth-ON monkeypatch pattern). This
PLAN is **"wire an existing, verified capability into the demo surface"** —
front-end wiring + small demo glue. No engine change, no new endpoint.

**Scope note — event mode only.** The Act panel renders only in event mode
(`view-hero.js:293`), the only opener with a *persisted* parked run
(`run_hero_event_governance_moment`, `run.py:444-545`, parks via `fire_event`,
guard `:481-486`). The manual/live opener (`run.py:320-403`) runs in-memory
via `run_procedure` (`:342-349`) and is not persisted — nothing to resolve
(governance_audit.py LOCKED #3, cited at `run.py:466`).

### Contract check — no new ADR needed (re-confirmed after SD ratification)

Verified against disk; this is demo wiring over shipped, ratified surfaces:

- **The production route is reused VERBATIM** (`runs.py:324-424`) — zero
  change to its code, its RF-1 check (`:346-353`), its SoD/error translation
  (`:386-398`), or its response model (`GateResolveResponse`, `:418-424`).
- **`resolve_gated_step` signature untouched** (`action_step.py:433-443`);
  reject semantics used exactly as shipped (`:471-480`).
- **ADR-016 S2 RF-1 is honored end-to-end**: the approver authenticates with
  a real bearer credential; `get_current_principal`
  (`services/api/auth.py:63-94`) resolves `appr-pm` to its authored `Person`
  server-side. No server-designated principal, no demo exception.
- **Enabling auth is configuration, not contract**: `api_auth_enabled`
  defaults **ON** (fail-closed, `services/api/config.py:53-61`), and the
  procurement operate demo is *already documented* to run auth-ON with an
  `appr-pm` key (`.env.example:47-57`; `API_KEYS` holds sha256 digests only,
  raw keys never in git — CLAUDE.md §8). This PLAN flips no ADR-governed
  default.
- **`HeroGovernanceAudit` reshape not required** — `hero` is
  `dict[str, Any]` (`services/api/models/demo.py:69`); adding `run_id` is
  additive. No new response model anywhere (the drafted `HeroGateResolution`
  is DROPPED along with rejected SD-A(a)).

If R2 review finds any of the above wrong, that is a **blocking finding** —
stop and route to ADR drafting instead of proceeding.

## Decisions

### LOCKED (structural, not up for re-litigation in this PLAN)

- **L-1 — the demo drives the REAL production resolve route.** No parallel
  demo resolve logic, no status-flip UPDATE, no guard bypass. DOA/SoD/RF-1
  and the governance pin execute for real (`runs.py:324-424`,
  `action_step.py:433-526`).
- **L-2 — evidence gate = deterministic backend integration test.** The
  browser render is supporting evidence only (see Verification).
- **L-3 — deterministic-offline.** No MS-S1 / host-state: fire and resume
  both run the registered deterministic procurement executor factory
  (`advisory_stub_factory`; startup registration `services/api/main.py:111-114`,
  `:156-163`). CLAUDE.md §8 unaffected.
- **L-4 — the render binds to persisted truth.** After a decision the panel
  renders from the `GateResolveResponse` (`runs.py:418-424`) and/or a
  re-fetch of `GET /runs/{run_id}` (`runs.py:236-267`) — never from a
  hardcoded client-side literal.

### SD-A — how the demo resolves the gate — **RATIFIED (b), Cray 2026-07-14**

**(b) CHOSEN:** enable `api_auth_enabled` + reuse the production
`POST /runs/{run_id}/gate/resolve` route verbatim. RF-1 is authenticated
end-to-end; `appr-pm` is a genuinely authenticated `Person`, not
server-designated.

*Mechanism (all shipped — verified on disk at re-scope):* auth defaults ON
(`config.py:53-61`); per-person static keys via `API_KEYS`
(sha256-digest → person_id, `config.py:62-70`; key-generation one-liner +
the procurement demo block documenting `API_AUTH_ENABLED=true` +
`API_KEYS={"<sha256-hex>": "appr-pm"}` at `.env.example:37-57`, set by the
`oct-demo-procurement` launch config). Front-end credential seam:
`services/api/static/assets/auth.js` — `login()` validates the key at login
via the `GET /whoami` probe (`auth.js:30-48`, PLAN-0058), per-tab
`sessionStorage`, `authHeader()` attaches `Authorization: Bearer` to operate
POSTs only (`auth.js:51-55`); View H already runs this exact flow (login bar
`view-monitor.js:391-427`, mode derived from `isLoggedIn`
`view-monitor.js:31,48`, header attach `:454`).

*Blast radius (checked):* `get_current_principal` guards only state-changing
routes — actions approve/execute (`actions.py:223,244`), admin warm/sleep
(`admin.py:177,223`), intake generate (`intake.py:198`), run / gate-resolve
/ cancel (`runs.py:277,329,431`), whoami (`whoami.py:22`). All demo routes
carry **no** auth dependency (`routers/demo.py:45-80`) — the event opener +
governance/impact reads keep working headerless with auth ON, so views C/G/H
reads are unaffected. View H is auth-native by design. The only logged-out
401s are on already-guarded operate/admin actions — shipped default-ON
behavior, not a regression from this PLAN.

*Lineage:* (a) demo-scoped `/demo/hero/resolve` with a server-designated
approver — REJECTED at ratification (weaker RF-1 reading); shipping a demo
credential in static JS — rejected at drafting.

### SD-B — scope of the beat — **RATIFIED (b), Cray 2026-07-14**

**(b) CHOSEN:** approve **and** reject/deny as real UI affordances.
`resolve_gated_step` supports `reject` verbatim (`action_step.py:471-480`).

**Corrected premise — shipped reject semantics (verified on disk; NEW design
tension surfaced at re-scope).** A reject is **NOT a distinct terminal run
state**. Per `action_step.py:471-480` and the proving test
`test_procedure_action_gate.py:192-236`: *reject = continue + record* — the
handler never fires (`:225`, no PO effect executes), `action_rejected` lands
on the step's reasoning trace (`:227`), and the resumed run **continues past
the rejected step** (`:229-236`) to its normal terminal — i.e. the run ends
`COMPLETED` with the rejection durably recorded and **no executed effect**.
There is no `rejected` run status to render. The UI must render the reject
outcome honestly — e.g. *"✗ REJECTED by appr-pm — no PO created (handler
never fired); decision recorded on the audit trace; run completed"* —
because inventing a fake "rejected terminal" badge would reintroduce exactly
the dishonesty this PLAN removes. (Whether this demo procedure's downstream
steps tolerate an empty executed-effect set is OQ-4 — the RED test decides.)

*Lineage:* (a) approve-only, reject as test-only — REJECTED at ratification
in favor of surfacing the full governed choice on stage.

### SD-C — repeatability / replay — **RATIFIED (a), Cray 2026-07-14**

**(a) CHOSEN:** generation-aware re-fire, as drafted. The event run is
event-keyed and idempotent: fixed demo timestamps (`run.py:438-441`) ⇒ fixed
`run_id = <procedure_id>@<event_key>`
(`services/engine/procedures/event_bridge.py:72-73`); `fire_event` no-ops
`ALREADY_FIRED` on an existing PK (`event_bridge.py:239-245`, `:303-305`).
Once beat 3 decides the run, a replayed `POST /demo/hero/event` would load a
non-`waiting_human` run and raise at `run.py:481-486`. Fix: when the
fixed-key run exists but is **no longer `waiting_human`** — **which under
SD-B(b) happens on EITHER path, approve OR reject, since both resume to
`COMPLETED`** — fire a FRESH parked run under a fresh event key (bumped
`detected_at`; the parameter already exists, `run.py:448-450`, so tests stay
deterministic by injection). Decided runs are **retained** as real audit
history. While a run of the procedure IS parked, keep today's behavior
(return the same parked run). **Hazard:** a fresh-key fire while another run
of the same procedure is parked returns `SKIPPED_IN_FLIGHT` with a
never-created `run_id` (`event_bridge.py:248-261`, `:306-308`) → `load_run`
`None` → the `run.py:481-486` guard raises; fresh-fire **only when no run of
`event_emergency_sourcing_round` is in flight**. The boot-time operate seed
targets the *different* procedure `emergency_sourcing_round` (`run.py:686`,
`main.py:169-187`) — no interference (the in-flight check is
per-`procedure_id`).

*Lineage:* (b) resolve-endpoint auto-reseed — rejected (couples
resolve+seed); delete/reset — rejected (destroys audit history).

### SD-D — where the approver authenticates in the hero view — **RATIFIED (a), Cray 2026-07-14**

SD-A(b) makes a **login moment** part of beat 3. The *mechanism* is settled
(the shipped `OCT.Auth` seam — no new auth surface either way); the open
choice was **stagecraft**, ratified by Cray:

- **(a) CHOSEN — inline login affordance in the Act panel.** When
  logged out, the Act panel renders a compact key+identity login (same seam
  and idiom as View H's operate bar, `view-monitor.js:391-427`); once logged
  in, the approve/reject buttons arm. *Rationale: "the approver
  authenticates, then signs" is itself a governance beat — it strengthens
  the ADR-016 RF-1 story on stage, and pre-staging stays trivially possible
  (log in before going on stage) with zero extra code.*
- **(b)** no login UI in View G — the Act panel, when logged out, points the
  operator to log in on View H first. *Less new render code; an awkward
  on-stage detour to another view mid-beat.*

Both options were backend-identical and integration-test-identical; SD-D
gated only Step 5's render work. *Lineage:* (b) pre-login on View H —
rejected at ratification (awkward mid-beat detour to another view).

## Acceptance Criteria

- [ ] **AC-1 (EVIDENCE GATE — authenticated approve → COMPLETED).** A
  deterministic backend integration test (per-checkout test DB;
  `procurement_registered` + `session` fixtures; API arm via `ASGITransport`
  as `tests/api/test_demo_hero_routes.py:21-24`; auth armed per the shipped
  pattern `tests/api/test_runs_endpoints.py:49-50` — monkeypatch
  `api_auth_enabled=True` + `api_keys={sha256(raw): "appr-pm"}` +
  `oct_vertical="procurement"`; note `tests/conftest.py:17` disables auth
  suite-wide, so each test arms it explicitly): `POST /demo/hero/event`
  parks the run (`waiting_human`, gate `approve`) → the **production**
  `POST /runs/{run_id}/gate/resolve` with `Authorization: Bearer <appr-pm
  key>` and all-approve decisions → a **fresh DB read** (`load_run` /
  `session.get`) shows `status == completed`; the `GateResolveResponse`
  reports the real `run_status` (`runs.py:418-424`).
- [ ] **AC-2 (SoD audit-to-control tie persisted at resolution).** The same
  test asserts the resolved `approve` step's persisted `audit`
  `governed_decision` contains the SoD control tie (`control_ref.kind ==
  "sod"`, constraint `_SOD_CONSTRAINT_ID`, `principal_id == "appr-pm"`) —
  written by `resolve_gated_step` at resolution (`action_step.py:400-403`),
  i.e. the REAL tie, not the parked view's derived preview
  (`run.py:376-384`).
- [ ] **AC-3 (fail-closed on a wrong approver — via the real auth seam).**
  With a second in-test key provisioned for `req-planner` (the event run's
  SP-5 owning human / recorded requester, `run.py:436`,
  `procedures.yaml:700`), an authenticated resolve attempt by `req-planner`
  → `PrincipalSoDError` → HTTP **403** with the structured verdict
  (`runs.py:386-390`); the run REMAINS `waiting_human`; the durable
  `gate_refused` audit row is written (`action_step.py:420-430`). An
  **unauthenticated** attempt → **401** (`auth.py:73-76`) — identity is
  never client-chosen (bearer key resolved server-side, `auth.py:66-69`).
- [ ] **AC-4 (authenticated reject → honest shipped semantics).** An
  authenticated `appr-pm` rejecting all proposals: the handler never fires
  (no PO effect in the rewritten `output_set`), `action_rejected` is on the
  step's persisted reasoning trace, and the resumed run **continues to
  `completed`** with no executed effect (`action_step.py:471-480`; engine
  semantics proven at `test_procedure_action_gate.py:192-236`). The test
  pins this end-to-end for THIS demo procedure (OQ-4).
- [ ] **AC-5 (replay — SD-C, both directions).** After a decided run
  (approved OR rejected — both end `completed`), `POST /demo/hero/event`
  returns a FRESH parked run (`waiting_human`, new `run_id`); the decided
  run is retained; while a run is parked, a repeat POST still returns that
  SAME parked run (today's `ALREADY_FIRED` behavior preserved).
- [ ] **AC-6 (front end renders persisted truth).** The Act panel:
  logged-out state per SD-D; logged-in `appr-pm` gets **Approve** and
  **Reject** affordances that call the production route with
  `OCT.Auth.authHeader()` (`auth.js:51-55`), building decisions from the
  parked run's proposals (read via `GET /runs/{run_id}`, `runs.py:236-267`,
  using the additive `hero.run_id`); renders from the response / a re-fetch:
  approve → COMPLETED + resolved-by + SoD tie; reject → the SD-B honest
  reject state; errors (401 / 403-with-verdict / 409) render honestly
  (no-mock-fallback posture, `api.js:82-93`). The hardcoded literal at
  `view-hero.js:230-237` is gone. Evidence: browser preview — explicitly
  **non-deterministic supporting evidence**, never the gate (see
  Verification).
- [ ] **AC-7 (production surfaces untouched; demo reads stay open).**
  `resolve_gated_step`'s signature and the production route's code
  (`runs.py:324-424`) are byte-identical; demo routes still carry no auth
  dependency (`demo.py:45-80`) so all views keep working with auth ON;
  existing suites pass unmodified except route-inventory/OpenAPI asserts
  (extend, don't weaken — pattern `test_demo_hero_routes.py:82-96`).
- [ ] **AC-8 (hygiene bar — per the recent-PLAN standard, cf. PLAN-0071).**
  Full suite green on the PR head AND re-run on the merge commit (CI is
  PR-only); `ruff check` + `ruff format --check` clean; `mypy --strict
  services/` clean; CI `gate` green; one pytest per checkout with Docker
  Postgres up; deterministic-offline (no MS-S1 / host-state). No raw key or
  digest committed — test keys are generated in-test; deployment keys live
  in the box's `.env` / launch config only (CLAUDE.md §8).

## Out of Scope

- ❌ The NL narrative→procedure beat-1 (separate, large, host-state PLAN).
- ❌ Unifying the Box-4 `economic_impact` facet (PLAN-0071) into the hero UI
  — beat 4 already works via `verticals/procurement/hero_demo/ledger.py`.
- ❌ Any ADR-007 / ADR-016 contract change (see the contract check — if one
  becomes necessary, this PLAN halts and routes to ADR drafting).
- ❌ Wiring resolve into the manual/live opener (no persisted run there —
  see Scope note).
- ❌ Any NEW auth surface: session tokens (the auth.js v2 note,
  `auth.js:14-17`), demo-scoped credentials or endpoints (rejected
  SD-A(a)), or key-provisioning changes beyond the existing documented
  mechanism (`.env.example:37-57`).
- ❌ Cancel-run UI in the hero view (`runs.py:427-449` exists; that is
  View H's concern, not beat 3's).

## Steps

### Step 1: Plan-first read of the result-producing code (pre-committed gate)

On the executing feature branch, re-read the full path before writing
anything: `action_step.py:433-543` (+ reject `:471-480`),
`runs.py:236-267` (run detail + read-only proposals), `:324-424` (resolve),
`:427-449` (cancel, for the route-inventory sweep), `auth.py` (whole file),
`config.py:52-70`, `.env.example:36-57`, `run.py:444-545` + `:653-700`,
`event_bridge.py:239-320`, `auth.js` (whole file),
`view-monitor.js:391-460` (login bar + header attach),
`view-hero.js:220-241`/`:293`/`:299-321`, `api.js:82-100`,
`test_event_procurement_demo.py:193-244`,
`test_procedure_action_gate.py:192-236`, `test_runs_endpoints.py:40-60`,
`tests/conftest.py:17`. **Pre-committed pass/fail read:** every file:line
citation in this PLAN matches disk on the executing branch. Any mismatch ⇒
stop, reconcile the PLAN (classify: superseded-by-new-info vs was-an-error)
before building.

### Step 2: RED — the deterministic integration tests

New test module (suggested `tests/services/db/test_demo_hero_resolve.py`;
API arm per `test_demo_hero_routes.py:21-24`; auth armed per
`test_runs_endpoints.py:49-50` with two generated-in-test keys — `appr-pm`
and `req-planner`). Encodes AC-1..AC-5 failing first: authenticated
approve→COMPLETED + persisted SoD tie; wrong-approver 403 + `gate_refused` +
still-parked; unauthenticated 401; authenticated reject → handler-not-fired
+ `action_rejected` on the trace + run `completed` with no executed effect
(this arm ALSO answers OQ-4 — if the demo procedure's downstream steps choke
on an empty executed-effect set, it surfaces here as a real finding); replay
matrix: parked→same-run, approved→fresh-run, rejected→fresh-run. DB-marked
so the suite skips cleanly when Postgres is down.

### Step 3: Backend glue (small — no new endpoint)

- Expose `run_id` additively on the event opener's returned `hero` dict
  (`run.py:522-545`; additive — `models/demo.py:69` is `dict[str, Any]`),
  so the front end can drive `GET /runs/{run_id}` + the production resolve.
- Nothing else server-side for the decision itself — the production route
  already does the whole decide→resume (`runs.py:376-409`).

### Step 4: Replay mechanics (SD-C(a))

Generation-aware re-fire in `run_hero_event_governance_moment`
(`run.py:444-545`): when the fixed-key run exists and is no longer
`waiting_human` (approved OR rejected — both `completed` per SD-B), fire a
fresh parked run under a bumped `detected_at`; fresh-fire only when no run
of `event_emergency_sourcing_round` is in flight (the `SKIPPED_IN_FLIGHT`
hazard, `event_bridge.py:306-308`). Covered by the AC-5 arm of Step 2.

### Step 5: Front end — the Act panel authenticates + decides for real (render gated on SD-D)

- `api.js`: thin wrappers for `GET /runs/{run_id}` and
  `POST /runs/{run_id}/gate/resolve` that attach `OCT.Auth.authHeader()`
  (join `api.js:95-100`; keep the no-mock-fallback posture).
- `view-hero.js` `renderActPanel` rework (`:220-241`): logged-out state per
  SD-D ((a) inline login reusing the `view-monitor.js:391-427` idiom, or
  (b) a pointer to View H); logged-in: **Approve** + **Reject** buttons; on
  click keep an optimistic paint strictly as a *loading* state (OQ-3); build
  decisions from the fetched proposals; render from the
  `GateResolveResponse` + re-fetch: approved-COMPLETED state (status,
  resolved-by, SoD tie), rejected state (SD-B honest wording), error states
  (401 not-logged-in, 403 SoD verdict, 409). Replay remounts event mode
  (backed by SD-C).
- Ensure `auth.js` is loaded on the hero page (it ships today for View H —
  verify the include) and bump the static-asset `?v=` cache tokens for every
  touched asset (project memory: the preview serves stale JS otherwise).

### Step 6: GREEN + evidence + PR

All Step-2 tests green; full suite + `ruff check` + `ruff format --check` +
`mypy --strict services/` on the branch; browser-preview supporting evidence
for AC-6 (login → approve on one fresh run; reject on another); confirm the
demo launch config carries `API_AUTH_ENABLED=true` + an `appr-pm` key per
`.env.example:47-57` (box `.env` / `.claude/launch.json` — never committed);
PR per CLAUDE.md §7 (branch + PR + merge, body via `--body-file`); after
merge, full-suite re-run on the merge commit (CI is PR-only).

## Open questions (R2-level engineering calls — not Cray SDs)

- **OQ-1 — glue ownership.** The `run_id` exposure + generation re-fire both
  live naturally in `verticals/procurement/hero_demo/run.py` (they modify
  its opener). Alternative: a `hero_demo/replay.py` helper if the re-fire
  logic grows. R2 picks.
- **OQ-2 — how the front end learns the parked run + proposals.**
  Recommended: additive `hero.run_id` (Step 3) + read the suspended step /
  proposals via the shipped `GET /runs/{run_id}` (`runs.py:236-267`) — no
  demo-contract growth beyond one key. Alternative: also embed
  `gate_step_id` / action ids in the event response (saves one GET, adds
  demo-contract surface).
- **OQ-3 — the optimistic paint.** Keep `renderActPanel`'s immediate visual
  feedback as a spinner/"deciding…" state only; terminal badges appear
  exclusively from response data (L-4).
- **OQ-4 — does THIS demo procedure tolerate a fully-rejected gate?** Engine
  semantics guarantee continue-past-reject
  (`test_procedure_action_gate.py:229-236`), but
  `event_emergency_sourcing_round`'s downstream steps consuming an empty
  executed-effect `output_set` is unproven for this specific procedure. The
  Step-2 reject arm decides it; if downstream chokes, surface as a finding
  (the fix belongs in the demo procedure's step config, not the engine)
  before proceeding.
- **OQ-5 — login-affordance componentization (under SD-D(a)).** Reuse the
  View-H login-bar markup inline vs extract a tiny shared login widget used
  by both views. Cosmetic; R2 picks at build time.

## Verification

How we know it worked (in gate order):

1. **The offline oracle is the gate (CLAUDE.md §8).** AC-1..AC-5 via the
   Step-2 deterministic integration tests — fresh pytest output on the
   executing branch, per-checkout test DB, auth armed in-test, no MS-S1.
   Pre-committed pass/fail read fixed in Step 2 (RED first).
2. **Full hygiene bar (AC-8):** full suite on the PR head; `ruff check` +
   `ruff format --check`; `mypy --strict services/`; CI `gate` green on the
   PR; after merge, the full suite re-run on the merge commit.
3. **On-screen evidence (AC-6) — supporting, NON-deterministic.** Browser
   preview on the fixed demo port with auth ON: log in as `appr-pm` (SD-D),
   drive the event opener, exercise BOTH arms (approve one fresh run, reject
   another — SD-C makes this a natural sequence), then verify via
   `preview_snapshot` + an in-page/API **re-fetch of the persisted run
   state** — never a screenshot gate. Known flaky-preview tax:
   `preview_screenshot` times out; `preview_click`/`fill` can race an async
   re-render (drive flaky steps via eval-click + confirm in a follow-up
   eval); static assets cache (bump `?v=`). A preview flake does NOT fail
   the PLAN while the Step-2 backend gate is green — but the backend gate
   can never be substituted by a preview pass.
4. **No-regression read (AC-7):** existing gate/SoD/runs/demo suites pass
   unmodified; `grep` confirms `resolve_gated_step`'s signature and
   `runs.py:324-424` are byte-identical; demo routes remain
   auth-dependency-free.

## References

- Fake reveal: `services/api/static/assets/view-hero.js:220-241` (comment
  `:220-222`, literal badge `:230-237`, event-mode-only `:293`, mount flow
  `:299-321`)
- Event opener + never-auto-resolves: `verticals/procurement/hero_demo/run.py:444-545`
  (constants `:433-441`, parked guard `:481-486`, derived SoD preview
  `:511-518`, docstring `:464-467`); manual opener `:320-403`; live builder
  `:406-422`; operate seed `:653-700` (procedure `emergency_sourcing_round`,
  `:686`)
- Real resolve capability: `services/engine/procedures/action_step.py:433-543`
  (signature `:433-443`, reject semantics `:471-480`, RF-1 library guard
  `:508-519` + `GateApproverError` `:92`, governance pin `:525-526`, SoD-tie
  emission `:400-403`, refusal audit `:406-430`)
- Production routes: `services/api/routers/runs.py:236-267` (run detail +
  read-only proposals), `:324-424` (gate resolve: RF-1 403 `:346-353`,
  resolve call `:376-385`, error translation `:386-398`, resume `:400-409`,
  `GateResolveResponse` `:418-424`), `:427-449` (cancel)
- Auth seam: `services/api/auth.py:36-94` (fail-closed dependency; 401
  `:73-76`/`:80-81`; server-side person resolution `:82-94`); toggle + keys
  `services/api/config.py:52-70` (default ON); provisioning + demo block
  `.env.example:36-57`; front-end `services/api/static/assets/auth.js`
  (login/whoami probe `:30-48`, `authHeader()` `:51-55`, v2 note `:14-17`);
  View-H usage `services/api/static/assets/view-monitor.js:391-427`, `:454`;
  whoami `services/api/routers/whoami.py:22`; guarded routes
  `actions.py:223,244`, `admin.py:177,223`, `intake.py:198`,
  `runs.py:277,329,431`
- Demo surface: `services/api/routers/demo.py:42-81` (no auth dependency;
  SD-3 guards `:17-22`); models `services/api/models/demo.py:60-75` (`hero`
  = `dict[str, Any]`, `:69`); registration `services/api/main.py:212`;
  executors at startup `main.py:111-114`, `:156-163`; operate seed
  `main.py:169-187`; client wrapper `services/api/static/assets/api.js:82-100`
- Event bridge idempotency: `services/engine/procedures/event_bridge.py:72-73`,
  `:239-245`, `:248-261` + `:306-308`, `:282-320`
- Proving tests: `tests/services/db/test_event_procurement_demo.py:193-244`
  (resolve→COMPLETED); `tests/services/db/test_procedure_action_gate.py:192-236`
  (reject = continue + record); `tests/api/test_runs_endpoints.py:49-50`
  (auth-ON monkeypatch pattern; RF-1 arms `:229-235`, `:347`);
  `tests/conftest.py:17` (suite-wide auth off — arm per test);
  route-inventory pattern `tests/api/test_demo_hero_routes.py:21-24`, `:82-96`
- Principals: `verticals/procurement/procedures.yaml:69` (`appr-pm`), `:87`
  (`svc-buyer` service principal), `:681`/`:700` (event run fires as
  `svc-buyer` on behalf of `req-planner`), `:871-872` (SoD resolution:
  intake→`req-planner`, approve→`appr-pm` at the ฿288k tier)
