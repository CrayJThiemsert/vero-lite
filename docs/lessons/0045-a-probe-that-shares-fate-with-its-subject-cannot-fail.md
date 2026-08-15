# Lesson #0045 — a probe that shares fate with its subject cannot fail

**Session:** 233 (2026-08-16) · **Measured on:** MS-S1 MAX, Ollama upgrade
0.32.3 → 0.32.13 · **Status:** advisory (§1 precedence — promote to ADR if it
must bind)

## The claim

A liveness probe that runs **inside** the thing it is checking reports `200` for
a subject that is already doomed. It is not a weak check — it is a check that
**cannot** return failure, so its green carries no information at all.

Two probes in one incident had this shape. Both were honestly green. Both were
worthless.

## What happened

`winget upgrade Ollama.Ollama` on MS-S1 replaced the binary and killed the
running server. Restarting it over SSH produced this, in a single session:

```
Proc=ollama pid=3980
LocalProbe=200 {"version":"0.32.13"}
Listen=TCP    0.0.0.0:11434    LISTENING    3980
```

Every line is true. The server was listening on all interfaces. Minutes later
`Get-Process ollama` found **nothing**, and three separate operations had already
failed against the corpse:

| Attempt | Symptom | Real cause |
|---|---|---|
| `ollama serve` via `Start-Process` | vanished silently | job object |
| `ollama pull` via CLI | `Failed to start: Unable to init instance` — it tried to boot a **desktop UI** because it found no server | job object |
| `POST /api/pull` over HTTP | curl hung, log stayed 0 bytes | job object |

🔴 **Windows OpenSSH puts the session's descendants in a job object and
terminates it on disconnect.** `Start-Process` does not escape it. The process
lives exactly as long as the SSH session that measured it — which is why
`LocalProbe` could never have caught this.

## The second probe with the same defect

The HTTP pull was launched with `curl --max-time 0`. That means *no timeout*, so
a connection that never establishes produces **no error, no output, and no exit**
— indistinguishable from a healthy 30 GB download in progress. The log sat at
0 bytes and read as "still working".

⚠️ **`pgrep` said the client was alive, and that was true and useless.** A client
can be perfectly alive while transferring nothing.

The check that actually resolved it measured the **outcome**, on the far side,
where no shared fate exists:

```
Sample1_TotalGiB=156.17    Partial=NONE
Sample2_TotalGiB=156.17    DeltaMiB_over_12s=0
```

Zero growth, no `-partial` file. Nothing was downloading — and once the real
pull began, the same probe showed `Partial=…-partial GiB=27.052` and steady
delta.

## The practice

1. **Probe from outside the session that started the subject.** For MS-S1, the
   only trustworthy Ollama check is `curl` from the WSL box after the SSH
   session has closed — never `Invoke-WebRequest` to `127.0.0.1` inside it.
2. **Never `--max-time 0`.** Set `--connect-timeout` so a dead path fails fast
   instead of impersonating progress.
3. **Measure the artifact, not the client.** Bytes on disk, rows in the table,
   the file that should exist. Client liveness is not work being done — see
   [Lesson #0007](0007-harness-exit-code-artifact.md) for the same family.

## The workaround, and what it does not fix

`Win32_Process.Create` spawns a process owned by the WMI service, outside the
SSH job object:

```powershell
Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmdline }
```

Verified: `pid=27064 sessionId=0`, still serving after the SSH session closed,
reachable from WSL (`http=200`, connect 2.7 ms), GPU offload unaffected
(`size_vram/size = 1.0000` under ROCm).

⚠️ **It is a stopgap, not the fix.** The process dies on reboot, and MS-S1's only
autostart is `Ollama.lnk` in the Startup folder — which fires on **interactive
sign-in**, so a headless reboot leaves vero-lite with no LLM. A scheduled task
("run whether user is logged on or not") is the durable fix; it is a persistent
host config change and needs Cray's go per `CLAUDE.md` §8. **Not done.**

## Related

- [#0007](0007-harness-exit-code-artifact.md) — an exit code that reports the
  truncator, not the command; same "the signal shares fate with the noise" family
- [#0035](0035-negative-measurement-needs-a-positive-control.md) — the same
  session's other instance: a grid that found no bug, with no control proving it
  could detect one
- `.claude/skills/ms-s1-admin/SKILL.md` — records "Ollama — no autostart
  configured", which is **imprecise**: a Startup-folder shortcut exists but is
  interactive-sign-in only
