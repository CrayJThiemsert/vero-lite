# PLAN-0018: Demo-Shell LLM Control — read-only `GET /llm/status` + MS-S1 warm/sleep affordance

**Status:** Done (shipped 2026-06-05, session 38 — Steps 1–3; see Completion)
**Owner:** Claude Code (Tier 2 executes; Cowork drafted per ADR-009 D1)
**Created:** 2026-06-05
**Related ADRs:** ADR-0015 (Consequences §Neutral — this PLAN's
forward-declaration; D5 live co-creation requires the operator to confirm
MS-S1 residency *before* the stakeholder types), ADR-0001 (`gpt-oss:20b`
model pin), ADR-002 (MS-S1 MAX host), ADR-009 (D1 Cowork drafts / D2 Code
commits)
**Related PLANs:** **PLAN-0017** (the consumer seam — its Out-of-Scope §2 +
Step 5 + AC-4 consume this affordance, building none of it),
**PLAN-0014** (done/ — minted `GET /warm` / `GET /sleep` + the
`OllamaUnreachableError` taxonomy this PLAN builds on), PLAN-0013 (the OCT
demo shell this UI lands in)

## Completion (2026-06-05, session 38)

**Shipped** — all acceptance criteria met; the backend is test-proven and the UI
was verified **live via Claude Preview against the real MS-S1** (`gpt-oss:20b`).

| Step | Deliverable | PR | Evidence |
|---|---|---|---|
| 1 | read-only `GET /llm/status` backend + typed model | **#166** (`d0c2e5d`) | 15 tests (INV-1/INV-2 mock-transport proof + AC-3…AC-6); suite 1177/2; ruff+mypy clean |
| 2 | demo-shell residency indicator + warm/sleep affordance | **#167** (`71e6c2d`) | live Preview cycle RESIDENT→guarded-sleep→COLD→warm(WARMING…)→RESIDENT; 0 console errors |
| 3 | runbook pre-warm checklist + STATUS + `git mv` to `done/` | this PR | runbook §5a; STATUS reconcile |

**AC outcomes.** INV-1 / INV-2 (poll-never-warms / read-only) + AC-1/AC-2
(mock-transport request-recording), AC-3 (states; a reachable-but-errored host
is never a false `cold`), AC-4 (right-model match — proven **live** while
`qwen3.6:35b` was *also* resident), AC-5 (short dedicated probe timeout), AC-6
(expiry honesty — a real nanosecond `expires_at` parsed, remaining-time
surfaced), AC-7 (guarded two-click sleep + auto-disarm — live), AC-8
(non-blocking warm + observable WARMING…→RESIDENT — live), AC-9 (typed Pydantic +
ruff/mypy/tests). **Delegated decisions resolved:** D-1 = a documented 5 s client
poll interval (no server-side cache); D-2 = route `GET /llm/status` on the admin
router, state enum `resident/cold/unreachable/error`, probe timeout =
`llm_status_timeout_s` (3.0 s), `warming` as a UI overlay.

> **Standalone + sequencing.** Independently PR-able: depends on neither
> the OQ-4 resolution nor PLAN-0017. **0018 ships before 0017**
> (Cray-ratified ordering) so the intake face builds once against the real
> status route — the status contract below is exactly PLAN-0017 AC-4's
> "clear, non-silent state" degradation substrate.
> **Drafted uncommitted** by Cowork (ADR-009 D1); no code/YAML/`.env`
> written during drafting; Code commits via PR (ADR-009 D2). File:line
> evidence verified live 2026-06-05 against the WSL working tree (dispatch
> reference HEAD `afb8c2f`).
> **Citation correction (drafter):** the dispatch's recovery-posture
> pointer reads "ADR-0014"; that slot is a withdrawn tombstone (cross-tab
> MCP transport). The actual substrate is **PLAN-0014**
> (`docs/plans/done/0014-llm-unreachable-telegram-notify.md`) —
> `admin.py`'s module docstring cites it directly. Cited as PLAN-0014
> throughout; erratum flagged in the completion handoff.

## Goal

A two-part demo-operator affordance, so the operator can confirm MS-S1 is
warm before the live moment and warm/sleep it deliberately from the shell:
**(1)** a read-only, pollable **`GET /llm/status`** reporting MS-S1
reachability + residency of the pinned recommender model — without the
poll ever loading the model; **(2)** an **in-UI residency indicator +
warm/sleep control** in the OCT demo shell, composed from the existing
`GET /warm` / `GET /sleep` routes (PLAN-0014) plus the new status poll.
Nothing is re-implemented — warm/sleep exist
(`services/api/routers/admin.py:53, 99`); the only net-new backend is the
status route (no `/llm/status` exists anywhere in `services/` —
grep-verified 2026-06-05).

## Contract invariants (non-negotiable, test-proven)

- **INV-1 — the poll must NEVER warm.** The status path (and any UI
  auto-poll built on it) issues **only** `GET /api/ps`
  (`OllamaClient.ps()` — the sole pure read,
  `services/engine/llm/client.py:182-186`) plus a reachability check. It
  never calls `warm()` / `unload()` / `/api/generate` — both mutators POST
  `/api/generate` and change residency (`client.py:159-180`). A
  warm-on-read status would re-load the model every poll cycle, pinning
  MS-S1 and defeating sleep.
- **INV-2 — read-only / non-destructive.** `GET /llm/status` changes no
  residency, no `keep_alive`, no host state. Idempotent and
  side-effect-free.

Both are proven in tests (AC-1/AC-2 below), not asserted in prose.

## Acceptance Criteria

*Naming note:* state names below (`unreachable` / `cold` / `resident` /
`warming` / `unknown`) are contract **concepts**; the literal enum values,
route shape, and response field names are Code's implementation call (see
Delegated decisions).

- [ ] **AC-1 (INV-1, test-proven):** a test records every request the
      status path issues (`httpx.MockTransport` — the client's existing
      injection seam, `client.py:79, 90`) and asserts the requested paths
      are exactly `GET /api/ps` (+ the reachability probe, if separate) —
      **never** `/api/generate`.
- [ ] **AC-2 (INV-2, test-proven):** the status call is non-destructive
      and idempotent — residency is unchanged across repeated polls.
- [ ] **AC-3 (R1 + R10 — states disambiguated; never a false `cold`):**
      status reports **≥3 distinct states** — at minimum `unreachable`
      (host down), `cold` (reachable, model not resident), `resident` — by
      branching `OllamaUnreachableError` vs `OllamaError` vs
      empty-but-reachable (`client.py:31-51, 150-157`). It does **not**
      blindly reuse `_ps_safe` (`admin.py:37-42`), which swallows every
      `OllamaError` to `[]` and collapses "powered off" and "on but
      evicted" — two worlds with different operator actions (power the box
      on vs just warm). A reachable-but-erroring host (bad JSON / non-2xx /
      mid-gen timeout) is reported as an explicit error/`unknown` state —
      never painted `cold`.
- [ ] **AC-4 (R2 — right-model residency):** residency is judged for
      `settings.recommender_model` specifically (`gpt-oss:20b` pin,
      ADR-0001; `services/api/config.py:77`), with tolerant tag matching
      (Ollama may report the bare name, an implicit/explicit `:latest`, or
      a digest). A foreign resident model is **not** `resident`.
- [ ] **AC-5 (R3 — bounded poll):** the status probe uses a short,
      dedicated timeout decoupled from `settings.llm_request_timeout_s`
      (the ~120 s *generation* timeout `_client()` inherits today,
      `admin.py:28-34`). Against a slow/half-down host, status returns
      within a small bound and degrades fast to `unreachable`/`unknown` —
      the indicator never hangs for a generation-length timeout per poll.
- [ ] **AC-6 (R8 — expiry honesty):** an `/api/ps` entry whose
      `expires_at` has already passed is never reported `resident` (it
      reads as `cold`); remaining-resident time is surfaced so the
      operator re-warms *before* the stakeholder types.
- [ ] **AC-7 (R5 — sleep is deliberate):** the in-UI sleep is destructive
      (frees VRAM → next LLM call is a ~11 s cold stall) and therefore
      **guarded** — a confirm step or an equivalently deliberate, visually
      distinct affordance; it cannot fire from a single accidental click
      adjacent to warm. Warm stays spam-safe (idempotent — a re-load just
      resets the `keep_alive` window, per the `admin.py` docstring).
- [ ] **AC-8 (R6 + R7 — non-blocking warm, observable transition):** the
      UI warm flow composes `GET /warm?wait=false` (`admin.py:64-70`) +
      polling status until `resident` — never the blocking default (~11 s
      page freeze when cold, `admin.py:53-62`). The warm→resident
      transition is observable (a `warming` state, or an equivalent
      non-flapping cold→resident progression) — the operator never stares
      at a dead `cold` mid-warm and re-clicks.
- [ ] **AC-9 (R9 — quality bar, CLAUDE.md §8):** the new route carries a
      typed Pydantic response model with `Field(description=...)` — the
      existing warm/sleep raw `dict[str, Any]` returns are prior art, not
      precedent. Type hints + tests + ruff clean + mypy clean.

## Decisions delegated to Code's PR (deliberate, not silent)

- **D-1 (R4 — poll amplification):** operator tab + stakeholder tab(s)
  each polling ⇒ O(tabs × Hz) `/api/ps` hits on MS-S1. Code chooses
  **either** a short server-side cache TTL **or** a documented client poll
  interval — named explicitly in the PR description so the posture is a
  decision, not an accident.
- **D-2 (boundary):** exact route path/shape, response field names, the
  state enum's literal values, the chosen short-timeout number, and all
  UI/CSS.

## Out of Scope

- ❌ **Auth** — the LAN/localhost **no-auth** demo posture stays,
  consistent with the existing unauthenticated demo routes (`admin.py`
  module docstring).
- ❌ **Re-implementing warm/sleep** — they exist (`admin.py:53, 99`); the
  UI composes them unchanged.
- ❌ **Model management beyond status + wiring** — no pull/delete/switch,
  no `keep_alive` tuning UI.
- ❌ **Persistence** — no status-history store; the poll is ephemeral.
- ❌ **The consumers** — extraction + NL-query degradation UX is
  **PLAN-0017** (Step 5 + AC-4), which consumes this contract and is not
  built here.

## Steps

### Step 1: read-only `GET /llm/status` backend

The net-new route: reachability + right-model residency built on `ps()`
**only**, branching the `OllamaUnreachableError` / `OllamaError` /
empty-but-reachable taxonomy (AC-3/AC-4; INV-1/INV-2 by construction),
expiry honesty from `expires_at` (AC-6), short dedicated probe timeout
(AC-5), typed response model (AC-9). Decide and record D-1 here.

### Step 2: demo-shell residency indicator + warm/sleep affordance

The indicator polls the status route; warm = `?wait=false` +
poll-to-`resident` (AC-8); sleep = guarded, deliberate control (AC-7). UI
specifics are Code's call (D-2).

### Step 3: verification + docs + closeout

Per-AC verification below; extend the run-oct-demo runbook with the
pre-demo warm checklist (status → warm → confirm `resident` — the seam
PLAN-0017 Step 6 ties into); STATUS update; `git mv` this plan to `done/`
on completion (Code's lane throughout, ADR-009 D2).

## Verification

- **AC-1/AC-2:** `pytest` with a request-recording mock transport — assert
  the status path's requested set is `{GET /api/ps}` (+ reachability probe
  if separate) and that residency is unchanged across repeated polls.
- **AC-3:** unit tests per branch — connect-refused ⇒ `unreachable`;
  reachable + `[]` ⇒ `cold`; reachable + pinned model resident ⇒
  `resident`; reachable + 5xx/bad-JSON ⇒ error/`unknown`, asserted
  **≠** `cold`.
- **AC-4:** foreign-model-resident fixture ⇒ not `resident`; tag-variant
  fixtures (bare name / `:latest` / digest) ⇒ `resident`.
- **AC-5:** slow/unresponsive-host simulation — status answers within the
  chosen bound (delayed mock transport or timeout-config assertion).
- **AC-6:** expired-`expires_at` fixture ⇒ not `resident`.
- **AC-7/AC-8:** live/manual demo-shell walkthrough per the runbook entry —
  sleep requires the deliberate path (adjacent-click test); warm-from-cold
  shows the transition and lands `resident` with no page freeze.
- **AC-9:** `ruff` + `mypy` clean; pre-commit passes.

---

*Drafter numbering check (Cowork, 2026-06-05): `docs/plans/` active =
0004/0010/0012/0017; `done/` tops at 0016 → **0018 free**, matching the
ADR-0015 Consequences §Neutral + PLAN-0017 Out-of-Scope §2
forward-declaration. Dispatch:
`.claude/handoffs/session-38/2026-06-05-1043-code-plan0018-llm-status-dispatch.md`.*
