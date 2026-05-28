# Lesson #16: Claude Desktop UWP (Microsoft Store) — `mcpServers` config lives in package LocalCache, not `%APPDATA%`

> **Status:** Codified 2026-05-28 (Session 21 closeout). Pattern surfaced 2026-05-28 Session 20 during PLAN-0012 OQ-B probe (`docs/research/private/2026-05-28-oq-b-chat-mcp-spawn-probe.md` §1.1 + §4.1) — initial merge of `mcpServers.vero-bridge-probe` into `%APPDATA%\Claude\claude_desktop_config.json` had **zero effect** on Desktop's tool surface, even after Full-Quit + restart. The cause was that Microsoft Store (UWP) builds redirect `%APPDATA%\Claude\` to a per-package LocalCache directory inside the package sandbox; the file at `%APPDATA%` is an orphan that Desktop never reads.
> **Severity:** High (silent — editing the "obvious" path looks like it should work and produces no error; the only signal is the absence of expected tool-surface changes). Compounds with [[lesson-0013-claude-desktop-process-env-cache-secret-rotation]] — both are "Desktop's runtime context is non-obvious from the outside" failure modes.
> **Cross-references:** [[lesson-0008-cowork-tier1-k1-k2-workflow]] (tab tool-scope baseline — needs updating after this lesson; the §1 table snapshot is now known to be incomplete for the user-MCP channel). [[memory_project_claude_desktop_strips_anthropic_api_key]] — sibling root-cause family (Desktop's filesystem + env handling between Windows and the UWP sandbox is non-obvious in multiple directions).

## 1. The finding

Claude Desktop on Windows ships in **two packaging formats**:

| Format | `claude_desktop_config.json` location | Documented in |
|---|---|---|
| **Standalone installer** (`.exe` from claude.ai/download) | `%APPDATA%\Claude\claude_desktop_config.json` = `C:\Users\<user>\AppData\Roaming\Claude\claude_desktop_config.json` | Anthropic docs + most online tutorials |
| **Microsoft Store (UWP)** | `C:\Users\<user>\AppData\Local\Packages\Claude_<package-id>\LocalCache\Roaming\Claude\claude_desktop_config.json` | **Not** documented in mainstream sources at time of this lesson (2026-05-28) |

The Store install **does not** read from `%APPDATA%\Claude\` — that path is silently orphan (or doesn't exist at all for fresh installs). UWP virtualization redirects the app's view of `%APPDATA%\<app>\` to `LocalCache\Roaming\<app>\` inside the package sandbox.

The failure mode is silent: editing the orphan path produces no error, the JSON parses fine (because Desktop never opens it), Desktop launches normally, and tabs show no new MCP tools. There is no log line saying "config not found" — the file Desktop is actually reading (the LocalCache one) is already valid (likely empty `{}` or has `coworkUserFilesPath` + `preferences` keys only), so nothing complains.

## 2. The mechanism

```
T0  Cray installs Claude Desktop from         → UWP package "Claude_pzs8sxrjxfjjc" registered
    Microsoft Store                              package sandbox: C:\Users\crayj\AppData\Local\
                                                   Packages\Claude_pzs8sxrjxfjjc\

T0  First Desktop launch                      → Desktop writes initial config to
                                                   .../LocalCache/Roaming/Claude/
                                                   claude_desktop_config.json
                                                 (UWP-virtualized %APPDATA%)
                                                 %APPDATA%\Claude\ is NOT created
                                                 (or is created empty by some other tool)

T1  Cray follows online MCP tutorial          → opens %APPDATA%\Claude\claude_desktop_config.json
    "add mcpServers to %APPDATA%\Claude\..."     creates the file if absent, edits it
                                                 file at %APPDATA%\Claude\ now has the merge,
                                                 but it is an ORPHAN (no process reads it)

T1  Cray Full-Quits + restarts Desktop        → Desktop reads .../LocalCache/Roaming/Claude/
                                                   claude_desktop_config.json (the real one)
                                                 sees NO mcpServers
                                                 spawns no MCP server processes
                                                 tabs see no new tools

T1  Cray runs ps aux | grep vero_bridge_probe → no matches (correctly — Desktop never read
                                                 the orphan, so it never spawned anything)

T2  Cray's "did the config take?" check       → checks %APPDATA%\Claude\claude_desktop_config.json
    on the orphan path                           sees mcpServers ✅ (because they put it there)
                                                 false-positive — the file with the merge
                                                 IS NOT the file Desktop reads

T3  Conclusion (wrong): "Desktop UWP doesn't  → A1 stdio-MCP path declared unworkable;
    honor mcpServers"                            PLAN-0012 OQ-A pivots away from stdio-MCP
                                                 to a more complex transport
                                                 (HTTP-loopback, named pipe, etc.) —
                                                 wasted design cycles
```

## 3. Reproduction

```powershell
# T0 — confirm install format
Get-AppxPackage -Name "*Claude*" | Select-Object Name, PackageFullName
# UWP install → returns a row with PackageFullName like "Claude_<version>_<arch>__<pubid>"
# Standalone install → returns nothing (or an unrelated row)
```

```powershell
# T1 — locate the correct config path for UWP install
$pkg = (Get-AppxPackage -Name "*Claude*").PackageFamilyName  # e.g. "Claude_pzs8sxrjxfjjc"
$cfgUWP   = "$env:LOCALAPPDATA\Packages\$pkg\LocalCache\Roaming\Claude\claude_desktop_config.json"
$cfgOrphan = "$env:APPDATA\Claude\claude_desktop_config.json"
Test-Path $cfgUWP    # → True (this is what Desktop reads)
Test-Path $cfgOrphan # → False or True (irrelevant either way for UWP)
```

```bash
# WSL equivalent (Lesson #16 was discovered through WSL diagnostics)
ls -la "/mnt/c/Users/$USER/AppData/Local/Packages/Claude_pzs8sxrjxfjjc/LocalCache/Roaming/Claude/"
# → shows claude_desktop_config.json + logs/ + sometimes a session_token cache
ls -la "/mnt/c/Users/$USER/AppData/Roaming/Claude/" 2>&1 || echo "(orphan path absent for UWP)"
```

## 4. Prevention checklist

Before editing `claude_desktop_config.json` on a Windows machine:

1. **Confirm install format first.** `Get-AppxPackage -Name "*Claude*"` — if it returns a row with a `PackageFullName`, you are on UWP. **Do not** use `%APPDATA%\Claude\`.
2. **Use the correct path per format** (see §1 table). For UWP, the canonical path is:
   ```
   C:\Users\<user>\AppData\Local\Packages\<package-name>\LocalCache\Roaming\Claude\claude_desktop_config.json
   ```
   The `<package-name>` is stable for a given Microsoft Store listing — record it in project memory / CLAUDE.md if you'll edit the file repeatedly. (For vero-lite as of 2026-05-28: `Claude_pzs8sxrjxfjjc`.)
3. **Race-condition mitigation.** Desktop holds config in-memory and writes it back to disk on quit. **Full-Quit Desktop before** editing the on-disk config, then verify the edit is still present on disk after Desktop has fully exited (before relaunching). If you edit while Desktop is alive, the quit-time write-back will erase your changes. (This applies to both standalone and UWP installs.)
4. **Sanity-check after restart.** After Full-Quit + restart, verify Desktop actually read the config by:
   - `ps aux | grep <your-server-binary>` (or `tasklist` on Windows) — the server process should be running
   - From any tab, list MCP tools — your server's tools should appear in the deferred list (`mcp__<server>__<tool>`)
   - From a tab, invoke the tool — end-to-end roundtrip confirms the channel is live

## 5. Mistakes to avoid

- ❌ **Don't trust tutorials that say "edit `%APPDATA%\Claude\claude_desktop_config.json`"** without first verifying your install format. Most public Anthropic MCP tutorials predate the Microsoft Store distribution and document only the standalone path.
- ❌ **Don't conclude "Desktop doesn't honor mcpServers"** based on a single test. If `mcpServers` is at the orphan path, Desktop honors the config at its real path — which doesn't have `mcpServers` because you edited the wrong file. Verify the file Desktop reads (per §3) before declaring the feature unworkable.
- ❌ **Don't edit config while Desktop is alive.** Quit-time write-back will erase your changes (per §4 step 3 mitigation).
- ❌ **Don't assume both files are the same.** A symlink or junction would unify them, but neither install format creates one by default. Treating `%APPDATA%\Claude\` and `LocalCache\Roaming\Claude\` as interchangeable is wrong on UWP.

## 6. Why this matters for vero-lite

This lesson is a **prerequisite** for PLAN-0012 (`vero-bridge` MCP transport) v1 execution on UWP-installed Claude Desktop machines (which includes Cray's primary dev machine). Without correct config path, the entire stdio-MCP transport approach (OQ-A = A1, ratified 2026-05-28 alongside this lesson) would appear unworkable through no fault of the design. The probe that established OQ-B RESOLVED YES (`docs/research/private/2026-05-28-oq-b-chat-mcp-spawn-probe.md`) was only possible after this path was discovered.

For Phase 1 of PLAN-0012 (Code-side server + Chat-client transport), the deployment instructions must reference the correct path per install format. A future runbook (likely `docs/runbooks/vero-bridge-deployment.md` once Phase 1 ships) should embed this lesson by reference.

## 7. Related artifacts

- `docs/research/private/2026-05-28-oq-b-chat-mcp-spawn-probe.md` §1.1 (UWP sandbox path discovery), §4.1 (this lesson's origin) — gitignored research note
- `docs/plans/0012-vero-bridge.md` §Open Questions OQ-B — resolved YES contingent on this lesson's mitigations being followed
- `.claude/handoffs/session-20/2026-05-28-1025-code-session21-midflight.md` §1 "Claude Desktop UWP sandbox" — first written-down articulation of the path (mid-flight working note; this lesson is the codified version)
- `docs/lessons/0013-claude-desktop-process-env-cache-secret-rotation.md` — sibling Desktop-runtime-context lesson

---

*Codified by Code session 21 from OQ-B probe evidence. AI-assisted; no `Co-Authored-By` trailer per CLAUDE.md §7.*
