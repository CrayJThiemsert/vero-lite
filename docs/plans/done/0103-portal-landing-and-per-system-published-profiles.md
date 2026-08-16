# PLAN-0103: The multi-vertical demo portal — vero-lite's side: per-system published profiles + the landing/framing content spec

**Status:** Complete — 2026-08-16 (session 234). All 11 ACs closed. The last two
were AC-10 and AC-11, both discharged by fleet's bring-up as published system #3
under Cray's typed §8 go; `deploy/published/` holds exactly three systems and all
three are live. Closeout record:
`docs/logs/2026-08-16-plan0103-step10-fleet-bring-up.md`.
**Owner:** Claude Code (execution) · Cray (SD rulings, every §8 go, all copy/tone calls)
**Created:** 2026-08-09
**Related ADRs:** ADR-0036 (D6 names this PLAN — its scope list is binding here),
ADR-0037 (**Accepted** — ratified 2026-08-10, s218; the SD-1-ruled
persistence-posture ADR; gated **fleet's DB half only** — see Step 4's gate
map, whose gate is now satisfied), ADR-0035 (portal arrangement — extended,
never touched), ADR-0032 (D5 positioning vocabulary), ADR-0026 (procurement
principals), PLAN-0100 (`deploy/published/` is the template artifact this PLAN
parameterizes — built on, never replaced), PLAN-0095 (the image every system
boots), PLAN-0096 (Tabs I/J), PLAN-0075 (cumulative roles — the approve-down
beat).

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
>
> **Rulings round (2026-08-10, rulings typed by Cray in session 218):** every SD
> slot below now carries Cray's typed ruling. SD-1's ruling — **a new ADR is
> required** — overruled the drafter+Code recommendation and is executed as
> **ADR-0037** (Proposed), which gates **fleet's DB half only**; Step 4's gate
> map states the parallelism so nobody stalls procurement. Consequences folded
> through Steps 2/4/5/6/7/8/10 and ACs 3/8/11. Separation still **INTACT**.
>
> **Correction round (2026-08-10, session 220, same drafter — Cray-approved
> dispatch):** four on-disk corrections, each re-verified against the code this
> session, none touching a step's scope, the AC set, or any ruling: Step 3's
> audit-target list (`was an error` — carried unfixed since the step ran,
> s219/PR #1111), the operate-demo seed-gate citation (`superseded by new
> info` — re-cited by branch, not line), AC-4's compose path + the standing
> instruction Step 4b has since resolved (`superseded by new info`), and one
> new **unruled** slot, SD-8 — the Tab-G Act-card coupling Step 5 exposed.
> Separation still **INTACT**.
>
> **Record round (2026-08-11, same drafter — Code dispatch, every claim
> re-verified on disk this session):** Step 1's answer recorded — Cray ruled
> (typed, s221): **no portal REPO will be created**; the portal and its landing
> surface still exist, configured in the Cloudflare dashboard, and only a
> separate git repository was ruled out (the full form is mandatory — the
> shorthand "no portal repo" misreads as "no portal"). AC-8 and AC-9 ticked
> against on-disk evidence (the fleet boot seed + the delta-asserted
> visitor-path scenario module; the three card-copy files + the AC-9 guard +
> the `docs/logs/` entry). No ruling, scope, step, or SD slot changed; SD-8
> remains unruled. Separation still **INTACT**.
>
> **Step-10 record round (2026-08-11, session 222, same drafter — Code
> dispatch, every claim re-verified on disk this session):** procurement's
> bring-up — published system #2, the first Step-10 execution — recorded
> against Step 10 and AC-10, citing the committed execution log by path
> rather than restating its evidence. AC-10 explicitly **stays open** (a
> per-bring-up obligation; fleet outstanding, AC-11-gated); one
> delivery-medium deviation from Step 10 item (2) recorded per Step 1's
> s221 answer; one live input appended to SD-8's slot, which **remains
> unruled**. No AC ticked, no ruling or scope changed, no Status change.
> Separation still **INTACT**.
>
> **Step-6 record + AC-closure round (2026-08-12, session 225, same drafter —
> Code dispatch; every on-disk claim re-verified this session by opening the
> cited file; run / PR-body / git-history facts are Code's 2026-08-12
> verifications against `main` = `445d18a`, attributed inline):** six ACs
> ticked against on-disk evidence (AC-1/2/3/4/5/7); AC-6 deliberately left
> open with its unmet clause named — no test anywhere guards
> `UI_DEMO_PERSONA_KEYS` out of any committed file, and the committed-env
> `API_KEYS` guard still covers energy only. Two corrections carried: AC-7's
> ladder premise (`was an error` — the DOA ladder that refuses วิรัช was on
> disk before the AC was written) and AC-1's literal grep closure
> (`superseded by new info` — the shipped oracle is comment-stripped,
> deliberately stronger than the AC's phrasing). Step 6's execution recorded
> under its step (PR #1138). One freshness correction carried across the file
> (`superseded by new info` — true when written, never refreshed): ADR-0037
> is **Accepted** on disk (`0037:3`, ratified by Cray 2026-08-10, s218), and
> the header's Related-ADRs line, Step 4's gate-map bullet, SD-1's ruling
> stamp, and the References entry called it "Proposed" — each now carries the
> Accepted status, the gate marked satisfied; the dated 2026-08-10
> rulings-round paragraph above keeps its original "(Proposed)" as a
> historical record, per this block's own convention for past rounds. No
> ruling, scope, step, or SD slot changed; no Status change. Separation still
> **INTACT**.
>
> **AC-6 closure round (2026-08-12, session 225 — the same drafter's second
> edit that day; Code dispatch; every on-disk citation re-verified this
> session by opening the cited file; PR / merge / probe / gate facts are
> Code's 2026-08-12 verifications against `main` = `0c1be0f`, attributed
> inline):** AC-6 ticked — closed **as code**, exactly as its partial record
> demanded: the per-profile guard
> `test_ac6_no_profile_commits_a_key_credential` shipped in PR #1140. The
> partial record is kept verbatim under a superseded-status marker
> (`superseded by new info` — true when written, earlier that same day; the
> guard it named missing now exists) because it is the record of why the AC
> was open, not debris. One typed Cray ruling (s225) recorded in the closure
> block: a REQUIRED interpolation is **not** accepted for the named key
> secrets — embedded in the guard's code, cited by this PLAN. No other AC
> changed state; no ruling, scope, step, or SD slot changed; no Status
> change. Separation still **INTACT**.

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

- [x] **AC-1 — the hardcode is dead, replaced by a declared set.**
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
  _[Closed 2026-08-12 — with one correction to this AC's literal closure
  condition, `superseded by new info`: a raw grep under `services/api/static/`
  returns **1 match today, not 0** — `app.js:36`, comment prose explaining
  what replaced the constant (a second such comment sits at
  `services/api/config.py:276`, outside this AC's stated path). Both are
  comments; live code carries zero mentions anywhere. The implementation kept
  the historical prose on purpose, and the shipped oracle is deliberately
  **stronger** than this AC's phrasing:
  `tests/api/test_ui_profile.py::test_the_n1_exclusion_constant_is_gone_from_every_asset`
  (`:446`) scans every `services/api/static/assets/*.js` through
  `strip_js_comments` — its own docstring records that a raw substring scan
  "reddens against a correct file for the crime of documenting itself".
  Corrected closure condition, so a future session running the literal grep
  does not read a 1-match result as an unclosed AC: **no live-code mention,
  comment-stripped**; the two comment sites above are the surviving, intended
  mentions. Rest of the AC, closed as written: the replacement setting is
  `ui_published_views` (`services/api/config.py:274-279` — the Step 2 block
  naming what it replaced); unknown key fails boot
  (`test_ui_profile.py:509`); a published page with no declared set refuses
  to render (`:571`); the two carriers agree (`:134`); the ten-tab census
  agrees in both of its homes (`:471`); the bit-identical clause is held as a
  property against the historical energy pin (`:338-348`, asserted at
  `:490`). Shipped in PR #1109 (`70e5b36`, merged `d162770`).]_
- [x] **AC-2 — all 11 `isPublished()` consumers accounted for.** The step's PR
  body carries a per-site disposition table for the full census — `api.js:37`
  (the predicate), `app.js:70,129`, `view-story.js:821,902`,
  `view-anomaly.js:112`, `view-hero.js:606`, `view-procedures.js:221,669`,
  `view-flow.js:184` — classified **tab-set** (re-sourced from the declared
  set) vs **profile-behaviour** (stays on `isPublished()`), with the census
  **re-run by grep at execution** (this PLAN's snapshot is not the oracle; a
  12th consumer added since s218 gets its own row). Every published-profile
  branch that becomes *reachable for the first time* on a new system (in
  practice exactly one: Tab G's published branch on procurement — dead code
  under energy, which filters G out; under fleet's tab set the H/I/J views —
  `view-monitor.js` / `view-case.js` / `view-export.js` — carry **no**
  published branch to go live, and correctly so: fleet has a Postgres and
  Step 5 admits their routes on fleet's own allowlist — see Step 3's s220
  correction note) is exercised by a test on that system's vertical fixture.
  Evidence: the table + the named tests.
  _[Closed 2026-08-12 — both clauses. Clause 1: the per-site disposition
  table lives in **PR #1109's body** — ⚠️ off-disk evidence, named honestly
  so nobody greps the repo for it: retrieve it as PR #1109 (verified by Code
  2026-08-12 via `gh pr view 1109 --json body`); it carries nine disposition
  rows with exactly one site classified tab-set (`app.js:70`) and the rest
  profile-behaviour, plus the record that one census entry was a
  `PUBLISHED_EXCLUDED_VIEWS.indexOf` line rather than an `isPublished()`
  site. Cited, not restated — two copies of a table are two chances to
  disagree. Clause 2: discharged by Step 3 (s219, PR #1111) and on disk as
  `tests/api/test_published_newly_reachable.py` — Tab G's published branch,
  the one genuinely newly-reachable surface, is exercised by
  `test_tab_g_published_branch_gates_both_toggles` (`:123`) and
  `test_the_event_wrapper_is_called_only_behind_that_branch` (`:146`), with
  the per-system hero behaviour driven on procurement's and fleet's own
  fixtures (`:91`, `:104`); the module's header carries the corrected audit
  table matching Step 3's s220 note.]_
- [x] **AC-3 — three committed per-system profiles.** `deploy/published/`
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
  `tests/deploy/test_verify_tunnel_credentials.py:31-32`. ⚠️ Rulings
  fold-in: fleet's profile is the **ADR-0037-gated half** (Step 4's gate
  map); energy's move and procurement's authoring are ungated and land
  first. AC re-read at the fold-in: still correct as written otherwise.
  _[Closed 2026-08-12 — the three profile directories are on disk
  (`deploy/published/{oct-energy,oct-procurement,oct-fleet-maintenance}/`),
  each carrying the five committed artifacts, guard-asserted per profile:
  `tests/deploy/test_published_profiles.py::test_a_profile_carries_every_committed_artifact`
  (`:211`, over `_REQUIRED_ARTIFACTS` `:201-207`). Fleet-only database,
  asserted in both directions:
  `test_only_a_granted_profile_declares_a_database` (`:410`, over
  `_DB_GRANTED` `:406`). The hardcoded-path clause:
  `tests/deploy/test_published_compose.py:58-59` now reads
  `_DEPLOY_ROOT = Path("deploy/published")` /
  `_DEPLOY = _DEPLOY_ROOT / "oct-energy"`. PRs: #1113 (energy moved), #1114
  (procurement authored), #1116 (fleet authored — the ADR-0037-gated half;
  the gate is satisfied on disk: ADR-0037's Status line reads **Accepted**,
  ratified 2026-08-10, s218).]_
- [x] **AC-4 — per-system network + project isolation (the ADR-0035 reopening
  tripwire).** No two per-system compose files share a Docker network or a
  compose project name. _[Corrected s220, `superseded by new info`: as
  drafted, this AC cited the pre-Step-4a compose at
  `deploy/published/docker-compose.yml` — its fixed network `name: vero_oct`,
  its project `name: vero-published`, and the warning block deferring the
  choice to this PLAN. Step 4a moved energy's compose to
  `deploy/published/oct-energy/docker-compose.yml`, and Step 4b **resolved**
  the standing instruction those lines carried rather than leaving it open:
  the fixed network `name:` is **dropped** (compose scopes each network under
  its own project), and the project `name:` is the **profile directory's
  name** (`oct-energy` et al.) — a rule, not a coincidence, per the compose
  header.]_ Evidence: `tests/deploy/test_published_profiles.py` parses every
  per-system compose file and asserts (a) project name == profile directory
  name (`test_ac4_the_project_name_is_the_directory_name`) and
  pairwise-distinct project names
  (`test_ac4_no_two_profiles_share_a_project_name`), (b) no profile declares
  a fixed network `name:` at all
  (`test_ac4_no_profile_declares_a_fixed_network_name` — per-project scoping
  makes a shared network structurally impossible), plus globally-unique
  container and volume names; non-vacuity probe: plant a colliding `name:`,
  see RED.
  _[Closed 2026-08-12 — all four named guards on disk in
  `tests/deploy/test_published_profiles.py`:
  `test_ac4_the_project_name_is_the_directory_name` (`:273`),
  `test_ac4_no_two_profiles_share_a_project_name` (`:288`),
  `test_ac4_no_profile_declares_a_fixed_network_name` (`:301`),
  `test_ac4_no_two_profiles_share_a_container_or_volume_name` (`:318`).]_
- [x] **AC-5 — no shadow registry, still domain-ignorant.** A guard test
  asserts: no committed file outside a per-system profile directory mentions
  **two or more** distinct `oct-*` system labels (`0036:142-147` label
  convention); each profile directory mentions **only its own** label; the
  apex domain appears nowhere in the repo (ADR-0035 D1(3) via `0036:149-155`).
  Non-vacuity probe: plant a two-label file, see RED.
  _[Closed 2026-08-12 — all three clauses guarded on disk. Labels:
  `tests/deploy/test_published_profiles.py::test_ac5_no_file_outside_a_profile_lists_two_system_labels`
  (`:629`) and `::test_ac5_a_profile_mentions_only_its_own_label` (`:658`).
  Domain:
  `tests/deploy/test_published_compose.py::test_no_unknown_domain_appears_in_the_deploy_docs`
  (`:499`), scanning the whole `deploy/published/` tree plus the
  published-demo runbooks — the surfaces where a real hostname wants to be
  pasted, per that module's own scope comment (`:50-57`).]_
- [x] **AC-6 — secrets stay out of git.** `API_KEYS` and any raw persona-key
  material appear in **no committed file**: the per-system env-parse tests
  assert each committed env file's key set excludes `API_KEYS` (and the
  persona-key variable if SD-4 introduces one); `detect-secrets` stays green;
  each per-system README documents host-env-local provisioning (the compose
  bare pass-through pattern, `docker-compose.yml:26-47`).
  _[Partial record, 2026-08-12 — **status superseded later the same s225
  day, `superseded by new info` (every claim below was true when written;
  the guard it demanded now exists — see the closure block after this one).
  The AC closed as code, exactly as this record's closing sentence required;
  the record itself stays verbatim, because it is the record of WHY this AC
  was open** — deliberately NOT ticked: the parenthetical
  above is now a LIVE obligation, and its guard does not exist. SD-4's ruling
  (b) (s218) introduced the persona-key variable — `UI_DEMO_PERSONA_KEYS` —
  and the s224 credential ruling (option (a); Step 6's record) made it a
  raw-key store served to the browser. What holds on inspection today
  (verified 2026-08-12): no committed file carries raw key **values** —
  `deploy/published/oct-fleet-maintenance/published.env:88-90` states the
  variable's deliberate absence and why; `docker-compose.yml:69` declares it
  as a bare host pass-through (rationale `:52-68`); `README.md:115-140`
  documents host-env-local provisioning including the generation recipe;
  `detect-secrets` green (CI). What is UNMET — the automated half of this
  AC's own wording: (1) **no test anywhere asserts `UI_DEMO_PERSONA_KEYS` is
  absent from any committed file** — the only two test files naming it
  (`tests/api/test_ui_profile.py`, `tests/api/test_fleet_persona_scenario.py`)
  CONSUME the setting; neither guards a committed file. (2) The `API_KEYS`
  env guard covers energy only:
  `tests/deploy/test_published_compose.py::test_ac4_no_secret_is_committed`
  (`:335`) checks its three forbidden names against `_ENV`, which resolves
  under `oct-energy/` (`:58-61`); the module's own comment (`:43-57`) records
  the non-parametrization as deliberate-and-temporary for a stated reason —
  "procurement's and fleet's are authored in the next step" — that EXPIRED
  when #1114/#1116 shipped. (3) The per-profile module's credential guard
  (`test_published_profiles.py::test_no_profile_commits_a_database_credential`,
  `:457`) scans only `PASSWORD`/`DATABASE_URL` values (`:454`) — no
  `API_KEYS` or persona-key coverage. Net: fleet's and procurement's
  committed env files are unguarded against exactly this AC's named secrets,
  and fleet is precisely the profile that introduced the raw-key variable.
  Closing this is a small CODE change (extend the per-profile guard), not a
  governance one — recorded here so it gets closed as code, never ticked as
  prose.]_
  _[Closed 2026-08-12, later the same s225 session — as code, exactly as the
  partial record above demanded, never as prose. The missing guard now
  exists:
  `tests/deploy/test_published_profiles.py::test_ac6_no_profile_commits_a_key_credential`
  (`:516`), parametrized over every discovered profile via the module's own
  `_profiles()`/`_profile_ids()` (`:515`), over both named secrets in
  `_SECRET_ENV_NAMES` (`:494` — `API_KEYS`, `UI_DEMO_PERSONA_KEYS`). Shipped
  in PR #1140 (`f936e55`, merged as `0c1be0f`; 2 files, +109 — the PR /
  merge / probe / gate facts in this block are Code's 2026-08-12
  verifications against that `main`). The record's three unmet items,
  discharged in order: (1) the persona-key variable is now guarded out of
  every committed profile file; (2) coverage is per-profile — the module
  choice is written in the guard's own docstring (`:525-533`), cited not
  restated: `test_published_compose.py::test_ac4_no_secret_is_committed`
  keeps its deliberate energy-only `_DEPLOY` pin (`:58-59` — that module's
  scope reasons remain valid *for it*), while the profiles module already
  reddens when a NEW profile arrives uncovered
  (`test_every_discovered_profile_has_an_expected_allow_set`, `:184`) — the
  property this AC actually needs; (3) the DB-credential guard's
  `PASSWORD`/`DATABASE_URL` scope stands unwidened — the key secrets take
  their own guard with two DIFFERENT assertions, because the two carriers
  have opposite correct shapes: in `published.env` (loaded wholesale by
  `env_file:`) any real assignment of a secret name is the violation,
  parsed through the comment-stripping `_read_env_file` (`:497`) since the
  names legitimately appear there in comments — a mere-mention guard would
  redden a correct file; in `docker-compose.yml` both names MUST be
  declared bare for the host pass-through to work at all (their absence is
  its own bug —
  `test_published_compose.py::test_the_app_can_actually_receive_api_keys_from_the_host`,
  `:345`), so there the violation is the same name carrying a value.
  🔴 **RULED (Cray, typed, s225) — a posture, embedded in the guard:** a
  REQUIRED interpolation (`${API_KEYS:?…}`) is **not** accepted for these
  secrets, even though the sibling DB-credential guard
  (`test_no_profile_commits_a_database_credential`, `:457`) demands exactly
  that shape — the divergence is deliberate: the compose files argue
  against that form for `API_KEYS` in their own comments
  (`deploy/published/oct-energy/docker-compose.yml:53-59`), and a guard
  accepting a shape the file itself rejects has stopped enforcing the
  file's design. The full rationale — including which line must change if
  the posture ever does — is committed above the guard's assertion loop
  (`test_published_profiles.py:556-564`), cited not restated. Non-vacuity,
  each clause independently (Code, 2026-08-12; planted from a `/tmp` copy,
  restoration verified byte-identical, green after): a planted
  `UI_DEMO_PERSONA_KEYS` assignment in fleet's `published.env` reddened
  clause 1 with its own assertion; a value on fleet's bare compose
  pass-through reddened clause 2 with its own assertion. The AC's other
  clauses, re-verified 2026-08-12 rather than assumed (Code):
  `detect-secrets` green on the shipping commit with `.secrets.baseline`
  unmodified; all three per-system READMEs document host-env-local
  provisioning — `oct-energy/README.md:82-84`,
  `oct-procurement/README.md:41,53` (this system expects no `API_KEYS`
  consumer, consistent with SD-8's live-input note),
  `oct-fleet-maintenance/README.md:98-143` (including the key-pair
  generation recipe). Gate on the shipping commit (Code, 2026-08-12): 4028
  passed / 8 skipped — the delta over the prior suite is exactly the three
  per-profile cases — `mypy --strict services/` clean over 134 source
  files, ruff check + format clean. PR #1140's second file, named so its
  diff is never read as an unexplained rider: `.gitignore` gained
  `.claude/launch.json` — an untracked-but-uncovered file naming
  `UI_DEMO_PERSONA_KEYS`, one `git add -A` away from a public-repo commit,
  the same file class this guard now catches. Not AC-6 evidence (the AC
  binds committed files, and that file was never committed); its rationale
  is committed in `.gitignore`'s own comment block above the entry, cited
  not restated.]_
- [x] **AC-7 — the persona loop is real (the demo's core moment).** A scenario
  test drives fleet's **real** procedures + auth + audit stack — no side
  mocked (CLAUDE.md §8 scenario rule) — with the three authored principals
  (`verticals/fleet_maintenance/procedures.yaml:102-111`): `req-mechanic-tom`
  is **refused** an approval above his tier; `appr-fleet-manager-wirat`
  approves within tier; `appr-owner` approves **down** (cumulative roles,
  PLAN-0075 Policy B); each decision lands in the real audit trail under the
  `person_id` that acted. Evidence: the named scenario test, green, with the
  refusal asserted **by name**, not by generic 4xx.
  _[Closed 2026-08-12 — with a correction to this AC's own middle clause,
  🔴 `was an error` (CLAUDE.md §6): "`appr-fleet-manager-wirat` approves
  within tier" was **false when written**. The engine refuses him —
  `tier_role_mismatch … routed to 'appr-owner'` — because the DOA ladder
  (`verticals/fleet_maintenance/procedures.yaml:290-293`: ฿0 ช่างใหญ่ ·
  ฿5,001 ผจก.เดินรถ · ฿30,001 เจ้าของกิจการ) routes the hero repair's amount
  to the owner tier, above วิรัช's rung; the YAML's own comment block
  (`:280-286`) says so in words — the ฿48,000 breakdown "clears ฿30,000 and
  lands on the OWNER's desk". Classification evidence (git history, Code
  2026-08-12): `git log --since=2026-08-08 --
  verticals/fleet_maintenance/procedures.yaml` is EMPTY — the file last
  changed 2026-07-29 (`f7f85ef`), the tier block at `c4aca35` (PLAN-0096
  Step 1) — so the ladder that refuses him was already on disk when this AC
  was authored (s218, 2026-08-09). Nobody ran it. Same failure family as
  Lesson #0041: a claim restated instead of grounded, carried as fact. The AC
  nevertheless CLOSES, because what shipped is strictly STRONGER than what it
  asked for: two refusals from two **different** governance mechanisms (ต้อม
  refused by separation of duties; วิรัช refused by DOA tier routing) plus
  one grant (เฮีย holds the routed tier) — as the evidence module's docstring
  puts it, a suite showing only a granted approval passes with SoD deleted,
  and one showing only an SoD refusal passes with the ladder flattened. The
  correction is to this AC's premise about the ladder, never a weakening of
  its closure. Evidence: `tests/api/test_fleet_persona_scenario.py` (PR
  #1138) — `test_the_offered_keys_are_the_keys_that_authenticate` (every card
  the picker renders resolves through the real auth seam to the `person_id`
  printed on that card; bearer tokens are read out of the picker's own offer
  set, never declared by the test),
  `test_all_three_personas_meet_the_ladder_refused_refused_granted` (the SoD
  refusal asserted by name — `sod`/`distinct` in the response text — and the
  tier refusal asserting `tier`; never a generic 4xx), and
  `test_the_audit_trail_records_the_acting_persona` (the structured
  `actor_person_id` column asserted positively AND negatively, plus
  `run_started` attributed to ต้อม). No side mocked: the producer is
  `resolve_demo_personas` (the exact function `/meta` calls), the consumers
  the real `POST /procedures/{id}/run` + `POST /runs/{id}/gate/resolve`
  behind the real `get_current_principal`. Fresh run (Code, 2026-08-12,
  `main` = `445d18a`): 3 passed in 4.17s, DB-backed and NOT skipped — the
  module's own docstring holds that a skip is never satisfaction.]_
- [x] **AC-8 — fleet's first paint is not empty.** Under SD-5's **ruling (a)**
  (Cray, typed, s218 — seed one at boot **and** keep the visitor path), a
  fleet scenario test proves Tab H's backing read returns ≥ 1 waiting run at
  boot (today the seed rides `main.py` lifespan's `vertical == "procurement"`
  branch only — PLAN-0054 Step 6c; cited by branch, not line, per Step 7's
  s220 correction note — so fleet's H opens empty), **and** the visitor path
  still closes end-to-end: a case
  opened via Tab I's backend appears in H's list. Real seed → real routes →
  real DB (fleet has one, LOCKED-1); no mocks.
  _[Closed 2026-08-11 — both clauses on disk. Clause 1: the seed now rides
  the lifespan for fleet — `_seed_fleet_operate_demo` in
  `services/api/main.py` (called unconditionally, gated inside on
  `vertical == "fleet_maintenance"` + `settings.oct_demo_seed_operate`;
  procurement's exact contract: env-gated, fixed `DEMO_RUN_ID`,
  skip-if-present, fail-soft), proven by
  `tests/verticals/fleet_maintenance/test_operate_seed.py` (Step 7,
  PR #1122) — the "today … opens empty" clause above describes the
  pre-Step-7 state. Clause 2:
  `tests/api/test_visitor_case_to_monitor_scenario.py::test_a_visitor_case_lands_in_the_monitor_beside_the_seed_not_instead_of_it`
  (PR #1124) — asserted as a **delta plus a case-identity tie**
  (`run_link.case_id_of`) against `GET /runs` **with the seed present**,
  because the seed alone would satisfy a presence check; the same module's
  two sibling tests discharge ADR-0037 D2.7 (recorded there, 2026-08-11
  amendment pass). DB-backed, real seams, no mocks.]_
- [x] **AC-9 — the framing layer exists on both sides of the boundary.** Each
  per-system profile directory carries its bilingual card-copy file with both
  TH and EN sections present (guard-asserted structurally — section presence,
  not copy quality, which has no oracle); the portal-side assembly request
  (card order incl. LOCKED-2 fleet-leftmost, the relocated Tab-E narrative
  per LOCKED-3, the arrival narrative, CTA per SD-7) is delivered as a
  handoff whose path is recorded in a committed `docs/logs/` thin summary.
  Evidence: the committed card files + guard + the `docs/logs/` entry.
  _[Closed 2026-08-11 — all three evidence pieces on disk. Cards:
  `deploy/published/{oct-energy,oct-procurement,oct-fleet-maintenance}/card-copy.md`.
  Guard:
  `tests/deploy/test_published_profiles.py::test_ac9_the_card_copy_is_bilingual_and_structurally_complete`
  — TH/EN section presence + subsection parity, never copy quality. Log:
  `docs/logs/2026-08-10-plan0103-step8b-portal-assembly-request.md`, naming
  the parked handoff path
  (`.claude/handoffs/session-221/2026-08-10-2030-code-plan0103-step8b-portal-assembly-request.md`,
  gitignored). Per Step 8b's own no-repo sub-branch the request is
  delivered-and-**parked**; with Step 1's s221 answer the addressee is the
  dashboard-configuration work, not a future repo bootstrap. The CTA's exact
  wording — SD-7's one open sub-item — was typed by Cray and is committed
  verbatim in all three card files, per the same log.]_
- [x] **AC-10 — measured before multiplied, gated before touched.** MS-S1
  headroom is **measured and recorded** (numbers, method, date — Step 9)
  **before** any second system is brought up; every bring-up and the
  measurement session itself each have their own explicit Cray go (§8 —
  host-state changes, do-no-harm to co-tenant stacks). Evidence: the recorded
  measurement + per-action go records in the execution log.
  _[Partial record, 2026-08-11 — deliberately NOT ticked: this AC is a
  per-bring-up obligation and one of two bring-ups is done; one live system
  does not approximate "every bring-up". On record so far: the measurement
  session's go (typed, s221 — one go covering migration phase 2 and the
  Step 9 measurement;
  `docs/logs/2026-08-10-oct-energy-migration-phase2-and-step9-headroom.md`)
  and procurement's bring-up go (typed, s222, for that bring-up
  specifically, plus a second typed go for its ACL step;
  `docs/logs/2026-08-11-plan0103-step10-procurement-bring-up.md` — the full
  execution record; cited, not restated). The first clause held in both
  directions: headroom was measured (s221) before any second system
  existed, and the first two-system measurement (recorded in the s222 log)
  landed well inside Step 9's three-system projection — the first evidence
  the measurement was any good, not merely that it was taken. Outstanding,
  and exactly why the box stays empty: fleet's bring-up has not happened,
  requires its own typed go, and is gated on AC-11's RoPA (still `[ ]`).]_
  ✅ **CLOSED 2026-08-16 (s234) — the per-bring-up obligation is now
  discharged for every system in this PLAN's scope.** `deploy/published/`
  holds exactly three systems and all three are live; there is no fourth
  bring-up this AC is still waiting on. Fleet's own typed §8 go (Cray,
  2026-08-16) and its full execution record are at
  `docs/logs/2026-08-16-plan0103-step10-fleet-bring-up.md` — cited by path,
  not restated. Do-no-harm held against a baseline captured **before** the
  first host-state action: neither live sibling's container was restarted
  (`Up 5 days` / `Up 4 days` on both sides of the bring-up), and every
  co-tenant stack stayed `exited`.
  ⚠️ **One honest qualifier on the first clause, recorded rather than
  smoothed over.** The three-system measurement came in at **≈1.33 GiB**
  against Step 9's **≈0.95 GiB** projection. The overrun is not the third
  system — it is that Step 9 modelled containers **at boot**: the two
  siblings measured 208.9 / 85.4 MiB when cold and 637.6 / 530.8 MiB at
  steady state, while fleet's two-minute-old app sat at 88.8 MiB. The
  numbers, method and date were recorded as this AC requires; the method
  **under-models by roughly 3–6× per app container** and a fourth system
  should be projected against steady-state figures, not cold ones. At 4.3%
  of available memory this changes no decision today.]_
- [x] **AC-11 — the RoPA reflects fleet's posture BEFORE fleet is reachable
  (appended 2026-08-10, amendment round; precondition of Step 10's fleet
  bring-up, not a follow-up).** Before the fleet system's go: the
  RoPA covers the LOCKED-1 consequence: the new processing activity
  (visitor-typed case free text), its storage location (fleet's Postgres), its
  retention number, and its DSR path.
  ✅ **RESOLVED and DELIVERED s233 — this AC's target is no longer an open
  choice.** Cray ruled (typed, 2026-08-14) that the coverage takes a **sibling
  per-dataset instance**, and it was written and **adopted 2026-08-15**:
  **`docs/compliance/ropa-fleet-cases.md`** (on `main`, `2d9056c`), carrying all
  six required inputs plus five typed promise rulings. _[Corrected s233: this
  clause read *"`docs/compliance/ropa-published-demo.md` — or a sibling
  per-dataset instance, Cray's structuring call"* for a full session after that
  call had been made. It is corrected rather than deleted because the staleness
  had a measured cost — it pointed the writer at the wrong file.]_
  ⚠️ **AC-11 stays `[ ]` even so, and the remaining half is NOT this repo's to
  write:** its evidence is *"the updated RoPA on `main` **and** fleet's Step-10
  go record citing it **by path**"*. The RoPA half is now done; the **go record
  does not exist yet**, and cannot until Cray gives fleet's typed §8 go. Same
  shape as PLAN-0106's AC-7. 🔴 **Authorship boundary: the RoPA is Cray's artifact, in Cray's
  controller voice — this PLAN gates on it and supplies the change statement
  (SD-1's consequence clause); it authors none of the text** (mirroring the
  portal-repo file boundary). The change statement is tracked at
  `docs/compliance/ropa-change-statement-fleet.md` (moved out of a session
  scratchpad, s224) — the controller's **input**, not RoPA text; its
  existence closes nothing here. Evidence that closes it: the updated RoPA on
  `main` (authored by Cray; committed via Code's PR per ADR-009 D2) **and**
  fleet's Step-10 go record citing it by path. No test double can satisfy
  this AC: the gate is the committed artifact plus the go record, and a fleet
  bring-up without both is a Step-10 **stop condition**, not a warning.
  (Rulings fold-in: AC-11 is the first instance of the standing obligation
  ADR-0037 D2.1 proposes.)
  ✅ **CLOSED 2026-08-16 (s234) — both halves now exist and the ordering the
  AC exists to enforce held.** The RoPA half:
  `docs/compliance/ropa-fleet-cases.md`, adopted 2026-08-15, on `main` at
  `610369f`. The go-record half:
  `docs/logs/2026-08-16-plan0103-step10-fleet-bring-up.md`, whose "The go"
  section cites that RoPA **by path**, as this AC requires. **The RoPA
  preceded reachability by a day** — its own Status block says so in the
  present tense (*"The system it describes is NOT live; that is the point of
  adopting it now"*), which is the ordering evidence rather than a claim
  about it. ⚠️ The **authorship** departure this AC's artifact carries —
  drafted by Code at Cray's request, against D2.1's reservation to the
  controller — is disclosed on the RoPA itself and remains open as ADR-0037
  **SD-1**; closing this AC records that the artifact exists and gated the
  bring-up, and settles nothing about who may write the next one.

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

**ANSWERED — Cray, typed, s221; recorded here 2026-08-11.** 🔴 Stated in full
because the shorthand misleads: **no portal REPO will be created** — the portal
and its landing surface still exist; DNS routes, Access policies and the
landing surface are configured in the **Cloudflare dashboard**, each published
system on its own `oct-<vertical-id>` subdomain label; **only a separate git
repository was ruled out**. Evidence:
`docs/logs/2026-08-10-plan0103-step8b-portal-assembly-request.md` (the s221
record — 52 repos enumerated, no organisations, and the typed ruling). The
**"does not exist" branch is taken — permanently**: there is no future
bootstrap for parked requests to wait on. Consequence, as the Step-8b log
already carries it: ADR-0036 D2's two-artifact-per-system price is
**unchanged**, paid as dashboard configuration rather than repo files — so
Step 10's "portal-side artifacts exist" condition is a check against the
dashboard, not against a repo (`oct-energy` has run exactly that way since
s213 without a checkout). The branch text above says "OQ-4 fires (Cray picks
the domain then)" — that trigger is now dead; ADR-0035's OQ-4 carries a
2026-08-11 amendment replacing it with the live condition Cray named (the
domain itself stays out of this repo, ADR-0035 D1(3)). Sequencing, honestly:
Step 8b ran in s221 — the same session the answer was obtained and logged —
with its request drafted and **parked** per this branch's own instruction, but
this PLAN-side record lagged until 2026-08-11, missing the pass/fail's
before-Step-8b ordering. Step 10 has not run; the record lands before any
bring-up, which is the bound that matters operationally.

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
  blank (`published.env:23-26`; the s218 fact-pack's procurement note). The
  declared sets are now **ruled** (SD-3 — Cray, typed, s218): energy
  `A,B,C,D,F` default A · procurement `G,F` **default G** · fleet
  `A,C,F,H,I,J` default A.
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
for the first time on a new system. _[Corrected s220, `was an error` — carried
unfixed since the step actually ran (s219, PR #1111): the draft's audit list
here named "the monitor/procedures/flow published behaviours" as newly
reachable, and that was wrong on disk in every part. `view-flow.js` is
**Tab D** and `view-procedures.js` is **Tab F** — both tabs energy publishes
and always has, so their published branches were never unreachable — and
`view-monitor.js` has **no `isPublished()` call at all**.]_ The audited scope
as established when the step ran: **Tab G's published branch**
(`view-hero.js` — the one genuinely dead branch, because energy filters G out
entirely), and **Tabs H/I/J** (`view-monitor.js` / `view-case.js` /
`view-export.js`), which carry **no** published branch — an absence that is
*correct*, not a gap to fill: fleet, the only system publishing H/I/J, has its
own Postgres (LOCKED-1), and Step 5 puts those tabs' routes on fleet's own
allowlist, so their modules owe the published profile no special-casing. For
each branch that a new system's tab set makes reachable, add a test on that
system's fixture asserting the branch's behaviour against that system's
posture (AC-2's second clause).

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
  🔴 **ADR-GATED (SD-1 ruling — Cray, typed, s218):** fleet's persistence
  posture is legitimate only under **ADR-0037** (**Accepted** — ratified
  2026-08-10, s218; this bullet read "Proposed" until the s225 freshness
  pass, `superseded by new info` — the gate is SATISFIED, not pending) — the
  ADR merges before the related implementation PR (CLAUDE.md §8), and its D2
  obligations (RoPA-first, retention number, DSR path, in-app disclosure,
  isolation, tenancy, the D2.7 audit-chain measurement) attach to the grant.
  **Gate map — read this before stalling anything:** *gated on ADR-0037's
  ratification:* fleet's profile directory (this bullet + fleet's env),
  fleet's allowlist (Step 5), the fleet seed (Step 7), the fleet-DB scenario
  tests that ride those PRs (AC-7/AC-8), and fleet's bring-up (Step 10).
  *NOT gated — proceeds while ADR-0037 is in flight:* Steps 2–3 (the
  view-set mechanism and branch audit), `oct-energy`'s move, **procurement's
  entire half** (profile, allowlist, bring-up — it is DB-less and first in
  bring-up order per SD-2(b)), the persona-picker UI code (Step 6 —
  profile-generic; only its fleet key-provisioning waits for fleet's
  system), Step 8's content, and Step 9's measurement.
  ⚠️ **Not-gated is not the same as safe-to-schedule-first, and the
  persona picker is the one place the two diverge** (Code R2, 2026-08-10,
  ruling on a boundary call the drafter flagged): the classification above
  is correct — ADR-0037's subject is *persistence*, the picker's is
  *identity*, so no gate applies. But under the SD-3/SD-4 joint ruling
  **fleet is its only consumer** — procurement takes no personas and energy
  stays keyless — and fleet's approve surface needs the granted Postgres.
  So if ADR-0037 ratifies otherwise than proposed, the picker is orphaned
  work. Build it in parallel if convenient; do not build it *first*.
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
- **`oct-procurement`:** authored to the **ruled** SD-3 set `G,F` (default
  G) — the two hero reads (`/demo/hero/governance`, `/demo/hero/impact`)
  return **for this system only**; **no H routes** (the SD-3/SD-4 joint
  ruling (ii) dropped H, so `GET /runs`, `GET /runs/{id}`,
  `POST /runs/{id}/gate/resolve`, `POST /runs/{id}/cancel`,
  `GET /audit/verify` all stay off this system's table); DB-backed routes
  stay off (procurement is DB-less, LOCKED-1). Nothing else in this step
  assumed H for procurement — checked at the rulings fold-in.
- **`oct-fleet-maintenance`** (ADR-0037-gated — Step 4's gate map): the
  conscious per-route reversal of PLAN-0100's
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
- **Delivery UX — SD-4 RULED (b) (Cray, typed, s218):** the
  published-profile-only **persona picker**, backed by raw demo keys in a
  host-env var, never git. The **on-screen disclosure** ships with it,
  bilingual: *you are acting as \<persona\>; every decision is recorded in
  the audit trail under this name.* _[Implementation note, verified s224:
  the published-profile branch this requires does not exist yet in
  `view-monitor.js` — the file has zero `isPublished()` references, and its
  `authBar()` login form (free-text identity + password-type key input,
  `view-monitor.js:425-467`) renders unconditionally whenever Tab H mounts;
  invisible today (fleet is the only system publishing Tab H, per SD-3's
  ruled sets) and visible at fleet's bring-up.]_
- **Scope note (verified nuance):** membership enforcement arms only where the
  vertical *ships* principals (`auth.py:9-18`) — the persona layer is
  meaningful on fleet — and the persona layer is now **fleet-only by
  ruling**: the SD-3/SD-4 joint ruling (ii) gives procurement **no**
  personas (it ships principals per ADR-0026, but its published story takes
  none); **energy stays keyless**, exactly as PLAN-0100 left it
  (`published.env:8-12`).

Pass/fail: AC-7's scenario test — refused-then-granted across real personas,
audit rows by name.

**EXECUTED — 2026-08-12, session 224; recorded here session 225.** Shipped as
PR #1138 (`45d0107`, merged to `main` as `445d18a`): 15 files, +1062/−15 (the
PR's diffstat) — `services/api/demo_personas.py` (new: one resolver, called
from both the lifespan and `/meta`, resolving through the same
`_principal_index` auth uses so "the picker offers a persona auth would
refuse" is structurally impossible), `config.py`'s paired-provisioning
validation, the picker UI (`view-monitor.js`, `auth.js`, `view-hero.js`),
`services/engine/ontology_meta.py`, the AC-7 scenario module
(`tests/api/test_fleet_persona_scenario.py`), the Step-6 guard block in
`tests/api/test_ui_profile.py`, and fleet's three profile files. PLAN-side
record, so nothing surfaces later as drift:

- **Cray's two typed rulings (s224), recorded before the first line of code —
  restated here, not re-litigated:** Step 6 **layout = option A** (three
  persona cards, over a one-line dropdown); Step 6 **credential = option
  (a)** (raw demo keys declared to the browser, over a new published-only
  login endpoint).
- **The credential ruling's standing consequence, stated as posture:** on
  fleet's published profile the raw persona keys **are served to the
  browser**, by ruling — anyone can read all three out of `/meta` and call
  the API as any persona. Acceptable **only** because they authenticate
  synthetic demo principals on synthetic data; the committed rationale lives
  at `deploy/published/oct-fleet-maintenance/docker-compose.yml:56-63` and is
  cited, not restated.
- **Boot refuses rather than degrades** on a mis-provisioned persona pair: a
  digest missing from `API_KEYS`, a **crossed pair** (one persona's raw key
  mapping to another's `person_id`), or a `person_id` the vertical does not
  author. The crossed pair is the case that earns the check — it logs in
  successfully while the card names one persona and the audit trail records
  another, making the on-screen disclosure false with nothing visibly wrong.
  Guards: `tests/api/test_ui_profile.py:659,673,683,699,711,723` — the
  refusals, the crossed pair at `:683`, the positive control at `:699`, the
  unauthored-persona refusals at `:711,723`.
- **`view-monitor.js`'s `isPublished()` count went 0 → 1** (the picker
  branch, `view-monitor.js:506`). Stated because Step 3's s220 correction
  note recorded the ZERO — a future reader comparing the two needs the
  transition, not an apparent contradiction.
- **SD-8's ruled (iii) was executed here, in the same PR** — the narrative
  copy in the Act card's place on procurement (guard:
  `tests/api/test_ui_profile.py::test_sd8_iii_narrative_copy_is_published_only`,
  `:616`). The slot's own stamp already carries the ruling and its
  "executed by Step 6 *adding* the narrative copy" reading; this line records
  only that Step 6 is where that happened.
- ⚠️ **Provenance limit:** the session-224 closeout additionally records
  8 pre-test non-vacuity probes, a browser display-honesty probe against a
  false typed identity, and a 4007 → 4025 test-count delta. Those are
  attributed to that closeout record and PR #1138, **not re-verified by this
  edit** — kept out of PLAN-level fact deliberately (Lesson #0041 is exactly
  the laundering of such items).

### Step 7: Fleet's first-paint posture (Tab H must not open empty)

Today the waiting-human seed is procurement-only — the `vertical ==
"procurement"` branch in `main.py`'s lifespan, env-gated on
`settings.oct_demo_seed_operate` (PLAN-0054 Step 6c — it seeds the one
`waiting_human` run) — while fleet gets projection refreshes only (the
`"fleet_maintenance" in known` block below it), so its Monitor opens empty
until a visitor files a case at Tab I. _[Corrected s220, `superseded by new
info`: the gate itself is unchanged; the draft's `main.py:329` / `:364-391`
line numbers drifted as the file grew, so the references above are by
branch/symbol — they cannot rot the same way again.]_ Per SD-5's **ruling
(a)** (Cray, typed, s218 — seed one **and** keep the visitor path); this step
is ADR-0037-gated (Step 4's gate map — the seed writes into fleet's granted
Postgres):

- Extend the seed gate with a fleet branch under the same contract as
  procurement's — env-gated, idempotent (fixed run_id, skip-if-present),
  fail-soft, exactly the procurement seed block's own written contract —
  writing one waiting_human run into fleet's own Postgres.
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
Copy is conservative; SD-7 is **ruled** (bilingual cards + disclosures,
English role renderings adopted — Cray, typed, s218), with the **CTA's exact
wording** the one sub-item still Cray's at delivery — there is no oracle over
narrative.

**8b — the portal-side request (never a committed vero-lite file):** one
handoff delivering the assembly spec — card order (**fleet leftmost**,
LOCKED-2; explicitly noting SD-2's card-order ≠ system-number ≠
deployment-order separation), the relocated **"Build a Vertical" narrative**
(LOCKED-3: the story Tab E told becomes portal landing copy; the intake
*product* stays in the dev console — SD-6 **ruled**: keep), the arrival
narrative (PIN email → pick a persona → be refused → be granted → "I want
this for my data"), the bilingual policy (LOCKED-4, SD-7 ruled), and the CTA
ask (exact wording Cray's at delivery — SD-7's one open sub-item).
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

Deployment order per SD-2(b)'s **ruling: procurement, then fleet** (Cray,
typed, s218). Procurement's bring-up is **not** ADR-0037-gated; fleet's is
(Step 4's gate map + AC-11). For each system, in order: (1) explicit
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

**EXECUTED — system #2 (procurement), 2026-08-11, session 222; recorded here
the same day.** The full execution record is committed at
`docs/logs/2026-08-11-plan0103-step10-procurement-bring-up.md` — the gos, the
image/credentials/edge/allowlist evidence, the ACL-step failure and revert,
the runbook corrections, and the two-system headroom reading all live there
and are **cited, not restated** (two copies of a measurement are two chances
to disagree). PLAN-side record, so nothing surfaces later as drift:

- **Procurement's bring-up is COMPLETE**, under Cray's typed s222 §8 go for
  *that bring-up specifically*, plus a second typed go for the ACL step —
  exactly the per-bring-up evidence AC-10's second clause asks for. All five
  items ran in order; the live checks were evidence-not-gate per §8.
- **AC-10 remains open** (see its annotation): the obligation is
  per-bring-up; fleet's bring-up has not happened, needs its own go, and is
  AC-11-gated. Nothing about this record is "closed in substance".
- **One deviation from item (2)'s literal text:** "one ingress entry + one
  Access policy" was delivered as **Cloudflare dashboard configuration** —
  the `oct-procurement` label's DNS route plus the Access application with
  its one allow policy — not as repo files, per Step 1's s221 answer (no
  portal repo; the "does not exist" branch is permanent). ADR-0036 D2's
  two-artifact-per-system price is unchanged; only the medium moved. Item
  (2)'s wording predates Step 1's answer — this is executed-as-answered,
  recorded here so it is never later read as drift.
- **Item (4)'s keyed-`/whoami` sub-check is not applicable to this system** —
  an energy-shaped check carried over in error: procurement's allowlist
  deliberately refuses `^/whoami$` (the log's "Not done, and why" section).
  The consequence — a provisioned `API_KEYS` with no consumer — is recorded
  as a live input in SD-8's slot; SD-8 stays unruled.

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
  **RULED (Cray, typed, s218; recorded 2026-08-10): 🔴 a NEW ADR is required
  before per-system DB posture is legitimate — not a D5 amendment, a new
  ADR.** This overrules the recommendation above (drafter and Code both
  recommended no separate ADR; recorded for attribution honesty — settled,
  not re-argued). The ADR is **ADR-0037**
  (`docs/adr/0037-published-system-data-persistence-posture.md` —
  **Accepted**, ratified by Cray 2026-08-10, s218; this stamp read
  "Proposed" until the s225 freshness pass, `superseded by new info` — true
  at recording, never refreshed);
  it gates **fleet's half only** (Step 4's gate map — procurement's half
  proceeds while it is in flight), and the D6-scope question this clause
  could only surface now has its home there (ADR-0037 D3).
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
  **RULED (Cray, typed, s218; recorded 2026-08-10):** (a) ADR-0036 OQ-3's
  fleet trigger **has fired** — confirmed. (b) Bring-up order:
  **procurement, then fleet** — the calendar variable resolved as no
  near-term demo commitment.
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
  **RULED (Cray, typed, s218; recorded 2026-08-10):** fleet =
  **`A,C,F,H,I,J`, default A** — Cray typed "เอา F", so the flagged F
  addition is **adopted**. Procurement (joint with SD-4) = **option (ii): H
  drops; set `G,F`, default G, no personas** — LOCKED-1's DB-less
  procurement stands unrevised. Energy unchanged (`A,B,C,D,F`, default A).
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
  **RULED (Cray, typed, s218; recorded 2026-08-10): (b)** — the
  published-profile-only **persona picker**; raw demo keys in a host-env
  var, never git. Procurement takes **no** personas (the SD-3 joint ruling,
  option (ii)).
- **SD-5 — Fleet Tab H first paint: seed vs visitor-drives-it.** **(a —
  recommended)** seed one waiting run at boot (procurement's exact contract,
  `main.py:330-357`) **and** keep the visitor path — H is never empty, and a
  visitor still watches their own Tab-I case enter the loop; cost: one seed
  function + fixture. **(b)** visitor-only — purest whole-loop story, but Tab
  I becomes load-bearing for H, and a visitor who opens H first sees an empty
  monitor at the exact moment the demo must not look dead. *Why Cray:* it is
  a call about what a cold visitor sees in the first minute — demo content,
  not engineering.
  **RULED (Cray, typed, s218; recorded 2026-08-10): (a)** — seed one waiting
  run at boot **and** keep the visitor path.
- **SD-6 — Dev-console Tab E's fate.** LOCKED-3 moved its *narrative*
  portal-side; the *surface* in the dev console is a separate call.
  **Recommendation: keep it in dev** — it is the intake surface for
  design-partner sessions, and it costs the published surface nothing (E is
  already profile-excluded). If Cray rules excision instead, that removal is
  its own scoped change walked with `tools/excision_scope.py` first — not a
  rider on this PLAN. *Why Cray:* deleting a working surface is a product
  call; the dispatch names it Cray's explicitly.
  **RULED (Cray, typed, s218; recorded 2026-08-10): keep Tab E in the dev
  console.** Only its narrative moved portal-side. No step of this PLAN
  removes or implies removing it.
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
  **RULED (Cray, typed, s218; recorded 2026-08-10):** bilingual **cards +
  disclosures**; role names **translated to English** — the proposed
  renderings adopted. ⚠️ The **CTA's exact wording** was not part of the
  typed ruling and remains Cray's at Step 8 delivery — the one open
  sub-item of this slot.
- **SD-8 — Tab G's Act card on a personaless system (surfaced s220 by Step
  5's execution; unruled s220–s223 — no recommendation was offered and no
  step assumed an answer; RULED s224 — stamp at the end of this slot;
  ⚠️ corrected s224, `was an error`: the slot's factual premise about the
  rendered surface was false when written — measured block below).**
  SD-3's joint ruling dropped Tab H from procurement's
  set by reasoning about *Tab H, the monitor* — H's backing run is written
  through `async_session` and procurement is DB-less, so H is
  storage-blocked, not persona-blocked. That reasoning is sound and is not
  reopened here. What the ruling did not consider: **Tab G's own "Act — the
  human DOA gate" card reaches the same H-family routes** — in
  `view-hero.js`, `renderActions()` renders Approve/Reject buttons whose
  `decide()` handler calls `GET /runs/{run_id}` and then
  `POST /runs/{run_id}/gate/resolve`. Procurement publishes G and admits
  **no** H routes, so a visitor who logged in would meet a control that 404s
  — the exact dead-control shape SD-3 itself named "worse on the public
  surface than absence". Step 5 shipped a defensive posture: `^/whoami$` is
  **denied** on procurement's allowlist, and since `auth.js` makes
  `GET /whoami` the one auth-validating read, login is impossible at the
  edge — the buttons are never reached. _[Corrected s224, `was an error` —
  the draft continued "and an unauthenticated visitor sees a login form,
  not a broken control", and that was false on the published surface: no
  login form renders there at all (measured block below); the visitor meets
  neither a form nor a broken control.]_ The posture is consistent with
  SD-3/SD-4's "anonymous read + hero, no personas", and nothing is broken on first
  paint; the full reasoning lives today in
  `deploy/published/oct-procurement/cloudflared/config.yml`'s header and PR
  #1114's body — neither of which is this PLAN, which is why this slot
  exists. **The residual question, corrected:** what a cold visitor should
  meet in the Act card's place on a personaless published system — a UI
  call belonging to **Step 6** (the persona layer). _[Corrected s224, `was
  an error` — as authored (s220) the question read "Tab G's Act card still
  renders a login form on a system that will always refuse the login" and
  asked whether that card should render at all. That premise was false when
  written: the Act card and its login form do not render on any published
  profile, and had not since PLAN-0100 Step 3 — which predates this slot's
  authoring, so the slot was written over a surface that had already
  changed. Classification per CLAUDE.md §6: `was an error`, not `superseded
  by new info`. It stood uncorrected through s222/s223 because nobody ran
  the published profile and looked.]_
  **The s224 measurement behind that correction:** the published
  procurement profile was reproduced locally from its own committed
  `deploy/published/oct-procurement/published.env` (`UI_PROFILE=published`,
  `UI_PUBLISHED_VIEWS=G,F`, `OCT_VERTICAL=procurement`,
  `API_AUTH_ENABLED=true`, no `API_KEYS` provisioned) and the rendered DOM
  probed in a browser. ⚠️ A faithful local **reproduction**, not a
  live-system reading — the published domain is deliberately absent from
  this repo (ADR-0035 D1(3)) and the live surface sits behind Cloudflare
  Access (ADR-0035 D3); the branch under test reads `O.isPublished()`,
  driven by the same `UI_PROFILE=published` the live container receives.
  Probes: "Act — the human DOA gate" absent from the DOM; zero `input`
  elements of any type on Tab G and on Tab F (hence zero password fields);
  no login-affordance words anywhere; rendered tabs `G`,`F` only. The
  mechanism is two facts in `services/api/static/assets/view-hero.js` that
  compose: the Act card renders only in event mode (`view-hero.js:655`)
  while `mount()` defaults to manual (`view-hero.js:662`), and the only
  control that reaches event mode — the manual↔event toggle — is suppressed
  on every published profile (`view-hero.js:604-614`, `if (!published)`
  over `O.isPublished()`), the code comment stating the reason verbatim:
  "PLAN-0100 Step 3: not rendered on the published profile — event mode
  fires POST /demo/hero/event, the unauthenticated DB write D5(2) excludes
  (F4)." So on any published profile `mode` stays `'manual'`,
  `renderActPanel` is never called, and the Act card does not exist on the
  published surface — on every published system, not just personaless ones,
  and for a data-write reason, not a persona reason.
  The options as authored, stated neutrally, with the s224 corrections
  marked: **(i)** keep the shipped state — the login form is a real
  control honestly refused at the edge, zero code, but a visitor who tries
  it hits a dead end _[Corrected s224, `was an error` — this rationale
  describes a state that does not exist: there is no form, so no dead end.
  The option's outcome (change nothing) was coherent; its rationale was
  not]_; **(ii)** suppress the Act card on personaless published systems —
  no dead-end control, at the cost of a new published-profile UI branch
  _[Corrected s224, `was an error` — already done, and it cost no new
  branch: PLAN-0100 Step 3 paid that price for the unrelated D5(2)/F4
  data-write reason, and the suppression is `if (!published)`-scoped to
  every published system, not personaless-scoped]_; **(iii)** replace it
  there with narrative copy (the approve beat is fleet's story) — no dead
  end and the portal narrative gains a pointer, at the cost of copy with no
  oracle. The shipped state is safe and reversible, so nothing here is
  urgent; it is recorded so Step 6 does not execute over an unstated hole.
  *Why Cray:* what a cold visitor meets on the public surface is trust
  posture — ADR-0032 D5 territory, the same class as SD-4 — and no oracle
  catches a wrong first impression.
  **Live input (2026-08-11, s222 — input to this slot, NOT a ruling; as of
  s222 the slot stayed unruled and no option gained a recommendation):**
  the shipped state is now the *live public surface* _[Corrected s224, `was
  an error` — the s222 note named the shipped state "option (i)"; option
  (i)'s rationale described a rendered login form, and no form renders
  (measured block above). What s222 observed live — the edge refusals
  below — is real; its characterisation as option (i) was not]_: procurement
  runs as published system #2 with `^/whoami$` refused at its edge, so that
  system
  has no login path and its provisioned `API_KEYS` has no consumer — the
  digest→person mapping is unverifiable from outside until a keyed route is
  admitted. Cray ruled (typed, s222): **keep the key provisioned** anyway,
  ready if the ruling here admits a keyed route. Record:
  `docs/logs/2026-08-11-plan0103-step10-procurement-bring-up.md` ("Not done,
  and why"); the inline reasoning the next reader meets first lives in
  `deploy/published/oct-procurement/cloudflared/config.yml`'s header, which
  flags this exact coupling as this slot's question and not closed.
  **RULED (Cray, typed, s224; recorded 2026-08-12): (iii) — replace it
  there with narrative copy** (the approve beat is fleet's story). The cost
  stated above stands and is accepted: copy with no oracle — no test
  reddens if the copy is wrong. Operational reading against the corrected
  facts: the Act card already never renders on a published profile, so
  (iii) is executed by Step 6 *adding* the narrative copy where the card
  would have been — nothing needs removing. (iii) admits no keyed route, so
  the s222-kept key remains provisioned without a consumer on procurement.
  ⚠️ `cloudflared/config.yml`'s header still describes this slot as open —
  it predates the ruling and is corrected on the next touch of that file,
  not by this PLAN edit.

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
- ADR-0037 `docs/adr/0037-published-system-data-persistence-posture.md`
  (**Accepted** — ratified 2026-08-10, s218; the SD-1-ruled
  persistence-posture ADR: D1 grant, D2 obligations incl. the D2.7
  audit-chain measurement, D3 D6-bounding, D4 erasure question; gated
  fleet's half only — satisfied).
- Compliance (amendment round, 2026-08-10):
  `docs/compliance/ropa-published-demo.md` — the demo RoPA instance, DB-less
  as written (`:64-70` stored set · `:100` retention · `:112-115` the
  audit-chain erasure boundary · `:145-147` the prompt-log-scoped DSR search)
  · ADR-0035 D6 (`0035:586-629` — the prompt-log regime, LLM-route-scoped)
  · `docs/conventions/partner-ropa-lite.md:3-5` — per-dataset template, no
  change needed.
