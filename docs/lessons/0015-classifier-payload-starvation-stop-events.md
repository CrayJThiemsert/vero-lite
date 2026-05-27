# Lesson #15: classifier payload starvation — Stop events ship without conversation content, Sonnet defaults to `proceed`

> **Status:** Codified 2026-05-27 (Session 16, post-PR-49 Path A Smoke 2 finding).
> **Source:** Direct observation 2026-05-27 ~09:55–10:05 +07 in Session 16. The D1 Stop dispatch arm of `_sonnet_classifier.classify` returned `proceed` for every Smoke 2 attempt (with and without in-flight Reads) under PR #49's now-working WSL HTTPS bridge. Direct in-process diagnostic confirmed Sonnet receives only the raw 5-field Stop payload — no transcript, no user message, no agent turn-1 content — and reasonably defaults to `proceed` with reason "no activity or pending action; no registry row matches."
> **Severity:** High (structural). The D1/D2 auto-dispatch arms of the autonomy layer (PLAN-0009 Step 5c-1 + Step 4 dispatch protocol) cannot fire for Stop events under the shipped implementation; the layer is observably classifier-blind in the half of the surface that the registry's D-rows + C-rows target.
> **Cross-references:** Lesson #14 (**direct sibling — same antipattern family**; argv vs stdin contract drift between impl + test stub silently disables the AFK fail-safe). [[feedback-coding-careful-pre-ship-checklist]] (extended with 5th point covering payload semantic content). PR [#49](https://github.com/CrayJThiemsert/vero-lite/pull/49) (the HTTPS bridge fix that *unblocked* this finding by letting Sonnet respond at all).

## 1. The finding

`.claude/hooks/_sonnet_classifier.py:234-253` defines:

```python
def _build_user_message(payload: dict[str, Any]) -> str:
    safe = json.dumps(payload, indent=2, sort_keys=True, default=str)
    event_hint = payload.get("hook_event_name") or payload.get("event") or "<unknown>"
    return (
        f"The agent has just emitted a `{event_hint}` hook event. The raw "
        "event payload follows. Decide whether to PROCEED (continue / "
        "allow the action), PAUSE (yield to Cray and deny / wait for "
        "review), or DISPATCH (auto-handoff a governance-drafting task "
        "to a co-located subagent).\n\n"
        f"```\n{safe}\n```"
    )
```

The classifier renders its user message as a **pure JSON dump of the hook event payload**. That works for **PreToolUse** events because that payload contains `tool_name` + `tool_input` (which includes file paths, content snippets, command strings — the semantic signal the classifier reasons over). It **fails for Stop events**, whose payload contains only:

| Field | Stop payload value |
|---|---|
| `hook_event_name` | `"Stop"` |
| `session_id` | (session ID) |
| `transcript_path` | path to Claude Code's transcript file |
| `cwd` | working directory |
| `stop_hook_active` | bool |

No user message text. No agent turn-1 response. No recent tool calls. No conversation excerpt. The `transcript_path` field is **present but never read** by `_build_user_message()` or any helper it calls.

So when the classifier fires on `Stop`, Sonnet is asked to decide proceed/pause/dispatch with essentially no semantic information about what just happened. The most reasonable default for "low-information Stop event" is `proceed` — which is what Sonnet returns, every time.

## 2. The mechanism — why CI stayed green

`tests/handoffs/test_stop_continuation.py` and siblings (`test_pretooluse_classifier_dispatch.py`, `test_phase2_integration.py`) mock `_sonnet_classifier._call_api` to return canned `{"decision": "dispatch", ...}` / `{"decision": "pause", ...}` / `{"decision": "proceed", ...}` strings:

```python
# tests/handoffs/test_stop_continuation.py — pattern
with patch("_sonnet_classifier._call_api") as mock_call:
    mock_call.return_value = json.dumps({"decision": "dispatch", ...})
    result = stop_continuation.main(payload)
    assert "dispatch" in result["block"]
```

The tests verify:
- Hook reads payload correctly ✅
- Classifier mock returns dispatch → hook emits block directive ✅
- Hook formats block message with dispatch routing template ✅
- Hook updates `stop-chain.json` depth correctly ✅

What the tests **never** verify:
- That the user message rendered by `_build_user_message(payload)` contains information sufficient for a real Sonnet to decide `dispatch` for the D1/D2/C1–C4 rows
- That what the model actually reads matches what the registry rows assume the model can see

The mock at `_call_api` is **above** `_build_user_message` in the call stack — the user message construction is exercised in the mocked path, but the mock returns a canned answer without inspecting what was passed in. So every test path is structurally blind to whether the prompt makes sense.

**Same antipattern as Lesson #14:** the test verifies that "impl and stub agree with each other," not that either matches a real outside reference (the real model, in this case). Lesson #14 was test-stub-vs-real-script contract drift; Lesson #15 is test-stub-vs-real-model contract drift. **Sibling bug, one layer up the stack.**

The bug shipped through PLAN-0009 Step 5c-1 (Stop dispatch arm, PR #41) and Step 5c-2 (PreToolUse arm, PR #42) without surfacing because:
- All unit tests mock `_call_api` — never read what the model sees
- The PreToolUse arm *happens* to work because PreToolUse payloads carry semantic content natively
- The Stop arm never fired in live testing prior to session 16 because session 14's Path A scenarios 3/4/5 were deferred (per session-14 Option-A "close now, iterate on findings")
- Sessions 14b + 15 + 15a + 15b were blocked by the SSL bug (PR #49) — classifier could not reach Sonnet at all, so the question "what does Sonnet see?" was never reachable

PR #49 (Option 2 WSL bridge) shipped the SSL fix. **Smoke 1 (G1 PreToolUse) PASSED — exposing that the PreToolUse arm has always worked end-to-end.** Smoke 2 (D1 Stop dispatch) **immediately surfaced the structural payload-starvation** the moment Sonnet could actually respond. PR #49 didn't cause this bug; it made the bug observable.

## 3. Reproduction

Trip the trap in <30 seconds, in-process, no real API call:

```bash
wsl bash -lc 'cd ~/work/vero-lite && python3 -c "
import sys
sys.path.insert(0, \".claude/hooks\")
from _sonnet_classifier import _build_user_message

stop_payload = {
    \"hook_event_name\": \"Stop\",
    \"session_id\": \"repro\",
    \"transcript_path\": \"/dev/null\",
    \"cwd\": \"/home/crayj/work/vero-lite\",
    \"stop_hook_active\": False,
}
print(_build_user_message(stop_payload))
"'
```

Output:

```
The agent has just emitted a `Stop` hook event. The raw event payload follows.
Decide whether to PROCEED (continue / allow the action), PAUSE (yield to Cray
and deny / wait for review), or DISPATCH (auto-handoff a governance-drafting
task to a co-located subagent).

```
{
  "cwd": "/home/crayj/work/vero-lite",
  "hook_event_name": "Stop",
  "session_id": "repro",
  "stop_hook_active": false,
  "transcript_path": "/dev/null"
}
```
```

That is everything Sonnet sees. The receiver's job is "look at what the agent just did and decide what to do next." The receiver gets five metadata fields and a path string. The right answer to give the receiver — given only that — is `proceed`.

## 4. The fix (deferred to follow-up chore PR / PLAN — session 17+)

`_build_user_message` must **read + summarize the transcript** before rendering. Minimal viable shape:

```python
def _build_user_message(payload: dict[str, Any]) -> str:
    safe = json.dumps(payload, indent=2, sort_keys=True, default=str)
    event_hint = payload.get("hook_event_name") or payload.get("event") or "<unknown>"
    transcript_excerpt = _summarize_transcript(payload.get("transcript_path"))
    return (
        f"The agent has just emitted a `{event_hint}` hook event. ..."
        f"\n\n## Recent conversation excerpt\n{transcript_excerpt}"
        f"\n\n## Raw payload\n```\n{safe}\n```"
    )
```

Where `_summarize_transcript(path)`:
1. Reads the JSONL transcript file
2. Extracts last N turns (user + assistant messages, and tool call summaries — not full tool outputs which would blow context budget)
3. Renders to a bounded markdown block (~2-4 KB cap, truncate with `[earlier turns elided]` prefix if over budget)
4. Returns `"(no transcript available)"` if path missing / unreadable (don't fail the hook)

Companion tests must:
- Construct a realistic transcript fixture (user message, agent ack, optional tool calls)
- Assert the rendered user message contains the user-message text + agent-turn-1 fragment
- Run **at least one** integration test that does NOT mock `_call_api` — flagged behind an env var (`RUN_LIVE_CLASSIFIER_TESTS=1`) and skipped in CI, but available for pre-merge smoke

This is similar in shape to PR #45's Lesson #14 fix (real end-to-end smoke alongside the unit tests).

**Why deferred:** Cray ratified Option 2 (defer fix; close Path A partial) on 2026-05-27 to preserve session-16 closeout scope. The fix is mechanical (~50 LOC + tests) but introduces transcript-parsing surface area + needs an integration-test gating decision that's worth its own PLAN. Tracked as the Step-D follow-up (placeholder PR or PLAN-NNNN to be opened next).

## 5. Prevention checklist (for future LLM-integration code)

Before declaring any LLM classifier / drafter / agent integration done, walk this checklist (codified in [[feedback-coding-careful-pre-ship-checklist]] as the 5th point):

1. **Read the prompt out loud.** Print the user message the model actually receives for at least one realistic scenario. If you can't answer "given this prompt and nothing else, would I make the right decision?" the prompt is under-specified.
2. **Sanity-check the prompt against the registry / spec.** If the prompt asks the model to match against rows in `.claude/autonomy-triggers.md` (or similar), check that the prompt actually surfaces the inputs those rows depend on. If a row says "match when user mentions ADR" and the prompt doesn't surface user messages, the row can never match.
3. **Mock `_call_api`, but inspect what gets passed in.** When unit tests mock the LLM call, add at least one assertion on the *input* to the mock (`mock_call.call_args` payload-string check) — verify the prompt rendered contains the semantic content the test scenario assumes the model needs. Don't just assert the canned-output path.
4. **End-to-end smoke before merge.** For any LLM integration touching a fail-safe / autonomy path, run at least one real-API smoke against a realistic payload. Gate behind an env var (`RUN_LIVE_*_TESTS=1`) so CI stays cheap, but make it 1-command-runnable for the developer.
5. **Asymmetric coverage = blind spot.** If the integration handles multiple event types (PreToolUse, Stop, PostToolUse, SubagentStop, …) and your unit tests cover all of them with the same mock, ask whether the **input shape** is the same across them. PreToolUse + Stop pass through the same `_build_user_message` but their payloads have radically different semantic content. A working PreToolUse mock is **no evidence at all** that Stop works.

## 6. Why this isn't covered by Lesson #14's checklist alone

Lesson #14's checklist item #5 says "End-to-end smoke before merge … run the real binary end-to-end (not just the stubbed test)." That points at the right discipline but at the wrong layer — Lesson #14 was about a shell-script bridge (test the bridge against the real script). Lesson #15 is about an LLM bridge (test the prompt against a real model).

The "real binary" for an LLM integration is the model. End-to-end smoke means **call the model with the real prompt and inspect what it returns** — not just confirm the API responds 200. Lesson #15's checklist items 1 + 2 + 5 are the LLM-specific refinements; item 4 is the umbrella from Lesson #14 specialized to "real model, not real shell script."

## 7. Adjacent observations

- **PR #45 Telegram fail-safe is unaffected.** The SubagentStop → Telegram path was validated end-to-end in this session via manual spawn (see `docs/research/private/step6-live-ac/scenario3-cray-driven-d1-stop-dispatch.md` §Telegram fail-safe end-to-end validation). Lesson #15 surfaces a structural bug *upstream* of where PR #45 lives.
- **PreToolUse classifier dispatch (Step 5c-2, PR #42) still works.** Smoke 1 G1 Edit-Accepted-ADR passed with real Sonnet judgment citing the G1 trigger row. The fix scope is narrow — `_build_user_message` for Stop events specifically. PreToolUse needs no change (and benefits from the transcript context if added — defensive enrichment is OK).
- **ADR-013 D1 phasing assumption holds.** The autonomy-axis relocation in Code (Tier 2) + subagents is sound; the bug is in *how* Sonnet sees the dispatch trigger, not in *whether* Sonnet runs there. Path A partial closure does not invalidate Direction B; it surfaces a verification gap in the integration's first live exercise.
- **PLAN-0010 Phase 4 dispatcher prewire (Path B in handoff §3) is independent.** That work concerns concurrent dispatcher races in `_archive` + `save_failure_state`; it is unrelated to classifier prompts.

## 8. References

- Implementation site of the bug: `.claude/hooks/_sonnet_classifier.py:234-253` (`_build_user_message`)
- Stop hook caller: `.claude/hooks/stop_continuation.py`
- PreToolUse hook caller (works correctly): `.claude/hooks/pretooluse_classifier_dispatch.py`
- Registry: `.claude/autonomy-triggers.md` (D-rows + C-rows that depend on conversation content; G-rows that depend on tool payload — only the latter currently works)
- Evidence files: `docs/research/private/step6-live-ac/scenario3-cray-driven-d1-stop-dispatch.md`, `scenario3-cray-driven-d1-stop-dispatch-attempt1-failed.md`, `scenario4-cray-driven-g1-edit-accepted-adr.md`, `scenario5-cray-driven-c2-add-dependency.md`
- PR [#45](https://github.com/CrayJThiemsert/vero-lite/pull/45) — sibling lesson (#14) Telegram fix
- PR [#49](https://github.com/CrayJThiemsert/vero-lite/pull/49) — Option 2 WSL bridge that unblocked observability of this bug
- Companion handoff: `.claude/handoffs/session-15/2026-05-27-0930-code-session16-kickoff.md` §3 Smoke 2 + §3 failure-modes

## 9. Sign-off

**Author:** Code (Tier 2, session 16). **Reviewer (independent check):** Cray at PR merge. **Independent-tier deliberation:** N/A for a structural-finding lesson; the finding is empirical (direct diagnostic output reproduces deterministically), not a design judgment. No author≠reviewer concern.

**Promotion criterion met:** appeared in a single live session as a structural surfacing the moment SSL bridge unblocked observability, with deterministic in-process reproduction in under a minute. Promote-on-first-occurrence under the Lesson promotion guideline because the bug class (test mocks hiding contract gaps at the LLM boundary) generalizes beyond this one site — any future hook/skill/subagent integration with an LLM is at risk.
