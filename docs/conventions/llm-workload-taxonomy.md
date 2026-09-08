# LLM workload taxonomy and call-site inventory

> **Canonical.** This file is the source of truth for *what kind of work* each LLM call
> site asks for. `tests/services/engine/llm/test_workload_inventory_contract.py` reads
> **this file** — not a constant of its own — and fails when a `.chat(` site under
> `services/` is missing from the inventory below.
>
> Origin: [`PLAN-0119`](../plans/0119-local-model-serving-policy.md) §3 + Step 1 (AC-1, AC-8).
> The numbers marked **(unmeasured)** are what PLAN-0119's experiment programme fills in;
> **they are not to be shipped as defaults before their step lands.**

---

## 1. The five classes

Each class declares: needs reasoning · structured or not · output size · latency budget ·
failure behaviour.

| Class | What it is | Reasoning | Structured | Output size | Latency budget | Failure behaviour |
|---|---|---|---|---|---|---|
| **G Gate** | The PreToolUse classifier — a hook, **outside** this client | no | yes (tiny schema) | tens of tokens | **p95 ≤ ~25 s** (hard — a human is blocked) | **fails closed** (deny) |
| **S Structure** | intake, NL/run-corpus translate, procedure-draft classify + prose | incidental (the model reasons anyway) | yes | 300–800 tok *(measured content segment: 135–381)* | interactive, seconds | retry loop, then validation exhaustion = a wrong answer that **stays** in the denominator |
| **J Judge** | recommender (Pattern B), `action_step` Pattern B, action-verification | **yes, explicitly** | yes | **≥ 4096 needed** ([Lesson 0049](../lessons/0049-measure-generation-demand-not-the-cap-that-happens-to-work.md)) | interactive-tolerant | recommender degrades to the deterministic floor; **`action_step` has no fallback — D-1** |
| **N Narrate** | free prose phrasing; the gate-advisory narrative | no | **no** | small (1–2 sentences) | latency-dominated, user-facing | **already degrades well** — deterministic fallback + an explicit empty-content branch |
| **A Author** | `scaffold.py` synthetic dataset — the largest output in the system | no | yes | **largest in the system (unmeasured)** | **none — CLI batch** | falls back to the deterministic draft, **with no truncation disclosure — D-2** |

### The G Gate class has two backends, and only one is local

`.claude/hooks/_sonnet_classifier.py` is a whole workload **outside** `services/engine/llm/`.
It calls Ollama directly with **no `num_predict` at all**, its own `keep_alive: "10m"`
against the app's `"30m"`, and its own **75 s** timeout. It also has an API backend
(`claude-sonnet-4-6`, 20 s). Its local model is `gpt-oss:20b` — *the same model the app's
recommender uses*. Two `keep_alive` values that must agree but have no shared source are a
defect waiting to happen (PLAN-0119 Step 9), and two workloads contending for one resident
model is a residency question (PLAN-0119 SD-5).

Because it is outside `services/`, the guard test **cannot see it** — it is listed in the
inventory below with `services_scope: no` and is covered by review, not by the guard. That
hole is named here rather than hidden.

---

## 2. Call-site inventory

Sites are addressed by **`path::function::shape`** — ruled by Cray (typed, session 286) over
a line-keyed alternative, because a line key reddens on any edit that shifts a line and 45
of the last 200 commits on `main` (~22%) touched one of these files. `shape` is what the
client's chokepoint can already tell apart with no new argument: `structuring` = a
`response_format` was passed, `reasoning` = `think` with no `response_format`, `bare` =
neither. The `Line` column is **documentation only — the guard does not read it**, so a
drifted line number is a stale comment, never a red build.

<!-- INVENTORY-TABLE-START -->
| Site | Class | Line | Live? | Accounting? |
|---|---|---|---|---|
| `services/engine/action_verification.py::judge_action_expression::structuring` | J | 294 | **off by default** (`verification_judge_enabled=False`) | no |
| `services/engine/llm/intake.py::extract_package::structuring` | S | 182 | yes — **the measured one** | no (the benchmark recorder adds it) |
| `services/engine/llm/structured.py::generate_judgment::reasoning` | J | 245 | yes | **yes** |
| `services/engine/llm/structured.py::generate_judgment::structuring` | J | 260 | yes | **yes** |
| `services/engine/nl_query.py::_translate::reasoning` | J | 678 | **no shipped caller** (`two_pass` arm) | no |
| `services/engine/nl_query.py::_translate::structuring` | S | 691 | yes | no |
| `services/engine/nl_query.py::_phrase::bare` | N | 1225 | yes — **published demo headline** | no |
| `services/engine/procedures/gate_advisory.py::_entry::bare` | N | 160 | **arm unreachable** — no construction passes `client_factory` | no |
| `services/engine/procedures/generator/pipeline.py::classify_narrative::reasoning` | J | 236 | **no shipped caller** (`two_pass` arm) | no |
| `services/engine/procedures/generator/pipeline.py::classify_narrative::structuring` | S | 245 | yes | no |
| `services/engine/procedures/generator/pipeline.py::build_skeleton::structuring` | S | 480 | yes | no |
| `services/engine/run_query.py::translate_run_query::structuring` | S | 511 | yes | no |
| `services/engine/run_query.py::phrase_run_answer::bare` | N | 574 | yes — **published demo headline** | no |
| `services/engine/scaffold.py::_llm_records::structuring` | A | 676 | yes (CLI) | no |
<!-- INVENTORY-TABLE-END -->

### Two workloads this table does NOT guard, named rather than hidden

| Workload | Class | Why it is not a guarded row |
|---|---|---|
| `.claude/hooks/_sonnet_classifier.py` | **G** | Outside `services/` — the guard's scope by construction. Covered by review only. |
| `services/engine/procedures/action_step.py` (`generate_judgment` at `:432`) | **J** | Not a `.chat(` site: it routes through `structured.py::generate_judgment`, so it is guarded **transitively** by that module's two rows. Its own defect (D-1) is §4 below. |

> ⚠️ **Correction to PLAN-0119 §3, recorded here — `was an error`.** That table says it was
> *"verified by grepping `\.chat\(` under `services/`"* and lists **14** rows. Re-measured at
> session 286 with an AST walk: there are indeed 14 `.chat(` sites, but **the two sets of 14
> are not the same set**. PLAN §3 includes `action_step.py:422→432`, which contains **zero**
> `.chat(` (grep exit 1 — verified), and omits `gate_advisory.py:160`, which **is** one — it
> appears only in that section's prose liveness notes. The counts matching at 14 is a
> coincidence of one error in each direction. Nothing downstream rested on the membership,
> so this is a table defect, not a decision defect; PLAN-0119 §3 still needs the same
> correction inline (a `docs/plans/` write — drafter dispatch).

---

## 3. Decision checklist for a new call site

Answered **in the PR that adds it**. The guard test fails a site that skips it (AC-8).

1. **Which class?** G / S / J / N / A. If none fits, the taxonomy is wrong — say so rather
   than forcing a fit.
2. **Does it need reasoning?** If yes, it is J, and a single-call constrained shape is a
   **known** failure mode (45/45).
3. **Structured?** If yes, note that schema masking is deferred until the end-of-thinking
   token — this is *why* a reasoning pass runs unconstrained.
4. **Expected output size**, and **how it was obtained** — measured `eval_count`, or a
   stated estimate marked as such.
5. **Latency budget**, and whether a human is blocked.
6. **Does `cap / decode_rate + load + prefill < timeout` hold** at the target model's
   measured decode rate? Show the arithmetic.
7. **Failure behaviour on truncation:** degrade, retry, fail closed, 500, or a bare error.
   **Neither "500" nor "a bare `error` trace with no judgment" is an acceptable answer** —
   the second is what D-1 actually is, and it is the quieter of the two.
8. **Is the truncation visible?** Is `done_reason` captured, and does the degrade path
   record it?
9. **Which model, and is it resident?** A cold load is 5–46 s depending on the arm
   (measured), against the latency budget in (5).

---

## 4. Two defects this taxonomy makes visible

- **D-1 — `action_step` has no deterministic fallback.**
  `services/engine/procedures/action_step.py` calls `generate_judgment(...)` bare inside its
  `for entity in input_set:` loop with no `try`/`except`. The orchestrator's D4
  fail-and-divert catches it and records a `FAILED` / `WAITING_HUMAN` step carrying a bare
  `error` trace **and no judgment** — quieter than a 500, and so a *stronger* argument for a
  deterministic fallback, not a weaker one. Unreachable today only because a stub is
  injected everywhere except **procurement**, whose parameterised factory is the hole.
  Fixed by PLAN-0119 Step 4 (AC-6).
- **D-2 — `scaffold.py` is a likely silent second victim.** It asks for an entire synthetic
  dataset — the largest output in the system — under the same 1024 cap. On truncation the
  fallback logs *"LLM synthetic draft unusable"* and returns the deterministic draft: **no
  `done_reason`, no truncation disclosure.** If this workload has been truncating all along,
  nothing on disk would say so. Fixed by PLAN-0119 Step 4 (AC-7).

---

*Derived from PLAN-0119 §3 (session 274 revision, nine Surfaced Decisions ruled by Cray).
The PLAN keeps the reasoning lineage; this file is the operational reference.*
