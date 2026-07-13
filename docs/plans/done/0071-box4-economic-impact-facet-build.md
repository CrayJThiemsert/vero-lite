# PLAN-0071: Box-4 economic-impact facet — build (ADR-0030 fast-follow)

**Status:** Complete — built + merged across **PR1 (#731, `feat` — engine core +
RED marker)** and **PR2 (#732, `feat` — four per-vertical producers + GREEN flips)**,
session 127 (2026-07-14). All 10 ACs met: AC-5 ≥3-vertical build-completion marker
**GREEN at N=4** (the RED `xfail(strict=True)` phase in PR1 proved it genuinely failed
pre-producers, discharging the ADR-016 erosion class with an OWNED marker); AC-9 GREEN
(the real energy producer makes a composed action carry exactly one `economic_impact`
step, net ฿405,000); the ADR-007 D2 envelope (`services/engine/actions.py`) byte-untouched.
Evidence: full suite **2591 passed / 7 skipped / 0 xfailed** WITH Postgres, verified on
both the PR head and the merge commit `b11ea40`; ruff + `ruff format --check` +
`mypy --strict services/` clean; deterministic-offline (no MS-S1 / host-state). SD-A…SD-G
ratified by Cray (session 126, all seven as-recommended via AskUserQuestion). Coupled-test
audit (every pin PINNED-UNMODIFIED) + the OQ-C procurement anchor-resolution fallback
disclosed in the #732 body.
**Owner:** Claude Code
**Created:** 2026-07-13
**Related ADRs:** **ADR-0030 (Accepted 2026-07-13, s126) — THE ratified contract
this PLAN builds**; its D6 fixed the ADR as contract-only and named this
fast-follow build PLAN. Also: ADR-007 D2 (the untouched "verbatim" envelope),
ADR-0022 / PLAN-0035 (the advisory trace-carried precedent the emission copies),
ADR-016 (the discharged deferral; its never-built N ≥ 3 marker is why AC-5
exists — ADR-0030 D4-3), ADR-0023 (registry auto-discovery — the producer-wiring
seam), ADR-0026 OQ-6 / PLAN-0044 AC-10 (the marker-that-WAS-built style AC-5
mirrors), PLAN-0045 (the demo ฿ ledger = the D3 shape prototype, untouched).

> **Author≠reviewer disclosure (ADR-012 D4.3).** Drafted by the in-harness
> `plan-drafter` subagent (ADR-013 D1 phased authoring) from a Code-originated
> session-126 dispatch (grounded fact-pack F1–F5 + SD leans explicitly marked as
> Code's inferences, NOT Cray decisions); every cited `file:line` was
> re-verified on disk 2026-07-13 during this drafting. Independent reviewers =
> Code R2 (re-verify citations, commit per ADR-009 D2) + Cray at SD
> ratification. Drafter ≠ committer ≠ ratifier — separation INTACT.
> **Drafter findings** the dispatch did not list:
> (i) the exact-order trace pin `tests/services/engine/llm/test_trace.py:66`
> (`["ontology_query", "llm_inference", "rule_check"]`) is on the **helper**
> `build_llm_reasoning_trace`, not the composed action — the facet must append
> at the composition sites and NEVER inside the helper, or that pin breaks;
> (ii) a raising economic producer inside `recommend()`'s IN-4 `try`
> (`recommender.py:203-249`) would **demote a good LLM judgment to the
> `_rule_recommend` fail-safe** — strictly worse than losing the facet — so the
> emission helper must be never-raise **by contract**, exactly the discipline
> the advisory judge documents ("this call never raises… so it stays out of
> the IN-4 contract", `recommender.py:226-228`), and AC-6 tests it;
> (iii) `_compose_llm_record` is called **positionally with 6 args** by the
> golden-trace composition test (`tests/services/engine/eval/test_eval_harness.py:97-99`)
> — the new parameter ripples there; that test's own comment (`:94-96`)
> records the identical PLAN-0030/PLAN-0035 param-add precedent;
> (iv) `_compose_action` appends **nothing** today (`action_step.py:178` is a
> bare `build_llm_reasoning_trace(...)`) — the economic step would be the FIRST
> appended advisory step on the governed composition; the
> `outcome.reasoning_trace[0]` pins in `test_action_step.py:116,133` are on the
> **StepOutcome dict telemetry trace** (`orchestrator.py:90`), a different
> trace — unaffected, named here to prevent confusion at R2;
> (v) `actions.py` already outgrew its "four models" docstring — `ControlRef` +
> `GovernedDecision` landed beside the contract via PLAN-0044
> (`actions.py:33-66`) — precedent for adding trace-payload models to the
> module, and the `:11` "verbatim" line needs one clarifying sentence (a
> disclosed, docstring-level diff to the contract module);
> (vi) procurement's real-฿ path is **async** (`ledger.py:39` awaits
> `fetch_objects`/`fetch_links`) while both compose sites are sync — but both
> CALLERS are async (`recommend()` `recommender.py:189`;
> `ActionStepExecutor.execute` `action_step.py:253`), so the facet threads
> through exactly like `verification_steps`: computed in the async caller,
> passed as a parameter. Also procurement's OperationalEvents carry
> `measured_value` = criticality, not ฿ (`synthetic.py:125-170`) — even
> procurement needs adapter fetches at emission time, not event fields;
> (vii) discovery failure-isolation is per-VERTICAL (`discovery.py:53-57`): a
> naive required import of a new `economic_impact` producer module would knock
> out a vertical's ENTIRE registration — the optional import must be guarded on
> `ModuleNotFoundError` with `exc.name` checked (only the producer module
> itself missing = fine; a broken transitive import must still surface).

## Goal

Build the ADR-0030 Box-4 economic-impact (฿) facet: engine-owned
`EconomicExposure` + `EconomicImpact` Pydantic models (the D3 sketch, finalized
by AC-1), a **never-raise** shared emission helper producing an **advisory,
append-only** `ReasoningStep(kind="economic_impact",
detail=EconomicImpact(...).model_dump(mode="json"))`, wired at the
`RecommendedAction` composition site(s) per SD-A
(`recommender.py:176-178` reactive; `action_step.py:178` governed), plus
per-vertical ฿ producers per SD-B/SD-C, and the **ADR-0030 D4-3 ≥ 3-vertical
build-completion assertion (AC-5)** — the enforcement that replaces ADR-016's
promised-but-never-built N ≥ 3 marker, this time owned by a named AC. Zero
change to the ADR-007 D2 "verbatim" envelope (`actions.py:11`); zero governance
impact (`reasoning_trace` is not in any H set, `draft.py:42-98`); every ฿
figure `provisional=True`, `Decimal`-never-float, advisory-never-gating
(ADR-0030 D5; CLAUDE.md §8 assistive discipline).

**Honesty note — the ADR-0030 D1 framing vs code (the SD-E disclosure).**
ADR-0030 Alt-2 says "the reasoning trace is the one surface both paths already
share" (`docs/adr/0030-box4-economic-impact-facet.md:326-327`). In code that
OVERSTATES: there are two distinct trace shapes — (a) the reactive
`RecommendedAction.reasoning_trace: list[ReasoningStep]` (typed,
`actions.py:92`), and (b) the governed per-step
`StepOutcome.reasoning_trace: list[dict[str, Any]]` → JSONB telemetry
(`orchestrator.py:90`; `services/engine/procedures/runs.py:109`). The ONLY
typed `ReasoningStep` surface on the governed path is nested inside the
`RecommendedAction` envelope the action step composes
(`action_step.py:154-185`, trace at `:178`) and serializes into the step
artifact `output_set` (`:188-196`). So "both paths" = **two composition sites
over the SHARED RecommendedAction envelope**, not one shared trace; non-action
procedure steps carry only dict telemetry and get NO typed facet in v1. Per
CLAUDE.md §6 this is recorded as a **`was an error`-class imprecision** in the
just-Accepted ADR — recorded honestly, and it does **not** reverse the ADR's
decision: the advisory trace-carried ReasoningStep remains the correct
placement, because the envelope IS the shared surface wherever an action
exists. Handling of the record itself is SD-E.

## Acceptance Criteria

- [ ] **AC-1 (the typed models — ADR-0030 D3's "final field set is the
  build-PLAN's first AC").** `EconomicExposure` (`label: str`,
  `exposure_thb: Decimal`, `components: dict[str, Decimal] = {}`) and
  `EconomicImpact` (`provisional: bool`, `currency: str`, `kind: str`,
  `baseline: EconomicExposure`, `governed: EconomicExposure`,
  `net_benefit_thb: Decimal`, `assumptions: list[str]`,
  `basis_refs: list[str] = []`) land engine-side beside the envelope models in
  `services/engine/actions.py` (the PLAN-0044 `ControlRef`/`GovernedDecision`
  precedent — drafter finding v; module home is OQ-A for R2), with
  `model_config = ConfigDict(extra="forbid")` (mirroring `demo.py:20,35`), all
  money `Decimal` (never float — `ledger.py:4` invariant, ADR-0030 D0), a
  `model_validator` enforcing `net_benefit_thb == baseline.exposure_thb -
  governed.exposure_thb` (producer-proof arithmetic; a mismatch raises
  `ValidationError`, unit-tested), and a docstring stating these are a
  **trace-step `detail` payload, NOT part of the ADR-007 D2 contract** — plus
  the one-sentence clarifier on the `:11` "four models… verbatim" line,
  disclosed in the PR body as the only contract-module diff.
- [ ] **AC-2 (the never-raise shared emission helper).** New
  `services/engine/economic_impact.py` (OQ-A): a producer registry
  (`register_economic_producer(vertical, producer)` + a test-resettable clear,
  mirroring the ADR-0023 registry disciplines `discovery.py:10-21`) and
  `async def build_economic_steps(event, vertical) -> list[ReasoningStep]`
  returning `[]` when no producer is registered, when the producer returns
  `None`, **or when the producer raises** (warning logged, exception NEVER
  propagates — the IN-4-protection contract, drafter finding ii; the contract
  comment mirrors `recommender.py:226-228`); on success, exactly one
  `ReasoningStep(step_id="economic-impact-0", kind="economic_impact",
  summary=<one-line ฿ sentence naming net benefit + "provisional estimate">,
  detail=EconomicImpact(...).model_dump(mode="json"))`. Unit tests cover all
  four branches.
- [ ] **AC-3 (wiring — per ratified SD-A).** Under SD-A (a): reactive —
  `recommend()` awaits the helper after `augment_with_advisory_judge`
  (`recommender.py:230-232`) and passes `economic_steps` to
  `_compose_llm_record`, whose trace sum (`:176-178`) gains a final
  `+ economic_steps` term (APPENDED LAST); governed —
  `ActionStepExecutor.execute` awaits the helper per entity
  (`action_step.py:269-274`) and `_compose_action` appends it after
  `build_llm_reasoning_trace(...)` (`:178`). `_rule_recommend`
  (`recommender.py:252+`) is **byte-untouched** — the facet NEVER rides the
  deterministic fail-safe. The golden-trace positional call site
  (`test_eval_harness.py:97-99`) is updated with the new argument + its `:94-96`
  precedent comment extended (drafter finding iii). `build_llm_reasoning_trace`
  itself is untouched (finding i).
- [ ] **AC-4 (per-vertical producers — per ratified SD-B/SD-C).** Under
  SD-B (a) + SD-C (a): `verticals/<ns>/economic_impact.py` exposing
  `register_<ns>_economic_impact()` for all four verticals;
  `discovery._register_vertical` (`discovery.py:62-71`) gains the **guarded
  optional import** (missing module = skip silently; a broken transitive
  import still logs per the `:55-57` isolation — drafter finding vii).
  Procurement computes from its real CSV columns
  (`fastenal_csv.py:78` `downtime_cost_per_hour_thb`, `:107`
  `quoted_unit_price_thb`, `:86` `total_thb`), mirroring the ledger's
  baseline/governed skeleton (`ledger.py:39-95`) with `basis_refs` citing the
  columns; energy / supply_chain / aquaculture are **assumptions-first** —
  every non-column input is a named `assumptions` entry (ADR-0030 D3;
  `ledger.py:28-29` precedent), values per ratified SD-G, NO ontology edit /
  regen / migration. `kind` labels per the ADR-0030 D3 table verbatim:
  `avoided_outage` / `expedite_tradeoff` / `spoilage_avoided` /
  `mortality_avoided`.
- [ ] **AC-5 (the ADR-0030 D4-3 ≥ 3-vertical build-completion marker — THE
  enforcement AC).** Additive
  `tests/services/engine/test_economic_impact_coverage.py` in the
  `test_principal_identity_retrigger.py` style (docstring cites ADR-0030 D4-3
  **and this PLAN's AC-5** — the D4-4 lesson: an owned marker, in the same
  breath): for each shipped vertical, feed its registered producer that
  vertical's representative synthetic trigger event and assert **≥ 3 verticals**
  yield a step with `kind == "economic_impact"` whose `detail` validates as
  `EconomicImpact` (`model_validate` round-trip). Lands **RED**
  (`xfail(strict=True)`-guarded, the PLAN-0068 PR1 discipline) in PR1; flips
  **GREEN** (guard removed) in PR2. Deterministic-offline (assumption producers
  are pure; procurement reads the committed CSVs).
- [ ] **AC-6 (advisory invariants — ADR-0030 D5).** Tests assert:
  (a) `provisional is True` in every v1 producer output; (b) the facet never
  alters the action — composed `RecommendedAction` fields
  (title/description/confidence/suggested_handler/handler_payload/
  requires_approval/affected_entities) are IDENTICAL with and without an
  emitting producer registered, and the facet is strictly appended; (c) a
  **raising** producer leaves the action intact + facet absent + warning
  logged — and on the reactive path does NOT trip the IN-4 fail-safe (the
  record still carries `actor_kind == "llm"`, never the rule path's
  `"engine"` — drafter finding ii); (d) the deterministic fail-safe pins pass
  **UNMODIFIED**: `test_recommender.py:187` + `test_recommender_config.py:72`
  set-equality `== {"rule_check"}`.
- [ ] **AC-7 (append-only pins pass UNMODIFIED).** Index-0 reads:
  `test_aquaculture_vertical.py:84`, `test_recommender_config.py:148,169`,
  `tests/api/test_action_endpoints.py:135`. Helper pins:
  `tests/services/engine/llm/test_trace.py:56,66` (the facet never enters
  `build_llm_reasoning_trace` — finding i). Tolerant membership asserts
  (`test_recommender.py:147-149`, `test_eval_harness.py:105-107`) simply keep
  passing.
- [ ] **AC-8 (serialization + round-trip).** `detail` is
  `model_dump(mode="json")` → every `Decimal` a **string** (Pydantic-v2
  JSON mode; the shipped precedent
  `tests/api/test_demo_hero_routes.py:75` — `{"value": "288000",
  "currency": "THB"}`); `EconomicImpact.model_validate(step.detail)`
  round-trips equal; the envelope round-trip (`test_eval_harness.py:103`)
  passes; on the governed path the step artifact's
  `entry["action"]["reasoning_trace"]` (JSONB `output_set`,
  `action_step.py:188-196`) round-trips via `RecommendedAction.model_validate`
  with the facet step intact.
- [ ] **AC-9 (RED→GREEN behavioural flip).** Pre-committed read, run against
  the pre-build tree first: a composed action on the mocked LLM path (energy)
  carries **NO** `kind == "economic_impact"` step (RED for the post-build
  assertion); post-build it carries **exactly one**, with `net_benefit_thb`
  equal to the SD-G-ratified `baseline − governed` arithmetic. A green
  pre-build = a wrong fixture; stop and fix.
- [ ] **AC-10 (hygiene + zero-collateral pins).** Full suite green WITH
  Postgres up (one pytest per checkout); `ruff check` + `ruff format --check`
  clean; `mypy --strict services/` clean; CI `gate` green per PR; full suite
  re-run on each merge commit (CI is PR-only). **Byte-identical:** every
  `procedures.yaml`, every ontology YAML, `generated/**`, `alembic/versions/`,
  the H governance sets (`draft.py:42-98` — `reasoning_trace` is not
  H-governed), `services/api/models/demo.py` + `hero_demo/ledger.py` +
  `/demo/hero/` routes (ADR-0030 D2 coexistence). **No MS-S1 / no host-state
  anywhere** — LLM-path tests ride the mocked `ChatClient`; the offline oracle
  is the gate (CLAUDE.md §8).

## Out of Scope

- ❌ **Ontology cost-carrier properties for the 3 non-procurement verticals**
  (v2 under SD-B (a); ADR-0030 OQ-1) — including any energy Alembic migration /
  ORM / schema-parity work (energy is the only vertical with a committed ORM;
  its ฿ property, if ever, is its own PLAN).
- ❌ **Retiring / generalizing `HeroImpactLedger`** — ADR-0030 D2 = coexist;
  `demo.py` + `ledger.py` + `view-hero.js` byte-identical (the ledger remains
  the demo-path computation; the facet is the production-path dimension).
- ❌ **A first-class envelope field** — ADR-0030 D1/OQ-3: reopens only when a
  real ROI-dashboard consumer exists; the ADR-007 D2 contract stays verbatim.
- ❌ **Multi-currency** — ADR-0030 OQ-4: THB-only; `currency` carried as an ISO
  field, no normalization.
- ❌ **A typed facet on non-action procedure steps** / typed-ifying the
  `StepResult.reasoning_trace` JSONB telemetry (`orchestrator.py:90`,
  `runs.py:109`) — the F2 code reality; a v2 conversation if a non-action ฿
  surface ever matters.
- ❌ **Any operator-UI render of the ฿ step** — a future render inherits the
  s74 trust-shape rule (ADR-0030 D5); nothing UI-facing ships here.
- ❌ **Editing ADR-0030** (per SD-E (a)) and the optional ADR-016 pointer
  annotation (ADR-0030 D7 nicety — G1-gated, not required).
- ❌ **ROI aggregation / SQL-side queryability** — the priced D1 deferral
  stands (filter trace steps by kind at pilot scale).
- ❌ Emitting the facet on `_rule_recommend` — the deterministic fail-safe
  stays facet-free by design (AC-6d), not as a TODO.

## Steps

### Step 1: Plan-first read of the result-producing code

Re-read on the executing branch: `recommender.py:148-186` (compose),
`:189-250` (the IN-4 try + judge never-raise comment `:226-228`), `:252+`
(`_rule_recommend` — untouched); `action_step.py:154-196` (compose + artifact
entry), `:253-278` (the async caller); `actions.py` (full);
`action_verification.py:110-132` (the `_verification_step` producer the
emission mirrors); `discovery.py:37-71`; `ledger.py` + `demo.py:17-57`;
`draft.py:42-98`; the AC-6/AC-7 pinned tests; `test_eval_harness.py:84-109`.
**Pass/fail read (pre-committed):** every citation in this PLAN matches
on-disk code — drift = stop, reconcile line numbers here before editing.

### Step 2 (PR1): The typed models (AC-1)

Add `EconomicExposure` + `EconomicImpact` per AC-1 (home per OQ-A), the
arithmetic `model_validator`, the not-the-D2-contract docstring, and the `:11`
clarifier line. Unit tests: field set, `extra="forbid"` rejection, Decimal
round-trip, validator rejects a mismatched `net_benefit_thb`. **Pass/fail
read:** `mypy --strict services/` clean; the validator test proves a bad
producer cannot construct an inconsistent figure.

### Step 3 (PR1): The never-raise emission helper (AC-2)

New `services/engine/economic_impact.py`: registry + `build_economic_steps`
with the four-branch contract (no producer / `None` / raise / success) and the
IN-4-protection comment. Unit tests per AC-2. **Pass/fail read:** all four
branches covered; the raise branch asserts the logged warning AND `[]` (never
a propagated exception).

### Step 4 (PR1): Wiring + the RED marker (AC-3, AC-5-RED, AC-6, AC-9-RED)

Thread `economic_steps` through both SD-A sites exactly as
`verification_steps` threads today (computed in the async caller, passed as a
param, appended LAST); update the golden-trace positional call
(`test_eval_harness.py:97-99` + comment); land the AC-6 with/without-producer
invariance tests + the raising-producer IN-4 test; record the AC-9 RED run
(no `economic_impact` step pre-producers); land the AC-5 marker
`xfail(strict=True)`-guarded. `_rule_recommend` untouched; the AC-7 pins run
UNMODIFIED. **Pass/fail read:** full suite green with the marker xfailing
strictly — mechanical proof the D4-3 assertion is RED before any producer
exists (the erosion class ADR-0030 D4 records cannot recur unnoticed).

### Step 5 (PR2): Four per-vertical producers (AC-4)

`verticals/<ns>/economic_impact.py` × 4 per AC-4 + the guarded discovery
import. Procurement: async adapter fetches mirroring `ledger.py:47-67`
(baseline = on-AVL preferred lead; governed = the event's emergency path),
`basis_refs` = the CSV columns, the single `productive_hours_per_day`
assumption; anchor resolution per OQ-C (unresolvable anchor → `None`, never a
guess). Energy / supply_chain / aquaculture: pure functions over the trigger
event + the SD-G constants, every constant a named `assumptions` entry,
`provisional=True`, `kind` per the D3 table. Per-producer unit tests: detail
validates as `EconomicImpact`; assumptions non-empty (assumption-based) /
basis_refs cite columns (procurement); the arithmetic validator holds.
**Pass/fail read:** each producer's unit test green; zero diffs under
`verticals/*/ontology/`, `generated/**`, `alembic/`.

### Step 6 (PR2): GREEN flips + coupled-test audit (AC-5, AC-9, AC-7)

Remove the AC-5 xfail guard (marker GREEN at N=4 under SD-C (a)); flip AC-9
GREEN with the SD-G arithmetic. Then the audit — every hit classified
touched / pinned-unmodified in the PR body, never silent (the 0067/0068/0070
discipline): grep sweep (via the Grep tool) for `economic_impact`,
`_compose_llm_record(`, `_compose_action(`, `step.kind for`,
`reasoning_trace\[0\]`, `== \{"rule_check"\}` across `tests/**` +
`services/**`; expected-UNMODIFIED pins verified green untouched:
`test_recommender.py:187`, `test_recommender_config.py:72,148,169`,
`test_aquaculture_vertical.py:84`, `test_action_endpoints.py:135`,
`test_trace.py:56,66`, `test_action_step.py:116,133` (the OTHER trace —
finding iv), golden traces (invariant-style, not byte-pinned —
`test_eval_harness.py:19-20`). **Pass/fail read:** marker + behavioural flip
GREEN; every audited module classified in the PR body; `git diff main --
services/api/models/demo.py verticals/procurement/hero_demo/` empty.

### Step 7: PR flow + hygiene + close (AC-10)

Per ratified SD-D. If (a) TWO PRs: PR1 = Steps 2–4
(`feat/plan0071-economic-facet-core`), PR2 = Steps 5–6
(`feat/plan0071-economic-producers`), PR2 rebased on PR1's merge; if Cray
diverges to (b) ONE PR, Steps 2–6 land together with the RED evidence
(AC-5 xfail + AC-9 pre-build run) recorded in the PR body before the flip
commits. Each PR: start `vero-postgres` (Docker Desktop, Windows engine); full
suite via WSL (one pytest per checkout); `ruff check .` + `ruff format
--check .` + `mypy --strict services/`; body via `--body-file` built with the
Write tool; cite ADR-0030 + this PLAN; CI `gate` green; fresh Cray sign-off
per merge; full-suite re-run on the merge commit. After close:
`git mv docs/plans/0071-*.md docs/plans/done/`. **Pass/fail read:** suite
green with DB up (~123 skips = DB down — restart and rerun); linters clean;
CI `gate` green; merge-commit re-run green.

## Surfaced decisions (SD-A … SD-G — ALL ratified as-recommended by Cray, session 126)

**Ratified 2026-07-13 (session 126, via AskUserQuestion):** Cray ratified all
seven SDs as-recommended — SD-B assumptions-first, SD-G the proposed
plausibility-grade ฿ constants, and SD-A/SD-C/SD-D/SD-E/SD-F as drafted. The
recommendations below are now the accepted build decisions; the "Recommend"
framing is retained as the ratification lineage, not open items.

Leans below originate from the Code dispatch (marked there as Code's grounded
inferences) except SD-G (drafter-added); the drafter re-verified each against
code and CONCURS with all six dispatch leans.

- **SD-A — path scope: which composition sites emit?** *Recommend: (a) BOTH*
  — reactive `_compose_llm_record` (`recommender.py:176-178`) + governed
  `_compose_action` (`action_step.py:178`) via the ONE shared helper. The F2
  reality reframes this decision honestly: "both paths" = two edit sites over
  the SHARED `RecommendedAction` envelope, and the threading mechanism is
  identical at both (drafter finding vi). The demo ฿-story spans both surfaces
  — the governed hero beat IS an action step; (b) recommend-only v1 halves the
  wiring but leaves the governed procedure surface (the demo centerpiece)
  ฿-blind, and the governed site would be the FIRST appended advisory step
  there (finding iv) — a small novelty cost (a) pays once, now. *Why Cray's
  call:* demo-visible scope + it operationalizes the ADR's cross-surface
  promise.
- **SD-B — per-vertical ฿ sourcing (THE central fork).** *Recommend: (a)
  ASSUMPTIONS-FIRST v1* — procurement uses its real CSV columns
  (`fastenal_csv.py:78,86,107`); energy / supply_chain / aquaculture source
  every ฿ input from named `assumptions` entries (ADR-0030 D3 requires exactly
  this disclosure), NO new ontology properties, NO regen, NO migration.
  Grounds: the ฿/cost grep across `verticals/` hits ONLY procurement files
  (verified 2026-07-13); an energy cost property is the one with committed
  ORM + Alembic + schema-parity weight; real cost-carrier properties are a
  clean v2 once a pilot supplies real figures. (b) add real properties to the
  3 verticals now = four ontology edits + regen + one migration for numbers
  that would still be invented. *Why Cray's call:* it fixes what the permanent
  record's v1 ฿ figures ARE (modelled estimates vs data-derived) — a
  positioning statement, not an engineering detail.
- **SD-C — v1 vertical scope.** *Recommend: (a) ALL 4* (procurement real + 3
  assumptions-based) — closes the economic Rule-of-Three symmetrically, clears
  the D4-3 floor with margin, and the marginal cost per assumption-based
  producer is a constants table + arithmetic + one unit test. (b) exactly 3
  (the floor); (c) procurement + 2. *Why Cray's call:* scope/effort on demo
  breadth — his own precedent line (the PLAN-0070 "demo-breadth, not
  moat-critical" honesty note).
- **SD-D — PR structure.** *Recommend: (a) TWO PRs* — PR1 engine core
  (models + helper + wiring + RED marker), PR2 producers + GREEN flips. The
  surface area is real: a contract-adjacent module edit, a new engine module,
  two wiring sites, a discovery seam, four vertical modules, a marker, and a
  coupled-test audit — engine-vs-producers rollback isolation pays. **Honest
  precedent note:** Cray typed 2 PRs on both engine-touching FK-band builds
  (0067 SD-1, 0068 SD-4) and 1 PR only on the zero-engine-change 0070; this
  build DOES touch `services/engine/` → (a) matches his own line. *Why Cray's
  call:* PR granularity is Cray's established prerogative.
- **SD-E — recording the ADR-0030 D1/Alt-2 imprecision (F2).** *Recommend:
  (a) disclose in THIS PLAN and do NOT edit the Accepted ADR* — the Goal's
  honesty note is the durable record ("two sites over the shared envelope";
  `was an error`-class imprecision per CLAUDE.md §6 that does NOT reverse the
  decision); a G1-gated Accepted-ADR erratum for a framing sentence with an
  unchanged conclusion is disproportionate process for zero design delta.
  (b) also file an ADR-0030 erratum edit (G1-gated, Cowork-drafted). *Why
  Cray's call:* it decides what the permanent governance record says about a
  just-Accepted ADR — reversal-cost judgment, not code.
- **SD-F — computation locus (ADR-0030 OQ-2).** *Recommend: (a) per-vertical
  producer computing the engine-owned type* — mirrors `ledger.py:39`
  (vertical-side computation), matches the ADR's OQ-2 lean; the vertical owns
  its domain arithmetic + assumptions, the engine owns the shape + the
  never-raise emission discipline. (b) an engine-generic calculator fed
  vertical params — pushes four genuinely different exposure arithmetics
  (outage-hours vs lead-time-downtime vs spoilage-fraction vs
  mortality-fraction) into engine config. *Why Cray's call:* it ratifies the
  ADR's OQ-2 lean into build reality — an ADR-follow-through call.
- **SD-G — the v1 assumption VALUES (drafter-added; the 0070 SD-2 precedent:
  demo-visible domain ฿ numbers are Cray's permanent-record bar).**
  *Recommend the following plausibility-grade v1 constants — explicitly
  drafter-INVENTED placeholders, Cray edits freely; whatever lands must
  satisfy the AC-1 arithmetic validator and appear verbatim in
  `assumptions`:*
  - **energy `avoided_outage`:** feeder-overload outage cost ฿120,000/hr;
    unmitigated duration 4 h vs governed intervention 0.5 h + ฿15,000
    crew/switching → baseline ฿480,000 vs governed ฿75,000 →
    `net_benefit_thb` ฿405,000.
  - **supply_chain `spoilage_avoided`:** pharma cold-chain cargo value
    ฿2,400,000; unmitigated excursion = 100% loss vs governed
    re-route/re-ice = 10% loss + ฿40,000 intervention → baseline ฿2,400,000
    vs governed ฿280,000 → net ฿2,120,000.
  - **aquaculture `mortality_avoided`:** pond biomass value ฿850,000
    (tiger-prawn pond near harvest, the s123 narrative); unmitigated low-DO
    mortality 35% vs governed aeration 5% + ฿8,000 energy/ops → baseline
    ฿297,500 vs governed ฿50,500 → net ฿247,000.
  - **procurement:** NO invented constants — real columns + the ledger's own
    single disclosed assumption (`productive_hours_per_day = 8`,
    `ledger.py:28-29`).
  *Why Cray's call:* these numbers become the repeatable cross-vertical ฿
  sentences the ADR's Consequences promise — permanent-record,
  customer-visible figures.

## Open questions (R2-level engineering calls — NOT Cray SDs)

- **OQ-A (module home split).** Drafted: models in `actions.py` (the dispatch
  F4 position + the PLAN-0044 in-module precedent, finding v); helper +
  registry in new `services/engine/economic_impact.py` (mirrors
  `action_verification.py` owning its step producer). R2 may instead co-locate
  the models in the new module (keeps `actions.py` byte-pristine); either
  satisfies "engine-owned" — settle at R2, not ratification.
- **OQ-B (reactive emission point vs the IN-4 try).** Drafted: inside
  `recommend()`'s try, after the judge, protected by the helper's never-raise
  contract (the judge's exact pattern, `recommender.py:226-232`). R2 verifies
  the contract comment lands adjacent to the call and AC-6(c) proves it.
- **OQ-C (procurement anchor resolution).** Whether the trigger event's
  asset/PO anchor resolves deterministically to the ledger-style
  baseline/governed pair at emission time (the events carry criticality, not
  ฿ — finding vi). Contract: unresolvable → producer returns `None` (facet
  absent), never a guessed figure. Verify at build; if resolution proves
  gnarly, procurement MAY fall back to assumption-based v1 with `basis_refs`
  citing the CSV columns as provenance — disclose in the PR body if taken.

## Verification

AC-1/AC-2 by unit tests (Steps 2–3: validator rejection, four helper
branches); AC-3 + AC-6 + AC-7 by the Step-4 invariance/raising/pin suite run
against both sites; AC-5 by the xfail-strict RED in PR1 → guard-removed GREEN
in PR2 (Steps 4/6); AC-9 by the pre-committed RED run against the pre-build
tree then the GREEN flip (Steps 4/6); AC-4 by per-producer unit tests + the
zero-ontology/regen/migration diff check (Step 5); AC-8 by the round-trip
asserts (Steps 4–6); AC-10 by the Step-7 full-suite + linters + CI `gate` +
merge-commit re-run. Evidence = fresh pytest/linter output on the branch;
pass/fail reads pre-committed per step (Lesson #0026). **No MS-S1 / no
host-state — deterministic offline throughout; Postgres (Docker Desktop) only
for the full-suite runs.**

## References

- `docs/adr/0030-box4-economic-impact-facet.md` — the Accepted contract: D1
  placement (`:121-142`), D3 shape sketch + kind table (`:158-198`), D4-3 the
  build-completion AC mandate (`:214-218`), D5 advisory (`:223-232`), D6 this
  PLAN's charter (`:234-242`), OQ-1/OQ-2 (`:379-392`), Alt-2's "one surface
  both paths share" (`:318-327` — the SD-E imprecision).
- `services/engine/recommender.py:148-186` (`_compose_llm_record`; the trace
  sum `:176-178`), `:189-250` (`recommend()`; the IN-4 try; the judge
  never-raise comment `:226-228`), `:252+` (`_rule_recommend` — untouched).
- `services/engine/procedures/action_step.py:154-185` (`_compose_action`;
  trace `:178`), `:188-196` (the JSONB artifact entry + round-trip contract),
  `:253-278` (the async caller; `:274` the compose call).
- `services/engine/actions.py:11` (the "verbatim" line gaining one
  clarifier), `:20-24` (`ReasoningStep` — `detail: dict[str, Any] | None`),
  `:33-66` (`ControlRef`/`GovernedDecision` — the PLAN-0044 in-module
  precedent), `:84-106` (`RecommendedAction`; `reasoning_trace` `:92`).
- `services/engine/action_verification.py:110-132` (`_verification_step` —
  the advisory step-producer model), `:23-24` (never-overrides constraint).
- `services/engine/discovery.py:37-71` (import-scan; `:53-57` per-vertical
  failure isolation; `:62-71` the entry-function convention the guarded
  optional import extends).
- `verticals/procurement/hero_demo/ledger.py:4` (Decimal invariant), `:28-29`
  (the disclosed-assumption precedent), `:39-95` (the baseline/governed
  computation skeleton); `verticals/procurement/data_adapter/fastenal_csv.py:78,86,107`
  (the real ฿ columns); `verticals/procurement/data_adapter/synthetic.py:125-170`
  (criticality events — no ฿ on events); `services/api/models/demo.py:17-57`
  (`ImpactSide`/`HeroImpactLedger` — the D3 prototype, untouched).
- `services/engine/procedures/orchestrator.py:81-91` (`StepOutcome` — the
  dict telemetry trace) + `services/engine/procedures/runs.py:109` (JSONB) —
  the F2 governed-path reality.
- `services/engine/procedures/draft.py:42-98` — the H governance sets
  (`reasoning_trace` absent = zero draft-governance impact).
- Pinned tests: `tests/services/engine/test_recommender.py:147-149,187`;
  `tests/services/engine/test_recommender_config.py:72,148,169`;
  `tests/services/engine/test_aquaculture_vertical.py:84`;
  `tests/api/test_action_endpoints.py:130-137`;
  `tests/services/engine/llm/test_trace.py:56,66`;
  `tests/services/engine/eval/test_eval_harness.py:19-20,84-109` (`:97-99`
  the positional call that ripples; `:103` the envelope round-trip);
  `tests/services/engine/procedures/test_action_step.py:114-116,133` (the
  OTHER trace); `tests/api/test_demo_hero_routes.py:75` (Decimal→str).
- `tests/services/engine/procedures/test_principal_identity_retrigger.py` —
  the owned-marker style AC-5 copies (ADR-0026 OQ-6 / PLAN-0044 AC-10).
- `docs/plans/done/0070-energy-overcurrent-band.md` — the build-shape
  precedent mirrored here (plan-first read, RED-verify, coupled audit
  classified in the PR body, SD ratification via AskUserQuestion, the SD-G
  demo-visible-numbers bar).

---

## Author≠reviewer disclosure (ADR-012 D4.3)

This draft was authored by the in-harness `plan-drafter` subagent under
ADR-013 D1 phased authority. The outline originator was the main Code agent
(session-126 dispatch: verified fact-pack F1–F5 + SD-A…SD-F leans, explicitly
marked as Code's inferences, not Cray decisions; SD-G is drafter-added). The
independent reviewer is the main Code agent (R2 — re-verify every citation,
commit via PR per ADR-009 D2), with Cray ratifying every SURFACED decision
(SD-A…SD-G) before Status moves to Ready. Separation: INTACT — drafter
(plan-drafter) ≠ reviewer (Code R2) ≠ ratifier (Cray).
