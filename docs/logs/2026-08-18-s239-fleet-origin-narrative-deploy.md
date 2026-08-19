# Session 239 — the Tab F origin-narrative panel deployed to MS-S1

**Date:** 2026-08-18 (session 239)
**Event type:** host-state change on MS-S1, under two explicit typed §8 gos
**Operator-grade detail:** this file. No gitignored companion — everything below is safe to commit.

## The gos

Cray typed them **separately, per phase**, which is the shape §8 asks for:

1. *"เริ่มเฟส A เลย"* — the read-only pre-flight.
2. *"go เฟส B"* — the ship and the `up -d`, after phase A's results were read.

The plan those phases execute was staged and reviewed **before** either go, with every
pass/fail read fixed in advance. `--execute` never appears in it — phase A measured the
demo `PRISTINE`, so the reset branch was cut before any command ran.

## 🔴 The finding that changed the plan: the shared deploy script cannot deploy this system

`docs/runbooks/published-demo-redeploy.md` §3 presents
`python3 deploy/published/deploy.py --host <alias>` as *the* deploy procedure. Run in its
default **plan** mode — which touches nothing, verified in the code (`Runner.run` returns
before `subprocess.run` when not executing, and that split lives in one class so a new
call site cannot execute during a plan) — it printed:

```
docker compose -f .../deploy/published/oct-energy/docker-compose.yml build app
ssh ms-s1 docker tag oct-energy-app:latest oct-energy-app:prev
ssh ms-s1 docker compose -f ...\oct-energy\docker-compose.yml -p oct-energy up -d
```

Every literal is **`oct-energy`**. The constants are hardwired (`_PROJECT`, `_IMAGE`,
`_HOST_COMPOSE`, `_CONNECTOR_CONFIG`) and argparse carries no system selector. Adding
`--execute` would have built and shipped the **energy** image and brought up the energy
project, doing nothing for fleet and touching a system nobody meant to touch.

**It is deliberate, and it was already written down** — `deploy.py:65-83` records Cray's
typed s219 decision to defer `--system`, `tests/deploy/test_deploy.py:44-47` pins it, and
`deploy/published/oct-fleet-maintenance/DEMO-RESET.md` §3.1 states plainly that this
system is deployed by the manual sequence instead.

**The gap is one of routing, not of knowledge.** §3 of the shared runbook hands you the
script with no caveat; the caveat lives in §4b's pointer and in the profile's own file. A
reader who follows §3 in order meets `--execute` before meeting the warning. Correction
owed to the runbook — see the end of this file.

## Pre-flight baseline — captured before any host-state action

| Container | State | Container id |
|---|---|---|
| `oct-fleet-maintenance-app` | `Up 4 hours (healthy)` | `e4b064983b36` |
| `oct-fleet-maintenance-cloudflared` | `Up 2 days` | `535f6d17a159` |
| `oct-fleet-maintenance-postgres` | `Up 2 days (healthy)` | `3e1daa1bebd1` |
| `oct-energy-app` / `-cloudflared` | `Up 8 days (healthy)` / `Up 6 days` | `6e66a8546884` / `3f3ce9c5d6a2` |
| `oct-procurement-app` / `-cloudflared` | `Up 7 days (healthy)` / `Up 6 days` | `316a9b28143a` / `87713924a147` |

- **Stop condition (runbook §0b) clear:** no `vero-published` project. The read is
  non-vacuous — `oct-fleet-maintenance` was present in the same output.
- **Live image before:** `sha256:f35eeac23cc6f601…040cab7b`, which is **exactly what the
  session-238 record says was deployed**. The host had not drifted.
- **Demo state before:** `DEMO-STATE: PRISTINE` — the beat had not been played since s238,
  so no reset was required and none was performed.

## What this deploy did NOT need, established rather than assumed

- **No host `git pull`.** The only file under `deploy/published/oct-fleet-maintenance/`
  changed since the last deploy is `DEMO-RESET.md`, which neither compose nor cloudflared
  reads. Measured with `git diff --name-only 20669ae..HEAD -- deploy/published/oct-fleet-maintenance/`.
- **No `--force-recreate cloudflared`.** `cloudflared/config.yml` is unchanged, so the
  ingress allowlist is byte-identical to the one already validated.
- **No reset, no deletion.** Phase A's `PRISTINE` removed the branch.

## Evidence, step by step — every pass/fail read fixed BEFORE the run

| # | Action | Pre-committed pass | Result |
|---|---|---|---|
| B0 | tag the live image `:prev` | `:prev` resolves to the OLD id | `f35eeac2…040cab7b` — rollback point established |
| B1 | `docker save` → `ssh … docker load` over stdin | a `Loaded image` line | `Loaded image: oct-fleet-maintenance-app:latest` |
| B2 | `docker image inspect` on the host | **id IDENTICAL to the dev box** | `e4afeb8f…101b8ee0` on both |
| B3 | `compose config --quiet` | **zero bytes** of output | 0 |
| B4 | `compose up -d` | **only `app` Recreated** | `postgres Running`, `cloudflared Running`, `app Recreated → Healthy` |
| C1 | `sha256sum` the narrative **inside the running container** | `47e3fd20…5a7e05` | matched |
| C2 | `ls -la` the narratives directory | 6325 bytes | 6325 |
| C3 | `docker inspect` the app container | `.Image` == the loaded id | `e4afeb8f…101b8ee0`, new container `9984c71e47f6` |
| C3b | boot log | the seed **skips** (rows survive) | `run 'run-fleet-operate-demo' already present — skip` |
| C4 | demo state after | still `PRISTINE` | `PRISTINE` |
| C5 | do-no-harm vs the baseline | siblings and this system's other two containers untouched | see below |

**B2's id equality is the guarantee.** "A rebuild produced the same id" would not be —
buildkit's provenance attestation makes an id identify a *build* rather than its content.
Ids are comparable across machines, never across rebuilds.

**B3 must always carry `--quiet`.** Without it the command prints the interpolated config,
including `DATABASE_URL` with the password and the full `API_KEYS`.

### Do-no-harm, verified rather than assumed

`oct-fleet-maintenance-cloudflared` kept container id `535f6d17a159` and its `Up 2 days`;
`oct-fleet-maintenance-postgres` kept `3e1daa1bebd1` and its `Up 2 days`. **The tunnel
never re-registered and `pgdata` was never at risk.** Both sibling systems' four
containers were untouched at `Up 8 days` / `Up 7 days` / `Up 6 days`. Only
`oct-fleet-maintenance-app` changed, `e4b064983b36` → `9984c71e47f6`.

### The demo survived the deploy, and that was the design

The run rows live in Postgres, which was not recreated, so the boot seed found them and
skipped — leaving the visitor's beat exactly where it was. `DEMO-STATE` read `PRISTINE`
before and after. This deploy neither restored nor consumed anything.

## The edge, closed the same day — by the one observation this process cannot make

Everything above proves the file is in the running container at the path the JS fetches.
It does **not** prove Cloudflare Access admits that path, because a committed allowlist
rule is not a served route, and the tunnel needs an interactive PIN that an automated
process has no way to satisfy. Session 238 hit the same wall and recorded it as an open
edge.

**Cray closed it, minutes after the deploy, by opening the live system** —
`oct-fleet-maintenance.cray-n8n.com/#F`, through Cloudflare Access, screenshot taken.
Observed on that surface:

- the **`อ่านเรื่องเล่าตั้งต้น` button** renders on Tab F, against the procedure prose;
- the **panel opens** — so `^/assets/.+$` does admit `/assets/narratives/…` at the edge,
  which is the claim no offline test and no in-container read can make;
- the **legend renders all six steps**, with step 3 (`reshape`) dimmed and carrying
  *"ไม่มีต้นทางในเรื่องเล่า — เป็นกลไกที่ระบบต้องมีเอง"* — the deliberate gap survived the
  trip to production intact;
- the **highlights carry their superscript numbers** in the prose;
- the **front matter is absent** — no PLAN number, no *"ฉบับปรับแก้เลอะ"*, no
  *"Cray-modified"* on a customer-facing screen.

Recorded as Cray's observation rather than as this process's measurement, because that is
what it is. The distinction matters: it is the half of Layer 3 that only a human holding
the Access credential can perform, and pretending otherwise would make the next deploy's
"verified" weaker than it looks.

## What remains unverified

- **The visitor beat played end to end on the live system.** Doing so would consume the
  beat, which `DEMO-STATE` currently reports `PRISTINE`. Left deliberately unplayed.

## Correction owed to the runbook

`docs/runbooks/published-demo-redeploy.md` §3 should name, at the point it hands over
`deploy.py`, that the script is energy-only and that other systems deploy by the manual
sequence. The fact is recorded in three places already — `deploy.py:65-83`,
`tests/deploy/test_deploy.py:44-47`, and this system's `DEMO-RESET.md` §3.1 — but not at
the place a reader following the runbook in order meets the command. To be applied in its
own PR.

## Reference

- Feature: [#1218](https://github.com/CrayJThiemsert/vero-lite/pull/1218), merged at `907a842`.
- Operator procedure for this system: `deploy/published/oct-fleet-maintenance/DEMO-RESET.md`.
- Prior host-state records: [`2026-08-18-plan0110-fleet-demo-reset-deploy.md`](2026-08-18-plan0110-fleet-demo-reset-deploy.md)
  (the reset tool's own deploy) and [`2026-08-16-plan0103-step10-fleet-bring-up.md`](2026-08-16-plan0103-step10-fleet-bring-up.md)
  (the image-ship mechanics and the forward-slash correction this deploy relied on).
