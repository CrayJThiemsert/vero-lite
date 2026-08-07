# Runbook — standing the published OCT demo up for the first time

> **Scope.** The one-time bring-up: creating the tunnel, binding a subdomain, putting
> the Access gate and the rate cap in front of it, getting the image onto the deploy
> host and starting the project. Ends where
> [`published-demo-operations.md`](published-demo-operations.md) begins — that one owns
> the steady state (prompt-log deletion, teardown, the Phase-5 protocol).
>
> **Written for ADR-0035 + ADR-0036, executed by PLAN-0100 Step 11.** Everything here is
> a *prerequisite* of Step 11, not Step 11 itself: Step 11 is the measured live run with
> its pass/fail reads fixed in advance, and it does not start until this runbook has
> finished and every offline AC is green.
>
> **Not vertical-specific by accident.** System #1 is the **energy** instance. A second
> vertical is a second compose project with its own tunnel, its own subdomain and its own
> Access policy (ADR-0036 D2) — this runbook is written so it can be re-run for it, and
> the places where "one system" assumptions are baked in are called out as such.

---

## 0. The standing gate, and the one rule about this file

**Every command that touches MS-S1 — deploying onto it, warming a model, any SSH — is a
host-state action and needs Cray's explicit go, every time** (CLAUDE.md §8). Nothing here
is pre-authorised by being written down.

🔴 **This file must never contain the domain, the team name, the account ID, an API key,
a tunnel token, or a credentials path that resolves to a real secret.** ADR-0035 D1(3)
puts the domain in exactly one layer — DNS at the vendor plus the portal repo's ingress
map — and states that *"nothing in this repo may reference the portal domain"*. That is
what keeps a domain change a DNS re-point rather than a code change (L6). The
placeholders below are load-bearing, and
`tests/deploy/test_published_compose.py::test_no_unknown_domain_appears_in_the_deploy_docs`
fails the build if a real one arrives.

### Fill these in locally — never commit them

| Placeholder | What it is | Where it may live |
|---|---|---|
| `<DOMAIN>` | the apex domain on Cloudflare | DNS + the Access policy only |
| `<SUBDOMAIN>` | `oct-energy.<DOMAIN>` — the label is fixed by ADR-0036 D2 (`oct-<vertical-id>`, `_`→`-`) | DNS + the Access policy only |
| `<TEAM>` | the Zero Trust team name (`<TEAM>.cloudflareaccess.com`) | Cloudflare only |
| `<CRED_PATH>` | absolute path to the tunnel credentials JSON **on the deploy host**, outside any git worktree | the host's `deploy/published/.env` |

---

## 1. Preconditions — confirm, do not assume

ADR-0035 records several of these as `[ext]` facts, which means **re-confirm on first
touch rather than trusting the last write-up** (`0035:292-317`). Session 213 confirmed the
list below; a later reader should re-run the checks, not copy the answers.

| # | Precondition | How to check |
|---|---|---|
| 1 | the apex domain is on Cloudflare nameservers | `Resolve-DnsName -Name <DOMAIN> -Type NS` → `*.ns.cloudflare.com` |
| 2 | a Zero Trust team exists | `one.dash.cloudflare.com` → Settings shows a team name; a "choose a team name" screen means it does not |
| 3 | a **rate limiting rule slot is free** | zone → Security → Security rules → the *Rate limiting rules* card shows `n/N rules` |
| 4 | the tunnel name `vero-oct-published` is not taken | Zero Trust → Networks → Tunnels & Mesh |
| 5 | `<SUBDOMAIN>` is not already a DNS record | zone → DNS → Records |
| 6 | the deploy host has `git` and `docker compose` | `ssh <host> 'git --version; docker compose version'` |
| 7 | the deploy host runs the Ollama the app will call | see §6; `OLLAMA_HOST` is pinned to `host.docker.internal`, which resolves to the **deploy host itself** |

🔴 **Precondition 7 is the one that silently produces a working-looking demo.** The
published compose pins `OLLAMA_HOST=http://host.docker.internal:11434`. That is correct
only when the compose runs on the same machine as Ollama. Bring it up anywhere else and
every LLM call fails to connect and degrades to the deterministic arm — disclosed, per
PLAN-0093, but a visitor sees a demo that never uses the model.

---

## 2. Decisions to make **before** touching the account

Each one is expensive to reverse after the fact. Stop here until they are typed.

### 2.1 The per-IP rate cap value

PLAN-0100 `§Pinned values` still reads *"needs Cray's nod"* — the drafted 10 req/10 s is
about 6× the ADR's recommended sustained rate, raised from an initial 2/10 s. Step 11's
case 6 measures against *"the pinned threshold"*, so the number has to exist before the
rule does.

### 2.2 The rate rule's **scope** — and why the slot count forces the question

On the free plan a zone gets **one** rate limiting rule. One zone hosts every system
(ADR-0036 D2: one subdomain per system, one zone). So the single rule is a shared
resource and its expression decides who is covered:

| Expression | System #1 | System #2 onwards |
|---|---|---|
| hostname **and** path (`<SUBDOMAIN>` + `/query`) | capped | **not capped** — PLAN-0100 `§Residual risks` predicted exactly this |
| path only (`/query`, any hostname) | capped | **also capped by the same rule** — but one visitor IP spends a single budget across all systems |

Neither is obviously right; the second trades semantics for coverage. Decide now, because
the only later remedies are "delete the rule and rewrite it" or "pay for a plan with more
rules". PLAN-0100 also leaves open whether the free plan's expression editor accepts a
path-only form at all — settle that when the rule is created and record the answer.

### 2.3 `tunnel:` by name or by UUID

`deploy/published/cloudflared/config.yml` declares `tunnel: vero-oct-published` — a
**name**. cloudflared resolves a name through the account origin certificate
(`~/.cloudflared/cert.pem`), which lives on whichever machine ran `tunnel login` and is
**not** normally on the deploy host.

* **Name** — keeps the file readable, but the deploy host then needs `cert.pem`, which
  grants account-wide authority rather than one tunnel's.
* **UUID** — the run is cert-free and the credentials file can be matched to the config
  offline (`verify_tunnel_credentials.py` cross-checks it). Costs a small PR to change the
  committed file.

This is a prediction, not a measurement: nobody has yet run the tunnel from a host with no
`cert.pem`. **Prove it before deciding** — §5 says how.

---

## 3. Create the tunnel

Run these wherever a browser is available. The tunnel belongs to the **account**, not to
the machine, so creating it on a workstation and copying the credentials to the deploy
host is normal and avoids installing `cloudflared` on the deploy host at all.

```bash
cloudflared tunnel login
```

Pick the zone in the browser. This writes `~/.cloudflared/cert.pem` — account-wide
authority. Keep it on the workstation; §2.3 is the decision about whether it ever needs to
travel.

```bash
cloudflared tunnel create vero-oct-published
```

🔴 **The name must be exactly `vero-oct-published`** — `config.yml` pins it. A different
name means editing a committed file, which is a PR, not a workaround.

The command prints the path of a new `<UUID>.json`. That file is the tunnel's credentials
and it is a **secret**: never commit it, never paste it into a chat or a ticket.

---

## 4. Verify the credentials — before they travel, and again after

```bash
python3 deploy/published/verify_tunnel_credentials.py <CRED_PATH> deploy/published/cloudflared/config.yml
```

Everything it prints is safe to share: shapes, lengths, PASS/FAIL and a SHA-256
fingerprint. The secret is never echoed.

**Run it on both machines and compare the `fingerprint` line.** Equal fingerprints prove
the copy arrived byte-identical. A truncated or newline-mangled copy shows up here rather
than as a mystery at `docker compose up` — which is the failure mode worth spending two
minutes to exclude, because the tunnel's error for a corrupt credentials file is not
obviously about the file.

Copy it to the deploy host outside any git worktree — the verifier's first check refuses a
path inside one, because a credentials file in the repo is one `git add -A` away from a
public commit.

---

## 5. Prove the tunnel can actually run

Two checks, in this order. The first is offline and free; the second is the only real test.

```bash
cloudflared tunnel --config deploy/published/cloudflared/config.yml ingress validate
```

⚠️ **`--config` goes on `tunnel`, before the subcommand.** The trailing form
`tunnel ingress validate --config F` prints `Incorrect Usage`, validates nothing, and
**still exits 0** (measured on 2025.8.1). Judge this on the output text — `OK` — never on
`$?`. If `cloudflared` is not installed, run the image the compose already pins; see
`deploy/published/README.md`.

Then run the tunnel **on the deploy host**, which is where §2.3's prediction is settled: a
name-form config with no `cert.pem` either resolves or it does not, and that is a fact
about that host, not about the config file.

---

## 6. Route the subdomain, gate it, cap it

```bash
cloudflared tunnel route dns vero-oct-published <SUBDOMAIN>
```

`config.yml` deliberately carries **no `hostname:` key** (D1(3)), so the DNS route is the
only thing that binds this subdomain to this system. A rule without `hostname` matches any
host, which is correct: the tunnel only ever receives traffic for the hostname its own
route points at.

**Access policy** — Zero Trust → Access → Applications → add a self-hosted application for
`<SUBDOMAIN>`, policy = allow, with an **email allowlist** and **one-time PIN** as the
login method (ADR-0035 D3, ratified). One-time PIN is built in; no external identity
provider is required.

Two consequences worth stating to whoever asks for the link:

* visitors cannot simply click through — each visit needs a PIN delivered to an allowlisted
  address, so **the addresses have to be collected in advance**;
* those addresses become **personal data processed at the vendor** (`0035:401-405`), and the
  free plan has a seat limit.

**Rate limiting rule** — zone → Security → Security rules → Rate limiting rules, using the
value from §2.1 and the scope from §2.2. There is no file for this in the repo, so no test
can close it; PLAN-0100 requires a **screenshot of the configured rule** as the closeout
artifact.

On the free plan the block response carries Cloudflare branding. That is a known,
accepted cost recorded in PLAN-0100's residual risks, not a defect to chase.

---

## 7. Get the source onto the deploy host

The published compose builds the app from source (`build: context: ../..`) and declares no
`image:`, so the deploy host needs a checkout. The repository is public, so a clone needs
no credentials.

```bash
ssh <host> 'powershell -NoProfile -Command -' < deploy.ps1
```

Drive it from a script file rather than an inline command: a `$` inside an inlined
`ssh … "…"` is eaten by the intervening shells and vanishes with no error. The script does
the clone-or-pull and then the bring-up:

```powershell
$root = "C:\projects\vero-lite"
if (-not (Test-Path $root)) {
  git clone https://github.com/CrayJThiemsert/vero-lite.git $root
}
Set-Location $root
git pull --ff-only
docker compose -f deploy/published/docker-compose.yml up -d --build
```

⚠️ **The image that runs is built on the deploy host, not the one tested on the
workstation.** Same Dockerfile and same commit, so it should be identical — but that is an
expectation, not a proof. When "the tested artifact is the shipped artifact" starts to
matter (a paying pilot, an incident), switch to a registry or a `docker save`/`load`; the
compose accepts an `image:` alongside `build:`, and `up` skips the build when that image is
already present, so the switch does not disturb the topology.

---

## 8. Host-side secrets

Neither value may enter the repo. Both live in an uncommitted `deploy/published/.env` next
to the compose file on the deploy host:

```
CLOUDFLARED_CREDENTIALS_FILE=<CRED_PATH>
API_KEYS={"<sha256-hex>": "<person-id>"}
```

Generate the key and its digest:

```bash
python -c "import secrets,hashlib; k=secrets.token_urlsafe(32); print('key:', k); print('sha256:', hashlib.sha256(k.encode()).hexdigest())"
```

The **raw key** is what an operator types to log in; only the digest is ever stored.

The `<person-id>` need not exist as an authored principal: `services/api/auth.py` resolves
the vertical's principal set and, when that vertical ships none, returns an authenticated
context with no `Person` attached rather than a 403. The energy vertical ships no
`principals` block, so any identifier works there. **A vertical that does declare
principals will 403 an unknown id**, so a second system must use one of its own.

Without `API_KEYS` the demo boots, serves every unkeyed route, and returns 401 from
`/whoami`. That is the documented, correct state — not a fault — which is why the compose
passes the variable through optionally rather than requiring it.

---

## 9. Bring it up, then hand over to Step 11

```bash
docker compose -f deploy/published/docker-compose.yml up -d
```

```bash
docker compose -p vero-published ps
```

Both services `running`/`healthy`, **no `postgres` service**, and **no published host
port** on anything. That is PLAN-0100's Step 11 case 0, and it gates every other case: if
`app` is not up, the downstream cases are void rather than passing.

From here the measured run is Step 11's, against pass/fail reads fixed **before** it
starts. Do not improvise them at the console — that is precisely what the fixed-in-advance
rule exists to prevent.

---

## 10. Changing the domain later

Cheap by construction, and worth keeping cheap.

1. add the new zone to Cloudflare and point its nameservers;
2. `cloudflared tunnel route dns vero-oct-published <NEW-SUBDOMAIN>`;
3. re-point the Access policy at the new hostname;
4. re-create the rate limiting rule if its expression names the old hostname (§2.2);
5. delete the old DNS record.

**No application change, no image rebuild, no redeploy.** The tunnel, the credentials, the
ingress allowlist and the container are all domain-ignorant. If a future step ever requires
editing something under `deploy/` or `services/` to change domains, that is the drift
`test_no_ingress_rule_binds_a_hostname` exists to catch — fix the leak rather than the
symptom.

---

## 11. Rollback

Fastest kill, in order of blast radius:

* **cut the public link** — stop the `cloudflared` service; the app keeps running and
  nothing external can reach it;
* **revoke one visitor** — remove the address from the Access allowlist;
* **revoke everyone** — delete the Access application;
* **remove the route** — delete the DNS record; the hostname stops resolving to the tunnel;
* **destroy the tunnel** — `cloudflared tunnel delete vero-oct-published`, which
  invalidates the credentials file everywhere it has been copied.

Teardown of the deployment itself, and the prompt-log obligations that survive it, belong
to [`published-demo-operations.md`](published-demo-operations.md).

---

*Sources: ADR-0035 (D1 exposure model, D3 Access, D6 prompt log), ADR-0036 (D2 subdomain
convention), PLAN-0100 (Step 8 artifacts, Step 11 protocol, §Pinned values, §Residual
risks), `deploy/published/README.md`. Preconditions were confirmed against the live
account in session 213; re-confirm rather than trusting that record.*
