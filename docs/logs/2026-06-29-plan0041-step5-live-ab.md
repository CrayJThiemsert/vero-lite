# PLAN-0041 Step 5 — live before/after twin metric (AC-7) — RESULT: PASS

**Date:** 2026-06-29
**Event type:** host-state live run (MS-S1 `gpt-oss:20b`) — confirming evidence, NOT the gate (OQ-D)
**Commit:** this `docs/plan0041-closeout` pair (PLAN-0041 → `done/` + this summary); the lever shipped in #475 (`035af38`) + #476 (`d06d420`)
**Raw evidence (gitignored):** `.claude/benchmark-results/plan0041-step5-live-ab.log`
**Harness:** `tests/services/engine/procedures/test_classify_enrichment_live.py` (`@live`, `OCT_LIVE_MS_S1=1`, N=3)

## Summary

The Cray-gated live before/after run for the PLAN-0041 classify-prompt enrichment lever, on
MS-S1 `gpt-oss:20b` (`192.168.1.133:11434`), over the 26-narrative fixture set. The **before**
arm reconstructs the pre-#475 (un-enriched) prompt; the **after** arm uses the shipped enriched
prompt; both route through the **byte-identical imported guard** (`pipeline._archetype_disagreement`).
N=3 reps, worst reported. **RESULT: PASS** — the pre-committed twin metric is met.

The lever lifts the gated AT-1+AT-3 match-rate from **8–9/11 (before) to a perfect 11/11 (after)
in all 3 reps**, with **zero AT-2 regression** (Arm B 11/11 abstain every rep). The strongest
possible guard-path outcome: all 33 Arm-B abstains came via `label_abstain` (the model itself
labels AT-2 as abstain) — the deterministic backstop (`step_disagreement`) **never fired**,
confirming the band-vs-out-of-scope explainer teaches the model to recognise AT-2 as out-of-scope
at the **label** level (no silent label→backstop shift).

## Key metrics

| rep | Arm A gated (before → after) | Arm B abstain (HARD) |
|---|---|---|
| 0 | 8/11 → **11/11** | **11/11** |
| 1 | 9/11 → **11/11** | **11/11** |
| 2 | 9/11 → **11/11** | **11/11** |
| **WORST** | **after 11/11** (paired before 8/11) | **11/11** |

- **Arm-B guard paths:** `{label_abstain: 33}` (33/33; `step_disagreement` = 0) — the model labels
  AT-2 out-of-scope itself; the deterministic backstop is untested-because-unneeded.
- **AT-1b (reported, not gated):** 11/12 matched.
- **Pre-committed PASS** (worst-rep): Arm B == 11/11 ✓ AND Arm A after ≥ 9/11 (=11) ✓ AND
  after > before (11 > 8) ✓.
- **Runtime:** 156 live calls (26 × 2 × 3), ~46 min (`gpt-oss:20b` structured ~18s/call).

## Significance

The **offline gate** (#475 guard byte-identity + enriched-prompt introspection; #476 fixture
validators) remains the binding bar; this live run is **confirming evidence** (OQ-D). It confirms
the value claim: the prompt-only lever closes the PLAN-0040 AC-B5 ~1-in-3 false-abstain finding
(the ~7/11 reference) to **11/11**, with the moat guard byte-identical and AT-2 zero-regression.

## Reference

- PLAN-0041 (the spine): `docs/plans/done/0041-classify-prompt-enrichment.md` (AC-7; OQ-C/D)
- Pre-committed read + harness: `tests/services/engine/procedures/test_classify_enrichment_live.py`
- Fixture set: `tests/services/engine/procedures/classify_enrichment_fixtures.py`
- The lever (offline gate, merged): #475 (`035af38`), #476 (`d06d420`)
- Adversarial fixture review: in-session (verdict: trustworthy, no blocking defect)

AI-assisted (Claude Code, session 87); no `Co-Authored-By` per CLAUDE.md §7.
