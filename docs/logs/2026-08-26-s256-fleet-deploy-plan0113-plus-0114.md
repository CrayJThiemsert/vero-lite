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

⚠️ **Not claimed:** an end-to-end request through the Cloudflare edge. The ingress row
is verified *present on the mounted file* and the connector was recreated to read it,
but no public request was made — that needs the published hostname, which is
deliberately absent from this repo (ADR-0036 D2). **PLAN-0113 AC-9's visitor walk and
PLAN-0114 AC-5's live half therefore remain OPEN**, now blocked only on that walk
rather than on the deploy.

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
