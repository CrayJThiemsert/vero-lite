# PLAN-0119: Local model-serving policy — a five-class workload taxonomy, a per-call-site budget seam, and the sequenced experiments that fill it in

**Status:** Draft
**Owner:** both (Claude Code executes; Cray adjudicates the Surfaced Decisions and every live arm)
**Created:** 2026-09-03
**Revised:** 2026-09-03 (session 274) — nine Surfaced Decisions ruled by Cray (typed); three verified factual defects corrected inline and marked `was an error`; Step 3 concretised to the ruled seam; Step 4b added as the home of SD-4's redirect. Each SD keeps its original options / recommendation / *Why Cray's* prose as reasoning lineage and records the ruling beneath it.
**Related ADRs:** none yet — **SD-9 RULED (c), s274:** PLAN now, ADR later once the arms have filled in the numbers; Step 3 is **not** blocked awaiting an ADR. Touches ADR-001 (the CHECKPOINT-0 `think`/`format` contract), ADR-0030 D5 (never-raise advisory), ADR-0022/PLAN-0035 (the advisory verification judge).
**Predecessor:** [`PLAN-0118`](done/0118-intake-extraction-benchmark.md) (Complete 6/6) — the measurement this rests on. Record: `benchmarks/intake_extraction/RESULTS.md`.
**Lesson:** [`0049`](../lessons/0049-measure-generation-demand-not-the-cap-that-happens-to-work.md) — *measure generation demand; never search for the cap that happens to work.* That lesson is this PLAN's method, not a citation.

---

## Goal

Give vero-lite a **policy for managing local models that is keyed to the kind of work being asked of them**, so that every LLM call site declares its demand explicitly and is auditable against what the server actually did. Concretely: a **five-class workload taxonomy** (Gate · Structure · Judge · Narrate · Author), a **per-call-site budget seam** at the Ollama client — which does not exist today and is the root obstacle to every other item here — and a **sequenced, non-confounded experiment programme** that fills the taxonomy's numbers in from measurement rather than from a guess.

This is a **framework**, not a truncation bug fix. PLAN-0118 found one workload (intake) failing loudly. The same global cap sits under four other workload classes whose behaviour under it is unmeasured, one of which (`A Author`) is believed to be failing **silently**. The framework is what turns "we found a bug" into "we can say, for each part of the system, what it asks of a model and whether it got it."

---

## 1. The measured base (PLAN-0118, session 273)

Every figure below is from `benchmarks/intake_extraction/RESULTS.md`, which this drafter read. Two live runs on MS-S1, three arms (`gpt-oss:20b` shipped, `qwen3.8:27b-mtp-q4_K_M`, `qwen3.8:27b-mtp-q8_0`), 11 gold cases each.

**The structural finding — invariant across both runs, all three arms, two model families:**

| | attempts | empty | of those `done_reason="length"` | non-empty | of those `"stop"` |
|---|---|---|---|---|---|
| total | **66** | **45** | **45 / 45** | **21** | **21 / 21** |

`eval_count` on **every** empty attempt is **exactly 1024** — the configured `settings.llm_max_output_tokens`, sent as `num_predict`. Zero exceptions in 66 attempts.

**It is the call path, not the model.** Empty rates: gpt-oss **53%**, qwen-q4 **74%**, qwen-q8 **75%**. The two alternative models are *worse* on the same rails, which is what rules out a `gpt-oss` habit.

**Decode rates and cost.** 48.3 / 19.5 / 18.5 tok/s (derived from the known-1024 truncated calls). End-to-end on 11 cases: 7m14s / 21m21s / 23m28s. *(Drafter's check: those three sum to 52m03s; RESULTS.md records the three-arm window as 23:00:58 → 23:54:17 = 53m19s, leaving ~76 s for the three warms against the reported 5–6 s / 24 s / 46 s = 75 s. The figures reconcile.)*

**`eval_count` is correct** and counts the content segment: `content_chars / eval_count` = **2.71–3.47** across arms. An earlier write-up indicted the counter; **that indictment is withdrawn in RESULTS.md and must not be repeated here or anywhere downstream.**

**Two things are open and must never be written down as conclusions:**

- 🔴 **The residual contradiction.** `total_duration − eval_duration` is 0.04–2.47 s on truncated attempts but **10.4–54.4 s** on delivering ones (per-arm medians 18.2 / 47.2 / 50.8 s). Reconstructing that residual at each arm's decode rate puts a delivering call's *total* near **1,089–1,292 tokens — above the 1024 cap**, implying separate budgets. Against that: Ollama's `thinking/parser.go` is a **post-generation string splitter** (one stream, one `num_predict`), and Ollama issue **#17978** reports our exact envelope (`eval_count == num_predict`, `done_reason "length"`, empty content), which requires reasoning tokens to be *inside* `eval_count`. **Both cannot be right.** The residual also contains prefill and grammar-compilation time, so the reconstruction may be an artefact of attributing all of it to decoding. **Unresolved — OQ-1.**
- 🔴 **Reasoning length does not separate the two groups.** Truncated 3,295–4,513 chars (median 3,783); delivering 1,860–4,032 (median 3,133). **6 of 21** delivering attempts reasoned inside the truncated range. So "reasoning ate the budget" over-claims the mechanism, and *why* some calls fit is **open — OQ-2**.

**Run-to-run variance is real.** Same model, same config, same gold set, hours apart: direction 7/8 vs 6/8, empty 11/20 vs 10/19. n = 8 scored cases per arm. **No rate claim and no model ranking is supportable from this instrument.**

**One honest asymmetry, recorded as a hypothesis and never a pin.** Where a Qwen arm delivered, it scored 5/5 and 4/4 on all four axes *including* `band_compliance`, which `gpt-oss` fails systematically. In the baseline run four of the five `band_compliance` failures were the identical missing `site_role` (RESULTS.md Finding 2). So the Qwen models may follow instructions better when they speak, and speak far less often. **At n=8 that is not a ranking and this PLAN does not make one.**

---

## 2. The structural gap — there is no per-call seam

Verified on disk by this drafter:

- `services/engine/llm/client.py:335` sends `"num_predict": settings.llm_max_output_tokens` (**1024**) on **every** call.
- `client.py:349` sends `"keep_alive": settings.ollama_keep_alive`; `client.py:363` reads the in-flight cap from `settings.llm_max_inflight`. Both are read from settings **inside** `chat()`.
- `chat()` (`client.py:300-307`) takes only `messages`, `think`, `response_format`, `temperature`.

> ⚠️ **Correction to the dispatch fact-pack.** It cited `keep_alive` at `client.py:352`; on disk `keep_alive` is at **`:349`** and `:352` is `body["think"] = think`. The substance is unchanged.

**There is therefore no seam through which any call site can ask for a different budget.** This is a *structural* gap, not a tuning gap, and it is the root obstacle to every other item in this PLAN. The client's own comment argues the chokepoint position deliberately (`client.py:329-332`: *"Sits beside `temperature` rather than in a per-call argument for the same reason the in-flight cap is read here — eight call sites construct a client, and a bound that must be passed correctly at each of them is one forgotten argument from being off"*). That reasoning is sound about **forgetting** and is exactly why SD-1's design — recommended (b), and **ruled (b)** in s274 — keeps the chokepoint while making the *class* declarable at construction.

**`CallRole`** (`client.py:131`, `Literal["reasoning","structuring"]`) already exists but tags **metrics only** — it never sets a cap.

**`num_ctx` is never sent** — 0 hits repo-wide (verified). Context headroom is not binding today: the maximum `prompt_eval_count` on a truncated call is 741, so 741 + 1024 ≈ 1,765. **It would bind at cap 4096** if the server's effective `num_ctx` is 4096 (741 + 4096 = 4,837). The box reports a model `context_length` of 32768, but Ollama's *runtime* `num_ctx` default is a separate thing and is unmeasured here. **Raising the cap without also sending `num_ctx` risks silently truncating the prompt instead of the output — a strictly worse failure, because it is invisible in `done_reason`.**

**Accounting is nearly absent.** `call_metrics` is invoked at **two** production lines only — `structured.py:251` and `:265` (verified: those are the only two outside `client.py`'s own definition at `:235`). Twelve of the fourteen in-client call sites emit **no generation accounting at all**, so the audit surface needed to answer *"what does this call site actually demand"* does not exist for them.

**Timeout semantics bind every design.** `settings.llm_request_timeout_s = 120.0` (`config.py:163`), and a client timeout **aborts and discards every token produced** — the config docstring at `config.py:168-179` says so in as many words. Projections from the measured decode rates (arithmetic re-checked by this drafter): gpt-oss at 4096 ≈ **85 s** (fits); qwen at 2048 ≈ **105–111 s** (does not, once load and prefill are added). PLAN-0118 SD-5 already ruled the scoring semantics: a **validation exhaustion counts wrong and stays** in the denominator; a **transport error is unscored and leaves** it.

> **The binding consequence: raising a cap without raising the timeout converts truncations into strictly-worse aborts** — a graded wrong answer becomes an ungraded missing one. **Cap and timeout move together, always.**

**Dead and unwired config.** `ollama_default_model` (`gemma4:26b`, `config.py:132`) is referenced by nothing. `reasoning_mode` (`structured.py:42`, default `"full"`) sends `think` as a *boolean*, which `gpt-oss` ignores.

> ⚠️ **Correction to the dispatch fact-pack.** It states `reasoning_mode` has "no caller". On disk it has **no *production* caller**, but `benchmarks/procedure_baseline/harness.py:196,232,248,332,383,437` and `run_benchmark.py:119,165,558` *do* pass it, and `run_benchmark.py:686` (the `add_argument` call) exposes it as a **CLI flag** — `:546` merely *prints* `args.reasoning_mode`, and `:558` threads it into the harness. *(Citation `was an error`, corrected s274: the original draft cited `:546` as the flag here and again in SD-1; verified on disk, `:546` is the print line and `:686` is the `add_argument`. The substantive point is unaffected.)* This matters and is not a nitpick: **the repo already has working prior art for threading a per-call knob from a CLI down to `chat()`** — threaded as a parameter on the `generate_judgment` helper, not as an argument on `chat()`. SD-1 must weigh that precedent. `harness.py:273-282` additionally already implements *"the model did not honour the knob"* detection (it raises when `think_off` still returns thinking), which Step 5 reuses rather than reinvents.

---

## 3. The five-class taxonomy (the spine of this PLAN)

Each class declares: needs reasoning · structured or not · output size · latency budget · failure behaviour. **The numbers marked (unmeasured) are what the experiment programme fills in; they are not to be shipped as defaults before their step lands.**

| Class | What it is | Reasoning | Structured | Output size | Latency budget | Failure behaviour |
|---|---|---|---|---|---|---|
| **G Gate** | The PreToolUse classifier — a hook, **outside** this client | no | yes (tiny schema) | tens of tokens | **p95 ≤ ~25 s** (hard — a human is blocked) | **fails closed** (deny) |
| **S Structure** | intake, NL/run-corpus translate, procedure-draft classify + prose | incidental (the model reasons anyway) | yes | 300–800 tok *(measured content segment: 135–381)* | interactive, seconds | retry loop, then validation exhaustion = a wrong answer that **stays** in the denominator |
| **J Judge** | recommender (Pattern B), `action_step` Pattern B, action-verification | **yes, explicitly** | yes | **≥ 4096 needed** (Lesson 0049) | interactive-tolerant | recommender degrades to the deterministic floor; **`action_step` has no fallback — see D-1** |
| **N Narrate** | free prose phrasing; the gate-advisory narrative | no | **no** | small (1–2 sentences) | latency-dominated, user-facing | **already degrades well** — deterministic fallback + an explicit empty-content branch |
| **A Author** | `scaffold.py` synthetic dataset — the largest output in the system | no | yes | **largest in the system** (unmeasured) | **none — CLI batch** | falls back to the deterministic draft, **with no truncation disclosure — see D-2** |

### Call-site inventory (measured — 14 in-client sites, plus one outside)

Verified by grepping `\.chat\(` under `services/`. This table is itself an AC deliverable (AC-1) because no such inventory exists today.

| # | Site | Class | Live? | Accounting? |
|---|---|---|---|---|
| 1 | `run_query.py:511` | S | yes | no |
| 2 | `run_query.py:574` | N | yes | no |
| 3 | `nl_query.py:691` | S | yes | no |
| 4 | `nl_query.py:1225` | N | yes | no |
| 5 | `nl_query.py:678` | J (two_pass reasoning) | **no shipped caller** | no |
| 6 | `intake.py:182` | S | yes — **the measured one** | no (the *benchmark recorder* adds it) |
| 7 | `structured.py:245` | J (call 1, reasoning) | yes | **yes** (`:251`) |
| 8 | `structured.py:260` | J (call 2, structuring) | yes | **yes** (`:265`) |
| 9 | `pipeline.py:245` | S (classify) | yes | no |
| 10 | `pipeline.py:480` | S (prose) | yes | no |
| 11 | `pipeline.py:236` | J (two_pass reasoning) | **no shipped caller** | no |
| 12 | `action_verification.py:294` | J | **off by default** (`verification_judge_enabled=False`, `config.py:191-192`) | no |
| 13 | `action_step.py:422→432` (`generate_judgment`) | J | **stubbed in every vertical except procurement** | via `structured.py` |
| 14 | `scaffold.py:676` | A | yes (CLI) | no |
| — | `.claude/hooks/_sonnet_classifier.py:707-733` | **G** | yes | n/a |

**Liveness notes, verified — and one correction.**

- `action_step.py`'s Pattern B rides `client_factory=advisory_stub_factory` in **energy** (`procedures_factory.py:71`), **aquaculture** (`:77`), **building_materials** (`:107`), **fleet_maintenance** (`:114`), **supply_chain** (`:294`) and `scaffolder/package.py:369`. **Procurement is the exception** — it takes the factory as a **parameter** (`verticals/procurement/hero_demo/run.py:296`), so a caller can inject a live client.
- ⚠️ **Correction to the dispatch fact-pack.** It called `gate_advisory.py:160` *"dead everywhere"* because `GateAdvisoryBuilder(client_factory=…)` has zero hits. The narrow claim is right — **no construction anywhere passes `client_factory`**, so the **live arm** at `gate_advisory.py:156-175` is unreachable. But the **builder itself is live and shipping** at three production sites (`scaffolder/package.py:374`, `verticals/procurement/hero_demo/run.py:267`, `verticals/fleet_maintenance/procedures_factory.py:119`), all constructing `GateAdvisoryBuilder()` and taking the **deterministic** arm (`client_factory is not None` guard, `:156`). *"The class is live; its LLM arm is dead"* — the distinction matters, because wiring that arm is a one-argument change at a shipping site.
- ⚠️ **Two live call sites the fact-pack omits:** `nl_query.py:1225` and `run_query.py:574`. Both are **N Narrate**, both are on the **published demo's** headline surface, and both already carry a deterministic fallback **and** an explicit empty-content branch (`nl_query.py:1236`, `run_query.py:585`). They are the class most exposed to truncation and the class that handles it best — but the degrade is logged as *"returned empty content"* with **no `done_reason`**, so a truncation is indistinguishable from a model that chose silence. That is precisely the ambiguity `done_reason` exists to remove, and it makes these two branches the cheapest, most valuable place to prove the disclosure design (SD-8).

### The G Gate class has two backends, and only one is local

`.claude/hooks/_sonnet_classifier.py` is a whole workload **outside** `services/engine/llm/`. Verified: it calls Ollama directly with **no `num_predict` at all** (`:723` sends `"options": {"temperature": 0}` only), its own `keep_alive: "10m"` (`:724`) against the app's `"30m"`, and its own **75 s** timeout (`OLLAMA_TIMEOUT_SEC = 75`, `:93`). It also has an **API backend** — `DEFAULT_MODEL = "claude-sonnet-4-6"` with `API_TIMEOUT_SEC = 20` (`:83,:87`) — and its local model is `DEFAULT_OLLAMA_MODEL = "gpt-oss:20b"` (`:92`), *the same model the app's recommender uses*. Two `keep_alive` values that must agree but have no shared source are a defect waiting to happen, and two workloads contending for one resident model is a residency question (SD-5). G is also the **only** workload with a published eval (`benchmarks/stop_classifier/RESULTS.md`).

---

## 4. Two real defects this PLAN fixes

- **D-1 — `action_step` has no deterministic fallback.** `services/engine/procedures/action_step.py:432-434` calls `generate_judgment(...)` bare inside the `for entity in input_set:` loop (`:430`) with **no `try`/`except`** (verified: `execute()` at `:410-476` wraps nothing). **What actually happens on `OllamaError` / `StructuredOutputError` — corrected, s274:** the exception does **not** reach an unhandled 500. `services/engine/procedures/orchestrator.py:965` is the **only** `executor.execute(` call site in `services/` (verified by grep, s274), and `:973` — `except Exception as exc:  # fail-and-divert catches ANY step failure (D4)` — catches it and records a `StepResult` of `WAITING_HUMAN` (when `step.on_failure is ESCALATE_TO_HUMAN`) or `FAILED` (`:982`), with `_failure_trace_entry(exc)` producing `{"kind": "error", "summary": "OllamaError: ..."}` (`:792`). **The accurate defect is therefore: a failed step carrying a bare `error` trace and no judgment** — unlike the recommender's fail-safe (`services/engine/recommender.py:271`, `except Exception as exc:  # fail-safe must catch everything`, returning a *disclosed* deterministic answer at `:288`) and unlike the N-class sites, which both degrade *with an answer*. That is **quieter** than a 500 — nothing surfaces to a user, the run diverts, and the trace names an exception rather than a truncation — and so it is an arguably **stronger** argument for a deterministic fallback, not a weaker one. It is unreachable today **only because the stub is injected**; procurement's parameterised factory (`run.py:296`) is the hole. A truncation on that path is a silent divert, not a degrade.
  > ⚠️ **`was an error` (s274 revision).** The original draft said these exceptions *"propagate to an unhandled 500"* and that *"a truncation on that path is a 500, not a degrade"*. Verified on disk: the orchestrator's D4 fail-and-divert catches every step failure, so no 500 occurs. The original also cited `execute()` as `:410-434`; the span is `:410-476`. The *"wraps nothing"* substance holds. AC-6 and checklist item 7 are corrected to match.
- **D-2 — `scaffold.py:676` is a likely silent second victim.** It asks for an entire synthetic dataset — the largest output in the system — under the same 1024 cap. On truncation, `_parse_synthetic` fails, `llm_synthetic_or_none` (`:684-694`) catches **everything**, logs *"LLM synthetic draft unusable"* and returns the deterministic draft. **No `done_reason`, no truncation disclosure.** If this workload has been truncating all along, nothing on disk would say so. **Checkable offline** by capturing `done_reason` on the next scaffold run.

---

## Acceptance Criteria

Evidence discipline is CLAUDE.md §8 throughout: **every load-bearing green is witnessed RED** through `tools/probe_battery/` (never a from-scratch `/tmp` script), one mutation per assertion; every verification report **prints the values it measured** (`pre=N post=M`), never a bare PASS/FAIL.

- [ ] **AC-1 — The taxonomy and the call-site inventory are on disk and guarded.** §3's two tables ship in the repo, and a **guard test reads the artifact** (not its own constant) asserting every `.chat(` site under `services/` appears in the inventory with a class. Positive control: a newly added call site must redden it. *(Lesson: a committed-file guard is blind to new files unless it enumerates from the tree.)*
- [ ] **AC-2 — The instrument records what the residual question needs.** The benchmark recorder captures `load_duration_ns`, `prompt_eval_duration_ns` (both **already computed in `CallMetrics`**, `client.py:191-192`, and dropped today) and the **raw `thinking` string** — which `CallMetrics` does **not** carry: it has only `thinking_chars: int | None` (`:172`). The raw string is `ChatResult.thinking` (`client.py:122`), which the recorder already holds as `result` at `benchmarks/intake_extraction/run_benchmark.py:181`. Step 2 lifts the two durations off `CallMetrics` and the thinking off `ChatResult` — not all three off one record *(clarified s274; the original draft left the string's source unstated, which read as "also from `CallMetrics`" — `was an error`)*. The runner grows `--num-predict` and `--think` flags, which do not exist today. Witnessed RED by removing one captured field and seeing *that* assertion redden.
- [ ] **AC-3 — The budget seam exists and is exercised end-to-end.** Per SD-1's ruled design, (b) — a `Workload` declared at client construction, shape derived at the chokepoint (s274). **This AC is unchanged by the ruling.** A **scenario test drives the real producer into the real consumer** on realistic simulated data — a real call site through the real client into a transport double that **asserts the `num_predict` on the wire matches the class**. A test that stubs `chat()` itself does **not** satisfy this: it would agree with itself by construction and could not see the wire.
- [ ] **AC-4 — The budget rule is checkable, not aspirational.** `cap / decode_rate + load + prefill < timeout` is implemented as a function with unit tests, **including a case that fails** (qwen at 2048 against a 120 s timeout). A guard asserts **cap and timeout cannot be changed independently** — raising one without the other reddens.
- [ ] **AC-5 — `num_ctx` is sent whenever the cap exceeds the measured safe headroom**, with a test proving prompt + cap ≤ context. Positive control: a prompt large enough to breach must redden it.
- [ ] **AC-6 — D-1 is fixed.** `action_step` degrades deterministically on `OllamaError`/`StructuredOutputError` — with a disclosed judgment on the trace (SD-8 = (b)) — instead of letting the orchestrator's D4 fail-and-divert (`orchestrator.py:973`) record a `FAILED` / `WAITING_HUMAN` step carrying a bare `error` trace and no judgment (the corrected D-1; the draft's "instead of 500-ing" was `was an error`, s274). Witnessed RED by a fault-injecting double at the **procurement** parameterised seam — the one path where it is reachable.
- [ ] **AC-7 — D-2 is disclosed.** A truncated `A Author` call is **visible** on disk: `scaffold.py`'s fallback records `done_reason` rather than a bare *"unusable"*. Witnessed RED by a double returning `done_reason="length"` with empty content.
- [ ] **AC-8 — The decision checklist ships** (§ *Decision checklist for a new call site*) and a new call site cannot be added without answering it — enforced by AC-1's guard, not by convention alone.
- [ ] **AC-9 — Offline gates at their true CI scope:** full `mypy services/`, full `tests/`, bare `ruff check .` (**never** `ruff check <paths>`, which bypasses `exclude`).
- [ ] **AC-10 — Every live arm is separately CLAUDE.md §8-gated** with its own typed Cray go, its own pre-committed pass/fail read fixed **before** the run, and **exactly one intervention per arm** (§ *Experiment sequencing*). A run that changes two variables is void by construction, not merely weak.
- [ ] **AC-11 — The `CallMetrics` docstring is corrected at the source.** `client.py:156-158` reads *"`eval_count` is generated tokens — the model's actual DEMAND, which is what a cap should be chosen from."* On PLAN-0118's evidence it is the **content segment's** tokens, so sizing a whole-call budget from it under-counts by whatever the reasoning pass costs. Sharpen the wording where it is read, not only in a PLAN.

---

## Out of Scope

- ❌ **Any model ranking.** n=8 scored per arm, with measured run-to-run variance at exactly that magnitude. This PLAN does not rank `gpt-oss` against Qwen and does not adopt a Qwen arm.
- ❌ **Any accuracy claim from this instrument.** The intake lane is a BEFORE/AFTER *truncation* instrument. It is not an accuracy oracle, and its fractions are not rates.
- ❌ **Fixing the `band_compliance` gap.** RESULTS.md Finding 2 localises it (four of five baseline failures = zero `site_role` properties); it does not diagnose prompt vs schema. Separate PLAN.
- ❌ **Any injection-resistance rate.** n=1 judged. A rate needs the dedicated injection lane PLAN-0118 SD-3 contemplated.
- ❌ **Any conclusion on the contested residual (OQ-1) until it is measured.** Nothing in this PLAN may be built on the ~1,089–1,292-token reconstruction.
- ❌ **Migrating the serving stack.** SD-7 frames the option space and names its evidence needs; it does not migrate — **RULED (a), s274: stay on Ollama now**, with an active watch on the capability gap. No stack change happens under this PLAN.
- ❌ **Prompt engineering.** Changing a prompt changes the demand, which would confound every arm below.
- ❌ **Retiring `ollama_default_model` / `reasoning_mode`.** Noted as unwired; removal is a separate `chore/*`.

---

## Steps

### Experiment sequencing (binding)

**Repair the instrument offline first → characterise the timeout empirically, one model resident at a time (Step 4b, added s274) → raise the timeout ALONE, to the measured number → then the cap on gpt-oss ALONE → then `think:"low"` → then Pattern B. Never two interventions in one arm.** Each live step is its own §8 go with its own pre-committed read. A step whose predecessor has not landed does not run. Step 4b is a *measurement*, not an intervention — it changes no configuration, so it does not consume the one-intervention slot — but it is live and §8-gated like every other live step (its go is the one Cray pre-approved under SD-4, scoped to it alone).

### Step 1 — Record the taxonomy and the inventory (offline, no code)
Ship §3's tables plus the decision checklist. Land AC-1's guard test. Unblocks nothing else — do it first so every later step has a place to write its numbers.

### Step 2 — Repair the instrument (offline)
AC-2. Capture `load_duration_ns`, `prompt_eval_duration_ns` — **from `CallMetrics`** (`client.py:191-192`) — and the raw `thinking` string — **from `ChatResult.thinking`** (`client.py:122`), which the recorder already holds as `result` (`run_benchmark.py:181`); `CallMetrics` carries only `thinking_chars` (`:172`), so the three values do not come off one record (clarified s274). Add `--num-predict` / `--think`. **This is the step that makes OQ-1 answerable**: without a prefill rate the budget rule of AC-4 is not evaluable, because `prefill` is currently an unmeasured term. It is offline work on the existing seam — no MS-S1 contact.

### Step 3 — Build the seam (offline)
Per **SD-1 = (b)** and **SD-3 = (b)** (both RULED, s274). Land AC-3, AC-4, AC-5, AC-8, AC-11. **Ship it with every class set to today's 1024** — a pure refactor with no behaviour change, so its own correctness is provable offline and the later arms measure one thing each. Resist the urge to bundle a new default here; that is the confound the sequencing rule exists to prevent. **Not blocked on an ADR** (SD-9 = (c)).

**The ruled design, concretely:**
- **The seam is a `Workload` literal declared at client construction** — a constructor argument on `OllamaClient`, set in each `client_factory` — **not** a `chat()` keyword. `chat()`'s signature (`client.py:300-307`) is untouched, so the `ChatClient` Protocols (`structured.py:65-72`, `intake.py:43`) and every test double are untouched.
- **The call shape is derived at the chokepoint** (`client.py:329-335`, where `num_predict` is set today) from what is already visible there: a `response_format` present ⟹ structuring pass; `think` set with no `response_format` ⟹ reasoning pass. Pattern B's two calls (`structured.py:245`, `:260`) are told apart without any new argument.
- **A per-model capacity clamp** sits beside it, keyed on `self._model` (assigned `client.py:291`, exposed `:295-298`) — the class asks for a budget, the clamp bounds it to what the bound model has a *measured* capacity for, and a clamp that fires is disclosed on the trace (SD-8 = (b)). An unlisted model **refuses at construction** (SD-2 = (b), app side).
- **Type-error enforcement lands at the constructor:** the `Workload` argument has **no default** (SD-3 = (b)); constructing a client without one is a `mypy` error at full `services/` scope. The migration is the set of **client-construction sites**, not the 14 call sites of §3's inventory, and it touches zero doubles (they implement the Protocol; they never construct `OllamaClient`).

**Pre-committed count — retained, re-scoped under (b).** The original draft's instruction that Step 3 *re-derives the exact figure with a scripted count as its pre-committed number* is **retained**, but the figure that matters is now the number of **client-construction sites** (the client's own comment says eight — `client.py:329-332` — which is the *only* on-disk figure and is itself unverified by count), because that is what the constructor-level type error enumerates. For reference only: a scripted count by the reviewing agent (s274) found **58** `async def chat(` definitions in source — 51 in `tests/`, 4 in `services/`, 2 in `benchmarks/`, 1 in `verticals/` — of which 57 are keyword-only with no `**kwargs`; the original draft's own check said 61. Both figures are **measured-by-review, not the pre-committed number**: under (b) they are the blast radius Step 3 *avoids*, not the one it pays. Step 3's own scripted count of constructor sites is what its verification report prints — `pre=N` constructions lacking a `Workload` before the migration, `post=0` after — witnessed RED by adding one undeclared construction and seeing `mypy` redden on *that* line.

**Open implementation question — not ruled (SD-1.1 below).** Where one constructed client serves call sites of *two* classes (candidate: `nl_query.py:691` S and `nl_query.py:1225` N, *if* they share a client — Step 3 checks), a constructor-level `Workload` cannot tell them apart, and the chokepoint's shape derivation separates reasoning from structuring, not S from N. Step 3 either constructs one client per class in the factory or surfaces the case to Cray; it must **not** quietly widen `Workload` into a per-call argument, because that is the (a) design SD-1 ruled against.

**AC-3 is unchanged by the ruling:** the scenario test still drives a real call site through the real client into a transport double that asserts the wire `num_predict` matches the class.

### Step 4 — Fix D-1 and D-2 (offline)
AC-6, AC-7. Independent of the live programme; do them while waiting for a §8 go.

### Step 4b — LIVE: characterise the timeout (added s274 — the home of SD-4's redirect)
Establish **min / max / default timeout empirically** for the current ecosystem across the three named models — `gpt-oss:20b`, `qwen3.8:27b-mtp-q4_K_M`, `qwen3.8:27b-mtp-q8_0` — with **strictly one model resident at a time** (SD-5's amendment; enforced via `keep_alive` plus an explicit unload between arms, **not** `llm_max_inflight` — see SD-5's mechanism note), on the repaired instrument (Step 2) so `load_duration` / `prompt_eval_duration` / `eval_duration` are recorded per call and `prefill` stops being an unmeasured term. **§8 go: approved in advance by Cray (typed, s274) for exactly this experiment** — scope as recorded under SD-4; it still requires a **pre-committed pass/fail read fixed before the run**, still minimises live runs, and the offline oracle is still the gate. What it feeds: Step 5's target timeout (a timeout cannot be "raised" to a number nobody has measured), AC-4's `cap / decode_rate + load + prefill < timeout` rule with measured `load` and `prefill` terms, and SD-4's deferred retry decision. **Design points not ruled** (fixed in the pre-committed read, never improvised at run time): at which `num_predict` the characterisation runs — the timeout a cap needs scales with the cap, so a 1024-only measurement does not bound Step 6's 4096 arm; the prompt set (the intake gold set keeps it comparable with PLAN-0118); and what *"default"* means operationally — the drafter's proposal is the p95 of `total_duration` across arms plus a stated margin, offered for Cray to ratify with the read (SD-4.1 below). Placement before Step 5 is the drafter's sequencing proposal, not a ruling.

### Step 5 — LIVE ARM A: raise the timeout **alone** — to Step 4b's measured number
`llm_request_timeout_s` up to the value Step 4b measured, cap unchanged at 1024. **Pre-committed read:** the empty-body fraction should be **unchanged** (truncation is a cap phenomenon, not a deadline one). If it moves, the model of the failure is wrong and the programme stops for re-analysis. This arm exists to buy headroom for Arm B and to falsify a lurking deadline effect — a null result is the expected, informative outcome.

### Step 6 — LIVE ARM B: raise the cap on **gpt-oss alone**, to 4096
Cap 4096, timeout already raised in Arm A. Projected decode 85 s at 48.3 tok/s. **`num_ctx` must be sent** (AC-5) — otherwise a 741-token prompt plus a 4096 cap breaches a 4096 default context and the failure moves somewhere invisible. **Pre-committed read:** `done_reason="length"` fraction falls materially; **any** `"length"` that remains is reported, not rounded away. Answers OQ-3 (does raising the cap alone suffice — untested today).

### Step 7 — LIVE ARM C: `think: "low"`
Only after Arm B. Effort levels are model-dependent and Ollama issue **#17785** measured no consistent effect on one family, so **this arm's honest expected outcome is "no effect"** — which is worth knowing and cheap once the instrument is repaired. Reuse `harness.py:273-282`'s existing *"the model did not honour the knob"* detection rather than writing a new one. **`think: false` is not a lever** — Ollama **#18044**: it disables the thinking *parser*, not the thinking *generation*, with `eval_count` unchanged. Do not test it.

### Step 8 — LIVE ARM D: Pattern B for intake
Give the reasoning pass its own budget by splitting intake into the two-call shape `structured.py` already runs. This is the design PLAN-0118's addendum commissions. It is last because it is the largest change and because Arms A–C may make it unnecessary — **and if OQ-1 resolves toward a single shared budget, Pattern B becomes the *only* fix that can work, since no single-call cap can separate the two channels.**

### Step 9 — Reconcile the G Gate workload (offline)
One shared source for `keep_alive`; a `num_predict` for the classifier's local arm; the residency question (SD-5) recorded against the fact that the classifier and the recommender want the **same** model resident.

### Step 10 — Re-run the intake lane as the AFTER instrument
Same gold set, same seam, same shipped config except the one ratified change. Report raw fractions only. **Comparability is the whole point of having kept PLAN-0118's baseline** — a run that changes the gold set or the seam is not an AFTER.

---

## Decision checklist for a new call site

Answered **in the PR that adds it**; AC-1's guard fails a site that skips it.

1. **Which class?** G / S / J / N / A. If none fits, the taxonomy is wrong — say so rather than forcing a fit.
2. **Does it need reasoning?** If yes, it is J, and a single-call constrained shape is a **known** failure mode (45/45).
3. **Structured?** If yes, note that schema masking is deferred until the end-of-thinking token — this is *why* a reasoning pass runs unconstrained.
4. **Expected output size**, and **how it was obtained** — measured `eval_count`, or a stated estimate marked as such.
5. **Latency budget**, and whether a human is blocked.
6. **Does `cap / decode_rate + load + prefill < timeout` hold** at the target model's measured decode rate? Show the arithmetic.
7. **Failure behaviour on truncation:** degrade, retry, fail closed, 500, or a bare error. **Neither "500" nor "a bare `error` trace with no judgment" is an acceptable answer** — the second is what D-1 actually is (corrected s274), and it is the quieter of the two.
8. **Is the truncation visible?** Is `done_reason` captured, and does the degrade path record it?
9. **Which model, and is it resident?** A cold load is 5–46 s depending on the arm (measured), against the latency budget in (5).

---

## Surfaced Decisions

Each carries options, a recommendation with a one-line reason, and why it is Cray's call rather than Code's. **All nine were ruled by Cray (typed, session 274, 2026-09-03).** Each SD records its ruling in a `RULING` block beneath the original prose, which is kept intact as the reasoning lineage — the alternatives are never deleted. One (SD-4) was not ruled among its options but **redirected** into a measurement prerequisite; where a ruling leaves something open, the block says so, and the follow-ups a ruling created are collected at the end of this section as SD-*n*.1 items, **not ruled**. *(The original draft read "None of these is decided by this draft" — superseded by the s274 rulings.)*

### SD-1 — The budget seam design
**Options.** **(a)** A `budget=` keyword on `chat()`. Explicit and legible at the call site; demand is auditable by reading the call. Blast radius: the dispatch measured **~42** existing test doubles that are keyword-only with no `**kwargs`, **plus** the `ChatClient` **Protocol** definitions (`structured.py:65-72`, `intake.py:43`) and the production stub clients (`advisory_stub.py:71`, `verticals/procurement/hero_demo/run.py:105`, two benchmark harnesses). *(Drafter's independent check: **61** `async def chat(` definitions exist repo-wide, of which at least 7 already accept `**kwargs`. That is consistent with ~42 keyword-only test doubles; **Step 3 re-derives the exact figure with a scripted count as its pre-committed number** rather than inheriting it.)*
**(b)** A **`Workload` literal on the client** (set at construction / in the `client_factory`), with the call *shape* — reasoning pass vs structuring pass — derived at the chokepoint from `response_format`/`think`, plus a **per-model capacity clamp**. **Zero test-double blast radius**, because doubles implement the Protocol and never construct `OllamaClient`.
**(c)** A settings-keyed table (`llm_budgets: dict[workload, int]`) with the workload passed per call — a hybrid inheriting (a)'s blast radius.
**Recommendation: (b)** — it is the only option that adds the knob without touching ~42 doubles and two Protocols, it preserves the client's own "one chokepoint cannot be bypassed" argument (`client.py:329-332,356-359`), the per-model clamp needs the model which only the client owns, and Pattern B's two calls are distinguished exactly where `think`/`response_format` are already visible.
**Honest counter, because it cuts against the recommendation:** (a) makes each site's demand readable *at the site*, which is closer to this PLAN's stated goal of explicit per-site demand; under (b) you must trace a factory to learn a call's budget. And the repo already has working per-call threading prior art (`reasoning_mode` through `generate_judgment`, with a CLI flag at `run_benchmark.py:686` — *corrected s274 from `:546`, the print line*) — so (a) is not unprecedented here.
**Why Cray's:** it trades **auditability-at-the-call-site** against **~42 files of churn plus two Protocol changes**. That is a taste-and-cost judgment about the codebase's future readers, not a correctness question.

**RULING (Cray, typed, 2026-09-03, s274): (b).** A `Workload` literal on the client, set at construction / in the `client_factory`; the call *shape* (reasoning pass vs structuring pass) derived at the chokepoint from `response_format`/`think`; plus a per-model capacity clamp. Zero test-double blast radius. **Basis as accepted** — two reasons, offered to Cray by the reviewing agent and accepted. They **differ from the drafter's original emphasis on labour cost** (~42 files), and both are recorded because the reason a ruling rests on is what a future revisit must re-examine:
1. **Reversal cost is asymmetric.** (b)→(a) later is **additive** — an optional per-call override layered on a client-level default, no doubles touched. (a)→(b) later requires *removing* an argument from ~41 files. Starting at (b) preserves the option; starting at (a) does not.
2. **The per-model clamp needs the model, and only the client owns it** (`self._model`, assigned `client.py:291`, exposed via the `model` property `:295-298`). A call site asking for 4096 cannot know whether the bound model can deliver it, so the clamp logic lands at the client under *either* option — (b) simply co-locates the class with the thing the clamp already needs.

**Accepted cost, recorded in substance:** under (b) a reader cannot learn a call's budget at the call site and must trace a factory. That **cuts against this PLAN's own stated goal of explicit per-site demand**, and it grows more expensive as more people read the code. Cray accepted that cost knowingly; it is the first thing to revisit if the additive (b)→(a) override is ever wanted. **Consequence:** Step 3 declares the seam at construction and enforces it at the constructor — see Step 3 and SD-3's interaction note. One implementation question this leaves open is SD-1.1 (a client shared by two classes).

### SD-2 — An unlisted model: fail closed, or refuse?
**Options.** (a) **Fail closed** — an unknown model gets the most conservative budget and logs. (b) **Refuse** — raise at construction; an unlisted model cannot be used until someone adds its measured capacity.
**Recommendation: (b) refuse, for the app; (a) fail closed, for the G Gate hook** — because a refusal in a PreToolUse hook blocks a human at the keyboard, while a refusal in the app surfaces at wiring time where it is cheap.
**Why Cray's:** (b) means adding a model requires a measurement first, which is either the discipline this whole PLAN is for or an unacceptable friction on experimentation. That is a workflow preference.

**RULING (Cray, typed, 2026-09-03, s274): (b) refuse — for the app.** Cray's stated reason, *"น่าจะเป็นจังหวะที่ดี"*, is recorded as a **timing / discipline judgment**: adding a model should require a measurement first, and now — while the seam is being built — is the moment to install that discipline. **The hook side is not contradicted by this ruling.** The drafter's split recommendation — (a) fail closed for the G Gate hook, because a refusal in a PreToolUse hook blocks a human at the keyboard — stands as the **hook-side reading**, marked as such: the ruling was typed for the app's client, and the G Gate hook (`.claude/hooks/_sonnet_classifier.py`) sits outside that client. The hook side therefore remains at recommendation status, not ruling status; Step 9 records whichever applies once it is typed.

### SD-3 — Is `"unspecified"` a permitted default, or a type error?
**Options.** (a) Permitted, mapping to today's 1024 — every existing call site keeps working untouched. (b) A **type error** — every call site must name its class; the type checker enumerates the work.
**Recommendation: (b)**, because a permitted default is *exactly* how the current global cap became invisible: 12 of 14 sites inherited it and nobody had to look. `mypy services/` at full scope turns the migration into a finite, enumerable list.
**Why Cray's:** (b) front-loads the whole inventory into one PR instead of allowing incremental adoption. That is a sequencing call with real schedule cost.

**RULING (Cray, typed, 2026-09-03, s274): (b) — a type error.** Every call site must name its class; `mypy services/` at full scope enumerates the migration.
🔴 **Interaction with SD-1 = (b), recorded explicitly.** Under SD-1 = (b) the `Workload` is declared at **construction**, so the enforcement point is the **constructor**, not the call. SD-3 = (b) therefore means: **constructing a client without a declared `Workload` is a type error.** What that enumerates is the **~8 client-construction sites** (the client's own comment, `client.py:329-332`: *"eight call sites construct a client"* — Step 3 re-derives the exact count as its pre-committed number), **not** the 14 call sites in §3's inventory — and it touches **zero** test doubles, because doubles implement the `ChatClient` Protocol (`structured.py:65-72`, `intake.py:43`) and never construct `OllamaClient`. The *"front-loads the whole inventory into one PR"* schedule cost above is correspondingly smaller than the draft estimated. The 14-site inventory still ships under AC-1 as the documented class of each *site*; the type checker enforces the class at the constructors that bind a client to it.

### SD-4 — Escalate on truncation: once, or not at all?
**Options.** (a) **Not at all** — a truncation is a wrong answer; disclose and move on. (b) **Retry once at a higher cap**, then give up. (c) Retry at the same cap (today's behaviour — the intake retry loop, which rescued 5 of 7 empty-first cases and never recovered 2).
**Recommendation: (a) not at all, for now.** An escalating retry doubles the worst-case latency against a **120 s timeout that aborts and discards everything**, and PLAN-0118 showed the retry loop's own error message (*"output was not valid JSON"*) misattributed the failure for an entire benchmark run. Fix the visibility before adding a rescue on top of it.
**Why Cray's:** (b) is a real availability/latency trade on a **user-facing** surface, and the published demo's tolerance for a slow answer versus a disclosed degrade is a product judgment.

**RULING (Cray, typed, 2026-09-03, s274): NOT ruled among (a)/(b)/(c) — REDIRECTED into a measurement prerequisite.** Cray's ruling: the **120 s timeout may itself be wrong**, and a retry decision made against a possibly-wrong timeout would inherit the error. Before deciding retry-on-truncation, **run an experiment to establish the min / max / default timeout empirically** for the current ecosystem, across all three models of interest on MS-S1 — `gpt-oss:20b`, `qwen3.8:27b-mtp-q4_K_M`, `qwen3.8:27b-mtp-q8_0`. **The retry question is deferred until those numbers exist.** The drafter's recommendation (a) stays on record as the recommendation, not as a ruling; nothing in this PLAN may treat SD-4 as settled.

**A scoped CLAUDE.md §8 go is APPROVED IN ADVANCE by Cray (typed, s274) — for exactly this experiment, and nothing else.** Scope, recorded precisely so it cannot be read as blanket:
- **Covers:** the timeout-characterisation runs on those **three named models** only.
- **Binds:** each arm live with **strictly one model resident at a time** (the SD-5 amendment); a **pre-committed pass/fail read fixed BEFORE the run**; *"minimize live runs"* still applies; the **offline oracle is still the gate** — a live run is evidence, not a CI gate.
- **Does NOT cover:** any other live arm in this PLAN — Step 5 (timeout alone), Step 6 (cap on gpt-oss), Step 7, Step 8, Step 10 — each of which still needs **its own typed go** (AC-10 is unchanged).

**Consequence for the programme:** the experiment is homed as **Step 4b**, sequenced before Step 5 (a timeout cannot be raised to a number nobody has measured) — placement is the drafter's proposal, SD-4.1. OQ-3's answer now depends on it, and OQ-9 is created to hold the measurement itself.

### SD-5 — Per-model `keep_alive` and residency
**Facts.** Observed VRAM: gpt-oss 12.15 GiB, qwen-q4 16.32, qwen-q8 27.12; **two fit at 44.7%** of the ~63.65 GiB allocated; loading a third made Ollama **evict the others itself**. Warm times 5–6 s / 24 s / 46 s. The app sends `"30m"`; the classifier hook sends `"10m"`; **both want `gpt-oss:20b` resident**.
**Options.** (a) One global `keep_alive` from a single source (the current app value), hook included. (b) Per-class `keep_alive` — long for G (a blocked human), short for A (batch, no latency budget). (c) Pin a residency set of at most two models explicitly.
**Recommendation: (a) + (c)** — one source removes the two-values-that-must-agree defect, and an explicit two-model residency set matches the measured eviction behaviour instead of discovering it.
**Why Cray's:** (c) allocates a scarce shared host resource across two workloads (the harness's own gate, and the product) whose relative priority is a business call.

**RULING (Cray, typed, 2026-09-03, s274): (a) + (c), as recommended — WITH an amendment.** One global `keep_alive` from a single source (hook included), plus an explicit residency set of **at most two** models. **Cray's amendment:** during model-comparison / benchmark runs, residency is restricted to **strictly one live model at a time**, to keep measurements clean — no second resident model contending for VRAM bandwidth or decode throughput, and no ambiguity about which model's warm a `load_duration` belongs to. The two-model set is the *product* posture; the one-model rule is the *measurement* posture, and every live step in this PLAN (4b, 5–8, 10) runs under the measurement posture.
🔴 **Mechanism note (measured by the reviewing agent, s274): `llm_max_inflight` CANNOT implement that amendment.** `_inflight_slot` (`client.py:93-108`) caps **concurrent calls per process** — `_inflight` is a module-level global (`global _inflight`, `:98`) — whereas residency is **models resident in the server's VRAM**, a property of the Ollama server, not of any client process. A process-wide in-flight cap of 1 says nothing about how many models the server keeps loaded. **Benchmark isolation must therefore be enforced via `keep_alive` plus an explicit unload between arms** — and *verified* by reading the server's loaded-model list before the next arm starts (mechanics live in the `ms-s1-ollama` skill, not here) — **not** via the in-flight cap. Each live arm's verification report prints the resident-model list as `pre=` / `post=` values, so a second resident model reddens the arm instead of silently contaminating it.

### SD-6 — Should `llm_max_inflight` be pinned to 1?
**Fact:** default is **0 = unlimited** (`config.py:330-340`), and the docstring already records *"Published demo pins 1"* — so the published posture is pinned; the question is the **default**.
**Options.** (a) Leave 0. (b) Pin 1 everywhere. (c) Pin 1 for dev/CI, leave the published override as-is.
**Recommendation: (b)**, because concurrent generations on one box contend for the same VRAM and the same decode throughput, which would make every latency figure in this PLAN's programme unreproducible — and reproducibility is the point of the programme.
**Why Cray's:** the config comment explicitly says *"If Cray meant 1 everywhere, this default is the one line to change"* — it is a decision already reserved to Cray in writing.

**RULING (Cray, typed, 2026-09-03, s274): (b) for dev/CI; (a) for demo/production.** Neither the drafter's (b)-everywhere nor option (c): it is (c)'s **mirror image** — the *default* becomes the pin and the *published demo* becomes the unlimited one. Mechanics as dispatched: `llm_max_inflight` default **0 → 1** in `services/api/config.py` (`:330-340`), AND the pin **REMOVED** from all three published profiles — `deploy/published/oct-energy/published.env:78`, `deploy/published/oct-fleet-maintenance/published.env:125`, `deploy/published/oct-procurement/published.env:93` — each currently `LLM_MAX_INFLIGHT=1` (verified on disk, s274).
> ⚠️ **Drafter's mechanics check (s274) — a question about the mechanic, not a re-ruling.** With the default raised to 1, *removing* the published pin leaves the demo at **1**, not unlimited — an absent env var means the Field default applies. For the demo to actually run (a) = unlimited, the three published profiles need an **explicit `LLM_MAX_INFLIGHT=0`**, not an absent line. The ruling's *intent* — dev/CI pinned, demo/production unlimited — is binding as typed.
>
> ✅ **SD-6.1 RULED (Cray, typed, 2026-09-03, s274): the explicit `LLM_MAX_INFLIGHT=0`.** The three published profiles carry the line rather than losing it. **The dispatched "remove the pin" mechanic was Code's error** — it would have realised (b)-everywhere by accident, the opposite of the ruling; the drafter caught it before any file changed. Under this mechanic the Field's `description` (*"Published demo pins 1"*, `config.py:338`) and the comment above it (*"If Cray meant 1 everywhere…"*, `:328-329`) become **false** and are rewritten in the PR that carries the change.
>
> 🔴 **Not carried by this PR.** This PLAN edit records decisions; the `config.py` default and the three `published.env` lines are a **behaviour change on the live published demo** and land with their owning implementation step, under an AC and the full `tests/` run — never in a docs-only PR with no oracle.

🔴 **This INVERTS the shipped posture — recorded as knowingly accepted, not as drift.** It is a deliberate behaviour change on the **published, customer-facing demo**. The risk being accepted, in the config's own words (`config.py:334-338`): over the cap a request fails fast to the deterministic arm *"rather than queueing — a visitor waiting behind someone else's generation experiences a hang, which is what the cap exists to prevent"*. Removing the production pin **re-admits that hang**: two concurrent visitors on the published demo contend for one box's VRAM and decode throughput, and the second waits instead of being answered deterministically. **The reviewing agent raised this conflict, with that evidence, before the ruling; Cray reaffirmed the literal reading.** The reason typed for the dev/CI side is the recommendation's own (every latency figure in this programme must be reproducible); no reason was typed for the demo side beyond the reaffirmation, and none is invented here.
**Implementer's note:** `_inflight_slot` (`client.py:93-108`) **refuses** rather than queues — over the cap it raises `OllamaBusyError` (`:99-103`). Pinning dev/CI to 1 therefore makes any *genuinely concurrent* LLM call in a test raise `OllamaBusyError` and take the deterministic arm; a test that expects two live generations in flight changes behaviour and must be found by the full `tests/` run (AC-9), not assumed absent. The intake benchmark runner is **serial**, so it is unaffected.

### SD-7 — Should we move off Ollama to llama.cpp or vLLM?
**The constraint, verbatim:** *"we still want to stand on Windows to the last possible moment in this development phase; we accept that we may have to move to Linux when we reach the production phase."*
**What forces the question:** only llama.cpp and vLLM expose a reasoning budget. **llama.cpp** documents `--reasoning-budget` (*"-1 unrestricted, 0 immediate end, N>0 token budget"*) and `--reasoning-format`. **vLLM** documents `thinking_token_budget`, which **forces the reasoning block closed** rather than truncating — *strictly better than a cap, because it guarantees a content channel survives* — plus `--structured-outputs-config.enable_in_reasoning`. **Ollama has no separate thinking budget**: PR **#17566** (*"there is currently no way to say 'think, but not forever'"*) is **unmerged**.
**Host facts:** MS-S1 MAX runs **Windows** (the remote shell is PowerShell; Windows services, scheduled tasks, event logs — `.claude/skills/ms-s1-admin/`), AMD Ryzen AI Max+ 395, ROCm gfx1151, ~63.65 GiB allocated of 128 GB, `context_length` 32768.
**Options.** (a) **Stay on Ollama**, work within cap + Pattern B; revisit if #17566 merges. (b) **Move to llama.cpp**. (c) **Move to vLLM**. (d) **Hybrid** — Ollama for G/N/S, a reasoning-budget server for J/A only.
**Recommendation: (a) now, with (b) as the pre-scoped fallback — and explicitly contingent on evidence this PLAN does not yet have.** Reason: Pattern B (Step 8) obtains a *per-channel* budget **without any stack change**, and `structured.py` already ships it — so the cheapest path to the actual goal does not require the migration at all. **⚠️ Marked as Code's inference, not a fact:** llama.cpp ships Windows builds and is, of the three, the only one that plausibly keeps the Windows constraint *and* gains a reasoning budget; vLLM is Linux-first and would force the Linux move early. **This is the option space with its evidence needs, not an assertion.**
**Evidence this SD needs before it can be decided:** (i) does Ollama pass `--reasoning-budget` down to its bundled llama-server (**OQ-4** — currently unknown); (ii) does llama.cpp's ROCm/gfx1151 Windows build actually run these models on this box; (iii) what does Step 8 (Pattern B) recover *without* a migration; (iv) whether vLLM's *force-close* semantics is materially better than llama.cpp's *budget* semantics for the J class.
**Why Cray's:** it trades a **development-phase platform constraint Cray stated personally** against a capability gap, and it front-loads the Linux migration that Cray explicitly wants deferred. No amount of code reading decides that.

**RULING (Cray, typed, 2026-09-03, s274): (a) — stay on Ollama now.** Cray's addition: **keep actively watching the Ollama-vs-llama.cpp capability gap** for a future decision point, since both projects ship new capabilities continuously — a revisit trigger, not a schedule. What this ruling does and does not settle: **no stack change happens under this PLAN** (Out of Scope stands); the *"llama.cpp keeps us on Windows"* point remains **Code's inference, not a fact**; and the four evidence needs listed above — (i) **OQ-4**, (ii) the ROCm/gfx1151 Windows build, (iii) what Step 8 recovers without a migration, (iv) force-close vs budget semantics — **stay open by design** and are what a future revisit must answer before (b)/(c)/(d) can be argued. The watch is a standing item, not an AC of this PLAN, and OQ-4 is not worked here.

### SD-8 — Does a truncated or clamped call become a user-visible disclosure?
**Options.** (a) **Log only.** (b) **Disclosure on the trace** (the existing `disclosure` channel the N sites already use, capped at `DISCLOSURE_CAP`). (c) Disclosure **plus** a UI marker.
**Recommendation: (b)**, because the two N-class sites already carry a `disclosure` field and already degrade — they are one field away from saying *why*, and RESULTS.md's whole lesson is that *"empty content"* without `done_reason` misattributes the cause for months.
**Why Cray's:** (c) puts a model-internals word in front of a **customer on the published demo**. That is positioning, not engineering.

**RULING (Cray, typed, 2026-09-03, s274): (b).** A truncated or clamped call becomes a **disclosure on the existing trace `disclosure` channel** — the one the two N-class sites (`nl_query.py:1236`, `run_query.py:585`) already use — **not** merely a log line (a), and **not** a UI marker (c). Consequences: the N-class empty-content branches gain the `done_reason` that tells a truncation from chosen silence; D-1's fix (AC-6) discloses its deterministic judgment on the trace rather than leaving a bare `error`; a clamp that fires in Step 3's seam is disclosed the same way; and (c)'s customer-facing wording question does not arise under this PLAN. For **A Author** (`scaffold.py`, a CLI batch with no run trace) AC-7's on-disk `done_reason` record is the equivalent surface — Step 4 states, per site, which surface carries the disclosure.

### SD-9 — *(added by the drafter)* Does the five-class taxonomy need ADR ratification?
**Why it is asked:** the highest ADR is **0038** and **none** governs LLM call budgeting; the CHECKPOINT-0 contract lives in ADR-001 and in code comments. CLAUDE.md §8 requires an ADR to be **merged before** its related implementation PR. If the taxonomy is architectural — and a typed `Workload` on the client that every call site must declare arguably is — then Step 3 is an implementation PR without its ADR.
**Options.** (a) PLAN-only; the taxonomy lives here. (b) A companion ADR ratifying the five classes and the budget rule, merged before Step 3. (c) PLAN now, ADR later once the arms have filled in the numbers.
**Recommendation: (c)** — the classes are stable but their *numbers* are exactly what the programme measures, and an ADR ratifying unmeasured defaults would need amending three times.
**Why Cray's:** it is a governance-routing call, and §8's "ADR merged before implementation" rule is Cray's to apply.

**RULING (Cray, typed, 2026-09-03, s274): (c).** PLAN now, ADR later once the arms have filled in the numbers. **Consequence: Step 3 is NOT blocked awaiting an ADR** — the seam ships under this PLAN, and the ADR that ratifies the five classes and the budget rule is authored after the programme's numbers exist (its own Cowork / `plan-drafter` dispatch, per CLAUDE.md §6 routing). The header's *Related ADRs* line is updated to match.

### Follow-ups surfaced by the s274 rulings — NOT ruled

These are questions the rulings *created*; none is decided here.

- **SD-1.1 — A client shared by two classes.** Under SD-1 = (b) a constructor-level `Workload` cannot serve two classes from one client (candidate: `nl_query.py:691` S and `:1225` N, if they share a client — Step 3 checks). **Drafter's recommendation:** construct one client per class in the factory. **Alternative:** a per-call override — but that is the (a) shape SD-1 ruled against, so it needs a fresh ruling, not an implementer's choice.
- **SD-4.1 — Step 4b's placement and read.** Placement before Step 5, the `num_predict` at which the characterisation runs, and the operational meaning of *"default"* (drafter's proposal: p95 of `total_duration` across arms plus a stated margin) are fixed in Step 4b's pre-committed read and ratified with it.
- ~~**SD-6.1 — Which mechanic realises "(a) for demo/production".**~~ **RULED (Cray, typed, 2026-09-03, s274): the explicit `LLM_MAX_INFLIGHT=0`** in all three published profiles. Recorded in the SD-6 block above; no longer open.

---

## Open questions

- **OQ-1 — The residual / shared-budget contradiction.** `total_duration − eval_duration` implies ~1,089–1,292 total tokens on delivering calls (above the 1024 cap ⟹ separate budgets); `thinking/parser.go` as a post-generation splitter and Ollama **#17978** imply one shared budget. The residual also contains prefill and grammar-compilation time. **Settled by Step 2 (offline)** — capture `load_duration` + `prompt_eval_duration` + the raw `thinking` string. **Nothing may be built on the reconstruction until then.**
- **OQ-2 — Why do some calls fit the budget?** Reasoning length does **not** separate the groups (6 of 21 delivering attempts reasoned inside the truncated range). Unexplained. May require OQ-1 to be settled first.
- **OQ-3 — Does raising the cap alone suffice?** Untested. Step 6. **New dependency (SD-4 redirect, s274):** Step 6 raises the cap against a timeout that Step 5 has raised to a *measured* number from Step 4b (OQ-9). Without that, a Step 6 result cannot be told apart from a deadline effect, and the answer to OQ-3 would be confounded by construction.
- **OQ-4 — Does Ollama pass `--reasoning-budget` down to llama-server?** Unknown; load-bearing for SD-7 option (a) versus (b). **Left open by design under SD-7 = (a), s274** — it is one of the four evidence needs a future revisit must answer; it is not worked under this PLAN.
- **OQ-5 — The CHECKPOINT-0 justification cites a stale issue.** Ollama **#15260** is **CLOSED** and concerns **gemma4**, not Qwen3.x; the Qwen sibling is **#14645**, also closed. Root cause of both: schema masking deferred until the end-of-thinking token — which is itself *why* a reasoning pass runs unconstrained. **The contract may still be right**; its justification needs re-checking against the running Ollama version. It is cited in code at `client.py:16-18`, `structured.py:50`, `intake.py:18`, `schemas.py:22`, `pipeline.py:33` — five places that would all need correcting together.
- **OQ-6 — Is `A Author` truncating today?** D-2 says likely and silent. Checkable offline on the next scaffold run.
- **OQ-7 — What is the effective `num_ctx` on the box?** Unmeasured. Binds AC-5 and Step 6.
- **OQ-8 — Is `J Judge`'s 4096 requirement general or one case?** Lesson 0049 measured it on one case (at 1024 it scored UNSCORED; at 4096 it produced a forbidden-handler proposal the shipped default had hidden entirely). This run **closes that lesson's `done_reason="length"` caveat** — recorded there as *asserted, not measured on this server*, now measured 45/45 — but the 4096 figure itself remains n=1.
- **OQ-9 — *(created by SD-4's redirect, s274)* What are the min / max / default timeouts, empirically, across the three models with one resident at a time?** Unmeasured. Answered by Step 4b under the pre-approved scoped §8 go. Blocks SD-4's deferred retry decision and Step 5's target value; feeds AC-4's `load` and `prefill` terms. The characterisation's `num_predict` must be stated in its read, because the timeout a cap needs scales with the cap (SD-4.1).

---

## Verification

- **Offline gates at true CI scope:** full `mypy services/`, full `tests/`, bare `ruff check .` (AC-9).
- **Probe battery** through `tools/probe_battery/` for every load-bearing green — one mutation per assertion, each probe proving its mutation reached the code, each report printing measured values (`pre=N post=M`).
- **Scenario test** (CLAUDE.md §8) driving a real call site into the real client against a transport double that asserts the wire `num_predict`. Stubbing `chat()` does not satisfy AC-3.
- **Live arms:** each under its own typed Cray §8 go, each with a pre-committed pass/fail read fixed **before** the run, one intervention per arm, `systemd --user` so the run cannot share a carrier's fate, artifacts under `.claude/benchmark-results/` and figures reported as **raw fractions** with the arm's n stated.
- **The AFTER read** is Step 10 against PLAN-0118's preserved baseline: same gold set, same seam, same shipped config but the one ratified change. A run that changes anything else is not an AFTER and is reported as a new baseline instead.
