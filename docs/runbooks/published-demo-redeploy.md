# Redeploying the published OCT demo

> **Scope.** This is the procedure that **repeats**: `main` moved, make the live
> demo be that, and prove it. Standing the system up the first time — the
> Cloudflare account work, the tunnel, the Access application, the host secrets —
> is [`published-demo-bring-up.md`](published-demo-bring-up.md) and does not
> repeat. Teardown, PDPA deletion paths and the prompt-log obligations are
> [`published-demo-operations.md`](published-demo-operations.md).

---

## 0. The standing gate

Every command in this runbook that reaches the deploy host is a **host-state
change** and needs **Cray's explicit go, recorded before it runs** (`CLAUDE.md`
§8). The gate covers the whole host, not just inference. The script's default
mode is a plan for exactly this reason — you can prepare and review a deploy
without asking for anything.

---

## 1. The shape of the problem

The published app runs on MS-S1 from an image built on the workstation. Three
facts set the whole procedure:

1. **The deploy host cannot `docker pull`.** Docker Desktop's credential helper
   needs an interactive desktop session and fails with *"A specified logon session
   does not exist"* — for **anonymous pulls of public images**, and **while a
   console session is signed in**. Auto-login does not fix it. So the host never
   builds; the workstation builds and ships the image.
2. **compose reads three files from the host's checkout, not from the image** —
   the compose file itself, `published.env` (via `env_file:`), and
   `cloudflared/config.yml` (a bind mount). Everything else the deploy needs is
   inside the image.
3. **`compose up` decides for itself whether a container is stale.** That decision
   is the one thing between a redeploy and a silent no-op, and it is not
   observable from the commands' output.

Fact 3 is why this procedure asserts an *effect* rather than counting successful
steps.

---

## 2. The two guarantees, which are not the same thing

Keep these apart — session 213 measured the first and it is easy to read it as
the second:

| Check | What it proves | What it does **not** prove |
|---|---|---|
| `docker image inspect` id equal on both machines | the **transfer** arrived intact | anything about what is running |
| running container's `.Image` equal to the loaded id | the **deploy took effect** | that the new code is *correct* |

⚠️ **Never use "a rebuild produced the same id" as a check.** buildkit's provenance
attestation makes the id identify a *build*, not its content, so it changes on
every rebuild even when every layer is a cache hit. Ids are comparable **across
machines**, never across rebuilds.

---

## 3. Deploy

```bash
python3 deploy/published/deploy.py --host <ssh-alias>
```

That is a **plan**. It prints every command and touches nothing. Read it, then
get Cray's go, then:

```bash
python3 deploy/published/deploy.py --host <ssh-alias> --execute --smoke-url https://<subdomain>/health
```

What it does, in order:

1. builds `app` from this checkout;
2. tags the host's current image `:prev` — **the rollback point, taken before the
   load overwrites `:latest`**;
3. `save` → `scp` → `load`, then asserts the ids match across machines;
4. `git pull --ff-only` on the host checkout, unconditionally — deciding whether a
   pull is needed is more expensive than pulling, and removes "I forgot to pull";
5. `compose up -d`, plus `--force-recreate cloudflared` **only if
   `cloudflared/config.yml` changed in that pull** (see §4);
6. asserts the running container's image is the one just loaded;
7. smokes: both services present, no published host port, `/health` internally,
   and `/health` through the edge returns **302**.

Exit code is 0 only if every check passed. The ledger at the end names any that
did not.

**Why a script and not a list of commands to paste.** Every command runs through
`subprocess.run` with a **list argv and no shell**. Session 213 lost time to three
separate shapes of the same hazard doing this by hand — a `$` that expanded one
shell layer early, inner double quotes stripped by PowerShell, and a `| head` that
reported the truncator's exit status while cutting the traceback. None of the
three can occur when nothing is re-parsed by an intervening shell.

---

## 4. What kind of change needs what

| What changed | Image rebuild | Host `git pull` | Connector recreate |
|---|---|---|---|
| App code, templates, UI assets | yes | harmless | no |
| `published.env` | yes¹ | **required** | no |
| `docker-compose.yml` | yes¹ | **required** | no |
| `cloudflared/config.yml` (the ingress allowlist) | no² | **required** | **required** |
| Cloudflare Access policy, rate rule, DNS | no | no | no — vendor-side, no deploy at all |
| The domain | no | no | no — see bring-up §10 |

¹ The script always rebuilds; it is cheap and removes a branch.
² Listed as "no" because nothing in the image changes — but the script rebuilds
anyway, and that is fine.

🔴 **The connector row is the trap.** `config.yml` is a **bind mount**: the new file
is on disk the moment the pull lands, and `compose up -d` sees no reason to replace
the container — so cloudflared keeps enforcing the ingress map it read at start.
Nothing in any command's output indicates this. The script detects it by diffing
the pull and forces the recreate; if you are ever doing this by hand, do it
yourself.

---

## 5. Rollback

```bash
python3 deploy/published/deploy.py --host <ssh-alias> --execute --rollback
```

Retags `:prev` back to `:latest`, force-recreates the app container, and **asserts
which image ended up running** — a rollback that silently did not take is the same
failure as a deploy that silently did not take.

Two limits, stated so they are not discovered mid-incident:

- **`:prev` is one deep.** Two bad deploys in a row and the good image is gone from
  the host. Recover by deploying from a known-good commit.
- **The first redeploy after bring-up has no `:prev`.** The script reports that as
  a FAIL rather than swallowing it: the deploy still completes, but rollback is
  unavailable until the next one.

Rollback replaces the app, not the link. To cut public access instead — stop the
connector, revoke one visitor, revoke everyone, remove the route, destroy the
tunnel — see bring-up §11, in that order of blast radius.

---

## 6. If the script cannot run

The manual sequence, for the case where Python is unavailable or the script itself
is what is suspect. Run each command **from a file**, never typed inline into an
`ssh "…"` string.

🔴 **Two rules, both measured on this host on 2026-08-08 — the first draft of this
section broke both and every remote command in it failed.**

1. **Never send `--format={{…}}` to the host.** The remote shell is **PowerShell**
   (`ssh <host> 'echo %COMSPEC%'` returns the string unexpanded, so it is not cmd),
   and PowerShell reads `{…}` as a script block. `docker version --format={{.Server.Version}}`
   comes back as `unknown shorthand flag: 'e' in -encodedCommand`. Ask for plain
   JSON instead and read the field yourself — `docker inspect <thing>` with no
   `--format` returns the whole object, exit 0.
2. **`git -C <path>`, not `cd <path> && git`.** Chaining with `&&` inside an `ssh`
   argument hands the chaining to that same shell.

Local half:

```bash
CLOUDFLARED_CREDENTIALS_FILE=/nonexistent/placeholder docker compose -f deploy/published/oct-energy/docker-compose.yml build app
docker image inspect vero-published-app:latest --format="{{.Id}}"     # local only — note this
docker save vero-published-app:latest -o /tmp/app.tar
```

The placeholder is required: compose interpolates the **whole** file before
deciding what to build, and the connector declares that variable
required-with-no-default, so a bare `build app` exits 1 without ever building.

Remote half — the tar goes in on **stdin**, so there is no staging path to create
and no Windows path in any command:

```bash
ssh <host> docker tag vero-published-app:latest vero-published-app:prev
ssh <host> docker load < /tmp/app.tar
ssh <host> docker image inspect vero-published-app:latest
ssh <host> git -C C:\projects\vero-lite pull --ff-only
ssh <host> docker compose -f C:\projects\vero-lite\deploy\published\docker-compose.yml -p vero-published up -d
ssh <host> docker inspect vero-published-app
```

Read `.Id` out of the third command's JSON and `.Image` out of the sixth's. **They
must be equal, and equal to the local id** — the first pair proves the transfer,
the second proves the deploy took effect.

If `cloudflared/config.yml` changed in that pull, add:

```bash
ssh <host> docker compose -f C:\projects\vero-lite\deploy\published\docker-compose.yml -p vero-published up -d --force-recreate cloudflared
```

---

## 7. Reading the result

`302` from the public `/health` is the healthy answer: Access is in front of a
working origin.

| Code | Meaning |
|---|---|
| **302** | healthy — the gate is applied and the origin is up |
| **530** | the tunnel is down — check the connector on the host |
| **200** | 🔴 **a security failure** — Access is not applied to this hostname |

A `200` is not a better result than a `302`. It means the demo is open.

---

## 7b. What the first real run looked like (measured 2026-08-08)

Recorded so the next operator can tell "worked" from "ran". Deploying `d0a2808`
over the image session 213 had shipped:

```
rollback point tagged                : PASS  (vero-published-app:prev)
image transferred intact             : PASS  (local sha256:153324a2995c… vs host sha256:153324a2995c…)
host checkout updated                : PASS  (9601f068 -> d0a28080, 14 files)
running container uses the new image : PASS  (container sha256:153324a2995c… vs loaded sha256:153324a2995c…)
both services present                : PASS
no published host port               : PASS
app healthcheck reports healthy      : PASS  (healthy)
edge gate is in front                : PASS  (HTTP 302)

=== 8 checks, 0 FAIL ===
```

Verified independently of that ledger, by reading the host directly: the container
**id** changed (`11b0fb7201be…` → `45f6440a2d48…`, i.e. a genuinely new container,
`Up 45 seconds` against the previous `Up 10 hours`), its `.Image` moved
`4c88145c8653…` → `153324a2995c…`, `:prev` now holds `4c88145c8653…` — the old
image, so rollback is live — and both `/health` and `/` answer `302` at the edge.

The connector was **not** recreated, correctly: none of the 14 changed files was
`cloudflared/config.yml`.

---

## 8. Known ground, so it is not rediscovered

- **The host checkout drifts.** It is a normal clone at `C:\projects\vero-lite`;
  nothing keeps it current between deploys. Step 4 pulls it every time.
- **Every deploy leaves a dangling image** — the one `:latest` used to point at,
  now untagged except while it is `:prev`. Reclaim with `docker image prune` on the
  host when disk matters; do **not** prune between a deploy and its rollback window.
- **`CLOUDFLARED_CREDENTIALS_FILE` must be set for a local `build`**, because
  compose interpolates the whole file before deciding what to build and the
  connector declares that variable required. Any path works — the script passes a
  placeholder. Nothing is created there; volumes are materialised at
  container-create time, not at build.
- **The credentials file's ACL on the host is inherited and wide**
  (`BUILTIN\Users: Read`, `Authenticated Users: Modify`). The `icacls` fix is in
  bring-up §8 and **was not applied as of session 213**. It needs a bind-mount
  re-test in the same sitting.
- **Docker Desktop does not auto-start on the host** (`com.docker.service` =
  `Manual`), and the daemon has been reachable over SSH anyway. Why it stopped
  serving 12 days before session 213 is still unexplained — if a deploy fails at
  the first `ssh … docker …`, that is the first thing to check.

---

## 9. Guarding this procedure

`tests/deploy/test_deploy.py` holds it to two things. The **drift guards** read the
committed `docker-compose.yml` and assert the script's project, container and
image literals still match it — the script is stdlib-only by design (an operator
runs it outside the venv) so it cannot read those names at runtime. The **scenario
cases** drive the real entry point against fake `docker`/`ssh`/`scp`/`curl` on
`PATH`, so argv construction, the no-shell invocation and exit-code handling are
all real and only the far side of the process boundary is simulated.

The load-bearing case is the one where every command succeeds and the running
container's image does not match what was loaded: it asserts the run **fails**.
That is the failure with no visible symptom, and it is the reason this procedure
exists in this shape.

---

*Sources: `deploy/published/deploy.py`, `deploy/published/oct-energy/docker-compose.yml`,
[`published-demo-bring-up.md`](published-demo-bring-up.md) §7/§9/§11, ADR-0035
(D1 exposure model, D3 Access), PLAN-0100 Step 8. The host-side facts in §8 were
measured in session 213 — re-confirm rather than trusting that record.*
