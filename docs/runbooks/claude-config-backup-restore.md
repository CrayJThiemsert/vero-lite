# Runbook: Claude Code config backup & restore (WSL + Windows)

**Status:** Active (added Session 206, 2026-08-05)
**Audience:** Tier 2 (Code tab) operators + Cray
**Tooling:** none — inline shell/PowerShell only, deliberately (see §9)
**Related:** `CLAUDE.md` §8 (host-state actions gate), `docs/runbooks/claude-code-setup.md`,
`docs/lessons/0007-harness-exit-code-artifact.md` (command-output-is-evidence)

---

## 1. Why this exists

Claude Code keeps configuration in **two** places on this machine, and **neither is in
git**:

- the WSL2 side (`/home/crayj/.claude*`) — used by `claude` run from a WSL terminal
- the Windows side (`C:\Users\crayj\.claude*`) — used by Claude Desktop

Losing either costs real work: MCP server registrations, plugin state, scheduled tasks,
and the **Tier-0 auto-memory** (`~/.claude/projects/<encoded-cwd>/memory/`) that
`CLAUDE.md` §4 defines as private-and-not-in-repo.

Run this before anything that could rewrite that state:

- `/doctor` — diagnostic, but it can *offer* to migrate the installer or repair the
  auto-updater; that is a **host-state change** under `CLAUDE.md` §8 and needs an
  explicit Cray go
- `claude migrate-installer`, an npm-global permissions fix, or a Claude Code upgrade
- any manual surgery on `.claude.json` / `settings.json`
- plugin marketplace changes you might want to roll back

## 2. The decision rule — "is it in git?"

Do **not** back up by gut feel about importance. Ask one question per path: *does git
already hold it?* Measured on 2026-08-05:

| Path | Status | Back up? |
|------|--------|----------|
| `.claude/skills/`, `.claude/settings.json`, `.claude/hooks/`, `.claude/agents/` | git-tracked | ❌ git is the backup |
| `docs/`, `services/`, `tests/`, `tools/` | git-tracked | ❌ |
| `~/.claude.json` (WSL **and** Windows — different files!) | not in git | ✅ **most important** |
| `~/.claude/settings.json` | not in git | ✅ |
| repo `.claude/settings.local.json` | gitignored (`.gitignore:65`) | ✅ |
| repo `.claude/state/` | gitignored (`.gitignore:69`) | ✅ |
| repo `.claude/launch.json`, `.claude/benchmark-results/` | **untracked** (`??`) | ✅ |
| `~/.claude/projects/*/memory/` | not in git (Tier 0) | ✅ |
| `~/.claude/plugins/`, `commands/`, `plans/`, `scheduled-tasks/`, `tasks/` | not in git | ✅ |
| `~/.claude/projects/*/*.jsonl` (transcripts, ~499 MB) | not in git | ❌ see §8 |
| `~/.claude/.credentials.json`, `.anthropic_api_key` | not in git | ❌ see §8 |
| repo `.claude/handoffs/` (~17 MB) | working notes | ❌ untouched by config surgery |

Confirm the tracked/ignored/untracked split rather than trusting this table — it is a
snapshot, not an invariant:

```bash
cd /home/crayj/work/vero-lite && git status --short .claude/ && git check-ignore -v .claude/state .claude/settings.local.json
```

## 3. Backup — WSL side

```bash
D=~/backup/claude-$(date +%Y%m%d-%H%M) && R=/home/crayj/work/vero-lite && mkdir -p "$D" && cp -a ~/.claude.json ~/.claude/settings.json "$D"/ && cp -a "$R/.claude/settings.local.json" "$R/.claude/launch.json" "$R/.claude/state" "$R/.claude/benchmark-results" "$D"/ && echo "DEST=$D" && ls -la "$D"
```

Destination is **outside the repo** on purpose — `~/backup/…` keeps `git status` clean.

Verify (see §6 for why `diff -r` and not a file count):

```bash
D=<the DEST printed above> && R=/home/crayj/work/vero-lite && md5sum ~/.claude.json "$D/.claude.json" && diff -r "$R/.claude/state" "$D/state" && diff -r "$R/.claude/benchmark-results" "$D/benchmark-results" && echo "ALL_MATCH"
```

Reference run (2026-08-05): 2.2 MB, `state/` 100 files, `benchmark-results/` 100 files,
`diff -r` clean on both, `.claude.json` md5 identical.

## 4. Backup — Windows side

The Windows tree is bigger and mixes secrets and 499 MB of transcripts into the same
directory, so it needs an allowlist, not a blanket copy. Save as `backup-win-claude.ps1`
and run it from any PowerShell:

```powershell
$ErrorActionPreference = 'Stop'
$srcHome = $env:USERPROFILE
$destRoot = Join-Path $srcHome ("backup\claude-win-" + (Get-Date -Format 'yyyyMMdd-HHmm'))
$destClaude = Join-Path $destRoot 'dot-claude'
New-Item -ItemType Directory -Force $destRoot  | Out-Null
New-Item -ItemType Directory -Force $destClaude | Out-Null

Copy-Item "$srcHome\.claude.json"        $destRoot
Copy-Item "$srcHome\.claude.json.backup" $destRoot -ErrorAction SilentlyContinue

foreach ($fileName in 'settings.json', 'mcp-needs-auth-cache.json', 'history.jsonl') {
    $p = Join-Path "$srcHome\.claude" $fileName
    if (Test-Path $p) { Copy-Item $p $destClaude }
}

foreach ($subName in 'commands', 'plans', 'scheduled-tasks', 'tasks', 'plugins', 'backups') {
    $p = Join-Path "$srcHome\.claude" $subName
    if (Test-Path $p) { Copy-Item $p (Join-Path $destClaude $subName) -Recurse }
}

# Tier-0 auto-memory only — never the sibling *.jsonl transcripts
$memRoot = Join-Path $destClaude 'projects-memory'
New-Item -ItemType Directory -Force $memRoot | Out-Null
foreach ($projDir in (Get-ChildItem "$srcHome\.claude\projects" -Directory)) {
    $m = Join-Path $projDir.FullName 'memory'
    if (Test-Path $m) { Copy-Item $m (Join-Path $memRoot $projDir.Name) -Recurse }
}

# stale process locks are worse than useless in a backup — drop them (see §7.3)
Get-ChildItem $destClaude -Recurse -File -Force |
    Where-Object { $_.FullName -like '*\.in_use\*' } |
    Remove-Item -Force -Confirm:$false

Write-Output "DEST=$destRoot"
```

Reference run (2026-08-05): 9.72 MB / 926 files. Memory dirs captured: `vero-lite` 249
files, `D--aaas-pov` 17, `D--smb-flow` 33.

> **Never name a loop variable `$d` in this script.** PowerShell variable names are
> case-insensitive, so `foreach ($d in …)` silently overwrites a `$D` holding the
> destination path. Measured: the report phase printed `DEST=backups` (the last loop
> value) and then hung. The copy survived only because it used different variables.

## 5. Restore

**WSL:**

```bash
B=~/backup/claude-<YYYYMMDD-HHMM> && cp -a "$B/.claude.json" ~/ && cp -a "$B"/{settings.local.json,launch.json,state,benchmark-results} /home/crayj/work/vero-lite/.claude/
```

**Windows:**

```powershell
$B="$env:USERPROFILE\backup\claude-win-<YYYYMMDD-HHMM>"; Copy-Item "$B\.claude.json" $env:USERPROFILE -Force; Copy-Item "$B\dot-claude\*" "$env:USERPROFILE\.claude" -Recurse -Force
```

Restore hygiene:

- **Quit Claude Code / Claude Desktop first.** A running client rewrites `.claude.json`
  in place — measured 2026-08-05: its mtime advanced mid-session, minutes after a backup
  read it — so restoring under a live client gets silently clobbered.
- Restoring `projects-memory` puts the memory dirs back at
  `~/.claude/projects/<encoded-cwd>/memory/` — the Windows script stages them one level
  aside, so copy them back into the matching project dir by name, not with the blanket
  `Copy-Item` above.
- Credentials are **not** in the backup by design — expect to sign in again (§8).
- The copy loses the Windows `Hidden` attribute, so a restored `plugins\…\.git` will be
  visible rather than hidden. Functionally harmless.

## 6. Verifying a backup — the direction rule

A file count proves nothing; two different sets can have the same size. Compare the
**path sets**, and read the two directions separately — they mean opposite things:

| Direction | Meaning | Severity |
|-----------|---------|----------|
| in **source** but not in backup | data was **not captured** | ❌ the failure that matters |
| in **backup** but not in source | superset — extra or since-deleted files | ⚠️ explain it, but not data loss |

```powershell
$s = @(Get-ChildItem $src -Recurse -File -Force | ForEach-Object { $_.FullName.Substring($src.Length) })
$t = @(Get-ChildItem $dst -Recurse -File -Force | ForEach-Object { $_.FullName.Substring($dst.Length) })
Compare-Object $s $t | Format-Table -AutoSize   # '<=' = missing from backup, '=>' = extra
```

When a mismatch appears, **enumerate the differing paths** before judging it. On
2026-08-05 a `532 vs 572` delta on `plugins/` looked like corruption and turned out to be
two benign causes (§7.2, §7.3) with zero files missing.

## 7. Measured gotchas

### 7.1 PowerShell variables are case-insensitive

`$d` and `$D` are one variable. Any `foreach ($d in …)` destroys a `$D` path variable.
Use descriptive names (`$destRoot`, `$subName`) in every backup script.

### 7.2 `Get-ChildItem` skips hidden files; `Copy-Item` copies them

`Get-ChildItem -Recurse -File` **omits** `Hidden` entries, but `Copy-Item -Recurse`
copies them — and the copy **loses** the Hidden attribute. So the same enumeration
command returns fewer files at the source than at the destination even though the data is
identical. Measured: `plugins/` source `532` without `-Force` vs `561` with it; the 29
extra were the marketplace clone's `.git\` internals. **Always pass `-Force` to both
sides when comparing.**

### 7.3 `.in_use\<pid>` files are process locks, not data

`~/.claude/plugins/cache/**/.in_use/` holds PID-named lock markers. They churn constantly
and restoring them re-creates locks for processes that no longer exist. The §4 script
drops them from the backup. To tell a live lock from a dead one:

```powershell
Get-Process -Id <pid> -ErrorAction SilentlyContinue
```

Beware PID reuse: on 2026-08-05 lock `7120` resolved to `SecurityHealthSystray`, an
unrelated process that had inherited the number — a live PID does **not** prove the lock
is live; the process *name* has to fit too.

### 7.4 Deleting "the stale ones" — filter by name, not by folder

A prune written as *"if the folder still exists at source, empty it"* removed **41** files
when **11** were intended, because the folder also held other processes' live locks. Filter
on the exact filenames you mean to remove, and always print an enumerated AFTER state — a
`removed=41` against an expected `11` is what surfaced the over-delete.

### 7.5 WSL command output is evidence

Every verification command here is a claim. Follow `CLAUDE.md` §8: merge streams with
`2>&1`, escape `\$` inside single-quoted `wsl bash -lc` arguments, chain with `&&`, and
never pipe into `head`/`tail` — redirect to a file and read a bounded slice instead.

## 8. Deliberate exclusions

| Excluded | Why | Recovery if lost |
|----------|-----|------------------|
| `~/.claude/.credentials.json`, `.anthropic_api_key` | secrets; a second plaintext copy is added exposure for near-zero benefit | sign in again |
| `~/.claude/projects/*/*.jsonl` (~499 MB) | transcripts already rotate on ~30-day retention; size makes the backup unusable | none — accepted |
| `cache/`, `paste-cache/`, `shell-snapshots/`, `debug/`, `telemetry/`, `sessions/`, `session-env/`, `ide/` | regenerated on demand | automatic |
| repo `.claude/handoffs/` | gitignored working notes; no config-surgery path touches them | none needed |

Verify the secrets really stayed out:

```powershell
Get-ChildItem $destRoot -Recurse -File -Force -Filter '.credentials.json' | Measure-Object   # expect Count = 0
```

## 9. Why there is no script in `tools/`

The commands live inline in this runbook rather than as a committed tool: they run a few
times a year, they are host-specific (two different OS sides of one machine), and a
committed script would be a maintenance surface that silently rots between uses. If the
cadence ever justifies it, promote §3–§4 into `tools/backup/` and note the move here.

## 10. Retention policy — TODO (Cray)

Each run leaves a new timestamped directory under `~/backup/`. Nothing prunes them today,
so they accumulate: ~2.2 MB per WSL run, ~9.7 MB per Windows run.

**Open decision — the trade-off is disk-and-clutter vs how far back you can roll:** keep
the last N runs? keep anything newer than N days? keep one per Claude Code version, since
that is the actual thing a restore is usually undoing? Fill this section in with the rule
plus a one-line prune command, and it becomes the standing policy.

---

*Runbook = operational how-to (`CLAUDE.md` §4 placement rule). Binding rules stay in
`CLAUDE.md`; durable learnings go to `docs/lessons/`.*
