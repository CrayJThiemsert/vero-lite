# `oct-energy` — published system #1, the OCT three-feature story

PLAN-0100 Step 8, moved into its own profile directory by PLAN-0103 Step 4a.
Brings up the public demo surface: the PLAN-0095 image behind a locally-managed
`cloudflared` tunnel, **no published ports**, **no Postgres**.

The compose project is named **`oct-energy`** — the same string as this directory,
which is the convention every profile follows and
`tests/deploy/test_published_profiles.py` enforces.

## ⚠️ Migration — if this system is already running as `vero-published`

PLAN-0103 Step 4b renamed the project, both container names and the prompt-log
volume from the `vero-published-*` family to `oct-energy-*`, so that a second
published system cannot land in the same compose project or on the same Docker
network (AC-4). **Docker does not follow a rename.** A host still running the old
project will keep it running, untouched and invisible to every command in the
runbooks — including
[`published-demo-operations.md`](../../../docs/runbooks/published-demo-operations.md)'s
**erasure paths**, which would then report success while addressing nothing.

🔴 **The prompt-log volume carries personal data under a 90-day retention promise**
(`docs/compliance/ropa-published-demo.md`). Renaming the volume does not move the
rows: a plain `up` under the new name starts with an **empty** log and orphans the
old one. Migrate the data, do not just re-`up`.

This is a **host-state change** and needs Cray's explicit go before it runs
(CLAUDE.md §8). Sketch, to be confirmed against the host's actual state first:

```bash
docker compose -p vero-published ps                      # is the old project real?
docker volume ls | grep prompt-log                       # which volumes exist
```

```bash
docker compose -p vero-published down                    # stop the old project
docker volume create oct-energy-prompt-log
docker run --rm -v vero-published-prompt-log:/from -v oct-energy-prompt-log:/to alpine sh -c "cp -a /from/. /to/"
```

Verify the row count matches on both sides **before** removing the old volume, and
record the migration in the operations runbook's log — the retention clock is a
commitment to a data subject, not an implementation detail.

| File | What it is |
|---|---|
| `docker-compose.yml` | the two-service project — `app` + `cloudflared` |
| `published.env` | every value §Pinned values pins. **Committed. No secrets.** |
| `cloudflared/config.yml` | the ingress **allowlist** — this file *is* the enforcement |

## What this deployment serves

`OCT_VERTICAL=energy` — one process serves exactly one vertical, so this project is
the **energy system**. A second vertical is a second compose project, not a setting
change. Tab G (the governed hero) is **not** registered here: the hero is bespoke
per design partner (ADR-0032 D1.2) and energy owns no hero builder.

## The two things you must supply

Both are **secrets** and neither may ever be committed (CLAUDE.md §8).

### 1. Tunnel credentials

Create the tunnel once, then point the compose at its credentials JSON:

```bash
cloudflared tunnel create vero-oct-published
```

```bash
export CLOUDFLARED_CREDENTIALS_FILE=/etc/vero/cloudflared-credentials.json
```

The compose declares this variable **required**, with no default — a missing value
fails `up` loudly rather than mounting something unintended.

⚠️ **Do not replace this with a `TUNNEL_TOKEN` remotely-managed tunnel.** That moves
the ingress map into the Cloudflare dashboard, out of this repo, and silently voids
AC-6(a): the offline test would keep passing against a file the running tunnel no
longer reads.

### 2. `API_KEYS`

`API_AUTH_ENABLED=true` is pinned, and `API_KEYS` is deliberately **absent** from
`published.env`. Until you supply it the demo boots and serves every unkeyed route,
but **nobody can log in** — keyless `/whoami` returns 401, which is the correct
behaviour, not a fault.

Generate a key + digest pair:

```bash
python -c "import secrets,hashlib; k=secrets.token_urlsafe(32); print('key:', k); print('sha256:', hashlib.sha256(k.encode()).hexdigest())"
```

Supply the mapping env-local on the host — a shell export, a systemd drop-in, or a
host-side env file **outside this repo**. The RAW key is what the operator types to
log in; only the sha256 digest is ever stored.

## Bring it up

```bash
docker compose -f deploy/published/oct-energy/docker-compose.yml up -d
```

## Verifying the allowlist without an account

`cloudflared` can evaluate the committed ingress offline — no Cloudflare account,
fully deterministic. This is Step 9's sanctioned fallback when no tunnel can be
established:

⚠️ **`--config` goes on `tunnel`, BEFORE the subcommand — and getting it wrong
exits 0.** Measured 2026-08-06 (Step 9) on `cloudflared 2025.8.1`: the trailing
form `tunnel ingress validate --config F` prints `Incorrect Usage: flag provided
but not defined: -config`, validates **nothing**, and still returns **exit 0**. A
runner that trusts the exit code records a PASS for a command that never ran.
Assert on the **output text** (`OK`, or the `service:` line), never on `$?`.

```bash
cloudflared tunnel --config deploy/published/oct-energy/cloudflared/config.yml ingress validate
```

```bash
cloudflared tunnel --config deploy/published/oct-energy/cloudflared/config.yml ingress rule https://example.invalid/insights/query
```

The second should report the **catch-all** rule. A route that resolves to
`http://app:8000` when it appears in PLAN-0100's *excluded* table is a leak.

### If `cloudflared` is not installed on the host

It was not on the Legion dev box at Step 9, and installing it is a host-state
change (CLAUDE.md §8). Run the **image this project already pins** instead — no
install, nothing left behind, and it is by construction the same binary the
`cloudflared` service runs:

```bash
docker run --rm -v "$(pwd)/deploy/published/oct-energy/cloudflared":/etc/cloudflared:ro cloudflare/cloudflared:2025.8.1 tunnel --config /etc/cloudflared/config.yml ingress validate
```

Mount read-only, as above: the evaluation must never be able to edit the file it
is evaluating.

## What is NOT here

- **The per-IP rate cap.** It is a Cloudflare **zone** rule (SD-3) with no file in
  this repo, so no test here can close it. Its configured values are recorded in
  Step 8's PR body.
- **The domain.** ADR-0035 D1(3): the domain appears only in the portal repo's
  cross-system ingress map and in DNS. Nothing in vero-lite may reference it — which
  is why `config.yml` carries no `hostname:` key.
- **Postgres.** SD-1's DB-less ruling. The routes that need a database are on the
  excluded table; the boot-time projection reads are fail-soft and log what they
  could not load rather than pretending nothing was there.
