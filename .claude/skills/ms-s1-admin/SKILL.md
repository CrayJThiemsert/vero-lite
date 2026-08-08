---
name: ms-s1-admin
description: Operate the MS-S1 MAX box itself over SSH from WSL — inspect or change Windows services, Docker Desktop, scheduled tasks, files, firewall, and event logs on CRAY-MS-S1-MAX. Encodes the mechanics that otherwise corrupt commands silently: invoke via the `ssh ms-s1` alias (never hand-build `user@host` — the account name contains a space), pipe a `.ps1` file over stdin instead of inlining PowerShell (a `$` inside a `wsl bash -lc "ssh …"` string is eaten by TWO bash layers and vanishes with no error), and NEVER send braces to the host — the remote shell is PowerShell even for a plain `ssh ms-s1 <program>`, so the universal `docker … --format={{.Id}}` form returns `unknown shorthand flag: 'e' in -encodedCommand`; ask for plain JSON and parse it locally. Also records that the session carries a FULL elevated admin token. Use whenever running any command on MS-S1 that is not an Ollama HTTP call — checking whether Docker or Ollama is up, reading Windows event logs, inspecting or editing scheduled tasks, or diagnosing why the box is not serving. For warming/running a model or the procedure-baseline benchmark use `ms-s1-ollama` instead.
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

## 🔴 The `{…}` trap — braces reach PowerShell as a SCRIPT BLOCK

**Different mechanism from the `$` trap below, and it bites the most ordinary
command there is.** `$` is eaten on *our* side by two bash layers. Braces survive
the trip intact and are then parsed by the **remote** shell — which is PowerShell,
not cmd, even for a plain `ssh ms-s1 <program> <args>` with no PowerShell invoked
anywhere in the command.

**Measured 2026-08-08 (session 214):**

```bash
ssh ms-s1 docker version --format={{.Server.Version}}
#  →  unknown shorthand flag: 'e' in -encodedCommand      (exit 1)
```

Five of eight probes failed identically. `--format={{…}}` is the form **every**
docker doc, every runbook and every Stack Overflow answer uses, so it arrives in a
command by reflex. Confirmation the shell is PowerShell rather than cmd:

```bash
ssh ms-s1 'echo %COMSPEC%'      # → the literal string %COMSPEC%, unexpanded
```

**The fix: ask for JSON and parse it on this side, where no shell is involved.**

```bash
ssh ms-s1 docker image inspect vero-published-app:latest    # full JSON, exit 0
ssh ms-s1 docker inspect vero-published-app                 # ditto
```

Then read `.Id` / `.Image` / `.State.Health.Status` locally. `deploy/published/deploy.py`
does exactly this and `tests/deploy/test_deploy.py` guards it — but that guard walks
only **that script's** argv, so it cannot protect a command you type here.

**The general rule for a bare `ssh ms-s1 …`:** literals only — **no braces, no
quotes, no `$`, no `;` `|` `&` `<` `>`**. Anything richer goes in a `.ps1` piped over
stdin (next section). And `git -C <path>`, never `cd <path> && git`: the `&&` is
handed to that same remote shell.

Full write-up of how this was missed for a whole PR — including a guard written for
this exact failure mode that went green over it —
[`docs/lessons/0039-a-self-authored-guard-inherits-the-authors-blind-spot.md`](../../../docs/lessons/0039-a-self-authored-guard-inherits-the-authors-blind-spot.md).

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
and quotes all arrive intact **in the script itself** — ⚠️ but see the next section:
that guarantee stops at the boundary where PowerShell hands an argument to a
**native executable**, which is where `docker run … python -c $code` lives. Verified
end-to-end:

```
PSVersion=5.1.26100.8875
Docker=Stopped/Manual
Ollama=running pid 8772
Elevated=True
```

**Inline is acceptable only for commands containing no `$`, no backtick and no
`$(…)`** — e.g. `ssh ms-s1 'Get-Service sshd'`. The moment a `$` appears, switch to
the file+stdin form. Do not try to out-escape it.

## 🔴 The stripped-`"` trap — PowerShell eats double quotes on the way to a native exe

**The `.ps1`-over-stdin form does NOT save you here, which is why this needs its own
section.** The section above is about getting a script to PowerShell intact. This one
is about what PowerShell does *next*, when it passes one of those strings on as an
argument to a **native executable** (`docker`, `git`, `python`): it **strips embedded
double quotes**. The `.ps1` was parsed perfectly; the exe still receives mangled argv.

**Measured 2026-08-08 (session 216)**, running a throwaway TCP server in a container:

```powershell
$py = 'import socket;srv=socket.socket();srv.bind(("0.0.0.0",11434));srv.listen(128)'
docker run -d --name p4-stall --entrypoint python vero-published-app:latest -c $py
```

```
docker logs p4-stall
#  →  srv.bind((0.0.0.0,11434))
#         ^^^^^   SyntaxError: invalid syntax. Perhaps you forgot a comma?
```

The `"` around `0.0.0.0` are simply gone. **The failure is silent one level up**:
`docker run` prints a container ID and exits 0, and `docker ps` then shows nothing
because the container already died. Only `docker logs` reveals it. A run that trusts
the exit code will happily proceed against a container that never started.

### ✅ Two forms that work

**1. Write the payload quote-free.** Often easy once you look for it — `str()` is the
empty host (`INADDR_ANY`), and any other string can come from `sys.argv`:

```powershell
$py = 'import socket,time;srv=socket.socket();srv.bind((str(),11434));srv.listen(128);time.sleep(86400)'
docker run -d --name p4-stall --entrypoint python <image> -c $py     # works
docker exec <container> python -c $probe p4-stall                    # argv[1] = the hostname
```

⚠️ Keep the payload **space-free** too when it rides a bare `ssh ms-s1 …`: `ssh` joins
its argv with spaces before the remote shell re-parses the result.

**2. Write the payload to a file on the host** (`Set-Content -Encoding utf8`, see the
caveats below) and pass the *path*, not the code. Verbose, but immune.

### The rule of thumb

This is the **third** member of one family, and they are worth reading together
because each has a different mechanism and each is silent:

| # | What is lost | Where it is lost |
|---|---|---|
| `{…}` | braces become a script block | the **remote** shell parses them (§ above) |
| `$` | variables vanish | **our** two bash layers expand them first (§ above) |
| `"` | quotes are stripped | PowerShell → **native exe** argv (this section) |

**Diagnostic, not preventive, but it catches all three:** never let a remote command's
exit code stand as the evidence. Read the *result* back — `docker logs` for a
container that should be running, `printenv` off the container for an env override —
and refuse to let a measurement count until it matches. See
[`docs/lessons/0007-harness-exit-code-artifact.md`](../../../docs/lessons/0007-harness-exit-code-artifact.md).

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
