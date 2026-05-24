# Changelog

## Phase 2 — PLAN-0008 Harness Autonomy Layer (PRs #9–#17)

Probabilistic / classifier-mediated autonomy on top of Phase 1's deterministic hooks. Suite end-state: **389 pass / 6 skip** (Phase 1 baseline 216). All 4 ACs verified.

- **[#9](https://github.com/CrayJThiemsert/vero-lite/pull/9) — Step 1: loop-counter state module.** `_loop_counter.py` (stdlib, ~340 lines), L1–L4 enum, atomic JSON round-trip, session-ID resolution (OQ-A), `last_6_actions` ring buffer. +49 tests.
- **[#10](https://github.com/CrayJThiemsert/vero-lite/pull/10) — Step 2: PreToolUse loop-detect.** Gates L1 (Write/Edit same path ≥6) + L4 (Bash same tokenized cmd ≥6 non-zero). Telegram payload per Cray E.4. +24 tests.
- **[#11](https://github.com/CrayJThiemsert/vero-lite/pull/11) — Step 3: PostToolUse progress observer + Wave 1 wire.** Writer side feeding the counter; L2/L3 fire inline on trigger. Settings registers Wave 1 hooks. +31 tests.
- **[#12](https://github.com/CrayJThiemsert/vero-lite/pull/12) — Step 4: Stop continuation + L1 turn-boundary reset.** `stop_continuation.py` with `stop_hook_active` guard, chain depth tracking, cap-hit policy (OQ-E), classifier stub. Closes L1 false-positive risk. +26 tests.
- **[#13](https://github.com/CrayJThiemsert/vero-lite/pull/13) — Step 5: Sonnet classifier helper + stub swap.** `_sonnet_classifier.py` (stdlib urllib + Messages API, pin `claude-sonnet-4-6`, fail-closed). Cray-supervised live conservatism proof 5/5 (G1/G2/C2 pause, routine proceed). Cost ≈ $0.005.
- **[#14](https://github.com/CrayJThiemsert/vero-lite/pull/14) — Step 6: Wave 2 completion + autonomy-triggers row flips.** Docs flip from "Phase 2 spec" → LIVE with concrete hook attribution.
- **[#15](https://github.com/CrayJThiemsert/vero-lite/pull/15) — Step 5b: classifier config-file fallback.** Defeats Claude Desktop's `ANTHROPIC_API_KEY=""` strip via `~/.claude/.anthropic_api_key` fallback. +10 tests.
- **[#16](https://github.com/CrayJThiemsert/vero-lite/pull/16) — Step 7: Phase 2 integration tests + mypy hook coverage.** 15 E2E scenarios driving real subprocess hooks against a local mock Sonnet server. Pre-commit `mypy` glob extended to `\.claude/hooks/`.
- **[#17](https://github.com/CrayJThiemsert/vero-lite/pull/17) — Step 8: Phase 2 closeout.** AC matrix + L3/L2-reset E2E + `PLAN-0008` moved to `docs/plans/done/`. AC-1 verified 2026-05-25 in supervised live session (≥5 auto-continues, 0 false-positive Telegram pings).

**Next:** PLAN-0009 (Phase 3 — subagent topology, ADR-013 D1 phased end-state).
