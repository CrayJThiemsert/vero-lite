# ADR-001: LLM Model Baseline (Phase 1)

> **Note (Session 10):** This document was authored during the vet clinic
> vertical (Phase 1 original scope). The vet clinic vertical is now parked
> as Phase 2 (see ADR-005 in the same Batch 2 push); Phase 1 vertical is
> now Operational Control Tower. The architectural decisions in this
> document remain valid and apply to both verticals.

**Status:** Accepted
**Date:** 2026-05-05
**Deciders:** Jirachai Thiemsert (founder)
**Related:** PLAN-001 (starter pack), ADR-002 (network topology)

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

**Pinning policy:** All references to local models in code, configs, and tests **must use the digest, not the tag**, when reproducibility matters (e.g., demo recordings, CI tests, locked dependencies).

For day-to-day development convenience, `gemma4:26b` and `qwen2.5-coder:32b` may be referenced by tag, but lock files (`docker-compose.override.yml`, etc.) freeze digests.

**Out of scope:** `groomflow-unified:latest` is preserved on disk as historical artifact from a prior project but is **not** used by vero-lite. It will not be removed from MS-S1 MAX.

**Re-evaluation triggers:** This ADR is reviewed and potentially superseded if any of the following occur:
1. Quality bar for vision tasks (>90% accuracy on Thai handwritten medical text) is not met by `gemma4:26b` after 4 weeks of testing.
2. A successor model (e.g., `qwen3-coder`, `gemma5`) becomes available and benchmarks show >15% improvement on representative vero-lite tasks.
3. VRAM budget changes due to MS-S1 MAX configuration update.

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
