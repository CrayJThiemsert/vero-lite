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
| `<CRED_PATH>` | absolute path to the tunnel credentials JSON **on the deploy host**, outside any git worktree | the host's `deploy/published/oct-energy/.env` |

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

### 2.3 `tunnel:` by name or by UUID — SETTLED, keep the name

**Not a decision any more.** This section previously predicted that
`tunnel: vero-oct-published` — a **name** rather than a UUID — would need the account
origin certificate (`cert.pem`) on the deploy host, and told you to prove it before
choosing. It was proved on 2026-08-07, and **the prediction was wrong in the safe
direction**: the name form works with the credentials file alone.

Measured, from the deploy host's own connector log:

```
INF Starting tunnel tunnelID=91339db6-…
ERR Cannot determine default origin certificate path. No file cert.pem in […]
INF Tunnel connection … ip=198.41.200.33
```

cloudflared reads the TunnelID out of the **credentials file**; the missing-cert line is
logged at ERR but is **not fatal**, and the connector goes on to register with the edge.

So: **keep `tunnel: <name>` and keep `cert.pem` on the workstation.** That is the safer
end state — `cert.pem` carries account-wide authority (it can create and delete tunnels
and DNS records), and nothing on the deploy host needs it.

One consequence to keep in view: `verify_tunnel_credentials.py` will always report
`config tunnel: matches credentials — FAIL` while the config names the tunnel, because a
name cannot be matched to a UUID offline. **That single FAIL is expected**; treat any
*other* FAIL as real.

---

## 3. Create the tunnel

**Run these on a machine with a browser — NOT on the deploy host.** `login` needs one, and
the tunnel belongs to the **account**, not the machine, so creating it on a workstation and
copying only the credentials onward is normal.

⚠️ **`cloudflared` is not installed on either machine, and installing it on the deploy host
would be a CLAUDE.md §8 host-state change.** It does not have to be: the commands below run
the **same pinned image the compose file already uses**, so nothing is installed anywhere.
(A single static binary from Cloudflare's releases works too — pick the version the compose
pins so the tool and the runtime agree.)

Three flags carry the whole thing, and each was learned by getting it wrong first:

| flag | why |
|---|---|
| `-v "$HOME/.cloudflared":/.cloudflared` | `--user <uid>` names a uid that is **not in the image's passwd**, so `HOME` falls back to `/` and cloudflared's default config dir becomes `/.cloudflared` — root-owned. Mount **where it will actually write**. `--origincert` sets where the *cert* goes; it does **not** move the config dir. |
| `-w /.cloudflared` | `login` also writes a temporary `cloudflared_priv.pem` into the **current directory**, and the image's `WorkingDir` (`/home/nonroot`) is not writable by that uid. |
| `--user 1000:1000` | so the files land owned by you rather than root. Substitute your own `id -u`/`id -g`. |

`docker image inspect <image> --format "{{.Config.WorkingDir}} {{.Config.User}}"` answers
both of the first two in one command — worth running before forcing `--user` on any image.

```bash
mkdir -p ~/.cloudflared
```

```bash
docker run --rm -it --user 1000:1000 -w /.cloudflared -v "$HOME/.cloudflared":/.cloudflared cloudflare/cloudflared:2025.8.1 tunnel --origincert /.cloudflared/cert.pem login
```

In a container it cannot open a browser, so it **prints a URL**; open that, pick the zone,
and `cert.pem` lands in `~/.cloudflared/`. That file is **account-wide authority** — keep it
on the workstation and do not copy it onward (§2.3).

```bash
docker run --rm --user 1000:1000 -w /.cloudflared -v "$HOME/.cloudflared":/.cloudflared cloudflare/cloudflared:2025.8.1 tunnel --origincert /.cloudflared/cert.pem create vero-oct-published
```

🔴 **The name must be exactly `vero-oct-published`** — `config.yml` pins it. A different
name means editing a committed file, which is a PR, not a workaround.

The command prints the UUID and writes `~/.cloudflared/<UUID>.json`. **That** file is the
tunnel's credentials and it is the secret that travels: never commit it, never paste it
into a chat or a ticket. A leftover `cloudflared_priv.pem` is a login temp file and can be
deleted.

---

## 4. Verify the credentials — before they travel, and again after

```bash
python3 deploy/published/verify_tunnel_credentials.py <CRED_PATH> deploy/published/oct-energy/cloudflared/config.yml
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

Offline, free, and worth running **on the deploy host** rather than the workstation — it
proves that machine can read the mounted config, which is the half that actually varies:

```bash
docker run --rm -v <REPO>/deploy/published/oct-energy/cloudflared:/etc/cloudflared:ro cloudflare/cloudflared:2025.8.1 tunnel --config /etc/cloudflared/config.yml ingress validate
```

Expect the literal word **`OK`**. Swap `ingress validate` for
`ingress rule https://example.invalid/<path>` to check any single route: an allowed one
answers `service: http://app:8000`, an excluded one `service: http_status:404`. Probing one
of each is worth the extra ten seconds — it shows the config *discriminates* rather than
merely parsing.

⚠️ **`--config` goes on `tunnel`, before the subcommand.** The trailing form
`tunnel ingress validate --config F` prints `Incorrect Usage`, validates nothing, and
**still exits 0** (measured on 2025.8.1). Judge this on the output text, never on `$?`.

⚠️ **Getting the pinned image onto the deploy host may not be a `docker pull`.** On a
Windows host driven over SSH, Docker Desktop's credential helper needs an interactive
desktop session and fails with *"A specified logon session does not exist"* — even for an
anonymous pull of a public image, and even when a console session is signed in. If that
bites, `docker save` the image on the workstation, `scp` the tar, and `docker load` it;
the same route works for the app image (§7).

---

## 6. Route the subdomain, gate it, cap it

🔴 **Order matters, and the hazard is easy to miss.** The DNS route below makes the
hostname **live immediately**. While the tunnel is stopped a visitor gets a harmless `530`
— but the moment §9 starts it, the demo is reachable by anyone who knows the name. **Create
the Access policy before bringing anything up.** Doing it in this order also buys a free
check: Access answers `302` *before* the request ever reaches the tunnel, so you can prove
the gate works while the demo is still switched off.

```bash
docker run --rm --user 1000:1000 -w /.cloudflared -v "$HOME/.cloudflared":/.cloudflared cloudflare/cloudflared:2025.8.1 tunnel --origincert /.cloudflared/cert.pem route dns vero-oct-published <SUBDOMAIN>
```

`config.yml` deliberately carries **no `hostname:` key** (D1(3)), so the DNS route is the
only thing that binds this subdomain to this system. A rule without `hostname` matches any
host, which is correct: the tunnel only ever receives traffic for the hostname its own
route points at.

### Access policy (ADR-0035 D3, ratified)

**Zero Trust → Access controls → Applications → Create new application → Self-hosted and
private → Public DNS.** (Login methods live under **Integrations → Identity providers**;
One-time PIN is there by default and no external IdP is needed.)

| field | value |
|---|---|
| Application name | e.g. `vero-oct-<vertical>` |
| Session Duration | 24 hours — one PIN covers a day of demoing |
| Subdomain / Domain | the `oct-<vertical-id>` label and the apex |
| Path | empty — gate the whole host |
| Policy Action | **Allow** |
| Policy Include | **Emails** (or *Emails ending in* for a whole partner org) |

🔴 **Never set the policy to "All authenticated users" or "Everyone".** With One-time PIN as
the login method, "authenticated" means *anyone who can receive mail at any address they
type* — that is an open door wearing a lock.

Two consequences worth stating to whoever asks for the link:

* visitors cannot simply click through — each visit needs a PIN delivered to an allowlisted
  address, so **the addresses have to be collected in advance**;
* those addresses become **personal data processed at the vendor** (`0035:401-405`), and the
  free plan has a seat limit.

**Verify before going further** — this works with the tunnel still stopped:

```bash
curl -sS -o /dev/null -D - https://<SUBDOMAIN>/health
```

`302` with a `location:` at `<TEAM>.cloudflareaccess.com` means the gate is live. A `530`
means Access is **not** applied and the request went straight through to the tunnel.

### 🔴 Access also blocks automation — and that collides with Step 11

Access gates every client, not just browsers. A plain `curl` gets `302`, so **PLAN-0100
Step 11's case list cannot run through the edge as written**: every row asserts an exact
status and body (`/health` → `200`, keyless `/whoami` → *exactly* `401`), and all of them
return `302` instead. Cloudflare says so itself — the redirect's own metadata carries
`"service_token_status": false`.

The standard remedy is a **service token**, and this is where it gets governed rather than
merely technical:

* Cloudflare's own UI warns that service tokens need the **Service Auth** action, not
  `Allow` — i.e. **a second policy** on the application;
* ADR-0035's acceptance shape names *"a second Access policy"* as a condition under which
  *"the arrangement has drifted and this ADR is reopened"*.

**Do not resolve this by quietly adding the policy.** It needs Cray's read of whether that
clause is about per-system onboarding cost (in which case a test-automation token is a
different axis) or literal policy count. Options are one policy and no scripted probes; a
permanent second policy plus an ADR amendment; or a temporary second policy for the Step 11
run, which then has to be recorded as evidence describing a configuration that no longer
exists.

### Rate limiting rule

Zone → **Security → Security rules → Rate limiting rules**, using the value from §2.1 and
the scope from §2.2. There is no file for this in the repo, so no test can close it;
PLAN-0100 requires a **screenshot of the configured rule** as the closeout artifact.

On the free plan the block response carries Cloudflare branding, and the zone gets **one**
rule — confirmed on the dashboard as `0/1 rules`. That is a known, accepted cost recorded in
PLAN-0100's residual risks, not a defect to chase.

⚠️ With Access already restricting the audience to an allowlist, the cap is no longer the
only thing standing between the demo and the internet. It can follow the first bring-up
rather than block it.

---

## 7. Get the source onto the deploy host

The published compose builds the app from source (`build: context: ../..`) and declares no
`image:`, so the deploy host needs **a checkout**. The repository is public, so the clone
itself needs no credentials.

```bash
ssh <host> 'powershell -NoProfile -Command -' < deploy.ps1
```

Drive it from a script file rather than an inline command: a `$` inside an inlined
`ssh … "…"` is eaten by the intervening shells and vanishes with no error — and inline
double quotes are dropped too, which arrives as a *syntax* error in whatever language you
were quoting and sends you debugging the wrong layer.

```powershell
$root = "C:\projects\vero-lite"
if (-not (Test-Path $root)) {
  git clone https://github.com/CrayJThiemsert/vero-lite.git $root
}
Set-Location $root
git pull --ff-only
```

🔴 **Do not add `--build` on a Windows deploy host driven over SSH.** The build must pull
`python:3.12-slim` and `ghcr.io/astral-sh/uv:0.11.9`, and Docker Desktop's credential helper
cannot run without an interactive desktop session — it fails with *"A specified logon
session does not exist"* even for anonymous pulls of public images, and even while a console
session is signed in. (So this is not something auto-login fixes.)

**Build on the workstation and ship the image instead.** It sidesteps the credential helper
entirely and gives the stronger guarantee — the artifact that runs is provably the one that
was tested:

```bash
CLOUDFLARED_CREDENTIALS_FILE=/nonexistent/placeholder docker compose -f deploy/published/oct-energy/docker-compose.yml build app
docker save oct-energy-app:latest -o /tmp/app.tar     # ~67 MB
scp /tmp/app.tar <host>:C:/<staging>/app.tar
ssh <host> 'docker load -i C:\<staging>\app.tar'
```

The dummy `CLOUDFLARED_CREDENTIALS_FILE` is needed because compose interpolates the **whole
file** before deciding what to build, and the cloudflared service declares that variable
required. Nothing is created at that path; volumes are materialised at container-create
time, not at build.

Then compare `docker image inspect oct-energy-app --format "{{.Id}}"` on both machines —
**equal ids prove the transfer, and that is the actual guarantee.** Do not use "a rebuild
produced the same id" as a check: buildkit's provenance attestation makes the id identify a
*build*, not its content, so it changes every time even when every layer is a cache hit.

`docker compose up` builds only when the image is missing, so a pre-loaded image is used as
is — no compose change is required to adopt this.

---

## 8. Host-side secrets

Neither value may enter the repo. Both live in an uncommitted `deploy/published/oct-energy/.env` next
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
passes the variable through optionally rather than requiring it. A first bring-up without
it is a reasonable way to separate "does the stack come up" from "does login work".

⚠️ **Write `.env` without a byte-order mark.** A BOM makes the first variable name
`\ufeffCLOUDFLARED_CREDENTIALS_FILE`, so compose's required-variable check fails for a
reason nobody would guess from the message. On Windows, PowerShell's `Set-Content -Encoding
utf8` and `Out-File -Encoding utf8` both emit one; `[System.IO.File]::WriteAllText` with a
`UTF8Encoding($false)` does not. Verify by reading the first bytes — they must be the
variable name, not `EF BB BF`.

Cheapest possible gate before starting anything, and it renders the whole file with the
variables substituted:

```bash
docker compose -f deploy/published/oct-energy/docker-compose.yml config --quiet
```

### 🔴 Windows inherits a much wider ACL than the file deserves

A credentials file created on Linux lands `0400`. The same file copied to `C:\…` inherits
the drive's default ACL, which was measured as **`BUILTIN\Users: Read`** and
**`NT AUTHORITY\Authenticated Users: Modify`** — every local account can read the tunnel
secret, and any authenticated one can replace it.

Tighten it deliberately:

```
icacls C:\<secrets-dir> /inheritance:r /grant:r "BUILTIN\Administrators:(OI)(CI)F" "NT AUTHORITY\SYSTEM:(OI)(CI)F"
```

⚠️ **Then re-run `docker compose up` and confirm the bind mount still works.** Docker
Desktop reads the file through its own file-sharing path; stripping `Authenticated Users`
may break that, and you want to find out in the same sitting rather than at the next
restart.

Put the file **outside every git worktree** — `C:\projects\vero-lite` is a repo, so the
secrets directory must not live under it. `verify_tunnel_credentials.py` refuses a path
inside a worktree for exactly this reason.

---

## 9. Bring it up, then hand over to Step 11

```bash
docker compose -f deploy/published/oct-energy/docker-compose.yml up -d
```

```bash
docker compose -p oct-energy ps
```

Both services `running`/`healthy`, **no `postgres` service**, and **no published host
port** on anything. That is PLAN-0100's Step 11 case 0, and it gates every other case: if
`app` is not up, the downstream cases are void rather than passing.

### What a healthy first run looked like (measured 2026-08-07)

Recorded so the next person can tell "working" from "started but wrong" without guessing:

* compose creates the network, the `prompt-log` volume and two containers; `app` reaches
  `healthy` before `cloudflared` is started (the compose `depends_on` condition);
* `ps` shows `app` with `8000/tcp` and `cloudflared` with **no ports at all** — the `8000`
  is the image's `EXPOSE`, not a published host port, and the distinction is the whole
  point of AC-5;
* the connector logs `Starting tunnel tunnelID=…` followed by an **ERR about a missing
  `cert.pem`** and then connects anyway — that error is expected and non-fatal (§2.3);
* the app logs `verticals discovered: … active='energy'`, both notifiers **DISARMED**, and
  **two `Connection refused` warnings** about fleet PM overrides and fleet live cases.
  Those two are the DB-less fail-soft path doing its job, not a failure;
* `docker compose exec app` fetching `http://127.0.0.1:8000/health` returns
  `{"status":"ok",…}` — the app answers on its own network even while the public edge
  answers `302`.

**Then re-run the §6 verification.** With the tunnel now live, `302` on every path proves
Access is in front of a *working* origin; a `200` would mean the gate is not applied and the
demo is open. Probe several paths, not one — and drive the loop from a **script file**, or a
variable that fails to expand will silently send every request to `/` and you will conclude
you tested seven things when you tested one.

From here the measured run is Step 11's, against pass/fail reads fixed **before** it
starts. Do not improvise them at the console — that is precisely what the fixed-in-advance
rule exists to prevent. Note §6's finding first: as written, those reads cannot run through
the Access gate at all.

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
risks), `deploy/published/oct-energy/README.md`. Preconditions were confirmed against the live
account in session 213; re-confirm rather than trusting that record.*
