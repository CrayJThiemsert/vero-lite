# Lesson #13: Claude Desktop process-env cache + secret rotation — restart Desktop after every Windows User-scope env update

> **Status:** Codified 2026-05-27 (Session 15b closeout). Pattern surfaced 2026-05-26 Session 15a during Telegram bot token rotation — Cray rotated `TELEGRAM_BOT_TOKEN` via BotFather + `setx`, but Claude Desktop's running process kept the old (revoked) value cached and forwarded it to WSL through `WSLENV`. Every subsequent `wsl bash -lc 'bash tools/notify/telegram.sh ...'` failed with HTTP 401, silently consumed by the hooks' best-effort discipline.
> **Severity:** High (silent — failure mode is "secret rotated, everything continues to use the old one until you happen to notice a 401 in a log"). Compounds with [[lesson-0014-argv-vs-stdin-contract-drift]] when both fail at once.
> **Cross-references:** Existing memory [[project-claude-desktop-strips-anthropic-api-key]] — sibling root-cause family (Desktop's env-passing behavior between Windows and WSL is non-obvious in multiple directions). CLAUDE.md §8 ("Public Repository — NEVER commit secrets") — this lesson is the runtime counterpart: secrets are stored in env, env is cached in Desktop, cache invalidation needs explicit action.

## 1. The finding

Claude Desktop (Windows) **captures Windows User-scope environment variables into its process env at launch**. Subsequent updates to the same User-scope variable via `setx` / `reg add` / Control Panel are **invisible to Claude Code** until Desktop is restarted. `WSLENV` then forwards the **stale process-env value** to WSL on every `wsl bash -lc '...'` call.

The failure mode is silent: HTTP 401 from the rotated-token service, captured by hook-level `capture_output=True` + `check=False` (the same discipline that hid the bug class in Lesson #14), exit 0 propagated up. The user only notices when a downstream consumer reports stale data or — in the Telegram case — silence.

## 2. The mechanism

```
T0  Cray launches Claude Desktop          → Desktop captures User env "TOKEN=Abc...mVt0"
T0  Desktop launches claude.exe child     → child inherits "TOKEN=Abc...mVt0" in process env
T0  claude.exe spawns wsl.exe with        → WSL bash sees "TOKEN=Abc...mVt0"
    WSLENV="TELEGRAM_BOT_TOKEN/u:..."

T1  Cray rotates token in BotFather       → new token "Abc...OSmeY" (last 5 bytes change;
    + runs setx TELEGRAM_BOT_TOKEN ...      bot id 8492382723 prefix is stable)

T2  Cray runs PowerShell verify           → User scope reads "TOKEN=Abc...OSmeY" ✅ NEW
    [Environment]::GetEnvironmentVariable(
      "TELEGRAM_BOT_TOKEN", "User")
    → "Abc...OSmeY"
    Invoke-RestMethod ".../getMe" → ok    ✅ NEW token valid

T2  Cray runs hook in Claude Code         → wsl.exe sees "TOKEN=Abc...mVt0" ❌ OLD
    (token still cached in Desktop's        (Desktop never re-read User scope; cache hot)
    process env)                            → HTTP 401 from Telegram API
                                            → telegram.sh logs "non-200 from Telegram API:
                                              HTTP 401" to stderr (captured + discarded
                                              by hook's capture_output=True)
                                            → hook exits 0 (silent failure)

T3  Cray restarts Claude Desktop          → Desktop re-captures User env
                                            → claude.exe child gets "TOKEN=Abc...OSmeY"
                                            → WSL sees NEW token
                                            → next hook fires Telegram correctly ✅
```

The hex-byte comparison that nailed it (Session 15a diagnostic):

| Source | First 12 hex bytes | Last 5 hex bytes |
|---|---|---|
| Windows User scope (NEW, valid) | `38 34 39 32 33 38 32 37 32 33 3A 41` (= `8492382723:A`) | `4F 53 6D 65 59` (= `OSmeY`) |
| WSL via WSLENV (OLD, revoked) | same prefix | `6B 4D 56 74 30` (= `kMVt0`) |

Bot id `8492382723` is stable across rotations (it's the bot user id, not the secret). **Only the secret portion changes** — always compare the **last 5 bytes** when troubleshooting "did the rotation take?", not the prefix.

## 3. Reproduction

```powershell
# T0 — capture current User token + verify Telegram is happy
$t = [Environment]::GetEnvironmentVariable("TELEGRAM_BOT_TOKEN","User")
$old = $t
(Invoke-RestMethod "https://api.telegram.org/bot$t/getMe").ok  # → True

# T1 — rotate via BotFather (manually), then update User scope
setx TELEGRAM_BOT_TOKEN "<new-token-from-botfather>"

# T2 — verify User scope sees the new value
$new = [Environment]::GetEnvironmentVariable("TELEGRAM_BOT_TOKEN","User")
$new -ne $old   # → True (User scope updated)

# T2 — but Claude Code (running in Desktop's process tree) STILL has the old
#      env. Trigger anything that forwards via WSLENV:
wsl bash -lc 'echo $TELEGRAM_BOT_TOKEN | tail -c 6'   # → "kMVt0" (OLD; should be "OSmeY")

# T3 — restart Claude Desktop, then re-run the same command:
wsl bash -lc 'echo $TELEGRAM_BOT_TOKEN | tail -c 6'   # → "OSmeY" (NEW)
```

## 4. The fix — operational discipline

There is no in-process fix from Claude Code's side. The Windows process-env model means a running process literally cannot see post-launch User-scope updates. The discipline is:

**After any secret rotation in Windows User scope, restart Claude Desktop before continuing the session.**

This applies to (at minimum):

- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` — AFK channel
- `ANTHROPIC_API_KEY` — but see [[project-claude-desktop-strips-anthropic-api-key]] (Desktop strips this at the child-env boundary anyway, so the cache is a non-issue for this specific var)
- GitHub PAT (`GH_TOKEN` / `GITHUB_TOKEN`) — gh CLI auth
- AWS / GCP / Azure session credentials, if forwarded via WSLENV

If a session is mid-flight and a restart is undesirable, the workaround is to override the env in the WSL shell directly (`wsl bash -lc 'TELEGRAM_BOT_TOKEN=<new> bash tools/notify/...'`) — but this only affects that one invocation, not the hook subprocess tree.

## 5. Troubleshooting recipe

When a secret-driven workflow starts failing after a rotation:

1. **Verify Windows User scope is correct:**
   ```powershell
   $t = [Environment]::GetEnvironmentVariable("TELEGRAM_BOT_TOKEN","User")
   $t.Substring($t.Length - 5)   # last 5 chars of secret portion
   ```
   Expected: the new value.

2. **Verify the same value reaches WSL:**
   ```bash
   wsl bash -lc 'echo "$TELEGRAM_BOT_TOKEN" | tail -c 6'
   ```
   Expected: same as step 1. If different, Desktop is caching the old value → **restart Claude Desktop**.

3. **Verify end-to-end via the real binary:**
   ```bash
   wsl bash -lc 'bash tools/notify/telegram.sh "rotation verify $(date -u +%s)"; echo "EXIT=$?"'
   ```
   Expected: `EXIT=0`, no `non-200` stderr line, message lands in Telegram chat.

The hex-byte tail comparison (step 1 / step 2) is faster than a full API call and bypasses any caching at the curl / Telegram CDN layer.

## 6. Why this isn't fixed by "use a .env file instead"

Tempting suggestion: stash the secret in `.env` (gitignored), source it in hooks. But:

- CLAUDE.md §8 says NO `.env*` files except `.env.example` in the repo. The gitignore rule is policy, not just safety.
- ADR-013 D5 + PLAN-0007 Step 2 require tokens come from the environment, never from a tracked file. The PolicyShield + detect-secrets layer is designed around this.
- A `.env` file in the worktree creates a different cache invalidation problem (file is read once at session start, edits don't propagate to running subprocesses either — same class of bug, different transport).

The right answer is to make the env-update boundary explicit: secret rotation = Desktop restart, full stop.

## 7. Adjacent observations

- **Existing memory [[project-claude-desktop-strips-anthropic-api-key]]** captures the *opposite* failure mode for the Anthropic API key: Desktop **strips** `ANTHROPIC_API_KEY` from the claude.exe child env (sets it to `""`) for OAuth isolation. Both lessons are the same root-cause family: Desktop is doing something non-obvious at the Windows → child-env boundary. When debugging env-related issues in this project, suspect the boundary before blaming WSLENV or the consumer.
- **The discovery loop in Session 15a took ~3 hours** because we attacked it from the wrong end: first assumed the bot was banned, then assumed `setx` hadn't taken, then assumed WSLENV syntax was wrong, then assumed telegram.sh had a bug — before realizing the process env was simply stale. **Heuristic for next time:** when a freshly-rotated secret fails on first use, suspect the Desktop process-env cache **before** anything else; restart-and-retest takes 60 seconds.
