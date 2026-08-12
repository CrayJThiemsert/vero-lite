# MS-S1 secrets ACL — the exposure closed, and the runbook's remedy replaced

**Date:** 2026-08-12 (session 223)
**Event type:** host-state change on MS-S1, under two explicit typed §8 gos
**Operator-grade detail:** this file. No gitignored companion — everything below is safe
to commit (no secret material, no apex domain).

Closes the exposure carried open by session 222's handoff §5.5 and by
`docs/logs/2026-08-11-plan0103-step10-procurement-bring-up.md` §"Residual". That record
states the remedy in `docs/runbooks/published-demo-bring-up.md` §8 does not work; it was
right, and this session replaced it with a form that does.

## The gos

**Cray, typed, 2026-08-12 (session 223), two of them:**

1. **Ladder A → C**, each rung tightening `C:\vero-secrets` and canary-verifying with a
   force-recreate of **procurement only** — energy explicitly not to be touched.
2. After both rungs passed, a **second go to restart energy for real**, chosen over a
   non-invasive mount probe, to close the last unproven gap end-to-end.

The second go was asked for rather than assumed: the first go named energy as
out of scope, and a still-running container proves nothing about a file it opened
38 hours before the ACL changed.

## Baseline — what was actually there

Every ACE **inherited** from the drive root (`AreAccessRulesProtected=False`), on the
directory and on both credentials files:

```
BUILTIN\Administrators:(I)(F)
NT AUTHORITY\SYSTEM:(I)(F)
BUILTIN\Users:(I)(RX)
NT AUTHORITY\Authenticated Users:(I)(M)
```

Every local account could read both tunnel secrets; every authenticated one could
replace them.

## What changed, and the evidence for each rung

| | Rung A | Rung C |
|---|---|---|
| Change | drop `Authenticated Users` | also drop `BUILTIN\Users`, grant the account SID `(RX)` |
| `oct-procurement-cloudflared` | `e04267502e92` → **`2cb360d9d6e3`** | → **`87713924a147`** |
| `Access is denied` | none | none |
| Tunnel actually back | 4× `Registered tunnel connection` | 4× `Registered tunnel connection` |
| Co-tenant | energy `76049f41de22` / `6e66a8546884` untouched, Up 38 h | unchanged |

Then, under the second go:

| | Energy proof |
|---|---|
| `oct-energy-cloudflared` | `76049f41de22` (Up 38 h) → **`3f3ce9c5d6a2`** |
| `oct-energy-app` | `6e66a8546884`, **never recreated**, Up 38 h (healthy) — only the connector was recreated |
| Result | `compose config` gate rc=0, `up` rc=0, 4× `Registered tunnel connection` |

**Final state, identical on the directory and both credentials files:**

```
CRAY-MS-S1-MAX\Jirachai Thiemsert:(OI)(CI)(RX)
BUILTIN\Administrators:(OI)(CI)(F)
NT AUTHORITY\SYSTEM:(OI)(CI)(F)
```

### The check was seen RED before it was trusted GREEN

A standalone verifier asserted two things at once — that the remote read *succeeded*
(3/3 targets returned `Successfully processed 1 files`) and that no `Authenticated Users`
ACE remained. It was run **before** any change and reported `authenticated_users_aces=4`,
`VERDICT: FAIL`; the same command after rung A reported `0` / `PASS`. The positive anchor
is load-bearing: without it an ssh failure would produce zero matches and pass silently —
the exact `|| echo`-shaped false pass this repo has been bitten by before.

## Why the old form failed — the part worth carrying forward

The session-222 command kept `BUILTIN\Administrators:(OI)(CI)F` **and the signed-in
account is an Administrator**, yet Docker still got `Access is denied`.

The only explanation consistent with that: Docker Desktop's backend runs under a
**filtered (non-elevated) token**, in which the `Administrators` group is marked
*deny-only* and grants nothing. The mount had been working on `BUILTIN\Users:(RX)` all
along. Granting the **account SID** directly is what makes full closure possible — a user
SID is always present and enabled in a filtered token.

A second, structural error in the old form: the wide ACEs were **inherited**, and an
inherited ACE cannot be edited in place. `/grant:r` alone adds an explicit ACE that
*unions* with the inherited one, so a "tightening" written that way changes nothing while
appearing to succeed. `/inheritance:d` must come first.

Removing an inheritable ACE on the directory propagated to both existing files
automatically — they still report `(I)`. `/t` was not needed and would have been wrong.

## Left on the host — needs cleanup

`C:\vero-secrets-acl-backup-s223.txt`, written by `icacls /save` before rung A. It holds
no secret material, only ACL descriptors — but it is a snapshot of the **wide** ACL, so
restoring it would reopen the exposure. Delete it rather than keep it as a rollback
reference; the rollback that matters is documented in bring-up §8, not in that file.

## Not a defect

`cloudflared` logs `ERR Cannot determine default origin certificate path … cert.pem` at
every start. It is expected for a credentials-file tunnel and was present on both systems
before and after; all four connections register immediately after it.
