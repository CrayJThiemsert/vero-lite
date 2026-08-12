# PLAN-0103 Step 10 — procurement brought up as published system #2

**Date:** 2026-08-11 (session 222)
**Event type:** host-state change on MS-S1 + Cloudflare account configuration, under an explicit typed §8 go
**Operator-grade detail:** this file. No gitignored companion — everything below is safe to commit.

> ⚠️ **Domain naming.** This record uses `oct-procurement.<DOMAIN>` rather than the
> apex, per ADR-0035 D1(3). That clause's scope over evidence documents is **ADR-0035
> OQ-6, open and unruled** (surfaced the same day, #1128). While it is open this record
> takes the conservative side; if OQ-6 rules that evidence records may name the zone,
> this file can be revisited. The subdomain **label** is not in question.

## The go

**Cray, typed, 2026-08-11 (session 222): §8 go for the procurement bring-up
specifically**, then a second typed go for the ACL step (§4 below) under the
canary-first sequence proposed before it ran. AC-10's second clause requires a
per-bring-up go; this is that record.

Deployment order is SD-2(b)'s ruling — procurement first, fleet second. Procurement's
bring-up is **not** ADR-0037-gated (it is DB-less: its compose declares `app` +
`cloudflared` and no postgres) and **not** AC-11-gated (the RoPA gates fleet only).

## What is live

| | |
|---|---|
| Compose project | `oct-procurement` |
| Containers | `oct-procurement-app` (healthy, `8000/tcp` EXPOSE only) · `oct-procurement-cloudflared` (no ports) |
| Volume / network | `oct-procurement-prompt-log` · `oct-procurement_vero_oct` |
| Tunnel | `vero-oct-procurement` (its own tunnel — each system has one; energy's is `vero-oct-published`) |
| Access application | `vero-oct-procurement`, one Allow policy `vero-oct-procurement-allowlist`, session 24 h |
| Published views | `G,F` |
| Admitted ingress paths | seven: `^/$` `^/assets/.+$` `^/health$` `^/meta$` `^/procedures$` `^/demo/hero/governance$` `^/demo/hero/impact$` |

## Evidence

**Image provenance — the artifact that runs is the one that was built and tested.**
Built on the dev box, `docker save` → `ssh … docker load` over **stdin** (the redeploy
runbook's form: no staging path, no Windows path in any command, no tar left on the
host). Image id identical on both machines:
`sha256:bc95aa04d945e2c5598fdacddd3016941948cddc056bc9319ad1959a2b106e0f`. Id equality
is the guarantee; "a rebuild produced the same id" is not, because buildkit's
provenance attestation makes the id identify a *build* rather than its content.

**Credentials transfer.** `verify_tunnel_credentials.py` on the workstation: 10 PASS,
1 FAIL — the FAIL is `config tunnel: matches credentials`, which runbook §2.3 documents
as permanently expected while the config names the tunnel by name. sha256 agreed across
three independent reads (the verifier, `sha256sum` recomputed later, `Get-FileHash` on
MS-S1): `719647d4…d473ad91`. Permissions `0400`, outside any git worktree.

**`.env` shipped BOM-free by construction, not by care.** Written with Linux tooling and
`scp`'d, so the PowerShell BOM hazard cannot arise. Verified before shipping: 0 × `0x0d`,
2 × `0x0a`, 175 bytes — matching the byte arithmetic exactly, which is what excludes a
BOM. Host hash equalled local hash. Functional gate: `docker compose config --quiet`
returned 0, which is the check a BOM would actually break.

**Offline gates on the host.** `compose config --quiet` → 0. `cloudflared … ingress
validate` → the literal `OK` (judged on output text, never on exit code — the trailing
`--config` form exits 0 while validating nothing).

**The gate is in front, proven by a before/after with a live control.** Measured at
12:41, DNS routed and tunnel down: procurement `530`, energy `302` in the same second.
Measured at 13:14, after the Access application existed: procurement `302` on `/`,
`/health`, `/whoami`, `/query`, `/meta`, with `location:` at the team domain and
`www-authenticate: Cloudflare-Access`. Taking the 530 reading *first* is what makes the
302 attributable to the Access application rather than to anything else.

**The allowlist binds, proven by a differential.** A non-allowlisted address reached the
"Enter your code" screen but **never received a PIN**; the allowlisted address received
one in the same sitting. Same mail path, same moment, opposite outcomes — which excludes
"mail is slow" and "mail is broken", the two explanations an absence alone cannot rule
out. The Access authentication log independently records `Allowed` for the allowlisted
address against application `vero-oct-procurement`.

**Runtime shape matches the recorded healthy shape.** App log: `active='procurement'`,
both notifiers `DISARMED`, and the two `Connection refused` warnings about fleet PM
overrides and fleet live cases — the DB-less fail-soft path working, not a failure.
Connector log: the expected non-fatal `cert.pem` ERR, then **four** registered tunnel
connections (bkk07 ×2, sin07, sin22).

**Do-no-harm (Step 10 item 5).** `oct-energy-app` and `oct-energy-cloudflared` showed
**Up 26 hours** afterwards — never restarted, never touched — and energy still answered
`302`. Every `smb-*` container had exited **two weeks** earlier, verified by timestamp
rather than assumed. The host checkout was **not** pulled: `git diff e938cf6..d9253fb --
deploy/` is empty, so the host's profile files were already byte-identical to `main`,
and skipping the pull removed the only step that would have touched a co-tenant's files.

**Headroom, now measured with two systems rather than projected from one.** 347.2 MiB
total across four containers (`oct-energy-app` 208.9, `oct-procurement-app` 85.4,
`oct-energy-cloudflared` 34.2, `oct-procurement-cloudflared` 18.8) of 31.16 GiB
available to the Docker VM. Step 9 projected ≈0.95 GiB for three systems; the projection
is conservative and system #3 is not resource-constrained. Note procurement's app had
been up 28 minutes against energy's 26 hours, so its figure will rise with use.

## 🔴 What failed: the runbook's ACL step is not applicable on this host

Runbook §8 prescribes `icacls … /inheritance:r /grant:r "BUILTIN\Administrators:(OI)(CI)F"
"NT AUTHORITY\SYSTEM:(OI)(CI)F"` on the secrets directory, and warns to re-test the bind
mount afterwards. **Applied, it breaks the bind mount outright:**

```
Container oct-procurement-cloudflared Error response from daemon:
CreateFile C:\vero-secrets\cloudflared-credentials-procurement.json: Access is denied.
```

Docker Desktop reads the file through its own file-sharing path and needs one of the
grants the tightening removes. Reverted with `icacls … /reset /t`; the ACL returned to
its prior state ACE-for-ACE on the directory and both credentials files, and the
subsequent `up -d` succeeded.

**Why the sequence mattered more than the outcome.** The tightening applies to the
directory, so **energy's credentials file was tightened too** — and energy kept running,
because an ACL governs *opening* a file and its container already held the handle. Had
the new system not been brought up immediately as the canary, the breakage would have
surfaced at the next Docker Desktop restart or host reboot, with nothing connecting it
back to an ACL change made weeks earlier. The live system was never at risk during the
test; the new one absorbed it.

> ✅ **CLOSED 2026-08-12 (session 223).** The untried idea below was tested and held —
> then went further: `Authenticated Users` **and** `BUILTIN\Users` are both gone, replaced
> by a direct grant to the signed-in account's SID, force-recreate-proven on both systems.
> The runbook's remedy has been replaced with the working form. Record:
> `docs/logs/2026-08-12-ms-s1-secrets-acl-tightening.md`. The paragraph below is preserved
> as the state at the time of writing — **do not act on it**.

**Residual, and it is pre-existing rather than introduced here.** Both credentials files
remain `BUILTIN\Users:(RX)` and `NT AUTHORITY\Authenticated Users:(M)` — every local
account can read the tunnel secrets and every authenticated one can modify them. The
runbook's remedy does not work, so this is **open for Cray**, not closed. One untried
idea with a real chance: the dangerous grant is **Modify**, not Read, and Docker
plausibly needs only Read — a tightening that keeps `(RX)` and drops `(M)` may satisfy
both. Testing it is now cheaper than it was, because procurement can be restarted freely
while nobody is using it.

## Not done, and why — the keyed `/whoami` check does not apply here

The bring-up package carried a "keyed `/whoami` = 200" check. **It is an energy-shaped
check and was carried over in error.** procurement's `cloudflared/config.yml` deliberately
does **not** admit `^/whoami$`: SD-3/SD-4 ruled this system "anonymous read + hero, no
personas", default-deny means a row must earn its place, and the file records the
consequence that decided it — Tab G renders Approve/Reject after a successful login, and
those buttons call H-family routes this system does not admit, so admitting `/whoami`
would buy a visitor a login leading to a control that 404s. energy **does** admit it.

Consequence: `API_KEYS` has no consumer on procurement and the digest→`appr-pm` mapping
is **unverified and unverifiable from outside** until a keyed route is admitted. **Cray
ruled (typed, s222): keep it**, so it is ready if Step 6 rules SD-8 and admits `/whoami`.
The host `.env` now carries that reasoning inline so the next reader does not infer a
login path that does not exist.

## Corrections owed to the runbook (applied in the same PR)

1. **§8's ACL step does not work on this host** — measured above.
2. **Access takes ~4 minutes to take effect** on a newly created application. The runbook
   presents the `302` check as immediate. Measured: `530` at 13:10, still `530` through
   eleven 20-second polls, `302` at ~13:13:40.
3. **Propagation is per-path, not atomic.** At 13:14:47 four paths answered `302` while
   `/meta` still answered `530`. Spot-checking one path can therefore produce a false
   PASS *or* a false FAIL depending which path is picked. The runbook already says "probe
   several paths, not one" — for a different reason (shell variables failing to expand).
4. **Route sets differ per system; read that system's `config.yml`.** A verification
   carried from another profile can assert a route this system deliberately refuses.
5. **The cheapest allowlist test is the differential PIN-delivery test** — try one
   allowlisted and one non-allowlisted address and see which receives mail. No code entry
   and no second mailbox needed. This also corrects an assumption stated during the run:
   Access does **not** send a PIN to every address; it shows the same code-entry screen
   but only mails allowlisted ones.

## Reference

- PLAN: `docs/plans/0103-portal-landing-and-per-system-published-profiles.md` §Step 10, AC-10.
- ADRs: ADR-0035 D1(3) + OQ-6 (domain naming, open) · ADR-0036 D2 (vertical-as-system,
  the two-artifact price) · ADR-0037 (DB posture — not engaged, procurement is DB-less).
- Runbook: `docs/runbooks/published-demo-bring-up.md` (corrected in the same PR).
- Companion: `docs/logs/2026-08-10-oct-energy-migration-phase2-and-step9-headroom.md`
  (Step 9's projection, now testable against a second system).

AI-assisted (Claude Code, session 222); no `Co-Authored-By` per CLAUDE.md §7.
