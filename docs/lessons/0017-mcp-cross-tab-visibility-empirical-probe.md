# Lesson #17: MCP transport across Claude Desktop tabs — verified visibility model + empirical-probe-before-trivial-resolution guard

> **Status:** Codified 2026-05-28 (Session 21 closeout, immediately after [[lesson-0016-claude-desktop-uwp-sandbox-config-path]] + PR #64 merge). Pattern surfaced 2026-05-28 Session 20 → 21 during PLAN-0012 OQ-B probe. Two distinct precision-improving findings woven into one lesson because they share an origin and reinforce each other.
> **Severity:** Medium (silent — wrong assumptions produce plausible-looking transport designs that drift from reality; the failure mode is a refactor cost when the assumption breaks during Phase 1 execution, not an immediate error). Compounds with [[lesson-0016-claude-desktop-uwp-sandbox-config-path]] (sibling Desktop-MCP visibility lesson) and [[lesson-0008-cowork-tier1-k1-k2-workflow]] (sibling cross-tab capability lesson; the §1 table snapshot was incomplete pre-user-MCP).
> **Cross-references:** [[lesson-0016-claude-desktop-uwp-sandbox-config-path]] (prerequisite — without correct config path, the probe that established this lesson would have been a false negative). PLAN-0012 §Open Questions OQ-T3 (refined per §3 server-process model of this lesson). `docs/research/private/2026-05-28-oq-b-chat-mcp-spawn-probe.md` (gitignored evidence note — full verbatim probe matrix that this lesson generalizes from).

## 1. The verified cross-tab MCP visibility model

PLAN-0012 OQ-B probe (T1–T7, 2026-05-28) empirically established that user-MCP servers — configured via `mcpServers` in `claude_desktop_config.json` — are surfaced **uniformly** across all three Claude Desktop tabs (Chat, Code, Cowork), in addition to each tab's own platform-MCP stack. This corrects an earlier assumption (session-20 handoff §1 working note) that Chat had a narrower MCP surface than Cowork.

| Layer | Source of truth | Visible in | Tool surface format |
|---|---|---|---|
| **Platform MCP — Code-specific** | Hosted by Claude Code Director (ccd) | Code tab only | `mcp__ccd_*` loaded + many deferred (Claude_Preview, Claude_in_Chrome, mcp-registry, scheduled-tasks, …) |
| **Platform MCP — Cowork-specific** | Cowork sandbox runtime | Cowork tab only | `mcp__workspace__*`, `mcp__cowork__*`, `mcp__visualize__*` loaded; `cowork-onboarding`, `session_info`, `skills`, `plugins` deferred |
| **Platform MCP — Chat-specific** | Chat runtime (narrowest) | Chat tab only | `Claude in Chrome` deferred (22 tools); historically also `mcp-registry` deferred |
| **Platform MCP — shared across tabs** | Multiple Anthropic-side primitives | Two or more tabs | `Claude_in_Chrome` is in **all 3 tabs** as deferred; `mcp-registry` is in Code + Cowork (Chat too as of 2026-05-28 with `search_mcp_registry` + `suggest_connectors`, but without `list_connectors`) |
| **User-MCP (provisioned via `mcpServers` config)** | `claude_desktop_config.json` (UWP: `LocalCache\Roaming\Claude\…` — see Lesson #16) | **All 3 tabs uniformly** (Chat, Code, Cowork) — verified by T1, T3, T6 | `mcp__<server-name>__<tool-name>` in each tab's deferred list |
| **Registry-MCP (public connector directory)** | Anthropic public registry, queried via `mcp__mcp-registry__search_mcp_registry(keywords)` | Wherever `mcp-registry` is exposed (Code + Cowork; Chat partially) | After install via Connectors UI, becomes a user-MCP-like surface |

**Key takeaway for tab work:** when planning a feature that depends on MCP tool availability across tabs, the **user-MCP channel is the one to design against** (uniform, predictable, controllable). The other layers are tab-specific and Anthropic-controlled — they can change without notice.

## 2. The registry-MCP vs user-MCP distinction (often confused)

| Question | User-MCP (`mcpServers` config) | Registry-MCP (public directory) |
|---|---|---|
| How discovered? | Provisioned at Desktop startup from local config file | Queried at runtime via `search_mcp_registry(keywords)` |
| Who controls? | The Desktop user (you, via config file edits) | Anthropic-hosted public directory |
| Surfaced in tab's deferred list? | Yes, immediately after Desktop restart | No — must be installed via Connectors UI first |
| Listed by `list_connectors`? | **No** (registry directory only — tested T5 with vero-bridge-probe absent) | Yes |
| Where to register a project-specific bridge? | **User-MCP** (this is the intended channel) | Don't — registry is for general-purpose public connectors |

**Anti-pattern:** "Search the registry to confirm my project-bridge is registered." A project-bridge will never be in the public registry; that's not its purpose. Confirm via direct invocation from a tab instead (Lesson #16 §4 step 4 sanity-check).

## 3. The server-process model (shared instances, not per-tab)

Claude Desktop spawns MCP server processes **at Desktop startup time** based on `mcpServers` config. The observed pattern (PLAN-0012 OQ-B, single config entry, fresh Desktop launch):

```
$ ps aux | grep vero_bridge_probe | grep -v grep
crayj  572  pts/4  uv run --extra dev python tools/probes/vero_bridge_probe.py
crayj  580  pts/4  /home/crayj/work/vero-lite/.venv/bin/python3 tools/probes/vero_bridge_probe.py
crayj 1625  pts/5  uv run --extra dev python tools/probes/vero_bridge_probe.py
crayj 1648  pts/5  /home/crayj/work/vero-lite/.venv/bin/python3 tools/probes/vero_bridge_probe.py
```

**2 server instance pairs** for **1** config entry. Each pair = parent `uv run` + child `python3` from the spawn command. The same PIDs **persisted across all 3 tab probes** (Chat T2/T4, Code T3, Cowork T7) — no new instance spawned when a tab connected.

**Working hypothesis (not yet verified — promote to OQ if PLAN-0012 Phase 1 needs it):** Claude Desktop spawns N instances per `mcpServers` entry where N = number of Desktop panels/windows open at launch (or maybe N = 2 always, for warm-start fanout). Tabs within a panel share an instance.

**Why this matters:**

- **Per-client identity is not free.** Under stdio-MCP, the "1 client per stdio session" assumption is **wrong** — the same server process serves multiple logical clients (Chat + Code + Cowork in the same window). Per-client identification at the server requires an explicit `caller_tag` argument convention at the tool-call level (or MCP-level session metadata if the protocol exposes it). PLAN-0012 OQ-T3 has been refined accordingly.
- **State accumulates across the entire Desktop session.** Server is long-lived (Desktop lifetime). Server processes should be **stateless** by design — any per-call state belongs in arguments or returned values, not server memory. State in server memory persists across tab switches and across hours of Desktop uptime.
- **Crash recovery is your problem.** No auto-respawn observed in OQ-B (server long-lived, no chaos test yet). PLAN-0012 OQ-T1 (failure mode) should pin fail-closed semantics — if server crashes, Cray notices, not a silent partial-degradation.

## 4. Diagnostic recipes — verify before drafting transport details

When working on any feature that touches the MCP transport surface (across tabs or within one), use these recipes to verify reality rather than infer.

### 4.1 "Is my user-MCP server actually being spawned?"

```bash
# WSL — assuming the spawn command runs WSL python
wsl bash -lc 'ps aux | grep <your-server-keyword> | grep -v grep'

# Windows — if spawn runs Windows python
wsl bash -lc '/mnt/c/Windows/System32/tasklist.exe /FI "IMAGENAME eq python.exe" 2>&1'
```

A row → spawn worked. No rows → Desktop did not read the `mcpServers` entry (most likely cause: wrong config path; see [[lesson-0016-claude-desktop-uwp-sandbox-config-path]] §1).

### 4.2 "Which tabs see my server's tools?"

In each tab (Chat, Code, Cowork), prompt: "list MCP tools" (paraphrase — do **not** copy verbatim from this lesson; the agent might recognize the verbatim trigger, per [[memory_feedback_live_test_trigger_freshness]]). Look for `<your-server>.<your-tool>` (or `mcp__<your-server>__<your-tool>`) in the deferred list.

If a tab does NOT see your server, check:
- Was Desktop Full-Quit + restarted after the config edit? (Cf. [[lesson-0016-claude-desktop-uwp-sandbox-config-path]] §4 step 3 — quit-time write-back hazard.)
- Is the tab in the same Desktop window as where the server was spawned? (Cross-window behavior unverified as of 2026-05-28.)

### 4.3 "Are multiple tabs sharing the same server instance, or do they each have their own?"

Before opening a 2nd tab: `ps aux | grep <server-keyword>`. Record PIDs. Open 2nd tab, invoke a tool from it. `ps aux` again. Compare:
- **Same PIDs** = shared instance (the common case per OQ-B finding); per-client identity must come from tool arguments
- **New PIDs added** = per-tab spawn (treat with cautious optimism — verify with a 3rd tab)

### 4.4 "Is the server alive across tab idle periods?"

Invoke a tool that returns a timestamp (like `bridge_ping` in OQ-B). Wait. Invoke again. Compare timestamps:
- **Different timestamps, same PID** = server long-lived, persisting state risk (§3 above)
- **Different timestamps, different PID** = respawn happened (likely on tool error or idle timeout — characterize before relying on it)

### 4.5 "Is the public registry telling me what I think it's telling me?"

The public registry (`mcp__mcp-registry__search_mcp_registry`) is **keyword search**, not `list_all`. It returns *public connector candidates that match your keywords*, not *what your Desktop currently has provisioned*. Your project-specific user-MCP servers are **never** in the public registry (§2 above). Don't conflate these channels.

## 5. The meta-lesson: empirical probe before trivially-resolving an OQ

In session 20, OQ-T3 (per-client identity under A1 stdio-MCP) was trivially-resolved as "one client per stdio session — trivial." This was a **plausible inference** from the stdio-MCP protocol shape (each client gets its own session), but it skipped one empirical step: `ps aux`. The session-21 probe revealed the wrong assumption (shared server process across tabs; see §3).

**Pattern:** When an OQ's resolution depends on a system property that you can observe externally (process tree, file existence, port binding, log lines), prefer **observing it** over **inferring it** from protocol shape or platform documentation. Inference is faster but routinely produces silent-wrong answers in this category.

**Prevention checklist before resolving an OQ as "trivial":**

1. **Is the resolution claim observable?** If yes (process count, file path, network port, response shape), observe it before claiming trivial. The cost of `ps aux` is seconds; the cost of a wrong-by-default transport design is a Phase rework.
2. **Has another tab/session already observed the same property?** Search `docs/research/private/` and `.claude/handoffs/` for prior probes. If yes, you may inherit their finding with a citation. If no, you need to probe.
3. **Does the claim depend on documented Anthropic platform behavior?** If yes, the platform docs are advisory only — many behaviors (UWP config path, sandbox bash UNC, Desktop env caching, mcpServers process model) are not documented or are documented inconsistently. Treat platform docs as a hypothesis, not a fact.
4. **Is the claim about your own code?** If yes, trivial-resolution is more defensible (you wrote it, you know its shape). Even then, an end-to-end smoke catches more than a code reading.

The session-20 → session-21 OQ-T3 episode is a clean example of failing step 1 and 3 simultaneously: the claim was observable (`ps aux`) and depended on undocumented Desktop spawn-model behavior, but was resolved by inference instead.

## 6. How to update this lesson when the model changes

The cross-tab visibility model + server-process model in this lesson is **empirical** as of 2026-05-28. Anthropic may change either at any time without notice. When working on PLAN-0012 Phase 1 (or any successor) the implementer **must re-probe** if any of the following has happened since 2026-05-28:

- Claude Desktop major version bump
- New tab type added (e.g., a "Mobile" tab)
- Anthropic ships a documented per-tab MCP scope feature
- Cray switches Desktop install format (UWP ↔ standalone)
- Cray opens multiple Desktop windows simultaneously (multi-window behavior is not characterized as of 2026-05-28)

If a re-probe contradicts §1, §2, or §3 above, update this lesson (don't fork) and reference the new probe artifact in the cross-reference block.

## 7. Related artifacts

- `docs/research/private/2026-05-28-oq-b-chat-mcp-spawn-probe.md` — full verbatim probe matrix T1–T7 (gitignored)
- `docs/lessons/0016-claude-desktop-uwp-sandbox-config-path.md` — prerequisite path discovery
- `docs/plans/0012-vero-bridge.md` §Open Questions — OQ-A pre-decision, OQ-B RESOLVED YES, OQ-T3 refined per this lesson's §3
- `.claude/handoffs/session-20/2026-05-28-1025-code-session21-midflight.md` §1 — first written-down (incomplete) version of the cross-tab table; superseded by §1 of this lesson

---

*Codified by Code session 21 immediately after PR #64 merge, at Cray's request to "บันทึก Lesson ที่พบให้ดี เพื่อให้การทำงานของทุก tab รอบคอบแม่นยำมากขึ้นต่อไป". AI-assisted; no `Co-Authored-By` trailer per CLAUDE.md §7.*
