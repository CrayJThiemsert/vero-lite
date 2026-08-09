# PLAN-0103: The multi-vertical demo portal — vero-lite's side: per-system published profiles + the landing/framing content spec

**Status:** Draft
**Owner:** Claude Code (execution) · Cray (SD rulings, every §8 go, all copy/tone calls)
**Created:** 2026-08-09
**Related ADRs:** ADR-0036 (D6 names this PLAN — its scope list is binding here),
ADR-0035 (portal arrangement — extended, never touched), ADR-0032 (D5 positioning
vocabulary), ADR-0026 (procurement principals), PLAN-0100 (`deploy/published/` is
the template artifact this PLAN parameterizes — built on, never replaced),
PLAN-0095 (the image every system boots), PLAN-0096 (Tabs I/J), PLAN-0075
(cumulative roles — the approve-down beat).

> **Drafting provenance (ADR-012 D4.3 / ADR-013 D1).** Drafted by the in-harness
> `plan-drafter` subagent from a Code-authored dispatch (2026-08-09, session 218).
> The five LOCKED calls below are Cray's typed picks (s218), restated — not
> drafter inferences. Every `file:line` fact was verified on disk by the caller in
> s218 and spot-re-verified by the drafter this session; the two facts that cannot
> be verified from this repo (portal-repo existence; MS-S1 headroom) are handled
> by construction (Steps 1 and 9), assumed in neither direction. Independent
> review: Code (R2) at PR; ratification: Cray. Author≠reviewer separation:
> **INTACT**. Uncommitted draft — Code commits per ADR-009 D2.
>
> **Amendment round (2026-08-10, post-R2/PR #1101, same drafter):** SD-1 gains
> its compliance-consequence clause + AC-11 (the RoPA bring-up gate); SD-3/SD-4
> become one joint ruling for procurement (with an on-disk correction to the
> original `G,F,H` recommendation); the model-override measurement is folded
> into Step 4's aggregate-LLM bullet with its tripwire; SD-2(b)'s reasoning is
> upgraded and the demo-calendar variable named. Separation still **INTACT**.

---

## The hard boundary (read before any step)

ADR-0036 D1 (ruling (a)) + ADR-0035 D4/L5 place **the `portal.` landing surface,
the cross-system ingress map, the Access policies, and the domain in the portal
repo**. ADR-0036 D2 adds the registry rule: *"no second registry of systems may
exist anywhere, and vero-lite contributes nothing to the list"* — a vero-lite
file enumerating the published systems would be a shadow ingress map and a D1(3)
leak (`0036:149-155`).

This PLAN therefore:

1. **Creates, names, and assumes zero portal-repo files.** Everything
   portal-side is a **request** (Step 8's delivery mechanism; Step 10's
   per-system ingress-entry + Access-policy asks), transmitted via the
   gitignored handoff channel with a `docs/logs/` thin summary as the tracked
   evidence (the PLAN-004 v2 two-artifact model).
2. **Builds no landing page inside vero-lite.** Each published system keeps
   booting into its own default tab; the "ninety seconds before the machine
   means anything" live on the portal's landing surface, which this PLAN only
   *specifies content for*, as a request.
3. **Splits the landing content so no committed file lists the systems:**
   each system's **self-description card copy** is committed *inside that
   system's own profile directory* (one system per file, no roster — Step 8a);
   the **roster, card order, and assembly** exist only in the portal-side
   request (Step 8b) and, durably, in the portal repo. A guard test enforces
   the split (AC-5). The N profile directories themselves are not a registry —
   they are ADR-0036 D5's own mandate (N committed profiles, `0036:207-217`).

## LOCKED (Cray, typed, session 218 — restated, not re-litigated)

1. **Per-system DB posture, option C:** fleet_maintenance's published system
   gets a Postgres inside its own compose project; energy and procurement stay
   DB-less. (Governance reading of *what authorizes this* — SD-1.)
2. **fleet is the LEFTMOST card** on the portal landing surface. ⚠️ Card order
   ≠ system number (ADR-0036 D4: #1 energy, #2 procurement, #3 fleet on Cray's
   trigger) — the interaction is SD-2, surfaced, not assumed.
3. **Tab E ("Build a Vertical") — its narrative moves to the portal.** E is
   already excluded from the published profile (`app.js:32-39,68`), so the
   app-side delta is small; the *dev-console* fate of E is SD-6, surfaced, not
   decided here.
4. **Bilingual (TH/EN).** Depth of application is SD-7.
5. **Three demo personas, one API key each** — visitors pick who they are, so
   the audit trail records the persona actually chosen, not one anonymous
   identity. Provisioning + disclosure are this PLAN's (Step 6); the keys are
   secrets and never enter git (CLAUDE.md §8; `published.env:8-12`).

## Goal

Deliver vero-lite's side of the ADR-0036 multi-vertical demo portal at zero
engine change to the serving architecture: (i) generalize the published-UI
mechanism off its N=1 hardcode (`app.js:68`) into server-declared, per-system
published view sets; (ii) parameterize PLAN-0100 Step 8's `deploy/published/`
into three committed per-system profiles — `oct-energy` (moved, content-intact),
`oct-procurement`, `oct-fleet-maintenance` (with its own Postgres per LOCKED-1)
— each on its own compose project and Docker network; (iii) author the
procurement and fleet route allowlists under the P12 provisional regime with
per-instance guards; (iv) stand up the three-persona identity layer and fleet's
first-paint posture so a cold visitor can be personally refused an approval and
then granted it as a different persona; and (v) produce the bilingual
landing/framing **content specification** — per-system card copy committed with
each profile, assembly/order/narrative delivered to the portal repo as a request
— without creating any portal-repo file, any in-repo landing page, or any
in-repo list of published systems.

## Acceptance Criteria

Every AC names the evidence that closes it. None is satisfiable by mocking the
seam under test; guards get a non-vacuity probe (plant the violation from a
`/tmp` copy, see the RED, restore).

- [ ] **AC-1 — the hardcode is dead, replaced by a declared set.**
  `PUBLISHED_EXCLUDED_VIEWS` appears nowhere under `services/api/static/`
  (Grep = 0 matches at execution time; today's sole definition+use:
  `app.js:68,72`). Published tab visibility is a per-system server-declared
  setting validated at boot against the ten-tab census — an unknown view key
  **fails the process loudly** (test plants a bad key and asserts the boot
  refusal, same fail-loud philosophy as `config.py:210-215`). The declared set
  reaches the browser pre-first-paint on the existing meta-tag channel **and**
  on `/meta` (`config.py:220-223`), and a test asserts the two carriers agree.
  With no env override, system #1's rendered tab set is **bit-identical** to
  today's published energy set — proven by the existing published-profile UI
  assertions in `tests/api/test_ui_profile.py` passing unmodified.
- [ ] **AC-2 — all 11 `isPublished()` consumers accounted for.** The step's PR
  body carries a per-site disposition table for the full census — `api.js:37`
  (the predicate), `app.js:70,129`, `view-story.js:821,902`,
  `view-anomaly.js:112`, `view-hero.js:606`, `view-procedures.js:221,669`,
  `view-flow.js:184` — classified **tab-set** (re-sourced from the declared
  set) vs **profile-behaviour** (stays on `isPublished()`), with the census
  **re-run by grep at execution** (this PLAN's snapshot is not the oracle; a
  12th consumer added since s218 gets its own row). Every published-profile
  branch that becomes *reachable for the first time* on a new system (Tab G's
  published branch on procurement — dead code under energy, which filters G
  out; the monitor/procedures/flow published branches under fleet's tab set)
  is exercised by a test on that system's vertical fixture. Evidence: the
  table + the named tests.
- [ ] **AC-3 — three committed per-system profiles.** `deploy/published/`
  is restructured into per-system profile directories (shape finalized in
  Step 4 under ADR-0036 D5's "PLAN's to finalize" grant): `oct-energy`'s
  content is PLAN-0100 Step 8's artifact **moved, functionally intact**
  (`git add` before `git mv` — the modified-file hazard); `oct-procurement`
  and `oct-fleet-maintenance` are authored. Each carries committed
  `{docker-compose.yml, published.env, cloudflared/config.yml, README, card
  copy}`. Fleet's compose carries a `postgres` service; energy's and
  procurement's carry **none** (LOCKED-1). Evidence: files on disk;
  per-system env-parse tests (AC-4-of-0100 pattern, extended per instance);
  the three test modules that hardcode the old paths updated and green —
  `tests/deploy/test_published_compose.py:43`,
  `tests/deploy/test_deploy.py:41-42,176`,
  `tests/deploy/test_verify_tunnel_credentials.py:31-32`.
- [ ] **AC-4 — per-system network + project isolation (the ADR-0035 reopening
  tripwire).** No two per-system compose files share a Docker network or a
  compose project name. Today's fixed `name: vero_oct`
  (`deploy/published/docker-compose.yml:105-106`) and project
  `name: vero-published` (`:13`) do not survive as shared literals — the
  compose file's own warning names this PLAN as the owner of that decision
  (`:95-107`). Evidence: a test parses every per-system compose file and
  asserts (a) pairwise-distinct project names, (b) no fixed network `name:`
  shared by two files (per-project scoping or per-system names); non-vacuity
  probe: plant a colliding `name:`, see RED.
- [ ] **AC-5 — no shadow registry, still domain-ignorant.** A guard test
  asserts: no committed file outside a per-system profile directory mentions
  **two or more** distinct `oct-*` system labels (`0036:142-147` label
  convention); each profile directory mentions **only its own** label; the
  apex domain appears nowhere in the repo (ADR-0035 D1(3) via `0036:149-155`).
  Non-vacuity probe: plant a two-label file, see RED.
- [ ] **AC-6 — secrets stay out of git.** `API_KEYS` and any raw persona-key
  material appear in **no committed file**: the per-system env-parse tests
  assert each committed env file's key set excludes `API_KEYS` (and the
  persona-key variable if SD-4 introduces one); `detect-secrets` stays green;
  each per-system README documents host-env-local provisioning (the compose
  bare pass-through pattern, `docker-compose.yml:26-47`).
- [ ] **AC-7 — the persona loop is real (the demo's core moment).** A scenario
  test drives fleet's **real** procedures + auth + audit stack — no side
  mocked (CLAUDE.md §8 scenario rule) — with the three authored principals
  (`verticals/fleet_maintenance/procedures.yaml:102-111`): `req-mechanic-tom`
  is **refused** an approval above his tier; `appr-fleet-manager-wirat`
  approves within tier; `appr-owner` approves **down** (cumulative roles,
  PLAN-0075 Policy B); each decision lands in the real audit trail under the
  `person_id` that acted. Evidence: the named scenario test, green, with the
  refusal asserted **by name**, not by generic 4xx.
- [ ] **AC-8 — fleet's first paint is not empty.** Under the SD-5 ruling, a
  fleet scenario test proves Tab H's backing read returns ≥ 1 waiting run at
  boot (today `main.py:329` gates the seed on `procurement` only, so fleet's
  H opens empty), **and** the visitor path still closes end-to-end: a case
  opened via Tab I's backend appears in H's list. Real seed → real routes →
  real DB (fleet has one, LOCKED-1); no mocks.
- [ ] **AC-9 — the framing layer exists on both sides of the boundary.** Each
  per-system profile directory carries its bilingual card-copy file with both
  TH and EN sections present (guard-asserted structurally — section presence,
  not copy quality, which has no oracle); the portal-side assembly request
  (card order incl. LOCKED-2 fleet-leftmost, the relocated Tab-E narrative
  per LOCKED-3, the arrival narrative, CTA per SD-7) is delivered as a
  handoff whose path is recorded in a committed `docs/logs/` thin summary.
  Evidence: the committed card files + guard + the `docs/logs/` entry.
- [ ] **AC-10 — measured before multiplied, gated before touched.** MS-S1
  headroom is **measured and recorded** (numbers, method, date — Step 9)
  **before** any second system is brought up; every bring-up and the
  measurement session itself each have their own explicit Cray go (§8 —
  host-state changes, do-no-harm to co-tenant stacks). Evidence: the recorded
  measurement + per-action go records in the execution log.
- [ ] **AC-11 — the RoPA reflects fleet's posture BEFORE fleet is reachable
  (appended 2026-08-10, amendment round; precondition of Step 10's fleet
  bring-up, not a follow-up).** Before the fleet system's go: the
  published-demo RoPA (`docs/compliance/ropa-published-demo.md` — or a
  sibling per-dataset instance, Cray's structuring call) covers the LOCKED-1
  consequence: the new processing activity (visitor-typed case free text),
  its storage location (fleet's Postgres), its retention number, and its DSR
  path. 🔴 **Authorship boundary: the RoPA is Cray's artifact, in Cray's
  controller voice — this PLAN gates on it and supplies the change statement
  (SD-1's consequence clause); it authors none of the text** (mirroring the
  portal-repo file boundary). Evidence that closes it: the updated RoPA on
  `main` (authored by Cray; committed via Code's PR per ADR-009 D2) **and**
  fleet's Step-10 go record citing it by path. No test double can satisfy
  this AC: the gate is the committed artifact plus the go record, and a fleet
  bring-up without both is a Step-10 **stop condition**, not a warning.

## Out of Scope

- ❌ **Any portal-repo file** — the ingress map, Access policies, the `portal.`
  landing surface, DNS, the domain (ADR-0036 D1/D6; ADR-0035 D4/L5). Requests
  only.
- ❌ **A landing page, intro screen, or CTA surface inside vero-lite.** The
  caller-verified s218 negative stands: the published app boots straight into
  its default tab, and this PLAN keeps it that way — framing is portal-side
  content, specified here, implemented there.
- ❌ **In-process multi-vertical serving / an in-app vertical picker**
  (ADR-0036 D3 records the measured blocker list; its LOCKED-1).
- ❌ **Full app-UI internationalization.** Bilingual scope is the card copy +
  persona disclosures (SD-7); the console UI's language is untouched.
- ❌ **A shared allowlist or compose generator.** N ≤ 3 near-duplicates are
  accepted deliberately (ADR-0036 D5, Rule of Three; Alt 4 rejected there).
- ❌ **Publishing any vertical beyond energy / procurement / fleet_maintenance.**
  Nine vertical dirs exist on disk; the published set is exactly three, and
  nothing here implies the others are demo-ready (ADR-0023 registry breadth is
  a supporting fact, not a roadmap).
- ❌ **Reopening PLAN-0100 or changing energy's posture.** Energy stays
  DB-less, keyless, tab-set-identical (ADR-0036 D4: PLAN-0100 "completes as
  scoped, for system #1").
- ❌ **A third `ui_profile` value.** The Literal stays two-valued
  (`config.py:215`) — rejected design, Step 2.
- ❌ **The bare `oct.` label's fate** — portal-side, Cray picks at ingress
  creation (ADR-0036 OQ-1).

## Steps

### Step 1: Confirm and branch — does the portal repo exist? (ADR-0036 D6.1)

Unverifiable from this repo; assumed in **neither** direction. Ask Cray.

- **Exists** → Steps 8b and 10 deliver their portal-side asks (per-system
  ingress entry + Access policy; the landing content spec) as coordinated
  requests against the real repo.
- **Does not exist** → its bootstrap is the portal repo's own concern
  (ADR-0035 Implementation Note 1), OQ-4 fires (Cray picks the domain then),
  and this PLAN proceeds on **everything repo-side** (Steps 2–8a) plus the
  Step 9 measurement; Step 10's bring-ups still make each system reachable
  only when its portal-side artifacts exist.

Pass/fail: Cray's answer recorded in this PLAN before Step 8b or Step 10 runs.
Steps 2–7 proceed immediately either way.

### Step 2: Kill `PUBLISHED_EXCLUDED_VIEWS`; server-declared per-system view sets

The bold cut over the strong-oracle seam (dispatch accelerator clause), and the
elimination the §Frontier invited: the exclusion constant does not get a third
profile or a per-vertical branch — **it dies**.

- **New setting** (name final at execution, e.g. `ui_published_views`): the
  ordered list of view keys the published profile renders, validated at boot
  against the ten-tab census (`app.js:12-30`) — unknown key = loud boot
  failure, mirroring `config.py:210-215`'s deliberate Literal rationale.
  **Default = today's energy set**, so system #1 needs no env change and
  `tests/api/test_ui_profile.py` passes unmodified (AC-1's bit-identical
  clause). `ui_profile` itself stays `Literal["dev","published"]` — a third
  value was the rejected alternative (it multiplies profiles per system,
  re-hardcodes the N=1 assumption under a new name, and abandons the
  fail-loud Literal design).
- **Carriage:** the declared set rides the two existing pre-paint channels —
  the injected meta tag + `/meta` (`config.py:220-223`) — so the filter point
  in `app.js` keeps its correct-by-construction property (`app.js:62-67`:
  filter `ALL_VIEWS` itself, never `buildTabs()`).
- **Per-system default tab = the first key of the declared set.** Today `go()`
  falls back to `'A'` — correct for energy, **wrong for procurement**, whose
  adapter's `stream_events` is an empty iterator by design, leaving Tab A
  blank (`published.env:23-26`; the s218 fact-pack's procurement note).
  Procurement's system must be able to land on G (SD-3).
- **The 11-consumer walk (AC-2):** re-grep the census, classify every site
  tab-set vs profile-behaviour, dispose of each in the PR table. Run
  `tools/excision_scope.py` over the constant before deleting — the
  walk-both-ways discipline; ruff will not find what only the census knows.
- Dev profile behaviour: untouched (`VIEWS = ALL_VIEWS` path).

Pass/fail (pre-committed): AC-1 + AC-2 evidence, plus the planted-bad-key boot
refusal test RED-then-green.

### Step 3: Audit the newly-reachable published branches; optional hero-fallback hardening

Published-profile branches in view modules were written under PLAN-0100 when
exactly one system (energy) existed — some are **dead code today** and go live
for the first time on a new system: Tab G's published branch
(`view-hero.js:606`) was unreachable because energy filters G out entirely;
the monitor/procedures/flow published behaviours were unreachable because H was
filtered. For each branch that a new system's tab set makes reachable, add a
test on that system's fixture asserting the branch's behaviour against that
system's posture (AC-2's second clause).

**Optional (flagged per ADR-0036 D4 "optional defense-in-depth," not required):**
refuse the request-time hero fallback for verticals without their own builders —
today `_FALLBACK_VERTICAL = "procurement"` resolves at request time
(`demo.py:61,142-149`), which is why energy edge-excludes G. Cheap under the
strong oracle; include if it costs < a session, drop without ceremony if not.

Pass/fail: named tests per newly-reachable branch; the optional item explicitly
marked taken/dropped in the PR body.

### Step 4: Parameterize `deploy/published/` into three per-system profiles (ADR-0036 D5)

Recommended shape (final under D5's "PLAN's to finalize" grant, ratified via
SD-1's reading): `deploy/published/<system-label>/` per system —
`oct-energy/`, `oct-procurement/`, `oct-fleet-maintenance/` (labels per
`0036:142-147`; the apex domain appears nowhere).

- **`oct-energy/`:** PLAN-0100 Step 8's artifact moved intact (`git add`
  before `git mv`); content deltas limited to internal path references and the
  per-system names below. PLAN-0100 is not reopened.
- **Per-system compose:** three committed compose files, near-duplicates
  accepted at N ≤ 3 (D5's own duplication posture, Rule of Three — same logic
  it applies to allowlists). Each carries: a **per-system project `name:`**, a
  **per-system network** (resolving the compose file's own standing
  instruction to this PLAN, `docker-compose.yml:95-107` — either drop the
  fixed `name:` for per-project scoping or use `vero_oct_<system>`; AC-4
  tests it), per-system container names and volume names, no `ports:` keys
  anywhere (PLAN-0100 AC-5's property, preserved per system).
- **Fleet's compose adds `postgres`** (LOCKED-1, option C): its own named
  volume, reachable only on fleet's network, `TENANT_ID=demo` stamped
  (ADR-0035 D7 — three systems, one demo tenant). Energy's and procurement's
  composes carry none.
- **Per-system env files:** energy's moves intact; procurement's and fleet's
  are authored from it — each pinning `OCT_VERTICAL`, its own
  `OCT_RECOMMEND_*` where energy's defaults don't apply
  (`published.env:31-35`'s warning), `LLM_MAX_INFLIGHT=1` per system.
- **Aggregate LLM posture, pinned as a named value (ADR-0036 OQ-2):**
  1 in-flight per system, **unchanged — and measured-safe today, not merely
  hoped.** The premise change is real: D5's "today at most one published
  system carries an `assisted` route" stops being true the moment fleet
  publishes Tab C — two assisted systems share one Ollama (SD-3 carries it
  to Cray). But the hazard that actually bites — **model-eviction thrash**
  between systems pinning different models — is **absent, measured**
  (Code post-R2; re-verified by the drafter 2026-08-10): `recommender_model`
  / `ollama_default_model` overrides across the repo's `.env`/`.yml`/`.yaml`
  files = **zero committed matches** (the single hit anywhere is the
  **untracked** local dev `.env:19`, which pins the *identical* default
  value), so every system serves the same `gpt-oss:20b`
  (`config.py:97-105`). What remains is plain concurrency, and the existing
  design already bounds it: each process caps at `LLM_MAX_INFLIGHT=1`, and
  over-cap a request **fails fast to the deterministic arm with the
  PLAN-0093 disclosure rather than queueing** (`published.env:47-52`).
  **Tripwire, named so nobody re-alarms and re-measures:** the day any
  per-system env introduces a `recommender_model` / `OLLAMA_DEFAULT_MODEL`
  override, eviction thrash returns and this posture is re-opened — this
  bullet is the dated baseline to diff against, not a claim to re-derive.
- **Test moves:** the three `tests/deploy/` modules' hardcoded paths (AC-3
  list) updated in the same PR as the restructure — never split across PRs.

Pass/fail: AC-3 + AC-4 + AC-6 evidence.

### Step 5: Author the procurement + fleet route allowlists (P12 provisional regime, per system)

Each system's `cloudflared/config.yml` is a committed, anchored,
catch-all-terminated allowlist with its **own** set-equality + anchoring guard
(D5: the guard extends *per instance*).

- **`oct-energy`:** unchanged (hero rows already dropped per ADR-0036 D4).
- **`oct-procurement`:** authored to its SD-3 tab set — the two hero reads
  (`/demo/hero/governance`, `/demo/hero/impact`) return **for this system
  only**; DB-backed routes stay off (procurement is DB-less, LOCKED-1).
- **`oct-fleet-maintenance`:** the conscious per-route reversal of PLAN-0100's
  exclusions, each with its own written basis — because the *bases* differ
  (`app.js:32-39`): Tabs I/J were excluded on SD-1(a) DB-less grounds, and
  that basis **dissolves** for fleet (it has a Postgres); Tab H's routes were
  excluded by **default-deny + C-3**, so each gets an explicit call, none
  inherited: `GET /runs`, `GET /runs/{id}`, `POST /runs/{id}/gate/resolve`,
  `POST /runs/{id}/cancel`, `GET /audit/verify` (the route census from
  PLAN-0100's SD-1 scope note, `0100:1905-1919`). A row PLAN-0100 excluded
  returning here is a **new decision for a new system**, not a reopening —
  P12 makes the allowlist a labelled provisional per system.

Pass/fail: per-system guards green; each fleet row's basis written next to it
in the config header, PLAN-0100-style.

### Step 6: The three-persona identity layer (LOCKED-5)

The personas are fleet's three authored principals — they already exist with a
real authority ladder (`procedures.yaml:102-111`): `req-mechanic-tom` (ต้อม —
ช่างใหญ่, requester), `appr-fleet-manager-wirat` (วิรัช — ผจก.เดินรถ, approver),
`appr-owner` (เฮีย — เจ้าของกิจการ, approver with cumulative roles).

- **Provisioning (this PLAN owns the procedure, never the values):**
  `API_KEYS` maps `sha256(raw key) → person_id` (`auth.py:1-7`) and is a
  secret — provisioned host-env-local via the existing compose bare
  pass-through (`docker-compose.yml:26-47`), documented in
  `oct-fleet-maintenance/README`. Three keys, one per principal. Never in git
  (AC-6; CLAUDE.md §8).
- **Delivery UX:** per SD-4 (recommendation: a published-profile-only persona
  picker backed by env-held raw demo keys; alternative: keys printed in the
  PIN email). Whichever is ruled, the **on-screen disclosure** ships with it,
  bilingual: *you are acting as \<persona\>; every decision is recorded in the
  audit trail under this name.*
- **Scope note (verified nuance):** membership enforcement arms only where the
  vertical *ships* principals (`auth.py:9-18`) — the persona layer is
  meaningful on fleet (procurement ships principals too, ADR-0026, but
  whether it joins is ruled **jointly in SD-3's procurement row**, not here);
  **energy stays keyless**, exactly as PLAN-0100 left it
  (`published.env:8-12`).

Pass/fail: AC-7's scenario test — refused-then-granted across real personas,
audit rows by name.

### Step 7: Fleet's first-paint posture (Tab H must not open empty)

Today the waiting-human seed is procurement-only (`main.py:329`); fleet gets
projection refreshes only (`main.py:364-391`), so its Monitor opens empty until
a visitor files a case at Tab I. Per the SD-5 ruling (recommendation: seed one
**and** keep the visitor path):

- Extend the seed gate with a fleet branch under the same contract as
  procurement's — env-gated, idempotent (fixed run_id, skip-if-present),
  fail-soft (`main.py:330-357`) — writing one waiting_human run into fleet's
  own Postgres.
- The visitor path stays load-bearing and tested: Tab I case → appears in H
  (AC-8's second clause) — the seed removes the empty first paint; the visitor
  still gets to watch their *own* case enter the governed loop.

Pass/fail: AC-8.

### Step 8: The landing/framing content spec (LOCKED-2/3/4) — split across the boundary

**8a — committed, per system (no roster anywhere):** each profile directory
gets one bilingual card-copy file describing **that system only** — name, the
one-line what-you-will-see, the persona hint (fleet's names the three personas
and the refused-then-granted moment), what a visitor does in the first ninety
seconds, and the CTA semantics. No file mentions another system (AC-5 guard).
Copy is conservative and every tone call defers to SD-7 — there is no oracle
over narrative.

**8b — the portal-side request (never a committed vero-lite file):** one
handoff delivering the assembly spec — card order (**fleet leftmost**,
LOCKED-2; explicitly noting SD-2's card-order ≠ system-number ≠
deployment-order separation), the relocated **"Build a Vertical" narrative**
(LOCKED-3: the story Tab E told becomes portal landing copy; the intake
*product* stays in the dev console per SD-6's ruling), the arrival narrative
(PIN email → pick a persona → be refused → be granted → "I want this for my
data"), the bilingual policy (LOCKED-4), and the CTA ask as ruled in SD-7.
Delivery evidence: the `docs/logs/` thin summary naming the handoff path
(AC-9). If Step 1 found no portal repo, the request is drafted and parked in
the same channel, addressed to the future bootstrap — content is not blocked
on the repo existing.

Pass/fail: AC-9.

### Step 9: Measure MS-S1 headroom — before any second system exists (ADR-0036 D6.3)

RAM/CPU for N concurrent app containers + one Postgres is **unmeasured; no
number is assumed anywhere in this PLAN**. With its own explicit Cray go (§8 —
the gated surface is the whole host, and a read-only session is still a host
session): measure the current stack's actual footprint, record numbers +
method + date in this PLAN's execution log, and project for +2 app containers
+1 Postgres against the co-tenant stacks' needs. The recorded result — not an
estimate — gates Step 10. If the projection does not fit, stop and surface:
sequencing/eviction is Cray's call, not a silent downgrade.

Pass/fail: AC-10's first clause.

### Step 10: Bring-up, one system at a time (§8, per-system go)

Deployment order per SD-2's ruling. For each system, in order: (1) explicit
Cray go for *that* bring-up; (2) portal-side asks delivered per Step 1's
branch — one ingress entry + one Access policy, the exact two-artifact cost
ADR-0036 D2's drift check prices; (3) host-side `deploy.py`-pattern bring-up
from that system's profile dir, credentials verified
(`verify_tunnel_credentials.py` pattern per system); (4) live verification of
that system's Step-9-of-0100-style checks (keyed/keyless `/whoami`, tab set,
allowlist behaviour) — live runs minimized, evidence-not-gate (§8; the
offline suite is the gate); (5) do-no-harm check on co-tenant stacks and the
already-published systems.

**Fleet-specific precondition (AC-11):** the fleet go is additionally gated on
the updated RoPA — Cray-authored, on `main`, cited by path in the go record.
No RoPA, no bring-up: a stop condition, not a warning.

Pass/fail: AC-10's second clause, plus AC-11 for the fleet system; per-system
live evidence recorded.

## Surfaced decisions — Cray's slots (recommendation ≠ ruling; nothing below is assumed by the steps)

- **SD-1 — What authorizes per-system DB posture (LOCKED-1's governance
  reading).** The dispatch requires this stated, not assumed. **Reading:**
  PLAN-0100's SD-1(a) ruled *the* published deployment DB-less when exactly
  one existed (`0100:1895-1903,1921-1928`) and PLAN-0100 closed **as scoped,
  for system #1** (ADR-0036 D4) — so SD-1(a) binds the energy system and
  never spoke for fleet. ADR-0036 D5's profile grant is parameterized as
  "{allowlist + env}" with the compose named a *template*, but the operative
  clause is **"recommended shape, PLAN's to finalize"** (`0036:214-217`) —
  compose topology is inside this PLAN's finalization authority — and the
  ADR-0035 acceptance shape prices a system as subdomain + policy *"with
  everything else riding inside the one compose project"* (`0036:134-138`), so
  a Postgres inside fleet's own project costs the portal arrangement nothing
  and fires no reopening trigger. **Recommendation: no separate ADR is owed —
  LOCKED-1 (Cray, typed, s218) + D5's finalization grant suffice, recorded by
  ratifying this SD**; energy's SD-1(a) posture is untouched.
  **Consequence clause (added 2026-08-10, amendment round — the ruling's
  compliance cost, made visible before it is taken, not discovered after):**
  the published demo's RoPA instance (`docs/compliance/ropa-published-demo.md`,
  ~9.2 KB, authored in Cray's voice **as data controller**) describes a
  **DB-less** system — `postgres` / `database`: **zero** mentions; its entire
  personal-data story is the prompt log as a **closed** stored set
  (`ropa:67-70`), explicitly not storing IP / headers / gate identity
  (`ropa:64-66`), 90-day rolling retention (`ropa:100`), 30-day DSR. Under
  LOCKED-1, fleet's system adds what that record does not cover: **Tab I is a
  visitor-writable surface whose free text persists to fleet's own Postgres**
  — a new processing activity, in a new storage location, with its own
  retention question and its own DSR surface (the RoPA's erasure path is
  content search *over the prompt log*, `ropa:145-147`, and never reaches a
  case row). Two scope facts, read before asserted: **ADR-0035 D6 is the
  prompt-log regime**, defined per request *to a published LLM route*
  (`0035:586,593-595`) — case text falls outside it, and D6's premise ("the
  only PII surface of the demo is what visitors type", `0035:588-590`, where
  that typing lands in the prompt log) goes stale-as-stated the day fleet
  publishes Tab I; whether D6 takes a pointer or an amendment is **ADR-level
  and only surfaced here** — a PLAN cannot amend an Accepted ADR. The
  template (`docs/conventions/partner-ropa-lite.md:3-5`) is per-dataset by
  construction and needs **no** change — the new dataset takes its own
  populated instance or a new section of the demo instance, Cray's
  structuring call as controller. One narrowing note so the scope stays
  exact: LOCKED-5 adds **no** visitor identity to the audit trail — the
  persona `person_id`s are synthetic shared identities and the gate email
  stays vendor-side — so the new activity is the case free text, not the
  persona mechanism. One sharp edge to hand Cray with the update: a case that
  drives a governed run enters the tamper-evident audit chain — the structure
  whose erasure the demo RoPA itself says cannot be promised
  (`ropa:112-115`) — so the case-text DSR answer is structurally different
  from the prompt log's, and only Cray can set it. 🔴 **The RoPA is Cray's
  artifact — this PLAN authors none of it** (the same author boundary this
  PLAN holds against portal-repo files); the PLAN's obligations are AC-11's
  bring-up gate and this clause's precise statement of what changed, so Cray
  can update in one pass. *Why Cray:* this is an interpretation of two
  governance artifacts' scopes — precedence calls are the constitution's to
  make, not a drafter's (CLAUDE.md §1) — and the consequence clause's duty
  lands on Cray personally, as controller.
- **SD-2 — Does s218 fire OQ-3, and what is the deployment order?** Three
  independent axes are in play: **card order** (LOCKED-2: fleet leftmost),
  **system number** (ADR-0036 D4: energy #1, procurement #2, fleet #3 "when
  Cray triggers it" — OQ-3: "Cray's trigger, not a schedule"), and
  **deployment order** (unruled). Cray said (s218) they expect to deploy the
  portal plus BOTH remaining verticals — this PLAN treats that as intent, and
  asks explicitly: **(a)** does it constitute OQ-3's fleet trigger? **(b)**
  bring-up order: system-number order (procurement then fleet) vs
  card/narrative order (fleet first)? **Recommendation:** (a) yes, confirm it
  fired — the shape is fixed by D2/D5, only the go was open; (b)
  system-number order (procurement then fleet) — upgraded reasoning
  (amendment round, 2026-08-10): not because procurement is the smaller step
  (a cost argument, and the weakest support available), but because it
  **decomposes two independent risks** — the *arrangement* risk (two systems
  on one shared host for the first time: headroom, per-project network
  isolation, the first live exercise of AC-4) and fleet's *feature* risk (the
  new DB posture, persona keys, the declared view sets, the Tab-H seed).
  Procurement proves the arrangement while touching none of fleet's new
  machinery — so if fleet later breaks, the broken axis is already isolated.
  Deployment order is invisible to visitors; card order is not; the two need
  never agree. **The variable that actually decides it — calendar knowledge
  only Cray holds, so it is asked, not assumed:** is there a near-term demo
  commitment? If anyone is being shown the portal within weeks, **fleet-first
  wins outright** — fleet is the leftmost card and the pitch, and the
  flagship should not queue behind a system that is not the story. The ruling
  should state which case holds. *Why Cray:* OQ-3 reserves the trigger to
  Cray by name; sequencing spends Cray's §8 host budget — and now the demo
  calendar, which neither drafter nor reviewer can see.
- **SD-3 — The three published tab sets + each system's default tab.**
  **Recommendation** (Cray types the sets; step 2's mechanism takes any):
  `oct-energy` — unchanged `A,B,C,D,F` (default A); `oct-fleet-maintenance` —
  `A,C,F,H,I,J` (default A): Cray's six favourites minus E (its narrative
  moves portal-side, LOCKED-3) **plus F, a drafter addition flagged as such**
  — the ladder the personas climb is *read* in Procedures, and hiding it
  weakens the refused-then-granted beat. `oct-procurement` — **ruled JOINTLY
  with SD-4's procurement sub-question: one decision, not two** (amendment
  round, 2026-08-10 — the pair can otherwise be ruled inconsistently, and one
  combination produces a dead control: a visible waiting approval a visitor
  cannot act on reads as *broken*, worse on the public surface than absence —
  exactly ADR-0032 D5 territory). ⚠️ **The original draft's `G,F,H` row was
  wrong on disk and is corrected here:** Tab H's backend is Postgres-served —
  PLAN-0100's C-3 struck the runs rows for exactly the DB-less posture
  (`0100:896-899,921-928`), and the waiting run H would display is written
  through `async_session` (`main.py:334-357`; pinned off and doubly inert on
  a DB-less system, `published.env:66-72`) — while LOCKED-1 keeps procurement
  DB-less. H on procurement was never merely persona-blocked; it is
  **storage-blocked**. **The joint options, explicit:** **(i)** procurement
  gets the persona mechanism **and** a Postgres — available only as Cray's
  own revision of LOCKED-1's typed "procurement stays DB-less", and it makes
  a second system tell an approval story, diluting D4's one-clean-story
  principle; **(ii — recommended, agreeing with Code's lean and strengthening
  it with the storage fact)** H drops from procurement's set: `G,F`,
  **default G** (its Tab A is structurally blank — empty `stream_events` by
  design, `published.env:23-26` — so it must not land there), anonymous
  read + hero, no personas — the governed hero *is* procurement's story
  (ADR-0036 D4); the approve beat is fleet's. ⚠️ Folded-in consequence to
  rule with the fleet set: fleet publishing **C** makes a **second assisted
  system** sharing one Ollama — a real premise change to ADR-0036 D5's
  wording, but **measured-mild**: every system serves the same model, so the
  eviction-thrash hazard is absent (Step 4's aggregate bullet carries the
  measurement, date, and tripwire); posture stays "1 per system, revisit at
  contention" unless Cray says otherwise. *Why Cray:* PLAN-0100's SD-1
  precedent — "which tabs the public ever sees" is Cray's call; the
  six-favourites list was a preference statement, not a typed set; and
  option (i) touches Cray's own typed LOCKED-1.
- **SD-4 — Persona-key delivery UX.** How does a visitor's browser get their
  chosen persona's key? **(a)** keys printed in the PIN email / portal page;
  visitor pastes — zero code, but the paste kills the cold visitor's first
  ninety seconds, and the key travels in an email body. **(b — recommended)**
  a published-profile-only persona picker: three buttons; raw demo keys held
  in a host-env variable (never git — AC-6) and served to Access-passed
  visitors only. Honest cost of (b), stated: `auth.py` deliberately holds
  digests, never raw keys (`auth.py:1-7`) — (b) introduces a demo-only
  raw-key env var beside that design, mitigated by naming (`DEMO_*`),
  published-profile-only routing, and README warnings that real keys must
  never be placed there. The keys' protective value is Access + the audit
  trail, not secrecy from the visitor — the visitor is *supposed* to hold
  one. **Procurement sub-question — ruled jointly inside SD-3's procurement
  row, never independently** (amendment round, 2026-08-10): the joint options
  and the dead-control hazard live there. An SD-4-only "yes" against an SD-3
  set without H buys personas with nothing to approve; an SD-3 "H" against an
  SD-4 "no" shows a control nobody can use — and the storage fact recorded in
  SD-3 makes H itself a LOCKED-1 question. One ruling covers both. *Why
  Cray:* trust posture + visitor UX on the public surface — ADR-0032 D5
  territory, and no oracle catches a wrong first impression.
- **SD-5 — Fleet Tab H first paint: seed vs visitor-drives-it.** **(a —
  recommended)** seed one waiting run at boot (procurement's exact contract,
  `main.py:330-357`) **and** keep the visitor path — H is never empty, and a
  visitor still watches their own Tab-I case enter the loop; cost: one seed
  function + fixture. **(b)** visitor-only — purest whole-loop story, but Tab
  I becomes load-bearing for H, and a visitor who opens H first sees an empty
  monitor at the exact moment the demo must not look dead. *Why Cray:* it is
  a call about what a cold visitor sees in the first minute — demo content,
  not engineering.
- **SD-6 — Dev-console Tab E's fate.** LOCKED-3 moved its *narrative*
  portal-side; the *surface* in the dev console is a separate call.
  **Recommendation: keep it in dev** — it is the intake surface for
  design-partner sessions, and it costs the published surface nothing (E is
  already profile-excluded). If Cray rules excision instead, that removal is
  its own scoped change walked with `tools/excision_scope.py` first — not a
  rider on this PLAN. *Why Cray:* deleting a working surface is a product
  call; the dispatch names it Cray's explicitly.
- **SD-7 — Bilingual depth, the EN renderings of the Thai roles, and the
  CTA.** **Recommendation:** bilingual = the card copy + persona disclosures
  only (full UI i18n is out of scope); proposed EN renderings for Cray to
  accept or replace — ช่างใหญ่ → "Head Mechanic", ผจก.เดินรถ → "Fleet
  Operations Manager", เฮีย — เจ้าของกิจการ → "the Owner"; CTA ask —
  recommendation: a reply-to-the-operator ask ("want this on your data — one
  KPI, zero integration to start"), consistent with the demo→pilot wedge
  (ADR-0032 D1) — exact wording Cray's. *Why Cray:* tone and rendering have
  no oracle (dispatch §4: conservative, mark uncertainty); the CTA is the
  business ask itself.

## Verification

- **Offline gate (the gate):** full CI scope on the feature branch — `ruff
  check .`, `ruff format --check .`, `mypy --strict services/`, the full test
  suite — including the new per-system guards, the boot-refusal test, and the
  AC-7/AC-8 scenario tests (real seams, no mocks; DB-backed ones run against
  the per-checkout test DB).
- **Non-vacuity probes (recorded in the PR):** AC-4's planted network
  collision, AC-5's planted two-label file, AC-1's planted unknown view key —
  each shown RED from a `/tmp`-restored copy, then green.
- **Live evidence (not a gate, minimized, §8-gated):** per-system bring-up
  checks in Step 10 — keyed/keyless `/whoami`, the rendered tab set, allowlist
  probes — recorded per system.
- **Boundary self-check before the closeout:** Grep proves
  `PUBLISHED_EXCLUDED_VIEWS` gone; the AC-5 guard proves no committed roster;
  a final review confirms no step created or named a portal-repo file.

## References

- ADR-0036 — D1 scope ruling; D2 vertical-as-system + label convention +
  registry rule (`0036:149-155`); D3 non-goal record; D4 system numbering +
  hero drop + UI corollary; D5 per-system profiles, duplication posture,
  network isolation, aggregate LLM posture; D6 this PLAN's scope list;
  OQ-1/2/3.
- ADR-0035 (via 0036's citations) — D1(3) domain-ignorance; D4-as-amended
  system property; acceptance shape; P12; D7 tenancy; Implementation Note 1.
- PLAN-0100 (`docs/plans/done/0100-exposure-published-demo-surface.md`) —
  Step 8 artifact; SD-1 ruling + scope note (`:1895-1932`); the H route census
  (`:1905-1919`).
- Code, spot-re-verified this session: `services/api/static/assets/app.js:12-74,129`
  · `services/api/static/assets/api.js:37` · the 11-site `isPublished()`
  census (8 files) · `services/api/config.py:205-224` ·
  `deploy/published/{published.env,docker-compose.yml}` ·
  `services/api/auth.py:1-22` · `services/api/main.py:320-391` ·
  `verticals/fleet_maintenance/procedures.yaml:102-119` ·
  `verticals/fleet_maintenance/data_adapter/__init__.py:73-84` ·
  `verticals/energy/procedures.yaml` (zero `principal` occurrences; positive
  control passed) · `tests/deploy/` path targets.
- Compliance (amendment round, 2026-08-10):
  `docs/compliance/ropa-published-demo.md` — the demo RoPA instance, DB-less
  as written (`:64-70` stored set · `:100` retention · `:112-115` the
  audit-chain erasure boundary · `:145-147` the prompt-log-scoped DSR search)
  · ADR-0035 D6 (`0035:586-629` — the prompt-log regime, LLM-route-scoped)
  · `docs/conventions/partner-ropa-lite.md:3-5` — per-dataset template, no
  change needed.
