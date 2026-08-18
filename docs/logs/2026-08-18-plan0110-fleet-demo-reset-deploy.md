# PLAN-0110 Step 7 — the fleet demo reset deployed and exercised on MS-S1

**Date:** 2026-08-18 (session 238)
**Event type:** host-state change on MS-S1, under an explicit typed §8 go
**Operator-grade detail:** this file. No gitignored companion — everything below is safe to commit.

## The go

**Cray, typed, 2026-08-18 (session 238):** *"deploy MS-S1, go"* — given after PLAN-0110
Steps 1–6 merged to `main` at `20669ae` ([#1213](https://github.com/CrayJThiemsert/vero-lite/pull/1213))
with CI green, and after the two divergences that PR carries were stated and read.

## Pre-flight baseline — captured before any host-state action

The do-no-harm comparison is against these, not against a memory:

| Container | State at probe time |
|---|---|
| `oct-fleet-maintenance-app` | `Up 2 days (healthy)` |
| `oct-fleet-maintenance-cloudflared` | `Up 2 days` |
| `oct-fleet-maintenance-postgres` | `Up 2 days (healthy)` |
| the two sibling systems' `app` containers | `Up 6 days` / `Up 8 days`, both `(healthy)` |
| the two sibling systems' `cloudflared` containers | `Up 6 days` |

Database counters, read directly from the live Postgres before anything was touched:

```
AUDIT_ROWS: 9
PIPELINE_RUNS: 2
run-fleet-demo-history   waiting_human   subject NULL
run-fleet-operate-demo   waiting_human   subject NULL
```

🔴 **`run-fleet-demo-history` at `waiting_human` is PR #1209's defect, still live.** A
repair whose invoice is keyed and whose case is CLOSED was sitting in the visitor's
approval queue. The fix shipped on 2026-08-18 but could not take effect, because
`services/api/main.py:307` skips the seed whenever the run row exists — which is the
same skip PLAN-0110 exists to break. This deploy is where that fix actually lands.

## 🔴 The finding: the documented reset ordering CANNOT hold on the first deploy

`deploy/published/oct-fleet-maintenance/DEMO-RESET.md`, merged in #1213 hours earlier,
prescribes **reset `--execute` first, `up -d` second** — because the seeds rebuild only
in the boot lifespan, so resetting after boot leaves the demo empty.

That ordering is correct for every deploy **except the one that introduces the tool**.
Measured on the live host before shipping anything:

```
ssh ms-s1 docker exec oct-fleet-maintenance-app python -m services.db.demo_run_reset
  →  /app/.venv/bin/python: No module named services.db.demo_run_reset      (exit 1)
```

The reset ships **inside the image it is meant to run before**. On a bootstrap deploy
the running container cannot have it.

**It fails safely, and by its own rule.** No `DEMO-STATE:` token is printed, and
`DEMO-RESET.md` §1 already says in writing that a missing token is a FAILED CHECK, never
a pass. The hazard is a wrong *ordering*, not a silent one.

**The bootstrap sequence used here** — two boots instead of one, and the intermediate
state is the consumed one the system was already in, so there is no regression window:

1. ship the image
2. `up -d` — app recreated on the new image; the boot seed still logs
   `run 'run-fleet-operate-demo' already present — skip` (the rows are still there)
3. `docker exec … --execute` — now the module exists
4. `compose restart app` — the boot lifespan rebuilds through the virgin-boot path

Written into `DEMO-RESET.md` §2a in the same PR as this record.

## Evidence, step by step — every pass/fail read fixed BEFORE the run

| # | Action | Pre-committed pass | Result |
|---|---|---|---|
| 1 | build on the dev box | image id captured | `HEAD=20669ae`, branch `main`, tree clean; `f35eeac2…` (was `f15acc13…`) |
| 2 | `docker save` → `ssh … docker load` | **id IDENTICAL on both machines** | `IDENTICAL` |
| 3 | `compose config --quiet` on host | exit 0 | 0 |
| 4 | `compose up -d` | **only `app` Recreated** | `postgres Running`, `cloudflared Running`, `app Recreated → Healthy` |
| 5 | plan mode | `DEMO-STATE: CONSUMED` | `CONSUMED` |
| 6 | `--execute` | counts printed, **`audit_log` absent from them** | 2 `pipeline_runs`, 2 `repair_case`, 6 `repair_case_run_link`, 11 `step_results` |
| 7 | `compose restart app` | boot log names both seeds | `settled history case seeded` + `run 'run-fleet-operate-demo' seeded (status=waiting_human)` |
| 8 | plan mode | `DEMO-STATE: PRISTINE` | `PRISTINE` |
| 9 | DB counters | audit rows **never decrease** | 9 → **17** |

Step 2's id equality is the guarantee. "A rebuild produced the same id" would not be —
buildkit's provenance attestation makes an id identify a *build* rather than its content
(the bring-up log's own note, still true).

Step 5 does double duty and that is why it is a gate rather than a formality: the module
was **measured absent** from the old image twenty minutes earlier, so a printed token can
only come from the new image running. Image provenance and demo state, one read.

### Final live state

```
AUDIT_ROWS: 17
PIPELINE_RUNS: 2
run-fleet-demo-history   completed       {"object_type": "Truck", "primary_key": "truck-02"}
run-fleet-operate-demo   waiting_human   {"object_type": "Truck", "primary_key": "truck-02"}
```

Three things changed that matter:

1. **Both runs now carry a `subject`** — `NULL` before. Tab A's double gate
   (`view-map.js` `computeRunFlags`) can key a marker for the first time on this system.
2. **The history run is `completed`** — PR #1209's fix is live. The settled repair has
   left the visitor's approval queue.
3. **The audit chain grew, never shrank** — 9 → 17. The reset deleted from four tables and
   `audit_log` was not one of them. *The demo resets; the audit log remembers.*

### Do-no-harm, verified rather than assumed

Only `oct-fleet-maintenance-app` changed (new container id, `Up 49 seconds (healthy)`).
This system's `cloudflared` and `postgres` kept their **original container ids** and their
`Up 2 days` — so the tunnel never re-registered and `pgdata` was never at risk. Both
sibling systems' containers were untouched at `Up 6 days` / `Up 8 days`.

## What was NOT verified here, stated rather than implied

- **The rendered marker on the published surface.** The map ring was verified in the local
  browser under the published profile before the deploy (in-flight amber dashed by
  default; a green, non-breathing settled ring under the `completed` mode; in-flight
  winning the precedence under `all`). It was **not** re-observed through the tunnel,
  which sits behind Cloudflare Access and needs an interactive PIN. The `/runs` payload it
  reads is verified above; the paint is not re-verified on this host.
- **The visitor beat played end to end on the live system.** Doing so would consume the
  beat this deploy just restored.

## Reference

- PLAN: [`docs/plans/done/0110-fleet-demo-run-markers-filter-and-deploy-reset.md`](../plans/done/0110-fleet-demo-run-markers-filter-and-deploy-reset.md) Step 7.
- Operator procedure: `deploy/published/oct-fleet-maintenance/DEMO-RESET.md`.
- Prior host-state record for this system: [`2026-08-16-plan0103-step10-fleet-bring-up.md`](2026-08-16-plan0103-step10-fleet-bring-up.md) — the image-ship mechanics and the forward-slash correction this deploy relied on.
