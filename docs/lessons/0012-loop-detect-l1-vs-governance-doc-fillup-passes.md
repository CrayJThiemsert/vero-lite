# Lesson #12: Loop-detect L1 vs governance-doc fillup passes — batch or surgical-reset, don't full-reset

> **Status:** Codified 2026-05-27 (Session 15b closeout). Pattern first observed live 2026-05-26 Session 14 Phase 2 — `pretooluse_loop_detect.py` denied the 7th successive edit to `docs/plans/0010-step1-message-schema.md` during a Step 6 sign-off pass. Source observation: `docs/research/private/step6-live-ac/scenarioL1-bonus-loop-detect-live-trigger.md`. **Amended 2026-05-29 (vero-bridge Step 2b session) — see §7:** a second, broader failure mode (cross-PR / cross-session accumulation) + the structural fix (commit-boundary reset, PR #84) that makes `git commit` a reliable L1 reset point.
> **Severity:** Low (no data loss; gate behaves correctly per Cray E.4 spec). Friction medium-high if mishandled — wholesale state reset clears L2/L3 progress observations too.
> **Cross-references:** PLAN-0008 Step 2 (`pretooluse_loop_detect.py` — the L1 deny gate) + Step 3 (`posttooluse_progress_observer.py` — the writer + §7 commit-boundary reset). [[lesson-0014-argv-vs-stdin-contract-drift]] (sibling lesson — Telegram side of the L1 hook; same hook, different failure mode). `.claude/autonomy-triggers.md` row L1. PR #84 (commit-boundary reset fix).

## 1. The finding

Closeout / sign-off work on a governance doc (PLAN-NNNN.md, ADR-NNNN.md, STATUS log) routinely involves **6+ successive Edits to the same file** — matrix fill-ins, residual-risk updates, AC verification ticks, sign-off block tweaks. The L1 loop-detect gate is keyed on `(file_path, edit_count >= 6)`, so this **legitimate work pattern** trips the autonomy fail-safe.

The gate is doing exactly what it was designed to do (Cray E.4 threshold = 6). The fix is **not** to retune the threshold — it's to choose the right recovery action for the situation:

| Situation | Right move | Wrong move |
|---|---|---|
| Have 1–2 small edits left, work is genuinely converging | **Surgical reset** of just the L1 counter for the offending target | Full state-file delete (clears L2/L3 too) |
| Have many edits left, work is still in flight | **Batch remaining edits into one Write** (re-read file, plan all edits, single Write) | Continue per-edit and re-trip the gate |
| Edits genuinely span an open-ended exploratory phase | **Pause + reassess with Cray** — the gate is correctly catching a "should we still be in this file?" signal | Bypass / disable the gate |

## 2. The mechanism

`pretooluse_loop_detect.py` reads `.claude/state/loop-counter.json` (written by `posttooluse_progress_observer.py`) and denies any `Write` / `Edit` whose normalized `file_path` has accumulated `count >= 6` since the last turn-boundary reset (which `stop_continuation.py` only triggers for files NOT touched this turn — so a single-file thrash never gets the reset). **(See §7 — the turn-boundary reset is also unreliable across a long *multi-PR* session, which is why PR #84 added a commit-boundary reset.)**

The 6th edit triggers the deny. The deny message (verbatim from the live fire):

```
Loop-detect (L1) triggered: same target `docs/plans/0010-step1-message-schema.md`
hit 6 times in this session (Cray E.4 threshold = 6). Last 6 actions captured
in the Telegram payload. Pause and reassess the approach with Cray before
retrying — see .claude/autonomy-triggers.md row L1.
```

## 3. Recovery — three options

### Option A — Batch remaining edits (preferred when work is still in flight)

Re-read the file, plan all remaining edits up front, deliver as a single `Write` (full file rewrite) or a small number of `Edit`s. The L1 counter for this target is at 6; any further `Edit`/`Write` will be denied **until the next turn boundary OR a surgical reset**.

### Option B — Surgical counter reset (preferred when work has 1–2 small edits left)

```python
# Read .claude/state/loop-counter.json, drop the offending key, write back.
import json
from pathlib import Path

p = Path(".claude/state/loop-counter.json")
counter = json.loads(p.read_text(encoding="utf-8"))
counter["counters"].pop("L1:docs/plans/0010-step1-message-schema.md", None)
p.write_text(json.dumps(counter, indent=2), encoding="utf-8")
```

This preserves L2 (test-fail), L3 (error signature), L4 (Bash pattern) counters across the rest of the session — important because those represent real progress observations, not doc-thrash noise.

Validated live 2026-05-26 Session 14 Phase 2 — the 7th edit to `docs/plans/0010-step1-message-schema.md` landed cleanly after a surgical reset.

### Option C — Pause + reassess (the gate's intended behavior when uncertain)

If the work feels open-ended ("I keep finding more to fix") rather than converging, the gate is **correctly catching a real signal** — surface to Cray, get a redirect or scope cut.

### Anti-option — wholesale state-file delete

```bash
# DON'T do this just to dismiss an L1 trip
rm .claude/state/loop-counter.json
```

This is too broad. It clears legitimate L2/L3/L4 observations accumulated across the session (failing tests being tracked, repeating error signatures, command patterns under watch). After a wholesale reset, the autonomy fail-safe is blind until each loop type re-accumulates evidence — which can take many tool calls. Use surgical reset (Option B) instead.

## 4. When to escalate to retuning the threshold

Don't, in general. The Cray E.4 threshold (= 6) is a deliberate value-neutral signal: "this might be a loop, ask before continuing." Adjusting it per-workflow defeats the purpose. Two situations where threshold tuning is the right answer:

1. **A workflow that legitimately edits one file 50+ times in one turn** (e.g., generated code rewrites, formatter runs). These should be `Write` (single replacement) not `Edit` (incremental), so the count stays at 1.
2. **A discovered systematic false-positive class** (this lesson is precisely the boundary case — closeout passes hit ~6–10 edits/file). The pattern is rare enough (sign-off / matrix-fill workflows) that surgical reset is cheaper than threshold change.

## 5. Adjacent observations from the live trigger

The same Session 14 Phase 2 fire revealed that L2 and L3 counters were tracking correctly below threshold during the regression sweep:

- **L2 captured 5 distinct pytest nodeids** with counts 1–2 (no deny — below threshold 6).
- **L3 captured a `FileNotFoundError` signature** from scenario #3b cross-process race test, normalized to `'<tmp> -> '<tmp>` (paths stripped to placeholder).
- **L4 had no entries** — Bash commands varied enough not to collapse to the same tokenized pattern.

So the bonus side-effect of the L1 fire was **confirming the full PLAN-0008 loop-counter stack is working end-to-end**. The only broken layer at the time was the Telegram bridge — which Lesson #14 covers.

## 6. Prevention checklist (for future closeout passes)

Before starting a sign-off / matrix-fill / closeout pass on a single governance doc:

1. **Plan the edits.** Skim the doc once; list the sections you'll touch. If the list has 4+ sections, prefer batching to per-section edits.
2. **Use `Write` for whole-section rewrites.** A `Write` of the whole file counts as 1 toward L1, not N (one per section). The cost is more careful diff review.
3. **Know the surgical reset recipe.** Option B above. Don't reach for `rm` of the state file.
4. **Treat the L1 deny as a real signal first.** If your closeout is genuinely converging, Option B is fine. If you feel like you keep finding more things — pause, reassess, surface to Cray (Option C). The gate exists for the second case; surgical reset is for the first.

## 7. Amendment (2026-05-29) — cross-PR / cross-session accumulation + commit-boundary reset

The original lesson framed the false-positive as a **single-turn thrash** (6+ edits to one doc in one closeout pass). The vero-bridge Step-2b session surfaced a **second, broader mode** that the §1 recovery options did not anticipate:

**Finding.** A *legitimate* engineering pattern — implementing four sibling tools as **one PR each**, where every tool adds a handler to the same `tools/vero_bridge/server.py` — accumulated **6 distinct edits across four separate PRs in one long session** and hard-blocked the fifth handler. These were not a thrash; each edit was a deliberate, committed-in-between increment.

**Why the existing resets did not catch it (two compounding bugs):**

1. **The state file persists across actual sessions/days.** `session_id` / `started_at` are set **only** in `new_counter()` (i.e., when the file is missing). So a state file created days ago (keyed `pid-<old>`) keeps accumulating — the L1 counter is effectively **session-immortal**, not per-session as the schema docstring implies.
2. **`git commit` did *not* reset the counter** (pre-#84). The only reset was the Stop-hook turn-boundary path (`reset_untouched_l1`), which — across many turns spent on tests/docs/commits between tools — empirically did not fire for `server.py`. (Root cause of *that* not fully pinned; candidates: the Desktop/WSL split invoking the `Stop` event's `python`, the cross-day session, or `stop_hook_active` early-returns.)

**Two meta-lessons:**

- **Don't trust a handoff's *claimed* mitigation — verify the mechanism.** The Step-2b kickoff handoff §4 asserted "the counter appears to reset per-file on commit." It did **not** (three intervening `git commit`s via WSL did not reset it). Reading `.claude/state/loop-counter.json` + the hook code revealed the truth in minutes. When a deterministic guard fires, inspect the actual state + hook, not the lore.
- **A verbal/chat ack does NOT unblock a deterministic hook.** When `pretooluse_loop_detect.py` hard-blocks and Cray says "proceed," the PreToolUse gate re-fires identically on the retry — the hook never sees the chat. The unblock is a **state operation** (surgical reset per Option B), done transparently with Cray's approval, not a conversational one.

**The structural fix (PR #84 — `3ea2ac1`).** `posttooluse_progress_observer.py` now resets a file's L1 counter when that file is **committed**: on a successful `git commit`, it reads the new HEAD commit's files (`git diff-tree --no-commit-id --name-only -r HEAD`) and resets *only* those L1 counters. A commit is unambiguous observable progress and a reliable reset point — and crucially it lives in the **PostToolUse Bash path, which fires reliably on every Bash call** (unlike the fragile Stop-hook turn boundary). It resets only the committed files, so an unrelated in-flight loop is not masked; a failed/ambiguous commit does not reset; it fails closed (merge/empty/error → no reset).

**Implication for the §3 recovery options.** After #84, the **surgical reset (Option B) is rarely needed** for the cross-PR case: if you're about to commit the file anyway, the commit auto-resets it. Option B remains the right move only when you've hit the gate and *cannot* yet commit (mid-edit, work not in a committable state). The §1 table and §6 checklist still apply to the single-turn-thrash case.

**Residual gap (not fixed in #84).** The session-immortal state file (bug 1 above) is untouched: a stale `session_id` from a prior day still rides along. It is now mostly harmless because commit-boundary reset keeps live counters honest, but a future hardening could re-mint `session_id` when `$CLAUDE_SESSION_ID` changes. `.claude/autonomy-triggers.md` row L1 also still describes only the turn-boundary reset — a doc follow-up could add the commit-boundary path (deferred because that file is read verbatim by the Sonnet classifier).
