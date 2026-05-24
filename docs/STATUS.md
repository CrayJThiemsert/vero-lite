---
last_updated: 2026-05-24T16:30:00+07:00
session: 10
current_batch: PLAN-0008 Step 1 (loop-counter state module + tests) MERGED via PR #9 (`2b303a0`); +49 unit tests (216 → 265 pass); stdlib-only module ships schema + atomic I/O + L1–L4 normalization + counter ops; Step 2 (PreToolUse loop-detect hook) next
current_actor: code (Step 2 starting)
blocked_on: nothing
next_action: PLAN-0008 Step 2 — `.claude/hooks/pretooluse_loop_detect.py` (read counter, gate on L1/L4 ≥6, fire telegram with Cray-E.4 payload `{loop_type, target, last_6_actions}`, deny) on branch `feat/plan0008-step2-pretooluse-loop-detect`
head_commit: 2b303a0
recent_commits: [2b303a0, e20a6f3, 473f07b, ec5e2ae, 5a34ab0, b53763d, a65f5d6, da4f91d, 21f0f7a, 7f00d18]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

**Session 10 — PLAN-0008 Step 1 (loop-counter state module) MERGED.**
PR #9 landed on `main` as `2b303a0` (single `feat(claude)` commit
`e20a6f3` + merge commit). New `.claude/hooks/_loop_counter.py` (~340
lines, stdlib-only) ships the Phase 2 state primitives: `LoopType`
enum (L1–L4 mapping to `.claude/autonomy-triggers.md`),
`LoopCounter`/`CounterEntry`/`ActionRecord` dataclasses with explicit
JSON round-trip, atomic `load_counter`/`save_counter` (tmpfile +
`os.replace`, tolerant of missing/empty/malformed/wrong-root files),
4 normalization helpers (file path reusing C4 hook idiom for
Windows-UNC, pytest nodeid stripping `[param]` suffix, error signature
stripping 6 volatile patterns, bash command tokenization), session-ID
resolution per **OQ-A** (`$CLAUDE_SESSION_ID` → `pid-<PID>` →
`uuid-<UUID>` fallback chain), counter ops (`increment` with
`last_6_actions` ring buffer per Cray E.4 payload contract, `reset`
removes entry, `get_count`, `has_triggered` against
`LOOP_TRIGGER_THRESHOLD=6`). 49 new tests
(`tests/handoffs/test_loop_counter_state.py`) incl concurrent-write
race (writer + reader threads, no partial reads); `pytest` 265 pass /
5 skip (Phase 1+C4 baseline 216 → 265); `ruff` + `mypy --strict` +
`detect-secrets` clean. **Next: Step 2** —
`.claude/hooks/pretooluse_loop_detect.py` (read state, gate on L1/L4
≥6, fire telegram, deny) on branch
`feat/plan0008-step2-pretooluse-loop-detect`.

**Prior — PLAN-0008 (Phase 2 harness autonomy layer) DRAFTED +
MERGED.** PR #8 landed on `main` as `ec5e2ae` (3 commits: draft
`b53763d` + OQ resolutions `5a34ab0` + merge). Phase 2 scope = three
coupled pieces layering the probabilistic / classifier-mediated engine
on top of Phase 1's deterministic hooks: (1) **`Stop` continuation
loop** with `stop_hook_active` re-entry guard +
`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP=8` chain cap; (2) **Sonnet
pause/proceed classifier** reading `.claude/autonomy-triggers.md`
verbatim (fail-closed, model pin `claude-sonnet-4-6`); (3) **stateful
loop-detection L1–L4** via `.claude/state/loop-counter.json`
(gitignored; payload `{loop_type, target, last_6_actions}` per ADR-013
/ Cray E.4). 4 ACs incl **AC-4 Phase 1 regression-free** (16-case
bypass-immune commit-deny + handoff-validator + C4 research-path-deny
all stay green). All 7 OQs (A–G) adjudicated by Cray on 2026-05-24:
A (session-ID = `$CLAUDE_SESSION_ID` → PID → UUID fallback), B
(Sonnet pin), C (registry path-reference, not inline), **D
(auto-handoff DEFERRED to PLAN-0009** — K-1/K-2 forcing fact still
blocks Cowork read-side so auto-draft does not reduce the Cray-paste
relay; Plan subagent = right author per ADR-013 D1; surface bloat),
E (BLOCK_CAP hit → pause + Telegram `"cap reached"`), F (no Phase 2
pre-filter; cost telemetry is the trigger), G (CI mocks Sonnet +
opt-in `RUN_LIVE_SONNET_TESTS=1`). Status: **Ready for execution**.
**Next: Step 1** — `.claude/state/` directory + `loop-counter.json`
schema + `.gitignore` extension + atomic-write tests, on branch
`feat/plan0008-step1-state-design`. Cowork-drafted under interim
ADR-009 D1 (ADR-013 D1 phasing); Code committed per ADR-009 D2.

**Prior — Research-path enforcement (C4 hook) MERGED.** PR #7
landed on `main` as `da4f91d` (single `feat(claude)` commit `21f0f7a`
+ merge commit). Third deterministic Phase-1 row in `.claude/autonomy-triggers.md`
alongside G5 (`pretooluse_git_deny.py`) and H1 (`posttooluse_validate_handoff.py`):
`.claude/hooks/pretooluse_research_path_deny.py` blocks `Write`/`Edit`
under `docs/research/` outside `docs/research/private/**`. Motivation
= N=2 violations of the documented rule (`cowork_tab_instructions.md`
line 192 + `.gitignore` lines 49-51) in 8 days — Lesson #5 §10.5
(2026-05-15 audit baseline, `docs/strategy/public/` drop) +
2026-05-23 `chat_harness_extension_points_analyzed.md` (detected
+ corrected during PLAN-0007 post-merge cleanup). Applies ADR-013 D2
precedent: when documentation alone fails twice, promote to
deterministic hook reinforcement. 20 new unit tests (allow private/
+ strategy/, deny public/ + bare research/ + arbitrary subdirs, path
normalization for Windows UNC both directions, edge cases for non-Write
tools + malformed stdin); `pytest` 216 pass / 5 skip; `ruff` + `mypy`
+ `detect-secrets` clean. Cowork research workflow unchanged for the
happy path (private/ writes allowed); only the off-policy writes are
blocked at the hook layer.

**Prior — Harness autonomy layer (ADR-013 + PLAN-0007) Phase 1
MERGED.** PR #6 landed on `main` as `b2ea9b8` (9 commits: 6 Phase A
governance + 3 Phase B execution). The `.claude/` autonomy layer is
live: deterministic PreToolUse deny on `git commit|push|merge` from
non-Code sessions (CLAUDE_TIER env marker, bypass-immune across 16
test cases incl `bash -c`, backtick, `git -C`, inline env spoof);
Notification hook → `tools/notify/telegram.sh` (env-var-only Telegram
bridge with graceful no-op when unset, live ping verified end-to-end
by Cray); PostToolUse handoff frontmatter auto-validator (Write|Edit
on `.claude/handoffs/**`, blocks on hard error); `.claude/autonomy-triggers.md`
registry (G1–G5 governance, C1–C3 config/dep/wording, H1 handoff,
L1–L4 loop-detect rows flagged "Phase 2 enforcement"). 28 new unit
tests; `pytest` 196 pass / 5 skip; `ruff` + `mypy` + `detect-secrets`
clean.

**OQ-3 resolution (Code-decided, ADR-013).** Session-identity signal =
env var `CLAUDE_TIER=code`, set by Cray on the launching shell.
Bypass-immune against `permission_mode=bypassPermissions` (hook
decisions run regardless of permission_mode) and against inline
command spoofing (hook reads its own process env, not the tool_input
string). Windows-host setup: `setx CLAUDE_TIER code` + `setx WSLENV
CLAUDE_TIER/u:TELEGRAM_BOT_TOKEN/u:TELEGRAM_CHAT_ID/u`. Token rotated
on 2026-05-23 after one-time screenshot leak in chat (Cray-handled
via `@BotFather`).

**Next:** PLAN-0008+ for Phase 2 entry conditions reached
(`Stop` continuation loop + Sonnet pause/proceed classifier reading
`.claude/autonomy-triggers.md` + stateful loop-detection state file +
subagent topology + MCP `vero-bridge` transport). Drafting cadence
per Cray; the deterministic safety pieces (commit deny, handoff
auto-validation) and the AFK channel are now load-bearing — Phase 2
adds the probabilistic / classifier-mediated layer on top.

---

**Prior — PLAN-0006 (LLM reasoning-hook execution) MERGED.** The brain
swap is done: `services/engine/recommender.py::recommend()` is now LLM-backed
(ADR-010 D5) — **merged to `main` via PR #5 (`68053fe`)**, 12 commits incl.
ADR-001 Amendment 1. Steps 0-8 of the Phase-1 kickoff dispatch all landed:
`ruff` + `mypy --strict` clean, **173 passed / 0 skipped** (with live
Postgres), coverage **94.56%** (new `services/engine/llm/` modules 92-100%).

**CHECKPOINT-0 (Step 0 / ADR-010 IN-1)** — verified live on MS-S1 MAX:
Ollama **0.24.0**, pin **`gpt-oss:20b`** (Cray-adjudicated; gpt-oss:20b and
gemma4:26b both honour the `format` schema constraint under every `think`
setting). The Ollama #15260 `think=false`+`format` bug is **still live for
the Qwen3.x family** but absent for gpt-oss:20b + gemma4:26b. Binding rule:
the structuring call omits `think` — never `think=false` with `format`.

New module set (PLAN-0006) — `services/engine/llm/`: `client.py` (async
Ollama wrapper), `prompt.py` (assembly + IN-2 injection containment),
`structured.py` (constrained generation + validate-and-retry + semantic
checks + the SC-1 reduced `LlmJudgment` sub-schema), `trace.py` (hybrid
reasoning trace). `recommender.py` rewired — `async`, with the deterministic
rule body retained as the fail-safe; `config.py` extended; one `await` at
the API call site; an eval harness + golden traces under
`tests/services/engine/eval/`.

**Follow-ons:** **TODO-A is done** — ADR-001 Amendment 1 (`30d2c8e`) pins
`gpt-oss:20b` + Ollama 0.24.0 for the recommender path (superseding
`gemma4:26b` for that path only). TODO-B (config default) is
satisfied — Step 1 added a dedicated `recommender_model` setting. **SC-1**
resolved by Code: constrained generation targets the reduced `LlmJudgment`
sub-schema; the harness composes the full (unchanged) ADR-007 D2 envelope.
A Step-7 live capture surfaced + fixed a `suggested_handler` defect (the
model invented unregistered handlers — now enum-constrained to the registry).

**Prior this session — PLAN-0005 Phase 2 (OCT Engine Runtime Layer) MERGED**
(PR #4, `c646bab`) — the runtime the LLM hook plugs into. **109 passed**,
coverage **95.34%**. Module / endpoint set (PLAN-0005 §11):

- `services/engine/data_adapter.py` — `DataAdapter` Protocol (ADR-007 D1)
- `services/engine/actions.py` — `RecommendedAction` runtime envelope (ADR-007 D2)
- `services/engine/registry.py` — `VerticalRegistry` (OQ-6 explicit registration)
- `services/engine/recommender.py` — rule-based recommender + minimal approval
  gate (`recommend` / `approve` / `reject` / `execute`; OQ-2/OQ-3)
- `verticals/energy/data_adapter/` — `EnergySyntheticAdapter` + synthetic dataset
- `verticals/energy/handlers.py` — energy `echo` action handler
- `services/db/` — async SQLAlchemy ORM (6 energy tables), session, and the
  envelope→entity persistence projection
- `alembic/` — async migration env + first revision (the six energy tables)
- `services/api/` — three-layer wiring: lifespan-registered energy vertical +
  the action-loop router: `GET /objects/{type}`, `GET /recommendations`,
  `POST /recommendations/{id}/approve`, `POST /recommendations/{id}/execute`;
  `/health` preserved

All six §8 Open Questions (Cray-adjudicated 2026-05-21) are honoured. Persistence
(OQ-4) is real `postgres:16-alpine` via SQLAlchemy 2.0 async + Alembic + asyncpg;
the §7.6 tests run against a live DB and the DDL/ORM parity test (C-1/R6) guards
type drift. The §8.1 deferred-foundational revisit register is in Active TODOs.

Tooling note: `ruff` + `mypy` are now pinned in `pyproject.toml` to the
pre-commit gate versions (`9d461f2`) — closes a `.venv`-vs-gate version skew.
The pre-commit `mypy` hook now also covers `^(services|verticals)/`
(`9dd1470`), not just `services/` — closes the flagged coverage gap.

---

## Prior focus (archived)

PLAN-003 Phase 1 (ontology engine + 5 emitters) and PLAN-0005 Phase 2
(OCT engine runtime layer) are both **merged and moved to
`docs/plans/done/`**. The Cowork-as-Tier-1 trial that ran as the
test-bed across those batches **concluded** — ratified permanently by
**ADR-009** (Cowork = merged Tier 0 + Tier 1 workspace; commits stay
Code-exclusive). PLAN-004 Phase A (handoff frontmatter schema + tooling)
also landed; Phase B/C remain deferred (backlog). Full detail lives in
`docs/plans/done/`, the Recent Decisions table below, and git history.

## Recent Decisions (last 5)

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-05-24 | **PLAN-0008 Step 1 (loop-counter state module) MERGED** — PR #9 → `main` (`2b303a0`), single `feat(claude)` commit `e20a6f3` + merge. New `.claude/hooks/_loop_counter.py` (~340 lines, stdlib-only) ships the schema + atomic I/O + 4 normalization helpers (file path / pytest nodeid / error signature / bash command) + session-ID resolution per **OQ-A** + counter ops with `last_6_actions` ring buffer per Cray E.4 payload contract. Step 2 (PreToolUse loop-detect hook) READS this module's state; Step 3 (PostToolUse progress observer) WRITES it. 49 new tests (`tests/handoffs/test_loop_counter_state.py`) incl concurrent-write race; pytest 265 pass / 5 skip (was 216 / 5); ruff + mypy --strict + detect-secrets clean. Closeout: this STATUS row | `2b303a0` (PR #9) / `.claude/hooks/_loop_counter.py` |
| 2026-05-24 | **PLAN-0008 (Phase 2 harness autonomy layer) DRAFTED + MERGED** — PR #8 → `main` (`ec5e2ae`), 3 commits (`b53763d` draft + `5a34ab0` OQ resolutions + merge). Phase 2 layers probabilistic / classifier-mediated engine on top of Phase 1 deterministic hooks: `Stop` continuation loop (`stop_hook_active` + `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP=8`) + Sonnet pause/proceed classifier (fail-closed, pin `claude-sonnet-4-6`, reads `.claude/autonomy-triggers.md` verbatim) + stateful loop-detection L1–L4 via `.claude/state/loop-counter.json` (gitignored; payload `{loop_type, target, last_6_actions}` per Cray E.4). 4 ACs incl **AC-4 Phase 1 regression-free** (16-case bypass-immune commit-deny + handoff-validator + C4 stay green). All 7 OQs adjudicated by Cray (A/B/C/E/F/G approve Code recommendations; **D auto-handoff Code→Cowork DEFERRED to PLAN-0009** — K-1/K-2 forcing fact blocks Cowork read-side so auto-draft does not reduce the human-relay bottleneck ADR-013 §Context targets; Plan subagent = right author per ADR-013 D1; surface bloat = step-sized design comparable to classifier). Status: Ready for execution. Step 1 (`.claude/state/` design + loop-counter schema) next on `feat/plan0008-step1-state-design`. Cowork-drafted under interim ADR-009 D1 (ADR-013 D1 phasing); Code committed per ADR-009 D2 | `ec5e2ae` (PR #8) / `docs/plans/0008-harness-autonomy-layer-phase-2.md` |
| 2026-05-24 | **Research-path enforcement (C4 hook) MERGED** — PR #7 → `main` (`da4f91d`). New `.claude/hooks/pretooluse_research_path_deny.py` blocks `Write`/`Edit` under `docs/research/` outside `docs/research/private/**`. Third deterministic Phase-1 row in `.claude/autonomy-triggers.md` (C4, alongside G5 git-deny + H1 handoff-validator). Trigger = N=2 violations of the documented rule (`cowork_tab_instructions.md` line 192 + `.gitignore` lines 49-51) in 8 days: Lesson #5 §10.5 (2026-05-15, `docs/strategy/public/` drop) + 2026-05-23 (`chat_harness_extension_points_analyzed.md`, detected during PLAN-0007 post-merge cleanup). Applies ADR-013 D2 precedent (documented-rule violation twice → promote to deterministic hook). 20 new tests (216 pass / 5 skip total, +20 from baseline); Windows-UNC path-normalization robust to host (backslash→forward-slash before pathlib). Closeout: this STATUS row | `da4f91d` (PR #7) / `.claude/hooks/pretooluse_research_path_deny.py` |
| 2026-05-23 | **PLAN-0007 Phase 1 (Harness autonomy layer) MERGED** — PR #6 → `main` (`b2ea9b8`), 9 commits (6 Phase A + 3 Phase B). All three ACs green incl live: AC-2 bypass-immune commit boundary verified across 16 test cases (inline `CLAUDE_TIER=code` env-spoof attempt, `bash -c`, backtick chains, `git -C path`, env prefix, `&&` chains — all denied; legitimate Code-tier commit allowed); AC-1 AFK Telegram ping verified end-to-end by Cray after token rotation + `WSLENV` setup; AC-3 handoff frontmatter auto-validator blocks on hard errors. OQ-3 resolved by Code: env marker `CLAUDE_TIER=code` (rejected file marker spoofable by `touch && commit`, cwd heuristic too coarse, settings-scope has no per-session distinction). `.claude/autonomy-triggers.md` registry shipped with G1–G5 / C1–C3 / H1 active and L1–L4 loop-detect rows flagged "Phase 2 enforcement". Plan moved to `docs/plans/done/`. Phase 2–4 (Stop continuation loop + Sonnet classifier + stateful loop-detection + subagent topology + MCP bus) → PLAN-0008+ | `b2ea9b8` (PR #6) / `docs/plans/done/0007-harness-autonomy-layer-phase-1.md` |
| 2026-05-23 | **ADR-013 (Autonomy axis relocation, Direction B) ACCEPTED + PLAN-0007 committed + T3–T6 follow-ons landed** — Cray ratified Direction B in free-form and adjudicated E.1–E.5 + OQ-1/2/3 (OQ-3 PreToolUse session-identity mechanism delegated to Code). ADR-013 D1 amends ADR-009 D1 (execution-automation axis relocates to Code + subagents; Cowork retained as advisory governance drafter per OQ-1); D2 preserves + reinforces "only Code commits" via deterministic PreToolUse deny hook (bypass-immune); D3 extends ADR-012 (free-form venues retained); D4 classifier=Sonnet + registry `.claude/autonomy-triggers.md`; D5 Telegram `@vero_tg_bot` env-var token. Branch `feat/plan0007-harness-autonomy-phase1` carries 5 governance commits (`770adf5` ADR-013, `c00dc98` PLAN-0007, `c45526b` CLAUDE.md §6 T3, `e64a4d2` tier instructions T4, `8eebe09` ADR-009/012 pointers T5). CLAUDE.md edit (T3) is constitutional — restart-bridge applies (Lesson #5 §1). Cowork-drafted, Code-committed per ADR-009 D2 | `8eebe09` / `docs/adr/0013-autonomy-axis-relocation.md` + `docs/plans/0007-harness-autonomy-layer-phase-1.md` |
| 2026-05-22 | **PLAN-0006 (LLM reasoning-hook) MERGED** — PR #5 merged to `main` (`68053fe`): `recommend()` is now LLM-backed (`gpt-oss:20b`, two-call Pattern B, deterministic rule fail-safe retained), new `services/engine/llm/` package + eval harness; ADR-001 Amendment 1 rode the same PR. Code-reviewed, no blockers; 173 passed / 0 skipped, coverage 94.56%. Post-merge: worktree + branch cleaned up | `68053fe` (PR #5) |
| 2026-05-22 | **ADR-001 Amendment 1 — `gpt-oss:20b` recommender-path pin (PLAN-0006 TODO-A)** — amends ADR-001's Primary-multimodal row for the OCT recommender path only: `gpt-oss:20b` + Ollama 0.24.0 supersedes `gemma4:26b`. Two independent grounds — `gemma4:26b` cannot complete the recommender's real nested-schema structuring call (>600s timeout vs gpt-oss 41s), and the still-live Ollama #15260 `think`/`format` interaction. gemma4's vision/multimodal role + `qwen2.5-coder:32b` untouched; cloud-fallback posture unchanged. Cowork-drafted (ADR-009 D1), Code-reviewed + committed onto the PLAN-0006 branch (Cray's routing call); live digest `17052f91a42e` captured | `30d2c8e` / `docs/adr/0001-llm-model-baseline.md` |
| 2026-05-22 | **PLAN-0006 (LLM reasoning-hook execution) EXECUTED — the brain swap** — `recommend()` is now LLM-backed (two-call Pattern B on `gpt-oss:20b`, fail-safe to the retained rule path). New `services/engine/llm/` package (client/prompt/structured/trace) + eval harness. CHECKPOINT-0 pinned `gpt-oss:20b` on Ollama 0.24.0 (#15260 still live for Qwen3.x). SC-1 resolved (reduced `LlmJudgment` sub-schema; ADR-007 D2 envelope unchanged). A Step-7 live capture surfaced + fixed a `suggested_handler` defect. 8 commits on `feat/plan0006-llm-reasoning-hook` (unmerged); 168 passed / 5 skipped, coverage 94.56%. TODO-A (ADR-001 amendment for the pin) pending Cray | `4f13b50`..`2fe1056` |
| 2026-05-22 | **PLAN-0006 (LLM reasoning-hook execution) drafted + committed** — the execution plan for the ADR-010 brain swap; Cowork-authored (Tier 1), Code R2-reviewed (fact-pack verified vs the live repo). Cray adjudicated SD-1..SD-5: async `recommend()` + retry 3, two-call Pattern B trace, gpt-oss-20b primary (provisional, Step-0-gated), raw structured-output (no new dep), seam-only hosted fallback. Next = Phase-1 kickoff dispatch | `d3a781e` / `docs/plans/0006-llm-reasoning-hook-execution.md` |
| 2026-05-22 | **C-2 Suffix-enum divergence RESOLVED — option α (expand the enum)** — Cray adjudicated α: `tools/handoffs/_schema.py:Suffix` gains `dispatch`/`completion`/`consultation`; PLAN-004 D4 + `handoff-frontmatter-schema.md` register them; 2 regression tests. Closes the schema ↔ `cowork_tab_instructions.md` divergence. `discussion` deliberately excluded (ADR-012 carries it via `phase:`). | `db9c5ed` |
| 2026-05-22 | **ADR-012 (Cowork second free-form tier) ACCEPTED** — amends ADR-009 D5: Cowork gains a second free-form role (Tier-1b — repo-grounded discussion / thinking-partner / informal code review) alongside Chat, which is **retained** (D5 extended, not revoked). D2 routing: Chat = repo-blind blue-sky, Cowork = repo-grounded. Adopted by Cray as a guarded trial (option α), regression triggers R-FF1..R-FF4 as exit criteria; commit authority stays Code-exclusive. T1 ADR + T2-T6 follow-on amendments (cowork/chat instructions, ADR-009 D5 pointer, CLAUDE.md §6, this STATUS row) committed by Code | `7916b39` / `docs/adr/0012-cowork-second-freeform-tier.md` |
| 2026-05-22 | **ADR-010 (LLM reasoning-hook surface) ACCEPTED** — five decisions fixing how an LLM replaces the rule recommender: D1 local-LLM-default + Claude-API consent-gated fallback (Cray-ratified), D2 schema-constrained output + retry, D3 hybrid reasoning trace, D4 approval gate = guardrail, D5 `recommend()` LLM-backed under the same signature; ADR-007 D2 envelope unchanged. Drafted by Cowork from two Tier-0 briefs; next = PLAN-0006 | `48fe240` / `docs/adr/0010-llm-reasoning-hook-surface.md` |
| 2026-05-21 | **mypy pre-commit gate extended to `verticals/`** — the hook now covers `^(services\|verticals)/`, not just `services/`; closes the flagged coverage gap (verified `pre-commit run mypy --all-files`) | `9dd1470` |
| 2026-05-21 | **PLAN-0005 Phase 2 — OCT Engine Runtime Layer MERGED** (PR #4, 13 commits) — DataAdapter Protocol + RecommendedAction envelope + vertical registry + rule-based recommender/approval gate + energy synthetic adapter + persistence (real `postgres:16-alpine`, SQLAlchemy 2.0 async + Alembic) + three-layer API wiring + end-to-end action loop; 109 tests, coverage 95.34%; six §8 OQs honoured; DDL/ORM parity test (C-1/R6) green; PLAN-003 + PLAN-0005 moved to `done/` | `c646bab` (PR #4) / `docs/plans/done/0005-oct-engine-runtime-layer.md` |
| 2026-05-21 | **ADR-009 ACCEPTED + 7-commit atomic PR #3 MERGED (`08117d5`)** — Cowork becomes Tier-0+1 merged workspace (dispatch/ADR/PLAN authoring), Chat narrows to free-form discussion only (D5 b), commit authority stays Code-exclusive (D2), K-1/K-2 workflow codified durably (Lesson #8). Hypothesis from parent discussion (2026-05-20-1235) supported by round 1 + round 2 trials (PASS / PASS). Commits 7c5c728 (ADR-009) → 601cdd4 (ADR-007 pointer T7) → 6759949 (cowork_tab T3) → dd9fe76 (chat_tab T4) → b6bf400 (Lesson #8 T6) → af6f858 (CLAUDE.md §6 T2) → e9f499b (STATUS T5). **Cray TODO:** re-paste cowork/chat tier instructions into Claude Desktop UI (repo canonical, UI sync target per CLAUDE.md §4) | `08117d5` / `docs/adr/0009-cowork-tier1-tier-topology.md` |
| 2026-05-20 | **PLAN-003 Phase 1 merged** (PR #2) — `services/engine/` package + 5 emitters + `verticals/energy/ontology/energy_v0.yaml` (ADR-008 D2 grammar; 6 object_types + 7 link_types) + L1 commit-time gate + `vero-lite` entry-point; 24 engine tests; coverage 94.06%; ADR-008 D2 binding per dispatch R-K1; PLAN-003 §8.6 list-of-dicts illustration is REJECTED at L1 (schema-fidelity guarantee) | `30619b8` |
| 2026-05-20 | PLAN-003 Phase 1 kickoff dispatch authored by Cowork-as-Tier-1 (trial test-bed); Code R2 pre-execution PASS; mid-execution C4=0 (no Lesson #6 firings during commits 1-7); trial-protocol §7.3 adjudication queued for Cray | `.claude/handoffs/session-10/2026-05-20-1530-cowork-plan003-phase1-kickoff-dispatch.md` |
| 2026-05-20 | PLAN-003 plan doc landed — `docs/plans/0003-ontology-engine.md` (427 lines); Phase 1 only (5 emitters: Pydantic+SQL+JSON Schema+MCP+TS-light); Typer CLI + ruamel.yaml parser + jsonschema; Alert↔OperationalEvent via explicit join object type (ADR-008 D4 stays; `many_to_many` deferred); coverage ≥70% aspirational (R-8); 3 J-class surfaces logged in dispatch closeout | `a7c68a2` |
| 2026-05-20 | PLAN-004 Phase A Batch 2 COMPLETE — Step 2a (20 files) + 2b.1 (12 renames + ref-graph, 5-ratification surface→re-dispatch chain) + 2b.2 (post-recovery, single-pass). Handoff-class schema-FAIL = `{}` | `ad81e7e` (2b.2 anchor), `098f8cd` (2b.1), `7f5035f` (2a) |
| 2026-05-20 | Strategic pivot — Option-1: pause PLAN-004 Phase B/C, prioritize PLAN-003 (Ontology Engine = the moat) | Cray decision 2026-05-20 |
| 2026-05-20 | Chat dispatch tooling/schema pre-verification protocol codified (operational layer; durable Lesson #8 mint deferred post-Phase-A per Q3=A) | `be38bce` `docs/conventions/chat_tab_instructions.md` |
| 2026-05-19 | PLAN-004 v2 Phase A Batch 1 landed | Schema doc + tools/handoffs/{_schema,validate_handoff,handoff_status}.py + ≥14 tests + runbook cross-link + CLAUDE.md §10 widening (docs/ → docs/ + tools/, Option B per Code midflight) | `9afde79` |
| 2026-05-17 | §11 Transcript Handoff ratified — Lesson #5 §2 "Cray-direct constitutional codification path" sub-rule + runbook §4 refresh + runbook §2 helper | `8d570b4` |
| 2026-05-16 | CLAUDE.md §11 "Transcript Handoff" constitutional subsection promoted — first instance of Cray-direct codification path (Lesson #5 §2 sub-rule) | `dd65d9b` |
| 2026-05-16 | Transcript tooling + runbook landed — `tools/handoffs/render_transcript.py` (stdlib-only, mypy-strict) + tests + `docs/runbooks/transcript-handoff.md` | `98e5591` |
| 2026-05-16 | Lesson-numbering offset sweep — `Lesson #12/#13/#14` → `#2/#3/#4` across repo (full normalization) | `c85a595` |
| 2026-05-16 | Lesson #5 audit baseline applied — `docs/lessons/0005-tier-system-audit-2026-05-15.md` (10 findings, tier-system audit); in-repo references normalized | `8274a66` |
| 2026-05-15 | Governance mini-batch — CLAUDE.md §1 precedence + §6 4-tier table + §11 Tier 2 ops; `docs/conventions/{chat,cowork}_tab_instructions.md` canonicalized | `ac3baf3` |
| 2026-05-13 | ADR-007 (OCT engine contracts) + ADR-008 (YAML ontology specification) — both Accepted | `docs/adr/0007-oct-engine-contracts.md`, `docs/adr/0008-yaml-ontology-specification.md` |
| 2026-05-13 | Cowork Tier 0 first deliverable — Palantir Foundry ontology reference brief (validates ADR-008's 4-tier model; cited from ADR-008 §Context as influencing reference) | `docs/research/private/2026-05-13-palantir-ontology-reference.md` |
| 2026-05-11 | ADR-006 — Vertical Plugin Architecture (D1–D4 + 5 core patterns; template-first multi-vertical) | `docs/adr/0006-vertical-plugin-architecture.md` |
| 2026-05-11 | ADR-005 — Strategic Pivot from SMB vet clinic to Operational Control Tower (vet clinic parked as Phase 2) | `docs/adr/0005-strategic-pivot-to-oct.md` |
| 2026-05-10 | ADR-004 closed — GitHub noreply alias as canonical author email (provisional) | `docs/adr/0004-canonical-author-email.md` |
| 2026-05-10 | Worktree mode policy codified in CLAUDE.md §6 (per Lesson #3) | `CLAUDE.md` §6 |
| 2026-05-10 | Handoff rotation policy codified in runbook | `docs/runbooks/claude-code-chat-handoff.md` |

## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [x] **ADR-007** — OCT engine contracts (DataAdapter, RecommendedAction, three-layer wiring) *(Session 10 Batch 3)*
- [x] **ADR-008** — YAML ontology specification (5 base types, JSON Schema validation) *(Session 10 Batch 3)*
- [x] **`.gitignore` extension** — add `docs/research/private/` (Cowork closeout flag #1) *(Session 10 Batch 3-prep)*
- [x] **PLAN-0005 Phase 2 — OCT Engine Runtime Layer** — DataAdapter Protocol + RecommendedAction envelope + vertical registry + rule-based recommender/approval gate + energy synthetic adapter + persistence (postgres:16-alpine, SQLAlchemy/Alembic) + three-layer API wiring + e2e action loop; merged PR #4 (`c646bab`) *(Session 10, 2026-05-21)*
- [x] **ADR-010 — LLM reasoning-hook surface** — D1 inference backend Cray-ratified (local LLM default + Claude API consent-gated fallback); D2–D5 recommended; ADR-007 D2 envelope unchanged *(Session 10, 2026-05-22; commit `48fe240`)*
- [x] **PLAN-0006 — LLM reasoning-hook execution** — EXECUTED. Steps 0-8 of the Phase-1 kickoff dispatch done on `feat/plan0006-llm-reasoning-hook` (8 commits `4f13b50`..`2fe1056`, **unmerged**); CHECKPOINT-0 pinned `gpt-oss:20b` / Ollama 0.24.0; new `services/engine/llm/` package + eval harness; `ruff` + `mypy --strict` clean, 168 passed / 5 skipped, coverage 94.56%. Closeout: `.claude/handoffs/session-10/2026-05-22-2355-code-plan0006-kickoff-dispatch-closeout.md`. *(Session 10, 2026-05-22)*
- [x] **PLAN-0008 Step 1 — loop-counter state module (MERGED)** — PR #9 → `main` (`2b303a0`); new `.claude/hooks/_loop_counter.py` ships stdlib-only schema + atomic I/O + 4 normalization helpers (L1–L4) + session-ID resolution per OQ-A + counter ops with `last_6_actions` ring buffer. 49 new tests; pytest 265 pass / 5 skip; ruff + mypy --strict + detect-secrets clean. **Step 2 next:** `.claude/hooks/pretooluse_loop_detect.py` on `feat/plan0008-step2-pretooluse-loop-detect`. *(Session 10, 2026-05-24)*
- [x] **PLAN-0008 — Harness autonomy layer Phase 2 (DRAFT MERGED)** — PR #8 → `main` (`ec5e2ae`), 3 commits (`b53763d` draft + `5a34ab0` OQ resolutions + merge). Phase 2 scope: `Stop` continuation loop + Sonnet pause/proceed classifier reading `.claude/autonomy-triggers.md` verbatim + stateful loop-detection L1–L4 via `.claude/state/loop-counter.json`. 4 ACs incl AC-4 Phase 1 regression-free. All 7 OQs (A–G) adjudicated by Cray 2026-05-24 (Code recommendations approved; **OQ-D auto-handoff DEFERRED to PLAN-0009** per K-1/K-2 forcing fact + Plan subagent role + surface bloat). Status: Ready for execution. **Step 1 next:** `.claude/state/` design + `loop-counter.json` schema + `.gitignore` extension + atomic-write tests on `feat/plan0008-step1-state-design`. *(Session 10, 2026-05-24)*
- [x] **Research-path enforcement (C4 hook)** — MERGED. PR #7 → `main` (`da4f91d`); new `.claude/hooks/pretooluse_research_path_deny.py` deterministically blocks `Write`/`Edit` under `docs/research/` outside `docs/research/private/**`. Registered as C4 in `.claude/autonomy-triggers.md` next to G5 + H1. Trigger = N=2 documented-rule violations (Lesson #5 §10.5 + 2026-05-23 `chat_harness_extension_points_analyzed.md`) applying ADR-013 D2 precedent. 20 new tests; pytest 216 / 5 skip. *(Session 10, 2026-05-24)*
- [x] **PLAN-0007 — Harness autonomy layer Phase 1** — MERGED. PR #6 → `main` (`b2ea9b8`), 9 commits (6 Phase A governance: `770adf5` ADR-013 Accepted, `c00dc98` PLAN-0007, `c45526b` CLAUDE.md §6 T3, `e64a4d2` tier instructions T4, `8eebe09` ADR-009/012 pointers T5, `c048117` STATUS T6; 3 Phase B execution: `28fac01` telegram.sh, `711971c` settings + hooks + tests, `7c6ae65` autonomy-triggers registry). All ACs green incl live (AC-2: 16/16 bypass-immune tests; AC-1: live Telegram smoke verified by Cray; AC-3: handoff frontmatter auto-validator). OQ-3 resolved (CLAUDE_TIER=code env marker). Plan moved to `docs/plans/done/`. Closeout: `.claude/handoffs/session-10/2026-05-23-1606-code-plan0007-phaseB-closeout.md`. *(Session 10, 2026-05-23)*
- [x] **TODO-A — ADR-001 amendment (PLAN-0006 follow-on)** — DONE. ADR-001 Amendment 1 pins `gpt-oss:20b` + Ollama 0.24.0 for the recommender path (superseding `gemma4:26b` for that path only; gemma4's multimodal role + `qwen2.5-coder:32b` untouched). Cowork-drafted (ADR-009 D1); Code reviewed against the PLAN-0006 fact-pack + committed (ADR-009 D2) with the live `gpt-oss:20b` digest captured; rides the PLAN-0006 branch / PR #5 per Cray's routing call. *(PLAN-0006 kickoff dispatch §7 TODO-A; commit `30d2c8e`)*
- [x] **Suffix-enum vs cowork-instruction divergence** (PLAN-0005 §4 C-2) — RESOLVED via option α (expand the enum): `tools/handoffs/_schema.py:Suffix` gained `dispatch`/`completion`/`consultation`; PLAN-004 D4 + `handoff-frontmatter-schema.md` registered them; 2 regression tests in `test_schema.py`. `discussion` deliberately not added (ADR-012 carries it via `phase: discussion`). *(surfaced 2026-05-21; Cray adjudicated α 2026-05-22; `db9c5ed`)*
- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten (full table: PLAN-0005 §8.1): rule-based recommender → **ADR-010 ACCEPTED (2026-05-22) → PLAN-0006 next** (LLM reasoning hook); minimal approval gate → **ADR-011+** (audit framework — trigger: first design-partner data / PDPA review); no mapping layer → **dbt/SQLMesh** (trigger: first non-synthetic source); hand-authored ORM → **"ORM emitter"** Rule-of-Three candidate (trigger: 3rd vertical / DDL↔ORM parity-test drift); base Postgres only → **PLAN-002** (pgvector/AGE — trigger: semantic + graph features); explicit registry → **ADR-006 D3 L2** (trigger: vertical #2/#3 or `new-vertical` generator). *(per Cray note 2026-05-21)*
- [ ] **Phase-enum amendment** — add `consultation` (or equivalent Q&A-round value) to canonical Phase enum (Q15 of `2026-05-20-0245-code-plan003-pre-draft-consultation-reply.md`); requires touching `tools/handoffs/_schema.py` + `docs/conventions/handoff-frontmatter-schema.md` + validator tests; PLAN-004 Phase B adjacent. *(Deferred per R-9, 2026-05-20)*
- [ ] **Cleanup stale `ontology/README.md`** — 2026-05-05 PLAN-001 artifact; ontology directory canon now lives at `verticals/<name>/ontology/<name>_v0.yaml` per ADR-006 D1 / ADR-008 D5; superseded by PLAN-003. *(Deferred per R-9 cohort, 2026-05-20)*
- [ ] **PLAN-004 Phase B/C — DEFERRED (backlog, post-PLAN-003):** validator-scope exclusion (`README.md` / `_rename-map.md`, manifest §4.2/§6.1) + Cat G `references_*` autofix + Phase C handoff dashboard + OQ-2 systemic candidate (effective-vs-authored `status:` / archival flag so dead handoffs don't surface as actionable in the dashboard) + **validator warning-swallow bug** — `tools/handoffs/_schema.py` `_build()` (lines ~302–306) returns `Frontmatter` and discards its local `errors` list when no hard error exists, so `_check_unknown()` WARNING-severity findings (e.g. unknown field `brief-number`) are unreachable on otherwise-valid files; fix to surface warnings + add a regression test *(found 2026-05-22 dog-fooding the 4 Cowork LLM-hook handoffs; Cray routed → Phase B)*
- [ ] **ADR-NN (TBD, ≥ ADR-014) + PLAN-002** — Custom Postgres image with extensions (ADR-011 earmarked for the audit framework, ADR-012 taken, ADR-013 taken by autonomy axis relocation; floor bumped from ≥0013 to ≥0014 on 2026-05-23 per ADR-013 T6)
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (low priority)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)
- [x] Filesystem cleanup: `.claude/worktrees/sad-northcutt-6a48ff/` removed *(Session 10, 2026-05-21)*
- [x] **ADR-006** — Vertical Plugin Architecture *(Session 10 Batch 2)*
- [x] **ADR-005** — Strategic Pivot to OCT (vet clinic parked Phase 2) *(Session 10 Batch 2)*
- [x] **Directory scaffolds** — `verticals/{_template, energy, supply_chain, vet_clinic}/` + `docs/strategy/{public, private}/` *(Session 10 Batch 2)*
- [x] **Parked-note pass** — 6 vet-mentioning docs annotated *(Session 10 Batch 2)*
- [x] **ADR-004** — Canonical author email (GitHub noreply, provisional) *(Session 10)*
- [x] **Worktree mode policy** — codified in CLAUDE.md §6 *(Session 10)*
- [x] **Handoff rotation policy** — codified in runbook *(Session 10)*
- [x] **Phase G** — commit + PR + merge + cleanup *(Session 9)*
- [x] **Lesson #2 amendment** — Misdiagnosis section *(Session 9)*
- [x] **Lesson #3** — Code Tab worktree lifecycle traps *(Session 9)*
- [x] **File-based handoff mechanism** — `.claude/handoffs/` live *(Session 9)*
- [x] **Setup Claude Code on Windows** *(Session 8)*
- [x] **Cowork Project setup** *(Session 8)*
- [x] **PLAN-001** — Starter pack scaffold *(Session 4)*
- [x] **ADR-003** — Service port strategy *(Session 4)*
- [x] **Memory architecture implementation** *(Session 5)*
- [x] Lesson cleanup batch — Lesson #3 amendment + Lesson #5 §2/§3 amendment + Lesson #6 new *(done `96bf51b`, 2026-05-18)*
- [x] **PLAN-004 Phase A** — Batch 1 (schema + tools) + Batch 2 (2a: 20 files / 2b.1: 12 renames + ref-graph / 2b.2: post-recovery) complete *(Session 10, 2026-05-19/20; anchor `ad81e7e`)*
- [x] **PLAN-003 Phase 1** — Ontology engine + 5 emitters + `energy_v0.yaml` + L1 commit-time gate *(Session 10, 2026-05-20; merge `30619b8`, PR #2)*
- [x] Adopt Q1(b) closeout-template line "STATUS.md updated: yes/no/N/A" — adopted (closeouts carry the line)
- [x] Adopt Q3(b/c) dedicated `docs(status): …` housekeeping commit at batch close — adopted (`894a1e5` first instance; this 2b.2 close repeats)

## Next Steps

1. **PLAN-0008 Phase 2 — Step 2 execution.** Step 1 (loop-counter state module) merged (PR #9 `2b303a0`). **Step 2** = `.claude/hooks/pretooluse_loop_detect.py` — reads `.claude/state/loop-counter.json` via the Step 1 module; on `Write`/`Edit` checks L1 counter (`(file_path) ≥ 6`), on `Bash` checks L4 counter (`(tokenized_command) ≥ 6` accumulated from PostToolUse non-zero exits); on trigger fires `tools/notify/telegram.sh` with Cray-E.4 payload `{loop_type, target, last_6_actions}` and emits `deny` decision. L2 (test fails) + L3 (error signatures) are inherently PostToolUse-fed and fire from Step 3, not here. Branch: `feat/plan0008-step2-pretooluse-loop-detect`. Then Steps 3–8 (PostToolUse progress observer → Stop continuation → Sonnet classifier helper → wire into `settings.json` + extend `autonomy-triggers.md` → tests → live verification).
2. **PLAN-0008 Step 1 — MERGED.** [PR #9](https://github.com/CrayJThiemsert/vero-lite/pull/9) merged to `main` (`2b303a0`); `_loop_counter.py` state primitives live.
3. **PLAN-0008 — DRAFTED + MERGED.** [PR #8](https://github.com/CrayJThiemsert/vero-lite/pull/8) merged to `main` (`ec5e2ae`); plan lives at `docs/plans/0008-harness-autonomy-layer-phase-2.md` (will move to `done/` after Step 8 closeout).
4. **PLAN-0007 — MERGED + closed.** [PR #6](https://github.com/CrayJThiemsert/vero-lite/pull/6) merged to `main` (`b2ea9b8`); plan archived at `docs/plans/done/0007-harness-autonomy-layer-phase-1.md`.
5. **PLAN-0006 — MERGED + closed.** [PR #5](https://github.com/CrayJThiemsert/vero-lite/pull/5) merged to `main` (`68053fe`); plan archived at `docs/plans/done/0006-llm-reasoning-hook-execution.md`.
6. **PLAN-0005 §8.1 revisit register** — remaining deferred-foundational simplifications at their batch boundaries (audit framework → ADR-011+, mapping layer, ORM emitter, base-Postgres → PLAN-002 (≥ADR-014), registry discovery).
7. **Partner-trial readiness gaps** — `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` awaits a dedicated Cray discussion.
8. **Deferred (backlog)** — PLAN-004 Phase B (validator-scope exclusion; Cat G `references_*` autofix; validator warning-swallow bug) + Phase C (handoff dashboard); PLAN-002 custom Postgres image (≥ADR-014).
9. **Ongoing** — Continue exercising the file-based handoff mechanism (Chat ↔ Code ↔ Cowork) across batches.

## Update Workflow

This file is updated when:
- A commit changes project state significantly
- A new ADR/PLAN is minted or completed
- Active priorities shift
- A batch closes (sync `last_updated` + `current_batch` + `head_commit` + `recent_commits` frontmatter)
- A session closes (sync all frontmatter fields; archive batch history if needed)

**Update mechanism (locked per STATUS staleness batch 2026-05-18, Hybrid A+B short-term, C long-term):**

- **Per closeout (Option A + Q1(b) discipline):** Closeout drafter includes the line "STATUS.md updated: yes / no / N/A" in their closeout. If `yes`, the closeout's commit batch should include a dedicated `docs(status): …` housekeeping commit (Q3(b/c) pattern) bumping at minimum the `last_updated` and `head_commit` frontmatter fields.
- **Per batch boundary (Option B full body):** Full body refresh (Current Focus + Recent Decisions + Active TODOs + Next Steps) at batch close, alongside the frontmatter bump.
- **Per session boundary:** Full body + frontmatter sync; consider archive of prior session's batch history.
- **Future (Option C, PLAN-004 Phase A):** Validator will flag stale STATUS.md by comparing **frontmatter `last_updated` field** against newest closeout's `created` timestamp (NOT file mtime — mtime is defeated by side-effect commits, e.g. `c85a595` 2026-05-16 normalization sweep that touched STATUS.md body without bumping `last_updated`).

**Q4 `head_commit` semantics (codified 2026-05-18, locked Cray ratification of midflight `2026-05-18-1049` §4 + closeout `2026-05-18-1202` §6.2):**

- `head_commit` = short SHA of the newest **substantive** commit on
  `origin/main` that STATUS.md content reflects.
- **Excluded from `head_commit`:** `docs(status): …` housekeeping
  commits. These commits encode no new repo state — they ARE the
  STATUS.md freshness marker. Including them in `head_commit` creates
  a self-defeat where every housekeeping commit makes STATUS.md appear
  "fresh" to Q4 detection regardless of substantive backlog.
- **Substantive (included in `head_commit`):** everything else —
  `docs(lessons):`, `docs(adr):`, `docs(runbook):`, `feat:`, `fix:`,
  `chore:` (when changing meaningful state), `refactor:`, `test:`, etc.
  Any commit type that changes durable repo content updates
  `head_commit` at the next STATUS.md edit.
- **Reader recipe (returning after a pause):**

  ```bash
  # Newest substantive commit on origin/main (the value head_commit should hold)
  git log -1 --format=%h --invert-grep --grep='^docs(status):' origin/main

  # Compare to STATUS.md head_commit field
  grep -E '^head_commit:' docs/STATUS.md
  ```

  If the two differ → STATUS.md content is stale relative to substantive
  repo state. If they match → STATUS.md is fresh.

- **Writer rule (at each STATUS.md update):** Set `head_commit` to the
  output of `git log -1 --format=%h --invert-grep --grep='^docs(status):' origin/main`
  *after* the substantive commits of the current batch land but *before*
  any `docs(status):` housekeeping commit (or, if the STATUS.md edit
  itself is in a substantive commit like `docs(lessons):`, set
  `head_commit` to that substantive commit's own SHA — which becomes
  knowable only post-commit, so the writer typically updates
  `head_commit` to the *most-recent prior substantive commit* and lets
  the next batch's first edit catch up).
- **Two failure modes this rule closes:**
  1. **mtime trap** (closeout `2026-05-18-1202` §2): side-effect commits
     that touch STATUS.md body without bumping `last_updated` (e.g.
     `c85a595` 2026-05-16 normalization sweep) leave the file mtime-fresh
     but semantically stale. A SHA in `head_commit` cannot drift this way.
  2. **Housekeeping self-defeat** (closeout `2026-05-18-1202` §6.2 +
     midflight `2026-05-18-1049` §4): if `head_commit` = own SHA, every
     `docs(status):` commit makes Q4 say "fresh" regardless of
     substantive backlog. Excluding `^docs(status):` from the comparison
     baseline closes this loophole.

Manually edited until Option C lands.
