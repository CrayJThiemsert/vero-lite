# Deploying this system

> Lives **in this profile directory** for the same reason `DEMO-RESET.md` does, and the
> reason is a rule rather than a filing preference. The commands below must carry this
> system's literal compose path and project name to be runnable at all, and a vero-lite
> file naming two published systems is a shadow ingress map (ADR-0036 D2), enforced by
> `tests/deploy/test_published_profiles.py`. The shared runbook already spends its one
> allowed label, so this procedure cannot live there. It belongs to this system, so it
> lives with it.
>
> **Why this file exists at all.** Before it, this system's deploy sequence existed only
> as prose inside `docs/logs/` — records of what happened once, in the archeology tier
> rather than the procedure tier (`CLAUDE.md` §10). Two deploys, two logs, and each one
> re-derived the sequence from the last. Both re-derivations found something the previous
> summary had dropped: the image ship (2026-08-16) and the fact that the shared script
> cannot target this system (2026-08-18). That is what a procedure with no home does.

---

## 0. The gate

Every command here that reaches the deploy host is a **host-state change** and needs
**Cray's explicit go, recorded before it runs** (`CLAUDE.md` §8). The go is **per
occasion** — one given for a previous deploy does not carry.

Ask per phase, not once for everything. §2 is read-only and can be gone first; §3 is the
half that changes the system.

---

## 1. 🔴 The shared deploy script does NOT deploy this system

`deploy/published/deploy.py` targets a **different profile**. Its compose path, project
name, image tag and connector config are hardwired constants and it has no `--system`
selector — deferred by Cray's typed s219 decision, recorded at `deploy.py:65-83` and
pinned by `tests/deploy/test_deploy.py`.

Running it with `--execute` while intending to deploy **this** system builds and ships the
other profile's image and brings up the other project: nothing happens here, and a
container is recreated on a system nobody meant to touch.

**Its plan mode is safe and is the cheap check** — `python3 deploy/published/deploy.py
--host <ssh-alias>` prints every command and touches nothing (`Runner.run` returns before
`subprocess.run` when not executing). Read which profile it names. If it is not this one,
you are in the right file and it is the wrong tool.

**This system deploys by the sequence below.** Do not add a branch for it to that script.

---

## 2. Pre-flight — read-only, changes nothing

Run all four before asking for the §3 go. Each is a read.

```bash
ssh <ssh-alias> hostname
ssh <ssh-alias> docker ps --format json
ssh <ssh-alias> docker compose ls --all --format json
ssh <ssh-alias> docker compose -f C:/projects/vero-lite/deploy/published/oct-fleet-maintenance/docker-compose.yml -p oct-fleet-maintenance exec -T app python -m services.db.demo_run_reset
```

| Read | Pass |
|---|---|
| `docker ps` | **capture the container ids and uptimes** — this is the do-no-harm baseline, and it is worthless captured afterwards |
| `docker compose ls` | no project named `vero-published` (the shared runbook's §0b stop condition). ⚠️ Also confirm **this** project appears, or the read proved nothing |
| `docker image inspect` on the live tag | note the id — it is the rollback point |
| the reset module, **plan mode** | one of `DEMO-STATE: PRISTINE` / `CONSUMED`. 🔴 **No token at all is a FAILED CHECK, never a pass** |

**The demo-state read decides the shape of the deploy.** `PRISTINE` → no reset, skip
straight to §3. `CONSUMED` → read `DEMO-RESET.md` **before** §3, because its ordering
constraint (reset first, boot second) changes the sequence.

### What you may not need — establish it, do not assume it

- **A host `git pull`** is only needed if something the host reads has changed. The host
  reads `docker-compose.yml` and `cloudflared/config.yml` from its checkout, not from the
  image. Check with `git diff --name-only <last-deployed-sha>..HEAD -- deploy/published/oct-fleet-maintenance/`.
- **`--force-recreate cloudflared`** is only needed if `cloudflared/config.yml` changed in
  that same diff. Recreating the connector re-registers the tunnel for no reason otherwise.

---

## 3. The sequence — five commands, in this order

```bash
ssh <ssh-alias> docker tag oct-fleet-maintenance-app:latest oct-fleet-maintenance-app:prev
docker save oct-fleet-maintenance-app:latest | ssh <ssh-alias> docker load
ssh <ssh-alias> docker image inspect oct-fleet-maintenance-app:latest
ssh <ssh-alias> docker compose -f C:/projects/vero-lite/deploy/published/oct-fleet-maintenance/docker-compose.yml -p oct-fleet-maintenance config --quiet
ssh <ssh-alias> docker compose -f C:/projects/vero-lite/deploy/published/oct-fleet-maintenance/docker-compose.yml -p oct-fleet-maintenance up -d
```

| # | Step | Pass, fixed **before** the run |
|---|---|---|
| 1 | tag `:prev` | resolves to the **old** id from §2. 🔴 **This is the whole rollback story** — without it a bad deploy costs a rebuild-and-ship to undo |
| 2 | ship over ssh **stdin** | a `Loaded image` line. No staging path, no Windows path in the transfer, no tar left on the host |
| 3 | inspect on the host | **id IDENTICAL to the dev box.** This is the guarantee |
| 4 | `config --quiet` | **zero bytes.** Proves both required host secrets interpolate |
| 5 | `up -d` | **only `app` Recreated**; `postgres` and `cloudflared` stay `Running` |

**Build on the dev box, never on the host.** The host's Docker Desktop credential helper
cannot run without an interactive desktop session, so even an anonymous pull of a public
base image fails there. The build needs `OCT_FLEET_DB_PASSWORD` and
`CLOUDFLARED_CREDENTIALS_FILE` set to **throwaway placeholders** — compose interpolates
the whole file before deciding what to build, and this profile declares both required.
Never real values; they are secrets and they live in the host environment.

🔴 **Step 3's id equality is the guarantee, and "a rebuild produced the same id" is not.**
Buildkit's provenance attestation makes an id identify a *build* rather than its content,
so it changes on every rebuild even when every layer is a cache hit. Ids are comparable
**across machines**, never across rebuilds.

⚠️ **Step 4 must carry `--quiet`.** Without it the command prints the interpolated config,
including `DATABASE_URL` with the password and the full `API_KEYS`.

---

## 4. Verify — against the §2 baseline, not against a memory

```bash
ssh <ssh-alias> docker inspect oct-fleet-maintenance-app
ssh <ssh-alias> docker logs --tail 25 oct-fleet-maintenance-app
ssh <ssh-alias> docker ps --format json
```

| Read | Pass |
|---|---|
| the container's `.Image` | equals the id loaded in §3 — proves the deploy **took effect**, which shipping alone does not |
| the boot log | names the seeds. `run 'run-fleet-operate-demo' already present — skip` means the rows survived and the visitor's beat is untouched |
| the reset module, plan mode again | the same `DEMO-STATE` you started with, unless you deliberately reset |
| `docker ps` | this system's `cloudflared` and `postgres` keep their **§2 container ids** — the tunnel never re-registered and `pgdata` was never at risk. Sibling systems' containers unchanged |

**Verify a file you shipped by reading it inside the running container**, not by trusting
the Dockerfile. Plain words only — no quotes, no braces:

```bash
ssh <ssh-alias> docker compose -f C:/projects/vero-lite/deploy/published/oct-fleet-maintenance/docker-compose.yml -p oct-fleet-maintenance exec -T app sha256sum /app/services/api/main.py
```

---

## 5. Rollback

```bash
ssh <ssh-alias> docker tag oct-fleet-maintenance-app:prev oct-fleet-maintenance-app:latest
ssh <ssh-alias> docker compose -f C:/projects/vero-lite/deploy/published/oct-fleet-maintenance/docker-compose.yml -p oct-fleet-maintenance up -d
```

Then re-read §4's first row: **confirm which image ended up running.** A rollback that
silently did not take is the same failure as a deploy that silently did not take.

⚠️ **`:prev` is one deep.** Two bad deploys in a row and the good image is gone from the
host — it would have to be rebuilt and shipped again.

---

## 6. Two rules for every remote command here

1. **Plain words, forward slashes.** Remote commands land in **PowerShell**: no quotes, no
   `$`, no braces, and a backslashed path is silently stripped to a relative one that
   fails as *"the system cannot find the file"* — an error that sends you checking the host
   checkout, which is intact. Every command above is already in the safe form.
2. **Read output text, never exit codes.** The ssh→PowerShell chain reports success for
   commands that never executed. Where a step prints a token, the token is the verdict.

---

## 7. What this procedure cannot establish

**That the change is reachable through the edge.** Everything above proves what is in the
running container. Cloudflare Access sits in front, and it needs an interactive PIN that no
automated step can satisfy — so "the allowlist admits this path" is a claim only a human
opening the live system can close. State it as an open item and hand it over; do not let a
green sequence imply it.

---

## Reference

- `DEMO-RESET.md` — the demo-state check, and the ordering constraint when a reset is needed.
- `README.md` — provisioning, secrets, and what this profile serves.
- `docs/runbooks/published-demo-redeploy.md` — the shared runbook. Its §0b stop condition
  and its rollback and image-provenance reasoning apply here; its §3 script does not.
- `docs/logs/` — this system's prior host-state records, each with the measured evidence
  of one deploy. Records, not the procedure; this file is the procedure.
