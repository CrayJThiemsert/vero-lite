# Runbook: PLAN-0010 loop-dispatcher scheduled task

> **Purpose:** Operationalize the PLAN-0010 Phase 4 Code Desktop scheduled
> task that drains `loop/inbox/` via `tools/loop/dispatcher.py` on a
> recurring cadence — closing the autonomy-loop primitive without
> requiring a human in the dispatch path.

## Status

- **Shipped:** session 17 (2026-05-27) — see PLAN-0010 Phase 4 PR
- **Type:** Code Desktop scheduled task (Local — Anthropic-cloud routine
  is **not** used; CLAUDE.md §11 + Lesson #9 require Sonnet 4.6+ on
  local checkout with full bash + git)
- **Cadence:** Hourly (matches Cray's "1-hour minimum cadence is
  acceptable" operator constraint from the 2026-05-25 research note)
- **Companion task:** `phase35-smoke-code-reader` (existing — observation-only
  smoke; this task is its commit-capable successor for real workloads)

## What it does

1. Reads `loop/inbox/*.msg.md` (mtime order)
2. Parses each message via `tools.loop._schema.parse_message_file`
3. Dispatches to a message-type handler (currently no-op handler;
   real handlers land in PLAN-0010 Step 5)
4. Atomically archives to `loop/processed/`
5. Prunes `loop/processed/` per the §6 retention policy (30-day age,
   100 MB size cap, 200-entry floor)
6. Surfaces failures via Telegram (`tools/notify/telegram.sh`) if
   `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` are set. Three alert reasons:
   - `poison_message` — per message, after `poison_threshold` (default 3)
     repeated dispatch failures on the same message.
   - `cycle_failures` — **one aggregate ping per cycle** when `parse_failed > 0`
     or `dispatch_failed > 0`, so a single malformed message (bad filename /
     bad frontmatter) is not silently quarantined with no push signal. Added
     after the session-29 live-drain finding (a valid-body / bad-filename
     message parse-failed with no alert under the poison-only policy).
   - `same_fs_check_failed` — fatal: inbox + processed on different
     filesystems → the scan aborts (the atomic-mv invariant cannot hold).

   `expired` is a benign TTL lifecycle outcome and is deliberately **not**
   alerted.

## One-time setup (Cray)

The `SKILL.md` prompt is checked into `~/.claude/scheduled-tasks/loop-dispatcher/SKILL.md`
(Windows path: `C:\Users\crayj\.claude\scheduled-tasks\loop-dispatcher\SKILL.md`).
The scheduled-task **schedule + folder + model + enabled** state is set in
the Claude Code Desktop UI, not the SKILL.md (per the routines docs:
https://code.claude.com/docs/en/desktop-scheduled-tasks).

Steps in Claude Code Desktop:

1. Open Desktop → **Routines** (left sidebar)
2. Click **New routine** → select **Local** (Desktop scheduled task — NOT
   Remote/Cloud; the loop dispatcher needs the local checkout)
3. **Name:** `loop-dispatcher` (Desktop should auto-detect the existing
   SKILL.md at the path above)
4. **Folder:** `~/work/vero-lite` (Windows: `\\wsl.localhost\Ubuntu-24.04\home\crayj\work\vero-lite`)
5. **Schedule:** Hourly (or custom `every 1 hour`)
6. **Model:** Sonnet 4.6 (per Lesson #9 Auto-mode + classifier floor)
7. **Permission mode:** Auto (per ADR-013 D2 — composed identity gate
   handles the commit boundary regardless of permission mode)
8. **Worktree:** OFF (the dispatcher needs to see the live `loop/inbox/`,
   which is on `main` working tree; worktree mode would isolate it from
   producer fires)
9. **Enabled:** Yes
10. Click **Save**, then **Run now** once to verify the task fires + reports

## Verification (one-shot smoke)

Without waiting for the scheduled fire, you can verify the dispatcher
chain works from any Code session:

```bash
wsl bash -lc 'cd ~/work/vero-lite && uv run --extra dev python -m tools.loop.dispatcher --quiet 2>&1'
```

Expected output (one line):

```
scan_cycle: ok=N parse_failed=N expired=N dispatch_failed=N poison=N skipped_idempotent=N pruned=N elapsed_ms=N
```

- `ok=N` — messages dispatched + archived this cycle
- `skipped_idempotent=N` — messages already in `processed/` with same
  name as an inbox entry (race-loser or replay); inbox copy unlinked
- `parse_failed=N` / `expired=N` / `poison=N` — failure dispositions
  (each with a sibling `.{kind}.log` next to the archived file)
- `pruned=N` — old `processed/` entries removed per retention policy

## Observability

| Signal | Location |
|---|---|
| Per-run summary | scheduled-task report message (Desktop UI Run history) |
| Per-run stdout | scheduled-task transcript (Desktop UI Run history) |
| Failure alerts | Telegram (if env vars set), stderr otherwise — reasons: `poison_message`, `cycle_failures`, `same_fs_check_failed` |
| Archived messages | `loop/processed/<name>.msg.md` (gitignored) |
| Sibling logs | `loop/processed/<name>.msg.md.{parse-error\|expired\|poison}.log` |
| Failure-counter state | `loop/.failures.json` (gitignored; per-process tmp suffix per Fix 2) |

## Known operational behaviors

- **App-open + machine-awake gate.** Local scheduled tasks pause when the
  app closes or the machine sleeps. On wake/reopen, Desktop fires **one**
  catch-up for the most recently missed slot in the last 7 days; older
  misses are discarded. This is a documented Anthropic constraint, not
  a bug — fits the heartbeat-class semantics of the current loop.
- **Idle-sleep prevention.** Settings → Desktop app → General → "Keep
  computer awake" prevents idle-sleep, **but closing the laptop lid
  still sleeps** (Cray's typical "leave Legion plugged in, lid open"
  topology is correct).
- **Concurrent fires.** If a manual `uv run python -m tools.loop.dispatcher`
  races with a scheduled-task fire on the same inbox, both processes are
  safe: `_archive` returns None for the race loser (Fix 1) and
  `save_failure_state` uses a per-pid tmp path (Fix 2). The scan summary
  reports the race as `skipped_idempotent=N` for the loser. See
  `tests/loop/test_dispatcher.py` PLAN-0010 Phase 4 test block.
- **Empty inbox.** No-op cycle; report shows all zeros. Not a failure.
- **Producer drift.** Cowork (the producer side) may write messages with
  a claimed-time in the body that diverges from the inbox mtime. The
  dispatcher trusts mtime (Step 1 §2 binding); the claimed-time is for
  archeology only. The Cowork smoke evidence in `docs/STATUS.md` shows
  +4–13h drift live without ill effect.

## Recovery

| Symptom | Recovery |
|---|---|
| Scheduled task didn't fire | Check Desktop app is open + machine awake; click "Run now" manually to confirm task is enabled + reachable |
| Dispatcher exits non-zero | Read the scheduled-task transcript for the full error; usually a same-filesystem check failure or a permission issue on `loop/processed/` |
| Inbox keeps growing despite task firing | Verify the dispatcher is actually running against the right inbox (`folder` field in scheduled task UI); messages may be malformed (check `parse_failed` count + sibling `.parse-error.log` files) |
| Poison alert | Read `loop/processed/<name>.msg.md.poison.log` for the failure signature; surface to Cray + leave message archived |
| `loop/.failures.json` corrupt | Delete it — `load_failure_state` treats missing/corrupt as empty (graceful) |

## Related

- PLAN-0010: `docs/plans/0010-phase3-5-scheduled-task-autonomy-loop.md`
- Archived spec: `docs/plans/done/0010-step1-message-schema.md` §5
  (Phase 4 unblock criteria + 2 bug fix specs)
- Research: `docs/research/private/2026-05-25-local-scheduled-task-autonomy-loop.md`
  §4 (Local vs Cloud comparison + operator constraints)
- ADR-013 D2: composed identity gate ensures `tier=code` for the
  scheduled-task session; G5 in `.claude/hooks/pretooluse_git_deny.py`
  enforces "only Code commits" boundary
- CLAUDE.md §11: Tier 2 (Code) operational policy
