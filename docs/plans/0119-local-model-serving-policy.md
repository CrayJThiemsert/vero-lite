# PLAN-0119: Local model-serving policy — a five-class workload taxonomy, a per-call-site budget seam, and the sequenced experiments that fill it in

**Status:** Draft
**Owner:** both (Claude Code executes; Cray adjudicates the Surfaced Decisions and every live arm)
**Created:** 2026-09-03
**Related ADRs:** none yet — see **SD-9** (whether the taxonomy needs ADR ratification). Touches ADR-001 (the CHECKPOINT-0 `think`/`format` contract), ADR-0030 D5 (never-raise advisory), ADR-0022/PLAN-0035 (the advisory verification judge).
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

**There is therefore no seam through which any call site can ask for a different budget.** This is a *structural* gap, not a tuning gap, and it is the root obstacle to every other item in this PLAN. The client's own comment argues the chokepoint position deliberately (`client.py:329-332`: *"Sits beside `temperature` rather than in a per-call argument for the same reason the in-flight cap is read here — eight call sites construct a client, and a bound that must be passed correctly at each of them is one forgotten argument from being off"*). That reasoning is sound about **forgetting** and is exactly why SD-1's recommended design keeps the chokepoint while making the *class* declarable.

**`CallRole`** (`client.py:131`, `Literal["reasoning","structuring"]`) already exists but tags **metrics only** — it never sets a cap.

**`num_ctx` is never sent** — 0 hits repo-wide (verified). Context headroom is not binding today: the maximum `prompt_eval_count` on a truncated call is 741, so 741 + 1024 ≈ 1,765. **It would bind at cap 4096** if the server's effective `num_ctx` is 4096 (741 + 4096 = 4,837). The box reports a model `context_length` of 32768, but Ollama's *runtime* `num_ctx` default is a separate thing and is unmeasured here. **Raising the cap without also sending `num_ctx` risks silently truncating the prompt instead of the output — a strictly worse failure, because it is invisible in `done_reason`.**

**Accounting is nearly absent.** `call_metrics` is invoked at **two** production lines only — `structured.py:251` and `:265` (verified: those are the only two outside `client.py`'s own definition at `:235`). Twelve of the fourteen in-client call sites emit **no generation accounting at all**, so the audit surface needed to answer *"what does this call site actually demand"* does not exist for them.

**Timeout semantics bind every design.** `settings.llm_request_timeout_s = 120.0` (`config.py:163`), and a client timeout **aborts and discards every token produced** — the config docstring at `config.py:168-179` says so in as many words. Projections from the measured decode rates (arithmetic re-checked by this drafter): gpt-oss at 4096 ≈ **85 s** (fits); qwen at 2048 ≈ **105–111 s** (does not, once load and prefill are added). PLAN-0118 SD-5 already ruled the scoring semantics: a **validation exhaustion counts wrong and stays** in the denominator; a **transport error is unscored and leaves** it.

> **The binding consequence: raising a cap without raising the timeout converts truncations into strictly-worse aborts** — a graded wrong answer becomes an ungraded missing one. **Cap and timeout move together, always.**

**Dead and unwired config.** `ollama_default_model` (`gemma4:26b`, `config.py:132`) is referenced by nothing. `reasoning_mode` (`structured.py:42`, default `"full"`) sends `think` as a *boolean*, which `gpt-oss` ignores.

> ⚠️ **Correction to the dispatch fact-pack.** It states `reasoning_mode` has "no caller". On disk it has **no *production* caller**, but `benchmarks/procedure_baseline/harness.py:196,232,248,332,383,437` and `run_benchmark.py:119,165,546` *do* pass it, and `run_benchmark.py:546` exposes it as a **CLI flag**. This matters and is not a nitpick: **the repo already has working prior art for threading a per-call knob from a CLI down to `chat()`** — threaded as a parameter on the `generate_judgment` helper, not as an argument on `chat()`. SD-1 must weigh that precedent. `harness.py:273-282` additionally already implements *"the model did not honour the knob"* detection (it raises when `think_off` still returns thinking), which Step 5 reuses rather than reinvents.

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

- **D-1 — `action_step` has no deterministic fallback.** `action_step.py:432` calls `generate_judgment(...)` with **no `try`/`except`** (verified: `execute()` at `:410-434` wraps nothing). `OllamaError` / `StructuredOutputError` propagate to an unhandled 500 — unlike the recommender's fail-safe and unlike the N-class sites, which both degrade. It is unreachable today **only because the stub is injected**; procurement's parameterised factory (`run.py:296`) is the hole. A truncation on that path is a 500, not a degrade.
- **D-2 — `scaffold.py:676` is a likely silent second victim.** It asks for an entire synthetic dataset — the largest output in the system — under the same 1024 cap. On truncation, `_parse_synthetic` fails, `llm_synthetic_or_none` (`:684-694`) catches **everything**, logs *"LLM synthetic draft unusable"* and returns the deterministic draft. **No `done_reason`, no truncation disclosure.** If this workload has been truncating all along, nothing on disk would say so. **Checkable offline** by capturing `done_reason` on the next scaffold run.

---

## Acceptance Criteria

Evidence discipline is CLAUDE.md §8 throughout: **every load-bearing green is witnessed RED** through `tools/probe_battery/` (never a from-scratch `/tmp` script), one mutation per assertion; every verification report **prints the values it measured** (`pre=N post=M`), never a bare PASS/FAIL.

- [ ] **AC-1 — The taxonomy and the call-site inventory are on disk and guarded.** §3's two tables ship in the repo, and a **guard test reads the artifact** (not its own constant) asserting every `.chat(` site under `services/` appears in the inventory with a class. Positive control: a newly added call site must redden it. *(Lesson: a committed-file guard is blind to new files unless it enumerates from the tree.)*
- [ ] **AC-2 — The instrument records what the residual question needs.** The benchmark recorder captures `load_duration_ns`, `prompt_eval_duration_ns` (both **already computed in `CallMetrics`** and dropped today) and the **raw `thinking` string**; the runner grows `--num-predict` and `--think` flags, which do not exist today. Witnessed RED by removing one captured field and seeing *that* assertion redden.
- [ ] **AC-3 — The budget seam exists and is exercised end-to-end.** Per SD-1's ratified design. A **scenario test drives the real producer into the real consumer** on realistic simulated data — a real call site through the real client into a transport double that **asserts the `num_predict` on the wire matches the class**. A test that stubs `chat()` itself does **not** satisfy this: it would agree with itself by construction and could not see the wire.
- [ ] **AC-4 — The budget rule is checkable, not aspirational.** `cap / decode_rate + load + prefill < timeout` is implemented as a function with unit tests, **including a case that fails** (qwen at 2048 against a 120 s timeout). A guard asserts **cap and timeout cannot be changed independently** — raising one without the other reddens.
- [ ] **AC-5 — `num_ctx` is sent whenever the cap exceeds the measured safe headroom**, with a test proving prompt + cap ≤ context. Positive control: a prompt large enough to breach must redden it.
- [ ] **AC-6 — D-1 is fixed.** `action_step` degrades deterministically on `OllamaError`/`StructuredOutputError` instead of 500-ing. Witnessed RED by a fault-injecting double at the **procurement** parameterised seam — the one path where it is reachable.
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
- ❌ **Migrating the serving stack.** SD-7 frames the option space and names its evidence needs; it does not migrate. No stack change happens under this PLAN.
- ❌ **Prompt engineering.** Changing a prompt changes the demand, which would confound every arm below.
- ❌ **Retiring `ollama_default_model` / `reasoning_mode`.** Noted as unwired; removal is a separate `chore/*`.

---

## Steps

### Experiment sequencing (binding)

**Repair the instrument offline first → raise the timeout ALONE → then the cap on gpt-oss ALONE → then `think:"low"` → then Pattern B. Never two interventions in one arm.** Each live step is its own §8 go with its own pre-committed read. A step whose predecessor has not landed does not run.

### Step 1 — Record the taxonomy and the inventory (offline, no code)
Ship §3's tables plus the decision checklist. Land AC-1's guard test. Unblocks nothing else — do it first so every later step has a place to write its numbers.

### Step 2 — Repair the instrument (offline)
AC-2. Capture `load_duration_ns`, `prompt_eval_duration_ns` and the raw `thinking` string; add `--num-predict` / `--think`. **This is the step that makes OQ-1 answerable**: without a prefill rate the budget rule of AC-4 is not evaluable, because `prefill` is currently an unmeasured term. It is offline work on the existing seam — no MS-S1 contact.

### Step 3 — Build the seam (offline)
Per SD-1. Land AC-3, AC-4, AC-5, AC-8, AC-11. **Ship it with every class set to today's 1024** — a pure refactor with no behaviour change, so its own correctness is provable offline and the later arms measure one thing each. Resist the urge to bundle a new default here; that is the confound the sequencing rule exists to prevent.

### Step 4 — Fix D-1 and D-2 (offline)
AC-6, AC-7. Independent of the live programme; do them while waiting for a §8 go.

### Step 5 — LIVE ARM A: raise the timeout **alone**
`llm_request_timeout_s` up, cap unchanged at 1024. **Pre-committed read:** the empty-body fraction should be **unchanged** (truncation is a cap phenomenon, not a deadline one). If it moves, the model of the failure is wrong and the programme stops for re-analysis. This arm exists to buy headroom for Arm B and to falsify a lurking deadline effect — a null result is the expected, informative outcome.

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
7. **Failure behaviour on truncation:** degrade, retry, fail closed, or 500. **"500" is never an acceptable answer** — that is D-1.
8. **Is the truncation visible?** Is `done_reason` captured, and does the degrade path record it?
9. **Which model, and is it resident?** A cold load is 5–46 s depending on the arm (measured), against the latency budget in (5).

---

## Surfaced Decisions

Each carries options, a recommendation with a one-line reason, and why it is Cray's call rather than Code's. **None of these is decided by this draft.**

### SD-1 — The budget seam design
**Options.** **(a)** A `budget=` keyword on `chat()`. Explicit and legible at the call site; demand is auditable by reading the call. Blast radius: the dispatch measured **~42** existing test doubles that are keyword-only with no `**kwargs`, **plus** the `ChatClient` **Protocol** definitions (`structured.py:65-72`, `intake.py:43`) and the production stub clients (`advisory_stub.py:71`, `verticals/procurement/hero_demo/run.py:105`, two benchmark harnesses). *(Drafter's independent check: **61** `async def chat(` definitions exist repo-wide, of which at least 7 already accept `**kwargs`. That is consistent with ~42 keyword-only test doubles; **Step 3 re-derives the exact figure with a scripted count as its pre-committed number** rather than inheriting it.)*
**(b)** A **`Workload` literal on the client** (set at construction / in the `client_factory`), with the call *shape* — reasoning pass vs structuring pass — derived at the chokepoint from `response_format`/`think`, plus a **per-model capacity clamp**. **Zero test-double blast radius**, because doubles implement the Protocol and never construct `OllamaClient`.
**(c)** A settings-keyed table (`llm_budgets: dict[workload, int]`) with the workload passed per call — a hybrid inheriting (a)'s blast radius.
**Recommendation: (b)** — it is the only option that adds the knob without touching ~42 doubles and two Protocols, it preserves the client's own "one chokepoint cannot be bypassed" argument (`client.py:329-332,356-359`), the per-model clamp needs the model which only the client owns, and Pattern B's two calls are distinguished exactly where `think`/`response_format` are already visible.
**Honest counter, because it cuts against the recommendation:** (a) makes each site's demand readable *at the site*, which is closer to this PLAN's stated goal of explicit per-site demand; under (b) you must trace a factory to learn a call's budget. And the repo already has working per-call threading prior art (`reasoning_mode` through `generate_judgment`, with a CLI flag at `run_benchmark.py:546`) — so (a) is not unprecedented here.
**Why Cray's:** it trades **auditability-at-the-call-site** against **~42 files of churn plus two Protocol changes**. That is a taste-and-cost judgment about the codebase's future readers, not a correctness question.

### SD-2 — An unlisted model: fail closed, or refuse?
**Options.** (a) **Fail closed** — an unknown model gets the most conservative budget and logs. (b) **Refuse** — raise at construction; an unlisted model cannot be used until someone adds its measured capacity.
**Recommendation: (b) refuse, for the app; (a) fail closed, for the G Gate hook** — because a refusal in a PreToolUse hook blocks a human at the keyboard, while a refusal in the app surfaces at wiring time where it is cheap.
**Why Cray's:** (b) means adding a model requires a measurement first, which is either the discipline this whole PLAN is for or an unacceptable friction on experimentation. That is a workflow preference.

### SD-3 — Is `"unspecified"` a permitted default, or a type error?
**Options.** (a) Permitted, mapping to today's 1024 — every existing call site keeps working untouched. (b) A **type error** — every call site must name its class; the type checker enumerates the work.
**Recommendation: (b)**, because a permitted default is *exactly* how the current global cap became invisible: 12 of 14 sites inherited it and nobody had to look. `mypy services/` at full scope turns the migration into a finite, enumerable list.
**Why Cray's:** (b) front-loads the whole inventory into one PR instead of allowing incremental adoption. That is a sequencing call with real schedule cost.

### SD-4 — Escalate on truncation: once, or not at all?
**Options.** (a) **Not at all** — a truncation is a wrong answer; disclose and move on. (b) **Retry once at a higher cap**, then give up. (c) Retry at the same cap (today's behaviour — the intake retry loop, which rescued 5 of 7 empty-first cases and never recovered 2).
**Recommendation: (a) not at all, for now.** An escalating retry doubles the worst-case latency against a **120 s timeout that aborts and discards everything**, and PLAN-0118 showed the retry loop's own error message (*"output was not valid JSON"*) misattributed the failure for an entire benchmark run. Fix the visibility before adding a rescue on top of it.
**Why Cray's:** (b) is a real availability/latency trade on a **user-facing** surface, and the published demo's tolerance for a slow answer versus a disclosed degrade is a product judgment.

### SD-5 — Per-model `keep_alive` and residency
**Facts.** Observed VRAM: gpt-oss 12.15 GiB, qwen-q4 16.32, qwen-q8 27.12; **two fit at 44.7%** of the ~63.65 GiB allocated; loading a third made Ollama **evict the others itself**. Warm times 5–6 s / 24 s / 46 s. The app sends `"30m"`; the classifier hook sends `"10m"`; **both want `gpt-oss:20b` resident**.
**Options.** (a) One global `keep_alive` from a single source (the current app value), hook included. (b) Per-class `keep_alive` — long for G (a blocked human), short for A (batch, no latency budget). (c) Pin a residency set of at most two models explicitly.
**Recommendation: (a) + (c)** — one source removes the two-values-that-must-agree defect, and an explicit two-model residency set matches the measured eviction behaviour instead of discovering it.
**Why Cray's:** (c) allocates a scarce shared host resource across two workloads (the harness's own gate, and the product) whose relative priority is a business call.

### SD-6 — Should `llm_max_inflight` be pinned to 1?
**Fact:** default is **0 = unlimited** (`config.py:330-340`), and the docstring already records *"Published demo pins 1"* — so the published posture is pinned; the question is the **default**.
**Options.** (a) Leave 0. (b) Pin 1 everywhere. (c) Pin 1 for dev/CI, leave the published override as-is.
**Recommendation: (b)**, because concurrent generations on one box contend for the same VRAM and the same decode throughput, which would make every latency figure in this PLAN's programme unreproducible — and reproducibility is the point of the programme.
**Why Cray's:** the config comment explicitly says *"If Cray meant 1 everywhere, this default is the one line to change"* — it is a decision already reserved to Cray in writing.

### SD-7 — Should we move off Ollama to llama.cpp or vLLM?
**The constraint, verbatim:** *"we still want to stand on Windows to the last possible moment in this development phase; we accept that we may have to move to Linux when we reach the production phase."*
**What forces the question:** only llama.cpp and vLLM expose a reasoning budget. **llama.cpp** documents `--reasoning-budget` (*"-1 unrestricted, 0 immediate end, N>0 token budget"*) and `--reasoning-format`. **vLLM** documents `thinking_token_budget`, which **forces the reasoning block closed** rather than truncating — *strictly better than a cap, because it guarantees a content channel survives* — plus `--structured-outputs-config.enable_in_reasoning`. **Ollama has no separate thinking budget**: PR **#17566** (*"there is currently no way to say 'think, but not forever'"*) is **unmerged**.
**Host facts:** MS-S1 MAX runs **Windows** (the remote shell is PowerShell; Windows services, scheduled tasks, event logs — `.claude/skills/ms-s1-admin/`), AMD Ryzen AI Max+ 395, ROCm gfx1151, ~63.65 GiB allocated of 128 GB, `context_length` 32768.
**Options.** (a) **Stay on Ollama**, work within cap + Pattern B; revisit if #17566 merges. (b) **Move to llama.cpp**. (c) **Move to vLLM**. (d) **Hybrid** — Ollama for G/N/S, a reasoning-budget server for J/A only.
**Recommendation: (a) now, with (b) as the pre-scoped fallback — and explicitly contingent on evidence this PLAN does not yet have.** Reason: Pattern B (Step 8) obtains a *per-channel* budget **without any stack change**, and `structured.py` already ships it — so the cheapest path to the actual goal does not require the migration at all. **⚠️ Marked as Code's inference, not a fact:** llama.cpp ships Windows builds and is, of the three, the only one that plausibly keeps the Windows constraint *and* gains a reasoning budget; vLLM is Linux-first and would force the Linux move early. **This is the option space with its evidence needs, not an assertion.**
**Evidence this SD needs before it can be decided:** (i) does Ollama pass `--reasoning-budget` down to its bundled llama-server (**OQ-4** — currently unknown); (ii) does llama.cpp's ROCm/gfx1151 Windows build actually run these models on this box; (iii) what does Step 8 (Pattern B) recover *without* a migration; (iv) whether vLLM's *force-close* semantics is materially better than llama.cpp's *budget* semantics for the J class.
**Why Cray's:** it trades a **development-phase platform constraint Cray stated personally** against a capability gap, and it front-loads the Linux migration that Cray explicitly wants deferred. No amount of code reading decides that.

### SD-8 — Does a truncated or clamped call become a user-visible disclosure?
**Options.** (a) **Log only.** (b) **Disclosure on the trace** (the existing `disclosure` channel the N sites already use, capped at `DISCLOSURE_CAP`). (c) Disclosure **plus** a UI marker.
**Recommendation: (b)**, because the two N-class sites already carry a `disclosure` field and already degrade — they are one field away from saying *why*, and RESULTS.md's whole lesson is that *"empty content"* without `done_reason` misattributes the cause for months.
**Why Cray's:** (c) puts a model-internals word in front of a **customer on the published demo**. That is positioning, not engineering.

### SD-9 — *(added by the drafter)* Does the five-class taxonomy need ADR ratification?
**Why it is asked:** the highest ADR is **0038** and **none** governs LLM call budgeting; the CHECKPOINT-0 contract lives in ADR-001 and in code comments. CLAUDE.md §8 requires an ADR to be **merged before** its related implementation PR. If the taxonomy is architectural — and a typed `Workload` on the client that every call site must declare arguably is — then Step 3 is an implementation PR without its ADR.
**Options.** (a) PLAN-only; the taxonomy lives here. (b) A companion ADR ratifying the five classes and the budget rule, merged before Step 3. (c) PLAN now, ADR later once the arms have filled in the numbers.
**Recommendation: (c)** — the classes are stable but their *numbers* are exactly what the programme measures, and an ADR ratifying unmeasured defaults would need amending three times.
**Why Cray's:** it is a governance-routing call, and §8's "ADR merged before implementation" rule is Cray's to apply.

---

## Open questions

- **OQ-1 — The residual / shared-budget contradiction.** `total_duration − eval_duration` implies ~1,089–1,292 total tokens on delivering calls (above the 1024 cap ⟹ separate budgets); `thinking/parser.go` as a post-generation splitter and Ollama **#17978** imply one shared budget. The residual also contains prefill and grammar-compilation time. **Settled by Step 2 (offline)** — capture `load_duration` + `prompt_eval_duration` + the raw `thinking` string. **Nothing may be built on the reconstruction until then.**
- **OQ-2 — Why do some calls fit the budget?** Reasoning length does **not** separate the groups (6 of 21 delivering attempts reasoned inside the truncated range). Unexplained. May require OQ-1 to be settled first.
- **OQ-3 — Does raising the cap alone suffice?** Untested. Step 6.
- **OQ-4 — Does Ollama pass `--reasoning-budget` down to llama-server?** Unknown; load-bearing for SD-7 option (a) versus (b).
- **OQ-5 — The CHECKPOINT-0 justification cites a stale issue.** Ollama **#15260** is **CLOSED** and concerns **gemma4**, not Qwen3.x; the Qwen sibling is **#14645**, also closed. Root cause of both: schema masking deferred until the end-of-thinking token — which is itself *why* a reasoning pass runs unconstrained. **The contract may still be right**; its justification needs re-checking against the running Ollama version. It is cited in code at `client.py:16-18`, `structured.py:50`, `intake.py:18`, `schemas.py:22`, `pipeline.py:33` — five places that would all need correcting together.
- **OQ-6 — Is `A Author` truncating today?** D-2 says likely and silent. Checkable offline on the next scaffold run.
- **OQ-7 — What is the effective `num_ctx` on the box?** Unmeasured. Binds AC-5 and Step 6.
- **OQ-8 — Is `J Judge`'s 4096 requirement general or one case?** Lesson 0049 measured it on one case (at 1024 it scored UNSCORED; at 4096 it produced a forbidden-handler proposal the shipped default had hidden entirely). This run **closes that lesson's `done_reason="length"` caveat** — recorded there as *asserted, not measured on this server*, now measured 45/45 — but the 4096 figure itself remains n=1.

---

## Verification

- **Offline gates at true CI scope:** full `mypy services/`, full `tests/`, bare `ruff check .` (AC-9).
- **Probe battery** through `tools/probe_battery/` for every load-bearing green — one mutation per assertion, each probe proving its mutation reached the code, each report printing measured values (`pre=N post=M`).
- **Scenario test** (CLAUDE.md §8) driving a real call site into the real client against a transport double that asserts the wire `num_predict`. Stubbing `chat()` does not satisfy AC-3.
- **Live arms:** each under its own typed Cray §8 go, each with a pre-committed pass/fail read fixed **before** the run, one intervention per arm, `systemd --user` so the run cannot share a carrier's fate, artifacts under `.claude/benchmark-results/` and figures reported as **raw fractions** with the arm's n stated.
- **The AFTER read** is Step 10 against PLAN-0118's preserved baseline: same gold set, same seam, same shipped config but the one ratified change. A run that changes anything else is not an AFTER and is reported as a new baseline instead.
