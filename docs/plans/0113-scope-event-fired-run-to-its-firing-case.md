# PLAN-0113: Scope the event-fired run to its firing case

**Status:** Draft
**Owner:** Claude Code
**Created:** 2026-08-23 (session 249)
**Related ADRs:** ADR-016 (query grammar; the Q4/PLAN-0061 join-projection amendment is
the shape precedent), ADR-0029 (event-trigger bridge — the `entity_ids` stamp this PLAN
consumes), ADR-0034 (D6 only-when-supplied — the hash-stability constraint on the new
field), ADR-0025 (gate content — untouched)

> **Author≠reviewer disclosure (ADR-012 D4.3).** Drafted by the in-harness
> `plan-drafter` subagent (ADR-013 D1) from a Code-authored, session-249-verified fact
> pack. Independent reviewer: Cray at PR merge. Every `file:line` citation below was
> re-read against the tree at `98463e7` during drafting.

---

## Goal

Make an **event-fired** run gate on **its firing case only**, instead of sweeping the
fleet: the vertical's YAML declares which field of the read scopes to the trigger's
engine-stamped `entity_ids` (`scope_by`), and declares per-step what happens when a run
carries no firing entity (`when_absent: sweep | refuse`). Fleet's
`governed_repair_approval` authors the clause, so a visitor who accepts a quote sees a
gate proposing **exactly one** case — their own — while the seeded demo run (which fires
with no entity ids, by design) keeps sweeping and the demo stays bootable. The engine
never learns any vertical's field name; procurement's event path and all 11
manual/schedule procedures are proven byte-identical.

## The ruling this PLAN enacts — a typed reversal, classified `superseded by new info`

`PLAN-0112 SD-4` (archived: `docs/plans/done/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md:1002-1039`) was
**RULED (Cray, typed, s243, 2026-08-21): (a)** — accept the multi-case gate. Its
rejected option read, verbatim:

> **(b)** Scope the run to the firing case — requires engine work (grammar
> parameterization) or per-case procedure authoring; both are the Out-of-Scope engine
> line unless Cray re-scopes the PLAN.

**Cray has now typed the reversal (s249, 2026-08-23): re-scope to option (b).** Cray's
stated reason, verbatim: *"เพราะมันเป็นทางเลือกที่ดู make sense ที่สุด มันควรมีให้เลือก
เฉพาะของตัวเอง ไม่ใช่แสดงมาให้เลือกทั้งกอง"*

**Classification: `superseded by new info` — NOT `was an error`** (CLAUDE.md §6
"Verification is hygiene, not a verdict"; `docs/lessons/0027-*`). (a) was correct in its
context: option (b) genuinely was outside PLAN-0112's scope, and the sharpened cost SD-4
recorded with its ruling (`done/0112:1011-1019`) — `GateResolveRequest.decisions`
(`services/api/models/runs.py:190-200`) *compels* an explicit decision on **every**
proposal, so an approver must re-decide the demo pair's re-proposals on every visitor
round — is exactly the cost this reversal removes. The lineage stays: SD-4's option text
is quoted above, and Step 7 records the reversal beside the original ruling (gated on
OQ-1 below).

**Two further Cray-typed picks (s249), both taken as recommended — LOCKED for this
PLAN:**

- **D1 — absent-scope policy: (ก+).** The YAML declares it **per-step**, e.g.
  `when_absent: sweep | refuse`. NOT an engine-wide policy. Fleet authors `sweep`.
- **D2 — grammar shape: (ก).** The YAML names the field:
  `scope_by: {field: <name>, from: trigger.entity_ids}`. The engine must **never**
  learn the token `case_id` — fleet's firing entity is a *case*, procurement's is an
  *asset* (`verticals/procurement/hero_demo/run.py:544`,
  `entity_ids=entity_ids or [_EVENT_ASSET_ID]`), and 11 of the 13 procedures across 6
  verticals are `manual`/`schedule` with no firing entity at all. Only two declare
  `trigger: event`: fleet `governed_repair_approval`
  (`verticals/fleet_maintenance/procedures.yaml:144`) and procurement
  `emergency_sourcing_round` (`verticals/procurement/procedures.yaml:861`) — measured
  s249 by grep, and re-verifiable with
  `git grep -n 'trigger: event' -- verticals/`.

## Why this is cheaper than SD-4 priced it — the verified mechanism

SD-4(b) was priced as "engine work (grammar parameterization) or per-case procedure
authoring". The first half is real but small, because the value to scope on is
**already stamped on every event run**:

| Fact | Citation (verified s249 @ `98463e7`) |
|---|---|
| `trigger_context["entity_ids"]` is engine-stamped on every event-fired run; for fleet it is `[case_id, quote_id]` | `services/api/routers/cases.py:148` (rationale `:126-131` — G-14 keys the dedup on the quote's identity) |
| It reaches `RunContext`, so a step executor can read it | `services/engine/procedures/orchestrator.py:898,905-912` |
| The API already resolves `entity_ids` → an ontology object for the run's subject | `services/api/routers/runs.py:213-237` (`_resolve_subject`) |
| 🔴 `query_step.py` contains **ZERO** references to `trigger_context` — the missing wire IS the whole gap | grounded negative, re-verified s249: `git grep -n trigger_context -- services/engine/procedures/query_step.py` → 0 hits |
| The grammar today has only static-literal narrowing: `StepInput.where` "field-equality filter … (all pairs)" and the per-join `JoinSpec.where` | `services/engine/procedures/spec.py:361-363` and `:265-268`; the `matches_where`/LOCKED-3 attachment is documented at `:241-242` |
| The join-path pipeline order is pinned: base `where` → per-join `where` → joins in declaration order → latest-per-group → renames | `services/engine/procedures/query_step.py:460-470` (docstring), base-`where` application `:486-491`, `latest_per` `:509-510` |

**The attachment point.** Scope must apply to the **base read's rows, post-`where`,
pre-join, pre-projection** — for the single-read path, alongside the existing
`matches_where` narrowing (`query_step.py:434-439`); for the join path, with the base
`where` at `query_step.py:486-491`. Applied *before* `latest_per`, the result is "the
firing case's own latest reading" (1 row); applied after, it is "the fleet's latest
reading iff it happens to be the firing case's" (possibly 0 rows). The ordering decides
whether the gate gets one proposal or none — it is fixed here, pre-execution.

**Match semantics (D2 rendered):** keep a row iff `row[field]` is a string **member of**
`trigger_context["entity_ids"]` (a list — fleet's carries the quote id too, which
matches no `case_id` and is harmless). A row missing the field never matches, mirroring
`matches_where`'s non-mapping posture (`spec.py:328-337`). `plan_read` stays pure
(no ctx): the compiled plan carries the *declaration*; the executor resolves it against
`ctx.trigger_context` at execute time.

**The constraint that shapes Step 1 — the seeded demo run has no firing case BY
DESIGN.** `verticals/fleet_maintenance/operate_seed.py:266-278` builds
`trigger_context={"source": "operate-demo-seed", "triggered_by": ...}` — no `trigger`
key, no `entity_ids` — with an in-code NOTE that fleet's breaching truck "is not
knowable at trigger time" (the truck is chosen by the declared query DURING the run).
`_trigger_of` (`services/api/routers/runs.py:239-242`) therefore reads it as `manual`.
`read_demo_state` (`services/db/demo_run_reset.py:179-205`) requires
`run-fleet-operate-demo` to be `waiting_human`, suspended at `approve`, with a non-empty
`output_set` — else `CONSUMED`. A fail-closed absent-scope policy would make
`DEMO-STATE: PRISTINE` unreachable and kill intro-video beat 4. **This is exactly why
D1 = `sweep` for fleet.** (Live read-only probe, s249: `DEMO-STATE: PRISTINE`.)

**What a visitor sees today (live-measured s249, read-only):** both seeded demo cases
are open and re-proposing — `case-fleet-operate-demo` → truck-02
(`operate_seed.py:120,:192,:328`) and `case-demo-truck03-gearbox` → truck-03
(`verticals/fleet_maintenance/data_adapter/synthetic.py:269`). Fleet has exactly 3
trucks, all with `minor_repair_ceiling_thb: 5001.0` (`synthetic.py:134,147,165`). A
visitor-fired run today proposes 3 candidates, of which only one is the visitor's.

## Acceptance Criteria

Every AC binds to **CLAUDE.md §8's witnessed-RED bullet**: one probe per assertion; under
each probe the *other* assertions must stay GREEN; every negative/zero claim carries a
positive control; every probe proves its mutation reached the code (prefer a
length-changing mutation; run with `PYTHONDONTWRITEBYTECODE=1`; restore from a `/tmp`
copy sha256-verified byte-identical — the PLAN-0112 AC-7(i) probe discipline).

- [ ] **AC-1 — the grammar lands, only-when-supplied.** `scope_by` (+ its `when_absent`
  companion) on the query step's input model; all 6 verticals load
  (`load_procedures`); **governance config hashes byte-identical for all 6** — oracle:
  `tests/verticals/test_governance_config_hash_stability.py` (exists, verified s249).
  🔴 The field MUST be dropped from the dump when absent (ADR-0034 D6; the authored
  precedent is `emergency_waiver.ratification_window_days`,
  `verticals/fleet_maintenance/procedures.yaml:348-357`): an always-present field moves
  every vertical's hash and makes in-flight runs fail closed on pin mismatch.
  Non-vacuity: make the field always-present in a scratch copy → the hash test reddens.
  Load-gate half: a `scope_by` on a non-query step, or without `reads`, or (per SD-1,
  **RULED required-explicit**) without an explicit `when_absent`, refuses at load — each refusal
  witnessed RED by a spec fixture. **[offline/no-DB]**
- [ ] **AC-2 — the wire works, three ways.** Unit-level, on `QueryStepExecutor` with a
  fake adapter (unit tests here; the real-seam proof is AC-3): (i) scope value present
  and matching → only matching rows survive, pre-`latest_per`; (ii) scope present, no
  row matches → 0 rows — positive control: the same fixture with a matching id yields
  >0; (iii) no `entity_ids` + `when_absent: sweep` → output **byte-identical** to
  today's (assert equality against the unscoped run of the same fixture); (iv) no
  `entity_ids` + `when_absent: refuse` → a **typed refusal**, never a silent `[]`
  (design note: an additive `ReadRefusalKind` member, the PLAN-0061
  `JOIN_SHAPE_VIOLATION` precedent — existing members untouched). A `scope`
  provenance entry is recorded with a post-scope count (never a silent narrowing;
  check whether the trace viewer needs a label for any new `kind` — audit the
  `"kind"` counts before shipping). One probe per assertion. **[offline/no-DB]**
- [ ] **AC-3 — fleet is scoped, proven at the real seam.** Scenario test (CLAUDE.md §8:
  real producer → real consumer, realistic data — no mock on either side): a visitor
  opens a case, accepts an at/above-ceiling quote, and the fired run's `approve` gate
  proposes **exactly one** proposal, the visitor's own case.
  `_assert_run_is_about` (`tests/api/test_case_acceptance_fires_governed_run_scenario.py:182-193`)
  tightens from `any(case_id in pid ...)` to *exactly one, and it is the firing case*.
  The two-gate walk (`:406-417`, approve → parks at fulfill → completed) stays green
  unchanged. **New observable, asserted:** a **sub-ceiling** acceptance fires a run
  that **completes with no gate** — `reshape` consumes only the breach subset
  (`procedures.yaml:224-227`), and under scoping no other truck's breach rides along
  (this re-supersedes `done/0112:885-894`'s s243 correction — see Blast radius #13).
  Witnessed RED: remove the `scope_by` clause from the YAML → the exactly-one assertion
  reddens with 3 proposals. **[offline/DB]**
- [ ] **AC-4 — the blast radius is bounded, with a positive control.** Procurement's
  event path (`emergency_sourcing_round`) and all 11 manual/schedule procedures behave
  identically to the Step 0 baseline — same tests green, and a targeted comparison for
  procurement's hero run. 🔴 Positive control (without it a green suite proves
  nothing — CLAUDE.md §8): apply a `scope_by` to procurement in a scratch copy → its
  comparison reddens; restore. **[offline/DB]**
- [ ] **AC-5 — link-row semantics follow the new bound.** A visitor-fired run's gate now
  decides only the visitor's case, so `on_resolved` writes **one** link row and the
  demo-scoped rows stop existing for visitor runs.
  `tests/api/test_fleet_demo_reset_coexistence_scenario.py` is re-authored per its own
  embedded instruction: `test_a_visitor_fired_runs_gate_also_decides_the_seeded_demo_case`
  (`:289-315`) was built to redden first on exactly this change and says *"do not
  simply delete this assertion"* (`:310-314`) — it inverts to assert the new bound
  (exactly the visitor's case, with its own positive control); the deletion/survival
  test's demo-scoped preconditions (`:335-342`) are re-homed onto the **seeded demo
  run's** rows so the both-key deletion (`services/db/demo_run_reset.py:208-239`)
  stays witnessed non-vacuously. The `_DELETE/RETAIN` map + id-reuse rationale
  (`demo_run_reset.py:131-149`) is re-read and its comments corrected where the
  population claim narrows; the deletion code itself is expected unchanged (the
  seeded runs still write demo-case rows) — verify, don't assume. **[offline/DB]**
- [ ] **AC-6 — the demo survives, offline.** With the fleet clause authored and
  `when_absent: sweep`: the operate seed boots, the seeded run parks at `approve` with
  a non-empty `output_set`, and `read_demo_state` reads `PRISTINE`
  (`demo_run_reset.py:179-205`). Witnessed RED: flip fleet to `when_absent: refuse` in
  a scratch copy → the seed's run refuses at intake and the state reads `CONSUMED`.
  **[offline/DB]**
- [ ] **AC-7 — the governance record is complete** *(GATED on OQ-1 — do not start the
  `done/` edits before Cray answers)*: the SD-4 reversal recorded beside the ruling
  with lineage intact; `done/0112` AC-7(i)'s narrowing and AC-2's s243 correction
  marked `superseded by new info` with pointers to this PLAN (never erased);
  `done/0110`'s post-archival amendment updated for the new population bound; STATUS's
  fleet-wide-scan narrative (`docs/STATUS.md` §'Current Focus') superseded on the next
  reconcile. Candidate mechanism: the additive `§Post-archival amendment` convention
  (PLAN-0100/0102; used at `done/0110`, executed by 0112 AC-7(ii)). Doc-read pass:
  each edit is additive, the ruled history above it untouched verbatim.
- [ ] **AC-8 — the offline gate is green at CI scope** (the offline oracle is the gate,
  CLAUDE.md §8): full `pytest tests/`, `mypy --strict services/ verticals/`, bare
  `ruff check .`, `ruff format --check .` — counts recorded against the Step 0
  baseline (s246 reference: 4267 passed / 8 skipped). **[offline]**
- [ ] **AC-9 — live evidence on MS-S1** *(evidence, not a gate)*: the visitor flow
  driven end to end on the live system shows a single-proposal gate; the demo reset +
  reseed still reads `PRISTINE`. 🔴 **Requires a typed Cray go per occasion AND per
  phase (CLAUDE.md §8 Host-State Actions; `DEPLOY.md` §0). The go is NOT held at
  drafting time — Step 8 must ask, not assume.** **[live/gated]**

## Out of Scope

- ❌ Rebuilding the seeded demo into 3 separate runs (the parked multi-candidate gate
  IS the seeded beat; SD-4's option (c) was priced self-defeating and stays rejected).
- ❌ Changing `approve`/`fulfill`'s two-gate shape — engine-enforced by
  `_check_no_auto_downstream_of_gate` (`services/engine/procedures/orchestrator.py:669`),
  red-team AC-9, guarded by `tests/services/engine/procedures/test_red_team_at2.py`.
- ❌ Any UI/copy work on the gate panel (the intro-video panel question is OQ-4, a
  pointer, not work here).
- ❌ Adopting `scope_by` in procurement or any other vertical (OQ-3).
- ❌ Any generator/lift work beyond classifying the new fields (SD-2); the generator
  emits neither field either way.

## Steps

### Step 0 — Baseline

Full `pytest tests/`, `mypy --strict services/ verticals/`, bare `ruff check .`,
`ruff format --check .`; record exact counts (s246 reference: 4267 passed / 8 skipped).
Capture procurement's hero-run observable(s) for the AC-4 comparison. The offline gate
must match CI scope — no path-scoped shortcuts.

### Step 0b — ADR-016 amendment (PREREQUISITE, added at review after OQ-2 was RULED)

OQ-2 is ruled YES, and `CLAUDE.md` §8 states plainly: **"All ADRs: must be merged before
related implementation PR."** So the amendment is a *prerequisite of Step 1*, not
parallel work: the new grammar member (`scope_by` / `when_absent`) plus SD-2's
governance classification, as a lightweight ADR-016 amendment following the PLAN-0061
Q4 precedent. Authoring a new/amended ADR is **G1/G2-gated for Code** (CLAUDE.md §6) —
route it Cowork/`plan-drafter` drafts → Code commits via PR. Pass read: the ADR is
merged to `main` before the Step-1 PR opens.

### Step 1 — Grammar (`spec.py`), consuming nothing yet

`scope_by: {field: <name>, from: trigger.entity_ids}` (D2 — `from` is a closed
`Literal["trigger.entity_ids"]`, the only source in v1) + `when_absent: sweep | refuse`
(D1 — per-step) on the query step's input model, `extra="forbid"` like its siblings.
Load-gate validation: query-step-with-`reads` only; `when_absent` **required-explicit**
whenever `scope_by` is present (SD-1, RULED). Classification per SD-2 (RULED): H-governed,
generator never emits, stripped at lift, pinned in the governance snapshot when supplied.
🔴 Only-when-supplied serialization (AC-1). Pass read: all 6 verticals
load; hash test byte-identical; the scratch always-present mutation reddens it.

### Step 2 — Wire `trigger_context` → `query_step`

Executor-side resolution against `ctx.trigger_context["entity_ids"]`; membership
semantics + attachment point exactly as pinned in "the verified mechanism" above (base
rows, post-`where`, pre-join, pre-`latest_per` — both the single-read path
`query_step.py:434-439` and the join path `:486-491`). "Absent" = no `entity_ids` list
on the context (missing key, non-list, or empty). `sweep` → byte-identical to today;
`refuse` → typed refusal (additive `ReadRefusalKind` member). Scope provenance entry
with counts. Pass read: AC-2's four-way battery, one probe per assertion.

### Step 3 — Author the fleet clause

`intake` (`verticals/fleet_maintenance/procedures.yaml:180-201`) gains
`scope_by: {field: case_id, from: trigger.entity_ids}` + `when_absent: sweep`. The
`case_id` field exists on the base read's rows: every real case event is built by
`build_event`, which stamps `"case_id": facts.case_id`
(`verticals/fleet_maintenance/case_events.py:95`, called from
`case_projection.apply` → `case_projection.py:149`).
_[Citation corrected at review (Code, s249): the draft cited `synthetic.py:269`, which is
the **fixture's** hardcoded case_id, not the projection's stamp. The claim held; the
pointer did not, and following it would suggest only fixture rows carry the field.]_
⚠️ Note the corollary, which is load-bearing for AC-3: the three ROUTINE fixture
events (`event-reading-01/03/04`) carry **no** `case_id`, so under the membership
semantics above they never match — correct, and the reason a scoped intake returns the
firing case's row alone. Pass read: AC-3's scenario battery — exactly-one proposal, the
two-gate walk green, the sub-ceiling no-gate observable, and the remove-the-clause RED.
Note: setting a supplied field moves **fleet's** governance hash deliberately and only
fleet's — in-flight fleet runs keep their pin and fail closed on mismatch, as designed
(the `ratification_window_days` precedent, `procedures.yaml:348-352`).

### Step 4 — Regression gate (AC-4)

Procurement event path + 11 manual/schedule procedures vs the Step 0 baseline, with the
scratch positive control. This is the PLAN-level positive control: without it, a green
suite proves nothing about "unchanged".

### Step 5 — Link-row semantics + `demo_run_reset` (AC-5)

Re-author the coexistence suite per its own tripwire instruction; re-home the
non-vacuity preconditions onto the seeded run's rows; re-verify (not assume) that the
both-key deletion and the `_DELETE/RETAIN` map survive unchanged; correct their
population-claim comments.

### Step 6 — Demo integrity, offline (AC-6)

Boot the operate seed against a disposable DB; assert `PRISTINE`; the scratch
`refuse`-flip RED.

### Step 7 — Governance records (AC-7) — **blocked on OQ-1**

The four record sites, additive-only, lineage intact. If OQ-1 resolves against editing
`done/`, fall back to recording the supersessions in THIS PLAN + STATUS and leaving
pointers unwritten in `done/` — surface that outcome to Cray rather than improvising a
third mechanism.

### Step 8 — Live verification on MS-S1 (AC-9) — **gated**

Ask for the typed go per occasion and per phase (deploy, reset/reseed, visitor walk).
The offline oracle (Steps 0–7) is the gate; this step is evidence. Minimize live runs.

## Blast radius — 13 sites (12 from the s249 fact pack, each re-verified; #13 found at drafting)

1. `services/engine/procedures/spec.py` — new grammar (Step 1; the only-when-supplied
   constraint, AC-1).
2. `services/engine/procedures/query_step.py` — the wire (Step 2).
3. `verticals/fleet_maintenance/procedures.yaml:180-201` — the clause (Step 3).
4. `tests/api/test_case_acceptance_fires_governed_run_scenario.py:182-193` — tighten
   `_assert_run_is_about`; `:406-417` two-gate walk stays green (Step 3).
5. `tests/api/test_fleet_demo_reset_coexistence_scenario.py` — 4 tests, 3 non-vacuity
   probes, built on the fleet-wide-scan premise; its own tripwire test names this
   change (Step 5).
6. `services/db/demo_run_reset.py:131-149,:208-239` — comments narrow; code expected
   unchanged, verified not assumed (Step 5).
7. `done/0112:412-427,:443-466` — AC-7(i)'s NARROWED clause (Cray, typed, s246): its
   whole justification is the fleet-wide scan → `superseded by new info`, pointer with
   lineage (Step 7, OQ-1).
8. `docs/plans/done/0110-*.md` — the post-archival amendment's population bound changes
   (Step 7, OQ-1).
9. `done/0112` SD-4 (`:1002-1039`) — record the reversal beside the ruling (Step 7,
   OQ-1).
10. `docs/STATUS.md` §'Current Focus' — the fleet-wide-scan narrative (Step 7). Cited by
    section, never by line: R7 forbids line-number citations of STATUS because R2/R6
    re-prune it every reconcile, so the number rots by construction
    (`docs/runbooks/memory-architecture.md` §'R7'; the `status-citation-guard`
    pre-commit hook enforces it, and it caught exactly this in the s249 fact pack).
11. Procurement's event path — proven unchanged (Step 4).
12. The 11 manual/schedule procedures — proven unchanged (Step 4).
13. **Found at drafting:** `done/0112:885-894` — AC-2's pass read was re-fixed s243 to
    "**every** visitor-fired run gates, sub-ceiling or not" *as a direct SD-4(a)
    consequence*; under (b) a sub-ceiling acceptance again completes with no gate.
    Record with the same supersession pointer (Step 7, OQ-1) and assert the behaviour
    in AC-3.

Do not treat this list as complete — the s202 lesson (an inherited defect list is not an
enumeration): Step 2's implementer re-greps `trigger_context`, `entity_ids`, and
`fleet-wide` before closing AC-4.

## Surfaced decisions

- **SD-1 — RULED (Cray, typed, s249, 2026-08-23): required-explicit.** A `scope_by`
  without an explicit `when_absent` is a **load-gate refusal**. Cray took the
  recommendation; the reasoning recorded below is the PLAN's, not Cray's. This is now
  LOCKED for Step 1 and AC-1.
- **SD-2 — RULED (Cray, typed, s249, 2026-08-23): mirror `join`/`project` exactly.**
  `scope_by`/`when_absent` are H-governed values the generator may never emit, stripped
  at lift, pinned in the governance snapshot when supplied. Cray took the
  recommendation. LOCKED for Step 1 and AC-1.

_The original option texts are retained verbatim below (the PLAN-0111 convention): a
future reader must see what was rejected and why._

- **SD-1 (as posed) — is `when_absent` REQUIRED whenever `scope_by` is present, or defaulted?**
  Cray's D1 fixes that the policy is per-step YAML; it does not fix whether omitting it
  is a load error or picks a default. **Recommendation: required-explicit** (load-gate
  refusal when `scope_by` is present without `when_absent`) — a silent default is
  exactly the fail-open/fail-closed ambiguity D1 exists to remove, and the project has
  already retired one fail-open default at this same gate (the PLAN-0096 `compliance`
  retirement, `procedures.yaml:237-250`). Alternatives: default `refuse` (fail-closed,
  but silently breaks any future `sweep`-intending author) or default `sweep`
  (fail-open — worst). Why Cray: it sets the authoring contract every future vertical
  inherits.
- **SD-2 (as posed) — governance classification of `scope_by`/`when_absent`.** `join`/`project`
  are "H-governed values the generator may never emit — stripped at lift, pinned in the
  governance snapshot" (`spec.py:346-351`). Scope changes **what population reaches a
  gate**, which is governance behaviour. **Recommendation: mirror join/project exactly**
  (generator never emits; pinned when supplied; only-when-supplied keeps absent
  verticals' hashes stable). Alternative: treat as plain read config (weaker; nothing
  pins the scoped-vs-sweeping distinction a run was approved under). Why Cray: it
  decides what the governance pin *means* for scoped runs.

## Open questions — record, do not resolve here

- 🔴 **OQ-1 (BLOCKS Step 7 / AC-7): how may Code record a supersession inside
  `docs/plans/done/`?** _[**Re-posed at review (Code, s249)** — the question as first
  drafted ("may Code edit `done/` at all?") was **too broad, and measurement narrowed
  it**. It is still the worked negative example in
  `.claude/skills/decision-lookup/SKILL.md:54,:130`, but that entry is about the absence
  of a **general** ruling, not about the absence of practice.]_

  **Measured s249 — the additive form already has six precedents, all merged:**
  `git grep -ln 'Post-archival amendment' -- docs/plans/done/` returns **6 files**
  (`0008`, `0035`, `0100`, `0102`, `0110`, `0112`). The most recent, `done/0110`'s
  `## Post-archival amendment — 2026-08-22 (session 245)`, landed in PR #1257 at
  `ee41b55` — **the commit currently deployed to production** — executing PLAN-0112
  AC-7(ii), whose pass read was verified at s245.

  🔴 **But the two forms are NOT equally precedented, and the distinction is the
  question:**
  - **Additive `## Post-archival amendment` section, appended, ruled history untouched**
    → **6 precedents.** Sanctioned in practice.
  - **Inline bracketed marker written into `done/` post-archive** → **zero precedents.**
    `done/0112` carries exactly one inline marker (AC-7(i)'s `_[NARROWED (Cray, typed,
    s246)...]_`), and `git log --follow` shows it was written in `2095e6e` — *the very
    commit that archived the file*, i.e. while it was still an active PLAN. No commit
    has ever added an inline marker to an already-archived PLAN.

  **The tension this creates.** CLAUDE.md §6 and the `decision-lookup` skill's Step 4
  both require correcting **in place**, "so a reader who stops at the old text is
  stopped *by* it". An appended section alone does not stop that reader — but the
  in-place form is exactly the one with no precedent in `done/`. Sites 7, 9 and 13 are
  in-place-shaped; site 8 is additive-shaped.

  **Recommendation: (b) — additive section carries the full record, PLUS a one-line
  inline pointer at each superseded site** (e.g. `_[Superseded s249 by PLAN-0113 — see
  §Post-archival amendment below]_`), with ruled history otherwise untouched verbatim.
  It satisfies §6's stopped-by-it requirement with the smallest possible extension to a
  convention that already exists, and it never rewrites a ruling. Alternatives:
  **(a) additive section only** — precedent-perfect, but the archive's old text still
  reads as live to anyone who stops there; **(c) touch `done/` not at all** — record the
  supersessions in this PLAN and STATUS only, which leaves four archived artifacts
  asserting a behaviour the code no longer has.

  **Still Cray's call — a recommendation is not a ruling.** The PLAN gates Step 7 and
  does not assume an answer.
- **OQ-2 — RULED (Cray, typed, s249, 2026-08-23): YES, a lightweight ADR-016 amendment**
  (the new grammar member + the SD-2 classification), consistent with the PLAN-0061
  join/project precedent (ADR-016 Q4, Accepted 2026-07-09). Cray took the
  recommendation. 🔴 **Consequence, binding: `CLAUDE.md` §8 requires the ADR to be
  MERGED before the related implementation PR.** The ADR is therefore a prerequisite of
  Step 1, not a parallel task — and authoring a new ADR is itself G2-gated for Code
  (CLAUDE.md §6), so it routes Cowork/`plan-drafter` drafts → Code commits. Add it to
  the execution order ahead of Step 1.
- **OQ-3: should procurement's `emergency_sourcing_round` adopt `scope_by`?** Out of
  scope here; named so it is not lost. Its firing entity is an asset, so D2's
  field-name-in-YAML shape covers it without engine change.
- **OQ-4: does the intro-video storyboard need a re-read** now that a visitor run shows
  1 candidate while the seeded demo run still shows 3?
  `docs/strategy/public/intro-video-production-rulings.md` §5 item 2 (`:172-177`) is
  already **Undecided** on exactly this panel ("3 candidates reached this gate").

## Verification

- Steps 0–7 offline: the AC-1..AC-8 pass reads above, each pre-committed, each with its
  witnessed-RED probe battery (probe discipline: `/tmp` copy, sha256-verified restore,
  `PYTHONDONTWRITEBYTECODE=1`, one mutation per assertion, positive controls for every
  zero/absence claim, and each probe proves its mutation reached the code).
- The offline oracle is the gate (CLAUDE.md §8). Step 8's live walk is evidence only,
  and only after a typed per-occasion, per-phase Cray go.
- Completion: all ACs ticked (AC-7 possibly narrowed by OQ-1's answer — surfaced, never
  silently dropped), then `git mv docs/plans/0113-*.md docs/plans/done/` per CLAUDE.md
  §6 — by Code, via PR.
