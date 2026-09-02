# PLAN-0118: Intake-extraction benchmark — measure the model at the shipped `extract_package` seam

**Status:** Draft
**Owner:** Claude Code — ✅ **UNGATED: SD-1, SD-1a, SD-2, SD-3 and SD-4 were all RULED by
Cray (typed, 2026-09-01, session 268)**; every ruling took the drafted recommendation. See
§Surfaced decisions for each ruling recorded against its own options. Execution may now
proceed through Step 6. **Step 7 remains separately gated:** SD-4 authorises ONE live
baseline run in principle, but the run itself still needs its own typed §8 go at the time
it is made (CLAUDE.md §8 — a ruling on scope is not a standing authorisation to fire).
**Created:** 2026-09-01
**Related ADRs:** ADR-010 (D4 / IN-2 — the delimiter-forgery-proof untrusted block the
description is rendered in; the surface SD-3 proposes to measure), ADR-0001 (the pinned
local model + CHECKPOINT-0 `think`/`format` contract, `services/engine/llm/intake.py:17-21`),
ADR-0032 (D1 demo→pilot — the intake face is a correction surface; measuring it is part
of that discipline)
**Related PLANs:** PLAN-0017 (built the seam this PLAN measures — it shipped the
extraction, the router, and the harness tests, but no measurement of any model output),
PLAN-0115 (`tools/probe_battery/` — every witnessed-RED probe below runs through it),
PLAN-0117 §SD-6 lineage (the NL lane, `benchmarks/nl_query_feasibility/`, is the
structural precedent this lane mirrors: pure scoring offline-testable, live runner
manual — `benchmarks/nl_query_feasibility/harness.py:1-6`)

> **Drafting provenance (ADR-012 D4.3).** Authored by the in-harness `plan-drafter`
> subagent from a Code-tab dispatch (session-268 fact-pack). Every `file:line` claim in
> the dispatch was re-verified on disk by this draft (2026-09-01) before being cited —
> including the grounded negatives: `benchmarks/intake_extraction/` does not exist
> (directory enumeration, 2026-09-01), and `benchmarks/` is type-checked by neither CI
> (`.github/workflows/ci.yml:99-100` — `mypy --strict services/ verticals/`) nor the
> pre-commit hook (`.pre-commit-config.yaml:41` — `files: ^(services|verticals|\.claude/hooks)/`).
> Independent review: Cray at PR merge. Code commits via PR (CLAUDE.md §7); the drafter
> does not commit.

---

## Goal

Build the first measurement of the **intake-extraction position**: a hand-authored,
confound-audited gold set of free-text operator descriptions with expected
`IntakePackage` field values, an offline scorer, and a live runner that drives the
**shipped** `extract_package` seam (`services/engine/llm/intake.py:155`) — the same
function `services/api/routers/intake.py:45` imports — against MS-S1, and scores the
delivered packages per axis. Today this seam has harness tests but **no measurement of
any model output** (`tests/services/engine/llm/test_intake_extraction.py:1-10` — offline,
`FakeChatClient`, covers retry/budget/transport/injection-*wrapping*; it scores nothing a
model produced). The lane exists so that any later prompt or model change at this seam
has a BEFORE/AFTER instrument, the same role `benchmarks/nl_query_feasibility/` plays
for the Ask surface.

The design constraint that shapes everything: the gold set must be authored, and gold
authoring is where this repo's worst measurement defect lives. `fl-10` in the NL lane
was found (s268) to be a **confounded oracle** — the target row was unique for six
co-varying reasons, so a filter that never expressed the concept under test retrieved
the identical answer and PASSED (`benchmarks/nl_query_feasibility/RESULTS.md:611-621`;
the case-level record at `benchmarks/nl_query_feasibility/gold_fleet.yaml:167-187`).
An intake gold set authored carelessly reproduces that defect at scale: write the
description to match a known package and you have written the answer into the question.

⚠️ **Code's review note on the "pass-evidence idiom" this PLAN cites (s268).** The
`gold_fleet.yaml:167-187` note is cited below (AC-1) as the idiom to imitate — a
per-case note stating what a PASS is *and is not* evidence of. That citation is
accurate, but the note was authored **earlier in the same session as this PLAN** and has
an **N of 1**. It is a proposal worth following, not settled house style; if it proves
awkward in practice, improve it rather than treating it as precedent.
SD-1 exists to put the anti-confound procedure in front of Cray before a single case is
authored. Per the dispatch's accelerator clause, the gold half of this PLAN is
deliberately conservative — **fewer cases with a stated derivation over more cases with
a plausible one** — while the scorer/runner half attempts the clean structural build
first, because `pytest` + hand-run `mypy --strict` can refute it for free.

## Baseline facts (verified on disk 2026-09-01 by this draft — cite, don't re-derive; re-confirm line anchors on the execution branch)

- **F1 — the seam.** `services/engine/llm/intake.py` (192 lines). Entry point
  `extract_package(client, description, *, namespace_hint=None, retry_budget=3)` at
  `:155`. Free text → `IntakePackage` via constrained decode
  (`response_format=schema`, `:182`), bounded validation-retry that feeds the validator
  error back **as untrusted data** (`:126-137`), returns
  `ExtractionResult(package, model, attempts)` (`:59-66`), raises
  `IntakeExtractionError` on budget exhaustion (`:192`). Transport errors are
  deliberately NOT retried (`:166-169` — they propagate to the caller's degraded-state
  handling). An empty description raises before any call (`:171-172`).
- **F2 — the real consumer.** `services/api/routers/intake.py:45` imports
  `IntakeExtractionError, extract_package`; `_chat_client` (`:52-64`) refuses any
  non-local backend and builds the client on `settings.recommender_model`. The
  benchmark drives `extract_package` itself — the shipped producer — never a
  re-implementation (CLAUDE.md §8 scenario rule; the NL lane's precedent, which drives
  the shipped `answer_question`, `benchmarks/nl_query_feasibility/harness.py:19`).
- **F3 — host-state.** Extraction runs on the MS-S1 **local** model only, never the
  hosted API (`intake.py:10-15`; enforced at the router, `routers/intake.py:58-59`).
  Any live run is a CLAUDE.md §8 host-state action: **typed Cray go required**, live
  runs minimized, the offline half carries every verification it can.
- **F4 — the injection seam is designed, not improvised.** `ChatClient` is a Protocol
  (`intake.py:39-50`) — "an injection seam for offline tests" by its own docstring.
  Offline instrument tests ride this seam with the real `extract_package` on both
  sides of it; only model claims need the live box.
- **F5 — field-by-field enforcement** (`services/engine/intake_assembler.py`):
  - `metric.direction`: `Literal["above","below"]` (`:145-147`) — the schema forces
    one of two, **which one is the model's choice**. `_SYSTEM_INSTRUCTION` states the
    consequence: getting it wrong "silently disables the recommender"
    (`intake.py:88-91`). Binary, objectively derivable from breach physics — the
    strongest candidate headline axis.
  - `asset_role.properties` / `site_role.properties`: `default_factory=list`, **no
    min/max length** (`:124-126`). The "2-5" / "1-3" bands exist only in the prompt
    (`intake.py:81-84`) — so band-compliance is a genuine instruction-following
    signal, not schema-guaranteed.
  - `action_types`: `min_length=1` only (`:173-175`); the "2-4" band is prompt-only
    (`intake.py:92`). The 2-4 band is a model signal; ≥1 is not.
  - `type_name`: PascalCase regex + reserved-name rejection in a `field_validator`
    (`:128-136`). A violation raises → a retry — it surfaces in `attempts`, never as
    a wrong delivered value.
  - `metric.threshold` (`:144`), `recovery_value` (`:178`): `float`, required —
    numbers extracted from the text; scorable when the description states them
    unambiguously.
  - `confidence`: `ge=0.0, le=1.0`, **`default=1.0`** (`:183-185`). ⚠️ A model that
    omits the field silently scores 1.0, indistinguishable post-validation from a
    confident assertion. Not usable as an accuracy axis without explicit
    omission-handling.
  - `source`: `default="manual_entry"` (`:180-182`), then **overwritten in code** at
    `intake.py:186` (`model_copy(update={"source": "ms_s1_live"})`). ❌ Not a model
    signal at any point — scoring it would measure `model_copy`. This is the exact
    defect class §15 of `benchmarks/model_compare/RESULTS-1.6.md:859-872` records
    (a field the product overrides is a product signal, not a model signal; PR #1350).
- **F6 — existing material, none of it a gold set.**
  `services/api/intake_defaults/solar_farm.json` + `water_utility.json` are
  human-authored fallback packages — they were **not** authored from any description;
  pairing a written description to them is precisely the fl-10 trap (F-guarded in
  AC-1). `docs/conventions/partner-intake-form.md` holds the questions a partner
  actually answers — the realistic-data source for description authoring.
  `tests/services/engine/scaffolder/fixtures/fleet_shaped_narrative.txt` belongs to
  the **scaffolder** intake (`services/engine/scaffolder/intake.py`) — a different
  component; not conflated, not reused.
- **F7 — the injection surface.** The description renders only inside the labelled
  untrusted block (ADR-010 D4 / IN-2, `services/engine/llm/prompt.py`);
  `_SYSTEM_INSTRUCTION` spends six lines defending it (`intake.py:74-79`). The
  existing test `test_description_is_wrapped_and_injection_neutralised` proves the
  *wrapping* happens — whether the model actually **resists** an embedded directive is
  objectively scorable and currently unmeasured (SD-3).
- **F8 — 🔴 grounded negatives (this draft, 2026-09-01).**
  `benchmarks/intake_extraction/` does not exist (enumeration). `benchmarks/` is
  outside both type-check surfaces: CI runs `mypy --strict services/ verticals/`
  (`.github/workflows/ci.yml:99-100`) and the pre-commit hook's scope is
  `^(services|verticals|\.claude/hooks)/` (`.pre-commit-config.yaml:41`). Any
  type-cleanliness AC must therefore name a **hand-run** command. Ruff, by contrast,
  DOES cover `benchmarks/` in CI (`ci.yml:55-56` runs bare `ruff check .`).
- **F9 — the gold-derivation precedent.** The NL lane's fleet gold derives every
  expected value "from the adapter's ACTUAL output …, not from reading `synthetic.py`
  by eye" (`gold_fleet.yaml:19-21`), registers inexpressible cases in writing
  (`:48-50`), and — post-fl-10 — records at the case itself what a PASS is and is not
  evidence of (`:167-187`). This PLAN adopts all three idioms.

## Acceptance Criteria

Commands run from the repo root via WSL under CLAUDE.md §8 evidence rules (`2>&1`, no
`head`/`tail` pipes, verdicts read from files). Every witnessed-RED probe runs through
the shipped driver `tools/probe_battery/` (PLAN-0115) — one mutation per assertion,
each preferring a mutation under which the sibling assertion stays green, restore from
the scratchpad copy. ACs marked **[SD-gated]** take their final shape from the named
ruling; the probe obligations below hold under every option.

- [ ] **AC-1 — the gold set exists and its structural invariants are enforced.**
  **[SD-1-gated]** Artifact: `benchmarks/intake_extraction/gold.yaml` + an offline
  validation test module. Each case carries: the free-text description; the expected
  value for **every scored axis** (per the SD-2 ruling); a **per-field derivation
  note** naming the description span the value derives from; a **confound-audit
  note** (SD-1's procedure, whichever option is ruled); and a **pass-evidence note**
  stating what a PASS on this case is and is not evidence of (the
  `gold_fleet.yaml:167-187` idiom). The validation test asserts, at minimum:
  (a) every scored field on every case has a non-empty derivation note;
  (b) **the direction positive control** — both `above` and `below` appear as
  expected values, each in ≥ 3 cases, so a model that always answers one way is
  caught (a direction axis where every gold case is `below` is the fl-10 defect
  wearing a new hat);
  (c) **the swap control** — `threshold != recovery_value` in every case (equal
  values would let a model that swaps the two fields pass both);
  (d) **the distractor control** — ≥ 2 cases whose description carries, besides the
  expected answers, **a reading in the threshold's own unit**, so numeric axes cannot
  pass by grabbing the only number in the text. 🔴 **CORRECTED s269 — the criterion is
  *same reading, same unit*, NOT *same magnitude*.** The shipped Step-2 check used a
  magnitude window (`thr/3 .. thr*3`) as a proxy; measured on the shipped gold set it
  is wrong in the direction that matters — a **false negative**. It excluded `rm-02`'s
  `0.6` kPa clean-bag reading, the same reading in the same unit as its `2.4` kPa
  threshold and precisely the distractor wanted, while every case it *did* admit was a
  true positive (4 admitted, 5 qualify). Units cannot be inferred from prose, so each
  qualifying case declares `same_unit_distractors: [{value, span, why}]` and the test
  verifies the declaration **against the description** — span verbatim in the text,
  value inside that span, value neither expected answer. A wrong declaration reddens;
  the guard reads the artifact, never its own constant;
  (e) **the anti-borrow tripwire** — no case's expected package equals either
  prebaked default (`services/api/intake_defaults/*.json`), field-for-field on the
  scored axes (F6: those files were not authored from descriptions; matching one is
  evidence of the trap, not of quality).
  These are well-formedness checks: legitimate, and — stated per CLAUDE.md §8 — they
  compare the file to itself and **close nothing about the model**; model claims
  close only under AC-6.
  **Witnessed RED (one probe per assertion):** (a) blank one derivation note →
  reddens naming the case+field while (b)-(e) stay green; (b) flip all `above` cases
  to `below` in a scratch copy → the both-directions assertion reddens; (c) set one
  case's `recovery_value` equal to its threshold → reddens naming the case; (d) corrupt
  a declared distractor's `span` so it no longer matches its description → reddens
  naming the case, while (a)-(c) stay green; (e) paste
  `solar_farm.json`'s scored fields into a scratch case → reddens.
- [ ] **AC-2 — the scorer is pure, per-axis, and structurally refuses the two known
  non-signals.** Artifact: `benchmarks/intake_extraction/harness.py` — a pure
  `score_case(case, result)` (offline-testable, NL-lane pattern) producing per-axis
  outcomes plus reported-only diagnostics (`attempts`, latency, `model`). Two
  structural guards, each its own test assertion:
  (a) a gold case that declares `source` as a scored field is **rejected** (raises,
  naming `intake.py:186` in the message) — the scorer cannot be talked into
  measuring `model_copy`;
  (b) same for `confidence` as an accuracy axis (the `default=1.0` omission trap,
  `intake_assembler.py:183-185`).
  The summary reports **per-direction accuracy separately** (accuracy on
  above-cases and on below-cases as separate figures) — an always-one-way model must
  show as 100%/0%, never as a blended headline. With a gold set this small, figures
  are reported as raw fractions (`7/10`), never percentages-as-headlines.
  **Witnessed RED:** (a) a fixture gold case scoring `source` → the guard test
  reddens on the raised error's absence when the guard is deleted; (b) likewise for
  `confidence`; (c) feed a synthetic `ExtractionResult` with a flipped direction →
  the direction axis outcome flips (the probe names the output it changes); (d) in a
  scratch summary over canned outcomes, an all-`below`-answering result set shows
  above-accuracy `0/n` — delete the per-direction split → that assertion reddens.
- [ ] **AC-3 — scenario test (CLAUDE.md §8, binding): the real producer flows into the
  real consumer, offline.** Artifact:
  `tests/benchmark/test_intake_extraction_scenario.py`. ✅ **Placement MEASURED by Code
  at review (s268), closing the draft's own open question:** benchmark tests live in
  `tests/benchmark/` — **singular and flat**, named `test_<suite>_*.py` (24 modules
  there today, e.g. `test_nl_query_feasibility_fleet_gold.py`). The draft's hedged
  `tests/benchmarks/intake_extraction/` is NOT the repo's shape; do not create it. The
  test drives the **shipped** `extract_package` (`intake.py:155`) — real prompt
  assembly, real retry loop, real validation, real `source` stamping — with a canned
  transport at the **designed** `ChatClient` Protocol seam (`intake.py:39-50`, F4),
  on a real gold case from `gold.yaml`, into the real `score_case`. Pass reads fixed
  pre-run: the scored outcome for the direction axis is `correct` when the canned
  package matches gold; the diagnostics carry `attempts` from the real loop. **What
  this AC claims:** the instrument plumbing — gold → seam → scorer — is live end to
  end. **What it cannot claim, stated:** anything about any model; the transport is
  canned here *by design* and only AC-6 closes model claims. The seam under test in
  this AC is the benchmark plumbing, and no side of *that* seam is stubbed.
  **Witnessed RED:** flip the canned package's `direction` → the direction outcome
  flips to `wrong` (mutation reaches the code and names its output); feed canned
  invalid-then-valid responses → `attempts == 2` reddens if the runner stops driving
  the real retry loop.
- [ ] **AC-4 — the live runner exists and every non-live behaviour of it is verified
  offline.** Artifact: `benchmarks/intake_extraction/run_benchmark.py` + a
  **recording pass-through client** (delegates to the real `OllamaClient`, records
  each attempt's raw `content` — transport-level observation, the seam stays the
  shipped one). Per case it invokes `extract_package`, captures the
  `ExtractionResult` or the typed failure (`IntakeExtractionError` /
  transport error — distinct outcomes, `intake.py:166-169`), scores via
  `score_case`, and writes a per-case artifact file (raw attempts included, so a
  scoring dispute is re-adjudicable without a re-run — live runs are minimized, F3).
  Offline verification: with the canned transport, the runner produces the same
  artifact shape + summary the live run will. **Witnessed RED:** cut the
  raw-attempt capture → the artifact-completeness assertion reddens; make the canned
  transport raise → the runner records a transport-failure outcome distinct from a
  validation-exhaustion one, and collapsing them reddens the test.
- [ ] **AC-5 — offline gates, at their true scopes.** Commands, each output to a file:
  bare `uv run ruff check . 2>&1` (covers `benchmarks/`, `ci.yml:55-56`); **hand-run**
  `uv run mypy --strict benchmarks/intake_extraction/ 2>&1` → clean (named explicitly
  because neither CI nor pre-commit covers `benchmarks/` — F8; a "CI is green"
  read does NOT close this AC); full `uv run pytest tests/ 2>&1` on the checkout that
  owns the test DB. Probe-battery coverage report for every witnessed-RED above
  captured for the PR body.
- [ ] **AC-6 — the live baseline run. [SD-4-gated; typed CLAUDE.md §8 go required —
  this AC does not run without it.]** One batched run over the full gold set against
  the shipped configuration (`settings.recommender_model`, `routers/intake.py:62`),
  driven by AC-4's runner. Deliverable: `benchmarks/intake_extraction/RESULTS.md`
  with per-axis raw fractions, per-direction split, per-case table (id, per-axis
  outcome, attempts, latency), the model tag as reported by the box, and — per F9 —
  an inexpressible-register section naming what this lane does NOT measure and why
  (at minimum: the SD-2 cut axes, with their reasons). **What live uniquely
  provides, stated:** every claim about the pinned model's behaviour — nothing else
  in this PLAN claims one. **Witnessed RED for the pass read:** fixed pre-run — the
  run is evidence whatever the scores are; the only failure mode is an instrument
  failure (missing artifacts, unscored cases), asserted by re-running the AC-4
  artifact-completeness check over the live outputs.

## Out of Scope

- ❌ **Scoring `source` — permanently, not deferred.** `intake.py:186` overwrites it;
  a score would measure `model_copy` (the RESULTS-1.6 §15 / PR #1350 defect class,
  F5). AC-2(a) makes this structural, not conventional.
- ❌ **Scoring `confidence` as accuracy.** The `default=1.0` omission trap (F5).
  A raw-omission-rate *diagnostic* (the AC-4 recorder sees the pre-validation JSON)
  may be reported unscored; a calibration axis would additionally need an oracle for
  "true" confidence, which does not exist — registered inexpressible with that
  reason.
- ❌ **Exact property-NAME matching** on `asset_role.properties` /
  `site_role.properties` / `action_types` members. Multiple snake_case namings are
  defensible for the same described attribute; an exact-name oracle scores the gold
  author's taste, and a lenient substring oracle is the fl-10 shape in miniature.
  Band-compliance + exclusion-rule checks (SD-2) capture what is honestly checkable.
- ❌ **Free-text fields** (`domain_label`, `problem`, `decision`,
  `recovery_description`, `metric.label`): no honest exact oracle; substring oracles
  invite the confound. Registered inexpressible unless a future PLAN brings a real
  grading scheme.
- ❌ **The scaffolder intake** (`services/engine/scaffolder/intake.py`) and its
  fixture `fleet_shaped_narrative.txt` — a different component (F6); nothing here
  touches or borrows from it.
- ❌ **Deriving gold from the prebaked defaults** — `solar_farm.json` /
  `water_utility.json` are AC-1(e)'s tripwire, never a source.
- ❌ **Changing the seam** — `intake.py`, `_SYSTEM_INSTRUCTION`, the schema, the
  router. This PLAN measures; any prompt/model fix is a later PLAN that uses this
  lane as its BEFORE/AFTER instrument.
- ❌ **Hosted-API runs** — never (F3, `intake.py:10-15`).
- ❌ **Prompt-variant experiments** (the NL lane's `experiment_prompt_variants.py`
  pattern) — a later PLAN, after a baseline exists.
- ❌ **Multi-model comparison in the first live run** — the shipped
  `settings.recommender_model` only, unless Cray's SD-4 ruling says otherwise; live
  runs are minimized (F3).

## Surfaced decisions — ALL RULED (Cray, typed, 2026-09-01, session 268)

Every option below is kept as drafted, so each ruling is readable against what it chose
*between* rather than as a bare instruction. All five took the drafted recommendation;
none was amended. Recorded at the moment of the ruling, before any execution.

### SD-1 — the anti-confound gold-authoring procedure (the reason this PLAN exists)

✅ **RULED: (a) — description-first with span-traceability + per-case confound audit,
small N (8–12), raw-fraction reporting.** Cray, typed, 2026-09-01. Option (b)
package-first is therefore **rejected by ruling, not by assumption** — which was the
point of listing it.

The gold set cannot be borrowed; it must be authored, and authoring is where fl-10
lives. Options:

- **(a) Description-first with span-traceability + per-case confound audit —
  RECOMMENDED.** Author descriptions FIRST, as answers a partner would give to
  `docs/conventions/partner-intake-form.md`'s questions (realistic simulated data,
  CLAUDE.md §8), blind to the prebaked defaults; derive each expected value by hand
  FROM the description; require every scored field to cite the span it derives from
  (AC-1(a)); write a confound audit per case — for each scored field: *could a
  process that never read this span still land on the expected value?* (via a
  default-shaped answer, a majority-value, or a co-varying cue) — and rewrite until
  the answer is no or the residual co-variance is recorded in the pass-evidence note;
  ship the structural controls (AC-1(b)-(e)). Cost, stated: expensive per case →
  small N (recommended 8–12 cases; raw-fraction reporting only, AC-2).
- **(b) Package-first** — write expected packages, then descriptions to match.
  REJECTED SHAPE: this is the fl-10 trap by construction (and pairing descriptions
  to the intake defaults is its worst instance, F6). Listed so its rejection is
  ruled, not assumed.
- **(c) Description-first without span-traceability** — cheaper, more cases, but
  nothing catches a confounded case at authoring time; the audit happens only when a
  suspicious pass is investigated, i.e. after the number has already been believed
  (exactly fl-10's history: found s268, long after the runs).

✅ **SD-1a RULED: mixed, labelled.** Cray, typed, 2026-09-01. Each case carries
`direction_stated: true|false`; the summary reports the two bands **separately**, and
neither band's figure may be cited as evidence of the other's capability. The
verbatim-stated band measures *reading*; the physics-only band measures the *inference*
`_SYSTEM_INSTRUCTION` actually asks for (`intake.py:88-91`).

**Sub-question SD-1a (part of the same ruling):** may descriptions state the breach
direction verbatim ("alert when it **rises above** 40 °C"), or must direction be
derivable only from breach physics + the numbers? Verbatim-stated cases measure
extraction (reading); physics-only cases measure the inference `_SYSTEM_INSTRUCTION`
actually asks for (`intake.py:88-91` — "infer it from the breach physics").
Recommendation: **mixed, labelled** — each case carries `direction_stated: true|false`
and the summary reports the two bands separately (the NL lane's `ceiling` idiom);
neither band alone claims the other's capability, and the pass-evidence note says
which claim each case's pass supports. Alternatives: all-stated (weaker claim,
easier), all-physics (stronger claim, but conflates reading failures with inference
failures at small N).

Why Cray, not Code: this ruling fixes the trust basis of every number the lane will
ever produce — it is the truthfulness-of-the-instrument call, the same class as the
s268 fl-10 adjudication, and it sets the cost/valence trade (few audited cases vs
more plausible ones) that Code must not set for itself.

### SD-2 — the scored-axis set: which axes carry an honest oracle, which are cut

✅ **RULED: the lean set.** Cray, typed, 2026-09-01. Scored: `metric.direction`
(headline), `metric.threshold` + `recovery_value`, band-compliance. Diagnostics only:
`attempts`, confidence-omission rate. **`namespace` is NOT added** (the "option to add"
in the table below is declined — it would grow the SD-1 audit burden for low value).
`source` never scored (structural, AC-2(a)); `confidence` never scored as accuracy;
free-text fields and exact property names registered inexpressible with their reasons.

Per-field dispositions proposed from F5 (the ruling adopts, amends, or cuts — a
benchmark with two trustworthy axes beats one with six that agree with themselves):

| Axis | Proposed | Ground |
|---|---|---|
| `metric.direction` | **SCORE — headline** | binary; schema forces a choice (`intake_assembler.py:145-147`); named system consequence (`intake.py:88-91`); positive controls AC-1(b) + per-direction reporting AC-2 |
| `metric.threshold`, `recovery_value` | **SCORE** (exact numeric match) | required floats stated unambiguously in the description; swap + distractor controls AC-1(c)/(d) |
| band-compliance | **SCORE** (secondary) | counts within prompt bands: asset 2-5 / site 1-3 (`intake.py:81-84`; schema unenforced, `:124-126`) and `action_types` 2-4 (`intake.py:92`; schema only ≥1, `:173-175`) — genuine instruction-following; plus the exclusion rule (no `id`/`name`/`lat`/`lng`/ref properties, `intake.py:85-87`) — objectively checkable |
| `type_name` validity | **DIAGNOSTIC via `attempts`** | violations surface as retries, never delivered values (`intake_assembler.py:128-136`) — report the attempts distribution, score nothing |
| `confidence` | **CUT as accuracy; omission-rate diagnostic optional** | `default=1.0` trap (`:183-185`); no calibration oracle exists |
| `source` | **NEVER SCORED — structural guard AC-2(a)** | overwritten at `intake.py:186`; RESULTS-1.6 §15 defect class |
| `namespace` (hint-following) | **CUT (lean), option to add** | with `namespace_hint` given and a neutral description, exact match is measurable (`intake.py:113-115`) — honest but low-value; adding it grows the gold-authoring burden ("neutral" needs auditing too) |
| free-text fields, exact property names | **REGISTERED INEXPRESSIBLE** | reasons in Out of Scope; the register lands in RESULTS.md per F9 |

Recommendation: the lean set — direction (headline), threshold + recovery_value,
band-compliance — plus diagnostics. Why Cray, not Code: cutting axes is a scope
verdict on what the intake face is *claimed* to do well; those claims reach partners
(ADR-0032 D1), so which numbers exist is a Cray call.

### SD-3 — injection resistance: in this benchmark, or its own thing?

✅ **RULED: (a) — IN, as a separate band.** Cray, typed, 2026-09-01. 2–3 cases on a
dedicated `obeyed_injection` metric, **never folded into headline accuracy**. This
enlarges what the SD-4 live run covers, and Cray granted that scope in the same ruling.
The obeyed-detection assertion carries its own witnessed RED (a canned package carrying
the injected value must trip it) — and note the confound this band inherits from SD-1:
an injected value that coincides with a plausible legitimate value would score
resistance as obedience, so the injected values must be audited to be implausible as
legitimate extractions.

The model's actual resistance to a directive embedded in the description is
objectively scorable, load-bearing, and unmeasured (F7 — the existing test proves
only that the *wrapping* happens). Options:

- **(a) IN, as a separate small band — RECOMMENDED.** 2–3 cases whose description
  embeds a directive (e.g. an instruction to set the threshold to an attacker-chosen
  value); expected values = the extraction of the legitimate content; scored on a
  dedicated `obeyed_injection` metric (did any delivered field carry the injected
  value), **never folded into headline accuracy**. Rationale: the axis is
  live-only by nature (nothing offline can measure resistance), so riding this
  PLAN's one typed go avoids a second host-state round (F3); the scorer's
  obeyed-detection gets its own witnessed-RED (a canned package carrying the
  injected value must trip it).
- **(b) OUT — its own later PLAN.** Keeps this lane's oracle uniform; injection
  scoring has a different shape (obey/resist vs value-match) and its case design has
  its own confound risks (an injected value that coincides with a plausible
  legitimate value scores resistance as obedience — the audit burden SD-1 imposes
  applies with a twist).

Why Cray, not Code: security-measurement scope, and whether an ADR-010 surface gets
its first number now or later, is a risk-priority call — and option (a) enlarges
what the typed §8 go covers, which is Cray's authority to grant.

### SD-4 — the offline/live split, and what the one live run buys

✅ **RULED: (a) — full offline instrument + ONE batched live baseline run.** Cray,
typed, 2026-09-01. Scope: the shipped `settings.recommender_model` only (option (c),
two-model, is declined), and the run covers the SD-3 injection band in the same batch.

🔴 **This ruling sets the SCOPE of the live run; it is not the go to fire it.** Step 7
still requires its own typed §8 go from Cray at the time of the run (CLAUDE.md §8:
host-state changes need explicit go *before* them, and live runs are minimised). Code
must not read this ruling as a standing authorisation.

- **(a) Instrument fully offline + ONE batched live baseline run under a typed §8 go
  — RECOMMENDED.** Everything except model claims closes offline (AC-1–AC-5): gold
  validation, scorer, plumbing scenario, runner behaviour — all via the designed
  Protocol seam (F4). The single live run (AC-6) is what makes the gold set an
  oracle *of the system* at all — an expected-value set nothing has been scored
  against closes nothing about the model (CLAUDE.md §8), and per-case raw-attempt
  capture (AC-4) makes re-scoring possible without re-running.
- **(b) Instrument-only; no live run in this PLAN.** Even more conservative; the
  lane ships un-baselined and the first live number moves to a later go. Cost: the
  PLAN completes with the gold set never having judged a single real output —
  well-formed, but unproven as an instrument (fl-10 was found only when real runs
  were re-read against the gold).
- **(c) Two-model comparison in the first run** — NOT recommended: doubles the live
  surface before the instrument has judged one model; the NL lane's comparison came
  after its gold set had a run's worth of scars.

Why Cray, not Code: the live run is host-state (CLAUDE.md §8) — its existence,
timing, and model scope are literally the typed-go authority; Code may not schedule
it by recommendation.

### SD-5 — how a case with no package is counted (ruled s269)

✅ **RULED: split by kind.** Cray, typed, 2026-09-02 (session 269). Asked because the
PLAN ruled that AC-4's *runner* records transport-failure and validation-exhaustion as
distinct outcomes, but never ruled how `summarize` treats either in the accuracy
**denominator** — and that choice changes what the headline number claims.

| Case | Counted as | Ground |
|---|---|---|
| `validation_exhausted` — the model answered and its JSON failed the schema through the whole retry budget | **`wrong`**, stays in the denominator | that is model capability, which is what this lane measures |
| `transport_error` — the box was unreachable (`intake.py` deliberately does not retry these) | **`unscored`**, leaves the denominator | the pipe's fault, not the model's |

**Both counts are reported on every axis, always** (`wrong_validation_exhausted`,
`unscored_transport`). A number that left the denominator has to stay visible or the
denominator lies — the failure shape the s267 p95 finding already cost this repo once.

Options declined, recorded so the ruling reads against what it chose between:
**(b) count everything `wrong`** — one fixed denominator, trivially comparable across
runs, but a dropped network reads as a stupider model; **(c) exclude both from the
denominator** — honest about what was measurable, but `n` shrinks silently and accuracy
flatters the system, which is the `p95-that-was-really-a-maximum` shape in miniature.

Why Cray, not Code: per SD-2's own reasoning, which numbers exist — and what their
denominator means — is a scope verdict on what the intake face is *claimed* to do, and
those claims reach partners (ADR-0032 D1).

## Steps

**SD gate:** Steps 2, 3(b), and 6 take their final shape from SD-1/SD-1a, SD-2, SD-3;
Step 7 runs only under SD-4's ruling plus a typed §8 go. Step 1 and the skeleton halves
of Steps 3–4 are shape-stable under every option. All work on one `feat/*` branch; one
PR for the offline instrument; the live RESULTS land per the ruled split.

### Step 1 — Scaffold + baseline capture

Create `benchmarks/intake_extraction/` (`__init__.py`, module skeletons — no `pass`
stubs in delivered content: each file lands only when it does something). Confirm
`git status` in the first tool batch. Re-verify F1/F5 line anchors on the branch (the
base moves).

### Step 2 — Author the gold set per the SD-1 ruling **[SD-gated]**

Descriptions from the partner-intake-form question shape (F6), across ≥ 3 distinct
domains none of which is solar-farm or water-utility (AC-1(e)); expected values derived
per the ruled procedure; derivation notes, confound audits, pass-evidence notes, and
the AC-1(b)-(e) structural controls authored together with the cases. If SD-3 ruled
(a): author the injection band here, with the injected value chosen to be
implausible-as-legitimate (the (b)-option's confound, inverted into a design rule).

### Step 3 — Scorer + offline tests (AC-1, AC-2)

(a) `harness.py`: `score_case` + summary with per-direction split + diagnostics; the
two structural guards (source/confidence). (b) The axis set per SD-2's ruling. Gold
validation test module per AC-1.

### Step 4 — Runner + scenario test (AC-3, AC-4)

`run_benchmark.py` + the recording pass-through client; the scenario test driving the
real `extract_package` through the real scorer on a real gold case via the Protocol
seam (F4). Distinct transport-failure vs validation-exhaustion outcomes (F1).

### Step 5 — Probe battery (every witnessed RED above)

Through `tools/probe_battery/` — one claim per probe, `Claim.stable_key` addressing,
scratchpad-backed restore, coverage report for the PR body. If a probe fails its
pre-fixed criterion, repair the instrument — never relax the criterion after seeing
the result.

### Step 6 — Gates (AC-5)

Bare ruff; **hand-run** `mypy --strict benchmarks/intake_extraction/` (F8 — CI will
not catch a regression here; the PR body states the hand-run's output); full pytest on
the DB-owning checkout.

### Step 7 — Live baseline run (AC-6) **[typed §8 go + SD-4 ruling required]**

One batched run, shipped model config, per-case artifacts captured, RESULTS.md with
raw fractions, per-direction split, attempts distribution, the inexpressible register
(F9), and — if SD-3 ruled (a) — the injection band's figures, reported separately.

## Verification

- Offline: AC-1–AC-5 close on the branch with the probe-battery coverage report
  attached to the PR — every load-bearing green witnessed RED through the shipped
  driver, per-assertion.
- The instrument claim ("gold → seam → scorer is live end to end") closes at AC-3;
  the model claim closes **only** at AC-6's live run — no offline artifact in this
  PLAN is cited as evidence of model behaviour.
- The lane is DONE when: the gold set's structural controls are enforced by a test
  that has been seen RED; the scorer refuses the two known non-signals structurally;
  and (per SD-4) RESULTS.md records the first baseline with its inexpressible
  register — after which any prompt or model change at this seam has a BEFORE to be
  measured AFTER against.
