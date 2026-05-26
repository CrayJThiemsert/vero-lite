# Lesson #12: Loop-detect L1 vs governance-doc fillup passes — batch or surgical-reset, don't full-reset

> **Status:** Codified 2026-05-27 (Session 15b closeout). Pattern first observed live 2026-05-26 Session 14 Phase 2 — `pretooluse_loop_detect.py` denied the 7th successive edit to `docs/plans/0010-step1-message-schema.md` during a Step 6 sign-off pass. Source observation: `docs/research/private/step6-live-ac/scenarioL1-bonus-loop-detect-live-trigger.md`.
> **Severity:** Low (no data loss; gate behaves correctly per Cray E.4 spec). Friction medium-high if mishandled — wholesale state reset clears L2/L3 progress observations too.
> **Cross-references:** PLAN-0008 Step 2 (`pretooluse_loop_detect.py` — the L1 deny gate). [[lesson-0014-argv-vs-stdin-contract-drift]] (sibling lesson — Telegram side of the L1 hook; same hook, different failure mode). `.claude/autonomy-triggers.md` row L1.

## 1. The finding

Closeout / sign-off work on a governance doc (PLAN-NNNN.md, ADR-NNNN.md, STATUS log) routinely involves **6+ successive Edits to the same file** — matrix fill-ins, residual-risk updates, AC verification ticks, sign-off block tweaks. The L1 loop-detect gate is keyed on `(file_path, edit_count >= 6)`, so this **legitimate work pattern** trips the autonomy fail-safe.

The gate is doing exactly what it was designed to do (Cray E.4 threshold = 6). The fix is **not** to retune the threshold — it's to choose the right recovery action for the situation:

| Situation | Right move | Wrong move |
|---|---|---|
| Have 1–2 small edits left, work is genuinely converging | **Surgical reset** of just the L1 counter for the offending target | Full state-file delete (clears L2/L3 too) |
| Have many edits left, work is still in flight | **Batch remaining edits into one Write** (re-read file, plan all edits, single Write) | Continue per-edit and re-trip the gate |
| Edits genuinely span an open-ended exploratory phase | **Pause + reassess with Cray** — the gate is correctly catching a "should we still be in this file?" signal | Bypass / disable the gate |

## 2. The mechanism

`pretooluse_loop_detect.py` reads `.claude/state/loop-counter.json` (written by `posttooluse_progress_observer.py`) and denies any `Write` / `Edit` whose normalized `file_path` has accumulated `count >= 6` since the last turn-boundary reset (which `stop_continuation.py` only triggers for files NOT touched this turn — so a single-file thrash never gets the reset).

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
