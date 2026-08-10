# `oct-procurement` — published system #2, the governed hero

PLAN-0103 Steps 4b + 5. Brings up the public procurement surface: the PLAN-0095
image behind a locally-managed `cloudflared` tunnel, **no published ports**,
**no Postgres**.

| File | What it is |
|---|---|
| `docker-compose.yml` | the two-service project — `app` + `cloudflared` |
| `published.env` | every pinned value. **Committed. No secrets.** |
| `cloudflared/config.yml` | the ingress **allowlist** — this file *is* the enforcement |

The compose project is named **`oct-procurement`** — the same string as this
directory, which is the convention every profile follows and
`tests/deploy/test_published_profiles.py` enforces.

## What this deployment serves

`OCT_VERTICAL=procurement` — one process serves exactly one vertical, so this
project is the **procurement system**. A second vertical is a second compose
project, not a setting change.

Published tabs: **`G,F`, landing on G** (SD-3/SD-4 joint ruling, Cray, typed s218).

- **Tab G — the governed hero.** This system's story, and the reason it exists.
  Procurement is the vertical that owns the hero builders
  (`verticals/procurement/hero_demo/`); energy's system denies these two reads at
  its edge precisely because the hero is bespoke per design partner
  (ADR-0032 D1.2).
- **Tab F — Procedures.** The ladder the governance narrative refers to, readable.

⚠️ **The landing tab is G and not A on purpose.** Tab A is structurally blank on
this vertical — the registered adapter is `FastenalCsvAdapter`, whose
`stream_events` is an empty async iterator by design
(`verticals/procurement/data_adapter/fastenal_csv.py:248-251`). Landing a cold
visitor on an empty map is the one first impression this surface cannot afford.

## No personas, and therefore no login

SD-3/SD-4 ruled this system **"anonymous read + hero, no personas"**, so
`^/whoami$` is **off** the allowlist and `API_KEYS` is not expected to be
provisioned here at all. `API_AUTH_ENABLED=true` stays pinned as the fail-closed
direction: with auth on and no keys, every keyed route refuses; turning it off
would open them.

Read `cloudflared/config.yml`'s header before changing this — the reasoning is
there, including the one UI question it deliberately leaves open (Tab G's "Act"
card still renders a login form on a system that will always refuse it; that is
Step 6's and ultimately Cray's call).

## The one thing you must supply

Only the **tunnel credentials** — unlike the other profiles, no `API_KEYS`.

```bash
cloudflared tunnel create vero-oct-procurement
```

```bash
export CLOUDFLARED_CREDENTIALS_FILE=/etc/vero/cloudflared-procurement-credentials.json
```

The compose declares this variable **required**, with no default — a missing value
fails `up` loudly rather than mounting something unintended. Use **this system's
own** credentials file; sharing energy's would put two systems on one tunnel.

⚠️ **Do not replace this with a `TUNNEL_TOKEN` remotely-managed tunnel.** That
moves the ingress map into the Cloudflare dashboard, out of this repo, and
silently voids the allowlist guard.

## Bring it up

```bash
docker compose -f deploy/published/oct-procurement/docker-compose.yml up -d
```

⚠️ **Bring-up is a host-state change and needs Cray's explicit go** (CLAUDE.md §8),
and SD-2 ruled the order: **procurement first, then fleet**. AC-10 additionally
requires MS-S1 headroom to be measured and recorded *before* any second system is
stood up.

## Verifying the allowlist without an account

`cloudflared` can evaluate the committed ingress offline — no Cloudflare account,
fully deterministic.

⚠️ **`--config` goes on `tunnel`, BEFORE the subcommand — and getting it wrong
exits 0.** The trailing form `tunnel ingress validate --config F` prints
`Incorrect Usage`, validates **nothing**, and still returns exit 0. Assert on the
**output text**, never on `$?`.

```bash
cloudflared tunnel --config deploy/published/oct-procurement/cloudflared/config.yml ingress validate
```

```bash
cloudflared tunnel --config deploy/published/oct-procurement/cloudflared/config.yml ingress rule https://example.invalid/whoami
```

The second should report the **catch-all** rule — `/whoami` is excluded on this
system. A route that resolves to `http://app:8000` when it appears in this
system's excluded table is a leak.

If `cloudflared` is not installed, run the image this project already pins (no
install, nothing left behind, and by construction the same binary the service
runs):

```bash
docker run --rm -v "$(pwd)/deploy/published/oct-procurement/cloudflared":/etc/cloudflared:ro cloudflare/cloudflared:2025.8.1 tunnel --config /etc/cloudflared/config.yml ingress validate
```

## What is NOT here

- **Postgres.** LOCKED-1 keeps this system DB-less, and SD-3 turned that from a
  preference into the reason Tab H is off the published set: H's backing run is
  written through `async_session`, so H is **storage-blocked, not
  persona-blocked**. It returns only if Cray revises LOCKED-1.
- **The operate-demo seed.** `OCT_DEMO_SEED_OPERATE=false`, and this is the system
  where that pin does real work — `main.py:348` gates the seed on the
  *procurement* vertical.
- **The per-IP rate cap.** A Cloudflare **zone** rule with no file in this repo,
  so no test here can close it. It is also the only thing bounding the anonymous
  procedure run behind `/demo/hero/governance?live=true` — see the allowlist
  header.
- **The domain.** ADR-0035 D1(3): it appears only in the portal repo and in DNS,
  which is why `config.yml` carries no `hostname:` key.
- **`deploy.py`.** The redeploy script at `deploy/published/` is pinned to system
  #1 and is not parameterized by system (deferred to PLAN-0103 Step 10, Cray typed
  s219). Bring this one up with the plain `docker compose` command above.
