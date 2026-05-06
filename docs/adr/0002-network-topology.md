# ADR-002: Network Topology — Cray ↔ MS-S1 MAX

**Status:** Accepted
**Date:** 2026-05-05
**Deciders:** Jirachai Thiemsert (founder)
**Related:** ADR-001 (LLM models), PLAN-001 (starter pack)

## Context

vero-lite Phase 1 development uses two physical machines on the same LAN:

- **Cray-Legion5Pro** — primary development laptop (Windows 11 + WSL2 Ubuntu 24.04). Codebase, Docker Desktop, IDE, agents.
- **CRAY-MS-S1-MAX** — local LLM inference server (Windows 11 + Ollama). LAN IP: `192.168.1.133`. Hosts 3 Ollama models (see ADR-001).

The development workflow requires the FastAPI app and Claude Code agents running on Cray-Legion5Pro to call Ollama on MS-S1 MAX over LAN. This requires a stable network bridge with:

1. Predictable hostname (so configs don't reference raw IPs)
2. Firewall opening for the Ollama port that does not expose the LLM endpoint to public networks (e.g., café WiFi)
3. Stable resolution from inside WSL2 (which has its own virtualized network)

## Decision

The network topology is fixed as follows:

```
┌──────────────────────────────────┐         ┌──────────────────────────────────┐
│ Cray-Legion5Pro                  │         │ CRAY-MS-S1-MAX                   │
│ (Dev machine)                    │         │ (LLM server)                     │
├──────────────────────────────────┤         ├──────────────────────────────────┤
│ Windows host: Cray-Legion5Pro    │         │ Windows host: CRAY-MS-S1-MAX     │
│ WSL2: Ubuntu 24.04 (crayj)       │         │ Ollama 0.0.0.0:11434             │
│   /etc/hosts:                    │  LAN    │ Firewall rule:                   │
│     192.168.1.133  ms-s1-max  ──┼─────────┤  "Ollama API (vero-lite)"        │
│   curl http://ms-s1-max:11434/   │         │  Profile: Domain, Private        │
│     api/tags  → HTTP 200         │         │  TCP inbound 11434               │
└──────────────────────────────────┘         └──────────────────────────────────┘
```

**Hostname mapping (Cray WSL `/etc/hosts`):**

```
192.168.1.133  ms-s1-max
```

**Firewall rule (MS-S1 MAX, Windows Defender Firewall):**

```powershell
New-NetFirewallRule `
  -DisplayName "Ollama API (vero-lite)" `
  -Direction Inbound `
  -Protocol TCP `
  -LocalPort 11434 `
  -Action Allow `
  -Profile Private,Domain `
  -Description "Allow Ollama API access from LAN for vero-lite project"
```

**Ollama binding (MS-S1 MAX):**

`OLLAMA_HOST=0.0.0.0` set as Machine-level environment variable. Ollama listens on `[::]:11434` (IPv6 dual-stack, accepts IPv4 connections via mapped addresses).

**Service discovery convention:** All vero-lite code, configs, and `.env` files reference Ollama as `http://ms-s1-max:11434` — never raw IP, never `localhost` (except for self-tests on MS-S1 MAX itself).

## Consequences

### Positive
- **Stability:** Code and demos do not break when MS-S1 MAX gets a new DHCP lease (only `/etc/hosts` needs update).
- **Security boundary:** Ollama port is closed when laptop joins a "Public" network classification (café, airport, hotel WiFi). Reduced attack surface for the local LLM endpoint.
- **Reproducibility:** Any new dev machine can be onboarded by adding one `/etc/hosts` line.
- **PDPA-aligned:** All LLM traffic stays on-prem LAN; never traverses public internet.

### Negative
- **Manual `/etc/hosts` maintenance:** Every WSL distro on every dev machine needs the entry. Mitigated by bootstrap script (`scripts/bootstrap.sh`) and documented in CLAUDE.md.
- **WSL2 hosts file regeneration:** WSL2 may regenerate `/etc/hosts` on Windows reboot. See "Persistence note" below.
- **DHCP dependency:** If MS-S1 MAX's IP changes (e.g., router replacement), all dev machines need `/etc/hosts` update. Could be mitigated by static DHCP reservation on the router (recommended but not part of this ADR).
- **Single point of failure:** MS-S1 MAX outage = all dev environments lose primary LLM. Cloud fallback (Claude API) handles this; documented in ADR-001.

### Neutral
- IPv6-first listening (`[::]:11434`) is intentional and correct; IPv4 connections work via dual-stack.
- LAN trust model assumes the home/office network is reasonably secured (WPA2/WPA3, no untrusted devices). This is fine for Phase 1 but should be re-evaluated when first design partner deploys to a real clinic environment (ADR-NN, future).

## Persistence Note: WSL2 `/etc/hosts` Regeneration

WSL2 by default regenerates `/etc/hosts` on each Windows boot, which can wipe the `ms-s1-max` entry. To prevent this, add to `/etc/wsl.conf`:

```ini
[network]
generateHosts = false
```

Then `wsl --shutdown` from PowerShell host and re-open WSL.

**Decision:** This is **recommended but not required**. The bootstrap script (`scripts/bootstrap.sh`) checks for the entry and re-adds if missing, so even without `wsl.conf` change, dev environment self-heals after boot.

## Alternatives Considered

### Alternative 1: mDNS / Avahi (`ms-s1-max.local`)
- **Pros:** No `/etc/hosts` maintenance; auto-discovery
- **Cons:** mDNS reliability across Windows + WSL2 + Linux is inconsistent; Bonjour (Apple) install required on Windows; one more moving part
- **Why rejected:** Static `/etc/hosts` is simpler and more reliable for a 2-machine setup. Re-evaluate at 5+ machines.

### Alternative 2: Reverse SSH tunnel (Cray → MS-S1 MAX)
- **Pros:** Works across NAT; no firewall rule needed on MS-S1 MAX
- **Cons:** Tunnel state to manage; latency overhead; both machines on same LAN already (no NAT issue)
- **Why rejected:** Solving a problem we don't have. LAN-direct is simpler.

### Alternative 3: Tailscale / WireGuard mesh VPN
- **Pros:** Works from anywhere; secure by default; stable hostnames via MagicDNS
- **Cons:** Third-party dependency; additional auth surface; overkill for local dev
- **Why rejected:** Premature for Phase 1. Will be reconsidered when remote development or design partner site connectivity becomes a need (likely ADR-NN, month 4+).

### Alternative 4: Open firewall port to Public profile too
- **Pros:** Works on any network without thinking
- **Cons:** Massive security hole — exposes LLM to anyone on café WiFi who can scan port 11434
- **Why rejected:** Security-by-default. The Private+Domain restriction is intentional.

## References

- Verified during Session 2 (2026-05-05) end-to-end test:
  ```bash
  curl -s http://ms-s1-max:11434/api/tags  # HTTP 200, models JSON returned
  ```
- Microsoft Defender Firewall profiles: https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/best-practices-configuring
- WSL2 networking: https://learn.microsoft.com/en-us/windows/wsl/networking
- Ollama OLLAMA_HOST documentation: https://github.com/ollama/ollama/blob/main/docs/faq.md

## Implementation Checklist (already done in Session 2)

- [x] `OLLAMA_HOST=0.0.0.0` set on MS-S1 MAX (Machine env var)
- [x] Ollama process restarted, verified listening on `[::]:11434`
- [x] Firewall rule "Ollama API (vero-lite)" created (Private+Domain only)
- [x] `/etc/hosts` entry added on Cray WSL
- [x] End-to-end test: `curl http://ms-s1-max:11434/api/tags` returns 200 with 3-model inventory
- [ ] (Optional, deferred) `/etc/wsl.conf` `generateHosts=false`
- [ ] (Optional, deferred) Static DHCP reservation for `192.168.1.133` on router
