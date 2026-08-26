# s256 — deploying PLAN-0113 + PLAN-0114 to the live fleet system

**Session:** 256 · **Date:** 2026-08-26 · **System:** `oct-fleet-maintenance` ·
**Author:** Claude Code (Tier 2)

> **The go, recorded BEFORE any command reached the host** (`CLAUDE.md` §8;
> `deploy/published/oct-fleet-maintenance/DEPLOY.md` §0). Cray, typed, 2026-08-26:
> **"รอจนเมื่อพร้อมแล้ว, deploy 0113+0114 ขึ้น live เลย เราอนุมัติ 'go'"** — one go for
> this occasion, covering its phases.
>
> 🔴 **The shared `deploy/published/deploy.py` was NOT used and must not be.** It
> targets `oct-energy` by hardwired constants with no `--system` selector; running it
> here would ship the wrong profile and recreate a container on a system nobody meant
> to touch. This system deploys by its own `DEPLOY.md` sequence.

## §2 Pre-flight — read-only baseline (the do-no-harm record)

| Read | Result |
|---|---|
| `hostname` | `CRAY-MS-S1-MAX` |
| fleet **app** | `15359d2a70be`, image `sha256:0fc679cf0e50…`, **Up 2 days (healthy)** |
| fleet **postgres** | `3e1daa1bebd1`, Up 2 days (healthy) |
| fleet **cloudflared** | `986aedd955fb`, Up 2 days |
| `docker compose ls` | `oct-fleet-maintenance` **running(3)** present ✅; **no `vero-published`** ✅ (the shared runbook's §0b stop condition is clear) |
| host checkout | `ee41b55` |
| demo state (plan mode) | **`DEMO-STATE: PRISTINE`** → no reset; skip straight to §3 |

**Rollback point: `sha256:0fc679cf0e50…`.**

**Pull decision, established rather than assumed.** Diffing `ee41b55..main` over
**only the two files the host actually reads**:

```
deploy/published/oct-fleet-maintenance/cloudflared/config.yml
```

⇒ a host `git pull` **is** required, and because the changed file is
`cloudflared/config.yml`, **`--force-recreate cloudflared` is required too**. That
file carries PLAN-0114's new ingress row `^/runs/[^/]+/continue$` — the row without
which the acknowledge button 404s at the edge.

## §2a Pre-ship — 🔴 this step caught a defect that would have taken the demo down

Built locally from `main` = `dd4228f` (verified: build context byte-identical to
`origin/main`). Then hashed the **13 files this deploy changes** inside the freshly
built image against the working tree.

**First run: 12 of 13.**

```
sha256sum: /app/services/engine/procedures/persistence.py: Permission denied
```

Chased to the direct oracle rather than stopping at the hash:

```
PermissionError: [Errno 13] Permission denied:
  '/app/services/engine/procedures/persistence.py'
```

**The image could not import its own engine.** Shipping it would have left the live
fleet demo unable to boot.

### Root cause — the probe-battery driver does not restore file MODE

Three files in the build context were `-rw-------` (0600):
`persistence.py`, `action_step.py`, `orchestrator.py`. Those are **exactly** the three
files this session's probe batteries mutated and restored. The driver restores
**content** byte-identically — which is all it verifies, and it verified true — but
writes the file back **0600**. The container runs as `uid=999(vero)`, so a 0600
`root`-owned module is unreadable to it.

**Why nothing else saw it:**

| Surface | Why it was blind |
|---|---|
| `git status` | `core.fileMode = false` in this repo — a mode change is invisible |
| the full test suite | tests read the files as their **owner**; 0600 is readable to `crayj` |
| CI | builds from a **fresh clone**, where git's recorded `100644` applies |
| `docker build` | copies the mode faithfully; nothing errors |

Git records `100644`, so **the fault is local to a post-battery working tree** — and
a local build is exactly what this procedure does.

**Fixed:** `chmod 644` on the three files (no git diff — the mode was never the
committed one), stale root-owned `.pyc` removed, rebuilt.

**Second run: `HASH-VERDICT: IDENTICAL across all 13 files`**, and the direct oracle
now answers `IMPORT-OK` with `continue_no_decision_run` and `continue_run_endpoint`
both present in the image.

⚠️ **This belongs back on `tools/probe_battery/`** as a defect: its restore is
content-complete and mode-incomplete, and its own byte-identical check cannot see
the gap. Recorded here; surfaced to Cray separately.

## §3 The sequence — all steps passed their pre-fixed read

| # | Step | Result |
|---|---|---|
| A | host `git pull --ff-only` | `ee41b55..dd4228f`, fast-forward, host checkout **clean** after |
| A2 | the new ingress row reached the **bind-mounted** file | `L166: - path: ^/runs/[^/]+/continue$`, sitting between `/cancel` and `/audit/verify` — read off the host's own `config.yml`, the file compose mounts |
| 1 | tag `:prev` | `sha256:0fc679cf0e50…` — **exactly the §2 baseline**. Rollback point secured |
| 2 | `docker save │ ssh … docker load` | `Loaded image: oct-fleet-maintenance-app:latest` |
| 3 | id equality across machines | **`sha256:880307365d7f…` on BOTH** — the transfer guarantee |
| 4 | `config --quiet` | **0 bytes** — both required host secrets interpolate |
| 5 | `up -d` | **only `app` Recreated**; `postgres` and `cloudflared` stayed `Running`; app → Healthy |
| 5b | `up -d --force-recreate cloudflared` | connector Recreated + Started — required because `config.yml` was in the diff, otherwise it keeps serving the OLD ingress map |

## §4 Verify — against the §2 baseline

| Read | Result |
|---|---|
| app container `.Image` | `sha256:880307365d7f…` — **equals the loaded id**, so the deploy *took effect*, which shipping alone does not prove |
| new container id | `e6984c248b51` (was `15359d2a70be`) · `running` · **healthy** |
| boot log | `run 'run-fleet-operate-demo' already present — skip` · `fleet live cases loaded: 4 case(s) with an accepted quote reach the gate` — **the seeded rows survived; the visitor's beat is untouched** |
| demo state, plan mode | **`DEMO-STATE: PRISTINE`** — same as the baseline |

**What is now live:** PLAN-0113 Steps 1–3 (trigger-scoped reads) **and** PLAN-0114
Steps 1–3 (the acknowledge-and-continue seam + its UI + its edge row), together, as
the one unit they had to ship as.

### The route-registration chain, stated so it is not overclaimed

The live app was **not** interrogated directly — a multi-line `python -c` through
`docker compose exec` is parsed by the host's **PowerShell**, not by a shell, and the
payload is destroyed (the `{…}` / quote-stripping family in the `ms-s1-admin` skill).
The claim rests on a chain instead, each link measured:

1. §2a hashed `services/api/routers/runs.py` **inside the image** — identical to the
   working tree, which contains `continue_run_endpoint`;
2. that same image answered `IMPORT-OK` with `continue_run_endpoint: True`;
3. §4 shows the running container's `.Image` is **that image id**.

*(The paragraph that stood here said no public request had been made. Cray supplied
the hostname and did the Cloudflare Access PIN; the walk below then ran. Kept as a
correction rather than a silent edit: the claim was true when written.)*

## §5 The visitor walk — PLAN-0113 AC-9 and PLAN-0114 AC-5 CLOSED

Driven through `https://oct-fleet-maintenance.cray-n8n.com` in a real browser, behind
Cloudflare Access. Cray performed the Access PIN; every step below is the visitor's
own path. All case text is synthetic and labelled `s256 live walk`, per the intake
surface's own notice.

**Before anything else — the new UI actually reached the browser.** The live page
serves `assets/api.js?v=c49` and `assets/view-monitor.js?v=c42`: the per-file
cache-bust counters this PLAN bumped. Not the container's copy — the browser's.

| # | Step | Measured |
|---|---|---|
| 1 | open a case, quote **฿12,000** (mid-band), accept — as **ต้อม** | `case-8a25399bd734`, accepted `201` |
| 2 | 🎯 **AC-9** — the fired run's gate | `@41bb7835…`, **exactly ONE proposal**, and it is `action-event-case-case-8a25399bd734` — **the visitor's own case**. The pre-scoping seeded run `run-fleet-operate-demo` still shows **3**, the fleet-wide shape, which is the contrast that makes the one meaningful |
| 3 | open a case, quote **฿4,500** (sub-ceiling), accept | `case-596c0244e638`; run `@d8f5a677…` parks at `approve` with **0 proposals** — the empty gate, reachable on the live system |
| 4 | switch to **วิรัช**, open the empty-gate run | panel reads *"No decidable proposals at this gate"* + **"Acknowledge — nothing to approve"**; **no Submit** |
| 5 | 🎯 **AC-5 positive control, same surface** | the mid-band run renders **Submit** and the DOA advisory (฿12,000 → `ผจก.เดินรถ`) and **no Acknowledge**. The affordance appears **exactly** when the gate is empty |
| 6 | 🎯 **AC-5 / SD-4(B)** — click Acknowledge **once** | `WAITING_HUMAN` → **`COMPLETED`**, panel: *"Acknowledged — nothing to approve. Run completed. **(2 empty gates)**"* |
| 7 | the artifact the ruling values | both `approve` **and** `fulfill` carry `no_decision_continuation`, `acknowledged_by: appr-fleet-manager-wirat`, `proposal_count: 0`; all six steps `complete` |
| 8 | `GET /audit/verify` | **`intact: true`**, 64 rows, **0 breaks** — the new action rides the tamper-evident chain |
| 9 | demo state after | **`DEMO-STATE: PRISTINE`** — unchanged by the walk |
| 10 | app after | `running`, **healthy**, still on `sha256:880307365d7f…` |

🔴 **The arity measured offline held on the live system.** "(2 empty gates)" is the
UI reporting that one click walked `approve` **and** `fulfill` — the correction that
invalidated AC-1's original premise and produced SD-4, confirmed end to end against
real data on the published surface.

⇒ **PLAN-0113 AC-9 CLOSED** · **PLAN-0114 AC-5's live half CLOSED.**

⚠️ **Left behind on purpose:** the walk created two real cases and left the mid-band
run `@41bb7835…` parked at its gate — a genuine single-proposal gate a visitor can
now resolve, which is the demo's own beat. `DEMO-RESET.md` exists if Cray wants them
gone; **not run** — that is a demo-content decision, not a deploy step.

## Rollback

One command, and the point is already tagged:

```bash
ssh ms-s1 docker tag oct-fleet-maintenance-app:prev oct-fleet-maintenance-app:latest
ssh ms-s1 docker compose -f C:/projects/vero-lite/deploy/published/oct-fleet-maintenance/docker-compose.yml -p oct-fleet-maintenance up -d
```

`:prev` = `sha256:0fc679cf0e50…`, built 2026-08-22. ⚠️ The host checkout is now at
`dd4228f`; rolling the image back does **not** roll back `cloudflared/config.yml`. The
extra ingress row is harmless with an old image — the route simply 404s from the app
instead of the edge — but a full revert would also need
`git -C C:/projects/vero-lite checkout ee41b55 -- deploy/published/oct-fleet-maintenance/cloudflared/`
and a connector recreate.

---

*Host state changed under Cray's typed go, recorded above before the first command.
Ollama received no contact. AI-assisted (Claude Code).*
