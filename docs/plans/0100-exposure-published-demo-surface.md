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
>
> **SD-sitting pass (session 207, Code, 2026-08-05).** ⚠️ The line above —
> "all five slots are empty" — describes the s205 state and is **superseded**:
> **all five SDs are now ruled** (Cray, typed 2026-08-05), and AC-13 is closed.
> Folded in the same pass: **finding C-3** (four allow-table rows the ruled DB
> posture cannot serve, two of them justified by a consumer this table excludes —
> the C-1 shape mirrored); **SD-3 restated and re-ruled** (ADR-0035 names no
> proxy; `cloudflared` ingress + the zone's Cloudflare rate-limiting rule win;
> **no `nginx` service**); the per-IP cap **re-pinned** to the Free-plan grammar
> measured on the zone; **Step 9's pass/fail read written** (AC-6(c) required it in
> advance and it was owed-but-unwritten); three `api.js` citations corrected.
> ⚠️ **Author≠reviewer separation is ABSENT on this pass** — Code both found C-3
> and wrote the fold-in, under no subagent drafting. The rulings are Cray's typed
> values; the surrounding analysis is not independently reviewed. A reviewer pass
> over C-3, the SD-3 restatement, and the Step 9 read is owed before Step 8 starts.
>
> **R2 review pass (session 207, three independent adversarial reviewers, all
> given a refute-not-bless mandate). The separation owed above is DISCHARGED —
> and it paid for itself.**
> - **C-3 — SOUND, 5/5 confirmed.** The reviewer independently re-enumerated all
>   eleven remaining allow rows for a DB dependency and found nothing C-3 missed.
> - **SD-3's ruling — SIX findings against it.** Cray re-affirmed the ruling as
>   **option (ii), "stay with cloudflared, fix the spec"** (2026-08-05). Three are
>   discharged by Step 8's new spec (anchoring, method non-enforceability,
>   bypass topology); **three are not** — a **blocking D4/L5 ADR debt**, a
>   vendor-branded 429, and NAT-shared-IP with no burst. All seven rows are
>   classified in SD-3's ruling table; none was summarised away.
> - **Step 9's v1 read — NOT FIT to gate.** Its "non-404" bar scored **4/5
>   against a completely dead app**, and it never drove `POST /query` — the wedge
>   itself. Rewritten as v2 with exact statuses, body assertions, a preflight
>   gate, both POST rows, and an explicit not-covered list.
> - **Two corrections to this PLAN's own prior text.** `GET /recommendations` was
>   pinned `deterministic` but is **LLM-backed** — so SD-1's recorded consequence
>   that "`/query` is the only published LLM route" was **false and is retracted**;
>   the live consequence is tracked as **OI-1**. And ~14 `api.js` citations were
>   stale by exactly **+7**: the s207 pass corrected three instances of that shift
>   without recognising it was systematic. All are now corrected from a
>   whole-file grep rather than an inherited list.

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
| `GET /warm`, `GET /sleep` (`admin.py:174-179`, `:222-223` — keyed GETs, but the dependency goes inert when `api_auth_enabled=false`, `auth.py:71-72`) | `.llmctl` header cluster — `llm-control.js:114` (warm), `:144` (sleep); mounted `app.js:56-57`; styled `theme.css:239`; wrappers `api.js:164-165` |
| `POST /intake/extract`, `GET /intake/defaults`, `POST /intake/generate` | Tab E "Build a Vertical" (`app.js:14`; view registered `intake-view.js:411`; calls `intake-view.js:160,355`); **story surface** "Go live" beat calls `/intake/extract` (`view-story.js:907`; wrappers `api.js:188-192`) |
| `POST /procedures/draft/{classify,build,instantiate}` (this PLAN's ruling — see SD-2) | Draft-authoring wizard `intake-procedures.js:158,181,201` (wrappers `api.js:203-210`) |
| `POST /demo/hero/event` (the unauthenticated DB write — F4, `0035:186`) | Tab G event mode — `view-hero.js:658` (wrapper `api.js:106` — citation corrected s207; the drafting census said `:99`) |

Controls whose backends **stay on the allowlist but are keyed** (approve/execute
`api.js:70-71` → e.g. `actions.py:224-228`; gate-resolve `api.js:112`) are
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
| Per-IP rate cap, LLM routes | **10 requests / 10 s, mitigation 10 s**, as the zone's single Cloudflare rate-limiting rule. ⚠️ **Raised from the 2/10 s first drafted at the sitting — needs Cray's nod, because it is ~6× the ADR's recommended sustained rate.** Reason: review finding 6 — Free counts **per IP with no burst allowance**, so a partner org behind one NAT egress IP shares one counter and 2/10 s hard-blocks the room mid-demo. The threshold is therefore set to tolerate a demo room, not to minimise sustained rate. **What actually bounds MS-S1 is the global in-flight cap of 1** (D5(3), shipped in Step 6), which serialises LLM work regardless of this number; a crawler or prefetch storm — the threat `0035:460-463` names — still trips 10/10 s cold. If Cray prefers the stricter reading, 2/10 s is a one-field change in the Cloudflare rule and needs no code | **Re-pinned under SD-3's ruling (Cray, 2026-08-05).** D5(3) `0035:441-451` *recommended* "10/min, burst 20" — that is nginx `limit_req` grammar (`rate=10r/m burst=20`), and the ADR never names an implementation. Cloudflare's Free plan offers a **10 s counting period and 10 s mitigation timeout only, and has no burst concept** (measured on the zone — see SD-3). `0035:446` states the numbers as "recommended defaults **for the exposure PLAN to pin**"; the ADR's binding requirement is that a per-IP cap *exists* before publishing, which this satisfies on the three grounds `0035:460-463` gives. **No ADR amendment owed** (AC-12 unchanged). |
| Global in-flight LLM cap | 1, fast-fail to the deterministic arm with the PLAN-0093 disclosure | D5(3) — no substrate exists (F5 `0035:187`; re-verified this pass: only LINE notify throttling, `services/notify/line.py:133,294-330`), so this is app code (see §ADR amendment) |
| Prompt-log retention | 90 days rolling, Cray-only reader, 30-day DSR honor, **no IP / headers / gate identity stored** | D6, ratified OQ-2 `0035:693-695` — restated, not re-decided |
| `UI_PROFILE` (new setting `ui_profile`) | `published` on the published deployment; default `dev` | This PLAN (s202 ruling); env name valid per `config.py:30-35` |
| `PROMPT_LOG_ENABLED` / `PROMPT_LOG_DIR` (new) | `true` / `/var/log/vero/prompt-log` (named volume `prompt-log`) on published; default `false` / same path | D6 `0035:513-515` |
| Published compose network name | `vero_oct` — ⚠️ **restated s207-R2.** As drafted this row read "the network **the portal repo's connector** joins", which SD-3's ruling contradicts: under (ii) **vero-lite ships its own `cloudflared`**. Under the amendment's reading (a) this network carries `app` + vero-lite's own connector and **no other connector joins it** (finding 3 — a second connector on this network reaches `app:8000` and bypasses the ingress allowlist entirely). Under reading (b) the original wording returns. **Pin the final wording when the D4/L5 amendment is ratified** — see §ADR amendment owed | This PLAN + D4 `0035:409-413` |
| `OCT_VERTICAL` | ⚠️ **UNPINNED — owed.** Added s207-R2 because the DB-less boot guarantee depends on it: the two *unwrapped* startup calls (`main.py:234` `fetch_objects`, `:242` `registrar()`) are DB-free for the **`energy`** default (`config.py:179-180`), which is what the independent review verified. The published demo shows the **procurement** hero (`/demo/hero/*`), so if it runs `OCT_VERTICAL=procurement` the DB-less boot claim is **unverified for the vertical actually deployed** | This PLAN — Step 8 must pin it **and** re-verify those two call sites for whichever vertical is pinned |

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
| `/meta` | GET | deterministic | UI boot (`api.js:67`, served `actions.py:209-212`); carries `ui_profile` after Phase 1 |
| `/objects/{type}` | GET | deterministic | Tabs A/D reads (`api.js:68`) |
| `/recommendations` | GET | **assisted** ⚠️ **CORRECTED s207-R2 — was `deterministic`, which was WRONG** | Tab B read (`api.js:69`). `recommender.py:194-195` states it outright: *"Recommend an action for an OperationalEvent — **LLM-backed** (ADR-010 D5)"*; the deterministic rule path (`_rule_recommend`, `:252-269`) is the **`except` fail-safe**, not the primary path. **See open item OI-1 below — this route is currently neither capped nor prompt-logged, which D6 requires of a published LLM route.** |
| `/recommendations/{id}/approve` | POST | deterministic | **keyed** (`actions.py:230-247`); operator-driven demo beat. DB-free — mutates the process-local `_action_store` (`actions.py:47`) only. **`/{id}/execute` was split off this row and excluded under SD-1** — see the excluded table |
| `/whoami` | GET | deterministic | **keyed** — the reject-at-login probe (PLAN-0058, `auth.js:39`). Added at the Step-1 census (s206): it was in neither table, so it fell to default-deny — see §Step 1 finding C-1. Without it **no key can be stored**, and every keyed row in this table becomes undrivable |
| `/query` | POST | **assisted** | the wedge's NL query (`api.js:72`); capped + logged; carries the PLAN-0093 disclosure |
| ~~`/insights/query`~~ | — | — | **EXCLUDED under SD-1 (Cray, 2026-08-05)** — moved to the excluded table. It reads the run corpus from Postgres (`insights.py:283` session dep, `:348` `execute_run_query`), which the DB-less posture cannot serve. Arm posture was beside the point: even pinned deterministic it would 500 rather than return its designed `"No runs matched that question."` refusal (`insights.py:349-357`) |
| `/procedures` | GET | deterministic | Tab F browse (`api.js:81`) |
| `/demo/hero/governance`, `/demo/hero/impact` | GET | deterministic | Tab G read modes (`api.js:103-104` — citation corrected s207; the drafting census said `96-97`). DB-free by construction: `demo.py:36-37` states it outright — *"The two READ views are deterministic + offline (no mutation, no DB, no LLM)"* |
| ~~`/runs/{id}`, `/runs/{id}/gate/resolve`~~ | — | — | **EXCLUDED under SD-1 (Cray, 2026-08-05)** — moved to the excluded table. Two independent reasons, either one sufficient — see finding C-3 |
| `/llm/status` | GET | deterministic | read-only residency probe, never warms (INV-1, `api.js:163`); tentative — kept because Ask gates on MS-S1 status (`theme.css:184-186`); Step 1 census confirms the dependency, else it drops |

**Excluded (do not exist on the published surface; UI disposition owed by Phase 1):**

| Route(s) | Excluded per | Published-profile UI disposition |
|---|---|---|
| `/warm`, `/sleep` | D5(2) | `.llmctl` cluster **not mounted** (`app.js:56-57` gated) |
| `/intake/*` (all three) | D5(2) | Tab E **not registered** (`app.js:14` gated); story "Go live" beat must not fire (`view-story.js:907` — scripted fallback if one exists, else launcher hidden; Step 1 census decides which, and the guard-registry tripwire pins it either way) |
| `/procedures/draft/*` (all three) | this PLAN — SD-2 | draft-authoring wizard entries not rendered (`intake-procedures.js:158-201` call sites guarded) |
| `/demo/hero/event` | D5(2) (F4) | Tab G event-mode control not rendered (`view-hero.js:658` branch gated) |
| `POST /recommendations/{id}/execute`, `GET /runs/{id}`, `POST /runs/{id}/gate/resolve`, `POST /insights/query` | **SD-1's DB-less ruling** (Cray, 2026-08-05) — see finding C-3 | All four are DB-backed and there is **no global exception handler anywhere in `services/api/`**, so under the DB-less posture each returns an **unhandled 500**, not a typed degrade. Published-profile UI disposition: **Tab B's Execute control not rendered** (Approve stays — it is DB-free); Tab G's Act panel is already unreachable (it mounts only in event mode, `view-hero.js:641`, and event mode is excluded above); the Ask/insights entry point for `/insights/query` not rendered. Guard-registry tripwire (AC-1) pins all three |
| everything else (`/intake/generate` included above; `/api/exports/*`, `/cases*`, Tab H's off-list routes — GET `/runs` `view-monitor.js:168` **and also `view-map.js:84`, a Tab A caller the drafting census missed — see finding C-2**, POST `/runs/{id}/cancel` `view-monitor.js:148`, GET `/audit/verify` `view-monitor.js:488` — and any route not in the allow table) | default-deny | **Tabs I/J: NOT REGISTERED** (SD-1 ruled (a), Cray 2026-08-05 — the BLOCKED-ON-SD-1 marker here is released). **Tab H still resolves in the Step 1 census on its own default-deny basis** — but the s205 note that "two of H's routes are already on the allow table … so H's backend is *not* entirely excluded" is **no longer true**: SD-1's C-3 disposition moved `/runs/{id}` (`view-monitor.js:235`) and `/runs/{id}/gate/resolve` (`view-monitor.js:133`) to the excluded table, so **every** Tab H backend route is now off the allow table. By this row's own closing rule — *any tab whose entire backend is excluded is not registered* — H's census disposition is now determined rather than open. Classified **superseded by new info** (the ruling changed the facts), not an error in the s205 note |

## Open items surfaced after ratification (OI)

- 🔴 **OI-1 — `GET /recommendations` is a published LLM route that is neither
  rate-capped nor prompt-logged. Found s207-R2 by an independent reviewer; NOT
  covered by any SD ruling, and it needs a decision before Step 8.**
  `recommender.py:194-195` — *"Recommend an action for an OperationalEvent —
  **LLM-backed** (ADR-010 D5)"*; the deterministic rule path (`_rule_recommend`,
  `:252-269`) is the `except` fail-safe. Consequences, all live in today's code:
  - An anonymous visitor's **first Tab B load after every container start** fans
    out unauthenticated MS-S1 inference. This is precisely the F2/F3 exposure D5
    exists to bound — *"the gate is the only thing between the internet and
    MS-S1's GPU"* (`0035:430-432`).
  - The Cloudflare rate rule is scoped to the LLM routes as pinned; **as long as
    that scope names only `/query`, this route is uncapped.**
  - **No prompt-log row is written** (`query.py` records; `actions.py` does not),
    so D6's regime — the RoPA instance, the 90-day retention story, the purge and
    DSR commands in the runbook — does not describe this route's traffic at all.
  - **Runnability hazard for Step 9:** with `OLLAMA_HOST` unreachable, this route
    walks `LLM_REQUEST_TIMEOUT_S` × retry budget × events before degrading, and
    can exceed the edge read ceiling — returning a vendor 5xx on the demo's main
    read. Each failure also calls `notify_llm_unreachable()` (`recommender.py:256-258`),
    i.e. **an anonymous public GET can page Cray on Telegram**.

  **Three options — Cray's call, none of them taken here:**
  **(a)** extend the rate-cap scope **and** the prompt-log writer to
  `/recommendations` (D6-coherent; adds work to Steps 7/8);
  **(b)** pin the published profile to force this route down the deterministic
  path (keeps Tab B, removes it from the LLM surface — needs a settings seam that
  does not exist today);
  **(c)** accept it as an uncapped, unlogged LLM route and say so explicitly in
  the RoPA + notice. ⚠️ **(c) conflicts with D6 as written** and should not be
  chosen silently.
  **Not raised as a sixth SD** — the SD gate is closed and all five are ruled;
  this is a post-ratification finding and is tracked here instead.

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
  default-deny. Closed by: (a) a set-equality test asserting the **committed
  `cloudflared` ingress config's** allow rules exactly equal the table above, and
  that the config's final entry is the catch-all `http_status:404` (SD-3's ruling
  — the target is the ingress file, not an nginx config; a remotely-managed
  token-only tunnel would void this AC and is forbidden by Step 8); (b) a census
  tripwire asserting every route string fetched anywhere in `assets/*.js` is ∈
  (allow ∪ excluded) — a new UI fetch to an unlisted route reddens it; (c) a
  documented local compose smoke on the dev box (not host-state): excluded routes
  → 404 at the edge, allowed → served; **pass/fail read written into Step 9 in
  advance — done, fixed 2026-08-05.**
  ⚠️ **Scope limit, stated so the closeout cannot overstate it:** (a) covers the
  route allowlist only. The **per-IP rate cap lives in the Cloudflare zone**, which
  is portal-side and has no file in this repo — **no offline test can close it.**
  It closes on AC-6(c) case 4 plus a screenshot of the configured rule, and if
  case 4 cannot run locally it is deferred to Step 11 and recorded as not covered.
- [ ] **AC-7 (caps — scenario-tested).** The global in-flight LLM cap of 1
  fast-fails to the deterministic arm with the PLAN-0093 disclosure. Closed by
  `tests/api/test_llm_inflight_cap.py`: boot the **real ASGI app**, point
  `OLLAMA_HOST` at a **real local HTTP server speaking the Ollama chat contract
  with controllable latency** (the upstream stand-in — realistic simulated
  responses, deliberately slow), fire two concurrent `POST /query` with
  realistic demo-script questions; assert the second returns fast (< 5 s) with
  the deterministic-arm disclosure while the first completes on the LLM arm;
  assert both produce prompt-log rows with correct outcome states. **The per-IP
  rate cap is NOT closed here and NOT closed by AC-6(a)** — under SD-3's ruling it
  is a Cloudflare zone rule with no file in this repo. It closes on AC-6(c) case 4
  (drive `POST /query` past the pinned threshold from one IP; assert rejection **at
  the edge**, and recovery after the 10 s mitigation window), or, if the local
  smoke does not sit behind the Cloudflare edge, on Step 11 with that deferral
  recorded explicitly. The in-flight cap (app code) and the per-IP cap (zone
  config) are **separate obligations with separate evidence** — a green AC-7 says
  nothing about the per-IP cap.
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
  ⚠️ **Widened s207-R2 — and one entry is now BLOCKING, which it was not before.**
  The D4/L5 connector-ownership conflict (the fourth entry) is not a
  documentation-tidying amendment like the other three: SD-3's ruling relocates
  the connector across a boundary the ADR assigns to the portal repo, and
  `0035:421-424`'s own drift trigger fires. **Step 8 must not start until that
  amendment is routed and ratified.** The other three entries remain
  record-and-route-later.
- [x] **AC-13 (adjudication record — the PLAN-0101 AC-9 pattern) — CLOSED
  2026-08-05: all five slots carry Cray's typed ruling + date; every
  BLOCKED-ON-SD marker is marked RELEASED at its step.** The five
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
- ❌ **The portal repo bootstrap** (`0035:868-874`): Access policies, the `portal.`
  landing surface, and the cross-system ingress map. ⚠️ **Narrowed s207-R2 — this
  bullet previously excluded "the `cloudflared` connector, ingress map" outright,
  which SD-3's ruling now contradicts**: under (ii) vero-lite ships its own
  `cloudflared` **and** its own committed ingress config. That relocation is exactly
  the D4/L5 conflict recorded in §ADR amendment owed, and it is why Step 8 is
  blocked on that amendment. This PLAN pins the contract the arrangement consumes
  (network `vero_oct`, no published ports — the "proxy service name" clause is
  **dropped**, there is no proxy service under (ii)) and states the audience need
  (an Access one-time-PIN allowlist for the demo audience).
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
  tables under SD-1's ratified answer (**BLOCKED-ON-SD-1 — RELEASED 2026-08-05;
  ruled (a), so Tabs I/J are not registered**). Dispose of
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
  **RESOLVED at the SD sitting (Cray, 2026-08-05): `GET /runs` is NOT added.**
  SD-1's DB-less ruling answers it structurally rather than by preference — runs
  live in Postgres (`runs.py:343` `load_run`), so a DB-less deployment has no run
  corpus to mark the map with; an allow row would buy a 500 in place of a clean
  empty state. The `view-map.js:80` degrade stands as the designed behaviour.

- **C-3 — four allow-table rows cannot be served by the posture SD-1 rules, and
  two of them were justified by a consumer the same table excludes.** Found at
  the SD sitting (s207) by tracing every allow-table handler for a DB session
  dependency, because SD-1's recommendation and the allow table had never been
  checked *against each other*. Two independent defects, either one sufficient:
  - **DB-backed under a DB-less posture (hard 500).** `POST /recommendations/{id}/execute`
    (`actions.py:253` session dep → `:267` `persist_executed_action`, no
    `try/except` around it), `GET /runs/{id}` (`runs.py:336,343`),
    `POST /runs/{id}/gate/resolve` (`runs.py:426,454,474,512`), and
    `POST /insights/query` (`insights.py:283,348`). The app itself **boots fine**
    without Postgres — the engine is lazy (`services/db/session.py:1-6`) and all
    three lifespan DB touches are fail-soft (`main.py:265,282,305`, comments at
    `:269,:294` naming "the DB-less demo (PLAN-0095) must still boot"), verified
    live in s177 (`docs/runbooks/run-oct-demo.md:114-121`). But there is **no
    global exception handler or middleware anywhere in `services/api/`**, so each
    of these four routes returns an unhandled 500 rather than degrading. The
    sharp one is `execute`: the allow table called it "operator-driven demo beat",
    so Approve would succeed and Execute would 500 — **the Tab B loop dying at its
    last step, in front of the audience the wedge exists to impress.**
  - **The reachability inversion (holds regardless of DB posture).** The runs pair
    was justified in the allow table as *"Tab G beat 3"*. Beat 3's Act panel mounts
    only in event mode — `view-hero.js:641`, `if (mode === 'event') container.appendChild(renderActPanel(...))`
    — and `renderActPanel` is the pair's only Tab G caller (`view-hero.js:317,320`).
    Event mode fires `O.Hero.event()` (`view-hero.js:658`) → `POST /demo/hero/event`,
    which **this table excludes**. So on the published surface those two rows had
    **zero Tab G callers**, and their only surviving caller is Tab H, whose
    registration this PLAN leaves undecided. **This is C-1 mirrored:** C-1 was a
    route *missing* that made a feature undrivable; C-3 is two routes *present*
    whose reachability path is excluded. The generalisation at §census —
    completeness w.r.t. routes a feature **calls** ≠ completeness w.r.t. routes
    that make it **reachable** — cuts in both directions, and neither direction is
    visible from the table alone.
  - **Disposition:** all four moved to the excluded table under SD-1's ruling.
    Method note for the closeout: the drafting census walked *UI call sites →
    routes*; C-3 needed the orthogonal walk, *routes → handler DB dependency*.
    Neither walk finds the other's defect.
- Output: the completed tables in this PLAN (one PR). Cray's adjudication of
  SD-1..SD-5 lands as typed rulings (value + date) in the five `**Ruling:**`
  slots under §Surfaced decisions — AC-13 is the adjudication record. No step
  marked BLOCKED-ON-SD (Step 1's I/J row finalization; Steps 3, 8, 9; Step 4's
  published-profile half) begins before those slots are filled.

### Phase 1 — The published UI profile (offline; the s202 ruling)

**Step 2: `ui_profile` setting + boot contract.** Add `ui_profile: str = "dev"`
to `Settings` (env `UI_PROFILE`, valid per `config.py:30-35`) with
`Field(description=...)`; surface it to the UI at boot (the natural seam is the
`/meta` response the UI already loads — `api.js:67`, `app.js:98-113`; note
`buildTabs()` currently runs before `initMeta()` (`app.js:74,79`), so the
implementation must make the profile available before header/tab construction —
mechanism is the implementer's choice, behavior is pinned by AC-1/AC-2).

**Step 3: Gate the excluded-backend controls (BLOCKED-ON-SD-1 / -SD-2 — both
RELEASED 2026-08-05).** Apply the §census disposition column, now fully
determined: Tab E not registered; `.llmctl` not mounted; **all three** draft-wizard
entries not rendered (SD-2 ruled exclude-all — `instantiate`'s entry does not
survive); hero event mode not rendered; story live-extract beat guarded; **Tabs
I/J not registered** (SD-1(a)); Tab H per Step 1's census, where the runs pair's
exclusion now leaves "not registered" as its only coherent option. **New under
SD-1's C-3 disposition:** Tab B's **Execute** control not rendered (Approve stays
— it is DB-free), and the insights/Ask entry point for `/insights/query` not
rendered. Ship the AC-1 guard-registry tripwire in the same PR (the registry is
the census table, executable) — and note the registry must now pin **three more**
controls than the drafting census listed.

**Step 4: Nav-bar ladder — published-profile half only (AC-3, blocking;
BLOCKED-ON-SD-4 — RELEASED 2026-08-05, ruled (a) measure-to-confirm).** The dev
half of this step is **already done —
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

**Step 8: `deploy/published/` (BLOCKED-ON-SD-1 / -SD-2 / -SD-3 — all three
RELEASED 2026-08-05).** A committed compose project with **exactly two services**:
`app` (the PLAN-0095 image) + `cloudflared` (**no `nginx`** — SD-3's ruling). No
`postgres` service (SD-1). Specifics:
🔴 **BLOCKED — do not start.** The D4/L5 connector-ownership amendment
(§ADR amendment owed) must be routed and ratified first. Under reading (b) this
step's shape changes materially, so building now risks rework.

- **`cloudflared` runs as a locally-managed tunnel** so its `config.yml` is
  **committed in this repo** — that file is AC-6(a)'s set-equality target. Its
  `ingress:` block lists exactly the allow table's routes and ends with the
  mandatory catch-all `- service: http_status:404`, which **is** the
  deny-by-default enforcement. Do **not** use a bare `TUNNEL_TOKEN`
  remotely-managed tunnel: that moves the ingress map into the dashboard, out of
  the repo, and silently voids AC-6(a).
- 🔴 **Every `path:` pattern MUST be anchored at both ends** (`^/query$`,
  `^/objects/[^/]+$`, `^/recommendations/[^/]+/approve$`, …). cloudflared matches
  `Path` as an **unanchored regex** (`r.Path.Regexp.MatchString` — verified in
  cloudflared's `ingress/rule.go`), so an unanchored `path: /query` **also admits
  the SD-1-excluded `/insights/query`**, and `path: /recommendations` admits the
  excluded `…/execute`. AC-6(a) must assert anchoring on every pattern, not just
  set-equality of the route list — an unanchored allowlist passes set-equality
  while admitting excluded routes.
- 🔴 **The Method column is NOT edge-enforceable.** The ingress Rule struct has
  only Hostname, Path, Service, Handlers, Config — **no method field**. A path
  allow therefore admits **all methods** on that path. The allowlist remains
  expressible because path alone separates every allowed route from every
  excluded one, but AC-6(b) must treat the Method column as documentation and the
  census tripwire must not assume method filtering exists.
- 🔴 **Topology, against the bypass (review finding 3).** `app` joins **only** an
  internal network reachable by vero-lite's own `cloudflared`. **No other
  connector may join it** — a second connector on `vero_oct` reaches `app:8000`
  directly and skips the ingress allowlist entirely, producing byte-identical
  AC-6(a) output. State the network layout explicitly in the compose file and
  prove it in Step 9.
- **Pin `OCT_VERTICAL`** (§Pinned values) and **re-verify `main.py:234` and
  `:242`** — the two unwrapped startup calls — are DB-free for whichever vertical
  is pinned. The DB-less boot guarantee was verified for `energy` only.
- **Free-plan expression caveat.** Confirm at implementation time whether the
  Cloudflare rate rule needs `hostname` scoping or path-only suffices; the working
  fallback is path-only (the zone's other app is n8n, which serves `/rest/` and
  `/webhook/` — no collision with `/query`). Record which was used.
- **The per-IP cap is NOT in this compose** — it is the zone's single Cloudflare
  rate-limiting rule (§Pinned values). Step 8's PR body records the rule's
  configured values; the rule itself is portal-side (see SD-3's ⚠️).
- network `vero_oct`, named volume `prompt-log`, **no `ports:` keys on any
  service**, the pinned env file (no secrets — `API_KEYS` provisioning stays
  env-local, documented in the runbook; `.env.example` gains the two `LLM_*`
  names it lacks today, `.env.example:17,45,55` context).
- ⚠️ **The `/whoami` allow row (finding C-1) must appear in the ingress config.**
  AC-6(a)'s set-equality closes on it, but it is called out here because omitting
  it makes the demo **unloginable** while every test that does not model login
  still passes.
Ship AC-4/AC-5/AC-6(a,b) tests in the same PR.

**Step 9: Local compose smoke (dev box — not host-state; BLOCKED-ON-SD-3 —
RELEASED 2026-08-05).** Bring the published project up on the Legion dev box and
execute the AC-6(c) cases against the pass/fail read below, **fixed here before
the run** (AC-6(c) requires it written into the step in advance; it was owed and
unwritten until s207). Record the full transcript in the PR.

> **Pass/fail read for Step 9 — v2, rewritten 2026-08-05 after an adversarial
> review of v1 found it scored 4/5 against a completely dead app.** Judged only
> against these; no post-hoc reinterpretation. Any case not observed is
> **INSUFFICIENT-EVIDENCE, not a pass**. **Statuses below are EXACT** — v1's
> "non-404" bar is what let a `502` from a crashed `app` container read as a pass
> on four cases at once, so no case may be closed on "not 404" again.
>
> **Topology this read assumes.** A locally-managed `cloudflared` fronting the
> published compose project, reachable over the tunnel. If no tunnel can be
> established (the portal repo is out of scope and the domain is unnamed until
> Phase 5), the **sanctioned offline fallback** is `cloudflared tunnel ingress
> validate` + per-route `cloudflared tunnel ingress rule <url>` — account-free and
> deterministic. It closes cases 2 and 7 only; cases 1, 3–6 are then **deferred to
> Step 11 and recorded as not covered**, never silently dropped.
>
> **Case 0 — preflight (gates every other case).** `docker compose ps` shows
> **both** services `running`/`healthy`, and **no `postgres` service at all**.
> If `app` is not up, STOP: every downstream case is void, not passing.
>
> 1. **Allowed routes are served — exact status + a body assertion each.**
>    `GET /health` → **200**, body `{"status":"ok"}` · `GET /meta` → **200** JSON
>    **carrying `ui_profile == "published"`** · `GET /` → **200** `text/html`
>    **whose `<meta name="ui-profile">` tag reads `published`** · a **named**
>    `/assets/*` file (not "one asset" — pin the list, including anything
>    `font-src 'self'` needs) → **200** with the right content-type ·
>    `GET /objects/<a type the deployed vertical actually has>` → **200** with a
>    **non-empty** array (every adapter returns `[]` for an unknown type, so a
>    literal placeholder proves nothing) · `GET /procedures` → **200** non-empty ·
>    `GET /demo/hero/governance` → **200** · **`GET /demo/hero/governance?live=true`
>    → 200** (the published Tab G still renders "▶ Run live" at
>    `view-hero.js:610-614`, which mounts in *manual* mode — only *event* mode is
>    excluded; this param drives a full live procedure run that raises
>    `ProcedureError` at `run.py:387` if the gate does not suspend, and with no
>    global exception handler that is an unhandled 500 in front of the partner) ·
>    `GET /demo/hero/impact` → **200** · `GET /llm/status` → **200**.
>    **Both POST rows, which v1 omitted entirely:**
>    `POST /query` with a real demo-script question → **200**, non-empty `answer`,
>    a `phrased_by` value present (this is the wedge; v1 never drove it) ·
>    `POST /recommendations/<real id>/approve` keyless → **401**, and with the
>    operator key → **200**.
>    `GET /whoami` **keyless → exactly 401.** **200 is a FAIL** — it is the
>    signature of `API_AUTH_ENABLED=false` in the running container, which would
>    leave every keyed row open to anonymous visitors and which AC-4 cannot catch
>    (AC-4 parses the committed compose *file*, not the running container). Record
>    the `auth_enabled` field in the transcript. **404 is also a FAIL** — that is
>    the C-1 defect. **Positive control:** keyed `/whoami` → **200** with non-null
>    `person_id`; this is the only evidence the demo is loginable at all.
> 2. **Excluded routes are denied — exact 404, and proven to be denied at the edge.**
>    `POST /demo/hero/event` · `GET /warm` · `GET /sleep` ·
>    `POST /intake/extract` · `GET /intake/defaults` · `POST /intake/generate` ·
>    `POST /procedures/draft/classify` · `POST /procedures/draft/build` ·
>    **`POST /procedures/draft/instantiate`** (SD-2 ruled exclude-all, and this is
>    the one that was *offered* as an allow — the likeliest to leak) ·
>    `GET /runs` · `POST /runs/{id}/cancel` · `GET /audit/verify` · one `/cases*` ·
>    one `/api/exports/*` · `POST /recommendations/<id>/execute` · `GET /runs/<id>` ·
>    `POST /insights/query` · and **`GET /openapi.json`** — in neither table, and
>    the highest-value leak on the list, since it publishes the complete route map
>    **including every excluded route** to anyone who asks. Also probe one
>    `pm_router` path (`main.py:336`), which neither table names.
>    Each → **exactly 404**. Use **ids that actually exist** for the parameterised
>    probes, so an app-level 404 (`actions.py:194-198`, `runs.py:344-345`) cannot
>    masquerade as an edge denial.
>    **Edge-denial proof + its positive control:** the app logs **no** request for
>    any of them, **and** the same transcript shows an allowed request **present**
>    in `docker compose logs app`. Without that control, "no request logged" is
>    also true when access logging is off, and the clause is unfalsifiable.
> 3. **DB-less posture — positive, not a restatement of case 1.** Assert
>    `postgres` absent from `docker compose ps`, **and** that the fail-soft boot
>    lines (`main.py:284`, `:307`) appear in the app log, **and** that a known
>    DB-backed *excluded* route 404s at the edge rather than 500ing.
>    ⚠️ Do **not** diagnose a 500 as "a DB-backed row survived on the allow table"
>    — the deliberate `RuntimeError` at `main.py:138-142` (published index missing
>    the `ui-profile` anchor) is a likelier cause. Require the traceback in the
>    transcript and diagnose from it.
> 4. **Arm posture — the allow table's third column, unchecked by v1.** Assert
>    from response fields: `/query` carries `phrased_by` / the PLAN-0093
>    disclosure; `/recommendations` carries its disclosure consistent with the
>    corrected **assisted** posture. ⚠️ Blocked on **OI-1** — do not run this case
>    until OI-1 is decided, and record which option was taken.
> 5. **Prompt log on the deployed container.** After case 1's `POST /query`,
>    assert a JSONL line exists under `PROMPT_LOG_DIR` on the named volume with
>    the closed D6 field set. `prompt_log.record` never raises by design
>    (`query.py:55`), so an unmounted or unwritable volume is **silent** — and the
>    RoPA instance, the 90-day retention story and the runbook's purge + DSR
>    commands would all describe a file that does not exist.
> 6. **Rate cap.** Drive `POST /query` from one IP past the pinned threshold;
>    assert rejection **at the edge** (a Cloudflare block response, not a
>    vero-lite body) and recovery after the 10 s mitigation window. ⚠️ If the
>    smoke does not sit behind the Cloudflare edge this case **cannot** run
>    locally — defer to Step 11 and record as **not covered here**.
> 7. **The running tunnel actually loaded the committed config.** Record
>    `cloudflared --version`, the **resolved config path**, `cloudflared tunnel
>    ingress validate`, and per-route `cloudflared tunnel ingress rule <url>` for
>    at least one allowed and one excluded route. Without this, a tunnel started
>    with a different `--config` — or an accidental token-based remotely-managed
>    tunnel, which Step 8 forbids but the smoke cannot otherwise see — produces
>    byte-identical case-2 output.
> 8. **No `ports:` exposure.** `docker compose ps` shows no published host port
>    for any service; the only reachable path is through the connector.
>    (Only meaningful once case 0 has shown the services actually running — a
>    crashed service also shows no ports.)
>
> **Not covered by this read, stated so the closeout cannot imply otherwise:**
> AC-1's excluded-control coherence and AC-9's banner are verified by offline
> source tripwires only — no case here loads the deployed page and asserts the
> excluded controls are absent; `_OCT_CSP` is stamped only on the static mount
> (`main.py:117-122`), so no case checks the header survives the edge on the JSON
> API; and nothing asserts the tunnel fronts only the intended service.

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
- 🔴 **`0035:414-418` + `0035:421-424` + `0035:868-874` — the connector-ownership
  boundary. ADDED s207-R2, and this one BLOCKS Step 8.** D4/L5 assigns the
  `cloudflared` connector config and the ingress map to the **portal repo**, with
  vero-lite contributing *"**only** its image (PLAN-0095) and its own compose
  project"*. SD-3's ruling puts a `cloudflared` service **and** a committed
  `config.yml` **and** tunnel credentials inside vero-lite — which is more than
  "one subdomain + one Access policy + one compose project", the exact condition
  `0035:421-424` names as drift: *"If a future system needs more than that, the
  arrangement has drifted and **this ADR is reopened**."*
  Proposed amendment (two readings, Cray picks): **(a)** vero-lite's `cloudflared`
  **is** this system's connector, declared in vero-lite's own compose project, and
  D4 is amended to say the portal repo owns the *ingress map across systems* while
  each system owns its *own* route allowlist; or **(b)** the ingress allowlist
  moves to the portal repo and vero-lite ships only the allow **table** as the
  contract — which voids AC-6(a)'s offline set-equality and re-opens SD-3.
  ⚠️ Until this is routed and ratified, **Step 8 must not start** — building
  against a boundary the ADR forbids would have to be undone.
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

  **Ruling: (a) DB-less — and strike the four allow-table rows the posture cannot
  serve. — Cray, 2026-08-05.** The ruling was taken against finding **C-3**, which
  was surfaced *before* the sitting precisely because the recommendation and the
  allow table had never been checked against each other. Consequences, recorded so
  the closeout cannot rediscover them: the published demo is **read + approve, not
  execute** — the governed approve→**execute** round trip and the gate-resolve beat
  are the Cray-driven screen-share, which is what SD-1's own recommendation text
  argued for (`:526-528`); Tabs I/J are **not registered** (Step 1's BLOCKED-ON-SD-1
  row finalization is hereby released to that answer); `/insights/query` leaves the
  published surface. ⚠️ **The sentence that stood here — "`/query` is the only
  published LLM route" — was FALSE and is retracted (s207-R2).** `GET /recommendations`
  is LLM-backed (`recommender.py:194-195`), so the published surface still has **two**
  LLM routes; the arm-posture column has been corrected and the consequence is now
  tracked as **OI-1** below. The rest of the consequence stands: the prompt-log writer
  stays wired to `/query` and `/insights/query` in code, so AC-8 is unchanged — it
  tests the writer, not the allowlist. Tab H's disposition is still the Step-1 census's to make on its own
  default-deny basis, but with the runs pair now excluded, **every** Tab H backend
  route is off the allow table, which makes "not registered" the only coherent
  option left for it.
- **SD-2 — `/procedures/draft/*` disposition.** Not named in D5(2); same intake
  family. **Recommendation: exclude all three** — classify/build are
  unauthenticated MS-S1 inference (F3 `0035:185`), instantiate is deterministic
  but is authoring surface, not demo script; the published wedge demo does not
  hand anonymous visitors a procedure-authoring wizard. Alternative: allow
  instantiate only (zero-LLM). Cray's call because it widens D5(2)'s named set.

  **Ruling: exclude all three (the recommended option). — Cray, 2026-08-05.**
  Step 3 therefore hides **all** draft-wizard entries (`intake-procedures.js:158,181,201`);
  `instantiate`'s entry does not survive.
- **SD-3 — Allowlist enforcement point. RESTATED at the sitting (s207) — the
  two-option framing was wrong, and neither drafted option won.** As drafted this
  SD asked: in-compose deny-by-default **nginx** (recommended) vs **vendor WAF**
  path rules. Two facts found at the sitting collapsed that framing:
  1. **ADR-0035 never names nginx** — not once in the file. It says only "a
     default-deny route allowlist **at vero-lite's edge**" (`0035:436`) and
     "rate limiting lives at the edge" (`0035:675`). What the ADR forecloses is
     rate limiting **inside `services/`** (F5 stays true); it does not mandate a
     proxy service. nginx was this PLAN's addition, not the ADR's ruling.
  2. **The two jobs have different best answers.** `cloudflared` — already
     required by D1, so not a new service — supports **locally-managed tunnels
     with an ingress config file**, **path matching**, and a **mandatory
     catch-all** that can return `http_status:404`. That is deny-by-default,
     natively, **as a file in this repo** (so AC-6(a) set-equality and offline
     testing both survive). It cannot rate limit. Cloudflare **can** rate limit,
     but only within the Free plan's grammar.

  **Measured on the zone at the sitting** (`cray-n8n.com`, Free — screenshots read
  by Cray, 2026-08-05): **Rate limiting rules 0/1 used**, **Custom rules 0/5 used**.
  The single free rate-limiting rule is **unclaimed**, so nothing had to be retired
  to free it. Free-plan limits (Cloudflare docs, read the same day): 1 rate-limiting
  rule, IP-only counting, **10 s counting period only**, **10 s mitigation only**,
  expression fields limited (Hostname availability **unconfirmed** — deferred to
  Step 8, with path-only scoping as the working fallback since `/query` does not
  collide with the zone's other app).

  **Ruling: enforce at the `cloudflared` edge — ingress allowlist with a catch-all
  404 (config file committed in this repo) + the zone's Cloudflare rate-limiting
  rule for the per-IP cap. NO nginx service. — Cray, 2026-08-05.**
  **Re-affirmed by Cray on 2026-08-05 as option (ii) — "stay with cloudflared, fix
  the spec"** — after an independent adversarial review returned **six findings
  against this ruling**. The review was run *because* this ruling was authored
  without author≠reviewer separation. The findings are recorded below **classified,
  not summarised away**: three are discharged by the spec fixes in Step 8, and
  **three are accepted consequences or an ADR debt that the spec cannot remove.**
  Anyone reading this later must not mistake "ruled" for "no longer a risk".

  | # | Finding | Status under (ii) |
  |---|---|---|
  | 1 | cloudflared `Path` is an **unanchored regex** (`r.Path.Regexp.MatchString`, verified in cloudflared's `ingress/rule.go`) — a rule `path: /query` also admits the SD-1-excluded `/insights/query` | **FIXED by spec** — Step 8 mandates fully anchored patterns (`^/query$`) and an AC-6(a) assertion that every pattern is anchored at both ends |
  | 2 | ingress has **no HTTP-method matching at all** (the Rule struct has only Hostname, Path, Service, Handlers, Config), so the allow table's **Method column is not edge-enforceable** | **FIXED by spec, with a stated limit** — the allowlist is expressible because path alone separates every allowed route from every excluded one (`^/recommendations$` and `^/recommendations/[^/]+/approve$` do not match `…/execute`). Step 8 states that a path allow implies **all methods** on that path, and AC-6(b) must treat the Method column as documentation, not enforcement |
  | 3 | **Allowlist bypass:** if the portal's connector also joins `vero_oct`, it reaches `app:8000` directly and the ingress allowlist is skipped entirely — AC-6(a) cannot see this | **FIXED by spec** — Step 8 pins the topology: `app` joins **only** an internal network with no connector but vero-lite's own; the ingress config is the sole path to it. AC-6(c) case must prove it |
  | 4 | **D4/L5 boundary:** `0035:414-418` makes the connector config + ingress map the **portal repo's property** — vero-lite "contributes **only** its image and its own compose project". A committed `config.yml` + tunnel credentials in vero-lite crosses that line, and `0035:421-424`'s drift trigger says *"the arrangement has drifted and this ADR is reopened"* | 🔴 **NOT fixable by spec — ADR debt.** Added to §ADR amendment owed and to AC-12. Step 8 must not start until that amendment is routed |
  | 5 | **Vendor-branded 429.** Free cannot customise the block response ("custom response … Pro plans and above"), so a rate-limited partner sees a Cloudflare page — the same harm `0035:472-475` legislated against for vendor 524s: *"never a vendor 524 in front of exactly the audience the wedge exists to impress"* | 🔴 **ACCEPTED CONSEQUENCE.** Not mitigated. Escape hatch if it bites: Pro (~$20/mo) restores a custom response |
  | 6 | **NAT + no burst.** Free counts by IP with no burst allowance, so a partner org behind one egress IP shares the counter — a handful of near-simultaneous questions hard-blocks the room | 🔴 **PARTIALLY MITIGATED by threshold choice, not removed.** See §Pinned values: the threshold is set to tolerate a demo room rather than to minimise sustained rate. A burst allowance does not exist on Free at any threshold |
  | 7 | **One free rule per zone** ⇒ system N+1 gets no cap, against L9's "accept an unnamed third without redesign" (`0035:227-230`) | 🔴 **ACCEPTED CONSEQUENCE**, recorded for the portal repo's own planning. Out of scope here |

  Other consequences of the ruling: AC-6(a)'s set-equality target is the **committed
  cloudflared ingress config**, not an nginx config; Step 8 drops the `nginx:alpine`
  service; Step 9's edge cases run against cloudflared.
  ⚠️ **The rate-limiting rule itself lives in the Cloudflare zone, which is
  portal-side and outside this repo** — so, unlike the ingress file, it **cannot**
  be closed by an offline test. It is closed by AC-6(c)'s smoke plus a screenshot
  of the rule in the closeout, and it is a **standing drift risk** named here so the
  closeout does not record it as covered.
  ⚠️ **Also unverifiable offline:** nothing binds the *running* tunnel to the
  *committed* ingress file. A tunnel started with a different `--config`, or an
  accidental token-based remotely-managed tunnel, produces byte-identical smoke
  output. Step 9 must record `cloudflared --version`, the resolved config path, and
  `cloudflared tunnel ingress validate` + per-route `ingress rule <url>` output.
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

  **Ruling: (a) measure-to-confirm — run AC-3 against the `54dfc7d` ladder
  unchanged; do not re-tune first. — Cray, 2026-08-05.** Step 4 is therefore a
  single measurement run against the pass/fail read already fixed at `:199-201`,
  with the dev table already recorded. A red measurement re-opens fix depth as a
  bounded follow-up rather than silently — that escape hatch is what makes (a) safe
  to take before the evidence exists.

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

  **Ruling: keep both. — Cray, 2026-08-05.** Schedules no work: the dev half is
  already measured green and the two tripwires are already committed. It sets the
  standing bar — a future dev-profile regression blocks link-sharing until
  re-measured. Relaxing to published-only later touches nothing else.

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
