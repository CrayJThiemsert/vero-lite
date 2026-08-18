# Resetting this system's demo — and checking whether it needs it

> Lives **in this profile directory** rather than in
> `docs/runbooks/published-demo-redeploy.md`, and that placement is a rule rather than
> a filing preference. ADR-0036 D2 puts the cross-system map in the portal repo: a
> vero-lite file naming two published systems is a shadow ingress map, and
> `tests/deploy/test_published_profiles.py::test_ac5_no_file_outside_a_profile_lists_two_system_labels`
> enforces it. The shared runbook already names one system, so the commands below —
> which must carry this system's literal compose path and project name to be runnable
> at all — cannot live there. They belong to this system, so they live with it. The
> runbook points here generically.

## Why this exists

This system ships a refused-then-granted approve beat that a visitor is **meant** to
play: `^/runs/[^/]+/gate/resolve$` is on the ingress allowlist and the personas ship
with keys. Playing it **consumes** it. `services/api/main.py:307` skips the operate
seed whenever the run row exists — *in any state* — so the seed never re-arms, and
every visitor after the first finds a demo with nothing left to approve.

**A redeploy alone does not fix this.** The rows survive the new image, and the boot
log says `run 'run-fleet-operate-demo' already present — skip`. That line was measured
on the live system.

🔴 **This is the priced cost of a ruled decision, not an oversight.** PLAN-0110 SD-C
(Cray, typed, s237) put the reset at deploy time rather than at boot, so that a
container crash-restart can never wipe a visitor's half-played run. The accepted
consequence is that a consumed demo **stays consumed until someone deploys** — which
is exactly why the zero-risk check below is worth running on an ordinary day.

## 1. Check the state — deletes nothing

```bash
ssh <ssh-alias> docker compose -f C:/projects/vero-lite/deploy/published/oct-fleet-maintenance/docker-compose.yml -p oct-fleet-maintenance exec -T app python -m services.db.demo_run_reset
```

Prints exactly one of:

- `DEMO-STATE: PRISTINE` — a visitor can play the beat. Nothing to do.
- `DEMO-STATE: CONSUMED` — the beat is spent, or the runs are missing. Reset below.

🔴 **No token printed at all is a FAILED CHECK, never a pass.** Its absence means the
module did not run — `python -m` against a wrong module path is a silent no-op. Read
the token; do **not** read the exit code, which passes through an ssh→PowerShell chain
that can report success for a command that never executed.

`PRISTINE` is stricter than "the run is `waiting_human`". The procedure is a
`request → approve → fulfill` spine whose **terminal** step is itself gated, so a run
whose `approve` gate a visitor already resolved parks again at `fulfill` — still
`waiting_human`, still counted in the Monitor, and no longer offering the beat. The
check reads the suspended STEP, not just the status.

## 2. Reset, then boot — in that order

```bash
ssh <ssh-alias> docker compose -f C:/projects/vero-lite/deploy/published/oct-fleet-maintenance/docker-compose.yml -p oct-fleet-maintenance exec -T app python -m services.db.demo_run_reset --execute
```

🔴 **The ORDER is load-bearing: reset FIRST, `up -d` second.** The seeds rebuild only
in the app's boot lifespan. Resetting *after* the app has booted leaves the demo
**EMPTY** until it next boots — a worse state than the consumed one you started from.

If the redeploy does not recreate the app container (image id unchanged), follow with:

```bash
ssh <ssh-alias> docker compose -f C:/projects/vero-lite/deploy/published/oct-fleet-maintenance/docker-compose.yml -p oct-fleet-maintenance restart app
```

Then re-run step 1 and confirm `DEMO-STATE: PRISTINE`.

## 2a. 🔴 The ONE case where the order above is impossible — a bootstrap deploy

Step 2's ordering assumes the reset tool is already on the running container. **It is
not, on the deploy that introduces it** — the tool ships *inside the image it is meant
to run before*. Measured on the live host, 2026-08-18, against the pre-PLAN-0110 image:

```
docker exec oct-fleet-maintenance-app python -m services.db.demo_run_reset
  →  /app/.venv/bin/python: No module named services.db.demo_run_reset   (exit 1)
```

It fails **safely and by this document's own rule**: no `DEMO-STATE:` token is printed,
and §1 already says a missing token is a failed check, never a pass. So the hazard is a
wrong ordering, not a silent one.

**When the tool (or a change to it) is part of the image you are shipping, use this
sequence instead** — two boots rather than one. The window between them leaves the demo
in the consumed state it was already in, so there is no regression:

1. ship the image (`docker save` → `ssh … docker load`; the image id must be **identical**
   on both machines — see the bring-up log)
2. `up -d` — the app is recreated on the new image. Expect the boot log to still say
   `run 'run-fleet-operate-demo' already present — skip`; the rows are still there, and
   that is the defect, not a failure of this step
3. **now** run §1's check — a printed token doubles as proof the new image is running —
   then §2's `--execute`
4. `restart app` — the boot lifespan rebuilds through the virgin-boot path

Every subsequent deploy uses §2's ordering, because by then the tool is already deployed.

## 3. Four things to know about these commands

1. **The shared `deploy/published/deploy.py` is not used for this system.** That script
   is hardwired to the energy profile's compose file by Cray's typed s219 decision
   (recorded at `deploy.py:65-83`), with `--system` parameterization explicitly
   deferred and `tests/deploy/test_deploy.py:44-47` pinning it. This system is deployed
   by the manual sequence in
   `docs/logs/2026-08-16-plan0103-step10-fleet-bring-up.md`. Do **not** add a step for
   this system to that script.
2. **Plain words only, forward slashes.** Remote commands land in **PowerShell**: no
   quotes, no `$`, no braces, and a backslashed path is silently stripped to a relative
   one (bring-up log, Correction 1). The commands above are already in the safe form.
3. **No credential leaves the deployed system.** The reset runs *inside* the app
   container on its own `DATABASE_URL` and `OCT_VERTICAL`, so it aims at the right
   database by construction, and it refuses outright if `OCT_VERTICAL` is not
   `fleet_maintenance`.
4. **The audit log is never touched.** `audit_log.run_id` carries no ForeignKey and
   `verify_chain` walks only audit rows, so every visitor decision stays on the record
   across every reset. Worth one sentence in the demo: *the demo resets; the audit log
   remembers.* Confirm afterwards with `GET /audit/verify`.

## 4. What a reset legitimately changes

Recorded rather than hidden, because both are visible on the demo surface:

- the repair-order number **advances by one** per reset (gap-free by construction —
  `operate_seed.py:571-577`);
- each rebuild **appends** one seed-round of audit rows.

Honest allocation and honest audit. Never suppress either.
