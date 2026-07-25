# Runbook — SSH admin access to MS-S1 (Cray-Legion5Pro → CRAY-MS-S1-MAX)

**Last verified:** Session 174 (2026-07-25) — set up and confirmed end-to-end in one session.
**Audience:** vero-lite contributors (and Code) operating MS-S1 from the dev laptop.
**Scope:** WSL2 Ubuntu 24.04 client → Windows 11 OpenSSH Server. LAN only.

> **The binding rule is not here.** Any state change on MS-S1 needs **explicit Cray
> go in-session** — that rule lives in [`CLAUDE.md`](../../CLAUDE.md) §8 *Host-State
> Actions*. This runbook is setup + recovery mechanics only. Day-to-day operating
> mechanics live in the `ms-s1-admin` skill; model/benchmark mechanics live in
> `ms-s1-ollama`.

---

## 1. Why this exists

[ADR-002](../adr/0002-network-topology.md) provisioned MS-S1 as an **inference
appliance**: one firewall rule, TCP 11434, profile `Private,Domain`. Nothing else
was reachable. That was sufficient while the only interaction was Ollama.

It stopped being sufficient once deployment/ops questions arrived — Docker Desktop
on MS-S1 is `StartType Manual` and was found `Stopped`, Ollama has no autostart,
and scheduled tasks on the box could not be inspected at all. None of that is
diagnosable over an HTTP model API.

This runbook records the **verified** procedure that opened a second, LAN-only
channel: OpenSSH on TCP 22, same profile scoping as the Ollama rule.

## 2. Current state (verified)

| Property | Value |
|---|---|
| Alias | `ssh ms-s1` (from `~/.ssh/config` in WSL) |
| Host | `192.168.1.133` — `CRAY-MS-S1-MAX` |
| Auth | ed25519 public key, **no passphrase** (required for non-interactive use) |
| Verified with | `ssh -o BatchMode=yes` — proves publickey, no password fallback |
| Remote shell | **Windows PowerShell 5.1** (`DefaultShell` repointed off `cmd.exe`) |
| Token | **Full elevated administrator token**, not UAC-filtered — see §5.3 |
| Firewall | `OpenSSH-Server-In-TCP`, `Enabled True`, profile `Domain, Private` |

## 3. Client side — Cray-Legion5Pro / WSL

Key generation and `~/.ssh` are **global config outside the worktree** → CLAUDE.md
§8 applies; get Cray's go before running these.

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
ssh-keygen -t ed25519 -N '' -C 'crayj@Cray-Legion5Pro-wsl (vero-lite)' -f ~/.ssh/ms_s1_ed25519
```

`-N ''` (no passphrase) is deliberate: a passphrase makes every `ssh` call block on
a prompt, which defeats non-interactive use entirely. The private key is protected
by mode `600` inside the WSL filesystem.

Then `~/.ssh/config` (mode `600`):

```
Host ms-s1
    HostName 192.168.1.133
    User "jirachai thiemsert"
    IdentityFile ~/.ssh/ms_s1_ed25519
    IdentitiesOnly yes
    StrictHostKeyChecking accept-new
    ConnectTimeout 10
```

Verify the config parses **before** blaming the server:

```bash
ssh -G ms-s1 | grep -E '^(user|hostname|identityfile) '
```

## 4. Server side — MS-S1, PowerShell **as Administrator**

### 4.1 Install and start

```powershell
Get-WindowsCapability -Online -Name OpenSSH.Server*
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Set-Service -Name sshd -StartupType Automatic
Start-Service sshd
```

On this box the capability was already `State : Installed` — the service was simply
not running, and `StartupType` was not `Automatic`. A closed port 22 therefore does
**not** imply OpenSSH is absent.

`ssh-agent` staying `Stopped` is correct. It is the *client* agent, for MS-S1
connecting outward; it plays no part here.

### 4.2 Firewall — scope it, do not merely open it

```powershell
Get-NetFirewallRule -Name *OpenSSH* | Select-Object Name,DisplayName,Enabled,Direction,Profile
Get-NetFirewallRule -Name *OpenSSH*In* | Set-NetFirewallRule -Profile Private,Domain -Enabled True
Get-NetFirewallRule -Name *OpenSSH* | Select-Object DisplayName,Enabled,Profile
```

Must end as `Domain, Private` — matching ADR-002's Ollama rule. **A successful
connection from the LAN proves nothing about the `Public` profile**: check the rule
explicitly, or SSH may be listening the next time the machine joins an untrusted
network. (Here the pre-existing rule was `Private`-only, so it had never been
publicly exposed; the command above widens it to include `Domain`, which is inert
on a non-domain-joined machine and buys consistency with ADR-002.)

### 4.3 Default shell → PowerShell

```powershell
New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell -Value "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -PropertyType String -Force
```

The default is `cmd.exe`, which has no cmdlets and different quoting — painful to
drive from a remote agent. Restart `sshd` after changing this.

### 4.4 Install the public key

`C:\ProgramData\ssh\sshd_config` ships with:

```
Match Group administrators
       AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys
```

**So for an administrator account, `~/.ssh/authorized_keys` is never read.** Confirm
which case applies before writing anything:

```powershell
whoami
whoami /groups | Select-String "S-1-5-32-544"
```

Output from the second command ⇒ administrator ⇒ use the central file:

```powershell
Add-Content -Path C:\ProgramData\ssh\administrators_authorized_keys -Encoding ascii -Value '<paste the .pub line here>'
icacls C:\ProgramData\ssh\administrators_authorized_keys /inheritance:r /grant "*S-1-5-32-544:F" /grant "*S-1-5-18:F"
```

No output ⇒ ordinary user ⇒ `$env:USERPROFILE\.ssh\authorized_keys`, granting that
user plus `*S-1-5-18`.

Then `Restart-Service sshd`.

## 5. The four traps

### 5.1 `icacls` must use SIDs, not group names

`"Administrators:F"` fails on a non-English Windows because the group is localised.
`"*S-1-5-32-544:F"` (Administrators) and `"*S-1-5-18:F"` (SYSTEM) are locale-proof.

The result must be **exactly two entries**:

```
NT AUTHORITY\SYSTEM:(F)
BUILTIN\Administrators:(F)
```

Anything else — the user's own name, `Users`, `Authenticated Users` — means
inheritance was not cut, and **sshd will refuse the key silently**, with no error
returned to the client.

### 5.2 An account name containing a space breaks `user@host`

This account is `jirachai thiemsert`. Never hand-assemble `user@host`; put the
quoted form in `~/.ssh/config` (`User "jirachai thiemsert"`) and always invoke the
alias. OpenSSH ≥ 7 parses the quoted value — verified on OpenSSH 9.6p1, which
resolves it to `user jirachai thiemsert`.

### 5.3 The session gets a **full** administrator token

Unlike an interactive UAC-filtered logon, an OpenSSH session for an administrator
carries an unfiltered token. Proof used here: reading
`administrators_authorized_keys`, whose ACL is `Administrators:F` + `SYSTEM:F` only
— a filtered token has that SID marked deny-only and the read fails.

**Consequence:** service, Docker, scheduled-task and firewall changes all succeed
without further elevation. That is convenient and it is exactly why CLAUDE.md §8
matters more now, not less.

### 5.4 Port closed ≠ not installed

See §4.1. Probe order that avoids a wrong diagnosis: TCP 22 reachable → sshd
answering → authentication. A `Permission denied (publickey,password,
keyboard-interactive)` is a **success signal** for the first two; only the key is
outstanding.

## 6. Verification

```bash
ssh -o BatchMode=yes ms-s1 'echo REMOTE_OK; hostname; whoami'
```

`BatchMode=yes` is the point: it forbids any interactive fallback, so a success
proves publickey authentication rather than a silent password prompt.

Expected:

```
REMOTE_OK
CRAY-MS-S1-MAX
cray-ms-s1-max\jirachai thiemsert
```

## 7. Debugging

sshd does not tell the client why it refused. Read the server's own log:

```powershell
Get-WinEvent -LogName "OpenSSH/Operational" -MaxEvents 30 | Format-List TimeCreated,Message
```

| Symptom | Cause |
|---|---|
| `Authentication refused: bad ownership or modes` | §5.1 — re-run `icacls` |
| Connection times out | Firewall profile wrong, or the network is currently classified `Public` |
| Password prompt despite an installed key | Administrator account, key written to `~/.ssh/authorized_keys` instead of the central file (§4.4) |
| Key silently ignored | File has a BOM, or the key was wrapped across lines — `Get-Content` must show **one** line starting `ssh-ed25519` |

Password authentication is deliberately left enabled as a fallback diagnostic. Turn
it off only once key auth is proven, and treat that as a host-state change.

## 8. Revoking access

```powershell
Set-Content -Path C:\ProgramData\ssh\administrators_authorized_keys -Value '' -Encoding ascii
Stop-Service sshd
Set-Service -Name sshd -StartupType Disabled
Get-NetFirewallRule -Name *OpenSSH*In* | Set-NetFirewallRule -Enabled False
```

Client side: `rm ~/.ssh/ms_s1_ed25519*` and drop the `Host ms-s1` block.

## 9. Security posture

- **LAN only.** Profile `Domain, Private` means the rule does not apply on a network
  Windows classifies `Public`. This stays inside ADR-002's existing two-machine LAN
  trust model; it is **not** public exposure and needs no hosting ADR.
- ADR-002 §Consequences flags that the LAN trust model *"assumes the home/office
  network is reasonably secured … no untrusted devices"* and names a future ADR for
  re-evaluation. **Any inbound path from the public internet — a tunnel, a
  port-forward, a hosted site — falls under that future ADR, not this runbook.**
- The private key has no passphrase. Its protection is filesystem permissions plus
  the fact that it grants access only to a LAN host. Rotate via §8 + §3.

---

*Sources: ADR-002 (network topology), CLAUDE.md §8 (the binding host-state rule).
Companion skills: `ms-s1-admin` (operating), `ms-s1-ollama` (models/benchmarks).*
