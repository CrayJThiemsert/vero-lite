# `oct-fleet-maintenance` — published system #3, the approval story

PLAN-0103 Steps 4b + 5. The PLAN-0095 image behind a locally-managed `cloudflared`
tunnel, **no published ports** — and, uniquely among the published systems, **its
own Postgres**.

| File | What it is |
|---|---|
| `docker-compose.yml` | the three-service project — `app` + `postgres` + `cloudflared` |
| `published.env` | every pinned value. **Committed. No secrets.** |
| `cloudflared/config.yml` | the ingress **allowlist** — this file *is* the enforcement |

The compose project is named **`oct-fleet-maintenance`** — the same string as this
directory, the convention every profile follows and
`tests/deploy/test_published_profiles.py` enforces.

## 🔴 Bring-up is gated. Authoring is not.

**Authoring this profile is ungated** — ADR-0037 is Accepted, which is what makes
the per-system database posture legitimate.

**Bringing it up is gated, on two separate things:**

1. **AC-11 — the RoPA must cover this system's posture BEFORE it is reachable**
   (ADR-0037 D2.1). Tab I is visitor-writable and its free text persists to the
   Postgres below. The published demo's existing RoPA describes a **DB-less**
   system whose entire personal-data story is the prompt log, and whose erasure
   path is a content search over that log — which never reaches a case row. The
   RoPA is **Cray's artifact, in Cray's controller voice**; this PLAN gates on it
   and supplies the change statement, and authors none of the text. A bring-up
   without it is a **stop condition, not a warning**.
2. **Order and headroom.** SD-2 ruled bring-up order **procurement, then fleet**,
   and AC-10 requires MS-S1 headroom to be **measured and recorded** (Step 9)
   before any second system is stood up. Every bring-up has its own explicit
   Cray go (CLAUDE.md §8).

One sharp edge to hand Cray with the RoPA update: a case that drives a governed run
enters the **tamper-evident audit chain** — the structure whose erasure the demo
RoPA itself says cannot be promised. So the case-text DSR answer is structurally
different from the prompt log's, and only Cray can set it.

## What this deployment serves

`OCT_VERTICAL=fleet_maintenance`. Published tabs: **`A,C,F,H,I,J`, landing on A**
(SD-3, Cray typed s218).

This is the system that tells the **approval** story. It is the only published
system with **personas** (LOCKED-5) and the only one with a **database**
(LOCKED-1), and those two facts are why Tabs H, I and J appear here and nowhere
else. The governed hero belongs to the procurement system; the three OCT features
belong to energy. One system, one story.

The core moment: a visitor picks a persona, is **refused** an approval above their
tier as ต้อม (ช่างใหญ่ / requester), then is **granted** it as วิรัช
(ผจก.เดินรถ / approver) — with each decision landing in the real audit trail under
the `person_id` that acted. The principals are authored in
`verticals/fleet_maintenance/procedures.yaml`.

⚠️ **Tab A's content depends on five pinned recommender values, and inheriting the
defaults would break the landing view.** See `published.env` — the short version is
that `measured_value` here is a **฿ repair quote**, the real boundary is the
**฿5,000 DOA ceiling**, and at that threshold exactly **two** of five readings
breach and route to two *different* tiers, which is what makes the ladder visibly a
ladder. Under energy's default threshold all five would breach.

## The three things you must supply

All are **secrets** and none may ever be committed (CLAUDE.md §8).

### 1. Tunnel credentials

```bash
cloudflared tunnel create vero-oct-fleet-maintenance
```

```bash
export CLOUDFLARED_CREDENTIALS_FILE=/etc/vero/cloudflared-fleet-credentials.json
```

Use **this system's own** credentials file; sharing another system's would put two
systems on one tunnel.

### 2. `OCT_FLEET_DB_PASSWORD`

The database password. The compose file declares it **required with no default**,
in two places (the `postgres` service and the `DATABASE_URL` the app composes at
runtime), so a missing value fails the `up` loudly rather than starting a system
that cannot reach its own database.

```bash
export OCT_FLEET_DB_PASSWORD="$(python -c 'import secrets; print(secrets.token_urlsafe(24))')"
```

It is **not** committed even though the database publishes no port and lives on
this system's own network: this repo is public, and the database stores
visitor-typed personal data.

### 3. `API_KEYS` — and here it is not optional

`API_AUTH_ENABLED=true` is pinned and `API_KEYS` is deliberately absent from
`published.env`. On the other published systems an unset value is a defensible
posture. **On this one it is a broken demo** — with no keys, no persona can log in
and the refused-then-granted beat is unreachable.

Generate a key + digest pair per persona:

```bash
python -c "import secrets,hashlib; k=secrets.token_urlsafe(32); print('key:', k); print('sha256:', hashlib.sha256(k.encode()).hexdigest())"
```

Supply the digest→`person_id` mapping env-local on the host — a shell export, a
systemd drop-in, or a host-side env file **outside this repo**. Only the sha256
digest is ever stored; the raw key is what the visitor holds.

## Bring it up

⚠️ **Read the gate section above first.** Then:

```bash
docker compose -f deploy/published/oct-fleet-maintenance/docker-compose.yml up -d
```

🔴 **Open bring-up question, not answered by this profile: how does the database
get its schema?** The compose starts an empty Postgres, and nothing in this file
runs migrations. Whether that is an `alembic upgrade head` step, an init container,
or something else is **Step 10's** to settle against a deployment that has actually
run — it is deliberately not invented here. Do not assume `up -d` alone yields a
working system.

## Verifying the allowlist without an account

`cloudflared` can evaluate the committed ingress offline — no Cloudflare account,
fully deterministic.

⚠️ **`--config` goes on `tunnel`, BEFORE the subcommand — and getting it wrong
exits 0.** The trailing form validates **nothing** and still returns exit 0. Assert
on the **output text**, never on `$?`.

```bash
cloudflared tunnel --config deploy/published/oct-fleet-maintenance/cloudflared/config.yml ingress validate
```

```bash
cloudflared tunnel --config deploy/published/oct-fleet-maintenance/cloudflared/config.yml ingress rule https://example.invalid/demo/hero/governance
```

The second should report the **catch-all** rule — the hero is not this system's
story. A route that resolves to `http://app:8000` when it appears in this system's
excluded table is a leak.

If `cloudflared` is not installed, run the image this project already pins:

```bash
docker run --rm -v "$(pwd)/deploy/published/oct-fleet-maintenance/cloudflared":/etc/cloudflared:ro cloudflare/cloudflared:2025.8.1 tunnel --config /etc/cloudflared/config.yml ingress validate
```

## What is NOT here

- **Tab H's seed.** SD-5 ruled (a) — seed one waiting run at boot **and** keep the
  visitor path, so the Monitor is never empty at the moment the demo must not look
  dead. That seed is **Step 7** and is not built: `main.py` gates the existing
  operate-demo seed on the *procurement* vertical, so it does nothing here.
  `OCT_DEMO_SEED_OPERATE=false` is pinned so the flag means what it says.
  ⚠️ Flipping it alone would be a no-op that reads like a fix.
- **The persona picker UI.** Step 6. This profile pins the auth posture the picker
  needs; it does not ship the picker.
- **Card copy.** Step 8a — AC-3's fifth committed artifact, not yet written for
  **any** system.
- **The per-IP rate cap.** A Cloudflare **zone** rule with no file in this repo.
- **The domain.** ADR-0035 D1(3) — portal repo and DNS only, which is why
  `config.yml` carries no `hostname:` key.
- **`deploy.py`.** The redeploy script at `deploy/published/` is pinned to system
  #1 and is not parameterized (deferred to Step 10). This system will likely owe
  verification steps the DB-less ones do not — that is part of what Step 10 has to
  settle.
