# ADR-001: LLM Model Baseline (Phase 1)

> **Note (Session 10):** This document was authored during the vet clinic
> vertical (Phase 1 original scope). The vet clinic vertical is now parked
> as Phase 2 (see ADR-005 in the same Batch 2 push); Phase 1 vertical is
> now Operational Control Tower. The architectural decisions in this
> document remain valid and apply to both verticals.

**Status:** Accepted — amended 2026-05-22 (**Amendment 1**: recommender-path model pin — `gpt-oss:20b` + Ollama 0.24.0 supersedes `gemma4:26b` for the ADR-010 recommender path only; see "Amendment 1" below)
**Date:** 2026-05-05 (Amendment 1: 2026-05-22)
**Deciders:** Jirachai Thiemsert (founder)
**Related:** PLAN-001 (starter pack), ADR-002 (network topology), ADR-010 (LLM reasoning-hook surface — D1/D5/IN-1, the Amendment 1 trigger), PLAN-0006 (LLM reasoning-hook execution — CHECKPOINT-0 + gemma4 viability finding)

## Context

vero-lite uses local LLM inference on the **MS-S1 MAX** server (AMD Ryzen AI Max+ 395, 128GB unified memory with ~64GB allocated as VRAM). The choice of models affects:

1. **Memory budget** — total of 3 models concurrently loaded must fit the VRAM allocation, with overhead for KV cache during inference.
2. **Quality of outputs** — multimodal capability (vision) is required for the killer demo (handwritten medical record digitization).
3. **Function calling** — needed for MCP tool exposure to Claude Code.
4. **Reproducibility** — model versions must be locked so that demo behavior is deterministic across machines and time.

At the time of this ADR, Ollama on MS-S1 MAX has the following models verified available via `curl http://ms-s1-max:11434/api/tags`:

| Model | Family | Params | Quant | Size | Digest |
|---|---|---|---|---|---|
| `groomflow-unified:latest` | gemma4 | 25.8B | Q4_K_M | 16.7 GB | `8b39f569b683` |
| `gemma4:26b` | gemma4 | 25.8B | Q4_K_M | 16.7 GB | `5571076f3d70` |
| `qwen2.5-coder:32b` | qwen2 | 32.8B | Q4_K_M | 18.5 GB | `b92d6a0bd47e` |

The original handoff document specified `qwen3-coder` as a target, but `qwen2.5-coder:32b` is what is actually installed and verified working. `groomflow-unified:latest` is a custom fine-tune from a previous unrelated project (pet grooming) and is preserved on the server but not part of vero-lite's model stack.

## Decision

For **Phase 1** (months 1–6) of vero-lite, the LLM baseline is:

| Role | Model | Pinned Digest | Purpose |
|---|---|---|---|
| **Primary multimodal** | `gemma4:26b` | `5571076f3d70` | Vision + reasoning, handwriting OCR, document understanding, function calling |
| **Code agent** | `qwen2.5-coder:32b` | `b92d6a0bd47e` | Code generation, code review, agent workflows via LangGraph |
| **Cloud fallback** | Anthropic Claude API (Sonnet/Opus, latest) | N/A | High-stakes vision tasks, complex reasoning where local quality is insufficient |

> **Amended 2026-05-22 (Amendment 1):** for the **OCT recommender path** (ADR-010 D5), `gpt-oss:20b` + Ollama 0.24.0 supersedes the `gemma4:26b` row above. gemma4:26b's vision / multimodal role is unchanged (the recommender path is text-only structured generation). See "Amendment 1" below.

**Pinning policy:** All references to local models in code, configs, and tests **must use the digest, not the tag**, when reproducibility matters (e.g., demo recordings, CI tests, locked dependencies).

For day-to-day development convenience, `gemma4:26b` and `qwen2.5-coder:32b` may be referenced by tag, but lock files (`docker-compose.override.yml`, etc.) freeze digests.

**Out of scope:** `groomflow-unified:latest` is preserved on disk as historical artifact from a prior project but is **not** used by vero-lite. It will not be removed from MS-S1 MAX.

**Re-evaluation triggers:** This ADR is reviewed and potentially superseded if any of the following occur:
1. Quality bar for vision tasks (>90% accuracy on Thai handwritten medical text) is not met by `gemma4:26b` after 4 weeks of testing.
2. A successor model (e.g., `qwen3-coder`, `gemma5`) becomes available and benchmarks show >15% improvement on representative vero-lite tasks.
3. VRAM budget changes due to MS-S1 MAX configuration update.

## Amendment 1 — Recommender-path model pin (2026-05-22)

> **Scope of this amendment.** This amends the **Decision** table's *Primary
> multimodal* row **for the OCT recommender path only** (ADR-010 / PLAN-0006).
> It does **not** revise ADR-001's general multimodal baseline, the code-agent
> baseline (`qwen2.5-coder:32b`), or the cloud-fallback posture. Drafted by
> Cowork (Tier-1, ADR-009 D1) from Code's TODO-A handoff; **Code reviews +
> commits** (ADR-009 D2). Cray adjudicated the amend-in-place route (vs a new
> superseding ADR) on 2026-05-22.

### A1.1 Trigger

PLAN-0006 (the LLM reasoning-hook "brain swap" for
`services/engine/recommender.py::recommend()`, executed — closeout
`2026-05-22-2355-code-plan0006-kickoff-dispatch-closeout.md`) pins
**`gpt-oss:20b`** as the model for the recommender's structured-generation
path. That diverges from this ADR's `gemma4:26b` *Primary multimodal* baseline,
which ADR-010 IN-1 + PLAN-0006 §7 named a **required** governance follow-on
(kickoff dispatch §7 TODO-A).

### A1.2 Amended pin (recommender path only)

For the **OCT recommender path** (ADR-010 D5 — the LLM-backed `recommend()`),
the pinned model is **`gpt-oss:20b`** served on MS-S1 MAX (ADR-002) under
**Ollama 0.24.0**. `gpt-oss:20b` is a 21B-parameter mixture-of-experts model
(~3.6B active), ≈14 GB, with a native structured-output path (research brief
`2026-05-22-llm-reasoning-hook-local-models.md` §3/§5). `gemma4:26b` is
**superseded for this path**.

| Path | Amended model | Digest | Ollama | Supersedes (this path) | Status |
|---|---|---|---|---|---|
| OCT recommender (ADR-010 D5) | `gpt-oss:20b` | `17052f91a42e` | 0.24.0 | `gemma4:26b` | Pinned (PLAN-0006) |

### A1.3 Rationale — two independent grounds

Both verified live on MS-S1 MAX under Ollama 0.24.0 during PLAN-0006 Step 0
(CHECKPOINT-0) and a Cray-requested follow-up (closeout §3 + §10):

1. **`gemma4:26b` is not viable for the recommender's real schema (decisive,
   independent of #15260).** With the real `LlmJudgment` structuring schema —
   which carries a nested `$ref` (`EntityRef`) — `gemma4:26b` does **not
   complete** the structuring call: it stalls past a 600 s timeout, both with a
   free-string handler and with an enum-constrained handler. `gpt-oss:20b`
   completes the same nested-schema call in **41 s**. (The
   misleadingly-passing CHECKPOINT-0 spike used a *flat* schema, which gemma4
   handled in 3.6–16 s; the real nested schema is the operative case.)
2. **The Ollama `think`/`format` interaction (#15260) is still live in 0.24.0 —
   but does not, by itself, disqualify gemma4.** Setting `think=false` together
   with a `format` JSON schema silently drops the schema constraint on the
   **Qwen3.x family** (`qwen3.5:35b`, `qwen3.6:35b` emitted non-JSON prose under
   `think=false`); it is **absent** for both `gpt-oss:20b` and `gemma4:26b`
   (both honour `format` in every `think` condition). #15260 therefore rules out
   the Qwen3.x fallback under a naive config, but ground (1) — not #15260 — is
   what disqualifies gemma4 for this path.

Net: `gpt-oss:20b` is the only surveyed local model that both honours `format`
reliably **and** completes the recommender's real nested-schema structuring
call.

CHECKPOINT-0 verdict grid (`format` honoured under each `think` setting):

| Model | no_think | think=false | think=true |
|---|---|---|---|
| `gemma4:26b` | OK | OK | OK |
| `gpt-oss:20b` | OK | OK | OK |
| `qwen3.5:35b` | OK | NOT_JSON | OK |
| `qwen3.6:35b` | OK | NOT_JSON | OK |

(`gemma4:26b` honours `format` here but fails the *separate* nested-schema
completion test in ground 1.)

### A1.4 What this amendment does NOT change

- **`gemma4:26b`'s general multimodal / vision role is intact.** ADR-001
  selected `gemma4:26b` primarily for vision + handwriting-OCR (the original
  Phase-1 driver). The recommender path is **text-only structured generation**,
  a different capability; superseding gemma4 here says nothing about its
  multimodal selection.
- **`qwen2.5-coder:32b` (code-agent baseline) is untouched** — it was not
  evaluated for the recommender path; the SD-3 survey did not select it.
- **The cloud-fallback posture** (Claude API, consent-gated, non-PII) is
  unchanged; ADR-010 D1 re-affirms it.
- **The structuring call must not pair `think=false` with `format`.** PLAN-0006
  bakes "omit `think` on the structuring call (Pattern B call 2)" into
  `services/engine/llm/`. Recorded here so a future model swap re-checks the
  #15260 interaction (ADR-010 IN-1).

### A1.5 Digest pinning — captured (Code)

This ADR's pinning policy requires a **digest**, not a tag, where
reproducibility matters. The `gpt-oss:20b` digest was captured live from MS-S1
MAX at commit time (`curl http://192.168.1.133:11434/api/tags`, 2026-05-22) and
is recorded here per the digest discipline used for the `gemma4:26b` /
`qwen2.5-coder:32b` rows above:

- **`gpt-oss:20b`** — digest `17052f91a42e` (12-char short form, per the
  Decision-table convention above); size 13793441244 bytes (~12.8 GiB); Ollama
  0.24.0. The full 64-char digest is recoverable via `ollama show gpt-oss:20b`
  on MS-S1 MAX.

The code pin (`Settings.recommender_model`) references the **tag** `gpt-oss:20b`
for day-to-day convenience, as the ADR-001 pinning policy permits; the digest
above is the reproducibility anchor for demo/CI lock-down.

### A1.6 Implementation status

The pin ships as `services/api/config.py::Settings.recommender_model` (default
`"gpt-oss:20b"`) on the **unmerged** branch `feat/plan0006-llm-reasoning-hook`
(committed + pushed, no PR). At the time of this draft, `services/api/config.py`
on `main` still defaults `ollama_default_model = "gemma4:26b"` with no
`recommender_model` field. This amendment and the code pin therefore land
together: per Cray's routing decision (2026-05-22) the amendment commit rides
the `feat/plan0006-llm-reasoning-hook` branch and ships in the PLAN-0006 PR. A
dedicated `recommender_model` setting (not a change to the general
`ollama_default_model`) satisfied PLAN-0006 TODO-B.

### A1.7 References (Amendment 1)

- `docs/adr/0010-llm-reasoning-hook-surface.md` — D1 (local-default backend),
  D5 (LLM-backed `recommend()`), IN-1 (the `think`/`format` verification item
  this amendment closes)
- `docs/plans/done/0006-llm-reasoning-hook-execution.md` — §8 SD-3 (model-pin
  ruling), §7 acceptance (the plan was moved to `done/` on this branch at
  PLAN-0006 Step 8, per CLAUDE.md §6 Plan Flow)
- `.claude/handoffs/session-10/2026-05-22-2355-code-plan0006-kickoff-dispatch-closeout.md`
  — §3 CHECKPOINT-0 verdict grid, §10 `gemma4:26b` nested-schema viability
  addendum
- `.claude/handoffs/session-10/2026-05-22-2230-cowork-plan0006-kickoff-dispatch.md`
  — §7 TODO-A (the amendment trigger), §2 SD-3
- `docs/research/private/2026-05-22-llm-reasoning-hook-local-models.md` — §3/§5
  `gpt-oss:20b` profile; §4.1 Ollama issue #15260
- Ollama issue #15260 — `think=false` + `format` silently drops the schema
  constraint: https://github.com/ollama/ollama/issues/15260
- Branch `feat/plan0006-llm-reasoning-hook` (the `recommender_model` config pin
  lands here)

## Consequences

### Positive
- **Reproducibility:** Demo videos, CI tests, and design partner pilots all run against locked digests — no "works on my machine" drift.
- **No surprise upgrades:** `ollama pull` will not silently change behavior.
- **Cost predictability:** Local-first means no per-token API charges during dev iteration.
- **PDPA compliance moat:** All medical data stays on-prem on MS-S1 MAX (key differentiator for Thai healthcare market).

### Negative
- **Aging risk:** Locked digests will become stale; we must periodically re-evaluate.
- **Manual digest tracking:** Each developer's machine must `ollama pull` the exact digest, which is operationally heavier than tag-based references.
- **Cloud fallback dependency:** Claude API requires internet connectivity and incurs cost — must be used judiciously.

### Neutral
- `qwen2.5-coder:32b` is one major version behind handoff doc's intent (`qwen3-coder`). Functional impact is limited because `qwen2.5-coder:32b` is widely used and known stable; upgrade decision deferred to first re-evaluation trigger.
- `gemma4` family is relatively new; we accept early-adopter risk in exchange for multimodal capability and Apache 2.0 license.

## Alternatives Considered

### Alternative 1: `qwen3-coder` (per original handoff)
- **Pros:** Newer, presumably better
- **Cons:** Not currently installed on MS-S1 MAX; would require pull + re-test; specific availability of stable `qwen3-coder` Ollama image at this date is not confirmed
- **Why rejected:** "Don't change two things at once." Lock what's verified working; upgrade in a separate ADR after Phase 1 stabilizes.

### Alternative 2: Cloud-only (Claude API as primary)
- **Pros:** Highest quality, simplest ops, no model management
- **Cons:** Breaks PDPA / data residency moat for Thai healthcare market; ongoing cost; latency variance; vendor lock-in
- **Why rejected:** The local-first capability **is** the moat. Cloud as fallback is fine; cloud as primary defeats the strategy.

### Alternative 3: Smaller models (gemma 7B / qwen 7B)
- **Pros:** Lower memory footprint, faster inference
- **Cons:** Vision quality on handwritten medical text expected to be insufficient; killer demo (Demo 5: 30-second onboarding) requires high accuracy
- **Why rejected:** MS-S1 MAX has the headroom for 26B/32B class; using smaller models squanders the hardware investment.

## References

- Handoff doc: `/3. Status output จาก MS-S1 MAX .md` (verified model inventory)
- Handoff doc: `vero-lite Project Handoff (Session 1 to Session 2).md` (original tech stack decisions)
- Ollama API docs: https://github.com/ollama/ollama/blob/main/docs/api.md
- Apache AGE + pgvector compatibility: documented in ADR-003 (TBD)

## Implementation Notes

When referencing models in code (`services/api/config.py`):

```python
ollama_default_model: str = Field(
    default="gemma4:26b",
    description="Default LLM model — see ADR-001 (digest 5571076f3d70)",
)
```

When pinning for reproducibility (e.g., in tests or demo configs):

```python
# Use digest pinning for reproducibility
OLLAMA_VISION_MODEL_DIGEST = "5571076f3d70050487b26b341705799e0ab29b808164f90d20d4cf84f699d251"
OLLAMA_CODE_MODEL_DIGEST = "b92d6a0bd47ee79114298de0177bf920c05a706d12633950b3936778492bef41"
```
