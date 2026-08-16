# PLAN-0103 Step 10 — fleet-maintenance brought up as published system #3

**Date:** 2026-08-16 (session 234)
**Event type:** host-state change on MS-S1, under an explicit typed §8 go
**Operator-grade detail:** this file. No gitignored companion — everything below is safe to commit.

> ⚠️ **Domain naming.** This record uses `oct-fleet-maintenance.<DOMAIN>` rather than the
> apex, per ADR-0035 D1(3). That clause's scope over evidence documents is **ADR-0035
> OQ-6, open and unruled**; while it is open this record takes the conservative side, as
> [`2026-08-11-plan0103-step10-procurement-bring-up.md`](2026-08-11-plan0103-step10-procurement-bring-up.md)
> did. The subdomain **label** is not in question.

## The go

**Cray, typed, 2026-08-16 (session 234):** *"ทำข้อ 1 fleet bring-up … allow typed §8 go
ตามที่แนะนำ"* — the §8 go for **this bring-up specifically**, given in the form the
preceding session recommended: citing the RoPA by path.

**AC-11's citation, which is what the go was waiting for:**
[`docs/compliance/ropa-fleet-cases.md`](../compliance/ropa-fleet-cases.md) — **Adopted by
Cray (controller), typed, 2026-08-15**, on `main` at `610369f`. Its own Status block states
the ordering this AC exists to enforce: *"The system it describes is **NOT live**; that is
the point of adopting it now."*

**PLAN-0106's AC-7 ordering clause** is discharged by the same record: PLAN-0106 merged to
`main` at `5425822` on 2026-08-15, **before** this go, and this record cites it by number.

Deployment order is SD-2(b)'s ruling — procurement first, fleet second; procurement went
live 2026-08-11. Fleet is the ADR-0037-gated one, and the gate is AC-11 above.

## Pre-flight — what was verified before anything was touched

A read-only probe of MS-S1 preceded every action. **Fleet had never been brought up**: no
`oct-fleet-maintenance` compose project, no container, and neither
`oct-fleet-maintenance-pgdata` nor `oct-fleet-maintenance-prompt-log` existed on the
daemon. The bring-up therefore starts from an empty database by construction, which is
what makes §9.0's schema step load-bearing rather than defensive.

**Live-sibling baseline, captured before the first host-state action** — the do-no-harm
comparison below is against these, not against a memory:

| Container | State at probe time |
|---|---|
| `oct-energy-app` | `Up 5 days (healthy)` |
| `oct-energy-cloudflared` | `Up 3 days` |
| `oct-procurement-app` | `Up 4 days (healthy)` |
| `oct-procurement-cloudflared` | `Up 3 days` |

Every `smb-*` co-tenant container was `exited` three weeks or more earlier — verified by
timestamp rather than assumed.

### 🔴 The host checkout was deliberately NOT pulled, and the reason is measured

The host sat at `205ba4b`; `main` was `3b9a084`, eight commits ahead. **`git diff --stat
205ba4b..3b9a084 -- deploy/` is empty** — not one byte of any published profile changed in
that range. Everything in it lives in `services/` and
`verticals/fleet_maintenance/operate_seed.py`, which are **baked into the image** and never
read from the host checkout at runtime.

So the pull would have bought nothing and cost the one thing worth avoiding: it is the
only step in this sequence that writes into a directory two **running** systems read from.
Skipped for exactly the reason s222 recorded when it skipped it for procurement. The host
checkout's fleet profile files were already byte-identical to `main`.

### 🔴 The image had to be shipped, and this step is missing from every summary of the sequence

`docker images` on MS-S1 carried `oct-energy-app`, `oct-procurement-app` and
`vero-published-app` — and **no `oct-fleet-maintenance-app`**. This system's compose
declares `build:` with no `image:`, so `docker compose up -d` would have tried to build
**on the deploy host**, which runbook §7 documents as failing outright: Docker Desktop's
credential helper cannot run without an interactive desktop session, so even an anonymous
pull of a public base image fails with *"A specified logon session does not exist"*.

The prose summaries of the remaining sequence — in the s232 and s233 handoffs, and in
[`2026-08-15-fleet-cloudflare-artifacts-and-secrets-staging.md`](2026-08-15-fleet-cloudflare-artifacts-and-secrets-staging.md)
§3 — all read *"go record → schema step → `up -d`"* and none of them names the image ship.
Recorded here so the next system's bring-up does not rediscover it at the console.

## Evidence

### Offline gates — run before any host-state action

The ingress allowlist was validated from the committed file, with no Cloudflare account
involved. ⚠️ Judged on **output text**, never on exit code: the trailing-`--config` form
exits 0 while validating nothing.

| Check | Result |
|---|---|
| `ingress validate` | the literal **`OK`** |
| `ingress rule …/demo/hero/governance` | **rule #20 → `http_status:404`** — the catch-all. The governed hero is procurement's story; a match on `http://app:8000` here would have been a leak |
| `ingress rule …/whoami` | **rule #4 → `http://app:8000`** — the persona login is admitted, and on this system that row is load-bearing: without it no persona can be selected and the refused-then-granted beat is unreachable |

The second and third are a matched pair on purpose — one proves the deny-by-default
catch-all still catches, the other proves the allowlist still admits. Either alone is
satisfiable by a broken config.

### Image provenance — the artifact that runs is the one that was built

Built on the dev box against `main` at `3b9a084`, `docker save` → `ssh … docker load` over
**stdin**: no staging path, no Windows path in the transfer, no tar left on the host. The
build needs `OCT_FLEET_DB_PASSWORD` and `CLOUDFLARED_CREDENTIALS_FILE` set to placeholders,
because compose interpolates the **whole file** before deciding what to build and this
profile declares both required.

**Image id identical on both machines:**
`sha256:ecab5052c773edbbe74efb7e2748c3387e8ceba96d3499257bfa219ce92631b0`, and the running
container's `com.docker.compose.image` label carries the same value — so the transfer and
the deploy are each proven, not inferred. Id equality is the guarantee; "a rebuild produced
the same id" is not, because buildkit's provenance attestation makes the id identify a
*build* rather than its content.

`docker compose config --quiet` on the host returned **0**, which is what proves the two
required host secrets interpolate. ⚠️ Always `--quiet`: without it the command prints the
interpolated config, including `DATABASE_URL` with the password and the full `API_KEYS`.

### The schema step (runbook §9.0) — and it mattered here

The database was created by this bring-up: `oct-fleet-maintenance-pgdata` did not exist
beforehand. So the empty-database hazard §9.0 describes was the actual starting state, not
a hypothetical.

```
alembic current  →  0025 (head)
```

That matches `alembic/versions/0025_task_event_seq.py` on disk. It is positive evidence
rather than an absence: `alembic current` on an unmigrated database prints no revision at
all, so the printed `0025 (head)` can only come from the upgrade having run.

Corroborated twice more downstream, which is what makes it more than a one-line read: the
boot log carries **no** `_is_schema_not_applied` ERROR (the s232 backstop stayed silent),
and `GET /runs` returned both seeded runs out of the database through the real route.

### Runtime shape

Three services, all up: `app` healthy, `postgres` healthy, `cloudflared` running.
**`PublishedPort: 0` on every service and `Publishers: []` on the connector** — PLAN-0100
AC-5's property holds, and on this system it holds for a database as well as an app: the
`postgres` service exposes `5432/tcp` and publishes nothing.

App log:

- `verticals discovered: …; active='fleet_maintenance'`, both notifiers **DISARMED**;
- `fleet operate-demo seed: settled history case seeded` and
  `run 'run-fleet-operate-demo' seeded (status=waiting_human)` — #1170's armed flag and
  #1187's settled history case, both working on the deployed artifact. The Monitor does not
  open empty (SD-5);
- `fleet live cases loaded: 1 case(s) with an accepted quote reach the gate`;
- 🔴 **no `Connection refused` warnings.** Energy's and procurement's healthy runs both log
  two of them — fleet PM overrides and fleet live cases failing soft against a database
  that is not there. This system **has** that database, so the absence of those two lines
  is the differential that distinguishes "DB-backed and connected" from "DB-less and
  degrading gracefully". A reader carrying the recorded healthy shape across from a
  DB-less system would have flagged their absence as a defect.

Connector log: tunnel ID **`c28103ab-e52a-47b2-8c8d-45b0315653dd`** — the tunnel Cray
created in s232, confirmed from the running system rather than from the record of its
creation — the expected non-fatal `cert.pem` ERR, and **four registered connections**
(sin14, bkk07, sin22, bkk07).

### 🔴 The keyed `/whoami` = 200 control — the check neither prior system could produce

Run from **inside** the container, because Cloudflare Access blocks automation at the edge
by design. Energy admits `/whoami` but is keyless; procurement does not admit the route at
all under a ruling that it serves anonymous read with no personas. Fleet is the first
published system where the check is both admitted and meaningful.

| Request | Result |
|---|---|
| `GET /whoami`, no credential | **401** `missing or malformed Authorization bearer API key` |
| `GET /whoami`, a persona's raw key | **200** `{"person_id":"req-mechanic-tom","display_name":"ต้อม — ช่างใหญ่ (ผู้ตั้งเรื่องเบิก)","auth_enabled":true}` |
| `GET /whoami`, a deliberately wrong key | **401** `unknown API key` |

**The third row is why the second one means anything.** A `200` alone is equally explained
by "the key is right" and by "authentication is off" — the same ambiguity a bare `302`
carries about an Access policy. A credential that is *present and wrong* being refused is
what excludes the second explanation. Same shape as the differential PIN test, applied to a
different gate.

It also settles the crossed-pair hazard **empirically** rather than by trusting that boot
would have refused: the digest in `API_KEYS` resolves to the same `person_id` that the raw
key in `UI_DEMO_PERSONA_KEYS` is offered under, so the persona card's name and the audit
trail's `person_id` cannot disagree.

Alongside it, on the same run: `/meta` served **three** personas in **authored** order
(`req-mechanic-tom` → `appr-fleet-manager-wirat` → `appr-owner` — the ladder read
bottom-up), `ui_published_views = ['A','C','F','H','I','J']` matching SD-3, `GET /runs`
returned both seeded runs, and `GET /audit/verify` returned
`{"intact":true,"rows_verified":4}` — the tamper-evident chain live and checkable, which is
the one read the trust story cannot be told without.

### Do-no-harm (Step 10 item 5) — against a baseline captured BEFORE the first action

| Container | Before | After |
|---|---|---|
| `oct-energy-app` | `Up 5 days (healthy)` | `Up 5 days (healthy)` |
| `oct-energy-cloudflared` | `Up 3 days` | `Up 3 days` |
| `oct-procurement-app` | `Up 4 days (healthy)` | `Up 4 days (healthy)` |
| `oct-procurement-cloudflared` | `Up 3 days` | `Up 3 days` |

Not one sibling restarted. Every `smb-*` co-tenant container remained `exited`, as it had
been for three weeks. **Skipping the host pull is what kept this cheap** — it was the only
step in the sequence that writes into a directory two running systems read from, and the
`deploy/` diff proved it would have changed nothing.

### ⚠️ Headroom — measured with three systems, and Step 9's projection is exceeded

| Container | Memory |
|---|---|
| `oct-energy-app` | 637.6 MiB |
| `oct-procurement-app` | 530.8 MiB |
| `oct-fleet-maintenance-app` | 88.8 MiB |
| `oct-fleet-maintenance-postgres` | 49.0 MiB |
| three connectors | 18.5 + 18.35 + 18.26 MiB |
| **total** | **≈1361 MiB ≈ 1.33 GiB** of 31.16 GiB available to the Docker VM |

Step 9 projected **≈0.95 GiB for three systems**. The measurement is **40% over** it.

🔴 **The overrun is not the third system, and reading it that way would be wrong.** At
s222 the same two app containers measured **208.9** and **85.4** MiB; they are now **637.6**
and **530.8**. Fleet's app, two minutes old, sits at **88.8** — almost exactly procurement's
28-minute figure. So the projection is not a bad number, it is a **cold** one: it models
containers at boot and steady state is several times that. s222's log already anticipated
the direction (*"its figure will rise with use"*) without folding it back into the
projection.

Consequence, stated plainly so system #4 does not rediscover it: **Step 9's method
under-models by roughly 3–6× per app container.** At 4.3% of available memory there is no
pressure today and this changes no decision — it changes what the projection should be
compared against next time.

### The edge, after the system is live — and what it can and cannot prove

Driven from a **script file**, per the runbook's own warning: a variable that fails to
expand in an inline loop sends every request to `/`, and you conclude you tested seven
things when you tested one.

Seven paths on `oct-fleet-maintenance.<DOMAIN>` — the six admitted ones (`/`, `/health`,
`/meta`, `/whoami`, `/query`, `/procedures`) plus one deliberately **excluded**
(`/demo/hero/governance`):

- **7/7 → `HTTP/2 302`**, every one with `location:` at
  `<team>.cloudflareaccess.com/cdn-cgi/access/login/oct-fleet-maintenance.<DOMAIN>` and
  `www-authenticate: Cloudflare-Access` present;
- **no `200` on any path** — that is the read that would have mattered, because a `200`
  means the gate is not applied and the demo is open;
- **no `530` stragglers** — propagation had completed, as it had in s232 and unlike s222's
  ~4-minute lag.

**A control neither prior bring-up recorded:** a live sibling (`oct-energy.<DOMAIN>/health`)
probed in the same second also returned `302` — but with a **different** `kid`/`aud`
(`392cf53f…` against fleet's `68313129…`) and its own hostname in the login URL. The two
systems therefore sit behind **separate Access applications**, not one policy spanning the
zone. Cheap, and it excludes a misconfiguration that a per-system `302` alone cannot.

🔴 **A correction to how this check is described, not to the check.** Runbook §9.1 says
that with the tunnel now live, `302` on every path *"proves Access is in front of a
**working** origin"*. **It does not, and s232's own evidence is the counterexample:** that
session measured `302` on 6/6 paths while fleet had **no origin at all** — no container, no
connector, nothing. Access intercepts before the request is ever routed to the tunnel, so
its `302` is origin-independent. What the edge check actually establishes is that the gate
still holds *after* the system was brought up — a no-regression read, which is worth taking.
**Origin health is proven by the in-container probe above, and only there.**

The excluded path returning `302` alongside the admitted ones is the same fact from the
other side: **the edge cannot distinguish an admitted route from a refused one**, because
Access gates the hostname and the policy's Path is empty. The allowlist is proven by the
offline `ingress rule` check in the first table, which is deterministic and needs no
account — not by anything observable from outside the gate.

## Corrections owed to the runbooks (applied in the same PR)

1. 🔴 **A backslashed Windows path does not survive the shell chain, and it fails as a
   missing file rather than as a quoting error.**
   `docs/runbooks/published-demo-redeploy.md` prescribes
   `ssh <host> docker compose -f C:\projects\vero-lite\deploy\published\…\docker-compose.yml …`.
   Measured today: driven from WSL through `ssh` into the host's PowerShell, **every
   backslash is stripped**, and the surviving argument is a *relative* path resolved against
   the SSH home directory:

   ```
   open C:\Users\…\projectsvero-litedeploypublishedoct-fleet-maintenancedocker-compose.yml:
   The system cannot find the file specified.
   ```

   The error names a plausible-looking absolute path, so it reads as "the file is missing"
   and sends you checking the host checkout — which is intact. **Use forward slashes**
   (`C:/projects/vero-lite/…`); Docker on Windows accepts them, and they cross every shell
   layer unchanged. Same family as Lesson #0007, one layer further out.
2. **A first bring-up needs the image shipped, and §9's narrative does not say so.**
   §7 documents the build-and-ship procedure, but the "bring it up" sequence — and every
   prose summary of it in the handoffs — goes straight from the schema step to `up -d`. On a
   system whose compose declares `build:` with no `image:`, that ordering fails on the
   deploy host. Noted at §9.1's head.

## Reference

- PLAN: [`docs/plans/0103-portal-landing-and-per-system-published-profiles.md`](../plans/0103-portal-landing-and-per-system-published-profiles.md) §Step 10, AC-10, AC-11.
- PLAN: [`docs/plans/0106-fleet-case-persistence-disclosure.md`](../plans/0106-fleet-case-persistence-disclosure.md) AC-7 — this record is its cited evidence.
- RoPA: [`docs/compliance/ropa-fleet-cases.md`](../compliance/ropa-fleet-cases.md) — AC-11's artifact, cited by path in "The go" above.
- ADRs: ADR-0035 D1(3) + OQ-6 (domain naming, open) · ADR-0036 D2 (the two-artifact price) ·
  ADR-0037 (this system's DB posture — engaged, unlike procurement's bring-up).
- **Cloudflare + host-secret evidence:** [`2026-08-15-fleet-cloudflare-artifacts-and-secrets-staging.md`](2026-08-15-fleet-cloudflare-artifacts-and-secrets-staging.md).
  Cited rather than restated, at that file's own instruction — a second copy would drift.
  The differential PIN test recorded there is **not re-run here**: the Access policy has not
  been touched since, and re-running it would prove nothing new.
- Runbook: [`docs/runbooks/published-demo-bring-up.md`](../runbooks/published-demo-bring-up.md) (corrected in the same PR).
- Sibling record: [`2026-08-11-plan0103-step10-procurement-bring-up.md`](2026-08-11-plan0103-step10-procurement-bring-up.md) — system #2, the shape this file follows.

AI-assisted (Claude Code, session 234); no `Co-Authored-By` per CLAUDE.md §7.
