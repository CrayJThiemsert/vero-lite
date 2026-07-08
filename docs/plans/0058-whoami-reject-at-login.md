# PLAN-0058: `GET /whoami` + reject-at-login

**Status:** Ready for execution
**Owner:** Claude Code
**Created:** 2026-07-08
**Related ADRs:** none new — executes the RATIFIED PLAN-0054 SD-A tail (`docs/plans/done/0054-control-leg-v1-oct-monitor-operate.md:259-262`) against the PLAN-0047 auth seam; `Person` semantics per ADR-0026
**Related PLANs:** PLAN-0054 (SD-A ratified 2026-07-06; `GET /whoami` named as a designed-into-seams v2 sequel at `0054:33`); PLAN-0047 (pilot-grade static API-key auth — the seam this reads)

> Authored by the in-harness `plan-drafter` subagent (ADR-013 D1 phased authority;
> ADR-012 D4.3 author≠reviewer disclosure). Outline originator: Cray (session 113
> next-work pick). Independent reviewer: Cray at PR merge; Code R2-verifies + commits
> (the drafter does not commit). Separation: INTACT.
> All four Surfaced Decisions (SD-1…SD-4) were **RATIFIED as-recommended by Cray on
> 2026-07-08 (session 113, via AskUserQuestion)** — the ACs/Steps below are folded to
> the ratified shape.

## Goal

Add a thin, deterministic **`GET /whoami`** read endpoint that echoes the principal the
existing auth seam resolves a bearer key to, and wire the frontend `login()` to probe it —
so a bad key is **rejected at LOGIN** instead of surfacing only as a 403 on the first
operate POST (the shipped optimistic behavior, documented at
`services/api/static/assets/auth.js:11-16`). This executes a **ratified direction with no
new governance surface**: **NO new ADR**, **NO new auth backend**, **NO change to
`get_current_principal`'s validation logic** — the endpoint *reads* the single fail-closed
dependency (`services/api/auth.py:63-94`) that PLAN-0054 SD-A locked as the one auth seam
(`0054:255-256`), resolving the SD-A tail's open "does the display need a lightweight
'who am I' read" question (`0054:259-262`) in the affirmative, as the endpoint v1
deliberately designed its seams for (`0054:33`). Everything here is offline,
deterministic, and MS-S1-independent — no LLM is touched.

## Acceptance Criteria

- [ ] **AC-1 — whoami echoes the resolved principal.** `GET /whoami` with a valid
      provisioned key returns **200** with the server-resolved identity (shape per SD-1):
      `person_id` always; the display name from the resolved `Person`
      (`services/engine/procedures/spec.py:749-768`) when the active vertical ships
      principals; `display_name: null` when it doesn't (the `person=None` no-principals
      branch, `auth.py:82-94`). The response model is Pydantic with
      `Field(description=...)` on every field (CLAUDE.md §8), mirroring the house pattern
      in `services/api/models/runs.py`.
- [ ] **AC-2 — fail-closed mirror.** whoami reuses `Depends(get_current_principal)`
      unchanged (per SD-2): missing/malformed header → **401** (`auth.py:73-76`), unknown
      key → **401** (`auth.py:80-81`), authenticated `person_id` with no `Person` mapping
      in a principals-shipping vertical → **403** (`auth.py:85-92`). No second auth code
      path exists — grep shows whoami injects the same dependency as
      `actions.py:223`/`runs.py:268`/`admin.py:177`/`intake.py:198`.
- [ ] **AC-3 — dev-escape behavior is defined.** With `api_auth_enabled=False` (the
      seam returns `AuthContext(None, None)`, `auth.py:71-72`), whoami returns **200**
      with `person_id: null` and an explicit `auth_enabled: false` field — the client can
      distinguish "auth is off (dev/demo)" from "authenticated as X". (Shape per the
      ratified SD-1/SD-2.)
- [ ] **AC-4 — reject-at-login.**
      `OCT.Auth.login()` probes `GET /whoami` with the entered key before storing a
      session: a 401/403 **rejects at login** with the server's error surfaced in the
      existing login-form error slot (`view-monitor.js:414-419`); a 200 stores the session
      (display identity per SD-1). The stale header comment at `auth.js:11-16`
      ("login() is OPTIMISTIC: the shipped API has no auth-validating READ to probe") is
      updated, and the static asset version token is bumped (`index.html:52`,
      `auth.js?v=c29` → next — preview caches static JS, project memory).
- [ ] **AC-5 — offline gate green.** Deterministic API tests per SD-4 (valid key → 200
      echo; no/unknown key → 401; unknown-person → 403; dev-escape → AC-3 shape) pass with
      the FULL offline suite + ruff + mypy under the required CI `gate` on a fresh PR. No
      MS-S1, no live LLM, no host-state action anywhere in this PLAN.

## Out of Scope

- ❌ Full user/password/session auth backend — the named v2 sequel (`0054:32-35`); v1
  stays key-based per PLAN-0054 SD-A.
- ❌ Any change to the resolve/cancel/operate endpoints or their auth injection.
- ❌ Any change to `get_current_principal`'s validation logic (`auth.py:63-94`) — whoami
  *consumes* the seam; it does not fork or extend it.
- ❌ Attaching `Bearer` to the monitor's data reads — `getJSON` reads stay header-less
  (`auth.js:9-10, 39`); the whoami probe is the ONE deliberate auth-validating read,
  called only from `login()`.
- ❌ Roles/RBAC exposure or enrichment beyond the SD-1-ratified echo shape.

## Steps

### Step 1: Backend — `WhoamiResponse` model + `GET /whoami` router
Add `services/api/models/whoami.py` with a `WhoamiResponse` Pydantic model
(`Field(description=...)` on every field; the ratified SD-1 shape:
`person_id: str | None`, `display_name: str | None`, `auth_enabled: bool`). Add
`services/api/routers/whoami.py` with `GET /whoami` injecting
`Annotated[AuthContext, Depends(get_current_principal)]` exactly like `runs.py:268` —
the handler is a pure echo (`person_id` from the context; `display_name` from
`auth.person.name` when `person` is not `None`, per `spec.py:763`). Register the router
in `services/api/main.py` beside the existing eight (`main.py:166-173`). No engine, DB,
or config change.

### Step 2: Tests — deterministic seam-mirror suite
New `tests/api/test_whoami.py` (or extend `tests/api/test_api_auth.py`) mirroring its
`auth_on` fixture pattern (`test_api_auth.py:31-36` — legacy conftest pins
`api_auth_enabled=False`, so auth-on tests flip it per-test with a provisioned digest →
person). Cases: (a) valid key → 200, `person_id` echoed + `display_name` resolved when
the vertical ships principals; (b) valid key, no-principals vertical → 200,
`display_name: null` (the `auth.py:94` branch); (c) missing header → 401; (d) unknown
key → 401; (e) provisioned `person_id` absent from a principals-shipping vertical → 403;
(f) `api_auth_enabled=False` → the AC-3 shape. All offline; no MS-S1.

### Step 3: Frontend — probe-at-login wiring
Make `OCT.Auth.login()` async: `fetch('whoami', { headers: { Authorization: 'Bearer ' +
key } })` before writing `sessionStorage` — non-200 → throw with the server detail
(rendered by the existing `catch` at `view-monitor.js:417-418`, which must become
promise-aware since `login()` is currently synchronous); 200 → store the session with the
display identity per SD-1. Update the `auth.js:11-16` header comment (the "no
auth-validating READ" premise is now false), bump `index.html:52`'s `?v=` token, and keep
`authHeader()`/`logout()`/reads untouched. One reviewable `feat` PR (may combine with
Steps 1–2 into a single XS PR at Code's discretion — the whole PLAN is XS–S).

### Step 4: Closeout
Preview click-through as confirming evidence only (login with a bad key → inline rejection;
valid key → banner) — cache-busted per project memory. STATUS reconcile + `git mv` to
`done/` per CLAUDE.md §6 Plan Flow.

## Surfaced Decisions

All four surfaced decisions were **RATIFIED as-recommended by Cray on 2026-07-08
(session 113, via AskUserQuestion)**. The recommendation + rationale text is retained
below with the ratified outcome stamped per entry; the ACs/Steps above are the ratified
shape.

- **SD-1 — whoami response shape: minimal echo vs richer.**
  *Recommendation:* minimal — `{person_id, display_name, auth_enabled}`. The only shipped
  consumer renders a single string ("Operating as `O.Auth.identity()`",
  `view-monitor.js:394`, today the user-TYPED identity from `auth.js:27,34`); `person_id`
  + the `Person.name` display field (`spec.py:759-763`) covers it, and `display_name`
  degrades to `null` cleanly on the no-principals branch (`auth.py:94`). *Alternatives:*
  include `roles` (`spec.py:764-768`) or the full `Person` — richer, but no shipped
  consumer needs it and exposing role sets on an echo endpoint widens the surface for no
  v1 value; add later if RBAC UI (a named v2 concern, `0054:35`) lands. *Why Cray:* the
  response shape is a public API contract — cheap now, breaking to change later.
  ✅ RATIFIED 2026-07-08 (Cray, session 113, via AskUserQuestion — as-recommended).
- **SD-2 — does whoami require auth (fail-closed) or act as a soft/unauthenticated probe?**
  *Recommendation:* fail-closed — reuse `Depends(get_current_principal)` verbatim, so a
  bad key → 401/403 exactly like every operate POST (`actions.py:223`, `runs.py:268`,
  `admin.py:177`, `intake.py:198`); that error IS the reject-at-login signal, and one seam
  means zero drift risk. Under the dev-escape (`auth.py:71-72`) the dependency is inert,
  so whoami returns the AC-3 shape (`200`, `person_id: null`, `auth_enabled: false`)
  rather than an error — consistent with every other endpoint being open in that mode.
  *Alternative:* a soft probe returning `{valid: bool}` without HTTP errors — friendlier
  status codes, but it forks the auth semantics into a second code path and weakens the
  fail-closed story. *Why Cray:* this sets whether an UNAUTHENTICATED caller can
  distinguish endpoint-exists (401) from anything else — a security-posture call, not an
  implementation detail.
  ✅ RATIFIED 2026-07-08 (Cray, session 113, via AskUserQuestion — as-recommended).
- **SD-3 — frontend scope: wire reject-at-login in this PLAN, or backend-only v1?**
  *Recommendation:* include the frontend wiring (Step 3) — it is the actual UX win named
  in this PLAN's title and small (~15 lines across `auth.js` + the `view-monitor.js:417`
  call site + a `?v=` bump); backend-only would ship a whoami nobody calls. *Surfaced
  because:* it touches the cached static asset (project memory: preview serves stale JS
  without a `?v=` bump), converts `login()` sync→async (a call-site contract change), and
  is the difference between "an endpoint" and "reject-at-login". *Alternative:*
  backend-only now, frontend in a follow-up — defensible if Cray wants the API contract
  ratified/merged before any UI motion. *Why Cray:* scope boundary of the deliverable.
  ✅ RATIFIED 2026-07-08 (Cray, session 113, via AskUserQuestion — as-recommended:
  frontend wiring IN scope; Step 3 + AC-4 are active).
- **SD-4 — test scope.**
  *Recommendation:* deterministic API tests only (Step 2's six cases), mirroring the
  seam's proven `test_api_auth.py` fixture pattern; frontend behavior verified by the
  Step-4 preview click-through as confirming evidence (the repo has no JS unit-test
  harness — PLAN-0054's frontend was preview-verified, `0054:29`). No MS-S1, no live
  runs. *Alternative:* add a JS test harness for `auth.js` — rejected as out of
  proportion for an XS PLAN. *Why Cray:* confirms the evidence bar for the frontend half
  matches prior practice rather than silently lowering (or raising) it.
  ✅ RATIFIED 2026-07-08 (Cray, session 113, via AskUserQuestion — as-recommended).

## Verification

**Binding bar:** the full offline suite + ruff + mypy green under the required CI `gate`
on a fresh PR (project memory: CI is PR-only — prove green via the PR's checks, full
suite, not a named subset). The Step-2 tests are the enforceable form of AC-1/2/3.
**Confirming evidence only (not a gate):** Step 4's preview click-through — bad key
rejected inline at login; valid key → "Operating as" banner; cache-busted asset fetch
confirms the new `?v=` token is live. Nothing in this PLAN touches MS-S1 or any
host-state (§8) surface.
