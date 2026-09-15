# PLAN-0126: The fleet story-mode explainer in the published console — `/story/`, the drift guard, and the deploy

**Status:** Draft — **all seven SDs RULED (Cray, typed 2026-09-15: "SD-1 ถึง SD-7: เอาตามที่แนะนำทั้งหมด"): SD-1 = (a) · SD-2 = (a) · SD-3 = (b) · SD-4 = (b) · SD-5 = (d), interpreted — Cray to confirm at PR review (§7) · SD-6 = (a) · SD-7 = (a)** — each recorded inside its own SD in §7 with the options and recommendation kept as drafted. Every Step is unblocked. Ruling the SDs does **not** ratify the PLAN, which stays `Draft` until Cray's separate act (the PLAN-0123 / PLAN-0125 precedent).
_[Status as drafted, kept for lineage: Draft — awaiting Cray's typed rulings on SD-1 … SD-7 (§7); Steps 0–2 unblocked by every SD except SD-1 and SD-4; Step 3 waited on SD-1, Step 4 on SD-3, Step 6 on SD-2, Step 9 on SD-5, Step 10 on SD-6, Step 13 on SD-7.]_
**Owner:** Claude Code (executes; all commits Code-exclusive per ADR-009 D2 / ADR-013 D2). Cray rules the SDs, gives each download and each host-state go **per occasion**, and reads AC-10 at PR merge.
**Created:** 2026-09-15 (session: unnumbered — the story-visualizer Code session. ✎ `was an error`: the draft inferred a session number from a branch name on `main` that belongs to the *concurrent* PLAN-0125 session; corrected at the revision round)
**Related ADRs:** ADR-0032 D6 (the `monitor→decide→approve→act` framing every caption uses), ADR-0035 D3 (Access is one policy per subdomain, so `/story/` inherits the OTP gate with no new policy — `docs/adr/0035-hosting-and-exposure-model.md:496-498`), ADR-0036 D2 (no shadow ingress map — this PLAN names **one** published system and no other), ADR-009 D1/D2 + ADR-013 D1 (drafting and commit authority), ADR-012 D4.3 (disclosure below).
**Related PLANs:** PLAN-0100 (the index rewrite and its fail-loud anchor — `services/api/main.py:124-137`, `:176-206` — which Step 3 narrows), PLAN-0103 (the fleet profile's ingress allowlist and its `_EXPECTED_ALLOW` row), PLAN-0107 (the asset-manifest bijection AC-6 extends to `story/`), PLAN-0080 (the strict-JSON block read by both the browser and a Python tripwire — the precedent AC-4 reuses), PLAN-0115 (`tools/probe_battery/`), PLAN-0033 (the console's existing "Story mode" overlay — the naming collision SD-2 resolves), PLAN-0095 (a local boot of the built image — the cheapest live-ish read before any host-state go).
**Related Lessons:** #0007 (command output is evidence), #0026 (pass/fail read fixed before the run), #0030 (verify inherited claims, especially negative ones — §2 does), #0056 (suspect the instrument first — §2 G6 records a dispatch claim the instrument refuted).
**Batteries:** planned as `tests/batteries/plan-0126-*.json` — ⚠️ this header is deliberately **inert** (no backticked glob straight after the field) until the first battery file exists, because `tools/check_ac_consistency.py` Check 3 errors on a `**Batteries:**` glob that matches no file (`tools/check_ac_consistency.py:317-331`). Code makes it live in the **same commit** as the first battery file (the PLAN-0125 Step 0 precedent), and no AC box is ticked before its probe.
**Number taken:** **0126**, per the dispatch (the caller enumerated `main`, the shared checkout and the concurrent PLAN-0125 worktree). Drafter re-check: a Glob over `docs/plans/` lists `0122`, `0124`, `0125` active and nothing at `0126`; the highest archived is `done/0123`. ✔
**Branch:** this draft rides `docs/plan0126-story-explainer-draft` (a `docs/*` PR, auto-merge allowed, CLAUDE.md §7); implementation on `feat/plan0126-story-explainer` — a `feat/*` branch **waits for Cray** and never carries `--auto`.
**Routing provenance:** CLAUDE.md §6 routes a new PLAN to a Cowork dispatch by default. **Cray typed on 2026-09-15: draft stage 2 with `plan-drafter`, no Cowork.** The in-harness drafter is exempt from the G2 classifier by design (PLAN-0034 prong 2) and bounded by its own `docs/{adr,plans}` write-allowlist; recorded here so the routing choice survives the session.

> **Author≠reviewer disclosure (ADR-012 D4.3).** Drafted by the in-harness `plan-drafter` subagent under ADR-013 D1 phased authority from a Code-authored dispatch (session scratchpad, gitignored; everything this PLAN needs from it is reproduced in §1–§2). The drafter had Read/Grep/Glob only — no shell — and **re-read every code, test, YAML, config and rulings line it cites** (✔ in §2); dispatch rows it could not re-derive are marked ⚠️ with the dispatch as their provenance. One dispatch claim was refuted by re-reading (G6) and is recorded, not laundered. Outline originator: **Code** (carrying Cray's typed rulings of 2026-09-15). Independent reviewer: **Cray** at PR merge and for every SD; Code re-verifies §2 before the first implementation commit. Separation: **INTACT** — originator (Code), drafter (plan-drafter), ratifier (Cray) are three actors.

> **Revision disclosure (2026-09-15, revision round).** Revised in place by the same in-harness `plan-drafter` from a coordinator message carrying Cray's typed SD rulings and four Code review corrections. The reviser re-read `verticals/fleet_maintenance/case_projection.py:88-139` and `data_adapter/synthetic.py:175-195` for correction 2 (G31, `confirmed`); the Artifact host's constraints under SD-5 (d) are the review's statements and are marked ⚠️ (G32). The drafter's own session-number inference was an error and is corrected in the `Created` line with its lineage. Separation unchanged: **INTACT**.

> **One-line frame.** Stage 1 built a single-file Three.js explainer of the real fleet flow whose Act-4 outcomes are *computed* from rules hand-mirrored out of the repo, and Cray passed its look and pacing. Nothing yet makes that page run under the console's `script-src 'self'` CSP, survive the static mount's index rewrite, pass the edge's anchored allowlist, or stop its mirrored graph and rules from drifting silently when the YAML or `sourcing.py` moves. This PLAN ports the page to `/story/`, replaces the JS *logic* mirror with one strict-JSON block that Python pins against the **real** ontology loader, the **real** procedure loader, the **real** `compute_three_quote` and the **real** seed, guards the new files with the same bijection discipline the console's assets already have, and deploys once — every download and every host-state command behind an explicit, per-occasion Cray go.

---

## Goal

Ship the stage-1 explainer as a standalone page at `/story/` in the published fleet console — opened in a **new tab** from the console, never a tab in the strip (L1) — that loads only same-origin files under the existing CSP, tells only the real fleet flow (L3), and carries a drift guard whose oracle is the repository's own loaders and rules, so that a change to the ontology, the procedure, the sourcing constants or the seed cases turns a Python test RED rather than letting the page quietly narrate a system that no longer exists. Then deploy it once, under the host-state gate, and keep the Claude-Artifact channel publishable as a **multi-file Artifact from the very same files** (L1, SD-5 (d)).

---

## 1. Cray's typed rulings (LOCKED — cited, never reopened)

Numbered L1–L6 here so they are not confused with the intro-video rulings file's R1–R8.

| # | Ruling (typed 2026-09-15) | Where it binds below |
|---|---|---|
| **L1** | **Channel:** a standalone page at `/story/`, opened in a **new browser tab** from the published fleet console. **Not** a Tab K. The second channel is a Claude Artifact built from the **same files** | §3.1, §3.5, §3.7, AC-7, AC-11, Out of Scope |
| **L2** | **The explainer is also part of the intro video.** The total video may grow longer; that is handled later and is **out of scope here**. Every caption therefore obeys the intro-video rulings: R1 (no numbers on the determinism point), R3 (barely say AI), R7 (no URL on screen), never read the ฿30,001 numeral, "tamper-evident" never "immutable", never "the model decides nothing", no benchmark numbers (`docs/strategy/public/intro-video-production-rulings.md` §2–§3) | §3.6, AC-5, Step 2, Step 10 |
| **L3** | **Honest story only.** The page must not depict an automated FK-graph → ontology lift (no such code exists), an LLM proposing spec changes (no such loop exists), or MCP tool-calling at runtime (`services/engine/nl_query.py:31-32` names it the deferred option B). Grounding is shown as the Ask three-stage path | §3.6, Step 2, §8 checklist |
| **L4** | **Two stages.** Stage 1 (the Artifact prototype, no repo writes) is done and passed. This PLAN is stage 2: the in-app page, the drift guard, the deploy | scope of this whole PLAN |
| **L5** | **Act-4 cases, in order:** (1) truck-01 ฿48,000 with 1 vendor — illustrative, bounces at `quote_gate` with `quotes_required`; (2) truck-01 ฿48,000 with 3 vendors — waits at `approve` for เจ้าของกิจการ; (3) **truck-03 ฿15,000 with 1 vendor** (`under_threshold` → ผจก.เดินรถ) — added by Cray; it restores the ladder contrast that R8 dropped from the Tab H shot. **R8 is not reversed for that shot.** The rulings file must record the addition beside R8 | §3.2, AC-4, AC-9, Step 10, SD-6 |
| **L6** | **Never delete or prune worktrees** under `.claude/worktrees/` without Cray's command. No Step here does so | Out of Scope, every Step |

---

## 2. Grounding — what this PLAN rests on, and how each row was verified

Legend: **✔** re-read by the drafter at the cited line · **✎** re-read, drift or nuance noted · **⚠️ asserted-not-verified** — the drafter could not run the measurement or did not open the file; provenance is the dispatch. **[V]** / **[A]** are the dispatch's own tags (re-read by the caller / reported by a research subagent).

| # | Claim | Source | Mark |
|---|---|---|---|
| G1 | The console CSP on every static-mount response: `script-src 'self'`, `style-src 'self' 'unsafe-inline'`, `img-src 'self' data:`, `font-src 'self'`, `connect-src 'self'`, `object-src 'none'`, `base-uri 'self'`, `frame-ancestors 'none'`. Consequence: no CDN script, no inline script, no import map, no Google Fonts, no cross-origin fetch. An inline `<style>` and CSSOM writes are allowed | `services/api/main.py:109-121` | ✔ |
| G2 | **Trap 1.** `_StaticFilesWithCSP.get_response` sends **any** `FileResponse` whose path ends in `index.html` to `_profiled_index`; on a non-`dev` profile that reads the file and **raises `RuntimeError`** when it lacks `<meta name="ui-profile" content="dev" />` — deliberately fail-loud. The rewritten index is served `Cache-Control: no-store` | `main.py:169-174` (dispatch), `:183-194` (raise), `:195-206` (no-store) | ✔ — a `static/story/index.html` on the published profile would raise, exactly as the dispatch says |
| G3 | The UI mount is `app.mount("/", _StaticFilesWithCSP(directory=_STATIC_DIR, html=True), name="ui")`. With `html=True`, a request for `/story/` resolves to `story/index.html` (and `/story` without the slash is a redirect the edge would 404 unless admitted) | `main.py:649` | ✔ |
| G4 | **Trap 2.** The fleet profile's edge allowlist is a set of **anchored** `path:` regexes ending in a catch-all `http_status:404`; `tests/deploy/test_published_profiles.py` asserts set-equality against `_EXPECTED_ALLOW["oct-fleet-maintenance"]`, anchoring of every pattern, and the catch-all last. A new path needs a row in **both** the config and the table | `deploy/published/oct-fleet-maintenance/cloudflared/config.yml:48-53`, `:252-258`; `tests/deploy/test_published_profiles.py:75`, `:114-115`, `:617-645` | ✔ |
| G5 | The **shadow-ingress guard**: any committed `.md/.yml/.yaml/.py/.env/.js` outside a profile that names **two or more** published system labels fails (`test_ac5_no_file_outside_a_profile_lists_two_system_labels`). This PLAN names only the fleet label, so it is safe whether or not `docs/plans/` is tier-exempt | `test_published_profiles.py:756-781` | ✔ (the exemption tiers `_AC5_EXEMPT_TIERS` were not read — the PLAN does not depend on them) |
| G6 | **Trap 3, corrected.** `test_asset_manifest.py` enumerates disk with a **non-recursive** `_ASSETS.glob("*.js")` / `("*.css")`, and parses references only from the root `index.html`. Consequence: files under `static/story/` **and** files under any `static/assets/<subdir>/` are guarded by nothing; only a **top-level** `assets/*.js|css` orphan reddens the reverse direction | `tests/api/test_asset_manifest.py:45-60`, `:98-114` | ✎ **dispatch claim refuted** — the dispatch [V] row said `static/assets/story/` "would redden the manifest unless referenced or exempted"; `Path.glob("*.js")` does not descend, so it would not. `confirmed — prior intact` on the half that matters (story files are unguarded either way), which is why AC-6 ships its own bijection |
| G7 | The tab census is pinned as set-equality over `app.js`'s `ALL_VIEWS` keys = `ABCDEFGHIJ`, and the inactive-label collapse must fire at ≥ 2253px. An entry **link** is not a view key and touches neither | `tests/api/test_static_ui.py:87`, `:110-123`, `:147` | ✔ |
| G8 | `docs/conventions/ui.md` binds everything under `services/api/static/`: §1 tokens; §3 `html:` is the only innerHTML sink and is for static SVG strings only; §4 the strict-JSON block between `TRACE_KINDS_JSON_BEGIN/END` read by both the browser and a Python tripwire; §5 no build step, `?v=` cache-bust on every asset edit, any UI tripwire is a Python test | `docs/conventions/ui.md:7-9`, `:23-39`, `:59-67`, `:69-97`, `:99-110` | ✔ |
| G9 | `assets/fonts/` holds IBM Plex Sans (Regular/Medium/SemiBold/Bold) and IBM Plex Mono (Regular/Medium/SemiBold) `.woff2` plus `LICENSE.txt` — **no Thai face** | Glob of `services/api/static/assets/fonts/` (8 files) | ✔ |
| G10 | The console's own font stack is `--sans: 'IBM Plex Sans', system-ui, sans-serif` and `--mono: 'IBM Plex Mono', ui-monospace, monospace` — Thai text in the product (persona names, Tab I free text) already renders through the **system** fallback | `services/api/static/assets/theme.css:82-83` | ✔ — load-bearing for SD-4 |
| G11 | The deployed image (`python:3.12-slim`) has no OS mime files; `_STATIC_MIME_TYPES` registers `.woff2`, `.woff`, `.md`, and a guard walks the real static tree and reddens on any extension the built-in table cannot type. `.js`, `.css`, `.html`, `.txt` are built-in | `main.py:50-75`; `tests/api/test_static_ui.py:155-164` (docstring) | ✔ — so the vendored module is named `three.module.js`, never `.mjs`, and the licence ships as `THREE_LICENSE.txt` |
| G12 | The console header's `.right` cluster already hosts launchers before the Refresh button; the MS-S1 control is skipped on the published profile; **PLAN-0033's "Story mode" overlay launcher is mounted there unconditionally** and has its own published-profile branches. The word "story" is therefore already taken in the header | `services/api/static/assets/app.js:202-231`; `view-story.js:2`, `:821`, `:902`, `:1791` | ✔ — SD-2 |
| G13 | `THREE_QUOTE_THRESHOLD_THB = Decimal("30000")`, `MIN_DISTINCT_VENDORS = 3`, `compute_three_quote(*, amount_thb, distinct_vendor_count, has_sole_source_justification) -> (bool, basis)` with branch order under_threshold → three_quotes → sole_source_justified → quotes_required; `PASSING_BASES` declared as data | `verticals/fleet_maintenance/sourcing.py:51`, `:54`, `:66-68`, `:71-94` | ✔ |
| G14 | `governed_repair_approval` (`:131`): `trigger: event`, `event_kind: repair_quote_accepted` (`:158-159`); steps start `:180`; `quote_gate` is `kind: evaluate` with `governance_content.kind: rule_gate`, criterion `three_quote` (`:283-322`); `approve` is `kind: action`, `autonomy: gated`, `governance_content.kind: doa_tier`, tiers `0 / 5001 / 30001` → `ช่างใหญ่ / ผจก.เดินรถ / เจ้าของกิจการ` (`:323-349`); `terminal: fulfill` (`:409`); SoD `distinct_steps: [intake, approve]` with roles requester/approver (`:416-420`) | `verticals/fleet_maintenance/procedures.yaml` | ✔ (✎ the dispatch's `:343-349` is the `governance_content` block; the tier rows themselves are `:347-349`) |
| G15 | The seed: all three trucks carry `minor_repair_ceiling_thb: 5001.0` (`:134`, `:147`, `:165`); the ฿15,000 truck-03 gearbox event carries `_sourcing_signal(15_000, distinct_vendors=1, sole_source=False)` (`:254-281`); the ฿48,000 truck-01 axle event carries `_sourcing_signal(48_000, distinct_vendors=3, sole_source=False)` (`:282-304`). `_sourcing_signal` **runs the real `compute_three_quote`** and stamps `compliance` + `three_quote_basis` on the row (`:75-93`); the event list is `_fixture_events()` (`:198`) behind `operational_events()` (`:175`) | `verticals/fleet_maintenance/data_adapter/synthetic.py` | ✔ — so a seed row is itself evidence of the real rule's verdict, which AC-4(i) uses |
| G16 | `load_procedures(vertical)` → `load_procedures_file(path, *, vertical)` → `parse_procedures` → `VerticalProcedures` | `services/engine/procedures/spec.py:2027-2037` | ✔ (the attribute names on the returned object — steps, governance content, SoD — were **not** read; Step 4 reads them before writing the assertions) |
| G17 | `generate_all(yaml_path, output_dir)` runs exactly seven emitters keyed `pydantic, sql, jsonschema, mcp, typescript, orm, context_pack`; only `energy`/`core` have committed ORM/Pydantic destinations, so fleet's seven all land in `output_dir` — safe to run into `tmp_path` | `services/engine/code_generator.py:900-903`, `:912-914`, `:917-940` | ✔ (dispatch [A], now drafter-verified) |
| G18 | The ontology declares 10 object types and 7 link types `(from, to)`; a `type: ref` property carries `target: <Type>` (e.g. `RepairCase.truck_id → Truck`) and the four such refs the prototype draws dashed have **no** `link_types` entry | `verticals/fleet_maintenance/ontology/fleet_maintenance_v0.yaml:402-418`, `:533-575` | ✔ (the other three undeclared refs — `RepairCaseQuote → RepairCase`, `RepairCaseAcceptedQuote → RepairCase`, `→ RepairCaseQuote` — were **not** individually re-read; AC-4(c) computes the set from the file rather than trusting the prototype's list) |
| G19 | `nl_query.py`: translate (LLM, enum-constrained object type) → execute (deterministic, no LLM; empty result short-circuits to a fixed answer) → phrase (LLM over retrieved records only); agentic tool-calling over `mcp_tools.json` is **the deferred option B** | `services/engine/nl_query.py:8-35` | ✔ — the L3 boundary |
| G20 | The published fleet tab set is `A,C,F,H,I,J`, default A; `OCT_DEMO_SEED_OPERATE=true` seeds the `waiting_human` run at boot | `deploy/published/oct-fleet-maintenance/published.env:37`, `:164` | ✔ (dispatch [A], now drafter-verified) |
| G21 | Deploy = `docker compose … build app` on the dev box (§2a, with in-image `sha256sum` of every changed file), `docker save \| ssh … docker load`, `image inspect` id equality, `config --quiet`, `up -d`; **every host-reaching command needs Cray's explicit go, per phase, per occasion**; the host reads `docker-compose.yml` and `cloudflared/config.yml` **from its own checkout**, so an ingress change needs a host `git pull` and `--force-recreate cloudflared`; the demo-state read (`DEMO-STATE: PRISTINE`/`CONSUMED`, no token = FAILED) decides the shape of the deploy | `deploy/published/oct-fleet-maintenance/DEPLOY.md:20-27`, `:51-96`, `:100-149`, `:153-184` | ✔ (dispatch [A], now drafter-verified) |
| G22 | Cloudflare Access with an OTP email allowlist gates the subdomain at the vendor edge; one policy pattern per subdomain, so a new path under the same subdomain inherits the gate | `docs/adr/0035-hosting-and-exposure-model.md:461-498` | ✔ (dispatch [A], now drafter-verified) |
| G23 | The rulings file is *a record, not a rule*; superseding a ruling needs Cray; R1–R8 with their dates; the four §3 filming constraints in plain text so `git grep` finds them; §4.1 records R8 (drop the ฿15,000 contrast) with *"Do not reopen this as 'the beat feels thin'"* and names option (c) "a build, not a retake"; §6 is the pre-shoot demo-state check; §7 is the provenance table | `docs/strategy/public/intro-video-production-rulings.md:3-11`, `:56-73`, `:76-91`, `:136-159`, `:190-205`, `:209-225` | ✔ |
| G24 | `test_ui_profile.py` simulates the published profile with `monkeypatch.setattr(settings, "ui_profile", "published")` and asserts the rewritten root index carries `content="published"`, not the dev tag, and `cache-control: no-store`; it also pins `_UI_PROFILE_META_DEV` to occur **exactly once** in the on-disk root `index.html` | `tests/api/test_ui_profile.py:117-131`, `:196-197` | ✔ — the pattern AC-2 reuses; the count pin is on the **root** index only, so a story page carrying (or not carrying) the tag does not touch it |
| G25 | Probe-battery mechanics: `python -m tools.probe_battery keys <test>` → battery JSON (`claim_sources`, `probes[].{subject,old,new,node_id,expect_claim,note}`, `exemptions`) → `run --battery`; only `WITNESSED` credits, exactly one claim per probe; committed batteries live under `tests/batteries/plan-NNNN-*.json` | `tools/probe_battery/README.md:43-107`; `tests/batteries/plan-0120-ac9-battery-child.json` | ✔ |
| G26 | The stage-1 prototype: one HTML file, `<script type="module">` **inline**, `import … from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js'`, a Google Fonts `<link>` for IBM Plex Sans / Sans Thai / Mono, tokens copied from `theme.css`, no `fetch`, `innerHTML` used **only** for two static SVG path literals (`.fill` span, play/pause icon), `prefers-reduced-motion` honoured, the frame a pure function of the story clock, Act 4 sized from `ACT4_CASES`, a `ถ่ายทำ` mode that hides all chrome, and a Sources drawer that shows repo `file:line` strings — never URLs | prototype §0–§9 (read in full by the drafter) | ✔ |
| G27 | Node is **not installed** in the WSL dev shell; no JS test runner exists | dispatch, measured 2026-09-15 | ⚠️ asserted-not-verified (an execution fact the drafter cannot re-run; consistent with ui.md §5's "no frontend test runner") |
| G28 | The prototype's on-screen source citations `db_objects.py:1-22`, `pm_import.py:11-21`, `fleet_maintenance_v0.yaml:76-95`, `docs/plans/done/0109-…:58-68` | dispatch [V] / prototype §4 | ⚠️ not re-read by the drafter — they are **on-screen** citations, so Step 2 re-reads each before the port ships (a wrong `file:line` on camera is a false citation) |
| G29 | The prototype's running length is ≈ 1:56 | dispatch | ⚠️ — computed by the page from its cases (`TOTAL` is recomputed after Act 4 is sized), not authored; the drafter cannot run it |
| G30 | No ADR numbered ≥ 0039 exists, so nothing above is overtaken by a later ADR (Lesson #0030 precedence check) | Grep `^# ADR-00(39\|4[0-9])` over `docs/adr/` → no match | ✔ |
| G31 | *(revision)* `operational_events()` returns `case_projection.apply(_fixture_events(), truck_records())`; `apply` overlays a **module-level cached** live-case view (`_facts`) that `refresh(session)` fills and that persists across tests in one process; `_fixture_events()` is the seed alone | `verticals/fleet_maintenance/data_adapter/synthetic.py:175-195`; `verticals/fleet_maintenance/case_projection.py:88-108`, `:122-139` | ✔ reviser re-read — Code's review correction 2 `confirmed`; AC-4(i) therefore reads `_fixture_events()` |
| G32 | *(revision)* The Artifact host accepts a files map keyed by published path; binary ≤ 15 MB and text ≤ 16 MB per file; root-relative paths are **not** served; sources are read only under the session's working directory or its scratchpad; the host wraps a page in its own document skeleton | Code's review, carried in the SD-5 (d) ruling | ⚠️ asserted-not-verified — the drafter cannot exercise the host; Step 9.3 measures the three properties that matter before the first publish |

---

## 3. Design

### 3.1 Files and serving — closing Trap 1 (SD-1)

The page lives at `services/api/static/story/` as five files plus a licence — **SD-1 ruled (a)**:

| File | Role | Served at |
|---|---|---|
| `index.html` | markup + the chrome; `<html lang="th">`; `<link href="story.css?v=…">`; `<script src="story-data.js?v=…">` (classic) then `<script type="module" src="story.js?v=…">` | `/story/` (via `html=True`, G3) |
| `story.css` | the stage-1 `<style>` block, moved out so AC-6 can see it; tokens copied from `theme.css` as stage 1 did; `@font-face` rules pointing **relatively** at the already shipped Plex files — `url('../assets/fonts/IBMPlexSans-Regular.woff2')` and siblings (G9) — so Plex loads with no download in the app (`/story/story.css` + `../assets/fonts/` resolves to `/assets/fonts/`, admitted by `^/assets/.+$`) **and** the same unedited file resolves in the multi-file Artifact, where `../` clamps to the root and the fonts are published under the key `assets/fonts/…` (SD-5 (d)) | `/story/story.css` |
| `story-data.js` | `window.STORY_DATA = /* STORY_DATA_JSON_BEGIN */ { … } /* STORY_DATA_JSON_END */;` — the one data block (§3.2), mirroring `trace-kinds.js` | `/story/story-data.js` |
| `story.js` | the scene, story track, schedule, `evaluate(t)`, controls — an ES module; `import * as THREE from './three.module.js?v=160'` (same-origin, so `script-src 'self'` admits it; no import map) | `/story/story.js` |
| `three.module.js` | Three.js `0.160.0`, vendored (MIT) — Step 1, Cray-permitted download | `/story/three.module.js` |
| `THREE_LICENSE.txt` | the MIT text, beside the file it licenses | `/story/THREE_LICENSE.txt` |

**Trap 1.** `_profiled_index` must not touch this page. The recommended fix narrows `get_response`'s trigger from *"any served path ending in `index.html`"* to *"the mount's root `index.html`"* (`Path(response.path) == Path(self.directory) / "index.html"`). PLAN-0100's guarantee — the **console's** index must carry the anchor or the process fails loud — is unchanged for the file it was written about; the story page is served by the plain `FileResponse` path with ETag/Last-Modified intact and gets the CSP header like every other file. AC-2 pins both halves: the story is served unprofiled on the published profile, **and** the root index is still rewritten and still raises without its anchor. SD-1 ruled (a); the alternatives are kept in §7 for lineage.

Everything under `services/api/static/` obeys `ui.md` (G8): tokens not hexes, `html:`/innerHTML only for static SVG literals, `?v=` bumped on every edit, tripwires in Python.

### 3.2 One data block, pinned by the real loaders — the drift guard (SD-3 ruled (b))

Stage 1 mirrored the graph, the rules and the constants into JS and computed each Act-4 outcome from the mirror. Stage 2 keeps *"derived, never authored"* and moves the derivation to where an oracle exists. The block (recommended shape; keys are `generate_all`'s own for the emitters):

```json
{
  "ontology": {
    "object_types": ["Truck", "Vendor", "Depot", "OperationalEvent", "Alert", "RecommendedAction",
                     "AlertEventLink", "RepairCase", "RepairCaseQuote", "RepairCaseAcceptedQuote"],
    "link_types": [["truck_at_depot", "Truck", "Depot"], ["event_for_truck", "OperationalEvent", "Truck"], "…"],
    "undeclared_refs": [["RepairCase", "Truck"], ["RepairCaseQuote", "RepairCase"], "…"]
  },
  "emitters": {"pydantic": "Pydantic", "orm": "ORM", "sql": "SQL DDL", "jsonschema": "JSON Schema",
               "mcp": "MCP tools", "typescript": "TypeScript", "context_pack": "context pack"},
  "procedure": {
    "id": "governed_repair_approval", "event_kind": "repair_quote_accepted",
    "steps": [{"id": "intake", "th": "อ่านใบเสนอราคาล่าสุด"}, {"id": "judge", "th": "…"}, "…"],
    "gates": {"quote_gate": {"kind": "rule_gate", "criterion": "three_quote"},
              "approve":    {"kind": "doa_tier",  "autonomy": "gated"}},
    "sod": {"distinct_steps": ["intake", "approve"]}
  },
  "rules": {"three_quote_threshold_thb": 30000, "min_distinct_vendors": 3, "minor_repair_ceiling_thb": 5001,
            "tiers": [{"min_amount": 0, "role": "ช่างใหญ่"}, {"min_amount": 5001, "role": "ผจก.เดินรถ"},
                      {"min_amount": 30001, "role": "เจ้าของกิจการ"}]},
  "cases": [
    {"truck": "truck-01", "what": "เพลาขาด", "amount_thb": 48000, "distinct_vendors": 1, "sole_source": false,
     "illustrative": true,
     "expected": {"breach": true, "sourcing_pass": false, "basis": "quotes_required", "tier_role": "เจ้าของกิจการ", "outcome": "fail"}},
    {"truck": "truck-01", "what": "เพลาขาด", "amount_thb": 48000, "distinct_vendors": 3, "sole_source": false,
     "illustrative": false,
     "expected": {"breach": true, "sourcing_pass": true, "basis": "three_quotes", "tier_role": "เจ้าของกิจการ", "outcome": "approved"}},
    {"truck": "truck-03", "what": "เกียร์เสียงดัง", "amount_thb": 15000, "distinct_vendors": 1, "sole_source": false,
     "illustrative": false,
     "expected": {"breach": true, "sourcing_pass": true, "basis": "under_threshold", "tier_role": "ผจก.เดินรถ", "outcome": "approved"}}
  ]
}
```

**The oracle is the repo, not the block.** `tests/api/test_story_drift.py` extracts the block between the delimiters, `json.loads` it, and asserts it against the **real** producers — `code_generator.load_doc` on the fleet YAML, `load_procedures("fleet_maintenance")`, `sourcing.compute_three_quote` + its two constants, `synthetic.truck_records()` / `operational_events()`, and `generate_all` run into `tmp_path` — one test function per assertion (AC-4 lists them). `expected.*` is therefore **pinned**, not authored: change a case and the test names the value the real rule produces. The block's header comment says so.

**What the page does with it (the eliminated mirror — SD-3 ruled (b)).** `story.js` reads `window.STORY_DATA` and **renders**: layout by ref depth (presentation logic, stays in JS), the rail, the ladder personas from `rules.tiers[].role`, Act-4 travel, captions chosen by `expected.outcome` / `expected.basis` / `expected.tier_role`. It evaluates **no** business rule. The stage-1 `computeThreeQuote` / `doaTier` functions are deleted, not ported: a JS copy of the rule would be the one piece of logic nothing in CI can see (G27), and its only oracle would be a runtime banner. One self-check stays in JS and is cheap: every case's `expected.outcome` must be in the closed set `{ok, fail, approved}` and `expected.basis` in `sourcing.py`'s four bases, else the page renders a visible failure line instead of a story — a schema check, not a rule. No runtime recomputation is built (SD-3 option (a) was not taken), and the Sources drawer says *"pinned against the real rule by CI"* where stage 1 said *"computed here"* — the property is kept, its home moved.

**Why the seed row is part of the oracle.** `_sourcing_signal` stamps the real rule's verdict onto each seeded event (G15). AC-4(i) therefore matches every `illustrative: false` case to a seed row by truck, amount and the stamped basis — and asserts the `illustrative: true` case matches **none**, with the two real matches printed as the positive control that the matcher finds known rows. The seed is read as `synthetic._fixture_events()` — the fixture alone — **never** `operational_events()`, which is `case_projection.apply(_fixture_events(), truck_records())` (`synthetic.py:195`) and overlays a module-level cached live-case view that any earlier test calling `case_projection.refresh(session)` can fill (G31); reading the overlay would make (i) depend on test order. The Sources drawer keeps stage 1's disclosure that case 1 is an illustration of the rule, not a seeded run.

### 3.3 The edge — closing Trap 2

Two rows, both anchored, added to `cloudflared/config.yml` under a *"— the explainer (PLAN-0126)"* comment carrying their own basis, and the identical two strings added to `_EXPECTED_ALLOW["oct-fleet-maintenance"]`:

```yaml
  - path: ^/story/$
    service: http://app:8000
  - path: ^/story/[^/]+$
    service: http://app:8000
```

`[^/]+` admits the five sibling files and nothing deeper — AC-3 asserts `story/` has no subdirectory and that every file in it fullmatches a row. The entry link is written `/story/` with the slash so no redirect is needed and `^/story$` is **not** admitted. The rows admit only what the UI drives (the profile's own standard, `config.yml:191-193`). `/assets/fonts/*` is already admitted by `^/assets/.+$`.

### 3.4 Guarding the story files — closing Trap 3 (G6)

`tests/api/test_story_page.py` carries a bijection scoped to `story/`, the PLAN-0107 shape: forward (every `src`/`href`/`import … from './…'`/`url(` reference resolves to a file in `story/` or `assets/`), reverse (every `.js`/`.css` in `story/` is referenced, or sits in a written `_UNREFERENCED_STORY_FILES` dict — empty), stale-exemption, and the two anti-vacuity controls (the parse found ≥ 1 reference of each kind; the directory is non-empty). It does not touch `test_asset_manifest.py`.

### 3.5 The entry link (SD-2 ruled (a))

An anchor, not a view: `href="/story/"`, `target="_blank"`, `rel="noopener"`, rendered through `h()` in the header's `.right` cluster before Refresh. `ALL_VIEWS` is untouched, so G7's census test is the positive control that no tab was added. The label is **"ทำไม"** (SD-2 ruled (a) — the drafter's suggested word, taken as ruled under *"ตามที่แนะนำ"*); it does not read "Story mode" — the header already has one (G12) — and is not a URL (R7). AC-7 pins the three attributes; the header width at 1280 / 1440 / 1920 on both profiles is a printed measurement in §8, because G7's test pins a breakpoint, not the live width.

### 3.6 Captions and rulings — a lexical tripwire plus a semantic checklist

There is no oracle for meaning, so the PLAN is conservative here (the dispatch's accelerator clause does not cover captions). Two layers:

- **Lexical (AC-5, a Python test).** Over the authored story files with JS comments stripped (`tests/api/js_source.strip_js_comments`), the vendored module excluded: no `http://`, `https://`, `www.` (R7); no `30,001`, `฿30,001` or `สามหมื่นเอ็ด` anywhere, and the bare `30001` appears **exactly as many times** as there are tiers with that minimum in the block (once — printed); no `immutable` and `tamper-evident` present (the second is the control that the scan reads the file); no `ไม่ให้โมเดลตัดสินอะไรเลย`; no `12/12`; the token `AI` (word-bounded, case-sensitive) at most once (R3). A fixture string carrying `฿30,001` is shown to be flagged.
- **Semantic (§8 checklist, Cray at PR).** L3's three excluded depictions; stage 1's two `notClaimed` disclosures survive the port verbatim; the Act-3 captions describe translate → execute → phrase with the empty-result fixed answer (G19) and nothing agentic; Act 2 shows fleet's emitter outputs as reference artifacts, not as runtime feed (G17); Act 5 says *who holds the authority*, never that the model does nothing.

### 3.7 The Artifact channel — the same files, published multi-file (SD-5 ruled (d), interpreted — Cray confirms at PR review)

L1 says the Artifact is built from the same files. The served page cannot be one file (inline module scripts are CSP-blocked, G1), and the ruling takes *"same files"* literally rather than bundling around it: the Artifact is published as a **multi-file** Artifact whose files map is `story/`'s own files at their `story/`-relative keys plus the shipped `assets/fonts/*.woff2` that `story.css` references, under the key `assets/fonts/…`. Nothing is inlined, rewritten or generated — there is no `tools/story_artifact.py`, no test for one, and no `tools/README.md` row. Two consequences shape the port: every reference in the story files must be **relative** (the Artifact host does not serve root-relative paths, G32 — AC-11 makes this a Python check with a control, so the files map is derivable from the files themselves), and the font `url()`s are written `../assets/fonts/…` so the one `story.css` resolves in both homes (§3.1). Three properties of the host are asserted by the review and not yet measured — a full `<!doctype>` document rendering inside the host's own skeleton, a same-origin `import './three.module.js?v=160'` loading, and the relative fonts resolving — so Step 9 verifies them before the first publish, with option (a) as the fallback. Who publishes and when: Code, on Cray's request, after a merge touching `story/`, from the shared checkout at the merged sha (or a scratchpad copy proven byte-equal), with a printed record `files=N sha_match=N rendered=yes|no`.

### 3.8 The deploy — once, gated (SD-7 ruled (a))

One deploy at the end (Step 13), by `DEPLOY.md`'s sequence, with every host-reaching command behind a recorded Cray go per phase. Because this deploy changes `cloudflared/config.yml`, the host checkout must be pulled and the connector recreated (G21) — a second host-state action inside the same occasion, named in the go request. The live read is **evidence, not the gate** (CLAUDE.md §8): AC-10 records `pre=<edge status before>` / `post=<status after>` and the CSP header, with the pre-deploy 404 as the natural RED baseline.

---

## 4. Acceptance Criteria

Every AC is a `[check]` witnessed through `tools/probe_battery/` (one mutation per assertion, §4.1) except AC-9 and AC-10, which are `[evidence]` with a printed instrument control. No AC stubs the YAML, the procedure loader, `sourcing.py`, the seed, or the static mount.

- [ ] **AC-1 [check] — the served story loads nothing from outside the origin.** No `http(s)://` or scheme-relative reference in any `src`, `href`, `import … from`, `@import` or `url(` across the authored story files (`index.html`, `story.js`, `story-data.js`, `story.css`; the vendored module is excluded **by name** and the test asserts each authored file exists, so the scanned set cannot be empty); the checker is shown to flag a fixture string holding the stage-1 CDN import. *Artifacts:* `tests/api/test_story_page.py::test_story_files_reference_no_external_origin`, `tests/api/test_story_page.py::test_the_origin_checker_flags_a_known_cdn_import`. *Pass read:* both green; the first prints `refs=N` with N ≥ 4. *Probes:* P1a, P1b.
- [ ] **AC-2 [check] — `/story/` is served under the console CSP on the published profile, unprofiled, and PLAN-0100's fail-loud root stays intact.** With `settings.ui_profile` patched to `published` (G24) and an ASGI client that does **not** raise app exceptions: `GET /story/` → 200, `Content-Security-Policy == main._OCT_CSP`, body contains `type="module" src="story.js`, body contains **no** `name="ui-profile"`, `cache-control` is not `no-store`. Controls: `GET /` on the same client contains `content="published"`; `_profiled_index` called directly on a `FileResponse` to a temp file lacking the anchor raises `RuntimeError`. *Artifacts:* `tests/api/test_story_page.py::test_story_index_is_served_unprofiled_on_the_published_profile`, `tests/api/test_story_page.py::test_root_index_is_still_profiled`, `tests/api/test_story_page.py::test_profiled_index_still_raises_without_the_anchor`. *Pass read:* all green; the first prints `status=200 csp=match profile_meta=absent`. *Probes:* P2a, P2b, P2c.
- [ ] **AC-3 [check] — the edge admits exactly the story paths, anchored, and the table says so.** `config.yml` gains `^/story/$` and `^/story/[^/]+$`; `_EXPECTED_ALLOW["oct-fleet-maintenance"]` gains the same two; every file in `static/story/` fullmatches a story row, `story/` has no subdirectory, and the control path `/story/sub/x.js` matches **no** row. *Artifacts:* `tests/deploy/test_published_profiles.py::test_the_allow_set_equals_this_systems_expected_table`, `tests/deploy/test_published_profiles.py::test_every_pattern_is_anchored_at_both_ends`, `tests/api/test_story_page.py::test_every_story_file_is_admitted_by_a_story_ingress_row`. *Pass read:* all green; the third prints `files=6 admitted=6 control_admitted=0`. *Probes:* P3a, P3b, P3c.
- [ ] **AC-4 [check] — the data block equals the real ontology, procedure, rules and seed, and every case outcome is the real rule's outcome.** Eleven assertions, one test each, all reading real producers (§3.2): (a) object types = `load_doc(yaml)["object_types"]` keys, set and count; (b) link types = the YAML's `(name, from, to)`; (c) undeclared refs = `type: ref` targets with no `link_types` pair, computed from the file, non-empty; (d) step ids in order = `load_procedures("fleet_maintenance")`'s `governed_repair_approval` steps, `quote_gate` = `rule_gate`/`three_quote`, `approve` = `doa_tier`/`gated`; (e) tiers = the loaded ladder's `(min_amount, approver_role)`; (f) SoD `distinct_steps` and `event_kind` match; (g) `three_quote_threshold_thb == int(THREE_QUOTE_THRESHOLD_THB)`, `min_distinct_vendors == MIN_DISTINCT_VENDORS`, `minor_repair_ceiling_thb` equals every `truck_records()` ceiling (all equal, printed); (h) per case `compute_three_quote(...) == (expected.sourcing_pass, expected.basis)`, `expected.tier_role` = the loaded ladder's tier for the amount, `expected.breach == amount >= ceiling`, `expected.outcome` derived; (i) every `illustrative: false` case matches a seed row in `synthetic._fixture_events()` — the fixture alone, read directly because `operational_events()` overlays the module-level live-case view that `case_projection.refresh(session)` fills, so its content would depend on which tests ran first (G31) — by truck, amount and stamped `three_quote_basis`; the `illustrative: true` case matches none; the count of real matches is printed (`seed_matches=2`); (j) `generate_all(yaml, tmp_path)` keys = the block's emitter keys and `"fleet_maintenance"` is in neither committed-destination map; (k) the delimiters occur once each, the block parses, every top-level list is non-empty, `len(cases) >= 3`. *Artifacts:* `tests/api/test_story_drift.py`. *Pass read:* eleven green; (g), (i) and (j) print their measured values. *Probes:* P4a–P4l (P4l mutates `sourcing.py` itself, proving the oracle reads the real function).
- [ ] **AC-5 [check] — no ruled-out literal in the authored story text (lexical, not semantic — §3.6).** Absent: `http://`, `https://`, `www.`, `30,001`, `฿30,001`, `สามหมื่นเอ็ด`, `immutable`, `ไม่ให้โมเดลตัดสินอะไรเลย`, `12/12`; present: `tamper-evident`; `30001` count equals the tier count at that minimum (printed); `AI` (word-bounded) ≤ 1 (printed); a fixture holding `฿30,001` is flagged by the same function. *Artifacts:* `tests/api/test_story_page.py::test_story_text_carries_no_ruled_out_literal`, `tests/api/test_story_page.py::test_the_literal_checker_flags_a_known_numeral`. *Pass read:* both green; prints `ai_tokens=0 band_numeral_in_data=1`. *Probes:* P5a, P5b, P5c.
- [ ] **AC-6 [check] — story references and story files are a bijection (Trap 3 closed for `story/`).** Forward: every reference in `index.html`, `story.js`, `story.css` resolves on disk; reverse: every `.js`/`.css` in `story/` is referenced or in `_UNREFERENCED_STORY_FILES` (empty); no stale exemption; the parse found ≥ 1 `.js` and ≥ 1 `.css` reference and the directory is non-empty. *Artifacts:* `tests/api/test_story_page.py::test_every_story_reference_resolves`, `tests/api/test_story_page.py::test_every_story_file_is_referenced_or_exempt`, `tests/api/test_story_page.py::test_the_story_parse_is_not_vacuous`. *Pass read:* all green; prints `refs_js=N refs_css=M files=K`. *Probes:* P6a, P6b.
- [ ] **AC-7 [check] — the console offers the link, it opens a new tab, and no tab was added.** The chosen module (SD-2) renders an anchor with `href: '/story/'`, `target: '_blank'`, `rel: 'noopener'` (parsed with comments stripped); the `ALL_VIEWS` census still equals `MEASURED_TAB_CENSUS` (imported from `test_static_ui.py`, so the control is the existing pin). *Artifacts:* `tests/api/test_story_page.py::test_console_offers_the_story_link_in_a_new_tab`, `tests/api/test_static_ui.py::test_tab_census_matches_the_measured_header_ladder`. *Pass read:* both green. *Probes:* P7a, P7b.
- [ ] **AC-8 [check] — scenario: a published visitor reaches the story through the real mount, and the data they receive is the real rules' data (CLAUDE.md §8).** With the published profile patched and no stub anywhere: `GET /` → 200 carrying the `app.js` reference; `GET /story/` → 200 with the CSP header; every reference parsed from the **served** `index.html` and `story.js` → 200 from the same mount; the block extracted from the **served** `story-data.js` body (not from disk) re-passes AC-4(h) against `compute_three_quote`; the served `three.module.js` body exceeds 100,000 bytes (a real library, printed). *Artifacts:* `tests/api/test_story_scenario.py::test_a_published_visitor_reaches_the_story_and_its_data_is_the_real_rules`. *Pass read:* green; prints `served_refs=N three_bytes=B cases_checked=3`. *Probes:* P8a, P8b.
- [ ] **AC-9 [evidence] — Cray's six explainer rulings and the R8-adjacent note are recorded in the rulings file as a record, not a rule.** *Artifact:* `docs/strategy/public/intro-video-production-rulings.md` (a new §2.3 and a note in §4.1 — SD-6). *Pass read:* `git grep -c` over the file prints `1` for the new R8 note's fixed phrase, `1` for the known control phrase `Drop the ฿15,000 contrast`, and `0` for a deliberately misspelt phrase; all three values printed in the PR body. *Probe:* the misspelt-phrase `0` is the negative control; the known phrase `1` the positive.
- [ ] **AC-10 [evidence] — `/story/` is live through the published edge, under Access, with the CSP header.** After Step 13, an authenticated read of `/story/` returns 200 and the CSP header; the same read taken **before** the deploy returned the edge's 404. *Pass read:* the PR body prints `pre=404 post=200 csp=present`, the demo-state token read after boot (`DEMO-STATE: PRISTINE` — no token is FAILED), and the Cray go it ran under. *Probe:* the pre-deploy 404 is the RED baseline; a post-deploy read that omits the CSP header is a FAIL, not a partial pass.
- [ ] **AC-11 [check] — every story reference is relative and resolves inside `story/` or `assets/fonts/`, so the multi-file Artifact's files map is derivable from the files themselves (SD-5 (d)) — plus the publish record as evidence.** Check: over the authored story files (comments stripped, vendor excluded), every `src`, `href`, `import … from`, `@import` and `url(` reference is **relative** (no scheme, no leading `/`) and resolves to a file under `story/` or `assets/fonts/`; a fixture holding a root-relative `/assets/fonts/x.woff2` is shown to be flagged. Evidence: the one publish record printing `files=N sha_match=N rendered=yes|no`, where `sha_match` counts files whose `git hash-object` blob id over the published source copy equals `git rev-parse <merged-sha>:<repo path>`, and `rendered` is Step 9.3's browser read. *Artifacts:* `tests/api/test_story_page.py::test_every_story_reference_is_relative_and_in_bounds`, `tests/api/test_story_page.py::test_the_relative_checker_flags_a_root_relative_url`. *Pass read:* both green; the first prints `refs=N relative=N`; the publish record is printed in the PR body with `sha_match == files` and `rendered=yes`. *Probes:* P11a, P11b.

### 4.1 Probe plan — one mutation, one assertion; the sibling that stays green is what makes the RED attributable

Batteries are written **after** the final format pass (README §"Write the battery AFTER…"); `expect_claim` keys come from `python -m tools.probe_battery keys <test>`, never by hand.

| Probe | Subject (mutation) | Node | Assertion predicted RED | Stays green |
|---|---|---|---|---|
| P1a | `story.js`: reinsert `import * as THREE from 'https://cdn.jsdelivr.net/…'` | AC-1 first | "no external origin" | AC-1 control, AC-6 |
| P1b | the checker's regex → `https://never` | AC-1 second | fixture-flagged control | AC-1 first (vacuous under this mutation — that is the point of the control) |
| P2a | `main.py`: root-index equality → back to `endswith("index.html")` | AC-2 first | `status == 200` (500 under the fail-loud raise) | AC-2 root control, AC-2 raise control |
| P2b | `main.py`: delete `response.headers["Content-Security-Policy"] = _OCT_CSP` | AC-2 first | `csp == _OCT_CSP` | `status == 200` |
| P2c | `main.py`: `raise RuntimeError(…)` → `return response` | AC-2 third | `pytest.raises(RuntimeError)` | AC-2 first, second |
| P3a | `config.yml`: remove the `^/story/$` row | set-equality test | `set(...) == expected` | anchoring test |
| P3b | `config.yml`: `^/story/[^/]+$` → `^/story/[^/]+` | anchoring test | `endswith("$")` | set-equality is RED too (different node — not run by this probe) |
| P3c | `config.yml` + table: `^/story/[^/]+$` → `^/story/[a-z]+$` (excludes the dotted filenames) | AC-3 third | `admitted == files` | `control_admitted == 0` |
| P4a | `story-data.js`: drop `"Vendor"` | AC-4(a) | object-type set equality | (b)–(k) |
| P4b | `story-data.js`: `["truck_at_depot","Truck","Depot"]` → `…"Vendor"]` | AC-4(b) | link-type equality | (a), (c)–(k) |
| P4c | `story-data.js`: drop `["RepairCase","Truck"]` | AC-4(c) | undeclared-ref equality | (a), (b), (d)–(k) |
| P4d | `story-data.js`: swap `judge` and `reshape` | AC-4(d) | ordered step ids | (e)–(k) |
| P4e | `story-data.js`: tier `5001` → `5000` | AC-4(e) | tier equality | (h) stays green (15,000 still lands on the same rung) |
| P4f | `story-data.js`: `"distinct_steps": ["intake","fulfill"]` | AC-4(f) | SoD equality | (g)–(k) |
| P4g | `story-data.js`: `"three_quote_threshold_thb": 29000` | AC-4(g) | constant equality | (h) — outcomes are pinned, not recomputed from the block |
| P4h | `story-data.js`: case 1 `"basis": "three_quotes"` | AC-4(h) | `compute_three_quote(...) == expected` | (i) — the seed match keys on truck/amount/basis of the **non**-illustrative cases |
| P4i | `story-data.js`: case 2 `"illustrative": true` | AC-4(i) | `seed_matches == 2` / illustrative-matches-none | (h) |
| P4j | `story-data.js`: `"context_pack"` → `"context"` | AC-4(j) | emitter-key equality | (a)–(i), (k) |
| P4k | `story-data.js`: delete the `STORY_DATA_JSON_END` delimiter | AC-4(k) | delimiter count / parse | — (every other test errors at extraction; this probe's declared claim is (k)'s own) |
| P4l | `sourcing.py`: `THREE_QUOTE_THRESHOLD_THB = Decimal("30000")` → `Decimal("50000")` — the **producer**, not the block | AC-4(h) | case 2's real basis becomes `under_threshold` ≠ pinned `three_quotes` — proves the oracle reads the real function | (a)–(f), (j), (k). ✎ (g) **and (i)** also redden under this mutation — (g) because the constant moved; (i) because `_sourcing_signal` restamps case 2's seed row `under_threshold` at import while the block's pinned `three_quotes` does not move — both are different nodes this probe does not run; P4l's declared claim is (h), and (g)/(i) have their own probes P4g/P4i |
| P5a | `story.js`: append ` ฿30,001` to an Act-4 caption | AC-5 first | band-numeral absence | `tamper-evident` present, `AI ≤ 1` |
| P5b | `story.js`: a Sources note → `https://example.invalid` | AC-5 first | URL absence | the rest |
| P5c | `story.js`: `tamper-evident` → `immutable` in the Act-5 sub-caption | AC-5 first | `immutable` absence (declared) — the test asserts this **before** the `tamper-evident` presence assert, so the first failing assert is the declared one; presence is witnessed separately by the fixture-control test | URL absence, numeral absence |
| P6a | `index.html`: add `<script src="ghost.js">` | AC-6 forward | dangling == [] | reverse (no new orphan) |
| P6b | `index.html`: delete the `story.css` `<link>` | AC-6 reverse | orphans == [] | forward (no dangling) |
| P7a | link module: remove `target: '_blank'` | AC-7 first | `target == _blank` | census pin |
| P7b | link module: `href: '/story'` | AC-7 first | `href == /story/` | census pin |
| P8a | `story-data.js`: case 3 `"basis": "three_quotes"` | AC-8 | served-block rule check | `served_refs` 200s, `three_bytes` |
| P8b | `index.html`: `src="story.js?…"` → `src="stori.js?…"` | AC-8 | every served reference → 200 | CSP on `/story/` |
| P11a | `story.css`: `url('../assets/fonts/IBMPlexSans-Regular.woff2')` → `url('/assets/fonts/IBMPlexSans-Regular.woff2')` | AC-11 first | `relative == refs` | the fixture control; AC-1 (a root-relative path is still same-origin — the two checks ask different questions) |
| P11b | the relative-checker's leading-`/` test → never matches | AC-11 second | fixture-flagged control | AC-11 first (vacuous under this mutation — the control's point) |

> Drafting note (Lesson #0056 — derive the expectation, do not relax the check): P4l was first drafted as `MIN_DISTINCT_VENDORS = 3 → 2`, which reddens **nothing** — case 1 (1 vendor) still fails on `quotes_required` and case 2 (3 vendors) still passes on `three_quotes`. The row above is the corrected mutation; the mis-prediction is recorded here so the next author does not re-derive it.

---

## 5. Out of Scope

- ❌ A **generated** story graph — deriving the data block from the YAML at generate time ("emitter #6", deferred by the design brief). The block is pinned by CI, not emitted.
- ❌ **Tab K** or any change to `ALL_VIEWS`, `MEASURED_TAB_CENSUS`, or `test_static_ui.py` (L1).
- ❌ Any DB → ontology feature, any LLM-proposes-spec loop, any MCP runtime tool-calling — not built and **not depicted** (L3).
- ❌ Narration audio / the VO script (private, gitignored).
- ❌ Re-timing the intro video; the total runtime question (L2).
- ❌ A language toggle; other verticals; publishing `/story/` on any other published profile.
- ❌ A JS test runner, Node, and any bundler or inliner — for the console (`ui.md` §5) **or** for the Artifact: SD-5 (d) publishes the Artifact multi-file from the same files; an inliner exists only as Step 9.4's fallback, and only after a new SD.
- ❌ Changing `_OCT_CSP`, the `?v=` scheme, or `test_asset_manifest.py`'s scope.
- ❌ Vendoring IBM Plex Sans Thai (SD-4 ruled (b): Thai falls to the system face, as the product's own Thai does).
- ❌ Deleting or pruning any worktree under `.claude/worktrees/` (L6).
- ❌ The shoot itself and its pre-shoot demo-state check (rulings file §6) — Step 13 leaves the state readable, nothing more.

---

## 6. Steps

Each Step names its Cray gate where one exists. Steps reference ACs in plain text; the AC ledger is §4.

### Step 0 — Capture the stage-1 prototype into the repo (no SD dependency)

1. Create `services/api/static/story/` and commit the prototype **verbatim** as `story/index.html` in the branch's first commit — it sits in a session scratchpad outside the repo and can vanish. The verbatim copy still carries the CDN import and the Google Fonts link; AC-1 is RED at this commit by design, and Step 2 turns it green.
2. Add a two-line header comment naming it "the stage-1 prototype, captured 2026-09-15" — no scratchpad path, no Artifact URL.

### Step 1 — Vendor Three.js (Cray gate: permission per download)

1. **Before downloading anything**, ask Cray for permission naming: filename (`three.module.js`), version (`0.160.0`, the one the prototype ran against), source (the npm package `three`'s `build/three.module.js`, or the same file from jsdelivr), licence (MIT), and the expected size (⚠️ not measured — report the actual byte count after download). Await the typed go.
2. Place it at `services/api/static/story/three.module.js` (SD-1 default) with `THREE_LICENSE.txt` beside it. Never `.mjs` (G11).
3. Record the download (source, sha256, bytes) in the commit body.
4. **No font download** (SD-4 ruled (b)).

### Step 2 — Port the page (SD-3 = (b), SD-4 = (b), SD-5 = (d) — unblocked)

1. Split the prototype: `story.css` (the `<style>` block + `@font-face` for the shipped Plex `.woff2` via **relative** `url('../assets/fonts/…')` — §3.1; every other reference relative too, for AC-11), `story-data.js` (the block, §3.2, mirroring `trace-kinds.js`'s IIFE + delimiter shape), `story.js` (an ES module; `import * as THREE from './three.module.js?v=160'`), `index.html` (`<!DOCTYPE html>`, `<html lang="th">`, charset + viewport metas, the chrome, `?v=` tokens on every reference).
2. Delete `computeThreeQuote`, `doaTier` and the JS constants; `story.js` reads `window.STORY_DATA` and renders (§3.2). Keep `evaluate(t)` pure, `prefers-reduced-motion`, the `ถ่ายทำ` clean mode, the Sources drawer.
3. `innerHTML` only for the two static SVG literals, or replace them with `document.createElementNS` — either satisfies `ui.md` §3. No `fetch`, no `eval`, no inline event handlers.
4. Re-read every `file:line` string the Sources drawer shows (G28) against `main`; correct any that moved. These strings are on camera.
5. Carry stage 1's two `notClaimed` disclosures and every caption verbatim except where §3.6's lexical rules or a G28 correction require a change; list every changed caption in the PR body for Cray's semantic read.
6. Remove the verbatim capture's CDN and Google Fonts lines. AC-1 goes green here.

### Step 3 — Serve it: narrow the index rewrite (SD-1 ruled (a) — unblocked)

1. `_StaticFilesWithCSP.get_response`: replace `str(response.path).endswith("index.html")` with equality against the mount's root index (`Path(response.path) == Path(self.directory).resolve() / "index.html"`, resolved the way `FileResponse.path` is). One line; the docstring gains one sentence saying nested indexes are served plain.
2. Write AC-2's three tests (`tests/api/test_story_page.py`), the ASGI client constructed with `raise_app_exceptions=False` so a raise reads as `500`, not as a crash.
3. SD-1 ruled (a); option (c)'s anchor-carrying variant is not built.

### Step 4 — The drift guard (SD-3 ruled (b) — unblocked)

1. Read `VerticalProcedures` / the step and governance-content models in `services/engine/procedures/spec.py` (G16) to name the attributes before writing assertions.
2. Write `tests/api/test_story_drift.py`: a module-level `_block()` extractor (delimiters, `json.loads`), then the eleven tests of AC-4, each printing what it measured where the AC says so. Real imports only: `services.engine.code_generator.load_doc` / `generate_all` / `_ORM_COMMITTED_DEST` / `_PYDANTIC_COMMITTED_DEST`, `services.engine.procedures.spec.load_procedures`, `verticals.fleet_maintenance.sourcing`, `verticals.fleet_maintenance.data_adapter.synthetic`.
3. Add the header comment to the block: *"`expected.*` is pinned by `tests/api/test_story_drift.py` against the real rules — edit the case, run the test, it prints the value the real rule produces."*
4. For (i), read the seed as `synthetic._fixture_events()` — never `operational_events()`, whose live-case overlay depends on test order (G31). SD-3 ruled (b): no runtime recompute or banner is built.

### Step 5 — The story guards: origin, lexical, bijection (no SD dependency)

Write AC-1, AC-5 and AC-6's tests in `tests/api/test_story_page.py`, each with its instrument control (the fixture-flag tests) and its anti-vacuity control (the counts printed).

### Step 6 — The entry link (SD-2 ruled (a) — unblocked)

1. Add the anchor in the header `.right` cluster before Refresh, through `h()`; label **"ทำไม"** (SD-2 ruled (a)), never "Story mode", never a URL.
2. Write AC-7's test; do **not** edit `test_static_ui.py`.
3. Measure the header width at 1280 / 1440 / 1920 on both profiles (browser devtools, `scrollWidth` vs `clientWidth`) and print the six numbers in the PR body — §8.

### Step 7 — The edge rows (no SD dependency)

Add the two rows to `config.yml` with their basis comment, the same two strings to `_EXPECTED_ALLOW["oct-fleet-maintenance"]`, and AC-3's reachability test. Nothing else in the profile directory changes.

### Step 8 — The scenario test (no SD dependency)

Write `tests/api/test_story_scenario.py` per AC-8 — real app, real mount, published profile, served bytes, real `compute_three_quote`.

### Step 9 — Verify the multi-file Artifact publishes from the same files, then publish on request (SD-5 ruled (d), interpreted — Cray confirms at PR review)

1. **The files map**, derived from AC-11's test rather than typed by hand: every authored file in `story/` plus `three.module.js` and `THREE_LICENSE.txt` at their `story/`-relative keys, and each `assets/fonts/*.woff2` that `story.css` references at the key `assets/fonts/<name>`. Root-relative paths are not served by the Artifact host (G32), which is why AC-11 requires every reference to be relative.
2. **Source location.** The Artifact host reads sources only under the session's working directory or its scratchpad (G32). Publish from the shared checkout **after** the merge and a pull to the merged sha, or from a scratchpad copy; either way record, per file, `git hash-object <published copy>` == `git rev-parse <merged-sha>:<repo path>` — `sha_match` in the publish record is the count of equalities and must equal `files`.
3. **Verify the three asserted-not-verified host properties before the first real publish** (a throwaway private publish is fine): (i) the full `<!doctype html>` document renders inside the host's own page skeleton; (ii) the same-origin module import `./three.module.js?v=160` loads (the scene draws); (iii) the fonts resolve (Plex glyphs on a Latin caption, compared against the console). Print `rendered=yes|no` with a one-line reason per item.
4. **Fallback if any of (i)–(iii) fails:** option (a) — a stdlib inliner `tools/story_artifact.py` (≤ ~80 lines, a printed `VERDICT:` line per Lesson #0007, refusing to write under `services/api/static/`, with a real-producer test and a `tools/README.md` row) — or, for (i) alone, a thin wrapper `index.html` that only loads the same files. Either fallback is surfaced to Cray as a **new SD** before it is built, because it re-introduces a build the ruling eliminated.
5. **Who and when.** Code publishes on Cray's request after a merge touching `story/`; each publish appends its record (`files= sha_match= rendered=`, the merged sha, the date) to the PR body or a deploy log under `docs/logs/`. Under (d) there is no inliner, no `tools/story_artifact.py`, and no `tools/README.md` row.

### Step 10 — Record the rulings (SD-6 ruled (a) — unblocked)

Edit `docs/strategy/public/intro-video-production-rulings.md`: a new §2.3 *"The story-mode explainer (typed 2026-09-15)"* carrying L1–L6 as a **record** in the file's own table shape; a dated note under §4.1 beside R8 — *"2026-09-15: the ฿15,000 contrast returns in the explainer's Act 4 as a third case (L5). R8 is not reversed for the Tab H shot"*; §5 gains *"the total runtime may grow with the explainer — not ruled"*; §7 gains the provenance rows. Then take AC-9's three `git grep -c` readings.

### Step 11 — Batteries and coverage (no SD dependency)

1. `python -m tools.probe_battery keys` over the four test modules; write `tests/batteries/plan-0126-*.json` (P1–P11), commit them **with** the `**Batteries:**` header made live in this PLAN.
2. Run each battery; every probe `WITNESSED`; run `tools/probe_coverage.py`; exemptions only with a written reason.
3. Full offline gate at CI scope: `ruff check .`, `mypy services/`, full `tests/` (the offline-gate rule).

### Step 12 — The PR (Cray merges)

`feat/plan0126-story-explainer` → PR with `--body-file`; body carries every printed value from §4 and the Step 6 widths, the Step 2.5 caption list, the Step 1 download record, and — for Cray's confirmation of the interpreted SD-5 (d) — the Step 9.3 verification reading. **No `--auto`.** Report green; Cray decides when it lands.

### Step 13 — Deploy once (Cray gate: explicit go per phase, per occasion; SD-7 ruled (a) — unblocked)

1. **Read-only pre-flight** (`DEPLOY.md` §2 — ask for the go anyway, it reaches the host): `docker ps` baseline, `compose ls`, live image id, `demo_run_reset` plan mode → the `DEMO-STATE` token; host `rev-parse HEAD`; `git diff --name-only <host-sha> HEAD -- …/docker-compose.yml …/cloudflared/` — **non-empty by construction here** (Step 7 changed `config.yml`), so the go request for phase 3 names *both* the image ship **and** the host `git pull` + `--force-recreate cloudflared` (G21).
2. **Pre-ship** (§2a, no host contact): build locally with placeholder secrets; `sha256sum` the six story files inside the image against the working tree — a `No such file` means `.dockerignore` or `COPY` never carried `story/` (⚠️ not read by the drafter; this is the check).
3. **Take the AC-10 pre-read**: an authenticated `GET /story/` through the edge → expect the catch-all 404. Record it. This is the RED baseline.
4. **Ship** (§3, after the recorded go): tag `:prev`, `save | ssh … load`, inspect (id identical), host `git pull`, `config --quiet` (zero bytes), `up -d` with `--force-recreate cloudflared`; verify against the §2 baseline (§4).
5. **Post-read**: `GET /story/` → 200 + CSP header; `GET /story/story.js` → 200; the demo-state token after boot. Print `pre= post= csp=` and the token in the PR body / the deploy log under `docs/logs/`.
6. If anything in 4–5 fails: `docker tag :prev` back and `up -d` (the rollback `DEPLOY.md` §3 step 1 exists for), under the same go.

### Step 14 — Close

STATUS reconcile (the ledger names `PLAN-0126 AC-N CLOSED` per Check 2's attribution rule); `git mv docs/plans/0126-*.md docs/plans/done/` in its own `docs/*` PR once Cray ratifies completion. No worktree is touched.

---

## 7. Surfaced decisions (Cray adjudicates; the draft's recommendations are contingent)

### SD-1 — Where the page lives, and how Trap 1 is closed

- **Question.** `static/story/index.html` at `/story/` requires that the index rewrite stop firing on it; the alternatives avoid the code change at a cost.
- **Options.** **(a)** `story/index.html`; narrow `_profiled_index`'s trigger to the **root** index (one line, `main.py:171`), AC-2 pins both the story's plain serving and the root's fail-loud raise. **(b)** `static/story.html` served at `/story.html` — no `main.py` change, but the URL is not the ruled `/story/`; making it `/story` needs a FastAPI route outside the CSP mount (a second serving path with its own header handling). **(c)** keep `story/index.html` and put `<meta name="ui-profile" content="dev" />` in it — no `main.py` change; the rewrite fires harmlessly (the story ignores the tag), but the page then depends on an anchor it never reads, 500s on the published profile if `_UI_PROFILE_META_DEV` ever changes (a *false* fail-loud), and is served `no-store`.
- **Recommendation: (a).** PLAN-0100 wrote `endswith("index.html")` when exactly one index existed; narrowing states the guarantee it actually meant, and the accelerator clause covers this — the serving tests run against the real mount under `TestClient`. Sub-choice folded in: the vendored module lives **story-local** (`story/three.module.js`) so AC-6 guards it and no `_UNREFERENCED_ASSETS` row is needed (a top-level `assets/three.module.js` would be a manifest orphan; an `assets/vendor/` subdir would be unguarded — G6).
- **Why Cray.** It edits a published-surface fail-loud mechanism Cray ratified under PLAN-0100.
- **RULED (a)** — Cray, typed 2026-09-15: *"SD-1 ถึง SD-7: เอาตามที่แนะนำทั้งหมด"*.

### SD-2 — Where the entry link lives, and what it says

- **Question.** The console must offer `/story/` in a new tab without a Tab K, without widening the header past its measured ladder, and without colliding with the existing PLAN-0033 "Story mode" launcher already in the header (G12).
- **Options.** **(a)** the header `.right` cluster, before Refresh, next to the existing launchers — an `iconbtn`-styled anchor. **(b)** Tab J's hero (the dispatch's candidate) — the export cover is the wrong home for a "why" page. **(c)** Tab F (Procedures) — the ladder the story explains is read there; a small link in the procedure card header. **(d)** the persistent D6 notice strip.
- **Recommendation: (a)**, labelled with a short Thai phrase that is not "story"/"เรื่อง" and not a URL — the drafter's suggestion is **"ทำไม"** (the page answers *why the flow is shaped this way*) with the `book`/`play` glyph from the in-repo icon set; Cray picks the word. Rationale: the `.right` cluster is where launchers already live, the published profile renders six tabs so headroom exists (G7's 2253px was ten tabs), and the census pin is the free control. Cost: G7's test pins a breakpoint, not the live width, so Step 6.3 prints the widths.
- **Why Cray.** It is the filmed console's chrome (L2/R7), and the label is a product-voice choice.
- **RULED (a), label "ทำไม"** — Cray, typed 2026-09-15 (the same *"เอาตามที่แนะนำทั้งหมด"*). "ทำไม" was the drafter's suggested word and is taken as ruled under *"ตามที่แนะนำ"*.

### SD-3 — The drift guard: eliminate the JS logic mirror, or keep it beside the Python pin

- **Question.** Stage 1 computed each Act-4 outcome in JS from mirrored rules. Stage 2 has a Python oracle (real loaders and functions) and no JS oracle (G27). Where should the computation live?
- **Options.** **(a)** as the dispatch sketched: the block carries constants, cases **and expected outcomes**; Python pins the block against the real functions; **and** the page recomputes each outcome in JS and shows a failure banner on mismatch. **(b)** **eliminate** the JS rule functions: the block carries constants, cases and expected outcomes; Python pins them against the real functions; the page **renders** from `expected.*` and evaluates no rule; one closed-vocabulary schema check remains in JS.
- **Recommendation: (b).** Under (a) the rule exists three times — the real one, the JS copy, and the pinned value — and the JS copy's only oracle is a banner no CI can see. Under (b) the outcome is still *computed, never authored* (by `compute_three_quote` and the loaded ladder, at test time — P4l proves the test reads the real function), and the page has no logic that can drift. What (b) gives up: the *runtime* self-check Cray saw in stage 1; the Sources drawer wording changes from "computed here" to "pinned against the real rule by CI".
- **Why Cray.** It changes a property of the artifact Cray's first look passed.
- **RULED (b)** — Cray, typed 2026-09-15 (the same ruling). No runtime recompute or banner is built; the page renders from the pinned block.

### SD-4 — The Thai face: vendor IBM Plex Sans Thai, or use the product's own fallback

- **Question.** Stage 1 loaded IBM Plex Sans Thai from Google Fonts (blocked by CSP). The shipped fonts have no Thai face (G9); the console's Thai already renders through `system-ui` (G10).
- **Options.** **(a)** vendor IBM Plex Sans Thai (OFL) — three weights, three `.woff2` files (sizes ⚠️ unmeasured) under `assets/fonts/` beside the existing licence, each download Cray-permitted; the manifest does not enumerate `fonts/`, so no exemption row. **(b)** **eliminate**: `story.css` copies `theme.css`'s stack, loads the **already shipped** Plex Sans/Mono via `@font-face` from `/assets/fonts/`, and lets Thai fall to the same system face the product uses — stage 1's own rationale (*"it must look like that product, not like a second one"*) argues for this.
- **Recommendation: (b)** for stage 2; (a) as a follow-up if the shoot machine's Thai fallback reads badly at 150% zoom (rulings file §5 item 3 already flags font size for the shoot).
- **Why Cray.** Filmed appearance; Cray's first look was of the Plex Sans Thai rendering.
- **RULED (b)** — Cray, typed 2026-09-15 (the same ruling). SD-5 (d) does not reopen this: the fonts are the same shipped Plex files, only referenced relatively (§3.1) so the one `story.css` resolves in both homes.

### SD-5 — How the Artifact channel stays single-source

- **Question.** L1 says the Artifact is built from the same files; a served page cannot be one CSP-legal file. Who builds it, how, and when?
- **Options.** **(a)** `tools/story_artifact.py` (Step 9, AC-11): a deterministic inliner that swaps the vendored import for the CDN import and adds the fonts link only in the Artifact build; Code runs it on Cray's request after any merge touching `story/`; Cray pastes the output into a private Artifact. **(b)** a documented manual concatenation procedure in `docs/runbooks/`, no code, no test. **(c)** freeze the Artifact at stage 1 — contradicts L1's "same files" and is listed only to be rejected. **(d)** *(added at the revision round, from Code's review)* publish a **multi-file** Artifact built from the very files in `services/api/static/story/` plus the shipped `assets/fonts/*.woff2` — no inliner, no `tools/story_artifact.py`, no `tools/README.md` row; the host takes a files map keyed by published path, does not serve root-relative paths, and reads sources only under the working directory or scratchpad (G32), so every story reference must be relative (AC-11) and the publish runs from the shared checkout at the merged sha or a scratchpad copy proven byte-equal; three host properties are asserted-not-verified and are measured in Step 9.3 with (a) as the fallback.
- **Recommendation: (a)** — 60–80 lines under a real-producer test is cheaper than a procedure that drifts; it does not touch the console's no-build rule (`ui.md` §5 scopes to the console).
- **Why Cray.** Republish cadence and ownership are workflow rulings, and a build tool beside a no-build console is a house-rule call.
- **RULED (d) — interpreted; Cray to confirm at PR review.** Code's review recommended (d) over the drafter's (a), and Cray's typed *"เอาตามที่แนะนำทั้งหมด"* (2026-09-15) is read as endorsing the review's recommendation. This is an **interpretation**, not a plain typed pick of (d), and it is written that way here and in the header. Step 9.3 verifies (d)'s three asserted-not-verified host properties before the first publish; if any fails, the fallback to (a) or a thin wrapper comes back to Cray as a new SD. The drafter's (a) recommendation above is kept as written for lineage.

### SD-6 — Where and how the six rulings and the R8 note are recorded

- **Question.** L5 requires the rulings file to record the ฿15,000 addition beside R8. Where do L1–L6 themselves go?
- **Options.** **(a)** the existing file: a new §2.3 table (same shape as §2.1/§2.2), a dated note under §4.1 beside R8, a §5 open item for the runtime, §7 provenance rows. **(b)** a sibling `docs/strategy/public/story-mode-explainer-rulings.md`, with only the R8 note in the existing file.
- **Recommendation: (a)** — one record to find; the file's own header says a session may not reverse a ruling's intent, and the R8 wording (*"not reversed for the Tab H shot"*) must be read next to §4.1's *"do not reopen this as 'the beat feels thin'"*, which (a) puts on the same page.
- **Why Cray.** The file is Cray's record of Cray's rulings; wording that sits beside R8 needs Cray's eyes.
- **RULED (a)** — Cray, typed 2026-09-15 (the same ruling).

### SD-7 — Deploy sequencing

- **Question.** One deploy at the end, or a verify-first deploy of the page before the link and rows land?
- **Options.** **(a)** one deploy after the PR merges — offline suite, local image build with in-image hashes, and a local boot of the built image with `UI_PROFILE=published` as the cheapest live-ish read, then the gated sequence. **(b)** two deploys (page first, link + rows second) — two host-state occasions for no additional evidence, since without the ingress rows the page is unreachable anyway.
- **Recommendation: (a).** The pre-shoot demo-state check stays the rulings file's §6, not a Step here; Step 13.5 only records the post-boot token.
- **Why Cray.** Each deploy is a host-state go (CLAUDE.md §8).
- **RULED (a)** — Cray, typed 2026-09-15 (the same ruling).

---

## 8. Verification

- **Printed values, never bare PASS.** Every test the ACs name prints what it measured (`refs=`, `status=`, `seed_matches=`, `three_bytes=`, `ai_tokens=`, widths, `pre=/post=`). A disagreement between an instrument and the artifact is investigated **at the artifact first** (Lesson #0056).
- **Witnessed RED before any tick.** §4.1's batteries, one claim per probe, coverage report attached; no AC box ticks before its probe (Check 3 binds this once the header goes live).
- **Semantic checklist for Cray at the PR** (no oracle — read the captions): L3's three exclusions absent; the two `notClaimed` lines present verbatim; Act 3 shows translate → execute → phrase and the fixed empty answer; Act 2 shows reference artifacts, not a runtime feed; Act 5 names who holds authority; no numeral for the band; "tamper-evident"; at most one "AI"; no URL anywhere including the Sources drawer; case order and outcomes per L5.
- **Header widths** at 1280 / 1440 / 1920 on dev and published profiles, `scrollWidth ≤ clientWidth` at each.
- **Manual browser read on the dev box** (`UI_PROFILE=published` local boot, PLAN-0095): the page plays end to end, `ถ่ายทำ` hides all chrome, the Sources drawer opens, no console CSP violation is logged — recorded as text in the PR body.
- **Live read** (AC-10) after Step 13, with the pre-read taken first.
- **Artifact publish record** (SD-5 (d), Step 9): `files=N sha_match=N rendered=yes|no` with the merged sha and the three Step 9.3 readings, each with its one-line reason — printed, never a bare "published".

---

## 9. Residual gaps / open questions

1. **Node absent** (G27) — dispatch-measured; the drafter cannot re-run it. Nothing here needs Node.
2. **G28 on-screen citations** (`db_objects.py:1-22`, `pm_import.py:11-21`, `fleet_maintenance_v0.yaml:76-95`, `done/0109:58-68`) — not re-read by the drafter; Step 2.4 re-reads them because they are filmed.
3. **Three.js byte size and the exact MIT text** — unknown until Step 1's permitted download; reported in the commit body.
4. **`VerticalProcedures` attribute names** (G16) — Step 4.1 reads `spec.py` before writing assertions.
5. **`h()` attribute pass-through for `href`/`target`/`rel`** — not verified; if `h()` filters attributes, Step 6 uses `setAttribute` on the returned node.
6. **`.dockerignore` / `COPY` coverage of `story/`** — not read; Step 13.2's in-image `sha256sum` is the check that exists for exactly this.
7. **`tests/api/js_source.strip_js_comments`** — exists (Glob), behaviour not read; AC-5 assumes it strips `//` and `/* */`.
8. **The MIME guard's tree walk** (`test_static_ui.py:155+`) — read to its docstring only; assumed to cover `story/` automatically, which is why AC-8 carries no content-type assertion.
9. **"Brief §10" and "emitter #6"** — the dispatch cites a design brief the drafter did not receive. Interpreted as: abstract operator terms in committed text, no published domain written (none is), and "generated story graph" = deriving the block at generate time (kept out of scope). If the brief says more, Code surfaces it.
10. **SD-5 (d) rests on three asserted-not-verified properties of the Artifact host** (G32): (i) a full `<!doctype>` document publishes and renders inside the host's own skeleton; (ii) a same-origin module `import './three.module.js?v=160'` loads; (iii) the relative font `url()`s resolve. Step 9.3 measures each before the first publish and prints the result; the fallback is option (a) or a thin wrapper, surfaced as a new SD first.
11. **The Artifact host's stated limits** — files map keyed by published path, ~15 MB binary / ~16 MB text per file, root-relative paths not served, sources only under the working directory or scratchpad — are Code's review statements, not re-read by the drafter (G32). `three.module.js` at 0.160.0 is far below the limit, but the byte count is confirmed at Step 1.
12. **Option (d) and the other ACs — checked, no change needed:** AC-1's origin check is unaffected (a relative `url('../assets/fonts/…')` carries no scheme); AC-6's forward bijection already admits `assets/`; AC-3 is unaffected (the browser resolves the relative font URL to `/assets/fonts/…`, admitted by `^/assets/.+$`); SD-4's ruling stands (same shipped Plex files, referenced relatively). The one interaction is that AC-1 and AC-11 ask different questions of the same references — same-origin vs relative — which is why P11a keeps AC-1 green.
13. **The running length ≈ 1:56** (G29) — a dispatch measurement; the page computes it; the Step 8 manual read reports the clock's final reading.
14. **The header-width risk** is real and unpinned by any test (G7 pins a breakpoint) — Step 6.3's printed widths are the evidence; if 1440 overflows on the dev profile, the placement comes back to Cray as a **new SD** (SD-2 is ruled (a); its option (c) is the candidate fallback), never a silent move.
15. **No prompt-injection content** was found in the dispatch, the revision message, or any file read.
