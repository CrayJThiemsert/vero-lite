# `oct-energy` migration phase 2 + PLAN-0103 Step 9 MS-S1 headroom — RESULT: PASS (all pre-committed criteria met; ~17 min downtime, 12 of it an instrument failure)

**Date:** 2026-08-10 (session 221)
**Event type:** host-state change on MS-S1 (`CRAY-MS-S1-MAX`) — the live published demo was stopped, its prompt-log volume migrated, and the stack restarted under the new compose project. Plus a read-only capacity measurement. **Evidence, not a gate** (CLAUDE.md §8): the offline suite remains the binding bar and was green before any host command ran.
**Cray-gated go:** typed in chat, session 221 — one go covering *both* phase 2 and the Step 9 measurement.
**Scope:** closes the migration PLAN-0103 Step 4b left owed (energy's live system still ran as compose project `vero-published` while the repo had renamed it to `oct-energy`), and discharges **AC-10's first clause** (headroom measured *before* a second system is brought up). Phase 1 — pull the host checkout forward 78 commits, build and ship the image, stage `.env`, take a rollback set — was completed in session 220 and is not repeated here.

---

## Part 1 — PLAN-0103 Step 9: MS-S1 headroom (the AC-10 measurement of record)

**Method.** Read-only over SSH: `docker stats --no-stream` for per-container footprint; `Get-CimInstance Win32_ComputerSystem` + `Win32_OperatingSystem` for host capacity; `Get-Process | Sort-Object WorkingSet64` for co-tenant load. Measured while the published stack was running, before the migration touched anything.

### Measured — the published stack

| container | memory | CPU | PIDs |
|---|---|---|---|
| app (`uvicorn`) | **295.4 MiB** | 0.46 % | 7 |
| `cloudflared` | **19.0 MiB** | 0.50 % | 16 |
| **one published system, total** | **≈ 314 MiB** | ≈ 1 % | |

### Measured — host capacity

| | |
|---|---|
| Docker Desktop Linux VM | **31.16 GiB**, 32 CPUs |
| host physical memory visible to Windows | **63.65 GiB** (`TotalPhysicalMemory` 68,340,748,288 B) |
| host physical memory free | **31.93 GiB** |
| largest co-tenant | **`llama-server` — 12.2 GiB** working set |
| next co-tenants | `vmmemWSL` 1.85 GiB · Docker backend 0.45 GiB |

⚠️ **The hardware is 128 GB unified, but only ~63.65 GiB is visible to Windows** — the memory is deliberately split roughly in half with the GPU (Cray, confirmed session 221; the split is an experiment to find the performance balance and is tunable). `CLAUDE.md` §5 / ADR-002 record the hardware figure, which is true of the machine and **false of what any process can allocate**. A projection that starts from 128 GB overstates available RAM by ~2×.

### Projection — +2 app containers and +1 Postgres (ADR-0036 D6.3)

| addition | basis | estimate |
|---|---|---|
| +2 app containers | measured 295.4 MiB each | ≈ 590 MiB |
| +2 `cloudflared` connectors | measured 19.0 MiB each — **each system carries its own connector**, so this scales with N and is easy to omit | ≈ 38 MiB |
| +1 `postgres:16-alpine` (fleet, ADR-0037) | ⚠️ **NOT MEASURED** — both co-tenant Postgres containers on this host are `Exited`, so no idle footprint was observable without starting someone else's stack. Bounded from typical idle usage. | 30–50 MiB |
| **total additional** | | **≈ 0.65 GiB** |
| **three published systems, total** | | **≈ 0.95 GiB of 31.16 GiB ≈ 3 %** |

**Verdict: RAM and CPU do not constrain a second or third published system.** The projected three-system footprint is ~3 % of the Docker VM's allocation, against 31.93 GiB free on the host.

🔴 **What this measurement does NOT settle, stated so it is not read as broader than it is.** The binding constraint on a second *assisted* system is not container footprint — it is the resident LLM (`llama-server`, 12.2 GiB) and the number of concurrent in-flight model calls. That is **ADR-0036 OQ-2**, and it remains **open**: this measurement clears the bring-up on capacity grounds only. One unmeasured term (Postgres idle) is declared above rather than folded silently into the total.

---

## Part 2 — the migration (phase 2, steps 6–10)

### Pre-committed pass/fail read (fixed BEFORE the run — CLAUDE.md §8 / Lesson #0026; `.claude/state/goal.json` session 221, C1 + J1–J7)

| id | criterion |
|---|---|
| C1 | `tests/deploy` + `tests/docker` green **before** any host command |
| J1 | project `vero-published` gone; `oct-energy` running(2), app healthy |
| J2 | new volume's payload byte-identical to the old — file count **and** per-file checksums compared on **both** sides |
| J3 | the running app can **write** to the prompt log as its own non-root user — an actual write, seen to succeed |
| J4 | keyless `/whoami` = 401 · internal `/health` = 200 · tunnel registered · public `/health` = 302 at the edge |
| J5 | the temporary bridge directory deleted; host checkout clean |
| J6 | the old volume removed **only after** J1–J4 pass, with an off-host backup still in hand at that moment |

### Result

| criterion | expected | observed | verdict |
|---|---|---|---|
| C1 offline gate | 0 failed | 193 passed, exit 0 | ✅ |
| J1 project state | `oct-energy` running(2), healthy | `running(2)`, `healthy`; `vero-published` absent from `compose ls`, `docker ps -a`, and networks | ✅ |
| J2 payload parity | 2 files, 3205 + 391 B, checksums equal | equal on both sides (`50e7fabc…` / `d5dac45f…`), owner `999:999`, mode 644, mtimes preserved | ✅ |
| J3 writability | write succeeds as uid 999 | `touch` exit 0 **and the artifact observed in the directory listing** owned `999:999`; then removed | ✅ |
| J4 liveness | 401 / 200 / registered / 302 | 401 · 200 · 4 tunnel connections registered · **302** at the edge with `www-authenticate: Cloudflare-Access` and `cache-control: no-store` | ✅ |
| J5 bridge + checkout | deleted, clean | `Test-Path` False; `git status --porcelain` empty | ✅ |
| J6 old volume | removed last | removed after J1–J4; payload re-verified through the running container **after** removal | ✅ |

**VERDICT: PASS.** The published energy demo now runs as compose project `oct-energy` on network `oct-energy_vero_oct` (derived, per Step 4b's dropped fixed network `name:`), serving image `f2c3717b…` — the same id as `oct-energy-app:latest`, so the deploy took effect rather than silently reusing the old container. `UI_PUBLISHED_VIEWS=A,B,C,D,F`, `OCT_VERTICAL=energy`, `API_AUTH_ENABLED=true`, and `API_KEYS` arrived non-empty.

### Two things the run could NOT prove, recorded rather than glossed

- **Keyed `/whoami` = 200** — the positive control the README calls "the only evidence the demo is loginable at all" — needs the raw operator key, which is Cray's secret. Keyless-401 alone does not distinguish "auth armed with a working key" from "no key mapping at all"; the `API_KEYS` env var was separately confirmed to reach the container non-empty, which narrows but does not close it.
- The public hostname is **not named in this file**. ADR-0035 D1(3) keeps the domain in the portal repo and DNS only; the 302 was verified against it out of band.

---

## Instrument failure — ~12 of the ~17 minutes of downtime

**Downtime: ≈ 17 min** (project stopped ≈ 18:34:31 +07, tunnel re-registered 18:51:50 +07), against a planned 2–5 min. **The migration work itself was not slow; the diagnosis was.**

The run was executed as one `.ps1` piped to `ssh <host> 'powershell -NoProfile -Command -'` — the form mandated for anything containing `$` or backslash paths. Two properties of that form combined into a 20-minute black box:

1. **`docker network ls` wedged.** A display-only line — it changes nothing — hung indefinitely. The daemon was healthy throughout: a second SSH session ran the same command successfully while the first was stuck.
2. **Output is block-buffered to the redirected file**, so the log stayed at **0 bytes** for the whole run. Zero bytes was not evidence that nothing had happened: two containers and a network had already been removed.

Diagnosis came from probing the host — `Get-CimInstance Win32_Process` returns `CreationDate` + `CommandLine`, which identified the wedged command exactly. Killing it did **not** resume the script: the child had inherited and consumed the remainder of the script from stdin, so PowerShell sat waiting for input that could never arrive. The run was abandoned and **the remaining steps were completed as individual `ssh` commands, each verified before the next** — which is what finished the migration.

**Carried forward:**

- For a multi-step **destructive** host sequence, prefer individual commands over one long `-Command -` script. If a long script is unavoidable, have it `Tee-Object` progress to a file **on the host** so a second session can watch it.
- Put `$LASTEXITCODE` guards after **state-changing** commands only. This script had none after `docker network ls`; a guard there would have aborted the run while the demo was down.
- `docker compose -p <name> down` **works from container labels alone** — verified here against a project whose recorded config file had been moved out from under it by Step 4a.

---

## Significance / next

- **The compliance defect the migration existed to prevent is closed.** The erasure paths in `published-demo-operations.md` address `-p oct-energy`; before this run they would have reported success while touching nothing, because the rows lived in the orphaned `vero-published-prompt-log` volume. That volume is a 90-day-retention artifact, so a silent no-op there was a controller-promise failure, not a cosmetic one.
- The off-host backup tar taken during phase 1 held prompt-log rows — personal data outside the retention system — and was **deleted** once the edge check passed, so no uncontrolled copy survives.
- `vero-published-app:latest` and `:prev` remain on the host **deliberately**, as the rollback window for the pre-migration app (redeploy runbook §8: do not prune between a deploy and its rollback window).
- **PLAN-0103 Step 10 is now unblocked on capacity grounds.** Procurement's bring-up is first (SD-2); fleet's remains gated on AC-11's RoPA. Step 8b (the portal-side assembly request) is still owed and is a Step 10 input.

## Reference

- Procedure: `deploy/published/oct-energy/README.md` §"Migration — if this system is already running as `vero-published`"; stop condition `docs/runbooks/published-demo-redeploy.md` §0b (which this run clears — it now returns empty).
- PLAN: `docs/plans/0103-portal-landing-and-per-system-published-profiles.md` — Step 9, Step 10, AC-10.
- ADRs: ADR-0036 D6.3 (headroom before multiplying) + OQ-2 (aggregate LLM posture, still open); ADR-0035 D1(3) (the domain is not this repo's property), D6 (prompt-log retention).
- Pre-committed read: `.claude/state/goal.json` (session 221, C1 + J1–J7).
- Operator-grade detail: `.claude/handoffs/session-221/` (gitignored).

AI-assisted (Claude Code, session 221); no `Co-Authored-By` per CLAUDE.md §7.
