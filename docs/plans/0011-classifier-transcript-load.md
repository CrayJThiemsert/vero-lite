# PLAN-0011: Classifier transcript-load fix — eliminate Stop-event payload starvation

**Status:** Draft
**Owner:** Claude Code
**Created:** 2026-05-27
**Related ADRs:** ADR-013 (autonomy axis relocation — autonomy primitives in Code Tier 2)
**Related Lessons:** [#15](../lessons/0015-classifier-payload-starvation-stop-events.md) (rationale — direct sibling); [#14](../lessons/0014-argv-vs-stdin-contract-drift.md) (sibling antipattern one layer down the stack — same fix-eating-mock family)
**Related Plans:** PLAN-0009 (subagent topology — Steps 5c-1 + 5c-2 shipped the bug); PLAN-0008 (Step 4 stop-continuation invoked the bug site)

## Goal

Eliminate classifier payload starvation on `Stop` hook events by loading and summarizing the hook payload's `transcript_path` inside `_build_user_message()` in `.claude/hooks/_sonnet_classifier.py`. Today the user message rendered for `Stop` events contains only five metadata fields (no conversation excerpt, no agent turn-1, no recent tool activity), so Sonnet correctly defaults to `proceed` and the D1/D2/C1–C4 auto-dispatch arms of the autonomy layer (PLAN-0009 Step 5c-1 + Step 4 dispatch protocol) cannot fire end-to-end. After this PLAN lands, **Smoke 2 (D1 Stop dispatch)** and **Smoke 3 (C2 add-dependency)** from `.claude/handoffs/session-15/2026-05-27-0930-code-session16-kickoff.md` §3 pass live against real Sonnet, the SubagentStop → Telegram chain delivers under the dispatch path, and the auto-dispatch arm of the autonomy layer becomes observably usable. The change is mechanical (~50 LOC + tests), additive to the existing JSON-dump prompt structure, and fail-safe (missing or unreadable transcript paths return `"(no transcript available)"` rather than raising).

## Acceptance Criteria

- [ ] **AC-1 — Stop events surface conversation content.** `_build_user_message(payload)` for a `Stop` event payload includes a `## Recent conversation excerpt` markdown section between the framing paragraph and the raw payload JSON dump. The excerpt contains the last N turns from `transcript_path` (user messages + assistant messages + tool-call summaries — not full tool outputs), bounded to ~2–4 KB. When the path is missing, unreadable, or empty, the section renders as `"(no transcript available)"` and the hook does not raise.
- [ ] **AC-2 — PreToolUse regression guard.** `_build_user_message(payload)` for a `PreToolUse` event payload still surfaces `tool_name` + `tool_input` semantic content via the raw JSON dump. The new transcript-summary section is **additive enrichment**, not a replacement; PreToolUse smoke (G1 Edit-Accepted-ADR) continues to pass with the same verdict shape as Smoke 1 in session 16.
- [ ] **AC-3 — Live Smoke 2 + Smoke 3 pass.** Re-running the Smoke 2 (D1 Stop dispatch) and Smoke 3 (C2 add-dependency) trigger texts verbatim from handoff §3 yields:
  - Smoke 2: `decision: dispatch` with `matched_rows` containing **D1**; block directive surfaces in Code's context; SubagentStop → Telegram fail-safe chain delivers a real message (PR #45 path) with a Telegram `message_id`.
  - Smoke 3: `decision: pause` with `matched_rows` containing **C2**; block directive surfaces in Code's context citing the add-dependency rule.
- [ ] **AC-4 — Mock-input assertions added (Lesson #15 §5 prevention).** At least one test per event class asserts on `mock_call.call_args` payload-string content:
  - `tests/handoffs/test_stop_continuation.py` — new assertion: rendered user message contains the fixture transcript's user-message text + agent turn-1 fragment.
  - `tests/handoffs/test_pretooluse_classifier_dispatch.py` — new assertion: rendered user message contains the fixture `tool_name` + a fragment of `tool_input`.
- [ ] **AC-5 — Gated live-API smoke test.** New `tests/handoffs/test_classifier_live_smoke.py` with `@pytest.mark.skipif(os.getenv("RUN_LIVE_CLASSIFIER_TESTS") != "1", reason=...)` runs the real Sonnet call against a fixture transcript that triggers D1, asserts the returned `decision == "dispatch"` and `matched_rows` includes D1. Skipped in CI by default; 1-command-runnable locally (`RUN_LIVE_CLASSIFIER_TESTS=1 uv run --extra dev pytest tests/handoffs/test_classifier_live_smoke.py`).
- [ ] **AC-6 — Suite + lint clean.** `uv run --extra dev pytest`, `ruff check .claude/hooks/ tests/handoffs/`, and `mypy .claude/hooks/` all pass with no new failures or warnings. Existing test count grows by at least 4 (Steps 3 + 4) and no existing test regresses.
- [ ] **AC-7 — Evidence files updated.** `docs/research/private/step6-live-ac/scenario3-cray-driven-d1-stop-dispatch.md` and `scenario5-cray-driven-c2-add-dependency.md` flipped from BLOCKED to PASS with verbatim Sonnet judgment captured and Telegram `message_id` recorded (Smoke 2). Original `scenario3-cray-driven-d1-stop-dispatch-attempt1-failed.md` preserved as archeology.

## Out of Scope

- ❌ **`_wsl_bridge.py` extraction.** Rule-of-three threshold is met (`notification_telegram.py` + `subagentstop_notify.py` + the inline bridge in `_sonnet_classifier.py:284-417`), but extraction is a separate refactor with its own test scope.
- ❌ **`.claude/autonomy-triggers.md` registry rewrite.** Trust the registry rows as-is; if a row needs revision post-live-smoke, surface separately. This PLAN does not edit registry semantics.
- ❌ **Re-architecting the payload schema to typed dataclasses.** The fix is an additive text insertion into the existing JSON-dump prompt structure, not a redesign of the classifier's payload contract.
- ❌ **Cross-process classifier caching.** Performance concern, not correctness; orthogonal to payload starvation.
- ❌ **PLAN-0010 Phase 4 dispatcher prewire.** Concurrent-dispatcher race scope carried separately (Path B in handoff §3); unrelated to classifier prompts.
- ❌ **ADR-0014 ratification.** Cray's separate decision per its `§Implementation Notes` author≠reviewer disclosure; not part of this fix.
- ❌ **Writing the fix code as part of this PLAN.** This is the *plan* for the fix, not the fix itself; implementation lives in the session 17+ branch.

## Steps

### Step 1: Implement `_summarize_transcript(path) -> str` helper

Add a new helper to `.claude/hooks/_sonnet_classifier.py` (sibling to `_build_user_message`):

- Signature: `def _summarize_transcript(path: str | None, *, max_turns: int = 8, max_bytes: int = 3072) -> str`
- Behavior:
  1. If `path` is `None`, empty, or `pathlib.Path(path).exists()` is False, return `"(no transcript available)"`.
  2. Read JSONL file line-by-line; each line is a transcript event. Tolerate malformed lines (skip with no raise).
  3. Extract the last `max_turns` user/assistant turns. For tool calls, include `tool_name` + a ≤200-char summary of `tool_input` (paths, command preview); **do not** include full tool outputs (context budget).
  4. Render as a bounded markdown block. If the rendered text exceeds `max_bytes`, truncate from the front and prepend `"[earlier turns elided]\n"`.
  5. Wrap entire body in a `try/except (OSError, json.JSONDecodeError, KeyError, ValueError)` block; on any exception return `"(transcript unreadable)"`.
- No external dependencies; stdlib only (`pathlib`, `json`).

### Step 2: Update `_build_user_message(payload)` to insert the excerpt

Modify lines 234–253 of `_sonnet_classifier.py`:

```python
def _build_user_message(payload: dict[str, Any]) -> str:
    safe = json.dumps(payload, indent=2, sort_keys=True, default=str)
    event_hint = payload.get("hook_event_name") or payload.get("event") or "<unknown>"
    transcript_excerpt = _summarize_transcript(payload.get("transcript_path"))
    return (
        f"The agent has just emitted a `{event_hint}` hook event. ..."  # existing framing preserved verbatim
        f"\n\n## Recent conversation excerpt\n{transcript_excerpt}"
        f"\n\n## Raw payload\n```\n{safe}\n```"
    )
```

Preserve the existing framing paragraph verbatim — only insert two new sections (`## Recent conversation excerpt`, `## Raw payload` header before the existing code fence). PreToolUse payloads also pass through this path; the excerpt is additive enrichment for them (often `"(no transcript available)"` if Claude Code doesn't pass `transcript_path` on PreToolUse — verify during Step 3 fixture construction).

### Step 3: Unit tests — summarizer + `_build_user_message` regression guard + AC-4 mock-input assertions

Add to `tests/handoffs/test_sonnet_classifier.py` (or extend if structure permits):

- `test_summarize_transcript_missing_path` — `path=None` → `"(no transcript available)"`.
- `test_summarize_transcript_nonexistent_path` — `path="/tmp/does-not-exist.jsonl"` → `"(no transcript available)"`.
- `test_summarize_transcript_valid_fixture` — fixture JSONL with 3 user turns + 3 assistant turns + 1 tool call; assert excerpt contains representative fragments from each, tool-output text NOT included.
- `test_summarize_transcript_budget_cap` — fixture with 50 turns of long messages; assert returned excerpt ≤ `max_bytes + len("[earlier turns elided]\n") + small margin` and starts with `"[earlier turns elided]"`.
- `test_summarize_transcript_malformed_lines` — fixture with mixed valid + malformed JSONL lines; assert no raise, malformed lines skipped.
- `test_build_user_message_stop_includes_excerpt` — Stop payload with fixture `transcript_path` → returned string contains both the user-message fragment AND the raw JSON dump.
- `test_build_user_message_pretooluse_preserves_tool_payload` — PreToolUse payload (no `transcript_path`) → returned string contains `tool_name` + `tool_input` fragments AND `"(no transcript available)"` in the excerpt section (regression guard for AC-2).

**AC-4 mock-input assertions** in existing files:

- `tests/handoffs/test_stop_continuation.py` — in at least one existing test that mocks `_call_api`, add `assert "<user-message fragment>" in mock_call.call_args.args[0]` (or equivalent for the rendered prompt arg).
- `tests/handoffs/test_pretooluse_classifier_dispatch.py` — same pattern, asserting `tool_name` + `tool_input` fragment presence in the rendered prompt arg.

### Step 4: Gated live-API smoke test

Create `tests/handoffs/test_classifier_live_smoke.py`:

- `@pytest.mark.skipif(os.getenv("RUN_LIVE_CLASSIFIER_TESTS") != "1", reason="live API smoke — set RUN_LIVE_CLASSIFIER_TESTS=1 to enable")`
- One test: `test_d1_stop_dispatch_live` — constructs a fixture transcript matching the Smoke 2 D1 trigger (Cray asking Code to draft an ADR), writes it to a `tmp_path` JSONL file, builds a synthetic Stop payload pointing at it, calls `_sonnet_classifier.classify(payload)` directly, asserts `result["decision"] == "dispatch"` and `"D1"` appears in `result.get("matched_rows", [])`.
- Uses the same Anthropic API key resolution path as the production hook (env var, then any fallback the hook already supports). No new key-management surface.
- Documented in the test docstring how to run it locally: `RUN_LIVE_CLASSIFIER_TESTS=1 uv run --extra dev pytest tests/handoffs/test_classifier_live_smoke.py -v`.

### Step 5: Live re-run + evidence update

Execute Smokes 2 and 3 from `.claude/handoffs/session-15/2026-05-27-0930-code-session16-kickoff.md` §3 verbatim:

- Smoke 2 trigger text (D1 Stop dispatch) → capture: rendered Sonnet verdict (JSON), block directive surfaced in Code, `stop-chain.json` depth update, Telegram `message_id` from SubagentStop notification.
- Smoke 3 trigger text (C2 add-dependency) → capture: rendered Sonnet verdict, block directive surfaced.
- Update `docs/research/private/step6-live-ac/scenario3-cray-driven-d1-stop-dispatch.md` and `scenario5-cray-driven-c2-add-dependency.md`:
  - Flip status header from BLOCKED → PASS.
  - Append a new `§Post-PLAN-0011 re-run (YYYY-MM-DD)` section with the captured artifacts.
  - Preserve all existing content as archeology (do not delete the failure analysis).

### Step 6: Commit + PR

- Branch: `chore/plan-0011-classifier-transcript-load`.
- Single PR per CLAUDE.md §7 (no direct push to main, no exceptions).
- PR body references Lesson #15 as the rationale + this PLAN as the scope + ADR-013 D1 as the governance context.
- Commit message body notes AI assistance per CLAUDE.md §7 (never as `Co-Authored-By`).
- After merge, flip this PLAN's Status from `Ready for execution` → `Complete` (Code does the flip in the same PR or a follow-up small PR), then `git mv docs/plans/0011-*.md docs/plans/done/`.

## Verification

How we know it worked — tied to commands and expected outputs:

- **Suite + lint:** `wsl bash -lc "cd ~/work/vero-lite && uv run --extra dev pytest tests/handoffs/ -v && ruff check .claude/hooks/ tests/handoffs/ && mypy .claude/hooks/"` exits 0; test count grows by ≥ 4 vs baseline; no existing test regresses (covers AC-6).
- **AC-4 mock-input assertions present:** `grep -n "call_args" tests/handoffs/test_stop_continuation.py tests/handoffs/test_pretooluse_classifier_dispatch.py` shows the new assertions (covers AC-4 visibility).
- **Gated live smoke:** `RUN_LIVE_CLASSIFIER_TESTS=1 wsl bash -lc "cd ~/work/vero-lite && uv run --extra dev pytest tests/handoffs/test_classifier_live_smoke.py -v"` passes locally; same invocation without the env var SKIPs cleanly (covers AC-5).
- **Live Smoke 2 (D1 Stop dispatch):** Trigger text from handoff §3 reproduced verbatim in a real Code session yields a Sonnet verdict with `decision: dispatch` + `matched_rows` including `D1`; `stop-chain.json` depth increments; Telegram message arrives with a captured `message_id`; block directive visible in Code's reply context (covers AC-3 Smoke 2 + AC-1 indirectly).
- **Live Smoke 3 (C2 add-dependency):** Trigger text from handoff §3 yields `decision: pause` + `matched_rows` including `C2`; block directive cites the add-dependency rule (covers AC-3 Smoke 3).
- **PreToolUse regression guard:** Re-run Smoke 1 G1 Edit-Accepted-ADR from session 16 — same verdict shape as before, classifier still cites G1 (covers AC-2).
- **Evidence files flipped:** `git diff` on `docs/research/private/step6-live-ac/scenario3-*.md` and `scenario5-*.md` shows BLOCKED → PASS header changes and new `§Post-PLAN-0011 re-run` section with verbatim Sonnet output + Telegram `message_id` (covers AC-7).

## Notes — author ≠ reviewer disclosure (ADR-012 D4.3 — mandatory)

This PLAN was authored by the in-harness `plan-drafter` subagent under ADR-013 D1 phased authority. The dispatching main-agent is also Code (Tier 2), so the canonical author≠reviewer separation is **NOT INTACT at draft time**. The load-bearing independent check is Cray's review at PR ratification (Status flip `Draft` → `Ready for execution`, then PR merge).

The Lesson #15 rationale itself was codified by Code in the same session (PR #50 merge `9e55554` at 10:50 +07), so the structural finding's author equals the executor of the fix. This is acceptable for this PLAN because: (a) Lesson #15 is **empirical** — direct in-process diagnostic output reproduces deterministically, not a design judgment; (b) the fix mechanism is **mechanical** — transcript-parse + insert text into prompt, limited room for designer bias; (c) Cowork advisory pass is available but the fix scope is small enough that the chicken-and-egg gating (Cray's call) does not apply.

**Separation status: NOT INTACT (drafter = same tier as eventual executor) — explicitly flagged for Cray's adjudication before Status flip.**
