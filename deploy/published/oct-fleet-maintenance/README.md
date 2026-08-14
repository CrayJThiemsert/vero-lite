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

### 4. `UI_DEMO_PERSONA_KEYS` — the picker's half of the same pair

The picker offers a card per persona and logs the visitor in with that persona's
**raw** key, so the raw side of every pair generated above goes here, as JSON
mapping `person_id` → raw key. Bare pass-through in the compose; **never** in
`published.env`.

🔴 **These keys are served to the browser.** That is the ruled credential path
(Cray, typed s224, option (a)): the cards cannot log anyone in otherwise. So
anyone can read the three keys out of `/meta` and drive the API directly as any
persona — the same power the cards grant, now stated rather than discovered.
Acceptable **only** because these three authenticate synthetic demo principals on
synthetic data. A key that authenticates anything real must never appear here.

Generate both halves together, so they cannot drift:

```bash
python - <<'PY'
import hashlib, json, secrets
people = ["req-mechanic-tom", "appr-fleet-manager-wirat", "appr-owner"]
raw = {p: secrets.token_urlsafe(32) for p in people}
print("export API_KEYS=" + json.dumps(
    {hashlib.sha256(k.encode()).hexdigest(): p for p, k in raw.items()}))
print("export UI_DEMO_PERSONA_KEYS=" + json.dumps(raw))
PY
```

**Boot refuses rather than degrades** if the two disagree — a digest missing from
`API_KEYS`, a **crossed pair** (one persona's raw key mapping to another's
`person_id`), or a `person_id` this vertical does not author. The crossed pair is
the one that earns the check: it logs in successfully, and the card would name one
persona while the audit trail recorded another — making the on-screen disclosure
("recorded in the audit trail under this name") false with nothing visibly wrong.

Leave it unset and Tab H falls back to the operator-key + free-text identity form,
which on a public surface asks a visitor for a key they do not have.

## Bring it up

⚠️ **Read the gate section above first.** Then:

```bash
docker compose -f deploy/published/oct-fleet-maintenance/docker-compose.yml up -d
```

### 🔴 The schema does NOT come with `up -d` — apply it first

_[✅ **ANSWERED s232.** This section was an open question deferred to Step 10.
RULED (Cray, typed, 2026-08-14): an **operator step**, with the skip made
**legible** rather than prevented by compose. Full procedure and the reasoning:
`docs/runbooks/published-demo-bring-up.md` §9.0 — read that, not a restatement.]_

```bash
docker compose -f deploy/published/oct-fleet-maintenance/docker-compose.yml up -d postgres
docker compose -f deploy/published/oct-fleet-maintenance/docker-compose.yml run --rm app alembic upgrade head
docker compose -f deploy/published/oct-fleet-maintenance/docker-compose.yml run --rm app alembic current
```

The third line is **evidence, not decoration** — its output goes in the go log,
and it is the only thing that distinguishes a migrated system from an unmigrated
one from outside.

⚠️ **Why the order matters, and why nothing downstream catches a miss.** On an
empty database this system **boots, passes its healthcheck, and opens its
tunnel** — `/health` is pure liveness and never touches Postgres, and
`cloudflared` gates only on `service_healthy`. It is reachable and looks correct.
**The first thing that fails is a visitor typing a case on Tab I**, which is this
system's whole point.

✅ **If the step is skipped, the boot log now says so at ERROR and names this
command** (`services/api/main.py::_is_schema_not_applied`, s232). That is a
backstop, not the plan — read the `alembic current` output.

_(Why not a compose `migrate` service that makes it un-skippable? Considered and
not taken: `depends_on: service_completed_successfully` appears nowhere in this
repo, and a gated one-shot host run is the wrong moment to debut an unmeasured
compose feature. The rejected option is recorded here so it is not re-proposed
without new information.)_

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

- ~~**Tab H's seed.** Step 7.~~ **SHIPPED s221; the flag was armed s232.** SD-5
  ruled (a) — seed one waiting run at boot **and** keep the visitor path, so the
  Monitor is never empty at the moment the demo must not look dead.
  `_seed_fleet_operate_demo` (`services/api/main.py`) carries **both** gates
  itself — the vertical check and `OCT_DEMO_SEED_OPERATE` — and AC-8 closed on
  it. `published.env` now pins `OCT_DEMO_SEED_OPERATE=true`.
  _[Corrected s232. This bullet said the seed "is not built", that `main.py`
  gates it on the *procurement* vertical, and that flipping the flag "would be a
  no-op that reads like a fix" — all true when written at Step 4b, all false from
  s221 onward. The pin itself carried the same stale claim and stayed `false` for
  eleven sessions because of it. **Nothing reads a comment or a README**, so ruff,
  mypy and the full suite were all silent. Read `published.env`'s own block for
  the fuller record.]_
- ~~**The persona picker UI.** Step 6.~~ **SHIPPED s224.** Tab H renders three
  persona cards on this profile — the authored ladder, in authored order, from
  `procedures.yaml`. Provisioning below; the code is `view-monitor.js`'s
  `personaPicker` behind `O.isPublished() && demoPersonas().length`.
- ~~**Card copy.** Step 8a.~~ **SHIPPED — AC-9 closed.** All three published
  profiles carry a `card-copy.md`, this one included. _[Corrected s232: this read
  "not yet written for **any** system", which was true at Step 4b and stopped
  being true when Step 8a landed.]_
- **The per-IP rate cap.** A Cloudflare **zone** rule with no file in this repo.
- **The domain.** ADR-0035 D1(3) — portal repo and DNS only, which is why
  `config.yml` carries no `hostname:` key.
- **`deploy.py` — and it does NOT block this system's bring-up.** ⚠️ The bullet
  here previously read as a Step-10 blocker; it is not one. That script is the
  **redeploy** tool ("the bring-up runbook stands the system up the FIRST time…
  none of that repeats"), it is pinned to system #1, and **procurement went live
  without it** — with the plain `docker compose … up -d` above, exactly as this
  README prescribes. Parameterizing it (vs copying per profile) is a real
  deferred decision, but it falls due at this system's **first redeploy**, not at
  its bring-up.
- 🔴 **A fleet-specific in-app disclosure (ADR-0037 D2.4)** — that typed case text
  is persisted, and for how long. **RULED (Cray, typed, 2026-08-14): fleet gets
  its own**, not a widening of the shared D6 prompt-log banner. Binding **before
  this system is reachable** (D2 obligations bind before reachability), and owned
  by its own PLAN. ⚠️ The existing published banner is **not** it: ADR-0037 D3
  refuses to widen D6, the two 90-day numbers are an independent coincidence the
  test suite actively guards against conflating, and that banner's *"read only by
  the operator"* clause is **false for case text on this profile** — Tab H shows
  visitor-opened cases to other visitors.
