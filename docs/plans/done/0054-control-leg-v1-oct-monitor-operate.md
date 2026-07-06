# PLAN-0054: Control-leg v1 — governed approve/reject/cancel a procedure run FROM the OCT Monitor UI

**Status:** Complete
**Owner:** Claude Code
**Created:** 2026-07-06
**Completed:** 2026-07-06 (session 103 — all Steps 1–7 + Step 6b shipped + merged; watch→operate live in the OCT Monitor, preview-verified E2E, secure-for-pilot)
**Related ADRs:** ADR-016 (procedure runs + gates + SoD, S2 authenticated-approver); ADR-013 (drafter/committer boundary); ADR-0026 (procurement SoD principals)
**Related PLANs:** PLAN-0052 (OCT Monitor v1, read-only — the seam this wires); PLAN-0053 (ADR-016 S2 Phase A — RF-1 authenticated-approver 403); PLAN-0047 (pilot-grade static API-key auth)

> Authored by the in-harness `plan-drafter` subagent (ADR-013 D1 phased authority).
> Outline originator: Code. Independent reviewer: Cray at PR merge. Cray ratified
> SD-A/SD-B/SD-C on 2026-07-06 (session 102); this refold folds those decisions.
> Code R2-verifies + commits (G5 binds — the drafter does not commit).
> Amended 2026-07-06 (session 102): Step 6b + AC-10 added — a Code-R2-caught completeness
> gap (the live resolve endpoint 409s for every vertical with no registered procedure-executor
> factory). Surgical addition within the Cray-ratified scope; existing Steps/ACs unchanged.

> **COMPLETION (2026-07-06, session 103).** All Steps 1–7 + Step 6b executed and merged to
> `main` (`68083c6`). **Control-leg v1 = COMPLETE:** the OCT Monitor (View H) flips
> **watch-only → watch + OPERATE** — a named, authenticated human approves/rejects a
> `waiting_human` gate and cancels a parked run FROM the UI, with SoD + a tamper-evident audit
> actor enforced server-side. PRs: **#584** (Step 1 — `POST /runs/{run_id}/cancel`; RF-1 403 /
> `waiting_human`-only 409 / `run_cancelled` audit naming the human) · **#585** (Step 6b / AC-10
> — `register_procurement_procedure_executors` at startup closes the resolve-endpoint 409;
> deterministic advisory-stub factory, MS-S1-independent) · **#586** (Step 6 — procurement
> operate-demo seed + lifespan auto-seed gated on `OCT_DEMO_SEED_OPERATE`, idempotent + fail-soft)
> · **#587** (Steps 2–5 + 7 — the operate UI: `auth.js` login-module + approve/reject/submit/cancel
> + 403/409 inline + Monitor scroll fix + audit `[object Object]` fix + "approved by" badge +
> reseed helper; 2 spawned specialists = secure-for-pilot; preview-verified E2E) · **#588** (CSP
> defense-in-depth on the static mount, parallel session) · **#589** (STATUS reconcile s103).
> Suite 2223 passed / 7 skipped; ruff + mypy clean. **All ACs (AC-1…AC-10) MET.** MS-S1 not
> exercised (deterministic by design). **v2 sequels** designed-into-seams but out of scope: full
> user/password/session login (the `authHeader()` + `get_current_principal` seams), `GET /whoami`,
> ADR-016 S2 Phase B (`ServicePrincipal` registry + non-human-approver rejection at
> `resolve_gated_step`) paired with S1 (automated scheduler), and multi-operator RBAC.

## Goal

Flip the OCT Monitor (View H) from **watch-only** to **watch → operate**: let a named,
authenticated human operator **log in** (SD-A ii), resolve a `waiting_human` gate
(approve/reject each proposal + submit) and cancel a parked run, from the same screen,
with SoD enforcement and a tamper-evident audit actor. Concretely: (1) wire
`view-monitor.js`'s already-shipped-but-inert `state.mode === 'operate'` seam to the
shipped `POST /runs/{run_id}/gate/resolve`; (2) add a **login-form auth surface** over the
existing static-key backend — the operator enters their raw API key (+ a display identity),
it is validated against the backend, held as a `sessionStorage` **session** ("logged in as
&lt;person&gt;", with logout), and attached as `Authorization: Bearer <key>` on operate POSTs
**only** (reads stay header-less); (3) add a net-new governed `POST /runs/{run_id}/cancel`
endpoint + audit row (SD-B: `waiting_human`-only in v1); (4) run the operate demo on the
**procurement** vertical (SD-C) — which already authors 5 principals with real SoD (a
requester + four tiered-DOA approvers, `verticals/procurement/procedures.yaml:56-71`) — by
launching `OCT_VERTICAL=procurement` with `API_AUTH_ENABLED=true` and provisioning ONE
operator key for one approver principal (e.g. `appr-buyer`) via env. Reads stay ungated so
the list/detail remain viewable.

The login form is **login-SHAPED** but the credential is the pilot API key (PLAN-0047
pilot-grade), not real user/password auth — an honest caveat, not real authentication.
Full user/password/session login is a named **v2 sequel** built on two seams designed in
here (see SD-A + Out of Scope).

The operate demo is **MS-S1-independent**: the resolve→resume path is wired to a
DETERMINISTIC procurement executor factory (Step 6b), so no live LLM (MS-S1 / §8 host-state)
fires at resolve time. Real-LLM production executor wiring is a separate concern, NOT v1.

## Acceptance Criteria

- [ ] **AC-1** — In `operate` mode, `proposalPanel()` renders per-proposal approve/reject
      controls for EVERY proposal (mirroring `GateResolveRequest.decisions` — no silent
      default; submit is disabled until every proposal has an explicit decision). *(preview:
      Monitor → `data-view="H"` tab → a `waiting_human` run shows a control per `data-testid`
      proposal row; grep `view-monitor.js` for the new operate branch replacing the empty
      `mon-prop-ops` span at ~line 152.)*
- [ ] **AC-2** — A single "submit decisions" action POSTs `{step_id, decisions}` to
      `/runs/{run_id}/gate/resolve` with `Authorization: Bearer <key>` sourced from the
      auth-module (`authHeader()`); on `GateResolveResponse` the detail re-renders via the
      `loadDetail` path (run may complete, suspend again at a later gate, or fail). *(pytest
      against the endpoint asserts the request shape; preview asserts re-render to the new
      `run_status`.)*
- [ ] **AC-3** — The UI handles **403** visibly: RF-1 (no authenticated approver / auth off)
      AND `PrincipalSoDError` (self-approval / SoD violation — a real risk on procurement,
      requester ≠ approver) render a distinct, non-silent operator message (not a generic
      failure). *(preview: force 403 by submitting logged-out OR logged in as the run's own
      triggerer; grep for the 403-branch copy.)*
- [ ] **AC-4** — The UI handles **409** visibly: `StaleDataError` optimistic-lock ("was updated
      concurrently — reload and retry") triggers a reload-and-retry affordance, NOT a dead-end
      error; `ProcedureError` (409) surfaces its detail. *(pytest asserts the 409 detail string
      is surfaced; preview asserts the reload affordance appears.)*
- [ ] **AC-5** — A new `POST /runs/{run_id}/cancel` endpoint exists, mirrors the RF-1 guard
      (`auth.person_id is None → 403`, `runs.py:335-342`), writes the run to `cancelled`, and
      appends a `run_cancelled` audit row with `actor_person_id = auth.person_id` and
      `payload.actor_kind = "human"` (mirroring the `run_resumed` idiom at
      `services/engine/procedures/persistence.py:363-370`). *(pytest: cancel a `waiting_human`
      run → status `cancelled` + one `run_cancelled` audit row with the actor; cancel with no
      auth → 403.)*
- [ ] **AC-6** — Cancel is offered in the Monitor detail **only for `waiting_human`** (SD-B: a
      parked run has no in-flight effect → safe; `running`-cancellation is a named v2 concern);
      a cancel on any non-`waiting_human` run returns **409** the UI surfaces. *(preview: a
      cancel button appears on a `waiting_human` run and transitions it to `cancelled` on
      success; it is absent / rejected on other states.)*
- [ ] **AC-7** — The **login-form** auth surface (SD-A ii) is present: the operator enters a raw
      key + display identity, `login()` validates + stores a `sessionStorage` session, the UI
      shows "logged in as &lt;person&gt;" with a **logout** control, and `authHeader()` attaches
      `Bearer` on operate POSTs only; reads (`getJSON`) never send it. The credential source is
      isolated in a frontend **auth-module** (`login()` / `authHeader()` / `logout()`) so v2 can
      swap key → session token without touching the operate UI. *(preview: login form present,
      logged-in state + logout render; grep confirms the auth-module + `sessionStorage` + the
      header attached only on operate fetches, not `getJSON`.)*
- [ ] **AC-8** — The operate demo runs on the **procurement** vertical (SD-C): the launch is
      scoped `OCT_VERTICAL=procurement` with `API_AUTH_ENABLED=true`, and ONE operator API key
      for one existing approver principal (e.g. `appr-buyer`) is provisioned via env (`API_KEYS`
      JSON = `{sha256(raw): appr-…}`); NO raw key is committed to git (§8). **No new principal
      authoring** — procurement already ships 5 SoD principals. *(grep
      `verticals/procurement/procedures.yaml` confirms the existing `principals:` block; grep the
      diff for the absence of any raw key value; `.env.example`/runbook documents provisioning +
      the launch config.)*
- [ ] **AC-9** — Static asset edits bump the shared `?v=` token in `services/api/static/index.html`
      from **`c26` → `c27`** so a normal reload serves the new `view-monitor.js` + the auth-module.
      *(grep the new `c27` token on the edited script tags + a cache-busted runtime probe.)*
- [ ] **AC-10** — The LIVE resolve endpoint returns **200 (not 409 "no procedure-executor factory")**
      for a seeded `waiting_human` procurement run — i.e. a `procurement` executor factory IS
      registered in the running app (Step 6b) — AND the operate demo requires **NO live MS-S1 call**
      (the factory is deterministic). *(pytest: the demo-registration path registers a `procurement`
      factory so `registry.get_procedure_executors("procurement")` resolves + the resolve endpoint no
      longer 409s "no procedure-executor factory"; grep the factory reuses the deterministic
      hero-harness executors — `verticals/procurement/hero_demo/run.py` `_executors` — with NO
      `OllamaClient` / real-LLM `ActionStepExecutor` client in the resolve path.)*

## Out of Scope

- ❌ **Full user/password/session login** (an auth backend, credential store, session tokens,
      OAuth, cookies, refresh tokens) — the named **v2 sequel**. The clean upgrade: swap the
      auth-module's credential source (key → session token) + swap `get_current_principal`'s
      validation (key digest → session-token lookup); the resolve/cancel endpoints + the operate
      UI are untouched. Designed for here via the two seams; NOT built in v1.
- ❌ Cancelling a **`running`** run (a mid-effect compensating action) — SD-B names this a v2
      concern; v1 cancels only the effect-free `waiting_human` state.
- ❌ The **S1 scheduler** (automated gate-firing / scheduled runs) — sequel.
- ❌ **ADR-016 S2 Phase B** — the ServicePrincipal registry + library-level rejection of a
      non-human approver at the `resolve_gated_step` chokepoint (the scheduler path) — sequel.
- ❌ **Multi-operator RBAC** / role hierarchies / per-action permissions beyond the existing
      SoD run-check — sequel.
- ❌ Editing proposals or authoring new gates from the UI — v1 only decides EXISTING proposals.

## Steps

### Step 1: Backend — `POST /runs/{run_id}/cancel` (net-new)
Add the endpoint in `services/api/routers/runs.py` alongside `resolve_gate_endpoint`
(runs.py:313–413). Mirror the RF-1 guard verbatim (`if auth.person_id is None: raise
HTTPException(403, …)`, runs.py:335-342). Load the run (`load_run`), 404 if absent. Enforce
**SD-B**: reject any non-`waiting_human` run with **409**. Set `run.status =
PipelineRunStatus.CANCELLED.value` + `run.updated_at`, then `append_audit(action="run_cancelled",
actor_person_id=auth.person_id, run_id=…, payload={"actor_kind": "human"})` in the SAME commit
(mirror the `run_resumed` idiom at `services/engine/procedures/persistence.py:363-370`). Add a
`CancelRunResponse` model in `services/api/models/runs.py` (`{run_id, run_status}`). Note
`PipelineRunStatus.CANCELLED` (`services/engine/procedures/runs.py`) is defined but set by NO
transition today — this is its first writer.

### Step 2: Frontend — operate controls in `proposalPanel()`
Replace the empty `state.mode === 'operate'` branch (`view-monitor.js:151–152`, the inert
`mon-prop-ops` span) with per-proposal approve/reject controls keyed by `action_id`. Hold
decisions in local state; disable "submit decisions" until EVERY proposal has an explicit
decision (mirrors the endpoint's no-silent-default contract, `models/runs.py:172`). Keep the
`mode==='read'` inert branch for read-only mode.

### Step 3: Frontend — auth-module + login form (SD-A ii)
Add a frontend **auth-module** exposing `login(rawKey, identity)` / `authHeader()` / `logout()`
as the SINGLE credential seam (v1 = the raw API key; v2 = a session token — swap here, nothing
else). `login()` validates the key against the backend and, on success, stores a session in
`sessionStorage` (the raw key + the resolved/display identity); the Monitor renders a login form
when logged out and a "logged in as &lt;person&gt;" banner + logout when logged in. `authHeader()`
returns `{Authorization: 'Bearer <key>'}` for operate POSTs only; `getJSON` (reads) stays
header-less. **OPEN (SD-A tail, see Surfaced Decisions):** whether the "logged in as
&lt;person&gt;" display needs a lightweight "who am I" read (echo the person a key resolves to)
or the existing surface suffices — resolve in Step 3 against the shipped endpoints before adding
one.

### Step 4: Frontend — submit + re-render + error handling
On submit, POST `{step_id, decisions}` to `/runs/{run_id}/gate/resolve` with `authHeader()`; on
success re-render via the `loadDetail` path (`view-monitor.js:129–138`, `renderDetail` at :194)
so the run's new `run_status` shows. Handle **403** (RF-1 / SoD self-approval) and **409**
(`StaleDataError` reload-and-retry; `ProcedureError` detail) with distinct visible operator
messages (AC-3/AC-4).

### Step 5: Frontend — cancel button
Add a cancel affordance in `renderDetail()` shown **only for `waiting_human`** (SD-B), POSTing to
the Step-1 endpoint with `authHeader()`; on success re-render to `cancelled`; surface 403/409
(a cancel on a non-`waiting_human` run → 409 message).

### Step 6: Procurement operate-demo provisioning (SD-C)
No new principal authoring — procurement already ships 5 SoD principals
(`verticals/procurement/procedures.yaml:56-71`). Instead: (a) add/scope an `oct-demo-procurement`
launch config (mirror the `oct-demo-supply-chain` :8098 pattern in `.claude/launch.json`) that
runs `OCT_VERTICAL=procurement` with `API_AUTH_ENABLED=true` on its own port; (b) document
provisioning ONE operator API key for one approver principal (e.g. `appr-buyer`) via env
`API_KEYS` = `{sha256(raw): appr-buyer}` in `.env.example` / the demo runbook — NO raw key in git
(§8); (c) seed a run to the `waiting_human` gate: the procurement `emergency_sourcing_round`
suspends at its `approve` gate, and the existing hero harness
(`verticals/procurement/hero_demo/run.py` — ships per-kind executors + runs to the suspended
`approve` gate) is the seed path — VERIFY it persists a `waiting_human` run reachable by the
Monitor detail (it currently runs the pure run-check to capture the governance moment; confirm a
persisted-run seam or note the small seed shim needed). Reads stay ungated.

### Step 6b: Register a production (deterministic) procurement executor factory
**Why this Step exists (Code R2, verified on-disk):** the resolve flow calls
`_executor_factory(vertical)` (`services/api/routers/runs.py:106-110, 362`) =
`registry.get_procedure_executors(vertical)` (`services/engine/registry.py:99-106`), which
raises `RegistryError` → **409** when NO procedure-executor factory is registered for the
vertical. `register_procedure_executors` (`registry.py:85`) is invoked ONLY in tests — the live
`discover_and_register()` / `_register_vertical()` (`services/engine/discovery.py:37-71`)
registers per-vertical adapter + **handlers** but DELIBERATELY not an executor factory (OQ-6:
explicit registration, no import-scan). So today the live `/runs/{run_id}/gate/resolve` 409s for
EVERY vertical — the operate demo cannot resolve a gate until a `procurement` factory is
registered. This gap is independent of SD-A/B/C.

**Requirement + constraint:** register a **procurement** procedure-executor factory in the
running app so `_executor_factory("procurement")` returns a factory (not 409). Respect the OQ-6
design — **explicit** registration, NOT import-scan discovery — e.g. an explicit
`register_procurement_procedure_executors()` invoked at startup for the active vertical (or wired
into the `oct-demo-procurement` launch path from Step 6), NOT auto-discovered by
`discover_and_register()`. *(Code decides the exact registration seam at build — this Step names
the requirement + the constraint.)*

**Deterministic, MS-S1-independent:** the factory MUST reuse the deterministic per-kind executors
the procurement hero harness already ships (`verticals/procurement/hero_demo/run.py` `_executors`
at :221-241) bound to a **stub/fake client factory** (the same seam `run.py` swaps for the real
`OllamaClient` in a live smoke, :90, :232-233) — NOT the real LLM `ActionStepExecutor` bound to
Ollama. Rationale (explicit): on resolve→resume the procurement `source` step
(`autonomy: auto`, LLM-assist) and the post-`approve` `issue_po` gated ACTION would fire the LLM
via a real `ActionStepExecutor`; a deterministic factory keeps the operate demo self-contained and
MS-S1-independent (no live host-state / §8 LLM run at resolve time).

**Seed consistency:** the SAME deterministic executors seed the `waiting_human` run (the Step-6(c)
hero-harness seed) AND resolve it here — ONE consistent factory registered for `procurement`.

### Step 7: Cache-bust + tests
Bump the shared `?v=` token on `view-monitor.js`, `app.js`, and the new auth-module asset in
`index.html` from **`c26` → `c27`**. Add pytest for the cancel endpoint (Step 1) + the resolve
request-shape/error paths; add the preview checks per AC.

## Surfaced Decisions

All three surfaced decisions were **RATIFIED by Cray on 2026-07-06 (session 102)**. The chosen
option + one-line rationale + the noted alternatives are recorded below; the Steps/ACs above are
folded to the ratified shape.

- **SD-A — auth surface. RATIFIED: (ii) a login FORM over the existing static-key backend.**
  The operator "logs in" by entering their raw API key (+ a display identity), validated against
  the backend, held as a `sessionStorage` session with logout, and attached as `Bearer` on
  operate POSTs only. *Rationale: login-shaped UX + a real named-approver audit, with no new auth
  backend in v1.* **Alternatives noted:** (i) the minimal single pasted-key field (rejected — too
  bare for a governed-hero demo); (iii) a full user/password/session auth backend (rejected for
  v1 — over-scoped; deferred to v2). **v2-upgrade seam note (binding design constraint):** design
  TWO explicit seams so full login is a clean v2, NOT a rewrite — (1) a frontend auth-module
  (`login()`/`authHeader()`/`logout()`) so the credential SOURCE is swappable (v1 key → v2 session
  token), and (2) the backend's EXISTING `get_current_principal` (`services/api/auth.py:63-94`)
  stays the SINGLE auth dependency, so v2 swaps its validation (key → session token) without
  touching the resolve/cancel endpoints or the operate UI. **Honest caveat:** (ii) is
  login-SHAPED but the credential is the pilot API key (PLAN-0047 pilot-grade), not real
  user/password auth. **SD-A tail (open sub-question, resolve in Step 3, NOT re-surfaced):**
  whether the "logged in as &lt;person&gt;" display needs a lightweight "who am I" read (echo the
  person a key resolves to) or the existing endpoints suffice — a Step-3 implementation choice
  against the shipped surface, not a governance decision.

- **SD-B — cancel semantics. RATIFIED: `waiting_human` ONLY is cancellable in v1.** *Rationale:
  a parked run has no in-flight effect, so cancelling it is safe.* Cancel requires
  `auth.person_id` (mirror RF-1) and audits `run_cancelled` + `actor_kind:"human"`. A cancel on
  any non-`waiting_human` run returns **409**. **Alternative noted:** cancelling a `running` run
  (a mid-effect compensating action) — deferred to v2 as a named concern (out of scope).

- **SD-C — operate demo vertical. RATIFIED: the PROCUREMENT vertical (NOT aquaculture).**
  *Rationale: procurement already authors 5 principals with real SoD (requester ≠ approver, tiered
  DOA — `verticals/procurement/procedures.yaml:56-71`), a richer governed demo than aquaculture,
  and needs NO new principal authoring.* Provision one operator key for one approver principal
  (e.g. `appr-buyer`) via env; run `OCT_VERTICAL=procurement` + `API_AUTH_ENABLED=true`; seed a
  run to the `approve`/`waiting_human` gate via the existing hero harness. **Alternative noted:**
  authoring a fresh single-approver principal on aquaculture (rejected — new authoring for a
  poorer SoD story).

## Test plan

- **pytest** — cancel endpoint: `waiting_human` → `cancelled` + one `run_cancelled` audit row
  (actor + `actor_kind:"human"`); no-auth cancel → 403; a non-`waiting_human` state → 409 (SD-B).
  Resolve path: request shape `{step_id, decisions}`; 403 on `auth.person_id is None`; 409 detail
  string surfaced for `StaleDataError`. **Executor-factory registration (Step 6b / AC-10):** the
  demo-registration path registers a `procurement` factory (`get_procedure_executors("procurement")`
  resolves, no `RegistryError`) so the live resolve endpoint no longer 409s "no procedure-executor
  factory".
- **preview / browser** (Monitor via `data-view="H"` tab, NOT `location.hash`): login form
  present when logged out; logged-in banner + logout render after `login()`; operate controls
  render per proposal; submit disabled until all decided; submit re-renders to new `run_status`;
  403 (logged out / SoD self-approval) + 409 (stale reload-and-retry) messages visible; cancel
  button on `waiting_human` transitions to `cancelled`; read fetches header-less.
- **grep** — new operate branch replaces the inert `mon-prop-ops` span; the auth-module
  (`login`/`authHeader`/`logout`) + `sessionStorage` exist; `Bearer` attached only on operate
  fetches; `OCT_VERTICAL=procurement` launch config present; NO raw key in the diff; the existing
  procurement `principals:` block is used (no new principal authored); `?v=c27` bumped on the
  edited assets; the `procurement` executor factory (Step 6b) reuses the deterministic hero-harness
  `_executors` with NO `OllamaClient` in the resolve path.

## Verification

Governed hero end-to-end (procurement): with `OCT_VERTICAL=procurement` +
`API_AUTH_ENABLED=true`, the operator **logs in** as an approver principal (e.g. `appr-buyer`),
approves/rejects a `waiting_human` gate on `emergency_sourcing_round` and the run resumes (or is
cancelled) with a `run_cancelled` / `run_resumed` audit row naming the human; a logged-out submit
or an SoD self-approval (requester approving their own request) fails closed (403) visibly; a
concurrent resolve loses cleanly (409 reload-and-retry). This is the "watch → operate" milestone
on the richest governed vertical (real requester ≠ approver SoD + tiered DOA).
