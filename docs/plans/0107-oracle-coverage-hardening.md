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
work is even considered.** At drafting the live seed held 2 cases, so nothing
overflowed and a browser stage added then would have gone green-and-vacuous on
day one — a detector that cannot fail. The browser stage itself is Out of
Scope (see below); this PLAN builds the reach it will need.
_[Corrected s241, `superseded by new info`: the vacuity ground above was true
on 2026-08-17 and was falsified when AC-7 closed (s236, #1206) — the seed now
holds **21** cases (the two narrative cases, `seed_demo_repair_case` +
`seed_settled_history_case`, plus the NINETEEN-entry closed backlog
`_CASE_LIST_HISTORY` seeded by `seed_case_list_history`; the module's own
comment above that tuple states the load-bearing arithmetic), one past the
UI's own `limit=20`, so the overflow state IS now reachable. The *conclusion*
still stands and was honoured in the event — reach landed first. What carries
the browser-stage deferral today is no longer unreachability but the
Out-of-Scope entry's ground (b): every PR already pays a full `gate` round, so
a browser stage belongs behind `workflow_dispatch` + a `ui` label in a
successor plan. The original text also cited the 2-case seed sites as
`operate_seed.py:201,:315`; AC-7's ~200 added lines moved both onto unrelated
code (`:201` now sits inside `_stamp_run_subject`'s proposal loop, `:315` on a
`description=(` line), so this section now anchors by symbol instead.]_

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

- [x] **AC-7 [check] — the live seed and a fixture reach the case-list UI's own
  limit.** *(Ruled by Cray 2026-08-17: the live seed itself grows.)*
  `verticals/fleet_maintenance/operate_seed.py` grows from 2 seeded cases
  (`:201,:315`) to **≥ 21 staggered cases** — timestamps spread across the
  trailing weeks so the month-end view reads as history, all bulk cases
  **CLOSED** (the seed module's own rationale: a closed case "leaves the event
  stream and never competes for the truck's latest-event slot" — the comment
  inside `seed_settled_history_case` _[Corrected s241, `superseded by new
  info`: this cite read `operate_seed.py:318-321`, measured correct at
  drafting; AC-7's own ~200 added lines moved the comment (near `:512` on disk
  today, while `:318` now holds a `status=CASE_STATUS_OPEN,` field), so it is
  re-anchored by symbol + quoted sentence rather than by line]_ — the two
  existing narrative cases and the truck-02 displacement logic stay intact),
  idempotent and fail-soft like the existing helpers. A scenario test then drives the real list endpoint
  (`services/api/routers/cases.py:248-274`): `limit=20` (the UI's own request,
  `services/api/static/assets/view-case.js:71`) returns exactly 20, newest
  first, stable across two reads (the `opened_at`/`case_id` tiebreak,
  `cases.py:270-274`); the default returns all; the boundary case is excluded
  at 20 and present at default. Today no fixture reaches the UI's limit, let
  alone the server's default 50 / clamp 500 (`cases.py:252,:273`); the 919px
  state that clipped came from a tree no fixture reproduces. Command:
  `uv run --no-sync pytest tests/api/test_case_list_overflow_scenario.py -q`.
  > **Closing evidence (Code, 2026-08-18).** `seed_case_list_history` seeds **19**
  > CLOSED backlog cases; with the two narrative cases the list holds **21**, one
  > past the UI's page. 6 tests, all green; suite 4123 → **4129**.
  > **Witnessed RED, three ways, each reddening the test that claims the property
  > and naming the cause:** removing `.limit(...)` from the real query reddens the
  > truncation test · seeding the backlog OPEN instead of CLOSED reddens the
  > demo-safety test · shrinking the backlog reddens the **anti-vacuity** test
  > *first*, which is the point of having one.
  > ⚠️ **Two things measured rather than assumed.** (1) The backlog is **invisible to
  > the month-end tab by construction, not by luck** — `repair_spend_export` builds
  > rows from cases carrying a `RepairCaseRunLink` or a `RepairCaseCloseout`, and
  > these have neither; checked against that query *before* writing the seed,
  > because a seed onto the demo's flagship truck once displaced its ฿48,000 axle
  > breach and only the full suite noticed. (2) The scenario must take its session
  > from **`api_db_maker`**, not a fresh `async_session()` — a second asyncpg
  > connection collides with the one the client holds (`another operation is in
  > progress`, measured on the first run).
- [x] **AC-8 [check] — the stub LLM stops issuing one identical judgment to
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
  > **Closing evidence (Code, 2026-08-18).** The stub is now `_judgment_for()`,
  > deriving title / description / `affected_entities` from the triggering event
  > recovered out of the rendered prompt. **`tests/api` stayed green with ZERO
  > assertion updates — 459 passed** (the AC anticipated updating pinned
  > assertions; measured, nothing outside `conftest.py` pinned the canned strings).
  > New scenario `tests/api/test_recommendation_fanout_scenario.py`, 4 tests.
  > **Witnessed RED:** restoring the OLD canned stub reddens the distinctness test
  > with *"5 recommendations collapsed to 1 distinct title"* — so the claim "the old
  > stub could not reveal this" is demonstrated, not asserted.
  >
  > 🔴 **A ② REACH finding the AC did not anticipate, measured rather than assumed.**
  > The AC says "a streamed batch of ≥ 2 events". Counting what each vertical's
  > synthetic stream actually trips through `_is_recommendation_trigger`:
  > **energy 1** of 11 · **aquaculture 0** of 7 · **supply_chain 0** of 4 ·
  > **procurement 0** (it streams nothing) · **building_materials 2** of 2 ·
  > **fleet_maintenance 5** of 5. On energy — the obvious default — this module's
  > distinctness assertions **passed vacuously on the first run**, and only the
  > anti-vacuity test refused them. Energy's events are LOCKED by AC-10, so the
  > scenario runs on **fleet_maintenance**: a vertical that already reaches the
  > state, rather than an edit that manufactures it.
  > ⚠️ **`aquaculture` streaming 0 triggering events is worth AC-9's attention** —
  > AC-9 cites the aquaculture dissolved-oxygen crash as its below-direction source.
- [x] **AC-9 [check] — the golden-trace corpus covers the `below` direction AND
  a non-`reading` event.** *(Ruled by Cray 2026-08-17: both traces. Re-scoped by
  Cray 2026-08-27 to option (b); delivered s258 — see the Delivered annotation
  below for what each half does and does not pin.)*
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
  > **Reviewer amendment (s241) — AC-9 is BLOCKED pending a Cray ruling on
  > re-scope: its Step 7 probe is UNRUNNABLE AS WRITTEN.** Three independent
  > defects, measured s241 and re-verified against the working tree 2026-08-20:
  >
  > **(1) The named seam holds no comparison.** Step 7 says to invert the
  > `below` comparison inside the threshold-crossing predicate
  > ("`demo_events.py:62` seam") — but `:62` is
  > `and crosses_threshold(e["measured_value"], threshold, direction)`, a
  > **delegation**; `below` appears in `demo_events.py` exactly twice, both in
  > a docstring. The comparison lives at `services/engine/recommender.py:77-79`
  > (`crosses_threshold`), whose own docstring names it *"The single source of
  > truth shared by the trigger (`_is_recommendation_trigger`), the fail-safe
  > rule (`_rule_recommend`), and the demo-anchor breach selector
  > (`demo_events._breach_event`)"* — inverting it reddens three unrelated
  > consumers, not one trace.
  >
  > **(2) The named oracle cannot observe the mutation.**
  > `tests/services/engine/eval/test_eval_harness.py:39-43` loads the corpus as
  > **static JSON** (`json.loads(path.read_text(...))`); its five tests assert
  > only a non-empty glob, `LlmJudgment` validation, confidence in range,
  > handler resolution and envelope composition. Grep
  > `crosses_threshold|demo_events` over `tests/services/engine/eval/`: **zero
  > matches**. The Step 7 mutation changes nothing this harness reads, so its
  > promised RED cannot fire there by construction.
  >
  > **(3) The producer this AC presumes may not exist.** The AC requires traces
  > *"produced by the same harness that produced traces 01–03"*; grep
  > `golden_trace` across every `.py` in the repo returns **one** file — the
  > test module itself — and Step 7 concedes the mechanism was never read
  > (*"mechanism read at execution — the corpus predates this PLAN"*).
  >
  > Executing this AC as written would therefore manufacture an **ADR-0038
  > class-C1 guard — a green that could not have gone RED — inside the PLAN
  > whose stated purpose is to eliminate class-C1 guards:** dropping two JSON
  > files into `golden_traces/` adds ~8 parametrized assertions checking
  > schema / confidence / handler / composition, none of which can pin the
  > `below` branch or the non-`reading` path. `docs/STATUS.md` §"Active TODOs"
  > has carried "AC-9 design-blocked" since s241, but that judgement had never
  > been written into this PLAN — this amendment closes that gap. **Re-scope
  > options for Cray, laid out neutrally; none is picked here:** (a) re-home
  > the below-direction oracle to where the predicate actually runs
  > (`recommender.crosses_threshold`, already reached by existing tests);
  > (b) build a real trace producer first, then the two traces; (c) retire
  > AC-9. Until ruled, this AC stays `[ ]` and no execution against it is
  > authorised.
  >
  > **RULED (Cray, typed, 2026-08-27, session 258): option (b)** — build a real
  > trace producer first, then the two traces. Rationale as given: the better
  > long-term investment of the three. Execution against AC-9 is now authorised
  > **under the re-scope below**, not as Step 7 stands.
  >
  > 🔴 **What was re-measured at ruling time (s258), which constrains execution.**
  > All three s241 defects re-verified against the working tree, and two further
  > facts measured that the s241 amendment did not carry:
  >
  > **(i) The below-direction half already has a live oracle with a control.**
  > `tests/services/engine/test_recommender_config.py:108-112` pins
  > `crosses_threshold` in the `below` direction at the exact aquaculture DO
  > values (3.2 vs 4.0, inclusive boundary, plus a negative); and
  > `tests/services/engine/test_demo_events.py:195` drives `below` through the
  > real `demo_events.events()` → `_breach_event` path, with `:213` as its
  > positive control (raise DO to 5.5 → nothing crosses → base survives). Both
  > predate this PLAN (PLAN-0016 Step 0). **A new below-direction assertion must
  > therefore state what it adds over these two, or it is a duplicate guard.**
  >
  > **(ii) The non-`reading` half is a real gap that current data cannot reach.**
  > The crossing filter's `event_type == "reading"` clause
  > (`demo_events.py:60`) is redundant with the `isinstance(measured_value,
  > int | float)` clause at `:61` on **every dataset the system has**: grepping
  > `"event_type":` across `tests/ services/ verticals/` and excluding `reading`
  > returns `alarm` / `transition` / `failure` / `low_stock`, and **not one of
  > them carries a `measured_value`** — they carry `description`. So the clause
  > is undiscriminating today and no test can redden on its removal. *(Static
  > grep evidence, s258 — NOT a witnessed RED; a probe through
  > `tools/probe_battery/` is owed before any AC closes on this.)* Making the
  > clause matter requires an event that does not exist, which is the
  > "manufactured state" this PLAN refuses elsewhere (AC-9's own ② REACH
  > annotation above).
  >
  > **(iii) The corpus is not yet an oracle of the system.** A golden trace is
  > `{name, source, event, model_output}` — a *recorded* `LlmJudgment`. The five
  > harness tests assert schema-validity, confidence range, handler resolution
  > and envelope composition: they compare the file to itself. Per CLAUDE.md §8
  > (*"an expected-value set … is not an oracle of the system until the system's
  > own output is scored against it"*), **a producer that only emits more such
  > files does not lift the corpus out of class C1.** Option (b) is therefore
  > scoped as: producer **plus** a scoring path the system's own output runs
  > through — and Step 7's probe is re-authored against that scoring path, since
  > the mutation it names today (`demo_events.py:62`) is a delegation the corpus
  > cannot observe.
  >
  > ✅ **DELIVERED (s258) — option (b), built as scoped above.**
  >
  > **The producer.** `tools/golden_trace/` — `refresh` recomputes each trace's
  > `expected_envelope` by running its recorded `event` + `model_output` through
  > the real `recommender._compose_llm_record`; `check` reports drift. This is
  > the mechanism defect (3) found missing: before it, `golden_trace` across
  > every `.py` in the repo matched only the consuming test module.
  >
  > **The scoring path — what actually lifts the corpus out of class C1.** The
  > harness gains invariant 5
  > (`test_golden_trace_matches_system_composition`): the envelope the system
  > composes **live** must equal the one recorded on disk. `created_at` is the
  > sole exclusion, and that is measured rather than assumed — composing the
  > same trace twice differs in exactly one of 16 top-level keys (s258
  > feasibility probe). Invariants 1–4 remain what they were: comparisons of
  > each file to itself.
  >
  > **The two traces.** `04-do-crash-below-direction-representative.json`
  > (aquaculture DO crash, 3.2 mg/L — keyed on `pond_id`, so it scores
  > composition against a **non-energy event shape**) and
  > `05-alarm-non-reading-representative.json` (an `alarm` carrying **no
  > `measured_value`**). Both are `representative`, the class traces 02–03
  > already established; no live capture, so **MS-S1 was not touched**.
  >
  > 🔴 **What these two traces do NOT claim**, stated so a later reader does not
  > over-read them: trace 04 does **not** pin the `below` comparison — that is
  > `recommender.crosses_threshold`, already covered per (i) above. Trace 05
  > does **not** pin the anchor filter's `event_type` clause — per (ii) that
  > clause is undiscriminating on current data, and manufacturing an event to
  > make it matter is refused. What both traces DO pin is the composition path
  > for event shapes the corpus previously could not express.
  >
  > **Witnessed RED** (`tools/probe_battery`, run `run-b9955b50`,
  > `PROBE-BATTERY: PASS` / `PROBE-COVERAGE: COMPLETE`, 0 gaps, 11 claims — 2
  > witnessed, 9 exempted with written reasons, tree restored byte-identical):
  > **P1** mutates the envelope `id` prefix inside `_compose_llm_record` →
  > invariant 5 reddens with `assert ['id'] == []` at its own site. **P3**
  > renames a trace's `expected_envelope` key → the precondition reddens.
  > **P2/P4** are their controls, both GREEN under the same mutations — the
  > green that rules out "something unrelated broke". One probe per assertion,
  > per CLAUDE.md §8.
- [x] **AC-10 [check] — every expressible gold case is compared to the real
  engine.** The nl-13 harness
  (`tests/benchmark/test_nl_query_feasibility_gold.py:220-244` — real engine,
  real adapter, real scorer, only the model transport stubbed) is extended to
  every non-ceiling case nl-01…nl-11 — **eleven** cases — each with its
  hand-authored structured translation. Today those eleven are checked only for
  internal self-consistency
  (`:68-89`, e.g. `expected_count == len(expected_ids)`) — **gold compared to
  gold**, the self-agreeing shape §8 forbids at a seam §8's wording does not
  reach. Any case inexpressible as a single structured query goes in an
  explicit in-test register with a written reason (an empty-reason entry fails
  the test). A mismatch against the engine is a **surfaced finding for Cray**,
  never a silent xfail and never a gold edit (LOCKED: the energy synthetic
  events do not change — `gold.yaml:64,:77,:145,:173,:218-224` hard-couple to
  them). Command: `uv run --no-sync pytest tests/benchmark/test_nl_query_feasibility_gold.py -q`.
  _[Corrected s241, `was an error`: this AC read "nl-01…nl-12" (and Step 8's
  heading "twelve more times") — but nl-12 is the gold set's ONLY
  `ceiling: true` case (`benchmarks/nl_query_feasibility/gold.yaml:190`, the
  honesty-no-data probe; corroborated by the well-formedness assertion
  `any(c["ceiling"] for c in cases)` at
  `tests/benchmark/test_nl_query_feasibility_gold.py:88`, which passes on
  nl-12 alone), so the non-ceiling remainder is **nl-01…nl-11, eleven cases**.
  nl-12 stays separately runnable via the scorer's ceiling lane if anyone wants
  it as a bonus, but is outside this AC's stated scope. Also recorded here so
  the next reader does not re-derive it: a circulating claim held that the two
  unruled silent drops in `services/engine/run_query.py` (`started_week`
  ignored; `group_by` never reaching `AggregateResult`) constrain this AC —
  measured FALSE s241: those live in the `pipeline_run` corpus compiler,
  `services/engine/nl_query.py` contains **zero** references to `run_query`
  (grep), and no gold case targets a run-corpus object type (the set's
  `expected_object_type` values are Asset / OperationalEvent / Site / Alert).
  They make ZERO nl-01…nl-11 cases inexpressible and must NOT appear in this
  AC's inexpressibility register.]_
  > **Closing evidence (Code, 2026-08-21 / s242,
  > [#1238](https://github.com/CrayJThiemsert/vero-lite/pull/1238), merged
  > `b453bef`).** `tests/benchmark/test_nl_query_feasibility_gold.py` grew
  > 245 → **428** lines (+184 insertions, **zero** production lines), all inside
  > that one module: `_HAND_AUTHORED_TRANSLATIONS` — eleven `StructuredQuery`
  > payloads for nl-01…nl-11, hand-authored and deliberately NOT derived from
  > gold (deriving either from the other would make the comparison circular) —
  > plus four tests: the partition test (every non-ceiling gold case is in the
  > table OR the register; both exclusions — nl-12 as the only `ceiling: true`
  > case, nl-13 keeping its own test — are derived from gold at runtime, never
  > restated), the written-reason test (a blank/whitespace reason fails), the
  > no-overlap test, and the engine-agreement test parametrized over the eleven
  > (a mismatch asserts a message containing `SURFACED FINDING` that names both
  > sides and says not to edit gold).
  > **The register shipped EMPTY — `_INEXPRESSIBLE: dict[str, str] = {}` — and
  > that emptiness is measured, not assumed:** a reconnaissance probe run
  > BEFORE any test was written returned `VERDICT=ALL_ELEVEN_REPRODUCE`
  > (correct 11, diverged 0, errored 0), so all eleven are expressible. No
  > surfaced finding exists, and no gold value was touched (LOCKED honoured).
  > **Witnessed RED, four ways — `VERDICT=ALL_FOUR_WITNESSED_RED`**, each probe
  > reddening its own test with the expected message, the file restored
  > byte-identical from `/tmp` (not via git), and the battery RE-RUN after
  > `ruff format` touched the file (a changed file invalidates the previous
  > RED): mistranslating nl-04 to `severity=warn` — the engine returns 2 warn
  > events instead of 1 critical, a behaviour change, not cosmetic — reddens
  > the grading assertion with `SURFACED FINDING` · dropping nl-07 from the
  > table reddens the partition test with `ungraded=['nl-07']` · registering
  > nl-07 with a blank reason reddens the written-reason test · putting nl-07
  > in both reddens the overlap test.
  > Gates at CI scope: `ruff check .` clean · `ruff format --check .` 647 files
  > · `mypy --strict services/ verticals/` 201 source files, no issues ·
  > `pytest -q` **4220 passed, 8 skipped** — baseline 4206 → **+14 exactly**
  > (11 parametrized + 3 structural), so nothing else moved.
- [x] **AC-11 [check] — negative money is pinned at a real seam.** The month-end
  ฿ aggregation seam (`services/db/repair_case_closeout.py` — confirmed by grep
  to carry ฿ amounts; internals read at execution, per Step 9) gets a test that
  drives a negative `Decimal` amount through the real producer→consumer path
  and pins ONE specific signed outcome: correct signed aggregation if the
  domain admits credits/refunds, or an explicit loud rejection if it does not —
  the step picks after reading the seam, and the test docstring states which.
  Today the repo has exactly one distinct negative `Decimal` literal and it is
  a DoA tier bound (`tests/services/engine/procedures/test_doa_tier.py:176`);
  sign handling in ฿ aggregation is untested. Command:
  `uv run --no-sync pytest tests/api/test_closeout_negative_money_scenario.py -q`
  (final module placement follows the house layout at execution; the command
  tracks the file).
  _[Corrected s241, `superseded by new info`: the command read
  `tests/services/test_closeout_negative_money.py`; the module landed at
  `tests/api/test_closeout_negative_money_scenario.py` — exactly the placement
  drift the parenthetical above pre-authorised, so the command now tracks the
  file that exists.]_
  > **Closing evidence (Code, 2026-08-19 / s240,
  > [#1226](https://github.com/CrayJThiemsert/vero-lite/pull/1226)).** A
  > four-test scenario, `tests/api/test_closeout_negative_money_scenario.py`,
  > whose module docstring opens *"A credit note keyed as a close-out, driven
  > into the month-end ฿ figure"* and names this AC. The pin chosen after
  > reading the seam is the **explicit loud rejection** (422 at the real
  > `POST /api/cases/{id}/closeout` producer, nothing stubbed on either side) —
  > and NOT because the domain lacks credits: it has them (ใบลดหนี้, Cray,
  > typed 2026-08-19). The record is append-only with **latest-wins**, so a
  > credit-note row would REPLACE the invoice it credits and the month-end ฿
  > figure would silently report the credit as the repair's entire cost — the
  > failure a completeness KPI structurally cannot see. The refusal is INTERIM
  > and says so at the seam; the schema that can hold an invoice and its credit
  > as two coexisting facts is PLAN-0111's subject.
- [x] **AC-12 [check] — a floor under the executed DB-test count.** *(Ruled by
  Cray 2026-08-17: close this as a count floor. Landed #1305; ticked s258 after
  re-running the AC's own command verbatim — it exits **1** with
  `4023 passed, 486 skipped` against a normal 8. Note the shape: pytest's own
  summary reports **nothing failed** and the process fails anyway, which is the
  session-finish floor doing its job.)* A session-finish check
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
- [x] **AC-13 [check] — the dead coverage floor stops existing.** *(Ruled by
  Cray 2026-08-17: delete, not arm. Landed #1305; ticked s258 after re-running
  the AC's own command — `git grep -n "fail_under" -- pyproject.toml` exits
  **1**, measured, not inferred from the PR body.)* `pyproject.toml:124` (`fail_under = 70`)
  is deleted: no `addopts` exists (`:109-116`) and `ci.yml:77` is a bare
  `pytest -q`, so coverage is never measured while the config reads as an
  enforced gate — a guard that reads as protection and is not. The
  `[tool.coverage.run]` scope (`:118-120`) and `show_missing` stay for
  on-demand local measurement; only the enforcement lie goes. Command:
  `git grep -n "fail_under" -- pyproject.toml` exits **1** (it exits 0 today).
  Any future *armed* coverage gate is a new decision for Cray, made against a
  measured number — not this PLAN's business.
- [x] **AC-14 [check] — the frozen `?v=` floor is replaced by a diff-aware
  gate, in the same PR.** *(Landed #1305; ticked s258 against all four of the
  AC's own reads: the unit suite is **6 passed**; `git grep -n "def
  test_every_edited_asset_got_a_cache_bust" -- tests/` exits **1** — retired,
  with a tombstone at `tests/api/test_ui_profile.py:725` stating why;
  `fetch-depth: 2` is at `ci.yml:43`; and the new step at `ci.yml:91` ran
  **success** on this PLAN's own closing PR.)* `tests/api/test_ui_profile.py:725-751` freezes
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

- [x] **AC-15 [evidence] — the CI bill is recorded.** The closing PR body
  records, per new CI step, the observed wall-clock delta on that PR's run.
  Recorded, **explicitly NOT a gate** — no threshold is enforced on these
  numbers; they exist so the later browser-plan discussion starts from
  measured cost, not vibes.
  > **Measured on this PLAN's closing PR** (#1307, run `33039045076`, gate
  > **585s** total, all 20 steps `success`). The two steps this PLAN added:
  > `JS assets parse (node --check)` (AC-1) **4s**; `Static assets carry a
  > fresh ?v= token (diff-aware)` (AC-14) **<1s**. Combined **~4s of 585s —
  > 0.7%** of the gate. For the browser-plan discussion the Out-of-Scope
  > section defers to: the dominant cost is `Full test suite (offline gate +
  > DB-backed tests)` at **483s (83%)**, and the rejected ~3-minute browser
  > stage would have been **~31%** on top of the whole gate — which is the
  > ground (b) that rejection rests on, now carrying a number.

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
  at drafting the 2-case seed meant nothing overflowed, so a browser stage
  added then would have been green and vacuous on day one; (b) protection is
  `strict:true`, so every PR already pays a full `gate` round — a ~3-minute
  browser stage on non-UI PRs is pure tax. When it lands it should be
  `workflow_dispatch` + a `ui` label, not a required check. LOCKED as to
  sequencing; the successor plan decides the rest.
  _[Corrected s241, `superseded by new info`: ground (a) was true on 2026-08-17
  and expired when AC-7 closed (s236, #1206) — the seed now holds **21** cases,
  one past the UI's `limit=20`, so the Phase B dependency is SATISFIED and (a)
  no longer argues for deferral on its own. The rejection still stands, resting
  on (b) plus the sequencing ruling; the LOCK is untouched.]_
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
(the rationale comment inside `seed_settled_history_case`), preserving the two
narrative cases and the truck-02 displacement design (the "live case DISPLACES
whatever the fixture had for that truck" comment inside `seed_demo_repair_case`)
untouched; idempotent and fail-soft like the existing helpers.
_[Corrected s241, `superseded by new info` (the second cite verified at review,
2026-08-20): this sentence cited `operate_seed.py:318-321` and the `:204-206`
region, both measured correct at drafting and both moved by AC-7's ~200 added
lines — on disk today `:318` holds a `status=CASE_STATUS_OPEN,` field and
`:204-206` sits inside `_stamp_run_subject`'s proposal loop, while the
rationale comment lives near `:512` in `seed_settled_history_case` and the
displacement comment near `:303-312` in `seed_demo_repair_case`. Re-anchored
by symbol + quoted comment, not by arithmetic on the old numbers.]_
Then write the overflow scenario
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

### Step 7 (B / AC-9): a producer, a scoring path, and two golden traces

_[Rewritten s258 after Cray ruled option (b). The prior text is preserved in
git history; it is `was an error`, not `superseded` — its two probes named a
mutation (`demo_events.py:62`) that is a delegation, and an oracle
(`test_eval_harness.py`) that reads static JSON and cannot observe it. Both
were measured unrunnable at s241 and re-verified s258. Executing them as
written would have produced the class-C1 guard this PLAN exists to remove.]_

Build `tools/golden_trace/` — the producer the corpus never had — with
`refresh` (recompute each trace's `expected_envelope` through the real
`recommender._compose_llm_record`) and `check` (report drift, exit 1). Measure
which envelope fields are reproducible **before** choosing what to pin, and
exclude only those that are not. Add invariant 5 to the eval harness: the
system's live composition must equal the recorded envelope. Backfill traces
01–03, then add the two new traces as `representative` (the class 02–03
established — no live capture, so no host-state gate applies). Split the
"expectation is recorded" precondition into its own assertion so an
unrecorded expectation fails loudly instead of letting the corpus go vacuous.

**Probe (a):** mutate the envelope `id` prefix inside `_compose_llm_record` →
invariant 5 reddens at its own site, while the precondition assertion stays
green under the same mutation (the control). **Probe (b):** rename a trace's
`expected_envelope` key → the precondition reddens, while a sibling trace's
stays green (the control). One probe per assertion; run through
`tools/probe_battery`, never a hand-rolled driver. Output changed: (a) the
composed envelope's `id`, hence the scoring verdict; (b) the presence of the
recorded expectation. Cost: inside pytest, not separately measured.

### Step 8 (B / AC-10): gold meets engine, eleven more times

_[Corrected s241, `was an error`: this heading read "twelve more times" and the
substep below read "nl-01…nl-12" / "twelve real-engine runs" — the non-ceiling
remainder is eleven; the measurement is in AC-10's correction annotation.]_

Parametrize the nl-13 harness over every non-ceiling case with hand-authored
structured translations; add the reasoned inexpressibility register.
**Measure-first substep:** run the extended comparison once BEFORE asserting;
any nl-01…nl-11 mismatch is written up as a surfaced finding for Cray (gold
wrong vs engine wrong is a ruling, not a guess), and the case enters the
register with that reason until ruled. The energy events are not touched
(LOCKED).
**Probe:** perturb one `expected_count` in a scratch copy of `gold.yaml` → that
case's comparison reds. Output changed: the scorer's verdict for the perturbed
case. Cost: not measured (eleven real-engine runs; record per AC-15).

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
