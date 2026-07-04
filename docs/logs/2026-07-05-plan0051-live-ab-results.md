# PLAN-0051 Step 5b — live A/B results (reason-then-structure)

**Run:** 2026-07-05, MS-S1 `gpt-oss:20b`, host-state (Cray §8 go — full N=3 both sites).
**Duration:** 2:17:02 (8222 s). **Outcome:** `2 passed` (both hard assertions held); sentinel rc=0.
**Harness:** `test_reason_then_structure_classify_live.py` (AC-6) + `test_reason_then_structure_nl_query_live.py` (AC-7), driven through the shared production drivers (`classify_ab_route` / `translate_ab_query`). Pre-committed reads fixed before the run (§8 / Lesson #0026).

## Headline: **NO measurable lift on either site → REJECT both variants; keep `baseline`.**

The July-2026 research finding ("reason-then-structure lifts constrained-decoding accuracy 10-30%") does **not** replicate on vero-lite's two single-pass structured-output paths. Both paths are already strongly prompted (the classify enriched prompt from PLAN-0041; the detailed translate prompt with explicit operation/filter/metric-kind rules) and `gpt-oss:20b` is a capable reasoning model — so the "format tax" the research warns about is not biting here. This is a **valid null result** by design (the experiment measured whether the lever helps; it did not assume it).

## Classify (AC-6) — worst rep per arm, N=3

| arm | Arm-A gated (AT-1+AT-3, /11) | Arm-B safety (AT-2 abstain, /11) | verdict |
|---|---|---|---|
| baseline | **11/11** | 11/11 | — |
| field_order_flip | 11/11 (+0) | 11/11 | no-lift |
| two_pass | 10/11 (−1) | 11/11 | no-lift |

- **Arm-B moat brake held 11/11 in every arm, every rep** (HARD assert passed) — the reasoning-order lever does not weaken the AT-2 abstain gate. No Arm-B false-accept anywhere.
- **No lift:** baseline is already at the 11/11 ceiling (the shipped enriched prompt maxes the gated set), so there is no headroom; `two_pass`'s −1 is a single-rep noise dip.

## nl_query (AC-7) — field-weighted score on the RAW `_translate` output (SD-1), worst rep per arm, N=3

| arm | mean score (/1.0) | hard-class mean (aggregate-superlative, /1.0) | verdict |
|---|---|---|---|
| baseline | **0.978** | **0.844** | — |
| field_order_flip | 0.965 | 0.844 (Δ +0.000) | no-lift |
| two_pass | 0.978 | 0.844 (Δ +0.000) | no-lift |

- **Regression floor OK** for both variants (neither fell below baseline − `REGRESSION_FLOOR_TOLERANCE`).
- **Hard-class Δ = +0.000** for both — the reasoning-order lever does **not** improve retention of `group_by` + `measured_kind` on "which X is most Y" at the worst rep. (`two_pass` reached 0.988 mean / 0.889 hard-class in one rep, but the pre-committed read is the worst rep, where it ties baseline at 0.844.)

## Recommendation (SD-6, ratified: measure-only)

**REJECT** `field_order_flip` and `two_pass` on **both** sites. The shipped default stays `baseline` — **no production default is changed by this PLAN** (SD-6). The experimental arm plumbing + corpora + harness remain (behind the `baseline`-default `arm` param) as reusable scaffolding, should a future model/prompt change reopen the question. No new ADR (SD-5); no adoption follow-up is warranted by this evidence.

## Notes / caveats

- The corpora are small + hand-authored (26 classify narratives / 27 nl_query questions) and the live model is non-deterministic — read the numbers as "X → Y on this corpus", never a population rate.
- Runtime was ~4× the pre-run estimate (~2h vs ~30 min): `gpt-oss:20b` per-call latency on these longer prompts (+ two-pass reasoning calls + nl_query validate-and-retry) is well above the structured-judgment benchmark's ~3.5 s/call. Future live A/B runs on this harness should budget ~2 h for full N=3 both sites.
- Offline gate (the binding acceptance bar, AC-1..AC-5) was green throughout; this live run is confirming evidence, not the gate (LOCKED-5).

*Evidence artifacts (gitignored): `.claude/benchmark-results/ab-live-step5b.{log,done}`. AI-assisted (Claude Code).*
