---
last_updated: 2026-07-22T22:32:13+07:00
session: 164
current_batch: "s164 — 1 PR: #859 PLAN-0091 filed Draft (the narrative→vertical scaffolder, `vero-lite scaffold`), 10 ACs / 8 Steps, create-shape only, gated on Cray's Step-0 adjudication."
current_actor: code
blocked_on: "PLAN-0091 is DECISION-gated on Cray's Step 0 (SD-1…SD-4); SD-1 may require an ADR first. main=f758509; suite 2995/7; mypy strict clean at 98 files; 0 open PRs; MS-S1 idle; dev Postgres UP."
next_action: "Nothing ordered — PLAN-0091 CANNOT build until Cray adjudicates Step 0 (SD-1…SD-4; SD-1 may need an ADR merged first). Others: PLAN-0088's 8-AC re-draft (ungated), the autonomy fork (decision)."
head_commit: f758509
recent_commits: [f758509, 74a49c2, caeda74, b39bd99, 1ce3546, 5f49023, a3ef955, db398bf, 20f2585, 2d34d80]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 164, 2026-07-22 (head_commit `1ce3546` → `f758509`) — a one-PR
> session whose real product was a REFUTATION, not a build: a 4-agent Explore
> fan-out re-ranked the five session-163 candidates against code and killed two
> standing claims before Cray picked the winner by typed AskUserQuestion.
> PLAN-0091 — the narrative→vertical scaffolder tool v1, `vero-lite scaffold` —
> is FILED at `Status: Draft`, 10 ACs / 8 Steps, CREATE-SHAPE ONLY, and CANNOT
> be built until Cray adjudicates its Step 0 (SD-1…SD-4).**
> **(the open.)** Orientation + a full sync matched the handoff on all six
> checks: `main=caeda74`, 0 open PRs, **2995 passed / 7 skipped** — the
> pre-committed read, hit exactly ⇒ `confirmed — prior intact` — `mypy
> --strict` clean at 98 files, ruff clean at CI scope, STATUS 55,745 B.
> **(the fan-out — two REFUTATIONS, the session's intellectual headline.)**
> **(a) The scaffolder was NOT greenfield.** The correct label is
> **brownfield-with-a-ratified-half**: **ADR-0024 is Accepted** and already pins
> the generation contract, and **PLAN-0040 already shipped the
> narrative→procedure pipeline** (`services/engine/procedures/generator/
> pipeline.py` S0–S6, the archetype REGISTRY, restricted draft types,
> `prose_lint`); the AT-2 breadth block was CANCELLED at N=4 and PLAN-0087 made
> a new AT-2 vertical zero-engine-diff. So the genuine gaps are **narrower than
> "a scaffolder"** — narrative→**ontology YAML** (no ADR covers it) and the
> **money spine**. **(b) PLAN-0088 has 12 defects, not 6**, and **ADR-0032 D2's
> pilot gate does NOT block it** — shape 2 is defined by *output*, Group A emits
> no proposal, and AC-11 enforces exactly that **statically** on five
> on-disk-verified symbols, so **Cray's L1 classification is correct**. What
> blocks Step 1 is the PLAN blocking itself: **AC-3 ⊗ AC-12 is a trilemma** —
> violate AC-3, violate its own Out-of-Scope, or introduce an unwritten `run_id`
> sort key that breaks `view-map.js`'s newest-first dependency (a **second `GET
> /runs` consumer** AC-12 never counted). **8 of 14 ACs need rewriting before
> any code.** Also grounded: **PLAN-0076 T1 is counter-indicated, not merely
> unqueued** — the PLAN itself calls it an "inert audit display-flag over-mark
> with zero live collisions", so building it is abstraction ahead of pressure,
> which **ADR-0031 D4.1 forbids**. **Tire is EXTERNALLY blocked** on a per-tyre
> data source (the ontology carries zero tyre representation; the GPS stream is
> per-truck). The multi-SP refinement is unmotivated at **N=0** (only two agents
> declare an SP, one each). **Cray then picked the scaffolder PLAN by typed
> AskUserQuestion**, over PLAN-0088 and PLAN-0076 T1.
> **(#859, `74a49c2` → merge `f758509`, `docs(plans)` — fast-forward, docs-only,
> 1 file +508.)** The dispatch **carried its spec inline because both spec
> inputs are gitignored** — the 14-row seam ledger and the 4-question intake log
> (`docs/research/private/2026-07-21-fleet-scaffold-{seam-ledger,question-log}.md`,
> cited by path only). Code verified the fact pack **BEFORE** dispatch and found
> **four drift corrections**, two of which make ledger rows **actively wrong**:
> **row 12 is DEAD** (`ComplianceCriterion` retired, `spec.py:876-884`;
> vocabulary is declared per vertical at `:1688`) and **the hand-wire count is
> 4, not 3** (PLAN-0090's mirror map `services/engine/cli.py:130`, pinned equal
> by `tests/services/engine/test_cli_registrars.py`). Standing rule for this
> spec: **cite the ledger, never the PLAN-0086 closeout**, whose tally says 6
> then enumerates seven (6+5+2=13≠14; the correct split is 7/5/2=14).
> **R2 found ONE defect, and its source was Code's own dispatch, not the
> drafter.** The intake round-trip cost was stated as "6m51s of 27m39s ≈ 25%" —
> **wrong twice over**: none of the interruption time is *inside* the hands-on
> number (every PLAN-0086 phase row has `wall == hands-on` and the rows sum to
> 27m38s, so all 6m51s falls in the 15m39s of wall that hands-on excludes), and
> 1m34s of it was spent **asking while work continued**, not idling. Corrected
> in place to **6m51s of 43m17s wall (~16%)**, of which **5m17s was
> fully-blocked idle (~12% of wall)**, with the correction **and its
> attribution** recorded inline in the PLAN. Everything else verified on disk,
> including the AT-2 fleet signature AC-7 pins on. **The drafter re-grounded
> Code's fact pack and reported no fifth drift**, with one precision worth
> keeping: the AT-2 cancellation **removes the bar but does not pre-approve
> generation**, so the PLAN makes the **affirmative** case (ADR-0024 OQ-8's
> typed-content precondition verified MET on disk) rather than citing the
> cancellation as approval.
> **(a Stop-hook misfire, observed live — evidence for the still-open autonomy
> fork.)** The hook dispatched "spawn `plan-drafter`" **while the `plan-drafter`
> it was asking for was already running**; Code declined via the trigger's own
> override clause. This is the **3rd misfire this session** and it **cleared
> BOTH existing layers**: the reason had real content (so #844's
> contentless-reason floor did not demote it) and it used no approval/merge
> vocabulary (so #843's prompt paragraph did not catch it). _Doc gap, still
> open: STATUS carries **no** Stop-hook misfire record for s163's three._
> **Verification / state:** `gate` PASS in 3m14s and **SHA-verified** (run
> `headSha` == PR head == `74a49c2`) before the merge, on Cray's typed
> instruction. **0 open PRs** at close; MS-S1 idle, no host-state change; dev
> Postgres UP; working tree clean but for the 2 KEEP untracked paths
> (`.claude/benchmark-results/`, `.claude/launch.json`). Commits: `74a49c2` →
> `f758509` (#859 merge, head_commit of record). Artifact:
> `docs/plans/0091-narrative-to-vertical-scaffolder-tool.md`, **Status `Draft`**.
> **Nothing is ordered next:** PLAN-0091 cannot start until Cray adjudicates
> SD-1…SD-4, and **SD-1's ruling may require an ADR merged first**; the other
> live candidates are PLAN-0088's 8-AC re-draft (ungated for Code) and the
> autonomy fork (a decision, not code).

> **Session 163 (second arc), 2026-07-22 (head_commit `1b942f5` → `1ce3546`) —
> a four-PR arc that filed, BUILT and CLOSED **PLAN-0090** inside one session:
> the fleet AT-3 **scheduled** calm path. Headline —
> `scheduled_pm_service_round` fires at 06:00 Asia/Bangkok as the
> `svc-fleet-scheduler` service principal and PARKS at the gated
> `schedule_service` for a human (RF-3), and its steps are **BYTE-IDENTICAL** to
> the manual `pm_service_round` — PROVEN, not asserted, by
> `test_spine_is_byte_identical_to_the_manual_path`, which compares dumped
> models, so a changed projection / `threshold_field` / direction / handler /
> autonomy / facet on either path goes RED. **Cadence is a trigger property, not
> a governance one:** the only difference between the two procedures is HOW a
> run starts.**
> **(#854, `06a93f0` → merge `2d34d80`, `docs(status)`.)** The s162 reconcile,
> bundled with the **R2 pointer-rule trim**: 9 RD rows + 6 Active TODOs
> compressed to ≤600-char pointers, and one Active TODO **RETIRED as discharged
> because it was FALSE, not stale** — s160's #845/#846 had already corrected all
> three artifacts it named. 59,697 → 53,758 B; headroom 5,839 → 11,778.
> **(#855, `bd44842` + `5e88450` → merge `20f2585`, `docs(plans)`.)** PLAN-0090
> filed, with the Step-0 SD ratifications recorded inline. The path is a
> **DISTINCT `procedure_id`, never a trigger flip** — the procurement donor's own
> reasoning: `trigger` is a single enum and a schedule descriptor is present IFF
> `trigger == schedule`, so flipping the manual path would break its manual runs,
> and SD-P3 skip-if-in-flight keys on `procedure_id`. The manual path stays
> runnable. The spine was **extracted** from the manual path at authoring time
> rather than retyped, so the byte-identity above is by construction.
> **(#856, `db398bf` → merge `a3ef955`, `feat(fleet_maintenance)` — the build,
> plus the L3 generic CLI fix.)** **A CORRECTED claim, recorded as an error and
> not silently dropped:** Code's own dispatch said an unwired fleet daemon "ticks
> but 409s at resolve". It does not — `_run_scheduler` calls
> `registry.get_procedure_executors()` **unguarded** (`cli.py:151`) and the
> registry raises `RegistryError` (`registry.py:114-121`), so the daemon
> **CRASHED AT STARTUP** for five of six verticals and never ticked at all. The
> `plan-drafter` caught it at drafting; Code verified both files at R2. The fix
> **replaces a rotted docstring with an assertion**: `_register_executor_factory`
> now dispatches over a six-vertical map **mirroring** (never importing)
> `services/api/main.py:_PROCEDURE_EXECUTOR_REGISTRARS` — `services/engine/` must
> not depend on `services/api/`, and importing the app would drag FastAPI into
> daemon startup — with a **set-equality tripwire** pinning the two vertical sets
> equal, so a 7th vertical wired into one and not the other goes RED. Proven
> **non-vacuous**: a vertical was removed from the map → RED → restored from a
> `/tmp` backup byte-identically (`cmp -s` clean), never `git checkout`.
> **(#857, `5f49023` → merge `1ce3546`, `docs(plans)`.)** Closed out **COMPLETE
> at 7/7** and archived to `docs/plans/done/0090-fleet-scheduled-calm-path.md`.
> **THE MEASUREMENT: 16m13s hands-on**, no interruptions (YAML 2m19s /
> catalog+census 2m44s / CLI+tests 5m16s / gate 3m55s / smoke 1m59s). The MS-1…
> MS-6 protocol was written into the PLAN **before** Cray ratified SD-2, so it
> could not have been shaped around a result it had not seen; the artifact is
> gitignored — `docs/research/private/2026-07-22-fleet-scheduled-timing-log.md`,
> cited by path only. **THE MS-6 CAVEAT IS BINDING AND TRAVELS WITH THE NUMBER
> WHEREVER IT IS WRITTEN, INCLUDING HERE:** 16m13s is a **LOWER BOUND** under
> maximally favourable conditions — the same operator who built the manual path,
> a shipped donor to copy, all scheduler machinery already shipped, every
> decision pre-ratified. It does **NOT** measure machinery construction, blind
> intake, or a fresh operator, and it is **NEVER** to be presented summed with
> PLAN-0086's 27m39s or PLAN-0089's ~14 min — three claims under three
> conditions, companions not addends.
> **Two deviations, recorded as deviations rather than absorbed. D-1:** AC-5's
> "the PLAN-0089 suite stays green UNMODIFIED" could not hold literally — that
> suite pins the vertical's procedure-id set by SET-EQUALITY, so a third
> procedure turns it RED by construction (the guard working as designed; every
> behavioural assertion about the hero is byte-untouched, only the census line
> moved). **D-2:** part of AC-3 ("a human resolution completes it") was written
> **after the clock stopped** and is therefore NOT inside the 16m13s — disclosed
> because a number that silently excludes required work is worse than a slower
> honest one.
> **Live evidence (AC-6) — and it is evidence, never a gate.** The daemon
> registered the schedule, computed `next_fire` = 06:00 Asia/Bangkok **from the
> cron unaided**, fired on a **backdated slot** (never an edited cron), parked at
> `schedule_service` with verdicts `['breach','ok','ok']` — identical to the
> offline run AND to PLAN-0089's manual run — recording `actor_kind: "service"`
> on behalf of `req-mechanic-tom`, then re-armed to the next slot. **A local boot
> is NOT a host-state action** (CLAUDE.md §8 scopes that to MS-S1 and
> host/global config; s161 recorded over-applying it here as an error).
> **The merge-commit gate, against a pass/fail read fixed BEFORE the run:**
> `a3ef955` = **2994 passed / 7 skipped**, `mypy --strict` clean at 98 files,
> ruff clean at CI scope — expected 2984 baseline + 10 new tests = 2994, hit
> exactly ⇒ **`confirmed — prior intact`**; **2995/7** after the closeout's added
> test. The merge commit's tree is **byte-identical** to the tested commit's
> (both `d085400b9bc5a469a176df40e01806f121651ae6`), so the pre-merge live
> evidence IS merge-commit evidence — proven, not assumed.
> **Cray-ratified typed selections (AskUserQuestion), all BEFORE the work they
> govern:** L1 cron `0 6 * * *` Asia/Bangkok · L2 `owning_person_id:
> req-mechanic-tom` (accountability parity, PLAN-0065 SD-5(b); NOT an SoD
> requester) · L3 fix `cli.py` generically · SD-1 `svc-fleet-scheduler` · SD-2
> yes, timed. STATUS: 55,745 B.

> **Session 162, 2026-07-22 (head_commit `e6bb8c8` → `1b942f5`) — a four-PR
> arc, two of it recorded LATE: #850 (the `PROCEDURE_ARCHETYPES` re-key) and
> #851 (PLAN-0089 filed) both merged during s161 and were never mentioned by
> the s161 reconcile; then PLAN-0089 was BUILT (#852) and CLOSED at 6/6 ACs +
> archived (#853, merged at the s163 open). The headline: `fleet_maintenance`
> gained the AT-3 calm path `pm_service_round` in **~14 min hands-on**, with
> **ZERO engine diff — PROVEN, not asserted** (`git diff df1982a..a8d679d --
> services/engine/` is EMPTY).**
> **(#850, `333f6f6` → merge `514dc1f`, `fix(api)` — recorded LATE, built by a
> spawned chip session, not the main one.)** `PROCEDURE_ARCHETYPES` was keyed
> on a bare `procedure_id`, but a `procedure_id` is unique only *within* a
> vertical (`services/engine/procedures/schedules.py:31-33`), so two verticals
> naming a procedure alike silently served each other's archetype —
> demonstrated repro: `energy` asking for `low_stock_reorder_round` received
> **procurement's AT-3**. A latent pre-existing bug, not a regression: the
> canonical catalog had always used `<vertical>.<procedure_id>`, so the mirror
> had drifted off its own canonical. Re-keyed to **`(vertical,
> procedure_id)`**, with a new `archetype_for()` as the single read point and a
> set-equality tripwire; +3 tests. The non-vacuity probe was done the right
> way — the old shape restored from a `/tmp` backup, never `git checkout`
> (which would have wiped the edit under test and produced a false PASS).
> **(#851, `f1cce45` + `fa43e6b` → merge `df1982a`, `docs(plans)` — also
> merged during s161, also recorded LATE.)** **PLAN-0089** filed: the fleet PM
> calm path as a *measured* "extend an existing vertical" experiment, with all
> **3 SDs Cray-ratified inline** — SD-1 manual trigger, SD-2 manual hand-port
> (no generator), SD-3 ride `Truck` with an **absolute**
> `next_service_due_km`, take the **third** truck, and name it
> `pm_service_round`, never `tire_*`.
> **(#852, `2904d77` + `610061b` → merge `a8d679d`, `feat(fleet_maintenance)`
> — PLAN-0089 BUILT.)** `fleet_maintenance.pm_service_round`, the **AT-3 calm
> path**: `read_odometer` → `judge_service_due` (`threshold_field:
> next_service_due_km`, `direction: above`) → gated `schedule_service`. Cray's
> **M-5 intake this session**: a 100,000 km service interval, all classes. +4
> tests; the counted-prose census moved **11 → 12**.
> **(#853, `b1d877f` → merge `1b942f5`, `docs(plans)` — merged at the s163
> open, head_commit of record.)** PLAN-0089 closed out `Draft` → **COMPLETE at
> 6/6 ACs** against fresh on-disk evidence, with a Closeout section, and
> archived to
> `docs/plans/done/0089-fleet-calm-path-extend-an-existing-vertical.md`.
> **(the measured number + its BINDING caveat.)** ~14 min hands-on to extend an
> existing vertical; the log lives at
> `docs/research/private/2026-07-22-fleet-extension-timing-log.md` —
> **gitignored, cite by path only**. **M-6 travels with the number and is
> BINDING: it is a lower bound under maximally favourable conditions, and it
> must NEVER be summed with PLAN-0086's 27m39s as one workflow.**
> **(what the instance taught the archetype.)** AT-3's catalog entry was too
> narrow and was **GENERALIZED** — "read stock, judge vs a reorder point" →
> "read a measure, judge vs a per-entity threshold". This instance **inverts
> the direction** (odometer *above* a ceiling vs stock *below* a floor), which
> is exactly what showed the archetype's signature is the **per-entity band +
> single gate**, not stock semantics. **N stays 4:** the AT-2 signature counter
> counts AT-2 signatures only, and `pm_service_round` is AT-3 — invisible to
> that counter by construction.
> **Verification.** Whole surface `df1982a..1b942f5` = 11 files / +496 / −37.
> AC-3's zero-engine-diff is proven by the EMPTY `git diff df1982a..a8d679d --
> services/engine/` (re-verified this session), not by prose. Offline gate on
> the merge commit `a8d679d`: `pytest tests/` = **2978 passed / 8 skipped / 5
> failed** — the 5 are the known **pre-existing worktree false-REDs** in
> `tests/handoffs/` (they pass in the main tree and in CI), not a regression;
> `mypy --strict services/` clean (98 files); ruff clean. **AC-5 live park
> (evidence, never a gate):** `run-0c69e3054102` read back from Postgres —
> `waiting_human` at `schedule_service`, verdicts `{truck-01: ok, truck-02:
> breach, truck-03: ok}`, handler `schedule_pm_service`, trace kinds
> `['action_proposed']` ONLY — **no** `advisory_recommendation` /
> `doa_tier_resolved` / `governed_kind`. That absence is **BY CONSTRUCTION,
> not by never-raising**: `GovernanceActionExecutor.execute` branches on
> `step.governance_content` and delegates straight to the base executor, and
> the advisory builder is invoked only inside `_doa_tier`
> (`services/engine/procedures/governance_step.py:183-191`, `:235-238`).
> **Process fact worth one clause (no commit).** A parallel session had already
> filed AND merged PLAN-0089 while s162 dispatched its own `plan-drafter`
> draft — caught only at `git fetch` before committing. Standing correction:
> `git fetch origin main` + `gh pr list --state open` **before** drafting any
> governance artifact. Commits: `333f6f6` → `514dc1f` (#850) → `f1cce45` →
> `fa43e6b` → `df1982a` (#851) → `2904d77` → `610061b` → `a8d679d` (#852) →
> `b1d877f` → `1b942f5` (HEAD of `main`, #853 merge, head_commit of record).

> **Session 161, 2026-07-22 (head_commit `0c9cdeb` → `e6bb8c8`) — a one-PR
> strategy-to-PLAN session: PLAN-0088 filed Draft (#848, `docs(plans)`) — the
> cross-run read substrate + run-insight readers. Cray's opening question (once
> we have enough pipeline-run data, how do those data + the ontology feed an LLM
> to create customer value?) grounded out to ONE architectural shape, not a menu
> of features: the repo records everything PER-RUN and aggregates NOTHING across
> runs.**
> **(the grounded finding.)** `pipeline_runs` / `step_results` already carry
> `step_principals`, `governance_snapshot`/`_hash`, `duration_ms`, `artifact`,
> `reasoning_trace` and `audit` per run — but the only SQL aggregate anywhere in
> `services/` is the audit-chain length count
> (`services/api/routers/audit.py:54`), and `GET /runs`
> (`services/api/routers/runs.py:273-331`) materializes **every** run into
> Python and counts steps in dicts. That read path does not survive the "enough
> run data" premise, so the substrate — not a feature list — is the work.
> **(two forks Cray ratified by typed selection; they are the PLAN's LOCKED
> constraints.)** **L1 — "Group A" is NOT Shape 2** (NL query over runs, ฿ ROI
> narrative, bottleneck / cycle-time, audit-readiness): it emits no typed
> improvement proposal, so it extends Shape 1's `monitor` leg and does **not**
> trip the **ADR-0032 D2 pilot gate**. The separation test is **mechanical, not
> documentary** — AC-11 is a static guard over the substrate, the insights
> router and the run-query compiler asserting no write primitive, no import of a
> five-symbol proposal/write-path deny-list (each symbol verified on disk), and
> no `sqlalchemy` import engine-side. **L2 — build Group A and *prove* the
> substrate can express Group B's questions; do NOT build Group B.** Group B
> (band/DoA recalibration, refusal mining, procedure generation) **is** Shape 2
> and stays pilot-gated; the proof is four executable query-shape tests (AC-10),
> not prose.
> **(two hazards PINNED, not inherited.)** **Run ordering is unsound by the
> code's own admission** (`runs.py:291-294`: `started_at` "is a wall clock that
> is not monotonic on this box"), and the deferral doctrine pinned in
> `tests/services/db/test_load_run_ordering_guard.py:29-49` says the
> monotonic-sequence-column fix deserves its own PLAN — *"if a correctness path
> ever starts depending on either ordering, the sequence-column PLAN stops being
> optional."* PLAN-0088 therefore stays on the safe side: order-insensitive
> aggregates only, day-or-coarser buckets, no cross-row wall-clock arithmetic,
> plus an AST tripwire (AC-3) forbidding `ORDER BY` on raw wall-clock columns.
> **The sequence-column PLAN is explicitly still UNOPENED.** Second hazard:
> **cross-currency sums are made unrepresentable, not merely checked** — the ฿
> rollup's group key structurally includes `currency`
> (`EconomicImpact.currency`, `economic_impact.py:63`; THB-only in v1 per
> ADR-0030 OQ-4) and the report model carries **no cross-currency total field**.
> **(process note — the drafter corrected the reviewer three times and was right
> each time.)** The PLAN was authored by the in-harness `plan-drafter` (ADR-013
> D1) from a Code-authored, Cray-ratified dispatch; Code reviewed it against the
> code in **two rounds** and ordered three amendments (corpus vertical scoping,
> test-corpus size, a runnable predicate for AC-11). The drafter corrected two
> line ranges in Code's own dispatch and — substantively — the framing of the
> currency risk: Code's R2 tied it to vertical separation; the drafter separated
> cross-vertical **scope** (a business-honesty risk → stamp the report with the
> declared vertical) from cross-currency **summation** (a correctness risk → key
> on the facet's own `currency`). Vertical separation was never the right guard
> for currency, even accidentally.
> **(also this session, no commit — recorded because it is evidence for a
> standing candidate.)** The Stop hook emitted a directive `reason` **twice** on
> turns where nothing had been ordered: first *"Continue drafting ADR-0032
> content"* (work Code is G1-gate-forbidden to do), then *"Proceed with
> reconciling the status of s160 and rotating the s157 note"* (real pending work,
> but picking one branch of a two-option question Code had just put to Cray).
> Code declined both. **Neither shape is caught by #844's contentless-reason
> floor** — both name a concrete action, and the floor only demotes a reason that
> names none. Direct material for the still-missing
> `.claude/autonomy-triggers.md` approval/merge row.
> **Verification:** #848 is docs-only (1 file, +505 lines) — CI `gate` PASS in
> 3m12s, SHA-verified (run head == PR head ==
> `0dce906c48395ce9e11dee71e6503f030eda0066`) before merge; no suite re-run
> needed (docs-only). Artifact:
> `docs/plans/0088-cross-run-read-substrate-and-run-insight-readers.md`, **Status
> `Draft`** — deliberately not `Accepted`, which would G1-gate the PLAN's own
> closeout. Commits: `0dce906` (build) → `e6bb8c8` (HEAD of `main`, #848 merge,
> head_commit of record — `docs(plans):` counts as substantive; only
> `docs(status):` is excluded).

> _Rotation note (session-164 reconcile — the PLAN-0091 filing, 2026-07-22,
> `docs(status):`): added the **Session 164** CF block and rotated the OLDEST —
> the **Session 160** block (the four-PR hook-hardening + doc-truth session,
> #843 / #844 / #845 / #846) — to the Current-Focus rotation base
> `docs/status-archive/2026-h1-current-focus.md`. Rotating it is what **R2
> requires**, not a headroom judgement: the 4 most-recent sessions are now **164
> / 163 / 162 / 161**, so the s160 block fell **outside** the window. CF
> arithmetic: **4** real blocks → +1 = 5 → −1 = **4 blocks** (well under the
> 8-block cap). _(A naive `^> \*\*Session` grep over-counts: a WRAPPED line
> inside a rotation note also starts that way; the real headers carry a date and
> a `(head_commit …)`.)_ Recent Decisions gained ONE row — the s164 PLAN-0091
> filing, written at ≤600-char pointer length **from birth** — and rotated its
> ONE OLDEST, the **s153-155** row (#822's runbook demo beat / s154's
> zero-commit Cerebras-KB read / #823's confidence-badge removal), to the
> rotation base `docs/status-archive/2026-h1-status.md`; RD is back to **10
> rows**. The rotation-note trail was carrying **two**; this pass rotates the
> OLDER (the first session-163 reconcile note) to the same base and adds this
> one, so the trail stays at **two**. **Nothing was re-trimmed:** the R2
> pointer-rule pass landed in #854 (s163) and the RD rows plus Active TODOs are
> already at pointer length. **STATUS was 55,745 B before this reconcile**
> (caller-measured); the net of this pass is a SHRINK — one CF block and one
> rotation note out, one CF block and one note in — and the caller re-measures
> against the 64 KB R1 ceiling. Per the STATUS.md Rotation Policy (R1/R2/R4)._
>
> _Rotation note (session-163 reconcile #2 — the PLAN-0090 arc, 2026-07-22,
> `docs(status):`): added the **Session 163 (second arc)** CF block (PLAN-0090
> filed #855 → BUILT #856 → CLOSED at 7/7 #857, on top of #854's reconcile +
> pointer trim) and rotated the OLDEST CF block — **Sessions 158 + 159**
> (PLAN-0087, the ADR-0031 D3 gate seam's criterion-vocabulary half, #840/#841)
> — to the Current-Focus rotation base
> `docs/status-archive/2026-h1-current-focus.md`. Rotating it is what **R2
> requires**, not a headroom judgement: the 4 most-recent sessions are now **163
> / 162 / 161 / 160**, so the s158+159 block fell **outside** the window. CF
> arithmetic: **4** real blocks → +1 = 5 → −1 = **4 blocks** (well under the
> 8-block cap). _(A naive `^> \*\*Session` grep over-counts by one: a WRAPPED
> line inside the session-161 rotation note also starts that way; the real
> headers carry a date and a `(head_commit …)`.)_ Recent Decisions gained ONE row
> — the s163 PLAN-0090 arc, written at ≤600-char pointer length **from birth** —
> and rotated its ONE OLDEST, the **s152** row (PLAN-0083, the procurement
> ontology↔CSV column drift closed at the `FastenalCsvAdapter` seam, #818/#819),
> to the rotation base `docs/status-archive/2026-h1-status.md`; RD is back to
> **10 rows**. The rotation trail carried **two** notes: the older —
> **session-161 reconcile** — was rotated to the same base (R4 consolidation) and
> this note added, so the trail stays at **two**. **Nothing was re-trimmed:** the
> R2 pointer-rule pass landed in #854 earlier this same session, and the Active
> TODOs plus the remaining RD rows are already at pointer length. **STATUS:
> 55,745 B** (caller-measured, not estimated), against the 64 KB R1
> ceiling. Per the STATUS.md Rotation Policy (R1/R2/R4)._

> _Older content rotates out of this file per the **STATUS.md Rotation Policy (R1-R7)** in [`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md) (Lesson #23): Current Focus keeps the 4 newest sessions (<=8 blocks); Recent Decisions keeps the last 10 rows. Rotated blocks/rows live in [`docs/status-archive/`](status-archive/) and git history (Tier 3). Layout — **two separate chains, both with letters ascending with time and the base holding the recent window**: the rotation archive `2026-h1b` → `c` → `d` → `e` → `f` → `2026-h1-status.md`, and the Current-Focus-only `2026-h1b` → `c` → `2026-h1-current-focus.md`. Rotations append to the two bases. **Grep the directory, not a filename** — the chain is one corpus and which file holds a given block is an artifact of where the ~192 KB R4 bar happened to fall. _[Chain created 2026-07-17 (s144): the single `2026-h1-status.md` had reached 592,577 B, 2.3x R4's cap, and the new guard (#789) forced the split.]_

## Prior focus (archived)

PLAN-003 Phase 1 (ontology engine + 5 emitters), PLAN-0005 Phase 2
(OCT engine runtime layer), PLAN-0006 (LLM reasoning hook),
PLAN-0007 Phase 1 (harness autonomy layer — deterministic floor),
and **PLAN-0008 Phase 2 (harness autonomy layer — probabilistic /
classifier-mediated engine on top of Phase 1)** are all **merged and
moved to `docs/plans/done/`**. The Cowork-as-Tier-1 trial that ran as
the test-bed across the earlier batches **concluded** — ratified
permanently by **ADR-009** (Cowork = merged Tier 0 + Tier 1 workspace;
commits stay Code-exclusive). PLAN-004 Phase A (handoff frontmatter
schema + tooling) also landed; Phase B/C remain deferred (backlog).
Full detail lives in `docs/plans/done/`, the Recent Decisions table
below, and git history.

## Recent Decisions (last 10)

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-22 | **s164 — PLAN-0091 filed Draft (#859, `docs(plans)`): the narrative→vertical scaffolder (`vero-lite scaffold`), 10 ACs / 8 Steps, create-shape only — BUILD-BLOCKED until Cray adjudicates Step 0 (SD-1…SD-4; SD-1 may require an ADR first).** A 4-agent Explore fan-out REFUTED two claims: the scaffolder is **brownfield-with-a-ratified-half** (ADR-0024 pins the generation contract; PLAN-0040 shipped narrative→procedure), and **PLAN-0088 has 12 defects, not 6** — the pilot gate does NOT block it, its own **AC-3 ⊗ AC-12 trilemma** does; 8 of 14 ACs need rewriting. Full narrative: the Session-164 CF block above | `f758509` (#859 merge, head_commit of record) / `74a49c2` (the filing commit) / `docs/plans/0091-narrative-to-vertical-scaffolder-tool.md` (Draft, Step 0 unadjudicated) |
| 2026-07-22 | **s163 — PLAN-0090 filed (#855) → BUILT (#856) → COMPLETE 7/7 + archived (#857): `fleet_maintenance.scheduled_pm_service_round`, the AT-3 SCHEDULED calm path — 16m13s hands-on, steps BYTE-IDENTICAL to the manual path (PROVEN by a dumped-model test).** MS-6 BINDING: a LOWER BOUND, never summed with PLAN-0086's 27m39s or PLAN-0089's ~14 min. A DISTINCT `procedure_id`, never a trigger flip. + the L3 CLI fix: the unwired daemon CRASHED at startup (not "409s at resolve"); a set-equality tripwire now mirrors `main.py`. Gate on `a3ef955`: 2994/7. Full narrative: the Session-163 CF block above | `1ce3546` (#857 merge, head_commit of record) / `a3ef955` (#856 build) / `20f2585` (#855) / `2d34d80` (#854 reconcile + trim) / `docs/plans/done/0090-fleet-scheduled-calm-path.md` (COMPLETE, 7/7) |
| 2026-07-22 | **s162 — PLAN-0089 filed (#851) → BUILT (#852) → COMPLETE 6/6 + archived (#853): `fleet_maintenance.pm_service_round`, the AT-3 calm path, as a measured "extend an existing vertical" experiment — ~14 min hands-on, ZERO engine diff PROVEN (`git diff df1982a..a8d679d -- services/engine/` EMPTY).** M-6 BINDING: a lower bound, never summed with PLAN-0086's 27m39s. + #850 `fix(api)` re-keyed `PROCEDURE_ARCHETYPES` on `(vertical, procedure_id)`. AT-3 GENERALIZED to "a measure vs a per-entity threshold"; N stays 4. Gate on `a8d679d`: 2978/8/5. Full narrative: the Session-162 CF block above | `1b942f5` (#853 merge, head_commit of record) / `a8d679d` (#852 build) / `df1982a` (#851) / `514dc1f` (#850) / `docs/plans/done/0089-fleet-calm-path-extend-an-existing-vertical.md` (COMPLETE, 6/6) |
| 2026-07-22 | **s161 — PLAN-0088 filed Draft (#848, `docs(plans)`): the cross-run read substrate + run-insight readers.** Two Cray-ratified TYPED forks are the PLAN's LOCKED constraints: L1 — "Group A" is NOT Shape 2 and does NOT trip the ADR-0032 D2 pilot gate, proven by a STATIC guard (AC-11), not prose; L2 — build Group A + PROVE the substrate expresses Group B (AC-10) but do NOT build Group B, which stays pilot-gated. Wall-clock ordering hazard PINNED not inherited (AC-3 AST tripwire); the sequence-column PLAN stays UNOPENED. Full narrative: the Session-161 CF block above | `e6bb8c8` (#848 merge, head_commit of record) / `0dce906` (build) / `docs/plans/0088-cross-run-read-substrate-and-run-insight-readers.md` (Draft) |
| 2026-07-22 | **s160 — four PRs hardening the Stop hook and the AT-2 doc record: #844 the CONTENTLESS-REASON FLOOR (complement to #843, landed s159 unrecorded); #845 AT-2 corrected to N=4 + a cross-procedure `step_id`-scope guard; #846 (`plan-drafter`, G1) ADR-0032 re-grounded + a dated ADR-0025 D7 OUTCOME amendment, its "N ≥ 2" decision text deliberately NOT rewritten.** Two premises are now pinned in code, not prose: `_RETRIGGER_N` is retired, and PLAN-0087's "zero live `step_id` collisions" is wrong — both carried by the guard docstrings cited right. Full narrative: the Session-160 CF block above | `0c9cdeb` (#846 merge, head_commit of record) / `d7bbb8b` (#845) / `c42abe4` (#844) / `0090161` (#843) / `tests/services/engine/procedures/test_sod_step_id_scope_guard.py` + `tests/services/engine/procedures/test_at2_signature_retrigger.py` + `docs/adr/0025-at2-managerial-layer.md` (D7 amendment) |
| 2026-07-21 | **s158 + s159 — PLAN-0087 BUILT (#840) then CLOSED at 8/8 ACs + archived (#841 `docs(plans)`): the ADR-0031 D3 gate seam's CRITERION-VOCABULARY half — `ComplianceCriterion` RETIRED from engine code, a vertical DECLARES its own `rule_gate` vocabulary in `procedures.yaml`, so a new AT-2 vertical ships its gate with ZERO engine diff (PROVEN by AC-1's fixture-criterion pair, not prose).** Behaviour-preserving — no pinned governance hash moved. Cray-ratified SD-1 = (a) (typed): the procedure-aware `ExecutorFactory` half stays owned by PLAN-0076 T1, its AC-6 guard ARMED. Full narrative: the Sessions 158+159 CF block above | `c6eec65` (#840 merge) / `e55f2b8` (head_commit of record, #841) / `services/engine/procedures/spec.py` + `tests/services/engine/procedures/test_declared_criterion_vocabulary.py` + `docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` (COMPLETE, 8/8) |
| 2026-07-21 | **s157 — PLAN-0086 COMPLETE (#838 `feat(verticals)`): the narrative→pipeline scaffolder run as a TIMED MANUAL baseline — a dirtied customer monologue → a live, governed, human-gated pipeline on the 6th vertical `fleet_maintenance` in 27m39s hands-on. AC-7 caveat, BINDING: a LOWER BOUND (Code drafted the pre-dirtied narrative).** ADR-0025 D7's AT-2-generator deferral CANCELLED at N=4 (Cray-ratified, typed); `_RETRIGGER_N` RETIRED, replaced by `test_at2_extraction_obligation_is_owned` (PLAN-0076 T1 owns). Full narrative: the Session-157 CF block, rotated to `docs/status-archive/2026-h1-current-focus.md` | `79358c6` (HEAD, #838 merge) / `a2ef45e` (build) / `verticals/fleet_maintenance/` + `tests/services/engine/procedures/test_at2_signature_retrigger.py` (guard replacement) + `docs/plans/0086-fleet-vertical-timed-manual-scaffold.md` (closeout pending) |
| 2026-07-21 | **s156 — PLAN-0085 "Advisory Gate Recommendation (AI-Transition Rung 1)" filed → 5 SDs Cray-ratified → BUILT → closed in ONE day (#831/#832 `docs(plans)`, #833 `feat(engine)`, #834 closeout): an advisory recommendation with grounded reasons at procurement's `doa_tier` approval gate — SHOWN, NEVER routes (the ADR-0019 determinism fence, now CI-pinned).** All 5 SDs = the draft rec; new `gate_advisory.py` (never-raise, ADR-0030 D5); Monitor gate-panel block, NO score (the #823 trust shape). Full narrative: the Session-156 CF block, rotated to `docs/status-archive/2026-h1-current-focus.md` | `2f46fc9` (#833 BUILT, head_commit of record) / `63009c3` (#834 closeout, main HEAD) / `8809776` (#831) / `d679036` (#832) / `services/engine/procedures/gate_advisory.py` + `docs/plans/done/0085-*.md` (archived, 8/8) + `docs/runbooks/run-oct-demo.md` §3e |
| 2026-07-21 | **s156 — the demo rehearsal (carried s153→155) PERFORMED + PASSED (Cray, Beats 1-5 on 8101), which GATED the PLAN-0084 closeout (#830 `docs(plans)`, 9/9 ACs + archived); + a map-label UI fix (#829 `fix(ui)`).** Cray then opened the two-view **AI-Transition** frame (LLM at the approval gate; narrative→pipeline scaffolder) and ratified the SEQUENCE: View-1 (Rung 1 = PLAN-0085) → reshape View-2 → build View-2. A model-economy policy ratified (private memory, not a repo change): Fable for complex planning/research, Opus 4.8 + Extra for execution/coding-to-plan. Full narrative: the Session-156 CF block, rotated to `docs/status-archive/2026-h1-current-focus.md` | `ad39774` (#830) / `19f5caa` (#829) / `docs/plans/done/0084-*.md` (archived, 9/9) + `.claude/handoffs/session-156/2026-07-21-0851-*-ai-transition-two-views.md` |
| 2026-07-20 | **s155 (late) — PLAN-0084 shipped end-to-end in one arc (#825 filed Draft → #826 all 5 SDs Cray-resolved → #827 `feat(demo)` BUILT): map↔monitor run linkage (runs stamp `trigger_context["subject"]`; the map direct-fetches `/runs`; node-panel "Open in Monitor →") + opt-in seed rotation (`--asset`/`--rotate`).** Headline = SD-F, Cray-ratified mid-build — the PLAN's grounding `was an error`: `register_procurement_adapter` now registers the `FastenalCsvAdapter` (split-brain demo closed). Live-verified on 8101. Full narrative: the Sessions 153+154+155 CF block, rotated to `docs/status-archive/2026-h1-current-focus.md` | `25b31e2` (HEAD, #827 merge) / `45fcba1` + `64119b9` (build) / `e5f3ede` (#826 merge) / `628bfa1` (#825 merge) / `docs/plans/0084-map-monitor-run-linkage-and-seed-rotation.md` (Draft, 6/6 SDs resolved) + `verticals/procurement/data_adapter/__init__.py:99` + `docs/runbooks/run-oct-demo.md` §3d |

## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13; guarded trial (parallel to ADR-012) — verdict **continue-with-adjustments**. Run 1 (energy, s93) + Run 2 (supply-chain, s94) both COMPLETE, S-checks all PASS against pre-committed oracles, no R-PS trigger fired; C-1..C-3 CONFIRMED → **no open partner-sim debt**. ADR-011 audit stays gated on a REAL partner conversation (R3: SYNTHETIC provenance INFORMS but never TRIGGERS it). Full record: `docs/adr/0020-*.md` + the gitignored run packages `docs/research/private/2026-07-02-partnersim-run{1,2}-*.md`. _(Full prior narrative — the ~8 schema-mismatch findings, both run details, cross-run synthesis — archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **Procurement vertical — GO + SHIPPED (PLAN-0036 Fastenal, Stage 1):** 4th vertical greenlit (s75); PLAN-0036 drafted + merged Draft (#412, `7a7c036`; SD-1…SD-5 confirm-all). Demo target = Fastenal Thailand (auto-parts / EEC); **hero** = asset-failure → governed emergency sourcing, **calm-path** = low-stock reorder. Stage 1 = a PLAN-only pure-config plugin on the ADR-016 engine (zero `services/` core edit; CQ-1 / ADR-0023). **Pitch** = asset-ontology-triggered governed sourcing (native ontology ADR-008 + engine ADR-016), NOT the commoditized "governed"/"cross-vertical" claims. Full record: `docs/plans/0036-*.md` + the s72 de-risk dossier `docs/research/private/2026-06-22-procurement-*.md` (5 files: spec-expressiveness, GTM, asset-aware incumbent scan, AI-sourcing teardown, platform-incumbent deepdive). _(Full prior narrative archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [ ] **The AT-2 extraction — only the F-FACTORY half remains, owned by PLAN-0076 T1.** The criterion-vocabulary half SHIPPED as PLAN-0087 — COMPLETE 8/8, ARCHIVED (s158 #840, s159 #841). ADR-0025 D7's generator deferral was CANCELLED at N=4 (Cray-ratified, typed). Cray-ratified SD-1 = (a): the procedure-aware `ExecutorFactory` half stays with PLAN-0076 T1, guard `test_at2_extraction_obligation_is_owned` ARMED. Full detail incl. the Closeout and the deliberately-unopened `scored_rule._KNOWN_CRITERIA`: `docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` + `docs/plans/0076-*.md` §A.
- [ ] **PLAN-0075 follow-ons — homed by PLAN-0076 (`Status: Tracking`, #752, s133).** T1 (ADR-0031 D3 gate-plugin seam, F-FACTORY) is PARTIALLY discharged: the criterion-vocabulary half shipped as PLAN-0087 (#840/#841); the procedure-aware-`ExecutorFactory` half stays OPEN and owned here. T2's F-PIN remainder CLOSED s143 (#784) — but **F-PIN itself stays OPEN**, so PLAN-0076 does NOT archive and its AC-6 presence guard (`test_at2_followon_tracking_guard.py`) stays ARMED. PLAN-0075 is COMPLETE (13/13) → `docs/plans/done/0075-*.md`. Full detail: `docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` §A.
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2) — open ONLY for the O-2 residue.** Every other leg is DONE + archived (PLAN-0046/0048/0061/0062/0066/0067/0068/0070/0071/0073 → `docs/plans/done/`). **The one OPEN residue:** procurement's `intake` is declared-expressible under shadow parity, but production execution stays the co-existing `_SeedQuery` for derived fields. Full detail: `docs/plans/done/0062-per-vertical-seed-migration.md` (SD-C co-exist) + the transform arc `done/0077-*.md`/`done/0078-*.md` (both COMPLETE); the fold-in is named in `docs/plans/0076-*.md`.
- [ ] **Bounded/incremental chain verification (PLAN-0063 SD-4 follow-up, s118).** `GET /audit/verify` walks the WHOLE chain O(n) on demand — accepted at pilot scale. Future work = a checkpointed head / verify-since-anchor design; anchor storage ≈ external anchoring — **do not build without re-reading the tripwire** in `docs/plans/done/0063-audit-chain-verification-surface.md` + the `services/api/routers/audit.py` module docstring (SD-4). _[Note: the docstring's "ADR-011 boundary" is an EARMARK — `docs/adr/` jumps 0010 → 0012.]_ *(#688/#690)*
- [ ] **DEFERRED: a monotonic `sequence` column on `step_results` — the ROOT fix for `load_run`'s wall-clock ordering.** Needs a DB migration → its own PLAN; none drafted, the deferral STANDS, and both surviving orderings are DISPLAY-ONLY. Full detail (ROOT-vs-guard, why it is tolerable, the AST guard, the un-defer trigger): the module docstring of `tests/services/db/test_load_run_ordering_guard.py`. _[s161: PLAN-0088 (#848) reads runs in aggregate but deliberately depends on neither ordering (AC-3 AST tripwire); any ordering-sensitive read on the substrate re-opens this FIRST.]_
- [ ] **Rock 4 — s84 deep research DELIVERED → O-sequence locked.** Cray locked **O-1 → O-3 → O-2 → O-4**. **O-1** (Box-4 ฿ pitch) **DONE** · **O-3 = ADR-0025 Accepted** · **O-4 = PARK** (agent-interop; `docs/adr/0032-*.md:169` D4 — option-only, un-park = a counterparty's *written* pull). **Remaining: O-2 only** (economic-impact facet + Q3 data-binding = Rock 3). Full detail: `docs/adr/0025-at2-managerial-layer.md:19` (O-sequence + Box-3 fit) + `:23-29` (the **evidence-asymmetry** finding — bullish ROI all vendor-authored, independent mostly skeptical — rehomed s142). *(s84 Cray ask)*
- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten. **Full table (all six rows + their triggers + where each lands): `docs/plans/done/0005-oct-engine-runtime-layer.md:390` §8.1** — which itself instructs this STATUS entry to be a pointer. *(per Cray note 2026-05-21)*
- [ ] **Demo card UX — "trust shape", NO operator confidence badge (s74 design, Cray-approved).** The operator card shows what / grounded-why / approve gate + a "show full reasoning trace" toggle; no confidence badge (`confidence_signal` is engine-internal QA, trace-only), and SD-3 settles at (a) — the first-class `verification` field is NOT needed. Full record + rationale + the reconsider-trigger: the §SD-3 post-archival amendment in `docs/plans/done/0035-governed-action-verify-reshape-build.md`; `ADR-0030` cites it. *(Trigger: the next demo / UI round.)*
- [ ] **PLAN-004 Phase C — OPTIONAL POLISH (forward-declared; "may never land"):** HTML/markdown handoff dashboard under `docs/` + references-graph (mermaid dispatch chains) + `render_transcript.py` unified session export (PLAN-0004 §"Phase C"). *(Phase A + B both COMPLETE — session 35; the prior TODO's validator **warning-swallow bug was FIXED #312**, s58. Minor never-formally-scoped sub-ideas — README/`_rename-map` walk-exclusion, Cat G `references_*` autofix, OQ-2 effective-vs-authored `status:` dashboard flag — fold in only if Phase C lands. Reconciled 2026-06-16 s65 audit.)*
- [ ] **Custom Postgres image with extensions (pgvector / AGE / pg_trgm) — needs a fresh ADR number + a PLAN; neither drafted.** *[Corrected s141: **PLAN-002 does not exist** ("NOT yet drafted", `docs/plans/done/0005-oct-engine-runtime-layer.md:14`), and the old "≥ ADR-014" floor is **moot** — ADRs now run to 0032 and `0014-WITHDRAWN.md` exists.]* Context: **`docs/adr/0013-autonomy-axis-relocation.md:285-289`** (the floor-bump note) + **`docs/plans/done/0005-*.md:403`** (trigger: semantic + graph features).
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (low priority)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)

## Next Steps

1. **PLAN-0005 §8.1 revisit register** — remaining deferred-foundational simplifications at their batch boundaries (audit framework, mapping layer, ORM emitter, base-Postgres → the custom-Postgres image, registry discovery). _[Corrected s153: dropped the stale "→ ADR-011+" and "→ PLAN-002 (≥ADR-014)" pointers — **ADR-011 does not exist** (earmark only, per the Active TODO above) and **PLAN-002 was never drafted** with its ADR floor moot; each item's corrected status lives in Active TODOs.]_
2. **Partner-trial readiness gaps** — `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` awaits a dedicated Cray discussion.
3. **Deferred (backlog)** — PLAN-004 Phase C only (optional polish: handoff dashboard / references-graph / unified export — Phase B complete s35, warning-swallow fixed #312); the custom Postgres image (needs a fresh ADR number + a PLAN — neither drafted; see the Active TODO for the corrected framing).
4. **Ongoing** — Continue exercising the file-based handoff mechanism (Chat ↔ Code ↔ Cowork) across batches.

## Update Workflow

This file is updated when:
- A commit changes project state significantly
- A new ADR/PLAN is minted or completed
- Active priorities shift
- A batch closes (sync `last_updated` + `current_batch` + `head_commit` + `recent_commits` frontmatter)
- A session closes (sync all frontmatter fields; archive batch history if needed)

**Update mechanism (locked per STATUS staleness batch 2026-05-18, Hybrid A+B short-term, C long-term):**

- **Per closeout (Option A + Q1(b) discipline):** Closeout drafter includes the line "STATUS.md updated: yes / no / N/A" in their closeout. If `yes`, the closeout's commit batch should include a dedicated `docs(status): …` housekeeping commit (Q3(b/c) pattern) bumping at minimum the `last_updated` and `head_commit` frontmatter fields.
- **Per batch boundary (Option B full body):** Full body refresh (Current Focus + Recent Decisions + Active TODOs + Next Steps) at batch close, alongside the frontmatter bump.
- **Per session boundary:** Full body + frontmatter sync; consider archive of prior session's batch history.
- **Future (Option C, PLAN-004 Phase A):** Validator will flag stale STATUS.md by comparing **frontmatter `last_updated` field** against newest closeout's `created` timestamp (NOT file mtime — mtime is defeated by side-effect commits, e.g. `c85a595` 2026-05-16 normalization sweep that touched STATUS.md body without bumping `last_updated`).

**Q4 `head_commit` semantics (codified 2026-05-18, locked Cray ratification of midflight `2026-05-18-1049` §4 + closeout `2026-05-18-1202` §6.2):**

- `head_commit` = short SHA of the newest **substantive** commit on
  `origin/main` that STATUS.md content reflects.
- **Excluded from `head_commit`:** `docs(status): …` housekeeping
  commits. These commits encode no new repo state — they ARE the
  STATUS.md freshness marker. Including them in `head_commit` creates
  a self-defeat where every housekeeping commit makes STATUS.md appear
  "fresh" to Q4 detection regardless of substantive backlog.
- **Substantive (included in `head_commit`):** everything else —
  `docs(lessons):`, `docs(adr):`, `docs(runbook):`, `feat:`, `fix:`,
  `chore:` (when changing meaningful state), `refactor:`, `test:`, etc.
  Any commit type that changes durable repo content updates
  `head_commit` at the next STATUS.md edit.
- **Reader recipe (returning after a pause):**

  ```bash
  # Newest substantive commit on origin/main (the value head_commit should hold)
  git log -1 --format=%h --invert-grep --grep='^docs(status):' origin/main

  # Compare to STATUS.md head_commit field
  grep -E '^head_commit:' docs/STATUS.md
  ```

  If the two differ → STATUS.md content is stale relative to substantive
  repo state. If they match → STATUS.md is fresh.

- **Writer rule (at each STATUS.md update):** Set `head_commit` to the
  output of `git log -1 --format=%h --invert-grep --grep='^docs(status):' origin/main`
  *after* the substantive commits of the current batch land but *before*
  any `docs(status):` housekeeping commit (or, if the STATUS.md edit
  itself is in a substantive commit like `docs(lessons):`, set
  `head_commit` to that substantive commit's own SHA — which becomes
  knowable only post-commit, so the writer typically updates
  `head_commit` to the *most-recent prior substantive commit* and lets
  the next batch's first edit catch up).
- **Two failure modes this rule closes:**
  1. **mtime trap** (closeout `2026-05-18-1202` §2): side-effect commits
     that touch STATUS.md body without bumping `last_updated` (e.g.
     `c85a595` 2026-05-16 normalization sweep) leave the file mtime-fresh
     but semantically stale. A SHA in `head_commit` cannot drift this way.
  2. **Housekeeping self-defeat** (closeout `2026-05-18-1202` §6.2 +
     midflight `2026-05-18-1049` §4): if `head_commit` = own SHA, every
     `docs(status):` commit makes Q4 say "fresh" regardless of
     substantive backlog. Excluding `^docs(status):` from the comparison
     baseline closes this loophole.

Manually edited until Option C lands.
