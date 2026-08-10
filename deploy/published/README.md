# `deploy/published/` — one directory per published system

Each **published system** is one compose project on one subdomain, serving one
vertical (ADR-0036 D2). This directory holds one profile per system plus the two
operator scripts they share.

```
deploy/published/
  deploy.py                     the redeploy procedure  (⚠️ oct-energy only — see below)
  verify_tunnel_credentials.py  credential/ingress check (takes its paths as arguments)
  oct-<system>/                 one directory per published system
    docker-compose.yml  published.env  cloudflared/config.yml  README.md
```

⚠️ **That `oct-<system>` is a placeholder on purpose, and this file may not expand
it.** Listing the systems here would make this file a roster, and a vero-lite file
enumerating the published systems is a shadow ingress map (ADR-0036 D2). PLAN-0103
AC-5 states the rule mechanically — **no committed file outside a profile directory
may mention two or more distinct `oct-*` labels** — and
`tests/deploy/test_published_profiles.py` enforces it, so writing the roster back
in reddens the suite rather than shipping. `ls deploy/published/` is the filesystem
answering the question, which is not the same thing as a committed list.

(The single mention of `oct-energy` below is within the rule: one label is a
reference, two or more is a registry.)

A profile directory carries everything that differs per system: the compose
project, its committed env file, and its ingress allowlist. Read that system's
own `README.md` before touching it — the reasoning for *its* choices lives there,
not here.

## The naming convention every profile follows

The compose project is named **exactly the profile directory's name**
(`oct-energy` → `name: oct-energy`), and no compose file declares a fixed network
`name:` at all — compose scopes the network under the project, giving
`oct-energy_vero_oct` and so on.

Both halves are guard-enforced (AC-4), because the failure they prevent is silent:
two projects sharing a network let each system's connector reach the other's
`app:8000` and skip that system's allowlist entirely, and the allowlist tests would
stay green throughout — they read a committed file and cannot see who else is on
the wire. ADR-0035 (`0035:490-493`) names a shared network as grounds for reopening
the whole hosting arrangement.

The reason the convention is *derived from the directory* rather than freely
chosen: a new profile is made by copying an existing one, and a per-system literal
is precisely what a copy forgets. Here there is nothing to remember — the guard
compares `name:` to the directory and reddens on a mismatch.

## Why the profiles are near-duplicates on purpose

ADR-0036 D5 accepts N ≤ 3 near-duplicate compose files and allowlists rather than
a generator, and PLAN-0103 puts a shared compose generator explicitly out of
scope. That is the Rule of Three: the shared shape gets extracted after three
working instances exist, not before. Two systems that look 90% alike are cheaper
to read side by side than one templating layer that hides which 10% matters.

The duplication is bounded by guards, not by discipline: no two compose files may
share a project name or a fixed network name, because two projects on one Docker
network let each system's connector reach the other's `app:8000` and skip that
system's allowlist entirely — a condition ADR-0035 names as grounds for reopening
the whole arrangement.

## ⚠️ `deploy.py` serves `oct-energy` only

It is not parameterized by system, and the literals inside it — project name,
container names, image tag, the host compose path — are energy's.

That is a deliberate deferral (Cray, typed, s219), not an oversight. Writing a
`--system` interface now would mean designing it against a second deployment that
has never run: fleet carries a Postgres and will likely owe verification steps
energy does not, and their shape is not yet observable. **The decision belongs to
PLAN-0103 Step 10**, where procurement's bring-up makes the requirements real.

Whoever takes it is choosing between parameterizing this script and copying it
per profile. Worth weighing: the script's value is its seven post-deploy
verification checks, and those are the only thing standing between a green
offline suite and a container that cannot boot — session 213 shipped 3,943
passing tests over exactly that. Three copies means three chances for that net to
rot, two of them silently.

`tests/deploy/test_deploy.py` pins the script to oct-energy's compose file, so a
second system cannot quietly start riding these energy-shaped literals.

## What is NOT here

- **No secrets.** `API_KEYS` and the tunnel credentials are provisioned
  host-env-local and never enter git (CLAUDE.md §8). Each profile's README states
  how.
- **No portal-repo files.** The ingress map across systems, the Access policies,
  the landing surface and the domain are the portal repo's property (ADR-0036 D1,
  ADR-0035 D4/L5). Nothing here names the apex domain.
- **No registry of systems.** No committed file outside a profile directory lists
  more than one system label — a vero-lite file enumerating the published systems
  would be a shadow ingress map (ADR-0036 D2). The directory listing above names
  only the systems that exist as directories, which is the filesystem, not a
  registry.
