# PLAN-0060: Reactive judgment handler catalog — per-handler descriptions in the recommender prompt

**Status:** Ready — SD-1…SD-5 ratified as-recommended by Cray (session 114, AskUserQuestion)
**Owner:** both (Claude Code executes; Cray ratified the surfaced decisions and gates the Step-7 live re-validate)
**Created:** 2026-07-08
**Related ADRs:** none new — this is a **build PLAN** (see the ADR-tripwire note below). Cites
ADR-010 (prompt-injection containment posture — unchanged), ADR-016 D5 (trusted-config `goal`
threading — the direct precedent for trusted catalog placement), ADR-0029 (event-trigger bridge —
the demo premise this unblocks).
**Related PLANs:** PLAN-0006 (LLM reasoning hook — the two-call exchange being extended),
PLAN-0056/PLAN-0057 (`docs/plans/done/` — the event bridge + hero opener whose live premise the
session-114 smoke found blocked), PLAN-0020 (reasoning modes — `skip` interaction noted in Step 4).
**Motivating evidence (on disk):**
[`docs/logs/2026-07-08-event-bridge-recommender-live-smoke.md`](../logs/2026-07-08-event-bridge-recommender-live-smoke.md)
— session 114 live smoke: the real MS-S1 recommender (`gpt-oss:20b`) engaged cleanly
(`actor_kind == "llm"`, confidence 1.0, entity resolved) but chose `suggested_handler ==
"reorder"` instead of `emergency_source` for an explicit line-down / spare-exhausted / "normal
reorder lead time is unacceptable" event.

> **Authorship disclosure (ADR-012 D4.3):** drafted by the in-harness `plan-drafter` subagent
> (ADR-013 D1 phased authority); outline originated by Code (session 114 finding, deferred per
> Cray); independent review = Code R2 (every citation) at PR merge. **SD-1…SD-5 are RATIFIED
> as-recommended by Cray (session 114, via AskUserQuestion).** Separation: INTACT.

> **This is a build PLAN — no new ADR.** Rationale: the prompt-injection containment posture
> (ADR-010 D4/IN-2) is unchanged — handler descriptions are **authored vertical config**, the
> same trust class as the ADR-016 D5 `goal` already threaded into the trusted system instruction
> (`services/engine/llm/prompt.py:49-63` documents exactly this trusted-config carve-out); the
> registry extension is additive and optional; "governed ≠ generated" (L-3) is untouched.
> **Tripwire — STOP and surface for an ADR if execution finds any of:** (i) the catalog would
> require operator-derived / dynamic text inside the trusted instruction (breaks the ADR-010
> containment model), (ii) the `LlmJudgment` schema shape must change (PLAN-0006 SC-1 contract),
> or (iii) descriptions must be sourced from governed procedure config at runtime (couples the
> reactive path to ADR-016 procedure semantics). Do not bake any of these in.

## Goal

Surface **per-handler descriptions** (an "Available actions" catalog) to the model in the
**reactive** recommender judgment prompt, so it can semantically distinguish registered handlers
— e.g. `emergency_source` = critical failure / line-down / urgent off-cycle sourcing, vs
`reorder` = routine calm-path restock — instead of guessing from bare names. Today the reactive
path shows the model **names only**: registration stores `name → Handler` with no description
slot (`services/engine/registry.py:37-43`, `:64-69`), the enum handed to Ollama `format` is
`list(handler_names)` (`services/engine/llm/structured.py:111-125`, applied at `:188`), the
judgment prompt never lists handlers or gives when-to-pick guidance
(`services/engine/llm/prompt.py:101-121`, `:124-173`), and the reactive path threads no `goal`
(`services/engine/recommender.py:205-207` passes none → `goal=None`). The distinguishing prose
exists **only** on the governed path (`verticals/procurement/procedures.yaml:93-103` goal,
`:139-143` source step, `:337-340` reorder step) and never reaches `generate_judgment`. Fixing
this unblocks the event-bridge demo premise: the bridge fires the governed
`event_emergency_sourcing_round` run **only** when the recommendation's `suggested_handler` is
the mapped event kind (`services/api/routers/actions.py:131`, `:143` — `event_kind =
action.suggested_handler`). A controlled live re-validate (evidence-only, Cray-gated) then
confirms the model picks `emergency_source` for the same event that produced the finding.

## Acceptance Criteria

- [ ] **AC-1 — registry captures descriptions (optional, additive).** `register_handler` accepts
      an optional per-handler `description` (keyword, default `None`); a new sorted
      `handler_catalog(vertical)` accessor returns `(name, description | None)` pairs alongside
      the existing `handler_names` (`services/engine/registry.py:112-122`). Every existing
      call site compiles and behaves unchanged without passing a description; duplicate-name
      registration still raises `RegistryError`; `reset()` clears descriptions. *(Shape per SD-1.)*
- [ ] **AC-2 — every handler-registering vertical declares descriptions.** All **four** verticals
      with a `handlers.py` (`procurement`, `energy`, `supply_chain`, `aquaculture` — `vet_clinic`
      registers no handlers; confirmed by glob, see Out of Scope) register a 1–2-line description
      for `echo` + every `ACTION_TYPES` entry. A per-vertical test asserts description keys ==
      registered handler names (no orphan, no gap). The procurement `emergency_source` vs
      `reorder` pair explicitly encodes urgent-critical-failure vs routine-restock. *(Scope per
      SD-3.)*
- [ ] **AC-3 — catalog renders in the judgment prompt (flag-on).** With the flag on, the trusted
      system instruction carries an "Available actions" block — one line per handler,
      `name — description` (name-only when description is `None`) — and, via the
      `build_structuring_messages` composition (`services/engine/llm/prompt.py:146` builds on
      `build_reasoning_messages`), the catalog reaches **both** call 1 and call 2 (and the
      PLAN-0020 `skip` single-call path) from a single render site. *(Placement per SD-2.)*
- [ ] **AC-4 — flag-off is byte-identical to today (default).** With the flag off (default),
      every prompt builder's output is byte-identical to the pre-change output — asserted the
      same way the `goal` precedent is
      (`tests/services/engine/llm/test_prompt.py:48` `test_goal_none_is_byte_identical_to_no_goal`),
      plus a pinned-literal check that the flag-off system instruction contains no
      "Available actions" marker. *(Flag per SD-4.)*
- [ ] **AC-5 — existing constraints unchanged.** The `suggested_handler` enum constraint
      (`structured.py:111-125`) still restricts generation to registered names; the semantic
      resolve-check backstop (`structured.py:257-263`) is untouched; the ADR-010 containment
      invariants (untrusted block markers, delimiter neutralisation —
      `services/engine/llm/prompt.py:27-46`) still pass their existing tests.
- [ ] **AC-6 — offline gate green.** Full offline suite + ruff + mypy green under the required CI
      `gate` on a fresh PR (no regression in `tests/services/engine/llm/test_prompt.py`,
      `test_structured.py`, `tests/services/engine/test_registry.py`,
      `test_recommender.py`, `test_recommender_config.py`, or any vertical suite).
- [ ] **AC-7 — controlled live re-validate (evidence-only, NOT a merge gate).** Post-merge,
      Cray-gated per CLAUDE.md §8: ONE live run against MS-S1 `gpt-oss:20b`, flag on, same event
      shape as the session-114 smoke, with the pass/fail read pre-committed **before** the run
      (`suggested_handler == "emergency_source"` AND `actor_kind == "llm"`); result recorded in a
      `docs/logs/` note either way. A miss is a **finding** (flag stays off; next move is a new
      Cray decision), never a gate failure. *(Split per SD-5.)*

## Out of Scope

- ❌ **The governed procedure path.** There the handler is author-pinned
  (`verticals/procurement/procedures.yaml:146` `handler: emergency_source`) and "the LLM never
  selects it" (governed ≠ generated, `verticals/procurement/handlers.py:14-16`). This PLAN
  touches ONLY the reactive/free-choice judgment path; procedure-step prompts, gates, and
  executors are untouched.
- ❌ **Re-litigating handler semantics or vocabulary.** Handler names, each vertical's
  `ACTION_TYPES` (the ontology `RecommendedAction.action_type` enum), and the no-op stub
  implementations all stay exactly as shipped — this PLAN adds *descriptions of* the existing
  vocabulary, it does not change it.
- ❌ **Treating the live run as a merge gate.** The offline suite is the binding bar
  (CLAUDE.md §8: "the offline oracle is the gate"); AC-7 is confirming evidence only, run once,
  never re-fired to fish for the wanted answer (contamination anti-pattern — smoke log §Harness).
- ❌ `vet_clinic` — it registers no handlers (no `verticals/vet_clinic/handlers.py` exists;
  Phase 2 parked per ADR-005), so there is nothing to describe.
- ❌ The deterministic rule fallback (`services/engine/recommender.py` `_rule_recommend`), the
  event bridge itself (`services/engine/procedures/event_bridge.py`), entity resolution, and the
  shipped hero demo (which uses the deterministic advisory stub — smoke log §Significance).
- ❌ Model or backend changes — `RECOMMENDER_MODEL=gpt-oss:20b` stays pinned; no prompt-model
  A/B (the PLAN-0051 null result stands: don't re-propose without a model change).

## Surfaced Decisions

All five surfaced decisions were **RATIFIED as-recommended by Cray (session 114, via
AskUserQuestion — PLAN-0058/0059 pattern)**. The recommendation + rationale text is retained
below with the ratified outcome stamped per entry; the ACs/Steps above are the settled shape.

- **SD-1 — where handler descriptions live / are captured.** ✅ **RATIFIED (as-recommended).**
  *Recommendation:* **(a)** extend the registry — `register_handler(vertical, name, handler,
  description: str | None = None)` and a `handler_catalog(vertical)` accessor next to
  `handler_names` (`registry.py:64-69`, `:112-122`); each vertical's `handlers.py` declares an
  `ACTION_DESCRIPTIONS: dict[str, str]` beside its existing `ACTION_TYPES` tuple and passes them
  at registration.
  *Rationale (1-line):* the registry is already the single place that defines the model's
  selection universe (it feeds the enum via `handler_names`) — keeping name + meaning in one
  registration keeps them incapable of drifting apart.
  *Alternatives:* **(b)** a static per-vertical description map consumed only by the prompt
  builder — no registry change, but creates a second registration surface that can silently
  drift (a handler with no map entry, or a map entry for an unregistered handler);
  **(c)** derive from `procedures.yaml` step descriptions — rejected: couples the reactive path
  to governed config (the source-step prose describes scored-rule supplier selection, meaningless
  reactively — `procedures.yaml:139-143`), and coverage is partial (`escalate`/`echo` appear in
  no procedure step).
  *Why Cray:* this fixes where a cross-vertical authoring surface lives — every future vertical
  author inherits the choice.

- **SD-2 — where the catalog renders in the prompt.** ✅ **RATIFIED (as-recommended).**
  *Recommendation:* render an "Available actions" block (one `name — description` line per
  handler) inside the **trusted system instruction** (`build_system_instruction`,
  `prompt.py:49-87`), threaded as a new optional parameter through both message builders and
  populated in `generate_judgment` beside the existing `registry.handler_names(vertical)` fetch
  (`structured.py:188`). Because `build_structuring_messages` composes on top of
  `build_reasoning_messages` (`prompt.py:146`), one render site reaches **both** calls — call 1,
  where the free-form action choice is actually made ("Name the recommended action by its
  imperative verb", `prompt.py:113-115`), and call 2, where the choice is snapped to the enum
  (`structured.py:208-212`) — and also the PLAN-0020 `skip` single-call path.
  *Rationale (1-line):* handler descriptions are authored config, the exact trust class the
  system instruction already carries for the ADR-016 D5 `goal` (`prompt.py:55-63`, `:81-86`) —
  same placement, same containment argument, both calls covered by construction.
  *Alternatives:* the call-1 user turn (also shared via `:146`, but mixes trusted guidance into
  the turn that carries the untrusted event block); call-2 only (too late — the semantic choice
  is made in call 1's draft); both calls independently (redundant given `:146`).
  *Why Cray:* this sets the LLM prompt contract for every vertical's reactive judgment — the
  same class of change ADR-016 D5 handled for the governed path.

- **SD-3 — scope / blast radius.** ✅ **RATIFIED (as-recommended).**
  *Recommendation:* **all four** handler-registering verticals (`procurement`, `energy`,
  `supply_chain`, `aquaculture`) get descriptions in this PLAN — ~20 short authored strings
  total (6, 5, 6, 5 handlers respectively incl. `echo`).
  *Rationale (1-line):* the failure class is cross-vertical by construction (every vertical
  selects from bare names today — smoke log §Significance), the mechanism is shared code either
  way, and descriptions are optional-by-type so partial coverage degrades gracefully to
  name-only lines.
  *Alternative:* procurement-first (smallest reviewable diff; but leaves three verticals on the
  known-bad prompt shape and forces a second near-identical PR).
  *Blast radius to name explicitly:* with the flag ON, **every vertical's reactive
  recommendation input changes** — mitigated by SD-4 (flag-off default = byte-identical) and the
  AC-6 offline bar; the governed path is untouched in all verticals.
  *Why Cray:* cross-vertical demo surfaces are Cray's call (which verticals' behavior may shift,
  and when).

- **SD-4 — ship-dark flag.** ✅ **RATIFIED (as-recommended).**
  *Recommendation:* **yes** — gate the catalog behind a default-off Settings flag (e.g.
  `handler_catalog_enabled: bool = False` in `services/api/config.py`), mirroring the repo's
  established pattern for recommender-semantics changes: `verification_judge_enabled`
  (`config.py:129-141`) and `event_bridge_enabled` (`config.py:142-152`). `recommend()` already
  reads `settings` (`recommender.py:205-207` uses `settings.llm_retry_budget`), so threading is
  one argument. Flag-off must be **byte-identical** to today (AC-4). Flip the default only after
  the AC-7 live re-validate, as its own one-line PR (the PLAN-0056 SD-P3 ship-dark precedent).
  *Rationale (1-line):* this changes the semantics-bearing input of every vertical's reactive
  recommender — exactly the change class the repo ships dark, and the flag costs one config
  field.
  *Alternative:* no flag (simpler; defensible since prompt text is "just words") — rejected
  because the live evidence for the new prompt does not exist until AC-7 runs, and default-on
  would change all four verticals' live behavior on merge, unvalidated.
  *Why Cray:* default-on/off decides what a demo audience sees before evidence exists.

- **SD-5 — verification split: offline binding bar vs live confirming evidence.** ✅ **RATIFIED
  (as-recommended).**
  *Recommendation:* the split codified in AC-1…AC-6 (offline, binding, merge-gating) vs AC-7
  (live, evidence-only, Cray-gated per CLAUDE.md §8). Offline: registry catalog tests
  (`tests/services/engine/test_registry.py`), prompt render + byte-parity tests
  (`tests/services/engine/llm/test_prompt.py`, mirroring the `:48` goal-parity pattern), enum +
  threading tests (`tests/services/engine/llm/test_structured.py`), flag-default tests
  (`tests/services/engine/test_recommender_config.py`, `test_recommender.py`), per-vertical
  key-coverage tests. Live: ONE controlled run reusing the session-114 smoke's event shape
  (same line-down / spare-exhausted phrasing — deliberately the **same** input so the prompt
  change is the only moved variable; the recommender model never reads this repo, so the
  committed phrasing poses no trigger-contamination risk to *this* model), pass/fail
  pre-committed before firing, result logged win-or-lose, never re-fired.
  *Rationale (1-line):* this is the CLAUDE.md §8 posture verbatim — the offline oracle is the
  gate, a live run is evidence — applied to the exact finding that motivated the PLAN.
  *Alternative:* add a live smoke to CI — rejected outright (host-state, non-deterministic,
  violates §8 minimize-live-runs).
  *Why Cray:* the live run is a host-state action on MS-S1 — explicitly Cray-gated by
  CLAUDE.md §8 regardless of what this PLAN says.

## Steps

### Step 1: Registry — optional description + `handler_catalog` (per SD-1)
Extend `register_handler` (`services/engine/registry.py:64-69`) with keyword-only
`description: str | None = None`; store descriptions in `_VerticalEntry` (`:37-43`) **without**
changing the `handlers: dict[str, Handler]` shape (e.g. a sibling `descriptions: dict[str, str]`
field) so `get_handler` (`:78-83`) is untouched. Add `handler_catalog(vertical) ->
list[tuple[str, str | None]]` beside `handler_names` (`:112-122`), sorted, empty-safe for
unknown verticals; `reset()` (`:134-136`) clears it. Tests in
`tests/services/engine/test_registry.py`: with/without description, sort order, duplicate still
raises, reset clears, unknown vertical → empty.

### Step 2: Vertical descriptions — 4 × `handlers.py` (per SD-1/SD-3)
In each of `verticals/{procurement,energy,supply_chain,aquaculture}/handlers.py`, add
`ACTION_DESCRIPTIONS: dict[str, str]` beside the existing `ACTION_TYPES` tuple (tuple unchanged
— it mirrors the ontology enum) plus a description for `echo`, and pass them in the existing
`register_*_handlers()` loops (e.g. `procurement/handlers.py:67-73`). Author the procurement
pair with care — it is the load-bearing distinction: `emergency_source` ≈ "urgent off-cycle
sourcing for a critical failure / line-down where normal reorder lead time is unacceptable";
`reorder` ≈ "routine on-contract restock at normal lead time (calm path)" — wording adapted
from, not copied out of, the governed prose (`procedures.yaml:139-143`, `:337-340`). Per-vertical
test: description keys == registered handler names.

### Step 3: Prompt — render the "Available actions" catalog (per SD-2)
Add an optional catalog parameter (default `None`) to `build_system_instruction`
(`prompt.py:49-87`), `build_reasoning_messages` (`:101-121`), and `build_structuring_messages`
(`:124-173`); when present, append an "Available actions" block to the trusted instruction
(placed with the `goal` block, `:81-86` — trusted authored config, never inside the untrusted
event block). `None` → byte-identical output (AC-4). Tests in
`tests/services/engine/llm/test_prompt.py`: render shape (name — description; name-only when
`None`), byte-parity mirroring `:48`, catalog-absent-from-untrusted-block (mirroring the `:64`
goal test), containment invariants untouched.

### Step 4: Structured — thread the catalog through `generate_judgment` (per SD-2)
In `generate_judgment` (`structured.py:152-225`), fetch `registry.handler_catalog(vertical)`
beside the existing `handler_names` fetch (`:188`) and pass it to both builder call sites
(`:198-201`, `:208-210`) behind a new keyword (default off/`None` → byte-identical), covering
all three `reasoning_mode`s including `skip`. Optionally sharpen the `suggested_handler` field
description (`:103-105`) to point at the catalog — only if it provably keeps the schema shape
(tripwire (ii) otherwise). Tests in `tests/services/engine/llm/test_structured.py`: catalog
threaded when enabled, enum still `list(handler_names)` (`:111-125` unchanged), default path
byte-identical.

### Step 5: Config flag + recommender threading (per SD-4)
Add the default-off flag to `Settings` (`services/api/config.py`, modeled on `:129-152`) and
thread it at the reactive call site (`recommender.py:205-207`). Tests:
`tests/services/engine/test_recommender_config.py` (default off; flag-on passes the catalog),
`test_recommender.py` (flag-off prompt unchanged end-to-end).

### Step 6: Offline gate + PR
Full suite + ruff + mypy green under the required CI `gate` on a fresh PR (AC-6; prove main-green
via the PR's CI, not a named subset). Conventional commit `feat(recommender): ...` referencing
PLAN-0060; Code commits via PR per CLAUDE.md §7 (ADR-009 D2).

### Step 7: Live re-validate — post-merge, Cray-gated, evidence-only (per SD-5; AC-7)
**Host-state (CLAUDE.md §8): explicit Cray go BEFORE running.** Pre-commit the pass/fail read
(`suggested_handler == "emergency_source"` AND `actor_kind == "llm"`), warm MS-S1, run the same
`recommend()`-only driver shape as the session-114 smoke with the flag on and the same event,
ONCE. Record the result in `docs/logs/2026-MM-DD-reactive-handler-catalog-live-revalidate.md`
win-or-lose. On pass → follow-up one-line default-flip PR (SD-4). On miss → finding, flag stays
off, next iteration is a new Cray decision (no silent prompt-fishing).

## Verification

How do we know it worked? **Binding:** AC-1…AC-6 — the offline suite proves the catalog is
captured, rendered flag-on, byte-absent flag-off, enum-constrained as before, and regression-free
under CI `gate` on a fresh PR. **Confirming (never gating):** AC-7 — one pre-committed,
Cray-gated live run shows the real `gpt-oss:20b` now selects `emergency_source` for the exact
event that produced the session-114 `reorder` finding, recorded on disk in `docs/logs/`.

## Open Questions

- **OQ-1 — flag name.** `handler_catalog_enabled` vs `recommender_handler_catalog_enabled` —
  cosmetic; settle at Step 5 review (the sibling flags carry no subsystem prefix, `config.py:129`,
  `:142`).
- **OQ-2 — does `echo` belong in the catalog?** It is a registered, enum-visible handler
  (session-114 smoke showed the model the 6-name enum including `echo`), so describing it
  ("diagnostic no-op — record the action without performing anything") is more honest than
  leaving the one undescribed name; but Cray may prefer it excluded from the *rendered* catalog
  while staying in the enum. Default in the Steps: describe it, render it.
- **OQ-3 — description length discipline.** Recommend a soft cap (~1–2 lines / ~160 chars) so
  the catalog never dominates the small local model's context; enforce by convention + test on
  string length, or convention-only? Default: convention-only in this PLAN.

## Size estimate

**S–M.** Core diff is small (one registry field + accessor, one prompt block, one flag, one
threading argument) but touches four verticals' `handlers.py` + five test modules; the authored
description strings are the only genuinely new content. Single PR, plus the Step-7 follow-up
flag-flip one-liner.
