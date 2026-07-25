# PLAN-0093: LLM-Arm Degrade Disclosure — no silent arm swap

**Status:** COMPLETE
**Owner:** Claude Code
**Created:** 2026-07-25
**Related ADRs:** ADR-007 (RecommendedAction envelope / ReasoningStep), ADR-010 (IN-4 fail-safe contract), ADR-0030 (advisory never-raise), ADR-0032 (standing direction — demo→pilot wedge)

## Goal

Make every LLM→deterministic degrade in the running system **disclosed in a
returned or persisted structure** — never only in a log line — so that when the
engine swaps a model judgment for a threshold rule or a phrasing template, the
consumer of the result can tell. This is the governance precondition for the
ratified forward direction (a deterministic arm and an LLM arm running side by
side in one pipeline): before arms can be *declared*, a swap between them must
be *visible*. Scope is disclosure only — no arm wiring changes, no per-step arm
vocabulary (that is a later, separate ADR). "Every" is meant literally, and the
ACs match it: the reactive action path (`/actions`), the NL-query path
(`/query`), the run-corpus insights path (`POST /insights/query`, shipped by
PLAN-0088 — AC-8, Cray-ratified widening), and the governed-procedure retry
budget. Partial disclosure would be worse than uniform silence — it implies a
coverage that is not there.

## Context — the verified fact base

The codebase has already ratified "disclosed, not silent" for exactly one
degrade: `services/engine/action_verification.py:339-352` `_degraded_step()`
merges `verification_mode` / `judge_status` / `judge_disclosure` into a trace
step's `detail` and appends a note to its `summary` ("constraint ④ — disclosed,
not silent"). And one shipped component already declares which arm ran:
`services/engine/procedures/gate_advisory.py:148-174` sets `detail["model"]` to
`"deterministic"` or the live model's name. Everything below extends those two
existing shapes; nothing here invents a new disclosure idiom.

The holes, each read off disk:

- **H1 — `actor_kind` computed then dropped.** `services/api/routers/actions.py:55-70`
  `_to_response()` omits `audit_metadata` entirely. `AuditMetadata.actor_kind`
  (`services/engine/actions.py:74`) is `"engine"` on the rule path
  (`services/engine/recommender.py:335`) and `"llm"` + model name on the LLM
  path (`services/engine/llm/trace.py:58-67`) — the correct discriminator,
  already computed, never crossing the HTTP boundary. `audit_metadata` is a
  **required** field on the envelope (`services/engine/actions.py:100`), and
  `_to_response` is the **only** constructor of `RecommendationResponse`
  (verified by grep), so a required additive projection is safe.
- **H2 — `outcome` computed then dropped.** `services/api/routers/query.py:19-29`
  maps 8 fields of `NlAnswer`; `NlAnswer.outcome` (`services/engine/nl_query.py:220`,
  `QueryOutcome` at `:85`) is not among them.
- **H3 — the recommender fail-safe discards the evidence.** `recommender.py:252-265`:
  the except-branch logs the exception and returns `_rule_recommend(event, vertical)`.
  The returned record's trace (`recommender.py:302-321`) is two `rule_check`
  steps — **byte-identical to a rule run where the LLM was never attempted** —
  and `RULE_CONFIDENCE` (applied at `:331`) is a plausible model confidence, so
  nothing in the record discriminates "rule by design" from "rule because the
  model died". Note the irony: `_rule_recommend`'s own docstring
  (`recommender.py:277-279`) claims the record "shows the path actually taken" —
  it shows *a* rule path ran, not that an LLM arm was attempted and failed.
- **H4 — the phrase-stage degrade has no channel at all.** `nl_query.py:1063-1071`:
  the exception branch logs and returns `_fallback_answer(...)`; the
  empty-content branch (`:1070-1071`, `answer or _fallback_answer(...)`) swaps
  in the template **with no log at all**. `_phrase` returns a bare `str` — the
  fact "a template wrote this" cannot be expressed in-process without a
  signature change. This is the substantive design problem (ruled in SD-1).
- **H4b — the run-corpus insights path has the identical hole (shipped two
  days ago by PLAN-0088).** `services/api/routers/insights.py:260-267`: an
  unconstructible backend logs and returns `run_query.fallback_run_answer(...)`;
  `services/engine/run_query.py:416-423`: the chat-exception branch logs and
  degrades (`:420-422`), and the empty-content branch (`:423`,
  `chat_result.content.strip() or fallback_run_answer(...)`) degrades **with
  no log at all** — verified on disk to be symmetric with
  `nl_query.py:1070-1071`, not assumed. `RunQueryAnswer`
  (`services/api/models/insights.py:209-238`) carries no arm signal, so a
  model-phrased and a template-phrased answer are indistinguishable at
  `grounded=True` (`insights.py:320-327`). Covered by AC-8 (Cray-ratified
  widening — the Goal's "every degrade" stands; the ACs widen to meet it).
- **H5 — `grounded` is not arm provenance.** `grounded` means "≥1 source object
  backed the answer" (`nl_query.py:203-209`, `services/api/models/query.py:32-35`).
  A template-phrased answer over 11 records is `grounded=True`, identical to a
  model-phrased one.
- **H6 — `LLM_RETRY_BUDGET` is inert on the governed procedure path.**
  `services/engine/procedures/action_step.py:286` hardcodes `retry_budget: int = 3`
  (passed at `:307`); no vertical factory overrides it (grep of `verticals/` is
  empty). `settings.llm_retry_budget` (`services/api/config.py:106-113`) is
  honoured on the reactive paths (`recommender.py:214`, `nl_query.py:1135`) but
  never on procedures — the disclosed configuration is not the operative one.
- **H7 — nothing durable on any degrade.** `append_audit`
  (`services/db/audit_log.py:133`) has **13** call sites on disk (the dispatch
  fact-pack said 12 — count corrected here; the substance holds): `event_skipped`,
  `schedule_skipped` ×2, `schedule_missed`, `read_refused`, `run_started`,
  `run_resumed`, `run_cancelled`, `gate_refused` ×2, `gate_decision`,
  `handler_receipt`, plus the **event-bridge fire-failure** site at
  `routers/actions.py:111` (inside `_alert_event_fire_failure`,
  `routers/actions.py:95-124` — writes `event_fire_missed` /
  `event_fire_failed`, best-effort inside `try/except` so a broken DB cannot
  break the read path). All 13 are governance/run state transitions or their
  loud failure records; none is an LLM degrade.
  `services/db/persistence.py:20-58` persists no reasoning trace and no
  `actor_kind`. (Ruled in SD-3: deferred.)
- **H8 — trace vocabulary is CI-pinned.** `services/api/static/assets/trace-kinds.js:33-61`
  is pinned by `tests/api/test_trace_kind_labels.py`. This PLAN deliberately
  mints **no new trace kind** (see SD-5), so that pin stays untouched and green.

Today every governed procedure run is end-to-end deterministic anyway: all six
vertical factories inject `advisory_stub_factory`
(`services/engine/procedures/advisory_stub.py:86-89`, `model="stub"`). That
wiring is **unchanged** by this PLAN (locked).

## Locked constraints (from the dispatch — do not reopen here)

- **Disclosure only.** No arm wiring flips; all six verticals keep
  `advisory_stub_factory`.
- **No 4-mode vocabulary** (`deterministic / assisted / required / shadow`) as
  shipped types — that changes `procedures.yaml`/`Step` (the moat's source of
  truth) and requires its own ADR, merged before implementation (CLAUDE.md §8).
- **No new top-level `arm`/`mode` field** on `Step`, `procedures.yaml`, or any
  response model. Reuse `actor_kind`, `outcome`, and `ReasoningStep.detail`
  keys shaped like `_degraded_step()`.
- **Additive only.** No existing response field changes type or disappears —
  the committed vanilla-JS UI under `services/api/static/` consumes these.
- **Shadow-forward-compatible.** A future `shadow` run has BOTH arms' results
  in one step; any scalar proposed here must not assume exactly-one-arm-ran.
- **Sequenced before the MS-S1 public-hosting workstream**; no hosting content.

## Design rulings (SD-1 … SD-5)

### SD-1 — `_phrase` discloses via a typed result object (signature change)

**Ruling: change the signature.** `_phrase` returns a small frozen dataclass
instead of a bare `str`:

```python
@dataclass(frozen=True)
class PhraseResult:
    text: str
    phrased_by: str          # "deterministic" | the live model name (gate_advisory.py:149,174 convention)
    disclosure: str | None   # None on the intended-arm path; the degrade reason (truncated [:300], F7 convention) otherwise
```

All three branches of `_phrase` (`nl_query.py:1063-1071`) become explicit:
model success → `PhraseResult(answer, result.model, None)`; exception →
`PhraseResult(fallback, "deterministic", f"phrasing degraded to deterministic template: {exc}"[:300])`;
**empty content** → `PhraseResult(fallback, "deterministic", "model returned empty content; deterministic template used")`.
The orchestrator (`answer_question`) maps it onto two additive `NlAnswer`
fields — **`phrased_by: str = field(kw_only=True)`, required with no default
(Cray-ratified this session), and `phrase_disclosure: str | None = None`**.
The frozen-dataclass field-ordering constraint is real (`NlAnswer`,
`nl_query.py:201-220`, has defaulted trailing fields) but **avoidable, not
forcing**: on Python 3.12, `field(kw_only=True)` lifts it entirely. A
`= "deterministic"` default was rejected because it recreates, one level up,
the exact failure class this PLAN exists to kill — a construction site that
forgets the field would silently *claim a deterministic author*. Required +
keyword-only turns a missed set into a `mypy --strict` / construction-time
failure instead of a quiet wrong answer. `phrase_disclosure` stays optional:
absence legitimately means "no degrade". The purely-deterministic answers
(`_ungrounded` `:1077-1089`, `_no_data_nlanswer` `:1092-1104`) set
`phrased_by="deterministic"` explicitly — deterministic was the *intended* arm
there; disclosure marks a **degrade**, not determinism itself. `PhraseResult`
is homed in `nl_query.py`: `run_query.py:47` already imports from `nl_query`,
so the insights path (AC-8) reuses the same type with no import cycle.
This separation (arm identity always present; disclosure only on degrade) is
exactly the `gate_advisory` + `_degraded_step` split already shipped.

*Alternatives rejected:* caller-side detection (comparing output text against
the template — heuristic, breaks the moment templates change); an
out-parameter/module global (forbidden by the dispatch, and rightly — hidden
state). The accelerator applies: H1–H4/H6 sit under the full CI gate
(`pytest tests/`, `mypy --strict services/`, ruff), so the structurally honest
signature change is the cheap option, not the risky one.

*Shadow-forward-compat:* `phrased_by` names **the author of the returned answer
text** — exactly-one by construction even when a future `shadow` run executes
both arms (the non-authoring arm's output rides `ReasoningStep.detail` / the
disclosure channel, which are list/dict-shaped and multi-arm-safe).

### SD-2 — project only `actor_kind` + `actor`; `governed_decision` stays server-side

**Ruling: project exactly two fields**, both required, onto
`RecommendationResponse`: `actor_kind: str` ("engine" | "llm" | "human",
`actions.py:74`) and `actor: str` (the model name on the LLM path,
`llm/trace.py:60-61`; `"engine"` on the rule path, `recommender.py:335`).

**Do not project the rest.** `AuditMetadata.governed_decision`
(`actions.py:77-82`) carries a `ControlRef` **and a `principal_id`** — a
canonical Person PK (`actions.py:64-67`). Regardless of the current auth
posture of the actions read path, least-exposure argues the recommendation
surface must not become a principal-identity surface as a side effect of a
disclosure PLAN; and the model's own docstrings (`actions.py:57-58, 71, 80-81`)
mark that structure as deliberately minimal pending the deferred ADR-011 audit
framework — wholesale projection would pre-empt it. `correlation_id` is
internal plumbing; `notes` is boilerplate prose whose disclosure content
already rides the reasoning trace, which `_to_response` **already projects**
(`routers/actions.py:66`). Two fields buy the whole discriminator.

### SD-3 — the durable audit-log row is DEFERRED (explicitly, not silently)

**Ruling: out of scope for this PLAN.** Three reasons. (i) All 13 existing
`append_audit` actions are **state transitions** of a governed run / gate /
schedule (list in H7); "the LLM degraded" is execution telemetry — admitting it
would change the audit table's semantic class, which is a bigger decision than
it looks. (ii) The moment a degrade genuinely becomes a *governance* event is
the future `required` mode (fails closed instead of degrading) — that
vocabulary belongs to the later two-arm ADR, and minting an `llm_degraded`
audit action name now would pre-empt it. (iii) Nothing here forecloses the row:
the disclosure step's `detail` keys (SD-4) are the exact payload a future
`llm_degraded` row would carry. Honest consequence, stated plainly: on the
reactive path the disclosure added by this PLAN is response-visible and rides
the in-memory record (`routers/actions.py:47`), not a durable row — durable
degrade evidence lands with that later ADR.

### SD-4 — the recommender fail-safe disclosure shape (H3)

Append **one** disclosure step to the rule record's trace in the except-branch
of `recommend()` (`recommender.py:252-265`), after `_rule_recommend` returns —
`_rule_recommend` itself stays byte-identical (it is also the honest
rule-by-design path and must not carry degrade language):

```python
ReasoningStep(
    step_id="llm-degrade-disclosure",
    kind="rule_check",                      # existing, CI-pinned kind — no trace-kinds.js change
    summary="LLM arm failed; the deterministic rule fail-safe produced this recommendation (disclosed).",
    detail={
        "recommendation_mode": "rule-fail-safe",   # detail-key shape per _degraded_step (action_verification.py:345-350)
        "llm_status": type(exc).__name__,
        "llm_disclosure": f"LLM arm failed; deterministic fail-safe ran: {exc}"[:300],
    },
)
```

plus the same sentence appended to the record's `AuditMetadata.notes`. The
degraded record's trace is thereby **structurally distinguishable** from a
never-attempted rule run (3 steps vs 2, plus the detail keys), which kills the
H3 byte-identity. `actor_kind` stays `"engine"` — correct: the engine authored
the surfaced recommendation; the disclosure says a model was *attempted*, not
that it *authored*. Because the trace already renders in the committed UI and
the summary-note convention is how `_degraded_step` surfaces there, this is
visible to a human reviewer with **zero UI changes**.

### SD-5 — no new trace kind; and one considered-and-declined elimination

Reusing `kind="rule_check"` (with the disclosure carried in `summary` +
`detail`) keeps `trace-kinds.js` and its pinned test untouched (H8). A
dedicated `llm_degrade` kind with its own UI label was considered and declined:
it is more vocabulary minted adjacent to the reserved 4-mode decision, for a
rendering nuance the summary-note already delivers. The later ADR can promote
the kind if the 4-mode work wants it — the detail keys make retrofitting
mechanical.

Per the dispatch's elimination licence, one elimination was considered:
`StepFacet.llm_assist` (`services/engine/procedures/spec.py:794-798`), a
non-authoritative prose field that *describes* LLM involvement the runtime
ignores — a latent drift surface once real arms exist. **Declined here**: it is
explicitly documented as non-authoritative, and its fate (delete vs promote to
the real arm declaration) is precisely the 4-mode ADR's call. Flagged for that
ADR's agenda; eliminating it now would be scope creep into L2 territory.

## Acceptance Criteria

Each AC names the mutation that reddens its test (the counterexample step).
No AC may be satisfied by asserting on a log line (`recommender.py:259` and
`nl_query.py:1068` already log today — logs are the failure mode, not the fix).

- [x] **AC-1 (H1):** `RecommendationResponse` carries **required** additive
  fields `actor_kind` + `actor`, projected from `record.action.audit_metadata`
  in `_to_response` (`routers/actions.py:55-70`). Test (extend
  `tests/services/engine/test_recommender.py` + `tests/api/test_action_loop.py`
  patterns): an LLM-path recommendation (stubbed judgment) yields
  `actor_kind == "llm"` and `actor == <model name>` in the HTTP response; a
  rule-path one yields `"engine"`/`"engine"`. **RED if** the two projection
  lines are silently removed from `_to_response` — the required response fields
  raise `ValidationError` (no default can mask it).
- [x] **AC-2 (H2):** `NlQueryResponse` carries a **required** additive
  `outcome: Literal["answered","no_data","clarify"]` mapped in
  `routers/query.py:_to_response`. Test: a question matching zero records
  returns `outcome == "no_data"` with `grounded == False`; an answered one
  returns `"answered"`. **RED if** the mapping is silently removed
  (`ValidationError`) or hardcoded to `"answered"` (the no-data assertion
  fails).
- [x] **AC-3 (H3):** a `recommend()` run whose LLM path raises returns a record
  whose trace **contains** the `llm-degrade-disclosure` step with detail keys
  `recommendation_mode` / `llm_status` / `llm_disclosure`, and whose
  `audit_metadata.notes` carries the degrade sentence; a direct
  `_rule_recommend` record for the same event does **not** contain that step —
  assert the two traces are no longer equal (the anti-byte-identity tripwire,
  set-shaped, not prose). **RED if** the disclosure append in the
  except-branch (`recommender.py:252-265`) is silently removed — the
  step-presence and trace-inequality assertions both fail.
- [x] **AC-4 (H4 / SD-1):** `_phrase` returns `PhraseResult` (typed — not a
  bare `str`), and **both** degrade branches disclose: a client that raises
  yields `phrased_by == "deterministic"` + non-None `disclosure`; a client
  returning `content=""` (today's zero-channel, zero-log branch,
  `nl_query.py:1070-1071`) yields the same with its distinct
  empty-content reason. **RED if** the empty-content branch is silently
  reverted to `answer or _fallback_answer(...)` returning bare text — the
  empty-content disclosure assertion fails (and mypy fails the signature).
- [x] **AC-5 (H5):** arm provenance crosses the HTTP boundary:
  `NlQueryResponse` gains required `phrased_by` + optional `phrase_disclosure`,
  mapped from `NlAnswer`. Test: over the **same** fixture records, a healthy
  stub-model run and a degraded run are both `grounded == True` (H5 preserved
  — grounding is orthogonal) yet differ in `phrased_by` (model name vs
  `"deterministic"`), and only the degraded one carries a disclosure. **RED
  if** the router mapping is silently removed (required-field
  `ValidationError`) or any `NlAnswer` construction site omits the
  now-required `phrased_by` (keyword-only, no default — `mypy --strict` and
  construction both fail; the leaking-default failure mode no longer exists
  by SD-1's Cray-ratified required-field design).
- [x] **AC-6 (H6):** `settings.llm_retry_budget` is honoured on the governed
  procedure path: `ActionStepExecutor.retry_budget` becomes `int | None = None`
  with use-time fallback to `settings.llm_retry_budget` (the exact
  `nl_query.py:1135` idiom); an explicit constructor value still wins. The
  oracle counts **structuring attempts, not `chat` calls** — per the retry
  mechanics in `services/engine/llm/structured.py:201-236`: the call-1
  reasoning pass (`:209`) sits OUTSIDE the retry loop (run once; skipped only
  under `reasoning_mode="skip"`, `:205-207`), the
  `for attempt in range(1, budget + 1)` loop (`:218`) wraps only the
  structuring call (`:223` — the one that passes `response_format`), and
  exhaustion raises `StructuredOutputError` (`:236`). A client that *raises*
  would die at `:209` before the loop is entered — the wrong oracle. Test:
  monkeypatch `settings.llm_retry_budget = 2`; run `ActionStepExecutor()` with
  a counting client whose `chat` **returns schema-invalid content and never
  raises**, so the loop is actually entered. `reasoning_mode` is pinned by
  construction: the executor passes none (`action_step.py:306-308`), so the
  `"full"` default (`structured.py:159`) applies and call 1 always runs.
  Expected: exactly **2 structuring attempts** (calls where
  `response_format is not None`) and **3 total `chat` calls** (1 reasoning +
  2 structuring), then `StructuredOutputError` — the procedure path already
  fails closed on exhaustion, unchanged. **RED if** the field is silently
  reverted to the hardcoded `int = 3` (`action_step.py:286`) — the
  structuring-attempt count reads 3 (total `chat` calls 4), not 2.
- [x] **AC-7 (L4 guard):** additive-only, verified by the existing gate: full
  `pytest tests/` + `mypy --strict services/` + ruff green; no existing
  response field renamed/retyped/removed; `trace-kinds.js` byte-untouched and
  `tests/api/test_trace_kind_labels.py` green without modification. **RED if**
  any existing response field or pinned trace-kind registry entry is silently
  removed — the existing suite and the H8 pin redden.
- [x] **AC-8 (H4b — Cray-ratified widening):** the insights run-corpus path
  discloses identically. `run_query.phrase_run_answer`
  (`services/engine/run_query.py:386-423`) and the router wrapper
  (`routers/insights.py:248-267`) return `PhraseResult` (the same type as
  AC-4, imported from `nl_query` — no cycle, `run_query.py:47`), with all
  **three** degrade branches disclosing: backend-unconstructible
  (`insights.py:260-266`), chat exception (`run_query.py:420-422`), and empty
  content (`run_query.py:423` — verified on disk, symmetric with
  `nl_query.py:1070-1071`, not assumed). `RunQueryAnswer` gains required
  `phrased_by` + optional `phrase_disclosure`; the three
  deterministic-by-design refusal sites (`insights.py:292, 301, 312`) set
  `phrased_by="deterministic"` with no disclosure (intended arm, not a
  degrade), and the phrase-backed site (`insights.py:320-327`) maps from the
  returned `PhraseResult`. Test: over a populated run corpus, a healthy
  stub-model run vs each of the three degraded runs — `grounded == True`
  alike, `phrased_by` differs, and only the degrades carry a disclosure.
  **RED if** the `RunQueryAnswer` mapping is silently removed (required field
  under `extra="forbid"`, `insights.py:218` → `ValidationError`) or the
  empty-content branch is silently reverted to the bare
  `or fallback_run_answer(...)` (the empty-content disclosure assertion
  fails).

## Out of Scope

- ❌ Per-step arm declaration in YAML / `Step`; the 4-mode vocabulary
  (`deterministic / assisted / required / shadow`) as shipped types — later ADR
- ❌ Any change to which arm runs anything; `advisory_stub_factory` wiring stays
- ❌ A new top-level `arm` / `mode` field anywhere
- ❌ Durable `append_audit` rows for degrades (SD-3 — deferred with the ADR)
- ❌ UI rendering work for the new fields on `/query`, `/actions`, or
  `/insights` (the trace summary-note already renders; dedicated affordances
  ride later work)
- ❌ Insights changes beyond the AC-8 disclosure pair on `RunQueryAnswer` —
  the three refusal answers (`insights.py:292-318`) stay byte-equivalent apart
  from the two new fields; translate-stage behavior untouched. (The insights
  *path itself* is IN scope — AC-8; this line bounds how much of it.)
- ❌ Async run submission / `202 + run_id`; wall-clock deadlines
- ❌ Hosting, Cloudflare, Docker, MS-S1 deployment; hosted (non-Ollama)
  backends; `llm_backend` type changes
- ❌ Eliminating `StepFacet.llm_assist` (flagged to the 4-mode ADR agenda,
  SD-5)

## Steps

Each step lands gate-green on its own; order is engine-out.

### Step 1: `_phrase` typed result + `NlAnswer` provenance (SD-1; AC-4 groundwork for AC-5)

`services/engine/nl_query.py`: add `PhraseResult`; rewrite the three `_phrase`
exit branches explicitly (model-success / exception / empty-content — the
empty-content branch also gains the log line it never had, as incidental
hygiene, **not** as any AC's oracle); add `NlAnswer.phrased_by` (required,
`field(kw_only=True)` per SD-1) + `NlAnswer.phrase_disclosure` (defaulted);
update `answer_question` and every `NlAnswer` construction site
(`_ungrounded`, `_no_data_nlanswer`, the answered/clarify paths — each must
now set `phrased_by` explicitly; a missed site fails `mypy --strict`). Engine tests in `tests/services/engine/`:
raising-client, empty-content-client, healthy-stub, and pure-deterministic
(no-degrade ⇒ `disclosure is None`) cases.

### Step 2: recommender fail-safe disclosure (SD-4; AC-3)

`services/engine/recommender.py`: in the except-branch, wrap the
`_rule_recommend` result — append the `llm-degrade-disclosure` step and the
`notes` sentence (a small pure helper, `_disclose_llm_degrade(record, exc)`,
so the branch stays readable). `_rule_recommend` itself: byte-unchanged.
Tests in `tests/services/engine/test_recommender.py`: the AC-3 presence +
trace-inequality pair.

### Step 3: HTTP projection (SD-2; AC-1, AC-2, AC-5)

`services/api/models/query.py`: add `outcome` (required) + `phrased_by`
(required) + `phrase_disclosure` (optional). `services/api/routers/query.py`:
map all three. `services/api/models/actions.py`: add `actor_kind` + `actor`
(required). `services/api/routers/actions.py:_to_response`: project them.
Router tests in `tests/api/`: the AC-1/AC-2/AC-5 assertions over the live
FastAPI test app.

### Step 3b: insights run-corpus disclosure (H4b; AC-8)

`services/engine/run_query.py`: `phrase_run_answer` returns `PhraseResult`
(imported from `nl_query`), all exit branches explicit — success / exception
(`:420-422`) / empty content (`:423`, which also gains its missing log line as
incidental hygiene, not an oracle). `services/api/routers/insights.py`: the
wrapper (`:248-267`) propagates `PhraseResult` (its backend-unconstructible
branch becomes the third disclosed degrade); `services/api/models/insights.py`:
`RunQueryAnswer` gains `phrased_by` (required) + `phrase_disclosure`
(optional); all four construction sites (`insights.py:292, 301, 312, 320`)
updated in the same commit (required field under `extra="forbid"` keeps this
step atomic and gate-green). Tests in `tests/api/`: the AC-8 four-way matrix.

### Step 4: honour the retry budget on the procedure path (AC-6)

`services/engine/procedures/action_step.py`: `retry_budget: int | None = None`;
resolve at the `generate_judgment` call site (`:307`). Verify no constructor
call site passes a positional/keyword value that changes meaning (grep of
`verticals/` already empty; check `services/` + `tests/`). Test per AC-6.

### Step 5: full-gate closeout (AC-7)

Run `pytest tests/`, `mypy --strict services/`, ruff + ruff-format; confirm
`trace-kinds.js` untouched (`git diff --stat`); non-vacuity sweep: for each of
AC-1…AC-6 and AC-8, apply the named counterexample mutation in the working tree, watch
the named test go RED, restore from a `/tmp` copy of the edited file (never
`git checkout` — that wipes the uncommitted work under test), re-run GREEN.

## Verification

- The CI `gate` (full `pytest tests/` — 3203+ passing today — plus
  `mypy --strict services/` over 110 files, ruff, ruff-format) is the oracle
  for every AC; no live MS-S1 run is required (all arms stubbed; §8 host-state
  rule untouched).
- The six degrade triggers this PLAN names — recommender exception
  (`recommender.py:252-265`); NL-query phrase exception + phrase empty-content
  (`nl_query.py:1063-1071`); insights backend-unconstructible
  (`insights.py:260-266`); run-corpus phrase exception + empty-content
  (`run_query.py:416-423`) — each have a test asserting a **returned
  structure** discloses the degrade; the Step-5 mutation sweep demonstrates
  each oracle is non-vacuous (the named test reddens under the named mutation).
- Discriminator spot-check (manual, cheap): hit `POST /query` (and the same
  pair against `POST /insights/query`) twice against the dev app — once with
  the backend up, once degraded — and confirm the payloads differ in
  `phrased_by` while both stay `grounded: true` over the same records.
- The reversal seam is clean: every change is additive; reverting this PLAN
  removes fields consumers may ignore and restores no silent behavior that
  anything else depends on.

## Outcome (session 172, 2026-07-25)

All 8 ACs met. Shipped in **#911** (`55d2007`), five commits, one per step:
`7a852e3` Step 1 · `b73b19c` Step 2 · `e0ed8d1` Step 3 · `82e518c` Step 3b ·
`27ef271` Step 4.

**Evidence.** Suite **3203 → 3217**; every delta was predicted before its run and
matched. `mypy --strict services/` clean over 110 files; ruff + ruff-format clean
over 479. `trace-kinds.js` byte-untouched and its pinned test green unmodified
(AC-7). The full gate was re-run on the merge commit `55d2007` — CI is PR-only,
so a merge commit is otherwise never tested. No live model was contacted at any
point; §8 host-state untouched.

**The Step-5 sweep is the load-bearing evidence.** For each of AC-1…AC-6 and
AC-8 the named counterexample mutation was applied to the working tree, the named
test confirmed RED, the file restored from a `/tmp` copy (never `git checkout`)
and confirmed byte-identical and GREEN again. All 7 reddened. No oracle is
vacuous.

**Two review corrections proved themselves in execution.** (1) `phrased_by`
required rather than defaulted (Cray-ratified): the moment it landed, a benchmark
gold-set helper failed loudly with `TypeError` — a fifth `NlAnswer` construction
site this PLAN had not counted. Under the drafted default it would have passed
silently while mislabelling its fixtures. (2) The insights widening
(Cray-ratified): reading the path on disk rather than assuming symmetry with
`/query` found **three** degrade branches there, not two.

**Carried forward, deliberately not built here:** the 4-mode arm vocabulary
(`deterministic / assisted / required / shadow`) and its per-step declaration in
`procedures.yaml`; a durable `append_audit` row for a degrade (SD-3); the fate of
`StepFacet.llm_assist` (SD-5). All three belong to the two-arm ADR.

---

*Drafted by the in-harness `plan-drafter` subagent (ADR-013 D1 phased
authority; ADR-012 D4.3 author≠reviewer disclosure). Outline originator: Code
(session dispatch, 2026-07-25, from Cray's two-arm direction). Independent
reviewer: Cray at PR merge; Code performs R2 + commits per ADR-009 D2.
Separation: INTACT.*
