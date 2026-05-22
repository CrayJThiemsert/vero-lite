---
plan: PLAN-0006
title: LLM reasoning-hook execution — swap recommend() from rule-based to LLM-backed (the "brain swap")
status: Ready
owner: Claude Code (executes); Cowork (authoring); Cray (adjudicates surfaced decisions)
created: 2026-05-22
session: 10
batch: plan0006-authoring
related_adrs:
  - ADR-010 (LLM reasoning-hook surface — AUTHORITATIVE; D1 backend, D2 structured output, D3 reasoning trace, D4 guardrail, D5 swap surface; IN-1..IN-4; follow-on T3)
  - ADR-007 (OCT engine contracts — D2 RecommendedAction envelope [UNCHANGED], D4 layer ownership)
  - ADR-001 (LLM model baseline — gemma4:26b / qwen2.5-coder:32b; cloud-fallback posture)
  - ADR-002 (network topology — MS-S1 MAX local LLM server http://ms-s1-max:11434)
  - ADR-009 (Cowork Tier-1 authorship + D2 "only Code commits" fail-safe + K-1/K-2 workflow)
related_plans:
  - PLAN-0005 (OCT Engine Runtime Layer — Phase 2; MERGED c646bab; this plan swaps its §6.5 rule recommender)
  - PLAN-002 (custom Postgres image — undrafted; not a dependency here)
authored_by: cowork-session-11 (Tier 0 + Tier 1 merged workspace per ADR-009 D1; uncommitted draft — Code commits per ADR-009 D2)
---

# PLAN-0006 — LLM reasoning-hook execution (the "brain swap")

## 1. Status

**Ready** — authored 2026-05-22 by Cowork (Tier 0 + Tier 1 merged workspace, per
ADR-009 D1) from the Cray-routed dispatch
`.claude/handoffs/session-10/2026-05-22-1900-code-plan0006-dispatch.md`, grounded
in **ADR-010 (Accepted, `48fe240`)** and the two Tier-0 research briefs. The §8
surfaced decisions SD-1..SD-5 were **adjudicated by Cray 2026-05-22** (rulings
recorded inline in §8). Code reviewed (R2 — fact-pack verified against the live
repo: the `recommend()` signature, the sole `async` call site, `RULE_CONFIDENCE`,
and the `kind`/`actor_kind` enums all check out) and commits per ADR-009 D2 ("only
Code commits" fail-safe).

Readiness gate:

- [x] Cray adjudicates the §8 surfaced decisions (SD-1..SD-5) — done 2026-05-22.
- [x] Code lands the doc on `origin/main`.
- [ ] A Phase-1 kickoff dispatch is then authored as a separate round (mirroring
      the PLAN-0005 → kickoff-dispatch split), carrying the §8 rulings as binding.

ADR-010 division of labour is binding: **ADR-010 owns the *what / surface*;
PLAN-0006 owns the *how*** — prompt assembly, structured-output wiring, parsing,
retry, fail-safe, and eval. Where this plan and ADR-010 appear to disagree,
**ADR-010 wins** and this plan must be amended.

## 2. Context

PLAN-0005 Phase 2 (MERGED, PR #4, `c646bab`) shipped a deliberately **rule-based**
recommender. `services/engine/recommender.py::recommend()` applies one deterministic
threshold rule (reading ≥ `OVERTEMP_THRESHOLD_CELSIUS` = 90.0) and emits a
`RecommendedAction` envelope (ADR-007 D2) wrapped in an `ActionRecord` at status
`proposed`; the read → recommend → approve → execute loop runs end-to-end on the
energy vertical with real persistence. The governing intent (recommender.py OQ-3)
was "prove the pipe runs, then swap the brain".

ADR-010 fixed the **surface** of that swap (five decisions D1–D5, four binding
Implementation Notes IN-1..IN-4). This plan executes the swap: it replaces the rule
body of `recommend()` with an LLM path that returns the **same** envelope, behind
the **same** approval gate, with a deterministic **fail-safe**.

### 2.1 Strategic frame

The recommender's reasoning "brain" is the actual product value (PLAN-0005 §8.1
revisit register, row 1); the rule was always a stand-in. This plan is the
foundational pickup of that deferral. Per ADR-010 D5 the blast radius is **one
function and its new prompt-assembly + parsing + client helpers** — the envelope
(ADR-007 D2), the approval gate (D4), persistence (`services/db/`), and the API
router structure stay intact.

## 3. Scope

### 3.1 Goal

Replace the deterministic body of `services/engine/recommender.py::recommend()`
with a **local-LLM-backed** reasoning path (ADR-010 D1: MS-S1 MAX default, Ollama
per ADR-002) that produces a schema-valid ADR-007 D2 `RecommendedAction` via
**JSON-schema-constrained generation + a bounded validate-and-retry loop**
(ADR-010 D2), populates a **hybrid reasoning trace** (ADR-010 D3), surfaces model
confidence as **advisory only** (ADR-010 D5 / IN-3), and **fails safe** to the
deterministic rule path or `None` on LLM failure (ADR-010 D5 / IN-4) — all behind
the **unchanged** approval gate (ADR-010 D4), with an **eval strategy** for the now
non-deterministic `recommend()` (ADR-010 T3). The verifiable deliverable is the
green read → recommend → approve → execute loop running on the LLM path against the
energy synthetic adapter, with the LLM fail-safe demonstrably falling back to the
rule path under induced failure.

### 3.2 In scope

| Deliverable | Path (proposed) | Source contract |
|---|---|---|
| Pre-implementation `think`/`format` verification spike (IN-1) | throwaway script + a recorded result in the kickoff/closeout; **a pinned config**, no production code | ADR-010 IN-1, brief 3b §4.1 |
| LLM client wrapper (Ollama; two-call Pattern B capable) | `services/engine/llm/client.py` (new pkg `services/engine/llm/`) | ADR-010 D1/D2; ADR-002 Ollama API |
| Prompt assembly + untrusted-text containment (IN-2) | `services/engine/llm/prompt.py` | ADR-010 D4 / IN-2; brief #3 §5 |
| Structured-output parse + validate-and-retry + semantic checks | `services/engine/llm/structured.py` | ADR-010 D2; brief #3 §3, brief 3b §4 |
| Hybrid reasoning-trace assembly | `services/engine/llm/trace.py` (or within `structured.py`) | ADR-010 D3 |
| `recommend()` rewired to the LLM path + fail-safe | `services/engine/recommender.py` (edit; signature preserved per §6.2) | ADR-010 D5 / IN-4 |
| LLM/runtime settings (backend, model pins, retry budget, timeout) | `services/api/config.py` (extend existing `Settings`) | ADR-010 D1/D2; §5 |
| Eval harness + golden-trace fixtures for a stochastic `recommend()` | `tests/engine/eval/` (+ fixtures) | ADR-010 T3 |
| Unit + integration tests (LLM path mocked; fail-safe; semantic checks) | `tests/engine/` + `tests/api/` | §7 |
| Dep additions if any (Instructor / Pydantic-AI — see SD-4) | `pyproject.toml` | Code-only edit |

### 3.3 Out of scope (defer)

- ❌ **Hosted Claude API path beyond a guarded, consent-gated stub.** ADR-010 D1
  makes the hosted path a *fallback*; this plan builds the local path end-to-end and
  leaves a clean seam (a backend selector) for the hosted fallback. Whether the
  hosted call is fully implemented now or stubbed is **SD-5**.
- ❌ **Full approval + audit framework** (correlation-id propagation, approval-chain
  enforcement, immutable audit log) — ADR-011+ (PLAN-0005 §8.1; ADR-010 D4
  "no new gate").
- ❌ **A second LLM-judge gate** before the human gate — ADR-010 D4 Alt; deferred.
- ❌ **External confidence calibration** — ADR-010 D5 keeps `confidence` advisory;
  deriving a calibrated score is a later ADR.
- ❌ **OpenTelemetry GenAI backend deployment** (Langfuse/OTLP) — the trace is
  populated in-envelope (D3); standing up an external trace backend is later
  observability work (brief #3 §4.1).
- ❌ **Serving-path BIOS/driver tuning + a serving runbook** — ADR-010 Consequences
  flags a runbook item; that is a deployment doc, not this plan's code (brief 3b §2.2).
- ❌ **Migrating off Ollama to vLLM / llama.cpp-HIP** — ADR-002 is Ollama-wired;
  a server change is a separate, larger decision (brief 3b §6 item 1).
- ❌ **Changing the ADR-007 D2 envelope or the `ActionStatus` lifecycle** — §6.1.

### 3.4 Forward reference (not this plan)

- Audit framework (ADR-011+) replacing the minimal gate.
- Hosted-fallback hardening + a backend-selection ADR if the local path proves
  insufficient on real (non-synthetic) partner data.
- Confidence-calibration method (future ADR).

## 4. Architectural anchors (read alongside this plan)

| Anchor | Path | Relevance |
|---|---|---|
| ADR-010 | `docs/adr/0010-llm-reasoning-hook-surface.md` | **Authoritative** — D1–D5, IN-1..IN-4, T3 |
| ADR-007 | `docs/adr/0007-oct-engine-contracts.md` | D2 envelope (UNCHANGED), D4 layer ownership |
| ADR-001 | `docs/adr/0001-llm-model-baseline.md` | model pins; gemma4 is named in the IN-1 bug |
| ADR-002 | `docs/adr/0002-network-topology.md` | MS-S1 MAX, Ollama endpoint, residency boundary |
| Brief #3 | `docs/research/private/2026-05-21-llm-reasoning-hook-design.md` | §3 structured output, §3.4 grammar/thinking, §4 trace faithfulness, §5 OWASP, §6 AIP |
| Brief #3b | `docs/research/private/2026-05-22-llm-reasoning-hook-local-models.md` | §2 throughput/serving, §3/§4 models, §4.1 #15260, §5 Pattern-B configs |
| Swap target | `services/engine/recommender.py` | `recommend()`, `RULE_CONFIDENCE`, gate |
| Envelope | `services/engine/actions.py` | `RecommendedAction`, `ReasoningStep.kind`, `AuditMetadata.actor_kind` |
| Registry / adapter | `services/engine/registry.py`, `services/engine/data_adapter.py` | handler resolution + adapter context |
| Lesson #7 | `docs/lessons/0007-harness-exit-code-artifact.md` | §3 reliable verification methods (all §7 use these) |

## 5. Toolchain + fact-pack (verified against the live repo at authoring)

| Item | Value | Source (live repo) |
|---|---|---|
| HTTP client | httpx `>=0.27.0` — already declared; the Ollama call uses `httpx.AsyncClient` | `pyproject.toml` (PLAN-0005 §5 row "HTTP client … future Ollama/LLM ingress") |
| Validation models | Pydantic v2; `RecommendedAction.model_json_schema()` is the generation schema | `services/engine/actions.py` |
| Settings | `services/api/config.py::Settings` (pydantic-settings) holds the async DB URL today | PLAN-0005 §5 |
| LLM server | Ollama at `http://ms-s1-max:11434` (LAN) | ADR-002 |
| Model baseline | `gemma4:26b`, `qwen2.5-coder:32b` | ADR-001 |
| **Sole `recommend()` call site** | `services/api/routers/actions.py::_populate_store()` line 55: `record = recommend(event, _VERTICAL)` — **called WITHOUT `await` inside an already-`async def`** | verified by grep + read at authoring |
| Envelope `kind` enum admits | `'ontology_query'`, `'llm_inference'`, `'rule_check'` (free-text `str`, documented values) | `services/engine/actions.py:22` |
| `actor_kind` enum admits | `'engine'`, `'llm'`, `'human'` | `services/engine/actions.py:37` |
| Existing fixed confidence | `RULE_CONFIDENCE = 0.8` (rule path) | `services/engine/recommender.py:31` |

**Load-bearing call-site finding (grounds SD on async, §6.2):** the *only* runtime
caller of `recommend()` is `_populate_store()`, which is already `async` and calls
`recommend()` synchronously. Converting `recommend()` to `async def` therefore costs
**one added `await`** at that call site and leaves the router endpoints, the
approval gate, persistence, and ADR-007 wiring untouched — consistent with ADR-010
D5 "API wiring unaffected". (Test/eval call sites are added by this plan.)

**IN-1 freshness caveat:** the model survey is post-cutoff (2026) and web-sourced in
the briefs; the `think`/`format` interaction (Ollama #15260) must be **verified on
the live box**, not assumed from the briefs — that is exactly what Step 0 does.

## 6. Component contracts

### 6.1 Hard constraints — do not violate (ADR-010 §6)

- The **ADR-007 D2 `RecommendedAction` envelope does not change.** The LLM fills
  existing fields (`reasoning_trace`, `confidence`, `affected_entities`,
  `suggested_handler`, `handler_payload`, `audit_metadata`).
- The **`ActionStatus` lifecycle, `approve()`/`reject()`/`execute()`, the
  registry-resolved handler dispatch, persistence, and API wiring are unaffected**
  (ADR-010 D5).
- The **existing approval gate is the guardrail** — no new gate (ADR-010 D4).
  `requires_approval` stays `True` on every recommendation.
- **Local LLM on MS-S1 MAX is the default backend**; Claude API is a consent-gated,
  non-PII-only fallback (ADR-010 D1).
- **Cowork does not commit and does not edit `services/**` or `tests/**`** — this
  plan *describes* the work; Code executes it later (ADR-009 D2).

### 6.2 Swap surface — `recommend()` signature (ADR-010 D5)

`recommend(event: dict[str, Any], vertical: str) -> ActionRecord | None` keeps its
**parameters and return type**. The body becomes LLM-backed. **One open mechanical
point — surfaced as SD-1 (async):** an Ollama call is network I/O; the cleanest
implementation is `async def recommend(...)` using `httpx.AsyncClient`. Per §5 the
sole runtime caller is already `async`, so this is a one-`await` change and does not
disturb the router. A literal reading of ADR-010 D5 ("same signature") does not
address sync-vs-async; this plan treats `async def` as the recommended,
minimal-blast-radius reading and flags it for Cray (SD-1).

### 6.3 LLM client + Pattern B (ADR-010 D2/D3)

`services/engine/llm/client.py` wraps the Ollama chat API (`httpx.AsyncClient`,
base URL + model + timeout from settings). It supports **Pattern B (two calls)**
per brief 3b §5: call 1 reasons (`think=true` → `message.thinking` becomes the
`llm_inference` narrative, `message.content` a draft); call 2 emits the constrained
envelope via `format` = `RecommendedAction.model_json_schema()`. Whether call 1 and
call 2 use one model or a best-of-breed pair is **SD-3**; whether the trace uses a
separate reasoning pass at all (Pattern B two-call) vs a single constrained call is
**SD-2**.

### 6.4 Structured output + validate-and-retry + semantic checks (ADR-010 D2)

`services/engine/llm/structured.py`:

1. Constrained generation against the envelope JSON Schema (Ollama `format`), or via
   a client-side wrapper (Instructor/Pydantic-AI over Ollama) — **SD-4**.
2. **Validate-and-retry loop**, retries capped per **SD-1-budget** (ADR-010 D2 says
   2–3): on Pydantic `ValidationError`, feed the validator error back as *context*
   for one bounded retry. **Containment (IN-2 corollary, brief #3 §5.2 item 4):** the
   validator-error string is model-derived and must be inserted as labelled
   untrusted context, never with system-instruction authority.
3. **Semantic checks beyond schema validity** (brief #3 §3.4 "syntax ≠ semantics"):
   `suggested_handler` resolves in the registry for the vertical
   (`registry.get_handler(vertical, name)` — catch `RegistryError`); every
   `affected_entities` primary key is non-empty/resolvable; `confidence ∈ [0,1]`
   (Pydantic already enforces the range). A semantic-check failure is a retry
   trigger, then a fail-safe trigger (§6.6).

### 6.5 Hybrid reasoning trace (ADR-010 D3)

The LLM path populates `RecommendedAction.reasoning_trace` with:

- one `ReasoningStep(kind="llm_inference")` carrying the **model-asserted** rationale
  (the `message.thinking` narrative), explicitly labelled as model-asserted — **not**
  a faithful explanation (brief #3 §4.2); and
- **harness-emitted** `ReasoningStep(kind="ontology_query")` / `kind="rule_check"`
  steps recording what the engine actually did (evidence retrieved via the adapter,
  thresholds/registry checks run).

`AuditMetadata.actor_kind = "llm"` on the LLM path. **`confidence` is advisory only**
(IN-3): surfaced to the reviewer, never used to gate automation. The trace is a
human-review + audit artifact, not a guarantee of model computation.

### 6.6 Fail-safe (ADR-010 D5 / IN-4)

`recommend()` **never raises into the runtime loop.** On LLM failure after the retry
budget (connection error / timeout / unparseable output / failed semantic checks),
it falls back to **the existing deterministic rule path** (retained, see below) or
returns `None`. The fallback emits an `llm_inference`-absent trace (rule_check steps
only) and `actor_kind="engine"` so the audit record shows the path actually taken.
The deterministic rule body is **retained** as the fail-safe (not deleted) — this
also keeps ADR-010's "fully reversible" property real.

### 6.7 Prompt-injection containment (ADR-010 D4 / IN-2)

`services/engine/llm/prompt.py`: ingested operational free-text (asset labels,
event free-text fields) is the injection surface (brief #3 §5.3). The prompt
assembler **segregates and labels** untrusted event text in a clearly delimited,
non-authoritative section; **never concatenates** it with system-instruction
authority; and relies on **least-privilege handler/registry access** so a
compromised prompt cannot reach an unintended handler (the §6.4 registry check is
the enforcement point). No claim of full prevention — containment + the human gate
is the posture (brief #3 §5.3).

## 7. Acceptance Criteria

All criteria use **Lesson #7 §3 reliable verification methods** — in-process return
probes, captured stderr/stdout summary lines, or behavioural side-effect assertions.
**No `echo $?`, no "expect exit N" wording** (Lesson #7 §4). LLM calls in tests are
**mocked/faked** (a fake Ollama client returning canned `thinking`/`content`/JSON)
so the suite stays deterministic and offline; the live-model behaviour is covered by
the Step 0 spike + the §7.6 eval harness, not the unit suite.

### 7.1 IN-1 verification (Step 0 gate)

- [ ] A recorded result shows whether the pinned model + Ollama version honours
      `format` schema constraint, and under which `think` setting (the #15260
      interaction) — captured as a written finding in the kickoff/closeout, with the
      chosen config pinned in settings. (Behavioural: the spike output line, not `$?`.)

### 7.2 Structured output + retry

- [ ] Given a fake LLM returning schema-valid JSON, `recommend()` returns a
      `RecommendedAction` that `model_validate(model_dump())` round-trips — in-process.
- [ ] Given a fake LLM returning malformed-then-valid JSON, the retry loop recovers
      within the budget and returns a valid envelope; the retry count is asserted —
      in-process on a spy/fake.
- [ ] Given a fake LLM whose `suggested_handler` is unregistered, the semantic check
      rejects it (retry, then fail-safe) — in-process assertion on the resulting path.

### 7.3 Reasoning trace + advisory confidence

- [ ] On the LLM path the trace contains ≥1 `kind="llm_inference"` step **and** ≥1
      harness-emitted step; `audit_metadata.actor_kind == "llm"` — in-process.
- [ ] `confidence` is carried through to the envelope and is **not** used in any
      approve/execute branch (asserted by code-path inspection in a test that
      approves/executes regardless of confidence value) — behavioural.

### 7.4 Fail-safe (the load-bearing safety criterion)

- [ ] With the LLM client forced to raise (connection error), `recommend()` returns a
      valid rule-path `ActionRecord` (or `None` for a sub-threshold event) and **does
      not raise** — in-process assertion that no exception escapes.
- [ ] The fail-safe record carries `actor_kind="engine"` and a rule_check-only trace
      — behavioural assertion on the returned envelope.

### 7.5 End-to-end loop (LLM path) + API regression

- [ ] One integration test drives read → recommend (LLM, faked) → approve → execute
      and asserts terminal `status == "executed"` and the persisted row reflects it —
      behavioural (mirrors PLAN-0005 §7.4).
- [ ] `GET /health` still returns `{"status": "ok", ...}`; the action-loop endpoints
      still return the expected transitions — assert on response JSON via `TestClient`,
      not `$?` (regression that the swap left the router intact).

### 7.6 Eval strategy (ADR-010 T3)

- [ ] An eval harness exists under `tests/engine/eval/` with ≥1 golden-trace fixture
      (a recorded model output for a known event) and an assertion strategy that does
      **not** assume bit-identical output (e.g. schema-validity + required-field +
      handler-resolves invariants over the fixture set). The closeout states what
      "the tests still pass" means for a stochastic `recommend()` — documentary +
      behavioural. (If Cray prefers to defer the eval suite, that is recorded with
      rationale per ADR-010 T3 "scope it or explicitly defer".)

### 7.7 Project-wide invariants

- [ ] `ruff check services/` clean; `mypy --strict services/` clean — read the tools'
      own summary lines, not `$?`.
- [ ] `pytest` suite green — read pytest's `N passed` summary line.
- [ ] Coverage ≥70% on new `services/engine/llm/` code (`pytest --cov=services`) —
      **aspirational**, mirrors PLAN-0005 §7.7; surface the gap in closeout rather
      than block.
- [ ] PD-wording grep across new files returns **0** hits for design-partner
      identifiers — assert captured `grep -rilE` count is `0` (side-effect, not `$?`).

## 8. Surfaced decisions — adjudicated by Cray 2026-05-22

Each presented options + a recommendation. **All five were adjudicated by Cray on
2026-05-22** ("agree with Code's review recommendation"); each ruling is recorded
inline below as **→ Ruling**. The Phase-1 kickoff dispatch carries these rulings as
binding execution instructions.

### SD-1: `recommend()` async + retry budget

Two coupled sub-items.

- **async:** (a) **`async def recommend(...)`** — recommended; the sole caller is
  already async (§5), so it costs one `await` and is the natural fit for httpx I/O.
  (b) keep sync and drive the call with a sync httpx client / `asyncio.run` — avoids
  touching the signature literally but is awkward inside an async server and risks
  event-loop reentrancy. **Recommendation: (a).** *Cray adjudicates* (it is a literal
  deviation from ADR-010 D5 "same signature", though parameters + return type are
  preserved).
- **retry budget (ADR-010 D2 = "2–3"):** options 2 or 3. **Recommendation: 3** (1
  initial + 2 retries) — a small margin over the brief's "single retry closes the
  majority" while staying bounded. *Cray adjudicates.*

**→ Ruling (Cray, 2026-05-22):** **(a) `async def recommend(...)`** + **retry
budget 3** (1 initial + 2 retries). The async change is a one-`await` edit at the
sole caller (`services/api/routers/actions.py:55` — verified `async`); ADR-010 D5
"same signature" holds for parameters + return type, and the sync→async change is
the deliberate, minimal-blast-radius reading.

### SD-2: D3 hybrid trace — separate reasoning pass vs single-pass

(a) **Two-call Pattern B** — call 1 reasons (`think=true`), call 2 emits the
constrained envelope; richest separable trace, sidesteps the #15260 think/format
interaction by not combining them; costs a second call (latency/cost). (b)
**single constrained call** with a `reasoning_trace` field — one call, but collides
with the grammar-vs-thinking conflict (brief #3 §3.4) and yields a weaker trace.
**Recommendation: (a) two-call Pattern B**, as the briefs' §5 configs assume and as
IN-1 risk-management favours. *Cray adjudicates* (it is the latency/cost vs
trace-quality trade ADR-010 D2/Consequences flags).

**→ Ruling (Cray, 2026-05-22):** **(a) two-call Pattern B** — call 1 reasons
(`think=true`), call 2 emits the constrained envelope. Accepts the second-call
latency to sidestep the IN-1 `think`/`format` interaction.

### SD-3: model + Ollama version pin (IN-1)

The pin must be **verified** in Step 0, not assumed. Candidate configs (brief 3b
§3/§4/§5):

- (a) **gpt-oss-20b on Ollama 0.18+ (native gfx1151 ROCm)** — native structured
  output + function calling + separable reasoning trace; the one family that may
  collapse Pattern B cleanly. Recommended primary to verify first.
- (b) **Qwen3.5-35B-A3B** (hybrid `/think`) — strong tool-use, ~45–55 tok/s here.
- (c) **keep ADR-001 `gemma4:26b`** — continuity, but gemma4 is the model *named in
  the #15260 bug*; only viable if Step 0 verifies its `format` path. **Not
  recommended without that verification.**

**Recommendation: pin (a) gpt-oss-20b + Ollama ≥0.18 (ROCm), pending Step 0
confirmation; fall back to (b).** *Cray adjudicates* — and note this may amend the
ADR-001 baseline for the recommender path (a follow-on Code TODO if so).

**→ Ruling (Cray, 2026-05-22):** **(a) gpt-oss-20b + Ollama ≥0.18 (ROCm) as the
primary candidate, (b) Qwen3.5-35B-A3B as fallback — PROVISIONAL, gated by the
Step 0 verification on MS-S1 MAX.** (c) `gemma4:26b` is rejected for the
structuring call unless Step 0 proves its `format` path. **If the Step-0-verified
pin is not ADR-001's `gemma4:26b`, an ADR-001 amendment is a required follow-on
(Code TODO).**

### SD-4: structured-output library

(a) **raw Ollama `format`** + a hand-rolled retry loop — zero new dependency, full
control. (b) **Instructor over Ollama** — batteries-included validate-and-retry,
small dep, brief 3b §4.1 confirms support. (c) **Pydantic-AI** — heavier, agent-
framed. **Recommendation: (b) Instructor** for the retry ergonomics, *or* (a) if Cray
prefers to keep the dependency surface minimal (the loop is ~30 lines). *Cray
adjudicates* (dependency weight vs build cost).

**→ Ruling (Cray, 2026-05-22):** **(a) raw Ollama `format` + a hand-rolled
validate-and-retry loop — no new dependency.** Keeps the dependency surface minimal
(consistent with the project's stdlib-first tooling posture); the loop is ~30 lines.
`pyproject.toml` gains no Instructor / Pydantic-AI entry.

### SD-5: hosted Claude fallback — implement now vs seam-only

(a) **seam-only** — build a backend selector + settings flag; the hosted branch
raises `NotImplementedError`/returns to fail-safe until needed. Lowest scope; ADR-010
D1 calls it a *fallback*. (b) **implement now** — consent-gated, non-PII-only, behind
the selector. **Recommendation: (a) seam-only**, since the energy data is synthetic
and the local path is the moat; implement the hosted branch when local quality is
shown insufficient. *Cray adjudicates.*

**→ Ruling (Cray, 2026-05-22):** **(a) seam-only** — build the backend selector +
settings flag; the hosted Claude branch is stubbed (returns to fail-safe / raises
`NotImplementedError`) until local quality is shown insufficient on real data.

## 9. Steps (commit-sized, dog-foodable; mirror PLAN-0005's phased style)

> Worktree mode **ON** (multi-file buildable Python touching `services/engine/`,
> `services/engine/llm/`, `services/api/config.py`, tests) per CLAUDE.md §11 +
> Lesson #3; the kickoff dispatch carries the full pre-flight ownership/shell-guard
> sequence as commands. Each step is one commit unless noted.

### Step 0 — IN-1 verification spike (gate; no production code)
Pin the SD-3 model + Ollama version on MS-S1 MAX; run a throwaway script that sends
`format` = a small schema with and without `think`, and record whether the constraint
holds (the #15260 interaction). **Output: a written finding + the pinned config.**
This gates Step 3's structuring-call configuration. If the recommended pin fails,
fall to the SD-3 alternative before writing code.

### Step 1 — settings + LLM client skeleton
Extend `services/api/config.py::Settings` with the backend selector (SD-5), Ollama
base URL (default `http://ms-s1-max:11434`, ADR-002), model pin(s) (SD-3), retry
budget (SD-1), and timeout. Add `services/engine/llm/client.py` with an
`httpx.AsyncClient`-based Ollama chat wrapper (Pattern B capable). Unit-test the
client against a fake transport (no live network). *Commit.*

### Step 2 — prompt assembly + injection containment (IN-2)
Add `services/engine/llm/prompt.py`: build the system instruction + a delimited,
labelled untrusted-event-text section (§6.7). Unit-test that event free-text lands
only in the untrusted section and never in the system block. *Commit.*

### Step 3 — structured output: constrained gen + retry + semantic checks (D2)
Add `services/engine/llm/structured.py` (per SD-4): constrained generation against
`RecommendedAction.model_json_schema()`, the bounded validate-and-retry loop (SD-1
budget; validator error fed back as *labelled untrusted* context), and the §6.4
semantic checks (registry handler resolves, entity PKs, confidence range). Unit-test
each branch with a fake LLM (valid / malformed-then-valid / unregistered-handler).
*Commit.*

### Step 4 — hybrid reasoning trace (D3)
Assemble the trace per §6.5 (`llm_inference` model-asserted step labelled as such +
harness-emitted `ontology_query`/`rule_check` steps); set `actor_kind="llm"`; carry
`confidence` as advisory (IN-3). Unit-test trace shape + `actor_kind`. *Commit.*

### Step 5 — rewire `recommend()` + fail-safe (D5/IN-4)
Make `recommend()` LLM-backed (async per SD-1), composing Steps 1–4; **retain the
deterministic rule body** as the fail-safe; ensure no exception escapes (§6.6). Add
the one `await` at `services/api/routers/actions.py:55`. Unit-test the fail-safe
(forced client error → rule-path record, no raise). *Commit.*

### Step 6 — end-to-end + API regression
Wire/adjust the integration test so the full read → recommend (LLM, faked) → approve
→ execute loop is green and the persisted row reflects `executed`; assert `/health`
and the action endpoints still behave (§7.5). *Commit.*

### Step 7 — eval harness + golden traces (T3)
Add `tests/engine/eval/` with ≥1 golden-trace fixture and the non-bit-identical
invariant assertions (§7.6); document what "tests pass" means for a stochastic
`recommend()`. (If Cray defers the suite, record the deferral + rationale instead.)
*Commit.*

### Step 8 — invariants + close
`ruff` + `mypy --strict` + `pytest` green (read summary lines); coverage report;
PD-wording grep = 0. Closeout names the final module/endpoint set (mirror PLAN-0005
R4) and records the Step 0 IN-1 finding + the SD rulings as implemented. *Commit
(+ `docs(status)` housekeeping per the STATUS update workflow).*

## 10. Risks and known unknowns

- **R1 — IN-1 think/format bug (ADR-010 D2/IN-1; brief 3b §4.1).** If the pinned
  model silently drops the schema constraint, the structuring call emits
  unconstrained text. **Mitigation: Step 0 gate before any code; SD-3 alternative
  ready.** Highest-priority risk.
- **R2 — async signature change (SD-1).** If Cray rules sync, Step 5 needs a sync
  httpx path / `asyncio.run`, with event-loop care inside the async server.
  Resolve SD-1 before kickoff.
- **R3 — prompt injection via operational data (IN-2).** No full prevention;
  containment + human gate only (brief #3 §5.3). Regression trigger: untrusted event
  text reaching the system block — guarded by the Step 2 test.
- **R4 — trace faithfulness (D3).** Over-trust of the `llm_inference` narrative;
  labelling discipline is the mitigation (brief #3 §4.2). Surface in closeout.
- **R5 — eval non-determinism (T3).** A stochastic `recommend()` defeats bit-identical
  tests; the §7.6 invariant strategy is the mitigation. The unit suite stays
  deterministic by mocking the LLM.
- **R6 — latency/ops cost (ADR-010 Consequences).** Two-call Pattern B + retries cost
  more than the rule path; acceptable for a human-gated proposal but real. Surface
  measured latency in the Step 0 / closeout notes.
- **R7 — serving-path version sensitivity on gfx1151 (brief 3b §2.2).** Ollama
  ROCm/Vulkan behaviour is version-sensitive; the Step 0 pin records the working
  config. A deployment runbook is out of scope (§3.3) but flagged.

## 11. Verification

"Done" for PLAN-0006 means: all §7 acceptance checkboxes pass via Lesson #7 §3
reliable methods; the read → recommend(LLM) → approve → execute loop is green with
the LLM path faked; the fail-safe demonstrably falls back under induced LLM failure;
the Step 0 IN-1 finding is recorded and its config pinned; `ruff` / `mypy --strict`
/ `pytest` are clean (read from their own summary lines); and the closeout names the
final module/endpoint set and records how each SD was implemented. Per ADR-009 D2,
**Code** runs the verification and commits; Cowork holds no execution or commit
authority.

## 12. References

### Governing
- `docs/adr/0010-llm-reasoning-hook-surface.md` (D1–D5, IN-1..IN-4, T3 — authoritative)
- `docs/adr/0007-oct-engine-contracts.md` (D2 envelope UNCHANGED, D4)
- `docs/adr/0001-llm-model-baseline.md`, `docs/adr/0002-network-topology.md`
- `CLAUDE.md` §6 (Plan Flow), §8 (AI-assistive + data residency)

### Grounding research (Tier-0, gitignored working notes)
- `docs/research/private/2026-05-21-llm-reasoning-hook-design.md` (§3, §3.4, §4, §5, §6)
- `docs/research/private/2026-05-22-llm-reasoning-hook-local-models.md` (§2, §4.1, §5)

### Plans + lessons
- `docs/plans/done/0005-oct-engine-runtime-layer.md` (the runtime this swaps; depth/phrasing model)
- `docs/plans/0000-template.md` (PLAN doc shape)
- `docs/lessons/0007-harness-exit-code-artifact.md` (§3 reliable verification methods)
- `docs/lessons/0003-code-tab-worktree-lifecycle-traps.md` (worktree prevention checklist)

### Live-repo fact-pack (verified at authoring)
- `services/engine/recommender.py` (`recommend()`, `RULE_CONFIDENCE`, gate)
- `services/engine/actions.py` (envelope; `kind` + `actor_kind` enums)
- `services/engine/registry.py`, `services/engine/data_adapter.py`
- `services/api/routers/actions.py` (sole `recommend()` call site — line 55, async)
- `services/api/config.py` (Settings — LLM settings target)

### Dispatch
- `.claude/handoffs/session-10/2026-05-22-1900-code-plan0006-dispatch.md` (this plan's brief)

---

*PLAN-0006 — Draft authored by Cowork (Tier 0 + Tier 1 merged workspace) 2026-05-22
from the Code-drafted, Cray-routed dispatch. Status moves to Ready for execution on
Cray adjudication of §8 SD-1..SD-5 + Code commit. A Phase-1 kickoff dispatch follows
as a separate round.*

*AI-assisted per project convention.*
