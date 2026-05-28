# Runbook: Cowork outbound-network execution locus

**Status:** Ratified 2026-05-28 (Cray) — OQ-C experiment outcome; v1 design input for PLAN-0012 `vero-bridge`
**Audience:** PLAN-0012 designers + future ADRs/PLANs that depend on Cowork's network locus (e.g. Chat-client OQ-5 from ADR-014 take 3)
**Related:** [Lesson #8 — Cowork K-1/K-2 sandbox facts](../lessons/0008-cowork-tier1-k1-k2-workflow.md) (this runbook extends Lesson #8 with a network-locus dimension; Lesson #8 stays canonical for file ops + bash), [ADR-013 D1](../adr/0013-autonomy-axis-relocation.md) (the MCP-transport-in-Code-Tier-2 decision PLAN-0012 operationalizes), [ADR-0014-WITHDRAWN](../adr/0014-WITHDRAWN.md) (the directive to run this experiment)
**Source experiment:** `docs/research/private/2026-05-28-oq-c-cowork-mcp-locus-experiment.md` (gitignored audit trail)

---

## 1. The question

Where do Cowork-initiated outbound network calls actually exit from? Three a-priori scenarios:

| Scenario | What it means |
|---|---|
| **(i) Desktop-proxy locus** | Cowork's MCP / outbound HTTP exits from **Cray's Windows desktop** (same as `Read`/`Glob`/`Write` per Lesson #8 §1). Loopback to `127.0.0.1` on Cray's machine works. |
| **(ii) Sandbox-VM locus** | Cowork's network call exits from **Cowork's remote cloud Linux VM** (same as `mcp__workspace__bash` per Lesson #8 §1). Loopback hits the VM itself, **not** Cray's machine. Cray's public IP **may** be reachable if VM has outbound + Cray opens a port. |
| **(iii) No capability** | Cowork cannot make outbound network calls at all. |

The answer was empirically unknown — Lesson #8 documents file-op proxy + bash sandbox-side, but did not state network-call locus.

## 2. The finding (ratified)

**Scenario (i) desktop-proxy is RULED OUT for `web_fetch`.** Scenario is **(ii)-leaning** — see §4 for the (ii-a)/(ii-b) refinement that remains open.

Decisive evidence (Cowork session 2026-05-28, ~07:00 +07:00, against an HTTP echo server on Cray's WSL `0.0.0.0:8765`):

1. **`web_fetch` reached the public internet** — control fetch of `https://example.com` returned full rendered body same session.
2. **`web_fetch` returned no body, no token, no headers** for all four local URLs (`127.0.0.1:8765`, `localhost:8765`, `host.docker.internal:8765`, `172.22.59.116:8765` (Cray's WSL2 vNIC)).
3. **Cray's server logged zero inbound connections** for the entire Cowork run window — server-side corroboration that no Cowork request ever reached Cray's loopback or WSL bind.

The combination of (1)+(2)+(3) means `web_fetch` is functional but does not exit Cray's machine. That rules out scenario (i) with HIGH confidence.

### 2.1 Other primitives observed

| Primitive | Status | Notes |
|---|---|---|
| `mcp__workspace__bash` | **Unavailable** | K-1 UNC abort, reproduced 3× — fails before executing any command string. Both `curl` and `python3 urllib` (the two natural network-probe primitives via bash) are blocked. Confirms Lesson #8 §1 K-1 also blocks network probing, not just `validate_handoff.py`. |
| `mcp__workspace__web_fetch` | **Functional but remote-egress** | Works for public destinations; cannot reach any of Cray's local IPs (loopback / WSL / Docker bridge alias). Returns body-only — no HTTP status, no headers — even on success: a **lossy view** for any transport built atop it. |
| `mcp__Claude_in_Chrome__*` | **Present but inert** | `list_connected_browsers` returned `[]`. Would in any case route through Cray's local Chrome (different egress class from the Cowork sandbox), so could not answer the Cowork-locus question even if connected. |

## 3. PLAN-0012 implication

**v1 design rule:** Do **not** ship a Cowork-client in PLAN-0012 v1 that assumes a loopback bus on Cray's machine. The desktop-proxy assumption is empirically false for `web_fetch`. **v1 takes option (a):** drop the Cowork-client from PLAN-0012 v1 and defer to v2 once a tunneled rendezvous (ngrok, cloudflared, or WAN + port-forward) has been designed and the (ii-a) reachability re-test from §4 has been run.

Secondary facts feeding v2 design:

- **`web_fetch` is lossy** — body-only, no status, no headers — preferring a richer outbound primitive when one ships.
- **bash is K-1-blocked** — not a fallback transport on this project.
- **Chrome routes through Cray's local browser** — different egress class; would not answer the Cowork-locus question and is not the same primitive as a sandbox-native MCP transport.

**Tiers unaffected:** Code (Tier 2) and Chat (Tier 1) clients in PLAN-0012 are not affected by this finding — they have their own MCP primitives. Only the Cowork-client section is narrowed.

## 4. Open question — (ii-a) vs (ii-b)

The OQ-C experiment **cannot distinguish** between:

- **(ii-a)** sandbox-VM, **public-IP reachable** — Cowork can hit a publicly-routable endpoint if Cray exposes one
- **(ii-b)** sandbox-VM, **no inbound path** — Cowork's outbound is one-way; nothing can reach Cray's machine from Cowork at all

Reason: URL D in the experiment used `172.22.59.116` (Cray's WSL2 vNIC — an RFC-1918 private address), not a publicly routable IP. A remote/cloud egress could never reach it regardless of firewall, so no inference is possible.

**Discriminating test (deferred to PLAN-0012 Cowork-client v2 design work):** re-run the OQ-C protocol with URL D set to a genuinely public endpoint — options are:

1. **ngrok / cloudflared tunnel** — ~15 min total (tunnel setup + new Cowork dispatch). Lower attack-surface cost than option 2.
2. **Cray's WAN IP + router port-forward** — ~5 min on Cray's side + new dispatch. Higher attack-surface cost (opens a port on the home router for the experiment window).

Either result lets v2 commit to option (b) "Cowork-client reaches Cray via public endpoint" with confidence, or fall back to option (a)+v3 "wait for Anthropic to ship a sandbox-side MCP transport client".

## 5. Anti-patterns / boundary

- **Do not cite this runbook for non-Cowork tier locus.** Chat-tab and Code-tab MCP locus questions are separate. ADR-014 take 3 §OQ-5 (Chat-client) is a parallel-shape experiment using the same `oqc-server.py` scaffold + a Chat-tab dispatch.
- **Do not assume web_fetch will gain new headers / status codes.** This runbook's "lossy view" finding holds across the Cowork session that was tested; if Anthropic ships a richer Cowork outbound primitive, supersede this runbook (don't silently update the conclusion).
- **Do not extrapolate to other Cowork projects.** The K-1/K-2 + network-locus findings are tied to the project topology in Lesson #8 §3 ("when this lesson applies"). A project with a Windows-native checkout path (no UNC) may exhibit different bash behavior; locus likely persists but should be re-tested for the new topology.

## 6. Provenance & supersession

- **Authored by:** code-session-19 (this session), 2026-05-28 (Asia/Bangkok)
- **Source experiment (gitignored audit trail):** `docs/research/private/2026-05-28-oq-c-cowork-mcp-locus-experiment.md`
- **Cowork execution session:** unnamed Cowork session that filled §3.2/§3.3/§4.1 of the source experiment file, 2026-05-28
- **Cray ratification:** 2026-05-28 (this session, via AskUserQuestion turn after Cowork's reply)
- **Supersession trigger:** if Anthropic ships a Cowork-side MCP client primitive, or if the (ii-a)/(ii-b) discriminating re-test from §4 runs and resolves, update §2 and §4 in place and bump the Status header date.
