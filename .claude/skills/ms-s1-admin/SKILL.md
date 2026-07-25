---
name: ms-s1-admin
description: Operate the MS-S1 MAX box itself over SSH from WSL — inspect or change Windows services, Docker Desktop, scheduled tasks, files, firewall, and event logs on CRAY-MS-S1-MAX. Encodes the mechanics that otherwise corrupt commands silently: invoke via the `ssh ms-s1` alias (never hand-build `user@host` — the account name contains a space), and pipe a `.ps1` file over stdin instead of inlining PowerShell (a `$` inside a `wsl bash -lc "ssh …"` string is eaten by TWO bash layers and vanishes with no error). Also records that the session carries a FULL elevated admin token. Use whenever running any command on MS-S1 that is not an Ollama HTTP call — checking whether Docker or Ollama is up, reading Windows event logs, inspecting or editing scheduled tasks, or diagnosing why the box is not serving. For warming/running a model or the procedure-baseline benchmark use `ms-s1-ollama` instead.
---

# MS-S1 MAX — operating the box over SSH

MS-S1 (`CRAY-MS-S1-MAX`, `192.168.1.133`) is reachable two ways: **Ollama HTTP on
11434** (models — see the `ms-s1-ollama` skill) and **SSH on 22** (the machine
itself — this skill). SSH access was set up and verified 2026-07-25; the setup and
recovery procedure is [`docs/runbooks/ms-s1-ssh-access.md`](../../../docs/runbooks/ms-s1-ssh-access.md).

## ⚠️ Host-state gate (binding rule lives elsewhere — do NOT rely on this skill to carry it)

Changing anything on MS-S1 — a service, Docker, a scheduled task, the firewall, a
file — is a **host-state change**. The binding rule is *ASK Cray before it*, and it
lives in **`CLAUDE.md` §8 Host-State Actions**, not here (a skill that fails to
trigger must never silently drop a binding rule — CLAUDE.md §4 bright line). This
skill is mechanics only, for once you have the go-ahead.

**The surface §8 covers got much wider when SSH landed.** It used to be
approximately "don't warm a model", because nothing else was reachable. It now
includes every service, container, task and file on the box. Read-only inspection
is fine unprompted; **anything that writes needs Cray's go.**

## Invoke via the alias — always

```bash
ssh ms-s1 '<command>'
```

Never hand-assemble `user@host`: the Windows account is **`jirachai thiemsert`,
which contains a space**. `~/.ssh/config` carries the quoted `User` form; the alias
is the only supported entry point. Verify the config resolves before blaming the
server:

```bash
ssh -G ms-s1 | grep -E '^(user|hostname|identityfile) '
```

Add `-o BatchMode=yes` when a result must *prove* key auth — it forbids any
interactive fallback, so a success cannot be a silent password prompt.

## ⚠️ The `$` trap — and the pattern that avoids it

The remote shell is **Windows PowerShell 5.1**, so real work needs `$`. But a
command reaches it through **two** bash layers (the harness's Git Bash, then
`wsl bash -lc`). Both expand `$` inside double quotes, and escaping only survives
one of them.

**Measured (2026-07-25):**

```bash
wsl bash -lc "ssh ms-s1 'Write-Output \"got:[$PSVersionTable]\"'"   # →  got:[]
```

Empty. **No error, no warning** — same silent-corruption class as the backtick
heredoc trap in the `git-workflow` skill. An escaped `\$(…)` fares no better: the
second layer command-substitutes it away, leaving stray syntax.

### ✅ Do this instead — write a `.ps1`, pipe it over stdin

Write the script with the **Write tool** (never a heredoc), then:

```bash
ssh -o BatchMode=yes ms-s1 'powershell -NoProfile -Command -' < /path/to/script.ps1
```

The script never passes through a shell parser, so `$var`, `$(…)`, `[Type]::Member`
and quotes all arrive intact. Verified end-to-end:

```
PSVersion=5.1.26100.8875
Docker=Stopped/Manual
Ollama=running pid 8772
Elevated=True
```

**Inline is acceptable only for commands containing no `$`, no backtick and no
`$(…)`** — e.g. `ssh ms-s1 'Get-Service sshd'`. The moment a `$` appears, switch to
the file+stdin form. Do not try to out-escape it.

## PowerShell 5.1 caveats on the remote side

Same edition as the harness's own PowerShell tool, so the same rules apply:

- **No `&&` / `||`** — parser error. Use `A; if ($?) { B }`.
- No ternary `?:`, no `??`, no `?.`.
- `ConvertFrom-Json` returns `PSCustomObject`; `-AsHashtable` does not exist.
- `Set-Content` / `Add-Content` default to system ANSI — pass `-Encoding` explicitly
  for anything another tool will read.
- Non-interactive: never `Read-Host`, `Get-Credential`, `Out-GridView`, or a
  confirmation-prompting destructive cmdlet without `-Confirm:$false`.

## The session is fully elevated

`Elevated=True` — an OpenSSH session for an administrator carries an **unfiltered**
token, unlike an interactive UAC-filtered logon. Service control, Docker, scheduled
tasks and firewall edits all succeed with no further elevation step.

Treat this as a hazard, not a convenience: there is no second prompt between a typo
and a stopped service. It is precisely why the §8 gate matters more now.

## Known box state (verify, don't trust this list)

- **Docker Desktop** — `com.docker.service`, `StartType Manual`, observed `Stopped`.
  It starts on *sign-in*, not boot. Any deployment story on this box has to deal
  with that.
- **Ollama** — running as a process, no autostart configured.
- Firewall: `OpenSSH-Server-In-TCP` scoped `Domain, Private`; the Ollama rule is
  scoped the same. Neither is exposed on `Public`.

## Reading the SSH server's own log

sshd never tells the client why it refused:

```bash
ssh ms-s1 'Get-WinEvent -LogName "OpenSSH/Operational" -MaxEvents 30 | Format-List TimeCreated,Message'
```

Fuller symptom→cause table in the runbook §7.

---

*Tier 2.6 skill (ADR-0017). Mechanics only — the host-state ASK-Cray gate is a
binding rule in `CLAUDE.md` §8, not here. Sources: ADR-002 (network topology),
`docs/runbooks/ms-s1-ssh-access.md` (setup + recovery). Companion: `ms-s1-ollama`
for models and benchmarks.*
