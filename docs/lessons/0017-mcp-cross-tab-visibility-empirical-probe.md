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

## 3. The server-process model (tab-group routing, not all-shared)

> **2026-05-28 PM correction.** The original §3 (committed in PR #65, drafted from OQ-B probe alone) said the server is "shared across all tabs". Empirical OQ-T3 follow-on probe (T8–T12 in research note `docs/research/private/2026-05-28-oq-b-chat-mcp-spawn-probe.md` §8) **refined** the model: tabs share instances **in groups** based on Desktop-internal routing, not uniformly. Original §3 wording is preserved at end of section for archeology; the corrected model is canonical. This correction is itself a meta-example of §5 (empirical-probe-before-trivial-resolution) — the original §3 was an under-specified inference from probe data that didn't include per-call PID evidence.

Claude Desktop spawns MCP server processes **at Desktop startup time** based on `mcpServers` config. The observed pattern (PLAN-0012 OQ-B + OQ-T3, single config entry, fresh Desktop launch):

```
$ ps aux | grep vero_bridge_probe | grep -v grep
crayj  605  pts/4  uv run --extra dev python tools/probes/vero_bridge_probe.py
crayj  613  pts/4  /home/crayj/work/vero-lite/.venv/bin/python3 tools/probes/vero_bridge_probe.py
crayj 2065  pts/5  uv run --extra dev python tools/probes/vero_bridge_probe.py
crayj 2092  pts/5  /home/crayj/work/vero-lite/.venv/bin/python3 tools/probes/vero_bridge_probe.py
```

**2 server instance pairs** for **1** config entry. Each pair = parent `uv run` (the spawn wrapper) + child `python3` (the actual server). The instances are **routed to tabs in groups** by Desktop-internal logic, not uniformly shared.

### 3.1 Tab-group routing pattern (empirical, OQ-T3 T8–T12)

When each tab invoked `bridge_whoami(claimed_tag)` (which returns the server's own PID):

| Tab | claimed_tag | PID returned | stdin_fd | Instance |
|---|---|---|---|---|
| Chat (T8) | `chat` | **613** | `pipe:[45615]` | A (pts/4) |
| Chat (T10 spoof) | `cowork` | **613** | `pipe:[45615]` | A — same instance |
| Cowork (T9) | `cowork` | **2092** | `pipe:[52773]` | B (pts/5) |
| Cowork (T11 spoof) | `chat` | **2092** | `pipe:[52773]` | B — same instance |
| Code (T12) | `code` | **2092** | `pipe:[52773]` | B — same as Cowork! |

**Refined model:**
- **Chat → instance A (alone)**
- **Code + Cowork → instance B (share)**

The routing rule is Desktop-internal — likely based on tab grouping (window? panel? tab-type?). It is **not externally controllable** and may differ across Desktop versions / install formats / window configurations.

### 3.2 Why this matters

- **Per-client identity has tiers of discriminability.** Under stdio-MCP, the server can discriminate **Chat vs (Code∪Cowork)** via PID/pipe-fd because they're on different instances. The server **cannot** discriminate **Code vs Cowork** via any transport-level signal (they share PID, ppid, stdin_fd, stdout_fd). And `claimed_tag` is fully spoofable — server echoes it verbatim with no native verify mechanism (T10, T11 empirical proof). PLAN-0012 OQ-T3 was RESOLVED 2026-05-28 PM with **Option I (capability-by-tool-design)** — `claimed_tag` retained as audit-only, tool surface restricted to tab-tier-safe operations, dangerous operations not exposed on bridge.

- **`env_keys_seen` is empty under Desktop spawn.** Desktop strips Claude-injected environment variables (CLAUDE_*, ANTHROPIC_*, MCP_*) when spawning the server via `wsl bash -lc '...'`. The probe sanity-check from CLI showed CLAUDE_TIER + ANTHROPIC_API_KEY in env, but T8–T12 from actual Desktop spawn showed `env_keys_seen: []`. **No env-based per-client discriminator is available.** This rules out the obvious "set per-tab env var" identity mechanism.

- **State accumulates across the entire Desktop session.** Server is long-lived (Desktop lifetime). Server processes should be **stateless** by design — any per-call state belongs in arguments or returned values, not server memory. State in server memory persists across tab switches and across hours of Desktop uptime.

- **Crash recovery is your problem.** No auto-respawn observed (server long-lived, no chaos test yet). PLAN-0012 OQ-T1 (failure mode) should pin fail-closed semantics — if server crashes, Cray notices, not a silent partial-degradation.

### 3.3 Archeology — original §3 wording (pre-2026-05-28-PM correction)

For provenance, the original §3 wording (PR #65 drafted from OQ-B `bridge_ping` evidence alone, before OQ-T3 follow-on probe):

> "*2 server instance pairs* for *1* config entry. … *the same PIDs persisted across all 3 tab probes (Chat T2/T4, Code T3, Cowork T7)* — no new instance spawned when a tab connected. … Per-client identity is not free. Under stdio-MCP, the '1 client per stdio session' assumption is **wrong** — the same server process serves multiple logical clients (Chat + Code + Cowork in the same window)."

The wording was correct that PIDs persisted across probe calls (server is long-lived) but **wrong** in inferring "same server process serves all clients" — `bridge_ping` returned no PID, so the inference was from ps aux state stability (which only told us the set of PIDs was constant, not which PID answered which call). The OQ-T3 follow-on probe added per-call PID evidence and revealed the tab-group routing pattern. **The lesson that codified empirical-probe discipline was itself drafted on insufficient empirical evidence** — see §5 5th-step refinement below.

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
5. **Does your probe capture per-call evidence that links system-level state to protocol-level behavior?** (Added 2026-05-28 PM after the OQ-T3 episode — see below.) If your probe relies on system-level introspection (ps aux, tasklist, ls), the probe should also capture per-call evidence (a tool that returns the answering server's PID, fd, or other state) that proves which system-level entity answered each protocol-level call. `ps aux` tells you what processes exist; only the protocol can tell you which process answered your call. Skipping this distinction produced the original §3 mis-inference: "PIDs persisted across probes" was read as "same process serves all tabs" when in fact different tabs hit different processes from the persistent set.

The session-20 → session-21 OQ-T3 episode (and its 2026-05-28 PM correction documented in §3.3) is a clean cascading example: step 1 + step 3 + step 5 all failed. The claim was observable (`ps aux` + `bridge_whoami` could have caught it), depended on undocumented Desktop spawn-model behavior, and the original probe used only system-level introspection without the per-call protocol-level link. The correction itself required a new probe (`bridge_whoami` returning the answering server's PID) — proving that even **the lesson that codified empirical-probe discipline was itself drafted on insufficient empirical evidence**. The corrected §3 documents the true tab-group routing pattern; the corrected §5 documents the 5th-step refinement that surfaces this kind of inference gap before it lands in a tracked artifact.

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
