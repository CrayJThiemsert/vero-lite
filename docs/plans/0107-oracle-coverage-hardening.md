# PLAN-0107: Oracle Coverage Hardening — Instrument, Reach, Arm (Implementation)

**Status:** Draft
**Owner:** Claude Code
**Created:** 2026-08-17
**Related ADRs:** ADR-0018 (Axis-B goal gate — the refute-not-bless mandate this PLAN extends to the oracles themselves); ADR-0032 (strategic frame — the published demo surfaces this PLAN protects are the D1 wedge).
**Sibling:** PLAN-0108 (convention/process half — weak oracle). **This PLAN depends on neither PLAN-0108 nor the companion ADR** named there: the implementation here is landable while the convention work is still being ratified. No ordering constraint runs in either direction.

> **Drafting provenance (ADR-012 D4.3).** Drafted by the in-harness `plan-drafter`
> subagent from the session-235 five-specialist audit fact-pack (originator: Cray
> dispatch). Independent reviewer: Cray at PR merge; committer: Code. Every
> `file:line` below was re-verified against the working tree on 2026-08-17 with
> Read/Grep; where the fact-pack's line numbers had drifted, the verified ones are
> used.

> **Rulings recorded (Cray, typed, 2026-08-17 — mid-draft).** S1 is RULED: two
> plans, split by **oracle strength** — this PLAN carries everything the offline
> gate can settle (①, ②, and the mechanical half of ③); PLAN-0108 carries the
> judgement half of ③. Also ruled into this PLAN's content: the live
> `operate_seed.py` grows to ≥ 21 staggered cases (not a test-fixture-only
> reach); the golden-trace corpus gains BOTH a below-direction and a
> non-`reading` trace; the DB-layer gap closes as a **floor on the executed
> DB-test count**; and the dead `fail_under = 70` is **deleted**, not armed.
> The scoped accelerator applies to this PLAN **in full**.

## Organising law (why this PLAN is shaped this way)

The session-235 audit converged on one law:

> An oracle sees a defect only when three independent conditions hold:
> **① an INSTRUMENT can read the artifact · ② the test DATA can reach the
> failing state · ③ someone ARMED it as a gate rather than as evidence.**

The Tab I clip (305px rendered clip, shipped to a live customer-facing system
while 4,113 tests were green) failed all three at once. This PLAN closes
*specific, named instances* of ①, ② and ③ — it is deliberately not "add more
tests": the repo's binding rules are already obeyed almost perfectly (the §8
scenario-rule audit over all 17 scenario/e2e files returned zero violations).
The gap lives in oracles that don't exist, states no fixture reaches, and
checks that exist as evidence instead of gates.

**Phase order is load-bearing: Phase B (② reach) must land before any browser
work is even considered.** With a 2-case live seed
(`verticals/fleet_maintenance/operate_seed.py:201,:315`) nothing overflows, so
a browser stage added today would go green-and-vacuous on day one — a detector
that cannot fail. The browser stage itself is Out of Scope (see below); this
PLAN builds the reach it will need.

## Goal

Close the audited instrument, data-reach and arming gaps with deterministic
gates: give CI a syntax oracle and a lifespan oracle it lacks (①); give the
fixtures the case volume, judgment diversity, breach direction, trace-kind
diversity, gold↔engine comparison and sign coverage they lack (②); and close
the mechanical half of ③ — replace the frozen `?v=` floor with a diff-aware
gate, put a floor under the executed DB-test count so a mass `pytest.skip`
cannot read as a pass, and delete the dead `fail_under = 70` that reads as an
enforced gate and is not — so that the next Tab-I-class defect reddens a
required check instead of shipping.

## Acceptance Criteria

Every AC declares its bucket per the dispatch contract — `check` (a command's
exit status decides it; the command is given) · `judge` (a named human/agent
reads a named artifact against a stated pass/fail read) · `evidence` (recorded,
explicitly NOT a gate). This PLAN eats its own dog food: no AC below claims a
runtime verb (renders / serves / boots / streams / persists) whose evidence is
a source-text read.

### Phase A — ① instruments

- [x] **AC-1 [check] — every shipped JS asset parses.** The CI `gate` job
  (`.github/workflows/ci.yml`) contains a step that enumerates
  `services/api/static/assets/*.js` **from disk at run time** (no frozen list),
  asserts the enumeration is **non-empty** (an empty glob must go RED, never
  loop zero times and pass — the 0100 null-selector trap,
  `docs/plans/done/0100-exposure-published-demo-surface.md:377-383`), and runs
  `node --check` on each. Command (the CI step itself):
  `files=(services/api/static/assets/*.js); test "${#files[@]}" -gt 0; for f in "${files[@]}"; do node --check "$f"; done`
  — exits nonzero naming file and line on any parse error. Measured cost:
  **11.0 s** over the **21** assets on disk, no repo deps (ubuntu runner ships
  node).
  > **Reviewer amendment (Code, 2026-08-17).** The draft asserted `≥ 20` here and
  > cited "22 assets"; measured on disk the same day, `services/api/static/assets/`
  > holds **21** `.js` files (plus 4 `.css`, a favicon and `fonts/`). A `-ge 20`
  > floor over a population of 21 leaves one file of headroom, and its misfire
  > remedy is editing the number — the guard-erosion ratchet this PLAN exists to
  > stop. The count invariant belongs in AC-2's bijection, which is strictly
  > stronger; non-empty is all AC-1 needs to close the null-glob trap.
- [x] **AC-2 [check] — every asset reference resolves; every asset is
  referenced.** A new test module `tests/api/test_asset_manifest.py` parses
  `services/api/static/index.html` for all `assets/` references (21 `<script
  src>` at `index.html:51-73`, 4 CSS links at `:28-31`), strips the `?v=`
  token, and asserts (forward) each resolves to a file on disk and (reverse)
  each on-disk `assets/*.js`/`assets/*.css` file is referenced or carries an
  entry in an in-test exemption dict with a written reason. **The bijection IS
  the anti-vacuity control** — measured 2026-08-17: 21 `<script src>` references
  and 21 `assets/*.js` files on disk, a perfect bijection with **zero** orphans
  (`mock.js` and `gate-fixture.js` are both referenced), so a dropped reference
  and an orphaned file each redden on their own, with no floor constant to
  drift. The parser additionally asserts it matched at least one reference, so an
  unparseable or emptied `index.html` cannot pass by matching nothing. Command:
  `uv run --no-sync pytest tests/api/test_asset_manifest.py -q`. Today only 3
  of 21 scripts are string-checked anywhere (`tests/api/test_static_ui.py:28`,
  `tests/api/test_export_cover_ui_contract.py:216`,
  `tests/api/test_view_hero_fleet_ui_contract.py:209`); a rename 404s silently
  and the page half-boots (the 404 mode is pinned at `test_static_ui.py:61-64`).
- [x] **AC-3 [check] — CI boots the app's lifespan, not just its import.** The
  runtime-closure step (`ci.yml:92-97`, today an import-only probe) is replaced
  by a boot smoke that enters `lifespan` (`services/api/main.py:460-467` —
  `discover_and_register()` across the vertical plugin trees, persona
  resolution at `:457`, the six lazy executor registrars at `:311-318`) via
  `fastapi.testclient.TestClient(app)` as a context manager — the pattern that
  demonstrably triggers lifespan at `tests/test_startup_log.py:26` — in the
  `--no-dev` venv (`httpx` is a runtime dep, `pyproject.toml:29`, so TestClient
  works there), with `DATABASE_URL` pointing at the job's postgres service.
  Command (in the step): `/tmp/vero-runtime-venv/bin/python tools/ci/boot_smoke.py`
  — exits nonzero if lifespan raises. This makes the spine's fail-loud contract
  (a malformed `procedures.yaml` fails at load — CLAUDE.md §3) CI-visible for
  the first time.
  > **Reviewer amendment (Code, 2026-08-17) — the fail-loud clause was MEASURED
  > and is ACTIVE-VERTICAL DEPENDENT; the step is scoped accordingly.** Probing
  > the smoke against a corrupted `procedures.yaml` for each spec-shipping
  > vertical: **CAUGHT** for `fleet_maintenance`, `building_materials`,
  > `supply_chain`, `procurement` — and ⚠️ **MISSED for `energy`, which boots
  > green.** Cause, verified at source: `lifespan` registers only
  > `_PROCEDURE_EXECUTOR_REGISTRARS[OCT_VERTICAL]`, and
  > `verticals/energy/procedures_factory.py` is the **one** spec-shipping factory
  > that never calls `load_procedures` (grep: every other one does).
  > 🔴 **`energy` is also the DEFAULT `OCT_VERTICAL`**, so a smoke that booted
  > only the default would have been green and blind to exactly the configuration
  > CI runs — a claim of a runtime property with no reach, which is the class of
  > defect this PLAN exists to close. **The CI step therefore runs the smoke once
  > per spec-shipping vertical, enumerated from disk** (6 boots, all green at
  > adoption). ⚠️ **The `energy` spec-parse residual stays OPEN and is recorded in
  > `tools/ci/boot_smoke.py`'s docstring** — closing it means energy's factory
  > loading its own spec, a behaviour change and out of scope here.
- [x] **AC-4 [check] — the executor-registrar map is complete against disk.** A
  new test asserts every vertical directory shipping a `procedures.yaml` has an
  entry in `_PROCEDURE_EXECUTOR_REGISTRARS` (`services/api/main.py:311-318`),
  with an explicit in-test exemption dict (reason required per entry —
  `vet_clinic` ships no `procedures.yaml`, per the map's own docstring
  `main.py:319-325`). This closes the hole the existing CLI-mirror equality
  (`tests/services/engine/test_cli_registrars.py:20-25`) cannot see: a 7th
  vertical missing from **both** maps is set-equal and green today. Command:
  `uv run --no-sync pytest tests/services/engine/test_registrar_completeness.py -q`.
- [x] **AC-5 [check] — CI mypy covers the plugin trees.** `ci.yml:56` becomes
  `uv run --no-sync mypy --strict services/ verticals/`. Measured: `mypy
  --strict verticals/` is already clean over 64 files, so remediation cost is
  zero; the pre-commit hook already covers this scope
  (`.pre-commit-config.yaml:41`) — CI merely stops trusting that the hook ran.
  Wall-clock delta: not measured. `tools/` is explicitly excluded (measured
  module-layout collision: `Source file found twice: "loop._schema" and
  "tools.loop._schema"` — a layout fix must come first, out of scope).
- [x] **AC-6 [check] — the two CI-orphaned pre-commit hooks run in CI.**
  `detect-secrets` (`.pre-commit-config.yaml:43-48`) and the ontology
  JSON-schema check (`:50-56`) — the ontology is the semantic layer, the core
  primitive, and `ontology_schema` appears in `tests/` exactly 0 times
  (verified grep) — gain a CI step. Commands:
  `uv run --no-sync pre-commit run detect-secrets --all-files` and
  `uv run --no-sync pre-commit run check-jsonschema --all-files`, each exiting
  nonzero on a finding. Cost: not measured.
  > **Reviewer amendment (Code, 2026-08-17).** The draft used `uvx`. Verified:
  > `pre-commit>=3.8.0`, `detect-secrets>=1.5.0` and `check-jsonschema>=0.29.0`
  > are all already in the dev extra (`pyproject.toml:45,:46,:48`), which
  > `ci.yml:44` installs — `uvx` would resolve and download a second copy. The
  > `--no-sync` is required for the same reason every other CI step carries it: a
  > bare `uv run` re-syncs without the dev extra and uninstalls the tooling
  > mid-job (`ci.yml:46-48`).

> **Phase A closing evidence (Code, 2026-08-18).** All six ACs are closed. The
> four `check` ACs whose oracle is a CI step are closed by run
> [32049063356](https://github.com/CrayJThiemsert/vero-lite/actions/runs/32049063356)
> on [#1204](https://github.com/CrayJThiemsert/vero-lite/pull/1204), where each
> step is recorded `success` **individually** — step 8 `JS assets parse`, step 9
> `mypy (strict, services/ + verticals/)`, step 10 `Secret scan`, step 11
> `Ontology schema check`, step 15 `Runtime closure BOOTS the app's lifespan, per
> vertical`. Step-level conclusions were read rather than the job's, because a
> green job does not distinguish a step that passed from one that was skipped.
>
> 🔴 **The first run of this PR FAILED, and the failure is worth keeping.** The
> AC-3 step died with `ModuleNotFoundError: No module named 'services'`: the
> runtime venv is built `--no-install-project` on purpose, and
> `python tools/ci/boot_smoke.py` puts the SCRIPT's directory on `sys.path` where
> the `python -c` probe it replaced put the CWD. **No local probe could have
> caught it** — every local run used the dev venv, which has the project
> installed, so the failing state was unreachable there by construction. That is
> a ② `reach` failure inside the PLAN that exists to close ② failures. Fixed with
> `PYTHONPATH: .` plus a comment recording the measurement, and verified by
> BUILDING the CI condition locally (a separate `--no-install-project` venv) and
> reproducing the error, not by reasoning about it.
>
> **Measured CI bill for Phase A (feeds AC-15):** the `gate` job went **7m53s →
> 9m7s**, i.e. **≈ +74 s** for all four new oracles, against the immediately
> preceding run on #1203. No new dependency: `node` ships on the ubuntu runner and
> the three hook tools were already in the dev extra.

### Phase B — ② data reach

- [ ] **AC-7 [check] — the live seed and a fixture reach the case-list UI's own
  limit.** *(Ruled by Cray 2026-08-17: the live seed itself grows.)*
  `verticals/fleet_maintenance/operate_seed.py` grows from 2 seeded cases
  (`:201,:315`) to **≥ 21 staggered cases** — timestamps spread across the
  trailing weeks so the month-end view reads as history, all bulk cases
  **CLOSED** (the seed module's own rationale: a closed case "leaves the event
  stream and never competes for the truck's latest-event slot",
  `operate_seed.py:318-321` — the two existing narrative cases and the
  truck-02 displacement logic stay intact), idempotent and fail-soft like the
  existing helpers. A scenario test then drives the real list endpoint
  (`services/api/routers/cases.py:248-274`): `limit=20` (the UI's own request,
  `services/api/static/assets/view-case.js:71`) returns exactly 20, newest
  first, stable across two reads (the `opened_at`/`case_id` tiebreak,
  `cases.py:270-274`); the default returns all; the boundary case is excluded
  at 20 and present at default. Today no fixture reaches the UI's limit, let
  alone the server's default 50 / clamp 500 (`cases.py:252,:273`); the 919px
  state that clipped came from a tree no fixture reproduces. Command:
  `uv run --no-sync pytest tests/api/test_case_list_overflow_scenario.py -q`.
- [ ] **AC-8 [check] — the stub LLM stops issuing one identical judgment to
  every event.** `_STUB_JUDGMENT` (`tests/api/conftest.py:29-39` — one canned
  object, autouse across the `tests/api` suite via `:70`, same
  title/confidence/`affected_entities` for every event in a streamed batch, as
  its own docstring admits at `:42-47`) becomes a factory deriving
  title/`affected_entities` from the triggering event, and a new scenario
  asserts a streamed batch of ≥ 2 events yields **distinct judgments mapped to
  the right events**. A recommend loop that maps every event to the first
  event's judgment is invisible today; after this AC it reddens. Command:
  `uv run --no-sync pytest tests/api -q` (the whole package must stay green
  with the factory — assertions that pinned the canned constant are updated
  without stubbing either side of any seam, per CLAUDE.md §8).
- [ ] **AC-9 [check] — the golden-trace corpus covers the `below` direction AND
  a non-`reading` event.** *(Ruled by Cray 2026-08-17: both traces.)*
  `tests/services/engine/eval/golden_traces/` (today 3 traces, all
  `event_type: reading`, all over-temp — verified listing) gains **two**
  traces, produced by the same harness that produced traces 01–03: (a) a
  below-direction trace (the aquaculture dissolved-oxygen crash the code
  itself cites, `services/engine/demo_events.py:44-53`, threshold comparison
  at `:62`), and (b) a trace exercising a non-`reading` event type — the
  anchor filter at `demo_events.py:57-64` selects `event_type == "reading"`
  only, so the corpus as it stands can never redden a regression in how
  non-reading events flow through the evaluated path. Command:
  `uv run --no-sync pytest tests/services/engine/eval -q`.
- [ ] **AC-10 [check] — every expressible gold case is compared to the real
  engine.** The nl-13 harness
  (`tests/benchmark/test_nl_query_feasibility_gold.py:220-244` — real engine,
  real adapter, real scorer, only the model transport stubbed) is extended to
  every non-ceiling case nl-01…nl-12, each with its hand-authored structured
  translation. Today those 12 are checked only for internal self-consistency
  (`:68-89`, e.g. `expected_count == len(expected_ids)`) — **gold compared to
  gold**, the self-agreeing shape §8 forbids at a seam §8's wording does not
  reach. Any case inexpressible as a single structured query goes in an
  explicit in-test register with a written reason (an empty-reason entry fails
  the test). A mismatch against the engine is a **surfaced finding for Cray**,
  never a silent xfail and never a gold edit (LOCKED: the energy synthetic
  events do not change — `gold.yaml:64,:77,:145,:173,:218-224` hard-couple to
  them). Command: `uv run --no-sync pytest tests/benchmark/test_nl_query_feasibility_gold.py -q`.
- [ ] **AC-11 [check] — negative money is pinned at a real seam.** The month-end
  ฿ aggregation seam (`services/db/repair_case_closeout.py` — confirmed by grep
  to carry ฿ amounts; internals read at execution, per Step 9) gets a test that
  drives a negative `Decimal` amount through the real producer→consumer path
  and pins ONE specific signed outcome: correct signed aggregation if the
  domain admits credits/refunds, or an explicit loud rejection if it does not —
  the step picks after reading the seam, and the test docstring states which.
  Today the repo has exactly one distinct negative `Decimal` literal and it is
  a DoA tier bound (`tests/services/engine/procedures/test_doa_tier.py:176`);
  sign handling in ฿ aggregation is untested. Command:
  `uv run --no-sync pytest tests/services/test_closeout_negative_money.py -q`
  (final module placement follows the house layout at execution; the command
  tracks the file).
- [ ] **AC-12 [check] — a floor under the executed DB-test count.** *(Ruled by
  Cray 2026-08-17: close this as a count floor.)* A session-finish check
  (in the top-level conftest, active when `CI` is set — GitHub sets `CI=true`)
  fails the run when the number of **executed** (non-skipped) DB-backed tests
  falls below a floor set from the CI baseline with an explicit margin and a
  comment stating the floor's failure mode (RED on shrink — loud; never a
  silent pass). Today `tests/db_support.py:217,:224` turns an unreachable test
  DB into `pytest.skip(_UNREACHABLE)` with no floor anywhere — the CI job
  *provides* a postgres service (`ci.yml:22-35`), yet if it were unreachable
  the whole DB layer would silently drop and `pytest -q` (`ci.yml:77`) would
  still exit 0. Local behaviour is untouched (worktrees legitimately lack the
  dev Docker Postgres; the dev-DB guard at `db_support.py:213` stays). Command
  (the probe is the check):
  `CI=1 TEST_DATABASE_URL=postgresql+asyncpg://vero:vero@localhost:59999/vero_lite_test uv run --no-sync pytest tests -q` <!-- pragma: allowlist secret — the throwaway CI-container cred already carried in ci.yml:27,:60,:75-76 and docker-compose.yml; port 59999 is deliberately unreachable, which is the whole probe -->
  exits **nonzero** (today it exits 0 with skips).
- [ ] **AC-13 [check] — the dead coverage floor stops existing.** *(Ruled by
  Cray 2026-08-17: delete, not arm.)* `pyproject.toml:124` (`fail_under = 70`)
  is deleted: no `addopts` exists (`:109-116`) and `ci.yml:77` is a bare
  `pytest -q`, so coverage is never measured while the config reads as an
  enforced gate — a guard that reads as protection and is not. The
  `[tool.coverage.run]` scope (`:118-120`) and `show_missing` stay for
  on-demand local measurement; only the enforcement lie goes. Command:
  `git grep -n "fail_under" -- pyproject.toml` exits **1** (it exits 0 today).
  Any future *armed* coverage gate is a new decision for Cray, made against a
  measured number — not this PLAN's business.
- [ ] **AC-14 [check] — the frozen `?v=` floor is replaced by a diff-aware
  gate, in the same PR.** `tests/api/test_ui_profile.py:725-751` freezes
  per-file minima over 9 of 21 JS files and 0 of 4 CSS files — editing
  `views.css` without bumping `index.html:29` passes today, and that exact
  bump (c43→c44, PR #1190) was hand-made and unguarded. **This guard passes
  today and would still pass if the thing it protects were broken — it is
  retired**, not kept alongside, in the PR that lands its replacement (SD-1):
  a script `tools/ci/cache_bust_diff_check.py` that, given the PR's changed
  files (`git diff --name-only HEAD^1 HEAD` — requires `fetch-depth: 2` on
  `ci.yml:37`; depth 1 has no parent) and `index.html`, exits nonzero when a
  changed `services/api/static/assets/*` file's `?v=` token did not change.
  The script takes the changed-file list and the HTML as inputs, so its unit
  tests drive both verdicts without git — including the PR #1190 shape
  (`views.css` changed, token unchanged → exit 1). Commands:
  `uv run --no-sync pytest tests/tools/test_cache_bust_diff_check.py -q` and
  the new CI step.

### Cross-phase

- [ ] **AC-15 [evidence] — the CI bill is recorded.** The closing PR body
  records, per new CI step, the observed wall-clock delta on that PR's run.
  Recorded, **explicitly NOT a gate** — no threshold is enforced on these
  numbers; they exist so the later browser-plan discussion starts from
  measured cost, not vibes.

## Out of Scope

- ❌ **`deploy/published/deploy.py` path guard** — already fixed in PR #1193
  (`fix/deploy-local-compose-path`, commit `17dca12`). LOCKED.
- ❌ **`on: push: branches: [main]` CI trigger** — rejected. Branch protection
  is `strict:true` with required context `gate` and `enforce_admins:true`
  (verified live via `gh api` in session 235): the base cannot move underneath,
  and a `pull_request` checkout grades `refs/pull/N/merge`, so the graded tree
  IS the tree that lands. A push trigger buys one duplicate run per merge.
  LOCKED.
- ❌ **DOM shim (jsdom / happy-dom)** — rejected. No layout engine means
  `getBoundingClientRect`/`offsetHeight` return zero: the motivating 305px clip
  is unrepresentable, and it would import the first JS toolchain into a repo
  whose `docs/conventions/ui.md` documents having none. LOCKED.
- ❌ **Browser stage (Playwright)** — the only instrument that can adjudicate a
  clip, and it belongs in a LATER plan: (a) it depends on this PLAN's Phase B —
  with a 2-case seed nothing overflows, so a browser stage today is green and
  vacuous on day one; (b) protection is `strict:true`, so every PR already pays
  a full `gate` round — a ~3-minute browser stage on non-UI PRs is pure tax.
  When it lands it should be `workflow_dispatch` + a `ui` label, not a required
  check. LOCKED as to sequencing; the successor plan decides the rest.
- ❌ **Arming a coverage floor** — the dead `fail_under` is deleted (AC-13,
  ruled); arming a measured one is a separate future decision, not smuggled in
  here.
- ❌ **Regenerating or enriching the energy synthetic events** —
  `gold.yaml:64,:77,:145,:173,:218-224` hard-codes counts, ids, a hand-computed
  mean and a per-entity cardinality map against
  `verticals/energy/data_adapter/synthetic.py`; one added Battery-Bank-B
  reading invalidates `:173`. Guard first (AC-10), enrich second — or never.
  The fleet seed growth (AC-7) is independent of this coupling. LOCKED.
- ❌ **Promoting any advisory lesson to binding, and the third `measure`
  criterion bucket** — behaviour-binding, therefore ADR territory (CLAUDE.md
  §1), carried by the companion ADR named in PLAN-0108. This PLAN does not
  depend on it and does not decide it. LOCKED.
- ❌ **The ③ convention work** — AC-authoring discipline, the runtime-verb
  audit, the fixture-boundary rule, the pre-close three-condition set. RULED
  into **PLAN-0108** (Cray, typed, 2026-08-17), which depends on the companion
  ADR; this PLAN does not.
- ❌ **Constitutional (`CLAUDE.md`) text** — the §8 wording question (dispatch
  S3) is a convention question and is surfaced in **PLAN-0108**, drafted by
  Cowork by convention (ADR-009 D1), never here.
- ❌ **`mypy --strict tools/`** — measured immediate failure (`Source file
  found twice`); a module-layout fix must precede it and is its own small
  chore.

## Surfaced decisions

**This PLAN carries no open surfaced decision.**

- **SD-1 (dispatch S2) — does retiring `test_ui_profile.py:725-751` need its own
  ratification? RULED (Cray, typed, 2026-08-17): NO separate ceremony.**
  Accepting this PLAN (AC-14 names the retirement in its text) plus normal PR
  review IS the ratification, because the replacement lands in the same commit
  and the retired guard's protective claim is demonstrably false — it passes
  today with the protected behaviour breakable. Rejected: a one-line
  ratification note in STATUS before the PR.
  > **Why this is the right default, recorded so the next retirement does not
  > re-open it.** The guard being retired meets the definition of **class C1**,
  > which ADR-0038 made binding on 2026-08-17: a green from an oracle that could
  > not have gone RED. If removing a guard already proved inert cost more
  > ceremony than leaving it in place, the incentive would run toward
  > accumulating guards that read as protection and are not — which is worse
  > than no guard, because it manufactures confidence at the point the repo
  > looks for evidence. Ceremony should scale with what a change puts at risk,
  > and retiring a demonstrably-inert guard puts nothing at risk that the
  > replacement does not already cover in the same commit.
- *(Dispatch S1 — RULED: two plans, recorded above. Dispatch S3 — a convention
  question; surfaced in PLAN-0108, not here.)*

## Steps

**The scoped accelerator applies to this PLAN in full** (ruled): attempt the
structurally bold version first — the offline gate (4,115 passed / 8 skipped ·
`mypy --strict services/` clean over 136 files · `ruff check` + `ruff format`
clean over 631) is the safety net, and a wrong bold attempt is caught free.

Every step names its **non-vacuity probe**: the specific mutation and the
output that mutation changes. A probe run happens on a scratch copy or scratch
branch, is reverted, and the RED is observed before the green is trusted
(restore from a scratch copy, not from git — the probe must be SEEN to fire).
A mutation that alters only comments, formatting or dead code does not count.

### Step 1 (A / AC-1): the JS syntax gate

Add the `node --check` step to `ci.yml` after the ruff steps (fail fast before
the expensive DB steps). Enumerate from disk, floor the count at 20 with a
comment stating the floor's failure mode (RED on shrink — loud; never a silent
pass, unlike the retired `?v=` floors).
**Probe:** corrupt one statement in a scratch copy of
`services/api/static/assets/view-case.js` → the step's exit code flips nonzero
and its stdout names `view-case.js` with a line number (measured shape:
`view-case.js:381 SyntaxError`). Output changed: the CI step's exit status +
the named file in its log. **Cost: 11.0 s, measured.**

### Step 2 (A / AC-2): the asset manifest test

Write `tests/api/test_asset_manifest.py` — forward resolution, reverse
referencing with reasoned exemptions, parse-count floor ≥ 20 asserted before
any judgment. The fact-pack measured 22 on-disk JS assets against 21 references
(`index.html:51-73`, verified): the reverse check will surface the unreferenced
one; its exemption entry (or its deletion) is decided at execution with the
reason written in the test.
**Probe:** in a scratch tree, rename `assets/view-export.js` on disk → the
forward check reds naming the dangling reference (`index.html:72`); separately,
add an unreferenced `assets/orphan.js` → the reverse check reds naming it.
Output changed: the pytest verdict and the assertion message naming the file.
Cost: inside the existing pytest step, not separately measured.

### Step 3 (A / AC-3 + AC-4): boot the lifespan; complete the registrar map

Write `tools/ci/boot_smoke.py` (TestClient context-manager boot, the
`tests/test_startup_log.py:26` pattern) and swap it into the runtime-closure
step (`ci.yml:92-97`) with the job's `DATABASE_URL` — the boot subsumes the
import probe (a module that cannot import cannot boot). Write
`tests/services/engine/test_registrar_completeness.py` (disk enumeration of
`verticals/*/procedures.yaml` vs `_PROCEDURE_EXECUTOR_REGISTRARS`,
reasoned exemption dict). Note what the boot smoke does NOT claim: the
projection loads inside lifespan are fail-soft by design, and their dedicated
guard already exists (`tests/test_startup_fleet_projections.py:1-20`, which
records the in-tree `UnboundLocalError` precedent); the smoke catches the
lifespan-*raising* class — registrar import errors, persona resolution
failures (`main.py:457`), and a malformed spec failing loudly at load.
**Probe (AC-3):** in a scratch tree, malform one `procedures.yaml` field → the
boot smoke exits nonzero with the spec loader's traceback. Output changed: the
CI step's exit status. **Probe (AC-4):** remove `"fleet_maintenance"` from
BOTH the API and CLI maps → the CLI-mirror test stays green (set-equal), the
new completeness test reds — proving the new test sees exactly the blind spot
the mirror cannot. Output changed: the completeness test's verdict. Cost: not
measured.

### Step 4 (A / AC-5 + AC-6): widen mypy; adopt the orphaned hooks

Amend `ci.yml:56` to `mypy --strict services/ verticals/`; add the
`uvx pre-commit run detect-secrets --all-files` and
`uvx pre-commit run check-jsonschema --all-files` steps.
**Probe (AC-5):** add an untyped `def f(x): return x` to a scratch
`verticals/energy/handlers.py` → mypy step reds. Output changed: the mypy
step's exit status. **Probe (AC-6):** violate the ADR-008 D2 schema in a
scratch copy of one `verticals/*/ontology/*.yaml` → check-jsonschema exits
nonzero; plant an unbaselined high-entropy canary string in a scratch tracked
file → detect-secrets exits nonzero. Output changed: each step's exit status.
Cost: not measured (record per AC-15).

### Step 5 (B / AC-7): grow the live seed past the UI's limit; pin the boundary

Grow `operate_seed.py` to ≥ 21 staggered cases (ruled): a bulk of CLOSED
historical cases with `opened_at` spread across the trailing weeks — closed so
they leave the event stream and never compete for a truck's latest-event slot
(`operate_seed.py:318-321` rationale), preserving the two narrative cases and
the truck-02 displacement design (`:204-206` region) untouched; idempotent
and fail-soft like the existing helpers. Then write the overflow scenario
against the real list endpoint: truncation boundary at the UI's own
`limit=20`, ordering stability (the `opened_at`/`case_id` tiebreak,
`cases.py:270-274`), default-limit inclusion.
**Probe:** delete the `.limit(...)` clause from the query in a scratch copy of
`cases.py:273` → the `limit=20` assertion reds (all cases returned). Output
changed: the response's case count, hence the pytest verdict. Also verify seed
idempotency: two boots, same case count (a second boot that doubles the seed
is a RED). Cost: inside pytest, not separately measured.

### Step 6 (B / AC-8): per-event stub judgments

Convert `_STUB_JUDGMENT` to a factory keyed on the triggering event; write the
distinct-judgments scenario; sweep `tests/api` for assertions that pinned the
canned title/entity and update them to the factory's derived values — without
stubbing either side of any seam (CLAUDE.md §8).
**Probe:** in a scratch copy, mutate the recommend batch loop to reuse the
first event's judgment for every event → the new scenario reds on the
distinct-mapping assertion while (instructively) the rest of the suite stays
green — the exact invisibility being closed. Output changed: the per-event
judgment fields in the streamed response, hence the scenario verdict. Cost:
not separately measured.

### Step 7 (B / AC-9): two golden traces — below-direction and non-reading

Read the harness that produced traces 01–03 (mechanism read at execution — the
corpus predates this PLAN), then produce and wire in: (a) the DO-crash
below-direction trace, and (b) a trace whose evaluated path carries a
non-`reading` event type (the anchor filter selects `reading` only,
`demo_events.py:57-64` — today a regression anywhere non-reading events flow
has no golden artifact that can redden).
**Probe (a):** invert the `below` comparison inside the threshold-crossing
predicate (`demo_events.py:62` seam) in a scratch copy → trace (a)'s eval
verdict reds while traces 01–03 stay green — proving the new artifact, and
only it, pins the below branch. **Probe (b):** in a scratch copy, drop
non-`reading` events from the pipeline the trace exercises → trace (b)'s
verdict reds while 01–03 stay green. Output changed: each new trace's eval
verdict. Cost: inside pytest, not separately measured.

### Step 8 (B / AC-10): gold meets engine, twelve more times

Parametrize the nl-13 harness over every non-ceiling case with hand-authored
structured translations; add the reasoned inexpressibility register.
**Measure-first substep:** run the extended comparison once BEFORE asserting;
any nl-01…nl-12 mismatch is written up as a surfaced finding for Cray (gold
wrong vs engine wrong is a ruling, not a guess), and the case enters the
register with that reason until ruled. The energy events are not touched
(LOCKED).
**Probe:** perturb one `expected_count` in a scratch copy of `gold.yaml` → that
case's comparison reds. Output changed: the scorer's verdict for the perturbed
case. Cost: not measured (twelve real-engine runs; record per AC-15).

### Step 9 (B / AC-11): pin negative money

Read `services/db/repair_case_closeout.py` (and its producer path) first;
decide credits-representable vs reject-loudly from what the domain already
does; write the scenario driving a negative `Decimal` through the real path;
state the pinned outcome in the test docstring.
**Probe:** wrap the aggregated amount in `abs()` in a scratch copy of the seam
→ the test reds (signed-outcome assertion), regardless of which pin was chosen.
Output changed: the aggregated ฿ figure (or the raised rejection), hence the
verdict. Cost: inside pytest, not separately measured.

### Step 10 (C / AC-12): the executed DB-test floor

Add the session-finish count check (CI-only, via the `CI` env var): count
executed non-skipped DB-backed tests, fail below the floor. Set the floor from
the CI baseline count with an explicit margin and a comment stating the
failure mode (RED on shrink — loud). Keep the local skip
(`db_support.py:217,:224`) and the dev-DB guard (`:213`) untouched. Add a unit
test for the counting mechanism itself (a synthetic session where all DB
tests skip must trip it).
**Probe:** the AC-12 command itself — dead-port URL with `CI=1` → every DB
test skips → the floor check fails the run where today it exits 0 with skips.
Output changed: the pytest process exit status. Cost: none (no new CI step).

### Step 11 (C / AC-13): delete the dead coverage floor

Delete `fail_under = 70` (`pyproject.toml:124`); keep `[tool.coverage.run]`
scope and `show_missing` for on-demand local measurement; grep the repo for
any other reader of `fail_under` before the commit (none is expected; a found
one is a surfaced finding, not a silent edit).
**Probe:** the AC-13 command run before and after — `git grep -n "fail_under"
-- pyproject.toml` exits 0 pre-deletion and 1 post-deletion. Output changed:
the grep exit status; the config no longer claims an enforcement that never
runs. Cost: none.

### Step 12 (C / AC-14): replace the frozen `?v=` floor

Write `tools/ci/cache_bust_diff_check.py` + its unit tests (both verdicts,
including the PR #1190 red shape); set `fetch-depth: 2` on `ci.yml:37`; add the
CI step; **delete `test_every_edited_asset_got_a_cache_bust`
(`test_ui_profile.py:725-751`) in the same commit** — the repo must not keep a
guard that reads as protection and is not (SD-1 governs whether extra
ceremony precedes this).
**Probe:** the script's unit red case IS the probe (changed `views.css`, token
`c44` unchanged → exit 1); additionally one scratch CI run on a branch editing
`views.css` without a bump → the new step reds. Output changed: the script's
exit status, unit-observed and CI-observed. Cost: not measured (a `git diff`
plus a parse; record per AC-15).

## Verification

How we know it worked — three reads, in order:

1. **Every gate proved it can fail before its green was trusted.** Each step's
   non-vacuity probe was run, its RED observed and its output-changed claim
   confirmed, then reverted (scratch-copy restore, not git-restore). A probe
   whose mutation changes only comments/formatting/dead code does not count;
   every probe above names a behavioural output (an exit status, a verdict, a
   response field) that flips.
2. **The offline gate holds after every phase:** full `pytest` (4,115+ tests —
   the count grows with this PLAN), `mypy --strict services/ verticals/`,
   `ruff check` + `ruff format --check`, all green; plus the new CI steps green
   on the PLAN's own PRs (which, per branch protection, is the merged tree).
3. **The three-condition law, re-audited against this PLAN's own claims:** for
   each closed AC, name which of ①②③ it closed and confirm the closure is a
   *gate* (a required-check exit status) — not evidence. AC-15 is the single
   deliberate exception and says so in its own text. Anything discovered
   during execution that this PLAN cannot close (a fourth failing subsystem,
   an nl-case mismatch, a floor baseline surprise) is surfaced to Cray, not
   absorbed silently.
