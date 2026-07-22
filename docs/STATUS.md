---
last_updated: 2026-07-22T18:40:37+07:00
session: 163
current_batch: "s162 — 4 PRs recorded: #850 archetype re-key on (vertical, procedure_id), #851 PLAN-0089 filed, #852 the fleet AT-3 calm path BUILT, #853 closeout COMPLETE 6/6 + archived."
current_actor: code
blocked_on: "Nothing blocking. main=1b942f5; PLAN-0089 archived; gate on a8d679d = 2978/8/5 (the 5 = pre-existing tests/handoffs/ worktree false-REDs, green in CI); MS-S1 idle; dev Postgres UP."
next_action: "Nothing ordered — 3 candidates: (1) PLAN-0088 Step 1 (the cross-run substrate), (2) Active-TODO/RD trim (STATUS pass 2), (3) autonomy-triggers row (Cowork). Fleet calm path DISCHARGED (#853)."
head_commit: 1b942f5
recent_commits: [1b942f5, b1d877f, a8d679d, 610061b, 2904d77, df1982a, fa43e6b, 514dc1f, f1cce45, 333f6f6]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

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

> **Session 160, 2026-07-22 (head_commit `e55f2b8` → `0c9cdeb`) — a four-PR
> hook-hardening + doc-truth session: the Stop-hook classifier gained a
> **contentless-reason FLOOR** (#844) complementing the s159
> Cray-reserved-step rule (#843), the stale **AT-2 `N=4`** count was corrected
> everywhere it had drifted and the real `step_id` invariant pinned by a new
> guard (#845), and two Accepted-ADR bodies were corrected by `plan-drafter`
> (#846).**
> **(#843, `c8f7184` → merge `0090161`, `fix(hooks)` — recorded LATE.)** This
> landed in session 159, but the s159 reconcile never mentioned it (it was
> written before the PR existed; the s159 handoff flags the omission
> explicitly). The Stop-hook classifier prompt now treats **a step reserved for
> Cray as a natural stop, never a PROCEED next action**, pinned by a contract
> test proven non-vacuous by strip → RED → restore.
> **(#844, `532d3e4` → merge `c42abe4`, `fix(hooks)` — the CONTENTLESS-REASON
> FLOOR.)** The hook passes the classifier's `proceed` reason back to the agent
> **verbatim as its continuation instruction**, and the prompt requires that
> reason to NAME the next action — nothing enforced it. Session 160 observed the
> reason `"Continue to the next work step"` on a turn whose only real next step
> was Cray's decision among unratified candidates. **This is the COMPLEMENTARY
> shape to #843, not a regression of it:** #843 forbids *naming* a
> Cray-reserved step; a contentless reason names nothing, so #843's rule has
> nothing to bite on, and its contract test is four substring assertions on the
> prompt (behaviourally blind). New `_reason_is_contentless()` demotes such a
> verdict to pause. The design call that keeps it free of judgement: **a
> contentless reason is worthless even when `proceed` is CORRECT**, because the
> reason IS the instruction. It is a FLOOR, not a specificity judge —
> `_META_REASON_TOKENS` excludes every real action verb (guard-tested), and the
> OTHER s159 directive ("Continue running the test and mypy suite on the merged
> commit") still passes verbatim as the committed calibration pin. A **missing
> `reason` key** now demotes too (the old fallback was the literal
> `"continue"`). Also adds the gold case `pause-long-batch-then-question`:
> `gpt-oss:20b` already answers the existing short-question case correctly
> (19/20), so the live miss is a **fixture FIDELITY gap, not a model gap** —
> real payloads are a large work batch with the question only at the tail of the
> 8-turn / 3072-byte window. **+20 tests.**
> **(#845, `66b9707` + `b5272e2` → merge `d7bbb8b`, `chore` — the stale AT-2
> N-count, plus a new guard.)** AT-2 is **N=4** (`procurement` /
> `supply_chain` / `building_materials` / `fleet_maintenance` declare a
> `rule_gate` vocabulary; `energy` + `aquaculture` do not). Corrected in
> `spec.py` (×3 sites), `docs/conventions/procedure-archetypes.md`, and **the
> test module's own docstring** — the last two were NOT in the original scope:
> the drift was wider than recorded, and PLAN-0086 had shipped
> `fleet_maintenance` **without extending the archetype catalog** (its
> Quick-reference row and Instances list still enumerated three signatures —
> fixed in `b5272e2`, found during #846's R2). **Two corrections worth keeping
> as facts, not prose:** (a) `_RETRIGGER_N` is **retired and guards nothing**
> (its own docstring says so) — the live tripwire is the `_BASELINE_SIGNATURES`
> set-equality assertion, RED on a FIFTH signature; (b) PLAN-0087's "zero live
> `step_id` collisions today" is **wrong** — collisions already exist
> (`procurement` reuses `intake` / `approve` across three procedures); what is
> zero is the **over-mark**. New
> `tests/services/engine/procedures/test_sod_step_id_scope_guard.py` pins the
> real invariant (a step is in the vertical-flat `sod_steps` union **iff** its
> OWN procedure declares it), because `GovernanceStepExecutor.sod_steps` is a
> bare per-vertical `frozenset[str]` with no procedure key and nothing raises on
> an over-mark; it carries a second test so the guard cannot silently become
> vacuous. This hardens the premise **PLAN-0076 Step T1 (F-FACTORY)** defers on.
> **(#846, `25110c8` → merge `0c9cdeb`, `docs(adr)` — two Accepted-ADR body
> corrections, authored by the `plan-drafter` subagent (G1-gated), Code R2.)**
> **ADR-0032**'s "Where vero-lite stands" is a STATE snapshot and had drifted on
> more than N: it still said `building_materials` was a Tier-1 Mirror with **no
> `procedures.yaml`** and an unbuilt hero, counted four verticals, and did not
> know `fleet_maintenance` existed. It now reads six verticals, the
> governed-credit hero BUILT (PLAN-0081), fleet named, the full N=4 arc, and
> **symbolic anchors replacing the rotted line-number ones**. Its
> positive-consequences bullet — which claimed the ADR record makes exactly this
> stale-N-count error class harder to reintroduce, **while itself being stale**
> — was rewritten to say the durable guard is **the test, not the prose** ("the
> tripwire is CI; the ADR is the narrative"). **ADR-0025 D7's decision text was
> deliberately NOT rewritten** ("N ≥ 2" is the faithful 2026-06-28 record;
> editing a decision to match later events destroys the reasoning lineage) — a
> dated **outcome amendment** was appended instead, following the amendment
> precedent already in that ADR. **Attribution corrected by the drafter against
> Code's own dispatch:** **Cray** cancelled the D7 deferral, typed, 2026-07-21
> (s157), at the PLAN-0086 N=4 escalation; PLAN-0087 only **executed** the
> answer.
> **(deliberately NOT built.)** The second s159 tripwire — **tripwire B, the
> PLAN-0076 AC-6 F-PIN arm** — was NOT built: the grounding REFUTED its
> mechanism. The guard checks **file presence, not T1 text**, so it cannot
> self-release; it can only be deleted by hand, and a tripwire against a hand
> deletion buys nothing.
> **Verification:** both new tripwires proven non-vacuous **empirically** —
> backed up to `/tmp`, broken, **RED confirmed**, then restored **from the
> backup, never from git** (the s159 trap: a `git checkout` restore wipes the
> uncommitted edit under test and the run still prints a pass),
> `md5sum`-verified. Merge-commit gate against a pass/fail read fixed **BEFORE**
> the run — expected `2955 + 20 + 2 = 2977`; actual on `0c9cdeb` = **2977 passed
> / 7 skipped** (164.66s) + `mypy --strict services/` clean (98 files) ⇒
> `confirmed — prior intact`. Branch protection is **`strict: true`** —
> discovered while landing the stack (each remaining PR went `BEHIND` after a
> merge and needed a re-sync + a fresh `gate` run); it substantially closes the
> old "CI is PR-only, so the merge commit is never tested" gap. Grounding for
> the whole session came from a **5-agent Explore fan-out over 6 candidates**
> (the `next-work-analyst` skill), which is what surfaced the corrections above.
> Deterministic-offline: **MS-S1 idle/COLD, zero calls**, no host-state change;
> dev Postgres UP; loop-dispatcher DISABLED; **0 open PRs**; working tree clean
> but for the 2 KEEP untracked paths (`.claude/benchmark-results/`,
> `.claude/launch.json`). Commits: `c8f7184` → `0090161` (#843 merge) →
> `532d3e4` → `c42abe4` (#844 merge) → `66b9707` + `b5272e2` → `d7bbb8b` (#845
> merge) → `25110c8` → `0c9cdeb` (#846 merge, head_commit of record). The three
> `Merge remote-tracking branch 'origin/main'` sync commits (`d852ab1`,
> `329bfac`, `39a37d4`) are strict-mode re-sync noise and are excluded from
> `recent_commits`.

> **Sessions 158 + 159, 2026-07-21 (head_commit `79358c6` → `e55f2b8`) —
> PLAN-0087 BUILT (#840) then CLOSED OUT + archived at 8/8 ACs (#841): the
> ADR-0031 D3 gate seam's **criterion-vocabulary half** is SHIPPED —
> `ComplianceCriterion` is RETIRED from engine code and a vertical now
> **declares** its own `rule_gate` vocabulary, so a new AT-2 vertical ships its
> gate with ZERO engine diff.**
> **(what shipped — s158, #840.)** `VerticalProcedures.compliance_criteria:
> list[CriterionId]` (`spec.py`) — pattern-constrained by the `CriterionId`
> type and membership-validated at load by `_validate_compliance_criteria`;
> only the four `rule_gate` verticals were migrated (`energy` + `aquaculture`
> YAMLs are absent from the diff entirely).
> **(the claim is PROVEN, not asserted.)** AC-1's proof pair: a fixture
> criterion `zzz_fixture_only_sourcing_check` that exists NOWHERE under
> `services/` loads through the real `load_procedures_file` and gates through
> the real `evaluate_compliance`, while its undeclared twin is REFUSED at load;
> a repo-grep static guard keeps the id confined to that one test module.
> **Behaviour-preserving:** no pinned governance hash moved — the declaration
> block sits outside the pin surface (the `principals` precedent).
> **(the scope split — Cray-ratified SD-1 = (a), typed.)** This discharges the
> criterion-vocabulary half of **PLAN-0076 Step T1 (F-FACTORY)** only; the
> procedure-aware `ExecutorFactory` half stays OPEN and still owned by
> PLAN-0076, so **PLAN-0076 does NOT archive** and its AC-6 presence guard
> stays ARMED — **no guard re-homing occurred, deliberately**. ADR-0031 D3
> row 3 was updated on landing per D4.4 — exactly one table row, which was
> AC-7's whole obligation.
> **(the closeout — s159, #841.)** `git mv docs/plans/0087-*.md
> docs/plans/done/`, Status `Draft` → **COMPLETE** (never flipped to
> `Accepted` — an `Accepted`-status PLAN is G1-gated for its own closeout), all
> 8 ACs ticked, plus a new **Closeout** section recording (a) the evidence read
> at closeout time and (b) what was deliberately left undone. Every AC was
> re-read against **fresh on-disk evidence** rather than carried over from the
> build session's notes — CLAUDE.md §6 ("Verification is hygiene, not a
> verdict") double-gates `confirmed — prior intact` on the pre-committed
> pass/fail read AND a fresh artifact.
> **(deliberately NOT done, and recorded as such in the PLAN.)** PLAN-0076 is
> **NOT** archived (T1's factory half open; §B item 1 — F-PIN's new-run
> re-routing threat — open by construction), so its guard stays armed.
> `scored_rule._KNOWN_CRITERIA` was NOT opened: zero extension pressure to
> date, and its shape is `derive`-grammar-like, not vocabulary-like. The stale
> `N=2`/`N=3` doc drift in ADR-0025 D7 + ADR-0032 was NOT folded in — s157
> expected it to ride along with PLAN-0087's G1-gated edits, but AC-7 obligated
> that one ADR-0031 row and nothing more; it now needs its own small
> `plan-drafter` dispatch.
> **Verification:** the suite walked **2943/7 → 2951/7 → 2954/7** across the
> build and re-ran GREEN on the merge commit `c6eec65`. Gate re-run at closeout
> on `main = c6eec65`: full suite **2954 passed / 7 skipped** (169.91s) and
> `mypy --strict services/` clean (98 source files) — **matching the build
> session exactly**; the four doc-reading guard tests re-ran green after the
> `git mv` (84 passed). Deterministic-offline: **MS-S1 idle/COLD, zero calls in
> both sessions**, no host-state change, no demo/dev server started; dev
> Postgres `vero-postgres` UP (localhost:5442 — evidenced by only 7 skips).
> `main` protected; **#841 is the only open PR**; loop-dispatcher DISABLED;
> working tree clean but for the 2 KEEP untracked paths
> (`.claude/benchmark-results/`, `.claude/launch.json`). Commits: `d9a0ad1` →
> `16c3622` → `bdd07ed` → `4f9cb7a` → `c6eec65` (HEAD of `main`, #840 merge) →
> `e55f2b8` (#841 closeout, head_commit of record).

> _Rotation note (session-163 reconcile, 2026-07-22, `docs(status):`): added
> the **Session 162** CF block (the four-PR arc — #850 the
> `PROCEDURE_ARCHETYPES` re-key and #851 PLAN-0089 filed, both merged during
> s161 and recorded LATE; #852 the AT-3 calm path BUILT; #853 the closeout,
> merged at the s163 open) and rotated **NO CF block**: Current Focus now holds
> **4 blocks covering sessions 162 / 161 / 160 / 159** (s158+159 share one
> block) — exactly the 4-most-recent-sessions window and well under the 8-block
> cap, so R2 requires no CF rotation this pass. Recent Decisions gained ONE row
> (the s162 PLAN-0089 arc, written as a ≤600-char pointer from birth) and
> rotated its ONE OLDEST — the **s151** PLAN-0081 governed-credit-HERO row
> (#814) — to the rotation base `docs/status-archive/2026-h1-status.md`. The
> rotation-note trail was carrying **three** (s161 + s160 + s159); this pass
> rotates **two out** (the s159 and s160 notes, to the same base) and adds one,
> so 3 − 2 + 1 = **2**, restoring the file's own habit (the runbook sets no
> note-count rule). One Active TODO was **RETIRED as discharged, not trimmed**:
> the "AT-2 stale `N=2` / `N=3` signature counts — doc drift across three
> artifacts" item is **FALSE as of session 160** — all three named artifacts
> were verified correct on disk (`services/engine/procedures/spec.py` states
> **N=4**, its surviving N=2/N=3 tokens being correctly-framed historical
> narrative of the firing arc; `docs/adr/0025-at2-managerial-layer.md` carries a
> dated 2026-07-22 **outcome amendment**, its "N ≥ 2" decision text deliberately
> PRESERVED rather than drift; `docs/adr/0032-*.md` is re-grounded to N=4) —
> discharged by **#845 / #846 (s160)**. Its full original text was emitted
> verbatim to the caller for the archive (R4).
> **PASS 2, same session and same PR — the R2 pointer-rule TRIM.** The 9 older
> Recent-Decisions rows (the s162 row was written to the rule at birth) and the
> 6 over-length Active TODOs were compressed to ≤ ~600-char pointers. **Counts
> are UNCHANGED — RD stays 10 rows, Active TODOs stay 13 items:** this is
> compression, not deletion, and every pre-trim original was appended to
> `docs/status-archive/2026-h1-status.md` BEFORE the trim landed (R4). Each item
> was trimmed **only after its tracked home was verified on disk** (PLAN-0087 +
> PLAN-0076 §A, PLAN-0076, PLAN-0062/0077/0078, the
> `tests/services/db/test_load_run_ordering_guard.py` module docstring,
> PLAN-0063 + the `services/api/routers/audit.py` SD-4 docstring, and the
> PLAN-0035 §SD-3 post-archival amendment). The ~600 budget is measured on the
> **Decision cell**, never the Reference column — R2's own wording ("full detail
> lives in the referenced ADR/PLAN/PR, which every row already links") makes the
> link the thing the rule preserves, so it cannot be what the budget consumes.
> **One carve-out HIT, retained verbatim at full length:** the s156
> model-economy ratification lives only in a private Tier-0 auto-memory, so it is
> not a duplicate and stays at full length until rehomed. **STATUS across both
> passes: 59,697 B → 61,616 B (reconcile) → 53,758 B (trim)** — caller-measured,
> not estimated — against the 64 KB R1 ceiling. Still above the 48 KB soft
> target, which the next reconcile inherits as its standing lever. Per the
> STATUS.md Rotation Policy (R1/R2/R4)._
>
> _Rotation note (session-161 reconcile, 2026-07-22, `docs(status):`): added the
> **Session 161** CF block (PLAN-0088 filed Draft, #848 — the cross-run read
> substrate + run-insight readers; the L1/L2 forks Cray-ratified by typed
> selection) and rotated the OLDEST CF block — **Session 157** (PLAN-0086, the
> timed manual scaffold of the 6th vertical `fleet_maintenance` #838 + the
> ADR-0025 D7 AT-2-generator deferral CANCELLED at N=4) — to the Current-Focus
> rotation base `docs/status-archive/2026-h1-current-focus.md`. Rotating it is
> what **R2 requires**, not a headroom judgement: the 4 most-recent sessions are
> now 161 / 160 / 159 / 158, so the s157 block fell **outside** the window.
> Recent Decisions gained ONE row (the s161 PLAN-0088 arc) and rotated its ONE
> OLDEST — the **s150** row (PLAN-0082 Steps 5-7 + the PLAN-0081 fold,
> #809-#812) — to the rotation base `docs/status-archive/2026-h1-status.md`. The
> **session-157** rotation note was itself rotated to the same base (R4
> consolidation): the trail had been carrying **three** notes rather than two
> because the s160 reconcile deliberately left it — that dispatch scoped exactly
> one CF block + one RD row, and silently dropping an un-instructed block was the
> exact failure mode that session existed to fix — so this pass instructs it
> explicitly. Because this pass also ADDS a note, the trail stays at **three**
> (s161 + s160 + s159): converging to two needs a SECOND note rotated, which was
> not instructed here. Nothing is violated — the runbook sets no note-count rule
> (grep-verified this session); "two" is the file's own habit, not R2.
> Window after this reconcile: **CF = 3
> blocks covering the 4 newest sessions** (s161 + s160 + s158/159 — well under
> the 8-block cap); RD = 10 rows. **STATUS: 56,272 B → 59,697 B**
> (caller-measured, not estimated), against the 64 KB R1 ceiling — the standing
> headroom levers remain the Active-TODO trim (~4.66 KB) and the oversized RD
> rows (~1,200-1,600 chars each against the ~600 target), both R4-gated on
> appending the full originals to the archive first. Per the STATUS.md Rotation
> Policy (R1/R2/R4)._

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
| 2026-07-22 | **s162 — PLAN-0089 filed (#851) → BUILT (#852) → COMPLETE 6/6 + archived (#853): `fleet_maintenance.pm_service_round`, the AT-3 calm path, as a measured "extend an existing vertical" experiment — ~14 min hands-on, ZERO engine diff PROVEN (`git diff df1982a..a8d679d -- services/engine/` EMPTY).** M-6 BINDING: a lower bound, never summed with PLAN-0086's 27m39s. + #850 `fix(api)` re-keyed `PROCEDURE_ARCHETYPES` on `(vertical, procedure_id)`. AT-3 GENERALIZED to "a measure vs a per-entity threshold"; N stays 4. Gate on `a8d679d`: 2978/8/5. Full narrative: the Session-162 CF block above | `1b942f5` (#853 merge, head_commit of record) / `a8d679d` (#852 build) / `df1982a` (#851) / `514dc1f` (#850) / `docs/plans/done/0089-fleet-calm-path-extend-an-existing-vertical.md` (COMPLETE, 6/6) |
| 2026-07-22 | **s161 — PLAN-0088 filed Draft (#848, `docs(plans)`): the cross-run read substrate + run-insight readers.** Two Cray-ratified TYPED forks are the PLAN's LOCKED constraints: L1 — "Group A" is NOT Shape 2 and does NOT trip the ADR-0032 D2 pilot gate, proven by a STATIC guard (AC-11), not prose; L2 — build Group A + PROVE the substrate expresses Group B (AC-10) but do NOT build Group B, which stays pilot-gated. Wall-clock ordering hazard PINNED not inherited (AC-3 AST tripwire); the sequence-column PLAN stays UNOPENED. Full narrative: the Session-161 CF block above | `e6bb8c8` (#848 merge, head_commit of record) / `0dce906` (build) / `docs/plans/0088-cross-run-read-substrate-and-run-insight-readers.md` (Draft) |
| 2026-07-22 | **s160 — four PRs hardening the Stop hook and the AT-2 doc record: #844 the CONTENTLESS-REASON FLOOR (complement to #843, landed s159 unrecorded); #845 AT-2 corrected to N=4 + a cross-procedure `step_id`-scope guard; #846 (`plan-drafter`, G1) ADR-0032 re-grounded + a dated ADR-0025 D7 OUTCOME amendment, its "N ≥ 2" decision text deliberately NOT rewritten.** Two premises are now pinned in code, not prose: `_RETRIGGER_N` is retired, and PLAN-0087's "zero live `step_id` collisions" is wrong — both carried by the guard docstrings cited right. Full narrative: the Session-160 CF block above | `0c9cdeb` (#846 merge, head_commit of record) / `d7bbb8b` (#845) / `c42abe4` (#844) / `0090161` (#843) / `tests/services/engine/procedures/test_sod_step_id_scope_guard.py` + `tests/services/engine/procedures/test_at2_signature_retrigger.py` + `docs/adr/0025-at2-managerial-layer.md` (D7 amendment) |
| 2026-07-21 | **s158 + s159 — PLAN-0087 BUILT (#840) then CLOSED at 8/8 ACs + archived (#841 `docs(plans)`): the ADR-0031 D3 gate seam's CRITERION-VOCABULARY half — `ComplianceCriterion` RETIRED from engine code, a vertical DECLARES its own `rule_gate` vocabulary in `procedures.yaml`, so a new AT-2 vertical ships its gate with ZERO engine diff (PROVEN by AC-1's fixture-criterion pair, not prose).** Behaviour-preserving — no pinned governance hash moved. Cray-ratified SD-1 = (a) (typed): the procedure-aware `ExecutorFactory` half stays owned by PLAN-0076 T1, its AC-6 guard ARMED. Full narrative: the Sessions 158+159 CF block above | `c6eec65` (#840 merge) / `e55f2b8` (head_commit of record, #841) / `services/engine/procedures/spec.py` + `tests/services/engine/procedures/test_declared_criterion_vocabulary.py` + `docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` (COMPLETE, 8/8) |
| 2026-07-21 | **s157 — PLAN-0086 COMPLETE (#838 `feat(verticals)`): the narrative→pipeline scaffolder run as a TIMED MANUAL baseline — a dirtied customer monologue → a live, governed, human-gated pipeline on the 6th vertical `fleet_maintenance` in 27m39s hands-on. AC-7 caveat, BINDING: a LOWER BOUND (Code drafted the pre-dirtied narrative).** ADR-0025 D7's AT-2-generator deferral CANCELLED at N=4 (Cray-ratified, typed); `_RETRIGGER_N` RETIRED, replaced by `test_at2_extraction_obligation_is_owned` (PLAN-0076 T1 owns). Full narrative: the Session-157 CF block, rotated to `docs/status-archive/2026-h1-current-focus.md` | `79358c6` (HEAD, #838 merge) / `a2ef45e` (build) / `verticals/fleet_maintenance/` + `tests/services/engine/procedures/test_at2_signature_retrigger.py` (guard replacement) + `docs/plans/0086-fleet-vertical-timed-manual-scaffold.md` (closeout pending) |
| 2026-07-21 | **s156 — PLAN-0085 "Advisory Gate Recommendation (AI-Transition Rung 1)" filed → 5 SDs Cray-ratified → BUILT → closed in ONE day (#831/#832 `docs(plans)`, #833 `feat(engine)`, #834 closeout): an advisory recommendation with grounded reasons at procurement's `doa_tier` approval gate — SHOWN, NEVER routes (the ADR-0019 determinism fence, now CI-pinned).** All 5 SDs = the draft rec; new `gate_advisory.py` (never-raise, ADR-0030 D5); Monitor gate-panel block, NO score (the #823 trust shape). Full narrative: the Session-156 CF block, rotated to `docs/status-archive/2026-h1-current-focus.md` | `2f46fc9` (#833 BUILT, head_commit of record) / `63009c3` (#834 closeout, main HEAD) / `8809776` (#831) / `d679036` (#832) / `services/engine/procedures/gate_advisory.py` + `docs/plans/done/0085-*.md` (archived, 8/8) + `docs/runbooks/run-oct-demo.md` §3e |
| 2026-07-21 | **s156 — the demo rehearsal (carried s153→155) PERFORMED + PASSED (Cray, Beats 1-5 on 8101), which GATED the PLAN-0084 closeout (#830 `docs(plans)`, 9/9 ACs + archived); + a map-label UI fix (#829 `fix(ui)`).** Cray then opened the two-view **AI-Transition** frame (LLM at the approval gate; narrative→pipeline scaffolder) and ratified the SEQUENCE: View-1 (Rung 1 = PLAN-0085) → reshape View-2 → build View-2. A model-economy policy ratified (private memory, not a repo change): Fable for complex planning/research, Opus 4.8 + Extra for execution/coding-to-plan. Full narrative: the Session-156 CF block, rotated to `docs/status-archive/2026-h1-current-focus.md` | `ad39774` (#830) / `19f5caa` (#829) / `docs/plans/done/0084-*.md` (archived, 9/9) + `.claude/handoffs/session-156/2026-07-21-0851-*-ai-transition-two-views.md` |
| 2026-07-20 | **s155 (late) — PLAN-0084 shipped end-to-end in one arc (#825 filed Draft → #826 all 5 SDs Cray-resolved → #827 `feat(demo)` BUILT): map↔monitor run linkage (runs stamp `trigger_context["subject"]`; the map direct-fetches `/runs`; node-panel "Open in Monitor →") + opt-in seed rotation (`--asset`/`--rotate`).** Headline = SD-F, Cray-ratified mid-build — the PLAN's grounding `was an error`: `register_procurement_adapter` now registers the `FastenalCsvAdapter` (split-brain demo closed). Live-verified on 8101. Full narrative: the Sessions 153+154+155 CF block, rotated to `docs/status-archive/2026-h1-current-focus.md` | `25b31e2` (HEAD, #827 merge) / `45fcba1` + `64119b9` (build) / `e5f3ede` (#826 merge) / `628bfa1` (#825 merge) / `docs/plans/0084-map-monitor-run-linkage-and-seed-rotation.md` (Draft, 6/6 SDs resolved) + `verticals/procurement/data_adapter/__init__.py:99` + `docs/runbooks/run-oct-demo.md` §3d |
| 2026-07-20 | **s153-155 — #822 `docs(runbook)` staged the config-pin fail-closed refusal as a deliberate demo beat (run-oct-demo.md §3c, Beat 06); s154 ZERO commits (Cerebras-KB strategy read: artifact-KB = D3 Shape-2, pilot-gated; reframe = "governed retrieval over the decision record"); #823 `fix(ui)` REMOVED the operator confidence badge from BOTH cards, executing the ratified s74 trust shape.** Trace/fault-mode/DAG confidence KEPT by design; 4 claim-vs-code corrections recorded. Full narrative: the Sessions 153+154+155 CF block, rotated to `docs/status-archive/2026-h1-current-focus.md` | `4edfa3f` (HEAD, #823 merge) / `ffb251b` + `f09cc99` (badge removal) / `d8057fb` (#822 merge) / `b45f5c4` (#821 merge) / `docs/runbooks/run-oct-demo.md` §3c + `services/api/static/assets/view-anomaly.js` + `view-story.js` |
| 2026-07-19 | **s152 — PLAN-0083 (fix c1) BUILT + verified + archived (#818 `feat`, #819 `docs(plans)`): the procurement ontology↔CSV column drift CLOSED at the `FastenalCsvAdapter` seam — `_COLUMN_RENAMES` on the `fetch_objects` path maps raw Fastenal CSV → canonical ontology names, so every consumer sees ONE canonical vocabulary.** Zero-core-edit under ADR-016's LOCKED "mapping absorbs source diversity" boundary (ADR-0023); a `test_fastenal_adapter_canonical_coverage.py` tripwire pins per-type set-equality, non-vacuous EMPIRICALLY. Full narrative: the Session-152 CF block, rotated to `docs/status-archive/2026-h1-current-focus.md` | `a53c6ed` (#818 merge) / `a211651` (build) / `5140ee3` (HEAD, #819 merge) / `docs/plans/done/0083-*.md` (archived) + `tests/verticals/procurement/test_fastenal_adapter_canonical_coverage.py` |

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
