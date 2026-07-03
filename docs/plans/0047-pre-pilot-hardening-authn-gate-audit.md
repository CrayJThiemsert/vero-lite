# PLAN-0047: Pre-pilot hardening — authn + run/gate endpoints, gate state machine, append-only audit + config pinning, CI

**Status:** Draft
**Owner:** Claude Code
**Created:** 2026-07-03
**Related ADRs:** ADR-0026 (principal identity + run-time SoD), ADR-016 (procedure engine), ADR-0025 (AT-2 typed governance) — this plan implements **enforcement/hardening on the shipped constructs and amends none of them**; if any step turns out to require an ADR amendment, execution stops and the question is surfaced to Cray.
**Related plans:** PLAN-0044 (A1b run enforcement + executors — done).

> **Drafting provenance (ADR-012 D4.3):** Drafted by the in-harness `plan-drafter`
> subagent under ADR-013 D1 phased authority, from the session-95 dispatch payload
> (3-specialist production-readiness audit, 2026-07-03). Outline originator: Code.
> Independent reviewer: Cray at PR merge. Separation: INTACT.

## Context

A 3-specialist production-readiness audit (2026-07-03, session 95) found pilot-blocking
gaps; Cray ratified the 7-item hardening-sprint ordering ("เห็นด้วยกับลำดับแก้ที่แนะนำ
ทั้ง 7 ข้อ"). **This plan scopes items 1–3 plus a minimal CI workflow (subset of
item 6) only.** Verified evidence anchors (re-checked against the working tree at
drafting time):

- **No authn anywhere:** the only `Depends` in `services/api/` is the DB session
  (`services/api/routers/actions.py:112`); `services/api/routers/admin.py` states
  "no auth (LAN/localhost demo box)". `POST /recommendations/{action_id}/approve`
  (`actions.py:98-106`) takes no identity.
- **Run/gate seams are library-only:** `run_procedure`
  (`services/engine/procedures/orchestrator.py:457-466`) and `resolve_gated_step`
  (`services/engine/procedures/action_step.py:333-343`) take
  `principal: Person | None` as a plain caller-supplied argument; no router exposes
  them (`services/api/routers/procedures.py` is a read-only catalog; `demo.py` is
  read-only governance/impact views).
- **Gate advances on artifact-presence alone:** `resume_run`
  (`services/engine/procedures/persistence.py:128-138`) marks the suspended step
  `complete` if `suspended.artifact is not None` — it never checks that
  `resolve_gated_step` actually ran, and never re-asserts SoD. `resolve_gated_step`
  never flips `target.status` (`action_step.py:473-477`), so a second call re-runs
  `approve()` + `gate_execute()` (`action_step.py:424-428`) — the handler fires
  twice. No idempotency key; no optimistic-lock/version column on `PipelineRun`.
- **Audit written after the effect:** handlers execute inside the loop; a single
  `session.commit()` follows (`action_step.py:425-427` vs `475-476`). `run_procedure`
  builds `PipelineRun`/`StepResult` in memory; persistence is a separate caller step
  (`persistence.py:45-50`).
- **No append-only audit / config pinning:** single all-powerful DB user `vero/vero`
  (`docker-compose.yml:5-8`); no GRANT/REVOKE/trigger in any migration
  (`alembic/versions/`, latest = `0004`); `services/engine/recommender.py:20-23`
  admits "no immutable audit log". `PipelineRun` records `procedure_id`/`agent_id`
  but no version/hash (`services/engine/procedures/runs.py:54-73`); `resume_run`
  validates the caller-supplied procedure re-read from disk (`persistence.py:92`) —
  a mid-flight DOA-ladder edit silently applies to old runs.
- **No CI:** `.github/` contains no `workflows/`; pre-commit runs ruff/mypy/jsonschema
  but not pytest. Offline baseline: ~2066 passed / 5 skipped.

## Goal

Close the three pilot-blocking gaps on the shipped procedure-governance path —
(1) real authentication with the missing run / gate-resolve HTTP endpoints and
identity bound server-side, (2) a gate state machine with idempotent resolution and
transactional (decision-before-effect) audit persistence, (3) an append-only audit
surface plus per-run governance-config pinning — and (4) stand up a minimal GitHub
Actions workflow that runs the offline gate on every PR, so every hardening claim in
this plan is enforced by CI from the moment it lands.

## Acceptance Criteria

Offline deterministic tests are the acceptance gate (CLAUDE.md §8 — no host-state /
live runs required). Each AC names its pre-committed pass/fail read.

- [ ] **AC-1 (authn fail-closed):** with authn enabled, an unauthenticated request to
  every state-changing endpoint (run, gate-resolve, approve, execute) returns
  **401/403**; an authenticated request succeeds and the resolved `person_id` appears
  in the persisted run/step record. *Pass/fail read:* new API tests assert both
  halves; grep confirms no state-changing route lacks the authn dependency.
- [ ] **AC-2 (no principal from the body):** the request models for
  `POST /procedures/{procedure_id}/run` and `POST /runs/{run_id}/gate/resolve`
  contain **no principal/person field**; a test posting a spoofed principal in the
  body shows the server-resolved identity (not the spoofed one) on the persisted
  record. *Pass/fail read:* test asserts persisted `person_id` == authenticated
  subject, != body value.
- [ ] **AC-3 (endpoints exist, typed):** both new endpoints ship with Pydantic
  request + response models, every field carrying `Field(description=...)`
  (CLAUDE.md §8); the run endpoint suspends at a gated step and returns the run id +
  status; the resolve endpoint applies decisions and returns the updated step.
  *Pass/fail read:* API tests drive run → suspend → resolve → resume through HTTP
  only (no library shortcut).
- [ ] **AC-4 (gate idempotency):** calling gate-resolve twice for the same step
  executes the handler **exactly once**; the second call is rejected (409-class
  error), verified via a counting stub handler. *Pass/fail read:* handler-invocation
  count == 1 and second response is an error.
- [ ] **AC-5 (state machine, not artifact-presence):** a run whose suspended step has
  an artifact but was **not** resolved through `resolve_gated_step` is **refused** by
  `resume_run` (fail-closed); a properly resolved step passes; resume re-asserts the
  recorded SoD verdict before continuing. *Pass/fail read:* both branches covered by
  new persistence tests; the artifact-presence branch for gated steps is gone from
  `persistence.py` (escalated-failure re-run branch retained).
- [ ] **AC-6 (write-ahead + decision-before-effect):** the `PipelineRun` row exists
  in the DB (status `running`) **before** the first step executes; the gate decision
  + audit record is committed in the same transaction as (or durably before) the
  handler effect — a handler that raises mid-resolve leaves a committed decision
  record and **no** phantom executed effect. *Pass/fail read:* DB-backed test
  injects a raising handler and asserts the post-crash DB state.
- [ ] **AC-7 (append-only audit):** an attempt to UPDATE or DELETE a committed audit
  record through the app's DB role fails at the database layer; each audit row
  carries a hash chaining to its predecessor, and a verification helper detects a
  tampered row. *Pass/fail read:* DB-backed test asserts the rejection + a
  hash-chain-verify pass on clean data / fail on mutated data. *(Shape gated on
  SD-3.)*
- [ ] **AC-8 (config pinning):** `PipelineRun` carries the resolved governance
  snapshot (ladder / SoD / rule) + content hash at start; after an on-disk edit to
  the procedure's governance config, `resume_run` and `resolve_gated_step` on the
  old run **fail closed** with an explicit pin-mismatch error (they never silently
  apply the new config). *Pass/fail read:* test edits the resolved config between
  suspend and resume and asserts the refusal; unedited config resumes normally.
- [ ] **AC-9 (migrations):** every new column/DDL lands as an Alembic migration
  under `alembic/versions/` (next after `0004`); `alembic upgrade head` on a fresh
  DB succeeds and the offline suite passes against it. *Pass/fail read:* migration
  test / CI job runs upgrade + suite.
- [ ] **AC-10 (CI):** `.github/workflows/` contains a workflow that, on every PR,
  runs ruff + `mypy --strict services/` + the pytest suite (scope per SD-4) and
  fails the PR on any failure. *Pass/fail read:* the PR that lands this plan shows
  the workflow green; a deliberate scratch failure (or the workflow's own log)
  demonstrates it actually gates.

## Out of Scope

- ❌ **Sprint item 4** — Alembic migration autogenerate (pairs with the v1 ontology
  batches; separate track).
- ❌ **Sprint item 5** — required-gate policy (during-pilot track).
- ❌ **Sprint item 7** — pitch wording (other track).
- ❌ **Sprint item 6 remainder** — deployment fixes (Dockerfile cannot boot the app —
  copies only `services/`, no `verticals/` or `alembic/`), backups, health checks.
  Only the CI workflow subset is in scope here.
- ❌ **Full ADR-011 audit framework** — stays earmarked, gated on real partner data
  (see SD-3; this plan ships at most the minimal append-only slice).
- ❌ **Reactive-loop durable persistence** (`actions.py:32` process-local store +
  the lossy `services/db/persistence.py` projection) — default deferred; see SD-2.
  (Binding identity onto the existing approve/execute endpoints IS in scope —
  item 1's "identity bound server-side".)
- ❌ **Amending ADR-0026 / ADR-016 / ADR-0025** — enforcement only; any step that
  would amend them stops and surfaces the question.
- ❌ **New verticals, ontology changes, UI work, live-model runs.**

## Surfaced Decisions (Cray adjudicates before the affected step starts)

- **SD-1 — Pilot authn mechanism (blocks Step 1).** Options: (a) **static
  per-person API keys** — hashed keys in server config/env mapped to `person_id`,
  sent as `Authorization: Bearer`; (b) signed session token (login endpoint +
  HMAC/JWT); (c) reverse-proxy header trust (proxy authenticates, app trusts a
  header). **Recommendation: (a)** — smallest surface for a 2-partner pilot,
  revocable per person, no session/login infra, no proxy dependency; keys stay out
  of git per §8 (env/`.env`, `.env.example` documents the shape). (b) adds login
  UX + token-expiry machinery the pilot doesn't need yet; (c) makes authn invisible
  to tests and couples correctness to deployment topology.
- **SD-2 — Reactive-loop (ADR-007) durable persistence in this plan?**
  **Recommendation: defer** — the procedure path is the pilot-critical one; the
  reactive loop gets identity binding on its endpoints now (AC-1) and durable
  persistence in a follow-up. Alternative: fold it in (adds a store rework + a
  fuller projection mid-sprint).
- **SD-3 — Minimal append-only audit now, without authoring ADR-011 first?**
  **Recommendation: yes, minimal** — ship an append-only audit table + restricted
  DB role (INSERT-only via REVOKE and/or a block-UPDATE/DELETE trigger) + a
  per-row hash chain, as migration DDL; the full audit *framework* (retention,
  export, external anchoring, PDPA surface) stays ADR-011, gated on real partner
  data. Alternative: author ADR-011 first (correct layering, but blocks a ratified
  pilot blocker on a document that needs partner input we don't have).
- **SD-4 — Do CI runs include the DB-backed tests?** **Recommendation: yes** — add
  a `postgres:16-alpine` service container to the workflow and set
  `TEST_DATABASE_URL` at the disposable test DB; AC-6/AC-7 assertions are
  DB-behavioral, so an offline-only CI would not guard exactly the properties this
  plan hardens. Alternative: offline-only subset first (faster to land, weaker
  gate), DB job as a fast-follow.

## Steps

Ordering: B (Steps 3–4) is engine-internal and unblocks nothing; A (Steps 1–2)
exposes it; C (Steps 5–6) adds the audit/pinning layer; D (Step 7) can land first
or in parallel — landing CI early is preferred so later steps merge under it.

### Step 1: Authn dependency + identity on existing endpoints *(blocked on SD-1)*

Add a FastAPI dependency (e.g. `services/api/auth.py::get_current_principal`) that
authenticates the request per the SD-1 mechanism and resolves the subject to a
`Person` **server-side** from the active vertical's authored principal set. Apply it
to every state-changing route, including the existing
`POST /recommendations/{action_id}/approve` and `/execute` (`actions.py`) and the
admin router (`admin.py` drops its "no auth" posture). Record the resolved
`person_id` on the approve/execute path's persisted projection. Fail-closed: missing
or unknown credential → 401; authenticated subject with no `Person` mapping → 403.
*Pre-committed pass/fail read:* AC-1 tests green; grep shows no state-changing route
without the dependency.

### Step 2: `POST /procedures/{procedure_id}/run` + `POST /runs/{run_id}/gate/resolve`

New router (or extension of `services/api/routers/procedures.py`) exposing the two
missing seams over `run_procedure` / `resolve_gated_step` / `resume_run`. Pydantic
request models carry only caller-legitimate fields (trigger context; per-action
decisions) — **never** a principal; the `principal: Person` argument is filled from
Step 1's dependency. Response models surface run id, status, suspended step, and
the resolved step's decisions/trace summary, all fields with
`Field(description=...)`. The resolve endpoint supplies the SoD resolution context
(`procedure` + `principals` + aliases) server-side, consistent with the
non-skippable check in `action_step.py:408-411`.
*Pre-committed pass/fail read:* AC-2 + AC-3 tests green (full HTTP-only
run→suspend→resolve→resume path).

### Step 3: Gate state machine + idempotency

In `resolve_gated_step`: on success, flip `target.status` from `waiting_human` to a
new `StepResultStatus.RESOLVED` value (statuses are stored as `Text` — no DDL for
the enum member itself). The existing `waiting_human` precondition
(`action_step.py:399`) then makes a second resolve fail — idempotent by state, not
by convention; surface it as 409 at the API. In `resume_run`
(`persistence.py:128-138`): replace the artifact-presence branch for gated/human
steps with a status check — only a `RESOLVED` step passes; `waiting_human`-with-
artifact is refused (fail-closed). Before continuing, resume re-asserts the SoD
verdict (the `governed_decision` audit tie from `action_step.py:472` must be present
on a SoD-constrained gate). Add a `version` (optimistic-lock) column to
`PipelineRun` and bump it on every state transition so concurrent resolve/resume
lose cleanly. Keep the escalated-failure (no-artifact) re-run branch unchanged.
Alembic migration `0005` for the new column.
*Pre-committed pass/fail read:* AC-4 + AC-5 tests green; existing PLAN-0044 suite
still green (SoD behavior unchanged).

### Step 4: Write-ahead run row + decision-before-effect audit

`run_procedure` (or a thin persistence-aware wrapper the API uses) persists the
`PipelineRun` row (status `running`) **before** executing step 1, and each
`StepResult` as it completes — not as a separate post-hoc `persist_run` call. In
`resolve_gated_step`, commit the decision + audit record **before or atomically
with** the handler effect: persist the per-action decision (status
`pending_execution`), commit, run the handler, then commit the receipt — so a crash
between decision and effect leaves a committed decision and no phantom effect
(current handlers are in-process, so same-transaction is acceptable where the
handler is not an external side effect; the pending→executed shape is the seam a
real outbox slots into later). Library callers (tests,
`verticals/procurement/hero_demo/run.py`) keep working via the wrapper.
*Pre-committed pass/fail read:* AC-6 DB-backed crash-injection test green.

### Step 5: Append-only audit role + hash chain *(blocked on SD-3)*

Migration `0006`: create the append-only audit surface — an `audit_log` table
(actor `person_id`, action, run/step refs, payload, `prev_hash`, `row_hash`,
timestamp) written at every governance-relevant transition (run start, gate
decision, handler receipt, resume, refusal); a restricted DB role for the app's
audit writes with INSERT-only rights (REVOKE UPDATE/DELETE + a block trigger, so it
holds even for the compose-default superuser path in dev); a pure-Python
hash-chain-verify helper. `docker-compose.yml` gains the role bootstrap; the
`vero/vero` credential itself is item-6-remainder territory and stays out of scope.
*Pre-committed pass/fail read:* AC-7 tests green (DB-layer rejection + chain
verify/tamper-detect).

### Step 6: Per-run governance-config pinning

Migration (same `0006` or `0007`): add `governance_snapshot` (JSONB — the resolved
ladder / SoD constraints / rule bindings) and `governance_hash` (Text) to
`pipeline_runs`. The orchestrator snapshots + hashes the resolved governance config
at run start (`runs.py` model + orchestrator write). `resume_run` and
`resolve_gated_step` recompute the hash from the caller-supplied procedure and
**fail closed on mismatch** with an explicit pin-mismatch `ProcedureError` (a
mid-flight DOA-ladder edit can no longer silently apply to an old run). Surface a
deliberate re-pin path only as a refusal message telling the operator to cancel +
re-run (no silent override).
*Pre-committed pass/fail read:* AC-8 test green (edit-between-suspend-and-resume
refused; clean config resumes).

### Step 7: CI workflow *(scope gated on SD-4; can land first)*

Add `.github/workflows/ci.yml`: on `pull_request` — checkout, `uv sync --extra dev`,
`ruff check`, `mypy --strict services/`, pytest. Per SD-4 recommendation: include a
`postgres:16-alpine` service container, run `alembic upgrade head` against a
disposable DB, export `TEST_DATABASE_URL`, run the full suite (baseline ~2066
passed / 5 skipped). No deploy/build/publish jobs (out of scope).
*Pre-committed pass/fail read:* AC-10 — the landing PR's checks are green and a
deliberate failure demonstrates gating; AC-9's upgrade-head runs here.

## Verification

- The full offline suite (plus the new AC-1..AC-8 tests) passes locally via WSL
  (`wsl bash -lc`, disposable `TEST_DATABASE_URL` DB) and in the Step-7 CI workflow —
  the offline oracle is the gate (CLAUDE.md §8); no live/host-state run is required
  by any step.
- Each AC's pre-committed pass/fail read is checked off in the PR that implements
  its step; the PR body cites the AC ids.
- End-to-end proof: one API-level test drives authenticate → run → suspend at gate →
  resolve (idempotent, SoD-checked, decision-committed-first) → resume (pin-verified,
  state-machine-gated) → completed, entirely over HTTP with a stub handler — the
  pilot-critical path exercised through every hardening layer this plan adds.
- After completion: `git mv docs/plans/0047-*.md docs/plans/done/` (Code-tab
  operation).
