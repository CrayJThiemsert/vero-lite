# PLAN-0100: The vero-lite exposure PLAN — a coherent published demo surface behind the ADR-0035 portal

**Status:** Draft
**Owner:** Claude Code (execution) + Cray (gates: ratification, live-evidence go, allowlist revision)
**Created:** 2026-08-03
**Related ADRs:** ADR-0035 (owner contract, `0035:875-887`), ADR-0032 (D1 wedge / D5 vocabulary), ADR-002 + ADR-0003 (amended-in-place context), ADR-007 (write gate — untouched). Related PLANs: PLAN-0095 (the image), PLAN-0093 (arm disclosure the degrade path rides), PLAN-0018 (llmctl), PLAN-0047 (authn seam), PLAN-0017/0040 (the intake/draft surfaces this PLAN hides in the published profile).

> **Drafting provenance (ADR-012 D4.3 / ADR-013 D1).** Drafted by the in-harness
> `plan-drafter` subagent from a Code-authored session-202 dispatch; the s202 UI
> ruling and the "PLAN-0100 owns the UI work" scope are Cray's typed picks, not
> drafter inferences. Every `file:line` below was re-verified on disk by the
> drafter at drafting time (branch `docs/plan-0100-exposure`, clean tree).
> Committed as `1e3275c`, merged as PR #1017.
>
> **Fold-in pass (session 205, `plan-drafter`, fresh dispatch).** Four verified
> findings folded in place: (1) `**Ruling:**` slots + AC-13 + BLOCKED-ON-SD
> markers on the PLAN-0101 adjudication pattern; (2) the Tab-H vs Tabs-I/J
> basis split applied consistently to the excluded table and SD-1; (3) the
> `54dfc7d` (PR #1018) measurement table recorded under AC-3 — dev half
> discharged, published half open; (4) SD-4 restated published-profile-only.
> No SD is ruled here — all five `**Ruling:**` slots are empty, awaiting Cray.
> Every new `file:line` re-verified on disk at fold-in. Independent review:
> Code (R2) at PR; ratification: Cray. Author≠reviewer separation: **INTACT**
> — Code commits per ADR-009 D2.

## Goal

Publish the synthetic OCT demo through the ADR-0035 portal as a **coherent**
surface: a published compose project (no `ports:` keys, edge-safe env profile), a
default-deny route allowlist with a declared per-route arm posture (**PROVISIONAL**
by design, D5's P12 ruling), pre-publication rate + concurrency caps, the D6
prompt-log regime (writer + rotation + populated RoPA-lite instance + in-app
notice banner), and — per Cray's typed session-202 ruling — **the UI work that
makes the published surface coherent**: every control whose backend the allowlist
excludes is hidden/removed in the published profile (the dev profile keeps them),
so no visible button 404s in front of exactly the audience the wedge exists to
impress. The nav-bar overflow fix is a **blocking** acceptance criterion before
any link is shared (`0035:883-887`). The live tunnel evidence (edge-timeout
measurement, eviction-coexistence check) is a single Cray-gated step with
pass/fail reads fixed before the run (CLAUDE.md §8).

### The correction this PLAN absorbs (Cray ruling, session 202)

ADR-0035 D5(5) closes with "**Env only — no code**" (`0035:484`), and its D5
preamble says "all config, zero app code, per L1" (`0035:433`). **Both are
contradicted by the ADR's own D5(2)** (`0035:436-440`): D5(2) rules that
`/intake/*` and `/warm`+`/sleep` "do not exist on the published surface — not
'exist but are patched'" — but the shipped UI mounts controls that call them
(census below). Excluding routes at the edge while leaving their controls on
screen ships a broken-looking demo. Cray ruled (s202, typed): **this PLAN owns
the difference** — the UI-coherence code, plus the in-app pieces the caps and
log regime require. This PLAN therefore never claims the exposure diff is
env-only; the ADR amendment owed for those lines is recorded in §"ADR amendment
owed" below and routed separately — **this PLAN does not edit ADR-0035**.

## The published-surface census (verified on disk, this drafting pass)

The UI's API seam is `services/api/static/assets/api.js` (all wrappers); view
modules call through it. Ten tabs are registered A–J (`app.js:9-26`). Excluded
backends and their live UI consumers:

| Excluded backend (D5(2) + this PLAN) | Live UI consumer (verified) |
|---|---|
| `GET /warm`, `GET /sleep` (`admin.py:174-179`, `:222-223` — keyed GETs, but the dependency goes inert when `api_auth_enabled=false`, `auth.py:71-72`) | `.llmctl` header cluster — `llm-control.js:114` (warm), `:144` (sleep); mounted `app.js:56-57`; styled `theme.css:239`; wrappers `api.js:157-158` |
| `POST /intake/extract`, `GET /intake/defaults`, `POST /intake/generate` | Tab E "Build a Vertical" (`app.js:14`; view registered `intake-view.js:411`; calls `intake-view.js:160,355`); **story surface** "Go live" beat calls `/intake/extract` (`view-story.js:907`; wrappers `api.js:181-185`) |
| `POST /procedures/draft/{classify,build,instantiate}` (this PLAN's ruling — see SD-2) | Draft-authoring wizard `intake-procedures.js:158,181,201` (wrappers `api.js:196-206`) |
| `POST /demo/hero/event` (the unauthenticated DB write — F4, `0035:186`) | Tab G event mode — `view-hero.js:658` (wrapper `api.js:99`) |

Controls whose backends **stay on the allowlist but are keyed** (approve/execute
`api.js:63-64` → e.g. `actions.py:224-228`; gate-resolve `api.js:105`) are
**not** hidden: with `API_AUTH_ENABLED=true` they fail closed with an honest
401/403 the UI already renders, and the demo script drives them with the
operator's provisioned key. The hide/remove rule applies to **excluded**
backends only — a 404 from a route that "does not exist" is incoherence; a 401
from a governed route is the product working.

⚠️ **That last argument had a hole until the s206 census closed it** (finding
C-1 below): the operator's key is *provisioned* by a `/whoami` probe
(`auth.js:39`), and `/whoami` appeared in **neither** table — so the paragraph
above rested on a route the same section default-denied. The allow row is now
present. Recorded rather than silently patched because the shape is worth
carrying: an allowlist that is complete with respect to the routes a **feature**
calls can still be incomplete with respect to the routes that make the feature
**reachable**.

## Pinned values (this PLAN pins them; ADR-0035 only recommended)

| Knob | Pinned value | Source of the recommendation |
|---|---|---|
| `API_AUTH_ENABLED` | `true` | D5(5) `0035:476-479`; setting exists `config.py:53-61` |
| `OLLAMA_HOST` | `http://host.docker.internal:11434` | D5(5) `0035:480-483`; default is a dev hosts-file name `config.py:79-82`; mechanism is `[ext]` — re-confirmed in Phase 5 |
| `LLM_REQUEST_TIMEOUT_S` | `25` | D5(4) `0035:467-475`; field `config.py:114-118`; valid env name — no `env_prefix`, case-insensitive `config.py:30-35`; absent from `.env.example` today |
| `LLM_RETRY_BUDGET` | `1` | D5(4); field `config.py:106-113` |
| Per-IP rate cap, LLM routes | 10 req/min, burst 20 | D5(3) `0035:441-451` |
| Global in-flight LLM cap | 1, fast-fail to the deterministic arm with the PLAN-0093 disclosure | D5(3) — no substrate exists (F5 `0035:187`; re-verified this pass: only LINE notify throttling, `services/notify/line.py:133,294-330`), so this is app code (see §ADR amendment) |
| Prompt-log retention | 90 days rolling, Cray-only reader, 30-day DSR honor, **no IP / headers / gate identity stored** | D6, ratified OQ-2 `0035:693-695` — restated, not re-decided |
| `UI_PROFILE` (new setting `ui_profile`) | `published` on the published deployment; default `dev` | This PLAN (s202 ruling); env name valid per `config.py:30-35` |
| `PROMPT_LOG_ENABLED` / `PROMPT_LOG_DIR` (new) | `true` / `/var/log/vero/prompt-log` (named volume `prompt-log`) on published; default `false` / same path | D6 `0035:513-515` |
| Published compose network name | `vero_oct` (the network the portal repo's connector joins — D4 `0035:409-413`) | This PLAN |

## The PROVISIONAL route allowlist + per-route arm posture

**This list is PROVISIONAL by design** (D5's P12 ruling, `0035:486-497`): the
first live measurement (P4 timeout, P5 eviction behavior) may revise it —
including any arm posture — **without reopening ADR-0035**. Revisions are made
by editing this table in a follow-up PR with the live-evidence artifact cited.
Enforcement is default-deny: anything not listed does not exist on the
published surface (D5(2)).

**Published (allow):**

| Route(s) | Method | Arm posture | Notes (consumer / DB posture) |
|---|---|---|---|
| `/`, `/assets/*` | GET | deterministic | the SPA itself |
| `/health` | GET | deterministic | healthcheck |
| `/meta` | GET | deterministic | UI boot (`api.js:60`, served `actions.py:209-212`); carries `ui_profile` after Phase 1 |
| `/objects/{type}` | GET | deterministic | Tabs A/D reads (`api.js:61`) |
| `/recommendations` | GET | deterministic | Tab B read (`api.js:62`) |
| `/recommendations/{id}/approve`, `/{id}/execute` | POST | deterministic | **keyed** (`actions.py:227`); operator-driven demo beat |
| `/whoami` | GET | deterministic | **keyed** — the reject-at-login probe (PLAN-0058, `auth.js:39`). Added at the Step-1 census (s206): it was in neither table, so it fell to default-deny — see §Step 1 finding C-1. Without it **no key can be stored**, and every keyed row in this table becomes undrivable |
| `/query` | POST | **assisted** | the wedge's NL query (`api.js:65`); capped + logged; carries the PLAN-0093 disclosure |
| `/insights/query` | POST | **assisted** (first candidate to flip to deterministic on P5 evidence) | LLM-before-first-DB-read (`0035:194-200`); capped + logged |
| `/procedures` | GET | deterministic | Tab F browse (`api.js:74`) |
| `/demo/hero/governance`, `/demo/hero/impact` | GET | deterministic | Tab G read modes (`api.js:96-97`) |
| `/runs/{id}`, `/runs/{id}/gate/resolve` | GET / POST | deterministic | Tab G beat 3 (`api.js:103,105`); resolve is **keyed** |
| `/llm/status` | GET | deterministic | read-only residency probe, never warms (INV-1, `api.js:156`); tentative — kept because Ask gates on MS-S1 status (`theme.css:184-186`); Step 1 census confirms the dependency, else it drops |

**Excluded (do not exist on the published surface; UI disposition owed by Phase 1):**

| Route(s) | Excluded per | Published-profile UI disposition |
|---|---|---|
| `/warm`, `/sleep` | D5(2) | `.llmctl` cluster **not mounted** (`app.js:56-57` gated) |
| `/intake/*` (all three) | D5(2) | Tab E **not registered** (`app.js:14` gated); story "Go live" beat must not fire (`view-story.js:907` — scripted fallback if one exists, else launcher hidden; Step 1 census decides which, and the guard-registry tripwire pins it either way) |
| `/procedures/draft/*` (all three) | this PLAN — SD-2 | draft-authoring wizard entries not rendered (`intake-procedures.js:158-201` call sites guarded) |
| `/demo/hero/event` | D5(2) (F4) | Tab G event-mode control not rendered (`view-hero.js:658` branch gated) |
| everything else (`/intake/generate` included above; `/api/exports/*`, `/cases*`, Tab H's off-list routes — GET `/runs` `view-monitor.js:168` **and also `view-map.js:84`, a Tab A caller the drafting census missed — see finding C-2**, POST `/runs/{id}/cancel` `view-monitor.js:148`, GET `/audit/verify` `view-monitor.js:488` — and any route not in the allow table) | default-deny | **Tabs I/J resolve with SD-1 + Step 1 census (BLOCKED-ON-SD-1); Tab H resolves with the Step 1 census alone** — its exclusions are default-deny, not DB-posture (see SD-1's scope note; two of H's routes are already on the allow table: `/runs/{id}` `view-monitor.js:235`, `/runs/{id}/gate/resolve` `view-monitor.js:133`, so H's backend is *not* entirely excluded); any tab whose entire backend is excluded is not registered in the published profile |

## Acceptance Criteria

Every AC names the artifact or test that closes it. No AC may be closed by
mocking the thing under test; where a local stand-in appears (AC-6/AC-7) it
stands in for the **upstream dependency** (Ollama), never for the route, cap,
degrade, or writer under test.

- [ ] **AC-1 (published UI coherence — the s202 ruling).** With
  `UI_PROFILE=published`, no control whose backend is excluded is rendered: no
  Tab E, no `.llmctl` cluster, no draft-authoring wizard entries, no hero
  event-mode control, no story live-extract firing. Closed by
  `tests/api/test_ui_profile.py`: (a) a `/meta` contract test (real app,
  env-set, asserts `ui_profile` is served — `httpx` against the ASGI app, per
  the existing `test_static_ui.py` pattern); (b) a **guard-registry
  set-equality tripwire** (Python, per `docs/conventions/ui.md:104`): for each
  excluded wrapper (`O.Llm.warm/sleep`, `O.Intake.*`, `O.Draft.*`,
  `O.Hero.event`) the test greps `assets/*.js` call sites and asserts the set
  of call sites **exactly equals** a pinned registry in which every entry names
  its profile guard — a new unguarded call site reddens the test.
- [ ] **AC-2 (dev profile unchanged).** With `UI_PROFILE` unset/`dev`, all ten
  tabs, the `.llmctl` cluster, and the wizard render exactly as today. Closed by
  the same test module (default-profile assertions) + the existing
  `tests/api/test_static_ui.py` suite staying green.
- [ ] **AC-3 (nav-bar overflow — BLOCKING before any link is shared,
  `0035:883-887`).** At pinned viewport widths **1280 / 1366 / 1440 / 1680 /
  1920**, `document.scrollingElement.scrollWidth <= clientWidth` and the header
  contains no horizontally clipped element, **in both profiles** — measured via
  the established preview_eval geometry procedure and recorded as a measurement
  table in this PLAN (dev half below; published half at closeout; the s197
  baseline: `scrollWidth 1825` vs `clientWidth 1382`, all 24 overflowing
  elements in the nav). The drafting-time responsive ladder (then
  `theme.css:189-213`, pre-`54dfc7d`) was written for an "A–E nav" of five
  tabs while `app.js:9-26` registers ten; the published profile still renders
  ≥8, so **hiding alone is not accepted as the fix** (see SD-4 — restated at
  fold-in). Plus a committed Python tripwire in
  `tests/api/test_static_ui.py`: extract the `VIEWS` keys from `app.js` and
  assert **set-equality** with the pinned census the ladder was measured
  against — adding tab K reddens the test and forces re-measurement.

  **Status at fold-in (s205): the dev half is DISCHARGED by `54dfc7d`
  (PR #1018); the published half stays OPEN** — it is not constructible until
  Step 2 lands `ui_profile` (verified at fold-in: zero `UI_PROFILE|ui_profile`
  matches under `services/`). `54dfc7d` rebuilt the ladder for the ten-tab
  census — the inactive-label collapse rung moved from `max-width 1360px` to
  `2299px` (now `theme.css:225`) — and both tripwires this AC asks for
  **already exist**, proven non-vacuous by probe:
  `test_tab_census_matches_the_measured_header_ladder`
  (`tests/api/test_static_ui.py:96`) and
  `test_header_ladder_collapses_inactive_tab_labels_by_default`
  (`tests/api/test_static_ui.py:112`). Do not re-run the dev pass (Step 4).
  Measurement record, **verbatim from `54dfc7d`'s commit body** — "Measured on
  the real page (ten tabs, 2026-08-03), not estimated":

  ```
    natural header width, every label + every chip ....... 2253px
    2560 viewport ................................ fits, overflow 0
    1920 viewport ................................ overflow  95px
    1440 viewport ................................ overflow 411px
    tab strip: full labels 1369px -> keys 478px (recovers ~890px)
  ```

  "Verified at the five widths PLAN-0100 AC-3 pins, against a pass/fail read
  fixed before the run (scrollWidth <= clientWidth AND no clipped header
  element)":

  ```
    1280 -> 0 overflow, 0 clipped     1680 -> 0 overflow, 0 clipped
    1366 -> 0 overflow, 0 clipped     1920 -> 0 overflow, 0 clipped (was 95)
    1440 -> 0 overflow, 0 clipped (was 411)
    2400 -> 0 overflow, full labels correctly return above the breakpoint
  ```

  `54dfc7d`'s own scope statement: "Partially discharges PLAN-0100 AC-3. The
  published-profile half of that AC stays open until UI_PROFILE exists
  (PLAN-0100 Phase 1); this covers the dev profile, which is the only one that
  exists today and was the one measured broken." This AC closes only when the
  published-profile pass is recorded here alongside the dev table (Step 4,
  under SD-4's ruling).
- [ ] **AC-4 (published env profile).** The published compose project pins every
  value in §Pinned values. Closed by `tests/deploy/test_published_compose.py`
  parsing the committed compose + env files (set-equality on the pinned keys;
  asserts `API_AUTH_ENABLED=true`, `LLM_REQUEST_TIMEOUT_S=25`,
  `LLM_RETRY_BUDGET=1`, `OLLAMA_HOST`, `UI_PROFILE=published`,
  `PROMPT_LOG_ENABLED=true`).
- [ ] **AC-5 (no published ports).** No service in the published compose file
  carries a `ports:` key (D1(1) `0035:256-264`; the dev compose publishes three —
  `docker-compose.yml:12-13,25-26,38-39` — and stays as-is per ADR-0003). Closed
  by the same test module (YAML parse, assert no `ports` key anywhere).
- [ ] **AC-6 (allowlist enforced + census-complete).** The published surface is
  default-deny. Closed by: (a) a set-equality test asserting the proxy config's
  allow rules exactly equal the table above; (b) a census tripwire asserting
  every route string fetched anywhere in `assets/*.js` is ∈ (allow ∪ excluded)
  — a new UI fetch to an unlisted route reddens it; (c) a documented local
  compose smoke on the dev box (not host-state): excluded routes → 404 at the
  proxy, allowed → served; pass/fail read written into the step before running.
- [ ] **AC-7 (caps — scenario-tested).** The global in-flight LLM cap of 1
  fast-fails to the deterministic arm with the PLAN-0093 disclosure. Closed by
  `tests/api/test_llm_inflight_cap.py`: boot the **real ASGI app**, point
  `OLLAMA_HOST` at a **real local HTTP server speaking the Ollama chat contract
  with controllable latency** (the upstream stand-in — realistic simulated
  responses, deliberately slow), fire two concurrent `POST /query` with
  realistic demo-script questions; assert the second returns fast (< 5 s) with
  the deterministic-arm disclosure while the first completes on the LLM arm;
  assert both produce prompt-log rows with correct outcome states. The per-IP
  rate cap (10/min burst 20) is proxy config: closed by the AC-6(a) config
  test + a rate-limit case in the AC-6(c) local smoke (burst 21 requests,
  assert the 21st is rejected at the proxy).
- [ ] **AC-8 (prompt-log writer — scenario-tested).** Same harness as AC-7:
  drive `POST /query` and `POST /insights/query` end-to-end; assert one JSONL
  line each with **key set exactly equal to** {ts_utc, route, vertical, text,
  model, outcome, arm} (D6 `0035:505-512`) — set-equality, so storing an IP,
  header, or identity reddens the test; assert `text` is the verbatim typed
  input; assert nothing is written when `PROMPT_LOG_ENABLED=false`. Rotation:
  plant files > 90 days old, invoke the rotation path, assert old deleted /
  young kept.
- [ ] **AC-9 (banner).** With `UI_PROFILE=published` the UI renders a persistent
  notice carrying all six D6 elements (typed text retained · 90 days · operator
  is sole reader · the gate processes the visitor's email via Cloudflare ·
  traffic transits the vendor's edge · demo is synthetic — enter no real
  personal data), absent in `dev`. Closed by a source-level Python tripwire
  (six-element presence + profile guard) in `tests/api/test_ui_profile.py`;
  final wording reviewed against ADR-0032 D5 vocabulary at R2.
- [ ] **AC-10 (governance artifacts).** A **populated** RoPA-lite instance
  exists (template `docs/conventions/partner-ropa-lite.md` §6 `:80`, §8 `:101`;
  demo posture: vero-lite = controller, Cloudflare = named recipient/processor
  per `0035:525-531`), and the runbook section below is complete — including the
  **manual purge command** (`0035:521-523`) and the 30-day DSR path. Closed by
  file existence + R2 review (no test can verify prose; the reviewer checks the
  D6 numbers appear verbatim).
- [ ] **AC-11 (live evidence — Cray-gated, single step).** The P4 edge-timeout
  measurement and the P5 eviction-coexistence check are executed **once**, after
  explicit Cray go, against pass/fail reads fixed in Step 10 **before** the run,
  and their artifacts are committed. The PROVISIONAL allowlist is then either
  revised (follow-up PR citing the artifact) or explicitly confirmed
  "no revision" in the closeout. A live run is evidence, not a CI gate — every
  offline AC above must already be green before this step is requested.
- [ ] **AC-12 (ADR amendment recorded, not performed).** §"ADR amendment owed"
  below names the exact ADR-0035 lines and proposed replacement text, and the
  closeout confirms Code routed it as a separate artifact. This PLAN's diff
  touches no file under `docs/adr/`.
- [ ] **AC-13 (adjudication record — the PLAN-0101 AC-9 pattern).** The five
  `**Ruling:**` slots in §Surfaced decisions are filled with Cray's typed
  rulings (value + date) **before** any step marked BLOCKED-ON-SD begins
  (Step 1's I/J allowlist-row finalization; Steps 3, 8, 9; Step 4's
  published-profile half). Closed by the filled slots themselves — Step 1's
  Output line points at them. This PLAN stays `Status: Draft` until Complete
  (an Accepted-status PLAN becomes G1-gated and Code cannot edit its own
  closeout).

## Out of Scope

- ❌ **The tenant-key PLAN — D7 (i)–(vii) in their entirety** (`0035:570-584`).
  ADR-0035 mandates **no ordering** between the two PLANs. Answering the
  dispatch's question directly: under SD-1(a) (DB-less published deployment)
  nothing persists, so `tenant_id` is not on this PLAN's critical path; even
  under SD-1(b) the column does not exist until that PLAN lands, so this PLAN
  ships a **commented** `# TENANT_ID=demo — activate when the tenant-key PLAN
  lands (ADR-0035 D7)` line in the published env file and takes no dependency
  either way.
- ❌ **The portal repo bootstrap** (`0035:868-874`): the `cloudflared` connector,
  ingress map, Access policies, `portal.` landing surface. This PLAN only pins
  the contract the connector consumes (network `vero_oct`, proxy service name,
  no ports) and states the audience need (an Access one-time-PIN allowlist for
  the demo audience).
- ❌ **Editing ADR-0035** (Cray's s202 ruling: record the amendment, route it
  separately) — and any other `docs/adr/` change.
- ❌ **Pilot posture** (D8 `0035:589-621`): per-route `Depends`, IdP/JWT, real
  data, off-LAN LLM endpoints — all future artifacts.
- ❌ **The dev compose file and dev UX**: `docker-compose.yml` keeps its ports
  (ADR-0003); the dev profile keeps every control.
- ❌ **Multi-tenant serving, RLS, per-request tenancy** (D7(vii)).

## Steps

Phases 0–4 are offline and deterministic — they land via normal PRs with no
host contact. Phase 5 is the only step that touches MS-S1 and is **single,
separately Cray-gated** (CLAUDE.md §8).

### Phase 0 — Preconditions (offline)

**Step 1: Restate OQ-4 + complete the census.**
- **OQ-4 restated (required here by `0035:702-704`): the portal domain is
  DELIBERATELY OPEN and non-blocking by construction (L6).** No artifact in
  this PLAN may reference a domain. Trigger: "the portal repo is stood up" —
  at that moment Cray picks the name and confirms whether the portal shares
  the existing Zero Trust account or gets its own. Phases 0–4 proceed without
  it; only Phase 5 needs the portal to exist.
- Complete the UI-route census: grep `assets/*.js` for every fetch outside the
  `api.js` wrappers (Tabs I/J and the insights caller were not fully walked at
  drafting; Tab H received a bounded fold-in walk, s205 — five call sites,
  recorded in the excluded table and SD-1's scope note — which this census
  re-verifies and completes). Finalize the **I/J** rows of the allowlist
  tables under SD-1's ratified answer (**BLOCKED-ON-SD-1**). Dispose of
  **Tab H** here in the census, on its own default-deny basis (SD-1's ruling
  cannot dispose of it — see SD-1's scope note): propose
  degrade-vs-not-registered in this step's PR; SD-1's answer bears on H only
  for whichever of its reads the walk shows to be DB-backed. Confirm whether
  Tab C gates on `/llm/status` and whether the story surface has a scripted
  fallback for its live-extract beat.
- Re-verify the fact anchors this PLAN inherits (F4/F5, `auth.py:71-72`,
  `admin.py:174-179,222-223`) against the working tree — Step 0 hygiene, not
  suspicion (CLAUDE.md §6).

**Census findings — the SD-free half, discharged in session 206.** Both were
found by walking `assets/*.js` call sites against the two tables above, and both
are `was an error` in the drafting census rather than drift: neither call site
has changed. Both are recorded here because each is a *silent* failure — the
published surface would look correct while behaving wrongly.

- **C-1 — `/whoami` was default-denied, which makes the published demo
  unloginable.** `auth.js:39` probes `GET /whoami` with the entered key *before*
  storing a session (PLAN-0058 reject-at-login); `auth.js:40-45` throws on any
  non-OK response, so `sessionStorage.setItem` at `:46` never runs. Under the
  allowlist as drafted the proxy would 404 that probe, the operator would see
  `"Login failed — invalid operator key (HTTP 404)"`, and **no key could ever be
  stored** — leaving approve/execute and gate-resolve undrivable even though both
  sit on the allow table as keyed routes. **Disposition: added to the allow
  table** (row above). This applies the PLAN's own §keyed-routes ruling — keyed
  routes stay allowed and fail closed with an honest 401 — to a route the census
  missed; it is not a new call, and Cray can veto it by striking the row.
- **C-2 — Tab A calls `GET /runs` directly, and the census attributed that route
  to Tab H alone.** `view-map.js:84` fetches `/runs` outside the `api.js`
  wrappers **deliberately** (`:76-79`: `O.API.request` would serve *mock* run
  markers on failure, and a fake governance marker is worse than none). Tab A is
  registered and allowed on the published surface, and `/runs` is default-denied,
  so on the published profile Tab A loses its run flags. **Disposition: no change
  proposed, and no code change needed** — `view-map.js:80` already catches and
  renders zero flags, which is AC-5's designed degrade. The excluded row now
  names this call site so AC-6(b)'s census tripwire (every route string fetched
  anywhere in `assets/*.js` ∈ allow ∪ excluded) can go green honestly rather than
  by omission.
  **⚠️ One question for Cray, demo-quality not safety:** the published Tab A will
  render *no* governed-run markers on the map. That is safe and already the
  code's behaviour, so it blocks nothing — but if the demo narrative wants those
  markers, `GET /runs` needs an allow row, which also hands Tab H one of its
  off-list reads. Deliberately **not** raised as a sixth SD: the safe default is
  already implemented, and inflating the all-or-nothing SD gate for a question
  with a working default would block five ruled steps on a sixth cosmetic one.
- Output: the completed tables in this PLAN (one PR). Cray's adjudication of
  SD-1..SD-5 lands as typed rulings (value + date) in the five `**Ruling:**`
  slots under §Surfaced decisions — AC-13 is the adjudication record. No step
  marked BLOCKED-ON-SD (Step 1's I/J row finalization; Steps 3, 8, 9; Step 4's
  published-profile half) begins before those slots are filled.

### Phase 1 — The published UI profile (offline; the s202 ruling)

**Step 2: `ui_profile` setting + boot contract.** Add `ui_profile: str = "dev"`
to `Settings` (env `UI_PROFILE`, valid per `config.py:30-35`) with
`Field(description=...)`; surface it to the UI at boot (the natural seam is the
`/meta` response the UI already loads — `api.js:60`, `app.js:98-113`; note
`buildTabs()` currently runs before `initMeta()` (`app.js:74,79`), so the
implementation must make the profile available before header/tab construction —
mechanism is the implementer's choice, behavior is pinned by AC-1/AC-2).

**Step 3: Gate the excluded-backend controls (BLOCKED-ON-SD-2 — the wizard
disposition; BLOCKED-ON-SD-1 — the census-surfaced tab set).** Apply the
§census disposition column: Tab E not registered; `.llmctl` not mounted;
wizard entries not rendered (SD-2's ruling decides whether all three draft
routes' entries go, or `instantiate`'s survives); hero event mode not
rendered; story live-extract beat guarded — plus the Tab I/J dispositions from
SD-1's ruling and Tab H's census disposition from Step 1. Ship the AC-1
guard-registry tripwire in the same PR (the registry is the census table,
executable).

**Step 4: Nav-bar ladder — published-profile half only (AC-3, blocking;
BLOCKED-ON-SD-4 as restated).** The dev half of this step is **already done —
do not re-run it**: PR #1018 (`54dfc7d`) rebuilt the ladder for the ten-tab
census (collapse rung now `theme.css:225`), measured before/after at the five
pinned widths against a pre-fixed pass/fail read, and committed both tripwires
probe-proven — the measurement table is recorded under AC-3. What remains:
once Step 2 lands `ui_profile`, execute SD-4's ruled option for the published
profile — measure at the five pinned widths via preview_eval against the same
pre-fixed pass/fail read, and record the published-profile measurement table
under AC-3 alongside the dev one.

**Step 5: The D6 banner (AC-9).** Published-profile persistent notice with the
six pinned elements; source tripwire; wording to R2 against ADR-0032 D5.

### Phase 2 — Resource posture code (offline)

**Step 6: Global in-flight LLM cap.** One process-wide slot at the LLM client
seam; on contention, the request takes the deterministic arm immediately and
the PLAN-0093 disclosure reports it honestly (no silent arm swap — that PLAN's
whole point). Ship the AC-7 scenario test in the same PR.

**Step 7: Prompt-log writer + rotation.** `PROMPT_LOG_ENABLED`/`PROMPT_LOG_DIR`
settings; append-only JSONL per day; the exact D6 field set; rotation deletes
files > 90 days on the write path; wired into the two published LLM routes.
Ship the AC-8 scenario test in the same PR. Default-off, so dev and CI are
untouched.

### Phase 3 — The published compose project + allowlist edge (offline)

**Step 8: `deploy/published/` (BLOCKED-ON-SD-1 — DB posture; BLOCKED-ON-SD-2 —
draft-route allowlist contents; BLOCKED-ON-SD-3 — whether the in-compose proxy
exists at all).** A committed compose project: `app` (the
PLAN-0095 image) + an `nginx:alpine` proxy that is the **only** thing the
connector reaches — deny-by-default allowlist (404 for everything else), per-IP
`limit_req` (10/min burst 20) on the LLM routes, network `vero_oct`, named
volume `prompt-log`, **no `ports:` keys on any service**, the pinned env file
(no secrets — `API_KEYS` provisioning stays env-local, documented in the
runbook; `.env.example` gains the two `LLM_*` names it lacks today, `.env.example:17,45,55`
context). DB posture per SD-1. Ship AC-4/AC-5/AC-6(a,b) tests in the same PR.

**Step 9: Local compose smoke (dev box — not host-state; BLOCKED-ON-SD-3 —
the AC-6(c) proxy cases presume the in-compose proxy).** Bring the published
project up on the Legion dev box; execute the AC-6(c)/AC-7 proxy cases against
the pre-written pass/fail read; record the transcript in the PR.

### Phase 4 — Governance artifacts (offline)

**Step 10: RoPA instance + runbook + live-evidence protocol.** Populate the
RoPA-lite instance (proposed home: `docs/compliance/ropa-published-demo.md`;
placement finalized at R2). Write the runbook section (below) into
`docs/runbooks/published-demo-operations.md`. Write the Phase 5 protocol with
its pass/fail reads **fixed now** (they are drafted in Step 11's box and
finalized here, before any go is requested). Record the ADR-amendment routing.

### Phase 5 — Cray-gated live evidence (HOST-STATE — single step)

**Step 11: The live run.** Preconditions: all offline ACs green; the portal
repo stood up (OQ-4 trigger fires — Cray names the domain); **explicit Cray go
recorded before any command touches MS-S1** (CLAUDE.md §8 — the gate covers
deploying the compose project, warming anything, and every SSH command).
One visit, minimized, under the D1(5) do-no-harm duty; also re-confirms the
`[ext]` facts on first touch (`0035:282-307`): Docker Desktop 24/7 posture,
`host.docker.internal` reachability, tunnel substrate.

Pass/fail reads, fixed before the run:
- **P4 edge-timeout measurement.** (i) Diagnostic sub-run: with the timeout
  temporarily at 120 s and the upstream stalled, record the vendor cut-off
  `T_edge`. FAIL if `T_edge < 40 s` (invalidates the 25 s profile's headroom —
  allowlist/profile revision required). (ii) Published-profile run (25/1): a
  stalled-LLM `POST /query` through the tunnel returns vero-lite's **own
  disclosed degrade** (HTTP 200, deterministic arm, PLAN-0093 fields) in
  < 35 s end-to-end, and **no vendor 5xx page is ever observed**. Both
  transcripts are the committed artifact.
- **P5 eviction-coexistence check.** During one capped vero-lite LLM call,
  record the Ollama residency timeline on MS-S1 (SSH — inside the same gate).
  The artifact is the timeline. Decision rule, fixed now: **if a single capped
  call evicts a resident neighbor model, every `assisted` row in the allowlist
  drops to `deterministic` until Cray re-rules** (the P12 bounded iteration,
  `0035:486-497`).
- Closeout: allowlist revised-or-confirmed (AC-11), measurement tables into
  this PLAN, then Draft → Complete → `git mv` to `done/`.

## Runbook section (lands as `docs/runbooks/published-demo-operations.md`)

Must contain, verbatim obligations from D6:
- **Manual purge command** (`0035:521-523`), operating on the named volume:
  `docker compose -p vero-oct exec app find /var/log/vero/prompt-log -name 'prompts-*.jsonl' -delete`
  — plus a date-scoped variant for partial purges. (Purge of log **files**; the
  underlying rotation function is AC-8-tested.)
- **DSR path (30 days):** locate + delete matching prompt-log lines/files;
  remove the requester's email from the vendor allowlist; file the vendor-side
  deletion request; note the action in the RoPA instance.
- Operate/teardown: bring-up order, the one-command kill (delete the tunnel
  route / stop the connector — portal-side), key provisioning for the demo
  operator, and the §8 reminder that every MS-S1 command needs Cray's go.

## ADR amendment owed (recorded here; routed separately — AC-12)

- `docs/adr/0035-hosting-and-exposure-model.md:484` — "Env only — no code."
  Should say (proposed): *"The two settings above are env-only. The published
  surface's full diff is not code-free — D5(2)'s exclusions require the
  published UI profile to hide the excluded controls, and D5(3)'s in-flight cap
  is app code (no substrate existed, F5) — both owned by PLAN-0100, per Cray's
  s202 ruling."*
- `0035:433` — "(all config, zero app code, per L1)" — same qualification: L1's
  ban is on per-route **authn** code, which remains honored (zero new
  `Depends`); it was never a ban on UI-coherence or cap code.
- `0035:631-634` (Consequences: "env + edge config + a log writer + a banner")
  — extend the enumeration with "+ the published UI profile + the in-flight
  cap", which the Consequences line half-acknowledged already.
- Route: G1-gated Accepted-body edit → per house rule it rides an in-context
  Cray approval in its own small `docs/*` PR (never flip-then-edit); Code owns
  routing. This PLAN's diff does not touch the ADR.

## Surfaced decisions (for Cray at ratification)

Rulings land in the `**Ruling:**` slots below as Cray's typed value + date
(AC-13 — the PLAN-0101 adjudication pattern). No step marked BLOCKED-ON-SD
begins until all five slots are filled.

- **SD-1 — Published deployment DB posture.** (a) **DB-less** (no postgres
  service; F4 bounded by construction *and* the allowlist; Tabs I/J and other
  DB-backed surfaces hidden in the published profile — census completes the
  list) vs (b) synthetic Postgres (full 10-tab story; F4 bounded by control
  only). **Recommendation: (a)** — ADR-0035's risk analysis leans on the
  DB-less bound (D8), the shareable link serves the zero-data guess-then-react
  wedge motion, and the full governed-loop demo remains a Cray-driven
  screen-share. This is Cray's call because it sets which tabs the public
  ever sees.

  **Scope of this ruling (fold-in, s205 — the H/I/J bases differ).** This SD
  disposes of **Tab I (Open a Case → `/cases*`, `app.js:21`) and Tab J
  (Month-End KPI → `/api/exports/*`, `app.js:26`)** plus any other DB-backed
  surface the Step-1 census surfaces. It does **not** dispose of **Tab H
  (Monitor, `app.js:17`)**, whichever way it is ruled: H never goes through
  the `api.js` seam (zero `monitor` hits in `api.js`; `view-monitor.js:86-92`
  ships its own raw `postOperate` over `fetch`), and its off-list routes are
  excluded by **default-deny**, not by DB posture — a bounded fold-in walk
  found GET `/runs` (`view-monitor.js:168`), POST `/runs/{id}/cancel`
  (`view-monitor.js:148`) and GET `/audit/verify` (`view-monitor.js:488`) off
  the allow table, while GET `/runs/{id}` (`view-monitor.js:235`) and POST
  `/runs/{id}/gate/resolve` (`view-monitor.js:133`) are **on** it, so H's
  backend is neither entirely excluded nor SD-1-contingent. H's disposition
  (degrade vs not-registered) resolves in the Step 1 census; only any of H's
  reads shown to be DB-backed inherit this ruling.

  **Ruling:** — awaiting Cray (typed value + date).
- **SD-2 — `/procedures/draft/*` disposition.** Not named in D5(2); same intake
  family. **Recommendation: exclude all three** — classify/build are
  unauthenticated MS-S1 inference (F3 `0035:185`), instantiate is deterministic
  but is authoring surface, not demo script; the published wedge demo does not
  hand anonymous visitors a procedure-authoring wizard. Alternative: allow
  instantiate only (zero-LLM). Cray's call because it widens D5(2)'s named set.

  **Ruling:** — awaiting Cray (typed value + date).
- **SD-3 — Allowlist enforcement point.** In-compose deny-by-default nginx
  (recommended: offline-testable, vendor-independent, satisfies "vero-lite's
  edge", carries the per-IP cap as pure config) vs vendor WAF path rules
  (config lives portal-side, not testable offline, silently driftable).
  Cray's call because it places a new service in the published stack.

  **Ruling:** — awaiting Cray (typed value + date).
- **SD-4 — Nav-bar fix depth (RESTATED at fold-in, s205 — published profile
  only).** The question as originally drafted — removals-only (published
  profile drops ~2 clusters; measured deficit 443 px at 1382 px viewport makes
  this unlikely to clear, and the dev profile stays broken) vs ladder rebuild
  for the real census, both profiles (recommended) — is no longer askable:
  **PR #1018 (`54dfc7d`) shipped the recommended option for the dev profile**
  (ladder rebuilt for the ten-tab census, measured green at all five pinned
  widths — table under AC-3 — with both tripwires committed and probe-proven),
  and removals-only was already rejected by that measurement. Neither original
  option is live. What remains is the **published-profile half**, which
  **cannot be measured today**: AC-3 requires measurement in both profiles,
  and the published profile is not constructible until Step 2 lands
  `ui_profile` (verified at fold-in: zero `UI_PROFILE|ui_profile` matches
  under `services/`). The restated question — once `UI_PROFILE=published`
  exists: (a) **measure-to-confirm (recommended)** — run the AC-3 pass against
  the `54dfc7d` ladder unchanged and accept green as the published-half
  discharge; the published profile only removes header content, so the rebuilt
  ladder is expected to clear a fortiori, and the census tripwire already pins
  the tab set — a red measurement re-opens fix depth as a bounded follow-up
  rather than silently; vs (b) re-tune the ladder for the published census
  **before** measuring — the published profile drops the `.llmctl` cluster and
  ≥2 tabs, freeing width (the `54dfc7d` record: "tab strip: full labels
  1369px -> keys 478px (recovers ~890px)") that could keep full labels at
  widths where the dev profile collapses to keys. Cray's call because
  "blocking before any link is shared" is Cray's bar to move.

  **Ruling:** — awaiting Cray (typed value + date).

- **SD-5 — Dev-profile geometry as blocking.** AC-3 as drafted measures both
  profiles. The strictly-ADR-0035 reading only blocks the published link.
  **Updated at fold-in (s205):** the dev half is already measured green
  (`54dfc7d`, table under AC-3), so this ruling no longer schedules any work —
  it sets the standing **bar**: under "keep both", a future dev-profile
  regression (e.g. a tab K reddening the census tripwire) blocks link-sharing
  until re-measured; under "published-only", it does not.
  **Recommendation: keep both** — the two committed tripwires already guard
  the dev census + collapse breakpoint at zero marginal cost. Cray may relax
  to published-only without touching anything else.

  **Ruling:** — awaiting Cray (typed value + date).

## Verification

- Offline: the named test files (`tests/api/test_ui_profile.py`,
  `test_llm_inflight_cap.py`, `test_prompt_log.py`, extended
  `test_static_ui.py`, `tests/deploy/test_published_compose.py`) green in the
  full-scope offline gate (full `mypy services/` + full `tests/`); the AC-3
  measurement tables recorded (dev half recorded at fold-in from `54dfc7d`;
  published half at closeout); the AC-6(c)/Step 9 smoke transcript in its PR.
- Live: the two Phase 5 artifacts, judged **only** against the pass/fail reads
  fixed in Step 10 — no post-hoc reinterpretation; INSUFFICIENT-EVIDENCE ≠ pass.
- Closeout: every AC checked with its closing artifact linked; allowlist
  PROVISIONAL status resolved (revised or confirmed); ADR amendment routed;
  PLAN → Complete → `docs/plans/done/`.
