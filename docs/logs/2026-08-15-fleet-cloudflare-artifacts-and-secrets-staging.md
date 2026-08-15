# Fleet — Cloudflare artifacts created and host secrets staged (2026-08-15)

**System:** `oct-fleet-maintenance` · **Session:** 232 · **Executed by:** Cray
(workstation + Cloudflare dashboard + MS-S1). **Code touched no host state.**

> ⚠️ **This file is RECONSTRUCTED, not written live.** It was transcribed at the
> s232 close from that session's record, after the actions had completed. Every
> value below was reported at execution time; none was re-measured while writing
> this file. It is marked so a future reader weighs it as a transcription rather
> than as a contemporaneous capture — re-verify anything load-bearing before
> relying on it.

## Why this file exists

ADR-0036 D2 prices each published system at **two artifacts that this repo
cannot verify by design** — a DNS route and an Access policy, both living in the
Cloudflare dashboard. PLAN-0103 **AC-10** requires that evidence. The bring-up
log that will normally own it **cannot be written until the bring-up happens**,
and fleet's bring-up is still gated on AC-11's RoPA. Without this file the
evidence for a completed, verified operation would exist only in a **gitignored
handoff** — i.e. nowhere durable. Precedent for the shape:
[`2026-08-12-ms-s1-secrets-acl-tightening.md`](2026-08-12-ms-s1-secrets-acl-tightening.md).

## 1. Cloudflare — the two artifacts

| Step | Result |
|---|---|
| `tunnel login` | **Correctly REFUSED** — `cert.pem` already existed from the energy bring-up (2026-08-07). ⚠️ The CLI advises moving or deleting it; **do not**. `cert.pem` is **account-wide** authority, one per account, and deleting it buys nothing. **Skip the login step whenever it exists.** |
| `tunnel list` (before) | 6 tunnels. `vero-oct-published` (energy) and `vero-oct-procurement` both live with 4 connections each; four co-tenant tunnels with none. **No fleet tunnel existed** — independent proof fleet was unreachable. |
| `tunnel create` | **`vero-oct-fleet-maintenance` = `c28103ab-e52a-47b2-8c8d-45b0315653dd`**. 🔴 The name is **pinned** by `deploy/published/oct-fleet-maintenance/cloudflared/config.yml` — any other name is a committed-file change, i.e. a PR, not a shortcut. |
| `verify_tunnel_credentials.py` | **11 checks, 1 FAIL — the expected one** (`config tunnel: matches credentials`, because the config names the tunnel by name, not UUID). `permissions 0400`, 175 bytes, all shape checks PASS. Credentials fingerprint **`dc7c3f44866f180544da69145b08eabbf6e4fe5ee97294aaa7a7612973f10a7a`** (safe to share — the verifier says so). |
| `route dns` | done |
| 🔴 **the `530` reference reading** | `HTTP/2 530`, `cf-ray a2b4e7b339d2fd87-SIN`, `server: cloudflare`. **Critically: NO `location:` and NO `www-authenticate`.** That **absence** is the negative carrying all the weight — it is what makes the later 302 attributable to the Access policy rather than to anything else. |
| Access app + policy | app `vero-oct-fleet-maintenance`, policy `vero-oct-fleet-maintenance-allowlist`; 24 h session; **Allow + Emails include**; Path empty. 🔴 Never "All authenticated users" / "Everyone" — under One-time PIN, *authenticated* means *anyone who can receive mail at an address they typed in*. |
| 302 verification | **6/6 paths** (`/`, `/health`, `/meta`, `/whoami`, `/query`, `/procedures`) → `302`, `location:` → `cloudflareaccess.com`, `www-authenticate` present. **No 530 stragglers** — propagation had completed, unlike s222's ~4-minute lag. |
| 🔴 **differential PIN test** | **An allowlisted address RECEIVED a PIN; a non-allowlisted address did NOT.** The Access log shows the allowlisted one `Allowed`. |

### The step order is load-bearing

`route dns` **→** read the `530` **→** create the Access application **→** verify
`302`. A `530` cannot be read before the DNS route exists, and it cannot be read
*after* the Access app exists either — the app is what turns it into a 302. An
in-session summary inverted the middle two steps and was corrected.

### Why the differential PIN test is the only sufficient check

🔴 **`302` alone proves nothing about who is allowed in** — a wide-open policy
returns exactly the same `302`, and the browser shows the **same** "Enter your
code" screen in both cases. The screen cannot distinguish them; only the mailbox
can. This is the single check that proves the policy **discriminates**.

⚠️ **Two propagation traps measured at s222, both still worth knowing:** a `530`
immediately after creating the application does **not** mean misconfiguration
(it persisted ~4 minutes, 11 consecutive 20-second polls, before flipping), and
propagation is **per-path, not simultaneous** — in one round 4 paths answered
`302` while `/meta` still answered `530`. **Checking a single path can mislead in
either direction.**

## 2. Host secrets — all four staged on MS-S1

| Step | Result |
|---|---|
| credentials file → host | `C:\vero-secrets\cloudflared-credentials-fleet-maintenance.json` (matching the existing procurement/energy naming; the name is convention only — the env var carries the path) |
| `icacls <file> /reset` | ✅ then `icacls C:\vero-secrets /t` over all 9 paths: fleet's file shows **all three ACEs as `(I)`**, inherited from the tightened parent, and is **byte-identical in ACL terms to procurement's live file**. No `BUILTIN\Users`, no `Authenticated Users`, no `(M)` anywhere in the tree. 🔴 A same-volume move is a rename and **carries the old, wider ACL with it** (measured s223) — which is why the `/reset` is not optional. |
| ⭐ bonus finding | the same `/t` sweep proved **s223's remediation is still intact three days on** — `acl-backup-s223.txt` no longer carries the wide ACEs. Spot-checking the new file alone could never have shown this. |
| fingerprint on MS-S1 | ✅ **matches** `dc7c3f44…f10a7a`. ⚠️ `Get-FileHash` returns UPPERCASE and the Python verifier lowercase — **compare case-insensitively** or two identical values read as different. |
| host checkout pull | ✅ fast-forward to `205ba4b`, 74 files. **Blast radius checked first:** the only live-system file in the diff was `oct-procurement/cloudflared/config.yml`, and reading it showed the change is **100% comments** — no route, ingress rule or tunnel name touched. |
| `.env` on host | ✅ 4 variables present (name-only check — `config --quiet` cannot see the two bare pass-throughs); **no BOM** (first three bytes `CLO`, not the UTF-8 BOM). 🔴 Write these on the Linux side and `scp`; PowerShell `>` / `Out-File` add a BOM. |
| `docker compose config --quiet` | ✅ **RC = 0** |

🔴 **`API_KEYS` and `UI_DEMO_PERSONA_KEYS` must be generated as ONE pair** — boot
refuses on a crossed pair, and a crossed pair that somehow passed would let login
succeed while the audit trail recorded the wrong principal, with nothing looking
wrong.

⚠️ **`docker compose config` WITHOUT `--quiet` prints the interpolated config**,
including `DATABASE_URL` with the password and the full `API_KEYS`. Always
`--quiet`.

### The deployed secret set is the SECOND one generated

🔴 Recorded so a future reader comparing values is not confused. The first set
was pasted into the session transcript while sharing command output. **Nothing
had been deployed**, so all four values were rotated and the exposed set was
never used. Risk assessment at the time: `UI_DEMO_PERSONA_KEYS` is **served to
the browser by ruling** (Cray, typed, s224), so its exposure changes nothing;
`API_KEYS` holds digests only; the DB password was the one value whose leak
would have mattered, and **it never reached a running system**. ⚠️ The
transcript store retains the exposed set for ~30 days.

## 3. What this discharges, and what it does not

✅ **ADR-0036 D2's two-artifact price is PAID and VERIFIED for fleet**, and the
four host secrets are staged. Together these close two of the five gates s232
enumerated for fleet's bring-up.

🔴 **This is not a bring-up.** Fleet is not serving. The remaining gate is
**PLAN-0103 AC-11's RoPA instance**, which only Cray can author as controller;
fleet's typed §8 go was given verbally but **cannot be validly recorded** until
the RoPA exists to cite **by path**. After that the sequence is mechanical: go
record → the runbook's schema step → `up -d` → live verification (including the
**keyed `/whoami` = 200** control that neither prior system could produce) →
do-no-harm across **two** live siblings → the bring-up log → tick AC-10 + AC-11.

⚠️ **When that bring-up log is written, it should cite this file rather than
restate it** — the two-artifact evidence is here, and a second copy would drift.
